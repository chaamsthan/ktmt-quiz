#!/usr/bin/env python3
"""Integration tests for NMMMH upgrades; isolated browser storage only."""
import argparse
import json
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://127.0.0.1:8765/')
    args=parser.parse_args();base=args.url.rstrip('/')+'/'
    manifest=json.loads((ROOT/'subjects/nmmmh/manifest.json').read_text())
    rows=[q for e in manifest['exams'] for q in json.loads((ROOT/e['question_file']).read_text())]
    assert len(rows)==173 and len({q['id'] for q in rows})==173
    assert len(manifest['exams'])==5 and not any(q['source_exam_id']=='de-thi-k16-1' for q in rows)
    assert all(q['chapter_ids'] and q['chapter_id'] in q['chapter_ids'] for q in rows)
    assert all(q.get('hint') for q in rows), 'All published questions need a short hint'
    folder=Path(tempfile.mkdtemp(prefix='nmmmh-upgrade-browser-'))
    with sync_playwright() as p:
        browser=p.chromium.launch()
        context=browser.new_context(viewport={'width':1440,'height':1000})
        page=context.new_page();errors=[];failed=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('response',lambda r:failed.append((r.status,r.url)) if r.status>=400 and 'favicon' not in r.url else None)

        def go(fragment,selector):
            page.goto(base+'#subject=nmmmh'+fragment);page.wait_for_selector(selector)

        go('','#practice-form')
        assert page.locator('.exam-detail-card').count()==5
        assert page.evaluate('practicePool().length')==173
        # One source bank covers every question, even when not deduplicated.
        assert page.evaluate('nmmmh.questions.every(q => (q.chapter_ids || [q.chapter_id]).some(id => nmmmh.manifest.chapters.some(c => c.id === id)))')
        for chapter in manifest['chapters']:
            expected=[q['id'] for q in rows if chapter['id'] in q['chapter_ids']]
            actual=page.evaluate('(id)=>nmmmh.questions.filter(q=>(q.chapter_ids||[q.chapter_id]).includes(id)).map(q=>q.id)',chapter['id'])
            assert actual==expected
        print('PASS coverage: all 173 stable source questions are in chapter practice; excluded exam remains excluded',flush=True)
        page.screenshot(path=str(folder/'home-desktop.png'),full_page=True)

        # Exercise all questions through study rendering, including every
        # table, source image and every canonical answer-to-display mapping.
        page.evaluate("history.replaceState(null,'','#subject=nmmmh&practice=1'); startQuiz('practice',false,'study',nmmmh.questions,{...nmmmhContext('all','all'),shuffle_options:true})")
        orders=page.evaluate('state.quiz.optionOrders')
        expected_keys={q['id']:q['correct_answer'] for q in rows}
        for index,q in enumerate(rows):
            page.locator(f'[data-index="{index}"]').click()
            assert page.locator('.question-id').inner_text()==f"Câu {q['source_question_number']}"
            assert page.locator('.option-key').all_text_contents()==list('ABCD')
            assert set(orders[q['id']])==set('ABCD')
            page.locator('#show-hint').click()
            assert page.locator('.quick-hint').count()==1
            assert page.locator('.answer-explanation').count()==0
            assert page.locator('.quick-hint .katex-error').count()==0
            for image in page.locator('.question-card img').all():
                image.evaluate('img=>img.decode()')
                assert image.evaluate('img=>img.naturalWidth>0')
            if q['correct_answer']:
                answer=q['correct_answer']
                page.locator(f'[data-option="{answer}"]').click()
                assert page.locator('.feedback.correct').count()==1,q['id']
                assert page.locator('.option-btn.correct .option-key').inner_text()=='ABCD'[orders[q['id']].index(answer)]
                assert not page.locator('.answer-explanation details').get_attribute('open')
            assert page.locator('.katex-error').count()==0,q['id']
        page.locator('#finish-now').click()
        graded=sum(bool(q['correct_answer']) for q in rows)
        assert page.evaluate('state.persisted.history.at(-1).graded')==graded
        assert page.locator('.score-card strong').inner_text()=='10.00/10'
        assert page.evaluate('state.quiz.questions.map(q=>q.correct_answer)')==list(expected_keys.values())
        before=page.evaluate('state.persisted.history.length')
        page.locator('.result-open').first.click()
        assert page.locator('.option-btn:not(:disabled)').count()==0
        page.locator('#finish-now').click()
        assert page.evaluate('state.persisted.history.length')==before
        print('PASS all-question study: hints separated, all images loaded, math rendered, shuffled display maps to immutable correct IDs, 10/10 on verified subset',flush=True)

        # Explicit new attempt (not automatic resume).
        go('&exam=de-thi-nmmmh','#full-start')
        page.locator('#full-mode').select_option('exam');page.locator('#full-start').click()
        first=page.evaluate('state.quiz.questions[0]')
        before_progress=page.evaluate('(id)=>state.persisted.progress[id]?.answered||0',first['id'])
        for letter in ['A','B','C',first['correct_answer']]:page.locator(f'[data-option="{letter}"]').click()
        assert page.locator('.feedback,.quick-hint,.answer-explanation,#show-hint').count()==0
        assert page.evaluate('(id)=>state.persisted.progress[id]?.answered||0',first['id'])==before_progress
        page.locator('[data-index="2"]').click()
        answers=page.evaluate('state.quiz.answers');order=page.evaluate('state.quiz.optionOrders')
        page.reload();page.wait_for_selector('.question-card')
        assert page.evaluate('state.quiz.index')==2 and page.evaluate('state.quiz.answers')==answers
        assert page.evaluate('state.quiz.optionOrders')==order
        page.locator('#finish-now').click()
        assert page.evaluate('(id)=>state.persisted.progress[id].answered',first['id'])==before_progress+1
        print('PASS exam isolation and reload: no immediate grading/stat changes; answer switching counts once; exact question/order/choices survive reload',flush=True)

        # Per-session study statistics: changing answer is one attempt, not
        # several trials that leak correct answers through dashboard counters.
        go('&exam=de-thi-at17-bo-1','#full-start');page.locator('#full-start').click()
        qid=page.evaluate('state.quiz.questions[0].id')
        before_stats=page.evaluate('(id)=>({...state.persisted.progress[id]})',qid)
        correct=page.evaluate('state.quiz.questions[0].correct_answer')
        wrong=next(l for l in 'ABCD' if l!=correct)
        page.locator(f'[data-option="{wrong}"]').click();page.locator(f'[data-option="{correct}"]').click()
        after=page.evaluate('(id)=>state.persisted.progress[id]',qid)
        assert after['answered']==before_stats.get('answered',0)+1
        assert after['correct']==before_stats.get('correct',0)+1
        page.reload();page.wait_for_selector('.question-card')
        page.locator(f'[data-option="{correct}"]').click()
        assert page.evaluate('(id)=>state.persisted.progress[id].answered',qid)==after['answered']
        print('PASS study statistics: final answer updates one attempt; reload does not double count',flush=True)

        empty_chapter=next(c['id'] for c in manifest['chapters'] if not any(q['source_exam_id']=='de-thi-at17-bo-1' and c['id'] in q['chapter_ids'] for q in rows))
        go('&exam=de-thi-at17-bo-1&chapter='+empty_chapter+'&action=start','.notice')
        assert page.locator('.loading-card').count()==0
        assert 'chưa có câu hỏi' in page.locator('#app').inner_text()
        # Empty filter and excessive question count show inline errors.
        go('','#practice-form')
        page.evaluate("state.persisted.mistakes = new Set(nmmmh.questions.filter(q=>!q.correct_answer).map(q=>q.id)); renderNmmmhHome()")
        assert page.locator('#nmmmh-mistakes').is_disabled()
        page.locator('#practice-status').select_option('mistakes')
        assert page.evaluate('practicePool().length')==0
        page.locator('#practice-status').select_option('all')
        for box in page.locator('[name="practice-chapter"]').all():box.uncheck()
        page.locator('#practice-form button[type="submit"]').click()
        assert page.locator('#practice-error').is_visible()
        page.locator('[name="practice-chapter"][value="2"]').check()
        page.locator('#practice-count').fill('3');page.locator('#practice-options').check();page.locator('#practice-random').check()
        page.locator('#practice-form button[type="submit"]').click();page.wait_for_selector('.question-card')
        assert page.evaluate('state.quiz.questions.length')==3
        assert page.evaluate("state.quiz.questions.every(q=>q.chapter_ids.includes('2'))")
        page.locator('.question-card img').first.click() if page.locator('.question-card img').count() else None
        if page.locator('#nmmmh-image-dialog[open]').count():page.locator('[data-zoom="close"]').click()
        print('PASS safe filtering: empty chapter and filters recover, question limits and multi/single-chapter pools use same records',flush=True)

        # Always exercise zoom, not only when a randomized short set has an image.
        go('&exam=de-thi-k16-3','#full-start');page.locator('#full-start').click()
        page.locator('[data-index="3"]').click()
        page.locator('.question-card img').first.click()
        assert page.locator('#nmmmh-image-dialog[open]').count()==1
        page.locator('[data-zoom="in"]').click()
        assert page.locator('#nmmmh-image-dialog img').get_attribute('data-width')=='130'
        page.keyboard.press('Escape');assert page.locator('#nmmmh-image-dialog[open]').count()==0
        print('PASS source-image zoom: opens, enlarges, and closes with keyboard without selecting an answer',flush=True)

        page.evaluate("state.persisted.bookmarks.add(nmmmh.questions.find(q=>q.correct_answer).id); startNmmmhSavedQuiz('bookmarks')")
        page.locator('[data-option="A"]').click()
        saved_answers=page.evaluate('state.quiz.answers')
        page.reload();page.wait_for_selector('.question-card')
        assert page.evaluate('state.quiz.answers')==saved_answers
        assert page.evaluate('state.quiz.context.scope_kind')=='bookmarks'
        print('PASS bookmarked-review session survives reload',flush=True)

        for width in (390,320):
            page.set_viewport_size({'width':width,'height':844})
            go('','#practice-form');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(folder/f'home-{width}.png'),full_page=True)
            go('&exam=de-thi-k16-2','#full-start');page.locator('#full-start').click();page.locator('[data-index="9"]').click()
            page.locator('#show-hint').click()
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(folder/f'matrix-{width}.png'),full_page=True)
        assert not errors,errors
        assert not failed,failed
        print('PASS desktop/mobile: 1440/390/320; no missing requests or JavaScript errors',flush=True)
        context.close()
        for raw in ['{"history":{},"progress":null,"bookmarks":[],"mistakes":[]}','not json']:
            c=browser.new_context();c.add_init_script('localStorage.setItem("ktmt-quiz-lab-v1",'+json.dumps(raw)+')')
            s=c.new_page();s.goto(base+'#subject=nmmmh&view=history');s.wait_for_selector('.history-table');assert not s.locator('.error-card').count();c.close()
        c=browser.new_context()
        c.add_init_script("Storage.prototype.setItem=function(){throw new DOMException('Quota','QuotaExceededError')}")
        s=c.new_page();se=[];s.on('pageerror',lambda e:se.append(str(e)))
        s.goto(base+'#subject=nmmmh&exam=de-thi-at17-bo-1&chapter=all&action=start');s.wait_for_selector('.question-card');s.locator('.option-btn').first.click()
        assert not se and 'không cho lưu' in s.locator('#app').inner_text();c.close()
        browser.close()
    print('PASS storage corruption/quota fallback; no learner browser data changed')
    print(f'ALL UPGRADE CHECKS PASSED; screenshots={folder}')


if __name__=='__main__':main()
