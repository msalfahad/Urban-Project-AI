"""Continuous wall-band topology (PA07B / PA07C).

Every accepted material band is a one-dimensional host: its axis parameter t is developed distance (mm) for straight
and curved bands alike.  The band is cut into longitudinal intervals from the coverage of its two faces:

    MATERIAL    both faces present
    OPENING     both faces interrupted and the interruption is an established / probable opening site
    JUNCTION    a crossing band passes here, or one face only is interrupted where another band meets this one
    UNRESOLVED  anything else: a single-face gap with no crossing band, a both-face gap without enough evidence

A site belongs to its host band (HOST_BAND_ID) and is classified from geometric evidence only: jamb returns across
the thickness at both ends, a leaf, a swing arc, frame lines, glazing.  A single-face gap is never a doorway.  Two
interrupted faces without jambs, leaf, swing or frame stay UNRESOLVED; nothing is merged silently.

Seals: the topology layer receives, for every band, its face lines over MATERIAL intervals, a chord across the full
thickness at every interval boundary and at both band ends, and the two face chords of every non-material interval.
Wall interiors therefore never connect to rooms (FM-P6-02) and curved bands host sites like straight ones (FM-P6-03).
Chords carry MATERIAL = False: they close topology, they never add material.
"""

from __future__ import annotations

import math
from collections import defaultdict

from engine.ingest import ids
from engine.ingest import material_bands as MB

INTERVAL_CLASSES = ("MATERIAL", "OPENING", "JUNCTION", "UNRESOLVED")
SITE_CLASSES = ("CONFIRMED_DOOR_OPENING", "PROBABLE_DOOR_OPENING", "CONFIRMED_WINDOW_OPENING", "CONFIRMED_GLAZED_OPENING", "CONFIRMED_OPEN_PASSAGE",
                "MATERIAL_CONTINUITY", "CAD_JUNCTION", "UNRESOLVED")
CAD_GAP_MM = 120.0            # faces that simply fail to meet
CONTINUITY_MAX_MM = 500.0     # a both-face break narrower than this without jambs is a drafting break, not a passage
UNEVIDENCED_BREAK_MM = 250.0  # PA07R2 (FM-R1-11): a both-face break wider than this with nothing drawn in it is a hatch, duct or niche question, not continuity
DOOR_SPAN = (600.0, 2500.0)
PROBABLE_DOOR_SPAN = (600.0, 1400.0)
SWING_RADIUS_TOL = 0.15
LEAF_LENGTH_TOL = (0.6, 1.25)
FRAME_MIN_SHARE = 0.7
RETURN_TOL = MB.JUNCTION_TOL
GLAZING_ROLES = ("GLAZING", "WINDOW_FRAME")


# ------------------------------------------------------------------ geometry on the band
def _tangent(b, t):
    if b["KIND"] == "S":
        return b["U"]
    th = b["THETA0"] + t / b["R_AXIS"]
    return (-math.sin(th), math.cos(th))


def _side_cover(b, side):
    ivs = [v[1] for v in b[side].values()]
    return MB._union([(max(lo, b["EXTENT"][0]), min(hi, b["EXTENT"][1])) for lo, hi in ivs if min(hi, b["EXTENT"][1]) > max(lo, b["EXTENT"][0])])


def _present(cover, t0, t1):
    """Is [t0, t1] (mostly) inside the covered intervals?"""
    mid = (t0 + t1) / 2
    return any(lo - 1e-6 <= mid <= hi + 1e-6 for lo, hi in cover)


def _returns_at(b, t, segs):
    """Segments across the thickness (perpendicular to the band, spanning it) whose midpoint sits at parameter t."""
    thk = b["THK"]; ux, uy = _tangent(b, t)
    out = []
    for q in segs:
        if q.kind != "SEGMENT" or q.object_id in b["FACES"]:
            continue
        L = MB._len(q)
        if not (0.6 * thk <= L <= 1.4 * thk + 30):
            continue
        mx, my = (q.x1 + q.x2) / 2, (q.y1 + q.y2) / 2
        tq, d = MB.band_param(b, mx, my)
        if abs(tq - t) > RETURN_TOL or abs(d) > thk / 2 + RETURN_TOL:
            continue
        qx, qy = (q.x2 - q.x1) / L, (q.y2 - q.y1) / L
        if abs(qx * ux + qy * uy) > math.sin(5 * MB.ANGLE_TOL):
            continue
        out.append(q.object_id)
    return out


def _swings(b, t0, t1, prims, roles):
    """Arcs whose centre sits on a jamb point (either face, either end) with radius ~ span."""
    span = t1 - t0
    out = []
    for q in prims:
        if q.kind != "ARC":
            continue
        if not (span * (1 - SWING_RADIUS_TOL) <= q.radius <= span * (1 + SWING_RADIUS_TOL)):
            continue
        tq, d = MB.band_param(b, q.cx, q.cy)
        if min(abs(tq - t0), abs(tq - t1)) <= RETURN_TOL and abs(d) <= b["THK"] / 2 + RETURN_TOL:
            out.append({"OBJECT_ID": q.object_id, "RADIUS_MM": round(q.radius, 1), "ROLE": roles.get(q.object_id, {}).get("ROLE")})
    return out


def _leaves(b, t0, t1, prims, roles):
    """Straight segments of about the span length starting at a jamb point and leaving the band (a door leaf)."""
    span = t1 - t0
    out = []
    for q in prims:
        if q.kind != "SEGMENT" or q.object_id in b["FACES"]:
            continue
        L = MB._len(q)
        if not (LEAF_LENGTH_TOL[0] * span <= L <= LEAF_LENGTH_TOL[1] * span):
            continue
        for (x, y), (ox, oy) in (((q.x1, q.y1), (q.x2, q.y2)), ((q.x2, q.y2), (q.x1, q.y1))):
            tq, d = MB.band_param(b, x, y)
            if min(abs(tq - t0), abs(tq - t1)) <= RETURN_TOL and abs(d) <= b["THK"] / 2 + RETURN_TOL:
                to, do = MB.band_param(b, ox, oy)
                if abs(do) > b["THK"] / 2 + 50 or (t0 - RETURN_TOL <= to <= t1 + RETURN_TOL and abs(do) > b["THK"] / 2 - 5):
                    out.append({"OBJECT_ID": q.object_id, "LENGTH_MM": round(L, 1), "ROLE": roles.get(q.object_id, {}).get("ROLE")})
                    break
    return out


def _frame_lines(b, t0, t1, prims, roles):
    """Segments along the band inside the gap strip spanning most of it (window / glazing frame)."""
    span = t1 - t0
    lines = []
    for q in prims:
        if q.object_id in b["FACES"] or q.kind not in ("SEGMENT", "ARC"):
            continue
        if q.kind == "ARC":
            if b["KIND"] != "C" or math.hypot(q.cx - b["CENTRE"][0], q.cy - b["CENTRE"][1]) > MB.AXIS_MERGE_MM:
                continue
            pa, pb = (q.cx + q.radius * math.cos(q.start_angle), q.cy + q.radius * math.sin(q.start_angle)), (q.cx + q.radius * math.cos(q.end_angle), q.cy + q.radius * math.sin(q.end_angle))
        else:
            pa, pb = (q.x1, q.y1), (q.x2, q.y2)
        ta, da = MB.band_param(b, *pa); tb, db = MB.band_param(b, *pb)
        if abs(da) > b["THK"] / 2 + 10 or abs(db) > b["THK"] / 2 + 10:
            continue
        lo, hi = min(ta, tb), max(ta, tb)
        ov = min(hi, t1) - max(lo, t0)
        if ov >= FRAME_MIN_SHARE * span and abs(da - db) <= 10:
            lines.append({"OBJECT_ID": q.object_id, "OFFSET_MM": round((da + db) / 2, 1), "ROLE": roles.get(q.object_id, {}).get("ROLE")})
    return lines


def _crossing(b, t0, t1, accepted):
    """An accepted band passing through the host over the gap, or ending on the host inside it (a wall meeting here)."""
    # PA07R1: a crossing band must contain the middle of the gap, not only its ends (two partitions across a corridor)
    mid = MB.band_point(b, (t0 + t1) / 2)
    for h in accepted:
        if h is b:
            continue
        if MB.in_strip(h, mid[0], mid[1], tol=10.0):
            return h
        for x, y in MB._ends(h):
            t, d = MB.band_param(b, x, y)
            if t0 - RETURN_TOL <= t <= t1 + RETURN_TOL and abs(d) <= b["THK"] / 2 + RETURN_TOL:
                return h
    return None


def _side_free(b, t, side_sign, accepted):
    """What lies just beyond face `side_sign` at parameter t: MATERIAL (another accepted band) or FREE."""
    x, y = MB.band_point(b, t, side_sign * (b["THK"] / 2 + 150))
    for h in accepted:
        if h is b:
            continue
        if MB.in_strip(h, x, y, tol=0.0):
            return "MATERIAL"
    return "FREE"


def _cut(b):
    """Breakpoints from both faces' coverage -> [(t0, t1, A_present, B_present)]."""
    ca, cb = _side_cover(b, "SIDE_A"), _side_cover(b, "SIDE_B")
    pts = {b["EXTENT"][0], b["EXTENT"][1]}
    for lo, hi in ca + cb:
        pts.update((lo, hi))
    pts = sorted(p for p in pts if b["EXTENT"][0] - 1e-6 <= p <= b["EXTENT"][1] + 1e-6)
    out = []
    for t0, t1 in zip(pts, pts[1:]):
        if t1 - t0 < 1e-6:
            continue
        out.append([t0, t1, _present(ca, t0, t1), _present(cb, t0, t1)])
    # merge neighbours with the same presence pattern
    merged = []
    for iv in out:
        if merged and merged[-1][2:] == iv[2:] and abs(merged[-1][1] - iv[0]) < 1e-6:
            merged[-1][1] = iv[1]
        else:
            merged.append(iv)
    return merged


# ------------------------------------------------------------------ classification
def classify_gap(b, t0, t1, prims, roles, accepted, segs, all_bands=()):
    """Evidence and class for a both-face interruption [t0, t1] of band b."""
    span = t1 - t0
    mid = MB.band_point(b, (t0 + t1) / 2)
    unresolved_here = [h["BAND_ID"] for h in all_bands if h is not b and h["STATUS"] != "ACCEPTED" and MB.in_strip(h, mid[0], mid[1], tol=10.0)]
    jamb_a, jamb_b = _returns_at(b, t0, segs), _returns_at(b, t1, segs)
    crossing = _crossing(b, t0, t1, accepted)
    swings = _swings(b, t0, t1, prims, roles)
    leaves = _leaves(b, t0, t1, prims, roles)
    frames = _frame_lines(b, t0, t1, prims, roles)
    glazing = [f for f in frames if f["ROLE"] in GLAZING_ROLES]
    free_a, free_b = _side_free(b, (t0 + t1) / 2, -1, accepted), _side_free(b, (t0 + t1) / 2, +1, accepted)
    ev = {"HOST_BAND_ID": b["BAND_ID"], "AXIAL_START": round(t0, 1), "AXIAL_END": round(t1, 1), "SPAN_MM": round(span, 1),
          "FACE_A_INTERRUPTED": True, "FACE_B_INTERRUPTED": True, "CROSSES_FULL_BAND": True,
          "JAMB_A": jamb_a, "JAMB_B": jamb_b, "LEAF_EVIDENCE": leaves, "SWING_EVIDENCE": swings,
          "FRAME_EVIDENCE": [f for f in frames if f["ROLE"] not in GLAZING_ROLES], "GLAZING_EVIDENCE": glazing,
          "FREE_SPACE_SIDE_A": free_a, "FREE_SPACE_SIDE_B": free_b, "CROSSING_BAND_ID": crossing["BAND_ID"] if crossing else None}
    jambs = bool(jamb_a and jamb_b)
    if crossing:
        cls, status, why = "CAD_JUNCTION", "ESTABLISHED", "an accepted band passes through / meets the host over this interval"
    elif span < CAD_GAP_MM and not jambs:
        cls, status, why = "CAD_JUNCTION", "ESTABLISHED", f"faces fail to meet by {round(span)} mm (< {CAD_GAP_MM:.0f}); drafting gap"
    elif span < CONTINUITY_MAX_MM and not jambs and not (swings or leaves or frames) and unresolved_here:
        cls, status, why = "UNRESOLVED", "BREAK_WITH_UNRESOLVED_ELEMENT", f"both faces break for {round(span)} mm where an unresolved candidate {unresolved_here[:2]} crosses the gap"
    elif span < UNEVIDENCED_BREAK_MM and not jambs and not (swings or leaves or frames):
        cls, status, why = "MATERIAL_CONTINUITY", "ESTABLISHED", f"both faces break for {round(span)} mm with no jamb, leaf, swing or frame and no candidate crossing the gap: face-line break inside one wall"
    elif span < CONTINUITY_MAX_MM and not jambs and not (swings or leaves or frames):
        cls, status, why = "UNRESOLVED", "UNEVIDENCED_BREAK", f"PA07R2: both faces break for {round(span)} mm with nothing drawn in the gap: serving hatch, duct, niche or a drafting break cannot be told apart; zero material, provisional"
    elif swings and len([f for f in frames if f["ROLE"] not in GLAZING_ROLES]) >= 2:
        cls, status, why = "UNRESOLVED", "DOOR_OR_WINDOW_CONFLICT", "PA07R2 (FM-R1-09): a swing arc together with >= 2 frame lines inside the gap: casement window, French window or a door with a threshold; the type decides height and deduction, so it is not established"
    elif swings and (jambs or leaves) and DOOR_SPAN[0] <= span <= DOOR_SPAN[1]:
        cls, status, why = "CONFIRMED_DOOR_OPENING", "ESTABLISHED", "swing arc at a jamb with radius ~ span, plus jamb returns or a leaf"
    elif jambs and leaves and DOOR_SPAN[0] <= span <= DOOR_SPAN[1]:
        cls, status, why = "CONFIRMED_DOOR_OPENING", "ESTABLISHED", "jamb returns at both ends and a leaf of the span length; no swing drawn"
    elif (swings or leaves) and DOOR_SPAN[0] <= span <= DOOR_SPAN[1]:
        cls, status, why = "PROBABLE_DOOR_OPENING", "PROVISIONAL", "swing or leaf evidence without jamb returns"
    elif jambs and len(frames) >= 2 and any(f["ROLE"] in GLAZING_ROLES for f in frames):
        cls, status, why = "CONFIRMED_WINDOW_OPENING", "ESTABLISHED", "jamb returns, >= 2 frame lines and a glazing / window-frame role among them"
    elif jambs and len(frames) >= 2:
        cls, status, why = "CONFIRMED_WINDOW_OPENING", "PROVISIONAL", "jamb returns and >= 2 frame lines from line count only (sliding door, threshold or window): span established, type provisional"
    elif jambs and glazing:
        cls, status, why = "CONFIRMED_GLAZED_OPENING", "ESTABLISHED", "jamb returns and a glazing line along the opening"
    elif jambs and PROBABLE_DOOR_SPAN[0] <= span <= PROBABLE_DOOR_SPAN[1]:
        cls, status, why = "PROBABLE_DOOR_OPENING", "PROVISIONAL", "jamb returns across the full band at a door-like span; leaf and swing missing"
    elif jambs and span > PROBABLE_DOOR_SPAN[1]:
        cls, status, why = "UNRESOLVED", "OPEN_PASSAGE_CANDIDATE", "jamb returns at a span wider than a door; becomes CONFIRMED_OPEN_PASSAGE only when both sides are interior spaces"
    else:
        cls, status, why = "UNRESOLVED", "INSUFFICIENT_EVIDENCE", "both faces interrupted without jambs, leaf, swing or frame; not merged, not counted"
    ev.update({"CLASS": cls, "STATUS": status, "REASON": why})
    return ev


def build_view(view_id, prims, roles, bands, source_id=None):
    """Intervals, opening sites and seals for the accepted bands of one view.

    `bands` = the working band dicts from material_bands.build (all statuses); only ACCEPTED non-column bands host intervals."""
    accepted = [b for b in bands if b["STATUS"] == "ACCEPTED"]
    hosts = [b for b in accepted if b.get("BAND_TYPE") != "COLUMN_BAND"]
    segs = [p for p in prims if p.kind == "SEGMENT"]
    intervals, sites, seals = [], [], []
    for b in hosts:
        cuts = _cut(b)
        ends = {"START": _end_state(b, b["EXTENT"][0], accepted, segs), "END": _end_state(b, b["EXTENT"][1], accepted, segs)}
        for k, (t0, t1, a_here, b_here) in enumerate(cuts):
            iid = ids.make_id("OPENING_SITE", "INT7", b["BAND_ID"], round(t0), round(t1), tol=10.0).replace("OS-", "BI-")
            row = {"INTERVAL_ID": iid, "HOST_BAND_ID": b["BAND_ID"], "VIEW_ID": view_id, "SOURCE_ID": source_id, "AXIAL_START": round(t0, 1), "AXIAL_END": round(t1, 1), "SPAN_MM": round(t1 - t0, 1),
                   "FACE_A_PRESENT": a_here, "FACE_B_PRESENT": b_here, "CLASS": None, "SITE_ID": None, "NOTE": None}
            if a_here and b_here:
                row["CLASS"] = "MATERIAL"
            elif not a_here and not b_here:
                ev = classify_gap(b, t0, t1, prims, roles, accepted, segs, all_bands=bands)
                sid = ids.make_id("OPENING_SITE", "SITE7", b["BAND_ID"], round(t0), round(t1), tol=10.0)
                ev.update({"SITE_ID": sid, "VIEW_ID": view_id, "SOURCE": {"SOURCE_ID": source_id, "HOST_FACES": sorted(b["FACES"]), "RULE": "band_topology.classify_gap"}})
                sites.append(ev)
                row["SITE_ID"] = sid
                row["CLASS"] = {"CONFIRMED_DOOR_OPENING": "OPENING", "PROBABLE_DOOR_OPENING": "OPENING", "CONFIRMED_WINDOW_OPENING": "OPENING", "CONFIRMED_GLAZED_OPENING": "OPENING",
                                "MATERIAL_CONTINUITY": "MATERIAL", "CAD_JUNCTION": "JUNCTION", "UNRESOLVED": "UNRESOLVED"}[ev["CLASS"]]
                row["NOTE"] = ev["CLASS"]
            else:
                crossing = _crossing(b, t0, t1, accepted)
                side = "A" if not a_here else "B"
                if crossing:
                    row["CLASS"], row["NOTE"] = "JUNCTION", f"face {side} interrupted where band {crossing['BAND_ID']} meets the host"
                else:
                    row["CLASS"], row["NOTE"] = "UNRESOLVED", f"single-face gap on face {side} with no band meeting here: never a doorway; niche, recess or drafting omission"
                    sid = ids.make_id("OPENING_SITE", "SITE7", b["BAND_ID"], round(t0), round(t1), tol=10.0)
                    sites.append({"SITE_ID": sid, "HOST_BAND_ID": b["BAND_ID"], "VIEW_ID": view_id, "AXIAL_START": round(t0, 1), "AXIAL_END": round(t1, 1), "SPAN_MM": round(t1 - t0, 1),
                                  "FACE_A_INTERRUPTED": not a_here, "FACE_B_INTERRUPTED": not b_here, "CROSSES_FULL_BAND": False, "JAMB_A": [], "JAMB_B": [], "LEAF_EVIDENCE": [], "SWING_EVIDENCE": [],
                                  "FRAME_EVIDENCE": [], "GLAZING_EVIDENCE": [], "FREE_SPACE_SIDE_A": None, "FREE_SPACE_SIDE_B": None, "CROSSING_BAND_ID": None,
                                  "CLASS": "UNRESOLVED", "STATUS": "SINGLE_FACE_GAP", "REASON": "one face interrupted only; a doorway interrupts both faces",
                                  "SOURCE": {"SOURCE_ID": source_id, "HOST_FACES": sorted(b["FACES"]), "RULE": "band_topology.build_view single-face rule"}})
                    row["SITE_ID"] = sid
            intervals.append(row)
        intervals[-1]["END_STATE"] = ends["END"]; intervals[-len(cuts)]["START_STATE"] = ends["START"]
        seals.extend(_seals(b, cuts, intervals[-len(cuts):]))
    for b in accepted:
        if b.get("BAND_TYPE") == "COLUMN_BAND":
            seals.extend(_column_seals(b))
    seals.extend(unresolved_seals(bands, prims, roles))
    return intervals, sites, seals


def _end_state(b, t, accepted, segs):
    x, y = MB.band_point(b, t)
    joined = [h["BAND_ID"] for h in accepted if h is not b and MB.in_strip(h, x, y)]
    capped = _returns_at(b, t, segs)
    if joined:
        return {"STATE": "JOINED", "BANDS": joined}
    if capped:
        return {"STATE": "CAPPED", "RETURNS": capped}
    return {"STATE": "FREE_END", "NOTE": "true wall termination or missing return; the topology closes it with a zero-material chord"}


def _poly(b, t0, t1, side, n=None):
    """Polyline along the band between t0 and t1 at offset side (mm); straight bands give 2 points, arcs are sampled."""
    if b["KIND"] == "S":
        return [MB.band_point(b, t0, side), MB.band_point(b, t1, side)]
    n = n or max(2, int((t1 - t0) / 50) + 1)
    return [MB.band_point(b, t0 + (t1 - t0) * i / n, side) for i in range(n + 1)]


def _seals(b, cuts, rows):
    """Barrier geometry for the topology layer: face lines over MATERIAL, chords elsewhere.  Chords carry no material."""
    out = []
    h = b["THK"] / 2
    for (t0, t1, a_here, b_here), row in zip(cuts, rows):
        if row["CLASS"] == "MATERIAL":
            out.append({"KIND": "FACE", "SIDE": "A", "BAND_ID": b["BAND_ID"], "INTERVAL_ID": row["INTERVAL_ID"], "MATERIAL": True, "PTS": _poly(b, t0, t1, -h)})
            out.append({"KIND": "FACE", "SIDE": "B", "BAND_ID": b["BAND_ID"], "INTERVAL_ID": row["INTERVAL_ID"], "MATERIAL": True, "PTS": _poly(b, t0, t1, +h)})
        else:
            tag = {"OPENING": "OPENING_CHORD", "JUNCTION": "JUNCTION_CHORD", "UNRESOLVED": "UNRESOLVED_CHORD"}[row["CLASS"]]
            # PA07R1: a face that is present stays a material FACE; only the interrupted side is chorded
            for side, sign, here in (("A", -1, a_here), ("B", +1, b_here)):
                if here:
                    out.append({"KIND": "FACE", "SIDE": side, "BAND_ID": b["BAND_ID"], "INTERVAL_ID": row["INTERVAL_ID"], "MATERIAL": True, "PTS": _poly(b, t0, t1, sign * h)})
                else:
                    out.append({"KIND": tag, "SIDE": side, "BAND_ID": b["BAND_ID"], "INTERVAL_ID": row["INTERVAL_ID"], "SITE_ID": row["SITE_ID"], "MATERIAL": False, "PTS": _poly(b, t0, t1, sign * h)})
        # chords across the thickness at both ends of every interval (wall interiors never connect to rooms)
        for t in (t0, t1):
            out.append({"KIND": "THICKNESS_CHORD", "BAND_ID": b["BAND_ID"], "INTERVAL_ID": row["INTERVAL_ID"], "MATERIAL": False, "PTS": [MB.band_point(b, t, -h), MB.band_point(b, t, +h)]})
    # PA07R1: at both band ends, zero-material stubs along both faces beyond the extent close the junction-tolerance gap (<= 80 mm) in the raster
    for t, sign in ((b["EXTENT"][0], -1), (b["EXTENT"][1], +1)):
        for side in (-h, +h):
            out.append({"KIND": "JUNCTION_CHORD", "SIDE": "END", "BAND_ID": b["BAND_ID"], "INTERVAL_ID": None, "SITE_ID": None, "MATERIAL": False, "PTS": [MB.band_point(b, t, side), MB.band_point(b, t + sign * (MB.JUNCTION_TOL + 20.0), side)]})
    return out


def unresolved_seals(bands, prims, roles):
    """PA07R1 (FM-P7-03): the faces of every UNRESOLVED candidate, of thin rejected pairs and of long unpaired candidate
    lines are zero-material UNRESOLVED_CHORD seals: rooms never merge silently across a wall the engine could not
    establish; the space beside them becomes BOUNDARY_PROVISIONAL and the SPACE_STATUS gate blocks it."""
    out = []
    used = set()
    for b in bands:
        used.update(b["FACES"])
        if b["STATUS"] == "ACCEPTED":
            continue
        reason = (b["REASON"] or "").split(" (")[0]
        if b["STATUS"] == "REJECTED" and reason not in ("THIN_PAIR_BELOW_WALL_MINIMUM", "CLOSED_FITTING_LOOP"):
            continue
        if b["LENGTH"] < MB.MIN_FREE_BAND_MM and not b.get("JOINS_ALL"):
            continue          # a short isolated candidate (annotation box, symbol) separates nothing that matters
        for f in b["FACES"].values():
            out.append({"KIND": "UNRESOLVED_CHORD", "SIDE": None, "BAND_ID": b["BAND_ID"], "INTERVAL_ID": None, "SITE_ID": None, "MATERIAL": False, "PTS": _prim_pts(f), "NOTE": f"face of {b['STATUS']} candidate: {reason}"})
    accepted = [b for b in bands if b["STATUS"] == "ACCEPTED"]
    for p in MB.candidates(prims, roles):
        if p.object_id in used or p.kind not in ("SEGMENT", "ARC"):
            continue
        if p.kind == "SEGMENT":
            if MB._len(p) < MB.MIN_FREE_BAND_MM:
                continue
            ends = ((p.x1, p.y1), (p.x2, p.y2))
        else:
            # PA07R2 (FM-R1-01): an unpaired arc of wall length (a curved face whose mate was not found) separates provisionally too
            sw = ((p.end_angle - p.start_angle) % (2 * math.pi)) or 2 * math.pi
            if p.radius * sw < MB.MIN_FREE_BAND_MM:
                continue
            ends = ((p.cx + p.radius * math.cos(p.start_angle), p.cy + p.radius * math.sin(p.start_angle)), (p.cx + p.radius * math.cos(p.end_angle), p.cy + p.radius * math.sin(p.end_angle)))
        # an unpaired line that runs wall to wall (both ends inside accepted band strips) may be a single-line partition or a glazing line: it separates, provisionally
        ends_in = [any(MB.in_strip(h, x, y, tol=MB.JUNCTION_TOL) for h in accepted) for x, y in ends]
        if all(ends_in):
            out.append({"KIND": "UNRESOLVED_CHORD", "SIDE": None, "BAND_ID": None, "INTERVAL_ID": None, "SITE_ID": None, "MATERIAL": False, "PTS": _prim_pts(p), "OBJECT_ID": p.object_id, "NOTE": "unpaired wall-to-wall line: single-line partition, glazing or overhead element; provisional separator"})
    return out


def _prim_pts(p):
    if p.kind == "SEGMENT":
        return [(p.x1, p.y1), (p.x2, p.y2)]
    sw = ((p.end_angle - p.start_angle) % (2 * math.pi)) or 2 * math.pi
    n = max(2, int(p.radius * sw / 50) + 1)
    return [(p.cx + p.radius * math.cos(p.start_angle + sw * k / n), p.cy + p.radius * math.sin(p.start_angle + sw * k / n)) for k in range(n + 1)]


def _column_seals(b):
    h = b["THK"] / 2
    t0, t1 = b["EXTENT"]
    return [{"KIND": "COLUMN_FACE", "SIDE": s, "BAND_ID": b["BAND_ID"], "INTERVAL_ID": None, "MATERIAL": True, "PTS": pts}
            for s, pts in (("A", _poly(b, t0, t1, -h)), ("B", _poly(b, t0, t1, +h)), ("START", [MB.band_point(b, t0, -h), MB.band_point(b, t0, +h)]), ("END", [MB.band_point(b, t1, -h), MB.band_point(b, t1, +h)]))]


def promote_open_passages(sites, side_class_of_site):
    """CONFIRMED_OPEN_PASSAGE only once the space layer says both sides are interior spaces."""
    for s in sites:
        if s["CLASS"] == "UNRESOLVED" and s["STATUS"] == "OPEN_PASSAGE_CANDIDATE":
            a, b = side_class_of_site(s)
            if a == "INTERIOR" and b == "INTERIOR":
                s["CLASS"], s["STATUS"], s["REASON"] = "CONFIRMED_OPEN_PASSAGE", "ESTABLISHED", s["REASON"] + "; both sides are interior spaces"
    return sites


def summarise(intervals, sites):
    out = {"INTERVALS": defaultdict(int), "MATERIAL_MM": 0.0, "OPENING_MM": 0.0, "JUNCTION_MM": 0.0, "UNRESOLVED_MM": 0.0, "SITES": defaultdict(int), "SITE_STATUS": defaultdict(int)}
    for r in intervals:
        out["INTERVALS"][r["CLASS"]] += 1
        out[r["CLASS"] + "_MM"] = round(out[r["CLASS"] + "_MM"] + r["SPAN_MM"], 1)
    for s in sites:
        out["SITES"][s["CLASS"]] += 1
        out["SITE_STATUS"][s["STATUS"]] += 1
    out["INTERVALS"] = dict(out["INTERVALS"]); out["SITES"] = dict(out["SITES"]); out["SITE_STATUS"] = dict(out["SITE_STATUS"])
    return out
