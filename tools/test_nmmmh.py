#!/usr/bin/env python3
"""Data and browser regression checks for the additive NMMMH subject.

Usage: uv run --with playwright==1.60.0 python tools/test_nmmmh.py --url http://127.0.0.1:8765/
Runs in a fresh browser context and does not modify the source dataset.
"""
import argparse
import csv
import json
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright
from import_nmmmh import content_blocks

WEB = Path(__file__).resolve().parents[1]
STORAGE_KEY = "ktmt-quiz-lab-v1"


def data_checks():
    manifest = json.loads((WEB / "subjects/nmmmh/manifest.json").read_text())
    report = json.loads((WEB / "subjects/nmmmh/import_report.json").read_text())
    rows = []
    assets = set()
    for exam in manifest["exams"]:
        questions = json.loads((WEB / exam["question_file"]).read_text())
        assert len(questions) == exam["question_count"]
        assert [q["source_order"] for q in questions] == sorted(q["source_order"] for q in questions)
        for q in questions:
            assert q["subject_id"] == "nmmmh"
            assert q["source_exam_code"] == exam["source_exam_code"]
            if q["chapter_parent"]:
                assert q["chapter_parent"]["name"] == q["chapter"].split(". ", 1)[-1]
            else:
                assert q["chapter_id"] == "unclassified"
            if q["correct_answer"]:
                assert q["answer_audit"]["status"] == "verified"
                assert q["correct_answer"] == q["answer_audit"]["correct_answer"]
            else:
                assert q["needs_review"]
            for holder in [q] + [q[letter] for letter in "ABCD"]:
                for block in holder.get("question_blocks", holder.get("blocks", [])):
                    if block["type"] == "image":
                        path = block["src"]
                        assert path.startswith("images/nmmmh/") and "base64" not in path
                        assert (WEB / path).is_file()
                        assets.add(path)
        rows.extend(questions)
    assert len(manifest["exams"]) == 5
    assert not any(e["id"] == "de-thi-k16-1" for e in manifest["exams"])
    assert not (WEB / "subjects/nmmmh/exams/de-thi-k16-1.json").exists()
    assert not any(q["source_exam_id"] == "de-thi-k16-1" for q in rows)
    assert len(rows) == 173 and len({q["id"] for q in rows}) == 173
    assert sum(bool(q["correct_answer"]) for q in rows) == 149
    assert sum(q["needs_review"] for q in rows) == 24
    assert len(assets) == 28
    assert {str(p.relative_to(WEB)) for p in (WEB / "images/nmmmh").iterdir() if p.is_file()} == assets
    assert [c["unique_count"] for c in report["aggregate"]] == [7, 41, 83, 18, 4, 0]
    assert sum(c["excluded_duplicates"] for c in report["aggregate"]) == 20
    assert len([g for g in report["duplicate_groups"] if g["status"] == "confirmed"]) == 15
    assert len([g for g in report["duplicate_groups"] if g["status"] == "potential"]) == 1
    with (WEB / "subjects/nmmmh/answers.csv").open(encoding="utf-8-sig", newline="") as answer_csv:
        answer_rows = list(csv.DictReader(answer_csv))
    assert len(answer_rows) == 173
    assert not any(r["de"] == "de-thi-k16-1" for r in answer_rows)
    by_id = {q["id"]: q for q in rows}
    for group in report["duplicate_groups"]:
        members = [by_id[s["id"]] for s in group["sources"]]
        assert len({q["chapter_id"] for q in members}) == 1
        if group["status"] == "confirmed":
            assert all(q["correct_answer"] for q in members)
            assert len({json.dumps(content_blocks(q[q["correct_answer"]]["blocks"]), sort_keys=True) for q in members}) == 1
    k16_3 = [q for q in rows if q["source_exam_id"] == "de-thi-k16-3"]
    assert [q["source_question_number"] for q in k16_3] == [str(i) for i in range(2021, 2061)]
    assert next(e for e in manifest["exams"] if e["id"] == "de-thi-k16-3")["year"] is None
    print("PASS data: K16-1 excluded; 5 exams, 173 records, 149 verified answers, 24 review records, 28 images; aggregate removes 20 duplicate copies", flush=True)
    return assets


def browser_checks(url, artifacts, assets):
    url = url.rstrip("/") + "/"
    errors = []
    responses = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        seed = {
            "bookmarks": ["1.1"], "mistakes": ["1.2"],
            "progress": {"1.1": {"seen": 1, "answered": 1, "correct": 1}},
            "history": [{"date": "2026-10-01T00:00:00.000Z", "mode": "study", "total": 1, "correct": 1, "scope": "Chương cũ", "set_id": "de-300-cau"}],
        }
        context.add_init_script(f"if (!localStorage.getItem({json.dumps(STORAGE_KEY)})) localStorage.setItem({json.dumps(STORAGE_KEY)}, {json.dumps(json.dumps(seed))});")
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("response", lambda response: responses.append((response.status, response.url)) if response.status >= 400 and "favicon" not in response.url else None)

        def goto(fragment, selector):
            page.goto(url + fragment)
            page.wait_for_selector(selector)

        def value(expression):
            return page.evaluate(expression)

        def answer_current(correct=True):
            letter = value("state.quiz.questions[state.quiz.index].correct_answer")
            if not letter:
                return
            if not correct:
                letter = next(candidate for candidate in "ABCD" if candidate != letter)
            page.locator(f'[data-option="{letter}"]').click()

        goto("", "#quiz-form")
        assert value("state.questions.length") == 300
        assert page.locator(".exam-card:disabled").count() == 1
        page.locator('#quiz-form button[type="submit"]').click()
        assert value("state.quiz.questions[0].id") == "1.1"
        assert value("state.quiz.questions.length") == 42
        answer_current()
        assert page.locator(".feedback.correct").count() == 1
        page.evaluate("state.quiz.index = state.quiz.questions.length - 1; renderQuiz();")
        page.locator("#next").click()
        assert value("state.persisted.history.at(-1).subject_id") == "ktmt"
        page.locator("#result-home").click()
        assert value("state.persisted.progress['1.1'].answered") == 2
        print("PASS legacy: KTMT 300 questions, 500-question placeholder, original order and shared grading remain functional", flush=True)

        page.locator('.subject-nav a[href="#subject=nmmmh"]').click()
        page.wait_for_selector("#aggregate-form")
        assert page.locator(".exam-detail-card").count() == 5
        assert "de-thi-k16-1" not in page.locator(".nmmmh-exams").inner_text()
        assert value("nmmmh.questions.length") == 173
        assert value("nmmmh.questions.every(q => q.source_exam_id !== 'de-thi-k16-1')")
        assert value("nmmmhPool('all', '2').length") == 41
        assert value("richBlocksHtml([{type:'image',src:'images/nmmmh/test.png'}], false).includes('<img')")
        assert not value("richBlocksHtml([{type:'image',src:'images/nmmmh/test.png'}], false).includes('<a ')")
        assert value("state.persisted.bookmarks.has('1.1')")
        page.screenshot(path=str(artifacts / "nmmmh-home-desktop.png"), full_page=True)
        for asset in assets:
            response = context.request.get(url + asset)
            assert response.ok, f"Missing asset: {asset}"
        print("PASS assets: all 28 retained source images load through relative project paths", flush=True)
        goto("#subject=nmmmh&exam=de-thi-k16-1&chapter=all&action=start", ".error-card")
        assert "Mã đề không tồn tại" in page.locator(".error-card").inner_text()
        page.locator(".error-card a").click()
        page.wait_for_selector("#aggregate-form")

        goto("#subject=nmmmh&exam=de-thi-k16-3&chapter=all&action=start", ".question-card")
        assert value("state.quiz.questions.length") == 40
        assert page.locator(".question-id").inner_text() == "Câu 2021"
        assert page.locator(".map-dot").first.inner_text() == "2021"
        page.locator(".map-dot").last.click()
        assert page.locator(".question-id").inner_text() == "Câu 2060"
        page.reload()
        page.wait_for_selector(".question-card")
        assert page.locator(".question-id").inner_text() == "Câu 2021"

        goto("#subject=nmmmh&exam=de-thi-k16-2&chapter=all&action=start", ".question-card")
        page.locator('[data-index="9"]').click()
        assert page.locator(".options .source-table").count() == 4
        assert page.locator('[data-option="A"] .source-table td').all_text_contents() == ["19", "8", "19", "23"]
        page.screenshot(path=str(artifacts / "nmmmh-matrix-desktop.png"), full_page=True)
        goto("#subject=nmmmh&exam=de-thi-k16-3&chapter=all&action=start", ".question-card")
        page.locator('[data-index="7"]').click()
        assert page.locator(".question-text .source-table").count() == 3
        assert page.locator(".question-text img").count() >= 1
        page.wait_for_function("[...document.querySelectorAll('.question-text img')].every(i => i.complete && i.naturalWidth > 0)")
        assert value("[...document.querySelectorAll('.question-text img')].every(i => i.complete && i.naturalWidth > 0)")
        print("PASS original content: numbering 2021–2060, question tables, option matrices and source images preserved", flush=True)

        goto("#subject=nmmmh&exam=de-thi-nmmmh&chapter=all&action=start", ".question-card")
        answer_current()
        page.locator("#bookmark").click()
        marked_id = value("state.quiz.questions[0].id")
        assert page.locator(".feedback.correct").count() == 1
        assert page.locator(".answer-explanation").count() == 1
        page.locator('[data-index="6"]').click()
        unknown_id = value("state.quiz.questions[state.quiz.index].id")
        assert value("state.quiz.questions[state.quiz.index].correct_answer") is None
        page.locator('[data-option="B"]').click()
        assert page.locator(".feedback.pending").count() == 1
        assert not value(f"state.persisted.mistakes.has({json.dumps(unknown_id)})")
        page.locator('[data-index="7"]').click()
        answer_current(correct=False)
        assert page.locator(".feedback.incorrect").count() == 1
        page.locator("#finish-now").click()
        entry = value("state.persisted.history.at(-1)")
        assert entry["subject_id"] == "nmmmh" and entry["exam"] == "De_thi_NMMMH"
        assert entry["chapter"] == "Cả đề" and entry["total"] == 40
        assert entry["graded"] == 36 and entry["ungraded"] == 4 and entry["correct"] == 1
        assert abs(entry["score"] - 10 / 36) < 1e-9
        assert page.locator(".result-item.is-pending").count() == 4
        history_size = value("state.persisted.history.length")
        page.locator(f'.result-open[data-id="{marked_id}"]').click()
        assert page.locator(".option-btn:not(:disabled)").count() == 0
        page.locator("#finish-now").click()
        assert value("state.persisted.history.length") == history_size
        page.locator("#review-wrong").click()
        assert value("state.quiz.questions.length") == 35
        assert value("state.quiz.questions.every(q => q.correct_answer)")
        print("PASS grading: approved answers only, 4 unknown questions excluded, no false mistakes or duplicate history on review", flush=True)

        goto("#subject=nmmmh&exam=de-thi-k16-3&chapter=all&action=start&mode=exam", ".question-card")
        answer_current()
        assert page.locator(".feedback").count() == 0
        assert page.locator(".answer-explanation").count() == 0
        for index, question in enumerate(value("state.quiz.questions.map(q => ({correct_answer:q.correct_answer}))")):
            if question["correct_answer"]:
                page.locator(f'[data-index="{index}"]').click()
                answer_current()
                assert page.locator(".feedback").count() == 0
        page.locator("#finish-now").click()
        assert page.locator(".score-card strong").inner_text() == "10.00/10"
        assert value("state.persisted.history.at(-1).graded") == 34
        assert value("state.persisted.history.at(-1).ungraded") == 6
        print("PASS exam mode: answers hidden until finish; 34 verified/6 unknown produces 10/10 when all verified answers are correct", flush=True)

        goto("#subject=nmmmh&exam=de-thi-nmmmh", "#exam-chapter-form")
        page.locator("#exam-chapter").select_option("2")
        assert "11 câu" in page.locator("#preview-heading").inner_text()
        page.locator("#exam-random").check()
        page.locator('#exam-chapter-form button[type="submit"]').click()
        assert value("state.quiz.questions.length") == 11
        assert value("state.quiz.context.scope_kind") == "exam_chapter"
        assert value("state.quiz.randomize")
        assert value("state.quiz.questions.every(q => q.chapter_id === '2' && q.source_exam_id === 'de-thi-nmmmh')")
        page.locator("#finish-now").click()
        assert value("state.persisted.history.at(-1).chapter_id") == "2"

        goto("#subject=nmmmh", "#aggregate-form")
        page.locator("#aggregate-chapter").select_option("2")
        page.locator("#aggregate-random").check()
        page.locator('#aggregate-form button[type="submit"]').click()
        assert value("state.quiz.questions.length") == 41
        assert value("state.quiz.context.scope_kind") == "all_exams_chapter"
        assert value("state.quiz.context.exam") == "Tất cả đề"
        assert value("state.quiz.randomize")
        assert value("new Set(state.quiz.questions.map(q => q.source_exam_id)).size") == 5
        assert value("state.quiz.questions.every(q => q.source_exam_id !== 'de-thi-k16-1')")
        assert value("(() => {const keys=state.quiz.questions.map(q=>q.duplicate_status==='confirmed'?q.duplicate_group:q.id);return new Set(keys).size===keys.length;})()")
        assert "Nguồn:" in page.locator(".source-meta").inner_text()
        page.locator("#finish-now").click()
        assert value("state.persisted.history.at(-1).scope_kind") == "all_exams_chapter"

        page.evaluate("startNmmmhQuiz('de-thi-k16-3', 'all', 'study', true)")
        assert not value("state.quiz.randomize")
        assert value("state.quiz.questions.map(q => q.source_question_number)") == [str(i) for i in range(2021, 2061)]
        goto("#subject=nmmmh&exam=de-thi-nmmmh&chapter=1&action=start", ".question-card")
        assert value("state.quiz.questions.length") == 1
        assert value("state.quiz.questions[0].correct_answer") is None
        page.locator("#finish-now").click()
        assert page.locator(".score-card strong").inner_text() == "Chưa chấm"
        assert value("state.persisted.history.at(-1).score") is None
        assert value("state.persisted.history.at(-1).graded") == 0
        assert page.locator("#review-wrong").is_disabled()
        print("PASS three scopes: full exam order, 11-question exam chapter, 41-question deduplicated aggregate; no K16-1 questions; unknown-key group is ungraded, not 0/10", flush=True)

        goto("#subject=nmmmh", "#aggregate-form")
        page.locator("#nmmmh-bookmarks").click()
        assert value("state.quiz.questions.every(q => state.persisted.bookmarks.has(q.id))")
        assert value("state.quiz.questions[0].id") == marked_id
        page.reload()
        page.wait_for_selector(".question-card")
        assert value("state.quiz.context.scope_kind") == "bookmarks"
        goto("#subject=nmmmh&view=history", ".history-table")
        assert "Chương cũ" in page.locator(".history-table").inner_text()
        assert "Tất cả đề" in page.locator(".history-table").inner_text()
        assert "Chưa chấm" in page.locator(".history-table").inner_text()
        assert value("state.persisted.bookmarks.has('1.1')")
        assert value("state.persisted.progress['1.1'].answered") == 2
        page.locator('.subject-nav a[href="#subject=ktmt"]').click()
        page.wait_for_selector("#quiz-form")
        assert value("state.questions.length") == 300
        assert value("state.questions.every(q => !q.subject_id)")
        assert page.locator(".stat-value").nth(2).inner_text() == "1"
        assert page.locator(".stat-value").nth(3).inner_text() == "100%"
        print("PASS storage: history/marks/progress survive reload; KTMT and NMMMH data and statistics remain isolated", flush=True)

        page.set_viewport_size({"width": 390, "height": 844})
        goto("#subject=nmmmh", "#aggregate-form")
        assert value("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(artifacts / "nmmmh-home-mobile.png"), full_page=True)
        goto("#subject=nmmmh&exam=de-thi-k16-2&chapter=all&action=start", ".question-card")
        page.locator('[data-index="9"]').click()
        assert value("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(artifacts / "nmmmh-matrix-mobile.png"), full_page=True)
        goto("#subject=nmmmh&exam=de-thi-k16-3&chapter=all&action=start", ".question-card")
        page.locator('[data-index="7"]').click()
        page.set_viewport_size({"width": 320, "height": 700})
        assert value("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(artifacts / "nmmmh-source-mobile.png"), full_page=True)
        goto("#subject=nmmmh&view=history", ".history-table")
        assert value("document.documentElement.scrollWidth <= innerWidth")
        assert not errors, errors
        assert not responses, responses
        print("PASS responsive: desktop, 390px and 320px; no page overflow, missing assets or JavaScript errors", flush=True)
        context.close()
        browser.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8765/")
    args = parser.parse_args()
    artifacts = Path(tempfile.mkdtemp(prefix="nmmmh-browser-"))
    assets = data_checks()
    browser_checks(args.url, artifacts, assets)
    print(f"ALL CHECKS PASSED. Screenshots: {artifacts}")


if __name__ == "__main__":
    main()
