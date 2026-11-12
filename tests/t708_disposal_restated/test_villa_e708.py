"""T-708 tools on villa E708 (hand-calculated, not the development villa).

Z2 of villa E708, EG +-0.00, owner manual method: plan 100 m2 x one depth 0.60 = 60.000 m3.
  P1 50 m2 at the main underside +0.60          -> 30.000 m3, delta 0
  P2 40 m2 at a lower floor, underside +0.20    ->  8.000 m3, delta 40 x (0.20 - 0.60) = -16.000
  P3 10 m2 split level, underside +0.20 .. +0.60 -> 2.000 .. 6.000, delta -4.000 .. 0
  G1 beam column outside the owner plan          -> +0.500 (owner 0)
  G2 blinding projections in panel fill          -> -0.040 (owner 0)
  engine 40.460 .. 44.460 = 60.000 - 19.540 .. - 15.540; residual 0.

Balance of villa E708 (in situ / compacted m3): L-E1 VALUE 100 [DC], L-E2 RANGE 10 .. 20 [ESTIMATED], L-E3 AT_LEAST
30 (beside), L-F1 RANGE 50 .. 60 [PV], L-F2 ZERO_BY_GEOMETRY, L-F3 BLANK, a NEW split row (no id).
  E closed 110 .. 120 (open: L-E3), D closed 50 .. 60 (open: L-F3).
  s = 0: disposal at least 120.000, import at least 60.000; s = 1 ends HELD (densities, geotech, losses).
  break-even k* = 110 / 60 = 1.833333 .. 120 / 50 = 2.400000 (indicator only).
  dry mass: 100 m3 in situ x rho_insitu 1.80 t/m3 MEASURED = 180.000 t; without the density: an expression, HELD.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t708"))
import balance_restate as R  # noqa: E402

B = R.B


def z2_terms():
    return [
        {"id": "P1", "kind": "PANEL", "area_m2": 50.0, "fill_m3": [30.0, 30.0], "cause": "main underside +0.60"},
        {"id": "P2", "kind": "PANEL", "area_m2": 40.0, "fill_m3": [8.0, 8.0], "cause": "lower floor +0.20"},
        {"id": "P3", "kind": "PANEL", "area_m2": 10.0, "fill_m3": [2.0, 6.0], "cause": "split level, not printed"},
        {"id": "G1", "kind": "OUTSIDE_PLAN", "fill_m3": [0.5, 0.5], "cause": "fill under an interior beam"},
        {"id": "G2", "kind": "OUTSIDE_PLAN", "fill_m3": [-0.04, -0.04], "cause": "blinding projections"},
    ]


# ------------------------------------------------------------------------------------ (a) reconciliation ----

def test_owner_plan_x_depth_reconciles_term_by_term():
    r = R.reconcile_plan_x_depth(z2_terms(), 0.60, owner_plan_m2=100.0, zone_ends=[40.46, 44.46])
    assert r["owner_m3"] == 60.0
    lo, hi = r["ends"]["low"], r["ends"]["high"]
    assert lo["engine_m3"] == 40.46 and hi["engine_m3"] == 44.46
    assert lo["difference_engine_minus_owner_m3"] == -19.54 and hi["difference_engine_minus_owner_m3"] == -15.54
    d = {t["id"]: t["delta_m3"] for t in r["terms"]}
    assert d == {"P1": [0.0, 0.0], "P2": [-16.0, -16.0], "P3": [-4.0, 0.0], "G1": [0.5, 0.5], "G2": [-0.04, -0.04]}
    assert lo["residual_m3"] == 0.0 and hi["residual_m3"] == 0.0


def test_rotation_mirror_or_order_do_not_enter():
    a = R.reconcile_plan_x_depth(z2_terms(), 0.60, owner_plan_m2=100.0)
    b = R.reconcile_plan_x_depth(list(reversed(z2_terms())), 0.60, owner_plan_m2=100.0)
    assert a["ends"] == b["ends"]


def test_plan_difference_is_a_cause_not_a_residual():
    with pytest.raises(R.RestateError, match="plan difference"):
        R.reconcile_plan_x_depth(z2_terms(), 0.60, owner_plan_m2=104.0)


def test_unexplained_published_difference_refused():
    with pytest.raises(R.RestateError, match="unexplained"):
        R.reconcile_plan_x_depth(z2_terms(), 0.60, zone_ends=[40.46, 44.96])


def test_held_term_cannot_be_reconciled_and_never_becomes_zero():
    t = z2_terms()
    t[2]["fill_m3"] = [None, None]
    with pytest.raises(R.RestateError, match="HELD"):
        R.reconcile_plan_x_depth(t, 0.60)


def test_millimetre_depth_and_missing_cause_refused():
    with pytest.raises(R.RestateError, match="mm"):
        R.reconcile_plan_x_depth(z2_terms(), 600.0)
    t = z2_terms()
    t[3]["cause"] = ""
    with pytest.raises(R.RestateError, match="cause"):
        R.reconcile_plan_x_depth(t, 0.60)
    t = z2_terms()
    t[1]["id"] = "P1"
    with pytest.raises(R.RestateError, match="twice"):
        R.reconcile_plan_x_depth(t, 0.60)


# ------------------------------------------------------------------------------------------- (b) restating ----

CAND = {"L-E1": "EW:B1-02:E1", "L-E2": "EW:B1-02:E2", "L-E3": "EW:B1-02:E3", "L-F1": "EW:B1-03:F1",
        "L-F2": "EW:B1-03:F2", "L-F3": "EW:B1-03:F3"}
ROLES = {k: (B.EXC if ":B1-02:" in v else B.FILL) for k, v in CAND.items()}
STATUS = {"L-E1": B.DC, "L-E2": B.EST, "L-F1": B.PV + " 3 / 4"}


def row(lid, bound, value=None, low=None, high=None, el=None, missing="x"):
    return {"line_id": lid, "element_id": el or CAND.get(lid, "EW:B1-03:F9"), "bound": bound, "value_m3": value,
            "low_m3": low, "high_m3": high, "basis": "proof" if bound == "ZERO_BY_GEOMETRY" else "b",
            "missing_input": missing}


def form():
    return [row("L-E1", "VALUE", 100.0, missing=""), row("L-E2", "RANGE", low=10.0, high=20.0),
            row("L-E3", "AT_LEAST", low=30.0), row("L-F1", "RANGE", low=50.0, high=60.0),
            row("L-F2", "ZERO_BY_GEOMETRY", 0.0, missing=""), row("L-F3", "BLANK"),
            row("NEW (split of L-F3)", "RANGE", low=1.0, high=2.0, el="EW:B1-03:F3S"),
            row("L-D0", "BLANK", el="EW:B1-04:ALL")]


def held_balance(T):
    return B.balance(T, rho_insitu=B.density(None, B.HELD, kind="INSITU"),
                     rho_target=B.density(None, B.HELD, kind="PLACEMENT_TARGET"), suit=B.suitability(),
                     loss_reuse=B.loss(B.REUSE), loss_import=B.loss(B.IMPORT), bulk=B.bulking())


def test_restated_balance_s0_ends_and_beside():
    T, beside = R.restate_terms(form(), CAND, ROLES, STATUS)
    res = held_balance(T)
    assert (res["excavation"]["low"], res["excavation"]["high"], res["excavation"]["open"]) == (110.0, 120.0, True)
    assert (res["fill_demand"]["low"], res["fill_demand"]["high"], res["fill_demand"]["open"]) == (50.0, 60.0, True)
    dh, ih = res["disposal_insitu_m3"]["high"], res["import_compacted_m3"]["high"]
    assert (dh["value"], dh["qualifier"]) == (120.0, "AT_LEAST")
    assert (ih["value"], ih["qualifier"]) == (60.0, "AT_LEAST")
    assert res["disposal_insitu_m3"]["low"]["value"] is None          # s = 1: densities / geotech / loss HELD
    assert [a["at_least_m3"] for a in beside["at_least"]] == [30.0]   # beside, never summed
    assert [a["line_id"] for a in beside["not_entered"]] == ["NEW (split of L-F3)"]
    z = next(t for t in T if t["line_id"] == "L-F2")
    assert (z["low"], z["high"], z["status"]) == (0.0, 0.0, B.CALC)


def test_break_even_yield_indicator():
    T, _ = R.restate_terms(form(), CAND, ROLES, STATUS)
    k = R.break_even_yield(held_balance(T))
    assert k["k_star"] == [1.833333, 2.4] and k["open_excavation_lines"] == 1 and k["open_fill_lines"] == 1


def test_term_diff_names_every_changed_line():
    before = [B.term(l, ROLES[l], status=B.HELD, zone=CAND[l]) for l in CAND]
    after, _ = R.restate_terms(form(), CAND, ROLES, STATUS)
    d = {x["line_id"] for x in R.term_diff(before, after)}
    assert d == {"L-E1", "L-E2", "L-F1", "L-F2"}                     # AT_LEAST and BLANK stay blank


def test_line_missing_from_the_form_refused():
    with pytest.raises(R.RestateError, match="missing from the form"):
        R.restate_terms(form()[1:], CAND, ROLES, STATUS)


def test_closed_term_without_a_source_status_refused():
    st = dict(STATUS)
    st.pop("L-E2")
    with pytest.raises(R.RestateError, match="non-HELD source status"):
        R.restate_terms(form(), CAND, ROLES, st)
    st["L-E2"] = B.HELD
    with pytest.raises(R.RestateError, match="non-HELD source status"):
        R.restate_terms(form(), CAND, ROLES, st)


def test_element_mismatch_and_twice_refused():
    f = form()
    f[0] = dict(f[0], element_id="EW:B1-02:OTHER")
    with pytest.raises(R.RestateError, match="form element"):
        R.restate_terms(f, CAND, ROLES, STATUS)
    with pytest.raises(R.RestateError, match="twice"):
        R.restate_terms(form() + [form()[0]], CAND, ROLES, STATUS)


def test_unsourced_zero_refused():
    f = form()
    f[4] = dict(f[4], basis="")
    with pytest.raises(R.RestateError, match="calculated 0"):
        R.restate_terms(f, CAND, ROLES, STATUS)


# ------------------------------------------------------------------------------------- (c) dry-mass inputs ----

def test_dry_mass_with_a_measured_density():
    z = [{"zone": "E1", "line_id": "L-E1", "role": B.EXC, "low_m3": 100.0, "high_m3": 100.0, "bound": "VALUE"}]
    r = R.dry_mass_inputs(z, {"INSITU": B.density(1.80, B.MEAS, source="field density test", kind="INSITU")})
    assert r[0]["dry_t"] == [180.0, 180.0] and r[0]["state"] == "VALUED"


def test_missing_density_never_becomes_a_mass_or_zero():
    z = [{"zone": "F1", "line_id": "L-F1", "role": B.FILL, "low_m3": 50.0, "high_m3": 60.0, "bound": "RANGE"},
         {"zone": "F3", "line_id": "L-F3", "role": B.FILL, "low_m3": None, "high_m3": None, "bound": "BLANK"},
         {"zone": "E3", "line_id": "L-E3", "role": B.EXC, "low_m3": 30.0, "high_m3": None, "bound": "AT_LEAST"}]
    r = R.dry_mass_inputs(z)
    assert all(x["dry_t"] is None and x["state"] == "HELD" for x in r)
    assert r[0]["expression"] == "50.000000 .. 60.000000 m3 x rho_placement_target t/m3"
    assert r[2]["expression"] == "30.000000 (at least) m3 x rho_insitu t/m3"
    assert "the zone volume (HELD)" in r[1]["missing"]


def test_wrong_density_kind_and_unit_refused():
    z = [{"zone": "E1", "line_id": "L-E1", "role": B.EXC, "low_m3": 100.0, "high_m3": 100.0, "bound": "VALUE"}]
    with pytest.raises(R.RestateError, match="density"):
        R.dry_mass_inputs(z, {"INSITU": B.density(1.9, B.SPEC, source="spec", kind="PLACEMENT_TARGET")})
    with pytest.raises(B.Refused):
        B.density(1800, B.MEAS, source="test", kind="INSITU")          # kg/m3 passed as t/m3
