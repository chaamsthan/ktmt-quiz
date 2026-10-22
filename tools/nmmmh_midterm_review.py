"""Manually source-compared transcription of all 46 PDF screenshot pages.

Rows are question units, not screenshot units. Missing 21–23 in Ca 1 are
reported separately; repeated screenshots of one question are not new records.
Options remain in the exact visible Forms order, including letter-only choices.
Keys below are independent decisions, NEVER copied from selected radio buttons.
"""
ROWS=[]

def row(ca,n,pages,topic,stem,options,key=None,proof='',crop=None,issue=''):
    assert len(options)==4
    ROWS.append(dict(ca=ca,number=n,pages=pages if isinstance(pages,list) else [pages],topic=topic,
                     stem=stem,options=options,key=key,proof=proof,crop=crop,issue=issue))

row(1,1,2,'math','Tìm cấp của phần tử a = 3 trên Z*59.',['15','58','59','29'],
    'D','Duyệt d tăng dần: số mũ d nhỏ nhất có pow(3,d,59)=1 là 29.',(2,448,145,830,194))
row(1,2,2,'gf','Chọn đáp án SAI về trạng thái, đa thức và đơn vị xử lý AES (nhãn trong hình).',list('CBAD'),
    'B','Nhãn B trong hình thiếu x^4 và x trong đa thức AES; các phát biểu còn lại phù hợp FIPS 197.',(2,448,395,832,522))
row(1,3,1,'math','Điều kiện để x là phần tử sinh của Z*101 (nhãn A–D trong hình).',list('BADC'),
    'D','101 nguyên tố, 100=2²×5²; x phải có x^50≠1 và x^20≠1 mod 101. Nhãn C của hình là lựa chọn thứ tư.',(1,448,160,829,358))
row(1,4,1,'shannon','Nguyên lí thiết kế mã khối của Shannon bao gồm:',
    ['Xáo trộn và khuếch tán.','Xáo trộn và thay thế','Khuếch tán, hoán vị và thay thế','Xáo trộn và hoán vị'],'A',
    'Hai mục tiêu là confusion và diffusion; thay thế/hoán vị là công cụ thực hiện, không phải cả hai mục tiêu.')
row(1,5,3,'mode','[Thân câu không xuất hiện trong PDF; chỉ còn bốn phương án về CFB.]',
    ['Cơ chế móc xích của CFB làm cho khối mã thứ i chỉ phụ thuộc vào các khối rõ trước đó',
     'Trong chế độ mã khối CFB lỗi bit trong một khối mã đơn lẻ sẽ chỉ ảnh hưởng việc giải mã của các khối tiếp theo.',
     'Trong chế độ mã khối CFB, quá trình mã hóa không thực hiện đối với bản rõ mà biến đổi IV hoặc bản mã của khối trước đó.',
     'CFB không có khả năng tự đồng bộ'],issue='Thiếu toàn bộ thân câu 5; không biết yêu cầu ĐÚNG hay SAI.')
row(1,6,[3,4],'ksa','Trong KSA của RC4, tại i=1 với T[0]=215, T[1]=227, sau lệnh swap hãy cho S[i],S[j].',
    ['(167,1)','(217,1)','(227,1)','(187,1)'],'D','Mô phỏng KSA: i=0 cho j=215; i=1 cho j=(215+1+227)%256=187; sau swap S[1]=187,S[187]=1.',(3,448,345,830,536))
row(1,7,4,'attack','Kẻ tấn công thám mã để tìm khóa được sử dụng trong quá trình mã hóa từ một số thông điệp được mã hóa, đó là hình thức tấn công nào?',
    ['Tấn công với bản mã được chọn','Tấn công chỉ với bản rõ','Tấn công với bản rõ đã biết','Tấn công chỉ với bản mã'],'D',
    'Dữ kiện chỉ gồm các thông điệp đã mã hóa, không có cặp bản rõ hay oracle lựa chọn.')
row(1,8,[4,5],'desbox','DES: tìm 8 bit ngoài cùng bên phải của E(R) XOR K theo hai chuỗi bit trong hình.',
    ['00110110','00010110','01011110','00001110'],crop=(4,448,451,831,514),
    issue='Chưa chốt được toàn bộ hai chuỗi bit nhỏ trong ảnh; không lấy lựa chọn đang tích làm kết quả.')
row(1,9,5,'block','Triển khai phần cứng thích hợp với loại nào hơn trong các lựa chọn sau?',
    ['ECB và OFB','Mã dòng','DES','AES'],issue='So sánh tốc độ/khả năng triển khai không có tiêu chí hay mô hình phần cứng xác định.')
row(1,10,5,'gf','Tính xtime(A4) ở hệ hex. Đáp án ghi đủ 2 ký tự.',
    ['53','48','56','68'],'A','xtime(0xA4)=((0xA4<<1)^0x11B)&255=0x53.',(5,448,411,829,450))
row(1,11,[5,6],'hill','Giải bản mã DKAD bằng Hill với ma trận giải k^−1 = [[13,10],[20,23]].',
    ['CARE','NEAR','FAIR','PAIR'],'C','A=0, vector hàng: DK×k^-1=(5,0)=FA, AD×k^-1=(8,17)=IR; kết quả FAIR.',(6,448,247,829,290))
row(1,12,6,'elgamal','A chọn p=2003 và một phần tử sinh của Z*2003. A cần chọn giá trị khóa riêng trong khoảng nào?',
    ['[1, 2001]','[1, 2003]','[1, 2002]','[2, 2000]'],
    issue='Theo HAC miền chuẩn là 1..p−2: A đầy đủ, D là một tập con hợp lệ; C thuộc quy ước mở rộng khác. Cách hỏi khoảng chưa xác định duy nhất.',crop=(6,448,498,830,553))
row(1,13,7,'desbox','Trong DES, cho B4=100101₂, tìm chuỗi bit thay thế qua hộp S4 trong hình.',
    ['1100','0000','1111','0001'],'B','Hai bit biên 11 cho hàng 3; bốn bit giữa 0010 cho cột 2; S4[3][2]=0 → 0000.',(7,448,104,830,352))
row(1,14,7,'symmetric','Lựa chọn khẳng định SAI về mật mã khóa đối xứng:',
    ['Khóa mã hóa của mật mã khóa đối xứng cần phải giữ bí mật và được bên gửi và nhận trao đổi trên kênh truyền an toàn.',
     'Mật mã khóa đối xứng thường có khả năng mã hóa/giải mã thông điệp nhanh hơn mật mã bất đối xứng.',
     'Trong mật mã khóa đối xứng khóa mã hóa và khóa giải mã là giống nhau hoặc dễ dàng suy ra nhau.',
     'Khóa của mật mã khóa đối xứng là cặp (khóa riêng; khóa công khai).'],'D','Cặp công khai/riêng thuộc mô hình bất đối xứng.')
row(1,15,8,'shift','Cho biết x13 và x32 sau ShiftRows của trạng thái trong hình.',
    ['4F, B2','A5, B2','4F, 46','A5, 87'],'A','Dịch trái hàng 1 một byte cho x13=4F; hàng 3 ba byte cho x32=B2.',(8,448,185,830,338))
row(1,16,8,'des','DES sử dụng mạng Feistel có đặc điểm là:',
    ['Quá trình mã hóa và giải mã là ngược nhau nhưng thứ tự khóa sử dụng giống nhau.',
     'Quá trình mã hóa và giải mã là ngược nhau.',
     'Mỗi vòng mã chỉ thực hiện biến đổi nửa trái của khối dữ liệu.',
     'Quá trình mã hóa và giải mã là đồng nhất chỉ khác ở thứ tự khóa con.'],'D',
    'Mạng Feistel giải mã bằng cùng cấu trúc, sử dụng khóa vòng theo thứ tự đảo.')
row(1,17,9,'math','Trên nhóm nhân Z*n, khẳng định nào ĐÚNG? (nhãn trong hình).',list('DCBA'),
    crop=(9,448,158,830,303),issue='Cần xác nhận ký hiệu số mũ ở A; nếu là φ(n), cả A và D đều đúng. Không chốt bằng lựa chọn tích trên ảnh.')
row(1,18,[9,10],'mode','Khẳng định nào sau đây là ĐÚNG?',
    ['Trong chế độ OFB các bản mã thu được chỉ phụ thuộc vào các bản rõ đầu vào.',
     'Nếu các khối bản rõ giống nhau được mã hóa với cùng một khóa và một IV theo chế độ CBC thì sẽ thu được các khối mã giống nhau.',
     'Trong chế độ ECB hai khối bản rõ giống nhau nhưng khác nhau vector IV thì cho ra hai khối bản mã khác nhau.',
     'Trong chế độ ECB một hay nhiều bit sai trong một khối mã đơn lẻ sẽ ảnh hưởng tới việc giải mã của các khối sau đó.'],
    issue='Bỏ qua vị trí khối/lịch sử móc xích khiến phát biểu CBC không đúng tổng quát; ba phát biểu còn lại sai. Không có đáp án duy nhất đủ chặt chẽ.')
row(1,19,10,'deskey','Khẳng định nào sau đây về thuật toán DES là ĐÚNG?',
    ['Thuật toán DES sử dụng 16 khóa con, mỗi khóa XOR với nửa trái hoặc phải của bản rõ/bản mã trong 16 vòng mã hóa/giải mã.',
     'Thuật toán DES sử dụng 16 khóa con, mỗi khóa tách ra thành 2 nửa trái và phải khi thực hiện mỗi vòng mã hóa/giải mã.',
     'Thuật toán DES sử dụng 16 khóa con, mỗi khóa XOR với nửa trái của bản rõ/bản mã trong 16 vòng mã hóa/giải mã.',
     'Thuật toán DES có 16 khóa con để sử dụng trong các vòng mã hóa/giải mã.'],'D','DES tạo 16 khóa vòng 48 bit; chúng XOR với E(R), không trực tiếp với nửa trái/phải 32 bit.')
row(1,20,10,'math','Hàm Phi Euler có tính chất φ(mn)=φ(m)φ(n) khi nào? (nhãn trong hình).',list('ACBD'),
    'C','Tính nhân của hàm Euler áp dụng khi gcd(m,n)=1; đó là nhãn B, lựa chọn thứ ba.',(10,448,432,830,567))
row(1,24,11,'ecc','Cho P,Q trên đường cong E(a,b). Khẳng định nào SAI? (công thức và nhãn trong hình).',list('ACDB'),
    'A','Điểm vô cực O là phần tử đơn vị: P+O=P, không phải O.',(11,448,116,830,188))
row(1,25,11,'aes','Chọn đáp án SAI về thuật toán mã khối Rijndael:',
    ['Độ dài của khóa không cần bằng với độ dài của khối dữ liệu','Khóa có độ dài tối đa là 256 bit',
     'Độ dài của khối phải chia hết cho 32','Khóa có độ dài tối đa là 512 bit'],'D','Thiết kế Rijndael gốc hỗ trợ độ dài khóa tới 256 bit, không phải 512 bit.')
row(1,26,[11,12],'rc4','Độ dài của khóa RC4 là:',
    ['40 – 256 bit','40 – 2048 bit','128 – 2048 bit','256 – 2048 bit'],'B','Theo thông số RC4 trong tài liệu môn học: khóa 5..256 byte. Không nhầm với mảng trạng thái S.')
row(1,27,12,'gf','Trong AES, tính 53_H × 2A_H trên GF(2^8) với m(x)=x^8+x^4+x^3+x+1.',
    ['76','86','43','2A'],'B','Nhân đa thức nhị phân và rút gọn modulo 0x11B: gf_mul(0x53,0x2A)=0x86.',(12,448,187,830,228))
row(1,28,[12,13],'lfsr','LFSR n=9, trạng thái ban đầu (1,0,1,1,0,1,0,0,0), phản hồi a0 XOR a3 XOR a5 XOR a8. Xuất a8…a0 tại t=1.',
    ['1000101001','1000101101','0000101101','1000111101'],crop=(12,448,402,830,682),
    issue='Nguồn yêu cầu 9 bit nhưng cả bốn phương án đều có 10 bit. Không tự xóa một bit để khớp đáp án.')
row(1,30,13,'math','Số phần tử sinh của nhóm nhân Z*19036 là?',
    ['2880','9534','3981','9516'],crop=(13,448,468,830,510),
    issue='19036 chia hết cho 4 và lớn hơn 4 nên nhóm nhân không cyclic, có 0 phần tử sinh; không có phương án 0.')
row(1,29,13,'public','Phát biểu nào sau đây về hệ mật khóa công khai là ĐÚNG?',
    ['Thường được xây dựng dựa trên các bài toán khó đã biết.','Có thể đảm bảo được độ an toàn vô điều kiện.',
     'Có độ an toàn không cao.','Ra đời nhằm thay thế cho các hệ mật khóa bí mật.'],'A','Các hệ thực dụng như RSA/ElGamal dựa vào giả thiết khó tính toán, không phải an toàn vô điều kiện.')
row(1,31,14,'elgamal','Chọn công thức giải mã ElGamal đúng theo y1=α^k, y2=xβ^k mod p (nhãn trong hình).',list('ACDB'),
    'C','β=α^a nên β^k=y1^a; x=y2×y1^(−a) mod p là nhãn D, lựa chọn thứ ba.',(14,448,147,830,263))
row(1,32,14,'math','Chọn đáp án ĐÚNG về định lí Fermat nhỏ (nhãn trong hình).',
    ['C','B','A',''],crop=(14,448,469,830,617),
    issue='Cả dạng a^p≡a cho a dương nhỏ hơn p và trường hợp a chẵn đều đúng; phương án thứ tư bị cắt khỏi nguồn.')
row(1,33,15,'mix','Tính x32 sau MixColumns của trạng thái AES trong hình.',
    ['C6','D8','D3','C1'],crop=(15,448,175,831,265),
    issue='Phép tính cho D6; phương án thứ hai nhìn giống D8 ở độ phân giải nguồn. Chưa xác nhận được ký tự, không tự sửa để khớp.')
row(1,34,15,'desbox','Cho biết các bit còn thiếu abcd trong đầu ra IP(x) của DES theo hình.',
    ['1010','1110','1101',''],crop=(15,448,463,831,599),
    issue='Phương án D bị cắt; cần nguồn đầy đủ và đối chiếu các ô nhỏ trước khi chấm.')
row(1,35,16,'aes','Kích thước khóa tối đa cho phép trong thuật toán mã Rijndael là:',
    ['192 bit','1024 bit','64 bit','256 bit'],'D','Độ dài khóa tối đa của Rijndael gốc là 256 bit.')
row(1,36,16,'rsa','Tính bảo mật của RSA dựa trên tính khó của …',
    ['Bài toán kiểm tra số nguyên tố','Lựa chọn thừa số nguyên tố','Bài toán phân tích một số nguyên thành thừa số nguyên tố','Bài toán tìm số nguyên tố'],'C',
    'Nền tảng giả thiết an toàn trong phạm vi môn là tính khó phân tích n=pq; không tuyên bố RSA đã được chứng minh tương đương bài toán này.')
row(1,37,16,'elgamal','ElGamal: p=211, α=116, a=64, k=76, x=81. Tính y1.',
    ['204','209','170','178'],'B','pow(116,76,211)=209; y1 không phụ thuộc a hoặc x.',(16,448,529,831,581))
row(1,38,17,'knapsack','Lựa chọn đáp án ĐÚNG cho thành phần của khóa riêng Merkle–Hellman:',
    ['(112 117 229 465 929 1857)','(112 115 229 458 919 1830)',
     '(112 117 233 465 929 1857)','(112 117 232 462 922 1857)'],'C','Kiểm tra nghiêm ngặt mỗi phần tử lớn hơn tổng tất cả phần tử trước nó; chỉ dãy thứ ba thỏa.')
row(1,39,17,'triple','Số lượng khóa khác nhau tối đa có thể sử dụng khi mã hóa bằng Triple DES là:',
    ['5','4','3','2'],'C','Cấu hình EDE ba khóa độc lập có ba khóa DES; không nhầm với các biến thể hai khóa.')
row(1,40,17,'des','Kích thước khối dữ liệu đầu vào của thuật toán DES là:',
    ['64 bit','128 bit','256 bit','192 bit'],'A','FIPS 46-3 quy định một khối dữ liệu DES có 64 bit.')

row(2,1,5,'gf','Trong AES, tính 60_H × 8_H trên GF(2^8) với đa thức rút gọn AES.',
    ['45','34','5A','A6'],crop=(5,512,144,1319,218))
row(2,2,[5,6],'math','Chọn đáp án ĐÚNG với n=pq, p,q là hai số nguyên tố p≠q. (Những công thức trong hình.)',list('ABCD'),
    'C','Với p,q lẻ, CRT cho |Q_n|=(p−1)(q−1)/4, nhãn C.',(6,512,140,1319,585),
    issue='Công thức cần giả thiết p,q lẻ; nguồn chưa nêu điều kiện này.')
row(2,3,7,'gf','Tính xtime(D3)_H. Đáp án hex ghi đủ hai ký tự.',
    ['CA','BD','3B','33'],'B','((0xD3<<1)^0x11B)&255=0xBD.',(7,512,259,1319,300))
row(2,4,7,'des','Chọn đáp án ĐÚNG về nhược điểm của mạng Feistel:',
    ['Chưa đáp ứng được đủ hai yêu cầu của Shannon về tính xáo trộn và khuếch tán',
     'Không tạo ra sự khuếch tán dữ liệu khi mã hóa',
     'Mỗi vòng mã hóa chỉ thực hiện biến đổi nửa phải của khối dữ liệu nên cần số vòng mã hóa lớn để đảm bảo an toàn của hệ mật, điều này làm giảm đáng kể tốc độ mã.',
     'Quá trình mã và giải mã có trình tự giống nhau chỉ khác nhau thứ tự khóa sử dụng nên dễ bị tấn công hơn.'],'C',
    'Phép cập nhật Feistel chỉ áp f lên một nửa khối mỗi vòng; số vòng cần để khuếch tán là đánh đổi cấu trúc, không phải bằng chứng yếu vì giải mã dùng chung cấu trúc.')
row(2,5,8,'desbox','Kích thước của hoán vị IP trong DES là:',
    ['4 × 16','7 × 8','8 × 8','8 × 6'],'C','Bảng IP chuẩn FIPS 46-3 được trình bày 8 hàng × 8 cột, phủ đủ 64 bit.')
row(2,6,8,'mode','Chế độ mã khối nào có thể xử lí mã hóa song song?',
    ['ECB và CTR','OFB và CTR','CBC và CTR','ECB'],issue='A liệt kê hai chế độ đúng nhưng D cũng nêu một chế độ đúng; nếu yêu cầu duy nhất phải ghi “đầy đủ nhất”.')
row(2,7,9,'lfsr','LFSR n=8, ban đầu (1,0,0,1,0,0,1,1), f=a1 XOR a2 XOR a4 XOR a6. Tìm a7…a0 tại t=1.',
    ['011001001','111001010','110010010','111001001'],crop=(9,512,345,1319,727),
    issue='Yêu cầu 8 bit nhưng tất cả phương án in 9 bit; không tự sửa chuỗi để chọn một phương án.')
row(2,8,10,'attack','Sử dụng cách tấn công vét cạn hiệu quả khi',
    ['Không gian khóa tồn tại khóa nửa yếu','Không gian khóa có lực lượng nhỏ','Không gian khóa tồn tại khóa yếu','Không gian khóa tồn tại điểm bất động'],
    'B','Số lần thử vét cạn tỷ lệ lực lượng không gian khóa; sự tồn tại khóa yếu không làm nhỏ toàn bộ không gian.')
row(2,9,10,'aesround','AES-256 thực hiện bao nhiêu vòng lặp?',
    ['10','12','16','14'],'D','Nk=256/32=8, Nr=Nk+6=14 theo FIPS 197.')
row(2,10,1,'elgamal','A và B sử dụng ElGamal, p=307. Khi mã hóa B chọn thêm số ngẫu nhiên k. B nên chọn k trong khoảng nào?',
    ['[0, 306]','[54, 150]','[45, 306]','[1, 307]'],'B',
    'HAC chọn k từ 1 đến p−2=305. B là khoảng duy nhất nằm hoàn toàn trong miền này; các khoảng khác chứa 0 hoặc p−1/p.')
row(2,11,1,'vigenere','Đâu là bản mã của ENGLISH bằng Vigenère với khóa NOW?',
    ['RBCYWQU','RBCYWOU','RBCYWOV','RBCYTOU'],'B','A=0, cộng từng chữ với NOW lặp: ENGLISH + NOWNOWN = RBCYWOU.')
row(2,12,11,'block','Khẳng định nào sau đây về mã khối là SAI?',
    ['Khóa của mã khối là đối xứng.','Bản rõ có kích thước cố định','Hoạt động tương tự mã dòng','Sử dụng cặp khóa công khai và khóa riêng để mã và giải mã.'],
    issue='D sai với mã khối đối xứng; C không mô tả tương đồng cụ thể và cũng có thể sai theo cách phân loại của môn. Cần đáp án chuẩn/giải thích tiêu chí.')
row(2,13,11,'hybrid','Phương pháp mật mã lai nào hiệu quả nhất để trao đổi lượng lớn thông tin nhạy cảm?',
    ['Sử dụng khóa riêng của người gửi để kí và dùng khóa công khai của người nhận để mã hóa.',
     'Phối hợp sử dụng khóa công khai và khóa riêng của cả bên gửi và bên nhận một cách phù hợp để mã hóa/giải mã và kí số.',
     'Sử dụng khóa công khai của người nhận để mã hóa và dùng khóa riêng của người nhận để giải mã.',
     'Trao đổi khóa bí mật dùng hệ mật khóa công khai sau đó dùng khóa bí mật này để mã hóa thông điệp.'],'D',
    'Mật mã lai dùng hệ công khai để thiết lập/bọc khóa phiên, sau đó mã đối xứng xử lý khối dữ liệu lớn.')
row(2,14,12,'security','Hệ mật khóa bí mật đảm bảo tính chất an toàn nào của thông tin?',
    ['Tính sẵn sàng và chống chối bỏ','Tính bí mật, toàn vẹn và sẵn sàng','Tính bí mật','Tính bí mật và sẵn sàng'],'C',
    'Phép mã hóa đối xứng đơn thuần cung cấp tính bí mật; không tự cung cấp khả dụng hay chống chối bỏ.')
row(2,15,12,'aeskey','Kích thước khóa mở rộng của AES-192 là bao nhiêu?',
    ['56 từ','44 từ','52 từ','50 từ'],'C','AES-192 có Nr=12; 4×(12+1)=52 từ 32 bit.')
row(2,16,13,'math','Tìm cấp của phần tử a=7 trên Z*59.',
    ['29','58','36','14'],'A','Duyệt d từ 1: pow(7,d,59)=1 lần đầu ở d=29.',(13,512,352,1319,437))
row(2,17,[13,14,15],'deskey','DES: K=0000 1010 1110 1001 1001 0110 1100 1101 1110 0010 0000 1111 0100 1011 1011 0011. Tìm bốn bit đầu PC-1(K).',
    ['1001','1011','1010','1110'],'A','PC-1 bắt đầu 57,49,41,33. Lấy các bit 1-based của chuỗi K cho 1001.',
    (14,512,89,1319,979))
row(2,18,15,'desbox','Thuật toán DES có bao nhiêu hộp thế?',
    ['14','12','10','8'],'D','DES chia đầu vào 48 bit thành tám khối 6 bit, qua S1..S8.')
row(2,19,16,'shift','Cho biết x10 và x21 sau ShiftRows trên trạng thái AES trong hình.',
    ['A3, FE','26, 9F','3F, 20','EE, 6C'],'A','Dịch trái hàng 1 một byte và hàng 2 hai byte: x10=A3,x21=FE.',(16,512,435,1319,720))
row(2,20,17,'knapsack','Độ phức tạp vét cạn giải bài toán xếp ba lô với n phần tử (nhãn trong hình).',list('DACB'),
    'A','Mỗi phần tử có hai trạng thái lấy/không lấy, tổng 2^n tập con; nhãn D là lựa chọn thứ nhất.',(17,512,360,1319,545))
row(2,21,[17,18],'security','Mật mã có tác dụng',
    ['Đảm bảo tính toàn vẹn, bí mật và kịp thời của dữ liệu.','Đảm bảo bí mật, xác thực và kịp thời của dữ liệu.',
     'Đảm bảo tính toàn vẹn, bí mật và xác thực của dữ liệu.','Đảm bảo tính toàn vẹn, bí mật, xác thực và sẵn sàng của dữ liệu.'],'C',
    'Các cơ chế mật mã có thể cung cấp bí mật, toàn vẹn và xác thực; không bảo đảm hệ thống luôn sẵn sàng/kịp thời.')
row(2,22,18,'symmetric','Khẳng định nào sau đây ĐÚNG về hệ mật mã đối xứng?',
    ['Mỗi bên sử dụng khóa bí mật của riêng mình để mã hóa.','Hai bên thỏa thuận trước để dùng chung một khóa.',
     'Mỗi bên gửi cho bên còn lại một phần khóa riêng của mình để sử dụng',
     'Hai bên không cần thỏa thuận trước vì từ khóa của riêng mình có thể dễ dàng suy ra khóa chung'],'B',
    'Trong mô hình mã đối xứng cơ bản, hai bên dùng chung bí mật hoặc các khóa dễ suy ra nhau.')
row(2,23,19,'rsa','RSA p=37,q=53,e=19,d=1675. Số điểm bất động ứng với tham số này là:',
    ['12','57','24','10'],'B','(1+gcd(18,36))×(1+gcd(18,52))=19×3=57; kiểm tra thêm bằng duyệt m^19=m mod 1961.')
row(2,24,19,'knapsack','Lựa chọn đáp án ĐÚNG cho thành phần khóa riêng Merkle–Hellman:',
    ['(109 114 227 453 905 1809)','(109 115 227 454 905 1810)',
     '(109 114 227 453 905 1809)','(109 112 223 453 895 1819)'],
    issue='Hai lựa chọn A,C giống nhau và đều là dãy siêu tăng; không thể chấm một nhãn duy nhất.')
row(2,25,20,'desbox','Khẳng định nào về DES là SAI? (nhãn trong hình).',list('BDAC'),
    'D','S-box DES phi tuyến; nhãn C khẳng định phụ thuộc tuyến tính là sai, nằm ở lựa chọn thứ tư.',(20,512,334,1319,577))
row(2,26,21,'mix','Tính x12 trong vòng MixColumns AES với ma trận trong hình.',
    ['A2','13','0D','B1'],crop=(21,512,480,1319,654))
row(2,27,2,'rc4','Thuật toán nào sau đây là mã dòng?',
    ['RC4, RC2','RC4, RC5','RC4, RC6','RC4'],'D','RC2,RC5,RC6 là mã khối; RC4 là mã dòng.')
row(2,28,[2,22],'desbox','Trong DES, nguồn ghi B5=101011₂ nhưng phần yêu cầu lại ghi tìm chuỗi thay thế B3; các hộp S3,S4,S5 trong hình.',
    ['1100','0001','1110','1010'],crop=(22,512,173,1319,677),
    issue='Nguồn mâu thuẫn B5/B3. Tra S5 cho 1110 nhưng tra S3 cho 1001 (không có phương án); không tự sửa chỉ số nguồn.')
row(2,29,23,'rsa','Trong RSA, khẳng định nào SAI? (nhãn trong hình).',list('ADCB'),
    'D','Điều kiện là gcd(e,φ(n))=1, không bắt buộc gcd(e,n)=1. Nhãn B trong hình là lựa chọn thứ tư.',(23,512,317,1319,499))
row(2,30,[23,24],'math','Số các thặng dư bậc 2 theo modulo 41 của Z*97 là:',
    ['40','90','48','96'],crop=(24,512,16,1319,82),
    issue='Nguồn đồng thời ghi modulo 41 và Z*97. Không thay 41 bằng 97 để ép đáp án 48; cần xác minh đề gốc.')
row(2,31,24,'knapsack','Merkle–Hellman: π=(9,2,4,8,5,1,7,3,6), s=(135,143,285,569,1137,2273,4545,9089,18177), W=103,M=36357,c=106752,W^−1=18355. Tìm thông điệp ban đầu.',
    ['010011101','011011101','001011101','111011101'],'B','Giải ba lô sau khi nhân nghịch đảo W; thử mã hóa lại 011011101 với khóa công khai cho tổng 106752.')
row(2,32,25,'aes','Chọn đáp án SAI về Rijndael:',
    ['Có thể được cài đặt trên thẻ thông minh','Độ dài của khối dữ liệu là 64 bit','Khóa có thể có độ dài là 256 bit.',
     'Các phép biến đổi trong vòng lặp có thể nghịch đảo được'],'B','Rijndael không có khối 64 bit trong thiết kế gốc; các độ dài khối bắt đầu từ 128 bit theo bước 32 bit.')
row(2,33,[25,26],'ksa','KSA RC4: i=1,T[0]=233,T[1]=108. Sau swap, S[i],S[j] bằng bao nhiêu?',
    ['(46,1)','(56,1)','(86,1)','(96,1)'],'C','i=0 cho j=233; i=1 cho j=(233+1+108)%256=86; sau swap là (86,1).',(26,512,296,1319,694))
row(2,34,27,'math','Nếu gcd(b,c)=1, hệ x≡a mod b và x≡a mod c có nghiệm nào? (nhãn trong hình).',
    ['C','','',''],crop=(27,512,337,1319,877),
    issue='Chỉ lựa chọn thứ nhất C xuất hiện; ba lựa chọn sau bị cắt khỏi PDF. Công thức đúng là nhãn D trong hình nhưng chưa biết vị trí lựa chọn.')
row(2,35,28,'mode','Chế độ nào cho phép giải mã khối thứ i mà không cần giải các mã khối từ khối thứ nhất tới i−1?',
    ['ECB, CBC','CTR, CFB','CBC','CFB, OFB'],
    issue='ECB,CBC,CTR và CFB đều giải mã một khối mà không giải mã các khối trước (CBC/CFB chỉ cần bản mã trước). Nhiều lựa chọn đúng theo đúng câu chữ.')
row(2,36,28,'hill','Bản rõ milk được mã hóa Hill m=2 thành AMVU. Hãy chọn khóa mã hóa đúng.',
    ['OSKB','MAIG','LCDF','GJNK'],'C','A=0, ma trận từ LCDF=[[11,2],[3,5]], vector hàng: MI→AM và LK→VU. Thử tất cả bốn khóa để xác nhận duy nhất.')
row(2,37,3,'autokey','Lựa chọn khẳng định ĐÚNG về các hệ mật cổ điển (nhãn trong hình).',list('BDCA'),
    'A','Nhãn B mô tả khóa chạy nối bản rõ sau mầm khóa; là lựa chọn thứ nhất.',(3,512,146,1319,539))
row(2,38,4,'des','DES: L2R2=0010 1011 1100 0001 1011 0000 1110 0001 0100 0110 0000 1111 0000 1111 0010 0011. Tìm tám bit cao nhất của L3.',
    ['00101011','00100011','11100001','01000110'],'D','L3=R2 nên lấy tám bit đầu nửa phải 32 bit: 01000110.',(4,512,219,1319,286))
row(2,39,[4,29],'math','Phần tử sinh nhỏ nhất của Z*97 là:',
    ['6','5','4','3'],'B','Duyệt x từ 2 theo tiêu chuẩn x^48≠1 và x^32≠1 mod97: số nhỏ nhất là 5. Lựa chọn đang tích trên ảnh là 4, KHÔNG dùng làm khóa.',(4,512,730,1319,819))
row(2,40,29,'math','α là phần tử sinh của Z*n nếu: (nhãn trong hình).',list('CABD'),
    crop=(29,512,457,1319,704),issue='Nhãn A dùng tập lũy thừa từ 0 tới φ(n), B từ 0 tới φ(n)−1; hai tập bằng nhau khi α sinh. Hai lựa chọn B,C trên giao diện đều đúng.')

# Final native-pixel crop review (coordinates never inferred from resized UI).
for r in ROWS:
    corrected={
      (1,15):(8,448,185,832,344),
      (1,28):(12,448,423,833,649),
      (2,1):(5,512,342,1326,413),
      (2,2):(6,512,313,1326,625),
      (2,17):(14,509,273,1320,987),
      (2,30):(24,512,191,1320,255),
      (2,37):(3,512,339,1320,584),
    }
    if (r['ca'],r['number']) in corrected:r['crop']=corrected[(r['ca'],r['number'])]
    if (r['ca'],r['number'])==(1,17):
        r.update(key='A',issue='',proof='Ảnh gốc A ghi a^(φ(n)−1), không phải φ(n). Cấp nhóm nhân Z*n là φ(n), nhãn D là lựa chọn thứ nhất.')
    if (r['ca'],r['number'])==(2,17):
        r['issue']='Bảng PC-1 trong nguồn bị ngắt giữa trang 14–15, hàng gần cuối không đủ; bốn vị trí cần tính ở hàng đầu vẫn đọc được.'
