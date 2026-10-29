"""T-329 villa B hand fixture (not Alsenan): one bathroom 2.00 x 2.50 m (perimeter 9.00 m), wall tile to 2.40 m
(printed on section S-2), plaster to the 3.00 m soffit (specification note 'internal plaster to the slab soffit'),
one door 0.80 x 2.10 on the north wall (2.00 m), one window 0.60 wide, sill 2.10 / head 2.70 on the east wall (2.50 m),
straddling the tile top.

Hand (m2):   face      backing (0 .. 2.40)                band (2.40 .. 3.00)
             north     2.00 x 2.40 - 0.80 x 2.10 = 3.12   2.00 x 0.60 = 1.20 (door head below the tile top)
             east      2.50 x 2.40 - 0.60 x 0.30 = 5.82   2.50 x 0.60 - 0.60 x 0.30 = 1.32
             south     2.00 x 2.40 = 4.80                 1.20
             west      2.50 x 2.40 = 6.00                 1.50
             total     19.74 (= the tile, closure 0.00)   5.22
Adverse: backing on an open side, band in both the wet and the dry plaster line, millimetres, a universal height,
openings that differ from the tile ledger, a reveal inside the backing, paint on the tiled face, held as 0.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t329"))
sys.path.insert(0, str(ROOT / "research" / "agents_t312"))

import t329_backing_rules as R      # noqa: E402
import t312_wall_tile_rules as T    # noqa: E402

TILE_H = {"value_m": 2.40, "source": "section S-2 (printed tile top)"}
PLAS_H = {"value_m": 3.00, "source": "specification note: internal plaster to the slab soffit"}
DOOR = {"id": "D1", "kind": "door", "w": 0.80, "head": 2.10}
WIN = {"id": "W1", "kind": "window", "w": 0.60, "sill": 2.10, "head": 2.70}
FACES = [("N", 2.00, [DOOR]), ("E", 2.50, [WIN]), ("S", 2.00, []), ("W", 2.50, [])]


def _all():
    return {fid: R.face_backing(L, TILE_H, PLAS_H, ops) for fid, L, ops in FACES}


def test_hand_fixture_face_by_face():
    r = _all()
    assert {k: v["backing"] for k, v in r.items()} == {"N": 3.12, "E": 5.82, "S": 4.80, "W": 6.00}
    assert {k: v["band"] for k, v in r.items()} == {"N": 1.20, "E": 1.32, "S": 1.20, "W": 1.50}
    assert R.total([v["backing"] for v in r.values()]) == (19.74, 0)
    assert R.total([v["band"] for v in r.values()]) == (5.22, 0)


def test_backing_closes_to_the_tile_ledger():
    r = _all()
    tile = sum(T.face_net(L, TILE_H, ops)["net_hi"] for _, L, ops in FACES)
    assert round(tile, 4) == 19.74
    assert R.closure_to_tile(round(sum(v["backing"] for v in r.values()), 4), round(tile, 4)) == 0.0


def test_owner_method_plaster_equal_to_tile_top_gives_no_band():
    r = R.face_backing(2.50, TILE_H, {"value_m": 2.40, "source": "owner Q-43 plaster height"}, [WIN])
    assert r["backing"] == 5.82 and r["band"] == 0.0
    # plaster recorded lower than the tile: the backing still follows the tile, no negative band
    r = R.face_backing(2.50, TILE_H, {"value_m": 2.20, "source": "owner plaster height"}, [])
    assert r["backing"] == 6.00 and r["band"] == 0.0


def test_window_wholly_above_the_tile_comes_off_the_band_only():
    hi = {"id": "W2", "kind": "window", "w": 0.60, "sill": 2.50, "head": 2.90}
    r = R.face_backing(2.50, TILE_H, PLAS_H, [hi])
    assert r["backing"] == 6.00 and r["band"] == round(1.50 - 0.24, 4)


def test_missing_data_is_held_never_zero():
    r = R.face_backing(2.50, {"value_m": None, "source": "section S-2 (not printed)"}, PLAS_H, [])
    assert r["backing"] is None and r["band"] is None and r["held"]
    r = R.face_backing(2.00, TILE_H, PLAS_H, [{"id": "D9", "kind": "door", "w": 0.80, "head": None}])
    assert r["backing"] is None and r["held"]
    r = R.face_backing(2.00, TILE_H, None, [])
    assert r["backing"] == 4.80 and r["band"] is None
    assert R.total([4.80, None]) == (4.80, 1)
    with pytest.raises(R.BackingError, match="CLOSURE_TO_TILE"):
        R.closure_to_tile(None, 4.80)


def test_mirror_and_rotation_do_not_change_the_faces():
    a = R.total([v["backing"] for v in _all().values()])
    b = R.total([R.face_backing(L, TILE_H, PLAS_H, ops)["backing"] for _, L, ops in reversed(FACES)])
    assert a == b


def test_scope_open_side_and_dry_face_refused():
    assert R.check_scope({"face_id": "N", "tile_scope": R.TILED, "backing": True}) is True
    with pytest.raises(R.BackingError, match="BACKING_ON_OPEN_SIDE"):
        R.check_scope({"face_id": "open", "tile_scope": R.OPEN_EDGE, "piece": "OPEN", "backing": True})
    with pytest.raises(R.BackingError, match="BACKING_OUT_OF_SCOPE"):
        R.check_scope({"face_id": "dry", "tile_scope": R.NOT_TILED, "backing": True})
    with pytest.raises(R.BackingError, match="BACKING_MISSING"):
        R.check_scope({"face_id": "N", "tile_scope": R.TILED, "backing": False})


def test_band_in_both_wet_and_dry_line_refused():
    ok = [(R.PLASTER, "L-wet", "WET", "E", "BACKING"), (R.PLASTER, "L-wet", "WET", "E", "ABOVE_TILE")]
    R.check_claims(ok)
    with pytest.raises(R.BackingError, match="BAND_TWICE"):
        R.check_claims(ok + [(R.PLASTER, "L-dry", "DRY", "E", "ABOVE_TILE")])
    with pytest.raises(R.BackingError, match="BAND_TWICE"):
        R.check_claims([(R.PLASTER, "L-dry", "DRY", "E", "ABOVE_TILE")])
    with pytest.raises(R.BackingError, match="FACE_TWICE"):
        R.check_claims(ok + [(R.PLASTER, "L-wet-2", "WET", "E", "BACKING")])
    with pytest.raises(R.BackingError, match="PAINT_ON_TILE"):
        R.check_claims([(R.PAINT, "L-paint", "WET", "E", "BACKING")])


def test_units_and_universal_heights_refused():
    with pytest.raises(R.BackingError, match="BAD_UNITS"):
        R.face_backing(2.50, {"value_m": 2400, "source": "section S-2"}, PLAS_H, [])
    with pytest.raises(R.BackingError, match="BAD_UNITS"):
        R.face_backing(2500, TILE_H, PLAS_H, [])
    with pytest.raises(R.BackingError, match="BAD_UNITS"):
        R.face_backing(2.50, TILE_H, PLAS_H, [{"id": "W", "kind": "window", "w": 600, "sill": 2.1, "head": 2.7}])
    with pytest.raises(R.BackingError, match="UNIVERSAL_HEIGHT"):
        R.face_backing(2.50, {"value_m": 2.40, "source": "DEFAULT"}, PLAS_H, [])
    with pytest.raises(R.BackingError, match="UNIVERSAL_HEIGHT"):
        R.face_backing(2.50, TILE_H, {"value_m": 3.0, "source": "typical"}, [])
    with pytest.raises(R.BackingError, match="NON_POSITIVE"):
        R.face_backing(0.0, TILE_H, PLAS_H, [])


def test_openings_follow_the_tile_ledger_and_reveals_stay_out():
    R.check_same_openings(["D1"], ["D1"])
    with pytest.raises(R.BackingError, match="BACKING_OPENINGS_DIFFER"):
        R.check_same_openings(["D1", "W1"], ["D1"])
    with pytest.raises(R.BackingError, match="OPENING_TWICE"):
        R.check_same_openings(["D1", "D1"], ["D1", "D1"])
    with pytest.raises(R.BackingError, match="REVEAL_IN_BACKING"):
        R.face_backing(2.00, TILE_H, PLAS_H, [DOOR, {"id": "D1-jamb", "kind": "jamb", "w": 0.2}])


def test_named_correction_piece_only_without_openings():
    r = R.face_backing(-0.50, TILE_H, PLAS_H, [], correction=True)
    assert r["backing"] == -1.20 and r["band"] == -0.30
    with pytest.raises(R.BackingError, match="BAD_CORRECTION"):
        R.face_backing(-0.50, TILE_H, PLAS_H, [DOOR], correction=True)
    with pytest.raises(R.BackingError, match="NON_POSITIVE"):
        R.face_backing(-0.50, TILE_H, PLAS_H, [])


def test_mortar_is_the_same_layer_information():
    assert R.mortar_m3(19.74) == round(19.74 * 0.02, 4)
    assert R.mortar_m3(None) is None
    assert R.COAT["status"] == "ASSUMED — OWNER-APPROVED"
