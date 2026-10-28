"""T-321 roof build-up ledger (research only, read by no method): zone x layer, any villa.

Physical element (ERS s.2 step 1). A flat roof / terrace is a stack of layers on the structural slab, each its own item
in its own unit, owned by ONE trade:

  FALLS_SCREED   screed to falls (thickness t0 at the outlet + the falls rise z(p)), m2 / m3      ROOFING (B13-01)
  MEMBRANE       waterproofing membrane + its upturn strip (m2 + lm)                              WATERPROOFING (B8-06)
  INSULATION     thermal insulation board / layer, m2                                             ROOFING (B13-01)
  PROTECTION     protection / separation layer over the membrane or insulation, m2                ROOFING (B13-01)
  FINISH         the walking surface (tiles, paving), m2                                          FLOOR FINISH

A layer EXISTS on a zone only by evidence: printed on a drawing (section, roof detail, note), or an owner rule that puts
it on every roof (then ASSUMED - OWNER-APPROVED with the rule id). With neither, its scope is UNKNOWN: a row is still
written (never dropped, never 0). A layer's plan AREA is measured to its OWN drawn edge (Checker rule 2026-10-23 21:05):
the finish to the designer's finish hatch, screed / membrane / insulation to the wall or parapet face; an edge with two
physical readings stays a range with its cause named. A THICKNESS comes only from a print (never a default): unprinted
-> HELD, and so is every volume that needs it. The upturn of a layer is its own item in lm (with its printed height, else
HELD), never folded into the flat m2. The membrane is carried here as a cross-reference only (its lines belong to the
waterproofing trade); a B13-01 row may never carry the membrane (refused: double count with WP).

Slope: a surface at fall f has area plan x sqrt(1 + f^2) (1 % adds 0.005 %); reported beside the plan area.
Units: every length in metres; `scale` converts drawing units (mm -> 0.001) before anything is measured.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

LAYERS = ("FALLS_SCREED", "MEMBRANE", "INSULATION", "PROTECTION", "FINISH")
OWNER_TRADE = {"FALLS_SCREED": "ROOFING B13-01", "MEMBRANE": "WATERPROOFING B8-06", "INSULATION": "ROOFING B13-01",
               "PROTECTION": "ROOFING B13-01", "FINISH": "FLOOR FINISH"}
B13_LAYERS = ("FALLS_SCREED", "INSULATION", "PROTECTION")
EDGE_BASIS = {"FALLS_SCREED": "face", "MEMBRANE": "face", "INSULATION": "face", "PROTECTION": "face",
              "FINISH": "finish"}
STATUSES = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "HELD", "UNKNOWN")


class Refused(ValueError):
    """an input the ledger must not accept (wrong trade, default thickness, folded upturn, held as 0)."""


def shoelace(pts):
    """signed-free polygon area of a closed vertex list (metres)."""
    n = len(pts)
    return abs(sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))) / 2.0


def arc_points(centre, r, a0_deg, a1_deg, step_deg=0.25):
    """points of a counter-clockwise arc from a0 to a1 (degrees), end points exact."""
    n = max(2, int(math.ceil(abs(a1_deg - a0_deg) / step_deg)))
    return [(centre[0] + r * math.cos(math.radians(a0_deg + (a1_deg - a0_deg) * k / n)),
             centre[1] + r * math.sin(math.radians(a0_deg + (a1_deg - a0_deg) * k / n))) for k in range(n + 1)]


def outline(spec, scale=1.0):
    """vertex list from a spec: items are (x, y) points or ('ARC', (cx, cy), r, a0, a1); scaled to metres.
    The arc segment is integrated exactly: its circular-segment area is added to the chord polygon."""
    pts, bulges = [], []
    for it in spec:
        if isinstance(it, (list, tuple)) and it and it[0] == "ARC":
            _, c, r, a0, a1 = it[:5]
            pts.extend(arc_points((c[0] * scale, c[1] * scale), r * scale, a0, a1))
        else:
            pts.append((it[0] * scale, it[1] * scale))
    out = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, out[-1]) > 1e-12:
            out.append(p)
    if math.dist(out[0], out[-1]) < 1e-12:
        out.pop()
    return out


def exact_area(spec, scale=1.0):
    """area of an outline with ARC items, the arcs integrated exactly (chord polygon + circular segments)."""
    chord = []
    seg = 0.0
    for it in spec:
        if isinstance(it, (list, tuple)) and it and it[0] == "ARC":
            _, c, r, a0, a1 = it[:5]
            p0 = (c[0] + r * math.cos(math.radians(a0)), c[1] + r * math.sin(math.radians(a0)))
            p1 = (c[0] + r * math.cos(math.radians(a1)), c[1] + r * math.sin(math.radians(a1)))
            chord.extend([p0, p1])
            th = math.radians(abs(a1 - a0))
            seg += r * r * (th - math.sin(th)) / 2.0
        else:
            chord.append(tuple(it))
    base = shoelace(_dedupe(chord))
    return (base + seg * _seg_sign(spec)) * scale * scale


def _dedupe(pts):
    out = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, out[-1]) > 1e-12:
            out.append(p)
    if math.dist(out[0], out[-1]) < 1e-12:
        out.pop()
    return out


def _seg_sign(spec):
    """+1 when the arcs bulge outward (convex corner of the outline), -1 inward: decided by comparing the sampled
    polygon with the chord polygon (both in drawing units, no tolerance needed: an arc of radius r moves the area by a
    finite segment)."""
    sampled = shoelace(outline(spec))
    chord = []
    for it in spec:
        if isinstance(it, (list, tuple)) and it and it[0] == "ARC":
            _, c, r, a0, a1 = it[:5]
            chord.extend([(c[0] + r * math.cos(math.radians(a0)), c[1] + r * math.sin(math.radians(a0))),
                          (c[0] + r * math.cos(math.radians(a1)), c[1] + r * math.sin(math.radians(a1)))])
        else:
            chord.append(tuple(it))
    return 1.0 if sampled >= shoelace(_dedupe(chord)) else -1.0


def slope_factor(fall):
    if fall is None:
        return None
    if not (0 < fall < 0.2):
        raise Refused(f"fall {fall!r} outside 0 .. 20 %: a gradient is a ratio, not a thickness or a percentage number")
    return math.sqrt(1.0 + fall * fall)


@dataclass
class Layer:
    name: str
    scope: str                    # PRINTED / OWNER_RULE / UNKNOWN
    source: str                   # drawing reference or rule id; for UNKNOWN: what was searched
    thickness_m: float | None = None
    thickness_source: str = ""
    upturn_height_m: float | None = None
    upturn_source: str = ""
    booked_trade: str | None = None   # the trade a line puts it in (checked against OWNER_TRADE)
    line_id: str | None = None        # candidate line carrying it, or None (NO LINE)


@dataclass
class Zone:
    zone_id: str
    face_area_m2: tuple            # (lo, hi) to wall / parapet faces
    finish_area_m2: tuple | None   # (lo, hi) to the designer's finish edge, None: no finish edge drawn
    footprints: dict = field(default_factory=dict)   # name -> (area m2, {layer: status}) e.g. dome footprints
    upturn_m: tuple = (0.0, 0.0)   # (lo, hi) lm of vertical faces round the zone (parapet + walls + dividers)
    fall: float | None = None
    fall_source: str = ""
    drains_drawn: bool = True
    held: str = ""                 # zone-level hold (e.g. outline not on any plan; owner Q-34)


def _status(layer: Layer, zone: Zone, qty_drawn: bool):
    if zone.held:
        return "HELD"
    if layer.scope == "UNKNOWN":
        return "UNKNOWN"
    if layer.scope == "OWNER_RULE":
        return "ASSUMED - OWNER-APPROVED"
    return "DRAWING-CONFIRMED" if qty_drawn else "HELD"


def check_layer(layer: Layer):
    """refusals that hold for any villa."""
    if layer.name not in LAYERS:
        raise Refused(f"unknown layer {layer.name!r}")
    if layer.booked_trade is not None and layer.booked_trade != OWNER_TRADE[layer.name]:
        raise Refused(f"{layer.name} booked under {layer.booked_trade!r}: its one owner trade is "
                      f"{OWNER_TRADE[layer.name]!r} (a membrane booked as insulation / roofing is a double count with "
                      f"the waterproofing line)")
    if layer.thickness_m is not None and not layer.thickness_source:
        raise Refused(f"{layer.name}: thickness {layer.thickness_m} has no printed source: an unprinted thickness is "
                      f"HELD (D-39), never a default")
    if layer.thickness_m is not None and layer.thickness_m <= 0:
        raise Refused(f"{layer.name}: thickness {layer.thickness_m} m is not a thickness (held is never 0)")
    if layer.upturn_height_m is not None and not layer.upturn_source:
        raise Refused(f"{layer.name}: upturn height {layer.upturn_height_m} has no source")


def zone_ledger(zone: Zone, layers: list[Layer]):
    """one row per layer of the zone. Quantities: plan area range (by the layer's edge basis), sloped surface,
    footprints per layer (their own status), upturn lm, thickness and volume (only with a printed thickness;
    the falls screed volume additionally needs the rise field, given separately)."""
    if zone.face_area_m2 is not None and zone.face_area_m2[0] <= 0 and not zone.held:
        raise Refused(f"{zone.zone_id}: a measured zone with area <= 0 (held is never 0)")
    names = [l.name for l in layers]
    if len(set(names)) != len(names):
        raise Refused(f"{zone.zone_id}: a layer listed twice {names}")
    rows = []
    sf = slope_factor(zone.fall) if zone.fall is not None else None
    for layer in layers:
        check_layer(layer)
        basis = EDGE_BASIS[layer.name]
        area = zone.face_area_m2 if basis == "face" else zone.finish_area_m2
        drawn = area is not None and not zone.held
        st = _status(layer, zone, drawn)
        row = {"zone": zone.zone_id, "layer": layer.name, "owner_trade": OWNER_TRADE[layer.name],
               "in_b13_01": layer.name in B13_LAYERS, "scope": layer.scope, "scope_source": layer.source,
               "edge_basis": basis,
               "plan_area_lo": None if (area is None or zone.held) else round(area[0], 4),
               "plan_area_hi": None if (area is None or zone.held) else round(area[1], 4),
               "sloped_area_lo": None, "sloped_area_hi": None,
               "footprints": {k: {"area_m2": round(v[0], 4), "status": v[1].get(layer.name, "UNKNOWN")}
                              for k, v in zone.footprints.items()},
               "upturn_lm_lo": None, "upturn_lm_hi": None, "upturn_height_m": layer.upturn_height_m,
               "upturn_status": None,
               "thickness_m": layer.thickness_m, "thickness_status": "PRINTED" if layer.thickness_m else "HELD",
               "volume_lo_m3": None, "volume_hi_m3": None,
               "line_id": layer.line_id, "line_state": "IN_LINE" if layer.line_id else "NO_LINE",
               "status": st, "zone_hold": zone.held or ""}
        if row["plan_area_lo"] is not None and sf is not None:
            row["sloped_area_lo"] = round(area[0] * sf, 4)
            row["sloped_area_hi"] = round(area[1] * sf, 4)
        if layer.name in ("MEMBRANE", "PROTECTION", "INSULATION", "FINISH", "FALLS_SCREED") and not zone.held:
            if layer.upturn_height_m is not None or layer.name == "MEMBRANE":
                row["upturn_lm_lo"], row["upturn_lm_hi"] = round(zone.upturn_m[0], 4), round(zone.upturn_m[1], 4)
                row["upturn_status"] = "DRAWING-CONFIRMED length" + ("" if layer.upturn_height_m else
                                                                    ", height HELD")
        if layer.thickness_m and row["plan_area_lo"] is not None and layer.name != "FALLS_SCREED":
            row["volume_lo_m3"] = round(area[0] * layer.thickness_m, 4)
            row["volume_hi_m3"] = round(area[1] * layer.thickness_m, 4)
        rows.append(row)
    return rows


def refuse_folded_upturn(flat_m2, upturn_lm, height_m, booked_m2):
    """an upturn strip is its own item: a flat line whose m2 equals flat + upturn x height is refused."""
    if height_m and abs(booked_m2 - (flat_m2 + upturn_lm * height_m)) < 1e-6 and upturn_lm > 0:
        raise Refused(f"upturn folded into the flat area: {booked_m2} = {flat_m2} + {upturn_lm} x {height_m}")
    return True


def refuse_held_as_zero(qty, status):
    if status in ("HELD", "UNKNOWN") and qty is not None and qty == 0:
        raise Refused("a HELD / UNKNOWN quantity carried as 0")
    return True


def closure(own, reference, causes, tol=1e-4):
    """own - reference must equal the sum of the named causes within tol, else the residual is UNEXPLAINED."""
    resid = own - reference
    named = sum(v for _, v in causes)
    left = resid - named
    return {"own": round(own, 6), "reference": round(reference, 6), "residual": round(resid, 6),
            "named": [(k, round(v, 6)) for k, v in causes], "unexplained": round(left, 6),
            "closes": abs(left) <= tol}


def falls_screed_volume(area_m2, t0_m, mean_rise_m):
    """screed to falls = area x (t0 + mean rise). t0 unprinted -> None (HELD); only the part above the t0 plane
    (area x mean rise) is reported, as T-221 did."""
    above = None if mean_rise_m is None else (area_m2 * mean_rise_m[0], area_m2 * mean_rise_m[1])
    if t0_m is None:
        return {"total_m3": None, "status": "HELD (t0 unprinted, D-39)", "above_t0_m3": above}
    return {"total_m3": (area_m2 * (t0_m + mean_rise_m[0]), area_m2 * (t0_m + mean_rise_m[1])),
            "status": "DRAWING-CONFIRMED", "above_t0_m3": above}
