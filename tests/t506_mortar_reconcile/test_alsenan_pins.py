"""T-506 on the development villa: the committed outputs rebuild byte-identically from the pinned inputs (T-367,
T-453 r2, T-496, line index V3.0.50); the wall-by-wall buckets close both ledgers with residual 0."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t506"
sys.path.insert(0, str(HERE))

import t506_mortar_reconcile as R  # noqa: E402


@pytest.fixture(scope="module")
def built():
    return R.build()


def test_outputs_rebuild_byte_identical(built, tmp_path):
    R.write(*built, tmp_path)
    for name in ("RECONCILIATION_T506.json", "MORTAR_RECONCILIATION_T506.csv", "PRODUCER_ROLES_T506.csv"):
        assert (tmp_path / name).read_bytes() == (HERE / "out" / name).read_bytes(), name


def test_reconciliation_closes(built):
    t = built[0]["totals"]
    # 3.870113 (T-367) = 1.588929 (T-453 PNET) + 0.056050 (2F-W05 RANGE high) + 2.191725 (0.15 m, material base,
    # HELD) + 0.033408 (3.02 m2 of REQUIRED RC lintel faces on 0.15 m walls, concrete)
    assert t[R.PNET]["m3"] == pytest.approx(1.588929, abs=1e-6) and t[R.PNET]["walls"] == 6
    assert t[R.RANGE]["low_m3"] == pytest.approx(0.051035, abs=1e-6)
    assert t[R.RANGE]["m3"] == pytest.approx(0.056050, abs=1e-6)
    assert t[R.HELD015]["m3"] == pytest.approx(2.191725, abs=2e-6) and t[R.HELD015]["walls"] == 17
    assert t[R.HELD015]["m2"] == pytest.approx(201.1421 - 3.02, abs=5e-4)
    assert t[R.LINTEL]["m2"] == pytest.approx(3.02, abs=1e-9)
    assert t["lintel_face_m3_by_t"] == {"0.15": pytest.approx(0.033408, abs=2e-6), "0.20": 0.0}
    assert t["t367_m3"] == pytest.approx(3.870113, abs=2e-6)
    assert t["residual_m3"] == 0.0
    assert built[0]["t453_015_beside_on_contract_net_m3"] == pytest.approx(2.225134, abs=1e-6)


def test_held_walls_named(built):
    import json
    held = sorted(h["wall_id"] for h in built[0]["held_walls"])
    named = json.loads((ROOT / "research/agents_t367/summary.json").read_text(encoding="utf-8"))["black_held_named"]
    assert held == sorted(named) and len(held) == 22          # blank by name in both ledgers, never 0
    assert len(built[0]["rows"]) == 24


def test_producer_census_clean(built):
    c = built[0]["producer_census"]
    assert c["keys_with_two_producers"] == [] and c["reader_divergences"] == []
    assert c["roles"]["T-367|BESIDE"] == 11
    assert c["roles"]["T-489|READER"] == 156 and c["roles"]["T-454|PRODUCER"] == 156
    assert c["rows"] == 1213


def test_t372_as_first_written_would_double(built):
    """wiring T-367's 3.870113 m3 as a producer beside T-453 r2 collides on the 4 computed / range 0.20 m lines."""
    walls, t453, bs, lines, _, _, total = R.load_inputs()
    R.ROLE_RULES[("T-367", "MASONRY_LAYING", "mortar_m3")] = "PRODUCER"
    try:
        census, _ = R.producer_census(list(bs) + R.t367_bindings(walls))
    finally:
        R.ROLE_RULES[("T-367", "MASONRY_LAYING", "mortar_m3")] = "BESIDE"
    assert len(census["keys_with_two_producers"]) == 4
