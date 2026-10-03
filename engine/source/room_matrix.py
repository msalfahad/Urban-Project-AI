"""ROOM QUANTITY MATRIX (RC1) - room-by-room VIEW of trade rows, with proof that the rooms add up.

row_breakdown() turns one trade row (its sites_used and its strip audit) into breakdown entries WITHOUT new
arithmetic on geometry: a site entry is the site area plus the effects of strips that lie INSIDE that site (e.g. a
passage soffit excluded from a ceiling); a strip that is its own physical site (a door strip) and is in the row total
becomes its own STRIP entry naming both sides. The entries must sum to the row value (within the row's rounding).

display_names() keeps every physical site distinct: two sites with the same label get an ordinal and a short site id
- a label is never a reason to merge, and never room authority by itself.

matrix() lays canonical items out as one row per room / strip (a VIEW: nothing is computed) and checks, per item,
that the matrix column sums to the item quantity; any item whose column does not reconcile is listed (RC1 blocks).

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "ROOM_QUANTITY_MATRIX_V1"
ROOM, STRIP, OUTSIDE = "ROOM", "STRIP", "OUTSIDE_ROOM"


def _digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def row_breakdown(sites_used: list, strip_audit: list, value, *, tol: float) -> dict:
    """sites_used: [{"site", "zones", "area_m2"}]; strip_audit: [{"strip", "location" (INSIDE_SITE / SEPARATE_SITE),
    "sides" {site: treatment}, "contribution_m2", "in_row_total", "state", "area_m2"}]."""
    by_site = {u["site"]: {"key": u["site"], "kind": ROOM, "zones": list(u["zones"]), "qty": u["area_m2"],
                           "site_area_m2": u["area_m2"], "inside_effects": []} for u in sites_used}
    strips = []
    for a in strip_audit:
        c = a.get("contribution_m2") or 0.0
        if a.get("location") == "INSIDE_SITE":
            home = [s for s in (a.get("sides") or {}) if s in by_site]
            if c and len(home) == 1:
                e = by_site[home[0]]
                e["qty"] = e["qty"] + c
                e["inside_effects"].append({"strip": a["strip"], "effect_m2": c, "state": a.get("state")})
            elif c:
                strips.append({"key": a["strip"], "kind": STRIP, "qty": c, "sides": sorted(a.get("sides") or {}),
                               "state": a.get("state"), "error": "INSIDE_SITE effect without one home site"})
        elif a.get("in_row_total") and c:
            strips.append({"key": a["strip"], "kind": STRIP, "qty": c, "sides": sorted(a.get("sides") or {}),
                           "state": a.get("state"), "strip_area_m2": a.get("area_m2")})
    entries = [by_site[k] for k in sorted(by_site)] + sorted(strips, key=lambda e: e["key"])
    total = sum(e["qty"] for e in entries)
    ok = value is not None and abs(total - value) <= tol and not any("error" in e for e in entries)
    return {"entries": entries, "sum": total, "value": value, "reconciles": ok, "tol": tol}


def display_names(sites: list) -> dict:
    """sites: [{"site_id", "zones"}] -> {site_id: display name}; equal names get ' (n) [site short id]'."""
    base = {s["site_id"]: " / ".join(s["zones"]) for s in sites}
    out = {}
    for sid in sorted(base):
        same = sorted(k for k, v in base.items() if v == base[sid])
        out[sid] = base[sid] if len(same) == 1 else f"{base[sid]} ({same.index(sid) + 1}) [{sid[5:13]}]"
    return out


def matrix(rows: list, items: list, *, tol: float) -> dict:
    """rows: [{"key", "kind", "display", ...}] (rooms then strips, in display order); items: canonical items (with
    room_breakdown keyed like rows). Each cell = the breakdown entry qty of that item for that row key, or None."""
    cols = [i["canonical_item_id"] for i in items]
    cells = {}
    for i in items:
        for b in i["room_breakdown"]:
            cells[(b["key"], i["canonical_item_id"])] = b["qty"]
    keys = {r["key"] for r in rows}
    out = [dict(r, cells={c: cells.get((r["key"], c)) for c in cols}) for r in rows]
    recon, unplaced = {}, []
    for i in items:
        c = i["canonical_item_id"]
        miss = [b["key"] for b in i["room_breakdown"] if b["key"] not in keys]
        unplaced += [{"item": c, "key": k} for k in miss]
        s = sum(v for r in out if (v := r["cells"][c]) is not None)
        additive = i.get("breakdown_additive", True)
        recon[c] = {"column_sum": s, "item_qty": i["qty"], "additive": additive,
                    "reconciles": (not additive) or i["qty"] is None and not i["room_breakdown"] or
                    (i["qty"] is not None and abs(s - i["qty"]) <= tol)}
    bad = sorted(c for c, v in recon.items() if not v["reconciles"])
    return {"policy": POLICY_ID, "columns": cols, "rows": out, "reconciliation": recon, "not_reconciled": bad,
            "unplaced": unplaced, "state": "PASS" if not bad and not unplaced else "FAIL", "view_only": True}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID,
           "breakdown": "site area + inside-site strip effects; separate-site strips in the row total are their own "
                        "STRIP entries; entries must sum to the row value",
           "names": "equal labels never merge sites: ordinal + short site id",
           "never": ["a matrix cell computed from geometry here", "a label as room authority", "a column that does "
                     "not reconcile to its canonical item"]}
    rec["digest"] = _digest(rec)
    return rec
