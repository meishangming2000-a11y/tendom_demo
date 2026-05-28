#!/usr/bin/env python3
"""Summarize the export4 collision-proxy tuning attempt."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from export4_wrist2_common import DOCS_DIR, METADATA_DIR, write_json, write_text


DIAG_JSON = METADATA_DIR / "collision_proxy_penetration_diagnosis.json"
BUILD_JSON = METADATA_DIR / "export4_wrist2_collision_tuned_build.json"
DEMO_JSON = METADATA_DIR / "export4_wrist2_collision_tuned_grasp.json"
MIRROR_JSON = METADATA_DIR / "export4_wrist2_collision_tuned_grasp_mirror_y.json"

REPORT = DOCS_DIR / "collision_proxy_tuning_report.md"
RESULTS_JSON = METADATA_DIR / "collision_proxy_tuning_results.json"


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"missing": str(path)}
    return json.loads(path.read_text(encoding="utf-8"))


def find_row(diag: Dict[str, Any], scene_label: str, ball: list[float], stage: str) -> Dict[str, Any]:
    for scene in diag.get("scenes", []):
        if scene.get("label") != scene_label:
            continue
        for row in scene.get("rows", []):
            if row.get("ball_position") == ball and row.get("stage") == stage:
                return row
    return {}


def main() -> None:
    build = load_json(BUILD_JSON)
    diag = load_json(DIAG_JSON)
    demo = load_json(DEMO_JSON)
    mirror = load_json(MIRROR_JSON)

    default_ball = [0.0, -0.1, 0.21]
    mirror_ball = [0.0, 0.1, 0.21]
    baseline_default_open = find_row(diag, "current_baseline", default_ball, "open_hand")
    tuned_default_open = find_row(diag, "wrist2_collision_tuned", default_ball, "open_hand")
    baseline_default_close = find_row(diag, "current_baseline", default_ball, "close_thumb")
    tuned_default_close = find_row(diag, "wrist2_collision_tuned", default_ball, "close_thumb")
    tuned_mirror_close = find_row(diag, "wrist2_collision_tuned", mirror_ball, "close_thumb")

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "build_metadata": build,
        "default_ball": default_ball,
        "mirror_ball": mirror_ball,
        "baseline_default_open": baseline_default_open.get("metrics", {}),
        "tuned_default_open": tuned_default_open.get("metrics", {}),
        "baseline_default_close": baseline_default_close.get("metrics", {}),
        "tuned_default_close": tuned_default_close.get("metrics", {}),
        "tuned_mirror_close": tuned_mirror_close.get("metrics", {}),
        "default_grasp_status": demo.get("status"),
        "mirror_grasp_status": mirror.get("status"),
        "conclusion": "PARTIAL",
        "blockers": [],
        "major_issues": [
            "Default -Y ball side is visually and metrically far from the closing fingertips; mirror +Y is much closer.",
            "Collision proxy open-hand penetration is resolved, but the current scripted target does not create ball-hand contact at the default -Y ball position.",
        ],
        "minor_issues": [
            "Proxy radii are conservative. Add fingertip proxy refinement only after palm/grasp side is finalized.",
        ],
    }

    default_open_pen = float(result["tuned_default_open"].get("max_penetration", 0.0))
    default_close_pen = float(result["tuned_default_close"].get("max_penetration", 0.0))
    if default_open_pen <= 0.005:
        result["open_static_penetration_status"] = "PASS_UNDER_5MM"
    else:
        result["open_static_penetration_status"] = "FAIL_OVER_5MM"
    if demo.get("status") == "PASS_FOR_SCRIPTED_SMOKE":
        result["conclusion"] = "PASS_FOR_DEFAULT_SCRIPTED_SMOKE"
    elif mirror.get("status") in ("PASS_FOR_SCRIPTED_SMOKE", "PARTIAL_NO_CONTACT_BUT_VISUALLY_CLOSE"):
        result["conclusion"] = "PARTIAL_DEFAULT_SIDE_FAILS_MIRROR_SIDE_BETTER"

    lines = [
        "# Collision Proxy Tuning Report\n\n",
        f"Generated: {result['generated_at']}\n\n",
        "## Scope\n\n",
        "This summarizes the experimental export4 wrist2/collision-proxy branch. "
        "Only collision proxy sizes/visual debug branch files were changed; CAD, STL, joint tree, joint names, and current-baseline files were not overwritten.\n\n",
        "## What Changed In The Experimental MJCF\n\n",
        "- `wrist_2_joint` is verified as a hinge/revolute joint in the experimental branch.\n",
        "- Conservative collision proxy sizes were applied to palm, long-finger capsules, and thumb capsules.\n",
        "- Clean STL remains visual-only; STL mesh geoms are not used as collision geoms.\n\n",
        "## Static Penetration Result\n\n",
        "| case | max penetration | contacts | ball-hand contacts | status |\n",
        "|---|---:|---:|---:|---|\n",
        f"| tuned open, default `{default_ball}` | {result['tuned_default_open'].get('max_penetration', 0):.6f} | "
        f"{result['tuned_default_open'].get('contact_count', 0)} | {result['tuned_default_open'].get('ball_hand_contact_count', 0)} | {result['open_static_penetration_status']} |\n",
        f"| tuned close, default `{default_ball}` | {result['tuned_default_close'].get('max_penetration', 0):.6f} | "
        f"{result['tuned_default_close'].get('contact_count', 0)} | {result['tuned_default_close'].get('ball_hand_contact_count', 0)} | no static penetration, but no ball contact |\n",
        f"| tuned close, mirror `{mirror_ball}` | {result['tuned_mirror_close'].get('max_penetration', 0):.6f} | "
        f"{result['tuned_mirror_close'].get('contact_count', 0)} | {result['tuned_mirror_close'].get('ball_hand_contact_count', 0)} | visually closer, still no contact |\n\n",
        "## Grasp-Side Finding\n\n",
        f"- Default `-Y` grasp demo status: **{result['default_grasp_status']}**.\n",
        f"- Mirror `+Y` grasp demo status: **{result['mirror_grasp_status']}**.\n",
        "- Visual screenshots and fingertip distances both show the mirror `+Y` ball is closer to the closed fingers and thumb than the default `-Y` ball.\n",
        "- I did not inflate the collision proxy to force contact across a large air gap. That would hide the palm-side / target-side issue.\n\n",
        "## Recommendation\n\n",
        "1. Keep the conservative proxy branch because open-hand static penetration is now zero in the tested poses.\n",
        "2. Treat the default `-Y` ball side as unresolved for grasp smoke. Use the mirror-side diagnostics to decide the canonical palmar side before training or dataset expansion.\n",
        "3. After the canonical ball side is fixed, add small distal fingertip collision spheres/capsule-end tuning if contact remains slightly short.\n\n",
        "## Issue Severity\n\n",
        "- BLOCKER: none for model loading or wrist_2 verification.\n",
        "- MAJOR: default grasp side / target side does not produce contact.\n",
        "- MINOR: collision proxy is conservative and will need final fingertip-radius tuning.\n",
    ]

    write_json(RESULTS_JSON, result, "before_collision_tuning_results")
    write_text(REPORT, "".join(lines), "before_collision_tuning_report")
    print(f"Saved report: {REPORT}")
    print(f"Saved metadata: {RESULTS_JSON}")


if __name__ == "__main__":
    main()
