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
    2  a grid has a cliff at EVERY grid line - two end points 1 ULP apart can fall in different cells. That
       cliff is unrelated to the noise/authored bands, so the check is run at GRID_PHASES (offsets of the grid
       origin). The grid origin is an arbitrary representation choice: a disagreement that disappears in some
       phase is a grid artefact; a defect of TS01 is phase-independent. A site AGREES if it agrees in any phase;
       it DISAGREES only if it disagrees in every phase.
    3  `polygonize`; for each TS01 site, the GEOS face containing the site's representative point must
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

CHECK_ID = "TOPOLOGY_CROSSCHECK_GEOS_V1"
AGREES, DISAGREES, NOT_APPLICABLE_CURVE = "AGREES", "DISAGREES", "NOT_APPLICABLE_CURVE"
UNAVAILABLE = "UNAVAILABLE"
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


def check(res, items, eps_n) -> dict:
    """Cross-check the sites of one TS01 analysis (topology.analyse result with its '_arr'). Returns
    {state, per_site: {site_id: {state, phase, reason}}, unclaimed_geos_faces, geos} - deterministic."""
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
        P = Polygon(_ring(arr, s["cycle"]), [_ring(arr, hc) for hc in s["hole_cycles"]])
        if not P.is_valid:
            P = P.buffer(0)
        todo.append((s, P.representative_point()))
    claimed = defaultdict(set)
    reasons = defaultdict(list)
    for ph_i, phase in enumerate(GRID_PHASES):
        pending = [(s, rp) for s, rp in todo if s["site_id"] not in out["per_site"]]
        if not pending:
            break
        faces = _faces(geos, segs, eps_n, phase) if segs else []
        ftree = STRtree(faces) if faces else None
        for s, rp in pending:
            hits = [faces[i] for i in sorted(ftree.query(rp, predicate="within"))] if ftree is not None else []
            if not hits:
                reasons[s["site_id"]].append(f"phase {ph_i}: no GEOS face contains the site")
                continue
            f = min(hits, key=lambda g: g.area)
            bound = s["certificate"]["area_bound"]
            if abs(f.area - s["area"]) > bound:
                reasons[s["site_id"]].append(f"phase {ph_i}: GEOS area {f.area!r} vs TS01 {s['area']!r} "
                                             f"(bound {bound!r})")
                continue
            src = sources_of(f)
            want = (set(s["boundary_source_ids"]) | set(s["hole_source_ids"])) - _dangle_only(arr, s)
            if src != want:
                reasons[s["site_id"]].append(f"phase {ph_i}: boundary provenance differs "
                                             f"({'a piece has no source' if src is None else sorted(src ^ want)[:4]})")
                continue
            out["per_site"][s["site_id"]] = {"state": AGREES, "phase": ph_i}
            claimed[ph_i].add(f.wkb_hex)
        if ph_i == 0:
            out["geos_faces_phase0"] = len(faces)
            out["unclaimed_geos_faces"] = sorted(
                ({"area": round(g.area, 9), "point": [round(c, 6) for c in g.representative_point().coords[0]]}
                 for g in faces if g.wkb_hex not in claimed[0]), key=lambda z: (z["area"], z["point"]))
    for s, _ in todo:
        if s["site_id"] not in out["per_site"]:
            out["per_site"][s["site_id"]] = {"state": DISAGREES, "reasons": reasons[s["site_id"]]}
    states = [v["state"] for v in out["per_site"].values()]
    out["counts"] = {k: states.count(k) for k in (AGREES, DISAGREES, NOT_APPLICABLE_CURVE)}
    phases = [str(v["phase"]) for v in out["per_site"].values() if v["state"] == AGREES]
    out["agreed_in_phase"] = {p: phases.count(p) for p in sorted(set(phases))}
    out["state"] = DISAGREES if DISAGREES in states else AGREES
    return out
