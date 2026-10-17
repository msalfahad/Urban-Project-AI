"""CAD TEXT CONTROL CODES (V1) - the AutoCAD %% codes as printed characters.

plain()   '%%c' -> diameter sign, '%%d' -> degree, '%%p' -> plus/minus, '%%%' -> '%'; '%%u' / '%%o' (underline /
          overline toggles) are removed. Case-insensitive. Returns the text and the codes found, so a caller can
          tell a typed number from one that carried a symbol. Nothing else is rewritten: no unit, no spacing fix.
legacy_codepage_suspect()
          a conservative flag for values written through a legacy single-byte font mapping (e.g. Arabic typed in
          an ANSI code page). The caller records such a value as UNDECODED; it is never translated by guess.

Clean reimplementation of the idea of a CAD label normaliser (UC4N labels.plain, MIT) - nothing copied. Stdlib only.
"""

from __future__ import annotations

import re

POLICY_ID = "CAD_TEXT_CONTROL_V1"
DIAMETER, DEGREE, PLUS_MINUS = "Ø", "°", "±"
_CODE = re.compile(r"%%(%|[cdpuoCDPUO])")
_MAP = {"c": DIAMETER, "d": DEGREE, "p": PLUS_MINUS, "%": "%", "u": "", "o": ""}


def plain(text):
    """(printed text, tuple of codes found in order)."""
    if text is None:
        return None, ()
    codes = []

    def sub(m):
        k = m.group(1).lower()
        codes.append("%%" + k)
        return _MAP[k]
    return _CODE.sub(sub, text), tuple(codes)


_LATIN_WORD = re.compile(r"[A-Za-z]{2,}")
_ODD = set("]['`{}|\\,;~^")


def legacy_codepage_suspect(text) -> bool:
    """A conservative flag only: printable non-ASCII bytes, or ASCII text mixing many glyph-mapping punctuation marks
    inside letter runs (e.g. 'Hg]v,M'). Plain English words and numbers are never flagged."""
    if not text:
        return False
    if any(ord(ch) > 126 for ch in text):
        return True
    words = text.split()
    odd = sum(1 for ch in text if ch in _ODD)
    return odd >= 1 and any(any(c in _ODD for c in w) and any(c.isalpha() for c in w) for w in words)


def policy_record() -> dict:
    return {"policy_id": POLICY_ID, "codes": {"%%" + k: v for k, v in sorted(_MAP.items())},
            "never": ["translating a legacy-codepage value by guess", "changing spacing or units"]}
