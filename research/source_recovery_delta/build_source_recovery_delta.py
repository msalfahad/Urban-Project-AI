"""SOURCE RECOVERY DELTA: S4 / S5 / S6 unresolved project-source exhaustion (second pass, no recalculation).

The project engineer states that the reinforcement information is contained in the issued construction plan set.
This round records that statement as a versioned PROJECT_ENGINEER_CLAIM (it authorises no assumption) and runs a
second, graphics-first search of the issued set for every unresolved or blocked S4 / S5 / S6 component:

    ST7757.dxf  plans + schedules (pp.1-7, 9-12): TEXT / MTEXT / ATTRIB / ATTDEF / DIMENSION / block geometry
    ST7757.pdf  issued plot; details pp.13-16 and schedules pp.9-12 read as VECTOR strokes per CAD layer (pypdf)
    P7757.dxf   architectural plans (FOLLOW ARCH references: level marks)

Every item gets exactly one terminal state (SOURCE_FOUND_EXPLICIT, SOURCE_FOUND_DERIVED, SOURCE_CONFLICT,
SOURCE_EXPECTED_NOT_LOCATED, PENDING_ENGINEER_CLARIFICATION, GENERIC_CODE_QA_ONLY). A graphical rule is DERIVED
only when its target is unambiguous, its dimensions bind, repeated examples agree and no project source contradicts
it (brief §6); the builder asserts each vector fact it relies on and stops if one does not hold.

The frozen S4 / S5 / S6 packages are read, hash-checked against their freeze manifests and never written. No kg is
computed here: the S4.1 / S5.1 / S6.1 candidate files name state changes and the components they would unlock.
No reference quantity, external engine or generic code value is read. PDF reading uses pypdf only (vector_pdf.py);
the engine PDF stack is not touched.

Run:  python3 -I research/source_recovery_delta/build_source_recovery_delta.py
"""

from __future__ import annotations

import collections
import csv
import hashlib
import io
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import ezdxf  # noqa: E402
from ezdxf import bbox as ezbbox  # noqa: E402

from engine.source import legacy_text  # noqa: E402
import vector_pdf as V  # noqa: E402

ROUND = "SOURCE_RECOVERY_DELTA_S4_S5_S6"
POLICY = "SOURCE_RECOVERY_DELTA_V1"
CLAIM_DATE = "2026-10-08"
TERMINAL = ("SOURCE_FOUND_EXPLICIT", "SOURCE_FOUND_DERIVED", "SOURCE_CONFLICT", "SOURCE_EXPECTED_NOT_LOCATED",
            "PENDING_ENGINEER_CLARIFICATION", "GENERIC_CODE_QA_ONLY")
NODE_KINDS = ("OCCURRENCE_COMPONENT", "SCHEDULE_CELL", "DETAIL_REFERENCE", "TYPICAL_DETAIL", "GENERAL_NOTE",
              "ARCHITECTURAL_REFERENCE")
INPUTS = {
    "ST7757.dxf": "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079",
    "ST7757.pdf": "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3",
    "P7757.dxf": "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4",
}
FROZEN = {
    "S4": ("research/alsenan_footing_rebar_s4", "S4_FREEZE_MANIFEST.json"),
    "S5": ("research/alsenan_ground_system_rebar_s5", "S5_FREEZE_MANIFEST.json"),
    "S6": ("research/alsenan_superstructure_beam_rebar_s6", "S6_FREEZE_MANIFEST.json"),
}
STR_ICON_ROWS = ("B17", "B19", "B20", "B21", "B22", "B23", "B24", "B25", "B26")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def src(name):
    p = ROOT / "data" / "inputs" / "by_sha256" / f"{INPUTS[name]}{Path(name).suffix.lower()}"
    if sha(p) != INPUTS[name]:
        raise SystemExit(f"input {name} does not match its sha256")
    return p


def rows_of(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def check(cond, what):
    if not cond:
        raise SystemExit(f"evidence check failed: {what}")
    return True


# ---------------------------------------------------------------------------------------------- frozen baselines
def frozen_baselines():
    out = {}
    for stage, (pkg, man) in FROZEN.items():
        m = json.loads((ROOT / pkg / man).read_text(encoding="utf-8"))
        for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", ROOT / pkg)):
            for k, h in m[group].items():
                check(sha(base / k) == h, f"{stage} frozen {group} {k} unchanged")
        out[stage] = {"package": pkg, "manifest": man, "manifest_sha256": sha(ROOT / pkg / man),
                      "engine_commit_stamp": m["engine_commit_stamp"], "state": m["state"]}
    return out


# ------------------------------------------------------------------------------------------------- DXF evidence
def dxf_evidence(doc):
    msp = doc.modelspace()
    ev = {}

    # E-DXF-01 FT / FTB block templates: no diameter glyph before BOXED; FN cleared the default
    ft = doc.blocks.get("FT")
    ft_texts = [e.dxf.text for e in ft if e.dxftype() == "TEXT"]
    ft_attdef = {e.dxf.tag: e.dxf.text for e in ft if e.dxftype() == "ATTDEF"}
    ftb_attdef = {e.dxf.tag: e.dxf.text for e in doc.blocks.get("FTB") if e.dxftype() == "ATTDEF"}
    boxed = {}
    for ins in msp.query('INSERT[name=="FT"]'):
        a = {x.dxf.tag: x.dxf.text for x in ins.attribs}
        boxed[a.get("FO-TY")] = {"handle": ins.dxf.handle, "BOXED": a.get("BOXED")}
    check(ft_texts.count("%%C") == 2 and ft_attdef.get("BOXED") == "3+-", "FT template: 2 Ø glyphs, BOXED '3+-'")
    check(boxed["FN"]["BOXED"] == "", "FN BOXED cell cleared")
    check(ftb_attdef.get("BOXED-T") == "TOP" and ftb_attdef.get("BOXED-B") == "BOT", "FTB BOXED column = labels")
    ev["E-DXF-01"] = {"id": "E-DXF-01", "channel": "DXF_BLOCK_TEMPLATE", "source": "ST7757.dxf blocks FT / FTB",
                      "handles": sorted(v["handle"] for v in boxed.values()),
                      "facts": {"FT_diameter_glyphs": ft_texts.count("%%C"), "FT_BOXED_default": "3+-",
                                "FTB_BOXED_defaults": ["TOP", "BOT"],
                                "BOXED_values": {k: v["BOXED"] for k, v in sorted(boxed.items())}},
                      "reading": "the BOXED column has no diameter glyph and no count / diameter pair; the leading "
                                 "'3' is template text; two-layer rows hold layer labels; FN cleared the default"}

    # E-DXF-02 whole-drawing text search: no boxed / anchorage / hook / development / concentrated-load definition
    texts = []
    for e in msp:
        if e.dxftype() in ("TEXT", "MTEXT"):
            texts.append((e.dxf.handle, e.dxf.text if e.dxftype() == "TEXT" else e.plain_text()))
    for b in doc.blocks:
        for e in b:
            if e.dxftype() in ("TEXT", "MTEXT", "ATTDEF"):
                texts.append((e.dxf.handle, e.dxf.text if e.dxftype() != "MTEXT" else e.plain_text()))
    for ins in msp.query("INSERT"):
        texts += [(a.dxf.handle, a.dxf.text) for a in ins.attribs]
    probes = {"BOX": ["BOXED"], "HOOK": [], "ANCHOR": [], "DEVELOP": [], "LAP": [], "SPLICE": [], "CONCENTR": [],
              "LEG": [], "CANTILEVER": [], "RING": [], "CURV": []}
    hits = {k: sorted({t for _, t in texts if t and k in t.upper()}) for k in probes}
    for k, allowed in probes.items():
        check(set(hits[k]) <= set(allowed), f"text probe {k}: {hits[k]}")
    ev["E-DXF-02"] = {"id": "E-DXF-02", "channel": "DXF_TEXT_ALL", "source": "ST7757.dxf modelspace + 420 blocks + ATTRIBs",
                      "handles": [], "facts": {"texts_scanned": len(texts), "probe_hits": hits},
                      "reading": "no TEXT / MTEXT / ATTRIB / ATTDEF in the drawing defines boxed bars, hooks, "
                                 "anchorage, development, laps, concentrated load, link legs, cantilever or ring-beam "
                                 "detailing; 'BOXED' occurs only as the schedule header"}

    # E-DXF-03 STR2 / str3 REMARKS icons = nested closed links with hook ticks; row binding
    icons = {}
    for nm in ("STR2", "str3"):
        blk = doc.blocks.get(nm)
        rects = [e for e in blk if e.dxftype() == "LWPOLYLINE" and e.closed and len(e) == 4]
        ticks = [e for e in blk if e.dxftype() == "LINE"]
        icons[nm] = {"closed_rectangles": len(rects), "hook_tick_lines": len(ticks),
                     "rect_widths": sorted(round(max(p[0] for p in r.get_points()) - min(p[0] for p in r.get_points()))
                                           for r in rects),
                     "rect_heights": sorted({round(max(p[1] for p in r.get_points()) - min(p[1] for p in r.get_points()))
                                             for r in rects})}
    check(icons["STR2"]["closed_rectangles"] == 2 and icons["STR2"]["hook_tick_lines"] == 4, "STR2 = 2 links")
    check(icons["str3"]["closed_rectangles"] == 3 and icons["str3"]["hook_tick_lines"] == 6, "str3 = 3 links")
    sbt = sorted(((ins.dxf.insert.y, {x.dxf.tag: x.dxf.text for x in ins.attribs}, ins.dxf.handle)
                  for ins in msp.query('INSERT[name=="SBT"]')), key=lambda r: -r[0])
    placed = []
    for ins in msp.query("INSERT"):
        if ins.dxf.name in ("STR2", "str3"):
            y = ins.dxf.insert.y
            row = min(sbt, key=lambda r: abs((r[0] - y) - 323))   # icons sit one half row (311-336) below the row insert
            check(abs((row[0] - y) - 323) < 20, f"icon {ins.dxf.handle} binds one schedule row")
            placed.append({"icon": ins.dxf.name, "handle": ins.dxf.handle, "row": row[1]["BEAM"],
                           "row_handle": row[2], "dy": round(row[0] - y, 1)})
    rows_with = sorted({p["row"] for p in placed if p["row"].startswith("B")})
    check(tuple(rows_with) == STR_ICON_ROWS, f"icon rows {rows_with}")
    ev["E-DXF-03"] = {"id": "E-DXF-03", "channel": "DXF_BLOCK_GEOMETRY", "source": "ST7757.dxf blocks STR2 / str3, "
                      "SBT REMARKS column (p.10)", "handles": sorted(p["handle"] for p in placed),
                      "facts": {"icons": icons, "placements": sorted(placed, key=lambda p: p["handle"])},
                      "reading": "STR2 = an outer closed rectangle + one inner closed rectangle of the same height, "
                                 "each with a pair of hook ticks at a top corner (2 links, 4 vertical legs); str3 = "
                                 "outer + two inner (3 links, 6 legs). Same symbol as the labelled closed links of the "
                                 "p.13 sections (closed rectangle + corner hook). Inner-link width is not dimensioned."}

    # E-DXF-04 SB2: two schedule rows; only one is inside the issued schedule sheet frame
    frame = doc.entitydb["1B2D"]
    fb = ezbbox.extents([frame])
    sb2 = {r[2]: {"y": round(r[0]), "W": r[1]["W"], "H": r[1]["H"], "TOP": f"{r[1]['TOP-B']}Ø{r[1]['TOP-D']}",
                  "BOT": f"{r[1]['BOT-B']}Ø{r[1]['BOT-D']}", "inside_sheet_frame": bool(fb.extmin.y <= r[0] <= fb.extmax.y)}
           for r in sbt if r[1].get("BEAM") == "SB2"}
    check(set(sb2) == {"1FBB", "2ABA"} and sb2["2ABA"]["inside_sheet_frame"] and not sb2["1FBB"]["inside_sheet_frame"],
          "SB2 rows vs sheet frame")
    ev["E-DXF-04"] = {"id": "E-DXF-04", "channel": "DXF_SHEET_EXTENT", "source": "ST7757.dxf SBT rows 1FBB / 2ABA, "
                      "DEFPOINTS sheet frame 1B2D (SCHEDULES 1, PDF p.10)", "handles": ["1FBB", "2ABA", "1B2D"],
                      "facts": {"rows": sb2, "sheet_frame_y": [round(fb.extmin.y), round(fb.extmax.y)]},
                      "reading": "row 2ABA (100x50) lies inside the schedules sheet frame and is the only SB2 row on "
                                 "the issued PDF p.10; row 1FBB (80x50) lies below the frame in model space and is "
                                 "not on the issued sheet"}

    # E-DXF-05 FF lift pit on the foundation plan: closed square bearing walls 1.8 / 2.2 m
    bw = {h: ezbbox.extents([doc.entitydb[h]]) for h in ("10EA", "10EB")}
    sizes = {h: [round(b.size.x), round(b.size.y)] for h, b in bw.items()}
    check(sizes == {"10EA": [1800, 1800], "10EB": [2200, 2200]}, "FF pit walls 1.8 / 2.2 m")
    check(doc.entitydb["1676"].dxf.text == "FF", "FF tag")
    ev["E-DXF-05"] = {"id": "E-DXF-05", "channel": "DXF_GEOMETRY", "source": "ST7757.dxf foundation plan: S-BW "
                      "polylines 10EA / 10EB around tag 1676 'FF', footing outline 1B2B", "handles": ["10EA", "10EB",
                      "1676", "1B2B"], "facts": {"pit_wall_inner_mm": 1800, "pit_wall_outer_mm": 2200,
                                                  "wall_thickness_mm": 200, "walls": 4},
                      "reading": "the lift pit is a closed square of four 20 cm bearing walls (inner 1.80 m, outer "
                                 "2.20 m); the p.14 section cuts two of them"}

    # E-DXF-06 CB typical figures are not to scale: printed factors do not reproduce the drawn lengths
    dims = {}
    for d in msp.query("DIMENSION"):
        t = d.dxf.get("text", "")
        if t in ("0.22 Ln", "0.3 Ln2", "0.15L", "Ln", "L", "7.5cm"):
            dims.setdefault(t, set()).add(round(d.get_measurement(), 2))
    ratio = {"0.22 Ln": round(max(dims["0.22 Ln"]) / max(dims["Ln"]), 4),
             "0.3 Ln2": round(max(dims["0.3 Ln2"]) / max(dims["Ln"]), 4),
             "0.15L": round(max(dims["0.15L"]) / max(dims["L"]), 4)}
    check(abs(ratio["0.22 Ln"] - 0.22) > 0.02 and abs(ratio["0.15L"] - 0.15) > 0.02, "CB typicals N.T.S.")
    ev["E-DXF-06"] = {"id": "E-DXF-06", "channel": "DXF_DIMENSION_MEASUREMENT", "source": "ST7757.dxf CB typical "
                      "figures (C-BEAM2 / C-BEAM3 headers, pp.11-12)", "handles": ["2785", "20C6", "222D", "2798",
                      "20D9", "225A", "2282"], "facts": {"measured_mm": {k: sorted(v) for k, v in sorted(dims.items())},
                                                        "drawn_ratio": ratio},
                      "reading": "the drawn lengths do not reproduce the printed factors (drawn 0.2593 Ln for '0.22 "
                                 "Ln', 0.0918 L for '0.15L', 697 mm for '7.5cm'): the figures are N.T.S., so neither "
                                 "'0.3 Ln2' in the 2-span figure nor the span meant by '0.15L' can be read off by scale"}

    # E-DXF-07 WITH STAIR tags sit on B3; the B3 schedule row
    ws = {}
    for h, b3 in (("6B6", "6B7"), ("6B8", "6B9"), ("1826", "1827")):
        e, t = doc.entitydb[h], doc.entitydb[b3]
        check(e.dxf.text == "(With Stair)" and t.dxf.text == "B3", f"{h} WITH STAIR + {b3} B3")
        ws[h] = {"tag": b3, "distance": round(math.dist((e.dxf.insert.x, e.dxf.insert.y), (t.dxf.insert.x, t.dxf.insert.y)))}
    b3row = next(r[1] for r in sbt if r[1].get("BEAM") == "B3")
    check((b3row["W"], b3row["H"], b3row["BOT-B"], b3row["BOT-D"], b3row["TOP-B"], b3row["TOP-D"], b3row["STI-B"],
           b3row["D"]) == ("20", "40", "4", "16", "2", "12", "6", "8"), "B3 row")
    ev["E-DXF-07"] = {"id": "E-DXF-07", "channel": "DXF_TEXT", "source": "ST7757.dxf plan tags + SBT row B3",
                      "handles": ["6B6", "6B7", "6B8", "6B9", "1826", "1827"],
                      "facts": {"with_stair_tags": ws, "B3_row": {"W": 20, "H": 40, "BOTTOM": "4Ø16", "TOP": "2Ø12",
                                                                   "STIRRUPS": "6Ø8/m"}},
                      "reading": "every '(With Stair)' qualifier sits beside a B3 tag; B3 = 20x40, 4Ø16 bottom, 2Ø12 "
                                 "top, 6Ø8/m"}

    # E-DXF-08 legacy-Arabic plan notes (re-decoded): exterior GB note, lift footing remark, soil notes
    notes = {}
    for h in ("B8", "1C64", "1E11", "1E12", "1B33", "1E10", "1E0E", "C8"):
        d = legacy_text.decode(doc.entitydb[h].dxf.text, legacy_text.ARABIC_KEYBOARD_101)
        notes[h] = {"text": d["text"], "state": d["state"], "layer": doc.entitydb[h].dxf.layer}
    check("الشناجات الخارجية" in notes["B8"]["text"] and "مصعد" in notes["1C64"]["text"], "Arabic notes decode")
    ev["E-DXF-08"] = {"id": "E-DXF-08", "channel": "DXF_TEXT (legacy Arabic decoded, engine.source.legacy_text)",
                      "source": "ST7757.dxf S-NOTE / S-TEXT.SCH texts", "handles": sorted(notes), "facts": notes,
                      "reading": "B8: exterior ground beams on the neighbour side are cast above and below a block "
                                 "wall built from foundation level (no depth, no bars); 1C64: FF REMARKS = 'lift "
                                 "base'; soil notes give founding / soil data only. None defines GB depth, development "
                                 "or a concentrated load."}

    # E-DXF-09 the '******' marks: plain text, no legend; '*' elsewhere is a note bullet only
    stars = {h: {"text": doc.entitydb[h].dxf.text, "layer": doc.entitydb[h].dxf.layer,
                 "xy": [round(doc.entitydb[h].dxf.insert.x), round(doc.entitydb[h].dxf.insert.y)]} for h in ("165A", "165B")}
    bullets = sorted({t for _, t in texts if t and t.strip().startswith("*") and t.strip() != "******"})
    check(all(s["text"] == "******" for s in stars.values()), "stars")
    ev["E-DXF-09"] = {"id": "E-DXF-09", "channel": "DXF_TEXT + neighbourhood", "source": "ST7757.dxf GBP sheet",
                      "handles": ["165A", "165B"], "facts": {"marks": stars, "other_star_texts": bullets},
                      "reading": "both marks sit at ground-beam junctions next to underlay strokes on layer '2'; the "
                                 "set has no legend for them; every other '*' text is a note bullet"}

    # E-DXF-10 F / F10 (carried, no new evidence) - footing schedule rows F and F10 both exist
    ftr = {k: v for k, v in boxed.items() if k in ("F", "F10")}
    ev["E-DXF-10"] = {"id": "E-DXF-10", "channel": "DXF_ATTRIB", "source": "ST7757.dxf FT rows F / F10",
                      "handles": sorted(v["handle"] for v in ftr.values()), "facts": ftr,
                      "reading": "no new project source bears on the F / F10 occurrence conflict"}
    return ev, sbt


def arch_evidence(path):
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    levels = collections.Counter()
    buildup = []
    for e in msp:
        if e.dxftype() == "TEXT":
            t = e.dxf.text.strip()
            if t.startswith(("+", "%%p", "-")) and any(c.isdigit() for c in t):
                levels[t] += 1
            if any(k in t.upper() for k in ("SCREED", "TILE", "SAND", "BUILD", "F.F.L", "FFL", "N.G.L", "SECTION")):
                buildup.append(t)
    check(not buildup, f"arch build-up text {buildup}")
    return {"E-ARCH-01": {"id": "E-ARCH-01", "channel": "DXF_TEXT (architectural)", "source": "P7757.dxf",
                          "handles": [], "facts": {"level_marks": dict(sorted(levels.items())), "build_up_texts": 0},
                          "reading": "the architectural DXF carries level marks only (+0.15 / +0.30 / +1.00 / ±0.00); "
                                     "no floor build-up, no section and no ground-beam depth"}}


# ------------------------------------------------------------------------------------------------- PDF evidence
def _topology(comp, tol=0.3):
    pts, edges, deg = [], set(), collections.Counter()

    def cid(p):
        for i, q in enumerate(pts):
            if math.dist(p, q) < tol:
                return i
        pts.append(p)
        return len(pts) - 1
    for s in comp:
        a, b = cid(s[2]), cid(s[3])
        if a != b and frozenset((a, b)) not in edges:
            edges.add(frozenset((a, b)))
            deg[a] += 1
            deg[b] += 1
    return dict(sorted(collections.Counter(deg.values()).items()))


def _r(p):
    return [round(v, 1) for v in p]


def pdf_evidence(pdf):
    ev = {}
    p13, p14, p11, p12, p15 = (V.paths(pdf, n) for n in (13, 14, 11, 12, 15))

    # E-PDF-01 p.13 isolated-footing details: 'Long bars' = U bar with up legs + 45° hooks; 'Boxed bars' = inverted U
    details = {}
    for name, box in (("SHALLOW", (380, 181, 820, 671)), ("DEEP", (380, 671, 820, 1161))):
        comps = V.components(V.segments(p13, box, {"S-REIN.D"}))
        outer = [c for c in comps if len(c) == 3 and V.length(c) > 250]
        inner = [c for c in comps if len(c) == 5 and V.length(c) > 250]
        check(len(outer) == 1 and len(inner) == 1, f"p.13 {name}: one inverted-U and one U bar")
        o, i = outer[0], inner[0]
        base = max(i, key=lambda s: math.dist(s[2], s[3]))
        legs = sorted((s for s in i if 30 < math.dist(s[2], s[3]) < math.dist(base[2], base[3])),
                      key=lambda s: s[2][1])
        hooks = [s for s in i if math.dist(s[2], s[3]) < 8]
        top = max(o, key=lambda s: math.dist(s[2], s[3]))
        olegs = [s for s in o if s is not top]
        check(len(legs) == 2 and len(hooks) == 2, f"p.13 {name}: U bar = base + 2 legs + 2 hooks")
        check(all(abs(abs(h[2][0] - h[3][0]) - abs(h[2][1] - h[3][1])) < 0.2 for h in hooks), "45° hooks")
        check(all(min(math.dist(p, q) for p in (s[2], s[3]) for q in (base[2], base[3])) < 0.2 for s in legs),
              f"p.13 {name}: legs share the base vertices")
        bot_level = base[2][0]
        check(all(abs(min(s[2][0], s[3][0]) - bot_level) < 0.2 for s in olegs), "boxed legs reach bottom-bar level")
        long_leader = V.leaders_onto(p13, (base[2], base[3]), box)
        boxed_leader = V.leaders_onto(p13, (top[2], top[3]), box)
        check(len(long_leader) == 1 and len(boxed_leader) == 1, f"p.13 {name}: one leader each")
        dots = [c for c in comps if V.is_dot(c) and abs(V.bbox(c)[0] - bot_level) < 1.0]
        details[name] = {"long_bar_U": {"base": [_r(base[2]), _r(base[3])], "legs": [[_r(s[2]), _r(s[3])] for s in legs],
                                        "hooks_45deg": [[_r(s[2]), _r(s[3])] for s in hooks],
                                        "leg_length_pt": [round(math.dist(s[2], s[3]), 1) for s in legs]},
                         "boxed_inverted_U": {"top": [_r(top[2]), _r(top[3])],
                                              "legs": [[_r(s[2]), _r(s[3])] for s in olegs], "hooks": 0},
                         "leader_on_long_bar": long_leader, "leader_on_boxed_bar": boxed_leader,
                         "bottom_bar_dots_in_section": len(dots)}
    ev["E-PDF-01"] = {"id": "E-PDF-01", "channel": "PDF_VECTOR (S-REIN.D) + visual label reading", "page": 13,
                      "source": "ST7757.pdf p.13 'TYP. DETAIL OF ISOLATED FOOTING' (with and without the >2.5 m "
                                "lower ground beam)", "handles": ["p13:S-REIN.D"], "facts": details,
                      "reading": "in BOTH footing details the bar labelled 'Long bars' is one drawn U: its bottom run "
                                 "shares exact vertices with two vertical legs that rise to just under the top bar and "
                                 "end in 45° hooks. The bar labelled 'Boxed bars.' is an inverted U: top run under the "
                                 "top face with two legs down to the bottom-bar level, no hooks. Short bars are drawn "
                                 "only as dots (seen in section). Leg and hook lengths are not dimensioned."}

    # E-PDF-02 p.13 ground-beam sections: one closed link + hook per section; the 30x30 link has no label leader
    secs = {}
    box = (50, 181, 340, 621)
    comps = V.components(V.segments(p13, box, {"S-REIN.D"}))
    links = [c for c in comps if not V.is_dot(c) and V.length(c) > 60]
    check(len(links) == 4, "four GB section links")
    others = [s for s in V.segments(p13, box) if s[0] != "S-REIN.D" and math.dist(s[2], s[3]) >= 8]
    names = {(30, 60): "GB_GT_5M (30x60)", (30, 30): "GB_LT_2_5M (30x30)", (30, 40): "GB_LT_5M (30x40)"}
    for c in links:
        bb = V.bbox(c)
        topo = _topology(c)
        check(set(topo) <= {1, 2, 3} and topo.get(1, 0) == topo.get(3, 0) >= 1, "closed link + hook branch")
        lead = 0
        for s in others:
            for e, o in ((s[2], s[3]), (s[3], s[2])):
                if min(V.point_to_segment(e, t[2], t[3]) for t in c) < 1.0 and \
                        min(V.point_to_segment(o, t[2], t[3]) for t in c) > 5:
                    lead += 1
        wpt, hpt = round(bb[3] - bb[1], 1), round(bb[2] - bb[0], 1)    # page is rotated: x = depth
        r = hpt / wpt                                                   # drawn depth / width of the link
        key = (names[(30, 30)] if r < 1.15 else names[(30, 40)] if r < 1.7 else names[(30, 60)] if r < 3.0
               else "GB_EXTERIOR (30 x FOLLOW ARCH)")
        check(key not in secs, f"one link per section ({key})")
        secs[key] = {"bbox_pt": _r(bb), "topology_degree_counts": topo, "links": 1,
                     "hook_branches": topo.get(3, 0), "label_leaders_on_link": lead}
    check(secs["GB_LT_2_5M (30x30)"]["label_leaders_on_link"] == 0, "30x30 link unlabelled")
    check(all(v["label_leaders_on_link"] == 1 for k, v in secs.items() if "2_5" not in k), "other links labelled")
    ev["E-PDF-02"] = {"id": "E-PDF-02", "channel": "PDF_VECTOR (S-REIN.D + leader strokes)", "page": 13,
                      "source": "ST7757.pdf p.13 ground-beam sections (1:20)", "handles": ["p13:S-REIN.D"],
                      "facts": secs,
                      "reading": "each of the four sections draws exactly one closed link (2 vertical legs) with a "
                                 "hook (one or two short strokes) at one corner; the >5 m, <5 m and exterior links each carry one label "
                                 "leader (Ø8/15cm); the <2.5 m (30x30) link has NO label leader - its diameter and "
                                 "spacing are not printed. Hook extension is not dimensioned."}

    # E-PDF-03 p.14 lift footing: '2 Ø16' = 2 bars at top + 2 at bottom mesh level inside each cut pit wall
    box = (420, 751, 790, 1171)
    comps = V.components(V.segments(p14, box, {"S-REIN.D"}))
    dots = sorted(((round((V.bbox(c)[0] + V.bbox(c)[2]) / 2, 1), round((V.bbox(c)[1] + V.bbox(c)[3]) / 2, 1))
                   for c in comps if V.is_dot(c)))
    walls = sorted((V.bbox(c) for c in comps if not V.is_dot(c) and V.length(c) > 400 and V.bbox(c)[3] - V.bbox(c)[1] < 25),
                   key=lambda b: b[1])
    loop = [c for c in comps if not V.is_dot(c) and V.bbox(c)[3] - V.bbox(c)[1] > 300]
    check(len(walls) == 2 and len(loop) == 1, "two pit walls + one footing loop")
    lb = V.bbox(loop[0])
    top_level, bot_level = lb[2] - 2.7, lb[0] + 2.6
    per_wall = []
    for w in walls:
        inside = [d for d in dots if w[1] < d[1] < w[3] and (abs(d[0] - top_level) < 1.5 or abs(d[0] - bot_level) < 1.5)]
        per_wall.append({"wall_band_y": [round(w[1], 1), round(w[3], 1)], "top": sum(abs(d[0] - top_level) < 1.5 for d in inside),
                         "bottom": sum(abs(d[0] - bot_level) < 1.5 for d in inside)})
    check(all(p["top"] == 2 and p["bottom"] == 2 for p in per_wall), "2+2 bars inside each wall band")
    lead_hits = collections.defaultdict(list)
    for s in V.segments(p14, box):
        if s[0] == "S-REIN.D" or math.dist(s[2], s[3]) < 10:
            continue
        for e, o in ((s[2], s[3]), (s[3], s[2])):
            for d in dots:
                if math.dist(e, d) < 3.2:
                    lead_hits[_r(o).__str__()].append(d)
    two16 = [v for v in lead_hits.values() if len(v) == 2 and all(walls[1][1] < d[1] < walls[1][3] for d in v)]
    check(len(two16) == 2, "two '2Ø16' leaders, each to two bars under one wall")
    topo = _topology(loop[0])
    ev["E-PDF-03"] = {"id": "E-PDF-03", "channel": "PDF_VECTOR (S-REIN.D + leader strokes) + visual / OCR label",
                      "page": 14, "source": "ST7757.pdf p.14 'DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT)'",
                      "handles": ["p14:S-REIN.D"],
                      "facts": {"bars_per_cut_wall": per_wall, "two_16_leaders": [sorted(v) for v in two16],
                                "footing_loop_topology": topo, "ocr_raw": ["2 916", "2 616"]},
                      "reading": "the two '2 Ø16' leaders end on two bar dots each: the pair at the footing TOP mesh "
                                 "level and the pair at the BOTTOM mesh level, both inside the footprint of the cut "
                                 "pit wall (between its two vertical bar lines); the other cut wall repeats the same "
                                 "2 + 2 dots unlabelled. They are wall-base bars inside the footing, running along the "
                                 "wall (seen in section), not footing-side bars. Their length is not dimensioned. The "
                                 "two-layer footing bars are drawn as one closed rounded loop, but the schedule gives "
                                 "6/m top against 9/m bottom, so the loop cannot pair the layers bar for bar."}

    # E-PDF-04 CB typical figures: the top bar bends down at each end support to the bottom-bar level
    legs = []
    for page, P, boxes in ((11, p11, ((615, 741, 715, 1031), (615, 290, 715, 580))), (12, p12, ((600, 400, 700, 900),))):
        for box in boxes:
            cs = V.components(V.segments(P, box, {"S-REIN.D"}))
            bottoms = [c[0] for c in cs if len(c) == 1 and math.dist(c[0][2], c[0][3]) > 120]
            ls = [c for c in cs if len(c) == 2 and V.length(c) > 60 and
                  sorted(abs(s[2][0] - s[3][0]) < 0.1 for s in c) == [False, True]]   # an L: one run + one leg
            check(len(ls) == 2 and bottoms, f"p.{page} {box}: two end-support top bars with legs")
            blev = sorted({round(min(b[2][0], b[3][0]), 1) for b in bottoms})
            for c in ls:
                run = max(c, key=lambda s: math.dist(s[2], s[3]))
                leg = min(c, key=lambda s: math.dist(s[2], s[3]))
                foot = min(leg[2][0], leg[3][0])
                near = min(abs(foot - b) for b in blev)
                check(near < 3.0, f"p.{page}: leg reaches the bottom-bar level ({near})")
                legs.append({"page": page, "top_level_x": round(run[2][0], 1), "leg_foot_x": round(foot, 1),
                             "bottom_bar_levels_x": blev, "gap_to_bottom_bar_pt": round(near, 1)})
    ev["E-PDF-04"] = {"id": "E-PDF-04", "channel": "PDF_VECTOR (S-REIN.D)", "page": "11-12",
                      "source": "ST7757.pdf p.11 (two 2-span typicals) and p.12 (3-span typical)",
                      "handles": ["p11:S-REIN.D", "p12:S-REIN.D"], "facts": {"end_support_top_bar_legs": legs},
                      "reading": "in all three CB typical figures the top bar at each END support turns down in one "
                                 "90° leg whose foot ends at the bottom-bar level (within 2.3 pt); bottom bars are "
                                 "drawn straight. The figures are N.T.S. (E-DXF-06), so the leg is bound to the "
                                 "section depth, not to a printed length."}

    # E-PDF-05 p.15 typical slab-on-beams beam section: one closed link, no inner link
    cs = V.components(V.segments(p15, (110, 491, 300, 1151), {"S-REIN.D"}))
    link = [c for c in cs if len(c) == 20 and V.length(c) > 140]
    check(len(link) == 1 and _topology(link[0]) == {2: 20}, "p.15 beam section: one closed link")
    ev["E-PDF-05"] = {"id": "E-PDF-05", "channel": "PDF_VECTOR (S-REIN.D) + visual", "page": 15,
                      "source": "ST7757.pdf p.15 'TYP. SLAB ON BEAMS DETAIL' beam section ('BEAM SIZE & REINF. SEE "
                                "SCHEDULE')", "handles": ["p15:S-REIN.D"],
                      "facts": {"closed_links": 1, "bbox_pt": _r(V.bbox(link[0])), "topology": _topology(link[0])},
                      "reading": "the typical beam section draws one closed rectangular link (2 legs) with hook ticks "
                                 "at the top corners; no inner link. Same convention as the labelled p.13 sections."}

    # E-PDF-06 visual + OCR readings that vectors cannot carry (stroke text): stair beam, planted column, labels
    ev["E-PDF-06"] = {"id": "E-PDF-06", "channel": "PDF_VECTOR render (pypdf strokes, scratchpad) read visually + "
                      "tesseract OCR cross-check", "page": "13-16", "source": "ST7757.pdf pp.13-16",
                      "handles": ["p13", "p14", "p15", "p16"],
                      "facts": {"p16_TYPICAL_DETAIL_OF_STAIR_BEAM": {"callouts": ["2Ø12 (top, twice)", "4Ø16 (bottom)",
                                                                                 "6Ø8/m (twice)", "AS PER SCH. (depth)"],
                                                                    "ocr_raw": ["2912", "2612", "4916", "608/m", "648 /m"],
                                                                    "geometry": "cranked beam column-to-column following "
                                                                                "the flight; top bar turned down into the "
                                                                                "column at one end, bottom bar turned up "
                                                                                "with a hook at the other; N.T.S."},
                                "p15_BEAM_CARRYING_PLANTED_COL": {"callouts": ["4Ø16", "DEPTH", "STIRRUPS", "10 10",
                                                                               "100 (along the planted column)"],
                                                                  "ocr_raw": ["4916", "DEPTH", "STIRRUPS"],
                                                                  "geometry": "two hooked extra rows under the planted "
                                                                              "column, extending DEPTH (beam depth) past "
                                                                              "each column face; one '4Ø16' leader "
                                                                              "touches BOTH rows; extra stirrups at 10 cm "
                                                                              "under the column"},
                                "p13_labels": ["Long bars", "Short bars", "Boxed bars.", "Ø8/15cm", "3Ø14 x3 (30x30)"]},
                      "reading": "label text on the detail sheets is plotted strokes; the words were read from a "
                                 "render of the vector strokes and cross-checked by OCR (Ø is read as 9 / 6 / 0 by "
                                 "OCR). Bindings (which bar a label points to) come from the vector leaders above."}
    return ev


# ------------------------------------------------------------------------------------------------ frozen registers
def frozen_rows():
    s4 = rows_of(ROOT / "research/alsenan_footing_rebar_s4/FOOTING_REBAR_UNRESOLVED.csv")
    s4c = rows_of(ROOT / "research/alsenan_footing_rebar_s4/FOOTING_REBAR_COMPONENTS.csv")
    s5 = rows_of(ROOT / "research/alsenan_ground_system_rebar_s5/GROUND_SYSTEM_REBAR_UNRESOLVED.csv")
    s6 = rows_of(ROOT / "research/alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_UNRESOLVED.csv")
    s6o = {r["occurrence_id"]: r for r in rows_of(ROOT / "research/alsenan_superstructure_beam_rebar_s6/"
                                                          "SUPERSTRUCTURE_BEAM_OCCURRENCES.csv")}
    return s4, s4c, s5, s6, s6o


def count(rows, **f):
    def ok(r):
        for k, v in f.items():
            if k.endswith("__in"):
                if r.get(k[:-4]) not in v:
                    return False
            elif k.endswith("__has"):
                if v not in (r.get(k[:-5]) or ""):
                    return False
            elif k.endswith("__not"):
                if v in (r.get(k[:-5]) or ""):
                    return False
            elif r.get(k) != v:
                return False
        return True
    return sum(1 for r in rows if ok(r))


# ------------------------------------------------------------------------------------------------------- items
def items(fr):
    s4, s4c, s5, s6, s6o = fr
    lb6 = {k for k, v in s6o.items() if v["occurrence_state"] == "LOWER_BOUND"}
    s6lb = [r for r in s6 if r["occurrence_id"] in lb6]
    single_layer = {r["occurrence_id"] for r in s4c if r["component"] == "TOP_SHORT" and r["state"] == "NOT_APPLICABLE"}
    ft_long = sum(1 for r in s4c if r["component"] == "BOTTOM_LONG" and r["state"] == "VERIFIED"
                  and r["occurrence_id"] in single_layer)
    ft_short = sum(1 for r in s4c if r["component"] == "BOTTOM_SHORT" and r["state"] == "VERIFIED"
                   and r["occurrence_id"] in single_layer)
    ftb_bottom = sum(1 for r in s4c if r["component"] in ("BOTTOM_SHORT", "BOTTOM_LONG") and r["state"] == "LOWER_BOUND"
                     and r["occurrence_id"] not in single_layer)
    boxed_val = count(s4, component="BOXED", raw_value__in=("3+4", "3+5", "3+8"))
    sp_icon = [r for r in s6lb if r["component"] == "STIRRUP_CORE_PATH" and r["mark"] in STR_ICON_ROWS]
    sp_single = [r for r in s6lb if r["component"] == "STIRRUP_CORE_PATH" and r["mark"] not in STR_ICON_ROWS]
    cb_hook_lb = [r for r in s6lb if r["subfamily"] == "CONTINUOUS_BEAM" and r["component"] in ("HOOK_1", "HOOK_2")]

    I = []

    def add(item_id, stage, topic, components, frozen_n, old_state, qid, brief, state, new, ev_ids, why, nxt,
            searched, graph):
        check(state in TERMINAL, f"{item_id} state")
        I.append({"ITEM_ID": item_id, "STAGE": stage, "TOPIC": topic, "COMPONENTS": components,
                  "FROZEN_ROWS_LINKED": frozen_n, "OLD_STATE": old_state, "QUESTION_IDS": qid, "BRIEF_TOPIC": brief,
                  "TERMINAL_STATE": state, "NEW_SOURCE_THIS_ROUND": "TRUE" if new else "FALSE",
                  "EVIDENCE_IDS": ";".join(ev_ids), "WHY": why, "NEXT_ACTION": nxt, "_searched": searched,
                  "_graph": graph})

    DXF_ALL = "ST7757.dxf all TEXT/MTEXT/ATTRIB/ATTDEF/DIMENSION + 420 block definitions (E-DXF-02)"
    P8 = "p.8 notes 1-24 (raster; S1 transcription P8-N01..N24, R4 OCR)"

    # ------------------------------------------------------------------------------------------------ S4
    add("S4-01", "S4", "BOXED value meaning ('3+4' / '3+5' / '3+6' / '3+8')", "BOXED", boxed_val, "BLOCKED_UNQUANTIFIED",
        "Q-R3-6", "§3 meaning of 3+4/3+5/3+6/3+8", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-01", "E-DXF-02", "E-PDF-01"],
        "no legend, note, remark or detail label defines either number; the p.13 detail draws one boxed bar profile "
        "without a count", "engineer to point to the sheet / note that defines '3+n' (claimed to be in the set)",
        [DXF_ALL, "FT block template", P8, "p.13 both footing details (vector)", "p.9 schedule plot"],
        [("SCHEDULE_CELL", "FT rows BOXED attribs", "ST7757.dxf FT inserts", "FOUND"),
         ("TYPICAL_DETAIL", "p.13 TYP. DETAIL OF ISOLATED FOOTING", "ST7757.pdf p.13", "FOUND"),
         ("GENERAL_NOTE", "p.8 notes", "ST7757.pdf p.8", "NOT_FOUND")])
    add("S4-02", "S4", "BOXED bar diameter", "BOXED", boxed_val, "BLOCKED_UNQUANTIFIED", "Q-R3-6",
        "§3 diameter", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-01", "E-PDF-01"],
        "the FT template prints a Ø glyph before SHORT and LONG diameters only; the p.13 'Boxed bars.' leader carries "
        "no diameter", "engineer: diameter of the boxed bar",
        [DXF_ALL, "FT block template", "p.13 labels (visual + OCR)"],
        [("SCHEDULE_CELL", "BOXED column (no Ø glyph)", "FT block", "FOUND"),
         ("TYPICAL_DETAIL", "p.13 'Boxed bars.'", "ST7757.pdf p.13", "FOUND"),
         ("GENERAL_NOTE", "p.8", "ST7757.pdf p.8", "NOT_FOUND")])
    add("S4-03", "S4", "BOXED bar shape", "BOXED", boxed_val, "BLOCKED_UNQUANTIFIED", "Q-R3-6", "§3 bar shape",
        "SOURCE_FOUND_DERIVED", True, ["E-PDF-01"],
        "vector: in both p.13 footing details the 'Boxed bars.' bar is one inverted U (top run under the top face, "
        "two legs down to the bottom-bar level, no hooks); the leader is unambiguous and both details agree. Shape "
        "topology only: leg and run lengths are not dimensioned, and the component stays blocked by S4-01 / S4-02",
        "S4.1 may record the shape facet; quantity still waits for S4-01 / S4-02",
        ["p.13 both footing details (vector S-REIN.D)"],
        [("TYPICAL_DETAIL", "p.13 outer inverted-U bar", "ST7757.pdf p.13 S-REIN.D", "FOUND")])
    add("S4-04", "S4", "BOXED orientation (which plan direction / both)", "BOXED", boxed_val, "BLOCKED_UNQUANTIFIED",
        "Q-R3-6", "§3 orientation", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-PDF-01"],
        "the set draws a single footing elevation; the boxed bar runs parallel to the long-bar run in it, which does "
        "not say whether a second set runs the other way", "engineer: direction(s) of the boxed bars",
        ["p.13 both details", "p.9 schedule"], [("TYPICAL_DETAIL", "p.13 single elevation", "ST7757.pdf p.13", "FOUND")])
    add("S4-05", "S4", "FN blank BOXED cell", "BOXED", count(s4, component="BOXED", mark="FN"), "BLOCKED_UNQUANTIFIED",
        "Q-R3-6", "§3 FN blank BOXED cell", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-01"],
        "the template default '3+-' was cleared for FN only; no remark explains the blank and the p.13 detail names no "
        "footing type", "engineer: does FN have boxed bars",
        [DXF_ALL, "FT block template", "p.9 REMARKS"], [("SCHEDULE_CELL", "FN BOXED = ''", "ST7757.dxf FT row FN", "FOUND")])
    add("S4-06", "S4", "Two-layer footing rows and boxed reinforcement", "BOXED (F8/F12/F13/F14/FF)",
        sum(1 for r in s4c if r["component"] == "BOXED" and r["state"] == "NOT_APPLICABLE"), "NOT_APPLICABLE",
        "", "§3 whether two-layer rows use boxed bars", "SOURCE_FOUND_EXPLICIT", False, ["E-DXF-01", "E-PDF-03"],
        "the FTB template puts the layer labels TOP / BOT in the BOXED column, so two-layer rows carry no boxed value; "
        "the p.14 two-layer (FF) detail draws top + bottom layers and no boxed bar", "none (S4 state confirmed)",
        ["FTB block template", "p.14 lift footing (vector)"],
        [("SCHEDULE_CELL", "FTB BOXED-T / BOXED-B", "FTB block", "FOUND"),
         ("TYPICAL_DETAIL", "p.14 lift footing", "ST7757.pdf p.14", "FOUND")])
    add("S4-07", "S4", "FF '2Ø16': detail association and footing-side vs wall-base", "OTHER_EXPLICIT_EXTRA (FF)",
        count(s4, mark="FF", component="OTHER_EXPLICIT_EXTRA"), "BLOCKED_UNQUANTIFIED", "S4-Q1",
        "§3 FF 2Ø16 association / footing-side vs wall-base", "SOURCE_FOUND_DERIVED", True, ["E-PDF-03", "E-DXF-05"],
        "vector leaders: each '2 Ø16' label ends on two bar dots - one pair at the footing top mesh level, one at the "
        "bottom mesh level - inside the footprint of the cut pit wall; the second cut wall repeats the 2 + 2 dots. "
        "They are wall-base bars inside the footing running along the wall, not footing-side bars",
        "S4.1: 2 top + 2 bottom Ø16 per cut wall; length still S4-08",
        ["p.14 (vector dots + leaders)", "foundation plan FF pit walls (DXF)"],
        [("SCHEDULE_CELL", "FF row REMARKS 'lift base' (1C64)", "ST7757.dxf", "FOUND"),
         ("DETAIL_REFERENCE", "FF -> p.14 lift detail", "ST7757.pdf p.14", "FOUND"),
         ("TYPICAL_DETAIL", "p.14 2Ø16 dots in wall band", "ST7757.pdf p.14 S-REIN.D", "FOUND")])
    add("S4-08", "S4", "FF '2Ø16': extent / length and number of walls", "OTHER_EXPLICIT_EXTRA (FF)",
        count(s4, mark="FF", component="OTHER_EXPLICIT_EXTRA"), "BLOCKED_UNQUANTIFIED", "S4-Q1", "§3 FF 2Ø16 extent",
        "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-PDF-03", "E-DXF-05"],
        "the bars are seen in section, so their length is not drawn; the plan pit is a closed square of four 20 cm walls "
        "(1.80 / 2.20 m) but the section cuts only two, and no detail says whether the other two carry the same bars",
        "engineer: bar length / lap at the pit corners and whether all four walls carry 2 + 2 Ø16",
        ["p.14", "foundation plan pit walls (DXF S-BW 10EA / 10EB)"],
        [("TYPICAL_DETAIL", "p.14", "ST7757.pdf p.14", "FOUND"),
         ("ARCHITECTURAL_REFERENCE", "pit size 'AS ARCH.' / lift manufacturer", "p.14 text", "NOT_FOUND")])
    add("S4-09", "S4", "F / F10 occurrence conflict", "ALL (footing F|F10)", count(s4, mark="F|F10"),
        "BLOCKED (SOURCE_CONFLICT)", "S4 F/F10", "§3 F/F10 - do not resolve by inference", "PENDING_ENGINEER_CLARIFICATION",
        False, ["E-DXF-10"], "known drawing conflict awaiting the engineer's separate answer; not resolved by inference",
        "wait for the engineer's answer", ["F / F10 schedule rows and plan tags"],
        [("OCCURRENCE_COMPONENT", "footing tagged F / F10", "ST7757.dxf", "FOUND"),
         ("SCHEDULE_CELL", "rows F and F10", "ST7757.dxf FT", "FOUND")])
    add("S4-10", "S4", "Per-metre two-layer counts: +1 edge bar", "BOTTOM/TOP SHORT/LONG (FTB rows)",
        count(s4, what_is_missing__has="EDGE_BAR_CONVENTION"), "LOWER_BOUND", "", "§3 (FTB rows)",
        "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-02", "E-PDF-03"],
        "no note or detail states the first / last bar position for '/m' rates", "engineer or S4.1 lower bound kept",
        [DXF_ALL, P8, "p.14"], [("SCHEDULE_CELL", "FTB '/m' rates", "ST7757.dxf FTB", "FOUND"),
                               ("GENERAL_NOTE", "p.8", "ST7757.pdf p.8", "NOT_FOUND")])
    add("S4-11", "S4", "Two-layer top-bar end treatment", "TOP_SHORT / TOP_LONG (FTB rows)",
        count(s4, what_is_missing__has="END_TREATMENT"), "LOWER_BOUND", "", "§3 (FTB rows)", "SOURCE_EXPECTED_NOT_LOCATED",
        False, ["E-PDF-03"], "only FF has a two-layer detail; it draws the layers as one closed loop, but 6/m top vs "
        "9/m bottom means the loop cannot pair bars; F8 / F12 / F13 / F14 have no detail",
        "engineer: end treatment of two-layer bars", ["p.14 loop (vector)", "FTB rates"],
        [("TYPICAL_DETAIL", "p.14 closed loop (FF only)", "ST7757.pdf p.14", "FOUND")])
    add("S4-12", "S4", "Single-layer FT bottom LONG bars: end treatment (frozen VERIFIED straight)", "BOTTOM_LONG (FT rows)",
        ft_long, "VERIFIED (END STRAIGHT_SOURCE_SUPPORTED)", "", "§3 common footing detail (second pass)",
        "SOURCE_FOUND_DERIVED", True, ["E-PDF-01"],
        "vector: the bar labelled 'Long bars' is drawn as a U with two up-legs and 45° hooks in BOTH p.13 footing "
        "details (legs share the bottom-run vertices exactly). The frozen S4 reading 'bottom bars straight (no hook)' "
        "is withdrawn; the straight core stays a valid lower bound. Leg / hook length not dimensioned",
        "S4.1: BOTTOM_LONG VERIFIED -> LOWER_BOUND, END_LEGS + HOOKS named missing (no kg change in this round)",
        ["p.13 both details (vector S-REIN.D)"],
        [("TYPICAL_DETAIL", "p.13 inner U bar + 'Long bars' leader", "ST7757.pdf p.13 S-REIN.D", "FOUND")])
    add("S4-13", "S4", "Single-layer FT bottom SHORT bars: end treatment (frozen VERIFIED straight)",
        "BOTTOM_SHORT (FT rows)", ft_short, "VERIFIED (END STRAIGHT_SOURCE_SUPPORTED)", "",
        "§3 common footing detail (second pass)", "SOURCE_EXPECTED_NOT_LOCATED", True, ["E-PDF-01"],
        "short bars are drawn only as dots (in section) in the single elevation, so their end shape is not shown; the "
        "'straight' reading is not supported by the drawing", "S4.1: BOTTOM_SHORT VERIFIED -> LOWER_BOUND (end shape "
        "not established); engineer to confirm", ["p.13 both details"],
        [("TYPICAL_DETAIL", "p.13 short-bar dots", "ST7757.pdf p.13", "FOUND")])
    add("S4-14", "S4", "Two-layer bottom bars: end treatment (frozen STRAIGHT)", "BOTTOM_SHORT / BOTTOM_LONG (FTB rows)",
        ftb_bottom, "LOWER_BOUND (END STRAIGHT_SOURCE_SUPPORTED)", "", "§3 (second pass)", "SOURCE_EXPECTED_NOT_LOCATED",
        True, ["E-PDF-01", "E-PDF-03"], "the straight reading came from the single-layer detail, which now shows U bars; "
        "two-layer footings have no applicable bottom-bar shape except the FF loop (S4-11)",
        "S4.1: add END_TREATMENT to the missing facets (state stays LOWER_BOUND)", ["p.13", "p.14"],
        [("TYPICAL_DETAIL", "p.13 / p.14", "ST7757.pdf", "FOUND")])

    # ------------------------------------------------------------------------------------------------ S5
    add("S5-01", "S5", "GB longitudinal development into supports (interior continuing supports)",
        "DEVELOPMENT_SUPPORT_1/2", count(s5, component__in=("DEVELOPMENT_SUPPORT_1", "DEVELOPMENT_SUPPORT_2")),
        "BLOCKED_UNQUANTIFIED", "Q7", "§4 longitudinal development into supports", "SOURCE_FOUND_DERIVED", True,
        ["E-PDF-01"], "vector: in both p.13 footing details the ground-beam bars ('Ground beam reinforcements') run "
        "unbroken through the column and on past both breaks - at an interior support where the GB line continues, the "
        "bars are continuous (no anchorage). The row count is all support ends; the split interior / end is S5.1 work",
        "S5.1: classify each support end; interior continuing ends -> THROUGH_SUPPORT run", ["p.13 (vector)"],
        [("TYPICAL_DETAIL", "p.13 GB bars through the column", "ST7757.pdf p.13 S-REIN.D", "FOUND")])
    add("S5-02", "S5", "GB development / anchorage at END supports and into footings",
        "DEVELOPMENT_SUPPORT_1/2 (end) + DEVELOPMENT_FOOTING_1/2",
        count(s5, component__in=("DEVELOPMENT_FOOTING_1", "DEVELOPMENT_FOOTING_2")), "BLOCKED_UNQUANTIFIED", "Q7",
        "§4 longitudinal development", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-02"],
        "no beam-end anchorage length or detail anywhere (note 9 70Ø / 40Ø is starter context only)",
        "engineer: anchorage of GB / strap bars at end supports and into footings", [DXF_ALL, P8, "pp.13-16"],
        [("GENERAL_NOTE", "p.8 note 9 (starters only)", "ST7757.pdf p.8", "FOUND"),
         ("TYPICAL_DETAIL", "end-support GB detail", "pp.13-16", "NOT_FOUND")])
    add("S5-03", "S5", "GB longitudinal hooks / bends", "HOOK_1/2", count(s5, component__in=("HOOK_1", "HOOK_2")),
        "BLOCKED_UNQUANTIFIED", "Q7", "§4 longitudinal hooks", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-02"],
        "GB bar ends are not drawn at any end support", "engineer", [DXF_ALL, "pp.13-16"],
        [("TYPICAL_DETAIL", "GB bar end", "pp.13-16", "NOT_FOUND")])
    add("S5-04", "S5", "GB stirrup shape and legs", "STIRRUP_CORE_PATH (legs facet)",
        count(s5, component="STIRRUP_CORE_PATH"), "BLOCKED_UNQUANTIFIED", "Q6",
        "§4 ground-beam stirrup shape / legs", "SOURCE_FOUND_DERIVED", True, ["E-PDF-02"],
        "vector: each of the four p.13 GB sections draws exactly one closed link (2 legs) with one hook branch; the "
        "label leader of the >5 m, <5 m and exterior links lands on that link", "S5.1: legs = 2, single closed link; "
        "core path lower bound once width / depth are known", ["p.13 sections (vector)"],
        [("TYPICAL_DETAIL", "p.13 GB sections", "ST7757.pdf p.13 S-REIN.D", "FOUND")])
    add("S5-05", "S5", "GB stirrup hook shape / extension", "STIRRUP_HOOK_1/2",
        count(s5, component__in=("STIRRUP_HOOK_1", "STIRRUP_HOOK_2")), "BLOCKED_UNQUANTIFIED", "Q6",
        "§4 stirrup hook shape", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-PDF-02"],
        "the hook is drawn as a short diagonal branch at one corner; angle and extension are not dimensioned",
        "engineer: hook angle and extension", ["p.13 sections"], [("TYPICAL_DETAIL", "hook branch", "ST7757.pdf p.13",
                                                                   "FOUND")])
    add("S5-06", "S5", "Exterior ground-beam depth (FOLLOW ARCH)", "SIDE_REBAR / STIRRUP_CORE_PATH (exterior)",
        count(s5, question_id="Q2"), "BLOCKED_UNQUANTIFIED", "Q2", "§4 exterior GB depth / FOLLOW ARCH connection",
        "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-ARCH-01", "E-DXF-08"],
        "the p.13 exterior section runs from the outer natural ground level to the GF slab level 'FOLLOW ARCH.'; the "
        "architectural set gives level marks (FFL +1.00, ±0.00) but no floor build-up, so D <= 1.00 m stays a bound; "
        "plan note B8 adds a neighbour-side block-wall condition, no depth", "engineer: GF slab (structural) level or "
        "floor build-up", ["P7757.dxf all texts", "P7757 raster PDFs (pre-S5.1)", "ST7757 note B8", "p.13 section"],
        [("TYPICAL_DETAIL", "p.13 exterior GB section", "ST7757.pdf p.13", "FOUND"),
         ("ARCHITECTURAL_REFERENCE", "FOLLOW ARCH -> P7757 levels", "P7757.dxf LEVEL texts", "FOUND"),
         ("ARCHITECTURAL_REFERENCE", "floor build-up", "P7757", "NOT_FOUND")])
    add("S5-07", "S5", "Annex +0.30 level vs the three-level exterior section", "exterior GB occurrences (annex)",
        count(s5, what_is_missing__has="DEPTH SOURCE_CONFLICT"), "BLOCKED_UNQUANTIFIED", "Q2",
        "§4 exterior GB depth", "SOURCE_CONFLICT", False, ["E-ARCH-01"],
        "architectural +0.30 (D <= 0.30 m) cannot hold the drawn exterior section (two project sources disagree)",
        "engineer (pending conflicts)", ["P7757 levels", "p.13 section"],
        [("ARCHITECTURAL_REFERENCE", "+0.30 annex mark", "P7757.dxf", "FOUND")])
    add("S5-08", "S5", "<2.5 m detail: stirrup diameter / rate", "STIRRUP_DIAMETER / STIRRUP_SPACING (Q4)",
        count(s5, component__in=("STIRRUP_DIAMETER", "STIRRUP_SPACING"), question_id="Q4"), "BLOCKED_UNQUANTIFIED", "Q4",
        "§4 <2.5 m stirrup diameter / rate", "SOURCE_EXPECTED_NOT_LOCATED", True, ["E-PDF-02"],
        "vector: the 30x30 section draws its link but NO leader touches it - only the three '3Ø14' rows are labelled; "
        "nothing else in the set gives that link", "engineer: link of the <2.5 m section", ["p.13 (vector leaders)"],
        [("TYPICAL_DETAIL", "p.13 30x30 section, unlabelled link", "ST7757.pdf p.13", "FOUND")])
    add("S5-09", "S5", "Detail precedence below 2.5 m ('<2.5 m' vs '<5 m')", "GB occurrences < 2.5 m",
        count(s5, question_id="Q4"), "BLOCKED_UNQUANTIFIED", "Q4", "§4 detail precedence", "SOURCE_EXPECTED_NOT_LOCATED",
        False, ["E-DXF-02"], "both titles hold below 2.5 m and no note states which governs", "engineer",
        [DXF_ALL, "p.13 titles"], [("TYPICAL_DETAIL", "two p.13 titles", "ST7757.pdf p.13", "FOUND")])
    add("S5-10", "S5", "'without concentrated load' definition", "all components of the 15 Q1 occurrences",
        count(s5, question_id__in=("Q1", "Q1+Q9", "Q1+Q9+Q8")), "BLOCKED_UNQUANTIFIED", "Q1",
        "§4 'without concentrated load' definitions / related detail", "SOURCE_EXPECTED_NOT_LOCATED", False,
        ["E-DXF-02"], "the p.13 titles use the phrase; no note, legend or detail defines a concentrated load or gives "
        "a 'with concentrated load' section (the CGT LOAD column is column load, not a GB rule)", "engineer",
        [DXF_ALL, P8, "pp.13-16"], [("TYPICAL_DETAIL", "'with concentrated load' section", "pp.13-16", "NOT_FOUND")])
    add("S5-11", "S5", "SB2 duplicate schedule rows", "SB2 strap (all)", count(s5, question_id="Q5"),
        "BLOCKED (SOURCE_CONFLICT)", "Q5", "§4 SB2 duplicate rows", "SOURCE_CONFLICT", True, ["E-DXF-04"],
        "NEW: only row 2ABA (100x50, 20Ø18 / 10Ø16) is inside the issued schedule sheet (PDF p.10); row 1FBB (80x50) "
        "lies below the sheet frame in model space. The issued sheet does not say 1FBB is void, so the brief's "
        "'explicit' test is not met: the conflict stays, with a one-line confirmation request",
        "engineer: confirm the issued-sheet row (100x50) governs", ["SBT rows + sheet frame (DXF)", "PDF p.10 plot"],
        [("SCHEDULE_CELL", "SB2 rows 1FBB / 2ABA", "ST7757.dxf", "FOUND"),
         ("SCHEDULE_CELL", "issued p.10 shows 2ABA only", "ST7757.pdf p.10", "FOUND")])
    add("S5-12", "S5", "Unidentified '******' symbols", "components of 3 occurrences", count(s5, question_id__has="Q9"),
        "BLOCKED_UNQUANTIFIED", "Q9", "§4 ****** symbols", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-09"],
        "two plain text marks at GB junctions with no legend; every other '*' is a note bullet", "engineer",
        [DXF_ALL], [("OCCURRENCE_COMPONENT", "165A / 165B", "ST7757.dxf", "FOUND"),
                    ("GENERAL_NOTE", "legend for ******", "ST7757", "NOT_FOUND")])
    add("S5-13", "S5", "Support / termination of 1811-1812", "GSO-1811-1812-1", count(s5, question_id="Q10"),
        "BLOCKED_UNQUANTIFIED", "Q10", "§4 support / termination of 1811-1812", "SOURCE_EXPECTED_NOT_LOCATED", False,
        ["E-DXF-02"], "the east end sits on the plot-boundary line with no column or footing; the only related source "
        "is the p.14 TYPICAL BOUNDARY WALL (columns 'SEE ARCH PLAN'), itself a known S1 conflict (P14-BOUNDARY)",
        "engineer", ["foundation / GB plans", "p.14 boundary wall"],
        [("TYPICAL_DETAIL", "p.14 boundary wall", "ST7757.pdf p.14", "FOUND"),
         ("ARCHITECTURAL_REFERENCE", "boundary columns 'SEE ARCH PLAN'", "P7757", "NOT_FOUND")])
    add("S5-14", "S5", "GB side reinforcement '2Ø12/30cm' (exterior section)", "SIDE_REBAR",
        count(s5, component="SIDE_REBAR"), "BLOCKED_UNQUANTIFIED", "Q2", "§4 side reinforcement where shown",
        "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-PDF-02", "E-ARCH-01"],
        "the exterior section draws one bar on each face per level with an X between levels; the count still depends "
        "on the unknown depth (S5-06) and the '/30cm' wording is not defined", "engineer (with S5-06)", ["p.13"],
        [("TYPICAL_DETAIL", "p.13 exterior section side bars", "ST7757.pdf p.13", "FOUND")])
    add("S5-15", "S5", "Length basis of the p.13 titles", "detail selection (Q3)", count(s5, question_id__has="Q3"),
        "BLOCKED_UNQUANTIFIED", "Q3", "§4 (detail selection)", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-02"],
        "no source says whether '5m length' is clear span or centreline", "engineer", [DXF_ALL, "p.13"],
        [("TYPICAL_DETAIL", "p.13 titles", "ST7757.pdf p.13", "FOUND")])
    add("S5-16", "S5", "Bar run where the drawn band and the support faces disagree", "bar runs (Q3B)",
        count(s5, question_id="Q3B"), "BLOCKED_UNQUANTIFIED", "Q3B", "§4 (geometry)", "SOURCE_CONFLICT", False, [],
        "two drawn geometries of the same beam end disagree (band vs support face)", "engineer (pending conflicts)",
        ["GB plan geometry (frozen S5)"], [("OCCURRENCE_COMPONENT", "GB band vs support faces", "ST7757.dxf", "FOUND")])
    add("S5-17", "S5", "Partly exterior / slab-edge spans: which section", "detail applicability (Q8)",
        count(s5, question_id__has="Q8"), "BLOCKED_UNQUANTIFIED", "Q8", "§4 (detail selection)",
        "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-02"], "no source assigns a section to mixed spans", "engineer",
        [DXF_ALL, "p.13"], [("TYPICAL_DETAIL", "p.13 sections", "ST7757.pdf p.13", "FOUND")])

    add("S5-18", "S5", "Strap-beam link topology (SB1 / SB3 STR2, SB2 str3)", "STIRRUP_CORE_PATH (straps)",
        count(s5, family="STRAP_BEAM", component="STIRRUP_CORE_PATH"), "BLOCKED_UNQUANTIFIED", "Q6",
        "§4 stirrup legs (straps)", "SOURCE_FOUND_DERIVED", True, ["E-DXF-03"],
        "block geometry: the SBT REMARKS icons give SB1 and SB3 two closed links (STR2, 4 legs) and SB2 three (str3, "
        "6 legs); the frozen S5 had 'LEGS / LINK TOPOLOGY NOT_STATED'. Inner-link widths are not dimensioned; SB2 "
        "stays blocked by its row conflict (S5-11)", "S5.1: SB1 / SB3 core path lower bound (outer link + inner "
        "link vertical legs, hooks excluded)", ["SBT REMARKS icons (DXF)", "p.10 plot"],
        [("SCHEDULE_CELL", "SB1 / SB2 / SB3 REMARKS icons", "ST7757.dxf SBT", "FOUND"),
         ("TYPICAL_DETAIL", "labelled closed link symbol", "ST7757.pdf p.13", "FOUND")])

    # ------------------------------------------------------------------------------------------------ S6
    add("S6-01", "S6", "Beam longitudinal development / anchorage", "DEVELOPMENT_1/2",
        count(s6, component__in=("DEVELOPMENT_1", "DEVELOPMENT_2")), "BLOCKED_UNQUANTIFIED", "Q1",
        "§5 longitudinal development", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-02"],
        "no beam development length anywhere (note 9 is starter context; the slab 0.25 L / 0.30 L rules are slab rules)",
        "engineer", [DXF_ALL, P8, "pp.11-16"], [("GENERAL_NOTE", "beam development", "ST7757", "NOT_FOUND")])
    add("S6-02", "S6", "CB top bar at END supports: bend / leg", "HOOK_1/2 (continuous beams)",
        count(s6, subfamily="CONTINUOUS_BEAM", component__in=("HOOK_1", "HOOK_2")), "BLOCKED_UNQUANTIFIED", "Q1",
        "§5 longitudinal hooks", "SOURCE_FOUND_DERIVED", True, ["E-PDF-04", "E-DXF-06"],
        "vector: in all three CB typical figures the end-support top bar turns down in one 90° leg whose foot ends at "
        "the bottom-bar level - the leg is bound to the section depth (h less covers), consistent in 3 figures, not "
        "contradicted. S6 recorded 'end legs drawn N.T.S. without a dimension'; the binding is to the section, not to "
        "a printed length", "S6.1: CB top-bar end leg lower bound = section depth less 2 x 25 mm cover less link and "
        "bar diameters", ["pp.11-12 typicals (vector)", "C-BEAM templates (DXF)"],
        [("TYPICAL_DETAIL", "CB typical end legs", "ST7757.pdf pp.11-12 S-REIN.D", "FOUND"),
         ("GENERAL_NOTE", "p.8 note 22 member cover 25 mm", "ST7757.pdf p.8", "FOUND")])
    add("S6-03", "S6", "Simple-beam (SBT) bar-end hooks / bends", "HOOK_1/2 (simple beams)",
        count(s6, subfamily="SIMPLE_BEAM", component__in=("HOOK_1", "HOOK_2")), "BLOCKED_UNQUANTIFIED", "Q1",
        "§5 longitudinal hooks", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-02"],
        "the SBT schedule has no typical figure; the only drawn simple-beam ends are the special p.15 / p.16 details",
        "engineer", ["p.10", "pp.13-16"], [("TYPICAL_DETAIL", "SBT typical", "p.10", "NOT_FOUND")])
    add("S6-04", "S6", "Stirrup topology: beams without a REMARKS icon", "STIRRUP_CORE_PATH (legs facet)",
        sum(1 for r in s6 if r["component"] == "STIRRUP_CORE_PATH" and r["mark"] not in STR_ICON_ROWS),
        "BLOCKED_UNQUANTIFIED", "Q7", "§5 stirrup topology", "SOURCE_FOUND_DERIVED", True,
        ["E-PDF-05", "E-PDF-02", "E-DXF-03"],
        "vector: the p.15 typical beam section ('BEAM SIZE & REINF. SEE SCHEDULE') draws one closed link and no inner "
        "link; the p.13 labelled sections use the same single closed link; rows that need more legs carry an icon "
        "(S6-05). Target unambiguous, examples agree, no contradiction", "S6.1: single 2-leg closed link; core path "
        "lower bound 2(b-2c-d)+2(h-2c-d), c = 25 mm (note 22), hooks excluded", ["p.15", "p.13", "p.10 icons"],
        [("SCHEDULE_CELL", "REMARKS without icon", "ST7757.dxf SBT", "FOUND"),
         ("TYPICAL_DETAIL", "p.15 beam section", "ST7757.pdf p.15 S-REIN.D", "FOUND")])
    add("S6-05", "S6", "Stirrup topology: STR2 / str3 icon rows (B17, B19-B26)", "STIRRUP_CORE_PATH (legs facet)",
        sum(1 for r in s6 if r["component"] == "STIRRUP_CORE_PATH" and r["mark"] in STR_ICON_ROWS),
        "BLOCKED_UNQUANTIFIED", "Q7", "§5 graphical link sketches STR2 / STR3", "SOURCE_FOUND_DERIVED", True,
        ["E-DXF-03", "E-PDF-02"], "block geometry: STR2 = outer + one inner closed link of full height, each with a "
        "hook-tick pair (4 legs); str3 = outer + two inner (6 legs, SB2). The symbol is the project's own labelled "
        "link symbol. PRE-S6 read it as 'PROJECT_PATTERN_ONLY'; the labelled examples make it DERIVED",
        "S6.1: 2 links (4 legs); outer link lower bound as S6-04, inner link lower bound = its two vertical legs "
        "(width not dimensioned, S6-06)", ["DXF STR2 / str3 blocks", "p.10 plot", "p.13 labelled links"],
        [("SCHEDULE_CELL", "REMARKS icon STR2", "ST7757.dxf SBT REMARKS", "FOUND"),
         ("TYPICAL_DETAIL", "labelled closed link symbol", "ST7757.pdf p.13", "FOUND")])
    add("S6-06", "S6", "Inner-link width of the STR2 rows", "STIRRUP_CORE_PATH (inner link)",
        sum(1 for r in s6 if r["component"] == "STIRRUP_CORE_PATH" and r["mark"] in STR_ICON_ROWS),
        "BLOCKED_UNQUANTIFIED", "Q7", "§5 stirrup topology", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-03"],
        "the icon is a sketch (inner link about one third of the outer width); no dimension", "engineer",
        ["STR2 block"], [("SCHEDULE_CELL", "STR2 icon", "ST7757.dxf", "FOUND")])
    add("S6-07", "S6", "Stirrup hook extension", "STIRRUP hooks (all)", count(s6, component="STIRRUP_CORE_PATH"),
        "BLOCKED_UNQUANTIFIED", "Q7", "§5 stirrup hooks", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-PDF-05", "E-DXF-03"],
        "hooks are drawn as tick pairs at a corner; angle / extension not dimensioned", "engineer",
        ["p.13 / p.15 / icons"], [("TYPICAL_DETAIL", "hook ticks", "ST7757.pdf", "FOUND")])
    add("S6-08", "S6", "CB upper / hanger row", "HANGER + TOP_SUPPORT (CB)",
        count(s6, component__in=("HANGER", "TOP_SUPPORT")), "BLOCKED_UNQUANTIFIED", "Q2", "§5 CB upper / hanger row",
        "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-PDF-04", "E-DXF-06"],
        "the typical draws an unlabelled second top row; no label, note or schedule cell gives its bars", "engineer",
        ["pp.11-12 (vector + DXF)"], [("TYPICAL_DETAIL", "unlabelled second top row", "ST7757.pdf p.11", "FOUND")])
    add("S6-09", "S6", "'0.3 Ln2' in the 2-span typicals / undimensioned left-end bar", "TOP_SUPPORT (CB end)",
        count(s6, component="TOP_SUPPORT"), "BLOCKED_UNQUANTIFIED", "Q3", "§5 0.3Ln2 notation",
        "SOURCE_EXPECTED_NOT_LOCATED", True, ["E-DXF-06"], "NEW negative test: the figures are N.T.S., so the drawn "
        "length cannot say which span 'Ln2' means in a 2-span frame; extension points put it on the last span's end "
        "bar, but the symbol stays undefined", "engineer", ["C-BEAM templates (DXF dimensions)"],
        [("TYPICAL_DETAIL", "'0.3 Ln2' dimension", "ST7757.dxf 2785 / 20C6", "FOUND")])
    add("S6-10", "S6", "'0.15L' in the 3-span typical", "BOTTOM extension (CB 3-span)", 0, "LEFT OUT (lower bound)",
        "Q4", "§5 0.15L notation", "SOURCE_EXPECTED_NOT_LOCATED", True, ["E-DXF-06"],
        "N.T.S.; one '0.15L' enters the span labelled L, the other the span labelled L3 - no scale or label decides",
        "engineer", ["C-BEAM3 template"], [("TYPICAL_DETAIL", "'0.15L' dimensions", "ST7757.dxf 225A / 2282", "FOUND")])
    add("S6-11", "S6", "Side bars '2Ø12/30cm', '2Ø16/20cm', '2Ø14/20cm' semantics", "SIDE_REBAR",
        count(s6, component="SIDE_REBAR"), "BLOCKED_UNQUANTIFIED", "Q6", "§5 side reinforcement", "SOURCE_EXPECTED_NOT_LOCATED",
        False, ["E-PDF-02"], "per face or total and the '/30cm' meaning are not defined; the only drawn example (GB "
        "exterior) is variable depth", "engineer", ["p.10 REMARKS", "p.11-12 MIDDLE REINT.", "p.13"],
        [("SCHEDULE_CELL", "REMARKS side-bar text", "ST7757.dxf SBT / C-BEAM", "FOUND")])
    add("S6-12", "S6", "Side-bar depth threshold", "SIDE_REBAR (rule)", 0, "KNOWN (P8-N21)", "Q6",
        "§5 depth threshold for side bars", "SOURCE_FOUND_EXPLICIT", False, [],
        "p.8 note 21: side bars in beams deeper than 60 cm 'unless stated otherwise' (already S1 P8-N21); the REMARKS "
        "override it per row", "none", [P8], [("GENERAL_NOTE", "p.8 note 21", "ST7757.pdf p.8", "FOUND")])
    add("S6-13", "S6", "Cantilever CA detail", "CA occurrences", 0, "BLOCKED (Q9)", "Q9", "§5 cantilever CA detail",
        "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-02"], "CA has a schedule row only; no cantilever detail on "
        "pp.13-16 and no text", "engineer", [DXF_ALL, "pp.13-16"],
        [("SCHEDULE_CELL", "CA row", "ST7757.dxf SBT", "FOUND"), ("TYPICAL_DETAIL", "cantilever", "pp.13-16", "NOT_FOUND")])
    add("S6-14", "S6", "'WITH STAIR' beam detail (B3 spans)", "all components of 2 B3 spans",
        sum(1 for r in s6 if r["occurrence_id"] in ("BM-1F_ROOF-B3-BL023-6B9", "BM-GF_ROOF-B3-BL033-6B7")),
        "BLOCKED (UNDEFINED_CANDIDATE_DETAIL Q9)", "Q9", "§5 WITH STAIR beam detail", "SOURCE_FOUND_DERIVED", True,
        ["E-DXF-07", "E-PDF-06"], "the p.16 'TYPICAL DETAIL OF STAIR BEAM' callouts (2Ø12 top, 4Ø16 bottom, 6Ø8/m, depth "
        "AS PER SCH.) equal the B3 schedule row exactly and every '(With Stair)' tag sits on a B3 tag: the detail adds "
        "no bars and changes none. It draws the beam cranked along the flight, so the plan run is a lower bound",
        "S6.1: release the B3 WITH STAIR spans as LOWER_BOUND (schedule bars over the plan run; STAIR_EXTRA none)",
        ["p.16 (render + OCR)", "DXF tags + SBT B3"],
        [("OCCURRENCE_COMPONENT", "B3 + '(With Stair)'", "ST7757.dxf 6B6-6B9 / 1826-1827", "FOUND"),
         ("SCHEDULE_CELL", "SBT B3", "ST7757.dxf", "FOUND"),
         ("TYPICAL_DETAIL", "p.16 stair beam", "ST7757.pdf p.16", "FOUND")])
    add("S6-15", "S6", "Planted-column beam detail (B26)", "base components of BM-GF_ROOF-B26-BL014-4CC",
        sum(1 for r in s6 if r["occurrence_id"] == "BM-GF_ROOF-B26-BL014-4CC"), "BLOCKED (Q9)", "Q9",
        "§5 planted-column beam detail", "SOURCE_FOUND_DERIVED", True, ["E-PDF-06"],
        "the p.15 detail adds extras only (4Ø16 hooked rows extending DEPTH past each column face; stirrups at 10 cm "
        "under the column); it does not change the schedule bars, so the base components are no longer blocked by it. "
        "The extra stays blocked: one '4Ø16' leader touches both rows (2 + 2 or 4 + 4 not stated)",
        "S6.1: base components LOWER_BOUND; PLANTED_COLUMN_EXTRA blocked (row split)", ["p.15 (render + OCR)"],
        [("TYPICAL_DETAIL", "p.15 planted column", "ST7757.pdf p.15", "FOUND"),
         ("GENERAL_NOTE", "legend P.C = planted column", "ST7757 p.3", "FOUND")])
    add("S6-16", "S6", "Curved / ring beam reinforcement (dome-ring arcs)", "arc occurrences", 0, "BLOCKED_TYPE (R6)",
        "Q9;R6", "§5 curved / ring beam", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-02"],
        "no ring-beam detail or bar-stop rule in the set", "engineer", [DXF_ALL, "pp.13-16"],
        [("TYPICAL_DETAIL", "ring beam", "pp.13-16", "NOT_FOUND")])
    add("S6-17", "S6", "Width conflicts (B6, CB10, B21, B29, CB2)", "5 occurrences",
        sum(1 for r in s6 if r["occurrence_id"] in R2_OCC), "BLOCKED (SOURCE_CONFLICT)", "R2",
        "§5 width-conflict source references", "SOURCE_CONFLICT", False, [],
        "drawn plan width and schedule width disagree; no detail or note decides", "engineer (pending conflicts)",
        ["plan bands vs SBT / C-BEAM widths"], [("SCHEDULE_CELL", "B column", "ST7757.dxf", "FOUND")])
    add("S6-18", "S6", "CB span conflicts (CB4, CB5 lengths; CB8 span count)", "3 occurrences",
        sum(1 for r in s6 if r["occurrence_id"] in R3_OCC), "BLOCKED (SOURCE_CONFLICT)", "R3", "§5 (CB)",
        "SOURCE_CONFLICT", False, [], "plan spans and schedule spans disagree", "engineer (pending conflicts)",
        ["plan c/c vs C-BEAM L-M fields"], [("SCHEDULE_CELL", "C-BEAM L1-M / L2-M / L3-M", "ST7757.dxf", "FOUND")])
    add("S6-19", "S6", "CB3: middle span also tagged 'B3 WITH STAIR'; edited MID1 / blank MID2", "CBO-GFRS-CB3-BL022",
        sum(1 for r in s6 if r["occurrence_id"] == "CBO-GFRS-CB3-BL022"), "BLOCKED (SOURCE_CONFLICT)", "R5",
        "§5 CB edited / empty MID fields", "SOURCE_CONFLICT", False, ["E-DXF-07"],
        "two marks claim one span; the p.16 detail equals B3, not CB3's span bars, so it does not decide", "engineer",
        ["CB3 frame", "B3 tag 1827"], [("SCHEDULE_CELL", "CB3 MID1 / MID2", "ST7757.dxf", "FOUND")])
    add("S6-20", "S6", "CB reading direction (CB2, CB7, CB13)", "span-1 end", 0, "candidate-invariant only (R4)", "R4",
        "§5 (CB)", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-02"],
        "no source marks span 1; both directions match the schedule", "engineer", [DXF_ALL],
        [("SCHEDULE_CELL", "LOCATION column (empty)", "ST7757.dxf", "FOUND")])
    add("S6-21", "S6", "Binding candidates (445, 45D, 474, 476, 78F)", "5 spans", 0, "candidate (R1)", "R1", "§5",
        "SOURCE_EXPECTED_NOT_LOCATED", False, [], "tag-to-span ambiguity; no new source", "engineer", ["plan tags"],
        [("OCCURRENCE_COMPONENT", "untied tags", "ST7757.dxf", "FOUND")])
    add("S6-22", "S6", "38 untagged spans / arcs", "38 geometries", count(s6, component="ALL"), "BLOCKED_TYPE (R6)", "R6",
        "§5", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-02"], "no tag or note names their type", "engineer",
        ["plans"], [("OCCURRENCE_COMPONENT", "untagged spans", "ST7757.dxf", "FOUND")])
    add("S6-23", "S6", "SBT bars uncurtailed support face to support face", "TOP_MAIN / BOTTOM_MAIN (simple)", 0,
        "LOWER_BOUND (Q8 confirmation)", "Q8", "§5", "SOURCE_EXPECTED_NOT_LOCATED", False, ["E-DXF-02"],
        "no curtailment rule or figure for SBT beams", "engineer confirmation", ["p.10"],
        [("SCHEDULE_CELL", "SBT rows", "ST7757.dxf", "FOUND")])
    add("S6-24", "S6", "Ln definition for the MID extent", "MID_TOP extent", 0, "SOURCE_DERIVED (Q5 confirmation)", "Q5",
        "§5 (CB)", "SOURCE_FOUND_DERIVED", False, ["E-DXF-06"],
        "every typical dimensions Ln axis to axis and L face to face (defpoints, PRE-S6); unchanged", "none",
        ["C-BEAM templates"], [("TYPICAL_DETAIL", "Ln / L dimensions", "ST7757.dxf", "FOUND")])
    add("S6-25", "S6", "T/M design-load values", "T/M tokens", 0, "EXCLUDED_DESIGN_LOAD", "", "§5 T/M stays DESIGN LOAD",
        "SOURCE_FOUND_EXPLICIT", False, [], "the C-BEAM T/M-n fields carry the unit 't/m' (design load); they never "
        "produce steel", "none", ["C-BEAM T/M fields"], [("SCHEDULE_CELL", "T/M-1..3", "ST7757.dxf C-BEAM", "FOUND")])
    return I, {"ft_long": ft_long, "ft_short": ft_short, "ftb_bottom": ftb_bottom, "sp_icon_lb": len(sp_icon),
               "sp_single_lb": len(sp_single), "cb_hook_lb": len(cb_hook_lb),
               "s5_core_topology_only": count(s5, component="STIRRUP_CORE_PATH",
                                              what_is_missing__has="LEGS / LINK TOPOLOGY NOT_VERIFIED",
                                              what_is_missing__not="DEPTH")}


R2_OCC = ("BM-1F_ROOF-B6-BL014-6C5", "BM-GF_ROOF-B21-BL001-468", "BM-GF_ROOF-B29-BL039-465", "CBO-FFRS-CB10-BL001",
          "CBO-GFRS-CB2-BL038")
R3_OCC = ("CBO-GFRS-CB4-BL016", "CBO-GFRS-CB5-BL008", "CBO-GFRS-CB8-BL024")


# --------------------------------------------------------------------------------------------------- candidates
def candidates(frozen, n):
    st = {k: v["engine_commit_stamp"] for k, v in frozen.items()}
    C = {"S4": [], "S5": [], "S6": []}

    def add(stage, cid, item, comp, scope, old, new_src, handles, auth, new_state, unlocked, kind, cond):
        C[stage].append({"CANDIDATE_ID": cid, "ITEM_ID": item, "COMPONENT": comp, "SCOPE": scope,
                         "FROZEN_BASELINE": f"{FROZEN[stage][0]}/{FROZEN[stage][1]} ({st[stage]})", "OLD_STATE": old,
                         "NEW_SOURCE": new_src, "NEW_SOURCE_HANDLES": handles, "NEW_AUTHORITY": auth,
                         "PROPOSED_NEW_STATE": new_state, "EXPECTED_COMPONENTS_UNLOCKED": unlocked, "CHANGE_KIND": kind,
                         "CONDITIONS": cond, "KG_RECALCULATED": "NO"})

    add("S4", "S4.1-C01", "S4-12", "BOTTOM_LONG", f"single-layer FT occurrences ({n['ft_long']} components)",
        "VERIFIED (straight)", "p.13 footing details: 'Long bars' drawn as a U with up-legs and 45° hooks",
        "ST7757.pdf p.13 S-REIN.D (E-PDF-01)", "SOURCE_FOUND_DERIVED (graphic)", "LOWER_BOUND",
        "none unlocked: a correction - END_LEGS + HOOKS become named missing facets", "CORRECTION_DOWNGRADE",
        "straight core kept as the lower bound; leg / hook length waits for a dimension")
    add("S4", "S4.1-C02", "S4-13", "BOTTOM_SHORT", f"single-layer FT occurrences ({n['ft_short']} components)",
        "VERIFIED (straight)", "p.13: short bars shown only in section; 'straight' not supported",
        "ST7757.pdf p.13 (E-PDF-01)", "SOURCE_EXPECTED_NOT_LOCATED", "LOWER_BOUND",
        "none unlocked: END_TREATMENT becomes a named missing facet", "CORRECTION_DOWNGRADE", "engineer may confirm")
    add("S4", "S4.1-C03", "S4-14", "BOTTOM_SHORT / BOTTOM_LONG", f"two-layer FTB occurrences ({n['ftb_bottom']} components)",
        "LOWER_BOUND (end straight)", "basis of 'straight' withdrawn (S4-12)", "E-PDF-01 / E-PDF-03",
        "SOURCE_EXPECTED_NOT_LOCATED", "LOWER_BOUND", "none: add END_TREATMENT to the missing facets", "FACET_ONLY", "")
    add("S4", "S4.1-C04", "S4-03", "BOXED", "FT rows with a printed BOXED value", "BLOCKED_UNQUANTIFIED",
        "p.13: boxed bar = inverted U, legs to the bottom-bar level, no hooks", "ST7757.pdf p.13 S-REIN.D (E-PDF-01)",
        "SOURCE_FOUND_DERIVED (graphic)", "BLOCKED_UNQUANTIFIED", "none: SHAPE facet resolved; count / diameter / "
        "orientation still missing (S4-01, S4-02, S4-04)", "FACET_ONLY", "")
    add("S4", "S4.1-C05", "S4-07", "OTHER_EXPLICIT_EXTRA (FF 2Ø16)", "FF (1 occurrence)", "BLOCKED_UNQUANTIFIED",
        "p.14 leaders: 2 top + 2 bottom Ø16 inside each cut pit wall (wall-base bars)", "ST7757.pdf p.14 (E-PDF-03); "
        "pit walls ST7757.dxf 10EA / 10EB (E-DXF-05)", "SOURCE_FOUND_DERIVED (graphic)", "BLOCKED_UNQUANTIFIED",
        "none: ASSIGNMENT + COUNT per cut wall resolved; LENGTH and wall count (2 or 4) still missing (S4-08)",
        "FACET_ONLY", "")

    add("S5", "S5.1-C01", "S5-04", "STIRRUP_CORE_PATH", f"GB occurrences blocked only by link topology "
        f"({n['s5_core_topology_only']} components)", "BLOCKED_UNQUANTIFIED (LEGS / LINK TOPOLOGY NOT_VERIFIED)",
        "p.13 sections: one closed 2-leg link per section, vector-verified", "ST7757.pdf p.13 S-REIN.D (E-PDF-02)",
        "SOURCE_FOUND_DERIVED (graphic)", "LOWER_BOUND",
        f"STIRRUP_CORE_PATH x {n['s5_core_topology_only']} (core path lower bound 2(b-2c-d)+2(h-2c-d) with c = 70 mm, "
        "valid for either note-22 cover; hooks excluded)", "UNLOCK",
        "only where width and depth are source-known (not the exterior / annex / <2.5 m / concentrated-load spans)")
    add("S5", "S5.1-C02", "S5-01", "DEVELOPMENT_SUPPORT_1/2", "GB ends at interior supports where the GB line continues",
        "BLOCKED_UNQUANTIFIED (Q7)", "p.13: GB bars run unbroken through the column", "ST7757.pdf p.13 (E-PDF-01)",
        "SOURCE_FOUND_DERIVED (graphic)", "THROUGH_SUPPORT (run extends across the support)",
        "DEVELOPMENT at interior continuing ends replaced by a through-support run (count of ends to be classified by "
        "S5.1 from the GB network nodes)", "UNLOCK", "end supports and footing ends stay blocked (S5-02)")

    add("S5", "S5.1-C03", "S5-18", "STIRRUP_CORE_PATH", "straps SB1 (SOCC-1689-1B1C) and SB3 (SOCC-1B26-1B27)",
        "BLOCKED_UNQUANTIFIED (LEGS / LINK TOPOLOGY NOT_STATED)", "SBT REMARKS icon STR2 = 2 closed links (4 legs)",
        "ST7757.dxf STR2 inserts 1FE6 / 2B11 (E-DXF-03)", "SOURCE_FOUND_DERIVED (graphic)", "LOWER_BOUND",
        "STIRRUP_CORE_PATH x 2 (outer link 2(b-2c-d)+2(h-2c-d) with c = 70 mm + the inner link's two vertical legs; "
        "inner width and hooks excluded)", "UNLOCK", "SB2 (str3) stays blocked by the 1FBB / 2ABA row conflict")
    add("S6", "S6.1-C01", "S6-04", "STIRRUP_CORE_PATH", f"LOWER_BOUND simple + CB occurrences without an icon "
        f"({n['sp_single_lb']} components)", "BLOCKED_UNQUANTIFIED (LEGS / TOPOLOGY UNRESOLVED; HOOKS)",
        "p.15 typical beam section: one closed link; same as the p.13 labelled links",
        "ST7757.pdf p.15 / p.13 S-REIN.D (E-PDF-05, E-PDF-02)", "SOURCE_FOUND_DERIVED (graphic)", "LOWER_BOUND",
        f"STIRRUP_CORE_PATH x {n['sp_single_lb']} (2(b-2c-d)+2(h-2c-d), c = 25 mm note 22; hooks excluded)", "UNLOCK",
        "occurrence already LOWER_BOUND; width not in conflict")
    add("S6", "S6.1-C02", "S6-05", "STIRRUP_CORE_PATH", f"LOWER_BOUND occurrences of B17, B19-B26 "
        f"({n['sp_icon_lb']} components)", "BLOCKED_UNQUANTIFIED", "SBT REMARKS icon STR2 = 2 closed links (4 legs)",
        "ST7757.dxf STR2 block + inserts (E-DXF-03)", "SOURCE_FOUND_DERIVED (graphic)", "LOWER_BOUND",
        f"STIRRUP_CORE_PATH x {n['sp_icon_lb']} (outer link as C01 + inner link's two vertical legs; inner width "
        "excluded)", "UNLOCK", "inner width (S6-06) and hooks (S6-07) stay missing")
    add("S6", "S6.1-C03", "S6-02", "HOOK_1 / HOOK_2 (CB top bar at end supports)", f"LOWER_BOUND CB occurrences "
        f"({n['cb_hook_lb']} components)", "BLOCKED_UNQUANTIFIED", "CB typicals: end-support top bar leg to the "
        "bottom-bar level (3 figures)", "ST7757.pdf pp.11-12 S-REIN.D (E-PDF-04)", "SOURCE_FOUND_DERIVED (graphic)",
        "LOWER_BOUND", f"HOOK x {n['cb_hook_lb']} as a 90° END_LEG lower bound = h - 2 x 25 mm - 2 d_link - d_bar "
        "(top bars at end supports only)", "UNLOCK", "interior-support and bottom-bar ends unchanged; development "
        "(S6-01) still missing")
    add("S6", "S6.1-C04", "S6-14", "ALL (B3 WITH STAIR spans)", "BM-1F_ROOF-B3-BL023-6B9, BM-GF_ROOF-B3-BL033-6B7",
        "BLOCKED (UNDEFINED_CANDIDATE_DETAIL)", "p.16 stair-beam callouts = SBT B3 row; '(With Stair)' tags on B3",
        "ST7757.pdf p.16 (E-PDF-06); ST7757.dxf 6B6-6B9, 1826-1827, SBT B3 (E-DXF-07)", "SOURCE_FOUND_DERIVED",
        "LOWER_BOUND", "TOP_MAIN 2Ø12, BOTTOM_MAIN 4Ø16, STIRRUP_COUNT 6/m over the plan run (lower bound: the beam is "
        "cranked); STAIR_EXTRA -> NOT_APPLICABLE", "UNLOCK", "cranked length, end bends and development stay missing")
    add("S6", "S6.1-C05", "S6-15", "base components (B26 planted-column span)", "BM-GF_ROOF-B26-BL014-4CC",
        "BLOCKED (Q9 planted column)", "p.15 detail adds extras only", "ST7757.pdf p.15 (E-PDF-06)",
        "SOURCE_FOUND_DERIVED", "LOWER_BOUND", "TOP_MAIN / BOTTOM_MAIN / STIRRUP_COUNT of B26 (schedule values); "
        "PLANTED_COLUMN_EXTRA stays BLOCKED (4Ø16 row split; length bound = column width + 2 x beam depth)", "UNLOCK",
        "side bars stay blocked (S6-11)")
    for stage, rows in C.items():
        for r in rows:
            check(r["PROPOSED_NEW_STATE"] not in ("VERIFIED", "VERIFIED_COMPLETE"), f"{r['CANDIDATE_ID']} never VERIFIED")
    return C


# -------------------------------------------------------------------------------------------- pending conflicts
def conflicts(s6o):
    def w(o):
        return s6o[o]["drawn_width_mm"], s6o[o]["schedule_width_mm"]
    P = [
        {"CONFLICT_ID": "PEC-01", "STAGE": "S4", "ITEM_ID": "S4-09", "TERMINAL_STATE": "PENDING_ENGINEER_CLARIFICATION",
         "SOURCE_A": "plan footing tag F", "SOURCE_A_VALUE": "F (90x80x30)", "SOURCE_B": "plan / schedule F10",
         "SOURCE_B_VALUE": "F10 (280x140x50)", "AFFECTED": "3 footing components (F|F10)",
         "NEW_EVIDENCE_THIS_ROUND": "none", "QUESTION": "Which type is the footing tagged F / F10?"},
        {"CONFLICT_ID": "PEC-02", "STAGE": "S5", "ITEM_ID": "S5-11", "TERMINAL_STATE": "SOURCE_CONFLICT",
         "SOURCE_A": "SBT row 1FBB", "SOURCE_A_VALUE": "SB2 80x50, 10Ø18 / 10Ø18", "SOURCE_B": "SBT row 2ABA",
         "SOURCE_B_VALUE": "SB2 100x50, 20Ø18 top / 10Ø16 bottom", "AFFECTED": "SB2 strap (all components)",
         "NEW_EVIDENCE_THIS_ROUND": "only 2ABA is inside the issued schedule sheet (PDF p.10); 1FBB lies below the "
                                    "sheet frame 1B2D in model space; the plan strap is drawn 987 mm wide",
         "QUESTION": "Confirm that the issued-sheet row (100x50, 20Ø18 / 10Ø16) governs SB2 (yes / no)."},
        {"CONFLICT_ID": "PEC-03", "STAGE": "S5", "ITEM_ID": "S5-07", "TERMINAL_STATE": "SOURCE_CONFLICT",
         "SOURCE_A": "P7757 annex level +0.30", "SOURCE_A_VALUE": "D <= 0.30 m", "SOURCE_B": "p.13 exterior GB section",
         "SOURCE_B_VALUE": "three bar levels (needs more depth)", "AFFECTED": "7 annex exterior GB components",
         "NEW_EVIDENCE_THIS_ROUND": "none (architectural DXF has level marks only)",
         "QUESTION": "What is the exterior ground-beam depth under the +0.30 annex?"},
        {"CONFLICT_ID": "PEC-04", "STAGE": "S5", "ITEM_ID": "S5-16", "TERMINAL_STATE": "SOURCE_CONFLICT",
         "SOURCE_A": "drawn GB band end", "SOURCE_A_VALUE": "band end", "SOURCE_B": "support face plane",
         "SOURCE_B_VALUE": "face", "AFFECTED": "6 GB occurrences (Q3B)", "NEW_EVIDENCE_THIS_ROUND": "none",
         "QUESTION": "Measure GB bars to the support face where the drawn band disagrees?"},
    ]
    for i, o in enumerate(R2_OCC, 5):
        d, s = w(o)
        P.append({"CONFLICT_ID": f"PEC-{i:02d}", "STAGE": "S6", "ITEM_ID": "S6-17", "TERMINAL_STATE": "SOURCE_CONFLICT",
                  "SOURCE_A": f"plan band ({o})", "SOURCE_A_VALUE": f"drawn width {d} mm", "SOURCE_B": "schedule width",
                  "SOURCE_B_VALUE": f"{s} mm", "AFFECTED": o, "NEW_EVIDENCE_THIS_ROUND": "none",
                  "QUESTION": f"Which width governs {s6o[o]['mark']}?"})
    for i, (o, a, b) in enumerate((("CBO-GFRS-CB4-BL016", "plan c/c [2.724, 3.75] m", "schedule [3.3, 3.7] m"),
                                   ("CBO-GFRS-CB5-BL008", "plan c/c [2.85, 4.2] m", "schedule [2.5, 4.5] m"),
                                   ("CBO-GFRS-CB8-BL024", "2 bound plan spans", "3 schedule spans")), 10):
        P.append({"CONFLICT_ID": f"PEC-{i:02d}", "STAGE": "S6", "ITEM_ID": "S6-18", "TERMINAL_STATE": "SOURCE_CONFLICT",
                  "SOURCE_A": "plan", "SOURCE_A_VALUE": a, "SOURCE_B": "C-BEAM schedule", "SOURCE_B_VALUE": b,
                  "AFFECTED": o, "NEW_EVIDENCE_THIS_ROUND": "none", "QUESTION": f"Which span data governs {o.split('-')[2]}?"})
    P.append({"CONFLICT_ID": "PEC-13", "STAGE": "S6", "ITEM_ID": "S6-19", "TERMINAL_STATE": "SOURCE_CONFLICT",
              "SOURCE_A": "C-BEAM CB3 frame", "SOURCE_A_VALUE": "middle span part of CB3 (MID1 edited, MID2 blank)",
              "SOURCE_B": "plan tag 1827", "SOURCE_B_VALUE": "middle span 'B3 WITH STAIR'", "AFFECTED": "CBO-GFRS-CB3-BL022",
              "NEW_EVIDENCE_THIS_ROUND": "the p.16 stair-beam callouts equal B3, not CB3 - consistent with tag B3, "
                                         "but no source voids the CB3 frame",
              "QUESTION": "Is the CB3 middle span a B3 stair beam, and what are CB3's MID bars?"})
    return P


# ------------------------------------------------------------------------------------------------------ writers
def write_csv(path, rows, cols=None):
    cols = cols or list(rows[0].keys())
    for c in cols:
        check("KG" not in c.upper().replace("KG_RECALCULATED", ""), f"no kg column ({c})")
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in cols})
    path.write_text(buf.getvalue(), encoding="utf-8")


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def claim():
    return {"claim_id": "PEC-CLAIM-2026-10-08-01", "kind": "PROJECT_ENGINEER_CLAIM", "version": 1,
            "recorded": CLAIM_DATE, "round": ROUND,
            "statement": "The project engineer has confirmed that the required construction / reinforcement "
                         "information is contained within the issued construction plan set.",
            "scope": "ST7757 structural set (DXF + issued PDF) and the architectural set where the structure points to "
                     "it (FOLLOW ARCH / AS PER ARCH)",
            "authorises_assumptions": False,
            "effect": "workflow only: a component not found is SOURCE_EXPECTED_NOT_LOCATED and the issued set is "
                      "exhausted again; only explicit source conflicts go back to the engineer",
            "workflow_old": "not found -> engineer required",
            "workflow_new": "not found -> SOURCE_EXPECTED_NOT_LOCATED -> exhaust the issued plan set -> only explicit "
                            "source conflicts go back to the engineer",
            "pending_separately": ["F / F10 (and other known drawing conflicts)"],
            "frozen_quantities_changed": False, "supersedes": None}


def main():
    out = HERE
    frozen = frozen_baselines()
    st_doc = ezdxf.readfile(str(src("ST7757.dxf")))
    ev, _ = dxf_evidence(st_doc)
    ev.update(arch_evidence(src("P7757.dxf")))
    ev.update(pdf_evidence(src("ST7757.pdf")))
    fr = frozen_rows()
    I, n = items(fr)
    for it in I:
        for e in filter(None, it["EVIDENCE_IDS"].split(";")):
            check(e in ev, f"{it['ITEM_ID']} cites {e}")
        if it["TERMINAL_STATE"] == "SOURCE_FOUND_DERIVED" and it["NEW_SOURCE_THIS_ROUND"] == "TRUE":
            check(any(e.startswith(("E-PDF", "E-DXF")) for e in it["EVIDENCE_IDS"].split(";")), "derived has evidence")
    C = candidates(frozen, n)
    P = conflicts(fr[4])

    reg_cols = ["ITEM_ID", "STAGE", "TOPIC", "COMPONENTS", "FROZEN_ROWS_LINKED", "OLD_STATE", "QUESTION_IDS",
                "BRIEF_TOPIC", "TERMINAL_STATE", "NEW_SOURCE_THIS_ROUND", "EVIDENCE_IDS", "WHY", "NEXT_ACTION"]
    write_json(out / "01_ENGINEER_PROJECT_CLAIM.json", claim())
    write_csv(out / "02_UNRESOLVED_MASTER_REGISTER.csv", I, reg_cols)
    graph = []
    for it in I:
        graph.append({"ITEM_ID": it["ITEM_ID"], "HOP": 0, "NODE_KIND": "OCCURRENCE_COMPONENT",
                      "NODE": it["COMPONENTS"], "SOURCE": f"frozen {it['STAGE']} unresolved register",
                      "LINK_STATE": "FOUND"})
        for k, (kind, node, source, state) in enumerate(it["_graph"], 1):
            check(kind in NODE_KINDS and state in ("FOUND", "NOT_FOUND"), f"graph node {it['ITEM_ID']}")
            graph.append({"ITEM_ID": it["ITEM_ID"], "HOP": k, "NODE_KIND": kind, "NODE": node, "SOURCE": source,
                          "LINK_STATE": state})
    write_csv(out / "03_UNRESOLVED_SOURCE_CONNECTION_GRAPH.csv", graph)
    rec_cols = ["ITEM_ID", "TOPIC", "SOURCES_SEARCHED", "EVIDENCE_IDS", "FINDING", "TERMINAL_STATE",
                "NEW_SOURCE_THIS_ROUND", "STILL_MISSING_OR_NEXT"]
    for stage, fn in (("S4", "04_S4_SOURCE_RECOVERY.csv"), ("S5", "05_S5_SOURCE_RECOVERY.csv"),
                      ("S6", "06_S6_SOURCE_RECOVERY.csv")):
        write_csv(out / fn, [{"ITEM_ID": it["ITEM_ID"], "TOPIC": it["TOPIC"], "SOURCES_SEARCHED": " | ".join(it["_searched"]),
                              "EVIDENCE_IDS": it["EVIDENCE_IDS"], "FINDING": it["WHY"], "TERMINAL_STATE": it["TERMINAL_STATE"],
                              "NEW_SOURCE_THIS_ROUND": it["NEW_SOURCE_THIS_ROUND"], "STILL_MISSING_OR_NEXT": it["NEXT_ACTION"]}
                             for it in I if it["STAGE"] == stage], rec_cols)
    for stage, fn in (("S4", "07_S4_1_CANDIDATES.csv"), ("S5", "08_S5_1_CANDIDATES.csv"), ("S6", "09_S6_1_CANDIDATES.csv")):
        write_csv(out / fn, C[stage])
    write_csv(out / "10_PENDING_ENGINEER_CONFLICTS.csv", P)
    write_csv(out / "11_SOURCE_EXPECTED_NOT_LOCATED.csv",
              [{"ITEM_ID": it["ITEM_ID"], "STAGE": it["STAGE"], "TOPIC": it["TOPIC"], "FROZEN_ROWS_LINKED":
                it["FROZEN_ROWS_LINKED"], "WHERE_SEARCHED": " | ".join(it["_searched"]), "ASK": it["NEXT_ACTION"]}
               for it in I if it["TERMINAL_STATE"] == "SOURCE_EXPECTED_NOT_LOCATED"])
    write_json(out / "13_GRAPHIC_EVIDENCE.json", {"policy": POLICY, "inputs": INPUTS, "evidence": ev,
                                                  "pdf_reader": "pypdf (pure Python, read-only, vector strokes per "
                                                                "optional-content layer); no PyMuPDF, engine PDF stack "
                                                                "untouched; renders for visual reading kept outside the "
                                                                "repository"})
    by = collections.defaultdict(collections.Counter)
    for it in I:
        by[it["STAGE"]][it["TERMINAL_STATE"]] += 1
    summary = {"round": ROUND, "policy": POLICY, "frozen_baselines": frozen, "inputs": INPUTS,
               "items": len(I), "items_by_stage": {s: sum(c.values()) for s, c in sorted(by.items())},
               "terminal_by_stage": {s: dict(sorted(c.items())) for s, c in sorted(by.items())},
               "new_source_items": sorted(it["ITEM_ID"] for it in I if it["NEW_SOURCE_THIS_ROUND"] == "TRUE"),
               "newly_resolved": sorted(it["ITEM_ID"] for it in I if it["NEW_SOURCE_THIS_ROUND"] == "TRUE" and
                                        it["TERMINAL_STATE"] in ("SOURCE_FOUND_EXPLICIT", "SOURCE_FOUND_DERIVED")),
               "withdrawn_interpretations": ["S4-12", "S4-13", "S4-14"],
               "candidates": {s: len(v) for s, v in C.items()}, "pending_conflicts": len(P),
               "candidate_counts": n, "kg_recalculated": False, "s7_started": False}
    write_json(out / "SRD_SUMMARY.json", summary)
    print(json.dumps({k: summary[k] for k in ("items_by_stage", "terminal_by_stage", "newly_resolved", "candidates",
                                              "pending_conflicts")}, indent=1))


if __name__ == "__main__":
    main()
