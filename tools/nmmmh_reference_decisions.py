"""Explicit, reference-backed repairs. Never infer a missing input from a key.

Page numbers refer to PDF pages (1-based), not printed slide numbers. Exercises
with irrecoverable inputs remain pending; new distractors are editorial repairs,
not claims about the original document. Originals are frozen separately.
"""
import copy
import json
import math
from pathlib import Path

from nmmmh_numeric_audit import phi, order, jacobi, gf_mul, hill

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / 'subjects/nmmmh/audit/single-answer-review'
LETTERS = 'ABCD'


def decisions():
    originals = json.loads((AUDIT/'original_questions.json').read_text())
    result = {}

    def add(id, key, pages, reason, *, stem=None, options=None, checks=None, hint=None, numeric=None, typed=False):
        q = originals[id]
        assert id not in result and key in LETTERS and pages
        texts = {l: q[l]['text'] for l in LETTERS}
        texts.update(options or {})
        assert checks and set(checks) == set(LETTERS), id
        assert [l for l in LETTERS if checks[l]['matches']] == [key], id
        result[id] = dict(id=id, correct_answer=key, question=stem or q['question'], options=texts,
                          reference_pages=pages, reason=reason, option_checks=checks, numeric=numeric,
                          hint=hint or 'Mẹo: Đọc đúng yêu cầu và kiểm tra từng phương án theo điều kiện đã nêu.',
                          typed=typed, status='verified')

    def fit(key, reasons):
        assert len(reasons) == 4
        return {l: {'matches': l == key, 'reason': why} for l, why in zip(LETTERS, reasons)}

    def number(id, expected, pages, reason, *, replacements=None, stem=None, hint=None, base=10, typed=False):
        q = originals[id]; opts = {l:q[l]['text'] for l in LETTERS};opts.update(replacements or {})
        values = {l:(int(t,base) if t != 'Không tồn tại' else None) for l,t in opts.items()}
        checks = {l:{'matches':v==expected,'value':v,'reason':f'Giá trị phương án {v}; kết quả tính độc lập {expected}.'} for l,v in values.items()}
        keys = [l for l in LETTERS if checks[l]['matches']];assert len(keys)==1,(id,keys)
        add(id,keys[0],pages,reason,stem=stem,options=replacements,checks=checks,hint=hint,numeric={'expected':expected,'base':base,'values':values},typed=typed)

    # ECB/CBC/OFB: fix the overbroad claim about separate equal blocks and
    # changing keys. OFB is scoped to the first full output block (bijection).
    cbc = 'Trong CBC, hai lần mã hóa cùng TOÀN BỘ dãy bản rõ, cùng khóa và cùng IV cho cùng dãy bản mã.'
    ofb = 'Trong OFB, với cùng khóa và cùng khối rõ đầu tiên, hai IV khác nhau cho hai khối mã đầu tiên khác nhau.'
    for suffix,key,cbc_l,ofb_l in [('de-thi-nmmmh-4','A','B','C'),('de-thi-mat-ma-2021-trac-nghiem-12','D','A','C'),('de-thi-k16-2-13','B','D','C')]:
        reasons = ['Phát biểu phù hợp công thức chế độ.']*4
        reasons[LETTERS.index(key)] = 'SAI: lỗi một khối mã ECB không lan sang các khối giải mã sau.'
        add('nmmmh-'+suffix,key,[140,141,142,146,148],
            'Làm rõ CBC theo toàn thông điệp; loại khẳng định quá mạnh về đổi khóa; OFB xét khối đầu đầy đủ.',
            options={cbc_l:cbc,ofb_l:ofb},checks=fit(key,reasons),
            hint='Mẹo: ECB giải mã từng khối độc lập. Với CBC phải xét cả khối mã trước; OFB dùng đầu ra mã hóa IV làm dòng khóa.')
    id='nmmmh-de-thi-k16-3-2045'
    add(id,'A',[140,142,146], 'Làm rõ phạm vi cả thông điệp trong phát biểu CBC sai.',
        options={'A':cbc.replace('cho cùng dãy bản mã','luôn cho hai dãy bản mã khác nhau'),'C':ofb},
        checks=fit('A',['SAI: mã hóa xác định cho cùng dữ liệu, khóa và IV.','ECB giữ tính bằng nhau của hai khối dưới cùng khóa.','E_K là song ánh trên khối IV.','Lỗi ECB chỉ ảnh hưởng chính khối đó.']),
        hint='Mẹo: Cố định bản rõ, khóa và IV thì công thức mã hóa không có nguồn ngẫu nhiên mới.')

    # The document explicitly uses a broad course definition of authentication.
    for suffix,key in [('de-thi-nmmmh-5','D'),('de-thi-mat-ma-2021-trac-nghiem-23','D'),('de-thi-k16-2-36','D'),('de-thi-k16-3-2038','C')]:
        reasons=['Chỉ liệt kê một phần, chưa ĐẦY ĐỦ ba khía cạnh.']*4;reasons[LETTERS.index(key)]='Đủ toàn vẹn, danh tính/nguồn gốc và chống chối từ theo nghĩa rộng của tài liệu.'
        add('nmmmh-'+suffix,key,[192], 'Theo slide 137; hỏi danh sách đầy đủ, không coi MAC riêng lẻ là chống chối bỏ.',
            stem='Theo phạm vi xác thực mẫu tin ở slide 137 trong tài liệu môn học (nghĩa rộng), phương án nào liệt kê ĐẦY ĐỦ các khía cạnh?',checks=fit(key,reasons),
            hint='Mẹo: Tìm danh sách bao quát tất cả các mục tiêu nêu trong bài; phân biệt phạm vi bài học với bảo đảm của riêng MAC.')

    for suffix,key,a,k,focus in [('de-thi-nmmmh-7','B',117,33,'cipher'),('de-thi-mat-ma-2021-trac-nghiem-20','B',117,33,'cipher'),('de-thi-k16-2-26','C',113,67,'cipher'),('de-thi-k16-3-2047','D',117,33,'decrypt')]:
        id='nmmmh-'+suffix;q=originals[id]; beta=pow(41,a,211);gamma=pow(41,k,211);delta=56*pow(beta,k,211)%211
        prompt='Phương án nào nêu ĐÚNG cặp bản mã (γ, δ) của thông điệp đã cho?' if focus=='cipher' else 'Phương án nào nêu ĐÚNG phép khôi phục bản rõ từ cặp bản mã đã cho?'
        # Restrict the requested object rather than pretend other true
        # statements (e.g. the public key) are mathematically false.
        cut=q['question'].rfind('Khẳng định');stem=(q['question'][:cut] if cut>=0 else q['question']+' ')+prompt
        why=[('Không trả lời đúng đối tượng được hỏi; '+q[l]['text']) for l in LETTERS]
        why[LETTERS.index(key)]=f'β={beta}, γ={gamma}, δ={delta}; m=δ(γ^a)^−1 mod 211=56.'
        add(id,key,[186], 'Giới hạn rõ đối tượng cần chọn; không phủ nhận các mệnh đề đúng về đối tượng khác.',stem=stem,checks=fit(key,why),
            hint='Mẹo: Chỉ xét phương án trả lời đúng đối tượng hỏi. Tính γ=α^k và δ=mβ^k modulo p; khi giải mã dùng nghịch đảo γ^a.',numeric={'beta':beta,'gamma':gamma,'delta':delta,'plaintext':delta*pow(pow(gamma,a,211),-1,211)%211})

    for suffix,key,label in [('de-thi-nmmmh-9','B','D'),('de-thi-mat-ma-2021-trac-nghiem-29','A','B'),('de-thi-k16-2-24','B','C'),('de-thi-k16-3-2056','D','C')]:
        reasons=['Đúng theo định nghĩa đồng dư và đại diện chuẩn.']*4;reasons[LETTERS.index(key)]='SAI: phép chia Euclid cho phép số dư bằng 0, ví dụ 7 chia 7.'
        add('nmmmh-'+suffix,key,[171,172], 'Sửa cách gọi các đại diện cùng lớp; không sao chép lỗi 0<r trong slide phép chia.',
            options={label:'−7, 0, 7, 14, … là các đại diện thuộc CÙNG MỘT lớp đồng dư modulo 7.'},checks=fit(key,reasons),
            hint='Mẹo: Thử trường hợp chia hết. Các số hơn kém nhau một bội của mô-đun nằm cùng một lớp đồng dư.')

    for suffix,key,label in [('de-thi-nmmmh-28','A','B'),('de-thi-mat-ma-2021-trac-nghiem-37','B','A'),('de-thi-k16-2-40','A','D'),('de-thi-k16-3-2046','B','D'),('de-cuong-2025-chuong3-1','D','A')]:
        reasons=['Đúng trong mô hình hệ mật công khai thông thường của môn học.']*4;reasons[LETTERS.index(key)]='SAI: mật mã công khai bổ sung, không thay thế toàn bộ mật mã đối xứng.'
        add('nmmmh-'+suffix,key,[183,191,192], 'Phân biệt giả thiết độ khó với định lý đã chứng minh; làm rõ thay thế toàn bộ.',
            options={label:'An toàn của hệ mật khóa công khai thường dựa trên GIẢ THIẾT một bài toán là khó về mặt tính toán.',key:'Mật mã khóa công khai ra đời để thay thế HOÀN TOÀN mật mã khóa bí mật trong mọi ứng dụng.'},checks=fit(key,reasons),
            hint='Mẹo: Hệ lai dùng khóa công khai để thiết lập khóa, còn dữ liệu lớn vẫn mã hóa đối xứng; đừng đồng nhất giả thiết khó với chứng minh độ khó.')

    for suffix in ['de-thi-nmmmh-29','de-thi-mat-ma-2021-trac-nghiem-26']:
        id='nmmmh-'+suffix;q=originals[id]; c=pow(1234,2,199*211)
        add(id,'B',[185], 'Hỏi riêng giá trị bản mã để loại sự nhập nhằng giữa đầu vào thuật toán và kết quả mã hóa.',
            stem=q['question'].split('Khẳng định')[0]+'Phương án nào nêu ĐÚNG giá trị bản mã c của m = 1234?',
            options={'A':'Đầu vào phép lấy căn của bản mã đã cho là c=11153, p=199, q=211.'},
            checks=fit('B',['Sai giá trị đầu vào: c thực tế là 11152, không phải 11153.',f'c=m² mod pq={c}.','Danh sách căn tương ứng m=1234, không phải m=1731.','Không thể tất cả đúng vì hai mệnh đề sai.']),
            hint='Mẹo: Chỉ cần bình phương bản rõ rồi lấy dư modulo pq; không cần tính bốn căn.',numeric={'n':199*211,'ciphertext':c})
    number('nmmmh-de-thi-k16-2-35',phi(765),[175,176], 'Không phương án nguồn nào bằng φ(765); sửa một phương án, giữ nguyên n và thứ tự nhãn.',replacements={'A':'384'},hint='Mẹo: Phân tích 765=3²×5×17; tính n∏(1−1/p) với mỗi ước nguyên tố chỉ lấy một lần.')
    id='nmmmh-de-thi-k16-3-2036'
    add(id,'C',[185], 'Sửa giá trị bản mã thiếu một chữ số trong một phương án, theo phép tính độc lập.',options={'C':'Bản mã c = 11152.'},
        checks=fit('C',['Mô-đun phải là 199×211=41989, không phải 49189.','1152 không bằng 1234² mod 41989.','11152=1234² mod 41989.','Các căn này không ứng với bản rõ 1731.']),numeric={'ciphertext':pow(1234,2,199*211)},hint='Mẹo: Tính pq trước rồi bình phương m lấy dư; để ý phương án thiếu chữ số.')

    for suffix in ['de-thi-nmmmh-32','de-thi-mat-ma-2021-trac-nghiem-39']:
        add('nmmmh-'+suffix,'D',[199,202,203], 'Nêu rõ mô hình TA của tài liệu và yêu cầu tập hợp đầy đủ.',
            stem='Theo mô hình TA và các định nghĩa chứng thực, thỏa thuận, phân phối khóa trong tài liệu môn học, phương án nào tổng hợp ĐẦY ĐỦ các phát biểu đúng sau đây?',
            options={'B':'Thỏa thuận khóa thiết lập khóa bí mật chung với sự tham gia đóng góp của các bên; không chỉ là một bên chuyển sẵn khóa cho bên kia.'},
            checks=fit('D',['Đúng nhưng chỉ nêu chứng thực.','Đúng nhưng chỉ nêu thỏa thuận.','Đúng trong mô hình TA, nhưng chỉ nêu phân phối.','Tổng hợp đủ ba nhận định đúng.']),hint='Mẹo: Phân biệt ba việc: gắn danh tính với khóa, cùng đóng góp tạo khóa, và TA phân phối thông tin khóa.')
    add('nmmmh-de-thi-k16-2-37','A',[199,202,203], 'Làm rõ mô hình giáo trình; thay phát biểu mơ hồ bằng hạn chế sai có phản ví dụ DH.',
        stem='Theo mô hình TA trong tài liệu môn học, khẳng định nào sau đây là SAI?',
        options={'A':'Thỏa thuận khóa bí mật chỉ có thể thực hiện nếu các bên đã có sẵn một kênh truyền bí mật.'},
        checks=fit('A',['DH thiết lập khóa chung qua kênh công khai; xác thực là yêu cầu riêng.','Đúng trong mô hình TA đang xét.','Chứng thực liên kết danh tính và khóa công khai.','Đúng về vai trò TA trong mô hình tài liệu.']),hint='Mẹo: Nhớ mục đích của Diffie–Hellman: thiết lập khóa qua kênh không an toàn; chống giả mạo cần thêm xác thực.')
    add('nmmmh-de-thi-k16-2-4','C',[15,192,193], 'Hỏi danh sách đầy đủ; yêu cầu bảo vệ giá trị băm tham chiếu.',
        stem='Phương án nào liệt kê ĐẦY ĐỦ ba kỹ thuật có thể dùng kiểm tra toàn vẹn trong tài liệu? Với hàm băm đơn, giả sử giá trị băm tham chiếu được bảo vệ tin cậy.',
        checks=fit('C',['Chỉ hàm băm, chưa đủ ba kỹ thuật.','Chỉ MAC, chưa đủ ba kỹ thuật.','Đủ chữ ký số, hàm băm, MAC.','Chỉ chữ ký số, chưa đủ ba kỹ thuật.']),hint='Mẹo: Câu hỏi yêu cầu danh sách đầy đủ, không chỉ một công cụ hợp lệ; digest không được tin cậy thì không chống sửa dữ liệu.')
    add('nmmmh-de-thi-k16-2-7','A',[193,194], 'Làm rõ tính xác định của hàm băm và sửa định nghĩa tiền ảnh thứ hai.',
        options={'A':'Cùng một hàm băm mật mã, cùng đầu vào vẫn có thể cho các đầu ra ngẫu nhiên khác nhau ở mỗi lần băm.',
                 'D':'Kháng tiền ảnh thứ hai: với x đã cho, không khả thi về tính toán để tìm x′≠x sao cho h(x′)=h(x).'},
        checks=fit('A',['SAI: hàm băm là xác định.','Đúng: định nghĩa kháng va chạm.','Đúng: kháng tiền ảnh.','Đúng: đầu vào gốc x được cho trước.']),hint='Mẹo: Phân biệt ba bài toán: tìm đầu vào từ digest, tìm đầu vào thứ hai cho x có sẵn, và tìm bất kỳ cặp va chạm.')
    add('nmmmh-de-thi-k16-2-11','C',[184], 'Chuẩn hóa f(n) thành φ(n) theo công thức sinh khóa RSA trong tài liệu.',
        options={'A':'Khóa bí mật có thể tính bằng d ≡ e⁻¹ (mod φ(n)).'},
        checks=fit('C',['Đúng vì ed≡1 mod φ(n).','Phân tích n là cơ sở độ khó thông thường; không khẳng định tương đương đã được chứng minh.','SAI: điều kiện cần là gcd(e,φ(n))=1, không phải gcd(e,n)=1.','Đúng: mã hóa RSA lấy modulo n.']),hint='Mẹo: Khi chọn số mũ dùng φ(n), khi mã hóa dùng n; hai mô-đun này không được đổi chỗ.')
    add('nmmmh-de-thi-k16-2-25','B',[84], 'Thay khẳng định cấp bit mơ hồ bằng phát biểu sai rõ ràng.',
        options={'D':'Nguyên lý Shannon chỉ áp dụng lên từng bit độc lập, không thể áp dụng phép thế trên byte.'},
        checks=fit('B',['Gán nhầm mục tiêu confusion/diffusion.','Đúng: hai mục tiêu confusion và diffusion.','Gán nhầm mục tiêu confusion/diffusion.','Sai: AES thực hiện phép thế byte và khuếch tán.']),hint='Mẹo: Tách mục tiêu thiết kế (confusion/diffusion) khỏi công cụ thực hiện (thay thế/hoán vị).')
    add('nmmmh-de-thi-k16-3-2052','B',[178,179], 'Xác định ký hiệu trên mẫu hợp số là Jacobi; n trong quy tắc cho 2 là số dương lẻ.',
        stem='Chọn khẳng định SAI. Ký hiệu (a/n) là Jacobi khi n là hợp số dương lẻ, và là Legendre khi n là nguyên tố lẻ; trong quy tắc cho 2, n là số dương lẻ.',
        checks=fit('B',['Bốn căn của 4 modulo 21 là 2,5,16,19.','SAI: Jacobi(21,235)=1, không phải −1.','Legendre(13,17)=1 vì 8²≡13 mod 17.','Đúng theo quy tắc bổ sung cho ký hiệu Jacobi.']),numeric={'jacobi_21_235':jacobi(21,235)},hint='Mẹo: Tách mẫu 235=5×47 rồi nhân hai ký hiệu; khi mẫu hợp số không dùng định nghĩa Legendre trực tiếp.')

    # Missing question verbs in native DOCX, with course-scoped definitions.
    simple=[
      ('chuong1',2,'B',[21,23],'Phát biểu nào sau đây là ĐÚNG về mã hóa dữ liệu?',{'A':'Mã hóa dữ liệu CHỈ được sử dụng trong lĩnh vực quân sự.'},['Sai: có cả ứng dụng dân sự.','Đúng: chuyển bản rõ thành bản mã.','Đó là che giấu thông tin, không phải mục tiêu định nghĩa mã hóa.','Băm/chữ ký không thay thế phép mã hóa bảo mật.'],'Mẹo: Phân biệt che giấu nội dung với che giấu sự tồn tại của thông điệp.'),
      ('chuong1',10,'C',[24,191],'Theo mô hình mã hóa đối xứng và chữ ký số thông thường trong môn học, phát biểu nào ĐÚNG?',{},['Chữ ký số thông thường dùng khóa riêng/công khai.','Mô tả hệ bất đối xứng.','Đúng: phù hợp mã hóa dữ liệu lớn.','Khóa chung không xác định riêng người ký để chống chối bỏ.'],'Mẹo: Khóa chung phù hợp bảo mật nhanh, không phân biệt ai trong hai bên đã tạo thông điệp.'),
      ('chuong1',11,'D',[24,192],'Theo phân loại các hệ mật thông thường của môn học, khẳng định nào về mật mã đối xứng là KHÔNG ĐÚNG?',{},['Có thể bảo mật dữ liệu.','Dùng khóa chung theo mô hình môn học.','Mã khối và mã dòng đều đối xứng.','SAI: chữ ký số thông thường không dựa trên khóa chung.'],'Mẹo: Chữ ký số cần phân biệt người ký với người xác minh; khóa chung không đáp ứng việc đó.'),
      ('chuong1',14,'D',[84],'Theo mục tiêu khuếch tán/hiệu ứng thác lũ, khi lật một bit BẢN RÕ thì phát biểu nào mô tả ĐÚNG sự thay đổi mong muốn của bản mã?',{'D':'Khi lật một bit bản rõ, trung bình khoảng một nửa số bit bản mã thay đổi.'},['Hai bit không phải mức thác lũ mong muốn.','Nói về bit khóa, không trả lời yêu cầu về bit bản rõ.','Một bit không khuếch tán tốt.','Đúng về trung bình, không phải mọi bản rõ đều đúng chính xác nửa số bit.'],'Mẹo: Đọc xem bit bị lật thuộc bản rõ hay khóa; mục tiêu là khuếch tán trên toàn khối, không phải chỉ một vài bit.'),
      ('chuong1',15,'B',[24],'Khẳng định nào sau đây là ĐÚNG về mô hình dùng khóa chung của mật mã đối xứng?',{},['Hai khóa độc lập không đủ để mã/giải mã đối xứng.','Đúng: khóa chung được thiết lập an toàn trước khi sử dụng.','Không tự suy ra khóa chung từ hai khóa tùy ý.','Gửi một phần khóa riêng không phải định nghĩa đối xứng.'],'Mẹo: Xét xem hai bên có dùng cùng bí mật để mã và giải mã hay không.'),
      ('chuong1',16,'B',[84],'Theo nguyên lý confusion (xáo trộn), quan hệ nào cần được che giấu phức tạp khi đối thủ suy ra KHÓA từ BẢN MÃ?',{},['Quan hệ tuyến tính không đạt mục tiêu confusion.','Đúng: làm phức tạp quan hệ bản mã–khóa.','Không phải cặp đối tượng đang được hỏi.','Tuyến tính giúp phân tích khóa, trái mục tiêu.'],'Mẹo: Với confusion, chú ý quan hệ giữa quan sát của kẻ thám mã và bí mật cần suy ra.'),
      ('tonghop1',6,'D',[113,114],'Chọn phát biểu ĐÚNG về kiến trúc AES.',{},['AES không kết hợp mạng Feistel.','Không cần mạng khác trong mô tả chuẩn.','Không phải Feistel.','Đúng: mạng thay thế–hoán vị SPN.'],'Mẹo: AES cập nhật toàn trạng thái bằng các phép thay thế và khuếch tán, khác cấu trúc hai nửa Feistel.'),
      ('tonghop1',9,'D',[28,82],'Chọn phát biểu ĐÚNG theo phân loại hệ mật trong tài liệu.',{},['Vernam không bất đối xứng.','AES là đối xứng.','DES là mã khối.','Đúng: Vernam cộng dòng khóa với dữ liệu.'],'Mẹo: Tách hai trục phân loại: đối xứng/bất đối xứng và mã khối/mã dòng.'),
      ('tonghop1',20,'D',[21,23],'Chọn phát biểu ĐÚNG về khái niệm mã hóa dữ liệu để bảo mật.',{'A':'Mã hóa dùng hàm một chiều không có phép giải mã, nên ngay cả người biết khóa hợp lệ cũng không thể khôi phục bản rõ.'},['SAI: phải có phép giải mã cho người giữ khóa hợp lệ.','Dùng khóa riêng người gửi không mô tả bảo mật khóa công khai.','Có rất nhiều ứng dụng dân sự.','Đúng theo định nghĩa bản rõ–bản mã.'],'Mẹo: Mã hóa phải có cách khôi phục bản rõ cho người giữ khóa hợp lệ.'),
      ('tonghop1',28,'B',[113],'Chọn phát biểu ĐÚNG về số vòng và độ dài khóa AES.',{},['64 bit không phải khóa AES.','Đúng: 10/12/14 vòng với 128/192/256 bit.','64 bit không phải khóa AES.','196 không phải 192.'],'Mẹo: Nhớ số vòng AES bằng số từ 32 bit của khóa cộng 6, với ba kích cỡ chuẩn.'),
      ('tonghop2',24,'B',[82,113],'Chọn phát biểu ĐÚNG về AES và DES.',{},['AES là mã khối.','Đúng: DES dùng khóa đối xứng.','AES không bất đối xứng.','DES có 56 bit khóa hiệu dụng.'],'Mẹo: Cả AES lẫn DES đều là mã khối đối xứng; đừng nhầm kích cỡ khóa với kích cỡ khối.'),
      ('tonghop3',10,'D',[190,191],'Với cùng mức an toàn tính toán theo các kích cỡ khóa thông thường, phát biểu nào ĐÚNG khi so ECC với RSA?',{},['Không có chứng minh tuyệt đối rằng ECC kém an toàn.','Không có chứng minh tuyệt đối rằng ECC an toàn hơn.','ECC cần khóa ngắn hơn, không dài hơn.','Đúng: khóa ECC ngắn hơn tại mức an toàn tương đương.'],'Mẹo: So độ dài khóa phải giữ cùng mức an toàn, không so số bit khóa bằng nhau.'),
    ]
    for exam,n,key,pages,stem,opts,why,hint in simple:
        add(f'nmmmh-de-cuong-2025-{exam}-{n}',key,pages,'Khôi phục yêu cầu ĐÚNG/SAI và nêu rõ phạm vi từ định nghĩa trong tài liệu.',stem=stem,options=opts,checks=fit(key,why),hint=hint)

    add('nmmmh-de-cuong-2025-chuong2-49','C',[186], 'Bỏ tiêu chí phổ biến nhất không có khảo sát; hỏi đúng mô hình tấn công.',
        stem='Đối thủ được chọn bản mã và truy vấn kết quả giải mã của các bản mã khác bản mã mục tiêu. Đây là mô hình tấn công nào?',
        checks=fit('C',['Không mô tả vét cạn.','Không chỉ quan sát bản mã.','Đúng: chosen-ciphertext attack.','Đối thủ chọn bản mã, không phải bản rõ.']),hint='Mẹo: Phân loại bằng quyền truy vấn của đối thủ, không bằng tần suất xuất hiện của kiểu tấn công.')
    add('nmmmh-de-cuong-2025-tonghop1-1','C',[111,113,114], 'Thay so sánh mạnh hơn thiếu thước đo bằng so sánh kích cỡ khối xác định được.',
        stem='Chọn phát biểu ĐÚNG về AES và Triple DES.',options={'A':'Triple DES kiểu EDE thực hiện ba phép E_K liên tiếp, không có bước D_K.',
            'C':'AES xử lý khối 128 bit; Triple DES xử lý khối 64 bit.','D':'AES xử lý khối 64 bit; Triple DES xử lý khối 128 bit.'},
        checks=fit('C',['Triple DES dạng EDE có bước giải mã ở giữa, không phải ba phép E liên tiếp.','DES có 16 vòng, không ít hơn 10/12/14 vòng AES.','Đúng về kích thước khối, không phụ thuộc tốc độ phần cứng.','Đảo nhầm hai kích thước khối.']),hint='Mẹo: Dùng thông số thiết kế cố định để loại phương án, không suy từ tốc độ phần cứng.')
    add('nmmmh-de-cuong-2025-tonghop1-38','D',[192], 'Hỏi riêng các ứng dụng RSA; không coi phát biểu về ElGamal là sai.',
        stem='Phương án nào mô tả ĐẦY ĐỦ cả hai ứng dụng mã hóa và chữ ký số của RSA?',
        checks=fit('D',['Sai vì chữ chỉ loại ứng dụng chữ ký.','Sai vì chữ chỉ loại ứng dụng mã hóa.','Nói về ElGamal, không trả lời RSA được hỏi.','Đúng: RSA có các lược đồ mã hóa và lược đồ chữ ký; không dùng cùng phép toán thô trong triển khai an toàn.']),hint='Mẹo: Chỉ xét thuật toán đang được hỏi; phân biệt thuật toán nền với lược đồ mã hóa/chữ ký cụ thể.')
    add('nmmmh-de-cuong-2025-tonghop2-4','D',[184,198], 'Khôi phục ĐÚNG và kiểm chứng độc lập chữ ký RSA.',
        stem=originals['nmmmh-de-cuong-2025-tonghop2-4']['question'].replace('là ?','là ĐÚNG?'),
        checks=fit('D',['Ký dùng d=103, không dùng e=87.','n công khai, không phải bí mật.','Xác minh phải modulo n=1189, không phải 1113.','Đúng: φ=1120 và 103×87≡1 mod 1120.']),numeric={'n':41*29,'phi':40*28,'e':pow(103,-1,1120),'signature':pow(142,103,1189)},hint='Mẹo: Tính n và φ; thử e×d modulo φ. Ký dùng d, xác minh dùng e và mô-đun n.')
    add('nmmmh-de-cuong-2025-tonghop2-17','B',[85,86,99], 'Phân biệt tổng không gian khóa với số phép thử trung bình.',
        stem='Để duyệt TOÀN BỘ không gian khóa hiệu dụng DES bằng vét cạn, phải xét bao nhiêu khóa?',
        checks=fit('B',['48 là kích cỡ khóa vòng.','Đúng: 56 bit khóa hiệu dụng cho 2^56 khóa.','64 gồm tám bit kiểm tra chẵn lẻ.','32 là nửa khối, không phải khóa.']),hint='Mẹo: Loại tám bit chẵn lẻ trước khi đếm không gian khóa; câu hỏi không hỏi số phép thử trung bình.')
    add('nmmmh-de-cuong-2025-tonghop2-18','D',[192,198], 'Khôi phục yêu cầu đầy đủ, làm rõ phát biểu đánh đồng ký với mã hóa bảo mật.',
        stem='Phát biểu nào mô tả ĐÚNG và ĐẦY ĐỦ hai bảo đảm xác thực nguồn gốc và toàn vẹn của chữ ký số?',
        options={'B':'Bản thân chữ ký số luôn mã hóa bí mật toàn bộ nội dung dữ liệu.'},checks=fit('D',['Ký không đồng nghĩa mã hóa bảo mật.','Chữ ký không tự bảo mật nội dung.','Từ chỉ bỏ sót bảo đảm toàn vẹn.','Đúng: xác minh nguồn gốc và toàn vẹn với khóa công khai tin cậy.']),hint='Mẹo: Chữ ký không giấu nội dung; xét cả ai ký và nội dung có bị thay đổi hay không.')
    add('nmmmh-de-cuong-2025-tonghop2-20','A',[85,99], 'Nêu rõ đang đếm khóa nạp có bit parity, không phải entropy khóa.',
        stem='Chọn phát biểu ĐÚNG; độ dài khóa DES trong câu này tính CẢ tám bit kiểm tra chẵn lẻ.',
        checks=fit('A',['Đúng: biểu diễn khóa nạp 64 bit, chỉ 56 bit hiệu dụng.','DES có 16 vòng.','Khóa AES ngắn nhất 128 bit.','AES không dùng khóa 64 bit.']),hint='Mẹo: Đọc xem đề tính cả bit parity hay chỉ các bit bí mật hiệu dụng.')
    number('nmmmh-de-cuong-2025-tonghop2-34',16,[99], 'Chuẩn hóa ký tự phương án lỗi 1r thành một nhiễu số; số khóa vòng suy từ lịch DES, không từ nhiễu.',replacements={'A':'14'},hint='Mẹo: Mỗi vòng Feistel dùng một khóa con; đọc số vòng trong lịch sinh khóa DES.')
    for exam,n,wrong in [('tonghop3',34,'B'),('tonghop4',39,'A')]:
        id=f'nmmmh-de-cuong-2025-{exam}-{n}'
        add(id,'C',[99], 'Khóa vòng có thể trùng ở khóa yếu; bỏ từ khác nhau và làm rõ kích cỡ hai nửa khóa.',
            stem='Khẳng định nào sau đây về lịch khóa DES là ĐÚNG?',
            options={'C':'DES sinh một dãy 16 khóa con 48 bit cho 16 vòng; với khóa yếu, các giá trị khóa con có thể trùng nhau.',wrong:'Sau PC-1, DES chia khóa thành hai nửa 32 bit trong mỗi vòng.'},
            checks=fit('C',[('Sai: sau PC-1 là hai nửa 28 bit.' if l==wrong else 'Đúng: 16 khóa vòng, không bảo đảm 16 giá trị phân biệt.' if l=='C' else 'Sai số lượng khóa vòng DES.') for l in LETTERS]),hint='Mẹo: Sau PC-1 chỉ còn 56 bit, chia hai nửa; 16 vòng không có nghĩa luôn có 16 giá trị khóa phân biệt.')
    add('nmmmh-de-cuong-2025-tonghop3-26','B',[91,92,93,95], 'Khôi phục KHÔNG ĐÚNG; phân biệt đầu vào R với đầy đủ đối số hàm f(R,K).',
        stem='Phát biểu nào KHÔNG ĐÚNG về hàm f(R,K) trong một vòng DES?',options={'B':'Hàm f chỉ nhận duy nhất khối R 32 bit, không sử dụng khóa vòng K.'},
        checks=fit('B',['Tám S-box biến 48 thành 32 bit.','SAI: còn dùng khóa vòng K 48 bit để XOR với E(R).','Kết quả f dài 32 bit.','Bốn bước E, XOR khóa, S-box, P.']),hint='Mẹo: Theo dõi độ dài qua E → XOR K → S-box → P; f nhận cả dữ liệu và khóa vòng.')

    # Arithmetic checks based on visually readable original inputs.
    number('nmmmh-de-cuong-2025-chuong3-30',jacobi(2634,889785),[178,179], 'Ký hiệu Jacobi bằng 0 do gcd(2634,889785)=3; sửa khóa nguồn −1, không sửa dữ liệu.',hint='Mẹo: Tính gcd tử và mẫu trước. Nếu không nguyên tố cùng nhau thì không cần dùng luật tương hỗ.')
    number('nmmmh-de-cuong-2025-chuong3-39',phi(phi(4802)),[176], '4802=2×7^4 có nhóm đơn vị cyclic; φ(φ(4802))=588, không có trong phương án cũ.',replacements={'C':'588'},hint='Mẹo: Kiểm tra n có dạng 2p^k rồi tính φ hai lần; không lấy φ(n)/2 thay cho φ(φ(n)).')
    for id,plain,seed,slot,pages in [('nmmmh-de-thi-k16-3-2032','CRYPTOGRAPHY','SUN','A',[62,63]),('nmmmh-de-cuong-2025-tonghop3-1','UNSTOPPABLE','SIA','D',[62,63])]:
        key=(seed+plain)[:len(plain)];cipher=''.join(chr((ord(a)+ord(b)-130)%26+65) for a,b in zip(plain,key))
        opts={l:originals[id][l]['text'].upper() for l in LETTERS};opts[slot]=cipher
        add(id,slot,pages, 'Không có phương án cũ khớp khóa chạy; sửa một nhiễu thành bản mã tính độc lập.',options={slot:cipher},
            checks={l:{'matches':t==cipher,'reason':f'Tính khóa chạy bằng mầm nối bản rõ, thu {cipher}; phương án này là {t}.'} for l,t in opts.items()},numeric={'plaintext':plain,'seed':seed,'keystream':key,'ciphertext':cipher},hint='Mẹo: Nối mầm khóa với BẢN RÕ, không lặp mầm; cộng mã chữ A=0 modulo 26.')
    id='nmmmh-de-cuong-2025-tonghop4-16';cipher=hill('LOVE',[[9,2],[1,5]])
    add(id,'A',[54], 'Nhân vector hàng đúng quy ước tài liệu; bản mã là JOLK, không phải khóa nguồn C.',
        checks={l:{'matches':originals[id][l]['text']==cipher,'reason':f'LOVE×[[9,2],[1,5]] mod 26 = {cipher}.'} for l in LETTERS},numeric={'matrix':[[9,2],[1,5]],'plaintext':'LOVE','ciphertext':cipher},hint='Mẹo: Dùng vector HÀNG (L,O) nhân ma trận trước để loại nhanh; A=0.')
    id='nmmmh-de-cuong-2025-tonghop4-21';cipher=''.join(chr((ord(a)+ord(b)-130)%26+65) for a,b in zip('VERNAM','TOMJEY'))
    add(id,'C',[29,30], 'Tài liệu xác nhận Vernam trên chữ Latin cộng modulo 26; không dùng XOR mã ASCII.',
        stem=originals[id]['question']+' Dùng bảng chữ A=0,…,Z=25 và C=(P+K) mod 26 như ví dụ Vernam của tài liệu.',
        checks={l:{'matches':originals[id][l]['text']==cipher,'reason':f'Cộng từng cặp mã chữ modulo 26 được {cipher}.'} for l in LETTERS},numeric={'plaintext':'VERNAM','keystream':'TOMJEY','ciphertext':cipher},hint='Mẹo: Thử 2–3 chữ đầu bằng cộng modulo 26; không XOR các mã ký tự ASCII.')
    number('nmmmh-de-cuong-2025-tonghop3-16',12,[93,94], 'S1(100011) dùng hàng 3 cột 1, được 12; thay phương án C trùng A bằng nhiễu 1010.',replacements={'C':'1010'},base=2,hint='Mẹo: Hai bit ngoài chọn hàng, bốn bit giữa chọn cột; chỉ dùng hộp S1.')
    number('nmmmh-de-giua-ki-2026-ca-1-8',0xA5^0xB3,[91,92], 'Đọc trực tiếp tám bit cuối trên ảnh: E(R) kết thúc 10100101, K kết thúc 10110011; không cần đoán toàn chuỗi.',base=2,hint='Mẹo: Chỉ XOR tám bit cuối; XOR từng nhóm bốn bit rồi ghép lại.')
    number('nmmmh-de-giua-ki-2026-ca-1-33',gf_mul(3,0x0B)^0xFE^0x20^gf_mul(2,0x87),[123,124], 'Giữ nguyên ma trận nguồn; x32=03·0B XOR FE XOR 20 XOR 02·87=D6; sửa một phương án không khớp.',replacements={'B':'D6'},base=16,hint='Mẹo: Chỉ lấy hàng hệ số thứ tư và cột thứ ba (chỉ số từ 0); cộng bằng XOR và nhân trong GF(2^8).')
    number('nmmmh-de-giua-ki-2026-ca-2-1',gf_mul(0x60,8),[120,121,122], 'Nhân đa thức và rút gọn modulo 0x11B được 2D_H, không phải 45_H (45 thập phân mới bằng 2D_H).',replacements={'A':'2D'},base=16,hint='Mẹo: Nhân 08 là ba lần xtime; mỗi lần tràn bit 7 thì XOR 1B, giữ một byte. Các phương án đều là HEX.')
    number('nmmmh-de-giua-ki-2026-ca-2-26',0x0B^gf_mul(2,0xFE)^gf_mul(3,0x20)^0x87,[123,124], 'x12=0B XOR 02·FE XOR 03·20 XOR 87=0B; sửa một phương án, giữ nguyên ma trận.',replacements={'C':'0B'},base=16,hint='Mẹo: Hàng thứ hai nhân cột thứ ba (chỉ số từ 0); dùng 03·a=(02·a) XOR a.')
    number('nmmmh-de-giua-ki-2026-ca-1-30',0,[176], '19036 chia hết cho 4 và lớn hơn 4, không thuộc dạng có nhóm đơn vị cyclic; không áp φ hai lần.',replacements={'A':'0'},hint='Mẹo: Nhóm đơn vị có phần tử sinh chỉ với n=2,4,p^k,2p^k (p lẻ); kiểm tra dạng n trước khi tính φ.')

    add('nmmmh-de-giua-ki-2026-ca-1-18','B',[140,142,146], 'Sửa mệnh đề CBC mơ hồ thành phát biểu xác định về toàn thông điệp.',options={'B':cbc},
        checks=fit('B',['OFB còn phụ thuộc khóa và IV.','Đúng: cùng toàn thông điệp, khóa và IV.','ECB không dùng IV.','Lỗi ECB không lan sang các khối sau.']),hint='Mẹo: Viết C_i=E_K(P_i XOR C_(i−1)); cùng P_i riêng lẻ chưa đủ, cùng toàn thông điệp và IV thì đủ.')
    add('nmmmh-de-giua-ki-2026-ca-2-6','A',[140,141,146,149], 'Loại phương án ECB đơn lẻ là tập con của đáp án ghép; thay bằng OFB để bốn lựa chọn loại trừ nhau.',
        options={'D':'OFB'},checks=fit('A',['ECB độc lập khối, CTR có các bộ đếm tính độc lập.','OFB phụ thuộc đầu ra bước trước.','Mã hóa CBC phụ thuộc bản mã bước trước.','OFB không sinh song song các khối dòng khóa theo thuật toán chuẩn.']),hint='Mẹo: Chỉ xét MÃ HÓA: đầu vào E_K có cần kết quả E_K của bước trước hay không?')
    add('nmmmh-de-giua-ki-2026-ca-2-12','D',[82,137,138], 'Làm rõ khối đầu vào cố định và ý nghĩa mã khối kết hợp các chế độ, tránh phát biểu tương tự mã dòng quá rộng.',
        options={'B':'Mỗi khối đầu vào của phép mã khối có kích thước cố định.','C':'Có thể dùng chế độ hoạt động để xử lý thông điệp dài gồm nhiều khối.'},
        checks=fit('D',['Đúng theo định nghĩa mã khối đối xứng.','Đúng: độ dài khối là thông số cố định.','Đúng: ECB/CBC/CFB/OFB/CTR là các chế độ.','SAI: mã khối đối xứng không dùng cặp khóa công khai/riêng.']),hint='Mẹo: Phân biệt khối đầu vào cố định với toàn thông điệp có thể dài tùy ý.')
    id='nmmmh-de-giua-ki-2026-ca-2-24';opts={l:originals[id][l]['text'] for l in LETTERS};opts['C']='(109 114 227 453 905 1808)'
    seqs={l:list(map(int,t.strip('()').split())) for l,t in opts.items()}
    add(id,'A',[188], 'Hai phương án nguồn A/C trùng nhau; giữ A, sửa phần tử cuối C bằng đúng tổng trước để tạo nhiễu không siêu tăng.',options={'C':opts['C']},
        checks={l:{'matches':all(v>sum(seq[:i]) for i,v in enumerate(seq)), 'reason':'Kiểm tra từng phần tử LỚN HƠN tổng tất cả phần tử trước.', 'partial_sums':[sum(seq[:i]) for i in range(len(seq))]} for l,seq in seqs.items()},numeric={'sequences':seqs},hint='Mẹo: Tính tổng lũy kế; bằng tổng trước cũng không phải siêu tăng, phải lớn hơn nghiêm ngặt.')

    # Printed option letters in embedded figures were previously stored as
    # "A: B" etc. Type their real formula, preserving that canonical mapping.
    for id,key,opts in [
      ('nmmmh-de-cuong-2025-chuong3-22','A',{
        'A':'Với p nguyên tố và 0<a<p, a^p ≡ a (mod p).',
        'B':'Với p nguyên tố và p không chia a, a^(p−1) ≢ 1 (mod p).',
        'C':'Với p nguyên tố và a là bội của p, luôn có a^(p−1) ≡ a (mod p).',
        'D':'Với p nguyên tố và mọi a chẵn (kể cả a=0), a^(p−1) ≡ 1 (mod p).'}),
      ('nmmmh-de-giua-ki-2026-ca-1-32','B',{
        'A':'Với p nguyên tố và a là bội của p, luôn có a^(p−1) ≡ a (mod p).',
        'B':'Với p nguyên tố và 0<a<p, a^p ≡ a (mod p).',
        'C':'Với p nguyên tố và p không chia a, a^(p−1) ≢ 1 (mod p).',
        'D':'Với p nguyên tố và mọi a chẵn (kể cả a=0), a^(p−1) ≡ 1 (mod p).'})]:
        why=[]
        for l in LETTERS:
            t=opts[l]
            why.append('Đúng theo Fermat nhỏ.' if l==key else 'Sai: thử p=3,a=3.' if 'bội' in t else 'Sai: thử p=3,a=0.' if 'chẵn' in t else 'Sai: thử p=3,a=1, được 1 chứ không khác 1.')
        add(id,key,[175], 'Gõ lại công thức theo ảnh; thay phát biểu đúng dạng trường hợp con bằng nhiễu sai rõ ràng để tránh hai đáp án đúng. Nhãn UI gốc được giữ; D bị bỏ trống ở ca 1 được chép từ hình rồi chuẩn hóa.',
            stem='Chọn phát biểu ĐÚNG về định lý Fermat nhỏ (các khẳng định hiểu là đúng với mọi dữ kiện thỏa điều kiện đã nêu).',options=opts,checks=fit(key,why),typed=True,
            hint='Mẹo: Với khẳng định phổ quát, thử a=0 hoặc a=p nếu điều kiện cho phép; đừng bỏ điều kiện p không chia a khi dùng số mũ p−1.')
    for id,key,opts in [
      ('nmmmh-de-cuong-2025-chuong3-23','D',{'A':'3(p+1)(q+1)/4','B':'(p+1)(q+1)/4','C':'3(p−1)(q−1)/4','D':'(p−1)(q−1)/4'}),
      ('nmmmh-de-giua-ki-2026-ca-2-2','C',{'A':'(p+1)(q+1)/4','B':'3(p−1)(q−1)/4','C':'(p−1)(q−1)/4','D':'3(p+1)(q+1)/4'})]:
        add(id,key,[178], 'Bổ sung điều kiện nguyên tố LẺ theo định lý; giữ đúng thứ tự công thức trên giao diện từng đề.',
            stem='Cho n=pq với p,q là hai số nguyên tố LẺ phân biệt. Q_n là tập các bình phương của phần tử thuộc nhóm đơn vị Z*_n. Công thức nào cho |Q_n|?',options=opts,
            checks=fit(key,['Đúng: mỗi mô-đun nguyên tố lẻ có (p−1)/2 bình phương khác 0; nhân theo CRT.' if l==key else 'Sai hệ số hoặc dấu: thử p=3,q=5, nhóm có đúng 2 bình phương đơn vị.' for l in LETTERS]),typed=True,hint='Mẹo: Đếm các bình phương khác 0 riêng modulo p và modulo q, rồi nhân hai số lượng theo CRT.')
    gen_opts={
        'A':'Với mọi ước nguyên tố r của φ(n), α^(φ(n)/r) ≡ 1 (mod n).',
        'B':'Z*_n = {α^i mod n : 1 ≤ i < φ(n)}.',
        'C':'Z*_n = {α^i mod n : 0 ≤ i < φ(n)}.',
        'D':'ord_n(α) = φ(φ(n)).'}
    for id in ['nmmmh-de-cuong-2025-chuong3-24','nmmmh-de-giua-ki-2026-ca-2-40']:
        add(id,'C',[176], 'Hai miền 0≤i≤φ(n) và 0≤i<φ(n) vốn tương đương; thay miền ở phương án B bằng miền thiếu phần tử đơn vị. Trang 176 slide 42 cũng có lỗi bỏ i=0; dùng định nghĩa đúng slide 41.',
            stem='Với n>2 và α∈Z*_n, điều kiện nào TƯƠNG ĐƯƠNG với việc α là phần tử sinh của Z*_n?',options=gen_opts,
            checks=fit('C',['Sai: α sinh phải có các lũy thừa này KHÁC 1.','Chỉ có tối đa φ(n)−1 giá trị, thiếu phần tử đơn vị khi α là phần tử sinh.','Đúng: liệt kê đầy đủ một chu kỳ từ 0 tới φ(n)−1.','Sai: cấp phải là φ(n), không phải số lượng phần tử sinh.']),typed=True,
            hint='Mẹo: Một nhóm có φ(n) phần tử cần đủ một chu kỳ lũy thừa, kể cả phần tử đơn vị α^0.')
    add('nmmmh-de-cuong-2025-tonghop2-27','A',[176], 'Bổ sung điều kiện nhóm CYCLIC; nếu không có điều kiện này công thức đếm không đúng cho mọi n.',
        stem='Giả sử nhóm Z*_n là CYCLIC. Số phần tử sinh của nhóm là bao nhiêu?',
        options={'A':'φ(φ(n))','B':'n−1','C':'φ(n)−1','D':'φ(n)'},
        checks=fit('A',['Đúng: φ của cấp nhóm cyclic.','Không phải với mọi n, ví dụ n=5 chỉ có 2 phần tử sinh.','n=5 cho 3 nhưng chỉ có 2.','Đây là cấp nhóm, không phải số phần tử sinh.']),typed=True,hint='Mẹo: Trước hết lấy cấp nhóm, rồi đếm các số mũ nguyên tố cùng nhau với cấp đó.')
    add('nmmmh-de-cuong-2025-tonghop4-6','B',[160], 'Theo khoảng khóa RC4 của tài liệu, loại lựa chọn trùng nhau; không phải khuyến nghị sử dụng RC4 hiện nay.',
        stem='Theo thông số RC4 được nêu trong tài liệu môn học, TOÀN BỘ khoảng độ dài khóa hỗ trợ là bao nhiêu?',
        options={'A':'40–256 bit','B':'40–2048 bit','C':'256–2048 bit','D':'128–256 bit'},
        checks=fit('B',['Thiếu phần trên 256 bit.','Đúng theo PDF trang 160.','Thiếu phần từ 40 đến dưới 256 bit.','Chỉ là một khoảng con.']),hint='Mẹo: Đổi khoảng 5–256 BYTE sang bit; đừng nhầm độ rộng phần tử mảng S với độ dài khóa.')
    add('nmmmh-de-giua-ki-2026-ca-1-12','A',[186], 'Hỏi toàn bộ miền chọn số mũ theo định nghĩa ElGamal của giáo trình, không hỏi một khoảng con hợp lệ.',
        stem='Theo định nghĩa ElGamal trong tài liệu, với p=2003, TOÀN BỘ miền cho phép của khóa riêng a (không phải một khoảng con) là khoảng nào?',
        checks=fit('A',['Đúng: 1≤a≤p−2.','Chứa cả p−1 và p.','Chứa p−1 ngoài miền giáo trình.','Là khoảng con, không phải toàn bộ miền.']),hint='Mẹo: Đối chiếu hai đầu mút miền a trong định nghĩa hệ mật; kiểm tra cả khoảng, không chỉ một số thuộc khoảng.')
    for id,initial,taps,slot,pages in [
        ('nmmmh-de-giua-ki-2026-ca-1-28',[1,0,1,1,0,1,0,0,0],[0,3,5,8],'B',[153,154,155]),
        ('nmmmh-de-giua-ki-2026-ca-2-7',[1,0,1,0,1,0,1,1],[1,2,4,6],'D',[153,154,155])]:
        feedback=0
        for i in taps:feedback^=initial[i]
        after=initial[1:]+[feedback];bits=''.join(map(str,reversed(after)))
        # New distractors have the same required width, each exactly one bit
        # away; never truncate source options and pretend they were correct.
        value=int(bits,2);alts=[value^1,value^2,value^4];j=0;opts={}
        for l in LETTERS:
            if l==slot:opts[l]=bits
            else:opts[l]=f'{alts[j]:0{len(initial)}b}';j+=1
        add(id,slot,pages, 'Ảnh cho rõ công thức a_i(t+1)=a_(i+1)(t). Sửa phương án thừa bit bằng bộ nhiễu mới đúng độ dài; ca 2 còn sửa dãy đầu bị chép sai so với ảnh (ảnh ghi 1,0,1,0,1,0,1,1).',
            stem=f'LFSR có n={len(initial)}, (a0,…,a{len(initial)-1}) tại t=0 là ({",".join(map(str,initial))}). '
                 f'Mỗi nhịp a_i(t+1)=a_(i+1)(t) với i<n−1; a_(n−1)(t+1)='+ ' XOR '.join('a'+str(i)+'(t)' for i in taps)+f'. Tìm a{len(initial)-1}…a0 tại t=1.',
            options=opts,checks={l:{'matches':v==bits,'reason':f'Sau dịch, a0…a{len(initial)-1}={after}; đảo thứ tự xuất được {bits}.'} for l,v in opts.items()},numeric={'initial':initial,'taps':taps,'feedback':feedback,'after':after,'bits':bits},typed=True,
            hint='Mẹo: Tính bit phản hồi từ trạng thái CŨ rồi dịch toàn bộ một lần; chỉ đảo thứ tự khi ghi chuỗi đầu ra, không đảo chiều phép dịch.')
    # The exact S2 is in the reference, so no missing arbitrary input needs
    # to be supplied. B2 identifies which of the eight standard S-boxes to use.
    number('nmmmh-de-cuong-2025-tonghop2-8',7,[93,94], 'B2=100100 qua S2: hàng 10₂=2, cột 0010₂=2, S2[2][2]=7. Bảng được khôi phục từ trang 94.',
        stem='Trong DES, cho B2=100100₂. Tìm bốn bit đầu ra S2(B2), dùng hộp S2 chuẩn trong bảng bên dưới.',base=2,typed=True,hint='Mẹo: B2 phải đi qua S2; hai bit ngoài chọn hàng, bốn bit giữa chọn cột.')
    # First PC-1 positions are fully readable even if a later table row in the
    # source is incomplete; that missing row cannot influence these outputs.
    number('nmmmh-de-giua-ki-2026-ca-2-17',int(''.join('0000101011101001100101101100110111100010000011110100101110110011'[i-1] for i in [57,49,41,33]),2),[99,100],
        'Bốn vị trí đầu PC-1 là 57,49,41,33, đều hiện rõ. Các hàng bị cụt phía cuối không tham gia phép tính này.',base=2,hint='Mẹo: Chỉ lấy các bit khóa ở bốn vị trí PC-1 đầu tiên, đánh số từ 1; không cần tính 52 bit đầu ra còn lại.')
    add('nmmmh-de-giua-ki-2026-ca-2-28','C',[93,94,95], 'Sửa tham chiếu B3 thành B5 cho khớp dữ kiện B5=101011 và hộp S5 có trong ảnh.',
        stem='Trong DES, cho B5=101011₂. Dùng hộp S5 trong hình để tính bốn bit S5(B5).',
        checks=fit('C',['Hàng 3 cột 5 không bằng 12.','Hàng 3 cột 5 không bằng 1.','S5[3][5]=14=1110₂.','Hàng 3 cột 5 không bằng 10.']),numeric={'box':5,'bits':'101011','row':3,'column':5,'expected':14},hint='Mẹo: Theo dữ kiện B5 hãy tra S5, không tra S3; hàng và cột đều bắt đầu từ 0.')
    add('nmmmh-de-giua-ki-2026-ca-2-34','D',[177,178], 'Đọc đủ A–D trên hình và ánh xạ đúng thứ tự UI cũ (A là nhãn C trên hình); không bịa các phương án thiếu trong bản chép.',
        stem='Cho b,c>1 và gcd(b,c)=1. Tập nghiệm ĐẦY ĐỦ của hệ x≡a (mod b), x≡a (mod c) là gì?',
        options={'A':'x ≡ a² (mod b+c)','B':'x ≡ a (mod b+c)','C':'x ≡ a² (mod bc)','D':'x ≡ a (mod bc)'},
        checks=fit('D',['Thử b=3,c=5,a=2; phương án không cho tập nghiệm đúng.','Sai mô-đun b+c thay cho bc.','Sai vế phải a² thay cho a.','CRT: b,c cùng chia x−a và nguyên tố cùng nhau nên bc chia x−a.']),typed=True,hint='Mẹo: Từ b|(x−a) và c|(x−a), dùng gcd(b,c)=1 để ghép thành bc|(x−a).')
    add('nmmmh-de-giua-ki-2026-ca-2-35','A',[140,141,146,149], 'Câu gốc random-access có nhiều lựa chọn đúng; làm rõ không lấy khối mã trước và không sinh dòng khóa tuần tự, đồng thời sửa cặp lựa chọn cho đủ.',
        stem='Trong các chế độ ECB,CBC,CFB,OFB,CTR, chọn cặp ĐẦY ĐỦ cho phép giải mã trực tiếp khối i mà KHÔNG cần đọc C_(i−1) và KHÔNG cần sinh tuần tự các khối dòng khóa trước đó (biết khóa, IV/bộ đếm và chỉ số i).',
        options={'A':'ECB, CTR','B':'CBC, CFB','C':'CBC','D':'CFB, OFB'},checks=fit('A',['ECB dùng riêng C_i; CTR tính trực tiếp bộ đếm i.','Cả CBC và CFB cần khối mã trước.','CBC cần C_(i−1).','CFB cần khối trước, OFB phải sinh tuần tự dòng khóa.']),hint='Mẹo: Viết công thức giải khối i; kiểm tra có cần C_(i−1) hay phải chạy lại chuỗi E_K từ IV không.')
    id='nmmmh-de-thi-at17-bo-1-3'
    matrices={'A':[[5,8],[7,13]],'B':[[5,8],[19,13]],'C':[[7,9],[8,3]]}
    outputs={l:hill('MONDAY',m) for l,m in matrices.items()}
    checks={l:{'matches':v=='OSSNOA','reason':f'Mã hóa toàn bộ MONDAY được {v}.'} for l,v in outputs.items()}
    checks['D']={'matches':False,'reason':'Hai ô cột phải bị che nhưng cột trái đọc được (5,7): (12×5+14×7) mod 26=2, cho chữ C, không thể là O. Không đoán hai ô bị che.'}
    add(id,'B',[54], 'Không cần đoán ô bị che: cột trái D đã đủ loại. Hiển thị dấu ? ở hai ô không đọc được, không trình bày số suy đoán như nguồn.',
        stem='Bản rõ MONDAY được mã hóa Hill m=2, quy ước vector hàng và A=0, cho bản mã OSSNOA. Ma trận khóa nào đúng? Hai ô bị che ở phương án D được giữ dấu ?; cột trái vẫn đọc rõ.',
        options={'A':'k = [[5,8],[7,13]]','B':'k = [[5,8],[19,13]]','C':'k = [[7,9],[8,3]]','D':r'\(k=\begin{pmatrix}5&?\\7&?\end{pmatrix}\)'},checks=checks,numeric={'outputs':outputs,'D_first_cipher_letter':(12*5+14*7)%26},typed=True,
        hint='Mẹo: Thử cặp MO trước. Chỉ cột trái ma trận đã quyết định chữ mã đầu; ô bị che ở cột phải không ảnh hưởng phép thử này.')
    id='nmmmh-de-cuong-2025-tonghop1-17';seq=[32,37,73,145,289,577];perm=[3,6,1,2,5,4]
    public=[210*seq[i-1]%1163 for i in perm]
    opts={l:originals[id][l]['text'] for l in LETTERS};opts['D']='('+', '.join(map(str,public))+')'
    add(id,'D',[188], 'Dãy nguồn và hoán vị đều có sáu phần tử nhưng mọi phương án chỉ có năm; sửa một phương án thành đủ sáu kết quả tính độc lập.',
        options={'D':opts['D']},checks=fit('D',['Nguồn chỉ có năm phần tử, không thể là khóa sáu thành phần.']*3+[f'Đúng: a_i=210·M_π(i) mod 1163 cho {public}.']),numeric={'weights':seq,'permutation':perm,'multiplier':210,'modulus':1163,'public':public},
        hint='Mẹo: Khóa công khai phải có cùng số thành phần với dãy riêng; tính W·M_π(i) mod M đúng chiều hoán vị.')
    # User explicitly approved rebuilding incomplete exercises while keeping
    # their originals. These are NEW explicit conditions, not recovered OCR.
    reconstructed=[]
    def reconstruct(id,why):
        reconstructed.append(id)
        result[id]['kind']='reconstructed_exercise_with_explicit_new_conditions'
        result[id]['reason']='BIÊN SOẠN LẠI THEO CHẤP THUẬN CỦA NGƯỜI DÙNG; không coi dữ kiện bổ sung là nguyên văn nguồn. '+why+' '+result[id]['reason']
    id='nmmmh-de-cuong-2025-chuong2-38'
    expected=[0xAE^0x04,0xFE,0x86,0x54]
    add(id,'D',[126,129], 'Thực hiện XOR từng byte với hằng vòng, không lấy đáp án tô màu làm đầu vào.',
        stem='AES: cho SubWord(RotWord(w))=(AE,FE,86,54)_H. Trong bài đã chuẩn hóa này, CHO THÊM j=3 và Rcon[3]=(04,00,00,00)_H. Tính g(w).',
        checks=fit('D',['EA khác AE XOR 04.','EE khác AE XOR 04.','A6 khác AE XOR 04.','AA FE 86 54 là XOR đúng với 04 00 00 00.']),numeric={'subword':[0xAE,0xFE,0x86,0x54],'rcon':[4,0,0,0],'expected':expected},hint='Mẹo: Rcon chỉ có byte đầu khác 0, nên giữ nguyên ba byte cuối và XOR byte đầu.')
    reconstruct(id,'Nguồn mất Rcon[j]; bổ sung rõ vòng j=3 thành một bài hoàn chỉnh theo lịch AES, không tuyên bố đó là vòng gốc.')
    def sbox(x):
        inv=0 if not x else 1
        if x:
            for _ in range(254):inv=gf_mul(inv,x)
        out=0x63
        for i in range(8):
            bit=((inv>>i)^(inv>>((i+4)%8))^(inv>>((i+5)%8))^(inv>>((i+6)%8))^(inv>>((i+7)%8)))&1
            out^=bit<<i
        return out
    id='nmmmh-de-cuong-2025-chuong2-39';w0=[0x12,0x70,0xAE,0xDB];w3=[0x82,0x35,0xEB,0x5F]
    g=list(map(sbox,w3[1:]+w3[:1]));g[0]^=1;w4=[a^b for a,b in zip(w0,g)]
    texts={l:originals[id][l]['text'] for l in LETTERS};texts['A']='; '.join(f'{x:02X}' for x in w4)
    add(id,'A',[120,126,129], 'Tự tính SubWord/RotWord/Rcon, sau đó XOR với w0; thay phương án A bằng kết quả mới.',
        stem='AES-128: cho w[0]=(12,70,AE,DB)_H. Bổ sung dữ kiện cho bài chuẩn hóa: w[3]=(82,35,EB,5F)_H và Rcon[1]=(01,00,00,00)_H. Tính w[4]=w[0] XOR g(w[3]).',
        options={'A':texts['A']},checks={l:{'matches':t==texts['A'],'reason':f'g(w3)={[f"{x:02X}" for x in g]}, w4={[f"{x:02X}" for x in w4]}.'} for l,t in texts.items()},numeric={'w0':w0,'w3':w3,'rcon':[1,0,0,0],'g':g,'w4':w4},hint='Mẹo: Xoay w3 một byte, tra S-box, XOR Rcon vào byte đầu; cuối cùng XOR với w0.')
    reconstruct(id,'Nguồn bỏ trống g(w3). Bổ sung w3 và Rcon rõ ràng rồi tính g, không suy g ngược từ phương án cũ.')
    id='nmmmh-de-cuong-2025-chuong3-43';orders=[order(x,19) for x in [2,9,13,17]];bits=''.join('1' if v==18 else '0' for v in orders)
    number(id,int(bits,2),[176], 'Tính bậc của từng phần tử modulo 19, đánh dấu 1 khi bậc bằng 18.',
        stem='Bài chuẩn hóa dùng NHẤT QUÁN nhóm Z*19. Với các phần tử 2,9,13,17 theo đúng thứ tự này, ghi 1 nếu là phần tử sinh, 0 nếu không. Chọn chuỗi bốn bit.',base=2,typed=True,hint='Mẹo: 18=2×3²; với từng a, thử a^9 và a^6 modulo 19. Phần tử sinh phải qua cả hai phép thử khác 1.')
    reconstruct(id,'Nguồn dùng cả 19 và 10; chọn công khai modulo 19 để biên soạn phiên bản nhất quán, không khẳng định 19 là ý định của đề gốc.')
    id='nmmmh-de-cuong-2025-tonghop1-4';column=[0x56,0x1F,0x65,0xAB];coeffs=[[2,3,1,1],[1,2,3,1],[1,1,2,3],[3,1,1,2]]
    mixed=[]
    for row in coeffs:
        v=0
        for a,b in zip(row,column):v^=gf_mul(a,b)
        mixed.append(v)
    opts={l:f'{mixed[i]:02X}' for l,i in zip(LETTERS,[1,3,0,2])}
    number(id,mixed[0],[123,124], 'Giữ cột đầu ma trận đọc rõ, chỉ định công khai ô S00; các nhiễu mới lấy từ các hàng khác của cùng phép nhân.',
        replacements=opts,stem='AES MixColumns: cột đầu trạng thái là (56,1F,65,AB)_H. Trong bài biên soạn lại, cần tính ô S00 (hàng đầu, cột đầu), dùng hàng hệ số (02,03,01,01). Chọn giá trị HEX.',base=16,typed=True,
        hint='Mẹo: Chỉ nhân hàng (02,03,01,01) với cột đã cho; 03·a=(02·a) XOR a, cộng các tích bằng XOR.')
    reconstruct(id,'Nguồn mất chỉ số ô cần tính; chọn và ghi rõ S00, không coi chỉ số này là OCR phục hồi.')
    IP=[58,50,42,34,26,18,10,2,60,52,44,36,28,20,12,4,62,54,46,38,30,22,14,6,64,56,48,40,32,24,16,8,
        57,49,41,33,25,17,9,1,59,51,43,35,27,19,11,3,61,53,45,37,29,21,13,5,63,55,47,39,31,23,15,7]
    for id,positions,slot in [('nmmmh-de-cuong-2025-tonghop1-7',[1,2,3,4],'A'),('nmmmh-de-giua-ki-2026-ca-1-34',[9,10,11,12],'D')]:
        x=f'{0x0123456789ABCDEF:064b}';out=''.join(x[i-1] for i in IP);bits=''.join(out[i-1] for i in positions);v=int(bits,2)
        opts={};other=iter([v^1,v^2,v^4])
        for l in LETTERS:opts[l]=bits if l==slot else f'{next(other):04b}'
        number(id,v,[89], 'Đánh số đầu vào/đầu ra từ 1, áp IP chuẩn rồi đọc đúng bốn vị trí đã chỉ định mới.',
            stem='Bài DES biên soạn lại: cho x=0123456789ABCDEF_H (64 bit, bit cao nhất bên trái). Sau IP chuẩn, lấy các bit ở vị trí '+', '.join(map(str,positions))+' theo thứ tự a,b,c,d. Chọn abcd.',replacements=opts,base=2,typed=True,
            hint='Mẹo: Với vị trí đầu ra j, lấy bit đầu vào ở IP[j]; không áp bảng theo chiều ngược lại.')
        reconstruct(id,'Nguồn thiếu đầu vào/vị trí đích hoặc thiếu phương án; dùng dữ kiện và các nhiễu mới được nêu rõ thay vì đoán phần bị mất.')
    id='nmmmh-de-cuong-2025-tonghop2-23';P=[16,7,20,21,29,12,28,17,1,15,23,26,5,18,31,10,2,8,24,14,32,27,3,9,19,13,30,6,22,11,4,25]
    x=f'{0x9F1AA34E:032b}';bits=''.join(x[i-1] for i in P[:4]);v=int(bits,2);opts={'A':f'{v^1:04b}','B':bits,'C':f'{v^2:04b}','D':f'{v^4:04b}'}
    number(id,v,[96], 'Áp bốn vị trí đầu P=(16,7,20,21), chỉ số bắt đầu từ 1.',
        stem='Bài DES biên soạn lại: cho C=9F1AA34E_H (32 bit, bit cao nhất bên trái). Tìm bốn bit ĐẦU của P(C) theo thứ tự A,B,C,D. Dùng hoán vị P chuẩn DES.',replacements=opts,base=2,typed=True,
        hint='Mẹo: Bốn bit đầu ra chỉ cần bốn bit đầu vào ở các chỉ số đầu tiên của bảng P; không cần hoán vị cả khối.')
    reconstruct(id,'Nguồn mất trạng thái và vị trí; cung cấp trạng thái 32 bit và vị trí đích mới, ghi rõ bài đã biên soạn lại.')
    id='nmmmh-de-cuong-2025-tonghop3-23';seq=[12,13,33,60,120,240,480];perm=[5,6,1,2,4,7,3];mod=1009
    public=[317*seq[i-1]%mod for i in perm]
    variants=[public[2:]+public[:2],public,[public[0],public[1],public[5],public[2],public[4],public[3],public[6]],list(reversed(public))]
    opts={l:'('+', '.join(map(str,a))+')' for l,a in zip(LETTERS,variants)}
    add(id,'B',[188], 'Sửa miền hoán vị thành 1..7 và chọn M=1009>958, gcd(317,1009)=1. Tính đủ bảy phần tử khóa công khai theo đúng chiều hoán vị.',
        stem='Merkle–Hellman: dãy siêu tăng (12,13,33,60,120,240,480), W=317. Bài chuẩn hóa chọn lại M=1009 để lớn hơn tổng dãy; π là hoán vị của {1,…,7}, π=(5,6,1,2,4,7,3). Tính khóa công khai a_i=W·M_π(i) mod 1009.',options=opts,
        checks={l:{'matches':a==public,'reason':f'Kết quả theo đúng π là {public}.'} for l,a in zip(LETTERS,variants)},numeric={'weights':seq,'permutation':perm,'modulus':mod,'multiplier':317,'public':public},typed=True,
        hint='Mẹo: Kiểm tra M lớn hơn TỔNG dãy và W khả nghịch; sau đó tính các vị trí có khác biệt giữa phương án trước.')
    reconstruct(id,'M=737 của nguồn không hợp lệ để bảo đảm giải mã; M=1009 và các nhiễu là dữ kiện biên soạn mới. Trang 188 ghi điều kiện M quá yếu, bổ sung bằng điều kiện chuẩn M>tổng dãy.')
    id='nmmmh-de-cuong-2025-tonghop4-8';plain='LOVELYDAY';cipher='CFMVCPURP';valid={l:all((ord(a)-65+int(originals[id][l]['text']))%26==ord(b)-65 for a,b in zip(plain,cipher)) for l in LETTERS}
    add(id,'A',[42,43], 'Bổ sung một cặp bản rõ–bản mã đầy đủ, thử độc lập mọi khóa trên từng ký tự.',
        stem='Caesar với A=0,…,Z=25, C=(P+K) mod 26. Bài chuẩn hóa CHO THÊM bản rõ LOVELYDAY, bản mã CFMVCPURP. Tìm khóa K.',
        checks={l:{'matches':ok,'reason':'Thử mã hóa cả LOVELYDAY bằng khóa ứng viên và so CFMVCPURP.'} for l,ok in valid.items()},numeric={'plaintext':plain,'ciphertext':cipher,'key':(ord(cipher[0])-ord(plain[0]))%26},hint='Mẹo: Một cặp chữ đã đủ tính K=C−P mod 26; thử thêm chữ thứ hai để kiểm tra.')
    reconstruct(id,'Nguồn chỉ cho bản mã, không xác định được khóa duy nhất; bản rõ LOVELYDAY là điều kiện bổ sung mới, không coi là được chứng minh từ nguồn.')
    id='nmmmh-de-cuong-2025-tonghop4-20';cipher='FHTZHWSMNABOFHQK';stream='MATMADEMAKHOTHAT';plain=''.join(chr((ord(a)-ord(b))%26+65) for a,b in zip(cipher,stream,strict=True))
    opts={l:originals[id][l]['text'] for l in LETTERS}
    add(id,'B',[29,30], 'Kiểm đếm lại cho thấy khóa MATMADEMAKHOTHAT và bản mã ĐỀU CÓ 16 ký tự; nhận định cũ khóa chỉ dài 15 là sai. Giữ nguyên khóa, bản mã và phương án; áp Vernam chữ Latin modulo 26 theo tài liệu.',
        stem=originals[id]['question']+' Dùng A=0,…,Z=25 và P=(C−K) mod 26 như ví dụ Vernam trong tài liệu; không XOR ASCII.',
        checks={l:{'matches':t.upper()==plain,'reason':f'Trừ từng ký tự khóa đủ dài cho kết quả {plain}.'} for l,t in opts.items()},numeric={'ciphertext':cipher,'keystream':stream,'plaintext':plain},hint='Mẹo: Kiểm tra hai chuỗi cùng độ dài rồi trừ từng cặp mã chữ modulo 26; không chuyển sang XOR ASCII.')
    id='nmmmh-de-giua-ki-2026-ca-1-5'
    add(id,'C',[143,144,145], 'Chọn yêu cầu ĐÚNG cho bài biên soạn lại, xét CFB full-block để phát biểu định nghĩa rõ ràng.',
        stem='Bài biên soạn lại: khẳng định nào ĐÚNG về CFB với kích thước đoạn bằng kích thước khối (full-block)?',
        checks=fit('C',['Khối mã còn phụ thuộc khối rõ HIỆN TẠI, không chỉ các khối trước.','Lỗi bản mã còn lật bit tương ứng trong khối rõ hiện tại.','Đúng: E_K tác động IV hoặc C_(i−1), rồi XOR bản rõ.','CFB có khả năng tự đồng bộ sau số đoạn hữu hạn.']),hint='Mẹo: Viết C_i=P_i XOR E_K(C_(i−1)), C_0=IV; theo dõi riêng đầu vào E_K và phép XOR.')
    reconstruct(id,'Thân câu gốc mất hoàn toàn; ĐÚNG và full-block là yêu cầu biên soạn mới, không phải nguyên văn phục hồi.')
    id='nmmmh-de-giua-ki-2026-ca-1-9'
    add(id,'B',[28,152,153,155], 'Thay so sánh phần cứng không có thước đo bằng định nghĩa thuật toán đủ chặt chẽ.',
        stem='Loại mật mã tổng quát nào xử lý lần lượt từng bit/ký tự bằng cách kết hợp với một dòng khóa, thay vì áp phép mã cố định lên từng khối dữ liệu?',
        checks=fit('B',['ECB/OFB là tên chế độ; ECB xử lý theo khối, không phải một loại tổng quát cùng tính chất.','Đúng: định nghĩa mã dòng.','DES là thuật toán mã khối.','AES là thuật toán mã khối.']),hint='Mẹo: Phân biệt loại mã (khối/dòng), tên thuật toán (DES/AES) và chế độ hoạt động.')
    reconstruct(id,'Không thể xác nhận thuật toán nào thích hợp hơn với mọi phần cứng; thay tiêu chí đó bằng định nghĩa mã dòng từ tài liệu.')
    id='nmmmh-de-giua-ki-2026-ca-2-30';count=len({x*x%97 for x in range(1,97)})
    number(id,count,[178], 'Đếm trực tiếp tập bình phương khác 0 modulo 97; so với công thức (97−1)/2.',
        stem='Bài chuẩn hóa chọn NHẤT QUÁN mô-đun 97: trong nhóm Z*97 có bao nhiêu thặng dư bậc hai khác 0?',typed=True,
        hint='Mẹo: Với p nguyên tố lẻ, hai phần tử x và −x cho cùng bình phương; đếm theo từng cặp trong nhóm đơn vị.')
    reconstruct(id,'Nguồn mâu thuẫn 41/97. Chọn công khai modulo 97 cho phiên bản mới, không khẳng định đó là ý định gốc.')
    assert len(reconstructed)==12
    # Pin precise PDF page citations after comparing the rendered reference.
    fixes={
        'nmmmh-de-thi-k16-2-11':[184,185],
        'nmmmh-de-thi-nmmmh-29':[186],
        'nmmmh-de-thi-mat-ma-2021-trac-nghiem-26':[186],
        'nmmmh-de-thi-k16-3-2036':[186],
        'nmmmh-de-thi-k16-3-2032':[59,60],
        'nmmmh-de-cuong-2025-tonghop3-1':[59,60],
        'nmmmh-de-cuong-2025-tonghop1-1':[87,105,107,116,117],
        'nmmmh-de-cuong-2025-tonghop1-6':[83,116,117],
        'nmmmh-de-cuong-2025-tonghop1-28':[117,126,127],
        'nmmmh-de-cuong-2025-tonghop2-4':[185,197,198],
        'nmmmh-de-cuong-2025-tonghop2-17':[87,99],
        'nmmmh-de-cuong-2025-tonghop2-20':[87,99,101],
        'nmmmh-de-giua-ki-2026-ca-2-1':[110,112,113,114],
        'nmmmh-de-giua-ki-2026-ca-2-17':[99,101],
        'nmmmh-de-giua-ki-2026-ca-2-28':[93,95],
        'nmmmh-de-cuong-2025-tonghop4-8':[40],
    }
    for id,pages in fixes.items():result[id]['reference_pages']=pages
    return result
