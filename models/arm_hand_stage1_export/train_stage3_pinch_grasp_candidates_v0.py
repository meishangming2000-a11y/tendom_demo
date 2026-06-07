#!/usr/bin/env python3
"""Train/search Stage3 pinch-grasp candidates.

This is a MuJoCo-only Stage3.8B training pass. "Training" here means
curriculum-style parameter search for scripted pinch families, not a neural
network update. Each family gets several tuned variants, then the best variant
per family is validated before one final demo-ready candidate is selected.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

from arm_hand_stage1_task_api import json_ready
from stage3_sensor_aware_gentle_grasp_hold_task_api import CURRENT_STAGE3_SCENE


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
SENSOR_ROOT = ROOT / "external_sensors"
if str(SENSOR_ROOT) not in sys.path:
    sys.path.insert(0, str(SENSOR_ROOT))

import eval_stage3_pinch_grasp_v0 as pinch
import run_stage3_visual_guided_grasp_sweep as sweep


DEFAULT_REPORT = DOCS / "stage3_pinch_grasp_training_v0_report.md"
DEFAULT_METADATA = META / "stage3_pinch_grasp_training_v0.json"
DEFAULT_SELECTED = META / "stage3_pinch_grasp_training_v0_selected.json"


def _clip(value: float, lo: float, hi: float) -> float:
    return float(np.clip(float(value), float(lo), float(hi)))


def tuned_candidate(base: pinch.PinchCandidate, suffix: str, **delta: float) -> pinch.PinchCandidate:
    """Return a bounded candidate variant."""

    return replace(
        base,
        name=f"{base.name}__{suffix}",
        thumb_cmc_abd=_clip(base.thumb_cmc_abd + float(delta.get("thumb_cmc_abd", 0.0)), -0.50, -0.20),
        thumb_cmc=_clip(base.thumb_cmc + float(delta.get("thumb_cmc", 0.0)), -0.06, 0.08),
        thumb_mcp=_clip(base.thumb_mcp + float(delta.get("thumb_mcp", 0.0)), 0.20, 0.46),
        thumb_ip=_clip(base.thumb_ip + float(delta.get("thumb_ip", 0.0)), -0.52, -0.18),
        active_mcp_flex=_clip(base.active_mcp_flex + float(delta.get("active_mcp_flex", 0.0)), -0.105, -0.030),
        active_mcp_abd=_clip(base.active_mcp_abd + float(delta.get("active_mcp_abd", 0.0)), -0.82, -0.48),
        active_pip=_clip(base.active_pip + float(delta.get("active_pip", 0.0)), -1.12, -0.66),
        active_dip=_clip(base.active_dip + float(delta.get("active_dip", 0.0)), -0.66, -0.28),
        inactive_scale=_clip(base.inactive_scale + float(delta.get("inactive_scale", 0.0)), 0.08, 0.36),
        approach_z_bias_delta=_clip(
            base.approach_z_bias_delta + float(delta.get("approach_z_bias_delta", 0.0)),
            -0.007,
            0.005,
        ),
        lift_delta_scale=_clip(base.lift_delta_scale + float(delta.get("lift_delta_scale", 0.0)), 0.92, 1.08),
    )


def variant_bank(base: pinch.PinchCandidate) -> list[pinch.PinchCandidate]:
    """Generate a compact search bank for one pinch family."""

    return [
        tuned_candidate(base, "base"),
        tuned_candidate(
            base,
            "firmer_close",
            thumb_mcp=0.030,
            thumb_ip=-0.030,
            active_mcp_abd=-0.030,
            active_pip=-0.060,
            active_dip=-0.040,
        ),
        tuned_candidate(
            base,
            "gentler_close",
            thumb_mcp=-0.020,
            thumb_ip=0.020,
            active_mcp_abd=0.020,
            active_pip=0.050,
            active_dip=0.030,
            inactive_scale=0.020,
        ),
        tuned_candidate(base, "lower_approach", approach_z_bias_delta=-0.003),
        tuned_candidate(base, "higher_approach", approach_z_bias_delta=0.003),
        tuned_candidate(base, "lift_plus", lift_delta_scale=0.040),
        tuned_candidate(
            base,
            "low_firm",
            approach_z_bias_delta=-0.002,
            thumb_mcp=0.025,
            thumb_ip=-0.025,
            active_pip=-0.050,
            active_dip=-0.035,
        ),
    ]


def family_bases(spec: str) -> list[pinch.PinchCandidate]:
    names = list(pinch.PINCH_CANDIDATES) if spec.strip().lower() in {"all", "*"} else [x.strip() for x in spec.split(",") if x.strip()]
    out = []
    for name in names:
        if name not in pinch.PINCH_CANDIDATES:
            raise ValueError(f"Unknown pinch family {name!r}; choose from {sorted(pinch.PINCH_CANDIDATES)}")
        out.append(pinch.PINCH_CANDIDATES[name])
    return out


def candidate_to_dict(candidate: pinch.PinchCandidate) -> dict[str, Any]:
    return {
        "name": candidate.name,
        "active_fingers": list(candidate.active_fingers),
        "thumb_cmc_abd": float(candidate.thumb_cmc_abd),
        "thumb_cmc": float(candidate.thumb_cmc),
        "thumb_mcp": float(candidate.thumb_mcp),
        "thumb_ip": float(candidate.thumb_ip),
        "active_mcp_flex": float(candidate.active_mcp_flex),
        "active_mcp_abd": float(candidate.active_mcp_abd),
        "active_pip": float(candidate.active_pip),
        "active_dip": float(candidate.active_dip),
        "inactive_scale": float(candidate.inactive_scale),
        "approach_z_bias_delta": float(candidate.approach_z_bias_delta),
        "lift_delta_scale": float(candidate.lift_delta_scale),
    }


def candidate_from_dict(raw: dict[str, Any]) -> pinch.PinchCandidate:
    return pinch.PinchCandidate(
        name=str(raw["name"]),
        active_fingers=tuple(str(x) for x in raw["active_fingers"]),
        thumb_cmc_abd=float(raw["thumb_cmc_abd"]),
        thumb_cmc=float(raw["thumb_cmc"]),
        thumb_mcp=float(raw["thumb_mcp"]),
        thumb_ip=float(raw["thumb_ip"]),
        active_mcp_flex=float(raw["active_mcp_flex"]),
        active_mcp_abd=float(raw["active_mcp_abd"]),
        active_pip=float(raw["active_pip"]),
        active_dip=float(raw["active_dip"]),
        inactive_scale=float(raw["inactive_scale"]),
        approach_z_bias_delta=float(raw.get("approach_z_bias_delta", 0.0)),
        lift_delta_scale=float(raw.get("lift_delta_scale", 1.0)),
    )


def stage_args(args: argparse.Namespace, *, stage: str, random_offset_std: float, hold_steps: int) -> SimpleNamespace:
    return SimpleNamespace(
        scene=Path(args.scene),
        report=Path(args.report),
        metadata=Path(args.metadata),
        debug_dir=Path(args.debug_dir),
        candidates="custom",
        episodes_per_candidate=1,
        seed=int(args.seed) + {"train": 0, "validate": 10000, "final": 20000}.get(stage, 30000),
        random_offset_std=float(random_offset_std),
        trial=str(args.trial),
        camera=str(args.camera),
        final_cameras=str(args.final_cameras),
        width=int(args.width),
        height=int(args.height),
        min_vision_confidence=float(args.min_vision_confidence),
        min_final_vision_confidence=float(args.min_final_vision_confidence),
        min_vision_lift_height=float(args.min_vision_lift_height),
        min_hold_stable_fraction=float(args.min_hold_stable_fraction),
        min_hold_pinch_fraction=float(args.min_hold_pinch_fraction),
        min_hold_pinch_purity=float(args.min_hold_pinch_purity),
        approach_steps=int(args.approach_steps),
        hand_steps=int(args.hand_steps),
        pinch_close_steps=int(args.pinch_close_steps),
        min_contact_settle_steps=int(args.min_contact_settle_steps),
        max_contact_settle_steps=int(args.max_contact_settle_steps),
        settle_stable_window_steps=int(args.settle_stable_window_steps),
        gate_slip_threshold=float(args.gate_slip_threshold),
        gate_crush_threshold=float(args.gate_crush_threshold),
        gate_penetration_threshold=float(args.gate_penetration_threshold),
        lift_steps=int(args.lift_steps),
        hold_steps=int(hold_steps),
        sample_every=int(args.sample_every),
        render_vision_debug=False,
    )


def episode_trial(trials: list[sweep.TrialConfig], trial_mode: str, local_episode: int) -> sweep.TrialConfig:
    if trial_mode == "cycle":
        return trials[local_episode % len(trials)]
    return pinch.selected_trial(trial_mode)


def evaluate_candidates(
    model,
    mujoco,
    *,
    candidates: list[pinch.PinchCandidate],
    episodes_per_candidate: int,
    run_args: SimpleNamespace,
    stage_name: str,
    episode_start: int,
) -> tuple[list[dict[str, Any]], int]:
    trials = sweep.trial_configs()
    rows: list[dict[str, Any]] = []
    episode_id = int(episode_start)
    for candidate in candidates:
        for local_episode in range(int(episodes_per_candidate)):
            trial = episode_trial(trials, str(run_args.trial), local_episode)
            row = pinch.run_pinch_episode(
                model,
                mujoco,
                candidate=candidate,
                trial=trial,
                episode_id=episode_id,
                args=run_args,
            )
            row["training_stage"] = stage_name
            row["family"] = candidate.name.split("__", 1)[0]
            rows.append(row)
            r = row.get("summary", {})
            print(
                f"{stage_name} ep={episode_id:03d} cand={candidate.name} trial={trial.name} {row['status']} "
                f"lift={r.get('true_lift_height_m', float('nan')):.4f} "
                f"vision={r.get('vision_lift_height_m', float('nan')):.4f} "
                f"pinch={r.get('hold_pinch_fraction', float('nan')):.3f} "
                f"slip={r.get('hold_max_slip_score', float('nan')):.3f} "
                f"reason={row['terminal_reason']}"
            )
            episode_id += 1
    return rows, episode_id


def score_summary(summary: dict[str, Any]) -> float:
    episodes = max(1, int(summary.get("episodes", 0)))
    success_rate = float(summary.get("success_count", 0)) / float(episodes)
    lift = float(summary.get("true_lift_height_m_mean", 0.0))
    stable = float(summary.get("hold_stable_fraction_mean", 0.0))
    pinch_fraction = float(summary.get("hold_pinch_fraction_mean", 0.0))
    purity = float(summary.get("hold_pinch_purity_mean_mean", 0.0))
    hold_slip = float(summary.get("hold_max_slip_score_max", 1.0))
    crush = float(summary.get("max_crush_risk_max", 1.0))
    penetration = float(summary.get("max_penetration_m_max", 0.01))
    risk_count = sum(int(v) for v in summary.get("risk_flag_counts", {}).values())
    failure_count = sum(int(v) for v in summary.get("failure_reason_counts", {}).values())
    return float(
        100.0 * success_rate
        + 12.0 * min(max(lift, 0.0) / 0.10, 1.2)
        + 6.0 * stable
        + 6.0 * pinch_fraction
        + 4.0 * purity
        - 10.0 * max(0.0, hold_slip - 0.18)
        - 4.0 * max(0.0, crush - 0.12)
        - 1000.0 * max(0.0, penetration - 0.004)
        - 0.35 * risk_count / episodes
        - 5.0 * failure_count / episodes
    )


def rank_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = pinch.summarize(rows)
    ranked = []
    for name, item in summary["by_candidate"].items():
        ranked.append(
            {
                "candidate": name,
                "family": name.split("__", 1)[0],
                "score": score_summary(item),
                "summary": item,
            }
        )
    ranked.sort(key=lambda row: (float(row["score"]), int(row["summary"].get("success_count", 0))), reverse=True)
    return ranked


def best_per_family(ranked: list[dict[str, Any]], candidates: dict[str, pinch.PinchCandidate]) -> list[pinch.PinchCandidate]:
    picked: dict[str, pinch.PinchCandidate] = {}
    for row in ranked:
        family = str(row["family"])
        if family not in picked:
            picked[family] = candidates[str(row["candidate"])]
    return list(picked.values())


def write_training_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage3.8B Pinch Grasp Training V0\n\n",
        f"Generated: {payload['generated_at']}\n\n",
        "这次训练仍然是 MuJoCo-only：使用虚拟摄像机定位/验收，使用合成触觉和滑移判断捏持质量，不使用现实摄像头或真实硬件。\n\n",
        "这里的“训练”是参数搜索和课程式评估，不是神经网络训练。每个捏持方法先生成多个参数变体，经过训练筛选、家族验证和最终随机扰动验收后，再选择一个 demo-ready 抓法。\n\n",
        "## Training Setup\n\n",
        f"- Families: `{payload['families']}`\n",
        f"- Variants tested: `{len(payload['candidate_bank'])}`\n",
        f"- Train episodes: `{len(payload['train_results'])}`\n",
        f"- Validation episodes: `{len(payload['validation_results'])}`\n",
        f"- Final episodes: `{len(payload['final_results'])}`\n",
        f"- Selected candidate: `{payload['selected_candidate']['name']}`\n",
        f"- Demo command: `{payload['demo_command']}`\n\n",
        "## Train Ranking\n\n",
        "| rank | candidate | family | score | success | true lift mean | hold pinch | purity | hold slip max | failures |\n",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---|\n",
    ]
    for idx, row in enumerate(payload["train_ranking"][:18], start=1):
        s = row["summary"]
        lines.append(
            f"| {idx} | {row['candidate']} | {row['family']} | {row['score']:.2f} | "
            f"{s['success_count']}/{s['episodes']} | "
            f"{s.get('true_lift_height_m_mean', float('nan')):.5f} | "
            f"{s.get('hold_pinch_fraction_mean', float('nan')):.3f} | "
            f"{s.get('hold_pinch_purity_mean_mean', float('nan')):.3f} | "
            f"{s.get('hold_max_slip_score_max', float('nan')):.3f} | "
            f"`{s['failure_reason_counts']}` |\n"
        )

    lines.extend(
        [
            "\n## Validation Ranking\n\n",
            "| rank | candidate | family | score | success | true lift mean | hold pinch | purity | hold slip max | failures |\n",
            "|---:|---|---|---:|---:|---:|---:|---:|---:|---|\n",
        ]
    )
    for idx, row in enumerate(payload["validation_ranking"], start=1):
        s = row["summary"]
        lines.append(
            f"| {idx} | {row['candidate']} | {row['family']} | {row['score']:.2f} | "
            f"{s['success_count']}/{s['episodes']} | "
            f"{s.get('true_lift_height_m_mean', float('nan')):.5f} | "
            f"{s.get('hold_pinch_fraction_mean', float('nan')):.3f} | "
            f"{s.get('hold_pinch_purity_mean_mean', float('nan')):.3f} | "
            f"{s.get('hold_max_slip_score_max', float('nan')):.3f} | "
            f"`{s['failure_reason_counts']}` |\n"
        )

    lines.extend(
        [
            "\n## Final Ranking\n\n",
            "| rank | candidate | family | score | success | true lift mean | hold pinch | purity | hold slip max | failures |\n",
            "|---:|---|---|---:|---:|---:|---:|---:|---:|---|\n",
        ]
    )
    for idx, row in enumerate(payload["final_ranking"], start=1):
        s = row["summary"]
        lines.append(
            f"| {idx} | {row['candidate']} | {row['family']} | {row['score']:.2f} | "
            f"{s['success_count']}/{s['episodes']} | "
            f"{s.get('true_lift_height_m_mean', float('nan')):.5f} | "
            f"{s.get('hold_pinch_fraction_mean', float('nan')):.3f} | "
            f"{s.get('hold_pinch_purity_mean_mean', float('nan')):.3f} | "
            f"{s.get('hold_max_slip_score_max', float('nan')):.3f} | "
            f"`{s['failure_reason_counts']}` |\n"
        )

    final_summary = payload["final_summary"]
    selected_summary = final_summary["by_candidate"][payload["selected_candidate"]["name"]]
    lines.extend(
        [
            "\n## Final Selected Result\n\n",
            f"- Candidate: `{payload['selected_candidate']['name']}`\n",
            f"- Success: `{selected_summary['success_count']} / {selected_summary['episodes']}`\n",
            f"- Mean true lift: `{selected_summary.get('true_lift_height_m_mean', float('nan')):.5f} m`\n",
            f"- Mean vision lift: `{selected_summary.get('vision_lift_height_m_mean', float('nan')):.5f} m`\n",
            f"- Hold stable fraction mean: `{selected_summary.get('hold_stable_fraction_mean', float('nan')):.3f}`\n",
            f"- Hold pinch fraction mean: `{selected_summary.get('hold_pinch_fraction_mean', float('nan')):.3f}`\n",
            f"- Hold pinch purity mean: `{selected_summary.get('hold_pinch_purity_mean_mean', float('nan')):.3f}`\n",
            f"- Max hold slip: `{selected_summary.get('hold_max_slip_score_max', float('nan')):.3f}`\n",
            f"- Max crush risk: `{selected_summary.get('max_crush_risk_max', float('nan')):.3f}`\n",
            f"- Max penetration: `{selected_summary.get('max_penetration_m_max', float('nan')):.6f} m`\n",
            f"- Failure reasons: `{selected_summary['failure_reason_counts']}`\n",
            f"- Risk flags: `{selected_summary['risk_flag_counts']}`\n\n",
            "## Interpretation\n\n",
            "- 如果 final success 是满分，当前 selected candidate 可以作为 Stage3.8B 成功 demo 的默认抓法。\n",
            "- 如果某些纯二指/二三指方法没通过，它们不会被删除，会保留为失败证据和下一轮修复对象。\n",
            "- 即使最终成功，`early_contact_in_approach` 或 `transient_slip_high` 仍然是后续优化方向；它们不等于 hold 失败。\n\n",
            "## 如果成功\n\n",
            "- 使用 demo 命令打开 MuJoCo，展示虚拟视觉、触觉区域、捏持区域和成功抬升。\n",
            "- 把 selected candidate 作为 Stage3.8B 当前捏持 demo baseline。\n",
            "- 下一轮可继续修早接触和瞬时滑移，或者挑战更纯的 thumb/index/middle 捏持。\n\n",
            "## 如果失败\n\n",
            "- 先看 failure_reason_counts：视觉失败、真实抬升失败、触觉捏持失败、hold slip 失败要分开修。\n",
            "- 如果只有 final vision 失败而真值/触觉成功，优先修验收相机，不先改抓法。\n",
            "- 如果 true lift 失败，优先修 approach_z_bias_delta、thumb 角度和 active finger 闭合角度。\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train/search Stage3 pinch-grasp candidate parameters.")
    parser.add_argument("--scene", type=Path, default=CURRENT_STAGE3_SCENE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--selected-config", type=Path, default=DEFAULT_SELECTED)
    parser.add_argument("--debug-dir", type=Path, default=DOCS / "visual_checks_stage3_pinch_training_v0")
    parser.add_argument("--families", default="all")
    parser.add_argument("--train-episodes-per-variant", type=int, default=2)
    parser.add_argument("--validation-episodes-per-family", type=int, default=3)
    parser.add_argument("--final-episodes", type=int, default=10)
    parser.add_argument("--finalists", type=int, default=4, help="How many validation-ranked family winners to run in final validation.")
    parser.add_argument("--seed", type=int, default=381)
    parser.add_argument("--train-random-offset-std", type=float, default=0.003)
    parser.add_argument("--validation-random-offset-std", type=float, default=0.005)
    parser.add_argument("--final-random-offset-std", type=float, default=0.005)
    parser.add_argument("--trial", default="cycle")
    parser.add_argument("--camera", default="stage3_egg_closeup")
    parser.add_argument("--final-cameras", default="stage3_egg_closeup,stage3_egg_overview")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--min-vision-confidence", type=float, default=0.55)
    parser.add_argument("--min-final-vision-confidence", type=float, default=0.35)
    parser.add_argument("--min-vision-lift-height", type=float, default=0.045)
    parser.add_argument("--min-hold-stable-fraction", type=float, default=0.60)
    parser.add_argument("--min-hold-pinch-fraction", type=float, default=0.55)
    parser.add_argument("--min-hold-pinch-purity", type=float, default=0.55)
    parser.add_argument("--approach-steps", type=int, default=300)
    parser.add_argument("--hand-steps", type=int, default=120)
    parser.add_argument("--pinch-close-steps", type=int, default=220)
    parser.add_argument("--min-contact-settle-steps", type=int, default=120)
    parser.add_argument("--max-contact-settle-steps", type=int, default=360)
    parser.add_argument("--settle-stable-window-steps", type=int, default=70)
    parser.add_argument("--gate-slip-threshold", type=float, default=0.22)
    parser.add_argument("--gate-crush-threshold", type=float, default=0.35)
    parser.add_argument("--gate-penetration-threshold", type=float, default=0.004)
    parser.add_argument("--lift-steps", type=int, default=520)
    parser.add_argument("--train-hold-steps", type=int, default=260)
    parser.add_argument("--validation-hold-steps", type=int, default=420)
    parser.add_argument("--final-hold-steps", type=int, default=700)
    parser.add_argument("--sample-every", type=int, default=240)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    import mujoco

    model = mujoco.MjModel.from_xml_path(str(Path(args.scene).resolve()))
    bases = family_bases(str(args.families))
    variants = [variant for base in bases for variant in variant_bank(base)]
    candidate_map = {candidate.name: candidate for candidate in variants}
    episode_cursor = 0

    train_rows, episode_cursor = evaluate_candidates(
        model,
        mujoco,
        candidates=variants,
        episodes_per_candidate=int(args.train_episodes_per_variant),
        run_args=stage_args(args, stage="train", random_offset_std=float(args.train_random_offset_std), hold_steps=int(args.train_hold_steps)),
        stage_name="train",
        episode_start=episode_cursor,
    )
    train_ranking = rank_candidates(train_rows)
    family_winners = best_per_family(train_ranking, candidate_map)
    print("family winners:", ", ".join(candidate.name for candidate in family_winners))

    validation_rows, episode_cursor = evaluate_candidates(
        model,
        mujoco,
        candidates=family_winners,
        episodes_per_candidate=int(args.validation_episodes_per_family),
        run_args=stage_args(
            args,
            stage="validate",
            random_offset_std=float(args.validation_random_offset_std),
            hold_steps=int(args.validation_hold_steps),
        ),
        stage_name="validate",
        episode_start=episode_cursor,
    )
    validation_ranking = rank_candidates(validation_rows)
    finalist_names = [str(row["candidate"]) for row in validation_ranking[: max(1, int(args.finalists))]]
    finalist_map = {candidate.name: candidate for candidate in family_winners}
    finalists = [finalist_map[name] for name in finalist_names if name in finalist_map]
    if not finalists:
        finalists = [family_winners[0]]

    final_rows, episode_cursor = evaluate_candidates(
        model,
        mujoco,
        candidates=finalists,
        episodes_per_candidate=int(args.final_episodes),
        run_args=stage_args(
            args,
            stage="final",
            random_offset_std=float(args.final_random_offset_std),
            hold_steps=int(args.final_hold_steps),
        ),
        stage_name="final",
        episode_start=episode_cursor,
    )
    final_summary = pinch.summarize(final_rows)
    final_ranking = rank_candidates(final_rows)
    selected = finalist_map.get(str(final_ranking[0]["candidate"]), finalists[0])
    demo_command = (
        "python .\\simulations\\models\\arm_hand_stage1_export\\demo_stage3_pinch_grasp_viewer.py "
        "--candidate-config .\\simulations\\models\\arm_hand_stage1_export\\metadata\\stage3_pinch_grasp_training_v0_selected.json"
    )
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scene": str(Path(args.scene).resolve()),
        "policy_scope": "scripted_visual_guided_pinch_parameter_search_with_synthetic_tactile_validation",
        "families": [base.name for base in bases],
        "candidate_bank": [candidate_to_dict(candidate) for candidate in variants],
        "family_winners": [candidate_to_dict(candidate) for candidate in family_winners],
        "selected_candidate": candidate_to_dict(selected),
        "demo_command": demo_command,
        "args": vars(args),
        "train_ranking": train_ranking,
        "validation_ranking": validation_ranking,
        "final_ranking": final_ranking,
        "train_summary": pinch.summarize(train_rows),
        "validation_summary": pinch.summarize(validation_rows),
        "final_summary": final_summary,
        "train_results": train_rows,
        "validation_results": validation_rows,
        "final_results": final_rows,
        "terminal_reason_counts": dict(Counter(str(row["terminal_reason"]) for row in train_rows + validation_rows + final_rows)),
        "failure_reason_counts": dict(Counter(reason for row in train_rows + validation_rows + final_rows for reason in row.get("failure_reasons", []))),
        "training_ready": True,
    }

    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    args.selected_config.parent.mkdir(parents=True, exist_ok=True)
    selected_payload = {
        "generated_at": payload["generated_at"],
        "source_metadata": str(Path(args.metadata).as_posix()),
        "selected_candidate": candidate_to_dict(selected),
        "selected_final_summary": final_summary["by_candidate"].get(selected.name, {}),
        "final_summary": final_summary,
        "demo_command": demo_command,
    }
    args.selected_config.write_text(json.dumps(json_ready(selected_payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_training_report(Path(args.report), json_ready(payload))
    print(json.dumps(json_ready(final_summary), indent=2, ensure_ascii=False))
    print(f"Saved training report: {args.report}")
    print(f"Saved training metadata: {args.metadata}")
    print(f"Saved selected config: {args.selected_config}")
    print(f"Demo command: {demo_command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
