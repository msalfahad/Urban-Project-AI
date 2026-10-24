"""CEILINGS_R2: room-by-room ceiling ledger rules (research module, unwired; any villa).

What is physically built under a slab over a floor piece, surface by surface (owner Q-57 A modified):
  1 horizontal decor ceiling (gypsum)          m2   the floor piece's polygon, at decor level, LESS what has no ceiling
                                                     plane above it (slab opening / light well / lift X box), LESS the
                                                     stair soffit over it (a stair finish, not a decor ceiling), LESS an
                                                     open dome / skylight position (HELD for the designer, never 0)
  2 board type in wet rooms                     -    moisture-resistant only where a sheet specifies it, else HELD
  4 vertical bulkhead faces                     m2   per beam piece inside the room: free edge x (D - 0.60) under the
                                                     owner method (Q-43 line + Q-48 A 0.15 decor depth), only for a
                                                     beam the CONC.BEAM ledger r2 calls CALCULATED; CONFLICT / HELD /
                                                     unregistered pieces stay HELD as lm of edge (Q-61 C), never 0
  5 cove returns / drops                        lm   HELD: no detail drawn -> run listed, no area invented
  6 paintable gypsum, owner method              m2   horizontal + owner bulkhead faces (coves / drops HELD, not in it)
  7 concrete ceiling plaster                    -    only where a sheet requires it (else NOT SPECIFIED, no quantity)
The drawing-derived bulkhead face (ceiling 0.15 under the slab soffit: free edge x (D - slab)) is a HELD candidate
while no ceiling level is printed (designer D-40), never added to a total.

Rule R-CEIL-R2-1 (proposed, any villa): a ceiling area is a SLAB-side quantity built on the FLOOR piece: start from the
floor piece's own polygon (the verified floor face, wall face to wall face), and deduct only what the slab plan above
draws over it (opening, light well, stair zone, dome opening) - each once, each with its own status - never 'ceiling =
floor area' and never a deduction the slab above does not draw. A floor piece that the slab above roofs although it has
no floor on the storey below a void is the double-height ceiling of that storey (counted on the plan whose slab closes
over it, once).
Rule R-CEIL-R2-3 (proposed, any villa): the free edge of a piece is measured segment by segment against the room's
wall faces; a segment lying on a wall face is excluded whole, every other segment counts in full (no tolerance is cut
off the ends of a crossing edge).
Rule R-CEIL-R2-2 (proposed, any villa): a bulkhead exists only where a beam piece lies inside the room's polygon below
the ceiling plane; its quantity follows the beam's own ledger status (a CONFLICT / HELD / unregistered beam -> HELD
edge, never a value picked from its candidates).
Status words: WORKFLOW_CONTROLS section 5 (DRAWING-CONFIRMED, ASSUMED - OWNER-APPROVED, HELD, UNKNOWN; VERIFIED is the
Checker's)."""
from __future__ import annotations

import math

OWNER_ALLOW = 0.60      # owner Q-43 manual line: beam allowance (m)
DECOR = 0.15            # owner Q-48 A decor depth under a beam (m)
SLAB_T = 0.16           # general-note slab thickness used only by the drawing-derived HELD candidate (Q-14)
EDGE_STEP_W = 0.06      # beam piece narrower than this: a beam face within 6 cm of the wall face (listed apart)
JUNCTION_MAX = 0.10     # m2: an unregistered piece below this is a beam / column junction, listed, no edge
EDGE_TOL = 0.012        # m: a piece edge within 12 mm of the room face is the room face

ROOM_CLASSES = ("DRY", "WET", "STAIR", "SHAFT", "HELD_CLASS")
NO_CEILING = ("OPENING", "VOID+STAIR")
STAIR_ABOVE = ("STAIR",)
UNEXPECTED = ("NOT_THIS_SLAB", "NOT_SLAB", "DETAIL", "OPENING+RING")
BEAMISH = ("BEAM_OR_COLUMN", "BEAM", "BEAM_HELD", "EDGE_HELD")

ST_DC = "DRAWING-CONFIRMED"
ST_OA = "ASSUMED - OWNER-APPROVED"
ST_H = "HELD"
ST_U = "UNKNOWN"


class LedgerError(ValueError):
    """The record cannot be measured as given (a deduction larger than the piece, a unit mix, a bad class)."""


# --------------------------------------------------------------------------------------------------- geometry part
def free_edge(piece, room, tol=EDGE_TOL):
    """Length of the piece's boundary that is NOT the room's wall face (R-CEIL-R2-3): segment by segment, a segment
    whose two ends and midpoint lie within tol of the room boundary is wall face; every other segment counts in FULL.
    (The T-147 form boundary.difference(room.boundary.buffer(tol)) cut tol off each end of every edge meeting a wall:
    -2 x 12 mm per crossing edge, e.g. 7.952 instead of 8.000 m on a 4.00 m crossing beam.)"""
    from shapely.geometry import Point as _P
    rb = room.boundary
    total = 0.0
    geoms = getattr(piece, "geoms", [piece])
    for g in geoms:
        if g.is_empty or g.geom_type != "Polygon":
            continue
        for ring in [g.exterior, *g.interiors]:
            c = list(ring.coords)
            for a, b in zip(c, c[1:]):
                m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                on = all(rb.distance(_P(p)) <= tol for p in (a, b, m))
                if not on:
                    total += math.dist(a, b)
    return total


def overlay(room, slab_faces, domes=(), edge_tol=EDGE_TOL, min_piece=0.005):
    """room: shapely polygon of the floor piece (drawing metres, already in the slab sheet's frame);
    slab_faces: iterable of (face_id, cls, polygon, member_info or None) of the slab plan ABOVE the room;
    domes: shapely polygons of open dome positions (Q-44 A) on that slab. Returns the record ledger() reads."""
    from shapely.ops import unary_union
    rec = {"area_m2": round(room.area, 6), "perimeter_m": round(room.length, 6), "above": {}, "beams": [],
           "openings": []}
    for fid, cls, poly, member in slab_faces:
        if not poly.intersects(room):
            continue
        x = poly.intersection(room)
        if x.area < min_piece:
            continue
        rec["above"][cls] = round(rec["above"].get(cls, 0.0) + x.area, 6)
        free = free_edge(x, room, edge_tol)
        if cls in BEAMISH:
            rr = list(x.minimum_rotated_rectangle.exterior.coords)
            e = sorted([math.dist(rr[0], rr[1]), math.dist(rr[1], rr[2])])
            b = {"slab_face": fid, "cls": cls, "piece_m2": round(x.area, 6), "w": round(e[0], 4),
                 "l": round(e[1], 4), "free_edge_m": round(free, 4)}
            b.update(member or {"member": None, "mark": None, "r2_status": "NO_REGISTER_ROW", "r2_depth": ""})
            rec["beams"].append(b)
        else:
            o = {"slab_face": fid, "cls": cls, "m2": round(x.area, 6), "edge_in_room_m": round(free, 4)}
            if cls.startswith("DOME"):
                op = unary_union([x.intersection(d) for d in domes]) if domes else None
                oa = op.area if op is not None else 0.0
                o["open_m2"] = round(oa, 6)
                o["ring_m2"] = round(x.area - oa, 6)
                o["open_edge_in_room_m"] = round(free_edge(op, room, edge_tol), 4) if oa > 0.05 else 0.0
            if cls in NO_CEILING or cls in STAIR_ABOVE or cls.startswith("DOME") or cls in UNEXPECTED:
                rec["openings"].append(o)
    rec["covered_m2"] = round(sum(rec["above"].values()), 6)
    return rec


# --------------------------------------------------------------------------------------------------- ledger part
def _depth(s):
    vals = set()
    for tok in str(s or "").split("/"):
        try:
            vals.add(round(float(tok), 3))
        except ValueError:
            pass
    return vals.pop() if len(vals) == 1 else None


def ledger(face, cls, cls_status, cls_basis, closed=True, held_parts=()):
    """face: record from overlay() plus 'face', 'floor', 'name' (and 'unit': 'm', the only unit accepted).
    cls: DRY / WET / STAIR / SHAFT / HELD_CLASS; cls_status / cls_basis: the evidence for the class.
    closed: False for an open zone whose wall run is not a closed room perimeter (no cove run listed).
    held_parts: [(what, m2, basis)] parts of the piece whose ceiling exists but whose type / height is not established
    (for example the top of a stair well): deducted from the decor ceiling once and listed HELD, never 0.
    Returns (rows, totals). Every HELD row carries a quantity or names why it has none; nothing HELD becomes 0."""
    if face.get("unit", "m") != "m":
        raise LedgerError(f"{face.get('face')}: unit {face.get('unit')!r} - convert to metres before the ledger")
    if cls not in ROOM_CLASSES:
        raise LedgerError(f"{face.get('face')}: class {cls!r} not in {ROOM_CLASSES}")
    A = float(face["area_m2"])
    rows, tot = [], {}

    def add(surface, qty, unit, method, status, basis, note=""):
        rows.append({"FACE": face["face"], "FLOOR": face["floor"], "ROOM": face.get("name") or "", "CLASS": cls,
                     "SURFACE": surface, "QTY": "" if qty is None else round(qty, 4), "UNIT": unit,
                     "METHOD": method, "STATUS": status, "BASIS": basis, "NOTE": note})

    def t(k, v):
        tot[k] = tot.get(k, 0.0) + v

    no_ceiling = stair = dome = unexpected = 0.0
    edge_open = 0.0
    for o in face.get("openings", ()):
        if o["cls"] in NO_CEILING:
            no_ceiling += o["m2"]
            edge_open += o.get("edge_in_room_m", 0.0)
        elif o["cls"] in STAIR_ABOVE:
            stair += o["m2"]
        elif o["cls"].startswith("DOME"):
            dome += o.get("open_m2", 0.0)
            edge_open += o.get("open_edge_in_room_m", 0.0)
        else:
            unexpected += o["m2"]
    held_part = sum(m2 for _, m2, _ in held_parts)
    ded = no_ceiling + stair + dome + unexpected + held_part
    if ded > A + 1e-6:
        raise LedgerError(f"{face['face']}: deductions {ded:.4f} m2 exceed the floor piece {A:.4f} m2 (counted twice?)")
    gap = A - float(face.get("covered_m2", A))
    add("floor piece (plan area, wall face to wall face)", A, "m2", "both", ST_DC, cls_basis,
        f"slab-plan overlay covers {face.get('covered_m2', A):.4f} m2; uncovered line-work residual {gap:+.4f} m2 "
        "(roofed: stays in the ceiling, named)")
    t("piece_" + cls, A)

    if cls in ("STAIR", "SHAFT"):
        if stair:
            add("stair soffit over the flights (stair finish, not a decor ceiling)", stair, "m2", "both", ST_H,
                "slab plan STAIR zone above; no soffit finish printed", "stair finish line")
        if no_ceiling:
            add("no ceiling: slab opening above (lift / shaft X box, light well)", no_ceiling, "m2", "both", ST_DC,
                "slab plan OPENING above")
        rest = A - stair - no_ceiling - dome - unexpected
        if rest > 0.005:
            add(f"{cls.lower()} top under the slab (landing / shaft top, not a room ceiling)", rest, "m2", "both", ST_H,
                "no finish printed for a shaft / stair top", "kept apart from the decor ceiling")
        t("apart_" + cls, A)
        return rows, tot

    if cls == "HELD_CLASS":
        add("plan area under the slab, ceiling type not decidable (class HELD: see basis)",
            A - ded, "m2", "both", ST_H, cls_basis, "measured, never 0; Q-68 C if it is exterior")
        t("held_class_m2", A - ded)
        lm = sum(b["free_edge_m"] for b in face.get("beams", ()))
        if lm:
            add("bulkhead edges of beam pieces over this held piece", lm, "m", "both", ST_H,
                "class HELD: no bulkhead face is decided where the ceiling type is not",
                "; ".join(f"{b.get('mark') or b['slab_face']} {b.get('r2_status')} ({b['free_edge_m']:.3f} m)"
                          for b in face["beams"]))
            t("held_bulk_lm_heldclass", lm)
        return rows, tot

    if no_ceiling:
        add("no ceiling here: opening in the slab above (light well / lift / court void)", no_ceiling, "m2", "both",
            ST_DC, "slab plan OPENING / VOID face above", "deducted once, not 0")
    if stair:
        add("stair soffit above (stair finish, not a decor ceiling)", stair, "m2", "both", ST_H,
            "slab plan STAIR zone above", "deducted from the decor ceiling")
    if dome:
        add("under an open dome / skylight position: no ceiling plane designed", dome, "m2", "both", ST_H,
            "Q-44 A open skylight; designer DCR-4", "held for the designer, never 0")
    if unexpected:
        add("slab-plan face of another storey / detail over the piece", unexpected, "m2", "both", ST_U,
            "overlay found a non-slab face above", "investigate; not in the ceiling")
    for what, m2, basis in held_parts:
        add(f"held part of the ceiling: {what}", m2, "m2", "both", ST_H, basis, "deducted once from the decor ceiling")
    t("held_part_m2", held_part)
    horiz = A - ded
    t("deduct_no_ceiling", no_ceiling)
    t("deduct_stair", stair)
    t("held_dome", dome)
    add("horizontal decor ceiling (gypsum), incl. bulkhead undersides", horiz, "m2", "both", ST_DC,
        "Q-57 A mod (1); Q-48 A; R-CEIL-R2-1",
        "gypsum board (dry room)" if cls == "DRY" else
        "board type HELD: moisture-resistant only where a sheet specifies it; none does")
    t("horiz_" + cls, horiz)
    if cls == "WET":
        add("ceiling board type (wet room)", None, "m2", "both", ST_H,
            "Q-57 A mod (2): moisture-resistant board only where specified", f"area {horiz:.4f} m2 measured above")

    own_m2 = own_lm = 0.0
    held_lm, held_cand, held_names, junctions = 0.0, 0.0, [], 0
    dwg_m2 = 0.0
    steps = 0.0
    for b in face.get("beams", ()):
        D = _depth(b.get("r2_depth"))
        st = b.get("r2_status")
        if b.get("member") is None:
            if b["cls"] in ("BEAM_HELD", "EDGE_HELD") or b["piece_m2"] >= JUNCTION_MAX:
                held_lm += b["free_edge_m"]
                held_names.append(f"{b['slab_face']} {b['cls']} no register row ({b['free_edge_m']:.3f} m)")
            else:
                junctions += 1
            continue
        if st != "CALCULATED" or D is None or b["cls"] == "EDGE_HELD":
            held_lm += b["free_edge_m"]
            if D is not None and D > OWNER_ALLOW:
                held_cand += b["free_edge_m"] * (D - OWNER_ALLOW)
            held_names.append(f"{b.get('mark')} {b['member']} {st} D {b.get('r2_depth') or '?'} "
                              f"({b['free_edge_m']:.3f} m)")
            continue
        if D > OWNER_ALLOW and b["free_edge_m"] > 0:
            h = D - OWNER_ALLOW
            m2 = b["free_edge_m"] * h
            own_m2 += m2
            own_lm += b["free_edge_m"]
            if b["w"] < EDGE_STEP_W:
                steps += m2
            add(f"bulkhead vertical face, owner method: {b.get('mark')} D {D:.2f} ({b['member']})", m2, "m2",
                "owner manual (Q-43 line, Q-48 A)", ST_OA,
                f"free edge {b['free_edge_m']:.3f} m x (D - {OWNER_ALLOW:.2f}) {h:.2f} m; piece {b['w']:.3f} x "
                f"{b['l']:.3f} m; beam ledger r2 CALCULATED",
                "edge step: beam face within 6 cm of the wall face" if b["w"] < EDGE_STEP_W else "")
        if D > SLAB_T:
            dwg_m2 += b["free_edge_m"] * (D - SLAB_T)
    if own_m2:
        add("bulkhead vertical faces, owner method, total", own_m2, "m2", "owner manual", ST_OA,
            f"{own_lm:.3f} m of free beam edge", f"of which edge steps {steps:.4f} m2")
    if dwg_m2:
        add("bulkhead vertical faces, drawing-derived candidate (ceiling 0.15 under the slab soffit)", dwg_m2, "m2",
            "drawing-derived", ST_H, "no ceiling level printed (designer D-40); candidate, never in a total")
    if held_lm:
        add("bulkhead edges on CONFLICT / HELD / unregistered beam pieces", held_lm, "m", "both", ST_H,
            "Q-61 C; beam ledger r2 status", "; ".join(held_names) +
            (f"; owner-method candidate {held_cand:.4f} m2 (not in any total)" if held_cand else ""))
    if junctions:
        add("beam / column junction pieces without a register row (< 0.10 m2)", junctions, "nr", "both", ST_DC,
            "listed only: no free edge of their own", "")
    t("own_bulk_m2", own_m2)
    t("dwg_bulk_cand_m2", dwg_m2)
    t("held_bulk_lm", held_lm)
    if edge_open:
        add("ceiling edge at an opening (drop / return)", edge_open, "m", "both", ST_H,
            "Q-57 A mod (5): no edge detail printed", "length measured, height HELD")
        t("edge_open_lm", edge_open)
    add("cove / cornice run at the wall (only if a detail is approved)",
        float(face["perimeter_m"]) if closed else None, "m", "both", ST_H,
        "no cove or cornice detail drawn; never a 0.10 m strip by convention",
        "room perimeter at the wall faces" if closed else "open zone: the run is not a closed room perimeter")
    if closed:
        t("cove_lm_" + cls, float(face["perimeter_m"]))
    paint = horiz + own_m2
    add("paintable gypsum surfaces, owner method (horizontal + bulkhead faces)", paint, "m2", "owner manual",
        ST_OA if own_m2 else ST_DC, "Q-57 A mod (6)", "coves and opening drops HELD, not included")
    t("paint_own_" + cls, paint)
    add("concrete ceiling plaster", None, "m2", "both", "NOT SPECIFIED",
        "Q-57 A mod (7): only where a sheet requires it; none does", "no item, not a zero quantity")
    return rows, tot


def reconcile(piece_m2, ceiling_m2, named):
    """piece -> ceiling in units: named = [(what, m2), ...] deductions (+) or additions (-) that explain the difference.
    Returns (residual_m2, rows). A residual above 0.001 m2 is returned for the caller to name; it is never absorbed."""
    rows = [("floor piece", round(piece_m2, 4))]
    v = piece_m2
    for what, m2 in named:
        v -= m2
        rows.append((what, round(-m2, 4)))
    rows.append(("horizontal ceiling", round(ceiling_m2, 4)))
    return round(v - ceiling_m2, 6), rows
