"""T-698 on the development villa: the committed readiness output equals a rebuild from merged repository files, every
mapped host is a V3.0.69 line (r2; r1 mapped V3.0.68), every ledger row is accounted once, and the census reconciles to the ledgers' own totals.
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
def i69():
    return A.index(A.IDX69)


def test_committed_output_reproduces(built):
    assert A.OUT_JSON.read_text(encoding="utf-8") == A.dumps(built)
    assert A.OUT_CSV.read_text(encoding="utf-8") == A.to_csv(built)


def test_candidate_and_index_pin(built):
    assert built["candidate"] == "ARCH_TAKEOFF_V3.0.69"
    assert built["line_index_sha256"].startswith("e908a5f1")      # the T-687 V3.0.69 index (Gate B PASS 0b6d1bc2)


def test_every_mapped_host_is_in_the_index(built, i69):
    on_target = [r for r in built["rows"] if r["class"] in (R.MAPPED, R.HOST_CHANGED, R.PENDING_CHANGE)]
    assert on_target and all(r["host_line_id"] in i69 for r in on_target)


def test_guard_fails_when_a_mapped_host_is_absent(built, i69):
    victim = next(r for r in built["rows"] if r["class"] == R.MAPPED)["host_line_id"]
    shrunk = {k: v for k, v in i69.items() if k != victim}
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
    assert built["census"]["B4-04"]["rebase_v3_0_61_to_v3_0_69"]["family_lines_changed"] == []


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
    by = a["by_host_class_strip_and_sharmat"]
    mesh = sum(v["determinate"] for k, v in by.items() if k.startswith("T-355 MESH_BY_WALL|"))
    ties = sum(v["determinate"] for k, v in by.items() if k.startswith("T-355 SHARMAT|"))
    assert mesh == pytest.approx(a["mesh_strip_net_m"], abs=1e-4)
    assert ties == a["sharmat_ties_pcs"] == 182
    assert not any(k.startswith("T-355 JOINT_MESH_CLASS|") for k in by)     # the band pair is never summed here


def test_joint_mesh_is_a_held_band_pair_reconciled_to_t355(built):
    """Gate A defect 2: owner band .. drawing band, neither chosen; never 'determinate'; MIXED split HELD."""
    jm = built["census"]["B9-03"]["after_t355"]["joint_mesh"]
    assert R.check_census_not_determinate(jm)
    t = jm["total"]
    assert t["rows"] == 132
    assert t["owner_band_m"] == pytest.approx(511.693869, abs=1e-6)
    assert t["drawing_band_m"] == pytest.approx(758.345928, abs=1e-6)
    hc = jm["by_host_class"]
    assert hc["MAPPED"]["owner_band_m"] == pytest.approx(442.199025, abs=1e-6)
    assert hc["HOST_CHANGED"]["owner_band_m"] == pytest.approx(69.494844, abs=1e-6)
    t355 = json.loads((ROOT / A.T355_SUM).read_text(encoding="utf-8"))["joint_mesh_by_class"]
    for c, v in jm["by_joint_class"].items():
        assert v["owner_band_m"] == pytest.approx(t355[c]["owner_band_m"], abs=1e-4)
        assert v["drawing_band_m"] == pytest.approx(t355[c]["drawing_band_m"], abs=1e-4)
        assert v["rows"] == t355[c]["sides"]
    assert jm["by_joint_class"]["MIXED"]["split"].startswith("HELD")
    joint = [r for r in built["rows"] if r["ledger"] == "T-355 JOINT_MESH_CLASS"]
    assert all(r["qty"] is None and r["held"] and r["band_pair"] for r in joint)
    assert all("HELD BAND PAIR" in r["ledger_state"] for r in joint)
    assert all("class split HELD" in r["ledger_state"] for r in joint if r["joint_class"] == "MIXED")


def test_joint_mesh_held_joints_carried_never_plain_zero(built):
    """Gate A defect 1: every joint-mesh row carries held_joints_owner / _drawing; 74 rows / 302 joints held; the 59
    rows of 0 m (owner band) with held joints are HELD, never a plain 0 (e.g. GF-W02 INT-A: 0.0 m + 1 held joint)."""
    joint = [r for r in built["rows"] if r["ledger"] == "T-355 JOINT_MESH_CLASS"]
    assert all(set(r["held_parts"]) == {"held_joints_owner", "held_joints_drawing"} for r in joint)
    held = [r for r in joint if any(r["held_parts"].values())]
    assert len(held) == 74
    assert sum(r["held_parts"]["held_joints_owner"] for r in joint) == 302
    assert sum(r["held_parts"]["held_joints_drawing"] for r in joint) == 302
    zero = [r for r in held if r["lo"] == 0]          # owner band 0.0 m + held joints (34 of them 0.0 on both bands)
    assert len(zero) == 59 and sum(1 for r in zero if r["hi"] == 0) == 34 and all(r["qty"] is None and r["held"] and "held joints" in r["ledger_state"] for r in zero)
    w02 = next(r for r in joint if r["row"] == "GF-W02|GF|WB-FL0007-FL0008#1|INT-A")
    assert w02["qty"] is None and w02["held_parts"] == {"held_joints_owner": 1, "held_joints_drawing": 1}
    jm = built["census"]["B9-03"]["after_t355"]["joint_mesh"]["total"]
    assert (jm["held_rows"], jm["held_joints_owner"], jm["held_joints_drawing"]) == (74, 302, 302)
    assert R.check_held_parts(built["rows"]) and R.check_band_pair(built["rows"])
    csv_rows = A.to_csv(built).splitlines()
    assert "held_joints_owner" in csv_rows[0]


def test_row_total_states_the_t135_rows(built):
    rt = built["row_total"]
    assert rt["rows"] == 802 == len(built["rows"])
    assert rt["without_t135_disposition"] == 788 and rt["b7_01_t135_disposition_rows"] == 14


def test_t687_pending_rows_resolved_on_v3_0_69(built):
    """r1 held 47 rows as MAPPED_PENDING_CHANGE on T-687 hosts; T-687 is merged: none waits on it now, each T-687
    after-state equals V3.0.69, and only the T-314 r2 stage (not merged) still holds rows pending."""
    assert built["t687_resolution"] == {"rows": 34, "changed": 16, "added": 18, "all_after_states_equal_v3_0_69": True}
    pend = [r for r in built["rows"] if r["class"] == R.PENDING_CHANGE]
    assert pend and all("T-687" not in r["reason"] for r in pend)
    assert all("T-314 r2" in r["reason"] for r in pend)
    on687 = [r for r in built["rows"] if "resolved by T-687 merged" in r["reason"] or "T-687 merged, V3.0.69" in r["reason"]]
    assert len(on687) == 47
    assert built["families"]["B4-05"]["classes"][R.PENDING_CHANGE] == 46
    assert built["v3_0_68_to_v3_0_69"]["changed"] == 15 and built["v3_0_68_to_v3_0_69"]["removed"] == 0


def test_wall_membership(built):
    m = built["wall_line_membership"]
    gf015 = m["L-adb393d6db51056d343b"]
    assert gf015["v3_0_45"] == ["CONFIRMED", 0.0] and gf015["v3_0_69"][0] == "RESIDUAL"
    assert gf015["v3_0_69_without_left"] == ["CONFIRMED", 0.0]
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
