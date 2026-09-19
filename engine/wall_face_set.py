"""WALL_FACE_SET / LINEAR_SURFACE_RUN - the measurement basis for wall
plaster that needs NO closed polygon (§9, §11, §12).

Wall plaster is applied to faces. A face has a length and a height; a
room ring is a floor-area instrument, not a plaster instrument. So the
basis here is a SET OF FACES, each carrying its own provenance, and the
result is a PARTIAL QUANTITY ARCHITECTURE:

    ESTABLISHED_SUBTOTAL     faces with an established length from a
                             permitted source and an established trace
    PROVISIONAL_SUBTOTAL     faces that exist provisionally or whose length
                             is a derived chain - reported apart, never
                             added to the established subtotal
    UNRESOLVED_SCOPE         faces with no established length or role, or
                             faces the trace could not establish - listed,
                             never bridged, never estimated
    EXCLUDED_FACES           faces whose material role carries no plaster
                             (glazing, open edges, open balustrades)
    COVERAGE_STATUS          how much of the zone the face set covers
    COMPLETE_TOTAL_STATUS    ESTABLISHED only when coverage is complete and
                             nothing is unresolved - otherwise NOT_ESTABLISHED

The established subtotal is a truthful smaller number. It is never called
the total. A face set built from a traced subset can never claim complete
coverage: SET_COMPLETENESS is declared by the caller and recorded.
"""

from __future__ import annotations

from engine import material_role_audit as MRA
from engine import qs_measurement_region as M

FACE_SET_RULE_VERSION = "QSMR-FS-1.0"

BASIS_TYPES = ("CLOSED_REGION", "WALL_FACE_SET", "LINEAR_SURFACE_RUN",
               "POLYGON_SURFACE", "CURVED_SURFACE")
FACE_SET_BASES = ("WALL_FACE_SET", "LINEAR_SURFACE_RUN")

# which contribution roles each wall-treatment trade accepts as a face
TRADE_ACCEPTS = {
    "NORMAL_INTERNAL_PLASTER": ("PLASTER_FACE",),
    "DOUBLE_HEIGHT_PLASTER": ("PLASTER_FACE",),
    "TILE_PREP_TARTUSHA": ("PLASTER_FACE",),
    "STAIR_WALL_PLASTER": ("PLASTER_FACE",),
    "COLUMN_BONDING_PLUS_PLASTER": ("COLUMN_BONDING_PLUS_PLASTER",),
    "EXTERNAL_PLASTER": ("PLASTER_FACE", "COLUMN_BONDING_PLUS_PLASTER"),
    "ROOF_PARAPET_EXTERNAL_FACE": ("PARAPET_FACE_PLASTER",),
    "ROOF_PARAPET_INTERNAL_FACE": ("PARAPET_FACE_PLASTER",),
    "ROOF_PARAPET_CAPPING": ("PARAPET_CAPPING",),
}
LENGTH_BASES = ("PRINTED_DIMENSION", "DERIVED_CHAIN", "SCALED_MEASUREMENT",
                "CAD_GEOMETRY", None)
SET_COMPLETENESS = ("TRACED_SUBSET", "ALL_FACES_DECLARED")


def classify_face(face: dict, trade: str) -> tuple:
    """-> (bucket, why). bucket in ESTABLISHED / PROVISIONAL / UNRESOLVED /
    EXCLUDED."""
    role = face.get("MATERIAL_ROLE") or "UNRESOLVED"
    crole = MRA.TRADE_CONTRIBUTION_ROLE.get(role, "UNRESOLVED")
    if role == "UNRESOLVED" or crole == "UNRESOLVED":
        return "UNRESOLVED", "material role not established"
    if crole not in TRADE_ACCEPTS.get(trade, ()):
        return "EXCLUDED", (f"{role} carries no {trade} face "
                            f"(contribution role {crole})")
    L = face.get("length_m")
    basis = face.get("length_basis")
    vts = face.get("VISUAL_TRACE_STATUS")
    if vts in ("TRACE_AMBIGUOUS", "TRACE_NOT_ESTABLISHED"):
        return "UNRESOLVED", f"trace status {vts}"
    if not isinstance(L, (int, float)):
        return "UNRESOLVED", "no established length"
    if basis == "SCALED_MEASUREMENT":
        return "UNRESOLVED", "length is a scaled measurement, not used"
    if vts == "TRACE_PROVISIONAL" or basis == "DERIVED_CHAIN":
        return "PROVISIONAL", (f"trace {vts}" if vts == "TRACE_PROVISIONAL"
                               else "length derived from a dimension chain")
    return "ESTABLISHED", "established trace with a printed or CAD length"


def build_face_set(*, set_id: str, faces: list, openings: list, trade: str,
                   basis: str, zone: str | None = None, floor: str | None = None,
                   set_completeness: str = "TRACED_SUBSET",
                   rule_version: str = FACE_SET_RULE_VERSION) -> dict:
    if basis not in FACE_SET_BASES:
        raise ValueError(f"{basis} is not a face-set basis; use build_region "
                         f"for CLOSED_REGION, or a surface builder")
    if set_completeness not in SET_COMPLETENESS:
        raise ValueError(f"unknown SET_COMPLETENESS {set_completeness}")
    if trade not in TRADE_ACCEPTS:
        raise ValueError(f"no face-set rule for trade {trade}")
    buckets = {"ESTABLISHED": [], "PROVISIONAL": [], "UNRESOLVED": [], "EXCLUDED": []}
    for f in faces:
        if f.get("length_basis") not in LENGTH_BASES:
            raise ValueError(f"unknown length_basis {f.get('length_basis')}")
        b, why = classify_face(f, trade)
        rec = dict(f)
        rec["BUCKET"] = b
        rec["WHY"] = why
        rec["TRADE_CONTRIBUTION_ROLE"] = MRA.TRADE_CONTRIBUTION_ROLE.get(
            f.get("MATERIAL_ROLE") or "UNRESOLVED", "UNRESOLVED")
        buckets[b].append(rec)
    est_lm = round(sum(f["length_m"] for f in buckets["ESTABLISHED"]), 4)
    prov_lm = round(sum(f["length_m"] for f in buckets["PROVISIONAL"]), 4)
    est_ids = {f["FACE_ID"] for f in buckets["ESTABLISHED"]}
    prov_ids = {f["FACE_ID"] for f in buckets["PROVISIONAL"]}
    ops = []
    for o in openings:
        host = o.get("HOSTED_IN")
        host = host[0] if isinstance(host, list) and host else host
        rec = dict(o)
        if host in est_ids:
            rec["DEDUCTION_STATUS"] = "DEDUCTIBLE_FROM_ESTABLISHED_FACE"
        elif host in prov_ids:
            rec["DEDUCTION_STATUS"] = "DEDUCTIBLE_FROM_PROVISIONAL_FACE"
        else:
            rec["DEDUCTION_STATUS"] = "UNRESOLVED_OPENING_HOST_NOT_ESTABLISHED"
        ops.append(rec)
    unresolved_scope = [{"FACE_ID": f["FACE_ID"], "WHY": f["WHY"],
                         "TRACE_IDS": f.get("trace_ids")}
                        for f in buckets["UNRESOLVED"]]
    if set_completeness == "TRACED_SUBSET":
        unresolved_scope.append({
            "FACE_ID": "*", "WHY": "the face set is a traced subset; faces of "
                                   "this zone that were not traced are outside "
                                   "it and are not estimated"})
    if not faces:
        coverage = "NONE"
    elif set_completeness == "ALL_FACES_DECLARED" and not buckets["UNRESOLVED"] \
            and not buckets["PROVISIONAL"]:
        coverage = "COMPLETE"
    elif buckets["ESTABLISHED"] or buckets["PROVISIONAL"]:
        coverage = "PARTIAL"
    else:
        coverage = "NONE"
    body = {
        "SET_ID": set_id, "RULE_VERSION": rule_version,
        "MEASUREMENT_BASIS": basis, "TRADE": trade,
        "ZONE": zone, "FLOOR": floor,
        "SET_COMPLETENESS": set_completeness,
        "NO_CLOSED_POLYGON_REQUIRED": True,
        "ESTABLISHED_FACES": buckets["ESTABLISHED"],
        "PROVISIONAL_FACES": buckets["PROVISIONAL"],
        "UNRESOLVED_FACES": buckets["UNRESOLVED"],
        "EXCLUDED_FACES": buckets["EXCLUDED"],
        "GROSS_BASIS": {
            "ESTABLISHED_LM": est_lm, "PROVISIONAL_LM": prov_lm,
            "IS_A_POLYGON_PERIMETER": False,
            "IS_A_SUM_OF_FACE_LENGTHS": True,
            "STATUS": "ESTABLISHED_SUBTOTAL" if buckets["ESTABLISHED"] else "NOT_ESTABLISHED",
        },
        "OPENINGS": ops,
        "COVERAGE_STATUS": coverage,
        "COMPLETE_TOTAL_STATUS": "ESTABLISHED" if coverage == "COMPLETE" else "NOT_ESTABLISHED",
        "UNRESOLVED_SCOPE": unresolved_scope,
        "THE_ESTABLISHED_SUBTOTAL_IS_NOT_THE_TOTAL": coverage != "COMPLETE",
    }
    body["INVARIANTS"] = {
        "FACE_SET_SHA256": M.canon_hash({k: v for k, v in body.items()}),
        "NO_SYNTHETIC_CLOSURE_WAS_NEEDED": True,
        "NO_GAP_WAS_BRIDGED": True,
    }
    return body
