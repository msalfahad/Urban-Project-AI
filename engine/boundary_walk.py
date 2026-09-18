"""E1.3 corrected — the boundary a point stands inside, walked edge by edge.

THE FAILURE THIS REPLACES

Three constructions were tried for a region that drawn material does not
enclose, and a cold challenge or a plain look at the overlay destroyed
each one:

  a local window closed around the point. engine.cad_geometry.trace walks
  face.exterior only, so a face's HOLES are dropped; for an unenclosed
  point the smallest containing face is the free space AROUND the blocks,
  its exterior is the window, and the rooms inside it are exactly the
  holes that get dropped. The challenger saw the result and named it -
  adjacent rooms held out as islands;

  a fan of sight lines from the point, taking the first material met in
  every direction. A sight line that leaves through an opening lands on
  the far wall of a space twenty metres away, so a PANTRY was proposed a
  boundary reaching into the stair core and two bathrooms;

  the same fan with what lies past a wall end removed. It removed almost
  everything, and left the PANTRY one partition.

What all three have in common is that they SELECT material by where it
is, rather than by what it bounds. Distance, direction and enclosure by a
window are not evidence about a boundary.

WHAT THIS DOES INSTEAD

A boundary is walked. It starts on one face of one wall and follows the
material, and each step is a step onto material that continues the same
side of the same space. Where the material ends and a classified gap
carries the boundary across, the walk crosses it and says which class of
gap it was. Where the material simply ends, THE WALK STOPS and says so.
Nothing is bridged to reach something further away, so no element of the
chain can belong to a space on the other side of an opening.

The face of a wall that the walk is on is decided by evidence and not by
convenience:

  where two faces are PAIRED at a separation that belongs to a wall
  thickness family inferred from this drawing, they are the two faces of
  one wall body, and the one that bounds this space is the one on the
  side the space is on;

  where no pair is established, the single line is the face, and that is
  recorded - it is not assumed to be a centre line, and no thickness is
  invented for it.

Never: the nearest face, the face that closes the chain, the face that
makes the area larger or smaller, or a face named by a challenger.
"""

from __future__ import annotations

import hashlib
import math

MODEL = "A_BOUNDARY_IS_WALKED_FROM_FACE_TO_FACE_V1"

# Two endpoints this close are the same node. Taken from the same snap the
# rest of the system nodes CAD geometry with.
NODE_SNAP_MM = 1.0

# Two faces are candidates to be a pair when their directions agree to
# this, and they overlap along their shared direction by at least this.
PARALLEL_DEG = 3.0
MIN_PAIR_OVERLAP_MM = 150.0

# A separation counts as a wall thickness when it sits within this of a
# thickness family inferred from the drawing under test.
THICKNESS_TOLERANCE_MM = 15.0

# Noding drawn geometry leaves behind pieces of no length. A piece with no
# length has no direction, so a walk that stepped onto one could not take
# the turn at the next node. They are dropped.
MIN_PIECE_MM = 0.5

WHY_A_FACE_IS_SELECTED = (
    "the two faces of a wall body are not interchangeable. One of them "
    "bounds this space and the other bounds whatever is on the far side "
    "of the wall. The one that bounds this space is the one on this "
    "space's side of the body, which the pairing establishes. Where no "
    "pair is established the drawn line is itself the face, and no "
    "thickness is attributed to it")

WHY_THE_WALK_STOPS = (
    "the material ends here and no classified gap carries the boundary "
    "across. The chain stops at the wall end. Nothing is bridged to reach "
    "material further away, because material further away bounds whatever "
    "space it stands in and not this one")

WHAT_A_DISCONNECTED_FRAGMENT_IS = (
    "drawn material that stands inside this region or against it but that "
    "the walk never reaches, because nothing connects it to the boundary. "
    "A free-standing pier and an island of joinery both look like this. "
    "It is reported where it is, and it is never used to close anything")

# What a step of the walk can be.
STEP_MATERIAL_FACE = "MATERIAL_WALL_FACE"
STEP_EXPOSED_COLUMN_FACE = "EXPOSED_COLUMN_FACE"
STEP_GLAZING = "GLAZING_BOUNDARY"
STEP_ACROSS_A_GAP = "ACROSS_A_CLASSIFIED_GAP"
STEP_STOPS = "BOUNDARY_RUNS_OUT_HERE"

# What a face's pairing is.
PAIRED = "TWO_FACES_PAIRED_AT_AN_INFERRED_WALL_THICKNESS"
UNPAIRED = "PAIRED_FACE_NOT_ESTABLISHED"

FACE_SELECTIONS = (
    "ROOM_SIDE_FACE_OF_A_PAIRED_WALL_BODY",
    "SINGLE_LINE_FACE_NO_PAIR_ESTABLISHED",
    "OPPOSITE_FACE_OF_A_PAIRED_WALL_BODY",
)


def model_hash() -> str:
    parts = [MODEL, str(NODE_SNAP_MM), str(PARALLEL_DEG),
             str(MIN_PAIR_OVERLAP_MM), str(THICKNESS_TOLERANCE_MM),
             str(MIN_PIECE_MM), STEP_SINGLE_LINE_END_TURN]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "NODE_SNAP_MM": NODE_SNAP_MM,
        "PARALLEL_DEG": PARALLEL_DEG,
        "MIN_PAIR_OVERLAP_MM": MIN_PAIR_OVERLAP_MM,
        "THICKNESS_TOLERANCE_MM": THICKNESS_TOLERANCE_MM,
        "MIN_PIECE_MM": MIN_PIECE_MM,
        "FACE_SELECTIONS": list(FACE_SELECTIONS),
        "why": {
            "a_face_is_selected": WHY_A_FACE_IS_SELECTED,
            "the_walk_stops": WHY_THE_WALK_STOPS,
            "a_single_line_end_turns": WHY_A_SINGLE_LINE_END_TURNS,
            "a_disconnected_fragment": WHAT_A_DISCONNECTED_FRAGMENT_IS,
        },
    }


# ------------------------------------------------------------------ pairing
def thickness_families(values, *, tolerance_mm=THICKNESS_TOLERANCE_MM):
    """The wall thicknesses this drawing actually uses, clustered."""
    vals = sorted(float(v) for v in values if v and float(v) > 0.0)
    fams, cur = [], []
    for v in vals:
        if cur and v - cur[0] > tolerance_mm:
            fams.append(cur)
            cur = []
        cur.append(v)
    if cur:
        fams.append(cur)
    return [{"nominal_mm": round(sum(f) / len(f), 1), "count": len(f),
             "min_mm": round(f[0], 1), "max_mm": round(f[-1], 1)}
            for f in fams]


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


def _project(p, o, u):
    return (p[0] - o[0]) * u[0] + (p[1] - o[1]) * u[1]


def _side(p, o, u):
    """Which side of the line through o along u the point p lies on."""
    return (p[0] - o[0]) * u[1] - (p[1] - o[1]) * u[0]


def pair_faces(faces, *, families=(), parallel_deg=PARALLEL_DEG,
               min_overlap_mm=MIN_PAIR_OVERLAP_MM,
               tolerance_mm=THICKNESS_TOLERANCE_MM):
    """Which drawn faces are the two faces of one wall body.

    `faces` are dicts with `a`, `b` (the ends of a straight run) and an
    `object_id`. A pair has to be parallel, has to overlap along its own
    direction, and its separation has to belong to a thickness family the
    drawing itself uses - a separation that matches nothing is not a wall
    body, it is two lines that happen to be parallel.
    """
    cos_lim = math.cos(math.radians(parallel_deg))
    noms = [f["nominal_mm"] for f in families]

    def in_a_family(d):
        for nom in noms:
            if abs(d - nom) <= tolerance_mm:
                return nom
        return None

    out = []
    for i, f in enumerate(faces):
        ui = _unit(f["a"], f["b"])
        for j in range(i + 1, len(faces)):
            g = faces[j]
            uj = _unit(g["a"], g["b"])
            if abs(ui[0] * uj[0] + ui[1] * uj[1]) < cos_lim:
                continue
            sep = abs(_side(g["a"], f["a"], ui))
            if abs(abs(_side(g["b"], f["a"], ui)) - sep) > tolerance_mm:
                continue
            nom = in_a_family(sep)
            if nom is None:
                continue
            lo_i = min(_project(f["a"], f["a"], ui),
                       _project(f["b"], f["a"], ui))
            hi_i = max(_project(f["a"], f["a"], ui),
                       _project(f["b"], f["a"], ui))
            lo_j = min(_project(g["a"], f["a"], ui),
                       _project(g["b"], f["a"], ui))
            hi_j = max(_project(g["a"], f["a"], ui),
                       _project(g["b"], f["a"], ui))
            overlap = min(hi_i, hi_j) - max(lo_i, lo_j)
            if overlap < min_overlap_mm:
                continue
            out.append({
                "face_a": f["object_id"], "face_b": g["object_id"],
                "i": i, "j": j,
                "thickness_mm": round(sep, 1),
                "matched_family_mm": nom,
                "overlap_mm": round(overlap, 1),
                "PAIRING": PAIRED,
                "why": ("two parallel faces separated by a distance that "
                        "belongs to a wall thickness family this drawing "
                        "uses, overlapping along their own direction"),
            })
    return out


def room_side_face(pair, faces, point):
    """Which face of a wall body bounds the space the point is in."""
    f, g = faces[pair["i"]], faces[pair["j"]]
    u = _unit(f["a"], f["b"])
    s_point = _side(point, f["a"], u)
    s_other = _side(g["a"], f["a"], u)
    if s_point == 0.0:
        return None, "THE_POINT_LIES_ON_THE_FACE_ITSELF"
    # the point is on this space's side of the body; the face that bounds
    # this space is the one the point is NOT separated from by the body
    if (s_point > 0.0) != (s_other > 0.0):
        return pair["i"], FACE_SELECTIONS[0]
    return pair["j"], FACE_SELECTIONS[0]


# ------------------------------------------------------------------- graph
def _nkey(p, snap=NODE_SNAP_MM):
    return (round(p[0] / snap), round(p[1] / snap))


def node_graph(pieces):
    """node -> the ends of the pieces that meet there."""
    nodes = {}
    for i, pc in enumerate(pieces):
        cs = pc["coords"]
        for end, p in ((0, cs[0]), (1, cs[-1])):
            nodes.setdefault(_nkey(p), []).append((i, end))
    return nodes


def _leaving(pieces, i, end):
    """The direction a piece leaves the node at `end`, and its far node."""
    cs = pieces[i]["coords"]
    if end == 0:
        return _unit(cs[0], cs[1]), cs[-1], 1
    return _unit(cs[-1], cs[-2]), cs[0], 0


def _next_at(pieces, nodes, at, back, *, exclude=None):
    """Keep the space on the left: take the first turn clockwise.

    Arriving at a node, the piece that continues the SAME side of the
    SAME space is the neighbour immediately clockwise from the way back.
    This is what makes a T-junction, a pier standing in the boundary, a
    corner, and the far side of an opening all come out right without a
    rule for each. `back` points back the way the walk arrived, whether
    it arrived along drawn material or across a classified gap.
    """
    here = [(i, e) for (i, e) in nodes.get(at, []) if i != exclude]
    if not here:
        return None
    a_back = math.atan2(back[1], back[0])
    best, best_turn = None, None
    for (i, e) in here:
        d, _far, _fe = _leaving(pieces, i, e)
        turn = (a_back - math.atan2(d[1], d[0])) % (2.0 * math.pi)
        if best_turn is None or turn < best_turn:
            best, best_turn = (i, e), turn
    return best


def _next_step(pieces, nodes, at, came_from):
    back, _far, _fe = _leaving(pieces, came_from[0], came_from[1])
    return _next_at(pieces, nodes, at, back, exclude=came_from[0])


def _face_each_other(a, b, *, junction_mm, cos_lim):
    """The pairing rule a gap has to satisfy to be a gap at all.

    A gap ALONG a wall has to continue both walls along their own lines.
    A gap at a corner is perpendicular by nature and is admitted on
    proximity. Two ends that satisfy neither are not facing each other.
    """
    pa, pb = a["point"], b["point"]
    gap = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
    if gap <= 0.0:
        return False, gap, None
    if gap <= junction_mm:
        return True, gap, "A_CORNER_GAP_ADMITTED_ON_PROXIMITY"
    ux, uy = (pb[0] - pa[0]) / gap, (pb[1] - pa[1]) / gap
    ha, hb = a["heading"], b["heading"]
    if (ha[0] * ux + ha[1] * uy >= cos_lim
            and hb[0] * -ux + hb[1] * -uy >= cos_lim):
        return True, gap, "BOTH_WALLS_RUN_TOWARD_EACH_OTHER_ALONG_THEIR_LINES"
    return False, gap, None


BOUNDARY_OPEN_AT_AN_UNCLASSIFIED_GAP = (
    "another wall end faces this one across a gap, and no classified gap "
    "carries the boundary over it. Two ends facing each other is what a "
    "doorway looks like and also what several other things look like, so "
    "it is not closed here on that shape alone. The boundary is open at "
    "this end, and the walk stops")


def facing_ends(pieces, nodes, *, junction_mm=None, collinear_deg=None):
    """Dangling ends that have another dangling end facing them.

    The test is the one a gap anywhere else in this system is proposed
    with: a gap along a wall has to continue BOTH walls along their own
    lines, and a gap at a corner is admitted on proximity. An end with
    something facing it is an end where the space carries on; an end with
    nothing facing it is material that simply stops.
    """
    from . import cad_geometry as cg
    if junction_mm is None:
        junction_mm = cg.JUNCTION_GAP_MM
    if collinear_deg is None:
        collinear_deg = cg.COLLINEAR_DEG
    cos_lim = math.cos(math.radians(collinear_deg))

    ends = []
    for key, here in nodes.items():
        if len(here) != 1:
            continue
        i, e = here[0]
        cs = pieces[i]["coords"]
        p = cs[0] if e == 0 else cs[-1]
        inward = cs[1] if e == 0 else cs[-2]
        ends.append({"key": key, "point": (p[0], p[1]),
                     "heading": _unit(inward, (p[0], p[1]))})

    out = {}
    for a in range(len(ends)):
        for b in range(a + 1, len(ends)):
            ok, _gap, why = _face_each_other(
                ends[a], ends[b], junction_mm=junction_mm, cos_lim=cos_lim)
            if not ok:
                continue
            out.setdefault(ends[a]["key"], []).append(ends[b]["point"])
            out.setdefault(ends[b]["key"], []).append(ends[a]["point"])
    return out


def walk(pieces, *, start, gaps_at=None, mates=None, facing=None,
         max_steps=4000):
    """Follow the boundary from one face until it closes or runs out.

    `start` is (piece_index, end) - the face the walk starts on and the
    end it leaves from, chosen so that the space is on the left.
    `gaps_at` maps a node to the classified gaps that begin there.
    """
    nodes = node_graph(pieces)
    gaps_at = gaps_at or {}
    mates = mates or {}
    facing = facing if facing is not None else facing_ends(pieces, nodes)

    steps, seen = [], set()
    cur = start
    closed = False
    for _ in range(max_steps):
        i, end = cur
        if (i, end) in seen:
            closed = True
            break
        seen.add((i, end))
        _d, far, far_end = _leaving(pieces, i, end)
        steps.append({"STEP": STEP_MATERIAL_FACE, "piece": i,
                      "entered_at_end": end})
        at = _nkey(far)
        nxt = _next_step(pieces, nodes, at, (i, far_end))
        if nxt is not None:
            cur = nxt
            continue
        g = gaps_at.get(at)
        if g:
            steps.append({"STEP": STEP_ACROSS_A_GAP, "gap": g["GAP_ID"],
                          "GAP_CLASS": g["GAP_CLASS"],
                          "start_mm": list(g["start_mm"]),
                          "end_mm": list(g["end_mm"])})
            near = tuple(g["start_mm"])
            far_end = tuple(g["end_mm"])
            if _nkey(near) != at:
                near, far_end = far_end, near
            # crossing an opening carries the boundary to the wall end
            # facing it. It does not step INTO the space beyond: the same
            # turn rule applies at the far end, with the way back being
            # the way across.
            back = _unit(far_end, near)
            nxt = _next_at(pieces, nodes, _nkey(far_end), back)
            if nxt is not None:
                cur = nxt
                continue
        if at in facing:
            steps.append({"STEP": STEP_STOPS, "at_mm": [far[0], far[1]],
                          "why": BOUNDARY_OPEN_AT_AN_UNCLASSIFIED_GAP,
                          "an_end_faces_this_one_across_a_gap":
                              [list(p) for p in facing[at][:4]]})
            break
        ret = _wall_end_return(pieces, nodes, mates, i, far)
        if ret is not None:
            steps.append({"STEP": STEP_WALL_END_RETURN,
                          "why": WHY_A_WALL_END_RETURNS, **ret})
            cur = (ret["mate_piece"], ret["mate_end"])
            continue
        if not mates.get(i):
            # one drawn line, no thickness established: both of its sides
            # face this space, so the boundary turns back along it
            steps.append({"STEP": STEP_SINGLE_LINE_END_TURN,
                          "at_mm": [far[0], far[1]], "length_mm": 0.0,
                          "why": WHY_A_SINGLE_LINE_END_TURNS})
            cur = (i, far_end)
            continue
        steps.append({"STEP": STEP_STOPS, "at_mm": [far[0], far[1]],
                      "why": WHY_THE_WALK_STOPS,
                      "the_mate_face_carries_on_here": True})
        break
    return {"MODEL": MODEL, "steps": steps,
            "CLOSED_BY_DRAWN_MATERIAL": closed,
            "pieces_walked": len({s["piece"] for s in steps
                                  if s["STEP"] == STEP_MATERIAL_FACE})}


# ------------------------------------------------------------------ pieces
def pieces_from(segments, *, tol_mm, owner_tol_mm=2.0):
    """Node drawn material into pieces, each carrying its source entity.

    A piece is a stretch of one drawn entity between two junctions. The
    walk steps from piece to piece, so a pier that interrupts a wall face
    and a T-junction both appear as what they are - a node with more than
    two ways on - instead of having to be special-cased.
    """
    from shapely.geometry import LineString, Point
    from shapely.ops import unary_union
    from shapely.strtree import STRtree

    lines, srcs = [], []
    for s in segments:
        pts = list(s.get("points") or ())
        if len(pts) < 2:
            continue
        lines.append(LineString(pts))
        srcs.append(s)
    if not lines:
        return []
    tree = STRtree(lines)
    noded = unary_union(lines)
    parts = list(getattr(noded, "geoms", [])) or [noded]

    out = []
    for part in parts:
        cs = []
        for c in part.coords:
            if not cs or math.hypot(c[0] - cs[-1][0],
                                    c[1] - cs[-1][1]) > MIN_PIECE_MM:
                cs.append((c[0], c[1]))
        # A piece with no length has no direction, and a step onto one
        # would make the turn at the next node meaningless.
        if len(cs) < 2 or part.length <= MIN_PIECE_MM:
            continue
        mid = part.interpolate(0.5, normalized=True)
        best, best_d = None, None
        for idx in tree.query(Point(mid).buffer(owner_tol_mm)):
            d = lines[int(idx)].distance(mid)
            if best_d is None or d < best_d:
                best, best_d = int(idx), d
        src = srcs[best] if best is not None and best_d is not None \
            and best_d <= owner_tol_mm else {}
        out.append({"coords": cs, "length_mm": part.length,
                    "object_id": src.get("object_id"),
                    "boundary_role": src.get("boundary_role"),
                    "layer": src.get("layer")})
    return out


def straight_runs(pieces):
    """Each piece reduced to the straight run between its ends, for pairing."""
    return [{"a": tuple(p["coords"][0]), "b": tuple(p["coords"][-1]),
             "object_id": p.get("object_id"), "piece": i}
            for i, p in enumerate(pieces)]


def first_material_met(seed, pieces, *, tol_mm=1.0):
    """The piece the point meets first, and where - not merely the nearest.

    Nearness is not a bounding relation. This takes the piece whose
    closest point the seed can actually reach without crossing anything
    else: the material that stands between this point and that direction,
    which is what bounding means.
    """
    from shapely.geometry import LineString, Point
    from shapely.strtree import STRtree

    geos = [LineString(p["coords"]) for p in pieces]
    if not geos:
        return None
    tree = STRtree(geos)
    sp = Point(seed)
    order = sorted(range(len(geos)), key=lambda i: geos[i].distance(sp))
    for i in order:
        foot = geos[i].interpolate(geos[i].project(sp))
        if foot.distance(sp) <= tol_mm:
            continue
        sight = LineString([seed, (foot.x, foot.y)])
        blocked = False
        for idx in tree.query(sight):
            j = int(idx)
            if j == i:
                continue
            hit = sight.intersection(geos[j])
            if hit.is_empty:
                continue
            if hit.distance(foot) > tol_mm:
                blocked = True
                break
        if not blocked:
            return {"piece": i, "at_mm": (foot.x, foot.y),
                    "distance_mm": foot.distance(sp)}
    return None


def leave_with_the_space_on_the_left(pieces, i, seed):
    """Which end to leave a face from, so the space stays on one side.

    _side returns the cross product (p - o) x u, which is NEGATIVE for a
    point to the LEFT of travel along u. Leaving from the far end instead
    reverses u, so exactly one of the two ends puts the space on the left.
    """
    cs = pieces[i]["coords"]
    u = _unit(cs[0], cs[-1])
    return 0 if _side(seed, cs[0], u) < 0.0 else 1


def walk_both_ways(pieces, *, start, gaps_at=None, mates=None,
                   facing=None, max_steps=4000):
    """A boundary that does not close still has two directions to follow.

    Walking one way and stopping reports half of what the drawing
    establishes. The chain is the run found going one way, joined to the
    run found going the other, with the face the walk started on in the
    middle exactly once.
    """
    i, end = start
    fwd = walk(pieces, start=(i, end), gaps_at=gaps_at, mates=mates,
               facing=facing, max_steps=max_steps)
    if fwd["CLOSED_BY_DRAWN_MATERIAL"]:
        fwd["DIRECTIONS_WALKED"] = 1
        return fwd
    back = walk(pieces, start=(i, 1 - end), gaps_at=gaps_at,
                mates=mates, facing=facing, max_steps=max_steps)
    tail = [s for s in back["steps"]
            if not (s["STEP"] == STEP_MATERIAL_FACE and s["piece"] == i)]
    steps = list(reversed(tail)) + fwd["steps"]
    return {"MODEL": MODEL, "steps": steps,
            "CLOSED_BY_DRAWN_MATERIAL": False,
            "DIRECTIONS_WALKED": 2,
            "pieces_walked": len({s["piece"] for s in steps
                                  if s["STEP"] == STEP_MATERIAL_FACE}),
            "why_two_directions": (
                "the boundary does not close, so it was followed both ways "
                "from the face the point first meets. It stops where the "
                "drawing stops, at each end")}


STEP_WALL_END_RETURN = "WALL_END_RETURN"
STEP_SINGLE_LINE_END_TURN = "SINGLE_LINE_WALL_END_TURN"

WHY_A_SINGLE_LINE_END_TURNS = (
    "this piece of material is drawn as one line and no mate establishes "
    "a thickness for it. Both of its sides face the same space, so the "
    "boundary runs up one side of it and back down the other, and the "
    "turn at its end crosses nothing. No thickness is attributed to it "
    "and no length is added for the turn")

WHY_A_WALL_END_RETURNS = (
    "a wall drawn as two faces has an end, and at that end the boundary "
    "turns across the wall's own thickness from one face to the other. "
    "That stretch is material - it is the end of the wall - and its "
    "length is the thickness the pairing establishes, not a number chosen "
    "to make anything meet. The turn is taken only where BOTH faces of "
    "the body stop at the same station, because a face that stops while "
    "its mate carries on is an interruption in that face, not the end of "
    "the wall")


def mate_map(pieces, *, families, parallel_deg=PARALLEL_DEG,
             min_overlap_mm=MIN_PAIR_OVERLAP_MM,
             tolerance_mm=THICKNESS_TOLERANCE_MM):
    """piece -> the pieces that are the other face of the same wall body."""
    runs = straight_runs(pieces)
    pairs = pair_faces(runs, families=families, parallel_deg=parallel_deg,
                       min_overlap_mm=min_overlap_mm,
                       tolerance_mm=tolerance_mm)
    out = {}
    for p in pairs:
        out.setdefault(p["i"], []).append(
            {"mate": p["j"], "thickness_mm": p["thickness_mm"],
             "matched_family_mm": p["matched_family_mm"]})
        out.setdefault(p["j"], []).append(
            {"mate": p["i"], "thickness_mm": p["thickness_mm"],
             "matched_family_mm": p["matched_family_mm"]})
    return out, pairs


def _wall_end_return(pieces, nodes, mates, i, at_xy, *,
                     tolerance_mm=THICKNESS_TOLERANCE_MM,
                     perpendicular_deg=PARALLEL_DEG):
    """The turn across a wall's thickness at the end of the wall body."""
    cs = pieces[i]["coords"]
    u = _unit(cs[0], cs[-1])
    cos_lim = math.cos(math.radians(90.0 - perpendicular_deg))
    for m in mates.get(i, ()):
        j = m["mate"]
        mc = pieces[j]["coords"]
        for end, p in ((0, mc[0]), (1, mc[-1])):
            if len(nodes.get(_nkey(p), [])) != 1:
                continue                      # the mate carries on here
            d = math.hypot(p[0] - at_xy[0], p[1] - at_xy[1])
            if abs(d - m["thickness_mm"]) > tolerance_mm:
                continue
            w = _unit(at_xy, p)
            if abs(u[0] * w[0] + u[1] * w[1]) > cos_lim:
                continue                      # not across the thickness
            return {"mate_piece": j, "mate_end": end,
                    "length_mm": round(d, 3),
                    "thickness_mm": m["thickness_mm"],
                    "matched_family_mm": m["matched_family_mm"],
                    "at_mm": [at_xy[0], at_xy[1]],
                    "to_mm": [p[0], p[1]]}
    return None


# --------------------------------------------------------------- assembly
RUN_CLOSED_AROUND_THE_POINT = "CLOSED_AROUND_THE_POINT"
RUN_CLOSED_NOT_AROUND_THE_POINT = "CLOSED_BUT_NOT_AROUND_THE_POINT"
RUN_OPEN = "OPEN_RUN_THAT_STOPS_WHERE_THE_DRAWING_STOPS"

WHY_A_CLOSED_RING_IS_CHECKED = (
    "a walk can close around something the point is OUTSIDE of - a pier, "
    "a block of joinery, a shaft. That ring is a real boundary of a real "
    "thing, and it is not this point's boundary. A closed run is this "
    "point's boundary only if the point is inside it; otherwise it is "
    "reported as what it is, an island standing in the region")

WHY_EVERY_VISIBLE_RUN_IS_TAKEN = (
    "where nothing encloses the point there is no single ring to choose, "
    "and choosing one would be arbitrary. Every run of boundary the point "
    "can see is walked, and all of them are reported. Runs reached from "
    "two different faces of the same run come out identical and are "
    "recorded once")


def visible_pieces(seed, pieces, *, rays=720, reach_mm=30000.0):
    """The pieces that are the first material met, looking out from a point."""
    from shapely.geometry import LineString
    from shapely.strtree import STRtree

    geos = [LineString(p["coords"]) for p in pieces]
    if not geos:
        return []
    tree = STRtree(geos)
    seen = {}
    for k in range(rays):
        a = 2.0 * math.pi * k / rays
        far = (seed[0] + reach_mm * math.cos(a),
               seed[1] + reach_mm * math.sin(a))
        ray = LineString([seed, far])
        best, best_d = None, None
        for idx in tree.query(ray):
            j = int(idx)
            hit = ray.intersection(geos[j])
            if hit.is_empty:
                continue
            pts = ([hit] if hit.geom_type == "Point"
                   else list(getattr(hit, "geoms", [])) or [])
            for q in pts:
                if q.geom_type != "Point":
                    continue
                d = math.hypot(q.x - seed[0], q.y - seed[1])
                if d <= 1e-6:
                    continue
                if best_d is None or d < best_d:
                    best, best_d = j, d
        if best is not None and best not in seen:
            seen[best] = best_d
    return sorted(seen, key=lambda j: seen[j])


def boundary_of_point(seed, pieces, *, gaps_at=None, mates=None,
                      rays=720, reach_mm=30000.0, max_steps=4000):
    """Every run of boundary this point can see, walked and classified."""
    from shapely.geometry import Point, Polygon

    starts = visible_pieces(seed, pieces, rays=rays, reach_mm=reach_mm)
    runs, seen_keys = [], set()
    for i in starts:
        end = leave_with_the_space_on_the_left(pieces, i, seed)
        r = walk(pieces, start=(i, end), gaps_at=gaps_at, mates=mates,
                 max_steps=max_steps)
        if not r["CLOSED_BY_DRAWN_MATERIAL"]:
            r = walk_both_ways(pieces, start=(i, end), gaps_at=gaps_at,
                               mates=mates, max_steps=max_steps)
        key = tuple(sorted((s["piece"], s["entered_at_end"])
                           for s in r["steps"]
                           if s["STEP"] == STEP_MATERIAL_FACE))
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        ring = []
        for s in r["steps"]:
            if s["STEP"] == STEP_MATERIAL_FACE:
                cs = pieces[s["piece"]]["coords"]
                ring.extend(cs if s["entered_at_end"] == 0
                            else list(reversed(cs)))
        kind = RUN_OPEN
        if r["CLOSED_BY_DRAWN_MATERIAL"] and len(ring) >= 4:
            try:
                poly = Polygon(ring)
                if poly.is_valid and poly.contains(Point(seed)):
                    kind = RUN_CLOSED_AROUND_THE_POINT
                else:
                    kind = RUN_CLOSED_NOT_AROUND_THE_POINT
            except Exception:
                kind = RUN_CLOSED_NOT_AROUND_THE_POINT
        r["RUN_KIND"] = kind
        r["started_on_piece"] = i
        runs.append(r)

    holding = [r for r in runs if r["RUN_KIND"] == RUN_CLOSED_AROUND_THE_POINT]
    islands = [r for r in runs
               if r["RUN_KIND"] == RUN_CLOSED_NOT_AROUND_THE_POINT]
    open_runs = [r for r in runs if r["RUN_KIND"] == RUN_OPEN]
    return {
        "MODEL": MODEL,
        "CLOSED_BY_DRAWN_MATERIAL": bool(holding),
        "runs_that_close_around_the_point": holding,
        "islands_standing_in_the_region": islands,
        "open_runs": open_runs,
        "faces_the_point_can_see": len(starts),
        "why": {
            "a_closed_ring_is_checked": WHY_A_CLOSED_RING_IS_CHECKED,
            "every_visible_run_is_taken": WHY_EVERY_VISIBLE_RUN_IS_TAKEN,
            "a_disconnected_fragment": WHAT_A_DISCONNECTED_FRAGMENT_IS,
        },
    }


ENCLOSED = "ENCLOSED_BY_DRAWN_MATERIAL"
NOT_ESTABLISHED = "BOUNDARY_NOT_ESTABLISHED_BY_THE_DRAWING"

WHY_THE_INNERMOST_RING = (
    "where more than one walked ring encloses the point, they are nested: "
    "an outer ring encloses other spaces as well as this one. The ring "
    "that bounds THIS space is the innermost one. This is the containment "
    "hierarchy, not a preference for a smaller area - no ring is chosen "
    "because of what it measures")

WHY_NOTHING_IS_PROPOSED = (
    "no walked ring encloses this point, so the drawing does not "
    "establish a boundary for it. What the walk did establish is kept and "
    "reported - the runs of real material, where they stop, and what "
    "stands near each stop - and no extent is proposed. A boundary that "
    "is not established is withheld, not approximated")


def face_selection_audit(pieces, steps, mates, seed):
    """For each face walked, whether it is the room-side face of its body."""
    runs = straight_runs(pieces)
    out = []
    for s in steps:
        if s["STEP"] != STEP_MATERIAL_FACE:
            continue
        i = s["piece"]
        ms = mates.get(i, ())
        if not ms:
            out.append({"piece": i, "object_id": pieces[i].get("object_id"),
                        "PAIRING": UNPAIRED,
                        "FACE_SELECTION": FACE_SELECTIONS[1],
                        "why": WHY_A_FACE_IS_SELECTED})
            continue
        m = ms[0]
        j = m["mate"]
        pair = {"i": i, "j": j}
        pick, how = room_side_face(pair, runs, seed)
        out.append({
            "piece": i, "object_id": pieces[i].get("object_id"),
            "mate_object_id": pieces[j].get("object_id"),
            "PAIRING": PAIRED,
            "thickness_mm": m["thickness_mm"],
            "matched_family_mm": m["matched_family_mm"],
            "FACE_SELECTION": (FACE_SELECTIONS[0] if pick == i
                               else FACE_SELECTIONS[2]),
            "THE_WALK_IS_ON_THE_ROOM_SIDE_FACE": pick == i,
            "how": how,
            "why": WHY_A_FACE_IS_SELECTED,
        })
    return out


def boundary_at(seed, pieces, *, gaps_at=None, mates=None, facing=None,
                rays=720, reach_mm=30000.0, max_steps=4000):
    """The corrected mechanism: one answer for one point, or none.

    Every face the point can see is a place the walk can start. A start
    whose walk closes AROUND THE POINT has found this space's boundary;
    where several do, they are nested and the innermost is this space's.
    Where none does, the drawing does not establish a boundary here, and
    nothing is proposed.
    """
    from shapely.geometry import Point, Polygon

    starts = visible_pieces(seed, pieces, rays=rays, reach_mm=reach_mm)
    if facing is None:
        facing = facing_ends(pieces, node_graph(pieces))
    sp = Point(seed)
    rings, islands, tried = [], [], set()
    for i in starts:
        end = leave_with_the_space_on_the_left(pieces, i, seed)
        r = walk(pieces, start=(i, end), gaps_at=gaps_at, mates=mates,
                 facing=facing, max_steps=max_steps)
        key = tuple(sorted((s["piece"], s["entered_at_end"])
                           for s in r["steps"]
                           if s["STEP"] == STEP_MATERIAL_FACE))
        if not key or key in tried:
            continue
        tried.add(key)
        if not r["CLOSED_BY_DRAWN_MATERIAL"]:
            continue
        ring = []
        for s in r["steps"]:
            if s["STEP"] == STEP_MATERIAL_FACE:
                cs = pieces[s["piece"]]["coords"]
                ring.extend(cs if s["entered_at_end"] == 0
                            else list(reversed(cs)))
        if len(ring) < 4:
            continue
        try:
            poly = Polygon(ring)
        except Exception:
            continue
        if not poly.is_valid:
            poly = poly.buffer(0)
        r["started_on_piece"] = i
        r["ring_area_mm2"] = poly.area
        if poly.contains(sp):
            rings.append((poly.area, r))
        else:
            islands.append(r)

    if rings:
        rings.sort(key=lambda t: t[0])
        chosen = rings[0][1]
        chosen["BOUNDARY_BASIS"] = ENCLOSED
        chosen["RING_ENCLOSES_THE_POINT"] = True
        chosen["rings_enclosing_the_point"] = len(rings)
        chosen["why_this_ring"] = WHY_THE_INNERMOST_RING
        chosen["FACE_SELECTION"] = face_selection_audit(
            pieces, chosen["steps"], mates or {}, seed)
        chosen["islands_standing_in_the_region"] = [
            {"pieces": [s["piece"] for s in r["steps"]
                        if s["STEP"] == STEP_MATERIAL_FACE],
             "why": WHAT_A_DISCONNECTED_FRAGMENT_IS} for r in islands]
        chosen["faces_the_point_can_see"] = len(starts)
        return chosen

    established = None
    if starts:
        i = starts[0]
        end = leave_with_the_space_on_the_left(pieces, i, seed)
        established = walk_both_ways(pieces, start=(i, end),
                                     gaps_at=gaps_at, mates=mates,
                                     facing=facing, max_steps=max_steps)
        established["started_on_piece"] = i
        established["FACE_SELECTION"] = face_selection_audit(
            pieces, established["steps"], mates or {}, seed)
    return {
        "MODEL": MODEL,
        "BOUNDARY_BASIS": NOT_ESTABLISHED,
        "CLOSED_BY_DRAWN_MATERIAL": False,
        "RING_ENCLOSES_THE_POINT": False,
        "steps": [] if established is None else established["steps"],
        "FACE_SELECTION": [] if established is None
        else established["FACE_SELECTION"],
        "started_on_piece": None if established is None
        else established["started_on_piece"],
        "rings_that_close_but_not_around_the_point": len(islands),
        "faces_the_point_can_see": len(starts),
        "why": WHY_NOTHING_IS_PROPOSED,
        "THIS_IS_NOT_A_PROPOSED_BOUNDARY": (
            "the steps recorded here are what the walk established before "
            "it ran out. They are a diagnostic of where the drawing stops "
            "carrying the boundary. They are not offered as this region's "
            "boundary and no area follows from them"),
    }


TWO_SEEDS_IN_ONE_ENCLOSURE = (
    "a straight sight line from one label's point to another's crosses no "
    "drawn material. Nothing is built between them, so they stand in one "
    "enclosure however differently they are named. This is a fact about "
    "the drawing and about where the labels sit; it is not a decision to "
    "merge them, and two names on one floor do not make a boundary")


def sight_line_is_clear(a, b, pieces, *, tol_mm=1.0):
    """Does the straight line from a to b cross any drawn material?"""
    from shapely.geometry import LineString
    from shapely.strtree import STRtree

    geos = [LineString(p["coords"]) for p in pieces]
    if not geos:
        return True, None
    tree = STRtree(geos)
    span = LineString([a, b])
    for idx in tree.query(span):
        j = int(idx)
        if span.intersects(geos[j]):
            hit = span.intersection(geos[j])
            if not hit.is_empty:
                return False, pieces[j].get("object_id")
    return True, None
