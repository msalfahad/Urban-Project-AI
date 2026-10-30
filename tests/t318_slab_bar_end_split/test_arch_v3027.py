"""T-318: ARCH_TAKEOFF_V3.0.27 (the suspended-slab DEVELOPMENT and TOP reinforcement lines re-booked bar end by bar end
from checker-merged support-class ledgers: drawn parts valued, undrawn ends / legs BLANK by name, all-continuous
development NOT_APPLICABLE) on a hand-calculated NON-Alsenan villa (V318), normal and adverse.

Villa V318, by hand (d10 bars, u = 10^2 / 162 = 0.617284 kg/m; 5 o 10/m over 3.00 m: count A = 15, B = 16 bars):
  S1 (clear span 4.00 m, x bars): one end on a 0.25 m EDGE beam, the other CONTINUOUS over a 0.20 m beam into S2
     (clear span 5.00 m).
     candidate development (note 9, 2 x 40 d .. 2 x 70 d per bar): 15 x 0.80 x u = 7.407 .. 16 x 1.40 x u = 13.827 kg
     drawn (p.15): continuous end 0 m; edge end straight 0.25 - 0.040 = 0.21 m:
       A 15 x 0.21 x u = 1.944 kg .. B 16 x 0.21 x u = 2.074 kg; up-turn leg at 15..16 ends HELD   -> PARENT + PART
     candidate top: 12.346 .. 30.000 kg (reading i .. p.15 past the span, as the T-152 line)
     p.15 on its ends: continuous 0.30 x max(4.00, 5.00) = 1.50 + band 0.10; edge 0.25 x 4.00 = 1.00 + across
       [0.21, 0.25]: A 15 x 2.81 x u = 26.019 .. B 16 x 2.85 x u = 28.148 kg; hook-down leg HELD
     note 2 on the same ends: i = L/6 per end: 15 x 1.3333 x u = 12.346; ii = L/3 per end + crossing 0.10:
       16 x 2.7667 x u = 27.325 kg
     -> PART bound [min(12.346, 26.019), max(27.325, 28.148)] = 12.346 .. 28.148 kg (two printed documents)
  S3 (both ends continuous): development NOT_APPLICABLE_WITH_EVIDENCE (no development drawn); top every end valued,
     nothing held: REBASE in place = [min(9.000, 11.500), max(18.000, 12.250)] = 9.000 .. 18.000 kg
  S4 (sunken panel, both ends at level steps): development HELD, top HELD (no detail draws a bar end at a step)
  A BOTTOM MESH line and a concrete line stay byte-identical.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v3027 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-v318", "f" * 64
DOCS = [{"file": "v318_structure.dxf", "sha256": "c" * 64}]
U = 100.0 / 162.0


def _r3(x):
    return round(x, 3)


# hand calculation (the figures the ledger of this villa would carry)
DEV_S1 = (_r3(15 * 0.21 * U), _r3(16 * 0.21 * U))                 # 1.944 .. 2.074
DEV_S1_BEFORE = (_r3(15 * 0.80 * U), _r3(16 * 1.40 * U))          # 7.407 .. 13.827
TOP_S1_P15 = (_r3(15 * 2.81 * U), _r3(16 * 2.85 * U))             # 26.019 .. 28.148
TOP_S1_N2 = (_r3(15 * (4.0 / 3.0) * U), _r3(16 * (8.0 / 3.0 + 0.10) * U))   # 12.346 .. 27.325


def _ln(eid, comp, part, low, high, floor="1F"):
    inputs = {"policy": "SLAB_STEEL_HAND_LEDGER_V1", "element": eid, "component": comp, "part": part}
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="STR.REBAR", unit="kg",
                        evidence_state="BOUNDED_EXPOSURE", measured_net=None,
                        element_id=f"HL:SLAB_STEEL:{eid}:{comp.replace(' / ', '_').replace(' ', '_')}:{part.upper()}",
                        floor=floor, physical_element="SLABS", bounded_range={"basis": "v318", "low": low,
                                                                              "high": high},
                        formula="v318 candidate", inputs=inputs, documents=DOCS, rule_id="R", rule_version="1",
                        rfi={"question": "bound"}, notes="v318", subtrade="SLABS / 10 mm")


def lines_3026():
    conc = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="STR.CONC.SLAB", unit="m3",
                        evidence_state="SOURCE_DERIVED", measured_net=2.4, element_id="SLAB:S1", floor="1F",
                        formula="4 x 3 x 0.20 = 2.4", documents=DOCS, rule_id="R", rule_version="1")
    return [conc,
            _ln("SLAB:S1", "BOTTOM MESH", "x", 20.0, 22.0),
            _ln("SLAB:S1", "DEVELOPMENT / ANCHORAGE", "x", *DEV_S1_BEFORE),
            _ln("SLAB:S1", "TOP BARS OVER SUPPORTS", "x", TOP_S1_N2[0], 30.0),
            _ln("SLAB:S3", "DEVELOPMENT / ANCHORAGE", "x", 7.407, 13.827),
            _ln("SLAB:S3", "TOP BARS OVER SUPPORTS", "x", 9.0, 18.0),
            _ln("SLAB:S4", "DEVELOPMENT / ANCHORAGE", "x", 3.951, 7.778),
            _ln("SLAB:S4", "TOP BARS OVER SUPPORTS", "x", 2.199, 9.301)]


def _lid(lines, eid, comp):
    return next(ln["line_id"] for ln in lines if (ln["calculation"]["inputs"] or {}).get("element") == eid
                and ln["calculation"]["inputs"].get("component") == comp)


SRC = {"T-307": {"task": "T-307", "file": "research/v318/dev.csv", "sha256": "1" * 64, "merge_commit": "a" * 40,
                 "checker_run": "checker run 7 (Gate A PASS)"},
       "T-316": {"task": "T-316", "file": "research/v318/top.csv", "sha256": "2" * 64, "merge_commit": "b" * 40,
                 "checker_run": "checker run 8 (Gate A PASS)"}}


def doc(lines=None):
    lines = lines or lines_3026()
    D, T = "DEVELOPMENT / ANCHORAGE", "TOP BARS OVER SUPPORTS"
    recs = [
        {"line_id": _lid(lines, "SLAB:S1", D), "element": "SLAB:S1", "direction": "x", "population": D,
         "status": "BOUND_PART_WITH_HELD", "before": {"low": DEV_S1_BEFORE[0], "high": DEV_S1_BEFORE[1]},
         "valued": {"low": DEV_S1[0], "high": DEV_S1[1], "basis": "p.15 straight part w - 0.040 m, count A .. B"},
         "ends_A": "CONTINUOUS=15;EDGE_BEAM=15", "ends_B": "CONTINUOUS=16;EDGE_BEAM=16",
         "held_items": "UPTURN_LEG at 15..16 edge-beam ends: leg not dimensioned", "source_task": "T-307"},
        {"line_id": _lid(lines, "SLAB:S3", D), "element": "SLAB:S3", "direction": "x", "population": D,
         "status": "NOT_APPLICABLE_WITH_EVIDENCE", "before": {"low": 7.407, "high": 13.827},
         "ends_A": "CONTINUOUS=30", "ends_B": "CONTINUOUS=32", "held_items": "", "source_task": "T-307"},
        {"line_id": _lid(lines, "SLAB:S4", D), "element": "SLAB:S4", "direction": "x", "population": D,
         "status": "HELD", "before": {"low": 3.951, "high": 7.778}, "ends_A": "STEP_EDGE=16",
         "ends_B": "STEP_EDGE=18", "held_items": "STEP_EDGE ends 16..18", "source_task": "T-307"},
        {"line_id": _lid(lines, "SLAB:S1", T), "element": "SLAB:S1", "direction": "x", "population": T,
         "status": "DRAWING_DERIVED_P15_PART_WITH_HELD_LEGS", "before": {"low": TOP_S1_N2[0], "high": 30.0},
         "note2_valued": {"low": TOP_S1_N2[0], "high": TOP_S1_N2[1]},
         "p15_valued": {"low": TOP_S1_P15[0], "high": TOP_S1_P15[1]},
         "held_ends": {}, "unresolved_ends": {}, "hook_legs_held": [15, 16],
         "ends_A": "CONTINUOUS=15;EDGE_BEAM=15", "ends_B": "CONTINUOUS=16;EDGE_BEAM=16", "source_task": "T-316"},
        {"line_id": _lid(lines, "SLAB:S3", T), "element": "SLAB:S3", "direction": "x", "population": T,
         "status": "DRAWING_DERIVED_P15", "before": {"low": 9.0, "high": 18.0},
         "note2_valued": {"low": 9.0, "high": 18.0}, "p15_valued": {"low": 11.5, "high": 12.25},
         "held_ends": {}, "unresolved_ends": {}, "hook_legs_held": None,
         "ends_A": "CONTINUOUS=30", "ends_B": "CONTINUOUS=32", "source_task": "T-316"},
        {"line_id": _lid(lines, "SLAB:S4", T), "element": "SLAB:S4", "direction": "x", "population": T,
         "status": "HELD", "before": {"low": 2.199, "high": 9.301}, "held_ends": {"STEP_EDGE": [18, 20]},
         "unresolved_ends": {}, "hook_legs_held": None, "ends_A": "STEP_EDGE=18", "ends_B": "STEP_EDGE=20",
         "source_task": "T-316"},
    ]
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "task": "T-318", "unit": "kg",
            "sources": copy.deepcopy(list(SRC.values())), "lines": recs}


def run(d=None, lines=None):
    lines = lines or lines_3026()
    inp = A.load_inputs(d or doc(lines), PID)
    ch, log = A.changes_for(inp, lines)
    out, ident = A.integrate(lines, ch)
    return lines, out, ident, ch, log


def _by_eid(out, eid, comp):
    return [ln for ln in out if (ln["calculation"]["inputs"].get("slab_bar_end_split_v3027") or {}).get("element")
            == eid and comp in (ln["calculation"]["inputs"]["slab_bar_end_split_v3027"].get("population") or "")]


# ================================================================================================ normal
def test_hand_figures():
    assert DEV_S1 == (1.944, 2.074)
    assert DEV_S1_BEFORE == (7.407, 13.827)
    assert TOP_S1_P15 == (26.019, 28.148)
    assert TOP_S1_N2 == (12.346, 27.325)


def test_development_split_parent_and_part():
    lines, out, ident, ch, log = run()
    rows = _by_eid(out, "SLAB:S1", "DEVELOPMENT")
    par = next(r for r in rows if r["calculation"]["inputs"]["slab_bar_end_split_v3027"]["action"] == "PARENT")
    part = next(r for r in rows if r["calculation"]["inputs"]["slab_bar_end_split_v3027"]["action"] == "PART")
    assert par["line_id"] == _lid(lines, "SLAB:S1", "DEVELOPMENT / ANCHORAGE")
    assert par["evidence_state"] == "BLOCKED_RFI" and par["measured_net"] is None and par["bounded_range"] is None
    assert "UPTURN_LEG" in par["rfi"]["question"]
    assert part["evidence_state"] == "BOUNDED_EXPOSURE" and part["measured_net"] is None
    assert (part["bounded_range"]["low"], part["bounded_range"]["high"]) == DEV_S1
    assert part["calculation"]["inputs"]["slab_bar_end_split_v3027"]["parent_line_id"] == par["line_id"]
    assert par["calculation"]["inputs"]["slab_bar_end_split_v3027"]["part"] == part["line_id"]
    assert part["item_code"] == "STR.REBAR" and part["unit"] == "kg" and part["location"]["floor"] == "1F"


def test_development_all_continuous_not_applicable():
    _l, out, *_ = run()
    (ln,) = _by_eid(out, "SLAB:S3", "DEVELOPMENT")
    assert ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE"
    assert ln["measured_net"] is None and ln["bounded_range"] is None and "p.15" in ln["notes"]


def test_held_lines_blank_never_zero():
    _l, out, *_ = run()
    for comp in ("DEVELOPMENT", "TOP BARS"):
        (ln,) = _by_eid(out, "SLAB:S4", comp)
        assert ln["evidence_state"] == "BLOCKED_RFI" and ln["measured_net"] is None and ln["bounded_range"] is None
        assert "STEP_EDGE" in ln["rfi"]["question"]


def test_top_split_envelope_of_two_documents():
    _l, out, *_ = run()
    rows = _by_eid(out, "SLAB:S1", "TOP BARS")
    part = next(r for r in rows if r["calculation"]["inputs"]["slab_bar_end_split_v3027"]["action"] == "PART")
    par = next(r for r in rows if r["calculation"]["inputs"]["slab_bar_end_split_v3027"]["action"] == "PARENT")
    assert (part["bounded_range"]["low"], part["bounded_range"]["high"]) == (12.346, 28.148)
    rd = part["calculation"]["inputs"]["slab_bar_end_split_v3027"]["readings"]
    assert rd["note2"] == {"low": 12.346, "high": 27.325} and rd["p15"] == {"low": 26.019, "high": 28.148}
    assert "hook-down leg" in par["rfi"]["question"] and par["bounded_range"] is None


def test_top_rebase_in_place():
    lines, out, *_ = run()
    (ln,) = _by_eid(out, "SLAB:S3", "TOP BARS")
    assert ln["line_id"] == _lid(lines, "SLAB:S3", "TOP BARS OVER SUPPORTS")
    assert ln["evidence_state"] == "BOUNDED_EXPOSURE" and (ln["bounded_range"]["low"], ln["bounded_range"]["high"]) \
        == (9.0, 18.0)


def test_outside_lines_byte_identical_and_identity():
    lines, out, ident, ch, _ = run()
    by = {ln["line_id"]: ln for ln in lines}
    for ln in out:
        if not ln["calculation"]["inputs"].get("slab_bar_end_split_v3027"):
            assert A30.line_sha(ln) == A30.line_sha(by[ln["line_id"]])
    assert ident["replaced"] == 6 and ident["added"] == 2 and ident["outside_rows"] == 2
    assert ident["slab_bar_ends"]["parts"] == 2 and ident["slab_bar_ends"]["not_applicable"] == 1
    assert ident["slab_bar_ends"]["restated"] == 2 and ident["slab_bar_ends"]["rebased"] == 1


def test_order_invariance():
    d = doc()
    d2 = copy.deepcopy(d)
    d2["lines"] = list(reversed(d2["lines"]))
    _l, o1, *_ = run(d)
    _l, o2, *_ = run(d2)
    assert sorted(A30.line_sha(x) for x in o1) == sorted(A30.line_sha(x) for x in o2)


def test_write_files_and_totals(tmp_path):
    lines, out, ident, ch, log = run()
    inp = A.load_inputs(doc(lines), PID)
    ch, log = A.changes_for(inp, lines)
    names, ident, led = A.write(tmp_path, lines, ch, log, inp, None)
    assert "V3_0_27_BOQ_LINES.json" in names and "V3_0_27_DIFF.csv" in names
    run_j = json.loads((tmp_path / "V3_0_27_RUN.json").read_text(encoding="utf-8"))
    assert list(run_j["totals_moved_by_code"]) == ["STR.REBAR|kg"]
    assert led["released_default"] is False
    assert log["kg"]["DEVELOPMENT / ANCHORAGE"]["valued_low"] == DEV_S1[0]


# ================================================================================================ adverse
def _bad(mut, match):
    d = doc()
    mut(d)
    with pytest.raises(A.InputsError, match=match):
        run(d)


def _rec(d, eid, pop_word):
    return next(r for r in d["lines"] if r["element"] == eid and pop_word in r["population"])


def test_na_with_value_refused():
    _bad(lambda d: _rec(d, "SLAB:S3", "DEV").update(valued={"low": 0.1, "high": 0.2, "basis": "p.15"}),
         "all-continuous")


def test_held_line_with_value_refused():
    _bad(lambda d: _rec(d, "SLAB:S4", "TOP").update(p15_valued={"low": 1.0, "high": 2.0}), "given a value")


def test_held_as_zero_refused():
    _bad(lambda d: _rec(d, "SLAB:S1", "DEV").update(valued={"low": 0.0, "high": 0.0, "basis": "p.15"}), "high 0")


def test_leg_value_refused():
    _bad(lambda d: _rec(d, "SLAB:S1", "DEV").update(leg_kg=0.5), "carry no figure")


def test_note9_basis_refused():
    _bad(lambda d: _rec(d, "SLAB:S1", "DEV")["valued"].update(basis="note 9 2 x 40 d per bar"), "note-9")


def test_lap_basis_refused():
    _bad(lambda d: _rec(d, "SLAB:S1", "DEV")["valued"].update(basis="owner 60 d lap"), "note-9 / lap")


def test_part_without_held_refused():
    def m(d):
        r = _rec(d, "SLAB:S1", "TOP")
        r["hook_legs_held"] = None
    _bad(m, "REBASE, not a split")


def test_rebase_with_held_refused():
    _bad(lambda d: _rec(d, "SLAB:S3", "TOP").update(held_ends={"STEP_EDGE": [1, 1]}), "must be split")


def test_low_above_high_refused():
    _bad(lambda d: _rec(d, "SLAB:S1", "DEV")["valued"].update(low=3.0), "low 3.0 > high")


def test_stale_before_refused():
    _bad(lambda d: _rec(d, "SLAB:S1", "DEV")["before"].update(high=14.0), "stale ledger")


def test_line_not_in_candidate_refused():
    _bad(lambda d: _rec(d, "SLAB:S1", "DEV").update(line_id="L-00000000000000000000"), "does not carry")


def test_wrong_component_refused():
    _bad(lambda d: _rec(d, "SLAB:S1", "DEV").update(direction="y"), "direction is not the line")


def test_twice_in_inputs_refused():
    def m(d):
        d["lines"].append(copy.deepcopy(d["lines"][0]))
    _bad(m, "twice")


def test_unknown_status_refused():
    _bad(lambda d: _rec(d, "SLAB:S1", "DEV").update(status="BOUND"), "status")


def test_unit_in_tonnes_refused():
    _bad(lambda d: d.update(unit="t"), "kg")


def test_source_without_checker_run_refused():
    _bad(lambda d: d["sources"][0].update(checker_run=""), "checker_run missing")


def test_applied_twice_refused():
    lines, out, *_ = run()
    inp = A.load_inputs(doc(lines), PID)
    with pytest.raises(A.InputsError):
        A.changes_for(inp, out)


def test_part_beside_parent_with_figure_refused():
    lines, out, ident, ch, _ = run()
    for c in ch:
        a = c["after"]
        if a["calculation"]["inputs"]["slab_bar_end_split_v3027"]["action"] == "PARENT":
            a["evidence_state"] = "BOUNDED_EXPOSURE"
            a["bounded_range"] = {"basis": "x", "low": 1.0, "high": 2.0}
            a["rfi"] = None
            break
    with pytest.raises(ValueError, match="carries a figure"):
        A.integrate(lines, ch)


def test_outside_line_changed_refused():
    lines, out, ident, ch, _ = run()
    ch.append(A.A305._change("SLAB_BAR_END_SPLIT", "REPLACE", lines[0], dict(lines[0], physical_element="edited"),
                             evidence_status="x"))
    with pytest.raises(ValueError):
        A.integrate(lines, ch)
