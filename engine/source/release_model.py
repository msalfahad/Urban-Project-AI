"""RELEASE MODEL (V3b) - one BOQ line, two release views: TECHNICAL_QTO and COMMERCIAL_BOQ.

    release(technical_class, technical_qty, commercial=None) -> {"technical": {...}, "commercial": {...}}
    totals(records)                                          -> technical / commercial / budget / procurement sums

TECHNICAL classes (the measured truth): MEASURED, DERIVED, RASTER_DERIVED, SOURCE_RULE, CODE_METHOD, OWNER_PROJECT_FACT,
URBAN_STANDARD, PARTIAL (the measured part of an incomplete population) enter the technical total; REVIEW, BLOCKED,
BLOCKED_SOURCE_CONFLICT, NOT_IN_SOURCE, PENDING never do.
COMMERCIAL classes: every technical class that enters the technical total, plus the labelled provisional classes
(PROVISIONAL_SOURCE_DERIVED, PROVISIONAL_SOURCE_RANGE, PROVISIONAL_GEOMETRIC_INFERENCE, PROVISIONAL_CODE_METHOD,
PROVISIONAL_URBAN_FALLBACK, PROVISIONAL_OWNER_METHOD, OWNER_APPROVED_PROVISIONAL), BUDGET_ESTIMATE, PENDING, TRUE_BLOCKER.

Rules (each is a test):
  1. a provisional class can never be the technical class, and a technical qty is never set from a provisional value;
  2. every commercial provisional / budget record carries METHOD, ASSUMPTION, CONFIDENCE, LOW, HIGH (LOW <= QTY <= HIGH);
  3. COMMERCIAL_TOTAL = technical classes + provisional classes; BUDGET_ESTIMATE is shown beside it (COMMERCIAL_TOTAL
     INCL. BUDGET), never inside a measured subtotal;
  4. PROCUREMENT_ELIGIBLE = the technical classes in total, CODE_METHOD, OWNER_APPROVED_PROVISIONAL and provisional
     records of confidence H; BUDGET_ESTIMATE, PENDING, TRUE_BLOCKER and lower-confidence provisionals are not.
Stdlib only, project-agnostic.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "TWO_LAYER_RELEASE_V1"
TECH_IN_TOTAL = ("MEASURED", "DERIVED", "RASTER_DERIVED", "SOURCE_RULE", "CODE_METHOD", "OWNER_PROJECT_FACT",
                 "URBAN_STANDARD", "PARTIAL")
TECH_OUT = ("REVIEW", "BLOCKED", "BLOCKED_SOURCE_CONFLICT", "NOT_IN_SOURCE", "PENDING")
PROVISIONAL = ("PROVISIONAL_SOURCE_DERIVED", "PROVISIONAL_SOURCE_RANGE", "PROVISIONAL_GEOMETRIC_INFERENCE",
               "PROVISIONAL_CODE_METHOD", "PROVISIONAL_URBAN_FALLBACK", "PROVISIONAL_OWNER_METHOD",
               "OWNER_APPROVED_PROVISIONAL")
BUDGET = "BUDGET_ESTIMATE"
COMM_OUT = ("PENDING", "TRUE_BLOCKER", "NOT_IN_SCOPE")
ALWAYS_ELIGIBLE = TECH_IN_TOTAL + ("OWNER_APPROVED_PROVISIONAL",)
REQUIRED = ("method", "assumption", "confidence", "low", "high")


class ReleaseError(ValueError):
    pass


def release(technical_class, technical_qty, commercial=None) -> dict:
    """commercial: None (= the technical view) or {"class", "qty", "method", "assumption", "confidence", "low", "high",
    "source"}."""
    if technical_class in PROVISIONAL or technical_class == BUDGET:
        raise ReleaseError(f"{technical_class} is not a technical class")
    if technical_class not in TECH_IN_TOTAL + TECH_OUT:
        raise ReleaseError(f"unknown technical class {technical_class}")
    tq = technical_qty if technical_class in TECH_IN_TOTAL else None
    tech = {"class": technical_class, "qty": tq, "in_total": technical_class in TECH_IN_TOTAL and tq is not None}
    if commercial is None:
        c = {"class": technical_class if tech["in_total"] else ("PENDING" if technical_class != "NOT_IN_SOURCE"
                                                                else "NOT_IN_SCOPE"),
             "qty": tq if tech["in_total"] else None, "method": "AS TECHNICAL", "assumption": None,
             "confidence": "H" if tech["in_total"] else None, "low": tq if tech["in_total"] else None,
             "high": tq if tech["in_total"] else None, "source": None}
    else:
        c = dict(commercial)
        cls = c.get("class")
        if cls not in TECH_IN_TOTAL + PROVISIONAL + (BUDGET,) + COMM_OUT:
            raise ReleaseError(f"unknown commercial class {cls}")
        if cls in PROVISIONAL + (BUDGET,):
            miss = [k for k in REQUIRED if c.get(k) is None]
            if miss:
                raise ReleaseError(f"{cls} record without {miss}")
            if c.get("qty") is None or not (c["low"] - 1e-9 <= c["qty"] <= c["high"] + 1e-9):
                raise ReleaseError(f"{cls}: qty {c.get('qty')} outside its range [{c['low']}, {c['high']}]")
        if cls in TECH_IN_TOTAL and cls != technical_class:
            raise ReleaseError("a commercial technical class must equal the technical class")
        for k in ("method", "assumption", "confidence", "low", "high", "source"):
            c.setdefault(k, None)
    c["in_commercial_total"] = c["class"] in TECH_IN_TOTAL + PROVISIONAL and c.get("qty") is not None
    c["budget"] = c["class"] == BUDGET
    c["procurement_eligible"] = c.get("qty") is not None and (
        c["class"] in ALWAYS_ELIGIBLE or (c["class"] in PROVISIONAL and c.get("confidence") == "H"))
    c["provisional"] = c["class"] in PROVISIONAL or c["budget"]
    return {"technical": tech, "commercial": c}


def totals(records) -> dict:
    """records [release dicts] of ONE unit."""
    t = sum(r["technical"]["qty"] for r in records if r["technical"]["in_total"])
    c = sum(r["commercial"]["qty"] for r in records if r["commercial"]["in_commercial_total"])
    p = sum(r["commercial"]["qty"] for r in records if r["commercial"]["in_commercial_total"]
            and r["commercial"]["provisional"])
    b = sum(r["commercial"]["qty"] for r in records if r["commercial"]["budget"])
    e = sum(r["commercial"]["qty"] for r in records if r["commercial"]["procurement_eligible"])
    lo = sum(r["commercial"]["low"] for r in records if r["commercial"]["in_commercial_total"] or r["commercial"]["budget"])
    hi = sum(r["commercial"]["high"] for r in records if r["commercial"]["in_commercial_total"] or r["commercial"]["budget"])
    return {"technical_total": t, "commercial_total": c, "commercial_provisional_part": p, "budget_allowance": b,
            "commercial_total_incl_budget": c + b, "procurement_eligible": e, "low": lo, "high": hi,
            "pending": sum(1 for r in records if r["commercial"]["class"] in COMM_OUT)}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "tech_in_total": list(TECH_IN_TOTAL), "tech_out": list(TECH_OUT),
           "provisional": list(PROVISIONAL), "budget": BUDGET, "required_provisional_fields": list(REQUIRED),
           "procurement": "technical-in-total, OWNER_APPROVED_PROVISIONAL, provisional of confidence H",
           "never": ["a provisional value in the technical column", "BUDGET_ESTIMATE inside a measured subtotal",
                     "an unlabelled provisional", "a provisional without its range"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
