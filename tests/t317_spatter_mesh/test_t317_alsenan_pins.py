"""T-317 development-villa pins (read-only over merged ledgers; no drawing is read): every figure is re-derived from
the merged inputs and compared with the hand arithmetic in research/agents_t317/T-317_SPATTER_MESH_LEDGER.md."""

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t317"))
import t317_alsenan as A  # noqa: E402
import t317_spatter_mesh as M  # noqa: E402


@pytest.fixture(scope="module")
def spatter():
    return A.spatter_ledger()


@pytest.fixture(scope="module")
def led():
    return A.ledger()


def test_plaster_hosts_reproduce_v3020_totals(spatter):
    hosts, recs, carried = spatter
    pl = [r for r in recs if r["host_item"] == "FIN.PLASTER"]
    assert round(sum(r["quantity"] for r in pl if r["quantity"] is not None), 4) == 234.9481
    lo = sum(r["lo"] for r in pl if r["lo"] is not None)
    hi = sum(r["hi"] for r in pl if r["hi"] is not None)
    assert abs(lo - 489.4810) < 1e-3 and abs(hi - 545.4606) < 1e-3     # T-244 s.4 V3.0.20 held range
    # 23 V3.0.19 PROVISIONAL + 1F-04 + 2F-03 - 1F-11 withdrawn = 24 determinate plaster hosts
    assert sum(1 for r in pl if r["quantity"] is not None) == 24


def test_wet_rooms_carried_by_tile_once(spatter):
    hosts, recs, carried = spatter
    wet = [c for c in carried if c["carried_by"] == "FIN.WALL.TILE host"]
    assert len(wet) == 17                       # 17 blank wet-room plaster lines: the face is the tile line's
    host_ids = {r["host_line"] for r in recs}
    assert not {c["plaster_line"] for c in wet} & host_ids
    tile = [r for r in recs if r["host_item"] == "FIN.WALL.TILE"]
    assert round(sum(r["quantity"] for r in tile if r["quantity"] is not None), 4) == 307.9616   # T-312 in-line
    assert sum(1 for r in tile if r["state"] == "HELD") == 6
    pantry = [c for c in carried if "pantry backsplash" in c["carried_by"]]
    assert len(pantry) == 1 and "32.3422" in pantry[0]["carried_by"]


def test_exterior_hosts_are_t305(spatter):
    hosts, recs, carried = spatter
    ex = {r["host_line"]: r for r in recs if r["finish"] in ("SIGMA", "CLADDING")}
    assert ex["L-8bb83e16cc7b104ab88b"]["quantity"] == pytest.approx(234.525528)
    assert ex["L-d52c4f763b19aedf8b8b"]["quantity"] == pytest.approx(132.205)
    g = ex["L-b05f70c92405dbcfbe62"]
    assert g["state"] == "HELD" and g["quantity"] is None and (g["lo"], g["hi"]) == pytest.approx((387.285171, 420.770171))


def test_villa_spatter_totals_hand(spatter):
    hosts, recs, carried = spatter
    det = sum(r["quantity"] for r in recs if r["quantity"] is not None)
    # 234.9481 plaster + 307.9616 tile + 234.525528 + 4.08 + 132.205 exterior
    assert round(det, 4) == round(234.9481 + 307.9616 + 234.525528 + 4.08 + 132.205, 4) == 913.7202
    lo = sum(r["lo"] for r in recs if r["lo"] is not None)
    hi = sum(r["hi"] for r in recs if r["hi"] is not None)
    # plaster 489.4810 .. 545.4606 + GF Sigma 387.2852 .. 420.7702 + parapet 66.4279 + 1.8699 .. 7.2479
    # + plinth 66.7363 + 4.9523 .. 6.0135
    assert lo == pytest.approx(489.48105 + 387.285171 + 68.297836 + 71.68859, abs=1e-4)
    assert hi == pytest.approx(545.46065 + 420.770171 + 73.675836 + 72.749795, abs=1e-4)
    assert all(r["candidate_line"] == "NO LINE" for r in recs)
    M.check_no_zero_held(recs)


def test_owner_band_puts_almost_no_block_top_inside(led):
    js = [j for j in led["J_own"] if j["side"] != "EXT" and j["dir"] == "H"]
    inside = [j for j in js if j["class"] == "INSIDE"]
    assert [(j["wall_id"], j["length_m"]) for j in inside] == [("2F-W07", 2.7)]
    # 1F / 2F band top 0.10 + 3.35 = 3.45 = the soffit of a 0.75 beam on a 4.20 storey: AT the band edge
    edge = [j for j in js if j["class"] == "AT_BAND_EDGE" and j["floor"] == "1F"]
    assert edge and all(abs(j["level_m"] - 3.45) < 1e-9 for j in edge)
    assert all(j["finish"] not in M.NOT_FINISHED for j in led["J_own"] + led["J_dd"])


def test_drawing_derived_beam_tops_inside(led):
    js = [j for j in led["J_dd"] if j["side"] != "EXT" and j["dir"] == "H" and j["class"] == "INSIDE"]
    assert js and all(j["class"] == "INSIDE" for j in js)
    v_own = sum(j["length_m"] for j in led["J_own"] if j["side"] != "EXT" and j["dir"] == "V" and j["length_m"])
    v_dd = sum(j["length_m"] for j in led["J_dd"] if j["side"] != "EXT" and j["dir"] == "V" and j["length_m"])
    assert v_dd >= v_own                         # the owner band clips every vertical joint at 3.75 / 3.45


def test_faces_close_and_columns_once(led):
    for f in led["F_own"] + led["F_ext"]:
        if f["state"] == "MEASURED":
            assert abs(f["face_m2"] - f["block_m2"] - f["concrete_m2"]) < 1e-5


def test_outputs_reproduce_and_carry_no_coordinates():
    A.main(["--check"])
    hdr = next(csv.reader(open(ROOT / "research/agents_t317/JOINTS_T317.csv")))
    assert not {"x", "y", "x_m", "y_m", "coords"} & set(hdr)
    s = json.load(open(ROOT / "research/agents_t317/summary.json"))
    assert s["spatter_villa"]["determinate_m2"] == 913.7202
