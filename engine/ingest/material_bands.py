"""Material band engine (PA07A).

Wall material is established by geometric relationships between faces, never by
layer membership.  A MATERIAL_BAND is a cluster of parallel face pairs (or
concentric arcs) at one wall thickness along one axis, whose interior holds no
other parallel faces, that is not a repetition family, not a closed fitting
loop, not a frame inside another band's strip, not the outermost line of the
view, that does not claim a face another band already claims with material on
the other side, and that is anchored: long enough and joined to another
established band (or a closed column loop).  A face becomes quantity-eligible
only through an ACCEPTED band (or an explicitly configured one-face
construction type).  Every rejected or unresolved candidate keeps its reason.
No raster appearance repairs a rejected candidate.

Failure modes this closes (PA06 cold review): FM-P6-01 (wrong primitive /
layer families become walls).  The interval / opening logic lives in
band_topology.py (FM-P6-02, FM-P6-03).
"""

from __future__ import annotations

import itertools
import math
from collections import defaultdict

from engine.ingest import ids

BAND_TYPES = ("STRAIGHT_BAND", "ANGLED_BAND", "CURVED_BAND", "COLUMN_BAND", "UNRESOLVED_BAND")
STATUSES = ("ACCEPTED", "REJECTED", "UNRESOLVED")
THICKNESS = (50.0, 600.0)          # candidate pair range: below 50 mm two lines are one line
WALL_MIN_MM = 75.0                 # a pair thinner than this is drafting offset / line doubling / frame, never masonry
MIN_OVERLAP_MM = 300.0
MIN_OVERLAP_SHARE = 0.3
MIN_FREE_BAND_MM = 600.0           # a structure needs at least one band this long
STRUCTURE_MIN_MM = 2000.0          # total developed length of a joined group of bands before it counts as a wall structure
COLUMN_FREE_MAX = 600.0            # a closed loop up to this side length is a column even when free-standing
COLUMN_SIDE_MAX = 1200.0           # up to this side length a closed loop joined to a wall band is a column
JOINERY_DEPTH_MIN_MM = 300.0       # PA07R1: a closed outline deeper than this (wardrobe 600, counter 600, bath 700) is joinery until hatched or confirmed
ANGLE_TOL = math.radians(1.0)
AXIS_MERGE_MM = 30.0
THK_MERGE_MM = 25.0
MAX_BAND_GAP_MM = 3000.0           # collinear pairs closer than this belong to one band (openings are intervals)
FAMILY_MIN = 6                     # two walls with doubled lines are 4-5 parallel lines; a repetition needs more
FAMILY_LENGTH_BAND = (0.5, 2.0)    # family members have comparable lengths (hatch strokes, treads); a wall face beside them does not
FAMILY_SPACING_MAX = 400.0
JUNCTION_TOL = 80.0
ENCLOSURE_SHARE = 0.5              # interior parallel faces covering this share of the band -> not one solid
EDGE_TOL = 5.0
HATCH_FILL_SHARE = 0.3             # hatch strokes over this share of a band = material fill evidence
HATCH_STROKE_MAX_MM = 300.0        # a PA06 HATCH_STROKE longer than this is re-examined here: the PA06 family rule swallows wall faces
EXCLUDED_ROLES = ("DIMENSION_LINE", "DIMENSION_EXTENSION", "DIMENSION_TEXT", "TEXT_OR_LABEL", "DOOR_SWING", "DOOR_LEAF", "GRID_OR_LEVEL", "STAIR_EDGE", "BEAM_EDGE")
NON_MATERIAL_LINETYPES = ("HIDDEN", "DASHED", "DASH", "DOT", "CENTER", "PHANTOM", "DIVIDE", "BORDER",
                          "ISO02", "ISO03", "ISO04", "ISO05", "ISO06", "ISO07", "ISO08", "ISO09", "ISO10", "ISO11", "ISO12", "ISO13", "ISO14", "ISO15", "JIS_02", "JIS_08", "JIS_09", "JIS_10", "JIS_11")   # PA07R1: ISO / JIS broken-line names
TWO_PI = 2 * math.pi
N_DIR = int(round(math.pi / ANGLE_TOL))


def _len(p):
    if p.kind == "SEGMENT":
        return math.hypot(p.x2 - p.x1, p.y2 - p.y1)
    if p.kind == "ARC":
        return p.radius * (((p.end_angle - p.start_angle) % TWO_PI) or TWO_PI)
    return TWO_PI * p.radius


def _angle(p):
    return math.atan2(p.y2 - p.y1, p.x2 - p.x1) % math.pi


def _dir_key(ang):
    return int(round(ang / ANGLE_TOL)) % N_DIR


def _proj(p, ux, uy):
    a, b = p.x1 * ux + p.y1 * uy, p.x2 * ux + p.y2 * uy
    return (a, b) if a <= b else (b, a)


def _union(intervals):
    out = []
    for lo, hi in sorted(intervals):
        if out and lo <= out[-1][1]:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return [tuple(x) for x in out]


def _covered(intervals):
    return sum(hi - lo for lo, hi in _union(intervals))


def candidates(prims, roles):
    """Every segment / arc that is not annotation, swing, leaf, tread, beam, hidden or invisible linework.

    A PA06 HATCH_STROKE is excluded only when it is short (a stroke inside a wall) or a member of a regular repetition
    family found here; the PA06 family rule has no regularity test and tags 1-3 m wall faces beside door frames as hatch."""
    out = []
    for p in prims:
        if p.kind not in ("SEGMENT", "ARC"):
            continue
        r = roles.get(p.object_id, {})
        if r.get("ROLE") in EXCLUDED_ROLES:
            continue
        if r.get("ROLE") == "HATCH_STROKE" and _len(p) <= HATCH_STROKE_MAX_MM:
            continue
        lt = str(getattr(p.provenance, "linetype", "CONTINUOUS") or "").upper()
        if any(t in lt for t in NON_MATERIAL_LINETYPES) or getattr(p.provenance, "invisible", False):
            continue
        if _len(p) < 30:
            continue
        out.append(p)
    return out


def fill_strokes(prims, roles, family_ids):
    """Segments that count as material fill: short PA06 hatch strokes and members of a regular repetition family."""
    return [p for p in prims if p.kind == "SEGMENT" and _len(p) <= HATCH_STROKE_MAX_MM and (roles.get(p.object_id, {}).get("ROLE") == "HATCH_STROKE" or p.object_id in family_ids)]   # PA07R1: long family members (shelves, louvres, tiles) are never fill


# ------------------------------------------------------------------ repetition families
def _families(segs):
    """Object ids in a repetition family: >= FAMILY_MIN parallel segments of comparable length at regular spacing <= FAMILY_SPACING_MAX."""
    return set().union(*[set(g) for g in family_groups(segs)]) if segs else set()


def family_groups(segs):
    """Repetition families as lists of object ids (each family = one register row)."""
    by_dir = defaultdict(list)
    for p in segs:
        ang = _angle(p); ux, uy = math.cos(ang), math.sin(ang)
        lo, hi = _proj(p, ux, uy)
        by_dir[_dir_key(ang)].append((-uy * p.x1 + ux * p.y1, lo, hi, p))
    groups = []

    def close(run):
        if len(run) < FAMILY_MIN:
            return
        med = sorted(hi - lo for _, lo, hi, _ in run)[len(run) // 2]
        core = [r for r in run if FAMILY_LENGTH_BAND[0] * med <= r[2] - r[1] <= FAMILY_LENGTH_BAND[1] * med]
        if len(core) >= FAMILY_MIN and _regular([r[0] for r in core]):
            groups.append([r[3].object_id for r in core])
    for items in by_dir.values():
        items.sort(key=lambda t: t[0])
        run = []
        for off, lo, hi, p in items:
            if run:
                poff, plo, phi, _ = run[-1]
                if off - poff > FAMILY_SPACING_MAX or min(hi, phi) - max(lo, plo) < 0.5 * min(hi - lo, phi - plo):
                    close(run); run = []
            run.append((off, lo, hi, p))
        close(run)
    return groups


def _regular(offs):
    """Uniform spacing, or an alternating two-gap pattern (tread + nosing lines)."""
    gaps = [b - a for a, b in zip(offs, offs[1:])]
    if not gaps:
        return False

    def uniform(g):
        m = sum(g) / len(g)
        return m > 0 and max(abs(x - m) for x in g) <= 0.25 * m + 5
    if uniform(gaps):
        return True
    return len(gaps) >= 6 and uniform(gaps[0::2]) and uniform(gaps[1::2])


# ------------------------------------------------------------------ pairs
def _pairs(segs):
    """Parallel segment pairs at a candidate thickness with real overlap.  -> [(a, b, thk, (lo, hi), (ux, uy), axis)]"""
    by_dir = defaultdict(list)
    for p in segs:
        ang = _angle(p); ux, uy = math.cos(ang), math.sin(ang)
        by_dir[_dir_key(ang)].append((-uy * p.x1 + ux * p.y1, _proj(p, ux, uy), p, (ux, uy)))
    out = []
    for items in by_dir.values():
        items.sort(key=lambda t: t[0])
        for i, (off, (lo, hi), p, u) in enumerate(items):
            for off2, (lo2, hi2), q, _ in items[i + 1:]:
                d = off2 - off
                if d > THICKNESS[1] + 1e-6:
                    break
                if d < THICKNESS[0] - 1e-6:
                    continue
                olo, ohi = max(lo, lo2), min(hi, hi2)
                ov = ohi - olo
                if ov >= MIN_OVERLAP_MM or (ov > 0 and ov >= MIN_OVERLAP_SHARE * min(hi - lo, hi2 - lo2)):
                    out.append((p, q, d, (olo, ohi), u, (off + off2) / 2))
    return out


def _arc_span(a):
    return ((a.end_angle - a.start_angle) % TWO_PI) or TWO_PI


def _arc_pairs(arcs):
    """Concentric arcs at a candidate thickness with angular overlap -> [(a, b, thk, (t_lo, t_hi), r_axis, theta0)]

    The band parameter is developed distance on the axis radius measured from theta0 = the smaller start angle."""
    out = []
    for i, a in enumerate(arcs):
        for b in arcs[i + 1:]:
            if math.hypot(a.cx - b.cx, a.cy - b.cy) > AXIS_MERGE_MM or not (THICKNESS[0] <= abs(a.radius - b.radius) <= THICKNESS[1]):
                continue
            sa, sb = _arc_span(a), _arc_span(b)
            a0, b0 = a.start_angle % TWO_PI, b.start_angle % TWO_PI
            best, best_iv = 0.0, None
            for shift in (-TWO_PI, 0.0, TWO_PI):
                lo, hi = max(a0, b0 + shift), min(a0 + sa, b0 + shift + sb)
                if hi - lo > best:
                    best, best_iv = hi - lo, (lo, hi)
            r_axis = (a.radius + b.radius) / 2
            if best_iv and (best * r_axis >= MIN_OVERLAP_MM or best >= MIN_OVERLAP_SHARE * min(sa, sb)):
                out.append((a, b, abs(a.radius - b.radius), best_iv, r_axis))
    return out


# ------------------------------------------------------------------ clusters -> raw bands
def _cluster(items, same):
    """Union-find over items with a symmetric predicate."""
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if same(items[i], items[j]):
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[rj] = ri
    groups = defaultdict(list)
    for i in range(len(items)):
        groups[find(i)].append(items[i])
    return list(groups.values())


def _gap(iv1, iv2):
    return max(iv1[0], iv2[0]) - min(iv1[1], iv2[1])


def _straight_bands(pairs):
    by_dir = defaultdict(list)
    for pr in pairs:
        by_dir[_dir_key(_angle(pr[0]))].append(pr)
    bands = []
    for items in by_dir.values():
        def same(x, y):
            return abs(x[5] - y[5]) <= AXIS_MERGE_MM and abs(x[2] - y[2]) <= THK_MERGE_MM and _gap(x[3], y[3]) <= MAX_BAND_GAP_MM
        for grp in _cluster(items, same):
            ux, uy = grp[0][4]; nx, ny = -uy, ux
            axis = sum(g[5] for g in grp) / len(grp)
            thk = sorted(g[2] for g in grp)[len(grp) // 2]
            faces = {}
            for a, b, _, _, _, _ in grp:
                faces[a.object_id] = a; faces[b.object_id] = b
            side_a, side_b = {}, {}
            for f in faces.values():
                off = nx * f.x1 + ny * f.y1
                (side_a if off < axis else side_b)[f.object_id] = (off, _proj(f, ux, uy))
            cover = _union([g[3] for g in grp])
            lo, hi = cover[0][0], cover[-1][1]
            ang = _angle(grp[0][0])
            orient = "HORIZONTAL" if abs(math.sin(ang)) < 1e-3 else ("VERTICAL" if abs(math.cos(ang)) < 1e-3 else "ANGLED")
            bands.append({"KIND": "S", "U": (ux, uy), "NORMAL": (nx, ny), "ANGLE": ang, "AXIS": axis, "THK": thk, "THK_SPREAD": max(g[2] for g in grp) - min(g[2] for g in grp),
                          "FACES": faces, "SIDE_A": side_a, "SIDE_B": side_b, "EXTENT": (lo, hi), "COVER": cover, "PAIRS": [(a.object_id, b.object_id, round(t, 1), round(iv[1] - iv[0], 1)) for a, b, t, iv, _, _ in grp],
                          "ORIENTATION": orient, "STATUS": None, "REASON": None, "EVIDENCE": {}, "BAND_TYPE": None})
    return bands


def _curved_bands(apairs):
    bands = []
    def same(x, y):
        return math.hypot(x[0].cx - y[0].cx, x[0].cy - y[0].cy) <= AXIS_MERGE_MM and abs(x[4] - y[4]) <= AXIS_MERGE_MM and abs(x[2] - y[2]) <= THK_MERGE_MM
    for grp in _cluster(apairs, same):
        r_axis = sum(g[4] for g in grp) / len(grp)
        cx = sum(g[0].cx for g in grp) / len(grp); cy = sum(g[0].cy for g in grp) / len(grp)
        theta0 = min(g[3][0] for g in grp)
        cover = _union([((iv[0] - theta0) * r_axis, (iv[1] - theta0) * r_axis) for _, _, _, iv, _ in grp])
        thk = sorted(g[2] for g in grp)[len(grp) // 2]
        faces, side_a, side_b = {}, {}, {}
        for a, b, _, _, _ in grp:
            for f in (a, b):
                faces[f.object_id] = f
                (side_a if f.radius < r_axis else side_b)[f.object_id] = (f.radius, (((f.start_angle % TWO_PI) - theta0) % TWO_PI * r_axis, (((f.start_angle % TWO_PI) - theta0) % TWO_PI + _arc_span(f)) * r_axis))
        bands.append({"KIND": "C", "CENTRE": (cx, cy), "R_AXIS": r_axis, "THETA0": theta0, "THK": thk, "THK_SPREAD": max(g[2] for g in grp) - min(g[2] for g in grp), "FACES": faces, "SIDE_A": side_a, "SIDE_B": side_b,
                      "EXTENT": (cover[0][0], cover[-1][1]), "COVER": cover, "PAIRS": [(a.object_id, b.object_id, round(t, 1), round((iv[1] - iv[0]) * r, 1)) for a, b, t, iv, r in grp],
                      "ORIENTATION": "CURVED", "STATUS": None, "REASON": None, "EVIDENCE": {}, "BAND_TYPE": None})
    return bands


def _split_loops(bands, segs):
    """A pair whose two faces are joined at both ends by returns (a closed four-sided loop) becomes its own band, so a
    column drawn against a wall face does not swallow the wall's cluster and the wall does not swallow the column."""
    by_pt = defaultdict(list)
    for q in segs:
        by_pt[(round(q.x1 / 10), round(q.y1 / 10))].append(q); by_pt[(round(q.x2 / 10), round(q.y2 / 10))].append(q)

    def joined(p1, p2):
        k1, k2 = (round(p1[0] / 10), round(p1[1] / 10)), (round(p2[0] / 10), round(p2[1] / 10))
        return [q for q in by_pt[k1] if q in by_pt[k2] and _len(q) > 0]
    out = []
    for b in bands:
        loops = []
        for a_id, b_id, thk, ov in b["PAIRS"]:
            a, c = b["FACES"][a_id], b["FACES"][b_id]
            ends_a, ends_c = [(a.x1, a.y1), (a.x2, a.y2)], [(c.x1, c.y1), (c.x2, c.y2)]
            for (p, q) in ((ends_c[0], ends_c[1]), (ends_c[1], ends_c[0])):
                c1, c2 = joined(ends_a[0], p), joined(ends_a[1], q)
                if c1 and c2 and c1[0] is not c2[0]:
                    if _len(a) > COLUMN_SIDE_MAX or _len(c) > COLUMN_SIDE_MAX or thk > COLUMN_SIDE_MAX:
                        # PA07R1 (FM-P7-01): a closed outline longer than a column inside a wall cluster (wardrobe, counter, bath drawn against the wall face)
                        b["LONG_LOOP"] = True
                        b["EVIDENCE"].setdefault("CLOSED_OUTLINE", []).append([a.object_id, c.object_id, c1[0].object_id, c2[0].object_id])
                    else:
                        loops.append((a, c, c1[0], c2[0], thk))
                    break
        if not loops or len(b["FACES"]) <= 2:
            out.append(b); continue
        for a, c, cap1, cap2, thk in loops:
            ux, uy = b["U"]; nx, ny = b["NORMAL"]
            lo, hi = _proj(a, ux, uy)
            axis = (nx * a.x1 + ny * a.y1 + nx * c.x1 + ny * c.y1) / 2
            sa, sb = ({a.object_id: (nx * a.x1 + ny * a.y1, _proj(a, ux, uy))}, {c.object_id: (nx * c.x1 + ny * c.y1, _proj(c, ux, uy))})
            if nx * a.x1 + ny * a.y1 > axis:
                sa, sb = sb, sa
            out.append({"KIND": "S", "U": b["U"], "NORMAL": b["NORMAL"], "ANGLE": b["ANGLE"], "AXIS": axis, "THK": thk, "THK_SPREAD": 0.0, "FACES": {a.object_id: a, c.object_id: c},
                        "SIDE_A": sa, "SIDE_B": sb, "EXTENT": (lo, hi), "COVER": [(lo, hi)], "PAIRS": [(a.object_id, c.object_id, round(thk, 1), round(hi - lo, 1))],
                        "ORIENTATION": b["ORIENTATION"], "STATUS": None, "REASON": None, "EVIDENCE": {"LOOP_SPLIT": [cap1.object_id, cap2.object_id]}, "BAND_TYPE": None})
            for f in (a, c):
                b["FACES"].pop(f.object_id, None); b["SIDE_A"].pop(f.object_id, None); b["SIDE_B"].pop(f.object_id, None)
        b["PAIRS"] = [pr for pr in b["PAIRS"] if pr[0] in b["FACES"] and pr[1] in b["FACES"]]
        if b["PAIRS"] and b["SIDE_A"] and b["SIDE_B"]:
            cover = _union([(max(v[1][0], w[1][0]), min(v[1][1], w[1][1])) for v in b["SIDE_A"].values() for w in b["SIDE_B"].values() if min(v[1][1], w[1][1]) > max(v[1][0], w[1][0])])
            if cover:
                b["COVER"] = cover; b["EXTENT"] = (cover[0][0], cover[-1][1])
                out.append(b)
    # a loop's faces belong to the loop: drop them from every other cluster (a column side drawn on a wall face)
    loop_faces = {f for b in out if b["EVIDENCE"].get("LOOP_SPLIT") for f in b["FACES"]}
    final = []
    for b in out:
        if b["EVIDENCE"].get("LOOP_SPLIT") or not (set(b["FACES"]) & loop_faces):
            final.append(b); continue
        for f in list(b["FACES"]):
            if f in loop_faces:
                b["FACES"].pop(f); b["SIDE_A"].pop(f, None); b["SIDE_B"].pop(f, None)
        b["PAIRS"] = [pr for pr in b["PAIRS"] if pr[0] in b["FACES"] and pr[1] in b["FACES"]]
        if b["PAIRS"] and b["SIDE_A"] and b["SIDE_B"]:
            cover = _union([(max(v[1][0], w[1][0]), min(v[1][1], w[1][1])) for v in b["SIDE_A"].values() for w in b["SIDE_B"].values() if min(v[1][1], w[1][1]) > max(v[1][0], w[1][0])])
            if cover:
                b["COVER"] = cover; b["EXTENT"] = (cover[0][0], cover[-1][1]); b["EVIDENCE"]["LOOP_FACES_REMOVED"] = sorted(set(b["FACES"]) ^ set(b["FACES"]))
                final.append(b)
    return final


# ------------------------------------------------------------------ geometry helpers on bands
def band_point(b, t, side=0.0):
    """Point on the band axis at parameter t (developed mm), offset `side` mm along the normal (S) / radial (C)."""
    if b["KIND"] == "S":
        ux, uy = b["U"]; nx, ny = b["NORMAL"]; off = b["AXIS"] + side
        return ux * t + nx * off, uy * t + ny * off
    th = b["THETA0"] + t / b["R_AXIS"]; r = b["R_AXIS"] + side
    return b["CENTRE"][0] + r * math.cos(th), b["CENTRE"][1] + r * math.sin(th)


def band_param(b, x, y):
    """(t, d): developed parameter along the band and signed distance from the axis."""
    if b["KIND"] == "S":
        ux, uy = b["U"]; nx, ny = b["NORMAL"]
        return x * ux + y * uy, (x * nx + y * ny) - b["AXIS"]
    dx, dy = x - b["CENTRE"][0], y - b["CENTRE"][1]
    th = (math.atan2(dy, dx) - b["THETA0"]) % TWO_PI
    return th * b["R_AXIS"], math.hypot(dx, dy) - b["R_AXIS"]


def in_strip(b, x, y, tol=JUNCTION_TOL, along_tol=None):
    t, d = band_param(b, x, y)
    a = tol if along_tol is None else along_tol
    return abs(d) <= b["THK"] / 2 + tol and b["EXTENT"][0] - a <= t <= b["EXTENT"][1] + a


def _ends(b):
    return [band_point(b, b["EXTENT"][0]), band_point(b, b["EXTENT"][1])]


def _joins(b, others):
    """Junction evidence: an end of b inside another band's strip, or another band's end inside b's strip."""
    joins = []
    for k, (px, py) in enumerate(_ends(b)):
        for h in others:
            if h is b:
                continue
            if in_strip(h, px, py, along_tol=JUNCTION_TOL + b["THK"] / 2):
                joins.append({"END": "START" if k == 0 else "END", "AT_MM": round(b["EXTENT"][k], 1), "BAND": h.get("BAND_ID") or h.get("KEY"), "KIND": "T_OR_L_JUNCTION"})
                break
    for h in others:
        if h is b:
            continue
        for k, (px, py) in enumerate(_ends(h)):
            if in_strip(b, px, py, along_tol=JUNCTION_TOL + h["THK"] / 2):
                joins.append({"END": "SIDE", "AT_MM": round(band_param(b, px, py)[0], 1), "BAND": h.get("BAND_ID") or h.get("KEY"), "KIND": "HOSTS_T_JUNCTION"})
                break
    return joins


def _end_caps(b, segs, face_ids=frozenset()):
    """Perpendicular segments joining the two faces at the band ends (closed loop evidence).  Straight bands only.
    A segment that is itself a face of another band is a crossing wall's face, not a cap."""
    if b["KIND"] != "S":
        return []
    ux, uy = b["U"]; thk = b["THK"]; ang = b["ANGLE"]
    caps = []
    for q in segs:
        if q.object_id in b["FACES"] or q.object_id in face_ids or abs(((_angle(q) - ang) % math.pi) - math.pi / 2) > 5 * ANGLE_TOL:
            continue
        L = _len(q)
        if not (0.6 * thk <= L <= 1.4 * thk + 30):
            continue
        t, d = band_param(b, (q.x1 + q.x2) / 2, (q.y1 + q.y2) / 2)
        if abs(d) > thk / 2 + JUNCTION_TOL:
            continue
        if abs(t - b["EXTENT"][0]) <= JUNCTION_TOL:
            caps.append(("START", q.object_id))
        elif abs(t - b["EXTENT"][1]) <= JUNCTION_TOL:
            caps.append(("END", q.object_id))
    return caps


def _material_fill(b, hatch, caps):
    """Material evidence inside the band: hatch strokes inside the strip, or end faces (caps) drawn across the two faces.

    A void between two elements has neither; a drawn element normally has at least one."""
    ivs = []
    half = b["THK"] / 2 - 5
    for q in hatch:
        t1, d1 = band_param(b, q.x1, q.y1); t2, d2 = band_param(b, q.x2, q.y2)
        if abs(d1) <= half and abs(d2) <= half:
            lo, hi = min(t1, t2), max(t1, t2)
            ivs.extend((max(lo, a), min(hi, c)) for a, c in b["COVER"] if min(hi, c) - max(lo, a) > 0)
    share = _covered(ivs) / max(b["COVERED"], 1e-9) if ivs else 0.0
    both_ends = {c[0] for c in caps} == {"START", "END"}
    evidenced = share >= HATCH_FILL_SHARE or both_ends          # PA07R1: one return is not fill evidence; both ends or hatch
    return {"HATCH_STROKES": len(ivs), "HATCH_FILLED_MM": round(_covered(ivs), 1), "HATCH_SHARE": round(share, 3), "END_CAPS": len(caps), "END_CAPS_BOTH": both_ends, "FILL": "EVIDENCED" if evidenced else "UNEVIDENCED"}


def _loop_evidence(b, segs):
    """PA07R1: hatch inside the loop strip, or a cross / diagonal drawn inside it (the structural column convention)."""
    if b["EVIDENCE"]["MATERIAL_FILL"]["HATCH_SHARE"] >= HATCH_FILL_SHARE:
        return True
    side = min(b["LENGTH"], b["THK"])
    for q in segs:
        if q.object_id in b["FACES"] or _len(q) < 0.5 * side:
            continue
        if in_strip(b, q.x1, q.y1, tol=0.0) and in_strip(b, q.x2, q.y2, tol=0.0) and abs(((_angle(q) - b["ANGLE"]) % (math.pi / 2))) > 5 * ANGLE_TOL and abs(((_angle(q) - b["ANGLE"]) % (math.pi / 2)) - math.pi / 2) > 5 * ANGLE_TOL:
            b["EVIDENCE"]["LOOP_CROSS"] = q.object_id
            return True
    return False


def _on_view_edge(p, bbox):
    if not bbox or p.kind != "SEGMENT":
        return False
    x0, y0, x1, y1 = bbox
    for v in (x0, x1):
        if abs(p.x1 - v) <= EDGE_TOL and abs(p.x2 - v) <= EDGE_TOL:
            return True
    for v in (y0, y1):
        if abs(p.y1 - v) <= EDGE_TOL and abs(p.y2 - v) <= EDGE_TOL:
            return True
    return False


def _interior_faces(b, cands_by_dir, arcs):
    """Parallel candidate faces strictly between the two faces of the band, with their coverage of the band's material intervals."""
    enclosed, doubling = [], []
    if b["KIND"] == "S":
        nx, ny = b["NORMAL"]; ux, uy = b["U"]
        lo_off = max(v[0] for v in b["SIDE_A"].values()) if b["SIDE_A"] else b["AXIS"] - b["THK"] / 2
        hi_off = min(v[0] for v in b["SIDE_B"].values()) if b["SIDE_B"] else b["AXIS"] + b["THK"] / 2
        for q in cands_by_dir.get(_dir_key(b["ANGLE"]), []):
            if q.object_id in b["FACES"]:
                continue
            off = nx * q.x1 + ny * q.y1
            if not (lo_off + THK_MERGE_MM < off < hi_off - THK_MERGE_MM):
                continue
            qlo, qhi = _proj(q, ux, uy)
            ov = [(max(qlo, lo), min(qhi, hi)) for lo, hi in b["COVER"] if min(qhi, hi) - max(qlo, lo) > 0]
            if not ov:
                continue
            item = {"FACE_ID": q.object_id, "OFFSET_FROM_A_MM": round(off - lo_off, 1), "OFFSET_FROM_B_MM": round(hi_off - off, 1), "OVERLAP_MM": round(_covered(ov), 1), "INTERVALS": ov}
            (doubling if min(off - lo_off, hi_off - off) < WALL_MIN_MM else enclosed).append(item)
    else:
        r_lo = max(v[0] for v in b["SIDE_A"].values()); r_hi = min(v[0] for v in b["SIDE_B"].values())
        for q in arcs:
            if q.object_id in b["FACES"] or math.hypot(q.cx - b["CENTRE"][0], q.cy - b["CENTRE"][1]) > AXIS_MERGE_MM:
                continue
            if not (r_lo + THK_MERGE_MM < q.radius < r_hi - THK_MERGE_MM):
                continue
            s = ((q.start_angle % TWO_PI) - b["THETA0"]) % TWO_PI * b["R_AXIS"]
            qlo, qhi = s, s + _arc_span(q) * b["R_AXIS"]
            ov = [(max(qlo, lo), min(qhi, hi)) for lo, hi in b["COVER"] if min(qhi, hi) - max(qlo, lo) > 0]
            if not ov:
                continue
            item = {"FACE_ID": q.object_id, "OFFSET_FROM_A_MM": round(q.radius - r_lo, 1), "OFFSET_FROM_B_MM": round(r_hi - q.radius, 1), "OVERLAP_MM": round(_covered(ov), 1), "INTERVALS": ov}
            (doubling if min(q.radius - r_lo, r_hi - q.radius) < WALL_MIN_MM else enclosed).append(item)
    return enclosed, doubling


def _strip_inside(b, h):
    """Is band b's strip inside band h's strip and extent (same direction / same centre)?"""
    if b["KIND"] != h["KIND"]:
        return False
    if b["KIND"] == "S":
        if abs(((h["ANGLE"] - b["ANGLE"]) % math.pi)) > 2 * ANGLE_TOL and abs(((h["ANGLE"] - b["ANGLE"]) % math.pi) - math.pi) > 2 * ANGLE_TOL:
            return False
        if abs(h["AXIS"] - b["AXIS"]) + b["THK"] / 2 > h["THK"] / 2 + 10:
            return False
        return b["EXTENT"][0] >= h["EXTENT"][0] - JUNCTION_TOL and b["EXTENT"][1] <= h["EXTENT"][1] + JUNCTION_TOL
    if math.hypot(h["CENTRE"][0] - b["CENTRE"][0], h["CENTRE"][1] - b["CENTRE"][1]) > AXIS_MERGE_MM or abs(h["R_AXIS"] - b["R_AXIS"]) + b["THK"] / 2 > h["THK"] / 2 + 10:
        return False
    return True


def _material_side(b, face_id):
    """+1 when the material lies on the +normal (outer radius) side of the face, -1 otherwise."""
    return +1 if face_id in b["SIDE_A"] else -1


# ------------------------------------------------------------------ build
def build(view_id, prims, roles, storey_id=None, source_id=None, single_line_layers=(), view_bbox=None):
    """PA07_MATERIAL_BAND_REGISTER rows for one view: accepted bands, rejected candidates with reasons, unresolved candidates.

    Returns (rows, bands); `bands` are the working dicts (geometry + evidence) used by the topology layer."""
    cands = candidates(prims, roles)
    segs = [p for p in cands if p.kind == "SEGMENT"]
    arcs = [p for p in cands if p.kind == "ARC"]
    fam_groups = family_groups(segs)
    fam = set().union(*[set(g) for g in fam_groups]) if fam_groups else set()
    hatch = fill_strokes(prims, roles, fam)
    segs = [p for p in segs if p.object_id not in fam]
    cands_by_dir = defaultdict(list)
    for p in segs:
        cands_by_dir[_dir_key(_angle(p))].append(p)
    bands = _split_loops(_straight_bands(_pairs(segs)), segs) + _curved_bands(_arc_pairs(arcs))
    for b in bands:
        b["KEY"] = _fingerprint(b)
        b["LENGTH"] = b["EXTENT"][1] - b["EXTENT"][0]
        b["COVERED"] = _covered(b["COVER"])
        b["BLOCK"] = all(f.provenance.block_path for f in b["FACES"].values())
    bands.sort(key=lambda b: (-b["LENGTH"], b["KEY"]))

    all_face_ids = {f for b in bands for f in b["FACES"] if b["LENGTH"] > COLUMN_SIDE_MAX and _len(b["FACES"][f]) > COLUMN_SIDE_MAX}
    # ---- phase 1: geometric rejections (each candidate judged on its own faces)
    for b in bands:
        ev = b["EVIDENCE"]
        ev["PAIRING"] = {"PAIRS": len(b["PAIRS"]), "FACES": len(b["FACES"]), "THICKNESS_MM": round(b["THK"], 1), "THICKNESS_SPREAD_MM": round(b["THK_SPREAD"], 1), "COVERED_MM": round(b["COVERED"], 1), "EXTENT_MM": round(b["LENGTH"], 1)}
        if b["BLOCK"]:
            ev["BLOCK_ASSEMBLY"] = sorted({"/".join(f.provenance.block_path) for f in b["FACES"].values()})
        caps = _end_caps(b, segs, all_face_ids - set(b["FACES"]))
        ev["END_CAPS"] = caps
        ev["MATERIAL_FILL"] = _material_fill(b, hatch, caps)
        if any(_on_view_edge(f, view_bbox) for f in b["FACES"].values()):
            _set(b, "UNRESOLVED", "VIEW_EXTENT_FACE (outermost line of the view: drawing border or boundary wall; source confirmation required)"); continue
        fam_faces = [i for i in b["FACES"] if i in fam]
        if fam_faces and len(fam_faces) >= max(1, len(b["FACES"]) // 2):
            ev["FAMILY_FACES"] = fam_faces
            _set(b, "REJECTED", "REPETITION_FAMILY (treads / hatch / grid at regular spacing)"); continue
        if b["THK"] < WALL_MIN_MM:
            _set(b, "REJECTED", f"THIN_PAIR_BELOW_WALL_MINIMUM ({round(b['THK'], 1)} mm < {WALL_MIN_MM:.0f} mm: drafting offset, line doubling or frame)"); continue
        enclosed, doubling = _interior_faces(b, cands_by_dir, arcs)
        if doubling:
            ev["FACE_DOUBLING"] = [{k: v for k, v in d.items() if k != "INTERVALS"} for d in doubling]
        if enclosed:
            share = _covered([iv for d in enclosed for iv in d["INTERVALS"]]) / max(b["COVERED"], 1e-9)
            ev["INTERIOR_FACES"] = {"FACES": [{k: v for k, v in d.items() if k != "INTERVALS"} for d in enclosed], "SHARE_OF_BAND": round(share, 3)}
            if share >= ENCLOSURE_SHARE:
                _set(b, "REJECTED", "ENCLOSES_PARALLEL_FACES (other faces run inside the pair: two elements or an element with a fitting, not one solid)"); continue
        if {c[0] for c in caps} == {"START", "END"} and len(b["FACES"]) <= 2 and b["KIND"] == "S":
            ev["INTERSECTION"] = {"CLOSED_LOOP": True, "SIDES_MM": [round(b["LENGTH"], 1), round(b["THK"], 1)]}
            if b["LENGTH"] > COLUMN_SIDE_MAX:
                b["LONG_LOOP"] = True          # a wall pier with returns, or a counter / fitting outline: decided by junctions and conflicts
                if b["BLOCK"]:
                    _set(b, "REJECTED", "CLOSED_FITTING_LOOP (closed outline from a block instance, longer than a column: furniture or fixture)"); continue
            else:
                b["LOOP"] = True
            continue
    # ---- phase 1b: a closed loop is found twice (both orthogonal pairs); keep the longer side as the band
    loops = defaultdict(list)
    for b in bands:
        if b.get("LOOP"):
            loops[frozenset(list(b["FACES"]) + [c[1] for c in b["EVIDENCE"]["END_CAPS"]])].append(b)
    for grp in loops.values():
        grp.sort(key=lambda b: (-b["LENGTH"], b["KEY"]))
        for dup in grp[1:]:
            dup["LOOP"] = False
            _set(dup, "REJECTED", f"DUPLICATE_OF_BAND (the other side pair of closed loop {grp[0]['KEY']})")
    # ---- phase 2: frames inside a thicker candidate's strip (candidate = not rejected in phase 1)
    live = [b for b in bands if b["STATUS"] is None]
    for b in live:
        for h in live:
            if h is b or h["STATUS"] is not None or h["THK"] <= b["THK"] or h.get("LOOP"):
                continue
            if _strip_inside(b, h):
                _set(b, "REJECTED", f"FRAME_WITHIN_HOST_BAND (thinner pair inside the strip of {h['KEY']}: window / glazing frame or finish line)")
                h["EVIDENCE"].setdefault("FRAMES_INSIDE", []).append(sorted(b["FACES"]))
                break
    # ---- phase 3: face-side consistency.  A line is the face of one wall: material on exactly one side,
    # unless both strips carry material evidence (hatch or end faces): a layered wall whose shared line is an interface.
    live = [b for b in bands if b["STATUS"] is None]
    claims = defaultdict(list)
    for b in live:
        for fid in b["FACES"]:
            claims[fid].append(b)
    # a strip whose every face is also the face of another candidate with material on the far side is the space
    # between elements (corridor, shaft, duct, void), never a wall: the nested-rectangle convention of plan drafting
    for b in live:
        if b.get("LOOP") or b["STATUS"] is not None:
            continue
        borrowed = []
        for fid in b["FACES"]:
            others = [o for o in claims[fid] if o is not b and o["STATUS"] is None and not o.get("LOOP") and _material_side(o, fid) != _material_side(b, fid) and _overlap(b, o, fid)]
            borrowed.append(bool(others))
        if borrowed and all(borrowed) and b["SIDE_A"] and b["SIDE_B"]:
            _set(b, "REJECTED", "BORROWED_FACES_STRIP (both faces belong to neighbouring elements with material on the far side: the space between them, not a wall)")
    live = [b for b in bands if b["STATUS"] is None]
    conflict_edges = defaultdict(set)
    for fid, bs in claims.items():
        for x, y in itertools.combinations(bs, 2):
            if x["STATUS"] is not None or y["STATUS"] is not None:
                continue
            if _material_side(x, fid) == _material_side(y, fid) or not _overlap(x, y, fid):
                continue
            if x.get("LOOP") or y.get("LOOP"):
                for z, o in ((x, y), (y, x)):
                    z["EVIDENCE"].setdefault("COLUMN_INTERFACE", []).append({"FACE_ID": fid, "WITH_BAND": o["KEY"]})
                continue
            if x.get("LONG_LOOP") or y.get("LONG_LOOP"):
                for z, o in ((x, y), (y, x)):
                    if z.get("LONG_LOOP") and z["STATUS"] is None:
                        _set(z, "UNRESOLVED", f"CLOSED_OUTLINE_AGAINST_WALL (closed outline sharing face {fid} with band {o['KEY']}: counter, fitting or lining drawn on a wall face)")
                continue
            fx, fy = x["EVIDENCE"]["MATERIAL_FILL"]["FILL"], y["EVIDENCE"]["MATERIAL_FILL"]["FILL"]
            if fx == "EVIDENCED" and fy == "EVIDENCED":
                for z, o in ((x, y), (y, x)):
                    z["EVIDENCE"].setdefault("LAYERED_INTERFACE", []).append({"FACE_ID": fid, "WITH_BAND": o["KEY"]})
                continue
            if fx != fy:
                loser = x if fx == "UNEVIDENCED" else y
                winner = y if loser is x else x
                _set(loser, "UNRESOLVED", f"VOID_BESIDE_EVIDENCED_ELEMENT (shares face {fid} with band {winner['KEY']} on the other side, which has fill or end-face evidence; this strip has none)")
                winner["EVIDENCE"].setdefault("VOID_NEIGHBOURS", []).append(loser["KEY"])
                continue
            conflict_edges[id(x)].add(id(y)); conflict_edges[id(y)].add(id(x))
    by_id = {id(b): b for b in live}
    for bid, others in conflict_edges.items():
        b = by_id[bid]
        if b["STATUS"] is not None:
            continue
        b["EVIDENCE"]["FACE_SIDE_CONFLICT"] = {"CONFLICTING_BANDS": [by_id[i]["KEY"] for i in others]}
        _set(b, "UNRESOLVED", "FACE_SIDE_CONFLICT (a face claimed with material on both sides and no fill or end-face evidence on either strip; treads, ducts, two elements or a void cannot be told apart)")
    # ---- phase 4: same-side duplicates (face doubling alternatives): keep the band that encloses the other's inner line
    live = [b for b in bands if b["STATUS"] is None]
    for b in live:
        if b["STATUS"] is not None:
            continue
        for h in live:
            if h is b or h["STATUS"] is not None or h["KIND"] != b["KIND"]:
                continue
            shared = [f for f in b["FACES"] if f in h["FACES"] and _material_side(b, f) == _material_side(h, f) and _overlap(b, h, f)]
            if shared and h["THK"] > b["THK"] and h["EVIDENCE"].get("FACE_DOUBLING"):
                _set(b, "REJECTED", f"DUPLICATE_OF_BAND (same face, same material side as {h['KEY']}: the inner line is recorded there as FACE_DOUBLING)")
                h["EVIDENCE"]["THICKNESS_ALTERNATIVES_MM"] = sorted(set(h["EVIDENCE"].get("THICKNESS_ALTERNATIVES_MM", [round(h["THK"], 1)]) + [round(b["THK"], 1)]))
                break
    # ---- phase 5: anchoring fixpoint.  Long bands joined to other long non-rejected bands seed; anything joined to an accepted band follows.
    live = [b for b in bands if b["STATUS"] is None]
    physical = [b for b in bands if b["STATUS"] != "REJECTED"]
    for b in live:
        b["JOINS_ALL"] = _joins(b, physical)
    phys_by_key = {b["KEY"]: b for b in physical}
    # connected structures over the junction graph: a component with enough developed length and at least one band of
    # free-band length is a wall structure; symbol groups (short pairs joining short pairs) never reach the threshold
    comp_of, comps = {}, []
    for b in live:
        if id(b) in comp_of or b.get("LOOP"):
            continue
        comp, stack = [], [b]
        while stack:
            z = stack.pop()
            if id(z) in comp_of or z.get("LOOP"):
                continue
            comp_of[id(z)] = len(comps); comp.append(z)
            for j in z.get("JOINS_ALL", []):
                h = phys_by_key.get(j["BAND"])
                if h is not None and h["STATUS"] is None and id(h) not in comp_of:
                    stack.append(h)
        comps.append(comp)
    accepted = set()
    for comp in comps:
        total = sum(z["LENGTH"] for z in comp)
        if len(comp) >= 2 and total >= STRUCTURE_MIN_MM and any(z["LENGTH"] >= MIN_FREE_BAND_MM for z in comp):
            accepted.update(id(z) for z in comp)
    for b in live:
        if b.get("LOOP") and b["LENGTH"] <= COLUMN_FREE_MAX and b["THK"] <= COLUMN_FREE_MAX and not b["BLOCK"] and _loop_evidence(b, segs):
            accepted.add(id(b))       # PA07R1: a free-standing closed rectangle is a column only with hatch or a cross inside it
    for b in live:
        if b.get("LONG_LOOP") and id(b) in accepted and b["THK"] > JOINERY_DEPTH_MIN_MM and b["EVIDENCE"]["MATERIAL_FILL"]["HATCH_SHARE"] < HATCH_FILL_SHARE:
            accepted.discard(id(b))   # PA07R1: a closed outline deeper than a partition, joined only by its ends and unhatched, is joinery until confirmed
            b["R1_LONG_LOOP_UNCONFIRMED"] = True
    # column-sized loops up to COLUMN_SIDE_MAX follow the structure they are joined to
    changed = True
    while changed:
        changed = False
        for b in live:
            if id(b) in accepted or not b.get("LOOP") or b["LENGTH"] > COLUMN_SIDE_MAX or b["THK"] > COLUMN_SIDE_MAX:
                continue
            if any(id(phys_by_key[j["BAND"]]) in accepted for j in b["JOINS_ALL"] if j["BAND"] in phys_by_key):
                accepted.add(id(b)); changed = True
    for b in live:
        b["EVIDENCE"]["INTERSECTION"] = dict(b["EVIDENCE"].get("INTERSECTION", {}), JOINS=[{k: v for k, v in j.items()} for j in b["JOINS_ALL"]])
        b["EVIDENCE"]["CONTINUITY"] = {"EXTENT_MM": round(b["LENGTH"], 1), "COVERED_MM": round(b["COVERED"], 1), "GAPS_MM": [round(b["COVER"][i + 1][0] - b["COVER"][i][1], 1) for i in range(len(b["COVER"]) - 1)]}
        if id(b) in accepted:
            if b.get("LOOP"):
                _set(b, "ACCEPTED", None); b["BAND_TYPE"] = "COLUMN_BAND"; b["ORIENTATION"] = "COLUMN"
            else:
                _set(b, "ACCEPTED", None); b["BAND_TYPE"] = "CURVED_BAND" if b["KIND"] == "C" else ("ANGLED_BAND" if b["ORIENTATION"] == "ANGLED" else "STRAIGHT_BAND")
        elif b.get("LOOP"):
            _set(b, "UNRESOLVED", "CLOSED_LOOP_UNRESOLVED (column-sized outline from a block or beyond the free-standing column limit, joined to no wall band)" if b["BLOCK"] or b["LENGTH"] > COLUMN_FREE_MAX
                 else "CLOSED_LOOP_UNRESOLVED (column-sized outline joined to no wall band, with no hatch or cross inside: trap, appliance or tile, not a column)")
        elif b.get("R1_LONG_LOOP_UNCONFIRMED"):
            _set(b, "UNRESOLVED", "CLOSED_OUTLINE_UNCONFIRMED (closed outline of fitting length joined only by its own ends, no hatch inside: wardrobe, counter, bath or a wall pier; owner confirmation or fill required)")
        else:
            _set(b, "UNRESOLVED", "ISOLATED_PAIR (joined to no established band: decorative, furniture, symbol or an unanchored wall fragment)")
    for b in bands:
        if b["BAND_TYPE"] is None:
            b["BAND_TYPE"] = "UNRESOLVED_BAND"
        b["BAND_ID"] = ids.make_id("WALL_FACE", "BAND7", view_id, b["KIND"], b["KEY"], tol=10.0).replace("WF-", "MB-")
    rows = [_row(b, view_id, storey_id, source_id, roles) for b in bands]
    by_oid = {p.object_id: p for p in cands}
    for g in fam_groups:
        members = [by_oid[i] for i in g]
        lengths = sorted(_len(p) for p in members)
        rows.append({"BAND_ID": ids.make_id("WALL_FACE", "BAND7", view_id, "F", sorted(g), tol=10.0).replace("WF-", "MB-"), "SOURCE_ID": source_id, "STOREY_ID": storey_id, "VIEW_ID": view_id,
                     "FACE_A_ID": g[0], "FACE_B_ID": g[1], "SIDE_A_FACE_IDS": sorted(g), "SIDE_B_FACE_IDS": [], "CENTERLINE_IF_DERIVED": None, "THICKNESS_MM": None, "THICKNESS_STATUS": "NOT_ESTABLISHED",
                     "DEVELOPED_LENGTH_MM": round(lengths[len(lengths) // 2], 1), "COVERED_LENGTH_MM": None, "ORIENTATION_TYPE": "FAMILY", "CURVATURE_TYPE": "STRAIGHT",
                     "ROLE_A": roles.get(g[0], {}).get("ROLE"), "ROLE_B": roles.get(g[1], {}).get("ROLE"), "PAIRING_EVIDENCE": {"FAMILY_MEMBERS": len(g)}, "CONTINUITY_EVIDENCE": None, "INTERSECTION_EVIDENCE": None,
                     "FACE_POSITION_STATUS": "NOT_ESTABLISHED", "BAND_TYPE": "UNRESOLVED_BAND", "MATERIAL_STATUS": "REJECTED",
                     "REJECTION_REASON": f"REPETITION_FAMILY ({len(g)} parallel lines of comparable length at regular spacing: treads, hatch, grid, louvres)",
                     "LAYERS": sorted({p.provenance.layer for p in members}), "PROVENANCE": {"RULE": "regular repetition families are never material; recorded so the rejection is visible"}})
    # ---- explicitly accepted one-face construction types (project configuration only)
    used = {f for b in bands for f in b["FACES"]}
    for p in segs:
        if p.provenance.layer in single_line_layers and _len(p) >= 500 and p.object_id not in used:
            rows.append({"BAND_ID": ids.make_id("WALL_FACE", "BAND7", view_id, "1", [p.x1, p.y1, p.x2, p.y2], tol=10.0).replace("WF-", "MB-"), "SOURCE_ID": source_id, "STOREY_ID": storey_id, "VIEW_ID": view_id,
                         "FACE_A_ID": p.object_id, "FACE_B_ID": None, "SIDE_A_FACE_IDS": [p.object_id], "SIDE_B_FACE_IDS": [], "CENTERLINE_IF_DERIVED": {"KIND": "LINE", "SINGLE_LINE": True}, "THICKNESS_MM": None, "THICKNESS_STATUS": "NOT_ESTABLISHED",
                         "DEVELOPED_LENGTH_MM": round(_len(p), 1), "COVERED_LENGTH_MM": round(_len(p), 1), "ORIENTATION_TYPE": "SINGLE_LINE", "CURVATURE_TYPE": "STRAIGHT", "ROLE_A": roles.get(p.object_id, {}).get("ROLE"), "ROLE_B": None,
                         "PAIRING_EVIDENCE": None, "CONTINUITY_EVIDENCE": None, "INTERSECTION_EVIDENCE": None, "FACE_POSITION_STATUS": "ESTABLISHED", "BAND_TYPE": "STRAIGHT_BAND", "MATERIAL_STATUS": "ACCEPTED",
                         "REJECTION_REASON": None, "LAYERS": [p.provenance.layer], "PROVENANCE": {"RULE": "explicitly accepted one-face construction type (project configuration SINGLE_LINE_WALL_LAYERS)"}})
    return rows, bands


def _set(b, status, reason):
    b["STATUS"], b["REASON"] = status, reason


def _overlap(x, y, fid):
    """Do bands x and y both use face fid over a common stretch?"""
    ix, iy = x["SIDE_A"].get(fid) or x["SIDE_B"].get(fid), y["SIDE_A"].get(fid) or y["SIDE_B"].get(fid)
    cx = [(max(lo, ix[1][0]), min(hi, ix[1][1])) for lo, hi in x["COVER"] if min(hi, ix[1][1]) - max(lo, ix[1][0]) > 0]
    cy = [(max(lo, iy[1][0]), min(hi, iy[1][1])) for lo, hi in y["COVER"] if min(hi, iy[1][1]) - max(lo, iy[1][0]) > 0]
    if x["KIND"] != y["KIND"]:
        return True
    if x["KIND"] == "S":
        # both bands share direction (they share a face); compare along that direction
        return any(min(h1, h2) - max(l1, l2) > 0 for l1, h1 in cx for l2, h2 in cy)
    return True


def _fingerprint(b):
    if b["KIND"] == "S":
        return f"S:{round(math.degrees(b['ANGLE']), 2)}:{round(b['AXIS'] / 10)}:{round(b['EXTENT'][0] / 10)}:{round(b['EXTENT'][1] / 10)}:{round(b['THK'] / 5)}"
    return f"C:{round(b['CENTRE'][0] / 10)}:{round(b['CENTRE'][1] / 10)}:{round(b['R_AXIS'] / 10)}:{round(b['EXTENT'][0] / 10)}:{round(b['THK'] / 5)}"


def _row(b, view_id, storey_id, source_id, roles):
    a_id, b_id = b["PAIRS"][0][0], b["PAIRS"][0][1]
    if b["KIND"] == "S":
        centre = {"KIND": "LINE", "AXIS_OFFSET_MM": round(b["AXIS"], 1), "ANGLE_DEG": round(math.degrees(b["ANGLE"]), 3), "EXTENT_MM": [round(b["EXTENT"][0], 1), round(b["EXTENT"][1], 1)], "U": [round(b["U"][0], 6), round(b["U"][1], 6)]}
    else:
        centre = {"KIND": "ARC", "CENTRE_MM": [round(b["CENTRE"][0], 1), round(b["CENTRE"][1], 1)], "R_AXIS_MM": round(b["R_AXIS"], 1), "THETA0_RAD": round(b["THETA0"], 6), "EXTENT_MM": [round(b["EXTENT"][0], 1), round(b["EXTENT"][1], 1)]}
    ev = b["EVIDENCE"]
    thk_status = "ESTABLISHED"
    if ev.get("THICKNESS_ALTERNATIVES_MM") or ev.get("FACE_DOUBLING"):
        thk_status = "AMBIGUOUS_FACE_DOUBLING"
    if b["STATUS"] != "ACCEPTED":
        thk_status = "NOT_ESTABLISHED"
    return {"BAND_ID": b["BAND_ID"], "SOURCE_ID": source_id, "STOREY_ID": storey_id, "VIEW_ID": view_id, "FACE_A_ID": a_id, "FACE_B_ID": b_id,
            "SIDE_A_FACE_IDS": sorted(b["SIDE_A"]), "SIDE_B_FACE_IDS": sorted(b["SIDE_B"]), "CENTERLINE_IF_DERIVED": centre,
            "THICKNESS_MM": round(b["THK"], 1), "THICKNESS_STATUS": thk_status, "DEVELOPED_LENGTH_MM": round(b["LENGTH"], 1), "COVERED_LENGTH_MM": round(b["COVERED"], 1),
            "ORIENTATION_TYPE": b["ORIENTATION"], "CURVATURE_TYPE": "ARC" if b["KIND"] == "C" else "STRAIGHT",
            "ROLE_A": roles.get(a_id, {}).get("ROLE"), "ROLE_B": roles.get(b_id, {}).get("ROLE"),
            "PAIRING_EVIDENCE": ev.get("PAIRING"), "CONTINUITY_EVIDENCE": ev.get("CONTINUITY"), "INTERSECTION_EVIDENCE": ev.get("INTERSECTION"),
            "END_CAPS": ev.get("END_CAPS"), "FRAMES_INSIDE": ev.get("FRAMES_INSIDE"), "FACE_DOUBLING": ev.get("FACE_DOUBLING"), "INTERIOR_FACES": ev.get("INTERIOR_FACES"),
            "FACE_SIDE_CONFLICT": ev.get("FACE_SIDE_CONFLICT"), "MATERIAL_FILL": ev.get("MATERIAL_FILL"), "LAYERED_INTERFACE": ev.get("LAYERED_INTERFACE"), "VOID_NEIGHBOURS": ev.get("VOID_NEIGHBOURS"), "BLOCK_ASSEMBLY": ev.get("BLOCK_ASSEMBLY"), "FAMILY_FACES": ev.get("FAMILY_FACES"),
            "FACE_POSITION_STATUS": "AMBIGUOUS_FACE_DOUBLING" if ev.get("FACE_DOUBLING") else "ESTABLISHED",
            "BAND_TYPE": b["BAND_TYPE"], "MATERIAL_STATUS": b["STATUS"], "REJECTION_REASON": b["REASON"], "LAYERS": sorted({f.provenance.layer for f in b["FACES"].values()}),
            "PROVENANCE": {"RULE": "material by paired geometry, interior-face, repetition, loop, host-strip, face-side and anchoring evidence; layer names are recorded, never decisive"}}


def summarise(rows):
    out = {"ACCEPTED": 0, "REJECTED": 0, "UNRESOLVED": 0, "BY_TYPE": defaultdict(int), "REJECTED_BY_REASON": defaultdict(int), "UNRESOLVED_BY_REASON": defaultdict(int),
           "ACCEPTED_DEVELOPED_M": {"STRAIGHT": 0.0, "CURVED": 0.0, "COLUMN": 0.0}, "ACCEPTED_WITH_FACE_DOUBLING": 0}
    for r in rows:
        out[r["MATERIAL_STATUS"]] += 1
        out["BY_TYPE"][r["BAND_TYPE"]] += 1
        reason = (r["REJECTION_REASON"] or "").split(" (")[0]
        if r["MATERIAL_STATUS"] == "REJECTED":
            out["REJECTED_BY_REASON"][reason] += 1
        elif r["MATERIAL_STATUS"] == "UNRESOLVED":
            out["UNRESOLVED_BY_REASON"][reason] += 1
        elif r["MATERIAL_STATUS"] == "ACCEPTED":
            k = "CURVED" if r["CURVATURE_TYPE"] == "ARC" else ("COLUMN" if r["BAND_TYPE"] == "COLUMN_BAND" else "STRAIGHT")
            out["ACCEPTED_DEVELOPED_M"][k] = round(out["ACCEPTED_DEVELOPED_M"][k] + r["DEVELOPED_LENGTH_MM"] / 1000, 3)
            if r.get("FACE_POSITION_STATUS") != "ESTABLISHED":
                out["ACCEPTED_WITH_FACE_DOUBLING"] += 1
    out["BY_TYPE"] = dict(out["BY_TYPE"]); out["REJECTED_BY_REASON"] = dict(out["REJECTED_BY_REASON"]); out["UNRESOLVED_BY_REASON"] = dict(out["UNRESOLVED_BY_REASON"])
    return out
