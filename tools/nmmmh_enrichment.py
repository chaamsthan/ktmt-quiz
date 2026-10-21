"""Additive presentation/learning metadata; source strings remain accessible.

Independent audit changes are explicit, per-ID overrides, never fuzzy matching.
"""
import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GREEK = {'α':r'\alpha','β':r'\beta','γ':r'\gamma','δ':r'\delta','φ':r'\varphi','π':r'\pi'}
SUBS = str.maketrans('₀₁₂₃₄₅₆₇₈₉','0123456789')
SUPS = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁻','0123456789-')


def tex_symbols(text):
    for char, tex in GREEK.items(): text=text.replace(char,tex+' ')
    return text.replace('−','-').replace('·',r'\cdot ').replace('×',r'\times ').replace('≡',r'\equiv ').replace('∈',r'\in ')


def math_display(text):
    # Process original plain source only. Existing delimited LaTeX is retained.
    if '\\(' in text or '\\[' in text: return text
    matrix=re.compile(r'\[\[\s*(-?\d+)\s*,\s*(-?\d+)\s*\],\s*\[\s*(-?\d+)\s*,\s*(-?\d+)\s*\]\]')
    text=matrix.sub(lambda m:r'\(\begin{pmatrix}'+m[1]+'&'+m[2]+r'\\'+m[3]+'&'+m[4]+r'\end{pmatrix}\)',text)
    text=re.sub(r'GF\(2\s*\^\s*8\)',lambda _:r'\(\mathrm{GF}(2^8)\)',text)
    # Atomic powers: do not consume surrounding Vietnamese or change values.
    power=re.compile(r'(?<![\\\w])([a-zA-Zαβγδ]|\d+)\s*\^\s*(\([^()]+\)|\{[^{}]+\}|[a-zA-Z]+|[-−]?\d+)')
    def power_tex(match):
        base, exponent=match.groups()
        if exponent.startswith(('(', '{')):exponent=exponent[1:-1]
        return r'\('+tex_symbols(base)+'^{'+tex_symbols(exponent)+r'}\)'
    # Split protected LaTeX produced above to avoid nesting delimiters.
    parts=re.split(r'(\\\(.*?\\\))',text)
    for i in range(0,len(parts),2):
        part=power.sub(power_tex,parts[i])
        part=re.sub(r'Z\*([₀-₉]+)',lambda m:r'\(\mathbb{Z}_{'+m[1].translate(SUBS)+r'}^{*}\)',part)
        part=re.sub(r'log([₀-₉]+)',lambda m:r'\(\log_{'+m[1].translate(SUBS)+r'}\)',part)
        part=re.sub(r'(?<![\\\w])([a-zA-Z])([⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+)',lambda m:r'\('+m[1]+'^{'+m[2].translate(SUPS)+r'}\)',part)
        parts[i]=part
    return ''.join(parts)


def display_blocks(blocks):
    result=copy.deepcopy(blocks)
    for block in result:
        if block['type']=='text': block['text']=math_display(block['text'])
    return result


def enrich(q, overrides, hints):
    change=overrides.get(q['id'],{})
    q['verification_revision']='nmmmh-20261021-v1'
    q['chapter_ids']=change.get('chapter_ids',[q['chapter_id']])
    if change.get('primary_chapter'):
        q['source_classification']={'chapter_id':q['chapter_id'],'chapter':q['chapter'],
                                    'chapter_parent':copy.deepcopy(q['chapter_parent']),
                                    'chapter_child':copy.deepcopy(q['chapter_child'])}
        parent=change['primary_chapter'];q['chapter_parent']=copy.deepcopy(parent)
        q['chapter_id']=str(parent['id']);q['chapter']=f'Chương {parent["id"]}. {parent["name"]}'
        topic=change.get('official_primary_topic')
        q['chapter_child']={'code':topic['id'],'name':topic['name'],'source':'knowledge_tree'} if topic else None
        q['topic_ids']=change['chapter_review']['topic_ids']
        q['classification_audit']=copy.deepcopy(change['chapter_review'])
        q['classification_needs_review']=change['chapter_review']['needs_taxonomy_review']
    q['exam_ids']=[q['source_exam_id']]
    q['original_question_number']=q['source_question_number']
    q['source_reference']=change.get('source_reference',{'file':q['source_file'],'page':q['source_page'],'status':'original_docx_unavailable'})
    q['source_fidelity_status']=change.get('source_fidelity_status','not_yet_rechecked')
    q['verification_status']=change.get('verification_status','previous_audit_only')
    q['verification_notes']=change.get('verification_notes','Không coi đáp án cũ là bằng chứng tái kiểm chứng. Xem audit/UPGRADE_REPORT.md.')
    q['hint']=hints.get(q['id'],'')
    q['explanation']=q['answer_audit']['explanation']
    for edit in change.get('edits',[]):
        field=edit['field']
        if field in 'ABCD' and len(field)==1:
            holder=q[field]
            assert holder['text']==edit['old'],(q['id'],field,'stale override')
            holder['text']=edit['new']
            for block in holder['blocks']:
                if block['type']=='text' and block['text']==edit['old']:block['text']=edit['new']
        elif field=='question':
            assert q[field]==edit['old'],(q['id'],field,'stale override')
            q[field]=edit['new']
            # Body may contain separate image/table blocks; update only the
            # exact matching text, not other sections of the source question.
            for block in q['question_blocks']:
                if block['type']=='text' and block['text']==edit['old']:block['text']=edit['new']
                elif block['type']=='text':
                    old_lines=edit['old'].split('\n');new_lines=edit['new'].split('\n')
                    if len(old_lines)==len(new_lines):
                        for before,after in zip(old_lines,new_lines):
                            if before!=after and block['text']==before:block['text']=after
        elif re.fullmatch(r'question_blocks\[\d+\]\.text',field):
            index=int(re.search(r'\[(\d+)\]',field)[1])
            assert q['question_blocks'][index]['text']==edit['old']
            q['question_blocks'][index]['text']=edit['new']
            q['question']='\n'.join(b['text'] for b in q['question_blocks'] if b['type']=='text')
        else:raise ValueError(f'Unsupported override field: {field}')
    if change.get('edits'):q['source_corrections']=q.get('source_corrections',[])+copy.deepcopy(change['edits'])
    for replacement in change.get('image_replacements',[]):
        found=False
        for holder in [q]+[q[l] for l in 'ABCD']:
            for block in holder.get('question_blocks',holder.get('blocks',[])):
                if block['type']=='image' and block['src']==replacement['old']:
                    block['original_src']=block['src']
                    block['src']=replacement['new'];found=True
        assert found,(q['id'],'image replacement not found',replacement)
    if change.get('answer_decision'):
        decision=change['answer_decision']
        assert decision.get('evidence') and decision.get('method')
        assert decision['correct_answer'] is None or decision['correct_answer'] in ('A','B','C','D')
        assert (decision['status']=='verified') == bool(decision['correct_answer'])
        q['answer_audit']={**q['answer_audit'],**decision}
        q['correct_answer']=decision['correct_answer']
        q['verification_status']=decision['status']
        q['explanation']=decision['explanation']
        q['needs_review']=decision['status']!='verified' or change.get('source_fidelity_status')=='needs_review'
        q['review_reasons']=[r for r in q['review_reasons'] if r.startswith('Nhãn chương')]
        if q['needs_review']:q['review_reasons'].append(decision['explanation'])
    if q['source_reference'].get('page'):q['source_page']=q['source_reference']['page']
    if q['source_fidelity_status']=='needs_review':
        q['needs_review']=True
        q['review_reasons'].extend(change.get('source_issues',[]))
    q['display_blocks']=display_blocks(q['question_blocks'])
    # The reviewed Hill figures contain the four matrices with printed A-D
    # labels together. Shuffling the text options would contradict those
    # source labels even if internal grading IDs remained correct.
    q['source_option_labels_in_figure']=bool(q['answer_audit'].get('proof_key')=='hill' and any(b['type']=='image' for b in q['question_blocks']))
    for letter in 'ABCD':q[letter]['display_blocks']=display_blocks(q[letter]['blocks'])
    return q


def load_metadata():
    folder=ROOT/'subjects/nmmmh/audit'
    file=folder/'approved_changes.json'
    overrides=json.loads(file.read_text()) if file.is_file() else {}
    hints_file=folder/'hints.json'
    hints_data=json.loads(hints_file.read_text()) if hints_file.is_file() else {}
    if isinstance(hints_data,dict) and 'hints' in hints_data:hints_data=hints_data['hints']
    if isinstance(hints_data,list):hints_data={r['id']:r['hint'] for r in hints_data}
    hints={k:(v['hint'] if isinstance(v,dict) else v) for k,v in hints_data.items()}
    return overrides,hints
