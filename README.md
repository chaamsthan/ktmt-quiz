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

### Chương 2 KTMT đã đối chiếu lại với PDF

59 câu chương 2 được đọc lại trực tiếp từ hình trang PDF 6–16. Nhãn A–D được giữ theo chữ in trong nguồn, kể cả khi PDF sắp hai cột; không lấy thứ tự từ luồng văn bản PDF. Sáu đáp án sửa lại theo highlight: 2.10 → D, 2.15 → C, 2.19 → B, 2.34 → C, 2.45 → B, 2.57 → D.

- `tools/ktmt_chapter2_source.json`: bản chép đã đối chiếu từng câu, công thức, lựa chọn và đáp án tô vàng.
- `images/ktmt/chapter-2/`: ba sơ đồ (2.7, 2.8, 2.18) và ba bảng (2.15, 2.17, 2.19), cắt đúng vùng nguồn ở 252 dpi. Bấm ảnh trong bài để mở kích thước đầy đủ.
- `subjects/ktmt/chapter2_audit.json`: SHA-256 PDF, tọa độ nhãn đáp án và highlight, tọa độ cắt ảnh và các lưu ý nguồn.

Số mũ dùng khối `math` với ký hiệu `^{...}`, được hiển thị bằng `<sup>` an toàn; giữ riêng dấu ×, ⊕, → và −. Câu 2.13, 2.31, 2.42 có mâu thuẫn/lỗi in ngay trong PDF: giữ nguyên nội dung và chấm theo highlight như nguồn, đồng thời hiện lưu ý sau khi trả lời. `needs_review` của các câu này đánh dấu lỗi nguồn, không có nghĩa là chưa xác định được highlight.

Tái tạo riêng chương 2 (không thay đổi 241 câu còn lại):

```bash
uv run --with pymupdf python tools/rebuild_ktmt_chapter2.py --write
uv run --with pymupdf python tools/rebuild_ktmt_chapter2.py
uv run --with playwright==1.60.0 python tools/test_ktmt_chapter2.py --url http://127.0.0.1:8000/
```

Không chạy bộ trích xuất cũ để ghi đè bản chương 2 đã kiểm chứng; nếu tái tạo cả ngân hàng thì phải áp dụng lại bản chương 2 này. PDF nguồn giữ ở máy, không bị sửa hay đưa vào Git.

## Môn Mật mã học

Môn mới dùng cùng HTML/CSS/JavaScript, máy chấm và khóa localStorage `ktmt-quiz-lab-v1` với KTMT. Dữ liệu KTMT trong `questions.json` và `exam_sets.json` không thay đổi.

### Hai nhóm mới: Đề cương 2025 / Đề giữa kì 2026

- `#subject=nmmmh&collection=de-cuong-2025`: 7 DOCX, 290 câu; giữ dấu đáp án tô vàng/gạch chân trong nguồn.
- `#subject=nmmmh&collection=de-giua-ki-2026`: 2 PDF scan, 77 câu xuất hiện (ca 1: 37, ca 2: 40). Nguồn ca 1 không có câu 21–23; giữ dãy số gốc, không bù câu bịa.
- `#subject=nmmmh` vẫn mở bộ đề cũ 5 đề/173 câu. Ba thẻ nhóm xuất hiện ngay trên trang môn; bộ lọc chương/đề, lịch sử và lượt đang làm hoạt động trong nhóm đang chọn.

Hai nhóm thêm bằng thuộc tính **tùy chọn** `collections` trong manifest; không thay cấu trúc các đề cũ. Cả đề và luyện chương vẫn dùng cùng file JSON. Báo cáo theo từng đề/chương, câu trùng và trường hợp chưa chốt: [COLLECTIONS_2025_2026.md](subjects/nmmmh/COLLECTIONS_2025_2026.md).

Phân biệt `source_marked` (đáp án theo dấu DOCX, không tuyên bố đã giải độc lập) và `verified` (có phép tính/đối chiếu độc lập). Mọi dấu gốc và vị trí run Word được giữ trong `audit/collections-2025-2026/*-native.json`. Khi dấu nguồn mâu thuẫn với phép tính hoặc đề có nhiều đáp án: giữ `source_marked_answer` để đối chiếu, tạm đặt `correct_answer: null`, không chấm bừa. Nút đã chọn trên ảnh PDF **không bao giờ** là đáp án chuẩn.

Tái tạo hai nhóm (cần đúng thư mục `NMMMH/NMMMH/Đề_cương_2025` và `NMMMH/NMMMH/Đề_giữa_kì_2026` bên dưới nguồn):

```bash
uv run --with lxml --with pymupdf --with rapidocr_onnxruntime python tools/extract_nmmmh_collections.py --source '/đường/dẫn/NMMMH' --ocr
uv run --with pillow python tools/import_nmmmh_collections.py
uv run --with pillow --with playwright==1.60.0 python tools/run_quiz_checks.py
```

OCR chạy cục bộ; DOCX dùng văn bản và ảnh gốc, không OCR lại văn bản đã có. `nmmmh_collection_review.py` / `nmmmh_midterm_review.py` ghi nhận đọc từng câu, chương, mẹo, tọa độ crop và quyết định; `numeric_docx` / `numeric_midterm` tính trước rồi so đủ bốn phương án. Không truyền khóa cũ hoặc trạng thái radio vào máy tính kiểm chứng. Crop được lưu nguyên pixel trong `images/nmmmh/collections/`; `crop_manifest.json` ghi SHA-256, trang và hộp pixel. `crop_visual_review.json` chỉ xác nhận sau khi mở kiểm tra toàn bộ ảnh cuối; crop mới đổi hash phải được xem lại. DOCX/PDF gốc không sửa hoặc commit.

Rollback: quay về commit trước đợt nhập, hoặc chỉ bỏ hai mục `collections` khỏi manifest; không phải xóa dữ liệu người học. Importer bộ cũ giữ nguyên `collections`, importer hai nhóm mới kiểm tra SHA-256 của mọi đề cũ và KTMT không đổi.

- `nmmmh.js`: bộ điều phối môn, chọn đề/chương và loại trùng khi gộp.
- `subjects/nmmmh/manifest.json`: tên/thứ tự chương và metadata năm đề đang xuất bản.
- `subjects/nmmmh/exams/*.json`: từng đề độc lập, giữ số câu nguồn và các trường câu hỏi hiện có; các trường ảnh/bảng, chương con, căn cứ đáp án và nguồn được thêm tùy chọn.
- `images/nmmmh/`: 28 ảnh nguồn đang sử dụng, không dùng base64.
- `subjects/nmmmh/excluded_exams.json`: các đề không xuất bản; hiện bỏ `de-thi-k16-1` theo yêu cầu người dùng, không xóa DOCX/bộ đáp án nguồn.
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

Thư mục nguồn cần `DAPAN_KIEMCHUNG/` và `TONGQUANKIENTHUC/NMMMH_Phan_loai_kien_thuc.json`. Nếu còn `DeThiOCR/PHAN_LOAI_THEO_CHUONG/`, importer đối chiếu bản phân loại đó. Nếu thiếu, giữ phân loại đã lưu rồi áp dụng các quyết định kiểm định tường minh, không đoán lại bằng từ khóa. Đợt 21/10/2026 dùng `DeThiPDF` theo xác nhận người dùng.

Importer đọc `excluded_exams.json` trước khi tạo đề, nhóm trùng, báo cáo và CSV đáp án. Vì vậy chạy lại sẽ không tự đưa K16-1 trở lại website. Nếu muốn khôi phục, bỏ ID này khỏi danh sách loại rồi nhập lại từ nguồn vẫn còn nguyên.

Kiểm tra dữ liệu và trình duyệt, sau khi chạy HTTP server:

```bash
uv run --with playwright==1.60.0 python -m playwright install chromium
uv run --with playwright==1.60.0 python tools/test_nmmmh.py --url http://127.0.0.1:8000/
```

Các kiểm tra chạy trong trình duyệt mới, không xóa localStorage của người học.

### Bản kiểm định NMMMH 21/10/2026

Báo cáo đầy đủ: [UPGRADE_REPORT.md](subjects/nmmmh/audit/UPGRADE_REPORT.md). Số liệu và giới hạn lấy từ file này, không dùng số cũ trong ghi chép triển khai trước.

- Một nguồn chuẩn: `subjects/nmmmh/exams/*.json`. Cả đề, chương trong đề, chương mọi đề và luyện nhiều chương đều đọc các bản ghi này. Không copy ngân hàng sang JavaScript.
- `nmmmh-practice.js`: chọn nhiều chương, số câu tùy ý/toàn bộ, lọc đề/trạng thái, trộn câu/phương án bằng ID gốc. Câu có tham chiếu nhãn hoặc hình chứa A–D gốc không trộn phương án.
- Công thức/ma trận dùng KaTeX local tại `vendor/katex/`; `display_blocks` được sinh từ văn bản nguồn, không sửa giá trị để làm đẹp. 28 ảnh crop mới có SHA-256, trang nguồn và bbox trong audit; ảnh cũ vẫn giữ để rollback. Bấm ảnh để phóng to.
- Gợi ý ngắn nằm trong JSON, không tự hiện đáp án. Giải thích/căn cứ tách trong nút riêng. Lượt thi không hiện đúng/sai trước khi nộp.
- Lượt đang làm có khóa riêng `nmmmh-active-session-v1`; lịch sử/đánh dấu vẫn dùng khóa chung cũ. Reload giữ trạng thái; thay nguồn/khóa sẽ vô hiệu bản lưu không còn khớp. Lịch sử cũ không bị xóa hoặc chấm lại tự động.
- `audit/approved_changes.json`: overlay ID ổn định, mỗi sửa OCR có old/new/evidence; quyết định đáp án có method/evidence. Tái nhập không ghi đè tài liệu nguồn. `source_classification` giữ nhãn cũ, `classification_audit` ghi lý do đổi chương; nhãn chưa đủ nguồn vẫn có cảnh báo.
- `audit/answer_changes.json`: khóa cũ/mới và căn cứ; `MANUAL_REVIEW.md` là câu chưa chốt, `CLASSIFICATION_REVIEW.md` là nhãn chương còn đề xuất. Hai loại rà soát không đồng nghĩa nhau.

Tái tạo từ chứng cứ đã kiểm định (không tự xác nhận lại câu mới):

```bash
python3 tools/assemble_nmmmh_audit.py --source '/đường/dẫn/NMMMH'
python3 tools/finalize_nmmmh_verification.py --source '/đường/dẫn/NMMMH'
python3 tools/import_nmmmh.py --source '/đường/dẫn/NMMMH'
python3 tools/nmmmh_numeric_audit.py --self-test
python3 tools/nmmmh_theory_audit.py --check
python3 tools/nmmmh_hints.py --require-complete
python3 tools/report_nmmmh_upgrade.py
```

Thêm câu/đề mới cần bổ sung chứng cứ source/chapter/numeric/theory/hint tương ứng. Không sửa duy nhất file JSON xuất bản rồi chạy importer, vì lần nhập sau sẽ ghi đè. Với một đáp án cần cập nhật nhanh, sửa đúng `approved_changes.json[ID].answer_decision`, kèm `correct_answer`, `status`, `valid_options`, `explanation`, `method`, `evidence`; chạy importer và kiểm thử. Nếu chưa có bằng chứng, dùng `correct_answer: null`, `status: "needs_review"`. Lưu ý: chạy lại **finalizer** sẽ tính lại overlay từ artifact kiểm chứng, nên một điều chỉnh thủ công đã xác nhận cũng phải được cập nhật vào artifact numeric/theory tương ứng trước khi tái tạo toàn bộ.

Kiểm thử trước commit/push:

```bash
node tools/check_site.cjs
python3 tools/test_nmmmh_data.py --source '/đường/dẫn/NMMMH'
python3 tools/nmmmh_numeric_audit.py --check
uv run --with playwright==1.60.0 python tools/test_nmmmh.py --url http://127.0.0.1:8000/
uv run --with playwright==1.60.0 python tools/test_nmmmh_upgrade.py --url http://127.0.0.1:8000/
uv run --with playwright==1.60.0 python tools/test_ktmt_chapter2.py --url http://127.0.0.1:8000/
```

Website không có bundler/framework build. `check_site.cjs` kiểm tra cú pháp JavaScript, dữ liệu, ảnh và render KaTeX thực tế; kiểm thử trình duyệt chạy cả desktop và điện thoại. Bộ numeric tự kiểm 65.536 cặp GF(2⁸), đối chiếu φ/Jacobi/ECC và kiểm tính độc lập với metadata đáp án/hoán vị A–D. Các kiểm tra tự động không thay cho bước đối chiếu trực quan PDF; chi tiết từng câu và các giới hạn được ghi trong audit.

Có thể chạy đồng thời ba bộ kiểm thử trình duyệt bằng preview tạm do runner tự quản lý (không cần mở server riêng):

```bash
uv run --with playwright==1.60.0 python tools/run_quiz_checks.py
```

Runner tự đóng preview sau kiểm thử. Thêm `--url https://chaamsthan.github.io/ktmt-quiz/` để kiểm tra bản đã triển khai; kiểm thử này chỉ đọc website và dùng localStorage trình duyệt tạm.
