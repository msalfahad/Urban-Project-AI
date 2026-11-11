"""T-705 on the development villa: the committed readiness output equals a rebuild from merged repository files, every
mapped host is a V3.0.70 line (stale 0), every ledger row is accounted once per piece, HELD rows carry no quantity, the
owner trade is named on every row, and the B4-09 census reconciles to T-697's own summary. Repository files only."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t705"))
import t705_alsenan as A  # noqa: E402
import t705_rules as R  # noqa: E402

R698 = R.R698


@pytest.fixture(scope="module")
def built():
    return A.build()


@pytest.fixture(scope="module")
def i70():
    return A.index(A.IDX70)


def test_committed_output_reproduces(built):
    assert A.OUT_JSON.read_text(encoding="utf-8") == A.dumps(built)
    assert A.OUT_CSV.read_text(encoding="utf-8") == A.to_csv(built)


def test_candidate_pin(built):
    assert built["candidate"] == "ARCH_TAKEOFF_V3.0.70"
    assert built["line_index_sha256"].startswith("6c12da07")       # T-693 LINE_INDEX_V3_0_70 (Gate B PASS 2bfa2fbe)
    assert built["inputs_sha256"][A.IDX70] == built["line_index_sha256"]


def test_stale_zero_and_hosts_present(built, i70):
    assert built["stale"] == 0 and not [r for r in built["rows"] if r["class"] == R698.STALE]
    on = [r for r in built["rows"] if r["class"] in (R698.MAPPED, R698.HOST_CHANGED, R698.PENDING_CHANGE)]
    assert on and all(r["host_line_id"] in i70 for r in on)


def test_guard_fails_when_a_host_is_removed(built, i70):
    victim = next(r for r in built["rows"] if r["class"] == R698.MAPPED)["host_line_id"]
    with pytest.raises(R.ReadinessError):
        R698.check_hosts_present(built["rows"], {k: v for k, v in i70.items() if k != victim})


def test_rows_once_per_piece(built):
    want = {"T-697": 185, "T-701": 2, "T-702": 34, "T-691": 25, "T-700": 21, "T-695": 20}
    assert {k: v["rows"] for k, v in built["pieces"].items()} == want
    for p, n in want.items():
        assert sum(built["pieces"][p]["classes"].values()) == n
    keys = [r["row"] for r in built["rows"]]
    assert len(keys) == len(set(keys))


def test_held_rows_carry_no_quantity_and_no_zero(built):
    for r in built["rows"]:
        if r["held"]:
            assert r["qty"] is None
        a = r["after"]
        if a and a["kind"] in (R.BOUND, R.BLANK):
            assert a["value"] is None
    assert R.check_no_zero(built["rows"])


def test_owner_named_every_row(built):
    assert all(r["owner_family"] and r["owner"] for r in built["rows"])
    fams = {r["owner_family"] for r in built["rows"]}
    assert {"B4-09", "B6-06", "B5", "B5-band", "B2", "B13", "B3/B7-04", "B8", "B1"} == fams


def test_bead_census_matches_t697_summary(built):
    s = A.jload(A.T697S)
    c = built["bead_census_m"]
    for scope, key in (("INTERIOR", "interior"), ("EXTERIOR", "exterior")):
        assert c[scope]["measured_m"] == pytest.approx(s[key]["owner_measured_m"], abs=1e-6)
        assert c[scope]["held_low"] == pytest.approx(s[key]["held_bounded_low_m"], abs=1e-6)
        assert c[scope]["held_high"] == pytest.approx(s[key]["held_bounded_high_m"], abs=1e-6)
        assert c[scope]["held_blank"] == s[key]["held_blank_rows"]
    assert c["INTERIOR"]["measured_m"] == pytest.approx(285.03) and c["EXTERIOR"]["measured_m"] == pytest.approx(310.6831)


def test_beads_wait_on_their_changed_hosts(built):
    by = {r["row"]: r for r in built["rows"]}
    # GF-01 / GF-04 annex hosts: re-bounded by H1 (T-701 R-T701-2) -> the beads wait on it
    gf = [r for r in built["rows"] if r["piece"] == "T-697" and r["host_line_id"] in
          ("L-b152995525ed123ddac9", "L-1ddc23d5657b4c4e4d0d")]
    assert gf and all(r["class"] == R698.PENDING_CHANGE for r in gf)
    ext = [r for r in built["rows"] if r["piece"] == "T-697" and r["host_line_id"] in
           ("L-8bb83e16cc7b104ab88b", "L-b05f70c92405dbcfbe62", "L-d52c4f763b19aedf8b8b")]
    assert len(ext) == 42 and all(r["class"] == R698.PENDING_CHANGE and "T-314" in r["reason"] for r in ext)
    amb = by["T-697:D-1F-02#1F-13|ST-1F"]
    assert amb["class"] == R698.AMBIGUOUS and amb["action"] == R.NONE and len(amb["carriers"]) == 2
    lift = [r for r in built["rows"] if r["owner_family"] == "B6-06"]
    assert len(lift) == 3 and all(r["action"] == R.NONE for r in lift)


def test_hub_order_and_sizes(built):
    h = {x["order"]: x for x in built["hub_order"]}
    assert (h[3]["changed"], h[3]["added"]) == (4, 0)          # GF-01, GF-04, GF-07 band, GF-14 band
    assert (h[4]["added"], h[6]["added"]) == (14, 4)           # B4-09 lines by host
    assert h[7]["changed"] == 2                                # GF-10 / GF-11 wall tile
    assert (h[8]["changed"], h[8]["added"]) == (23, 4)         # 20 WP + 3 falls screeds; 3 pantry pieces + pantry FD
    assert (h[9]["changed"], h[9]["added"]) == (8, 1)          # T-700 form + the B1-03 strap split
    assert h[5]["changed_lines"] == 18


def test_known_line_changes_by_hand(built):
    ch = {(c["piece"], c["line_id"]): c for c in built["line_changes"]}
    assert ch[("T-701", "L-b152995525ed123ddac9")]["after"] == "BOUND 47.960668 .. 66.26068"
    assert ch[("T-701", "L-1ddc23d5657b4c4e4d0d")]["after"] == "BOUND 34.33 .. 43.78"
    assert ch[("T-691", "L-636fd3ff1784a12e653b")]["after"] == "BOUND 115.65646 .. 115.81396"
    assert ch[("T-691", "L-5ce5ba49792e8f9d1f6f")]["after"] == "VALUE 92.925"
    assert ch[("T-700", "L-eac006402d3035da007b")]["after"] == "BOUND 136.900995 .. 163.479489"
    assert ch[("T-700", "L-b4ebff00041d90e03eca")]["after"] == "BOUND 31.05 .. OPEN"


def test_t695_restated_once_by_t700(built):
    rows = [r for r in built["rows"] if r["piece"] == "T-695"]
    assert len(rows) == 20 and all(r["action"] == R.NONE for r in rows)
    form = {r["host_line_id"] for r in built["rows"] if r["piece"] == "T-700"}
    assert {r["host_line_id"] for r in rows} <= form
