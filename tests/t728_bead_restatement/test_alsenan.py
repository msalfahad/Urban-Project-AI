"""T-728 on the development villa: the committed restatement equals a rebuild from merged repository files; 116 / 116
rows by arris id, each once, each on a V3.0.72 host (stale 0), none released on a HELD host, none 0, owner trade named;
totals reconcile with the T-697 ledger by hand. Repository files only; nothing is written."""
from __future__ import annotations

import copy
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t728"))
import t728_alsenan as A  # noqa: E402
import t728_rules as R  # noqa: E402


@pytest.fixture(scope="module")
def built():
    return A.build()


@pytest.fixture(scope="module")
def rows(built):
    return {r["edge_id"]: r for r in built["rows"]}


def test_committed_output_reproduces(built):
    assert A.OUT_JSON.read_text(encoding="utf-8") == A.dumps(built)
    assert A.OUT_CSV.read_text(encoding="utf-8") == A.to_csv(built)


def test_pins_and_candidate(built):
    assert built["candidate"] == "ARCH_TAKEOFF_V3.0.72"
    assert set(built["inputs_sha256"]) == set(A.PINS)
    assert built["inputs_sha256"][A.IDX72] == A.sha(A.IDX72)


def test_116_rows_each_once_stale_0(built, rows):
    assert built["rows_restated"] == len(rows) == 116 and built["stale"] == 0
    with (ROOT / A.T723).open(encoding="utf-8") as f:
        flagged = {r["row"].split(":", 1)[1] for r in csv.DictReader(f)
                   if r["piece"] == "T-697" and "RULING_RESTATE" in r["flags"]}
    assert flagged == set(rows)
    i72 = A.index(A.IDX72)
    assert all(r["host_line"] in i72 for r in rows.values())


def test_no_release_on_held_host_none_zero_owner_named(rows):
    for r in rows.values():
        assert r["owner_trade"] == "plaster (B4-09)"
        assert r["bead_state"] != R.RELEASED  # every V3.0.72 host is HELD
        assert r["value"] is None
        if r["bead_state"] == R.HELD_BOUND:
            assert r["high"] > 0 and r["high"] >= r["low"]
        else:
            assert r["low"] is None and r["high"] is None
        assert r["cause"]


def test_host_states_on_v3072(built):
    s = built["summary"]
    assert s["hosts_by_state"] == {"BOUNDED": 14, "BLANK": 4}
    assert s["released_rows"] == 0
    assert s["rows_by_scope_state"] == {"EXTERIOR|HELD_BLANK": 43, "INTERIOR|HELD_BLANK": 6,
                                        "INTERIOR|HELD_BOUND": 67}


def test_interior_reconciles_with_t697_by_hand(built):
    # T-697: interior owner 285.03 + held 14.4528 .. 14.8528 (GF-08 V60 / V61 2 x 3.4364 .. 3.5364, ST-2F 7.58 .. 7.78);
    # D-1F-02 far ring 5.40 (BINDING_OPEN, not a ruling row) stays outside: 285.03 - 5.40 + 14.4528 = 294.0828
    s = built["summary"]["held_bound_m_by_scope"]["INTERIOR"]
    assert (s["low"], s["high"], s["rows"]) == (294.0828, 294.4828, 67)


def test_exterior_blank_hosts_keep_the_ledger_as_text_only(built, rows):
    hosts = built["summary"]["hosts"]
    ref = sum(h["ledger_m_on_blank_host_reference_only"] for h in hosts.values())
    assert round(ref, 4) == 310.6831  # T-697 exterior owner m.l, not a quantity here
    ext = [r for r in rows.values() if r["scope"] == "EXTERIOR"]
    assert len(ext) == 43 and all(r["bead_state"] == R.HELD_BLANK for r in ext)
    assert rows["EXT#GF-CONVEX"]["ledger_ref"].startswith("ledger 66.9 m")
    assert "2.1 .. 2.55" in rows["EXT#GF-CONVEX-PLINTH"]["ledger_ref"]


def test_specific_rows(rows):
    v60 = rows["GF-08#V60"]
    assert (v60["bead_state"], v60["low"], v60["high"]) == (R.HELD_BOUND, 3.4364, 3.5364)
    st2 = rows["ST-2F#V10 + ST-2F#V11"]
    assert (st2["low"], st2["high"], st2["host_state"]) == (7.58, 7.78, R.BOUNDED)
    v06 = rows["1F-01#V06"]
    assert (v06["low"], v06["high"]) == (3.35, 3.35) and "3.35 .. 3.99" in v06["drawing_band"]
    assert "D-39" in v06["cause"]
    assert rows["A-GF-01#GF-01"]["bead_state"] == R.HELD_BLANK
    assert rows["W17#IN"]["cause"].startswith("bead: curved opening")


def test_pending_hosts_named(built):
    p = built["summary"]["pending_rows"]
    assert sum(v for k, v in p.items() if k.startswith("T-314 r3")) == 42
    assert sum(v for k, v in p.items() if "H1" in k) == 4


def test_adverse_row_twice_and_released_on_held(built):
    r = copy.deepcopy(built["rows"])
    with pytest.raises(R.BeadStateError, match="twice"):
        R.check_rows(r + [r[0]])
    bad = copy.deepcopy(r)
    i = next(k for k, x in enumerate(bad) if x["bead_state"] == R.HELD_BOUND)
    bad[i].update(bead_state=R.RELEASED, value=bad[i]["low"], low=None, high=None)
    with pytest.raises(R.BeadStateError, match="RELEASED on a BOUNDED host"):
        R.check_rows(bad)
