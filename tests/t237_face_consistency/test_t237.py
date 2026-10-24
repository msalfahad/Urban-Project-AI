"""T-237: cross-trade wall-face consistency (blockwork / plaster / paint), rule R-T237-1 (proposed, any villa).

Fixture villa T237-F (NOT Alsenan), hand truth:
  storey (structural top to structural top) 3.50, slab 0.15.
  Room A and room B share block wall X (4.00 m long); beam BX 0.20 x 0.45 sits on X over its full length.
    block X:  3.50 - 0.45 = 3.05            plaster top (slab soffit): 3.50 - 0.15 = 3.35
    plaster - block = 0.30 = beam band 0.45 - 0.15 (concrete beam side face, not block) -> BAND_EXPLAINED, residual 0
  Room A's exterior wall Y has only the slab over it: block 3.50 - 0.15 = 3.35 = plaster top -> AGREES.
  Door D1 1.00 x 2.20 in X (one deduction on face A/X and one on face B/X); window W1 1.20 wide in Y, head HELD.
  Room A net, face 16.00 m, paint height 3.00 .. 3.20:
    lo = 16 x 3.00 - 1.00 x 2.20 - 1.20 x 3.00 (held window, full band) = 48.00 - 2.20 - 3.60 = 42.20
    hi = 16 x 3.20 - 2.20 (held window not deducted)                     = 51.20 - 2.20 = 49.00
  Stair void face (no slab soffit at the face): block 3.05, plaster runs to the storey 3.50: band = full beam depth
  0.45 (beam side + slab edge) -> BAND_EXPLAINED; read as a room under a slab it leaves a 0.15 residual (DATUM_RESIDUAL).
Adverse: the same opening deducted twice on one face; a plaster top above the block top with no member (or slab-only
members); a HELD block height carried as a plaster number; heights in mm; split parts that do not sum to the width;
a mismatched door width (one opening, two sizes).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t237"
sys.path.insert(0, str(HERE))

import face_consistency as F  # noqa: E402

BEAM = [(0.45, 4.00, 3.05)]            # (depth, length, block h) as the register prints a member piece
SLAB = [(0.15, 3.00, 3.35)]


# ------------------------------------------------------------------------------------------------ normal cases
def test_shared_wall_beam_band_explained_by_hand():
    r = F.height_check(3.35, 0.15, 3.05, "SOURCE-SUPPORTED", BEAM)
    assert r["code"] == "BAND_EXPLAINED"
    assert r["delta_m"] == pytest.approx(0.30)
    assert r["band_m"] == pytest.approx(0.30)
    assert r["residual_m"] == pytest.approx(0.0, abs=1e-9)
    assert r["storey_plaster_m"] == pytest.approx(3.50) and r["storey_block_m"] == pytest.approx(3.50)


def test_slab_only_wall_agrees():
    r = F.height_check(3.35, 0.15, 3.35, "SOURCE-SUPPORTED", SLAB)
    assert r["code"] == "AGREES" and r["band_m"] == pytest.approx(0.0)


def test_one_deduction_per_face_and_two_faces_per_door():
    assert F.check_deductions([{"id": "D1", "w": 1.0}, {"id": "W1", "w": 1.2}])
    pop = F.check_id_population([("A", "X", "D1", 1.0), ("B", "X", "D1", 1.0), ("A", "Y", "W1", 1.2)],
                                {"D1": 1.0, "W1": 1.2})
    assert pop == []                       # two faces of one door: 0 findings


def test_room_net_bounds_by_hand():
    lo, hi, held = F.net_bounds(16 * 3.00, 16 * 3.20, 3.00, 3.20,
                                [dict(id="D1", w=1.00, sill=0.0, head=2.20), dict(id="W1", w=1.20, sill=None, head=None)])
    assert lo == pytest.approx(42.20) and hi == pytest.approx(49.00) and held == ["W1"]


def test_fixed_outline_deduction_used_as_is():
    lo, hi, _ = F.net_bounds(10.0, 10.0, 3.0, 3.0, [dict(id="M1", w=1.2, fixed_m2=2.9655)])
    assert lo == pytest.approx(7.0345) and hi == pytest.approx(7.0345)


def test_stair_void_full_member_depth():
    r = F.height_check(3.50, 0.15, 3.05, "SOURCE-SUPPORTED", BEAM, void=True)
    assert r["code"] == "BAND_EXPLAINED" and r["band_m"] == pytest.approx(0.45)
    r2 = F.height_check(3.50, 0.15, 3.05, "SOURCE-SUPPORTED", BEAM)
    assert r2["code"] == "DATUM_RESIDUAL" and r2["residual_m"] == pytest.approx(0.15)


def test_split_face_sums_to_the_width():
    pop = F.check_id_population([("A", "X", "D1", 1.0), ("B1", "X", "D1", 0.42), ("B2", "X", "D1", 0.58)], {"D1": 1.0})
    assert [p["code"] for p in pop] == ["SPLIT_FACE_SUMS"]


def test_member_pieces_parse_register_evidence():
    ev = ("roof-slab plan, CB8 BM-GF-041 (h 0.75 CALCULATED): 6.34 m -> h 3.75; B1 BM-GF-014 (h 0.4 CALCULATED): "
          "1.12 m -> h 4.10; slab GF-139 (slab t 0.16): 1.64 m -> h 3.84; storey heights GF 4.50")
    assert F.member_pieces(ev) == [(0.75, 6.34, 3.75), (0.4, 1.12, 4.10), (0.16, 1.64, 3.84)]


# ------------------------------------------------------------------------------------------------ adverse cases
def test_same_opening_twice_on_one_face_refused():
    with pytest.raises(F.ConsistencyRefused, match="DOUBLE_DEDUCTION"):
        F.check_deductions([{"id": "D1", "w": 1.0}, {"id": "D1", "w": 1.0}])
    pop = F.check_id_population([("A", "X", "D1", 1.0), ("A", "X", "D1", 1.0)], {"D1": 1.0})
    assert pop[0]["code"] == "DOUBLE_DEDUCTION"


def test_plaster_above_block_without_member_refused():
    with pytest.raises(F.ConsistencyRefused, match="NO_MEMBER"):
        F.height_check(3.35, 0.15, 3.05, "SOURCE-SUPPORTED", [])
    with pytest.raises(F.ConsistencyRefused, match="NO_MEMBER"):
        F.height_check(3.35, 0.15, 3.05, "SOURCE-SUPPORTED", SLAB)       # slab-only members cannot make a 0.30 band


def test_held_block_height_carried_as_plaster_refused():
    with pytest.raises(F.ConsistencyRefused, match="HELD_BLOCK_CARRIED"):
        F.height_check(3.05, 0.15, None, "HELD", BEAM, plaster_from_block=True)
    r = F.height_check(3.35, 0.15, None, "HELD", BEAM)                  # independent plaster top: block stays HELD
    assert r["code"] == "BLOCK_HELD" and r["delta_m"] is None           # never 0


def test_heights_in_millimetres_refused():
    with pytest.raises(F.ConsistencyRefused, match="UNITS"):
        F.height_check(3350.0, 0.15, 3.05, "SOURCE-SUPPORTED", BEAM)


def test_split_parts_that_do_not_sum_are_named():
    pop = F.check_id_population([("B1", "X", "W9", 1.625), ("B2", "X", "W9", 5.106)], {"W9": 6.57})
    assert pop[0]["code"] == "SPLIT_FACE_SUM_DIFFERS" and pop[0]["d_w_m"] == pytest.approx(0.161)


def test_one_opening_two_sizes_named_with_m2():
    code, dw, dh, dm2 = F.size_check("D1", 0.95, 2.20, 1.00, 2.20)
    assert code == "SIZE_DIFFERS" and dm2 == pytest.approx(-0.11)
    assert F.size_check("W1", 1.2, None, 1.2, 1.5)[0] == "AGREES_WIDTH_HEIGHT_HELD"
    assert F.size_check("W1", None, None, 1.2, 1.5)[0] == "WIDTH_HELD"


# ------------------------------------------------------------------------------------------------ development villa
def test_alsenan_crosswalk_reproduces_and_names_the_findings(tmp_path):
    import alsenan_t237 as A
    s, d = A.build(tmp_path)
    assert s["rooms"] == 32 and s["rooms_with_a_crosswalked_wall"] == 32
    assert s["reproduced_rooms"] == 30                       # the 2 rooms with no drawn level stay HELD ('-')
    assert s["applied_to_merged_ledgers"] is False
    k = s["findings"]
    assert "DOUBLE_DEDUCTION" not in k and "PLASTER_ABOVE_BLOCK_NO_MEMBER" not in k and "DATUM_RESIDUAL" not in k
    f = {(x["kind"], x["detail"].split(":")[0]) for x in d["findings"]}
    assert ("ROOM_ASSIGNMENT_DIFFERS", "W06") in f              # T-128 wedge B vs T-175 wedge A
    assert any(x["kind"] == "SPLIT_FACE_SUM_DIFFERS" and x["detail"].startswith("W03: split parts sum - census width = 0.161")
               for x in d["findings"])
    sz = {(r["room"], r["census_id"]): r for r in d["sizes"]}
    assert sz[("1F-13", "W15")]["d_m2_per_face"] == pytest.approx(0.442)      # 4.805 -> 4.363 (T-238)
    assert sz[("ST-2F", "W26")]["d_m2_per_face"] == pytest.approx(0.165)      # 2.040 -> 1.875 (T-238)
    assert sz[("1F-11", "W17")]["code"].startswith("T-128 DEDUCTS A HEIGHT")  # T-238: HELD, bound 10.024
    rooms = {r["room"]: r for r in d["rooms"]}
    assert rooms["GF-10"]["dwg_net_new_m2"] == "HELD"                          # missing never becomes 0
    assert "W17" in rooms["1F-11"]["held_new"]
    for r in d["faces"]:
        if r["height_code"] == "BAND_EXPLAINED":
            assert abs(float(r["residual_m"])) <= F.TOL_M
    assert json.loads((tmp_path / "summary.json").read_text())["faces"] == s["faces"]
