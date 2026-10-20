"""ROUTE G SCOPE V1 - which route-G column occurrences and blinding layers are drawn, member family by member family
(method ROUTE_G_SCOPE_V1). A NEW piece beside the frozen route: it reads a route-G result (generic_route.py, frozen,
and the CONCRETE_LEDGER_V2 items when they are passed) and edits neither. No released method calls it; the opt-in
candidate (ARCH_TAKEOFF_V3.0 + route G, lane I) wires it.

Why (development finding T-100, hand reading of a villa's structural set):
  - columns: route G counts a column piece on a storey when the column-plan mark is bound to an outline AND that
    storey's roof-slab plan draws an outline there; a mark that the column plan binds to NO outline is counted on the
    schedule band alone (risk COLUMN_STOREY_PRESENCE_UNVERIFIED), so a column that stops below a partial upper slab
    is released on that slab's storey although its plan draws nothing there;
  - blinding: route G releases one footing layer and one ground / strap beam layer. A footing whose own concrete is
    in conflict (two labels and two schedule sizes in one outline) still gives its blinding; the beam layer rests on
    a footing-detail choice (beam blinding a layer of its own, or merged with the footing layer below it) that the
    founding level decides; strap blinding is counted though no strap section prints one.

Rules (no assumptions, owner answers):
  COLUMNS   drawing first (MISSION.md "No assumptions", owner Q-17 A: a typed or read value only with drawing
            evidence). A column piece is RELEASED only where the roof-slab plan of its storey draws a column outline
            at the occurrence's position, NOT_PRESENT (listed with the sheet and the nearest outline, never a silent 0)
            where it draws none, HELD where the position or the plan cannot be established. The position is the
            column-plan outline; for a mark bound to none, the anchor is the outline of the SAME mark on the
            foundation plan nearest the mark (within ANCHOR_REACH_M, the next same-mark outline at least
            ANCHOR_MARGIN_M farther, and not the outline of another bound occurrence); without an anchor, one outline
            on the storey plan within reach drawn at a section the schedule prints for that mark. Heights and
            sections are the route's (heights to the controlling member are another piece).
  BLINDING  per member family, each square metre once (union of the outlines, as route G's M4 overlap):
            FOOTING      released only where the footing's own concrete is released; a footing in conflict (owner
                         Q-31 C) or held keeps its blinding HELD with the candidate range;
            GROUND_BEAM  HELD as a range while the footing-detail choice is open (owner Q-21 C: the founding level
                         decides which typical footing detail governs): low = beam strips merged with the footing
                         layer, high = beam strips as their own layer (crossings once);
            STRAP        HELD while no strap section prints a blinding (designer request), with its range.
  Every record ends RELEASED, HELD (exposure range, blocker) or NOT_PRESENT; missing never becomes 0
  (UP-QTY-STATUS-001). Nothing here names a project, a sheet, a layer, a mark or a coordinate.

    measure(R, *, items=None, beam_detail=None, strap_blinding_printed=False) -> scope record
    apply(R, sc, items=None) -> the item list with the superseded route items replaced
"""

from __future__ import annotations

import math

from engine.source import generic_route as GR
from engine.source import member_detection as MD
from engine.source import provisional_estimate as PE

METHOD = "ROUTE_G_SCOPE_V1"
RULES = ("OWNER-Q-17", "OWNER-Q-21", "OWNER-Q-31", "URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1", "UP-QTY-STATUS-001")
PRESENCE_TOL_M = 0.25      # as generic_route storey presence: an outline centre this near is the same column
ANCHOR_REACH_M = 2.5       # a mark labels an outline on the same plan frame at most this far from it
ANCHOR_MARGIN_M = 0.5      # the next candidate must be this much farther, else the anchor is ambiguous
SIZE_TOL_M = 0.02          # as member_detection: a drawn section equals a printed one within 2 cm
CONFLICT_STATES = ("LABEL_TYPE_CONFLICT",)
CONFLICT_BLOCKERS = ("SOURCE_CONFLICT", "FOOTING_LABEL_CONFLICT")
BEAM_DETAILS = ("OWN_LAYER", "MERGED_WITH_FOOTING")


class ScopeError(ValueError):
    pass


def _r(v, n=6):
    return None if v is None else round(v + 0.0, n)


def _local(p, rec):
    o = rec["sheet"].get("origin") or (0.0, 0.0)
    return (p[0] - o[0], p[1] - o[1])


def _centre(box, rec):
    return _local(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), rec)


def _size(box, u):
    return tuple(sorted((abs(box[2] - box[0]) * u, abs(box[3] - box[1]) * u)))


def _sheets(D, role):
    return [rec for _, rec in sorted(D["sheets"].items()) if rec["sheet"]["role"] == role]


def _plan_outlines(D):
    """storey -> [(centre local, (short, long) m, sheet id)] from every roof-slab plan of that storey"""
    out = {}
    u = D["unit_m"]
    for rec in _sheets(D, "SLAB_PLAN"):
        lst = out.setdefault(rec["sheet"]["storey"], [])
        for b in list(rec.get("column_boxes", [])) + list(rec.get("column_presence", [])):
            c, s = _centre(b, rec), _size(b, u)
            # a column box is usually also a presence record: one outline once
            if not any(math.dist(c, c2) * u <= 0.01 and abs(s[0] - s2[0]) <= 0.01 and abs(s[1] - s2[1]) <= 0.01
                       for c2, s2, _ in lst):
                lst.append((c, s, rec["sheet"]["sheet_id"]))
    return out


def _nearest(p, outlines, u):
    if not outlines:
        return None, None
    d, o = min(((math.dist(p, c) * u, (c, s, sid)) for c, s, sid in outlines), key=lambda x: x[0])
    return d, o


def _schedule_sections(row):
    out = set()
    for b in ((row or {}).get("by_storey") or {}).values():
        W, H = (b.get("dims_m") or {}).get("W"), (b.get("dims_m") or {}).get("H")
        if W and H:
            out.add((min(W, H), max(W, H)))
    return out


def _fits(sz, sections):
    return any(abs(sz[0] - a) <= SIZE_TOL_M and abs(sz[1] - b) <= SIZE_TOL_M for a, b in sections)


def _anchor(occ, cp_rec, fnd, claimed, u):
    """the foundation-plan outline of the same mark that anchors a column-plan mark bound to no outline
    -> (centre local, evidence) or (None, reason)"""
    m = _local(occ["mark_at"], cp_rec)
    cand = []
    for rec in fnd:
        for c in rec.get("columns", []):
            if c.get("mark") != occ["mark"] or not c.get("box"):
                continue
            p = _centre(c["box"], rec)
            if any(math.dist(p, q) * u <= PRESENCE_TOL_M for q in claimed):
                continue                      # the outline of an occurrence the column plan already binds
            cand.append((math.dist(m, p) * u, p, c["member_id"]))
    cand.sort(key=lambda x: x[0])
    if not cand or cand[0][0] > ANCHOR_REACH_M:
        return None, "no outline of this mark on the foundation plan within reach"
    if len(cand) > 1 and cand[1][0] - cand[0][0] < ANCHOR_MARGIN_M:
        return None, f"two outlines of this mark on the foundation plan ({cand[0][0]:.2f} / {cand[1][0]:.2f} m)"
    return cand[0][1], f"foundation-plan outline {cand[0][2]} at {cand[0][0]:.2f} m from the mark"


def _section_match(occ, cp_rec, outlines, u):
    m = _local(occ["mark_at"], cp_rec)
    secs = _schedule_sections(occ.get("row"))
    near = [(math.dist(m, c) * u, c, s, sid) for c, s, sid in outlines if math.dist(m, c) * u <= ANCHOR_REACH_M]
    fit = [x for x in near if _fits(x[2], secs)]
    if len(fit) == 1:
        return fit[0]
    return None


def _occurrence_items(items, prefix="COL:"):
    """component id -> the route items of a column piece (any trade)"""
    by = {}
    for it in items:
        cid = it.get("component_id") or ""
        if it.get("family") == "COLUMNS" and cid.startswith(prefix) and "|" in cid:
            by.setdefault(cid, []).append(it)
    return by


def column_scope(R, items=None):
    """one record per column piece of the route (occurrence x storey band above the foundation)."""
    g = R.get("generic") or {}
    D = g.get("D")
    if not D:
        raise ScopeError("column_scope needs a route-G result (generic.D)")
    u = D["unit_m"]
    items = R["items"] if items is None else items
    fnd = _sheets(D, "FOUNDATION_PLAN")
    cps = _sheets(D, "COLUMN_PLAN") or fnd      # as route G: no column plan -> the foundation plan's occurrences
    plans = _plan_outlines(D)
    occ_of, cp_of = {}, {}
    for rec in cps:
        for o in rec.get("columns", []):
            occ_of[o["member_id"]] = o
            cp_of[o["member_id"]] = rec
    claimed = [_centre(o["box"], cp_of[k]) for k, o in occ_of.items() if o.get("box")]
    out = []
    for cid, its in sorted(_occurrence_items(items).items()):
        mid, st = cid.rsplit("|", 1)
        conc = [i for i in its if i.get("trade") == "CONCRETE"]
        if not conc or mid not in occ_of or st in ("FOUNDATION", "UNKNOWN"):
            continue                      # planted columns (no column-plan occurrence), necks, unknown types: as is
        c0 = conc[0]
        o, rec = occ_of[mid], cp_of[mid]
        base = c0.get("base")
        dims = c0.get("dimensions") or {}
        r = {"component_id": cid, "occurrence": mid, "mark": o["mark"], "storey": st,
             "route_category": c0["category"], "route_m3": _r(base), "section_m": dims.get("section_m"),
             "height_m": dims.get("height_m"), "item_ids": [i["item_id"] for i in its]}
        if c0["category"] == "UNRESOLVED":
            r.update(status="HELD", basis="ROUTE_HELD", reason=c0.get("blocker") or "held by the route")
            out.append(r)
            continue
        outlines = plans.get(st)
        if not outlines:
            r.update(status="HELD", basis="NO_STOREY_PLAN",
                     reason=f"no roof-slab plan of storey {st} in the set: presence cannot be read")
            out.append(r)
            continue
        if o.get("box"):
            pos, basis, ev = _centre(o["box"], rec), "COLUMN_PLAN_OUTLINE", "column-plan outline"
        else:
            pos, ev = _anchor(o, rec, fnd, claimed, u)
            basis = "FOUNDATION_PLAN_ANCHOR" if pos is not None else None
        if pos is None:
            sm = _section_match(o, rec, outlines, u)
            if sm is not None:
                r.update(status="RELEASED", basis="SECTION_MATCH_ON_STOREY_PLAN", plan=sm[3],
                         nearest_outline_m=_r(sm[0], 2), drawn_m=[_r(x, 2) for x in sm[2]],
                         reason=f"no anchor ({ev}); one outline within reach drawn at a printed section")
            else:
                r.update(status="HELD", basis="PRESENCE_UNVERIFIED",
                         reason=f"column-plan mark bound to no outline and {ev}; no single outline at a printed "
                                f"section near the mark on the {st} plan")
            out.append(r)
            continue
        d, hit = _nearest(pos, outlines, u)
        r.update(plan=hit[2], nearest_outline_m=_r(d, 2), anchor=ev, basis=basis)
        if d <= PRESENCE_TOL_M:
            r.update(status="RELEASED", drawn_m=[_r(x, 2) for x in hit[1]],
                     reason=f"the {st} roof-slab plan draws a column outline at the position ({d:.2f} m)")
        else:
            r.update(status="NOT_PRESENT",
                     reason=f"the {st} roof-slab plan ({hit[2]}) draws no column outline at the position "
                            f"(nearest {d:.2f} m); the schedule band alone is no evidence")
        out.append(r)
    # pieces the route itself did not count (no outline on the storey plan): listed, never silent
    for k in g.get("risk") or ():
        if k.get("KIND") == "COLUMN_ABSENT_ON_STOREY_PLAN":
            cid = (k.get("DETAIL") or "").split(":", 3)
            cid = ":".join(cid[:3]) if len(cid) >= 3 else None
            if cid and "|" in cid:
                out.append({"component_id": cid, "occurrence": cid.rsplit("|", 1)[0], "storey": cid.rsplit("|", 1)[1],
                            "mark": (k.get("WHERE") or " ").split(" ", 1)[-1], "route_category": None,
                            "route_m3": None, "item_ids": [], "status": "NOT_PRESENT", "basis": "ROUTE_ABSENT",
                            "reason": "route G already found no outline on the storey plan (not counted)"})
    return out


# ----------------------------------------------------------------------------------------------------- blinding
def _footing_dims(f, conv):
    """the footing size route G gives its blinding (same selection as generic_route._blinding_items)"""
    if f["state"] == "LABEL_TYPE_CONFLICT" and f.get("candidates"):
        sizes = sorted((c["schedule_m"] for c in f["candidates"].values() if c.get("schedule_m")),
                       key=lambda d: d[0] * d[1])
        if sizes:
            return (sizes[0] if GR._cv(conv, "FOOTING_LABEL_CONFLICT", "LARGER") == "SMALLER" else sizes[-1])[:2]
        return None
    if f["state"] in ("LABEL_ONLY", "LABEL_TYPE_CONFLICT") and f.get("schedule_m"):
        return f["schedule_m"][:2]
    if f["state"] not in ("LABEL_TYPE_CONFLICT_SECONDARY", "NESTED_OR_DUPLICATE_OUTLINE", "NO_OUTLINE") and \
            f.get("drawn_m"):
        return f["drawn_m"][:2]
    return None


def _footing_item(f, items):
    mid = f.get("member_id") or ""
    for it in items:
        if it.get("trade") == "CONCRETE" and it.get("family") == "FOOTINGS" and mid and \
                (it.get("component_id") == mid or (it.get("component_id") or "").startswith(mid + ":")):
            return it
    return None


def _quad(box, pn):
    return [(box[0] - pn, box[1] - pn), (box[2] + pn, box[1] - pn), (box[2] + pn, box[3] + pn),
            (box[0] - pn, box[3] + pn)]


def _union(polys):
    return GR._convex_union_area(polys)[0] if polys else 0.0


def blinding_scope(R, items=None, *, beam_detail=None, strap_blinding_printed=False):
    """footing blinding member by member, ground-beam and strap blinding as families, each m2 once."""
    g = R.get("generic") or {}
    D, conv = g.get("D"), R.get("conv")
    if not D or conv is None:
        raise ScopeError("blinding_scope needs a route-G result (generic.D, conv)")
    if beam_detail is not None and beam_detail not in BEAM_DETAILS:
        raise ScopeError(f"beam_detail {beam_detail!r}: one of {BEAM_DETAILS} or None (open)")
    items = R["items"] if items is None else items
    if "BLINDING_PROJECTION_M" not in conv.items or "BLINDING_THICKNESS_M" not in conv.items:
        return {"state": "NOT_PRINTED", "records": [], "reason": "blinding thickness or projection not in the data"}
    p, t = GR._trip(conv, "BLINDING_PROJECTION_M")[1], GR._trip(conv, "BLINDING_THICKNESS_M")[1]
    u = D["unit_m"]
    pn = p / u
    under = GR._cv(conv, "BLINDING_UNDER", "FOOTINGS_ONLY")
    state, shift, _ = GR._register_on_foundation(D)
    recs, F_rel, F_all = [], [], []
    free_rel = 0.0
    for rec in _sheets(D, "FOUNDATION_PLAN"):
        sid = rec["sheet"]["sheet_id"]
        for f in rec.get("footings", []):
            dims = _footing_dims(f, conv)
            if dims is None:
                if f["state"] not in ("LABEL_TYPE_CONFLICT_SECONDARY", "NESTED_OR_DUPLICATE_OUTLINE"):
                    recs.append({"family": "FOOTING", "member": f.get("member_id"), "mark": f.get("mark"),
                                 "status": "HELD", "m3": None, "exposure_m3": None,
                                 "reason": "footing record without a size: no blinding can be measured"})
                continue
            L, W = dims
            a = (L + 2 * p) * (W + 2 * p)
            placed = bool(f.get("box") and f.get("drawn_m") and list(dims) == list(f["drawn_m"][:2]) and
                          state == "REGISTERED")
            it = _footing_item(f, items)
            conflict = f["state"] in CONFLICT_STATES or (it is not None and (
                it["category"] == "UNRESOLVED" or it.get("blocker") in CONFLICT_BLOCKERS))
            r = {"family": "FOOTING", "member": f.get("member_id"), "mark": f.get("mark"), "sheet": sid,
                 "size_m": [_r(L, 3), _r(W, 3)], "plan_m2_each": _r(a), "placed": placed,
                 "footing_item": it["item_id"] if it else None}
            if placed:
                F_all.append(_quad(f["box"], pn))
            if conflict:
                cands = sorted(((c["schedule_m"][0] + 2 * p) * (c["schedule_m"][1] + 2 * p)
                                for c in (f.get("candidates") or {}).values() if c.get("schedule_m")))
                lo, hi = (max(cands), sum(cands)) if cands else (a, a)
                r.update(status="HELD", m3=None, exposure_m3=[_r(lo * t), _r(hi * t)],
                         route_m3=_r(a * t), blocker="FOOTING_HELD_OR_IN_CONFLICT",
                         reason="the footing's own concrete is held or in conflict (owner Q-31 C): its blinding "
                                "follows it; range = the larger candidate alone .. every candidate as its own pad")
            else:
                r.update(status="RELEASED", m3=_r(a * t))
                if placed:
                    F_rel.append(_quad(f["box"], pn))
                else:
                    free_rel += a
            recs.append(r)
    fp_rel = _union(F_rel) * u * u + free_rel
    released_footing_m3 = fp_rel * t
    overlap_m2 = sum(r["plan_m2_each"] for r in recs if r["status"] == "RELEASED") - fp_rel
    # beams and straps: strips in the foundation frame (band +- p), route G's own outline
    beams, straps = [], []
    for rec in sorted(D["sheets"].values(), key=lambda r: r["sheet"]["sheet_id"]):
        sid = rec["sheet"]["sheet_id"]
        if rec["sheet"]["role"] == "GROUND_BEAM_PLAN":
            bpoly = {x["band_id"]: x for x in rec.get("bands", [])}
            for b in rec.get("beams", []):
                beams.append((b, bpoly.get(b["band_id"]), sid))
        for b in (rec.get("straps") or {}).get("bands", []):
            straps.append((b, b if b.get("u") else None, sid))

    def strips(group):
        S, free, n = [], 0.0, 0
        for b, band, sid in group:
            n += 1
            q = GR._strip_outline(b, band, pn, *shift[sid]) if (state == "REGISTERED" and sid in shift) else None
            if q is None:
                free += b["net_plan_m2"] + 2 * p * b["length_m"]
                continue
            if sum(q[i][0] * q[(i + 1) % 4][1] - q[(i + 1) % 4][0] * q[i][1] for i in range(4)) < 0:
                q = q[::-1]
            S.append(q)
        return S, free, n
    Sb, fb, nb = strips(beams)
    Ss, fs, ns = strips(straps)
    uF = _union(F_all)
    uFb = _union(F_all + Sb)
    beam_low = ((uFb - uF) * u * u + fb) * t              # merged with the footing layer below
    beam_high = (_union(Sb) * u * u + fb) * t             # its own layer (crossings once)
    strap_low = ((_union(F_all + Sb + Ss) - uFb) * u * u + fs) * t
    strap_high = (_union(Ss) * u * u + fs) * t
    if under == "FOOTINGS_AND_GROUND_BEAMS" and nb:
        r = {"family": "GROUND_BEAM", "members": nb, "free_strips": sum(1 for b, band, sid in beams
                                                                         if band is None and not b.get("polygon")),
             "low_merged_m3": _r(beam_low), "high_own_layer_m3": _r(beam_high)}
        if beam_detail == "OWN_LAYER":
            r.update(status="RELEASED", m3=_r(beam_high), reason="detail choice given: beam blinding its own layer")
        elif beam_detail == "MERGED_WITH_FOOTING":
            r.update(status="RELEASED", m3=_r(beam_low), reason="detail choice given: merged with the footing layer")
        else:
            r.update(status="HELD", m3=None, exposure_m3=[_r(beam_low), _r(beam_high)],
                     blocker="FOOTING_DETAIL_CHOICE_OPEN",
                     reason="which typical footing detail governs (beam blinding its own layer at beam level, or "
                            "merged with the footing blinding below) depends on the founding level, held (owner "
                            "Q-21 C)")
        recs.append(r)
    elif nb:
        recs.append({"family": "GROUND_BEAM", "members": nb, "status": "HELD", "m3": None,
                     "exposure_m3": [_r(beam_low), _r(beam_high)], "blocker": "BLINDING_UNDER_BEAMS_NOT_ESTABLISHED",
                     "reason": "no typical detail shows blinding under the ground beams"})
    if ns:
        # a strap runs between footings at footing level: its blinding can only merge with theirs, so the held
        # quantity is the merged strip (the own-strip area is kept as a diagnostic, never a reading)
        r = {"family": "STRAP", "members": ns, "merged_m3": _r(strap_low), "own_strip_diagnostic_m3": _r(strap_high)}
        if strap_blinding_printed and under == "FOOTINGS_AND_GROUND_BEAMS":
            r.update(status="RELEASED", m3=_r(strap_low), reason="a strap section prints the blinding")
        else:
            r.update(status="HELD", m3=None, exposure_m3=[_r(strap_low), _r(strap_low)],
                     blocker="STRAP_BLINDING_NOT_PRINTED",
                     reason="the strap schedule prints sizes only; no strap section shows a blinding (designer "
                            "request)")
        recs.append(r)
    rel = sum(r["m3"] for r in recs if r["status"] == "RELEASED" and r["family"] == "FOOTING")
    rel_other = sum(r["m3"] for r in recs if r["status"] == "RELEASED" and r["family"] != "FOOTING")
    held = [r for r in recs if r["status"] == "HELD"]
    hl = sum((r.get("exposure_m3") or [0, 0])[0] or 0 for r in held)
    hh = sum((r.get("exposure_m3") or [0, 0])[1] or 0 for r in held)
    released = released_footing_m3 + rel_other
    return {"state": "MEASURED", "registration": state, "thickness_m": t, "projection_m": p,
            "records": recs, "footing_overlap_m2": _r(overlap_m2),
            "footing_records_sum_m3": _r(rel), "released_m3": _r(released),
            "held_exposure_m3": [_r(hl), _r(hh)], "total_range_m3": [_r(released + hl), _r(released + hh)],
            "released_footing_m3": _r(released_footing_m3)}


# ------------------------------------------------------------------------------------------------- the piece
def measure(R, *, items=None, beam_detail=None, strap_blinding_printed=False):
    items = R["items"] if items is None else items
    cols = column_scope(R, items)
    bl = blinding_scope(R, items, beam_detail=beam_detail, strap_blinding_printed=strap_blinding_printed)
    by_st = {}
    for c in cols:
        k = by_st.setdefault(c["storey"], {"RELEASED": 0.0, "HELD": 0.0, "NOT_PRESENT": 0.0, "route": 0.0,
                                           "not_present": []})
        v = c.get("route_m3") or 0.0
        k[c["status"]] += v
        if c.get("route_category") not in (None, "UNRESOLVED"):
            k["route"] += v
        if c["status"] == "NOT_PRESENT" and c.get("route_m3"):
            k["not_present"].append(c["component_id"])
    for k in by_st.values():
        for x in ("RELEASED", "HELD", "NOT_PRESENT", "route"):
            k[x] = _r(k[x])
    return {"method": METHOD, "rules": list(RULES), "columns": cols, "columns_by_storey": by_st,
            "blinding": bl, "parameters": {"presence_tol_m": PRESENCE_TOL_M, "anchor_reach_m": ANCHOR_REACH_M,
                                           "anchor_margin_m": ANCHOR_MARGIN_M, "size_tol_m": SIZE_TOL_M,
                                           "beam_detail": beam_detail,
                                           "strap_blinding_printed": strap_blinding_printed}}


def _held_column_item(c, it):
    B, H = (c.get("section_m") or (None, None))
    v = c.get("route_m3")
    return PE.item(item_id=f"U-C:{c['component_id']}", component_id=c["component_id"], trade="CONCRETE",
                   family="COLUMNS", storey=c["storey"], category="UNRESOLVED", support="NO_GEOMETRY",
                   confidence="LOW", blocker="COLUMN_PRESENCE_UNVERIFIED",
                   exposure_low=0.0 if v is not None else None, exposure_high=v,
                   source=it.get("source") or METHOD, dimensions=it.get("dimensions") or {},
                   expression=f"0 .. {B} x {H} x {c.get('height_m')}: {c['reason']}")


def apply(R, sc, items=None):
    """the item list with: NOT_PRESENT column pieces removed (every item of the piece, any trade; listed in
    sc["columns"]), HELD pieces as an UNRESOLVED concrete item with its exposure (their other items removed), and
    the two route blinding items replaced by the family records."""
    items = R["items"] if items is None else items
    drop, put = set(), {}
    for c in sc["columns"]:
        if c["status"] in ("NOT_PRESENT", "HELD") and c.get("item_ids") and c.get("route_category") != "UNRESOLVED":
            drop.update(c["item_ids"])
            if c["status"] == "HELD":
                first = next(i for i in items if i["item_id"] in c["item_ids"] and i.get("trade") == "CONCRETE")
                put[first["item_id"]] = [_held_column_item(c, first)]
    bl = sc["blinding"]
    if bl.get("state") == "MEASURED":
        old = [i for i in items if i.get("family") == "PLAIN_CONCRETE" and
               (i.get("component_id") or "").startswith("PLAIN_CONCRETE:FOUNDATION:BLINDING_")]
        if old:
            src = old[0].get("source") or METHOD
            new = []
            asm = ["BLINDING_THICKNESS_M", "BLINDING_PROJECTION_M"]
            fv = bl["released_footing_m3"]
            new.append(PE.item(item_id="P-C:PLAIN_CONCRETE:FOUNDATION:BLINDING_FOOTINGS_RELEASED",
                               component_id="PLAIN_CONCRETE:FOUNDATION:BLINDING_FOOTINGS_RELEASED", trade="CONCRETE",
                               family="PLAIN_CONCRETE", storey="FOUNDATION", category="PROVISIONAL", low=fv,
                               base=fv, high=fv, source=src, assumptions=asm, support="CONVENTION_ONLY",
                               confidence="MEDIUM", blocker="BLINDING_PROJECTION",
                               formula="union of (L + 2p)(W + 2p) under each released footing x t",
                               dimensions={"members": sum(1 for r in bl["records"] if r["family"] == "FOOTING" and
                                                          r["status"] == "RELEASED")}))
            for k, r in enumerate(bl["records"]):
                cid = f"PLAIN_CONCRETE:FOUNDATION:BLINDING_{r['family']}" + (
                    f":{r.get('member')}" if r["family"] == "FOOTING" else "")
                if r["status"] == "RELEASED" and r["family"] != "FOOTING":
                    new.append(PE.item(item_id=f"P-C:{cid}", component_id=cid, trade="CONCRETE",
                                       family="PLAIN_CONCRETE", storey="FOUNDATION", category="PROVISIONAL",
                                       low=r["m3"], base=r["m3"], high=r["m3"], source=src,
                                       assumptions=asm + ["BLINDING_UNDER"], support="CONVENTION_ONLY",
                                       confidence="MEDIUM", blocker="BLINDING_PROJECTION", formula=r["reason"]))
                elif r["status"] == "HELD":
                    ex = r.get("exposure_m3") or [None, None]
                    new.append(PE.item(item_id=f"U-C:{cid}", component_id=cid, trade="CONCRETE",
                                       family="PLAIN_CONCRETE", storey="FOUNDATION", category="UNRESOLVED",
                                       support="NO_GEOMETRY", confidence="LOW", blocker=r.get("blocker") or "HELD",
                                       exposure_low=ex[0], exposure_high=ex[1], source=src,
                                       expression=r["reason"]))
            drop.update(i["item_id"] for i in old)
            put[old[0]["item_id"]] = new
    out = []
    for it in items:
        if it["item_id"] in put:
            out.extend(put[it["item_id"]])
        elif it["item_id"] not in drop:
            out.append(it)
    PE.check(out, R.get("conv"))
    return out


def policy_record():
    return {"policy": METHOD, "rules": list(RULES), "presence_tol_m": PRESENCE_TOL_M,
            "anchor_reach_m": ANCHOR_REACH_M, "anchor_margin_m": ANCHOR_MARGIN_M, "size_tol_m": SIZE_TOL_M,
            "rule": "a column piece is released only where the roof-slab plan of its storey draws it (position from "
                    "the column-plan outline, else the same mark's foundation-plan outline, else one outline at a "
                    "printed section); undrawn pieces NOT_PRESENT and listed; blinding per member family: footing "
                    "blinding follows its footing, ground-beam blinding a held range while the footing detail is "
                    "open (Q-21 C), strap blinding held while no strap section prints it; missing never 0"}
