"""T-449 round 1: the concrete correction register and the declared-facts file of the development villa.

The register is rebuilt from the merged input builders (each pins its own ledgers) and compared with the committed
output; the checks are the A1 acceptance of the round: every concrete entry classed, no class C left, every declared
fact used and only by the lines it lists, the generic rules reproduce the valued patches within the 4-decimal print.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from engine import project_config as pc

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "research/agents_t449/t449_concrete_register.py"
OUT = ROOT / "research/agents_t449/out/CORRECTION_REGISTER_CONCRETE_T449.json"
CSV = ROOT / "research/agents_t449/out/CORRECTION_REGISTER_CONCRETE_T449.csv"
FACTS = ROOT / "research/agents_t449/DEVELOPMENT-VILLA-T131.concrete_facts.json"


@pytest.fixture(scope="module")
def tool():
    spec = importlib.util.spec_from_file_location("t449_register_test", TOOL)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def reg(tool):
    return tool.build()


def test_committed_register_is_the_fresh_build(reg, tool):
    assert json.loads(json.dumps(reg, sort_keys=True)) == json.loads(OUT.read_text(encoding="utf-8"))
    assert CSV.read_text(encoding="utf-8") == tool.to_csv(reg)


def test_every_concrete_entry_is_classed_and_none_is_unexplained(reg):
    allowed = {"A-REPRODUCED", "A-SPECIFIED", "B"}
    assert reg["entries"] and all(e["class"] in allowed for e in reg["entries"])
    assert all(e["item_code"].startswith("STR.CONC.") for e in reg["entries"])
    assert "C" not in reg["counts"]
    assert reg["counts"] == {"A-REPRODUCED": 66, "A-SPECIFIED": 17}
    assert all(e["rule"] for e in reg["entries"])


def test_valued_patches_reproduced_within_the_ledger_print(reg):
    v = [e for e in reg["entries"] if e.get("rule_minus_patch_m3") is not None]
    assert len(v) == 19 and all(e["class"] == "A-REPRODUCED" for e in v)
    assert all(abs(e["rule_minus_patch_m3"]) <= 0.00005 + 1e-12 for e in v)
    assert reg["valued_reproduced"] == {"lines": 19, "patch_m3": 17.807512, "rule_m3": 17.807491}


def test_held_and_conflict_stay_blank(reg):
    for e in reg["entries"]:
        rr = e.get("rule_result") or {}
        if rr.get("state") in ("HELD", "CONFLICT"):
            assert rr.get("value") is None, e["line_id"]


def test_facts_file_loads_and_every_fact_lists_exactly_its_lines(reg):
    cfg = pc.load_project_config(FACTS)
    assert cfg.project_id == "DEVELOPMENT-VILLA-T131"
    declared = {f.fact_id: set(f.affected_lines) for f in cfg.facts}
    assert {k: set(v) for k, v in reg["fact_usage"].items()} == declared
    assert all(f.source_kind not in pc.REFUSED_SOURCE_KINDS for f in cfg.facts)


def test_open_items_are_not_declared(reg):
    cfg = pc.load_project_config(FACTS)
    for fid in reg["held_by_undeclared_fact"]:
        assert not cfg.history(fid) and cfg.lookup(fid).status == pc.HELD
    assert cfg.lookup("GB.EXTERIOR.DEPTH_BASIS.ANNEX").status == pc.HELD      # PENDING designer item D-35


def test_adverse_changed_level_moves_the_reproduction(tool, monkeypatch, tmp_path):
    """A wrong declared fact must show: the main GF top at +0.90 instead of +0.95 breaks every main GB line."""
    data = json.loads(FACTS.read_text(encoding="utf-8"))
    for fct in data["facts"]:
        if fct["fact_id"] == "LEVEL.STRUCTURAL_TOP.GF.MAIN":
            fct["value"] = 0.90
    p = tmp_path / "facts.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(tool, "FACTS", p)
    bad = tool.build()
    gb = [e for e in bad["entries"] if e["rule"] == "R-GB-EXT-DEPTH-1" and e["action"] == "REBASE"]
    assert len(gb) == 16 and all(e["class"] == "A-SPECIFIED" and e.get("not_reproduced") for e in gb)


def test_no_client_text_in_the_outputs():
    for p in (OUT, CSV, FACTS):
        t = p.read_text(encoding="utf-8").lower()
        assert "alsenan" not in t and "senan" not in t
