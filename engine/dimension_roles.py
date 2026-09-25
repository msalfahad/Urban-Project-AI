"""DIMENSION ROLES - a printed value is not a length of anything until its
role is known.

    WALL_THICKNESS        20 / 15 beside a wall: block thickness, never a run
    LINEAR_SPAN           a wall or face run between two extension lines
    SETTING_OUT_SEGMENT   a segment of an external dimension chain: it
                          measures the setting-out, not a plaster face
    OVERALL_WIDTH         a structural / setting-out width across an opening
                          including its construction
    CLEAR_OPENING         the opening itself, after the construction on each
                          side is taken off

The lesson the owner set from the plan: OVERALL 150 with 20 + 20 of
construction is a CLEAR opening of 110. That arithmetic applies only to the
specific opening where the overall and both sides are actually traced; it
is never a universal door rule.
"""

from __future__ import annotations

DIMENSION_ROLES = ("WALL_THICKNESS", "LINEAR_SPAN", "SETTING_OUT_SEGMENT",
                   "OVERALL_WIDTH", "CLEAR_OPENING", "UNRESOLVED_ROLE")


def clear_opening_width(overall_m: float, sides_m: list) -> dict:
    """CLEAR = OVERALL - sum(sides). Every input must be traced for THIS
    opening; the result records what it was made of."""
    if not isinstance(overall_m, (int, float)) or not sides_m or \
            not all(isinstance(s, (int, float)) for s in sides_m):
        return {"CLEAR_OPENING_M": None, "STATUS": "NOT_ESTABLISHED",
                "WHY": "overall width and every side must be traced for this opening"}
    clear = round(overall_m - sum(sides_m), 4)
    return {"CLEAR_OPENING_M": clear, "OVERALL_WIDTH_M": overall_m, "SIDES_M": list(sides_m),
            "CALC": f"{overall_m} - {' - '.join(str(s) for s in sides_m)} = {clear}",
            "STATUS": "ESTABLISHED_FOR_THIS_OPENING_ONLY",
            "NOT_A_UNIVERSAL_RULE": True}


def chain_is_continuous(segments: list, tol_m: float = 0.005) -> dict:
    """segments: [{FROM_MM, TO_MM}] in chain order. Continuous only when
    each segment starts where the previous ended; a gap or overlap breaks
    it and the chain must not be summed as one."""
    breaks = []
    for a, b in zip(segments, segments[1:]):
        gap = (b["FROM_MM"] - a["TO_MM"]) / 1000.0
        if abs(gap) > tol_m:
            breaks.append({"AFTER": a.get("ID"), "BEFORE": b.get("ID"), "GAP_M": round(gap, 4)})
    return {"CONTINUOUS": not breaks, "BREAKS": breaks,
            "SUM_M": (round(sum((s["TO_MM"] - s["FROM_MM"]) / 1000.0 for s in segments), 4)
                      if not breaks else None)}
