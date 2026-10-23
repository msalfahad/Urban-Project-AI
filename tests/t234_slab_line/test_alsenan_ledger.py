"""T-234 Alsenan CONC.SLAB ledger from committed inputs only (T-139 PANELS.csv from Drive 'ST7757 dxf.dxf' sha
9f9d1179; freelancer cells from tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json). Re-runs the check without
writing and pins the engineering results (development villa; not an accuracy claim)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t234"
sys.path.insert(0, str(HERE))
import t234_alsenan_check as C  # noqa: E402

SUM, ROWS, LINE, PART = C.main(write=False)


def test_every_panel_once_and_line_total():
    assert SUM["panels"] == 62 and len({r[0] for r in ROWS[1:]}) == 62
    assert SUM["measured_m3"] == pytest.approx(60.280396, abs=1e-6)
    by = SUM["by_storey"]
    assert (by["GF"]["n"], by["1F"]["n"], by["2F"]["n"]) == (33, 22, 7)
    assert by["GF"]["m3"] == pytest.approx(33.06952, abs=1e-6)
    assert by["1F"]["m3"] == pytest.approx(19.756576, abs=1e-6)
    assert by["2F"]["m3"] == pytest.approx(7.4543, abs=1e-6)


def test_thickness_basis_note_or_tag_only():
    bases = {(r[3], r[4]) for r in ROWS[1:]}
    assert bases == {("0.16", "GENERAL_NOTE"), ("0.16", "TAG"), ("0.18", "TAG")}
    assert sum(1 for r in ROWS[1:] if r[4] == "TAG") == 5          # GF x2, 1F x1 'T 16'; 2F tank x2 'T 18'


def test_sunken_panels_full_depth():
    sunk = [r for r in ROWS[1:] if r[5] == "yes"]
    assert len(sunk) == 6 and SUM["sunken_m2"] == pytest.approx(24.7964, abs=1e-4)
    assert all(r[3] == "0.16" for r in sunk)


def test_openings_once_and_partition():
    assert SUM["openings_not_deducted"] == [] and len(SUM["openings"]) == 6
    assert SUM["partition"] == {"GF": "PASS", "1F": "PASS", "2F": "PASS"}
    assert SUM["status"] == "CLOSABLE" and SUM["held"] == []


def test_released_reconciled_to_named_causes():
    rel = SUM["released"]
    assert rel["total"] == pytest.approx(61.551385, abs=1e-6)
    for fl, v in rel["per_floor"].items():
        assert abs(v["residual"]) < 5e-4, fl                      # 1F -0.000243 = panel areas rounded to 4 dp
    assert rel["per_floor"]["2F"]["diff"] == pytest.approx(0.68951, abs=1e-5)   # tag spread 0.625 + 2 faces 0.0645


def test_released_tag_spread_is_refused_by_the_rule():
    import slab_line as SL
    with pytest.raises(ValueError, match="general note"):
        SL.panel_thickness(dict(id="2F-x", t_basis="SHEET_UNIFORM", t_m=0.18), 0.16)


def test_freelancer_reconciled():
    fr = SUM["freelancer"]
    assert fr["total"] == pytest.approx(59.8174, abs=1e-6)
    assert SUM["measured_m3"] - fr["total"] == pytest.approx(0.462996, abs=1e-5)
    for fl, v in fr["per_floor"].items():
        assert abs(v["residual"]) < 1e-9, fl
