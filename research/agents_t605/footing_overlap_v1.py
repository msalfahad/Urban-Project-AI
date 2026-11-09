"""T-605 FOOTING_OVERLAP_V1: footings whose drawn outlines overlap, touch, or are notched round each other (every
villa; research only, unwired).

Physical element: each isolated footing is a prism = its DRAWN plan outline x its scheduled depth H, standing on its
own bottom level; its blinding is the drawn outline grown by the printed projection p (one plain-concrete layer, one
layer per plan point); its side forms are its vertical faces. Where two footings meet, the shared material is one
block of concrete, one layer of blinding, and one interface (formed at most once).

Rules (R-T605-1 .. 5, PROPOSED; provenance T-605, ELEMENT_REGISTER 'FOOTING OVERLAP' (Lead 2026-11-07 16:17),
Checker F-C-T597-1, R-T597-1 .. 5, T-233, T-478 (one layer, deeper pit), T-206 (printed bottom stack), ERS s.2):
  R-T605-1  OUTLINE: concrete, blinding and forms follow the DRAWN outline. Where the drawn outline is notched (its
            area is below its bounding rectangle that equals the schedule L x W) the scheduled rectangle is refused as
            the plan; a drawn outline that is missing is HELD (never the schedule rectangle, never 0).
  R-T605-2  CONCRETE ONCE: where two drawn outlines overlap in plan (area A > 0), the common prism is A x the overlap
            of their vertical intervals; it is counted once, owned by the footing that contains it (the deeper one on
            a common bottom); the other footing's volume is net of it. Bottom levels unknown -> the pair is HELD (no
            depth assumed); a missing depth is HELD, never 0. Where one outline is notched round the other the drawing
            has already given the piece away: A = 0 and nothing is deducted twice.
  R-T605-3  BLINDING ONCE: the blinding plan is the union of the grown drawn outlines (R-T597-2); a projection overlap
            goes to the footing whose drawn outline is whole when the other is notched toward it (the drawing decides),
            else to the deeper footing (T-478); equal depths -> SHARED (counted once in the total, not allocated).
  R-T605-4  INTERFACE FORMED AT MOST ONCE: along an edge length e shared by two drawn outlines with vertical contact
            c, each footing's face is formed only where exposed (H - c); the contact c x e is formed once (sequential
            pours) or not at all (monolithic pour): a bound [0, c x e], never 2 c e. Pour sequence not printed -> the
            bound stays open by name.
  R-T605-5  STATEMENT: every pair whose grown outlines overlap or whose drawn outlines touch is listed with drawn vs
            scheduled area, neat overlap, shared edge, grown overlap, and the m3 / m2 deltas against a summed
            schedule rectangle; a sum that counts an overlap twice is refused as a line value.

Units: inputs in metres or millimetres (`unit` required, converted once); outputs m, m2, m3 at 6 dp.
"""
from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import LineString, MultiLineString, Polygon, box
from shapely.ops import unary_union

SCALE = {"m": 1.0, "mm": 0.001}
EPS = 1e-9


class FootingOverlapError(ValueError):
    pass


@dataclass
class Footing:
    fid: str
    outline: list | None            # drawn outline vertices [(x, y), ...]; None = not drawn -> HELD
    depth: float | None             # scheduled H; None -> HELD
    bottom: float | None = None     # bottom level (any common datum); None -> vertical relation unknown
    sched_LW: tuple | None = None   # schedule (L, W) for the rectangle check
    unit: str = "m"


def _s(unit):
    if unit not in SCALE:
        raise FootingOverlapError(f"undeclared unit {unit!r}")
    return SCALE[unit]


def polygon(f: Footing):
    if f.outline is None:
        return None
    s = _s(f.unit)
    g = Polygon([(x * s, y * s) for x, y in f.outline])
    if not g.is_valid or g.area <= EPS:
        raise FootingOverlapError(f"{f.fid}: invalid or empty outline")
    return g


def depth(f: Footing):
    if f.depth is None:
        return None
    d = f.depth * _s(f.unit)
    if d <= 0:
        raise FootingOverlapError(f"{f.fid}: non-physical depth {d}")
    return d


def bottom(f: Footing):
    return None if f.bottom is None else f.bottom * _s(f.unit)


def notched(f: Footing) -> bool:
    """True when the drawn outline is smaller than its bounding rectangle (a notch / cut corner)."""
    g = polygon(f)
    return g is not None and g.envelope.area - g.area > 1e-9


def plan_m2(f: Footing, use_schedule: bool = False):
    """R-T605-1: the plan is the drawn outline; the schedule rectangle is refused where the outline is notched."""
    g = polygon(f)
    if g is None:
        return None
    if use_schedule:
        if f.sched_LW is None:
            raise FootingOverlapError(f"{f.fid}: no schedule size")
        s = _s(f.unit)
        rect = f.sched_LW[0] * s * f.sched_LW[1] * s
        if abs(rect - g.area) > 1e-9:
            raise FootingOverlapError(f"{f.fid}: schedule rectangle {rect:.6f} refused, drawn outline {g.area:.6f}")
        return round(rect, 6)
    return round(g.area, 6)


def grown(g, p):
    """Mitred offset (square corners): the blinding slab has straight edges."""
    return g.buffer(p, join_style="mitre", mitre_limit=10.0)


def vertical_contact(a: Footing, b: Footing):
    da, db, ba, bb = depth(a), depth(b), bottom(a), bottom(b)
    if None in (da, db, ba, bb):
        return None
    return max(0.0, min(ba + da, bb + db) - max(ba, bb))


def _shared_edge(ga, gb, tol=1e-6):
    """Length of boundary the two outlines share (collinear contact within tol, m). An exact line intersection misses
    a shared edge once the drawing is rotated (float noise); a crossing yields only pieces of about 2 tol, dropped."""
    from shapely.ops import snap
    near = snap(ga.boundary, gb.boundary, tol).intersection(gb.boundary)
    parts = getattr(near, "geoms", [near])
    return float(sum(g.length for g in parts if isinstance(g, (LineString, MultiLineString)) and g.length > 20 * tol))


def pair(a: Footing, b: Footing, p: float | None):
    """Pair statement (R-T605-5). p = printed blinding projection (m) or None (blinding HELD)."""
    ga, gb = polygon(a), polygon(b)
    r = {"pair": [a.fid, b.fid]}
    if ga is None or gb is None:
        r["status"] = "HELD: outline not drawn (%s)" % ",".join(f.fid for f, g in ((a, ga), (b, gb)) if g is None)
        return r
    r["drawn_m2"] = [round(ga.area, 6), round(gb.area, 6)]
    r["notched"] = [notched(a), notched(b)]
    A = ga.intersection(gb).area
    e = _shared_edge(ga, gb)
    r["neat_overlap_m2"] = round(A, 6)
    r["shared_edge_m"] = round(e, 6)
    r["gap_m"] = round(ga.distance(gb), 6)
    c = vertical_contact(a, b)
    da, db = depth(a), depth(b)
    # concrete (R-T605-2)
    if A > EPS:
        if c is None:
            r["concrete"] = {"status": "HELD: neat outlines overlap, bottom level or depth unknown", "overlap_m2": round(A, 6)}
        else:
            if abs(da - db) <= EPS and abs(bottom(a) - bottom(b)) <= EPS:
                owner, net = "SHARED", [a.fid, b.fid]       # identical prisms there: counted once, not allocated
            else:
                owner = a.fid if da > db else b.fid
                net = [b.fid if owner == a.fid else a.fid]
            r["concrete"] = {"status": "COUNTED_ONCE", "overlap_m3": round(A * c, 6), "owner": owner,
                             "net_of_it": net}
    else:
        r["concrete"] = {"status": "NO_COMMON_PRISM", "overlap_m3": 0.0}
    # interface forms (R-T605-4)
    if e > EPS:
        if c is None:
            r["formwork"] = {"status": "HELD: contact height unknown", "shared_edge_m": round(e, 6)}
        else:
            r["formwork"] = {"status": "BOUNDED", "contact_m2": round(c * e, 6),
                             "exposed_m2": {a.fid: round((da - c) * e, 6), b.fid: round((db - c) * e, 6)},
                             "interface_formed_m2": [0.0, round(c * e, 6)],
                             "summed_faces_would_be_m2": round((da + db) * e, 6)}
    # blinding (R-T605-3)
    if p is None:
        r["blinding"] = {"status": "HELD: projection not printed"}
    else:
        Ga, Gb = grown(ga, p), grown(gb, p)
        ov = Ga.intersection(Gb).area
        owner = None
        if ov > EPS:
            # the drawing decides when one outline is notched toward the other
            a_yields = notched(a) and ga.envelope.intersection(gb).area > EPS
            b_yields = notched(b) and gb.envelope.intersection(ga).area > EPS
            if a_yields != b_yields:
                owner, why = (b.fid, "drawn whole") if a_yields else (a.fid, "drawn whole")
            elif da is not None and db is not None and abs(da - db) > EPS:
                owner, why = (a.fid if da > db else b.fid), "deeper (T-478)"
            else:
                owner, why = "SHARED", "equal depth or depth unknown: counted once in the union, not allocated"
            r["blinding"] = {"status": "COUNTED_ONCE", "overlap_m2": round(ov, 6), "owner": owner, "why": why}
        else:
            r["blinding"] = {"status": "NO_OVERLAP", "overlap_m2": 0.0}
    return r


def footing_concrete(footings: list[Footing]):
    """Per-footing concrete m3 on the drawn outline, each neat overlap once (R-T605-2); HELD -> None."""
    out = {}
    for f in footings:
        g, d = polygon(f), depth(f)
        out[f.fid] = None if g is None or d is None else g.area * d
    for i, a in enumerate(footings):
        for b in footings[i + 1:]:
            r = pair(a, b, None)
            cc = r.get("concrete", {})
            if cc.get("status") == "COUNTED_ONCE":
                for n in cc["net_of_it"]:
                    if out.get(n) is not None:
                        out[n] -= cc["overlap_m3"]
                if cc["owner"] == "SHARED":
                    out[f"{a.fid}|{b.fid}:SHARED"] = cc["overlap_m3"]
            elif str(cc.get("status", "")).startswith("HELD"):
                out[a.fid] = out[b.fid] = None
    return {k: (None if v is None else round(v, 6)) for k, v in out.items()}


def blinding_plan(footings: list[Footing], p: float | None):
    """Union of grown drawn outlines (R-T605-3 / R-T597-2): (union m2, sum m2, held ids)."""
    if p is None:
        return None, None, [f.fid for f in footings]
    gs, held = [], []
    for f in footings:
        g = polygon(f)
        if g is None:
            held.append(f.fid)
        else:
            gs.append(grown(g, p))
    if not gs:
        return None, None, held
    return round(unary_union(gs).area, 6), round(sum(g.area for g in gs), 6), held


def side_forms(footings: list[Footing], contact_formed: bool):
    """Total vertical face m2 of the group with each interface once (contact_formed True) or not at all (False)."""
    tot = 0.0
    for f in footings:
        g, d = polygon(f), depth(f)
        if g is None or d is None:
            return None
        tot += g.length * d
    for i, a in enumerate(footings):
        for b in footings[i + 1:]:
            r = pair(a, b, None)
            fw = r.get("formwork")
            if fw is None:
                continue
            if fw["status"] != "BOUNDED":
                return None
            tot -= 2 * fw["contact_m2"]
            if contact_formed:
                tot += fw["contact_m2"]
    return round(tot, 6)


def refuse_double(summed: float, once: float, what: str):
    """R-T605-5: a summed figure that exceeds the counted-once figure is refused as a line value."""
    if summed - once > 1e-6:
        raise FootingOverlapError(f"{what}: summed {summed:.6f} exceeds counted-once {once:.6f}: overlap counted twice")
    return once
