#!/usr/bin/env python3
"""Validate a customer API productization delivery manifest.

This validator is intentionally layout- and stack-neutral. It verifies the
declared readiness state, required deliverable kinds, gate decisions, and that
evidence paths resolve inside the selected workspace. It does not claim that a
referenced artifact is semantically correct.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


MODES = {"ASSESS", "BASELINE", "EXPAND", "HARDEN"}
STATUSES = {
    "ASSESSMENT_COMPLETE",
    "PILOT_PACKAGE_READY",
    "GA_PACKAGE_READY",
    "EVIDENCE_BLOCKED",
}
FIT_DECISIONS = {"PRODUCTIZE", "DISCOVERY_ONLY", "NOT_SUITABLE"}
READY_STATUSES = {"PILOT_PACKAGE_READY", "GA_PACKAGE_READY"}
ASSESSMENT_ENUMS = {
    "target_audience": {
        "external_customers",
        "external_partners",
        "external_customers_and_partners",
        "internal_only",
        "one_off_counterparty",
        "unknown",
    },
    "business_capability_maturity": {"stable", "controlled_pilot", "volatile", "unknown"},
    "tenant_boundary": {"defined", "partial", "missing", "unknown"},
    "data_action_authority": {"confirmed", "partial", "missing", "unknown"},
    "operational_owner": {"defined", "partial", "missing", "unknown"},
}
EXTERNAL_AUDIENCES = {
    "external_customers",
    "external_partners",
    "external_customers_and_partners",
}
READY_MATURITY = {"stable", "controlled_pilot"}

REQUIRED_ASSESSMENT_FIELDS = {
    "fit_decision",
    "target_audience",
    "repeatable_integration",
    "business_capability_maturity",
    "tenant_boundary",
    "data_action_authority",
    "operational_owner",
    "rationale",
}

CORE_DELIVERABLES = {
    "product_scope",
    "machine_contract",
    "integration_guide",
    "test_plan",
    "operations_runbook",
    "changelog",
}

PILOT_GATES = {
    "FIT-01",
    "OWN-01",
    "SCOPE-01",
    "CONTRACT-01",
    "CONTRACT-02",
    "AUTH-01",
    "TENANT-01",
    "DATA-01",
    "GOVERNANCE-01",
    "ENV-01",
    "ERROR-01",
    "RETRY-01",
    "DOCS-01",
    "TEST-01",
    "OPS-01",
    "CAPACITY-01",
    "RELEASE-01",
    "ACTIVATION-01",
}

GA_GATES = {"PILOT-01", "SUPPORT-01", "DEPRECATION-01", "ROLLBACK-01"}
CONDITIONAL_GATES = {
    "webhooks": "WEBHOOK-01",
    "async_operations": "ASYNC-01",
    "protected_files": "FILE-01",
    "batch_operations": "BATCH-01",
    "official_sdk": "SDK-01",
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"manifest not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest is not valid JSON: {exc}") from None
    if not isinstance(value, dict):
        raise ValueError("manifest root must be a JSON object")
    return value


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def resolve_workspace_path(workspace: Path, raw_path: Any) -> tuple[Path | None, str | None]:
    if not non_empty_string(raw_path):
        return None, "path must be a non-empty string"
    path = Path(raw_path)
    candidate = path.resolve() if path.is_absolute() else (workspace / path).resolve()
    try:
        candidate.relative_to(workspace)
    except ValueError:
        return None, f"path escapes workspace: {raw_path}"
    if not candidate.is_file():
        return None, f"file does not exist: {raw_path}"
    return candidate, None


def validate(manifest: dict[str, Any], workspace: Path) -> list[str]:
    errors: list[str] = []

    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    mode = manifest.get("mode")
    status = manifest.get("status")
    if mode not in MODES:
        errors.append(f"mode must be one of: {', '.join(sorted(MODES))}")
    if status not in STATUSES:
        errors.append(f"status must be one of: {', '.join(sorted(STATUSES))}")

    assessment = manifest.get("assessment")
    if not isinstance(assessment, dict):
        errors.append("assessment must be an object")
        assessment = {}
    missing_assessment = sorted(REQUIRED_ASSESSMENT_FIELDS - assessment.keys())
    if missing_assessment:
        errors.append("assessment missing fields: " + ", ".join(missing_assessment))
    if assessment.get("fit_decision") not in FIT_DECISIONS:
        errors.append("assessment.fit_decision must be PRODUCTIZE, DISCOVERY_ONLY, or NOT_SUITABLE")
    for field, allowed_values in ASSESSMENT_ENUMS.items():
        if assessment.get(field) not in allowed_values:
            errors.append(f"assessment.{field} must be one of: {', '.join(sorted(allowed_values))}")
    rationale = assessment.get("rationale")
    if not isinstance(rationale, list) or not rationale or not all(non_empty_string(item) for item in rationale):
        errors.append("assessment.rationale must be a non-empty list of non-empty strings")

    if status == "ASSESSMENT_COMPLETE" and mode != "ASSESS":
        errors.append("ASSESSMENT_COMPLETE requires mode ASSESS")
    if status in READY_STATUSES and assessment.get("fit_decision") != "PRODUCTIZE":
        errors.append(f"{status} requires assessment.fit_decision PRODUCTIZE")
    if status in READY_STATUSES and assessment.get("repeatable_integration") is not True:
        errors.append(f"{status} requires repeatable_integration true")
    if status in READY_STATUSES and assessment.get("target_audience") not in EXTERNAL_AUDIENCES:
        errors.append(f"{status} requires an external customer or partner target_audience")
    if status in READY_STATUSES and assessment.get("business_capability_maturity") not in READY_MATURITY:
        errors.append(f"{status} requires stable or controlled_pilot business capability maturity")
    if status in READY_STATUSES and assessment.get("tenant_boundary") != "defined":
        errors.append(f"{status} requires tenant_boundary defined")
    if status in READY_STATUSES and assessment.get("data_action_authority") != "confirmed":
        errors.append(f"{status} requires data_action_authority confirmed")
    if status in READY_STATUSES and assessment.get("operational_owner") != "defined":
        errors.append(f"{status} requires operational_owner defined")

    if status not in READY_STATUSES:
        return errors

    features = manifest.get("features")
    if not isinstance(features, dict):
        errors.append("features must be an object for ready statuses")
        features = {}
    for feature in CONDITIONAL_GATES:
        if feature not in features or not isinstance(features.get(feature), bool):
            errors.append(f"features.{feature} must be true or false")

    deliverables = manifest.get("deliverables")
    if not isinstance(deliverables, list):
        errors.append("deliverables must be a list for ready statuses")
        deliverables = []
    delivered_kinds: set[str] = set()
    for index, item in enumerate(deliverables):
        label = f"deliverables[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        kind = item.get("kind")
        if not non_empty_string(kind):
            errors.append(f"{label}.kind must be a non-empty string")
            continue
        delivered_kinds.add(kind)
        _, path_error = resolve_workspace_path(workspace, item.get("path"))
        if path_error:
            errors.append(f"{label}: {path_error}")
    missing_deliverables = sorted(CORE_DELIVERABLES - delivered_kinds)
    if missing_deliverables:
        errors.append("missing deliverable kinds: " + ", ".join(missing_deliverables))

    gates = manifest.get("gates")
    if not isinstance(gates, list):
        errors.append("gates must be a list for ready statuses")
        gates = []

    gate_map: dict[str, dict[str, Any]] = {}
    for index, gate in enumerate(gates):
        label = f"gates[{index}]"
        if not isinstance(gate, dict):
            errors.append(f"{label} must be an object")
            continue
        gate_id = gate.get("id")
        if not non_empty_string(gate_id):
            errors.append(f"{label}.id must be a non-empty string")
            continue
        if gate_id in gate_map:
            errors.append(f"duplicate gate id: {gate_id}")
            continue
        gate_map[gate_id] = gate

        gate_status = gate.get("status")
        if gate_status not in {"pass", "fail", "not_applicable"}:
            errors.append(f"{label}.status must be pass, fail, or not_applicable")
            continue
        if gate_status != "pass":
            if not non_empty_string(gate.get("reason")):
                errors.append(f"{label}.reason is required when status is {gate_status}")
            continue
        evidence = gate.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{label}.evidence must be a non-empty list when status is pass")
            continue
        for evidence_index, evidence_item in enumerate(evidence):
            evidence_label = f"{label}.evidence[{evidence_index}]"
            if not isinstance(evidence_item, dict):
                errors.append(f"{evidence_label} must be an object")
                continue
            _, path_error = resolve_workspace_path(workspace, evidence_item.get("path"))
            if path_error:
                errors.append(f"{evidence_label}: {path_error}")
            if not non_empty_string(evidence_item.get("detail")):
                errors.append(f"{evidence_label}.detail must be a non-empty string")

    required_gates = set(PILOT_GATES)
    if status == "GA_PACKAGE_READY":
        required_gates.update(GA_GATES)
    for feature, gate_id in CONDITIONAL_GATES.items():
        if features.get(feature) is True:
            required_gates.add(gate_id)

    missing_gates = sorted(required_gates - gate_map.keys())
    if missing_gates:
        errors.append("missing required gates: " + ", ".join(missing_gates))

    for gate_id in sorted(required_gates & gate_map.keys()):
        if gate_map[gate_id].get("status") != "pass":
            errors.append(f"required gate {gate_id} must have status pass")

    for feature, gate_id in CONDITIONAL_GATES.items():
        if features.get(feature) is False and gate_id in gate_map:
            gate = gate_map[gate_id]
            if gate.get("status") != "not_applicable":
                errors.append(f"{gate_id} must be not_applicable when features.{feature} is false")
            elif not non_empty_string(gate.get("reason")):
                errors.append(f"{gate_id}.reason is required when feature is not applicable")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to the JSON delivery manifest")
    parser.add_argument("--workspace", type=Path, required=True, help="Common root for deliverables and evidence")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit machine-readable output")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    if not workspace.is_dir():
        result = {"valid": False, "status": None, "errors": [f"workspace is not a directory: {workspace}"]}
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json_output else result["errors"][0])
        return 1

    try:
        manifest = load_json(args.manifest.resolve())
    except ValueError as exc:
        result = {"valid": False, "status": None, "errors": [str(exc)]}
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json_output else str(exc))
        return 1

    errors = validate(manifest, workspace)
    status = manifest.get("status")
    valid = not errors and status != "EVIDENCE_BLOCKED"
    result = {"valid": valid, "status": status, "errors": errors}

    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        print("Productization manifest failed validation:")
        for error in errors:
            print(f"- {error}")
    elif status == "EVIDENCE_BLOCKED":
        print("Productization manifest is structurally valid but status is EVIDENCE_BLOCKED.")
    else:
        print(f"Productization manifest is valid: {status}")

    if errors:
        return 1
    if status == "EVIDENCE_BLOCKED":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
