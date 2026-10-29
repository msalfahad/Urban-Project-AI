"""T-339 roof build-up binding (research only, read by no method): every roof x layer bound ONCE to a candidate line id
or to a NEW row name, the layer edges at the parapet INNER face, closure against the roof slab zone, and a cross-check
that no layer shares an area with a parapet row. Any villa; provenance T-339 (rules R-T339-1 .. 5 below).

Physical element (ERS s.2 step 1). A flat roof / terrace of a villa is, from the bottom: the structural roof slab (its
concrete is STR.CONC.SLAB, under every layer, never a layer), the parapet standing on the slab edge (its RC / block body,
its faces, top and arrises are parapet rows: STR.CONC.PARAPET, MAS.BLOCK, FIN.EXT.FINISH, parapet inner face, top), and
the build-up inside the parapet INNER face: screed to falls, membrane (+ its upturn on the parapet / wall faces),
insulation, protection, walking finish. Owner trade per layer (ELEMENT_REGISTER 2026-10-29, Lead ruling):

  FALLS_SCREED  SCREED (Q-41), ONE volume per roof (m3); its plan area is its basis, not its BOQ quantity
  MEMBRANE      WATERPROOFING (FIN.WP.ROOF, m2)            -- an existing line, cross-referenced, never a B13-01 row
  UPTURN        WATERPROOFING (FIN.WP.ROOF_UPTURN, lm)      -- its own item, never folded into the flat m2
  INSULATION    ROOFING B13-01 (m2)
  PROTECTION    ROOFING B13-01 (m2)
  FINISH        ROOFING B13-01 (roof walking finish, m2)

R-T339-1 (edges). A layer's area is measured to its OWN drawn edge INSIDE the parapet inner face (and the wall faces
round the roof); an area that reaches the parapet OUTER face (or the slab edge) includes the parapet footprint and is
refused: the footprint belongs to the parapet rows (top surface + RC / block body).
R-T339-2 (one binding). Each (roof, layer) is bound exactly once: to an existing candidate line (its item code and unit
must be the layer's) or to a NEW row name that is not an existing line; a layer bound twice, or to a line of another
trade, is refused. A layer with no evidence (no print, no owner rule) is UNKNOWN: a row with NO number, never 0, never
dropped. A HELD quantity is blank (bounds beside it), never 0.
R-T339-3 (one screed). The falls layer is ONE screed VOLUME per roof (Q-41; Q-45 governs its mix only): a second falls
row, or a falls row booked as an area (m2) BOQ quantity, is refused; with its base thickness unprinted (D-39) the volume
is HELD, never a default thickness.
R-T339-4 (closure). Per roof: slab roof zone (to the parapet's drawn wall line) - parapet footprint (the parapet top
surfaces, centreline x drawn thickness) - layer area = the sum of NAMED causes (D-band ranges, a divider, a dome
footprint, finish-edge annotation); any remainder over the tolerance is UNEXPLAINED and reported, never forced.
R-T339-5 (no shared area). A layer's plan polygon intersects no parapet footprint polygon (0.000 m2), and no layer
other than the membrane carries a vertical row on a parapet face unless its height is printed (the faces are the parapet
rows'); a layer row that names a parapet component, or a parapet row inside a layer, is refused.
"""
from __future__ import annotations

from dataclasses import dataclass, field

LAYERS = ("FALLS_SCREED", "MEMBRANE", "UPTURN", "INSULATION", "PROTECTION", "FINISH")
TRADE = {"FALLS_SCREED": "SCREED", "MEMBRANE": "WATERPROOFING", "UPTURN": "WATERPROOFING",
         "INSULATION": "ROOFING B13-01", "PROTECTION": "ROOFING B13-01", "FINISH": "ROOFING B13-01"}
UNIT = {"FALLS_SCREED": "m3", "MEMBRANE": "m2", "UPTURN": "lm", "INSULATION": "m2", "PROTECTION": "m2",
        "FINISH": "m2"}
ITEM = {"MEMBRANE": "FIN.WP.ROOF", "UPTURN": "FIN.WP.ROOF_UPTURN"}   # the existing families; others are NEW rows
NEW_ITEM = {"FALLS_SCREED": "B13-01 ROOF SCREED TO FALLS", "INSULATION": "B13-01 ROOF INSULATION",
            "PROTECTION": "B13-01 ROOF PROTECTION", "FINISH": "B13-01 ROOF FINISH"}
EDGE = {"FALLS_SCREED": "face", "MEMBRANE": "face", "UPTURN": "faces round the roof", "INSULATION": "face",
        "PROTECTION": "face", "FINISH": "finish"}
STATUSES = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "HELD", "UNKNOWN")
PARAPET_WORDS = ("PARAPET", "COPING", "INNER_FACE", "TOP_SURFACE", "ARRIS")
TOL = 1e-4


class Refused(ValueError):
    """a binding the ledger must not accept."""


@dataclass
class Roof:
    roof_id: str
    element_id: str                      # the roof element the candidate lines carry (room / element id)
    floor: str                           # storey label of the roof WP lines (plan above)
    slab_floor: str                      # storey whose roof slab carries it (structural convention)
    outer_m2: float | None               # slab roof zone to the parapet's drawn wall line (outer face of the 0.20 wall)
    footprint_m2: tuple | None           # parapet top surfaces (lo, hi)
    face_m2: tuple | None                # (lo, hi) inside the parapet inner face / wall faces
    finish_m2: tuple | None              # (lo, hi) to the designer's finish edge
    upturn_lm: tuple | None = None       # (lo, hi) vertical faces round the roof (membrane upturn base)
    domes_m2: dict = field(default_factory=dict)   # dome footprints inside the face outline: name -> m2
    held: str = ""                       # roof-level hold (e.g. no roof plan, owner Q-34)


def check_area(roof: Roof, layer: str, area):
    """R-T339-1: a layer area is never larger than the area inside the parapet inner face (plus the tolerance)."""
    if area is None:
        return True
    lo, hi = area
    if lo is not None and lo <= 0:
        raise Refused(f"{roof.roof_id} {layer}: area {lo} <= 0 (held is blank, never 0)")
    if roof.face_m2 is not None and hi > roof.face_m2[1] + TOL:
        raise Refused(f"{roof.roof_id} {layer}: {hi} m2 exceeds the area inside the parapet inner face "
                      f"{roof.face_m2[1]} m2: the layer edge was taken beyond the inner face (parapet footprint "
                      f"{roof.footprint_m2} m2 belongs to the parapet rows)")
    return True


def bind(roof: Roof, layer: str, *, scope: str, scope_source: str, area=None, quantity=None, quantity_status=None,
         line=None, new_row=None, booked_unit=None, thickness_m=None, thickness_source="", upturn_height_m=None,
         upturn_source="", bounds_beside=None, held_reason="", edge_handles=()):
    """one (roof, layer) binding row. line: an existing candidate line dict (line_id, item_code, unit, state, quantity);
    new_row: the name of a NEW row. Exactly one of the two."""
    if layer not in LAYERS:
        raise Refused(f"unknown layer {layer!r}")
    if (line is None) == (new_row is None):
        raise Refused(f"{roof.roof_id} {layer}: bind to ONE existing line or ONE new row (got line={line!r}, "
                      f"new_row={new_row!r})")
    unit = booked_unit or UNIT[layer]
    if unit != UNIT[layer]:
        raise Refused(f"{roof.roof_id} {layer}: booked in {unit}, its quantity unit is {UNIT[layer]} "
                      f"(the falls screed is ONE volume, its plan area only the basis)")
    if line is not None:
        if layer not in ITEM:
            raise Refused(f"{roof.roof_id} {layer}: no existing family carries it; {line['item_code']} belongs to "
                          f"another trade")
        if line["item_code"] != ITEM[layer] or line["unit"] != UNIT[layer]:
            raise Refused(f"{roof.roof_id} {layer}: line {line['line_id']} is {line['item_code']} / {line['unit']}, "
                          f"the layer's family is {ITEM[layer]} / {UNIT[layer]}")
    if new_row is not None:
        if layer in ITEM:
            raise Refused(f"{roof.roof_id} {layer}: a NEW row for a layer an existing family owns "
                          f"({ITEM[layer]}): double count with the waterproofing line")
        if any(w in new_row.upper() for w in PARAPET_WORDS):
            raise Refused(f"{roof.roof_id} {layer}: row {new_row!r} names a parapet component (R-T339-5)")
    if thickness_m is not None and not thickness_source:
        raise Refused(f"{roof.roof_id} {layer}: thickness {thickness_m} without a printed source (D-39: HELD)")
    if thickness_m is not None and thickness_m <= 0:
        raise Refused(f"{roof.roof_id} {layer}: thickness {thickness_m} (a held thickness is blank, never 0)")
    if upturn_height_m is not None and layer not in ("UPTURN",) and not upturn_source:
        raise Refused(f"{roof.roof_id} {layer}: an upturn on the parapet face without a printed height: the face is "
                      f"the parapet rows' (R-T339-5)")
    check_area(roof, layer, area if EDGE[layer] != "faces round the roof" else None)
    if roof.held:
        status = "HELD"
    elif scope == "UNKNOWN":
        status = "UNKNOWN"
    else:
        status = quantity_status or ("ASSUMED - OWNER-APPROVED" if scope == "OWNER_RULE" else "DRAWING-CONFIRMED")
    if status not in STATUSES:
        raise Refused(f"status {status!r}")
    if status in ("HELD", "UNKNOWN") and quantity is not None:
        if quantity == 0 or quantity == (0, 0):
            raise Refused(f"{roof.roof_id} {layer}: a {status} quantity carried as 0")
        raise Refused(f"{roof.roof_id} {layer}: a {status} row carries a number {quantity!r} (blank, bounds beside)")
    if status == "UNKNOWN" and area is not None:
        raise Refused(f"{roof.roof_id} {layer}: an UNKNOWN layer carries no area (its basis goes beside, as text)")
    return {"roof": roof.roof_id, "element_id": roof.element_id, "floor": roof.floor, "layer": layer,
            "owner_trade": TRADE[layer], "unit": UNIT[layer], "scope": scope, "scope_source": scope_source,
            "edge": EDGE[layer], "edge_handles": " ".join(edge_handles),
            "area_lo": None if area is None or roof.held else area[0],
            "area_hi": None if area is None or roof.held else area[1],
            "quantity_lo": None if quantity is None else quantity[0],
            "quantity_hi": None if quantity is None else quantity[1],
            "status": status, "binding": "EXISTING_LINE" if line is not None else "NEW_ROW",
            "line_id": line["line_id"] if line is not None else "",
            "line_state": line.get("state", "") if line is not None else "",
            "line_quantity": line.get("quantity") if line is not None else None,
            "new_row": new_row or "", "bounds_beside": bounds_beside or "", "held_reason": held_reason}


def check_bindings(rows):
    """R-T339-2 / 3 over a whole ledger: one row per (roof, layer); one screed per roof; one line never under two roofs
    or two layers; every HELD / UNKNOWN blank."""
    seen, lines = set(), {}
    for r in rows:
        k = (r["roof"], r["layer"])
        if k in seen:
            raise Refused(f"{k} bound twice")
        seen.add(k)
        if r["line_id"]:
            if r["line_id"] in lines and lines[r["line_id"]] != k:
                raise Refused(f"line {r['line_id']} bound under {lines[r['line_id']]} and {k}")
            lines[r["line_id"]] = k
        if r["status"] in ("HELD", "UNKNOWN") and (r["quantity_lo"] is not None or r["quantity_hi"] is not None):
            raise Refused(f"{k}: {r['status']} with a number")
    screeds = {}
    for r in rows:
        if r["layer"] == "FALLS_SCREED":
            screeds[r["roof"]] = screeds.get(r["roof"], 0) + 1
    for roof, n in screeds.items():
        if n != 1:
            raise Refused(f"{roof}: {n} falls rows (one screed volume per roof)")
    return True


def closure(roof: Roof, layer_area, causes, end="hi"):
    """R-T339-4: outer - footprint - layer = sum(named causes) within TOL, else UNEXPLAINED. end picks the lo or hi
    reading of the footprint (the layer area is passed as the matching reading by the caller)."""
    if roof.outer_m2 is None or roof.footprint_m2 is None:
        raise Refused(f"{roof.roof_id}: no slab roof zone or footprint to close against")
    fp = roof.footprint_m2[1] if end == "hi" else roof.footprint_m2[0]
    resid = roof.outer_m2 - fp - layer_area
    named = sum(v for _, v in causes)
    left = resid - named
    return {"roof": roof.roof_id, "end": end, "outer_m2": round(roof.outer_m2, 6), "footprint_m2": round(fp, 6),
            "layer_m2": round(layer_area, 6), "residual_m2": round(resid, 6),
            "named": [[k, round(v, 6)] for k, v in causes], "unexplained_m2": round(left, 6),
            "closes": abs(left) <= TOL}


def shared_area(layer_poly, parapet_polys):
    """R-T339-5: plan area a layer polygon shares with the parapet footprint polygons (shapely geometries)."""
    return sum(layer_poly.intersection(p).area for p in parapet_polys)


def fill_rows(rows, note_by_layer=None):
    """the FILL table a roof build-up integration consumes unchanged: one row per NEW row / existing line, with its
    quantity fields (blank when HELD / UNKNOWN) and what it is exclusive with."""
    out = []
    for r in rows:
        out.append({"target": r["line_id"] or r["new_row"], "action": "UNCHANGED (cross-reference)" if r["line_id"]
                    else ("ADD (blank, held)" if r["status"] in ("HELD", "UNKNOWN") else "ADD"),
                    "roof": r["roof"], "element_id": r["element_id"], "floor": r["floor"], "layer": r["layer"],
                    "owner_trade": r["owner_trade"], "unit": r["unit"],
                    "quantity_lo": r["quantity_lo"], "quantity_hi": r["quantity_hi"],
                    "basis_area_lo": r["area_lo"], "basis_area_hi": r["area_hi"], "status": r["status"],
                    "bounds_beside": r["bounds_beside"], "held_reason": r["held_reason"],
                    "exclusive_with": "parapet rows (STR.CONC.PARAPET, MAS.BLOCK parapet alternative, FIN.EXT.FINISH "
                                      "PARAPET-OUTER, parapet inner face / top / arrises); STR.CONC.SLAB under it",
                    "note": (note_by_layer or {}).get(r["layer"], "")})
    return out
