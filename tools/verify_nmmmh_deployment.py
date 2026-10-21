#!/usr/bin/env python3
"""Read-only SHA-256 comparison of deployed quiz data/code/images with local."""
import argparse
import hashlib
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='https://chaamsthan.github.io/ktmt-quiz/')
    args=parser.parse_args();base=args.url.rstrip('/')+'/'
    files={'index.html','app.js','nmmmh.js','nmmmh-practice.js','styles.css','questions.json','exam_sets.json',
           'subjects/nmmmh/manifest.json','subjects/nmmmh/import_report.json','subjects/nmmmh/needs_review.json',
           'subjects/nmmmh/answers.csv','vendor/katex/katex.min.js','vendor/katex/katex.min.css','vendor/katex/contrib/auto-render.min.js'}
    manifest=json.loads((ROOT/'subjects/nmmmh/manifest.json').read_text())
    rows=json.loads((ROOT/'questions.json').read_text())
    for exam in manifest['exams']:
        files.add(exam['question_file']);rows.extend(json.loads((ROOT/exam['question_file']).read_text()))
    for q in rows:
        if q.get('question_image'):files.add(q['question_image'])
        for holder in [q]+[q.get(l,{}) for l in 'ABCD']:
            if holder.get('image'):files.add(holder['image'])
            for b in holder.get('question_blocks',holder.get('blocks',[])):
                if b['type']=='image':files.add(b['src'])
    stamp=str(int(time.time()))
    def compare(file):
        try:
            request=urllib.request.Request(base+file+'?audit_verify='+stamp,headers={'Cache-Control':'no-cache'})
            with urllib.request.urlopen(request,timeout=30) as response:data=response.read()
            expected=hashlib.sha256((ROOT/file).read_bytes()).hexdigest()
            actual=hashlib.sha256(data).hexdigest()
            return None if expected==actual else {'file':file,'error':'content_hash_mismatch'}
        except Exception as exc:return {'file':file,'error':str(exc)}
    with ThreadPoolExecutor(max_workers=6) as executor:
        failures=[r for r in executor.map(compare,sorted(files)) if r]
    result={'url':base,'assets_compared':len(files),'all_sha256_match':not failures,'failures':failures}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
