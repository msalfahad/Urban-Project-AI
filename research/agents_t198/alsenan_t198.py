"""T-198 Alsenan (development villa): opening census r3 and the downstream deltas it causes, from repository files only.

Usage (Python 3.11, from the repository root):
    python3 -I research/agents_t198/alsenan_t198.py            # writes OPENINGS_T198.csv, DOWNSTREAM_T198.csv,
                                                               #        ELEVATION_ONLY_T198.csv, summary.json
    python3 -I research/agents_t198/alsenan_t198.py --check    # rebuilds in memory, compares byte for byte

Inputs (committed, read only): research/agents_t150/OPENINGS_T150.csv (census r2, Checker MERGED b35666a; never edited),
agents_t175 (hosts / consequences / net block), agents_t143 (block runs), agents_t128 (plaster / paint openings r3),
alsenan_lintels_s8_6 (lintel binding and QTO), agents_t194 (consistency), agents_t162 (Sigma opening list).
Readings typed below (READINGS) were made this run by worker 2 on Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip
(P7757.dxf) and Alsenan_Architectural_P7757_Pages_07-08 p.7; each cites its DIMENSION handle or sheet. No drawing, no
coordinate, no client name is committed."""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import census_r3 as C                                                   # noqa: E402

EXTRA = ("SILL_LEVEL_M", "HEAD_LEVEL_M", "FFL_M", "HEAD_ABOVE_FFL_M", "LEVEL_BASIS", "LEVEL_SOURCE", "PCS_STATUS",
         "PCS_REASON", "R3_CHANGE")

# ---------------------------------------------------------------------------------------------------- own readings ---
READINGS = {
    "W01": dict(ffl_m=1.00, sill_level_m=2.00, head_level_m=4.00, chain_base_m=0.15, chain_parts_m=[1.85, 2.00],
                source=("P7757.dxf SE elevation frame: level-marker block A$C4EB10A95 with text '+0.15' (the chain base; "
                        "the same frame's markers '+0.30' / '+4.30' are 4000 units apart = 1 unit per mm, and DIMENSION "
                        "245B 1000.0 runs +-0.00 -> +1.00); W01 chain DIMENSION 2A72 1850.0 (+0.15 -> +2.00) and 2A80 "
                        "2000.0 (+2.00 -> +4.00), printed 185 / 200 on Pages_05-06 p.6. FFL +1.00: plan LEVEL mark '+1.00' "
                        "in the stair hall, inside face of W01's wall; '+0.15' outside it (court). The window stands beside "
                        "the stair flights: the floor under it is not one flat level, so a band or soffit check reads the "
                        "absolute levels +2.00 / +4.00, and 'above FFL' means above the +1.00 hall floor")),
    "W03": dict(ffl_m=1.00, sill_level_m=1.00, head_level_m=5.30, chain_base_m=0.30, chain_parts_m=[0.70, 4.30],
                source=("P7757.dxf NW elevation frame: DIMENSION 29EE 1000.0 (+-0.00 -> +1.00, level-marker block with "
                        "text '+1.00'); chain 2E5E 1150.0 (-0.85 -> +0.30), 2E6C 700.0 (+0.30 -> +1.00), 2E7A 4300.0 "
                        "(+1.00 -> +5.30), 2E88 200.0 (+5.30 -> +5.50 = 1F FFL); printed 115 / 70 / 430 / 20 on "
                        "Pages_07-08 p.8. FFL +1.00 = GF master bed room / pool-court glazing line (T-150, T-175)")),
}

# ------------------------------------------------------------------------------------------- the three openings ---
ADD = [
    dict(ID="P-GF-01", KIND="OPENING", FLOOR="GF", BOQ_LINE="OPENING.PASSAGE_NO_LEAF", CLASS_STATUS=C.DC,
         CLASS_EVIDENCE=("doorless opening between the GF stair hall and the basin space: no leaf, no door block, two "
                         "head lines drawn on the plan (engine marks head_lines 2); T-128 r3 rows ST-GF / GF-11 "
                         "'doorway (no leaf drawn)', faces 0.890 / 0.891"),
         LEAVES="", FORM="doorway (no leaf)", WIDTH_M="0.90", WIDTH_BASIS="jamb to jamb",
         WIDTH_SOURCE=("DXF band opening (engine GF OP-020 PASSAGE, jambs column / masonry); T-175 trace: 0.90 jamb to "
                       "jamb on the face that carries both jambs (1.10 on the face where a 0.20 cross wall ends)"),
         HEIGHT_M="", SILL_M="0.00", HEIGHT_STATUS="HELD",
         HEIGHT_SOURCE="no sheet prints its head (sections A-A / B-B do not cut it); S8.6 OP-GF-020: an S1 beam band lies "
                       "over the whole opening, head vs beam soffit not established (Q-HEAD-UNDER-BEAM)",
         MATERIAL="none", MATERIAL_SOURCE="no leaf drawn", WALL_T_M="0.20", SIDE_A="GF stair hall",
         SIDE_B="GF basin space (wash lobby)", ENGINE_REF="GF OP-020", PRIOR_REF="T-175 P-GF-01; S8.6 OP-GF-020",
         FREELANCER_KEY="none", VERDICT="NOT COMPARABLE",
         NOTE="new to the census (found by T-175, confirmed by T-194 MISSING_FROM_LIST); no supply item; reveals, head "
              "soffit, finishes and the GF-W14 deduction follow from its head",
         HOLD_CAUSE="head not printed (D-45 family); Q-55 C is a door rule and does not apply to a leafless opening",
         LEVEL_BASIS="ABOVE_FFL (sill at the floor: no step drawn)", FFL_M="1.00",
         LEVEL_SOURCE="plan LEVEL mark '+1.00' in the stair hall beside the opening; the basin space prints no level of "
                      "its own"),
    dict(ID="P-1F-01", KIND="OPENING", FLOOR="1F", BOQ_LINE="OPENING.PASSAGE_NO_LEAF", CLASS_STATUS=C.DC,
         CLASS_EVIDENCE=("doorless opening between the 1F east master bed room and its entry: no leaf, two head lines "
                         "drawn (engine head_lines 2); T-128 r2 fix (a): 'its 1.29 m doorless opening to its entry', the "
                         "mouth strip at the same plan point joined into room 1F-11"),
         LEAVES="", FORM="doorway (no leaf)", WIDTH_M="1.30", WIDTH_BASIS="jamb to jamb",
         WIDTH_SOURCE="DXF band opening (engine 1F OP-009 PASSAGE, jambs masonry / closure); S8.6 OP-1F-021 1300",
         HEIGHT_M="", SILL_M="0.00", HEIGHT_STATUS="HELD",
         HEIGHT_SOURCE="no sheet prints its head; S8.6 binds a schedule lintel L2 150 x 200 under no structural member "
                       "(LT-OP-1F-021, released): the head is the lintel underside, its level not printed",
         MATERIAL="none", MATERIAL_SOURCE="no leaf drawn", WALL_T_M="0.15", SIDE_A="1F east master bed room",
         SIDE_B="its entry (same room, T-128 1F-11)", ENGINE_REF="1F OP-009", PRIOR_REF="T-175 P-1F-01; S8.6 OP-1F-021",
         FREELANCER_KEY="none", VERDICT="NOT COMPARABLE",
         NOTE="new to the census (T-175 / T-194); outside the hand runs 1F-W14 / 1F-W15 (T-143 L1 = L2b, the 1.30 under "
              "openings_other 0.65 + 0.65): the masonry ABOVE its lintel is in no run",
         HOLD_CAUSE="head not printed (D-45 family)", LEVEL_BASIS="ABOVE_FFL (sill at the floor)", FFL_M="5.50",
         LEVEL_SOURCE="plan LEVEL marks '+5.50' on the 1F"),
    dict(ID="P-GF-05", KIND="OPENING", FLOOR="GF", BOQ_LINE="OPENING.PASSAGE_NO_LEAF", CLASS_STATUS=C.DC,
         CLASS_EVIDENCE=("mouth of the side passage in the court-facing GF wall line, between two column jambs: no leaf, "
                         "no glazing, no head line on the plan (engine head_lines 0); the SW elevation (Pages_07-08 p.7) "
                         "draws it between two vertical lines with a HEAD line across and a face above it up to the "
                         "top band (re-read this run); S8.6 OP-GF-012: an S1 beam band over the whole opening"),
         LEAVES="", FORM="passage mouth (no leaf)", WIDTH_M="1.20", WIDTH_BASIS="jamb to jamb",
         WIDTH_SOURCE="DXF band opening (engine GF OP-007 PASSAGE, column jambs both sides); S8.6 OP-GF-012 1200",
         HEIGHT_M="", SILL_M="0.00", HEIGHT_STATUS="HELD",
         HEIGHT_SOURCE="no sheet prints the head; plan (no head line) and SW elevation (head line) DIFFER on whether a "
                       "head below the beam exists; S8.6 Q-HEAD-UNDER-BEAM",
         MATERIAL="none", MATERIAL_SOURCE="no leaf, no glazing drawn", WALL_T_M="0.20", SIDE_A="side passage (outdoors)",
         SIDE_B="court (outdoors)", ENGINE_REF="GF OP-007", PRIOR_REF="T-175 P-GF-05 (open side); T-194; S8.6 OP-GF-012",
         FREELANCER_KEY="none", VERDICT="NOT COMPARABLE",
         NOTE="new to the census (T-194: drawn on SW as an opening under a head); both sides outdoors at +0.15: no "
              "masonry deduction (in no run), no threshold established, Sigma head + soffit only",
         HOLD_CAUSE="head not printed; plan vs elevation differ on the head (designer)",
         LEVEL_BASIS="ABOVE_FFL (court / passage +0.15, no step)", FFL_M="0.15",
         LEVEL_SOURCE="plan LEVEL marks '+0.15' in the court 1.9 m outside it and in the passage 3.5 m inside it"),
]

PCS_W02 = ("HELD", "T-181 Checker verdict faa04202: the plan draws one 6.33 opening, the render (T-161 F23) two windows "
                   "with a pier; count 1 or 2 not settled (designer D-53)")


def _read(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def build():
    census = _read(RES / "agents_t150" / "OPENINGS_T150.csv")
    t175c = {r["opening"]: r for r in _read(RES / "agents_t175" / "T175_OPENING_CONSEQUENCES.csv")}
    t175n = {r["row_id"]: r for r in _read(RES / "agents_t175" / "T175_NET_BLOCK_BY_WALL.csv")}
    t143 = {r["row_id"]: r for r in _read(RES / "agents_t143" / "T143_BLOCK_BY_WALL_RUN.csv")}
    t128 = _read(RES / "agents_t128" / "OPENINGS_T128_R3.csv")
    t128r = {r["ROW"]: r for r in _read(RES / "agents_t128" / "ROOMS_T128_R3.csv")}
    lint = {r["OPENING_ID"]: r for r in _read(RES / "alsenan_lintels_s8_6" / "04_OPENING_LINTEL_BINDING_MATRIX.csv")}
    lqto = {}
    with open(RES / "alsenan_lintels_s8_6" / "06_LINTEL_CONCRETE_QTO.csv", encoding="utf-8", newline="") as fh:
        rd = csv.reader(fh)
        hdr = next(rd)
        for row in rd:
            lqto[row[1]] = dict(zip(hdr, row))
    t194 = {r["opening_id"]: r for r in _read(RES / "agents_t194" / "CONSISTENCY_T194.csv")}
    t162 = {r["CENSUS_IDS (T-150)"] for r in _read(RES / "agents_t162" / "OPENINGS_T162.csv")}

    # --- re-datum (own readings; level and chain must agree) ---
    red, notes = {}, {}
    for oid, rd_ in READINGS.items():
        s, h, basis = C.redatum(ffl_m=rd_["ffl_m"], sill_level_m=rd_["sill_level_m"], head_level_m=rd_["head_level_m"],
                                chain_base_m=rd_["chain_base_m"], chain_parts_m=rd_["chain_parts_m"])
        old = next(r for r in census if r["ID"] == oid)
        red[oid] = {"SILL_M": f"{s:.2f}"}
        notes[oid] = (f"SILL_M {old['SILL_M']} -> {s:.2f} above FFL (r2 held the {'chain part' if oid == 'W01' else 'level'}); "
                      f"head above FFL {h:.2f}; height {old['HEIGHT_M']} unchanged")
        red[oid].update({"SILL_LEVEL_M": f"{rd_['sill_level_m']:+.2f}", "HEAD_LEVEL_M": f"{rd_['head_level_m']:+.2f}",
                         "FFL_M": f"{rd_['ffl_m']:+.2f}", "HEAD_ABOVE_FFL_M": f"{h:.2f}", "LEVEL_BASIS": basis,
                         "LEVEL_SOURCE": rd_["source"]})
        assert abs((h - s) - float(old["HEIGHT_M"])) < 0.005, oid
    pcs = {}
    for r in census:
        if r["BOQ_LINE"] == "WINDOW.ALUMINIUM":
            pcs[r["ID"]] = PCS_W02 if r["ID"] == "W02" else ("SETTLED", "one window drawn, class settled")
    for r in census:
        if r["ID"] in red:
            continue
        if r["SILL_M"] not in ("", None) and r["ID"] not in red:
            red[r["ID"]] = {"LEVEL_BASIS": "ABOVE_FFL (r2 value; T-194 found no other mixed basis)"}
    adds = []
    for a in ADD:
        row = {k: v for k, v in a.items()}
        adds.append(row)
        notes[a["ID"]] = "added in r3 (missing from r2)"
    rev = C.Revision(additions=adds, redatums=red, pcs=pcs, notes=notes)
    r3 = C.revise(census, rev, EXTRA)
    for a in ADD:            # the level columns of the additions
        row = next(r for r in r3 if r["ID"] == a["ID"])
        for k in ("LEVEL_BASIS", "FFL_M", "LEVEL_SOURCE"):
            row[k] = a[k]
        row["PCS_STATUS"], row["PCS_REASON"] = "NOT_A_SUPPLY_ITEM", "no leaf, no glazing: no door or window pcs"

    # --- downstream ledger ---
    D = []

    def line(change, oid, boq, owner, unit, before, bst, after, ast, note):
        def f(v):
            return "" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))
        delta = ""
        if isinstance(before, float) and isinstance(after, float):
            delta = f"{after - before:+.3f}"
        elif before != after:
            delta = "status change" if (before is None and after is None) else "see note"
        else:
            delta = "0" if before is not None else ("status change" if bst != ast else "none")
        D.append({"CHANGE": change, "OPENING": oid, "BOQ_LINE": boq, "OWNER_LEDGER": owner, "UNIT": unit,
                  "BEFORE": f(before), "BEFORE_STATUS": bst, "AFTER": f(after), "AFTER_STATUS": ast, "DELTA": delta,
                  "NOTE": note})

    # C1 P-GF-01 (inside GF-W14's gross)
    w14 = t175n["GF-W14"]
    clear14 = 3.75   # T-143 GF-W14: the lowest member over the run (B7 BM-GF-026 h 0.75 -> 3.75), T-175 bounds basis
    pgf01 = C.Opening("P-GF-01", "PASSAGE", 0.90, None, "BLOCK", True, 0.20, clear_height_m=clear14, edge="THRESHOLD")
    c = C.consequences(pgf01)
    gross14 = float(w14["gross_m2_t143"])
    net = C.wall_net(gross14, [pgf01])
    assert f"{net[2][0]:.3f} .. {net[2][1]:.3f}" == w14["net_bounds_m2"].strip(), (net, w14["net_bounds_m2"])
    line("C1 add", "P-GF-01", "census row", "T-150 -> T-198", "row", None, "absent", "OPENING.PASSAGE_NO_LEAF", C.DC,
         "width 0.90 DRAWING-CONFIRMED, head HELD; no supply item (no leaf)")
    line("C1 add", "P-GF-01", "opening m2 (finishes / register)", "T-181 register", "m2", None, "absent", None, C.HELD,
         "0.90 x head, head not printed: HELD, never 0")
    line("C1 add", "P-GF-01", "block deduction GF-W14 (black 0.20)", "T-175 / T-176", "m2", None, t175c["P-GF-01"]["block_status"],
         c["BLOCK_DEDUCTION_M2"][0], c["BLOCK_DEDUCTION_M2"][1],
         f"already HELD in T-175 (found there): GF-W14 net stays HELD, bounds {w14['net_bounds_m2']} m2 on the "
         f"PROVISIONAL gross {gross14:.3f} (0.90 x clear {clear14:.2f}); no change for T-176")
    line("C1 add", "P-GF-01", "plaster / paint face deductions (2 faces)", "T-128 r3 ST-GF + GF-11", "m2", None, C.HELD, None,
         C.HELD, "T-128 already lists it ('doorway, no leaf drawn', faces 0.890 / 0.891, HELD): unchanged")
    line("C1 add", "P-GF-01", "reveal (2 jambs + head)", "T-175", "m.l", None, t175c["P-GF-01"]["reveal_lm_status"], None,
         c["REVEAL_LM"][1], "0.90 + 2 x head: HELD; depth 0.20 (frameless, wall thickness) DRAWING-CONFIRMED")
    line("C1 add", "P-GF-01", "head soffit (internal plaster / paint)", "none yet (T-128 has no soffit line)", "m2", None,
         "not measured", c["HEAD_SOFFIT_M2"][0], c["HEAD_SOFFIT_M2"][1],
         "0.90 x 0.20: a member spans it (plan head lines; S8.6 S1 beam band); extent independent of the head level")
    line("C1 add", "P-GF-01", "threshold", "T-175", "m.l", float(t175c["P-GF-01"]["edge_m"]), C.DC, c["THRESHOLD_LM"][0],
         c["THRESHOLD_LM"][1], "unchanged (already in T-175's 42.22)")
    lg = lint["OP-GF-020"]
    line("C1 add", "P-GF-01", "lintel L1 (S8.6 OP-GF-020)", "S8.6", "m3", None, lg["DECISION"], None, lg["DECISION"],
         f"unchanged: {lg['REASON']}; S8.6 sensitivity only {lqto['OP-GF-020']['M3']} m3 ({lqto['OP-GF-020']['LANE']})")

    # C2 P-1F-01 (outside the runs; lintel released)
    lq = lqto["OP-1F-021"]
    bearing = 0.40
    lint_len = float(lq.get("LENGTH_MM") or 0) / 1000 if lq.get("LENGTH_MM") else None
    clear1f = float(t143["1F-W15"]["height_m_weighted"])          # 4.04: slab 1F-025 soffit (T-143)
    p1f01 = C.Opening("P-1F-01", "PASSAGE", 1.30, None, "BLOCK", False, 0.15, lintel_bearing_m=bearing,
                      lintel_status=C.DC, clear_height_m=clear1f, lintel_depth_m=0.20, edge="THRESHOLD")
    c = C.consequences(p1f01)
    b = C.masonry_above_head_bounds(p1f01)
    line("C2 add", "P-1F-01", "census row", "T-150 -> T-198", "row", None, "absent", "OPENING.PASSAGE_NO_LEAF", C.DC,
         "width 1.30 DRAWING-CONFIRMED, head HELD; no supply item")
    line("C2 add", "P-1F-01", "opening m2", "T-181 register", "m2", None, "absent", None, C.HELD, "1.30 x head: HELD")
    line("C2 add", "P-1F-01", "block deduction (1F-W14 / 1F-W15)", "T-175", "m2", None, C.NA, None, c["BLOCK_DEDUCTION_M2"][1],
         "outside the measured runs (T-143 L1 = L2b): nothing to deduct, deducting again would be a double deduction")
    line("C2 add", "P-1F-01", "masonry ABOVE the lintel (black 0.15), in no run", "T-143 / T-176 (block lane)", "m2", None,
         "not measured", c["MASONRY_ABOVE_HEAD_M2"][0], c["MASONRY_ABOVE_HEAD_M2"][1],
         f"SCOPE GAP: built (S8.6: lintel under no member, masonry beyond both jambs) but in no T-143 row; 1.30 x "
         f"({clear1f:.2f} slab soffit - head - 0.20 lintel); bounds {b[0]:.3f} .. {b[1]:.3f} m2 "
         f"({b[0] * 0.15:.3f} .. {b[1] * 0.15:.3f} m3), never a quantity")
    line("C2 add", "P-1F-01", "lintel L2 150 x 200 (S8.6 LT-OP-1F-021)", "S8.6", "m", lint_len, "RELEASED (S8.6)",
         c["LINTEL_LENGTH_M"][0], "RELEASED (S8.6)",
         f"unchanged: the lintel line already carries this opening ({lq['M3']} m3, {lq['LANE']}); 1.30 + 2 x 0.40 "
         f"bearing = {c['LINTEL_LENGTH_M'][0]:.2f} m reproduces S8.6's length")
    r11 = t128r["1F-11"]
    ph_owner, ph_dwg = float(r11["OWNER_H_M"]), float(r11["DWG_PLASTER_H_TOP_M"])
    line("C2 add", "P-1F-01", "plaster / paint faces ABOVE the head (2 faces)", "T-128 r3 1F-11", "m2", None,
         "not measured", None, C.HELD,
         f"SCOPE GAP: T-128 joins bed room and entry through the opening (mouth strip), so the two wall faces above the "
         f"head are in no room face; 2 x 1.30 x (H - head): owner method H {ph_owner:.2f} -> bounds 0 .. "
         f"{2 * 1.30 * ph_owner:.3f}; drawing method H {ph_dwg:.2f} -> 0 .. {2 * 1.30 * ph_dwg:.3f}; HELD on the head")
    line("C2 add", "P-1F-01", "head soffit (internal plaster / paint)", "none yet", "m2", None, "not measured",
         c["HEAD_SOFFIT_M2"][0], c["HEAD_SOFFIT_M2"][1], "1.30 x 0.15 under the released lintel")
    line("C2 add", "P-1F-01", "reveal (2 jambs + head)", "T-175", "m.l", None, t175c["P-1F-01"]["reveal_lm_status"], None,
         c["REVEAL_LM"][1], "1.30 + 2 x head: HELD; depth 0.15 DRAWING-CONFIRMED. T-128 already plasters the two "
         "0.15 jamb faces as wall: the jamb part of a reveal finish must not be counted again")
    line("C2 add", "P-1F-01", "threshold", "T-175", "m.l", float(t175c["P-1F-01"]["edge_m"]), C.DC, c["THRESHOLD_LM"][0],
         c["THRESHOLD_LM"][1], "unchanged")

    # C3 P-GF-05 (open-air passage mouth, host NONE)
    pgf05 = C.Opening("P-GF-05", "PASSAGE", 1.20, None, "NONE", False, 0.20, faces=(None, None), spanned=True,
                      edge="UNKNOWN")
    c = C.consequences(pgf05)
    lg = lint["OP-GF-012"]
    line("C3 add", "P-GF-05", "census row", "T-150 -> T-198", "row", None, "absent", "OPENING.PASSAGE_NO_LEAF", C.DC,
         "width 1.20 DRAWING-CONFIRMED, head HELD; KIND passage (no leaf, no glazing on plan or SW): no supply item, "
         "window pcs unaffected")
    line("C3 add", "P-GF-05", "opening m2", "T-181 register", "m2", None, "absent", None, C.HELD, "1.20 x head: HELD")
    line("C3 add", "P-GF-05", "block deduction", "T-175", "m2", None, t175c["P-GF-05"]["block_status"], None,
         c["BLOCK_DEDUCTION_M2"][1], "open side, in no run: nothing built to deduct from (unchanged)")
    line("C3 add", "P-GF-05", "wall / beam face ABOVE the head (both faces)", "T-143 / T-162", "m2", None, "not measured",
         None, C.UNKNOWN, "the SW elevation draws a face above the head line; S8.6 puts an S1 beam (400) over the whole "
         "opening; head level, beam soffit at this bay and the material between are not printed: UNKNOWN (designer)")
    line("C3 add", "P-GF-05", "head soffit (exterior plaster / Sigma)", "T-162", "m2", None, "not measured",
         c["HEAD_SOFFIT_M2"][0], c["HEAD_SOFFIT_M2"][1], "1.20 x 0.20 under whatever spans it (beam or head)")
    line("C3 add", "P-GF-05", "Sigma opening reveal (head + jambs)", "T-162", "m.l",
         None, "absent (not in the T-162 facade list)" if "P-GF-05" not in t162 else "listed", None, C.HELD,
         "head 1.20 known + 2 x head height HELD; the jambs are column faces: whether T-162's column arrises already "
         "count them is not established (no double count until checked)")
    line("C3 add", "P-GF-05", "threshold", "T-175", "m.l", float(t175c["P-GF-05"]["edge_m"]), C.DC, None, C.UNKNOWN,
         "-1.200 m.l from the established thresholds: no door, no level change (court +0.15 / passage +0.15), no strip "
         "drawn; any edge there is an outdoor-floor joint (OWNER_RULE_OUTDOOR_FLOORS), not a door threshold")
    line("C3 add", "P-GF-05", "lintel L2 (S8.6 OP-GF-012)", "S8.6", "m3", None, lg["DECISION"], None, lg["DECISION"],
         f"unchanged: {lg['REASON']}; S8.6 sensitivity only {lqto['OP-GF-012']['M3']} m3")

    # C4 / C5 re-datum (W01, W03)
    for oid, chg in (("W01", "C4 re-datum"), ("W03", "C5 re-datum")):
        old = next(r for r in census if r["ID"] == oid)
        new = next(r for r in r3 if r["ID"] == oid)
        area = round(float(old["WIDTH_M"]) * float(old["HEIGHT_M"]), 3)
        line(chg, oid, "census SILL_M (above FFL)", "T-150 -> T-198", "m", float(old["SILL_M"]), "mixed basis",
             float(new["SILL_M"]), C.DC, f"head above FFL {float(old['SILL_M']) + float(old['HEIGHT_M']):.2f} -> "
             f"{new['HEAD_ABOVE_FFL_M']}; absolute {new['SILL_LEVEL_M']} / {new['HEAD_LEVEL_M']} (own read)")
        line(chg, oid, "opening m2 (w x h)", "T-150 / T-181 / T-162", "m2", area, C.DC, area, C.DC,
             "w x h does not read the sill: unchanged")
        cr = t175c[oid]
        line(chg, oid, "block deduction", "T-175", "m2", float(cr["block_deduction_m2"]) if cr["block_deduction_m2"] else None,
             cr["block_status"], float(cr["block_deduction_m2"]) if cr["block_deduction_m2"] else None, cr["block_status"],
             f"T-175 already used sill {cr['sill_m']} above FFL (its SILL_ABOVE_FFL_M): unchanged")
        tr = [r for r in t128 if r["OPENING"].startswith(oid)]
        line(chg, oid, "plaster / paint band position", "T-128 r3", "m", None,
             ", ".join(f"{r['ROOM_ROW']} {r['SILL_M']}/{r['HEAD_M']}" for r in tr), None,
             ", ".join(f"{r['ROOM_ROW']} {r['SILL_M']}/{r['HEAD_M']}" for r in tr),
             "T-128 already reads the corrected sill / head: unchanged")
    line("C4 re-datum", "W01", "latent error removed", "any consumer of T-150 SILL_M", "m", 3.85, "r2 head above FFL",
         3.00, C.DC, "r2 SILL_M + HEIGHT_M put the head 0.10 m above GF-W15's 3.75 clear height (T-175 HEAD_ABOVE_SOFFIT "
         "guard); r3 carries the absolute levels so the check reads +4.00 against the member soffit")

    # C6 windows pcs
    settled, held = C.pcs_summary(r3, "WINDOW.ALUMINIUM")
    line("C6 pcs", ",".join(held), "WINDOW.ALUMINIUM[nr]", "T-150 -> T-198 (T-181 verdict)", "pcs", "29", "r2 '29 vs 29 AGREE'",
         f"{settled} settled + {len(held)} HELD", C.HELD, f"{settled} settled + {len(held)} HELD ({', '.join(held)}: count 1 or 2) -> {settled + 1} .. "
         f"{settled + 2} vs the freelancer's 29: line HELD; the three additions are not windows (no glazing)")

    # C7 elevation-only features (T-194), no line
    elev = [
        dict(ID="E-SE-01..03", SHEET="SE elevation (P7757.dxf SE frame; Pages_05-06 p.6)", FLOOR="1F",
             WHAT="three closed 100 x 100 mm squares (layer 1) 0.80 m apart, 0.29 m above the W14 head",
             ON_PLAN="no", STATUS=C.UNKNOWN, IF_THROUGH_WALL="3 x 0.01 = 0.03 m2 of deduction; possibly a vent / "
             "sleeve item", ASK="designer: vent, AC sleeve or ornament?"),
        dict(ID="E-FE-01..06", SHEET="fence elevation (Pages_11-12 p.12)", FLOOR="GF",
             WHAT="six small squares above W11 / W12", ON_PLAN="no", STATUS=C.UNKNOWN,
             IF_THROUGH_WALL="6 x 0.01 = 0.06 m2 at most; possibly a vent / sleeve item", ASK="designer (same question)"),
    ]

    s_thr = sum(float(r["edge_m"]) for r in t175c.values() if r["edge"] == "THRESHOLD" and r["edge_m"])
    open_sides = {k: float(t175c[k]["edge_m"]) for k in ("P-GF-02", "P-GF-03", "P-GF-04")}
    summary = {
        "task": "T-198", "method": "census r3 (new file; OPENINGS_T150.csv untouched) + downstream deltas",
        "census_rows_r2": len(census), "census_rows_r3": len(r3),
        "added": [a["ID"] for a in ADD], "redatumed": sorted(READINGS),
        "windows_pcs": {"settled": settled, "held": held, "range": [settled + 1, settled + 2], "freelancer": 29,
                        "status": C.HELD},
        "released_quantity_moved": False,
        "block_m2_established_delta": 0.0,
        "new_scope_gaps": {
            "P-1F-01 masonry above lintel m2 bounds": list(C.masonry_above_head_bounds(p1f01)),
            "P-1F-01 plaster faces above head m2 upper bounds owner / drawing method": [round(2 * 1.30 * ph_owner, 3),
                                                                         round(2 * 1.30 * ph_dwg, 3)],
            "P-GF-05 face above head": C.UNKNOWN},
        "head_soffits_m2_drawing_confirmed": {"P-GF-01": 0.18, "P-1F-01": 0.195, "P-GF-05": 0.24},
        "thresholds_m_l": {"t175_established": round(s_thr, 3), "P-GF-05_to_UNKNOWN": -1.2,
                           "after": round(s_thr - 1.2, 3),
                           "open_sides_flagged_for_T-175_owner": open_sides},
        "elevation_only_unknown": [e["ID"] for e in elev],
        "t194_existence": {k: t194[k]["EXISTENCE_VERDICT"] for k in ("P-GF-01", "P-1F-01", "P-GF-05")},
    }
    return r3, D, elev, summary


def _csv(rows, cols=None):
    buf = io.StringIO()
    cols = cols or list(rows[0].keys())
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def outputs():
    r3, D, elev, summary = build()
    return {"OPENINGS_T198.csv": _csv(r3), "DOWNSTREAM_T198.csv": _csv(D), "ELEVATION_ONLY_T198.csv": _csv(elev),
            "summary.json": json.dumps(summary, indent=1, ensure_ascii=False, sort_keys=True) + "\n"}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    outs = outputs()
    if "--check" in argv:
        bad = [n for n, t in outs.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("T-198 check:", "OK" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    for n, t in outs.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print("written:", ", ".join(outs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
