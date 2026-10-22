#!/usr/bin/env python3
"""Read-only source inventory plus frozen before-snapshots for reference repair."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'subjects/nmmmh/audit/single-answer-review'

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    import pymupdf
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True);args=parser.parse_args()
    document=args.source/'Bản full đã gộp.pdf';pdf=pymupdf.open(document)
    out=args.source/'NMMMH_REFERENCE_REVIEW_20261022';out.mkdir(exist_ok=True)
    pages=[{'page':i+1,'text':p.get_text(),'size':list(p.rect),'images':len(p.get_images())} for i,p in enumerate(pdf)]
    save(out/'reference_pages.json',pages)
    manifest=json.loads((ROOT/'subjects/nmmmh/manifest.json').read_text())
    exams=manifest['exams']+[e for c in manifest.get('collections',[]) for e in c['exams']]
    rows=[q for e in exams for q in json.loads((ROOT/e['question_file']).read_text())]
    flagged=[q for q in rows if q.get('needs_review')]
    originals=AUDIT/'original_questions.json'
    if not originals.exists():save(originals,{q['id']:q for q in flagged})
    frozen=json.loads(originals.read_text())
    save(AUDIT/'reference.json',{'file':'Bản full đã gộp.pdf','sha256':hashlib.sha256(document.read_bytes()).hexdigest(),
                               'pdf_pages':len(pdf),'initial_review_count':len(frozen),'initial_question_count':len(rows),
                               'question_ids':list(frozen),'source_policy':'Original scans/DOCX remain immutable. Record substantive normalization separately from transcription.'})
    queue=[]
    for q in frozen.values():
        queue+=['# '+q['id'],q['question']]
        for b in q.get('question_blocks',[]):
            if b['type']=='image':queue.append('IMAGE: '+b['src'])
            elif b['type']=='table':queue.append('TABLE: '+json.dumps(b['rows'],ensure_ascii=False))
        for l in 'ABCD':queue.append(l+'. '+q[l]['text'])
        queue+=['OLD KEY: '+str(q['correct_answer']),'REASONS: '+' '.join(q.get('review_reasons',[])),
                'SOURCE: '+json.dumps(q.get('source_reference'),ensure_ascii=False),'']
    (out/'review_queue.md').write_text('\n'.join(queue)+'\n',encoding='utf-8')
    print('Reference',len(pdf),'pages; frozen',len(frozen),'flagged questions; total',len(rows))
    print(dict(Counter(q['source_exam_id'] for q in frozen.values())))
    print(out)

if __name__=='__main__':main()
