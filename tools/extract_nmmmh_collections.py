#!/usr/bin/env python3
"""Native OOXML extraction and original scan inventory, never edit sources.

Only highlights/underlined option labels/non-default font colours provide
answer-mark evidence; ActiveX radio controls are explicitly ignored.
"""
import argparse
import copy
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

from lxml import etree as E

NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'm':'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
W='{'+NS['w']+'}'
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'subjects/nmmmh/audit/collections-2025-2026'
HEAD=re.compile(r'^\s*(?:Câu\s*)?(\d+)\s*[.)]?\s*(.*)$',re.I)
OPTION=re.compile(r'^\s*(?:\(([A-D])\)|([A-D])(?:[.)]|\s))\s*(.*)$',re.S)


def txt(node):
    return ''.join(node.xpath('.//w:t/text()|.//m:t/text()',namespaces=NS))


def paragraph(node,index,relationships,archive,exam_id):
    text=txt(node)
    tokens=[];blocks=[];mark=[];images=[]
    for run_index,run in enumerate(node.findall('w:r',NS)):
        value=txt(run)
        if run.find('w:tab',NS) is not None:value+='\t'
        if run.find('w:br',NS) is not None:value+='\n'
        pr=run.find('w:rPr',NS)
        properties={E.QName(x.tag).localname:x.get(W+'val','true') for x in pr} if pr is not None else {}
        if value:
            vertical=properties.get('vertAlign')
            display=value
            if vertical in ('superscript','subscript') and value.strip():
                display=('^{' if vertical=='superscript' else '_{')+value+'}'
            if tokens and tokens[-1].get('type')=='text':tokens[-1]['text']+=display
            else:tokens.append({'type':'text','text':display})
        if value.strip() or run.findall('.//a:blip',NS):
            if properties.get('highlight') not in (None,'none','white'):
                mark.append({'kind':'highlight','value':properties['highlight'],'text':value,'run':run_index})
            # Underlined ordinary words/formulas are not automatically keys.
            if properties.get('u') not in (None,'none') and re.fullmatch(r'\s*[A-D][.)]?\s*',value):
                mark.append({'kind':'underlined_option_label','value':properties['u'],'text':value,'run':run_index})
            if properties.get('color','auto').upper() not in ('AUTO','000000','242424','FFFFFF'):
                mark.append({'kind':'font_color','value':properties['color'],'text':value,'run':run_index})
        # w:object/w:control represents a radio button, not content or truth.
        for blip in run.findall('.//w:drawing//a:blip',NS):
            rel=blip.get('{'+NS['r']+'}embed');source=relationships.get(rel)
            if not source:raise ValueError(('Missing image relationship',rel))
            blob=archive.read(source);digest=hashlib.sha256(blob).hexdigest()
            extension=Path(source).suffix.lower()
            if extension not in ('.png','.jpg','.jpeg','.gif','.svg','.webp'):
                raise ValueError(('Unconverted inline figure',source))
            asset=f'images/nmmmh/collections/{exam_id}/{digest[:20]}{extension}'
            target=ROOT/asset;target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():assert target.read_bytes()==blob
            else:target.write_bytes(blob)
            block={'type':'image','src':asset,'alt':'Hình/công thức gốc từ DOCX'}
            tokens.append(block)
            images.append({'src':asset,'archive_path':source,'relationship':rel,'sha256':digest})
    for token in tokens:
        if token['type']=='text':
            if token['text'].strip():blocks.append(token)
        else:blocks.append(token)
    return {'index':index,'text':text,'blocks':blocks,'marks':mark,'images':images,
            'radio_controls_ignored':len(node.findall('.//w:control',NS))}


def strip_label(blocks,label):
    result=copy.deepcopy(blocks)
    for block in result:
        if block['type']=='text':
            block['text']=re.sub(r'^\s*(?:\('+label+r'\)|'+label+r'(?:[.)]|\s))\s*','',block['text'],count=1)
            break
    return result


def extract_docx(file):
    exam_id='de-cuong-2025-'+file.stem.lower()
    questions=[];current=None;target=None;intro=[];paragraphs=[]
    with ZipFile(file) as z:
        relationships={r.get('Id'):'word/'+r.get('Target').lstrip('/') for r in E.fromstring(z.read('word/_rels/document.xml.rels'))}
        body=E.fromstring(z.read('word/document.xml')).find('w:body',NS)
        for index,node in enumerate(body):
            if node.tag!=W+'p':
                if node.tag==W+'tbl':raise ValueError(('Table requires structured handler',file.name,index))
                continue
            p=paragraph(node,index,relationships,z,exam_id);paragraphs.append(p)
            text=p['text'].strip();header=HEAD.match(text)
            # Bare numerical expressions are not headings unless the source
            # actually starts a question with Câu or n. (Chuong1's format).
            is_header=header and (text.lower().startswith('câu') or re.match(r'^\d+\.',text))
            if is_header:
                number=header[1];rest=header[2]
                current={'id':f'nmmmh-{exam_id}-{number}','source_exam_id':exam_id,
                         'source_file':file.name,'source_question_number':number,
                         'source_order':len(questions),'source_docx_block':index,
                         'question_blocks':[],'source_paragraphs':[],'implicit_options':file.stem.lower()=='chuong1',
                         **{l:{'text':'','blocks':[],'source_label':l,'mark_evidence':[]} for l in 'ABCD'}}
                questions.append(current);target='question_blocks'
                for block in copy.deepcopy(p['blocks']):
                    if block['type']=='text':
                        block['text']=re.sub(r'^\s*(?:Câu\s*)?\d+\s*[.)]?\s*','',block['text'],count=1,flags=re.I)
                        if not block['text'].strip():continue
                    current['question_blocks'].append(block)
                continue
            if current is None:
                if text:intro.append(text)
                continue
            if not p['blocks']:continue
            current['source_paragraphs'].append(index)
            option=OPTION.match(text)
            if re.match(r'^[AB]\s+(?:và\s+B|nhận được|sử dụng|gửi thông tin)',text):
                option=None  # Alice/Bob in the stem, not an unpunctuated label.
            if option:
                label=option[1] or option[2];target=label
                current[label]['blocks']+=strip_label(p['blocks'],label)
                current[label]['mark_evidence']+=p['marks']
            elif current['implicit_options']:
                # Chuong1 has four unlabelled source paragraphs after the
                # numbered stem. Preserve their order as A/B/C/D, explicitly.
                label=next((l for l in 'ABCD' if not current[l]['blocks']),None)
                if label is None:raise ValueError(('Extra implicit option paragraph',file.name,current['id'],index,text))
                current[label]['blocks']+=p['blocks'];current[label]['mark_evidence']+=p['marks']
                target=label
            elif target=='question_blocks':current['question_blocks']+=p['blocks']
            else:
                current[target]['blocks']+=p['blocks'];current[target]['mark_evidence']+=p['marks']
    for q in questions:
        q['question']='\n'.join(b['text'] for b in q['question_blocks'] if b['type']=='text')
        for l in 'ABCD':q[l]['text']='\n'.join(b['text'] for b in q[l]['blocks'] if b['type']=='text')
        candidates={kind:[l for l in 'ABCD' if any(m['kind']==kind for m in q[l]['mark_evidence'])]
                    for kind in ('highlight','underlined_option_label','font_color')}
        # Retain the full raw evidence. A single conflicting mark is never
        # resolved using option position or an existing answer key.
        q['source_mark_candidates']=candidates
        strong=[set(candidates[k]) for k in ('highlight','underlined_option_label') if candidates[k]]
        weak=set(candidates['font_color'])
        union=set().union(*strong) if strong else weak
        q['source_marked_answer']=next(iter(union)) if len(union)==1 else None
        q['mark_status']='unique_source_mark' if q['source_marked_answer'] else 'needs_review'
        q['source_issues']=[]
        if not q['question'] and not q['question_blocks']:q['source_issues'].append('Thiếu thân câu trong nguồn.')
        for l in 'ABCD':
            if not q[l]['blocks']:q['source_issues'].append('Thiếu phương án '+l+' trong nguồn.')
    return {'exam_id':exam_id,'file':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
            'headings':intro,'questions':questions,'paragraphs':paragraphs,
            'radio_controls_used_as_keys':False,'question_count':len(questions)}


def pdf_inventory(file,preview):
    import pymupdf
    document=pymupdf.open(file);pages=[]
    for index,page in enumerate(document):
        images=page.get_images(full=True)
        assert len(images)==1,(file.name,index,len(images))
        blob=document.extract_image(images[0][0]);data=blob['image']
        target=preview/f'{file.stem}-source-p{index+1}.{blob["ext"]}'
        if target.exists():assert target.read_bytes()==data
        else:target.write_bytes(data)
        pages.append({'page':index+1,'path':str(target),'size':[blob['width'],blob['height']],
                      'sha256':hashlib.sha256(data).hexdigest(),'native_text':page.get_text()})
    return {'file':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'pages':pages}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--ocr',action='store_true');args=parser.parse_args()
    folder=args.source/'NMMMH/NMMMH';DEST.mkdir(parents=True,exist_ok=True)
    taxonomy_file=args.source/'TONGQUANKIENTHUC/NMMMH_Phan_loai_kien_thuc.json'
    taxonomy=json.loads(taxonomy_file.read_text())
    (DEST/'taxonomy.json').write_text(json.dumps({'source':'TONGQUANKIENTHUC/NMMMH_Phan_loai_kien_thuc.json',
        'sha256':hashlib.sha256(taxonomy_file.read_bytes()).hexdigest(),'chapters':taxonomy['chapters'],
        'topics':[{k:t[k] for k in ['code','chapter','topic','pdf_pages']} for t in taxonomy['topics']]},ensure_ascii=False,indent=2)+'\n')
    preview=args.source/'NMMMH_AUDIT_20261022/previews';preview.mkdir(parents=True,exist_ok=True)
    docs=[]
    for file in sorted((folder/'Đề_cương_2025').glob('*.docx')):
        record=extract_docx(file);docs.append(record)
        (DEST/(file.stem.lower()+'-native.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(file.name,record['question_count'],'questions;',dict(Counter(q['mark_status'] for q in record['questions'])),flush=True)
    pdfs=[pdf_inventory(f,preview) for f in sorted((folder/'Đề_giữa_kì_2026').glob('*.pdf'))]
    (DEST/'pdf_inventory.json').write_text(json.dumps(pdfs,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    review=[]
    for doc in docs:
        review+=['# '+Path(doc['file']).name,'']
        for q in doc['questions']:
            review+=['## '+q['source_question_number']+' ['+str(q['source_marked_answer'])+'] '+q['question']]
            for l in 'ABCD':review.append(l+'. '+q[l]['text'])
            figures=[b['src'] for h in [q]+[q[l] for l in 'ABCD'] for b in h.get('question_blocks',h.get('blocks',[])) if b['type']=='image']
            if figures:review.append('FIGURES: '+' '.join(figures))
            if q['mark_status']!='unique_source_mark':review.append('MARKS: '+json.dumps(q['source_mark_candidates']))
            review.append('')
    (DEST/'native_review.md').write_text('\n'.join(line.rstrip() for line in review).rstrip()+'\n',encoding='utf-8')
    if args.ocr:
        from rapidocr_onnxruntime import RapidOCR
        cache_file=DEST/'pdf_ocr.json'
        previous=json.loads(cache_file.read_text()) if cache_file.exists() else []
        cache={}
        for p in previous:
            if Path(p['path']).exists() and hashlib.sha256(Path(p['path']).read_bytes()).hexdigest()==p['sha256']:
                cache[(p['pdf'],p['page'],p['sha256'])]=p['ocr']
        engine=RapidOCR();results=[]
        for pdf in pdfs:
            for page in pdf['pages']:
                key=(pdf['file'],page['page'],page['sha256'])
                if key in cache:result=cache[key]
                else:result,_=engine(page['path'])
                record={'pdf':pdf['file'],**page,'ocr':result or []}
                results.append(record)
                print(Path(pdf['file']).name,'page',page['page'],'OCR lines',len(result or []),flush=True)
                (DEST/'pdf_ocr.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
