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
