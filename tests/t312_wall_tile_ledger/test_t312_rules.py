"""T-312 villa T hand fixture (not Alsenan): a 2.40 x 3.00 bath and an American pantry with one open edge.

Bath (wet, UP-FIN-WALL-001): perimeter 2 x (2.40 + 3.00) = 10.80 m; tile top H = 2.60 m from the drawn section
(source 'section S-1'); door 0.80 x 2.10 printed on a 2.40 wall; window 0.60 wide, sill 2.70 / head 3.20 = wholly
above the tile top (no deduction).  Hand: 10.80 x 2.60 = 28.08 - 0.80 x 2.10 = 1.68 -> 26.40 m2.

Pantry (open zone, UP-PANTRY-001): box 3.00 (x) x 2.00 (y), the south edge y = 0 open to the living room; walls north
(3.00), west (2.00), east (2.00). Counter 0.60 deep along the whole north wall + a 1.20 m return along the west wall
(L); nothing on the east wall. H = 2.70 m (owner project fact). Window over the counter on the north wall 1.20 wide,
sill 1.10 / head 2.20.
Hand: north 3.00 x 2.70 = 8.10 - 1.20 x 1.10 = 1.32 -> 6.78; west 2.00 x 2.70 = 5.40 (whole host wall, FULL_WALL);
east NOT_TILED (no installation); south open edge NOT_TILED.  Tiled 12.18 m2; closure 3.00 + 2.00 + 2.00 + 3.00 = 10.00.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t312"))

import t312_wall_tile_rules as R  # noqa: E402

H_BATH = {"value_m": 2.60, "source": "section S-1 (drawn tile top)"}
H_PAN = {"value_m": 2.70, "source": "owner project fact villa T"}
DOOR = {"id": "D1", "kind": "door", "w": 0.80, "head": 2.10}
HIGH_WIN = {"id": "W1", "kind": "window", "w": 0.60, "sill": 2.70, "head": 3.20}
PAN_WIN = {"id": "W2", "kind": "window", "w": 1.20, "sill": 1.10, "head": 2.20}

# pantry plan (m): walls as face lines, counter as an L polygon
NORTH = [(0.0, 2.0), (3.0, 2.0)]
WEST = [(0.0, 0.0), (0.0, 2.0)]
EAST = [(3.0, 0.0), (3.0, 2.0)]
SOUTH_OPEN = [(0.0, 0.0), (3.0, 0.0)]
# counter outline (0,2)-(3,2)-(3,1.4)-(0.6,1.4)-(0.6,0.8)-(0,0.8): two runs (legs), each by its back line;
# the north run's END butts the east wall over its 0.60 depth (an end, not a back)
COUNTER = [[(0.0, 2.0), (3.0, 2.0)], [(0.0, 2.0), (0.0, 0.8)]]


def _bath_faces():
    return [("N", 2.40, [DOOR]), ("E", 3.00, [HIGH_WIN]), ("S", 2.40, []), ("W", 3.00, [])]


def test_bath_hand_value():
    nets = [R.face_net(L, H_BATH, ops) for _, L, ops in _bath_faces()]
    assert [n["status"] for n in nets] == ["DETERMINATE"] * 4
    assert sum(n["net_lo"] for n in nets) == pytest.approx(26.40, abs=1e-9)
    assert R.room_closure([L for _, L, _ in _bath_faces()], 10.80) == 0.0
    assert R.face_scope(R.WET, "WALL") == (R.TILED, "UP-FIN-WALL-001 full height (wet area)")


def test_window_above_tile_top_deducts_nothing_and_a_claimed_deduction_is_refused():
    assert R.opening_band(HIGH_WIN, 2.60) == 0.0
    R.check_claimed_deduction(HIGH_WIN, 2.60, 0.0)
    with pytest.raises(R.TileError, match="^WINDOW_ABOVE_TILE"):
        R.check_claimed_deduction(HIGH_WIN, 2.60, 0.60 * 0.50)
    # partly inside the band: only the part below the tile top
    assert R.opening_band({"id": "W", "kind": "window", "w": 0.60, "sill": 2.00, "head": 3.20}, 2.60) == \
        pytest.approx(0.36)


def test_universal_height_refused():
    for src in ("", "DEFAULT", "universal", None):
        with pytest.raises(R.TileError, match="^UNIVERSAL_HEIGHT"):
            R.face_net(2.40, {"value_m": 2.40, "source": src}, [])
    with pytest.raises(R.TileError, match="^UNIVERSAL_HEIGHT"):
        R.face_net(2.40, None, [])


def test_millimetre_inputs_refused():
    with pytest.raises(R.TileError, match="^BAD_UNITS"):
        R.face_net(2400.0, H_BATH, [])
    with pytest.raises(R.TileError, match="^BAD_UNITS"):
        R.face_net(2.40, {"value_m": 2600.0, "source": "section S-1"}, [])
    with pytest.raises(R.TileError, match="^BAD_UNITS"):
        R.face_net(2.40, H_BATH, [{"id": "D", "kind": "door", "w": 800.0, "head": 2.10}])


def test_held_height_and_held_head_never_zero():
    n = R.face_net(2.40, {"value_m": None, "source": "roof datum not printed"}, [DOOR])
    assert n["status"] == "HELD" and n["net_lo"] is None and n["net_hi"] is None
    b = R.face_net(2.40, H_BATH, [{"id": "D", "kind": "door", "w": 0.80, "head": None}])
    assert b["status"] == "HELD (BOUNDED)"
    assert b["net_lo"] == pytest.approx(2.40 * 2.60 - 0.80 * 2.60) and b["net_hi"] == pytest.approx(2.40 * 2.60)
    assert R.total([b["net_lo"], 6.0], [b["status"], "DETERMINATE"]) == (6.0, 1)
    # the Q-55 C fallback head
    f = R.face_net(2.40, H_BATH, [{"id": "D", "kind": "door", "w": 0.80, "head": None, "fallback": True}])
    assert f["net_lo"] == pytest.approx(2.40 * 2.60 - 0.80 * 2.20)


def _pantry_faces(walls, counter):
    rows = []
    cls = R.pantry_class(open_edges_m=3.0)
    for fid, seg, piece in walls:
        host = None if counter is None else (R.host_overlap_m(seg, counter) if piece == "WALL" else 0.0)
        sc, why = R.face_scope(cls, piece, host)
        rows.append(dict(face_id=fid, piece=piece, room_class=cls, scope=sc, host_m=host, why=why,
                         length_m=LineStringLen(seg)))
    return rows


def LineStringLen(seg):
    (x0, y0), (x1, y1) = seg
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5


PANTRY_WALLS = [("N", NORTH, "WALL"), ("W", WEST, "WALL"), ("E", EAST, "WALL"), ("S", SOUTH_OPEN, "OPEN")]


def test_american_pantry_host_walls_only():
    rows = _pantry_faces(PANTRY_WALLS, COUNTER)
    sc = {r["face_id"]: r["scope"] for r in rows}
    assert sc == {"N": R.TILED, "W": R.TILED, "E": R.NOT_TILED, "S": R.OPEN_EDGE}
    host = {r["face_id"]: r["host_m"] for r in rows}
    assert host["N"] == pytest.approx(3.00, abs=1e-6) and host["W"] == pytest.approx(1.20, abs=1e-6)
    for r in rows:
        R.check_scope(r)
    nets = {"N": R.face_net(3.0, H_PAN, [PAN_WIN]), "W": R.face_net(2.0, H_PAN, [])}
    assert nets["N"]["net_lo"] == pytest.approx(6.78) and nets["W"]["net_lo"] == pytest.approx(5.40)
    assert nets["N"]["net_lo"] + nets["W"]["net_lo"] == pytest.approx(12.18)
    assert R.room_closure([r["length_m"] for r in rows], 10.00) == 0.0


def test_open_edge_tiled_refused_and_imaginary_closed_pantry_refused():
    rows = _pantry_faces(PANTRY_WALLS, COUNTER)
    s = dict(next(r for r in rows if r["face_id"] == "S"), scope=R.TILED)
    with pytest.raises(R.TileError, match="^OPEN_EDGE_TILED"):
        R.check_scope(s)
    e = dict(next(r for r in rows if r["face_id"] == "E"), scope=R.TILED)
    with pytest.raises(R.TileError, match="^IMAGINARY_PANTRY"):
        R.check_scope(e)
    with pytest.raises(R.TileError, match="^TILE_OUT_OF_SCOPE"):
        R.check_scope(dict(face_id="X", piece="WALL", room_class=R.DRY, scope=R.TILED))


def test_pantry_with_no_installation_drawn_is_unresolved_not_all_walls():
    rows = _pantry_faces(PANTRY_WALLS, None)
    assert {r["face_id"]: r["scope"] for r in rows} == {"N": R.UNRESOLVED, "W": R.UNRESOLVED, "E": R.UNRESOLVED,
                                                        "S": R.OPEN_EDGE}
    assert R.pantry_class(0.0) == R.PANTRY_ENCLOSED
    assert R.face_scope(R.PANTRY_ENCLOSED, "WALL")[0] == R.TILED


@pytest.mark.parametrize("tf", [
    lambda x, y: (-x, y),                      # mirror
    lambda x, y: (y, -x),                      # rotate 90
    lambda x, y: (x * 0.6 - y * 0.8 + 41.0, x * 0.8 + y * 0.6 - 7.5),   # rotate + shift
])
def test_pantry_hosts_mirror_and_rotation_invariant(tf):
    T = lambda seg: [tf(*p) for p in seg]  # noqa: E731
    walls = [(f, T(s), p) for f, s, p in PANTRY_WALLS]
    rows = _pantry_faces(walls, [T(r) for r in COUNTER])
    assert {r["face_id"]: r["scope"] for r in rows} == {"N": R.TILED, "W": R.TILED, "E": R.NOT_TILED,
                                                        "S": R.OPEN_EDGE}
    host = {r["face_id"]: r["host_m"] for r in rows}
    assert host["W"] == pytest.approx(1.20, abs=1e-6)


def test_a_corner_touch_is_no_host():
    # a run whose back is perpendicular to the east wall touches it at one point only; a back 3 cm off the face
    # (beyond the 2 cm drafting tolerance) is a free-standing run, no host
    assert R.host_overlap_m(EAST, [[(2.0, 1.4), (3.0, 1.4)]]) < R.HOST_MIN_M
    assert R.host_overlap_m(EAST, [[(2.97, 0.2), (2.97, 1.8)]]) == 0.0
    assert R.host_overlap_m(EAST, [[(2.99, 0.2), (2.99, 1.8)]]) == pytest.approx(1.6, abs=1e-6)


def test_face_in_two_lines_refused_and_no_line_reported():
    faces = [dict(face_id="B|N", room="B", scope=R.TILED), dict(face_id="P|E", room="P", scope=R.NOT_TILED),
             dict(face_id="P|N", room="P", scope=R.TILED)]
    out = R.bind(faces, {"B": ["L-bath"]})
    assert out == {"B|N": "L-bath", "P|N": R.NO_LINE}
    with pytest.raises(R.TileError, match="^FACE_TWICE"):
        R.bind(faces, {"B": ["L-bath", "L-other"]})
    with pytest.raises(R.TileError, match="^FACE_TWICE"):
        R.check_line_claims([("L-bath", "B|N"), ("L-pantry", "B|N")])


def test_opening_twice_refused_and_bad_closure_refused():
    R.check_openings_once([("B", "D1"), ("C", "D1")])        # one door, two rooms: once per side
    with pytest.raises(R.TileError, match="^OPENING_TWICE"):
        R.check_openings_once([("B", "D1"), ("B", "D1")])
    with pytest.raises(R.TileError, match="^CLOSURE"):
        R.room_closure([2.40, 3.00, 2.40], 10.80)            # a face missing
    assert R.room_closure([2.40, 3.00, 2.40], 10.80, named_residual_m=3.00) == 0.0
