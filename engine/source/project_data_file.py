"""PROJECT DATA FILE V1 (task T-064; not wired into any released method; no quantity changed) - the controlled file
through which a value a person TYPED in from a drawing may feed a quantity (owner answer Q-17 = A, 2026-10-19).

Owner Q-17 A: "A value typed in from a drawing goes into a controlled project data file with: drawing filename, number
and revision, sheet or page, exact note, dimension or detail reference, units, value, applicable floors or members,
verification status and reviewer or source. Status words: DRAWING-VERIFIED, OWNER-CONFIRMED, DESIGNER-CONFIRMED,
INFERRED (from verified values with documented logic), ASSUMED, HELD. The engine must not claim it extracted a value
automatically when it was typed in, and manually supplied answers must not inflate automated-extraction accuracy."

One file = one project (schema URBAN_PROJECT_DATA_FILE_V1):

    {"schema": "URBAN_PROJECT_DATA_FILE_V1", "project": "<project id>", "records": [<record>, ...]}

Record (every field required unless marked optional):

    key                 unique name of the value (e.g. STOREY_HEIGHT_GF)
    project             must equal the file's project (a record never moves to another project)
    kind                number | choice | table
    unit                number: m | cm | mm | fraction | count; choice / table: none
    value               number (finite, not bool) for kind number, a string for choice, a list / dict for table;
                        may be null only for HELD (a HELD value is never used, even when it is shown)
    status              DRAWING-VERIFIED | OWNER-CONFIRMED | DESIGNER-CONFIRMED | INFERRED | ASSUMED | HELD
    drawing_file        drawing file name the value is typed from (or applies to)
    drawing_number      drawing number
    revision            revision as printed; when the sheet prints none, say so in words (never left empty)
    sheet               sheet or page
    reference           the exact printed note / dimension text / detail title the value is read from
    applies_to          {"floors": [...], "members": [...]}: at least one non-empty list; "ALL" is an explicit entry
    reviewer_or_source  who read / confirmed it, or the owner / designer answer it rests on: a record without a
                        source is refused
    entered_by          must be "TYPED" (this file never holds automatic extraction)
    logic               INFERRED only (required): the documented derivation
    inferred_from       INFERRED only (required): keys of this file the value derives from; each must exist and be
                        DRAWING-VERIFIED, OWNER-CONFIRMED or DESIGNER-CONFIRMED
    hold_reason         HELD only (required): why it is held (owner question, conflict, not printed)
    conditions          optional: printed conditions of use (e.g. "without concentrated load")
    alternatives        optional: other printed / candidate values, shown, never used
    notes               optional

Use:

    load(doc) / load_path(path)  -> ProjectDataFile (ProjectDataFileError lists every fault; nothing half-loaded)
    validate(doc)                -> [fault, ...] (empty = valid)
    pdf.value(key, floor=, member=)
                                 -> {"key", "status", "usable", "value", "value_m", "unit", "source", "basis": TYPED}
    pdf.dependency(keys, floor=, member=)
                                 -> {"state": RELEASABLE | HELD, "held_by": [...], "basis": TYPED, "inputs": [...]}
    pdf.quantity(keys, compute, floor=, member=)
                                 -> {"state", "quantity": number or None, "held_by", "basis", "inputs"}: compute(values)
                                    is called only when every input is usable; otherwise the quantity is None (HELD),
                                    never 0 (UP-QTY-STATUS-001)
    is_typed(line) / automatic_only(lines)
                                 -> keep TYPED-basis lines out of an automated-extraction accuracy count

Usable statuses: DRAWING-VERIFIED, OWNER-CONFIRMED, DESIGNER-CONFIRMED and INFERRED (validated as above). ASSUMED and
HELD values make every dependent quantity HELD. A key missing from the file, or a record whose applies_to does not
cover the asked floor / member, also holds the quantity (missing never becomes 0). Every result carries basis TYPED:
a quantity resting on this file is never reported as automatic extraction.

Separate from project_rules.py (URBAN_PROJECT_RULES_V1: project overrides of Urban rule values) and project_claims.py
(answers that adjudicate engine flags): this file holds typed drawing VALUES with their verification status.
Project-agnostic; stdlib only."""

from __future__ import annotations

import copy
import json
import math

SCHEMA = "URBAN_PROJECT_DATA_FILE_V1"
POLICY_ID = "PROJECT_DATA_FILE_V1"

DRAWING_VERIFIED = "DRAWING-VERIFIED"
OWNER_CONFIRMED = "OWNER-CONFIRMED"
DESIGNER_CONFIRMED = "DESIGNER-CONFIRMED"
INFERRED = "INFERRED"
ASSUMED = "ASSUMED"
HELD = "HELD"
STATUSES = (DRAWING_VERIFIED, OWNER_CONFIRMED, DESIGNER_CONFIRMED, INFERRED, ASSUMED, HELD)
VERIFIED = (DRAWING_VERIFIED, OWNER_CONFIRMED, DESIGNER_CONFIRMED)   # may be cited by an INFERRED record
USABLE = VERIFIED + (INFERRED,)                                       # may feed a quantity

TYPED = "TYPED"
BASIS = "TYPED_PROJECT_DATA"          # tag on every result: never automatic extraction
RELEASABLE = "RELEASABLE"

KINDS = ("number", "choice", "table")
NUMBER_UNITS = {"m": 1.0, "cm": 0.01, "mm": 0.001, "fraction": None, "count": None}
LENGTH_UNITS = ("m", "cm", "mm")

REQUIRED = ("key", "project", "kind", "unit", "value", "status", "drawing_file", "drawing_number", "revision", "sheet",
            "reference", "applies_to", "reviewer_or_source", "entered_by")
OPTIONAL = ("logic", "inferred_from", "hold_reason", "conditions", "alternatives", "notes")
TEXT_FIELDS = ("key", "project", "drawing_file", "drawing_number", "revision", "sheet", "reference",
               "reviewer_or_source")
ALL = "ALL"


class ProjectDataFileError(ValueError):
    """The file is refused; .faults lists every fault found."""

    def __init__(self, faults):
        self.faults = list(faults)
        super().__init__("project data file refused: " + "; ".join(self.faults))


def _text(v):
    return isinstance(v, str) and v.strip() != ""


def _number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _record_faults(r, i, project):
    f = []
    tag = "record %d" % i
    if not isinstance(r, dict):
        return [tag + ": not an object"]
    if _text(r.get("key")):
        tag = "record %d (%s)" % (i, r["key"])
    for k in REQUIRED:
        if k not in r:
            f.append("%s: field %s missing" % (tag, k))
    for k in r:
        if k not in REQUIRED and k not in OPTIONAL:
            f.append("%s: unknown field %s" % (tag, k))
    for k in TEXT_FIELDS:
        if k in r and not _text(r[k]):
            f.append("%s: %s empty%s" % (tag, k, " (a record without a source is refused)"
                                          if k == "reviewer_or_source" else ""))
    if "project" in r and _text(r.get("project")) and r["project"] != project:
        f.append("%s: project %r is not the file's project %r" % (tag, r["project"], project))
    if "entered_by" in r and r["entered_by"] != TYPED:
        f.append("%s: entered_by must be %s (this file never holds automatic extraction)" % (tag, TYPED))
    st = r.get("status")
    if "status" in r and st not in STATUSES:
        f.append("%s: status %r is not one of %s" % (tag, st, ", ".join(STATUSES)))
    kind, unit, val = r.get("kind"), r.get("unit"), r.get("value")
    if "kind" in r and kind not in KINDS:
        f.append("%s: kind %r is not one of %s" % (tag, kind, ", ".join(KINDS)))
    if kind == "number":
        if unit not in NUMBER_UNITS:
            f.append("%s: unit %r is not one of %s" % (tag, unit, ", ".join(NUMBER_UNITS)))
        if val is not None and not _number(val):
            f.append("%s: value %r is not a finite number" % (tag, val))
        if unit == "count" and _number(val) and (val < 0 or val != int(val)):
            f.append("%s: a count must be a whole number >= 0" % tag)
    elif kind in ("choice", "table"):
        if "unit" in r and unit != "none":
            f.append("%s: unit of a %s must be 'none'" % (tag, kind))
        if val is not None and kind == "choice" and not _text(val):
            f.append("%s: a choice value must be a non-empty string" % tag)
        if val is not None and kind == "table" and not (isinstance(val, (list, dict)) and val):
            f.append("%s: a table value must be a non-empty list or object" % tag)
    if "value" in r and val is None and st != HELD:
        f.append("%s: value missing; only a HELD record may have no value" % tag)
    at = r.get("applies_to")
    if "applies_to" in r:
        if not isinstance(at, dict) or set(at) - {"floors", "members"}:
            f.append("%s: applies_to must be {'floors': [...], 'members': [...]}" % tag)
        else:
            lists = [at.get(k) for k in ("floors", "members") if k in at]
            if any(not isinstance(x, list) or not all(_text(y) for y in x) for x in lists):
                f.append("%s: applies_to lists must hold non-empty strings" % tag)
            elif not any(lists):
                f.append("%s: applies_to names no floor and no member" % tag)
    if st == INFERRED:
        if not _text(r.get("logic")):
            f.append("%s: INFERRED without documented logic is refused" % tag)
        src = r.get("inferred_from")
        if not isinstance(src, list) or not src or not all(_text(x) for x in src):
            f.append("%s: INFERRED must cite the verified keys it derives from (inferred_from)" % tag)
    elif "inferred_from" in r:
        f.append("%s: inferred_from is for INFERRED records only" % tag)
    if st == HELD and not _text(r.get("hold_reason")):
        f.append("%s: HELD without hold_reason" % tag)
    if "hold_reason" in r and st != HELD:
        f.append("%s: hold_reason on a %s record" % (tag, st))
    if "alternatives" in r and not isinstance(r["alternatives"], list):
        f.append("%s: alternatives must be a list" % tag)
    if "conditions" in r and not (isinstance(r["conditions"], list) and all(_text(x) for x in r["conditions"])):
        f.append("%s: conditions must be a list of texts" % tag)
    return f


def validate(doc):
    """Every fault of the file (empty list = valid)."""
    if not isinstance(doc, dict):
        return ["the file is not an object"]
    f = []
    if doc.get("schema") != SCHEMA:
        f.append("schema must be %s" % SCHEMA)
    project = doc.get("project")
    if not _text(project):
        f.append("project missing")
    for k in doc:
        if k not in ("schema", "project", "records", "notes"):
            f.append("unknown top-level field %s" % k)
    recs = doc.get("records")
    if not isinstance(recs, list) or not recs:
        return f + ["records must be a non-empty list"]
    seen = {}
    for i, r in enumerate(recs):
        f.extend(_record_faults(r, i, project))
        if isinstance(r, dict) and _text(r.get("key")):
            if r["key"] in seen:
                f.append("record %d (%s): duplicate key (also record %d)" % (i, r["key"], seen[r["key"]]))
            else:
                seen[r["key"]] = i
    by_key = {r["key"]: r for r in recs if isinstance(r, dict) and _text(r.get("key"))}
    for i, r in enumerate(recs):
        if not isinstance(r, dict) or r.get("status") != INFERRED or not isinstance(r.get("inferred_from"), list):
            continue
        for src in r["inferred_from"]:
            s = by_key.get(src)
            if src == r.get("key"):
                f.append("record %d (%s): INFERRED from itself" % (i, r["key"]))
            elif s is None:
                f.append("record %d (%s): INFERRED from %r, which is not in the file" % (i, r["key"], src))
            elif s.get("status") not in VERIFIED:
                f.append("record %d (%s): INFERRED from %s, whose status %s is not a verified input (%s)"
                         % (i, r["key"], src, s.get("status"), ", ".join(VERIFIED)))
    return f


def _covers(lst, item):
    return ALL in lst or (item is not None and item in lst)


class ProjectDataFile:
    def __init__(self, doc):
        self.doc = copy.deepcopy(doc)
        self.project = doc["project"]
        self.records = {r["key"]: r for r in self.doc["records"]}

    def keys(self):
        return list(self.records)

    def _applies(self, r, floor, member):
        # a scoped record (a list without ALL) applies only to a caller naming a floor / member in that list: an
        # unscoped call never picks up a value typed for one floor or one member
        at = r["applies_to"]
        for dim, item in (("floors", floor), ("members", member)):
            lst = at.get(dim)
            if lst and not _covers(lst, item):
                return False
        return True

    def value(self, key, floor=None, member=None):
        r = self.records.get(key)
        if r is None:
            return {"key": key, "status": "MISSING", "usable": False, "value": None, "value_m": None, "unit": None,
                    "source": None, "basis": BASIS, "reason": "not in the project data file"}
        out = {"key": key, "status": r["status"], "unit": r["unit"], "value": None, "value_m": None,
               "source": {k: r[k] for k in ("drawing_file", "drawing_number", "revision", "sheet", "reference",
                                            "reviewer_or_source")},
               "entered_by": TYPED, "basis": BASIS}
        if not self._applies(r, floor, member):
            out.update(usable=False, reason="applies_to does not cover floor %r / member %r" % (floor, member))
            return out
        usable = r["status"] in USABLE
        out["usable"] = usable
        if not usable:
            out["reason"] = r.get("hold_reason") if r["status"] == HELD else "ASSUMED value: never feeds a quantity"
            out["shown_value"] = r["value"]
            return out
        out["value"] = copy.deepcopy(r["value"])
        if r["kind"] == "number" and r["unit"] in LENGTH_UNITS:
            out["value_m"] = round(r["value"] * NUMBER_UNITS[r["unit"]], 9)
        if r.get("conditions"):
            out["conditions"] = list(r["conditions"])
        return out

    def dependency(self, keys, floor=None, member=None):
        inputs = [self.value(k, floor=floor, member=member) for k in keys]
        held = [{"key": v["key"], "status": v["status"], "reason": v.get("reason")} for v in inputs if not v["usable"]]
        state = HELD if held or not inputs else RELEASABLE
        if not inputs:
            held = [{"key": None, "status": "MISSING", "reason": "no input named"}]
        return {"state": state, "held_by": held, "basis": BASIS, "inputs": inputs}

    def quantity(self, keys, compute, floor=None, member=None):
        dep = self.dependency(keys, floor=floor, member=member)
        out = {"state": dep["state"], "quantity": None, "held_by": dep["held_by"], "basis": BASIS,
               "inputs": dep["inputs"]}
        if dep["state"] == RELEASABLE:
            vals = {v["key"]: (v["value_m"] if v["value_m"] is not None else v["value"]) for v in dep["inputs"]}
            q = compute(vals)
            if q is None or not _number(q):
                out.update(state=HELD, quantity=None,
                           held_by=[{"key": None, "status": "NO_RESULT", "reason": "compute gave no number"}])
            else:
                out["quantity"] = q
        return out

    def summary(self):
        counts = {s: 0 for s in STATUSES}
        for r in self.records.values():
            counts[r["status"]] += 1
        return {"project": self.project, "records": len(self.records), "by_status": counts,
                "usable": sorted(k for k, r in self.records.items() if r["status"] in USABLE),
                "not_usable": sorted(k for k, r in self.records.items() if r["status"] not in USABLE),
                "basis": BASIS}


def load(doc):
    faults = validate(doc)
    if faults:
        raise ProjectDataFileError(faults)
    return ProjectDataFile(doc)


def load_path(path):
    with open(path, encoding="utf-8") as fh:
        return load(json.load(fh))


def is_typed(line):
    """True when a BOQ line (dict) rests on a typed project-data value (its basis or any input basis is TYPED)."""
    if not isinstance(line, dict):
        return False
    if line.get("basis") == BASIS:
        return True
    return any(isinstance(v, dict) and v.get("basis") == BASIS for v in line.get("inputs") or ())


def automatic_only(lines):
    """The lines that rest on no typed value: the only ones an automated-extraction accuracy figure may count."""
    return [ln for ln in lines if not is_typed(ln)]


def policy_record():
    return {"policy_id": POLICY_ID, "schema": SCHEMA, "statuses": list(STATUSES), "usable": list(USABLE),
            "holds_dependents": [ASSUMED, HELD], "entered_by": TYPED, "basis": BASIS,
            "owner_answers": ["Q-17 A (2026-10-19)"], "rules": ["UP-QTY-STATUS-001", "UP-HGT-001"]}
