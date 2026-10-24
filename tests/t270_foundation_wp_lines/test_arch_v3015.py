"""T-270: ARCH_TAKEOFF_V3.0.15 foundation waterproofing line family on a hand-calculated villa that is not the
development villa (P-270), plus the development villa's inputs pinned to the Checker's own figures.

Villa P-270 (printed footing detail: 5 cm screed / 2 cm membrane / 10 cm plain concrete, membrane and screed end at the
footing faces, the blinding projects 0.10 each side):
  FA x2  1.20 x 1.00 = 1.200 each (blinding 1.40 x 1.20 = 1.680)
  FB     2.00 x 1.50 = 3.000      (blinding 2.20 x 1.70 = 3.740)
  FC     1.00 x 1.00 less a 0.30 x 0.20 notch = 0.940 (blinding 1.380)
  FD     one outline with two schedule tags: HELD (readings 1.50 / 1.62 in the scenario file only)
  membrane = screed plan = 1.200 + 1.200 + 3.000 + 0.940 = 6.340 m2; screed 6.340 x 0.05 = 0.317 m3
  footing sides HELD on the detail selection (readings 7.00 liquid / 8.20 sheet, scenario only)
Lift pit: base 3.00 x 3.00 = 9.000, H 0.50, screed 0.05, pit envelope 1.80 x 1.80 = 3.240:
  membrane 9.000 + 12.00 x 0.55 = 6.600 + (9.000 - 3.240) 5.760 = 21.360 m2; board 6.600 + 5.760 = 12.360 m2;
  screed 9.000 m2 / 0.450 m3; walls HELD (12.00 m2 per m of pit depth, scenario only)
Buried liquid coating: interior run 2 x (0.40 - 0.10) x 4.00 = 2.400 + exterior inner face 0.85 x 3.00 = 2.550
  = 4.950 m2 DRAWING-CONFIRMED (2.550 own-checked: PARTIALLY VERIFIED); footing tops HELD; procurement HELD.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

from engine.source import arch_v30 as A30
from engine.source import arch_v3015 as A
from engine.source import boq_line as BL

ROOT = Path(__file__).resolve().parents[2]
PID, REV = "P-270", "7" * 64
SRC = {"file": "research/fx/FOUNDATION_WP_FX.csv", "sha256": "1" * 64, "task": "T-FXW", "merge_commit": "fx27001",
       "checker_run": "Verifier fixture W"}
SRC2 = {"file": "research/fx/BURIED_FX.csv", "sha256": "2" * 64, "task": "T-FXB", "merge_commit": "fx27002",
        "checker_run": "Verifier fixture B"}
FM, FS, SIDES = "WP.FOUNDATION.FOOTING_MEMBRANE", "WP.FOUNDATION.FOOTING_SCREED", "WP.FOUNDATION.FOOTING_SIDES"
PM, PB, PS = "WP.FOUNDATION.LIFT_PIT_MEMBRANE", "WP.FOUNDATION.LIFT_PIT_BOARD", "WP.FOUNDATION.LIFT_PIT_SCREED"
BUR, PROC = "WP.FOUNDATION.BURIED_LIQUID", "WP.FOUNDATION.PROCUREMENT"
OUTLINES = [("FA1", 1.2, 1.68), ("FA2", 1.2, 1.68), ("FB", 3.0, 3.74), ("FC", 0.94, 1.38)]


def candidate():
    """a V3.0.14-like candidate: footing concrete, blinding (CONCRETE) and one finish line."""
    mk = dict(project_id=PID, revision_set_sha256=REV, documents=[], rule_id="FX", rule_version="1",
              evidence_state="SOURCE_DERIVED", floor="FOUNDATION", formula="fixture")
    return [BL.make_line(item_code="STR.CONC.FOOTING", unit="m3", measured_net=2.4, element_id="FTG:ALL", **mk),
            BL.make_line(item_code="STR.CONC.BLINDING", unit="m3", measured_net=0.848, element_id="BLD:ALL", **mk),
            BL.make_line(item_code="FIN.WP.FLOOR", unit="m2", measured_net=12.0, element_id="WET:1",
                         **dict(mk, floor="GF"))]


def comps(unit="m2"):
    out = []
    for oid, a, b in OUTLINES:
        v = a if unit == "m2" else round(a * 0.05, 6)
        out.append({"id": oid, "value": v, "extent": "FOOTING_OUTLINE", "outline_m2": a, "blinding_m2": b})
    return out


def records():
    held_fd = ["FD carries two schedule tags: never one picked"]
    return [
        {"id": "M", "item_code": FM, "unit": "m2", "state": "RELEASED", "task": "T-FXW", "floor": "FOUNDATION",
         "element": "UNDERLAY", "value": 6.34, "components": comps(), "verified_by": "Verifier fixture W",
         "verified_components": "ALL"},
        {"id": "M-FD", "item_code": FM, "unit": "m2", "state": "HELD", "task": "T-FXW", "floor": "FOUNDATION",
         "element": "UNDERLAY_FD", "reasons": held_fd, "scenario": {"readings": {"outline": 1.5, "rows": 1.62}}},
        {"id": "S2", "item_code": FS, "unit": "m2", "state": "RELEASED", "task": "T-FXW", "floor": "FOUNDATION",
         "element": "SCREED", "value": 6.34, "components": comps(), "verified_by": "Verifier fixture W",
         "verified_components": "ALL"},
        {"id": "S3", "item_code": FS, "unit": "m3", "state": "RELEASED", "task": "T-FXW", "floor": "FOUNDATION",
         "element": "SCREED", "value": 0.317, "components": comps("m3"), "verified_by": "Verifier fixture W",
         "verified_components": "ALL"},
        {"id": "SIDES", "item_code": SIDES, "unit": "m2", "state": "HELD", "task": "T-FXW", "floor": "FOUNDATION",
         "element": "SIDES", "reasons": ["detail not selected (founding level)"],
         "scenario": {"readings": {"liquid": 7.0, "sheet": 8.2}}},
        {"id": "PM", "item_code": PM, "unit": "m2", "state": "RELEASED", "task": "T-FXW", "floor": "FOUNDATION",
         "element": "PIT_MEMBRANE", "value": 21.36,
         "components": [{"id": "soffit", "value": 9.0}, {"id": "sides", "value": 6.6}, {"id": "top", "value": 5.76}],
         "verified_by": "Verifier fixture W", "verified_components": "ALL"},
        {"id": "PM-W", "item_code": PM, "unit": "m2", "state": "HELD", "task": "T-FXW", "floor": "FOUNDATION",
         "element": "PIT_MEMBRANE_WALLS", "reasons": ["pit depth not printed"],
         "scenario": {"readings": {"per_m_height": 12.0}}},
        {"id": "PB", "item_code": PB, "unit": "m2", "state": "RELEASED", "task": "T-FXW", "floor": "FOUNDATION",
         "element": "PIT_BOARD", "value": 12.36,
         "components": [{"id": "sides", "value": 6.6}, {"id": "top", "value": 5.76}]},
        {"id": "PS2", "item_code": PS, "unit": "m2", "state": "RELEASED", "task": "T-FXW", "floor": "FOUNDATION",
         "element": "PIT_SCREED", "value": 9.0, "components": [{"id": "base", "value": 9.0}]},
        {"id": "PS3", "item_code": PS, "unit": "m3", "state": "RELEASED", "task": "T-FXW", "floor": "FOUNDATION",
         "element": "PIT_SCREED", "value": 0.45, "components": [{"id": "base", "value": 0.45}]},
        {"id": "B", "item_code": BUR, "unit": "m2", "state": "RELEASED", "task": "T-FXB", "floor": "FOUNDATION",
         "element": "GB_FACES", "value": 4.95,
         "components": [{"id": "R1 A", "value": 1.2}, {"id": "R1 B", "value": 1.2}, {"id": "R2 inner", "value": 2.55}],
         "partial_check": {"m2_or_unit": 2.55, "run": "Verifier fixture B"}},
        {"id": "B-TOPS", "item_code": BUR, "unit": "m2", "state": "HELD", "task": "T-FXB", "floor": "FOUNDATION",
         "element": "TOPS", "reasons": ["detail selection"]},
        {"id": "P", "item_code": PROC, "unit": "item", "state": "HELD", "task": "T-FXW", "floor": "FOUNDATION",
         "element": "PROCUREMENT", "reasons": ["product not printed"]},
    ]


DECLARED = {f"{FM} m2": {"released": 6.34, "held_lines": 1}, f"{FS} m2": {"released": 6.34, "held_lines": 0},
            f"{FS} m3": {"released": 0.317, "held_lines": 0}, f"{SIDES} m2": {"released": 0.0, "held_lines": 1},
            f"{PM} m2": {"released": 21.36, "held_lines": 1}, f"{PB} m2": {"released": 12.36, "held_lines": 0},
            f"{PS} m2": {"released": 9.0, "held_lines": 0}, f"{PS} m3": {"released": 0.45, "held_lines": 0},
            f"{BUR} m2": {"released": 4.95, "held_lines": 1}, f"{PROC} item": {"released": 0.0, "held_lines": 1}}


def inputs(recs=None, declared=None, **pc_kw):
    pc = {"piece": "FOUNDATION_WP", "source": SRC, "sources": [SRC2],
          "chain": {"screed_t": 0.05, "membrane_extent": "FOOTING_OUTLINE"},
          "blinding": {"item_codes": ["STR.CONC.BLINDING"]}, "records": records() if recs is None else recs,
          "declared_totals": DECLARED if declared is None else declared}
    pc.update(pc_kw)
    return {"schema": A.INPUTS_SCHEMA, "project": PID, "pieces": [pc]}


def run(inp=None, lines=None):
    lines = candidate() if lines is None else lines
    inp = A.load_inputs(inputs() if inp is None else inp, PID)
    ch, logs = A.changes_for(inp, lines)
    out, ident = A.integrate(lines, ch)
    return lines, ch, logs, out, ident


def _one(lines, code, unit, state):
    hit = [ln for ln in lines if ln["item_code"] == code and ln["unit"] == unit and ln["evidence_state"] == state]
    assert len(hit) == 1, (code, unit, state, len(hit))
    return hit[0]


# ================================================================================================ normal
def test_family_totals_equal_the_hand_calculation():
    _l, ch, logs, out, ident = run()
    assert ident["added"] == 13 and ident["replaced"] == 0 and ident["outside_rows_identical_to_v3_0_14"] == 3
    fam = ident["family"]
    assert fam[f"{FM} m2"] == {"released": 6.34, "lines": 2, "held_lines": 1}
    assert fam[f"{FS} m3"]["released"] == 0.317 and fam[f"{PM} m2"]["released"] == 21.36
    assert fam[f"{PB} m2"]["released"] == 12.36 and fam[f"{PS} m3"]["released"] == 0.45
    assert fam[f"{BUR} m2"] == {"released": 4.95, "lines": 2, "held_lines": 1}
    assert logs[0]["evidence_status"] == {"VERIFIED": 4, "HELD": 5, "DRAWING-CONFIRMED": 4}
    assert logs[1]["state"] == "NO_PROJECT_INPUT"


def test_membrane_is_on_the_footing_outline_not_the_blinding():
    *_, out, _ = run()
    m = _one(out, FM, "m2", "SOURCE_DERIVED")
    assert m["measured_net"] == 6.34 and m["trade"] == "WATERPROOFING" and m["location"]["floor"] == "FOUNDATION"
    blind = sum(b for _i, _a, b in OUTLINES)
    assert abs(m["measured_net"] - blind) > 1.0          # 6.34 vs the blinding plan 8.48
    assert _one(out, FS, "m3", "SOURCE_DERIVED")["measured_net"] == 0.317


def test_blinding_and_every_other_line_byte_identical():
    lines, _ch, _logs, out, ident = run()
    by = {ln["line_id"]: ln for ln in out}
    for ln in lines:
        assert A30.line_sha(by[ln["line_id"]]) == A30.line_sha(ln)
    assert ident["blinding_lines_identical"] == 1


def test_held_lines_are_blank_never_zero_and_readings_only_in_the_scenario(tmp_path):
    lines, ch, logs, out, _ = run()
    held = [ln for ln in out if ln["item_code"] in A.ITEMS and ln["evidence_state"] == "BLOCKED_RFI"]
    assert len(held) == 5
    for ln in held:
        assert ln["measured_net"] is None and ln["bounded_range"] is None and ln["rfi"]["question"]
        assert "readings" not in json.dumps(ln["calculation"])
    names, ident, led = A.write(tmp_path, lines, ch, logs, A.load_inputs(inputs(), PID), released_lines=[])
    sc = json.loads((tmp_path / "V3_0_15_SCENARIOS.json").read_text(encoding="utf-8"))["scenarios"]
    assert {s["id"]: s["readings"] for s in sc} == {"M-FD": {"outline": 1.5, "rows": 1.62},
                                                    "SIDES": {"liquid": 7.0, "sheet": 8.2},
                                                    "PM-W": {"per_m_height": 12.0}}
    assert "V3_0_15_DIFF.csv" in names and led["integration_package"] is True
    diff = (tmp_path / "V3_0_15_DIFF.csv").read_text(encoding="utf-8")
    assert diff.count("ADDED") == 13 and diff.count(",SAME,") == 3
    assert all(r["release_status"] == "NOT RELEASED" for r in led["rows"])


def test_partial_check_is_named_never_promoted():
    *_, out, _ = run()
    b = _one(out, BUR, "m2", "SOURCE_DERIVED")
    w = b["calculation"]["inputs"]["foundation_wp_v3015"]
    assert w["verified_by"] is None and w["partial_check"]["m2_or_unit"] == 2.55
    _l, ch, *_ = run()
    st = {c["after"]["line_id"]: c["evidence_status"] for c in ch}
    assert st[b["line_id"]] == "DRAWING-CONFIRMED"


def test_component_order_does_not_change_the_lines():
    recs = records()
    recs[0]["components"] = list(reversed(recs[0]["components"]))
    a = {ln["line_id"]: ln["measured_net"] for ln in run()[3]}
    b = {ln["line_id"]: ln["measured_net"] for ln in run(inputs(recs))[3]}
    assert a == b


# ================================================================================================ adverse
def _bad(mutate, match, declared=None, **kw):
    recs = records()
    mutate(recs)
    with pytest.raises((A.InputsError, ValueError), match=match):
        run(inputs(recs, declared=declared, **kw))


def test_adverse_membrane_on_the_blinding_area_is_refused():
    def m(r):
        r[0]["components"][2]["value"] = 3.74
        r[0]["value"] = round(6.34 - 3.0 + 3.74, 6)
    _bad(m, "BLINDING outline")


def test_adverse_blinding_extent_is_refused():
    _bad(lambda r: r[0]["components"][0].update(extent="BLINDING_OUTLINE"), "extent")


def test_adverse_held_written_as_zero_is_refused():
    _bad(lambda r: r[1].update(value=0.0), "BLANK")


def test_adverse_range_inside_the_boq_is_refused():
    _bad(lambda r: r[4].update(low=7.0, high=8.2), "BLANK")


def test_adverse_scenario_reading_zero_is_refused():
    _bad(lambda r: r[4]["scenario"]["readings"].update(liquid=0.0), "reading")


def test_adverse_component_sum_mismatch_is_refused():
    _bad(lambda r: r[5].update(value=21.0), "sum of its components")


def test_adverse_screed_m3_not_outline_x_printed_thickness_is_refused():
    def m(r):
        r[3]["components"][0]["value"] = 0.12        # 1.20 x 0.10: the blinding thickness, not the screed
        r[3]["value"] = round(0.317 - 0.06 + 0.12, 6)
    _bad(m, "printed")


def test_adverse_millimetres_as_metres_is_refused():
    def m(r):
        r[3]["components"][0]["value"] = 60.0        # 1.20 x 50 (mm)
        r[3]["value"] = round(0.317 - 0.06 + 60.0, 6)
    _bad(m, "printed")


def test_adverse_component_counted_twice_is_refused():
    def m(r):
        r[0]["components"].append(dict(r[0]["components"][0]))
        r[0]["value"] = round(6.34 + 1.2, 6)
    _bad(m, "twice")


def test_adverse_verified_without_every_component_is_refused():
    _bad(lambda r: r[0].update(verified_components="SOME"), "every component")


def test_adverse_released_procurement_is_refused():
    def m(r):
        r[-1].update(state="RELEASED", value=3.0, components=[{"id": "rolls", "value": 3.0}])
        r[-1].pop("reasons")
    _bad(m, "printed product")


def test_adverse_unknown_task_is_refused():
    _bad(lambda r: r[0].update(task="T-NOPE"), "merged sources")


def test_adverse_declared_total_mismatch_is_refused():
    d = copy.deepcopy(DECLARED)
    d[f"{FM} m2"]["released"] = 6.0
    with pytest.raises(ValueError, match="declared"):
        run(inputs(declared=d))


def test_adverse_family_already_in_the_candidate_is_refused():
    lines = candidate()
    lines.append(BL.make_line(project_id=PID, revision_set_sha256=REV, documents=[], rule_id="FX", rule_version="1",
                              evidence_state="SOURCE_DERIVED", floor="FOUNDATION", formula="fx", item_code=FM,
                              unit="m2", measured_net=6.34, element_id="X", item_en="x", item_ar="x",
                              trade="WATERPROOFING"))
    with pytest.raises(A.InputsError, match="already carries"):
        run(lines=lines)


def test_adverse_candidate_without_its_blinding_is_refused():
    with pytest.raises(A.InputsError, match="no blinding line"):
        run(lines=[ln for ln in candidate() if ln["item_code"] != "STR.CONC.BLINDING"])


def test_adverse_a_change_that_replaces_the_blinding_is_refused():
    lines, ch, *_ = run()
    b = [ln for ln in lines if ln["item_code"] == "STR.CONC.BLINDING"][0]
    after = copy.deepcopy(b)
    after["measured_net"] = 0.5
    bad = ch + [{"piece": "FOUNDATION_WP", "action": "REPLACE", "before": b, "after": after}]
    with pytest.raises(ValueError, match="ADDED"):
        A.integrate(lines, bad)


def test_adverse_a_held_line_with_a_figure_in_the_boq_is_refused():
    *_, out, _ = run()
    out = copy.deepcopy(out)
    h = [ln for ln in out if ln["item_code"] == SIDES][0]
    h["bounded_range"] = {"low": 7.0, "high": 8.2}
    with pytest.raises(ValueError, match="carries a figure"):
        A.check_family(out)


# ================================================================================================ development villa
def test_development_villa_inputs_pinned_to_the_checker_figures():
    sys.path.insert(0, str(ROOT / "research" / "agents_t270"))
    import t270_inputs as T
    doc = A.load_inputs(T.inputs("DEV"), "DEV")
    pc = doc["pieces"][0]
    dec = pc["declared_totals"]
    for k, v in T.CHECKER_FIGURES.items():
        assert dec[k]["released"] == pytest.approx(v, abs=1e-6), k
    assert dec["WP.FOUNDATION.FOOTING_MEMBRANE m2"] == {"released": 109.85, "held_lines": 1}
    assert dec["WP.FOUNDATION.BURIED_LIQUID m2"]["held_lines"] == 4
    assert len(pc["records"]) == 19
    fm = [r for r in pc["records"] if r["id"] == "FTG-MEMBRANE"][0]
    assert len(fm["components"]) == 24
    assert sum(c["blinding_m2"] for c in fm["components"]) > 109.85 + 10   # the blinding plan is larger: not used
    sides = [r for r in pc["records"] if r["id"] == "FTG-SIDES"][0]
    assert sides["scenario"]["readings"] == {"single_liquid_P_x_H": 80.037171,
                                             "double_sheet_P_x_H_plus_0_07": 93.033788}
    bur = [r for r in pc["records"] if r["id"] == "BURIED-GB"][0]
    assert bur["verified_by"] is None and bur["partial_check"]["m2_or_unit"] == 5.3825 and len(bur["components"]) == 21


def test_every_added_line_carries_its_guard_element():
    # the guard re-check (arch_v307.guard_changes) maps each added line to a drawn element: refused without it (the
    # development-villa run failed on exactly this before the fix)
    _l, ch, *_ = run()
    adds = [c for c in ch if c["action"] == "ADD"]
    assert adds and all(c["guard_element"] == {"element_id": c["after"]["location"]["element_id"], "part": "WHOLE"}
                        for c in adds)
    from engine.source import arch_v307 as A307
    m = A307._carried_map([], adds)
    assert set(m) == {c["after"]["line_id"] for c in adds}
