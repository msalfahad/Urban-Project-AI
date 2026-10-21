"""QUANTITY RELEASE (M7) - one release state per quantity item, from named evidence; engineer decisions bound to the
source revision they were made on; rejected OCR readings that never come back on their own (generic, stdlib only).

    assess(item, *, sources, check=None, decisions=(), ocr_dependencies=(), ocr_ledger=None) -> release row
    register(items, *, sources, checks=None, decisions=(), ocr_dependencies=None, ocr_ledger=None)
                                        -> {"rows", "totals", "invalidated", "refused"}
    fingerprint(item)                   -> the hash a decision is bound to (what the quantity IS, not where it is shown)
    decision(item, verdict, reviewer, role, on, sources, note="")  -> a decision record bound to this revision
    OcrLedger                           rejected readings, keyed by (record, value); a re-admission needs its own
                                        decision naming the rejection

Evidence ladder (machine rungs, each needs the one before):
    DETECTED                 the item points at drawing entities (a source pointer)
    CLASSIFIED               it has a structural family (not UNKNOWN)
    GEOMETRICALLY_MEASURED   it has a base quantity from drawn geometry (support is not NO_GEOMETRY)
    SOURCE_SUPPORTED         every dimension is drawn or printed (support RELEASED / SOURCE_COMPLETE_UNREVIEWED)
    INDEPENDENTLY_CHECKED    a second method (another geometry library, another formula) agrees within tolerance
Release state (exactly one):
    EXCLUDED                 an engineer's valid EXCLUDE decision (scope)
    UNRESOLVED               the item has no defensible base (category UNRESOLVED), an independent check DIFFERS, an
                             engineer rejected it, or it depends on a rejected OCR reading
    ENGINEER_APPROVED        a valid APPROVE decision by an engineer on this revision of this item
    ENGINEER_REVIEWED        a valid REVIEW decision (looked at, not approved)
    PROVISIONAL              measured, but at least one dimension rests on a convention / assumption
    <highest machine rung>   otherwise (DETECTED .. INDEPENDENTLY_CHECKED)
A decision is valid only when it names a reviewer, the reviewer's role allows the verdict (APPROVE / EXCLUDE need
ENGINEER), its source sha256 equals the current file's and its item fingerprint equals the current item's;
otherwise it is INVALIDATED (SOURCE_REVISION_CHANGED / ITEM_CHANGED / NO_REVIEWER / ROLE_NOT_ALLOWED) and the item
falls back to its machine state - a changed drawing never keeps an old approval.

Totals keep their denominators and never collapse to one percentage:
    released            ENGINEER_APPROVED only (the only quantity a quotation may call released)
    machine_supported   SOURCE_SUPPORTED + INDEPENDENTLY_CHECKED, not yet reviewed
    provisional         PROVISIONAL + ENGINEER_REVIEWED + lower machine rungs that carry a base
    unresolved          count and exposure low / high (never added to a base total)
    excluded            count (and the base they carried, for the record)
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict

POLICY_ID = "QUANTITY_RELEASE_M7"
LADDER = ("DETECTED", "CLASSIFIED", "GEOMETRICALLY_MEASURED", "SOURCE_SUPPORTED", "INDEPENDENTLY_CHECKED")
STATES = LADDER + ("PROVISIONAL", "ENGINEER_REVIEWED", "ENGINEER_APPROVED", "UNRESOLVED", "EXCLUDED")
VERDICTS = ("APPROVE", "REVIEW", "REJECT", "EXCLUDE")
ROLE_ALLOWS = {"ENGINEER": set(VERDICTS), "ESTIMATOR": {"REVIEW", "REJECT"}, "QA": {"REVIEW", "REJECT"}}
SOURCE_SUPPORT = ("RELEASED", "SOURCE_COMPLETE_UNREVIEWED")
ASSUMED_SUPPORT = ("CONVENTION_ONLY", "ONE_ASSUMED_DIMENSION", "ASSUMPTION_DOMINATED", "FROZEN_STAGE_MODEL")
NO_GEOMETRY = "NO_GEOMETRY"
FINGERPRINT_FIELDS = ("item_id", "component_id", "trade", "family", "storey", "category", "unit", "low", "base",
                      "high", "dia_mm", "dimensions", "assumptions", "support", "blocker", "exposure_low",
                      "exposure_high", "part")


class ReleaseError(ValueError):
    pass


def _r(v):
    return round(float(v), 9) if isinstance(v, (int, float)) and not isinstance(v, bool) else v


def _canon(x):
    if isinstance(x, dict):
        return {str(k): _canon(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (list, tuple)):
        return [_canon(v) for v in x]
    return _r(x)


def fingerprint(item):
    """sha256 over the fields that define the quantity (rounded to 1e-9): a decision on this fingerprint is a
    decision on THIS quantity; any change of value, dimension, assumption or category makes it a different one."""
    body = {k: _canon(item.get(k)) for k in FINGERPRINT_FIELDS}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def source_file(item):
    """the drawing file an item was measured on: the first token of its source pointer."""
    s = (item.get("source") or "").strip()
    return s.split()[0] if s else None


def decision(item, verdict, reviewer, role, on, sources, note=""):
    """a decision record bound to the item's current fingerprint and to the current sha256 of its source file."""
    if verdict not in VERDICTS:
        raise ReleaseError(f"unknown verdict {verdict}")
    f = source_file(item)
    return {"decision_id": "DEC-" + hashlib.sha256(f"{item['item_id']}|{verdict}|{reviewer}|{on}".encode())
            .hexdigest()[:12], "item_id": item["item_id"], "verdict": verdict, "reviewer": reviewer, "role": role,
            "on": on, "source_file": f, "source_sha256": sources.get(f), "item_fingerprint": fingerprint(item),
            "note": note}


def validate_decision(d, item, sources):
    """-> (valid, reason). reason is None when valid."""
    if not d.get("reviewer"):
        return False, "NO_REVIEWER"
    if d.get("verdict") not in ROLE_ALLOWS.get(d.get("role"), set()):
        return False, "ROLE_NOT_ALLOWED"
    f = source_file(item)
    if not f or d.get("source_file") != f or not d.get("source_sha256") or d["source_sha256"] != sources.get(f):
        return False, "SOURCE_REVISION_CHANGED"
    if d.get("item_fingerprint") != fingerprint(item):
        return False, "ITEM_CHANGED"
    return True, None


class OcrLedger:
    """rejected OCR readings: (record_id, normalised value) -> the rejection decision. A rejection is never lifted by
    a new run, a new revision or a second machine reading; only a READMIT decision that names the rejection id and
    a reviewer lifts it (and is itself recorded)."""

    def __init__(self, entries=()):
        self.rejected, self.readmitted = {}, {}
        for e in entries:
            self.add(e)

    @staticmethod
    def key(record_id, value):
        return (str(record_id), " ".join(str(value or "").upper().split()))

    def add(self, e):
        k = self.key(e["record_id"], e["value"])
        if e["kind"] == "REJECT":
            self.rejected.setdefault(k, e)
        elif e["kind"] == "READMIT":
            rej = self.rejected.get(k)
            if not e.get("reviewer") or rej is None or e.get("rejection_id") != rej.get("rejection_id"):
                raise ReleaseError(f"a READMIT must name the rejection it lifts and a reviewer: {e}")
            self.readmitted[k] = e
        else:
            raise ReleaseError(f"unknown OCR ledger entry {e.get('kind')}")

    def is_rejected(self, record_id, value):
        k = self.key(record_id, value)
        return k in self.rejected and k not in self.readmitted

    def screen(self, readings):
        """readings [{record_id, value, ...}] -> (kept, dropped): a rejected reading never re-enters."""
        kept, dropped = [], []
        for r in readings:
            (dropped if self.is_rejected(r["record_id"], r["value"]) else kept).append(r)
        return kept, dropped


def machine_rung(item, check=None):
    """the highest ladder rung the item's own evidence reaches (None: not even detected)."""
    rung = None
    if not (item.get("source") or "").strip():
        return rung
    rung = "DETECTED"
    if not item.get("family") or item.get("family") == "UNKNOWN":
        return rung
    rung = "CLASSIFIED"
    if item.get("category") not in ("PROVISIONAL", "VERIFIED") or item.get("base") is None or \
            item.get("support") == NO_GEOMETRY:
        return rung
    rung = "GEOMETRICALLY_MEASURED"
    if item.get("support") not in SOURCE_SUPPORT:
        return rung
    rung = "SOURCE_SUPPORTED"
    if check and check.get("result") == "PASS":
        rung = "INDEPENDENTLY_CHECKED"
    return rung


def assess(item, *, sources, check=None, decisions=(), ocr_dependencies=(), ocr_ledger=None):
    """one release row. check: {result PASS / DIFFERS / NOT_COMPARABLE, method, engine, independent, tolerance}."""
    rung = machine_rung(item, check)
    valid, invalid = [], []
    for d in decisions:
        ok, why = validate_decision(d, item, sources)
        (valid if ok else invalid).append(d if ok else dict(d, invalid_reason=why))
    latest = sorted(valid, key=lambda d: (d.get("on") or "", d["decision_id"]))[-1] if valid else None
    rejected_ocr = [r for r in ocr_dependencies if ocr_ledger and ocr_ledger.is_rejected(r["record_id"], r["value"])]
    reasons = []
    measured = rung in LADDER[2:]
    if latest and latest["verdict"] == "EXCLUDE":
        state = "EXCLUDED"
        reasons.append("ENGINEER_EXCLUDED")
    elif item.get("category") == "UNRESOLVED" or not measured:
        state = "UNRESOLVED"
        reasons.append(item.get("blocker") or "NO_MEASURED_BASE")
    elif check and check.get("result") == "DIFFERS":
        state = "UNRESOLVED"
        reasons.append("INDEPENDENT_CHECK_DIFFERS")
    elif rejected_ocr:
        state = "UNRESOLVED"
        reasons.append("DEPENDS_ON_REJECTED_OCR")
    elif latest and latest["verdict"] == "REJECT":
        state = "UNRESOLVED"
        reasons.append("ENGINEER_REJECTED")
    elif latest and latest["verdict"] == "APPROVE":
        state = "ENGINEER_APPROVED"
    elif latest and latest["verdict"] == "REVIEW":
        state = "ENGINEER_REVIEWED"
    elif item.get("support") in ASSUMED_SUPPORT:
        state = "PROVISIONAL"
        reasons.append("ASSUMPTION:" + ",".join(a for a in (item.get("assumptions") or [item.get("support")])
                                                 if not str(a).startswith("FROZEN:")))
    else:
        state = rung
    nxt = _next_requirement(item, rung, check, state)
    return {"ITEM_ID": item["item_id"], "TRADE": item.get("trade"), "FAMILY": item.get("family"),
            "STOREY": item.get("storey"), "CATEGORY": item.get("category"), "UNIT": item.get("unit"),
            "BASE": item.get("base"), "LOW": item.get("low"), "HIGH": item.get("high"),
            "EXPOSURE_LOW": item.get("exposure_low"), "EXPOSURE_HIGH": item.get("exposure_high"),
            "SUPPORT": item.get("support"), "MACHINE_RUNG": rung, "STATE": state,
            "REASONS": ";".join(reasons), "CHECK": (check or {}).get("result", "NONE"),
            "CHECK_METHOD": (check or {}).get("method", ""), "DECISION": latest["decision_id"] if latest else "",
            "INVALIDATED_DECISIONS": ";".join(f"{d['decision_id']}:{d['invalid_reason']}" for d in invalid),
            "REJECTED_OCR": ";".join(r["record_id"] for r in rejected_ocr), "NEXT_REQUIREMENT": nxt,
            "FINGERPRINT": fingerprint(item)[:16], "SOURCE_FILE": source_file(item),
            "SOURCE_SHA256": (sources.get(source_file(item)) or "")[:16]}


def _next_requirement(item, rung, check, state):
    if state in ("ENGINEER_APPROVED", "EXCLUDED"):
        return ""
    if rung is None:
        return "a source pointer to drawing entities"
    if rung == "DETECTED":
        return "a structural family"
    if rung == "CLASSIFIED":
        return f"drawn geometry for a base quantity ({item.get('blocker') or 'no base'})"
    if rung == "GEOMETRICALLY_MEASURED":
        return "printed / drawn values for the assumed dimensions: " + ",".join(item.get("assumptions") or
                                                                                 [str(item.get("support"))])
    if check and check.get("result") == "DIFFERS":
        return "resolve the independent-check difference"
    if rung == "SOURCE_SUPPORTED":
        return "an independent check, then an engineer's approval"
    return "an engineer's approval on this revision"


def register(items, *, sources, checks=None, decisions=(), ocr_dependencies=None, ocr_ledger=None):
    """release rows for every item, totals with denominators, the invalidated decisions and the refused ones."""
    by_item = defaultdict(list)
    for d in decisions:
        by_item[d["item_id"]].append(d)
    known = {i["item_id"] for i in items}
    refused = [dict(d, invalid_reason="NO_SUCH_ITEM") for d in decisions if d["item_id"] not in known]
    rows = [assess(i, sources=sources, check=(checks or {}).get(i["item_id"]), decisions=by_item.get(i["item_id"], ()),
                   ocr_dependencies=(ocr_dependencies or {}).get(i["item_id"], ()), ocr_ledger=ocr_ledger)
            for i in items]
    invalid = [x for r in rows for x in r["INVALIDATED_DECISIONS"].split(";") if x]
    return {"policy": POLICY_ID, "rows": rows, "totals": totals(rows), "invalidated": invalid, "refused": refused}


def totals(rows):
    """per trade / unit: every bucket with its item count and base sum; the denominators travel with the numbers."""
    out = {}
    for tr in sorted({r["TRADE"] for r in rows}):
        R = [r for r in rows if r["TRADE"] == tr]

        def b(states):
            S = [r for r in R if r["STATE"] in states and r["BASE"] is not None]
            return {"n": len(S), "base": round(sum(r["BASE"] for r in S), 6),
                    "low": round(sum(r["LOW"] if r["LOW"] is not None else r["BASE"] for r in S), 6),
                    "high": round(sum(r["HIGH"] if r["HIGH"] is not None else r["BASE"] for r in S), 6)}
        U = [r for r in R if r["STATE"] == "UNRESOLVED"]
        measured = [r for r in R if r["BASE"] is not None and r["STATE"] != "EXCLUDED"]
        out[tr] = {"unit": R[0]["UNIT"] if R else None, "items": len(R),
                   "released": b(("ENGINEER_APPROVED",)),
                   "machine_supported": b(("SOURCE_SUPPORTED", "INDEPENDENTLY_CHECKED")),
                   "provisional": b(("PROVISIONAL", "ENGINEER_REVIEWED", "GEOMETRICALLY_MEASURED")),
                   "unresolved": {"n": len(U),
                                  "exposure_low": round(sum(r["EXPOSURE_LOW"] or 0.0 for r in U), 6),
                                  "exposure_high": round(sum(r["EXPOSURE_HIGH"] or 0.0 for r in U), 6),
                                  "n_without_exposure": sum(1 for r in U if r["EXPOSURE_HIGH"] is None)},
                   "excluded": b(("EXCLUDED",)),
                   "measured_items": len(measured),
                   "by_state": {s: sum(1 for r in R if r["STATE"] == s) for s in STATES}}
    return out


def policy_record():
    return {"policy": POLICY_ID, "ladder": list(LADDER), "states": list(STATES), "verdicts": list(VERDICTS),
            "role_allows": {k: sorted(v) for k, v in ROLE_ALLOWS.items()},
            "source_support": list(SOURCE_SUPPORT), "assumed_support": list(ASSUMED_SUPPORT),
            "fingerprint_fields": list(FINGERPRINT_FIELDS),
            "rules": ["only ENGINEER_APPROVED is released",
                      "a decision binds to the source sha256 and the item fingerprint; any change invalidates it",
                      "an independent check that differs makes the item UNRESOLVED, whatever its support",
                      "a rejected OCR reading is never re-admitted without a READMIT decision naming the rejection",
                      "UNRESOLVED carries exposure only; it never enters a base total",
                      "totals keep item counts beside every sum; no single percentage"]}
