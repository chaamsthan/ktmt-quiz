#!/usr/bin/env python3
"""Publish conservative decisions from independent audits, never old keys.

Source text remains immutable in DAPAN_KIEMCHUNG. The generated overlay records
the evidence, including non-unique/undefined conclusions, for each stable ID.
"""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'subjects/nmmmh/audit'


def read(name):
    return json.loads((AUDIT/name).read_text())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True,type=Path)
    args=parser.parse_args()
    old={q['id']:q for q in json.loads((args.source/'DAPAN_KIEMCHUNG/questions_verified.json').read_text())}
    changes=read('approved_changes.json')
    numeric={r['id']:r for r in read('numeric_audit.json')['rows']}
    theory={r['id']:r for r in read('theory_audit.json')['post_source_corrected_candidates']}
    decisions=[];changed=[]
    for identifier,overlay in changes.items():
        n=numeric[identifier];t=theory.get(identifier)
        answer=None;valid=[];status='needs_review';sources=[]
        evidence=['audit/numeric_audit.json#'+identifier]
        if t:
            method='independent_theory_and_option_evaluation'
            evidence.append('audit/theory_audit.json#'+identifier)
            explanation=t['reasoning']
            sources=[s['url'] for s in t.get('source_citations',[]) if s.get('url')]
            if t['status']=='verified':
                answer=t['candidate_answer'];valid=[answer];status='verified'
                if n['status']=='unique_match' and n.get('candidate_set_complete'):
                    assert n['conventional_candidates']==[answer],(identifier,'conflicting independent audits')
            else:
                valid=n['candidates'] if n.get('candidate_set_complete') else []
        else:
            method='independent_calculation_'+str(n.get('method'))
            valid=n.get('conventional_candidates',n['candidates'])
            notes=' '.join(n.get('notes',[]))
            # A complete A-D check is required. A finite witness alone does
            # not establish all the other universal propositions.
            if n.get('candidate_set_complete') and len(valid)==1 and n['status'] in ('unique_match','multiple_matches'):
                answer=valid[0];status='verified'
                if len(n['candidates'])>1:
                    assert 'tất cả' in old[identifier][answer]['text'].lower() or 'cả ba' in old[identifier][answer]['text'].lower(),identifier
                    explanation='Đã kiểm tra từng mệnh đề. Chọn phương án tổng hợp theo quy ước “tất cả các đáp án trên”. '
                else:explanation='Tính độc lập và đối chiếu đủ A–D; chỉ '+answer+' khớp. '
            elif n['status']=='no_match':explanation='Không có phương án khớp kết quả tính độc lập. '
            elif n['status']=='multiple_matches':explanation='Có nhiều phương án cùng thỏa yêu cầu: '+', '.join(valid)+'. Không ép một đáp án. '
            else:explanation='Chưa đủ bằng chứng để chốt đáp án duy nhất. '
            explanation+='Kết quả: '+json.dumps(n.get('computed'),ensure_ascii=False)+('. '+notes if notes else '')
        # Readable alternatives cannot be invented where the original cursor
        # covers cells, even if the old transcription supplied plausible ones.
        if overlay['source_fidelity_status']=='needs_review':
            answer=None;status='needs_review'
            explanation+=' Cần đối chiếu nguồn: '+'; '.join(overlay['source_issues'])
            valid=[]
        if status!='verified' and not n.get('candidate_set_complete'):valid=[]
        if answer is None and status=='verified':raise AssertionError(identifier)
        decision={'status':status,'correct_answer':answer,'valid_options':valid,
                  'candidate_options':n.get('candidates',[]),
                  'method':method,'evidence':evidence,'sources':list(dict.fromkeys(sources)),
                  'explanation':explanation}
        overlay['answer_decision']=decision
        overlay['verification_status']=status
        overlay['verification_notes']='; '.join(evidence)
        row={'id':identifier,'source_exam_id':old[identifier]['source_exam_id'],
             'source_question_number':old[identifier]['source_question_number'],
             'old_answer':old[identifier]['correct_answer'],'new_answer':answer,
             **decision}
        decisions.append(row)
        if row['old_answer']!=answer:changed.append(row)
    assert len(decisions)==173
    for name,value in [('approved_changes.json',changes),('answer_decisions.json',decisions),('answer_changes.json',changed)]:
        (AUDIT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'reviewed':len(decisions),'verified':sum(r['status']=='verified' for r in decisions),
                      'needs_review':sum(r['status']!='verified' for r in decisions),
                      'answer_changes':len(changed),'changed_existing_letter':sum(bool(r['old_answer'] and r['new_answer']) for r in changed)}))


if __name__=='__main__':main()
