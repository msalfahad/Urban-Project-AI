"""T-309: pool membrane and protection screed, face by face on a verified pool shell (every villa; unwired research).

What the printed pool detail fixes, and what it leaves open (ENGINEERING_REASONING_STANDARD s.2.1 / s.3):

    water | RC wall | protection screed | membrane | soil          (outer wall faces, drawn to the wall top)
    water | RC base | protection screed | membrane | blinding      (under the base, to the outer face of the wall layers)

- A printed layer is measured only on the shell faces its hatch is drawn on (COVERED); a face the section shows with no
  hatch is NOT_COVERED with that sheet evidence; a face where two documents disagree on the layer's end (for example a
  pool upstand left exposed above a deck by the architectural cut while the structural detail draws the layer to the wall
  top) is UNRESOLVED: blank quantity, its geometric bound beside it, never 0 and never silently included.
- Contract measure of the membrane (m2) = the protected concrete face it covers (base underside + outer wall faces from
  the base underside to the drawn end), the convention of the merged foundation waterproofing family. The layer's own
  developed surface (offset by the screed in front of the concrete) is reported beside it as information for procurement,
  never added to the measure.
- Screed (m3) = exact solid of the drawn layer: the vertical band in plan (straight L t, arc theta/2 ((r+t)^2 - r^2),
  each square convex corner t^2) x its height from the base underside to its end, plus the horizontal sheet under the
  base, which runs to the outer face of the vertical screed (footprint + all bands) x t.
- The printed word ('INSULATION MEMBRANE') fixes a thickness and a material word, not a function: a function label is
  refused unless it carries its own source; the family stays 'pool membrane' with function HELD (consultant S8.2).
- Units: metres only (a mm input is refused, not converted); a printed layer with thickness 0 is refused; a layer whose
  thickness is not printed (None) yields None = HELD.

Rule R-T309-1 (PROJECT-INDEPENDENT research rule, provenance T-309 / T-183 r2 / T-303): a pool / tank layer is booked
face by face on the verified shell; each shell face once, in exactly one status; an upstand above an adjoining finished
level is its own face and its layer is UNRESOLVED while the documents disagree on the termination.
"""

from __future__ import annotations

import math

COVERED, NOT_COVERED, UNRESOLVED = "COVERED", "NOT_COVERED", "UNRESOLVED"
DRAWING_CONFIRMED, HELD = "DRAWING-CONFIRMED", "HELD"
TOL = 1e-9


class RefusedInput(ValueError):
    """An input the rules refuse (never silently repaired)."""


def _check_function(function):
    if function is None:
        return {"label": None, "status": HELD, "source": None}
    if not isinstance(function, dict) or not function.get("label") or not function.get("source"):
        raise RefusedInput("a layer function label needs its own source (drawing note, specification, consultant)")
    return {"label": function["label"], "status": DRAWING_CONFIRMED, "source": function["source"]}


def _thickness(name, t):
    if t is None:
        return None
    if t <= 0:
        raise RefusedInput(f"{name}: a printed layer cannot have thickness {t}; an unprinted one is None (HELD)")
    if t > 0.5:
        raise RefusedInput(f"{name}: {t} m is not a layer thickness (mm passed as m?)")
    return float(t)


def _band_plan(seg, t):
    """Plan area of a layer band of thickness t in front of one outer-face segment (square corners owned by it)."""
    if seg["kind"] == "STRAIGHT":
        a = seg["length"] * t
    elif seg["kind"] == "ARC":
        r, theta = seg["r"], seg["length"] / seg["r"]
        a = theta / 2.0 * ((r + t) ** 2 - r ** 2)
    else:
        raise RefusedInput(f"segment {seg['id']}: unknown kind {seg['kind']}")
    return a + seg.get("square_corners", 0) * t * t


def _offset_length(seg, t):
    """Length of the segment's face offset outward by t (square corners add 2 t each)."""
    if seg["kind"] == "STRAIGHT":
        base = seg["length"]
    else:
        base = seg["length"] / seg["r"] * (seg["r"] + t)
    return base + seg.get("square_corners", 0) * 2.0 * t


def validate(shell):
    if shell.get("unit") != "m":
        raise RefusedInput(f"unit {shell.get('unit')!r} refused: metres only (convert at the source, by its print)")
    lv = shell["levels"]
    if shell.get("wall_face_basis") != "STRUCTURAL":
        raise RefusedInput("outer / water wall faces are measured on the structural shell (rim -> structural base top); "
                           "a finished depth is never a concrete face")
    if not (lv["base_underside"] < lv["base_top_structural"] < lv["rim"]):
        raise RefusedInput("levels out of order: base underside < structural base top < rim")
    if abs((lv["base_top_structural"] - lv["base_underside"]) - shell["base_t"]) > 1e-6:
        raise RefusedInput("base thickness disagrees with the levels")
    segs = shell["segments"]
    ids = [s["id"] for s in segs]
    if len(set(ids)) != len(ids):
        raise RefusedInput("a segment id is given twice")
    for s in segs:
        if s["length"] <= 0:
            raise RefusedInput(f"segment {s['id']}: length {s['length']}")
        if s["edge"] not in ("DECK", "NO_DECK"):
            raise RefusedInput(f"segment {s['id']}: edge must be DECK or NO_DECK")
    perim = sum(s["length"] for s in segs)
    if abs(perim - shell["outer_perimeter"]) > 1e-6:
        raise RefusedInput(f"segments {perim:.6f} m do not close the outer perimeter {shell['outer_perimeter']:.6f} m")
    if shell["water_area"] >= shell["outer_area"]:
        raise RefusedInput("water area must be inside the outer footprint")
    return perim


def ledger(shell, layers, coverage, function=None):
    """Face-by-face ledger.

    shell: verified shell geometry (outer_area, outer_perimeter, water_area, water_perimeter, base_t, levels, segments).
    layers: {'screed_t': m or None, 'membrane_t': m or None}.
    coverage: the drawn hatch extent: {'base_underside': bool, 'outer_walls': bool, 'outer_walls_to': 'WALL_TOP' | level,
               'water_faces': bool, 'wall_top': bool, 'source': str}.
    """
    validate(shell)
    fn = _check_function(function)
    ts = _thickness("screed", layers.get("screed_t"))
    tm = _thickness("membrane", layers.get("membrane_t"))
    lv = shell["levels"]
    if coverage.get("water_faces") or coverage.get("wall_top"):
        # a hatch on the water side would be its own family (tanking / lining); not this detail
        raise RefusedInput("this ledger books an outer protective layer; a water-face or wall-top hatch is another family")
    top = lv["rim"] if coverage.get("outer_walls_to") in (None, "WALL_TOP") else float(coverage["outer_walls_to"])
    if not (lv["base_underside"] < top <= lv["rim"] + TOL):
        raise RefusedInput("the drawn layer end must lie between the base underside and the rim")
    deck = lv.get("deck_finish")
    wall_h = lv["rim"] - lv["base_top_structural"]
    band = shell["outer_area"] - shell["water_area"]
    src = coverage.get("source", "")

    rows = []

    def add(face_id, face, m2, status, membrane_m2, screed_m3, basis, bound=None):
        rows.append({"face_id": face_id, "face": face, "shell_m2": m2, "status": status,
                     "membrane_m2": membrane_m2, "membrane_bound_m2": bound,
                     "screed_m3": screed_m3, "basis": basis})

    # base underside
    hz_plan = shell["outer_area"] + (sum(_band_plan(s, ts) for s in shell["segments"]) if ts else 0.0)
    if coverage.get("base_underside"):
        add("BASE-U", "base underside", shell["outer_area"], COVERED,
            shell["outer_area"] if tm is not None else None,
            hz_plan * ts if ts is not None else None,
            f"hatch under the whole base ({src}); screed sheet plan {hz_plan:.6f} m2 runs to the outer face of the "
            f"vertical screed")
    else:
        add("BASE-U", "base underside", shell["outer_area"], NOT_COVERED, None, None, f"no hatch under the base ({src})")

    # outer faces per segment: covered part, upstand part, part above the drawn end
    for s in shell["segments"]:
        h_full = lv["rim"] - lv["base_underside"]
        pieces = []
        if not coverage.get("outer_walls"):
            pieces.append(("all", lv["base_underside"], lv["rim"], NOT_COVERED, "no hatch on the outer wall face"))
        else:
            split = top
            if s["edge"] == "DECK" and deck is not None and deck < top - TOL:
                pieces.append(("below-deck", lv["base_underside"], deck, COVERED, "hatch drawn; face below the deck finish"))
                pieces.append(("upstand", deck, top, UNRESOLVED,
                               "upstand above the deck finish: the detail draws the layer to its end, the deck section "
                               "leaves the face exposed; termination not detailed (blank, bound beside)"))
            else:
                pieces.append(("to-end", lv["base_underside"], split, COVERED, "hatch drawn to its end"))
            if top < lv["rim"] - TOL:
                pieces.append(("above-end", top, lv["rim"], NOT_COVERED, "above the drawn end of the hatch"))
        for tag, z0, z1, st, why in pieces:
            h = z1 - z0
            m2 = s["length"] * h
            screed = _band_plan(s, ts) * h if (ts is not None and st == COVERED) else None
            if st == COVERED:
                add(f"OUT-{s['id']}-{tag}", f"outer face {s['id']} {z0:+.2f} -> {z1:+.2f}", m2, st,
                    m2 if tm is not None else None, screed, f"{why} ({src})")
            elif st == UNRESOLVED:
                add(f"OUT-{s['id']}-{tag}", f"outer face {s['id']} {z0:+.2f} -> {z1:+.2f}", m2, st, None, None,
                    f"{why} ({src})", bound=[0.0, m2])
                rows[-1]["screed_bound_m3"] = [0.0, _band_plan(s, ts) * h] if ts is not None else None
            else:
                add(f"OUT-{s['id']}-{tag}", f"outer face {s['id']} {z0:+.2f} -> {z1:+.2f}", m2, st, None, None, why)
        assert abs(sum(p[2] - p[1] for p in pieces) - h_full) < 1e-9

    # water faces and wall top: not covered (sheet evidence: the hatch lies outside the concrete only)
    add("WATER-FLOOR", "water floor on the structural base top", shell["water_area"], NOT_COVERED, None, None,
        f"no hatch on the water side ({src})")
    add("WATER-WALLS", "water wall faces, structural base top -> rim", shell["water_perimeter"] * wall_h, NOT_COVERED,
        None, None, f"no hatch on the water side ({src})")
    add("WALL-TOP", "wall top (coping surface)", band, NOT_COVERED, None, None, f"no hatch on the wall top ({src})")

    return _summarise(shell, rows, ts, tm, fn, top, wall_h, band)


def _summarise(shell, rows, ts, tm, fn, top, wall_h, band):
    lv = shell["levels"]
    total = (shell["outer_area"] + shell["outer_perimeter"] * (lv["rim"] - lv["base_underside"])
             + shell["water_area"] + shell["water_perimeter"] * wall_h + band)
    by = {}
    for r in rows:
        by[r["status"]] = by.get(r["status"], 0.0) + r["shell_m2"]
    keys = [r["face_id"] for r in rows]
    if len(set(keys)) != len(keys):
        raise RefusedInput("a shell face is booked twice")
    residual = total - sum(by.values())
    cov = [r for r in rows if r["status"] == COVERED]
    unres = [r for r in rows if r["status"] == UNRESOLVED]
    mem = None if tm is None else sum(r["membrane_m2"] for r in cov)
    scr = None if ts is None else sum(r["screed_m3"] for r in cov)
    # information only: the membrane's own inner surface (offset by the screed in front of the concrete)
    info = None
    if tm is not None:
        off = ts or 0.0
        hz = shell["outer_area"] + sum(_band_plan(s, off) for s in shell["segments"])
        vert = sum(_offset_length(s, off) for s in shell["segments"]) * (top - (lv["base_underside"] - off))
        info = {"membrane_inner_surface_m2": hz + vert,
                "basis": "membrane face against the screed: horizontal sheet to offset t_screed, vertical at offset "
                         "t_screed from the underside of the horizontal screed to the drawn end, upstand included; "
                         "INFORMATION (procurement side), never the measure"}
    return {
        "rows": rows,
        "closure": {"shell_total_m2": total, "by_status_m2": by, "residual_m2": residual},
        "membrane": {"family": "pool membrane", "function": fn, "thickness_m": tm, "unit": "m2",
                     "quantity": mem, "status": DRAWING_CONFIRMED if mem is not None else HELD,
                     "unresolved_bound_m2": [0.0, sum(r["membrane_bound_m2"][1] for r in unres)],
                     "layer_surface_info": info},
        "screed": {"family": "pool protection screed", "thickness_m": ts, "unit": "m3", "quantity": scr,
                   "face_m2": sum(r["shell_m2"] for r in cov) if ts is not None else None,
                   "status": DRAWING_CONFIRMED if scr is not None else HELD,
                   "unresolved_bound_m3": [0.0, sum((r.get("screed_bound_m3") or [0, 0])[1] for r in unres)]},
    }


def book(ledger_out, face_id, layer):
    """Booking a layer on a face the hatch does not cover is refused (a hatch is never extended)."""
    for r in ledger_out["rows"]:
        if r["face_id"] == face_id:
            if r["status"] != COVERED:
                raise RefusedInput(f"{layer} on {face_id} refused: face status {r['status']}")
            return r
    raise RefusedInput(f"{face_id}: no such shell face")


def consumer_lines(ledger_out, element_id, source):
    """Lane I consumer shape (proposed lines; nothing written into any candidate)."""
    m, s = ledger_out["membrane"], ledger_out["screed"]
    return [
        {"key": f"WP.POOL_TANK.POOL_MEMBRANE[m2]/{element_id}/BASE_AND_OUTER_WALLS", "unit": "m2",
         "quantity": m["quantity"], "status": m["status"], "held_part_bound": m["unresolved_bound_m2"],
         "function": m["function"], "source": source},
        {"key": f"WP.POOL_TANK.POOL_PROTECTION_SCREED[m3]/{element_id}/BASE_AND_OUTER_WALLS", "unit": "m3",
         "quantity": s["quantity"], "status": s["status"], "held_part_bound": s["unresolved_bound_m3"],
         "face_m2": s["face_m2"], "source": source},
    ]


def d_shell(back, r, wall_t, base_t, levels, back_edge="NO_DECK", side_edge="DECK", arc_edge="DECK"):
    """Helper: a D-shaped shell (straight back, two straight sides of length r, half circle radius r), metres."""
    ri = r - wall_t
    outer_area = back * r + math.pi * r * r / 2.0
    water_area = (back - 2 * wall_t) * ri + math.pi * ri * ri / 2.0
    segs = [{"id": "BACK", "kind": "STRAIGHT", "length": back, "edge": back_edge, "square_corners": 2},
            {"id": "SIDE-1", "kind": "STRAIGHT", "length": r, "edge": side_edge},
            {"id": "SIDE-2", "kind": "STRAIGHT", "length": r, "edge": side_edge},
            {"id": "ARC", "kind": "ARC", "length": math.pi * r, "r": r, "edge": arc_edge}]
    return {"unit": "m", "wall_face_basis": "STRUCTURAL", "outer_area": outer_area,
            "outer_perimeter": back + 2 * r + math.pi * r, "water_area": water_area,
            "water_perimeter": (back - 2 * wall_t) + 2 * ri + math.pi * ri,
            "base_t": base_t, "levels": levels, "segments": segs}
