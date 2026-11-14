"""T-786 UNMARKED_PIECE_DEPTH_V1: unmarked beam pieces follow the company ladder; roof-edge projection bands that a section
cuts without concrete (or of the same drawn type) take the printed slab thickness.

Normal (synthetic villa, not Alsenan): a span past a column 0.25 x 3.20 m with the adjacent span printed 25 x 60 ->
0.80 m2 x 0.60 = 0.480 m3 DEFAULT; the same span with no adjacent span -> 0.60 company default (never 0); a 0.25 x 6.00
band outside an edge beam, cut by a section showing no concrete, slab 0.18 printed -> 1.50 m2 x 0.18 = 0.270 m3; a
mirrored / rotated band (same plan area) gives the same figure. Adverse: no printed slab thickness -> HELD 0 .. 0.60
range (never 0 released); a section that shows concrete in the band keeps it a beam; a band not outside an edge beam
stays a beam piece; mm read as m, NaN, negative. The Alsenan set (committed numbers only): 11 lines change, nothing new.
Writes nothing."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t786"))
import t786_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t786" / "out" / "FIX_ROWS.json"


def test_unmarked_beam_adjacent_span_by_hand():
    v = R.piece_m3(0.25 * 3.20, "BEAM_PIECE", adjacent_span=0.60)
    assert v["net"] == pytest.approx(0.48) and v["label"] == "DEFAULT" and v["step"] == "adjacent_span"


def test_unmarked_beam_no_adjacent_span_takes_060_never_zero():
    v = R.piece_m3(0.25 * 3.20, "BEAM_PIECE")
    assert v["net"] == pytest.approx(0.48) and v["depth_m"] == 0.60 and v["step"] == "company_default_0.60"
    assert v["net"] > 0


def test_printed_depth_wins_over_ladder():
    v = R.piece_m3(1.0, "BEAM_PIECE", printed=0.75, same_mark=0.50, adjacent_span=0.40)
    assert v["net"] == pytest.approx(0.75) and v["label"] == "DRAWING-READ"


def test_projection_band_cut_by_section_takes_slab_thickness():
    kind = R.classify(outside_edge_beam=True, roof_edge=True, section_cuts_band=True, section_shows_concrete_in_band=False)
    assert kind == "PROJECTION_BAND"
    v = R.piece_m3(0.25 * 6.00, kind, slab_thickness=0.18)
    assert v["net"] == pytest.approx(0.27) and v["label"] == "DEFAULT"


def test_same_type_band_and_mirror_rotation_invariant():
    kind = R.classify(True, True, None, None, same_type_as_cut_band=True)
    assert kind == "PROJECTION_BAND"
    a = R.piece_m3(6.00 * 0.25, kind, slab_thickness=0.18)["net"]     # rotated 90 degrees: same plan area
    b = R.piece_m3(0.25 * 6.00, kind, slab_thickness=0.18)["net"]     # mirrored
    assert a == pytest.approx(b)


def test_adverse_no_slab_thickness_is_held_range_not_zero():
    v = R.piece_m3(1.50, "PROJECTION_BAND", slab_thickness=None)
    assert v["class"] == "HELD" and v["net"] is None
    assert v["low"] == 0.0 and v["high"] == pytest.approx(0.90)


def test_adverse_section_with_concrete_or_not_outside_beam_stays_beam():
    assert R.classify(True, True, True, True) == "BEAM_PIECE"
    assert R.classify(False, True, True, False) == "BEAM_PIECE"
    assert R.classify(True, True, None, None, same_type_as_cut_band=False) == "BEAM_PIECE"


@pytest.mark.parametrize("bad", [180.0, -0.16, float("nan"), True])
def test_adverse_units_and_garbage(bad):
    with pytest.raises(R.DepthRuleError):
        R.piece_m3(1.0, "PROJECTION_BAND", slab_thickness=bad)
    with pytest.raises(R.DepthRuleError):
        R.piece_m3(1.0, "BEAM_PIECE", adjacent_span=bad)


def test_adverse_missing_area_raises():
    with pytest.raises(R.DepthRuleError):
        R.piece_m3(None, "BEAM_PIECE")


def test_alsenan_set_committed_numbers():
    out = json.loads(OUT.read_text())
    assert out["candidate_version"] == "ARCH_TAKEOFF_V3.0.85" and out["new_lines"] == []
    rows = out["rows"]
    assert len(rows) == 11 and len({r["line_id"] for r in rows}) == 11
    for r in rows:
        assert r["after"]["class"] == "RELEASED" and r["after"]["net"] > 0       # never 0
        assert r["after"]["net"] == pytest.approx(r["before"]["net"] * 0.16 / 0.60, abs=6e-4)
        assert r["label"] == "DEFAULT" and r["designer_item"] == "D-26" and "0.16" in r["basis"]
    s = out["summary"]
    assert s["beam_delta_m3"] == pytest.approx(sum(r["after"]["net"] - r["before"]["net"] for r in rows), abs=1e-6)
    assert s["beam_unresolved_after_m3"] <= s["one_pct_of_his_rc_total_m3"]
    assert all(u["reference"] for u in out["beam_unresolved_named"] + out["nonbeam_unresolved_named"])
    assert not math.isnan(s["beam_m3_after"])
