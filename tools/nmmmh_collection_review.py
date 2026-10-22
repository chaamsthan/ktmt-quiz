"""Human review of the seven native documents, in exact source question order.

This is import/audit input, NOT a second browser question bank. Published JSON
is canonical. Topic choices were made after reading stems, options and figures.
No radio selection is treated as an answer key.
"""
TOPICS = {
 'security':('1',None,'Mục tiêu và dịch vụ an toàn thông tin'),
 'symmetric':('1','01.06','Phân loại mật mã: đối xứng/bất đối xứng'),
 'classify':('1','01.05','Các khái niệm cơ bản của hệ mật'),
 'block':('1','01.07','Mã khối và mã dòng'),
 'attack':('1','01.05','Các khái niệm cơ bản của hệ mật'),
 'shannon':('2','02.03.01','Nguyên lý thiết kế của Shannon'),
 'classic':('2','02.01.01','Tổng quan mật mã cổ điển'),
 'caesar':('2','02.01.03','Mã dịch vòng Caesar'),
 'affine':('2','02.01.04','Mã Affine'),
 'vigenere':('2','02.01.06','Mã Vigenère'),
 'hill':('2','02.01.07','Mã Hill'),
 'autokey':('2','02.01.08','Mã khóa chạy'),
 'otp':('2','02.01.09','Mã dùng một lần'),
 'transpose':('2','02.01.10','Mã hoán vị'),
 'des':('2','02.03.02','Tổng quan DES và mạng Feistel'),
 'desbox':('2','02.03.03','Hàm f, hộp thế và hoán vị DES'),
 'deskey':('2','02.03.04','Sinh khóa vòng DES'),
 'desprop':('2','02.03.05','Tính chất và khóa yếu DES'),
 'triple':('2','02.03.06','DES bội hai và Triple DES'),
 'aes':('2','02.03.07','Tổng quan AES'),
 'gf':('2','02.03.08','Phép toán trong GF(2^8)'),
 'aesround':('2','02.03.09','Trạng thái và vòng mã hóa AES'),
 'sub':('2','02.03.10','SubBytes'),
 'shift':('2','02.03.11','ShiftRows'),
 'mix':('2','02.03.12','MixColumns'),
 'add':('2','02.03.13','AddRoundKey'),
 'aeskey':('2','02.03.14','Mở rộng khóa AES'),
 'mode':('2',None,'Chế độ hoạt động của mã khối'),
 'lfsr':('2','02.06.02','Thanh ghi dịch phản hồi tuyến tính'),
 'rc4':('2','02.06.04','Tổng quan RC4'),
 'ksa':('2','02.06.06','Khởi tạo khóa RC4 (KSA)'),
 'math':('3',None,'Cơ sở số học cho mật mã khóa công khai'),
 'rsa':('3',None,'Hệ mật RSA'),
 'ecc':('3',None,'Mật mã đường cong elliptic'),
 'elgamal':('3',None,'Hệ mật ElGamal'),
 'knapsack':('3',None,'Hệ mật Merkle–Hellman và bài toán ba lô'),
 'rabin':('3',None,'Hệ mật Rabin'),
 'public':('3',None,'Hệ mật khóa công khai'),
 'signature':('4',None,'Chữ ký số'),
 'hash':('4',None,'Hàm băm'),
 'hybrid':('5',None,'Phân phối khóa và mật mã lai'),
}

# One reviewed line per original question: topic | answer-free quick hint.
REVIEW_TEXT = {
'chuong1':r'''
security|Phân biệt việc giữ dữ liệu không bị sửa với việc che nội dung và kiểm tra người gửi.
security|Xét riêng khả năng đọc thông điệp của người không có khóa; đừng gộp nhầm với khả dụng.
security|Tách dịch vụ do kỹ thuật mật mã cung cấp khỏi khả năng duy trì hệ thống luôn hoạt động.
symmetric|Kiểm tra từ “tất cả”: khóa công khai và khóa giải mã có cùng yêu cầu giữ bí mật không?
block|Xét DES xử lý một khối cố định hay tạo từng phần tử dòng khóa; không nhầm số vòng với kích thước khối.
des|Đối chiếu từng chữ viết tắt DES, đặc biệt từ đầu tiên; bỏ các tên ghép gần giống.
symmetric|So sánh cách cấp khóa của hệ đối xứng với cặp khóa công khai/riêng của hệ bất đối xứng.
otp|Chỉ xét tính mật hoàn thiện khi khóa ngẫu nhiên đều, dùng đúng một lần và đủ dài.
security|Hỏi khả năng ngăn đọc trộm, không phải phát hiện thay đổi hoặc kiểm tra người gửi.
classify|Đọc lại chủ thể và mục đích mã hóa; loại phương án chỉ nói đến quân sự hoặc hàm không đảo được.
classify|Câu nguồn thiếu một phần tiêu chí “KHÔNG”; đối chiếu ghi chú nguồn trước khi chốt lựa chọn.
classify|Đếm các tiêu chí phân loại độc lập: phép biến đổi, quan hệ khóa và cách xử lý bản rõ.
classify|Phân biệt chiều biến đổi bản rõ → bản mã với chiều giải mã và kỹ thuật thám mã.
shannon|Hiệu ứng thác lũ nói về số bit thay đổi ở đầu ra khi chỉ đảo một bit đầu vào.
symmetric|Kiểm tra hai bên có cần thống nhất bí mật dùng chung trước khi mã hóa hay không.
shannon|Phân biệt che quan hệ khóa–bản mã với việc lan ảnh hưởng của một bit ra nhiều bit khác.
shannon|Ghép đúng hai nguyên lý thiết kế mã khối; “thay thế” và “hoán vị” là công cụ, không phải tên cả hai nguyên lý.
block|Xét định nghĩa mã khối trong nhóm thuật toán đối xứng; không nhầm với phép RSA trên một số nguyên.
caesar|So sánh số bảng thay thế được dùng trong cùng một thông điệp ở bốn hệ mật.
vigenere|Vigenère thay bảng theo vị trí khóa; vì vậy không thể chỉ áp dụng tần suất toàn bản mã như mã đơn biểu.
''',
'chuong2':r'''
block|Loại RC4 trước khi kiểm tra các cặp thuật toán còn lại có cùng xử lý theo khối không.
block|Xác định thuật toán tạo ra gì ở mỗi bước rồi mới xét tốc độ hay cách triển khai.
attack|Ước lượng số lần thử khóa; vét cạn phụ thuộc độ lớn không gian khóa, không chỉ khóa yếu.
attack|Tìm phương án cho kẻ tấn công các cặp bản rõ–bản mã tương ứng, không chỉ một trong hai.
attack|Phân biệt dữ kiện đã biết với quyền chủ động chọn bản rõ hoặc bản mã để hỏi hệ thống.
security|Mã hóa đơn thuần ngăn đọc trộm; không tự coi nó là cơ chế bảo đảm mọi dịch vụ an toàn.
shannon|Đảo một bit ở đầu vào rồi xét độ lan truyền sang các bit bản mã, không đổi toàn bộ thông điệp.
symmetric|Dựa vào quan hệ giữa khóa mã và khóa giải, thay vì dựa vào việc có công bố thuật toán hay không.
mode|So sánh chế độ hồi tiếp dòng khóa với chế độ nối bản mã theo khối; giữ nguyên “CRT” như bản nguồn.
shannon|Tìm mục tiêu che giấu quan hệ phức tạp giữa khóa và bản mã, đừng lẫn với lan truyền bit.
shannon|Phân biệt hai mục tiêu Shannon với hai phép biến đổi thường dùng để đạt chúng.
block|Đối chiếu định nghĩa mã khối đối xứng; kích thước đầu vào cố định không đồng nghĩa dùng cặp khóa công khai.
aesround|Kiểm tra tính tuyến tính trên GF(2^8): hoán vị vị trí và nhân ma trận khác với tra S-box phi tuyến.
otp|So kích thước không gian khóa với không gian bản rõ khi yêu cầu mật hoàn thiện.
rc4|Theo dõi lệnh swap trong PRGA; lưu ý trường hợp hai chỉ số có thể trùng nhau.
rc4|Phân biệt độ dài khóa đầu vào với mảng S gồm 256 phần tử; đây là thông số RC4 theo tài liệu môn học.
aes|Phân biệt kích thước khối cố định của AES với ba kích thước khóa được hỗ trợ.
sub|Xét S-box như một bảng ánh xạ byte; không lấy số lần áp dụng bảng làm số loại bảng.
aesround|Dùng liên hệ Nr = Nk + 6, với Nk là số từ 32 bit của khóa đang hỏi.
aesround|Đổi khóa 192 bit ra số từ 32 bit rồi dùng quan hệ số vòng theo Nk.
aesround|Từ khóa 128 bit suy ra Nk, rồi tra quan hệ Nr = Nk + 6.
aesround|Một trạng thái gồm một khối AES; chia số byte thành các cột có bốn byte.
aesround|Ghép từng độ dài khóa với số vòng tương ứng theo Nr = Nk + 6.
aes|Chỉ giữ các độ dài khóa được FIPS 197 hỗ trợ; không nhầm với độ dài khối.
aes|Phân biệt Rijndael tổng quát với AES; kiểm tra giới hạn độ dài khóa của thiết kế gốc.
aes|Chú ý phát biểu về giới hạn khóa, không suy từ kích thước thanh ghi hay khối dữ liệu.
aes|Kiểm tra phát biểu nói về khối Rijndael, không phải DES; loại kích thước thuộc thuật toán khác.
aes|Rijndael cho phép một số độ dài theo bước 32 bit; đừng áp giới hạn khối AES cho toàn họ.
sub|SubBytes có nghịch đảo và phi tuyến; xét riêng phát biểu gán khả năng khuếch tán cho phép thay byte.
aes|Trong hình có cả nhãn A–D gốc: phân biệt độ dài khóa với khối cố định của AES trước khi chọn nhãn.
sub|S-box AES là ánh xạ khả nghịch trên các byte; phân biệt số đầu vào với số bit của một byte.
gf|So đa thức m(x) trong hình với đa thức chuẩn bậc 8; đặc biệt kiểm tra các hạng x^4 và x.
aeskey|Khóa AES-192 sinh toàn bộ khóa vòng: số từ = 4 × (Nr + 1), kể cả khóa vòng đầu.
aeskey|Đừng chỉ đếm các vòng biến đổi; khóa vòng ban đầu cũng chiếm bốn từ.
aeskey|Tính số vòng từ Nk, sau đó nhân bốn từ cho mỗi khóa vòng, kể cả vòng đầu.
gf|Từ RC5 = 10 ở hệ hex, áp dụng xtime một lần để suy ra RC6.
aeskey|Tách khóa theo đúng thứ tự byte thành các từ bốn byte; w3 là từ thứ tư, không phải byte thứ tư.
aeskey|Tra riêng từng byte của SubWord; nguồn bỏ trống Rcon[j], hãy đọc ghi chú trước khi dùng câu này.
aeskey|w4 = w0 XOR g(w3); nguồn đang bỏ trống g(w3), không tự điền giá trị từ phương án.
add|Chỉ lấy hai phần tử cùng vị trí (2,0) ở bản rõ và khóa trong hình rồi XOR ở hệ hex.
lfsr|Dịch từng ô theo chiều mũi tên, tính bit phản hồi bằng XOR rồi xuất a8…a0, không đảo thêm lần nữa.
ksa|Tính j ở i=0 trước; tại i=1 dùng j cũ, S[1] và T[1], rồi mới thực hiện swap.
affine|Khóa Affine phải có hệ số nhân khả nghịch modulo 26; kiểm tra điều kiện bị bỏ sót trong hình.
aesround|So cấu trúc từng sơ đồ: mạng thay thế–hoán vị không có thao tác tách nửa kiểu Feistel.
des|Tìm sơ đồ chia khối thành hai nửa và đổi chỗ sau mỗi vòng; không chọn hình chỉ thay byte.
des|Viết một vòng (L,R) → (R,L XOR f(R,K)); từ đó so từng phát biểu về phần được biến đổi.
des|Đối chiếu cấu trúc thuật toán thay vì chỉ dựa vào tên RC; các thành viên họ RC không cùng một cấu trúc.
rc4|Loại các thuật toán xử lý khối; xét thuật toán dùng hoán vị S để tạo dòng khóa.
attack|Tách câu định nghĩa một kiểu tấn công khỏi nhận xét “thường gặp nhất”, vốn cần ngữ cảnh mô hình đe dọa.
attack|Dữ kiện là các cặp bản rõ–bản mã có sẵn, không có quyền gửi truy vấn tùy ý.
''',
'chuong3':r'''
public|Xét riêng khẳng định “thay thế hoàn toàn” và “đã chứng minh tính khó”; hai cách nói tuyệt đối đều cần dè chừng.
public|Nhận diện các thuật toán có khóa công khai, rồi loại cặp chứa mã khối đối xứng.
attack|Tìm quyền gửi bản mã tùy chọn để quan sát kết quả giải mã, không chỉ đọc bản mã có sẵn.
attack|So chi phí thử hết khóa với lực lượng không gian khóa; các loại khóa yếu không quyết định toàn bộ vét cạn.
attack|Một cặp tương ứng bản rõ–bản mã khác với danh sách bản rõ không biết bản mã tương ứng.
attack|Xác định dữ kiện đã có và quyền chọn dữ kiện của đối thủ trước khi gọi tên kiểu tấn công.
attack|Chọn đúng mô hình có các cặp bản rõ và bản mã tương ứng đã biết.
otp|Điều kiện để so độ an toàn: khóa độc lập, ngẫu nhiên đều, không tái sử dụng và đủ dài.
public|An toàn tính toán khác an toàn vô điều kiện; tìm phát biểu dựa vào bài toán khó.
security|Theo nguyên lý Kerckhoffs, thuật toán có thể công khai; xác định thông tin thực sự phải giữ bí mật.
classify|Phân biệt các tiêu chí phân loại: phép xử lý, quan hệ khóa và cách chia thông điệp.
symmetric|Khi nói ưu điểm cho dữ liệu lớn, so chi phí tính toán mã đối xứng với phép toán khóa công khai.
classify|Phân biệt chiều bản rõ → bản mã với chiều ngược lại; đọc đúng thuật ngữ tiếng Anh.
attack|Nếu chỉ quan sát được các bản mã, đừng tự thêm quyền chọn bản rõ hay biết cặp tương ứng.
public|Khóa riêng thuộc từng chủ thể; dùng chung một cặp khóa sẽ không còn mô hình sở hữu riêng đó.
public|So bài toán nền của từng hệ với bài toán phân tích số nguyên, không chỉ so công thức lũy thừa.
ecc|So độ dài khóa để đạt cùng mức an toàn, không so bằng cùng số bit khóa ở mọi hệ.
math|Hai đồng dư có cùng số dư; dùng gcd(b,c)=1 để ghép modulo tích, không cộng hai modulo.
math|Với Legendre, phân biệt a chia hết cho p, thặng dư và bất thặng dư; sau đó chọn nhãn trong hình.
math|Kiểm tra dấu trong luật tương hỗ bậc hai; trường hợp cả hai số ≡ 3 mod 4 là ngoại lệ.
math|Số Blum đòi hỏi hai số nguyên tố phân biệt và cùng thuộc lớp dư 3 modulo 4.
math|Dùng Fermat cho a không chia hết cho p và dạng a^p ≡ a; chú ý phương án chỉ là trường hợp con.
math|Với p,q lẻ phân biệt, đếm các bình phương khác 0 ở từng modulo rồi dùng CRT; kiểm tra giả thiết “lẻ”.
math|Nhóm do α sinh có số phần tử bằng ord(α); kiểm tra khoảng số mũ và đừng nhầm với φ(φ(n)).
math|Phân tích 36 thành thừa số nguyên tố; chỉ cần thử x^(36/r) cho từng thừa số nguyên tố r.
math|Với modulo nguyên tố 41, số bình phương khác 0 bằng một nửa lực lượng nhóm nhân.
math|Bình phương các số từ 1 đến 6 modulo 13, khử trùng kết quả rồi so toàn bộ tập trong đáp án.
math|Thử từng ứng viên vào cả ba đồng dư 9, 7, 5; chỉ cần một đồng dư sai để loại.
math|Phân tích 119 thành hai số nguyên tố rồi dùng tính nhân của φ với hai thừa số nguyên tố cùng nhau.
math|Tách lũy thừa của 2, dùng luật tương hỗ Jacobi và tiếp tục lấy phần dư để giảm số.
math|Dùng tiêu chuẩn Euler với p=4001: tính a^((p−1)/2) mod p rồi đổi số dư sang ký hiệu Legendre.
math|Bậc phải chia φ(61); thử các ước tăng dần và dừng ở số mũ đầu tiên cho dư 1.
math|Mỗi dòng Euclid giữ a = qb + r; sau đó cập nhật hệ số x,y theo cùng thương q.
math|Theo đúng thuật toán trong khung: phân tích p−1, khởi tạo c,r rồi chạy duy nhất vòng i=1.
math|Thử bình phương từng số được liệt kê modulo 437; đáp án phải đúng cả bốn căn, không chỉ một số.
math|Viết 93 ở hệ nhị phân theo bit thấp trước; A bình phương liên tiếp, B chỉ nhân khi bit bằng 1.
math|Trong bước lớn–bước nhỏ, tính m từ bậc của α chứ không tự lấy căn n nếu α không sinh cả nhóm.
math|Tìm giao hai hàng bảng; dùng log = m×i+j với đúng chỉ số cột, không cộng hai giá trị trong bảng.
math|Trước khi dùng φ(φ(n)), kiểm tra nhóm có phần tử sinh; nếu không cyclic thì không áp công thức đếm đó.
math|Phân tích 72 rồi thử lần lượt các số nhỏ bằng tiêu chuẩn lũy thừa theo thừa số nguyên tố của 72.
math|Cấp của nhóm nhân là số lớp dư nguyên tố cùng nhau với 776; tính φ(776), không tính φ hai lần.
math|Phân tích 1764 rồi áp φ(n)=n∏(1−1/p), mỗi thừa số nguyên tố chỉ dùng một lần.
math|Kiểm tra từng phần tử bằng bậc của nó; hình nguồn ghi hai modulo khác nhau, cần đọc cảnh báo.
math|Nhóm nhân modulo n chỉ cyclic khi n thuộc dạng 1,2,4,p^k,2p^k với p lẻ nguyên tố.
math|Tính gcd của từng số với 3528; tư cách thuộc nhóm không đòi hỏi phần tử phải sinh cả nhóm.
math|Phân tích từng số thành p×q; chỉ ghi 1 khi p≠q và cả hai ≡ 3 mod 4.
rsa|Xét hai khóa mã và giải có thể công bố đồng thời hay không; không phân loại theo tên “khóa riêng”.
rsa|Phân biệt bài toán phân tích số nguyên với việc sinh hay kiểm tra số nguyên tố.
rsa|Điều kiện của e liên quan φ(n), không phải n; tìm phản ví dụ với e có thừa số chung với n.
rsa|So modulo trong quan hệ e×d với modulo dùng khi mã hóa; hai modulo có vai trò khác nhau.
''',
'tonghop1':r'''
aes|So AES và Triple DES về cấu trúc, tốc độ và số vòng; nguồn đang thiếu tiêu chí ĐÚNG/SAI ở đầu câu.
public|Hệ công khai giải quyết vấn đề phân phối khóa, không có nghĩa loại bỏ toàn bộ hệ khóa bí mật.
rc4|Nhận diện thuật toán tạo dòng khóa, không chọn thuật toán khóa công khai chỉ vì có phép toán tuần tự.
mix|Xác định ô đích Sij trước khi nhân hàng với cột; đề nguồn bỏ trống chỉ số ô cần tính.
hill|Thử gcd(det K,26) cho từng ma trận trong hình, không kiểm tra gcd của từng phần tử riêng lẻ.
aesround|Theo dõi vòng AES: thay byte, dịch hàng, trộn cột, cộng khóa; so với nhánh tách nửa Feistel.
desbox|Muốn điền abcd của IP phải có bảng đầu vào và vị trí ô; nguồn câu này chưa có hình tương ứng.
desbox|Đếm số khối 6 bit đưa vào tầng S-box sau mở rộng; không lấy số vòng làm số hộp thế.
block|Vernam kết hợp bản rõ với dòng khóa; phân biệt loại mã với cách quản lý cặp khóa.
math|Dùng dạng n cho phép nhóm nhân cyclic trước khi xét số phần tử sinh trong từng nhóm.
rsa|Tính d là nghịch đảo của 307 modulo (37−1)(19−1), rồi thử m^307 mod n với từng đáp án.
ecc|Tính λ=(yQ−yP)/(xQ−xP) mod 11; dùng nó suy ra xR,yR và kiểm tra điểm trên đường cong.
rsa|Số điểm bất động bằng (1+gcd(e−1,p−1))(1+gcd(e−1,q−1)); chú ý cộng 1 trước khi nhân.
math|Kiểm tra n thuộc dạng p^k hoặc 2p^k với p lẻ nguyên tố; không chỉ xét n có là số chẵn không.
knapsack|Thử tổng trọng lượng được chọn trong từng phương án; dãy siêu tăng cũng cho phép tham lam từ cuối.
shift|Dịch trái hàng r đúng r vị trí theo chỉ số bắt đầu từ 0; chỉ lấy hai ô cần hỏi trong hình.
knapsack|Tính W×si mod M rồi áp đúng chiều hoán vị; kiểm tra số phần tử vì nguồn cho dãy và phương án khác độ dài.
signature|Chữ ký của A dùng dA,nA, không dùng khóa của B; thử lũy thừa công khai của A để xác minh.
desbox|Lấy hai bit biên của 010011 làm hàng, bốn bit giữa làm cột; tra đúng S5 chứ không tra S3.
classify|Mã hóa phải đảo được khi có khóa; phân biệt với hàm một chiều không có thao tác giải mã.
math|Thử bình phương các lớp dư hoặc tiêu chuẩn Euler cho từng ứng viên modulo 23.
rsa|Thử y = 301^7 mod (31×17); rút gọn sau mỗi lần bình phương để tránh số lớn.
security|Phân biệt bí mật/toàn vẹn với khả dụng; mã hóa không thay thế cơ chế duy trì dịch vụ.
elgamal|Khóa công khai β = α^a mod p; ở đây hai ký hiệu “a” bị dùng lẫn, phân biệt 39 và 93 theo vai trò.
sub|Tìm phép phi tuyến tạo confusion trong AES; dịch hàng và trộn cột chủ yếu giúp diffusion.
vigenere|Đếm số bảng thay thế thay đổi theo vị trí khóa của Vigenère, không đếm số ký tự của bảng chữ cái.
caesar|Một khóa Caesar cố định ánh xạ mỗi chữ rõ sang một chữ mã cố định trong toàn thông điệp.
aesround|Đổi độ dài khóa ra Nk rồi kiểm tra từng cặp bằng Nr=Nk+6; chú ý phương án viết nhầm 196.
des|Kiểm tra từng từ của tên tiếng Anh DES; đừng chọn từ bắt đầu bằng Digital chỉ vì viết tắt giống nhau.
rsa|Người nhận B giải bằng nB và dB; tìm nghịch đảo của 93 modulo (29−1)(17−1), không dùng khóa A.
math|Hai đồng dư có cùng số dư; nghiệm modulo tích phải giữ nguyên số dư khi thử lại cả 213 và 211.
knapsack|Mã hóa là cộng các trọng số khóa công khai ở vị trí bit 1, không lấy modulo từng tổng nếu đề không yêu cầu.
aesround|Vòng giữa không có AddRoundKey ở đầu; phân biệt khởi tạo trước vòng 1 với cấu trúc một vòng thông thường.
sub|Tra S-box bằng nibble cao làm hàng, nibble thấp làm cột; đọc đúng s31 và s12 trong hình.
math|Nhóm modulo 14 cyclic; số phần tử sinh là φ của cấp nhóm, không phải φ(14) trực tiếp.
aes|Đổi byte ra bit trước khi so tập độ dài khóa AES; đừng lẫn khóa DES thực dụng với khối DES.
des|Cấu trúc giải mã dùng lại mạng Feistel với thứ tự khóa đảo; số vòng không đổi theo chiều xử lý.
public|Phân biệt khả năng của họ thuật toán với một thao tác mã hóa cụ thể; nguồn có hai phát biểu cùng có thể đúng.
affine|Với khóa cố định, Affine là một ánh xạ chữ–chữ; “đơn biểu” không đồng nghĩa “dịch vòng”.
gf|xtime là phép nhân trong trường với một đa thức đơn thức; số mũ không phải số lần dịch tùy ý.
''',
'tonghop2':r'''
autokey|Vigenère lặp từ khóa, còn khóa chạy nối tiếp bản rõ; so kỹ phát biểu trộn hai cơ chế này.
elgamal|Thành phần y1 chỉ dùng α,k,p; bỏ qua khóa riêng a và bản tin x khi tính thành phần này.
elgamal|Khóa công khai chứa β=17^62 mod 113; tính lũy thừa modulo rồi so bộ ba đầy đủ.
signature|Tính n, φ(n), rồi e=d^−1 mod φ(n); khi xác minh phải dùng cùng modulo n, không đổi sang số gần giống.
knapsack|Nhân c với W^−1 modulo M, tham lam trên dãy siêu tăng rồi đảo đúng hoán vị; có thể thử mã hóa ngược đáp án.
ecc|Dùng nhân đôi P, tiếp tục nhân đôi để có 4P rồi cộng P; luôn kiểm tra phép chia bằng nghịch đảo modulo 11.
rabin|Mã Rabin là bình phương bản tin modulo pq; thử tính 114^2 mod (41×53) trước khi chọn.
desbox|Tra S2 theo hai bit ngoài làm hàng và bốn bit giữa làm cột; nguồn thiếu bảng minh họa của câu này.
gf|Trong GF(2^8), phép cộng và phép nhân khác nhau; chỉ một trong hai tương đương XOR bit.
affine|Giải P=7^−1(C−2) mod 26, rồi chỉ đọc những vị trí có dấu sao trong hình.
caesar|Cộng khóa 15 modulo 26 ở đúng bốn vị trí có dấu sao; không cần mã toàn bộ BEAUTIFULGIRL.
des|Nhận diện phép chia khối thành hai nửa và đổi chỗ trong DES; đừng nhầm với SPN của AES.
deskey|Phân biệt độ dài khóa được cung cấp kể cả parity với số bit khóa thực sự tham gia thuật toán.
math|Thử 103×x mod 1013 cho mỗi đáp án; số âm và đại diện dương có thể là cùng một lớp dư.
math|Viết 25=16+8+1 rồi bình phương liên tiếp modulo 9781; chỉ nhân ba lũy thừa cần thiết.
des|Đây là độ lớn khối dữ liệu, không phải số bit khóa hiệu dụng; xác định trường đại lượng trước khi chọn.
deskey|Vét cạn đếm các khóa hiệu dụng, không tính tám bit parity thành bí mật bổ sung.
signature|Chữ ký số kiểm tra người ký và dữ liệu có bị đổi; không mặc định giúp che nội dung thông điệp.
affine|Khóa Affine phải là cặp (a,b), với gcd(a,26)=1; loại một số đơn và ma trận trước.
deskey|Nguồn nói độ dài khóa ban đầu, khác số bit hữu ích sau PC-1; kiểm tra cách tính parity.
math|Tính gcd từng cặp bằng Euclid; một cặp có số thứ hai là bội số của số thứ nhất giúp loại nhanh.
deskey|Từ vòng 7 sang 9, cộng số bước dịch của vòng 8 và 9; dịch riêng hai nửa 28 bit, không dịch cả chuỗi 56 bit.
desbox|Cần cả dữ liệu C và vị trí ABCD để áp bảng P; hình tương ứng không có trong câu nguồn này.
symmetric|So cách dùng khóa của DES với cặp công khai/riêng; đừng suy từ tên chuẩn AES hay kích thước khóa.
hill|Ma trận khả nghịch modulo 26 khi và chỉ khi định thức nguyên tố cùng nhau với 26.
knapsack|X phải lớn hơn tổng các phần tử trước nó, đồng thời phần tử ngay sau X vẫn phải lớn hơn toàn tổng phía trước.
math|Chỉ áp số phần tử sinh = φ(φ(n)) khi nhóm nhân cyclic; giả thiết này đang bị lược trong nguồn.
sub|Tra ba byte đầu vào tương ứng trong S-box; giữ thứ tự s11,s32,s23 và đọc chỉ số từ 0.
desbox|IP là hoán vị của một khối DES; số ô bảng bằng số bit dữ liệu, không phải số bit khóa.
sub|Hàm thay byte nghịch đảo không dùng chính cùng ánh xạ S-box thuận; so cả chiều mã và giải.
math|Thử a^11 mod 23 để phân biệt thặng dư bậc hai khác 0; không nhầm với việc a có là số nguyên tố không.
gf|Đọc từng số mũ trong đa thức AES chuẩn bậc 8; giữ cả hạng hằng và hạng x.
desbox|Một hộp DES không thay byte bằng byte; tách đầu vào mở rộng 48 bit thành các khối nhỏ để kiểm tra.
deskey|Đếm số khóa dùng cho các vòng; không cộng khóa whitening như trong một số mã khối khác.
transpose|Hoán vị vị trí giữ nguyên từng chữ và tần suất chữ; phép thế thường chuyển tần suất sang chữ khác.
aes|So từng từ của tên AES, chú ý từ đầu tiên; không chọn phương án chỉ có chữ viết tắt tương tự.
rsa|B gửi A thì dùng khóa công khai của A; tính 117^37 mod (19×31), không dùng eB để mã cho chính B.
gf|81 có bit cao bằng 1 ở hệ hex: dịch trái rồi rút gọn bằng đa thức AES, giữ đúng một byte.
desbox|Tầng mở rộng tạo 48 bit trước tám hộp thế; chia đều số bit này để suy kích thước đầu vào mỗi hộp.
vigenere|Giải từng vị trí bằng C−K mod 26, lặp khóa BUY; chỉ ghép các ô có dấu sao trong nguồn.
''',
'tonghop3':r'''
autokey|Ghép SIA với phần đầu UNSTOPPABLE để tạo khóa chạy rồi cộng modulo 26; thử vài chữ đầu để loại.
mode|Mã hóa CFB cần bản mã bước trước; phân biệt khả năng song song khi mã hóa với khi giải mã.
math|Phần tử sinh có các lũy thừa phủ toàn nhóm; kiểm tra điều kiện về cấp và khoảng số mũ trong hình.
mode|Xét phụ thuộc dữ liệu của CFB khi mã hóa; việc bộ mã khối có thể chạy song song không xóa phụ thuộc này.
math|Bậc phải chia 72; tính bậc của từng ứng viên bằng các ước tăng dần, không chỉ so giá trị số.
rsa|Thử m^211 mod 1517 bằng từng phương án; cách này kiểm tra giải mã mà không phải dựng lại khóa.
block|Mã dòng tạo keystream trước khi kết hợp với bản rõ; đừng phân loại theo lời khẳng định tốc độ tuyệt đối.
caesar|Không gian khóa dịch vòng khác với toàn bộ hoán vị bảng chữ cái; kiểm tra dấu giai thừa.
math|481 có hai thừa số nguyên tố lẻ khác nhau; kiểm tra tính cyclic trước khi đếm số phần tử sinh.
ecc|So độ dài khóa ở cùng mức an toàn, không phát biểu rằng có chứng minh tuyệt đối hơn/kém RSA.
hash|Phân biệt hàm tóm lược một chiều với phép mã hóa có thể giải ngược khi có khóa.
affine|Thử (a,b) vào cả hai cặp 20→13 và 14→23; một cặp khớp chưa đủ xác nhận khóa.
ecc|Khóa công khai là 6G; dùng 2G,4G rồi cộng lại, kiểm tra dấu y khi cộng điểm.
elgamal|Phân biệt logarit rời rạc trên nhóm hữu hạn với bài toán phân tích số nguyên và biến thể trên đường cong.
triple|Đếm số khóa DES độc lập tối đa trong cấu hình EDE, không nhầm số lượt thao tác với số bit khóa.
desbox|100011 cho hàng từ hai bit ngoài và cột từ bốn bit giữa; nguồn tô cả A và C giống nhau nên không chấm một chữ cái.
aeskey|Số từ mở rộng bằng bốn lần số khóa vòng, bao gồm khóa khởi tạo trước vòng đầu.
gf|91 là byte hex có bit cao 1; áp xtime với bước rút gọn, không chỉ dịch và bỏ tràn.
math|Bậc của một phần tử sinh phải là 22; chỉ cần thử các ước nguyên tố của 22 để loại nhanh.
math|Bậc của a luôn chia cấp nhóm; phân biệt φ(n) với φ(φ(n)) trong các khẳng định của hình.
math|41 nguyên tố nên bậc phần tử sinh phải là 40; thử số mũ 20 và 8 cho mỗi ứng viên.
math|Theo cột bit 117 đọc từ thấp lên cao; A luôn bình phương, b chỉ nhân A khi bit ki bằng 1.
knapsack|Tính W×si mod M rồi đặt theo p; nguồn ghi miền hoán vị sáu phần tử nhưng lại dùng bảy, cần kiểm tra ghi chú.
public|So bài toán nền của RSA với Rabin, ElGamal và Merkle–Hellman; không dựa vào cùng kích thước khóa.
math|Phân tích 667 rồi áp tính nhân của φ cho các thừa số nguyên tố khác nhau.
desbox|Phân biệt đầu vào hàm f gồm R và khóa vòng với đầu vào riêng tầng mở rộng; nguồn thiếu chữ trong tiêu chí phủ định.
elgamal|y2 = m×β^k mod p; ưu tiên dùng β trong khóa công khai thay vì suy lại từ a nếu dữ kiện không khớp.
math|Bậc của 12 phải chia 36; thử lần lượt các ước thích hợp và chọn số mũ nhỏ nhất cho dư 1.
hash|Hàm băm không có thao tác giải mã bằng khóa; phân biệt one-way với bảo mật bằng thuật toán mã hóa.
hill|Thử mỗi ma trận trong hình lên cặp FR theo quy ước vector hàng; loại khóa không tạo cặp EB.
rabin|Kiểm tra c=m^2 mod pq trước, rồi thử bình phương lại cả bốn nghiệm được đưa ra.
aesround|Suy số vòng từ số từ khóa Nk thay vì từ số byte bản rõ; AES-128 không đổi số vòng theo thông điệp.
signature|Ký bằng m^d mod n, xác minh bằng e; giữ riêng modulo n và φ(n) khi kiểm tra từng phát biểu.
deskey|Đếm số khóa vòng DES; từ “khác nhau” cần lưu ý ngoại lệ khóa yếu, không coi là định lý cho mọi khóa.
knapsack|Với dãy siêu tăng, mỗi phần tử phải lớn hơn toàn tổng trước nó; vét cạn xét tất cả tập con.
math|Chỉ nhóm modulo dạng 2p^k với p lẻ nguyên tố trong các lựa chọn mới có thể cyclic.
hash|Hàm băm hỗ trợ phát hiện thay đổi khi bản băm tham chiếu đáng tin; không tự coi nó là bảo mật nội dung.
mode|Phân biệt mã hóa CBC nối tiếp với CTR/ECB; “CRT” trong nguồn được giữ nguyên, không đổi sang thuật toán số học.
math|Chỉ cần tìm một ước chung lớn hơn 1 ở từng cặp; tránh kiểm tra tính nguyên tố từng số riêng lẻ.
aeskey|SubWord tra độc lập bốn byte 68,A7,6D,79 trong S-box; giữ đúng thứ tự và so cả bốn byte.
''',
'tonghop4':r'''
vigenere|Mỗi vị trí Vigenère thực hiện một phép dịch vòng do ký tự khóa quyết định; không phải phép nhân Affine.
otp|Với yêu cầu mật hoàn thiện, khóa phải đủ số khả năng cho toàn bộ bản rõ; kiểm tra bất đẳng thức trong đáp án.
autokey|So việc nối bản rõ vào mầm khóa với việc lặp từ khóa; hai cơ chế không đồng nhất.
affine|Tìm điều kiện khả nghịch của a modulo 26; việc chỉ nói (a,b) thuộc Z26 là chưa đủ.
rc4|PRGA thực hiện swap S[i],S[j]; phân biệt hai vị trí được trao đổi với mọi ô của mảng S.
rc4|Nguồn có hai phương án in cùng một khoảng độ dài khóa; đọc cảnh báo thay vì phân biệt bằng vị trí.
hill|Đổi từng khóa bốn chữ thành ma trận 2×2 rồi thử mã hóa cặp WE trước; kiểm tra cả chiều vector hàng.
caesar|Thử giải CFMVCPURP bằng từng khóa rồi đọc bản rõ; chỉ dựa vào “có nghĩa” chưa phải bằng chứng duy nhất.
affine|Thử a×18+b≡0 và a×14+b≡6 mod 26; cần khớp đồng thời cả hai.
transpose|Với 24 chữ chia sáu cột, đọc ngược từng cột bản mã vào bảng rồi lấy bốn vị trí 8,16,19,23.
affine|Từ C→H và H→E lập hai đồng dư; tìm a khả nghịch rồi giải bản mã ở bốn ô abcd.
vigenere|Lặp KHONG, cộng với PHUONGPHAPKISO theo A=0; thử vài vị trí khác nhau vì các phương án gần giống nhau.
hill|Ở đây nguồn đã cho k^−1; nhân từng cặp QC,TO với ma trận giải, không nghịch đảo nó thêm lần nữa.
hill|Tính nghịch đảo ma trận khóa trước khi áp vào EY,UJ; kiểm tra lại bằng cách mã hóa bản rõ ứng viên.
hill|Tính det A mod 26 rồi nhân ma trận phụ hợp với nghịch đảo định thức; thử A×A^−1 để xác nhận.
hill|Thử trực tiếp mã hóa LO và VE với từng ma trận đã cho; giữ quy ước vector hàng trong tài liệu môn học.
autokey|Khóa chạy = KEY nối bản rõ, cắt đúng độ dài; thử ký tự thứ ba rồi kiểm tra phần sau khi hết mầm khóa.
transpose|Chia bản rõ thành các nhóm bốn ký tự, áp đúng chiều π; giữ cả dấu chấm vì nguồn đưa nó vào bản rõ.
affine|Dùng C=(5P+24) mod 26; thử những vị trí làm các đáp án khác nhau để giảm phép tính.
otp|So độ dài bản mã và khóa trước; nếu không bằng nhau thì chưa thể áp phép Vernam theo toàn chuỗi.
otp|Dùng cách đánh số chữ đúng quy ước Vernam của tài liệu; khác quy ước cộng/XOR sẽ cho bản mã khác.
affine|Tính a=gcd(667,1196), b=3a mod 26 rồi thử 1–2 ký tự phân biệt của HARDWORKING.
classic|Đảo thứ tự hai tầng: giải Vigenère bằng LONDON trước, rồi dùng nghịch đảo 3 để giải Affine.
classic|Đảo hoán vị năm ký tự trước rồi trừ khóa MONEY modulo 26; đừng giải theo thứ tự mã hóa.
des|Viết phép biến đổi Feistel đảo rồi so thứ tự khóa; không cần xây dựng một hàm f nghịch đảo.
des|Mỗi vòng chỉ tác động một nửa qua hàm f; xét ảnh hưởng tới số vòng cần dùng, không suy rằng giải mã giống là yếu.
triple|Xét cấu hình nhiều khóa độc lập của Triple DES; một khóa dùng lại không làm tăng số khóa độc lập.
des|Đếm vòng Feistel, không cộng IP và IP^−1 thành vòng mã hóa riêng.
desbox|Trong f, mở rộng R rồi trộn khóa, thay thế và hoán vị; chú ý đại lượng đầu ra của cả hàm.
des|Đây là kích thước khối dữ liệu vào, không phải độ dài khóa hữu ích hoặc đầu vào tầng S-box.
desbox|Số ô của IP phải phủ một khối dữ liệu DES; kiểm tra tích hàng×cột.
des|Nhận diện cấu trúc tách nửa và đổi chỗ; không lấy số khóa vòng làm loại mã dòng/mã khối.
desbox|Đầu vào tám S-box được chia từ 48 bit và đầu ra ghép thành 32 bit; suy kích thước mỗi hộp.
des|Tách ba đại lượng số vòng, khóa hiệu dụng, khối dữ liệu; đừng dùng độ dài khóa có parity cho cột khóa hiệu dụng.
symmetric|Xét quan hệ giữa khóa mã và khóa giải của DES, không dựa vào số hộp thế để phân loại.
mode|Đối chiếu tên chuẩn ECB,CBC,CFB; một từ “feedback” gần giống chưa đủ là tên chế độ thật.
deskey|Tám bit parity không tăng không gian khóa cần vét cạn; phân biệt khóa nạp vào với khóa hữu ích.
deskey|Vòng 1,2,9,16 dùng lịch dịch khác các vòng còn lại; kiểm tra đúng số vòng trong phát biểu.
deskey|Xét số khóa con được dùng qua các vòng; lưu ý khóa yếu có thể khiến các khóa con trùng nhau.
desbox|S-box phải tạo quan hệ phi tuyến; so kỹ chiều phụ thuộc đầu vào/đầu ra trong phát biểu tuyến tính.
des|Kiểm tra loại đại lượng: kích thước khối dữ liệu không phải số bit khóa hiệu dụng.
desprop|Xét khóa yếu có làm hai lần mã hóa trở về đầu vào không; phân biệt khóa yếu với cặp khóa bán yếu.
triple|Mã hóa hai tầng dùng hai phép E; giải phải đảo thứ tự hai phép D, không thay E bằng D khi viết mã hóa.
lfsr|Tính XOR ở các nhánh hồi tiếp rồi dịch trạng thái; xuất chuỗi a8…a0 theo đúng mẫu trong ảnh.
ksa|Ở i=1 phải mang j từ vòng i=0; tính j modulo 256 rồi đọc hai giá trị sau swap.
desbox|Với mỗi ô đích abcd, đọc số ở bảng IP rồi lấy bit nguồn đánh số từ 1; không nhầm chỉ số ô và bit.
des|Ở vòng kế tiếp L bằng R của vòng trước; chỉ cần lấy tám bit đầu của nửa phải được cho.
desbox|Chuỗi thuộc B3 nên tra S3; hai bit biên chọn hàng, bốn bit giữa chọn cột rồi đổi kết quả sang bốn bit.
desbox|Đọc chỉ số P tại từng ô ABCD, lấy bit C đúng vị trí đó; giữ thứ tự A,B,C,D khi ghép.
desbox|XOR từng bit của E(R) với khóa vòng rồi lấy tám bit bên phải; không tra S-box ở bước này.
''',
}

def reviewed_rows(stem):
    return [tuple(line.split('|',1)) for line in REVIEW_TEXT[stem].strip().splitlines()]

# Explicit defects observed in the ORIGINAL source, not speculative OCR edits.
SOURCE_ISSUES = {
 'chuong1':{2:'Thân câu thiếu tiêu chí ĐÚNG/SAI.',10:'Thân câu thiếu tiêu chí ĐÚNG/SAI.',11:'Tiêu chí “KHÔNG” bị cụt.',14:'Thân câu thiếu tiêu chí ĐÚNG/SAI.',15:'Thân câu thiếu tiêu chí ĐÚNG/SAI.',16:'Thân câu thiếu tiêu chí ĐÚNG/SAI.'},
 'chuong2':{38:'Nguồn bỏ trống Rcon[j].',39:'Nguồn bỏ trống g(w3).',49:'Nhận xét “thường gặp nhất” không nêu mô hình/ngữ cảnh.'},
 'chuong3':{1:'Cả khẳng định về chứng minh bài toán khó và thay thế hệ đối xứng đều cần xem lại.',22:'Hai phát biểu Fermat dạng a^p ≡ a (một phát biểu giới hạn a chẵn) cùng đúng.',23:'Công thức đếm yêu cầu p,q là hai số nguyên tố lẻ; nguồn chưa nêu lẻ.',24:'Hai khoảng số mũ đóng/mở đều tạo cùng tập vì α^φ(n)=1; nhiều phát biểu đúng.',43:'Hình ghi nhóm Z*19 nhưng phần yêu cầu lại ghi Z*10.'},
 'tonghop1':{1:'Nguồn thiếu từ ĐÚNG/SAI.',4:'Nguồn thiếu chỉ số Sij cần tính.',6:'Nguồn thiếu từ ĐÚNG/SAI.',7:'Nguồn không chứa hình đầu vào và vị trí abcd.',9:'Nguồn thiếu từ ĐÚNG/SAI.',17:'Dãy/hoán vị có 6 phần tử nhưng mỗi phương án chỉ có 5.',20:'Nguồn thiếu từ ĐÚNG/SAI.',28:'Nguồn thiếu từ ĐÚNG/SAI.',38:'RSA và họ ElGamal đều có sơ đồ mã hóa/chữ ký; nhiều phát biểu đúng.'},
 'tonghop2':{4:'Nguồn thiếu từ ĐÚNG/SAI.',8:'Nguồn không có bảng S2 được nhắc tới.',17:'Nguồn thiếu từ ĐÚNG/SAI.',18:'Nguồn thiếu từ ĐÚNG/SAI.',20:'Nguồn thiếu từ ĐÚNG/SAI.',23:'Nguồn không có hình C và vị trí ABCD.',24:'Nguồn thiếu từ ĐÚNG/SAI.',27:'Công thức số phần tử sinh cần giả thiết nhóm cyclic.',34:'Phương án A in “1r”, giữ nguyên thay vì đoán số.'},
 'tonghop3':{10:'Nguồn thiếu từ ĐÚNG/SAI.',16:'Hai phương án A,C cùng là 1100 và đều tô vàng.',23:'Nguồn ghi hoán vị của 6 phần tử nhưng cho 7 giá trị và dãy 7 phần tử; M còn nhỏ hơn tổng dãy.',26:'Nguồn thiếu từ trong tiêu chí phủ định; đầu vào f gồm R và khóa vòng nên phát biểu B cần ngữ cảnh.',34:'Từ “khác nhau” không đúng với mọi khóa DES; có ngoại lệ khóa yếu.'},
 'tonghop4':{6:'A và B in cùng một khoảng độ dài khóa, chỉ B được gạch chân.',8:'Nguồn không cho bản rõ hay điều kiện xác định duy nhất khóa dịch vòng.',20:'Bản mã 16 chữ nhưng khóa 15 chữ; nguồn thiếu ký tự hoặc quy ước kéo dài khóa.',21:'Cần xác nhận quy ước Vernam: A=0 và cộng modulo 26 không cho phương án nào.',39:'Từ “khác nhau” không đúng với mọi khóa DES; có ngoại lệ khóa yếu.'},
}
