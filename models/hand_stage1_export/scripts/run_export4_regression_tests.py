#!/usr/bin/env python3
"""Run export4 tuned-scene regression tests."""

from __future__ import annotations

import json
import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from export4_wrist2_common import (
    DATA_DIR,
    DOCS_DIR,
    HAND_TUNED,
    METADATA_DIR,
    SCENE_TUNED,
    contact_summary,
    joint_names,
    load_model,
    set_ball_position,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
REPORT = DOCS_DIR / "export4_regression_test_report.md"
METADATA = METADATA_DIR / "export4_regression_test_results.json"
DATASET = DATA_DIR / "export4_scripted_smoke_dataset.npz"


def run_cmd(name: str, args: List[str], status_json: Path | None = None, status_key: str = "status") -> Dict[str, Any]:
    cmd = [sys.executable, *args]
    proc = subprocess.run(cmd, cwd=str(ROOT.parents[1]), text=True, capture_output=True)
    payload: Dict[str, Any] = {
        "name": name,
        "command": cmd,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
        "status_json": str(status_json) if status_json else None,
        "reported_status": None,
        "result": "PASS" if proc.returncode == 0 else "FAIL",
    }
    if status_json and status_json.exists():
        try:
            data = json.loads(status_json.read_text(encoding="utf-8"))
            payload["reported_status"] = data.get(status_key)
            if isinstance(payload["reported_status"], str) and payload["reported_status"].startswith("FAIL"):
                payload["result"] = "FAIL"
            payload["status_payload_excerpt"] = {
                key: data.get(key)
                for key in ("status", "conclusion", "open_static_penetration_status", "default_grasp_status", "mirror_grasp_status")
                if key in data
            }
        except Exception as exc:
            payload["result"] = "FAIL"
            payload["status_parse_error"] = str(exc)
    return payload


def model_load_test(scene: Path) -> Dict[str, Any]:
    try:
        mujoco, model, data = load_model(scene)
        return {
            "name": "model_load_test",
            "result": "PASS",
            "summary": {
                "scene": str(scene),
                "nbody": int(model.nbody),
                "njnt": int(model.njnt),
                "nu": int(model.nu),
                "ngeom": int(model.ngeom),
                "nsite": int(model.nsite),
            },
        }
    except Exception as exc:
        return {"name": "model_load_test", "result": "FAIL", "error": str(exc)}


def joint_smoke_test(scene: Path) -> Dict[str, Any]:
    try:
        mujoco, model, data = load_model(scene)
        rows = []
        for jid, name in enumerate(joint_names(model)):
            if name == "ball_freejoint" or int(model.jnt_type[jid]) == int(mujoco.mjtJoint.mjJNT_FREE):
                continue
            qadr = int(model.jnt_qposadr[jid])
            baseline = data.qpos.copy()
            for value in (-0.05, 0.05):
                data.qpos[:] = model.qpos0
                data.qvel[:] = 0.0
                low, high = model.jnt_range[jid]
                data.qpos[qadr] = float(np.clip(value, low, high))
                mujoco.mj_forward(model, data)
                if not np.all(np.isfinite(data.xpos)):
                    raise RuntimeError(f"non-finite xpos after moving {name}")
            rows.append({"joint": name, "qposadr": qadr, "range": model.jnt_range[jid].copy()})
            data.qpos[:] = baseline
        return {"name": "joint_smoke_test", "result": "PASS", "tested_joint_count": len(rows), "rows": rows}
    except Exception as exc:
        return {"name": "joint_smoke_test", "result": "FAIL", "error": str(exc)}


def collision_open_static_test(scene: Path, ball_position: list[float]) -> Dict[str, Any]:
    try:
        mujoco, model, data = load_model(scene)
        data.qpos[:] = model.qpos0
        data.qvel[:] = 0.0
        data.ctrl[:] = 0.0
        set_ball_position(model, data, mujoco, ball_position)
        mujoco.mj_forward(model, data)
        summary = contact_summary(model, data, mujoco)
        result = "PASS" if float(summary["max_penetration"]) < 0.005 else "FAIL"
        return {
            "name": "collision_open_static_test",
            "result": result,
            "ball_position": ball_position,
            "summary": summary,
        }
    except Exception as exc:
        return {"name": "collision_open_static_test", "result": "FAIL", "error": str(exc)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run export4 regression tests.")
    parser.add_argument("--scene", default=str(SCENE_TUNED))
    parser.add_argument("--hand", default=str(HAND_TUNED))
    parser.add_argument("--label", default="wrist2_collision_tuned")
    parser.add_argument("--ball-x", type=float, default=0.0)
    parser.add_argument("--ball-y", type=float, default=-0.1)
    parser.add_argument("--ball-z", type=float, default=0.21)
    parser.add_argument("--dataset", default=str(DATASET))
    parser.add_argument("--report", default=str(REPORT))
    parser.add_argument("--metadata", default=str(METADATA))
    args = parser.parse_args()
    scene = Path(args.scene).resolve()
    hand = Path(args.hand).resolve()
    label = args.label
    ball_position = [args.ball_x, args.ball_y, args.ball_z]
    report = Path(args.report).resolve()
    metadata = Path(args.metadata).resolve()
    dataset = Path(args.dataset).resolve()

    results: List[Dict[str, Any]] = []
    results.append(model_load_test(scene))
    results.append(joint_smoke_test(scene))
    results.append(
        run_cmd(
            "wrist_2_test",
            [
                str(SCRIPTS / "test_wrist2_joint_export4.py"),
                "--scene",
                str(scene),
                "--hand",
                str(hand),
                "--report",
                str(DOCS_DIR / f"export4_regression_{label}_wrist2_report.md"),
                "--metadata",
                str(METADATA_DIR / f"export4_regression_{label}_wrist2.json"),
                "--ball-x",
                str(args.ball_x),
                "--ball-y",
                str(args.ball_y),
                "--ball-z",
                str(args.ball_z),
            ],
            METADATA_DIR / f"export4_regression_{label}_wrist2.json",
        )
    )
    results.append(collision_open_static_test(scene, ball_position))
    results.append(
        run_cmd(
            "adapter_unit_test",
            [
                str(SCRIPTS / "test_export4_adapter_mapping.py"),
                "--scene",
                str(scene),
                "--report",
                str(DOCS_DIR / f"export4_regression_{label}_adapter_report.md"),
                "--metadata",
                str(METADATA_DIR / f"export4_regression_{label}_adapter.json"),
                "--ball-x",
                str(args.ball_x),
                "--ball-y",
                str(args.ball_y),
                "--ball-z",
                str(args.ball_z),
            ],
            METADATA_DIR / f"export4_regression_{label}_adapter.json",
        )
    )
    results.append(
        run_cmd(
            "scripted_grasp_task_smoke",
            [
                str(SCRIPTS / "run_export4_scripted_grasp_task.py"),
                "--scene",
                str(scene),
                "--ball-x",
                str(args.ball_x),
                "--ball-y",
                str(args.ball_y),
                "--ball-z",
                str(args.ball_z),
                "--save-rollout",
                "--report",
                str(DOCS_DIR / f"export4_regression_{label}_scripted_grasp_report.md"),
                "--metadata",
                str(METADATA_DIR / f"export4_regression_{label}_scripted_grasp.json"),
                "--rollout",
                str(METADATA_DIR / f"export4_regression_{label}_rollout.npz"),
            ],
            METADATA_DIR / f"export4_regression_{label}_scripted_grasp.json",
        )
    )
    if dataset.exists():
        results.append(
            run_cmd(
                "replay_smoke_dataset",
                [
                    str(SCRIPTS / "replay_export4_smoke_dataset.py"),
                    "--dataset",
                    str(dataset),
                    "--scene",
                    str(scene),
                    "--max-frames",
                    "120",
                    "--report",
                    str(DOCS_DIR / f"export4_regression_{label}_replay_report.md"),
                ],
                None,
            )
        )
    else:
        results.append({"name": "replay_smoke_dataset", "result": "SKIPPED", "reason": f"Dataset not found: {dataset}"})

    pass_count = sum(1 for row in results if row["result"] == "PASS")
    fail_count = sum(1 for row in results if row["result"] == "FAIL")
    skipped_count = sum(1 for row in results if row["result"] == "SKIPPED")
    can_enter_dataset_v0 = fail_count == 0
    if any(row["name"] == "scripted_grasp_task_smoke" and row["result"] == "FAIL" for row in results):
        can_enter_dataset_v0 = False
    overall = "PASS" if fail_count == 0 else "FAIL"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "label": label,
        "scene": str(scene),
        "hand": str(hand),
        "ball_position": ball_position,
        "overall": overall,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "skipped_count": skipped_count,
        "can_enter_dataset_collection_v0": bool(can_enter_dataset_v0),
        "results": results,
        "notes": [
            "Dataset collection v0 is allowed only when the selected scene/ball-side scripted grasp smoke passes.",
            "This runner does not modify CAD, STL, URDF joint tree, joint names, or current-baseline files.",
        ],
    }
    write_json(metadata, payload, "before_export4_regression_results")

    lines = [
        "# Export4 Regression Test Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Label: `{label}`\n",
        f"- Scene: `{scene}`\n",
        f"- Ball position: `{ball_position}`\n",
        f"- Overall: **{overall}**\n",
        f"- PASS / FAIL / SKIPPED: `{pass_count} / {fail_count} / {skipped_count}`\n",
        f"- Can enter dataset collection v0: `{can_enter_dataset_v0}`\n\n",
        "## Tests\n\n",
        "| test | result | status/excerpt |\n",
        "|---|---|---|\n",
    ]
    for row in results:
        excerpt = row.get("status_payload_excerpt") or row.get("summary") or row.get("reason") or row.get("error") or row.get("reported_status") or ""
        lines.append(f"| `{row['name']}` | **{row['result']}** | `{excerpt}` |\n")
    lines.extend(
        [
            "\n## Blocking Failure\n\n",
            "- If `scripted_grasp_task_smoke` is FAIL, the selected ball side/collision proxy is not ready for dataset collection v0.\n",
            "- If all tests pass, the selected experimental branch can be used for a tiny dataset-v0 dry run, but still not for training.\n\n",
            "## Next Fix Before Dataset v0\n\n",
            "1. Inspect visual frames for the selected scene and ball side.\n",
            "2. Confirm the selected ball side is the actual palm side.\n",
            "3. Keep training disabled until dataset quality checks are added.\n",
        ]
    )
    write_text(report, "".join(lines), "before_export4_regression_report")
    print(f"Regression overall: {overall}")
    print(f"PASS/FAIL/SKIPPED: {pass_count}/{fail_count}/{skipped_count}")
    print(f"Can enter dataset v0: {can_enter_dataset_v0}")
    print(f"Saved report: {report}")
    print(f"Saved metadata: {metadata}")


if __name__ == "__main__":
    main()
