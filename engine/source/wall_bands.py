"""WALL BANDS, WALL ENDS AND OPEN PASSAGES - topology-obstacle geometry from structure, never from size.

R8.14 (WALL_BAND_POLICY_V5) = V4 + two hardenings of the R8.13 post-blind observations:
  O2 TIE        elongation is decided against the declared tolerance: a run is elongated only when
                run - elongation_ratio x separation > eps_r; within eps_r of equality it is NOT elongated
                (ELONGATION_BOUNDARY_CASE, fail closed) - never by binary floating-point equality.
  O1 AUTHORITY  band GEOMETRY is not band PHYSICAL AUTHORITY: a band with a face on an ISOLATED CLOSED LOOP (a closed
                single-entity polyline whose segments touch no admitted segment of any other entity) and no positive
                physical authority for that entity is a GEOMETRIC_BAND_CANDIDATE - recorded, but it carries no ends,
                closures, passages or paired-face corroboration. Positive authority: a part-scoped owner role claim on
                the entity (physical_authority). Never by thickness, size or location.

R8.13 (WALL_BAND_POLICY_V4) = V3 + three generic corrections of the two R8.12 post-blind defects:
  D1 IDENTITY   a face chain is identified by its source entities + its SUPPORTING LINE (canonical direction and
                signed offset) + its parameter interval along that line: two parallel sides of one closed polyline with
                the same extent no longer share an id. Band ids are built from the two chain ids. A residual id
                collision is never silent: the chains are recorded and excluded from pairing (fail closed).
  D2 SUPPORT    ASSEMBLY_STRUCTURAL_SUPPORT: elongation is tested on the LOCAL RUN (the contiguous locally mutual
                nearest interval with its spans, overlaps and nodes), not on the raw chain overlap. A run longer than
                elongation_ratio x separation is SELF_SUPPORTED; a shorter run is INHERITED_SUPPORT only when it is
                joined to a self-supported run of the SAME chain pair and side across gaps each filled by a full-width
                closed structural loop (a column through the wall); otherwise it is UNSUPPORTED - a non-authoritative
                pair-run candidate, never a band, a passage source or an ambiguity source.
  PASSAGE       both sides structural: the source is an ESTABLISHED supported band end, the far side a wall face /
                structural obstacle segment or another established band end (never furniture, a dimension, glazing,
                an opening closure or an unresolved-role line).

R8.12 (WALL_BAND_POLICY_V3): FACE CHAINS + LOCAL BAND SPANS + WALL-BAND ASSEMBLIES.

FACE CHAIN (derived, traceable; never a CAD entity, a material wall or a quantity): admitted TOPOLOGY_BOUNDARY
source fragments that are ONE continuous face along one supporting line. Fragments join only when continuity is
positively established: collinear within eps_n, end points coincident within eps_n, the same occurrence path, and no
opening / glazing segment ending at the joint (OPENING_BREAK). A gap of any size - including one inside the 50 mm
review band - is never joined. Collinear fragments that OVERLAP are one chain with a DUPLICATE interval (ambiguous,
never a double wall). Joints and faces ending on the chain are recorded as nodes (CONTINUOUS_JOIN / BRANCH_NODE /
CROSSING_NODE): a T-junction subdivides, it does not end the face. Identity (V4): revision + region + the source
ENTITIES + the SUPPORTING LINE + the chain's extent along its canonical direction (stable under fragment order,
reversed orientation, unrelated insertion and an equivalent re-segmentation of the same entity).

LOCAL BAND SPAN: two parallel chains facing each other are paired INTERVAL BY INTERVAL. Breakpoints are the
projections of every parallel overlapping chain of both chains (both sides); at the middle of each elementary
interval the pair must be LOCALLY mutually nearest (no nearer face on that side, no nearer face on the far side of
either chain, no tie). Geometry outside the interval never disqualifies it. V4: the LOCAL RUN must be structurally
supported (see D2 above); V3 tested the raw overlap of the two chains, which let a pair that is mutually nearest over
a sliver (another wall's core seen crosswise) become a band. The local strip must
hold no label and no arc; crossings SUBDIVIDE it:
  WALL_BAND_SPAN       free obstacle strip
  OBSTACLE_OVERLAP     a crossing passes over the interval, or the strip lies inside a closed admitted loop (a
                       column outline): only that interval is blocked
  CROSSING_WALL_NODE   between two full-width crossings by wall faces (a crossing wall's core)
  ENCLOSED_NODE        between two full-width crossings of other roles
  AMBIGUOUS_*          a centreline, a duplicate fragment, a chain paired on both sides
Every span keeps the exact source-part parameter intervals it uses (never just "source H477").

WALL-BAND ASSEMBLY (the `bands` list, id "WB-"): one local pair run of two chains with its spans, overlaps and
nodes. ESTABLISHED when it holds a span and nothing ambiguous. It is TOPOLOGY_OBSTACLE_GEOMETRY only: no wall
length, thickness authority, masonry, plaster, paint or skirting follows from it.

ENDS (per assembly end): JUNCTION_OR_CONTINUATION (a chain continues past it), RECEIVING_FACE_JUNCTION (A1: the end
line continues beyond both chain end points), OPENING_JAMB (an opening / glazing closure meets the end), CAPPED (an
admitted boundary joins both end points), ALIGNED_FREE_END. A fragmented face that reaches the same end gives the
same end as a one-piece face. A drawn segment of any role except a door / window symbol across an aligned end is CAP
CORROBORATION: WALL_END_CAP_PROVEN (exact) / WALL_END_CAP_CANDIDATE (within the review band). The derived closure of
an open aligned end is the segment between the two chains' END POINTS (source coordinates): topology_closures.

OPEN PASSAGES: a band end facing, along the band, the first segment (or band end) spanning the band width across an
empty strip with open long sides: OPEN_PASSAGE_SITE, physically connected.

Every behaviour-changing constant is in PARAMS and in policy_record(). Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field

from . import geometry_role as GR
from . import role_authority as RA

POLICY_ID = "WALL_BAND_POLICY_V5"      # V5 (R8.14): V4 + tolerance tie + geometric vs physical band authority
ESTABLISHED = "WALL_BAND_ESTABLISHED"
AMBIGUOUS = "WALL_BAND_AMBIGUOUS"
ALIGNED_FREE_END = "ALIGNED_FREE_END"
CAPPED = "CAPPED"
RECEIVING_FACE_JUNCTION = "RECEIVING_FACE_JUNCTION"
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
    return u1 - u0 > PARAMS["numeric_guards"]["clip_parameter"]


def _pt_in_open_rect(p, frame, s0, s1, t0, t1):
    s, t = frame.st(p)
    return s0 < s < s1 and t0 < t < t1


# ---------------------------------------------------------------- R8.12 (V3): every behaviour constant is here
PARAMS = {
    "chain_join": "collinear within eps_n both ways; end points coincident within eps_n (touching); same occurrence "
                  "path; TOPOLOGY_BOUNDARY on both sides; NO opening / glazing segment end within eps_r of the "
                  "joint (OPENING_BREAK). A gap of any size, including inside the 50 mm review band, is never joined",
    "duplicate": "collinear fragments overlapping by more than eps_n are ONE chain with a DUPLICATE interval; a span "
                 "over a duplicate interval is AMBIGUOUS",
    "parallel": "|cross(u_a, u_b)| x overlap <= eps_r",
    "overlap_min": "eps_r", "separation_min": "eps_r",
    "elongation_ratio": 1.0,
    "elongation_basis": "V4: the LOCAL RUN (contiguous locally mutual nearest interval incl. its spans, obstacle "
                        "overlaps and nodes); never the raw chain overlap (V3-D2), never a single span",
    "structural_support": "SELF_SUPPORTED: run length > elongation_ratio x separation. INHERITED_SUPPORT: a shorter run "
                          "of the SAME chain pair and side joined to a self-supported run across gaps each filled by a "
                          "full-width closed loop of a support role (every corner of the gap strip, inset by eps_r, "
                          "inside the loop). Never inherited from a group's total length; an UNSUPPORTED run is "
                          "recorded, never a band",
    "support_loop_roles": ["TOPOLOGY_BOUNDARY", "STRUCTURAL_OBSTACLE"],
    "elongation_tie": "V5: elongated only when length - elongation_ratio x separation > eps_r (raw overlap pre-check and "
                      "local run alike); within eps_r of equality -> NOT elongated (ELONGATION_BOUNDARY_CASE, fail "
                      "closed)",
    "physical_authority": "V5: a band with a face on an ISOLATED CLOSED LOOP (closed single-entity loop touching no "
                          "admitted segment of another entity, within eps_n) is a GEOMETRIC_BAND_CANDIDATE unless that "
                          "entity carries positive physical authority (a part-scoped owner role claim); candidates "
                          "carry no ends, closures, passages or paired-face corroboration",
    "chain_identity": "entities + parameter interval along the canonical direction (V3, kept wherever it is unique "
                      "so a nudged face and an equivalent re-segmentation keep their id); chains of the SAME entities "
                      "and extent (parallel sides of one closed polyline) are told apart by their SUPPORTING LINE "
                      "(canonical direction + signed offset). The sub-part index is provenance only (a "
                      "re-segmentation renumbers it); -0.0 -> 0.0",
    "band_identity": "the two chain ids + the run interval in the frame of the lower chain id",
    "id_collision": "colliding chains are recorded and excluded from pairing (fail closed)",
    "passage_target_roles": ["TOPOLOGY_BOUNDARY", "STRUCTURAL_OBSTACLE", "an ESTABLISHED band end"],
    "local_mutual_nearest": "evaluated at the middle of every elementary interval (breakpoints: projections of all "
                            "parallel overlapping chains of both chains, both sides)",
    "one_side_margin": "eps_r", "nearest_tie": "eps_r (a tie between two chains is never paired)",
    "strip": "a label anywhere in the RAW strip of the chain pair (the whole chain overlap) rejects the pair - local "
             "pairing must never turn an unlabelled slice of a room into a band; labels or arcs in the local strip "
             "reject the run; crossings subdivide it",
    "id_coordinate_decimals": 6, "canonical_direction_guard": 1e-9,
    "eps_n_default_ratio_of_eps_r": 1e-3, "full_width_margin_in_eps_r": 2.0,
    "numeric_guards": {"ray_parallel": 1e-15, "segment_length_floor": 1e-12, "clip_parameter": 1e-12},
    "pair_search": "exhaustive over admitted faces (no direction buckets, no neighbourhood window)",
    "review_band": "role_authority.NEAR_MISS_REVIEW_BAND_MM / unit - cap grading only, never a join"}
ID_DECIMALS = PARAMS["id_coordinate_decimals"]
CANON_GUARD = PARAMS["canonical_direction_guard"]
ELONGATION = PARAMS["elongation_ratio"]

# chain nodes and interval classes
JOIN, BRANCH, CROSSING, OPENING_BREAK, DUPLICATE = ("CONTINUOUS_JOIN", "BRANCH_NODE", "CROSSING_NODE",
                                                     "OPENING_BREAK", "DUPLICATE_OVERLAP")
SPAN = "WALL_BAND_SPAN"
OBSTACLE_OVERLAP = "OBSTACLE_OVERLAP"
CROSSING_WALL_NODE = "CROSSING_WALL_NODE"
ENCLOSED_NODE = "ENCLOSED_NODE"
AMBIGUOUS_CENTRELINE = "AMBIGUOUS_CENTRELINE"
AMBIGUOUS_DUPLICATE = "AMBIGUOUS_DUPLICATE"
AMBIGUOUS_BOTH_SIDES = "AMBIGUOUS_PAIRED_BOTH_SIDES"
OPENING_JAMB = "OPENING_JAMB"
JUNCTION = "JUNCTION_OR_CONTINUATION"
IDENTITY_EXTENT = "ENTITIES_AND_EXTENT"            # V4 chain identity bases
IDENTITY_LINE = "ENTITIES_EXTENT_AND_SUPPORTING_LINE"
GEOMETRIC_CANDIDATE = "WALL_BAND_GEOMETRIC_CANDIDATE"   # V5: geometry without physical authority
PHYSICAL = "PHYSICAL_WALL_BAND_ESTABLISHED"
ISOLATED_CLOSED_LOOP = "ISOLATED_CLOSED_LOOP"
BOUNDARY_CASE = "ELONGATION_BOUNDARY_CASE"
SELF_SUPPORTED = "SELF_SUPPORTED"                     # V4 structural support of a local run
INHERITED_SUPPORT = "INHERITED_SUPPORT"
UNSUPPORTED = "UNSUPPORTED"


class _Axis:
    """A chain's supporting line: s along the canonical direction, t across it (0 on the line)."""
    __slots__ = ("u", "n", "t0")

    def __init__(self, u, t0):
        self.u, self.n, self.t0 = u, (-u[1], u[0]), t0

    def st(self, p):
        return p[0] * self.u[0] + p[1] * self.u[1], p[0] * self.n[0] + p[1] * self.n[1] - self.t0

    def at(self, s, t=0.0):
        tt = t + self.t0
        return (s * self.u[0] + tt * self.n[0], s * self.u[1] + tt * self.n[1])


def _canon(u):
    if u[0] < -CANON_GUARD or (abs(u[0]) <= CANON_GUARD and u[1] < 0):
        return (-u[0], -u[1])
    return u


def _occ(sid):
    p = sid.split("|")
    return p[2] if len(p) > 2 else ""


def _entity(sid):
    return sid.rsplit("|", 1)[0]


def _r(v):
    return round(float(v), ID_DECIMALS) + 0.0          # + 0.0: -0.0 and 0.0 are one id coordinate


@dataclass
class FaceChain:
    """A DERIVED face: source fragments that are one continuous face along one supporting line. Not a CAD entity,
    not a material wall, not a quantity."""
    chain_id: str
    occurrence: str
    fragments: list                 # [{"source", "s": [s0, s1], "low": p, "high": p}] ordered along the chain
    s_range: tuple
    nodes: list = field(default_factory=list)
    duplicate_intervals: list = field(default_factory=list)


def _build_chains(faces, allsegs, openers, eps_n, eps_r, revision_id, region_id):
    n = len(faces)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    dups, breaks = [], []
    for i in range(n):
        a = faces[i]
        for j in range(i + 1, n):
            b = faces[j]
            if _occ(a.item.source_id) != _occ(b.item.source_id):
                continue
            if abs(a.u[0] * b.u[1] - a.u[1] * b.u[0]) * max(a.L, b.L) > eps_n:
                continue
            (sa, ta), (sb, tb) = a.st(b.a), a.st(b.b)
            if max(abs(ta), abs(tb)) > eps_n or max(abs(b.st(a.a)[1]), abs(b.st(a.b)[1])) > eps_n:
                continue
            lo, hi = min(sa, sb), max(sa, sb)
            ov = min(a.L, hi) - max(0.0, lo)
            if ov > eps_n:
                dups.append((i, j))
                parent[find(i)] = find(j)
                continue
            if ov < -eps_n:
                continue                                                    # a gap: never joined
            p = a.b if abs(lo - a.L) <= eps_n else a.a
            if any(min(math.dist(o.a, p), math.dist(o.b, p)) <= eps_r for o in openers):
                breaks.append((i, j, p))
                continue
            parent[find(i)] = find(j)
    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
    chains, member = [], {}
    for idxs in groups.values():
        segs = [faces[i] for i in idxs]
        ref = max(segs, key=lambda f: (f.L, f.item.source_id))
        u = _canon(ref.u)
        ax = _Axis(u, ref.a[0] * -u[1] + ref.a[1] * u[0])
        frs = []
        for f in segs:
            s0, s1 = ax.st(f.a)[0], ax.st(f.b)[0]
            low, high = (f.a, f.b) if s0 <= s1 else (f.b, f.a)
            frs.append({"source": f.item.source_id, "s": [min(s0, s1), max(s0, s1)], "low": low, "high": high,
                        "_seg": f})
        frs.sort(key=lambda z: (z["s"][0], z["source"]))
        srange = (min(z["s"][0] for z in frs), max(z["s"][1] for z in frs))
        ents = sorted({_entity(z["source"]) for z in frs})
        base = {"rev": revision_id, "region": region_id, "entities": ents, "s": [_r(srange[0]), _r(srange[1])]}
        cid = "FC-" + _digest(base)[:16]
        mine = {z["source"] for z in frs}
        nodes = []
        for k in range(len(frs) - 1):                                      # joints between consecutive fragments
            if abs(frs[k]["s"][1] - frs[k + 1]["s"][0]) <= eps_n:
                p = frs[k]["high"]
                kind = JOIN
                for o in allsegs:
                    if o.item.source_id in mine:
                        continue
                    if min(math.dist(o.a, p), math.dist(o.b, p)) <= eps_n:
                        kind = BRANCH
                        break
                    if _on_seg(p, o, eps_n):
                        kind = CROSSING
                nodes.append({"kind": kind, "s": frs[k]["s"][1], "point": [_r(p[0]), _r(p[1])],
                              "between": [frs[k]["source"], frs[k + 1]["source"]]})
        for o in allsegs:                                                    # branches ending on the chain
            if o.item.source_id in mine:
                continue
            for q in (o.a, o.b):
                s, t = ax.st(q)
                if abs(t) <= eps_n and srange[0] + eps_n < s < srange[1] - eps_n and \
                        not any(abs(s - nd["s"]) <= eps_n for nd in nodes):
                    nodes.append({"kind": BRANCH, "s": s, "point": [_r(q[0]), _r(q[1])], "by": o.item.source_id})
        nodes.sort(key=lambda z: z["s"])
        di = []
        for x in range(len(frs)):
            for y in range(x + 1, len(frs)):
                lo, hi = max(frs[x]["s"][0], frs[y]["s"][0]), min(frs[x]["s"][1], frs[y]["s"][1])
                if hi - lo > eps_n:
                    di.append([lo, hi])
        ch = FaceChain(cid, _occ(frs[0]["source"]), frs, srange, nodes, di)
        ch._axis = ax
        ch._ents = ents
        ch._line = dict(base, line={"u": [_r(u[0]), _r(u[1])], "offset": _r(ax.t0)})
        ch.identity_basis = IDENTITY_EXTENT
        chains.append(ch)
        for z in frs:
            member[z["source"]] = ch
    same = defaultdict(list)                         # V4 (D1): chains of the SAME entities + extent are told apart
    for c in chains:                                 # by their supporting line; every other id stays the V3 id
        same[c.chain_id].append(c)
    for cs in same.values():
        if len(cs) > 1:
            for c in cs:
                c.chain_id = "FC-" + _digest(c._line)[:16]
                c.identity_basis = IDENTITY_LINE
    chains.sort(key=lambda c: c.chain_id)
    brk = [{"kind": OPENING_BREAK, "between": sorted([faces[i].item.source_id, faces[j].item.source_id]),
            "point": [_r(p[0]), _r(p[1])]} for i, j, p in breaks]
    return chains, member, brk


def _chain_points(ch, ax):
    """The chain's extreme points projected into another axis."""
    lo = min(ch.fragments, key=lambda z: z["s"][0])["low"]
    hi = max(ch.fragments, key=lambda z: z["s"][1])["high"]
    return ax.st(lo), ax.st(hi), lo, hi


def _clip(seg, ax, s0, s1, t0, t1):
    """(c0, c1, tmin, tmax) of the part of seg inside the open rectangle, in ax coordinates, or None."""
    (sa, ta), (sb, tb) = ax.st(seg.a), ax.st(seg.b)
    u0, u1 = 0.0, 1.0
    ds, dt = sb - sa, tb - ta
    for p, q in ((-ds, sa - s0), (ds, s1 - sa), (-dt, ta - t0), (dt, t1 - ta)):
        if p == 0.0:
            if q <= 0.0:
                return None
            continue
        r = q / p
        if p < 0:
            u0 = max(u0, r)
        else:
            u1 = min(u1, r)
        if u0 >= u1:
            return None
    if u1 - u0 <= PARAMS["numeric_guards"]["clip_parameter"]:
        return None
    sA, sB = sa + u0 * ds, sa + u1 * ds
    tA, tB = ta + u0 * dt, ta + u1 * dt
    return min(sA, sB), max(sA, sB), min(tA, tB), max(tA, tB)


def _closed_loops(allsegs, eps_n):
    """Entities whose straight segments form one closed loop (every end point shared by exactly two segments)."""
    by = defaultdict(list)
    for s in allsegs:
        by[_entity(s.item.source_id)].append(s)
    out = {}
    for ent, ss in by.items():
        if len(ss) < 3:
            continue
        pts = [p for s in ss for p in (s.a, s.b)]
        if all(sum(1 for q in pts if math.dist(p, q) <= eps_n) == 2 for p in pts):
            out[ent] = ss
    return out


def _inside(p, segs):
    x, y = p
    c = False
    for s in segs:
        (x1, y1), (x2, y2) = s.a, s.b
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                c = not c
    return c


def _elongated(length, d, eps_r):
    """V5 tie rule: True / False, or None at the boundary (within eps_r of length == ratio x separation)."""
    m = length - ELONGATION * d
    if m > eps_r:
        return True
    return None if m >= -eps_r else False


def _isolated_loops(loops, items, eps_n):
    """Closed single-entity loops whose segments touch no admitted segment of another entity."""
    adm = [_Seg(it) for it in items if it.kind == "SEGMENT"]
    out = {}
    for ent, ss in sorted(loops.items()):
        mine = {x.item.source_id for x in ss}
        if not mine <= {a.item.source_id for a in adm}:
            continue                                      # not an admitted boundary loop
        touch = False
        for o in adm:
            if o.item.source_id in mine:
                continue
            for x in ss:
                if any(_on_seg(q, x, eps_n) for q in (o.a, o.b)) or any(_on_seg(q, o, eps_n) for q in (x.a, x.b)):
                    touch = True
                    break
            if touch:
                break
        if not touch:
            out[ent] = sorted(mine)
    return out


def detect(items, *, eps_r, band_review, revision_id, region_id, labels=(), texts=(), unit_native_to_mm=None,
           cap_pool=(), extra_targets=(), eps_n=None, physical_authority=()) -> dict:
    """R8.13 (WALL_BAND_POLICY_V4): FACE CHAINS (strict contiguity, supporting-line identity) + LOCAL BAND SPANS
    (local mutual nearest over elementary intervals) + WALL_BAND ASSEMBLIES (contiguous spans / obstacle overlaps /
    nodes of one chain pair) whose LOCAL run is structurally supported. `bands` are the assemblies (they carry ends,
    closures and passages); `spans` and `chains` are their provenance; `unsupported_runs` and `chain_id_collisions`
    are recorded, never used."""
    eps_n = eps_r * PARAMS["eps_n_default_ratio_of_eps_r"] if eps_n is None else eps_n
    faces = [_Seg(it) for it in items if it.kind == "SEGMENT" and it.role == GR.TOPOLOGY_BOUNDARY
             and not it.source_id.startswith(("CLOSURE|", "GLAZED|", "TCLOSURE|"))]
    faces = [f for f in faces if f.L > eps_r]
    selfdim = {f.item.source_id for f in faces if RA.self_dimension_text(f.item, texts, unit_native_to_mm)}
    faces = [f for f in faces if f.item.source_id not in selfdim]
    allsegs = [_Seg(it) for it in list(items) + list(extra_targets) if it.kind == "SEGMENT"]
    allsegs = [s for s in allsegs if s.L > PARAMS["numeric_guards"]["segment_length_floor"]]
    openers = [s for s in allsegs if s.item.source_id.startswith(("CLOSURE|", "GLAZED|")) or
               s.item.role in (GR.GLAZING_BOUNDARY, GR.OPENING_BOUNDARY)]
    arcs = [it for it in items if it.kind != "SEGMENT"]
    lab_pts = [(lt.x, lt.y) for lt in labels]
    chains, member, chain_breaks = _build_chains(faces, allsegs, openers, eps_n, eps_r, revision_id, region_id)
    seen_ids = defaultdict(list)
    for c in chains:
        seen_ids[c.chain_id].append(c)
    collisions = [{"chain_id": cid, "fragments": sorted([z["source"] for z in c.fragments] for c in cs)}
                  for cid, cs in sorted(seen_ids.items()) if len(cs) > 1]
    chains = [c for c in chains if len(seen_ids[c.chain_id]) == 1]          # V4: a collision fails closed
    byc = {c.chain_id: c for c in chains}
    loops = _closed_loops(allsegs, eps_n)
    support_roles = set(PARAMS["support_loop_roles"])
    proven = {_entity(x) for x in physical_authority}
    isolated = {e: v for e, v in _isolated_loops(loops, items, eps_n).items() if e not in proven}

    # ------------------------------------------------ facing candidates per chain, in that chain's own frame
    cand = defaultdict(list)                     # chain id -> [(side, d, other id, lo, hi)]
    def facing(X, Y):
        ax = X._axis
        (s0, t0), (s1, t1), _, _ = _chain_points(Y, ax)
        lo, hi = max(X.s_range[0], min(s0, s1)), min(X.s_range[1], max(s0, s1))
        if hi - lo <= eps_r:
            return None
        if abs(X._axis.u[0] * Y._axis.u[1] - X._axis.u[1] * Y._axis.u[0]) * (hi - lo) > eps_r:
            return None
        mid = (lo + hi) / 2
        t = t0 + (t1 - t0) * ((mid - s0) / (s1 - s0)) if s1 != s0 else t0
        if abs(t) <= eps_r:
            return None
        return (1 if t > 0 else -1, abs(t), Y.chain_id, lo, hi)
    for i, A in enumerate(chains):
        for B in chains[i + 1:]:
            fab, fba = facing(A, B), facing(B, A)
            if fab is not None and fba is not None:
                cand[A.chain_id].append(fab)
                cand[B.chain_id].append(fba)

    def nearest(cid, side, s):
        hits = sorted((d, o) for sd, d, o, lo, hi in cand[cid] if sd == side and lo < s < hi)
        if not hits:
            return None, False
        tie = len(hits) > 1 and hits[1][0] - hits[0][0] <= eps_r and hits[1][1] != hits[0][1]
        return hits[0], tie

    # ------------------------------------------------ local pair runs
    runs = []
    for A in chains:
        for side, d, bid, lo, hi in sorted(cand[A.chain_id], key=lambda z: (z[2], z[0])):
            if bid < A.chain_id:
                continue                                      # each pair once, in the frame of the smaller id
            B = byc[bid]
            if not _elongated(hi - lo, d, eps_r):
                continue                                      # the raw overlap is not elongated: nothing can be
            rt = (0.0, d) if side > 0 else (-d, 0.0)
            if any(_pt_in_open_rect(p, A._axis, lo + eps_r, hi - eps_r, rt[0] + eps_r, rt[1] - eps_r)
                   for p in lab_pts):
                continue                                      # a label in the RAW pair strip: a room, never a band
            bk = {lo, hi}
            bk |= {x for sd, dd, o, l_, h_ in cand[A.chain_id] for x in (l_, h_)}
            for sd, dd, o, l_, h_ in cand[bid]:
                for x in (l_, h_):
                    bk.add(A._axis.st(B._axis.at(x))[0])
            pts = sorted(x for x in bk if lo - eps_n <= x <= hi + eps_n)
            sideB = next(sd for sd, dd, o, l_, h_ in cand[bid] if o == A.chain_id)
            ok = []
            for x0, x1 in zip(pts, pts[1:]):
                if x1 - x0 <= eps_r:
                    continue
                m = (x0 + x1) / 2
                (na, tie_a) = nearest(A.chain_id, side, m)
                if na is None or tie_a or na[1] != bid:
                    continue
                oa, _ = nearest(A.chain_id, -side, m)
                if oa is not None and oa[0] < na[0] - eps_r:
                    continue
                sb = B._axis.st(A._axis.at(m))[0]
                (nb, tie_b) = nearest(bid, sideB, sb)
                if nb is None or tie_b or nb[1] != A.chain_id:
                    continue
                ob, _ = nearest(bid, -sideB, sb)
                if ob is not None and ob[0] < nb[0] - eps_r:
                    continue
                ok.append([x0, x1])
            merged = []
            for iv in ok:
                if merged and iv[0] - merged[-1][1] <= eps_n:
                    merged[-1][1] = iv[1]
                else:
                    merged.append(list(iv))
            for iv in merged:
                runs.append({"A": A, "B": B, "side": side, "sideB": sideB, "d": d, "lo": iv[0], "hi": iv[1],
                             "raw_overlap": hi - lo})

    # ------------------------------------------------ V4 ASSEMBLY_STRUCTURAL_SUPPORT (D2): the LOCAL run must carry it
    def obstacle_gap(r1, r2):
        ax, d = r1["A"]._axis, r1["d"]
        tlo, thi = (0.0, d) if r1["side"] > 0 else (-d, 0.0)
        g0, g1 = r1["hi"], r2["lo"]
        if g1 - g0 <= 2 * eps_r:
            return None
        own = {_entity(z["source"]) for z in r1["A"].fragments} | {_entity(z["source"]) for z in r1["B"].fragments}
        corners = [ax.at(x, t) for x in (g0 + eps_r, g1 - eps_r) for t in (tlo + eps_r, thi - eps_r)]
        for ent, ss in sorted(loops.items()):
            if ent in own or not {x.item.role for x in ss} <= support_roles:
                continue
            if all(_inside(q, ss) for q in corners):
                return ent
        return None
    groups = defaultdict(list)
    for k, r in enumerate(runs):
        groups[(r["A"].chain_id, r["B"].chain_id, r["side"])].append(k)
    for ks in groups.values():
        ks.sort(key=lambda k: runs[k]["lo"])
        comps, links = [[ks[0]]], {}
        for k0, k1 in zip(ks, ks[1:]):
            ent = obstacle_gap(runs[k0], runs[k1])
            if ent is not None:
                comps[-1].append(k1)
                links[k1] = ent
            else:
                comps.append([k1])
        for comp in comps:
            el = {k: _elongated(runs[k]["hi"] - runs[k]["lo"], runs[k]["d"], eps_r) for k in comp}
            selfs = [k for k in comp if el[k]]
            for k in comp:
                if el[k] is None:
                    runs[k]["support"] = {"state": UNSUPPORTED, "reason": BOUNDARY_CASE}
                elif k in selfs:
                    runs[k]["support"] = {"state": SELF_SUPPORTED}
                elif selfs:
                    runs[k]["support"] = {"state": INHERITED_SUPPORT,
                                          "across": sorted({links[x] for x in comp if x in links})}
                else:
                    runs[k]["support"] = {"state": UNSUPPORTED}
    unsupported = [{"chain_a": r["A"].chain_id, "chain_b": r["B"].chain_id, "s": [_r(r["lo"]), _r(r["hi"])],
                    "local_run": r["hi"] - r["lo"], "separation": r["d"], "raw_chain_overlap": r["raw_overlap"],
                    "state": UNSUPPORTED, "reason": r["support"].get("reason", "NOT_ELONGATED_LOCAL_RUN"),
                    "means": "NON_AUTHORITATIVE_PAIR_RUN: no band, no passage, no ambiguity"}
                   for r in runs if r["support"]["state"] == UNSUPPORTED]
    runs = [r for r in runs if r["support"]["state"] != UNSUPPORTED]

    # ------------------------------------------------ a chain paired on BOTH sides over the same interval: ambiguous
    per = defaultdict(list)
    for k, r in enumerate(runs):
        per[(r["A"].chain_id, r["side"])].append((r["lo"], r["hi"], k))
        bl, bh = sorted(r["B"]._axis.st(r["A"]._axis.at(x))[0] for x in (r["lo"], r["hi"]))
        per[(r["B"].chain_id, r["sideB"])].append((bl, bh, k))
    amb = set()
    for (cid, side), ivs in per.items():
        for lo1, hi1, k1 in ivs:
            for lo2, hi2, k2 in per.get((cid, -side), []):
                if min(hi1, hi2) - max(lo1, lo2) > eps_r:
                    amb |= {k1, k2}

    # ------------------------------------------------ strip analysis: spans, overlaps, nodes -> assemblies
    bands, spans_out = [], []
    for k, r in enumerate(runs):
        A, B, side, d, lo, hi = r["A"], r["B"], r["side"], r["d"], r["lo"], r["hi"]
        ax = A._axis
        e = eps_r
        tlo, thi = (0.0, d) if side > 0 else (-d, 0.0)
        mine = {z["source"] for z in A.fragments} | {z["source"] for z in B.fragments}
        ev = {"separation": d, "overlap": hi - lo, "raw_chain_overlap": r["raw_overlap"], "local_mutual_nearest": True,
              "structural_support": r["support"]}
        lab_in = [p for p in lab_pts if _pt_in_open_rect(p, ax, lo + e, hi - e, tlo + e, thi - e)]
        arc_in = [it.source_id for it in arcs if _arc_bbox_hits(it, ax, (lo, hi), tlo, thi, e)]
        if lab_in or arc_in:
            continue                                           # the strip is a room / holds a curve: no band at all
        cross, centre = [], []
        for s in allsegs:
            if s.item.source_id in mine:
                continue
            c = _clip(s, ax, lo + e, hi - e, tlo + e, thi - e)
            if c is None:
                continue
            if abs(s.u[0] * ax.u[1] - s.u[1] * ax.u[0]) * s.L <= eps_r:
                centre.append((c[0], c[1], s.item.source_id))
            else:
                fm = PARAMS["full_width_margin_in_eps_r"] * e
                full = c[2] <= tlo + fm and c[3] >= thi - fm
                cross.append((c[0], c[1], s.item.source_id, s.item.role, full))
        bk = sorted({lo, hi} | {x for c0, c1, *_ in cross for x in (c0, c1)} |
                    {x for c0, c1, _ in centre for x in (c0, c1)})
        bk = [x for x in bk if lo - eps_n <= x <= hi + eps_n]
        dupA = A.duplicate_intervals
        dupB = [sorted(ax.st(B._axis.at(v))[0] for v in iv) for iv in B.duplicate_intervals]
        subs = []
        for x0, x1 in zip(bk, bk[1:]):
            if x1 - x0 <= eps_n:
                continue
            m = (x0 + x1) / 2
            role = None
            if any(a0 < m < a1 for a0, a1 in dupA) or any(a0 < m < a1 for a0, a1 in dupB):
                cls = AMBIGUOUS_DUPLICATE
            elif any(c0 < m < c1 for c0, c1, _ in centre):
                cls = AMBIGUOUS_CENTRELINE
            elif any(c0 < m < c1 and c1 - c0 > eps_r for c0, c1, *_ in cross):
                cls, role = OBSTACLE_OVERLAP, next(rl for c0, c1, _, rl, _f in cross if c0 < m < c1)
            else:
                w = ax.at(m, (tlo + thi) / 2)
                ent = next((en for en, ss in loops.items() if en not in {_entity(x) for x in mine}
                            and _inside(w, ss)), None)
                lb = [c for c in cross if c[4] and min(abs(c[0] - x0), abs(c[1] - x0)) <= eps_r]
                rb = [c for c in cross if c[4] and min(abs(c[0] - x1), abs(c[1] - x1)) <= eps_r]
                if ent is not None:
                    cls, role = OBSTACLE_OVERLAP, next(s.item.role for s in loops[ent])
                elif lb and rb:
                    both_walls = lb[0][3] == GR.TOPOLOGY_BOUNDARY and rb[0][3] == GR.TOPOLOGY_BOUNDARY
                    cls = CROSSING_WALL_NODE if both_walls else ENCLOSED_NODE
                else:
                    cls = AMBIGUOUS_BOTH_SIDES if k in amb else SPAN
            if subs and subs[-1]["class"] == cls and subs[-1].get("role") == role:
                subs[-1]["s"][1] = x1
            else:
                subs.append({"class": cls, "role": role, "s": [x0, x1]})
        for sb in subs:
            if sb["class"] in (OBSTACLE_OVERLAP, CROSSING_WALL_NODE, ENCLOSED_NODE):
                sb["by"] = sorted({c[2] for c in cross if c[0] <= sb["s"][1] + e and c[1] >= sb["s"][0] - e})[:8]
        if not any(sb["class"] == SPAN for sb in subs) and not any(sb["class"].startswith("AMBIGUOUS") for sb in subs):
            continue
        state = AMBIGUOUS if any(sb["class"].startswith("AMBIGUOUS") for sb in subs) else ESTABLISHED
        iso = sorted({_entity(z["source"]) for z in A.fragments + B.fragments} & set(isolated))
        if iso and state == ESTABLISHED:
            state = GEOMETRIC_CANDIDATE                       # V5: geometry without physical authority
        bid = "WB-" + _digest({"rev": revision_id, "region": region_id, "chains": [A.chain_id, B.chain_id],
                               "s": [_r(lo), _r(hi)]})[:16]
        frA = [z for z in A.fragments if z["s"][1] > lo + eps_n and z["s"][0] < hi - eps_n]
        blo, bhi = sorted(B._axis.st(ax.at(x))[0] for x in (lo, hi))
        frB = [z for z in B.fragments if z["s"][1] > blo + eps_n and z["s"][0] < bhi - eps_n]
        band_spans = []
        for sb in subs:
            if sb["class"] != SPAN:
                continue
            x0, x1 = sb["s"]
            sid = "BS-" + _digest({"band": bid, "s": [_r(x0), _r(x1)]})[:16]
            band_spans.append(sid)
            spans_out.append({"span_id": sid, "band_id": bid, "state": state, "chain_a": A.chain_id,
                              "chain_b": B.chain_id, "s": [x0, x1], "width": d,
                              "source_intervals": _intervals(A, ax, x0, x1, eps_n) +
                              _intervals(B, ax, x0, x1, eps_n)})
        fa_, fb_ = sorted([frA[0]["source"], frB[0]["source"]])
        ev = dict(ev, physical_authority={"state": GEOMETRIC_CANDIDATE, "why": ISOLATED_CLOSED_LOOP, "entities": iso}
                  if iso else {"state": PHYSICAL})
        bd = WallBand(bid, fa_, fb_, d, (lo, hi), state,
                      dict(ev, intervals=[{"class": sb["class"], "role": sb.get("role"),
                                           "s": [_r(sb["s"][0]), _r(sb["s"][1])],
                                           "by": sb.get("by", [])} for sb in subs]))
        bd.chain_a, bd.chain_b = A.chain_id, B.chain_id
        bd.faces = sorted({z["source"] for z in frA} | {z["source"] for z in frB})
        bd.spans = band_spans
        bd.axis = tuple(ax.u)
        bd._run = (A, B, side, ax)
        bands.append(bd)
    for bd in bands:
        A, B, side, ax = bd._run
        del bd._run
        if bd.state == ESTABLISHED:
            bd.ends = _ends_v3(bd, A, B, side, ax, items, extra_targets, cap_pool, eps_r, eps_n, band_review)
    bands.sort(key=lambda b: b.band_id)
    passages = _passages(bands, allsegs, eps_r, revision_id, region_id, items, extra_targets)
    return {"policy_id": POLICY_ID, "bands": bands, "passages": passages, "unsupported_runs": unsupported,
            "chain_id_collisions": collisions,
            "isolated_loops": [{"entity": e, "segments": v} for e, v in sorted(isolated.items())],
            "physical_authority_entities": sorted(proven),
            "spans": sorted(spans_out, key=lambda z: z["span_id"]),
            "chains": [{"chain_id": c.chain_id, "identity_basis": c.identity_basis, "occurrence": c.occurrence,
                        "fragments": [{"source": z["source"], "s": z["s"]} for z in c.fragments],
                        "s_range": list(c.s_range), "nodes": c.nodes, "duplicate_intervals": c.duplicate_intervals}
                       for c in chains],
            "chain_breaks": chain_breaks,
            "face_ids_in_bands": sorted({x for bd in bands if bd.state == ESTABLISHED for x in bd.faces})}


def _intervals(ch, ax, x0, x1, eps_n):
    """Exact source-part intervals of chain `ch` that lie under [x0, x1] of axis `ax` (parameter along each source
    segment from its first point, in native units)."""
    lo, hi = sorted(ch._axis.st(ax.at(x))[0] for x in (x0, x1))
    out = []
    for z in ch.fragments:
        a, b = max(lo, z["s"][0]), min(hi, z["s"][1])
        if b - a <= eps_n:
            continue
        seg = z["_seg"]
        s_first = ch._axis.st(seg.a)[0]
        p0, p1 = sorted((abs(a - s_first), abs(b - s_first)))
        out.append({"source": z["source"], "parameter_interval": [_r(p0), _r(min(p1, seg.L))],
                    "source_length": _r(seg.L)})
    return out


def _ends_v3(band, A, B, side, ax, items, extra_targets, cap_pool, eps_r, eps_n, review):
    out = []
    keys = set(band.faces) | {z["source"] for z in A.fragments} | {z["source"] for z in B.fragments}
    adm = [_Seg(it) for it in items if it.kind == "SEGMENT" and it.source_id not in keys]
    openings = [_Seg(it) for it in extra_targets if it.kind == "SEGMENT"]
    pool = [(_Seg(it), role) for it, role in cap_pool if it.kind == "SEGMENT" and role != GR.OPENING_SYMBOL]
    (bs0, _), (bs1, _), blo_p, bhi_p = _chain_points(B, ax)
    b_low, b_high = (blo_p, bhi_p) if bs0 <= bs1 else (bhi_p, blo_p)
    b_range = (min(bs0, bs1), max(bs0, bs1))
    a_low = min(A.fragments, key=lambda z: z["s"][0])
    a_high = max(A.fragments, key=lambda z: z["s"][1])
    for k, s_end in enumerate(band.interval):
        rec = {"end": k, "s": s_end, "outward": -1 if k == 0 else 1}
        a_end = abs(A.s_range[k] - s_end) <= eps_r
        b_end = abs(b_range[k] - s_end) <= eps_r
        if not (a_end and b_end):
            out.append(dict(rec, kind=JUNCTION, continues=[c for c, e_ in ((A.chain_id, a_end), (B.chain_id, b_end))
                                                          if not e_]))
            continue
        fa = a_low if k == 0 else a_high
        pa = fa["low"] if k == 0 else fa["high"]
        pb = b_low if k == 0 else b_high
        fb = next(z for z in B.fragments if math.dist(z["low"], pb) <= eps_n or math.dist(z["high"], pb) <= eps_n)
        if fb["source"] < fa["source"]:                         # source order, never chain-id order
            fa, fb, pa, pb = fb, fa, pb, pa
        rec.update(face_a_end=pa, face_b_end=pb, faces=[fa["source"], fb["source"]], kind=ALIGNED_FREE_END)
        recv_a, recv_b = _beyond(pa, pb, adm, eps_r), _beyond(pb, pa, adm, eps_r)
        if recv_a and recv_b:
            out.append(dict(rec, kind=RECEIVING_FACE_JUNCTION, receiving_face=sorted(set(recv_a + recv_b))))
            continue
        jamb = [o.item.source_id for o in openings if min(math.dist(o.a, pa), math.dist(o.b, pa),
                                                          math.dist(o.a, pb), math.dist(o.b, pb)) <= eps_r
                or (_on_seg(pa, o, eps_r) and _on_seg(pb, o, eps_r))]
        if jamb:
            out.append(dict(rec, kind=OPENING_JAMB, opening=sorted(jamb)))
            continue
        capped = [s.item.source_id for s in adm if _on_seg(pa, s, eps_r) and _on_seg(pb, s, eps_r)]
        if capped:
            rec.update(kind=CAPPED, closed_by=capped)
        caps = []
        w = band.width
        for s, role in pool:
            if abs(s.u[0] * ax.u[0] + s.u[1] * ax.u[1]) * s.L > eps_r:      # not perpendicular
                continue
            (sa, ta), (sb, tb) = ax.st(s.a), ax.st(s.b)
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


def _arc_bbox_hits(it, frame, iv, tlo, thi, e):
    cx, cy, r = it.geometry[0], it.geometry[1], it.geometry[2]
    pts = [(cx - r, cy - r), (cx + r, cy - r), (cx + r, cy + r), (cx - r, cy + r)]
    st = [frame.st(p) for p in pts]
    s_lo, s_hi = min(p[0] for p in st), max(p[0] for p in st)
    t_lo, t_hi = min(p[1] for p in st), max(p[1] for p in st)
    return s_hi > iv[0] + e and s_lo < iv[1] - e and t_hi > tlo + e and t_lo < thi - e


def _beyond(p, q, segs, eps):
    """Admitted segments collinear with the end line p-q that touch p and extend more than eps beyond p, away from q
    (a receiving wall face continuing past this face end point)."""
    L = math.dist(p, q)
    if L <= eps:
        return []
    ux, uy = (p[0] - q[0]) / L, (p[1] - q[1]) / L            # outward from q through p
    out = []
    for s in segs:
        ts = []
        for r in (s.a, s.b):
            dx, dy = r[0] - p[0], r[1] - p[1]
            if abs(-dx * uy + dy * ux) > eps:
                break
            ts.append(dx * ux + dy * uy)
        else:
            if min(ts) <= eps and max(ts) > eps:
                out.append(s.item.source_id)
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


def _passages(bands, allsegs, eps_r, revision_id, region_id, items=(), extra_targets=()):
    """Band end -> the first segment along the band (an admitted segment, or another band's END) that spans the band
    width across an empty strip whose long sides are open (no wall, door or glazing closure along them)."""
    out, seen = [], set()
    ends = [_EndSeg(f"BANDEND|{bd.band_id}|{e['end']}", e["face_a_end"], e["face_b_end"])
            for bd in bands if bd.state == ESTABLISHED for e in bd.ends if e["kind"] in (ALIGNED_FREE_END, CAPPED)]
    lines = [_Seg(it) for it in list(items) + list(extra_targets) if it.kind == "SEGMENT"]
    allsegs = list(allsegs) + ends
    target_roles = set(PARAMS["passage_target_roles"][:2])
    end_ids = {e.item.source_id for e in ends}
    for bd in bands:
        if bd.state != ESTABLISHED:
            continue
        u = bd.axis
        for end in bd.ends:
            if end["kind"] not in (ALIGNED_FREE_END, CAPPED):
                continue
            pa, pb = end["face_a_end"], end["face_b_end"]
            o = end["outward"]
            ux, uy = u[0] * o, u[1] * o
            best = None
            for s in allsegs:
                if s.item.source_id in bd.faces or s.item.source_id in end.get("closed_by", ()) or \
                        s.item.source_id == f"BANDEND|{bd.band_id}|{end['end']}":
                    continue
                if abs(s.u[0] * u[0] + s.u[1] * u[1]) * s.L > eps_r:          # must cross the band line
                    continue
                if s.item.source_id not in end_ids and (s.item.role not in target_roles or
                                                        s.item.source_id.startswith(("CLOSURE|", "GLAZED|"))):
                    continue                                  # V4: the far side must be structural too
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
            blocked = [s.item.source_id for s in allsegs if s.item.source_id not in set(bd.faces) | {target}
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
    if abs(den) < PARAMS["numeric_guards"]["ray_parallel"]:
        return None
    wx, wy = s.a[0] - p[0], s.a[1] - p[1]
    k = (wx * ey - wy * ex) / den
    m = (wx * d[1] - wy * d[0]) / den
    floor = PARAMS["numeric_guards"]["segment_length_floor"]
    if k < -eps or m < -eps / max(s.L, floor) or m > 1 + eps / max(s.L, floor):
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
        c = sorted((_r(x), _r(y)) for x, y in p["polygon"])
        if any(all(math.dist(a, b) <= eps for a, b in zip(c, sorted((_r(x), _r(y)) for x, y in q["polygon"])))
               for q in out):
            continue
        out.append(p)
    return out


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID,
           "model": ["FACE_CHAIN (strict contiguity, typed nodes, supporting-line identity)", "LOCAL BAND SPAN "
                     "(local mutual nearest per elementary interval)", "WALL_BAND_ASSEMBLY (spans + obstacle overlaps "
                     "+ nodes of one chain pair) with ASSEMBLY_STRUCTURAL_SUPPORT on the local run",
                     "OPEN_PASSAGE between two STRUCTURAL sides"],
           "support": [SELF_SUPPORTED, INHERITED_SUPPORT, UNSUPPORTED],
           "unsupported_reasons": ["NOT_ELONGATED_LOCAL_RUN", BOUNDARY_CASE],
           "band_authority": [PHYSICAL, GEOMETRIC_CANDIDATE],
           "params": PARAMS,
           "interval_classes": [SPAN, OBSTACLE_OVERLAP, CROSSING_WALL_NODE, ENCLOSED_NODE, AMBIGUOUS_CENTRELINE,
                                AMBIGUOUS_DUPLICATE, AMBIGUOUS_BOTH_SIDES],
           "chain_nodes": [JOIN, BRANCH, CROSSING, OPENING_BREAK, DUPLICATE],
           "ends": [JUNCTION, RECEIVING_FACE_JUNCTION, OPENING_JAMB, CAPPED, ALIGNED_FREE_END],
           "caps": [CAP_PROVEN, CAP_CANDIDATE, NOT_WALL_CAP, CAP_UNRESOLVED],
           "never": ["thickness", "area", "nearest parallel pair alone", "coordinates alone", "material identity",
                     "a join across any gap", "the 50 mm review band as continuity", "whole-face disqualification by "
                     "geometry outside the local interval", "elongation on the raw chain overlap", "support inherited "
                     "from a group's total length", "an id from entities + extent alone", "a passage to a "
                     "non-structural line", "binary floating-point equality as an elongation decision", "physical "
                     "authority from band geometry alone"],
           "history": ["V1 (R8.11 freeze 5895981): whole-face pairing",
                       "V2 (R8.11 amendment A1): RECEIVING_FACE_JUNCTION",
                       "V3 (R8.12): face chains + local spans + assemblies + OPENING_JAMB; A1 kept",
                       "V4 (R8.13): D1 supporting-line chain identity + chain-id band identity + fail-closed "
                       "collisions; D2 structural support on the LOCAL run (inherited only across a full-width "
                       "structural loop); structural passage targets",
                       "V5 (R8.14): O2 elongation tie against eps_r (fail closed); O1 geometric band candidate for "
                       "isolated closed loops without positive physical authority"],
           "means": "TOPOLOGY_OBSTACLE_GEOMETRY, not MASONRY_CONFIRMED"}
    rec["digest"] = _digest(rec)
    return rec
