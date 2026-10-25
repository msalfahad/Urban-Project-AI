"""CEILINGS_R3: the room-by-room ceiling ledger made integration-ready (research module, unwired; any villa).

Builds on CEILINGS_R2 (research/agents_t271/ceilings_r2.py, MERGED 789ebbb4, T-271 r2b), which it imports and never
edits. Two rules are added; both close a way in which a face of the R2 ledger could be counted in the wrong surface:

R-CEIL-R3-1 (proposed, any villa; Verifier test-adequacy note on T-271 r2b): a stair drawn under a slab (hidden treads,
    flights, landings) is ONE footprint. It is distributed over EVERY slab face of that plan that it crosses - the
    stair-class face, the void face, and the beam / band / column faces next to them - and the parts must sum to the
    footprint (residual <= 1e-6 m2). A part outside every slab face (over a wall line) is returned by name, never
    dropped. Intersecting the footprint with one face only (the T-271 `split_structural_void` call) clips the rest
    silently: under a beam band crossed by a flight the ceiling then stays 'decor ceiling' although the flight is
    what is built below the band. Every part over a floor piece is a STAIR ZONE: deducted once from the decor ceiling,
    HELD for the stair-soffit line (T-281 pieces), never 0.

R-CEIL-R3-2 (proposed, any villa): a bulkhead vertical face exists only along a beam-piece edge that has DECOR CEILING
    on its open side. An edge segment whose open side is a no-ceiling part (light well, pocket, shaft), a stair zone or
    an open dome / skylight position is an opening edge: it is listed ONCE, as an opening edge (drop / return / well
    face, HELD on its height), never also as an owner-method bulkhead face (m2) or a held bulkhead edge (m). Segments
    are judged one by one as in R-CEIL-R2-3 (both ends and the midpoint within tol of the open part); a straight edge
    that only touches a circle at a tangent is not bordering it.

Statuses: WORKFLOW_CONTROLS s.5. Nothing here names a project, a sheet, a layer or a coordinate."""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agents_t271"))
import ceilings_r2 as CR  # noqa: E402

LedgerError = CR.LedgerError
OWNER_ALLOW = CR.OWNER_ALLOW
EDGE_TOL = CR.EDGE_TOL
BORDER_TOL = 0.003          # m: a free-edge segment lying within 3 mm of an open part borders it
CLOSE_TOL = 1e-6            # m2: the footprint parts must close to this
STAIR_REF = "T-281 (stair soffit geometry per flight and landing): HELD until it merges, never 0"
ST_DC, ST_OA, ST_H, ST_U = CR.ST_DC, CR.ST_OA, CR.ST_H, CR.ST_U
STAIR_CLASSES = ("STAIR",)


# ----------------------------------------------------------------------------------------------- R-CEIL-R3-1
def stair_zone_parts(footprint, slab_faces, min_part=0.0005):
    """footprint: shapely polygon (or multipolygon) of the stair drawn under the slab, whole (every flight, landing and
    edge strip the slab plan draws under it). slab_faces: [(face_id, cls, polygon)] of that slab plan.
    Returns (parts, outside_m2): parts = [(face_id, cls, polygon)] for every face the footprint crosses (area >
    min_part), outside_m2 = footprint area in no face (over wall lines; listed, never dropped). Faces that overlap
    each other are refused (a footprint part would be counted twice). Raises LedgerError when the parts plus the
    outside do not close to the footprint."""
    from shapely.ops import unary_union
    if footprint is None or footprint.is_empty or footprint.area <= 0:
        raise LedgerError("empty stair footprint")
    parts, seen = [], []
    for fid, cls, poly in slab_faces:
        x = poly.intersection(footprint)
        if x.area <= min_part:
            continue
        for oid, op in seen:
            if op.intersection(x).area > 1e-6:
                raise LedgerError(f"slab faces {oid} and {fid} overlap inside the stair footprint: counted twice")
        seen.append((fid, x))
        parts.append((fid, cls, x))
    covered = unary_union([p for _, _, p in parts]) if parts else None
    outside = footprint.area if covered is None else footprint.difference(covered).area
    tot = sum(p.area for _, _, p in parts) + outside
    if abs(tot - footprint.area) > CLOSE_TOL + min_part * len(slab_faces):
        raise LedgerError(f"stair footprint does not close: parts {tot:.6f} vs footprint {footprint.area:.6f} m2")
    return parts, round(outside, 6)


def single_face_split_refused(footprint, face, other_faces, min_part=0.0005):
    """The adverse check: a stair footprint intersected with ONE face while it also crosses other faces is the silent
    clip R-CEIL-R3-1 forbids. Returns the area that the single-face split would lose; raises LedgerError if > 0."""
    lost = sum(p.intersection(footprint).area for _, _, p in other_faces if p.intersection(footprint).area > min_part)
    if lost > 0:
        raise LedgerError(f"stair footprint crosses {lost:.4f} m2 beyond face: a one-face split clips it silently")
    return 0.0


def flight_footprints(treads, going_max=0.36, tol=0.005):
    """Footprint of each straight flight from its drawn tread lines: lines grouped by direction and by the two
    stringer lines their end points lie on (a dog-leg's two flights are two groups); one flight = the rectangle from
    its first to its last tread line. A single isolated line (a winder, a curtail) is not a flight here (returned in
    'loose'). treads: [(id, (x0, y0), (x1, y1))] metres. Returns ([(ids, polygon)], loose_ids). Landings and the
    goings beyond the end treads are NOT in these footprints (T-281 measures them)."""
    from shapely.geometry import MultiLineString, LineString
    groups = {}
    for tid, a, b in treads:
        L = math.dist(a, b)
        if L <= 0:
            raise LedgerError(f"tread {tid}: zero length")
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        if ux < -1e-9 or (abs(ux) < 1e-9 and uy < 0):
            ux, uy, a, b = -ux, -uy, b, a
        s0, s1 = a[0] * ux + a[1] * uy, b[0] * ux + b[1] * uy
        key = (round(math.degrees(math.atan2(uy, ux)) % 180, 1), round(s0 / tol) * tol, round(s1 / tol) * tol)
        groups.setdefault(key, []).append((tid, LineString([a, b]), (-uy, ux)))
    flights, loose = [], []
    for key, g in groups.items():
        n = g[0][2]
        g.sort(key=lambda t: t[1].coords[0][0] * n[0] + t[1].coords[0][1] * n[1])
        run = [g[0]]
        for t in g[1:]:
            prev = run[-1][1].coords[0]
            cur = t[1].coords[0]
            if abs((cur[0] - prev[0]) * n[0] + (cur[1] - prev[1]) * n[1]) <= going_max:
                run.append(t)
            else:
                (flights if len(run) > 1 else loose).append(run)
                run = [t]
        (flights if len(run) > 1 else loose).append(run)
    out = [([t[0] for t in r], MultiLineString([t[1] for t in r]).convex_hull) for r in flights if len(r) > 1]
    return out, [r[0][0] for r in loose if len(r) == 1]


# ----------------------------------------------------------------------------------------------- R-CEIL-R3-2
STABLE = 0.9               # a coincident edge keeps >= 90 % of its contact when the tolerance is cut to 1/6


def contact(line, poly, tol=BORDER_TOL):
    """Length of the free edge `line` (LineString / MultiLineString) that runs ALONG poly's boundary or inside poly.
    The part of the line within tol of poly is merged into connected runs; a run counts only when it is stable under
    the tolerance: a coincident edge keeps its length at tol / 6, a straight edge touching a curve at a tangent does
    not (its contact shrinks with the square root of the tolerance, 2 sqrt(2 R tol)). Returns (length, the counted
    runs as one geometry or None)."""
    from shapely.ops import linemerge, unary_union
    near = line.intersection(poly.buffer(tol, 64))
    if near.is_empty or near.length <= 0:
        return 0.0, None
    runs = getattr(near, "geoms", [near])
    lines = [g for g in runs if g.geom_type in ("LineString", "MultiLineString") and g.length > 0]
    if not lines:
        return 0.0, None
    u = unary_union(lines)
    merged = linemerge(list(getattr(u, "geoms", [u])))
    tight = poly.buffer(tol / 6, 64)
    keep = [r for r in getattr(merged, "geoms", [merged])
            if r.length > 0.01 and r.intersection(tight).length >= STABLE * r.length]
    if not keep:
        return 0.0, None
    k = unary_union(keep)
    return k.intersection(tight).length, k      # measured at tol / 6: the run's ends overshoot by <= 0.5 mm


def border_segments(piece, room, open_parts, tol=BORDER_TOL, edge_tol=EDGE_TOL):
    """Free edge of a beam piece (R-CEIL-R2-3: segments not on the room's wall face) split by what lies on its open
    side. open_parts: [(kind, polygon)] with kind in NO_CEILING / STAIR_ZONE / DOME_OPEN, in priority order.
    Returns {'decor': m, kind: m, ...}: the runs of the free edge along an open part (contact(), stable under the
    tolerance) belong to the first kind that claims them, the rest is decor; each metre once."""
    from shapely.geometry import LineString, MultiLineString, Point
    rb = room.boundary
    segs = []
    for g in getattr(piece, "geoms", [piece]):
        if g.is_empty or g.geom_type != "Polygon":
            continue
        for ring in [g.exterior, *g.interiors]:
            c = list(ring.coords)
            for a, b in zip(c, c[1:]):
                m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                if all(rb.distance(Point(p)) <= edge_tol for p in (a, b, m)):
                    continue                                        # wall face: not a free edge
                if math.dist(a, b) > 0:
                    segs.append(LineString([a, b]))
    out = {"decor": 0.0}
    if not segs:
        return out
    free = MultiLineString(segs)
    total = sum(x.length for x in segs)
    left = free
    for kind, poly in open_parts:
        L, k = contact(left, poly, tol)
        if L > 0:
            out[kind] = out.get(kind, 0.0) + L
            left = left.difference(k.buffer(1e-9))
            if left.is_empty:
                break
    out["decor"] = max(total - sum(v for kk, v in out.items() if kk != "decor"), 0.0)
    return {k: round(v, 4) for k, v in out.items()}


def bulkhead_split(free_edge_m, borders, depth, status, tol=0.002):
    """Owner-method bulkhead of one beam piece after R-CEIL-R3-2. free_edge_m: the R2 free edge; borders: the dict of
    border_segments (its sum must equal the free edge within tol m, else the record is refused). Returns
    {'owner_m2', 'owner_lm', 'held_lm', 'opening_lm': {kind: m}} with owner faces only on the decor part of a
    CALCULATED beam deeper than the owner allowance."""
    tot = sum(borders.values())
    if abs(tot - free_edge_m) > tol:
        raise LedgerError(f"border split {tot:.4f} m does not close the free edge {free_edge_m:.4f} m")
    opening = {k: v for k, v in borders.items() if k != "decor" and v > 0}
    dec = max(free_edge_m - sum(opening.values()), 0.0)     # the measured free edge of record, less the open part
    res = {"owner_m2": 0.0, "owner_lm": 0.0, "held_lm": 0.0, "opening_lm": opening}
    if status == "CALCULATED" and depth is not None:
        if depth > OWNER_ALLOW:
            res["owner_m2"] = round(dec * (depth - OWNER_ALLOW), 6)
            res["owner_lm"] = round(dec, 4)
    else:
        res["held_lm"] = round(dec, 4)
    return res


# ----------------------------------------------------------------------------------------------- face record (r3)
def face_r3(face, r2_rows, deltas):
    """One integration record per floor piece. face: the T-271 input record; r2_rows: its CEILINGS_T271 rows (dicts);
    deltas: {'stair_beyond': [(slab_face, m2)], 'beams': {slab_face: {'borders': {...}, 'status', 'depth',
    'free_edge_m'}}} from the R3 extract. Returns the record with every surface, its quantity, unit and status."""
    def q(surface_prefix):
        v = 0.0
        hit = False
        for r in r2_rows:
            if r["SURFACE"].startswith(surface_prefix) and r["QTY"] != "":
                v += float(r["QTY"])
                hit = True
        return round(v, 4) if hit else None

    cls = r2_rows[0]["CLASS"] if r2_rows else None
    beyond = round(sum(m2 for _, m2 in deltas.get("stair_beyond", ())), 6)
    rec = {"face_id": face["face"], "floor": face["floor"], "room": face.get("name") or "", "class": cls,
           "floor_piece_m2": round(float(face["area_m2"]), 4), "surfaces": [], "held": []}
    horiz_r2 = q("horizontal decor ceiling")
    if cls in ("STAIR", "SHAFT", "HELD_CLASS") or horiz_r2 is None:
        for r in r2_rows:
            if r["SURFACE"].startswith("floor piece"):
                continue
            rec["surfaces"].append(_s(r["SURFACE"], r["QTY"], r["UNIT"], r["STATUS"], r["BASIS"]))
            if r["STATUS"] in (ST_H, ST_U):
                rec["held"].append(r["SURFACE"])
        if cls == "STAIR":
            rec["stair_ref"] = STAIR_REF
        return rec
    horiz = round(horiz_r2 - beyond, 4)
    if horiz < -1e-6:
        raise LedgerError(f"{face['face']}: stair beyond the face {beyond} m2 exceeds the decor ceiling {horiz_r2} m2")
    rec["surfaces"].append(_s("horizontal decor ceiling (gypsum), incl. bulkhead undersides", horiz, "m2", ST_DC,
                              "R2 less the R-CEIL-R3-1 stair parts beyond the stair face" if beyond else "R2"))
    for pre, label in (("no ceiling", "no ceiling: opening in the slab above"),
                       ("stair soffit", "stair zone (stair face of the slab plan)"),
                       ("under an open dome", "under an open dome position (Q-44 A; DCR-4)"),
                       ("held part of the ceiling", "held part of the ceiling")):
        v = q(pre)
        if v:
            st = ST_DC if pre == "no ceiling" else ST_H
            rec["surfaces"].append(_s(label, v, "m2", st, "R2"))
            if st == ST_H:
                rec["held"].append(label)
    if beyond:
        rec["surfaces"].append(_s("stair zone beyond the stair face (R-CEIL-R3-1: flight under a beam band)", beyond,
                                  "m2", ST_H, "; ".join(f"{sf} {m2:.4f}" for sf, m2 in deltas["stair_beyond"])))
        rec["held"].append("stair zone beyond the stair face")
    if beyond or q("stair soffit"):
        rec["stair_ref"] = STAIR_REF
    opening = {}
    changed = []
    beams = deltas.get("beams", {})
    own_r2 = q("bulkhead vertical faces, owner method, total") or 0.0
    held_r2 = q("bulkhead edges on CONFLICT") or 0.0
    own, held_lm = own_r2, held_r2
    for sf, b in sorted(beams.items()):
        split = bulkhead_split(b["free_edge_m"], b["borders"], b["depth"], b["status"])
        if b["status"] == "CALCULATED" and b["depth"] is not None and b["depth"] > OWNER_ALLOW:
            before = round(b["free_edge_m"] * (b["depth"] - OWNER_ALLOW), 6)
            own += split["owner_m2"] - before
            if abs(split["owner_m2"] - before) > 5e-5:
                changed.append(f"{b.get('mark') or sf} owner face {before:.4f} -> {split['owner_m2']:.4f} m2")
        elif b["status"] != "CALCULATED" or b["depth"] is None:
            held_lm += split["held_lm"] - b["free_edge_m"]
            if abs(split["held_lm"] - b["free_edge_m"]) > 5e-5:
                changed.append(f"{b.get('mark') or sf} held edge {b['free_edge_m']:.4f} -> {split['held_lm']:.4f} m")
        for k, v in split["opening_lm"].items():
            opening[k] = round(opening.get(k, 0.0) + v, 4)
    if own > 1e-9:
        rec["surfaces"].append(_s("bulkhead vertical faces, owner method (decor side only, R-CEIL-R3-2)", round(own, 4),
                                  "m2", ST_OA, "Q-48 A + Q-43; beam ledger r2 CALCULATED, D > 0.60"))
    if held_lm > 1e-9:
        rec["surfaces"].append(_s("bulkhead edges on CONFLICT / HELD / unregistered beams (decor side)",
                                  round(held_lm, 4), "m", ST_H, "Q-61 C"))
        rec["held"].append("bulkhead edges (beam status)")
    if opening.get("STAIR_ZONE"):
        rec["surfaces"].append(_s("beam edge at a stair zone: stair-well face, not a bulkhead (R-CEIL-R3-2)",
                                  opening["STAIR_ZONE"], "m", ST_H, "height and finish with the stair zone (T-281)"))
        rec["held"].append("beam edge at a stair zone")
    inside = round(sum(v for k, v in opening.items() if k != "STAIR_ZONE"), 4)
    for pre in ("ceiling edge at an opening", "cove / cornice run", "ceiling board type",
                "bulkhead vertical faces, drawing-derived candidate", "beam / column junction pieces"):
        for r in r2_rows:
            if r["SURFACE"].startswith(pre):
                basis = r["BASIS"]
                if pre == "ceiling edge at an opening" and inside:
                    basis += (f"; of which {inside:.4f} m run along beam pieces (R-CEIL-R3-2: counted here once, "
                              "no longer also as a bulkhead)")
                if pre.startswith("bulkhead vertical faces, drawing-derived"):
                    basis += "; carried from R2 unchanged (not re-split by R-CEIL-R3-2): a HELD candidate, never a total"
                rec["surfaces"].append(_s(r["SURFACE"], r["QTY"], r["UNIT"], r["STATUS"], basis))
                if r["STATUS"] in (ST_H, ST_U):
                    rec["held"].append(r["SURFACE"].split(" (")[0])
    if inside and not any(r["SURFACE"].startswith("ceiling edge at an opening") for r in r2_rows):
        raise LedgerError(f"{face['face']}: {inside} m of beam edge borders an opening that R2 lists no edge for")
    paint = round(horiz + own, 4)
    rec["surfaces"].append(_s("paintable gypsum, owner method (horizontal + owner bulkhead faces)", paint, "m2",
                              ST_OA if own > 1e-9 else ST_DC, "Q-57 A mod (6)"))
    rec["surfaces"].append(_s("concrete ceiling plaster", None, "m2", "NOT SPECIFIED", "Q-57 A mod (7)"))
    rec["changes_vs_r2"] = ([f"decor ceiling {horiz_r2:.4f} -> {horiz:.4f} m2 (stair beyond the face)"]
                            if beyond else []) + changed
    rec["horizontal_m2"], rec["owner_bulkhead_m2"], rec["paint_owner_m2"] = horiz, round(own, 4), paint
    return rec


def _s(surface, qty, unit, status, basis):
    if qty == "" or qty is None:
        qty = None
    else:
        qty = round(float(qty), 4)
    if status in (ST_H, ST_U) and qty == 0:
        raise LedgerError(f"{surface}: a HELD / UNKNOWN surface never carries 0")
    return {"surface": surface, "qty": qty, "unit": unit, "status": status, "basis": basis}
