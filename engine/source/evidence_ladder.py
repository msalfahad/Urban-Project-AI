"""Explicit fallback ladders per fact type (generic).

A missing fact is looked for level by level, in a fixed order, and every level that was tried is recorded - also the
ones that found nothing or were not available. The first level that answers wins; its authority and fact origin
travel with the value. A level is never skipped silently, and nothing below the source levels is ever reported as a
source fact. Stdlib only.
"""

from __future__ import annotations

# (level_id, fact_origin, authority, kind)  kind: VALUE (one value) / RANGE (low-high) / NONE
LADDERS = {
    "MEMBER_DIMENSION": (
        ("LOCAL_EXPLICIT_DIMENSION", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("LOCAL_DETAIL", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("OCCURRENCE_BOUND_SCHEDULE", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("TYPE_SCHEDULE", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("PAIRED_GEOMETRY", "DERIVED", "VERIFIED", "VALUE"),
        ("REPEATED_IDENTICAL_OCCURRENCES", "DERIVED", "PROVISIONAL", "VALUE"),
        ("PROJECT_GENERAL_RULE", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("APPROVED_ENGINEERING_METHOD", "ENGINEERING_METHOD", "PROVISIONAL", "VALUE"),
        ("URBAN_PROVISIONAL_FALLBACK", "URBAN_PROVISIONAL", "PROVISIONAL", "RANGE"),
        ("UNKNOWN", None, "BLOCKED", "NONE"),
    ),
    "WALL_HEIGHT": (
        ("EXPLICIT_LOCAL_HEIGHT", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("ARCHITECTURAL_LEVEL_ELEVATION", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("STRUCTURAL_INTERVAL_MINUS_MEMBER", "DERIVED", "VERIFIED", "VALUE"),   # printed levels - scheduled depth
        ("FLOOR_TO_FLOOR_MINUS_STRUCTURE", "DERIVED", "PROVISIONAL", "VALUE"),
        ("ROOM_HEIGHT_NOTE", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("PROJECT_DEFAULT_FINISH_HEIGHT", "HUMAN_CLAIM", "PROVISIONAL", "VALUE"),
        ("URBAN_PROVISIONAL_SCENARIO", "URBAN_PROVISIONAL", "PROVISIONAL", "RANGE"),
        ("UNKNOWN", None, "BLOCKED", "NONE"),
    ),
    "GROUND_BEAM_DEPTH": (
        ("LOCAL_DIMENSION", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("SCHEDULE", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("DETAIL", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("SAME_MARK_ELSEWHERE", "DERIVED", "PROVISIONAL", "VALUE"),
        ("PAIRED_FACES_SECTION_GEOMETRY", "DERIVED", "VERIFIED", "VALUE"),
        ("PROJECT_TYPICAL", "SOURCE_FACT", "PROVISIONAL", "VALUE"),
        ("BOUNDED_CANDIDATE", "DERIVED", "PROVISIONAL", "RANGE"),
        ("UNKNOWN", None, "BLOCKED", "NONE"),
    ),
    "SLAB_THICKNESS": (
        ("PRINTED_IN_REGION", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("SECTION_OR_DETAIL", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("SAME_SHEET_TYPICAL_LABEL", "SOURCE_FACT", "PROVISIONAL", "VALUE"),
        ("PROJECT_GENERAL_RULE", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("URBAN_PROVISIONAL_FALLBACK", "URBAN_PROVISIONAL", "PROVISIONAL", "RANGE"),
        ("UNKNOWN", None, "BLOCKED", "NONE"),
    ),
    "MEMBER_BINDING": (
        ("NEARBY_TAG", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("PAIRED_FACES", "DERIVED", "VERIFIED", "VALUE"),
        ("COLUMN_ENDPOINTS", "DERIVED", "VERIFIED", "VALUE"),
        ("CONTINUITY_WITH_ADJACENT_SPAN", "DERIVED", "PROVISIONAL", "VALUE"),
        ("SCHEDULE_WIDTH_MATCH", "DERIVED", "PROVISIONAL", "VALUE"),
        ("SAME_TYPE_MEDIAN_LENGTH", "URBAN_PROVISIONAL", "PROVISIONAL", "RANGE"),
        ("UNKNOWN", None, "BLOCKED", "NONE"),
    ),
    "TEXT_READING": (
        ("CAD_TEXT", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("PDF_VECTOR_TEXT", "SOURCE_FACT", "VERIFIED", "VALUE"),
        ("NORMALISED_ARABIC_DECODE", "DERIVED", "VERIFIED", "VALUE"),
        ("VISUAL_INSPECTION", "DERIVED", "PROVISIONAL", "VALUE"),
        ("HUMAN_REVIEW", None, "BLOCKED", "NONE"),
    ),
}


class LadderError(ValueError):
    pass


def resolve(fact_type, resolvers, context=None):
    """resolvers: {level_id: callable(context) -> None | {value | low+high, ref}}. Levels without a resolver are
    recorded NOT_AVAILABLE; levels that return None are recorded NOT_FOUND. Returns the resolution + attempts."""
    if fact_type not in LADDERS:
        raise LadderError(f"no ladder for {fact_type}")
    unknown = set(resolvers) - {lvl[0] for lvl in LADDERS[fact_type]}
    if unknown:
        raise LadderError(f"resolver for a level not on the {fact_type} ladder: {sorted(unknown)}")
    attempts = []
    for rank, (lvl, origin, authority, kind) in enumerate(LADDERS[fact_type], 1):
        if kind == "NONE":
            attempts.append({"rank": rank, "level": lvl, "result": "TERMINAL_UNKNOWN"})
            return {"fact_type": fact_type, "resolved": False, "level": lvl, "rank": rank, "value": None,
                    "low": None, "high": None, "fact_origin": None, "authority": authority, "attempts": attempts}
        fn = resolvers.get(lvl)
        if fn is None:
            attempts.append({"rank": rank, "level": lvl, "result": "NOT_AVAILABLE"})
            continue
        got = fn(context)
        if not got:
            attempts.append({"rank": rank, "level": lvl, "result": "NOT_FOUND"})
            continue
        if kind == "VALUE" and got.get("value") is None:
            raise LadderError(f"{lvl} must return a value")
        if kind == "RANGE" and (got.get("low") is None or got.get("high") is None):
            raise LadderError(f"{lvl} must return low and high")
        attempts.append({"rank": rank, "level": lvl, "result": "FOUND", "ref": got.get("ref")})
        value = got.get("value")
        if value is None:
            value = got.get("best", (got["low"] + got["high"]) / 2.0)
        lo = got.get("low") if got.get("low") is not None else value
        hi = got.get("high") if got.get("high") is not None else value
        return {"fact_type": fact_type, "resolved": True, "level": lvl, "rank": rank, "value": value,
                "low": lo, "high": hi, "ref": got.get("ref"),
                "fact_origin": origin, "authority": authority, "attempts": attempts}
    raise LadderError(f"{fact_type} ladder has no terminal level")


def levels(fact_type):
    return [lvl[0] for lvl in LADDERS[fact_type]]
