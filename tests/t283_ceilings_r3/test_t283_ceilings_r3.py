"""T-283 ceilings r3: R-CEIL-R3-1 (a stair drawn under the slab is one footprint over every face it crosses) and
R-CEIL-R3-2 (a bulkhead face only on a beam edge with decor ceiling on its open side), on a hand-calculated villa W
(not Alsenan) under mirror / rotation / translation, adverse cases, and the Alsenan pins (rebuild, totals, privacy)."""
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t283"
sys.path.insert(0, str(HERE))
import ceilings_r3 as C3  # noqa: E402

CR = C3.CR
Q = 1024          # circle resolution (segments per quarter) so polygon lengths are within 1e-5 of the arcs

# ------------------------------------------------------------------------------------------- villa W (hand truth)
# Room 8.00 x 6.00 = 48.000 m2. Slab above: stair face 2.40 x 3.00 = 7.200 (x 0..2.4, y 0..3.0); beam band B1 0.40
# wide along y 3.0 .. 3.4 over the full width (D 0.75, CALCULATED; 3.200 m2); a dome opening r 1.00 at (5.5, 4.7) =
# 3.1416 m2 with a ring beam RB1 r 1.00 .. 1.20 (D 0.75, CALCULATED; 1.3823 m2); the rest slab. The flight drawn
# under the slab (treads x 0..1.2, y 0.4 .. 3.3) runs 0.30 m beyond the stair face, under B1: 1.20 x 0.30 = 0.360.
# Decor ceiling, one-face clip (R2): 48 - 7.2 - 3.1416 = 37.6584; R3: 37.6584 - 0.360 = 37.2984.
# Owner bulkheads (D - 0.60 = 0.15): B1 edges 8 + 8 = 16 m -> R2 2.400; R3: 2.40 m of its south edge faces the
#   stair zone -> 13.60 x 0.15 = 2.040; RB1 R2 (2 pi 1.0 + 2 pi 1.2) x 0.15 = 2.0735, R3 inner edge faces the dome
#   opening -> 2 pi 1.2 x 0.15 = 1.1310. Stair-well edge 2.400 m; dome-opening edge 6.2832 m (once, in the R2 row).
HAND = {"horiz_r2": 48 - 7.2 - math.pi, "beyond": 0.36, "own_r2": 2.4 + (2 * math.pi * 2.2) * 0.15,
        "own_r3": 13.6 * 0.15 + 2 * math.pi * 1.2 * 0.15, "stair_edge": 2.4, "dome_edge": 2 * math.pi}
HAND["horiz_r3"] = HAND["horiz_r2"] - HAND["beyond"]


def villa_w(T=lambda g: g):
    room = T(box(0, 0, 8, 6))
    stair = T(box(0, 0, 2.4, 3.0))
    band = T(box(0, 3.0, 8, 3.4))
    disc = T(Point(5.5, 4.7).buffer(1.0, Q))
    ring = T(Point(5.5, 4.7).buffer(1.2, Q).difference(Point(5.5, 4.7).buffer(1.0, Q)))
    slab = room.difference(unary_union([stair, band, disc, ring]))
    treads = [(f"t{i}", (0.0, 0.4 + 0.29 * i), (1.2, 0.4 + 0.29 * i)) for i in range(11)]       # 0.40 .. 3.30
    treads = [(i, T(Point(a)).coords[0], T(Point(b)).coords[0]) for i, a, b in treads]
    faces = [("W-STAIR", "STAIR", stair, None),
             ("W-B1", "BEAM", band, {"member": "BM-W-01", "mark": "B1", "r2_status": "CALCULATED", "r2_depth": "0.75"}),
             ("W-DOME", "DOME_OPENING+RING", disc, None),
             ("W-RB1", "BEAM", ring, {"member": "BM-W-02", "mark": "RB1", "r2_status": "CALCULATED",
                                      "r2_depth": "0.75"}),
             ("W-SLAB", "SLAB", slab, None)]
    return room, faces, treads, disc


def run(T=lambda g: g):
    room, faces, treads, disc = villa_w(T)
    rec = CR.overlay(room, faces, domes=[disc])
    rec.update({"face": "W-R1", "floor": "1F", "name": "Hall"})
    rows, _ = CR.ledger(rec, "DRY", "DRAWING-CONFIRMED", "villa W hall")
    fl, loose = C3.flight_footprints(treads)
    fp = unary_union([p for _, p in fl])
    parts, outside = C3.stair_zone_parts(fp, [(i, c, p) for i, c, p, _ in faces])
    stairz = unary_union([faces[0][2], fp])
    opens = [("STAIR_ZONE", stairz), ("DOME_OPEN", disc)]
    deltas = {"stair_beyond": [], "beams": {}}
    for fid, c, p, m in faces:
        if c != "BEAM":
            continue
        x = p.intersection(room)
        u = x.intersection(fp).area
        if u > 0.0005:
            deltas["stair_beyond"].append((fid, u))
        deltas["beams"][fid] = {"mark": m["mark"], "status": "CALCULATED", "depth": 0.75,
                                "free_edge_m": CR.free_edge(x, room), "borders": C3.border_segments(x, room, opens)}
    return C3.face_r3(rec, rows, deltas), parts, outside, fl, loose


TRANSFORMS = {
    "identity": lambda g: g,
    "mirror": lambda g: affinity.scale(g, -1, 1, origin=(0, 0)),
    "rot37+translate": lambda g: affinity.translate(affinity.rotate(g, 37, origin=(0, 0)), 512.3, -88.7),
    "mirror+rot-90": lambda g: affinity.rotate(affinity.scale(g, 1, -1, origin=(0, 0)), -90, origin=(0, 0)),
}


@pytest.mark.parametrize("name", list(TRANSFORMS))
def test_villa_w_hand_truth(name):
    r, parts, outside, fl, loose = run(TRANSFORMS[name])
    assert len(fl) == 1 and not loose
    assert r["horizontal_m2"] == pytest.approx(HAND["horiz_r3"], abs=2e-4)
    assert r["owner_bulkhead_m2"] == pytest.approx(HAND["own_r3"], abs=2e-4)
    s = {x["surface"].split(" (")[0].split(":")[0]: x for x in r["surfaces"]}
    assert s["stair zone beyond the stair face"]["qty"] == pytest.approx(0.36, abs=1e-4)
    assert s["stair zone beyond the stair face"]["status"] == "HELD"
    assert s["beam edge at a stair zone"]["qty"] == pytest.approx(2.4, abs=1e-3)
    edge = s["ceiling edge at an opening"]
    assert edge["qty"] == pytest.approx(HAND["dome_edge"], abs=1e-3)
    assert "run along beam pieces" in edge["basis"]                       # counted once, in the opening row
    assert r["paint_owner_m2"] == pytest.approx(HAND["horiz_r3"] + HAND["own_r3"], abs=3e-4)
    by = {p[0]: p[2].area for p in parts}
    assert by["W-B1"] == pytest.approx(0.36, abs=1e-6) and by["W-STAIR"] == pytest.approx(1.2 * 2.6, abs=1e-6)
    assert outside == pytest.approx(0.0, abs=1e-6)


def test_r2_one_face_clip_is_the_defect_r3_fixes():
    """the R2 figure keeps the 0.360 m2 of flight under B1 as decor ceiling and the B1 / RB1 edges at the stair and
    the dome as bulkheads; the hand difference is exactly the two named causes."""
    room, faces, treads, disc = villa_w()
    rec = CR.overlay(room, faces, domes=[disc])
    rec.update({"face": "W-R1", "floor": "1F", "name": "Hall"})
    rows, tot = CR.ledger(rec, "DRY", "DRAWING-CONFIRMED", "villa W hall")
    assert tot["horiz_DRY"] == pytest.approx(HAND["horiz_r2"], abs=2e-4)
    assert tot["own_bulk_m2"] == pytest.approx(HAND["own_r2"], abs=2e-4)
    r = run()[0]
    assert tot["horiz_DRY"] - r["horizontal_m2"] == pytest.approx(0.36, abs=1e-4)
    assert tot["own_bulk_m2"] - r["owner_bulkhead_m2"] == pytest.approx(2.4 * 0.15 + 2 * math.pi * 0.15, abs=2e-4)


# ------------------------------------------------------------------------------------------- adverse cases
def test_adverse_hidden_stair_beyond_face_one_face_split_refused():
    room, faces, treads, disc = villa_w()
    fp = unary_union([p for _, p in C3.flight_footprints(treads)[0]])
    with pytest.raises(C3.LedgerError, match="beyond face"):
        C3.single_face_split_refused(fp, faces[0][2], [(i, c, p) for i, c, p, _ in faces[1:]])


def test_adverse_stair_inside_its_face_passes_single_face_check():
    fp = box(0, 0.4, 1.2, 2.9)
    room, faces, *_ = villa_w()
    assert C3.single_face_split_refused(fp, faces[0][2], [(i, c, p) for i, c, p, _ in faces[1:]]) == 0.0


def test_adverse_overlapping_faces_refused():
    fp = box(0, 0, 2, 2)
    with pytest.raises(C3.LedgerError, match="overlap"):
        C3.stair_zone_parts(fp, [("A", "STAIR", box(0, 0, 2, 1.5)), ("B", "BEAM", box(0, 1, 2, 2))])


def test_part_over_a_wall_is_named_not_dropped():
    fp = box(0, 0, 2, 2)
    parts, outside = C3.stair_zone_parts(fp, [("A", "STAIR", box(0, 0, 2, 1.8))])
    assert outside == pytest.approx(0.4, abs=1e-6) and parts[0][2].area == pytest.approx(3.6)


def test_adverse_tangent_is_not_a_border():
    """a straight band edge touching the dome circle at one point borders nothing (contact not stable)."""
    room = box(0, 0, 8, 6)
    disc = Point(6, 3).buffer(1.0, Q)
    band = box(0, 4.0, 8, 4.4)                                      # south edge y = 4.0 tangent to the disc top
    b = C3.border_segments(band, room, [("DOME_OPEN", disc)])
    assert b.get("DOME_OPEN", 0.0) == 0.0 and b["decor"] == pytest.approx(16.0, abs=1e-6)


def test_adverse_dog_leg_is_two_flights_not_one_hull():
    tr = [(f"w{i}", (0.0, 0.3 * i), (1.15, 0.3 * i)) for i in range(5)] + \
         [(f"e{i}", (1.35, 0.3 * i + 0.25), (2.5, 0.3 * i + 0.25)) for i in range(5)]
    fl, loose = C3.flight_footprints(tr)
    assert len(fl) == 2 and not loose
    assert sum(p.area for _, p in fl) == pytest.approx(2 * 1.15 * 1.2, abs=1e-9)


def test_adverse_border_split_not_closing_refused():
    with pytest.raises(C3.LedgerError, match="does not close"):
        C3.bulkhead_split(5.0, {"decor": 2.0, "STAIR_ZONE": 2.5}, 0.75, "CALCULATED")


def test_adverse_conflict_beam_edge_stays_held_on_decor_side_only():
    s = C3.bulkhead_split(4.35, {"decor": 3.0351, "DOME_OPEN": 1.3149}, None, "CONFLICT")
    assert s["owner_m2"] == 0.0 and s["held_lm"] == pytest.approx(3.0351) and s["opening_lm"] == {"DOME_OPEN": 1.3149}


def test_adverse_held_surface_never_zero():
    with pytest.raises(C3.LedgerError, match="never carries 0"):
        C3._s("stair zone", 0.0, "m2", "HELD", "x")


def test_adverse_stair_beyond_larger_than_decor_refused():
    room, faces, treads, disc = villa_w()
    rec = CR.overlay(room, faces, domes=[disc])
    rec.update({"face": "W-R1", "floor": "1F", "name": "Hall"})
    rows, _ = CR.ledger(rec, "DRY", "DRAWING-CONFIRMED", "villa W hall")
    with pytest.raises(C3.LedgerError, match="exceeds the decor ceiling"):
        C3.face_r3(rec, rows, {"stair_beyond": [("W-B1", 99.0)], "beams": {}})


def test_units_metres_only():
    room, faces, treads, disc = villa_w(lambda g: affinity.scale(g, 1000, 1000, origin=(0, 0)))
    rec = CR.overlay(room, faces, domes=[disc])
    rec.update({"face": "W-R1", "floor": "1F", "name": "Hall", "unit": "mm"})
    with pytest.raises(CR.LedgerError, match="unit"):
        CR.ledger(rec, "DRY", "DRAWING-CONFIRMED", "villa W hall")


# ------------------------------------------------------------------------------------------- Alsenan pins
def test_alsenan_outputs_reproduce():
    r = subprocess.run([sys.executable, "-I", str(HERE / "t283_build.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_alsenan_totals_and_causes():
    s = json.loads((HERE / "summary.json").read_text())
    t = s["totals"]
    assert t["horizontal_m2"]["villa"] == pytest.approx(361.2287, abs=1e-4)
    assert t["horizontal_m2"]["villa"] - 363.1732 == pytest.approx(-1.9444, abs=2e-4)       # stair beyond, named
    assert t["owner_bulkhead_m2"]["villa"] == pytest.approx(27.9345, abs=1e-4)
    assert s["held_by_surface"]["stair zone beyond the stair face [m2]"] == pytest.approx(1.9444, abs=1e-4)
    assert s["held_by_surface"]["beam edge at a stair zone [m]"] == pytest.approx(8.0773, abs=1e-4)
    assert t["horizontal_by_class_m2"]["DRY"] + t["horizontal_by_class_m2"]["WET"] == \
        pytest.approx(t["horizontal_m2"]["villa"], abs=2e-4)


def test_alsenan_every_piece_once_and_held_never_zero():
    e = json.loads((HERE / "CEILING_LEDGER_R3_EXPORT.json").read_text())
    ids = [r["face_id"] for r in e["records"]]
    assert len(ids) == len(set(ids)) == 39
    for r in e["records"]:
        for s in r["surfaces"]:
            if s["status"] in ("HELD", "UNKNOWN"):
                assert s["qty"] != 0
    d = {x["DOME"]: x for x in e["domes"]}
    assert set(d) == {"west", "east"}
    for x in d.values():
        assert float(x["OVER_FLOOR_PIECES_M2"]) + float(x["OVER_WALLS_OR_OUTSIDE_M2"]) == \
            pytest.approx(float(x["OPEN_DISC_M2"]), abs=2e-4)


def test_alsenan_no_coordinates_committed():
    for n in ("ALSENAN_T283_DELTAS.json", "CEILING_LEDGER_R3_EXPORT.json", "summary.json"):
        t = (HERE / n).read_text()
        assert "POLYGON" not in t and "coords" not in t and "wkt" not in t
