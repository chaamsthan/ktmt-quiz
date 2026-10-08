#!/usr/bin/env python3
"""Import the approved, verified dataset into the existing static quiz.

This only writes subjects/nmmmh and images/nmmmh. Original questions.json and
exam_sets.json stay intact. Every exam is written and logged before the next.
"""
import argparse
import csv
import hashlib
import json
import re
import shutil
import unicodedata
from collections import defaultdict
from pathlib import Path

WEB = Path(__file__).resolve().parents[1]

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def normal(text):
    text = unicodedata.normalize('NFKC', text).lower()
    text = text.replace('kí', 'ký').replace('–', '-').replace('−', '-').replace('’', "'").replace('“', '"').replace('”', '"')
    text = re.sub(r'^đáp án nào (?:sau đây|dưới đây)', 'đáp án nào', text)
    return re.sub(r'\s+', '', text).rstrip('.?')

def content_blocks(blocks):
    result=[]
    for b in blocks:
        if b['type']=='text':
            if b['text'].startswith('Hình '): continue
            result.append(['text',normal(b['text'])])
        elif b['type']=='table':result.append(['table',[[normal(cell) for cell in row] for row in b['rows']]])
        elif b['type']=='image':result.append(['image',Path(b['src']).name])
    return result

def fingerprint(q):
    stem = re.sub(r'^Hình[^\n]*\n?', '', q['question'], flags=re.M)
    choices = sorted(json.dumps(content_blocks(q[l].get('blocks',[])) or [['text',normal(q[l]['text'])]], ensure_ascii=False, sort_keys=True) for l in 'ABCD')
    assets = content_blocks([b for b in q.get('question_blocks',[]) if b['type']!='text'])
    payload=json.dumps([normal(stem),choices,assets],ensure_ascii=False,sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()

def source_reference(q):
    return {k:q[k] for k in ['id','source_exam_id','source_exam_code','source_question_number','source_file']}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source', required=True, type=Path)
    args=parser.parse_args()
    root=args.source.resolve()
    stage=root/'DAPAN_KIEMCHUNG'
    taxonomy=json.loads((root/'TONGQUANKIENTHUC/NMMMH_Phan_loai_kien_thuc.json').read_text())
    classified=json.loads((root/'DeThiOCR/PHAN_LOAI_THEO_CHUONG/questions_classified.json').read_text())
    questions=json.loads((stage/'questions_verified.json').read_text())
    exams=json.loads((stage/'exams.json').read_text())
    source_map={(q['source_file'],q['source_question_number']):q for q in classified['questions']}
    assert len(questions)==len(source_map) and len({q['id'] for q in questions})==len(questions)
    # Publication exclusions live in the website, not in the original DOCX
    # or approved answer bank. Re-importing must not restore a removed exam.
    exclusions_file=WEB/'subjects/nmmmh/excluded_exams.json'
    exclusions=json.loads(exclusions_file.read_text()) if exclusions_file.is_file() else {}
    excluded=set(exclusions.get('excluded_exam_ids',[]))
    known_exam_ids={e['id'] for e in exams}
    assert excluded <= known_exam_ids, f'Unknown excluded exams: {excluded-known_exam_ids}'
    exams=[e for e in exams if e['id'] not in excluded]
    included={e['id'] for e in exams}
    questions=[q for q in questions if q['source_exam_id'] in included]
    for q in questions:
        original=source_map[(q['source_file'],q['source_question_number'])]
        assert q['chapter_parent']==original['chapter_parent'] and q['chapter_child']==original['chapter_child']
        assert q['correct_answer'] is None or (q['answer_audit']['status']=='verified' and q['correct_answer']==q['answer_audit']['correct_answer'])
        q['subject_id']='nmmmh'
        q['subject']='Mật mã học'
        # Code is the source file stem, not a newly invented examination code.
        q['source_exam_code']=Path(q['source_file']).stem
        q['duplicate_group']=None
        q['duplicate_status']=None
        q.pop('duplicate_sources',None)
        q['content_fingerprint']=fingerprint(q)
        q['classification_needs_review']=bool(q['chapter_child'] and q['chapter_child']['source']!='knowledge_tree')
        for holder in [q]+[q[l] for l in 'ABCD']:
            blocks=holder.get('question_blocks',holder.get('blocks',[]))
            for b in blocks:
                if b['type']=='image':
                    src=stage/b['src']; dst=WEB/b['src']
                    assert src.is_file(),src
                    dst.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(src,dst)
                    dst.chmod(0o644)

    groups=defaultdict(list)
    for q in questions:
        if not q.get('source_missing'):groups[q['content_fingerprint']].append(q)
    duplicate_report=[]
    for key, group in groups.items():
        if len(group)<2:continue
        buckets=defaultdict(list)
        for q in group:
            answer=q['correct_answer']
            token=json.dumps(content_blocks(q[answer]['blocks']),ensure_ascii=False,sort_keys=True) if answer else None
            # Unknown keys are potential duplicates and are never collapsed.
            buckets[token].append(q)
        for answer, members in buckets.items():
            if len(members)<2:continue
            confirmed=answer is not None
            group_id=hashlib.sha256((key+(answer or 'unknown')).encode()).hexdigest()
            references=[source_reference(q) for q in members]
            duplicate_report.append({'group_id':group_id,'status':'confirmed' if confirmed else 'potential','sources':references})
            for q in members:
                q['duplicate_group']=group_id
                q['duplicate_status']='confirmed' if confirmed else 'potential'
                q['duplicate_sources']=references

    chapters=[{'id':str(c['id']),'name':c['name'],'label':f'Chương {c["id"]}. {c["name"]}','source_status':c['status']} for c in taxonomy['chapters']]
    chapters.append({'id':'unclassified','name':'Chưa phân loại','label':'Chưa phân loại','source_status':'missing_source'})
    target=WEB/'subjects/nmmmh'
    logs=[];catalog=[]
    for exam in exams:
        rows=[q for q in questions if q['source_exam_id']==exam['id']]
        assert len(rows)==exam['question_count']
        assert [q['source_order'] for q in rows]==sorted(q['source_order'] for q in rows)
        code=Path(exam['source_file']).stem
        headings=exam['source_headings']
        title=exam['title']
        period=next((h for h in headings if 'THI KTHP' in h),title)
        year=re.search(r'20\d{2}(?:[-–]20\d{2})?',period)
        attempt=re.search(r'LẦN\s+(\d+)',period,re.I)
        meta={**exam,'source_exam_code':code,'subject':'Mật mã học','year':year[0] if year else None,
              'attempt':int(attempt[1]) if attempt else None,
              'question_file':f'subjects/nmmmh/exams/{exam["id"]}.json',
              'graded_count':sum(bool(q['correct_answer']) for q in rows),
              'review_count':sum(q['needs_review'] for q in rows),
              'readable_count':sum(not q.get('source_missing') for q in rows),
              'chapter_counts':{c['id']:sum(q['chapter_id']==c['id'] for q in rows) for c in chapters}}
        # Only explicit title text supplies years; 2021–2060 are question
        # numbers in K16-3's third heading and are not an academic year.
        save(WEB/meta['question_file'],rows)
        catalog.append(meta)
        logs.append({'source_file':exam['source_file'],'exam_id':exam['id'],'question_count':len(rows),'status':'imported'})
        save(target/'import_log.json',logs)
        print('Imported',code,len(rows),'records;',meta['graded_count'],'graded',flush=True)

    aggregate=[]
    for c in chapters:
        pool=[q for q in questions if q['chapter_id']==c['id']]
        seen=set();unique=[]
        for q in pool:
            key=q['duplicate_group'] if q['duplicate_status']=='confirmed' else q['id']
            if key not in seen:unique.append(q);seen.add(key)
        aggregate.append({'chapter_id':c['id'],'chapter':c['label'],'raw_count':len(pool),'unique_count':len(unique),'excluded_duplicates':len(pool)-len(unique),'graded_count':sum(bool(q['correct_answer']) for q in unique)})
    reviews=[{'id':q['id'],**source_reference(q),'chapter':q['chapter'],'reasons':q['review_reasons'],'answer_status':q['answer_audit']['status']} for q in questions if q['needs_review']]
    report={'exam_count':len(catalog),'record_count':len(questions),'readable_count':sum(not q.get('source_missing') for q in questions),'graded_count':sum(bool(q['correct_answer']) for q in questions),'review_count':len(reviews),'excluded_exam_ids':sorted(excluded),'exams':catalog,'aggregate':aggregate,'duplicate_groups':duplicate_report,'needs_review':reviews}
    save(target/'manifest.json',{'id':'nmmmh','name':'Mật mã học','chapters':chapters,'exams':catalog,'answer_policy':'approved_verified_solutions'})
    save(target/'import_report.json',report)
    save(target/'needs_review.json',reviews)
    # Export only published exams. Preserve Excel's UTF-8 BOM and LF endings.
    with (stage/'answers.csv').open(encoding='utf-8-sig',newline='') as source_csv:
        reader=csv.DictReader(source_csv)
        fieldnames=reader.fieldnames
        answer_rows=[row for row in reader if row['de'] in included]
    assert len(answer_rows)==len(questions)
    with (target/'answers.csv').open('w',encoding='utf-8-sig',newline='') as output_csv:
        writer=csv.DictWriter(output_csv,fieldnames=fieldnames,lineterminator='\n')
        writer.writeheader()
        writer.writerows(answer_rows)
    (target/'answers.csv').chmod(0o644)
    lines=['# Báo cáo nạp môn Mật mã học','',f'{len(catalog)} đề; {len(questions)} bản ghi; {report["readable_count"]} câu có nội dung; {report["graded_count"]} câu có đáp án kiểm chứng.','', 'Đáp án tự giải/đối chiếu đã được người dùng chấp thuận để chấm. Câu chưa chốt không tính điểm. Nhãn chương con được giữ đúng file phân loại; nhãn đề xuất có cờ classification_needs_review.','', '| Mã đề nguồn | Tổng | C1 | C2 | C3 | C4 | C5 | Chưa phân loại | Có đáp án | Cần rà soát |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for e in catalog:lines.append('| '+e['source_exam_code']+' | '+ ' | '.join(str(n) for n in [e['question_count'],*[e['chapter_counts'][c['id']] for c in chapters],e['graded_count'],e['review_count']])+' |')
    lines+=['','## Gộp tất cả đề theo chương','','| Chương | Trước loại trùng | Sau loại trùng | Đã loại | Có đáp án |','|---|---:|---:|---:|---:|']
    for row in aggregate:lines.append(f'| {row["chapter"]} | {row["raw_count"]} | {row["unique_count"]} | {row["excluded_duplicates"]} | {row["graded_count"]} |')
    lines+=['','## Nhóm trùng','', 'Chỉ gộp khi nội dung và nội dung đáp án đúng cùng khớp. Hoán đổi thứ tự A–D không làm thay đổi nội dung câu. Ảnh/bảng khác nhau được giữ riêng.']
    for group in duplicate_report:lines.append('- '+group['status']+': '+', '.join(f'{r["source_exam_code"]} / câu {r["source_question_number"]}' for r in group['sources']))
    lines+=['','## Cần rà soát','']
    for row in reviews:lines.append(f'- {row["source_exam_code"]} / câu {row["source_question_number"]}: '+ '; '.join(row['reasons']))
    lines+=['','## Ba màn hình mẫu','', '- Cả đề: https://chaamsthan.github.io/ktmt-quiz/#subject=nmmmh&exam=de-thi-nmmmh&chapter=all&action=start', '- Chương trong đề: https://chaamsthan.github.io/ktmt-quiz/#subject=nmmmh&exam=de-thi-nmmmh&chapter=2&action=start', '- Chương trong tất cả đề: https://chaamsthan.github.io/ktmt-quiz/#subject=nmmmh&exam=all&chapter=2&action=start']
    if 'de-thi-k16-1' in included:
        lines+=['', 'K16-1 có 8 vị trí thiếu thân câu (10–15,22–23), cùng ba câu biến thể33-HP,34-HP,35-HP. Cả đề giữ đủ39 bản ghi và số câu nguồn, kể cả các vị trí cần bổ sung.']
    if excluded:
        lines+=['', 'Đề không xuất bản trên web: '+', '.join(sorted(excluded))+'. DOCX và bộ đáp án nguồn vẫn được giữ nguyên.']
    (target/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Total',len(questions),'records;',len(duplicate_report),'duplicate groups;',len(reviews),'review records')

if __name__=='__main__':main()
