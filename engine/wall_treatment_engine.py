"""WALL-TREATMENT ENGINE over a face set - deterministic, no hidden arithmetic.

    WALL_FACE_SET  x  parameter registry  ->  one checkable sheet per
                                              (face set, treatment)

Every line: the product of numbers also on the sheet, with the provenance
of every input and the weakest-input state of ITS OWN inputs. The sheet
reports (§12):

    ESTABLISHED_SUBTOTAL_M2   established faces x height, less deductible
                              openings on those faces
    PROVISIONAL_SUBTOTAL_M2   provisional faces, kept apart
    COMPLETE_TOTAL_STATUS     ESTABLISHED only when the face set covers the
                              whole zone and nothing is unresolved
    UNRESOLVED_SCOPE          what is not in either subtotal, and why

Trade rules encoded here (each its own line, never mixed):
  §16 reveals: window girth 2h+2w, door girth 2h+w, times a depth; an
      opening's ACTUAL depth wins over the parameter default
  §17 steel profiles: eligible edge lengths in lm per category
      (DOOR_JAMB, DOOR_HEAD, WINDOW_JAMB, WINDOW_HEAD, WINDOW_SILL,
      EXTERNAL_CORNER, OTHER); whether an edge takes a profile is a rule
      (STEEL_PROFILE_RULE) - UNKNOWN means eligible lm is reported and the
      profile quantity is NOT_ESTABLISHED
  §18 tartusha rooms: their own treatment and height parameter
  §19 columns: bonding + plaster is its own treatment; beams are not plaster
  §20 stairs: LINEAR_SURFACE_RUN, a stair-well height parameter; the
      underside is never approximated here
  §21 external plaster: per floor, height from the floor's owner storey
      height; per facade segment
  §22/§23 parapets: external face, internal face and capping are three
      treatments; a face's height comes from ITS traced dimension or is
      unresolved; no general parapet height exists
  §24 control joints: no spacing is invented - NOT_ESTABLISHED unless a
      rule parameter exists
  §28 floors are not ceilings: nothing here is a ceiling quantity
"""

from __future__ import annotations

from engine import material_role_audit as MRA
from engine.plaster_trade_engine import READER_SOURCE_TO_PROVENANCE, WEAK_READ_SOURCES
from research.a21_trace_sufficiency_01.parameters import PROVENANCE_RANK, RANK_TO_STATE

ENGINE_RULE_VERSION = "WTE-1.0"

TREATMENTS = (
    "NORMAL_INTERNAL_PLASTER", "DOUBLE_HEIGHT_PLASTER", "TILE_PREP_TARTUSHA",
    "COLUMN_BONDING_PLUS_PLASTER", "STAIR_WALL_PLASTER", "STAIR_UNDERSIDE",
    "OPENING_REVEALS_AND_RETURNS", "STEEL_CORNER_AND_EDGE_PROFILES",
    "EXTERNAL_PLASTER", "EXTERNAL_CONTROL_JOINT",
    "ROOF_PARAPET_EXTERNAL_FACE", "ROOF_PARAPET_INTERNAL_FACE",
    "ROOF_PARAPET_CAPPING",
)
FACE_TREATMENTS = tuple(t for t in TREATMENTS if t not in (
    "STAIR_UNDERSIDE", "OPENING_REVEALS_AND_RETURNS",
    "STEEL_CORNER_AND_EDGE_PROFILES", "EXTERNAL_CONTROL_JOINT"))

HEIGHT_PARAMETER_FOR = {
    "NORMAL_INTERNAL_PLASTER": "NORMAL_INTERNAL_PLASTER_HEIGHT",
    "COLUMN_BONDING_PLUS_PLASTER": "NORMAL_INTERNAL_PLASTER_HEIGHT",
    "DOUBLE_HEIGHT_PLASTER": "DOUBLE_HEIGHT_PLASTER_HEIGHT",
    "TILE_PREP_TARTUSHA": "TARTUSHA_HEIGHT",
    "STAIR_WALL_PLASTER": "STAIR_WELL_PLASTER_HEIGHT",
    "EXTERNAL_PLASTER": {"GROUND": "EXTERNAL_STOREY_HEIGHT_GROUND",
                         "FIRST": "EXTERNAL_STOREY_HEIGHT_FIRST",
                         "SECOND_ROOF_ROOM": "EXTERNAL_STOREY_HEIGHT_SECOND_ROOF_ROOM"},
    # parapets: the face's own traced height, else unresolved
    "ROOF_PARAPET_EXTERNAL_FACE": None,
    "ROOF_PARAPET_INTERNAL_FACE": None,
    "ROOF_PARAPET_CAPPING": None,      # width, not height: from the face
}
OPENING_DEFAULTS = {"DOOR": ("DOOR_WIDTH", "DOOR_HEIGHT"),
                    "WINDOW": ("WINDOW_WIDTH", "WINDOW_HEIGHT")}
REVEAL_DEPTH_PARAMETER = {"DOOR": "DOOR_REVEAL_DEPTH", "WINDOW": "WINDOW_REVEAL_DEPTH"}
PROFILE_CATEGORIES = ("DOOR_JAMB", "DOOR_HEAD", "WINDOW_JAMB", "WINDOW_HEAD",
                      "WINDOW_SILL", "EXTERNAL_CORNER", "OTHER")


def _prov(t) -> str:
    t = t or "UNKNOWN"
    return READER_SOURCE_TO_PROVENANCE.get(t, t)


def _state(sources) -> str:
    if not sources:
        return "NOT_APPLICABLE"
    return RANK_TO_STATE[max(PROVENANCE_RANK.get(_prov(s), 4) for s in sources)]


def _num(x) -> bool:
    return isinstance(x, (int, float))


def _param(reg, pid):
    p = reg.get(pid) or {}
    return p.get("VALUE"), (p.get("SOURCE_TYPE") or "UNKNOWN")


def _height_for(face: dict, reg: dict, treatment: str, floor: str | None):
    """(value, source, parameter_id or None). A face's own traced height
    wins for parapets; a treatment parameter otherwise; a face-level
    HEIGHT_PARAMETER override is honoured and recorded."""
    if face.get("HEIGHT_PARAMETER"):
        v, s = _param(reg, face["HEIGHT_PARAMETER"])
        return v, s, face["HEIGHT_PARAMETER"]
    if _num(face.get("height_m")):
        return face["height_m"], face.get("height_source") or "UNKNOWN", None
    hp = HEIGHT_PARAMETER_FOR.get(treatment)
    if isinstance(hp, dict):
        hp = hp.get(floor or "")
        if hp is None:
            return None, "UNKNOWN", None
    if hp is None:
        return None, "UNKNOWN", None
    v, s = _param(reg, hp)
    return v, s, hp


def calculate(face_set: dict, reg: dict, *, treatment: str,
              floor: str | None = None) -> dict:
    if treatment not in FACE_TREATMENTS:
        raise ValueError(f"{treatment} is not a face treatment")
    if face_set["TRADE"] != treatment:
        raise ValueError("face set was built for another trade")
    floor = floor or face_set.get("FLOOR")
    sheet, contributions = [], []
    inputs = {"ESTABLISHED": [], "PROVISIONAL": [], "REVEALS": [], "PROFILES": []}
    is_capping = treatment == "ROOF_PARAPET_CAPPING"
    dim_word = "WIDTH" if is_capping else "HEIGHT"

    def face_lines(bucket: str):
        total = 0.0
        for f in face_set[f"{bucket}_FACES"]:
            if is_capping:
                H, H_src, hp = f.get("width_m"), f.get("width_source") or "UNKNOWN", None
            else:
                H, H_src, hp = _height_for(f, reg, treatment, floor)
            L, L_src = f["length_m"], f.get("length_source") or "UNKNOWN"
            area = round(L * H, 4) if _num(L) and _num(H) else None
            inputs[bucket] += [L_src, H_src]
            sheet.append({
                "LINE": f"{bucket}_FACE", "FACE_ID": f["FACE_ID"],
                "PHYSICAL_OBJECT_ID": f.get("PHYSICAL_OBJECT_ID"),
                "MATERIAL_ROLE": f.get("MATERIAL_ROLE"),
                "LENGTH_M": L, "LENGTH_SOURCE": L_src,
                "LENGTH_BASIS": f.get("length_basis"),
                f"{dim_word}_M": H, f"{dim_word}_SOURCE": H_src,
                f"{dim_word}_PARAMETER": hp,
                "SUPPORTING_DIMENSIONS": f.get("supporting_dimensions"),
                "TRACE_IDS": f.get("trace_ids"),
                "CALC": f"{L} x {H} = {area}", "AREA_M2": area,
                "WHY_BUCKET": f.get("WHY"),
            })
            if area is None:
                total = None
            elif total is not None:
                total = round(total + area, 4)
            contributions.append({
                "TRADE_CONTRIBUTION_ID": MRA.trade_contribution_id(
                    treatment, f.get("PHYSICAL_OBJECT_ID") or f["FACE_ID"],
                    f.get("SIDE") or f["FACE_ID"], "FACE"),
                "TRADE": treatment, "PHYSICAL_OBJECT_ID": f.get("PHYSICAL_OBJECT_ID"),
                "FACE_ID": f.get("SIDE") or f["FACE_ID"], "ITEM": "FACE",
                "MATERIAL_ROLE": f.get("MATERIAL_ROLE"),
                "HOST_OBJECT": f.get("HOST_OBJECT"), "VALUE": area,
                "BUCKET": bucket, "TRACE_IDS": f.get("trace_ids"),
            })
        return total

    gross_est = face_lines("ESTABLISHED")
    gross_prov = face_lines("PROVISIONAL")
    for f in face_set["UNRESOLVED_FACES"]:
        sheet.append({"LINE": "UNRESOLVED_FACE", "FACE_ID": f["FACE_ID"],
                      "AREA_M2": None, "WHY": f["WHY"], "TRACE_IDS": f.get("trace_ids")})
    for f in face_set["EXCLUDED_FACES"]:
        sheet.append({"LINE": "EXCLUDED_FACE", "FACE_ID": f["FACE_ID"],
                      "MATERIAL_ROLE": f.get("MATERIAL_ROLE"), "AREA_M2": 0.0,
                      "WHY": f["WHY"]})
    sheet.append({"LINE": "ESTABLISHED_GROSS_SUBTOTAL", "AREA_M2": gross_est})
    sheet.append({"LINE": "PROVISIONAL_GROSS_SUBTOTAL", "AREA_M2": gross_prov,
                  "KEPT_APART": True})

    # ---- openings: deductions, reveals, profile-eligible edges ---
    ded_est, ded_prov, reveals = 0.0, 0.0, 0.0
    prof = {c: 0.0 for c in PROFILE_CATEGORIES}
    n_openings = 0
    for o in face_set["OPENINGS"]:
        st = o["DEDUCTION_STATUS"]
        if st.startswith("UNRESOLVED"):
            sheet.append({"LINE": "UNRESOLVED_OPENING", "OPENING_ID": o["OPENING_ID"],
                          "TYPE": o["TYPE"], "WHY": st, "AREA_M2": None})
            continue
        if is_capping:
            continue
        n_openings += 1
        wp, hp = OPENING_DEFAULTS.get(o["TYPE"], (None, None))
        w, w_src = o.get("width_m"), o.get("width_source")
        if not _num(w):
            w, w_src = _param(reg, wp or "")
        h, h_src = o.get("height_m"), o.get("height_source")
        if not _num(h):
            h, h_src = _param(reg, hp or "")
        w_src, h_src = w_src or "UNKNOWN", h_src or "UNKNOWN"
        bucket = "ESTABLISHED" if st.endswith("ESTABLISHED_FACE") else "PROVISIONAL"
        inputs[bucket] += [w_src, h_src]
        inputs["REVEALS"] += [w_src, h_src]
        inputs["PROFILES"] += [w_src, h_src]
        area = round(w * h, 4) if _num(w) and _num(h) else None
        if bucket == "ESTABLISHED":
            ded_est = None if area is None or ded_est is None else round(ded_est + area, 4)
        else:
            ded_prov = None if area is None or ded_prov is None else round(ded_prov + area, 4)
        sheet.append({"LINE": "DEDUCTION", "OPENING_ID": o["OPENING_ID"], "TYPE": o["TYPE"],
                      "FROM": bucket, "WIDTH_M": w, "WIDTH_SOURCE": w_src,
                      "HEIGHT_M": h, "HEIGHT_SOURCE": h_src,
                      "CALC": f"{w} x {h} = {area}", "AREA_M2": area,
                      "TRACE_IDS": o.get("trace_ids")})
        # §16 reveals: actual depth wins
        if _num(o.get("reveal_depth_m")):
            d, d_src = o["reveal_depth_m"], o.get("reveal_depth_source") or "UNKNOWN"
        else:
            d, d_src = _param(reg, REVEAL_DEPTH_PARAMETER.get(o["TYPE"], ""))
        inputs["REVEALS"].append(d_src)
        if _num(w) and _num(h) and _num(d):
            girth = (2 * h + w) if o["TYPE"] == "DOOR" else (2 * h + 2 * w)
            rv = round(girth * d, 4)
        else:
            girth, rv = None, None
        reveals = None if rv is None or reveals is None else round(reveals + rv, 4)
        sheet.append({"LINE": "REVEAL", "OPENING_ID": o["OPENING_ID"], "GIRTH_M": girth,
                      "DEPTH_M": d, "DEPTH_SOURCE": d_src, "CALC": f"{girth} x {d} = {rv}",
                      "AREA_M2": rv, "SEPARATE_FROM_THE_WALL_FACE": True})
        # §17 profile-eligible edges, lm per category
        if _num(w) and _num(h):
            if o["TYPE"] == "DOOR":
                prof["DOOR_JAMB"] += 2 * h
                prof["DOOR_HEAD"] += w
            elif o["TYPE"] == "WINDOW":
                prof["WINDOW_JAMB"] += 2 * h
                prof["WINDOW_HEAD"] += w
                prof["WINDOW_SILL"] += w
            else:
                prof["OTHER"] += 2 * h + w
        else:
            prof = {c: None for c in prof}
    # external corners: declared per face (count x face height)
    if prof.get("EXTERNAL_CORNER") is not None:
        for f in face_set["ESTABLISHED_FACES"]:
            n = f.get("EXTERNAL_CORNER_COUNT") or 0
            H, H_src, _ = _height_for(f, reg, treatment, floor)
            if n and _num(H):
                prof["EXTERNAL_CORNER"] += n * H
                inputs["PROFILES"].append(H_src)
            elif n:
                prof["EXTERNAL_CORNER"] = None

    principal_est = (round(gross_est - ded_est, 4) if _num(gross_est) and _num(ded_est) else None)
    principal_prov = (round(gross_prov - ded_prov, 4) if _num(gross_prov) and _num(ded_prov) else None)
    sheet.append({"LINE": "ESTABLISHED_SUBTOTAL",
                  "CALC": f"{gross_est} - {ded_est} = {principal_est}", "AREA_M2": principal_est})
    sheet.append({"LINE": "PROVISIONAL_SUBTOTAL",
                  "CALC": f"{gross_prov} - {ded_prov} = {principal_prov}",
                  "AREA_M2": principal_prov, "KEPT_APART": True})
    sheet.append({"LINE": "REVEALS_AND_RETURNS_SUBTOTAL", "AREA_M2": reveals,
                  "KEPT_SEPARATE_FROM_THE_WALL_FACE": True})
    rule_v, rule_src = _param(reg, "STEEL_PROFILE_RULE")
    for c in PROFILE_CATEGORIES:
        sheet.append({"LINE": "PROFILE_ELIGIBLE_EDGE", "CATEGORY": c, "UNIT": "lm",
                      "ELIGIBLE_LM": (round(prof[c], 4) if _num(prof[c]) else None),
                      "PROFILE_RULE": rule_src, "NEVER_ADDED_TO_M2": True})
    cj_v, cj_src = _param(reg, "CONTROL_JOINT_RULE")
    if treatment == "EXTERNAL_PLASTER":
        sheet.append({"LINE": "CONTROL_JOINTS", "UNIT": "lm", "VALUE": None,
                      "RULE_SOURCE": cj_src,
                      "WHY": "no spacing is invented; NOT_ESTABLISHED until a rule exists"})

    no_openings = n_openings == 0
    states = {
        "ESTABLISHED_SUBTOTAL": (_state(inputs["ESTABLISHED"])
                                 if principal_est is not None and face_set["ESTABLISHED_FACES"]
                                 else "NOT_ESTABLISHED"),
        "PROVISIONAL_SUBTOTAL": (_state(inputs["PROVISIONAL"])
                                 if principal_prov is not None and face_set["PROVISIONAL_FACES"]
                                 else ("NOT_APPLICABLE" if not face_set["PROVISIONAL_FACES"]
                                       else "NOT_ESTABLISHED")),
        "REVEALS_AND_RETURNS": ("NOT_APPLICABLE" if no_openings else
                                (_state(inputs["REVEALS"]) if reveals is not None
                                 else "NOT_ESTABLISHED")),
        "STEEL_PROFILES": ("NOT_APPLICABLE" if no_openings and not any(
            f.get("EXTERNAL_CORNER_COUNT") for f in face_set["ESTABLISHED_FACES"])
                           else "NOT_ESTABLISHED"),   # rule UNKNOWN -> never established
        "CONTROL_JOINTS": ("NOT_ESTABLISHED" if treatment == "EXTERNAL_PLASTER"
                           else "NOT_APPLICABLE"),
    }
    if rule_src != "UNKNOWN" and states["STEEL_PROFILES"] == "NOT_ESTABLISHED":
        states["STEEL_PROFILES"] = _state(inputs["PROFILES"] + [rule_src])
    all_inputs = [t for v in inputs.values() for t in v]
    guard = MRA.guard_contributions([c for c in contributions if c["BUCKET"] == "ESTABLISHED"])
    return {
        "TREATMENT": treatment, "SET_ID": face_set["SET_ID"], "FLOOR": floor,
        "ZONE": face_set.get("ZONE"),
        "ENGINE_RULE_VERSION": ENGINE_RULE_VERSION,
        "FACE_SET_RULE_VERSION": face_set["RULE_VERSION"],
        "MEASUREMENT_BASIS": face_set["MEASUREMENT_BASIS"],
        "SHEET": sheet,
        "RESULT": {
            "ESTABLISHED_SUBTOTAL_M2": principal_est,
            "PROVISIONAL_SUBTOTAL_M2": principal_prov,
            "REVEALS_AND_RETURNS_M2": reveals,
            "PROFILE_ELIGIBLE_LM": {c: (round(prof[c], 4) if _num(prof[c]) else None)
                                    for c in PROFILE_CATEGORIES},
            "COMPLETE_TOTAL_STATUS": face_set["COMPLETE_TOTAL_STATUS"],
            "COVERAGE_STATUS": face_set["COVERAGE_STATUS"],
            "UNRESOLVED_SCOPE": face_set["UNRESOLVED_SCOPE"],
            "THE_ESTABLISHED_SUBTOTAL_IS_NOT_THE_TOTAL":
                face_set["THE_ESTABLISHED_SUBTOTAL_IS_NOT_THE_TOTAL"],
            "M2_AND_LM_ARE_NEVER_COMBINED": True,
        },
        "QUANTITY_STATE": states,
        "INPUT_PROVENANCE": {k: sorted(set(v)) for k, v in inputs.items()},
        "INPUTS_THAT_ARE_WEAK_READS": sorted({t for t in all_inputs if t in WEAK_READ_SOURCES}),
        "CONTRIBUTIONS": contributions,
        "DOUBLE_COUNT_GUARD": guard,
        "NO_HIDDEN_ARITHMETIC": True,
        "NOT_A_CEILING_QUANTITY": True,
    }
