"""Shared helpers for the Qortuba blind package: paths, loaders, the Arabic keyboard-map decoder, canonical states."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01.pa08.qortuba import blind as B

OUT, BLIND, DECODE, DWG, PDF = B.OUT, B.BLIND, B.DECODE, B.DWG, B.PDF
STATES = ("SOURCE_ESTABLISHED", "OWNER_PROJECT_INPUT", "OWNER_PARAMETRIC", "PROVISIONAL", "GEOMETRIC_REFERENCE_ONLY", "NOT_ESTABLISHED", "SOURCE_REQUIRED", "HUMAN_REVIEW", "NOT_APPLICABLE")

# Arabic 101 keyboard layout as typed through a Latin shape font: every key produces the Arabic letter of that key.
# Upper-case keys behave like their lower-case letter in this font family (H -> alef, B -> lam-alef, M -> teh marbuta).
_KB = {'q': 'ض', 'w': 'ص', 'e': 'ث', 'r': 'ق', 't': 'ف', 'y': 'غ', 'u': 'ع', 'i': 'ه', 'o': 'خ', 'p': 'ح', '[': 'ج', ']': 'د', 'a': 'ش', 's': 'س', 'd': 'ي', 'f': 'ب', 'g': 'ل', 'h': 'ا',
       'j': 'ت', 'k': 'ن', 'l': 'م', ';': 'ك', "'": 'ط', 'z': 'ئ', 'x': 'ء', 'c': 'ؤ', 'v': 'ر', 'b': 'لا', 'n': 'ى', 'm': 'ة', ',': 'و', '.': 'ز', '/': 'ظ', '`': 'ذ', '{': 'ج', '}': 'د'}
for _k in list(_KB):
    if _k.isalpha():
        _KB[_k.upper()] = _KB[_k]


def kb_decode(s):
    """Deterministic keyboard-map transliteration of a Latin-glyph Arabic string.  Returns (decoded, share_of_mapped_chars)."""
    out, mapped = [], 0
    for ch in s:
        if ch in _KB:
            out.append(_KB[ch]); mapped += 1
        else:
            out.append(ch)
    letters = sum(1 for ch in s if not ch.isspace())
    return "".join(out), (mapped / letters if letters else 0.0)


def looks_keyboard_arabic(s):
    """A Latin string with no vowel-shaped English word, containing keyboard-Arabic signatures (mixed case, ] [ , ' { patterns)."""
    t = s.strip()
    if not t or any('؀' <= c <= 'ۿ' for c in t):
        return False
    if t.upper() == t and t.replace(".", "").replace(" ", "").isalpha():
        return False           # plain upper-case English (HALL, BATH)
    return any(c in t for c in "[]{},';") or (sum(1 for c in t if c.islower()) > 0 and sum(1 for c in t if c.isupper()) > 0 and " " not in t) or t.islower()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_blind(name):
    p = BLIND / f"{name}.json"
    return json.loads(p.read_text("utf-8")) if p.exists() else None


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{name}.json"
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str), "utf-8")
    return str(p)


def decode():
    return json.loads(Path(DECODE).read_text("utf-8"))
