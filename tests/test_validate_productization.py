from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_productization.py"
SPEC = importlib.util.spec_from_file_location("validate_productization", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ValidateProductizationTest(unittest.TestCase):
    def assessment(self, fit_decision: str = "PRODUCTIZE") -> dict:
        return {
            "fit_decision": fit_decision,
            "target_audience": "external_customers",
            "repeatable_integration": fit_decision == "PRODUCTIZE",
            "business_capability_maturity": "controlled_pilot",
            "tenant_boundary": "defined",
            "data_action_authority": "confirmed",
            "operational_owner": "defined",
            "rationale": ["The same stable capability is required by multiple external customers."],
        }

    def base_manifest(self, workspace: Path, status: str = "PILOT_PACKAGE_READY") -> dict:
        artifact = workspace / "evidence.md"
        artifact.write_text("current evidence\n", encoding="utf-8")
        deliverables = [
            {"kind": kind, "path": "evidence.md"}
            for kind in sorted(MODULE.CORE_DELIVERABLES)
        ]
        required_gates = set(MODULE.PILOT_GATES)
        if status == "GA_PACKAGE_READY":
            required_gates.update(MODULE.GA_GATES)
        gates = []
        for gate_id in sorted(required_gates):
            evidence_type = sorted(MODULE.REQUIRED_GATE_EVIDENCE_TYPES.get(gate_id, {"decision"}))[0]
            evidence = {
                "type": evidence_type,
                "path": "evidence.md",
                "detail": f"Evidence for {gate_id}",
            }
            if evidence_type in MODULE.TIMED_EVIDENCE_TYPES:
                evidence["observed_at"] = "2026-09-20T12:00:00+08:00"
            gates.append({"id": gate_id, "status": "pass", "evidence": [evidence]})
        return {
            "schema_version": 1,
            "mode": "HARDEN",
            "status": status,
            "source_revision": "example-revision",
            "evaluated_at": "2026-09-20T12:30:00+08:00",
            "evidence_cutoff_at": "2026-09-01T00:00:00+08:00",
            "scope": ["customer API v1"],
            "assessment": self.assessment(),
            "features": {
                "webhooks": False,
                "async_operations": False,
                "protected_files": False,
                "batch_operations": False,
                "official_sdk": False,
            },
            "deliverables": deliverables,
            "gates": gates,
        }

    def test_assessment_only_accepts_not_suitable_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = {
                "schema_version": 1,
                "mode": "ASSESS",
                "status": "ASSESSMENT_COMPLETE",
                "assessment": self.assessment("NOT_SUITABLE"),
            }
            manifest["next_steps"] = ["Use a one-off managed integration instead of a customer API product."]
            self.assertEqual([], MODULE.validate(manifest, Path(directory).resolve()))

    def test_assessment_complete_requires_next_steps(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = {
                "schema_version": 1,
                "mode": "ASSESS",
                "status": "ASSESSMENT_COMPLETE",
                "assessment": self.assessment("DISCOVERY_ONLY"),
            }
            errors = MODULE.validate(manifest, Path(directory).resolve())
            self.assertTrue(any("next_steps" in error for error in errors), errors)

    def test_pilot_ready_manifest_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = self.base_manifest(workspace)
            self.assertEqual([], MODULE.validate(manifest, workspace))

    def test_productize_decision_rejects_internal_only_audience(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = {
                "schema_version": 1,
                "mode": "ASSESS",
                "status": "ASSESSMENT_COMPLETE",
                "assessment": self.assessment(),
                "next_steps": ["Proceed to BASELINE after confirming the external audience."],
            }
            manifest["assessment"]["target_audience"] = "internal_only"
            errors = MODULE.validate(manifest, Path(directory).resolve())
            self.assertTrue(any("PRODUCTIZE requires an external" in error for error in errors), errors)

    def test_ready_status_rejects_assess_mode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = self.base_manifest(workspace)
            manifest["mode"] = "ASSESS"
            errors = MODULE.validate(manifest, workspace)
            self.assertTrue(any("cannot use mode ASSESS" in error for error in errors), errors)

    def test_ready_status_requires_revision_time_and_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = self.base_manifest(workspace)
            manifest.pop("source_revision")
            manifest.pop("evaluated_at")
            manifest.pop("evidence_cutoff_at")
            manifest.pop("scope")
            errors = MODULE.validate(manifest, workspace)
            self.assertTrue(any("source_revision" in error for error in errors), errors)
            self.assertTrue(any("evaluated_at" in error for error in errors), errors)
            self.assertTrue(any("evidence_cutoff_at" in error for error in errors), errors)
            self.assertTrue(any("scope" in error for error in errors), errors)

    def test_blocked_status_requires_actionable_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = {
                "schema_version": 1,
                "mode": "HARDEN",
                "status": "EVIDENCE_BLOCKED",
                "assessment": self.assessment(),
            }
            errors = MODULE.validate(manifest, Path(directory).resolve())
            self.assertTrue(any("blockers" in error for error in errors), errors)

    def test_blocked_cli_returns_two_for_actionable_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = {
                "schema_version": 1,
                "mode": "HARDEN",
                "status": "EVIDENCE_BLOCKED",
                "assessment": self.assessment(),
                "blockers": [
                    {
                        "issue": "Tenant-isolation test environment is unavailable.",
                        "impact": "Cross-customer access cannot be verified.",
                        "next_step": "Provision the isolated environment and rerun negative tests.",
                    }
                ],
            }
            manifest_path = workspace / "blocked.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(manifest_path), "--workspace", str(workspace), "--json"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            self.assertEqual(2, result.returncode, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["valid"])
            self.assertEqual("EVIDENCE_BLOCKED", payload["status"])

    def test_execution_gate_rejects_decision_only_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = self.base_manifest(workspace)
            test_gate = next(gate for gate in manifest["gates"] if gate["id"] == "TEST-01")
            test_gate["evidence"][0]["type"] = "decision"
            test_gate["evidence"][0].pop("observed_at", None)
            errors = MODULE.validate(manifest, workspace)
            self.assertTrue(any("TEST-01 requires evidence type" in error for error in errors), errors)

    def test_execution_evidence_cannot_be_newer_than_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = self.base_manifest(workspace)
            test_gate = next(gate for gate in manifest["gates"] if gate["id"] == "TEST-01")
            test_gate["evidence"][0]["observed_at"] = "2026-09-20T13:00:00+08:00"
            manifest["evaluated_at"] = "2026-09-20T12:30:00+08:00"
            errors = MODULE.validate(manifest, workspace)
            self.assertTrue(any("cannot be later than evaluated_at" in error for error in errors), errors)

    def test_execution_evidence_cannot_predate_declared_cutoff(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = self.base_manifest(workspace)
            test_gate = next(gate for gate in manifest["gates"] if gate["id"] == "TEST-01")
            test_gate["evidence"][0]["observed_at"] = "2026-08-31T23:59:59+08:00"
            errors = MODULE.validate(manifest, workspace)
            self.assertTrue(any("cannot be earlier than evidence_cutoff_at" in error for error in errors), errors)

    def test_missing_security_and_traceability_delivery_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = self.base_manifest(workspace)
            manifest["deliverables"] = [
                item
                for item in manifest["deliverables"]
                if item["kind"] not in {"security_model", "traceability"}
            ]
            manifest["gates"] = [gate for gate in manifest["gates"] if gate["id"] != "TRACE-01"]
            errors = MODULE.validate(manifest, workspace)
            self.assertTrue(any("security_model" in error for error in errors), errors)
            self.assertTrue(any("traceability" in error for error in errors), errors)
            self.assertTrue(any("TRACE-01" in error for error in errors), errors)

    def test_disabled_feature_rejects_pass_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = self.base_manifest(workspace)
            manifest["gates"].append(
                {
                    "id": "WEBHOOK-01",
                    "status": "pass",
                    "evidence": [
                        {
                            "type": "test_run",
                            "path": "evidence.md",
                            "detail": "Webhook test",
                            "observed_at": "2026-09-20T12:00:00+08:00",
                        }
                    ],
                }
            )
            errors = MODULE.validate(manifest, workspace)
            self.assertTrue(any("WEBHOOK-01 must be not_applicable" in error for error in errors), errors)

    def test_webhook_feature_requires_webhook_gate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = self.base_manifest(workspace)
            manifest["features"]["webhooks"] = True
            errors = MODULE.validate(manifest, workspace)
            self.assertTrue(any("WEBHOOK-01" in error for error in errors), errors)

    def test_ready_status_rejects_partial_tenant_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = self.base_manifest(workspace)
            manifest["assessment"]["tenant_boundary"] = "partial"
            errors = MODULE.validate(manifest, workspace)
            self.assertTrue(any("tenant_boundary defined" in error for error in errors), errors)

    def test_ga_requires_additional_gates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = self.base_manifest(workspace)
            manifest["status"] = "GA_PACKAGE_READY"
            errors = MODULE.validate(manifest, workspace)
            self.assertTrue(any("DEPRECATION-01" in error for error in errors), errors)

    def test_evidence_cannot_escape_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = self.base_manifest(workspace)
            manifest["gates"][0]["evidence"][0]["path"] = "/etc/hosts"
            errors = MODULE.validate(manifest, workspace)
            self.assertTrue(any("escapes workspace" in error for error in errors), errors)

    def test_manifest_file_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = self.base_manifest(workspace)
            manifest_path = workspace / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertEqual(manifest, MODULE.load_json(manifest_path))


if __name__ == "__main__":
    unittest.main()
