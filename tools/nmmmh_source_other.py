#!/usr/bin/env python3
"""Validate the visual audit, export hints/candidates, or render NEW figures.

  python tools/nmmmh_source_other.py
  python tools/nmmmh_source_other.py --hints
  python tools/nmmmh_source_other.py --numeric-candidates
  uv run --with pymupdf python tools/nmmmh_source_other.py --render-figures

Never writes exam JSON or replaces an existing image. Source PDFs are read-only.
The audit records visual judgments; this helper validates provenance and bounds,
not the correctness of an answer key or the truth of a visual judgment.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "subjects/nmmmh/audit/source_other_review.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_figures(audit):
    import pymupdf

    for figure in audit["figure_assets"]:
        destination = ROOT / figure["path"]
        if destination.exists():
            print(f"EXISTS (preserved): {figure['path']}")
            continue
        source = Path(figure["source_pdf"])
        with pymupdf.open(source) as pdf:
            page = pdf[figure["pdf_page"] - 1]
            width, height = figure["source_render_size"]
            x0, y0, x1, y1 = figure["crop_bbox"]
            clip = pymupdf.Rect(
                x0 * page.rect.width / width,
                y0 * page.rect.height / height,
                x1 * page.rect.width / width,
                y1 * page.rect.height / height,
            )
            pixmap = page.get_pixmap(
                matrix=pymupdf.Matrix(2.6, 2.6), clip=clip, alpha=False
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(pixmap.tobytes("png"))
        print(f"CREATED: {figure['path']} ({pixmap.width}x{pixmap.height})")


def validate(audit):
    records = [q for e in audit["exams"] for q in e["questions"]]
    assert len(records) == 93
    assert len({q["question_id"] for q in records}) == 93
    assert len(audit["hints"]) == 93
    checked_renders = set()
    drifts = []
    for exam in audit["exams"]:
        assert digest(Path(exam["source_pdf"])) == exam["source_pdf_sha256"]
        if digest(ROOT / exam["published_file"]) != exam["published_sha256"]:
            drifts.append(exam["published_file"])
        pages = set()
        for question in exam["questions"]:
            assert question["source_pages"]
            for evidence in question["source_evidence"]:
                pages.add(evidence["pdf_page"])
                width, height = evidence["image_size"]
                x0, y0, x1, y1 = evidence["crop_bbox"]
                assert 0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height
                source_render = Path(evidence["source_render"])
                if source_render not in checked_renders:
                    assert digest(source_render) == evidence["sha256"]
                    checked_renders.add(source_render)
            assert question["text_status"] in {"match", "mismatch", "partial"}
        assert pages == set(range(1, exam["source_page_count"] + 1))
    assert len(checked_renders) == 64
    for figure in audit.get("figure_assets", []):
        width, height = figure["source_render_size"]
        x0, y0, x1, y1 = figure["crop_bbox"]
        assert 0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height
        path = ROOT / figure["path"]
        assert path.is_file(), str(path)
        if figure.get("sha256"):
            assert digest(path) == figure["sha256"], str(path)
    summary = {
        "questions": len(records),
        "text_status": dict(Counter(q["text_status"] for q in records)),
        "source_pages": len(checked_renders),
        "figures": len(audit.get("figure_assets", [])),
        "hints": len(audit["hints"]),
        "numeric_candidates": len(audit["numeric_export_candidates"]),
        "published_drift_since_review": drifts,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--render-figures", action="store_true")
    mode.add_argument("--hints", action="store_true")
    mode.add_argument("--numeric-candidates", action="store_true")
    args = parser.parse_args()
    audit = json.loads(AUDIT.read_text())
    if args.render_figures:
        render_figures(audit)
    elif args.hints:
        print(json.dumps(audit["hints"], ensure_ascii=False, indent=2))
    elif args.numeric_candidates:
        print(json.dumps({
            "policy": audit["numeric_export_policy"],
            "candidates": audit["numeric_export_candidates"],
        }, ensure_ascii=False, indent=2))
    else:
        validate(audit)


if __name__ == "__main__":
    main()
