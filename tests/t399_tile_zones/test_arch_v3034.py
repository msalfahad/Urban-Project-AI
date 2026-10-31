"""T-399: ARCH_TAKEOFF_V3.0.34 (B4-02 kitchen / laundry / pantry tiled zones bound to the wall-tile line, no second
quantity; the paint under a full-height zone NOT_APPLICABLE) on a hand-calculated NON-Alsenan villa (V399).

Villa V399, by hand (own figures; nothing from the development villa):
  K   closed wet kitchen 4.00 x 3.20 (contour 14.40 m), tile top 3.35 (owner height), door 0.90 x 2.20 = 1.98, window
      1.20 x 1.20 (sill 1.00, head 2.20 < 3.35: deducted whole) = 1.44: 14.40 x 3.35 - 1.98 - 1.44 = 44.820 m2 =
      the FIN.WALL.TILE line (PROVISIONAL) = its backing FIN.PLASTER line; its paint line BLOCKED_RFI blank (old
      hold) -> NOT_APPLICABLE; a 'paint above wall tile' line already NOT_APPLICABLE stays as it is
  P   open pantry: host walls 3.00 + 1.40 = 4.40 m x 3.65 = 16.060 m2, the table reads 16.0700 (drawn 4.4027 m: a
      0.0100 m2 residual, 0.06 %, named); open edge 2.50 m nothing
  L   laundry, owner height not established: carrier, backing HELD BLANK; the table HELD by name
  D   a dry living room: FIN.PLASTER 60.000 and FIN.PAINT 60.000 m2 valued: untouched (not a zone room)
  totals: every valued total identical; FIN.PAINT|m2 one blank line fewer (NOT_APPLICABLE leaves the totals).
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
from engine.source import arch_v3034 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-v399", "e" * 64
DOCS = [{"file": "v399_plan.dxf", "sha256": "d" * 64}]
SRC = [{"task": "T-351", "file": "research/v399/zones.csv", "sha256": "1" * 64, "merge_commit": "a" * 40,
        "checker_run": "checker run 61 (Gate A PASS)"},
       {"task": "T-388", "file": "research/v399/consistency.md", "sha256": "2" * 64, "merge_commit": "b" * 40,
        "checker_run": "checker run 62 (Gate A PASS)"}]
K_NET = round(14.40 * 3.35 - 0.90 * 2.20 - 1.20 * 1.20, 4)          # 44.820
P_NET = round(4.40 * 3.65, 4)                                        # 16.060
P_TABLE = 16.07


def _line(code, room, eid, ev, net=None, unit="m2", floor="GF"):
    kw = {"rfi": {"question": "held"}} if ev == "BLOCKED_RFI" else {}
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=eid, floor=floor, room_id=room, physical_element=eid,
                        gross=net, formula=f"{eid}", documents=DOCS, rule_id="R", rule_version="1",
                        notes="v399", **kw)


def lines_3033():
    return [_line("FIN.WALL.TILE", "R-K", "R-K:wall_tile", "PROVISIONAL", K_NET),
            _line("FIN.PLASTER", "R-K", "R-K:backing", "PROVISIONAL", K_NET),
            _line("FIN.PAINT", "R-K", "R-K:paint", "BLOCKED_RFI"),
            _line("FIN.PAINT", "R-K", "R-K:paint above wall tile", "NOT_APPLICABLE_WITH_EVIDENCE"),
            _line("FIN.WALL.TILE", "R-P", "R-P:wall_tile", "PROVISIONAL", P_NET),
            _line("FIN.PLASTER", "R-P", "R-P:backing", "PROVISIONAL", P_NET),
            _line("FIN.WALL.TILE", "R-L", "R-L:wall_tile", "BLOCKED_RFI", floor="1F"),
            _line("FIN.PLASTER", "R-L", "R-L:backing", "BLOCKED_RFI", floor="1F"),
            _line("FIN.PLASTER", "R-D", "R-D:plaster", "PROVISIONAL", 60.0),
            _line("FIN.PAINT", "R-D", "R-D:paint", "PROVISIONAL", 60.0)]


def _id(lines, eid):
    return next(x["line_id"] for x in lines if x["location"]["element_id"] == eid)


def inputs(lines):
    z = [{"room": "K", "code": "KITCHEN", "engine_room": "R-K", "floor": "GF", "zone": "FULL_HEIGHT", "faces": 4,
          "carrier_line": _id(lines, "R-K:wall_tile"),
          "carrier_expect": {"evidence_state": "PROVISIONAL", "measured_net": K_NET}, "table_net_m2": K_NET,
          "backing_line": _id(lines, "R-K:backing"), "band_above_tile_m2": 0.0, "source_tasks": ["T-351"]},
         {"room": "P", "code": "PANTRY", "engine_room": "R-P", "floor": "GF", "zone": "HOST_FULL_WALL", "faces": 2,
          "carrier_line": _id(lines, "R-P:wall_tile"),
          "carrier_expect": {"evidence_state": "PROVISIONAL", "measured_net": P_NET}, "table_net_m2": P_TABLE,
          "residual": {"m2": round(P_TABLE - P_NET, 6), "cause": "drawn 4.4027 m vs the walk 4.40 m"},
          "backing_line": _id(lines, "R-P:backing"), "band_above_tile_m2": 0.0, "source_tasks": ["T-351"]},
         {"room": "L", "code": "LAUNDRY", "engine_room": "R-L", "floor": "1F", "zone": "FULL_HEIGHT", "faces": 6,
          "carrier_line": _id(lines, "R-L:wall_tile"), "carrier_expect": {"evidence_state": "BLOCKED_RFI",
                                                                          "measured_net": None},
          "table_net_m2": None, "held_item": "owner height not established",
          "backing_line": _id(lines, "R-L:backing"), "band_above_tile_m2": 0.0, "source_tasks": ["T-351"]}]
    rows = [{"action": "ZONE_PAINT_NA", "line_id": _id(lines, "R-K:paint"), "room": "K",
             "expect": {"item_code": "FIN.PAINT", "floor": "GF", "room_id": "R-K", "element_id": "R-K:paint",
                        "evidence_state": "BLOCKED_RFI"},
             "cause": "UP-WET-001 paint none", "old_hold": "plaster rule open", "evidence_status":
             "ASSUMED — OWNER-APPROVED", "source_tasks": ["T-351", "T-388"]}]
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": copy.deepcopy(SRC), "zones": z, "rows": rows}


def _run(lines=None, doc=None):
    lines = lines or lines_3033()
    d = A.load_inputs(doc or inputs(lines), PID)
    ch, log = A.changes_for(d, lines)
    out, ident = A.integrate(lines, ch, (), d)
    return lines, d, ch, log, out, ident


# ------------------------------------------------------------------------------------------------ normal
def test_hand_figures():
    assert K_NET == 44.82 and P_NET == 16.06


def test_zones_bound_no_new_line():
    lines, d, ch, log, out, ident = _run()
    assert len(out) == len(lines) and ident["added"] == 0 and log["b4_02_lines_added"] == 0
    assert log["zones"] == 3 and log["zones_valued"] == 2
    assert log["zone_m2_on_carriers"] == round(K_NET + P_NET, 6)
    z = {r["room"]: r for r in A.zone_check(d, out)}
    assert z["K"]["zone_m2_on_carrier"] == K_NET and z["K"]["double_count_m2"] == 0.0
    assert z["P"]["residual"]["m2"] == 0.01 and z["L"]["zone_m2_on_carrier"] is None
    assert z["L"]["evidence_status"] == "HELD"


def test_paint_na_and_everything_else_identical():
    lines, d, ch, log, out, ident = _run()
    kp = _id(lines, "R-K:paint")
    after = next(x for x in out if x["line_id"] == kp)
    assert after["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and after["measured_net"] is None
    assert after["gross"] is None and after["rfi"] is None and after["notes"]
    for a, b in zip(lines, out):
        if a["line_id"] != kp:
            assert A30.line_sha(a) == A30.line_sha(b)
    assert ident["outside_rows_identical_to_v3_0_33"] == len(lines) - 1


def test_totals_valued_unchanged():
    lines, d, ch, log, out, ident = _run()
    t0, t1 = A304.code_totals(lines), A304.code_totals(out)
    for k in t0:
        assert t0[k]["released"] == t1[k]["released"]
    assert t0["FIN.PAINT|m2"]["blocked_lines"] - t1["FIN.PAINT|m2"]["blocked_lines"] == 1


def test_write_files(tmp_path):
    lines = lines_3033()
    d = A.load_inputs(inputs(lines), PID)
    ch, log = A.changes_for(d, lines)
    names, ident, led = A.write(tmp_path, lines, ch, log, d)
    assert "V3_0_34_BOQ_LINES.json" in names and led["integration_package"]
    acts = [r["action"] for r in led["rows"]]
    assert acts.count("ZONE_COVERED") == 3 and acts.count("ZONE_PAINT_NA") == 1
    diff = (tmp_path / "V3_0_34_DIFF.csv").read_text().splitlines()[1:]
    changed = [r for r in diff if ",CHANGED," in r]                       # the one state change (no figure)
    assert len(changed) == 1 and "BLOCKED_RFI,NOT_APPLICABLE_WITH_EVIDENCE" in changed[0]
    assert sum(",SAME," in r for r in diff) == len(lines) - 1


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut, err=(A.InputsError, ValueError)):
    lines = lines_3033()
    doc = inputs(lines)
    lines = mut(lines, doc) or lines
    with pytest.raises(err):
        d = A.load_inputs(doc, PID)
        ch, _ = A.changes_for(d, lines)
        A.integrate(lines, ch, (), d)


def test_stale_carrier_figure_refused():
    def m(lines, doc):
        doc["zones"][0]["carrier_expect"]["measured_net"] = 44.9
        doc["zones"][0]["table_net_m2"] = 44.9
    _bad(m)


def test_unnamed_residual_refused():
    def m(lines, doc):
        doc["zones"][1].pop("residual")
    _bad(m)


def test_material_residual_refused():
    def m(lines, doc):
        doc["zones"][1]["table_net_m2"] = 17.0
        doc["zones"][1]["residual"]["m2"] = round(17.0 - P_NET, 6)
    _bad(m)


def test_printed_band_is_not_a_coverage():
    def m(lines, doc):
        doc["zones"][0]["zone"] = "BAND"
    _bad(m)


def test_held_zone_with_value_refused():
    def m(lines, doc):
        doc["zones"][2]["table_net_m2"] = 0
    _bad(m)


def test_held_carrier_with_figure_refused():
    def m(lines, doc):
        i = next(i for i, x in enumerate(lines) if x["location"]["element_id"] == "R-L:wall_tile")
        lines[i] = dict(lines[i], measured_net=0.0)
    _bad(m)


def test_valued_paint_on_zone_refused():
    def m(lines, doc):
        return lines + [_line("FIN.PAINT", "R-P", "R-P:paint", "PROVISIONAL", 5.0)]
    _bad(m)


def test_ordinary_plaster_on_zone_refused():
    def m(lines, doc):
        return lines + [_line("FIN.PLASTER", "R-K", "R-K:plaster 2", "PROVISIONAL", 5.0)]
    _bad(m)


def test_second_tile_line_in_zone_refused():
    def m(lines, doc):
        return lines + [_line("FIN.WALL.TILE", "R-K", "R-K:splash band", "PROVISIONAL", 2.28)]
    _bad(m)


def test_backing_not_the_carrier_refused():
    def m(lines, doc):
        i = next(i for i, x in enumerate(lines) if x["location"]["element_id"] == "R-K:backing")
        lines[i] = BL.validate(dict(lines[i], measured_net=40.0, gross=40.0))
    _bad(m)


def test_paint_row_on_dry_room_refused():
    def m(lines, doc):
        doc["rows"][0]["expect"]["room_id"] = "R-D"
    _bad(m)


def test_plaster_row_refused():
    def m(lines, doc):
        doc["rows"][0]["expect"]["item_code"] = "FIN.PLASTER"
    _bad(m)


def test_valued_paint_row_refused():
    def m(lines, doc):
        doc["rows"][0]["expect"]["evidence_state"] = "PROVISIONAL"
    _bad(m)


def test_stale_paint_binding_refused():
    def m(lines, doc):
        doc["rows"][0]["expect"]["element_id"] = "R-K:other"
    _bad(m)


def test_unmerged_source_refused():
    def m(lines, doc):
        doc["rows"][0]["source_tasks"] = ["T-999"]
    _bad(m)


def test_room_in_two_zones_refused():
    def m(lines, doc):
        doc["zones"].append(copy.deepcopy(doc["zones"][0]))
    _bad(m)


def test_band_above_tile_refused():
    def m(lines, doc):
        doc["zones"][0]["band_above_tile_m2"] = 0.5
    _bad(m)


def test_applied_twice_refused():
    lines, d, ch, log, out, ident = _run()
    with pytest.raises(A.InputsError):
        A.changes_for(d, out)


def test_change_outside_rows_refused():
    lines, d, ch, log, out, ident = _run()
    bad = copy.deepcopy(ch)
    bad[0]["after"] = dict(bad[0]["after"], item_code="FIN.PLASTER")
    with pytest.raises(ValueError):
        A.integrate(lines, bad, (), d)


def test_b4_02_line_refused():
    def m(lines, doc):
        x = _line("FIN.WALL.TILE", "R-X", "R-X:t", "PROVISIONAL", 1.0)
        x["item_code"] = "FIN.WALL." + "SPLASHBACK"
        return lines + [x]
    _bad(m)
