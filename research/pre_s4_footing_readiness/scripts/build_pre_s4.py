"""PRE-S4 FOOTING REBAR READINESS - build the research / readiness package (no kg, no S4).

    python3 -I research/pre_s4_footing_readiness/scripts/build_pre_s4.py <ST7757.dxf>

Reads, read-only:
  * ST7757.dxf (sha256-checked): the Schedule of Footings grid, header texts, FT / FTB inserts and their ATTRIBs,
    the FT / FTB block definitions (ATTDEF defaults, glyph texts), and the REMARKS column;
  * the frozen S1 registers (FOOTING_DEFINITION / OCCURRENCE): plan tags, outlines and the F / F10 conflict;
  * the frozen R4 visual capture (VISUAL_EVIDENCE_CAPTURE.json): crop hashes and OCR of the p.8 / p.13 / p.14
    details. The page-level observations of this round (PDF_ITEMS) cite page, crop and crop hash.
Writes 01 / 02 / 03 / 06 (csv), PRE_S4_SUMMARY.json and INDEX.json. Deterministic: two runs give identical bytes.
Uses the production guard (engine.source.footing_rebar_guard) and schedule_table reader unchanged; nothing here
writes to a production register.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import footing_rebar_guard as FG  # noqa: E402
from engine.source import schedule_grammar as SG  # noqa: E402
from engine.source import schedule_table as ST  # noqa: E402
from engine.source import slab_rebar_binding as SRB  # noqa: E402
from engine.source import structural_schedule as SS  # noqa: E402

DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
BASELINE = "445dd1d"
ROUND = "PRE_S4_HARDENING"
S1 = ROOT / "research/alsenan_structural_census_s1"
R4_CAPTURE = ROOT / "research/alsenan_rebar_source_exhaustion_04/evidence/VISUAL_EVIDENCE_CAPTURE.json"
TABLE_BOX = (138300.0, 155200.0, -5600.0, 8500.0)       # Schedule of Footings, model space (raw DXF units, mm)
GRID_LAYER = "S-LINE.SCH"
DOUBLE_LINE_EPS = 60.0                                   # the schedule is drawn with double rules 45.7 mm apart
PLACE_EPS = 10.0
COVER_CM = 7.0                                           # p.8 note 22 (soil-contact concrete); used in diagnostics

# adapter fixed table (research/external_engine_lab/alsenan_structural_source_v2.py): ATTRIB tag -> header label
FIXED_FT = {"FO-TY": "TYPE OF FOOT.", "W": "L", "H": "W", "DEPHT": "H", "SH-B": "SHORT BARS", "SH-D": "SHORT BARS",
            "LO-B": "LONG BARS", "LO-D": "LONG BARS", "BOXED": "BOXED"}
FIXED_FTB_TOP = {"FO-TY": "TYPE OF FOOT.", "W": "L", "H": "W", "DEPHT": "H", "SH-T-B": "SHORT BARS",
                 "SH-T-D": "SHORT BARS", "LO-T-B": "LONG BARS", "LO-T-D": "LONG BARS", "BOXED-T": "BOXED"}
FIXED_FTB_BOT = {"SH-B-B": "SHORT BARS", "SH-B-D": "SHORT BARS", "LO-B-B": "LONG BARS", "LO-B-D": "LONG BARS",
                 "BOXED-B": "BOXED"}
PAIRS_FT = (("SHORT", "SH-B", "SH-D", "BOTTOM_SHORT"), ("LONG", "LO-B", "LO-D", "BOTTOM_LONG"))
PAIRS_FTB = (("TOP_SHORT", "SH-T-B", "SH-T-D", "TOP_SHORT"), ("TOP_LONG", "LO-T-B", "LO-T-D", "TOP_LONG"),
             ("BOTTOM_SHORT", "SH-B-B", "SH-B-D", "BOTTOM_SHORT"), ("BOTTOM_LONG", "LO-B-B", "LO-B-D", "BOTTOM_LONG"))

# OQ-11 (V3C donor audit, an owner question): "F3 is tagged twice on the foundation plan; is that right?" It is a
# question only. No external count is carried into any register here.
COUNT_QUERIES = {"F3": "OQ-11"}

# page-level observations of the PDF-only sheets (p.8 notes, p.13 / p.14 details). Each cites the R4 crop id (its
# hash is read from the frozen capture) or the page; the reading itself is recorded, not inferred.
PDF_ITEMS = [
    # id, page, crop, raw, item_type, terminal, consumer, reason
    ("PDF-P13T-TITLE", 13, "P13_FOOTING_TYPICAL", "TYP. DETAIL OF ISOLATED FOOTING.", "DETAIL_TITLE", "NOT_REBAR",
     None, "title; scope = isolated footings (no type restriction printed)"),
    ("PDF-P13T-BOXED", 13, "P13_FOOTING_TYPICAL", "Boxed bars.", "DETAIL_LABEL", "BLOCKED_SEMANTICS", "S4",
     "a separate bar drawn along the footing top and down both side faces (shape only); count, diameter, spacing "
     "and leg lengths not printed; the schedule value '3+n' is not explained"),
    ("PDF-P13T-LONG", 13, "P13_FOOTING_TYPICAL", "Long bars", "DETAIL_LABEL", "PARSED_BOUND", "S4",
     "bottom bars drawn straight between the side legs (no end hook drawn)"),
    ("PDF-P13T-SHORT", 13, "P13_FOOTING_TYPICAL", "Short bars", "DETAIL_LABEL", "PARSED_BOUND", "S4",
     "bottom bars (section dots) - the second bottom direction"),
    ("PDF-P13T-MIN30", 13, "P13_FOOTING_TYPICAL", "Min. 30cm", "DETAIL_DIMENSION", "PARSED_BOUND", "COLUMN_REBAR",
     "column starter foot >= 30 cm on the bottom mesh (owned by the column engine, S3.1)"),
    ("PDF-P13T-MAX10", 13, "P13_FOOTING_TYPICAL", "Max. 10cm", "DETAIL_DIMENSION", "PARSED_BOUND", "COLUMN_REBAR",
     "starter foot within 10 cm of the bottom mesh (column engine)"),
    ("PDF-P13T-40D", 13, "P13_STARTER_40D", "40 ø", "DETAIL_DIMENSION", "PARSED_BOUND", "COLUMN_REBAR",
     "starter projection 40 x bar diameter above the footing (column engine)"),
    ("PDF-P13T-LXW", 13, "P13_FOOTING_TYPICAL", "L x W / D / 10 / 10", "DETAIL_DIMENSION", "NOT_REBAR", None,
     "footing plan size / depth / blinding projection labels (concrete)"),
    ("PDF-P13T-OTHER", 13, "P13_FOOTING_TYPICAL", "Ground beam reinforcements. / Column reinforcement / Column "
     "stirrups.", "DETAIL_LABEL", "PARSED_BOUND", "OTHER_TRADES", "ground-beam and column bars shown for context"),
    ("PDF-P13D-TITLE", 13, "P13_FOOTING_DEEP", "TYP. DETAIL OF ISOLATED FOOTING. (WITH OUT BASEMENT) (level "
     "difference > 2.5m)", "DETAIL_TITLE", "NOT_REBAR", None, "deep-footing variant title"),
    ("PDF-P13D-BOXED", 13, "P13_FOOTING_DEEP", "Boxed bars.", "DETAIL_LABEL", "BLOCKED_SEMANTICS", "S4",
     "same boxed bar in the deep variant: same shape, same missing values"),
    ("PDF-P13D-LONGSHORT", 13, "P13_FOOTING_DEEP", "Long bars / Short bars", "DETAIL_LABEL", "DUPLICATE_SOURCE", "S4",
     "repeats the typical detail's bottom-bar labels"),
    ("PDF-P13D-LOWERGB", 13, "P13_FOOTING_DEEP", "Lower Ground beam reinforcements.", "DETAIL_LABEL",
     "PARSED_BOUND", "OTHER_TRADES", "lower ground beam when the level difference exceeds 2.5 m"),
    ("PDF-P14-TITLE", 14, "P14_LIFT_FOOTING", "DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT)",
     "DETAIL_TITLE", "PARSED_BOUND", "S4", "the FF lift footing (schedule REMARKS 'lift footing')"),
    ("PDF-P14-ASPERSCH", 14, "P14_LIFT_FOOTING", "AS PER SCH.", "DETAIL_LABEL", "PARSED_BOUND", "S4",
     "the FF bottom / top bars are the schedule's"),
    ("PDF-P14-2D16", 14, "P14_LIFT_FOOTING", "2 Ø16 (at the footing side / wall base, two labels)", "DETAIL_LABEL",
     "PARSED_AMBIGUOUS", "S4",
     "a 2Ø16 label at the footing side and one at the wall base: whether it is a footing side bar, a wall-base bar "
     "or both, and its length, are not stated"),
    ("PDF-P14-WALLS", 14, "P14_LIFT_FOOTING", "6Ø12/m, 6Ø16/m, 2Ø12 (pit walls)", "DETAIL_LABEL", "PARSED_BOUND",
     "LIFT", "lift-pit wall bars (LIFT category, not S4)"),
    ("PDF-P08-N22", 8, "P08_NOTE_22_COVER", "note 22: cover >= 2.5 cm (columns, slabs, beams), 7 cm concrete in "
     "contact with soil", "GENERAL_NOTE", "PARSED_BOUND", "S4", "footing cover 7 cm (soil contact)"),
    ("PDF-P08-N09", 8, "P08_NOTE_09_DEVELOPMENT", "note 9: development length >= 70 Ø tension, 40 Ø compression",
     "GENERAL_NOTE", "PARSED_BOUND", "S4", "anchorage / lap rule; no footing bar exceeds the 12 m stock"),
    ("PDF-P08-OTHER", 8, None, "notes 1-8, 10-21, 23-24 (no reinforcement detail for footings; none names boxed "
     "bars)", "GENERAL_NOTE", "NOT_REBAR", None, "read on the rendered page; no footing reinforcement content"),
    ("PDF-P09-PRINT", 9, None, "Schedule of Footings (printed page)", "SCHEDULE_PRINT", "DUPLICATE_SOURCE", "S4",
     "the PDF page prints the same DXF table (values, layout and the REMARKS section icons agree)"),
    ("PDF-P15-P16", 15, None, "pp.15-16 details (columns, slabs, stairs, beams)", "DETAIL_SHEET", "NOT_REBAR", None,
     "no footing reinforcement; no boxed bars"),
]


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _r(v, n=1):
    return None if v is None else round(float(v), n)


# ------------------------------------------------------------------ DXF read
def read_dxf(path):
    import ezdxf
    if _sha(path) != DXF_SHA:
        raise SystemExit(f"ST7757.dxf sha mismatch: expected {DXF_SHA}")
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    x0, x1, y0, y1 = TABLE_BOX
    inside = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1  # noqa: E731
    H, V, texts, inserts, rein = [], [], [], [], []
    for e in msp:
        t = e.dxftype()
        if t in ("LINE", "LWPOLYLINE") and e.dxf.layer == GRID_LAYER:
            if t == "LINE":
                segs = [((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y))]
            else:
                pts = [tuple(p[:2]) for p in e.get_points()]
                if e.closed:
                    pts.append(pts[0])
                segs = list(zip(pts, pts[1:]))
            for a, b in segs:
                if not (inside(*a) and inside(*b)):
                    continue
                if abs(a[1] - b[1]) < 1:
                    H.append((a[1], a[0], b[0], e.dxf.handle))
                elif abs(a[0] - b[0]) < 1:
                    V.append((a[0], a[1], b[1], e.dxf.handle))
        elif t == "TEXT" and inside(e.dxf.insert.x, e.dxf.insert.y):
            texts.append({"handle": e.dxf.handle, "text": e.dxf.text, "x": e.dxf.insert.x, "y": e.dxf.insert.y,
                          "h": e.dxf.height, "layer": e.dxf.layer})
        elif t == "INSERT" and e.dxf.name in ("FT", "FTB"):
            inserts.append({"name": e.dxf.name, "handle": e.dxf.handle, "x": e.dxf.insert.x, "y": e.dxf.insert.y,
                            "attribs": [{"tag": a.dxf.tag, "text": a.dxf.text, "handle": a.dxf.handle,
                                         "x": a.dxf.insert.x, "y": a.dxf.insert.y, "h": a.dxf.height}
                                        for a in e.attribs]})
        elif t in ("LWPOLYLINE", "HATCH") and e.dxf.layer == "S-REIN.D":
            from ezdxf import bbox
            b = bbox.extents([e])
            if b.has_data and inside(b.extmin.x, b.extmin.y):
                rein.append({"handle": e.dxf.handle, "type": t, "x": b.extmin.x, "y": b.extmin.y,
                             "x1": b.extmax.x, "y1": b.extmax.y})
    blocks = {}
    for name in ("FT", "FTB"):
        blk = doc.blocks.get(name)
        blocks[name] = {"attdefs": [{"tag": a.dxf.tag, "default": a.dxf.text, "x": round(a.dxf.insert.x, 1),
                                     "y": round(a.dxf.insert.y, 1)} for a in blk if a.dxftype() == "ATTDEF"],
                        "glyphs": [{"text": a.dxf.text, "x": round(a.dxf.insert.x, 1), "y": round(a.dxf.insert.y, 1)}
                                   for a in blk if a.dxftype() == "TEXT"]}
    # every TEXT / MTEXT / ATTRIB in the drawing that looks like a boxed pair or names boxed / cage bars
    pat = re.compile(r"^\s*\d+\s*\+\s*\d*\s*$|box|cage", re.I)
    hits = []
    for lay in doc.layouts:
        for e in lay:
            t = e.dxftype()
            vals = []
            if t == "TEXT":
                vals = [(e.dxf.handle, e.dxf.text, None)]
            elif t == "MTEXT":
                vals = [(e.dxf.handle, e.plain_text(), None)]
            elif t == "INSERT":
                vals = [(a.dxf.handle, a.dxf.text, a.dxf.tag) for a in e.attribs]
            for h, s, tag in vals:
                if s and pat.search(s):
                    hits.append({"layout": lay.name, "handle": h, "text": s, "tag": tag})
    for b in doc.blocks:
        if b.name.startswith("*"):
            continue
        for e in b:
            if e.dxftype() in ("TEXT", "ATTDEF") and e.dxf.text and pat.search(e.dxf.text):
                hits.append({"layout": "BLOCK:" + b.name, "handle": e.dxf.handle, "text": e.dxf.text,
                             "tag": getattr(e.dxf, "tag", None)})
    return {"H": H, "V": V, "texts": texts, "inserts": sorted(inserts, key=lambda i: -i["y"]), "rein": rein,
            "blocks": blocks, "boxed_text_hits": sorted(hits, key=lambda z: (z["layout"], z["handle"]))}


def _merge_lines(lines, eps=DOUBLE_LINE_EPS):
    out = []
    for ln in sorted((l0, min(a, b), max(a, b), k) for l0, a, b, k in lines):
        if out and abs(ln[0] - out[-1][0]) <= eps and not (ln[2] < out[-1][1] - 1 or ln[1] > out[-1][2] + 1):
            o = out[-1]
            out[-1] = (o[0], min(o[1], ln[1]), max(o[2], ln[2]), o[3] + "+" + ln[3])
        else:
            out.append(ln)
    return out


def _snap(v, refs, eps=DOUBLE_LINE_EPS):
    best = min(refs, key=lambda r: abs(r - v))
    return best if abs(best - v) <= eps else v


def read_table(D):
    H, V = _merge_lines(D["H"]), _merge_lines(D["V"])
    vx, hy = [v[0] for v in V], [h[0] for h in H]
    H = [(h[0], _snap(h[1], vx), _snap(h[2], vx), h[3]) for h in H]
    V = [(v[0], _snap(v[1], hy), _snap(v[2], hy), v[3]) for v in V]
    items = [ST.Item(t["handle"], t["text"], t["x"], t["y"] + 0.5 * t["h"]) for t in D["texts"]]
    for i in D["inserts"]:
        items += [ST.Item(a["handle"], a["text"], a["x"], a["y"] + 0.5 * a["h"], "ATTRIB", a["tag"], i["handle"])
                  for a in i["attribs"]]
    tab = ST.read(items, H, V, eps=PLACE_EPS)
    return tab, {"h_lines_raw": len(D["H"]), "v_lines_raw": len(D["V"]), "h_lines": len(H), "v_lines": len(V)}


# ------------------------------------------------------------------ helpers over the table
def band_of_attr(tab, handle):
    for b in tab["bands"]:
        for c in b["cells"]:
            for v in c["values"]:
                if v["key"] == handle:
                    return b["band"], c
    return None, None


HEADER_BANDS = (1, 2, 3)


def headers_by_x(tab):
    leaves = ST.header_paths(tab, list(HEADER_BANDS))
    return [(lf["x0"], lf["x1"], lf["path"][-1] if lf["path"] else "") for lf in leaves]


def header_at(leaves, x):
    for x0, x1, lab in leaves:
        if x0 <= x <= x1:
            return lab
    return None


# ------------------------------------------------------------------ 01 token parity
def _fmt(form):
    if form is None:
        return "REJECT"
    if "multiple" in form:
        return "MULTIPLE:" + ";".join(_fmt(x) for x in form["multiple"])
    s = f"{form['count']}xØ{form['dia_mm']}" if form["count"] is not None else f"Ø{form['dia_mm']}"
    s += "/m" if form["per_m"] else ""
    s += f"@{form['spacing_cm']}cm" if form.get("spacing_cm") else ""
    s += f" {form['position']}" if form.get("position") else ""
    return s


def _oracle(count_raw, dia_raw):
    """Research oracle, independent of the Urban parsers: the expected normalised form of a split cell pair."""
    c, d = (count_raw or "").strip(), (dia_raw or "").strip()
    m = re.fullmatch(r"(\d+)\s*(/\s*m)?", d)
    if re.fullmatch(r"\d+", c) and m:
        return f"{int(c)}xØ{int(m[1])}" + ("/m" if m[2] else "")
    return "NOT_A_BAR_PAIR"


def token_register(D, tab, leaves, defs_by_type, occ_count):
    rows = []
    n = 0
    for ins in D["inserts"]:
        a = {x["tag"]: x for x in ins["attribs"]}
        mark = a["FO-TY"]["text"]
        pairs = PAIRS_FT if ins["name"] == "FT" else PAIRS_FTB
        for label, ct, dt, comp in pairs:
            n += 1
            c, d = a[ct], a[dt]
            adm = FG.admit_cells(c["text"], d["text"])
            joined = FG.joined_form(c["text"], d["text"])
            p1 = FG._run(FG.P_PARSE_BAR, joined)
            p2 = FG._run(FG.P_BAR_SPEC, joined)
            p3 = FG._run(FG.P_SLAB, joined)
            jf = {k: v for k, v in (("p1", p1), ("p2", p2), ("p3", p3))}
            jok = len({repr(sorted(v.items())) if v else "REJECT" for v in jf.values()}) == 1
            band, _ = band_of_attr(tab, c["handle"])
            rows.append({
                "TOKEN_ID": f"TK{n:03d}", "RAW_TEXT": f"{c['text']} | {d['text']}",
                "SOURCE_HANDLE": f"{ins['handle']}:{c['handle']}+{d['handle']}",
                "SOURCE_TYPE": f"SCHEDULE_ATTRIB_CELL_PAIR ({ins['name']} {ct}+{dt})", "FOOTING_MARK": mark,
                "COMPONENT": comp, "PLAN_OCCURRENCES": occ_count.get(mark, 0),
                "LOCATION": f"Schedule of Footings p.9 band {band} / header {header_at(leaves, c['x'])}",
                "S4_ROUTE": adm["route"] or "NONE", "TOKEN_CLASS": adm["token_class"],
                "PARSER_CELLS_bar_from_cells": _fmt(adm["parsers"].get(FG.P_CELLS)),
                "PARSER_1_parse_bar": f"{_fmt(p1)} (joined '{joined}')",
                "PARSER_2_bar_spec": f"{_fmt(p2)} (joined)", "PARSER_3_slab_parse": f"{_fmt(p3)} (joined)",
                "NORMALIZED_EXPECTED_FORM": _oracle(c["text"], d["text"]),
                "PARITY_STATUS": ("PARITY_OK" if adm["decision"] == FG.ADMITTED and
                                  _fmt(adm["form"]) == _oracle(c["text"], d["text"]) else "PARITY_FAIL"),
                "JOINED_FORM_PARITY": "AGREE" if jok and p1 else "DIFFER",
                "S4_DECISION": adm["decision"], "REASON": adm["reason"]})
        for tag in ("BOXED",) if ins["name"] == "FT" else ("BOXED-T", "BOXED-B"):
            n += 1
            x = a[tag]
            adm = FG.admit_token(x["text"])
            band, _ = band_of_attr(tab, x["handle"])
            rows.append({
                "TOKEN_ID": f"TK{n:03d}", "RAW_TEXT": x["text"], "SOURCE_HANDLE": f"{ins['handle']}:{x['handle']}",
                "SOURCE_TYPE": f"SCHEDULE_ATTRIB_CELL ({ins['name']} {tag})", "FOOTING_MARK": mark,
                "COMPONENT": "BOXED_REBAR" if tag == "BOXED" else "LAYER_LABEL",
                "PLAN_OCCURRENCES": occ_count.get(mark, 0),
                "LOCATION": f"Schedule of Footings p.9 band {band} / header {header_at(leaves, x['x'])}",
                "S4_ROUTE": adm["route"] or "NONE", "TOKEN_CLASS": adm["token_class"],
                "PARSER_CELLS_bar_from_cells": "N/A",
                "PARSER_1_parse_bar": _fmt(FG._run(FG.P_PARSE_BAR, x["text"])),
                "PARSER_2_bar_spec": _fmt(FG._run(FG.P_BAR_SPEC, x["text"])),
                "PARSER_3_slab_parse": _fmt(FG._run(FG.P_SLAB, x["text"])),
                "NORMALIZED_EXPECTED_FORM": ("BOXED_PAIR (no bar form)" if FG.token_class(x["text"]) == FG.BOXED_PAIR
                                             else "EMPTY" if not x["text"].strip() else "LAYER_LABEL"),
                "PARITY_STATUS": "NOT_A_BAR_TOKEN (all parsers reject)" if all(
                    FG._run(p, x["text"]) is None for p in (FG.P_PARSE_BAR, FG.P_BAR_SPEC, FG.P_SLAB))
                else "PARSER_ACCEPTS_NON_BAR", "JOINED_FORM_PARITY": "N/A",
                "S4_DECISION": adm["decision"], "REASON": adm["reason"]})
    # the one bar label on the PDF-only lift-footing detail that could touch a footing
    n += 1
    adm = FG.admit_token("2Ø16")
    rows.append({"TOKEN_ID": f"TK{n:03d}", "RAW_TEXT": "2 Ø16", "SOURCE_HANDLE": "PDF:p14:P14_LIFT_FOOTING",
                 "SOURCE_TYPE": "DETAIL_LABEL (PDF, OCR + visual)", "FOOTING_MARK": "FF",
                 "COMPONENT": "FOOTING_SIDE_BAR?", "PLAN_OCCURRENCES": occ_count.get("FF", 0),
                 "LOCATION": "p.14 DETAIL OF LIFT WITH ISOLATED FOOTING, footing side", "S4_ROUTE": adm["route"],
                 "TOKEN_CLASS": adm["token_class"], "PARSER_CELLS_bar_from_cells": "N/A",
                 "PARSER_1_parse_bar": _fmt(adm["parsers"].get(FG.P_PARSE_BAR)),
                 "PARSER_2_bar_spec": _fmt(adm["parsers"].get(FG.P_BAR_SPEC)),
                 "PARSER_3_slab_parse": _fmt(adm["parsers"].get(FG.P_SLAB)), "NORMALIZED_EXPECTED_FORM": "2xØ16",
                 "PARITY_STATUS": "PARITY_OK" if adm["decision"] == FG.ADMITTED else "PARITY_FAIL",
                 "JOINED_FORM_PARITY": "N/A", "S4_DECISION": adm["decision"],
                 "REASON": adm["reason"] + "; APPLICABILITY AMBIGUOUS (footing side bar or wall base) - parity is "
                                           "not authority"})
    return rows


# ------------------------------------------------------------------ 02 census
def census(D, tab, leaves, defs, occ, r4):
    C = FG.Census()
    out = []
    row_occ = Counter(r["type"] for r in occ["rows"] if r["type"])
    conflict_types = {t for r in occ["rows"] for t in (r["candidate_types"] or [])}

    def add(item_id, item_type, source, raw, mark, location, terminal, reason, consumer=None, quantity=None):
        C.admit(item_id, item_type, source)
        C.terminate(item_id, terminal, reason, quantity=quantity, consumer=consumer)
        out.append({"ITEM_ID": item_id, "ITEM_TYPE": item_type, "SOURCE": source, "RAW": raw, "FOOTING_MARK": mark,
                    "LOCATION": location, "TERMINAL_STATE": terminal, "REASON": reason, "CONSUMER": consumer or "",
                    "QUANTITY": "" if quantity is None else quantity})

    # schedule header / title texts
    for t in sorted(D["texts"], key=lambda z: z["handle"]):
        b, _ = band_of_attr(tab, t["handle"])
        if b is not None and b in HEADER_BANDS:
            add(f"HDR-{t['handle']}", "SCHEDULE_HEADER", f"DXF:{t['handle']}", t["text"], "",
                f"band {b}", "NOT_REBAR", "header / title text: binds the column below it (FT-04)", "S4")
    # REMARKS column texts (one legacy-encoded Arabic remark) and section icons
    for t in sorted(D["texts"], key=lambda z: z["handle"]):
        b, _ = band_of_attr(tab, t["handle"])
        if b is not None and b not in HEADER_BANDS:
            hdr = header_at(leaves, t["x"])
            if hdr and "R E M A R K S" in hdr:
                add(f"RMK-{t['handle']}", "SCHEDULE_REMARK", f"DXF:{t['handle']}", t["text"], "FF",
                    f"band {b} / REMARKS", "NOT_REBAR",
                    "legacy-encoded Arabic remark; the PDF prints it as 'lift footing' (FF); no reinforcement value")
    icons = defaultdict(list)
    for e in D["rein"]:
        for i in D["inserts"]:
            # the icon sits in the REMARKS cell of one FTB row (row spans 2 bands)
            if i["name"] == "FTB" and i["y"] - 1042.3 - 1 <= e["y"] <= i["y"] + 1:
                icons[i["handle"]].append(e["handle"])
    for i in D["inserts"]:
        if i["handle"] in icons:
            mark = {a["tag"]: a["text"] for a in i["attribs"]}["FO-TY"]
            add(f"ICON-{i['handle']}", "SCHEDULE_REMARK_SYMBOL", "DXF:" + "|".join(sorted(icons[i["handle"]])),
                "section symbol: dashed rectangle, 3 bar dots top + 3 bottom", mark, "REMARKS column",
                "PARSED_AMBIGUOUS",
                "a drawn section of a two-layer footing; it carries no value and its meaning is not stated (F8 has "
                "none); it does not gate any S4 quantity")
    # schedule rows, cells and block glyphs
    for i in D["inserts"]:
        a = {x["tag"]: x for x in i["attribs"]}
        mark = a["FO-TY"]["text"]
        n_occ = row_occ.get(mark, 0)
        in_conflict = mark in conflict_types
        if in_conflict and n_occ == 0:
            row_term, why = "PARSED_SOURCE_CONFLICT", "row is a candidate of the F / F10 outline only"
        elif n_occ:
            row_term, why = "PARSED_BOUND", f"row defines type {mark}; {n_occ} plan occurrence(s)" + (
                " (+ a conflict candidate)" if in_conflict else "")
        else:
            row_term, why = "PARSED_BOUND", f"row defines type {mark}; 0 plan occurrences (the plan decides " \
                                            "occurrence; the schedule never creates one)"
        add(f"ROW-{i['handle']}", "SCHEDULE_ROW", f"DXF:{i['handle']}", f"{i['name']} {mark}", mark,
            "Schedule of Footings p.9", row_term, why, "S4")
        for x in sorted(i["attribs"], key=lambda z: z["tag"]):
            tag, txt = x["tag"], x["text"]
            hdr = header_at(leaves, x["x"])
            loc = f"{i['name']} {tag} under '{hdr}'"
            if tag in ("BOXED",):
                if FG.token_class(txt) == FG.BOXED_PAIR:
                    term, rsn = "BLOCKED_SEMANTICS", f"BOXED '{txt}': component exists (p.13 'Boxed bars.'); " \
                                                     "count / diameter / shape / length meaning not stated"
                else:
                    term, rsn = "BLOCKED_SEMANTICS", "BOXED cell EMPTY (the block default '3+-' was cleared); " \
                                                     "whether the footing has boxed bars is not stated"
            elif tag in ("BOXED-T", "BOXED-B"):
                term, rsn = "NOT_REBAR", f"layer label '{txt}' in the BOXED column: binds the {txt} bar sub-row"
            elif tag == "FO-TY":
                term, rsn = "PARSED_BOUND", "type key"
            elif tag in ("W", "H", "DEPHT"):
                term, rsn = "PARSED_BOUND", f"dimension, bound by drawn header '{hdr}' (attribute tag {tag})"
            else:
                term, rsn = "PARSED_BOUND", "bar cell (count or diameter) of a split-cell token; route bar_from_cells"
            if in_conflict and n_occ == 0 and term == "PARSED_BOUND":
                term, rsn = "PARSED_SOURCE_CONFLICT", rsn + "; the row is only an F / F10 conflict candidate"
            add(f"CELL-{x['handle']}", "SCHEDULE_CELL", f"DXF:{i['handle']}:{x['handle']}", txt, mark, loc, term, rsn,
                "S4")
        glyphs = D["blocks"][i["name"]]["glyphs"]
        for k, g in enumerate(glyphs):
            add(f"GLYPH-{i['handle']}-{k}", "SCHEDULE_GLYPH", f"DXF:BLOCK {i['name']} TEXT #{k} via {i['handle']}",
                g["text"], mark, f"block text at {g['x']},{g['y']}", "NOT_REBAR",
                "the Ø glyph printed before a diameter cell (consumed by the cell pair)")
    # plan tags and outlines (frozen S1 occurrence register)
    for r in occ["rows"]:
        fid = r["footing_id"]
        t = r["tag"]
        issues = []
        mm = [m for m in occ.get("mismatches", []) if m["kind"] == "FOOTING_OUTLINES_OVERLAP"
              and any(x.split(":")[-1] == r["outline"]["handle"].split(":")[0] for x in m["footings"])]
        if mm:
            issues.append(f"OUTLINE_OVERLAP {mm[0]['overlap_m2']} m2 with {'/'.join(mm[0]['footings'])}")
        if r["type"] is None:
            add(f"TAG-{t['handle']}", "PLAN_TAG", f"DXF:{t['handle']}", t["text"], "F|F10", fid,
                "PARSED_SOURCE_CONFLICT", "one of two tags (F, F10) inside outline 1B1B; never nearest-wins", "S4")
            for ct in r["competing_tags"]:
                add(f"TAG-{ct['handle']}", "PLAN_TAG", f"DXF:{ct['handle']}", ct["text"], "F|F10", fid,
                    "PARSED_SOURCE_CONFLICT", "competing tag in the same outline", "S4")
            add(f"OUT-{r['outline']['handle']}", "PLAN_OUTLINE", f"DXF:{r['outline']['handle']}",
                f"{r['outline']['geometry']} bbox {r['outline']['bbox']}", "F|F10", fid, "PARSED_SOURCE_CONFLICT",
                "outline holds tags F and F10; hypotheses {2 x F, F10, drawn outline}", "S4")
            continue
        q = COUNT_QUERIES.get(r["type"])
        note = f"; occurrence-count query {q} open (review question, no external count used)" if q else ""
        add(f"TAG-{t['handle']}", "PLAN_TAG", f"DXF:{t['handle']}", t["text"], r["type"], fid, "PARSED_BOUND",
            f"tag bound to its own outline; type {r['type']}{note}", "S4")
        add(f"OUT-{r['outline']['handle']}", "PLAN_OUTLINE", f"DXF:{r['outline']['handle']}",
            f"{r['outline']['geometry']} bbox {r['outline']['bbox']}", r["type"], fid, "PARSED_BOUND",
            f"outline bound to one tag; drawn {r['sizes']['drawn_L_cm']}x{r['sizes']['drawn_W_cm']} cm = schedule"
            + ("; " + "; ".join(issues) if issues else "") + note, "S4")
    # PDF-only sheets
    crops = r4["crops"] if isinstance(r4["crops"], dict) else {c["crop_id"]: c for c in r4["crops"]}
    for pid, page, crop, raw, typ, term, cons, rsn in PDF_ITEMS:
        h = crops[crop]["crop_hash"][:16] if crop else "page-level"
        add(pid, typ, f"PDF:{PDF_SHA[:12]}:p{page}" + (f":{crop}#{h}" if crop else ""), raw,
            "FF" if page == 14 else "", f"ST7757.pdf p.{page}", term, rsn, cons)
    chk = C.check()
    return out, chk


# ------------------------------------------------------------------ 03 boxed + diagnostics
def _rank(v):
    s = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and v[s[j + 1]] == v[s[i]]:
            j += 1
        for k in range(i, j + 1):
            r[s[k]] = (i + j) / 2.0 + 1
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = _rank(x), _rank(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return None if den == 0 else round(num / den, 3)


HYPOTHESES = {
    "H1": "'3+n' = 3 bars in one plan direction + n bars in the other (a two-direction box cage)",
    "H2": "'3+n' = 3 boxed bars + n of something else (e.g. side / face bars) on the same cage",
    "H3": "'3+n' = 3 bars of diameter n mm",
    "H4": "'n' is a spacing / count per metre",
    "H5": "'3+n' = 3 top bars + n side bars per face",
}


def boxed(D, tab, leaves, defs, occ, r4):
    occ_by = defaultdict(list)
    for r in occ["rows"]:
        if r["type"]:
            occ_by[r["type"]].append(r)
    xs = [r["outline"]["bbox"][0] for r in occ["rows"]] + [r["outline"]["bbox"][2] for r in occ["rows"]]
    ys = [r["outline"]["bbox"][1] for r in occ["rows"]] + [r["outline"]["bbox"][3] for r in occ["rows"]]
    X0, X1, Y0, Y1 = min(xs), max(xs), min(ys), max(ys)

    def pos_class(b, tol=1000.0):
        ex = b[0] - X0 <= tol or X1 - b[2] <= tol
        ey = b[1] - Y0 <= tol or Y1 - b[3] <= tol
        return "CORNER" if ex and ey else "EDGE" if ex or ey else "INTERNAL"

    vals = Counter(a["text"] for i in D["inserts"] for a in i["attribs"] if a["tag"] == "BOXED")
    leaf_names = [lab for _, _, lab in leaves]
    rows, diag = [], []
    for i in D["inserts"]:
        a = {x["tag"]: x for x in i["attribs"]}
        mark = a["FO-TY"]["text"]
        d = defs[mark]
        tags = ("BOXED",) if i["name"] == "FT" else ("BOXED-T", "BOXED-B")
        for tag in tags:
            x = a[tag]
            band, cell = band_of_attr(tab, x["handle"])
            bd = tab["bands"][band]
            ci = next(k for k, c in enumerate(bd["cells"]) if c is cell)
            left = bd["cells"][ci - 1]["values"] if ci > 0 else []
            right = bd["cells"][ci + 1]["values"] if ci + 1 < len(bd["cells"]) else []
            hdr = header_at(leaves, x["x"])
            k = leaf_names.index(hdr)
            rights = [v["value"] for v in right]
            icon = [e["handle"] for e in D["rein"] if bd["y_lo"] - 1 <= e["y"] <= bd["y_hi"] + 1]
            raw = x["text"]
            is_pair = FG.token_class(raw) == FG.BOXED_PAIR
            occs = occ_by.get(mark, [])
            if tag != "BOXED":
                status, sem = "NOT_A_BOXED_VALUE (layer label)", "N/A"
                ev_for, ev_against, poss = (f"FTB row uses the BOXED column for the sub-row label '{raw}'; the bars "
                                            "of the sub-row are its SHORT / LONG cells"), "", "LAYER_LABEL"
            elif not raw.strip():
                status, sem = "UNRESOLVED (EMPTY CELL)", FG.UNRESOLVED
                poss = "NOT_REQUIRED | NOT_YET_SPECIFIED"
                ev_for = ("NOT_REQUIRED: the FT block default '3+-' was actively cleared for FN (the drafter removed "
                          "the template value)")
                ev_against = ("p.13 'TYP. DETAIL OF ISOLATED FOOTING' shows boxed bars with no type restriction; F "
                              "(90x80x30, smaller than FN 100x100x30) carries '3+4'; nothing states that FN has no "
                              "boxed bars")
            else:
                status, sem = "UNRESOLVED", FG.UNRESOLVED
                poss = "|".join(HYPOTHESES)
                ev_for = ("component exists: header 'BOXED' (TEXT 1C53) heads its own column; p.13 typical and deep "
                          "details label 'Boxed bars.' (top + both side faces); the block template pre-prints '3+' "
                          "(ATTDEF default '3+-'), so the '3' is fixed and only the second number varies")
                ev_against = ("no Ø glyph in the BOXED cell (the SHORT / LONG cells have one in the block), no "
                              "diameter, no spacing, no shape dimension anywhere in the set; the leading '3' is the "
                              "same for W = 80 ... 270 cm")
            diag_row = {"mark": mark, "element": d["element"], "L_cm": d["L_cm"], "W_cm": d["W_cm"],
                        "D_cm": d["D_cm"], "boxed": raw if tag == "BOXED" else None}
            rows.append({
                "BOXED_ID": f"BX-{mark}-{tag}", "FOOTING_MARK": mark, "RAW_VALUE": raw if raw else "(empty)",
                "HANDLE": f"{i['handle']}:{x['handle']}", "BLOCK": i["name"], "SCHEDULE_ROW": f"band {band}",
                "SCHEDULE_COLUMN_HEADER": hdr,
                "ADJACENT_HEADERS": f"{leaf_names[k - 1] if k else ''} | {leaf_names[k + 1] if k + 1 < len(leaf_names) else ''}",
                "NEIGHBOUR_CELLS": f"left (LONG BARS) {[v['value'] for v in left]} | right (REMARKS) "
                                   f"{rights if rights else 'section symbol (S-REIN.D)' if icon else '[]'}",
                "DRAWING_LOCATION": f"model ({_r(x['x'])}, {_r(x['y'])}); ST7757.pdf p.9 Schedule of Footings",
                "REPEATED_VALUE_ELSEWHERE": (f"same value on {vals[raw] - 1} other schedule row(s); 0 elsewhere in "
                                             "the DXF; 0 on PDF-only sheets") if tag == "BOXED" else "N/A",
                "DETAIL_REFERENCES": "p.13 TYP. DETAIL OF ISOLATED FOOTING 'Boxed bars.'; p.13 deep variant 'Boxed "
                                     "bars.'" if tag == "BOXED" else "p.14 lift footing (FF only)",
                "PLAN_OCCURRENCES": len(occs),
                "FOOTING_SIZE_cm": f"{d['L_cm']}x{d['W_cm']}x{d['D_cm']}",
                "POSSIBLE_SEMANTICS": poss, "EVIDENCE_FOR": ev_for, "EVIDENCE_AGAINST": ev_against,
                "SEMANTICS_CLASS": sem, "STATUS": status,
                "S4_TREATMENT": ("BLOCKED_UNQUANTIFIED (footing REBAR_LOWER_BOUND)" if tag == "BOXED" else
                                 "N/A (layer label)")})
            if tag == "BOXED" and is_pair:
                n2 = int(raw.split("+")[1])
                sb = next(c for c in d["components"] if c["component"] == "BOTTOM_SHORT")
                lb = next(c for c in d["components"] if c["component"] == "BOTTOM_LONG")
                cols = sorted({c for o in occs for c in o["supported_column_types"]})
                diag_row.update(n1=int(raw.split("+")[0]), n2=n2, area_m2=round(d["L_cm"] * d["W_cm"] / 1e4, 4),
                                short=f"{sb['count']}Ø{sb['dia_mm']}", long=f"{lb['count']}Ø{lb['dia_mm']}",
                                dia_mm=sb["dia_mm"], short_count=sb["count"], long_count=lb["count"],
                                s_short_cm=round((d["L_cm"] - 2 * COVER_CM) / (sb["count"] - 1), 1),
                                s_long_cm=round((d["W_cm"] - 2 * COVER_CM) / (lb["count"] - 1), 1),
                                s_short_if_reversed_cm=round((d["W_cm"] - 2 * COVER_CM) / (sb["count"] - 1), 1),
                                s_long_if_reversed_cm=round((d["L_cm"] - 2 * COVER_CM) / (lb["count"] - 1), 1),
                                occurrences=len(occs), columns="/".join(cols) or "-",
                                columns_per_footing=max((len(o["supported_column_types"]) for o in occs), default=0),
                                position="/".join(sorted({pos_class(o["outline"]["bbox"]) for o in occs})) or "-")
                diag.append(diag_row)
    return rows, diag


def diagnostics(diag):
    keys = ("L_cm", "W_cm", "D_cm", "area_m2", "dia_mm", "short_count", "long_count")
    n2 = [r["n2"] for r in diag]
    rho = {k: spearman([r[k] for r in diag], n2) for k in keys}
    by_L = sorted(diag, key=lambda r: (r["L_cm"], r["mark"]))
    mono_L = all(a["n2"] <= b["n2"] for a, b in zip(by_L, by_L[1:]))
    by_W = sorted(diag, key=lambda r: (r["W_cm"], r["mark"]))
    mono_W = all(a["n2"] <= b["n2"] for a, b in zip(by_W, by_W[1:]))
    by_D = sorted(diag, key=lambda r: (r["D_cm"], r["mark"]))
    mono_D = all(a["n2"] <= b["n2"] for a, b in zip(by_D, by_D[1:]))
    groups = defaultdict(list)
    for r in diag:
        groups[r["n2"]].append(r["L_cm"])
    return {"rows": diag, "spearman_n2_vs": rho,
            "monotone_non_decreasing_in": {"L_cm": mono_L, "W_cm": mono_W, "D_cm": mono_D},
            "n1_values": sorted({r["n1"] for r in diag}),
            "L_range_by_n2": {k: [min(v), max(v)] for k, v in sorted(groups.items())},
            "bar_direction_check": {r["mark"]: [r["s_short_cm"], r["s_long_cm"]] for r in diag},
            "bar_direction_check_if_reversed": {r["mark"]: [r["s_short_if_reversed_cm"], r["s_long_if_reversed_cm"]]
                                                for r in diag},
            "bar_direction_note": "spacing (cm) = (distribution length - 2 x 7 cm cover) / (count - 1); SHORT bars "
                                  "distributed along L and LONG bars along W give near-equal spacing both ways on "
                                  "every FT type; the reversed reading does not",
            "status": "DIAGNOSTIC_ONLY - correlation is not authority; no rule is promoted"}


# ------------------------------------------------------------------ header binding (FT-04 on the real table)
def header_bindings(D, tab):
    out = []
    for i in D["inserts"]:
        a = {x["tag"]: x for x in i["attribs"]}
        b_top, _ = band_of_attr(tab, a["FO-TY"]["handle"])
        if i["name"] == "FT":
            res = [("ROW", b_top, FG.header_binding(tab, list(HEADER_BANDS), b_top, FIXED_FT))]
        else:
            b_bot, _ = band_of_attr(tab, a["SH-B-B"]["handle"])
            res = [("TOP", b_top, FG.header_binding(tab, list(HEADER_BANDS), b_top, FIXED_FTB_TOP)),
                   ("BOT", b_bot, FG.header_binding(tab, list(HEADER_BANDS), b_bot, FIXED_FTB_BOT))]
        layer = None
        if i["name"] == "FTB":
            # the TOP / BOT label and its bar cells sit on one text line; the sub-row rule may be missing (FF)
            dt = abs(a["BOXED-T"]["y"] - a["SH-T-B"]["y"])
            db = abs(a["BOXED-B"]["y"] - a["SH-B-B"]["y"])
            tol = max(a["SH-T-B"]["h"], a["SH-B-B"]["h"])
            ruled = band_of_attr(tab, a["BOXED-T"]["handle"])[0] != band_of_attr(tab, a["BOXED-B"]["handle"])[0]
            layer = {"top_label_to_top_cells_mm": round(dt, 1), "bot_label_to_bot_cells_mm": round(db, 1),
                     "aligned": dt <= tol and db <= tol, "sub_row_rule_drawn": ruled,
                     "binding": "GRID_SUB_ROW" if ruled else "TEXT_LINE_ALIGNMENT (no sub-row rule in the DXF)"}
        for sub, band, r in res:
            out.append({"insert": i["handle"], "mark": a["FO-TY"]["text"], "sub_row": sub, "band": band,
                        "state": r["state"], "conflicts": r["conflicts"], "layer_alignment": layer,
                        "derived": {k: v.split(" / ")[-1] if isinstance(v, str) else v for k, v in r["derived"].items()}})
    return out


# ------------------------------------------------------------------ 06 readiness matrix
def readiness(cen_chk, tok, hb, diag, occ):
    tok_ok = all(r["S4_DECISION"] == "ADMITTED" for r in tok if r["COMPONENT"] not in ("BOXED_REBAR", "LAYER_LABEL",
                                                                                      "FOOTING_SIDE_BAR?"))
    hb_ok = all(r["state"] == "BOUND_BY_HEADER" and (r["layer_alignment"] is None or r["layer_alignment"]["aligned"])
                for r in hb)
    dir_ok = all(abs(v[0] - v[1]) <= 6.0 for v in diag["bar_direction_check"].values())
    R = []

    def row(item, src, sem, geo, formula, tested, status, evidence, blocker=""):
        R.append({"ITEM": item, "SOURCE_AVAILABLE": src, "SEMANTICS_AVAILABLE": sem, "GEOMETRY_AVAILABLE": geo,
                  "FORMULA_AVAILABLE": formula, "TESTED": tested, "S4_STATUS": status, "EVIDENCE": evidence,
                  "BLOCKER_OR_CONDITION": blocker})
    row("footing occurrence census", "YES", "YES", "YES", "N/A", "YES", "READY",
        f"26 outlines / 27 tags, conservation {cen_chk['conserved']}; 25 established + F/F10 conflict",
        "F/F10 SOURCE_CONFLICT -> that occurrence REBAR_BLOCKED; F3 OQ-11 -> F3 occurrences PROVISIONAL until "
        "answered")
    row("schedule binding (header position)", "YES", "YES", "YES", "N/A", "YES",
        "READY" if hb_ok else "BLOCKED_COMPONENT",
        f"{sum(r['state'] == 'BOUND_BY_HEADER' for r in hb)}/{len(hb)} schedule (sub-)rows bound by drawn header; "
        "W->L, H->W, DEPHT->H confirmed", "" if hb_ok else "header conflict")
    row("bottom short bars", "YES", "YES" if dir_ok else "PARTIAL", "YES", "YES", "YES",
        "READY" if tok_ok else "BLOCKED_COMPONENT",
        "FT SH-B/SH-D absolute counts; FTB SH-B-B/SH-B-D per metre; bar_from_cells parity OK on every cell pair; "
        "direction: SHORT bars span W, distributed along L (counts give equal spacing both ways, diagnostic)",
        "per-metre FTB counts: the end-bar convention (+1) stays PROVISIONAL until stated")
    row("bottom long bars", "YES", "YES" if dir_ok else "PARTIAL", "YES", "YES", "YES",
        "READY" if tok_ok else "BLOCKED_COMPONENT", "FT LO-B/LO-D; FTB LO-B-B/LO-B-D per metre; as short bars",
        "as short bars")
    row("top short bars", "YES (FTB only)", "YES", "YES", "YES", "YES", "READY_LOWER_BOUND",
        "FTB SH-T-B/SH-T-D per metre (F8, F12, F13, F14, FF); single-layer FT footings have no top mesh",
        "top-layer end detail (bend down / hook) not drawn -> core length only; end detail BLOCKED")
    row("top long bars", "YES (FTB only)", "YES", "YES", "YES", "YES", "READY_LOWER_BOUND", "FTB LO-T-B/LO-T-D",
        "as top short bars")
    row("BOXED", "YES (value + detail)", "NO", "PARTIAL (shape drawn, not dimensioned)", "NO", "YES",
        "BLOCKED_COMPONENT",
        "11 values 3+4/3+5/3+6/3+8 + FN empty; semantics UNRESOLVED after source exhaustion (04)",
        "owner / engineer answer to Q-R3-6; until then BLOCKED_UNQUANTIFIED on 12 footing types (FT incl. FN)")
    row("starters / dowels", "YES (p.13 40Ø, min 30 cm foot)", "YES", "YES", "YES", "YES", "NOT_APPLICABLE",
        "column starters are owned by COLUMN_REBAR (S3.1 lap / starter register); S4 must not count them again", "")
    row("cover", "YES (p.8 note 22: 7 cm soil contact)", "YES", "N/A", "YES", "PARTIAL", "READY",
        "R4 visual claim P08_NOTE_22_COVER (OCR + review)", "S4 records COVER rule id on every bar")
    row("bar length", "YES", "YES", "YES", "YES", "PARTIAL", "READY",
        "bottom bars straight between side legs (p.13): length = footing dimension - 2 x cover", "")
    row("hooks", "YES (none drawn on bottom bars)", "YES", "YES", "YES", "PARTIAL", "READY",
        "p.13 draws straight bottom bars; FTB top-bar ends not drawn", "FTB top-bar end detail -> lower bound")
    row("anchorage", "YES (note 9)", "YES", "N/A", "N/A", "NO", "NOT_APPLICABLE",
        "footing mesh bars end at cover; anchorage applies to starters (column engine)", "")
    row("laps", "YES (note 9)", "YES", "YES", "YES", "PARTIAL", "NOT_APPLICABLE",
        "longest footing bar 4.46 m (FF 460 cm - 2 x 7) < 12 m stock: no lap", "re-check if a longer footing appears")
    row("unit mass", "YES", "YES", "N/A", "YES (D^2/162)", "YES", "READY", "rebar_model.kgm / rebar_unit_mass", "")
    row("waste", "NO (owner / estimating parameter)", "NO", "N/A", "YES (waste_procurement)", "YES",
        "PROVISIONAL_ONLY", "kept out of the accurate net quantity", "owner waste % for procurement view")
    row("procurement", "NO", "NO", "N/A", "YES (bbs_optimiser 12 m stock)", "YES", "PROVISIONAL_ONLY",
        "cutting / stock optimisation is a procurement view, never the accurate net", "")
    row("provenance", "YES", "YES", "N/A", "N/A", "YES", "READY",
        "accurate_boq_rebar.validate_s4_part / summarise_s4 (contract 05)", "")
    row("release states", "YES", "YES", "N/A", "N/A", "YES", "READY",
        "footing_rebar_guard.footing_release: VERIFIED / LOWER_BOUND / PROVISIONAL / BLOCKED", "")
    return R


# ------------------------------------------------------------------ writers
def _csv(path, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    path.write_text(buf.getvalue(), encoding="utf-8")


def _json(path, obj):
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main(dxf):
    D = read_dxf(dxf)
    tab, grid = read_table(D)
    if tab["state"] != ST.COMPLETE:
        raise SystemExit(f"schedule table not COMPLETE: {tab['unplaced']}")
    leaves = headers_by_x(tab)
    defs = {r["footing_type"]: r for r in _j(S1 / "FOOTING_DEFINITION_REGISTER.json")["rows"]}
    occ = _j(S1 / "FOOTING_OCCURRENCE_REGISTER.json")
    r4 = _j(R4_CAPTURE)
    occ_count = Counter(r["type"] for r in occ["rows"] if r["type"])
    tok = token_register(D, tab, leaves, defs, occ_count)
    cen, cen_chk = census(D, tab, leaves, defs, occ, r4)
    bx, diag_rows = boxed(D, tab, leaves, defs, occ, r4)
    diag = diagnostics(diag_rows)
    hb = header_bindings(D, tab)
    rm = readiness(cen_chk, tok, hb, diag, occ)
    _csv(PKG / "01_FOOTING_TOKEN_PARITY_REGISTER.csv", tok)
    _csv(PKG / "02_FOOTING_ANNOTATION_CENSUS.csv", cen)
    _csv(PKG / "03_BOXED_OCCURRENCES.csv", bx)
    _csv(PKG / "06_S4_READINESS_MATRIX.csv", rm)
    summary = {
        "round": ROUND, "baseline": BASELINE, "drawing": {"ST7757.dxf": DXF_SHA, "ST7757.pdf": PDF_SHA},
        "guard_policy": FG.policy_record(),
        "schedule_table": {"state": tab["state"], "bands": len(tab["bands"]), "grid": grid,
                           "header_leaves": [lab for _, _, lab in leaves], "digest": ST.digest(tab)},
        "block_templates": D["blocks"], "boxed_text_hits": D["boxed_text_hits"],
        "token_parity": {"tokens": len(tok), "by_decision": dict(Counter(r["S4_DECISION"] for r in tok)),
                         "by_class": dict(sorted(Counter(r["TOKEN_CLASS"] for r in tok).items())),
                         "by_parity": dict(sorted(Counter(r["PARITY_STATUS"] for r in tok).items())),
                         "bar_tokens_admitted": sum(1 for r in tok if r["S4_DECISION"] == "ADMITTED"),
                         "joined_form_parity": dict(Counter(r["JOINED_FORM_PARITY"] for r in tok))},
        "census": {k: cen_chk[k] for k in ("source_items", "terminal_items", "conserved", "unterminated",
                                           "double_terminations", "unknown_terminations", "blocked_with_quantity",
                                           "by_terminal_state", "by_type")},
        "header_binding": {"rows": hb, "bound": sum(r["state"] == "BOUND_BY_HEADER" for r in hb), "total": len(hb)},
        "boxed": {"occurrences": len(bx), "values": dict(Counter(r["RAW_VALUE"] for r in bx if r["BLOCK"] == "FT")),
                  "terminal_classification": FG.UNRESOLVED, "component_existence": FG.SOURCE_EXPLICIT,
                  "diagnostics": diag, "hypotheses": HYPOTHESES},
        "count_queries": COUNT_QUERIES,
        "readiness": dict(Counter(r["S4_STATUS"] for r in rm)),
    }
    _json(PKG / "PRE_S4_SUMMARY.json", summary)
    files = {}
    for p in sorted(PKG.iterdir()):
        if p.is_file() and p.name != "INDEX.json":
            files[p.name] = _sha(p)
    _json(PKG / "INDEX.json", {"round": ROUND, "baseline": BASELINE, "files": files})
    print(json.dumps({"tokens": len(tok), "census": summary["census"]["source_items"],
                      "conserved": summary["census"]["conserved"], "boxed": len(bx),
                      "header_bound": f"{summary['header_binding']['bound']}/{len(hb)}"}, indent=0))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
