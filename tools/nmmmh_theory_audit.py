#!/usr/bin/env python3
"""Read-only validation and hint/input export for the independent theory audit.

python tools/nmmmh_theory_audit.py --check
python tools/nmmmh_theory_audit.py --hints
python tools/nmmmh_theory_audit.py --corrected-input QUESTION_ID

Candidates are human theory decisions stored in the artifact. This helper never
derives a candidate from an existing key and never writes app or question data.
"""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "subjects/nmmmh/audit/theory_audit.json"
LETTERS = "ABCD"


def get_hint(question_id, audit=None):
    """Return a simple text hint or None, without consulting a stored key."""
    if audit is None:
        audit = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    return audit["hints"].get(question_id)


def corrected_input(question_id, audit):
    """Apply explicit source overrides to the audit's frozen baseline snapshot."""
    q = next((q for q in audit["questions"] if q["id"] == question_id), None)
    if q is None:
        q = audit["supplemental_input_snapshots"][question_id]
    result = {"question": q["question"], "options": dict(q["options"])}
    for override in audit["corrected_input_overrides"]:
        if override["question_id"] != question_id:
            continue
        field = override["field"]
        if field == "question":
            assert result["question"] == override["old"]
            result["question"] = override["new"]
        else:
            letter, suffix = field.split(".")
            assert letter in LETTERS and suffix == "text"
            assert result["options"][letter] == override["old"]
            result["options"][letter] = override["new"]
    return result


def validate(audit):
    baseline = {q["id"]: q for q in audit["questions"]}
    corrected = {q["id"]: q for q in audit["post_source_corrected_candidates"]}
    assert len(baseline) == len(audit["questions"]) == 69
    supplemental_ids = set(audit.get("supplemental_input_snapshots", {}))
    assert set(baseline).isdisjoint(supplemental_ids)
    assert set(baseline) | supplemental_ids == set(corrected) == set(audit["hints"])
    assert audit["independence"]["old_answer_used_to_derive"] is False
    assert not set(baseline).intersection(audit["scope"]["numeric_handoff"])

    for label, rows in (("baseline", baseline), ("post_source_corrected", corrected)):
        counts = audit["counts"][label]
        core = {qid: q for qid, q in rows.items() if qid in baseline}
        verified = sum(q["candidate_answer"] is not None for q in core.values())
        assert counts["verified"] == verified
        assert counts["ambiguous"] == len(core) - verified
        assert counts["pending"] == 0
        assert counts["reviewed"] == len(core)
        for q in rows.values():
            candidate = q["candidate_answer"]
            assert candidate is None or candidate in LETTERS
            assert (q["status"] == "verified") == (candidate is not None)
            assert q["old_answer_comparison"]["comparison_performed_after_independent_decision"]
            assert q["reasoning"] and q["hint"] and q["source_citations"]
            assert set(q["option_evaluations"]) == set(q["options"]) == set(LETTERS)
            vector = q["truth_vector"] or q["answer_fit_vector"]
            assert set(vector) == set(LETTERS)
            citations = {s["source_id"] for s in q["source_citations"]}
            for letter in LETTERS:
                ev = q["option_evaluations"][letter]
                assert ev["value"] is None or type(ev["value"]) is bool
                assert ev["value"] == vector[letter]
                assert ev["reasoning"] and ev["source_ids"]
                assert set(ev["source_ids"]).issubset(citations)
            assert q["vector_complete"] == all(type(v) is bool for v in vector.values())
            if candidate:
                assert q["vector_complete"], q["id"]
                stem = q["question"].lower()
                negative = any(term in stem for term in ("sai", "không đúng", "không là"))
                if all(vector.values()):
                    assert not negative and candidate == "D", q["id"]
                else:
                    matching = [k for k, v in vector.items() if v is not negative]
                    assert matching == [candidate], (q["id"], matching, candidate)

    for qid, q in corrected.items():
        assert q["corrected_input"] == corrected_input(qid, audit), qid
        assert q["question"] == q["corrected_input"]["question"]
        assert q["options"] == q["corrected_input"]["options"]

    supplement = [corrected[qid] for qid in supplemental_ids]
    if supplement:
        counts = audit["counts"]["supplemental"]
        assert counts["reviewed"] == len(supplement)
        assert counts["verified"] == sum(q["candidate_answer"] is not None for q in supplement)
        assert counts["pending"] == 0

    # Check actual published text, not key equality, against the explicit input.
    manifest = json.loads((ROOT / "subjects/nmmmh/manifest.json").read_text())
    published = {}
    for exam in manifest["exams"]:
        for q in json.loads((ROOT / exam["question_file"]).read_text()):
            published[q["id"]] = q
    for qid, q in corrected.items():
        current = published[qid]
        actual = {"question": current["question"], "options": {k: current[k]["text"] for k in LETTERS}}
        assert actual == q["corrected_input"], f"Published input drift: {qid}"

    for snapshot in audit["source_review_snapshots"]:
        digest = hashlib.sha256((ROOT / snapshot["path"]).read_bytes()).hexdigest()
        assert digest == snapshot["sha256"], f"Source report changed: {snapshot['path']}"
    return audit["counts"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--hints", action="store_true")
    parser.add_argument("--corrected-input", metavar="QUESTION_ID")
    args = parser.parse_args()
    audit = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    if args.hints:
        result = audit["hints"]
    elif args.corrected_input:
        result = corrected_input(args.corrected_input, audit)
    elif args.check:
        result = {"validation": "passed", "counts": validate(audit)}
    else:
        result = audit["counts"]
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
