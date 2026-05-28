#!/usr/bin/env python3
"""Diagnose static collision-proxy penetrations for export4 baseline and tuned scenes."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from export4_wrist2_common import (
    DEFAULT_BALL_POSITION,
    DOCS_DIR,
    LONG_FINGER_TARGETS,
    METADATA_DIR,
    PRESHAPE_TARGETS,
    SCENE_BASELINE,
    SCENE_TUNED,
    THUMB_SMOKE_TARGETS,
    contact_rows,
    json_ready,
    load_model,
    model_summary,
    phase_metrics,
    render_standard_views,
    set_qpos_targets,
    write_json,
    write_text,
)


DEFAULT_REPORT = DOCS_DIR / "collision_proxy_penetration_diagnosis.md"
DEFAULT_METADATA = METADATA_DIR / "collision_proxy_penetration_diagnosis.json"
DEFAULT_VISUAL_DIR = DOCS_DIR / "visual_checks_collision_proxy_tuned"

BALL_POSITIONS = [
    [0.0, -0.1, 0.21],
    [0.0, -0.08, 0.21],
    [0.0, -0.1, 0.195],
    [0.0, 0.1, 0.21],
]


def stage_targets() -> Dict[str, Dict[str, float]]:
    return {
        "open_hand": {},
        "preshape": dict(PRESHAPE_TARGETS),
        "close_four_fingers": dict(LONG_FINGER_TARGETS),
        "close_thumb": {**LONG_FINGER_TARGETS, **THUMB_SMOKE_TARGETS},
    }


def run_scene(scene: Path, label: str, visual_dir: Path, render: bool) -> Dict[str, Any]:
    mujoco, model, data = load_model(scene)
    scene_rows: List[Dict[str, Any]] = []
    for ball_position in BALL_POSITIONS:
        for stage_name, targets in stage_targets().items():
            set_qpos_targets(model, data, mujoco, targets, ball_position=ball_position)
            metrics = phase_metrics(model, data, mujoco, ball_position)
            rows = contact_rows(model, data, mujoco, top_n=20)
            images = {}
            if render and stage_name in ("open_hand", "close_thumb") and ball_position in (BALL_POSITIONS[0], BALL_POSITIONS[-1]):
                stem = f"{label}_{stage_name}_ball_{ball_position[0]:+.2f}_{ball_position[1]:+.2f}_{ball_position[2]:+.3f}".replace("+", "p").replace("-", "m").replace(".", "d")
                images = render_standard_views(model, data, mujoco, visual_dir, stem)
            scene_rows.append(
                {
                    "scene_label": label,
                    "scene": str(scene),
                    "ball_position": ball_position,
                    "stage": stage_name,
                    "metrics": metrics,
                    "top_contacts": rows,
                    "images": images,
                }
            )
    return {"label": label, "scene": str(scene), "summary": model_summary(model), "rows": scene_rows}


def write_report(path: Path, payload: Dict[str, Any]) -> None:
    lines = [
        "# Collision Proxy Penetration Diagnosis\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "## Scope\n\n",
        "Static open/close pose diagnosis for current baseline and wrist2/collision-tuned experimental scene. "
        "No CAD, STL, joint tree, or joint names were modified by this diagnostic script.\n\n",
        "## Ball Positions\n\n",
    ]
    for pos in BALL_POSITIONS:
        note = "default" if pos == DEFAULT_BALL_POSITION else ("mirror-side diagnostic" if pos[1] > 0 else "variant")
        lines.append(f"- `{pos}`: {note}\n")
    lines.append("\n## Summary Table\n\n")
    lines.append("| scene | ball | stage | contacts | max pen (m) | ball-hand contacts | ball-hand max pen (m) | source counts |\n")
    lines.append("|---|---|---|---:|---:|---:|---:|---|\n")
    for scene in payload["scenes"]:
        for row in scene["rows"]:
            metrics = row["metrics"]
            lines.append(
                f"| {row['scene_label']} | `{row['ball_position']}` | {row['stage']} | "
                f"{metrics['contact_count']} | {metrics['max_penetration']:.6f} | "
                f"{metrics['ball_hand_contact_count']} | {metrics['ball_hand_max_penetration']:.6f} | "
                f"`{metrics['source_counts']}` |\n"
            )
    lines.append("\n## Deepest Contacts By Case\n\n")
    for scene in payload["scenes"]:
        lines.append(f"### {scene['label']}\n\n")
        for row in scene["rows"]:
            contacts = row["top_contacts"]
            if not contacts:
                continue
            lines.append(f"#### {row['stage']} ball `{row['ball_position']}`\n\n")
            lines.append("| rank | geom1 | body1 | geom2 | body2 | penetration | source | position |\n")
            lines.append("|---:|---|---|---|---|---:|---|---|\n")
            for idx, contact in enumerate(contacts[:10], start=1):
                lines.append(
                    f"| {idx} | `{contact['geom1']}` | `{contact['body1']}` | `{contact['geom2']}` | "
                    f"`{contact['body2']}` | {contact['penetration']:.6f} | {contact['source']} | "
                    f"`{[round(float(v), 5) for v in contact['position']]}` |\n"
                )
            lines.append("\n")
    tuned_rows = next(scene for scene in payload["scenes"] if scene["label"] == "wrist2_collision_tuned")["rows"]
    default_open = next(row for row in tuned_rows if row["stage"] == "open_hand" and row["ball_position"] == DEFAULT_BALL_POSITION)
    default_close = next(row for row in tuned_rows if row["stage"] == "close_thumb" and row["ball_position"] == DEFAULT_BALL_POSITION)
    lines.extend(
        [
            "## Diagnosis\n\n",
            f"- Tuned default open-hand max penetration: `{default_open['metrics']['max_penetration']:.6f}` m.\n",
            f"- Tuned default close-thumb max penetration: `{default_close['metrics']['max_penetration']:.6f}` m.\n",
            "- If default-side ball contact remains poor while mirror-side contact is natural, treat it as a grasp-side placement issue rather than a collision-proxy issue.\n",
            "- The four-finger `*_mcp_flex_joint` names are retained, but their current mechanical role is lateral spread / abduction-adduction.\n",
        ]
    )
    write_text(path, "".join(lines), "before_collision_diagnosis")


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose export4 collision proxy static penetrations.")
    parser.add_argument("--baseline-scene", default=str(SCENE_BASELINE))
    parser.add_argument("--tuned-scene", default=str(SCENE_TUNED))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA))
    parser.add_argument("--visual-dir", default=str(DEFAULT_VISUAL_DIR))
    parser.add_argument("--no-render", action="store_true")
    args = parser.parse_args()

    visual_dir = Path(args.visual_dir).resolve()
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "ball_positions": BALL_POSITIONS,
        "default_ball_position": DEFAULT_BALL_POSITION,
        "scenes": [
            run_scene(Path(args.baseline_scene).resolve(), "current_baseline", visual_dir, not args.no_render),
            run_scene(Path(args.tuned_scene).resolve(), "wrist2_collision_tuned", visual_dir, not args.no_render),
        ],
    }
    write_json(Path(args.metadata).resolve(), payload, "before_collision_diagnosis_metadata")
    write_report(Path(args.report).resolve(), json_ready(payload))
    tuned = payload["scenes"][1]["rows"]
    default_open = next(row for row in tuned if row["stage"] == "open_hand" and row["ball_position"] == DEFAULT_BALL_POSITION)
    default_close = next(row for row in tuned if row["stage"] == "close_thumb" and row["ball_position"] == DEFAULT_BALL_POSITION)
    print(f"Tuned open max penetration: {default_open['metrics']['max_penetration']:.6f} m")
    print(f"Tuned close max penetration: {default_close['metrics']['max_penetration']:.6f} m")
    print(f"Saved report: {Path(args.report).resolve()}")
    print(f"Saved metadata: {Path(args.metadata).resolve()}")


if __name__ == "__main__":
    main()
