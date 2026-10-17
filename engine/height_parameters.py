"""Project height parameter table (PA04 §9): no single plaster height is
hard-coded; every scope carries VALUE / SOURCE / STATUS / EFFECTIVE_SCOPE /
OWNER_OVERRIDE / REVISION.  A scope with no value still allows lm outputs.
"""

from __future__ import annotations

SCOPES = ("GROUND_NORMAL_INTERNAL", "FIRST_NORMAL_INTERNAL", "SECOND_ROOF_NORMAL_INTERNAL", "RECEPTION_DOUBLE_HEIGHT",
          "STAIR_WELL_BY_SEGMENT", "EXTERNAL_FACE_BY_STOREY", "PARAPET_FACE", "WET_ROOM_TILE_PREP")
STATUSES = ("OWNER_AUTHORISED", "SOURCE_ESTABLISHED", "PROVISIONAL", "NOT_ESTABLISHED")


def parameter(*, scope, value, source, status, effective_scope, owner_override=None, revision=1, note=None, segments=None):
    if scope not in SCOPES:
        raise ValueError(f"unknown height scope {scope}")
    if status not in STATUSES:
        raise ValueError(f"unknown status {status}")
    if status == "NOT_ESTABLISHED" and value is not None:
        raise ValueError("a NOT_ESTABLISHED height carries no value")
    if status == "OWNER_AUTHORISED" and not owner_override:
        raise ValueError("OWNER_AUTHORISED needs the owner record reference in owner_override")
    return {"SCOPE": scope, "VALUE": value, "SOURCE": source, "STATUS": status, "EFFECTIVE_SCOPE": effective_scope,
            "OWNER_OVERRIDE": owner_override, "REVISION": revision, "NOTE": note, "SEGMENTS": segments,
            "LM_OUTPUT_ALLOWED_WITHOUT_VALUE": True}


def table(params):
    seen = set()
    for p in params:
        if p["SCOPE"] in seen:
            raise ValueError(f"duplicate scope {p['SCOPE']}")
        seen.add(p["SCOPE"])
    missing = [s for s in SCOPES if s not in seen]
    return {"PARAMETERS": list(params), "MISSING_SCOPES": missing, "GLOBAL_HEIGHT_HARDCODED": False}


def area_from(length_m, param):
    """Area only when the scope's height exists; otherwise the lm stands alone."""
    if param["VALUE"] is None:
        return {"LM": length_m, "M2": None, "STATE": "NOT_ESTABLISHED", "WHY": f"{param['SCOPE']} height {param['STATUS']}"}
    state = {"OWNER_AUTHORISED": "OWNER_PARAMETRIC_QUANTITY", "SOURCE_ESTABLISHED": "SOURCE_ESTABLISHED_QUANTITY", "PROVISIONAL": "PROVISIONAL_QUANTITY"}[param["STATUS"]]
    return {"LM": length_m, "M2": round(length_m * param["VALUE"], 4), "STATE": state, "HEIGHT_SCOPE": param["SCOPE"], "HEIGHT_REVISION": param["REVISION"]}
