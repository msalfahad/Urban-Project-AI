"""T-187: ARCH_TAKEOFF_V3.0.6, the SAME opt-in candidate as V3.0 .. V3.0.5 extended (engine.source.arch_v306), on
synthetic data only (no client drawing).

VILLA M (not the development villa). Dog-leg stair ST-A, GF +0.00 -> 1F +3.40 -> 2F +6.80, every flight 10 risers of
r = 0.17 m, going g = 0.30 m, width w = 1.10 m, printed waist t = 0.15 m ('T 15' in the stair panel):
    cos = 0.30 / sqrt(0.30^2 + 0.17^2) = 0.30 / 0.344819 = 0.870019; t / cos = 0.172410 m
    steps (owner Q-19): 10 x 1/2 x 0.17 x 0.30 x 1.10 = 0.280500 m3
    waist (owner Q-47 A, first to last riser line, plan 9 x 0.30 = 2.70 m): 2.70 x 0.172410 x 1.10 = 0.512056 m3
    one flight = 0.792556 m3; half landing 1.10 x 2.30 x 0.15 = 0.379500 m3
1F -> 2F (the storey route G folds away): MS2-L 0.792556 (VERIFIED by the checker), MS2-U head inside a full-depth
beam billed through the shaft: 0.30 x 1.10 x the waist band below the floor (0.05 m) = 0.016500 m3 owned by the beam
-> 0.776056 (DRAWING-CONFIRMED), landing MS2-LD held 0.3795 .. 0.3960 (two drawn widths 2.30 / 2.40), transition MS2-TR
UNQUANTIFIED (levels not printed): released 1.568612, held 0.379500 .. 0.396000, unknown 1.
Route G GF line (GF -> 1F): waist convention 0.175 m (T 15 printed): 2 flights + landing at 0.175 = 2.0 m3 PROVISIONAL.
Route G pool floor: convention 0.25 m on 10.00 m2 = 2.50 m3 while the structural detail prints 0.35 (3.50 m3): the guard
holds 2.50 and cites 0.35; it never re-values the line.
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
from engine.source import arch_v306 as A306                   # noqa: E402
from engine.source import boq_line as BL                      # noqa: E402
from engine.source import provisional_estimate as PE          # noqa: E402

A = pytest.approx
PID = "synthetic-v306-villa-m"
COS = 0.30 / math.hypot(0.30, 0.17)
FLIGHT = 10 * 0.5 * 0.17 * 0.30 * 1.10 + 2.70 * (0.15 / COS) * 1.10
HEAD = 0.30 * 1.10 * 0.05
CONV = [{"id": "STAIR_WAIST_M", "kind": "dimension", "base": 0.175}, {"id": "POOL_FLOOR_T_M", "kind": "dimension",
                                                                         "base": 0.25},
        {"id": "LINTEL_BEARING_M", "kind": "dimension", "base": 0.20}]


def to_line(it):
    return BL.from_route_g(it, project_id=PID, revision_set_sha256="0" * 64, conventions_set="SV",
                           conventions_digest="d" * 16, documents=[{"file": "M-ST.dxf", "sha256": "1" * 64}])


def route_item(iid, family, storey, q, conv=("X",), trade="CONCRETE", category="PROVISIONAL", exposure=None):
    kw = dict(low=q, base=q, high=q) if category in ("PROVISIONAL", "VERIFIED") else dict(
        exposure_low=exposure[0], exposure_high=exposure[1])
    return PE.item(item_id=iid, component_id=iid.split(":", 1)[1], trade=trade, family=family, storey=storey,
                   category=category, formula="convention", assumptions=list(conv),
                   support="RELEASED" if category == "VERIFIED" else "CONVENTION_ONLY",
                   confidence="MEDIUM", blocker="NOT_REVIEWED", source="SV", **kw)


def base_lines(extra=()):
    its = [route_item("P-C:SCOPE:STAIRS:GF:ST-A:FLIGHTS", "STAIRS", "GF", 2.0, conv=("STAIR_WAIST_M",)),
           route_item("P-C:SCOPE:POOL:GROUND:PL-1:FLOOR", "POOL", "GROUND", 2.50, conv=("POOL_FLOOR_T_M",)),
           route_item("P-C:BEAMS:1F:BAND0007", "BEAMS", "1F", 1.20, conv=(), category="VERIFIED"),
           route_item("P-C:LINTELS:GF:L1", "BEAMS", "GF", 0.30, conv=("LINTEL_BEARING_M",)),
           route_item("U-C:SCOPE:POOL:GROUND:PL-1:WALLS", "POOL", "GROUND", None, conv=("POOL_FLOOR_T_M",),
                      category="UNRESOLVED", exposure=(1.0, 2.0))] + list(extra)
    return [to_line(it) for it in its]


def src(task):
    return {"file": f"research/{task}.json", "sha256": "e" * 64, "task": task, "merge_commit": "abc1234",
            "checker_run": f"verifier run for {task} (MERGED abc1234)"}


def stair_records():
    ge = {"element_id": "ST-A", "part": "1F-2F"}
    return [{"element": "ST-A", "component": "MS2-L", "floor": "1F", "state": "RELEASED", "value": round(FLIGHT, 6),
             "verified_by": "checker own re-measure 0.0 %", "guard_element": ge},
            {"element": "ST-A", "component": "MS2-U", "floor": "1F", "state": "RELEASED",
             "value": round(FLIGHT - HEAD, 6), "guard_element": ge},
            {"element": "ST-A", "component": "MS2-LD", "floor": "1F", "state": "HELD_RANGE", "low": 0.3795,
             "high": 0.396, "reasons": ["two drawn landing widths 2.30 / 2.40"], "guard_element": ge},
            {"element": "ST-A", "component": "MS2-TR", "floor": "1F", "state": "UNQUANTIFIED",
             "reasons": ["landing levels scaled, not printed"], "guard_element": ge}]


def evidence():
    return {"documents": [{"doc": "M-ST.dxf", "role": "PLAN"}, {"doc": "M-ST.pdf", "role": "STRUCTURAL_DETAIL"}],
            "doc_alias": {},
            "printed": [{"id": "EV-T15", "element_kind": "STAIR", "element_id": None, "param": "STAIR_WAIST_M",
                         "value": 0.15, "unit": "m", "doc": "M-ST.pdf", "basis": "STRUCTURAL", "note": "T 15"},
                        {"id": "EV-POOL-35", "element_kind": "POOL", "element_id": "PL-1", "param": "POOL_FLOOR_T_M",
                         "value": 0.35, "unit": "m", "doc": "M-ST.pdf", "basis": "STRUCTURAL", "note": "pool detail"}],
            "inventory": [{"id": "ST-A", "kind": "STAIR", "parts": {"GF-1F": None, "1F-2F": None}},
                          {"id": "PL-1", "kind": "POOL", "parts": {"FLOOR": None, "WALLS": None}}],
            "mapping": {"P-C:SCOPE:STAIRS:GF:ST-A:FLIGHTS": {"element_id": "ST-A", "element_kind": "STAIR",
                                                             "part": "GF-1F"},
                        "P-C:SCOPE:POOL:GROUND:PL-1:FLOOR": {"element_id": "PL-1", "element_kind": "POOL",
                                                             "part": "FLOOR"},
                        "U-C:SCOPE:POOL:GROUND:PL-1:WALLS": {"element_id": "PL-1", "element_kind": "POOL",
                                                             "part": "WALLS"}}}


def inputs(stair=True, records=None, scope_extra=None, placeholders=None, hold=("DG-1", "DG-3", "DG-4", "DG-5"),
           recorded=("DG-2",)):
    doc = {"schema": A306.INPUTS_SCHEMA, "project": PID,
           "guard": {"source": src("T-G"), "evidence": evidence(), "evidence_file": "ev.json",
                     "evidence_sha256": "f" * 64, "conventions": CONV, "conventions_file": "conv.json",
                     "conventions_sha256": "c" * 64, "holding_checks": list(hold), "recorded_checks": list(recorded),
                     "placeholders": placeholders if placeholders is not None else
                     {"ST-A:1F-2F": {"item_code": "STR.CONC.STAIR", "floor": "1F", "physical_element": "STAIRS",
                                     "why": "drawn on the 1F roof slab plan"}}}}
    if stair:
        sc = {"physical_element": "STAIRS", "floors": ["1F", "2F"], "supersede_lines": [], "other_elements": []}
        sc.update(scope_extra or {})
        doc["stair"] = {"piece": "STAIR_CONCRETE", "item_code": "STR.CONC.STAIR", "unit": "m3", "source": src("T-S"),
                        "scope": sc, "records": records if records is not None else stair_records(),
                        "declared_totals": {"released": round(2 * FLIGHT - HEAD, 6), "held_low": 0.3795,
                                            "held_high": 0.396}}
    return doc


def run(doc, base=None):
    base = base if base is not None else base_lines()
    inp = A306.load_inputs(doc, PID)
    ch, logs = A306.changes_for(inp, base)
    out, ident = A306.integrate(base, ch)
    return base, ch, logs, out, ident


def by_eid(lines):
    return {ln["location"]["element_id"]: ln for ln in lines}


# ------------------------------------------------------------------------------------------------ hand values
def test_hand_values_of_villa_m():
    assert 0.15 / COS == A(0.172410, abs=1e-6)
    assert FLIGHT == A(0.280500 + 0.512056, abs=2e-6) and FLIGHT == A(0.792556, abs=1e-6)
    assert HEAD == A(0.0165) and 2 * FLIGHT - HEAD == A(1.568612, abs=2e-6)


# ------------------------------------------------------------------------------------------------ normal case
def test_upper_storey_enters_flight_by_flight_with_its_statuses():
    base, ch, logs, out, ident = run(inputs())
    st = logs[0]
    assert st["totals"]["released"] == A(1.568612, abs=1e-6)
    assert st["totals"]["held_low"] == A(0.3795) and st["totals"]["held_high"] == A(0.396)
    assert st["totals"]["unquantified"] == 1
    adds = {c["after"]["calculation"]["inputs"]["component"]: c for c in ch
            if c["piece"] == "STAIR_CONCRETE" and c["action"] == "ADD"}
    assert sorted(adds) == ["MS2-L", "MS2-LD", "MS2-TR", "MS2-U"]
    assert adds["MS2-L"]["evidence_status"] == "VERIFIED" and adds["MS2-L"]["after"]["measured_net"] == A(0.792556)
    assert adds["MS2-U"]["evidence_status"] == "DRAWING-CONFIRMED"
    assert adds["MS2-LD"]["evidence_status"] == "HELD"
    assert adds["MS2-LD"]["after"]["bounded_range"] == {"low": 0.3795, "high": 0.396, "basis": "ledger readings"}
    tr = adds["MS2-TR"]["after"]
    assert adds["MS2-TR"]["evidence_status"] == "UNKNOWN" and tr["evidence_state"] == "BLOCKED_RFI"
    assert tr["measured_net"] is None and tr["bounded_range"] is None          # missing is never 0
    for c in adds.values():
        ln = c["after"]
        assert ln["item_code"] == "STR.CONC.STAIR" and ln["location"]["floor"] == "1F"
        assert ln["location"]["element_id"].startswith("HL:STAIR_CONCRETE:ST-A:")
        assert ln["rule"]["rule_id"] == "UP-STAIR-003"
    assert ident["outside_rows_identical_to_v3_0_5"] == ident["outside_rows"]


def test_guard_holds_convention_lines_and_cites_the_printed_value():
    base, ch, logs, out, ident = run(inputs())
    g = logs[1]
    held = {c["before"]["location"]["element_id"]: c for c in ch if c["piece"] == "DEFAULT_GUARD"
            and c["action"] == "REPLACE"}
    assert sorted(held) == ["P-C:SCOPE:POOL:GROUND:PL-1:FLOOR", "P-C:SCOPE:STAIRS:GF:ST-A:FLIGHTS"]
    pool = held["P-C:SCOPE:POOL:GROUND:PL-1:FLOOR"]["after"]
    assert pool["evidence_state"] == "BLOCKED_RFI" and pool["measured_net"] is None
    dg = pool["calculation"]["inputs"]["default_guard"]
    assert dg["info_qty_v3_0_5"]["value"] == A(2.50)                        # kept as information, never re-valued
    assert [c["value"] for f in dg["findings"] for c in f["citation"]] == [0.35]
    assert "CONVENTION_WHERE_PRINTED" in pool["rfi"]["question"]
    stair = held["P-C:SCOPE:STAIRS:GF:ST-A:FLIGHTS"]["after"]
    assert [c["value"] for f in stair["calculation"]["inputs"]["default_guard"]["findings"]
            for c in f["citation"]] == [0.15]
    assert g["held_by_trade_unit"] == {"CONCRETE m3": A(4.50)}
    # the lintel line rests on a convention no document prints: DG-1 passes, DG-2 is recorded only, line unchanged
    lin = by_eid(out)["P-C:LINTELS:GF:L1"]
    assert lin == by_eid(base)["P-C:LINTELS:GF:L1"]
    assert any(r["line_id"] == lin["line_id"] and "SEARCH_INCOMPLETE" in r["codes"] for r in g["recorded_only"])
    # an already held (bounded) line with a finding is listed, never re-held
    walls = by_eid(out)["U-C:SCOPE:POOL:GROUND:PL-1:WALLS"]
    assert walls == by_eid(base)["U-C:SCOPE:POOL:GROUND:PL-1:WALLS"]
    assert [x["element_id"] for x in g["listed_not_live"]] == ["U-C:SCOPE:POOL:GROUND:PL-1:WALLS"]
    # the ledger carries ST-A 1F-2F: no silent omission, no placeholder
    assert g["placeholders"] == [] and "SILENT_OMISSION" not in g["findings_by_code"]
    t = A30._qty
    rel = sum(t(ln)["value"] for ln in out if ln["trade"] == "CONCRETE" and ln["evidence_state"] in
              ("PROVISIONAL", "SOURCE_DERIVED", "MEASURED") and t(ln)["value"] is not None)
    assert rel == A(1.20 + 0.30 + 1.568612, abs=1e-6)                       # beam + lintel + upper storey


def test_released_quantities_unchanged_without_guard_input_old_behaviour():
    doc = inputs()
    del doc["guard"]
    base, ch, logs, out, ident = run(doc)
    assert logs[1]["state"] == "NO_PROJECT_INPUT"
    assert by_eid(out)["P-C:SCOPE:POOL:GROUND:PL-1:FLOOR"]["measured_net"] == A(2.50)   # the defect passes silently


# ------------------------------------------------------------------------------------------------ adverse cases
def test_upper_storey_absent_from_the_ledger_stays_held_never_zero():
    base, ch, logs, out, ident = run(inputs(stair=False))
    g = logs[1]
    assert [p["key"] for p in g["placeholders"]] == ["ST-A:1F-2F"]
    ph = by_eid(out)["DG5:ST-A:1F-2F"]
    assert ph["evidence_state"] == "BLOCKED_RFI" and ph["measured_net"] is None and ph["bounded_range"] is None
    assert ph["item_code"] == "STR.CONC.STAIR" and ph["location"]["floor"] == "1F"
    assert "SILENT_OMISSION" in ph["rfi"]["question"]


def test_silent_omission_without_a_placeholder_entry_is_refused():
    with pytest.raises(A306.InputsError, match="placeholder"):
        run(inputs(stair=False, placeholders={}))


def test_an_existing_route_line_of_the_same_element_must_be_accounted_for():
    extra = [route_item("P-C:SCOPE:STAIRS:1F:SITE", "STAIRS", "1F", 1.40, conv=("STAIR_WAIST_M",))]
    with pytest.raises(A306.InputsError, match="only\\s+adds is refused|only adds is refused"):
        run(inputs(), base_lines(extra))
    # superseded by name: NOT_APPLICABLE, its figure kept in the note; never summed
    _b, ch, logs, out, _i = run(inputs(scope_extra={"supersede_lines": [
        {"element_id": "P-C:SCOPE:STAIRS:1F:SITE", "floor": "1F", "why": "the same flights MS2-L / MS2-U"}]}),
        base_lines(extra))
    ln = by_eid(out)["P-C:SCOPE:STAIRS:1F:SITE"]
    assert ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and "1.4" in ln["notes"]
    # declared another physical element: kept, and the guard still checks it (convention where printed -> held)
    doc = inputs(scope_extra={"other_elements": [
        {"element_id": "P-C:SCOPE:STAIRS:1F:SITE", "floor": "1F", "why": "an outside stair ST-B, not ST-A"}]})
    doc["guard"]["evidence"]["mapping"]["P-C:SCOPE:STAIRS:1F:SITE"] = {"element_id": "ST-B", "element_kind": "STAIR",
                                                                       "part": "WHOLE"}
    _b, ch, logs, out, _i = run(doc, base_lines(extra))
    assert logs[0]["scope_lines"][0]["accounted"] == "OTHER_ELEMENT"
    assert by_eid(out)["P-C:SCOPE:STAIRS:1F:SITE"]["evidence_state"] == "BLOCKED_RFI"


def test_named_scope_line_missing_is_refused():
    with pytest.raises(A306.InputsError, match="does not have"):
        run(inputs(scope_extra={"supersede_lines": [{"element_id": "P-C:NOPE", "floor": "1F", "why": "x"}]}))


def test_inputs_refusals():
    bad = inputs()
    bad["guard"]["holding_checks"] = ["DG-3"]
    with pytest.raises(A306.InputsError, match="always hold"):
        A306.load_inputs(bad, PID)
    bad = inputs()
    bad["guard"]["recorded_checks"] = ["DG-1"]
    with pytest.raises(A306.InputsError, match="disjoint"):
        A306.load_inputs(bad, PID)
    bad = inputs()
    del bad["stair"]["source"]["checker_run"]
    with pytest.raises(A306.InputsError, match="checker MERGED"):
        A306.load_inputs(bad, PID)
    r = stair_records()
    del r[2]["reasons"]
    with pytest.raises(A306.InputsError, match="why it is held"):
        A306.load_inputs(inputs(records=r), PID)
    r = stair_records()
    del r[0]["guard_element"]
    with pytest.raises(A306.InputsError, match="guard_element"):
        A306.load_inputs(inputs(records=r), PID)
    r = stair_records()
    r[0]["floor"] = "GF"
    with pytest.raises(A306.InputsError, match="outside the scope"):
        A306.load_inputs(inputs(records=r), PID)
    with pytest.raises(A306.InputsError, match="project inputs are for"):
        A306.load_inputs(inputs(), "another-project")


def test_declared_total_mismatch_is_refused():
    doc = inputs()
    doc["stair"]["declared_totals"]["released"] = 1.6
    with pytest.raises(ValueError, match="own total"):
        run(doc)


def test_mirrored_and_reordered_inputs_give_the_same_lines():
    """order of the route lines and of the ledger records does not change any line (ids from content, not order)."""
    _b, _c, _l, out1, _i = run(inputs())
    r = list(reversed(stair_records()))
    doc = inputs(records=r)
    _b, _c, _l, out2, _i = run(doc, list(reversed(base_lines())))
    assert {ln["line_id"]: A30.line_sha(ln) for ln in out1} == {ln["line_id"]: A30.line_sha(ln) for ln in out2}


def test_unit_must_be_cubic_metres():
    doc = inputs()
    doc["stair"]["unit"] = "m2"
    with pytest.raises(A306.InputsError, match="unit m3"):
        A306.load_inputs(doc, PID)


def test_integrate_refuses_a_line_changed_twice():
    base, ch, logs, out, ident = run(inputs())
    rep = [c for c in ch if c["action"] == "REPLACE"][0]
    with pytest.raises(ValueError, match="changed twice"):
        A306.integrate(base, ch + [copy.deepcopy(rep)])


def test_write_files_and_diff(tmp_path):
    base, ch, logs, out, ident = run(inputs())
    inp = A306.load_inputs(inputs(), PID)
    names, ident2, led = A306.write(tmp_path, base, ch, logs, inp, released_lines=base)
    assert names == sorted(["V3_0_6_BOQ_LINES.json", "V3_0_6_BOQ_LINES.csv", "V3_0_6_INTEGRATION_LEDGER.json",
                            "V3_0_6_INTEGRATION_LEDGER.csv", "V3_0_6_DIFF.csv", "V3_0_6_RUN.json"])
    assert ident2["diff"]["vs_v3_0_5"] == {"SAME": 3, "CHANGED": 2, "ADDED": 4}
    assert led["integration_package"] is True and led["released_default"] is False
    assert all(r["release_status"] == "NOT RELEASED" for r in led["rows"])


def test_cli_registers_the_method_and_its_inputs_flag(tmp_path):
    from tools import urban_boq_m9 as M
    assert M.V306 == A306.METHOD and M.CANDIDATE_EXTENSIONS_V306 == (A306.METHOD,)
    assert A306.EXTENDS == M.V305
    with pytest.raises(SystemExit):
        M.main(["arch", "--drawings", "x.dxf", "--out", str(tmp_path), "--method", "ARCH_TAKEOFF_V3.0.5",
                "--v306-inputs", "x.json"])


def test_a_line_the_drawing_shows_is_not_a_stair_is_held_never_summed():
    """adverse: a dome drawn on the 1F slab plan (lines radiating 360 deg from one point to the dome radius) read by
    the route as a winder stair zone 1.80 m3: held as MISREAD, its figure kept as information, never 0."""
    extra = [route_item("P-C:STAIRS:1F:SITE-dome", "STAIRS", "1F", 1.80, conv=("STAIR_WAIST_M",))]
    doc = inputs(scope_extra={"misread_lines": [
        {"element_id": "P-C:STAIRS:1F:SITE-dome", "floor": "1F",
         "why": "18 lines radiate over 360 deg from one point to r 2.21 m: dome ribs, not treads"}]})
    _b, ch, logs, out, _i = run(doc, base_lines(extra))
    ln = by_eid(out)["P-C:STAIRS:1F:SITE-dome"]
    assert ln["evidence_state"] == "BLOCKED_RFI" and ln["measured_net"] is None and ln["bounded_range"] is None
    assert ln["calculation"]["inputs"]["misread"]["info_qty_v3_0_5"]["value"] == A(1.80)
    assert ln["rfi"]["question"].startswith("MISREAD_AS_STAIRS")
    assert logs[0]["scope_lines"][0]["accounted"] == "MISREAD_HELD"
    # the guard sees it as not live: listed at most, never held twice
    assert ln["line_id"] not in {c["before"]["line_id"] for c in ch if c["piece"] == "DEFAULT_GUARD"
                                 and c["action"] == "REPLACE"}
    with pytest.raises(A306.InputsError, match="accounted for twice"):
        doc2 = copy.deepcopy(doc)
        doc2["stair"]["scope"]["other_elements"] = doc2["stair"]["scope"]["misread_lines"]
        run(doc2, base_lines(extra))


def test_mapping_additions_bind_engine_ids_the_evidence_does_not_know():
    """adverse: the candidate's own stair id is not in the evidence mapping: without an addition the guard neither
    sees the printed waist (kind STAIRS != STAIR) nor counts the part as carried (silent omission refused)."""
    extra = [route_item("P-C:STAIRS:GROUND:SITE-round", "STAIRS", "GROUND", 1.10, conv=("STAIR_WAIST_M",))]
    doc = inputs()
    doc["guard"]["evidence"]["inventory"].append({"id": "ST-R", "kind": "STAIR", "parts": {"WHOLE": None}})
    with pytest.raises(A306.InputsError, match="ST-R:WHOLE has no placeholder"):
        run(doc, base_lines(extra))
    doc["guard"]["mapping_additions"] = {"P-C:STAIRS:GROUND:SITE-round": {
        "element_id": "ST-R", "element_kind": "STAIR", "part": "WHOLE", "why": "zone 8.37 m2 = the round stair zone"}}
    _b, ch, logs, out, _i = run(doc, base_lines(extra))
    ln = by_eid(out)["P-C:STAIRS:GROUND:SITE-round"]
    assert ln["evidence_state"] == "BLOCKED_RFI"
    assert "CONVENTION_WHERE_PRINTED" in ln["rfi"]["question"]
    bad = copy.deepcopy(doc)
    del bad["guard"]["mapping_additions"]["P-C:STAIRS:GROUND:SITE-round"]["why"]
    with pytest.raises(A306.InputsError, match="mapping addition"):
        A306.load_inputs(bad, PID)


def test_convention_equal_to_the_printed_value_is_rebased_not_held():
    """normal: lintel bearing convention 0.20 where the detail prints 0.20 -> REBASED_ON_PRINTED, line unchanged;
    adverse: the same switch never rescues a different printed value (pool 0.25 vs 0.35 stays held)."""
    doc = inputs()
    doc["guard"]["evidence"]["printed"].append({"id": "EV-LB-20", "element_kind": None, "element_id": None,
                                                "param": "LINTEL_BEARING_M", "value": 0.20, "unit": "m",
                                                "doc": "M-ST.pdf", "basis": "STRUCTURAL", "note": "lintel detail"})
    base, ch, logs, out, _i = run(doc)
    assert by_eid(out)["P-C:LINTELS:GF:L1"]["evidence_state"] == "BLOCKED_RFI"        # switch off: held
    doc["guard"]["equal_value_rebase"] = True
    base, ch, logs, out, _i = run(doc)
    lin = by_eid(out)["P-C:LINTELS:GF:L1"]
    assert lin == by_eid(base)["P-C:LINTELS:GF:L1"]
    assert [r["element_id"] for r in logs[1]["rebased_on_printed"]] == ["P-C:LINTELS:GF:L1"]
    assert by_eid(out)["P-C:SCOPE:POOL:GROUND:PL-1:FLOOR"]["evidence_state"] == "BLOCKED_RFI"
