"""T-571 on the training villa: the 60 masonry openings of the V3.0.58 lintel lines (= merged T-453 r2 ledger, sha
pinned) + the 8 census openings not in a masonry wall (census r3, sha pinned). No private file is needed: the freelancer
side is checked on the committed count file (numbers only).

ENGINE, owner manual method, b = 0.15 (hand, from the ledger widths):
  1.20 m: widths 0.50 x1, 0.60 x10, 0.80 x12, 0.90 x7 = 30 (GF 13, 1F 14, 2F 3)
  1.50 m: 1.00 x16, 1.20 x4 = 20 (GF 9, 1F 6, 2F 5)
  2.50 m: 1.30, 1.50 x2, 1.55 x3, 1.95 x2, 2.00 = 9 (GF 5, 1F 4)
  3.00 m: 2.45 (W14) = 1; 4.00 m: 0; FLAGGED (> 4.00): 0  -> AT_MOST 60 nr, lm beside 36.0 / 30.0 / 22.5 / 3.0 / 0 = 91.5
  ESTABLISHED (16 REQUIRED): 1.20 x9 (D-1F-04 / -07 / -08 / -10, D-2F-03, D-GF-10 / -11 / -12, W18), 1.50 x5 (D-1F-02,
  D-1F-03, D-2F-01, D-GF-06, D-GF-13), 2.50 W15, 3.00 W14 = 16 nr, 23.8 lm. Cross-check: the merged T-516 company-0.15
  pieces on the five white REQUIRED lintels (D-2F-01 1.50, D-GF-06 1.50, W14 3.00, W15 2.50, W18 1.20) are the same.
  Project MIN 0.40 beside (drawing detail): 1.50 x11, 2.50 x45, 3.00 x3, 4.00 x1 = 60 nr, 142.0 lm.
FREELANCER (his blockwork opening-deduction rows; he has NO lintel row): 54 openings -> 1.20 x27, 1.50 x17, 2.50 x8,
  3.00 x1, 4.00 x1 (his 3.15 m = W17) = 54 nr, 84.9 lm.
DIFFERENCE ours - his (AT_MOST): +3 @1.20, +3 @1.50, +1 @2.50, 0 @3.00, -1 @4.00 = +6 nr, causes:
  WIDTH_READ 3 (D-GF-03, D-GF-09 0.90 drawn vs his 1.00; P-GF-01 0.90 between both jambs vs 1.10 on the face where a
  cross wall ends): +3 @1.20, -3 @1.50; NOT_IN_MASONRY W17 (no masonry host in the merged fill; his 3.15 deducted from
  block): -1 @4.00; ENGINE_ONLY 7 (+6 @1.50, +1 @2.50).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t571"))

import t571_lintel_count as T  # noqa: E402

OUT = ROOT / "research" / "agents_t571" / "out" / "T571_LINTEL_COUNT.json"


@pytest.fixture(scope="module")
def doc():
    return T.build()


@pytest.fixture(scope="module")
def committed():
    return json.loads(OUT.read_text())


def _col(t, L):
    return sum(t["at_most"][L].values())


def test_engine_records_pinned_and_complete():
    recs = T.engine_records()
    ids = [r["id"] for r in recs]
    assert len(ids) == len(set(ids)) == 68
    st = [r["state"] for r in recs]
    assert st.count(T.REQUIRED) == 16 and st.count(T.HELD) == 42 and st.count(T.FLAGGED) == 2
    assert st.count(T.NO_LINTEL) == 8


def test_engine_owner_015_by_hand(doc):
    t = doc["engine_owner_0.15"]
    assert [_col(t, L) for L in T.STOCK] == [30, 20, 9, 1, 0]
    assert t["at_most"][1.2] == {"GF": 13, "1F": 14, "2F": 3, "UNSPLIT": 0}
    assert t["at_most"][1.5] == {"GF": 9, "1F": 6, "2F": 5, "UNSPLIT": 0}
    assert t["at_most"][2.5] == {"GF": 5, "1F": 4, "2F": 0, "UNSPLIT": 0}
    assert t["total_at_most_nr"] == 60 and t["total_established_nr"] == 16
    assert [sum(t["established"][L].values()) for L in T.STOCK] == [9, 5, 1, 1, 0]
    assert t["flagged"] == [] and len(t["no_lintel"]) == 8
    assert sum(t["lm_beside_at_most"].values()) == pytest.approx(91.5)
    est_lm = sum(L * sum(t["established"][L].values()) for L in T.STOCK)
    assert est_lm == pytest.approx(23.8)


def test_engine_matches_t516_company_pieces_on_white_required():
    recs = {r["id"]: r for r in T.engine_records()}
    for oid, piece in (("D-2F-01", 1.5), ("D-GF-06", 1.5), ("W14", 3.0), ("W15", 2.5), ("W18", 1.2)):
        assert T.piece(recs[oid]["width_m"])["piece_m"] == piece


def test_engine_project_min_040_beside(doc):
    t = doc["engine_project_min_0.40"]
    assert [_col(t, L) for L in T.STOCK] == [0, 11, 45, 3, 1]
    assert sum(t["lm_beside_at_most"].values()) == pytest.approx(142.0)


def test_governing_precast_not_applicable_not_zero(doc):
    assert doc["governing_precast_on_this_villa"].startswith("NOT_APPLICABLE (not 0)")


def test_committed_engine_tables_equal_rebuild(doc, committed):
    for k in ("engine_owner_0.15", "engine_project_min_0.40"):
        a = json.loads(json.dumps(T._keyfix(doc[k])))
        assert a == committed[k]


def test_committed_freelancer_counts_and_closure(committed):
    f = committed["freelancer_owner_0.15"]
    assert [sum(f["at_most"][str(L)].values()) for L in T.STOCK] == [27, 17, 8, 1, 1]
    assert f["total_at_most_nr"] == 54
    assert sum(f["lm_beside_at_most"].values()) == pytest.approx(84.9)
    for tag in ("owner_0.15", "project_min_0.40"):
        r = committed[f"reconciliation_{tag}"]
        d = r["table_difference_nr_by_length"]
        c = r["causes_nr_by_length"]
        assert {L: sum(c[k][L] for k in c) for L in d} == d
    r = committed["reconciliation_owner_0.15"]
    assert r["table_difference_nr_by_length"] == {"1.2": 3, "1.5": 3, "2.5": 1, "3.0": 0, "4.0": -1}
    assert r["causes_nr_by_length"]["WIDTH_READ"] == {"1.2": 3, "1.5": -3, "2.5": 0, "3.0": 0, "4.0": 0}
    assert r["causes_nr_by_length"]["NOT_IN_MASONRY"]["4.0"] == -1
    assert sum(r["causes_nr_by_length"]["ENGINE_ONLY"].values()) == 7
    assert sum(r["causes_nr_by_length"]["OTHER_ONLY"].values()) == 0
    assert r["held_or_flagged_in_pairs_nr"] == 40                        # 13 REQUIRED + 40 held + W17 = his 54


def test_committed_pairs_carry_each_opening_once(committed):
    rows = committed["pairs_owner_0.15"]
    ours = [r["ours"] for r in rows if r.get("ours")]
    theirs = [r["theirs"] for r in rows if r.get("theirs")]
    assert len(ours) == len(set(ours)) == 68
    assert len(theirs) == len(set(theirs)) == 54
    w17 = [r for r in rows if r.get("ours") == "W17"][0]
    assert w17["cause"] == "NOT_IN_MASONRY" and w17["piece_theirs"] == 4.0
    wr = sorted(r["ours"] for r in rows if r["cause"] == "WIDTH_READ")
    assert wr == ["D-GF-03", "D-GF-09", "P-GF-01"]


def test_stale_ledger_refused(monkeypatch):
    monkeypatch.setitem(T.PINS, "ledger_sha16", "0" * 16)
    with pytest.raises(T.CountError, match="stale"):
        T.engine_records()
