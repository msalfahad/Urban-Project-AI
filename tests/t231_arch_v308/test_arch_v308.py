"""T-231: ARCH_TAKEOFF_V3.0.8, the SAME opt-in candidate as V3.0 .. V3.0.7 extended (engine.source.arch_v308), on
synthetic data only (no client drawing).

VILLA Q (not the development villa). Hand values:
  strap ST-1, printed 0.60 x 0.50, oblique at 30 degrees to the grid, axis between the two footing faces 3.00 m:
    plan area 0.60 x 3.00 = 1.80 m2 x 0.50 = 0.900 m3 (owner Q-74: section x the axis length). The route line carried
    the projection on the grid axis 3.00 x cos 30 = 2.598076 m -> 0.60 x 0.50 x 2.598076 = 0.779423 m3 (changed by an
    earlier candidate version, so it is superseded only with that change named). Item move +0.120577 m3.
  strap ST-1 at its far end runs into an OPEN footing outline: the route kept a bounded line 0 .. 0.30 m3 (0.60 x 0.50
    x 1.00); the record resolves the face (closed by its chord) and the part inside is footing concrete (strap depth
    0.50 = footing thickness 0.50): the bounded line is superseded with no strap line replacing it (footing owns it).
  strap ST-2, printed 0.40 x 0.50 on a 0.30 thick footing: inside the outline A_in 0.40 m2; the strap is 0.20 deeper
    than the footing and its level against the footing is not printed: strap concrete in no footing 0.40 x [0.20 ..
    0.50] = 0.080 .. 0.200 m3 BOUNDED (HELD); ST-2 itself 0.40 x 0.50 x 2.00 = 0.400 m3 (route 0.400, the same).
  planted column PC-A, 0.20 x 0.60 = 0.12 m2 from the carrying beam top +4.00 to the slab top +7.50 = 3.50 m ->
    0.420 m3 DRAWING-CONFIRMED; PC-B section conflict (plan text 0.20 x 0.50 vs drawn 0.20 x 0.40) and top not
    printed -> HELD, figures as information.
  the released 2F column C4 (0.504 m3) stands where the 2F slab plan draws nothing -> HELD, consultant item DQ-1; the
    1F column C1 (0.420 m3) is drawn and stays byte-identical.
"""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v304 as A304                   # noqa: E402
from engine.source import arch_v307 as A307                   # noqa: E402
from engine.source import arch_v308 as A308                   # noqa: E402
from engine.source import boq_line as BL                      # noqa: E402

A = pytest.approx
PID = "synthetic-v308-villa-q"
DOCS = [{"file": "Q-ST.dxf", "sha256": "1" * 64}]
PROJ = 0.6 * 0.5 * 3.0 * math.cos(math.radians(30))           # 0.779423 m3, the projection the route carried

ST1, ST1_IN, ST2 = ("P-C:GROUND_BEAMS:FOUNDATION:BAND0001", "P-C:GROUND_BEAMS:FOUNDATION:BAND0001:IN_OPEN",
                    "P-C:GROUND_BEAMS:FOUNDATION:BAND0002")
C1, C4, BEAM = "P-C:COL:SH1:C1@1,1|1F", "P-C:COL:SH1:C4@9,9|2F", "P-C:BEAMS:1F:BAND0007"


def line(eid, item, floor, q=None, ev="SOURCE_DERIVED", br=None, pe="X"):
    return BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code=item, unit="m3", evidence_state=ev,
                        measured_net=q, bounded_range=br, element_id=eid, floor=floor, physical_element=pe,
                        formula="route", documents=DOCS, rule_id="SV", rule_version="1",
                        rfi={"question": "q", "unlocks": eid} if ev == "BLOCKED_RFI" else None)


def l307():
    """the V3.0.7 candidate of villa Q (built directly; arch_v307 is not run on it)."""
    return [line(ST1, "STR.CONC.STRAP", "FOUNDATION", round(PROJ, 6), pe="GROUND_BEAMS"),
            line(ST1_IN, "STR.CONC.STRAP", "FOUNDATION", None, "BOUNDED_EXPOSURE",
                 {"low": 0.0, "high": 0.3, "basis": "open outline"}, pe="GROUND_BEAMS (inside an open footing outline)"),
            line(ST2, "STR.CONC.STRAP", "FOUNDATION", 0.4, pe="GROUND_BEAMS"),
            line(C1, "STR.CONC.COLUMN", "1F", 0.42, "PROVISIONAL", pe="COLUMNS"),
            line(C4, "STR.CONC.COLUMN", "2F", 0.504, "PROVISIONAL", pe="COLUMNS"),
            line(BEAM, "STR.CONC.BEAM", "1F", 1.2, pe="BEAMS")]


def lid(lines, eid):
    return next(ln["line_id"] for ln in lines if ln["location"]["element_id"] == eid)


def src(task):
    return {"file": f"research/{task}.json", "sha256": "e" * 64, "task": task, "merge_commit": "abc1234",
            "checker_run": f"verifier run for {task} (MERGED abc1234)"}


def strap_records(st1_value=0.9, st1_dims_area=1.8, basis="STRUCTURAL", excess=(0.08, 0.2)):
    return [{"element": "ST-1", "component": "CONCRETE", "floor": "FOUNDATION", "state": "RELEASED",
             "value": st1_value,
             "dims": {"kind": "PRISM", "area_m2": st1_dims_area, "height_m": 0.5, "height_basis": basis},
             "verified_by": "checker own re-measure: axis 3.00 m, 0.0 %",
             "guard_element": {"element_id": "ST-1", "part": "CONCRETE"}},
            {"element": "ST-2", "component": "CONCRETE", "floor": "FOUNDATION", "state": "RELEASED", "value": 0.4,
             "dims": {"kind": "PRISM", "area_m2": 0.8, "height_m": 0.5, "height_basis": "STRUCTURAL"},
             "guard_element": {"element_id": "ST-2", "part": "CONCRETE"}},
            {"element": "ST-2", "component": "IN_FOOTING", "part": "F-2", "floor": "FOUNDATION", "state": "BOUNDED",
             "range": list(excess), "evidence_status": "HELD",
             "reasons": ["strap 0.50 deep enters a 0.30 footing; the strap level against the footing is not printed"],
             "guard_element": {"element_id": "ST-2", "part": "IN_FOOTING"}}]


def strap_piece(records=None, supersede=None, other=None):
    return {"piece": "STRAP_CONCRETE", "item_code": "STR.CONC.STRAP", "unit": "m3", "source": src("T-ST"),
            "scope": {"floors": ["FOUNDATION"],
                      "supersede_lines": supersede if supersede is not None else [
                          {"element_id": ST1, "floor": "FOUNDATION", "carried": round(PROJ, 6),
                           "earlier_change": "the V3.0 strap piece measured the projection", "why": "ST-1 at its axis"},
                          {"element_id": ST1_IN, "floor": "FOUNDATION", "carried": [0.0, 0.3],
                           "why": "the open outline closed by its chord: inside it the strap is footing concrete"},
                          {"element_id": ST2, "floor": "FOUNDATION", "carried": 0.4, "why": "ST-2 at its axis"}],
                      "other_elements": other or []},
            "records": records if records is not None else strap_records(),
            "declared_totals": {"released_added": 1.3, "superseded_value": round(PROJ + 0.4, 6),
                                "bounded_added": [0.08, 0.2], "bounded_superseded": [0.0, 0.3]}}


def column_records(section=0.12, height=3.5, value=0.42):
    return [{"element": "PC-A", "component": "CONCRETE", "floor": "1F", "state": "RELEASED", "value": value,
             "dims": {"kind": "PRISM", "area_m2": section, "height_m": height, "height_basis": "STRUCTURAL"},
             "guard_element": {"element_id": "PC-A", "part": "WHOLE"},
             "info": {"owner_split_m3": {"column": 0.33, "joint": 0.06, "slab_part": 0.03}}},
            {"element": "PC-B", "component": "CONCRETE", "floor": "2F", "state": "UNQUANTIFIED",
             "evidence_status": "HELD", "reasons": ["section CONFLICT 0.08 .. 0.10 m2", "top not printed"],
             "guard_element": {"element_id": "PC-B", "part": "WHOLE"}, "info": {"solid_upper_bound_m3": 0.35}}]


def column_piece(records=None, markers=None, other=None):
    return {"piece": "PLANTED_COLUMN", "item_code": "STR.CONC.COLUMN", "unit": "m3", "source": src("T-PC"),
            "scope": {"floors": ["1F", "2F"], "element_markers": markers or [":PC@"],
                      "supersede_lines": [], "other_elements": other or []},
            "records": records if records is not None else column_records()}


def existence(lines_=None):
    return {"source": src("T-EX"), "item_code": "STR.CONC.COLUMN", "unit": "m3", "declared_total": 0.504,
            "lines": lines_ if lines_ is not None else [
                {"element_id": C4, "floor": "2F", "carried": 0.504, "consultant_item": "DQ-1",
                 "why": "no 2F slab over the position; the 2F slab plan draws no member there",
                 "evidence": ["2F slab plan: nothing at the position"], "verified_by": "checker re-read"}]}


def inputs(pieces=None, ex="default", guard=None):
    d = {"schema": A308.INPUTS_SCHEMA, "project": PID,
         "pieces": pieces if pieces is not None else [strap_piece(), column_piece()],
         "existence": existence() if ex == "default" else ex}
    if guard is not None:
        d["guard"] = guard
    return d


def run(doc, base=None, earlier=None):
    l7 = base or l307()
    inp = A308.load_inputs(doc, PID)
    ch, logs = A308.changes_for(inp, l7, earlier if earlier is not None else {lid(l7, ST1)})
    out, ident = A308.integrate(l7, ch)
    return l7, ch, logs, out, ident


def by_eid(lines):
    return {ln["location"]["element_id"]: ln for ln in lines}


# ------------------------------------------------------------------------------------------------ hand values
def test_hand_values_of_villa_q():
    assert PROJ == A(0.779423, abs=1e-6)
    assert 0.60 * 3.00 * 0.50 == A(0.900) and 0.40 * 0.20 == A(0.08) and 0.40 * 0.50 == A(0.20)
    assert 0.12 * (7.50 - 4.00) == A(0.42)


# ------------------------------------------------------------------------------------------------ normal case
def test_normal_records_replace_the_element_lines_and_everything_else_is_identical():
    l7, ch, logs, out, ident = run(inputs())
    e = by_eid(out)
    assert e[ST1]["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and e[ST1]["measured_net"] is None
    assert e[ST1_IN]["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and e[ST1_IN]["bounded_range"] is None
    assert e[ST2]["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE"
    assert e["HL:STRAP_CONCRETE:ST-1:CONCRETE"]["measured_net"] == A(0.9)
    assert e["HL:STRAP_CONCRETE:ST-2:CONCRETE"]["measured_net"] == A(0.4)
    b = e["HL:STRAP_CONCRETE:ST-2:IN_FOOTING:F_2"]
    assert b["evidence_state"] == "BOUNDED_EXPOSURE" and (b["bounded_range"]["low"], b["bounded_range"]["high"]) == (
        A(0.08), A(0.2))
    assert e["HL:PLANTED_COLUMN:PC-A:CONCRETE"]["measured_net"] == A(0.42)
    pcb = e["HL:PLANTED_COLUMN:PC-B:CONCRETE"]
    assert pcb["evidence_state"] == "BLOCKED_RFI" and pcb["measured_net"] is None and "CONFLICT" in pcb["rfi"]["question"]
    c4 = e[C4]
    assert c4["evidence_state"] == "BLOCKED_RFI" and "DQ-1" in c4["rfi"]["question"]
    assert c4["calculation"]["inputs"]["member_existence_v308"]["info_qty_v3_0_7"]["value"] == A(0.504)
    # the drawn column and the beam are byte-identical
    old = by_eid(l7)
    for k in (C1, BEAM):
        assert A308.A30.line_sha(old[k]) == A308.A30.line_sha(e[k])
    assert ident["replaced"] == 4 and ident["added"] == 5 and ident["outside_rows_identical_to_v3_0_7"] == 2


def test_item_totals_move_exactly_by_records_minus_superseded():
    l7, ch, logs, out, _ = run(inputs())
    t7, t8 = A304.code_totals(l7), A304.code_totals(out)
    log = {lg["piece"]: lg for lg in logs}
    assert log["STRAP_CONCRETE"]["totals"]["released_added"] == A(1.3)
    assert log["STRAP_CONCRETE"]["totals"]["item_move"] == A(1.3 - PROJ - 0.4, abs=1e-6)   # +0.120577
    assert log["STRAP_CONCRETE"]["totals"]["bounded_added"] == [A(0.08), A(0.2)]
    assert log["PLANTED_COLUMN"]["totals"]["item_move"] == A(0.42)
    assert log["MEMBER_EXISTENCE"]["held_total_info"] == A(0.504)
    assert set(t8) == set(t7)
    assert t8["STR.CONC.BEAM|m3"] == t7["STR.CONC.BEAM|m3"]
    s7, s8 = t7["STR.CONC.STRAP|m3"], t8["STR.CONC.STRAP|m3"]
    assert s8["released"] - s7["released"] == A(1.3 - round(PROJ, 6) - 0.4, abs=1e-6)          # +0.120577
    assert (s7["held_low"], s7["held_high"], s8["held_low"], s8["held_high"]) == (0.0, A(0.3), A(0.08), A(0.2))
    c7, c8 = t7["STR.CONC.COLUMN|m3"], t8["STR.CONC.COLUMN|m3"]
    assert c8["released"] - c7["released"] == A(0.42 - 0.504)                  # PC-A added, C4 held
    assert c8["blocked_lines"] - c7["blocked_lines"] == 2                       # PC-B and C4


def test_evidence_status_verified_only_with_a_checker_re_measure():
    _, ch, _, _, _ = run(inputs())
    st = {c["after"]["location"]["element_id"]: c["evidence_status"] for c in ch if c["action"] == "ADD"}
    assert st["HL:STRAP_CONCRETE:ST-1:CONCRETE"] == "VERIFIED"
    assert st["HL:STRAP_CONCRETE:ST-2:CONCRETE"] == "DRAWING-CONFIRMED"
    assert st["HL:STRAP_CONCRETE:ST-2:IN_FOOTING:F_2"] == "HELD"
    assert st["HL:PLANTED_COLUMN:PC-A:CONCRETE"] == "DRAWING-CONFIRMED"
    assert st["HL:PLANTED_COLUMN:PC-B:CONCRETE"] == "HELD"


def test_ledger_and_diff_name_every_row_against_v307_and_released():
    l7, ch, logs, out, _ = run(inputs())
    rows = A308.ledger_rows(ch, released_lines=[l7[0], l7[3]])
    assert {r["piece"] for r in rows} >= {"STRAP_CONCRETE", "PLANTED_COLUMN", "MEMBER_EXISTENCE"}
    assert all(r["release_status"] == "NOT RELEASED" for r in rows)
    st1 = next(r for r in rows if r["element_id"] == ST1)
    assert st1["before_v3_0_7"]["value"] == A(round(PROJ, 6)) and "EARLIER_CHANGE" in st1["codes"]
    assert st1["before_released_v2_9"]["value"] == A(round(PROJ, 6))
    diff = A308.diff_rows(l7, out, [l7[0]])
    assert sum(1 for d in diff if d["vs_v3_0_7"] == "SAME") == 2
    assert sum(1 for d in diff if d["vs_v3_0_7"] == "ADDED") == 5


def test_write_files(tmp_path):
    l7, ch, logs, out, _ = run(inputs())
    names, ident, led = A308.write(tmp_path, l7, ch, logs, A308.load_inputs(inputs(), PID), released_lines=l7)
    assert "V3_0_8_BOQ_LINES.json" in names and led["integration_package"] is True and led["released_default"] is False
    assert (tmp_path / "V3_0_8_DIFF.csv").read_text(encoding="utf-8").startswith("line_id,")


def test_default_guard_class_declared():
    assert A308.DEFAULT_GUARD_CLASS == "GUARD_HOST"
    src = (ROOT / "engine/source/arch_v308.py").read_text(encoding="utf-8")
    assert "strap_beam_takeoff" not in src and "planted_columns" not in src   # never an unwired producer


# ------------------------------------------------------------------------------------------------ adverse cases
def test_adverse_an_integration_that_only_adds_is_refused():
    p = strap_piece(supersede=[{"element_id": ST1, "floor": "FOUNDATION", "carried": round(PROJ, 6),
                                "earlier_change": "x", "why": "ST-1"}])
    with pytest.raises(A308.InputsError, match="neither superseded by name"):
        run(inputs([p, column_piece()]))


def test_adverse_superseded_figure_must_be_the_one_the_line_carries():
    p = strap_piece()
    p["scope"]["supersede_lines"][2]["carried"] = 0.45
    with pytest.raises(A308.InputsError, match="carries"):
        run(inputs([p, column_piece()]))
    p = strap_piece()
    p["scope"]["supersede_lines"][1]["carried"] = 0.3          # a bounded line states its range, not one value
    with pytest.raises(A308.InputsError, match="carries"):
        run(inputs([p, column_piece()]))


def test_adverse_an_earlier_change_is_superseded_only_when_named():
    p = strap_piece()
    del p["scope"]["supersede_lines"][0]["earlier_change"]
    with pytest.raises(A308.InputsError, match="earlier candidate version"):
        run(inputs([p, column_piece()]))


def test_adverse_projection_offered_as_the_axis_length_disagrees_with_its_dimensions():
    # 0.900 stated, but dimensions of the projection (1.558846 m2 = 0.60 x 2.598) give 0.779: refused
    with pytest.raises(A308.InputsError, match="disagrees with its dimensions"):
        A308.load_inputs(inputs([strap_piece(records=strap_records(st1_dims_area=0.6 * 2.598076)), column_piece()]), PID)


def test_adverse_units_mm_value_refused():
    with pytest.raises(A308.InputsError, match="disagrees with its dimensions"):
        A308.load_inputs(inputs([strap_piece(records=strap_records(st1_value=900.0)), column_piece()]), PID)
    p = strap_piece()
    p["unit"] = "m2"
    with pytest.raises(A308.InputsError, match="unit m3"):
        A308.load_inputs(inputs([p, column_piece()]), PID)


def test_adverse_full_storey_height_through_the_beam_refused():
    # a planted column measured from the floor below the carrying beam (+3.15, i.e. through the 0.85 beam): 0.12 x 4.35
    # = 0.522 stated against a 3.50 m beam-top height -> refused
    with pytest.raises(A308.InputsError, match="disagrees with its dimensions"):
        A308.load_inputs(inputs([strap_piece(), column_piece(records=column_records(value=0.522))]), PID)


def test_adverse_finished_height_basis_holds_the_record():
    p = strap_piece(records=strap_records(basis="FINISHED"))
    p["declared_totals"] = {}
    _, ch, _, out, _ = run(inputs([p, column_piece()]))
    e = by_eid(out)
    st1 = e["HL:STRAP_CONCRETE:ST-1:CONCRETE"]
    assert st1["evidence_state"] == "BLOCKED_RFI" and st1["measured_net"] is None
    assert st1["calculation"]["inputs"]["figure_not_released_m3"] == A(0.9)


def test_adverse_missing_is_never_zero_and_ranges_are_ordered():
    bad = strap_records()
    bad[0]["value"] = 0
    with pytest.raises(A308.InputsError, match="value > 0"):
        A308.load_inputs(inputs([strap_piece(records=bad), column_piece()]), PID)
    with pytest.raises(A308.InputsError, match="low <= high"):
        A308.load_inputs(inputs([strap_piece(records=strap_records(excess=(0.2, 0.08))), column_piece()]), PID)
    with pytest.raises(A308.InputsError, match="low <= high"):
        A308.load_inputs(inputs([strap_piece(records=strap_records(excess=(0.0, 0.0))), column_piece()]), PID)
    held = column_records()
    del held[1]["reasons"]
    with pytest.raises(A308.InputsError, match="names why"):
        A308.load_inputs(inputs([strap_piece(), column_piece(records=held)]), PID)


def test_adverse_a_released_column_line_kept_without_its_member_is_refused_by_scope():
    # a route line at a planted column position (marker ':PC@') that the inputs neither supersede nor declare -> refused
    base = l307() + [line("P-C:COL:SH1:PC@5,5|1F", "STR.CONC.COLUMN", "1F", 0.42, "PROVISIONAL", pe="COLUMNS")]
    with pytest.raises(A308.InputsError, match="neither superseded by name"):
        run(inputs(), base=base)
    # accounted for by name (the same planted column): superseded, carried once by the record
    p = column_piece()
    p["scope"]["supersede_lines"] = [{"element_id": "P-C:COL:SH1:PC@5,5|1F", "floor": "1F", "carried": 0.42,
                                      "why": "PC-A drawn as a route column"}]
    _, _, logs, out, _ = run(inputs([strap_piece(), p]), base=base)
    assert {lg["piece"]: lg for lg in logs if "totals" in lg}["PLANTED_COLUMN"]["totals"]["item_move"] == A(0.0)


def test_adverse_existence_hold_only_on_a_live_line_with_its_own_figure():
    with pytest.raises(A308.InputsError, match="carries"):
        run(inputs(ex=existence([dict(existence()["lines"][0], carried=0.42)])))
    with pytest.raises(A308.InputsError, match="found 0"):
        run(inputs(ex=existence([dict(existence()["lines"][0], element_id="P-C:COL:SH1:C9@0,0|2F")])))
    base = l307()
    base[4] = line(C4, "STR.CONC.COLUMN", "2F", None, "BLOCKED_RFI", pe="COLUMNS")
    with pytest.raises(A308.InputsError, match="only a live line"):
        run(inputs(), base=base)
    with pytest.raises(A308.InputsError, match="consultant_item"):
        A308.load_inputs(inputs(ex=existence([dict(existence()["lines"][0], consultant_item="")])), PID)


def test_adverse_a_line_cannot_be_held_and_superseded():
    p = column_piece(markers=[":C4@"])
    p["scope"]["supersede_lines"] = [{"element_id": C4, "floor": "2F", "carried": 0.504, "why": "x"}]
    with pytest.raises(ValueError, match="held for existence and changed"):
        run(inputs([strap_piece(), p]))


def test_adverse_pieces_need_a_checker_merged_source():
    p = strap_piece()
    p["source"]["checker_run"] = ""
    with pytest.raises(A308.InputsError, match="checker_run"):
        A308.load_inputs(inputs([p, column_piece()]), PID)
    with pytest.raises(A308.InputsError, match="schema"):
        A308.load_inputs(dict(inputs(), schema="URBAN_V307_INPUTS_V1"), PID)


def test_adverse_mirrored_input_order_changes_nothing():
    # the same pieces and lines in reverse order give the same lines (no order dependence)
    a = run(inputs())[3]
    rev = inputs([column_piece(), strap_piece()])
    b = run(rev, base=list(reversed(l307())))[3]
    assert sorted(A308.A30.line_sha(x) for x in a) == sorted(A308.A30.line_sha(x) for x in b)


def test_no_project_input_changes_nothing():
    l7 = l307()
    ch, logs = A308.changes_for(None, l7)
    assert ch == [] and {lg["state"] for lg in logs} == {"NO_PROJECT_INPUT"}
    out, ident = A308.integrate(l7, ch)
    assert ident["outside_rows_identical_to_v3_0_7"] == len(l7)


# ------------------------------------------------------------------------------------------------ NOT_PRESENT lines
def _not_present(base, eid, route_m3):
    """the V3.0.1 route-scope record: a released column line set NOT_APPLICABLE as NOT_PRESENT, figure kept."""
    out = []
    for ln in base:
        if ln["location"]["element_id"] == eid:
            ln = copy.deepcopy(ln)
            ln.update(evidence_state="NOT_APPLICABLE_WITH_EVIDENCE", measured_net=None)
            ln["calculation"]["inputs"]["v3_0_1"] = {"status": "NOT_PRESENT", "route_m3": route_m3,
                                                     "policy": "ROUTE_G_SCOPE_V1"}
        out.append(ln)
    return out


def test_not_present_line_becomes_a_visible_held_line_and_no_released_quantity_moves():
    base = _not_present(l307(), C4, 0.504)
    ex = existence([dict(existence()["lines"][0], earlier_change="V3.0.1 set it NOT_PRESENT")])
    l7, ch, logs, out, _ = run(inputs(ex=ex), base=base, earlier={lid(base, ST1), lid(base, C4)})
    c4 = by_eid(out)[C4]
    assert c4["evidence_state"] == "BLOCKED_RFI" and c4["measured_net"] is None and "DQ-1" in c4["rfi"]["question"]
    m = c4["calculation"]["inputs"]["member_existence_v308"]
    assert m["figure_m3_information"] == A(0.504) and m["was"].startswith("NOT_APPLICABLE")
    lg = {x["piece"]: x for x in logs}["MEMBER_EXISTENCE"]
    assert lg["held_total_info"] == A(0.504) and lg["released_moved"] == 0.0
    t7, t8 = A304.code_totals(l7)["STR.CONC.COLUMN|m3"], A304.code_totals(out)["STR.CONC.COLUMN|m3"]
    assert t8["released"] - t7["released"] == A(0.42)                    # only PC-A; C4 was not summed before either
    assert t8["blocked_lines"] - t7["blocked_lines"] == 2                # PC-B and the re-opened C4


def test_adverse_not_present_line_without_its_earlier_change_named_or_with_another_figure():
    base = _not_present(l307(), C4, 0.504)
    with pytest.raises(A308.InputsError, match="earlier candidate version"):
        run(inputs(), base=base, earlier={lid(base, ST1), lid(base, C4)})
    ex = existence([dict(existence()["lines"][0], earlier_change="x", carried=0.588)])
    with pytest.raises(A308.InputsError, match="carries 0.504"):
        run(inputs(ex=ex), base=base, earlier={lid(base, ST1), lid(base, C4)})
    plain = l307()
    plain[4] = copy.deepcopy(plain[4])
    plain[4].update(evidence_state="NOT_APPLICABLE_WITH_EVIDENCE", measured_net=None)   # no NOT_PRESENT record
    with pytest.raises(A308.InputsError, match="only a live line"):
        run(inputs(), base=plain)


# ------------------------------------------------------------------------------------------------ guard re-check
def guard(inventory_parts=("CONCRETE",), printed=()):
    return {"source": src("T-G"),
            "evidence": {"documents": [{"doc": "Q-ST.dxf", "role": "PLAN"}], "doc_alias": {}, "printed": list(printed),
                         "inventory": [{"id": "ST-1", "kind": "STRAP", "parts": {p: None for p in inventory_parts}}],
                         "mapping": {}},
            "evidence_file": "ev.json", "evidence_sha256": "f" * 64,
            "conventions": [{"id": "STOREY_HEIGHT_2F", "kind": "dimension", "base": 4.2}],
            "conventions_file": "conv.json", "conventions_sha256": "c" * 64,
            "holding_checks": ["DG-1", "DG-3", "DG-4", "DG-5"], "recorded_checks": ["DG-2"],
            "equal_value_rebase": True, "new_records": []}


def test_guard_re_check_runs_over_the_v308_view():
    _, ch, logs, out, _ = run(inputs(guard=guard()))
    lg = {x["piece"]: x for x in logs}["DEFAULT_GUARD"]
    assert lg["state"] == "RUN" and lg["held_live_new"] == [] and lg["silent_omissions"] == []
    assert not [c for c in ch if c["piece"] == "DEFAULT_GUARD"]


def test_adverse_guard_refuses_a_drawn_part_no_line_carries():
    with pytest.raises(A308.InputsError, match="carried by no line"):
        run(inputs(guard=guard(inventory_parts=("CONCRETE", "IN_FOOTING"))))
