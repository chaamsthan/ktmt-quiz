#!/usr/bin/env python3
"""Validate the K16 source audit; optionally create its new, source-only figure crops.

Read-only by default. Crop mode writes only the nine new reviewed PNGs; it never
changes an exam JSON or source file. Requires PyMuPDF only for --crop-figures:
    uv run --with pymupdf python tools/nmmmh_source_k16.py --crop-figures
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "subjects/nmmmh/audit/source_k16_review.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crop-figures", action="store_true")
    args = parser.parse_args()
    audit = json.loads(AUDIT.read_text())
    assert len(audit["questions"]) == 80
    assert len({q["id"] for q in audit["questions"]}) == 80
    if audit["status"] == "complete":
        assert audit["counts"]["evidence_finalized"] == 80
        assert audit["counts"]["pending"] == 0
        assert audit["counts"]["unreviewed"] == 0
        assert not audit["pending_question_ids"] and not audit["unreviewed_questions"]
        assert len(audit["hints"]) == 80
    by_exam = Counter(q["exam_id"] for q in audit["questions"])
    assert by_exam == {"de-thi-k16-2": 40, "de-thi-k16-3": 40}
    source_pages = {}
    for source in audit["source_documents"]:
        assert sha256(Path(source["pdf_path"])) == source["pdf_sha256"]
        published = ROOT / source["published_json"]
        # A later independent integration may intentionally change published data.
        # Report drift instead of failing provenance checks for the captured audit.
        if sha256(published) != source["published_json_sha256"]:
            print(f"Published data changed since audit snapshot: {published}")
        else:
            print(f"Published snapshot unchanged: {published.relative_to(ROOT)}")
        for page in source["pages"]:
            assert sha256(Path(page["original_png"])) == page["original_png_sha256"]
            source_pages[(source["exam_id"], page["pdf_page"])] = page
    figures = []
    for question in audit["questions"]:
        for region in question["crop_regions"]:
            page = source_pages[(question["exam_id"], region["pdf_page"])]
            assert region["original_png"] == page["original_png"]
            assert region["coordinate_image_size_px"] == page["original_png_size_px"]
            width, height = region["coordinate_image_size_px"]
            x0, y0, x1, y1 = region["pixel_crop_bbox"]
            assert 0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height
            if region["purpose"] == "formula_or_table_replacement":
                figures.append((question, region))
        for correction in question["corrections"]:
            assert "old" in correction and "new" in correction
        for replacement in question.get("image_replacements", []):
            target = ROOT / replacement["new"]
            assert sha256(target) == replacement["sha256"]
            header = target.read_bytes()[:24]
            assert header[:8] == b"\x89PNG\r\n\x1a\n"
            assert list(struct.unpack(">II", header[16:24])) == replacement["size_px"]
            assert replacement["visually_checked_final_asset"]
    assert len(figures) == 9
    if args.crop_figures:
        import pymupdf

        for question, region in figures:
            source_path = Path(region["original_png"])
            width, height = region["coordinate_image_size_px"]
            target = ROOT / "images/nmmmh/reviewed" / f"{question['id']}-figure.png"
            target.parent.mkdir(parents=True, exist_ok=True)
            # Build a pixel-sized page, avoiding the PNG's DPI-to-points scaling.
            document = pymupdf.open()
            page = document.new_page(width=width, height=height)
            page.insert_image(page.rect, filename=str(source_path))
            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(1, 1),
                clip=pymupdf.Rect(region["pixel_crop_bbox"]),
                alpha=False,
            )
            data = pixmap.tobytes("png")
            if target.exists():
                if target.read_bytes() != data:
                    raise FileExistsError(f"Refusing to overwrite different existing crop: {target}")
            else:
                target.write_bytes(data)
            print(json.dumps({
                "question_id": question["id"],
                "asset": str(target.relative_to(ROOT)),
                "size_px": [pixmap.width, pixmap.height],
                "sha256": sha256(target),
                "source_png": str(source_path),
                "pixel_crop_bbox": region["pixel_crop_bbox"],
            }, ensure_ascii=False))
    print(json.dumps({"questions": 80, "questions_by_exam": by_exam,
                      "figures": len(figures), "counts": audit["counts"]}))


if __name__ == "__main__":
    main()
