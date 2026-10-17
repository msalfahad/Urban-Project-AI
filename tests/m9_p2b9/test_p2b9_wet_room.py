"""Phase 2B-9 acceptance: worked example 2, a 4.00 x 3.00 m bathroom (door D1 1.00 x 2.20) under ARCH_TAKEOFF_V2.8,
every height from the drawing (section F.C.L. +3.00 / U/S SLAB +3.00, the schedule's door height). The owner's
wet-area rules (UP-FIN-WALL-001 full-height porcelain, UP-CER-004 no skirting, UP-FIN-PAINT-001 no paint over it) and
the membrane system (1 x 10 m rolls, 0.10 m laps, 0.20 m upturn: UP-WP-001..004) give the Phase 2B-3 WP-B proof
(research/urban_m9_p2b3/WP2_BATHROOM_3x4_PROOF.md): 14.80 m2 proven, 2.72 m2 laps, 17.52 installed, 17.80 consumed,
2 rolls, 0.28 m2 waste. Corners (4) and penetrations stay withheld: no detail is drawn, none is invented."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

pytest.importorskip("ezdxf")

import p2b9_fixtures as F                                     # noqa: E402
import p2b9_run as R                                          # noqa: E402
import p2b9_truth as T                                        # noqa: E402

A = 1e-6


@pytest.fixture(scope="module")
def bath(tmp_path_factory):
    work = tmp_path_factory.mktemp("p2b9_wet")
    return R.run(F.example2(work / "e2.dxf"), work / "o_e2")


def test_wet_room_finishes_from_the_drawing(bath):
    assert R.net(bath, "FIN.FLOOR.WET_TILE", "floor") == pytest.approx(T.E2_FLOOR, abs=A)
    tile = R.the(bath, "FIN.WALL.TILE", "wall_tile")
    assert tile["measured_net"] == pytest.approx(T.E2_WALL_TILE, abs=A)
    assert R.net(bath, "FIN.PLASTER", "plaster") == pytest.approx(T.E2_PLASTER, abs=A)
    for code, el in (("FIN.SKIRTING", "skirting"), ("FIN.PAINT", "paint above wall tile")):
        ln = R.the(bath, code, el)
        assert (ln["evidence_state"], ln["measured_net"]) == ("NOT_APPLICABLE_WITH_EVIDENCE", None)
    h = R.room_heights(bath, "Bathroom / W.C.")
    assert (h["PLASTER"]["governing"], h["PAINT"]["governing"]) == ("SECTION", "SECTION")
    assert R.missing(bath) == []


def test_wet_room_waterproofing_matches_the_v25_proof(bath):
    assert R.net(bath, "FIN.WP.FLOOR", "wp_floor") == pytest.approx(T.E2_FLOOR, abs=A)
    assert R.net(bath, "FIN.WP.WALL_UPTURN", "wp_wall_upturn") == pytest.approx(T.E2_WP_UPTURN, abs=A)
    assert R.net(bath, "FIN.WP.DOORWAY", "doorway") == pytest.approx(T.E2_WP_DOORWAY, abs=A)
    a = R.load(bath, "WATERPROOFING_SCHEDULE.json")["waterproofing"]["areas"]
    assert len(a) == 1
    a = a[0]
    assert a["proven_subtotal"]["total_m2"] == pytest.approx(T.E2_WP_SUBTOTAL, abs=A)
    assert (a["laps_m2"], a["B_installed_m2"], a["consumed_m2"], a["true_waste_m2"]) == (
        pytest.approx(T.E2_WP_LAPS, abs=A), pytest.approx(T.E2_WP_INSTALLED, abs=A),
        pytest.approx(T.E2_WP_CONSUMED, abs=A), pytest.approx(T.E2_WP_WASTE, abs=A))
    assert a["roll_packing"]["first_fit_decreasing"] == T.E2_WP_ROLLS and a["direction"] == "ALONG_Y"
    # not invented: the corners have no detail, the penetrations are not drawn, the junction is open
    assert (a["corners"]["count"], a["corners"]["state"], a["corners"]["quantity"]) == (T.E2_CORNERS, "WITHHELD",
                                                                                         None)
    assert (a["penetrations"]["state"], a["penetrations"]["quantity"]) == ("NOT_SHOWN", None)
    assert a["junction"]["state"] == "UNRESOLVED" and a["junction"]["rolls_range"] == [2, 3]
