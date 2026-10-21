"""UNIT_CONTROL (final BOQ V3 unit addendum): display units are a pure reporting conversion of the frozen V3a registers.

Each mutation must make the gate FAIL: kg rebar in the summary, concrete in a unit other than m³, m² + lm added,
No. added to an area, a comparison taken before unit normalisation, a summary row mixing rebar bases."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from engine.reporting_v3 import units as U

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "tests/alsenan/registers_v3"
EVAL = ROOT / "tests/alsenan/registers_v3_eval"
pytestmark = pytest.mark.skipif(not REG.exists(), reason="V3 registers not frozen yet")


def R(n, d=REG):
    return json.loads((d / f"{n}.json").read_text())


def engine_model():
    boq = R("BOQ_LINES")
    return {"lines": boq["lines"], "levels": boq["levels"], "level_names": boq["level_names"], "trades": boq["trades"],
            "master": R("MASTER_MATRIX")}


@pytest.fixture(scope="module")
def dm():
    return U.display(engine_model())


def test_frozen_model_passes_unit_control_with_the_normalised_evaluation(dm):
    uc = U.unit_control(dm, evaluation=R("BENCHMARK_EVALUATION_V3", EVAL))
    assert uc["state"] == "PASS", uc["problems"]


def test_display_is_a_pure_factor_and_the_engine_registers_are_untouched(dm):
    em = engine_model()
    before = hashlib.sha256(json.dumps(em, sort_keys=True).encode()).hexdigest()
    U.display(em)
    assert hashlib.sha256(json.dumps(em, sort_keys=True).encode()).hexdigest() == before        # input not mutated
    for a, b in zip(em["lines"], dm["lines"]):
        f = U.UNIT_POLICY[a["unit"]][1]
        assert b["engine_qty"] == a["qty"] and b["engine_unit"] == a["unit"]
        assert (a["qty"] is None and b["qty"] is None) or b["qty"] == a["qty"] * f                 # no rounding
    reb = {r["item"]: r for r in dm["master"]["rows"] if r["trade"] == "REBAR"}
    assert reb["Procurement weight incl. laps (complete sets)"]["total"] == pytest.approx(6.890619, abs=1e-9)
    assert reb["Net design weight (complete sets)"]["total"] == pytest.approx(6.246578, abs=1e-9)
    assert reb["Straight weight - sets with hooks not detailed"]["total"] == pytest.approx(6.601841, abs=1e-9)
    tot = reb[U.REBAR_TOTAL_ITEM]
    assert tot["no_total"] and tot["total"] is None and tot["status"] == "PARTIAL"
    assert sum(1 for r in reb.values() if r["basis"].startswith("OFFICIAL")) == 1


def test_unit_register_lists_every_summary_row_and_the_official_convention(dm):
    ur = U.unit_register(dm)
    assert len([x for x in ur["rows"] if not x["ITEM"].endswith("(line-level only)")]) == len(dm["master"]["rows"])
    reb = [x for x in ur["rows"] if x["ITEM"].startswith("REBAR /")]
    assert all(x["ENGINE_UNIT"] == "kg" and x["DISPLAY_UNIT"] == "t" and x["FACTOR"] == 0.001 for x in reb)
    conc = [x for x in ur["rows"] if x["ITEM"].startswith("CONCRETE /")]
    assert conc and all(x["DISPLAY_UNIT"] == "m³" for x in conc)
    assert {c["ITEM"]: c["OFFICIAL_UNIT"] for c in ur["convention"]}["REINFORCEMENT / REBAR"] == "t"
    frozen = R("UNIT_REGISTER", EVAL)
    assert frozen == json.loads(json.dumps(ur, ensure_ascii=False))


def _fails(dm, check, evaluation=None, cell_maps=()):
    uc = U.unit_control(dm, evaluation=evaluation, cell_maps=cell_maps)
    assert uc["state"] == "FAIL" and not uc["checks"][check], uc["checks"]


def test_mutation_rebar_summary_in_kg_fails(dm):
    m = copy.deepcopy(dm)
    r = next(r for r in m["master"]["rows"] if r["trade"] == "REBAR" and not r.get("no_total"))
    r["unit"] = "kg"
    _fails(m, "rebar_in_tonnes")


def test_mutation_concrete_not_in_m3_fails(dm):
    m = copy.deepcopy(dm)
    next(x for x in m["lines"] if x["trade"] == "CONCRETE")["unit"] = "m²"
    _fails(m, "concrete_in_m3")


def test_mutation_m2_and_lm_added_together_fails(dm):
    m = copy.deepcopy(dm)
    sk = next(x for x in m["lines"] if x["trade"] == "FLOORING_PORCELAIN" and x["unit"] == "lm" and x["qty"]
              and x["status"] in U.IN_TOTAL)
    sk["sumrow"] = "Floor finish"                                   # skirting lm pushed into the floor m² row
    row = next(r for r in m["master"]["rows"] if r["item"] == "Floor finish")
    row["total"] += sk["qty"]
    _fails(m, "no_cross_unit_sum")


def test_mutation_count_added_to_area_fails(dm):
    m = copy.deepcopy(dm)
    d = next(x for x in m["lines"] if x["trade"] == "ALUMINIUM_OPENINGS" and x["unit"] == "No." and x["qty"])
    d["sumrow"] = "Salon glazing"
    _fails(m, "no_cross_unit_sum")


def test_mutation_comparison_before_normalisation_fails(dm):
    ev = copy.deepcopy(R("BENCHMARK_EVALUATION_V3", EVAL))
    r = next(x for x in ev["rows"] if x["benchmark"].startswith("REBAR"))
    r["units_normalised"], r["v3_display_unit"] = False, "kg"           # kg compared with tonnes
    _fails(dm, "compare_after_normalisation", evaluation=ev)


def test_mutation_row_mixing_rebar_bases_fails(dm):
    m = copy.deepcopy(dm)
    st = next(x for x in m["lines"] if x["trade"] == "REBAR" and x["code"].endswith("-STRAIGHT") and x["qty"])
    st["sumrow"] = "Procurement weight incl. laps (complete sets)"
    row = next(r for r in m["master"]["rows"] if r["item"] == st["sumrow"])
    row["total"] += st["qty"]
    _fails(m, "single_basis_per_row")


def test_mutation_project_rebar_total_summing_bases_fails(dm):
    m = copy.deepcopy(dm)
    t = next(r for r in m["master"]["rows"] if r["item"] == U.REBAR_TOTAL_ITEM)
    t["total"] = sum(r["total"] for r in m["master"]["rows"] if r["trade"] == "REBAR" and not r.get("no_total"))
    _fails(m, "bases_never_summed")


def test_mutation_subtotal_formula_without_unit_criterion_fails(dm):
    cm = [[{"sheet": "GF", "cell": "G40", "kind": "formula", "formula": '=SUMIFS($G$5:$G$30,$J$5:$J$30,"Wall tile")'}]]
    _fails(dm, "subtotal_formulas_unit_scoped", cell_maps=cm)


def test_evaluation_normalised_every_row_and_compares_rebar_in_tonnes():
    ev = R("BENCHMARK_EVALUATION_V3", EVAL)
    assert ev["unit_policy"] == U.POLICY_ID
    for r in ev["rows"]:
        assert r["units_normalised"] and (r["difference_pct"] is None) == (r["unit_check"] != "SAME_UNIT"
                                                                          or r["v3_qty"] is None)
    reb = next(r for r in ev["rows"] if r["benchmark"].startswith("REBAR"))
    assert reb["benchmark_unit_normalised"] == reb["v3_display_unit"] == "t" and reb["v3_engine_unit"] == "kg"
    assert reb["v3_qty"] == pytest.approx(reb["v3_engine_qty"] / 1000.0)
