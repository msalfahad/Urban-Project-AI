"""WALL BANDS, WALL ENDS AND OPEN PASSAGES (R8.11) - topology-obstacle geometry from structure, never from size.

A WALL BAND is TOPOLOGY_OBSTACLE_GEOMETRY: two admitted straight boundary faces that are the two faces of one
physical obstacle. It is NOT a masonry / material claim. It is established from structure only:

  PARALLEL            the faces' directions agree to within eps_r over their overlap (no angular threshold)
  OVERLAP             their projections overlap by more than eps_r
  SEPARATED           their distance exceeds eps_r (a duplicate line is not a band)
  ELONGATED           the overlap exceeds the separation (shape, not size: two jamb caps across a door are not a
                      band)
  MUTUAL NEAREST      across the strip, each is the other's nearest overlapping facing face: no third admitted
                      face lies nearer on that side over the overlap (a corridor's walls pair with their own
                      partner faces, never with each other), and a face pairs on ONE side only (its nearer one)
  EMPTY STRIP         no established label inside the strip; no admitted boundary crosses the strip's interior; no
                      other parallel admitted line inside it (a centreline makes the band AMBIGUOUS)
  WALL ROLES          both faces are TOPOLOGY_BOUNDARY (glazing, furniture, dimension graphics never form a band);
                      neither is self-dimensioned (role_authority.self_dimension_text)

No thickness, no area, no nearest-pair-alone rule. Identity: a digest of revision + region + the two face source
ids (sorted) - stable across input ordering and traceable to the physical sources.

WALL ENDS. At each end of the overlap the band is
  ALIGNED_FREE_END    both faces END there (their end points agree to within eps_r along the band)
  CAPPED              an admitted boundary already joins the two end points
  (otherwise)         a junction / continuation: not a wall end
A drawn segment of ANY role except a door / window symbol (a DIM line included) lying across an aligned end is CAP
CORROBORATION, graded
  WALL_END_CAP_PROVEN     both its end points coincide (<= eps_r) with the two face end points
  WALL_END_CAP_CANDIDATE  it spans the end within the near-miss REVIEW band (role_authority) but not exactly
The derived closure of an open aligned end is the segment between the two FACE END POINTS (source coordinates of
the faces, never of the cap): see topology_closures.

OPEN PASSAGES. A band end (aligned, capped or closed) facing, along the band, the first admitted segment that
spans the band width across an empty strip is an OPEN PASSAGE: a physical strip through the wall line with no door
in it. It stays physically connected; it is a separate trade object (OPEN_PASSAGE_SITE), like a door threshold.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field

from . import geometry_role as GR
from . import role_authority as RA

POLICY_ID = "WALL_BAND_POLICY_V1"
ESTABLISHED = "WALL_BAND_ESTABLISHED"
AMBIGUOUS = "WALL_BAND_AMBIGUOUS"
ALIGNED_FREE_END = "ALIGNED_FREE_END"
CAPPED = "CAPPED"
CAP_PROVEN = "WALL_END_CAP_PROVEN"
CAP_CANDIDATE = "WALL_END_CAP_CANDIDATE"
NOT_WALL_CAP = "NOT_WALL_CAP"
CAP_UNRESOLVED = "UNRESOLVED"
OPEN_PASSAGE = "OPEN_PASSAGE_SITE"


def _digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


class _Seg:
    __slots__ = ("item", "a", "b", "L", "u", "n")

    def __init__(self, item):
        x1, y1, x2, y2 = item.geometry
        self.item, self.a, self.b = item, (x1, y1), (x2, y2)
        self.L = math.hypot(x2 - x1, y2 - y1)
        self.u = ((x2 - x1) / self.L, (y2 - y1) / self.L) if self.L else (1.0, 0.0)
        self.n = (-self.u[1], self.u[0])

    def st(self, p):
        dx, dy = p[0] - self.a[0], p[1] - self.a[1]
        return dx * self.u[0] + dy * self.u[1], dx * self.n[0] + dy * self.n[1]

    def at(self, s, t=0.0):
        return (self.a[0] + s * self.u[0] + t * self.n[0], self.a[1] + s * self.u[1] + t * self.n[1])


@dataclass
class WallBand:
    band_id: str
    face_a: str
    face_b: str
    width: float
    interval: tuple                 # overlap (s0, s1) in face A's frame
    state: str
    evidence: dict = field(default_factory=dict)
    ends: list = field(default_factory=list)


def _crosses_open_rect(seg, frame, s0, s1, t0, t1):
    """Does straight segment `seg` (world coords) enter the OPEN rectangle (s0, s1) x (t0, t1) of `frame`?"""
    (sa, ta), (sb, tb) = frame.st(seg[0]), frame.st(seg[1])
    u0, u1 = 0.0, 1.0
    ds, dt = sb - sa, tb - ta
    for p, q in ((-ds, sa - s0), (ds, s1 - sa), (-dt, ta - t0), (dt, t1 - ta)):
        if p == 0.0:
            if q <= 0.0:
                return False
            continue
        r = q / p
        if p < 0:
            u0 = max(u0, r)
        else:
            u1 = min(u1, r)
        if u0 >= u1:
            return False
    return u1 - u0 > 1e-12


def _pt_in_open_rect(p, frame, s0, s1, t0, t1):
    s, t = frame.st(p)
    return s0 < s < s1 and t0 < t < t1


def detect(items, *, eps_r, band_review, revision_id, region_id, labels=(), texts=(), unit_native_to_mm=None,
           cap_pool=(), extra_targets=()) -> dict:
    """{bands, ends, passages} for the admitted boundary `items` (BoundaryItem). `cap_pool`: every other straight
    visible linework [(BoundaryItem, role)] that may corroborate a cap (any role). `extra_targets`: further
    admitted segments (door / glazing closures) a passage ray may stop at."""
    faces = [_Seg(it) for it in items if it.kind == "SEGMENT" and it.role == GR.TOPOLOGY_BOUNDARY
             and not it.source_id.startswith(("CLOSURE|", "GLAZED|", "TCLOSURE|"))]
    faces = [f for f in faces if f.L > eps_r]
    selfdim = {f.item.source_id for f in faces if RA.self_dimension_text(f.item, texts, unit_native_to_mm)}
    allsegs = [_Seg(it) for it in list(items) + list(extra_targets) if it.kind == "SEGMENT"]
    arcs = [it for it in items if it.kind != "SEGMENT"]
    lab_pts = [(lt.x, lt.y) for lt in labels]

    # ------------------------------------------------ candidate partners per face side (direction buckets)
    def ang(f):
        a = math.atan2(f.u[1], f.u[0]) % math.pi
        return a if a < math.pi - 1e-9 else 0.0
    buckets = defaultdict(list)
    for f in faces:
        buckets[round(ang(f) / 2e-3)].append(f)
    nbr = defaultdict(list)                      # face id -> [(side, d, other, (s0, s1))]
    for k, fs in buckets.items():
        pool = fs + buckets.get(k - 1, []) + buckets.get(k + 1, [])
        last = round(math.pi / 2e-3)
        if k == 0:
            pool += buckets.get(last, []) + buckets.get(last - 1, [])
        for a in fs:
            for b in pool:
                if b is a:
                    continue
                (s0, t0), (s1, t1) = a.st(b.a), a.st(b.b)
                lo, hi = max(0.0, min(s0, s1)), min(a.L, max(s0, s1))
                if hi - lo <= eps_r:
                    continue
                cross = abs(a.u[0] * b.u[1] - a.u[1] * b.u[0])
                if cross * (hi - lo) > eps_r:                       # not parallel over the overlap
                    continue
                d = (t0 + t1) / 2.0
                if abs(d) <= eps_r:                                  # duplicate / collinear
                    continue
                nbr[a.item.source_id].append((1 if d > 0 else -1, abs(d), b, (lo, hi)))
    byid = {f.item.source_id: f for f in faces}

    def nearest(fid, side, interval):
        best = None
        for sd, d, b, iv in nbr.get(fid, []):
            if sd != side or iv[1] <= interval[0] + eps_r or iv[0] >= interval[1] - eps_r:
                continue
            if best is None or (d, b.item.source_id) < (best[0], best[1].item.source_id):
                best = (d, b)
        return best

    bands, seen = [], set()
    for fid in sorted(byid):
        a = byid[fid]
        sides = sorted({sd for sd, *_ in nbr.get(fid, [])})
        for side in sides:
            cand = nearest(fid, side, (0.0, a.L))
            if cand is None:
                continue
            d, b = cand
            key = tuple(sorted((fid, b.item.source_id)))
            if key in seen:
                continue
            (s0, t0), (s1, t1) = a.st(b.a), a.st(b.b)
            iv = (max(0.0, min(s0, s1)), min(a.L, max(s0, s1)))
            bside = 1 if b.st(a.at((iv[0] + iv[1]) / 2))[1] > 0 else -1
            back = nearest(b.item.source_id, bside, (0.0, b.L))
            ev = {"parallel": True, "separation": d, "overlap": iv[1] - iv[0]}
            if back is None or back[1] is not a:
                continue                                              # not mutual nearest
            other_side = [x for x in nbr.get(fid, []) if x[0] != side]
            near_other = min((x[1] for x in other_side), default=None)
            if near_other is not None and near_other < d - eps_r:
                continue                                              # A pairs on its nearer side only
            if iv[1] - iv[0] <= d:
                continue                                              # not elongated: two jamb caps, a column
            seen.add(key)
            tlo, thi = (0.0, d) if side > 0 else (-d, 0.0)
            e = eps_r
            lab_in = [p for p in lab_pts if _pt_in_open_rect(p, a, iv[0] + e, iv[1] - e, tlo + e, thi - e)]
            crossing = sorted(s.item.source_id for s in allsegs if s.item.source_id not in key and
                              _crosses_open_rect((s.a, s.b), a, iv[0] + e, iv[1] - e, tlo + e, thi - e))
            arc_in = [it.source_id for it in arcs if _arc_bbox_hits(it, a, iv, tlo, thi, e)]
            parallel_inside = [c for c in crossing if c in byid and
                               abs(byid[c].u[0] * a.u[1] - byid[c].u[1] * a.u[0]) * byid[c].L <= eps_r]
            ev.update(mutual_nearest=True, labels_inside=len(lab_in), crossing_boundaries=crossing[:12],
                      arcs_in_strip=arc_in[:6], parallel_inside=parallel_inside[:6],
                      self_dimensioned=sorted(set(key) & selfdim))
            if lab_in or (crossing and not parallel_inside) or arc_in or (set(key) & selfdim):
                continue                                              # not a band at all
            state = AMBIGUOUS if parallel_inside else ESTABLISHED
            bid = "WB-" + _digest({"rev": revision_id, "region": region_id, "faces": list(key)})[:16]
            band = WallBand(bid, fid, b.item.source_id, d, iv, state, ev)
            band._geo = (a, b, side)
            bands.append(band)
    # a face that is a band face on BOTH of its sides (a centreline between two faces, a layered wall) makes every
    # band it is in AMBIGUOUS: which pair is the obstacle is not decided by structure
    sides_of = defaultdict(set)
    for bd in bands:
        a, b, side = bd._geo
        sides_of[bd.face_a].add(side)
        sides_of[bd.face_b].add(1 if b.st(a.at((bd.interval[0] + bd.interval[1]) / 2))[1] > 0 else -1)
    for bd in bands:
        if len(sides_of[bd.face_a]) > 1 or len(sides_of[bd.face_b]) > 1:
            bd.state = AMBIGUOUS
            bd.evidence["face_paired_on_both_sides"] = True
    for bd in bands:
        a, b, side = bd._geo
        del bd._geo
        if bd.state == ESTABLISHED:
            bd.ends = _ends(bd, a, b, side, items, cap_pool, eps_r, band_review)
    passages = _passages(bands, byid, allsegs, eps_r, revision_id, region_id, items, extra_targets)
    return {"policy_id": POLICY_ID, "bands": bands, "passages": passages,
            "face_ids_in_bands": sorted({x for bd in bands if bd.state == ESTABLISHED for x in (bd.face_a, bd.face_b)})}


def _arc_bbox_hits(it, frame, iv, tlo, thi, e):
    cx, cy, r = it.geometry[0], it.geometry[1], it.geometry[2]
    pts = [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)]
    st = [frame.st(p) for p in pts]
    s_lo, s_hi = min(p[0] for p in st), max(p[0] for p in st)
    t_lo, t_hi = min(p[1] for p in st), max(p[1] for p in st)
    return s_hi > iv[0] + e and s_lo < iv[1] - e and t_hi > tlo + e and t_lo < thi - e


def _endpoint_at(seg, frame, s_target, eps):
    for p in (seg.a, seg.b):
        if abs(frame.st(p)[0] - s_target) <= eps:
            return p
    return None


def _ends(band, a, b, side, items, cap_pool, eps_r, review):
    out = []
    adm = [_Seg(it) for it in items if it.kind == "SEGMENT" and it.source_id not in (band.face_a, band.face_b)]
    pool = [(_Seg(it), role) for it, role in cap_pool if it.kind == "SEGMENT" and role != GR.OPENING_SYMBOL]
    for k, s_end in enumerate(band.interval):
        pa, pb = _endpoint_at(a, a, s_end, eps_r), _endpoint_at(b, a, s_end, eps_r)
        rec = {"end": k, "s": s_end, "outward": -1 if k == 0 else 1}
        if pa is None or pb is None:
            out.append(dict(rec, kind="JUNCTION_OR_CONTINUATION"))
            continue
        rec.update(face_a_end=pa, face_b_end=pb, kind=ALIGNED_FREE_END)
        capped = [s.item.source_id for s in adm if _on_seg(pa, s, eps_r) and _on_seg(pb, s, eps_r)]
        if capped:
            rec.update(kind=CAPPED, closed_by=capped)
        caps = []
        w = band.width
        for s, role in pool:
            if abs(s.u[0] * a.u[0] + s.u[1] * a.u[1]) * s.L > eps_r:     # not perpendicular
                continue
            (sa, ta), (sb, tb) = a.st(s.a), a.st(s.b)
            if max(abs(sa - s_end), abs(sb - s_end)) > review:
                continue
            tt = sorted((ta * side, tb * side))
            if tt[0] > review or tt[1] < w - review:
                continue
            ga, gb = min(math.dist(s.a, pa), math.dist(s.b, pa)), min(math.dist(s.a, pb), math.dist(s.b, pb))
            exact = ga <= eps_r and gb <= eps_r
            caps.append({"source": s.item.source_id, "role": role, "grade": CAP_PROVEN if exact else CAP_CANDIDATE,
                         "gap_to_face_a_end": ga, "gap_to_face_b_end": gb,
                         "offset_along_band": max(abs(sa - s_end), abs(sb - s_end)),
                         "shortfall_across": max(0.0, tt[0]) + max(0.0, w - tt[1])})
        rec["drawn_caps"] = sorted(caps, key=lambda c: (c["grade"] != CAP_PROVEN, c["source"]))
        out.append(rec)
    return out


def _on_seg(p, s, eps):
    t = ((p[0] - s.a[0]) * s.u[0] + (p[1] - s.a[1]) * s.u[1])
    if t < -eps or t > s.L + eps:
        return False
    q = s.at(max(0.0, min(s.L, t)))
    return math.dist(p, q) <= eps


class _EndSeg(_Seg):
    def __init__(self, sid, p, q):
        from .topology import BoundaryItem
        super().__init__(BoundaryItem(sid, "SEGMENT", (p[0], p[1], q[0], q[1]), "BAND_END"))


def _passages(bands, byid, allsegs, eps_r, revision_id, region_id, items=(), extra_targets=()):
    """Band end -> the first segment along the band (an admitted segment, or another band's END) that spans the band
    width across an empty strip whose long sides are open (no wall, door or glazing closure along them)."""
    out, seen = [], set()
    ends = [_EndSeg(f"BANDEND|{bd.band_id}|{e['end']}", e["face_a_end"], e["face_b_end"])
            for bd in bands if bd.state == ESTABLISHED for e in bd.ends if e["kind"] in (ALIGNED_FREE_END, CAPPED)]
    lines = [_Seg(it) for it in list(items) + list(extra_targets) if it.kind == "SEGMENT"]
    allsegs = list(allsegs) + ends
    for bd in bands:
        if bd.state != ESTABLISHED:
            continue
        a = byid[bd.face_a]
        for end in bd.ends:
            if end["kind"] not in (ALIGNED_FREE_END, CAPPED):
                continue
            pa, pb = end["face_a_end"], end["face_b_end"]
            o = end["outward"]
            ux, uy = a.u[0] * o, a.u[1] * o
            best = None
            for s in allsegs:
                if s.item.source_id in (bd.face_a, bd.face_b) or s.item.source_id in end.get("closed_by", ()) or \
                        s.item.source_id == f"BANDEND|{bd.band_id}|{end['end']}":
                    continue
                if abs(s.u[0] * a.u[0] + s.u[1] * a.u[1]) * s.L > eps_r:      # must cross the band line
                    continue
                hits = []
                for p in (pa, pb):
                    h = _ray_hit(p, (ux, uy), s, eps_r)
                    if h is None:
                        break
                    hits.append(h)
                if len(hits) == 2 and min(hits) > eps_r and abs(hits[0] - hits[1]) <= eps_r:
                    if best is None or (hits[0], s.item.source_id) < (best[0], best[1]):
                        best = (hits[0], s.item.source_id)
            if best is None:
                continue
            g, target = best
            strip = [pa, pb, (pb[0] + ux * g, pb[1] + uy * g), (pa[0] + ux * g, pa[1] + uy * g)]
            blocked = [s.item.source_id for s in allsegs if s.item.source_id not in (bd.face_a, bd.face_b, target)
                       and _seg_hits_quad(s, strip, eps_r)]
            sides = [s.item.source_id for s in lines if _along(s, strip[0], strip[3], eps_r) or
                     _along(s, strip[1], strip[2], eps_r)]
            if blocked or sides:
                continue                              # a wall, a door / glazing closure: not an open passage
            pid = "OP-" + _digest({"rev": revision_id, "region": region_id, "band": bd.band_id, "end": end["end"],
                                   "target": target})[:16]
            key = (bd.band_id, end["end"])
            if key in seen:
                continue
            seen.add(key)
            out.append({"passage_id": pid, "kind": OPEN_PASSAGE, "band_id": bd.band_id, "band_end": end["end"],
                        "end_kind": end["kind"], "target": target, "width": g, "wall_thickness": bd.width,
                        "area_native": g * bd.width, "polygon": strip,
                        "jamb_faces": [{"band_id": bd.band_id, "segment": [pa, pb]}],
                        "head_condition": "NOT_ESTABLISHED_IN_SOURCE", "physically_connected": True,
                        "trade_allocation": "NOT_ALLOCATED"})
    return _dedupe_collinear(out, eps_r)


def _along(s, p, q, eps):
    """Does segment s lie on the line p-q and overlap the open interval between them by more than eps?"""
    L = math.dist(p, q)
    if L <= eps:
        return False
    ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
    ts = []
    for r in (s.a, s.b):
        dx, dy = r[0] - p[0], r[1] - p[1]
        if abs(-dx * uy + dy * ux) > eps:
            return False
        ts.append(dx * ux + dy * uy)
    lo, hi = max(0.0, min(ts)), min(L, max(ts))
    return hi - lo > eps


def _ray_hit(p, d, s, eps):
    """Distance along ray p + k d to segment s (None when it misses)."""
    ex, ey = s.b[0] - s.a[0], s.b[1] - s.a[1]
    den = d[0] * ey - d[1] * ex
    if abs(den) < 1e-15:
        return None
    wx, wy = s.a[0] - p[0], s.a[1] - p[1]
    k = (wx * ey - wy * ex) / den
    m = (wx * d[1] - wy * d[0]) / den
    if k < -eps or m < -eps / max(s.L, 1e-12) or m > 1 + eps / max(s.L, 1e-12):
        return None
    return k


def _seg_hits_quad(s, quad, eps):
    """Does s enter the open interior of the rectangle `quad` (corners in order)?"""
    (x0, y0), (x1, y1), _, (x3, y3) = quad
    ux, uy = x1 - x0, y1 - y0
    vx, vy = x3 - x0, y3 - y0
    lu, lv = math.hypot(ux, uy), math.hypot(vx, vy)
    if lu <= 0 or lv <= 0:
        return False

    class F:
        @staticmethod
        def st(p):
            dx, dy = p[0] - x0, p[1] - y0
            return (dx * ux + dy * uy) / lu, (dx * vx + dy * vy) / lv
    return _crosses_open_rect((s.a, s.b), F, eps, lu - eps, eps, lv - eps)


def _dedupe_collinear(ps, eps):
    """Two band ends facing each other give the same strip twice: keep one (the lower passage id)."""
    out = []
    for p in sorted(ps, key=lambda z: z["passage_id"]):
        c = sorted((round(x, 6), round(y, 6)) for x, y in p["polygon"])
        if any(all(math.dist(a, b) <= eps for a, b in zip(c, sorted((round(x, 6), round(y, 6))
                                                                       for x, y in q["polygon"]))) for q in out):
            continue
        out.append(p)
    return out


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "band": ["parallel within eps_r over the overlap", "overlap > eps_r",
                                            "separation > eps_r", "elongated: overlap > separation (shape, not size)",
                                            "mutual nearest facing faces; one side only; a face paired on both sides "
                                            "makes its bands AMBIGUOUS",
                                            "empty strip: no label, no crossing boundary, no arc",
                                            "TOPOLOGY_BOUNDARY faces; not self-dimensioned"],
           "never": ["thickness", "area", "nearest parallel pair alone", "coordinates alone", "material identity"],
           "ends": [ALIGNED_FREE_END, CAPPED], "caps": [CAP_PROVEN, CAP_CANDIDATE, NOT_WALL_CAP, CAP_UNRESOLVED],
           "means": "TOPOLOGY_OBSTACLE_GEOMETRY, not MASONRY_CONFIRMED"}
    rec["digest"] = _digest(rec)
    return rec
