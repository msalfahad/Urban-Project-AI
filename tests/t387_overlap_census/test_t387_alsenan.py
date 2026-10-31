"""T-387 committed outputs (candidate of record ARCH_TAKEOFF_V3.0.29, V3_0_29_BOQ_LINES.json 6b5dc44f): the census tables
are internally consistent. These tests read the committed CSV / JSON only (no private input, no network)."""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t387"


def rows(name):
    return list(csv.DictReader(open(D / name, encoding="utf-8")))


@pytest.fixture(scope="module")
def summary():
    return json.loads((D / "summary_t387.json").read_text(encoding="utf-8"))


def test_every_structural_concrete_line_bound_once(summary):
    b = rows("BINDING_T387.csv")
    assert len(b) == summary["structural_concrete_lines"] == 525
    assert len({r["line_id"] for r in b}) == len(b)
    assert Counter(r["binding"] for r in b) == {"BOUND": 525}
    assert all(r["family"] and r["owner_trade"] and r["element_id"] for r in b)
    assert summary["lines_json_sha256"].startswith("6b5dc44f")


def test_held_lines_carry_no_value_and_are_never_summed(summary):
    b = rows("BINDING_T387.csv")
    for r in b:
        if r["status"] != "VALUED":
            assert r["valued_m3"] == ""
    by = defaultdict(float)
    for r in b:
        if r["status"] == "VALUED":
            by[r["family"]] += float(r["valued_m3"])
    for fam, t in summary["families"].items():
        assert by.get(fam, 0.0) == pytest.approx(t["valued_m3"], abs=1e-5)


def test_downgraded_lines_are_held(summary):
    b = {r["line_id"]: r for r in rows("BINDING_T387.csv")}
    held_by_dg = [r for r in b.values() if r["status_reason"].startswith("downgrade DG-")]
    assert held_by_dg and all(r["status"] == "HELD" for r in held_by_dg)


def test_family_totals_match_the_t385_reconciliation(summary):
    f = summary["families"]
    assert f["BEAM"]["valued_m3"] == pytest.approx(66.3179, abs=1e-4)
    assert f["COLUMN"]["valued_m3"] == pytest.approx(28.2155, abs=1e-4)
    assert f["SLAB"]["valued_m3"] == pytest.approx(60.2802, abs=1e-4)
    assert f["FOOTING"]["valued_m3"] + f["STRAP"]["valued_m3"] == pytest.approx(67.6945, abs=1e-4)
    assert f["GROUND_BEAM"]["valued_m3"] + f["GROUND_SLAB"]["valued_m3"] == pytest.approx(44.8661, abs=1e-4)


def test_level_bands_closed_or_named(summary):
    lb = summary["level_bands"]
    assert set(lb) == {"2F", "1F", "GF", "GROUND"}
    for fl, v in lb.items():
        assert v["double_m3"] == 0
    # T-392: the GF gap is no longer an unexplained 0.001356 on B8 but named on the drawing (never netted): the T-146
    # ring-overlap deduction 0.002566 (R-T392-1) + the CB8 end short of S-BEAM 326 0.003406 = GAP 0.005972; CB8's band
    # beyond 326 inside B27 = DOUBLE 0.002767 (R-T392-2); the level band stays FAIL until lane I settles them
    assert lb["GF"]["gap_m3"] == 0
    assert lb["GF"]["t392_named_gap_m3"] == pytest.approx(0.005972, abs=1e-6)
    assert lb["GF"]["t392_named_double_m3"] == pytest.approx(0.002767, abs=1e-6)
    assert lb["GF"]["status"].startswith("FAIL")
    m = rows("MEMBERS_T387.csv")
    assert not [r for r in m if r["verdict"] == "NO_LINE"]           # every unlined member names its successor
    for r in m:
        if r["verdict"] == "OK":
            assert abs(float(r["residual_m3"] or 0.0)) <= 0.001
        if r["verdict"] == "LEDGER_ADJUSTED":
            assert abs(float(r["unexplained_m3"])) <= 0.001


def test_pair_register_never_ok_with_a_held_line():
    reg = rows("PAIR_REGISTER_T387.csv")
    b = {r["line_id"]: r["status"] for r in rows("BINDING_T387.csv")}
    for r in reg:
        if r["status"] in ("OK", "CARRIED_OK", "PASS"):
            assert r["m3"] == "0.000000"
        if r["status"] == "UNDETERMINED":
            assert r["m3"] == "" and r["line_ids"]
            assert all(b[i] == "HELD" for i in r["line_ids"].split())
