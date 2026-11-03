"""T-449 round 3: the blockwork correction register over the merged project inputs (public research files only).

The register imports the merged input builders of the V3.0.44 candidate run (each pins its own ledgers by sha256) and
the declared facts; it needs no private drawing. Checks: the committed output is what the register builds; the census
leaves no masonry input unclassed; every closable wall the generic rule reproduces is within the 4 dp print or a named
residual under 0.5 %; held stays held (never 0); every A-SPECIFIED entry names the rule its generic code owes; the
declared facts' affected lines are exactly the lines the register uses them for; an adverse fact (a wrong storey
height) breaks the reproduction instead of being absorbed.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from engine import project_config as pc

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research/agents_t449/round3"


@pytest.fixture(scope="module")
def M():
    spec = importlib.util.spec_from_file_location("t449_blockwork_register_test", HERE / "t449_blockwork_register.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def reg(M):
    return M.build()


def _mas(reg):
    return [e for e in reg["entries"] if e["version"] == "ARCH_TAKEOFF_V3.0.26" and e["item_code"] == "MAS.BLOCK"]


def test_committed_register_is_the_build(reg, M):
    committed = json.loads((HERE / "out/CORRECTION_REGISTER_BLOCKWORK_T449.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(reg, sort_keys=True)) == committed
    assert (HERE / "out/CORRECTION_REGISTER_BLOCKWORK_T449.csv").read_text(encoding="utf-8") == M.to_csv(reg)


def test_census_classes_every_builder(reg):
    cens = {c["version"]: c for c in reg["census"]}
    assert len(cens) == 42                                   # V3.0.2, V3.0.3, V3.0.5 .. V3.0.44 (V3.0.4: T-167 files)
    reach = sorted(v for v, c in cens.items() if c["reach"] == "REACHES")
    assert reach == ["ARCH_TAKEOFF_V3.0.19", "ARCH_TAKEOFF_V3.0.23", "ARCH_TAKEOFF_V3.0.26", "ARCH_TAKEOFF_V3.0.35"]
    assert all(c["reach"] in ("REACHES", "TEXT_ONLY", "NONE") for c in cens.values())
    assert all(c["masonry_words"] == 0 for c in cens.values() if c["reach"] == "NONE")


def test_counts_and_no_class_c(reg):
    assert reg["counts"] == {"A-REPRODUCED": 234, "A-SPECIFIED": 26}
    assert all(e["class"] in ("A-REPRODUCED", "A-SPECIFIED") for e in reg["entries"])     # no B / C entry


def test_every_v3026_wall_item_is_classed_once(reg):
    es = [e for e in reg["entries"] if e["version"] == "ARCH_TAKEOFF_V3.0.26"]
    assert len(es) == 228
    keys = {(e["line_id"], e["element_id"]) for e in es}
    assert len(keys) == 228
    assert len(_mas(reg)) == 76


def test_reproduced_walls_within_print_or_named_residual(reg):
    rep = [e for e in _mas(reg) if e["class"] == "A-REPRODUCED" and e["patch"]["carried"] is not None]
    assert len(rep) == 37
    for e in rep:
        r = abs(e["carried_minus_rule_m2"])
        assert r <= 0.0005 or ("residual_named" in e and r <= 0.005 * e["patch"]["carried"]), e["element_id"]
    m = reg["mas_block"]
    assert m["carried_m2"] == pytest.approx(499.304, abs=1e-4) and m["rule_m2"] == pytest.approx(499.3007, abs=1e-4)
    assert m["max_abs_residual_m2"] <= 0.004


def test_drop_walls_reproduced_carry_upper_bound_only(reg):
    d = [e for e in _mas(reg) if e["action"] == "HELD ON DROP" and e["class"] == "A-REPRODUCED"]
    assert {e["element_id"] for e in d} == {"GF-W12", "GF-W31", "GF-W32"}
    for e in d:
        assert e["rule_result"]["state"] == "DROP" and e["rule_result"]["value"] is None


def test_held_walls_stay_held_never_zero(reg):
    held = [e for e in _mas(reg) if e["action"] == "HELD"]
    assert len(held) == 28 and all(e["class"] == "A-REPRODUCED" for e in held)
    for e in held:
        assert e["patch"]["carried"] is None and e["rule_result"]["state"] == "HELD"
        assert e["rule_result"]["value"] is None and e["rule_result"]["held"]


def test_annex_walls_held_on_the_undeclared_storey(reg, M):
    ax = [e for e in _mas(reg) if any("STOREY_HEIGHT.GF.ANNEX" in h for h in (e.get("rule_result") or {}).get(
        "held", []))]
    assert len(ax) >= 10 and all(e["action"] == "HELD" for e in ax)
    assert M.F_ANNEX in reg["not_declared"]


def test_every_specified_entry_names_its_pending_rule(reg):
    for e in reg["entries"]:
        if e["class"] == "A-SPECIFIED":
            assert e.get("not_reproduced"), e["element_id"]
            if e["version"] == "ARCH_TAKEOFF_V3.0.26" and e["item_code"] == "MAS.BLOCK":
                assert e.get("rule_pending", "").startswith("R-MAS-"), e["element_id"]


def test_panel_and_volume_follow_the_masonry_wall(reg):
    mas = {e["element_id"]: e for e in _mas(reg)}
    for e in reg["entries"]:
        if e["version"] != "ARCH_TAKEOFF_V3.0.26" or e["item_code"] == "MAS.BLOCK":
            continue
        assert e["class"] == mas[e["element_id"]]["class"]
        if e["item_code"] == "ARCH.WALL_VOLUME" and e["patch"]["carried"] is not None:
            assert abs(e["patch"]["carried"] - mas[e["element_id"]]["patch"]["carried"] * e["thickness_m"]) <= 5e-4


def test_complete_lines_reproduce_the_declared_figures(reg):
    full = [v for v in reg["lines"].values() if v["all_walls_reproduced"]]
    assert len(full) == 4
    for v in full:
        for k in ("determinate_diff_pct", "parts_diff_pct"):
            assert v[k] is None or abs(v[k]) <= 0.01


def test_parapet_block_alternatives(reg):
    p = [e for e in reg["entries"] if e["version"] == "ARCH_TAKEOFF_V3.0.23"]
    assert len(p) == 25 and sum(e["class"] == "A-REPRODUCED" for e in p) == 23
    spec = {e["element_id"]: e for e in p if e["class"] == "A-SPECIFIED"}
    assert set(spec) == {"ANNEX_ROOF#PARAPET_RC:NE-6x", "1F_ROOF#PARAPET_RC:NW-2"}
    assert spec["1F_ROOF#PARAPET_RC:NW-2"]["rule_result"]["high"] == pytest.approx(3.1672, abs=1e-9)  # not 3.6107


def test_fence_and_trace_reproduced(reg):
    for v, n in (("ARCH_TAKEOFF_V3.0.35", 5), ("ARCH_TAKEOFF_V3.0.19", 2)):
        es = [e for e in reg["entries"] if e["version"] == v]
        assert len(es) == n and all(e["class"] == "A-REPRODUCED" for e in es)


def test_declared_facts_load_and_match_usage(reg, M):
    cfg = pc.load_project_config(M.FACTS)
    for fid, lines in reg["fact_usage"].items():
        fact = cfg.lookup(fid).fact
        assert fact is not None and list(fact.affected_lines) == lines, fid
    assert {f.fact_id for f in cfg.active_facts()} == set(reg["fact_usage"])
    assert cfg.lookup(M.F_ANNEX).status == "HELD"


def test_adverse_wrong_storey_breaks_reproduction(M):
    data = json.loads(M.FACTS.read_text(encoding="utf-8"))
    bad = copy.deepcopy(data)
    for f in bad["facts"]:
        if f["fact_id"] == M.F_STOREY["1F"]:
            f["value"] = 4.10
    reg = M.build(cfg=pc.parse_project_config(bad))
    lost = [e for e in _mas(reg) if e["floor"] == "1F" and e["patch"]["carried"] is not None
            and e["class"] == "A-REPRODUCED"]
    assert lost == [], "a wrong storey height must not be absorbed into a reproduction"
