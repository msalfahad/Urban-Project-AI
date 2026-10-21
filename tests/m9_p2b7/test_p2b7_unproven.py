"""Phase 2B-7 Section 3: the five proposals the authorization asks to validate separately - each with adversarial
synthetic drawings and an independent proof (tests/m9_p2b7/p2b7_indep: ezdxf and math only, no engine module).

    1  per-line source-entity provenance  every traced entity resolves in the DXF (handle, insert path, block
                                          membership); a room line's entities run along the room's boundary within
                                          1 mm and leave uncovered only its openings; a wall line's entities lie on a
                                          face of a wall of its family; an opening's entities lie at the opening
    2  door opening-position recomputation the engine's opening centre and width equal the middle and span of the
                                          extreme full-thickness door-layer jamb lines read from the DXF, moved,
                                          turned, mirrored, in metres and nested
    3  zero-length segment repair         wp_geometry.segments / dedupe on hand-made rings: a piece <= 0.1 mm merged
                                          (V2.7 only), a 2 mm piece kept, lengths conserved, the V2.6 call unchanged
    4  nested-plan door scoping           a door block whose frame lines are read from its own insert, not from a
                                          group block or the plan blocks around it
    5  WC recognition from fixture geometry  more adversaries (a bidet, a chair, a detached cistern) stay REVIEW;
                                          two known errors are recorded as strict xfails (a round-bowl W.C. missed,
                                          an armchair drawn with a W.C.'s outline taken for one)"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / "m9_p2b5_bench"))

ezdxf = pytest.importorskip("ezdxf")

import p2b7_fixtures as F                                     # noqa: E402
import p2b7_indep as I                                        # noqa: E402
import p2b7_run as R                                          # noqa: E402

TOL_M = 0.001
ARC_TOL_M = 0.001 + 1e-6                     # the room polygon follows an arc by chords of sagitta <= 1 mm


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b7_unproven")


def _bench(work, case, kind=None):
    import bench_cases as BC
    import bench_drawings as BD
    dxf = work / f"{case}.dxf"
    if not dxf.exists():
        BD.dxf(BC.BY_ID[case], dxf)
    if kind is None:
        return dxf
    return F.variant(dxf, work / f"{case}_{kind}.dxf", kind)


def _crossing(work, kind=None):
    dxf = work / "CROSSING.dxf"
    if not dxf.exists():
        F.door_plan(dxf, "CROSSING")
    return dxf if kind is None else F.variant(dxf, work / f"CROSSING_{kind}.dxf", kind)


def _villa(work, kind=None):
    from tools import arch_synth as AS
    dxf = work / "villa.dxf"
    if not dxf.exists():
        AS.villa(dxf)
    return dxf if kind is None else F.variant(dxf, work / f"villa_{kind}.dxf", kind)


CASES = {
    "CROSSING": lambda w: (_crossing(w), F.ROLES),
    "CROSSING_rot30": lambda w: (_crossing(w, "rot30"), F.ROLES),
    "CROSSING_mirror": lambda w: (_crossing(w, "mirror"), F.ROLES),
    "CROSSING_metres": lambda w: (_crossing(w, "metres"), F.ROLES),
    "CROSSING_nest": lambda w: (_crossing(w, "nest"), F.ROLES),
    "B10": lambda w: (_bench(w, "B10"), None),
    "B10_nest": lambda w: (_bench(w, "B10", "nest"), None),
    "B02": lambda w: (_bench(w, "B02"), None),
    "B09": lambda w: (_bench(w, "B09"), None),
    "villa": lambda w: (_villa(w), None),
}


@pytest.fixture(scope="module")
def runs(work):
    cache = {}

    def get(name):
        if name not in cache:
            dxf, roles = CASES[name](work)
            out = R.run(dxf, work / f"o_{name}", roles=roles, facts=True)
            cache[name] = (dxf, out, ezdxf.readfile(str(dxf)))
        return cache[name]
    return get


# -- 1  per-line source-entity provenance ------------------------------------------------------------------------------

@pytest.mark.parametrize("name", list(CASES))
def test_provenance_every_entity_resolves(runs, name):
    """every reference on every line names a live entity of the DXF, placed by INSERTs that really contain it
    (outermost first); every measured room line and every wall line is traced (no NOT_TRACED among them)."""
    dxf, out, doc = runs(name)
    seen, bases = set(), set()
    for ln in R.lines(out):
        e = ln["source"]["entities"]
        bases.add(e["basis"])
        for ref in e["entities"]:
            if ref["id"] not in seen:
                I.resolve(doc, ref)
                seen.add(ref["id"])
        if (ln.get("location") or {}).get("room_id") in {r["room_id"] for r in R.rooms(out)}:
            assert e["basis"] in ("ROOM_BOUNDARY", "OPENING") and e["entities"], ln["item_code"]
        if str(ln.get("physical_element") or "").startswith("walls t="):
            assert e["basis"] == "WALL_BANDS" and e["entities"], ln["item_code"]
    assert seen and "ROOM_BOUNDARY" in bases
    if name.endswith("nest"):
        # the plan's own linework is two inserts deep, a door block's three
        assert all(len(x.split("@")[1].split("/")) >= 2 for x in seen if "@" in x) and \
            any("@" in x for x in seen)


@pytest.mark.parametrize("name", list(CASES))
def test_provenance_room_entities_run_along_the_boundary(runs, name):
    """for each measured room: every entity attached to its lines has at least 10 mm (or all of itself, if shorter)
    within 1 mm of the room's boundary; and the boundary not within 1 mm of any of them is no longer than the room's
    openings (door, passage and window thresholds and open edges, by the room's own run record) + 2 mm."""
    dxf, out, doc = runs(name)
    rooms = {r["room_id"]: r for r in R.rooms(out)}
    by_room = {}
    for ln in R.lines(out):
        e = ln["source"]["entities"]
        if e["basis"] == "ROOM_BOUNDARY":
            by_room.setdefault(e["room_id"], {x["id"]: x for x in e["entities"]})
    assert by_room
    for rid, refs in by_room.items():
        r = rooms[rid]
        rings = [r["polygon_m"]] + list(r.get("hole_polygons_m") or ())
        tol = ARC_TOL_M
        geo = {k: I.world(doc, ref) for k, ref in refs.items()}
        for k, g in geo.items():
            pts = I.sample(g, 0.002)
            near = sum(1 for p in pts if min(I.d_poly(p, ring, closed=True) for ring in rings) <= tol)
            assert near * 0.002 >= min(0.010, I.length(g)) - 0.002, (name, rid, k, near, I.length(g))
        runs_ = r["runs_lm"]
        allowed = sum(runs_.get(x, 0.0) for x in ("door", "passage", "window_threshold", "other")) + 0.002
        uncovered = 0.0
        for ring in rings:
            for i in range(len(ring)):
                a, b = ring[i], ring[(i + 1) % len(ring)]
                L = math.dist(a, b)
                n = max(1, int(L / 0.002))
                for j in range(n):
                    p = (a[0] + (b[0] - a[0]) * (j + 0.5) / n, a[1] + (b[1] - a[1]) * (j + 0.5) / n)
                    if all(I.d_poly(p, g) > tol for g in geo.values()):
                        uncovered += L / n
        assert uncovered <= allowed, (name, rid, round(uncovered, 4), round(allowed, 4))


@pytest.mark.parametrize("name", ["CROSSING", "CROSSING_rot30", "CROSSING_nest", "B10", "villa"])
def test_provenance_wall_entities_lie_on_a_wall_face(runs, name):
    """every entity of a wall line lies, for at least 10 mm, within 1 mm of a face of a wall of that thickness family
    on that floor (a straight wall: the centreline offset by t/2 within its run; a curved band: its two radii)."""
    dxf, out, doc = runs(name)
    W = R.load(out, "ARCH_WALLS.json")["floors"]
    k = I.unit_m(doc)
    for ln in R.lines(out):
        e = ln["source"]["entities"]
        if e["basis"] != "WALL_BANDS":
            continue
        walls = [w for fl in W if fl["floor"] == e["floor"] for w in fl["walls"] if w["family"] == e["family"]]
        assert walls
        for ref in e["entities"]:
            pts = I.sample(I.world(doc, ref), 0.002)

            def on_face(p):
                for w in walls:
                    if w.get("curved"):
                        c = w["curved"]["centre"]
                        d = math.dist(p, (c[0] * k, c[1] * k))
                        if min(abs(d - w["curved"]["r1_m"]), abs(d - w["curved"]["r2_m"])) <= TOL_M:
                            return True
                        continue
                    (x0, y0), (x1, y1) = [(x * k, y * k) for x, y in w["centreline"]]
                    L = math.dist((x0, y0), (x1, y1))
                    u = ((x1 - x0) / L, (y1 - y0) / L)
                    s = (p[0] - x0) * u[0] + (p[1] - y0) * u[1]
                    o = -(p[0] - x0) * u[1] + (p[1] - y0) * u[0]
                    if -TOL_M <= s <= L + TOL_M and abs(abs(o) - w["t_m"] / 2) <= TOL_M:
                        return True
                return False
            near = sum(1 for p in pts if on_face(p))
            assert near * 0.002 >= min(0.010, I.length(I.world(doc, ref))) - 0.002, (name, ref["id"])


@pytest.mark.parametrize("name", ["CROSSING", "CROSSING_mirror", "CROSSING_nest", "B02", "B10_nest", "villa"])
def test_provenance_opening_entities_lie_at_the_opening(runs, name):
    """every entity of an opening line lies at its opening: a door's (its swing, its jamb lines) within a leaf's reach
    of a jamb (a leaf at most the opening + 0.10 m), a window's glazing inside the opening box (centre +- width / 2 along the
    wall, +- t / 2 across it, 1 mm), a passage's wall faces end at a corner of its gap (1 mm)."""
    dxf, out, doc = runs(name)
    ops = {(o["floor"], o["opening_id"]): o for o in R.openings(out)}
    traced = 0
    for ln in R.lines(out):
        e = ln["source"]["entities"]
        if e["basis"] != "OPENING" or not e["entities"]:
            continue
        o = ops[(e["floor"], e["opening_id"])]
        c, (ux, uy) = o["position"]["centre_m"], o["position"]["wall_axis"]
        for ref in e["entities"]:
            for p in I.world(doc, ref):
                s = (p[0] - c[0]) * ux + (p[1] - c[1]) * uy
                n = -(p[0] - c[0]) * uy + (p[1] - c[1]) * ux
                if o["kind"] == "WINDOW":
                    assert abs(s) <= o["width_m"] / 2 + TOL_M and abs(n) <= o["wall_t_m"] / 2 + TOL_M, (name, ref)
                elif o["kind"] == "DOOR":                    # a jamb corner + a leaf of at most the opening + 0.10
                    reach = math.hypot(o["width_m"] / 2, o["wall_t_m"] / 2) + o["width_m"] + 0.10
                    assert math.hypot(s, n) <= reach + TOL_M, (name, ref)
            if o["kind"] == "PASSAGE":                       # a wall face ending at a jamb corner of the gap
                assert any(abs(abs(s_) - o["width_m"] / 2) <= TOL_M and abs(abs(n_) - o["wall_t_m"] / 2) <= TOL_M
                           for p in I.world(doc, ref)
                           for s_, n_ in [((p[0] - c[0]) * ux + (p[1] - c[1]) * uy,
                                           -(p[0] - c[0]) * uy + (p[1] - c[1]) * ux)]), (name, ref)
            traced += 1
    assert traced


def test_provenance_block_door_through_a_mirrored_insert(runs):
    """B02: the door is a block inserted mirrored (x scale -1). Its swing is traced through the insert and its world
    arc - read through the insert's matrix by ezdxf - has its centre (the hinge) on a jamb of the 0.80 m opening at
    the wall face, and its radius is the leaf (0.80 m: the block's unit door)."""
    dxf, out, doc = runs("B02")
    d = [o for o in R.openings(out) if o["kind"] == "DOOR"][0]
    refs = [x for ln in R.lines(out) if ln["source"]["entities"].get("opening_id") == d["opening_id"]
            for x in ln["source"]["entities"]["entities"]]
    arc = next(x for x in refs if I.resolve(doc, x)[0].dxftype() == "ARC")
    e, ins = I.resolve(doc, arc)
    assert ins and ins[-1].dxf.xscale < 0
    pts = I.world(doc, arc)
    (ax, ay), (bx, by), (cx, cy) = pts[0], pts[len(pts) // 2], pts[-1]
    dd = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    hinge = (((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / dd,
             ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / dd)
    assert all(abs(math.dist(hinge, p) - 0.8) < 1e-6 for p in pts)
    c, (ux, uy) = d["position"]["centre_m"], d["position"]["wall_axis"]
    s = (hinge[0] - c[0]) * ux + (hinge[1] - c[1]) * uy
    n = -(hinge[0] - c[0]) * uy + (hinge[1] - c[1]) * ux
    assert abs(abs(s) - d["width_m"] / 2) < TOL_M and abs(abs(n) - d["wall_t_m"] / 2) < TOL_M


# -- 2  door opening-position recomputation ---------------------------------------------------------------------------

@pytest.mark.parametrize("plan", ["CROSSING", "PLAIN"])
@pytest.mark.parametrize("kind", [None, "translate", "rot30", "mirror", "metres", "nest"])
def test_opening_position_from_the_drawn_jambs(work, plan, kind):
    """the door's position (centre at mid wall) and width are the middle and span of the extreme full-thickness
    A-DOOR lines (jamb and frame lines, 0.20 m long) read from the DXF by ezdxf, through every block level - to
    1 mm, in every placement. CROSSING: (1.400, 0.100), 0.80 m in the base drawing (V2.6: (1.5135, 0.100) - the
    middle of the whole 1.027 m wall gap)."""
    base = work / f"{plan}.dxf"
    if not base.exists():
        F.door_plan(base, plan)
    dxf = base if kind is None else F.variant(base, work / f"{plan}_{kind}.dxf", kind)
    out = R.run(dxf, work / f"o_pos_{plan}_{kind}", roles=F.ROLES, facts=True)
    d = R.openings(out, "DOOR")
    assert len(d) == 1
    j = I.jamb_span(ezdxf.readfile(str(dxf)), F.DOOR, 0.2)
    assert abs(d[0]["width_m"] - j["width_m"]) <= TOL_M
    assert math.dist(d[0]["position"]["centre_m"], j["centre_m"]) <= TOL_M, (d[0]["position"], j)
    if kind is None:
        assert d[0]["position"]["centre_m"] == [1.4, 0.1]


def test_opening_position_v26_as_found(work):
    """V2.6 keeps the middle of the whole wall gap (1.000 .. 2.027 m) - the as-found value, unchanged."""
    out = R.run(_crossing(work), work / "o_pos_v26", roles=F.ROLES, facts=True, method=R.V26)
    d = R.openings(out, "DOOR")[0]
    assert d["position"]["centre_m"] == [1.5135, 0.1]


# -- 3  zero-length segment repair -------------------------------------------------------------------------------------

def _wg():
    from engine.source import wp_geometry as WG
    return WG


def _square(L=3.0):
    return [(0.0, 0.0), (L, 0.0), (L, L), (0.0, L)]


def _walls(gaps=()):
    """WALL features on the four sides of the 3 x 3 m square; gaps: [(side, at_end_m)] shortens a side's feature by
    at_end_m at its far end."""
    sq = _square()
    out = []
    for i in range(4):
        a, b = sq[i], sq[(i + 1) % 4]
        cut = dict(gaps).get(i, 0.0)
        L = math.dist(a, b)
        bb = (a[0] + (b[0] - a[0]) * (L - cut) / L, a[1] + (b[1] - a[1]) * (L - cut) / L)
        out.append({"role": "WALL", "id": f"W{i}", "a": a, "b": bb})
    return out


@pytest.mark.parametrize("cut", [5e-5, 9.9e-5])
def test_sliver_merged_under_v27(cut):
    """a wall feature ending 0.05 / 0.099 mm short of a corner: V2.6 types the piece OTHER (an open edge), V2.7
    merges it into the wall; the ring's length is conserved (12.000 m) either way."""
    WG = _wg()
    v26 = WG.segments(_square(), _walls([(1, cut)]))
    v27 = WG.segments(_square(), _walls([(1, cut)]), sliver_m=WG.SLIVER_M)
    assert [s["role"] for s in v26].count("OTHER") == 1
    assert all(s["role"] == "WALL" for s in v27) and len(v27) == 4
    for segs in (v26, v27):
        assert abs(sum(s["length_m"] for s in segs) - 12.0) < 1e-12


def test_real_gap_kept():
    """a 2 mm gap at a corner is a drawn gap, not a rounding error: OTHER in both readings, 0.002 m long."""
    WG = _wg()
    for kw in ({}, {"sliver_m": WG.SLIVER_M}):
        segs = WG.segments(_square(), _walls([(1, 0.002)]), **kw)
        other = [s for s in segs if s["role"] == "OTHER"]
        assert len(other) == 1 and abs(other[0]["length_m"] - 0.002) < 1e-12


def test_sliver_between_two_roles():
    """a 0.05 mm untyped piece between a WALL run and a DOOR threshold on one edge joins the piece before it; the
    threshold keeps its 0.80 m."""
    WG = _wg()
    f = _walls()
    f[0] = {"role": "WALL", "id": "W0", "a": (0.0, 0.0), "b": (1.0 - 5e-5, 0.0)}
    f.append({"role": "WALL", "id": "W0b", "a": (1.8, 0.0), "b": (3.0, 0.0)})
    f.append({"role": "DOOR", "id": "T", "a": (1.0, 0.0), "b": (1.8, 0.0)})
    segs = [s for s in WG.segments(_square(), f, sliver_m=WG.SLIVER_M) if s["edge"] == 0]
    assert [s["role"] for s in segs] == ["WALL", "DOOR", "WALL"]
    assert abs(segs[1]["length_m"] - 0.8) < 1e-12 and abs(segs[0]["length_m"] - 1.0) < 1e-12


def test_dedupe_ring():
    """a vertex 0.03 mm from the one before it is dropped; a vertex 2 mm away is kept; the closing vertex too."""
    WG = _wg()
    ring = [(0.0, 0.0), (3.0, 0.0), (3.0, 3e-5), (3.0, 3.0), (0.0, 3.0), (0.0, 0.002)]
    out = WG.dedupe(ring, WG.SLIVER_M)
    assert out == [(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0), (0.0, 0.002)]


def test_rot37_metres_has_no_sliver_termination(work):
    """the drawing that exposed the sliver (CROSSING turned 37 degrees and rescaled to metres): no OTHER piece and no
    termination of kind OTHER in the bathroom's waterproofing; V2.6 as found: one."""
    dxf = _crossing(work, "rot37_metres")
    out = R.run(dxf, work / "o_rot37", roles=F.ROLES, facts=True)
    up = [ln for ln in R.lines(out) if ln["item_code"] == "FIN.WP.WALL_UPTURN"][0]
    assert "OTHER" not in up["calculation"]["inputs"]["by_role_lm"]
    assert not [ln for ln in R.lines(out) if ln["item_code"] == "FIN.WP.TERMINATION" and
                ln["calculation"]["inputs"].get("kind") == "OTHER"]


# -- 4  nested-plan door scoping --------------------------------------------------------------------------------------

def _framed(work, kind, method=R.V27):
    dxf = work / f"FR_{kind}.dxf"
    if not dxf.exists():
        F.framed_door_plan(dxf, kind)
    return R.run(dxf, work / f"o_fr_{kind}_{method[-3:]}", roles=F.ROLES, facts=True, method=method)


@pytest.mark.parametrize("kind", ["FLAT", "GROUP", "NEST", "GROUP_NEST"])
def test_door_block_frame_from_its_own_insert(work, kind):
    """the frame of the door block is the span of the block's own lines in the wall strip (0.80 m) whether the block
    sits in model space, in a group block with a window's glazing in the same wall, or in a plan nested two levels
    deep; the door is released and every quantity equals FLAT's."""
    out = _framed(work, kind)
    el = R.load(out, "DOOR_SCHEDULE.json")["doors"]["elements"]
    assert len(el) == 1 and el[0]["frame_width_m"] == F.FRAMED_TRUTH["frame_m"] and el[0]["released"]
    assert [o["width_m"] for o in R.openings(out, "DOOR")] == [F.FRAMED_TRUTH["door_m"]]
    assert sorted(o["width_m"] for o in R.openings(out, "WINDOW")) == F.FRAMED_TRUTH["windows_m"]
    assert [r["area_m2"] for r in R.room(out, "Bath")] == [F.FRAMED_TRUTH["bath_m2"]]
    assert R.invariant(_framed(work, "FLAT"), out, tol=1e-9)


@pytest.mark.parametrize("kind,frame", [("FLAT", 0.8), ("GROUP", 2.4), ("NEST", 4.4), ("GROUP_NEST", 4.4)])
def test_door_block_frame_v26_as_found(work, kind, frame):
    """V2.6 as found: the frame is read from the OUTERMOST insert of the swing's path - the group pools the window's
    glazing (2.80 .. 3.40 m: frame 2.40 m), the plan blocks pool the whole south wall (4.40 m); the door is then
    withheld (not released). Kept in V2.6 (frozen)."""
    out = _framed(work, kind, R.V26)
    el = R.load(out, "DOOR_SCHEDULE.json")["doors"]["elements"][0]
    assert el["frame_width_m"] == frame and el["released"] == (kind == "FLAT")


# -- 5  WC recognition from sanitary fixture geometry ------------------------------------------------------------------

def _lobby(work, kind):
    dxf = work / f"WC_{kind}.dxf"
    if not dxf.exists():
        F.wc_plan(dxf, kind)
    out = R.run(dxf, work / f"o_wc_{kind}", roles=F.ROLES, facts=True)
    lob = [r for r in R.rooms(out) if abs(r["area_m2"] - F.WC_TRUTH["lobby_m2"]) < 1e-6]
    assert len(lob) == 1
    return lob[0]


@pytest.mark.parametrize("kind", ["BASIN_FITTINGS", "BIDET", "CHAIR", "DETACHED"])
def test_wc_adversaries_stay_review(work, kind):
    """the basin's own fittings drawn loose on the sanitary layer beside it (found on the reference plan: a hand-wash
    lobby typed a bathroom by its basins' taps), a bowl with no cistern (a bidet), a chair, a bowl and cistern that
    do not touch: no second piece of evidence - the basin stays alone and the lobby REVIEW (no room type, never
    DRY)."""
    lob = _lobby(work, kind)
    assert not lob["codes"] and lob["issue"].startswith("WET_CLASSIFICATION_REVIEW")


@pytest.mark.xfail(strict=True, reason="KNOWN LIMITATION (V2.7): a W.C. whose bowl is drawn as a circle is not "
                                       "recognised (BOWL_ASPECT 1.15 .. 2.0) - the lobby stays REVIEW, the safe "
                                       "direction; the desired reading is WET")
def test_round_bowl_wc_is_recognised(work):
    assert _lobby(work, "ROUND_BOWL")["codes"] == ["BATHROOM"]


@pytest.mark.xfail(strict=True, reason="KNOWN LIMITATION (V2.7): an armchair drawn with a W.C.'s outline (an "
                                       "elliptical seat 0.45 x 0.55 touching a 0.45 x 0.15 back) passes the shape "
                                       "test; with the basin the lobby is typed a bathroom (flagged "
                                       "ROOM_TYPE_FROM_FIXTURES+WC_SHAPE). Geometry alone cannot separate the two")
def test_seat_lookalike_is_not_a_wc(work):
    assert not _lobby(work, "SEAT_LOOKALIKE")["codes"]
