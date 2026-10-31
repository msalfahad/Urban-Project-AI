"""T-405: plaster corner beads (B4-09). Non-Alsenan villa E405 with hand calculations, adverse cases (corner counted
twice, bead under tile, arc as chord, held class as 0, door height borrowed for a passage, units, mirror / rotation,
tessellated arc), then the development-villa ledger pins (committed inputs only)."""

import importlib.util
import json
import math
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "research", "agents_t405")


def _load(name):
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


B = _load("t405_bead_rules")
A = _load("t405_alsenan")

# villa E405, bedroom 5.00 x 4.00 m (drawn in mm): a column 0.50 wide standing 0.10 proud of the north wall and a wall
# nib 0.15 thick standing 0.60 into the room from the east wall
ROOM_MM = [(0, 0), (5000, 0), (5000, 1500), (4400, 1500), (4400, 1650), (5000, 1650), (5000, 4000),
           (3000, 4000), (3000, 3900), (2500, 3900), (2500, 4000), (0, 4000)]
OWNER = B.Top(3.10, B.OA, "fixture owner plaster height 3.10")
DWG_HELD = B.Top(None, B.HELD, "fixture drawing top", "roof datum not printed")
DRY = B.Face("E-BED", "PLASTER", OWNER, DWG_HELD, 3.10, "L-E405-BED")
BATH = B.Face("E-BATH", "TILE", None, None, None, "L-E405-BATH")


def _m(pts, angle=0.0, mirror=False):
    c, s = math.cos(angle), math.sin(angle)
    out = []
    for x, y in pts:
        x, y = B.to_m(x, "mm"), B.to_m(y, "mm")
        if mirror:
            x = -x
        out.append((x * c - y * s, x * s + y * c))
    return out


def test_fixture_arrises_and_hand_length():
    arr, arc = B.arris_vertices(_m(ROOM_MM))
    assert len(arr) == 4 and arc == []          # column 2 + nib 2
    edges = [B.corner_edge(f"E-BED#V{i}", "E-BED", "EXTERNAL_CORNER", 1, DRY, "col", "fixture") for i in arr]
    t = B.totals(B.check_ledger(edges))
    assert t["measured_m"] == pytest.approx(4 * 3.10)            # hand: 4 x 3.10 = 12.40 m.l
    assert all(e["dwg_m"] is None and e["dwg_status"] == B.HELD for e in edges)   # drawing method HELD, never 0


@pytest.mark.parametrize("angle,mirror", [(0.0, False), (0.7, False), (math.pi / 2, True), (2.0, True)])
def test_mirror_rotation_and_clockwise(angle, mirror):
    pts = _m(ROOM_MM, angle, mirror)
    assert len(B.arris_vertices(pts)[0]) == 4
    assert len(B.arris_vertices(pts[::-1])[0]) == 4


def test_tessellated_arc_is_one_surface_not_arrises():
    # 6.00 x 4.00 room whose east wall bulges INTO the room as a drawn arc (centre 7.50 / 2.00, r 2.50) in 8 facets
    f0 = math.asin(0.8)
    pts = [(0.0, 0.0)]
    for k in range(9):
        f = -f0 + k * 2 * f0 / 8
        pts.append((7.5 - 2.5 * math.cos(f), 2.0 + 2.5 * math.sin(f)))
    pts.append((0.0, 4.0))
    arr, arc = B.arris_vertices(pts)
    assert len(arc) >= 5
    assert all(i not in arc for i in arr)
    # the two ends of the arc meet the straight wall at a real kink: at most those are arrises, never the facets
    assert len(arr) <= 2


def test_obtuse_corner_is_an_arris_and_small_kink_is_not():
    obtuse = [(0, 0), (4, 0), (4, 2), (3, 3), (4, 4), (0, 4)]       # reflex 90 deg at (3, 3)
    assert len(B.arris_vertices(obtuse)[0]) == 1
    kink = [(0, 0), (4, 0), (4, 2), (3.95, 2.5), (4, 3), (4, 4), (0, 4)]   # ~11 deg vs 6 deg
    n = len(B.arris_vertices(kink, min_deg=15.0)[0])
    assert n == 0


def test_door_ring_on_the_plastered_face_only():
    door = B.Opening("D-E1", "DOOR", 0.90, 2.20, B.OA)
    dry = B.opening_face_edge("D-E1#BED", "E-BED", door, DRY, "fixture")
    bath = B.opening_face_edge("D-E1#BATH", "E-BATH", door, BATH, "fixture")
    assert dry["owner_m"] == pytest.approx(2 * 2.20 + 0.90)        # hand 5.30
    assert dry["owner_status"] == B.OA
    assert bath["class"] == "TILED_FACE" and bath["owner_status"] == B.NOT_BEAD and bath["owner_m"] == 0.0
    B.check_ledger([dry, bath])


def test_door_head_above_the_lowest_plaster_top_is_held():
    low = B.Face("E-LOW", "PLASTER", B.Top(2.10, B.OA, "fixture"), DWG_HELD, 2.10, "L")
    e = B.opening_face_edge("D-E2#LOW", "E-LOW", B.Opening("D-E2", "DOOR", 0.9, 2.2, B.OA), low, "fixture")
    assert e["owner_m"] is None and e["owner_status"] == B.HELD and e["held_range"].startswith("0 .. 5.3000")


def test_flush_window_has_no_room_side_arris():
    e = B.flush_window_face("W-E1#IN", "E-BED", B.Opening("W-E1", "WINDOW", 1.2, 1.4, B.DC), DRY, "fixture")
    assert e["class"] == "FLUSH_FRAME" and e["owner_m"] == 0.0
    assert B.totals([e])["measured_m"] == 0.0


def test_arched_head_on_the_developed_arc():
    dev = math.pi * 0.60                                              # semicircle r 0.60: 1.884956 m
    face = B.Face("E-FAC", "PLASTER", B.Top(6.0, B.DC, "fixture"), B.Top(6.0, B.DC, "fixture"), 6.0, "L-EXT")
    op = B.Opening("W-E2", "WINDOW", 1.20, 1.40, B.DC, head_basis="ARC_DEVELOPED", head_m=dev)
    e = B.opening_face_edge("W-E2#OUT", "facade", op, face, "fixture")
    assert e["owner_m"] == pytest.approx(round(2 * 1.40 + dev, 4))   # hand 4.684956 (chord would give 4.0000)


# ------------------------------------------------------------------------------------------------- adverse

def test_arc_as_chord_refused():
    face = B.Face("E-FAC", "PLASTER", B.Top(6.0, B.DC, "f"), B.Top(6.0, B.DC, "f"), 6.0, "L")
    with pytest.raises(B.BeadError):
        B.opening_face_edge("W#OUT", "facade", B.Opening("W", "WINDOW", 1.2, 1.4, B.DC, head_basis="CHORD"), face, "f")
    row = B.cited_edge("W#X", "EXTERIOR", "facade", "WINDOW_JAMB_HEAD", 1, 4.0, B.DC, "f", basis="RECTANGLE")
    with pytest.raises(B.BeadError):
        B.check_ledger([row])


def test_corner_counted_twice_refused():
    e = B.corner_edge("E#V1", "E-BED", "EXTERNAL_CORNER", 1, DRY, "c", "f")
    with pytest.raises(B.BeadError):
        B.check_ledger([e, dict(e)])
    with pytest.raises(B.BeadError):
        B.check_corner_keys([("ROOM-A#V3", ("GF", 1000, 2000)), ("ROOM-B#V7", ("GF", 1000, 2000))])
    assert B.check_corner_keys([("ROOM-A#V3", ("GF", 1000, 2000)), ("ROOM-B#V7", ("1F", 1000, 2000))])


def test_bead_under_tile_refused():
    bad = {"edge_id": "X", "scope": "INTERIOR", "room": "E-BATH", "class": "TILED_FACE", "count": 1, "owner_m": 3.1,
           "owner_status": B.OA, "dwg_m": 3.1, "dwg_status": B.OA, "held_range": "", "basis": ""}
    with pytest.raises(B.BeadError):
        B.check_ledger([bad])
    # a corner with a tiled face is not a plaster bead at all
    assert B.corner_length(DRY, BATH, "owner") == (0.0, B.NOT_BEAD)


def test_held_class_as_zero_refused():
    h = B.held_edge("H", "INTERIOR", "E", "OPENING_UNDER_HEAD", 3, "head not drawn")
    zero = dict(h, owner_m=0.0)
    with pytest.raises(B.BeadError):
        B.check_ledger([zero])
    with pytest.raises(B.BeadError):
        B.held_edge("H2", "INTERIOR", "E", "OPENING_UNDER_HEAD", 3, "")
    t = B.totals([h])
    assert t["measured_m"] == 0.0 and t["held_edges_by_class"] == {"OPENING_UNDER_HEAD": 3}


def test_door_height_not_borrowed_for_a_passage():
    with pytest.raises(B.BeadError):
        B.opening_face_edge("P#BED", "E-BED", B.Opening("P", "PASSAGE", 1.0, 2.2, B.OA), DRY, "f")
    e = B.opening_face_edge("P#BED", "E-BED", B.Opening("P", "PASSAGE", 1.0, None, B.HELD), DRY, "f")
    assert e["owner_status"] == B.HELD and e["owner_m"] is None


def test_units_and_bad_inputs():
    assert B.to_m(3100, "mm") == pytest.approx(3.10)
    with pytest.raises(B.BeadError):
        B.to_m(3.1, "ft")
    with pytest.raises(B.BeadError):
        B.Top(3100.0, B.OA, "a height typed in mm")
    with pytest.raises(B.BeadError):
        B.Top(3.10, B.HELD, "a held top with a figure")
    with pytest.raises(B.BeadError):
        B.arris_vertices([(0, 0), (1, 0), (2, 0)])
    with pytest.raises(B.BeadError):
        B.corner_edge("E", "E", "DOOR_JAMB_HEAD", 1, DRY, "", "")


def test_missing_face_finish_is_held_not_zero():
    unk = B.Face("E-UNK", "UNKNOWN", None, None, None, "")
    e = B.opening_face_edge("D#UNK", "E-UNK", B.Opening("D", "DOOR", 0.9, 2.2, B.OA), unk, "f")
    assert e["owner_status"] == B.HELD and e["owner_m"] is None


# ------------------------------------------------------------------------------------------------- development villa

def test_alsenan_rebuild_byte_identical():
    for name, text in A.outputs().items():
        with open(os.path.join(HERE, name), encoding="utf-8", newline="") as f:
            assert f.read() == text, name


def test_alsenan_totals_pinned():
    s = json.loads(A.outputs()["summary.json"])
    io = s["interior_owner_method"]
    assert io["by_class_m"] == {"DOOR_JAMB_HEAD": 139.9, "EXTERNAL_CORNER": 129.35, "WALL_END": 6.7}
    assert io["measured_by_status_m"] == {B.OA: 268.95, B.DC: 7.0}
    assert s["interior_drawing_method"]["measured_m"] == 139.9      # corners HELD on the drawing method, never 0
    assert s["exterior"]["measured_m"] == pytest.approx(310.6831)
    assert s["interior_corner_vertices"] == 45 and s["interior_corner_vertices_not_beads"] == 1
    assert s["freelancer_interior_check_ml"] == 770.75


def test_alsenan_ledger_invariants():
    edges = A.build()
    ids = [e["edge_id"] for e in edges]
    assert len(ids) == len(set(ids))
    assert not [e for e in edges if e["class"] == "TILED_FACE" and e["owner_status"] != B.NOT_BEAD]
    arched = {e["edge_id"]: e for e in edges if e["edge_id"] in ("W15#OUT", "W16#OUT", "W26#OUT")}
    assert {k: (v["basis"], v["owner_m"]) for k, v in arched.items()} == {
        "W15#OUT": ("ARC_DEVELOPED", 6.8461), "W16#OUT": ("ARC_DEVELOPED", 6.8461), "W26#OUT": ("ARC_DEVELOPED", 4.0709)}
    # every straight window (27; W03 / W17 curved, HELD): room side flush (no arris)
    flush = [e for e in edges if e["class"] == "FLUSH_FRAME"]
    assert len(flush) == 27 and all(e["owner_m"] == 0.0 for e in flush)
    # the shaft corners stay HELD (Q-72), never 0
    st = [e for e in edges if e["room"].startswith("ST-") and e["class"] == "EXTERNAL_CORNER"]
    assert len(st) == 6 and all(e["owner_m"] is None and e["owner_status"] == B.HELD for e in st)
    # one face per shared polygon: D-1F-02 has two faces, not three
    assert sorted(i for i in ids if i.startswith("D-1F-02#")) == ["D-1F-02#1F-01", "D-1F-02#1F-13|ST-1F"]
    # the pantry column is a tile corner (T-368), not a bead
    assert next(e for e in edges if e["edge_id"] == "GF-08#V48")["class"] == "TILED_FACE"
