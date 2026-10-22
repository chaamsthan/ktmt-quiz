#!/usr/bin/env python3
"""Migration/source invariants and independent arithmetic regression.

uv run --with sympy python tools/test_nmmmh_reference.py
Baseline commit is fixed BEFORE the repair, not calculated from current output.
"""
import copy
import hashlib
import json
import math
import re
import subprocess
import unittest
from pathlib import Path

import sympy
from apply_nmmmh_reference_review import REVISION, migrate
from nmmmh_reference_decisions import AUDIT, ROOT, decisions
from nmmmh_answer_corrections import JACOBI_ID, apply_answer_correction

BASELINE='013ffcdb3dea7260cc48b5d3442516b267dc2e50'
LETTERS='ABCD'


def read(p):return json.loads(p.read_text())
def git_file(path):return subprocess.check_output(['git','show',BASELINE+':'+path],cwd=ROOT)


class ReferenceReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=read(ROOT/'subjects/nmmmh/manifest.json')
        cls.exams=cls.manifest['exams']+[e for c in cls.manifest['collections'] for e in c['exams']]
        cls.rows=[q for e in cls.exams for q in read(ROOT/e['question_file'])]
        cls.by_id={q['id']:q for q in cls.rows};cls.frozen=read(AUDIT/'original_questions.json');cls.decisions=decisions()

    def test_exact_same_ids_numbering_order_and_chapters(self):
        self.assertEqual(len(self.exams),14);self.assertEqual(len(self.rows),540);self.assertEqual(len(self.by_id),540)
        self.assertEqual(len(self.decisions),103);self.assertEqual(set(self.decisions),set(self.frozen))
        for e in self.exams:
            before=json.loads(git_file(e['question_file']));current=read(ROOT/e['question_file'])
            for a,b in zip(before,current,strict=True):
                for key in ['id','source_question_number','source_order','source_exam_id','chapter_id','chapter_ids','source_reference']:
                    self.assertEqual(a[key],b[key],(a['id'],key))
                if a['id'] in self.frozen:self.assertEqual(a,self.frozen[a['id']])
                else:
                    if a['id']==JACOBI_ID:apply_answer_correction(a)
                    # Only derived duplicate grouping can change when a
                    # related question has been substantively corrected.
                    for key in ['duplicate_status','duplicate_group','duplicate_sources']:
                        a.pop(key,None);b.pop(key,None)
                    self.assertEqual(a,b,a['id'])

    def test_other_subject_byte_identical(self):
        for path in ['questions.json','exam_sets.json','app.js','nmmmh-practice.js','styles.css']:
            self.assertEqual((ROOT/path).read_bytes(),git_file(path),path)

    def test_all_current_answers_unique_and_all_changes_documented(self):
        self.assertTrue(all(q['correct_answer'] in LETTERS and not q['needs_review'] for q in self.rows))
        for id,d in self.decisions.items():
            q=self.by_id[id]
            self.assertEqual(q['question'],d['question']);self.assertEqual(q['correct_answer'],d['correct_answer'])
            self.assertEqual(q['verification_revision'],REVISION)
            self.assertEqual(q['answer_audit']['valid_options'],[d['correct_answer']])
            self.assertEqual([l for l in LETTERS if d['option_checks'][l]['matches']],[d['correct_answer']])
            self.assertTrue(all(d['option_checks'][l]['reason'] for l in LETTERS))
            self.assertTrue(d['reference_pages']);self.assertTrue(q['normalization']['reason'])
            for l in LETTERS:self.assertEqual(q[l]['text'],d['options'][l])
            self.assertEqual(len({q[l]['text'] for l in LETTERS}),4,id)
            self.assertNotIn('pending',q['verification_status'])
        self.assertEqual(read(AUDIT/'pending.json'),[])
        report=read(AUDIT/'report.json');self.assertEqual(report['resolved'],103);self.assertEqual(report['remaining_review'],0)

    def test_explicitly_authorized_reconstructions(self):
        auth=read(AUDIT/'reconstruction_authorization.json')
        ids={id for id,d in self.decisions.items() if d.get('kind')}
        self.assertEqual(len(ids),12);self.assertEqual(ids,set(auth['question_ids']))
        self.assertEqual(auth['user_approval'],'Có, chuẩn hóa câu lỗi và giữ bản gốc')
        for id in ids:
            self.assertIn('không',self.decisions[id]['reason'].lower())
            self.assertEqual(self.by_id[id]['normalization']['kind'],'reconstructed_exercise_with_explicit_new_conditions')

    def test_math_totient_orders_jacobi_and_crypto(self):
        self.assertEqual(int(sympy.totient(765)),384)
        self.assertEqual(int(sympy.jacobi_symbol(2634,889785)),0)
        self.assertEqual(int(sympy.jacobi_symbol(21,235)),1)
        self.assertEqual(int(sympy.totient(sympy.totient(4802))),588)
        self.assertEqual([sympy.n_order(a,19) for a in [2,9,13,17]],[18,9,18,9])
        self.assertIsNone(sympy.primitive_root(19036))
        for a,k in [(117,33),(113,67)]:
            beta=pow(41,a,211);gamma=pow(41,k,211);delta=56*pow(beta,k,211)%211
            self.assertEqual(delta*pow(pow(gamma,a,211),-1,211)%211,56)
        self.assertEqual(pow(1234,2,199*211),11152)
        self.assertEqual([x for x in range(41989) if x*x%41989==11152],[1234,14169,27820,40755])
        self.assertEqual(pow(103,-1,1120),87)
        self.assertEqual(pow(pow(142,103,1189),87,1189),142)
        self.assertEqual(len({x*x%97 for x in range(1,97)}),48)

    def test_independent_gf_multiplication_and_aes_sbox(self):
        # Different implementation from production polynomial long division.
        def multiply(a,b):
            out=0
            for _ in range(8):
                if b&1:out^=a
                a=((a<<1)^0x11B) if a&0x80 else a<<1;b>>=1
            return out
        self.assertEqual(multiply(0x60,8),0x2D)
        self.assertEqual(multiply(3,0x0B)^0xFE^0x20^multiply(2,0x87),0xD6)
        self.assertEqual(0x0B^multiply(2,0xFE)^multiply(3,0x20)^0x87,0x0B)
        self.assertEqual(multiply(2,0x56)^multiply(3,0x1F)^0x65^0xAB,0x43)
        # Four S-box entries read from the reference table (PDF 120), not
        # calculated by the production affine implementation.
        sub=[0x96,0xE9,0xCF,0x13];sub[0]^=1
        w4=[a^b for a,b in zip([0x12,0x70,0xAE,0xDB],sub)]
        q=self.by_id['nmmmh-de-cuong-2025-chuong2-39']
        self.assertEqual(w4,[0x85,0x99,0x61,0xC8]);self.assertEqual(q['answer_audit']['numeric']['w4'],w4)

    def test_lfsr_against_original_image_and_own_shift_model(self):
        cases=[('nmmmh-de-giua-ki-2026-ca-1-28',[1,0,1,1,0,1,0,0,0],[0,3,5,8],'100010110'),
               ('nmmmh-de-giua-ki-2026-ca-2-7',[1,0,1,0,1,0,1,1],[1,2,4,6],'11101010')]
        for id,initial,taps,expected in cases:
            n=len(initial);register=sum(v<<i for i,v in enumerate(initial))
            feedback=sum((register>>i)&1 for i in taps)%2
            shifted=(register>>1)|(feedback<<(n-1))
            bits=f'{shifted:0{n}b}';self.assertEqual(bits,expected)
            q=self.by_id[id];self.assertEqual(q[q['correct_answer']]['text'],bits)
            self.assertTrue(all(len(q[l]['text'])==n for l in LETTERS))

    def test_new_mh_parameters_and_exact_output(self):
        q=self.by_id['nmmmh-de-cuong-2025-tonghop3-23'];v=q['answer_audit']['numeric']
        self.assertGreater(v['modulus'],sum(v['weights']));self.assertEqual(math.gcd(v['modulus'],v['multiplier']),1)
        self.assertTrue(all(a>sum(v['weights'][:i]) for i,a in enumerate(v['weights'])))
        expected=[v['weights'][i-1]*v['multiplier']%v['modulus'] for i in v['permutation']]
        self.assertEqual(expected,v['public']);self.assertEqual(expected,[707,405,777,85,858,810,371])

    def test_vernam_preserves_real_sixteen_character_key(self):
        q=self.by_id['nmmmh-de-cuong-2025-tonghop4-20'];v=q['answer_audit']['numeric']
        self.assertEqual(v['keystream'],'MATMADEMAKHOTHAT')
        self.assertEqual(len(v['keystream']),16);self.assertEqual(len(v['ciphertext']),16)
        self.assertEqual(v['plaintext'],'THANHTOANQUAMAQR');self.assertEqual(q['correct_answer'],'B')
        self.assertNotEqual(q['normalization']['kind'],'reconstructed_exercise_with_explicit_new_conditions')

    def test_jacobi_image_label_maps_to_correct_web_option(self):
        q=self.by_id[JACOBI_ID]
        self.assertEqual(q['correct_answer'],'C');self.assertEqual(q['C']['text'],'B')
        self.assertEqual(q['source_marked_answer'],'B')  # Preserve the incorrect source mark as evidence.
        self.assertEqual(int(sympy.jacobi_symbol(3,7)),-1)
        self.assertEqual(int(sympy.jacobi_symbol(7,3)),1)
        self.assertEqual(q['answer_audit']['valid_options'],['C'])

    def test_images_retained_and_never_data_urls(self):
        for id,old in self.frozen.items():
            q=self.by_id[id]
            old_paths={b['src'] for h in [old]+[old[l] for l in LETTERS] for b in h.get('question_blocks',h.get('blocks',[])) if b['type']=='image'}
            paths=set(q.get('images',[]))|set(q['normalization']['original_images'])
            self.assertLessEqual(old_paths,paths,id)
            for path in paths:
                self.assertTrue((ROOT/path).is_file(),path);self.assertFalse(path.startswith('data:'))
        for q in self.rows:
            self.assertLessEqual(len(q['hint'].splitlines()),4)
            self.assertIsNone(re.search(r'(?:đáp án đúng|chọn đáp án|chọn phương án|chọn)\s*[:=]?\s*[ABCD]\b',q['hint'],re.I),q['id'])

    def test_migration_idempotent(self):migrate(check=True)


if __name__=='__main__':unittest.main(verbosity=2)
