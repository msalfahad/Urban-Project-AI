"""CONTRACTOR / SITE MEASUREMENT BASIS - the commercial convention, kept
apart from engineering geometry (§1, §4).

A contractor rulebook is a record of HOW A SITE RECORD MEASURED: heights by
floor as the record used them, HALF or FULL opening deduction as the record
shows, door sizes and reveal girths as listed, corners at "2 m = 1 m", and
parapet or facade heights as measured. Every entry carries

    SOURCE_TYPE = SITE_RECORD | CONTRACTOR_MEASUREMENT_RULE

and none of it is geometry: a half deduction is a payment convention, a
site height is what the record says, and neither replaces a drawing or an
owner project input on the engineering basis.

calculate_contractor() applies the rulebook to the SAME face set the
engineering engine used, so the two results differ only by convention and
the difference can be decomposed by driver.
"""

from __future__ import annotations

CONTRACTOR_RULE_VERSION = "CSM-1.0"
SOURCE_TYPES = ("SITE_RECORD", "CONTRACTOR_MEASUREMENT_RULE")
DEDUCTION_RULES = ("FULL_OPENING_DEDUCTION", "HALF_OPENING_DEDUCTION",
                   "NO_OPENING_DEDUCTION")


def rule(rid: str, value, unit, *, source_type: str, reference: str, scope: str,
         note: str | None = None) -> dict:
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"a contractor rulebook entry must be SITE_RECORD or "
                         f"CONTRACTOR_MEASUREMENT_RULE, not {source_type}")
    return {"RULE_ID": rid, "VALUE": value, "UNIT": unit, "SOURCE_TYPE": source_type,
            "SOURCE_REFERENCE": reference, "SCOPE": scope, "NOTE": note,
            "IS_GEOMETRY": False, "BASIS": "CONTRACTOR_SITE_MEASUREMENT"}


def _num(x):
    return isinstance(x, (int, float))


def calculate_contractor(face_set: dict, rulebook: dict, *, treatment: str,
                         floor: str | None = None, height_key: str | None = None) -> dict:
    """CONTRACTOR_MEASUREMENT_QUANTITY on the engineering face set.

    rulebook keys used: HEIGHT_<floor-or-zone> (m), OPENING_DEDUCTION_RULE,
    DOOR_WIDTH, DOOR_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT, DOOR_REVEAL_DEPTH,
    DOOR_REVEAL_GIRTH (optional), CORNER_ENDING_RULE.
    """
    floor = floor or face_set.get("FLOOR")
    hk = height_key or f"HEIGHT_{floor}"
    H = (rulebook.get(hk) or {}).get("VALUE")
    ded_rule = (rulebook.get("OPENING_DEDUCTION_RULE") or {}).get("VALUE", "FULL_OPENING_DEDUCTION")
    if ded_rule not in DEDUCTION_RULES:
        raise ValueError(f"unknown deduction rule {ded_rule}")
    factor = {"FULL_OPENING_DEDUCTION": 1.0, "HALF_OPENING_DEDUCTION": 0.5,
              "NO_OPENING_DEDUCTION": 0.0}[ded_rule]
    sheet, gross = [], 0.0
    faces = face_set["ESTABLISHED_FACES"]
    used_rules = [hk, "OPENING_DEDUCTION_RULE"]
    for f in faces:
        h = f.get("height_m") if _num(f.get("height_m")) else H
        area = round(f["length_m"] * h, 4) if _num(h) else None
        gross = None if area is None or gross is None else round(gross + area, 4)
        sheet.append({"LINE": "FACE", "FACE_ID": f["FACE_ID"], "LENGTH_M": f["length_m"],
                      "HEIGHT_M": h, "HEIGHT_RULE": (None if _num(f.get("height_m")) else hk),
                      "AREA_M2": area})
    ded, reveals = 0.0, 0.0
    for o in face_set["OPENINGS"]:
        if o["DEDUCTION_STATUS"] != "DEDUCTIBLE_FROM_ESTABLISHED_FACE":
            continue
        wk, hk2 = (("DOOR_WIDTH", "DOOR_HEIGHT") if o["TYPE"] == "DOOR"
                   else ("WINDOW_WIDTH", "WINDOW_HEIGHT"))
        w = o.get("width_m") if _num(o.get("width_m")) else (rulebook.get(wk) or {}).get("VALUE")
        h = o.get("height_m") if _num(o.get("height_m")) else (rulebook.get(hk2) or {}).get("VALUE")
        used_rules += [wk, hk2]
        a = round(w * h, 4) if _num(w) and _num(h) else None
        d = round(a * factor, 4) if a is not None else None
        ded = None if d is None or ded is None else round(ded + d, 4)
        sheet.append({"LINE": "DEDUCTION", "OPENING_ID": o["OPENING_ID"], "TYPE": o["TYPE"],
                      "WIDTH_M": w, "HEIGHT_M": h, "OPENING_AREA_M2": a,
                      "DEDUCTION_RULE": ded_rule, "DEDUCTED_M2": d})
        if o["TYPE"] == "DOOR":
            g = (rulebook.get("DOOR_REVEAL_GIRTH") or {}).get("VALUE")
            dep = (rulebook.get("DOOR_REVEAL_DEPTH") or {}).get("VALUE")
            used_rules += ["DOOR_REVEAL_DEPTH", "DOOR_REVEAL_GIRTH"]
            girth = g if _num(g) else ((2 * h + w) if _num(w) and _num(h) else None)
            rv = round(girth * dep, 4) if _num(girth) and _num(dep) else None
            reveals = None if rv is None or reveals is None else round(reveals + rv, 4)
            sheet.append({"LINE": "REVEAL", "OPENING_ID": o["OPENING_ID"], "GIRTH_M": girth,
                          "DEPTH_M": dep, "AREA_M2": rv})
    net = round(gross - ded, 4) if _num(gross) and _num(ded) else None
    sheet.append({"LINE": "CONTRACTOR_MEASURED_SUBTOTAL", "GROSS_M2": gross,
                  "DEDUCTED_M2": ded, "NET_M2": net, "REVEALS_M2": reveals})
    return {
        "TREATMENT": treatment, "SET_ID": face_set["SET_ID"], "FLOOR": floor,
        "BASIS": "CONTRACTOR_SITE_MEASUREMENT", "RULE_VERSION": CONTRACTOR_RULE_VERSION,
        "RULES_USED": {k: rulebook.get(k) for k in dict.fromkeys(used_rules) if rulebook.get(k)},
        "SHEET": sheet,
        "RESULT": {"CONTRACTOR_MEASUREMENT_QUANTITY_M2": net, "GROSS_M2": gross,
                   "DEDUCTED_M2": ded, "REVEALS_M2": reveals,
                   "HEIGHT_USED_M": H, "OPENING_DEDUCTION_RULE": ded_rule,
                   "COVERAGE_STATUS": face_set["COVERAGE_STATUS"],
                   "COMPLETE_TOTAL_STATUS": face_set["COMPLETE_TOTAL_STATUS"]},
        "STATUS": ("NOT_ESTABLISHED" if net is None else
                   ("NOT_APPLICABLE" if not faces else "CONTRACTOR_MEASURED")),
        "THIS_IS_A_COMMERCIAL_CONVENTION_NOT_GEOMETRY": True,
    }


def decompose(face_set: dict, eng_result: dict, eng_reg: dict, rulebook: dict, *,
              treatment: str, floor: str | None, engine_calculate) -> dict:
    """Attribute the contractor-minus-engineering delta to drivers by
    substituting one convention at a time into the engineering engine
    (height, then door dimension, then reveals) and applying the deduction
    rule last; what remains is OTHER."""
    floor = floor or face_set.get("FLOOR")
    base = eng_result["RESULT"]["ESTABLISHED_SUBTOTAL_M2"]
    contractor = calculate_contractor(face_set, rulebook, treatment=treatment, floor=floor)
    target = contractor["RESULT"]["CONTRACTOR_MEASUREMENT_QUANTITY_M2"]
    if not _num(base) or not _num(target):
        return {"DECOMPOSABLE": False, "WHY": "one basis has no quantity",
                "ENGINEERING_M2": base, "CONTRACTOR_M2": target,
                "DRIVERS": {"SCOPE": None}}
    import json as _json
    steps, prev = {}, base
    reg = _json.loads(_json.dumps(eng_reg))
    # HEIGHT: substitute the contractor height into the engineering height parameter
    hk = f"HEIGHT_{floor}"
    hp = None
    for ln in eng_result["SHEET"]:
        if ln["LINE"] == "ESTABLISHED_FACE" and ln.get("HEIGHT_PARAMETER"):
            hp = ln["HEIGHT_PARAMETER"]
            break
    if hp and (rulebook.get(hk) or {}).get("VALUE") is not None:
        reg[hp] = dict(reg[hp], VALUE=rulebook[hk]["VALUE"])
        r = engine_calculate(face_set, reg, treatment=treatment, floor=floor)
        v = r["RESULT"]["ESTABLISHED_SUBTOTAL_M2"]
        steps["HEIGHT"] = round(v - prev, 4)
        prev = v
    # DOOR_DIMENSION
    for pid in ("DOOR_WIDTH", "DOOR_HEIGHT", "WINDOW_WIDTH", "WINDOW_HEIGHT"):
        if pid in reg and (rulebook.get(pid) or {}).get("VALUE") is not None:
            reg[pid] = dict(reg[pid], VALUE=rulebook[pid]["VALUE"])
    r = engine_calculate(face_set, reg, treatment=treatment, floor=floor)
    v = r["RESULT"]["ESTABLISHED_SUBTOTAL_M2"]
    steps["DOOR_DIMENSION"] = round(v - prev, 4)
    prev = v
    # OPENING_DEDUCTION: full -> contractor rule on the same openings
    ded_full = sum((ln["AREA_M2"] or 0.0) for ln in r["SHEET"]
                   if ln["LINE"] == "DEDUCTION" and ln.get("FROM") == "ESTABLISHED")
    factor = {"FULL_OPENING_DEDUCTION": 1.0, "HALF_OPENING_DEDUCTION": 0.5,
              "NO_OPENING_DEDUCTION": 0.0}[
        (rulebook.get("OPENING_DEDUCTION_RULE") or {}).get("VALUE", "FULL_OPENING_DEDUCTION")]
    steps["OPENING_DEDUCTION"] = round(ded_full * (1 - factor), 4)
    prev = round(prev + steps["OPENING_DEDUCTION"], 4)
    steps["REVEALS"] = 0.0     # reveals are separate on both bases; never in the face m2
    steps["OTHER"] = round(target - prev, 4)
    return {"DECOMPOSABLE": True, "ENGINEERING_M2": base, "CONTRACTOR_M2": target,
            "DELTA_M2": round(target - base, 4), "DRIVERS": steps,
            "ORDER": ["HEIGHT", "DOOR_DIMENSION", "OPENING_DEDUCTION", "REVEALS", "OTHER"],
            "SUM_OF_DRIVERS_M2": round(sum(steps.values()), 4)}
