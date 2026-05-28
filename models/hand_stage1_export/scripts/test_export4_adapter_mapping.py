#!/usr/bin/env python3
"""Unit tests for the export4 wrist2/collision-tuned adapter mapping."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from export4_wrist2_common import (
    DEFAULT_BALL_POSITION,
    DOCS_DIR,
    LONG_FINGER_TARGETS,
    METADATA_DIR,
    PRESHAPE_TARGETS,
    SCENE_TUNED,
    THUMB_SMOKE_TARGETS,
    actuator_names,
    contact_summary,
    ctrl_from_targets,
    fingertip_metrics,
    joint_names,
    json_ready,
    load_model,
    set_ball_position,
    site_pos,
    write_json,
    write_text,
)


DEFAULT_REPORT = DOCS_DIR / "export4_adapter_unit_test_report.md"
DEFAULT_METADATA = METADATA_DIR / "export4_adapter_unit_test.json"

EXPECTED_SITES = [
    "index_tip_site",
    "middle_tip_site",
    "ring_tip_site",
    "little_tip_site",
    "thumb_tip_site",
]


def build_obs(model, data, mujoco, ball_position: list[float]) -> Dict[str, Any]:
    contact = contact_summary(model, data, mujoco)
    tips = fingertip_metrics(model, data, mujoco)
    ball_joint = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "ball_freejoint")
    if ball_joint >= 0:
        qadr = int(model.jnt_qposadr[ball_joint])
        ball_pose = data.qpos[qadr : qadr + 7].copy()
    else:
        ball_pose = np.asarray([*ball_position, 1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    vector = np.concatenate(
        [
            data.qpos.copy(),
            data.qvel.copy(),
            np.concatenate([site_pos(model, data, mujoco, site) for site in EXPECTED_SITES]),
            ball_pose,
            np.asarray(
                [
                    contact["contact_count"],
                    contact["max_penetration"],
                    contact["ball_hand_contact_count"],
                    contact["ball_hand_max_penetration"],
                    tips["four_finger_avg_tip_ball_distance"],
                    tips["thumb_ball_distance"],
                    tips["thumb_index_distance"],
                ],
                dtype=np.float64,
            ),
        ]
    )
    return {
        "qpos": data.qpos.copy(),
        "qvel": data.qvel.copy(),
        "fingertip_site_positions": {site: site_pos(model, data, mujoco, site) for site in EXPECTED_SITES},
        "ball_pose": ball_pose,
        "contact_summary": contact,
        "fingertip_summary": tips,
        "vector": vector,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Test export4 adapter/action/obs mapping.")
    parser.add_argument("--scene", default=str(SCENE_TUNED))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--ball-x", type=float, default=DEFAULT_BALL_POSITION[0])
    parser.add_argument("--ball-y", type=float, default=DEFAULT_BALL_POSITION[1])
    parser.add_argument("--ball-z", type=float, default=DEFAULT_BALL_POSITION[2])
    args = parser.parse_args()

    scene = Path(args.scene).resolve()
    ball_position = [args.ball_x, args.ball_y, args.ball_z]
    mujoco, model, data = load_model(scene)
    set_ball_position(model, data, mujoco, ball_position)
    mujoco.mj_forward(model, data)

    joints = joint_names(model)
    actuators = actuator_names(model)
    action_dim = int(model.nu)
    obs0 = build_obs(model, data, mujoco, ball_position)
    reset_qpos = data.qpos.copy()

    target = {**PRESHAPE_TARGETS, **LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS}
    ctrl = ctrl_from_targets(model, target)
    data.ctrl[:] = ctrl
    ctrl_written = data.ctrl.copy()

    data.qpos[:] = model.qpos0
    data.qvel[:] = 0.0
    set_ball_position(model, data, mujoco, ball_position)
    mujoco.mj_forward(model, data)
    reset_qpos_again = data.qpos.copy()
    obs1 = build_obs(model, data, mujoco, ball_position)

    site_ids = {
        site: int(mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, site))
        for site in EXPECTED_SITES
    }
    tests: List[Dict[str, Any]] = []

    def check(name: str, condition: bool, detail: Any) -> None:
        tests.append({"name": name, "pass": bool(condition), "detail": detail})

    check("joint_name_list_nonempty", len(joints) > 0, len(joints))
    check("actuator_name_list_nonempty", len(actuators) > 0, len(actuators))
    check("action_dim_equals_actuator_count", action_dim == len(actuators), {"action_dim": action_dim, "actuators": len(actuators)})
    check("wrist_2_joint_in_joint_list", "wrist_2_joint" in joints, joints)
    check("wrist_2_joint_in_action_mapping", "wrist_2_joint_pos" in actuators, actuators)
    check("obs_contains_qpos", len(obs0["qpos"]) == model.nq, {"obs_qpos": len(obs0["qpos"]), "model_nq": int(model.nq)})
    check("obs_contains_qvel", len(obs0["qvel"]) == model.nv, {"obs_qvel": len(obs0["qvel"]), "model_nv": int(model.nv)})
    check("obs_contains_fingertips", all(site_ids[site] >= 0 for site in EXPECTED_SITES), site_ids)
    check("obs_contains_ball_pose", len(obs0["ball_pose"]) == 7, obs0["ball_pose"])
    check("obs_contains_contact_summary", "contact_count" in obs0["contact_summary"], obs0["contact_summary"])
    check("reset_qpos_consistent", bool(np.allclose(reset_qpos, reset_qpos_again)), float(np.max(np.abs(reset_qpos - reset_qpos_again))))
    check("scripted_target_writes_ctrl", bool(np.allclose(ctrl, ctrl_written)), {"ctrl_norm": float(np.linalg.norm(ctrl_written))})
    check("obs_vector_stable_length", len(obs0["vector"]) == len(obs1["vector"]), {"obs0": len(obs0["vector"]), "obs1": len(obs1["vector"])})

    status = "PASS" if all(item["pass"] for item in tests) else "FAIL"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(scene),
        "status": status,
        "joint_names": joints,
        "actuator_names": actuators,
        "action_dim": action_dim,
        "obs_dim": int(len(obs0["vector"])),
        "obs_fields": ["qpos", "qvel", "fingertip_site_positions", "ball_pose", "contact_summary"],
        "ball_position": ball_position,
        "tests": tests,
        "notes": [
            "This validates the adapter scaffold only. It does not imply training readiness or stable free-object grasp.",
            "wrist_2_joint is included in both joint and action mappings.",
        ],
    }
    write_json(Path(args.metadata).resolve(), payload, "before_export4_adapter_tests")

    lines = [
        "# Export4 Adapter Unit Test Report\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        f"- Scene: `{payload['scene']}`\n",
        f"- Status: **{status}**\n",
        f"- Action dim: `{action_dim}`\n",
        f"- Obs dim: `{payload['obs_dim']}`\n",
        f"- wrist_2 in action mapping: `{'wrist_2_joint_pos' in actuators}`\n\n",
        "## Tests\n\n",
        "| test | pass | detail |\n",
        "|---|---:|---|\n",
    ]
    for item in tests:
        lines.append(f"| `{item['name']}` | {item['pass']} | `{json_ready(item['detail'])}` |\n")
    lines.extend(
        [
            "\n## Notes\n\n",
            "- This is an adapter smoke/unit test, not a learning experiment.\n",
            "- Current unresolved grasp-side/contact issues are tracked separately in `collision_proxy_tuning_report.md`.\n",
        ]
    )
    write_text(Path(args.report).resolve(), "".join(lines), "before_export4_adapter_report")
    print(f"Adapter tests: {status}")
    print(f"Saved report: {Path(args.report).resolve()}")
    print(f"Saved metadata: {Path(args.metadata).resolve()}")


if __name__ == "__main__":
    main()
