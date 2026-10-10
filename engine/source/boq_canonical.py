"""CANONICAL BOQ ITEM MODEL (RC1) - one payable identity per physical measurement item.

A canonical item carries its quantity (copied from one engine register row), its room / detail breakdown, and the
LEGACY row ids that once described the same measurement. Legacy ids are NEVER additive: they live in the item, not
beside it. Relations a legacy id may have to its canonical item:
  SAME_QUANTITY          the legacy row measured exactly this quantity (value must equal the item quantity)
  COMPONENT              the legacy row measured a part of it (value must equal the sum of the breakdown keys it names)
  MISLABELLED_DUPLICATE  a report row that presented this quantity under another trade label (value must equal the
                         breakdown keys it names); kept for provenance only
  HISTORICAL_MEANING     an older-revision row with the same meaning (value not comparable - another source)
A MEASURE PAIR is two items that measure the SAME physical thing in two units (e.g. a threshold by m2 and by lm):
both stay in the summary, each names the other, and the model states 'price one basis'.

validate() refuses: duplicate canonical ids; a legacy id in two items or also used as a canonical id; two ADDITIVE
items with the same physical layer, unit and overlapping breakdown keys (a double count) unless they are a declared
measure pair; a breakdown that does not sum to its quantity (within tol) unless declared non-additive; an alias value
that disagrees with what it claims; a quantity on a BLOCKED item; an approved item without RELEASED.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "CANONICAL_BOQ_ITEM_MODEL_V1"
SAME, COMPONENT, MISLABELLED, HISTORICAL = "SAME_QUANTITY", "COMPONENT", "MISLABELLED_DUPLICATE", "HISTORICAL_MEANING"
RELATIONS = (SAME, COMPONENT, MISLABELLED, HISTORICAL)
RELEASED, COMPLETE, SUBTOTAL, BLOCKED = "RELEASED", "COMPUTED_SHADOW_COMPLETE", "AUTHORISED_SUBTOTAL", "BLOCKED"
STATUSES = (COMPLETE, SUBTOTAL, BLOCKED, RELEASED)
FIELDS = ("canonical_item_id", "legacy_row_ids", "trade", "description_ar", "description_en", "qty", "unit", "status",
          "room_breakdown", "source", "rules")


def _digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def item(canonical_item_id, *, trade, layer, unit, qty, status, description_ar, description_en, breakdown,
         breakdown_additive=True, legacy=(), measure_pair=None, source=None, rules=(), blockers=(), evidence=None,
         notes=()):
    """breakdown: [{"key", "label", "qty", "kind"}] (kind ROOM / STRIP / OPENING / DETAIL / OUTSIDE_ROOM);
    legacy: [{"id", "relation", "value", "keys", "note"}]."""
    return {"canonical_item_id": canonical_item_id, "trade": trade, "layer": layer, "unit": unit, "qty": qty,
            "status": status, "description_ar": description_ar, "description_en": description_en,
            "room_breakdown": list(breakdown), "breakdown_additive": bool(breakdown_additive),
            "legacy_row_ids": [dict(x) for x in legacy], "measure_pair": measure_pair, "source": source,
            "rules": list(rules), "blockers": list(blockers), "evidence": evidence, "notes": list(notes),
            "approved_for_boq": status == RELEASED, "additive_in_summary": True}


def build(items: list, *, run: dict) -> dict:
    m = {"policy": POLICY_ID, "run": run, "items": items, "pricing": None, "calculates": False,
         "summary_rule": "ONE additive summary line per canonical item; legacy ids are attributes, never lines; a "
                         "measure pair is two lines of ONE physical item - price one basis"}
    m["digest"] = _digest({k: v for k, v in m.items() if k != "digest"})
    return m


def _close(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


def validate(model: dict, *, tol: float = 1e-6) -> dict:
    items = model["items"]
    ids = [i["canonical_item_id"] for i in items]
    by_id = {i["canonical_item_id"]: i for i in items}
    errors = []
    for x in sorted({x for x in ids if ids.count(x) > 1}):
        errors.append({"error": "DUPLICATE_CANONICAL_ID", "id": x})
    seen = {}
    for i in items:
        for a in i["legacy_row_ids"]:
            if a["relation"] not in RELATIONS:
                errors.append({"error": "UNKNOWN_ALIAS_RELATION", "item": i["canonical_item_id"], "alias": a["id"]})
            if a["id"] in by_id:
                errors.append({"error": "ALIAS_IS_ALSO_CANONICAL", "alias": a["id"]})
            if a["id"] in seen and a["relation"] != HISTORICAL:
                errors.append({"error": "ALIAS_IN_TWO_ITEMS", "alias": a["id"], "items": [seen[a["id"]],
                                                                                         i["canonical_item_id"]]})
            seen.setdefault(a["id"], i["canonical_item_id"])
            bd = {b["key"]: b["qty"] for b in i["room_breakdown"]}
            if a["relation"] == SAME and not _close(a.get("value"), i["qty"], tol):
                errors.append({"error": "ALIAS_VALUE_DIFFERS", "item": i["canonical_item_id"], "alias": a["id"],
                               "alias_value": a.get("value"), "qty": i["qty"]})
            if a["relation"] in (COMPONENT, MISLABELLED):
                keys = a.get("keys") or []
                part = sum(bd.get(k) or 0.0 for k in keys) if keys and all(k in bd for k in keys) else None
                if not _close(a.get("value"), part, tol):
                    errors.append({"error": "ALIAS_COMPONENT_DIFFERS", "item": i["canonical_item_id"],
                                   "alias": a["id"], "alias_value": a.get("value"), "breakdown_part": part})
    for i in items:
        if i["status"] not in STATUSES:
            errors.append({"error": "UNKNOWN_STATUS", "item": i["canonical_item_id"]})
        if i["status"] == BLOCKED and i["qty"] is not None:
            errors.append({"error": "QTY_ON_BLOCKED", "item": i["canonical_item_id"]})
        if i["approved_for_boq"] and i["status"] != RELEASED:
            errors.append({"error": "APPROVED_WITHOUT_RELEASE", "item": i["canonical_item_id"]})
        if i["breakdown_additive"] and i["qty"] is not None and i["room_breakdown"]:
            s = sum(b["qty"] for b in i["room_breakdown"] if b["qty"] is not None)
            if not _close(s, i["qty"], tol):
                errors.append({"error": "BREAKDOWN_DOES_NOT_RECONCILE", "item": i["canonical_item_id"],
                               "sum": s, "qty": i["qty"]})
        p = i.get("measure_pair")
        if p is not None and (p not in by_id or by_id[p].get("measure_pair") != i["canonical_item_id"]):
            errors.append({"error": "MEASURE_PAIR_NOT_RECIPROCAL", "item": i["canonical_item_id"], "pair": p})
    for n, a in enumerate(items):
        for b in items[n + 1:]:
            if a["layer"] != b["layer"] or a["unit"] != b["unit"]:
                continue
            if a.get("measure_pair") == b["canonical_item_id"]:
                continue
            ka = {x["key"] for x in a["room_breakdown"]}
            kb = {x["key"] for x in b["room_breakdown"]}
            if ka & kb or (not ka and not kb):
                errors.append({"error": "ADDITIVE_DOUBLE_COUNT", "items": [a["canonical_item_id"],
                                                                         b["canonical_item_id"]],
                               "layer": a["layer"], "shared_keys": sorted(ka & kb)})
    pairs = sorted({tuple(sorted((i["canonical_item_id"], i["measure_pair"]))) for i in items if i["measure_pair"]})
    return {"state": "PASS" if not errors else "FAIL", "errors": errors, "items": len(items),
            "aliases": sum(len(i["legacy_row_ids"]) for i in items), "measure_pairs": [list(p) for p in pairs],
            "digest_ok": model["digest"] == _digest({k: v for k, v in model.items() if k != "digest"})}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "fields": list(FIELDS), "relations": list(RELATIONS), "statuses": list(STATUSES),
           "identity": "physical layer + unit + breakdown keys (sites / strips / openings)",
           "never": ["a legacy id as a separate additive line", "two additive items on the same layer, unit and site",
                     "a measure pair presented as two quantities to add", "a breakdown that does not reconcile",
                     "a quantity computed here (every qty is copied from an engine register row)"]}
    rec["digest"] = _digest(rec)
    return rec
