#!/usr/bin/env python3
"""Compile and inspect a MuJoCo model contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import mujoco
import numpy as np


OBJ_TYPES = {
    "body": mujoco.mjtObj.mjOBJ_BODY,
    "site": mujoco.mjtObj.mjOBJ_SITE,
    "joint": mujoco.mjtObj.mjOBJ_JOINT,
    "actuator": mujoco.mjtObj.mjOBJ_ACTUATOR,
    "equality": mujoco.mjtObj.mjOBJ_EQUALITY,
}


def _name_exists(model: mujoco.MjModel, obj_type: str, name: str) -> bool:
    return mujoco.mj_name2id(model, OBJ_TYPES[obj_type], name) >= 0


def _collect_names(model: mujoco.MjModel, obj_type: str, count: int) -> List[str]:
    names = []
    for idx in range(count):
        name = mujoco.mj_id2name(model, OBJ_TYPES[obj_type], idx)
        if name:
            names.append(name)
    return names


def build_report(args: argparse.Namespace) -> Dict[str, Any]:
    model_path = Path(args.model).resolve()
    model = mujoco.MjModel.from_xml_path(str(model_path))
    data = mujoco.MjData(model)

    for _ in range(max(0, int(args.steps))):
        if model.nu:
            data.ctrl[:] = np.zeros(model.nu)
        mujoco.mj_step(model, data)

    required = {
        "body": list(args.require_body),
        "site": list(args.require_site),
        "joint": list(args.require_joint),
        "actuator": list(args.require_actuator),
        "equality": list(args.require_equality),
    }
    missing = {
        obj_type: [
            name for name in names
            if not _name_exists(model, obj_type, name)
        ]
        for obj_type, names in required.items()
    }

    report = {
        "model": str(model_path),
        "compiled": True,
        "steps": int(args.steps),
        "counts": {
            "nq": int(model.nq),
            "nv": int(model.nv),
            "nu": int(model.nu),
            "nbody": int(model.nbody),
            "ngeom": int(model.ngeom),
            "nsite": int(model.nsite),
            "njnt": int(model.njnt),
            "neq": int(model.neq),
        },
        "required": required,
        "missing": missing,
        "ok": not any(missing.values()),
    }

    if args.include_names:
        report["names"] = {
            "bodies": _collect_names(model, "body", model.nbody),
            "sites": _collect_names(model, "site", model.nsite),
            "joints": _collect_names(model, "joint", model.njnt),
            "actuators": _collect_names(model, "actuator", model.nu),
            "equalities": _collect_names(model, "equality", model.neq),
        }

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile and inspect a MuJoCo model")
    parser.add_argument("--model", required=True, help="Path to an MJCF XML model")
    parser.add_argument("--steps", type=int, default=5, help="Zero-control steps to simulate after compile")
    parser.add_argument("--require-body", action="append", default=[], help="Required body name")
    parser.add_argument("--require-site", action="append", default=[], help="Required site name")
    parser.add_argument("--require-joint", action="append", default=[], help="Required joint name")
    parser.add_argument("--require-actuator", action="append", default=[], help="Required actuator name")
    parser.add_argument("--require-equality", action="append", default=[], help="Required equality name")
    parser.add_argument("--include-names", action="store_true", help="Include discovered names in the report")
    parser.add_argument("--report", default="", help="Optional JSON report path")
    parser.add_argument("--indent", type=int, default=2, help="JSON indent")
    args = parser.parse_args()

    report = build_report(args)
    text = json.dumps(report, indent=args.indent, ensure_ascii=False)
    print(text)

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(text + "\n", encoding="utf-8")

    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
