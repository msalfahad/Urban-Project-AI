"""T-698 on the development villa: the committed readiness output equals a rebuild from merged repository files, every
mapped host is a V3.0.68 line, every ledger row is accounted once, and the census reconciles to the ledgers' own totals.
Repository files only (no drawing, no Drive)."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t698"))
import t698_alsenan as A  # noqa: E402
import t698_rules as R  # noqa: E402


@pytest.fixture(scope="module")
def built():
    return A.build()


@pytest.fixture(scope="module")
def i68():
    return A.index(A.IDX68)


def test_committed_output_reproduces(built):
    assert A.OUT_JSON.read_text(encoding="utf-8") == A.dumps(built)
    assert A.OUT_CSV.read_text(encoding="utf-8") == A.to_csv(built)


def test_candidate_and_index_pin(built):
    assert built["candidate"] == "ARCH_TAKEOFF_V3.0.68"
    assert built["line_index_sha256"].startswith("fc485958")      # the T-672 index T-696 also pins


def test_every_mapped_host_is_in_the_index(built, i68):
    on_target = [r for r in built["rows"] if r["class"] in (R.MAPPED, R.HOST_CHANGED, R.PENDING_CHANGE)]
    assert on_target and all(r["host_line_id"] in i68 for r in on_target)


def test_guard_fails_when_a_mapped_host_is_absent(built, i68):
    victim = next(r for r in built["rows"] if r["class"] == R.MAPPED)["host_line_id"]
    shrunk = {k: v for k, v in i68.items() if k != victim}
    with pytest.raises(R.ReadinessError):
        R.check_hosts_present(built["rows"], shrunk)


def test_every_ledger_row_once_by_family(built):
    want = {"B4-04": 109 + 18, "B4-04 stage": 18, "B4-05": 271 + 40, "B9-03": 69 + 117 + 132, "B7-01": 14,
            "B7-01 fix": 14}
    assert {k: v["rows"] for k, v in built["families"].items()} == want
    got = Counter(r["family"] if r["ledger"] not in ("T-314 r2 stage", "T-645 FIN.STAIR.FLIGHT") else
                  r["family"] + (" stage" if r["ledger"] == "T-314 r2 stage" else " fix") for r in built["rows"])
    assert dict(got) == want
    for fam, v in built["families"].items():
        assert sum(v["classes"].values()) == v["rows"]


def test_no_stale_and_no_wrong_host(built):
    assert not [r for r in built["rows"] if r["class"] in (R.STALE, R.WRONG)]


def test_named_exceptions(built):
    no_host = [r for r in built["rows"] if r["class"] == R.NO_HOST]
    assert len(no_host) == 13 and all("MISSING" in r["reason"] for r in no_host)
    amb = [r for r in built["rows"] if r["class"] == R.AMBIGUOUS]
    assert [r["row"] for r in amb] == ["PENDING:REVEAL.WINDOW_OUT:W02"]


def test_t314_stage_rebases_clean(built):
    stage = [r for r in built["rows"] if r["ledger"] == "T-314 r2 stage"]
    assert Counter(r["class"] for r in stage) == {R.MAPPED: 3, R.PENDING_LINE: 15}
    assert built["census"]["B4-04"]["rebase_v3_0_61_to_v3_0_68"]["family_lines_changed"] == []


def test_spatter_census_reconciles_to_t349(built):
    c = built["census"]["B4-05"]
    by = c["after_t349_fill_by_host_class"]
    ll = c["after_t349_line_level"]
    for fam in ("INT", "EXT", "PENDING"):
        det = sum(v["determinate_m2"] for k, v in by.items() if k.startswith(fam + "|"))
        assert det == pytest.approx(ll[fam]["determinate"], abs=1e-6)
        assert sum(v["lines"] for k, v in by.items() if k.startswith(fam + "|")) == ll[fam]["lines"]
    # the determinate interior spatter resting on hosts that moved = the T-556 dry-plaster lines (released 217.2081)
    assert by["INT|HOST_CHANGED"]["determinate_m2"] == pytest.approx(217.2081, abs=1e-6)


def test_mesh_census_reconciles_to_t355(built):
    a = built["census"]["B9-03"]["after_t355"]
    by = a["by_host_class"]
    mesh = sum(v["determinate"] for k, v in by.items() if k.startswith("T-355 MESH_BY_WALL|"))
    ties = sum(v["determinate"] for k, v in by.items() if k.startswith("T-355 SHARMAT|"))
    joint = sum(v["determinate"] for k, v in by.items() if k.startswith("T-355 JOINT_MESH_CLASS|"))
    assert mesh == pytest.approx(a["mesh_strip_net_m"], abs=1e-4)
    assert ties == a["sharmat_ties_pcs"] == 182
    assert joint == pytest.approx(sum(a["joint_mesh_by_class_owner_band_m"].values()), abs=1e-4)


def test_wall_membership(built):
    m = built["wall_line_membership"]
    gf015 = m["L-adb393d6db51056d343b"]
    assert gf015["v3_0_45"] == ["CONFIRMED", 0.0] and gf015["v3_0_68"][0] == "RESIDUAL"
    assert gf015["v3_0_68_without_left"] == ["CONFIRMED", 0.0]
    w22 = [r for r in built["rows"] if r["host_named"] == "GF-W22" and r["family"] == "B9-03"]
    assert w22 and all(r["class"] == R.HOST_CHANGED for r in w22)


def test_stair_flight_fix_rows_ready(built):
    fix = [r for r in built["rows"] if r["ledger"] == "T-645 FIN.STAIR.FLIGHT"]
    assert all(r["class"] == R.MAPPED for r in fix)
    assert built["census"]["B7-01"]["after_t645"]["released_lm"] == pytest.approx(13.36392, abs=1e-6)


def test_held_never_zero(built):
    assert R.check_no_zero_for_held(built["rows"])


def test_pending_extract_pinned(built):
    p = json.loads((ROOT / A.PENDING).read_text(encoding="utf-8"))
    assert p["T-314"]["blob"] == built["pending"]["T-314"]["blob"]
    assert built["pending"]["T-314"]["blob"].startswith("040ed5f9")
    assert built["pending"]["T-687"]["blob"].startswith("6252bd8d")
