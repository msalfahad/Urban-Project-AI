"""T-608 DRAWING READ (research, unwired): the lift landing openings of the architectural DXF (Drive "Alsenan chalet
project" / P7757_DXF_COMPRESSED.zip, decoded into .work/private only), re-read from the gaps the merged T-601 census
found with PANEL_LINES evidence (T601_DRAWN.json, pinned), plus a whole-drawing text census for any printed note that
would name the lift package, a landing-door height or a door schedule. Writes T608_DRAWN.json (handles and figures
only: no coordinate, no drawing text, no client name). The builder t608_alsenan.py reads only that JSON.

    .work/venv/bin/python -I research/agents_t608/t608_extract.py --dxf <P7757.dxf> --st <ST7757 dxf.dxf> --write
    .work/venv/bin/python -I research/agents_t608/t608_extract.py --dxf <P7757.dxf> --st <ST7757 dxf.dxf>   (compare)

Per lift gap (generic method):
  * the two wall face lines of the band (layer 1, the jamb face handles of T-601) give the two face offsets across the
    band; every panel line (T-601 ids) gets its offset from the face on the SHAFT side, in mm;
  * the shaft side = the side holding a non-wall diagonal LINE (layer 5) longer than 1.0 m within 2.5 m of the gap: the
    drawn shaft cross (car / shaft symbol). No diagonal -> side NOT ESTABLISHED (the kind then stays FRAMED, not LIFT);
  * text census (architectural DXF, and the structural DXF with --st): every TEXT / MTEXT / ATTRIB in model space and
    in non-anonymous blocks, raw and with its key-mapped Arabic decoded, is tested against three patterns (lift /
    elevator words in English and Arabic; a door / opening height notation; a supply, manufacturer or schedule note);
    only counts and handles are written.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "T608_DRAWN.json"
T601 = ROOT / "research" / "agents_t601" / "T601_DRAWN.json"
MM = 0.001
WALL, MARK = "1", "5"
PATTERNS = {
    "lift_words": re.compile(r"\b(lift|elevator|elev\.?|ELV)\b|مصعد|اسانسير|أسانسير", re.I),
    "height_notation": re.compile(r"\b(h|ht|height)\s*[=:]\s*\d|\b\d{3,4}\s*[xX\*]\s*\d{3,4}\b|ارتفاع", re.I),
    "supply_or_schedule": re.compile(r"suppl|manufactur|schedule|by others|vendor|جدول|المورد|الشركة|المصنع", re.I),
}
# Arabic typed through the Latin key positions of the Arabic (101) keyboard, as this drawing set stores its Arabic notes
# (SHX fonts): each key letter is mapped back before matching, and drawing punctuation inside words ('{', '}', '<', '>')
# is dropped. A raw-text match and a decoded match are both counted.
_KEYS = "qwertyuiop[]asdfghjkl;'zxcvnm,./`"
_VALS = ["ض", "ص", "ث", "ق", "ف", "غ", "ع", "ه", "خ", "ح", "ج", "د", "ش", "س", "ي", "ب", "ل", "ا", "ت", "ن", "م", "ك",
         "ط", "ئ", "ء", "ؤ", "ر", "ى", "ة", "و", "ز", "ظ", "ذ"]
KEYMAP = dict(zip(_KEYS, _VALS))
KEYMAP.update({"b": "لا", "H": "أ", "B": "لإ", "Y": "إ", "N": "آ", "G": "لأ", "T": "لإ"})


def decode_keyed(s):
    return "".join(KEYMAP.get(ch, ch) for ch in s if ch not in "{}<>")


def _seg(e):
    return (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)


def _texts(doc):
    for e in doc.modelspace():
        yield from _text_of(e, "msp")
    for b in doc.blocks:
        if b.name.startswith("*"):
            continue
        for e in b:
            yield from _text_of(e, "block")


def _text_of(e, where):
    t = e.dxftype()
    if t == "TEXT":
        yield where, e.dxf.handle, e.dxf.text or ""
    elif t == "MTEXT":
        yield where, e.dxf.handle, e.plain_text() or ""
    elif t == "INSERT":
        for a in e.attribs:
            yield where, a.dxf.handle, a.dxf.text or ""


def read(path, census=None):
    """census: the T-601 drawn census dict (default: the merged T601_DRAWN.json)."""
    import ezdxf

    doc = ezdxf.readfile(path)
    assert doc.header.get("$INSUNITS") == 4, "drawing units are not mm"
    db = doc.entitydb
    t601 = census if census is not None else json.loads(T601.read_text(encoding="utf-8"))
    marks = [e for e in doc.modelspace().query("LINE") if e.dxf.layer == MARK]
    gaps = {}
    for st, s in sorted(t601["storeys"].items()):
        for g in s["gaps"]:
            if "PANEL_LINES" not in g.get("evidence", []):
                continue
            if abs(g["band_angle_deg"]) > 1e-6:
                raise SystemExit(f"{st}: only axis-parallel bands are read here (angle {g['band_angle_deg']})")
            faces = [_seg(db[h]) for h in g["jamb_face_handles"]]
            ys = sorted({round(p[1], 3) for f in faces for p in f})
            if len(ys) != 2:
                raise SystemExit(f"{st}: jamb faces are not two parallel face lines")
            # inner jamb ends: the two middle x of the four face lines' near ends
            ends = []
            for f in faces:
                ends.extend([f[0][0], f[1][0]])
            ends.sort()
            lo_face, hi_face = ys
            # gap = the span between the face lines' inner ends (the two values bracketing the opening)
            inner = sorted(ends)[len(ends) // 2 - 1: len(ends) // 2 + 1]
            gx0, gx1 = inner
            cx, cy = (gx0 + gx1) / 2, (lo_face + hi_face) / 2
            diag = []
            for e in marks:
                (x0, y0), (x1, y1) = _seg(e)
                if abs(x1 - x0) < 1 or abs(y1 - y0) < 1:
                    continue
                if math.hypot(x1 - x0, y1 - y0) < 1000:
                    continue
                mx, my = (x0 + x1) / 2, (y0 + y1) / 2
                if math.hypot(mx - cx, my - cy) <= 2500:
                    diag.append((e.dxf.handle, "HI" if my > hi_face else ("LO" if my < lo_face else "IN")))
            sides = sorted({s_ for _, s_ in diag if s_ != "IN"})
            shaft = sides[0] if len(sides) == 1 else None
            ref = hi_face if shaft == "HI" else lo_face
            offs = []
            for h in g["ids"]["panel_lines"]:
                (x0, y0), (x1, y1) = _seg(db[h])
                if abs(y1 - y0) > 1e-3:
                    raise SystemExit(f"{st} {h}: panel line not parallel to the band")
                span = (min(x0, x1), max(x0, x1))
                offs.append({"handle": h, "offset_from_shaft_face_mm": round(abs(y0 - ref), 1),
                             "covers_gap": span[0] <= gx0 + 1 and span[1] >= gx1 - 1})
            gaps[st] = {"jamb_face_handles": g["jamb_face_handles"], "width_m": round((gx1 - gx0) * MM, 3),
                        "wall_t_m": round((hi_face - lo_face) * MM, 3),
                        "shaft_cross_handles": sorted(h for h, _ in diag), "shaft_side": shaft is not None,
                        "panel_lines": sorted(offs, key=lambda r: r["offset_from_shaft_face_mm"]),
                        "evidence": ["PANEL_LINES"] + (["SHAFT_CROSS"] if shaft else [])}
    census = text_census(doc)
    return {"schema": "T608_DRAWN_V1",
            "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf)",
            "units": "mm drawing; figures written in m / mm as named",
            "from_census": "research/agents_t601/T601_DRAWN.json (gaps with PANEL_LINES evidence)",
            "lift_gaps": gaps,
            "text_census": {"P7757.dxf": census,
                            "patterns": {k: p.pattern for k, p in PATTERNS.items()},
                            "note": "a hit is listed by handle only; the builder refuses any hit it has no reviewed "
                                    "reading for (t608_alsenan.REVIEWED_HITS)"}}


def text_census(doc):
    hits = {k: set() for k in PATTERNS}
    n = 0
    for where, h, s in _texts(doc):
        n += 1
        for form in (s, decode_keyed(s)):
            for k, p in PATTERNS.items():
                if p.search(form):
                    hits[k].add(h)
    return {"text_entities": n, "hits": {k: sorted(v) for k, v in hits.items()}}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--st", help="the structural DXF (Drive 'Alsenan chalet project' / ST7757 dxf.dxf), text census only")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    data = read(a.dxf)
    if a.st:
        import ezdxf

        data["text_census"]["ST7757 dxf.dxf"] = text_census(ezdxf.readfile(a.st))
    text = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if a.write:
        OUT.write_text(text, encoding="utf-8")
        print(f"written {OUT.name}")
        return 0
    same = OUT.exists() and OUT.read_text(encoding="utf-8") == text
    print("re-read identical" if same else "re-read DIFFERS")
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
