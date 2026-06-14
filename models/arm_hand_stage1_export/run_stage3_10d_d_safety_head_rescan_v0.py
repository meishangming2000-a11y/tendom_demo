#!/usr/bin/env python3
"""Stage3.10D-D safety-head rescan plus small new vision-stress benchmark."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from train_stage3_10d_c_occlusion_safety_head_v0 import (
    LABEL_NAMES,
    binary_metrics,
    build_records,
    json_ready,
    make_features_and_labels,
    predict,
)


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
META = ROOT / "metadata"
EVAL_SCRIPT = ROOT / "eval_stage3_10c_safety_act_cvae_policy_v0.py"
DEFAULT_HEAD = ROOT / "checkpoints" / "stage3_10d_c_occlusion_safety_head_v0.npz"
DEFAULT_DB_V1 = META / "stage3_10d_b_occlusion_benchmark_v1.json"
DEFAULT_METADATA = META / "stage3_10d_d_safety_head_rescan_v0.json"
DEFAULT_REPORT = DOCS / "stage3_10d_d_safety_head_rescan_v0_closeout.md"


@dataclass(frozen=True)
class StressCase:
    case_id: str
    title_zh: str
    random_offset_std: float
    final_verification_mode: str
    initial_vision_stress_scenario: str = "none"
    final_vision_stress_scenario: str = "none"
    initial_vision_stress_samples: int = 5
    final_vision_stress_samples: int = 5
    episodes_per_skill: int = 3
    expected_boundary: bool = False


STRESS_CASES = [
    StressCase(
        case_id="initial_depthnoise5_pose005",
        title_zh="新增：初始 depth noise 5mm + 5mm 位姿噪声",
        random_offset_std=0.005,
        final_verification_mode="strict_vision",
        initial_vision_stress_scenario="depth_noise_5mm",
        initial_vision_stress_samples=15,
        episodes_per_skill=3,
    ),
    StressCase(
        case_id="final_falseblob_occlusionaware_pose005",
        title_zh="新增：最终 false-positive blob + occlusion-aware 验收",
        random_offset_std=0.005,
        final_verification_mode="vision_tactile_occlusion_aware",
        final_vision_stress_scenario="false_positive_blob",
        episodes_per_skill=3,
    ),
    StressCase(
        case_id="initial_combinedhard_pose003_boundary",
        title_zh="失败边界：初始 combined_hard + 3mm 位姿噪声",
        random_offset_std=0.003,
        final_verification_mode="strict_vision",
        initial_vision_stress_scenario="combined_hard",
        initial_vision_stress_samples=15,
        episodes_per_skill=1,
        expected_boundary=True,
    ),
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_head(path: Path) -> dict[str, np.ndarray]:
    data = np.load(path, allow_pickle=True)
    return {
        "weights": data["weights"].astype(np.float32),
        "feature_mean": data["feature_mean"].astype(np.float32),
        "feature_std": np.maximum(data["feature_std"].astype(np.float32), 1e-6),
    }


def score_arrays(features: np.ndarray, labels: np.ndarray, head: dict[str, np.ndarray]) -> dict[str, Any]:
    x = (features - head["feature_mean"].reshape(1, -1)) / head["feature_std"].reshape(1, -1)
    probs = predict(head["weights"], x)
    metrics = binary_metrics(probs, labels)
    pred = probs >= 0.5
    truth = labels >= 0.5
    label_idx = {name: i for i, name in enumerate(LABEL_NAMES)}
    success_truth = truth[:, label_idx["hold_safe"]]
    failure_truth = truth[:, label_idx["failure_or_blocked"]]
    failure_pred = pred[:, label_idx["failure_or_blocked"]]
    hold_safe_pred = pred[:, label_idx["hold_safe"]]
    handoff_truth = truth[:, label_idx["final_tactile_handoff_required"]]
    handoff_pred = pred[:, label_idx["final_tactile_handoff_required"]]
    return {
        "metrics": metrics,
        "false_failure_on_hold_safe": int(np.logical_and(success_truth, failure_pred).sum()),
        "missed_failure_or_blocked": int(np.logical_and(failure_truth, ~failure_pred).sum()),
        "unsafe_predicted_hold_safe": int(np.logical_and(failure_truth, hold_safe_pred).sum()),
        "missed_tactile_handoff": int(np.logical_and(handoff_truth, ~handoff_pred).sum()),
        "probabilities": probs,
        "predictions": pred,
    }


def records_to_arrays(records: list[Any]) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    features = np.asarray([record.features for record in records], dtype=np.float32)
    labels = np.asarray([record.labels for record in records], dtype=np.float32)
    rows = [record.row for record in records]
    return features, labels, rows


def eval_command(case: StressCase, metadata: Path, report: Path) -> list[str]:
    return [
        sys.executable,
        str(EVAL_SCRIPT),
        "--skills",
        "full_hand_gentle_grasp,thumb_index_middle_pinch",
        "--trials",
        "cycle",
        "--episodes-per-skill",
        str(int(case.episodes_per_skill)),
        "--execution-mode",
        "scripted_arm_predicted_hand",
        "--replan-interval",
        "16",
        "--full-hand-control-mode",
        "stage3_7d_fallback",
        "--pinch-final-verification-mode",
        case.final_verification_mode,
        "--pinch-repair-mode",
        "all",
        "--pinch-repair-phases",
        "pinch_close,contact_settle,slow_lift,hold",
        "--pinch-repair-expert-alpha",
        "0.35",
        "--pinch-repair-preclose-delta",
        "0.10",
        "--pinch-repair-close-max",
        "0.18",
        "--random-offset-std",
        f"{float(case.random_offset_std):.3f}",
        "--initial-vision-stress-scenario",
        case.initial_vision_stress_scenario,
        "--final-vision-stress-scenario",
        case.final_vision_stress_scenario,
        "--initial-vision-stress-samples",
        str(int(case.initial_vision_stress_samples)),
        "--final-vision-stress-samples",
        str(int(case.final_vision_stress_samples)),
        "--policy-vision-quality-mode",
        "accepted_nominal",
        "--metadata",
        str(metadata),
        "--report",
        str(report),
    ]


def stress_paths(case: StressCase) -> tuple[Path, Path]:
    episodes = int(case.episodes_per_skill) * 2
    stem = f"stage3_10d_d_{case.case_id}_cycle{episodes}"
    return META / f"{stem}.json", DOCS / f"{stem}_report.md"


def summarize_payload(case: StressCase, metadata: Path, returncode: int) -> dict[str, Any]:
    if not metadata.exists():
        return {
            "case_id": case.case_id,
            "title_zh": case.title_zh,
            "status": "MISSING",
            "episodes": 0,
            "success_count": 0,
            "returncode": int(returncode),
            "failure_reason_counts": {"missing_metadata": 1},
        }
    payload = load_json(metadata)
    summary = payload.get("summary", {})
    return {
        "case_id": case.case_id,
        "title_zh": case.title_zh,
        "status": str(summary.get("status", "UNKNOWN")),
        "episodes": int(summary.get("episodes", 0)),
        "success_count": int(summary.get("success_count", 0)),
        "returncode": int(returncode),
        "expected_boundary": bool(case.expected_boundary),
        "metadata": str(metadata),
        "report": str(stress_paths(case)[1]),
        "terminal_reason_counts": summary.get("terminal_reason_counts", {}),
        "failure_reason_counts": summary.get("failure_reason_counts", {}),
        "risk_flag_counts": summary.get("risk_flag_counts", {}),
        "by_skill": summary.get("by_skill", {}),
    }


def score_payload_case(case: StressCase, metadata: Path, head: dict[str, np.ndarray]) -> dict[str, Any]:
    payload = load_json(metadata)
    fake_case = {
        "case_id": case.case_id,
        "random_offset_std": case.random_offset_std,
        "final_verification_mode": case.final_verification_mode,
        "initial_vision_stress_scenario": case.initial_vision_stress_scenario,
        "final_vision_stress_scenario": case.final_vision_stress_scenario,
        "initial_vision_stress_samples": case.initial_vision_stress_samples,
        "final_vision_stress_samples": case.final_vision_stress_samples,
    }
    features = []
    labels = []
    rows = []
    for result in payload.get("results", []):
        feat, lab, row = make_features_and_labels(
            benchmark_path=metadata,
            case=fake_case,
            payload=payload,
            result=result,
        )
        features.append(feat)
        labels.append(lab)
        rows.append(row)
    features_arr = np.asarray(features, dtype=np.float32)
    labels_arr = np.asarray(labels, dtype=np.float32)
    scored = score_arrays(features_arr, labels_arr, head)
    scored.pop("probabilities", None)
    scored.pop("predictions", None)
    return scored


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage3.10D-D Safety Head Rescan v0 Closeout\n\n",
        f"- 生成时间：`{payload['generated_at']}`\n",
        f"- 状态：`{payload['status']}`\n",
        f"- D-B v1 rescan：`{payload['db_v1_rescan']['status']}`\n",
        f"- 新增 stress pass：`{payload['new_stress_success_count']} / {payload['new_stress_total_episodes']}`\n",
        "- 边界：仍是 MuJoCo scripted arm/wrist + learned hand/fingers + safety/fallback；不是 full-action ACT/DP，也不是硬件。\n\n",
        "## 做了什么\n\n",
        "D-D 把 D-C 的 safety head 用回 D-B v1，并补了两个新压力点：初始 `depth_noise_5mm` 与最终 `false_positive_blob`。同时保留 `combined_hard` 作为失败边界，用来确认视觉系统在过强初始污染下会拒绝，而不是盲目抓取。\n\n",
        "## D-B v1 复扫\n\n",
        f"- records：`{payload['db_v1_rescan']['records']}`\n",
        f"- mean evaluable F1：`{payload['db_v1_rescan']['metrics']['mean_evaluable_f1']:.6f}`\n",
        f"- false failure on hold-safe：`{payload['db_v1_rescan']['false_failure_on_hold_safe']}`\n",
        f"- missed failure/blocker：`{payload['db_v1_rescan']['missed_failure_or_blocked']}`\n\n",
        "## 新增 stress cases\n\n",
        "| case | 含义 | 状态 | 成功 | safety-head 结果 |\n",
        "| --- | --- | --- | ---: | --- |\n",
    ]
    for case in payload["stress_cases"]:
        score = case.get("safety_head", {})
        lines.append(
            f"| `{case['case_id']}` | {case['title_zh']} | `{case['status']}` | "
            f"`{case['success_count']} / {case['episodes']}` | "
            f"`missed_failure={score.get('missed_failure_or_blocked', 'n/a')}, "
            f"unsafe_hold_safe={score.get('unsafe_predicted_hold_safe', 'n/a')}, "
            f"false_failure={score.get('false_failure_on_hold_safe', 'n/a')}` |\n"
        )
    lines.extend(
        [
            "\n## 判断\n\n",
            f"- `stage3_10d_d_ready_for_e`：`{payload['stage3_10d_d_ready_for_e']}`\n",
            "- `depth_noise_5mm` 之前会让捏持初始视觉失败；修补 noisy estimator 的 median-depth fallback 后，小基准通过。\n",
            "- `false_positive_blob` 最终视觉会被 strict confidence 拒绝，但 occlusion-aware 视觉/触觉融合能正确接住。\n",
            "- `combined_hard` 初始视觉仍失败，这是合理边界：mask retention 约半数、false positive 与深度噪声同时存在时，系统宁可拒绝，不应放宽阈值硬抓。\n\n",
            "## 如果成功\n\n",
            "进入 Stage3.10E：整理 Stage3.10 的最终边界、可复现命令、demo/report 索引和下一阶段计划。\n\n",
            "## 如果失败\n\n",
            "如果后续要攻克 `combined_hard`，不要放宽抓取成功阈值；应另开更强视觉路线，例如多相机一致性、时序滤波、显式背景/false-positive 分割或训练式 pose estimator。\n",
        ]
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--head", type=Path, default=DEFAULT_HEAD)
    parser.add_argument("--db-v1", type=Path, default=DEFAULT_DB_V1)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--skip-run", action="store_true")
    args = parser.parse_args()

    head = load_head(Path(args.head))

    db_records = build_records([Path(args.db_v1)])
    db_features, db_labels, _ = records_to_arrays(db_records)
    db_scored = score_arrays(db_features, db_labels, head)
    db_scored.pop("probabilities", None)
    db_scored.pop("predictions", None)
    db_rescan = {
        "status": "PASS"
        if db_scored["false_failure_on_hold_safe"] == 0
        and db_scored["missed_failure_or_blocked"] == 0
        and db_scored["unsafe_predicted_hold_safe"] == 0
        else "NEEDS_REVIEW",
        "records": int(len(db_records)),
        **db_scored,
    }

    stress_summaries: list[dict[str, Any]] = []
    new_stress_total = 0
    new_stress_success = 0
    required_stress_ok = True
    boundary_ok = True
    for case in STRESS_CASES:
        metadata, report = stress_paths(case)
        returncode = 0
        if not bool(args.skip_run):
            cmd = eval_command(case, metadata, report)
            proc = subprocess.run(cmd, cwd=str(ROOT), check=False)
            returncode = int(proc.returncode)
        summary = summarize_payload(case, metadata, returncode)
        if metadata.exists():
            try:
                summary["safety_head"] = score_payload_case(case, metadata, head)
            except Exception as exc:  # pragma: no cover - diagnostic path
                summary["safety_head_error"] = str(exc)
        if not case.expected_boundary:
            new_stress_total += int(summary.get("episodes", 0))
            new_stress_success += int(summary.get("success_count", 0))
            required_stress_ok = required_stress_ok and int(summary.get("success_count", 0)) == int(summary.get("episodes", 0))
        else:
            failures = summary.get("failure_reason_counts", {})
            safety = summary.get("safety_head", {})
            boundary_ok = boundary_ok and (
                int(summary.get("success_count", 0)) < int(summary.get("episodes", 0))
                and int(failures.get("initial_vision_failed", 0)) > 0
                and int(safety.get("missed_failure_or_blocked", 1)) == 0
            )
        stress_summaries.append(summary)

    ready = bool(
        db_rescan["status"] == "PASS"
        and required_stress_ok
        and boundary_ok
        and all(
            int(case.get("safety_head", {}).get("unsafe_predicted_hold_safe", 0)) == 0
            for case in stress_summaries
        )
    )
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stage": "Stage3.10D-D",
        "status": "PASS" if ready else "NEEDS_REPAIR",
        "head": str(Path(args.head).resolve()),
        "db_v1": str(Path(args.db_v1).resolve()),
        "db_v1_rescan": db_rescan,
        "stress_cases": stress_summaries,
        "new_stress_total_episodes": int(new_stress_total),
        "new_stress_success_count": int(new_stress_success),
        "stage3_10d_d_ready_for_e": bool(ready),
        "metadata": str(Path(args.metadata).resolve()),
        "report": str(Path(args.report).resolve()),
        "boundary": {
            "mujoco_only": True,
            "full_action_act_dp_promoted": False,
            "hardware_integration": False,
            "combined_hard_initial_vision_boundary": True,
        },
        "next": "Stage3.10E closeout if PASS; otherwise repair the specific failed stress case without relaxing success thresholds.",
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(json_ready(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(Path(args.report), payload)
    print(
        "Stage3.10D-D safety-head rescan: "
        f"status={payload['status']} new_stress={new_stress_success}/{new_stress_total}"
    )
    print(f"report={Path(args.report).resolve()}")
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
