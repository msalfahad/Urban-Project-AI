"""T-200 on the development villa input (research/agents_t200/ALSENAN_LEVEL_INPUT.json: values, sheet titles,
layers and handles only). The four known level errors of the villa are found from the drawings, the structural tops are
HELD because no sheet prints them, and the pool chain closes at formation -1.50 under the T-183 r2 ruling."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(ROOT / "research" / "agents_t200"))
import t200_alsenan_check as A  # noqa: E402


@pytest.fixture(scope="module")
def runs():
    return A.run()


def _use(res, uid):
    return next(u for u in res["uses"] if u["use_id"] == uid)


def _datum(res, c, k):
    return next(r for r in res["datums"] if r["chain_id"] == c and r["kind"] == k)


def _link(res, c, layer):
    return next(r for r in res["links"] if r["chain_id"] == c and r["layer"] == layer)


def test_four_known_cases_found(runs):
    res = runs["with_t183_ruling"]
    u = _use(res, "A1-POOL-WALL-r1")                      # pool: finished depth taken as the RC wall height
    assert u["code"] == "FINISHED_AS_STRUCTURAL" and "+0.050" in u["detail"]
    assert _use(res, "A1-POOL-WALL-r2")["code"] == "OK"
    u = _use(res, "A2-SILL-W01-r1")                       # W01 / W03 sill read from the +0.15 ground line
    assert u["code"] == "WRONG_REFERENCE" and "-0.850" in u["detail"]
    assert _use(res, "A2-SILL-W01-r3")["code"] == "OK"
    assert _use(res, "A3-NECK-TOP")["code"] == "FINISHED_AS_STRUCTURAL"   # necks to the +1.00 FFL
    assert _use(res, "A3-NECK-FOOT")["code"] == "NEEDS_HELD"              # founding level not printed (Q-21 C)
    for uid in ("A4-STAIR-B20", "A4-STAIR-B23"):                          # beam top taken at the FFL
        u = _use(res, uid)
        assert u["code"] == "FINISHED_AS_STRUCTURAL" and "not proven" in u["sensitivity"]


def test_structural_tops_held_never_a_convention(runs):
    res = runs["with_t183_ruling"]
    for c in ("GF-FLOOR", "1F-FLOOR", "2F-FLOOR", "2F-ROOF", "ANNEX-FLOOR", "ANNEX-ROOF", "GF-EXT-F8"):
        assert not any(r["chain_id"] == c and r["kind"] == "SLAB_TOP" and r["value"] is not None
                       for r in res["datums"]), c
        assert _link(res, c, "FLOOR_BUILD_UP" if "ROOF" not in c else "ROOF_BUILD_UP")["status"] == "HELD"
    # the owner's manual 0.10 floor finishing is shown beside, never used as a structural datum
    assert {m["layer"] for m in res["owner_manual_layers"]} == {"FLOOR_BUILD_UP"}
    assert all(m["thickness"] == pytest.approx(0.10) for m in res["owner_manual_layers"])


def test_storey_and_foundation_datums(runs):
    res = runs["with_t183_ruling"]
    assert _datum(res, "1F-FLOOR", "FFL")["value"] == pytest.approx(5.50)
    assert _datum(res, "2F-FLOOR", "FFL")["value"] == pytest.approx(9.70)   # P7757 and ST7757 SH02 agree
    assert _link(res, "2F-ROOF", "PARAPET_HEIGHT")["thickness"] == pytest.approx(0.50)
    assert _datum(res, "GF-EXT-F8", "FOOTING_BOTTOM")["status"] == "HELD"
    assert _link(res, "GF-EXT-F8", "EXCAVATION_DEPTH")["status"] == "HELD"
    assert res["bounds"][0]["result"].startswith("OPEN")                   # 'not less than 1.5 m' stays a limit


def test_pool_chain_and_the_two_document_conflict(runs):
    res = runs["with_t183_ruling"]
    assert _link(res, "POOL", "RC_WALL_HEIGHT")["thickness"] == pytest.approx(1.20)
    assert _datum(res, "POOL", "POOL_BASE_UNDERSIDE")["value"] == pytest.approx(-1.30)
    assert _datum(res, "POOL", "FORMATION")["value"] == pytest.approx(-1.50)
    assert _link(res, "POOL", "EXCAVATION_DEPTH")["thickness"] == pytest.approx(1.50)
    raw = runs["as_printed"]
    assert _link(raw, "POOL", "BASE_THICKNESS")["status"] == "CONFLICT"     # arch cut 0.15 vs ST detail 0.40
    assert _datum(raw, "POOL", "FORMATION")["status"] == "CONFLICT"
