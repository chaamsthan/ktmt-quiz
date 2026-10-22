#!/usr/bin/env python3
"""Source, decision, crop-provenance and migration invariants (stdlib only)."""
import argparse
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'subjects/nmmmh/audit'
SOURCE=None


def read(path):return json.loads(path.read_text())


class DataAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=read(ROOT/'subjects/nmmmh/manifest.json')
        cls.rows=[q for e in cls.manifest['exams'] for q in read(ROOT/e['question_file'])]
        cls.by_id={q['id']:q for q in cls.rows}
        cls.overrides=read(AUDIT/'approved_changes.json')
        cls.originals=read(AUDIT/'single-answer-review/original_questions.json')
        cls.reference_decisions=read(AUDIT/'single-answer-review/decisions.json')

    def test_all_questions_and_order_preserved(self):
        self.assertEqual(len(self.rows),173);self.assertEqual(len(self.by_id),173)
        self.assertEqual(len(self.manifest['exams']),5)
        for exam in self.manifest['exams']:
            rows=[q for q in self.rows if q['source_exam_id']==exam['id']]
            self.assertEqual(len(rows),exam['question_count'])
            self.assertEqual([q['source_order'] for q in rows],sorted(q['source_order'] for q in rows))
        if SOURCE:
            original=[q for q in read(SOURCE/'DAPAN_KIEMCHUNG/questions_verified.json') if q['source_exam_id']!='de-thi-k16-1']
            self.assertEqual(set(self.by_id),{q['id'] for q in original})
            for exam in self.manifest['exams']:
                expected=[(q['id'],q['source_question_number'],q['source_order']) for q in original if q['source_exam_id']==exam['id']]
                actual=[(q['id'],q['source_question_number'],q['source_order']) for q in self.rows if q['source_exam_id']==exam['id']]
                self.assertEqual(actual,expected)

    def test_decisions_are_complete_and_safe(self):
        decisions=read(AUDIT/'answer_decisions.json')
        self.assertEqual({d['id'] for d in decisions},set(self.by_id))
        for q in self.rows:
            if q['id'] in self.reference_decisions:
                d=self.reference_decisions[q['id']]
                self.assertEqual(q['correct_answer'],d['correct_answer'])
                self.assertEqual(q['answer_audit']['valid_options'],[d['correct_answer']])
                self.assertEqual([l for l,c in d['option_checks'].items() if c['matches']],[q['correct_answer']])
                self.assertTrue(d['reference_pages'])
                self.assertEqual(q['verification_status'],'verified')
                continue
            d=self.overrides[q['id']]['answer_decision']
            self.assertEqual(q['correct_answer'],d['correct_answer'])
            self.assertTrue(d['method']);self.assertTrue(d['evidence'])
            self.assertEqual(q['verification_status'],d['status'])
            if q['correct_answer']:
                self.assertIn(q['correct_answer'],'ABCD')
                self.assertEqual(d['status'],'verified')
                self.assertIn(q['correct_answer'],d['valid_options'])
            else:self.assertTrue(q['needs_review'])

    def test_source_comparisons_cover_every_record(self):
        self.assertEqual(set(self.overrides),set(self.by_id))
        for q in self.rows:
            ref=q['source_reference']
            self.assertTrue(ref['pages']);self.assertEqual(len(ref['pdf_sha256']),64)
            if SOURCE:self.assertEqual(hashlib.sha256((SOURCE/ref['file']).read_bytes()).hexdigest(),ref['pdf_sha256'])

    def test_options_and_corrections_match_recorded_evidence(self):
        for q in self.rows:
            for letter in 'ABCD':
                self.assertEqual(q[letter]['source_label'],letter)
                self.assertTrue(q[letter]['text'] or q[letter].get('blocks'))
            # The previous source-comparison audit is immutable historical
            # evidence. Check it against the retained pre-normalization row.
            q=self.originals.get(q['id'],q)
            for edit in self.overrides[q['id']]['edits']:
                field=edit['field']
                if field in 'ABCD' and len(field)==1:value=q[field]['text']
                elif field=='question':value=q['question']
                else:value=q['question_blocks'][int(re.search(r'\[(\d+)\]',field)[1])]['text']
                self.assertEqual(value,edit['new'],q['id'])

    def test_new_crops_belong_to_exact_question_and_match_hash(self):
        assets={r['path']:r['sha256'] for r in read(AUDIT/'source_other_review.json')['figure_assets']}
        for row in read(AUDIT/'source_k16_review.json')['questions']:
            for image in row['image_replacements']:assets[image['new']]=image['sha256']
        self.assertEqual(len(assets),28)
        for q in self.rows:
            q=self.originals.get(q['id'],q)
            replacements=self.overrides[q['id']]['image_replacements']
            for image in replacements:
                self.assertEqual(Path(image['new']).name,q['id']+'-figure.png')
                self.assertEqual(hashlib.sha256((ROOT/image['new']).read_bytes()).hexdigest(),assets[image['new']])
                blocks=q['question_blocks']+sum((q[l]['blocks'] for l in 'ABCD'),[])
                self.assertTrue(any(b.get('src')==image['new'] and b.get('original_src')==image['old'] for b in blocks))
            for holder in [q]+[q[l] for l in 'ABCD']:
                for block in holder.get('question_blocks',holder.get('blocks',[])):
                    if block['type']=='image':
                        self.assertNotIn('base64',block['src']);self.assertTrue((ROOT/block['src']).is_file())

    def test_hints_short_and_no_explicit_answer(self):
        for q in self.rows:
            self.assertTrue(q['hint']);self.assertLessEqual(len(q['hint'].splitlines()),4)
            self.assertIsNone(re.search(r'(?:đáp án đúng|chọn đáp án|chọn phương án|chọn)\s*[:=]?\s*[ABCD]\b',q['hint'],re.I),q['id'])

    def test_chapter_membership_covers_same_source_bank(self):
        chapters={c['id'] for c in self.manifest['chapters']}
        for q in self.rows:
            self.assertTrue(q['chapter_ids']);self.assertIn(q['chapter_id'],q['chapter_ids'])
            self.assertLessEqual(set(q['chapter_ids']),chapters)
        for exam in self.manifest['exams']:
            for chapter,count in exam['chapter_counts'].items():
                self.assertEqual(count,sum(chapter in q['chapter_ids'] for q in self.rows if q['source_exam_id']==exam['id']))

    def test_theory_uses_current_source_corrected_input(self):
        for row in read(AUDIT/'theory_audit.json')['post_source_corrected_candidates']:
            q=self.originals.get(row['id'],self.by_id[row['id']]);data=row['corrected_input']
            self.assertEqual(data['question'],q['question'],q['id'])
            self.assertEqual(data['options'],{l:q[l]['text'] for l in 'ABCD'},q['id'])

    def test_known_corrections_and_uncertainties(self):
        self.assertEqual(self.by_id['nmmmh-de-thi-k16-3-2022']['correct_answer'],'C')
        self.assertEqual(self.by_id['nmmmh-de-thi-k16-2-35']['correct_answer'],'A')
        self.assertEqual(self.by_id['nmmmh-de-thi-at17-bo-1-3']['correct_answer'],'B')
        self.assertEqual(self.by_id['nmmmh-de-thi-k16-3-2056']['correct_answer'],'D')
        self.assertFalse(any(q['source_exam_id']=='de-thi-k16-1' for q in self.rows))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path)
    args,rest=parser.parse_known_args();SOURCE=args.source
    unittest.main(argv=[__file__,*rest],verbosity=2)
