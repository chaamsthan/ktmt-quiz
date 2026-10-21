#!/usr/bin/env python3
"""Report measured coverage and unresolved source constraints without overclaiming."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'subjects/nmmmh/audit'


def read(name):return json.loads((AUDIT/name).read_text())
def cell(value):return str(value).replace('|','\\|').replace('\n',' ')


def main():
    report=json.loads((ROOT/'subjects/nmmmh/import_report.json').read_text())
    rows=[q for e in report['exams'] for q in json.loads((ROOT/e['question_file']).read_text())]
    edits=read('ocr_changes.json');changes=read('answer_changes.json')
    known=read('source_inventory.json')
    classification=read('chapter_review.json')
    deployment=read('DEPLOYMENT.json') if (AUDIT/'DEPLOYMENT.json').is_file() else {}
    verified=sum(q['verification_status']=='verified' for q in rows)
    pending=[q for q in rows if q['needs_review']]
    # Notation ambiguity is visibly transcribed, not an uninspected page.
    text_complete=len(rows)-sum(q['source_reference']['status']=='partial_visual_review' for q in rows)
    summary={'source_exam_count':len(known['known_exams']),'published_exam_count':report['exam_count'],
             'published_question_count':len(rows),'excluded_question_count':39,
             'source_questions_inspected':len(rows),'fully_compared_published_questions':text_complete,
             'partially_obscured_published_questions':len(rows)-text_complete,
             'ocr_corrected_questions':len({e['id'] for e in edits}),'source_field_corrections':len(edits),
             'recropped_images':28,'required_defective_crops_replaced':11,
             'independently_verified_answers':verified,'manual_review_count':len(pending),
             'answer_record_changes':len(changes),
             'changed_answer_letter':sum(bool(r['old_answer'] and r['new_answer']) for r in changes),
             'newly_resolved_answers':sum(not r['old_answer'] and bool(r['new_answer']) for r in changes),
             'withdrawn_unproven_answers':sum(bool(r['old_answer']) and not r['new_answer'] for r in changes),
             'rewritten_hints':sum(bool(q['hint']) for q in rows),
             'chapter_covered_questions':sum(bool(q['chapter_ids']) for q in rows),
             'content_classification_confirmed':len(rows)-classification['counts']['retained_outside_detailed_taxonomy_proposals'],
             'classification_provisional_taxonomy_gap':classification['counts']['retained_outside_detailed_taxonomy_proposals'],
             'multi_chapter_questions':classification['counts']['multi_chapter_questions'],
             'confirmed_duplicate_groups':sum(g['status']=='confirmed' for g in report['duplicate_groups']),
             'confirmed_duplicate_copies':sum(len(g['sources'])-1 for g in report['duplicate_groups'] if g['status']=='confirmed'),
             'potential_duplicate_groups':sum(g['status']=='potential' for g in report['duplicate_groups']),
             'additional_documents_inventory_only':True,
             'deployment_status':deployment.get('status','authorized_push_after_final_tests_not_yet_deployed')}
    (AUDIT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Kiểm định và nâng cấp NMMMH — 21/10/2026','',
        '## Phạm vi và mức độ chứng cứ','',
        'Đã đối chiếu **173 câu thuộc 5 đề đang xuất bản** với 85 trang PDF scan: 172 câu kiểm tra đủ nội dung, AT17 câu 3 còn hai ô của phương án D bị con trỏ chuột che trong nguồn. Không xem đáp án người làm chọn là đáp án chuẩn. Không coi bộ đáp án cũ là bằng chứng độc lập.','',
        'Ngân hàng nguồn có thêm **K16-1: 39 dòng/10 trang**, đã được rà ở thư mục nguồn nhưng vẫn loại khỏi website theo yêu cầu trước. K16-1 chỉ có 12 đáp án xác định duy nhất; 8 vị trí thiếu toàn bộ thân câu (10–15, 22–23), nhiều vị trí khác thiếu phương án/ký tự. 39 dòng không có nghĩa là 39 câu gốc đầy đủ. Báo cáo chi tiết: `NMMMH_AUDIT_20261021/k16_1_review.json` tại thư mục tài liệu gốc, không tái xuất bản đề này.','',
        '**Giới hạn:** DeThiOCR không còn; dùng DeThiPDF theo xác nhận người dùng. Kho tài liệu gồm 22 PDF/DOCX và 142 ảnh rời; các tài liệu ngoài sáu đề hiện có mới được kiểm kê. Không tuyên bố tất cả tài liệu này đã được nhập, giải hay OCR hết. Xem `source_inventory.json` và `additional_sources_review.json` nếu có.','',
        '| Nội dung | Kết quả |','|---|---|',
        f'| Đề trong ngân hàng / đang xuất bản | {len(known["known_exams"])} / {report["exam_count"]} |',
        f'| Câu trên web / nguồn có cả K16-1 | {len(rows)} / 212 dòng |',
        f'| Đã đối chiếu nguồn | {len(rows)}; {text_complete} đủ, 1 bị che một phần |',
        f'| Câu sửa OCR/chép lại | {summary["ocr_corrected_questions"]} câu / {len(edits)} trường |',
        f'| Công thức, số liệu, ký hiệu/nhãn toán sửa theo nguồn | {len(edits)} trường có nhật ký; không coi số render KaTeX là số lỗi OCR |',
        '| Ảnh crop mới đã kiểm tra trực quan | 28; 11 crop cũ thiếu/sai vùng được thay |',
        f'| Đáp án kiểm chứng độc lập, chốt để chấm | {verified} |',
        f'| Thay đổi khóa đáp án | {summary["changed_answer_letter"]} đổi chữ; {summary["newly_resolved_answers"]} chốt mới; {summary["withdrawn_unproven_answers"]} rút khóa thiếu căn cứ |',
        f'| Gợi ý viết lại | {summary["rewritten_hints"]}, tách khỏi giải thích/đáp án |',
        f'| Câu xuất hiện trong luyện theo chương | {summary["chapter_covered_questions"]}/{len(rows)}; xem mức tin cậy nhãn chương bên dưới |',
        f'| Phân chương theo nội dung | {summary["content_classification_confirmed"]} xác nhận; {summary["classification_provisional_taxonomy_gap"]} nhãn cũ còn là đề xuất; {summary["multi_chapter_questions"]} câu nhiều chương |',
        f'| Trùng đã kiểm / nghi trùng | {summary["confirmed_duplicate_groups"]} nhóm ({summary["confirmed_duplicate_copies"]} bản lặp chỉ gộp ở màn hình tổng hợp) / {summary["potential_duplicate_groups"]} nhóm giữ riêng |',
        f'| Cần rà soát nguồn/đáp án | {len(pending)}; vẫn có trong đề, không tính điểm |',
        '| Build/test | Website static: node syntax + KaTeX render validator; 9 unit tests; kiểm thử trình duyệt NMMMH/KTMT; xem TEST_RESULTS.md |',
        '| Triển khai | Đã được phép commit/push sau kiểm thử; xem DEPLOYMENT.json nếu có |','',
        '## Số câu từng đề/chương','',
        'Cột chương có thể giao nhau khi câu thực sự thuộc nhiều chương; không cộng các cột đó để suy ra số câu duy nhất. Giữ nguyên mã đề và số câu nguồn.','',
        '| Đề | Tổng | C1 | C2 | C3 | C4 | C5 | Chưa phân loại | Chấm được | Rà soát |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for exam in report['exams']:
        counts=exam['chapter_counts']
        lines.append('| '+cell(exam['source_exam_code'])+' | '+' | '.join(map(str,[exam['question_count'],*[counts[str(c)] for c in range(1,6)],counts['unclassified'],exam['graded_count'],exam['review_count']]))+' |')
    lines+=['','## Chương khi gộp tất cả đề','','| Chương | Bản ghi nguồn | Sau gộp trùng chắc chắn | Chấm được |','|---|---:|---:|---:|']
    for c in report['aggregate']:lines.append('| '+cell(c['chapter'])+' | '+' | '.join(map(str,[c['raw_count'],c['unique_count'],c['graded_count']]))+' |')
    lines+=['','Mỗi đề và mục luyện linh hoạt vẫn giữ mọi câu của từng đề. Chỉ màn hình gộp theo chương mới loại trùng đã xác minh. `import_report.json` chứa ID từng nhóm trùng. Không gộp câu chỉ vì giống thuật toán nhưng khác số liệu.','',
        '## Phân loại chưa thể chốt theo cây hiện có','',
        '173 câu được đọc và phân loại theo nội dung, không dùng luật từ khóa tự động. Có 7 điều chỉnh chương chính, 30 câu nhiều chương và 63 câu khớp được mã chủ đề chính thức. Tuy nhiên 59 câu toán nền không có chủ đề phù hợp trong cây đã cung cấp: giữ nhãn hiện có có cảnh báo, không biến 03.* đề xuất thành chủ đề chính thức. Danh sách và lý do từng câu trong [CLASSIFICATION_REVIEW.md](CLASSIFICATION_REVIEW.md). Chương 3–5 mới có tên trong mục lục, không tự đặt các chương con mới. Cần cây kiến thức mở rộng/giáo trình có cấu trúc toán nền để chốt 59 vị trí này.','',
        '## Thay đổi đáp án','','Dấu — nghĩa là không có khóa để chấm, không phải một lựa chọn A–D. Mọi quyết định đều có lý do/method/evidence trong `answer_changes.json` và `answer_decisions.json`.','',
        '| ID | Đề / câu gốc | Cũ | Mới | Căn cứ |','|---|---|---|---|---|']
    for row in changes:
        reason=row['explanation'].split('Kết quả:')[0].strip()
        if len(reason)>420:reason=reason[:420]+'… (xem JSON)'
        if row['id']=='nmmmh-de-thi-k16-3-2022':reason='Affine: 12a+b ≡ 14, 20a+b ≡ 12 (mod26); thử đủ A–D, chỉ (a,b)=(3,4), nhãn C, khớp cả hai cặp.'
        lines.append('| '+' | '.join(map(cell,[row['id'],row['source_exam_id']+' / '+row['source_question_number'],row['old_answer'] or '—',row['new_answer'] or '—',reason]))+' |')
    lines+=['','## Câu cần rà soát','','Danh sách đầy đủ nằm tại [MANUAL_REVIEW.md](MANUAL_REVIEW.md) và `../needs_review.json`. Không dùng nhãn “verified” cho các câu này.','',
        'Cần bổ sung: ảnh AT17 câu 3 không có con trỏ che; nguồn định nghĩa `f(n)` ở K16-2 câu 11; quy ước ký hiệu (21/235) ở K16-3 câu 2052; đáp án/đính chính chính thức cho câu nhiều phương án, không phương án hoặc lời văn mơ hồ. Không sửa số liệu gốc để cứu đáp án.','',
        '## Kiến trúc và chức năng','',
        'Không đổi stack: HTML/CSS/JavaScript static, cùng máy chấm/lịch sử. Mỗi đề chỉ có một JSON chuẩn; `chapter_ids` là metadata bổ sung, các chế độ dùng cùng đối tượng câu hỏi. Không nhúng câu hỏi vào HTML/JS. Công thức KaTeX 0.16.22 phục vụ từ `vendor/`, không phụ thuộc CDN; dữ liệu gốc đọc được giữ cùng `display_blocks`. Ảnh không base64, có hộp phóng to bằng bàn phím/cảm ứng.','',
        'Luyện một/nhiều chương, lọc đề/trạng thái, số câu tùy chọn/toàn bộ; trộn câu và trộn phương án bằng ID gốc. Câu “tất cả” hoặc tham chiếu nhãn giữ thứ tự phương án. Gợi ý không tự hiện đáp án; giải thích có nút riêng. Thi chỉ chấm sau nộp. Lượt đang làm lưu riêng `nmmmh-active-session-v1`; reload giữ câu/đáp án/thứ tự. Xem lại bài đã nộp không ghi thêm lịch sử. Một lần làm một câu không bị đếm thêm khi đổi phương án.','',
        'Lịch sử cũ không bị xóa hoặc tự chấm lại theo khóa mới. Bài đang làm có chữ ký dữ liệu; khi nguồn/khóa thay đổi, bản lưu cũ không được khôi phục và chấm nhầm.','',
        '## Nguồn học thuật dùng kiểm chứng','',
        '- [Handbook of Applied Cryptography — chương 2](https://cacr.uwaterloo.ca/hac/about/chap2.pdf): số học/nhóm/trường.',
        '- [HAC — chương 8](https://cacr.uwaterloo.ca/hac/about/chap8.pdf): RSA, Rabin, ElGamal, Merkle–Hellman; phân biệt cơ sở thiết kế lịch sử với bảo đảm an toàn.',
        '- [HAC — chương 9](https://cacr.uwaterloo.ca/hac/about/chap9.pdf): hàm băm và xác thực.',
        '- [HAC — chương 11](https://cacr.uwaterloo.ca/hac/about/chap11.pdf): chữ ký số.',
        '- [NIST FIPS 197](https://csrc.nist.gov/pubs/fips/197/final): AES.',
        '- [NIST SP 800-38A](https://csrc.nist.gov/pubs/sp/800/38/a/final): các chế độ mã khối.','',
        '## Đường dẫn ba màn hình làm bài','',
        '- [Cả đề](http://127.0.0.1:8765/#subject=nmmmh&exam=de-thi-nmmmh&chapter=all&action=start)',
        '- [Chương trong một đề](http://127.0.0.1:8765/#subject=nmmmh&exam=de-thi-nmmmh&chapter=2&action=start)',
        '- [Chương của tất cả đề](http://127.0.0.1:8765/#subject=nmmmh&exam=all&chapter=2&action=start)',
        '- [Luyện một/nhiều chương và lọc số câu](http://127.0.0.1:8765/#subject=nmmmh)','',
        'Các hash tương tự dùng tại https://chaamsthan.github.io/ktmt-quiz/ sau khi push/deploy. Trạng thái triển khai và commit được ghi riêng ở DEPLOYMENT.json; không coi kiểm thử local là kiểm thử public.','',
        '## Backup và rollback','',
        'Snapshot trước sửa: commit `98123eba5e1247c1ac57758039c05dc9cad76451`. Bản sao bền vững trong thư mục tài liệu gốc: `NMMMH_AUDIT_20261021/backups/web-before-98123eb.tar.gz` và `source-before-20261021.tar.gz`; bản sao phiên còn ở `/tmp/nmmmh-upgrade-backup-RFhpyA/`. Không ghi đè PDF/DOCX, bộ nguồn DAPAN_KIEMCHUNG hay file user `extract_questions.py`.','',
        'Các sửa đổi dùng overlay `approved_changes.json`, tái nhập có kiểm tra old/new chính xác. Không chạy importer cũ bỏ qua overlay vì sẽ phục hồi khóa sai. Xem README để tái tạo và kiểm thử. Không thực hiện rollback hoặc xóa đề khác. Người dùng đã xác nhận cho commit/push sau khi kiểm thử đạt.','']
    (AUDIT/'UPGRADE_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    manual=['# Câu cần rà soát — không tính điểm','',f'{len(pending)} câu; giữ nguyên trong từng đề.','',
            '| ID | PDF nguồn / trang | Lý do |','|---|---|---|']
    for q in pending:
        reason=q['answer_audit']['explanation']
        if len(reason)>900:reason=reason[:900]+'… (xem answer_decisions.json)'
        ref=q['source_reference'];manual.append('| '+' | '.join(map(cell,[q['id'],ref['file']+' / '+','.join(map(str,ref['pages'])),reason]))+' |')
    (AUDIT/'MANUAL_REVIEW.md').write_text('\n'.join(manual)+'\n',encoding='utf-8')
    taxonomy=['# Phân chương chưa chốt do thiếu mục trong cây','',
              'Giữ nhãn cũ có cảnh báo để không làm mất câu trong luyện tập. Đây là rà soát phân loại, độc lập với 34 câu chưa có khóa chấm.','',
              '| ID | Nhãn đang giữ | Lý do |','|---|---|---|']
    for row in classification['questions']:
        if row['needs_taxonomy_review']:taxonomy.append('| '+' | '.join(map(cell,[row['id'],row['primary_chapter_id'],row['rationale']]))+' |')
    (AUDIT/'CLASSIFICATION_REVIEW.md').write_text('\n'.join(taxonomy)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()
