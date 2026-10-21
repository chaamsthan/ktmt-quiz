#!/usr/bin/env python3
"""Collect explicit visual review findings into reproducible ID-based overlays.

Does not infer text or answers from OCR. Applies only documented high-confidence
transcriptions. Original JSON in DAPAN_KIEMCHUNG remains an immutable input.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'subjects/nmmmh/audit'


def read(name,default=None):
    p=AUDIT/name
    return json.loads(p.read_text()) if p.is_file() else default


def findings():
    other=read('source_other_review.json',{})
    k16=read('source_k16_review.json',{})
    for exam in other.get('exams',[]):
        for row in exam['questions']:
            yield row['question_id'],exam['source_pdf'],row.get('source_pages',[]),row,row.get('mismatches',[])
    docs={r['exam_id']:r['pdf_path'] for r in k16.get('source_documents',[])}
    for row in k16.get('questions',[]):
        yield row['id'],docs[row['exam_id']],row.get('pdf_pages',[]),row,row.get('corrections',[])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True,type=Path)
    args=parser.parse_args();source=args.source.resolve()
    original=json.loads((source/'DAPAN_KIEMCHUNG/questions_verified.json').read_text())
    published={e['id'] for e in json.loads((ROOT/'subjects/nmmmh/manifest.json').read_text())['exams']}
    by_id={q['id']:q for q in original if q['source_exam_id'] in published}
    overrides={};change_log=[]
    for identifier,file,pages,row,edits in findings():
        q=by_id[identifier]
        status='visually_compared'
        if row.get('unchecked_fields') or row.get('review_status') in ('evidence_pending','in_progress'):
            status='partial_visual_review'
        issues=[]
        issue_log=copy.deepcopy(row.get('source_issues',[]))
        for issue in issue_log:
            # Fixed crops/transcriptions and intentionally false options are
            # evidence, not outstanding failures of source fidelity.
            if isinstance(issue,dict):
                if issue.get('kind')!='source_notation_ambiguity':continue
                issues.append(issue['details'])
            else:issues.append(issue)
        if row.get('unchecked_fields'):issues.append('Chưa xác nhận đầy đủ các trường: '+', '.join(row['unchecked_fields']))
        evidence={'file':str(Path(file).relative_to(source)), 'page':pages[0] if pages else None, 'pages':pages,
                  'pdf_sha256':hashlib.sha256(Path(file).read_bytes()).hexdigest(),
                  'status':status,'review_artifact':'source_k16_review.json' if '-k16-' in identifier else 'source_other_review.json'}
        overrides[identifier]={'source_reference':evidence,'source_fidelity_status':'needs_review' if issues else status,'source_issues':issues,'source_issue_log':issue_log,'edits':[],'image_replacements':[]}
        for edit in edits:
            field=edit.get('field','').removesuffix('.text') if not edit.get('field','').startswith('question_blocks') else edit['field']
            if edit.get('confidence')!='high' or not isinstance(edit.get('new'),str):continue
            if field not in ('question','A','B','C','D') and not re.fullmatch(r'question_blocks\[\d+\]\.text',field):continue
            if field in 'ABCD' and len(field)==1:current=q[field]['text']
            elif field=='question':current=q[field]
            else:current=q['question_blocks'][int(re.search(r'\[(\d+)\]',field)[1])]['text']
            if current!=edit['old']:raise ValueError(f'Stale source correction {identifier} {field}')
            item={'field':field,'old':edit['old'],'new':edit['new'],'evidence':edit.get('evidence',''),'source_pages':pages}
            overrides[identifier]['edits'].append(item)
            change_log.append({'id':identifier,**item})
        # Image assets are created by the visual reviewers and independently
        # opened after crop; collect only assets with a confirmed recorded path.
        replacements=row.get('image_replacements',[])
        replacements += [{'old':item['path'],'new':item['replacement_asset'],
                          'visually_checked_final_asset':True}
                         for item in row.get('published_images',[])
                         if item.get('replacement_asset_visual_status')=='final_asset_visually_inspected']
        for item in replacements:
            if item.get('new') and (ROOT/item['new']).is_file():overrides[identifier]['image_replacements'].append(item)
    assert len(overrides)==173, f'Incomplete visual manifest: {len(overrides)}/173'
    chapter_review=read('chapter_review.json',{})
    if chapter_review:
        assert chapter_review['status']=='complete'
        chapters={c['id']:c for c in chapter_review['chapter_catalog']}
        topics={t['id']:t for t in chapter_review['topic_catalog']}
        assert {r['id'] for r in chapter_review['questions']}==set(overrides)
        for row in chapter_review['questions']:
            assert row['review_complete'] and row['rationale']
            primary=chapters[row['primary_chapter_id']]
            change=overrides[row['id']]
            change['chapter_ids']=row['chapter_ids']
            change['primary_chapter']={'id':int(primary['id']),'name':primary['name'],'status':primary['source_status']}
            change['chapter_review']={k:row[k] for k in ('status','rationale','taxonomy_scope','needs_taxonomy_review','primary_topic_id','topic_ids','topic_review_status')}
            change['official_primary_topic']=topics.get(row['primary_topic_id'])
    previous=read('approved_changes.json',{})
    # Preserve separately reviewed answer decisions, never discard them on
    # a rerun of the source-fidelity assembler.
    for identifier,entry in previous.items():
        if identifier in overrides:
            for field in ('answer_decision','verification_status','verification_notes'):
                if field in entry:overrides[identifier][field]=entry[field]
    (AUDIT/'approved_changes.json').write_text(json.dumps(overrides,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (AUDIT/'ocr_changes.json').write_text(json.dumps(change_log,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'source_records':len(overrides),'text_edits':len(change_log),'questions_edited':len({r['id'] for r in change_log}),'image_replacements':sum(len(r['image_replacements']) for r in overrides.values())}))


if __name__=='__main__':main()
