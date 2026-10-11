"""DRAWING MODEL (M2) - a normalized, source-pointed model of one structural drawing set (generic, stdlib).

Input: the plain intake record of tools/urban_intake.py (geometry placed in world coordinates by the K2 kernel,
texts placed by ezdxf.disassemble). Output: sheets with a role and a storey, every entity mapped to its sheet, in
drawing units with the unit -> metre factor and its evidence. Nothing here knows a project:

    sheets      outermost closed axis-aligned frames at least `min_frame` (drawing units) in size; a sheet's role and
                storey come from the title-like texts inside it, matched against a bilingual lexicon (English and
                Arabic, Kuwait villa vocabulary). Several matches -> the strongest title wins and the others are kept as
                evidence; no match -> UNKNOWN (never guessed from position).
    units       $INSUNITS gives the declared unit; it is checked against the drawn geometry (closed rectangles vs
                typical member sizes). A missing or contradicted unit is a WARNING with both candidates.
    labels      every text is normalized (CAD control codes, Arabic-Indic digits) and matched to an engineering label
                family (footing, column, beam, ground beam, strap, slab, stair, landing, lintel, neck, pool, lift ...)
                by token, never by position.

The model never rewrites a source coordinate: local sheet coordinates are offsets from the frame origin and the
transformation is recorded.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict

POLICY_ID = "DRAWING_MODEL_V1"
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")

# (role, storey, weight, patterns) - first the most specific; patterns match the NORMALIZED upper-case title
SHEET_LEXICON = (
    ("GROUND_BEAM_PLAN", "GROUND", 9, (r"GROUND\s*BEAMS?\s*(PLAN|LAYOUT)", r"TIE\s*BEAMS?\s*PLAN", r"G\.?\s*B\.?\s*PLAN",
                                       r"مخطط\s*الميد", r"الميدات")),
    ("FOUNDATION_PLAN", "FOUNDATION", 9, (r"FOUNDATIONS?\s*(PLAN|LAYOUT)", r"FOOTINGS?\s*(PLAN|LAYOUT)",
                                          r"مخطط\s*القواعد", r"القواعد", r"الأساسات")),
    ("COLUMN_PLAN", "ALL", 8, (r"COLUMNS?\s*(&|AND)?\s*(AXIS|AXES)?\s*(PLAN|LAYOUT)", r"مخطط\s*الأعمدة")),
    ("SLAB_PLAN", "GF", 8, (r"GROUND\s*FLOOR\s*(ROOF|CEILING)?\s*SLAB", r"GROUND\s*FLOOR\s*ROOF",
                            r"سقف\s*الدور\s*الأرضي", r"سقف\s*الأرضي")),
    ("SLAB_PLAN", "1F", 8, (r"(FIRST|1ST)\s*FLOOR\s*(ROOF|CEILING)?\s*SLAB", r"(FIRST|1ST)\s*FLOOR\s*ROOF",
                            r"سقف\s*الدور\s*الأول")),
    ("SLAB_PLAN", "2F", 8, (r"(SECOND|2ND)\s*FLOOR\s*(ROOF|CEILING)?\s*SLAB", r"(SECOND|2ND)\s*FLOOR\s*ROOF",
                            r"سقف\s*الدور\s*الثاني")),
    ("SLAB_PLAN", "3F", 8, (r"(THIRD|3RD)\s*FLOOR\s*(ROOF|CEILING)?\s*SLAB", r"سقف\s*الدور\s*الثالث")),
    ("SLAB_PLAN", "ROOF", 7, (r"(TOP|UPPER|MAIN|PENT\s*HOUSE)\s*ROOF", r"ROOF\s*SLAB", r"سقف\s*السطح", r"الملحق")),
    ("SCHEDULE", "ALL", 6, (r"SCHEDULE\s*OF", r"SCHEDULE", r"جدول")),
    ("SECTION", "ALL", 4, (r"SECTION\s+[A-Z]\s*-\s*[A-Z]", r"قطاع")),
    ("DETAIL", "ALL", 3, (r"DETAILS?\s+OF", r"TYPICAL\s+DETAIL", r"تفصيل")),
)
# engineering label families (bilingual); tag patterns are for plan marks, words for titles / notes
LABEL_WORDS = {
    "FOOTING": ("FOOTING", "FOUNDATION", "قاعدة", "قواعد"),
    "COLUMN": ("COLUMN", "عمود", "أعمدة"),
    "BEAM": ("BEAM", "كمرة", "جسر", "كمرات", "جسور"),
    "GROUND_BEAM": ("GROUND BEAM", "TIE BEAM", "ميدة", "ميدات"),
    "STRAP_BEAM": ("STRAP", "شداد"),
    "SLAB": ("SLAB", "سقف", "بلاطة"),
    "STAIR": ("STAIR", "درج", "سلم"),
    "LANDING": ("LANDING", "بسطة"),
    "LINTEL": ("LINTEL", "عتب", "عتبة"),
    "NECK": ("NECK", "رقبة"),
    "POOL": ("POOL", "SWIMMING", "مسبح"),
    "LIFT": ("LIFT", "ELEVATOR", "مصعد"),
    "WALL": ("WALL", "جدار", "حائط"),
}
# plan-mark tag families: (family, regex on the normalized mark)
TAG_FAMILIES = (
    ("FOOTING", r"^(F|PF|CF|FC|FF|IF)(-?\d{1,3}[A-Z]?|N)?$"),          # M3: FF (a schedule type) and F-1 forms
    ("COLUMN", r"^(C|CN|TC|SC)\d{0,3}[A-Z]?$"),
    ("GROUND_BEAM", r"^(GB|TB|G\.B)\d{0,3}[A-Z]?$"),
    ("STRAP_BEAM", r"^(SB|STB|STR)\d{1,3}[A-Z]?$"),
    ("CONTINUOUS_BEAM", r"^CB\d{1,3}[A-Z]?$"),
    ("BEAM", r"^(B|RB|EB|HB)\d{1,3}[A-Z]?$"),
    ("LINTEL", r"^(L|LT)\d{1,3}[A-Z]?$"),
    ("SLAB", r"^(S|SL)-?\d{1,3}[A-Z]?$"),
)
UNIT_CANDIDATES_M = {"mm": 0.001, "cm": 0.01, "m": 1.0, "in": 0.0254}
TYPICAL_MEMBER_M = (0.15, 1.2)            # widths of columns / beams / small footings, used only to test a unit


def normalize(raw):
    """CAD control codes and Arabic-Indic digits -> plain text; formatting removed; whitespace collapsed."""
    if raw is None:
        return ""
    s = str(raw)
    s = re.sub(r"%%[cC]", "Ø", s)
    s = re.sub(r"%%[dD]", "°", s)
    s = re.sub(r"%%[pP]", "±", s)
    s = re.sub(r"%%[uUoOkK]", "", s)
    s = s.replace("\\P", " ").replace(" ", " ")
    s = s.translate(ARABIC_DIGITS)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("⌀", "Ø").replace("ø", "Ø").replace("Φ", "Ø").replace("φ", "Ø")
    return re.sub(r"\s+", " ", s).strip()


def mark_family(mark):
    m = normalize(mark).upper().replace(" ", "")
    for fam, rx in TAG_FAMILIES:
        if re.match(rx, m):
            return fam, m
    return None, m


def label_families(text):
    t = normalize(text).upper()
    return sorted({f for f, words in LABEL_WORDS.items() for w in words if w.upper() in t})


def classify_title(texts):
    """[(text, weight_hint)] -> (role, storey, evidence list). The strongest lexicon match wins."""
    best, ev = None, []
    for t in texts:
        u = normalize(t).upper()
        if re.match(r"^\s*(SCHEDULE|TABLE|جدول)\b", u) or re.match(r"^\s*جدول", u):
            # a title that OPENS with a schedule word is a schedule, whatever members it lists ("schedule of
            # footings ..." must not read as a foundation plan) - M2 component-test finding
            ev.append({"text_match": "LEADING_SCHEDULE_WORD", "role": "SCHEDULE", "storey": "ALL", "weight": 99})
            best = ("SCHEDULE", "ALL", 99)
            continue
        for role, storey, w, pats in SHEET_LEXICON:
            for p in pats:
                if re.search(p, u):
                    ev.append({"text_match": p, "role": role, "storey": storey, "weight": w})
                    if best is None or w > best[2]:
                        best = (role, storey, w)
                    break
    if best is None:
        return "UNKNOWN", "UNKNOWN", ev
    return best[0], best[1], ev


def _inside(box, x, y):
    return box[0] <= x <= box[2] and box[1] <= y <= box[3]


def _rect(pts, eps=1e-6):
    if len(pts) == 5 and abs(pts[0][0] - pts[-1][0]) < eps and abs(pts[0][1] - pts[-1][1]) < eps:
        pts = pts[:4]
    if len(pts) != 4:
        return None
    xs = sorted({round(p[0], 6) for p in pts})
    ys = sorted({round(p[1], 6) for p in pts})
    if len(xs) != 2 or len(ys) != 2:
        return None
    return (xs[0], ys[0], xs[1], ys[1])


def closed_rectangles(segments, eps=1.0):
    """Axis-aligned closed rectangles formed by the four sides of one polyline (consecutive spans of one source)."""
    by_src = defaultdict(list)
    for s in segments:
        by_src[s["id"].rsplit(":", 1)[0]].append(s)
    out = []
    for src, ss in by_src.items():
        if len(ss) != 4:
            continue
        pts = [tuple(s["a"]) for s in ss]
        r = _rect(pts)
        if r and r[2] - r[0] > eps and r[3] - r[1] > eps:
            out.append({"box": r, "layer": ss[0]["layer"], "source": src})
    return out


def frames(segments, min_frame):
    rects = closed_rectangles(segments)
    big = [r for r in rects if r["box"][2] - r["box"][0] >= min_frame[0] and r["box"][3] - r["box"][1] >= min_frame[1]]
    outer = [r for r in big if not any(o is not r and o["box"][0] <= r["box"][0] and o["box"][1] <= r["box"][1] and
                                       o["box"][2] >= r["box"][2] and o["box"][3] >= r["box"][3] and o["box"] != r["box"]
                                       for o in big)]
    seen, out = set(), []
    for r in sorted(outer, key=lambda r: r["box"]):
        if r["box"] in seen:
            continue
        seen.add(r["box"])
        out.append(r)
    return out


def infer_units(intake, rects):
    """Declared unit vs drawn evidence: the share of small closed rectangles whose short side falls in the typical
    member range under each candidate unit. Returns {unit_m, declared, evidence, warning}."""
    declared = intake.get("unit_m")
    sides = [min(r["box"][2] - r["box"][0], r["box"][3] - r["box"][1]) for r in rects]
    sides = [s for s in sides if s > 0]
    score = {}
    for name, f in UNIT_CANDIDATES_M.items():
        score[name] = sum(1 for s in sides if TYPICAL_MEMBER_M[0] <= s * f <= TYPICAL_MEMBER_M[1])
    best = max(score, key=lambda k: (score[k], -abs(UNIT_CANDIDATES_M[k] - (declared or 0.001))))
    warning = None
    if declared is None:
        unit_m = UNIT_CANDIDATES_M[best]
        warning = f"$INSUNITS not set: unit inferred as {best} from {score[best]} member-sized outlines"
    else:
        unit_m = declared
        dec_name = next((k for k, f in UNIT_CANDIDATES_M.items() if abs(f - declared) < 1e-12), str(declared))
        if score.get(best, 0) > 2 * max(score.get(dec_name, 0), 1) and best != dec_name:
            warning = f"declared unit {dec_name} contradicted by drawn geometry (best fit {best}); declared kept"
    return {"unit_m": unit_m, "declared_m": declared, "member_fit": score, "warning": warning}


def build(intake, *, min_frame_m=(10.0, 7.0)):
    """The normalized model. Sheets in drawing units; unit_m converts to metres."""
    rects = closed_rectangles(intake["segments"])
    units = infer_units(intake, rects)
    f = units["unit_m"]
    fr = frames(intake["segments"], (min_frame_m[0] / f, min_frame_m[1] / f))
    texts = [dict(t, norm=normalize(t["value"])) for t in intake["texts"]]
    sheets = []
    for k, r in enumerate(fr, 1):
        box = r["box"]
        inside = [t for t in texts if _inside(box, t["x"], t["y"])]
        titles = [t["norm"] for t in inside if 4 <= len(t["norm"]) <= 80]
        role, storey, ev = classify_title(titles)
        sheets.append({"sheet_id": f"SH{k:02d}", "box": box, "frame_source": r["source"], "role": role,
                       "storey": storey, "title_evidence": ev[:6], "origin": (box[0], box[1]),
                       "n_texts": len(inside), "transform": "local = world - origin (drawing units)"})
    def sheet_of(x, y):
        for s in sheets:
            if _inside(s["box"], x, y):
                return s["sheet_id"]
        return None
    for t in texts:
        t["sheet"] = sheet_of(t["x"], t["y"])
        t["mark_family"], t["mark"] = mark_family(t["norm"])
    return {"policy": POLICY_ID, "sha256": intake.get("sha256"), "file": intake.get("file"), "units": units,
            "sheets": sheets, "texts": texts, "rects": rects, "sheet_of": sheet_of,
            "role_counts": dict(Counter(s["role"] for s in sheets))}


def sheet_entities(model, intake, sheet_id):
    s = next(x for x in model["sheets"] if x["sheet_id"] == sheet_id)
    b = s["box"]
    segs = [x for x in intake["segments"] if _inside(b, *x["a"]) and _inside(b, *x["b"])]
    arcs = [x for x in intake["arcs"] if _inside(b, *x["s"]) and _inside(b, *x["e"])]
    texts = [t for t in model["texts"] if t["sheet"] == sheet_id]
    rects = [r for r in model["rects"] if _inside(b, r["box"][0], r["box"][1]) and _inside(b, r["box"][2], r["box"][3])]
    return {"segments": segs, "arcs": arcs, "texts": texts, "rects": rects, "box": b}


def policy_record():
    return {"policy": POLICY_ID, "sheet_roles": sorted({r for r, *_ in SHEET_LEXICON}),
            "label_families": sorted(LABEL_WORDS), "tag_families": [f for f, _ in TAG_FAMILIES],
            "rule": "roles and storeys come from printed titles only; an unmatched sheet is UNKNOWN"}
