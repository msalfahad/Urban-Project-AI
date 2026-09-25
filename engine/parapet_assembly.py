"""PARAPET ASSEMBLY MODEL - what physical material exists at a roof edge,
before any plaster quantity is asked (directive §2-§5).

A roof edge is not one "parapet". It is an assembly of components, each
with its own geometry, material status, and its own faces. A printed
dimension belongs to a component; a face belongs to a component; a
quantity belongs to a face. Balustrade and handrail components carry
zero plasterable face by construction.
"""

from __future__ import annotations

import math

COMPONENT_TYPES = (
    "SLAB_ROOF_DATUM", "SOLID_PARAPET", "SOLID_KERB", "CURVED_UPSTAND",
    "BALUSTRADE", "HANDRAIL", "COPING_CAPPING", "FACADE_WALL",
    "TOWER_DOME_FEATURE", "STRUCTURAL_EDGE", "EXTERNAL_FINISH_FACE",
    "INTERNAL_ROOF_SIDE_FACE", "UNKNOWN_COMPONENT",
)
ZERO_PLASTER_TYPES = ("BALUSTRADE", "HANDRAIL", "SLAB_ROOF_DATUM",
                      "TOWER_DOME_FEATURE", "UNKNOWN_COMPONENT")
GEOMETRY_TYPES = ("LINE", "ARC", "POLYLINE", "SPLINE", "LEVEL", "POINT", "NONE")
MATERIAL_STATUSES = ("SOLID_MASONRY_OR_RC", "OPEN_METAL", "SOLID_PROVISIONAL",
                     "FINISH_LAYER_UNKNOWN", "NOT_ESTABLISHED", "NOT_A_MATERIAL")
FACE_STATUSES = ("ELIGIBLE", "ELIGIBLE_PROVISIONAL", "ZERO_BY_MATERIAL",
                 "NOT_ESTABLISHED", "NOT_APPLICABLE")
CORRESPONDENCE = ("ESTABLISHED_CORRESPONDENCE", "PROPOSED_CORRESPONDENCE",
                  "NO_CORRESPONDENCE", "NOT_ATTEMPTED")
CURVE_TYPES = ("STRAIGHT", "ARC", "POLYLINE_WITH_BULGES", "SPLINE", "MIXED")
REQUIRED = (
    "ASSEMBLY_ID", "SHEET_ID", "SOURCE_OBJECT_ID", "CAD_OBJECT_ID", "COMPONENT_TYPE",
    "GEOMETRY_TYPE", "START_POINT", "END_POINT", "LENGTH", "HEIGHT", "THICKNESS",
    "CURVED_OR_STRAIGHT", "MATERIAL_STATUS", "PLASTERABLE_EXTERNAL_FACE_STATUS",
    "PLASTERABLE_INTERNAL_FACE_STATUS", "COPING_STATUS", "BALUSTRADE_STATUS",
    "HANDRAIL_STATUS", "SOURCE_DIMENSION_IDS", "DIMENSION_OWNER_STATUS",
    "SOURCE_CONFIDENCE_STATUS", "OWNER_VERIFICATION_STATUS", "QUANTITY_ELIGIBILITY",
    "PROVENANCE",
)
FACE_SIDES = ("EXTERNAL", "ROOF_SIDE", "TOP", "END", "INTERNAL")


def developed_length(entities) -> dict:
    """Sum of authored entity lengths: a LINE by its endpoints, an ARC by
    r * sweep, never a chord and never a bounding box.

    entities: [{KIND: LINE|ARC, ... , length_mm | (radius_mm, sweep_rad)}]
    """
    total = 0.0
    kinds = set()
    for e in entities:
        k = e["KIND"]
        kinds.add(k)
        if k == "LINE":
            total += float(e["length_mm"])
        elif k == "ARC":
            total += float(e["radius_mm"]) * abs(float(e["sweep_rad"]))
        elif k == "POLYLINE_SPAN":
            total += float(e["length_mm"])
        else:
            raise ValueError(f"unsupported entity kind {k}")
    curve = ("STRAIGHT" if kinds <= {"LINE", "POLYLINE_SPAN"}
             else "ARC" if kinds == {"ARC"} else "MIXED")
    return {"DEVELOPED_LENGTH_M": round(total / 1000.0, 4),
            "CURVE_TYPE": curve, "SOURCE_ENTITY_IDS": [e.get("ID") for e in entities],
            "CHORD_OR_BBOX_USED": False}


def component(**f) -> dict:
    missing = [k for k in REQUIRED if k not in f]
    if missing:
        raise ValueError(f"component {f.get('ASSEMBLY_ID')}: missing {missing}")
    if f["COMPONENT_TYPE"] not in COMPONENT_TYPES:
        raise ValueError(f"unknown COMPONENT_TYPE {f['COMPONENT_TYPE']}")
    if f["GEOMETRY_TYPE"] not in GEOMETRY_TYPES:
        raise ValueError(f"unknown GEOMETRY_TYPE {f['GEOMETRY_TYPE']}")
    if f["MATERIAL_STATUS"] not in MATERIAL_STATUSES:
        raise ValueError(f"unknown MATERIAL_STATUS {f['MATERIAL_STATUS']}")
    for k in ("PLASTERABLE_EXTERNAL_FACE_STATUS", "PLASTERABLE_INTERNAL_FACE_STATUS"):
        if f[k] not in FACE_STATUSES:
            raise ValueError(f"{f['ASSEMBLY_ID']}: {k}={f[k]} not in {FACE_STATUSES}")
    if f["COMPONENT_TYPE"] in ZERO_PLASTER_TYPES:
        for k in ("PLASTERABLE_EXTERNAL_FACE_STATUS", "PLASTERABLE_INTERNAL_FACE_STATUS"):
            if f[k] not in ("ZERO_BY_MATERIAL", "NOT_APPLICABLE"):
                raise ValueError(f"{f['ASSEMBLY_ID']}: a {f['COMPONENT_TYPE']} carries no "
                                 f"plasterable face ({k}={f[k]})")
        f["PLASTERABLE_SOLID_FACE_M2"] = 0.0
    return dict(f)


def face(*, face_id, component_id, side, bottom, bottom_source, top, top_source,
         material, eligibility, length_m=None, length_source=None, notes=None,
         area_from_polygon_m2=None, polygon_source=None) -> dict:
    if side not in FACE_SIDES:
        raise ValueError(f"unknown FACE_SIDE {side}")
    if eligibility not in FACE_STATUSES:
        raise ValueError(f"unknown eligibility {eligibility}")
    h = (round(top - bottom, 3) if isinstance(top, (int, float))
         and isinstance(bottom, (int, float)) else None)
    if h is not None and h <= 0:
        raise ValueError(f"{face_id}: FACE_TOP must exceed FACE_BOTTOM")
    return {"FACE_ID": face_id, "COMPONENT_ID": component_id, "FACE_SIDE": side,
            "FACE_BOTTOM": bottom, "FACE_BOTTOM_SOURCE": bottom_source,
            "FACE_TOP": top, "FACE_TOP_SOURCE": top_source, "FACE_HEIGHT": h,
            "FACE_MATERIAL": material, "FACE_PLASTER_ELIGIBILITY": eligibility,
            "FACE_LENGTH_M": length_m, "FACE_LENGTH_SOURCE": length_source,
            "AREA_FROM_POLYGON_M2": area_from_polygon_m2, "POLYGON_SOURCE": polygon_source,
            "NOTES": notes or []}


def face_area(f: dict) -> dict:
    """Gross face area with the weakest-input state; zero by material when
    the face is not eligible."""
    from engine.quantity_state import weakest
    if f["FACE_PLASTER_ELIGIBILITY"] in ("ZERO_BY_MATERIAL", "NOT_APPLICABLE"):
        return {"GROSS_AREA_M2": 0.0, "QUANTITY_STATE": "SOURCE_ESTABLISHED_QUANTITY",
                "WHY": f["FACE_PLASTER_ELIGIBILITY"]}
    if f["FACE_PLASTER_ELIGIBILITY"] == "NOT_ESTABLISHED":
        ref = (round(f["FACE_HEIGHT"] * f["FACE_LENGTH_M"], 4)
               if isinstance(f["FACE_HEIGHT"], (int, float)) and isinstance(f["FACE_LENGTH_M"], (int, float)) else None)
        return {"GROSS_AREA_M2": None, "REFERENCE_GROSS_M2_IF_ELIGIBLE": ref,
                "QUANTITY_STATE": "NOT_ESTABLISHED", "WHY": "plaster eligibility of this face is not established"}
    if f.get("AREA_FROM_POLYGON_M2") is not None:
        st = weakest([f["POLYGON_SOURCE"], f["FACE_LENGTH_SOURCE"], "PROVISIONAL"])
        return {"GROSS_AREA_M2": round(f["AREA_FROM_POLYGON_M2"], 4), "QUANTITY_STATE": st,
                "WHY": "area from a traced face polygon (variable-height profile)"}
    if f["FACE_HEIGHT"] is None or f["FACE_LENGTH_M"] is None:
        return {"GROSS_AREA_M2": None, "QUANTITY_STATE": "NOT_ESTABLISHED",
                "WHY": "height or length missing"}
    st = weakest([f["FACE_BOTTOM_SOURCE"], f["FACE_TOP_SOURCE"], f["FACE_LENGTH_SOURCE"]])
    if f["FACE_PLASTER_ELIGIBILITY"] == "ELIGIBLE_PROVISIONAL":
        st = weakest([st, "PROVISIONAL"])
    return {"GROSS_AREA_M2": round(f["FACE_HEIGHT"] * f["FACE_LENGTH_M"], 4),
            "QUANTITY_STATE": st, "WHY": None}
