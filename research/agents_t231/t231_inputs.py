"""T-231: the project inputs of ARCH_TAKEOFF_V3.0.8 (URBAN_V308_INPUTS_V1) for the development villa. Research code; it
reads the merged files as committed and changes none of their quantities. Every choice cites its source. Values,
handles and BOQ ids only (no coordinates other than those inside route G line ids, no names, no drawing content).

STRAP_CONCRETE (T-174, MERGED 984ebbe1, Verifier 2026-10-23 15:06 UTC; owner Q-74 axis length):
  SB1 0.70 x 0.50 x 4.55 m axis (F8 face -> F10+F outline face) = 3.185 m2 x 0.50 = 1.5925 m3 DRAWING-CONFIRMED (the
      Checker did not re-measure SB1)
  SB2 1.00 x 0.50 x 2.2927 m axis (F11 chord face -> F6 face) = 1.1464 m3 DRAWING-CONFIRMED: Checker own re-measure
      2.2927 m / 1.1464 m3 (0.0 %), but the section rests on the issued p.10 row with D-38 open, so not VERIFIED
  SB3 0.50 x 0.40 x 3.2580 m axis (F15 face -> F3 face) = 1.629 m2 x 0.40 = 0.6516 m3 VERIFIED (Checker own re-measure
      3.2580 m, 0.6516 m3 = worker, 0.0 %)
  SB3 inside F3: strap 0.40 deep on a 0.30 footing, A_in 0.2953 m2 (0.3416 gross - column C3 0.0463, Checker own
      shapely 0.2954) x [0.10 .. 0.40] = 0.0295 .. 0.1181 m3 HELD (strap level against the footing not printed; T-230)
  SB1 inside the open F10 + F outline: A_in 0.770 m2 (column C10 0.035 removed) x [0 .. 0.50] = 0 .. 0.385 m3 HELD
      (which footing, F10 H 0.50 or F H 0.30, owner Q-31 C)
  SB2 inside F11 / F6 and SB1 inside F8, SB3 inside F15: strap depth <= footing thickness -> footing concrete, counted
      once in the footing line (T-174 table, owner FOOTING)
  supersedes the five V3.0 strap-piece lines (T-073 PLOT_EDGE_MEMBERS_V1, an earlier candidate change, named):
      BAND0003 SB1 1.5925, BAND0019 SB2 1.146382, BAND0002 SB3 0.651535 (= 3.390417), BAND0003:IN_OPEN_FOOTING_OUTLINE
      0 .. 0.402518 (1.15 m x 0.70 x 0.50, column not removed), BAND0019:IN_OPEN_FOOTING_OUTLINE 0 .. 1.406176 (the
      F11 outline is open on the strap side: T-174 closes it by its chord, the face the strap enters; the Checker
      re-measured that face on outline 1B07; inside it the strap is F11 footing concrete, D 0.50 = H
      0.50, counted once in the footing line).

PLANTED_COLUMN (T-220, MERGED 579e613d, Verifier 2026-10-23 15:58 UTC):
  FINDING OF THIS INTEGRATION (no double count, ERS s.5 WORKER 3): route G already carries the three planted columns
  as "planted column: label section x storey height" lines (released V2.9 and every V3.0.x state, 4.20 m convention):
      P-C:COL:SH06:PC@131833,50119|1F 0.588 (0.20 x 0.70, planted on GF)  = PC-1F-A (GFRS 329 'P.C 20x70')
      P-C:COL:SH06:PC@146492,50119|1F 0.420 (0.20 x 0.50, planted on GF)  = PC-1F-B (GFRS 386 'P.C 20x50')
      P-C:COL:SH04:PC@100236,60677|2F 0.420 (0.20 x 0.50, planted on 1F)  = PC-2F (FFRS 77B / text 77C 'P.C 20x50')
  Identity (own read of ST7757 dxf.dxf 9f9d1179 in this task): 329 and 386 centroids differ by 14,658.3 mm in x and 0
  in y; the two SH06 lines by 14,659 / 0 (one sheet frame, the same translation); SH06 is the GF roof slab frame that
  holds both start symbols; SH04 (the 1F roof slab frame, T-193 s.5.1) holds one planted column, 77B, the only P.C
  of that sheet; sections and storeys agree. T-217 / T-220 recorded "no line in any state" (missing scope): that is
  not so; adding the records beside these lines would have counted 1.428 m3 twice. They are superseded here.
  PC-1F-A 0.20 x 0.70 = 0.14 m2 x (beam top +5.45 -> 1F roof slab top +9.65 = 4.20) = 0.588 m3 DRAWING-CONFIRMED
      (Checker own re-measure 0.0 %; status stays DRAWING-CONFIRMED: B27 lies between sunken panels whose beam top is
      unprinted, T-213 s.4); owner split 0.483 + 0.0826 + 0.0224 beside
  PC-1F-B solid 0.10 x 4.20 = 0.420 drawing-derived, owner split HELD (D-26: framing projections of unprinted depth;
      column <= 0.345, joint >= 0.059): HELD, figure as information (task row T-231)
  PC-2F HELD: section CONFLICT 0.08 .. 0.10 m2 (text 20x50 vs two 0.20 x 0.40 outlines), stops at the B7 soffit (B7 is
      billed through it and owns the joint), roof structural top HELD (D-39); solid <= 0.350, owner column 0.276 ..
      0.345; the route line's 4.20 m through B7 counted B7's joint a second time

MEMBER_EXISTENCE (T-220, MERGED 579e613d; Checker re-measured 2F C8 on FP 10E0): five released upper column lines
  with no member on their storey's slab plan, NOT_DRAWN (consultant item D-65, never a verified 0), 2.268 m3. In the
  candidate V3.0.1 (T-126 route scope) had already set all five NOT_APPLICABLE as NOT_PRESENT (route figure kept in the
  line inputs): they left the released total in V3.0.1, so this version moves no released quantity; it turns the five
  "not applicable" lines into visible HELD lines with D-65 (an absence of a drawn member is not a measured 0). Route ids
  from the T-217 ledger (MERGED 65fef8fa: FP handle -> released line) translated to this run's SH12 frame by the one
  offset (+75,968 / +14,447) that maps all four FP positions of that ledger onto this run's lines (within 1 mm, checked
  at <= 2 mm; route ids round the label point):
      FP 10C5 C3 2F 0.42 / FP 10E4 C3 1F 0.42 / FP 10E4 C3 2F 0.42 / FP 10BD C5 2F 0.42 / FP 10E0 C8 2F 0.588

GUARD: the V3.0.7 guard inputs unchanged (research/agents_t193/t193_inputs.py, evidence version 2, no new record).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T174 = "research/agents_t174/T174_STRAPS.json"
T220 = "research/agents_t220/summary.json"
T217 = "research/agents_t217/LEDGER_T217.csv"

V30_STRAP = ("the V3.0 strap piece (T-073, PLOT_EDGE_MEMBERS_V1) changed this line; T-174 (checker-merged) measures the "
             "same strap face to face along its axis (Q-74) and now carries it")


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def _straps():
    d = {s["strap_id"]: s for s in json.loads((ROOT / T174).read_text(encoding="utf-8"))}
    sb1, sb2, sb3 = d["SB1"], d["SB2"], d["SB3"]
    assert (sb1["concrete"]["volume_m3"], sb2["concrete"]["volume_m3"], sb3["concrete"]["volume_m3"]) == (
        1.5925, 1.1464, 0.6516)
    assert (sb1["lengths"]["axis_face_to_face_m"], sb2["lengths"]["axis_face_to_face_m"],
            sb3["lengths"]["axis_face_to_face_m"]) == (4.55, 2.2927, 3.258)
    f3 = next(c for c in sb3["concrete_in_footings"] if c["footing"].startswith("F3"))
    assert f3["status"] == "HELD" and f3["range_m3"] == [0.0295, 0.1181] and f3["A_in_m2"] == 0.2953
    f10 = next(c for c in sb1["concrete_in_footings"] if c["footing"].startswith("F10+F"))
    assert f10["status"] == "HELD" and f10["A_in_m2"] == 0.77 and f10["H_m"] is None
    for s, f in (("SB2", "F11"), ("SB2", "F6"), ("SB1", "F8"), ("SB3", "F15")):
        c = next(c for c in d[s]["concrete_in_footings"] if c["footing"].startswith(f + " "))
        assert c["owner"] == "FOOTING" and c["volume_m3"] == 0.0
    return sb1, sb2, sb3, f3, f10


def strap_piece():
    sb1, sb2, sb3, f3, f10 = _straps()
    src = {"file": T174, "sha256": sha(T174), "task": "T-174 (angled strap beams at their axis length)",
           "merge_commit": "984ebbe1",
           "checker_run": "Verifier 2026-10-23 15:06 UTC (T-174 MERGED; own re-measure of SB2 / SB3 from ST7757 dxf.dxf)"}
    chk = ("Verifier 2026-10-23 15:06 (T-174 MERGED 984ebbe1): own re-measure from ST7757 dxf.dxf, SB3 edges 1B26 / 1B27 "
           "between F15 1B2A face and F3 (insert 166B) face: centreline 3.2580 m, section 50 x 40 (ST7757.pdf p.10), "
           "0.50 x 0.40 x 3.2580 = 0.6516 m3 = worker (0.0 %)")
    p10 = "ST7757.pdf p.10 Schedule of Simple Beams"
    recs = [
        {"element": "SB1", "component": "CONCRETE", "floor": "FOUNDATION", "state": "RELEASED", "value": 1.5925,
         "dims": {"kind": "PRISM", "area_m2": 3.185, "height_m": 0.5, "height_basis": "STRUCTURAL"},
         "physical_element": "GROUND_BEAMS",
         "printed": f"{p10} SB1 70 x 50; ST7757 dxf.dxf strap edges 1689 / 1B1C, F8 outline 1B24 face to the F10 + F "
                    "outline 1B1B face",
         "formula": "0.70 x 4.55 (axis, face to face, Q-74) = 3.185 m2 x 0.50 = 1.5925 m3 (both edges cross one straight "
                    "face of each footing: plan area outside the outlines = B x axis)",
         "geometry_source": "CAD_VECTOR", "guard_element": {"element_id": "SB1", "part": "CONCRETE"},
         "info": {"axis_m": 4.55, "checker_re_measure": "not re-measured by the Checker (SB1 open in the verdict)"}},
        {"element": "SB1", "component": "IN_FOOTING", "part": "F10+F", "floor": "FOUNDATION", "state": "BOUNDED",
         "range": [0.0, 0.385], "evidence_status": "HELD", "physical_element": "GROUND_BEAMS (inside an open footing outline)",
         "range_basis": "A_in 0.770 m2 x [0 (a footing at least 0.50 deep owns it) .. 0.50 (no footing under it)]",
         "reasons": ["SB1 inside the open F10 + F outline (one outline drawn round two schedule footings, F10 H 0.50 / F "
                     "H 0.30): A_in 0.770 m2 (column C10 0.035 m2 removed) is footing concrete where the footing is at "
                     "least as deep as the strap, strap concrete where it is not; which footing lies under it is owner "
                     "Q-31 C (HELD); T-230 decides every strap end"],
         "printed": "ST7757 dxf.dxf outline 1B1B (open), ST7757.pdf p.9 F10 50 / F 30",
         "guard_element": {"element_id": "SB1", "part": "IN_FOOTING_F10+F"}},
        {"element": "SB2", "component": "CONCRETE", "floor": "FOUNDATION", "state": "RELEASED", "value": 1.1464,
         "dims": {"kind": "PRISM", "area_m2": 2.2927, "height_m": 0.5, "height_basis": "STRUCTURAL"},
         "physical_element": "GROUND_BEAMS",
         "printed": f"{p10} SB2 100 x 50 (the issued row; D-38: an off-sheet 80 x 50 row); ST7757 dxf.dxf edges 1B08 / "
                    "1B09 between the F11 chord face (open outline 1B07) and the F6 face (1B19, label C6/F6 168D)",
         "formula": "1.00 x 2.2927 (axis, face to face, Q-74) = 2.2927 m2 x 0.50 = 1.14635 -> 1.1464 m3",
         "geometry_source": "CAD_VECTOR", "guard_element": {"element_id": "SB2", "part": "CONCRETE"},
         "info": {"axis_m": 2.2927,
                  "checker_re_measure": "Verifier 15:06 own re-measure axis 2.2927 m, concrete 1.1464 m3 (0.0 %); stays "
                                        "DRAWING-CONFIRMED while D-38 (section row) is open",
                  "if_d38_80x50_m3": 0.9171}},
        {"element": "SB3", "component": "CONCRETE", "floor": "FOUNDATION", "state": "RELEASED", "value": 0.6516,
         "dims": {"kind": "PRISM", "area_m2": 1.629, "height_m": 0.4, "height_basis": "STRUCTURAL"},
         "physical_element": "GROUND_BEAMS", "verified_by": chk,
         "printed": f"{p10} SB3 50 x 40; ST7757 dxf.dxf edges 1B26 / 1B27 between the F15 face (1B2A) and the F3 face "
                    "(insert 166B, label C3/F3 168F)",
         "formula": "0.50 x 3.2580 (axis, face to face, Q-74) = 1.629 m2 x 0.40 = 0.6516 m3",
         "geometry_source": "CAD_VECTOR", "guard_element": {"element_id": "SB3", "part": "CONCRETE"},
         "info": {"axis_m": 3.258}},
        {"element": "SB3", "component": "IN_FOOTING", "part": "F3", "floor": "FOUNDATION", "state": "BOUNDED",
         "range": [0.0295, 0.1181], "evidence_status": "HELD", "physical_element": "GROUND_BEAMS (inside a footing)",
         "range_basis": "A_in 0.2953 m2 x [0.10 (strap spans the full footing thickness) .. 0.40 (no vertical overlap)]",
         "reasons": ["SB3 (0.40 deep) enters F3 (0.30 thick): inside the outline A_in 0.2953 m2 (0.3416 gross - column C3 "
                     "0.0463; Checker own overlap 0.2954) the excess depth is strap concrete in no footing; the strap "
                     "level against the footing is not printed (designer item; T-230 decides strap-end ownership): "
                     "0.0295 .. 0.1181 m3, never 0"],
         "printed": "ST7757.pdf p.9 F3 160 x 140 x 30; p.10 SB3 50 x 40",
         "guard_element": {"element_id": "SB3", "part": "IN_FOOTING_F3"},
         "info": {"checker_re_measure": "Verifier 15:06 own shapely overlap 0.3417 m2 - C3 0.0463 = 0.2954 m2 = worker"}},
    ]
    sup = [
        {"element_id": "P-C:GROUND_BEAMS:FOUNDATION:BAND0003", "floor": "FOUNDATION", "carried": 1.5925,
         "earlier_change": V30_STRAP, "why": "SB1 strap concrete: carried by SB1:CONCRETE (same 1.5925 m3)"},
        {"element_id": "P-C:GROUND_BEAMS:FOUNDATION:BAND0019", "floor": "FOUNDATION", "carried": 1.146382,
         "earlier_change": V30_STRAP,
         "why": "SB2 strap concrete 2.293 x 1.00 x 0.50: carried by SB2:CONCRETE on the DXF axis 2.2927 m (1.1464 m3)"},
        {"element_id": "P-C:GROUND_BEAMS:FOUNDATION:BAND0002", "floor": "FOUNDATION", "carried": 0.651535,
         "earlier_change": V30_STRAP,
         "why": "SB3 strap concrete: carried by SB3:CONCRETE on the DXF axis 3.2580 m (0.6516 m3)"},
        {"element_id": "P-C:GROUND_BEAMS:FOUNDATION:BAND0003:IN_OPEN_FOOTING_OUTLINE", "floor": "FOUNDATION",
         "carried": [0.0, 0.402518], "earlier_change": V30_STRAP,
         "why": "SB1 inside the open F10 + F outline (1.15 m x 0.70 x 0.50, column not removed): carried by "
                "SB1:IN_FOOTING:F10+F (0 .. 0.385, column C10 removed)"},
        {"element_id": "P-C:GROUND_BEAMS:FOUNDATION:BAND0019:IN_OPEN_FOOTING_OUTLINE", "floor": "FOUNDATION",
         "carried": [0.0, 1.406176], "earlier_change": V30_STRAP,
         "why": "SB2 'inside the open F11 outline': the outline is closed by its chord where the strap enters (T-174; "
                "the Checker re-measured that face); inside it the strap is F11 footing concrete (D 0.50 = H 0.50), "
                "counted once in the footing line, so no strap concrete is carried here"},
    ]
    return {"piece": "STRAP_CONCRETE", "item_code": "STR.CONC.STRAP", "unit": "m3", "source": src,
            "scope": {"floors": ["FOUNDATION"], "supersede_lines": sup, "other_elements": []},
            "records": recs,
            "declared_totals": {"released_added": 3.3905, "superseded_value": 3.390417, "item_move": 0.000083,
                                "bounded_added": [0.0295, 0.5031], "bounded_superseded": [0.0, 1.808694]},
            "line_group": {"STRAPS": "PARTIALLY VERIFIED: concrete 3.3905 m3 (SB3 0.6516 VERIFIED, SB1 1.5925 and SB2 "
                                     "1.1464 DRAWING-CONFIRMED, D-38 open on SB2); strap ends SB3 / F3 0.0295 .. 0.1181 "
                                     "and SB1 / F10 + F 0 .. 0.385 HELD (T-230, Q-31 C); bars (SB2 HELD D-38, anchorage "
                                     "D-36), side formwork 9.449 m2 (OQ-10) and excavation (Q-21 C) a later package"}}


def _planted():
    d = json.loads((ROOT / T220).read_text(encoding="utf-8"))
    pc = {p["id"]: p["on_reference_beam_register"] for p in d["planted"]}
    a, b, c = pc["PC-1F-A"], pc["PC-1F-B"], pc["PC-2F"]
    assert a["status"] == "DRAWING-CONFIRMED" and abs(a["solid_m3"][0] - 0.588) < 1e-9 and a["height_m"] == 4.2
    assert abs(a["section"]["area_lo"] - 0.14) < 1e-9 and (a["base"], a["top"]) == (5.45, 9.65)
    assert abs(b["solid_m3"][0] - 0.42) < 1e-9 and b["owner_method"]["status"] == "HELD"
    assert c["section"]["status"] == "CONFLICT" and c["solid_m3"] is None and abs(c["solid_upper_bound_m3"] - 0.35) < 1e-9
    return d, a, b, c


def planted_piece():
    d, a, b, c = _planted()
    src = {"file": T220, "sha256": sha(T220), "task": "T-220 (planted columns and upper column lines without a member)",
           "merge_commit": "579e613d",
           "checker_run": "Verifier 2026-10-23 15:58 UTC (T-220 MERGED; own re-measure of PC-1F-A and 2F C8 on FP 10E0)"}
    recs = [
        {"element": "PC-1F-A", "component": "CONCRETE", "floor": "1F", "state": "RELEASED", "value": 0.588,
         "dims": {"kind": "PRISM", "area_m2": 0.14, "height_m": 4.2, "height_basis": "STRUCTURAL"},
         "physical_element": "COLUMNS",
         "printed": "ST7757 dxf.dxf GFRS 329 (ANSI35 start symbol, 700 x 200) on B27 90x85, FFRS 66A (SOLID, its own "
                    "storey), text 544 'P.C 20x70'; levels T-214 (beam top +5.45, 1F roof slab top +9.65)",
         "formula": "0.20 x 0.70 = 0.14 m2 x (9.65 - 5.45 = 4.20, carrying beam top -> slab top; B4 / CB13 / CB11 are "
                    "billed net of it, so the column owns the joint) = 0.588 m3",
         "geometry_source": "CAD_VECTOR", "guard_element": {"element_id": "PC-1F-A", "part": "WHOLE"},
         "info": {"owner_split_m3": {"column": 0.483, "joint": 0.0826, "slab_part": 0.0224,
                                     "rule": a["owner_method"]["rule"]},
                  "checker_re_measure": "Verifier 15:58 own re-measure 0.14 x 4.20 = 0.588 m3, owner split 0.588 (0.0 % "
                                        "on both); status stays DRAWING-CONFIRMED (B27 between sunken panels whose beam "
                                        "top is unprinted, T-213 s.4)",
                  "beam_below": "B27 keeps the junction under the column (R-CONC-OWN-1); its route line is short 0.119 "
                                "m3 under it (T-229, not changed here)"}},
        {"element": "PC-1F-B", "component": "CONCRETE", "floor": "1F", "state": "UNQUANTIFIED", "evidence_status": "HELD",
         "physical_element": "COLUMNS",
         "reasons": ["planted column PC-1F-B: solid 0.10 x 4.20 = 0.420 m3 drawing-derived (GFRS 386 -> FFRS 69D, text "
                     "548 'P.C 20x50', on B26 65x85), but the owner split is HELD: two framing projections of unprinted "
                     "depth touch it (D-26), so the column part is an upper bound (<= 0.345) and the joint a lower bound "
                     "(>= 0.059)"],
         "printed": "ST7757 dxf.dxf GFRS 386 / FFRS 69D 500 x 200, text 548",
         "guard_element": {"element_id": "PC-1F-B", "part": "WHOLE"},
         "info": {"solid_m3_drawing_derived": 0.42, "owner_column_upper_m3": 0.345, "owner_joint_lower_m3": 0.059}},
        {"element": "PC-2F", "component": "CONCRETE", "floor": "2F", "state": "UNQUANTIFIED", "evidence_status": "HELD",
         "physical_element": "COLUMNS",
         "reasons": ["planted column PC-2F: section CONFLICT 0.08 .. 0.10 m2 (text 77C 'P.C 20x50' vs outlines 77B / 778 "
                     "0.20 x 0.40, no dimension chain, no schedule row)",
                     "it stops at the soffit of B7 20x75, which is billed through it and owns the joint (R-CONC-OWN-1); "
                     "the roof structural top is not printed (D-39)"],
         "printed": "ST7757 dxf.dxf FFRS 77B (ANSI35) on B19 40x75, SFRS 778 (SOLID), text 77C",
         "guard_element": {"element_id": "PC-2F", "part": "WHOLE"},
         "info": {"solid_upper_bound_m3": 0.35, "owner_column_m3": [0.276, 0.345],
                  "route_4_20_through_b7": "the superseded route line ran 4.20 m through B7 and counted B7's joint twice"}},
    ]
    why_route = ("route G 'planted column: label section x storey height' (4.20 m convention, planted on the storey "
                 "below): the same physical column as the record; adding the record beside it would count it twice")
    sup = [
        {"element_id": "P-C:COL:SH06:PC@131833,50119|1F", "floor": "1F", "carried": 0.588,
         "why": f"PC-1F-A (GFRS 329 'P.C 20x70', 0.20 x 0.70): {why_route}; carried by PC-1F-A:CONCRETE (0.588 m3, "
                "now from the beam top to the slab top)"},
        {"element_id": "P-C:COL:SH06:PC@146492,50119|1F", "floor": "1F", "carried": 0.42,
         "why": f"PC-1F-B (GFRS 386 'P.C 20x50', 0.20 x 0.50): {why_route}; carried by PC-1F-B:CONCRETE (HELD, D-26)"},
        {"element_id": "P-C:COL:SH04:PC@100236,60677|2F", "floor": "2F", "carried": 0.42,
         "why": f"PC-2F (FFRS 77B / text 77C 'P.C 20x50'): {why_route}; carried by PC-2F:CONCRETE (HELD: section "
                "CONFLICT, B7 soffit, D-39)"},
    ]
    return {"piece": "PLANTED_COLUMN", "item_code": "STR.CONC.COLUMN", "unit": "m3", "source": src,
            "scope": {"floors": ["1F", "2F"], "element_markers": [":PC@"], "supersede_lines": sup,
                      "other_elements": []},
            "records": recs,
            "declared_totals": {"released_added": 0.588, "superseded_value": 1.428, "item_move": -0.84},
            "line_group": {"PLANTED_COLUMNS": "PC-1F-A 0.588 m3 DRAWING-CONFIRMED (Checker re-measured 0.0 %); PC-1F-B "
                                              "HELD (owner split, D-26; solid 0.420 as information); PC-2F HELD "
                                              "(section CONFLICT, D-39); links not printed (no steel line here)"}}


# FP handle -> route line of this run: the T-217 ledger's released line, translated by the one offset that maps all four
# FP positions of that ledger onto this run's SH12 lines; route ids round the label point, so each must lie within 2 mm
OFFSET = (75968, 14447)
EXIST = [("10C5", "C3", "2F", 0.42, "P-C:COL:SH12:C3@243004,52949|2F"),
         ("10E4", "C3", "1F", 0.42, "P-C:COL:SH12:C3@254464,51322|1F"),
         ("10E4", "C3", "2F", 0.42, "P-C:COL:SH12:C3@254464,51322|2F"),
         ("10BD", "C5", "2F", 0.42, "P-C:COL:SH12:C5@243102,55481|2F"),
         ("10E0", "C8", "2F", 0.588, "P-C:COL:SH12:C8@256160,53630|2F")]


def _t217_lines():
    import csv
    rows = list(csv.DictReader((ROOT / T217).read_text(encoding="utf-8").splitlines()))
    out = {}
    for fp, mark, st, q, eid in EXIST:
        r = next(r for r in rows if r["member"] == fp and r["storey"] == st)
        assert r["status"] == "NOT_DRAWN" and abs(float(r["released_m3"]) - q) < 1e-9 and r["mark"] == mark
        head, xy = r["released_line"].split("@")
        x, y = (int(v) for v in xy.split("|")[0].split(","))
        h2, xy2 = eid.split("@")
        x2, y2 = (int(v) for v in xy2.split("|")[0].split(","))
        assert h2 == head and eid.endswith("|" + st) and abs(x + OFFSET[0] - x2) <= 2 and abs(y + OFFSET[1] - y2) <= 2
        out[(fp, st)] = eid
    return out


def existence():
    d = json.loads((ROOT / T220).read_text(encoding="utf-8"))
    rel = d["released_lines"]
    assert d["totals"] == {"released_without_member_m3": 2.268, "not_drawn_count": 5}
    ids = _t217_lines()
    src = {"file": T220, "sha256": sha(T220), "task": "T-220 (planted columns and upper column lines without a member)",
           "merge_commit": "579e613d",
           "checker_run": "Verifier 2026-10-23 15:58 UTC (T-220 MERGED; 2F C8 on FP 10E0 NOT_DRAWN AGREES, own SFRS "
                          "read)"}
    lines = []
    for (fp, mark, st, q, _eid), r in zip(EXIST, rel):
        assert fp in r["line"] and mark in r["line"] and r["storey"] == st and r["existence"] == "NOT_DRAWN"
        assert abs(r["released_m3"] - q) < 1e-9
        lines.append({"element_id": ids[(fp, st)], "floor": st, "carried": q, "consultant_item": "D-65",
                      "earlier_change": "V3.0.1 (ROUTE_G_SCOPE_V1, T-126) set this line NOT_APPLICABLE as NOT_PRESENT "
                                        "(no outline on the storey's slab plan) and kept the route figure; T-220 "
                                        "(checker-merged) classifies it NOT_DRAWN, a consultant item (parapet stub "
                                        "possible): an absence of a drawn member is HELD, never a verified 0",
                      "why": f"{mark} {st} on FP {fp}: {r['roof_over']}; the storey's slab plan draws no member there "
                             "(T-217 SOLID / ANSI35 convention), the architectural plans show a terrace with a parapet "
                             "('CHECK ARCHITECTURAL DETAIL OF PARAPET': a parapet stub is possible)",
                      "evidence": r["evidence"],
                      **({"verified_by": "Verifier 15:58 own SFRS re-read: no outline, hatch, beam text or slab bar at "
                                         "the position; FFRS 69A SOLID (the 1F column ends under the 1F roof)"}
                         if fp == "10E0" else {})})
    return {"source": src, "item_code": "STR.CONC.COLUMN", "unit": "m3", "lines": lines, "declared_total": 2.268}


def inputs(project_id):
    sys.path.insert(0, str(ROOT / "research/agents_t193"))
    sys.path.insert(0, str(ROOT / "research/agents_t187"))
    import t193_inputs as L7   # noqa: E402  (the V3.0.7 guard inputs, unchanged)
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V308_INPUTS_V1", "project": project_id, "pieces": [strap_piece(), planted_piece()],
            "existence": existence(), "guard": g}
