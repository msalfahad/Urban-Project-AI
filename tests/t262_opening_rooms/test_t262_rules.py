"""T-262: opening-to-room assignment by geometry (opening_rooms.py), on a hand-built fixture that is NOT the development
villa. Hand calculation (metres):

  R1 = [0, 4] x [0, 3] (12.00 m2), wall strip x 4.00 .. 4.15 (0.15 thick), R2 = [4.15, 8] x [0, 3] (11.55 m2).
  Door D1 in that wall: closure line on R1's face x = 4.00, y 1.00 .. 1.80, swing into R1 (side A = -x).
    -> side A: R1 at 0.02 m; side B: walk +x, inside the wall strip 0.02 .. 0.14, R2 at its face 0.15 m. Pair {R1, R2}.
  Window W1 on R1's outer face y = 0 (glass line at y = -0.10 inside a 0.20 outer wall), x 1.00 .. 2.00:
    -> +y: R1 at 0.10 m; -y: no room within 0.70 m. Pair {R1, NO_ROOM}.
  Glazing band G on the outer face y = 3.00 of both rooms, x 3.50 .. 4.60 (it spans the partition end x 4.00 .. 4.15):
    -> room side MULTI_ROOM {R1 (0.50 m), R2 (0.45 m)}, the 0.15 m partition end a NO_ROOM_RUN_IN_LINE, not a side.
  R2 region drawn OVER the wall strip (R2' = [4.00, 8] x [0, 3], 12.00 m2): it covers the strip 0.15 x 3.00 = 0.45 m2;
    a door in that strip lies inside R2' on both sides at the first step -> REVEAL_IN_REGION, side = R1 beyond.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t262"))
import opening_rooms as J  # noqa: E402


def rect(x0, y0, x1, y1):
    return [{"ext": [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], "holes": []}]


def line_stations(a, b, n, side_a_normal=None, spacing=None):
    L = math.dist(a, b)
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    nv = side_a_normal or (-u[1], u[0])
    st = [{"p": (a[0] + u[0] * L * (k + 0.5) / n, a[1] + u[1] * L * (k + 0.5) / n), "n": nv} for k in range(n)]
    return {"stations": st, "line_m": L}


ROOMS = {"R1": rect(0, 0, 4, 3), "R2": rect(4.15, 0, 8, 3)}
OPEN_ZONES = ()


def xf(p, fn):
    return fn(p)


def transform(rooms, op, fn, nfn):
    r2 = {k: [{"ext": [fn(p) for p in pt["ext"]], "holes": []} for pt in v] for k, v in rooms.items()}
    o2 = {"stations": [{"p": fn(s["p"]), "n": nfn(s["n"])} for s in op["stations"]], "line_m": op["line_m"]}
    return r2, o2


def door_d1():
    return line_stations((4.0, 1.0), (4.0, 1.8), 16, side_a_normal=(-1.0, 0.0))


def test_hand_fixture_door_two_rooms():
    g = J.join_opening(door_d1(), ROOMS)
    assert g["A"]["state"] == g["B"]["state"] == "ESTABLISHED"
    assert (g["A"]["room"], g["B"]["room"]) == ("R1", "R2")
    assert {d for _, d in g["A"]["per_station"]} == {0.02}
    # the 0.15 wall is crossed: R2 entered at its face (0.15, on the boundary) or the next 0.01 step
    assert all(0.15 <= d <= 0.16 for _, d in g["B"]["per_station"])
    assert J.door_pair_check("DOOR", g) == "TWO_SIDES"


def test_hand_fixture_window_one_room_and_outdoors():
    w = line_stations((1.0, -0.10), (2.0, -0.10), 20, side_a_normal=(0.0, 1.0))
    g = J.join_opening(w, ROOMS)
    assert (g["A"]["room"], g["B"]["room"]) == ("R1", "NO_ROOM")
    assert {d for _, d in g["A"]["per_station"]} == {0.1}
    assert J.door_pair_check("WINDOW", g) == "N/A"


def test_window_label_naming_the_wrong_room_is_label_wrong():
    w = line_stations((1.0, -0.10), (2.0, -0.10), 20, side_a_normal=(0.0, 1.0))
    g = J.join_opening(w, ROOMS)
    assert J.label_verdict(({"R2"}, {"NO_ROOM"}), g) == "LABEL_WRONG"
    assert J.label_verdict(({"NO_ROOM"}, {"R1"}), g) == "AGREE"       # census order is not a geometric side
    # the geometric result is the same whatever the label says (a label never overrides geometry)
    assert J.join_opening(w, ROOMS)["A"]["room"] == "R1"


def test_door_labels_swapped_rooms_refused_as_name_match():
    g = J.join_opening(door_d1(), {"R1": ROOMS["R1"], "R2": ROOMS["R2"], "R3": rect(8.15, 0, 10, 3)})
    assert J.label_verdict(({"R1"}, {"R3"}), g) == "LABEL_WRONG"     # one side right is not agreement
    assert J.label_verdict(({"R1"}, {"R2"}), g) == "AGREE"


@pytest.mark.parametrize("name,fn,nfn", [
    ("mirror_x", lambda p: (-p[0], p[1]), lambda n: (-n[0], n[1])),
    ("rotate_37", lambda p: (p[0] * math.cos(0.6458) - p[1] * math.sin(0.6458),
                             p[0] * math.sin(0.6458) + p[1] * math.cos(0.6458)),
     lambda n: (n[0] * math.cos(0.6458) - n[1] * math.sin(0.6458), n[0] * math.sin(0.6458) + n[1] * math.cos(0.6458))),
    ("translate_far", lambda p: (p[0] - 163.0, p[1] - 811.0), lambda n: n),
])
def test_mirror_rotation_translation_keep_the_rooms(name, fn, nfn):
    rooms, op = transform(ROOMS, door_d1(), fn, nfn)
    g = J.join_opening(op, rooms)
    assert (g["A"]["room"], g["B"]["room"]) == ("R1", "R2"), name


def test_units_millimetres_must_be_scaled_before_the_join():
    # the same fixture in millimetres: scaled by 0.001 it gives the metre result; left in mm the 0.70 walk stays inside
    # the 150 mm wall and the far room is not found (a units slip shows, it is never silently right)
    mm = lambda p: (p[0] * 1000.0, p[1] * 1000.0)
    rooms_mm, op_mm = transform(ROOMS, door_d1(), mm, lambda n: n)
    back = lambda p: (p[0] / 1000.0, p[1] / 1000.0)
    rooms_m, op_m = transform(rooms_mm, op_mm, back, lambda n: n)
    g = J.join_opening(op_m, rooms_m)
    assert (g["A"]["room"], g["B"]["room"]) == ("R1", "R2")
    g_mm = J.join_opening(op_mm, rooms_mm)
    assert g_mm["B"]["room"] == "NO_ROOM"


def test_glazing_band_over_a_partition_end_serves_two_rooms():
    band = line_stations((3.50, 3.10), (4.60, 3.10), 22, side_a_normal=(0.0, -1.0))
    g = J.join_opening(band, ROOMS)
    assert g["A"]["state"] == "MULTI_ROOM" and g["A"]["rooms"] == {"R1", "R2"}
    assert g["B"]["room"] == "NO_ROOM"
    assert any(f.startswith("NO_ROOM_RUN_IN_LINE:R1|R2:0.15") for f in g["flags"])
    # shares are station shares (R1 0.50 m, R2 0.45 m of 0.95 m of room face)
    assert g["A"]["shares"]["R1"] == pytest.approx(0.50 / 0.95, abs=0.03)
    assert J.label_verdict(({"R1"}, {"NO_ROOM"}), g) == "LABEL_INCOMPLETE"
    assert J.label_verdict(({"R1", "R2"}, {"NO_ROOM"}), g) == "AGREE"


def test_room_region_drawn_over_a_wall_strip_is_found_and_named():
    rooms = {"R1": ROOMS["R1"], "R2": rect(4.00, 0, 8, 3)}           # R2' covers the strip x 4.00 .. 4.15
    strips = [{"handles": ("F1", "F2"), "t_m": 0.15, "overlap_m": 3.0,
               "quad": [(4.00, 0), (4.00, 3), (4.15, 3), (4.15, 0)]}]
    ov = J.strip_overlaps(rooms, strips)
    assert ov == [{"room": "R2", "handles": ("F1", "F2"), "t_m": 0.15, "overlap_m2": 0.45}]
    # contact only (the correct regions) is not an overlap
    assert J.strip_overlaps(ROOMS, strips) == []
    # a door whose reveal lies inside R2': the far side is the room beyond, the reveal is named
    d = line_stations((4.075, 1.0), (4.075, 1.8), 16, side_a_normal=(1.0, 0.0))
    # R1 and R2' touch at x = 4.00 only; the station line is inside R2' on both sides at the first step
    g = J.join_opening(d, rooms)
    assert "REVEAL_IN_REGION:R2" in g["flags"]
    assert {g["A"]["room"], g["B"]["room"]} == {"R1", "R2"}


def test_overlapping_room_regions_are_refused():
    rooms = {"R1": rect(0, 0, 4.10, 3), "R2": rect(4.0, 0, 8, 3)}     # an overlap counted in both rooms
    with pytest.raises(ValueError, match="two room regions"):
        J.join_opening(door_d1(), rooms)


def test_a_door_with_one_side_not_established_is_refused():
    # side B: half the stations reach R2, half find no room (R2 drawn only over y >= 1.4)
    rooms = {"R1": ROOMS["R1"], "R2": rect(4.15, 1.4, 8, 3)}
    g = J.join_opening(door_d1(), rooms)
    assert g["B"]["state"] == "SPLIT" and g["B"]["room"] is None
    assert J.door_pair_check("DOOR", g) == "REFUSED_ONE_SIDE_NOT_ESTABLISHED"
    assert J.label_verdict(({"R1"}, {"R2"}), g) == "NOT_ESTABLISHED"


def test_missing_data_is_refused_never_zero():
    with pytest.raises(ValueError, match="at least two probe stations"):
        J.join_opening({"stations": []}, ROOMS)
    g = J.join_opening(door_d1(), {})                               # no room regions at all
    assert (g["A"]["room"], g["B"]["room"]) == ("NO_ROOM", "NO_ROOM")
    assert J.door_pair_check("DOOR", g) == "TWO_SIDES"              # established as no room, not as a room


def test_open_zone_parts_agree_only_as_open_zone():
    rooms = {"R1": ROOMS["R1"], "Z1": rect(4.15, 0, 6, 3), "Z2": rect(6, 0, 8, 3)}
    g = J.join_opening(door_d1(), rooms)
    assert J.label_verdict(({"R1"}, {"Z2"}), g) == "LABEL_WRONG"
    assert J.label_verdict(({"R1"}, {"Z2"}), g, [{"Z1", "Z2"}]) == "AGREE_OPEN_ZONE"
