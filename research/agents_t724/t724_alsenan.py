"""T-724 development-villa build (research, unwired): the four open Checker findings on merged concrete / formwork pieces
closed from the drawings on the candidate of record ARCH_TAKEOFF_V3.0.72 (T-703 line index).

  (1) F-V721-1  east dome ring L-ab37afa1: do the two drawn side-bar levels define the ring depth?      (R-T724-1)
  (2) F-V714-1  T-714 SCALED soffits: own drawn edge width instead of the 0.2502 concrete-ratio width  (R-T724-2)
  (3) F-T723-3  GROUND_BEAM L-fb7a6431 index 0 .. 3.5256: one census state                            (R-T724-3)
  (4) T-721     0.378618 m2 of drawn roof-edge strip in no line: owned once or named                  (R-T724-4)

Inputs: merged repository files (sha256-pinned in PINS.json) and the drawing facts below, read by this worker on
2026-11-12 from the private copies of Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179...) and
'ST7757.pdf' p.7 (drawing facts only: handles, distances, labels; no drawing content is stored). Piece geometry is
given in a LOCAL frame (metres from the strip's west end / the corner square's inner corner), not in sheet coordinates.
Writes out/T724_FINDINGS.json and out/T724_CENSUS.md. Nothing is wired, released or VERIFIED; no candidate, released,
rule / knowledge version, registry or frozen file is touched.

    python3 -I research/agents_t724/t724_alsenan.py [--write|--check]
"""
from __future__ import annotations

import csv
import re
import hashlib
import json
import sys
from pathlib import Path

from shapely.geometry import Point, box

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t724_rules as R  # noqa: E402

D, BR = R.D, R.BR
SCHEMA = "URBAN_T724_CHECKER_FINDINGS_V1"
CANDIDATE = "ARCH_TAKEOFF_V3.0.72"
INDEX = "research/agents_t703/out/LINE_INDEX_V3_0_72.json"
T714 = "research/agents_t714/out/T714_FORMWORK_BOUNDS.json"
T402 = "research/agents_t402/HELD_LINES_T402.csv"
T721 = "research/agents_t721/out/T721_LEDGER.json"
T712 = "research/agents_t712/out/T712_LEDGER.json"
PIN_FILE = HERE / "PINS.json"
OUT_JSON = HERE / "out" / "T724_FINDINGS.json"
OUT_MD = HERE / "out" / "T724_CENSUS.md"
DXF_SHA = "9f9d1179"

# ---- drawing facts (own read, ST DXF sha 9f9d1179; ST pdf p.7) ----------------------------------------------------
RING = {
    "line_id": "L-ab37afa17f2ac5b0efd1",
    "detail": "ST p.7 'DETAIL OF DOME' (N.I.S.); sheet note: 'THE BUILDER TO WORK WITH STATED DIMENSIONS. NOT TO SCALE "
              "DRAWING.'",
    "outline": "1A0A (section outline, open at the dome springing), link 1A0B inside it",
    "depth_dimension": "182F: measured 3750 drawing units, text overridden 'AS PER ARCH' (no stated depth)",
    "link_dia": "0.008",                       # 1A29 '8T8/m' (link drawn 1A0B)
    "levels": [
        {"name": "top 3T16", "role": "top", "dia": "0.016", "tied_to_face": True, "label": "count",
         "handles": "1A47 label; circles 1A33 / 1A49 / 1A35 on the link's top edge"},
        {"name": "side 2T14/20cm level 1 (labelled)", "role": "side", "dia": "0.014", "tied_to_face": True,
         "label": "pitch", "set_id": "2T14/20cm", "handles": "1A37 label, leader 1A36 to circle 1A2B; 1A2D opposite face"},
        {"name": "side 2T14/20cm level 2 (drawn)", "role": "side", "dia": "0.014", "tied_to_face": True,
         "label": "pitch", "set_id": "2T14/20cm", "handles": "circles 1A2F / 1A31, no label of their own"},
        {"name": "bottom 3T18", "role": "bottom", "dia": "0.018", "tied_to_face": True, "label": "count",
         "handles": "1A4B label; circles 1A22 / 1A26 / 1A24 on the link's bottom edge"},
        {"name": "unlabelled circle near the top (dome shell T12/15cm lapping into the section)", "role": None,
         "dia": "0.012", "tied_to_face": False, "label": None, "handles": "1A4D (smaller circle, off the link verticals)"},
    ],
    "plan_area_readings_m2": ["1.799300", "1.7994065"],      # T-721 (line / own shapely), least taken
    "t721_at_least_m3": "0.115155",
    "alternative_m3": "0.140345",                             # Checker F-V721-1: two side levels counted
    "scaled_reading": "pitch drawn 1000 units = printed 0.20 m gives 1:5; outline 1000 x 3750 -> 0.20 x 0.75 m: a "
                      "measurement of a not-to-scale detail whose depth figure is overridden; shown, never used",
}

# drawn edge pairs of every SCALED soffit's member (perpendicular distance between the two edge LINEs, metres)
EDGES = {
    "274/278": {"width": "0.250", "f2f_note": "LINE 274 and LINE 278 parallel, 250.0 units at both ends (CB2, BM-GF-055)"},
    "5E7/5E8": {"width": "0.300", "f2f_note": "LINE 5E7 / 5E8 parallel, 300.0 (CB10, BM-1F-031 / 1F-072)"},
    "434/433": {"width": "0.400", "f2f_note": "LINE 434 / 433 skew-parallel, 400.0 perpendicular (B21, GF-109)"},
    "2CE/463": {"width": "0.200", "f2f_note": "LINE 2CE / 463 parallel, 200.0 (B29, GF-108)"},
    "5CD/5CC": {"width": "0.200", "f2f_note": "LINE 5CD / 5CC parallel, 200.0 (B6, 1F-024)"},
}

GB = {
    "line_id": "L-fb7a6431fede62e93fd5",
    "evidence": "S-BOUN bands 7FE 8.344 + 7FC 0.230 + 810 0.240 = 8.814 m2 / 0.20 = 44.07 m (own DXF read); x 0.20 x "
                "0.40 (ST p.14 '(20x40)', A-A; T-403 Gate A) = 3.5256 m3 gross; boundary columns 20 x 30 'SEE ARCH "
                "PLAN': none drawn (0 column entities inside the bands, own read), count not printed (M4 / Q-28); "
                "each takes 0.20 x 0.30 x 0.40 = 0.024 m3 of the beam",
}

# projection pieces in no line: local frames (metres). Strip: x along the strip from its west end, y outward from the
# beam's outer face. Corner square 0.20 x 0.20 (x east, y north from its SW corner); its rounded outer (NW) corner is
# ARC 316 (GF) / 647 (1F): same radius and same centre offset on both floors (own read, exact to the DXF doubles):
FILLET = {"r": 0.2313343644363808, "cx": 0.22945189872931, "cy": -0.02945189872836}  # square frame: x east, y north from its SW corner
STRIPS = [
    {"floor": "GF", "member": "BM-GF-058 projection BAND0031 (edges 2C6 / 2C7, 0.200 apart, unbroken 4.325 m)",
     "column": "366 (S-COL.BON, 0.80 x 0.25, north face = strip edge 2C6)", "length": 4.325, "col": (3.000, 3.800),
     "lines": {"L-634cefe5e8a7fb458e16": (0.0, 3.0005), "L-331d4bbef719a7f0bbca": (3.800, 4.3251)},
     "corner_arc": "316", "corner_between": "north strip BAND0031 (starts at the square's east face, 2C6 / 2C7 end "
                                            "x = 2B5) and the GF west strip (2B7 / 2B5, ends at the square's south face)"},
    {"floor": "1F", "member": "BM-1F-033 projection BAND0013 (edges 5E1 / 5E6, 0.200 apart, unbroken 4.325 m)",
     "column": "68C (S-COL.BON, 0.80 x 0.25, north face = strip edge 5E1)", "length": 4.325, "col": (3.000, 3.800),
     "lines": {"L-67f3d325019e618328eb": (0.0, 2.9987), "L-54e397fe7b1485b2e8fe": (3.800, 4.3238)},
     "corner_arc": "647", "corner_between": "north strip BAND0013 (starts at 5E7, the square's east face) and the 1F "
                                            "west strip BAND0014 L-a9d5e7dc (5E7 / 5E5, ends at y of 5E1)"},
]


def sha16(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def check_pins():
    pins = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    bad = {p: (sha16(p), v) for p, v in pins.items() if sha16(p) != v}
    if bad:
        raise R.Refused(f"input drift (sha256[:16] now, pinned): {bad}")
    return pins


def load():
    pins = check_pins()
    idx = {x["line_id"]: x for x in json.loads((ROOT / INDEX).read_text(encoding="utf-8"))["lines"]}
    t714 = {x["line_id"]: x for x in json.loads((ROOT / T714).read_text(encoding="utf-8"))["lines"]}
    with open(ROOT / T402, encoding="utf-8", newline="") as fh:
        t402 = {r["line_id"]: r for r in csv.DictReader(fh)}
    t721 = {x["line_id"]: x for x in json.loads((ROOT / T721).read_text(encoding="utf-8"))["rows"]}
    t712 = json.loads((ROOT / T712).read_text(encoding="utf-8"))
    return {"pins": pins, "index": idx, "t714": t714, "t402": t402, "t721": t721, "t712": t712}


# ---- (1) ring ---------------------------------------------------------------------------------------------------------
def finding_ring(data):
    ix = data["index"][RING["line_id"]]
    assert ix["item_code"] == "STR.CONC.BEAM" and ix["class"] == "HELD" and ix["held_low"] is None, ix
    led = data["t721"][RING["line_id"]]
    assert led["at_least_m3"] == RING["t721_at_least_m3"] and led["plan_area_readings_m2"] == RING["plan_area_readings_m2"]
    st = R.stack_depth(link_dia=RING["link_dia"], levels=RING["levels"])
    area = min(D(a) for a in RING["plan_area_readings_m2"])
    floor = BR.round_low(BR.mul(area, st["depth_m"]))
    # the Checker's alternative, reproduced to name it
    alt_depth = st["depth_m"] + D("0.014")
    alt = BR.round_low(BR.mul(area, alt_depth))
    assert str(alt) == RING["alternative_m3"], alt
    return {"finding": "F-V721-1", "line_id": RING["line_id"], "before": f"AT_LEAST {RING['t721_at_least_m3']} m3",
            "after": f"AT_LEAST {floor} m3", "changed": str(floor) != RING["t721_at_least_m3"],
            "depth_floor_m": str(st["depth_m"]), "counted_levels": st["counted"],
            "excluded_levels": [{"level": n, "why": w} for n, w in st["excluded"]],
            "not_adopted": {"two_side_levels_m3": str(alt), "two_side_levels_depth_m": str(alt_depth),
                            "why": "the second level is a drawn picture of the '/20cm' pitch in a detail marked N.I.S. "
                                   "whose sheet says 'work with stated dimensions'; the number of levels of a pitch "
                                   "set follows the depth, so it cannot bound the depth (R-T724-1)",
                            "scaled_0.75": RING["scaled_reading"]},
            "cause_named": "D-28: the ring depth is not stated (182F overridden 'AS PER ARCH'; the architect's sections "
                           "draw no ring); the upper end stays open",
            "drawing": {k: RING[k] for k in ("detail", "outline", "depth_dimension")},
            "formwork_effect": "T-714 ring formwork line keeps FLOOR_ONLY soffit 1.7993 m2 (plan band): unchanged"}


# ---- (2) scaled soffits -----------------------------------------------------------------------------------------------
def _edge_key(handles):
    a, b = handles.split()
    for k in EDGES:
        if set(k.split("/")) == {a, b}:
            return k
    raise R.Refused(f"no own edge read for {handles}")


def finding_soffits(data):
    rows, fam_shift_low = [], D(0)
    for lid, line in sorted(data["t714"].items()):
        scaled = [f for f in line["faces"] if f["dep"] == "SCALED"]
        if not scaled:
            continue
        assert line["class_after"] in ("BOUNDED", "AT_LEAST"), lid
        ix = data["index"][lid]
        assert ix["item_code"] == "STR.FORMWORK" and ix["class"] == "HELD" and ix["held_low"] is None, lid
        mlines = [m["line_id"] for m in line["member"]["lines"]]
        recs = [data["t402"][m] for m in mlines]
        keys = {_edge_key(r["edge_handles"]) for r in recs}
        recorded = {D(r["drawn_width_m"]) for r in recs}
        if len(keys) != 1 or len(recorded) != 1:
            raise R.Refused(f"{lid}: one member width expected ({keys}, {recorded})")
        key, wr = keys.pop(), recorded.pop()
        we = D(EDGES[key]["width"])
        sched = {D(re.search(r"schedule b (\d+\.\d+)", r["why_held"]).group(1)) for r in recs}
        assert len(sched) == 1
        wo = sched.pop()
        new_faces, lo_sum, hi_sum = [], D(0), D(0)
        for f in line["faces"]:
            if f["dep"] != "SCALED":
                new_faces.append(dict(f))
                lo_sum += D(f["low"]) if f["low"] is not None else D(0)
                hi_sum += D(f["high"]) if f["high"] is not None else D(0)
                continue
            fig = D(f["high"]) if wo < we else D(f["low"])          # the face at the drawn width
            f2f = max(D(r["f2f_length_m"]) for r in recs)
            res = R.scaled_face(figure=fig, edge_width=we, other_width=wo, f2f_length=f2f, recorded_width=wr)
            if not res.get("recorded_differs"):
                # denominator already the drawn edge width: T-714's face (floored from its unrounded figure) stands;
                # the recomputation from the 6 dp figure must agree within 1e-6
                assert abs(res["low"] - D(f["low"])) <= D("0.000001") and res["high"] == D(f["high"]), (lid, res, f)
                res = dict(res, low=D(f["low"]), high=D(f["high"]))
            nf = dict(f, low=str(res["low"]), high=str(res["high"]), edge_width=str(we), edge_pair=key,
                      recorded_width=str(wr), implied_length_m=str(res["implied_length_m"]),
                      length_matches_f2f=res["length_matches_f2f"])
            new_faces.append(nf)
            lo_sum += res["low"]
            hi_sum += res["high"]
        old_lo, old_hi = D(line["low"]), D(line["high"])
        if hi_sum != old_hi:
            raise R.Refused(f"{lid}: high moved {old_hi} -> {hi_sum} (only the low end may move)")
        shift = lo_sum - old_lo
        fam_shift_low += shift
        rows.append({"line_id": lid, "class": line["class_after"], "member_lines": mlines, "edge_pair": key,
                     "edge_width_m": str(we), "recorded_width_m": str(wr), "schedule_width_m": str(wo),
                     "recorded_differs": abs(wr - we) > R.EDGE_TOL, "before": f"{old_lo} .. {old_hi}",
                     "after": f"{lo_sum} .. {hi_sum}", "shift_low_m2": str(shift), "faces": new_faces})
    return {"finding": "F-V714-1", "scaled_faces": len(rows), "restated": [r for r in rows if r["recorded_differs"]],
            "stand": [r for r in rows if not r["recorded_differs"]], "family_low_shift_m2": str(fam_shift_low),
            "source_of_0.2502": "T-402 HELD_LINES_T402.csv column drawn_width_m = schedule b x the member's concrete "
                                "ratio (0.433997 / 0.34692 x 0.20 = 0.250198 -> 0.2502): the band polygon area carries "
                                "joint slivers, so it is not the edge distance; edges 274 / 278 are 0.250 exactly"}


# ---- (3) ground-beam census -------------------------------------------------------------------------------------------
def finding_gb(data):
    gb = {lid: (x["held_low"], x["held_high"]) for lid, x in data["index"].items()
          if x["item_code"] == "STR.CONC.GROUND_BEAM" and x["class"] == "HELD" and x["held_high"] is not None}
    fam = R.family_census(gb)
    st = R.census_state(*gb[GB["line_id"]])
    naive_lo = BR.add(*[D(repr(v[0])) for v in gb.values()])
    naive_hi = BR.add(*[D(repr(v[1])) for v in gb.values()])
    lo, hi, cap = BR.round_low(fam["bounded_low"]), BR.round_high(fam["bounded_high"]), BR.round_high(fam["caps_beside"])
    assert st["state"] == "HELD_BLANK_CAP" and cap == D("3.5256"), st
    return {"finding": "F-T723-3", "line_id": GB["line_id"], "index": "0.0 .. 3.5256", "state": "HELD BLANK, cap "
            "3.5256 m3 beside (AT_MOST, gross DRAWING-CONFIRMED; net = 3.5256 - n x 0.024, n not printed)",
            "evidence": GB["evidence"], "family_before_T712_form": f"{len(gb)} bounded {BR.round_low(naive_lo)} .. "
            f"{BR.round_high(naive_hi)}", "family_after": f"{fam['by_state']['BOUNDED']} BOUNDED {lo} .. {hi} + "
            f"{fam['by_state']['HELD_BLANK_CAP']} HELD BLANK with cap {cap} beside",
            "matches_T704_code_form": hi == D("1.571171"), "census": fam["by_state"],
            "t712_at_least_lines": data["t712"]["census"]}


# ---- (4) strip pieces -------------------------------------------------------------------------------------------------
def finding_pieces(data):
    out, total = [], D(0)
    for s in STRIPS:
        for lid in s["lines"]:
            r = data["t721"][lid]
            assert r["bound"] == "BLANK_NAMED", lid
        bases = {lid: box(a, 0.0, b, 0.2) for lid, (a, b) in s["lines"].items()}
        col = box(s["col"][0], -0.25, s["col"][1], 0.0)          # column footprint, south of the strip edge
        beam = box(0.0, -0.40, s["length"], 0.0)                    # beam band below the strip edge (outer face y 0)
        piece = box(s["col"][0], 0.0, s["col"][1], 0.2)
        res = R.own_piece(piece_id=f"{s['floor']}-STRIP-AT-COL", piece=piece, line_bases=bases,
                          carriers={"column " + s["column"]: col, "beam band (outer face = strip edge)": beam},
                          member=s["member"], item="D-05 / D-26 (projection: no section / mark / bars / material)",
                          sliver_m2=0.0002)
        res.update(where=f"strip piece in front of flush column {s['column']}", area_m2=str(res["area_m2"]),
                   m3_per_m_depth=str(res["m3_per_m_depth"]))
        out.append(res)
        total += D(res["area_m2"])
        sq = box(0.0, 0.0, 0.2, 0.2)
        corner = sq.intersection(Point(FILLET["cx"], FILLET["cy"]).buffer(FILLET["r"], quad_segs=20000))
        nb = {"north strip lines (start at the square's east face)": box(0.2, 0.0, 4.525, 0.2),
              "west strip line (ends at the square's south face)": box(0.0, -7.5, 0.2, 0.0)}
        res2 = R.own_piece(piece_id=f"{s['floor']}-NW-CORNER", piece=corner, line_bases=nb,
                           carriers={}, member=f"{s['floor']} NW corner of the roof-edge projection",
                           item="D-05 / D-26 (projection corner, rounded outline arc " + s["corner_arc"] + ")")
        a = BR.round_point(D(repr(corner.area)))
        res2.update(where=s["corner_between"], area_m2=str(a), m3_per_m_depth=str(a))
        out.append(res2)
        total += a
    return {"finding": "T-721 strip pieces", "pieces": out, "total_m2": str(total),
            "slab_check": "T-139 / T-241 partition: GF-063 and 1F-043 are EDGE_HELD faces with no slab m3 -> no slab "
                          "double count; the beam bands end at the strip edge (outer face) and the columns 366 / 68C lie "
                          "south of it (0 overlap)"}


def build(data):
    f1, f2, f3, f4 = finding_ring(data), finding_soffits(data), finding_gb(data), finding_pieces(data)
    assert f4["total_m2"] == "0.378618", f4["total_m2"]
    return {"schema": SCHEMA, "task": "T-724", "candidate": CANDIDATE, "dxf_sha8": DXF_SHA, "rules": R.RULES,
            "pins": data["pins"], "findings": [f1, f2, f3, f4],
            "not_claimed": "nothing wired, released or VERIFIED; the candidate is not restated (concrete round 10 / the "
                           "formwork hub wire it); no freelancer row exists for these members (NOT_COMPARABLE)"}


def census_md(doc):
    f1, f2, f3, f4 = doc["findings"]
    L = ["# T-724 census (generated by t724_alsenan.py; do not edit)", "",
         f"Candidate {doc['candidate']}; ST DXF sha {doc['dxf_sha8']}.", "",
         "| Finding | Line(s) | Before | After |", "|---|---|---|---|",
         f"| F-V721-1 ring | {f1['line_id'][:10]} | {f1['before']} | {f1['after']} (depth >= {f1['depth_floor_m']}; "
         f"2-level {f1['not_adopted']['two_side_levels_m3']} not adopted) |"]
    for r in f2["restated"]:
        L.append(f"| F-V714-1 soffit | {r['line_id'][:10]} | {r['before']} | {r['after']} (edge {r['edge_width_m']} "
                 f"vs {r['recorded_width_m']}) |")
    L.append(f"| F-V714-1 stand | {len(f2['stand'])} lines | edge width = recorded | unchanged |")
    L.append(f"| F-T723-3 | {f3['line_id'][:10]} | index {f3['index']} | {f3['state']} |")
    for p in f4["pieces"]:
        L.append(f"| strip piece | {p['piece']} | in no line | {p['state']} {p['area_m2']} m2 |")
    L += ["", f"Formwork BOUNDED family low shift: +{f2['family_low_shift_m2']} m2; ground-beam family "
              f"{f3['family_after']}; pieces {f4['total_m2']} m2.", ""]
    return "\n".join(L)


def main(argv):
    doc = build(load())
    js = json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"
    md = census_md(doc)
    if "--write" in argv:
        OUT_JSON.parent.mkdir(exist_ok=True)
        OUT_JSON.write_text(js, encoding="utf-8")
        OUT_MD.write_text(md, encoding="utf-8")
    elif "--check" in argv:
        if OUT_JSON.read_text(encoding="utf-8") != js or OUT_MD.read_text(encoding="utf-8") != md:
            print("T724 outputs stale")
            return 1
        print("T724 outputs current")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
