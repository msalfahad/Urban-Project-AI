"""SHX ARABIC TEXT INTAKE - Arabic notes and labels drawn with legacy SHX fonts (TEXT, MTEXT, ATTRIB).

Why: Arabic drawn with a legacy SHX font is stored as Latin keyboard codes (a level note reads 'lks,f' where the sheet
shows منسوب), so every string search, room vocabulary and note reader misses it. This module decodes such text from
the font named by its text style (or an MTEXT \\F font switch). It is NOT wired into any method; no quantity changes.

Rules
  UP-KB-PREC-001     the printed drawing is the source: a letter comes from a reviewed font table, never a guess.
  UP-QTY-STATUS-001  every text is reported once: DECODED, untouched (Latin / Unicode font) or HELD with a reason.
                     Undecoded text is reported, never dropped.

Font table (FONT_TABLE, reviewed; every entry carries its source)
  ARABIC_SHX   X-ARAB* / XARAB* (glyph family) and XARB* / ARABIC101* (Arabic 101 keyboard family): the tables of the
               frozen engine/source/legacy_text.py (LEGACY_CAD_TEXT_DECODE_V1), read here, never edited.
  LATIN_SHX    the 22 Latin SHX fonts shipped with AutoCAD (Autodesk Docs "Supported DWF, DWG and RVT Fonts"): text
               is left untouched.
  UNICODE      .ttf / .otf / .ttc files and MTEXT \\f (TrueType) switches: the DXF stores Unicode; left untouched.
  anything else (or a style that does not exist) is UNKNOWN: text with Latin codes in it is HELD
  UNDECODED_SHX_CANDIDATE (the font may be a keyboard Arabic font nobody reviewed); never decoded by assumption.

Decoding (keyboard family)
  key -> letter by legacy_text.KEYBOARD_101 (upper case = the same letter, alternate glyph); digit keys 0-9 stay the
  digits (Windows Arabic 101 layout KBDA1, unshifted digit row); Arabic Unicode already in the string passes through.
  '.' and ',' between two digits are HELD (decimal point / thousands mark, or the letters ز / و: the SHX glyph is not
  established by any reviewed source). A code outside the map is HELD with its index. Glyph family: legacy_text.XARAB.
  The DXF string is in reading order (first letter first), so the decoded string is logical-order Unicode; a backward,
  upside-down, rotated or block-mirrored text decodes the same (its flags are recorded, not applied to the letters).

API
  font_class(font, truetype=False) -> {"kind", "family", "source"}
  decode_text(raw, font, *, entity="TEXT") -> record (status, release, text, runs, issues)
  records_from_doc(doc) -> one record per TEXT / MTEXT / ATTRIB in model space, paper space and (recursively) block
  references, with layout, handle path, world insert point, OCS rotation, mirrored flags and $INSUNITS.

stdlib only (records_from_doc takes an ezdxf document but does not import ezdxf).
"""

from __future__ import annotations

import math
import re

from engine.source import legacy_text as _lt

POLICY_ID = "SHX_ARABIC_INTAKE_V1"

# statuses
DECODED = "DECODED"
PARTIAL = "PARTIAL_DECODE"
UNDECODED = "UNDECODED_SHX_CANDIDATE"
UNKNOWN_NO_CODES = "UNKNOWN_FONT_NO_LETTER_CODES"
LATIN = "LATIN_FONT_UNTOUCHED"
UNICODE = "UNICODE_FONT_UNTOUCHED"
EMPTY = "EMPTY_TEXT"
RELEASED, HELD, NOT_APPLICABLE = "RELEASED", "HELD", "NOT_APPLICABLE"
_RELEASE = {DECODED: RELEASED, PARTIAL: HELD, UNDECODED: HELD, UNKNOWN_NO_CODES: HELD,
            LATIN: NOT_APPLICABLE, UNICODE: NOT_APPLICABLE, EMPTY: NOT_APPLICABLE}

ARABIC_SHX, LATIN_SHX, UNICODE_FONT, UNKNOWN = "ARABIC_SHX", "LATIN_SHX", "UNICODE", "UNKNOWN"

_SRC_LEGACY = "engine/source/legacy_text.py LEGACY_CAD_TEXT_DECODE_V1 (FONT_FAMILIES; tables with per-glyph evidence)"
_SRC_AUTODESK = ("Autodesk Docs, 'Supported DWF, DWG and RVT Fonts' (help.autodesk.com/view/DOCS/ENU/"
                 "?guid=Supported_Fonts_Docs): AutoCAD SHX fonts")
_SRC_TTF = "DXF reference: a style whose font file is TrueType / OpenType stores text as Unicode"
_SRC_KBDA1 = "Windows Arabic (101) keyboard layout KBDA1: unshifted digit row types the digits 0-9"

LATIN_SHX_FONTS = ("TXT", "MONOTXT", "SIMPLEX", "COMPLEX", "ITALIC", "ITALICC", "ITALICT", "ROMANC", "ROMAND",
                   "ROMANS", "ROMANT", "SCRIPTC", "SCRIPTS", "GOTHICE", "GOTHICG", "GOTHICI", "ISOCP", "ISOCP2",
                   "ISOCP3", "ISOCT", "ISOCT2", "ISOCT3")

FONT_TABLE = tuple(
    [{"match": "prefix", "name": p, "kind": ARABIC_SHX, "family": fam, "source": _SRC_LEGACY}
     for p, fam in _lt.FONT_FAMILIES]
    + [{"match": "exact", "name": n, "kind": LATIN_SHX, "family": None, "source": _SRC_AUTODESK}
       for n in LATIN_SHX_FONTS]
    + [{"match": "extension", "name": e, "kind": UNICODE_FONT, "family": None, "source": _SRC_TTF}
       for e in (".TTF", ".OTF", ".TTC")])

_ARABIC_UNICODE = re.compile("[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
_TTF_RE = re.compile(r"\.(TTF|OTF|TTC)$")


def _base(font) -> str:
    return (font or "").strip().replace("\\", "/").rsplit("/", 1)[-1].upper()


def font_class(font, truetype=False) -> dict:
    """Classify a font file name (style font or MTEXT \\F) or, with truetype=True, an MTEXT \\f family name."""
    if truetype:
        return {"kind": UNICODE_FONT, "family": None, "source": "MTEXT \\f switch selects a TrueType family; " + _SRC_TTF}
    b = _base(font)
    if not b:
        return {"kind": UNKNOWN, "family": None, "source": "no font file"}
    if _TTF_RE.search(b):
        return {"kind": UNICODE_FONT, "family": None, "source": _SRC_TTF}
    fam = _lt.font_family(b)
    if fam:
        return {"kind": ARABIC_SHX, "family": fam, "source": _SRC_LEGACY}
    stem = b[:-4] if b.endswith(".SHX") else b
    if stem in LATIN_SHX_FONTS:
        return {"kind": LATIN_SHX, "family": None, "source": _SRC_AUTODESK}
    return {"kind": UNKNOWN, "family": None, "source": "not in the reviewed font table"}


# ---------------------------------------------------------------- raw text -> runs

_CONTROL = {"D": "\u00b0", "P": "\u00b1", "C": "\u2300"}


def _text_controls(s: str) -> str:
    """AutoCAD TEXT control codes: %%d %%p %%c symbols, %%nnn character code, %%u / %%o toggles dropped, %%% -> %."""
    s = re.sub(r"\\U\+([0-9A-Fa-f]{4})", lambda m: chr(int(m.group(1), 16)), s)

    def rep(m):
        t = m.group(1)
        if t.isdigit():
            return chr(int(t))
        if t.upper() in _CONTROL:
            return _CONTROL[t.upper()]
        if t.upper() in ("U", "O"):
            return ""
        return "%"
    return re.sub(r"%%(\d{3}|[dDpPcCuUoO%])", rep, s)


def _mtext_runs(raw: str, font: str | None):
    """MTEXT content -> [(font, truetype, text)], following \\F / \\f switches and { } groups."""
    runs, buf = [], []
    cur = (font, False)
    stack = []

    def flush():
        if buf:
            runs.append((cur[0], cur[1], "".join(buf)))
            buf.clear()
    i, n = 0, len(raw)
    while i < n:
        ch = raw[i]
        if ch == "\\" and i + 1 < n:
            c = raw[i + 1]
            if c in "\\{}":
                buf.append(c)
                i += 2
            elif c in "PN":
                buf.append("\n")
                i += 2
            elif c == "~":
                buf.append(" ")
                i += 2
            elif c in "LlOoKk":
                i += 2
            elif c == "U" and raw[i + 2:i + 3] == "+" and re.match(r"[0-9A-Fa-f]{4}", raw[i + 3:i + 7]):
                buf.append(chr(int(raw[i + 3:i + 7], 16)))
                i += 7
            elif c in "FfHWQTACcpS":
                j = raw.find(";", i + 2)
                j = n if j < 0 else j
                arg = raw[i + 2:j]
                if c in "Ff":
                    flush()
                    cur = (arg.split("|", 1)[0], c == "f")
                elif c == "S":
                    buf.append(re.sub(r"[\^#]", "/", arg))
                i = j + 1
            else:
                buf.append(ch)
                i += 1
        elif ch == "{":
            flush()
            stack.append(cur)
            i += 1
        elif ch == "}":
            flush()
            if stack:
                cur = stack.pop()
            i += 1
        else:
            buf.append(ch)
            i += 1
    flush()
    return runs


# ---------------------------------------------------------------- decoding

def _decode_run(s: str, family: str, offset: int):
    out, issues = [], []
    for k, ch in enumerate(s):
        idx = offset + k
        if _ARABIC_UNICODE.match(ch) or ch in " \n" or ch in _CONTROL.values():
            out.append(ch)
            continue
        if family == _lt.ARABIC_KEYBOARD_101:
            if ch.isascii() and ch.isdigit():
                out.append(ch)
                continue
            if ch in ".," and 0 < k < len(s) - 1 and s[k - 1].isdigit() and s[k + 1].isdigit():
                out.append("?")
                issues.append({"index": idx, "code": ch, "reason": "DIGIT_SEPARATOR_OR_LETTER_NOT_ESTABLISHED"})
                continue
            key = ch.lower() if ch.isascii() and ch.isalpha() else ch
            if key in _lt.KEYBOARD_101:
                out.append(_lt.KEYBOARD_101[key])
                continue
        elif ch in _lt.XARAB:
            out.append(_lt.XARAB[ch][0])
            continue
        out.append("?")
        issues.append({"index": idx, "code": ch, "reason": "CODE_NOT_IN_REVIEWED_MAP"})
    return "".join(out), issues


def _has_latin_codes(s: str) -> bool:
    return any(ch.isascii() and (ch.isalpha() or ch in "[];',./`{}_<>") for ch in s)


def decode_text(raw, font, *, entity="TEXT") -> dict:
    """Decode one TEXT / ATTRIB (control codes) or MTEXT (format codes) string drawn with style font `font`."""
    raw = raw or ""
    if entity == "MTEXT":
        runs = [(f, tt, _text_controls(t)) for f, tt, t in _mtext_runs(raw, font)]
    else:
        runs = [(font, False, _text_controls(raw))]
    out_runs, issues, kinds, unknown_codes = [], [], set(), False
    offset = 0
    for f, tt, t in runs:
        fc = font_class(f, truetype=tt)
        kinds.add(fc["kind"])
        if fc["kind"] == ARABIC_SHX:
            dec, iss = _decode_run(t, fc["family"], offset)
            issues += iss
        else:
            dec = t
            if fc["kind"] == UNKNOWN and _has_latin_codes(t):
                unknown_codes = True
        out_runs.append({"font": f, "truetype": tt, "kind": fc["kind"], "family": fc["family"],
                         "source": fc["source"], "raw": t, "text": dec})
        offset += len(t)
    text = "".join(r["text"] for r in out_runs)
    if not text.strip():
        status = EMPTY
    elif UNKNOWN in kinds:
        status = UNDECODED if unknown_codes else UNKNOWN_NO_CODES
    elif issues:
        status = PARTIAL
    elif ARABIC_SHX in kinds:
        status = DECODED
    elif LATIN_SHX in kinds:
        status = LATIN
    else:
        status = UNICODE
    if status in (UNDECODED, UNKNOWN_NO_CODES):
        # an unknown font is never decoded: the text stays exactly as stored
        text = "".join(r["raw"] if r["kind"] == UNKNOWN else r["text"] for r in out_runs)
    return {"policy": POLICY_ID, "entity": entity, "font": font, "raw": raw, "text": text, "status": status,
            "release": _RELEASE[status], "runs": out_runs, "issues": issues}


# ---------------------------------------------------------------- DXF intake

def _style_font(doc, name):
    try:
        st = doc.styles.get(name)
    except Exception:  # noqa: BLE001 - ezdxf raises DXFTableEntryError for a missing style
        st = None
    if st is None:
        return None, "STYLE_NOT_FOUND"
    return (st.dxf.get("font", "") or None), None


def _ocs_to_wcs(p, ez):
    """DXF arbitrary axis algorithm: an OCS point of a planar entity with extrusion `ez` -> world (x, y)."""
    nz = math.sqrt(sum(c * c for c in ez)) or 1.0
    az = tuple(c / nz for c in ez)
    if abs(az[0]) < 1.0 / 64.0 and abs(az[1]) < 1.0 / 64.0:
        ax = (az[2], 0.0, -az[0])            # (0, 1, 0) x Az
    else:
        ax = (-az[1], az[0], 0.0)            # (0, 0, 1) x Az
    n = math.sqrt(sum(c * c for c in ax))
    ax = tuple(c / n for c in ax)
    ay = (az[1] * ax[2] - az[2] * ax[1], az[2] * ax[0] - az[0] * ax[2], az[0] * ax[1] - az[1] * ax[0])
    z = p[2] if len(p) > 2 else 0.0
    return tuple(p[0] * ax[i] + p[1] * ay[i] + z * az[i] for i in range(2))


def _is_mirrored_insert(ins) -> bool:
    sx, sy, sz = (ins.dxf.get("xscale", 1.0), ins.dxf.get("yscale", 1.0), ins.dxf.get("zscale", 1.0))
    neg = (sx < 0) ^ (sy < 0) ^ (sz < 0)
    ez = ins.dxf.get("extrusion", (0, 0, 1))
    return bool(neg ^ (ez[2] < 0))


def _record(doc, e, layout, path, mirrored, units):
    t = e.dxftype()
    style = e.dxf.get("style", "Standard")
    font, problem = _style_font(doc, style)
    raw = e.text if t == "MTEXT" else e.dxf.get("text", "")
    rec = decode_text(raw, font, entity="MTEXT" if t == "MTEXT" else "TEXT")
    ez = tuple(e.dxf.get("extrusion", (0, 0, 1)))
    p = e.dxf.get("insert", (0.0, 0.0, 0.0))
    if t != "MTEXT":                         # TEXT / ATTRIB insert is an OCS point; MTEXT insert is WCS
        p = _ocs_to_wcs(tuple(p), ez)
    flag = e.dxf.get("text_generation_flag", 0) if t != "MTEXT" else 0
    rec.update({"dxftype": t, "layout": layout, "handle_path": path, "layer": e.dxf.get("layer", "0"),
                "style": style, "style_problem": problem, "insert": (round(p[0], 6), round(p[1], 6)),
                "rotation_deg_ocs": round(e.dxf.get("rotation", 0.0) % 360.0, 6), "backward": bool(flag & 2),
                "upside_down": bool(flag & 4), "mirrored_by_block": mirrored, "extrusion_negative": ez[2] < 0,
                "insunits": units})
    return rec


def _walk(doc, entities, layout, prefix, mirrored, units, out, depth):
    for k, e in enumerate(entities):
        h = e.dxf.get("handle") or f"v{k}"
        path = f"{prefix}/{h}" if prefix else h
        t = e.dxftype()
        if t in ("TEXT", "MTEXT", "ATTRIB"):
            out.append(_record(doc, e, layout, path, mirrored, units))
        elif t == "INSERT":
            m = mirrored ^ _is_mirrored_insert(e)
            for a in getattr(e, "attribs", ()):
                out.append(_record(doc, a, layout, f"{path}/{a.dxf.get('handle') or 'attrib'}", m, units))
            if depth >= 16:
                out.append({"policy": POLICY_ID, "status": "BLOCK_DEPTH_LIMIT", "release": HELD,
                            "handle_path": path, "layout": layout})
                continue
            try:
                virt = list(e.virtual_entities())
            except Exception as exc:  # noqa: BLE001 - a block that cannot be exploded is reported, not dropped
                out.append({"policy": POLICY_ID, "status": "BLOCK_NOT_EXPLODED", "release": HELD,
                            "handle_path": path, "layout": layout, "error": type(exc).__name__})
                continue
            _walk(doc, virt, layout, f"{path}:{e.dxf.get('name', '')}", m, units, out, depth + 1)


def records_from_doc(doc) -> list:
    """Every TEXT / MTEXT / ATTRIB of every layout (blocks expanded to world position), decoded or HELD."""
    units = doc.header.get("$INSUNITS", 0)
    out = []
    for layout in doc.layouts:
        _walk(doc, list(layout), layout.name, "", False, units, out, 0)
    return out


def census(records) -> dict:
    """Counts by status and the HELD records (never silently absent)."""
    by = {}
    for r in records:
        by[r["status"]] = by.get(r["status"], 0) + 1
    return {"policy": POLICY_ID, "total": len(records), "by_status": dict(sorted(by.items())),
            "held": [r for r in records if r.get("release") == HELD]}


def policy_record() -> dict:
    return {"id": POLICY_ID, "font_table": [dict(r) for r in FONT_TABLE], "digit_source": _SRC_KBDA1,
            "rule": "decode only fonts in the reviewed table; unknown fonts with Latin codes and unmapped codes are "
                    "HELD with their index, never guessed; not wired into any method"}

