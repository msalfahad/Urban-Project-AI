"""STRUCTURAL QTO (V1) - deterministic concrete rows from drawn elements + schedules; rebar FAIL CLOSED.

rectangles()     closed axis-aligned rectangles from segments of ONE element layer: collinear touching / overlapping
                 segments are merged first, then every pair of parallel edges of equal span joined by two edges at
                 both ends is a rectangle. Nested rectangles are all reported; nothing is snapped.
associate()      each element tag (text) is placed in the SMALLEST rectangle that contains it strictly; a rectangle
                 with no tag, or with two tags, is reported (never resolved by distance).
size_check()     a drawn rectangle against its schedule plan size (either orientation), in millimetres, within an
                 explicit tolerance - the schedule size is CONFIRMED by the drawing or the row is not COMPLETE.
concrete_row()   one row: element class, floor, element id, source ids, every dimension WITH its source, formula,
                 quantity. A missing dimension makes the row BLOCKED and names it; nothing defaults.
rebar_gate()     a rebar quantity needs bar diameter, count or spacing, bar length, bar shape, laps and cover from the
                 source. Anything missing -> PARTIAL (spec known) or BLOCKED. A kg/m3 ratio is refused outright.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "STRUCTURAL_QTO_V1"
COMPLETE, PARTIAL, BLOCKED = "COMPUTED_SHADOW_COMPLETE", "PARTIAL", "BLOCKED"
SIZE_CONFIRMED, SIZE_MISMATCH = "SIZE_CONFIRMED", "SIZE_MISMATCH"
NO_TAG, MULTIPLE_TAGS, TAG_OUTSIDE = "RECTANGLE_WITHOUT_TAG", "RECTANGLE_WITH_SEVERAL_TAGS", "TAG_OUTSIDE_EVERY_RECTANGLE"
REBAR_FIELDS = ("bar_diameter_mm", "count_or_spacing", "bar_length", "bar_shape", "laps", "cover")
FORBIDDEN_REBAR_KEYS = ("kg_per_m3", "ratio", "steel_ratio", "kg_m3")


def _merge(spans, eps):
    out = []
    for a, b, keys in sorted(spans):
        if out and a <= out[-1][1] + eps:
            out[-1] = (out[-1][0], max(out[-1][1], b), out[-1][2] + keys)
        else:
            out.append((a, b, list(keys)))
    return out


def edges(segments, *, eps):
    """segments [(key, x1, y1, x2, y2)] -> (horizontal [(y, x0, x1, keys)], vertical [(x, y0, y1, keys)])."""
    hz, vt = {}, {}
    for key, x1, y1, x2, y2 in segments:
        if abs(y1 - y2) <= eps and abs(x1 - x2) > eps:
            hz.setdefault(round((y1 + y2) / 2.0 / eps), []).append((min(x1, x2), max(x1, x2), [key]))
        elif abs(x1 - x2) <= eps and abs(y1 - y2) > eps:
            vt.setdefault(round((x1 + x2) / 2.0 / eps), []).append((min(y1, y2), max(y1, y2), [key]))
    H = [(k * eps, a, b, sorted(keys)) for k, sp in hz.items() for a, b, keys in _merge(sp, eps)]
    V = [(k * eps, a, b, sorted(keys)) for k, sp in vt.items() for a, b, keys in _merge(sp, eps)]
    return sorted(H), sorted(V)


def _covers(edge_list, at, lo, hi, eps):
    return [e for e in edge_list if abs(e[0] - at) <= eps and e[1] <= lo + eps and e[2] >= hi - eps]


def rectangles(segments, *, eps) -> list:
    H, V = edges(segments, eps=eps)
    xs = sorted({round(v[0] / eps) * eps for v in V})
    out, seen = [], set()
    for i, (ya, a0, a1, ka) in enumerate(H):
        for yb, b0, b1, kb in H[i + 1:]:
            if yb - ya <= eps:
                continue
            lo, hi = max(a0, b0), min(a1, b1)
            if hi - lo <= eps:
                continue
            cand = [x for x in xs if lo - eps <= x <= hi + eps and _covers(V, x, ya, yb, eps)]
            for p in range(len(cand)):
                for q in range(p + 1, len(cand)):
                    x0, x1 = cand[p], cand[q]
                    if not (_covers([(ya, a0, a1, ka)], ya, x0, x1, eps) and _covers([(yb, b0, b1, kb)], yb, x0, x1, eps)):
                        continue
                    # minimal: no other covering vertical edge strictly between, no other horizontal edge between
                    if any(x0 + eps < x < x1 - eps for x in cand[p + 1:q]):
                        continue
                    if any(ya + eps < h[0] < yb - eps and h[1] <= x0 + eps and h[2] >= x1 - eps for h in H):
                        continue
                    b = (round(x0, 6), round(ya, 6), round(x1, 6), round(yb, 6))
                    if b in seen:
                        continue
                    seen.add(b)
                    vk = sorted(set(_covers(V, x0, ya, yb, eps)[0][3] + _covers(V, x1, ya, yb, eps)[0][3]))
                    out.append({"bounds": b, "width": x1 - x0, "height": yb - ya,
                                "edge_keys": sorted(set(ka + kb + vk))})
    return sorted(out, key=lambda r: r["bounds"])


def associate(rects, tags) -> dict:
    """tags [{"key", "value", "x", "y"}] -> {"rectangles": [rect + tags], "orphans": [...], "issues": [...]}."""
    rs = [dict(r, tags=[]) for r in rects]
    orphans = []
    for t in sorted(tags, key=lambda t: t["key"]):
        inside = [r for r in rs if r["bounds"][0] < t["x"] < r["bounds"][2] and r["bounds"][1] < t["y"] < r["bounds"][3]]
        if not inside:
            orphans.append(dict(t, why=TAG_OUTSIDE))
            continue
        min(inside, key=lambda r: (r["width"] * r["height"], r["bounds"]))["tags"].append(t)
    issues = [{"rectangle": r["bounds"], "why": NO_TAG if not r["tags"] else MULTIPLE_TAGS,
               "tags": [t["value"] for t in r["tags"]]} for r in rs if len(r["tags"]) != 1]
    return {"rectangles": rs, "orphans": orphans, "issues": issues}


def size_check(rect, length_mm, width_mm, native_to_mm, *, tol_mm) -> dict:
    a, b = rect["width"] * native_to_mm, rect["height"] * native_to_mm
    ok = min(max(abs(a - length_mm), abs(b - width_mm)), max(abs(a - width_mm), abs(b - length_mm))) <= tol_mm
    return {"state": SIZE_CONFIRMED if ok else SIZE_MISMATCH, "drawn_mm": [round(a, 3), round(b, 3)],
            "schedule_mm": [length_mm, width_mm], "tol_mm": tol_mm}


def concrete_row(*, item, element_class, floor, element_id, count, dims, formula, sources, extra_blockers=()) -> dict:
    """dims {name: {"m": value or None, "source": text or None}}; qty = count x product of dims (m3)."""
    blockers = list(extra_blockers)
    if count is None:
        blockers.append("COUNT_NOT_ESTABLISHED")
    for n, d in sorted(dims.items()):
        if d.get("m") is None or not d.get("source"):
            blockers.append(f"DIMENSION_NOT_ESTABLISHED:{n}")
    qty = None
    if not blockers:
        q = float(count)
        for d in dims.values():
            q *= d["m"]
        qty = round(q, 6)
    return {"item": item, "element_class": element_class, "floor": floor, "element_id": element_id,
            "count": count, "dims": dims, "formula": formula, "qty": qty, "unit": "m3",
            "status": COMPLETE if qty is not None else BLOCKED, "blockers": sorted(set(blockers)),
            "sources": sorted(set(sources))}


def rebar_gate(spec: dict) -> dict:
    bad = sorted(k for k in spec if k in FORBIDDEN_REBAR_KEYS)
    if bad:
        raise ValueError(f"rebar from a ratio is refused: {bad}")
    have = [f for f in REBAR_FIELDS if spec.get(f) not in (None, "")]
    missing = [f for f in REBAR_FIELDS if f not in have]
    state = COMPLETE if not missing else PARTIAL if {"bar_diameter_mm", "count_or_spacing"} <= set(have) else BLOCKED
    return {"state": state, "have": have, "missing": missing, "quantity_kg": None if missing else "COMPUTABLE"}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "rebar_fields": list(REBAR_FIELDS), "forbidden": list(FORBIDDEN_REBAR_KEYS),
           "never": ["a default dimension", "a kg/m3 ratio", "a tag resolved by nearest distance",
                     "a schedule size the drawing contradicts"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
