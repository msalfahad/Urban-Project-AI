"""S7A - dated engineering-QA layer over the frozen S7 slab release (2026-10-08). No S7 file is edited.

    python3 -I research/alsenan_slab_rebar_s7a_qa/build_s7a_qa.py

What it does, after hash-checking the S7, PRE-S7.1 and PRE-S7 freeze manifests and the two issued drawings:

1. Re-reads the original sources for the top-over-support rule:
   - plan note 2 from ST7757.dxf: its Arabic text, decoded from the legacy SHX font;
   - the p.15 TYP. SLAB ON BEAMS detail: the frozen PRE-S7 visual reading, plus the drawn stroke geometry read from
     the PDF vector layers (pypdf only; no renderer);
   - the continuous-beam schedule dimensions ("0.22 Ln", "0.3 Ln2").
   Each candidate reading of "one third of the span" is recorded with its supporting and contrary evidence. None is
   picked for convenience: the source does not establish one.
2. Recomputes S7's released top-over-support extensions (the frozen 04_S7_BAR_RUNS.csv strip rows) under five
   readings, A to E. The opposite-side clear span comes from the frozen PRE-S7.1 local bar strips, matched along the
   bar line by transverse overlap. Reading A must reproduce S7's frozen kg exactly.
3. Tabulates the p.15 50/50 and 0.125 L bottom rules by support type, and audits every strip end: is its continuity
   ESTABLISHED by geometry, or only INFERRED?
4. Writes a dated errata record. It withdraws S7's "lower bound of the physical steel" wording and leaves S7's
   3,802.015 kg unchanged.

The builder is blind. It reads no external reference quantity, no earlier estimate and no steel-per-volume profile, and it chooses no interpretation by comparing against one. Every scenario figure is SENSITIVITY_ONLY: none
is a release, and none replaces the S7 total.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "research" / "source_recovery_delta") not in sys.path:
    sys.path.insert(0, str(ROOT / "research" / "source_recovery_delta"))

from engine.source import delta_release as DR  # noqa: E402
from engine.source import legacy_text as LT  # noqa: E402

import vector_pdf as VP  # noqa: E402

ROUND = "S7A_QA"
QA_DATE = "2026-10-08"
POLICY = "S7A_SOURCE_INTERPRETATION_QA_V1"
BASELINE_HEAD = "aeb8798"
R = ROOT / "research"
S7P = R / "alsenan_slab_rebar_s7"
P71 = R / "alsenan_slab_rebar_pre_s7_1"
PRE = R / "alsenan_slab_rebar_pre_s7"
S1 = R / "alsenan_structural_census_s1"
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
PDF = ROOT / "data/inputs/by_sha256/74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3.pdf"
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
MANIFESTS = {"PRE-S7": PRE / "PRE_S7_FREEZE_MANIFEST.json", "PRE-S7.1": P71 / "PRE_S7_1_FREEZE_MANIFEST.json",
             "S7": S7P / "12_S7_FREEZE_MANIFEST.json"}
S7_TOTAL_KEY = "RESTRICTED_S7_PROJECT_BASIS_KG"
CODE = ["research/alsenan_slab_rebar_s7a_qa/build_s7a_qa.py", "research/source_recovery_delta/vector_pdf.py",
        "engine/source/legacy_text.py", "engine/source/delta_release.py"]
INPUTS = ["research/alsenan_slab_rebar_s7/12_S7_FREEZE_MANIFEST.json",
          "research/alsenan_slab_rebar_s7/01_S7_RELEASE_ITEMS.csv",
          "research/alsenan_slab_rebar_s7/02_S7_BLOCKED_ITEMS.csv",
          "research/alsenan_slab_rebar_s7/04_S7_BAR_RUNS.csv",
          "research/alsenan_slab_rebar_s7/09_S7_PROJECT_SUMMARY.json",
          "research/alsenan_slab_rebar_pre_s7_1/PRE_S7_1_FREEZE_MANIFEST.json",
          "research/alsenan_slab_rebar_pre_s7_1/05_TOP_RULE_IDENTITY.csv",
          "research/alsenan_slab_rebar_pre_s7_1/07_LOCAL_BAR_STRIPS.csv",
          "research/alsenan_slab_rebar_pre_s7_1/09_REMAINING_CONFLICTS.csv",
          "research/alsenan_slab_rebar_pre_s7/PRE_S7_FREEZE_MANIFEST.json",
          "research/alsenan_slab_rebar_pre_s7/01_SLAB_PANEL_CENSUS.csv",
          "research/alsenan_slab_rebar_pre_s7/05_SUPPORT_REGISTER.csv",
          "research/alsenan_slab_rebar_pre_s7/source_search_inputs/PRE_S7_VISUAL_READING.json",
          "research/alsenan_structural_census_s1/STRUCTURAL_PROJECT_RULE_REGISTER.json"]
OUTPUTS = ["00_README.md", "01_TOP_EXTENT_INTERPRETATIONS.csv", "02_SOURCE_EVIDENCE.json",
           "03_BAR_FAMILY_IDENTITY_QA.csv", "04_TOP_SENSITIVITY_SCENARIOS.csv", "05_TOP_SENSITIVITY_BY_END_CLASS.csv",
           "06_TOP_SENSITIVITY_BY_STRIP_END.csv", "07_BOTTOM_RULE_SUPPORT_TYPE_TABLE.csv",
           "08_END_CONDITION_AUDIT.csv", "09_S7_ERRATA.json", "10_S7A_SUMMARY.json"]
MANIFEST_NAME = "11_S7A_FREEZE_MANIFEST.json"

NOTE2_RULE = "P4-6-NOTE-2-TOP-OVER-BEAMS"
NOTE2_HANDLES = {"GFRS": ("D8", "D9", "DA"), "FFRS": ("E1", "E2", "E3"), "SFRS": ("EA", "EB", "EC")}
NOTE2_TAIL = "الجسور بطول ثلث البحر في الاتجاهين"
NOTE2_HEAD = "يجب وضع حديد علوي للبلاطات فوق"
SPAN_WORD = "البحر"
LOWER_BOUND_WORDING = "a lower bound of the physical steel (every blocked portion is excluded, not zero)"
# S7's own lower-bound claims outside its frozen outputs (post-freeze write-up, by line; not read by this builder)
POST_FREEZE_CLAIMS = [
    {"file": "research/alsenan_slab_rebar_s7/post_freeze/S7_POST_FREEZE_COMPARISON.md", "line": 9,
     "wording": "That is the restricted lower bound of 476 items"},
    {"file": "research/alsenan_slab_rebar_s7/post_freeze/S7_POST_FREEZE_COMPARISON.md", "line": 57,
     "wording": "against a restricted lower-bound QTO"}]

TE_ROLE, TX_ROLE = "TOP_OVER_SUPPORT_EXTENSION", "TOP_SUPPORT_CROSSING"
CONT = ("END_CONTINUOUS_RUN", "END_CONTINUOUS_SPLIT")
NONCONT = ("END_NON_CONTINUOUS",)
UNRES = ("END_UNRESOLVED",)
SCENARIOS = ("A", "B", "C", "D1", "D2", "E")
SCENARIO_TEXT = {
    "A": "S7 frozen reading (AD2-D06 / S7-AC01): one third of the local clear span, from the support face, into "
         "each side panel, at every end class",
    "B": "note 2 as a TOTAL bar length of L/3 centred on the support: L_own/6 from the face into each side panel, at "
         "every end class (the crossing over the beam is kept)",
    "C": "one third of the COMBINED span: (L_own + L_opposite)/6 from the face into each side at a continuous end; "
         "at a non-continuous end only one span exists -> L_own/6; an unresolved end uses the opposite span "
         "where a strip faces it, else L_own/6",
    "D1": "p.15 extents with note-2 size / spacing (one family, p.15 length): continuous 0.30 x max(L_own, "
          "L_opposite) per side from the face; non-continuous 0.25 x L_own; unresolved ends taken as "
          "NON-continuous (0.25 x L_own)",
    "D2": "as D1, but unresolved ends taken as CONTINUOUS: 0.30 x max(L_own, L_opposite), or 0.30 x L_own where "
          "no strip faces it",
    "E": "one third of the LARGER adjacent span per side (by analogy with p.15 'whichever larger'): max(L_own, "
         "L_opposite)/3 at continuous and unresolved ends; L_own/3 at non-continuous ends"}


class Stop(Exception):
    pass


def check(cond, what):
    if not cond:
        raise Stop(f"S7A STOP: {what}")


# ------------------------------------------------------------------ io helpers
def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _full(v):
    if v is None:
        return None
    s = f"{float(v):.9f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return _full(v)
    if isinstance(v, (list, tuple, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(name, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in fields})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def _json(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _r(v, n=6):
    return None if v is None else round(float(v), n)


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode())
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()[:16]


# ------------------------------------------------------------------ frozen inputs
def verify_inputs():
    frozen = {k: DR.verify_frozen(m, ROOT) for k, m in MANIFESTS.items()}
    s7 = _j(MANIFESTS["S7"])
    for f in ("01_S7_RELEASE_ITEMS.csv", "02_S7_BLOCKED_ITEMS.csv", "04_S7_BAR_RUNS.csv",
              "09_S7_PROJECT_SUMMARY.json"):
        check(s7["outputs"][f] == _sha(S7P / f), f"S7 {f} is the frozen output")
    check(s7["state"] == "FROZEN_BEFORE_REFERENCE_COMPARISON", "S7 is frozen")
    o71 = _j(MANIFESTS["PRE-S7.1"])["outputs"]
    for f in ("05_TOP_RULE_IDENTITY.csv", "07_LOCAL_BAR_STRIPS.csv", "09_REMAINING_CONFLICTS.csv"):
        check(o71[f] == _sha(P71 / f), f"PRE-S7.1 {f} is the frozen output")
    pre = _j(MANIFESTS["PRE-S7"])
    for f in ("01_SLAB_PANEL_CENSUS.csv", "05_SUPPORT_REGISTER.csv"):
        check(pre["outputs"][f] == _sha(PRE / f), f"PRE-S7 {f} is the frozen output")
    for f in ("research/alsenan_slab_rebar_pre_s7/source_search_inputs/PRE_S7_VISUAL_READING.json",
              "research/alsenan_structural_census_s1/STRUCTURAL_PROJECT_RULE_REGISTER.json"):
        check(pre["inputs"][f] == _sha(ROOT / f), f"PRE-S7 input {f} unchanged")
    check(pre["drawing_sha256"] == {"ST7757.dxf": DXF_SHA, "ST7757.pdf": PDF_SHA}, "PRE-S7 drawings")
    check(_sha(DXF) == DXF_SHA and _sha(PDF) == PDF_SHA, "issued ST7757 DXF / PDF unchanged")
    return frozen


# ------------------------------------------------------------------ source evidence: note 2, span word, schedules
def note2_dxf(doc):
    """The three plan-note copies (GF / 1F / 2F roof slab sheets), decoded."""
    fam = {s.dxf.name: LT.font_family(s.dxf.font) for s in doc.styles}
    out = {}
    for sheet, (h_head, h_spec, h_tail) in NOTE2_HANDLES.items():
        rec = {}
        for role, h in (("head", h_head), ("spec", h_spec), ("tail", h_tail)):
            e = doc.entitydb.get(h)
            check(e is not None and e.dxftype() == "TEXT", f"note 2 entity {h}")
            raw = e.dxf.text
            d = LT.decode(raw, fam.get(e.dxf.style))
            rec[role] = {"handle": h, "layer": e.dxf.layer, "style": e.dxf.style,
                         "font_family": fam.get(e.dxf.style), "raw": raw, "decoded": d["text"],
                         "decode_state": d["state"], "unknown_codes": d["unknown"],
                         "insert_mm": [round(e.dxf.insert[0], 1), round(e.dxf.insert[1], 1)],
                         "height": round(float(e.dxf.height), 1)}
        check(NOTE2_HEAD in rec["head"]["decoded"], f"note 2 head on {sheet}")
        check(rec["spec"]["raw"] == "5%%C10/m", f"note 2 specification on {sheet}")
        check(rec["tail"]["decoded"] == NOTE2_TAIL, f"note 2 tail on {sheet}")
        out[sheet] = rec
    return out


def span_word_occurrences(doc):
    """Every decoded text in the drawing that carries the word used for 'span' in note 2."""
    fam = {s.dxf.name: LT.font_family(s.dxf.font) for s in doc.styles}
    out = []
    spaces = [("MODEL", doc.modelspace())] + [(b.name, b) for b in doc.blocks
                                              if not b.name.upper().startswith("*MODEL")]
    for name, sp in spaces:
        for e in sp.query("TEXT MTEXT"):
            raw = e.dxf.text if e.dxftype() == "TEXT" else e.text
            f = fam.get(e.dxf.get("style"))
            dec = LT.decode(raw, f)["text"] if f else raw
            if SPAN_WORD in dec:
                sib = [x.dxf.text for x in sp.query("TEXT") if x is not e] if name != "MODEL" else []
                ins = [i.dxf.handle for i in doc.modelspace().query("INSERT") if i.dxf.name == name] \
                    if name != "MODEL" else []
                out.append({"space": name, "handle": e.dxf.handle, "decoded": dec, "siblings_in_block": sib,
                            "block_inserts_in_model": ins})
    return out


def beam_schedule_fraction_dims(doc):
    """Continuous-beam schedule dimensions labelled as a fraction of Ln: which side of which support they measure."""
    rows = []
    for d in doc.modelspace().query("DIMENSION"):
        t = d.dxf.get("text", "") or ""
        if "Ln" not in t:
            continue
        p2, p3 = d.dxf.get("defpoint2"), d.dxf.get("defpoint3")
        rows.append({"handle": d.dxf.handle, "layer": d.dxf.layer, "text": t.replace("\\A1;", ""),
                     "x0": round(min(p2[0], p3[0]), 1), "x1": round(max(p2[0], p3[0]), 1),
                     "row_y": round(d.dxf.defpoint[1], 0)})
    spans = [r for r in rows if re.fullmatch(r"Ln\d?", r["text"])]
    fracs = [r for r in rows if not re.fullmatch(r"Ln\d?", r["text"])]
    joints = sorted({x for s in spans for x in (s["x0"], s["x1"])})
    for f in fracs:
        near = min(joints, key=lambda j: min(abs(f["x0"] - j), abs(f["x1"] - j))) if joints else None
        f["nearest_span_joint_x"] = near
        if near is not None:
            f["side_of_joint"] = "RIGHT" if f["x0"] >= near - 1 else "LEFT"
            f["offset_from_joint"] = round(min(abs(f["x0"] - near), abs(f["x1"] - near)), 1)
    pairs = []
    for a in fracs:
        for b in fracs:
            if a["handle"] < b["handle"] and a.get("nearest_span_joint_x") == b.get("nearest_span_joint_x") and \
                    a.get("side_of_joint") != b.get("side_of_joint") and abs(a["row_y"] - b["row_y"]) < 300:
                pairs.append({"joint_x": a["nearest_span_joint_x"], "left": a["text"] if a["side_of_joint"] ==
                              "LEFT" else b["text"], "right": b["text"] if a["side_of_joint"] == "LEFT" else a["text"],
                              "offsets_from_joint": [a["offset_from_joint"], b["offset_from_joint"]]})
    return {"dimensions": sorted(rows, key=lambda r: (r["row_y"], r["x0"])), "per_side_pairs": pairs}


# ------------------------------------------------------------------ source evidence: p.15 strokes (NTS)
P15_BOX = (110.0, 500.0, 240.0, 1100.0)    # TYP. SLAB ON BEAMS DETAIL, PDF points (page rotated 270)


def _const_x(s, tol=0.05):
    return abs(s[2][0] - s[3][0]) <= tol


def _const_y(s, tol=0.05):
    return abs(s[2][1] - s[3][1]) <= tol


def p15_strokes():
    """Drawn proportions of the slab-on-beams detail. The sheet is NOT TO SCALE ('THE BUILDER TO WORK WITH STATED
    DIMENSIONS NOT TO SCALE DRAWING'): these ratios are read only to see WHERE the drawn bars run (which side of which
    face), never as lengths."""
    ps = VP.paths(PDF, 15)
    ext = [s for s in VP.segments(ps, P15_BOX, layers={"S-EXTL.D"}) if math.dist(s[2], s[3]) > 5]
    rein = [s for s in VP.segments(ps, P15_BOX, layers={"S-REIN.D"}) if math.dist(s[2], s[3]) > 5]
    slab_top = max((s for s in ext if _const_x(s)), key=lambda s: math.dist(s[2], s[3]))
    x_top = slab_top[2][0]
    ys = sorted({round(p[1], 1) for s in ext if _const_y(s) and s[1] >= 0.7
                 for p in (s[2], s[3]) if abs(p[0] - 120.5) < 0.6 or abs(p[0] - 148.8) < 0.6})
    faces = [y for y in ys if any(_const_y(s) and abs(s[2][1] - y) < 0.2 and
                                   abs(abs(s[2][0] - s[3][0]) - 28.3) < 0.6 for s in ext)]
    check(len(faces) >= 3, f"p.15 support faces found {faces}")
    beam_l2_face, beam_l1_face = min(faces), sorted(faces)[1]          # continuous beam: two faces
    nc_inner = max(f for f in faces if f > beam_l1_face + 100)          # non-continuous support, inner face
    top = sorted((s for s in rein if _const_x(s) and abs(s[2][0] - (x_top - 2.9)) < 0.5 and
                  math.dist(s[2], s[3]) > 50), key=lambda s: min(s[2][1], s[3][1]))
    check(len(top) == 3, f"p.15 three long top-bar strokes, found {len(top)}")
    l2_top, l1_top, nc_top = top
    lo = lambda s: min(s[2][1], s[3][1])  # noqa: E731
    hi = lambda s: max(s[2][1], s[3][1])  # noqa: E731
    over = [s for s in rein if _const_x(s) and abs(s[2][0] - (x_top - 2.9)) < 0.5 and
            lo(s) <= beam_l2_face + 6 and hi(s) >= beam_l1_face - 6]
    l1_drawn = nc_inner - beam_l1_face
    cont_l1 = hi(l1_top) - beam_l1_face
    cont_l2 = beam_l2_face - lo(l2_top)
    anchor = nc_inner - lo(nc_top)
    bottoms = sorted((s for s in rein if _const_x(s) and s[2][0] < 155 and math.dist(s[2], s[3]) > 50),
                     key=lambda s: (s[2][0], lo(s)))
    stops = [{"x_pt": round(s[2][0], 1), "from_pt": round(lo(s), 1), "to_pt": round(hi(s), 1)} for s in bottoms]
    return {"page": 15, "box_pdf_pt": list(P15_BOX), "rotation": 270, "nts": True,
            "slab_top_x_pt": round(x_top, 1),
            "continuous_beam_faces_y_pt": [round(beam_l2_face, 1), round(beam_l1_face, 1)],
            "non_continuous_inner_face_y_pt": round(nc_inner, 1),
            "top_bar_strokes_pt": {"L2_side": [round(lo(l2_top), 1), round(hi(l2_top), 1)],
                                   "L1_side_at_continuous": [round(lo(l1_top), 1), round(hi(l1_top), 1)],
                                   "non_continuous_anchor": [round(lo(nc_top), 1), round(hi(nc_top), 1)]},
            "top_stroke_over_continuous_beam": bool(over),
            "drawn_L1_clear_pt": round(l1_drawn, 1),
            "drawn_extent_from_face_pt": {"continuous_L1_side": round(cont_l1, 1),
                                          "continuous_L2_side": round(cont_l2, 1),
                                          "non_continuous_anchor": round(anchor, 1)},
            "drawn_ratio_to_L1": {"continuous_L1_side": round(cont_l1 / l1_drawn, 3),
                                  "non_continuous_anchor": round(anchor / l1_drawn, 3)},
            "bottom_bar_strokes_pt": stops,
            "reading": "at the continuous support the top bar is one stroke that crosses the beam and runs into BOTH "
                       "spans, measured from the two faces (drawn ~93.6 pt on the L1 side, ~85.6 pt on the L2 side); "
                       "at the non-continuous support the top anchor bar runs from the support into L1 only and "
                       "turns down into the support. The p.15 extents are therefore PER SIDE, FROM THE FACE. The "
                       "drawn ratios (0.33 L1 continuous, 0.25 L1 anchor) are not used: the sheet is not to scale "
                       "and the printed labels are 0.30 max(L1, L2) and 0.25 L1."}


# ------------------------------------------------------------------ interpretations
def interpretations(ev):
    nb = ev["beam_schedule"]["per_side_pairs"]
    return [
        {"READING_ID": "I-A", "SCENARIO": "A", "READING": "L/3 of each adjacent clear span, from the support face, "
         "per side (S7 frozen)",
         "SUPPORTING_EVIDENCE": ["p.15 TYP. SLAB ON BEAMS: the top bar over a continuous support runs into both "
                                 "spans and its extent is dimensioned from the face (per side)",
                                 "p.15 'TOP ANCHOR BARS. FOR SIZE & SPACING SEE SCHEDULE OR PLAN': the top family's "
                                 "length convention is the detail's (per side, from the face)",
                                 f"continuous-beam schedule: {len(nb)} pairs of fraction-of-Ln dimensions, one each "
                                 "side of a support, each labelled with its own span (per side, from the face) - "
                                 "beams, not slabs: analogous project evidence only",
                                 "'في الاتجاهين' ('in the two directions') can be read as the two sides of the beam"],
         "CONTRARY_EVIDENCE": ["'بطول ثلث البحر' literally gives the bar a LENGTH ('with a length of') of one third "
                               "of the span, not an extension each side",
                               "'في الاتجاهين' is the usual Arabic note wording for the two orthogonal bar "
                               "directions of a slab (it does not have to mean the two sides)",
                               "p.15 note 2 of the temperature notes writes top-over-beam steel as one TOTAL length "
                               "('X 2000 ... 1000 @ SPANDREL'): in this sheet set a single length over a beam is a "
                               "total length (analogous evidence, temperature family)"],
         "STATE": "SUPPORTED_NOT_ESTABLISHED",
         "AUTHORITY": "URBAN_OWNER_MEASUREMENT_RULE (AD2-D06, URBAN_QTO_TOP_OVER_SUPPORT_EXTENT_V1); the 1/3 ratio "
                      "is PROJECT_SOURCE"},
        {"READING_ID": "I-B", "SCENARIO": "B", "READING": "a total bar length of L/3, centred on the support (L/6 per "
         "side from the face)",
         "SUPPORTING_EVIDENCE": ["literal wording: 'بطول' = 'with a length of' one third of the span",
                                 "p.15 temperature note 2: top steel over beams given as one total length (2000) "
                                 "with half (1000) at a spandrel - total-length convention in the same set "
                                 "(analogous)"],
         "CONTRARY_EVIDENCE": ["L/6 per side is shorter than both p.15 extents (0.25 L1 at a non-continuous support, "
                               "0.30 max(L1, L2) at a continuous one) for the same top family",
                               "note 2 states no centring, origin or beam-width treatment"],
         "STATE": "SUPPORTED_NOT_ESTABLISHED", "AUTHORITY": "NOT_ESTABLISHED (reading of PROJECT_SOURCE wording)"},
        {"READING_ID": "I-C", "SCENARIO": "C", "READING": "one third of the combined span L1 + L2 (total), i.e. "
         "(L1 + L2)/6 per side",
         "SUPPORTING_EVIDENCE": ["'البحر' (the span) is singular and names no side: a support between two spans "
                                 "has no single span unless they are combined or one is chosen"],
         "CONTRARY_EVIDENCE": ["no project text combines spans; p.15 chooses the larger span instead "
                               "('WHICHEVER LARGER')", "undefined at a non-continuous support"],
         "STATE": "WEAK_NOT_ESTABLISHED", "AUTHORITY": "NOT_ESTABLISHED"},
        {"READING_ID": "I-D", "SCENARIO": "D1/D2", "READING": "note 2 supplies size / spacing only; the p.15 typical "
         "extents govern length (0.30 max(L1, L2) continuous, 0.25 L1 non-continuous, from the face)",
         "SUPPORTING_EVIDENCE": ["p.15 defers size & spacing to the 'SCHEDULE OR PLAN': note 2 is the plan's only "
                                 "general top specification", "p.15 states span basis (CLEAR SPAN) and origin "
                                 "(face) explicitly; note 2 states neither"],
         "CONTRARY_EVIDENCE": ["note 2 states its own length ('one third of the span'): a floor-specific plan note "
                               "normally governs a typical detail where they differ",
                               "unresolved ends: p.15 does not say which extent applies at a level step, a "
                               "special slab beyond, or a non-beam support"],
         "STATE": "SUPPORTED_NOT_ESTABLISHED",
         "AUTHORITY": "NOT_ESTABLISHED (precedence between plan note and typical detail is not stated)"},
        {"READING_ID": "I-E", "SCENARIO": "E", "READING": "L/3 of the LARGER adjacent span, per side from the face",
         "SUPPORTING_EVIDENCE": ["p.15 continuous-support rule takes the larger span ('WHICHEVER LARGER'); p.15 "
                                 "temperature note 3 'WHERE TOP REINF. DIFFERS BETWEEN ADJACENT SPANS USE LAGER "
                                 "REINF.'"],
         "CONTRARY_EVIDENCE": ["note 2 names no larger span; the analogy is with the p.15 extent rule, not with "
                               "note 2 itself"],
         "STATE": "WEAK_NOT_ESTABLISHED", "AUTHORITY": "NOT_ESTABLISHED"},
        {"READING_ID": "I-F", "SCENARIO": None, "READING": "note 2 and the p.15 anchor bars are two SEPARATE top "
         "families (both placed)",
         "SUPPORTING_EVIDENCE": ["'يجب وضع' ('must be placed') reads as an instruction to provide steel, which "
                                 "could be in addition to the typical detail"],
         "CONTRARY_EVIDENCE": ["p.15 gives the anchor bars no size or spacing of their own - only 'SEE SCHEDULE OR "
                               "PLAN', and the plan's only top specification is note 2 itself",
                               "no plan or schedule names a second top family over beams"],
         "STATE": "NOT_SUPPORTED_UNQUANTIFIABLE",
         "AUTHORITY": "a second family would have no size / spacing source: it cannot be quantified (no kg)"}]


def family_identity(top_identity, rules):
    p15 = {r["rule_id"]: r for r in rules if r["rule_id"].startswith("P15-")}
    rows = []
    for t in top_identity:
        if t["RULE_B"] != NOTE2_RULE or not t["RULE_A"].startswith("P15-TOP"):
            continue
        rows.append({"RULE_A": t["RULE_A"], "RULE_B": NOTE2_RULE, "PRE_S7_1_IDENTITY": t["IDENTITY"],
                     "PRE_S7_1_GOVERNING": t["GOVERNING"], "PRE_S7_1_AUTHORITY": t["AUTHORITY"],
                     "SAME_FAMILY_EVIDENCE": json.loads(t["EVIDENCE"]),
                     "CONFLICTING_EVIDENCE": [
                         "length: note 2 'one third of the span' vs p.15 " +
                         {"P15-TOP-NONCONT-0.25L1": "0.25 L1 (non-continuous)",
                          "P15-TOP-CONT-0.30Lmax": "0.30 max(L1, L2) (continuous)",
                          "P15-TOP-EXTEND-50PCT": "50% into the adjacent slab 'WHERE POSSIBLE' (no length)"}[
                             t["RULE_A"]],
                         "precedence between a floor-specific plan note and a typical detail is not stated in "
                         "the drawings",
                         "note 2 wording 'يجب وضع' ('must be placed') could mean additional steel"],
                     "QA_STATE": "SAME_FAMILY_SUPPORTED_NOT_PROVEN",
                     "IF_SEPARATE_FAMILIES": "the p.15 family has no size / spacing of its own -> "
                                             "BLOCKED_UNQUANTIFIED (no kg); S7's note-2 kg unchanged",
                     "S7_EFFECT": "none: S7 counts one family (note 2) and never the p.15 extents"})
    t = p15.get("P15-TEMP-NOTES")
    rows.append({"RULE_A": "P15-TEMP-NOTES (note 2: TEMP. REINF. X 2000 TOP, at right angles to beams parallel to "
                           "main bars)", "RULE_B": NOTE2_RULE, "PRE_S7_1_IDENTITY": "NOT_RECORDED",
                 "PRE_S7_1_GOVERNING": "", "PRE_S7_1_AUTHORITY": "",
                 "SAME_FAMILY_EVIDENCE": ["both are top steel over beams"],
                 "CONFLICTING_EVIDENCE": ["role: temperature (shrinkage) steel where the beam is parallel to the "
                                          "main slab bars, not the main top steel over supports",
                                          "own size from the temperature table; own length (2000, 1000 at a "
                                          "spandrel)", f"raw: {t['raw_text'] if t else 'absent'}"],
                 "QA_STATE": "SEPARATE_FAMILY (temperature, excluded from S7)",
                 "IF_SEPARATE_FAMILIES": "temperature family stays excluded in S7 (S7 TEMPERATURE_EXCLUDED)",
                 "S7_EFFECT": "none (excluded); it is analogous evidence that a single top length over a beam is a "
                              "total length in this sheet set"})
    return rows


# ------------------------------------------------------------------ sensitivity geometry
BOUND = re.compile(r"^(?P<sup>.+?) \((?P<cls>END_[A-Z_]+)(?:; beyond: (?P<nb>\S+))?\)$")


def _bound(text):
    m = BOUND.match(text or "")
    check(m is not None, f"boundary text {text!r}")
    return m.group("sup"), m.group("cls"), m.group("nb")


def _lin(t0, t1, v0, v1):
    return lambda t: v0 + (v1 - v0) * ((t - t0) / (t1 - t0) if t1 > t0 else 0.0)


def _int_lin(f, a, b):
    return 0.5 * (f(a) + f(b)) * (b - a)


def _int_max(f, g, a, b):
    """Exact integral of max(f, g) over [a, b] for linear f, g."""
    ha, hb = f(a) - g(a), f(b) - g(b)
    if ha >= 0 and hb >= 0:
        return _int_lin(f, a, b)
    if ha <= 0 and hb <= 0:
        return _int_lin(g, a, b)
    c = a + (b - a) * ha / (ha - hb)
    return (_int_lin(f, a, c) if ha > 0 else _int_lin(g, a, c)) + (_int_lin(f, c, b) if hb > 0 else
                                                                     _int_lin(g, c, b))


def opposite_pieces(t0, t1, cands):
    """Split [t0, t1] by the opposite strips that face it: [(a, b, span_fn or None)], plus the ambiguity count."""
    cuts = sorted({t0, t1} | {x for c in cands for x in (c["t0"], c["t1"]) if t0 < x < t1})
    out, amb = [], 0
    for a, b in zip(cuts, cuts[1:]):
        if b - a <= 1e-9:
            continue
        m = 0.5 * (a + b)
        cov = [c for c in cands if c["t0"] - 1e-9 <= m <= c["t1"] + 1e-9]
        if len(cov) > 1:
            amb += 1
        out.append((a, b, cov[0]["fn"] if len(cov) == 1 else None, len(cov)))
    return out, amb


def extension_integrals(own, cls, pieces):
    """Integral over the strip width of the per-side extension length (mm x mm) for every scenario."""
    I = {k: 0.0 for k in SCENARIOS}
    unmatched = ambiguous = 0.0
    for a, b, fn, ncov in pieces:
        if fn is None:
            if ncov > 1:
                ambiguous += b - a
            else:
                unmatched += b - a
        lo = _int_lin(own, a, b)
        mx = _int_max(own, fn, a, b) if fn else lo
        sm = (lo + _int_lin(fn, a, b)) if fn else 2.0 * lo
        I["A"] += lo / 3.0
        I["B"] += lo / 6.0
        if cls in CONT:
            I["C"] += sm / 6.0
            I["D1"] += 0.30 * mx
            I["D2"] += 0.30 * mx
            I["E"] += mx / 3.0
        elif cls in NONCONT:
            I["C"] += lo / 6.0
            I["D1"] += 0.25 * lo
            I["D2"] += 0.25 * lo
            I["E"] += lo / 3.0
        elif cls in UNRES:
            I["C"] += (sm / 6.0) if fn else lo / 6.0
            I["D1"] += 0.25 * lo
            I["D2"] += 0.30 * mx
            I["E"] += mx / 3.0
        else:
            raise Stop(f"S7A STOP: top extension at end class {cls}")
    return I, unmatched, ambiguous


def sensitivity(runs, items, strips):
    by_item = {i["S7_ITEM_ID"]: i for i in items}
    idx = defaultdict(list)
    for s in strips:
        t = json.loads(s["TRANSVERSE_POSITION_MM"])
        L = json.loads(s["LOCAL_CLEAR_SPAN_MM"])
        idx[(s["PANEL"], s["BAR_DIRECTION"])].append(
            {"id": s["LOCAL_BAR_STRIP_ID"], "t0": t[0], "t1": t[1], "fn": _lin(t[0], t[1], L[0], L[1]),
             "nbs": (s["START_NEIGHBOUR"], s["END_NEIGHBOUR"])})
    rows, amb_total = [], 0
    for r in runs:
        if r["BAR_ROLE"] != TE_ROLE:
            continue
        it = by_item[r["S7_ITEM_ID"]]
        sid = it["SUPPORT_ID"]
        sup, cls, nb = _bound(r["END_BOUNDARY"] if r["END_USED"] == "END" else r["START_BOUNDARY"])
        check(sup == sid, f"top run {r['BAR_RUN_ROW_ID']} meets its own support")
        t = json.loads(r["TRANSVERSE_POSITION_MM"])
        L = json.loads(r["LOCAL_CLEAR_SPAN_MM"])
        own = _lin(t[0], t[1], L[0], L[1])
        cands = [c for c in idx.get((nb, r["DIRECTION"]), []) if r["PANEL_ID"] in c["nbs"] and
                 c["t1"] > t[0] + 1e-9 and c["t0"] < t[1] - 1e-9] if nb else []
        pieces, amb = opposite_pieces(t[0], t[1], cands)
        amb_total += amb
        I, unmatched, ambiguous = extension_integrals(own, cls, pieces)
        rate, frac, um = float(it["RATE_PER_M"]), float(it["DENSITY_FRACTION"]), float(it["UNIT_MASS_KG_M"])
        frozen = float(r["KG"])
        recomputed = rate * frac * (I["A"] * 1e-6) * um
        # the CSV keeps transverse positions to 0.001 mm; S7 computed at full precision -> 1e-4 relative here
        check(abs(recomputed - frozen) <= 1e-4 * frozen, f"reading A recomputes S7 {r['BAR_RUN_ROW_ID']}")
        kg = {k: frozen * I[k] / I["A"] for k in SCENARIOS}       # scaled from the frozen kg: A is exact
        width = t[1] - t[0]
        matched = width - unmatched - ambiguous
        opp_mean = (sum(_int_lin(fn, a, b) for a, b, fn, _ in pieces if fn) / matched) if matched > 1e-9 else None
        rows.append({"BAR_RUN_ROW_ID": r["BAR_RUN_ROW_ID"], "S7_ITEM_ID": r["S7_ITEM_ID"], "FLOOR": r["FLOOR"],
                     "SUPPORT_ID": sid, "PANEL_ID": r["PANEL_ID"], "DIRECTION": r["DIRECTION"],
                     "STRIP_ID": r["STRIP_ID"], "END_CLASS": cls, "BEYOND_PANEL": nb, "STRIP_WIDTH_MM": width,
                     "OWN_CLEAR_SPAN_MEAN_MM": 0.5 * (L[0] + L[1]),
                     "OPPOSITE_CLEAR_SPAN_MEAN_MM": opp_mean, "OPPOSITE_MATCHED_WIDTH_MM": matched,
                     "OPPOSITE_UNMATCHED_WIDTH_MM": unmatched, "OPPOSITE_AMBIGUOUS_WIDTH_MM": ambiguous,
                     "OPPOSITE_STRIPS": sorted(c["id"] for c in cands),
                     **{f"KG_{k}": kg[k] for k in SCENARIOS}, "S7_FROZEN_KG": frozen,
                     "RECOMPUTED_A_REL_DEVIATION": (recomputed - frozen) / frozen})
    return rows, amb_total


def scenario_tables(rows, s7tot):
    te_frozen = math.fsum(r["S7_FROZEN_KG"] for r in rows)
    tx = s7tot["TOP_SUPPORT_CROSSING_KG"]
    total = s7tot[S7_TOTAL_KEY]
    scen = []
    for k in SCENARIOS:
        te = math.fsum(r[f"KG_{k}"] for r in rows)
        scen.append({"SCENARIO": k, "DEFINITION": SCENARIO_TEXT[k], "TOP_EXTENSION_KG": te,
                     "TOP_SUPPORT_CROSSING_KG": tx, "TOP_SUPPORT_KG": te + tx,
                     "DELTA_TOP_VS_S7_KG": te - te_frozen, "DELTA_TOP_VS_S7_PCT": 100.0 * (te - te_frozen) /
                     te_frozen, "S7_SCOPE_TOTAL_UNDER_SCENARIO_KG": total - te_frozen + te,
                     "S7_FROZEN_TOTAL_KG": total, "STATE": "SENSITIVITY_ONLY" if k != "A" else
                     "S7_FROZEN_REPRODUCED", "RELEASED": False,
                     "SAME_POPULATION": "the S7-released top-extension strip ends only; blocked top items stay "
                                        "blocked; bottom steel and crossings unchanged"})
    by = defaultdict(list)
    for r in rows:
        by[r["END_CLASS"]].append(r)
    cls_rows = []
    for c in sorted(by):
        rs = by[c]
        cls_rows.append({"END_CLASS": c, "STRIP_ENDS": len(rs),
                         "SUPPORTS": len({r["SUPPORT_ID"] for r in rs}),
                         "OPPOSITE_MATCHED_SHARE": math.fsum(r["OPPOSITE_MATCHED_WIDTH_MM"] for r in rs) /
                         math.fsum(r["STRIP_WIDTH_MM"] for r in rs),
                         **{f"KG_{k}": math.fsum(r[f"KG_{k}"] for r in rs) for k in SCENARIOS}})
    return scen, cls_rows, te_frozen


# ------------------------------------------------------------------ bottom rules and end-condition audit
def support_kinds(sups):
    return {s["SUPPORT_ID"]: s["SUPPORT_KIND"] for s in sups}


def unresolved_reason(pid, nb, census, kind):
    if kind and kind != "BEAM":
        return f"NON_BEAM_SUPPORT ({kind})"
    c = census.get(nb)
    if not c:
        return "NO_PANEL_BEYOND_RECORD"
    if c["SCOPE"] == "IN_SCOPE_S7":
        sp, sn = census[pid]["PANEL_CLASS"] == "SUNKEN_SLAB", c["PANEL_CLASS"] == "SUNKEN_SLAB"
        return "LEVEL_STEP (sunken on one side only)" if sp != sn else "UNRESOLVED_OTHER"
    return f"SPECIAL_OR_BLOCKED_SLAB_BEYOND ({c['PANEL_CLASS']})"


BOTTOM_TABLE = {
    "END_CONTINUOUS_RUN": ("BEAM, slab both sides at one level, same bottom specification", "SOURCE_APPLIES",
                           "p.15 CONTINUOUS SUPPORT: STOP 50% OF BOT. REINF. 0.125 L from the face; BALANCE "
                           "CONTINUOUS", "50/50 split; the curtailed half stops 0.125 L short of the face; the "
                           "continuing half crosses (owned by the support, once)", "none (rule applies as drawn)"),
    "END_CONTINUOUS_SPLIT": ("BEAM, slab both sides at one level, bottom specification differs or unresolved",
                             "SOURCE_APPLIES_IN_PANEL; CROSSING_NOT_ESTABLISHED",
                             "p.15 CONTINUOUS SUPPORT (the detail draws one specification each side)",
                             "50/50 split and the 0.125 L stop in each panel; the continuation across the "
                             "support (lap / splice / which bar continues) is blocked as TRANSITION",
                             "if both halves stop at the face (no continuity of a differing bar), the in-panel "
                             "kg is unchanged; only the blocked transition is affected"),
    "END_NON_CONTINUOUS": ("BEAM, no slab beyond (edge, court, void)", "SOURCE_APPLIES (no stop)",
                           "p.15 NON CONTINUOUS SUPPORT: bottom bars run into the support; no 50% stop drawn",
                           "full density to the face; the end anchorage into the support is blocked (shape only)",
                           "none"),
    "END_UNRESOLVED": ("BEAM with a level step, a special / blocked slab beyond, or a non-beam support",
                       "INFERRED (the detail is 'slab on beams' at one level)",
                       "p.15 does not draw a stepped, special-beyond or wall-supported case",
                       "the curtailed half is shortened by 0.125 L as if continuous; the stop zone (present only "
                       "if NON-continuous) is blocked, not zero", "if the end is actually non-continuous, the "
                       "curtailed half runs to the face: + the deduction shown (S7 reads less there)"),
    "END_OBLIQUE": ("support met at an angle (bar does not cross it squarely)", "INFERRED",
                    "p.15 draws square crossings only", "as END_UNRESOLVED (0.125 L deducted, stop zone blocked)",
                    "as END_UNRESOLVED"),
    "END_NO_SUPPORT_RECORD": ("boundary edge with no support record", "INFERRED", "no detail",
                              "as END_UNRESOLVED (0.125 L deducted, stop zone blocked)", "as END_UNRESOLVED"),
    "END_OPENING": ("opening / hole boundary", "NOT_DRAWN (no trim detail)", "no opening detail on p.15",
                    "full density to the opening edge; trim and diagonal bars blocked", "none for the mesh")}


def bottom_table(runs, items):
    by_item = {i["S7_ITEM_ID"]: i for i in items}
    agg = defaultdict(lambda: {"ends": 0, "deduction_kg": 0.0, "rows": 0, "panels": set()})
    for r in runs:
        if r["BAR_ROLE"] not in ("BOTTOM_CURTAILED_50", "BOTTOM_CONTINUING_50", "BOTTOM_IN_PANEL"):
            continue
        it = by_item[r["S7_ITEM_ID"]]
        rate, frac, um = float(it["RATE_PER_M"]), float(it["DENSITY_FRACTION"]), float(it["UNIT_MASS_KG_M"])
        width = float(r["STRIP_WIDTH_MM"]) * 1e-3
        base = float(r["BASE_RUN_MM"]) * 1e-3
        for b in (r["START_BOUNDARY"], r["END_BOUNDARY"]):
            _, cls, _nb = _bound(b)
            a = agg[(r["BAR_ROLE"], cls)]
            a["ends"] += 1
            a["rows"] += 1
            a["panels"].add(r["PANEL_ID"])
            if r["BAR_ROLE"] == "BOTTOM_CURTAILED_50" and cls in ("END_CONTINUOUS_RUN", "END_CONTINUOUS_SPLIT",
                                                                   "END_UNRESOLVED", "END_OBLIQUE",
                                                                   "END_NO_SUPPORT_RECORD"):
                a["deduction_kg"] += rate * frac * width * 0.125 * base * um
    out = []
    for cls, (stype, appl, p15, s7, alt) in BOTTOM_TABLE.items():
        cur = agg.get(("BOTTOM_CURTAILED_50", cls), {"ends": 0, "deduction_kg": 0.0, "panels": set()})
        cont = agg.get(("BOTTOM_CONTINUING_50", cls), {"ends": 0, "panels": set()})
        full = agg.get(("BOTTOM_IN_PANEL", cls), {"ends": 0, "panels": set()})
        out.append({"END_CLASS": cls, "SUPPORT_TYPE": stype, "P15_RULE": p15, "APPLICABILITY": appl,
                    "S7_TREATMENT": s7, "CURTAILED_HALF_STRIP_ENDS": cur["ends"],
                    "CONTINUING_HALF_STRIP_ENDS": cont["ends"], "FULL_DENSITY_STRIP_ENDS": full["ends"],
                    "PANELS": len(cur["panels"] | cont["panels"] | full["panels"]),
                    "S7_STOP_DEDUCTION_KG": cur["deduction_kg"] if cls not in ("END_NON_CONTINUOUS",
                                                                                "END_OPENING") else 0.0,
                    "ALTERNATIVE": alt,
                    "QA_FLAG": "INFERRED_CONTINUITY" if appl.startswith("INFERRED") else
                    ("CROSSING_BLOCKED" if "NOT_ESTABLISHED" in appl else "")})
    return out


def grade(cls, src):
    if cls in ("END_UNRESOLVED", "END_OBLIQUE", "END_NO_SUPPORT_RECORD"):
        return "NOT_ESTABLISHED"
    if cls == "END_OPENING":
        return "ESTABLISHED_OPENING"
    if src == "GEOMETRY":
        return "ESTABLISHED_BY_GEOMETRY"
    if src.startswith("GEOMETRY (neighbour; S1 named another"):
        return "INFERRED_GEOMETRY_OVERRIDES_S1"
    if src.startswith("S1_EDGE"):
        return "INFERRED_FROM_S1_EDGE_ONLY"
    return "INFERRED_OTHER"


def end_audit(strips, runs, items, census, kinds, conflicts):
    by_item = {i["S7_ITEM_ID"]: i for i in items}
    te = defaultdict(float)
    ded = defaultdict(float)
    for r in runs:
        it = by_item[r["S7_ITEM_ID"]]
        rate, frac, um = float(it["RATE_PER_M"]), float(it["DENSITY_FRACTION"]), float(it["UNIT_MASS_KG_M"])
        if r["BAR_ROLE"] == TE_ROLE:
            te[(r["STRIP_ID"], 1 if r["END_USED"] == "END" else 0)] += float(r["KG"])
        elif r["BAR_ROLE"] == "BOTTOM_CURTAILED_50":
            for k, b in enumerate((r["START_BOUNDARY"], r["END_BOUNDARY"])):
                if _bound(b)[1] in ("END_CONTINUOUS_RUN", "END_CONTINUOUS_SPLIT", "END_UNRESOLVED", "END_OBLIQUE",
                                    "END_NO_SUPPORT_RECORD"):
                    ded[(r["STRIP_ID"], k)] += rate * frac * float(r["STRIP_WIDTH_MM"]) * 1e-3 * 0.125 * \
                        float(r["BASE_RUN_MM"]) * 1e-3 * um
    gsup = {c["WHERE"]: c["PRE_S7_CONFLICT_ID"] for c in conflicts if c["PRE_S7_CONFLICT_ID"].startswith("G-")}
    out = []
    for s in strips:
        src = json.loads(s["NEIGHBOUR_SOURCE"])
        for k, (sup, nb, cond) in enumerate(((s["START_SUPPORT"], s["START_NEIGHBOUR"], s["START_CONDITION"]),
                                             (s["END_SUPPORT"], s["END_NEIGHBOUR"], s["END_CONDITION"]))):
            g = grade(cond, src[k])
            kind = kinds.get(sup) if sup else None
            why = unresolved_reason(s["PANEL"], nb, census, kind) if cond == "END_UNRESOLVED" else ""
            same_level = ""
            if cond in CONT:
                same_level = "INFERRED_FROM_PANEL_CLASS (no per-panel level text; sunken hatch legend only)"
            out.append({"STRIP_ID": s["LOCAL_BAR_STRIP_ID"], "END": ("START", "END")[k], "PANEL": s["PANEL"],
                        "FLOOR": s["FLOOR"], "DIRECTION": s["BAR_DIRECTION"], "SUPPORT_ID": sup,
                        "SUPPORT_KIND": kind, "BEYOND_PANEL": nb, "END_CLASS": cond, "NEIGHBOUR_SOURCE": src[k],
                        "CONTINUITY_GRADE": g, "UNRESOLVED_REASON": why, "SAME_LEVEL_BASIS": same_level,
                        "TOPOLOGY_CORRECTION": gsup.get(sup, ""),
                        "S7_TOP_EXTENSION_KG_AT_END": te.get((s["LOCAL_BAR_STRIP_ID"], k), 0.0),
                        "S7_BOTTOM_STOP_DEDUCTION_KG_AT_END": ded.get((s["LOCAL_BAR_STRIP_ID"], k), 0.0),
                        "QA_FLAG": "" if g.startswith("ESTABLISHED") else "CONTINUITY_INFERRED_OR_UNRESOLVED"})
    return out


# ------------------------------------------------------------------ errata
def errata(items, readme_text, scen):
    rows = [i["S7_ITEM_ID"] for i in items if LOWER_BOUND_WORDING in i["QUANTITY_AUTHORITY"]]
    lo = min(s["TOP_EXTENSION_KG"] for s in scen)
    hi = max(s["TOP_EXTENSION_KG"] for s in scen)
    a = next(s for s in scen if s["SCENARIO"] == "A")
    return {"id": "S7A-E01", "date": QA_DATE, "round": ROUND, "baseline": BASELINE_HEAD,
            "applies_to": "research/alsenan_slab_rebar_s7 (frozen; not edited)",
            "withdrawn_wording": LOWER_BOUND_WORDING,
            "where": {"01_S7_RELEASE_ITEMS.csv QUANTITY_AUTHORITY": {"rows": len(rows),
                                                                      "first": rows[0], "last": rows[-1]},
                      "00_README.md": "no lower-bound claim" if "lower bound" not in readme_text else
                      "lower-bound claim present", "post_freeze": POST_FREEZE_CLAIMS},
            "why": ["the one-third top extent is not established by the source (01_TOP_EXTENT_INTERPRETATIONS.csv): "
                    f"over the same released strip ends the top extension ranges {_full(lo)} to {_full(hi)} kg "
                    f"across the readings, against S7's {_full(a['TOP_EXTENSION_KG'])} kg - several readings give "
                    "LESS steel than S7, so S7 is not below the physical steel by construction",
                    "the continuity of many strip ends is inferred, not established (08_END_CONDITION_AUDIT.csv)",
                    "the equivalent (unrounded) count and the nominal D^2/162 unit mass are QTO conventions, not "
                    "physical bar counts or rolled masses",
                    "excluding every blocked portion makes S7 a RESTRICTED quantity of the released items, not a "
                    "proven bound of the whole physical slab steel"],
            "replacement_wording": "PROJECT_BASIS_QTO: rate density over the frozen PRE-S7.1 local bar strips under "
                                   "the recorded interpretation (AD2-D06 / S7-AC01 / S7-AC02); every blocked "
                                   "portion is excluded (not zero); not a proven bound of the physical steel in "
                                   "either direction; not a bar-by-bar BBS",
            "kg_change": 0.0, "s7_total_kg": a["S7_FROZEN_TOTAL_KG"], "s7_total_unchanged": True,
            "s7_files_edited": False,
            "rule": "S7 stays frozen and byte-identical; this dated record supersedes the wording only. A future "
                    "release that changes a quantity needs its own correction layer, evidence and version."}


# ------------------------------------------------------------------ build / write
def build():
    import ezdxf
    frozen = verify_inputs()
    doc = ezdxf.readfile(str(DXF))
    ev = {"note2": note2_dxf(doc), "span_word": span_word_occurrences(doc),
          "beam_schedule": beam_schedule_fraction_dims(doc), "p15_strokes": p15_strokes()}
    vis = _j(PRE / "source_search_inputs" / "PRE_S7_VISUAL_READING.json")
    check(vis["pdf_sha256"] == PDF_SHA, "visual reading is of the issued PDF")
    ev["p15_visual_reading_frozen"] = {"source": "PRE-S7 PRE_S7_VISUAL_READING.json (renders kept as hashes)",
                                       "renders_sha256": {k: v for k, v in vis["renders_sha256"].items()
                                                          if k.startswith("p15")},
                                       **vis["p15_slab_on_beams_detail"]}
    rules = _j(S1 / "STRUCTURAL_PROJECT_RULE_REGISTER.json")["rows"]
    rmap = {r["rule_id"]: r for r in rules}
    ev["rule_records"] = {k: {"raw_text": rmap[k]["raw_text"], "normalized_rule": rmap[k]["normalized_rule"],
                              "status": rmap[k]["status"], "page": rmap[k]["page"]}
                          for k in ("P4-6-NOTE-2", "P15-SLAB-ON-BEAMS", "P15-TEMP-NOTES")}
    ev["span_word_homonym"] = all(any("SEA VIEW" in x for x in o["siblings_in_block"]) for o in ev["span_word"]
                                  if o["space"] != "MODEL")
    ev["finding"] = {
        "one_third_extent": "NOT_ESTABLISHED_BY_SOURCE",
        "ratio_one_third": "PROJECT_SOURCE (note 2)",
        "span_basis": "NOT_STATED in note 2 (p.15 states CLEAR SPAN for its own extents)",
        "origin": "NOT_STATED in note 2 (p.15 measures from the support face)",
        "total_vs_per_side": "NOT_STATED in note 2; literal wording ('with a length of') favours a TOTAL length; "
                             "p.15 geometry and the beam-schedule convention favour PER SIDE",
        "unequal_spans": "NOT_STATED in note 2 (p.15 uses the larger span at a continuous support)",
        "same_family_as_p15": "SUPPORTED_NOT_PROVEN (p.15 defers size / spacing to the plan; lengths conflict)",
        "s7_reading": "A - URBAN_OWNER_MEASUREMENT_RULE (AD2-D06), retained for the frozen S7 baseline; not "
                      "re-selected here and not replaced"}
    interp = interpretations(ev)
    top_identity = _rows(P71 / "05_TOP_RULE_IDENTITY.csv")
    fam = family_identity(top_identity, rules)
    runs = _rows(S7P / "04_S7_BAR_RUNS.csv")
    items = _rows(S7P / "01_S7_RELEASE_ITEMS.csv")
    strips = _rows(P71 / "07_LOCAL_BAR_STRIPS.csv")
    s7sum = _j(S7P / "09_S7_PROJECT_SUMMARY.json")
    s7tot = s7sum["totals_kg"]
    sens, amb = sensitivity(runs, items, strips)
    scen, cls_rows, te_frozen = scenario_tables(sens, s7tot)
    check(abs(te_frozen - s7tot["TOP_EXTENSION_KG"]) <= 1e-9 * te_frozen, "top extension reconciles to S7")
    census = {c["SLAB_PANEL_ID"]: c for c in _rows(PRE / "01_SLAB_PANEL_CENSUS.csv")}
    kinds = support_kinds(_rows(PRE / "05_SUPPORT_REGISTER.csv"))
    conflicts = _rows(P71 / "09_REMAINING_CONFLICTS.csv")
    btab = bottom_table(runs, items)
    audit = end_audit(strips, runs, items, census, kinds, conflicts)
    ded_total = math.fsum(r["S7_BOTTOM_STOP_DEDUCTION_KG_AT_END"] for r in audit)
    check(abs(ded_total - math.fsum(b["S7_STOP_DEDUCTION_KG"] for b in btab)) <= 1e-6,
          "bottom stop deductions reconcile between the audit and the support-type table")
    te_audit = math.fsum(r["S7_TOP_EXTENSION_KG_AT_END"] for r in audit)
    check(abs(te_audit - te_frozen) <= 1e-6, "every S7 top extension sits on one audited strip end")
    err = errata(items, (S7P / "00_README.md").read_text(encoding="utf-8"), scen)
    return {"frozen": frozen, "ev": ev, "interp": interp, "fam": fam, "sens": sens, "amb": amb, "scen": scen,
            "cls_rows": cls_rows, "btab": btab, "audit": audit, "err": err, "s7tot": s7tot,
            "blocked": _rows(S7P / "02_S7_BLOCKED_ITEMS.csv")}


def summarise(B):
    g = Counter(r["CONTINUITY_GRADE"] for r in B["audit"])
    gkg = defaultdict(lambda: [0.0, 0.0])
    for r in B["audit"]:
        gkg[r["CONTINUITY_GRADE"]][0] += r["S7_TOP_EXTENSION_KG_AT_END"]
        gkg[r["CONTINUITY_GRADE"]][1] += r["S7_BOTTOM_STOP_DEDUCTION_KG_AT_END"]
    blocked_top = Counter(b["ITEM"] for b in B["blocked"] if b["ITEM"].startswith("TOP"))
    scen = {s["SCENARIO"]: {"top_extension_kg": round(s["TOP_EXTENSION_KG"], 3),
                            "top_support_kg": round(s["TOP_SUPPORT_KG"], 3),
                            "delta_top_vs_s7_kg": round(s["DELTA_TOP_VS_S7_KG"], 3),
                            "delta_top_vs_s7_pct": round(s["DELTA_TOP_VS_S7_PCT"], 2),
                            "s7_scope_total_under_scenario_kg": round(s["S7_SCOPE_TOTAL_UNDER_SCENARIO_KG"], 3)}
            for s in B["scen"]}
    return {"round": ROUND, "date": QA_DATE, "policy": POLICY, "baseline": BASELINE_HEAD,
            "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
            "frozen_baselines": {k: v["manifest_sha256"] for k, v in B["frozen"].items()},
            "s7_frozen_total_kg": B["s7tot"][S7_TOTAL_KEY], "s7_total_unchanged": True, "s7_files_edited": False,
            "finding": B["ev"]["finding"], "scenarios": scen,
            "scenario_range_top_extension_kg": [round(min(s["TOP_EXTENSION_KG"] for s in B["scen"]), 3),
                                                round(max(s["TOP_EXTENSION_KG"] for s in B["scen"]), 3)],
            "top_extension_strip_ends": len(B["sens"]), "opposite_ambiguous_pieces": B["amb"],
            "by_end_class": {r["END_CLASS"]: {"strip_ends": r["STRIP_ENDS"],
                                              "opposite_matched_share": round(r["OPPOSITE_MATCHED_SHARE"], 4)}
                             for r in B["cls_rows"]},
            "end_condition_grades": dict(sorted(g.items())),
            "end_condition_kg": {k: {"s7_top_extension_kg": round(v[0], 3), "s7_bottom_stop_deduction_kg":
                                     round(v[1], 3)} for k, v in sorted(gkg.items())},
            "blocked_top_items_unchanged": dict(sorted(blocked_top.items())),
            "errata": {"id": B["err"]["id"], "rows": B["err"]["where"]["01_S7_RELEASE_ITEMS.csv QUANTITY_AUTHORITY"][
                "rows"], "kg_change": 0.0},
            "released": False, "state": "SENSITIVITY_ONLY_NO_RELEASE",
            "references_read": [], "interpretation_selected_by_reference": False}


def readme(B, s):
    sc = {x["SCENARIO"]: x for x in B["scen"]}

    def k(x):
        return f"{x:,.1f}"
    lines = [
        "# S7A: dated engineering QA of the S7 slab release (2026-10-08)",
        "",
        "S7 stays frozen and byte-identical. Its **RESTRICTED_S7_PROJECT_BASIS_KG = "
        f"{B['s7tot'][S7_TOTAL_KEY]:,.3f} kg** is unchanged.",
        "",
        "This layer re-reads the sources for the top-over-support rule. It quantifies the alternative readings as "
        "SENSITIVITY_ONLY, tabulates the bottom rules by support type, and grades every strip end's continuity. It "
        "also withdraws one S7 wording (errata S7A-E01). Nothing is released.",
        "",
        "## Source finding (01, 02, 03)",
        "",
        "- **Plan note 2** (ST7757.dxf handles D8/D9/DA, E1/E2/E3, EA/EB/EC):",
        "  - text: «يجب وضع حديد علوي 5Ø10/m للبلاطات فوق الجسور بطول ثلث البحر في الاتجاهين»;",
        "  - meaning: top steel 5Ø10/m for the slabs over the beams, *with a length of* one third of the span, *in "
        "the two directions*.",
        "  - It states the ratio (1/3) but no span basis, no origin, no total-versus-per-side and no rule for unequal "
        "spans.",
        "  - The only other «البحر» in the drawing is a SEA VIEW site marker (the same word means \"the sea\").",
        "- **p.15 TYP. SLAB ON BEAMS** (vector strokes, not to scale):",
        "  - At the continuous support, one top bar crosses the beam and runs into both spans, measured from each "
        "face.",
        "  - At the non-continuous support, the anchor bar runs into L1 and turns down.",
        "  - The extents are per side, from the face: 0.30 max(L1, L2) and 0.25 L1.",
        "  - Size and spacing are deferred to the \"SCHEDULE OR PLAN\".",
        "- **Continuous-beam schedule:** fraction-of-Ln dimensions sit on each side of a support, each against its "
        "own span. This is the per-side convention, but for beams: analogous evidence only.",
        "- **p.15 temperature note 2** gives top-over-beam steel as one total length (X 2000; 1000 at a spandrel). "
        "This is analogous evidence for a total-length reading.",
        "- **Result:** the one-third extent is NOT ESTABLISHED by the source.",
        "  - Reading A (S7) is an owner measurement convention (AD2-D06). Its supporting and contrary evidence are "
        "kept beside the other readings.",
        "  - The note-2 / p.15 identity is SAME_FAMILY_SUPPORTED_NOT_PROVEN.",
        "  - A separate p.15 family would have no size or spacing source, so it could not be quantified.",
        "",
        "## Top-steel sensitivity on the S7-released strip ends (04, 05, 06)",
        "",
        "| scenario | top extension kg | top incl. crossings kg | vs S7 | S7-scope total under it kg |",
        "|---|---|---|---|---|"]
    for x in SCENARIOS:
        r = sc[x]
        lines.append(f"| {x} | {k(r['TOP_EXTENSION_KG'])} | {k(r['TOP_SUPPORT_KG'])} | "
                     f"{r['DELTA_TOP_VS_S7_PCT']:+.1f} % | {k(r['S7_SCOPE_TOTAL_UNDER_SCENARIO_KG'])} |")
    lines += [
        "",
        "How the scenarios are computed:",
        "",
        "- Each one changes only the top-extension length per strip end. Bottom steel, the crossings over beams and "
        "every blocked item are as frozen.",
        "- The opposite-side clear span (for C, D and E) comes from the frozen PRE-S7.1 strips of the panel beyond, "
        "matched along the bar line.",
        "- Where no strip faces the end, the own span is used. That width is reported per row.",
        "- Reading A reproduces S7's kg row by row.",
        "",
        "The definitions are in 04_TOP_SENSITIVITY_SCENARIOS.csv. No scenario is selected, and none is a release.",
        "",
        "## Bottom rules by support type (07) and end-condition audit (08)",
        "",
        "- The p.15 50/50 split with the 0.125 L stop is drawn only for a slab on beams at one level.",
        "- At unresolved, oblique and unrecorded ends, S7 applied the stop as if the end were continuous, and "
        "blocked the stop zone.",
        "- Strip-end grades:"]
    for g, n in s["end_condition_grades"].items():
        lines.append(f"  - {g}: {n} strip ends; S7 top extension "
                     f"{s['end_condition_kg'][g]['s7_top_extension_kg']:,.1f} kg; bottom stop deduction "
                     f"{s['end_condition_kg'][g]['s7_bottom_stop_deduction_kg']:,.1f} kg.")
    lines += [
        "- Same-level continuity across a beam is inferred from the panel classes (sunken hatch). No per-panel level "
        "text was found.",
        "",
        "## Errata S7A-E01 (09)",
        "",
        f"S7's {s['errata']['rows']} release items say QUANTITY_AUTHORITY \"{LOWER_BOUND_WORDING}\". The post-freeze "
        "write-up also calls the total a \"restricted lower bound\". Both are withdrawn.",
        "",
        "- Why: the top extent is not established, several readings give less steel than S7, and many continuities "
        "are inferred.",
        "- Replacement: S7 is a PROJECT_BASIS_QTO under the recorded interpretation. It is not a proven bound of the "
        "physical steel in either direction.",
        "- The kg change is 0, and no S7 file is edited.",
        "",
        "## Reproduce",
        "",
        "```",
        "python3 -I research/alsenan_slab_rebar_s7a_qa/build_s7a_qa.py",
        "```",
        "",
        "The build is byte-identical on rebuild. It reads no external reference or earlier estimate.",
        ""]
    return "\n".join(lines)


def write(B):
    interp_f = ["READING_ID", "SCENARIO", "READING", "SUPPORTING_EVIDENCE", "CONTRARY_EVIDENCE", "STATE",
                "AUTHORITY"]
    _csv("01_TOP_EXTENT_INTERPRETATIONS.csv", B["interp"], interp_f)
    _json("02_SOURCE_EVIDENCE.json", B["ev"])
    _csv("03_BAR_FAMILY_IDENTITY_QA.csv", B["fam"], list(B["fam"][0]))
    _csv("04_TOP_SENSITIVITY_SCENARIOS.csv", B["scen"], list(B["scen"][0]))
    _csv("05_TOP_SENSITIVITY_BY_END_CLASS.csv", B["cls_rows"], list(B["cls_rows"][0]))
    _csv("06_TOP_SENSITIVITY_BY_STRIP_END.csv", B["sens"], list(B["sens"][0]))
    _csv("07_BOTTOM_RULE_SUPPORT_TYPE_TABLE.csv", B["btab"], list(B["btab"][0]))
    _csv("08_END_CONDITION_AUDIT.csv", B["audit"], list(B["audit"][0]))
    _json("09_S7_ERRATA.json", B["err"])
    s = summarise(B)
    _json("10_S7A_SUMMARY.json", s)
    (HERE / "00_README.md").write_text(readme(B, s), encoding="utf-8")
    return s


def main():
    B = build()
    s = write(B)
    man = {"round": ROUND, "date": QA_DATE, "state": "FROZEN_QA_LAYER_NO_RELEASE", "references_read": [],
           "baseline": BASELINE_HEAD, "engine_commit_stamp": s["engine_commit"],
           "rule": "S7A changes no S7 file and no S7 quantity; scenario figures are sensitivity only; a quantity "
                   "change needs a new dated correction layer with its own evidence",
           "code": {c: _sha(ROOT / c) for c in CODE}, "inputs": {i: _sha(ROOT / i) for i in INPUTS},
           "drawing_sha256": {"ST7757.dxf": DXF_SHA, "ST7757.pdf": PDF_SHA},
           "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
           "frozen_baselines": s["frozen_baselines"], "s7_total_kg": _full(s["s7_frozen_total_kg"])}
    _json(MANIFEST_NAME, man)
    print(json.dumps({k: s[k] for k in ("scenarios", "scenario_range_top_extension_kg", "by_end_class",
                                        "end_condition_grades", "end_condition_kg", "opposite_ambiguous_pieces",
                                        "errata")}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
