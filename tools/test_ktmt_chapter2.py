#!/usr/bin/env python3
"""Check chapter-2 source fidelity, grading and actual browser rendering.

uv run --with playwright==1.60.0 python tools/test_ktmt_chapter2.py --url http://127.0.0.1:8765/
Uses a fresh browser context; the learner's localStorage is never touched.
"""
import argparse
import json
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
CORRECTED = {"2.10": "D", "2.15": "C", "2.19": "B", "2.34": "C", "2.45": "B", "2.57": "D"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8765/")
    args = parser.parse_args()
    url = args.url.rstrip("/") + "/"
    transcript = json.loads((ROOT / "tools/ktmt_chapter2_source.json").read_text())
    expected = transcript["questions"]
    artifacts = Path(tempfile.mkdtemp(prefix="ktmt-ch2-browser-"))
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        errors, failed = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("response", lambda response: failed.append((response.status, response.url))
                if response.status >= 400 and "favicon" not in response.url else None)

        def start(mode="study"):
            page.goto(url)
            page.wait_for_selector("#quiz-form")
            page.locator("#scope").select_option(transcript["chapter"])
            if mode == "exam":
                page.locator('[data-mode="exam"]').click()
            page.locator('#quiz-form button[type="submit"]').click()
            assert page.evaluate("state.quiz.questions.length") == 59

        start()
        actual = page.evaluate("state.quiz.questions")
        assert [q["id"] for q in actual] == [q["id"] for q in expected]
        for question, source in zip(actual, expected):
            assert question["question"] == source["question"], source["id"]
            assert [question[l]["text"] for l in "ABCD"] == source["options"], source["id"]
            assert question["correct_answer"] == source["answer"], source["id"]
            assert question["source_audit"]["highlight"]["letter"] == source["answer"]
            assert question["source_audit"]["visually_reviewed"]
            assert not any(0xE000 <= ord(c) <= 0xF8FF for c in json.dumps(question, ensure_ascii=False))
        assert {q["id"]: q["correct_answer"] for q in actual if q["id"] in CORRECTED} == CORRECTED
        assert sum(bool(q["question_image"]) for q in actual) == 6
        print("PASS published data: 59 source questions, A–D order, six corrected keys and six crops", flush=True)

        # Exercise every question through the public controls and shared grader.
        for index, source in enumerate(expected):
            assert page.locator(".question-text").inner_text() == source["question"]
            page.locator(f'[data-option="{source["answer"]}"]').click()
            assert page.locator(".feedback.correct").count() == 1, source["id"]
            assert "tô vàng" in page.locator(".answer-explanation").inner_text()
            if index < 58:
                page.locator("#next").click()
        page.locator("#next").click()
        assert page.locator(".score-card strong").inner_text() == "59/59"
        assert page.evaluate("state.persisted.history.at(-1).score") == 10
        print("PASS study: all 59 source-highlight answers grade correctly", flush=True)

        start("exam")
        for index, source in enumerate(expected):
            page.locator(f'[data-option="{source["answer"]}"]').click()
            assert page.locator(".feedback,.answer-explanation").count() == 0
            if index < 58:
                page.locator("#next").click()
        page.locator("#next").click()
        assert page.locator(".score-card strong").inner_text() == "59/59"
        print("PASS exam: answers remain hidden until grading; final result 59/59", flush=True)

        start()
        for width in [1440, 390, 320]:
            page.set_viewport_size({"width": width, "height": 1000})
            for index, source in enumerate(expected):
                page.locator(f'[data-index="{index}"]').click()
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (width, source["id"])
                if any("^{" in option for option in source["options"]):
                    assert page.locator(".options sup").count() > 0
                    assert "^{" not in page.locator(".options").inner_text()
                    assert page.locator(".options").inner_text().count("⊕") == sum(o.count("⊕") for o in source["options"])
                if source["id"] in transcript["visuals"]:
                    image = page.locator(".question-card .source-image-link img")
                    image.evaluate("img => img.decode()")
                    assert image.evaluate("img => img.naturalWidth > 0 && img.naturalHeight > 0")
                    assert page.locator(".question-card .source-image-link").get_attribute("target") == "_blank"
                    assert page.locator(".question-card .source-image-link").get_attribute("href") == actual[index]["question_image"]
                if width in [1440, 390] and source["id"] in ["2.8", "2.17", "2.30", "2.51"]:
                    page.screenshot(path=str(artifacts / f"{source['id']}-{width}.png"), full_page=True)
        # Preserve separate exponents, especially distractors which differ only
        # by exponent placement, multiplication versus XOR, or the exponent sign.
        page.locator('[data-index="28"]').click()
        assert page.locator('[data-option="D"] sup').inner_text() == "S · M"
        page.locator('[data-index="29"]').click()
        assert page.locator('[data-option="D"] sup').all_text_contents() == ["S1 ⊕ S2", "E1 + E2"]
        page.locator('[data-index="50"]').click()
        assert page.locator('[data-option="C"] sup').all_text_contents() == ["S", "E − 127"]
        print("PASS rendering: actual superscripts/XOR, all six decoded images, full-size image links; all 59 questions at 1440/390/320 px", flush=True)

        for question_id in transcript["source_notes"]:
            page.locator(f'[data-index="{int(question_id.split(".")[1]) - 1}"]').click()
            page.locator('[data-option="A"]').click()
            assert transcript["source_notes"][question_id] in page.locator(".answer-explanation").inner_text()
        assert not errors, errors
        assert not failed, failed
        print("PASS source notes: all three source inconsistencies disclosed; no JS errors or failed assets", flush=True)
        context.close()
        browser.close()
    print(f"ALL CHAPTER-2 CHECKS PASSED. Screenshots: {artifacts}")


if __name__ == "__main__":
    main()
