"""T-317 hand fixture (NOT the development villa): one room 4.0 x 5.0 m, four corner columns 0.30 x 0.30, beams
0.20 x 0.60 (overall, incl. the slab) on every side under a 0.15 m slab, storey 3.50 m slab to slab, block walls
between the columns in plane with the columns' room faces. One 4.0 m face is tiled full height (wet wall).

Hand calculation (metres):
  each room face = col 0.30 | block B | col 0.30, B = 3.40 (4.0 faces) or 4.40 (5.0 faces); block top = beam soffit
  3.50 - 0.60 = 2.90 above the structural floor.
  DRAWING-DERIVED band: floor finish 0.10 .. slab soffit 3.50 - 0.15 = 3.35 (H = 3.25)
    4.0 face: 13.000 = columns 2 x 0.30 x 3.25 = 1.950 + beam band 3.40 x (3.35 - 2.90) = 1.530 -> concrete 3.480,
              block 3.40 x (2.90 - 0.10) = 9.520
    5.0 face: 16.250 = concrete 1.950 + 4.40 x 0.45 = 1.980 -> 3.930, block 4.40 x 2.80 = 12.320
    room 58.500 m2 = concrete 14.820 + block 43.680
    joints: H inside 2 x 3.40 + 2 x 4.40 = 15.600 m; V 8 x (2.90 - 0.10) = 22.400 m
  OWNER band (the Q-43 / Q-48 A form, measured from the finished floor): FFL = 0.10, height = 3.50 - 0.60 beam
    - 0.15 decor ceiling - 0.10 floor finish = 2.65 -> band 0.10 .. 2.75 above the structural floor (H = 2.65)
    4.0 face: 10.600 = columns 2 x 0.30 x 2.65 = 1.590 + block 3.40 x 2.65 = 9.010 (beam band: 2.90 > 2.75 -> 0)
    5.0 face: 13.250 = 1.590 + 4.40 x 2.65 = 11.660
    room 47.700 m2 = concrete 6.360 + block 41.340
    joints: H all ABOVE_BAND (2.90 > 2.75): 15.600 m listed, none inside; V 8 x (2.75 - 0.10) = 21.200 m
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t317"))
import t317_spatter_mesh as M  # noqa: E402

DD = (0.10, 3.35)
OWN = (0.10, 2.75)


def face(wid, B, cols, band, finish="PLASTER", units="m", k=1.0):
    pcs = [M.Piece("COLUMN", 0.30 * k, None, cols[0]), M.Piece("BLOCK", B * k, 2.90 * k, "BM"),
           M.Piece("COLUMN", 0.30 * k, None, cols[1])]
    sides = [M.Side("R1", finish, band[0] * k, band[1] * k), M.Side("OUT", "NONE", None, None)]
    return M.make_wall(wid, 3.50 * k, pcs, sides, units=units)


def room(band, units="m", k=1.0, tile_first=False):
    return [face("N", 3.40, ("C1", "C2"), band, "TILE" if tile_first else "PLASTER", units, k),
            face("E", 4.40, ("C2", "C3"), band, units=units, k=k),
            face("S", 3.40, ("C3", "C4"), band, units=units, k=k),
            face("W", 4.40, ("C4", "C1"), band, units=units, k=k)]


def split_total(walls):
    claimed = {}
    tot = {"face": 0.0, "conc": 0.0, "blk": 0.0}
    for w in walls:
        for s in w.sides:
            f = M.face_split(w, s, claimed)
            if f["state"] == "MEASURED":
                tot["face"] += f["face_m2"]
                tot["conc"] += f["concrete_m2"]
                tot["blk"] += f["block_m2"]
    return {k: round(v, 6) for k, v in tot.items()}


def test_drawing_derived_faces_hand():
    t = split_total(room(DD))
    assert t == {"face": 58.5, "conc": 14.82, "blk": 43.68}
    w = room(DD)[0]
    f = M.face_split(w, w.sides[0])
    assert (f["face_m2"], f["concrete_m2"], f["block_m2"]) == (13.0, 3.48, 9.52)


def test_owner_band_faces_hand():
    t = split_total(room(OWN))
    assert t == {"face": 47.7, "conc": 6.36, "blk": 41.34}


def test_joints_drawing_derived_hand():
    js = [j for w in room(DD) for j in M.joints(w)]
    h = sum(j["length_m"] for j in js if j["dir"] == "H" and j["class"] == "INSIDE")
    v = sum(j["length_m"] for j in js if j["dir"] == "V" and j["class"] == "INSIDE")
    assert round(h, 6) == 15.6 and round(v, 6) == 22.4
    assert sum(1 for j in js if j["dir"] == "V") == 8
    assert all(j["side"] == "R1" for j in js)          # no joint on the unfinished side


def test_joints_owner_band_hand():
    js = [j for w in room(OWN) for j in M.joints(w)]
    assert not [j for j in js if j["dir"] == "H" and j["class"] == "INSIDE"]
    assert round(sum(j["length_m"] for j in js if j["dir"] == "H" and j["class"] == "ABOVE_BAND"), 6) == 15.6
    assert round(sum(j["length_m"] for j in js if j["dir"] == "V"), 6) == 21.2


def test_band_edge_is_not_inside():
    w = M.make_wall("X", 3.50, [M.Piece("BLOCK", 2.0, 2.75, "BM")], [M.Side("R", "PLASTER", 0.10, 2.75)])
    (j,) = M.joints(w)
    assert j["class"] == "AT_BAND_EDGE"
    rec = M.mesh_records([j], M.Scope("B9-03", "PROJECT-RULE-X", frozenset({"PLASTER"})))
    assert rec == []


def test_tiled_face_kept_apart():
    js = [j for w in room(DD, tile_first=True) for j in M.joints(w)]
    tiled = [j for j in js if j["finish"] == "TILE"]
    assert round(sum(j["length_m"] for j in tiled if j["dir"] == "H"), 6) == 3.4
    assert round(sum(j["length_m"] for j in tiled if j["dir"] == "V"), 6) == 5.6
    scope = M.Scope("B9-03", "PROJECT-RULE-X", frozenset({"PLASTER"}))
    recs = M.mesh_records(js, scope)
    held = [r for r in recs if r["finish"] == "TILE"]
    assert held and all(r["state"] == "HELD" and r["quantity"] is None for r in held)
    meas = [r for r in recs if r["state"] == "MEASURED"]
    assert round(sum(r["quantity"] for r in meas), 6) == round(15.6 - 3.4 + 22.4 - 5.6, 6)


def test_mesh_without_scope_is_held_never_zero():
    js = [j for w in room(DD) for j in M.joints(w)]
    recs = M.mesh_records(js, M.Scope("B9-03", None))
    assert recs and all(r["state"] == "HELD" and r["quantity"] is None for r in recs)
    assert round(sum(r["population_m"] for r in recs), 6) == 38.0
    assert M.check_no_zero_held(recs)


def test_held_as_zero_refused():
    with pytest.raises(M.LedgerError):
        M.check_no_zero_held([{"state": "HELD", "quantity": 0.0}])


def test_default_mesh_width_refused():
    with pytest.raises(M.LedgerError):
        M.Scope("B9-03", "PROJECT-RULE-X", frozenset({"PLASTER"}), {"mesh_width_m": 0.20})


def test_joint_on_unplastered_side_refused():
    bad = {"wall": "N", "side": "OUT", "finish": "NONE", "dir": "H", "at": "BM", "length_m": 3.4, "class": "INSIDE"}
    with pytest.raises(M.LedgerError):
        M.mesh_records([bad], M.Scope("B9-03", None))


def test_column_face_from_both_rooms_refused():
    claimed = {}
    w = room(DD)[0]
    M.face_split(w, w.sides[0], claimed)
    with pytest.raises(M.LedgerError):              # the same face listed again (a second enumeration)
        M.face_split(w, w.sides[0], claimed)
    # wall N's room face seen again from a second room id (rooms split along one wall face): refused
    w2 = M.make_wall("N", 3.50, w.pieces, [M.Side("R2", "PLASTER", 0.10, 3.35), M.Side("OUT", "NONE", None, None)])
    with pytest.raises(M.LedgerError):
        M.face_split(w2, w2.sides[0], claimed)
    # the column's OTHER face of the same plane (the opposite side) and its face on the other wall are distinct
    w3 = M.make_wall("N", 3.50, w.pieces, [M.Side("R1", "PLASTER", 0.10, 3.35), M.Side("R9", "PLASTER", 0.10, 3.35)])
    assert M.face_split(w3, w3.sides[1], claimed)["concrete_m2"] == round(2 * 0.30 * 3.25 + 3.40 * 0.45, 6)
    w4 = room(DD)[1]                                # wall E shares corner column C2 with wall N
    assert M.face_split(w4, w4.sides[0], claimed)["state"] == "MEASURED"


def test_mirror_and_mm_units_identical():
    a = [j for w in room(DD) for j in M.joints(w)]
    b = [j for w in room(DD) for j in M.joints(M.mirrored(w))]
    tot = lambda js: sorted((j["dir"], j["class"], j["length_m"]) for j in js)  # noqa: E731
    assert tot(a) == tot(b)
    c = [j for w in room(DD, units="mm", k=1000.0) for j in M.joints(w)]
    assert tot(a) == tot(c)
    assert split_total(room(DD, units="mm", k=1000.0)) == split_total(room(DD))


def test_mm_read_as_metres_refused():
    with pytest.raises(M.LedgerError):
        room(DD, units="m", k=1000.0)


def test_opening_at_column_holds_that_joint():
    pcs = [M.Piece("COLUMN", 0.30, None, "C1", ("end",)), M.Piece("BLOCK", 2.0, 2.90, "BM")]
    w = M.make_wall("D", 3.50, pcs, [M.Side("R", "PLASTER", 0.10, 3.35)])
    v = [j for j in M.joints(w) if j["dir"] == "V"]
    assert len(v) == 1 and v[0]["class"] == "HELD" and v[0]["length_m"] is None
    vm = [j for j in M.joints(M.mirrored(w)) if j["dir"] == "V"]
    assert vm[0]["class"] == "HELD"


def test_unknown_block_top_held_not_zero():
    w = M.make_wall("U", 3.50, [M.Piece("BLOCK", 2.0, None, "?")], [M.Side("R", "PLASTER", 0.10, 3.35)])
    f = M.face_split(w, w.sides[0])
    assert f["state"] == "HELD" and f["face_m2"] is None
    (j,) = M.joints(w)
    assert j["class"] == "HELD"


def test_spatter_is_the_host_population_once():
    hosts = [
        {"line_id": "L-1", "finish": "PLASTER", "faces": ["N", "E"], "state": "DRAWING-CONFIRMED", "quantity": 29.25},
        {"line_id": "L-2", "finish": "TILE", "faces": ["S"], "state": "ASSUMED — OWNER-APPROVED", "quantity": 13.0},
        {"line_id": "L-3", "finish": "PLASTER", "faces": ["W"], "state": "HELD", "quantity": None, "lo": 15.0,
         "hi": 16.25},
    ]
    scope = M.Scope("B4-05", "OD-V3B-4/5", frozenset({"PLASTER", "TILE"}))
    recs = M.spatter_records(hosts, scope)
    assert [r["quantity"] for r in recs] == [29.25, 13.0, None]
    assert recs[2]["state"] == "HELD" and (recs[2]["lo"], recs[2]["hi"]) == (15.0, 16.25)
    assert all(r["candidate_line"] == "NO LINE" for r in recs)
    M.check_no_zero_held(recs)
    # the substrate split of the measured faces closes to the host population (58.5 m2 drawing-derived room)
    assert round(29.25 + 13.0 + 16.25, 6) == split_total(room(DD))["face"]


def test_spatter_face_in_two_hosts_refused():
    hosts = [{"line_id": "L-1", "finish": "PLASTER", "faces": ["N"], "state": "VERIFIED", "quantity": 1.0},
             {"line_id": "L-2", "finish": "TILE", "faces": ["N"], "state": "VERIFIED", "quantity": 1.0}]
    with pytest.raises(M.LedgerError):
        M.spatter_records(hosts, M.Scope("B4-05", "OD", frozenset({"PLASTER", "TILE"})))


def test_spatter_without_scope_held():
    hosts = [{"line_id": "L-1", "finish": "SIGMA", "faces": ["X"], "state": "VERIFIED", "quantity": 10.0}]
    (r,) = M.spatter_records(hosts, M.Scope("B4-05", None))
    assert r["state"] == "HELD" and r["quantity"] is None and r["population"][0] == 10.0
    (r,) = M.spatter_records(hosts, M.Scope("B4-05", "OD", frozenset({"PLASTER"})))
    assert r["state"] == "HELD"


def test_held_host_with_figure_refused():
    with pytest.raises(M.LedgerError):
        M.spatter_records([{"line_id": "L", "finish": "PLASTER", "state": "HELD", "quantity": 0.0}],
                          M.Scope("B4-05", "OD", frozenset({"PLASTER"})))


def test_drawing_derived_to_soffit_hand():
    walls = []
    for w in room(DD):
        ps = tuple(M.Piece(p.kind, p.length, p.top, p.member, p.opening_at, "BEAM" if p.kind == "BLOCK" else "")
                   for p in w.pieces)
        walls.append(M.Wall(w.wall_id, w.storey_h, ps, w.sides))
    js = [j for w in walls for j in M.joints_to_soffit(w, 0.10)]
    assert round(sum(j["length_m"] for j in js if j["dir"] == "H" and j["class"] == "INSIDE"), 6) == 15.6
    assert round(sum(j["length_m"] for j in js if j["dir"] == "V"), 6) == 22.4
    # a block straight under the slab soffit meets the ceiling at the wall / ceiling corner: not inside the face
    w = M.make_wall("S", 3.50, [M.Piece("BLOCK", 2.0, 3.35, "SL", (), "SLAB")], [M.Side("R", "PLASTER", 0.10, 3.35)])
    (j,) = M.joints_to_soffit(w, 0.10)
    assert j["class"] == "AT_BAND_EDGE"


def test_step_joint_where_the_member_changes_level():
    # block 2.0 under a 0.60 beam (top 2.90) then 1.5 under a 0.90 crossing beam (top 2.60): step 0.30 m
    pcs = [M.Piece("BLOCK", 2.0, 2.90, "B1", (), "BEAM"), M.Piece("BLOCK", 1.5, 2.60, "B2", (), "BEAM")]
    w = M.make_wall("T", 3.50, pcs, [M.Side("R", "PLASTER", 0.10, 3.35)])
    st = [j for j in M.joints(w) if j["dir"] == "STEP"]
    assert len(st) == 1 and st[0]["length_m"] == 0.3
    # owner band 0.10 .. 2.75: only 2.75 - 2.60 = 0.15 of the step is inside the band
    w2 = M.make_wall("T", 3.50, pcs, [M.Side("R", "PLASTER", 0.10, 2.75)])
    st2 = [j for j in M.joints(w2) if j["dir"] == "STEP"]
    assert st2[0]["length_m"] == 0.15
    # both tops above the band: no step inside
    pcs3 = [M.Piece("BLOCK", 2.0, 3.00, "B1", (), "BEAM"), M.Piece("BLOCK", 1.5, 2.90, "B2", (), "BEAM")]
    w3 = M.make_wall("T", 3.50, pcs3, [M.Side("R", "PLASTER", 0.10, 2.75)])
    assert [j["class"] for j in M.joints(w3) if j["dir"] == "STEP"] == ["ABOVE_BAND"]
    assert [j["length_m"] for j in M.joints_to_soffit(M.mirrored(w), 0.10) if j["dir"] == "STEP"] == [0.3]
