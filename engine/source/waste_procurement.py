"""WASTE / PROCUREMENT (V3b) - net quantity stays the BOQ; waste and procurement are a separate, rule-driven layer.

    resolve(item_code, trade, material, rules)  -> the governing waste rule (hierarchy) or PENDING
    apply(net_qty, unit, rule)                  -> {NET, WASTE_METHOD, WASTE_PCT, WASTE_QTY, PROCUREMENT, STATE}

Hierarchy: ITEM override > TRADE / MATERIAL rule > PROJECT rule > PENDING. No universal percentage exists: when no
approved rule applies the record is PENDING with WASTE_PCT / WASTE_QTY / PROCUREMENT blank (None), never 0.
A rule is {"scope": "ITEM" | "TRADE_MATERIAL" | "PROJECT", "key", "method", "pct" | None, "approved_by", "source"};
an unapproved rule (approved_by None) is ignored. A COMPUTED rule (e.g. rebar cutting optimisation) passes its own
waste quantity: {"method": "CUTTING_OPTIMISATION", "waste_qty", "procurement"}.
Stdlib only, project-agnostic.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "WASTE_PROCUREMENT_V1"
ORDER = ("ITEM", "TRADE_MATERIAL", "PROJECT")


def resolve(item_code, trade, material, rules) -> dict | None:
    keys = {"ITEM": (item_code,), "TRADE_MATERIAL": (f"{trade}|{material}", trade) if material else (trade,),
            "PROJECT": ("*",)}
    for scope in ORDER:
        for k in keys[scope]:                       # the more specific key first
            for r in rules:
                if r.get("scope") == scope and r.get("approved_by") and r.get("key") == k:
                    return r
    return None


def apply(net_qty, unit, rule) -> dict:
    out = {"NET": net_qty, "UNIT": unit, "WASTE_METHOD": None, "WASTE_PCT": None, "WASTE_QTY": None,
           "PROCUREMENT": None, "RULE_SCOPE": None, "SOURCE": None, "STATE": "PENDING"}
    if net_qty is None:
        out["STATE"] = "NO_NET_QUANTITY"
        return out
    if rule is None:
        out["WASTE_METHOD"] = "PENDING (no approved waste rule)"
        return out
    out.update(WASTE_METHOD=rule["method"], RULE_SCOPE=rule.get("scope"), SOURCE=rule.get("source"))
    if rule.get("method") == "CUTTING_OPTIMISATION":
        w = rule["waste_qty"]
        out.update(WASTE_QTY=w, PROCUREMENT=rule["procurement"],
                   WASTE_PCT=(100.0 * w / rule["procurement"]) if rule["procurement"] else 0.0, STATE="COMPUTED")
        return out
    pct = rule.get("pct")
    if pct is None:
        out["STATE"] = "PENDING"
        return out
    w = net_qty * pct / 100.0
    out.update(WASTE_PCT=pct, WASTE_QTY=w, PROCUREMENT=net_qty + w, STATE="APPLIED")
    return out


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "hierarchy": list(ORDER) + ["PENDING"],
           "rule": "net quantity is the BOQ; waste = approved rule only; unapproved = PENDING with blank fields",
           "never": ["a universal waste %", "0 % in place of PENDING", "waste mixed into the net quantity"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
