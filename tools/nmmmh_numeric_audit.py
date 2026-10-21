#!/usr/bin/env python3
"""Independent NMMMH arithmetic audit. Python 3.10+, standard library only.

Run: python tools/nmmmh_numeric_audit.py
No answer metadata is passed to the solver. Published keys are compared only
after calculation. A candidate is an option matching the requested predicate,
including each true option and a true conjunction in composite questions.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LETTERS = "ABCD"
HAC8 = "https://cacr.uwaterloo.ca/hac/about/chap8.pdf"
HINTS = {
    "orders": "Nhân lặp modulo n; lấy số mũ dương đầu tiên cho kết quả 1.",
    "generators": "Tính φ(n), rồi so sánh bậc của từng phần tử với φ(n).",
    "generator_count": "Đếm các đơn vị có bậc đúng bằng φ(n).",
    "gcd": "Dùng thuật toán Euclid cho từng phương án, rồi xét yêu cầu của đề.",
    "euler": "Phân tích n; φ(n) = n ∏(1 − 1/p) với p là các ước nguyên tố khác nhau.",
    "logs": "Tìm x sao cho g^x ≡ y (mod p); kiểm tra mọi phương án.",
    "gf": "Nhân đa thức trên GF(2), rút gọn theo x⁸+x⁴+x³+x+1.",
    "mix": "Lấy hàng hệ số và cột trạng thái đúng chỉ số, nhân GF(2⁸), cộng bằng XOR.",
    "hill": "Đổi A=0,…,Z=25; nhân từng vector hàng 2 ký tự với ma trận modulo 26.",
    "affine": "Lập ax+b ≡ y (mod 26) cho từng cặp; yêu cầu gcd(a,26)=1.",
    "autokey": "Nối mầm khóa với bản rõ; cộng mã chữ modulo 26.",
    "elgamal": "β=α^a; γ=α^k; δ=mβ^k (mod p); khóa riêng là a.",
    "ecc": "Kiểm tra điểm trên đường cong rồi dùng cộng điểm và nhân vô hướng.",
    "rsa_signature": "n=pq, φ=(p−1)(q−1), e=d⁻¹ mod φ; S=m^d mod n.",
    "rabin": "n=pq, c=m² mod n; liệt kê các căn và kiểm tra từng phát biểu.",
    "merkle": "Khóa công khai thứ i là W·M[π(i)] mod M_modulus.",
    "knapsack": "Kiểm tra mỗi phần tử lớn hơn tổng trước nó; duyệt các vector bit để kiểm tra tổng.",
    "dh": "So sánh (g^a)^b và (g^b)^a modulo p.",
    "tonelli": "Phân tích p−1=2^s·t; chạy đúng vòng i của thuật toán trong đề.",
    "square_multiply": "Duyệt bit số mũ từ thấp lên cao; lưu A và b sau mỗi bước.",
    "euclid": "Cập nhật thương, dư và hai hệ số Bézout; đối chiếu đúng cột bị khuyết.",
    "des_s1": "Hai bit ngoài chọn hàng; bốn bit giữa chọn cột của S1.",
    "des_p": "Bit đầu ra thứ i lấy từ bit đầu vào P[i] (chỉ số bắt đầu từ 1).",
    "unit_membership": "a thuộc nhóm đơn vị modulo n khi và chỉ khi gcd(a,n)=1.",
    "rc4": "Khởi tạo S[i]=i, j=0; cập nhật j=(j+S[i]+T[i]) mod 256 rồi swap.",
    "group_propositions": "Nếu nhóm cyclic có bậc h thì số phần tử sinh là φ(h); dùng định lý Lagrange cho bậc phần tử.",
    "congruence_propositions": "Tính các số dư; phép chia cho phép r=0 và các đại diện cùng dư thuộc cùng lớp.",
    "totient_multiplicativity": "Dùng công thức tích của φ và định lý phần dư Trung Hoa khi gcd(m,n)=1.",
    "rsa_propositions": "Kiểm tra mô-đun n khi mã/giải mã và mô-đun φ(n) khi tính nghịch đảo số mũ.",
    "des_schedule": "Đối chiếu lịch dịch 16 vòng của DES; PC-1 bỏ 8 bit chẵn lẻ, PC-2 chọn 48 bit.",
}


def norm(text):
    return unicodedata.normalize("NFKC", text).replace("−", "-").replace("–", "-")


def nums(text):
    return [int(x) for x in re.findall(r"(?<![A-Za-z])[-+]?\d+", norm(text))]


def format_hint(row):
    """UI helper: never discloses a stored answer or treats pending as proved."""
    hint = HINTS.get(row.get("method"), "Đọc các dữ kiện và kiểm tra từng phương án độc lập.")
    if row.get("status") in {"pending", "insufficient_source", "ambiguous_source", "partial_proposition"}:
        hint += " Cần đối chiếu dữ kiện/ảnh nguồn; chưa có kết luận đầy đủ."
    return hint


def phi(n):
    value, remaining, p = n, n, 2
    while p * p <= remaining:
        if remaining % p == 0:
            value -= value // p
            while remaining % p == 0:
                remaining //= p
        p += 1
    if remaining > 1:
        value -= value // remaining
    return value


def order(a, n):
    if math.gcd(a, n) != 1:
        return None
    v = 1
    for k in range(1, phi(n) + 1):
        v = v * a % n
        if v == 1:
            return k
    raise AssertionError("Unit order must divide phi(n)")


def jacobi(a, n):
    assert n > 0 and n % 2
    sign = 1
    a %= n
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5):
                sign = -sign
        a, n = n, a
        if a % 4 == n % 4 == 3:
            sign = -sign
        a %= n
    return sign if n == 1 else 0


def gf_mul(a, b):
    # Carryless polynomial product followed by explicit long division.
    value = 0
    for i in range(b.bit_length()):
        if b >> i & 1:
            value ^= a << i
    while value.bit_length() > 8:
        value ^= 0x11B << (value.bit_length() - 9)
    return value


def ec_add(P, Q, p, a):
    if P is None:
        return Q
    if Q is None:
        return P
    x, y = P
    u, v = Q
    if x == u and (y + v) % p == 0:
        return None
    slope = ((3*x*x+a) * pow(2*y, -1, p) if P == Q
             else (v-y)*pow(u-x, -1, p)) % p
    r = (slope*slope-x-u) % p
    return (r, (slope*(x-r)-y) % p)


def ec_mul(k, P, p, a):
    R = None
    while k:
        if k & 1:
            R = ec_add(R, P, p, a)
        P = ec_add(P, P, p, a)
        k >>= 1
    return R


def hill(text, matrix):
    v = [ord(c)-65 for c in text.upper() if "A" <= c <= "Z"]
    assert len(v) % 2 == 0
    return "".join(chr((v[i]*matrix[0][j]+v[i+1]*matrix[1][j]) % 26+65)
                   for i in range(0, len(v), 2) for j in range(2))


def subset_solutions(seq, total):
    return [list(bits) for bits in itertools.product((0, 1), repeat=len(seq))
            if sum(a*b for a, b in zip(seq, bits)) == total]


def increasing(seq):
    return [{"value": x, "previous_sum": sum(seq[:i]), "greater": x > sum(seq[:i])}
            for i, x in enumerate(seq)]


def grab(pattern, text, flags=0):
    match = re.search(pattern, text, flags)
    if not match:
        raise ValueError(f"Unparsed required source field: {pattern}")
    return match


def parameter(text, name):
    return int(grab(r"(?<!\w)" + re.escape(name) + r"\s*=\s*(\d+)", text)[1])


def option_texts(q):
    return {c: norm(q[c]["text"]) for c in LETTERS}


def finish(method, inputs, computed, checks, notes=(), status=None):
    """Every solver must submit an explicit comparison for every option."""
    assert set(checks) == set(LETTERS)
    checks = {c: dict(checks[c]) for c in LETTERS}
    candidates = [c for c in LETTERS if checks[c].get("matches") is True]
    unknown = [c for c in LETTERS if checks[c].get("matches") is None]
    if status is None:
        status = ("partial_proposition" if unknown else "unique_match" if len(candidates) == 1
                  else "multiple_matches" if candidates else "no_match")
    return {"method": method, "status": status, "inputs": inputs, "computed": computed,
            "candidates": candidates, "option_checks": checks, "notes": list(notes)}


def equal_options(method, inputs, expected, values, notes=(), status=None):
    checks = {c: {"value": values[c], "matches": values[c] == expected} for c in LETTERS}
    return finish(method, inputs, expected, checks, notes, status)


def propositions(method, q, inputs, computed, checks, notes=(), status=None):
    false_requested = bool(re.search(r"\bSAI\b|KHÔNG", q["question"], re.I))
    # Do not impose the customary 'D overrides A/B/C' convention. Every true
    # statement and the conjunction are independently evaluated and exported.
    for c in LETTERS:
        text = q[c]["text"].lower()
        if "tất cả" in text or "đều đúng" in text or "cả a, b" in text:
            truth = [checks[x]["truth"] for x in LETTERS if x != c]
            checks[c] = {"truth": False if False in truth else None if None in truth else True,
                         "evidence": {"conjunction_of": [x for x in LETTERS if x != c]}}
    for check in checks.values():
        truth = check["truth"]
        check["matches"] = None if truth is None else truth != false_requested
    result = finish(method, {**inputs, "requested_truth": not false_requested}, computed, checks, notes, status)
    aggregates = [c for c in LETTERS if isinstance(checks[c].get("evidence"),dict)
                  and checks[c]["evidence"].get("conjunction_of") and checks[c]["matches"] is True]
    result["conventional_candidates"] = aggregates or result["candidates"]
    result["aggregate_policy"] = "candidates contains every matching statement; conventional_candidates prefers a matching explicit all-of-the-above conjunction"
    return result


def unknown_checks(reason):
    return {c: {"matches": None, "reason": reason} for c in LETTERS}


# Manual input transcriptions from images actually opened during this audit.
# They contain inputs/blank locations only, never computed outputs/answers.
# Full SHA-256 pinning prevents silently applying a transcription to a new image.
IMAGE_INPUTS = {
    "27f642010dea20e01056.jpg": {
        "sha256": "27f642010dea20e010562b8af89b887a94debcbc6f0d78ffeaae82e1bb58371d",
        "state": [["63", "EB", "9F", "A0"], ["2F", "93", "92", "C0"],
                  ["AF", "C7", "AB", "30"], ["A2", "20", "CB", "2B"]]},
    "35899c0e1f21223fc251.jpg": {
        "sha256": "35899c0e1f21223fc2518b187d48905772c2318c36d10b59acb7b37399b3a1e9",
        "initial_pair": [1120, 311], "blank_row": 6,
        "columns": ["q", "r", "x", "y", "a", "b", "x2", "x1", "y2", "y1"]},
    "1862285d17e232d48e64.jpg": {
        "sha256": "1862285d17e232d48e6492caba114f0f732fc96640d363754a85c1cd9c543140",
        "blank_cells": [["bit", 5], ["bit", 6], ["A", 5], ["A", 6], ["b", 5], ["b", 6]]},
    "9251b90a0b3f1b5b57c7.jpg": {
        "sha256": "9251b90a0b3f1b5b57c7efb346eadd8de1355c0910fdeab7faf5c3fc727a9a31",
        "C": "10010111111011001001011101010110",
        "P": [16,7,20,21,29,12,28,17,1,15,23,26,5,18,31,10,2,8,24,14,32,27,3,9,19,13,30,6,22,11,4,25],
        "shown": "01100??1101100???111000101??1110"},
    "5dcf9227dd4f9f236032.png": {
        "sha256": "5dcf9227dd4f9f236032523caef2200e263267139d3598b528a9a162691dfe8c",
        "C": "10010111111011001001011101010110",
        "P": [16,7,20,21,29,12,28,17,1,15,23,26,5,18,31,10,2,8,24,14,32,27,3,9,19,13,30,6,22,11,4,25],
        "shown": "01100?1?101100???111000101??1110"},
}

# Supplemental inputs independently read from complete original-page crops.
# These survive replacement of the old, defective published raster. Preview
# hashes document what was inspected, not a lock on future published JSON.
_STATE = [["63","EB","9F","A0"],["2F","93","92","C0"],
          ["AF","C7","AB","30"],["A2","20","CB","2B"]]
_CELLS = [["bit",5],["bit",6],["A",5],["A",6],["b",5],["b",6]]
SOURCE_INPUTS = {
    "nmmmh-de-thi-k16-3-2052": {
        "symbol_interpretation":"Jacobi_or_Legendre",
        "source_note":"Original prints an unlabelled symbol with composite denominator 235. Keep the requested Jacobi/Legendre alternatives explicit even after removal of an editorial label."},
    "nmmmh-de-thi-k16-2-6": {
        "state": _STATE,
        "source_review": "subjects/nmmmh/audit/source_k16_review.json",
        "source_page":8,
        "original_source":"DeThiPDF/Đề-K16/Đề 2/248710978_937086153554118_7890491191277638242_n.png",
        "inspected_preview":"/tmp/nmmmh-source-review/crop-k16-2-q6.png",
        "inspected_preview_sha256":"d3c8b2ffe9c233ee1a3c38ea8354746b3382b83c8916c62de8547ece449a199b"},
    "nmmmh-de-thi-k16-3-2049": {
        "blank_cells":_CELLS,
        "source_review":"subjects/nmmmh/audit/source_k16_review.json",
        "source_page":7,
        "original_source":"DeThiPDF/Đề-K16/Đề 3/279913163_1485804291815169_6485129110588514982_n.png",
        "inspected_preview":"/tmp/nmmmh-source-review/crop-k16-3-q2049.png",
        "inspected_preview_sha256":"b3db8addb7d831652de1c560e83247e168c26911a51f40b0ee7067cbc8153857"},
    "nmmmh-de-thi-mat-ma-2021-trac-nghiem-7": {
        "blank_cells":_CELLS,
        "source_review":"subjects/nmmmh/audit/source_other_review.json",
        "source_page":2,"original_source":"DeThiPDF/dematma2021tracnghiem.pdf",
        "inspected_preview":"/tmp/nmmmh-source-review/other-2021-q7-recrop-preview.png",
        "inspected_preview_sha256":"5c84ef0d0dfe65494ae2bb4ef8d99b95fe5f56a236e472196f10ae0dc42a58b3"},
    "nmmmh-de-thi-mat-ma-2021-trac-nghiem-15": {
        "C":"10010111111011001001011101010110",
        "P":[16,7,20,21,29,12,28,17,1,15,23,26,5,18,31,10,2,8,24,14,32,27,3,9,19,13,30,6,22,11,4,25],
        "shown":"01100??1101100???111000101??1110",
        "source_review":"subjects/nmmmh/audit/source_other_review.json",
        "source_page":4,"original_source":"DeThiPDF/dematma2021tracnghiem.pdf",
        "inspected_preview":"/tmp/nmmmh-source-review/other-2021-q15-recrop-preview.png",
        "inspected_preview_sha256":"61cc8e9c488339053e70dc79549dd2ed492cb3f10840591b5f544f2669ad348b"},
    "nmmmh-de-thi-mat-ma-2021-trac-nghiem-17": {
        "state":_STATE,"source_review":"subjects/nmmmh/audit/source_other_review.json",
        "source_page":4,"original_source":"DeThiPDF/dematma2021tracnghiem.pdf",
        "inspected_preview":"/tmp/nmmmh-source-review/other-2021-q17-recrop-preview.png",
        "inspected_preview_sha256":"1818643505c6670941a1277c5a104f8a61a9730584785a7f6e8cf9745c7a83e5"},
}
for _question_id, _image_name in {
    "nmmmh-de-thi-at17-bo-1-7":"27f642010dea20e01056.jpg",
    "nmmmh-de-thi-at17-bo-1-13":"35899c0e1f21223fc251.jpg",
    "nmmmh-de-thi-nmmmh-35":"9251b90a0b3f1b5b57c7.jpg",
    "nmmmh-de-thi-nmmmh-36":"1862285d17e232d48e64.jpg",
    "nmmmh-de-thi-k16-2-27":"5dcf9227dd4f9f236032.png",
}.items():
    SOURCE_INPUTS[_question_id] = {"original_published_image":"images/nmmmh/"+_image_name,
                                   **IMAGE_INPUTS[_image_name]}


def image_input(q, root):
    for block in q.get("question_blocks") or []:
        if block.get("type") != "image":
            continue
        path = root / block["src"]
        item = IMAGE_INPUTS.get(path.name)
        if item and path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]:
            return {"image": block["src"], "provenance": "manually inspected input cells; pinned SHA-256", **item}
    return None


def classify(q):
    text = norm(q["question"])
    lower = text.lower()
    combined = lower + " " + " ".join(q[c]["text"].lower() for c in LETTERS)
    if "mixcolumns" in lower and re.search(r"x\d", text): return "mix"
    if "gf(2" in lower and "(03)" in text: return "gf"
    if "hill" in lower: return "hill"
    if "affine" in lower: return "affine"
    if "khóa chạy" in lower: return "autokey"
    if "elgamal" in lower and re.search(r"p\s*=\s*\d", text): return "elgamal"
    if "elliptic" in lower: return "ecc"
    if "rabin" in lower and re.search(r"p\s*=\s*\d", text): return "rabin"
    if "rsa" in lower and re.search(r"p\s*=\s*\d", text): return "rsa_signature"
    if "hellman" in lower and "hoán vị" in lower: return "merkle"
    if "diffie" in lower: return "dh"
    if "euclid" in lower: return "euclid"
    if "nhân bình phương" in lower: return "square_multiply"
    if "thuật toán" in lower and "căn bậc" in lower: return "tonelli"
    if "ksa" in lower and "rc4" in lower: return "rc4"
    if "s1" in lower and re.search(r"[01]{6}", text): return "des_s1"
    if "p(c)" in lower: return "des_p"
    if "log" in lower and re.search(r"log\d", text): return "logs"
    if "φ(" in text and "kết quả" in lower: return "euler"
    if "số phần tử sinh" in lower and re.search(r"Z\*?\d", text): return "generator_count"
    if "phần tử sinh" in lower and re.search(r"Z\*?\d", text): return "generators"
    if "phần tử sinh" in lower and "Z*n" in text: return "generators"
    if ("bậc của phần tử" in lower or "cấp của phần tử" in lower): return "orders"
    if "nguyên tố cùng nhau" in lower or "gcd(" in combined and "lớn nhất" in lower: return "gcd"
    if "không thuộc nhóm nhân" in lower: return "unit_membership"
    if any(w in combined for w in ("legendre", "thặng dư bậc hai", "(2/n)", "(158/235)")): return "jacobi"
    if "siêu tăng" in combined and ("dãy (" in combined or "dãy siêu tăng (" in combined): return "knapsack"
    if "cyclic" in combined: return "group_propositions"
    if "lớp tương đương" in combined: return "congruence_propositions"
    if "phi euler" in lower: return "totient_multiplicativity"
    if "rsa" in lower and "mod" in combined: return "rsa_propositions"
    if "sinh khóa vòng" in lower and "des" in lower: return "des_schedule"
    return None


def solve(q, root):
    method = classify(q)
    if method is None:
        return finish(None, {}, None, unknown_checks("No numerical calculation requested"),
                      ["Not numerically verified; outside arithmetic audit scope."], "not_numerical")
    try:
        return calculate(method, q, root)
    except (ValueError, IndexError, KeyError, TypeError, AssertionError) as error:
        return finish(method, {}, None, unknown_checks(str(error)),
                      [f"Required field/algorithm not resolved: {error}"], "unsupported")


def calculate(method, q, root):
    text = norm(q["question"])
    opts = option_texts(q)
    if method in {"orders", "generators", "generator_count", "unit_membership"}:
        match = re.search(r"Z\*?(\d+)", text)
        if match:
            n = int(match[1])
            ph = phi(n)
            inputs = {"modulus": n, "phi": ph}
            if method == "generator_count":
                generators = [a for a in range(1, n) if order(a, n) == ph]
                return equal_options(method, inputs, {"count": len(generators), "generators": generators},
                                     {c: {"count": int(opts[c]), "generators": generators} for c in LETTERS})
            if "a =" in text:
                a = parameter(text, "a")
                return equal_options(method, {**inputs, "element": a}, order(a, n),
                                     {c: int(opts[c]) for c in LETTERS})
            values = {c: int(opts[c]) for c in LETTERS}
            orders = {c: order(a, n) for c, a in values.items()}
            if method == "unit_membership":
                checks = {c: {"value": a, "gcd": math.gcd(a, n), "matches": math.gcd(a, n) != 1}
                          for c, a in values.items()}
                return finish(method, {**inputs, "elements": values}, {"gcds": {c: v["gcd"] for c,v in checks.items()}}, checks)
            if "nhỏ nhất" in text:
                if method == "orders":
                    target = min(o for o in orders.values() if o is not None)
                    checks = {c: {"order": orders[c], "matches": orders[c] == target} for c in LETTERS}
                else:
                    target = next(a for a in range(1, n) if order(a, n) == ph)
                    checks = {c: {"order": orders[c], "matches": values[c] == target} for c in LETTERS}
            else:
                target = ph
                negate = "không" in text.lower()
                checks = {c: {"order": orders[c], "matches": (orders[c] == ph) != negate} for c in LETTERS}
            return finish(method, {**inputs, "elements": values}, {"orders": orders, "target": target}, checks)
        # Question asks which multiplicative group is cyclic, one modulus per option.
        moduli = {c: int(grab(r"Z\*?(\d+)", opts[c])[1]) for c in LETTERS}
        computed = {c: {"phi": phi(n), "generators": [a for a in range(1, n) if order(a,n) == phi(n)]}
                    for c, n in moduli.items()}
        return finish(method, {"moduli": moduli}, computed,
                      {c: {"matches": bool(computed[c]["generators"]), **computed[c]} for c in LETTERS})
    if method == "gcd":
        pairs = {c: nums(v) for c, v in opts.items()}
        assert all(len(v) == 2 for v in pairs.values())
        values = {c: math.gcd(*v) for c, v in pairs.items()}
        if "lớn nhất" in text:
            checks = {c: {"value": values[c], "matches": values[c] == max(values.values())} for c in LETTERS}
        else:
            negate = "không" in text.lower()
            checks = {c: {"value": values[c], "matches": (values[c] == 1) != negate} for c in LETTERS}
        return finish(method, {"pairs": pairs}, values, checks)
    if method == "euler":
        n = int(grab(r"φ\((\d+)\)", text)[1])
        expected = phi(n)
        assert expected == sum(math.gcd(i, n) == 1 for i in range(n))
        return equal_options(method, {"n": n, "cross_check": "enumerated units"}, expected,
                             {c: int(opts[c]) for c in LETTERS})
    if method == "logs":
        g, y = map(int, grab(r"log(\d+)\s+(\d+)", text).groups())
        p = int(grab(r"Z\*?(\d+)", text)[1])
        roots = [i for i in range(phi(p)) if pow(g, i, p) == y]
        return finish(method, {"g": g, "y": y, "modulus": p}, {"exponents_in_0_phi": roots},
                      {c: {"exponent": int(opts[c]), "power": pow(g,int(opts[c]),p),
                           "matches": pow(g,int(opts[c]),p) == y} for c in LETTERS})
    if method == "gf":
        a, b = (int(x, 16) for x in grab(r"\(([0-9A-F]{2})\).*?\(([0-9A-F]{2})\)", text, re.I).groups())
        expected = gf_mul(a, b)
        values = {c: int(grab(r"([01 ]+)(?:2|$)", opts[c])[1].replace(" ", ""), 2) for c in LETTERS}
        return equal_options(method, {"a": a, "b": b, "reduction_polynomial": "0x11b"}, expected, values,
                             ["The explicit (03) product determines the operation; xtime alone normally means multiplication by 02."])
    if method == "dh":
        g, p = parameter(text, "g"), parameter(text, "p")
        a, b = map(int, grab(r"lần lượt là (\d+) và (\d+)", text).groups())
        sides = [pow(pow(g,a,p),b,p), pow(pow(g,b,p),a,p)]
        assert sides[0] == sides[1]
        return equal_options(method, {"g": g, "p": p, "a": a, "b": b, "two_sides": sides}, sides[0],
                             {c: int(opts[c]) for c in LETTERS})
    if method == "hill":
        plain = grab(r"(?:bản rõ[^'\"“]*['\"“]([A-Za-z ]+)['\"”])", text, re.I)[1]
        cipher = grab(r"bản mã(?: nhận được là)?\s*['\"“]?([A-Z]{4,})", text)[1]
        decrypt = "khóa giải mã" in text
        matrices = {}
        for c in LETTERS:
            tables = [b["rows"] for b in q[c].get("blocks", []) if b["type"] == "table"]
            digits = [int(v) for row in tables[0] for v in row] if tables else nums(opts[c])
            assert len(digits) == 4
            matrices[c] = [digits[:2], digits[2:]]
        expected = plain.upper() if decrypt else cipher
        checks = {}
        for c, matrix in matrices.items():
            output = hill(cipher if decrypt else plain, matrix)
            determinant = (matrix[0][0]*matrix[1][1]-matrix[0][1]*matrix[1][0]) % 26
            checks[c] = {"matrix": matrix, "determinant_mod26": determinant, "output": output,
                         "matches": output == expected and math.gcd(determinant,26) == 1}
        return finish(method, {"plaintext": plain, "ciphertext": cipher, "direction": "decrypt" if decrypt else "encrypt",
                               "alphabet": "A=0,...,Z=25", "vectors": "row"}, expected, checks)
    if method == "affine":
        pairs = [(int(x), int(y)) for y, x in re.findall(
            r"[A-Za-z]\((\d+)\) là (?:bản )?mã(?: hóa)? của [A-Za-z]\((\d+)\)", text)]
        assert len(pairs) == 2
        solutions = [[a,b] for a in range(26) for b in range(26) if math.gcd(a,26) == 1
                     and all((a*x+b) % 26 == y for x,y in pairs)]
        labels = re.findall(r"([A-Za-z])\((\d+)\)", text)
        conflicts = [{"letter": c, "printed_index": int(n), "alphabet_index": ord(c.upper())-65}
                     for c,n in labels if int(n) != ord(c.upper())-65]
        checks = {c: {"key": nums(opts[c]), "matches": nums(opts[c]) in solutions} for c in LETTERS}
        notes = []
        computed = {"solutions_using_explicit_indices": solutions}
        if conflicts:
            alpha_pairs = [(ord(x.upper())-65,ord(y.upper())-65) for y,x in re.findall(
                r"([A-Za-z])\(\d+\) là (?:bản )?mã(?: hóa)? của ([A-Za-z])\(\d+\)",text)]
            alternate = [[a,b] for a in range(26) for b in range(26) if math.gcd(a,26) == 1
                         and all((a*x+b)%26 == y for x,y in alpha_pairs)]
            computed["solutions_using_letter_labels"] = alternate
            for c in LETTERS:
                checks[c]["alternate_matches"] = nums(opts[c]) in alternate
            notes.append("Letter/index conflict. Candidates use printed numeric indices only; no unconditional verification.")
        return finish(method, {"pairs": pairs, "modulus": 26, "conflicts": conflicts}, computed, checks,
                      notes, "ambiguous_source" if conflicts else None)
    if method == "autokey":
        strings = re.findall(r"[“\"]([^”\"]+)[”\"]", text)
        assert len(strings) == 2
        plain, seed = (re.sub(r"[^A-Z]", "", s.upper()) for s in strings)
        key = (seed+plain)[:len(plain)]
        result = "".join(chr((ord(a)+ord(b)-130)%26+65) for a,b in zip(plain,key))
        repeat = (seed*((len(plain)+len(seed)-1)//len(seed)))[:len(plain)]
        repeated_result = "".join(chr((ord(a)+ord(b)-130)%26+65) for a,b in zip(plain,repeat))
        return equal_options(method, {"plaintext": plain, "seed": seed, "keystream": key,
                                      "alternative_repeated_vigenere": repeated_result}, result,
                             {c: re.sub(r"[^A-Z]", "", opts[c].upper()) for c in LETTERS},
                             ["Plaintext-autokey interpretation, as in the reference algorithm. Repeated Vigenere shown separately, not silently substituted."])
    return calculate_more(method, q, root)


def calculate_more(method, q, root):
    text = norm(q["question"])
    opts = option_texts(q)
    if method == "elgamal":
        p, a, k, m = (parameter(text, s) for s in ("p", "a", "k", "m"))
        alpha = parameter(text, "α")
        beta, gamma = pow(alpha,a,p), pow(alpha,k,p)
        delta = m*pow(beta,k,p) % p
        inv = pow(pow(gamma,a,p),-1,p)
        checks = {}
        for c, value in opts.items():
            low = value.lower()
            if "tất cả" in low or "đều đúng" in low:
                checks[c] = {"truth": None}
            elif "khóa riêng" in low:
                v = int(grab(r"=\s*(\d+)\s*\.?$", value)[1])
                checks[c] = {"truth": v == a, "claimed": v, "computed": a}
            elif "khóa công khai" in low:
                triple = re.search(r"\((\d+),\s*(\d+),\s*(\d+)\)", value)
                claimed = list(map(int,triple.groups())) if triple else int(grab(r"=\s*(\d+)\s*\.?$",value)[1])
                target = [p,alpha,beta] if triple else beta
                checks[c] = {"truth": claimed == target, "claimed": claimed, "computed": target}
            elif "khôi phục" in low:
                claimed = list(map(int,grab(r"=\s*(\d+)\s*[·.]\s*(\d+)\s*mod\s*(\d+)\s*=\s*(\d+)",value).groups()))
                checks[c] = {"truth": claimed == [inv,delta,p,m], "claimed": claimed,
                             "computed": [inv,delta,p,inv*delta % p]}
            elif "bản mã" in low:
                claimed = list(map(int,grab(r"\((\d+),\s*(\d+)\)", value).groups()))
                checks[c] = {"truth": claimed == [gamma,delta], "claimed": claimed, "computed": [gamma,delta]}
            else:
                checks[c] = {"truth": None, "reason": "Unrecognized ElGamal proposition"}
        return propositions(method,q,{"p":p,"alpha":alpha,"a":a,"k":k,"m":m},
                            {"beta":beta,"gamma":gamma,"delta":delta,"inverse_gamma_a":inv},checks)
    if method == "rsa_signature":
        p,qprime,d,m = (parameter(text,s) for s in ("p","q","d","m"))
        n,ph = p*qprime,(p-1)*(qprime-1)
        e = pow(d,-1,ph)
        sig = pow(m,d,n)
        checks = {}
        for c,value in opts.items():
            low = value.lower()
            if "xác minh" in low:
                # NFKC turns superscript digits into adjacent ordinary digits.
                pattern = r"=\s*(\d+)\^(\d+)\s*mod\s*(\d+)"
                found = re.search(pattern,value)
                if found:
                    s,exp,modulus = map(int,found.groups())
                else:
                    raw = q[c]["text"]
                    found = grab(r"=\s*(\d+)([⁰¹²³⁴⁵⁶⁷⁸⁹]+)\s*mod\s*(\d+)",raw)
                    s,exp,modulus = int(found[1]),int(norm(found[2])),int(found[3])
                recovered = pow(s,exp,modulus)
                checks[c] = {"truth": s == sig and modulus == n and recovered == m and (exp*d)%ph == 1,
                             "signature": s, "exponent": exp, "modulus": modulus,"recovered":recovered}
            elif "khóa công khai" in low:
                public = list(map(int,grab(r"\((\d+),\s*(\d+)\)",value).groups()))
                private = int(grab(r"khóa bí mật là (\d+)",value)[1])
                checks[c] = {"truth":public == [n,e] and private == d,"claimed_public":public,"computed_public":[n,e]}
            elif "giữ bí mật" in low:
                # The claim literally includes n, a public modulus, or phi(n).
                secret_phi = "φ(n)" in value
                checks[c] = {"truth": secret_phi,"evidence": "p,q,phi(n) are private parameters; n is public"}
            elif "chữ ký" in low or "chữ kí" in low or "sau khi" in low:
                v = parameter(value,"S")
                checks[c] = {"truth": v == sig,"claimed_signature":v,"computed_signature":sig}
            else:
                checks[c] = {"truth":None,"reason":"Unrecognized signature proposition"}
        return propositions(method,q,{"p":p,"q":qprime,"d":d,"m":m},
                            {"n":n,"phi":ph,"e":e,"signature":sig,"verified_message":pow(sig,e,n)},checks,
                            ["Signing requires gcd(d,phi(n))=1; a printed gcd(d,n) condition alone is insufficient in general."])
    if method == "rabin":
        p,qprime,m = (parameter(text,s) for s in ("p","q","m"))
        n,cipher = p*qprime,m*m % (p*qprime)
        roots = [v for v in range(n) if v*v % n == cipher]
        def egcd(a,b):
            if not b:return (a,1,0)
            g,x,y = egcd(b,a%b)
            return g,y,x-(a//b)*y
        _,aa,bb = egcd(p,qprime)
        intermediate = [aa,bb,pow(cipher,(p+1)//4,p),pow(cipher,(qprime+1)//4,qprime)]
        checks = {}
        for letter,value in opts.items():
            low = value.lower()
            if "tất cả" in low:
                checks[letter] = {"truth":None}
            elif "nghiệm" in low:
                stated_m = parameter(value,"m")
                claimed = list(map(int,grab(r"\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)",value).groups()))
                statement_cipher = stated_m*stated_m % n
                actual = [v for v in range(n) if v*v % n == statement_cipher]
                checks[letter] = {"truth":sorted(claimed) == actual,"claimed_roots":claimed,
                                 "statement_plaintext":stated_m,"statement_ciphertext":statement_cipher,"computed_roots":actual}
            elif "các giá trị a" in low:
                claimed = nums(value.split("lần lượt là",1)[1])
                checks[letter] = {"truth":claimed == intermediate,"claimed":claimed,"computed":intermediate}
            elif "đầu vào" in low:
                cc = parameter(value,"c")
                nn = re.search(r"n\s*=.*?=\s*(\d+)",value)
                if nn:
                    truth = cc == cipher and int(nn[1]) == n
                    claim = {"ciphertext":cc,"modulus":int(nn[1])}
                else:
                    pp,qq = parameter(value,"p"),parameter(value,"q")
                    truth = (cc,pp,qq) == (cipher,p,qprime)
                    claim = {"ciphertext":cc,"p":pp,"q":qq}
                checks[letter] = {"truth":truth,"claimed":claim}
            elif "bản mã c" in low:
                v = parameter(value,"c")
                checks[letter] = {"truth":v == cipher,"claimed":v,"computed":cipher}
            elif "Z" in value:
                v = int(grab(r"Z(\d+)",value)[1])
                checks[letter] = {"truth":v == n,"claimed_modulus":v,"computed_modulus":n}
            else:
                checks[letter] = {"truth":None,"reason":"Unrecognized Rabin proposition"}
        return propositions(method,q,{"p":p,"q":qprime,"m":m},
                            {"n":n,"ciphertext":cipher,"roots":roots,"a_b_r_s":intermediate,
                             "bezout":aa*p+bb*qprime},checks,
                            ["Each root proposition is checked against its own explicitly stated m, including m different from the stem."])
    if method == "ecc":
        p = int(grab(r"mod\s+(\d+)",text)[1])
        # Parse coefficients rather than assuming the reference's fixed curve.
        curve = grab(r"x(?:\^3|3)\s*\+\s*(?:(\d+)\s*[·*]?\s*)?x\s*\+\s*(\d+)",text)
        a,b = int(curve[1] or 1),int(curve[2])
        G = tuple(map(int,grab(r"G\s*=\s*\((\d+),\s*(\d+)\)",text).groups()))
        def point(pattern):return tuple(map(int,grab(pattern,text).groups()))
        def valid(P):return (P[1]*P[1]-P[0]**3-a*P[0]-b)%p == 0
        if "khóa riêng" in text:
            scalar = int(grab(r"n_?A\s*=\s*(\d+)",text)[1])
            expected = list(ec_mul(scalar,G,p,a))
            return equal_options(method,{"curve":{"p":p,"a":a,"b":b},"G":G,"scalar":scalar},expected,
                                 {c:nums(opts[c]) for c in LETTERS})
        k = parameter(text,"k")
        public = point(r"(?:P_?Pub|P_?A)\s*=\s*\((\d+),\s*(\d+)\)")
        message = point(r"P_?M\s*=\s*\((\d+),\s*(\d+)\)")
        claimed_shared = point(r"k\s*[·.]?\s*P_?(?:Pub|A)\s*=\s*\((\d+),\s*(\d+)\)")
        assert all(valid(P) for P in (G,public,message,claimed_shared))
        shared = ec_mul(k,public,p,a)
        first = ec_mul(k,G,p,a)
        second = ec_add(message,shared,p,a)
        expected = [list(first),list(second)]
        values = {c:[nums(opts[c])[:2],nums(opts[c])[2:]] for c in LETTERS}
        return equal_options(method,{"curve":{"p":p,"a":a,"b":b},"G":G,"k":k,"public_point":public,
                                      "message_point":message,"printed_kP":claimed_shared,"computed_kP":shared},
                             expected,values,[],"ambiguous_source" if shared != claimed_shared else None)
    if method == "merkle":
        permutation = [int(v) for v in re.findall(r"π\(\d+\)\s*=\s*(\d+)",text)]
        seq = nums(grab(r"[Dd]ãy siêu tăng[^({]*[({]([\d, ]+)[)}]",text)[1])
        w = int(grab(r"W\s*(?:được chọn là|=)\s*(\d+)",text)[1])
        modulus = int(grab(r"M\s*(?:được chọn là|=)\s*(\d+)",text)[1])
        assert sorted(permutation) == list(range(1,len(seq)+1))
        expected = [seq[i-1]*w % modulus for i in permutation]
        return equal_options(method,{"permutation":permutation,"private_sequence":seq,"multiplier":w,"modulus":modulus,
                                      "superincreasing_check":increasing(seq),"gcd_W_M":math.gcd(w,modulus)},
                             expected,{c:nums(opts[c]) for c in LETTERS})
    if method == "knapsack":
        if "Khẳng định" not in text:
            seq = nums(grab(r"siêu tăng\s*\(([^)]+)\)",text)[1])
            total = parameter(text,"S")
            solutions = subset_solutions(seq,total)
            checks = {}
            for c,value in opts.items():
                bits = [int(v) for v in value.strip()]
                checks[c] = {"bits":bits,"sum":sum(a*b for a,b in zip(seq,bits)),"matches":bits in solutions}
            return finish(method,{"sequence":seq,"target":total,"superincreasing_check":increasing(seq)},
                          {"solutions":solutions},checks)
        checks,computed = {},{}
        for c,value in opts.items():
            low = value.lower()
            if "dãy (" in low:
                seq = nums(grab(r"dãy\s*\(([^)]+)\)",value,re.I)[1])
                if "không có lời giải" in low:
                    target = parameter(value,"S")
                    solutions = subset_solutions(seq,target)
                    checks[c] = {"truth":not solutions,"sequence":seq,"target":target,"solutions":solutions}
                else:
                    trace = increasing(seq)
                    checks[c] = {"truth":all(v["greater"] for v in trace),"sequence":seq,"prefix_checks":trace}
            elif "vét cạn" in low:
                checks[c] = {"truth":bool(re.search(r"O\(2\^?n\)",value)),
                             "evidence":"n binary choices give 2^n subsets; incremental enumeration takes O(2^n) arithmetic operations"}
            elif "độ phức tạp O(n)" in value:
                checks[c] = {"truth":True,"evidence":"Reverse greedy scans n entries once when the sequence is superincreasing",
                             "derivation":"For largest b_i, all smaller entries sum to less than b_i. Thus s>=b_i forces choosing b_i, and s<b_i forces omitting it. Subtract when chosen and induct downward; n comparisons/subtractions.",
                             "reference":{"url":HAC8,"location":"Definition 8.34 and Algorithm 8.35 (book page 300)"}}
            elif "độ an toàn" in low and "merkle" in low:
                checks[c] = {"truth":True,"basis":"textbook computational design basis",
                             "derivation":"The public encryption equation is a subset sum in binary message bits; the private modular multiplier/permutation maps it to a superincreasing instance for greedy inversion.",
                             "reference":{"url":HAC8,"location":"Table 8.1; Algorithms 8.36-8.37; Note 8.40"},
                             "limitation":"True as a statement of design motivation. It does not prove security or a reduction from general subset-sum; basic Merkle-Hellman is broken (Note 8.40)."}
            elif "tất cả" in low:
                checks[c] = {"truth":None}
            else:
                checks[c] = {"truth":None,"reason":"Security assertion is not established by a subset calculation"}
        computed = {c:check for c,check in checks.items() if "prefix_checks" in check or "solutions" in check}
        return propositions(method,q,{},computed,checks,
                            ["Arithmetic options are computed; complexity options use operation-count proofs. Merkle-Hellman hardness wording, when present, is assessed as textbook design motivation, not a security theorem."])
    if method == "jacobi":
        checks = {}
        for c,value in opts.items():
            if "(2/n)" in value:
                expected = int(grab(r"\(2/n\)\s*=\s*(-?\d+)",value)[1])
                residues = [int(v) for v in grab(r"≡\s*(\d+).*?hoặc\s*(\d+)",value).groups()]
                actual = {str(r):(-1 if r in (3,5) else 1) for r in residues}
                checks[c] = {"truth":all(v == expected for v in actual.values()),"residue_classes_mod8":actual,
                             "evidence":"Jacobi supplementary law (2/n)=(-1)^((n²-1)/8), odd positive n"}
            elif "căn bậc hai" in value:
                radicand,modulus = map(int,grab(r"của\s+(\d+)\s+mod\s+(\d+)",value).groups())
                claimed = nums(value.split(":",1)[1])
                roots = [i for i in range(modulus) if i*i%modulus == radicand]
                checks[c] = {"truth":sorted(claimed) == roots,"claimed_roots":claimed,"computed_roots":roots}
            else:
                a,n,claim = map(int,grab(r"\((\d+)/(\d+)\)\s*=\s*(-?\d+)",value).groups())
                actual = jacobi(a,n)
                truth = actual == claim
                squares = None
                if "là thặng dư" in value:
                    squares = [i for i in range(n) if i*i % n == a % n]
                    truth &= bool(squares)
                checks[c] = {"truth":truth,"numerator":a,"denominator":n,"claimed_symbol":claim,
                             "computed_symbol":actual,"roots_if_residuosity_claimed":squares}
        interpretation = (q.get("numeric_inputs") or {}).get("symbol_interpretation")
        ambiguous = any(("legendre" in opts[c].lower() or interpretation == "Jacobi_or_Legendre") and "denominator" in check
                        and any(check["denominator"]%p == 0 for p in range(2,math.isqrt(check["denominator"])+1))
                        for c,check in checks.items())
        notes = ["Computed as Jacobi. A composite denominator does not define a Legendre symbol; the unlabelled source notation remains conditional, independently of any editorial label."] if ambiguous else []
        result = propositions(method,q,{}, {c:dict(v) for c,v in checks.items()},checks,notes,
                              "ambiguous_source" if ambiguous else None)
        if ambiguous:
            result["interpretations"] = {"jacobi":{"candidates":result["candidates"],"defined":True},
                                         "legendre":{"defined":False,"reason":"Composite denominator"}}
        return result
    return calculate_visual_or_theory(method,q,root)


def calculate_visual_or_theory(method,q,root):
    text = norm(q["question"])
    opts = option_texts(q)
    picture = image_input(q,root)
    extra = q.get("numeric_inputs") or {}
    if extra:
        picture = {**(picture or {}), **extra, "provenance": "explicit source-correction input"}
    if method == "mix":
        index = grab(r"x(\d)(\d)",text)
        r,c = int(index[1]),int(index[2])
        tables = [b["rows"] for b in q.get("question_blocks",[]) if b["type"] == "table"]
        numeric_tables = [t for t in tables if len(t) == 4 and all(len(row) == 4 and all(re.fullmatch(r"[0-9A-Fa-f]{2}",str(v)) for v in row) for row in t)]
        coefficients = [[2,3,1,1],[1,2,3,1],[1,1,2,3],[3,1,1,2]]
        provenance = "AES MixColumns standard coefficients; source state data"
        if numeric_tables:
            state = [[int(v,16) for v in row] for row in numeric_tables[-1]]
            if len(numeric_tables) > 1:
                coefficients = [[int(v,16) for v in row] for row in numeric_tables[0]]
            column = [state[i][c] for i in range(4)]
        elif picture and "state" in picture:
            state = [[int(v,16) if isinstance(v,str) else v for v in row] for row in picture["state"]]
            column = [state[i][c] for i in range(4)]
            provenance = picture
        else:
            match = re.search(r"cột\s+(\d+)\s+là\s*\(([^)]+)\)",text)
            if match and int(match[1]) == c:
                column = [int(v.strip(),16) for v in match[2].split(",")]
            elif extra.get("column"):
                column = extra["column"]
            else:
                return finish(method,{"row":r,"column_index":c},None,unknown_checks("State column missing in text/cropped image"),
                              ["No state inferred from answer choices or another question."],"insufficient_source")
        terms = [gf_mul(a,b) for a,b in zip(coefficients[r],column)]
        value = 0
        for term in terms:value ^= term
        values = {ch:int(grab(r"^([0-9A-Fa-f]{2})",opts[ch])[1],16) for ch in LETTERS}
        return equal_options(method,{"row":r,"column_index":c,"index_origin":0,"state_column":column,
                                      "coefficients":coefficients[r],"gf_products":terms,"source":provenance},value,values)
    if method == "euclid":
        if not picture or "initial_pair" not in picture:
            return finish(method,{},None,unknown_checks("Initial a,b and blank locations unavailable"),[],"insufficient_source")
        original_a,original_b = picture["initial_pair"]
        a,b,x2,x1,y2,y1 = original_a,original_b,1,0,0,1
        trace = []
        while b:
            quotient,remainder = divmod(a,b)
            x,y = x2-quotient*x1,y2-quotient*y1
            a,b,x2,x1,y2,y1 = b,remainder,x1,x,y1,y
            trace.append([quotient,remainder,x,y,a,b,x2,x1,y2,y1])
        wanted = trace[picture["blank_row"]-1]
        assert wanted[2]*original_a+wanted[3]*original_b == wanted[1]
        return equal_options(method,{"source":picture,"row_trace":trace},wanted,{c:nums(opts[c]) for c in LETTERS})
    if method == "tonelli":
        a,p,b = map(int,grab(r"của (\d+) mod (\d+)\s*\(chọn b\s*=\s*(\d+)\)",text).groups())
        requested = int(grab(r"vòng lặp i\s*=\s*(\d+)",text)[1])
        assert jacobi(a,p) == 1 and jacobi(b,p) == -1
        t,s = p-1,0
        while t % 2 == 0:t//=2;s+=1
        c,r = pow(b,t,p),pow(a,(t+1)//2,p)
        trace = []
        for i in range(1,s):
            d = pow(r*r*pow(a,-1,p)%p,2**(s-i-1),p)
            if d == p-1:r = r*c%p
            c = c*c%p
            trace.append({"i":i,"d":d,"r":r,"c":c})
        selected = trace[requested-1]
        expected = [selected[x] for x in ("d","r","c")]
        return equal_options(method,{"a":a,"p":p,"nonresidue_b":b,"requested_iteration":requested,
                                      "s":s,"t":t,"algorithm":"d=(r²/a)^(2^(s-i-1)); conditional r*=c; c*=c",
                                      "trace":trace},expected,{ch:nums(opts[ch]) for ch in LETTERS})
    if method == "square_multiply":
        raw = q["question"]
        power = re.search(r"tính (\d+)\^(\d+) mod (\d+)",raw)
        if power:
            a,k,n = map(int,power.groups())
        else:
            power = grab(r"tính (\d+)([⁰¹²³⁴⁵⁶⁷⁸⁹]+) mod (\d+)",raw)
            a,k,n = int(power[1]),int(norm(power[2])),int(power[3])
        A,b,trace = a,1,[]
        for i in range(k.bit_length()):
            bit = k>>i&1
            if bit:b = b*A % n
            trace.append({"i":i,"bit":bit,"A":A,"b":b})
            A = A*A % n
        assert b == pow(a,k,n)
        cells = picture.get("blank_cells") if picture else None
        if "k_i:" in text or "ki:" in text:
            cells = [["bit",5],["bit",6],["A",5],["A",6],["b",5],["b",6]]
        if not cells:
            return finish(method,{"base":a,"exponent":k,"modulus":n},{"trace":trace,"power":b},
                          unknown_checks("X1...X6 cell mapping missing in cropped source"),
                          ["Exponentiation independently computed, but options cannot be mapped to missing table cells."],"insufficient_source")
        expected = [trace[i][field] for field,i in cells]
        values = {ch:[int(v) for v in re.findall(r"X\d\s*=\s*(\d+)",opts[ch])] for ch in LETTERS}
        return equal_options(method,{"base":a,"exponent":k,"modulus":n,"trace":trace,"blank_cells":cells,
                                      "image_source":picture},expected,values)
    if method == "des_s1":
        # Standard algorithm constant, also printed in full in K16-2 question 21.
        S1 = [[14,4,13,1,2,15,11,8,3,10,6,12,5,9,0,7],
              [0,15,7,4,14,2,13,1,10,6,12,11,9,5,3,8],
              [4,1,14,8,13,6,2,11,15,12,9,7,3,10,5,0],
              [15,12,8,2,4,9,1,7,5,11,3,14,10,0,6,13]]
        bits = grab(r"[01]{6}",text)[0]
        rows = re.findall(r"Hàng \d:\s*([^\n]+)",text)
        if rows:
            S1 = [nums(row) for row in rows]
            assert len(S1) == 4 and all(len(row) == 16 for row in S1)
        if extra.get("S1"):S1 = extra["S1"]
        row,col = int(bits[0]+bits[-1],2),int(bits[1:-1],2)
        values = {ch:int(grab(r"^([01]{4})",opts[ch])[1],2) for ch in LETTERS}
        return equal_options(method,{"input_bits":bits,"row":row,"column":col,"S1":S1,
                                      "table_basis":"explicit text" if rows else "DES standard S1 algorithm constant; local raster fidelity not implied"},
                             S1[row][col],values)
    if method == "des_p":
        if not picture or "C" not in picture:
            return finish(method,{},None,unknown_checks("Full C/P/blank mask not available"),
                          ["Do not recover missing input bits by matching answer choices."],"insufficient_source")
        C,P,shown = picture["C"],picture["P"],picture["shown"]
        assert len(C) == len(P) == len(shown) == 32
        output = "".join(C[i-1] for i in P)
        blank_positions = [i for i,ch in enumerate(shown) if ch == "?"]
        expected = "".join(output[i] for i in blank_positions)
        contradictions = [{"position_1_based":i+1,"printed":bit,"calculated":output[i]}
                          for i,bit in enumerate(shown) if bit != "?" and bit != output[i]]
        checks = {ch:{"value":"".join(re.findall(r"[01]",opts[ch])),
                      "matches":"".join(re.findall(r"[01]",opts[ch])) == expected} for ch in LETTERS}
        notes = []
        if contradictions:notes.append("Fixed output cells contradict recomputed P(C); candidates match only the requested missing cells.")
        computed = {"output":output,"missing_bits":expected,"fixed_cell_conflicts":contradictions}
        if "Đọc lại từ ảnh" in text:
            # Audit the text fallback independently of the inspected raster too.
            cc = grab(r"Khối C[^:]*:[\s\n]*([01 |]+)",text)[1]
            textual_C = "".join(re.findall(r"[01]",cc))
            if textual_C != C:
                textual_out = "".join(textual_C[i-1] for i in P)
                computed["text_fallback"] = {"C":textual_C,"output":textual_out,
                                             "missing_bits":"".join(textual_out[i] for i in blank_positions)}
                notes.append("Text fallback differs from inspected source image; both calculations retained.")
        return finish(method,{"source":picture,"blank_positions_1_based":[i+1 for i in blank_positions]},computed,checks,
                      notes,"ambiguous_source" if contradictions or computed.get("text_fallback") else None)
    if method == "rc4":
        T = [int(grab(r"T\["+str(i)+r"\]\s*=\s*(\d+)",text)[1]) for i in (0,1)]
        S,j,trace = list(range(256)),0,[]
        for i,t in enumerate(T):
            j = (j+S[i]+t)%256
            S[i],S[j] = S[j],S[i]
            trace.append({"i":i,"j":j,"swap":[i,j]})
        checks = {}
        for ch,value in opts.items():
            indices,entries = value.split("S[i]:")
            indices = nums(indices)
            entries = nums(entries)
            assert len(indices) == len(entries)
            failures = [{"i":i,"claimed":v,"computed":S[i]} for i,v in zip(indices,entries) if S[i] != v]
            checks[ch] = {"matches":not failures,"listed_indices":indices,"listed_entries":entries,"conflicts":failures}
        return finish(method,{"T_prefix":T,"initial_state":"S[i]=i, j=0"},
                      {"trace":trace,"final_nonidentity_entries":{str(i):v for i,v in enumerate(S) if i != v}},checks)
    if method in {"group_propositions","congruence_propositions","totient_multiplicativity","rsa_propositions","des_schedule"}:
        return theory_calculation(method,q)
    return finish(method,{},None,unknown_checks("No arithmetic evaluator implemented"),[],"unsupported")


def theory_calculation(method,q):
    opts = option_texts(q)
    checks,computed = {},{}
    if method == "group_propositions":
        n = 7
        orders = {str(a):order(a,n) for a in range(1,n)}
        generators = [int(a) for a,v in orders.items() if v == phi(n)]
        computed = {"counterexample_modulus":n,"phi":phi(n),"orders":orders,
                    "generators":generators,"generator_count":len(generators),"phi_phi":phi(phi(n))}
        for c,value in opts.items():
            if "số phần tử sinh" in value:
                checks[c] = {"truth":False,"evidence":computed,
                             "derivation":"For a cyclic group of order h, g^k generates iff gcd(k,h)=1; count phi(h), not h"}
            elif "tất cả" in value.lower():checks[c] = {"truth":None}
            elif "t |" in value or "t|" in value:
                checks[c] = {"truth":True,"derivation":"Lagrange: cosets of <a> partition the finite group into sets of size ord(a)"}
            elif "cyclic" in value:
                checks[c] = {"truth":True,"derivation":"Definition: a cyclic group has a generator"}
            elif "ord(" in value:
                checks[c] = {"truth":True,"derivation":"If ord(alpha)=|G|, powers of alpha enumerate all elements of G"}
            else:checks[c] = {"truth":None,"reason":"Unparsed group statement"}
    elif method == "congruence_propositions":
        for c,value in opts.items():
            if "lớp tương đương" in value:
                pairs = re.findall(r"(-?\d+)\s*mod\s*(\d+)",value)
                remainders = [int(a)%int(n) for a,n in pairs]
                checks[c] = {"truth":len(set(remainders)) > 1,"residues":remainders,
                             "derivation":"Equal residues represent the same equivalence class, not distinct classes"}
            elif "phép chia" in value:
                strict = "0 < r" in value
                checks[c] = {"truth":not strict,"counterexample_if_strict":{"a":7,"n":7,"q":1,"r":0} if strict else None,
                             "derivation":"Division algorithm permits remainder zero"}
            elif "đại diện" in value or "phần dư như nhau" in value:
                checks[c] = {"truth":True,"derivation":"Canonical residue in [0,n) is unique; equality of residues iff n divides a-b"}
            else:checks[c] = {"truth":None}
        computed = {c:v for c,v in checks.items() if "residues" in v or "counterexample_if_strict" in v}
    elif method == "totient_multiplicativity":
        # CRT proves sufficiency and the product formula proves necessity for
        # positive m,n: shared prime factors make the ratio p/(p-1)>1.
        computed = {"coprime_example":{"m":4,"n":9,"lhs":phi(36),"rhs":phi(4)*phi(9)},
                    "noncoprime_counterexample":{"m":4,"n":6,"lhs":phi(24),"rhs":phi(4)*phi(6)}}
        for c,value in opts.items():
            good = bool(re.search(r"GCD\(m,\s*n\)\s*=\s*1",value))
            checks[c] = {"truth":good,"derivation":"CRT for gcd=1; common primes violate multiplicativity"}
    elif method == "rsa_propositions":
        p,qprime,e = 5,11,3
        n,ph = p*qprime,(p-1)*(qprime-1)
        d = pow(e,-1,ph)
        wrong_d = pow(e,-1,n)
        computed = {"witness":{"p":p,"q":qprime,"n":n,"phi":ph,"e":e,"d":d,"inverse_mod_n":wrong_d,
                                "message":2,"ciphertext":pow(2,e,n),
                                "wrong_decryption":pow(pow(2,e,n),wrong_d,n),
                                "wrong_phi_decryption":pow(pow(2,e,n),d,ph)},
                    "bad_e":{"n":n,"phi":ph,"e":2,"gcd_e_n":math.gcd(2,n),"gcd_e_phi":math.gcd(2,ph)}}
        for c,value in opts.items():
            low = value.lower()
            if "gcd(e," in low:
                truth = "φ(n)" in value
                checks[c] = {"truth":truth,"evidence":computed["bad_e"] if not truth else "Exponent must be invertible modulo phi(n)"}
            elif "khóa bí mật được tính" in low:
                checks[c] = {"truth":None if "f(n)" in value else "φ(n)" in value,
                             "evidence":computed["witness"],
                             "note":"Undefined f(n) cannot be silently replaced by phi(n)" if "f(n)" in value else ""}
                if "f(n)" in value:checks[c]["conditional_truth_if_f_means_phi"] = True
            elif "giải mã" in low:
                checks[c] = {"truth":"mod φ(n)" not in value,"evidence":computed["witness"]}
            elif "bản mã được tính" in low:
                checks[c] = {"truth":True,"derivation":"Definition of textbook RSA encryption y=x^e modulo n"}
            elif "độ an toàn" in low:
                checks[c] = {"truth":True,"basis":"textbook computational design basis",
                             "derivation":"Factoring n=pq reveals phi(n), then d=e^(-1) mod phi(n), enabling decryption.",
                             "reference":{"url":HAC8,"location":"Table 8.1; section 8.2; Algorithms 8.1-8.3"},
                             "limitation":"No claim that generic RSA inversion is proved equivalent to factoring; this evaluates the stated textbook basis."}
            else:checks[c] = {"truth":None}
    elif method == "des_schedule":
        shifts = [1,1,2,2,2,2,2,2,1,2,2,2,2,2,2,1]
        computed = {"standard_DES_left_shifts":shifts,"one_bit_rounds":[i+1 for i,v in enumerate(shifts) if v == 1],
                    "two_bit_rounds":[i+1 for i,v in enumerate(shifts) if v == 2],"key_bits":64,"after_PC1":56,"after_PC2":48}
        for c,value in opts.items():
            low = value.lower()
            if "tất cả" in low:checks[c] = {"truth":None}
            elif "tại các vòng" in value:
                rounds = nums(grab(r"tại các vòng (.*?) ta thực hiện",value)[1])
                bits = int(grab(r"dịch trái (\d+) bit",value)[1])
                checks[c] = {"truth":rounds == [i+1 for i,v in enumerate(shifts) if v == bits],
                             "claimed_rounds":rounds,"claimed_shift_bits":bits}
            elif "PC-1" in value and "PC-2" in value:
                checks[c] = {"truth":True,"derivation":"PC-1 selects/reorders 56 non-parity bits; rotate 28-bit halves; PC-2 selects 48 bits for each round"}
            else:checks[c] = {"truth":None}
    return propositions(method,q,{},computed,checks,
                        ["Symbolic theorem/definition reasoning is explicitly distinguished from numerical witnesses; finite witnesses do not prove universal claims."])


def correction_records(paths):
    """Read field patches from either source-review schema or a simple list.

    Simple schema: [{"id": source_id, "field": "question" or "A.text",
    "old": optional_expected_text, "new": replacement, "evidence": ...}].
    A row can also supply numeric_inputs containing input state/blank locations.
    No candidate/answer metadata from these files is consulted.
    """
    result,provenance = {},[]
    def visit(obj):
        if isinstance(obj,list):
            for item in obj:visit(item)
        elif isinstance(obj,dict):
            ident = obj.get("question_id",obj.get("id"))
            if ident:
                patches = obj.get("corrections",obj.get("mismatches",[]))
                if "field" in obj and "new" in obj:patches = [obj]
                for patch in patches:
                    if isinstance(patch.get("new"),str) and (patch.get("field") == "question" or
                       re.fullmatch(r"[ABCD]\.text|question_blocks\[\d+\]\.text",patch.get("field",""))):
                        result.setdefault(ident,[]).append({k:patch[k] for k in ("field","old","new","evidence") if k in patch})
                if isinstance(obj.get("numeric_inputs"),dict):
                    result.setdefault(ident,[]).append({"numeric_inputs":obj["numeric_inputs"]})
            for key,value in obj.items():
                if key not in {"corrections","mismatches","numeric_inputs","answer_audit","candidates"}:visit(value)
    for path in paths:
        raw = path.read_bytes()
        provenance.append({"path":str(path),"sha256":hashlib.sha256(raw).hexdigest()})
        visit(json.loads(raw))
    return result,provenance


def apply_corrections(q, patches):
    applied,conflicts = [],[]
    for patch in patches:
        if "numeric_inputs" in patch:
            q["numeric_inputs"] = {**q.get("numeric_inputs",{}),**patch["numeric_inputs"]}
            applied.append(patch)
            continue
        field,old,new = patch["field"],patch.get("old"),patch["new"]
        if field == "question":
            container,key = q,"question"
        elif re.fullmatch(r"[ABCD]\.text",field):
            container,key = q[field[0]],"text"
        else:
            index = int(grab(r"\[(\d+)\]",field)[1])
            container,key = q["question_blocks"][index],"text"
        current = container[key]
        if current == new:
            continue
        if old is not None and current != old:
            conflicts.append({**patch,"current":current,"reason":"Patch old text differs from current input; not applied"})
            continue
        container[key] = new
        # Stems have both flattened and block forms. Keep the local audit-only
        # view consistent; never write back into the published exam.
        if field.startswith("question_blocks") and old and old in q["question"]:
            q["question"] = q["question"].replace(old,new)
        applied.append(patch)
    return applied,conflicts


def solver_input(original):
    """The sole boundary between published records and the independent solver."""
    q = {k: original.get(k) for k in ("question","question_blocks",*LETTERS)}
    for letter in LETTERS:
        q[letter] = {k:original[letter].get(k) for k in ("text","blocks")}
    if original["id"] in SOURCE_INPUTS:
        q["numeric_inputs"] = SOURCE_INPUTS[original["id"]]
    return json.loads(json.dumps(q))


def build_report(root, corrections=()):
    patches,correction_sources = correction_records(corrections)
    rows, files = [], []
    for path in sorted((root / "subjects/nmmmh/exams").glob("*.json")):
        raw = path.read_bytes()
        files.append({"path": str(path.relative_to(root)), "sha256": hashlib.sha256(raw).hexdigest()})
        for original in json.loads(raw):
            # Strict allowlist: source_text, answer_audit, explanations, selected
            # screenshot labels and every answer key are outside the solver.
            q = solver_input(original)
            baseline = solve(q,root) if patches.get(original["id"]) else None
            applied,conflicts = apply_corrections(q,patches.get(original["id"],[]))
            result = solve(q, root)
            if conflicts:
                result["status"] = "ambiguous_source"
                result["notes"].append("Explicit source corrections conflict with current source text; inspect source_corrections.conflicts.")
            row = {k: original.get(k) for k in ("id", "source_exam_id", "source_question_number", "source_file")}
            row.update(result)
            row.setdefault("conventional_candidates",row["candidates"])
            row["candidate_set_complete"] = row["status"] in {"unique_match","multiple_matches","no_match"}
            row["unresolved_options"] = [c for c,check in row["option_checks"].items() if check.get("matches") is None]
            row["source_corrections"] = {"applied":applied,"conflicts":conflicts}
            if applied and baseline is not None:row["published_derivation_before_corrections"] = baseline
            row["input_data"] = q
            row["published_proof_key"] = original.get("answer_audit", {}).get("proof_key")
            # Coverage metadata only. Even a newly added proof_key without a
            # recognized content-based evaluator cannot inherit verification.
            if row["published_proof_key"] and row["method"] is None:
                row["status"] = "unsupported"
                row["notes"].append("Proof-key row has no independently recognized arithmetic evaluator.")
            row["stored_key_comparison"] = {
                "stored_key": original.get("correct_answer"),
                "stored_valid_options": original.get("answer_audit", {}).get("valid_options", []),
                "performed_after_derivation": True,
                "agreement": None,
                "conventional_agreement":None,
                "stored_key_is_candidate":None,
            }
            if result["status"] in {"unique_match", "multiple_matches", "no_match"}:
                row["stored_key_comparison"]["agreement"] = (
                    set(result["candidates"]) == set(row["stored_key_comparison"]["stored_valid_options"]))
                row["stored_key_comparison"]["conventional_agreement"] = (
                    set(row["conventional_candidates"]) == set(row["stored_key_comparison"]["stored_valid_options"]))
                row["stored_key_comparison"]["stored_key_is_candidate"] = original.get("correct_answer") in row["candidates"]
            row["numerical_evidence"] = row["computed"] is not None and row["method"] not in {
                "group_propositions","rsa_propositions","des_schedule","totient_multiplicativity","congruence_propositions"}
            row["verification_basis"] = (
                "not_numerically_evaluated" if row["method"] is None else
                "symbolic_reasoning_with_numeric_witnesses" if row["method"] in {"group_propositions","rsa_propositions","des_schedule","totient_multiplicativity","congruence_propositions"} else
                "arithmetic_and_explicit_proposition_reasoning" if any("truth" in v for v in row["option_checks"].values()) else
                "independent_arithmetic")
            row["hint"] = format_hint(row)
            rows.append(row)
    counts = Counter(r["status"] for r in rows)
    full = sum(counts[s] for s in ("unique_match", "multiple_matches", "no_match"))
    proof_rows = [r for r in rows if r["published_proof_key"]]
    incomplete = [r for r in rows if r["status"] not in {"unique_match","multiple_matches","no_match","not_numerical"}]
    errors = [{"id":r["id"],"status":r["status"],"method":r["method"],"candidates":r["candidates"],
               "notes":r["notes"]} for r in rows if r["status"] not in {"unique_match","not_numerical"}]
    discrepancies = [{"id":r["id"],"candidates":r["candidates"],"conventional_candidates":r["conventional_candidates"],
                      **r["stored_key_comparison"]} for r in rows if r["stored_key_comparison"]["agreement"] is False]
    all_statuses = ("unique_match","multiple_matches","no_match","partial_proposition","ambiguous_source",
                    "insufficient_source","unsupported","pending","not_numerical")
    return {"schema_version": 1, "derivation": "question/options/tables and explicitly recorded image transcriptions only; no stored keys",
            "reference_algorithms":"verify_nmmmh_answers.py read for algorithms only; not imported or executed; no decision/proof output consumed",
            "complete": not incomplete, "all_rows_attempted": not counts["pending"],
            "candidate_policy":"Every matching A-D statement is exported; conventional_candidates separately prefers an explicit true aggregate option.",
            "source_files": files,"source_correction_files":correction_sources,
            "summary": {"total_rows": len(rows), "status_counts": {s:counts[s] for s in all_statuses},
                        "independently_calculated_rows": full,"numerical_evidence_rows":sum(r["numerical_evidence"] for r in rows),
                        "verified_count":counts["unique_match"],"verified_count_definition":"unique complete option match only",
                        "pending_count":len(incomplete),"unattempted_count":counts["pending"],
                        "published_proof_key_rows":len(proof_rows),
                        "proof_key_complete_rows":sum(r["candidate_set_complete"] for r in proof_rows),
                        "proof_key_with_computation":sum(r["computed"] is not None for r in proof_rows),
                        "supplemental_without_proof_key_rows":sum(r["method"] is not None and not r["published_proof_key"] for r in rows),
                        "stored_valid_set_discrepancies":len(discrepancies),
                        "conventional_unique_matches":sum(r["candidate_set_complete"] and len(r["conventional_candidates"]) == 1 for r in rows),
                        "conventional_multiple_matches":sum(r["candidate_set_complete"] and len(r["conventional_candidates"]) > 1 for r in rows),
                        "method_counts":dict(sorted(Counter(r["method"] for r in rows if r["method"]).items())),
                        "exam_counts":dict(sorted(Counter(r["source_exam_id"] for r in rows).items()))},
            "hint_templates": HINTS,"errors":errors,"incomplete_ids":[r["id"] for r in incomplete],
            "key_discrepancies":discrepancies,"rows": rows}


def self_test(root):
    """Differential arithmetic and complete-dataset independence checks."""
    for n in range(2,201):
        assert phi(n) == sum(math.gcd(i,n) == 1 for i in range(n))
    def shift_multiply(a,b):
        value = 0
        for _ in range(8):
            if b&1:value ^= a
            a = ((a<<1) ^ (0x11B if a&0x80 else 0)) & 255
            b >>= 1
        return value
    for a in range(256):
        for b in range(256):
            assert gf_mul(a,b) == shift_multiply(a,b)
    # Independent Jacobi evaluation: trial factorization plus Euler's criterion
    # for every odd denominator <= 99, including non-coprime inputs.
    for n in range(3,100,2):
        for a in range(n):
            remaining,p,expected = n,3,1
            while remaining > 1:
                if remaining % p:
                    p += 2
                    continue
                exponent = 0
                while remaining % p == 0:remaining//=p;exponent+=1
                symbol = pow(a%p,(p-1)//2,p)
                if symbol == p-1:symbol = -1
                expected *= symbol**exponent
            assert jacobi(a,n) == expected
    points = [(x,y) for x in range(11) for y in range(11) if (y*y-x*x*x-x-6)%11 == 0]
    for P in points:
        R = None
        for k in range(1,25):
            R = ec_add(R,P,11,1)
            assert ec_mul(k,P,11,1) == R
            assert R is None or R in points
    tested = 0
    for path in sorted((root/"subjects/nmmmh/exams").glob("*.json")):
        for original in json.loads(path.read_text()):
            q = solver_input(original)
            baseline = solve(q,root)
            poisoned = json.loads(json.dumps(original))
            poisoned.update(correct_answer="POISON",answer_audit={"correct_answer":"POISON","valid_options":["POISON"],
                            "proof_key":"POISON","status":"verified","explanation":"POISON"},
                            answer_evidence="POISON",source_text="POISON",source_notes=["POISON"])
            assert solve(solver_input(poisoned),root) == baseline,original["id"]
            shuffled = json.loads(json.dumps(q))
            mapping = dict(zip(LETTERS,reversed(LETTERS)))
            for c in LETTERS:shuffled[c] = q[mapping[c]]
            result = solve(shuffled,root)
            assert result["method"] == baseline["method"],original["id"]
            assert result["status"] == baseline["status"],original["id"]
            assert result["candidates"] == [c for c in LETTERS if mapping[c] in baseline["candidates"]],original["id"]
            tested += 1
    def fixture(values):
        return {"question":"Đáp án nào dưới đây là kết quả của φ(15)?","question_blocks":[],
                **{c:{"text":str(v),"blocks":[]} for c,v in zip(LETTERS,values)}}
    assert solve(fixture([8,8,2,1]),root)["candidates"] == ["A","B"]
    assert solve(fixture([7,6,2,1]),root)["status"] == "no_match"
    assert solve(fixture([7,6,8,1]),root)["candidates"] == ["C"]
    # Explicit source corrections alter only the local input view, not the bank.
    corrected = fixture([8,8,2,1])
    applied,conflicts = apply_corrections(corrected,[{"field":"A.text","old":"8","new":"7"}])
    assert applied and not conflicts and solve(corrected,root)["candidates"] == ["B"]
    print(f"Self-test passed: {tested} rows key-blind and A-D permutation invariant; 65536 GF pairs; phi/Jacobi/ECC cross-checks; multiple/no-match fixtures.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--source-corrections",type=Path,action="append",default=[],
                        help="Read explicit input patches (repeatable); never changes exam JSON. Accepts both source-review schemas or a simple list.")
    parser.add_argument("--self-test",action="store_true",help="Run differential arithmetic and full-bank key/permutation independence checks")
    parser.add_argument("--check",action="store_true",help="Check deterministic report freshness without writing")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.self_test:self_test(root)
    report = build_report(root,args.source_corrections)
    output = args.output or root / "subjects/nmmmh/audit/numeric_audit.json"
    if args.check:
        # Solver tuples (e.g. affine curve points) serialize as JSON arrays;
        # compare the serialized representation, not Python tuple/list types.
        expected = json.dumps(report,ensure_ascii=False,indent=2) + "\n"
        if not output.is_file() or output.read_text(encoding="utf-8") != expected:
            raise SystemExit("Audit is stale or missing; rerun without --check.")
        print("Audit is current and deterministic.")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
