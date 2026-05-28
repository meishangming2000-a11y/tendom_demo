from __future__ import annotations

import json
import os
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
URDF_PATH = ROOT / "robot.urdf"
METADATA_DIR = ROOT / "metadata"
DOCS_DIR = ROOT / "docs"


def main() -> int:
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    result = {
        "urdf_path": str(URDF_PATH),
        "mujoco_python_available": False,
        "load_attempted": False,
        "load_success": False,
        "error_type": None,
        "error": None,
        "model_summary": None,
        "notes": [],
    }

    try:
        import mujoco  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        result["notes"].append("mujoco Python package is not available in this environment.")
        write_outputs(result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 2

    result["mujoco_python_available"] = True
    result["load_attempted"] = True

    old_cwd = Path.cwd()
    try:
        os.chdir(ROOT)
        model = mujoco.MjModel.from_xml_path(str(URDF_PATH))
        result["load_success"] = True
        result["model_summary"] = {
            "nbody": int(model.nbody),
            "njnt": int(model.njnt),
            "nq": int(model.nq),
            "nv": int(model.nv),
            "nu": int(model.nu),
            "ngeom": int(model.ngeom),
            "nmesh": int(model.nmesh),
        }
        result["notes"].append("MuJoCo loaded the URDF path directly through mujoco.MjModel.from_xml_path.")
    except Exception as exc:  # pragma: no cover - environment dependent
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        result["traceback_tail"] = traceback.format_exc().splitlines()[-8:]
        result["notes"].append(
            "Direct MuJoCo URDF load failed; no forced MJCF conversion or structural rewrite was attempted."
        )
    finally:
        os.chdir(old_cwd)

    write_outputs(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["load_success"] else 1


def write_outputs(result: dict) -> None:
    (METADATA_DIR / "mujoco_load_check.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    status = "success" if result["load_success"] else "failed"
    lines = [
        "# MuJoCo URDF Load Smoke Test",
        "",
        f"- URDF: `{result['urdf_path']}`",
        f"- mujoco Python available: {'yes' if result['mujoco_python_available'] else 'no'}",
        f"- Load attempted: {'yes' if result['load_attempted'] else 'no'}",
        f"- Load status: {status}",
    ]
    if result["model_summary"]:
        lines.append(f"- Model summary: `{json.dumps(result['model_summary'], ensure_ascii=False)}`")
    if result["error"]:
        lines.append(f"- Error type: `{result['error_type']}`")
        lines.append(f"- Error: `{result['error']}`")
    if result["notes"]:
        lines.append("")
        lines.append("## Notes")
        lines.extend(f"- {note}" for note in result["notes"])
    lines.append("")
    (DOCS_DIR / "mujoco_load_check.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
