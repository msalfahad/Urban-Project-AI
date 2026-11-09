"""R-T647-1: a HELD line always carries ONE recorded cause with a committed source (every villa; T-647, research only).

A cause record is accepted only when
  (a) its class is one of CAUSE_CLASSES and its reference has the form that class names (an owner decision Q-nn, a
      designer item D-nn / C-ST-n / RFI-..., a Checker downgrade DG-<hex>, a printed-value gap naming a sheet, a
      dependency on another HELD line by id, or a drawing-confirmed fix row with its own hand calculation);
  (b) it cites at least one committed source file AND the text it was read on (a cause with no source is invented:
      refused);
  (c) a DEPENDENCY names a host line that is itself HELD in the same census (a released host is not a cause);
  (d) the line stays HELD: it carries no measured quantity, and HELD lines are never summed (held_total refuses).
Nothing here computes or changes a quantity; a FIX_ROW is a proposal beside the HELD line, never wired.
"""
from __future__ import annotations

import re

CAUSE_CLASSES = {
    "OWNER_DECISION": re.compile(r"^Q-\d+( [A-Z])?$"),
    "DESIGNER_ITEM": re.compile(r"^(D-\d+|C-ST-\d+|RFI-[A-Z0-9-]+( \([a-z]\))?)$"),
    "CHECKER_DOWNGRADE": re.compile(r"^DG-[0-9a-f]{8,}$"),
    "PRINTED_VALUE_GAP": re.compile(r"^(ST|AR|SAN) p\.\d+.*|^(arch|structural) sheet .+"),
    "DEPENDENCY": re.compile(r"^L-[0-9a-f]{20}$"),
    "FIX_ROW": re.compile(r"^FR-T\d+-\d+$"),
}


class CauseError(ValueError):
    """a cause record that R-T647-1 refuses."""


def check(rec: dict, held_ids: set | None = None) -> dict:
    """validate one cause record (R-T647-1 (a) - (d)); returns it unchanged."""
    lid = rec.get("line_id")
    if not lid:
        raise CauseError("a cause record names no line id")
    cls, ref = rec.get("cause_class"), rec.get("ref")
    if cls not in CAUSE_CLASSES:
        raise CauseError(f"{lid}: cause class {cls!r} is not one of {sorted(CAUSE_CLASSES)}")
    if not isinstance(ref, str) or not CAUSE_CLASSES[cls].match(ref):
        raise CauseError(f"{lid}: reference {ref!r} is not a {cls} reference")
    src = rec.get("sources") or []
    if not src or not all(isinstance(s, dict) and s.get("file") and s.get("read_on") for s in src):
        raise CauseError(f"{lid}: no committed source with the text it was read on: an invented cause is refused")
    if not str(rec.get("cause") or "").strip():
        raise CauseError(f"{lid}: empty cause text")
    if rec.get("measured_net") not in (None, ""):
        raise CauseError(f"{lid}: a HELD line carries a measured quantity {rec['measured_net']!r} (HELD is blank)")
    if cls == "DEPENDENCY":
        if ref == lid:
            raise CauseError(f"{lid}: a line cannot depend on itself")
        if held_ids is not None and ref not in held_ids:
            raise CauseError(f"{lid}: host {ref} is not HELD: a released host is not a cause")
    if cls == "FIX_ROW":
        fr = rec.get("fix_row") or {}
        if not fr.get("hand_calculation") or not fr.get("proposed_state"):
            raise CauseError(f"{lid}: a fix row without its own hand calculation and proposed state")
        if fr.get("wired"):
            raise CauseError(f"{lid}: a fix row is a proposal, never wired here")
    return rec


def held_total(lines):
    """HELD is never summed (and never 0): any HELD line in the set refuses a total."""
    held = [l["line_id"] for l in lines if l.get("class") == "HELD"]
    if held:
        raise CauseError(f"a total over {len(held)} HELD line(s) is refused (HELD is never summed, never 0)")
    return sum(l["measured_net"] for l in lines)
