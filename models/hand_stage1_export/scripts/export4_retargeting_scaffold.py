#!/usr/bin/env python3
"""Create a semantic retargeting scaffold for export4.

This script does not perform real retargeting. It only defines keypoints,
action groups, and semantic aliases for later human/Shadow -> export4 mapping.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from export4_task_api import load_model
from export4_wrist2_common import DOCS_DIR, METADATA_DIR, SCENE_TUNED, json_ready, write_json, write_text


DOC = DOCS_DIR / "export4_retargeting_scaffold.md"
META = METADATA_DIR / "export4_semantic_joint_aliases.json"


def build_mapping() -> Dict[str, Any]:
    api = load_model(SCENE_TUNED)
    joints = set(api.get_joint_names())
    keypoints = {
        "palm_reference": {
            "body": "palm_link",
            "note": "Use palm_link pose as the current palm reference. TODO: finalize palmar/dorsal side convention.",
        },
        "index_tip": {"site": "index_tip_site"},
        "middle_tip": {"site": "middle_tip_site"},
        "ring_tip": {"site": "ring_tip_site"},
        "little_tip": {"site": "little_tip_site"},
        "thumb_tip": {"site": "thumb_tip_site"},
    }
    rows: List[Dict[str, str]] = [
        {
            "semantic_name": "wrist_yaw_or_roll_1",
            "current_joint_name": "wrist_1_joint",
            "actual_motion_semantics": "wrist root DOF, exact anatomical meaning TBD",
            "note": "Keep as explicit wrist group for Shadow/human alignment.",
        },
        {
            "semantic_name": "wrist_yaw_or_roll_2",
            "current_joint_name": "wrist_2_joint",
            "actual_motion_semantics": "wrist/palm active hinge, confirmed should be revolute",
            "note": "Included in action mapping after wrist2 experiment.",
        },
    ]
    for finger in ("index", "middle", "ring", "little"):
        rows.extend(
            [
                {
                    "semantic_name": f"{finger}_spread",
                    "current_joint_name": f"{finger}_mcp_flex_joint",
                    "actual_motion_semantics": "spread / abduction-adduction",
                    "note": "Name is misleading; do not rename yet. Semantic alias used for retargeting.",
                },
                {
                    "semantic_name": f"{finger}_mcp_flexion",
                    "current_joint_name": f"{finger}_mcp_abd_joint",
                    "actual_motion_semantics": "likely primary MCP flexion for current export4",
                    "note": "Name may be semantically reversed relative to CAD labels; verify with visual audit before training.",
                },
                {
                    "semantic_name": f"{finger}_pip_flexion",
                    "current_joint_name": f"{finger}_pip_joint",
                    "actual_motion_semantics": "PIP flexion",
                    "note": "Current scripted close uses negative target sign.",
                },
                {
                    "semantic_name": f"{finger}_dip_flexion",
                    "current_joint_name": f"{finger}_dip_joint",
                    "actual_motion_semantics": "DIP flexion",
                    "note": "Current scripted close uses negative target sign.",
                },
            ]
        )
    rows.extend(
        [
            {
                "semantic_name": "thumb_cmc_abduction",
                "current_joint_name": "thumb_cmc_abd_joint",
                "actual_motion_semantics": "thumb first CMC DOF; axis confirmed through center in SolidWorks",
                "note": "Sign selected by scripted target; do not flip axis automatically.",
            },
            {
                "semantic_name": "thumb_cmc_flexion",
                "current_joint_name": "thumb_cmc_joint",
                "actual_motion_semantics": "thumb second CMC/flexion DOF in export4 naming",
                "note": "Export3/4 naming kept as `thumb_cmc_joint`; semantic alias records actual role.",
            },
            {
                "semantic_name": "thumb_mcp_flexion",
                "current_joint_name": "thumb_mcp_joint",
                "actual_motion_semantics": "thumb MCP flexion",
                "note": "Axis previously confirmed by user as mechanically credible.",
            },
            {
                "semantic_name": "thumb_ip_flexion",
                "current_joint_name": "thumb_ip_joint",
                "actual_motion_semantics": "thumb IP flexion",
                "note": "Target sign remains scripted/audited.",
            },
        ]
    )
    for row in rows:
        row["exists_in_model"] = str(row["current_joint_name"] in joints)
    groups = {
        "wrist_joints": ["wrist_1_joint", "wrist_2_joint"],
        "four_finger_spread_joints_currently_named_mcp_flex": [f"{finger}_mcp_flex_joint" for finger in ("index", "middle", "ring", "little")],
        "four_finger_flex_joints": [
            joint
            for finger in ("index", "middle", "ring", "little")
            for joint in (f"{finger}_mcp_abd_joint", f"{finger}_pip_joint", f"{finger}_dip_joint")
        ],
        "thumb_joints": ["thumb_cmc_abd_joint", "thumb_cmc_joint", "thumb_mcp_joint", "thumb_ip_joint"],
    }
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(SCENE_TUNED),
        "keypoints": keypoints,
        "action_groups": groups,
        "semantic_joint_aliases": rows,
        "notes": [
            "This is a scaffold only, not real human/Shadow retargeting.",
            "Four-finger *_mcp_flex_joint names are retained but aliased as spread/abd-add.",
            "Four-finger *_mcp_abd_joint may be the primary MCP flexion in current export4.",
            "TODO: finalize palm-side convention before mapping video hand pose to ball-relative targets.",
        ],
    }


def write_doc(payload: Dict[str, Any]) -> None:
    lines = [
        "# Export4 Retargeting Scaffold\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "This is only a semantic mapping scaffold for future human/Shadow -> export4 retargeting. "
        "It does not consume video/glove data, optimize targets, train a model, or rename joints.\n\n",
        "## Export4 Keypoints\n\n",
        "| semantic keypoint | model object | note |\n",
        "|---|---|---|\n",
    ]
    for name, item in payload["keypoints"].items():
        obj = item.get("site") or item.get("body")
        lines.append(f"| `{name}` | `{obj}` | {item.get('note', '')} |\n")
    lines.extend(["\n## Action Groups\n\n"])
    for group, joints in payload["action_groups"].items():
        lines.append(f"- `{group}`: `{joints}`\n")
    lines.extend(
        [
            "\n## Semantic Joint Alias Table\n\n",
            "| semantic name | current joint name | actual motion semantics | exists | note |\n",
            "|---|---|---|---:|---|\n",
        ]
    )
    for row in payload["semantic_joint_aliases"]:
        lines.append(
            f"| `{row['semantic_name']}` | `{row['current_joint_name']}` | "
            f"{row['actual_motion_semantics']} | {row['exists_in_model']} | {row['note']} |\n"
        )
    lines.extend(
        [
            "\n## TODO Before Real Retargeting\n\n",
            "1. Finalize canonical palmar side and ball-side convention.\n",
            "2. Decide whether Shadow/video coordinates map to fingertip positions, joint angles, or a hybrid objective.\n",
            "3. Add quality checks for physically impossible poses, joint-limit clipping, and self-collision.\n",
            "4. Keep this as semantic aliasing; do not rename export4 joints until CAD/URDF naming is deliberately revised.\n",
        ]
    )
    write_text(DOC, "".join(lines), "before_export4_retargeting_scaffold")


def main() -> None:
    payload = build_mapping()
    write_json(META, payload, "before_export4_semantic_aliases")
    write_doc(payload)
    print(f"Saved retargeting scaffold: {DOC}")
    print(f"Saved semantic aliases: {META}")


if __name__ == "__main__":
    main()
