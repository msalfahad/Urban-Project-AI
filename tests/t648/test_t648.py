"""T-648 finishes HELD-line cause census (R-T648-1): synthetic villa W648 by hand (normal + adverse) and the development
villa pinned to the committed outputs.

Villa W648 (synthetic, not the development villa), by hand:
  dry bedroom floor 12.50 m2, Q-45 band 0.03 .. 0.04 m -> bed 0.375 .. 0.500 m3
  wet bath floor 4.20 m2, band 0.04 .. 0.06 m          -> bed 0.168 .. 0.252 m3
  arch opening strip 1.10 m clear x 0.20 m wall         -> fix row 0.220 m2 (DRAWING-CONFIRMED)
  mirrored plan (x -> -x) changes no length: same values; a 20 cm wall typed as 20 (cm read as m) is refused
"""
import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t648"))
import t648_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t648" / "out" / "FINISH_HOLD_CAUSE_CENSUS_T648.json"


def _entry(**kw):
    e = {"line_id": "L-w648-1", "group": "B3", "item_code": "FIN.FLOOR.BED.DRY", "unit": "m3", "element_id": "W648-R1",
         "held_low": "0.375", "held_high": "0.5", "measured_net": None, "class": "OWNER_DECISION",
         "cause": "owner band Q-45", "source": "W648 ledger row 1", "drawing": "W648 plan", "owner_ref": "Q-45"}
    e.update(kw)
    return e


# ---------------------------------------------------------------- normal cases (hand values)

def test_band_dry_and_wet_by_hand():
    assert R.band_bound("12.50", ("0.03", "0.04")) == (Decimal("0.375000"), Decimal("0.500000"))
    assert R.band_bound("4.20", ("0.04", "0.06")) == (Decimal("0.168000"), Decimal("0.252000"))


def test_band_mirror_and_rotation_invariant():
    # a mirrored / rotated room keeps its area: the bound is unchanged
    a = Decimal("3.0") * Decimal("4.1666666")
    assert R.band_bound(a, ("0.03", "0.04")) == R.band_bound(Decimal("4.1666666") * Decimal("3.0"), ("0.03", "0.04"))


def test_fix_row_by_hand():
    v = R.fix_value({"clear_width_m": ("1.10", "W648 plan jambs"), "wall_m": ("0.20", "W648 wall faces")})
    assert v == Decimal("0.220000")
    e = _entry(item_code="ARCH.THRESHOLD", unit="m2", held_low=None, held_high=None)
    e["class"] = "PRINTED_VALUE_GAP"
    e["fix"] = {"status": "DRAWING-CONFIRMED", "wired": False, "value": "0.22", "unit": "m2",
                "terms": {"clear_width_m": ["1.10", "W648 plan jambs"], "wall_m": ["0.20", "W648 wall faces"]}}
    assert R.check_entry(e)


def test_census_counts_per_trade_unit():
    a = _entry()
    b = _entry(line_id="L-w648-2", group="B8", item_code="FIN.WP.PENETRATION", unit="pcs", held_low=None,
               held_high=None, **{"class": "DESIGNER_ITEM"}, designer_ref="D-99")
    c = R.census_counts([a, b])
    assert c["lines"] == 2 and c["by_class"] == {"DESIGNER_ITEM": 1, "OWNER_DECISION": 1}
    assert c["by_trade_unit"]["B3|m3"]["after_with_cause"] == 1


# ---------------------------------------------------------------- adverse cases

def test_mid_value_band_refused():
    with pytest.raises(R.RuleError):
        R.band_bound("12.50", ("0.035", "0.035"))


def test_cm_read_as_m_refused():
    with pytest.raises(R.RuleError):
        R.band_bound("12.50", ("3", "4"))
    with pytest.raises(R.RuleError):
        R.fix_value({"clear_width_m": ("110", "plan"), "wall_m": ("0.20", "plan")})


def test_missing_area_is_not_zero():
    with pytest.raises(R.RuleError):
        R.band_bound(None, ("0.03", "0.04"))
    with pytest.raises(R.RuleError):
        R.band_bound("0", ("0.03", "0.04"))


def test_unprinted_term_refuses_fix_row():
    with pytest.raises(R.RuleError):
        R.fix_value({"clear_width_m": ("1.10", "W648 plan"), "height_m": ("2.20", "")})


def test_freelancer_figure_as_cause_refused():
    with pytest.raises(R.RuleError):
        R.check_entry(_entry(cause="matches the freelancer total 72.01 m2"))
    with pytest.raises(R.RuleError):
        R.check_entry(_entry(source="his sheet row 7"))


def test_held_as_zero_refused():
    with pytest.raises(R.RuleError):
        R.check_entry(_entry(held_low="0", held_high="0"))
    with pytest.raises(R.RuleError):
        R.check_entry(_entry(measured_net="0"))


def test_fix_row_value_must_be_the_product():
    e = _entry(item_code="ARCH.THRESHOLD", unit="m2", held_low=None, held_high=None)
    e["class"] = "PRINTED_VALUE_GAP"
    e["fix"] = {"status": "DRAWING-CONFIRMED", "wired": False, "value": "0.25", "unit": "m2",
                "terms": {"w": ["1.10", "plan"], "t": ["0.20", "plan"]}}
    with pytest.raises(R.RuleError):
        R.check_entry(e)
    e["fix"]["value"], e["fix"]["wired"] = "0.22", True
    with pytest.raises(R.RuleError):
        R.check_entry(e)


def test_dependency_rules():
    e = _entry(**{"class": "DEPENDENCY"}, depends_on="L-w648-1")
    with pytest.raises(R.RuleError):
        R.check_entry(e)                        # self-reference
    e["depends_on"] = "L-w648-9"
    with pytest.raises(R.RuleError):
        R.check_entry(e, held_ids={"L-w648-1"})  # not a HELD line
    assert R.check_entry(e, held_ids={"L-w648-9"})


def test_one_class_one_line():
    with pytest.raises(R.RuleError):
        R.census_counts([_entry(), _entry()])
    with pytest.raises(R.RuleError):
        R.check_entry(_entry(**{"class": "MAYBE"}))
    with pytest.raises(R.RuleError):
        R.check_entry(_entry(owner_ref=None))
    with pytest.raises(R.RuleError):
        R.check_entry(_entry(**{"class": "DESIGNER_ITEM"}, designer_ref="RFI-1"))


# ---------------------------------------------------------------- development villa (pinned outputs)

def _build():
    import t648_alsenan as A
    return A, A.build()


def test_dev_villa_matches_committed_output():
    A, b = _build()
    assert A.dumps(b) == OUT.read_text(encoding="utf-8")


def test_dev_villa_scope_and_census():
    _, b = _build()
    c = b["counts"]
    assert c["lines"] == 198 and c["fix_rows"] == 1
    assert sum(c["by_class"].values()) == 198
    per = {}
    for e in b["lines"]:
        per[e["group"]] = per.get(e["group"], 0) + 1
        assert e["measured_net"] is None and e["cause"] and e["source"]
    assert per == {"B2": 2, "B3": 65, "B4": 10, "B6": 14, "B7": 44, "B8": 48, "B13": 15}
    assert all(v["no_cause_after"] == 0 for v in b["census_per_trade_unit"].values())


def test_dev_villa_beds_recomputed_and_fix_row():
    _, b = _build()
    beds = [e for e in b["lines"] if e["item_code"].startswith("FIN.FLOOR.BED.")]
    assert len(beds) == 44
    for e in beds:
        chk = e["bound_check"]
        lo, hi = R.band_bound(chk["area_m2"], chk["band_m"])
        assert (R.S(lo), R.S(hi)) == (e["held_low"], e["held_high"])
    fx = b["fix_rows"]
    assert [f["line_id"] for f in fx] == ["L-868aee125705bb8d17f6"] and fx[0]["value"] == "0.15"


def test_dev_villa_doors_bound_arithmetic():
    # GF PVC doors: 3 x 0.69 x 2.20 = 4.554 .. 3 x 0.80 x 2.20 = 5.280; 1F: (0.89 + 0.69) x 2.20 = 3.476 ..
    # (1.00 + 0.80) x 2.20 = 3.960 (T-232 widths, Q-55 height): the held bounds carried agree to 1e-6
    _, b = _build()
    by = {e["line_id"]: e for e in b["lines"]}
    gf, f1 = by["L-ac8a0ea9174f53a359dd"], by["L-f4a12cd20b0f5e173430"]
    h = Decimal("2.20")
    assert Decimal(gf["held_low"]) == 3 * Decimal("0.69") * h and Decimal(gf["held_high"]) == 3 * Decimal("0.80") * h
    assert Decimal(f1["held_low"]) == (Decimal("0.89") + Decimal("0.69")) * h
    assert Decimal(f1["held_high"]) == (Decimal("1.00") + Decimal("0.80")) * h


@pytest.mark.skipif(os.environ.get("URBAN_T648_WRITE") != "1", reason="writes the committed outputs")
def test_write_outputs():
    import t648_alsenan as A
    A.write_outputs()
