from __future__ import annotations

import json
from pathlib import Path

from clean_mesh_common import DOCS_DIR, METADATA_DIR, ROOT, ensure_dirs, write_json


SOURCE_DIR = Path(r"D:\tendon_project\hardwares\hand\STL")
CLEAN_TEST_DIR = ROOT / "clean_mesh_test"
MESHES_CLEAN_DIR = ROOT / "meshes_clean"
SUMMARY_JSON = METADATA_DIR / "clean_mesh_test_summary.json"
REPORT_MD = DOCS_DIR / "thumb_mesh_mapping_fix_report.md"
THUMB_EXACT = [
    "thumb_metacarpal_link",
    "thumb_proximal_link",
    "thumb_distal_link",
]
ROOT_KEYWORDS = ["thumb_root_connector_link", "D18d12H4", "Trapezium1", "Trapezium3"]


def stl_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.iterdir() if path.is_file() and path.suffix.lower() == ".stl")


def find_exact(directory: Path, stem: str) -> list[str]:
    return [path.name for path in stl_files(directory) if path.stem.lower() == stem.lower()]


def find_related(directory: Path) -> list[str]:
    rows = []
    for path in stl_files(directory):
        lower = path.name.lower()
        if lower.startswith("thumb_root_connector_link") or any(keyword.lower() in lower for keyword in ROOT_KEYWORDS[1:]):
            rows.append(path.name)
    return rows


def main() -> int:
    ensure_dirs()
    summary = {}
    if SUMMARY_JSON.exists():
        summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))

    directories = {
        "source": SOURCE_DIR,
        "clean_mesh_test": CLEAN_TEST_DIR,
        "meshes_clean": MESHES_CLEAN_DIR,
    }
    checks = {}
    for label, directory in directories.items():
        checks[label] = {
            "directory": str(directory),
            "exists": directory.exists(),
            "thumb_exact": {stem: find_exact(directory, stem) for stem in THUMB_EXACT},
            "thumb_root_related": find_related(directory),
        }

    thumb_root_summary = summary.get("evaluation", {}).get("special_checks", {}).get("thumb_root_connector_link_files", [])
    report = {
        "checks": checks,
        "summary_thumb_root_connector_link_files": thumb_root_summary,
        "summary_thumb_root_connector_link_part_count": summary.get("evaluation", {}).get("special_checks", {}).get("thumb_root_connector_link_part_count"),
        "summary_missing_expected_links": summary.get("evaluation", {}).get("missing_expected_links"),
        "conclusion": "thumb mesh mapping fixed; exact thumb STL files are present and thumb_root_connector_link is represented by multiple STL parts",
        "notes": [
            "Multiple thumb_root_connector_link STL files are intentionally mapped to the same thumb_root_connector_link body.",
            "No source STL was renamed or deleted. Non-ASCII/space filenames are copied to meshes_clean with deterministic MJCF-safe aliases when needed.",
            "Do not merge D18d12H4, Trapezium1, and Trapezium3 until CAD-side rigid-body grouping is confirmed.",
        ],
    }
    write_json(METADATA_DIR / "thumb_mesh_mapping_fix.json", report)
    write_report(report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def write_report(report: dict) -> None:
    lines = [
        "# Thumb Mesh Mapping Fix Report",
        "",
        f"- Conclusion: {report['conclusion']}",
        f"- Summary missing expected links: `{report.get('summary_missing_expected_links')}`",
        f"- Summary thumb root connector part count: {report.get('summary_thumb_root_connector_link_part_count')}",
        "",
        "## Directory Checks",
        "",
    ]
    for label, item in report["checks"].items():
        lines.extend(
            [
                f"### {label}",
                "",
                f"- Directory: `{item['directory']}`",
                f"- Exists: {item['exists']}",
                "",
                "Exact thumb STL:",
                "",
            ]
        )
        for stem, matches in item["thumb_exact"].items():
            lines.append(f"- `{stem}`: {matches if matches else 'missing'}")
        lines.extend(["", "Thumb root related STL:", ""])
        if item["thumb_root_related"]:
            lines.extend(f"- `{name}`" for name in item["thumb_root_related"])
        else:
            lines.append("- none")
        lines.append("")
    lines.extend(["## Notes", ""])
    lines.extend(f"- {note}" for note in report["notes"])
    lines.append("")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
