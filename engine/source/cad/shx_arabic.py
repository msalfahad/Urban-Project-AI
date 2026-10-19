"""SHX ARABIC TEXT INTAKE (T-047) - decode TEXT / MTEXT / ATTRIB drawn in legacy Arabic SHX fonts.

Legacy Arabic AutoCAD fonts store no Unicode: the DXF holds Latin code points and the SHX font draws an Arabic glyph
for each, so the note a QS reads as "من منسوب" is stored as "lK lks,F". Every string search, room vocabulary and note
reader then misses it. This module turns such a text into Arabic Unicode (logical order: first letter first, the order
the keys were typed and the order the frozen decoder already reads; joining and right-to-left shaping are a display
matter and are not applied to the stored string), or reports why it cannot.

Inputs are plain records, so the module stays stdlib-only (engine/source rule, tests/r8_1): the caller reads the DXF
(ezdxf, lab adapter) and passes
    styles  {STYLE NAME: {"font": font file, "bigfont": big font file}}   (the STYLE table)
    text    {"handle", "type": TEXT | MTEXT | ATTRIB | ATTDEF, "value": raw string, "style": style name, ...}
Geometry fields (insert, rotation, height, mirror flags, units) are carried through untouched: decoding depends only on
the code points and the font, never on where or how the text is placed (a mirrored or rotated text, or a mm / m
drawing, decodes the same).

Font decision (FONT_TABLE, a reviewed table; every entry names its source):
    ARABIC_LEGACY  the font has a reviewed map -> decode with it
    LATIN          a standard Latin SHX font -> text untouched (status UNCHANGED)
    UNICODE        a TrueType / OpenType font -> the string already is Unicode -> untouched (UNCHANGED)
    UNKNOWN        any other font file. A text on it that holds Latin letters is reported UNDECODED_SHX_CANDIDATE
                   (HELD): it may be Arabic that no reviewed map covers. Never silently treated as Latin or dropped.
MTEXT inline font switches (\\F / \\f) are honoured run by run, so a mixed MTEXT decodes only its Arabic runs.

Maps: the two families of the frozen decoder `engine/source/legacy_text.py` (LEGACY_CAD_TEXT_DECODE_V1; read, never
edited) plus, for the keyboard family only, the digit row of the Arabic (101) keyboard (digit keys type digits and
"-" types "-": Microsoft, Arabic (101) keyboard, https://learn.microsoft.com/globalization/keyboards/kbda1).
A code point outside the map stays undecoded and is reported with its index ("?" in the text), never guessed. A "."
or "," between two digits is reported AMBIGUOUS_DIGIT_SEPARATOR: on the keyboard map it is the letter ز / و, but a
decimal point is as likely, and the drawing alone does not say which.

Status (UP-QTY-STATUS-001: every text reported once; UP-KB-PREC-001: the printed drawing is the source):
    DECODED                 every code point mapped (status RELEASED)
    PARTIAL_DECODE          some code points undecoded (HELD, the undecoded ones listed)
    UNDECODED_SHX_CANDIDATE unknown font with Latin-code text (HELD)
    UNCHANGED               Latin or Unicode font, or no Latin letters on an unknown font (text returned as stored)
Not wired into any method: no quantity reads it yet.
"""

from __future__ import annotations

import re

from .. import legacy_text as LT

POLICY_ID = "SHX_ARABIC_INTAKE_V1"
ARABIC_LEGACY, LATIN, UNICODE, UNKNOWN = "ARABIC_LEGACY", "LATIN", "UNICODE", "UNKNOWN"
DECODED, PARTIAL, CANDIDATE, UNCHANGED = "DECODED", "PARTIAL_DECODE", "UNDECODED_SHX_CANDIDATE", "UNCHANGED"
RELEASED, HELD = "RELEASED", "HELD"
NOT_IN_MAP, AMBIGUOUS_SEP, UNSUPPORTED_CODE = "NOT_IN_MAP", "AMBIGUOUS_DIGIT_SEPARATOR", "UNSUPPORTED_MTEXT_CODE"

SRC_LEGACY = "engine/source/legacy_text.py LEGACY_CAD_TEXT_DECODE_V1 FONT_FAMILIES (frozen; glyph evidence per entry)"
SRC_KBDA1 = "Microsoft Arabic (101) keyboard, https://learn.microsoft.com/globalization/keyboards/kbda1"
SRC_ACAD = "AutoCAD standard SHX fonts shipped in the product Fonts folder (Autodesk AutoCAD help, 'SHX fonts')"

# (font file stem without .SHX, match "exact" | "prefix", class, family, source). First match wins; order matters.
FONT_TABLE = (
    ("X-ARAB", "prefix", ARABIC_LEGACY, LT.XARAB_GLYPH, SRC_LEGACY + " (X-ARAB / X-ARAB1B / X-ARABIC1)"),
    ("XARAB", "prefix", ARABIC_LEGACY, LT.XARAB_GLYPH, SRC_LEGACY),
    ("XARB", "prefix", ARABIC_LEGACY, LT.ARABIC_KEYBOARD_101, SRC_LEGACY + "; digit row: " + SRC_KBDA1),
    ("ARABIC101", "prefix", ARABIC_LEGACY, LT.ARABIC_KEYBOARD_101, SRC_LEGACY + "; digit row: " + SRC_KBDA1),
) + tuple((stem, "exact", LATIN, None, SRC_ACAD) for stem in (
    "TXT", "MONOTXT", "SIMPLEX", "COMPLEX", "ITALIC", "ROMANS", "ROMAND", "ROMANC", "ROMANT", "SCRIPTS", "SCRIPTC",
    "ITALICC", "ITALICT", "GOTHICE", "GOTHICG", "GOTHICI", "ISOCP", "ISOCP2", "ISOCP3", "ISOCT", "ISOCT2", "ISOCT3",
    "ISOCPEUR", "ISOCTEUR"))
UNICODE_EXT = (".TTF", ".TTC", ".OTF")

# digit row of the Arabic (101) keyboard (SRC_KBDA1): unshifted digit keys and "-" type themselves
KEYBOARD_DIGITS = {c: c for c in "0123456789-"}
SPECIAL = {"%%D": "°", "%%P": "±", "%%C": "⌀", "%%%": "%"}  # AutoCAD control codes, resolved before the font


def _stem(font_file) -> str:
    f = (font_file or "").replace("\\", "/").rsplit("/", 1)[-1].strip().upper()
    return f[:-4] if f.endswith(".SHX") else f


def classify_font(font_file) -> dict:
    """{"font", "class", "family", "source"} for a text style's font file."""
    raw = (font_file or "").strip()
    stem = _stem(raw)
    if stem.endswith(UNICODE_EXT):
        return {"font": raw, "class": UNICODE, "family": None, "source": "TrueType / OpenType fonts are Unicode"}
    key = re.sub(r"[^A-Z0-9-]", "", stem)
    for pat, how, cls, fam, src in FONT_TABLE:
        if (how == "exact" and key == pat) or (how == "prefix" and key.startswith(pat)):
            return {"font": raw, "class": cls, "family": fam, "source": src}
    return {"font": raw, "class": UNKNOWN, "family": None, "source": None}


def _map_char(ch, family):
    if family == LT.ARABIC_KEYBOARD_101:
        if ch in KEYBOARD_DIGITS:
            return KEYBOARD_DIGITS[ch]
        k = ch.lower() if ch.isascii() and ch.isalpha() else ch
        return LT.KEYBOARD_101.get(k)
    if family == LT.XARAB_GLYPH:
        hit = LT.XARAB.get(ch)
        return hit[0] if hit else None
    return None


def decode_run(value, family, offset=0) -> tuple:
    """(text, undecoded [{"index", "char", "reason"}]) for one run in one legacy family."""
    out, bad = [], []
    s = value or ""
    for i, ch in enumerate(s):
        if family == LT.ARABIC_KEYBOARD_101 and ch in ".," and 0 < i < len(s) - 1 \
                and s[i - 1].isdigit() and s[i + 1].isdigit():
            bad.append({"index": offset + i, "char": ch, "reason": AMBIGUOUS_SEP})
            out.append("?")
            continue
        m = _map_char(ch, family)
        if m is None:
            bad.append({"index": offset + i, "char": ch, "reason": NOT_IN_MAP})
            out.append("?")
        else:
            out.append(m)
    return "".join(out), bad


def _specials(s):
    return re.sub(r"%%[dDpPcC%]", lambda m: SPECIAL[m.group(0).upper()], s or "")


def mtext_runs(value, font_file) -> tuple:
    """Split an MTEXT string into [(plain text, font file)] runs and a list of unsupported codes.

    Handles \\P (new line), \\~ (space), \\\\ \\{ \\} (escapes), { } groups (font scope), \\F / \\f font switches,
    \\U+XXXX, and drops formatting-only codes (\\H \\W \\Q \\T \\A \\C \\c \\p ... up to ';', \\L \\l \\O \\o \\K \\k).
    \\S (stacked text) is kept as "a/b". Anything else is reported, never silently dropped."""
    runs, unsupported = [], []
    stack, font, buf = [], font_file, []
    s, i, n = value or "", 0, len(value or "")

    def flush():
        if buf:
            runs.append(("".join(buf), font))
            buf.clear()

    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n:
            d = s[i + 1]
            if d in "\\{}":
                buf.append(d); i += 2; continue
            if d == "P":
                buf.append("\n"); i += 2; continue
            if d == "~":
                buf.append(" "); i += 2; continue
            if d in "LlOoKk":
                i += 2; continue
            if d == "U" and s[i + 2:i + 3] == "+" and re.fullmatch(r"[0-9A-Fa-f]{4}", s[i + 3:i + 7] or ""):
                flush()
                runs.append((chr(int(s[i + 3:i + 7], 16)), None))  # an explicit Unicode code point: no font map
                i += 7; continue
            j = s.find(";", i)
            if d in "Ff" and j > 0:
                flush()
                font = s[i + 2:j].split("|", 1)[0]
                if d == "f" and not font.upper().endswith(UNICODE_EXT):
                    font = font + ".ttf"  # \f names a TrueType family (AutoCAD MTEXT codes)
                i = j + 1; continue
            if d == "S" and j > 0:
                buf.append(re.sub(r"[\^#]", "/", s[i + 2:j])); i = j + 1; continue
            if d in "HWQTACcpX" and j > 0:
                i = j + 1; continue
            unsupported.append({"index": i, "code": "\\" + d, "reason": UNSUPPORTED_CODE})
            i += 2; continue
        if c == "{":
            flush(); stack.append(font); i += 1; continue
        if c == "}":
            flush(); font = stack.pop() if stack else font; i += 1; continue
        buf.append(c); i += 1
    flush()
    return runs, unsupported


def decode_text(text, styles) -> dict:
    """One output record per input text: the input fields, plus decoded text, status and evidence."""
    st = (styles or {}).get((text.get("style") or "").upper()) or {}
    style_font = st.get("font", "")
    raw = text.get("value") or ""
    if (text.get("type") or "TEXT").upper() == "MTEXT":
        runs, unsupported = mtext_runs(raw, style_font)
    else:
        runs, unsupported = [(raw, style_font)], []
    parts, undecoded, families, candidates, fonts = [], [], set(), [], []
    pos = 0
    for value, font in runs:
        value = _specials(value)
        if font is None:  # explicit \U+ code point
            parts.append(value); pos += len(value); continue
        fc = classify_font(font)
        fonts.append({k: fc[k] for k in ("font", "class", "family", "source")})
        if fc["class"] == ARABIC_LEGACY:
            families.add(fc["family"])
            segs, out = re.split(r"(\n)", value), []
            for seg in segs:
                if seg == "\n":
                    out.append("\n"); pos += 1; continue
                t, bad = decode_run(seg, fc["family"], pos)
                out.append(t); undecoded += bad; pos += len(seg)
            parts.append("".join(out))
            continue
        if fc["class"] == UNKNOWN and re.search(r"[A-Za-z]", value):
            candidates.append({"font": fc["font"], "run": value})
        parts.append(value); pos += len(value)
    decoded = "\n".join(re.sub(r" {2,}", " ", ln).strip() for ln in "".join(parts).split("\n"))
    if candidates:
        state, status = CANDIDATE, HELD
    elif families and (undecoded or unsupported):
        state, status = PARTIAL, HELD
    elif families:
        state, status = DECODED, RELEASED
    else:
        state, status = UNCHANGED, (HELD if unsupported else RELEASED)
    rec = dict(text)
    if not families:  # Latin / Unicode / unknown font: the stored text is kept as is (MTEXT: codes removed only)
        decoded = "".join(parts) if (text.get("type") or "TEXT").upper() == "MTEXT" else raw
    rec.update({"policy": POLICY_ID, "raw": raw, "decoded": decoded,
                "state": state, "status": status, "families": sorted(families), "fonts": fonts,
                "undecoded": undecoded, "unsupported_codes": unsupported, "candidates": candidates,
                "order": "LOGICAL", "rules": ["UP-KB-PREC-001", "UP-QTY-STATUS-001"]})
    return rec


def decode_all(texts, styles) -> dict:
    """Every text in, one record out (none dropped), plus a census by state."""
    recs = [decode_text(t, styles) for t in texts or ()]
    census = {}
    for r in recs:
        census[r["state"]] = census.get(r["state"], 0) + 1
    return {"policy": POLICY_ID, "records": recs, "census": dict(sorted(census.items())),
            "held": [r.get("handle") for r in recs if r["status"] == HELD]}


def policy_record() -> dict:
    return {"id": POLICY_ID,
            "font_table": [{"stem": p, "match": h, "class": c, "family": f, "source": s} for p, h, c, f, s in FONT_TABLE],
            "keyboard_digits": dict(sorted(KEYBOARD_DIGITS.items())), "digit_source": SRC_KBDA1,
            "decoder": LT.POLICY_ID,
            "rule": "unknown font with Latin-code text -> UNDECODED_SHX_CANDIDATE (HELD); a code point outside the map "
                    "stays undecoded and is listed; decoding never depends on placement, rotation, mirror or units"}
