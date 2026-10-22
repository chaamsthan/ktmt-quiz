#!/usr/bin/env python3
"""Add 2025/2026 collections without rewriting any existing exam or course.

Run extractor first, then: python tools/import_nmmmh_collections.py
Rollback: remove only the two optional manifest.collections entries (or restore
the pre-import Git commit). Original documents, PDFs and old JSON stay intact.
"""
import copy
import hashlib
import json
import math
import re
from collections import Counter,defaultdict
from pathlib import Path

from nmmmh_collection_review import TOPICS,SOURCE_ISSUES,reviewed_rows
from nmmmh_midterm_review import ROWS
from nmmmh_numeric_audit import phi,order,jacobi,gf_mul,hill,ec_add,ec_mul

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'subjects/nmmmh/audit/collections-2025-2026'
LETTERS='ABCD'
NAMES={'de-cuong-2025':'Đề cương 2025','de-giua-ki-2026':'Đề giữa kì 2026'}
AES='https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.197-upd1.pdf'
DES='https://csrc.nist.gov/files/pubs/fips/46-3/final/docs/fips46-3.pdf'
HAC='https://cacr.uwaterloo.ca/hac/about/chap8.pdf'

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def display_blocks(blocks):
    result=copy.deepcopy(blocks)
    for b in result:
        if b['type']=='text':
            text=re.sub(r'\^(?!\{)([-−]?\d+|[a-zA-Z])',r'^{\1}',b['text'])
            # Preserve source run super/subscripts without exposing raw syntax.
            if re.search(r'[_^]\{[^{}]+\}',text):b.update(type='math',text=text)
            else:b['text']=re.sub(r'Z\*(\d+|n|p)\b',lambda m:r'\(\mathbb{Z}_{'+m[1]+r'}^{*}\)',text)
    return result

def annotate(q,topic,hint,chapters,collection):
    chapter_id,code,topic_name=TOPICS[topic];chapter=next(c for c in chapters if c['id']==chapter_id)
    if topic=='security':code='01.02'
    if topic=='attack':code=None  # no invented official subchapter for attack models
    if topic=='otp' and 'Vernam' in q['question']:chapter_id='1';chapter=next(c for c in chapters if c['id']=='1');code='01.08'
    taxonomy=json.loads((AUDIT/'taxonomy.json').read_text())
    official=next((t for t in taxonomy['topics'] if t['code']==code),None)
    if code:assert official and str(official['chapter'])==chapter_id
    q.update(subject_id='nmmmh',subject='Mật mã học',collection_id=collection,collection_name=NAMES[collection],
             chapter=chapter['label'],chapter_id=chapter_id,chapter_ids=[chapter_id],
             chapter_parent={'id':chapter_id,'name':chapter['name']},
             chapter_child={'code':code,'name':official['topic']} if code else None,
             study_topic=topic_name,classification_needs_review=False,
             classification_evidence='Đọc nội dung, tất cả phương án và hình; ánh xạ thủ công theo cây NMMMH_Cay_kien_thuc.md.',
             classification_notes='Cây nguồn chỉ có mục lục chương này; không tự đặt mã chương con.' if chapter['source_status']=='toc_only' else '',
             hint=format_hint(hint),verification_revision='collections-20261022-v1',
             display_blocks=display_blocks(q['question_blocks']))
    for l in LETTERS:q[l]['display_blocks']=display_blocks(q[l]['blocks'])
    q['images']=[b['src'] for h in [q]+[q[l] for l in LETTERS] for b in h.get('question_blocks',h.get('blocks',[])) if b['type']=='image']
    q['source_option_labels_in_figure']=bool(q['images'])  # conservative, never break figure label mapping


def format_hint(value):
    greek={'α':r'\alpha','β':r'\beta','φ':r'\varphi'}
    def replace(m):
        base=greek.get(m[1],m[1]);exp=m[2].strip('{}()').replace('−','-')
        return r'\('+base+'^{'+exp+r'}\)'
    return re.sub(r'([a-zA-Zαβφ])\^(\{[^{}]+\}|\([^()]+\)|[-−]?\d+|[a-zA-Z])',replace,value)


def compare_numeric(q,expected,method,computed=None):
    """Calculate first, then compare ALL options; never use the marked key as input."""
    values={l:q[l]['text'].strip() for l in LETTERS}
    valid=[l for l in LETTERS if values[l].casefold()==str(expected).casefold()]
    return {'method':method,'computed':expected if computed is None else computed,'valid_options':valid,
            'complete':True,'option_values':values}

def numbers(q):
    return {l:[int(v) for v in re.findall(r'-?\d+',q[l]['text'])] for l in LETTERS}

def numeric_docx(q,stem,n):
    # Inputs transcribed from the native question and visually checked figures.
    computed={
      ('chuong2',36):lambda:'20',
      ('chuong2',40):lambda:f'{0x6C^0x4D:02X}',
      ('chuong3',26):lambda:str(len({x*x%41 for x in range(1,41)})),
      ('chuong3',29):lambda:str(phi(119)),
      ('chuong3',30):lambda:str(jacobi(2634,889785)),
      ('chuong3',31):lambda:str(jacobi(1076,4001)),
      ('chuong3',32):lambda:str(order(3,61)),
      ('chuong3',38):lambda:str(next(x for x in range(60) if pow(31,x,61)==32)),
      ('chuong3',39):lambda:str(sum(order(a,4802)==phi(4802) for a in range(1,4802) if math.gcd(a,4802)==1)),
      ('chuong3',40):lambda:str(next(a for a in range(1,73) if order(a,73)==72)),
      ('chuong3',41):lambda:str(phi(776)),
      ('chuong3',42):lambda:str(phi(1764)),
      ('chuong3',45):lambda:''.join(str(int(math.gcd(a,3528)==1)) for a in [13,231,1021,454]),
      ('tonghop1',11):lambda:str(pow(131,pow(307,-1,36*18),37*19)),
      ('tonghop1',13):lambda:str((1+math.gcd(4,18))*(1+math.gcd(4,42))),
      ('tonghop1',22):lambda:str(pow(301,7,31*17)),
      ('tonghop1',24):lambda:str(pow(39,93,211)),
      ('tonghop1',30):lambda:str(pow(119,pow(93,-1,28*16),29*17)),
      ('tonghop1',35):lambda:str(sum(order(a,14)==phi(14) for a in range(1,14) if math.gcd(a,14)==1)),
      ('tonghop2',2):lambda:str(pow(39,43,211)),
      ('tonghop2',7):lambda:str(114**2%(41*53)),
      ('tonghop2',14):lambda:str(pow(103,-1,1013)),
      ('tonghop2',15):lambda:str(pow(354,25,9781)),
      ('tonghop2',37):lambda:str(pow(117,37,19*31)),
      ('tonghop2',38):lambda:f'{gf_mul(0x81,2):02X}',
      ('tonghop3',6):lambda:str(pow(237,1051,37*41)),
      ('tonghop3',9):lambda:'0',
      ('tonghop3',18):lambda:f'{gf_mul(0x91,2):02X}',
      ('tonghop3',25):lambda:str(phi(667)),
      ('tonghop3',27):lambda:str(85*pow(133,79,211)%211),
      ('tonghop3',28):lambda:str(order(12,37)),
    }
    key=(stem,n)
    if key in computed:return compare_numeric(q,computed[key](),'exact_integer_or_GF_arithmetic')
    vals=numbers(q)
    if key==('chuong3',27):
        expected=sorted({i*i%13 for i in range(1,13)});valid=[l for l in LETTERS if vals[l]==expected]
        return dict(method='enumerate_quadratic_residues',computed=expected,valid_options=valid,complete=True)
    if key==('chuong3',28):
        valid=[l for l in LETTERS if vals[l][0]%9==5 and vals[l][0]%7==3 and vals[l][0]%5==2]
        return dict(method='substitute_all_CRT_options',valid_options=valid,computed=122,complete=True)
    if key==('chuong3',35):
        roots=[i for i in range(437) if i*i%437==6]
        return dict(method='enumerate_all_modular_square_roots',computed=roots,valid_options=[l for l in LETTERS if sorted(vals[l])==roots],complete=True)
    if key in [('tonghop1',12),('tonghop2',6),('tonghop3',13)]:
        point=ec_add((2,4),(3,5),11,1) if stem=='tonghop1' else ec_mul(5,(5,2),11,1) if stem=='tonghop2' else ec_mul(6,(2,7),11,1)
        return dict(method='elliptic_curve_group_law',computed=point,valid_options=[l for l in LETTERS if vals[l]==list(point)],complete=True)
    if key==('tonghop2',3):
        result=[113,17,pow(17,62,113)]
        return dict(method='ElGamal_public_key',computed=result,valid_options=[l for l in LETTERS if vals[l]==result],complete=True)
    if key in [('tonghop3',19),('tonghop3',21)]:
        modulus=23 if n==19 else 41
        valid=[l for l in LETTERS if order(vals[l][0],modulus)!=phi(modulus)]
        return dict(method='test_every_candidate_multiplicative_order',computed={l:order(vals[l][0],modulus) for l in LETTERS},valid_options=valid,complete=True)
    if key==('tonghop3',5):
        orders={l:order(vals[l][0],73) for l in LETTERS}
        return dict(method='compare_all_multiplicative_orders',computed=orders,valid_options=[l for l in LETTERS if orders[l]==min(orders.values())],complete=True)
    if key in [('tonghop3',12),('tonghop4',9)]:
        pairs=[(20,13),(14,23)] if stem=='tonghop3' else [(18,0),(14,6)]
        valid=[l for l in LETTERS if len(vals[l])==2 and math.gcd(vals[l][0],26)==1 and all((vals[l][0]*x+vals[l][1])%26==y for x,y in pairs)]
        return dict(method='test_all_Affine_keys',computed={'known_pairs':pairs},valid_options=valid,complete=True)
    if key in [('tonghop3',1),('tonghop4',17)]:
        plain,seed=('UNSTOPPABLE','SIA') if stem=='tonghop3' else ('DAYLADANGMAVACHMATRAN','KEY')
        stream=(seed+plain)[:len(plain)]
        expected=''.join(chr((ord(x)+ord(y)-130)%26+65) for x,y in zip(plain,stream))
        return compare_numeric(q,expected,'plaintext_autokey_mod26')
    if key in [('tonghop4',12),('tonghop4',19),('tonghop4',22)]:
        if n==12:
            plain='PHUONGPHAPKISO';seed='KHONG';stream=(seed*4)[:len(plain)]
            expected=''.join(chr((ord(x)+ord(y)-130)%26+65) for x,y in zip(plain,stream))
        else:
            plain,a,b=('GIOITHIEUVEMATMA',5,24) if n==19 else ('HARDWORKING',math.gcd(667,1196),3*math.gcd(667,1196)%26)
            expected=''.join(chr((a*(ord(x)-65)+b)%26+65) for x in plain)
        return compare_numeric(q,expected,'classical_cipher_mod26')
    if key in [('tonghop4',13),('tonghop4',16),('tonghop3',30)]:
        matrix=[[23,18],[22,19]] if n==13 else [[9,2],[1,5]] if n==16 else None
        if n==13:return compare_numeric(q,hill('QCTO',matrix),'Hill_row_vector_decrypt')
        if n==16:return compare_numeric(q,hill('LOVE',matrix),'Hill_row_vector_encrypt')
        matrices=[[[5,8],[7,13]],[[7,19],[8,3]],[[5,8],[11,13]],[[5,8],[7,15]]]
        # Browser choices are references to image labels, not matrices themselves.
        outputs={label:hill('FRIDAY',m) for label,m in zip(LETTERS,matrices)}
        valid=[l for l in LETTERS if outputs[q[l]['text']]=='EBVZEA']
        return dict(method='test_all_Hill_matrices_in_source_image',computed=outputs,valid_options=valid,complete=True)
    if key==('tonghop2',21):
        values={l:math.gcd(*vals[l]) for l in LETTERS}
        return dict(method='compare_all_gcds',computed=values,valid_options=[l for l in LETTERS if values[l]==max(values.values())],complete=True)
    return None


SEVERE={
 'chuong3':{1,22,23,24,43},
 'tonghop1':{4,7,17,38},
 'tonghop2':{23,27},
 'tonghop3':{16,23,26},
 'tonghop4':{6,8,20,21},
}


def finish_question(q,answer,status,explanation,sources,reasons):
    q.update(correct_answer=answer,needs_review=bool(reasons or not answer),review_reasons=reasons,
             answer_evidence='source_docx_formatting' if status=='source_marked' else 'independent_calculation_or_reference' if answer else 'insufficient_or_ambiguous_source',
             verification_status=status,explanation=explanation,
             answer_audit={'status':status,'explanation':explanation,'sources':sources,'valid_options':[answer] if answer else []})


def docx_rows(record,chapters):
    stem=Path(record['file']).stem.lower();reviews=reviewed_rows(stem)
    assert len(reviews)==len(record['questions'])
    result=[]
    for index,source in enumerate(record['questions']):
        n=int(source['source_question_number']);assert n==index+1
        q=copy.deepcopy(source);topic,hint=reviews[index]
        if (stem,n)==('tonghop1',40):
            # Blank Word choices; the attached source image explicitly prints
            # all four choices. Transcribe those, retaining raw native evidence.
            for l,text in zip(LETTERS,['Phép nhân một đa thức với x','Phép nhân một đa thức với x^{2}',
                                      'Phép nhân một đa thức với x^{3}','Phép nhân một đa thức với 1']):
                q[l].update(text=text,blocks=[{'type':'text','text':text}],source_transcription='option text read from original inline image')
            q['option_transcription_notes']='Thân ảnh gốc in đủ A–D; bốn nhãn Word không kèm nội dung. Bản native không bị sửa.'
        q.update(source_exam_code=Path(record['file']).stem,source_page=None,
                 source_reference={'file':'NMMMH/NMMMH/Đề_cương_2025/'+Path(record['file']).name,'sha256':record['sha256'],'docx_block':q['source_docx_block']},
                 source_fidelity_status='native_text_and_original_images',
                 source_marked_answer=source['source_marked_answer'])
        if not q['question'].strip():q['question']='Câu hỏi theo hình gốc đính kèm.'
        reasons=q['source_issues'][:]
        issue=SOURCE_ISSUES.get(stem,{}).get(n)
        if issue:reasons.append(issue)
        answer=source['source_marked_answer']
        if not answer:reasons.append('Không có đúng một phương án được đánh dấu trong DOCX.')
        explanation=('Đáp án theo dấu định dạng khác biệt trong DOCX gốc: '+answer+'. ' if answer else '')
        explanation+='Dấu tô vàng/gạch chân nhãn được lưu đầy đủ trong hồ sơ native; không dùng trạng thái nút radio. '
        calculation=numeric_docx(q,stem,n)
        status='source_marked' if answer else 'needs_review';sources=[]
        if calculation:
            q['independent_check']=calculation
            explanation+='Kiểm tra độc lập: '+json.dumps(calculation['computed'],ensure_ascii=False)+'. '
            if calculation['valid_options']==[answer]:status='verified'
            else:
                reasons.append('Dấu đáp án nguồn không khớp tập kết quả tính độc lập '+str(calculation['valid_options'])+'; giữ dấu gốc để đối chiếu, tạm không chấm.')
                answer=None;status='needs_review'
        if n in SEVERE.get(stem,set()):answer=None;status='needs_review'
        if any(not any(b['type']=='image' or b.get('text','').strip() for b in q[l]['blocks']) for l in LETTERS):
            answer=None;status='needs_review';reasons.append('Thiếu nội dung ít nhất một phương án nguồn.')
        if reasons:explanation+='Lưu ý nguồn: '+' '.join(reasons)
        finish_question(q,answer,status,explanation,sources,reasons)
        annotate(q,topic,'Mẹo: '+hint,chapters,'de-cuong-2025')
        result.append(q)
    return result


def midterm_rows(ca,pdf,chapters):
    from PIL import Image
    exam=f'de-giua-ki-2026-ca-{ca}';result=[];crops=[]
    for source_order,r in enumerate(sorted((r for r in ROWS if r['ca']==ca),key=lambda x:x['number'])):
        n=r['number'];q={'id':f'nmmmh-{exam}-{n}','source_question_number':str(n),
            'source_exam_id':exam,'source_exam_code':f'AT2101 Ca 1' if ca==1 else 'AT2102 Ca 2',
            'source_file':Path(pdf['file']).name,'source_order':source_order,'source_page':r['pages'][0],
            'source_reference':{'file':'NMMMH/NMMMH/Đề_giữa_kì_2026/'+Path(pdf['file']).name,'sha256':pdf['sha256'],'pages':r['pages']},
            'question':r['stem'],'question_blocks':[{'type':'text','text':r['stem']}],
            'source_fidelity_status':'visually_compared_to_original_scan','source_marked_answer':None,
            'source_radio_selection_used_as_key':False}
        for l,text in zip(LETTERS,r['options']):q[l]={'text':text,'blocks':[{'type':'text','text':text}] if text else [],'source_label':l}
        boxes=[r['crop']] if r['crop'] else []
        if (ca,n)==(2,17):boxes.append((15,512,166,1319,225))  # last PC-1 row continued in source
        if (ca,n)==(2,28):boxes=[(22,512,233,1319,678)]  # table only; full stem transcribed above
        for part,box in enumerate(boxes):
            page,x0,y0,x1,y1=box;page_meta=pdf['pages'][page-1]
            original=Image.open(page_meta['path']);assert 0<=x0<x1<=original.width and 0<=y0<y1<=original.height
            path=f'images/nmmmh/collections/{exam}/q{n:02d}-p{page:02d}-stem.png'
            target=ROOT/path;target.parent.mkdir(parents=True,exist_ok=True)
            original.crop((x0,y0,x1,y1)).save(target)
            q['question_blocks'].append({'type':'image','src':path,'alt':f'Hình gốc câu {n}, ca {ca}, trang {page}'})
            crops.append({'question_id':q['id'],'path':path,'sha256':sha(target),'source_sha256':page_meta['sha256'],'source_page':page,'source_box_pixels':[x0,y0,x1,y1],
                          'source_size':page_meta['size'],'resized':False,'visual_review':'pending_final_contact_sheet'})
        reasons=[r['issue']] if r['issue'] else []
        answer=r['key'];proof=r['proof'] or r['issue']
        calculation=numeric_midterm(q,ca,n)
        if calculation:
            q['independent_check']=calculation
            candidates=calculation['valid_options'];answer=candidates[0] if len(candidates)==1 else None
            proof='Kết quả tính độc lập: '+json.dumps(calculation['computed'],ensure_ascii=False)+'. Các phương án khớp: '+str(candidates)+'.'
            if not answer:reasons.append('Không có đúng một phương án khớp phép tính; không sửa số liệu hay phương án nguồn để ép đáp án.')
        status='verified' if answer else 'needs_review'
        sources=[AES] if r['topic'] in {'gf','aes','aesround','aeskey','mix','shift'} else [DES] if r['topic'].startswith('des') else [f'https://cacr.uwaterloo.ca/hac/about/chap{1 if r["topic"] in {"security","symmetric","attack","hybrid","public"} else 2 if r["topic"]=="math" else 6 if r["topic"] in {"rc4","ksa"} else 7 if r["topic"] in {"shannon","classic","hill","vigenere","autokey","triple","block"} else 8}.pdf']
        finish_question(q,answer,status,proof,sources,reasons)
        # Use a question-specific shortcut from the reviewed source bank where
        # the concept is identical, not the final answer/proof text.
        specific=MIDTERM_HINTS[(ca,n)]
        annotate(q,r['topic'],'Mẹo: '+specific,chapters,'de-giua-ki-2026')
        result.append(q)
    return result,crops


def numeric_midterm(q,ca,n):
    # The scan radio state and review draft keys are not inputs to this solver.
    expected={
      (1,1):lambda:str(order(3,59)),(1,6):lambda:f'({(215+1+227)%256},1)',
      (1,10):lambda:f'{gf_mul(0xA4,2):02X}',(1,11):lambda:hill('DKAD',[[13,10],[20,23]]),
      (1,13):lambda:f'{0:04b}',(1,15):lambda:'4F, B2',
      (1,27):lambda:f'{gf_mul(0x53,0x2A):02X}',(1,30):lambda:'0',
      (1,33):lambda:f'{gf_mul(3,0x0B)^0xFE^0x20^gf_mul(2,0x87):02X}',
      (1,37):lambda:str(pow(116,76,211)),
      (2,1):lambda:f'{gf_mul(0x60,8):02X}',(2,3):lambda:f'{gf_mul(0xD3,2):02X}',
      (2,11):lambda:''.join(chr((ord(a)+ord(b)-130)%26+65) for a,b in zip('ENGLISH','NOWNOWN')),
      (2,15):lambda:str(4*(192//32+6+1))+' từ',
      (2,16):lambda:str(order(7,59)),
      (2,17):lambda:''.join('0000101011101001100101101100110111100010000011110100101110110011'[i-1] for i in [57,49,41,33]),
      (2,19):lambda:'A3, FE',
      (2,23):lambda:str(sum(pow(x,19,37*53)==x for x in range(37*53))),
      (2,26):lambda:f'{0x0B^gf_mul(2,0xFE)^gf_mul(3,0x20)^0x87:02X}',
      (2,33):lambda:f'({(233+1+108)%256},1)',
      (2,38):lambda:'01000110',
      (2,39):lambda:str(next(a for a in range(1,97) if order(a,97)==96)),
    }
    if (ca,n) in expected:return compare_numeric(q,expected[(ca,n)](),'source_transcribed_arithmetic; no_selected_radio_input')
    if (ca,n)==(2,36):
        outputs={}
        for l in LETTERS:
            v=[ord(c)-65 for c in q[l]['text']];outputs[l]=hill('MILK',[v[:2],v[2:]])
        return dict(method='test_all_Hill_key_options',computed=outputs,valid_options=[l for l in LETTERS if outputs[l]=='AMVU'],complete=True)
    if (ca,n) in {(1,38),(2,24)}:
        seqs=numbers(q);checks={l:all(x>sum(seqs[l][:i]) for i,x in enumerate(seqs[l])) for l in LETTERS}
        return dict(method='strict_superincreasing_check_all_options',computed=checks,valid_options=[l for l in LETTERS if checks[l]],complete=True)
    return None


MIDTERM_HINTS={
 (1,1):'Bậc phải chia 58; thử các ước tăng dần bằng lũy thừa modulo 59.',
 (1,2):'So các số mũ của đa thức trong hình với đa thức AES chuẩn; đừng đổi vị trí các nhãn trên giao diện.',
 (1,3):'Phân tích 100 ra thừa số nguyên tố, kiểm tra lũy thừa 100/r không được dư 1 với từng r.',
 (1,4):'Phân biệt hai mục tiêu Shannon với các công cụ thay thế và hoán vị dùng để đạt chúng.',
 (1,5):'Nguồn thiếu thân câu; chưa thể biết phải chọn khẳng định đúng hay sai. Không suy từ nút đã tích.',
 (1,6):'Mang j từ i=0 sang i=1, tính j modulo 256 rồi mới swap; dùng T0=215,T1=227 đúng thứ tự.',
 (1,7):'Xác định đối thủ có bản rõ, cặp tương ứng hay chỉ các thông điệp đã mã hóa; không tự thêm quyền chọn dữ kiện.',
 (1,8):'Chỉ XOR tám bit cuối của hai chuỗi; cần đọc chắc từng bit trước khi so phương án.',
 (1,9):'Cần tiêu chí phần cứng cụ thể để so các thuật toán; đây không phải kết luận đúng cho mọi cách triển khai.',
 (1,10):'A4 có bit cao 1: dịch trái một bit rồi XOR phần rút gọn AES, giữ lại một byte.',
 (1,11):'Nguồn cho sẵn k nghịch đảo; thử mã hóa ngược các bản rõ ứng viên hoặc nhân DK,AD với ma trận giải.',
 (1,12):'Đối chiếu miền số mũ chuẩn 1…p−2 rồi kiểm tra cả khoảng, kể cả các khoảng con.',
 (1,13):'Hai bit ngoài của 100101 chọn hàng, bốn bit trong chọn cột; phải tra đúng hộp S4.',
 (1,14):'So mô hình khóa dùng chung với mô hình hai khóa công khai/riêng; chú ý câu hỏi yêu cầu SAI.',
 (1,15):'Dịch trái hàng r đúng r byte, chỉ đọc hai ô x13 và x32 sau khi dịch.',
 (1,16):'Đảo công thức một vòng Feistel để kiểm tra cấu trúc giải mã; xét riêng thứ tự khóa con.',
 (1,17):'Phân biệt cấp nhóm, cấp phần tử và φ của cấp; cần đọc đúng số mũ rất nhỏ trong hình.',
 (1,18):'Viết công thức CBC cho hai vị trí; cùng khối rõ không đủ nếu khối bản mã trước khác nhau.',
 (1,19):'Khóa vòng XOR với R sau mở rộng, không XOR trực tiếp nửa dữ liệu 32 bit; so độ dài để loại.',
 (1,20):'Tính nhân của φ cần hai thừa số nguyên tố cùng nhau; không đòi hỏi chúng đều là số nguyên tố.',
 (1,24):'Điểm vô cực đóng vai trò như số 0 của phép cộng nhóm; thử cộng nó với một điểm hữu hạn.',
 (1,25):'Đừng suy độ dài khóa Rijndael từ kích thước bộ nhớ; phân biệt giới hạn khóa và độ dài khối.',
 (1,26):'Đổi khoảng khóa từ bit ra byte rồi phân biệt với 256 phần tử của mảng trạng thái RC4.',
 (1,27):'2A ở nhị phân chọn các lũy thừa cần XOR; dùng xtime liên tiếp cho 53 rồi ghép các phần được chọn.',
 (1,28):'Đếm độ dài đầu ra trước khi tính phản hồi: đề yêu cầu a8…a0 nhưng phương án có thêm bit.',
 (1,29):'An toàn tính toán dựa vào giả thiết bài toán khó khác với an toàn vô điều kiện.',
 (1,30):'Kiểm tra dạng modulo có nhóm nhân cyclic trước khi áp công thức φ(φ(n)).',
 (1,31):'Từ y1=α^k và β=α^a, tìm nghịch đảo của thừa số nhân với x trong y2.',
 (1,32):'Kiểm tra cả dạng Fermat tổng quát lẫn trường hợp con; một phương án đúng không đảm bảo chỉ có một.',
 (1,33):'Chỉ nhân hàng hệ số thứ ba với cột thứ hai (chỉ số từ 0); phép cộng là XOR.',
 (1,34):'Đọc chỉ số bảng IP tại từng ô abcd rồi lấy bit nguồn 1-based; cần đủ bốn phương án trước khi chấm.',
 (1,35):'Phân biệt giới hạn độ dài khóa Rijndael với khối DES và độ rộng thanh ghi máy tính.',
 (1,36):'Phân biệt phân tích số nguyên với kiểm tra hay tìm số nguyên tố; không coi chúng là cùng một bài toán.',
 (1,37):'Thành phần y1 chỉ phụ thuộc α,k,p; bỏ qua a,x để giảm phép tính.',
 (1,38):'Cộng dồn từ trái qua phải; mỗi phần tử mới phải lớn hơn nghiêm ngặt toàn tổng phía trước.',
 (1,39):'Đếm khóa DES độc lập trong cấu hình EDE, không đếm số bit hay số vòng DES bên trong.',
 (1,40):'Xác định đang hỏi khối dữ liệu, không phải khóa hữu ích hoặc số bit sau mở rộng E.',
 (2,1):'Nhân 08 tương đương áp xtime ba lần cho 60 ở hệ hex; rút gọn sau mỗi lần dịch.',
 (2,2):'Đếm bình phương khác 0 theo từng modulo nguyên tố lẻ rồi dùng CRT; chú ý điều kiện p,q lẻ.',
 (2,3):'D3 có bit cao 1; sau dịch trái phải rút gọn theo đa thức AES, không chỉ bỏ bit tràn.',
 (2,4):'Xét mỗi vòng biến đổi bao nhiêu phần của khối; đừng suy rằng dùng chung cấu trúc giải mã là yếu.',
 (2,5):'Bảng IP chuẩn phủ toàn bộ bit của một khối DES; không nhầm với bảng PC-1 của khóa.',
 (2,6):'Viết phụ thuộc đầu vào giữa các khối; kiểm tra cả đáp án liệt kê nhiều chế độ lẫn đáp án chỉ liệt kê một.',
 (2,7):'Đếm số bit phương án và số ô thanh ghi trước; nguồn đang lệch độ dài, không tự bỏ một bit.',
 (2,8):'Vét cạn thử toàn bộ không gian khóa; xét số lượng khóa hơn là sự tồn tại một vài khóa yếu.',
 (2,9):'Đổi 256 bit ra Nk từ 32 bit, rồi dùng liên hệ Nr=Nk+6.',
 (2,10):'Kiểm tra cả hai đầu mỗi khoảng có nằm trong miền số mũ 1…p−2 hay không.',
 (2,11):'Lặp NOW dưới ENGLISH, cộng modulo 26 với A=0; thử chỗ phương án khác nhau trước.',
 (2,12):'Xét riêng phát biểu dùng cặp khóa và phát biểu tương đồng mã dòng; nguồn cần làm rõ tiêu chí.',
 (2,13):'Dữ liệu lớn cần mã đối xứng nhanh; xác định phần việc nhỏ nào nên giao cho hệ công khai.',
 (2,14):'Mã hóa đơn thuần che nội dung; không tự bổ sung bảo đảm khả dụng hoặc chống chối bỏ.',
 (2,15):'Tính 4×(Nr+1), kể cả khóa vòng khởi tạo; không chỉ đếm các vòng biến đổi.',
 (2,16):'Bậc phải chia 58; thử các ước tăng dần và chọn số mũ dương nhỏ nhất cho dư 1.',
 (2,17):'Bốn vị trí đầu PC-1 là 57,49,41,33; lấy đúng bit từ chuỗi khóa, đếm từ 1.',
 (2,18):'Chia 48 bit sau mở rộng E thành các nhóm đầu vào S-box, không lấy số vòng làm số hộp.',
 (2,19):'Dịch hàng 1 và 2 sang trái tương ứng 1 và 2 byte; đọc đúng cặp x10,x21.',
 (2,20):'Mỗi đồ vật có hai lựa chọn lấy/không; đếm toàn bộ tập con thay vì số hoán vị.',
 (2,21):'Tách toàn vẹn/xác thực/bí mật khỏi việc duy trì dịch vụ sẵn sàng và kịp thời.',
 (2,22):'Phân biệt khóa dùng chung với hai khóa riêng độc lập; xem bước thỏa thuận trước.',
 (2,23):'Dùng (1+gcd(e−1,p−1))(1+gcd(e−1,q−1)); không cần mã hóa thử mọi thông điệp.',
 (2,24):'Kiểm tra điều kiện siêu tăng và so các phương án trùng chữ; không phân biệt hai dãy giống nhau bằng vị trí.',
 (2,25):'S-box tạo tính phi tuyến; kiểm tra dấu phủ định ở câu hỏi trước khi chọn nhãn trong ảnh.',
 (2,26):'Chỉ lấy hàng hệ số 1 và cột trạng thái 2 theo chỉ số từ 0; nhân trong GF(2^8), cộng bằng XOR.',
 (2,27):'Các thành viên họ RC có thể thuộc loại khác nhau; kiểm tra từng tên trong cặp thay vì suy từ tiền tố RC.',
 (2,28):'Đọc chỉ số B và S-box được yêu cầu; nguồn đang ghi B5 ở đầu nhưng B3 ở cuối, chưa được tự chọn một cách hiểu.',
 (2,29):'Điều kiện của e dùng φ(n), còn mã/giải dùng n; thử phản ví dụ cho điều kiện gcd(e,n).',
 (2,30):'Nguồn ghi đồng thời modulo 41 và nhóm modulo 97; cần thống nhất trước khi áp công thức đếm.',
 (2,31):'Nhân c với W nghịch đảo modulo M, tham lam trên dãy siêu tăng rồi đảo hoán vị; có thể thử mã hóa ngược đáp án.',
 (2,32):'Phân biệt khối Rijndael với khối DES; khả năng cài trên thẻ không quyết định kích thước khối.',
 (2,33):'Mang j của vòng i=0 sang i=1, cộng S[1] và T[1] rồi lấy dư 256 trước khi swap.',
 (2,34):'Hai đồng dư cùng số dư ghép được theo modulo tích khi gcd(b,c)=1; nguồn thiếu các lựa chọn cuối.',
 (2,35):'Không cần giải mã khối trước khác với không cần bản mã trước; kiểm tra CBC và CFB theo sự phân biệt này.',
 (2,36):'Đổi bốn chữ khóa thành ma trận 2×2, thử riêng cặp MI trước với vector hàng và A=0.',
 (2,37):'Phân biệt lặp từ khóa với nối bản rõ sau mầm khóa; giữ ánh xạ nhãn trong hình và lựa chọn giao diện.',
 (2,38):'Ở vòng tiếp theo, nửa trái bằng nửa phải trước đó; không cần tính hàm f để tìm L3.',
 (2,39):'Phân tích 96 và thử x^(96/r) với mỗi thừa số nguyên tố r; kiểm tra lần lượt từ x nhỏ nhất.',
 (2,40):'Một tập không đổi khi thêm lại phần tử α^φ(n)=1; hai khoảng số mũ trong hình có thể cùng đúng.',
}


def deduplicate(rows):
    groups=defaultdict(list)
    for q in rows:
        if not q['correct_answer']:continue
        def content(h):
            blocks=h.get('question_blocks',h.get('blocks',[]))
            return [(b['type'],sha(ROOT/b['src']) if b['type']=='image' else re.sub(r'\s+',' ',b.get('text','')).strip()) for b in blocks]
        choices=[content(q[l]) for l in LETTERS]
        fingerprint=json.dumps([content(q),sorted(choices,key=str),content(q[q['correct_answer']])],sort_keys=True,ensure_ascii=False)
        groups[hashlib.sha256(fingerprint.encode()).hexdigest()].append(q)
    duplicate_groups=[]
    for key,qs in groups.items():
        if len(qs)<2:continue
        sources=[{k:q[k] for k in ['id','source_exam_id','source_exam_code','source_question_number','source_file']} for q in qs]
        for q in qs:q.update(duplicate_status='confirmed',duplicate_group='collection-'+key[:20],duplicate_sources=sources)
        duplicate_groups.append({'id':'collection-'+key[:20],'sources':sources,'criterion':'exact normalized content, same image bytes, same correct option content'})
    for q in rows:
        q.setdefault('duplicate_status','unique');q.setdefault('duplicate_group',None);q.setdefault('duplicate_sources',[])
    return duplicate_groups


def exam_meta(exam,rows,title,file,collection):
    return {'id':exam,'source_file':file,'title':title,'source_headings':[title],
            'source_exam_code':rows[0]['source_exam_code'],'subject':'Mật mã học','year':2025 if collection=='de-cuong-2025' else 2026,
            'year_evidence':'Tên thư mục do người dùng cung cấp; không suy từ ảnh chụp.','attempt':None,
            'collection_id':collection,'question_file':f'subjects/nmmmh/exams/{exam}.json','question_count':len(rows),
            'graded_count':sum(bool(q['correct_answer']) for q in rows),'review_count':sum(q['needs_review'] for q in rows),
            'readable_count':sum(not q.get('source_missing') for q in rows),'images':sum(len(q['images']) for q in rows),
            'chapter_counts':dict(Counter(c for q in rows for c in q['chapter_ids']))}


def main():
    manifest_path=ROOT/'subjects/nmmmh/manifest.json';manifest=json.loads(manifest_path.read_text());chapters=manifest['chapters']
    baseline={e['question_file']:sha(ROOT/e['question_file']) for e in manifest['exams']}
    baseline.update({p:sha(ROOT/p) for p in ['questions.json','exam_sets.json']})
    collections=[];all_rows=[];crops=[];imports=[]
    collection='de-cuong-2025';rows=[];exams=[]
    for stem in ['chuong1','chuong2','chuong3','tonghop1','tonghop2','tonghop3','tonghop4']:
        record=json.loads((AUDIT/(stem+'-native.json')).read_text())
        questions=docx_rows(record,chapters)
        title=('Chương '+stem[-1] if stem.startswith('chuong') else 'Tổng hợp '+stem[-1])+' · Đề cương 2025'
        meta=exam_meta(record['exam_id'],questions,title,Path(record['file']).name,collection)
        # Write/log each source as a separate import unit, before moving on.
        save(ROOT/meta['question_file'],questions);rows+=questions;exams.append(meta)
        imports.append({'exam':meta['id'],'questions':len(questions),'source_sha256':record['sha256'],'status':'written'})
        save(AUDIT/'import_log.json',imports)
    duplicates=deduplicate(rows)
    for e in exams:save(ROOT/e['question_file'],[q for q in rows if q['source_exam_id']==e['id']])
    collections.append(dict(id=collection,name=NAMES[collection],exams=exams,
        description='Đáp án lấy từ phần tô vàng/gạch chân khác biệt trong DOCX gốc. Dấu nguồn được giữ riêng với kết quả kiểm chứng; câu mâu thuẫn hoặc nhiều đáp án không tính điểm.',
        report='subjects/nmmmh/COLLECTIONS_2025_2026.md'))
    all_rows+=rows
    pdfs=json.loads((AUDIT/'pdf_inventory.json').read_text());collection='de-giua-ki-2026';rows=[];exams=[]
    for ca,pdf in enumerate(pdfs,1):
        questions,assets=midterm_rows(ca,pdf,chapters);crops+=assets
        title=f'Kiểm tra giữa kì {"AT2101" if ca==1 else "AT2102"} · Ca {ca} · 2026'
        meta=exam_meta(f'de-giua-ki-2026-ca-{ca}',questions,title,Path(pdf['file']).name,collection)
        if ca==1:meta['missing_source_question_numbers']=[21,22,23]
        save(ROOT/meta['question_file'],questions);rows+=questions;exams.append(meta)
        imports.append({'exam':meta['id'],'questions':len(questions),'source_sha256':pdf['sha256'],'status':'written','missing_numbers':meta.get('missing_source_question_numbers',[])})
        save(AUDIT/'import_log.json',imports)
    duplicates+=deduplicate(rows)
    for e in exams:save(ROOT/e['question_file'],[q for q in rows if q['source_exam_id']==e['id']])
    collections.append(dict(id=collection,name=NAMES[collection],exams=exams,
        description='Hai PDF ảnh chụp bài làm. Không lấy nút đã tích làm đáp án chuẩn. Ca 1 thiếu câu 21–23 trong nguồn; câu bị cắt hoặc lỗi đề vẫn giữ số gốc và không tính điểm khi chưa chốt.',
        report='subjects/nmmmh/COLLECTIONS_2025_2026.md'))
    all_rows+=rows
    assert len(all_rows)==367 and len({q['id'] for q in all_rows})==367
    manifest['collections']=collections;save(manifest_path,manifest)
    assert all(sha(ROOT/p)==digest for p,digest in baseline.items()),'Unrelated/old data changed'
    save(AUDIT/'preserved_legacy_sha256.json',baseline)
    reviews_path=AUDIT/'crop_visual_review.json'
    visual=json.loads(reviews_path.read_text()) if reviews_path.exists() else {}
    for c in crops:
        if visual.get(c['path'],{}).get('sha256')==c['sha256']:c['visual_review']=visual[c['path']]['review']
    save(AUDIT/'crop_manifest.json',crops)
    reviews=[{k:q[k] for k in ['id','source_exam_id','source_question_number','correct_answer','source_marked_answer','source_reference','review_reasons']} for q in all_rows if q['needs_review']]
    save(AUDIT/'needs_review.json',reviews)
    save(AUDIT/'duplicate_groups.json',duplicates)
    aggregate=[]
    for collection in collections:
        qs=[q for q in all_rows if q['collection_id']==collection['id']]
        for chapter in chapters:
            pool=[q for q in qs if chapter['id'] in q['chapter_ids']]
            unique={q['duplicate_group'] or q['id'] for q in pool}
            aggregate.append({'collection_id':collection['id'],'chapter_id':chapter['id'],'raw':len(pool),'unique':len(unique)})
    report={'source_files':9,'new_exams':9,'new_questions':len(all_rows),'native_docx_questions':290,'pdf_questions':77,
            'unique_source_marks':sum(q.get('source_marked_answer') is not None for q in all_rows),
            'graded':sum(bool(q['correct_answer']) for q in all_rows),'independently_verified':sum(q['verification_status']=='verified' for q in all_rows),
            'source_marked_only':sum(q['verification_status']=='source_marked' for q in all_rows),
            'ungraded':sum(not q['correct_answer'] for q in all_rows),
            'needs_review':len(reviews),'pdf_source_pages_reviewed':46,'original_docx_image_occurrences':80,'new_crops':len(crops),
            'missing_source_questions':{'de-giua-ki-2026-ca-1':[21,22,23]},'collections':collections,'aggregate':aggregate}
    save(AUDIT/'import_report.json',report)
    lines=['# Đề cương 2025 và Đề giữa kì 2026','',
           'Nguồn: 7 DOCX đọc trực tiếp OOXML; 2 PDF scan (46 trang) OCR cục bộ rồi đối chiếu ảnh. Không dùng API key, base64 hoặc trạng thái radio làm khóa đáp án. Không sửa tài liệu gốc.',
           '',f'Thêm **9 đề, {len(all_rows)} câu**. 290 câu DOCX; 77 câu xuất hiện trong PDF. Ca 1 không có câu 21–23 trong nguồn; không tạo câu bịa để bù.',
           '',f'289 câu có đúng một dấu đáp án nguồn. {report["independently_verified"]} câu được kiểm chứng độc lập; {report["source_marked_only"]} câu đang chấm theo dấu gốc, KHÔNG gắn nhãn đã giải độc lập. {report["ungraded"]} câu chưa chấm; {report["needs_review"]} câu cần rà soát nguồn (gồm cả câu có khóa nguồn rõ nhưng thiếu tiêu chí/ngữ cảnh).',
           '', 'Câu nguồn mâu thuẫn, nhiều đáp án hoặc không có phương án khớp: lưu dấu nguồn để đối chiếu, để correct_answer=null; không tự đoán hay đổi âm thầm sang đáp án khác.',
           '', '## Số câu từng đề', '', '| Nhóm | Đề | Câu | Có đáp án | Rà soát | Chương: số câu |','|---|---|---:|---:|---:|---|']
    for c in collections:
        for e in c['exams']:lines.append(f'| {c["name"]} | {e["title"]} | {e["question_count"]} | {e["graded_count"]} | {e["review_count"]} | '+', '.join(f'{k}: {v}' for k,v in e['chapter_counts'].items())+' |')
    lines+=['','## Gộp theo chương','', '| Nhóm | Chương | Toàn bộ | Sau loại trùng đã xác nhận |','|---|---|---:|---:|']
    for a in aggregate:
        if a['raw']:lines.append(f'| {NAMES[a["collection_id"]]} | {a["chapter_id"]} | {a["raw"]} | {a["unique"]} |')
    lines+=['','## Dấu đáp án nguồn không khớp phép tính độc lập','',
            '| ID | Dấu nguồn giữ lại | Đáp án chấm | Kết quả độc lập | Phương án khớp |',
            '|---|---|---|---|---|']
    for q in all_rows:
        check=q.get('independent_check')
        if q['collection_id']=='de-cuong-2025' and check and check['valid_options']!=[q['source_marked_answer']]:
            lines.append(f'| {q["id"]} | {q["source_marked_answer"]} | Không chấm | '+json.dumps(check['computed'],ensure_ascii=False).replace('|','/')+' | '+str(check['valid_options'])+' |')
    lines+=['','## Câu trùng đã xác nhận','',
            'Chỉ gộp khi nội dung, ảnh gốc và nội dung đáp án đúng trùng; không gộp câu chỉ gần giống. Mọi bản ghi vẫn giữ trong đề nguồn.','']
    for group in duplicates:lines.append('- '+group['id']+': '+', '.join(s['id'] for s in group['sources']))
    lines+=['','## Cần rà soát','', '| ID câu | Dấu đáp án nguồn | Trạng thái | Lý do |','|---|---|---|---|']
    for q in reviews:lines.append(f'| {q["id"]} | {q["source_marked_answer"] or "—"} | {"Có khóa nguồn, cần xem ngữ cảnh" if q["correct_answer"] else "Không chấm"} | '+ ' '.join(q['review_reasons']).replace('|','/')+' |')
    lines+=['','## Đường dẫn', '', '- [Đề cương 2025](../../#subject=nmmmh&collection=de-cuong-2025)',
            '- [Đề giữa kì 2026](../../#subject=nmmmh&collection=de-giua-ki-2026)',
            '- [Làm cả ca 2](../../#subject=nmmmh&collection=de-giua-ki-2026&exam=de-giua-ki-2026-ca-2&chapter=all&action=start)',
            '- [Chương trong ca 2](../../#subject=nmmmh&collection=de-giua-ki-2026&exam=de-giua-ki-2026-ca-2&chapter=2&action=start)',
            '- [Chương gộp hai ca giữa kì](../../#subject=nmmmh&collection=de-giua-ki-2026&exam=all&chapter=2&action=start)',
            '- [Cả đề tổng hợp 1 năm 2025](../../#subject=nmmmh&collection=de-cuong-2025&exam=de-cuong-2025-tonghop1&chapter=all&action=start)',
            '- [Chương trong tổng hợp 1 năm 2025](../../#subject=nmmmh&collection=de-cuong-2025&exam=de-cuong-2025-tonghop1&chapter=2&action=start)',
            '- [Chương gộp toàn đề cương 2025](../../#subject=nmmmh&collection=de-cuong-2025&exam=all&chapter=2&action=start)',
            '', '## Kiểm tra và rollback','',
            'Importer chỉ thêm collections và chín file đề mới; SHA-256 các file đề cũ và KTMT được kiểm tra không đổi. Chạy tools/test_nmmmh_collections.py để kiểm thử dữ liệu, nguồn, crop và giao diện. Phục hồi bằng Git commit trước migration hoặc bỏ hai mục collections trong manifest; không cần sửa dữ liệu gốc hay localStorage.',
            '', 'Hồ sơ chi tiết: audit/collections-2025-2026/{import_report,needs_review,crop_manifest,duplicate_groups,import_log}.json. Câu trùng vẫn nằm trong từng đề; chỉ chế độ gộp theo chương loại bản sao có nội dung và đáp án giống hệt đã xác nhận.']
    report_text=('\n'.join(lines)+'\n').replace('(../../#subject=', '(https://chaamsthan.github.io/ktmt-quiz/#subject=')
    (ROOT/'subjects/nmmmh/COLLECTIONS_2025_2026.md').write_text(report_text,encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in {'collections','aggregate'}},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
    from apply_nmmmh_reference_review import migrate
    migrate()
