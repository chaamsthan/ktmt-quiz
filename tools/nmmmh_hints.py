#!/usr/bin/env python3
"""Export curated, answer-free NMMMH hints; never mutate source question banks.

Run: python tools/nmmmh_hints.py --require-complete
Optional: --check-excluded-source /path/to/nmmmh/DAPAN_KIEMCHUNG validates
K16-1 hints in memory only. Export always contains published questions only.
Integration: JSON ``hints`` is an id -> string mapping; ``hint_for(q)`` is pure.
Unknown IDs raise KeyError, never receive an unrelated generic hint.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]

# Curated after reading stems, all four choices and answer_audit/proof data.
# Reuse is by identical task AND inputs, independent of option ordering/key.
TEXT = {
    "orders37": r"Với từng số 18, 10, 13, 4, thử các ước dương tăng dần của \(37-1\)." "\n"
        r"Dừng khi \(a^d\equiv1\pmod{37}\); so sánh số mũ nhỏ nhất của từng số, không so sánh giá trị a.",
    "rsa_decrypt": r"Tách môđun của phép mã/giải mã khỏi môđun dùng để tìm số mũ nghịch đảo." "\n"
        r"Viết hai phép biến đổi liên tiếp để kiểm tra có khôi phục thông điệp trong \(\mathbb Z_n\) không.",
    "hill_monday": r"Dùng A=0,…,Z=25; chia MONDAY và OSSNOA thành các cặp liên tiếp." "\n"
        r"Thử vectơ hàng MO nhân từng ma trận mod 26, so với OS; ma trận còn lại phải khớp cả ND và AY.",
    "rsa_related": "Gắn mỗi hệ trong bốn lựa chọn với bài toán khó của nó.\nĐối chiếu với thao tác tìm các thừa số nguyên tố của môđun RSA, đừng chỉ dựa vào việc đều dùng khóa công khai.",
    "roles": "Lập hai hàng: truyền tin mật và ký thông điệp; ghi ai cần giữ bí mật, ai cần kiểm tra.\nVới phát biểu ghép nhiều kỹ thuật, kiểm tra riêng khả năng đọc nội dung và khả năng xác minh nguồn gốc.",
    "affine19": r"Thử từng cặp \((a,b)\) vào \(19a+b\equiv9\pmod{26}\), rồi \(4a+b\equiv16\pmod{26}\)." "\n"
        r"Chỉ giữ cặp thỏa cả hai và có \(\gcd(a,26)=1\); không cần giải hệ từ đầu.",
    "mix21": "Chỉ số ảnh bắt đầu từ 0: x₂₁ lấy hàng thứ ba của ma trận hằng và cột thứ hai (EB,93,C7,20).\nNhân từng byte trong GF(2⁸), dùng xtime cho hệ số 02, xtime XOR byte cho 03, rồi XOR bốn tích.",
    "elgamal149": r"Với p=211, α=149, a=103, k=79, m=85: phân biệt số mũ lưu lâu dài và số dùng cho một lần mã." "\n"
        r"Kiểm từng phát biểu bằng \(\beta=\alpha^a,\ \gamma=\alpha^k,\ \delta=m\beta^k\pmod p\); giải mã thử bằng \(\delta\gamma^{-a}\).",
    "count693": r"Phân tích 693 trước; kiểm tra môđun có dạng \(2,4,\ell^t,2\ell^t\) với ℓ nguyên tố lẻ, t≥1 không." "\n"
        r"Chỉ khi nhóm nhân cyclic mới dùng công thức đếm \(\varphi(\varphi(n))\); không áp dụng máy móc cho mọi n.",
    "knapsack1653": "Với từng chuỗi bit, cộng các số ở vị trí bit 1 trong (33,74,157,316,620,1230,2460), so với 1653.\nHoặc trừ tham lam từ số lớn nhất không vượt phần dư; ghi bit theo thứ tự dãy ban đầu.",
    "sbox_affine": r"Trong \(y=Ax^{-1}+c\), tách phép nghịch đảo trên trường khỏi phép biến đổi affine trên các bit." "\n"
        "Kiểm xem một byte đầu vào đổi sẽ tác động tới bao nhiêu byte đầu ra ngay tại SubBytes; dùng đó để xét phát biểu về khuếch tán.",
    "aes_layers": "Liệt kê đầu vào/đầu ra của SubBytes, ShiftRows, MixColumns: bước nào tác động một byte, bước nào trộn vị trí hoặc nhiều byte?\nĐối chiếu từng tên bước với vai trò mà phát biểu gán cho nó.",
    "shannon_aes": "Trong AES, tách bước tác động một byte khỏi bước đổi vị trí và trộn nhiều byte; trong DES, xem S-box thay giá trị hay chỉ đổi chỗ.\nDùng các thao tác cụ thể ấy kiểm cách từng phát biểu gán tên xáo trộn/khuếch tán, đặc biệt phát biểu đảo phép thế và hoán vị.",
    "euclid": r"Bắt đầu từ hàng có a=61, b=2; dùng \(q=\lfloor a/b\rfloor,\ r=a-qb\), rồi cập nhật hai cặp hệ số." "\n"
        r"Kiểm dấu bằng bất biến \(1120x+311y=r\), và phân biệt hệ số vừa tính với hệ số dịch sang hàng kế.",
    "hill_friday": r"Mã chữ A=0,…,Z=25; tách FRIDAY→FR, ID, AY và ADDHOM→AD, DH, OM." "\n"
        "Thử vectơ hàng FR nhân từng khóa mod 26; chỉ cần một tọa độ sai để loại, rồi kiểm hai cặp còn lại.",
    "gf_a9": r"Ở đây cần nhân 03 với A9, không chỉ gọi xtime một lần: dùng \(03\cdot u=\operatorname{xtime}(u)\oplus u\)." "\n"
        "Dịch A9 trái một bit; nếu bit cao ban đầu là 1 thì XOR 1B, giữ 8 bit, rồi XOR lại A9.",
    "residues17": r"Với 11 mod 17, dùng tiêu chuẩn Euler \(11^{(17-1)/2}\pmod{17}\); với phân số mẫu hợp số, tính Jacobi." "\n"
        "Bình phương lại từng căn được nêu mod 21; kiểm riêng công thức cho (2/n) với n lẻ.",
    "modes": r"Viết \(P_i=D_K(C_i)\) cho ECB, rồi thử thay một khối mã: công thức khối kế có dùng khối bị thay không?" "\n"
        "Với CBC chỉ so sánh khi cùng tiền tố bản rõ, khóa và IV; với OFB theo dõi chuỗi khóa sinh từ IV.",
    "authentication": "Lập ba tình huống: nội dung bị sửa, giả người gửi, người gửi phủ nhận đã gửi.\nĐối chiếu phạm vi xác thực trong học phần với từng tình huống; lựa chọn tổng hợp phải bao quát đủ, không chỉ đúng một phần.",
    "generators41": r"Với mỗi ứng viên g, thử \(g^{(41-1)/r}\pmod{41}\) cho từng ước nguyên tố r của 41−1." "\n"
        "Nếu có phép thử ra phần tử đơn vị thì loại g khỏi tập phần tử sinh; đề hỏi phần tử KHÔNG sinh.",
    "elgamal41_117": r"Với p=211, α=41, a=117, k=33, m=56, tính riêng \(\beta=\alpha^a,\gamma=\alpha^k,\delta=m\beta^k\pmod p\)." "\n"
        r"Thử giải mã \(\delta\gamma^{-a}\); đừng đổi vị trí γ,δ hoặc nhầm a với k. Kiểm từng phát biểu, có thể không chỉ một phát biểu đúng.",
    "inverse": "Trong mỗi biểu thức, xác định tích đang trả về phần tử ban đầu hay phần tử trung hòa.\nThử yêu cầu: thực hiện phép toán với một phần tử rồi với nghịch đảo của nó phải triệt tiêu tác động ban đầu.",
    "congruences7zero": "Thử phép chia hết để kiểm điều kiện về số dư.\nVới −7, 0, 7, 14, xét hiệu từng cặp có chia hết cho 7 không; phân biệt nhiều đại diện với nhiều lớp đồng dư. Kiểm từng phát biểu độc lập.",
    "des110101": "Với 110101, ghép bit đầu và cuối để xác định hàng; bốn bit giữa xác định cột của S₁, đều đếm từ 0.\nTra đúng ô trên ảnh, đổi giá trị ô thành 4 bit rồi so với từng lựa chọn.",
    "phi969": r"Phân tích 969 thành thừa số nguyên tố, rồi dùng \(\varphi(n)=n\prod_{\ell\mid n}(1-1/\ell)\)." "\n"
        "Mỗi thừa số nguyên tố chỉ xuất hiện một lần trong tích; ước lượng trước kết quả phải nhỏ hơn 969 để loại nhiễu.",
    "log17_15": r"Thay từng số mũ t trong lựa chọn vào \(17^t\bmod97\), so với 15." "\n"
        "Lập vài bình phương liên tiếp của 17 để tái sử dụng; không cần lập bảng logarit toàn nhóm.",
    "des_keys": "Đánh dấu riêng bước bỏ bit kiểm tra chẵn lẻ, chia đôi khóa và chọn bit tạo khóa vòng.\nĐối chiếu lịch dịch từng vòng với bảng DES, đặc biệt các vòng 6, 8, 9; một vòng bị ghi sai đủ loại cả phát biểu.",
    "ecc_encrypt2": r"Bản mã gồm hai điểm \((kG,\ P_M+kP_A)\), không phải cặp điểm có sẵn bất kỳ trong đề." "\n"
        "Với k=2, G=(7,2), nhân đôi G; cộng (3,6) với (10,2) trên đường cong mod 11, rồi so sánh đủ hai thành phần.",
    "knapsack_good": "Với (15,47,67,130,287), so từng số với tổng TẤT CẢ số đứng trước, không chỉ số liền trước.\nĐếm số tập con khi vét cạn và số lần xét phần tử khi chọn tham lam trên dãy siêu tăng; kiểm từng mệnh đề.",
    "tonelli75": r"Với a=75, p=97, b=5: tách \(p-1=2^s t\), t lẻ; khởi tạo c,r đúng công thức trên ảnh." "\n"
        "Chạy riêng i=1: tính d từ r cũ; chỉ sửa r nếu d≡−1, nhưng luôn bình phương c. So bộ ba sau cập nhật.",
    "coprime": "Dùng Euclid cho (117,391), (391,153), (85,187), (85,255): thay (u,v) bằng (v,u mod v) tới khi số dư bằng 0.\nSo ước chung cuối cùng với đơn vị; đừng chọn theo việc hai số đều lẻ hoặc không cùng chia hết cho số nhỏ.",
    "cyclic": "Viết riêng định nghĩa nhóm cyclic, định lý Lagrange về bậc phần tử và tiêu chuẩn một phần tử sinh toàn nhóm.\nTrong nhóm nhân đơn vị, xác định bậc nhóm trước khi đối chiếu các công thức có φ(n).",
    "order17_20": r"Thử từng số mũ t trong lựa chọn bằng \(17^t\pmod{20}\); số mũ cho đơn vị còn phải là nhỏ nhất dương." "\n"
        r"Có thể bắt đầu từ các ước của \(\varphi(20)\); loại các số mũ lớn khi đã có số mũ nhỏ hơn thỏa mãn.",
    "private_encrypt": "Tưởng tượng ai cũng có khóa công khai: nếu dữ liệu được biến đổi bằng khóa riêng, những ai có thể thực hiện phép ngược?\nDùng thử nghiệm đó để tách mục tiêu truyền tin mật khỏi ký; kiểm tiếp định nghĩa khóa chung của mã đối xứng.",
    "hash_length": "Giữ nguyên một thuật toán băm rồi thay thông báo rất ngắn bằng thông báo rất dài: độ dài đầu ra có đổi theo không?\nXét thêm việc nhiều đầu vào có thể cùng đầu ra; phân biệt khó tính tiền ảnh với một phép giải mã.",
    "ca_all": "Vẽ ba vai: thực thể đăng ký, bên phát hành chứng thư, người kiểm tra chứng thư.\nĐối chiếu từng phát biểu với việc nộp khóa công khai, gắn danh tính và ký xác nhận; kiểm riêng từng mệnh đề trước lựa chọn tổng hợp.",
    "ca_not": "Tách chủ thể được ghi tên trong chứng thư khỏi chủ thể phát hành chứng thư.\nHỏi người kiểm tra phải tin khóa công khai của ai để kiểm chữ ký trên chứng thư; từ đó xét bên giữ khóa ký tương ứng.",
    "gcd_max": "Chạy Euclid cho từng cặp ở bốn lựa chọn, ghi ước chung cuối cùng ngay bên cạnh.\nSo các ước chung, không so kích thước hai số đầu vào; có thể lọc nhanh bằng chia hết trước khi tính tiếp.",
    "rsa_exponent": r"Viết điều kiện để d là nghịch đảo của e: \(ed\equiv1\) theo môđun nào?" "\n"
        "Dùng điều kiện tồn tại nghịch đảo để rà cả phát biểu về gcd lẫn cách tìm d; đừng đồng nhất môđun thông điệp với môđun số mũ.",
    "public_claims": "Xét một hệ lai dùng khóa công khai để trao khóa phiên, rồi mã đối xứng cho dữ liệu dài.\nDùng mô hình ấy kiểm từ “thay thế”; kiểm riêng “đã được chứng minh” có mạnh hơn giả thiết độ khó không. Câu chữ cần đối chiếu nguồn.",
    "rabin1234": r"Tự tính \(n=199\cdot211\), rồi \(c=1234^2\bmod n\); so từng phát biểu với cùng bộ dữ kiện." "\n"
        "Bình phương lại từng căn được nêu; nếu một phát biểu đổi bản rõ sang 1731 thì phải kiểm phép mã mới, không dùng lại c cũ.",
    "rsa_signature": r"Với p=31, q=23, d=223, m=439: tách \(n=pq\) và \(\varphi(n)=(p-1)(q-1)\)." "\n"
        r"Tìm e nghịch đảo d mod φ(n); kiểm từng phát biểu bằng \(s=m^d\bmod n\) và \(s^e\bmod n\). Chú ý môđun, số mũ và đại lượng nào được công khai.",
    "ecc3_2_7": r"Tính \(P_A=3G=2G+G\) với G=(2,7), mod 11; không nhân tọa độ trực tiếp với 3." "\n"
        r"Nhân đôi dùng \(\lambda=(3x_G^2+1)(2y_G)^{-1}\); cộng hai điểm khác nhau dùng hệ số góc tương ứng, rồi thay ngược kiểm đường cong.",
    "key_management": "Phân biệt ba câu hỏi: khóa thuộc về ai, hai bên tạo bí mật chung thế nào, cơ quan tin cậy quản lý khóa ra sao.\nGhép từng phát biểu với đúng câu hỏi; khi truyền tin mật và khi ký, xác định riêng chủ thể sở hữu khóa cần chứng thực.",
    "hash_properties": "Trong từng định nghĩa, khoanh dữ kiện đã được cho: một digest, một thông báo hay chưa cho cả hai.\nRồi kiểm mục tiêu cần tìm và dấu so sánh giữa hai giá trị băm; một dấu sai đủ làm hỏng mệnh đề.",
    "rc4": r"Bắt đầu S[i]=i và j=0; làm cả vòng i=0 trước, với T[0]=13." "\n"
        r"Sang i=1, dùng j và mảng S đã đổi, tính \(j\leftarrow(j+S[i]+27)\bmod256\), rồi mới swap; không đặt lại j.",
    "des_p": r"Trải C thành 32 bit theo hàng, đánh số từ 1; mỗi ô j của đầu ra lấy \(C_{P_j}\), không đảo chiều bảng P." "\n"
        "Chỉ tra các ô dấu ? rồi đọc chúng từ trên xuống, trái sang phải; nếu bản chữ và ảnh lệch nhau, đối chiếu ảnh trước khi loại phương án.",
    "pow27_101": r"Viết 101 ở hệ nhị phân; theo bảng đang xét bit thấp trước, bình phương cơ số mod 211 sau mỗi bước." "\n"
        "Chỉ nhân bộ tích lũy khi bit đang xét là 1; với cơ số 27, kiểm từng ô theo quan hệ với hàng trước, không chỉ ô cuối.",
    "shannon": "Thử tách hai thao tác: thay giá trị ký hiệu và đổi vị trí ký hiệu.\nVới mỗi thao tác, hỏi nó che quan hệ khóa–bản mã hay lan ảnh hưởng của dữ liệu; đối chiếu cách gán tên xáo trộn/khuếch tán trong từng phát biểu.",
    "merkle361254": r"Đặt dãy riêng là b; ứng viên khóa công khai phải thỏa \(a_i=635b_{\pi(i)}\bmod737\)." "\n"
        "Với π=(3,6,1,2,5,4), thử vị trí mà các lựa chọn khác nhau trước; phân biệt b ở vị trí π(i) với đưa phần tử thứ i tới vị trí π(i).",
    "autokey_sun_squid": "Bỏ khoảng trắng trong SQUID GAME, dùng A=0,…,Z=25; viết SUN rồi nối tiếp bằng bản rõ để đủ khóa.\nThử giải ngược từng chuỗi theo phép trừ mod 26; đặc biệt kiểm từ ký tự thứ tư, nơi khóa không còn là mầm ban đầu.",
    "stream": "Với từng phát biểu, hỏi mã dòng xử lý đơn vị dữ liệu nào và phần nào tạo chuỗi khóa.\nThử đối chiếu với OFB tạo chuỗi khóa từ mã khối; việc có thêm một loại mã có đồng nghĩa thay thế loại cũ để tăng an toàn không?",
    "dh": r"Thử từng ứng viên K bằng phép tính độc lập \(10^{5\cdot8}\bmod541\)." "\n"
        r"Hoặc tính hai khóa công khai rồi kiểm \((10^5)^8\) và \((10^8)^5\) cùng môđun; không cộng hai số mũ bí mật.",
    "integrity": "Giả sử kẻ tấn công sửa cả thông báo lẫn dữ liệu kiểm tra: kỹ thuật nào cần khóa hoặc một giá trị đối chiếu đáng tin?\nXét riêng từng kỹ thuật được nêu và phạm vi “hỗ trợ toàn vẹn” trong slide; lựa chọn chỉ liệt kê một kỹ thuật có đầy đủ không?",
    "order13_20": r"Thế từng số mũ t vào \(13^t\bmod20\), bắt đầu từ t nhỏ nhất." "\n"
        r"Cấp là số mũ dương đầu tiên cho đơn vị, không phải giá trị lũy thừa; kiểm thêm nó phải chia \(\varphi(20)\).",
    "mix33": "Ảnh đánh số từ 0: x₃₃ dùng hàng thứ tư của ma trận hằng và cột thứ tư (A0,C0,30,2B).\nNhân từng byte trong GF(2⁸) rồi XOR; hệ số 03 là xtime(byte) XOR byte. Nếu hình bị cắt hàng trên, đối chiếu bản nguồn đầy đủ.",
    "hash_random": "Thử băm cùng một thông báo hai lần với cùng thuật toán; so tính xác định với tính chất được mô hình hóa như ngẫu nhiên.\nVới mô tả tiền ảnh thứ hai, chỉ rõ x đã cho hay chưa và x′ phải thỏa điều kiện nào; đừng bỏ qua câu chữ mơ hồ.",
    "tonelli37": r"Với a=37, p=41, b=3: phân tích \(p-1=2^s t\), t lẻ, rồi khởi tạo c,r theo Thuật toán 4." "\n"
        "Tại i=1 dùng r cũ tính d; chỉ nhân r với c khi d≡−1, nhưng luôn bình phương c. So bộ ba SAU vòng lặp, không phải trạng thái đầu.",
    "generator73": r"Tính \(73-1\), phân tích các ước nguyên tố r; g chỉ sinh nhóm nếu mọi \(g^{(73-1)/r}\not\equiv1\pmod{73}\)." "\n"
        "Kiểm ứng viên theo thứ tự giá trị tăng dần, không theo thứ tự phương án; nếu cần khẳng định nhỏ nhất, kiểm cả số nhỏ hơn chưa có trong lựa chọn.",
    "hill_inverse": "Đề hỏi khóa GIẢI mã: tách ADDHOM thành cặp, thử vectơ hàng AD nhân từng ma trận mod 26 để khôi phục FR.\nKiểm tiếp hai cặp còn lại; các ma trận nằm trong bảng phương án, không chỉ ở trường chữ “k =”.",
    "rsa_f_notation": r"Tách môđun thông điệp khỏi môđun cần cho \(ed\equiv1\); kiểm điều kiện tồn tại nghịch đảo." "\n"
        "Nếu nguồn ghi f(n), xác nhận ký hiệu ấy có được định nghĩa là φ(n) không trước khi đánh giá; không tự coi f(n) là n hay tự sửa nguồn.",
    "ecc3_7_2": r"Tính \(P_A=3G=2G+G\) với G=(7,2) trên mod 11." "\n"
        r"Nhân đôi dùng \(\lambda=(3x_G^2+1)(2y_G)^{-1}\); cộng G lần nữa, rút gọn sau mỗi phép toán và thử điểm thu được vào đường cong.",
    "affine12_13": r"Thử \((a,b)\) của từng lựa chọn vào \(12a+b\equiv14\) và \(13a+b\equiv17\pmod{26}\)." "\n"
        "Dùng đúng cặp M(12)→O(14), N(13)→R(17) từ nguồn; kiểm cả hai cặp và tính khả nghịch của a thay vì chỉ thử một chữ.",
    "log19_12": r"Thử trực tiếp \(19^t\bmod53\) với t lấy từ từng lựa chọn, so với 12." "\n"
        "Tách t thành tổng các lũy thừa của 2 để tái dùng bảng bình phương, không cần tìm logarit bằng vét cạn cả nhóm.",
    "residues97": r"Kiểm 5 và 47 bằng tiêu chuẩn Euler \(a^{(97-1)/2}\pmod{97}\)." "\n"
        "Bình phương từng căn được nêu mod 15; công thức (2/n) cần n lẻ và chỉ phụ thuộc n mod 8. Kiểm hết các mệnh đề trước khi chọn SAI.",
    "cyclic_count": r"Nếu nhóm cyclic có bậc h, viết phần tử của nó thành \(g^k\); khi nào \(g^k\) vẫn có bậc h?" "\n"
        "Đếm các số mũ k phù hợp trong một chu kỳ, rồi thay h bằng bậc nhóm đơn vị; đừng nhầm số phần tử với số phần tử sinh.",
    "gf_af": r"Tách \(03\cdot AF=(02\cdot AF)\oplus AF\) trong trường AES." "\n"
        "Để nhân 02, dịch trái giữ một byte; nếu bit cao của AF là 1 thì XOR 1B trước khi XOR lại AF. So với lựa chọn ở dạng nhị phân.",
    "des101010": "Với B₁=101010, lấy hai bit ngoài làm chỉ số hàng, bốn bit giữa làm chỉ số cột của S₁; đếm từ 0.\nTra ô và đổi thành đúng 4 bit. Tên “SubBytes” trong thân không thay quy tắc tra hộp S₁ của DES.",
    "generators97": r"Với mỗi g trong 10, 2, 29, 5, kiểm \(g^{(97-1)/r}\pmod{97}\) cho mọi ước nguyên tố r của 97−1." "\n"
        "Một phép thử cho đơn vị là đủ chứng tỏ g không sinh nhóm; đề yêu cầu phần tử KHÔNG sinh, không phải bậc cụ thể.",
    "congruences7one": "Với −6, 1, 8, 15, xét hiệu hai số liên tiếp và phần dư khi chia cho 7 để phân biệt lớp với đại diện.\nKiểm riêng điều kiện số dư bằng một phép chia hết; nhiều phát biểu có thể cùng sai.",
    "shannon_ambiguous": "Dùng hai thao tác thay giá trị và đổi vị trí để kiểm cách gán tên xáo trộn/khuếch tán.\nXét riêng câu “thực hiện trên bit”: nó mô tả cách biểu diễn hay một định nghĩa? Câu chữ này cần đối chiếu nguồn trước khi chốt duy nhất.",
    "elgamal41_113": r"Với p=211, α=41, a=113, k=67, m=56: tính \(\beta=\alpha^a,\gamma=\alpha^k,\delta=m\beta^k\pmod p\)." "\n"
        "Đánh giá từng khẳng định độc lập, phân biệt khóa riêng lâu dài với ngẫu nhiên từng lần; lựa chọn tổng hợp chỉ đúng khi mọi thành phần đúng.",
    "ecc_encrypt3_3_5": r"Dùng cấu trúc \((kG,\ P_M+kP_{\rm Pub})\) với k=3, G=(2,7), mod 11." "\n"
        "Tính 2G+G cho điểm thứ nhất; điểm thứ hai chỉ cần cộng (3,5) với (7,9). Thử ngược cấu trúc từng cặp lựa chọn.",
    "cia": "Gạch chân “mọi người dùng”, “không một ai” trong các lựa chọn; thử trường hợp người được cấp quyền đọc hoặc sửa hợp lệ.\nĐối chiếu từng định nghĩa với điều kiện trái phép và ba mục tiêu bí mật, toàn vẹn, khả dụng.",
    "rabin1731": r"Tính lại \(n=199\cdot211\) trước, rồi \(c=1731^2\bmod n\); tránh dùng môđun in sẵn làm dữ kiện đúng." "\n"
        "Kiểm các căn bằng bình phương mod n; với hệ số ghép CRT, kiểm quan hệ Bézout tương ứng với thứ tự p,q trong thuật toán.",
    "knapsack_bad13": "Kiểm dãy (13,42,57,123,234) bằng tổng tích lũy các phần tử trước, đặc biệt ở phần tử cuối.\nVới tổng 344 và dãy (12,13,33,60,120,240,480), kiểm khả năng biểu diễn bằng các bit 0/1; đánh giá riêng hai phát biểu độ phức tạp.",
    "phi765": r"Theo nguồn đã đối chiếu, đầu vào là 765: phân tích thừa số rồi dùng \(\varphi(n)=n\prod_{\ell\mid n}(1-1/\ell)\)." "\n"
        "Nhớ xử lý lũy thừa của cùng một số nguyên tố; thử đối chiếu tích chưa rút gọn với các lựa chọn và kiểm đúng đầu vào trên ảnh.",
    "agreement_scope": "Tách thuật toán thực hiện trao đổi khỏi loại khóa mà hai bên thu được.\nThử dùng Diffie–Hellman làm ví dụ cho phát biểu “chỉ áp dụng”; phân biệt điều đó với TA quản trị khóa và chứng thực danh tính khóa.",
    "pow41_101": "Viết 101 dạng nhị phân và đọc bit thấp trước theo bảng; với cơ số 41, bình phương A mod 211 ở mỗi cột.\nChỉ nhân b với A khi bit tương ứng là 1; dùng giá trị b của cột trước, không giữ nguyên mọi cột cuối.",
    "affine12_20": r"Thế từng khóa vào \(12a+b\equiv14\) và \(20a+b\equiv12\pmod{26}\)." "\n"
        "Chỉ cần một đồng dư sai để loại, nhưng phải thử cả hai nếu đồng dư đầu đúng; đừng bỏ phần dịch b.",
    "units235": r"Thử \(\gcd(u,235)\) với từng u trong 42,44,43,45." "\n"
        "Điều kiện thuộc nhóm nhân là có nghịch đảo môđun, không phải chỉ nằm giữa 1 và 234; đề hỏi phần tử KHÔNG thuộc nhóm.",
    "hill_objzma": "Chia FRIDAY thành FR, ID, AY và OBJZMA thành OB, JZ, MA, quy ước A=0,…,Z=25.\nThử vectơ hàng FR nhân từng ma trận mod 26; ma trận qua phép thử đầu phải tiếp tục khớp hai cặp sau.",
    "public_private": "Lập bảng người nắm từng loại khóa trong hai mô hình đối xứng và khóa công khai.\nThử phát biểu có từ “tất cả” bằng trường hợp một người lạ biết cả hai thành phần của cặp khóa: mục tiêu bí mật còn giữ được không?",
    "hash_encrypt": "Với mỗi kỹ thuật, hỏi người nhận có bước dùng khóa để khôi phục nguyên thông báo hay chỉ kiểm một digest.\nKiểm riêng ba mục tiêu tìm tiền ảnh, tiền ảnh thứ hai và va chạm; đừng đánh đồng chúng với mã hóa có giải mã.",
    "mix13": "Chỉ số bắt đầu từ 0: x₁₃ dùng hàng thứ hai của ma trận hằng và cột thứ tư (A0,C0,30,2B).\nTính tích vô hướng trong GF(2⁸): cộng bằng XOR, nhân 03 bằng xtime XOR byte; không nhân/cộng như số nguyên thông thường.",
    "generators41_alt": r"Nhóm nguồn là \(\mathbb Z_{41}^{*}\): với g trong 9,13,24,19, kiểm \(g^{(41-1)/r}\pmod{41}\) cho các ước nguyên tố r của 41−1." "\n"
        "Một số mũ thử cho đơn vị đủ loại khả năng sinh; đọc đúng môđun của nhóm trên nguồn đã đối chiếu.",
    "orders21": r"Với a trong 8,4,10,5, thử các ước dương d của \(\varphi(21)\), tìm d nhỏ nhất sao cho \(a^d\equiv1\pmod{21}\)." "\n"
        "So bốn số mũ thu được; phần tử có giá trị nhỏ nhất không nhất thiết có bậc nhỏ nhất.",
    "autokey_crypto": "Viết SUN rồi nối bằng CRYPTOGRAPHY để có khóa chạy đủ độ dài; mã chữ từ A=0 và cộng mod 26.\nThử giải từng lựa chọn, đặc biệt từ ký tự thứ tư. Nếu không khớp, kiểm quy ước Autokey trong slide, không tự đổi sang SUN lặp.",
    "des110001": "Với 110001, hai bit ngoài chọn hàng, bốn bit giữa chọn cột S₁, đều đếm từ 0.\nTra bảng S₁ đủ bốn hàng rồi đổi giá trị thành 4 bit; nếu hình đang hiển thị câu khác, cần đối chiếu bảng đầy đủ từ nguồn.",
    "ecc2_2_7": r"Với G=(2,7), cần nhân đôi điểm trên \(y^2=x^3+x+6\pmod{11}\), không nhân đôi từng tọa độ." "\n"
        r"Tính \(\lambda=(3x_G^2+1)(2y_G)^{-1}\pmod{11}\), rồi \(x'=\lambda^2-2x_G,\ y'=\lambda(x_G-x')-y_G\); thử điểm vào đường cong.",
    "merkle452163": r"Với π=(4,5,2,1,6,3), kiểm từng ứng viên bằng \(a_i=635b_{\pi(i)}\bmod737\), b là dãy riêng trong đề." "\n"
        "Chọn vị trí mà các ứng viên khác nhau để thử trước; nếu hai dãy chỉ đổi chỗ một cặp, chỉ cần kiểm cặp đó rồi xác minh toàn dãy.",
    "knapsack_bad15": "Với (15,47,67,130,240), so từng phần tử với tổng tất cả phần tử đứng trước, đặc biệt ở cuối dãy.\nTách điều kiện siêu tăng khỏi độ phức tạp vét cạn và độ phức tạp tham lam; một phần tử vi phạm đủ bác bỏ cả dãy.",
    "which_cyclic": r"Phân tích 21,50,30,35; đối chiếu dạng \(2,4,\ell^t,2\ell^t\) với ℓ là nguyên tố lẻ, t≥1." "\n"
        "Chỉ nhóm có cấu trúc cyclic mới có phần tử sinh toàn nhóm; đừng chỉ kiểm từng nhóm có phần tử khả nghịch hay không.",
    "elgamal_basis": "Viết phép tính khóa công khai của ElGamal truyền thống, rồi đặt câu hỏi khôi phục số mũ bí mật từ các tham số công khai.\nSo dạng bài toán ngược đó với bốn lựa chọn; phân biệt nhóm nhân modulo số nguyên tố với nhóm điểm elliptic.",
    "hash_oneway": "Giữ cố định thuật toán và so ba khía cạnh: độ dài digest, khả năng nhiều thông báo cùng băm, chi phí tìm đầu vào khi chỉ biết digest.\nĐọc “không có khả năng” theo nghĩa khó tính toán trong phạm vi an toàn, không theo nghĩa tuyệt đối không tồn tại tiền ảnh.",
    "pow41_117": "Với cơ số 41 và số mũ 117, đọc bit thấp trước; cập nhật A bằng bình phương mod 211, b bằng nhân có điều kiện theo bit.\nKiểm cả các cột giữa: số mũ 117 có các bit khác 101, nên không chép nguyên dòng tích lũy của bài 41¹⁰¹.",
    "phi_product": "Thử phản ví dụ m và n có chung một ước nguyên tố, rồi đối chiếu công thức φ cho lũy thừa nguyên tố.\nTrong tích các thừa số nguyên tố phân biệt, điều kiện nào giúp hai tích của m và n không đếm lặp cùng một thừa số?",
    "residues235": "Đọc đúng mẫu số trong nguồn, nhất là 235; kiểm nó có phải số nguyên tố trước khi gọi ký hiệu là Legendre.\nNếu dùng Jacobi cho mẫu hợp số, phân tích mẫu và dùng tính nhân; bình phương lại các căn mod 21, kiểm công thức (2/n) riêng.",
    "count666": r"Phân tích 666; xét điều kiện có căn nguyên thủy: môđun phải thuộc \(2,4,\ell^t,2\ell^t\), ℓ nguyên tố lẻ, t≥1." "\n"
        r"Kiểm tính cyclic trước khi dùng \(\varphi(\varphi(n))\) để đếm; không phải mọi nhóm nhân đều có phần tử sinh.",
    "not_coprime": "Dùng Euclid với (701,89), (391,15), (3765,156), (85,247); đề hỏi KHÔNG nguyên tố cùng nhau nên cần ước chung ngoài đơn vị.\nCó thể lọc bằng tính chia hết trước, nhưng phải kiểm các cặp còn lại để tránh chỉ chọn theo trực giác.",
    "gf_2f": r"Để nhân \(03\cdot2F\), dùng \(\operatorname{xtime}(2F)\oplus2F\), không chỉ dịch trái." "\n"
        "Kiểm bit cao ban đầu của 2F trước khi quyết định có XOR 1B hay không; giữ đúng 8 bit và so ở hệ nhị phân.",
    "congruences7three": "Với −11, −4, 3, 10, 17, xét hiệu từng cặp để quyết định có cùng một lớp mod 7 không.\nKiểm riêng bất đẳng thức số dư bằng phép chia hết; đừng dừng sau mệnh đề sai đầu tiên nếu đề có lỗi nhiều lựa chọn.",
    "ecc_encrypt3_10_9": r"Dùng cấu trúc \((kG,\ P_M+kP_A)\), k=3, G=(2,7), mod 11." "\n"
        "Tính 2G+G cho điểm thứ nhất; cộng (10,9) với (3,5) cho điểm thứ hai. Kiểm cả dấu tung độ trong từng phương án.",
    "log17_21": r"Thử \(17^t\bmod97\) với mỗi số mũ t trong lựa chọn và so với 21." "\n"
        "Dùng bình phương có lặp để kiểm nhanh; không lấy nghịch đảo hay đổi 21 thành số mũ của 17 theo phép logarit thực.",
    "phi1001": r"Phân tích 1001 thành thừa số nguyên tố; dùng \(\varphi(n)=n\prod_{\ell\mid n}(1-1/\ell)\)." "\n"
        "Kiểm mỗi thừa số thực sự nguyên tố và chỉ đưa vào tích một lần; đối chiếu tính chia hết của tích với các ứng viên.",
    "missing_stem": "Nguồn không có thân câu hỏi ở vị trí này.\nCần bổ sung đúng câu và các phương án từ trang gốc trước khi có thể xác định cách giải; không mượn nội dung câu liền kề.",
    "missing_ecc": "Chỉ còn vài tọa độ phương án, thiếu thân đề và dữ kiện phép toán.\nCần tìm phần đầu câu trên trang trước để biết đang tính khóa công khai hay bản mã; chưa thể chọn một công thức cụ thể.",
    "missing_roles": "Nguồn chỉ còn phần cuối các phát biểu về mã đối xứng, thiếu yêu cầu đúng/sai và các phương án đầu.\nCần bổ sung thân đề trước; không suy ra lựa chọn tổng hợp từ hai phát biểu nhìn thấy.",
    "missing_ca": "Chỉ đọc được một phát biểu về CA; các lựa chọn còn lại bị cắt.\nLập vai trò đăng ký, phát hành, kiểm chứng để chuẩn bị đối chiếu, nhưng cần đủ phương án trước khi xét lựa chọn tổng hợp.",
    "missing_shannon": "Nguồn chỉ còn một phát biểu về khuếch tán và lựa chọn tổng hợp; chưa biết đề hỏi đúng hay sai.\nCần bổ sung phần đầu câu; có thể chuẩn bị so sánh thay giá trị với đổi vị trí ký hiệu, chưa thể chốt phương án.",
    "missing_knapsack": "Chỉ thấy phát biểu độ phức tạp tham lam và lựa chọn tổng hợp, thiếu thân đề và các dữ kiện đầu.\nCần khôi phục phần còn lại để biết phải kiểm dãy siêu tăng, tổng đích hay độ phức tạp; không mặc định giống một câu khác.",
    "missing_cyclic": "Phát biểu về bậc bị cụt và chưa đủ phương án.\nChuẩn bị định nghĩa cyclic, bậc phần tử và bậc nhóm, nhưng cần nguyên văn điều kiện cùng dấu chia hết trước khi đối chiếu.",
    "missing_inverse_options": "Thân câu nói về nghịch đảo nhưng không có các phương án.\nDựa vào tác động triệt tiêu về phần tử trung hòa để nhận dạng biểu thức khi bổ sung được lựa chọn; chưa thể đối chiếu ngay.",
    "missing_affine_options": r"Nếu đúng hai cặp 19→9 và 4→16, lập \(19a+b\equiv9,\ 4a+b\equiv16\pmod{26}\)." "\n"
        "Các lựa chọn bị cắt; dùng hệ này để kiểm khóa khi bổ sung đủ nguồn, không suy ra một chữ cái từ câu tương tự.",
    "missing_rabin_options": r"Với p=199,q=211,m=1234, chuẩn bị kiểm \(n=pq\) và \(c=m^2\bmod n\)." "\n"
        "Bản này không có phương án; cần bổ sung đúng phần bị cắt, không tự sao chép lựa chọn từ câu có thân tương tự.",
    "missing_des_row": "Với B₁=110101, xác định hàng bằng hai bit ngoài và cột bằng bốn bit giữa.\nHàng cuối S₁ và các phương án đều bị cắt; cần bảng đầy đủ từ nguồn trước khi tra, không đoán giá trị ô thiếu.",
    "hill_addhcm": "Thử các khóa bằng vectơ hàng FR, ID, AY mod 26, đối chiếu lần lượt với AD, DH, CM.\nNếu không khóa nào khớp cả ba, xem lại chữ C/O trên ảnh bản mã ADDHCM; không tự đổi chữ để khớp một khóa.",
    "autokey_son": "Theo bản chữ hiện có, nối mầm SON bằng SQUIDGAME rồi cộng mod 26 với A=0.\nNếu không khớp, đối chiếu ảnh ở mầm SON/SUN và ký tự mở đầu các lựa chọn; chưa được tự sửa dữ kiện theo một đề khác.",
    "order17_29": r"Thử \(17^t\bmod29\) với từng số mũ t trong lựa chọn, theo thứ tự tăng dần." "\n"
        r"Cấp cần là số mũ dương nhỏ nhất cho đơn vị và phải chia \(29-1\); kiểm số mũ nhỏ hơn trước khi giữ một ứng viên.",
    "jacobi156": r"Kiểm \(\gcd(156,231)\) trước khi áp dụng quy tắc Jacobi; không mặc định ký hiệu chỉ có hai giá trị ±1." "\n"
        "Với 11 mod 17 dùng tiêu chuẩn Euler; bình phương lại các căn mod 21. Kiểm đủ từng khẳng định, không ép chỉ có một câu sai.",
}

EXAMS = {
    "de-thi-at17-bo-1": dict(zip(map(str, range(1, 14)), [
        "orders37", "rsa_decrypt", "hill_monday", "rsa_related", "roles",
        "affine19", "mix21", "elgamal149", "count693", "knapsack1653",
        "sbox_affine", "aes_layers", "euclid",
    ])),
    "de-thi-nmmmh": dict(zip(map(str, range(1, 41)), [
        "hill_friday", "gf_a9", "residues17", "modes", "authentication",
        "generators41", "elgamal41_117", "inverse", "congruences7zero", "des110101",
        "roles", "phi969", "log17_15", "des_keys", "ecc_encrypt2",
        "knapsack_good", "tonelli75", "coprime", "cyclic", "order17_20",
        "private_encrypt", "hash_length", "ca_all", "ca_not", "affine19",
        "gcd_max", "rsa_exponent", "public_claims", "rabin1234", "rsa_signature",
        "ecc3_2_7", "key_management", "hash_properties", "rc4", "des_p",
        "pow27_101", "shannon", "merkle361254", "mix21", "autokey_sun_squid",
    ])),
    "de-thi-mat-ma-2021-trac-nghiem": dict(zip(map(str, range(1, 41)), [
        "tonelli75", "rc4", "ca_all", "des_keys", "hash_properties",
        "order17_20", "pow27_101", "log17_15", "coprime", "des110101",
        "merkle361254", "modes", "gf_a9", "ca_not", "des_p",
        "knapsack_good", "mix21", "affine19", "ecc3_2_7", "elgamal41_117",
        "rsa_signature", "ecc_encrypt2", "authentication", "hill_friday", "inverse",
        "rabin1234", "cyclic", "generators41", "congruences7zero", "rsa_exponent",
        "phi969", "autokey_sun_squid", "gcd_max", "shannon", "private_encrypt",
        "roles", "public_claims", "hash_length", "key_management", "residues17",
    ])),
    "de-thi-k16-2": dict(zip(map(str, range(1, 41)), [
        "merkle361254", "stream", "dh", "integrity", "order13_20",
        "mix33", "hash_random", "tonelli37", "generator73", "hill_inverse",
        "rsa_f_notation", "ecc3_7_2", "modes", "gcd_max", "affine12_13",
        "roles", "log19_12", "residues97", "cyclic_count", "gf_af",
        "des101010", "rsa_signature", "generators97", "congruences7one", "shannon_ambiguous",
        "elgamal41_113", "des_p", "ecc_encrypt3_3_5", "cia", "rabin1731",
        "knapsack_bad13", "des_keys", "inverse", "hash_length", "phi765",
        "authentication", "agreement_scope", "ca_not", "pow41_101", "public_claims",
    ])),
    "de-thi-k16-3": dict(zip(map(str, range(2021, 2061)), [
        "roles", "affine12_20", "units235", "hill_objzma", "public_private",
        "hash_encrypt", "order13_20", "mix13", "rsa_exponent", "generators41_alt",
        "orders21", "autokey_crypto", "des110001", "ecc2_2_7", "gcd_max",
        "rabin1234", "merkle452163", "authentication", "inverse", "knapsack_bad15",
        "cyclic_count", "which_cyclic", "elgamal_basis", "hash_oneway", "modes",
        "public_claims", "elgamal41_117", "shannon_aes", "pow41_117", "phi_product",
        "ca_not", "residues235", "count666", "not_coprime", "gf_2f",
        "congruences7three", "ecc_encrypt3_10_9", "log17_21", "phi1001", "rsa_signature",
    ])),
    # Optional excluded material is supported by hint_for, never exported.
    "de-thi-k16-1": {
        **dict(zip(map(str, range(1, 37)), [
            "jacobi156", "rabin1234", "hash_properties", "merkle361254", "phi969",
            "gf_a9", "ecc_encrypt2", "congruences7zero", "missing_inverse_options", "missing_stem",
            "missing_stem", "missing_stem", "missing_stem", "missing_stem", "missing_stem",
            "missing_ecc", "des_p", "rsa_signature", "hash_length", "tonelli75",
            "des_keys", "missing_stem", "missing_stem", "missing_roles", "hill_addhcm",
            "autokey_son", "missing_ca", "missing_shannon", "order17_29", "coprime",
            "roles", "missing_affine_options", "missing_knapsack", "key_management", "elgamal41_117",
            "missing_cyclic",
        ])),
        "33-HP": "public_claims", "34-HP": "missing_rabin_options", "35-HP": "missing_des_row",
    },
}

# These pairs are inputs from all four options, not computed gcd values.
GCD_INPUTS = {
    "de-thi-nmmmh": "(137,479), (130,315), (42,286), (281,389)",
    "de-thi-mat-ma-2021-trac-nghiem": "(137,479), (130,315), (42,286), (281,389)",
    "de-thi-k16-2": "(65,95), (347,491), (214,694), (91,133)",
    "de-thi-k16-3": "(391,805), (85,77), (323,57), (416,65)",
}


def hint_for(q):
    """Return a curated 1–4-line hint without consulting the stored answer key."""
    exam = q.get("source_exam_id")
    number = str(q.get("source_question_number", ""))
    if not exam or not number:
        # A minimal {id: ...} object also works for UI/build integration.
        for candidate in EXAMS:
            prefix = f"nmmmh-{candidate}-"
            if q.get("id", "").startswith(prefix):
                exam, number = candidate, q["id"][len(prefix):]
                break
    key = EXAMS[exam][number]
    hint = TEXT[key]
    if key == "gcd_max":
        hint = "Chạy Euclid cho " + GCD_INPUTS[exam] + "; ghi ước chung cuối cùng của từng cặp.\n" + hint.splitlines()[1]
    return hint


def normalize(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value)).strip().casefold()


def option_text(q, letter):
    option = q.get(letter, {})
    parts = [option.get("text", "")]
    for block in option.get("blocks", []):
        if block.get("type") == "table":
            parts.append(json.dumps(block["rows"], ensure_ascii=False))
    return " ".join(parts).strip()


def validate_hint(q, hint):
    """Disclosure tripwires, not a mathematical proof of spoiler-freedom."""
    errors = []
    if not 1 <= len(hint.splitlines()) <= 4 or any(len(s) > 300 for s in hint.splitlines()):
        errors.append("expected 1–4 short lines (max 300 characters each)")
    if hint.count(r"\(") != hint.count(r"\)"):
        errors.append("unbalanced inline math")
    if re.search(r"(?:đáp án|phương án|chọn|khoanh|loại|giữ)(?!\w)\s*(?:(?:đúng|sai|là)\s*)*[:=]?\s*[A-D](?![\w–—-])", hint, re.I):
        errors.append("option-letter disclosure")
    audit = q.get("answer_audit", {})
    explanation = normalize(audit.get("explanation", ""))
    normalized = normalize(hint)
    if explanation and len(explanation) >= 24 and explanation in normalized:
        errors.append("copied explanation")
    # Catch copying a substantial contiguous passage, even with a new prefix.
    words = explanation.split()
    if any(" ".join(words[i:i + 10]) in normalized for i in range(len(words) - 9)):
        errors.append("copied explanation passage")
    stem = normalize(q.get("question", ""))
    # Scan ALL candidates, independent of correct_answer: keys can be wrong.
    for letter in "ABCD":
        candidate = normalize(option_text(q, letter))
        if len(candidate) >= 8 and candidate in normalized and candidate not in stem:
            errors.append("verbatim candidate answer")
        # A lone numerical/point/bit/cipher option must not be supplied as a result.
        if re.fullmatch(r"[-−+\d\s.,;()\[\]–_₂₁₆Hh]+", candidate) and candidate:
            result_intro = r"(?:kết quả|đáp số|thu được|bậc|cấp|điểm|nghiệm|chữ ký|bản mã|bản rõ|khóa|giá trị|logarit|bằng)\s*(?:là|=|:)\s*"
            compact = re.sub(r"\s+", "", candidate)
            flexible_candidate = r"\s*".join(map(re.escape, compact))
            if re.search(result_intro + flexible_candidate + r"(?!\d)", normalized):
                errors.append("solved candidate result")
    # Cipher outputs are absent even if the answer key is missing or incorrect.
    source = q.get("question", "")
    for token in re.findall(r"\b[A-Z]{6,}\b", hint):
        if token not in re.sub(r"\s+", "", source.upper()):
            errors.append("cipher/plaintext not present in question inputs")
    return sorted(set(errors))


def load_questions():
    manifest = json.loads((ROOT / "subjects/nmmmh/manifest.json").read_text(encoding="utf-8"))
    questions = []
    files = []
    for exam in manifest["exams"]:
        path = ROOT / exam["question_file"]
        questions.extend(json.loads(path.read_text(encoding="utf-8")))
        files.append(path)
    published_ids = {q["id"] for q in questions}
    # Read approved edit metadata for provenance only. It belongs to the main
    # integrator; this generator never applies edits to any source JSON.
    changes = ROOT / "subjects/nmmmh/audit/approved_changes.json"
    if changes.is_file():
        files.append(changes)
    return questions, published_ids, files


def build_export(questions, published_ids, files=()):
    if {q["id"] for q in questions} != published_ids or len(questions) != len(published_ids):
        raise ValueError("Export must contain exactly the published IDs, without duplicates or excluded questions")
    hints, pending, failures, by_exam = {}, [], {}, Counter()
    for q in questions:
        try:
            hint = hint_for(q)
        except KeyError:
            pending.append(q["id"])
            continue
        problems = validate_hint(q, hint)
        if problems:
            failures[q["id"]] = problems
        hints[q["id"]] = hint
        by_exam[q["source_exam_id"]] += 1
    if failures:
        raise ValueError(json.dumps(failures, ensure_ascii=False, indent=2))
    completed = set(hints)
    return {
        "metadata": {
            "schema_version": 1,
            "generator": "tools/nmmmh_hints.py",
            "language": "vi",
            "status": "complete" if not pending else "partial",
            "published_total": len(published_ids),
            "published_verified_hint_count": len(completed & published_ids),
            "published_pending_hint_count": len(published_ids - completed),
            "excluded_verified_hint_count": len(completed - published_ids),
            "excluded_pending_hint_count": len(set(pending) - published_ids),
            "total_hint_count": len(hints),
            "pending_ids": pending,
            "counts_by_exam": dict(sorted(by_exam.items())),
            "validation": {"passed": True, "disclosure_pattern_failures": 0,
                           "scanned_option_set": "all A–D, regardless of stored key",
                           "checks": ["1–4 short logical lines", "balanced inline math delimiters",
                                      "option-letter disclosure", "verbatim candidate answer",
                                      "solved numerical/point candidate result", "copied explanation",
                                      "unexpected cipher/plaintext output"]},
            "verification_scope": "Hints manually checked against stems, A–D and existing audit/proofs; not new answer-key certification.",
            "caveats": ["Pattern checks cannot guarantee absence of every semantic spoiler.",
                        "Review questions remain uncertain; hints never repair or certify their answer keys.",
                        "Line count is logical; display wrapping depends on the UI width."],
            "source_sha256": {str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else p.name:
                              hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        },
        "hints": hints,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-excluded-source", type=Path, help="Validate excluded K16-1 in memory; never add it to the export")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    questions, published, files = load_questions()
    result = build_export(questions, published, files)
    meta = result["metadata"]
    if args.require_complete and meta["pending_ids"]:
        raise SystemExit(f"Unmapped questions: {meta['pending_ids']}")
    if args.check_excluded_source:
        source = args.check_excluded_source / "questions_verified.json"
        excluded = [q for q in json.loads(source.read_text(encoding="utf-8"))
                    if q["source_exam_id"] == "de-thi-k16-1"]
        assert len(excluded) == 39, "Expected the complete 39-record excluded source"
        for q in excluded:
            problems = validate_hint(q, hint_for(q))
            if problems:
                raise ValueError(f"{q['id']}: {problems}")
        meta["optional_excluded_validation"] = {"supported": len(excluded), "exported": 0,
                                                 "source_incomplete_exceptions": sum(
                                                     EXAMS[q['source_exam_id']][q['source_question_number']].startswith("missing_")
                                                     for q in excluded)}
    target = ROOT / "subjects/nmmmh/audit/hints.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: meta[k] for k in ("status", "published_verified_hint_count", "published_pending_hint_count",
                                         "excluded_verified_hint_count", "excluded_pending_hint_count")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
