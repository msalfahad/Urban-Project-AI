"""T-193: ARCH_TAKEOFF_V3.0.7, the SAME opt-in candidate as V3.0 .. V3.0.6 extended (engine.source.arch_v307), on
synthetic data only (no client drawing).

VILLA N (not the development villa). Hand values:
  pool, rectangular, outer 4.00 x 3.00 = 12.00 m2, walls 0.20 -> water 3.60 x 2.60 = 9.36 m2, band 2.64 m2;
    base printed 0.35 -> 12.00 x 0.35 = 4.200 m3; RC height rim +0.30 -> structure line -1.00 = 1.30 (STRUCTURAL; the
    printed finished depth 1.25 sits over a 0.05 build-up) -> 2.64 x 1.30 = 3.432 m3; RC 7.632 m3; steps not drawn.
    Route conventions: floor 2.50 m3 (0.25), walls 1.50 m3 (half the ring) = 4.00 m3 -> item move +3.632 m3.
  dome shell, chord 4.00, rise 1.50, thickness 0.10 (all printed):
    R_o = (2.00^2 + 1.50^2) / 3.00 = 2.083333; R_i = 1.983333; h_i = 1.40
    V = pi/3 [1.50^2 (3 x 2.083333 - 1.50) - 1.40^2 (3 x 1.983333 - 1.40)] = pi/3 (10.6875 - 8.918) = 1.853016 m3.
    Route convention 3.000 m3 -> item move -1.146984 m3. The same dome drawn on the 1F slab sheet read as a 4.000 m3
    winder stair (V3.0.6 MISREAD hold): retired, counted once by the dome line.
  dome DM-2: no structural detail -> the V3.0.6 placeholder stays HELD.
"""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30                     # noqa: E402
from engine.source import arch_v304 as A304                   # noqa: E402
from engine.source import arch_v306 as A306                   # noqa: E402
from engine.source import arch_v307 as A307                   # noqa: E402
from engine.source import boq_line as BL                      # noqa: E402
from engine.source import provisional_estimate as PE          # noqa: E402

A = pytest.approx
PID = "synthetic-v307-villa-n"
DOME = math.pi / 3 * (1.5 ** 2 * (3 * (4.0 + 2.25) / 3.0 - 1.5) - 1.4 ** 2 * (3 * ((4.0 + 2.25) / 3.0 - 0.1) - 1.4))
CONV = [{"id": "POOL_FLOOR_T_M", "kind": "dimension", "base": 0.25},
        {"id": "POOL_WALL_H_M", "kind": "dimension", "base": 1.60},
        {"id": "DOME_T_M", "kind": "dimension", "base": 0.12},
        {"id": "STAIR_WAIST_M", "kind": "dimension", "base": 0.175},
        {"id": "BLIND_T_M", "kind": "dimension", "base": 0.10}]


def to_line(it):
    return BL.from_route_g(it, project_id=PID, revision_set_sha256="0" * 64, conventions_set="SV",
                           conventions_digest="d" * 16, documents=[{"file": "N-ST.dxf", "sha256": "1" * 64}])


def route_item(iid, family, storey, q, conv=("X",), category="PROVISIONAL"):
    return PE.item(item_id=iid, component_id=iid.split(":", 1)[1], trade="CONCRETE", family=family, storey=storey,
                   category=category, formula="convention", assumptions=list(conv),
                   support="RELEASED" if category == "VERIFIED" else "CONVENTION_ONLY", confidence="MEDIUM",
                   blocker="NOT_REVIEWED", source="SV", low=q, base=q, high=q)


POOL_F, POOL_W = "P-C:SCOPE:POOL:GROUND:PL-1:FLOOR", "P-C:SCOPE:POOL:GROUND:PL-1:WALLS"
DOME_1, STAIR_X = "P-C:SCOPE:DOMES:2F:DM-1:SHELL", "P-C:STAIRS:1F:SITE-X"
BLIND, BEAM = "P-C:PLAIN_CONCRETE:FOUNDATION:BLIND", "P-C:BEAMS:1F:BAND0007"


def base_lines():
    its = [route_item(POOL_F, "POOL", "GROUND", 2.50, conv=("POOL_FLOOR_T_M",)),
           route_item(POOL_W, "POOL", "GROUND", 1.50, conv=("POOL_WALL_H_M",)),
           route_item(DOME_1, "DOMES", "2F", 3.0, conv=("DOME_T_M",)),
           route_item(STAIR_X, "STAIRS", "1F", 4.0, conv=("STAIR_WAIST_M",)),
           route_item(BLIND, "PLAIN_CONCRETE", "FOUNDATION", 5.0, conv=("BLIND_T_M",)),
           route_item(BEAM, "BEAMS", "1F", 1.20, conv=(), category="VERIFIED")]
    return [to_line(it) for it in its]


def src(task):
    return {"file": f"research/{task}.json", "sha256": "e" * 64, "task": task, "merge_commit": "abc1234",
            "checker_run": f"verifier run for {task} (MERGED abc1234)"}


def evidence(extra=()):
    return {"documents": [{"doc": "N-ST.dxf", "role": "PLAN"}, {"doc": "N-ST.pdf", "role": "STRUCTURAL_DETAIL"}],
            "doc_alias": {},
            "printed": [{"id": "EV-POOL-35", "element_kind": "POOL", "element_id": "PL-1", "param": "POOL_FLOOR_T_M",
                         "value": 0.35, "unit": "m", "doc": "N-ST.pdf", "basis": "STRUCTURAL", "note": "pool detail"},
                        {"id": "EV-POOL-FIN", "element_kind": "POOL", "element_id": "PL-1", "param": "POOL_WALL_H_M",
                         "value": 1.25, "unit": "m", "doc": "N-AR.dxf", "basis": "FINISHED", "note": "water depth"},
                        {"id": "EV-DOME-10", "element_kind": "DOME", "element_id": None, "param": "DOME_T_M",
                         "value": 0.10, "unit": "m", "doc": "N-ST.pdf", "basis": "STRUCTURAL", "note": "dome detail"}]
            + list(extra),
            "inventory": [{"id": "PL-1", "kind": "POOL", "parts": {"FLOOR": None, "WALLS": None}},
                          {"id": "DM-1", "kind": "DOME", "parts": {"SHELL": None}},
                          {"id": "DM-2", "kind": "DOME", "parts": {"SHELL": None}}],
            "mapping": {POOL_F: {"element_id": "PL-1", "element_kind": "POOL", "part": "FLOOR"},
                        POOL_W: {"element_id": "PL-1", "element_kind": "POOL", "part": "WALLS"},
                        DOME_1: {"element_id": "DM-1", "element_kind": "DOME", "part": "SHELL"}}}


def guard(ev=None, new_records=()):
    return {"source": src("T-G"), "evidence": ev or evidence(), "evidence_file": "ev.json", "evidence_sha256": "f" * 64,
            "conventions": CONV, "conventions_file": "conv.json", "conventions_sha256": "c" * 64,
            "holding_checks": ["DG-1", "DG-3", "DG-4", "DG-5"], "recorded_checks": ["DG-2"],
            "equal_value_rebase": True, "new_records": list(new_records),
            "placeholders": {"DM-2:SHELL": {"item_code": "STR.CONC.DOME", "floor": "2F", "physical_element": "DOMES",
                                            "why": "no structural detail"}}}


def v306_inputs():
    return {"schema": A306.INPUTS_SCHEMA, "project": PID, "guard": guard(),
            "stair": {"piece": "STAIR_CONCRETE", "item_code": "STR.CONC.STAIR", "unit": "m3", "source": src("T-S"),
                      "scope": {"physical_element": "STAIRS", "floors": ["1F"], "supersede_lines": [],
                                "other_elements": [],
                                "misread_lines": [{"element_id": STAIR_X, "floor": "1F",
                                                   "why": "radial lines from one point: dome ribs"}]},
                      "records": [], "declared_totals": {}}}


def l306():
    """the V3.0.6 candidate of villa N (V3.0.6 itself, unchanged)."""
    base = base_lines()
    inp = A306.load_inputs(v306_inputs(), PID)
    ch, _logs = A306.changes_for(inp, base)
    out, _ident = A306.integrate(base, ch)
    return out, {c["after"]["line_id"] for c in ch}


def pool_records(height=1.30, basis="STRUCTURAL", value=None):
    return [{"element": "PL-1", "component": "BASE", "floor": "GROUND", "state": "RELEASED", "value": 4.2,
             "dims": {"kind": "PRISM", "area_m2": 12.0, "height_m": 0.35, "height_basis": "STRUCTURAL"},
             "verified_by": "checker own re-measure 0.0 %", "guard_element": {"element_id": "PL-1", "part": "FLOOR"}},
            {"element": "PL-1", "component": "WALLS", "floor": "GROUND", "state": "RELEASED",
             "value": round(2.64 * height, 6) if value is None else value,
             "dims": {"kind": "PRISM", "area_m2": 2.64, "height_m": height, "height_basis": basis},
             "verified_by": "checker own re-measure 0.0 %", "guard_element": {"element_id": "PL-1", "part": "WALLS"}},
            {"element": "PL-1", "component": "STEPS", "floor": "GROUND", "state": "UNQUANTIFIED",
             "evidence_status": "HELD", "reasons": ["STEPS: NOT DRAWN - consultant item"],
             "guard_element": {"element_id": "PL-1", "part": "STEPS"}}]


def dome_records(basis="PRINTED", value=None):
    return [{"element": "DM-1", "component": "SHELL", "floor": "2F", "state": "RELEASED",
             "value": round(DOME, 6) if value is None else value,
             "dims": {"kind": "SPHERICAL_CAP_SHELL", "chord_m": 4.0, "rise_m": 1.5, "thickness_m": 0.1,
                      "basis": {"chord_m": "PRINTED", "rise_m": basis, "thickness_m": "PRINTED"}},
             "verified_by": "checker own re-measure 0.0 %", "guard_element": {"element_id": "DM-1", "part": "SHELL"}}]


def pool_piece(records=None, supersede=None, other=None):
    return {"piece": "POOL_CONCRETE", "item_code": "STR.CONC.POOL", "unit": "m3", "source": src("T-P"),
            "scope": {"physical_element": "POOL", "floors": ["GROUND"],
                      "supersede_lines": supersede if supersede is not None else [
                          {"element_id": POOL_F, "floor": "GROUND", "convention_qty": 2.5, "why": "pool base"},
                          {"element_id": POOL_W, "floor": "GROUND", "convention_qty": 1.5, "why": "pool walls"}],
                      "other_elements": other or [], "retire_lines": []},
            "records": records if records is not None else pool_records()}


def dome_piece(records=None, retire=None):
    return {"piece": "DOME_SHELL", "item_code": "STR.CONC.DOME", "unit": "m3", "source": src("T-D"),
            "scope": {"physical_element": "DOMES", "floors": ["2F"],
                      "supersede_lines": [{"element_id": DOME_1, "floor": "2F", "convention_qty": 3.0,
                                           "why": "dome 1 shell"}],
                      "other_elements": [{"element_id": "DG5:DM-2:SHELL", "floor": "2F", "why": "no detail"}],
                      "retire_lines": retire if retire is not None else [
                          {"element_id": STAIR_X, "floor": "1F", "item_code": "STR.CONC.STAIR", "convention_qty": 4.0,
                           "counted_by": "DM-1:SHELL", "why": "dome 1 drawn on its slab sheet"}]},
            "records": records if records is not None else dome_records()}


def inputs(pieces=None, ev=None, new_records=(), beside=None):
    return {"schema": A307.INPUTS_SCHEMA, "project": PID,
            "pieces": pieces if pieces is not None else [pool_piece(), dome_piece()],
            "beside": beside if beside is not None else [
                {"scenario": "S1_CLIENT_REQUESTED", "element": "DM-1", "item": "shell concrete", "unit": "m3",
                 "qty": 0, "status": "OMITTED_BY_SCENARIO", "basis": "client request", "released": False}],
            "guard": guard(ev, new_records)}


def run(doc, prev=None):
    l6, v6ids = prev or l306()
    inp = A307.load_inputs(doc, PID)
    ch, logs = A307.changes_for(inp, l6, (), v6ids)
    out, ident = A307.integrate(l6, ch)
    return l6, ch, logs, out, ident


def by_eid(lines):
    return {ln["location"]["element_id"]: ln for ln in lines}


def totals(lines):
    return A304.code_totals(lines)


# ------------------------------------------------------------------------------------------------ hand values
def test_hand_values_of_villa_n():
    v = A307.spherical_cap_shell_m3(4.0, 1.5, 0.1)
    assert v == A(1.853016, abs=1e-6) and v == A(DOME, abs=1e-12)
    assert math.pi / 3 * (10.6875 - 8.918) == A(1.853016, abs=1e-6)
    # a hemisphere is the special case rise = half chord: 2/3 pi (R^3 - (R - t)^3)
    assert A307.spherical_cap_shell_m3(4.0, 2.0, 0.1) == A(2 / 3 * math.pi * (2.0 ** 3 - 1.9 ** 3), abs=1e-9)
    assert 12.0 * 0.35 == A(4.2) and 2.64 * 1.30 == A(3.432)


def test_the_v3_0_6_candidate_holds_the_convention_lines_first():
    l6, _ = l306()
    b = by_eid(l6)
    for e in (POOL_F, POOL_W, DOME_1, STAIR_X):
        assert b[e]["evidence_state"] == "BLOCKED_RFI" and b[e]["measured_net"] is None
    assert "DG5:DM-2:SHELL" in b and b[BLIND]["evidence_state"] == "PROVISIONAL"


# ------------------------------------------------------------------------------------------------ normal case
def test_items_move_by_exactly_verified_minus_convention():
    l6, ch, logs, out, ident = run(inputs())
    t6, t7 = totals(l6), totals(out)
    assert t7["STR.CONC.POOL|m3"]["released"] == A(7.632, abs=1e-6)
    assert t7["STR.CONC.POOL|m3"]["released"] - (t6.get("STR.CONC.POOL|m3") or {}).get("released", 0.0) == A(7.632)
    pool, dome = logs[0], logs[1]
    assert pool["totals"] == {"released_added": A(7.632), "convention_superseded": A(4.0), "item_move": A(3.632)}
    assert dome["totals"]["item_move"] == A(1.853016 - 3.0, abs=1e-6)
    assert t7["STR.CONC.DOME|m3"]["released"] == A(DOME, abs=1e-6)
    # the dome is counted once: the misread stair line is retired, no stair quantity anywhere
    assert "STR.CONC.STAIR|m3" not in t7 or t7["STR.CONC.STAIR|m3"]["released"] == 0
    assert dome["retired"][0]["counted_by"] == "DM-1:SHELL" and dome["retired"][0]["info_qty"] == A(4.0)


def test_statuses_and_line_states():
    _l6, ch, _logs, out, _ = run(inputs())
    b = by_eid(out)
    for e in (POOL_F, POOL_W, DOME_1, STAIR_X):
        assert b[e]["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and b[e]["measured_net"] is None
        assert b[e]["rfi"] is None and "V3.0.7" in b[e]["notes"]
    assert "RETIRED" in b[STAIR_X]["notes"] and "SUPERSEDED" in b[POOL_W]["notes"]
    added = [c for c in ch if c["action"] == "ADD"]
    st = {c["after"]["location"]["element_id"]: c["evidence_status"] for c in added}
    assert st == {"HL:POOL_CONCRETE:PL-1:BASE": "VERIFIED", "HL:POOL_CONCRETE:PL-1:WALLS": "VERIFIED",
                  "HL:POOL_CONCRETE:PL-1:STEPS": "HELD", "HL:DOME_SHELL:DM-1:SHELL": "VERIFIED"}
    steps = b["HL:POOL_CONCRETE:PL-1:STEPS"]
    assert steps["evidence_state"] == "BLOCKED_RFI" and steps["measured_net"] is None
    assert "NOT DRAWN" in steps["rfi"]["question"]
    assert b["HL:POOL_CONCRETE:PL-1:WALLS"]["measured_net"] == A(3.432)


def test_every_other_line_is_byte_identical_and_kept():
    l6, _ch, _logs, out, ident = run(inputs())
    b6, b7 = by_eid(l6), by_eid(out)
    for e in (BLIND, BEAM, "DG5:DM-2:SHELL"):
        assert A30.line_sha(b6[e]) == A30.line_sha(b7[e])
    assert ident["replaced"] == 4 and ident["added"] == 4
    assert ident["outside_rows"] == len(l6) - 4 and ident["v3_0_7_lines"] == len(l6) + 4


def test_released_default_untouched_and_scenarios_beside_never_summed(tmp_path):
    l6, ch, logs, out, _ = run(inputs())
    names, _ident, led = A307.write(tmp_path, l6, ch, logs, A307.load_inputs(inputs(), PID))
    import json
    run_doc = json.loads((tmp_path / "V3_0_7_RUN.json").read_text(encoding="utf-8"))
    assert run_doc["released_default"] is False and led["released_default"] is False
    assert run_doc["beside_never_summed"][0]["scenario"] == "S1_CLIENT_REQUESTED"
    assert all(ln["location"]["element_id"].find("S1") < 0 for ln in out)
    assert all(r["release_status"] == "NOT RELEASED" for r in led["rows"])
    assert "V3_0_7_DIFF.csv" in names


def test_no_inputs_changes_nothing():
    l6, v6 = l306()
    ch, logs = A307.changes_for(None, l6, (), v6)
    out, ident = A307.integrate(l6, ch)
    assert ch == [] and ident["outside_rows"] == len(l6)
    assert {x["state"] for x in logs} == {"NO_PROJECT_INPUT"}


# ------------------------------------------------------------------------------------------------ adverse
def test_adverse_pool_wall_known_only_as_a_finished_depth_stays_held():
    doc = inputs(pieces=[pool_piece(pool_records(height=1.25, basis="FINISHED")), dome_piece()])
    _l6, ch, _logs, out, _ = run(doc)
    w = by_eid(out)["HL:POOL_CONCRETE:PL-1:WALLS"]
    assert w["evidence_state"] == "BLOCKED_RFI" and w["measured_net"] is None
    assert "FINISHED" in w["rfi"]["question"] and w["calculation"]["inputs"]["figure_not_released_m3"] == A(3.3)
    st = {c["after"]["location"]["element_id"]: c["evidence_status"] for c in ch if c["action"] == "ADD"}
    assert st["HL:POOL_CONCRETE:PL-1:WALLS"] == "HELD"
    assert totals(out)["STR.CONC.POOL|m3"]["released"] == A(4.2)     # never 0, never the finished figure


def test_adverse_dome_rise_not_printed_stays_held():
    doc = inputs(pieces=[pool_piece(), dome_piece(dome_records(basis="CONVENTION"))])
    _l6, _ch, _logs, out, _ = run(doc)
    d = by_eid(out)["HL:DOME_SHELL:DM-1:SHELL"]
    assert d["evidence_state"] == "BLOCKED_RFI" and "rise_m" in d["rfi"]["question"]


def test_adverse_value_disagreeing_with_its_dimensions_is_refused():
    with pytest.raises(A307.InputsError, match="disagrees with its dimensions"):
        A307.load_inputs(inputs(pieces=[pool_piece(pool_records(value=3.0)), dome_piece()]), PID)
    # units: a height typed in mm instead of m disagrees by a factor 1000
    with pytest.raises(A307.InputsError, match="disagrees"):
        A307.load_inputs(inputs(pieces=[pool_piece(pool_records(height=1300.0, value=3.432)), dome_piece()]), PID)


def test_adverse_rise_equal_to_radius_is_a_different_solid():
    # the route's hemisphere reading (rise = half chord) gives another volume: never accepted for a printed rise
    assert A307.spherical_cap_shell_m3(4.0, 2.0, 0.1) != A(DOME, abs=1e-3)
    with pytest.raises(A307.InputsError, match="disagrees"):
        A307.load_inputs(inputs(pieces=[pool_piece(), dome_piece(dome_records(
            value=round(A307.spherical_cap_shell_m3(4.0, 2.0, 0.1), 6)))]), PID)


def test_adverse_unaccounted_scope_line_refuses_the_run():
    doc = inputs(pieces=[pool_piece(supersede=[{"element_id": POOL_F, "floor": "GROUND", "convention_qty": 2.5,
                                                "why": "base"}]), dome_piece()])
    with pytest.raises(A307.InputsError, match="only adds is refused"):
        run(doc)


def test_adverse_convention_figure_must_be_the_one_the_line_carries():
    doc = inputs(pieces=[pool_piece(supersede=[
        {"element_id": POOL_F, "floor": "GROUND", "convention_qty": 2.5, "why": "base"},
        {"element_id": POOL_W, "floor": "GROUND", "convention_qty": 1.6, "why": "walls"}]), dome_piece()])
    with pytest.raises(A307.InputsError, match="must be the one the line carries"):
        run(doc)


def test_adverse_line_changed_by_an_earlier_version_is_never_replaced():
    l6, v6 = l306()
    pf = by_eid(l6)[POOL_F]["line_id"]
    inp = A307.load_inputs(inputs(), PID)
    with pytest.raises(ValueError, match="V3.0.1 .. V3.0.5"):
        A307.changes_for(inp, l6, {pf}, v6)


def test_adverse_retiring_a_live_line_of_another_item_is_refused():
    base = base_lines()
    doc6 = v306_inputs()
    doc6["stair"]["scope"]["misread_lines"] = []
    doc6["stair"]["scope"]["other_elements"] = [{"element_id": STAIR_X, "floor": "1F", "why": "kept"}]
    inp6 = A306.load_inputs(doc6, PID)
    ch6, _ = A306.changes_for(inp6, base)
    l6 = A306.integrate(base, ch6)[0]
    assert by_eid(l6)[STAIR_X]["evidence_state"] == "PROVISIONAL"
    with pytest.raises(A307.InputsError, match="was not held by V3.0.6"):
        run(inputs(), (l6, {c["after"]["line_id"] for c in ch6}))


def test_adverse_retire_must_name_the_record_that_carries_the_element():
    bad = [{"element_id": STAIR_X, "floor": "1F", "item_code": "STR.CONC.STAIR", "convention_qty": 4.0,
            "counted_by": "DM-9:SHELL", "why": "x"}]
    with pytest.raises(A307.InputsError, match="counted_by"):
        A307.load_inputs(inputs(pieces=[pool_piece(), dome_piece(retire=bad)]), PID)


def test_adverse_missing_is_never_zero():
    recs = pool_records()
    recs[0]["value"] = 0
    with pytest.raises(A307.InputsError, match="never 0"):
        A307.load_inputs(inputs(pieces=[pool_piece(recs), dome_piece()]), PID)
    recs = pool_records()
    del recs[2]["evidence_status"]
    with pytest.raises(A307.InputsError, match="HELD / UNKNOWN"):
        A307.load_inputs(inputs(pieces=[pool_piece(recs), dome_piece()]), PID)


def test_adverse_piece_without_a_checker_verdict_is_not_integrated():
    p = pool_piece()
    p["source"]["checker_run"] = ""
    with pytest.raises(A307.InputsError, match="checker MERGED"):
        A307.load_inputs(inputs(pieces=[p, dome_piece()]), PID)


def test_adverse_scenario_beside_never_s0_never_released():
    with pytest.raises(A307.InputsError, match="beside"):
        A307.load_inputs(inputs(beside=[{"scenario": "S0", "element": "DM-1", "qty": 1}]), PID)
    with pytest.raises(A307.InputsError, match="beside"):
        A307.load_inputs(inputs(beside=[{"scenario": "S1_CLIENT_REQUESTED", "released": True}]), PID)


# ------------------------------------------------------------------------------------------------ guard re-check
def test_guard_new_equal_record_confirms_a_live_line():
    rec = {"id": "EV-BLIND-10", "element_kind": None, "element_id": None, "param": "BLIND_T_M", "value": 0.10,
           "unit": "m", "doc": "N-ST.pdf", "basis": "STRUCTURAL", "note": "10 cm plain concrete under footings"}
    _l6, ch, logs, out, _ = run(inputs(ev=evidence([rec]), new_records=["EV-BLIND-10"]))
    g = logs[-1]
    assert g["state"] == "RUN" and g["held_live_new"] == []
    assert [x["element_id"] for x in g["rebased_on_printed"]] == [BLIND]
    assert g["new_records"]["EV-BLIND-10"][0]["code"] == "CONVENTION_WHERE_PRINTED"
    assert by_eid(out)[BLIND]["measured_net"] == A(5.0)               # unchanged, now resting on the printed value


def test_guard_new_differing_record_holds_a_live_line_never_zero():
    rec = {"id": "EV-BLIND-15", "element_kind": None, "element_id": None, "param": "BLIND_T_M", "value": 0.15,
           "unit": "m", "doc": "N-ST.pdf", "basis": "STRUCTURAL", "note": "15 cm"}
    _l6, ch, logs, out, _ = run(inputs(ev=evidence([rec]), new_records=["EV-BLIND-15"]))
    b = by_eid(out)[BLIND]
    assert b["evidence_state"] == "BLOCKED_RFI" and b["measured_net"] is None
    assert b["calculation"]["inputs"]["default_guard_v307"]["info_qty_v3_0_6"]["value"] == A(5.0)
    assert logs[-1]["held_live_new"][0]["element_id"] == BLIND


def test_guard_a_new_drawn_part_no_line_carries_refuses_the_run():
    ev = evidence()
    ev["inventory"].append({"id": "TK-1", "kind": "TANK", "parts": {"WALLS": None}})
    with pytest.raises(A307.InputsError, match="carried by no line"):
        run(inputs(ev=ev))


def test_guard_new_record_must_be_in_the_evidence():
    with pytest.raises(A307.InputsError, match="new record"):
        A307.load_inputs(inputs(new_records=["EV-NOPE"]), PID)


def test_cli_refuses_v307_inputs_without_the_method(tmp_path):
    from tools import urban_boq_m9 as M
    with pytest.raises(SystemExit, match="--v307-inputs needs"):
        M.main(["arch", "--drawings", str(tmp_path / "x.dxf"), "--out", str(tmp_path), "--method",
                "ARCH_TAKEOFF_V3.0.6", "--v307-inputs", str(tmp_path / "i.json")])


def test_policy_record():
    p = A307.policy_record()
    assert p["extends"] == "ARCH_TAKEOFF_V3.0.6" and p["released_default"] is False
    assert {"POOL_CONCRETE", "DOME_SHELL", "DEFAULT_GUARD"} <= set(p["pieces"])
