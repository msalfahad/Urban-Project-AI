"""PHYSICAL_POPULATION_CONSERVATION (generic).

    SOURCE OBJECT -> PHYSICAL OCCURRENCE -> TERMINAL OCCURRENCE RECORD          (no silent drop)

Every admitted physical occurrence ends in exactly one terminal record:

    MEASURED_COMPLETE      all geometry measured, quantity established
    MEASURED_PARTIAL       some geometry measured, some components unquantified
    CANDIDATE_QUANTIFIED   geometry known, meaning / dimension a candidate -> scenario quantity
    BOUNDED_QUANTIFIED     a dimension only bounded -> low / high quantity
    UNQUANTIFIED           exists (count, position, handles kept) but no quantity yet

A missing schedule row, a type conflict, a missing height, an unreadable detail, an uncertain floor binding or a
missing engineering interpretation may change the terminal state - never remove the occurrence. Schedule / legend /
detail rows are definitions and never become occurrences. Stdlib only.
"""

from __future__ import annotations

from collections import Counter

TERMINAL_STATES = ("MEASURED_COMPLETE", "MEASURED_PARTIAL", "CANDIDATE_QUANTIFIED", "BOUNDED_QUANTIFIED",
                   "UNQUANTIFIED")
DEFINITION_ROLES = ("SCHEDULE_ROW", "LEGEND", "DETAIL", "TYPICAL_SECTION", "NOTE")
KEEP_FIELDS = ("count", "position", "known_geometry", "source_handles", "candidate_definitions")


class ConservationError(ValueError):
    pass


def admit(source_objects):
    """Physical occurrences from source objects; definition rows are kept apart (never occurrences)."""
    occ, definitions = [], []
    seen = set()
    for o in source_objects:
        oid = o["object_id"]
        if oid in seen:
            raise ConservationError(f"source object {oid} admitted twice")
        seen.add(oid)
        if o.get("role") in DEFINITION_ROLES:
            definitions.append(oid)
            continue
        occ.append({"occurrence_id": o.get("occurrence_id") or oid, "source_object": oid,
                    "source_handles": list(o.get("source_handles") or []), "position": o.get("position"),
                    "count": o.get("count", 1), "known_geometry": dict(o.get("known_geometry") or {}),
                    "candidate_definitions": list(o.get("candidate_definitions") or [])})
    return {"occurrences": occ, "definitions_not_occurrences": definitions}


def terminal(occurrence, state, *, quantity=None, unresolved=(), why=None):
    """The terminal record of one occurrence: identity and known facts always survive."""
    if state not in TERMINAL_STATES:
        raise ConservationError(f"unknown terminal state {state}")
    if state == "MEASURED_COMPLETE" and unresolved:
        raise ConservationError(f"{occurrence['occurrence_id']}: MEASURED_COMPLETE with unresolved facts")
    if state != "UNQUANTIFIED" and quantity is None:
        raise ConservationError(f"{occurrence['occurrence_id']}: {state} needs a quantity")
    rec = {"occurrence_id": occurrence["occurrence_id"], "terminal_state": state, "quantity": quantity,
           "unresolved": list(unresolved), "why": why}
    for k in KEEP_FIELDS:
        rec[k] = occurrence.get(k)
    return rec


def conserve(occurrences, terminals):
    """In = out, one terminal per occurrence, no orphan terminal, no duplicate."""
    ids_in = [o["occurrence_id"] for o in occurrences]
    ids_out = [t["occurrence_id"] for t in terminals]
    dup_in = [k for k, n in Counter(ids_in).items() if n > 1]
    dup_out = [k for k, n in Counter(ids_out).items() if n > 1]
    missing = sorted(set(ids_in) - set(ids_out))
    orphan = sorted(set(ids_out) - set(ids_in))
    lost_identity = [t["occurrence_id"] for t in terminals
                     if t["terminal_state"] == "UNQUANTIFIED" and not (t.get("source_handles") or t.get("position"))]
    ok = not (dup_in or dup_out or missing or orphan or lost_identity)
    return {"ok": ok, "occurrences_in": len(ids_in), "terminal_records": len(ids_out),
            "by_state": dict(Counter(t["terminal_state"] for t in terminals)), "missing": missing,
            "orphans": orphan, "duplicates_in": dup_in, "duplicates_out": dup_out,
            "unquantified_without_identity": lost_identity}


def require_conserved(occurrences, terminals):
    r = conserve(occurrences, terminals)
    if not r["ok"]:
        raise ConservationError(f"population not conserved: {r}")
    return r
