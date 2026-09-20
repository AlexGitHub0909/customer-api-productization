from __future__ import annotations

import importlib.util
import json
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
        gates = [
            {
                "id": gate_id,
                "status": "pass",
                "evidence": [{"path": "evidence.md", "detail": f"Evidence for {gate_id}"}],
            }
            for gate_id in sorted(required_gates)
        ]
        return {
            "schema_version": 1,
            "mode": "HARDEN",
            "status": status,
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
            self.assertEqual([], MODULE.validate(manifest, Path(directory).resolve()))

    def test_pilot_ready_manifest_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory).resolve()
            manifest = self.base_manifest(workspace)
            self.assertEqual([], MODULE.validate(manifest, workspace))

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
