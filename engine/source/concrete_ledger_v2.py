"""CONCRETE LEDGER V2 - the frozen route-G concrete ledger with its strip measurement replaced by the strip guard and
the curved-strip pairing (method CONCRETE_LEDGER_V2). A NEW method version beside the frozen pieces: it imports
concrete_completeness and scope_quantities (both FROZEN, not edited) and edits nothing; no released method calls it.

Why: the frozen pass measures a band or a wall strip from `_parallel_pairs` over the lines its geometry ledger left
unexplained (concrete_completeness.geometry_ledger / _describe_group, then scope_quantities._boundary / _pool):
  - a band face that a member is cast against is removed by the 5-point rule before the pairing (EXPLAINED_BY_MEMBER,
    or CONTEXT_OF_OTHER_SHEET) and its partner is left unpaired: a whole side of a band vanishes with no record (T-050);
  - a strip is measured on the shorter face (paired overlap): a closed band loses one width per corner;
  - arcs are never paired: the curved half of a D-shaped pool or a curved wall is silently absent (T-037 F-P1).
This version re-measures the finding's drawn faces with concrete_strip_guard.guard (centre line, corners once, faces
under members HELD, unpaired faces HELD) and concrete_curved_strips.curved_strips (concentric arc pairs), and turns
the result into route-G items that replace the frozen items of the same finding.

Release (no assumptions, owner answers):
  BOUNDARY_WALL band  Q-12 = B (conditional): a band along the plot boundary is released only for a member type that
                      was identified with sheet evidence (boundary-wall footing B.W, boundary-wall ground beam G.B,
                      isolated footing) and passed in `member_types`; until then every part is HELD
                      MEMBER_TYPE_PENDING with its length and plan area, no volume. The section depth comes only from
                      that identification or the family's schedule row (UP-KB-PREC-001, Q-19); no depth -> area only.
  POOL walls / floor  wall plan area from the drawn faces (straight + curved); a volume only from a printed dimension
                      note beside the pool (wall height, floor thickness); a convention size is never used (Q-19:
                      "usual villa sizes" not approved; Q-26 pool depth open): no note -> HELD with the area.
Every face of a re-measured finding ends in exactly one record: MEASURED, HELD (STRIP_UNDER_MEMBER,
STRIP_FACE_UNPAIRED, MEMBER_TYPE_PENDING, CURVED_STRIP_UNPAIRED / _AMBIGUOUS, ...) or UNSUPPORTED; never silently
absent and never 0 (UP-QTY-STATUS-001). Findings of other families keep their frozen items unchanged; the strip
census (`census`) lists frozen vs re-measured strip length for every strip-shaped finding as a diagnostic only.

    measure(R, *, member_types=None) -> {"method", "findings": [...], "items": [...], "supersedes": [...], "census"}
    apply(R, v2) -> the route's item list with the superseded frozen items replaced by the v2 items

R is the result of tools/urban_boq_m2.compute(..., completeness=True) with conventions that switch on
SCOPE_FROM_FINDINGS (V6), so that the completeness params keep every finding's group entities.
Nothing here names a project, a sheet, a layer or a handle.
"""

from __future__ import annotations

import math

from engine.source import concrete_completeness as CC
from engine.source import concrete_curved_strips as CV
from engine.source import concrete_strip_guard as SG
from engine.source import member_detection as MD
from engine.source import provisional_estimate as PE
from engine.source import scope_quantities as SQ

METHOD = "CONCRETE_LEDGER_V2"
RULES = ("UP-QTY-STATUS-001", "UP-KB-PREC-001", "UP-WALL-GEOM-001", "OWNER-Q-12", "OWNER-Q-19")
BAND_FAMILIES = ("BOUNDARY_WALL",)
WALL_FAMILIES = ("POOL",)
MEMBER_KINDS = ("FOOTING", "COLUMN", "COLUMN_BOX", "BAND", "STRAP_CANDIDATE")   # concrete a strip may be cast into
MEMBER_TYPES = ("BOUNDARY_WALL_FOOTING", "BOUNDARY_WALL_GROUND_BEAM", "ISOLATED_FOOTING")   # owner Q-12
ROW_WIDTH_TOL_M = 0.011        # as scope_quantities._boundary: a schedule row whose first size is the drawn width
LOOP_EPS_M = 0.002             # as scope_quantities._wall_geometry: loop nodes closer than this are one node


class LedgerError(ValueError):
    pass


def _r(v):
    return None if v is None else round(v, 6)


# ====================================================================== geometry of one finding
def finding_geometry(CR, D, f, claimed=()):
    """the finding's drawn faces in drawing units: its group entities plus the same-layer faces inside its box that
    the frozen ledger removed before grouping (REMOVED_STATES) and that no other finding holds; the sheet's concrete
    member footprints (drawn outlines only). -> {"lines", "curves", "members", "approx_members_not_used", "box",
    "unit_m", "group_ids", "removed_ids", "plot_edges"}"""
    P = CR.get("params") or {}
    ents = (P.get("_ents") or {}).get(f["SHEET"])
    if ents is None:
        raise LedgerError(f"{f['FINDING_ID']}: the completeness params hold no entities of {f['SHEET']} "
                          "(run with SCOPE_FROM_FINDINGS conventions)")
    ids = (P.get("_group_eids") or {}).get(f["FINDING_ID"])
    if ids is None:
        ids = [x for x in (f.get("REFS") or "").replace("...", "").split(",") if x]
    ids = set(ids)
    u = D["unit_m"]
    group = [e for e in ents if e["eid"] in ids]
    layers = {e["layer"] for e in group}
    sh = D["sheets"][f["SHEET"]]["sheet"]
    org = sh.get("origin") or (0.0, 0.0)
    box = f.get("BOX_M")
    extra = []
    if box and group:
        g = SG.EXPLAIN_TOL_M + CC.PARAMS["STRIP_WIDTH_M"][1]
        bx = ((box[0] - g) / u + org[0], (box[1] - g) / u + org[1],
              (box[2] + g) / u + org[0], (box[3] + g) / u + org[1])
        for e in ents:
            if e["eid"] in ids or e["eid"] in claimed or e["layer"] not in layers:
                continue
            if e.get("state") in SG.REMOVED_STATES and all(CC._in_box(bx, x, y) for x, y in e["pts"]):
                extra.append(e)
    plot = []
    if any(str(x).startswith("PLOT_EDGE:") for x in ids) and group:
        # the frozen ledger takes a plot / building outline loop out of the groups and keeps only its edges that pair
        # with a strip line as PLOT_EDGE:<i> (concrete_completeness._split_outline_loops, not stored): rebuild them
        # from the same-layer lines of that loop, keeping each edge that pairs with one of the group's lines
        cand = [e for e in ents if e["type"] == "LINE" and e["layer"] in layers and e["eid"] not in ids and
                e["eid"] not in claimed and e.get("state") in ("UNEXPLAINED", "OUTSIDE_PLAN_AREA")]
        glines = [e for e in group if e["type"] == "LINE"]
        for k, ring in enumerate(CC._loops(cand, LOOP_EPS_M / u)):
            for i in range(len(ring)):
                a, b = tuple(ring[i]), tuple(ring[(i + 1) % len(ring)])
                edge = {"a": a, "b": b}
                if any(CC._parallel_pairs([edge, gl], 0.08 / u, 0.8 / u, 0.5 / u) for gl in glines):
                    plot.append({"eid": f"PLOT_EDGE:{f['SHEET']}:{k}:{i}", "type": "LINE",
                                 "layer": glines[0]["layer"] if glines else None, "a": a, "b": b,
                                 "state": "PLOT_OR_OUTLINE"})
    lines, curves = [], []
    for e in group + extra + plot:
        if e["type"] == "LINE":
            lines.append({"id": e["eid"], "layer": e["layer"], "a": tuple(e["a"]), "b": tuple(e["b"]),
                          "state": e.get("state")})
        elif e["type"] == "ARC":
            s, m, en = e["pts"]
            curves.append({"type": "ARC", "id": e["eid"], "layer": e["layer"], "c": tuple(e["c"]), "r": e["r"],
                           "s": s, "m": m, "e": en, "state": e.get("state")})
        elif e["type"] == "CIRCLE":
            curves.append({"type": "CIRCLE", "id": e["eid"], "layer": e["layer"], "c": tuple(e["c"]), "r": e["r"],
                           "state": e.get("state")})
    members, approx = [], []
    for m in CC._members(D).get(f["SHEET"], []):
        if m["kind"] not in MEMBER_KINDS or m.get("suspect"):
            continue
        if m.get("approx"):                    # a footprint sized from a schedule around a mark is not drawn
            approx.append(m["mid"])
            continue
        members.append({"id": m["mid"], "kind": m["kind"], "poly": [tuple(p[:2]) for p in m["poly"]]})
    ebox = None
    for e in group:
        ebox = CC._union_box(ebox, e["box"])
    return {"lines": lines, "curves": curves, "members": members, "approx_members_not_used": sorted(approx),
            "box": ebox, "unit_m": u,
            "group_ids": sorted(ids), "removed_ids": sorted(e["eid"] for e in extra),
            "plot_edges": [e["eid"] for e in plot]}


def loop_areas(lines, curves, unit_m):
    """closed loops of straight faces and arc chords (every node of degree 2), as (area m2, loop) largest first. An
    arc adds its circular segment r^2 / 2 (theta - sin theta) when it bulges out of the chord polygon, else removes
    it. Exact for drawn lines and arcs; a chain that does not close is not a loop (left out)."""
    eps = LOOP_EPS_M / unit_m
    key = lambda p: (round(p[0] / eps), round(p[1] / eps))          # noqa: E731
    edges = [("L", ln["a"], ln["b"], None) for ln in lines]
    for c in curves:
        if c["type"] == "ARC":
            edges.append(("A", tuple(c["s"]), tuple(c["e"]), c))
    adj, pos = {}, {}
    for k, (_, a, b, _) in enumerate(edges):
        ka, kb = key(a), key(b)
        if ka == kb:
            continue
        pos[ka], pos[kb] = a, b
        adj.setdefault(ka, []).append((kb, k))
        adj.setdefault(kb, []).append((ka, k))
    seen, out = set(), []
    for start in list(adj):
        if start in seen:
            continue
        comp, stack = [], [start]
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            comp.append(n)
            stack.extend(m for m, _ in adj[n] if m not in seen)
        if len(comp) < 2 or any(len(adj[n]) != 2 for n in comp):
            continue
        ring, used, cur = [comp[0]], [], comp[0]
        while True:
            nxt = [(m, k) for m, k in adj[cur] if k not in used]
            if not nxt:
                break
            m, k = nxt[0]
            used.append(k)
            if m == ring[0]:
                break
            ring.append(m)
            cur = m
        if len(used) != len(comp):
            continue
        poly = [pos[n] for n in ring]
        area = abs(CC._signed_area(poly)) if len(poly) >= 3 else 0.0
        segs = []
        for k in used:
            kind, a, b, c = edges[k]
            if kind != "A":
                continue
            theta = CC._arc_sweep(c)
            seg = c["r"] ** 2 / 2.0 * (theta - math.sin(theta))
            mx, my = c["m"]
            out_of = len(poly) < 3 or not MD.point_in_poly(mx, my, poly)
            area += seg if out_of else -seg
            segs.append({"c": tuple(c["c"]), "r": c["r"], "a": a, "b": b, "m": (mx, my), "out": out_of})
        out.append((area * unit_m * unit_m, {"poly": poly, "segs": segs, "eps": eps}))
    return sorted(out, key=lambda x: -x[0])


def _in_segment(x, y, sg):
    """inside the circular segment between an arc and its chord (the arc's side of the chord)."""
    if math.dist((x, y), sg["c"]) > sg["r"] * (1 + 1e-9):
        return False
    (ax, ay), (bx, by), (mx, my) = sg["a"], sg["b"], sg["m"]
    side = lambda px, py: (bx - ax) * (py - ay) - (by - ay) * (px - ax)       # noqa: E731
    return side(x, y) * side(mx, my) >= 0


def in_loop(x, y, loop):
    """the point lies inside a loop of lines and arcs, or on its boundary (within the loop tolerance)."""
    poly = loop["poly"]
    on = len(poly) >= 2 and min(CC._seg_dist(x, y, poly[i], poly[(i + 1) % len(poly)])
                                for i in range(len(poly))) <= loop["eps"]
    inside = len(poly) >= 3 and MD.point_in_poly(x, y, poly)
    for sg in loop["segs"]:
        if _in_segment(x, y, sg):
            if sg["out"]:
                return True
            return abs(math.dist((x, y), sg["c"]) - sg["r"]) <= loop["eps"]
    return inside or on


def _arcs_m(curve, u):
    """the curve's world arcs with the radius in metres ([] when the curve is bad data: it is UNSUPPORTED)."""
    try:
        arcs, _ = CV.world_curves(curve)
    except (ValueError, TypeError):
        return []
    return [{"r": a["r"] * u, "sweep": a["sweep"]} for a in arcs]


def strip_measure(geom, strip_width_m=None):
    """the guard on the straight faces + the curved pairing on the arcs; conservation of every face length."""
    w = strip_width_m or CC.PARAMS["STRIP_WIDTH_M"]
    u = geom["unit_m"]
    g = SG.guard(geom["lines"], geom["members"], u, tuple(w))
    c = CV.curved_strips(geom["curves"], u, tuple(w))
    face_len = sum(math.dist(ln["a"], ln["b"]) for ln in geom["lines"]) * u
    accounted = sum(f.get("in_strip_length_m") or 0.0 for f in g["faces"]) + \
        sum(h["length_m"] for h in g["held"] if h["reason"] == "STRIP_FACE_UNPAIRED")
    loops = loop_areas(geom["lines"], geom["curves"], u)
    t = g["totals"]
    curved_area = (c["totals"] or {}).get("strip_area_m2", 0.0)
    wall_plan = t["released_area_m2"] + t["held_under_member_area_m2"] + curved_area
    ring = None
    if len(loops) >= 2 and all(in_loop(x, y, loops[0][1]) for x, y in loops[1][1]["poly"]) and \
            all(in_loop(sg["m"][0], sg["m"][1], loops[0][1]) for sg in loops[1][1]["segs"]):
        ring = {"outer_m2": _r(loops[0][0]), "inner_m2": _r(loops[1][0]), "ring_m2": _r(loops[0][0] - loops[1][0]),
                "strips_m2": _r(wall_plan), "difference_m2": _r(wall_plan - (loops[0][0] - loops[1][0]))}
    arc_len = sum(e["r"] * math.radians(e["sweep"]) for cv in geom["curves"] for e in _arcs_m(cv, u))
    arc_acc = sum((s["r_inner_m"] + s["r_outer_m"]) * math.radians(s["sweep_deg"]) for s in c["strips"]) + \
        sum(h["length_m"] for h in c["held"])
    return {"guard": g, "curved": c, "loops": [_r(a) for a, _ in loops], "ring_check": ring,
            "conservation": {"face_length_m": _r(face_len), "accounted_m": _r(accounted),
                             "difference_m": _r(face_len - accounted), "arc_length_m": _r(arc_len),
                             "arc_accounted_m": _r(arc_acc), "arc_difference_m": _r(arc_len - arc_acc),
                             "unsupported_curves": len(c["unsupported"]), "unsupported_lines": len(g["unsupported"])},
            "wall_plan_m2": _r(wall_plan),
            "centre_line_m": _r(t["strip_centre_line_m"] + ((c["totals"] or {}).get("strip_length_m") or 0.0))}


# ====================================================================== items
def _item(f, fam, part, *, category, dims, formula, blocker="", base=None, assumptions=(), support="NO_GEOMETRY",
          src="drawing"):
    st = f.get("STOREY") or "UNKNOWN"
    cid = f"V2:{fam}:{st}:{f['FINDING_ID']}:{part}"
    kw = {}
    if category == "PROVISIONAL":
        kw = {"low": base, "base": base, "high": base}
    return PE.item(item_id=f"P-C:{cid}", component_id=cid, trade="CONCRETE", family=fam, storey=st, category=category,
                   formula=formula, assumptions=list(assumptions), support=support,
                   confidence="LOW" if category == "UNRESOLVED" else "MEDIUM", blocker=blocker,
                   source=f"{src} {f['SHEET']} completeness finding {f['FINDING_ID']} ({f['KIND']}), {METHOD}",
                   dimensions=dims, part=part,
                   double_count_risk="replaces the frozen items of the same finding; faces under members are held, "
                                     "never added", **kw)


def _schedule_section(CR, fam, width_m):
    """(W, H) m of the family's schedule row whose first size is the drawn width (as scope_quantities._boundary)."""
    for r in CR["findings"]:
        if r["KIND"] != "SCHEDULE_ROW_UNREAD" or r["FAMILY"] != fam:
            continue
        sizes = (r.get("MAGNITUDE") or {}).get("sizes") or []
        if len(sizes) >= 2:
            W, H = SQ._row_section_m(sizes)
            if abs(W - width_m) <= ROW_WIDTH_TOL_M:
                return (W, H), r["FINDING_ID"]
    return None, None


def _band(CR, f, sm, member_types, src):
    g = sm["guard"]
    mt = (member_types or {}).get(f["FINDING_ID"])
    if mt is not None and (mt.get("member_type") not in MEMBER_TYPES or not mt.get("evidence")):
        raise LedgerError(f"{f['FINDING_ID']}: a member type is one of {MEMBER_TYPES} with its sheet evidence")
    widths = sorted({s["strip_width_m"] for s in g["strips"] + g["held"] if "strip_width_m" in s})
    row, row_id = _schedule_section(CR, f["FAMILY"], widths[len(widths) // 2]) if widths else (None, None)
    depth = depth_src = None
    if mt is not None and mt.get("section_depth_m"):
        depth, depth_src = float(mt["section_depth_m"]), mt["evidence"]
    elif mt is not None and row is not None:
        depth, depth_src = row[1], f"schedule row {row_id}"
    meas = [s for s in g["strips"]]
    under = [h for h in g["held"] if h["reason"] == "STRIP_UNDER_MEMBER"]
    unpaired = [h for h in g["held"] if h["reason"] == "STRIP_FACE_UNPAIRED"]
    base_dims = {"method": METHOD, "rings": g["rings"], "strip_widths_m": widths,
                 "candidate_row_section_m": list(row) if row else None, "schedule_finding": row_id,
                 "member_type": (mt or {}).get("member_type"), "member_type_evidence": (mt or {}).get("evidence"),
                 "frozen_view": {k: v for k, v in (g["frozen_view"] or {}).items() if k != "omissions"},
                 "frozen_omissions": [{k: o[k] for k in ("id", "frozen_state", "length_m", "detail")}
                                      for o in ((g["frozen_view"] or {}).get("omissions") or [])],
                 "conservation": sm["conservation"]}
    items, records = [], []
    L = sum(s["strip_length_m"] for s in meas)
    A = sum(s["area_m2"] for s in meas)
    dims = dict(base_dims, strip_length_m=_r(L), area_m2=_r(A), pieces=len(meas))
    if meas:
        if mt is None:
            items.append(_item(f, f["FAMILY"], "BAND_PENDING_MEMBER_TYPE", category="UNRESOLVED", dims=dims,
                               formula="centre-line length x drawn width (area only)", src=src,
                               blocker="MEMBER_TYPE_PENDING: identify the member (boundary-wall footing B.W, "
                                       "boundary-wall ground beam G.B or isolated footing) with its sheet evidence "
                                       "(owner Q-12)"))
            records.append({"status": "HELD", "reason": "MEMBER_TYPE_PENDING", **dims})
        elif depth is None:
            items.append(_item(f, f["FAMILY"], "BAND_NO_SECTION_DEPTH", category="UNRESOLVED", dims=dims, src=src,
                               formula="centre-line length x drawn width (area only)",
                               blocker="SECTION_DEPTH_NOT_PRINTED: no schedule row or printed detail gives the depth"))
            records.append({"status": "HELD", "reason": "SECTION_DEPTH_NOT_PRINTED", **dims})
        else:
            v = sum(s["area_m2"] for s in meas) * depth
            d2 = dict(dims, section_depth_m=depth, section_depth_source=depth_src, volume_m3=_r(v))
            items.append(_item(f, f["FAMILY"], "BAND_MEASURED", category="PROVISIONAL", base=v, dims=d2, src=src,
                               formula="centre-line length x drawn width x section depth",
                               assumptions=["SCOPE_FROM_FINDINGS"], support="SOURCE_COMPLETE_UNREVIEWED"))
            records.append({"status": "MEASURED", **d2})
    if under:
        d = dict(base_dims, strip_length_m=_r(sum(h["strip_length_m"] for h in under)),
                 area_m2=_r(sum(h["area_m2"] for h in under)), pieces=len(under),
                 members=sorted({m for h in under for m in h["members"]}),
                 member_kinds=sorted({k for h in under for k in h["member_kinds"]}))
        items.append(_item(f, f["FAMILY"], "BAND_UNDER_MEMBER", category="UNRESOLVED", dims=d, src=src,
                           formula="centre-line length inside member footprints x drawn width (area only)",
                           blocker="STRIP_UNDER_MEMBER: the band runs inside a footing / column footprint; that "
                                   "concrete may already be in the member (reviewer decides; never added)"))
        records.append({"status": "HELD", "reason": "STRIP_UNDER_MEMBER", **d})
    if unpaired:
        d = dict(base_dims, face_length_m=_r(sum(h["length_m"] for h in unpaired)), pieces=len(unpaired),
                 faces=sorted({h["id"] for h in unpaired}))
        items.append(_item(f, f["FAMILY"], "BAND_FACE_UNPAIRED", category="UNRESOLVED", dims=d, src=src,
                           formula="drawn face with no partner at a strip width (length only)",
                           blocker="STRIP_FACE_UNPAIRED: a drawn band face has no parallel partner"))
        records.append({"status": "HELD", "reason": "STRIP_FACE_UNPAIRED", **d})
    return items, records


def _pool(CR, D, f, geom, sm, conv, src):
    g, c = sm["guard"], sm["curved"]
    notes = {}
    if geom["box"] and (conv is None or "PRINTED_DIMENSION_NOTES" in conv.items):
        texts = [t for t in D["model"]["texts"] if t.get("sheet") == f["SHEET"]]
        notes = SQ.notes_in_box(texts, geom["box"], geom["unit_m"])
    one = lambda k: sorted({round(v, 4) for v in notes.get(k, ())})           # noqa: E731
    H, T = one("height"), one("floor")
    wall_plan = sm["wall_plan_m2"]
    outer = sm["loops"][0] if sm["loops"] else None
    dims = {"method": METHOD, "wall_plan_m2": wall_plan, "straight_strip_m2": _r(g["totals"]["released_area_m2"]),
            "straight_under_member_m2": _r(g["totals"]["held_under_member_area_m2"]),
            "curved_strip_m2": _r((c["totals"] or {}).get("strip_area_m2")), "outer_m2": outer,
            "ring_check": sm["ring_check"], "printed": sorted(notes), "conservation": sm["conservation"],
            "held_faces": [{k: h.get(k) for k in ("reason", "id", "length_m")} for h in g["held"] + c["held"]
                           if h["reason"] != "STRIP_UNDER_MEMBER"]}
    items, records = [], []
    if len(H) == 1:
        v = wall_plan * H[0]
        d = dict(dims, wall_height_m=H[0], volume_m3=_r(v))
        items.append(_item(f, "POOL", "WALLS", category="PROVISIONAL", base=v, dims=d, src=src,
                           formula="wall plan area (straight + curved strips) x printed wall height",
                           assumptions=["SCOPE_FROM_FINDINGS", "PRINTED_DIMENSION_NOTES"],
                           support="SOURCE_COMPLETE_UNREVIEWED"))
        records.append({"status": "MEASURED", "part": "WALLS", **d})
    else:
        why = "POOL_WALL_HEIGHT_NOT_PRINTED" if not H else "PRINTED_HEIGHTS_DISAGREE"
        items.append(_item(f, "POOL", "WALLS", category="UNRESOLVED", dims=dict(dims, printed_heights_m=H), src=src,
                           formula="wall plan area (straight + curved strips); height not printed (area only)",
                           blocker=f"{why}: no printed pool depth beside the pool (owner Q-19, Q-26)"))
        records.append({"status": "HELD", "part": "WALLS", "reason": why, **dims})
    if outer is not None and len(T) == 1:
        v = outer * T[0]
        d = dict(dims, floor_t_m=T[0], volume_m3=_r(v))
        items.append(_item(f, "POOL", "FLOOR", category="PROVISIONAL", base=v, dims=d, src=src,
                           formula="outer plan area (drawn lines and arcs) x printed floor thickness",
                           assumptions=["SCOPE_FROM_FINDINGS", "PRINTED_DIMENSION_NOTES"],
                           support="SOURCE_COMPLETE_UNREVIEWED"))
        records.append({"status": "MEASURED", "part": "FLOOR", **d})
    else:
        why = "POOL_OUTLINE_NOT_CLOSED" if outer is None else (
            "POOL_FLOOR_THICKNESS_NOT_PRINTED_NEAR" if not T else "PRINTED_FLOOR_THICKNESSES_DISAGREE")
        items.append(_item(f, "POOL", "FLOOR", category="UNRESOLVED", dims=dict(dims, printed_floor_m=T), src=src,
                           formula="outer plan area (area only)",
                           blocker=f"{why}: no printed floor thickness beside the pool (owner Q-19; a detail on "
                                   "another sheet is not bound here)"))
        records.append({"status": "HELD", "part": "FLOOR", "reason": why, **dims})
    return items, records


# ====================================================================== the pass
def measure_finding(CR, D, f, geom, sm=None, *, conv=None, member_types=None, src="drawing"):
    """(items, records) of one band or wall finding re-measured from its drawn faces; (None, None) for a family this
    version does not re-measure (its frozen items stay)."""
    sm = sm or strip_measure(geom)
    if f["FAMILY"] in BAND_FAMILIES:
        return _band(CR, f, sm, member_types, src)
    if f["FAMILY"] in WALL_FAMILIES:
        return _pool(CR, D, f, geom, sm, conv, src)
    return None, None


def _scope_item_ids(f):
    return [x for x in (f.get("SCOPE_ITEMS") or "").split(",") if x]


def measure(R, *, member_types=None):
    """-> {"method", "findings", "items", "supersedes", "census"} over a route-G result with completeness."""
    g = R.get("generic") or {}
    CR, D = g.get("completeness"), g.get("D")
    if not CR or not D:
        raise LedgerError("measure needs a route-G result computed with completeness=True")
    conv = R.get("conv")
    src = next((i.get("file") for i in R.get("inputs") or () if i.get("kind") == "DXF"), None) or "drawing"
    P = CR.get("params") or {}
    gids = P.get("_group_eids") or {}
    claimed_by_sheet = {}
    for f in CR["findings"]:
        for e in gids.get(f["FINDING_ID"]) or ():
            claimed_by_sheet.setdefault(f["SHEET"], set()).add(e)
    out = {"method": METHOD, "rules": list(RULES), "findings": [], "items": [], "supersedes": [], "census": []}
    for f in CR["findings"]:
        mag = f.get("MAGNITUDE") or {}
        if f["FAMILY"] not in BAND_FAMILIES + WALL_FAMILIES and not mag.get("strip_length_m"):
            continue
        if f["KIND"] == "SCHEDULE_ROW_UNREAD" or f["SHEET"] not in (P.get("_ents") or {}):
            continue
        geom = finding_geometry(CR, D, f, claimed_by_sheet.get(f["SHEET"], set()))
        if not geom["lines"] and not geom["curves"]:
            continue
        sm = strip_measure(geom)
        frozen_ids = _scope_item_ids(f)
        frozen = [i for i in R["items"] if i["item_id"] in frozen_ids]
        cen = {"finding": f["FINDING_ID"], "family": f["FAMILY"], "sheet": f["SHEET"], "storey": f.get("STOREY"),
               "frozen_strip_length_m": mag.get("strip_length_m"), "v2_centre_line_m": sm["centre_line_m"],
               "v2_wall_plan_m2": sm["wall_plan_m2"], "faces": len(geom["lines"]), "curves": len(geom["curves"]),
               "removed_faces_recovered": geom["removed_ids"], "plot_edges": geom["plot_edges"],
               "conservation": sm["conservation"],
               "members_used": len(geom["members"]), "approx_members_not_used": geom["approx_members_not_used"],
               "frozen_items": frozen_ids, "replaced": False}
        items = records = None
        if f.get("SCOPE_STATE") == "MEASURED" and frozen:
            items, records = measure_finding(CR, D, f, geom, sm, conv=conv, member_types=member_types, src=src)
        if items is not None:
            cen["replaced"] = True
            out["supersedes"].extend(frozen_ids)
            out["items"].extend(items)
            out["findings"].append({"finding": f["FINDING_ID"], "family": f["FAMILY"], "sheet": f["SHEET"],
                                    "storey": f.get("STOREY"), "records": records,
                                    "frozen": [{"item_id": i["item_id"], "base": i["base"], "category": i["category"]}
                                               for i in frozen]})
        out["census"].append(cen)
    return out


def apply(R, v2):
    """the route's items with every superseded frozen item replaced by the v2 items (order kept: v2 items take the
    place of the first superseded item of their finding)."""
    gone = set(v2["supersedes"])
    by_finding = {}
    for it in v2["items"]:
        by_finding.setdefault(it["component_id"].split(":")[3], []).append(it)
    out, placed = [], set()
    for it in R["items"]:
        if it["item_id"] not in gone:
            out.append(it)
            continue
        fid = it["component_id"].split(":")[3]
        if fid not in placed:
            out.extend(by_finding.get(fid, []))
            placed.add(fid)
    PE.check(out, R.get("conv"))
    return out


def policy_record():
    return {"policy": METHOD, "rules": list(RULES), "band_families": list(BAND_FAMILIES),
            "wall_families": list(WALL_FAMILIES), "member_kinds": list(MEMBER_KINDS),
            "member_types": list(MEMBER_TYPES),
            "rule": "the frozen route-G ledger with strips re-measured on the centre line (strip guard) and arcs "
                    "paired "
                    "(curved strips); band volume only for an identified member type (owner Q-12), depths only from a "
                    "schedule row or a printed note (Q-19); every face in exactly one record, missing never 0"}
