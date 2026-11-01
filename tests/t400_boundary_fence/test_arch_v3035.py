"""T-400: ARCH_TAKEOFF_V3.0.35 (B13-04 boundary fence and gates, component by component) on a hand-calculated
NON-Alsenan villa (V400).

Villa V400, by hand (own figures; nothing from the development villa):
  REAR   neighbour run 18.00 m (owns both corner squares), 0.20 thick, height 2.40 PRINTED above N.G.:
         plane 18.00 x 2.40 = 43.200 m2; faces: outside 18.00 x 2.40 = 43.200, plot (stops at the inner corner)
         17.80 x 2.40 = 42.720 m2; top 18.00 m.l
  SIDE   street run 9.00 m: corner 0.20 owned by REAR, gate G-1 3.00 m -> solid 5.80 m: plane 5.80 x 2.40 = 13.920 m2
  BACK   a third run 4.00 m whose height is not printed: plane HELD blank (4.00 x 2.40 = 9.600 comparison only)
  plane total 43.200 + 13.920 = 57.120 m2 valued; faces valued 43.200 + 42.720 = 85.920 m2
  upper G.B 20 x 40 on the band 31.80 m: 31.80 x 0.20 x 0.40 = 2.544 m3 gross, net HELD (columns not printed):
         its HELD line restated to the range 0 .. 2.544
  lower band line (valued, carries a downgrade) and the opening line of gate G-2: bound, unchanged
  totals: only the B13-04 codes and the upper G.B held range move; every other line byte-identical.
"""
from __future__ import annotations

import copy
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3035 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-v400", "f" * 64
DOCS = [{"file": "v400_plan.dxf", "sha256": "d" * 64}]
SRC = [{"task": t, "file": f"research/v400/{t}.csv", "sha256": str(i) * 64, "merge_commit": chr(97 + i) * 40,
        "checker_run": f"checker run {60 + i} (Gate A PASS)"} for i, t in enumerate(("T-396", "T-403", "T-404",
                                                                                     "T-361"), 1)]
REAR_PLANE = round(18.00 * 2.40, 6)       # 43.200
SIDE_PLANE = round(5.80 * 2.40, 6)        # 13.920
REAR_OUT = round(18.00 * 2.40, 6)         # 43.200
REAR_PLOT = round(17.80 * 2.40, 6)        # 42.720
GB = round(31.80 * 0.20 * 0.40, 6)        # 2.544


def _line(code, eid, ev, net=None, unit="m3", rng=None):
    kw = {"rfi": {"question": "held: depth / count not printed"}} if ev == "BLOCKED_RFI" else {}
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=eid, floor="FOUNDATION", physical_element=eid, gross=net,
                        bounded_range=rng, formula=f"{eid}", documents=DOCS, rule_id="R", rule_version="1",
                        notes="v400", item_en=eid, item_ar=eid, trade="CONCRETE", **kw)


def lines_3034():
    return [_line("STR.CONC.GROUND_BEAM", "BOUNDARY:UPPER_GB", "BLOCKED_RFI"),
            _line("STR.CONC.BOUNDARY_WALL", "BOUNDARY:LOWER_BAND", "MEASURED", 4.0),
            _line("FIN.PAINT", "GATE-OPENING-G-2", "BLOCKED_RFI", unit="m2"),
            _line("STR.CONC.FOOTING", "F1", "MEASURED", 3.0)]


def _id(lines, eid):
    return next(x["line_id"] for x in lines if x["location"]["element_id"] == eid)


def _v(code, eid, terms, value, tasks=("T-396",)):
    return {"action": "FENCE_VALUE", "item_code": code, "element_id": eid, "physical_element": eid, "terms": terms,
            "value": value, "evidence_status": "DRAWING-CONFIRMED", "cause": "hand", "source_tasks": list(tasks)}


def _h(code, eid, held, beside=None, tasks=("T-396",)):
    return {"action": "FENCE_HELD", "item_code": code, "element_id": eid, "physical_element": eid,
            "held_reason": held, "beside": beside, "evidence_status": "HELD", "cause": "hand",
            "source_tasks": list(tasks)}


def inputs(lines):
    rows = [_v(A.WALL, "FENCE:REAR:WALL_PLANE", {"length_m": 18.0, "height_m": 2.4}, REAR_PLANE),
            _v(A.WALL, "FENCE:SIDE:WALL_PLANE", {"length_m": 5.8, "height_m": 2.4}, SIDE_PLANE),
            _h(A.WALL, "FENCE:BACK:WALL_PLANE", "height not printed",
               {"kind": "COMPARISON_ONLY", "value": 9.6, "unit": "m2"}),
            _h(A.BLOCK, "FENCE:REAR:BLOCK_NET", "columns not printed",
               {"kind": "AT_MOST", "value": REAR_PLANE, "unit": "m2"}),
            _h(A.BLOCK_COUNT, "FENCE:ALL:BLOCKS", "block type HELD"),
            _h(A.BELOW_NG, "FENCE:BAND:MASONRY_BELOW_NG", "formation a minimum",
               {"kind": "AT_LEAST", "value": 12.72, "unit": "m2"}, ("T-403",)),
            _h(A.PAD, "FENCE:BAND:PADS", "pad count not printed", {"kind": "PER_UNIT", "value": 0.312,
                                                                   "unit": "m3 per pad"}, ("T-403",)),
            _v(A.FACE, "FENCE:REAR:FACE:OUTSIDE", {"length_m": 18.0, "height_m": 2.4}, REAR_OUT, ("T-404",)),
            _v(A.FACE, "FENCE:REAR:FACE:PLOT", {"length_m": 17.8, "height_m": 2.4}, REAR_PLOT, ("T-404",)),
            _h(A.PLASTER, "FENCE:REAR:FACE:OUTSIDE:PLASTER", "no finish printed",
               {"kind": "AT_MOST", "value": REAR_OUT, "unit": "m2"}, ("T-404",)),
            _v(A.TOP, "FENCE:REAR:TOP", {"length_m": 18.0}, 18.0, ("T-404",)),
            _h(A.GATE, "FENCE:G-1:LEAF", "no leaf drawn", {"kind": "OPENING_WIDTH", "value": 3.0, "unit": "m"},
               ("T-361",))]
    rest = [{"action": "HELD_BOUND", "line_id": _id(lines, "BOUNDARY:UPPER_GB"),
             "expect": {"item_code": "STR.CONC.GROUND_BEAM", "evidence_state": "BLOCKED_RFI", "measured_net": None},
             "gross_terms": {"length_m": 31.8, "width_m": 0.2, "depth_m": 0.4}, "low": 0.0, "high": GB,
             "cause": "columns not printed", "source_tasks": ["T-403"]}]
    binds = [{"action": "BIND", "line_id": _id(lines, "BOUNDARY:LOWER_BAND"),
              "expect": {"item_code": "STR.CONC.BOUNDARY_WALL", "evidence_state": "MEASURED", "measured_net": 4.0},
              "what": "lower band", "share": {"FENCE": [1.0, 2.0]}, "cause": "downgrade on the line",
              "source_tasks": ["T-403"]},
             {"action": "BIND", "line_id": _id(lines, "GATE-OPENING-G-2"),
              "expect": {"item_code": "FIN.PAINT", "evidence_state": "BLOCKED_RFI"},
              "what": "an opening line of gate G-2 (counted once)", "cause": "opening census", "source_tasks": ["T-361"]}]
    recs = [{"item": "FENCE:ALL:COPING", "status": "NOT_DRAWN", "cause": "no coping drawn", "source_tasks": ["T-404"]}]
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": copy.deepcopy(SRC), "lines": rows,
            "restates": rest, "bindings": binds, "records": recs,
            "checks": {"plane_total_m2": round(REAR_PLANE + SIDE_PLANE, 6),
                       "faces_dc_total_m2": round(REAR_OUT + REAR_PLOT, 6), "facade_shared_m2": 0.0,
                       "gate_ids": {"G-1": "FENCE_GATE_LINE", "G-2": "OPENING_CENSUS"}}}


def _run(lines=None, doc=None):
    lines = lines or lines_3034()
    d = A.load_inputs(doc or inputs(lines), PID)
    ch, log = A.changes_for(d, lines)
    out, ident = A.integrate(lines, ch, (), d)
    return lines, d, ch, log, out, ident


# ------------------------------------------------------------------------------------------------ normal
def test_hand_figures():
    assert (REAR_PLANE, SIDE_PLANE, REAR_PLOT, GB) == (43.2, 13.92, 42.72, 2.544)


def test_lines_added_values_and_blanks():
    lines, d, ch, log, out, ident = _run()
    assert ident["added"] == 12 and ident["replaced"] == 1 and len(out) == len(lines) + 12
    f = ident["fence"]
    assert f["valued"] == {"EXT.FENCE.WALL|m2": 57.12, "EXT.FENCE.FACE|m2": 85.92, "EXT.FENCE.TOP|lm": 18.0}
    assert f["blank"] == 7 and f["lines"] == 12
    by = {x["location"]["element_id"]: x for x in out}
    assert by["FENCE:REAR:WALL_PLANE"]["measured_net"] == 43.2 and by["FENCE:REAR:WALL_PLANE"]["evidence_state"] == \
        "MEASURED"
    for eid in ("FENCE:BACK:WALL_PLANE", "FENCE:REAR:BLOCK_NET", "FENCE:BAND:PADS", "FENCE:G-1:LEAF"):
        x = by[eid]
        assert x["evidence_state"] == "BLOCKED_RFI" and x["measured_net"] is None and x["gross"] is None
        assert x["rfi"]["question"].startswith("HELD") and x["bounded_range"] is None
    assert "at least 12.72 m2 beside" in by["FENCE:BAND:MASONRY_BELOW_NG"]["calculation"]["formula"]


def test_held_bound_and_bindings():
    lines, d, ch, log, out, ident = _run()
    gb = next(x for x in out if x["location"]["element_id"] == "BOUNDARY:UPPER_GB")
    assert gb["evidence_state"] == "BLOCKED_RFI" and gb["measured_net"] is None
    assert (gb["bounded_range"]["low"], gb["bounded_range"]["high"]) == (0.0, 2.544)
    rows = A.bind_check(d, out)
    assert [r["action"] for r in rows] == ["BIND", "BIND", "RECORD"] and all(r["lines_added"] == 0 for r in rows)
    band = next(x for x in out if x["location"]["element_id"] == "BOUNDARY:LOWER_BAND")
    assert A30.line_sha(band) == A30.line_sha(lines[1])


def test_everything_else_identical_and_totals():
    lines, d, ch, log, out, ident = _run()
    for a in lines:
        b = next(x for x in out if x["line_id"] == a["line_id"])
        if a["location"]["element_id"] != "BOUNDARY:UPPER_GB":
            assert A30.line_sha(a) == A30.line_sha(b)
    t0, t1 = A304.code_totals(lines), A304.code_totals(out)
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    assert all(k.split("|")[0] in set(A.NEW_ITEMS) | {"STR.CONC.GROUND_BEAM"} for k in moved)
    assert t0["STR.CONC.FOOTING|m3"] == t1["STR.CONC.FOOTING|m3"]


def test_order_invariance():
    lines = lines_3034()
    doc = inputs(lines)
    base = _run(lines, doc)[4]
    d2 = copy.deepcopy(doc)
    random.Random(7).shuffle(d2["lines"])
    other = _run(lines, d2)[4]
    assert sorted(A30.line_sha(x) for x in base) == sorted(A30.line_sha(x) for x in other)


def test_write_files(tmp_path):
    lines, d, ch, log, out, ident = _run()
    names, ident2, led = A.write(tmp_path, lines, ch, log, d)
    assert "V3_0_35_BOQ_LINES.json" in names and led["integration_package"] is True
    assert ident2["diff"]["vs_v3_0_34"] == {"SAME": 3, "CHANGED": 1, "ADDED": 12}
    assert "FENCE:REAR:WALL_PLANE" in (tmp_path / "V3_0_35_INTEGRATION_LEDGER.csv").read_text(encoding="utf-8")


# ------------------------------------------------------------------------------------------------ adverse
def _refused(mut, match=None):
    lines = lines_3034()
    doc = inputs(lines)
    mut(doc, lines)
    with pytest.raises((A.InputsError, ValueError), match=match):
        _run(lines, doc)


def test_adverse_typed_figure_not_its_terms():
    _refused(lambda d, l: d["lines"][0].update(value=45.0), "not its terms")


def test_adverse_held_component_with_a_value():
    _refused(lambda d, l: d["lines"][2].update(value=9.6), "BLANK")


def test_adverse_block_net_valued():
    def m(d, l):
        d["lines"][3] = _v(A.BLOCK, "FENCE:REAR:BLOCK_NET", {"length_m": 18.0, "height_m": 2.4}, REAR_PLANE)
    _refused(m, "cannot carry a figure")


def test_adverse_held_as_zero():
    _refused(lambda d, l: d["lines"][5]["beside"].update(value=0), "never 0")


def test_adverse_mm_as_m():
    _refused(lambda d, l: d["lines"][0].update(terms={"length_m": 18.0, "height_m": 2400.0}, value=43200.0),
             "mm or cm")


def test_adverse_gate_wider_than_face():
    _refused(lambda d, l: d["lines"][7].update(terms={"length_m": 2.0, "height_m": 2.4, "deduct_m2": 5.0},
                                               value=0.0))


def test_adverse_component_twice():
    _refused(lambda d, l: d["lines"].append(copy.deepcopy(d["lines"][0])), "two lines")


def test_adverse_drawn_only_height_valued():
    _refused(lambda d, l: d["lines"][0].update(evidence_status="UNKNOWN"), "DRAWING-CONFIRMED")


def test_adverse_stale_binding():
    _refused(lambda d, l: d["bindings"][0]["expect"].update(measured_net=4.5), "stale binding")


def test_adverse_bound_not_the_drawn_gross():
    _refused(lambda d, l: d["restates"][0].update(high=3.0), "drawn gross")


def test_adverse_bound_low_not_zero():
    _refused(lambda d, l: d["restates"][0].update(low=2.0), "low end")


def test_adverse_facade_shared():
    _refused(lambda d, l: d["checks"].update(facade_shared_m2=0.5), "double count")


def test_adverse_total_not_the_verified_total():
    _refused(lambda d, l: d["checks"].update(plane_total_m2=60.0), "verified total")


def test_adverse_applied_twice():
    lines, d, ch, log, out, ident = _run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(d, out)


def test_adverse_other_line_names_a_fence_element():
    lines, d, ch, log, out, ident = _run()
    bad = copy.deepcopy(out)
    x = next(x for x in bad if x["item_code"] == "STR.CONC.FOOTING")
    x["location"]["element_id"] = "FENCE:REAR:WALL_PLANE"
    with pytest.raises(ValueError, match="outside B13-04"):
        A.check_fence(bad, d)


def test_adverse_gate_counted_twice():
    lines, d, ch, log, out, ident = _run()
    bad = copy.deepcopy(d)
    bad["checks"]["gate_ids"] = {"G-1": "FENCE_GATE_LINE", "G-2": "FENCE_GATE_LINE"}
    with pytest.raises(ValueError, match="counted once"):
        A.check_fence(out, bad)
