"""T-449 round 1: CONCRETE_BASIS_RULES_V1 on a SYNTHETIC villa (VILLA-SYNTH-03), never the training villa.

Every expected value is a hand calculation from the fixture below. Normal cases, then adverse cases: units (mm),
a declared 0.00 m level, missing / pending / superseded facts, inverted levels, run order (mirror), bad geometry.
"""

from __future__ import annotations

import pytest

from engine import project_config as pc
from engine.source import concrete_basis_rules_v1 as R


def f(fid, value, unit="m", kind="LENGTH", status="APPROVED", src="DRAWING", version=1, supersedes=None,
      conf=None):
    d = {"fact_id": fid, "version": version, "quantity_kind": kind, "value": value, "unit": unit,
         "source": {"kind": src, "reference": "synthetic sheet S-02"},
         "approval": {"status": status, "date": "2026-10-01"}, "affected_lines": ["CONC.SYNTH"],
         "confidence": conf or ("CONFIRMED" if status == "APPROVED" else "PROVISIONAL")}
    if status in ("APPROVED", "SUPERSEDED"):
        d["approval"]["by"] = "DESIGNER"
    if supersedes:
        d["supersedes"] = supersedes
    return d


def cfg(*facts):
    return pc.parse_project_config({"schema": pc.SCHEMA, "project_id": "VILLA-SYNTH-03", "config_version": "0.1.0",
                                    "facts": list(facts)})


BASIS = f("GB.BASIS.Z1", "TWO_PRINTED_LEVELS", unit="none", kind="CATEGORY")
TOP = f("LVL.TOP.Z1", 1.20)
NGL = f("LVL.NGL", 0.20)
RUNS = [R.Run("r1", 4.0, 0.25), R.Run("r2", 2.0, 0.25)]


def gb(c, runs=RUNS, basis="GB.BASIS.Z1", top="LVL.TOP.Z1", ngl="LVL.NGL"):
    return R.ground_beam_exterior(c, runs, top_level=top, outer_ground_level=ngl, depth_basis=basis)


# ---------------------------------------------------------------- ground beam, normal

def test_gb_two_printed_levels_hand_value():
    r = gb(cfg(BASIS, TOP, NGL))
    # depth 1.20 - 0.20 = 1.00; (4.0 + 2.0) x 0.25 x 1.00 = 1.500 m3
    assert r.state == R.VALUED and r.value == pytest.approx(1.5, abs=1e-9)
    assert set(r.facts_used) == {"GB.BASIS.Z1", "LVL.TOP.Z1", "LVL.NGL"}


def test_gb_millimetre_levels_give_the_same_volume():
    r = gb(cfg(BASIS, f("LVL.TOP.Z1", 1200, unit="mm"), f("LVL.NGL", 200, unit="mm")))
    assert r.state == R.VALUED and r.value == pytest.approx(1.5, abs=1e-9)


def test_gb_declared_zero_ground_level_is_a_level_not_missing():
    r = gb(cfg(BASIS, TOP, f("LVL.NGL", 0.0)))
    assert r.state == R.VALUED and r.value == pytest.approx(6.0 * 0.25 * 1.20, abs=1e-9)   # 1.800 m3


def test_gb_mirrored_run_order_same_value():
    a = gb(cfg(BASIS, TOP, NGL), runs=RUNS)
    b = gb(cfg(BASIS, TOP, NGL), runs=list(reversed(RUNS)))
    assert a.value == b.value


# ---------------------------------------------------------------- ground beam, adverse

def test_gb_missing_level_is_held_never_zero():
    r = gb(cfg(BASIS, TOP))
    assert r.state == R.HELD and r.value is None and "LVL.NGL" in r.held_reason


def test_gb_basis_not_declared_is_held():
    r = gb(cfg(TOP, NGL))
    assert r.state == R.HELD and r.value is None


def test_gb_pending_conflict_basis_reports_conflict_with_literal_reading_beside():
    pend = f("GB.BASIS.Z1", "CONFLICT", unit="none", kind="CATEGORY", status="PENDING", src="CONSULTANT_RFI")
    r = gb(cfg(pend, f("LVL.TOP.Z1", 0.45), NGL))
    # literal reading (0.45 - 0.20) x 6.0 x 0.25 = 0.375 m3: shown, never the value
    assert r.state == R.CONFLICT and r.value is None
    assert r.readings["literal_two_levels_m3"] == pytest.approx(0.375, abs=1e-9)


def test_gb_pending_other_basis_is_held_not_conflict():
    pend = f("GB.BASIS.Z1", "TWO_PRINTED_LEVELS", unit="none", kind="CATEGORY", status="PENDING",
             src="CONSULTANT_RFI")
    assert gb(cfg(pend, TOP, NGL)).state == R.HELD


def test_gb_superseded_level_only_is_held():
    old = f("LVL.NGL", 0.20, status="SUPERSEDED", conf="CONFIRMED")
    r = gb(cfg(BASIS, TOP, old))
    assert r.state == R.HELD and r.value is None


def test_gb_other_basis_value_is_held():
    r = gb(cfg(f("GB.BASIS.Z1", "INTERIOR_CLASS", unit="none", kind="CATEGORY"), TOP, NGL))
    assert r.state == R.HELD


def test_gb_inverted_levels_are_held():
    r = gb(cfg(BASIS, f("LVL.TOP.Z1", 0.10), NGL))
    assert r.state == R.HELD and r.value is None


def test_gb_level_fact_of_wrong_kind_is_held():
    r = gb(cfg(BASIS, f("LVL.TOP.Z1", 1.2, unit="m2", kind="AREA"), NGL))
    assert r.state == R.HELD


@pytest.mark.parametrize("runs", [[], [R.Run("r", 0.0, 0.25)], [R.Run("r", 3.0, -0.2)],
                                  [R.Run("r", float("nan"), 0.25)]])
def test_gb_bad_geometry_refused(runs):
    with pytest.raises(ValueError):
        gb(cfg(BASIS, TOP, NGL), runs=runs)


# ---------------------------------------------------------------- columns

def test_column_between_levels_hand_value():
    r = R.column_between_levels(cfg(f("L.B", 0.30), f("L.T", 3.90)), 0.25 * 0.40, base_level="L.B",
                                top_level="L.T")
    assert r.state == R.VALUED and r.value == pytest.approx(0.36, abs=1e-9)   # 0.10 x 3.60


def test_column_undeclared_top_is_held():
    r = R.column_between_levels(cfg(f("L.B", 0.30)), 0.1, base_level="L.B", top_level="L.ROOF")
    assert r.state == R.HELD and r.value is None and "L.ROOF" in r.held_reason


def test_column_equal_levels_held():
    r = R.column_between_levels(cfg(f("L.B", 3.0), f("L.T", 3.0)), 0.1, base_level="L.B", top_level="L.T")
    assert r.state == R.HELD


def test_section_conflict_range_and_agreement():
    same = R.column_section_conflict(0.10, 0.10, 3.0)
    assert same.state == R.VALUED and same.value == pytest.approx(0.30)
    c = R.column_section_conflict(0.10, 0.125, 3.0, designer_item="D-x")
    assert c.state == R.CONFLICT and c.value is None
    assert (c.low, c.high) == (pytest.approx(0.30), pytest.approx(0.375))
    d = R.column_section_conflict(0.125, 0.10, 3.0)   # schedule larger than drawn: still the range, never an end
    assert (d.low, d.high) == (pytest.approx(0.30), pytest.approx(0.375))
    assert d.readings == {"SCHEDULE": pytest.approx(0.375), "DRAWN": pytest.approx(0.30)}


def test_section_conflict_bad_input_refused():
    with pytest.raises(ValueError):
        R.column_section_conflict(0.0, 0.1, 3.0)


# ---------------------------------------------------------------- parapet

RUNS_P = [{"top_lo_m2": 2.0, "top_hi_m2": 2.2, "h_hi_m": 1.0}, {"top_lo_m2": 1.0, "top_hi_m2": 1.0, "h_hi_m": 0.5}]


def test_parapet_bounds_hand_values():
    r = R.parapet_rc_bounds(cfg(f("P.UP", 300, unit="mm")), RUNS_P, upstand_min="P.UP", material_item="Q-x")
    # low (2.0 + 1.0) x 0.30 = 0.90; high 2.2 x 1.0 + 1.0 x 0.5 = 2.70; the line stays HELD
    assert r.state == R.HELD and r.value is None
    assert (r.low, r.high) == (pytest.approx(0.90), pytest.approx(2.70))


def test_parapet_without_upstand_keeps_low_open():
    r = R.parapet_rc_bounds(cfg(), RUNS_P, upstand_min="P.UP", material_item="Q-x")
    assert r.state == R.HELD and r.low is None and r.high == pytest.approx(2.70)


def test_parapet_inverted_top_refused():
    with pytest.raises(ValueError):
        R.parapet_rc_bounds(cfg(f("P.UP", 0.3)), [{"top_lo_m2": 3.0, "top_hi_m2": 2.0, "h_hi_m": 1.0}],
                            upstand_min="P.UP", material_item="Q-x")


def test_module_is_an_unwired_producer_and_imports_no_research():
    src = (R.__file__ and open(R.__file__, encoding="utf-8").read())
    assert R.DEFAULT_GUARD_CLASS == "UNWIRED_PRODUCER"
    assert "research" not in "".join(l for l in src.splitlines() if l.startswith(("import", "from")))


# ---------------------------------------------------------------- neck cut (split band)

def test_split_unloaded_run_valued_at_its_printed_section():
    r = R.ground_beam_split_run(0.25, 3.0, 3.0, [0.50], loaded=False)
    assert r.state == R.VALUED and r.value == pytest.approx(0.375)          # 0.25 x 0.50 x 3.00


def test_split_loaded_run_held_with_range_never_zero():
    r = R.ground_beam_split_run(0.25, 3.0, 3.1, [0.50], loaded=True, held_depths_m=[0.50, 0.70])
    assert r.state == R.HELD and r.value is None
    assert (r.low, r.high) == (pytest.approx(0.375), pytest.approx(0.5425))   # 0.25x0.5x3.0 .. 0.25x0.7x3.1


def test_split_span_or_depth_range_is_held():
    assert R.ground_beam_split_run(0.25, 3.0, 3.2, [0.50], loaded=False).state == R.HELD
    r = R.ground_beam_split_run(0.25, 3.0, 3.0, [0.40, 0.60], loaded=False)
    assert r.state == R.HELD and (r.low, r.high) == (pytest.approx(0.30), pytest.approx(0.45))


def test_split_no_printed_section_is_blank():
    r = R.ground_beam_split_run(0.25, 0.1, 0.1, [], loaded=False)
    assert r.state == R.HELD and r.value is None and r.low is None


def test_split_conserves_band_and_refuses_lost_length():
    assert R.split_conserves_band(7.0, [3.35, 3.35], [0.30])
    assert not R.split_conserves_band(7.0, [3.35, 3.35], [])          # neck ignored: length lost
    with pytest.raises(ValueError):
        R.ground_beam_split_run(0.25, 3.2, 3.0, [0.5], loaded=False)   # span low above span high


def test_held_string_is_the_loaders_and_the_module_imports_no_engine_code():
    assert R.HELD == pc.HELD
    src = open(R.__file__, encoding="utf-8").read()
    imports = [l for l in src.splitlines() if l.startswith(("import ", "from "))]
    assert all(l.split()[1].split(".")[0] in {"__future__", "math", "dataclasses", "typing"} for l in imports), imports
