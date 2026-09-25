"""The evidence barrier: one frozen opening state that every derived register is built from.

R6 resolved window heights from the room standard AFTER it had already built the opening register, the
deductions, the dependency graph and the question register.  The height evidence lived in a dict the opening
object shared with the admission record, so that dict updated in place and read as ESTABLISHED - while the
serialised registers beside it still carried the pre-category snapshot, with a null area and a question asking
for the height that had just been answered.  Every one of those records was internally consistent.  Together
they described two different moments.

The fix is not to rebuild the registers in the right order by hand each time.  It is to make "the evidence is
final" an explicit, checkable event:

    admit -> resolve hosts -> assemble the spaces room-use needs -> resolve room evidence
          -> resolve every remaining dimension -> FREEZE -> derive everything else

`freeze` takes the final opening state and returns it with a version derived from its own contents.  Every
register built afterwards records that version.  `verify` re-reads the live objects and reports whether they
still agree with the frozen state, so a later mutation cannot pass unnoticed - and the acceptance gate can ask
the question a reader cannot: are these registers all describing the same moment?
"""

from __future__ import annotations

import hashlib
import json

from engine.qs_core import evidence as EV

UNVERSIONED = "NO_EVIDENCE_VERSION_RECORDED"
VERSION_FIELD = "DERIVED_FROM_EVIDENCE_VERSION"


def _dimension(record):
    """The part of a dimension record that decides a quantity.  Prose and ordering are not part of it."""
    if not record:
        return {"STATUS": None, "VALUE": None, "SOURCE": None, "REFERENCE": None}
    return {"STATUS": record.get("STATUS"), "VALUE": record.get("VALUE"),
            "SOURCE": record.get("SOURCE"), "REFERENCE": record.get("REFERENCE")}


def opening_state(opening):
    """One opening's final, quantity-bearing state - the fields a later register must not contradict."""
    admission = opening.admission or {}
    width = _dimension(admission.get("WIDTH_EVIDENCE"))
    height = _dimension(admission.get("HEIGHT_EVIDENCE"))
    area = None
    if width["STATUS"] == EV.ESTABLISHED and height["STATUS"] == EV.ESTABLISHED:
        area = round(width["VALUE"] * height["VALUE"], 9)
    return {
        "OPENING_REF": opening.opening_ref,
        "FLOOR": opening.floor,
        "TYPE": opening.opening_type,
        "CLASSIFICATION": admission.get("CLASSIFICATION"),
        "WIDTH_EVIDENCE": width,
        "HEIGHT_EVIDENCE": height,
        "WIDTH_M": width["VALUE"] if width["STATUS"] == EV.ESTABLISHED else None,
        "HEIGHT_M": height["VALUE"] if height["STATUS"] == EV.ESTABLISHED else None,
        "AREA_M2": area,
        "AREA_IS": ("WIDTH_M x HEIGHT_M" if area is not None else
                    "null, because a required dimension is not established"),
        "HOST_ASSIGNMENT_STATUS": opening.host_status,
        "HOST_COMPONENT_REF": opening.host_component_ref,
        "HOST_THICKNESS_M": opening.host_thickness,
    }


def version_of(rows):
    """A version derived from the state itself, so it cannot be stamped on a register that does not match."""
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"), default=str)
    return "EV-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]


def freeze(openings):
    """Close the evidence stage.  Nothing that reads this may change what it describes."""
    rows = [opening_state(o) for o in sorted(openings, key=lambda x: x.opening_ref)]
    return {
        "EVIDENCE_VERSION": version_of(rows),
        "OPENINGS": rows,
        "OPENING_COUNT": len(rows),
        "WIDTH_ESTABLISHED": sum(1 for r in rows if r["WIDTH_M"] is not None),
        "HEIGHT_ESTABLISHED": sum(1 for r in rows if r["HEIGHT_M"] is not None),
        "AREA_AVAILABLE": sum(1 for r in rows if r["AREA_M2"] is not None),
        "RULE": "every register built after this point is derived from this state and records its version; a "
                "register that carries a different version is describing a different moment and its numbers "
                "may not be read beside these",
        "ORDER": ["ADMIT_ON_WHAT_THE_SOURCE_NAMES", "RESOLVE_HOSTS", "ASSEMBLE_THE_SPACES_ROOM_USE_NEEDS",
                  "RESOLVE_ROOM_AND_CATEGORY_EVIDENCE", "RESOLVE_EVERY_REMAINING_DIMENSION",
                  "FREEZE", "DERIVE_AREAS_DEDUCTIONS_DEPENDENCIES_QUESTIONS_AND_DOCUMENTS"],
    }


def stamp(register, final):
    """Record on a derived register which evidence state it was built from."""
    if register is None:
        return register
    register[VERSION_FIELD] = (final or {}).get("EVIDENCE_VERSION", UNVERSIONED)
    return register


def verify(final, openings):
    """Do the live objects still say what the frozen state says?  A drift here is a stale register upstream."""
    now = [opening_state(o) for o in sorted(openings, key=lambda x: x.opening_ref)]
    drifted = []
    before = {r["OPENING_REF"]: r for r in final.get("OPENINGS", [])}
    for r in now:
        was = before.get(r["OPENING_REF"])
        if was != r:
            drifted.append({"OPENING_REF": r["OPENING_REF"], "FROZEN": was, "NOW": r})
    missing = sorted(set(before) - {r["OPENING_REF"] for r in now})
    return {
        "EVIDENCE_VERSION": final.get("EVIDENCE_VERSION"),
        "VERSION_NOW": version_of(now),
        "UNCHANGED": not drifted and not missing,
        "DRIFTED": drifted,
        "MISSING_AFTER_THE_FREEZE": missing,
        "WHY": "evidence resolved after the freeze would leave every register built before it describing an "
               "earlier moment, which is the defect this barrier exists to make impossible",
    }
