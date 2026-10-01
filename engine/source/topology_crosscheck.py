"""TOPOLOGY CROSS-CHECK (R8.8 addendum): an independent GEOS reconstruction of TS01's straight-edged sites.

Why it exists
    TS01 owns its noding (exact segment/arc intersection, distance-based node equivalence). Three route-sensitivity
    defects were found in it by real data in R8.8 (F-R88-08..10). An independent kernel that shares none of that
    code is the cheapest way to catch the next one. GEOS is that kernel: it is mature, widely used and does not
    know TS01's clustering, probes or site identities.

What it is - and is not
    * a CHECK, never an authority: no area, edge, site or identity produced here is ever measured or stored as a
      site. GEOS output acquires no source identity; it is compared, then discarded.
    * straight edges only: GEOS has no exact arc. A site whose boundary or holes contain an arc is
      NOT_APPLICABLE_CURVE. Curves are never flattened to make them checkable.
    * fail closed: a site TS01 certified that GEOS cannot reproduce gets GEOS_CROSSCHECK_DISAGREES and is
      REVIEW_REQUIRED. A disagreement never changes a number; it withholds one.

Method
    1  the straight admitted items (opening closures included) are noded by GEOS (`node`) after precision
       reduction to a grid of cell eps_n (topology_policy NOISE). Exact GEOS without a grid cannot be used:
       route noise of a few ULP leaves near-miss end points that GEOS keeps apart, and faces leak.
    2  a grid has a cliff at EVERY grid line - two end points 1 ULP apart can fall in different cells. The check is
       therefore run at ALL GRID_PHASES (offsets of the grid origin) and reported per site (R8.9 V2):
         ALL_PHASES_AGREE              independent confirmation of TS01
         PHASE_SENSITIVE_INCONCLUSIVE  the answer depends on the arbitrary grid origin: evidence about the CHECK's
                                       instability, not confirmation of TS01 (TS01's own two-build certificate
                                       still decides; it is never reported as agreement)
         ALL_PHASES_DISAGREE           GEOS_CROSSCHECK_DISAGREES -> REVIEW_REQUIRED
    3  `polygonize`; the TS01 site polygon is built from its ONE-SIDED boundary (interior stubs removed exactly,
       never repaired): if that polygon is invalid the check reports CHECK_INPUT_INVALID - it never repairs what it
       is meant to challenge (no buffer(0)). For each site, the GEOS face containing its representative point must
         a. exist,
         b. have the same area within the site's certificate bound (eps_r x perimeter), and
         c. PROVENANCE PROOF: every boundary piece of that GEOS face must lie, within 2 x eps_n, on at least one
            straight admitted source item, and the union of the source items so containing a piece must equal
            the site's TS01 boundary + hole source identities (less stubs the face walk passes on both sides,
            which GEOS polygonize drops as dangles). Containment is by every item that contains the
            piece (never the nearest one); a piece no source contains disproves the face.
    4  every GEOS face no TS01 site claims is reported (an input-level finding, not a site issue).

Shapely / GEOS is the project's declared geometry kernel (requirements.txt). It is imported lazily; without it
the check is UNAVAILABLE and recorded as such (TS01's own certificate is unaffected).
"""

from __future__ import annotations

from collections import defaultdict

CHECK_ID = "TOPOLOGY_CROSSCHECK_GEOS_V2"
ALL_PHASES_AGREE, PHASE_SENSITIVE_INCONCLUSIVE, ALL_PHASES_DISAGREE = (
    "ALL_PHASES_AGREE", "PHASE_SENSITIVE_INCONCLUSIVE", "ALL_PHASES_DISAGREE")
AGREES, DISAGREES = ALL_PHASES_AGREE, ALL_PHASES_DISAGREE          # R8.8 names, kept as aliases
NOT_APPLICABLE_CURVE, CHECK_INPUT_INVALID = "NOT_APPLICABLE_CURVE", "CHECK_INPUT_INVALID"
UNAVAILABLE = "UNAVAILABLE"
STATES = (ALL_PHASES_AGREE, PHASE_SENSITIVE_INCONCLUSIVE, ALL_PHASES_DISAGREE, NOT_APPLICABLE_CURVE,
          CHECK_INPUT_INVALID)
GEOS_CROSSCHECK_DISAGREES = "GEOS_CROSSCHECK_DISAGREES"
GRID_PHASES = ((0.0, 0.0), (0.5, 0.5), (0.5, 0.0), (0.0, 0.5))      # in grid cells
CONTAINMENT_FACTOR = 2.0                                               # x eps_n (TS01 edge merge uses 2 x eps)


def _geos():
    try:
        import shapely
        from shapely.geometry import LineString, Polygon, Point
        from shapely.strtree import STRtree
        return shapely, LineString, Polygon, Point, STRtree
    except Exception:                                                  # pragma: no cover - environment dependent
        return None


def _ring(arr, cyc):
    return [arr.nodes[arr.edges[k]["n0"] if fw else arr.edges[k]["n1"]] for k, fw in cyc]


def _straight(arr, cycles):
    return all(arr.edges[k]["kind"] == "S" for cyc in cycles for k, _ in cyc)


def _dangle_only(arr, s):
    """Sources met only on edges the face walk traverses in BOTH directions (a stub / bridge inside the face).
    GEOS polygonize drops such edges, so they are not part of a GEOS face boundary; the TS01 site keeps them."""
    seen = defaultdict(set)
    for cyc in [s["cycle"], *s["hole_cycles"]]:
        for k, fw in cyc:
            seen[k].add(fw)
    one = {src for k, d in seen.items() if len(d) == 1 for src in arr.edges[k]["sources"]}
    two = {src for k, d in seen.items() if len(d) == 2 for src in arr.edges[k]["sources"]}
    return two - one


def _pieces(poly):
    for ring in [poly.exterior, *poly.interiors]:
        cs = list(ring.coords)
        for p, q in zip(cs, cs[1:]):
            if p != q:
                yield p, q


def _on_segment(pt, g, tol):
    (x1, y1, x2, y2), (px, py) = g, pt
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    if L2 == 0.0:
        return (px - x1) ** 2 + (py - y1) ** 2 <= tol * tol
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    qx, qy = x1 + t * dx, y1 + t * dy
    return (px - qx) ** 2 + (py - qy) ** 2 <= tol * tol


def _faces(geos, segs, eps_n, phase):
    shapely, LineString, *_ = geos
    ox, oy = phase[0] * eps_n, phase[1] * eps_n
    lines = shapely.MultiLineString([[(g[0] + ox, g[1] + oy), (g[2] + ox, g[3] + oy)] for g in segs])
    noded = shapely.node(shapely.set_precision(lines, eps_n))
    polys = list(shapely.polygonize(list(noded.geoms)).geoms)
    return [shapely.affinity.translate(p, -ox, -oy) for p in polys]


def _despiked(nodes):
    """A closed node sequence with every out-and-back spike (a stub the face walk passes on both sides) removed."""
    v = list(nodes)
    changed = True
    while changed and len(v) >= 3:
        changed = False
        n = len(v)
        for i in range(n):
            if v[(i - 1) % n] == v[(i + 1) % n]:
                drop = {i, (i + 1) % n}
                v = [x for k, x in enumerate(v) if k not in drop]
                changed = True
                break
    return v


def _site_polygon(Polygon, arr, s):
    def ring(cyc):
        nodes = _despiked([arr.edges[k]["n0"] if fw else arr.edges[k]["n1"] for k, fw in cyc])
        return [arr.nodes[n] for n in nodes]
    outer = ring(s["cycle"])
    holes = [ring(hc) for hc in s["hole_cycles"]]
    if len(outer) < 3 or any(len(h) < 3 for h in holes):
        return None
    P = Polygon(outer, holes)
    return P if P.is_valid and not P.is_empty else None


def check(res, items, eps_n) -> dict:
    """Cross-check the sites of one TS01 analysis (topology.analyse result with its '_arr'). Returns
    {state, per_site: {site_id: {state, phases, reasons}}, counts, unclaimed_geos_faces, geos} - deterministic."""
    geos = _geos()
    out = {"check": CHECK_ID, "grid_cell": eps_n, "grid_phases": [list(p) for p in GRID_PHASES],
           "containment_tolerance": CONTAINMENT_FACTOR * eps_n, "per_site": {}, "unclaimed_geos_faces": []}
    if geos is None:
        out.update(state=UNAVAILABLE, geos=None)
        return out
    shapely, LineString, Polygon, Point, STRtree = geos
    import shapely.affinity  # noqa: F401  (submodule used by _faces)
    out["geos"] = {"shapely": shapely.__version__, "geos": shapely.geos_version_string}
    arr = res["_arr"]
    straight = sorted((it for it in items if it.kind == "SEGMENT"), key=lambda it: it.source_id)
    segs = [it.geometry for it in straight]
    tree = STRtree([LineString([(g[0], g[1]), (g[2], g[3])]) for g in segs]) if segs else None
    tol = CONTAINMENT_FACTOR * eps_n

    def sources_of(face):
        found = set()
        for p, q in _pieces(face):
            cand = tree.query(LineString([p, q]).buffer(tol)) if tree is not None else []
            own = {straight[i].source_id for i in sorted(cand)
                   if _on_segment(p, segs[i], tol) and _on_segment(q, segs[i], tol)}
            if not own:
                return None                                            # a piece no source item contains
            found |= own
        return found

    todo = []
    for s in res["sites"]:
        if not _straight(arr, [s["cycle"], *s["hole_cycles"]]):
            out["per_site"][s["site_id"]] = {"state": NOT_APPLICABLE_CURVE,
                                             "reason": "an arc edge bounds the site; curves are not flattened"}
            continue
        P = _site_polygon(Polygon, arr, s)
        if P is None:
            out["per_site"][s["site_id"]] = {"state": CHECK_INPUT_INVALID,
                                             "reason": "the TS01 site's one-sided boundary is not a valid simple "
                                                       "polygon (e.g. a bridge to an inner loop); not repaired"}
            continue
        todo.append((s, P.representative_point()))
    verdict = defaultdict(dict)
    reasons = defaultdict(list)
    for ph_i, phase in enumerate(GRID_PHASES):
        faces = _faces(geos, segs, eps_n, phase) if segs else []
        ftree = STRtree(faces) if faces else None
        claimed = set()
        for s, rp in todo:
            sid = s["site_id"]
            hits = [faces[i] for i in sorted(ftree.query(rp, predicate="within"))] if ftree is not None else []
            if not hits:
                reasons[sid].append(f"phase {ph_i}: no GEOS face contains the site")
                verdict[sid][ph_i] = False
                continue
            f = min(hits, key=lambda g: g.area)
            bound = s["certificate"]["area_bound"]
            if abs(f.area - s["area"]) > bound:
                reasons[sid].append(f"phase {ph_i}: GEOS area {f.area!r} vs TS01 {s['area']!r} (bound {bound!r})")
                verdict[sid][ph_i] = False
                continue
            src = sources_of(f)
            want = (set(s["boundary_source_ids"]) | set(s["hole_source_ids"])) - _dangle_only(arr, s)
            if src != want:
                reasons[sid].append(f"phase {ph_i}: boundary provenance differs "
                                    f"({'a piece has no source' if src is None else sorted(src ^ want)[:4]})")
                verdict[sid][ph_i] = False
                continue
            verdict[sid][ph_i] = True
            claimed.add(f.wkb_hex)
        if ph_i == 0:
            out["geos_faces_phase0"] = len(faces)
            out["unclaimed_geos_faces"] = sorted(
                ({"area": round(g.area, 9), "point": [round(c, 6) for c in g.representative_point().coords[0]]}
                 for g in faces if g.wkb_hex not in claimed), key=lambda z: (z["area"], z["point"]))
    for s, _ in todo:
        v = verdict[s["site_id"]]
        agree = sorted(k for k, ok in v.items() if ok)
        st = (ALL_PHASES_AGREE if len(agree) == len(GRID_PHASES) else ALL_PHASES_DISAGREE if not agree
              else PHASE_SENSITIVE_INCONCLUSIVE)
        out["per_site"][s["site_id"]] = {"state": st, "phases_agreeing": agree,
                                         "reasons": reasons[s["site_id"]] if st != ALL_PHASES_AGREE else []}
    states = [v["state"] for v in out["per_site"].values()]
    out["counts"] = {k: states.count(k) for k in STATES}
    out["state"] = (ALL_PHASES_DISAGREE if ALL_PHASES_DISAGREE in states else
                    PHASE_SENSITIVE_INCONCLUSIVE if PHASE_SENSITIVE_INCONCLUSIVE in states else ALL_PHASES_AGREE)
    return out
