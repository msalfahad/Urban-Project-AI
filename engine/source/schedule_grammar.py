"""SCHEDULE_GRAMMAR - reinforcement text grammar and schedule-cell provenance for machine-readable (attributed)
structural schedules.

    normalise(raw)                 -> CAD control codes to text (%%c / %%C -> Ø, %%u underline removed)
    parse_bar(raw)                 -> {"grammar", "count", "dia_mm", "per_m", "spacing_cm", "position", "raw", ...}
                                      grammar: COUNT_DIA | COUNT_DIA_PER_M | DIA_AT_SPACING | COUNT_DIA_AT_SPACING |
                                      UNPARSED; an UNPARSED text keeps its raw value and is BLOCKED_INTERPRETATION
    bar_from_cells(count, dia)     -> the same record from a count attribute + a diameter attribute ("14" or "14/m")
    cell(block, handle, tag, raw, *, drawing, layer, position, page=None) -> one provenance record
    key_conflicts(records, key)    -> SOURCE_CONFLICT_DUPLICATE_SCHEDULE_KEY groups (no row is chosen)

Grammar is token-level only: "2Ø12/30cm" is COUNT_DIA_AT_SPACING (2, 12, 30 cm) - what the count means for a beam
side face is an interpretation the caller must not apply without a detail (state CANDIDATE).
Stdlib only, project-agnostic.
"""

from __future__ import annotations

import re
from collections import defaultdict

POLICY_ID = "SCHEDULE_GRAMMAR_V1"
CONFLICT = "SOURCE_CONFLICT_DUPLICATE_SCHEDULE_KEY"

_PAT = [
    ("COUNT_DIA_AT_SPACING", re.compile(r"^(\d+)\s*Ø\s*(\d+)\s*(?:MM)?\s*/\s*(\d+)\s*cm$", re.I)),
    ("DIA_AT_SPACING", re.compile(r"^Ø\s*(\d+)\s*(?:MM)?\s*/\s*(\d+)\s*cm$", re.I)),
    ("COUNT_DIA_PER_M", re.compile(r"^(\d+)\s*Ø\s*(\d+)\s*/\s*m(?:\s+E\.?W\.?)?$", re.I)),
    ("COUNT_DIA_POSITION", re.compile(r"^(\d+)\s*Ø\s*(\d+)\s*/\s*(Top|Bot|Bottom)$", re.I)),
    ("COUNT_DIA", re.compile(r"^(\d+)\s*Ø\s*(\d+)$", re.I)),
]


def normalise(raw):
    if raw is None:
        return ""
    s = str(raw)
    s = re.sub(r"%%[cC]", "Ø", s)
    s = re.sub(r"%%[uUoO]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_bar(raw) -> dict:
    n = normalise(raw)
    out = {"raw": raw, "normalised": n, "grammar": "UNPARSED", "count": None, "dia_mm": None, "per_m": False,
           "spacing_cm": None, "position": None, "each_way": False}
    for g, p in _PAT:
        m = p.match(n)
        if not m:
            continue
        out["grammar"] = g
        if g == "COUNT_DIA_AT_SPACING":
            out.update(count=int(m[1]), dia_mm=int(m[2]), spacing_cm=int(m[3]))
        elif g == "DIA_AT_SPACING":
            out.update(dia_mm=int(m[1]), spacing_cm=int(m[2]))
        elif g == "COUNT_DIA_PER_M":
            out.update(count=int(m[1]), dia_mm=int(m[2]), per_m=True, each_way=bool(re.search(r"E\.?W", n, re.I)))
        elif g == "COUNT_DIA_POSITION":
            out.update(count=int(m[1]), dia_mm=int(m[2]), position=m[3].upper().replace("BOTTOM", "BOT"))
        else:
            out.update(count=int(m[1]), dia_mm=int(m[2]))
        break
    out["interpretation_state"] = "TOKENS_PARSED" if out["grammar"] != "UNPARSED" else "BLOCKED_INTERPRETATION"
    return out


def bar_from_cells(count_raw, dia_raw) -> dict:
    """A bar callout split over two attribute cells: count ('6') and diameter ('14' or '14/m')."""
    c, d = normalise(count_raw), normalise(dia_raw)
    if not c and not d:
        return {"grammar": "EMPTY", "count": None, "dia_mm": None, "per_m": False, "raw": [count_raw, dia_raw],
                "interpretation_state": "NOT_APPLICABLE"}
    m = re.match(r"^(\d+)\s*(/\s*m)?$", d)
    if not re.match(r"^\d+$", c) or not m:
        return {"grammar": "UNPARSED", "count": None, "dia_mm": None, "per_m": False, "raw": [count_raw, dia_raw],
                "interpretation_state": "BLOCKED_INTERPRETATION"}
    return {"grammar": "COUNT_DIA_PER_M" if m[2] else "COUNT_DIA", "count": int(c), "dia_mm": int(m[1]),
            "per_m": bool(m[2]), "raw": [count_raw, dia_raw], "interpretation_state": "TOKENS_PARSED"}


def cell(block, handle, tag, raw, *, drawing, layer=None, position=None, page=None) -> dict:
    return {"drawing": drawing, "page": page, "block": block, "insert_handle": handle, "layer": layer, "tag": tag,
            "raw": raw, "normalised": normalise(raw), "position": position}


def key_conflicts(records, key) -> list:
    """records sharing one schedule key with different content -> one conflict group; every row stays visible."""
    groups = defaultdict(list)
    for r in records:
        groups[r[key]].append(r)
    out = []
    for k, rs in sorted(groups.items()):
        contents = {tuple(sorted((t, v) for t, v in r["attributes"].items())) for r in rs}
        if len(rs) > 1 and len(contents) > 1:
            out.append({"key": k, "state": CONFLICT, "rows": [r.get("handle") for r in rs],
                        "variants": [r["attributes"] for r in rs]})
    return out
