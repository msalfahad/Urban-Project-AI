"""T-477: the three modules merged by T-458 / T-459 / T-449 r2 are declared in the rebar-product firewall registry,
each in the class matching what it computes, and the undeclared-module check still catches a new module (adverse)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
import rebar_product_registry as RP  # noqa: E402

WORDS = ("rebar", "bbs", "reinforc")


def _declared():
    return set(RP.ACCURATE_MODULES) | set(RP.ROUGH_MODULES) | set(RP.REPORT_MODULES) | set(RP.SANITY_QA_MODULES) | \
        set(RP.COMPARISON_MODULES) | set(RP.OTHER_REBAR_AWARE)


def _undeclared(root: Path, declared):
    found = {str(p.relative_to(root)) for p in (root / "engine").rglob("*.py")
             if any(w in p.read_text(encoding="utf-8", errors="ignore").lower() for w in WORDS)}
    return sorted(found - declared)


def test_new_modules_declared_in_their_class():
    # bar populations and lap splices of the accurate takeoff (drawing-derived, no ratio)
    assert "engine/source/rebar_basis_rules_v1.py" in RP.ACCURATE_MODULES
    assert "engine/source/rebar_lap_rule_v2.py" in RP.ACCURATE_MODULES
    # waterproofing areas: mentions rebar only in an evidence string -> neither product
    assert "engine/source/waterproofing_policy_v2.py" in RP.OTHER_REBAR_AWARE
    for m in ("engine/source/rebar_basis_rules_v1.py", "engine/source/rebar_lap_rule_v2.py",
              "engine/source/waterproofing_policy_v2.py"):
        assert (ROOT / m).exists(), m
        assert m not in set(RP.ROUGH_MODULES) | set(RP.REPORT_MODULES) | set(RP.COMPARISON_MODULES), m


def test_each_module_declared_exactly_once():
    groups = (RP.ACCURATE_MODULES, RP.ROUGH_MODULES, RP.REPORT_MODULES, RP.SANITY_QA_MODULES,
              RP.COMPARISON_MODULES, RP.OTHER_REBAR_AWARE)
    for m in ("engine/source/rebar_basis_rules_v1.py", "engine/source/rebar_lap_rule_v2.py",
              "engine/source/waterproofing_policy_v2.py"):
        assert sum(g.count(m) for g in groups) == 1, m


def test_working_tree_has_no_undeclared_rebar_module():
    assert _undeclared(ROOT, _declared()) == []


def test_adverse_new_undeclared_module_is_caught(tmp_path):
    (tmp_path / "engine" / "source").mkdir(parents=True)
    (tmp_path / "engine" / "source" / "new_bbs_thing.py").write_text("# computes REINFORCEMENT kg\n", encoding="utf-8")
    (tmp_path / "engine" / "source" / "plain.py").write_text("x = 1\n", encoding="utf-8")
    assert _undeclared(tmp_path, set()) == ["engine/source/new_bbs_thing.py"]
    assert _undeclared(tmp_path, {"engine/source/new_bbs_thing.py"}) == []
