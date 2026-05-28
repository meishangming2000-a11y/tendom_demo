from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from export3_common import ARCHIVE_DIR, DOCS_DIR, MJCF_DIR


SOURCE_HAND = MJCF_DIR / "hand_stage1_export3.xml"
SOURCE_SCENE = MJCF_DIR / "scene_ball_export3.xml"
TUNED_HAND = MJCF_DIR / "hand_stage1_export3_thumb_limit_tuned.xml"
TUNED_SCENE = MJCF_DIR / "scene_ball_export3_thumb_limit_tuned.xml"
REPORT = DOCS_DIR / "export3_thumb_limit_tuned_model_report.md"

THUMB_RANGES = {
    "thumb_cmc_abd_joint": (-1.2, 1.2),
    "thumb_cmc_flex_joint": (-1.2, 1.2),
    "thumb_mcp_joint": (-0.2, 1.4),
    "thumb_ip_joint": (-0.2, 1.2),
}


def fmt_range(values: tuple[float, float]) -> str:
    return f"{values[0]:g} {values[1]:g}"


def backup(path: Path, stamp: str) -> Path | None:
    if not path.exists():
        return None
    target_dir = ARCHIVE_DIR / f"thumb_limit_tuned_overwrite_{stamp}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / path.name
    shutil.copy2(path, target)
    return target


def tune_hand_xml() -> dict:
    tree = ET.parse(SOURCE_HAND)
    root = tree.getroot()
    changed_joints = {}
    changed_actuators = {}
    for joint in root.findall(".//joint"):
        name = joint.get("name")
        if name in THUMB_RANGES:
            old = joint.get("range")
            new = fmt_range(THUMB_RANGES[name])
            joint.set("limited", "true")
            joint.set("range", new)
            changed_joints[name] = {"old_range": old, "new_range": new}
    for actuator in root.findall(".//position"):
        joint_name = actuator.get("joint")
        if joint_name in THUMB_RANGES:
            old = actuator.get("ctrlrange")
            new = fmt_range(THUMB_RANGES[joint_name])
            actuator.set("ctrllimited", "true")
            actuator.set("ctrlrange", new)
            changed_actuators[actuator.get("name") or joint_name] = {
                "joint": joint_name,
                "old_ctrlrange": old,
                "new_ctrlrange": new,
            }
    tree.write(TUNED_HAND, encoding="utf-8", xml_declaration=True)
    return {"joints": changed_joints, "actuators": changed_actuators}


def tune_scene_xml() -> None:
    tree = ET.parse(SOURCE_SCENE)
    root = tree.getroot()
    root.set("model", "hand_stage1_export3_thumb_limit_tuned_ball_scene")
    include = root.find(".//include")
    if include is None:
        raise RuntimeError(f"No include element found in {SOURCE_SCENE}")
    include.set("file", TUNED_HAND.name)
    tree.write(TUNED_SCENE, encoding="utf-8", xml_declaration=True)


def write_report(payload: dict) -> None:
    lines = [
        "# Export3 Thumb Limit Tuned Model Report",
        "",
        "Status: experimental MJCF variant. Main export3 model is not overwritten.",
        "",
        f"- Source hand MJCF: `{SOURCE_HAND}`",
        f"- Source scene MJCF: `{SOURCE_SCENE}`",
        f"- Tuned hand MJCF: `{TUNED_HAND}`",
        f"- Tuned scene MJCF: `{TUNED_SCENE}`",
        "",
        "## User-Confirmed Mechanical Semantics",
        "",
        "- `D18d12H4.STEP` and `Trapezium3.STEP` are fixed root parts under `thumb_root_connector_link`.",
        "- `Trapezium1.STEP` is the first moving CMC-abduction link: `thumb_trapezium1_link`.",
        "- `Os metacarpale I 3.STEP` is after the second CMC joint: `thumb_metacarpal_link`.",
        "- `thumb_cmc_abd_joint` must allow negative angles because negative direction improves opposition.",
        "- `thumb_mcp_axis` has been confirmed mechanically credible in SolidWorks.",
        "",
        "## Changed Joint Ranges",
        "",
        "| Joint | Old range | New range |",
        "|---|---:|---:|",
    ]
    for name, item in payload["changes"]["joints"].items():
        lines.append(f"| `{name}` | `{item['old_range']}` | `{item['new_range']}` |")
    lines.extend(["", "## Changed Actuator Control Ranges", "", "| Actuator | Joint | Old ctrlrange | New ctrlrange |", "|---|---|---:|---:|"])
    for name, item in payload["changes"]["actuators"].items():
        lines.append(f"| `{name}` | `{item['joint']}` | `{item['old_ctrlrange']}` | `{item['new_ctrlrange']}` |")
    lines.extend(
        [
            "",
            "## Constraints",
            "",
            "- No CAD edits.",
            "- No STL edits.",
            "- No link tree edits.",
            "- No joint renaming.",
            "- No tendon routing or training.",
            "- STL remains visual-only; collision remains primitive proxy.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backups = {str(path): str(backup(path, stamp)) for path in [TUNED_HAND, TUNED_SCENE, REPORT]}
    changes = tune_hand_xml()
    tune_scene_xml()
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_hand": str(SOURCE_HAND),
        "source_scene": str(SOURCE_SCENE),
        "tuned_hand": str(TUNED_HAND),
        "tuned_scene": str(TUNED_SCENE),
        "report": str(REPORT),
        "backups": backups,
        "changes": changes,
    }
    write_report(payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
