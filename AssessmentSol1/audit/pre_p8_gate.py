from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def run_gate() -> dict:
    issues: list[dict] = []

    p4_qa = ROOT / "abt" / "artifacts" / "p4_qa_summary.json"
    p4_manifest = ROOT / "abt" / "artifacts" / "p4_artifact_manifest.json"
    if not p4_qa.exists() or not p4_manifest.exists():
        issues.append(
            {
                "id": "P4_RUNTIME_GATE",
                "severity": "BLOCKER",
                "status": "FAIL",
                "reason": "Prompt-4 runtime QA/manifest are absent.",
            }
        )
    else:
        qa = load_json(p4_qa)
        if qa.get("status") != "PASS":
            issues.append(
                {
                    "id": "P4_RUNTIME_GATE",
                    "severity": "BLOCKER",
                    "status": "FAIL",
                    "reason": f"p4_qa_summary status={qa.get('status')}",
                }
            )

    target = load_json(ROOT / "target" / "target_contract.json")
    if target.get("primary", {}).get("id") != "T1_FIRST_INQUIRY_EVENTUAL_SCHEDULED_VISIT_V1":
        issues.append({"id": "TARGET_FREEZE", "severity": "BLOCKER", "status": "FAIL"})

    split = load_json(ROOT / "splits" / "split_contract.json")
    if split.get("version") != "SPLIT_V1_T1_CALENDAR_FROZEN_2026-08-30":
        issues.append({"id": "SPLIT_FREEZE", "severity": "BLOCKER", "status": "FAIL"})

    ablation = load_json(ROOT / "features" / "ablation_plan.json")
    if not ablation.get("frozen_before_training"):
        issues.append({"id": "ABLATION_FREEZE", "severity": "BLOCKER", "status": "FAIL"})

    model = load_json(ROOT / "models" / "lead_quality" / "FROZEN_MODEL_CONFIG.json")
    if model.get("status") != "FROZEN":
        issues.append({"id": "T1_MODEL_FREEZE", "severity": "BLOCKER", "status": "FAIL"})
    if model.get("model_family") != "BASE_RATE" or model.get("calibrator", {}).get("method") != "RAW":
        issues.append(
            {
                "id": "T1_AUDIT_DECISION",
                "severity": "BLOCKER",
                "status": "FAIL",
                "reason": "Expected audited champion BASE_RATE + RAW.",
            }
        )

    holdout = model.get("holdout_integrity", {})
    if holdout.get("status") != "CONSUMED_BY_METHOD_INCIDENT_BEFORE_FREEZE":
        issues.append(
            {
                "id": "HOLDOUT_STATUS",
                "severity": "HIGH",
                "status": "FAIL",
                "reason": "Holdout incident must remain explicit.",
            }
        )

    status = "PASS" if not issues else "BLOCKED"
    return {"gate": "PRE_P8", "status": status, "issues": issues}


if __name__ == "__main__":
    result = run_gate()
    out = ROOT / "audit" / "PRE_P8_GATE_STATUS.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 2)
