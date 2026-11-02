"""T-445 on the development villa (research/agents_t445; committed own-read values, merged ledgers T-233 / T-320 /
T-322 / T-433 / T-469 read only). Pins the 24-pit VERIFIED layer, the candidate lines re-added from their pieces, the
lane I proposal per line id and the -47.055 m3 blinding item split term by term."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t445"))
import blinding_piece_ledger_v1 as B  # noqa: E402
import t445_alsenan as A  # noqa: E402

NOW = "NOW (V3.0.41: no blinding valued)"
PA = "PROPOSAL A (value the 24 VERIFIED pits only)"
PB = "PROPOSAL B (A + FF ESTIMATED 2.352 under the RFI-S08 label, never VERIFIED)"


@pytest.fixture(scope="module")
def run():
    return A.run()


def test_24_pits_re_add_exactly_to_the_verified_layer(run):
    inp, rec, out, _, _ = run
    ps = [p for p in out[NOW]["pieces"] if p["status"] == B.VERIFIED]
    assert len(ps) == 24
    assert sum(p["value"] for p in ps) == pytest.approx(12.7344375, abs=1e-9)
    assert round(sum(p["value"] for p in ps), 6) == 12.734438                       # T-322 / T-320 figure
    assert sum(rec[k]["given_m2"] for k in inp["pits"]) == pytest.approx(0.195625)   # 180C / 180F 0.19 + 10F0 / 1B24
    assert rec["180C"]["given_to"] == {"180F": pytest.approx(0.19)}
    assert rec["10F0"]["given_to"] == {"1B24": pytest.approx(0.005625)}


def test_footing_line_reconciles_to_named_pieces(run):
    _, _, out, _, _ = run
    m = out[NOW]["lines"]["L-98eb2d58075c9eddf1b4"]
    assert m["proposal"] == B.SPLIT and m["value_m3"] == pytest.approx(12.7344375)
    assert abs(m["residual_low"]) <= 5e-7 and abs(m["residual_high"]) <= 5e-7        # 15.179437 (6 dp) re-added
    held = {h["id"]: h for h in m["held"]}
    assert set(held) == {"BEYOND_BOUNDARY", "1B2B:FF"}
    assert held["BEYOND_BOUNDARY"]["high"] == pytest.approx(0.189)
    assert (held["1B2B:FF"]["low"], held["1B2B:FF"]["high"]) == (pytest.approx(2.256), pytest.approx(2.352))
    ff = next(p for p in out[NOW]["pieces"] if p["id"] == "1B2B:FF")
    assert ff["readings"]["at_least"] == pytest.approx(2.070) and ff["value"] is None


def test_other_lines_held_and_the_wall_base_missing(run):
    _, _, out, _, _ = run
    ls = out[NOW]["lines"]
    for lid in ("L-080c97f5f6a92452cd04", "L-7a5214a334ea3559fa2d", "L-35382b18e2e362df3ae6"):
        assert ls[lid]["proposal"] == B.KEEP_HELD and ls[lid]["value_m3"] == 0
    f = next(p for p in out[NOW]["pieces"] if p["id"] == "1B1B:F10+F")
    assert (f["low"], f["high"]) == (pytest.approx(0.480), pytest.approx(0.590))       # owner 3 scenarios
    w = next(p for p in out[NOW]["pieces"] if p["id"] == "BW_BASE")
    assert w["line"] == "MISSING" and w["low"] is None and w["status"] == B.UNMEASURED


def test_blinding_item_split_term_by_term(run):
    _, _, out, _, _ = run
    r = out[NOW]["reference"]
    assert r["residual_m3"] == pytest.approx(-47.055)
    t = {x["piece"]: x for x in r["terms"]}
    assert sum(x["term_low"] for x in r["terms"] if x["status"] == B.VERIFIED) == pytest.approx(-12.7344375)
    assert (t["1B2B:FF"]["term_low"], t["1B2B:FF"]["term_high"]) == (pytest.approx(-2.352), pytest.approx(-2.256))
    assert (t["GB"]["term_low"], t["GB"]["term_high"]) == (pytest.approx(-9.422514), pytest.approx(-4.949374))
    rd = r["rule_difference"]
    assert (rd["term_low"], rd["term_high"]) == (pytest.approx(-26.2573855), pytest.approx(-21.1841715))
    assert [b["piece"] for b in r["beside"]] == ["BEYOND_BOUNDARY"]
    assert rd["contains_unmeasured_pieces"] == ["BW_BASE"]
    assert out[PA]["reference"]["residual_m3"] == pytest.approx(-34.3205625)
    assert out[PB]["reference"]["residual_m3"] == pytest.approx(-31.9685625)


def test_no_value_from_the_reference_plate(run):
    _, _, out, _, _ = run
    for st in out.values():
        for p in st["pieces"]:
            assert p["value"] is None or p["value"] < 25.0                           # no piece carries the plate
            assert "47.055" not in str(p["readings"])
