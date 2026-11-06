"""T-562: statement adapters V3 for T-551 (B10 m3), T-553 (B3 floor tile m2), the T-559 restatement of the B9
openings and the T-556 supersession of the B5 plaster restatement, on the T-548 builder and the T-554 / T-557 adapters
(all read only). Synthetic villa "S562" (not the training villa) by hand per adapter, adverse cases, then the merged
training-villa sources (committed research outputs only; no private input)."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t562"))
import t562_adapters as Y  # noqa: E402
import t562_build as B  # noqa: E402

S = Y.S
Dd = Decimal


def close(sec):
    return S.build_statement([Y.SA.for_builder(sec)])["sections"][0]


def ln(lid, code, cls, unit, net=None, lo=None, hi=None, el="E"):
    return {"line_id": lid, "item_code": code, "class": cls, "unit": unit, "measured_net": net,
            "held_low": lo, "held_high": hi, "element_id": el}


# ------------------------------------------------------------------------------------------------ T-551 format ----
# S562 structure by hand (engine - his in the report; the statement shows his - engine):
#  columns GF: engine R1 1.2 + R2 0.8 = 2.0, his 2.5: COUNT CA -0.40 (valued) + CB +0.10 (a HELD drawn member beyond
#    his count), HELD -0.40, JOINT_HEAD +0.10 (RULE_DIFFERENCE), HEIGHT_OPEN +0.10 (TRACED_SPLIT_OPEN) = -0.50.
#    Statement +0.50 = ER +0.40, HELD +0.40 - 0.10 = +0.30 (CB moved, F-T562-2), RD -0.10, UNRESOLVED -0.10 (F-T562-4).
#  necks: 0 valued, N1 HELD 0.2 .. 0.4, his 0.30 -> HELD +0.30, bounded AT_LEAST 0.2 .. 0.4.
#  lift: pit wall HELD, his 0.15 = SCOPE_DOUBLE 0.05 (ER, NONE) + HELD 0.10.
#  footing line: F1 2.5 + S1 0.5 = 3.0 valued, FH HELD 2.0 .. 2.2, band BW HELD 1.2 .. 1.2; his 5.0:
#    COUNT +0.2, HELD -2.2 (FH 1.0 + band 1.2) -> statement -0.2 ER, +1.0 HELD, +1.2 HELD = +2.0; bounded 6.2 .. 6.4.
#  blinding: B1 1.0 valued, BH HELD 0.5 .. 1.0, his 4.0: residual -3.0 = HELD -0.5 / RD -2.5 (low end), HELD -1.0 /
#    RD -2.0 (high end) -> one HELD row +3.0, split beside [0.5, 1.0] + [2.0, 2.5].
def s562_structure():
    index = {x["line_id"]: x for x in [
        ln("R1", "STR.CONC.COLUMN", "RELEASED", "m3", 1.2, el="P-C:COL:SH1:CA@1,1|GF"),
        ln("R2", "STR.CONC.COLUMN", "RELEASED", "m3", 0.8, el="P-C:COL:SH1:CA@2,1|GF"),
        ln("H1", "STR.CONC.COLUMN", "HELD", "m3", None, 0.1, 0.2, el="P-C:COL:SH1:CB@3,1|GF"),
        ln("H2", "STR.CONC.COLUMN", "HELD", "m3", None, None, None, el="P-C:COL:SH1:CC@4,1|GF"),
        ln("N1", "STR.CONC.NECK", "HELD", "m3", None, 0.2, 0.4, el="P-C:NECK:COL:SH1:CA@1,1"),
        ln("LP", "STR.CONC.LIFT", "HELD", "m3", None, el="LIFT_PIT:WALLS"),
        ln("F1", "STR.CONC.FOOTING", "RELEASED", "m3", 2.5, el="P-C:FTG:1"),
        ln("FH", "STR.CONC.FOOTING", "HELD", "m3", None, 2.0, 2.2, el="P-C:FTG:2"),
        ln("S1", "STR.CONC.STRAP", "RELEASED", "m3", 0.5, el="HL:STRAP:SB1"),
        ln("BW", "STR.CONC.BOUNDARY_WALL", "HELD", "m3", None, 1.2, 1.2, el="P-C:SCOPE:BOUNDARY_WALL:FOUNDATION:BEAM"),
        ln("B1", "STR.CONC.BLINDING", "RELEASED", "m3", 1.0, el="BLIND:1"),
        ln("BH", "STR.CONC.BLINDING", "HELD", "m3", None, 0.5, 1.0, el="BLIND:2")]}
    d = {"columns": {"GF": {"engine_m3": "2.0", "his_m3": "2.5", "components": {
            "COUNT": {"m3": "-0.30", "verdict": "ENGINE_RIGHT"}, "HELD": {"m3": "-0.40", "verdict": "HELD"},
            "JOINT_HEAD": {"m3": "0.10", "verdict": "RULE_DIFFERENCE"},
            "HEIGHT_OPEN": {"m3": "0.10", "verdict": "TRACED_SPLIT_OPEN"}}}},
         "necks": {"engine_m3": "0", "his_m3": "0.30", "engine_held_lines": 1, "engine_held_bound_m3": ["0.2", "0.4"],
                   "components": {"HELD": {"m3": "-0.30", "verdict": "HELD"}}},
         "lift_walls": {"engine_m3": "0", "his_m3": "0.15", "components": {
             "SCOPE_DOUBLE": {"m3": "-0.05", "verdict": "ENGINE_RIGHT"}, "HELD": {"m3": "-0.10", "verdict": "HELD"}}},
         "footing_line": {"engine_m3": "3.0", "his_m3": "5.0", "components": {
             "COUNT": {"m3": "0.2", "verdict": "ENGINE_RIGHT"}, "HELD": {"m3": "-2.2", "verdict": "HELD"}}},
         "blinding": {"engine_released_m3": "1.0", "engine_held_bound_m3": ["0.5", "1.0"], "his_m3": "4.0",
                      "residual_m3": "-3.0", "held_low_end": {"HELD": "-0.5", "RULE_DIFFERENCE": "-2.5"},
                      "held_high_end": {"HELD": "-1.0", "RULE_DIFFERENCE": "-2.0"}}}
    kw = {"count_marks": {"GF": [("CA", "-0.40"), ("CB", "0.10")]}, "count_on_held": {("GF", "CB")},
          "count_held_sum": "0.10", "count_checker": {("GF", "CA")},
          "footing_held": [("HELD outline FH", "1.0", "FOOTING"), ("HELD band", "1.2", "BAND")]}
    return d, index, kw


def test_t551_by_hand():
    d, index, kw = s562_structure()
    secs = {x["section_id"]: x for x in Y.t551_from(d, index, **kw)}
    c = close(secs["T-551/columns"])
    assert (c["reference_total"], c["engine_valued"], c["difference"]) == ("2.5", "2", "0.5")
    assert c["by_class"] == {"ENGINE_RIGHT": "0.4", "ENGINE_WRONG": "0", "RULE_DIFFERENCE": "-0.1", "HELD": "0.3",
                             "TOLERANCE": "0", "UNRESOLVED": "-0.1"}
    cb = [r for r in secs["T-551/columns"]["rows"] if r["name"].endswith("COUNT CB")][0]
    assert cb["class"] == "HELD" and cb["held_line_ids"] == ["H1"] and cb["reclass"]["tag"] == "F-T562-2"
    assert Y.expected_by_class(secs["T-551/columns"]["source_by_class"], secs["T-551/columns"]["rows"]) == c["by_class"]
    n = close(secs["T-551/necks"])
    assert n["by_class"]["HELD"] == "0.3" and n["engine_bounded"] == {"low_at_least": "0.2", "high": "0.4",
                                                                       "high_open": False}
    lf = close(secs["T-551/lift-walls"])
    assert (lf["by_class"]["ENGINE_RIGHT"], lf["by_class"]["HELD"]) == ("0.05", "0.1")
    f = close(secs["T-551/footing-line"])
    assert (f["difference"], f["by_class"]["HELD"], f["by_class"]["ENGINE_RIGHT"]) == ("2", "2.2", "-0.2")
    assert f["engine_bounded"] == {"low_at_least": "6.2", "high": "6.4", "high_open": False}
    b = close(secs["T-551/blinding"])
    assert (b["difference"], b["by_class"]["HELD"], b["by_class"]["RULE_DIFFERENCE"]) == ("3", "3", "0")
    assert secs["T-551/blinding"]["beside"]["held_share_range_m3"] == ["0.5", "1"]
    assert secs["T-551/blinding"]["beside"]["rule_difference_share_range_m3"] == ["2", "2.5"]
    assert Y.expected_by_class(secs["T-551/blinding"]["source_by_class"], secs["T-551/blinding"]["rows"]) == b["by_class"]


def test_t551_adverse():
    d, index, kw = s562_structure()
    bad = copy.deepcopy(kw)
    bad["count_marks"]["GF"][0] = ("CA", "-0.41")                       # per-mark table does not sum
    with pytest.raises(Y.AdapterError):
        Y.t551_from(d, index, **bad)
    bad = copy.deepcopy(kw)
    bad["count_held_sum"] = "0.20"                                      # R-T394-2 sum not met
    with pytest.raises(Y.AdapterError):
        Y.t551_from(d, index, **bad)
    d2 = copy.deepcopy(d)
    d2["blinding"]["held_high_end"]["RULE_DIFFERENCE"] = "-2.1"          # a held end that does not close
    with pytest.raises(Y.AdapterError):
        Y.t551_from(d2, index, **kw)
    i2 = copy.deepcopy(index)
    i2["R1"]["measured_net"] = 1.3                                       # stale engine total
    with pytest.raises(Y.AdapterError):
        Y.t551_from(d, i2, **kw)
    d3 = copy.deepcopy(d)
    d3["columns"]["GF"]["components"]["SECTION"] = {"m3": "0.05", "verdict": "ENGINE_RIGHT"}   # unlisted component
    with pytest.raises(Y.AdapterError):
        Y.t551_from(d3, index, **kw)


def test_unmapped_verdict_refused():
    with pytest.raises(Y.AdapterError):
        Y.expected_by_class({"TRACED_SPLIT_OPEN": "0.1", "HELD": "1"}, [])


# ------------------------------------------------------------------------------------------------ T-553 format ----
# S562 floor tile by hand (engine - his): room A engine 20.0 his 23.0 = -3.0: stair footprint -1.0 RULE_DIFFERENCE
# owned by marble M1 (engine NONE), band -1.5 HELD with no floor line (-> UNRESOLVED, F-T562-3), dressing -0.5
# ENGINE_WRONG (fix row T-X). Room B engine 5.0 his 4.9: +0.1 ENGINE_RIGHT. Engine 25.0 vs his 27.9: statement +2.9 =
# RD 1.0 + UNRESOLVED 1.5 + EW 0.5 + ER -0.1.
def s562_floor():
    index = {x["line_id"]: x for x in [
        ln("P1", "FIN.FLOOR.PORCELAIN", "RELEASED", "m2", 20.0), ln("W1", "FIN.FLOOR.WET_TILE", "RELEASED", "m2", 5.0),
        ln("M1", "FIN.MARBLE.LANDING", "RELEASED", "m2", 1.0), ln("G1", "ARCH.EXTERIOR", "RELEASED", "m2", 1.5)]}
    t = {"engine_total": "25.0", "freelancer_total": "27.9", "gap_engine_minus_freelancer": "-2.9", "held_lines": [],
         "by_cause": {"RULE_DIFFERENCE": "-1.0", "HELD": "-1.5", "ENGINE_WRONG": "-0.5", "ENGINE_RIGHT": "0.1"},
         "class_moves": [], "by_size": {},
         "rows": [{"room": "A", "delta": "-3.0", "components": [
             {"cause": "RULE_DIFFERENCE", "delta": "-1.0", "name": "stair", "owned_by": "M1"},
             {"cause": "HELD", "delta": "-1.5", "name": "band", "owned_by": "G1"},
             {"cause": "ENGINE_WRONG", "delta": "-0.5", "name": "dressing"}]},
             {"room": "B", "delta": "0.1", "components": [{"cause": "ENGINE_RIGHT", "delta": "0.1", "name": "size"}]}]}
    d = {"table": t, "freelancer_dry": "20.0", "freelancer_wet": "7.9", "outdoor": {},
         "missing_floor_lines": [{"area": 0.5, "element": "A-DR", "space_line": "SP"}]}
    return d, index


def test_t553_by_hand():
    d, index = s562_floor()
    sec = Y.t553_from(d, index, fix_row="T-X")
    c = close(sec)
    assert (c["difference"], c["by_class"]["RULE_DIFFERENCE"], c["by_class"]["UNRESOLVED"],
            c["by_class"]["ENGINE_WRONG"], c["by_class"]["ENGINE_RIGHT"], c["by_class"]["HELD"]) == \
        ("2.9", "1", "1.5", "0.5", "-0.1", "0")
    rows = {r["name"]: r for r in sec["rows"]}
    assert rows["A: stair"]["engine_status"] == "NONE"
    assert rows["A: band"]["reclass"]["tag"] == "F-T562-3" and rows["A: band"]["source_cause"] == "HELD"
    assert rows["A: dressing"]["fix_row"] == "T-X"
    assert sec["beside"]["engine_wrong_restated"]["engine_with_correction_m2"] == "25.5"
    assert Y.expected_by_class(sec["source_by_class"], sec["rows"]) == c["by_class"]


def test_t553_adverse():
    d, index = s562_floor()
    d2 = copy.deepcopy(d)
    d2["table"]["rows"][0]["components"][0]["delta"] = "-1.1"           # room does not close
    with pytest.raises(Y.AdapterError):
        Y.t553_from(d2, index)
    d3 = copy.deepcopy(d)
    d3["table"]["engine_total"] = "25.1"                                 # stale engine total
    with pytest.raises(Y.AdapterError):
        Y.t553_from(d3, index)
    d4 = copy.deepcopy(d)
    d4["freelancer_wet"] = "8.0"                                         # his total != dry + wet
    with pytest.raises(Y.AdapterError):
        Y.t553_from(d4, index)


# ------------------------------------------------------------------------------------------------ T-559 format ----
# S562 blockwork by hand: the section's four openings rows (UNRESOLVED -1.0 / -0.5 / -0.2 / -0.3 = -2.0) are replaced
# by: GF D-GF-01 height -0.4 RULE_DIFFERENCE in valued wall GF-W01 (stays); GF W01 height -0.6 ENGINE_RIGHT in HELD
# wall GF-W02 (-> HELD, F-T562-1); GF D-GF-02 held opening -0.8 HELD; 1F his-only unit -0.2 UNRESOLVED (NONE).
# Class totals: UNRESOLVED -2.0 -> -0.2, RD -0.4, HELD -1.4, ER 0.
def s562_block():
    rows = [{"name": n, "delta": v, "class": "UNRESOLVED", "source_cause": "UNRESOLVED", "engine_status": "VALUED",
             "held_line_ids": [], "source": "s", "note": ""} for n, v in
            [("GF: openings census: x", "-1.0"), ("1F: openings census: x", "-0.5"), ("2F: openings census: x", "-0.2"),
             ("his 20 cm openings with no floor", "-0.3")]]
    rows.insert(0, {"name": "GF: other", "delta": "5", "class": "ENGINE_RIGHT", "source_cause": "ENGINE_RIGHT",
                    "engine_status": "VALUED", "held_line_ids": [], "source": "s", "note": "n"})
    rows.append({"name": Y.PER_RUN_ROW + "'s printed height", "delta": "0.7", "class": "HELD", "source_cause":
                 "ENGINE_RIGHT", "engine_status": "HELD", "held_line_ids": ["HG"], "source": "s", "note": "p"})
    sec = {"section_id": "T-543/blockwork", "unit": "m2", "rows": rows}
    walls = [{"wall_id": "GF-W01", "floor": "GF", "t_m": "0.15", "valued_m2": "10", "state_v3_0_58": "ESTABLISHED"},
             {"wall_id": "GF-W02", "floor": "GF", "t_m": "0.20", "valued_m2": None, "state_v3_0_58": "HELD"}]
    held = [{"line_id": "HG", "element_id": "GF-WALLS:walls t=0.20", "class": "HELD", "qty": None},
            {"line_id": "HG15", "element_id": "GF-WALLS:walls t=0.15", "class": "HELD", "qty": None}]
    hosts = {"D-GF-01": {("GF-W01", False)}, "W01": {("GF-W02", False)}, "D-GF-02": {("GF-W01", True)}}
    g = [{"floor": "GF", "delta": "-1.8", "rows": [
        {"cause": "RULE_DIFFERENCE", "delta": "-0.4", "name": "GF D-GF-01 vs his", "term": "height"},
        {"cause": "ENGINE_RIGHT", "delta": "-0.6", "name": "GF W01 vs his", "term": "height"},
        {"cause": "HELD", "delta": "-0.8", "name": "GF D-GF-02 vs his", "term": "held opening"}]},
         {"floor": "1F", "delta": "-0.2", "rows": [
             {"cause": "UNRESOLVED", "delta": "-0.2", "name": "1F his 0.60 x 0.80 (no engine opening)", "term": "count"}]}]
    d = {"openings": {"groups": g, "rows": [r for x in g for r in x["rows"]], "total": "-2.0"},
         "openings_t550_m2": "-2.0", "t550_unresolved_m2": "3.0",
         "by_cause": {"RULE_DIFFERENCE": "-0.4", "ENGINE_RIGHT": "-0.6", "HELD": "-0.8", "UNRESOLVED": "4.8"},
         "per_run_sum_m2": "0.7", "per_run_heights_1F": [{"run": "R1", "centreline_m": "1", "h_status": "PRINTED"}],
         "edge_summary": {"CARRIED_ONCE": 2, "OMITTED": 0}, "unresolved_gross_abs_m2": "1"}
    return sec, d, walls, held, hosts


def test_t559_by_hand():
    sec, d, walls, held, hosts = s562_block()
    out = Y.t559_restate(sec, d, walls, held, hosts)
    rows = {r["name"]: r for r in out["rows"]}
    assert [r["name"] for r in out["rows"]][0] == "GF: other"            # order kept, new rows at the first target
    w = rows["openings GF: GF W01 vs his / height"]
    assert (w["class"], w["engine_status"], w["held_line_ids"], w["reclass"]["tag"]) == ("HELD", "HELD", ["HG"],
                                                                                         "F-T562-1")
    assert rows["openings GF: GF D-GF-01 vs his / height"]["class"] == "RULE_DIFFERENCE"
    assert rows["openings 1F: 1F his 0.60 x 0.80 (no engine opening) / count"]["engine_status"] == "NONE"
    h = rows["openings GF: GF D-GF-02 vs his / held opening"]
    assert (h["class"], h["held_line_ids"]) == ("HELD", ["HG15"])         # held opening in a valued wall
    prev = {"ENGINE_RIGHT": "5", "ENGINE_WRONG": "0", "RULE_DIFFERENCE": "0", "HELD": "0.7", "TOLERANCE": "0",
            "UNRESOLVED": "-2"}
    assert Y.t559_expected_by_class(prev, out) == {"ENGINE_RIGHT": "5", "ENGINE_WRONG": "0", "RULE_DIFFERENCE": "-0.4",
                                                    "HELD": "-0.7", "TOLERANCE": "0", "UNRESOLVED": "-0.2"}
    assert "T-559 per-run table" in rows[Y.PER_RUN_ROW + "'s printed height"]["note"]


def test_t559_adverse():
    sec, d, walls, held, hosts = s562_block()
    d2 = copy.deepcopy(d)
    d2["openings"]["total"] = "-2.1"                                     # parts do not sum to the target
    with pytest.raises(Y.AdapterError):
        Y.t559_restate(sec, d2, walls, held, hosts)
    s2 = copy.deepcopy(sec)
    s2["rows"][1]["class"] = "HELD"                                      # target changed under us
    with pytest.raises(Y.AdapterError):
        Y.t559_restate(s2, d, walls, held, hosts)
    h2 = dict(hosts)
    h2["W01"] = {("GF-W02", False), ("GF-W01", False)}                    # opening with two host walls
    with pytest.raises(Y.AdapterError):
        Y.t559_restate(sec, d, walls, held, h2)
    d3 = copy.deepcopy(d)
    d3["per_run_sum_m2"] = "0.8"                                         # per-run row differs from T-559
    with pytest.raises(Y.AdapterError):
        Y.t559_restate(sec, d3, walls, held, hosts)


def test_per_run_heights_never_engine_right():
    st = {"sections": [{"section_id": "T-543/blockwork", "rows": [
        {"name": Y.PER_RUN_ROW + "x", "class": "ENGINE_RIGHT", "engine_status": "HELD"}]}]}
    with pytest.raises(Y.AdapterError):
        Y.verify_per_run_held(st)
    st["sections"][0]["rows"][0]["class"] = "HELD"
    Y.verify_per_run_held(st)


# ------------------------------------------------------------------------------------------------ T-556 supersession
def s562_plaster():
    index = {x["line_id"]: x for x in [ln("PR", "FIN.PLASTER", "RELEASED", "m2", 10.0),
                                       ln("PH", "FIN.PLASTER", "HELD", "m2", None, 8.0, 9.0)]}
    sec = {"section_id": "T-552/plaster-internal", "beside": {"engine_wrong_restated": {
        "verdict": "ENGINE_WRONG", "released_lines_now_m2": "10", "released_lines_restated_HELD_BOUNDED_m2": ["12", "13"]}}}
    d = {"rows": [{"room": "A", "line_id": "PR", "candidate_class": "RELEASED", "new_lo": "12.4", "new_hi": "12.5",
                   "old_paint_height_basis": {"value": ["10", "10"]}, "t552_restated": ["12", "13"], "zone": "GF",
                   "status": "HELD"},
                  {"room": "B", "line_id": "PH", "candidate_class": "HELD", "new_lo": "11", "new_hi": "11.5",
                   "old_paint_height_basis": {"value": ["8", "9"]}, "t552_restated": ["10", "12"], "zone": "GF",
                   "status": "HELD"}],
         "released_4_lines": {"old": "10", "new": ["12.4", "12.5"]}, "totals": {"new": ["23.4", "24.0"]},
         "freelancer_same_rooms": {"engine_gross_at_plaster_height": "30", "his_gross": "28", "delta": "2",
                                   "delta_pct": "7.1", "cause": "c"}}
    return sec, d, index


def test_supersession_by_hand():
    sec, d, index = s562_plaster()
    out = Y.t556_supersede(sec, d, index)
    cur = Y.current_restatement(out["beside"])
    assert cur["released_lines_restated_HELD_BOUNDED_m2"] == ["12.4", "12.5"]
    assert cur["all_11_dry_lines_restated_HELD_BOUNDED_m2"] == ["23.4", "24"]
    old = out["beside"]["engine_wrong_restated_superseded_T557"]
    assert old["status"] == "SUPERSEDED" and old["released_lines_restated_HELD_BOUNDED_m2"] == ["12", "13"]
    st = {"sections": [out]}
    Y.verify_supersession(st, d)


def test_superseded_quoted_as_current_refused():
    sec, d, index = s562_plaster()
    out = Y.t556_supersede(sec, d, index)
    swapped = copy.deepcopy(out)
    swapped["beside"]["engine_wrong_restated"] = swapped["beside"]["engine_wrong_restated_superseded_T557"]
    with pytest.raises(Y.AdapterError):
        Y.current_restatement(swapped["beside"])
    with pytest.raises(Y.AdapterError):
        Y.verify_supersession({"sections": [swapped]}, d)
    unlabeled = copy.deepcopy(out)
    unlabeled["beside"]["engine_wrong_restated_superseded_T557"]["status"] = "CURRENT"
    with pytest.raises(Y.AdapterError):
        Y.verify_supersession({"sections": [unlabeled]}, d)
    stale = copy.deepcopy(out)
    stale["beside"]["engine_wrong_restated"]["released_lines_restated_HELD_BOUNDED_m2"] = ["12", "13"]
    with pytest.raises(Y.AdapterError):
        Y.verify_supersession({"sections": [stale]}, d)
    with pytest.raises(Y.AdapterError):                                   # superseding twice
        Y.t556_supersede(swapped, d, index)


def test_held_bound_as_point_refused():
    sec, d, index = s562_plaster()
    for lo, hi in (("12.4", None), (None, "12.5"), ("12.6", "12.5")):
        d2 = copy.deepcopy(d)
        d2["rows"][0]["new_lo"], d2["rows"][0]["new_hi"] = lo, hi
        with pytest.raises(Y.AdapterError):
            Y.t556_supersede(sec, d2, index)
    with pytest.raises(Y.X.AdapterError):
        Y.require_range("12.4", "point")


# ------------------------------------------------------------------------------------------------ gross / blinding --
def test_gross_beside_net():
    st = {"sections": [{"section_id": "A", "difference": "0", "rows": [{"class": "HELD", "delta": "5"},
                                                                       {"class": "ENGINE_RIGHT", "delta": "-5"}]}],
          "totals": [{"trade": "t", "sections": ["A"]}]}
    Y.add_gross(st)
    assert st["sections"][0]["gross_abs"] == "10" and st["totals"][0]["gross_abs"] == "10"
    Y.verify_gross(st)
    del st["totals"][0]["gross_abs"]
    with pytest.raises(Y.AdapterError):
        Y.verify_gross(st)


def test_blinding_never_in_structural_total():
    st = {"sections": [{"section_id": "T-551/blinding"}],
          "totals": [{"trade": "B10", "sections": ["T-551/blinding", "T-551/footing-line"]}]}
    with pytest.raises(Y.AdapterError):
        Y.verify_blinding_apart(st)


# ------------------------------------------------------------------------------------------------ training villa --
@pytest.fixture(scope="module")
def st():
    return B.build()


def test_reproduces_committed():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t562/t562_build.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_acceptance_numbers(st):
    secs = {c["section_id"]: c for c in st["sections"]}
    cur = Y.current_restatement(secs["T-552/plaster-internal"]["beside"])
    assert cur["released_lines_restated_HELD_BOUNDED_m2"] == ["262.01799", "262.05199"]
    old = secs["T-552/plaster-internal"]["beside"]["engine_wrong_restated_superseded_T557"]
    assert old["status"] == "SUPERSEDED" and old["released_lines_restated_HELD_BOUNDED_m2"] == ["261.77493", "269.32863"]
    assert (secs["T-551/columns"]["difference"], secs["T-551/footing-line"]["difference"],
            secs["T-551/blinding"]["difference"]) == ("8.77", "9.936", "34.320562")
    ft = secs["T-553/floor-tile"]
    assert (ft["reference_total"], ft["engine_valued"], ft["by_class"]["ENGINE_WRONG"]) == ("409.58", "387.09405", "2.97")
    assert [r["fix_row"] for r in ft["rows"] if r["class"] == "ENGINE_WRONG"] == ["T-564"]
    b9 = secs["T-543/blockwork"]
    assert b9["difference"] == "792.897" and b9["by_class"]["UNRESOLVED"] == "58.506437"
    per = [r for r in b9["rows"] if r["name"].startswith(Y.PER_RUN_ROW)][0]
    assert per["class"] == "HELD" and per["delta"] == "7.6306805"
    for c in st["sections"]:                                            # every section closes, gross beside net
        assert sum((Dd(r["delta"]) for r in c["rows"]), Dd(0)) == Dd(c["difference"])
        assert Dd(c["gross_abs"]) >= abs(Dd(c["difference"]))
    for t in st["totals"]:
        assert "gross_abs" in t
    assert st["released_quantities_changed"] == 0


def test_every_new_row_labelled(st):
    for c in st["sections"]:
        for r in c["rows"]:
            if c["section_id"] in B.NEW_SECTIONS or r.get("correction") == "T-559":
                assert r.get("verification") in Y.X.VERIF, r["name"]


def test_other_sections_untouched(st):
    prev = json.loads(B.B557.JSON_OUT.read_text(encoding="utf-8"))
    old = {c["section_id"]: c for c in prev["sections"]}
    for c in st["sections"]:
        if c["section_id"] in old and c["section_id"] not in B.TOUCHED:
            c2 = {k: v for k, v in c.items() if k not in ("gross_abs", "by_class_gross_abs")}
            assert c2 == old[c["section_id"]], c["section_id"]


def test_engine_wrong_never_agreement(st):
    bad = copy.deepcopy(st)
    ft = [c for c in bad["sections"] if c["section_id"] == "T-553/floor-tile"][0]
    for r in ft["rows"]:
        if r["class"] == "ENGINE_WRONG":
            r["class"] = "ENGINE_RIGHT"
    with pytest.raises(Y.X.AdapterError):
        Y.X.verify_engine_wrong(bad, B.ENGINE_WRONG_CONFIRMED)


def test_untouched_section_change_refused():
    index = Y.SA.load_index()
    secs, prov, ctx = B.assemble(index)
    prev = json.loads(B.B557.JSON_OUT.read_text(encoding="utf-8"))
    prev2 = copy.deepcopy(prev)
    [c for c in prev2["sections"] if c["section_id"] == "T-547/wall-tile"][0]["rows"][0]["delta"] = "1"
    with pytest.raises(Y.AdapterError):
        B.build_from(secs, prov, index, ctx, prev=prev2)


def test_held_host_walls_cross_checked_with_t543(st):
    """Independent route: every F-T562-1 move names a host wall that T-543's own HELD rows list (the register state
    and the report agree); a held opening may sit in a valued wall only with its source class HELD."""
    import re
    d = json.loads((ROOT / "research/agents_t543/out/T543_BLOCKWORK_RECONCILE.json").read_text(encoding="utf-8"))
    held = set()
    for comp in d["rows"]:
        if comp["cause"] == "SPLIT" and comp["name"].endswith("storey walls (net of openings)"):
            for r in comp["decomposition"]["rows"]:
                if r["cause"] == "HELD":
                    for w in r["walls"]:
                        held.update(x.strip() for x in w.split("+"))
    b9 = [c for c in st["sections"] if c["section_id"] == "T-543/blockwork"][0]
    moved = 0
    for r in b9["rows"]:
        if r.get("correction") == "T-559" and r["engine_status"] == "HELD":
            m = re.search(r"host wall (\S+) ", r["note"])
            wall = m.group(1) if m else "GF-W04"
            if r.get("reclass"):
                moved += 1
                assert wall in held, r["name"]
            elif wall not in held:
                assert r["source_cause"] == "HELD" and "opening HELD" in r["note"], r["name"]
    assert moved == 25
