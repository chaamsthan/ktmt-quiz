# Kiểm thử NMMMH — 21/10/2026

## Bản local trước push

Tất cả mục sau đã chạy thật và đạt trên dữ liệu cuối: 5 đề, 173 câu, 139 khóa chấm, 34 câu không chấm; 28 ảnh crop mới. K16-1 vẫn không xuất bản. Các bộ trình duyệt dùng profile/localStorage tạm, không chạm dữ liệu người học.

| Kiểm tra | Kết quả |
|---|---|
| `node tools/check_site.cjs` | PASS: cú pháp 3 JS, dữ liệu, 173 hints, 231 biểu thức KaTeX, 28 ảnh |
| `python3 tools/test_nmmmh_data.py --source …` | PASS: 9 unit tests; đúng ID/số câu/thứ tự, nguồn SHA-256, A–D, các sửa có chứng cứ, khóa/cờ rà soát, ảnh đúng ID/hash, chương, corrected theory input |
| `python3 tools/nmmmh_numeric_audit.py --self-test` | PASS: độc lập metadata đáp án, hoán vị A–D cho 173 dòng; 65.536 cặp GF, φ/Jacobi/ECC; trường hợp đa/không đáp án |
| `python3 tools/nmmmh_numeric_audit.py --check` | PASS: báo cáo hiện hành và tái tạo xác định |
| `python3 tools/nmmmh_theory_audit.py --check` | PASS: 69 câu gốc + Q2040, đủ đánh giá A–D, nguồn và chuỗi input hiện tại |
| `python3 tools/nmmmh_hints.py --require-complete` | PASS: 173/173 hints, 0 pending; kiểm mẫu không tiết lộ chữ đáp án |
| `python3 tools/nmmmh_source_k16.py` / `nmmmh_source_other.py` | PASS: provenance/bbox/hash; không coi script validator thay được nhận xét trực quan |
| ESLint 9.39.1, `no-unreachable`, `no-dupe-keys`, `no-constant-condition` | PASS; lint cơ bản, không tuyên bố có cấu hình lint framework sẵn |
| Ruff `E9,F63,F7,F82` trên các Python thay đổi | PASS |
| `git diff --check` | PASS |
| `git diff --exit-code -- questions.json exam_sets.json subjects/ktmt` | PASS: dữ liệu môn KTMT không đổi |
| `uv run --with playwright==1.60.0 python tools/run_quiz_checks.py` | PASS cả 3 bộ bên dưới; runner tự quản lý preview HTTP và đóng sau chạy |

Không có bundler/framework nên không có lệnh `npm run build` để chạy. Static validator và kiểm thử trình duyệt là cổng build/QA thực tế; không gắn nhãn một lệnh build chưa tồn tại là đã chạy.

## Phạm vi kiểm thử trình duyệt

- `test_nmmmh.py`: KTMT 300 + placeholder500; NMMMH cả đề/chương trong đề/chương tất cả đề; điểm chỉ từ khóa đã kiểm chứng; nhóm không có khóa ghi “Chưa chấm”; ảnh/bảng/ma trận; giữ số câu 2021–2060; không thêm lịch sử khi xem lại bài; đánh dấu/ôn sai/lịch sử; cách ly môn; 1440/390/320 px; không JS error, thiếu asset hoặc tràn trang.
- `test_nmmmh_upgrade.py`: render/làm lần lượt đủ 173 câu; hint/answer riêng; kiểm A–D hiển thị tới ID gốc khi shuffle; ảnh decode và KaTeX; reload lượt học/thi/đánh dấu giữ câu và lựa chọn; nộp một lần; đổi đáp án chỉ tính một lượt; bộ lọc rỗng và giới hạn số câu; loại unknown-key khỏi danh sách sai cũ; zoom ảnh và Escape; dữ liệu localStorage hỏng/quota bị chặn không làm crash.
- `test_ktmt_chapter2.py`: cả 59 câu KTMT, study/exam, 59/59; 6 ảnh/sơ đồ, số mũ/XOR, 3 lưu ý nguồn; mọi câu ở 1440/390/320 px.

Ảnh QA local của lần chạy cuối:

- `/tmp/nmmmh-browser-t449rvk3`
- `/tmp/nmmmh-upgrade-browser-b4aczfid`
- `/tmp/ktmt-ch2-browser-0thfkia5`

Các thư mục screenshot là chứng cứ của phiên kiểm thử, không phải tài liệu nguồn hoặc bảo đảm không có lỗi chưa được test. Báo cáo không thay thế rà soát thủ công 34 câu/59 nhãn còn thiếu căn cứ.

## Bản public

Trạng thái triển khai, commit và kiểm tra public được ghi riêng trong `DEPLOYMENT.json` sau push. Không lấy kết quả local ở trên để khẳng định public đã cập nhật.
