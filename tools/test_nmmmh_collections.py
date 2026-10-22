#!/usr/bin/env python3
"""Data/source and isolated Playwright regression for 2025/2026 collections."""
import argparse
import copy
import hashlib
import json
import re
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'subjects/nmmmh/audit/collections-2025-2026'

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def data_checks(source=None):
    from import_nmmmh_collections import numeric_docx,numeric_midterm
    from PIL import Image
    manifest=read(ROOT/'subjects/nmmmh/manifest.json');groups=manifest['collections']
    assert [c['id'] for c in groups]==['de-cuong-2025','de-giua-ki-2026']
    assert [c['name'] for c in groups]==['Đề cương 2025','Đề giữa kì 2026']
    assert [len(c['exams']) for c in groups]==[7,2]
    baseline=read(AUDIT/'preserved_legacy_sha256.json')
    originals=read(ROOT/'subjects/nmmmh/audit/single-answer-review/original_questions.json')
    # KTMT remains byte-identical. Legacy NMMMH is intentionally repaired in
    # the subsequent migration and checked by test_nmmmh_reference.py.
    for p,digest in baseline.items():
        if not p.startswith('subjects/nmmmh/'):assert sha(ROOT/p)==digest,p
    rows=[]
    for c in groups:
        for exam in c['exams']:
            qs=read(ROOT/exam['question_file']);rows+=qs
            expected=list(range(1,41)) if exam['id'].endswith('ca-2') else [n for n in range(1,41) if n not in {21,22,23}] if exam['id'].endswith('ca-1') else list(range(1,exam['question_count']+1))
            assert [int(q['source_question_number']) for q in qs]==expected
            assert [q['source_order'] for q in qs]==list(range(len(qs)))
            assert len(qs)==exam['question_count']
            assert sum(bool(q['correct_answer']) for q in qs)==exam['graded_count']
            for q in qs:
                assert q['collection_id']==c['id'] and q['source_exam_id']==exam['id']
                assert q['subject_id']=='nmmmh' and q['chapter_id'] in q['chapter_ids']
                assert all(cid in {ch['id'] for ch in manifest['chapters']} for cid in q['chapter_ids'])
                assert q['hint'] and not re.search(r'(?:chọn|đáp án đúng\s*(?:là|:))\s*[ABCD]\b',q['hint'])
                assert len(q['hint'].splitlines())<=4
                assert q['source_reference']['sha256']
                if source:assert sha(source/q['source_reference']['file'])==q['source_reference']['sha256']
                if q['correct_answer']:
                    assert q['correct_answer'] in 'ABCD'
                    assert q[q['correct_answer']]['text'].strip() or any(b['type']=='image' for b in q[q['correct_answer']]['blocks'])
                    if q['verification_status']=='source_marked':assert q['correct_answer']==q['source_marked_answer']
                else:assert q['needs_review']
                for l in 'ABCD':assert q[l]['source_label']==l
                historical=originals.get(q['id'],q)
                if historical.get('independent_check'):
                    blank=copy.deepcopy(historical);blank['correct_answer']=None;blank['source_marked_answer']='POISON';blank['answer_audit']={}
                    n=int(q['source_question_number'])
                    again=numeric_docx(blank,exam['id'].rsplit('-',1)[1],n) if c['id']=='de-cuong-2025' else numeric_midterm(blank,int(exam['id'][-1]),n)
                    assert json.loads(json.dumps(again))==historical['independent_check'],q['id']
                    if historical['correct_answer']:assert again['valid_options']==[historical['correct_answer']]
                if c['id']=='de-giua-ki-2026':assert q['source_radio_selection_used_as_key'] is False
    assert len(rows)==367 and len({q['id'] for q in rows})==367
    assert not any(q['source_exam_id']=='de-thi-k16-1' for q in rows)
    taxonomy={t['code']:t['topic'] for t in read(AUDIT/'taxonomy.json')['topics']}
    for q in rows:
        if q['chapter_child']:assert taxonomy[q['chapter_child']['code']]==q['chapter_child']['name']
    # Every native question is preserved once, with the exact source option
    # order and formatting evidence; the one image-only option recovery is explicit.
    by_id={q['id']:q for q in rows}
    native=[q for f in AUDIT.glob('*-native.json') for q in read(f)['questions']]
    assert len(native)==290
    for old in native:
        q=originals.get(old['id'],by_id[old['id']])
        assert q['question_blocks']==old['question_blocks']
        assert q['source_mark_candidates']==old['source_mark_candidates']
        for l in 'ABCD':
            if not q.get('option_transcription_notes'):
                assert q[l]['text']==old[l]['text'] and q[l]['blocks']==old[l]['blocks']
    images={b['src'] for q in rows for holder in [q]+[q[l] for l in 'ABCD'] for b in holder.get('question_blocks',holder.get('blocks',[])) if b['type']=='image'}
    for path in images:
        assert not path.startswith('data:') and (ROOT/path).is_file()
        with Image.open(ROOT/path) as img:img.verify()
    inventory=read(AUDIT/'pdf_inventory.json');crops=read(AUDIT/'crop_manifest.json')
    assert len(crops)==41
    for crop in crops:
        assert crop['sha256']==sha(ROOT/crop['path'])
        assert crop['visual_review']=='visually_compared_final_crop_with_original_page'
        assert crop['question_id'] in by_id
        current=by_id[crop['question_id']]
        assert crop['path'] in current['images']+current.get('normalization',{}).get('original_images',[])
        ca=int(by_id[crop['question_id']]['source_exam_id'][-1]);page=inventory[ca-1]['pages'][crop['source_page']-1]
        assert crop['source_sha256']==page['sha256']
        if source:
            original=Image.open(page['path']);actual=Image.open(ROOT/crop['path'])
            assert original.crop(crop['source_box_pixels']).tobytes()==actual.tobytes()
    # Critical independent findings must not regress to screenshot selections.
    assert by_id['nmmmh-de-giua-ki-2026-ca-2-39']['correct_answer']=='B'
    assert by_id['nmmmh-de-giua-ki-2026-ca-1-37']['correct_answer']=='B'
    for id,key in [('nmmmh-de-cuong-2025-tonghop3-16','A'),('nmmmh-de-giua-ki-2026-ca-2-24','A'),('nmmmh-de-giua-ki-2026-ca-2-7','D'),('nmmmh-de-giua-ki-2026-ca-2-1','A')]:
        assert by_id[id]['correct_answer']==key and not by_id[id]['needs_review']
    print(f'PASS collection data: 9 exams, 367 records, source order/marks and frozen originals, {len(images)} live assets, 41 exact unscaled archived crops, KTMT unchanged',flush=True)
    return manifest,rows


def browser_checks(url,manifest,rows):
    from playwright.sync_api import sync_playwright
    folder=Path(tempfile.mkdtemp(prefix='nmmmh-collections-browser-'));base=url.rstrip('/')+'/'
    with sync_playwright() as p:
        browser=p.chromium.launch();context=browser.new_context(viewport={'width':1440,'height':1000})
        page=context.new_page();errors=[];failures=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('response',lambda r:failures.append((r.status,r.url)) if r.status>=400 and 'favicon' not in r.url else None)
        def go(fragment,selector='#practice-form'):
            page.goto(base+'#subject=nmmmh'+fragment);page.wait_for_selector(selector)
        go('');assert page.locator('.exam-detail-card').count()==5
        assert page.locator('.collection-card').count()==3
        for c in manifest['collections']:
            go('&collection='+c['id'])
            qs=[q for q in rows if q['collection_id']==c['id']]
            assert page.locator('.exam-detail-card').count()==len(c['exams'])
            assert page.evaluate('nmmmh.questions.length')==len(qs)
            assert page.evaluate('practicePool().length')==len(qs)
            assert page.evaluate('nmmmh.questions.every(q=>nmmmh.allQuestions.find(a=>a.id===q.id)===q)')
            for chapter in manifest['chapters']:
                expected=[q['id'] for q in qs if chapter['id'] in q['chapter_ids']]
                assert page.evaluate('(id)=>nmmmh.questions.filter(q=>q.chapter_ids.includes(id)).map(q=>q.id)',chapter['id'])==expected
            page.screenshot(path=str(folder/(c['id']+'-desktop.png')),full_page=True)
            # One canonical bank for whole exams, per-exam and aggregate chapters.
            for exam in c['exams']:
                go('&collection='+c['id']+'&exam='+exam['id'],'#full-start')
                page.locator('#full-start').click();page.wait_for_selector('.question-card')
                expected=[q['source_question_number'] for q in qs if q['source_exam_id']==exam['id']]
                assert page.locator('.map-dot').all_text_contents()==expected
                page.locator('#finish-now').click()
                assert page.evaluate('state.persisted.history.at(-1).collection_id')==c['id']
            go('&collection='+c['id'])
            page.locator('#practice-options').check();page.locator('#practice-form button[type="submit"]').click()
            page.wait_for_selector('.question-card')
            # Render and grade EVERY new question. Click the actual canonical
            # option buttons after verifying display mapping; no key mutation.
            for index,q in enumerate(qs):
                page.locator(f'[data-index="{index}"]').click()
                assert page.locator('.question-id').inner_text()==f"Câu {q['source_question_number']}"
                assert page.locator('.option-key').all_text_contents()==list('ABCD')
                page.locator('#show-hint').click()
                assert page.locator('.quick-hint').count()==1
                assert page.locator('.answer-explanation').count()==0
                assert page.locator('.katex-error').count()==0,q['id']
                for img in page.locator('.question-card img').all():img.evaluate('img=>img.decode()')
                if q['correct_answer']:
                    answer=q['correct_answer'];page.locator(f'[data-option="{answer}"]').click()
                    assert page.locator('.feedback.correct').count()==1,q['id']
                    assert page.evaluate('(id)=>state.quiz.answers[id]',q['id'])==answer
                if index%50==0:print(f'  rendered {c["id"]}: {index+1}/{len(qs)}',flush=True)
            page.locator('#finish-now').click()
            assert page.locator('.score-card strong').inner_text()=='10.00/10'
            graded=sum(bool(q['correct_answer']) for q in qs)
            assert page.evaluate('state.persisted.history.at(-1).graded')==graded
            assert page.evaluate('state.persisted.history.at(-1).ungraded')==len(qs)-graded
            # Mobile, option shuffle, reload and separated groups.
            go('&collection='+c['id'])
            page.locator('#practice-count').fill('3');page.locator('#practice-random').check()
            page.locator('#practice-options').check();page.locator('#practice-mode').select_option('exam')
            page.locator('#practice-form button[type="submit"]').click();page.wait_for_selector('.question-card')
            assert page.locator('#show-hint,#show-answer,.feedback').count()==0
            page.locator('.option-btn:not(:disabled)').first.click()
            before=page.evaluate('JSON.stringify([state.quiz.questions.map(q=>q.id),state.quiz.answers,state.quiz.optionOrders])')
            page.reload();page.wait_for_selector('.question-card')
            assert page.evaluate('JSON.stringify([state.quiz.questions.map(q=>q.id),state.quiz.answers,state.quiz.optionOrders])')==before
            for width in [390,320]:
                page.set_viewport_size({'width':width,'height':844});page.screenshot(path=str(folder/f'{c["id"]}-{width}.png'),full_page=True)
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            page.set_viewport_size({'width':1440,'height':1000})
            page.locator('#finish-now').click()
            print('PASS collection browser: '+c['id']+'; all questions render/grade, safe shuffle, unknowns excluded, history/reload/mobile',flush=True)
        # Legacy home still defaults to its original five exams.
        go('');assert page.evaluate('nmmmh.questions.length')==173
        go('&collection=de-cuong-2025')
        page.locator('.collection-card',has_text='Đề giữa kì 2026').click();page.wait_for_selector('#practice-form')
        page.wait_for_function('nmmmh.collection === "de-giua-ki-2026" && nmmmh.questions.length === 77')
        assert page.evaluate('nmmmh.questions.length')==77
        page.locator('.collection-card',has_text='Bộ đề các khóa').click();page.wait_for_selector('#practice-form')
        page.wait_for_function('nmmmh.collection === "legacy" && nmmmh.questions.length === 173')
        assert page.evaluate('nmmmh.questions.length')==173
        assert not errors,errors;assert not failures,failures
        browser.close()
    print('ALL COLLECTION CHECKS PASSED. Screenshots: '+str(folder),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--url');parser.add_argument('--source',type=Path);args=parser.parse_args()
    manifest,rows=data_checks(args.source)
    if args.url:browser_checks(args.url,manifest,rows)

if __name__=='__main__':main()
