"""T-643: rebar on HELD concrete + concrete binding of bar lines (R-T643-1). Synthetic villa "V643" (not the training
villa) by hand with adverse cases; then the development villa: the 14 RELEASED column main-bar lines of F-T639-1
decided, the 208 unbound lines classed (repository files only; the schedule re-read from the private DXF only when the
private copy is present)."""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t643"))
import t643_rules as R  # noqa: E402
import t643_alsenan as A  # noqa: E402

D = Decimal

# ---- villa "V643" (hand) --------------------------------------------------------------------------------------------
# Column K7 on storey 2F, schedule row 'K7 2F: 10 ø 16'; declared levels +7.20 (2F) and +11.00 (roof) -> interval 3.80
# (clear height 3.30 + beam depth 0.50; bars run through the joint). Main bars 10 x 3.80 x 16^2/162 (1.580247)
# = 38.00 m x 1.580247 = 60.049383 kg.
#   case S: concrete HELD on schedule 0.25 x 0.50 vs drawn 0.30 x 0.50 (section only)       -> KEEP 60.049 kg
#   case R: concrete HELD because the roof level is not declared (interval open)              -> DOWNGRADE
BAR = {"population": "COLUMN_MAIN_BARS_OVER_STOREY_INTERVAL", "count": 10, "dia_mm": 16, "length_m": "3.80",
       "released_kg": "60.049"}
HOLD_S = {"rule": "R-COL-SECTION-CONFLICT-1", "facts_used": [], "held_reason": "schedule vs drawn section",
          "facts_h": 3.8, "declared_levels": ["LEVEL.STRUCTURAL_TOP.2F.MAIN", "LEVEL.STRUCTURAL_TOP.ROOF.MAIN"]}
HOLD_R = {"rule": "R-COL-LEVEL-HEIGHT-1", "facts_used": ["LEVEL.STRUCTURAL_TOP.ROOF.MAIN"],
          "held_reason": "LEVEL.STRUCTURAL_TOP.ROOF.MAIN: not declared for this project", "facts_h": None,
          "declared_levels": []}


def test_v643_by_hand():
    assert R.q(R.population_kg(10, "3.80", 16)) == D("60.049383")
    assert R.q(R.population_kg(10, "3.30", 16) + R.population_kg(10, "0.50", 16)) == D("60.049383")


def test_v643_section_hold_keeps_printed_bars():
    d = R.decide_inherit(BAR, HOLD_S, schedule={"count": 10, "dia_mm": 16})
    assert d["decision"] == "KEEP" and d["kg_kept"] == D("60.049383") and d["inputs_entered"] == []


def test_v643_roof_level_hold_downgrades():
    d = R.decide_inherit(BAR, HOLD_R)
    assert d["decision"] == "DOWNGRADE" and d["to"] == "HELD" and d["inputs_entered"] == ["L"]


def test_v643_mirror_rotation_units():
    # a mirrored / rotated plan changes no input of n x L x d^2/162; the storey order of the levels does not matter
    assert R.decide_inherit(dict(BAR, count="10", length_m=D("3.8")), HOLD_S)["decision"] == "KEEP"
    with pytest.raises(R.RuleError, match="UNIT_REFUSED"):
        R.decide_inherit(dict(BAR, length_m=3800, released_kg=None), HOLD_S)
    with pytest.raises(R.RuleError, match="UNIT_REFUSED"):
        R.decide_inherit(dict(BAR, dia_mm=0.016, released_kg=None), HOLD_S)


def test_adverse_unprinted_height_kept_released_refused():
    for bad in (dict(HOLD_S, facts_h=None), dict(HOLD_S, declared_levels=[])):
        with pytest.raises(R.RuleError, match="unprinted height cannot stay released"):
            R.decide_inherit(BAR, bad)
    with pytest.raises(R.RuleError, match="!= declared interval"):
        R.decide_inherit(BAR, dict(HOLD_S, facts_h=4.2))


def test_adverse_missing_or_contradicted_inputs_refused():
    for k in ("count", "dia_mm", "length_m"):
        with pytest.raises(R.RuleError, match="never 0"):
            R.decide_inherit(dict(BAR, **{k: None}), HOLD_S)
    with pytest.raises(R.RuleError, match="schedule re-read"):
        R.decide_inherit(BAR, HOLD_S, schedule={"count": 8, "dia_mm": 16})
    with pytest.raises(R.RuleError, match="released"):
        R.decide_inherit(dict(BAR, released_kg="61.000"), HOLD_S)
    with pytest.raises(R.RuleError, match="not mapped"):
        R.decide_inherit(BAR, dict(HOLD_S, rule="R-UNKNOWN"))
    with pytest.raises(R.RuleError, match="no input map"):
        R.decide_inherit(dict(BAR, population="BEAM_LINKS"), HOLD_S)
    with pytest.raises(R.RuleError, match="whole number"):
        R.decide_inherit(dict(BAR, count=9.5, released_kg=None), HOLD_S)


def test_binding_rules():
    b = R.classify_binding([("L-a", "RELEASED"), ("L-b", "HELD")], "band")
    assert b["binding"] == "BOUND" and b["concrete_class"] == "HELD"
    u = R.classify_binding([("L-a", "RELEASED"), ("L-b", "HELD")], "pair", mixed_is_unresolved=True)
    assert u["binding"] == "UNRESOLVED" and u["concrete_class"] is None
    assert R.classify_binding([], "", unresolved="inferred only")["binding"] == "UNRESOLVED"
    assert R.classify_binding([("L-a", "EXCLUDED"), ("L-b", "HELD")], "x")["concrete_class"] == "EXCLUDED"
    with pytest.raises(R.RuleError):
        R.concrete_state(["MAYBE"])


# ---- development villa (repository files) ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def out():
    return A.build()


def test_dev_14_decided_and_kg_readd(out):
    p1 = out["part1"]
    assert p1["n"] == 14 and p1["by_decision"] == {"DOWNGRADE": 4, "KEEP": 10}
    assert D(p1["kg_kept_released"]) == D("595.435") and D(p1["kg_proposed_held"]) == D("159.288")
    assert D(p1["kg_kept_released"]) + D(p1["kg_proposed_held"]) == D("754.723")
    down = {r["column"] for r in p1["lines"] if r["decision"] == "DOWNGRADE"}
    assert down == {"COL-2F-50", "COL-2F-51", "COL-2F-53", "COL-2F-54"}
    for r in p1["lines"]:
        assert r["schedule_reread"]["agrees"]
        if r["decision"] == "DOWNGRADE":
            assert r["concrete_hold"]["rule"] == "R-COL-LEVEL-HEIGHT-1"
            assert "LEVEL.STRUCTURAL_TOP.ROOF.MAIN" in r["concrete_hold"]["facts_used"]
        else:
            assert r["concrete_hold"]["rule"] == "R-COL-SECTION-CONFLICT-1"
            assert D(str(r["concrete_hold"]["facts_h"])) == D(r["L_m"])
    assert len(p1["downgrade_proposals"]) == 4 and all(d["checker"] is None for d in p1["downgrade_proposals"])


def test_dev_three_by_hand(out):
    by = {r["column"]: r for r in out["part1"]["lines"]}
    # COL-1F-41 C9 1F: 12 x 4.20 x 1.580247 = 79.644444 ; COL-GF-14 C3 GF: 8 x 4.50 x 1.580247 = 56.888889
    # COL-2F-50 C2 2F: 6 x 4.20 x 1.580247 = 39.822222 (proposed HELD: interval to the undeclared roof level)
    assert by["COL-1F-41"]["kg_kept"] == "79.644444" and by["COL-1F-41"]["decision"] == "KEEP"
    assert by["COL-GF-14"]["kg_kept"] == "56.888889" and by["COL-GF-14"]["decision"] == "KEEP"
    assert by["COL-2F-50"]["kg_withdrawn"] == "39.822222" and by["COL-2F-50"]["decision"] == "DOWNGRADE"


def test_dev_208_classed_nothing_released(out):
    p2 = out["part2"]
    assert p2["n"] == 208 and sum(p2["by_binding"].values()) == 208
    assert p2["by_binding"] == {"BOUND": 185, "UNRESOLVED": 23}
    for r in p2["lines"]:
        assert r["binding"] in ("BOUND", "UNRESOLVED")
        assert (r["binding"] == "BOUND") == bool(r.get("basis")) and (r["binding"] == "UNRESOLVED") == bool(r.get("reason"))
        assert r["state"] in ("BLANK", "OPEN_HIGH") and "computed" not in r
    assert D(out["part1"]["released_B11_if_downgrades_applied_kg"]) < D(out["part1"]["released_B11_before_kg"])
    assert "NOTHING RELEASED" in out["released"]


def test_dev_outputs_current(out):
    assert A.OUT_JSON.exists(), "run test_write_outputs with URBAN_T643_WRITE=1"
    disk = json.loads(A.OUT_JSON.read_text(encoding="utf-8"))
    assert disk == json.loads(json.dumps(out, ensure_ascii=False, sort_keys=True))


@pytest.mark.skipif(not A.PRIVATE_DXF.exists(), reason="private structural DXF not present (.work/private)")
def test_private_schedule_reread():
    got = A.reread_schedule()
    for k, v in A.SCHEDULE_REREAD.items():
        assert got.get(k) == v, (k, got.get(k), v)


@pytest.mark.skipif(os.environ.get("URBAN_T643_WRITE") != "1", reason="writer: URBAN_T643_WRITE=1 only")
def test_write_outputs():
    A.write()
