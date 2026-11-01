"""T-421: ARCH_TAKEOFF_V3.0.38 (stair-room floor parts + lift-entrance marble, one step, no double count) on a
hand-calculated NON-Alsenan villa (K421).

Villa K421, by hand (own figures; nothing from the development villa):
  GF hall     porcelain 40.00 m2 SOURCE_DERIVED (zone GF-DRY b 0.05), with its V3.0.37 bed 40.00 m2 / 1.20 .. 1.60 m3.
              The GF lift door opens on it: clear width 0.90 m (drawn), depth 0.50 (owner UP-ELEV-005), wall band 0.25:
              threshold 0.90 x 0.50 = 0.450 m2 + 0.90 m.l; floor part certain 0.90 x (0.50 - 0.25) = 0.225 m2, the
              rest 0 .. 0.225 (0.90 x 0.25) HELD by position -> hall net 39.775 m2; bed restated 39.775 m2 /
              1.19325 .. 1.591 m3, bound 39.775 x 0.05 = 1.98875.
  Band line   ARCH.THRESHOLD 0.90 x 0.25 = 0.225 m2 BOUNDED_EXPOSURE -> listed, no quantity (owned by B6-07).
  Stair room  STAIR face with a FIN.MARBLE.LANDING bound 0 .. 7.30 m2; floor parts: foot hall 3.60 m2 (finish HELD,
              FIN.FLOOR.FINISH_HELD, zone GF-DRY b 0.05), back lobby 1.10 m2 (finish HELD, sub-level, no b),
              unread strip 0 .. 0.20 HELD -> bound 7.30 - 3.60 - 1.10 - 0.20 = 2.40.
              Beds: 3.60 -> 0.108 .. 0.144 m3 (bound 0.18); 1.10 -> 0.033 .. 0.044 (no bound).
  Surround    HELD 0.95 .. 4.40 m2 (door height not printed).
Lines: 2 changed floor / band, 1 changed landing bound, 2 restated beds; added: threshold m2 + m.l + surround, 2 floor
parts + 1 held part, 2 bed pairs (4 lines) = 10 added, 5 changed.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v3037 as A37  # noqa: E402
from engine.source import arch_v3038 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-k421", "e" * 64
DOCS = [{"file": "k421_plan.dxf", "sha256": "c" * 64}]
OWNER = {"DRY": {"lo": 0.03, "hi": 0.04, "rule": "Q-45 dry"}, "WET": {"lo": 0.04, "hi": 0.06, "rule": "Q-45 wet"}}
OWN = "ASSUMED — OWNER-APPROVED"
DC = "DRAWING-CONFIRMED"


def _src(t):
    return {"task": t, "file": f"research/k421/{t}.csv", "sha256": t[-1] * 64, "merge_commit": "b" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _line(code, eid, net=None, ev="SOURCE_DERIVED", floor="GF", unit="m2", br=None, trade="FLOOR_FINISH", notes="k"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=eid, floor=floor, room_id=eid.split(":")[0], physical_element=eid,
                        gross=net, bounded_range=br, formula=f"{eid}", documents=DOCS, rule_id="R", rule_version="1",
                        notes=notes, item_en=eid, item_ar=eid, trade=trade)


def lines_3037():
    hall = _line("FIN.FLOOR.PORCELAIN", "GF-HALL:floor", 40.0)
    base = [hall,
            _line("FIN.MARBLE.LANDING", "GF-STAIR:landings", None, ev="BOUNDED_EXPOSURE",
                  br={"low": 0.0, "high": 7.3, "basis": "face - treads"}, trade="STAIR_FINISH"),
            _line("ARCH.THRESHOLD", "HL:THRESHOLD:GF:OP-L1", None, ev="BOUNDED_EXPOSURE",
                  br={"low": 0.225, "high": 0.225, "basis": "band"}, trade="OPENINGS"),
            _line("ARCH.PASSAGE", "GF-OP-L1", 1.0, ev="PROVISIONAL", unit="pcs", trade="OPENINGS")]
    doc = {"schema": A37.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-414")], "owner": copy.deepcopy(OWNER),
           "b_upper": {}, "rows": [{"action": "BED", "finish_line": hall["line_id"], "kind": "DRY", "space_kind": "DRY",
                                    "layer": "MORTAR_BED", "zone": "GF-DRY", "membrane_in_room": "NONE",
                                    "source_tasks": ["T-414"], "area_status": DC,
                                    "expect": {"item_code": "FIN.FLOOR.PORCELAIN", "element_id": "GF-HALL:floor",
                                               "evidence_state": "SOURCE_DERIVED", "measured_net": 40.0},
                                    "ledger": {"m3_owner_low": 1.2, "m3_owner_high": 1.6, "b": 0.05,
                                               "m3_drawing_high": 2.0}}]}
    ch, _log = A37.changes_for(A37.load_inputs(doc, PID), base)
    return A37.integrate(base, ch)[0]


def _id(lines, eid):
    return next(x["line_id"] for x in lines if x["location"]["element_id"] == eid)


def inputs(lines, **over):
    land, hall = _id(lines, "GF-STAIR:landings"), _id(lines, "GF-HALL:floor")
    doc = {"schema": A.INPUTS_SCHEMA, "project_id": PID,
           "sources": [_src("T-418"), _src("T-413"), _src("T-414")], "owner_bed": copy.deepcopy(OWNER), "b_upper": {},
           "floor_parts": [
               {"part": "ST-FOOT", "room": "GF-STAIR", "floor": "GF", "level": "+0.80", "area": 3.6,
                "item_code": A.FIN_HELD, "finish": "porcelain or marble (landing)", "finish_status": "HELD",
                "area_status": DC, "zone": "GF-DRY", "b": 0.05, "template_line": land,
                "source_tasks": ["T-418", "T-414"]},
               {"part": "ST-LOBBY", "room": "GF-STAIR", "floor": "GF", "level": "+0.20", "area": 1.1,
                "item_code": A.FIN_HELD, "finish": "porcelain or marble", "finish_status": "HELD", "area_status": DC,
                "zone": "GF-SUBLEVEL", "b": None, "template_line": land, "source_tasks": ["T-418", "T-414"]}],
           "held_parts": [{"part": "ST-STRIP", "room": "GF-STAIR", "floor": "GF", "low": 0.0, "high": 0.2,
                           "why": "unread lines", "template_line": land, "source_tasks": ["T-418"]}],
           "landing_bounds": [{"line_id": land, "high_before": 7.3, "parts": ["ST-FOOT", "ST-LOBBY", "ST-STRIP"],
                               "source_tasks": ["T-418"]}],
           "stations": [{"station": "L1-GF", "floor": "GF", "opening": "OP-L1", "width": 0.9, "width_status": DC,
                         "depth": 0.5, "depth_status": OWN, "depth_source": "UP-ELEV-005", "band": 0.25,
                         "front_edge": 0.9, "surround_low": 0.95, "surround_high": 4.4,
                         "surround_formula": "A(h) = h x 1.0 + 0.5 x 1.9", "surround_held": "door height not printed",
                         "band_line": _id(lines, "HL:THRESHOLD:GF:OP-L1"), "floor_line": hall, "floor_part": None,
                         "template_line": _id(lines, "GF-OP-L1"), "source_tasks": ["T-413"]}],
           "restate_beds": [{"finish_line": hall, "zone": "GF-DRY"}]}
    doc.update(over)
    return doc


def run(lines=None, doc=None):
    lines = lines or lines_3037()
    d = A.load_inputs(doc or inputs(lines), PID)
    ch, log = A.changes_for(d, lines)
    out, ident = A.integrate(lines, ch)
    return lines, ch, log, out, ident


def _get(out, eid, unit="m2"):
    return next(x for x in out if x["location"]["element_id"] == eid and x["unit"] == unit)


# ------------------------------------------------------------------------------------------------ normal cases
def test_hand_figures():
    lines, ch, log, out, ident = run()
    assert ident["added"] == 10 and ident["replaced"] == 5
    assert ident["outside_rows_identical_to_v3_0_37"] == len(lines) - 5
    thr = _get(out, "LIFT:L1-GF")
    assert thr["item_code"] == A.LIFT_THR and thr["measured_net"] == pytest.approx(0.45)
    assert thr["evidence_state"] == "PROVISIONAL"
    assert _get(out, "LIFT:L1-GF:edge", "lm")["measured_net"] == pytest.approx(0.9)
    su = _get(out, "LIFT:L1-GF:surround")
    assert su["evidence_state"] == "BOUNDED_EXPOSURE" and su["measured_net"] is None
    assert (su["bounded_range"]["low"], su["bounded_range"]["high"]) == (0.95, 4.4)
    hall = _get(out, "GF-HALL:floor")
    assert hall["measured_net"] == pytest.approx(39.775) and hall["gross"] == 40.0
    assert [d["qty"] for d in hall["deductions"]] == [pytest.approx(0.225)]
    band = _get(out, "HL:THRESHOLD:GF:OP-L1")
    assert band["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and band["measured_net"] is None
    assert band["bounded_range"] is None and thr["line_id"] in band["notes"]
    b2, b3 = _get(out, "GF-HALL:floor:bed"), _get(out, "GF-HALL:floor:bed", "m3")
    assert b2["measured_net"] == pytest.approx(39.775)
    assert (b3["bounded_range"]["low"], b3["bounded_range"]["high"]) == pytest.approx((1.19325, 1.591))
    assert b3["calculation"]["inputs"][A37.REC_KEY]["drawing_bound"]["high"] == pytest.approx(1.98875)
    land = _get(out, "GF-STAIR:landings")
    assert land["bounded_range"]["high"] == pytest.approx(2.4)
    foot = _get(out, "GF-STAIR:ST-FOOT")
    assert foot["item_code"] == A.FIN_HELD and foot["measured_net"] == 3.6
    f3 = _get(out, "GF-STAIR:ST-FOOT:bed", "m3")
    assert (f3["bounded_range"]["low"], f3["bounded_range"]["high"]) == pytest.approx((0.108, 0.144))
    assert f3["calculation"]["inputs"][A37.REC_KEY]["drawing_bound"]["high"] == pytest.approx(0.18)
    l3 = _get(out, "GF-STAIR:ST-LOBBY:bed", "m3")
    assert (l3["bounded_range"]["low"], l3["bounded_range"]["high"]) == pytest.approx((0.033, 0.044))
    assert l3["calculation"]["inputs"][A37.REC_KEY]["drawing_bound"]["high"] is None
    strip = _get(out, "GF-STAIR:ST-STRIP")
    assert strip["evidence_state"] == "BOUNDED_EXPOSURE" and strip["bounded_range"]["high"] == 0.2
    assert not [x for x in out if x["location"]["element_id"] == "GF-STAIR:ST-STRIP:bed"]


def test_each_threshold_counted_once():
    """0 overlap: B6-07 owns the footprint; the band carries no quantity; the floor deducts exactly the certain part;
    band + certain floor part = the footprint."""
    out = run()[3]
    s = A.check_lift(out)
    assert s["stations"] == 1 and s["overlap_m2"] == 0.0
    assert s["threshold_m2"] == pytest.approx(0.45) and s["floor_deducted_certain_m2"] == pytest.approx(0.225)
    assert s["floor_held_more_m2"] == pytest.approx(0.225)
    thr = _get(out, "LIFT:L1-GF")
    band_qty = sum(BL.totals([x for x in out if x["item_code"] == "ARCH.THRESHOLD"], by=())[()].get("m2", {}).get(k, 0)
                   for k in ("net", "bounded_high"))
    hall_ded = sum(d["qty"] for d in _get(out, "GF-HALL:floor")["deductions"] if d["id"] == thr["line_id"])
    # the footprint in other lines: band quantity 0 + the floor still holds 0.90 x 0.50 - 0.225 - 0.225 (band) = 0
    assert band_qty == 0.0 and hall_ded == pytest.approx(0.45 - 0.9 * 0.25)


def test_landing_bound_reduced_in_the_same_step():
    out = run()[3]
    assert A.check_landing(out) == {"bounds": 1, "parts_moved": 3}


def test_only_named_lines_change_and_totals_move_in_own_codes():
    lines, ch, log, out, ident = run()
    named = {c["after"]["line_id"] for c in ch if c["action"] == "CHANGE"}
    for a in lines:
        b = next(x for x in out if x["line_id"] == a["line_id"])
        assert (A30.line_sha(a) == A30.line_sha(b)) == (a["line_id"] not in named)
    pas = _get(out, "GF-OP-L1", "pcs")
    assert pas == next(x for x in lines if x["line_id"] == pas["line_id"])


def test_mirror_order_identical():
    lines = lines_3037()
    a = run(lines)[3]
    doc = inputs(lines)
    doc["floor_parts"] = list(reversed(doc["floor_parts"]))
    b = run(lines, doc)[3]
    assert sorted(A30.line_sha(x) for x in a) == sorted(A30.line_sha(x) for x in b)


def test_two_f_station_on_a_new_floor_part():
    """a threshold whose landing floor is a NEW floor part: that part is added net of the certain floor part."""
    lines = lines_3037()
    doc = inputs(lines)
    st = dict(doc["stations"][0], floor_line=None, floor_part="ST-FOOT")
    doc["stations"] = [st]
    doc["restate_beds"] = []
    out = run(lines, doc)[3]
    foot = _get(out, "GF-STAIR:ST-FOOT")
    assert foot["measured_net"] == pytest.approx(3.375) and foot["gross"] == 3.6
    assert _get(out, "GF-STAIR:ST-FOOT:bed")["measured_net"] == pytest.approx(3.375)
    assert _get(out, "GF-HALL:floor")["measured_net"] == 40.0
    assert _get(out, "GF-STAIR:landings")["bounded_range"]["high"] == pytest.approx(2.4)   # gross part leaves the bound
    assert A.check_lift(out)["stations"] == 1


# ------------------------------------------------------------------------------------------------ adverse cases
def test_stair_face_dropped_whole_refused():
    """R-T418-1 adverse 'STAIR face dropped whole': a floor part added while the landing bound keeps it."""
    lines = lines_3037()
    doc = inputs(lines, landing_bounds=[])
    with pytest.raises(ValueError, match="still inside a landing bound"):
        run(lines, doc)


def test_bound_not_holding_the_parts_refused():
    lines = lines_3037()
    doc = inputs(lines)
    doc["landing_bounds"][0]["high_before"] = 7.3
    land = next(x for x in lines if x["location"]["element_id"] == "GF-STAIR:landings")
    land["bounded_range"] = dict(land["bounded_range"], high=4.0)
    doc["landing_bounds"][0]["high_before"] = 4.0
    with pytest.raises(A.InputsError, match="exceed the bound"):
        run(lines, doc)


def test_held_as_zero_refused():
    lines = lines_3037()
    doc = inputs(lines)
    doc["floor_parts"][0]["area"] = 0.0
    with pytest.raises(A.InputsError, match="HELD_AS_ZERO"):
        run(lines, doc)


def test_unsettled_finish_as_porcelain_refused():
    lines = lines_3037()
    doc = inputs(lines)
    doc["floor_parts"][0]["item_code"] = "FIN.FLOOR.PORCELAIN"
    with pytest.raises(A.InputsError, match="settled finish"):
        run(lines, doc)


def test_threshold_depth_without_source_refused():
    lines = lines_3037()
    doc = inputs(lines)
    doc["stations"][0]["depth_source"] = None
    with pytest.raises(A.InputsError, match="names its source"):
        run(lines, doc)
    doc["stations"][0]["depth_status"] = "UNKNOWN"
    with pytest.raises(A.InputsError, match="THRESHOLD_DEPTH_NOT_ESTABLISHED"):
        run(lines, doc)


def test_mm_refused():
    lines = lines_3037()
    doc = inputs(lines)
    doc["stations"][0]["width"] = 900
    with pytest.raises(A.InputsError, match="mm refused"):
        run(lines, doc)


def test_band_left_with_a_quantity_refused():
    """the check catches a band line that still carries a quantity beside the threshold."""
    out = run()[3]
    band = next(x for x in out if x["location"]["element_id"] == "HL:THRESHOLD:GF:OP-L1")
    bad = copy.deepcopy(band)
    bad["evidence_state"], bad["bounded_range"] = "BOUNDED_EXPOSURE", {"low": 0.225, "high": 0.225, "basis": "x"}
    out2 = [bad if x["line_id"] == band["line_id"] else x for x in out]
    with pytest.raises(ValueError, match="double count"):
        A.check_lift(out2)


def test_floor_not_deducted_refused():
    out = run()[3]
    hall = next(x for x in out if x["location"]["element_id"] == "GF-HALL:floor")
    bad = dict(copy.deepcopy(hall), deductions=[])
    out2 = [bad if x["line_id"] == hall["line_id"] else x for x in out]
    with pytest.raises(ValueError, match="deduct its floor part once"):
        A.check_lift(out2)


def test_bed_not_restated_refused():
    """a finish net moved without its bed: the bed check refuses (R-T421-1 c)."""
    lines = lines_3037()
    doc = inputs(lines, restate_beds=[])
    with pytest.raises(ValueError, match="not its finish line's net"):
        run(lines, doc)


def test_stale_band_binding_refused():
    lines = lines_3037()
    doc = inputs(lines)
    doc["stations"][0]["band"] = 0.20
    with pytest.raises(A.InputsError, match="band line"):
        run(lines, doc)


def test_applied_twice_refused():
    out = run()[3]
    lines = lines_3037()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(inputs(lines), PID), out)


def test_floor_line_twice_for_a_station_refused():
    lines = lines_3037()
    doc = inputs(lines)
    doc["stations"][0]["floor_part"] = "ST-FOOT"
    with pytest.raises(A.InputsError, match="ONE floor line"):
        run(lines, doc)
