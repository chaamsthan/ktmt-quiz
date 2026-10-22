#!/usr/bin/env python3
"""Idempotent final migration after either source importer; --check is read-only.

Does not modify PDF/DOCX, frozen previous audits, KTMT, IDs, order or chapters.
Restoration: revert the migration commit, or restore each row from the frozen
original_questions.json and rerun the metadata refresh. Git is the full backup.
"""
import argparse
import copy
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path

from nmmmh_enrichment import display_blocks, math_display
from nmmmh_reference_decisions import AUDIT, ROOT, decisions

REVISION='reference-full-20261022-v1'
SOURCE='Bản full đã gộp.pdf'


def read(p):return json.loads(p.read_text())
def encoded(obj):return json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
def digest(obj):return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


SOURCE_DEFECTS={
 'nmmmh-de-cuong-2025-chuong2-38':'Thiếu giá trị Rcon[j] và chỉ số vòng; tài liệu cho công thức chung, không cho dữ kiện riêng câu này. Không suy Rcon từ đáp án tô màu.',
 'nmmmh-de-cuong-2025-chuong2-39':'Thiếu g(w[3]); w[0] không đủ để xác định w[4]. Cần bổ sung biểu thức/ảnh bị mất.',
 'nmmmh-de-cuong-2025-chuong3-43':'Cùng câu dùng nhóm Z*19 nhưng hỏi Z*10; cần xác nhận mô-đun, không chọn 19 chỉ vì khớp phương án.',
 'nmmmh-de-cuong-2025-tonghop1-4':'Không có chỉ số ô cần tính trong câu MixColumns; cần chỉ rõ x_ij, không tự chọn một ô.',
 'nmmmh-de-cuong-2025-tonghop1-7':'Thiếu cả khối bit đầu vào và sơ đồ vị trí abcd của IP; bảng IP chuẩn không khôi phục được dữ kiện riêng.',
 'nmmmh-de-cuong-2025-tonghop2-23':'Thiếu trạng thái C và vị trí ABCD của P(C); không lấy dữ kiện từ câu khác để ghép.',
 'nmmmh-de-cuong-2025-tonghop3-23':'Miền hoán vị ghi 6 nhưng có 7 phần tử; M=737 nhỏ hơn tổng dãy 958. Có thể tính biến đổi số học nhưng không coi đó là bộ tham số Merkle–Hellman hợp lệ. Cần xác nhận tham số muốn sửa.',
 'nmmmh-de-cuong-2025-tonghop4-8':'Chỉ có bản mã Caesar, không có bản rõ hay điều kiện xác định khóa; mọi khóa cho một bản rõ khác. Không chọn theo độ giống tiếng Anh.',
 'nmmmh-de-giua-ki-2026-ca-1-5':'Thiếu thân câu nên không biết yêu cầu ĐÚNG hay SAI. Tài liệu CFB không khôi phục được nguyên văn phần bị mất.',
 'nmmmh-de-giua-ki-2026-ca-1-9':'Thiếu tiêu chí/mô hình phần cứng để so mã dòng, DES, AES và chế độ. Không có kết luận phổ quát phù hợp mọi cách thực thi.',
 'nmmmh-de-giua-ki-2026-ca-1-34':'Hình còn đọc được nhưng phương án D bị thiếu; cần đủ phương án để xác nhận duy nhất một lựa chọn, không bịa lựa chọn D.',
 'nmmmh-de-giua-ki-2026-ca-2-30':'Đề ghi đồng thời modulo 41 và nhóm Z*97, cho hai cách hiểu khác nhau; cần xác nhận mô-đun trước khi chốt.',
}
PENDING={}  # User approved explicit reconstructed exercises for all 12 defects.


def apply_question(q, decision, reference):
    q=copy.deepcopy(q)
    original_images=list(q.get('images',[]))
    # Legacy image lists may be absent, derive from source blocks as well.
    original_images+= [b['src'] for h in [q]+[q[l] for l in 'ABCD'] for b in h.get('question_blocks',h.get('blocks',[])) if b['type']=='image']
    original_images=list(dict.fromkeys(original_images))
    q['question']=decision['question']
    if decision['typed']:
        q['question_blocks']=[{'type':'text','text':q['question']}]
        q['source_option_labels_in_figure']=False
    else:
        # Keep image/table inputs, replace only the leading/source prose.
        body=[b for b in q['question_blocks'] if b['type']!='text']
        q['question_blocks']=[{'type':'text','text':q['question']}]+body
    for l in 'ABCD':
        if decision['typed'] or decision['options'][l]!=q[l]['text']:
            q[l]['text']=decision['options'][l]
            q[l]['blocks']=[{'type':'text','text':q[l]['text']}]
        q[l]['display_blocks']=display_blocks(q[l]['blocks'])
    # Exact presentation for whole-formula options; canonical text/IDs stay
    # unchanged and are still used by the audit and shuffling/grading.
    formula_options={
        'nmmmh-de-cuong-2025-chuong3-23':[r'\frac{3(p+1)(q+1)}4',r'\frac{(p+1)(q+1)}4',r'\frac{3(p-1)(q-1)}4',r'\frac{(p-1)(q-1)}4'],
        'nmmmh-de-giua-ki-2026-ca-2-2':[r'\frac{(p+1)(q+1)}4',r'\frac{3(p-1)(q-1)}4',r'\frac{(p-1)(q-1)}4',r'\frac{3(p+1)(q+1)}4'],
        'nmmmh-de-cuong-2025-tonghop2-27':[r'\varphi(\varphi(n))','n-1',r'\varphi(n)-1',r'\varphi(n)'],
        'nmmmh-de-giua-ki-2026-ca-2-34':[r'x\equiv a^2\pmod{b+c}',r'x\equiv a\pmod{b+c}',r'x\equiv a^2\pmod{bc}',r'x\equiv a\pmod{bc}'],
    }
    for id in ['nmmmh-de-cuong-2025-chuong3-24','nmmmh-de-giua-ki-2026-ca-2-40']:
        formula_options[id]=[r'\forall r\mid\varphi(n),\ r\text{ nguyên tố}:\ \alpha^{\varphi(n)/r}\equiv1\pmod n',
            r'\mathbb Z_n^*=\{\alpha^i\bmod n:1\le i<\varphi(n)\}',r'\mathbb Z_n^*=\{\alpha^i\bmod n:0\le i<\varphi(n)\}',r'\operatorname{ord}_n(\alpha)=\varphi(\varphi(n))']
    if q['id'] in formula_options:
        for l,tex in zip('ABCD',formula_options[q['id']]):q[l]['display_blocks']=[{'type':'text','text':r'\('+tex+r'\)'}]
    # Restore the exact standard S2 table from reference PDF 94 (0-based rows).
    if q['id']=='nmmmh-de-cuong-2025-tonghop2-8':
        s2=[[15,1,8,14,6,11,3,4,9,7,2,13,12,0,5,10],
            [3,13,4,7,15,2,8,14,12,0,1,10,6,9,11,5],
            [0,14,7,11,10,4,13,1,5,8,12,6,9,3,2,15],
            [13,8,10,1,3,15,4,2,11,6,7,12,0,5,14,9]]
        q['question_blocks'].append({'type':'table','rows':[[str(v) for v in row] for row in s2]})
    q['display_blocks']=display_blocks(q['question_blocks'])
    q['images']=[b['src'] for h in [q]+[q[l] for l in 'ABCD'] for b in h.get('question_blocks',h.get('blocks',[])) if b['type']=='image']
    q['correct_answer']=decision['correct_answer'];q['needs_review']=False;q['review_reasons']=[]
    q['hint']=math_display(decision['hint'])
    explanation=decision['reason']+'\n'+'\n'.join(l+': '+decision['option_checks'][l]['reason'] for l in 'ABCD')
    explanation+=f'\nTham khảo: {SOURCE}, trang PDF '+', '.join(map(str,decision['reference_pages']))+'.'
    q.update(verification_status='verified',verification_revision=REVISION,
             answer_evidence='independent_reference_review',explanation=explanation,
             source_fidelity_status='reference_normalized_not_original_transcription')
    q['answer_audit']={'status':'verified','correct_answer':q['correct_answer'],'valid_options':[q['correct_answer']],
        'explanation':explanation,'sources':[], 'reference':{'file':SOURCE,'sha256':reference['sha256'],'pages':decision['reference_pages']},
        'option_checks':decision['option_checks'],'numeric':decision['numeric']}
    # Keep earlier independent_check as historical evidence (its input may
    # have changed), never present it as verification of the revised question.
    if 'independent_check' in q:
        q['previous_independent_check']=q.pop('independent_check')
    q['normalization']={'revision':REVISION,'reason':decision['reason'],'reference_pages':decision['reference_pages'],
        'original_snapshot':'subjects/nmmmh/audit/single-answer-review/original_questions.json',
        'original_images':original_images,'original_question':read(AUDIT/'original_questions.json')[q['id']]['question'],
        'kind':decision.get('kind','editorial_repair_or_reference_clarification_not_claimed_as_original')}
    return q


def signature(q):
    def blocks(holder):
        return holder.get('question_blocks',holder.get('blocks',[]))
    return digest([blocks(q), sorted(json.dumps(blocks(q[l]),sort_keys=True,ensure_ascii=False) for l in 'ABCD'),blocks(q[q['correct_answer']]) if q['correct_answer'] else None])


def migrate(check=False):
    frozen=read(AUDIT/'original_questions.json');reference=read(AUDIT/'reference.json');approved=decisions()
    assert set(approved).isdisjoint(PENDING) and set(approved)|set(PENDING)==set(frozen)
    manifest=read(ROOT/'subjects/nmmmh/manifest.json')
    units=[('legacy',manifest['exams'])]+[(c['id'],c['exams']) for c in manifest['collections']]
    all_rows=[];by_exam={};old_files={};seen=set()
    for collection,exams in units:
        for exam in exams:
            rows=read(ROOT/exam['question_file']);old_files[exam['question_file']]=copy.deepcopy(rows);updated=[]
            for q in rows:
                id=q['id']
                if id in frozen:
                    seen.add(id)
                    # Recompute from the frozen baseline, not from a previous
                    # output, making repeated execution exactly idempotent.
                    assert q.get('verification_revision')==REVISION or digest(q)==digest(frozen[id]),f'Stale source: {id}'
                    if id in approved:q=apply_question(frozen[id],approved[id],reference)
                    else:
                        q=copy.deepcopy(frozen[id]);q.update(correct_answer=None,needs_review=True,review_reasons=[PENDING[id]],verification_status='needs_review',verification_revision=REVISION,
                            explanation=PENDING[id],answer_evidence='insufficient_source_after_full_reference_review')
                        q['answer_audit']={'status':'needs_review','correct_answer':None,'valid_options':[],'explanation':PENDING[id],'sources':[]}
                updated.append(q)
            by_exam[exam['id']]=updated;all_rows+=updated
    assert seen==set(frozen) and len(all_rows)==540 and len({q['id'] for q in all_rows})==540
    # A changed answer/stem invalidates historical duplicate proofs. Keep old
    # proofs for unaffected groups; rebuild touched groups only by exact
    # current content including image paths and the correct option contents.
    touched={q.get('duplicate_group') for q in frozen.values() if q.get('duplicate_group')}
    for q in all_rows:
        if q.get('duplicate_group') in touched or q['id'] in frozen:
            q.update(duplicate_status='unique',duplicate_group=None,duplicate_sources=[])
    for collection,exams in units:
        grouped=defaultdict(list)
        for e in exams:
            for q in by_exam[e['id']]:
                if q['correct_answer']:grouped[signature(q)].append(q)
        for key,rows in grouped.items():
            if len(rows)<2 or not any(q['id'] in frozen for q in rows):continue
            sources=[{k:q[k] for k in ['id','source_exam_id','source_exam_code','source_question_number','source_file']} for q in rows]
            for q in rows:q.update(duplicate_status='confirmed',duplicate_group='ref-'+key[:20],duplicate_sources=sources)

    def aggregate(rows,legacy):
        out=[]
        for ch in manifest['chapters']:
            pool=[q for q in rows if ch['id'] in q['chapter_ids']];unique={q.get('duplicate_group') or q['id']:q for q in pool}
            if legacy:out.append({'chapter_id':ch['id'],'chapter':ch['label'],'raw_count':len(pool),'unique_count':len(unique),'excluded_duplicates':len(pool)-len(unique),'graded_count':sum(bool(q['correct_answer']) for q in unique.values())})
            else:out.append({'chapter_id':ch['id'],'raw':len(pool),'unique':len(unique)})
        return out

    outputs={}
    for _,exams in units:
        for e in exams:
            rows=by_exam[e['id']]
            before=old_files[e['question_file']]
            assert [(q['id'],q['source_question_number'],q['source_order']) for q in rows]==[(q['id'],q['source_question_number'],q['source_order']) for q in before]
            e['graded_count']=sum(bool(q['correct_answer']) for q in rows);e['review_count']=sum(q['needs_review'] for q in rows)
            e['images']=sum(len(q.get('images',[])) for q in rows)
            outputs[e['question_file']]=encoded(rows)
    manifest['reference_review']={'revision':REVISION,'report':'subjects/nmmmh/REFERENCE_REVIEW.md','resolved':len(approved),'reconstructed':len(SOURCE_DEFECTS),'remaining':len(PENDING)}
    outputs['subjects/nmmmh/manifest.json']=encoded(manifest)
    legacy=[q for q in all_rows if not q.get('collection_id')]
    legacy_reviews=[{'id':q['id'],'source_exam_code':q['source_exam_code'],'source_question_number':q['source_question_number'],'reasons':q['review_reasons'],'answer_status':q['answer_audit']['status']} for q in legacy if q['needs_review']]
    report=read(ROOT/'subjects/nmmmh/import_report.json')
    valid_groups={q['duplicate_group'] for q in legacy if q.get('duplicate_group')}
    report['duplicate_groups']=[g for g in report['duplicate_groups'] if g['group_id'] in valid_groups]
    known={g['group_id'] for g in report['duplicate_groups']}
    for group in sorted(valid_groups-known):
        qs=[q for q in legacy if q['duplicate_group']==group]
        report['duplicate_groups'].append({'group_id':group,'status':'confirmed','sources':qs[0]['duplicate_sources'],'criterion':'exact revised source blocks and correct option content'})
    report.update(exams=manifest['exams'],graded_count=sum(bool(q['correct_answer']) for q in legacy),review_count=len(legacy_reviews),needs_review=legacy_reviews,aggregate=aggregate(legacy,True),reference_review_revision=REVISION)
    outputs['subjects/nmmmh/import_report.json']=encoded(report);outputs['subjects/nmmmh/needs_review.json']=encoded(legacy_reviews)
    answer_rows=[{'de':q['source_exam_id'],'cau':q['source_question_number'],'dap_an':q['correct_answer'] or '',
        'cac_phuong_an_hop_le':','.join(q['answer_audit'].get('valid_options',[])),'trang_thai':q['answer_audit']['status'],'can_ra_soat':q['needs_review'],'giai_thich':q['answer_audit']['explanation']} for q in legacy]
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=list(answer_rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(answer_rows)
    outputs['subjects/nmmmh/answers.csv']='\ufeff'+stream.getvalue()
    modern=[q for q in all_rows if q.get('collection_id')];reviews=[q for q in modern if q['needs_review']]
    cp='subjects/nmmmh/audit/collections-2025-2026/'
    cr=read(ROOT/(cp+'import_report.json'))
    cr.update(graded=sum(bool(q['correct_answer']) for q in modern),ungraded=sum(not q['correct_answer'] for q in modern),needs_review=len(reviews),
              independently_verified=sum(q['verification_status']=='verified' for q in modern),source_marked_only=sum(q['verification_status']=='source_marked' for q in modern),collections=manifest['collections'],reference_review_revision=REVISION)
    cr['aggregate']=[{'collection_id':c['id'],**a} for c in manifest['collections'] for a in aggregate([q for q in modern if q['collection_id']==c['id']],False)]
    outputs[cp+'import_report.json']=encoded(cr)
    outputs[cp+'needs_review.json']=encoded([{k:q.get(k) for k in ['id','source_exam_id','source_question_number','correct_answer','source_marked_answer','source_reference','review_reasons']} for q in reviews])
    outputs['subjects/nmmmh/audit/single-answer-review/decisions.json']=encoded(approved)
    outputs['subjects/nmmmh/audit/single-answer-review/pending.json']=encoded([{'id':id,'reason':why,'correct_answer':None,'needs_review':True} for id,why in PENDING.items()])
    outputs['subjects/nmmmh/audit/single-answer-review/source_defects.json']=encoded(SOURCE_DEFECTS)
    outputs['subjects/nmmmh/audit/single-answer-review/reconstruction_authorization.json']=encoded({'user_approval':'Có, chuẩn hóa câu lỗi và giữ bản gốc','scope':'Sửa cả câu dẫn/phương án theo tài liệu để chỉ còn một đáp án đúng; dữ kiện mới ghi rõ là biên soạn lại, không giả nhận OCR phục hồi.','question_ids':list(SOURCE_DEFECTS)})
    summary={'revision':REVISION,'reference':reference,'exams':len(by_exam),'total_questions':len(all_rows),'initial_flagged':len(frozen),'resolved':len(approved),'remaining_review':len(PENDING),
             'graded':sum(bool(q['correct_answer']) for q in all_rows),'ungraded':sum(not q['correct_answer'] for q in all_rows),'reconstructed_exercises':len(SOURCE_DEFECTS),
             'verification_status_totals':dict(Counter(q['verification_status'] for q in all_rows)),
             'scope_note':'Lượt này kiểm tra lại 103 câu từng gắn cờ; không tuyên bố đã giải độc lập thêm 196 câu chỉ chấm theo dấu nguồn.',
             'answer_changes':[{'id':id,'exam':frozen[id]['source_exam_id'],'old':frozen[id]['correct_answer'],'old_source_marked':frozen[id].get('source_marked_answer'),'new':d['correct_answer'],'reason':d['reason'],'reference_pages':d['reference_pages']} for id,d in approved.items() if frozen[id]['correct_answer']!=d['correct_answer']],
             'pending':PENDING}
    outputs['subjects/nmmmh/audit/single-answer-review/report.json']=encoded(summary)
    lines=['# Đối chiếu Bản full đã gộp.pdf','',f'PDF: 205 trang; SHA-256 `{reference["sha256"]}`.',
           '',f'Giữ đủ 14 đề / 540 câu. Trong 103 câu gắn cờ ban đầu, {len(approved)} câu đã được chốt một đáp án theo câu đã chuẩn hóa; {len(PENDING)} câu còn thiếu dữ kiện, KHÔNG chấm.',
           '', 'Sửa câu dẫn/phương án được ghi riêng với bản chép gốc. Không tuyên bố các nhiễu mới là nguyên văn PDF. Các ô Hill bị che được giữ dấu ? và loại bằng cột đọc rõ. Không sửa/xóa tài liệu nguồn.',
           '',summary['scope_note'],
           '', '## Theo đề', '', '| Đề | Tổng | Có đáp án | Cần rà soát |','|---|---:|---:|---:|']
    for _,exams in units:
        for e in exams:lines.append(f'| {e["id"]} | {e["question_count"]} | {e["graded_count"]} | {e["review_count"]} |')
    lines+=['','## Thay đổi đáp án','', '| ID | Cũ | Mới | Trang PDF | Căn cứ |','|---|---|---|---|---|']
    for d in summary['answer_changes']:lines.append(f'| {d["id"]} | {d["old"] or "Chưa chốt"} | {d["new"]} | '+', '.join(map(str,d['reference_pages']))+' | '+d['reason'].replace('|','/')+' |')
    lines+=['','## Câu phải biên soạn lại vì nguồn thiếu/mâu thuẫn','', 'Người dùng đã đồng ý: “Có, chuẩn hóa câu lỗi và giữ bản gốc”. Các câu sau được cung cấp dữ kiện/tiêu chí mới rõ ràng; KHÔNG tuyên bố đã khôi phục nguyên văn đề gốc.','']
    for id,why in SOURCE_DEFECTS.items():lines.append('- '+id+': '+why+' **Đã có phiên bản biên soạn lại**, xem decisions.json.')
    lines+=['','## Còn cần rà soát đáp án phiên bản hiện tại','', 'Không còn.' if not PENDING else 'Xem pending.json.']
    for id,why in PENDING.items():lines.append('- '+id+': '+why)
    lines+=['','## Tái lập / rollback','',
            '`python tools/apply_nmmmh_reference_review.py --write` áp lại đúng cùng kết quả sau khi chạy importer; `--check` kiểm tra không ghi file.',
            'Bản trước sửa: `audit/single-answer-review/original_questions.json`; quyết định đủ A–D: `decisions.json`; danh sách chưa chốt: `pending.json`. Các hồ sơ kiểm định cũ là bằng chứng LỊCH SỬ, không thay thế quyết định mới.',
            'Rollback: revert commit migration để phục hồi đồng bộ JSON, báo cáo và frontend. Không cần xóa PDF, ảnh, lịch sử hoặc dữ liệu môn khác.',
            '', 'Lượt đang làm có chữ ký dữ liệu cũ sẽ không được tiếp tục với đáp án mới; lịch sử đã lưu được giữ nguyên như kết quả tại thời điểm làm.']
    outputs['subjects/nmmmh/REFERENCE_REVIEW.md']='\n'.join(lines)+'\n'
    for path in ['subjects/nmmmh/REPORT.md','subjects/nmmmh/COLLECTIONS_2025_2026.md']:
        current=(ROOT/path).read_text();marker='> CẬP NHẬT ĐỐI CHIẾU: '
        body=current.split('\n',2)[2] if current.startswith(marker) else current
        outputs[path]=marker+'Các số liệu dưới đây là báo cáo lần nhập gốc. Số liệu và đáp án hiện tại: [REFERENCE_REVIEW.md](REFERENCE_REVIEW.md).\n\n'+body
    changed=[]
    for path,content in outputs.items():
        target=ROOT/path
        if not target.exists() or target.read_text(encoding='utf-8')!=content:
            changed.append(path)
            if not check:target.parent.mkdir(parents=True,exist_ok=True);target.write_text(content,encoding='utf-8',newline='')
    if check and changed:raise AssertionError('Migration output stale: '+', '.join(changed))
    print(json.dumps({k:summary[k] for k in ['total_questions','initial_flagged','resolved','remaining_review','graded','ungraded']},ensure_ascii=False))
    print(('CHECK OK' if check else 'Wrote')+f': {len(changed)} files')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
    migrate(check=not args.write)
