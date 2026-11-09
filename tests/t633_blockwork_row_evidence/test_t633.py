"""T-633: B9 blockwork UNKNOWN rows to evidence (R-T633-1). Hand-calculated non-development fixture (villa T633-V: a
block panel between two columns under a beam, with a door and a window), adverse cases, and the development-villa
build (committed drawing read + pinned statement; the drawing re-read is skipped when the private DXF is absent)."""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal as D
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t633"
sys.path.insert(0, str(HERE))
import t633_rules as R  # noqa: E402

PRIV = ROOT.parents[1] / ".work" / "private"
DXF = Path(os.environ.get("T633_DXF", PRIV / "P7757" / "P7757.dxf"))


# ---- fixture villa T633-V. Columns 0.30 wide at grid 0 / 4.60 m: clear panel 4.30 m. Floor plate top +0.00, slab
# soffit +3.80, beam B1 0.25 x 0.60 drawn over the panel (beam soffit +3.20 = 3.80 - 0.60).
# Door D1 0.90 x 2.20, window W1 1.20 x 1.50. By hand: gross 4.30 x 3.20 = 13.760; openings 1.980 + 1.800 = 3.780;
# net 9.980 m2. --------------------------------------------------------------------------------------------------
PANEL = dict(length="4.30", floor_level="0.00", soffit_beam="3.20", soffit_slab="3.80", beam_drawn=True)
OPEN = [("D1", "0.90", "2.20"), ("W1", "1.20", "1.50")]


def test_panel_between_columns_under_beam_by_hand():
    net, gross, ded = R.panel_net(**PANEL, openings=OPEN, on_panel_ids=["D1", "W1"])
    assert (gross, ded, net) == (D("13.7600"), D("3.7800"), D("9.9800"))


def test_mirrored_panel_same_net():
    net, _, _ = R.panel_net(**PANEL, openings=list(reversed(OPEN)), on_panel_ids=["W1", "D1"])
    assert net == D("9.9800")


def test_no_beam_takes_the_slab_soffit():
    net, gross, _ = R.panel_net(**dict(PANEL, beam_drawn=False, soffit_beam=None), openings=OPEN)
    assert gross == D("16.3400") and net == D("12.5600")


def test_adverse_opening_not_deducted_refused():
    with pytest.raises(R.RuleError, match="not deducted"):
        R.panel_net(**PANEL, openings=[OPEN[0]], on_panel_ids=["D1", "W1"])


def test_adverse_height_to_slab_where_beam_drawn_refused():
    with pytest.raises(R.RuleError, match="beam is drawn"):
        R.panel_net(**PANEL, openings=OPEN, height_to="slab")


@pytest.mark.parametrize("bad", [dict(PANEL, length=None), dict(PANEL, soffit_beam=None)])
def test_adverse_missing_value_is_held_never_zero(bad):
    with pytest.raises(R.RuleError, match="missing"):
        R.panel_net(**bad, openings=OPEN)


def test_adverse_units_mm_input_refused():
    # a length typed in mm (4300) makes the 0.90 door fit but the height 3200 makes it taller than a panel: the
    # opening-in-metres vs panel-in-mm mix is caught as a wider/taller or negative check, never silently accepted
    with pytest.raises(R.RuleError):
        R.panel_net(length="4.30", floor_level="0", soffit_beam="3.20", soffit_slab="3.80", beam_drawn=True,
                    openings=[("D1", "900", "2200")])


def test_opening_row_identity_width_plus_height():
    # his 0.90 x 2.40 vs own 1.00 x 2.20: width +0.24, height -0.20, sum = -(2.16 - 2.20) = +0.04
    w = R.opening_delta("width", w_his="0.90", h_his="2.40", w_own="1.00")
    h = R.opening_delta("height", h_his="2.40", h_own="2.20", w_own="1.00")
    assert (w, h, w + h) == (D("0.2400"), D("-0.2000"), D("0.0400"))


def test_his_only_needs_own_census():
    with pytest.raises(R.RuleError, match="census"):
        R.opening_delta("his_only", w_his="0.60", h_his="0.80")
    assert R.opening_delta("his_only", w_his="0.60", h_his="0.80", census_has_opening=False) == D("-0.4800")


def test_residual_tolerance_only_for_small_width_drift():
    assert R.residual_class(D("-0.1594"), D("-0.16"), D("-0.003"))[1] == "TOLERANCE"
    assert R.residual_class(D("-0.1500"), D("-0.16"), D("-0.010"))[1] == "FINDING"
    assert R.residual_class(D("1"), D("1"), None) == (D("0"), None)


def test_split_refuses_bad_class():
    with pytest.raises(R.RuleError):
        R.split([{"class": "AGREE", "evidence": "OWN_DXF", "own_delta": "1"}])


# ---- development villa build ------------------------------------------------------------------------------------
def test_build_matches_committed_output():
    import t633_alsenan as A
    b = A.build()
    assert A.dumps(b) == A.OUT_JSON.read_text(encoding="utf-8")
    assert A.markdown(b) == A.OUT_MD.read_text(encoding="utf-8")
    assert b["unknown_rows"] == 39 and b["held_rows_untouched"] == 50
    assert b["held_signed_untouched"] == "561.2232755"
    assert b["statement_unknown_signed"] == "231.6737245"
    # the signed split by class equals the own total exactly; own - statement = sum of residuals
    assert sum(D(v) for v in b["by_class_proposed"].values()) == D(b["own_unknown_signed"])
    assert D(b["own_unknown_signed"]) - D(b["statement_unknown_signed"]) == D(b["residual"])
    assert all(r["residual_class"] in (None, "TOLERANCE") for r in b["rows"])
    assert "HELD" not in b["by_class_proposed"]


def test_build_refuses_a_tampered_statement(monkeypatch):
    import t633_alsenan as A
    monkeypatch.setattr(A, "SCORECARD_SHA", "0" * 64)
    with pytest.raises(R.RuleError, match="re-pin"):
        A.build()


def test_committed_drawing_read_has_no_coordinates():
    d = json.loads((HERE / "T633_DRAWN.json").read_text(encoding="utf-8"))
    txt = json.dumps(d)
    assert "insert\"" not in txt and "_iv" not in txt and "_c\"" not in txt
    assert sum(1 for c in d["census_1f_windows"] if c["width"] == "0.600") == 5


@pytest.mark.skipif(not DXF.exists(), reason="private DXF absent")
def test_drawing_reread_equals_committed():
    import t633_extract as X
    assert X.read(str(DXF)) == json.loads((HERE / "T633_DRAWN.json").read_text(encoding="utf-8"))
