"""PLASTER / WALL-TREATMENT ENGINE - the fourth arrow, deterministic.

    TRADE_MEASUREMENT_REGIONS  ->  QUANTITIES

Consumes a measurement region from engine.qs_measurement_region and the
parameter registry from research.a21_trace_sufficiency_01.parameters,
and writes a calculation sheet a human QS could check line by line:

    Wall A   4.00 x H
    Wall B   3.00 x H
    ...                                    = GROSS
    less door D-01     1.00 x 2.20
    less window W-01   1.50 x 1.50           = PRINCIPAL WALL FACE
    plus reveals       (2h + w) x depth      = FINAL TREATMENT AREA (m2)
    profiles                                   lm, on their own line, never
                                               added to any m2

Every line carries the provenance of every input, and the sheet's state
is the weakest input in it:

    SOURCE_ESTABLISHED_QUANTITY   every input from a permitted project source
    OWNER_PARAMETRIC_QUANTITY     a QS input came from the owner
    PROVISIONAL_DEFAULT_QUANTITY  a temporary default is in the arithmetic
    NOT_ESTABLISHED               an input is unknown

There is no hidden arithmetic: every number on the sheet is the product of
numbers also on the sheet.
"""

from __future__ import annotations

from research.a21_trace_sufficiency_01.parameters import (
    PROVENANCE_RANK, RANK_TO_STATE)

TREATMENTS = (
    "NORMAL_INTERNAL_PLASTER", "TILE_PREP_TARTUSHA",
    "COLUMN_BONDING_PLUS_PLASTER", "STAIR_WALL_PLASTER", "STAIR_UNDERSIDE",
    "OPENING_REVEALS_AND_RETURNS", "STEEL_CORNER_AND_EDGE_PROFILES",
    "EXTERNAL_PLASTER", "EXTERNAL_CONTROL_JOINT",
    "ROOF_PARAPET_EXTERNAL_FACE", "ROOF_PARAPET_INTERNAL_FACE",
    "ROOF_PARAPET_CAPPING",
)

HEIGHT_PARAMETER_FOR = {
    "NORMAL_INTERNAL_PLASTER": "APPLICABLE_PLASTER_HEIGHT",
    "TILE_PREP_TARTUSHA": "APPLICABLE_PLASTER_HEIGHT",
    "COLUMN_BONDING_PLUS_PLASTER": "APPLICABLE_PLASTER_HEIGHT",
    "STAIR_WALL_PLASTER": "APPLICABLE_PLASTER_HEIGHT",
    "EXTERNAL_PLASTER": "APPLICABLE_PLASTER_HEIGHT",
}
OPENING_HEIGHT_PARAMETER = {"DOOR": "DOOR_HEIGHT", "WINDOW": "WINDOW_HEIGHT"}
REVEAL_DEPTH_PARAMETER = {"DOOR": "DOOR_REVEAL_DEPTH",
                          "WINDOW": "WINDOW_REVEAL_DEPTH"}


# A21 speaks in reader source types; the parameter layer speaks in
# provenance ranks. The bridge is explicit so a reader vocabulary can
# never silently rank as UNKNOWN and drag a whole sheet to NOT_ESTABLISHED.
READER_SOURCE_TO_PROVENANCE = {
    "DRAWING_PRINTED_DIMENSION": "DRAWING",
    "DRAWING_SCALED_MEASUREMENT": "DRAWING",
    "DRAWING_SCHEDULE": "DRAWING",
    "PROJECT_SPECIFICATION": "SPECIFICATION",
    "TEMPORARY_OWNER_DEFAULT": "TEMPORARY_DEFAULT",
    "VISUAL_INTERPRETATION": "DRAWING",
}
# Which of those are weaker READS of the same source - reported on the
# sheet so a reviewer can see them, without inventing a new state.
WEAK_READ_SOURCES = ("DRAWING_SCALED_MEASUREMENT", "VISUAL_INTERPRETATION")


def _prov(t) -> str:
    t = t or "UNKNOWN"
    return READER_SOURCE_TO_PROVENANCE.get(t, t)


def _state(source_types) -> str:
    rank = max(PROVENANCE_RANK.get(_prov(t), 4) for t in source_types)
    return RANK_TO_STATE[rank]


def _param(reg: dict, pid: str):
    p = reg.get(pid) or {}
    return p.get("VALUE"), (p.get("SOURCE_TYPE") or "UNKNOWN")


def _num(x) -> bool:
    return isinstance(x, (int, float))


def calculate(region: dict, reg: dict, *, treatment: str) -> dict:
    """One treatment, one region, one checkable sheet."""
    if treatment not in TREATMENTS:
        raise ValueError(f"unknown treatment {treatment}")
    sheet = []
    # inputs are tracked PER RESULT LINE. A reveal depth the registry does
    # not have must not drag the principal wall face - which never used
    # it - down to NOT_ESTABLISHED. Each result line carries the weakest
    # of ITS OWN inputs, and there is no single state for the sheet.
    inputs = {"PRINCIPAL_WALL_FACE": [], "REVEALS_AND_RETURNS": [],
              "STEEL_PROFILES": []}

    if region["MEASUREMENT_REGION_STATUS"] not in (
            "MEASUREMENT_REGION_CLOSED", "MEASUREMENT_RUN_ESTABLISHED"):
        return {"TREATMENT": treatment, "REGION_ID": region["REGION_ID"],
                "QUANTITY_STATE": "NOT_ESTABLISHED",
                "WHY": "the measurement region was not formed",
                "REGION_REASONS": region.get("NOT_ESTABLISHED_BECAUSE"),
                "SHEET": []}

    # ---- height --------------------------------------------------
    hp = HEIGHT_PARAMETER_FOR.get(treatment)
    H, H_src = _param(reg, hp) if hp else (None, "UNKNOWN")
    inputs["PRINCIPAL_WALL_FACE"].append(H_src)
    inputs["STEEL_PROFILES"].append(H_src)
    sheet.append({"LINE": "HEIGHT", "PARAMETER": hp, "VALUE_M": H,
                  "SOURCE_TYPE": H_src})

    # ---- gross, wall by wall -------------------------------------
    gross = 0.0 if _num(H) else None
    for e in region["GROSS_BASIS"]["CONTRIBUTING_EDGES"]:
        L = e.get("length_m")
        inputs["PRINCIPAL_WALL_FACE"].append(e.get("length_source") or "UNKNOWN")
        area = round(L * H, 4) if _num(L) and _num(H) else None
        if gross is not None:
            gross = None if area is None else round(gross + area, 4)
        sheet.append({"LINE": "WALL", "EDGE_ID": e["EDGE_ID"],
                      "LENGTH_M": L, "LENGTH_SOURCE": e.get("length_source"),
                      "TRACE_IDS": e.get("trace_ids"),
                      "CALC": f"{L} x {H} = {area}", "AREA_M2": area})
    for e in region["GROSS_BASIS"]["NON_CONTRIBUTING_EDGES"]:
        sheet.append({"LINE": "EXCLUDED_EDGE", "EDGE_ID": e["EDGE_ID"],
                      "KIND": e["KIND"], "REASON": e["REASON"], "AREA_M2": 0.0})
    for c in region["SYNTHETIC_CLOSURES"]:
        sheet.append({"LINE": "SYNTHETIC_CLOSURE", "EDGE_ID": c["EDGE_ID"],
                      "AREA_M2": 0.0,
                      "REASON": "a closure is a measurement instrument, "
                                "not a wall"})
    sheet.append({"LINE": "GROSS", "AREA_M2": gross})

    # ---- deductions, opening by opening --------------------------
    deductions = 0.0
    reveals = 0.0
    for o in region["OPENINGS"]:
        w, w_src = o.get("width_m"), o.get("width_source") or "UNKNOWN"
        h, h_src = o.get("height_m"), o.get("height_source")
        if not _num(h):
            h, h_src = _param(reg, OPENING_HEIGHT_PARAMETER.get(o["TYPE"], ""))
        inputs["PRINCIPAL_WALL_FACE"] += [w_src, h_src or "UNKNOWN"]
        inputs["REVEALS_AND_RETURNS"] += [w_src, h_src or "UNKNOWN"]
        area = round(w * h, 4) if _num(w) and _num(h) else None
        deductions = (None if area is None or deductions is None
                      else round(deductions + area, 4))
        sheet.append({"LINE": "DEDUCTION", "OPENING_ID": o["OPENING_ID"],
                      "TYPE": o["TYPE"], "WIDTH_M": w, "WIDTH_SOURCE": w_src,
                      "HEIGHT_M": h, "HEIGHT_SOURCE": h_src,
                      "TRACE_IDS": o.get("trace_ids"),
                      "CALC": f"{w} x {h} = {area}", "AREA_M2": area})
        # reveals: head + two jambs for a door, all four sides for a window
        d, d_src = _param(reg, REVEAL_DEPTH_PARAMETER.get(o["TYPE"], ""))
        inputs["REVEALS_AND_RETURNS"].append(d_src)
        if _num(w) and _num(h) and _num(d):
            girth = (2 * h + w) if o["TYPE"] == "DOOR" else (2 * h + 2 * w)
            rv = round(girth * d, 4)
        else:
            girth, rv = None, None
        reveals = None if rv is None or reveals is None else round(reveals + rv, 4)
        sheet.append({"LINE": "REVEAL", "OPENING_ID": o["OPENING_ID"],
                      "GIRTH_M": girth, "DEPTH_M": d, "DEPTH_SOURCE": d_src,
                      "CALC": f"{girth} x {d} = {rv}", "AREA_M2": rv})

    principal = (round(gross - deductions, 4)
                 if _num(gross) and _num(deductions) else None)
    sheet.append({"LINE": "PRINCIPAL_WALL_FACE",
                  "CALC": f"{gross} - {deductions} = {principal}",
                  "AREA_M2": principal})
    sheet.append({"LINE": "REVEALS_AND_RETURNS_SUBTOTAL", "AREA_M2": reveals,
                  "KEPT_SEPARATE_FROM_THE_WALL_FACE": True})

    # ---- profiles: lm, never added to m2 -------------------------
    profiles_lm = None
    if _num(H):
        arrises = 2 * len(region["OPENINGS"])
        profiles_lm = round(arrises * H, 4)
    sheet.append({"LINE": "STEEL_CORNER_AND_EDGE_PROFILES", "UNIT": "lm",
                  "VALUE": profiles_lm,
                  "CALC": f"2 jambs per opening x {len(region['OPENINGS'])} "
                          f"openings x {H}",
                  "NEVER_ADDED_TO_M2": True})

    states = {
        "PRINCIPAL_WALL_FACE": (_state(inputs["PRINCIPAL_WALL_FACE"])
                                if principal is not None else "NOT_ESTABLISHED"),
        "REVEALS_AND_RETURNS": (_state(inputs["REVEALS_AND_RETURNS"])
                                if reveals is not None else "NOT_ESTABLISHED"),
        "STEEL_PROFILES": (_state(inputs["STEEL_PROFILES"])
                           if profiles_lm is not None else "NOT_ESTABLISHED"),
    }
    all_inputs = [t for v in inputs.values() for t in v]
    return {
        "TREATMENT": treatment,
        "REGION_ID": region["REGION_ID"],
        "RULE_VERSION": region["RULE_VERSION"],
        "MEASUREMENT_BASIS": region["MEASUREMENT_BASIS"],
        "SHEET": sheet,
        "RESULT": {
            "PRINCIPAL_WALL_FACE_M2": principal,
            "REVEALS_AND_RETURNS_M2": reveals,
            "STEEL_PROFILES_LM": profiles_lm,
            "M2_AND_LM_ARE_NEVER_COMBINED": True,
        },
        "INPUT_PROVENANCE": {k: sorted(set(v)) for k, v in inputs.items()},
        "INPUTS_THAT_ARE_WEAK_READS": sorted(
            {t for t in all_inputs if t in WEAK_READ_SOURCES}),
        "QUANTITY_STATE": states,
        "THERE_IS_NO_SINGLE_STATE_FOR_THE_SHEET": (
            "each result line carries the weakest provenance among ITS "
            "OWN inputs. A missing reveal depth leaves the principal wall "
            "face untouched, because the wall face never used it"),
        "NO_HIDDEN_ARITHMETIC": True,
    }
