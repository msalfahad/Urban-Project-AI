"""OWNER_DECISION_QUEUE (§22): an ambiguity is queued with its evidence and
its options; unrelated work continues. Only a materially blocking item
stops the run."""

from __future__ import annotations

FIELDS = ("DECISION_ID", "LOCATION", "TRADE", "QUESTION", "WHY_SOURCE_HIERARCHY_FAILED",
          "AVAILABLE_EVIDENCE", "OPTION_A", "OPTION_B", "OPTION_C_IF_REQUIRED",
          "QUANTITY_IMPACT_IF_KNOWN", "BLOCKS_WHAT", "CAN_OTHER_WORK_CONTINUE", "VISUAL_CARD")
PRIORITY = ("BLOCKS_LARGE_SCOPE", "QUANTITY_AFFECTING_SMALL", "CLASSIFICATION_ONLY", "INFORMATION")


def item(**f) -> dict:
    missing = [k for k in FIELDS if k not in f]
    if missing:
        raise ValueError(f"decision {f.get('DECISION_ID')}: missing {missing}")
    if f.get("PRIORITY", "QUANTITY_AFFECTING_SMALL") not in PRIORITY:
        raise ValueError("unknown priority")
    f.setdefault("PRIORITY", "QUANTITY_AFFECTING_SMALL")
    f.setdefault("TECHNICAL_RECOMMENDATION", None)
    f.setdefault("STATUS", "OPEN")
    return dict(f)


def stop_gate(queue: list) -> dict:
    """The run stops for the owner only when a decision blocks a large
    portion of the next phase or would require inventing geometry."""
    blocking = [q["DECISION_ID"] for q in queue if q["PRIORITY"] == "BLOCKS_LARGE_SCOPE"
                or q["CAN_OTHER_WORK_CONTINUE"] is False]
    return {"STOP_REQUIRED": bool(blocking), "BLOCKING": blocking,
            "OPEN": [q["DECISION_ID"] for q in queue if q["STATUS"] == "OPEN"]}
