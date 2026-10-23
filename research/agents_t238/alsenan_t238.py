"""T-238: arched / banded opening census and the DELTA of the merged opening ledgers (development villa P7757).

Run from the repository root:  python3 -I research/agents_t238/alsenan_t238.py [--check]
Writes CENSUS_T238.csv (one row per census r3 opening + the arched features that are not census openings),
DELTA_T238.csv (old -> new -> cause, per affected line and ledger) and summary.json. --check reproduces them.

Inputs: repository files only (merged ledgers, read only, never edited):
  research/agents_t198/OPENINGS_T198.csv   census r3 (68 openings)
  research/agents_t150/OPENINGS_T150.csv   windows / doors line (T-150, merged)
  research/agents_t175/T175_OPENING_CONSEQUENCES.csv, research/agents_t201/CONSEQUENCES_T201.csv
  research/agents_t128/OPENINGS_T128_R3.csv, ROOMS_T128_R3.csv (plaster / paint rooms, merged)
  research/agents_t225/BLOCKWORK_WALL_REGISTER_V1.csv + research/agents_t227/register_delta.csv (block register)
Measured values (own reads this run, private drawings, values only; no coordinate, image or client name stored):
  Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha256 ab54dd55..): SE and NW elevation frames,
  every LINE / ARC of layers 1, W, 5, D walked; datum = the DIMENSION tick +-0.00 / +1.00 of each frame (1 unit = 1 mm).
  Drive "Alsenan chalet project" / the architectural .dwf (DWF 6, vector; research/agents_t201/w2d_reader.py): SW, NE
  elevations, sections A-A and B-B rendered and their arcs listed.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import arch_rules as R  # noqa: E402

PKG = "T-238"

# ---------------------------------------------------------------------------------------------- own measurements
# Opening line = the layer-1 jamb pair the plan width binds to + the arch chain springing from their tops (shortest
# connected path, horizontal and below-springing lines excluded). Levels from the frame's +-0.00 / +1.00 DIMENSION.
MEASURED = {
    "W15": dict(width=1.5523, spring=2.1609, crown=3.0000, segment=1.0088, length=2.5243, band=0.101,
                evidence="P7757.dxf NW frame, layer 1: jambs 2889 / 288A (+5.50 .. +7.661), 46-segment arch chain "
                         "299F .. 299E, crown +8.50 = DIMENSION 3000 (printed 300); the outer chain 0.10 outside "
                         "(DIMENSIONs 100 each side, 101 above the crown; printed 10) runs down both jambs = surround "
                         "band. Own outline 4.3632 m2 vs T-227 / Checker 4.3629 (0.0003 m2)"),
    "W16": dict(width=1.5523, spring=2.1609, crown=3.0000, segment=1.0088, length=2.5243, band=0.101,
                evidence="P7757.dxf NW frame, layer 1: jambs 2566 / 256A, 49-segment arch chain 274C .. 274B (crown "
                         "2785 / 2786); W15's outline translated (T-201); band as W15"),
    "W26": dict(width=1.2000, spring=1.0500, crown=1.7000, segment=0.6147, length=1.9709, band=0.0495,
                evidence="P7757.dxf SE frame, layer 1: jambs 2211 / 2229 of the 1.200 stair-window column, sill line "
                         "2319 at +10.80, 28-segment arch chain 1C67 .. 222E, springing +11.85, apex +12.50 = the end "
                         "of DIMENSION 2AB8 1700 (printed 170); the next line 49.5 above (DIMENSION 2AC6) is a 1.300 "
                         "chain (1C99 .. 1CA4) on the column's outer edge lines = 0.05 band, not the opening"),
}
# A-GF-01: one ARC entity (layer 5, handle 2422) between jamb lines 2420 / 2421 drawn from +0.30, in the wall beyond
# the annex cut on the SE frame (T-194 binding: dewaneya / wash arch). Chord 1.000, rise 0.2993, r 0.5673.
AGF01 = dict(chord=1.0000, rise=0.29925, spring=2.2000, floor="+0.30",
             evidence="P7757.dxf SE frame (annex section, wall beyond the cut): ARC 2422 r 0.5673 m, 28.2 .. 151.8 "
                      "deg, chord 1.000, springing +2.50 on jamb lines 2420 / 2421 from +0.30 (2.20 above the floor), "
                      "crown +2.799; no dimension printed (N09)")
# W17: curved on plan (host GLAZED); NW frame: inner pair of arch lines crown +8.500 / +8.5505 (DIMENSION 2E97 3050.5
# ends on the outer line of the pair), an archivolt pair 0.40 .. 0.45 outside it, crown +8.954 / +9.004 (DIMENSION
# 2EA5 454.3); it runs down both jambs ~0.10 outside; the window frame (layer W) stays inside the inner arch.
W17 = dict(developed_width=3.29, crown_lo=3.000, crown_hi=3.0505, surround_crown=3.5043, chord_plan_face=2.6915,
           evidence="P7757.dxf NW frame, layer 1: inner arch pair 273C / 273D (crown +8.500) and 271F / 2726 (+8.5505, "
                    "end of DIMENSION 3050.5, printed 305); archivolt pair 270C / 2710 (+8.954) and 2729 / 2731 "
                    "(+9.004, end of DIMENSION 454.3, printed 45) 0.40 .. 0.45 above the opening crown, ~0.10 outside "
                    "the jambs; window frame lines (layer W 2A4D / 2A50) stop below the inner arch")

FEATURES = [
    dict(ID="F-PORCH-ARCH", KIND="FEATURE", FLOOR="GF", view="SE (P7757.dxf)", code="FEATURE_NOT_AN_OPENING",
         measured="voussoir (stone-block) quarter arch r 1.90 m on layer 1 springing about +2.15 at the porch mouth; the "
                  "other half lies behind the annex section edge (T-194): width not decidable from this view",
         consequence="porch mouth = an open side (T-175 / T-194: not a building opening): nothing deducts it; the "
                     "arch's face, soffit and arrises are in no merged ledger: UNKNOWN (facade / Sigma owner, T-162 "
                     "lists the entrance face SE-2 under the porch only)",
         status=R.UNKNOWN),
    dict(ID="F-SE-STAIR-PANEL", KIND="FEATURE", FLOOR="GF-2F", view="SE (P7757.dxf)", code="FEATURE_NOT_AN_OPENING",
         measured="double-line arch over the 1.20 stair-window column (crown ~+13.43, DIMENSION 2AD7 876.4 above W26's "
                  "band): a recessed facade panel; W01 / W13 / W26 sit inside it on their own opening lines",
         consequence="none on the opening ledgers (the Q-32 question text '170 to where the arch starts and 88 above "
                     "it' read W26 against this panel; the drawn W26 crown is +12.50 = 1.70 above the sill)",
         status=R.DC),
    dict(ID="F-BB-GF-ARCH", KIND="FEATURE", FLOOR="GF", view="section B-B (architectural .dwf)", code="UNBOUND_FEATURE",
         measured="one circular arc in the wall beyond the B-B cut, GF main (+1.00): chord 1.255 m, rise 0.269 m, its "
                  "left end on a wall line and its right end on the head of a drawn door frame (~2.2 m above +1.00); no "
                  "jamb pair, no dimension",
         consequence="identity UNKNOWN: binding tried (B-B cut line on the DWF GF plan, looking north; section x = "
                     "plan x + offset solved from the cut walls): AMBIGUOUS, two offsets 1.85 m apart (6 of 30 lines within "
                     "0.01 m; 9 of 30 within 0.06 m, the latter fitting the W02 cut): the arc lands on the front wall "
                     "of the wash / basin space (P-GF-01 0.90 doorless, head HELD; the 45-degree W.C. doors) or on the "
                     "wall east of it; no census opening is 1.255 wide, so it is not bound; never a quantity; for the "
                     "Checker / designer (D-45 family)",
         status=R.UNKNOWN),
]

VIEWS_READ = ("P7757.dxf SE and NW frames (every LINE / ARC, chains of short oblique segments >= 6 detected); "
              "architectural .dwf SW, NE elevations, sections A-A, B-B (rendered; arcs listed)")


# ---------------------------------------------------------------------------------------------- merged ledgers
def _read(rel):
    with open(ROOT / rel, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def merged():
    m = {"t198": {r["ID"]: r for r in _read("research/agents_t198/OPENINGS_T198.csv")},
         "t150": {r["ID"]: r for r in _read("research/agents_t150/OPENINGS_T150.csv")},
         "t175": {r["opening"]: r for r in _read("research/agents_t175/T175_OPENING_CONSEQUENCES.csv")},
         "t201": {r["opening"]: r for r in _read("research/agents_t201/CONSEQUENCES_T201.csv")},
         "heads": {r["ID"]: r for r in _read("research/agents_t201/HEADS_T201.csv")},
         "t128o": _read("research/agents_t128/OPENINGS_T128_R3.csv"),
         "t128r": {r["ROW"]: r for r in _read("research/agents_t128/ROOMS_T128_R3.csv")},
         "reg": {r["wall_id"]: r for r in _read("research/agents_t225/BLOCKWORK_WALL_REGISTER_V1.csv")},
         "t227": {r["wall_id"]: r for r in _read("research/agents_t227/register_delta.csv")}}
    return m


def f(v):
    return None if v in ("", None) else float(v)


def outlines():
    o = {}
    for oid, m in MEASURED.items():
        o[oid] = R.arched_outline(oid, m["width"], m["spring"], m["crown"], m["segment"], m["length"], band_m=m["band"],
                                  window_width_m={"W15": 1.55, "W16": 1.55, "W26": 1.20}[oid])
    seg, length, _ = R.circular_segment(AGF01["chord"], AGF01["rise"])
    o["A-GF-01"] = R.arched_outline("A-GF-01", AGF01["chord"], AGF01["spring"], AGF01["spring"] + AGF01["rise"], seg,
                                    length, status=R.SS, sill_edge=False)
    return o


# ---------------------------------------------------------------------------------------------- census
def census(m, o):
    rows = []
    for oid, r in m["t198"].items():
        merged_head = f(m["t150"].get(oid, {}).get("HEIGHT_M"))
        t175 = m["t175"].get(oid, {})
        if oid in ("W15", "W16", "W26"):
            out = o[oid]
            head = merged_head if merged_head is not None else f(m["t201"].get(oid, {}).get("height_m"))
            mas = f(t175.get("block_deduction_m2")) or f(m["t201"].get(oid, {}).get("block_deduction_m2"))
            code = R.census_code("arched", True, merged_head_m=head, opening_crown_m=out["crown_m"],
                                 band_crown_m=round(out["crown_m"] + out["band_m"], 2) if oid != "W26" else None,
                                 merged_masonry_m2=mas, outline_m2=out["masonry_deduction_m2"])
            meas = (f"opening line: w {out['width_m']} x springing {out['spring_m']} + arch {out['arch_segment_m2']} "
                    f"(length {out['arch_length_m']}), crown {out['crown_m']}; band {out['band_m']} outside "
                    f"(crown {out['band_crown_m']}); outline {out['masonry_deduction_m2']} m2, Q-32 A "
                    f"{out['window_area_q32a_m2']} m2, reveal {out['reveal_lm']} m")
            ev, st = MEASURED[oid]["evidence"], R.DC
        elif oid == "A-GF-01":
            out = o[oid]
            code = R.census_code("arch", True, merged_head_m=None)
            meas = (f"drawn segmental arch: w {out['width_m']} x springing {out['spring_m']} + segment "
                    f"{out['arch_segment_m2']} (arc {out['arch_length_m']}), crown {out['crown_m']} above +0.30; "
                    f"candidate outline {out['masonry_deduction_m2']} m2 per face (never 1.00 x {out['crown_m']} = "
                    f"{out['window_area_q32a_m2']})")
            ev, st = AGF01["evidence"], R.SS
        elif oid == "A-1F-01":
            code, meas, st = "NOT_DRAWN", "no elevation or section read this run draws it (1F +5.50 on A-A / B-B: " \
                                          "rectangular doors only)", R.HELD
            ev = VIEWS_READ
        elif oid == "W17":
            code = R.census_code("arched", True, curved_on_plan=True)
            b = R.curved_plan_bound("W17", W17["developed_width"], W17["crown_lo"], W17["crown_hi"])
            meas = (f"opening crown {W17['crown_lo']:.3f} .. {W17['crown_hi']:.4f} above +5.50; archivolt to "
                    f"{W17['surround_crown']:.4f} (the census 3.50); Q-32 A on the opening line "
                    f"{b['window_q32a_range_m2'][0]} .. {b['window_q32a_range_m2'][1]} m2 (Q-39 C width 3.29) vs owner "
                    f"example 3.29 x 3.50 = 11.515")
            ev, st = W17["evidence"], R.HELD
        elif oid in m["heads"] and m["heads"][oid]["STATUS"] in R.ESTABLISHED:
            h = m["heads"][oid]
            code, st = "RECT_ON_OPENING_LINE", R.DC
            meas = (f"rectangular on {h['VIEW']}: outline width = plan width {h['WIDTH_M']} (T-201 binding), head "
                    f"{h['HEAD_ABOVE_FFL_M']} above FFL read on the outline itself; no arc, no outer chain")
            ev = VIEWS_READ
        elif oid in ("W11", "W12"):
            code, st = "RECT_ON_OPENING_LINE", "as merged (T-207)"
            meas = ("rectangular on the fence elevation: opening between the shutter leaves (T-207); the frame inside "
                    "and the leaves beside it are own items, not the opening; no arc")
            ev = "fence elevation (T-207 reading, DWF + current issue)"
        elif r["KIND"] in ("WINDOW", "DOOR") and oid != "W02" and r["HEIGHT_STATUS"] != "HELD":
            code = "RECT_ON_OPENING_LINE"
            st = R.DC if r["HEIGHT_STATUS"] == "PRINTED" else r["HEIGHT_STATUS"]
            meas = (f"rectangular; width {r['WIDTH_M']} (= plan width); height basis as merged "
                    f"({r['HEIGHT_SOURCE'][:90]}); no arc and no outer chain at the opening on the views read")
            ev = VIEWS_READ
        else:
            code, st = "HELD_ELSEWHERE", R.HELD
            meas = f"held: {(r['HOLD_CAUSE'] or r['HEIGHT_SOURCE'])[:160]}"
            ev = VIEWS_READ + "; no arc at this opening on any view read"
        rows.append({"ID": oid, "KIND": r["KIND"], "FLOOR": r["FLOOR"], "FORM_T198": r["FORM"],
                     "CODE": code, "CODE_MEANING": R.CENSUS_CODES[code], "OPENING_LINE_READING": meas,
                     "STATUS": st, "EVIDENCE": ev})
    for ft in FEATURES:
        rows.append({"ID": ft["ID"], "KIND": ft["KIND"], "FLOOR": ft["FLOOR"], "FORM_T198": "(not a census opening)",
                     "CODE": ft["code"], "CODE_MEANING": R.CENSUS_CODES[ft["code"]],
                     "OPENING_LINE_READING": ft["measured"] + " | " + ft["consequence"], "STATUS": ft["status"],
                     "EVIDENCE": ft["view"]})
    return rows


# ---------------------------------------------------------------------------------------------- delta
def delta(m, o):
    D = []
    add = D.append
    w15, w16, w26, agf = o["W15"], o["W16"], o["W26"], o["A-GF-01"]
    q32 = "Q-32 A enclosing rectangle on the OPENING line (crown 3.00), not the 0.10 band crown 3.10 (Checker 20:14)"
    # windows line
    add(R.delta_row("WINDOW.ALUMINIUM", "W15", "T-150 OPENINGS_T150.csv", "window area", "m2",
                    1.55 * f(m["t150"]["W15"]["HEIGHT_M"]), w15["window_area_q32a_m2"], R.DC, q32))
    add(R.delta_row("WINDOW.ALUMINIUM", "W16", "T-201 HEADS / CONSEQUENCES_T201.csv", "window area", "m2",
                    f(m["t201"]["W16"]["opening_m2"]), w16["window_area_q32a_m2"], R.DC, q32 + "; twin of W15"))
    add(R.delta_row("WINDOW.ALUMINIUM", "W17", "T-150 OPENINGS_T150.csv", "window area", "m2",
                    3.29 * f(m["t150"]["W17"]["HEIGHT_M"]), None, R.HELD,
                    "3.50 = the ARCHIVOLT crown (chain 305 + 45: 305 ends on the opening arch, 45 is the surround); "
                    "Q-32 A on the opening line gives 3.29 x 3.000 .. 3.0505 = 9.870 .. 10.036 m2; the owner's Q-32 / "
                    "Q-39 example 3.29 x 3.50 = 11.515 was built on a question text that read 305 as the springing and "
                    "45 as the arch rise: owner confirmation through the Lead (ERS 2.7: an owner-stated figure would "
                    "change); HELD 9.870 .. 11.515, never 0"))
    add(R.delta_row("WINDOW.ALUMINIUM", "W26", "T-150 OPENINGS_T150.csv", "window area", "m2",
                    1.20 * f(m["t150"]["W26"]["HEIGHT_M"]), w26["window_area_q32a_m2"], R.DC,
                    "confirmed: the 170 chain ends on the opening apex +12.50; the 0.05 line above is a band"))
    # blockwork
    add(R.delta_row("BLOCKWORK (1F-W00)", "W15", "T-175 T175_OPENING_CONSEQUENCES.csv", "masonry deduction", "m2",
                    f(m["t175"]["W15"]["block_deduction_m2"]), w15["masonry_deduction_m2"], R.VERIFIED,
                    "true outline (A2); already applied in the block register by T-227 r2 (MERGED ebce3d97, 4.363): "
                    "no further change to 1F-W00 net 12.863", applied_by="T-227"))
    add(R.delta_row("BLOCKWORK (1F-W00)", "W16", "T-201 CONSEQUENCES_T201.csv", "masonry deduction", "m2",
                    f(m["t201"]["W16"]["block_deduction_m2"]), w16["masonry_deduction_m2"], R.VERIFIED,
                    "as W15", applied_by="T-227"))
    reg = m["reg"]["2F-W07"]
    add(R.delta_row("BLOCKWORK (2F-W07)", "W26", "T-175 T175_OPENING_CONSEQUENCES.csv; register v1 2F-W07",
                    "masonry deduction", "m2", f(m["t175"]["W26"]["block_deduction_m2"]), w26["masonry_deduction_m2"],
                    R.DC, f"rectangle 1.20 x 1.70 to the crown -> true outline (A2); host gross {reg['gross_class']} "
                          f"{reg['gross_m2']}: net stays HELD, its deduction is corrected"))
    rg = m["reg"]["GF-W26"]
    add(R.delta_row("BLOCKWORK (GF-W26)", "A-GF-01", "T-175; register v1 GF-W26 (net bounds "
                    f"{rg['net_bounds_m2']})", "masonry deduction", "m2", "HELD", "HELD", R.HELD,
                    f"drawn outline candidate {agf['masonry_deduction_m2']} m2 (SOURCE-SUPPORTED, A6; never 1.00 x "
                    f"{agf['crown_m']} = {agf['window_area_q32a_m2']} or 1.00 x 3.50); stays HELD until the Checker "
                    "re-measures ARC 2422 / designer D-45"))
    add(R.delta_row("BLOCKWORK (1F-W16)", "A-1F-01", "T-175 / T-201", "masonry deduction", "m2", "HELD", "HELD",
                    R.HELD, "not drawn on any view read: HELD (D-45), never 0"))
    # plaster / paint faces (T-175 / T-201 consequences)
    for oid, out, src, row in (("W15", w15, "T-175", m["t175"]["W15"]), ("W16", w16, "T-201", m["t201"]["W16"]),
                               ("W26", w26, "T-175", m["t175"]["W26"])):
        for face, fam in (("face_A", row["face_A_family"]), ("face_B", row["face_B_family"])):
            add(R.delta_row(fam, oid, f"{src} consequences {face}", "finish deduction", "m2",
                            f(row[f"{face}_m2"]), out["finish_deduction_m2"], R.DC,
                            "true outline (A2): a rectangle to the crown / band crown deducts plaster and paint that "
                            "are physically built in the spandrels"))
        add(R.delta_row("REVEAL (UP-REVEAL-001)", oid, f"{src} consequences reveal_lm", "reveal length", "m.l",
                        f(row["reveal_lm"]), out["reveal_lm"], R.DC,
                        f"2 x springing + arch {out['arch_length_m']} + sill (A3); was 2 x head + 2 x width"))
        add(R.delta_row("SIGMA ARRISES (T-162)", oid, "T-162 opening arrises (arched heads at chord)",
                        "head edge: arch minus chord", "m.l", 0.0, out["arch_edge_extra_m"], R.HELD,
                        "information for the facade arris line (T-162 counts the arched head at its chord, arc extra "
                        "UNKNOWN); not applied here"))
    # T-128 rooms (plaster / paint, both methods)
    t128 = {(r["ROOM_ROW"], r["OPENING"]): r for r in m["t128o"]}
    rooms = m["t128r"]
    for (row, name), oid, out in ((("1F-13", "W15"), "W15", w15), (("ST-2F", "W26 arched"), "W26", w26)):
        r = t128[(row, name)]
        w, s, h = f(r["WIDTH_M"]), f(r["SILL_M"]), f(r["HEAD_M"])
        old_owner = w * (min(h, f(rooms[row]["OWNER_H_M"])) - s) if rooms[row]["OWNER_H_M"] not in ("HELD", "") \
            else None
        cap = f(rooms[row]["OWNER_H_M"]) if old_owner is not None else None
        new_owner = R.clipped_finish_deduction(out, cap - s)["m2"] if cap is not None else None
        add(R.delta_row("PLASTER / PAINT (T-128 owner method)", oid, f"T-128 r3 room {row}", "opening deduction",
                        "m2", old_owner if old_owner is not None else "HELD (room height, Q-72)",
                        new_owner if new_owner is not None else "HELD (room height, Q-72)",
                        R.DC if new_owner is not None else R.HELD,
                        f"band w x (min(head, H) - sill) = {w} x ({h} - {s}) -> outline (A2 / A4)"))
        add(R.delta_row("PLASTER / PAINT (T-128 drawing method)", oid, f"T-128 r3 room {row}", "opening deduction",
                        "m2", w * (h - s), out["finish_deduction_m2"], R.DC,
                        f"head {h} below every drawing height {rooms[row]['DWG_PLASTER_H_TOP_M']}: full outline"))
    r = t128[("1F-13", "W16 (twin of W15)")]
    add(R.delta_row("PLASTER / PAINT (T-128 both methods)", "W16", "T-128 r3 room 1F-13", "opening deduction", "m2",
                    "HELD", w16["finish_deduction_m2"], R.SS,
                    "T-128 held W16 as an inferred twin; T-201 (MERGED) established the head: the outline applies "
                    "when lane I takes T-201 into the plaster ledger (T-237 crosswalk)"))
    r = t128[("1F-11", "W17")]
    b = R.curved_plan_bound("W17", f(r["WIDTH_M"]), W17["crown_lo"], W17["crown_hi"])
    own_h = f(rooms["1F-11"]["OWNER_H_M"])
    add(R.delta_row("PLASTER / PAINT (T-128 owner method)", "W17", "T-128 r3 room 1F-11", "opening deduction", "m2",
                    f(r["WIDTH_M"]) * min(f(r["HEAD_M"]), own_h), None, R.HELD,
                    f"3.50 is the archivolt crown; the opening crown is 3.00 .. 3.05; curved on plan: developed "
                    f"outline HELD (A5), upper bound {b['finish_deduction_upper_m2']} m2 (3.286 x 3.05)"))
    add(R.delta_row("PLASTER / PAINT (T-128 drawing method)", "W17", "T-128 r3 room 1F-11", "opening deduction", "m2",
                    f(r["WIDTH_M"]) * f(r["HEAD_M"]), None, R.HELD,
                    f"as the owner method; upper bound {b['finish_deduction_upper_m2']} m2"))
    for row, name in (("GF-01", "arch to wash"), ("GF-02", "arch to dewaneya")):
        add(R.delta_row("PLASTER / PAINT (T-128 both methods)", "A-GF-01", f"T-128 r3 room {row}",
                        "opening deduction", "m2", "HELD", "HELD", R.HELD,
                        f"candidate outline {agf['finish_deduction_m2']} m2 (A6), stays HELD with the opening"))
    return D


# ---------------------------------------------------------------------------------------------- totals
def totals(m, o):
    t198 = m["t198"]
    eight = ["W01", "W03", "W13", "W14", "W15", "W17", "W18", "W26"]
    area = {"W01": 2.400, "W03": 28.251, "W13": 2.760, "W14": 3.920, "W15": 4.805, "W17": 11.515, "W18": 1.080,
            "W26": 2.040}
    # reproduce T-150's 8 established windows from the census widths x heights
    for k in eight:
        r = t198[k]
        if abs(float(r["WIDTH_M"]) * float(r["HEIGHT_M"]) - area[k]) > 0.0015 and k != "W03":
            raise ValueError(f"{k}: census w x h does not reproduce the T-150 area")
    before8 = round(sum(area.values()), 3)
    after = dict(area, W15=o["W15"]["window_area_q32a_m2"])
    after.pop("W17")
    after7 = round(sum(after.values()), 3)
    fl = {k: float(t198[k]["FREELANCER_W"]) * float(t198[k]["FREELANCER_H"]) for k in eight}
    fl7 = round(sum(v for k, v in fl.items() if k != "W17"), 3)
    return {"windows_T150_established_8_before_m2": before8,
            "windows_same_7_after_m2 (W17 to HELD)": after7,
            "freelancer_same_8_m2": round(sum(fl.values()), 3), "freelancer_same_7_m2": fl7,
            "engine_vs_freelancer_7": [round(after7 - fl7, 3), round((after7 - fl7) / fl7 * 100, 2)],
            "W16_T201_window_before_after_m2": [4.805, o["W16"]["window_area_q32a_m2"]],
            "W17_window_HELD_range_m2": [round(3.29 * W17["crown_lo"], 3), 11.515],
            "W17_freelancer_m2": round(fl["W17"], 3)}


# ---------------------------------------------------------------------------------------------- outputs
def csv_text(cols, rows):
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return s.getvalue()


def outputs():
    m = merged()
    o = outlines()
    c = census(m, o)
    d = delta(m, o)
    files = {"CENSUS_T238.csv": csv_text(list(c[0].keys()), c), "DELTA_T238.csv": csv_text(list(d[0].keys()), d)}
    codes = {}
    for r in c:
        codes[r["CODE"]] = codes.get(r["CODE"], 0) + 1
    summ = {"package": PKG, "census_rows": len(c), "census_openings": len(m["t198"]), "codes": dict(sorted(codes.items())),
            "outlines": {k: {kk: v[kk] for kk in ("status", "width_m", "spring_m", "crown_m", "arch_segment_m2",
                                                  "masonry_deduction_m2", "window_area_q32a_m2", "reveal_lm",
                                                  "arch_length_m", "band_crown_m")} for k, v in o.items()},
            "W17": {"opening_crown_m": [W17["crown_lo"], W17["crown_hi"]], "archivolt_crown_m": W17["surround_crown"],
                    "window_HELD_m2": [round(3.29 * W17["crown_lo"], 3), 11.515],
                    "finish_deduction_upper_m2": R.curved_plan_bound("W17", 3.286, 3.0, 3.0505)[
                        "finish_deduction_upper_m2"]},
            "windows": totals(m, o), "delta_rows": len(d),
            "finish_deduction_change_m2_per_face": {"W15": round(o["W15"]["finish_deduction_m2"] - 4.805, 3),
                                                    "W16": round(o["W16"]["finish_deduction_m2"] - 4.805, 3),
                                                    "W26": round(o["W26"]["finish_deduction_m2"] - 2.040, 3)},
            "masonry_deduction_change_m2": {"W26 (2F-W07, net HELD)": round(o["W26"]["masonry_deduction_m2"] - 2.040, 3),
                                            "W15 / W16 (1F-W00)": "applied by T-227 r2 (merged)"},
            "released_change": "none (nothing released; the delta is for lane I: T-211 / T-232 / T-237)",
            "verified_by_checker_m2": 0.0}
    files["summary.json"] = json.dumps(summ, indent=1, ensure_ascii=False) + "\n"
    return files


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    files = outputs()
    if a.check:
        bad = [n for n, t in files.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("CHECK", "PASS" if not bad else f"FAIL {bad}")
        return 0 if not bad else 1
    for n, t in files.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print(files["summary.json"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
