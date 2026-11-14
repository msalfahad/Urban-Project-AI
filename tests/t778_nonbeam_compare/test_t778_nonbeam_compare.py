"""T-778 NON-BEAM concrete candidate vs freelancer by element and named cause (NONBEAM_COMPARE_V1, proposed).

Normal: a synthetic villa (not Alsenan) splits a counted member difference exactly into COUNT / SECTION / HEIGHT and the
column height into JOINT_HEAD + STOREY_BASE; the Alsenan candidate (V3.0.81 + T-761 / T-757 fix rows) closes every
family and the whole-trade bridge to named causes with residual below 1 %. Adverse: missing / negative dimensions, a
member list that does not match its count, a figure that is no printed section, a HELD line with no figure, and equal
totals hiding offsetting causes are refused or exposed. Reads committed inputs only; writes nothing."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t778"))
import nonbeam_vs_freelancer as N  # noqa: E402


# ------------------------------------------------------------------ normal (synthetic villa)
def test_count_section_height_sum_exactly():
    c, s, h = N.split_count_section_height(3, [0.10, 0.10, 0.125], [4.0, 4.0, 3.5], 2, 0.125, 3.4)
    assert c + s + h == pytest.approx(0.10 * 4 * 2 + 0.125 * 3.5 - 2 * 0.125 * 3.4, abs=1e-12)
    assert c == pytest.approx(0.125 * 3.4)


def test_column_joint_head_is_his_head_times_section():
    j, r = N.split_column_height([0.10, 0.20], [4.50, 4.50], 3.75)
    assert j == pytest.approx(0.30 * 0.75) and r == pytest.approx(0.0, abs=1e-12)
    j, r = N.split_column_height([0.10], [3.875], 3.75)            # annex column under a lower roof
    assert r == pytest.approx(0.10 * (3.875 - 4.50))


def test_equal_totals_with_offsetting_causes_are_exposed():
    # one more drawn column (count +) and a frame that stops 0.75 short (height -): totals equal, two causes named
    c, s, h = N.split_count_section_height(2, [0.10, 0.10], [3.0, 3.0], 1, 0.10, 6.0)
    assert c + s + h == pytest.approx(0.0, abs=1e-12)
    assert c == pytest.approx(0.6) and h == pytest.approx(-0.6)


def test_units_mm_do_not_mix():
    a = N.split_count_section_height(1, [0.1], [4.0], 1, 0.125, 3.5)
    b = N.split_count_section_height(1, [1e5], [4000], 1, 1.25e5, 3500)
    assert sum(b) / 1e9 == pytest.approx(sum(a), abs=1e-12)


# ------------------------------------------------------------------ adverse
@pytest.mark.parametrize("bad", [(1, [None], [4.0], 1, 0.1, 3.0), (1, [0.1], [-4.0], 1, 0.1, 3.0),
                                 (2, [0.1], [4.0], 1, 0.1, 3.0), (1, [0.1], [4.0], 1, None, 3.0)])
def test_missing_dimension_refused_never_zero(bad):
    with pytest.raises(ValueError):
        N.split_count_section_height(*bad)


def test_figure_that_is_no_printed_section_is_refused():
    assert N.schedule_section(0.5625, 4.50) == 0.125
    assert N.schedule_section(0.47, 4.50) is None
    with pytest.raises(ValueError):
        N.column_member(dict(line_id="X", basis="", m3=0.47), "1F")


def test_held_line_without_figure_refused():
    L = {"lines": [dict(line_id="L-x", item_code="STR.CONC.NECK", class_="HELD")]}
    L["lines"][0]["class"] = "HELD"
    L["lines"][0]["element_id"] = "P-C:NECK:COL:SH10:C1@0,0"
    with pytest.raises(ValueError):
        N.engine_lines(L, {}, "STR.CONC.NECK")


# ------------------------------------------------------------------ Alsenan (committed inputs)
@pytest.fixture(scope="module")
def built():
    return N.build()


def test_every_family_closes_below_one_percent(built):
    for f in built["families"]:
        assert abs(f["residual_m3"]) <= N.MATERIALITY * f["his_m3"], f["family"]
        assert set(f["verdicts"].values()) <= {"ENGINE_RIGHT", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "UNRESOLVED", "AGREE"}


def test_bridge_closes_and_pins(built):
    assert built["his_rc_total_m3"] == pytest.approx(352.436075)
    assert built["engine_concrete_m3"] == pytest.approx(406.7941, abs=1e-3)
    assert abs(built["bridge_residual_m3"]) < 1e-3
    fam = {f["family"]: f for f in built["families"]}
    assert fam["STR.CONC.FOOTING"]["causes"]["F-1 F3 count (2 drawn outlines vs his 1)"] == pytest.approx(0.672)
    assert fam["STR.CONC.GROUND_SLAB"]["diff_m3"] == pytest.approx(-7.9091, abs=1e-4)
    assert fam["STR.CONC.POOL"]["causes"]["P-1 pump room walls + floor not drawn"] == pytest.approx(-3.48)


def test_lines_disjoint_from_beams_and_boundary(built):
    ids = [l for f in built["families"] for l in f["lines"]]
    assert len(ids) == len(set(ids))                                   # every line once
    import json
    beam = {x["line_id"] for x in json.load(open(ROOT / N.T777))["lines"]}
    t776 = {r["line_id"] for r in json.load(open(ROOT / N.T776))["rows"]}
    assert not (set(ids) & beam) and not (set(ids) & t776)


def test_joint_head_mirrors_the_beam_split(built):
    j = built["beams_plus_columns_joint"]
    assert j["t778_C4"] > 0 > j["t777_C2c2"]                          # same joint volume, opposite lines


def test_outputs_reproduce():
    import json
    d = N.build()
    js = json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    assert (N.OUT / "NONBEAM_CAUSES.json").read_text(encoding="utf-8") == js
    assert (N.OUT / "NONBEAM_CAUSES.md").read_text(encoding="utf-8") == N.write_md(d)
