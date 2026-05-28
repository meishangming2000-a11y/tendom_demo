from __future__ import annotations

import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import validate_clean_mesh_test as validator


ROOT = Path(__file__).resolve().parents[1]
EXPORT2_ROOT = Path(r"D:\tendon_project\hardwares\hand\hand_export2\hand_export")
EXPORT2_MESH_DIR = EXPORT2_ROOT / "meshes"
EXPORT2_CLEAN_TEST_DIR = ROOT / "clean_mesh_test_export2"
EXPORT2_MESHES_CLEAN_DIR = ROOT / "meshes_clean_export2"
EXPORT2_DRAFT_XML = ROOT / "mjcf" / "hand_stage1_clean_mesh_export2_draft.xml"
EXPORT2_REPORT_MD = ROOT / "docs" / "clean_mesh_export2_test_report.md"
EXPORT2_SUMMARY_JSON = ROOT / "metadata" / "clean_mesh_export2_test_summary.json"
EXPORT2_REPLACEMENT_STATUS_MD = ROOT / "docs" / "clean_mesh_export2_replacement_status.md"


def copy_export2_meshes() -> None:
    if not EXPORT2_MESH_DIR.exists():
        raise FileNotFoundError(f"Export2 mesh directory not found: {EXPORT2_MESH_DIR}")
    EXPORT2_CLEAN_TEST_DIR.mkdir(parents=True, exist_ok=True)
    for src in sorted(EXPORT2_MESH_DIR.iterdir()):
        if src.is_file() and src.suffix.lower() == ".stl":
            shutil.copy2(src, EXPORT2_CLEAN_TEST_DIR / src.name)


def patch_export2_meshdir() -> None:
    if not EXPORT2_DRAFT_XML.exists():
        return
    tree = ET.parse(EXPORT2_DRAFT_XML)
    root = tree.getroot()
    root.set("model", "hand_stage1_clean_mesh_export2_draft")
    compiler = root.find("compiler")
    if compiler is not None:
        compiler.set("meshdir", "../meshes_clean_export2")
    tree.write(EXPORT2_DRAFT_XML, encoding="utf-8", xml_declaration=True)


def main() -> int:
    copy_export2_meshes()
    validator.CLEAN_TEST_DIR = EXPORT2_CLEAN_TEST_DIR
    validator.MESHES_CLEAN_DIR = EXPORT2_MESHES_CLEAN_DIR
    validator.CLEAN_DRAFT_XML = EXPORT2_DRAFT_XML
    validator.REPORT_MD = EXPORT2_REPORT_MD
    validator.SUMMARY_JSON = EXPORT2_SUMMARY_JSON
    validator.REPLACEMENT_STATUS_MD = EXPORT2_REPLACEMENT_STATUS_MD
    validator.CLEAN_MESH_SCALE = "1 1 1"
    code = validator.main()
    patch_export2_meshdir()
    return code


if __name__ == "__main__":
    sys.exit(main())
