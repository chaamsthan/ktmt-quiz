# KTMT Quiz Lab

Trang web trắc nghiệm tương tác được sinh từ `300-cau-hoi-trac-nghiem-kien-truc-may-tinh.pdf`.

Trên trang chủ, chọn một chương để làm toàn bộ câu hỏi theo thứ tự trong PDF. Tick `Trộn câu hỏi ngẫu nhiên` nếu muốn xáo trộn thứ tự câu trong chương đó.

## Chạy local

```bash
python3 -m http.server 8000
```

Mở <http://localhost:8000>.

Không mở trực tiếp bằng `file://` vì trình duyệt sẽ chặn `fetch("questions.json")`.

## Dữ liệu

- `exam_sets.json`: danh sách các bộ đề; thêm bộ mới bằng cách thêm metadata và file câu hỏi tương ứng.
- `questions.json`: 300 câu theo đúng thứ tự trong PDF, chia thành 6 chương.
- `images/`: ảnh/sơ đồ được crop từ PDF cho 27 câu có hình.
- `extract_questions.py`: script tái tạo JSON và ảnh crop từ PDF nguồn.

Tái tạo dữ liệu:

```bash
uv run --with pymupdf --with vietnamese python extract_questions.py
```

Đáp án trong JSON được lấy từ vùng highlight vàng có sẵn trong PDF (`answer_evidence: highlighted_in_source_pdf`). Các câu không có bằng chứng đáp án sẽ có `correct_answer: null` và `needs_review: true`.

## Môn Mật mã học

Môn mới dùng cùng HTML/CSS/JavaScript, máy chấm và khóa localStorage `ktmt-quiz-lab-v1` với KTMT. Dữ liệu KTMT trong `questions.json` và `exam_sets.json` không thay đổi.

- `nmmmh.js`: bộ điều phối môn, chọn đề/chương và loại trùng khi gộp.
- `subjects/nmmmh/manifest.json`: tên/thứ tự chương và metadata sáu đề nguồn.
- `subjects/nmmmh/exams/*.json`: từng đề độc lập, giữ số câu nguồn và các trường câu hỏi hiện có; các trường ảnh/bảng, chương con, căn cứ đáp án và nguồn được thêm tùy chọn.
- `images/nmmmh/`: 32 ảnh nguồn, không dùng base64.
- `subjects/nmmmh/REPORT.md`: số câu từng đề/chương, nhóm trùng và danh sách rà soát.
- `subjects/nmmmh/needs_review.json`: danh sách rà soát máy đọc được.
- `subjects/nmmmh/import_log.json`: ghi nhận nạp xong từng đề trước khi sang đề tiếp theo.

Ba màn hình làm bài:

- Cả đề: `#subject=nmmmh&exam=de-thi-nmmmh&chapter=all&action=start`
- Chương trong đề: `#subject=nmmmh&exam=de-thi-nmmmh&chapter=2&action=start`
- Chương trong tất cả đề: `#subject=nmmmh&exam=all&chapter=2&action=start`

Thêm `&mode=exam` để thi; mặc định là học. Nhóm chương có checkbox trộn câu, còn cả đề luôn giữ thứ tự gốc. Điểm tính trên câu có đáp án kiểm chứng đã được người dùng chấp thuận, **không phải bảng đáp án chính thức của trường**. Câu chưa chốt đáp án giữ `correct_answer: null`, không tính điểm, không đưa vào câu sai. Nhóm không có đáp án được ghi “Chưa chấm”, không ghi điểm 0.

Khi gộp, chỉ loại trùng đã xác minh cả nội dung câu, các lựa chọn và nội dung đáp án đúng; vẫn giữ nguyên mọi bản ghi trong từng đề. Câu nghi trùng thiếu đáp án được giữ riêng. Ảnh/bảng khác nhau không tự gộp. Lịch sử dùng chung, bổ sung môn, đề, chương, số câu, số câu chấm được và điểm; ID môn mới có tiền tố riêng nên không ghi đè tiến độ KTMT.

Nạp lại từ bộ dữ liệu đã phân loại/kiểm chứng (không OCR hoặc tự giải lại):

```bash
python3 tools/import_nmmmh.py --source '/đường/dẫn/NMMMH'
```

Thư mục nguồn phải có `DAPAN_KIEMCHUNG/`, `DeThiOCR/PHAN_LOAI_THEO_CHUONG/` và `TONGQUANKIENTHUC/NMMMH_Phan_loai_kien_thuc.json`. Bổ sung/sửa câu tại nguồn rồi chạy importer, kiểm tra báo cáo và commit dữ liệu sinh ra để GitHub Pages cập nhật.

Kiểm tra dữ liệu và trình duyệt, sau khi chạy HTTP server:

```bash
uv run --with playwright==1.60.0 python -m playwright install chromium
uv run --with playwright==1.60.0 python tools/test_nmmmh.py --url http://127.0.0.1:8000/
```

Các kiểm tra chạy trong trình duyệt mới, không xóa localStorage của người học.
