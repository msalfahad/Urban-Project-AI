"""STRUCTURAL SCHEDULE-DRIVEN QTO (V1) - plan mark = type identity, schedule = nominal dimensions, plan geometry =
validation. Every plan mark becomes exactly ONE occurrence row (computed or blocked); type summaries are derived
from the occurrence rows, never written by hand.

parse_mark()        a plan text -> the schedule type(s) it names: '/'-separated tokens matched EXACTLY against the
                    admitted schedule types (an optional normalisation that only drops '.' / blanks is allowed when it
                    gives exactly one type, and is recorded). A text naming no admitted type is not a mark.
entity_rings()      closed outlines from ONE source entity's segments (a polyline): chained end to end; an outline open
                    at exactly one straight gap closes only when BOTH gap ends are met by another element line that
                    does not run along the gap (an entering strap / tie) -> GAP_EXPLAINED (the entering keys recorded).
bind_by_containment each mark to the SMALLEST candidate outline containing its insertion point (polygon test). An
                    outline holding marks of two or more occurrences is a COMBINED outline.
footing_occurrences one row per footing mark with a geometry state:
   GEOMETRY_CONFIRMED                  its own outline (single mark) is exactly the scheduled plan size, drawn whole
   SCHEDULE_AUTHORITY_INTERRUPTED      its own outline has the scheduled extent but is interrupted by an adjacent
                                       element: an entering strap / tie gap, a notch occupied by a neighbouring
                                       outline, or a side carried by a support line (overlaps recorded, not deducted)
   SCHEDULE_AUTHORITY_COUNT_UNIQUE     no outline contains the mark; the free outlines of the scheduled size equal
                                       the type's unbound marks (structural_qto.complete_by_count)
   SOURCE_CONFLICT_COMBINED_OUTLINE    the outline holding the mark holds another occurrence's mark too -> BLOCKED,
                                       schedule value and drawn extent both reported
   SOURCE_CONFLICT_DRAWN_SIZE          its own single-mark outline is drawn at another size -> BLOCKED
   TAG_WITHOUT_BOUND_GEOMETRY          nothing binds the mark (count mismatch / no candidate) -> BLOCKED
   TYPE_NOT_IN_SCHEDULE                the mark parses to no admitted schedule row -> BLOCKED
   An explicit local dimension bound to the occurrence is the only override (EXPLICIT_LOCAL_OVERRIDE); a candidate
   assembled by a matcher (clipping, footing + strap union) is never quantity authority.
type_summary()      TYPE | COUNT_TAGGED | CONFIRMED | PARTIAL | CONFLICT | BLOCKED | L | W | H | M3_EACH | M3_TOTAL
                    from the occurrence rows only.
reconcile()         per type: tags == computed + blocked, every tag key exactly once, every used type scheduled.
column_storeys()    per-storey column sections from schedule storey bands; counts from plan marks; plan areas; the
                    printed per-occurrence size labels compared as a multiset (deviations reported, never overriding).
beam_bands()        a beam / strap occurrence is measurable only when its mark lies BETWEEN a parallel pair of element
                    lines whose separation is the scheduled breadth; the clear length is the pair's common span minus
                    the parts inside supporting outlines (footings / columns).
rebar_definitions() bar counts / diameters per schedule row (DEFINITION); a weight needs cutting length, cover,
                    hooks and laps from the source -> BLOCKED otherwise; a kg/m3 ratio is refused.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict

from engine.source import structural_qto as SQ

POLICY_ID = "STRUCTURAL_SCHEDULE_QTO_V1"
COMPLETE, BLOCKED = SQ.COMPLETE, SQ.BLOCKED
CONFIRMED = "GEOMETRY_CONFIRMED"
INTERRUPTED = "SCHEDULE_AUTHORITY_INTERRUPTED"
COUNT_UNIQUE = "SCHEDULE_AUTHORITY_COUNT_UNIQUE"
OVERRIDE = "EXPLICIT_LOCAL_OVERRIDE"
COMBINED = "SOURCE_CONFLICT_COMBINED_OUTLINE"
DRAWN_SIZE = "SOURCE_CONFLICT_DRAWN_SIZE"
UNBOUND = "TAG_WITHOUT_BOUND_GEOMETRY"
NOT_SCHEDULED = "TYPE_NOT_IN_SCHEDULE"
COMPUTED_STATES = (CONFIRMED, INTERRUPTED, COUNT_UNIQUE, OVERRIDE)
PARTIAL_STATES = (INTERRUPTED, COUNT_UNIQUE)
CONFLICT_STATES = (COMBINED, DRAWN_SIZE)
GAP_EXPLAINED, CLOSED, NOTCHED = "GAP_EXPLAINED_BY_ENTERING_ELEMENT", "CLOSED", "NOTCH_AT_ADJACENT_OUTLINE"
FORBIDDEN_REBAR_KEYS = SQ.FORBIDDEN_REBAR_KEYS
BAND_WIDTH_DEVIATION_MAX = 0.05   # a band whose drawn width is within 5 % of the scheduled breadth still holds the
                                  # mark (schedule authority for the section; the deviation is reported)


# ------------------------------------------------------------------ marks
def parse_mark(value, types, *, normalise=True) -> dict:
    """-> {"types": [...], "normalised": bool}. Exact token match first; '.'/blank removal only if it yields one."""
    toks = [t.strip() for t in str(value or "").replace(" ", "").split("/") if t.strip()]
    ts = set(types)
    exact = [t for t in toks if t in ts]
    if exact:
        return {"types": exact, "normalised": False}
    if normalise:
        norm = {re.sub(r"[.\s]", "", t): t for t in ts}
        hit = [norm[re.sub(r"[.\s]", "", t)] for t in toks if re.sub(r"[.\s]", "", t) in norm]
        if len(hit) == 1:
            return {"types": hit, "normalised": True}
    return {"types": [], "normalised": False}


# ------------------------------------------------------------------ geometry helpers
def _d(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def polygon_area(poly) -> float:
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2.0


def point_in_polygon(x, y, poly) -> bool:
    inside, n = False, len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def _bounds(poly):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    return (min(xs), min(ys), max(xs), max(ys))


def _simplify(poly, eps):
    out = list(poly)
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            if abs(cross) <= eps * max(_d(a, c), 1e-9) or _d(a, b) <= eps:
                del out[i]
                changed = True
                break
    return out


def _entity(key):
    """'REV|H6939||SEGMENT|3' -> 'REV|H6939|' (the source entity: everything before the part kind / index)."""
    parts = str(key).split("|")
    return "|".join(parts[:-2]) if len(parts) >= 3 else str(key)


def _touches(pt, seg, eps):
    _, x1, y1, x2, y2 = seg
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((pt[0] - x1) * dx + (pt[1] - y1) * dy) / L2))
    return math.hypot(pt[0] - x1 - t * dx, pt[1] - y1 - t * dy) <= eps


def entity_rings(segments, *, eps, others=()) -> list:
    """segments [(key, x1, y1, x2, y2)] of one element layer; `others` the element lines that may enter an outline.
    -> [{"id", "entity", "polygon", "bounds", "area", "state", "keys", "gap_keys"}]"""
    by = defaultdict(list)
    for s in segments:
        by[_entity(s[0])].append(s)
    pool = list(segments) + list(others)
    out = []
    for ent, ss in sorted(by.items()):
        if len(ss) < 3:
            continue
        pts = []
        for s in ss:
            for p in ((s[1], s[2]), (s[3], s[4])):
                if not any(_d(p, q) <= eps for q in pts):
                    pts.append(p)
        idx = lambda p: next(i for i, q in enumerate(pts) if _d(p, q) <= eps)
        adj = defaultdict(list)
        for s in ss:
            a, b = idx((s[1], s[2])), idx((s[3], s[4]))
            if a != b:
                adj[a].append(b)
                adj[b].append(a)
        deg = {i: len(v) for i, v in adj.items()}
        if any(d > 2 for d in deg.values()) or len(adj) < 3:
            continue
        ends = sorted(i for i, d in deg.items() if d == 1)
        if len(ends) not in (0, 2):
            continue
        # walk one chain
        start = ends[0] if ends else min(adj)
        order, prev, cur = [start], None, start
        while True:
            nxt = [j for j in adj[cur] if j != prev]
            if not nxt or (not ends and nxt[0] == start):
                break
            prev, cur = cur, nxt[0]
            if cur in order:
                break
            order.append(cur)
        if len(order) != len(adj):
            continue                                          # not one connected chain
        state, gap_keys = CLOSED, []
        if ends:
            a, b = pts[ends[0]], pts[ends[1]]
            ux, uy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(ux, uy)
            if L <= eps:
                continue
            ent_keys = {s[0] for s in ss}

            def entering(p):
                hits = []
                for o in pool:
                    if o[0] in ent_keys:
                        continue
                    ox, oy = o[3] - o[1], o[4] - o[2]
                    Lo = math.hypot(ox, oy)
                    if Lo <= eps or abs(ux * oy - uy * ox) / (L * Lo) < 0.5:       # runs along the gap
                        continue
                    if _touches(p, o, eps):
                        hits.append(o[0])
                return hits
            ha, hb = entering(a), entering(b)
            if not (ha and hb):
                continue
            state, gap_keys = GAP_EXPLAINED, sorted(set(ha + hb))
        poly = _simplify([pts[i] for i in order], eps)
        if len(poly) < 3:
            continue
        out.append({"id": "RING:" + ent, "entity": ent, "polygon": [(round(x, 6), round(y, 6)) for x, y in poly],
                    "bounds": tuple(round(v, 6) for v in _bounds(poly)), "area": polygon_area(poly), "state": state,
                    "keys": sorted(s[0] for s in ss), "gap_keys": gap_keys, "kind": "ENTITY_RING"})
    return out


def rect_candidate(r, kind="RECTANGLE"):
    x0, y0, x1, y1 = r["bounds"]
    poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return {"id": f"{kind}:{x0:.3f},{y0:.3f},{x1:.3f},{y1:.3f}", "entity": None, "polygon": poly,
            "bounds": tuple(r["bounds"]), "area": (x1 - x0) * (y1 - y0),
            "state": r.get("state", CLOSED) if kind == "TEMPLATE" else CLOSED,
            "keys": list(r.get("edge_keys", [])), "gap_keys": [], "kind": kind,
            "sides": r.get("sides")}


def merge_candidates(*groups) -> list:
    """De-duplicate by bounds (entity rings first, then rectangles, then templates); keys are united."""
    out = {}
    for g in groups:
        for c in g:
            b = tuple(round(v, 3) for v in c["bounds"])
            if b in out and abs(out[b]["area"] - c["area"]) <= 1e-6 * max(c["area"], 1.0):
                out[b]["keys"] = sorted(set(out[b]["keys"]) | set(c["keys"]))
                out[b].setdefault("also", []).append(c["kind"])
                continue
            if b not in out:
                out[b] = dict(c)
    return [out[k] for k in sorted(out)]


def contains(c, x, y) -> bool:
    return point_in_polygon(x, y, c["polygon"])


# ------------------------------------------------------------------ footings
def _size_ok(c, L_mm, W_mm, umm, tol_mm):
    b = c["bounds"]
    a, h = (b[2] - b[0]) * umm, (b[3] - b[1]) * umm
    return min(max(abs(a - L_mm), abs(h - W_mm)), max(abs(a - W_mm), abs(h - L_mm))) <= tol_mm, [round(a, 3), round(h, 3)]


def footing_occurrences(marks, library, candidates, *, umm, tol_mm, eps, templates_by_type=None, carriers=(),
                        overrides=None) -> dict:
    """marks [{"key", "value", "x", "y", "type"}] (type parsed against `library`); library {type: {"L_cm", "W_cm",
    "H_cm", "keys", ...}}; candidates: merged outlines (entity rings + rectangles + schedule-size templates).
    overrides {mark key: {"L_m", "W_m", "H_m", "source"}} - explicit local dimensions bound to the occurrence."""
    overrides = overrides or {}
    templates_by_type = templates_by_type or {}
    bound = {}
    for m in marks:
        inside = [c for c in candidates if contains(c, m["x"], m["y"])]
        if inside:
            bound[m["key"]] = min(inside, key=lambda c: (c["area"], c["id"]))
    holders = defaultdict(list)
    for m in marks:
        if m["key"] in bound:
            holders[bound[m["key"]]["id"]].append(m)
    rows, orphans = {}, defaultdict(list)
    for m in sorted(marks, key=lambda z: z["key"]):
        t, ft = m["type"], library.get(m["type"])
        base = {"type": t, "mark_key": m["key"], "mark_value": m["value"], "mark_xy": [round(m["x"], 3), round(m["y"], 3)],
                "schedule_row": None if ft is None else {"type": t, "keys": ft.get("keys", []), "L_cm": ft["L_cm"],
                                                          "W_cm": ft["W_cm"], "H_cm": ft["H_cm"]}}
        if ft is None or None in (ft.get("L_cm"), ft.get("W_cm"), ft.get("H_cm")):
            rows[m["key"]] = dict(base, geometry_state=NOT_SCHEDULED, why="mark names no admitted schedule row")
            continue
        c = bound.get(m["key"])
        if c is None:
            orphans[t].append(m)
            continue
        held = holders[c["id"]]
        geo = {"outline": c["id"], "outline_kind": c["kind"], "outline_state": c["state"],
               "drawn_mm": _size_ok(c, ft["L_cm"] * 10, ft["W_cm"] * 10, umm, tol_mm)[1],
               "outline_keys": c["keys"], "gap_keys": c.get("gap_keys", [])}
        if len(held) > 1:
            rows[m["key"]] = dict(base, geometry_state=COMBINED, geometry=geo,
                                  shared_with=[h["key"] for h in held if h["key"] != m["key"]],
                                  why=f"one source outline {geo['drawn_mm']} mm holds {len(held)} marks "
                                      f"({', '.join(sorted(h['value'] for h in held))}); the schedule rectangles "
                                      "cannot all equal it")
            continue
        ok, drawn = _size_ok(c, ft["L_cm"] * 10, ft["W_cm"] * 10, umm, tol_mm)
        if not ok:
            rows[m["key"]] = dict(base, geometry_state=DRAWN_SIZE, geometry=geo,
                                  why=f"its own outline is drawn {drawn} mm, schedule {[ft['L_cm'] * 10, ft['W_cm'] * 10]} mm")
            continue
        bb = (c["bounds"][2] - c["bounds"][0]) * (c["bounds"][3] - c["bounds"][1])
        full_rect = abs(c["area"] - bb) <= 1e-4 * bb
        if full_rect and c["state"] in (CLOSED, SQ.FULL):
            state, why = CONFIRMED, "own outline drawn whole at the scheduled plan size"
        elif not full_rect:
            # notch: the missing part of the bounding box must lie inside another candidate outline
            b = c["bounds"]
            notch = (b[2] - b[0]) * (b[3] - b[1]) - c["area"]
            others = [o for o in candidates if o["id"] != c["id"] and SQ._overlap(o["bounds"], b)
                      and not contains(o, m["x"], m["y"])]
            if others:
                state, why = INTERRUPTED, "outline notched where an adjacent outline sits"
                geo["notch_m2"] = round(notch * umm * umm / 1e6, 6)
                geo["adjacent_outlines"] = [o["id"] for o in others]
                geo["outline_state"] = NOTCHED
            else:
                rows[m["key"]] = dict(base, geometry_state=DRAWN_SIZE, geometry=geo,
                                      why="outline is not the scheduled rectangle and no adjacent outline explains it")
                continue
        else:
            state, why = INTERRUPTED, f"outline {c['state']} (an entering element / support line interrupts it)"
        rows[m["key"]] = dict(base, geometry_state=state, geometry=geo, why=why)
    # orphans -> constraint-unique completion against the schedule-size templates
    taken = sorted({bound[k]["bounds"] for k in bound})
    tagpts = [(m["x"], m["y"]) for m in marks]
    comp = SQ.complete_by_count({t: [dict(o) for o in v] for t, v in orphans.items()}, templates_by_type,
                                taken=taken, carriers=carriers, tags=tagpts) if orphans else {}
    for t, v in orphans.items():
        res = comp.get(t, {})
        for o in v:
            if res.get("state") == SQ.COUNT_UNIQUE and res.get("unmatched_after_containment") == len(v):
                rows[o["key"]] = dict(_base(o, library), geometry_state=COUNT_UNIQUE,
                                      geometry={"free_outlines": [x["bounds"] for x in res["outlines"]],
                                                "orphans_of_type": len(v)},
                                      why=f"{len(v)} unbound mark(s), {len(res['outlines'])} free disjoint outline(s) "
                                          "of the scheduled size carrying a column")
            else:
                rows[o["key"]] = dict(_base(o, library), geometry_state=UNBOUND,
                                      geometry={"completion": res.get("state"), "free": res.get("free_candidates")},
                                      why=f"no outline contains the mark; completion {res.get('state')} "
                                          f"({len(v)} unbound, {res.get('free_candidates')} free)")
    for k, ov in overrides.items():
        if k in rows:
            rows[k] = dict(rows[k], geometry_state=OVERRIDE, override=ov, why="explicit local dimension bound to it")
    return {"rows": [_quantify(rows[k], library) for k in sorted(rows)], "completion": comp,
            "bindings": {k: bound[k]["id"] for k in sorted(bound)}}


def _base(m, library):
    ft = library.get(m["type"])
    return {"type": m["type"], "mark_key": m["key"], "mark_value": m["value"],
            "mark_xy": [round(m["x"], 3), round(m["y"], 3)],
            "schedule_row": None if ft is None else {"type": m["type"], "keys": ft.get("keys", []), "L_cm": ft["L_cm"],
                                                      "W_cm": ft["W_cm"], "H_cm": ft["H_cm"]}}


def _quantify(r, library):
    ft = library.get(r["type"])
    st = r["geometry_state"]
    src = f"SCHEDULE OF FOOTINGS (cm) row {r['type']}"
    if ft is not None and None not in (ft.get("L_cm"), ft.get("W_cm"), ft.get("H_cm")):
        dims = {"L": {"m": ft["L_cm"] / 100.0, "source": src}, "W": {"m": ft["W_cm"] / 100.0, "source": src},
                "H": {"m": ft["H_cm"] / 100.0, "source": src}}
        if st == OVERRIDE:
            ov = r["override"]
            dims = {k: {"m": ov[k + "_m"], "source": ov["source"]} for k in ("L", "W", "H")}
        each = round(dims["L"]["m"] * dims["W"]["m"] * dims["H"]["m"], 6)
    else:
        dims, each = None, None
    computed = st in COMPUTED_STATES
    return dict(r, dims=dims, formula="1 x L x W x H", schedule_value_m3=each,
                qty=each if computed else None, unit="m3", status=COMPLETE if computed else BLOCKED,
                blockers=[] if computed else [f"{st}: {r.get('why', '')}"])


def type_summary(rows, library) -> list:
    by = defaultdict(list)
    for r in rows:
        by[r["type"]].append(r)
    out = []
    for t in sorted(set(library) | set(by), key=_type_key):
        rs, ft = by.get(t, []), library.get(t)
        comp = [r for r in rs if r["status"] == COMPLETE]
        each = None if ft is None or None in (ft.get("L_cm"), ft.get("W_cm"), ft.get("H_cm")) else \
            round(ft["L_cm"] * ft["W_cm"] * ft["H_cm"] / 1e6, 6)
        out.append({"type": t, "count_tagged": len(rs),
                    "count_geometry_confirmed": sum(r["geometry_state"] == CONFIRMED for r in rs),
                    "count_partial_geometry": sum(r["geometry_state"] in PARTIAL_STATES for r in rs),
                    "count_override": sum(r["geometry_state"] == OVERRIDE for r in rs),
                    "count_conflict": sum(r["geometry_state"] in CONFLICT_STATES for r in rs),
                    "count_blocked_other": sum(r["status"] == BLOCKED and r["geometry_state"] not in CONFLICT_STATES
                                               for r in rs),
                    "count_computed": len(comp),
                    **{k + "_m": (None if ft is None or ft.get(k + "_cm") is None else ft[k + "_cm"] / 100.0)
                       for k in ("L", "W", "H")},
                    "m3_each": each, "m3_total_computed": round(sum(r["qty"] for r in comp), 6),
                    "tag_keys": [r["mark_key"] for r in rs],
                    "status": ("NOT_TAGGED_ON_PLAN" if not rs else COMPLETE if len(comp) == len(rs) else
                               "PARTIAL" if comp else BLOCKED)})
    return out


def _type_key(t):
    m = re.match(r"^([A-Z.]*?)(\d*)$", t)
    return (m.group(1), int(m.group(2)) if m and m.group(2) else -1, t) if m else (t, 0, t)


def reconcile(marks, rows, library) -> dict:
    keys = Counter(r["mark_key"] for r in rows)
    per = {}
    for t in sorted({m["type"] for m in marks}, key=_type_key):
        n = sum(m["type"] == t for m in marks)
        c = sum(r["type"] == t and r["status"] == COMPLETE for r in rows)
        b = sum(r["type"] == t and r["status"] == BLOCKED for r in rows)
        per[t] = {"tags": n, "computed": c, "blocked": b, "state": "PASS" if n == c + b else "FAIL"}
    lost = sorted(m["key"] for m in marks if keys.get(m["key"]) != 1)
    unsched = sorted({r["type"] for r in rows if r["status"] == COMPLETE and r["type"] not in library})
    ok = all(v["state"] == "PASS" for v in per.values()) and not lost and not unsched
    return {"state": "PASS" if ok else "FAIL", "per_type": per, "tags_not_exactly_once": lost,
            "computed_types_not_in_schedule": unsched, "tags": len(marks), "rows": len(rows)}


# ------------------------------------------------------------------ columns
SIZE_LABEL = re.compile(r"^\s*(\d{1,3})\s*[Xx×]\s*(\d{1,3})\s*$")


def column_storeys(library, marks, *, size_labels=(), per_sheet_outlines=None) -> dict:
    """library {type: {band: {"B_cm", "D_cm", "reinf"}}} (bands in schedule order); marks [{"type", "key"}] from the
    column plan; size_labels [text values like '30X50'] printed on the column plan; per_sheet_outlines
    {band: [(a_mm, b_mm)]} column rectangles drawn on the sheet that shows that storey (corroboration only)."""
    cnt = Counter(m["type"] for m in marks)
    bands = []
    for t in library.values():
        for b in t:
            if b not in bands:
                bands.append(b)
    storeys = {}
    for b in bands:
        rows = []
        for t in sorted(library, key=_type_key):
            sec = library[t].get(b) or {}
            n = cnt.get(t, 0)
            ok = sec.get("B_cm") is not None and sec.get("D_cm") is not None
            rows.append({"type": t, "count": n, "B_cm": sec.get("B_cm"), "D_cm": sec.get("D_cm"),
                         "reinf": sec.get("reinf"),
                         "plan_area_each_m2": round(sec["B_cm"] * sec["D_cm"] / 1e4, 6) if ok else None,
                         "plan_area_total_m2": round(n * sec["B_cm"] * sec["D_cm"] / 1e4, 6) if ok else None,
                         "status": (COMPLETE if ok else "SECTION_NOT_SCHEDULED_FOR_STOREY") if n else "NOT_TAGGED"})
        expected = Counter()
        for r in rows:
            if r["plan_area_each_m2"] is not None and r["count"]:
                expected[tuple(sorted((r["B_cm"], r["D_cm"])))] += r["count"]
        corr = None
        if per_sheet_outlines and b in per_sheet_outlines:
            drawn = Counter(tuple(sorted((round(a / 10), round(c / 10)))) for a, c in per_sheet_outlines[b])
            corr = {"drawn": {f"{k[0]}x{k[1]}": v for k, v in sorted(drawn.items())},
                    "expected_from_marks": {f"{k[0]}x{k[1]}": v for k, v in sorted(expected.items())},
                    "drawn_count": sum(drawn.values()), "expected_count": sum(expected.values()),
                    "state": "AGREES" if drawn == expected else "DIFFERS"}
        storeys[b] = {"rows": rows, "columns_with_section": sum(r["count"] for r in rows if r["plan_area_each_m2"] is not None),
                      "plan_area_m2": round(sum(r["plan_area_total_m2"] or 0.0 for r in rows), 6),
                      "corroboration": corr}
    labels = Counter()
    for v in size_labels:
        m = SIZE_LABEL.match(str(v))
        if m:
            labels[tuple(sorted((int(m.group(1)), int(m.group(2)))))] += 1
    lab = None
    if labels:
        cmp = {}
        for b in bands:
            exp = Counter()
            for t, n in cnt.items():
                sec = (library.get(t) or {}).get(b) or {}
                if sec.get("B_cm") is not None and sec.get("D_cm") is not None:
                    exp[tuple(sorted((sec["B_cm"], sec["D_cm"])))] += n
            diff = {f"{k[0]}x{k[1]}": labels.get(k, 0) - exp.get(k, 0) for k in sorted(set(labels) | set(exp))
                    if labels.get(k, 0) != exp.get(k, 0)}
            cmp[b] = {"deviation_count": sum(v for v in diff.values() if v > 0), "differences": diff}
        best = min(cmp, key=lambda b: (cmp[b]["deviation_count"], bands.index(b)))
        lab = {"printed": {f"{k[0]}x{k[1]}": v for k, v in sorted(labels.items())}, "printed_count": sum(labels.values()),
               "by_band": cmp, "closest_band": best,
               "use": "aggregate check only: a printed size overrides nothing unless bound to one occurrence"}
    return {"marks": dict(sorted(cnt.items(), key=lambda kv: _type_key(kv[0]))), "mark_count": sum(cnt.values()),
            "bands": bands, "storeys": storeys, "printed_size_labels": lab}


# ------------------------------------------------------------------ beams / straps
def beam_bands(marks, library, lines, *, umm, tol_mm, eps, supports=()) -> list:
    """marks [{"key", "value", "type", "x", "y"}]; library {type: {"B_cm", "D_cm"}}; lines [(key, x1, y1, x2, y2)]
    element lines that may be beam edges; supports: candidate outlines (polygons) the clear length stops at.
    -> one record per mark: state MEASURED / NO_BAND / AMBIGUOUS_BAND / SECTION_NOT_SCHEDULED."""
    out = []
    for m in sorted(marks, key=lambda z: z["key"]):
        sec = library.get(m["type"])
        rec = {"type": m["type"], "mark_key": m["key"], "mark_value": m["value"], "mark_xy": [round(m["x"], 3), round(m["y"], 3)],
               "B_cm": sec and sec.get("B_cm"), "D_cm": sec and sec.get("D_cm")}
        if not sec or sec.get("B_cm") is None or sec.get("D_cm") is None:
            out.append(dict(rec, state="SECTION_NOT_SCHEDULED", length_m=None, volume_m3=None))
            continue
        width = sec["B_cm"] * 10.0 / umm
        found = []
        for i, a in enumerate(lines):
            for b in lines[i + 1:]:
                pair = _band(a, b, m["x"], m["y"], width, tol_mm / umm, eps)
                if pair:
                    found.append(pair)
        uniq = {(round(p["t0"], 3), round(p["t1"], 3), round(p["offset"], 3)): p for p in found}
        found = list(uniq.values())
        deviation = None
        if not found:
            wide = []
            for i, a in enumerate(lines):
                for b in lines[i + 1:]:
                    pair = _band(a, b, m["x"], m["y"], width, BAND_WIDTH_DEVIATION_MAX * width, eps)
                    if pair:
                        wide.append(pair)
            wide = list({(round(p["t0"], 3), round(p["t1"], 3), round(p["offset"], 3)): p for p in wide}.values())
            if len(wide) == 1:
                found = wide
                deviation = round(abs(wide[0]["offset"]) * umm - sec["B_cm"] * 10.0, 1)
        if not found:
            seps = set()                                   # diagnostic only: pairs the mark lies between at any width
            for i, a in enumerate(lines):
                for b in lines[i + 1:]:
                    p = _band(a, b, m["x"], m["y"], None, None, eps)
                    if p and abs(p["offset"]) * umm <= 3 * sec["B_cm"] * 10.0:
                        seps.add(round(abs(p["offset"]) * umm, 1))
            out.append(dict(rec, state="NO_BAND_HOLDS_THE_MARK", length_m=None, volume_m3=None,
                            pairs_between_mm=sorted(seps), scheduled_breadth_mm=sec["B_cm"] * 10.0,
                            tolerance_mm=tol_mm))
            continue
        if len(found) > 1:
            out.append(dict(rec, state="AMBIGUOUS_BAND", candidates=len(found), length_m=None, volume_m3=None))
            continue
        p = found[0]
        clear = _clear_span(p, supports, eps)
        if clear is None:
            out.append(dict(rec, state="SPAN_ENDS_NOT_AT_SUPPORTS", band=p["keys"], length_m=None, volume_m3=None))
            continue
        L = clear["length"] * umm / 1000.0
        out.append(dict(rec, state="MEASURED" if deviation is None else "MEASURED_WITH_WIDTH_DEVIATION",
                        width_deviation_mm=deviation, drawn_width_mm=round(abs(p["offset"]) * umm, 1),
                        band=p["keys"], span_native=[round(p["t0"], 3), round(p["t1"], 3)],
                        clear=clear["cut_by"], length_m=round(L, 6),
                        volume_m3=round(L * sec["B_cm"] / 100.0 * sec["D_cm"] / 100.0, 6),
                        formula="clear length x B x D"))
    return out


def _band(a, b, x, y, width, tol, eps):
    (ka, ax1, ay1, ax2, ay2), (kb, bx1, by1, bx2, by2) = a, b
    La, Lb = math.hypot(ax2 - ax1, ay2 - ay1), math.hypot(bx2 - bx1, by2 - by1)
    if La <= eps or Lb <= eps:
        return None
    u = ((ax2 - ax1) / La, (ay2 - ay1) / La)
    if abs(u[0] * (by2 - by1) / Lb - u[1] * (bx2 - bx1) / Lb) > 1e-3:          # not parallel
        return None
    n = (-u[1], u[0])
    off = lambda px, py: (px - ax1) * n[0] + (py - ay1) * n[1]
    t = lambda px, py: (px - ax1) * u[0] + (py - ay1) * u[1]
    ob = off(bx1, by1)
    if abs(off(bx2, by2) - ob) > max(eps, 1e-9) * 4 and width is not None:
        return None                                                             # not a constant offset
    if width is not None and abs(abs(ob) - width) > tol:
        return None
    if abs(ob) <= eps:
        return None
    om = off(x, y)
    if not (min(0.0, ob) < om < max(0.0, ob)):                                  # mark strictly between the lines
        return None
    s0, s1 = sorted((t(bx1, by1), t(bx2, by2)))
    t0, t1 = max(0.0, s0), min(La, s1)
    tm = t(x, y)
    if not (t0 < tm < t1):
        return None
    return {"keys": sorted([ka, kb]), "t0": t0, "t1": t1, "offset": ob, "origin": (ax1, ay1), "u": u, "n": n,
            "mid_offset": ob / 2.0, "mark_t": tm}


def _clear_span(p, supports, eps):
    """The pair's common span, cut back at the first support outline met on each side of the mark along the band
    centre line. Both ends must stop inside a support (an unsupported free end is not a measured span)."""
    ox, oy = p["origin"]
    u, n, mo = p["u"], p["n"], p["mid_offset"]
    at = lambda t: (ox + u[0] * t + n[0] * mo, oy + u[1] * t + n[1] * mo)
    steps = max(int((p["t1"] - p["t0"]) / max(eps, 1e-6)), 1)
    step = (p["t1"] - p["t0"]) / min(steps, 20000)
    cut = {}
    for side, rng in (("lo", -1), ("hi", 1)):
        t = p["mark_t"]
        hit = None
        while p["t0"] <= t <= p["t1"]:
            x, y = at(t)
            s = next((c for c in supports if contains(c, x, y)), None)
            if s is not None:
                hit = (t, s["id"])
                break
            t += rng * step
        if hit is None:
            return None
        cut[side] = hit
    if any(contains(c, *at(p["mark_t"])) for c in supports):
        return None
    return {"length": cut["hi"][0] - cut["lo"][0], "cut_by": [cut["lo"][1], cut["hi"][1]]}


# ------------------------------------------------------------------ rebar definitions
BAR = re.compile(r"(\d+)\s*[ØO%cC]+\s*(\d+)(\s*/\s*m)?", re.I)


def bar_spec(text) -> list:
    """'8 Ø 12' -> [{"count": 8, "dia_mm": 12, "per_m": False}]; '6 Ø 14/m' -> per_m True. Unreadable -> []."""
    out = []
    for m in BAR.finditer(str(text or "").replace("%%c", "Ø").replace("%%C", "Ø")):
        out.append({"count": int(m.group(1)), "dia_mm": int(m.group(2)), "per_m": bool(m.group(3))})
    return out


def rebar_definitions(rows) -> list:
    """rows [{"element", "type", "fields": {name: text}}] -> definition records; the weight is BLOCKED unless the
    source states cutting length, cover, hooks and laps (it never does here) - no ratio is ever used."""
    out = []
    for r in rows:
        bad = sorted(k for k in r.get("fields", {}) if k in FORBIDDEN_REBAR_KEYS)
        if bad:
            raise ValueError(f"rebar from a ratio is refused: {bad}")
        defs = {k: bar_spec(v) for k, v in sorted(r.get("fields", {}).items())}
        readable = {k: v for k, v in defs.items() if v}
        out.append({"element": r["element"], "type": r["type"], "fields": r.get("fields", {}), "bars": readable,
                    "definition": COMPLETE if readable else BLOCKED,
                    "weight_kg": None, "weight_state": "BLOCKED",
                    "weight_missing": ["cutting length", "cover", "hooks / bends", "laps / anchorage"],
                    "never": "kg/m3"})
    return out


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID,
           "authority": {"type_identity": "plan mark (exact schedule token)", "nominal_size": "admitted schedule row",
                         "geometry": "validation: confirmed / interrupted / count-unique / conflict",
                         "override": "explicit local dimension bound to the occurrence only"},
           "computed_states": list(COMPUTED_STATES), "blocked_states": [COMBINED, DRAWN_SIZE, UNBOUND, NOT_SCHEDULED],
           "band_width_deviation_max": BAND_WIDTH_DEVIATION_MAX,
           "never": ["nearest-distance association", "a matcher-assembled outline as authority",
                     "a type total written by hand", "a kg/m3 ratio", "an architectural height as a column height"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
