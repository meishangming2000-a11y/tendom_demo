from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from export3_common import DOCS_DIR, METADATA_DIR, ROOT


DEFAULT_EVAL = METADATA_DIR / "export3_bc_pinned_wrap_v0_eval_all75.json"
DEFAULT_REPORT = DOCS_DIR / "export3_bc_v0_failure_buckets.md"
DEFAULT_METADATA = METADATA_DIR / "export3_bc_v0_failure_buckets.json"


def hold_metric(episode: dict, key: str, default=0.0):
    return episode.get("stages", {}).get("hold", {}).get(key, default)


def ball_key(episode: dict) -> str:
    return "[" + ", ".join(f"{float(v):.3f}" for v in episode.get("ball_position", [])) + "]"


def summarize_group(episodes: list[dict]) -> dict:
    total = len(episodes)
    partial = [ep for ep in episodes if ep.get("classification") != "PINNED_WRAP_PASS"]
    return {
        "total": total,
        "partial": len(partial),
        "partial_rate": len(partial) / total if total else 0.0,
        "mean_hold_contacts": sum(float(hold_metric(ep, "ball_contact_count", 0)) for ep in episodes) / total if total else 0.0,
        "mean_hold_penetration": sum(float(hold_metric(ep, "max_penetration", 0.0)) for ep in episodes) / total if total else 0.0,
        "mean_four_tip_distance": sum(float(hold_metric(ep, "mean_four_tip_distance", 0.0)) for ep in episodes) / total if total else 0.0,
        "mean_thumb_ball": sum(float(hold_metric(ep, "thumb_to_ball", 0.0)) for ep in episodes) / total if total else 0.0,
    }


def make_report(summary: dict) -> str:
    lines = [
        "# Export3 BC v0 Failure Buckets",
        "",
        "Status: diagnostic pinned-wrap failure analysis, not a promoted stable_grasp baseline.",
        "",
        f"- Eval metadata: `{summary['eval_metadata']}`",
        f"- Episodes: {summary['episode_count']}",
        f"- Pass: {summary['classification_counts'].get('PINNED_WRAP_PASS', 0)}",
        f"- Partial/fail: {summary['partial_count']}",
        f"- Pass rate: {summary['pass_rate']:.3f}",
        "",
        "## Partial Episodes",
        "",
        "| Episode | Ball | Finger scale | Thumb rank | Hold contacts | Penetration | Mean four-tip | Thumb-ball | Thumb-index |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in summary["partial_episodes"]:
        lines.append(
            f"| {item['episode']} | `{item['ball_position']}` | {item['finger_scale']:.2f} | {item['thumb_rank']} | "
            f"{item['hold_contacts']} | {item['hold_penetration']:.6f} | {item['mean_four_tip_distance']:.6f} | "
            f"{item['thumb_to_ball']:.6f} | {item['thumb_to_index']:.6f} |"
        )

    def add_bucket(title: str, rows: dict):
        lines.extend(["", f"## {title}", "", "| Bucket | Total | Partial | Partial rate | Mean contacts | Mean penetration | Mean four-tip | Mean thumb-ball |", "|---|---:|---:|---:|---:|---:|---:|---:|"])
        for key, item in rows.items():
            lines.append(
                f"| `{key}` | {item['total']} | {item['partial']} | {item['partial_rate']:.3f} | "
                f"{item['mean_hold_contacts']:.2f} | {item['mean_hold_penetration']:.6f} | "
                f"{item['mean_four_tip_distance']:.6f} | {item['mean_thumb_ball']:.6f} |"
            )

    add_bucket("By Ball Position", summary["by_ball_position"])
    add_bucket("By Finger Scale", summary["by_finger_scale"])
    add_bucket("By Thumb Rank", summary["by_thumb_rank"])

    lines.extend(
        [
            "",
            "## Takeaways",
            "",
            "- BC v0 is still the best current diagnostic policy, but its failures are not uniformly distributed.",
            "- The next dataset should target the highest partial-rate buckets instead of broad DAgger aggregation.",
            "- Keep this analysis scoped to pinned-wrap; it does not prove free-object retention or gravity grasp.",
            "",
            "## Recommended Next Collection",
            "",
        ]
    )
    for item in summary["recommended_buckets"]:
        lines.append(
            f"- Add scripted successful samples near `{item['bucket_type']}={item['bucket']}` "
            f"(partial rate {item['partial_rate']:.3f}, partial {item['partial']}/{item['total']})."
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze export3 BC v0 pinned-wrap failure buckets.")
    parser.add_argument("--eval-metadata", type=Path, default=DEFAULT_EVAL)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    args = parser.parse_args()

    data = json.loads(args.eval_metadata.read_text(encoding="utf-8"))
    episodes = data.get("episodes", [])
    if not episodes:
        raise RuntimeError(f"No episodes found in {args.eval_metadata}")

    partial_rows = []
    groups = {
        "by_ball_position": defaultdict(list),
        "by_finger_scale": defaultdict(list),
        "by_thumb_rank": defaultdict(list),
    }
    for index, episode in enumerate(episodes, start=1):
        groups["by_ball_position"][ball_key(episode)].append(episode)
        groups["by_finger_scale"][f"{float(episode.get('finger_scale', 0.0)):.2f}"].append(episode)
        groups["by_thumb_rank"][str(int(episode.get("thumb_rank", 0)))].append(episode)
        if episode.get("classification") != "PINNED_WRAP_PASS":
            partial_rows.append(
                {
                    "episode": index,
                    "ball_position": ball_key(episode),
                    "finger_scale": float(episode.get("finger_scale", 0.0)),
                    "thumb_rank": int(episode.get("thumb_rank", 0)),
                    "hold_contacts": int(hold_metric(episode, "ball_contact_count", 0)),
                    "hold_penetration": float(hold_metric(episode, "max_penetration", 0.0)),
                    "mean_four_tip_distance": float(hold_metric(episode, "mean_four_tip_distance", 0.0)),
                    "thumb_to_ball": float(hold_metric(episode, "thumb_to_ball", 0.0)),
                    "thumb_to_index": float(hold_metric(episode, "thumb_to_index", 0.0)),
                }
            )

    bucket_summaries = {
        name: {key: summarize_group(value) for key, value in sorted(values.items())}
        for name, values in groups.items()
    }
    candidates = []
    for group_name, rows in bucket_summaries.items():
        for key, item in rows.items():
            if item["partial"] > 0:
                candidates.append(
                    {
                        "bucket_type": group_name.replace("by_", ""),
                        "bucket": key,
                        "total": item["total"],
                        "partial": item["partial"],
                        "partial_rate": item["partial_rate"],
                    }
                )
    candidates.sort(key=lambda item: (-item["partial_rate"], -item["partial"], item["bucket_type"], item["bucket"]))

    counts = Counter(ep.get("classification", "UNKNOWN") for ep in episodes)
    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "diagnostic_failure_bucket_analysis_not_promoted_baseline",
        "eval_metadata": str(args.eval_metadata),
        "report_path": str(args.report),
        "metadata_path": str(args.metadata),
        "episode_count": len(episodes),
        "classification_counts": dict(counts),
        "partial_count": len(partial_rows),
        "pass_rate": counts.get("PINNED_WRAP_PASS", 0) / len(episodes),
        "partial_episodes": partial_rows,
        **bucket_summaries,
        "recommended_buckets": candidates[:8],
    }

    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(make_report(summary), encoding="utf-8")
    print(json.dumps({"report": str(args.report), "metadata": str(args.metadata), "partial_count": len(partial_rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
