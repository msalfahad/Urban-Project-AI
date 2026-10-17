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
END_GAP_MAX_MM = DOOR_SPAN[1]          # PA07R3 (PA08-R1, FC-2): a band end is probed this far along its axis for the wall it stops short of
END_GAP_STEP_MM = 25.0
HINGE_SHARE = 0.2                      # PA07R3 (FC-8): a leaf hinge may sit inside the gap by up to this share of the span (the frame width)
OUTLINE_SHORT_SIDE_MAX_MM = 2.5 * MB.THICKNESS[1]   # PA07R3 (FC-4): a closed outline of unpaired material lines up to this depth (niche, duct, pier, tub, counter) separates provisionally


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


def _leaves(b, t0, t1, prims, roles, exclude=frozenset()):
    """Straight segments of about the span length starting at a jamb point and leaving the band (a door leaf), or two
    half-span leaves hung on opposite jambs (PA07R3 §4: a double-leaf door).
    `exclude`: faces of accepted bands and closed-outline members (PA07R3): a wall face or an outline edge is never a leaf."""
    span = t1 - t0
    out, halves = [], []
    hinge_tol = max(RETURN_TOL, HINGE_SHARE * span)      # PA07R3 (FC-8): a leaf hung on a frame starts up to a frame width inside the gap
    for q in prims:
        if q.kind != "SEGMENT" or q.object_id in b["FACES"] or q.object_id in exclude:
            continue
        L = MB._len(q)
        full = LEAF_LENGTH_TOL[0] * span <= L <= LEAF_LENGTH_TOL[1] * span
        half = LEAF_LENGTH_TOL[0] * span / 2 <= L <= LEAF_LENGTH_TOL[1] * span / 2
        if not (full or half):
            continue
        for (x, y), (ox, oy) in (((q.x1, q.y1), (q.x2, q.y2)), ((q.x2, q.y2), (q.x1, q.y1))):
            tq, d = MB.band_param(b, x, y)
            near0, near1 = abs(tq - t0) <= hinge_tol, abs(tq - t1) <= hinge_tol
            if (near0 or near1) and t0 - RETURN_TOL <= tq <= t1 + RETURN_TOL and abs(d) <= b["THK"] / 2 + RETURN_TOL:
                to, do = MB.band_param(b, ox, oy)
                if abs(do) > b["THK"] / 2 + 50 or (t0 - RETURN_TOL <= to <= t1 + RETURN_TOL and abs(do) > b["THK"] / 2 - 5):
                    row = {"OBJECT_ID": q.object_id, "LENGTH_MM": round(L, 1), "ROLE": roles.get(q.object_id, {}).get("ROLE")}
                    if full:
                        out.append(row)
                    else:
                        halves.append((0 if near0 else 1, row))
                    break
    ends = {k for k, _ in halves}
    if not out and ends == {0, 1}:
        out = [dict(r, DOUBLE_LEAF=True) for _, r in halves]
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
def classify_gap(b, t0, t1, prims, roles, accepted, segs, all_bands=(), not_leaves=None):
    """Evidence and class for a both-face interruption [t0, t1] of band b."""
    span = t1 - t0
    mid = MB.band_point(b, (t0 + t1) / 2)
    unresolved_here = [h["BAND_ID"] for h in all_bands if h is not b and h["STATUS"] != "ACCEPTED" and MB.in_strip(h, mid[0], mid[1], tol=10.0)]
    jamb_a, jamb_b = _returns_at(b, t0, segs), _returns_at(b, t1, segs)
    crossing = _crossing(b, t0, t1, accepted)
    swings = _swings(b, t0, t1, prims, roles)
    leaves = _leaves(b, t0, t1, prims, roles, exclude=not_leaves if not_leaves is not None else {f for h in accepted for f in h["FACES"]})
    frames = _frame_lines(b, t0, t1, prims, roles)
    glazing = [f for f in frames if f["ROLE"] in GLAZING_ROLES]
    free_a, free_b = _side_free(b, (t0 + t1) / 2, -1, accepted), _side_free(b, (t0 + t1) / 2, +1, accepted)
    ev = {"HOST_BAND_ID": b["BAND_ID"], "AXIAL_START": round(t0, 1), "AXIAL_END": round(t1, 1), "SPAN_MM": round(span, 1),
          "FACE_A_INTERRUPTED": True, "FACE_B_INTERRUPTED": True, "CROSSES_FULL_BAND": True,
          "JAMB_A": jamb_a, "JAMB_B": jamb_b, "LEAF_EVIDENCE": leaves, "SWING_EVIDENCE": swings,
          "FRAME_EVIDENCE": [f for f in frames if f["ROLE"] not in GLAZING_ROLES], "GLAZING_EVIDENCE": glazing,
          "FREE_SPACE_SIDE_A": free_a, "FREE_SPACE_SIDE_B": free_b, "CROSSING_BAND_ID": crossing["BAND_ID"] if crossing else None}
    jambs = bool(jamb_a and jamb_b)
    end_gap = not (b["EXTENT"][0] - 1e-6 <= (t0 + t1) / 2 <= b["EXTENT"][1] + 1e-6)
    if end_gap and crossing is not None and not MB.in_strip(crossing, mid[0], mid[1], tol=10.0):
        crossing = None          # PA07R3 (FC-2): the wall an end gap runs up to is its far jamb, not a wall crossing the gap
    ev_end = {"END_GAP": end_gap}
    if crossing and span > crossing["THK"] + 2 * CAD_GAP_MM and not (jambs or swings or leaves or frames):
        # PA07R3 (PA08-R1): a gap far wider than the crossing wall is not a junction; it holds the junction AND something else (doors, an opening, a recess)
        cls, status, why = "UNRESOLVED", "GAP_WIDER_THAN_CROSSING_WALL", f"an accepted band meets the host inside this {round(span)} mm gap but is only {round(crossing['THK'])} mm thick; the rest of the gap is undecided"
    elif crossing:
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
    if end_gap and cls == "CAD_JUNCTION" and span >= CAD_GAP_MM:
        cls, status, why = "UNRESOLVED", "END_GAP_UNEVIDENCED", f"PA07R3: the band ends {round(span)} mm short of an accepted wall with nothing drawn in the gap; a doorless opening, a recess or a drafting omission cannot be told apart; zero material, provisional"
    ev.update(ev_end); ev.update({"CLASS": cls, "STATUS": status, "REASON": why})
    return ev


def build_view(view_id, prims, roles, bands, source_id=None):
    """Intervals, opening sites and seals for the accepted bands of one view.

    `bands` = the working band dicts from material_bands.build (all statuses); only ACCEPTED non-column bands host intervals."""
    accepted = [b for b in bands if b["STATUS"] == "ACCEPTED"]
    hosts = [b for b in accepted if b.get("BAND_TYPE") != "COLUMN_BAND"]
    segs = [p for p in prims if p.kind == "SEGMENT"]
    intervals, sites, seals = [], [], []
    end_gaps = _end_gaps(hosts, accepted, segs)
    not_leaves = {f for h in accepted for f in h["FACES"]}      # a face of an established wall is never a door leaf
    for b in hosts:
        cuts = _cut(b)
        ends = {"START": _end_state(b, b["EXTENT"][0], accepted, segs), "END": _end_state(b, b["EXTENT"][1], accepted, segs)}
        # PA07R3 (FC-2): an end that is not joined but stops short of an accepted wall hosts an END GAP interval, classified like any gap
        for end in ("START", "END"):
            eg = end_gaps.get((b["BAND_ID"], end))
            if eg is None:
                continue
            ends[end] = dict(ends[end], **eg)
            if eg["STATE"] != "END_GAP":
                continue
            span = eg["SPAN_MM"]
            if end == "START":
                cuts.insert(0, [b["EXTENT"][0] - span, b["EXTENT"][0], False, False])
            else:
                cuts.append([b["EXTENT"][1], b["EXTENT"][1] + span, False, False])
        for k, (t0, t1, a_here, b_here) in enumerate(cuts):
            iid = ids.make_id("OPENING_SITE", "INT7", b["BAND_ID"], round(t0), round(t1), tol=10.0).replace("OS-", "BI-")
            row = {"INTERVAL_ID": iid, "HOST_BAND_ID": b["BAND_ID"], "VIEW_ID": view_id, "SOURCE_ID": source_id, "AXIAL_START": round(t0, 1), "AXIAL_END": round(t1, 1), "SPAN_MM": round(t1 - t0, 1),
                   "FACE_A_PRESENT": a_here, "FACE_B_PRESENT": b_here, "CLASS": None, "SITE_ID": None, "NOTE": None}
            if a_here and b_here:
                row["CLASS"] = "MATERIAL"
            elif not a_here and not b_here:
                ev = classify_gap(b, t0, t1, prims, roles, accepted, segs, all_bands=bands, not_leaves=not_leaves)
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
    # PA07R3 (PA08-R1): opening evidence wins over outline detection.  A door leaf, swing, frame or jamb read at a classified site is
    # that opening's evidence; a closed loop through those same lines (a double leaf plus its two jambs) is not an outline.
    opening_evidence = {z["OBJECT_ID"] for s_ in sites for k in ("LEAF_EVIDENCE", "SWING_EVIDENCE", "FRAME_EVIDENCE", "GLAZING_EVIDENCE") for z in s_[k]}
    opening_evidence |= {i for s_ in sites for i in s_["JAMB_A"] + s_["JAMB_B"]}
    seals.extend(unresolved_seals(bands, prims, roles, opening_evidence))
    return intervals, sites, seals


def _end_state(b, t, accepted, segs):
    x, y = MB.band_point(b, t)
    # PA07R3: the same along-axis tolerance as material_bands._joins (a wall drawn to the inner corner still joins the wall it meets)
    joined = [h["BAND_ID"] for h in accepted if h is not b and MB.in_strip(h, x, y, along_tol=MB.JUNCTION_TOL + b["THK"] / 2)]
    capped = _returns_at(b, t, segs)
    if joined:
        return {"STATE": "JOINED", "BANDS": joined}
    if capped:
        return {"STATE": "CAPPED", "RETURNS": capped}
    return {"STATE": "FREE_END", "NOTE": "true wall termination or missing return; the topology closes it with a zero-material chord"}


def _end_gap(b, end, accepted):
    """PA07R3 (PA08-R1, FC-2): the wall a band end stops short of.  The band axis is probed beyond the end up to END_GAP_MAX_MM;
    the first accepted band strip met (a perpendicular wall, or a wall the band runs into) bounds an END GAP: the corner door,
    the doorless opening or the drafting gap between this wall's end and that wall.  Returns (span_mm, band) or None."""
    t_end = b["EXTENT"][0 if end == "START" else 1]
    sign = -1.0 if end == "START" else 1.0
    s = END_GAP_STEP_MM
    while s <= END_GAP_MAX_MM:
        x, y = MB.band_point(b, t_end + sign * s)
        for h in accepted:
            if h is b or h.get("BAND_TYPE") == "COLUMN_BAND":
                continue
            # met from the side (a perpendicular wall crossing the axis) or at its end (a wall that stops at the far jamb of the gap)
            if MB.in_strip(h, x, y, tol=0.0, along_tol=MB.JUNCTION_TOL):
                return s, h
        s += END_GAP_STEP_MM
    return None


def _end_gaps(hosts, accepted, segs):
    """PA07R3 (FC-2): every host band end that is not joined and stops short of an accepted wall -> {(band_id, end): state}.

    JUNCTION           gap <= CAD_GAP_MM + JUNCTION_TOL: faces fail to meet by a drafting tolerance (no site; the end stubs close it)
    END_GAP_ALONG_WALL an accepted band lies directly beside the gap on either side: the band runs along / into a wall, not between rooms (no site)
    END_GAP_SHARED     two bands face each other across the same gap (a door between two wall runs of different thickness): one hosts the site
    END_GAP            classified as an interval of this band (corner door, doorless opening, unevidenced end gap)"""
    raw = {}
    for b in hosts:
        for end in ("START", "END"):
            t = b["EXTENT"][0 if end == "START" else 1]
            x, y = MB.band_point(b, t)
            if any(h is not b and MB.in_strip(h, x, y, along_tol=MB.JUNCTION_TOL + b["THK"] / 2) for h in accepted):
                continue
            eg = _end_gap(b, end, accepted)
            if eg is None:
                continue
            span, h = eg
            sign = -1.0 if end == "START" else 1.0
            tm = t + sign * span / 2
            if span <= CAD_GAP_MM + MB.JUNCTION_TOL:
                raw[(b["BAND_ID"], end)] = {"STATE": "JUNCTION", "SPAN_MM": round(span, 1), "TO_BAND": h["BAND_ID"], "NOTE": "faces fail to meet the next wall by a drafting tolerance"}
            elif _side_free(b, tm, -1, accepted) == "MATERIAL" or _side_free(b, tm, +1, accepted) == "MATERIAL":
                raw[(b["BAND_ID"], end)] = {"STATE": "END_GAP_ALONG_WALL", "SPAN_MM": round(span, 1), "TO_BAND": h["BAND_ID"], "NOTE": "an accepted wall lies beside the gap: the band runs along or into a wall here, no room-to-room opening"}
            else:
                raw[(b["BAND_ID"], end)] = {"STATE": "END_GAP", "SPAN_MM": round(span, 1), "TO_BAND": h["BAND_ID"], "_HOST": b, "_T": t, "_SIGN": sign,
                                            "NOTE": "the band stops short of an accepted wall; the gap between is classified as an interval of this band (corner door, doorless opening or drafting gap)"}
    # two bands facing each other across one gap: the longer one hosts the site
    keys = [k for k, v in raw.items() if v["STATE"] == "END_GAP"]
    for i, k1 in enumerate(keys):
        for k2 in keys[i + 1:]:
            v1, v2 = raw[k1], raw[k2]
            if v1["STATE"] != "END_GAP" or v2["STATE"] != "END_GAP":
                continue
            b1, b2 = v1["_HOST"], v2["_HOST"]
            if v1["TO_BAND"] != b2["BAND_ID"] or v2["TO_BAND"] != b1["BAND_ID"]:
                continue
            _, d = MB.band_param(b1, *MB.band_point(b2, v2["_T"]))
            if abs(d) > (b1["THK"] + b2["THK"]) / 2:
                continue
            loser = k2 if (b1["LENGTH"], b1["KEY"]) >= (b2["LENGTH"], b2["KEY"]) else k1
            raw[loser] = {"STATE": "END_GAP_SHARED", "SPAN_MM": raw[loser]["SPAN_MM"], "TO_BAND": raw[loser]["TO_BAND"], "SITE_HOST": (b1 if loser is k2 else b2)["BAND_ID"], "NOTE": "the same gap is hosted by the band facing this one; one site, not two"}
    for v in raw.values():
        v.pop("_HOST", None); v.pop("_T", None); v.pop("_SIGN", None)
    return raw


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


def unresolved_seals(bands, prims, roles, opening_evidence=frozenset()):
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
        if b["STATUS"] == "UNRESOLVED":
            # PA07R3 (PA08-R1): the gaps of an unresolved candidate (its door and window positions) separate provisionally too: both sides are
            # chorded over the full extent, so rooms never merge through the doorway of a wall the engine could not establish
            h = b["THK"] / 2
            lo, hi = b["EXTENT"]
            acc_now = [z for z in bands if z["STATUS"] == "ACCEPTED"]
            # a strip with an accepted wall directly beyond one of its faces is a lining, counter or wardrobe drawn against that wall: its
            # interior is room floor under joinery and stays connected to the room (PA07R1 FM-01).  A strip free on both sides is a
            # partition candidate: its interior is capped and its end gaps are chorded (PA07R3 FC-2 / FC-3)
            free_both_sides = _strip_free_both_sides(b, acc_now)
            if free_both_sides:
                for end in ("START", "END"):
                    eg = _end_gap(b, end, acc_now)
                    if eg is not None and eg[0] >= END_GAP_STEP_MM:
                        if end == "START":
                            lo -= eg[0]
                        else:
                            hi += eg[0]
            for side in (-h, +h):
                out.append({"KIND": "UNRESOLVED_CHORD", "SIDE": None, "BAND_ID": b["BAND_ID"], "INTERVAL_ID": None, "SITE_ID": None, "MATERIAL": False, "PTS": _poly(b, lo, hi, side),
                            "NOTE": f"full extent of {b['STATUS']} candidate (gaps{' and end gaps' if free_both_sides else ''} included): {reason}"})
            if free_both_sides:
                for t in (lo, hi):
                    out.append({"KIND": "UNRESOLVED_CHORD", "SIDE": "END", "BAND_ID": b["BAND_ID"], "INTERVAL_ID": None, "SITE_ID": None, "MATERIAL": False, "PTS": [MB.band_point(b, t, -h), MB.band_point(b, t, +h)],
                                "NOTE": f"end cap of {b['STATUS']} candidate strip (free space on both sides: never a corridor between rooms): {reason}"})
    accepted = [b for b in bands if b["STATUS"] == "ACCEPTED"]
    out.extend(closed_outline_seals(bands, prims, roles, accepted, used, opening_evidence))     # PA07R3 (FC-4)
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


def _strip_free_both_sides(b, accepted, probe_mm=30.0):
    """Neither side of the strip, just beyond its faces at the strip's middle, lies inside an accepted band."""
    mid = (b["EXTENT"][0] + b["EXTENT"][1]) / 2
    for sign in (-1.0, 1.0):
        x, y = MB.band_point(b, mid, sign * (b["THK"] / 2 + probe_mm))
        if any(MB.in_strip(h, x, y, tol=0.0) for h in accepted if h is not b):
            return False
    return True


def closed_outline_seals(bands, prims, roles, accepted, used, opening_evidence=frozenset()):
    """PA07R3 (PA08-R1, FC-4): a closed outline of material candidate lines that no accepted band uses, whose short side is at most
    OUTLINE_SHORT_SIDE_MAX_MM and that touches accepted wall strips at two or more of its vertices, is a niche, duct, pier, tub or
    counter drawn on a material layer.  It is not a wall (no candidate pair at its depth) but it is not floor either: every edge is an
    UNRESOLVED_CHORD, so the rooms on its two sides never merge through it and its interior becomes a provisional enclosed face."""
    acc_faces = {f for b in accepted for f in b["FACES"]}
    segs = [p for p in MB.candidates(prims, roles) if p.kind == "SEGMENT" and p.object_id not in acc_faces and p.object_id not in opening_evidence
            and not p.provenance.block_path and MB._len(p) >= MB.WALL_MIN_MM]
    key = lambda x, y: (round(x / 10), round(y / 10))
    by_pt = defaultdict(list)
    for q in segs:
        by_pt[key(q.x1, q.y1)].append(q); by_pt[key(q.x2, q.y2)].append(q)
    out, seen = [], set()
    for start in segs:
        if start.object_id in seen:
            continue
        # walk the endpoint graph from start; a closed simple loop of 4..8 edges with axis-aligned turns is an outline
        loop = _walk_loop(start, by_pt, key)
        if not loop:
            continue
        ids_ = tuple(sorted(q.object_id for q in loop))
        if ids_ in seen:
            continue
        seen.update(ids_)
        xs = [v for q in loop for v in (q.x1, q.x2)]; ys = [v for q in loop for v in (q.y1, q.y2)]
        w, hgt = max(xs) - min(xs), max(ys) - min(ys)
        short = min(w, hgt)
        if short > OUTLINE_SHORT_SIDE_MAX_MM or short < MB.WALL_MIN_MM:
            continue
        verts = {key(q.x1, q.y1) for q in loop} | {key(q.x2, q.y2) for q in loop} | {key((q.x1 + q.x2) / 2, (q.y1 + q.y2) / 2) for q in loop}   # vertices and edge midpoints (an edge crossing a wall's gap)
        touching = sum(1 for vx, vy in verts if any(MB.in_strip(h, vx * 10.0, vy * 10.0, tol=MB.JUNCTION_TOL) for h in accepted))
        # a wall that ends on the outline (the outline completes the wall line) touches it as well
        for h in accepted:
            for ex, ey in MB._ends(h):
                if any(_point_seg_dist(ex, ey, q) <= MB.JUNCTION_TOL + h["THK"] / 2 for q in loop):
                    touching += 1
                    break
        if touching < 2:
            continue
        # an outline with a wall directly beyond one of its long sides is joinery against that wall (wardrobe, counter): floor continues under it
        long_edges = sorted(loop, key=MB._len)[-2:]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        against_wall = False
        for q in long_edges:
            mx, my = (q.x1 + q.x2) / 2, (q.y1 + q.y2) / 2
            L = MB._len(q); nx, ny = -(q.y2 - q.y1) / L, (q.x2 - q.x1) / L
            if (mx - cx) * nx + (my - cy) * ny < 0:
                nx, ny = -nx, -ny          # outward
            px, py = mx + nx * 30.0, my + ny * 30.0
            if any(MB.in_strip(h, px, py, tol=0.0) for h in accepted):
                against_wall = True
        if against_wall:
            continue
        for q in loop:
            out.append({"KIND": "UNRESOLVED_CHORD", "SIDE": None, "BAND_ID": None, "INTERVAL_ID": None, "SITE_ID": None, "MATERIAL": False, "PTS": _prim_pts(q), "OBJECT_ID": q.object_id,
                        "OUTLINE": list(ids_), "OUTLINE_SIZE_MM": [round(w), round(hgt)], "NOTE": "closed outline of unpaired material lines joined to walls: niche, duct, pier, tub or counter; provisional separator, not floor, not wall"})
    return out


def _point_seg_dist(x, y, q):
    dx, dy = q.x2 - q.x1, q.y2 - q.y1
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - q.x1) * dx + (y - q.y1) * dy) / L2))
    return math.hypot(x - (q.x1 + t * dx), y - (q.y1 + t * dy))


def _walk_loop(start, by_pt, key, max_edges=8):
    """Follow endpoint adjacency from `start`; return the edge list of a simple closed loop through it, or None."""
    path = [start]
    a, cur = key(start.x1, start.y1), key(start.x2, start.y2)
    while len(path) < max_edges:
        nxt = [q for q in by_pt[cur] if q is not path[-1] and q not in path]
        if len(nxt) != 1:
            return None
        q = nxt[0]
        path.append(q)
        cur = key(q.x2, q.y2) if key(q.x1, q.y1) == cur else key(q.x1, q.y1)
        if cur == a:
            return path if len(path) >= 4 else None
    return None


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


# ------------------------------------------------------------------ PA07R3 (PA08-R1 §5): contextual classification of short transverse elements
SHORT_ELEMENT_CLASSES = ("TRUE_WALL_RETURN", "JAMB", "WALL_NIB", "PIER", "COLUMN", "FRAME", "ANNOTATION", "OTHER")


def short_element_rows(bands, sites, prims, roles):
    """Every short candidate (a pair shorter along its axis than it is thick, a column-sized loop, a block-borne strip) classified by
    its CONTEXT, never by a global relaxation: what it joins, what site it sits at, where its lines come from."""
    by_id = {b["BAND_ID"]: b for b in bands}
    rows = []
    for b in bands:
        ev = b["EVIDENCE"]; reason = (b["REASON"] or "").split(" (")[0]
        short = b.get("R2_SHORT_TRANSVERSE") or b.get("LOOP") or b.get("R2_WALL_NIB_OF") or b.get("R2_COLUMN_CANDIDATE") or reason in ("MIXED_BLOCK_STRIP", "REPEATED_BLOCK_SYMBOL_STRIP", "THIN_PAIR_BELOW_WALL_MINIMUM", "REPETITION_FAMILY", "CLOSED_LOOP_UNRESOLVED", "WALL_NIB_OR_PIER", "COLUMN_CANDIDATE", "SHORT_TRANSVERSE_PAIR")
        if not short:
            continue
        cls, why = "OTHER", "no context rule applies"
        at_site = None
        for s in sites:
            h = by_id.get(s["HOST_BAND_ID"])
            if h is None or h is b:
                continue
            for t in (s["AXIAL_START"], s["AXIAL_END"]):
                x, y = MB.band_point(h, t)
                if MB.in_strip(b, x, y, tol=MB.JUNCTION_TOL):
                    at_site = s; break
            if at_site:
                break
        if b.get("R3_WALL_RETURN_OF"):
            cls, why = "TRUE_WALL_RETURN", f"joined to accepted band {b['R3_WALL_RETURN_OF']} of the same authored thickness"
        elif at_site is not None:
            cls, why = "JAMB", f"sits at a jamb of site {at_site['SITE_ID']} ({at_site['CLASS']})"
        elif b.get("R2_WALL_NIB_OF"):
            cls, why = "WALL_NIB", f"closed outline of the host wall's thickness on the axis of {b['R2_WALL_NIB_OF']}"
        elif b.get("BAND_TYPE") == "COLUMN_BAND" or b.get("R2_COLUMN_CANDIDATE"):
            cls, why = "COLUMN", "closed outline joined to the wall structure / free-standing with cross or hatch"
        elif b.get("LOOP") and reason == "CLOSED_LOOP_UNRESOLVED":
            cls, why = "PIER", "column-sized closed outline joined to no wall band: pier, trap, appliance or tile"
        elif b["BLOCK"] or reason in ("MIXED_BLOCK_STRIP", "REPEATED_BLOCK_SYMBOL_STRIP", "THIN_PAIR_BELOW_WALL_MINIMUM"):
            cls, why = "FRAME", "block-borne or thinner than a wall: door / window frame, leaf or symbol piece"
        elif reason == "REPETITION_FAMILY" or ev.get("FAMILY_FACES"):
            cls, why = "ANNOTATION", "member of a regular repetition family: hatch, treads, grid"
        rows.append({"BAND_ID": b["BAND_ID"], "KEY": b["KEY"], "STATUS": b["STATUS"], "THICKNESS_MM": round(b["THK"], 1), "LENGTH_MM": round(b["LENGTH"], 1), "CONTEXT_CLASS": cls, "WHY": why,
                     "REASON": b["REASON"], "LAYERS": sorted({f.provenance.layer for f in b["FACES"].values()}), "BLOCK": b["BLOCK"], "AT_SITE": at_site["SITE_ID"] if at_site else None,
                     "COUNTED_AS_WALL": b["STATUS"] == "ACCEPTED" and cls == "TRUE_WALL_RETURN", "PRINCIPLE": "context decides; a short element is never promoted by thickness alone and never by a global relaxation"})
    return rows
