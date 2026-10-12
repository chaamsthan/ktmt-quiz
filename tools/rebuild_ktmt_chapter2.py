#!/usr/bin/env python3
"""Rebuild only chapter 2 from its visually reviewed PDF transcription.

Run: uv run --with pymupdf python tools/rebuild_ktmt_chapter2.py --write
Without --write, verify the published data and crops against the source.
The original PDF and every other chapter are left intact.
"""

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPT = ROOT / "tools/ktmt_chapter2_source.json"
REPORT = ROOT / "subjects/ktmt/chapter2_audit.json"
LETTERS = "ABCD"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def highlighted_labels(document):
    """Use printed letters and glyph centres, never visual option order.

    PDF text streams can visit A,C,B,D in a two-column layout. A highlight
    can also touch the bottom edge of the preceding line; intersecting the
    whole glyph box is insufficient. Require the letter's centre to be
    inside yellow, then retain the source coordinates as evidence.
    """
    found = {}
    current = None
    for number in range(6, 17):
        page = document[number - 1]
        yellow = [
            pymupdf.Rect(drawing["rect"])
            for drawing in page.get_drawings()
            if drawing.get("fill")
            and drawing["fill"][0] > 0.9
            and drawing["fill"][1] > 0.9
            and drawing["fill"][2] < 0.2
        ]
        events = []
        for block in page.get_text("rawdict")["blocks"]:
            for line in block.get("lines", []):
                chars = [char for span in line["spans"] for char in span["chars"]]
                text = "".join(char["c"] for char in chars)
                for match in re.finditer(r"(?<!\d)([123]\.\d+)\.", text):
                    box = pymupdf.Rect(chars[match.start()]["bbox"])
                    events.append((box.y0, 0, match.group(1), box))
                for match in re.finditer(r"(?<!\S)([a-d])\.", text):
                    box = pymupdf.Rect(chars[match.start()]["bbox"])
                    box |= pymupdf.Rect(chars[match.start() + 1]["bbox"])
                    events.append((box.y0, 1, match.group(1).upper(), box))
        for _, kind, value, box in sorted(events, key=lambda e: (e[0], e[1], e[3].x0)):
            if kind == 0:
                current = value
                continue
            if not current or not current.startswith("2."):
                continue
            centre = pymupdf.Point((box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2)
            evidence = [rect for rect in yellow if rect.contains(centre)]
            if evidence:
                record = {
                    "letter": value,
                    "page": number,
                    "label_rect": [round(v, 3) for v in box],
                    "yellow_rects": [[round(v, 3) for v in rect] for rect in evidence],
                }
                assert current not in found, f"Multiple highlighted labels: {current}"
                found[current] = record
    expected = {f"2.{n}" for n in range(1, 60)}
    assert set(found) == expected, f"Missing or extra labels: {expected ^ set(found)}"
    return found


def build(questions, transcript, evidence, source_sha):
    reviewed = {q["id"]: q for q in transcript["questions"]}
    expected = [f"2.{n}" for n in range(1, 60)]
    assert list(reviewed) == expected
    assert [q["id"] for q in questions if q["id"].startswith("2.")] == expected
    result = copy.deepcopy(questions)
    for question in result:
        if question["id"] not in reviewed:
            continue
        row = reviewed[question["id"]]
        assert len(row["options"]) == 4 and all(row["options"])
        assert row["answer"] == evidence[row["id"]]["letter"], row["id"]
        question["chapter"] = transcript["chapter"]
        question["question"] = row["question"]
        question["source_page"] = row["page"]
        question["correct_answer"] = row["answer"]
        question["answer_evidence"] = "highlighted_in_source_pdf"
        question["question_image"] = None
        question.pop("source_visual", None)
        for letter, text in zip(LETTERS, row["options"]):
            question[letter] = {"text": text, "image": None, "source_label": letter}
            if "^{" in text:
                question[letter]["blocks"] = [{"type": "math", "text": text}]
        visual = transcript["visuals"].get(row["id"])
        if visual:
            path = f"images/ktmt/chapter-2/q-{row['id']}-{visual['kind']}.png"
            question["question_image"] = path
            question["source_visual"] = {**visual, "src": path}
        note = transcript["source_notes"].get(row["id"])
        question["needs_review"] = bool(note)
        question["review_reason"] = note
        question["answer_audit"] = {
            "status": "source_highlight_visually_reviewed",
            "correct_answer": row["answer"],
            "explanation": f"Đáp án {row['answer']} được tô vàng ở trang {evidence[row['id']]['page']} của PDF nguồn."
            + (f"\nLưu ý nguồn: {note}" if note else ""),
        }
        question["source_audit"] = {
            "revision": "ktmt-ch2-2026-10-12",
            "source_pdf": transcript["source_pdf"],
            "source_sha256": source_sha,
            "question_page": row["page"],
            "highlight": evidence[row["id"]],
            "visually_reviewed": True,
        }
    assert [q for q in questions if not q["id"].startswith("2.")] == [
        q for q in result if not q["id"].startswith("2.")
    ]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    transcript_bytes = TRANSCRIPT.read_bytes()
    transcript = json.loads(transcript_bytes)
    source = ROOT / transcript["source_pdf"]
    source_sha = digest(source.read_bytes())
    original = json.loads((ROOT / "questions.json").read_text())
    with pymupdf.open(source) as document:
        evidence = highlighted_labels(document)
        rebuilt = build(original, transcript, evidence, source_sha)
        reviewed = [q for q in rebuilt if q["id"].startswith("2.")]
        if args.write:
            # Generated dataset; only chapter-2 objects are changed.
            (ROOT / "questions.json").write_text(
                json.dumps(rebuilt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        else:
            assert rebuilt == original, "Chapter 2 differs from reviewed transcription; run --write"
        crops = []
        for question in reviewed:
            if not question.get("source_visual"):
                continue
            visual = question["source_visual"]
            rect = pymupdf.Rect(visual["rect"])
            page = document[visual["page"] - 1]
            assert page.rect.contains(rect)
            # 252 dpi keeps register subscripts/table cells legible at full size.
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(3.5, 3.5), clip=rect, alpha=False)
            image_bytes = pixmap.tobytes("png")
            destination = ROOT / visual["src"]
            if args.write:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(image_bytes)
            else:
                assert destination.read_bytes() == image_bytes, destination
            crops.append({
                "id": question["id"], **visual,
                "pixel_size": [pixmap.width, pixmap.height],
                "sha256": digest(image_bytes),
            })
    report = {
        "source_pdf": transcript["source_pdf"],
        "source_sha256": source_sha,
        "transcription_sha256": digest(transcript_bytes),
        "review_method": transcript["review_method"],
        "question_count": len(reviewed),
        "source_highlight_count": len(evidence),
        "answer_policy": "Follow the printed highlighted letter; source inconsistencies are disclosed, not silently corrected.",
        "source_notes": transcript["source_notes"],
        "visuals": crops,
        "highlights": evidence,
    }
    if args.write:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        assert json.loads(REPORT.read_text()) == report
    print(f"{'Rebuilt' if args.write else 'Verified'} chapter 2: {len(reviewed)} questions, "
          f"{len(evidence)} highlighted labels, {len(crops)} exact source crops.")


if __name__ == "__main__":
    main()
