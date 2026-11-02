"""T-449 round 2: the reinforcement correction register over the merged project inputs (public research files only).

The register imports the merged input builders (each pins its own ledgers by sha256) and the declared facts; it needs
no private drawing. Checks: the committed output is what the register builds; every released reinforcement line is
reproduced by the generic rule per line and per bar population within +-0.5 % in t; the declared facts' affected lines
are exactly the lines the register uses them for; held stays held; the census leaves no reinforcement input unclassed;
an adverse fact (another unit-mass method) breaks the reproduction instead of being absorbed.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from engine import project_config as pc

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/agents_t449/round2"


@pytest.fixture(scope="module")
def M():
    spec = importlib.util.spec_from_file_location("t449_rebar_register_test", HERE / "t449_rebar_register.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def reg(M):
    return M.build()


def test_committed_register_is_the_build(reg, M):
    committed = json.loads((HERE / "out/CORRECTION_REGISTER_REBAR_T449.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(reg, sort_keys=True)) == committed
    assert (HERE / "out/CORRECTION_REGISTER_REBAR_T449.csv").read_text(encoding="utf-8") == M.to_csv(reg)


def test_every_released_line_reproduced(reg):
    rel = [e for e in reg["entries"] if e["version"] == "ARCH_TAKEOFF_V3.0.3" and e["action"] == "RELEASED"]
    assert len(rel) == 350 and all(e["class"] == "A-REPRODUCED" for e in rel)
    assert all(e["line_id"] for e in rel), "every released record maps to its candidate line id"
    for e in rel:
        assert abs(e["rule_result"]["value"] - e["patch"]["line_net"]) <= e["tol_kg"]
    r = reg["released"]
    assert r["ledger_kg"] == pytest.approx(8311.066, abs=1e-6) and r["line_net_kg"] == pytest.approx(8311.066, abs=1e-6)
    assert abs(r["rule_kg"] - r["ledger_kg"]) < 0.01            # 350 x the 3 dp print, named residual
    assert r["populations"] == r["populations_within_0_5_pct"] > 0


def test_every_v3024_rebar_formula_fix_maps_to_a_reproduced_record(reg):
    fx = [e for e in reg["entries"] if e["version"] == "ARCH_TAKEOFF_V3.0.24" and e["action"] == "REBAR_FORMULA"]
    assert len(fx) == 350 and all(e["ledger_entry_class"] == "A-REPRODUCED" for e in fx)


def test_slab_lines_reproduced_or_named(reg):
    sl = [e for e in reg["entries"] if e["version"] == "ARCH_TAKEOFF_V3.0.27"]
    assert len(sl) == 196
    bad = [e for e in sl if e["class"] != "A-REPRODUCED"]
    assert len(bad) == 3 and all(e["rule_pending"]["rule"].startswith("R-SLAB-BAR-END-1 + R-LABEL") for e in bad)
    sup = [e for e in reg["entries"] if e["class"] == "SUPERSEDED"]
    assert len(sup) == 196 and {e["line_id"] for e in sup} == {e["line_id"] for e in sl}


def test_every_specified_entry_names_its_rule(reg):
    sp = [e for e in reg["entries"] if e["class"] == "A-SPECIFIED"]
    assert sp and all(not e["rule_pending"]["why"].startswith("not classified") for e in sp)


def test_no_class_c_and_held_stays_held(reg):
    assert "C" not in reg["counts"]
    for e in reg["entries"]:
        rr = e.get("rule_result") or {}
        if e["class"] == "A-REPRODUCED" and rr.get("state") != "VALUED":
            assert rr.get("value") is None, e["element_id"]


def test_census_classes_every_reinforcement_input(reg):
    for c in reg["census"]:
        if c["rebar_words"]:
            assert c["reach"] in ("REACHES", "TEXT_ONLY") and c["why"]
    reaches = {c["version"] for c in reg["census"] if c["reach"] == "REACHES"}
    assert reaches == {"ARCH_TAKEOFF_V3.0.2", "ARCH_TAKEOFF_V3.0.3", "ARCH_TAKEOFF_V3.0.5", "ARCH_TAKEOFF_V3.0.24",
                       "ARCH_TAKEOFF_V3.0.27"}
    assert len(reg["census"]) == 40          # V3.0.2 .. V3.0.42 less V3.0.4 (its inputs come from the T-167 run)


def test_declared_facts_load_and_affect_exactly_their_usage(reg):
    cfg = pc.load_project_config(HERE / "DEVELOPMENT-VILLA-T131.rebar_facts.json")
    assert {f.fact_id: sorted(f.affected_lines) for f in cfg.active_facts()} == reg["fact_usage"]
    assert cfg.lookup("REBAR.SLAB.BAR_END.CLEAR_COVER").status == pc.DRAWING_CONFIRMED
    assert cfg.lookup("REBAR.UNIT_MASS.METHOD").status == pc.ASSUMED_OWNER_APPROVED
    for absent in ("REBAR.LAP.COLUMN_D", "REBAR.LINK.FIRST_OFFSET"):
        assert not cfg.lookup(absent).usable          # not declared: moves no line of this villa


def test_adverse_other_unit_mass_method_breaks_the_reproduction(M):
    data = json.loads((HERE / "DEVELOPMENT-VILLA-T131.rebar_facts.json").read_text(encoding="utf-8"))
    for fct in data["facts"]:
        if fct["fact_id"] == "REBAR.UNIT_MASS.METHOD":
            fct["value"] = "D2_OVER_162_16"
    bad = M.build(cfg=pc.parse_project_config(data))
    rel = [e for e in bad["entries"] if e["version"] == "ARCH_TAKEOFF_V3.0.3" and e["action"] == "RELEASED"]
    assert sum(e["class"] == "A-REPRODUCED" for e in rel) < 10, "a wrong declared fact must not be absorbed"


def test_adverse_undeclared_cover_holds_the_slab_lines(M):
    data = json.loads((HERE / "DEVELOPMENT-VILLA-T131.rebar_facts.json").read_text(encoding="utf-8"))
    data["facts"] = [x for x in data["facts"] if x["fact_id"] != "REBAR.SLAB.BAR_END.CLEAR_COVER"]
    bad = M.build(cfg=pc.parse_project_config(data))
    dev = [e for e in bad["entries"] if e["version"] == "ARCH_TAKEOFF_V3.0.27"
           and e["patch"].get("valued") is not None]
    assert dev and all(e["rule_result"]["state"] == "HELD" and e["rule_result"]["low"] is None for e in dev)
