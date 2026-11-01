"""T-420: ARCH_TAKEOFF_V3.0.37 (FLOOR_BED: B3-05 bed per valued floor-finish line, m2 + installed m3 measure pair) on
a hand-calculated NON-Alsenan villa (V420).

Villa V420, by hand (own figures; nothing from the development villa):
  GF living   porcelain 24.00 m2 SOURCE_DERIVED, zone GF-DRY b 0.05 -> bed m2 24.00; owner Q-45 0.03 .. 0.04 m:
              0.72 .. 0.96 m3; drawing bound 24.00 x 0 .. 0.05 = 0 .. 1.20 m3 (HELD beside, CONSISTENT: 0.04 <= 0.05).
  1F bedroom  porcelain 15.50 m2 PROVISIONAL (area ASSUMED - OWNER-APPROVED), zone 1F-DRY b 0.049 with the drawn range
              to 0.051: owner 0.465 .. 0.62 m3; bound 15.50 x 0.051 = 0.7905 (upper end), not 0.7595.
  GF bath     wet tile 6.00 m2: owner 0.04 .. 0.06 m: 0.24 .. 0.36 m3; no drawing bound (wet level not printed).
  GF strip    porcelain doorway strip NOT_APPLICABLE_WITH_EVIDENCE: no bed line.
  Roof        FIN.ROOF.FINISH 40.00 m2 offered as a bed row: refused (B13-01).
Totals: dry m2 39.50, m3 1.185 .. 1.58; wet m2 6.00, m3 0.24 .. 0.36; 6 lines added (3 beds x m2 + m3).
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3037 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-v420", "f" * 64
DOCS = [{"file": "v420_plan.dxf", "sha256": "d" * 64}]
SRC = [{"task": "T-414", "file": "research/v420/room_table.csv", "sha256": "1" * 64, "merge_commit": "a" * 40,
        "checker_run": "checker run 90 (Gate A PASS)"}]
OWNER = {"DRY": {"lo": 0.03, "hi": 0.04, "rule": "Q-45 dry"}, "WET": {"lo": 0.04, "hi": 0.06, "rule": "Q-45 wet"}}
B_UP = {"1F-DRY": {"b": 0.051, "source": "checker: upper end of the drawn range"}}


def _line(code, eid, net, ev="SOURCE_DERIVED", floor="GF", notes="v420"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit="m2", evidence_state=ev,
                        measured_net=net, element_id=eid, floor=floor, room_id=eid.split(":")[0], physical_element=eid,
                        gross=net, formula=f"{eid} floor", documents=DOCS, rule_id="R", rule_version="1",
                        notes=notes, item_en=eid, item_ar=eid, trade="FLOOR_FINISH")


def lines_3036():
    return [_line("FIN.FLOOR.PORCELAIN", "GF-LIV:floor", 24.0),
            _line("FIN.FLOOR.PORCELAIN", "1F-BED:floor", 15.5, ev="PROVISIONAL", floor="1F"),
            _line("FIN.FLOOR.WET_TILE", "GF-BATH:floor", 6.0),
            _line("FIN.FLOOR.PORCELAIN", "GF-STRIP:doorway strip", None, ev="NOT_APPLICABLE_WITH_EVIDENCE",
                  notes="no floor finish in the strip (evidence)")]


ROOF = _line("FIN.ROOF.FINISH", "ROOF-1:finish", 40.0, floor="RF")   # a roof layer line (B13-01), offered as a bed


def _fid(lines, eid):
    return next(x["line_id"] for x in lines if x["location"]["element_id"] == eid)


def _row(lines, eid, kind, area, ev, status, b=None, dh=None, zone=None, action="BED", code="FIN.FLOOR.PORCELAIN"):
    o = OWNER[kind]
    r = {"action": action, "finish_line": _fid(lines, eid), "kind": kind, "space_kind": kind, "layer": "MORTAR_BED",
         "zone": zone, "membrane_in_room": "WHOLE" if kind == "WET" else "NONE", "source_tasks": ["T-414"],
         "expect": {"item_code": code, "element_id": eid, "evidence_state": ev}}
    if action == "BED":
        r["expect"]["measured_net"] = area
        r["area_status"] = status
        r["ledger"] = {"m3_owner_low": round(area * o["lo"], 4), "m3_owner_high": round(area * o["hi"], 4),
                       "b": b, "m3_drawing_high": dh}
    return r


def inputs(lines):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": SRC, "owner": copy.deepcopy(OWNER), "b_upper": copy.deepcopy(B_UP), "rows": [
        _row(lines, "GF-LIV:floor", "DRY", 24.0, "SOURCE_DERIVED", "DRAWING-CONFIRMED", 0.05, 1.2, "GF-DRY"),
        _row(lines, "1F-BED:floor", "DRY", 15.5, "PROVISIONAL", "ASSUMED — OWNER-APPROVED", 0.049, 0.7595, "1F-DRY"),
        _row(lines, "GF-BATH:floor", "WET", 6.0, "SOURCE_DERIVED", "DRAWING-CONFIRMED", code="FIN.FLOOR.WET_TILE"),
        _row(lines, "GF-STRIP:doorway strip", "DRY", None, "NOT_APPLICABLE_WITH_EVIDENCE", None,
             action="NOT_APPLICABLE")]}


def run(lines=None, doc=None):
    lines = lines or lines_3036()
    d = A.load_inputs(doc or inputs(lines), PID)
    ch, log = A.changes_for(d, lines)
    out, ident = A.integrate(lines, ch)
    return lines, ch, log, out, ident


def _bed(out, eid, unit):
    return next(x for x in out if x["location"]["element_id"] == f"{eid}:bed" and x["unit"] == unit)


# ------------------------------------------------------------------------------------------------ normal cases
def test_hand_figures():
    lines, ch, log, out, ident = run()
    assert ident["added"] == 6 and ident["outside_rows_identical_to_v3_0_36"] == 4
    liv2, liv3 = _bed(out, "GF-LIV:floor", "m2"), _bed(out, "GF-LIV:floor", "m3")
    assert liv2["item_code"] == A.BED_DRY and liv2["measured_net"] == 24.0 and liv2["evidence_state"] == "SOURCE_DERIVED"
    assert liv3["evidence_state"] == "BOUNDED_EXPOSURE" and liv3["measured_net"] is None and liv3["gross"] is None
    assert liv3["bounded_range"]["low"] == pytest.approx(0.72) and liv3["bounded_range"]["high"] == pytest.approx(0.96)
    db = liv3["calculation"]["inputs"][A.REC_KEY]["drawing_bound"]
    assert db["high"] == pytest.approx(1.2) and db["status"] == "HELD" and db["owner_check"] == "CONSISTENT"
    bath3 = _bed(out, "GF-BATH:floor", "m3")
    assert bath3["item_code"] == A.BED_WET
    assert (bath3["bounded_range"]["low"], bath3["bounded_range"]["high"]) == pytest.approx((0.24, 0.36))
    assert bath3["calculation"]["inputs"][A.REC_KEY]["drawing_bound"]["high"] is None
    k = log["by_kind"]
    assert k["DRY"]["m2"] == pytest.approx(39.5) and k["WET"]["m2"] == pytest.approx(6.0)
    assert (k["DRY"]["m3_owner_low"], k["DRY"]["m3_owner_high"]) == pytest.approx((1.185, 1.58))
    assert k["DRY"]["m3_drawing_bound_high"] == pytest.approx(1.2 + 0.7905)


def test_upper_bound_takes_the_upper_end_of_the_drawn_range():
    out = run()[3]
    db = _bed(out, "1F-BED:floor", "m3")["calculation"]["inputs"][A.REC_KEY]["drawing_bound"]
    assert db["b"] == 0.049 and db["b_upper"] == 0.051 and db["high"] == pytest.approx(0.7905)
    m2 = _bed(out, "1F-BED:floor", "m2")
    assert m2["evidence_state"] == "PROVISIONAL"
    assert m2["calculation"]["inputs"][A.REC_KEY]["evidence_status"] == "ASSUMED — OWNER-APPROVED"


def test_one_bed_per_finish_line_none_on_na_or_roof():
    lines, ch, log, out, ident = run()
    beds = [x for x in out if x["item_code"] in A.NEW_ITEMS]
    fins = {x["calculation"]["inputs"][A.REC_KEY]["finish_line"] for x in beds}
    assert fins == {_fid(lines, e) for e in ("GF-LIV:floor", "1F-BED:floor", "GF-BATH:floor")}
    assert log["not_applicable"] == [_fid(lines, "GF-STRIP:doorway strip")]
    assert ident["beds"]["beds"] == 3 and ident["beds"]["lines"] == 6


def test_measure_pair_price_one_basis():
    out = run()[3]
    a, b = _bed(out, "GF-LIV:floor", "m2"), _bed(out, "GF-LIV:floor", "m3")
    assert a["measure_pair"] == b["measure_pair"] and a["measure_pair"]["price_one_basis"] is True
    assert set(a["measure_pair"]["lines"]) == {a["line_id"], b["line_id"]}


def test_every_other_line_byte_identical_and_totals_only_in_bed_codes():
    lines, ch, log, out, ident = run()
    for x, y in zip(lines, out):
        assert A30.line_sha(x) == A30.line_sha(y)
    t0, t1 = A304.code_totals(lines), A304.code_totals(out)
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    assert moved == {f"{A.BED_DRY}|m2", f"{A.BED_DRY}|m3", f"{A.BED_WET}|m2", f"{A.BED_WET}|m3"}
    assert t1[f"{A.BED_DRY}|m3"]["released"] == 0 and t1[f"{A.BED_DRY}|m3"]["bounded_lines"] == 2


def test_write_files(tmp_path):
    lines, ch, log, out, ident = run()
    names, ident2, led = A.write(tmp_path, lines, ch, log)
    assert "V3_0_37_BOQ_LINES.json" in names and ident2["diff"]["vs_v3_0_36"] == {"SAME": 4, "ADDED": 6}
    assert any(r["action"] == "NOT_APPLICABLE" for r in led["rows"])


def test_mirror_and_rotation_do_not_matter():
    """a mirrored / rotated plan gives the same finish nets, so the same beds (the bed reads no coordinate)."""
    a = run()[3]
    lines = lines_3036()[::-1]
    b = run(lines, inputs(lines))[3]
    q = lambda o: sorted((x["location"]["element_id"], x["unit"], A30._qty(x)["value"], A30._qty(x)["high"])
                         for x in o if x["item_code"] in A.NEW_ITEMS)
    assert q(a) == q(b)


# ------------------------------------------------------------------------------------------------ adverse cases
def _bad(mut, match):
    lines = lines_3036()
    doc = inputs(lines)
    mut(lines, doc)
    with pytest.raises(A.InputsError, match=match):
        d = A.load_inputs(doc, PID)
        A.changes_for(d, lines)


def test_bed_on_a_roof_refused():
    def m(lines, doc):
        doc["rows"].append(_row([ROOF], "ROOF-1:finish", "DRY", 40.0, "SOURCE_DERIVED", "DRAWING-CONFIRMED", 0.05, 2.0,
                                "RF-DRY", code="FIN.ROOF.FINISH"))
    _bad(m, "OWNED_ELSEWHERE")

    def m2(lines, doc):
        doc["rows"][0]["space_kind"] = "TERRACE"
    _bad(m2, "OWNED_ELSEWHERE")


def test_held_as_zero_refused():
    def m(lines, doc):
        doc["rows"][0]["expect"]["measured_net"] = 0.0
    _bad(m, "HELD_AS_ZERO")


def test_bed_ahead_of_a_finish_refused():
    def m(lines, doc):
        doc["rows"][3]["action"] = "BED"
    _bad(m, "never ahead of it|NOT_APPLICABLE")


def test_finish_line_missing_from_the_table_stops():
    def m(lines, doc):
        lines.append(_line("FIN.FLOOR.PORCELAIN", "2F-NEW:floor", 9.0, floor="2F"))
    _bad(m, "not named by the table")


def test_stale_binding_stops():
    def m(lines, doc):
        lines[0]["measured_net"] = 23.9
    _bad(m, "stale binding")


def test_defaulted_thickness_refused():
    def m(lines, doc):
        doc["owner"].pop("WET")
    _bad(m, "DEFAULTED_THICKNESS")


def test_wet_room_never_takes_the_dry_b():
    def m(lines, doc):
        doc["rows"][2]["ledger"]["b"] = 0.05
        doc["rows"][2]["ledger"]["m3_drawing_high"] = 0.3
    _bad(m, "STEPPED_SLAB_NOT_OWN_LEVEL")


def test_upper_bound_below_the_drawn_b_refused():
    def m(lines, doc):
        doc["b_upper"]["1F-DRY"]["b"] = 0.045
    _bad(m, "upper end")


def test_units_mm_not_metres_refused():
    def m(lines, doc):
        doc["owner"]["DRY"] = {"lo": 30, "hi": 40, "rule": "mm by mistake"}
    _bad(m, "not a bed range in metres")


def test_ledger_figure_mismatch_stops():
    def m(lines, doc):
        doc["rows"][0]["ledger"]["m3_owner_high"] = 1.0
    _bad(m, "stale ledger")


def test_same_finish_line_twice_refused():
    def m(lines, doc):
        doc["rows"].append(copy.deepcopy(doc["rows"][0]))
    _bad(m, "named twice")


def test_applied_once():
    lines, ch, log, out, ident = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(inputs(lines), PID), out)


def test_check_beds_refuses_a_valued_m3_or_a_lonely_line():
    out = run()[3]
    bad = copy.deepcopy(out)
    m3 = next(x for x in bad if x["item_code"] in A.NEW_ITEMS and x["unit"] == "m3")
    m3["evidence_state"], m3["measured_net"], m3["bounded_range"] = "SOURCE_DERIVED", 0.9, None
    with pytest.raises(ValueError, match="owner range"):
        A.check_beds(bad)
    bad = [x for x in copy.deepcopy(out) if not (x["item_code"] in A.NEW_ITEMS and x["unit"] == "m3"
                                                  and x["location"]["element_id"] == "GF-LIV:floor:bed")]
    with pytest.raises(ValueError, match="a pair"):
        A.check_beds(bad)
