"""T-560: B11 reinforcement tonnage reconciled against a freelancer by scope group (research/agents_t560, R-T560-1 .. 5).
Hand villa "K560" (not the training villa): a counted pad mat with normal and adverse cases; then the committed
development-villa table rebuilt from merged repository files (the private workbook re-read runs only when present)."""
from __future__ import annotations

import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t560"))
import t560_rules as R  # noqa: E402

sys.path.insert(0, str(ROOT / "engine" / "source"))
import rebar_unit_mass as UM  # noqa: E402

OUT = ROOT / "research" / "agents_t560" / "out" / "T560_REBAR_RECONCILE.json"
PRIVATE_WB = ROOT.parent / "private" / "concrete_rebar.xlsx"
D = Decimal
TABLE = {"method": UM.STANDARD_MASS_TABLE, "table": {16: 1.578, 12: 0.888}, "authority": "hand fixture K560"}


# ---- villa "K560" (hand) ------------------------------------------------------------------------------------------
# Pad 2.00 x 2.00, bottom mat T16 @ 200 both ways, cover 0.075 (counting convention: first and last bar on the cover
# line, N = 1 + floor((B - 2c) / s); not universal, Q-71: a drawing that prints another convention governs).
#   N = 1 + floor(1.85 / 0.20) = 10 each way; bar 2.00 - 0.15 = 1.85 m; 2 x 10 x 1.85 x 1.578 = 58.386 kg
def test_hand_pad_mat_counted():
    kgm = UM.kg_per_m(16, TABLE)
    r = R.mat_mass_kg(2.00, 2.00, 0.075, 0.20, 0.20, kgm)
    assert (r["n_x"], r["n_y"]) == (10, 10)
    assert r["len_x"] == r["len_y"] == D("1.850000")
    assert r["kg"] == D("58.386000")
    assert R.to_t(r["kg"], "kg") == D("0.058386")


def test_hand_pad_rotation_and_mirror_invariant():
    # 2.40 x 1.60, T16 @ 200 along x / @ 150 along y: 8 x 2.25 + 16 x 1.45 = 41.2 m x 1.578 = 65.0136 kg
    a = R.mat_mass_kg(2.40, 1.60, 0.075, 0.20, 0.15, 1.578)
    b = R.mat_mass_kg(1.60, 2.40, 0.075, 0.15, 0.20, 1.578)          # rotated 90 degrees (mirror is the same set)
    assert (a["n_x"], a["n_y"]) == (8, 16) and (b["n_x"], b["n_y"]) == (16, 8)
    assert a["kg"] == b["kg"] == D("65.013600")


def test_unit_mass_method_is_the_project_table_not_a_hidden_formula():
    assert UM.kg_per_m(16, TABLE) == 1.578
    # d^2/162 would give 2 x 10 x 1.85 x 1.580247 = 58.469 kg: a different (named) method, never mixed in one table
    alt = R.mat_mass_kg(2.00, 2.00, 0.075, 0.20, 0.20, UM.kg_per_m(16, {"method": UM.D2_OVER_162}))
    assert alt["kg"] == D("58.469136")
    with pytest.raises(UM.UnitMassError):
        UM.assert_single_method([TABLE, {"method": UM.D2_OVER_162}])


def test_missing_spacing_is_held_never_zero():
    r = R.mat_mass_kg(2.00, 2.00, 0.075, None, 0.20, 1.578)
    assert r["kg"] is None and r["status"].startswith("HELD")


def test_millimetres_refused():
    with pytest.raises(ValueError, match="millimetres"):
        R.mat_mass_kg(2000, 2000, 75, 200, 200, 1.578)


# ---- adverse: units --------------------------------------------------------------------------------------------------
def test_kg_relabelled_as_t_refused():
    with pytest.raises(ValueError, match="relabelled"):
        R.bench_value(5800, "t", row_unit="kg")
    with pytest.raises(ValueError, match="not printed"):
        R.bench_value(5.8, "ton?")
    # a kg figure typed under a t header: implied 74,712 kg per m3 of concrete is above the steel density
    with pytest.raises(ValueError, match="density of steel"):
        R.plausible_t(R.bench_value(5800, "t"), "77.6305")
    assert R.plausible_t(D("5.8"), "77.6305") == D("74.71")


def test_t_only_at_the_boundary():
    assert R.to_t(D("9375.306"), "kg") == D("9.375306")
    assert R.to_t(D("44.19"), "t") == D("44.190000")
    with pytest.raises(ValueError):
        R.to_t(1, "kN")


# ---- adverse: basis and agreement -------------------------------------------------------------------------------
def test_ratio_or_lump_never_agreement_or_percent():
    assert R.classify_basis(False, None) == "TYPED_LUMP"
    assert R.classify_basis(False, "=E17*0.075") == "RATIO"
    assert R.comparison_class("TYPED_LUMP") == R.comparison_class("RATIO") == "RULE_DIFF"
    assert R.comparison_class("COUNTED") == "LIKE_FOR_LIKE"
    with pytest.raises(ValueError, match="never 'agreement'"):
        R.refuse_agreement("RULE_DIFF", "AGREE")
    eng = R.engine_parts([{"class": "RELEASED", "measured_net": 58.386, "unit": "kg"}])
    c = R.causes(D("0.058386"), eng, "TYPED_LUMP")      # numerically equal, still RULE_DIFF, no percentage
    assert c["cls"] == "RULE_DIFF" and c["gap_valued_t"] == D("0") and c["percent"] is None


def test_rate_interval_is_an_observation():
    lo, hi = R.rate_interval("7.95", "39.7515")
    assert lo <= D("200") < hi                            # a round rate reproduces the typed value ...
    lo, hi = R.rate_interval("5.8", "77.6305")
    assert not any(lo <= D(r) < hi for r in range(0, 400, 5))   # ... and for another family none on a 5 kg grid does


# ---- adverse: engine parts ---------------------------------------------------------------------------------------
def test_engine_parts_kept_apart():
    p = R.engine_parts([
        {"class": "RELEASED", "measured_net": 11.5, "unit": "kg"},
        {"class": "HELD", "measured_net": None, "held_low": 14.4, "held_high": 25.2, "unit": "kg"},
        {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None, "unit": "kg"},
        {"class": "EXCLUDED", "measured_net": None, "held_low": None, "held_high": None, "unit": "kg"},
    ])
    assert p["valued_kg"] == D("11.500000") and (p["held_low_kg"], p["held_high_kg"]) == (D("14.4"), D("25.2"))
    assert p["held_blank"] == 1 and p["excluded"] == 1
    none = R.engine_parts([{"class": "HELD", "measured_net": None, "held_low": None, "held_high": None, "unit": "kg"}])
    assert none["valued_kg"] is None and none["held_low_kg"] is None           # absent stays None, never 0


@pytest.mark.parametrize("bad, msg", [
    ({"class": "HELD", "measured_net": 3.0, "held_low": None, "held_high": None, "unit": "kg"}, "never enters"),
    ({"class": "HELD", "measured_net": None, "held_low": 1.0, "held_high": None, "unit": "kg"}, "half-open"),
    ({"class": "HELD", "measured_net": None, "held_low": 2.0, "held_high": 1.0, "unit": "kg"}, "low above high"),
    ({"class": "EXCLUDED", "measured_net": 4.0, "held_low": None, "unit": "kg"}, "excluded"),
    ({"class": "RELEASED", "measured_net": 0.0045, "unit": "t"}, "kg internally"),
    ({"class": "RELEASED", "measured_net": None, "unit": "kg"}, "no quantity"),
])
def test_engine_parts_refusals(bad, msg):
    with pytest.raises(ValueError, match=msg):
        R.engine_parts([bad])


def test_groups_each_family_once():
    g = {"A": {"engine": ["F1", "F2"], "bench": ["X"]}, "B": {"engine": ["F2"], "bench": ["Y"]}}
    with pytest.raises(ValueError, match="two groups"):
        R.check_groups(g, ["F1", "F2"], ["X", "Y"])
    with pytest.raises(ValueError, match="no group"):
        R.check_groups({"A": {"engine": ["F1"], "bench": ["X"]}}, ["F1", "F2"], ["X"])


def test_no_row_group():
    eng = R.engine_parts([{"class": "HELD", "measured_net": None, "held_low": None, "held_high": None, "unit": "kg"}])
    c = R.causes(None, eng, "TYPED_LUMP")
    assert c["cls"] == "NO_ROW" and c["gap_valued_t"] is None and c["percent"] is None


def test_causes_residual_bounds():
    eng = R.engine_parts([{"class": "RELEASED", "measured_net": 1000, "unit": "kg"},
                          {"class": "HELD", "measured_net": None, "held_low": 200, "held_high": 500, "unit": "kg"}])
    c = R.causes(D("2.0"), eng, "TYPED_LUMP")
    assert c["gap_valued_t"] == D("1.000000")
    assert (c["residual_low_t"], c["residual_high_t"]) == (D("0.500000"), D("0.800000"))


# ---- development villa (committed files) -------------------------------------------------------------------------
def _build():
    spec = importlib.util.spec_from_file_location("t560_alsenan", ROOT / "research/agents_t560/t560_alsenan.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_dev_villa_rebuild_equals_committed():
    m = _build()
    assert m.dumps(m.build()) == OUT.read_text(encoding="utf-8")


def test_dev_villa_totals_and_closure():
    o = json.loads(OUT.read_text(encoding="utf-8"))
    t = o["engine_totals_t"]
    assert (t["valued"], t["held_low"], t["held_high"]) == ("9.375306", "14.278249", "19.646878")
    assert (t["held_blank_lines"], t["excluded_lines"], o["engine_lines"]) == (799, 577, 2644)
    g = o["groups"]
    assert sum(D(v["his_t"]) for v in g.values() if v["his_t"] is not None) == D(o["bench"]["total_t"]) == D("44.19")
    assert sum(v["engine_kg"]["held_blank"] for v in g.values()) == 799
    assert sum(D(v["engine_kg"]["valued_kg"]) for v in g.values() if v["engine_kg"]["valued_kg"]) == D("9375.305760")
    assert all(v["percent"] is None for v in g.values())
    assert {v["cls"] for v in g.values()} == {"RULE_DIFF", "NO_ROW"}
    assert o["bench"]["bar_rows_in_workbook"] == 0 and o["bench"]["basis"] == "TYPED_LUMP"
    assert all(f["formula"] is None for f in o["bench"]["families"].values())


def test_dev_villa_hand_check_one_line():
    # BM-GF-039 R043 bottom: 5 bars ø18 face to face 1.15 m x 18^2/162 = 5 x 1.15 x 2.0 = 11.5 kg (T-149 basis);
    # its ends (note 9) 10 x 2 layers: 40 d .. 70 d = 0.72 .. 1.26 m x 2.0 x 10 = 14.4 .. 25.2 kg, HELD beside
    o = json.loads(OUT.read_text(encoding="utf-8"))
    li = json.loads((ROOT / o["inputs"]["line_index"]).read_text(encoding="utf-8"))
    by = {ln["element_id"]: ln for ln in li["lines"]}
    assert by["HL:BEAM_STEEL:BM-GF-039:R043:BOTTOM"]["measured_net"] == pytest.approx(5 * 1.15 * 18 ** 2 / 162)
    e = by["HL:BEAM_STEEL:BM-GF-039:R043:BOTTOM_ENDS_NOTE_9_40D_70D"]
    assert (e["held_low"], e["held_high"]) == (pytest.approx(10 * 0.72 * 2.0), pytest.approx(10 * 1.26 * 2.0))


@pytest.mark.skipif(not PRIVATE_WB.exists(), reason="private workbook not present (decode it into .work/private)")
def test_private_workbook_has_no_bar_rows():
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.load_workbook(PRIVATE_WB)
    steel_words = ("حديد", "كجم", "kg", "ton")
    hits = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and (any(w in c.value.lower() for w in steel_words)
                                                 or c.value.strip() == "طن"):
                    hits.append((ws.title, c.coordinate))
    # only the summary header, the total label and its unit mention steel: no bar row anywhere
    assert len(hits) == 3 and {h[0] for h in hits} == {wb.sheetnames[0]}
    ws = wb.worksheets[0]
    for r in range(17, 24):
        assert isinstance(ws[f"H{r}"].value, (int, float))           # typed constants, no formula
    assert isinstance(ws["H25"].value, (int, float))
