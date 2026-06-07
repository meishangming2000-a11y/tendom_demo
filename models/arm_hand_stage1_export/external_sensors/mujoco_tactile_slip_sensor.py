#!/usr/bin/env python3
"""MuJoCo contact-derived tactile/slip sensor for Stage3.

This stays simulation-only. It converts MuJoCo contact state into the same
policy-visible tactile/slip fields used by the Stage3 task API.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np


SENSOR_ROOT = Path(__file__).resolve().parent
ROOT = SENSOR_ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stage3_sensor_abstractions import Stage3TactileConfig, build_tactile_observation
from stage3_sensor_aware_gentle_grasp_hold_task_api import Stage3Thresholds


HAND_KEYWORDS = ("palm", "finger", "thumb", "distal", "proximal", "wrist", "mcp", "hand_base")
ARM_KEYWORDS = ("base_link", "link_1", "link_2", "link_3", "ee_mount")


@dataclass
class TactileSlipSensorState:
    contact_persistence_steps: int = 0
    last_object_position: np.ndarray | None = None
    last_relative_object_position: np.ndarray | None = None
    had_contact_last_sample: bool = False


def name_for(model, mujoco, obj_type, idx: int, fallback: str) -> str:
    return mujoco.mj_id2name(model, obj_type, int(idx)) or fallback


def classify_region(names: Iterable[str]) -> str:
    joined = " ".join(str(name).lower() for name in names)
    for region in ("thumb", "index", "middle", "ring", "little"):
        if region in joined:
            return region
    if "palm" in joined or "hand_base" in joined or "wrist" in joined:
        return "palm"
    if "floor" in joined:
        return "support"
    if any(key in joined for key in ARM_KEYWORDS):
        return "arm"
    return "unknown"


class MujocoTactileSlipSensor:
    def __init__(
        self,
        model,
        mujoco,
        *,
        egg_body_name: str = "egg",
        config: Stage3TactileConfig | None = None,
        thresholds: Stage3Thresholds | None = None,
    ):
        self.model = model
        self.mujoco = mujoco
        self.config = config or Stage3TactileConfig()
        self.thresholds = thresholds or Stage3Thresholds()
        self.egg_body_name = egg_body_name
        self.egg_body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, egg_body_name)
        self.palm_body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "palm_link")
        if self.egg_body_id < 0:
            raise ValueError(f"Unknown egg body: {egg_body_name!r}")
        self.state = TactileSlipSensorState()

    def reset(self, data=None) -> None:
        self.state.contact_persistence_steps = 0
        self.state.had_contact_last_sample = False
        if data is not None:
            self.state.last_object_position = data.xpos[self.egg_body_id].copy()
            self.state.last_relative_object_position = self.relative_object_position(data)
        else:
            self.state.last_object_position = None
            self.state.last_relative_object_position = None

    def contact_summary(self, data) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        max_penetration = 0.0
        egg_hand = 0
        egg_floor = 0
        egg_arm = 0
        regions: dict[str, int] = {}
        for idx in range(data.ncon):
            c = data.contact[idx]
            geoms = [int(c.geom1), int(c.geom2)]
            names: list[str] = []
            body_ids: list[int] = []
            for geom_id in geoms:
                body_id = int(self.model.geom_bodyid[geom_id])
                body_ids.append(body_id)
                names.append(name_for(self.model, self.mujoco, self.mujoco.mjtObj.mjOBJ_GEOM, geom_id, f"geom_{geom_id}"))
                names.append(name_for(self.model, self.mujoco, self.mujoco.mjtObj.mjOBJ_BODY, body_id, f"body_{body_id}"))
            joined = " ".join(names).lower()
            has_egg = "egg" in joined or self.egg_body_id in body_ids
            pen = max(0.0, -float(c.dist))
            if has_egg:
                max_penetration = max(max_penetration, pen)
                hand_hit = any(key in joined for key in HAND_KEYWORDS)
                floor_hit = "floor" in joined
                arm_hit = any(key in joined for key in ARM_KEYWORDS)
                if hand_hit:
                    egg_hand += 1
                if floor_hit:
                    egg_floor += 1
                if arm_hit:
                    egg_arm += 1
                region = classify_region(names)
                regions[region] = regions.get(region, 0) + 1
            rows.append(
                {
                    "names": names,
                    "has_egg": bool(has_egg),
                    "penetration": float(pen),
                    "dist": float(c.dist),
                    "pos": np.asarray(c.pos).copy(),
                }
            )
        rows.sort(key=lambda row: float(row["penetration"]), reverse=True)
        return {
            "contact_count": int(data.ncon),
            "egg_hand_contact_count": int(egg_hand),
            "egg_floor_contact_count": int(egg_floor),
            "egg_arm_contact_count": int(egg_arm),
            "egg_contact_regions": sorted(regions),
            "egg_contact_region_counts": regions,
            "max_penetration": float(max_penetration),
            "top_contacts": rows[:12],
        }

    def relative_object_position(self, data) -> np.ndarray:
        egg_pos = data.xpos[self.egg_body_id].copy()
        if self.palm_body_id >= 0:
            return egg_pos - data.xpos[self.palm_body_id].copy()
        return egg_pos

    def object_velocity(self, data, *, contact_present: bool) -> np.ndarray:
        current = data.xpos[self.egg_body_id].copy()
        current_relative = self.relative_object_position(data)
        if not contact_present:
            self.state.last_object_position = current
            self.state.last_relative_object_position = current_relative
            self.state.had_contact_last_sample = False
            return np.zeros(3, dtype=np.float64)
        if not self.state.had_contact_last_sample or self.state.last_relative_object_position is None:
            velocity = np.zeros(3, dtype=np.float64)
        else:
            dt = max(float(self.model.opt.timestep), 1e-9)
            velocity = (current_relative - self.state.last_relative_object_position) / dt
        self.state.last_object_position = current
        self.state.last_relative_object_position = current_relative
        self.state.had_contact_last_sample = True
        return velocity

    def sample(self, data) -> dict[str, Any]:
        contact = self.contact_summary(data)
        contact_present = int(contact["egg_hand_contact_count"]) > 0
        if contact_present:
            self.state.contact_persistence_steps += 1
        else:
            self.state.contact_persistence_steps = 0
        velocity = self.object_velocity(data, contact_present=contact_present)
        tactile = build_tactile_observation(
            contact_summary=contact,
            object_velocity=velocity,
            contact_persistence_steps=int(self.state.contact_persistence_steps),
            success_max_slip_score=float(self.thresholds.success_max_slip_score),
            success_max_crush_risk=float(self.thresholds.success_max_crush_risk),
            failure_max_penetration_m=float(self.thresholds.failure_max_penetration_m),
            config=self.config,
        )
        tactile.update(
            {
                "egg_hand_contact_count": int(contact["egg_hand_contact_count"]),
                "egg_floor_contact_count": int(contact["egg_floor_contact_count"]),
                "egg_arm_contact_count": int(contact["egg_arm_contact_count"]),
                "egg_contact_region_counts": dict(contact["egg_contact_region_counts"]),
                "object_velocity_world": velocity,
                "max_penetration": float(contact["max_penetration"]),
                "sensor_source": "mujoco_contact_derived_tactile_slip",
            }
        )
        return tactile
