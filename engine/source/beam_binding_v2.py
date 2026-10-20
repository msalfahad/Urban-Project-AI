"""BEAM BINDING V2 (T-085) - three corrections to how slab-plan beam bands are cut, bound and completed, as a NEW
policy beside the frozen MEMBER_DETECTION_V1 (engine/source/member_detection.py is read, never changed). Not wired
into any released method: a method version that wants it calls these functions instead of the V1 ones.

1. Planted columns do not cut the beam that carries them.
   V1 `split_at_supports` cuts a band at every column outline it overlaps. A column printed as planted ('P.C 20x50')
   stands ON the beam and is carried by it; it is no support. `planted_columns` links each planted-column label to
   one column outline by the drawing's own leader (the label's landing line, the leader to its tip, the tip on a
   circle round the column or inside the column outline) and checks the outline against the printed section;
   `split_at_supports_v2` then leaves the band whole across a LINKED planted column that lies inside the band's
   width. A label with no leader, a leader that reaches no column, or a printed section that differs from the drawn
   outline is reported and the column stays a support (V1 behaviour: nothing is released on a guess).

2. A mark is not compared with an arc band without a direction test.
   V1 `bind_marks` skips the text-angle test for ARC bands (band_axis_deg is None), so a straight mark beside an arc
   piece counts the arc as a second candidate and is held AMBIGUOUS (Alsenan GF B7 strip). `bind_marks_v2` gives an
   arc band the set of directions it actually takes (its tangent over its angular range) and applies the SAME
   angle tolerance as straight bands. No distance tolerance is added or changed.

3. Beam upstands are their own line, only from a printed section.
   `section_profile` decomposes a dimensioned rectilinear section outline into the beam rectangle and an upstand
   above it; every length used must be printed by a dimension on that outline, and the printed unit is proven by the
   schedule row of the beam (printed beam width / schedule width), never assumed. `section_cuts` binds a section
   title ('SECTION A-A') to its cut line on the plan (the cut line crosses the section's view arrows, the arrows'
   nearest titled letter is the section letter) and `upstand_lines` turns a printed upstand into width x height x
   the clear span the cut line crosses. Anything missing stays HELD with its reason; missing never becomes 0.

Rules: owner Q-16 = A (exhaust the drawing, never copy a neighbour's section), UP-QTY-STATUS-001 (MEASURED / HELD /
UNSUPPORTED, no silent omission), UP-KB-PREC-001. Tolerances: only the caller's existing ones (the route's drawing
tolerance `tol_native`, the binder's width / angle tolerances and its text gap). Project-agnostic; stdlib + shapely.

4. Ring beams round circular openings (owner Q-44 = A: the ring round each dome / skylight opening stays).
   `ring_beams` finds every pair of concentric drawn circles / arcs whose radial gap is a scheduled beam width, takes
   its section from the mark bound to an arc piece of that ring (PRINTED_MARK) or, when no mark is printed on that
   ring, from a section the caller passes with its basis (e.g. an owner answer: OWNER_RULE), else HELD; the
   concrete is the full annulus less what straight beam bands and columns already own, times the scheduled depth.
   V1 pairs only ARC entities, so a ring whose inner face is a full CIRCLE has no band at all (silent).
"""

from __future__ import annotations

import math
import re

from engine.source import member_detection as MD

POLICY_ID = "BEAM_BINDING_V2"
# the planted-column label of the generic route (generic_route._planted_column_items / conventions
# PLANTED_COLUMN_LABELS): callers pass the conventions' pattern and unit; these are only the documented defaults
PLANTED_LABEL = r"^\s*P\.?\s*C\.?\s*(\d{2,3})\s*[xX*]\s*(\d{2,3})\s*$"
PLANTED_LABEL_UNIT_M = 0.01
SECTION_TITLE = re.compile(r"SECTION\s*([A-Z0-9]{1,2})\s*-\s*\1\b")


# ----------------------------------------------------------------------------------------------------- geometry
def _dir(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0


def _adiff(a, b):
    """smallest difference of two undirected line directions, degrees in [0, 90]"""
    return abs(((a - b) + 90.0) % 180.0 - 90.0)


def _pt_seg(p, a, b):
    ax, ay = b[0] - a[0], b[1] - a[1]
    L2 = ax * ax + ay * ay
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * ax + (p[1] - a[1]) * ay) / L2))
    return math.hypot(p[0] - a[0] - t * ax, p[1] - a[1] - t * ay)


def _seg_cross(a, b, c, d):
    """proper or touching intersection point of segments ab and cd, or None"""
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-12:
        return None
    t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den
    u = ((c[0] - a[0]) * r[1] - (c[1] - a[1]) * r[0]) / den
    if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9:
        return (a[0] + t * r[0], a[1] + t * r[1])
    return None


def _in_box(p, box, grow=0.0):
    return box[0] - grow <= p[0] <= box[2] + grow and box[1] - grow <= p[1] <= box[3] + grow


# ------------------------------------------------------------------------------------- 2. arc-aware binding
def arc_directions(b):
    """(lo_deg, span_deg) of the tangent directions an ARC band takes over its angular range, mod 180; None when the
    band carries no range (then the caller cannot test the angle and says so)."""
    rng = b.get("OVERLAP_RANGE")
    if rng and len(rng) == 2:
        a0, a1 = float(rng[0]), float(rng[1])
        span = (a1 - a0) % 360.0 if a1 != a0 else 0.0
    elif b.get("start_rad") is not None and b.get("overlap_rad") is not None:
        a0 = math.degrees(float(b["start_rad"]))
        span = math.degrees(float(b["overlap_rad"]))
    else:
        return None
    return ((a0 + 90.0) % 180.0, min(span, 180.0))


def arc_angle_gap(rot_deg, b):
    """smallest angle between a text direction and any tangent direction of the arc band (degrees), None if the
    band has no angular range"""
    d = arc_directions(b)
    if d is None:
        return None
    lo, span = d
    if span >= 180.0:
        return 0.0
    x = (rot_deg % 180.0 - lo) % 180.0
    return 0.0 if x <= span else min(x - span, 180.0 - x)


def bind_marks_v2(bands, beam_marks, widths_of, unit_m, width_tol_m=0.015, angle_tol=12.0):
    """MEMBER_DETECTION_V1.bind_marks with one change: an ARC band qualifies only when the mark's direction is within
    angle_tol of a tangent direction the arc takes (V1 skipped the test for arcs). Same states, same distance gap,
    same width test, same ambiguity margin. An arc with no angular range keeps V1 behaviour and is flagged
    `arc_angle_untested` on the mark."""
    by_id = {b["band_id"]: b for b in bands}
    out = []
    for m in beam_marks:
        w_sched = widths_of.get((m["family"], m["mark"]))
        ws = None if w_sched is None else tuple(w_sched) if isinstance(w_sched, (list, tuple, set)) else (w_sched,)
        ws = tuple(w for w in ws if w) if ws else None
        untested = []

        def qualifies(b, check_width):
            if check_width and (not ws or all(abs(b["width_native"] * unit_m - w) > width_tol_m for w in ws)):
                return None
            ax = MD.band_axis_deg(b)
            if ax is not None:
                if _adiff(m["rot"], ax) > angle_tol:
                    return None
            elif b["kind"] == "ARC":
                g = arc_angle_gap(m["rot"], b)
                if g is None:
                    untested.append(b["band_id"])
                elif g > angle_tol:
                    return None
            gap = max(m["h"] * 2.5, b["width_native"] * 1.5)
            dd = MD.dist_point_poly(m["x"], m["y"], b["polygon"])
            return dd if dd <= gap else None
        extra = {}
        if not ws:
            out.append(dict(m, state="TYPE_NOT_IN_SCHEDULE", band=None, bands=[]))
            continue
        cands = sorted((d, b["band_id"]) for b in bands if (d := qualifies(b, True)) is not None)
        state = "BOUND"
        if not cands:
            cands = sorted((d, b["band_id"]) for b in bands if (d := qualifies(b, False)) is not None)
            state = "BOUND_WIDTH_CONFLICT"
        if untested:
            extra["arc_angle_untested"] = sorted(set(untested))
        if not cands:
            out.append(dict(m, state="TAG_UNBOUND", band=None, bands=[], **extra))
            continue
        first = by_id[cands[0][1]]
        chain = [c for c in cands if MD._same_arc_chain(first, by_id[c[1]], first["width_native"] * 0.1)]
        if first["kind"] == "ARC" and len(chain) > 1:
            out.append(dict(m, state="BOUND_ARC_CHAIN" if state == "BOUND" else state, band=first["band_id"],
                            bands=[c[1] for c in chain], **extra))
        elif len(cands) == 1 or cands[1][0] - cands[0][0] > max(m["h"], 1e-9):
            out.append(dict(m, state=state, band=cands[0][1], bands=[cands[0][1]], gap_native=cands[0][0], **extra))
        else:
            out.append(dict(m, state="AMBIGUOUS", band=None, bands=[], candidates=[c[1] for c in cands[:3]], **extra))
    return out


# ------------------------------------------------------------------------------------- 1. planted columns
def _chains(segments, layer, tol):
    """connected segment chains of one layer (endpoints within tol); each chain: list of segments"""
    segs = [s for s in segments if s.get("layer") == layer]
    parent = list(range(len(segs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, a in enumerate(segs):
        for j in range(i + 1, len(segs)):
            b = segs[j]
            if min(math.dist(p, q) for p in (a["a"], a["b"]) for q in (b["a"], b["b"])) <= tol:
                parent[find(i)] = find(j)
    groups = {}
    for i, s in enumerate(segs):
        groups.setdefault(find(i), []).append(s)
    return list(groups.values())


def _chain_ends(chain, tol):
    pts = [p for s in chain for p in (s["a"], s["b"])]
    return [p for p in pts if sum(1 for q in pts if math.dist(p, q) <= tol) == 1]


def planted_columns(texts, segments, circles, column_boxes, unit_m, tol_native, *, label_pattern=PLANTED_LABEL,
                    label_unit_m=PLANTED_LABEL_UNIT_M, size_tol_m=0.02, angle_tol=12.0, annotation_layers=None):
    """One record per planted-column label on the sheet:
        LINKED            leader found, it ends at exactly one column outline whose drawn size is the printed one
        SECTION_MISMATCH  the leader reaches a column, but its drawn size is not the printed section (stays a support)
        LEADER_NO_COLUMN  a leader is found but its tip reaches no column outline / no circle round one
        NO_LEADER         no landing line under the label
        AMBIGUOUS         the tip reaches two or more columns
    Landing: a segment of the label's own annotation drawing, parallel to the text (angle_tol), at most one text
    height from the text anchor and running under it; the leader is the chain of segments connected to it on that
    layer; its tip is the chain end farthest from the label. Tip -> column: the tip inside a column outline (within
    tol_native), or on a circle (|distance - r| <= tol_native) whose centre lies inside a column outline.
    annotation_layers: the layers a leader may be on (None = any layer that is not a band-edge or column layer is the
    caller's job to pass; here None means every layer)."""
    pat = re.compile(label_pattern)
    out = []
    for t in texts:
        mt = pat.match(t.get("value") or "")
        if not mt:
            continue
        a_m, b_m = int(mt.group(1)) * label_unit_m, int(mt.group(2)) * label_unit_m
        h = t.get("height") or 0.0
        rot = t.get("rotation") or 0.0
        anchor = (t["x"], t["y"])
        rec = {"text_id": t.get("id"), "label": t["value"], "section_m": (a_m, b_m), "x": t["x"], "y": t["y"]}
        landing = []
        for s in segments:
            if annotation_layers is not None and s.get("layer") not in annotation_layers:
                continue
            if math.dist(s["a"], s["b"]) <= 0 or _adiff(_dir(s["a"], s["b"]), rot) > angle_tol:
                continue
            ux, uy = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            ta = (s["a"][0] - anchor[0]) * ux + (s["a"][1] - anchor[1]) * uy
            tb = (s["b"][0] - anchor[0]) * ux + (s["b"][1] - anchor[1]) * uy
            if not (min(ta, tb) <= 0.0 <= max(ta, tb)):
                continue
            perp = _pt_seg(anchor, s["a"], s["b"])
            if perp <= h:
                landing.append((perp, s))
        if not landing:
            out.append(dict(rec, state="NO_LEADER"))
            continue
        landing.sort(key=lambda x: x[0])
        s0 = landing[0][1]
        chain = next(c for c in _chains(segments, s0.get("layer"), tol_native) if any(x is s0 for x in c))
        ends = _chain_ends(chain, tol_native) or [s0["a"], s0["b"]]
        tip = max(ends, key=lambda p: math.dist(p, anchor))
        hits = []
        for c in column_boxes:
            if _in_box(tip, c, tol_native):
                hits.append(("TIP_IN_OUTLINE", c))
                continue
            for ci in circles or ():
                if abs(math.dist(tip, ci["c"]) - ci["r"]) <= tol_native and _in_box(ci["c"], c):
                    hits.append(("TIP_ON_CIRCLE", c))
                    break
        rec.update(leader=[(s.get("id"), s.get("layer")) for s in chain], tip=tip)
        uniq = {tuple(c) for _, c in hits}
        if not uniq:
            out.append(dict(rec, state="LEADER_NO_COLUMN"))
            continue
        if len(uniq) > 1:
            out.append(dict(rec, state="AMBIGUOUS", columns=sorted(uniq)))
            continue
        how, box = hits[0]
        dw, dh = sorted(((box[2] - box[0]) * unit_m, (box[3] - box[1]) * unit_m))
        pw, ph = sorted((a_m, b_m))
        same = abs(dw - pw) <= size_tol_m and abs(dh - ph) <= size_tol_m
        out.append(dict(rec, state="LINKED" if same else "SECTION_MISMATCH", column=tuple(box), link=how,
                        drawn_m=(round(dw, 4), round(dh, 4))))
    return out


def _inside_width(b, box, tol_native):
    """the column outline lies across the band's width only inside its two faces (planted ON the beam)"""
    n = b["n"]
    ns = [x * n[0] + y * n[1] for x, y in MD.box_poly(box)]
    lo, hi = sorted((b["lo_off"], b["hi_off"]))
    return min(ns) >= lo - tol_native and max(ns) <= hi + tol_native


def split_at_supports_v2(bands, column_boxes, min_piece_native, min_overlap_native2=0.0, planted=(),
                         tol_native=0.0):
    """MEMBER_DETECTION_V1.split_at_supports with one change: a column outline that `planted_columns` LINKED to a
    planted-column label and that lies inside the band's width does not cut the band (the beam carries it). Such a
    column is listed on the piece as `carries_planted`; every other column cuts exactly as in V1."""
    linked = {tuple(p["column"]) for p in planted if p.get("state") == "LINKED"}
    out = []
    for b in bands:
        if b["kind"] != "STRAIGHT" or not column_boxes:
            out.append(dict(b, parent=b["band_id"], cut_by=[], carries_planted=[]))
            continue
        u, n = b["u"], b["n"]
        cuts, carried = [], []
        for c in column_boxes:
            poly = MD.box_poly(c)
            if MD.overlap_area(b["polygon"], poly) <= min_overlap_native2:
                continue
            if tuple(c) in linked and _inside_width(b, c, tol_native):
                carried.append(tuple(round(v, 1) for v in c))
                continue
            ts = [x * u[0] + y * u[1] for x, y in poly]
            cuts.append((max(min(ts), b["t0"]), min(max(ts), b["t1"]), tuple(round(v, 1) for v in c)))
        cuts.sort()
        pieces, t = [], b["t0"]
        for c0, c1, cid in cuts:
            if c0 > t:
                pieces.append((t, c0))
            t = max(t, c1)
        if b["t1"] > t:
            pieces.append((t, b["t1"]))
        pieces = [pc for pc in pieces if pc[1] - pc[0] >= min_piece_native]
        if not cuts:
            out.append(dict(b, parent=b["band_id"], cut_by=[], carries_planted=carried))
            continue
        for k, (t0, t1) in enumerate(pieces, 1):
            lo, hi = b["lo_off"], b["hi_off"]
            poly = [(u[0] * t0 + n[0] * lo, u[1] * t0 + n[1] * lo), (u[0] * t1 + n[0] * lo, u[1] * t1 + n[1] * lo),
                    (u[0] * t1 + n[0] * hi, u[1] * t1 + n[1] * hi), (u[0] * t0 + n[0] * hi, u[1] * t0 + n[1] * hi)]
            on = [cb for cb in carried if t0 <= ((cb[0] + cb[2]) / 2 * u[0] + (cb[1] + cb[3]) / 2 * u[1]) <= t1]
            out.append(dict(b, band_id=f"{b['band_id']}.{k}", parent=b["band_id"], t0=t0, t1=t1, length=t1 - t0,
                            polygon=poly, cut_by=[c[2] for c in cuts], carries_planted=on))
    return out


# ------------------------------------------------------------------------------------- 3. upstands
def _strips(pts, tol):
    """horizontal strips of a rectilinear polygon: [(y0, y1, x0, x1)], or None when an edge is not axis-parallel or a
    strip is not one interval"""
    n = len(pts)
    edges = [(pts[i], pts[(i + 1) % n]) for i in range(n)]
    for a, b in edges:
        if abs(a[0] - b[0]) > tol and abs(a[1] - b[1]) > tol:
            return None
    ys = []
    for y in sorted(p[1] for p in pts):                  # one level per drawn height (vertices within tol merge)
        if not ys or y - ys[-1] > tol:
            ys.append(y)
    out = []
    for y0, y1 in zip(ys, ys[1:]):
        ym = (y0 + y1) / 2
        xs = sorted(a[0] for a, b in edges if abs(a[0] - b[0]) <= tol and min(a[1], b[1]) < ym < max(a[1], b[1]))
        if len(xs) != 2:
            return None
        out.append((y0, y1, xs[0], xs[1]))
    return out


def _printed(dims, axis, lo, hi, tol):
    """the printed dimensions that measure [lo, hi] along axis ('x' or 'y'): [(shown value, drawn length)]"""
    out = []
    for d in dims:
        if d.get("axis") != axis or d.get("shown") is None:
            continue
        a, b = sorted((d["lo"], d["hi"]))
        if abs(a - lo) <= tol and abs(b - hi) <= tol:
            out.append((float(d["shown"]), b - a))
    return out


def section_profile(outline, dims, schedule_w_m, schedule_d_m, tol):
    """A printed beam section -> {state, beam_w_m, beam_d_m, upstand:{w_m, h_m, side} | None, unit_m, scale, why}.
    outline: the section outline vertices (section-view units, y up); dims: [{axis, lo, hi, shown}] (shown = the
    printed number, DIMLFAC applied); schedule_w_m / _d_m: the beam's schedule row (m).
    The beam is the widest strip stack; an upstand is a narrower stack ABOVE it. The printed unit is the schedule
    width over the printed beam width (must be 0.01 or 0.001 or 1 exactly: cm / mm / m); every length that is used
    needs its own printed dimension; one drawing scale for all of them."""
    pts = [tuple(p[:2]) for p in outline]
    if len(pts) > 2 and math.dist(pts[0], pts[-1]) <= tol:
        pts = pts[:-1]
    st = _strips(pts, tol)
    if not st:
        return {"state": "UNSUPPORTED", "why": "outline is not one rectilinear profile"}
    wmax = max(s[3] - s[2] for s in st)
    beam = [s for s in st if abs((s[3] - s[2]) - wmax) <= tol]
    by0, by1 = min(s[0] for s in beam), max(s[1] for s in beam)
    if any(not (s[1] <= by0 + tol or s[0] >= by1 - tol) for s in st if s not in beam):
        return {"state": "UNSUPPORTED", "why": "the full-width part is not one stack"}
    bx0, bx1 = beam[0][2], beam[0][3]
    above = [s for s in st if s[0] >= by1 - tol]
    pw = _printed(dims, "x", bx0, bx1, tol)
    pd = _printed(dims, "y", by0, by1, tol)
    if not pw:
        return {"state": "HELD", "why": "beam width not printed on the section"}
    shown_w, drawn_w = pw[0]
    f = schedule_w_m / shown_w if shown_w else None
    unit = next((k for k in (0.01, 0.001, 1.0) if f and abs(f - k) <= k * 1e-6), None)
    if unit is None:
        return {"state": "HELD", "why": f"printed beam width {shown_w:g} does not match the schedule width "
                                        f"{schedule_w_m:g} m in cm, mm or m"}
    scale = shown_w / drawn_w

    def val(p):
        shown, drawn = p
        if abs(shown / drawn - scale) > scale * 1e-3:
            return None
        return shown * unit
    rec = {"beam_w_m": round(shown_w * unit, 6), "unit_m": unit, "scale": scale, "upstand": None}
    if not pd or val(pd[0]) is None:
        return dict(rec, state="HELD", why="beam depth not printed on the section (or at another scale)")
    rec["beam_d_m"] = round(val(pd[0]), 6)
    if schedule_d_m is not None and abs(rec["beam_d_m"] - schedule_d_m) > 1e-6:
        return dict(rec, state="HELD", why=f"section depth {rec['beam_d_m']:g} m differs from the schedule "
                                           f"{schedule_d_m:g} m (designer RFI)")
    if not above:
        return dict(rec, state="PRINTED")
    ux0, ux1 = above[0][2], above[0][3]
    if any(abs(s[2] - ux0) > tol or abs(s[3] - ux1) > tol for s in above):
        return dict(rec, state="UNSUPPORTED", why="the part above the beam changes width (not one upstand)")
    uy1 = max(s[1] for s in above)
    w = _printed(dims, "x", ux0, ux1, tol)
    hh = _printed(dims, "y", by1, uy1, tol)
    if not w or not hh or val(w[0]) is None or val(hh[0]) is None:
        return dict(rec, state="HELD", why="upstand drawn but its width or height is not printed",
                    upstand={"w_m": None, "h_m": None})
    side = "FLUSH_RIGHT" if abs(ux1 - bx1) <= tol else "FLUSH_LEFT" if abs(ux0 - bx0) <= tol else "INSIDE"
    rec["upstand"] = {"w_m": round(val(w[0]), 6), "h_m": round(val(hh[0]), 6), "side": side}
    return dict(rec, state="PRINTED")


def section_cuts(texts, segments, bands, unit_m, *, edge_layers=(), angle_tol=12.0, titles=None):
    """Section letter -> cut line on one plan sheet.
    titles: the section letters that have a printed title 'SECTION X-X' anywhere in the set (from SECTION_TITLE).
    A cut line is a straight segment, not on a band-edge layer, that crosses at least one band face to face at a right
    angle (angle_tol) and is crossed at a right angle by at least one shorter segment (a view arrow). Each arrow takes
    the single-letter titled text nearest to its midpoint; a cut whose arrows name one letter is that letter's cut.
    Returns {letter: {state CUT / AMBIGUOUS, segment, bands:[band ids crossed]}}."""
    letters = [t for t in texts if (t.get("value") or "").strip() in (titles or ())]
    if not letters:
        return {}
    straight = [b for b in bands if b["kind"] == "STRAIGHT"]

    def crossed(s):
        hit = []
        for b in straight:
            ax = MD.band_axis_deg(b)
            if _adiff(_dir(s["a"], s["b"]), ax + 90.0) > angle_tol:
                continue
            u, n = b["u"], b["n"]
            na = s["a"][0] * n[0] + s["a"][1] * n[1]
            nb = s["b"][0] * n[0] + s["b"][1] * n[1]
            lo, hi = sorted((b["lo_off"], b["hi_off"]))
            if not (min(na, nb) <= lo and max(na, nb) >= hi):
                continue
            # where the segment crosses the band centre line, the point must be inside the band's length
            mid = (lo + hi) / 2
            if nb == na:
                continue
            k = (mid - na) / (nb - na)
            p = (s["a"][0] + k * (s["b"][0] - s["a"][0]), s["a"][1] + k * (s["b"][1] - s["a"][1]))
            tt = p[0] * u[0] + p[1] * u[1]
            if b["t0"] <= tt <= b["t1"]:
                hit.append(b["band_id"])
        return hit
    cands = []
    for s in segments:
        if s.get("layer") in edge_layers or math.dist(s["a"], s["b"]) <= 0:
            continue
        hit = crossed(s)
        if hit:
            cands.append((s, hit))
    found = {}
    for s, hit in cands:
        L = math.dist(s["a"], s["b"])
        names = set()
        for a in segments:
            if a is s or math.dist(a["a"], a["b"]) >= L or _adiff(_dir(a["a"], a["b"]), _dir(s["a"], s["b"]) + 90) \
                    > angle_tol or _seg_cross(s["a"], s["b"], a["a"], a["b"]) is None:
                continue
            mid = ((a["a"][0] + a["b"][0]) / 2, (a["a"][1] + a["b"][1]) / 2)
            near = min(letters, key=lambda t: math.dist((t["x"], t["y"]), mid))
            if min(math.dist((t["x"], t["y"]), mid) for t in texts if t is not near and
                   (t.get("value") or "").strip()) < math.dist((near["x"], near["y"]), mid):
                continue                                # another text is nearer: this is no view arrow of a letter
            names.add(near["value"].strip())
        if len(names) == 1:
            found.setdefault(next(iter(names)), []).append((s, hit))
    out = {}
    for k, v in found.items():
        if len(v) == 1:
            out[k] = {"state": "CUT", "segment": (v[0][0].get("id"), v[0][0]["a"], v[0][0]["b"]), "bands": v[0][1]}
        else:
            out[k] = {"state": "AMBIGUOUS", "segments": [x[0].get("id") for x in v]}
    return out


def upstand_lines(profile, cut, bands, unit_m, *, section="?", mark=None, width_tol_m=0.015):
    """A printed upstand on the clear span its cut line crosses: one record
    {state MEASURED / HELD, band, w_m, h_m, length_m, volume_m3, formula, why}. The span is the crossed band whose
    width is the printed beam width (binder width tolerance); none or two -> HELD."""
    rec = {"section": section, "mark": mark}
    if not profile or profile.get("state") != "PRINTED":
        return dict(rec, state="HELD", why=(profile or {}).get("why", "no printed section"))
    up = profile.get("upstand")
    if not up:
        return dict(rec, state="NOT_PRESENT", why="the printed section has no upstand")
    if not cut or cut.get("state") != "CUT":
        return dict(rec, state="HELD", why="the section's cut line is not found on the plan", w_m=up["w_m"],
                    h_m=up["h_m"])
    by = {b["band_id"]: b for b in bands}
    hit = [by[i] for i in cut["bands"] if i in by and abs(by[i]["width_native"] * unit_m - profile["beam_w_m"]) <=
           width_tol_m]
    if len(hit) != 1:
        return dict(rec, state="HELD", why=f"{len(hit)} crossed bands at the printed width", w_m=up["w_m"],
                    h_m=up["h_m"])
    b = hit[0]
    L = MD.band_length_native(b) * unit_m
    v = up["w_m"] * up["h_m"] * L
    return dict(rec, state="MEASURED", band=b["band_id"], w_m=up["w_m"], h_m=up["h_m"], length_m=round(L, 6),
                volume_m3=round(v, 6), side=up["side"],
                formula=f"{up['w_m']:g} x {up['h_m']:g} (printed section {section}) x {L:.3f} (clear span crossed "
                        f"by the cut line)")


# ------------------------------------------------------------------------------------- 4. ring beams
def ring_beams(arcs, circles, bands, column_boxes, marks, widths_of, lib, unit_m, tol_native, *, width_tol_m=0.015,
               fallback=None, parent_bands=None):
    """One record per circular ring (two concentric drawn faces, radial gap = a scheduled beam width):
        {centre, r_inner_m, r_outer_m, state PRINTED_MARK / OWNER_RULE / HELD, mark, section_m, annulus_m2,
         owned_by_others_m2, net_plan_m2, volume_m3, arc_bands (the ARC band pieces this line replaces), why}
    marks: the bound marks (bind_marks_v2 output); a mark bound to an ARC band of this ring names its section.
    fallback: {"family", "mark", "basis"} used only for a ring with no mark of its own (e.g. an owner answer).
    parent_bands: the bands before the support split; a face running into a beam's full width counts as closed there
    (V1's split leaves the strip beside a narrow column to no one), while the deduction is what the pieces and the
    columns own."""
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    def span(a):
        a0 = math.atan2(a["s"][1] - a["c"][1], a["s"][0] - a["c"][0])
        a1 = math.atan2(a["e"][1] - a["c"][1], a["e"][0] - a["c"][0])
        if a.get("dir") == "CW":
            a0, a1 = a1, a0
        return (math.degrees(a0) % 360.0, (math.degrees(a1) - math.degrees(a0)) % 360.0)
    curves = [("C", c["c"], c["r"], (0.0, 360.0)) for c in circles or ()] + \
        [("A", a["c"], a["r"], span(a)) for a in arcs or ()]
    centres = []
    for _, c, r, _s in curves:
        if not any(math.dist(c, x) <= tol_native for x in centres):
            centres.append(c)
    ws = sorted({w for v in widths_of.values() for w in (v if isinstance(v, (list, tuple, set)) else (v,)) if w})
    arc_by_id = {b["band_id"]: b for b in bands if b["kind"] == "ARC"}
    straight = [Polygon(b["polygon"]) for b in bands if b["kind"] == "STRAIGHT"]
    others = unary_union([p.buffer(0) for p in straight] + [Polygon(MD.box_poly(c)) for c in column_boxes or ()]) \
        if (straight or column_boxes) else None
    par = [Polygon(b["polygon"]).buffer(0) for b in (parent_bands or bands) if b["kind"] == "STRAIGHT"]
    closer = unary_union(par + [Polygon(MD.box_poly(c)) for c in column_boxes or ()]) if (par or column_boxes) \
        else None
    out = []
    for c in centres:
        radii = []
        for _, cc, r, _s in curves:
            if math.dist(cc, c) <= tol_native and not any(abs(r - x) <= tol_native for x in radii):
                radii.append(r)
        radii.sort()
        for i, ri in enumerate(radii):
            for ro in radii[i + 1:]:
                w = (ro - ri) * unit_m
                if not any(abs(w - x) <= width_tol_m for x in ws):
                    continue
                pieces = [bid for bid, b in arc_by_id.items() if math.dist(b["centre"], c) <= tol_native and
                          abs(b["r_inner"] - ri) <= tol_native and abs(b["r_outer"] - ro) <= tol_native]
                mk = sorted({(m["family"], m["mark"]) for m in marks if m.get("state", "").startswith("BOUND") and
                             set(m.get("bands") or []) & set(pieces)})
                rec = {"centre": tuple(c), "r_inner_m": round(ri * unit_m, 6), "r_outer_m": round(ro * unit_m, 6),
                       "arc_bands": sorted(pieces)}
                # the ring's own concrete: the annulus less the full width of every straight beam and column it runs
                # into; each remaining piece must be drawn: every point where it meets the inner or outer circle lies
                # on a drawn arc / circle of that face. A piece that meets the circles only where nothing is drawn
                # (the bulge beyond a beam's far face) is no concrete; a piece that meets them both drawn and undrawn
                # makes the ring PARTIAL (its arc band pieces stay as they are, nothing is guessed)
                spans = {r: [sp for _, cc, rr, sp in curves if math.dist(cc, c) <= tol_native and
                             abs(rr - r) <= tol_native] for r in (ri, ro)}

                def drawn(r, x, y):
                    ang = math.degrees(math.atan2(y - c[1], x - c[0])) % 360.0
                    slack = math.degrees(tol_native / r)
                    return any((ang - a0 + slack) % 360.0 <= sw + 2 * slack for a0, sw in spans[r])
                ring = Point(c).buffer(ro, 256).difference(Point(c).buffer(ri, 256))
                rest = ring.difference(closer) if closer is not None else ring
                parts = list(getattr(rest, "geoms", [rest])) if not rest.is_empty else []
                kept, mixed = [], []
                for g in parts:
                    if g.geom_type != "Polygon" or g.area * unit_m ** 2 < 1e-6:
                        continue
                    hits = [drawn(r, x, y) for x, y in g.exterior.coords for r in (ri, ro)
                            if abs(math.dist((x, y), c) - r) <= tol_native]
                    if hits and all(hits):
                        kept.append(g)
                    elif any(hits):
                        mixed.append(g)
                if mixed or not kept:
                    out.append(dict(rec, state="PARTIAL_RING", why="a ring piece meets a face where it is not drawn "
                                                                    "(its arc pieces stay as bands)" if mixed else
                                    "no drawn ring piece"))
                    continue
                exact = math.pi * (ro * ro - ri * ri) * unit_m ** 2
                net = sum(g.area for g in kept) * unit_m ** 2
                own = exact - net
                rec.update(annulus_m2=round(exact, 6), owned_by_others_m2=round(own, 6), net_plan_m2=round(net, 6))
                if len(mk) > 1:
                    out.append(dict(rec, state="HELD", why=f"two marks on one ring: {mk}"))
                    continue
                basis = None
                if mk:
                    fam, mark = mk[0]
                    basis = "PRINTED_MARK"
                elif fallback:
                    fam, mark, basis = fallback["family"], fallback["mark"], "OWNER_RULE"
                    rec["basis_note"] = fallback.get("basis")
                if basis is None:
                    out.append(dict(rec, state="HELD", why="no mark printed on this ring"))
                    continue
                row = lib.get((fam, mark))
                W = (row or {}).get("dims_m", {}).get("W")
                H = (row or {}).get("dims_m", {}).get("H")
                if not row or not W or not H or abs(W - w) > width_tol_m:
                    out.append(dict(rec, state="HELD", mark=mark, why="schedule row missing or its width is not "
                                                                       "the drawn ring width"))
                    continue
                out.append(dict(rec, state=basis, mark=mark, family=fam, section_m=(W, H),
                                volume_m3=round(net * H, 6),
                                pieces=len(kept),
                                formula=f"(pi x ({ro * unit_m:.4f}^2 - {ri * unit_m:.4f}^2) - {own:.4f} in straight "
                                        f"beams / columns or not drawn) x {H:g}"))
    return out


def policy_record():
    return {"policy": POLICY_ID, "supersedes_for_callers": "MEMBER_DETECTION_V1 split_at_supports / bind_marks",
            "frozen_untouched": "engine/source/member_detection.py",
            "rules": ["UP-QTY-STATUS-001", "UP-KB-PREC-001", "owner Q-16 = A"],
            "rule": "a linked planted column does not cut its beam; an arc band is direction-tested like a straight "
                    "one; an upstand is measured only from a printed section bound to its cut line; a ring beam is "
                    "the drawn annulus between two concentric faces less what straight beams and columns own"}
