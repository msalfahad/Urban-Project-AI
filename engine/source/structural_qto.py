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


# ======================================================================== A2: constraint-unique completion
COMPLETION_POLICY_ID = "STRUCTURAL_COMPLETION_V1"
COUNT_UNIQUE, COUNT_MISMATCH, NO_CANDIDATE = "COUNT_UNIQUE", "COUNT_MISMATCH", "NO_TEMPLATE_CANDIDATE"
FULL, CLIPPED = "FULLY_DRAWN", "CLIPPED_ONE_SIDE_BY_SUPPORT_LINE"


def _coverage(edge_list, at, lo, hi, eps):
    """Fraction of [lo, hi] covered by the merged edges lying at `at`."""
    iv = sorted((max(e[1], lo), min(e[2], hi)) for e in edge_list if abs(e[0] - at) <= eps and e[2] > lo and e[1] < hi)
    cov, cur = 0.0, None
    for a, b in iv:
        if cur is None or a > cur[1]:
            if cur is not None:
                cov += cur[1] - cur[0]
            cur = [a, b]
        else:
            cur[1] = max(cur[1], b)
    if cur is not None:
        cov += cur[1] - cur[0]
    return cov / (hi - lo) if hi > lo else 0.0


def _uncovered(edge_list, at, lo, hi, eps):
    iv = sorted((max(e[1], lo), min(e[2], hi)) for e in edge_list if abs(e[0] - at) <= eps and e[2] > lo and e[1] < hi)
    gaps, cur = [], lo
    for a, b in iv:
        if a > cur + eps:
            gaps.append((cur, a))
        cur = max(cur, b)
    if hi > cur + eps:
        gaps.append((cur, hi))
    return gaps


def template_outlines(segments, length_mm, width_mm, native_to_mm, *, eps, min_cover=0.8, support=(),
                      entry_cover=0.5) -> list:
    """Axis-aligned outlines of EXACTLY the schedule plan size (either orientation) in one element layer's
    linework: the lower-left corner is a drawn end point, and each side is covered >= min_cover by the layer's
    merged edges. A side covered >= entry_cover whose every uncovered stretch is bounded at BOTH ends by segments of
    the layer that do NOT run along the side and touch or pass through the gap end (an element entering the outline: a strap / tie beam)
    passes as ENTRY_GAPS_EXPLAINED; a bare gap (only the side's own pieces end there) does not. `support` (another layer's segments, e.g. a site boundary) may cover AT MOST ONE side
    (CLIPPED). Nothing is snapped or scaled; the schedule size is the template, the drawing must carry it."""
    H, V = edges(segments, eps=eps)
    sH, sV = edges(support, eps=eps) if support else ([], [])
    ends = [(x, y) for _, x1, y1, x2, y2 in segments for x, y in ((x1, y1), (x2, y2))]
    import math as _m

    def entering_end(x, y, horiz):
        """a segment NOT running along the side touches or passes through this gap end (an entering element)"""
        for _, x1, y1, x2, y2 in segments:
            if (abs(y1 - y2) <= eps) if horiz else (abs(x1 - x2) <= eps):
                continue
            dx, dy = x2 - x1, y2 - y1
            L2 = dx * dx + dy * dy
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
            if _m.hypot(x - x1 - t * dx, y - y1 - t * dy) <= eps:
                return True
        return False
    out, seen = [], set()
    sizes = {(length_mm / native_to_mm, width_mm / native_to_mm), (width_mm / native_to_mm, length_mm / native_to_mm)}
    corners = sorted({(round(x, 6), round(y, 6)) for x, y in ends})
    for x, y in corners:
        for a, b in sorted(sizes):
            x1, y1 = x + a, y + b
            spec = {"S": (H, y, x, x1, True), "N": (H, y1, x, x1, True), "W": (V, x, y, y1, False),
                    "E": (V, x1, y, y1, False)}
            sides, how, weak = {}, {}, []
            for k, (E_, at, lo, hi, horiz) in spec.items():
                c = _coverage(E_, at, lo, hi, eps)
                sides[k] = c
                if c >= min_cover:
                    how[k] = "COVERED"
                    continue
                gaps = _uncovered(E_, at, lo, hi, eps)
                pts = [((g0, at), (g1, at)) if horiz else ((at, g0), (at, g1)) for g0, g1 in gaps]
                if c >= entry_cover and gaps and all(entering_end(*p0, horiz) and entering_end(*p1, horiz)
                                                      for p0, p1 in pts):
                    how[k] = "ENTRY_GAPS_EXPLAINED"
                    continue
                weak.append(k)
            state = FULL if all(v == "COVERED" for v in how.values()) and not weak else "ENTRY_GAPS_EXPLAINED"
            if len(weak) == 1 and support:
                k = weak[0]
                c = (_coverage(sH, y if k == "S" else y1, x, x1, eps) if k in "SN"
                     else _coverage(sV, x if k == "W" else x1, y, y1, eps))
                if c >= min_cover:
                    state, how[k], weak = CLIPPED, "SUPPORT_LINE", []
            if weak:
                continue
            bnd = (round(x, 6), round(y, 6), round(x1, 6), round(y1, 6))
            if bnd in seen:
                continue
            seen.add(bnd)
            out.append({"bounds": bnd, "width": a, "height": b, "state": state, "sides": dict(sorted(how.items())),
                        "side_cover": {k: round(v, 4) for k, v in sorted(sides.items())}})
    return sorted(out, key=lambda r: r["bounds"])


def _overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def complete_by_count(orphans: dict, candidates: dict, taken=(), carriers=(), tags=()) -> dict:
    """Type-level constraint-unique completion. orphans {type: [tag records with x, y]} (tags matched to no drawn
    outline), candidates {type: [template outlines]}. A candidate is admissible only if it overlaps no outline
    already matched (`taken`) and carries a supported element inside (`carriers`: [(x, y)], e.g. column centres).
      1 CONTAINED      an admissible candidate holding exactly one tag of all `tags`, and that tag is an orphan of
                       this type -> that orphan is matched to it
      2 COUNT_UNIQUE   the admissible candidates holding no tag, pairwise disjoint, EXACTLY as many as the orphans
                       still unmatched -> those orphans are complete by two independent channels (tag; drawn outline
                       of the scheduled size) without deciding which tag names which outline
    Anything else stays blocked and says why. Never by nearest distance."""
    out = {}
    inside = lambda b, x, y: b[0] < x < b[2] and b[1] < y < b[3]
    for typ in sorted(orphans):
        adm = []
        for c in candidates.get(typ, []):
            b = c["bounds"]
            if any(_overlap(b, t) for t in taken):
                continue
            if carriers and not any(inside(b, x, y) for x, y in carriers):
                continue
            adm.append(c)
        left = list(orphans[typ])
        contained, free = [], []
        for c in adm:
            held = [(x, y) for x, y in tags if inside(c["bounds"], x, y)]
            if not held:
                free.append(c)
                continue
            mine = [o for o in left if inside(c["bounds"], o["x"], o["y"])]
            if len(held) == 1 and len(mine) == 1:
                contained.append(dict(c, matched_tag=mine[0]["key"], rule="CONTAINED"))
                left = [o for o in left if o is not mine[0]]
        free = [c for c in free if not any(_overlap(c["bounds"], k["bounds"]) for k in contained)]
        disjoint = all(not _overlap(a["bounds"], b["bounds"]) for i, a in enumerate(free) for b in free[i + 1:])
        n, m = len(left), len(free)
        if n == 0:
            state = COUNT_UNIQUE if contained else NO_CANDIDATE
        else:
            state = COUNT_UNIQUE if (n == m and disjoint) else (NO_CANDIDATE if m == 0 and not contained
                                                                 else COUNT_MISMATCH)
        out[typ] = {"state": state, "orphan_tags": len(orphans[typ]), "contained": contained,
                    "unmatched_after_containment": n, "free_candidates": m, "disjoint": disjoint,
                    "outlines": [dict(c, rule="COUNT_UNIQUE") for c in free] if state == COUNT_UNIQUE else
                    [dict(c, rule="CANDIDATE_ONLY") for c in free]}
    return out


def completion_policy_record() -> dict:
    rec = {"id": COMPLETION_POLICY_ID,
           "template": "schedule plan size L x W (either orientation) drawn in the element layer; corner at a drawn "
                       "end point; every side covered >= 0.8, or >= 0.5 with every gap bounded by drawn end points "
                       "(an entering strap / tie beam); one side may be covered by a support line (CLIPPED)",
           "uniqueness": "per type: candidates overlapping no matched outline and carrying a supported element; "
                         "CONTAINED when a candidate holds exactly one tag and it is this type's orphan; then "
                         "COUNT_UNIQUE iff the tag-free disjoint candidates equal the orphans left",
           "never": ["nearest-distance matching", "snapping", "scaling", "a candidate holding another tag"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
