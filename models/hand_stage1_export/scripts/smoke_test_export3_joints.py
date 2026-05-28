from __future__ import annotations

import json
from pathlib import Path

from export3_common import DOCS_DIR, HAND_XML, METADATA_DIR, CONTROLLED_JOINTS, joint_map, load_model, actual_qpos, write_json


REPORT_MD = DOCS_DIR / "export3_joint_smoke_test_report.md"
REPORT_JSON = METADATA_DIR / "export3_joint_smoke_test.json"


def main() -> int:
    try:
        mujoco, model, data = load_model(HAND_XML)
    except Exception as exc:
        report = {"load_success": False, "xml": str(HAND_XML), "error": f"{type(exc).__name__}: {exc}"}
        write_outputs(report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    joints = joint_map(model, mujoco)
    rows = []
    for name, jid in joints.items():
        if model.jnt_type[jid] != mujoco.mjtJoint.mjJNT_HINGE:
            continue
        adr = int(model.jnt_qposadr[jid])
        low, high = [float(value) for value in model.jnt_range[jid]]
        span = max(high - low, 0.0)
        positive = min(0.2, span * 0.25) if span > 0 else 0.0
        target = min(max(positive, low), high)
        data.qpos[:] = 0.0
        data.qvel[:] = 0.0
        baseline = actual_qpos(model, data, joints, [name]).get(name, 0.0)
        data.qpos[adr] = target
        mujoco.mj_forward(model, data)
        actual = float(data.qpos[adr])
        rows.append(
            {
                "joint": name,
                "range": [low, high],
                "target": target,
                "baseline": baseline,
                "actual": actual,
                "moved": abs(actual - baseline) > 1e-6,
                "expected_new_export3_thumb_joint": name in {"thumb_cmc_abd_joint", "thumb_cmc_flex_joint"},
            }
        )

    joint_names = [row["joint"] for row in rows]
    report = {
        "load_success": True,
        "xml": str(HAND_XML),
        "body_count": int(model.nbody),
        "joint_count": int(model.njnt),
        "hinge_count": len(rows),
        "actuator_count": int(model.nu),
        "geom_count": int(model.ngeom),
        "site_count": int(model.nsite),
        "mesh_count": int(model.nmesh),
        "joint_names": joint_names,
        "rows": rows,
        "all_hinges_moved": all(row["moved"] for row in rows),
        "thumb_cmc_abd_present": "thumb_cmc_abd_joint" in joint_names,
        "thumb_cmc_flex_present": "thumb_cmc_flex_joint" in joint_names,
        "old_thumb_cmc_joint_present": "thumb_cmc_joint" in joint_names,
        "wrist_2_joint_present_as_hinge": "wrist_2_joint" in joint_names,
        "missing_expected_controlled_joints": sorted(set(CONTROLLED_JOINTS) - set(joint_names)),
        "notes": [
            "This smoke test directly sets qpos for small positive hinge motion only.",
            "It verifies numerical mobility, not visual correctness or physical contact stability.",
            "export3 URDF has wrist_2_joint as fixed, so it is not expected in the hinge list unless the CAD export changes.",
        ],
    }
    write_outputs(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["all_hinges_moved"] and report["thumb_cmc_abd_present"] and report["thumb_cmc_flex_present"] else 1


def write_outputs(report: dict) -> None:
    write_json(REPORT_JSON, report)
    lines = [
        "# Export3 Joint Smoke Test Report",
        "",
        f"- XML: `{report.get('xml', HAND_XML)}`",
        f"- Load success: {'yes' if report.get('load_success') else 'no'}",
    ]
    if report.get("error"):
        lines.append(f"- Error: `{report['error']}`")
    lines.extend(
        [
            f"- Bodies / joints / hinges / actuators / geoms / sites / meshes: {report.get('body_count')} / {report.get('joint_count')} / {report.get('hinge_count')} / {report.get('actuator_count')} / {report.get('geom_count')} / {report.get('site_count')} / {report.get('mesh_count')}",
            f"- All hinge joints moved numerically: {'yes' if report.get('all_hinges_moved') else 'no'}",
            f"- `thumb_cmc_abd_joint` present: {'yes' if report.get('thumb_cmc_abd_present') else 'no'}",
            f"- `thumb_cmc_flex_joint` present: {'yes' if report.get('thumb_cmc_flex_present') else 'no'}",
            f"- Old `thumb_cmc_joint` present: {'yes' if report.get('old_thumb_cmc_joint_present') else 'no'}",
            f"- `wrist_2_joint` present as hinge: {'yes' if report.get('wrist_2_joint_present_as_hinge') else 'no'}",
            f"- Missing expected controlled joints: {report.get('missing_expected_controlled_joints') or 'None'}",
            "",
            "## Per Joint",
            "",
            "| Joint | Range | Target | Actual | Moved |",
            "|---|---|---:|---:|---|",
        ]
    )
    for row in report.get("rows", []):
        lines.append(f"| `{row['joint']}` | `{row['range']}` | {row['target']:.6f} | {row['actual']:.6f} | {'yes' if row['moved'] else 'no'} |")
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report.get("notes", []))
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
