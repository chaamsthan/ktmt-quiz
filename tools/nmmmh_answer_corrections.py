"""Small, explicit answer corrections; never change source option ordering."""
JACOBI_ID='nmmmh-de-cuong-2025-chuong3-20'


def apply_answer_correction(q):
    if q['id']!=JACOBI_ID:return q
    assert {l:q[l]['text'] for l in 'ABCD'}=={'A':'A','B':'D','C':'B','D':'C'}
    explanation=('Đáp án C trên web tương ứng B trong ảnh. Công thức tương hỗ ở B trong ảnh bị đảo dấu: '
                 '(m/n)=−(n/m) khi m≡n≡3 (mod 4), còn lại là dấu cộng. '
                 'Phản ví dụ m=3,n=7: (3/7)=−1 nhưng (7/3)=1. '
                 'Các công thức A,C,D trong ảnh đúng. Dấu đáp án B trong DOCX được giữ riêng để đối chiếu, không dùng để chấm.')
    q.update(correct_answer='C',verification_status='verified',verification_revision='jacobi-answer-20261022-v1',
             answer_evidence='user_correction_and_independent_counterexample',explanation=explanation)
    q['answer_audit']={'status':'verified','correct_answer':'C','valid_options':['C'],
                      'explanation':explanation,'sources':[],
                      'option_checks':{
                          'A':{'matches':False,'reason':'Nhãn A trong ảnh: công thức bổ sung cho (2/n) đúng.'},
                          'B':{'matches':False,'reason':'Nhãn D trong ảnh: tính bất biến khi tử đồng dư là đúng.'},
                          'C':{'matches':True,'reason':'Nhãn B trong ảnh: luật tương hỗ bị đảo dấu; m=3,n=7 là phản ví dụ.'},
                          'D':{'matches':False,'reason':'Nhãn C trong ảnh: tính nhân theo tử đúng.'}}}
    q['answer_correction']={'previous_correct_answer':'B','correct_answer':'C','source_image_label':'B',
                            'reason':'User requested C on website, corresponding to B in the image; independently checked using m=3,n=7.',
                            'reference_pdf_pages':[179]}
    return q
