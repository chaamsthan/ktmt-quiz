# Kiểm định và nâng cấp NMMMH — 21/10/2026

## Phạm vi và mức độ chứng cứ

Đã đối chiếu **173 câu thuộc 5 đề đang xuất bản** với 85 trang PDF scan: 172 câu kiểm tra đủ nội dung, AT17 câu 3 còn hai ô của phương án D bị con trỏ chuột che trong nguồn. Không xem đáp án người làm chọn là đáp án chuẩn. Không coi bộ đáp án cũ là bằng chứng độc lập.

Ngân hàng nguồn có thêm **K16-1: 39 dòng/10 trang**, đã được rà ở thư mục nguồn nhưng vẫn loại khỏi website theo yêu cầu trước. K16-1 chỉ có 12 đáp án xác định duy nhất; 8 vị trí thiếu toàn bộ thân câu (10–15, 22–23), nhiều vị trí khác thiếu phương án/ký tự. 39 dòng không có nghĩa là 39 câu gốc đầy đủ. Báo cáo chi tiết: `NMMMH_AUDIT_20261021/k16_1_review.json` tại thư mục tài liệu gốc, không tái xuất bản đề này.

**Giới hạn:** DeThiOCR không còn; dùng DeThiPDF theo xác nhận người dùng. Kho tài liệu gồm 22 PDF/DOCX và 142 ảnh rời; các tài liệu ngoài sáu đề hiện có mới được kiểm kê. Không tuyên bố tất cả tài liệu này đã được nhập, giải hay OCR hết. Xem `source_inventory.json` và `additional_sources_review.json` nếu có.

| Nội dung | Kết quả |
|---|---|
| Đề trong ngân hàng / đang xuất bản | 6 / 5 |
| Câu trên web / nguồn có cả K16-1 | 173 / 212 dòng |
| Đã đối chiếu nguồn | 173; 172 đủ, 1 bị che một phần |
| Câu sửa OCR/chép lại | 19 câu / 21 trường |
| Công thức, số liệu, ký hiệu/nhãn toán sửa theo nguồn | 21 trường có nhật ký; không coi số render KaTeX là số lỗi OCR |
| Ảnh crop mới đã kiểm tra trực quan | 28; 11 crop cũ thiếu/sai vùng được thay |
| Đáp án kiểm chứng độc lập, chốt để chấm | 139 |
| Thay đổi khóa đáp án | 1 đổi chữ; 4 chốt mới; 14 rút khóa thiếu căn cứ |
| Gợi ý viết lại | 173, tách khỏi giải thích/đáp án |
| Câu xuất hiện trong luyện theo chương | 173/173; xem mức tin cậy nhãn chương bên dưới |
| Phân chương theo nội dung | 114 xác nhận; 59 nhãn cũ còn là đề xuất; 30 câu nhiều chương |
| Trùng đã kiểm / nghi trùng | 34 nhóm (42 bản lặp chỉ gộp ở màn hình tổng hợp) / 7 nhóm giữ riêng |
| Cần rà soát nguồn/đáp án | 34; vẫn có trong đề, không tính điểm |
| Build/test | Website static: node syntax + KaTeX render validator; 9 unit tests; kiểm thử trình duyệt NMMMH/KTMT; xem TEST_RESULTS.md |
| Triển khai | Đã được phép commit/push sau kiểm thử; xem DEPLOYMENT.json nếu có |

## Số câu từng đề/chương

Cột chương có thể giao nhau khi câu thực sự thuộc nhiều chương; không cộng các cột đó để suy ra số câu duy nhất. Giữ nguyên mã đề và số câu nguồn.

| Đề | Tổng | C1 | C2 | C3 | C4 | C5 | Chưa phân loại | Chấm được | Rà soát |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| De_thi_AT17_bo_1 | 13 | 1 | 5 | 7 | 1 | 0 | 0 | 12 | 1 |
| De_thi_NMMMH | 40 | 4 | 12 | 21 | 9 | 3 | 0 | 33 | 7 |
| De_thi_mat_ma_2021_trac_nghiem | 40 | 4 | 12 | 21 | 9 | 3 | 0 | 33 | 7 |
| de-thi-k16-2 | 40 | 6 | 10 | 22 | 8 | 3 | 0 | 29 | 11 |
| de-thi-k16-3 | 40 | 4 | 9 | 26 | 6 | 1 | 0 | 32 | 8 |

## Chương khi gộp tất cả đề

| Chương | Bản ghi nguồn | Sau gộp trùng chắc chắn | Chấm được |
|---|---:|---:|---:|
| Chương 1. Tổng quan về mật mã học | 19 | 17 | 8 |
| Chương 2. Các hệ mật khóa bí mật | 48 | 37 | 26 |
| Chương 3. Các hệ mật khóa công khai | 97 | 75 | 57 |
| Chương 4. Hàm băm, xác thực và chữ ký số | 33 | 22 | 13 |
| Chương 5. Vấn đề phân phối và thỏa thuận khóa | 10 | 6 | 3 |
| Chưa phân loại | 0 | 0 | 0 |

Mỗi đề và mục luyện linh hoạt vẫn giữ mọi câu của từng đề. Chỉ màn hình gộp theo chương mới loại trùng đã xác minh. `import_report.json` chứa ID từng nhóm trùng. Không gộp câu chỉ vì giống thuật toán nhưng khác số liệu.

## Phân loại chưa thể chốt theo cây hiện có

173 câu được đọc và phân loại theo nội dung, không dùng luật từ khóa tự động. Có 7 điều chỉnh chương chính, 30 câu nhiều chương và 63 câu khớp được mã chủ đề chính thức. Tuy nhiên 59 câu toán nền không có chủ đề phù hợp trong cây đã cung cấp: giữ nhãn hiện có có cảnh báo, không biến 03.* đề xuất thành chủ đề chính thức. Danh sách và lý do từng câu trong [CLASSIFICATION_REVIEW.md](CLASSIFICATION_REVIEW.md). Chương 3–5 mới có tên trong mục lục, không tự đặt các chương con mới. Cần cây kiến thức mở rộng/giáo trình có cấu trúc toán nền để chốt 59 vị trí này.

## Thay đổi đáp án

Dấu — nghĩa là không có khóa để chấm, không phải một lựa chọn A–D. Mọi quyết định đều có lý do/method/evidence trong `answer_changes.json` và `answer_decisions.json`.

| ID | Đề / câu gốc | Cũ | Mới | Căn cứ |
|---|---|---|---|---|
| nmmmh-de-thi-nmmmh-4 | de-thi-nmmmh / 4 | A | — | A chắc chắn sai về lan lỗi ECB; B mơ hồ/không đúng tuyệt đối. Không ép đáp án đơn cho lời văn CBC thiếu điều kiện. |
| nmmmh-de-thi-nmmmh-5 | de-thi-nmmmh / 5 | D | — | A,B là khía cạnh chuẩn; chống chối bỏ được thêm trong slide môn học theo nghĩa rộng. Thiếu ràng buộc nghĩa. |
| nmmmh-de-thi-nmmmh-32 | de-thi-nmmmh / 32 | D | — | A đúng; B,C chỉ chấp nhận được khi nêu ngữ cảnh giáo trình cụ thể. Không ép D từ định nghĩa lỏng. |
| nmmmh-de-thi-mat-ma-2021-trac-nghiem-5 | de-thi-mat-ma-2021-trac-nghiem / 5 | — | D | Áp dụng B.text từ source override, quan hệ là h(x)=h(x'). A,B,C đều là ba định nghĩa đúng; D đúng theo quy ước chọn 'tất cả'. Kết luận tính trên chuỗi corrected_input bên dưới, không lấy từ đáp án cũ. |
| nmmmh-de-thi-mat-ma-2021-trac-nghiem-6 | de-thi-mat-ma-2021-trac-nghiem / 6 | — | D | Tính độc lập và đối chiếu đủ A–D; chỉ D khớp. |
| nmmmh-de-thi-mat-ma-2021-trac-nghiem-12 | de-thi-mat-ma-2021-trac-nghiem / 12 | D | — | D chắc chắn sai; A mơ hồ về khối/toàn thông điệp và bảo đảm đổi khóa. Không tự ép D khi A cũng có cách đọc sai. |
| nmmmh-de-thi-mat-ma-2021-trac-nghiem-23 | de-thi-mat-ma-2021-trac-nghiem / 23 | D | — | Theo định nghĩa chuẩn A,B đúng, chống chối bỏ là mục tiêu khác; Slide 138 bao gồm chống chối bỏ trong phạm vi xác thực rộng. |
| nmmmh-de-thi-mat-ma-2021-trac-nghiem-29 | de-thi-mat-ma-2021-trac-nghiem / 29 | B | — | Sau override, A có 0<r<n nên sai ở r=0; B vẫn gọi các đại diện một lớp là các lớp nên sai. C,D đúng. A+B sai: không còn đáp án SAI đơn; không chuyển B sang A. |
| nmmmh-de-thi-mat-ma-2021-trac-nghiem-39 | de-thi-mat-ma-2021-trac-nghiem / 39 | D | — | A đúng; B quá ngắn để phân biệt agreement/transport và C chỉ là mô hình TA. D là cách hiểu kỳ vọng của môn nhưng không là kết luận duy nhất từ định nghĩa chuẩn. |
| nmmmh-de-thi-at17-bo-1-3 | de-thi-at17-bo-1 / 3 | B | — | Tính độc lập và đối chiếu đủ A–D; chỉ B khớp. |
| nmmmh-de-thi-k16-2-4 | de-thi-k16-2 / 4 | C | — | Thiếu điều kiện bảo vệ digest cho hàm băm; MAC và chữ ký đều là đáp án đúng độc lập. Slide p15 cho danh sách C nếu hỏi bộ kỹ thuật đầy đủ, nhưng đề không nêu cách chọn này. |
| nmmmh-de-thi-k16-2-13 | de-thi-k16-2 / 13 | B | — | B chắc chắn sai. D thiếu ngữ cảnh toàn bộ thông điệp hay khối lặp và phát biểu quá tuyệt đối khi đổi khóa; không ép một đáp án cho câu mơ hồ. |
| nmmmh-de-thi-k16-2-22 | de-thi-k16-2 / 22 | — | D | Tính độc lập và đối chiếu đủ A–D; chỉ D khớp. |
| nmmmh-de-thi-k16-2-36 | de-thi-k16-2 / 36 | D | — | A và B là các khía cạnh chuẩn; C,D theo mục tiêu rộng của Slide 138. Thiếu định nghĩa chọn giữa nghĩa rộng và nghĩa bảo đảm chuẩn. |
| nmmmh-de-thi-k16-3-2022 | de-thi-k16-3 / 2022 | D | C | Affine: 12a+b ≡ 14, 20a+b ≡ 12 (mod26); thử đủ A–D, chỉ (a,b)=(3,4), nhãn C, khớp cả hai cặp. |
| nmmmh-de-thi-k16-3-2027 | de-thi-k16-3 / 2027 | — | D | Tính độc lập và đối chiếu đủ A–D; chỉ D khớp. |
| nmmmh-de-thi-k16-3-2038 | de-thi-k16-3 / 2038 | C | — | B là mô tả chuẩn của xác thực bản tin. C là các mục tiêu rộng trong Slide 138. Đề không nêu nghĩa nào, nên giữ mơ hồ thay đổi khóa từ một cách đọc sang cách khác. |
| nmmmh-de-thi-k16-3-2045 | de-thi-k16-3 / 2045 | A | — | A sai khi mã lại cùng toàn bộ thông điệp, nhưng lời 'cùng khối' có thể nói các khối lặp trong chuỗi CBC. Các lựa chọn còn lại đúng trong mô hình đầy đủ khối. |
| nmmmh-de-thi-k16-3-2056 | de-thi-k16-3 / 2056 | C | — | Sau override, C sai vì các biểu thức cùng một lớp không phải các lớp khác nhau; D sai do loại số dư 0. A,B đúng. C+D sai: đáp án C đơn không còn hợp lệ. |

## Câu cần rà soát

Danh sách đầy đủ nằm tại [MANUAL_REVIEW.md](MANUAL_REVIEW.md) và `../needs_review.json`. Không dùng nhãn “verified” cho các câu này.

Cần bổ sung: ảnh AT17 câu 3 không có con trỏ che; nguồn định nghĩa `f(n)` ở K16-2 câu 11; quy ước ký hiệu (21/235) ở K16-3 câu 2052; đáp án/đính chính chính thức cho câu nhiều phương án, không phương án hoặc lời văn mơ hồ. Không sửa số liệu gốc để cứu đáp án.

## Kiến trúc và chức năng

Không đổi stack: HTML/CSS/JavaScript static, cùng máy chấm/lịch sử. Mỗi đề chỉ có một JSON chuẩn; `chapter_ids` là metadata bổ sung, các chế độ dùng cùng đối tượng câu hỏi. Không nhúng câu hỏi vào HTML/JS. Công thức KaTeX 0.16.22 phục vụ từ `vendor/`, không phụ thuộc CDN; dữ liệu gốc đọc được giữ cùng `display_blocks`. Ảnh không base64, có hộp phóng to bằng bàn phím/cảm ứng.

Luyện một/nhiều chương, lọc đề/trạng thái, số câu tùy chọn/toàn bộ; trộn câu và trộn phương án bằng ID gốc. Câu “tất cả” hoặc tham chiếu nhãn giữ thứ tự phương án. Gợi ý không tự hiện đáp án; giải thích có nút riêng. Thi chỉ chấm sau nộp. Lượt đang làm lưu riêng `nmmmh-active-session-v1`; reload giữ câu/đáp án/thứ tự. Xem lại bài đã nộp không ghi thêm lịch sử. Một lần làm một câu không bị đếm thêm khi đổi phương án.

Lịch sử cũ không bị xóa hoặc tự chấm lại theo khóa mới. Bài đang làm có chữ ký dữ liệu; khi nguồn/khóa thay đổi, bản lưu cũ không được khôi phục và chấm nhầm.

## Nguồn học thuật dùng kiểm chứng

- [Handbook of Applied Cryptography — chương 2](https://cacr.uwaterloo.ca/hac/about/chap2.pdf): số học/nhóm/trường.
- [HAC — chương 8](https://cacr.uwaterloo.ca/hac/about/chap8.pdf): RSA, Rabin, ElGamal, Merkle–Hellman; phân biệt cơ sở thiết kế lịch sử với bảo đảm an toàn.
- [HAC — chương 9](https://cacr.uwaterloo.ca/hac/about/chap9.pdf): hàm băm và xác thực.
- [HAC — chương 11](https://cacr.uwaterloo.ca/hac/about/chap11.pdf): chữ ký số.
- [NIST FIPS 197](https://csrc.nist.gov/pubs/fips/197/final): AES.
- [NIST SP 800-38A](https://csrc.nist.gov/pubs/sp/800/38/a/final): các chế độ mã khối.

## Đường dẫn ba màn hình làm bài

- [Cả đề](https://chaamsthan.github.io/ktmt-quiz/#subject=nmmmh&exam=de-thi-nmmmh&chapter=all&action=start)
- [Chương trong một đề](https://chaamsthan.github.io/ktmt-quiz/#subject=nmmmh&exam=de-thi-nmmmh&chapter=2&action=start)
- [Chương của tất cả đề](https://chaamsthan.github.io/ktmt-quiz/#subject=nmmmh&exam=all&chapter=2&action=start)
- [Luyện một/nhiều chương và lọc số câu](https://chaamsthan.github.io/ktmt-quiz/#subject=nmmmh)

Các hash tương tự dùng tại https://chaamsthan.github.io/ktmt-quiz/ sau khi push/deploy. Trạng thái triển khai và commit được ghi riêng ở DEPLOYMENT.json; không coi kiểm thử local là kiểm thử public.

## Backup và rollback

Snapshot trước sửa: commit `98123eba5e1247c1ac57758039c05dc9cad76451`. Bản sao bền vững trong thư mục tài liệu gốc: `NMMMH_AUDIT_20261021/backups/web-before-98123eb.tar.gz` và `source-before-20261021.tar.gz`; bản sao phiên còn ở `/tmp/nmmmh-upgrade-backup-RFhpyA/`. Không ghi đè PDF/DOCX, bộ nguồn DAPAN_KIEMCHUNG hay file user `extract_questions.py`.

Các sửa đổi dùng overlay `approved_changes.json`, tái nhập có kiểm tra old/new chính xác. Không chạy importer cũ bỏ qua overlay vì sẽ phục hồi khóa sai. Xem README để tái tạo và kiểm thử. Không thực hiện rollback hoặc xóa đề khác. Người dùng đã xác nhận cho commit/push sau khi kiểm thử đạt.
