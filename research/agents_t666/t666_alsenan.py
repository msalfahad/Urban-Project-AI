"""T-666 ledger (development villa): junction-square ownership of the five R-T660-2 unlabelled beam pieces (Checker
F-T661-1) and the boundary band L-6290a9f3 on the plot-line stretches where the building stands (T-659 residual).
Research only: nothing wired, nothing released, no candidate line changed here (wiring is lane I).

Committed inputs (no drawing is opened here):
  candidate lines  research/agents_t661/out/LINE_INDEX_V3_0_62.json (ARCH_TAKEOFF_V3.0.62, Checker Gate B PASS)
  band bound       research/agents_t659/out/T659_LEDGER.json (row L-6290a9f3, merged 907ace46)
Printed facts re-read this run (own read, Drive 'Alsenan chalet project': 'ST7757 dxf.dxf' and 'ST7757.pdf', decoded
into .work/private only; `t666_extract.py` prints every value below from the DXF; the PDF pages were read by eye):
  READS: local frames per piece in m (x across the piece from its first edge, y along it); no absolute coordinate.

    python3 -I research/agents_t666/t666_alsenan.py [--write]
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t666_rules as R  # noqa: E402

D = Decimal
INDEX = ROOT / "research" / "agents_t661" / "out" / "LINE_INDEX_V3_0_62.json"
T659 = ROOT / "research" / "agents_t659" / "out" / "T659_LEDGER.json"
OUT = HERE / "out" / "T666_LEDGER.json"

DEPTHS_W020 = ("0.40", "1.20")  # ST p.10 simple-beam schedule, breadth-0.20 rows: 0.40 (B1-B3) .. 1.20 (B15) (R-T660-2)

# ---- (a) the five pieces: local frames (m) --------------------------------------------------------------------------
# Each entry: line id, drawn width, the candidate extent that F-T661-1 questioned (y from .. to), the end squares with
# the members around them (columns / through spans as plan boxes in the same local frame; a neighbour line that stops at
# the piece's face is drawn as an ADJACENT box, which never covers the square), depths beside.
PIECES = {
    "BAND0008.1": dict(
        line_id="L-dc8cbfc119d006ff3927", floor="2F", edges="399 / 39C", width="0.20",
        extent=("0", "1.60"),
        reads=("edges 399 / 39C start on the south outer line 392 (the south band's inner-face line is drawn in two "
               "pieces 394 / 395 that stop at the piece's edges); column 418 (0.20 x 0.70) from y 1.40; crossing band "
               "398 / 3A2 (y 1.40 .. 1.60) lies inside column 418; south band lines BAND0004 (B1) / BAND0005 (B2) "
               "measured 1.80 / 3.00 m between the piece's faces and the next faces (route G net plan)"),
        squares=[(("0", "0", "0.20", "0.20"), "south band zone"), (("0", "1.40", "0.20", "1.60"), "crossing band 398 / 3A2")],
        columns=[("418 -> L-53f223b06db14ac41d47 (C9 2F, HELD)", ("0", "1.40", "0.20", "2.10"))],
        through=[("BAND0004 L-b835f51602e05704c045", ("-1.80", "0", "0", "0.20")),
                 ("BAND0005 L-2999807a87e55d057be3", ("0.20", "0", "3.20", "0.20")),
                 ("BAND0007.1 L-13031ccc9cc57a0f3465", ("-1.80", "1.40", "0", "1.60")),
                 ("BAND0007.2 L-b2efc69ac20dee663880", ("0.20", "1.40", "3.20", "1.60"))],
        abut_depth={"south band zone": "0.40"}),
    "BAND0011.1": dict(
        line_id="L-7c3edce23ec8faa3d674", floor="2F", edges="3A1 / 39E", width="0.20",
        extent=("0", "1.60"),
        reads=("edges 3A1 / 39E start on the outer line 392 (south band inner-face lines 393 / 394 stop at them); "
               "column 41E (0.20 x 0.50) from y 1.40; crossing band 398 (y 1.40 .. 1.60) ends inside column 41E"),
        squares=[(("0", "0", "0.20", "0.20"), "south band zone"), (("0", "1.40", "0.20", "1.60"), "crossing band 398 / 3A2")],
        columns=[("41E -> L-33a9b7728781fcba12e2 (C2 2F, HELD)", ("0", "1.40", "0.20", "1.90"))],
        through=[("BAND0003 L-bcfa6dddf762d6cf0fb3", ("-2.50", "0", "0", "0.20")),
                 ("BAND0004 L-b835f51602e05704c045", ("0.20", "0", "2.00", "0.20")),
                 ("BAND0007.1 L-13031ccc9cc57a0f3465", ("0.20", "1.40", "2.00", "1.60"))],
        abut_depth={"south band zone": "0.40"}),
    "BAND0006.1": dict(
        line_id="L-d62d2fcf3d0023ad1ad1", floor="2F", edges="397 / 3AD", width="0.20",
        extent=("0", "3.30"),
        reads=("west band edges 397 / 3AD start on the outer line 392 (south band inner-face line 393 starts at 3AD: "
               "the SW corner square is drawn inside the west band); column 424 (0.25 x 0.50) from y 3.10; crossing "
               "band 772 / 773 (y 3.10 .. 3.30) starts at the column's east face"),
        squares=[(("0", "0", "0.20", "0.20"), "SW corner"), (("0", "3.10", "0.20", "3.30"), "crossing band 772 / 773")],
        columns=[("424 -> L-c10e2945d582b5a03126 (C3 2F, HELD)", ("0", "3.10", "0.25", "3.60"))],
        through=[("BAND0003 L-bcfa6dddf762d6cf0fb3", ("0.20", "0", "2.70", "0.20")),
                 ("BAND0002 L-46f3fb2ab0f763994f26", ("0.25", "3.10", "2.70", "3.30"))],
        abut_depth={"SW corner": "0.40"}),
    "BAND0001.3": dict(
        line_id="L-8d031491396379f0cbb1", floor="2F", edges="38D / 38E", width="0.20",
        extent=("0", "1.13"),
        # local frame rotated: y along the north band from column 415's east face, x across it (0 = inner face 38E)
        reads=("north band edges 38D / 38E run from column 415's east face to the east outer line 39A (1.13); the east "
               "band's inner face 39B stops at 38E and BAND0009 (B7 20x75) is measured 6.60 = outer south line to 38E: "
               "the NE corner square is drawn inside the north band and billed by no other line"),
        squares=[(("0", "0.93", "0.20", "1.13"), "NE corner")],
        columns=[("415 (0.60 x 0.20), west of the extent", ("0", "-0.60", "0.20", "0"))],
        through=[("BAND0009 L-f4a95b8019ae333d81ae (B7 20x75)", ("-6.60", "0.93", "0", "1.13"))],
        abut_depth={"NE corner": "0.75"}),
    "BAND0005.1": dict(
        line_id="L-f83c4a469845c7e14dfa", floor="1F", edges="5C6 / 5E3", width="0.20",
        extent=("-0.45", "0.80"),
        reads=("edges 5C6 / 5E3 start on B23's north face 5E1; B23 (5E4 / 5E1, 0.45) runs through; its east span "
               "BAND0031.2 (B23 45x75, 3.30 m between column 68E and column 67F faces) covers the square; column 691 "
               "(0.25 x 0.50) from y 0.80"),
        squares=[(("0", "-0.45", "0.20", "0"), "B23 crossing")],
        columns=[("691 -> L-cc702b8541c15fdfd98c (C3 1F, HELD)", ("0", "0.80", "0.25", "1.30"))],
        through=[("BAND0031.2 (B23 45x75, RELEASED)", ("-0.60", "-0.45", "2.70", "0"))],
        through_depth="0.75"),
}

BAND_STRETCHES = {  # t666_extract.py (b): band centre line under the building's 0.30 exterior G.B, m
    "side 1 lower neighbour, G.B F8 / 7D4": dict(cl="10.43", in_footings="2.33", relation="DISJOINT",
                                                 why="ST p.1 note 2: exterior ground beams on the neighbour side cast "
                                                     "above AND below black brick built up from foundation level"),
    "side 1 lower neighbour, G.B FC / 7D0": dict(cl="18.77", in_footings="10.60", relation="DISJOINT",
                                                 why="ST p.1 note 2 (as above)"),
    "street lower, G.B 136 / 7D5": dict(cl="6.60", in_footings="1.40", relation="DISJOINT",
                                        why="ST p.13 'Ground Beams for exterior walls': G.B from the GF slab level to the "
                                            "outer normal ground level ('FOLLOW ARCH.', D-35) on 10 cm blinding; ST p.14 "
                                            "A-A: lower beam at the base, brick 'AS PER EXCAVATION DEPTH BELOW N.G. LEVEL' "
                                            "between; no note names what fills the street side (masonry, not concrete)"),
    "sea lower, G.B FD / 7E0": dict(cl="7.80", in_footings="4.25", relation="DISJOINT",
                                    why="as the street stretch"),
}


def piece_rows(index):
    rows = []
    for band, p in PIECES.items():
        before = index[p["line_id"]]
        owners, ends = [], []
        for sq, label in p["squares"]:
            kind, who = R.square_owner(sq, columns=p["columns"], through=p["through"], piece_id=p["line_id"])
            owners.append({"square": label, "owner_kind": kind, "owner": who, "area_m2": None})
            ends.append((sq[1], sq[3], (kind, who)))
        L = R.owned_length(p["extent"], ends)
        lo, hi = R.envelope(p["width"], L, *DEPTHS_W020)
        exposures = []
        for sq, label in p["squares"]:
            o = next(x for x in owners if x["square"] == label)
            area = (D(sq[2]) - D(sq[0])) * (D(sq[3]) - D(sq[1]))
            o["area_m2"] = str(area)
            if o["owner_kind"] == "PIECE" and label in p.get("abut_depth", {}):
                e = R.depth_exposure("PIECE", area, d_other=p["abut_depth"][label], d_piece_low=DEPTHS_W020[0],
                                     d_piece_high=DEPTHS_W020[1])
                if e[1] > 0:
                    exposures.append({"what": f"GAP below the piece soffit at the {label} if the abutting member "
                                              f"({p['abut_depth'][label]} deep) continues to the outer face",
                                      "m3": [str(e[0]), str(e[1])]})
            if o["owner_kind"] == "THROUGH":
                e = R.depth_exposure("THROUGH", area, d_other=p["through_depth"], d_piece_low=DEPTHS_W020[0],
                                     d_piece_high=DEPTHS_W020[1])
                if e[1] > 0:
                    exposures.append({"what": f"piece below the through member's soffit ({p['through_depth']}) inside "
                                              f"its footprint, only if the piece is deeper than it", "m3": [str(e[0]), str(e[1])]})
        near = D(p["extent"][1]) - D(p["extent"][0]) - sum((D(s[0][3]) - D(s[0][1]) for s in p["squares"]), D(0))
        rows.append({
            "line_id": p["line_id"], "element": f"{p['floor']} {band}", "edges": p["edges"], "reads": p["reads"],
            "squares": owners, "owned_length_m": str(L), "all_near_face_length_m": str(near),
            "before_V3_0_62": [before["held_low"], before["held_high"]],
            "after": [str(lo), str(hi)], "status": "HELD_BOUNDED_AS_DRAWN",
            "delta_m3": [str(lo - D(str(before["held_low"]))), str(hi - D(str(before["held_high"])))],
            "length_term": "route G face-to-face length replaced by the drawn edge length (exact on the DXF)",
            "exposures_beside": exposures,
        })
    return rows


def band_row(index, t659):
    b = next(r for r in t659["rows"] if r["line_id"] == "L-6290a9f3d93f38cd46d6")
    cand = index["L-6290a9f3d93f38cd46d6"]
    st, total, free = [], D(0), D(0)
    for k, s in BAND_STRETCHES.items():
        cl, inf = D(s["cl"]), D(s["in_footings"])
        own = R.stretch_ownership(shared_length=cl, band_width="0.20", band_depth_low="0.40", band_depth_high="0.60",
                                  relation=s["relation"])
        st.append({"stretch": k, "band_centre_line_m": s["cl"], "inside_footings_m": s["in_footings"],
                   "free_m": str(cl - inf), "relation": s["relation"], "evidence": s["why"],
                   "ownership": own["status"], "deduction_m3": str(own["deduction_m3"])})
        total += cl
        free += cl - inf
    return {
        "line_id": "L-6290a9f3d93f38cd46d6", "element": cand["element_id"],
        "before_V3_0_62": [cand["held_low"], cand["held_high"]],
        "T659_bound": [b["low"], b["high"]],
        "after": [b["low"], b["high"]], "status": "HELD_BOUNDED_AS_DRAWN",
        "continues_under_building_stretches": True,
        "reads": ("FOUNDATION PLAN (ST p.2): closed S-BOUN pair 1658 / 1659 (0.20, centre line 91.94) with ONE "
                  "ANSI37 hatch 1657 over the whole ring: the band is drawn on all four sides, including under the "
                  "three stretches where the building stands on the plot line; GROUND BEAMS PLAN (ST p.3): the "
                  "building's 0.30 exterior G.B (F8 / 7D4, FC / 7D0, 136 / 7D5, FD / 7E0) on the same plot line; the "
                  "N.G.-level boundary pieces 7FE / 7FC / 810 abut the building G.B ends (no overlap)"),
        "stretches": st,
        "shared_centre_line_m": str(total), "shared_free_m": str(free),
        "owned_once": ("the band line bills the foundation-level prism, the G.B lines bill the N.G.-level prisms "
                       "(title depths, R-T658-1 / 3 / 8); no 3-D intersection: nothing removed, nothing counted twice"),
        "wiring_note": "V3.0.62 still carries the single reading 7.2204 (T661_BOUNDARY_BAND not wired); the bound to "
                       "wire is the T-659 one, unchanged by T-666",
    }


def build():
    idx = {l["line_id"]: l for l in json.loads(INDEX.read_text())["lines"]}
    t659 = json.loads(T659.read_text())
    rows = piece_rows(idx)
    lo_b = sum((D(str(r["before_V3_0_62"][0])) for r in rows), D(0))
    hi_b = sum((D(str(r["before_V3_0_62"][1])) for r in rows), D(0))
    lo_a = sum((D(r["after"][0]) for r in rows), D(0))
    hi_a = sum((D(r["after"][1]) for r in rows), D(0))
    return {
        "schema": "T666_LEDGER_V1", "candidate": "ARCH_TAKEOFF_V3.0.62 (NOT RELEASED)",
        "rules": ["R-T666-1", "R-T666-2", "UP-CONC-JOINT-001", "R-CONC-OWN-1 (proposed)", "R-T660-2"],
        "pieces": rows,
        "pieces_totals": {"before": [str(lo_b), str(hi_b)], "after": [str(lo_a), str(hi_a)],
                          "delta": [str(lo_a - lo_b), str(hi_a - hi_b)]},
        "F_T661_1": {
            "checker_near_face_lengths": "1.200 / 1.200 / 0.930 / 2.900 would leave the south squares of BAND0008.1 "
                                         "/ BAND0011.1, the NE corner of BAND0001.3 and the SW corner of BAND0006.1 "
                                         "in NO line (4 x 0.016 .. 0.048 m3): refused (never in neither)",
            "checker_far_face_reading": "the lengths 1.400 / 1.400 / 3.100 are right, but the square they own is at the "
                                        "outer end; the square at the crossing band lies inside the column, which owns "
                                        "it to the slab top (UP-CONC-JOINT-001)",
            "residual_m3": "0.000 from ownership; length term to the drawn edges +0.000144 / +0.000432",
        },
        "band": band_row(idx, t659),
    }


def main(argv=None):
    argv = argv or sys.argv[1:]
    data = build()
    text = json.dumps(data, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        OUT.write_text(text)
    print(json.dumps({"pieces_totals": data["pieces_totals"], "band": data["band"]["after"]}, indent=1))


if __name__ == "__main__":
    main()
