"""OPENING AREA (T-078): door and window areas in m2 from the plan width and a PRINTED height. Method piece, NOT wired
into a released method: arch_measure.py, door_model.py, arch_v28.py and every frozen method are untouched; no released
line or quantity changes.

Why (T-040, research/agents_t040): ARCH_TAKEOFF_V2.9 emits doors and windows as pieces only. Their heights are printed,
when at all, as vertical dimension chains on elevation views, which the engine reads only for level texts (L-P9-02).
This piece binds each plan opening to its drawn elevation opening and reads the printed chain:

    measure(plan_openings, views, *, floors, curved_width_basis=None) -> {"records", "views", "summary", "policy"}

    plan_openings  every opening of the plan run, one dict each:
                   {"id", "floor", "kind" (WINDOW / DOOR / PASSAGE), "xy" (m, the opening centre in ONE plan frame
                   for all floors: the run's own cross-floor registration applied), "axis" (unit vector along the wall),
                   "width_m" (plan jamb to jamb), optional "faces_outside" (False when the run finds a space on
                   both sides: never looked up on an elevation), "curved": {"chord_m", "bases_m": {basis: m}},
                   "door_class" (the run's door class), "schedule_height_m" + "schedule_source" (an opening or door
                   schedule row bound by the run), "material_drawn" (a material the drawing writes for it)}
    views          elevation views of the drawing (read_view builds one from a DXF):
                   {"view_id", "unit_m" (metres per drawing unit), "header_dimlfac", "dims" (records in the
                   tools/arch_dimensions.py format), "segments" [(x1, y1, x2, y2, source_id)]}
    floors         floor names bottom to top (stack order)
    curved_width_basis  the owner's basis for the width of a curved-on-plan opening (a key of "bases_m", or "CHORD");
                   None -> such an opening's area is HELD CURVED_WIDTH_BASIS (both candidates reported)

Steps, each one evidence, never a guess:
1. Printed value of a dimension: the number the drawing shows (text override or rendered text) through its effective
   DIMLFAC (dimension_evidence.resolve). It is used only when it equals the defpoint geometry within half a unit of
   its last printed digit (a rounded print, e.g. "269" for 2691.5 mm); otherwise it is STALE and never used.
2. View mapping: an elevation's horizontal axis is a plan axis a, seen straight (s = +1) or mirrored (s = -1):
   x_view = s * (xy . a) + c. (a, s, c) is accepted only when at least TWO printed width dimensions at different
   places match plan openings of that axis by width (UP-OPEN-SCHED-001: within 0.03 m) AND position (within 0.03 m),
   and no other (a, s, c) has as much support. One matched width proves nothing about position: no mapping.
3. Drawn opening: at the projected range [x - w/2, x + w/2] two vertical jamb lines (one at each end, within 0.03 m)
   with the same foot. Pairs that enclose another pair (a surround drawn over several storeys) are not openings.
4. Printed height: a vertical dimension whose two witness origins lie inside the range and whose low witness is the
   jamb foot. RECTANGULAR when its high witness is the jamb top (within 0.03 m). ARCHED when the jambs stop below the
   head and curved lines rise above them inside the range: the height then runs to the TOP OF THE ARCH (owner Q-32 =
   A, the enclosing rectangle), read only as consecutive printed dimensions of the same range from the foot to a
   witness at the highest curved point; the arch top not printed -> HELD ARCH_TOP_NOT_PRINTED.
5. Stack: the drawn openings at one range are given to the plan openings projecting onto that range, floor by floor
   bottom to top, only when both counts agree and no floor has two of them (the front and the back face project
   alike); otherwise HELD STACK_NOT_BOUND.
6. Height order (UP-DOOR-HGT-001 order 1.4.0, UP-OPEN-SCHED-001): a bound schedule height first, then the elevation;
   both present and different -> the schedule governs, a review finding is kept.
7. Area = width x height (UP-DOOR-AREA-001 AS_DRAWN for doors: the drawn wall opening; the owner-standard view stays
   with door_standards.door_scenarios and is never added here). Width = the plan width; a printed elevation width at
   the same place that differs by more than 0.03 m -> HELD WIDTH_CONFLICT.

Status (UP-QTY-STATUS-001; every opening reported once, never dropped, never 0):
  MEASURED   width and height both from the drawing; area released by this piece (not wired)
  HELD       no area, with the reason and every candidate value found (never a default height, never a benchmark)
  EXCLUDED   a passage / archway: no door or window to supply (EXCLUDED_WITH_REASON)
  UNSUPPORTED  an opening kind or geometry this piece does not read (with the reason)
Material (owner Q-33 = A, 2026-10-19): a window is ALUMINIUM unless the drawing writes another material; a door
keeps the run's door class (UP-DOOR-CLS-002: an outdoor door is aluminium).

Project-agnostic: no layer, block, title or project name is coded. Stdlib only, except read_view (ezdxf, lazy).
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from engine.source import dimension_evidence as DE

POLICY_ID = "OPENING_AREA_V1"
TOL_M = 0.03                 # UP-OPEN-SCHED-001: a width agrees within 0.03 m; used for every place / level match
AXIS_DEG = 1.0               # two wall axes are one axis within this
MEASURED, HELD, EXCLUDED, UNSUPPORTED = "MEASURED", "HELD", "EXCLUDED", "UNSUPPORTED"
RULES = ("UP-OPEN-SCHED-001", "UP-DOOR-AREA-001", "UP-DOOR-HGT-001", "UP-QTY-STATUS-001", "OWNER-Q32-A",
         "OWNER-Q33-A")
HOLD_ORDER = ("HEIGHT_CONFLICT", "WIDTH_CONFLICT", "ARCH_TOP_NOT_PRINTED", "HEAD_ABOVE_JAMBS_NO_ARCH",
              "NO_PRINTED_HEIGHT", "STACK_NOT_BOUND", "NOT_DRAWN_ON_THIS_ELEVATION")
NUM = re.compile(r"[-+]?\d+(?:[.,]\d+)?")


# ----------------------------------------------------------------------------------------------- printed values
def printed(rec, header_dimlfac, unit_m):
    """One dimension record -> {"handle", "p2", "p3", "dir", "value_m", "usable", "why_not"}; value_m is the printed
    number in metres, used only when it is the defpoint geometry rounded to its own last digit."""
    r = DE.resolve(rec, header_dimlfac, unit_m)
    out = {"handle": rec.get("handle"), "p2": rec.get("p2"), "p3": rec.get("p3"), "dir": r.get("dir"),
           "value_m": None, "usable": False, "why_not": r.get("why_not"), "shown": r.get("shown_value")}
    if r.get("why_not") in ("NOT_LINEAR", "NO_SHOWN_VALUE") or r.get("shown_value") is None:
        return out
    txt = rec.get("text") if rec.get("text") not in (None, "", "<>") else rec.get("shown_text")
    m = NUM.search((txt or "").replace("\\P", " "))
    decimals = len(m.group(0).replace(",", ".").split(".")[1]) if m and "." in m.group(0).replace(",", ".") else 0
    half_du = 0.5 * (10.0 ** -decimals) / r["dimlfac"]                   # half a printed unit, in drawing units
    if abs(r["value_du"] - r["geometry_du"]) > max(half_du, 0.0005 / unit_m) + 1e-9:
        out["why_not"] = "STALE_OR_OVERRIDDEN (printed %s vs defpoints %.1f du)" % (r["shown_value"], r["geometry_du"])
        return out
    out.update(value_m=r["value_du"] * unit_m, usable=True, why_not=None)
    return out


def _split(dims):
    """usable printed dimensions -> horizontal (widths) and vertical (heights), in drawing units."""
    hor, ver = [], []
    for d in dims:
        if not d["usable"] or not d["dir"]:
            continue
        ux, uy = d["dir"]
        (x2, y2), (x3, y3) = d["p2"], d["p3"]
        if abs(ux) >= math.cos(math.radians(AXIS_DEG)):
            hor.append({**d, "x0": min(x2, x3), "x1": max(x2, x3), "xc": (x2 + x3) / 2.0})
        elif abs(uy) >= math.cos(math.radians(AXIS_DEG)):
            lo, hi = sorted(((y2, x2), (y3, x3)))
            ver.append({**d, "low": lo[0], "high": hi[0], "xs": (lo[1], hi[1])})
    return hor, ver


# ------------------------------------------------------------------------------------------------- the mapping
def _axes(plan_openings):
    axes = []
    for p in plan_openings:
        a = p.get("axis")
        if not a:
            continue
        n = math.hypot(*a) or 1.0
        a = (a[0] / n, a[1] / n)
        if a[0] < -1e-12 or (abs(a[0]) <= 1e-12 and a[1] < 0):
            a = (-a[0], -a[1])
        if not any(abs(a[0] * b[0] + a[1] * b[1]) >= math.cos(math.radians(AXIS_DEG)) for b in axes):
            axes.append(a)
    return axes


def _parallel(p, a):
    v = p.get("axis")
    if not v:
        return False
    n = math.hypot(*v) or 1.0
    return abs(v[0] * a[0] + v[1] * a[1]) / n >= math.cos(math.radians(AXIS_DEG))


def plan_width(p):
    """The width the elevation shows: the plan width, or the chord of an opening curved on plan."""
    if p.get("curved"):
        return (p["curved"] or {}).get("chord_m")
    return p.get("width_m")


def view_mapping(view, plan_openings):
    """(axis, s, c) of one elevation from printed widths matched by width and position; or the reason it has none."""
    u = view["unit_m"]
    hor, _ = _split(view["printed"])
    best, cands = None, []
    for a in _axes(plan_openings):
        for s in (1, -1):
            pairs = []
            for e in hor:
                for p in plan_openings:
                    w = plan_width(p)
                    if w is None or not _parallel(p, a) or abs(e["value_m"] - w) > TOL_M:
                        continue
                    pos = p["xy"][0] * a[0] + p["xy"][1] * a[1]
                    pairs.append((e["xc"] * u - s * pos, e, p))
            pairs.sort(key=lambda t: t[0])
            for c0, _, _ in pairs:
                grp = [t for t in pairs if abs(t[0] - c0) <= TOL_M]
                places = {round(t[1]["xc"] * u / TOL_M) for t in grp}
                dims = {t[1]["handle"] for t in grp}
                cands.append((len(places), len(dims), a, s, sum(t[0] for t in grp) / len(grp), grp))
    if not cands:
        return {"state": "NO_MAPPING", "why": "no printed width matches a plan opening by width"}
    cands.sort(key=lambda t: (-t[0], -t[1]))
    top = cands[0]
    if top[0] < 2:
        return {"state": "NO_MAPPING", "why": "fewer than two printed widths at different places match plan openings "
                                              "by width and position (one match proves no position)"}
    rivals = [t for t in cands[1:] if t[0] == top[0] and (t[2] != top[2] or t[3] != top[3]
                                                          or abs(t[4] - top[4]) > TOL_M)]
    if rivals:
        return {"state": "AMBIGUOUS_MAPPING", "why": "two mappings have the same support", "support": top[0]}
    return {"state": "MAPPED", "axis": [round(top[2][0], 6), round(top[2][1], 6)], "mirrored": top[3] == -1,
            "s": top[3], "c_m": round(top[4], 4), "support_places": top[0],
            "matches": sorted({(t[1]["handle"], t[2]["id"], t[2]["floor"]) for t in top[5]})}


# --------------------------------------------------------------------------------------- drawn openings, heights
def _verticals(view):
    """vertical lines of the view; collinear pieces that meet end to end (a jamb drawn in pieces, an arc flattened
    into short near-vertical chords at its springing) are joined into one line first. Overlapping collinear lines
    (a surround over a jamb) stay apart."""
    u = view["unit_m"]
    raw = sorted((((x1 + x2) / 2.0, min(y1, y2), max(y1, y2), sid) for (x1, y1, x2, y2, sid) in view["segments"]
                  if abs(x1 - x2) * u <= 0.002 and abs(y1 - y2) > 0), key=lambda r: (round(r[0] * u / 0.002), r[1]))
    out = []
    for x, lo, hi, sid in raw:
        same = [v for v in out if abs(v["x"] - x) * u <= 0.002 and abs(lo - v["top"]) * u <= 0.002]
        if same:
            v = same[0]
            v["foot"], v["top"] = min(v["foot"], lo), max(v["top"], hi)
            v["pieces"].append(sid)
        else:
            out.append({"x": x, "foot": lo, "top": hi, "id": sid, "pieces": [sid]})
    return [v for v in out if (v["top"] - v["foot"]) * u > TOL_M]


def _curved(view):
    u = view["unit_m"]
    return [s for s in view["segments"] if abs(s[0] - s[2]) * u > 0.002 and abs(s[1] - s[3]) * u > 0.002]


def drawn_openings(view, x0, x1):
    """jamb pairs at [x0, x1] (drawing units) -> [{"foot", "top", "jambs"}], innermost only, bottom to top."""
    t = TOL_M / view["unit_m"]
    vs = view.get("_verticals") or _verticals(view)
    left = [v for v in vs if abs(v["x"] - x0) <= t]
    right = [v for v in vs if abs(v["x"] - x1) <= t]
    pairs = []
    for L in left:
        for R in right:
            if abs(L["foot"] - R["foot"]) <= t:
                pairs.append({"foot": (L["foot"] + R["foot"]) / 2.0, "top": min(L["top"], R["top"]),
                              "jambs": [L["id"], R["id"]]})
    uniq = []
    for p in sorted(pairs, key=lambda q: (q["foot"], q["top"])):
        same = next((q for q in uniq if abs(q["foot"] - p["foot"]) <= t and abs(q["top"] - p["top"]) <= t), None)
        if same:
            same["jambs"] = sorted(set(same["jambs"]) | set(p["jambs"]))
        else:
            uniq.append(dict(p))
    inner = [p for p in uniq if not any(q is not p and q["foot"] >= p["foot"] - t and q["top"] <= p["top"] + t
                                        and (q["top"] - q["foot"]) < (p["top"] - p["foot"]) - t for q in uniq)]
    return inner


def printed_height(view, x0, x1, opening):
    """The printed height of one drawn opening -> {"state": "PRINTED", "height_m", "shape", "dims"} or a hold."""
    u = view["unit_m"]
    t = TOL_M / u
    _, ver = _split(view["printed"])
    mine = [d for d in ver if all(x0 - t <= x <= x1 + t for x in d["xs"])]
    foot, top = opening["foot"], opening["top"]
    rect = [d for d in mine if abs(d["low"] - foot) <= t and abs(d["high"] - top) <= t]
    vals = sorted({round(d["value_m"], 4) for d in rect})
    if len(vals) > 1:
        return {"state": "HEIGHT_CONFLICT", "values_m": vals, "dims": [d["handle"] for d in rect]}
    w = x1 - x0
    arcs = [s for s in _curved(view) if all(x0 - t <= x <= x1 + t for x in (s[0], s[2]))
            and all(top - t <= y <= top + w for y in (s[1], s[3]))]
    apex = max((max(s[1], s[3]) for s in arcs), default=None)
    if rect:
        springs = any(min(s[1], s[3]) <= top + t for s in arcs)          # a curve that starts at the jamb tops
        if not (springs and apex is not None and apex > top + t):
            out = {"state": "PRINTED", "height_m": vals[0], "shape": "RECTANGULAR", "dims": [rect[0]["handle"]]}
            if arcs:
                out["note"] = "curved lines above the head do not start at the jamb tops: not this opening's arch"
            return out
        starts = rect                                                       # an arch over a printed springing
    else:
        starts = [d for d in mine if abs(d["low"] - foot) <= t and d["high"] > top + t]
        if not starts:
            cand = sorted({round(d["value_m"], 4) for d in mine if abs(d["low"] - foot) <= t})
            return {"state": "NO_PRINTED_HEIGHT", "why": "no printed vertical dimension from the jamb foot inside "
                                                        "the opening's range", "candidates_m": cand}
        if apex is None or apex <= top + t:
            return {"state": "HEAD_ABOVE_JAMBS_NO_ARCH", "why": "the printed head is above the jamb tops and no "
                                                               "curved line is drawn there",
                    "dims": [d["handle"] for d in starts]}
    paths = [[d] for d in starts]
    for _ in range(12):
        nxt = []
        for path in paths:
            h = path[-1]["high"]
            if abs(h - apex) <= t:
                return {"state": "PRINTED", "shape": "ARCHED", "height_m": round(sum(d["value_m"] for d in path), 4),
                        "dims": [d["handle"] for d in path], "parts_m": [round(d["value_m"], 4) for d in path],
                        "rule": "OWNER-Q32-A: to the top of the arch (enclosing rectangle)"}
            if h > apex + t:
                continue
            nxt += [path + [d] for d in mine if abs(d["low"] - h) <= t and d["high"] > h + t]
        paths = nxt
        if not paths:
            break
    return {"state": "ARCH_TOP_NOT_PRINTED", "why": "no chain of printed dimensions inside the opening reaches the "
                                                   "top of the drawn arch", "arch_top_above_foot_m":
            round((apex - foot) * u, 4), "dims_from_foot": [(d["handle"], round(d["value_m"], 4)) for d in starts]}


# ------------------------------------------------------------------------------------------------------ measure
def _material(p):
    if p["kind"] == "WINDOW":
        if p.get("material_drawn"):
            return {"material": p["material_drawn"], "source": "DRAWING"}
        return {"material": "ALUMINIUM", "source": "OWNER-Q33-A (a window is aluminium unless the drawing says "
                                                   "otherwise)"}
    cls = p.get("door_class")
    if cls is None:
        return {"material": None, "source": "door class not established by the run"}
    mat = "ALUMINIUM" if "ALUMINIUM" in str(cls).upper() else "PVC" if "PVC" in str(cls).upper() else None
    return {"material": mat, "source": f"run door class {cls} (UP-DOOR-CLS-002)"}


def _held(p, reason, **ev):
    return {"id": p["id"], "floor": p["floor"], "kind": p["kind"], "status": HELD, "reason": reason,
            "width_m": p.get("width_m"), "height_m": None, "area_m2": None, "evidence": ev, **_material(p)}


def measure(plan_openings, views, *, floors, curved_width_basis=None):
    fidx = {f: i for i, f in enumerate(floors)}
    vout = []
    for v in views:
        v = dict(v)
        v["printed"] = [printed(d, v.get("header_dimlfac"), v["unit_m"]) for d in v.get("dims") or ()]
        v["_verticals"] = _verticals(v)
        v["mapping"] = view_mapping(v, plan_openings)
        vout.append(v)
    # every elevation the opening can be read on: (view, x0, x1) in drawing units
    found = defaultdict(list)          # opening id -> [(view, x0, x1)]
    for v in vout:
        m = v["mapping"]
        if m["state"] != "MAPPED":
            continue
        a, s, c, u = m["axis"], m["s"], m["c_m"], v["unit_m"]
        for p in plan_openings:
            w = plan_width(p)
            if w is None or not _parallel(p, a) or p["kind"] not in ("WINDOW", "DOOR") or p.get("xy") is None:
                continue
            if p.get("faces_outside") is False:
                continue
            xm = s * (p["xy"][0] * a[0] + p["xy"][1] * a[1]) + c
            found[p["id"], p["floor"]].append((v, (xm - w / 2.0) / u, (xm + w / 2.0) / u))
    records = []
    for p in plan_openings:
        key = (p["id"], p["floor"])
        if p["kind"] == "PASSAGE":
            records.append({"id": p["id"], "floor": p["floor"], "kind": p["kind"], "status": EXCLUDED,
                            "reason": "PASSAGE_NO_DOOR_OR_WINDOW", "width_m": p.get("width_m"), "height_m": None,
                            "area_m2": None, "evidence": {}, "material": None, "source": None})
            continue
        if p["kind"] not in ("WINDOW", "DOOR"):
            records.append({**_held(p, "UNSUPPORTED_KIND"), "status": UNSUPPORTED})
            continue
        if p.get("width_m") is None:
            records.append(_held(p, "WIDTH_MISSING"))
            continue
        cand = []                                   # (source, height_m, evidence)
        notes = {}
        for v, x0, x1 in found.get(key, ()):
            t = TOL_M / v["unit_m"]
            peers = [q for q in plan_openings if any(vv is v and abs(qx0 - x0) <= t and abs(qx1 - x1) <= t
                                                     for vv, qx0, qx1 in found.get((q["id"], q["floor"]), ()))]
            per_floor = Counter(q["floor"] for q in peers)
            ops = drawn_openings(v, x0, x1)
            hor, _ = _split(v["printed"])
            wd = [e for e in hor if abs(e["x0"] - x0) <= t and abs(e["x1"] - x1) <= t]
            if any(abs(e["value_m"] - plan_width(p)) > TOL_M for e in wd):
                notes[v["view_id"]] = {"state": "WIDTH_CONFLICT", "printed_m": [round(e["value_m"], 4) for e in wd]}
                continue
            if not ops:
                notes[v["view_id"]] = {"state": "NOT_DRAWN_ON_THIS_ELEVATION", "why": "no jamb pair at the projected "
                                       "range (an inner or hidden opening, or a facade drawn without it)"}
                continue
            if any(n > 1 for n in per_floor.values()) or len(ops) != len(peers):
                notes[v["view_id"]] = {"state": "STACK_NOT_BOUND", "drawn_openings": len(ops),
                                       "plan_openings_on_range": sorted((q["floor"], q["id"]) for q in peers)}
                continue
            order = sorted(peers, key=lambda q: fidx.get(q["floor"], 99))
            op = ops[next(i for i, q in enumerate(order) if q["id"] == p["id"] and q["floor"] == p["floor"])]
            h = printed_height(v, x0, x1, op)
            ev = {"view": v["view_id"], "jambs": op["jambs"], "foot_du": round(op["foot"], 3),
                  "jamb_top_du": round(op["top"], 3), **h}
            notes[v["view_id"]] = ev
            if h["state"] == "PRINTED":
                cand.append(("ELEVATION", h["height_m"], ev))
        if p.get("schedule_height_m") is not None:
            sched = float(p["schedule_height_m"])
            diff = [c for c in cand if abs(c[1] - sched) > TOL_M]
            rec_ev = {"schedule": {"height_m": sched, "source": p.get("schedule_source")}, "elevations": notes}
            if diff:
                rec_ev["finding"] = ("REVIEW: the schedule height %.3f governs over the elevation %s (UP-DOOR-HGT-001 "
                                     "order)" % (sched, [c[1] for c in diff]))
            cand = [("SCHEDULE", sched, rec_ev)]
        if p.get("faces_outside") is False and not cand:
            records.append(_held(p, "INTERIOR_OPENING", why="the run finds a space on both sides: no elevation shows "
                                                            "it; its height comes from a schedule or section only"))
            continue
        if not found.get(key) and not cand:
            records.append(_held(p, "NO_ELEVATION_OF_THIS_FACE", views=[(v["view_id"], v["mapping"]["state"])
                                                                          for v in vout]))
            continue
        hs = sorted({round(c[1], 4) for c in cand})
        if not hs:
            states = {n.get("state") for n in notes.values()}
            reason = next((r for r in HOLD_ORDER if r in states), "NO_PRINTED_HEIGHT")
            records.append(_held(p, reason, elevations=notes))
            continue
        if len(hs) > 1:
            records.append(_held(p, "HEIGHT_CONFLICT", values_m=hs, elevations=notes))
            continue
        width, wsrc = p["width_m"], "PLAN (jamb to jamb)"
        if p.get("curved"):
            bases = dict((p["curved"].get("bases_m") or {}), CHORD=p["curved"].get("chord_m"))
            if curved_width_basis is None or bases.get(curved_width_basis) is None:
                records.append(_held(p, "CURVED_WIDTH_BASIS", height_m_printed=hs[0], candidates_m2={
                    k: round(b * hs[0], 3) for k, b in bases.items() if b is not None}, elevations=notes))
                continue
            width, wsrc = bases[curved_width_basis], f"PLAN curved, basis {curved_width_basis} (owner)"
        rec = {"id": p["id"], "floor": p["floor"], "kind": p["kind"], "status": MEASURED, "reason": None,
               "width_m": round(width, 4), "width_source": wsrc, "height_m": hs[0], "height_source": cand[0][0],
               "area_m2": round(width * hs[0], 3), "view": "AS_DRAWN", "evidence": cand[0][2], **_material(p),
               "plan_width_m": p["width_m"]}
        records.append(rec)
    _same_drawn_size(records, {v["view_id"]: v["unit_m"] for v in vout})
    return {"records": records, "views": [{"view_id": v["view_id"], "mapping": v["mapping"],
                                           "printed": Counter("USABLE" if d["usable"] else (d["why_not"] or "?")
                                                              .split(" ")[0] for d in v["printed"])}
                                          for v in vout],
            "summary": summary(records), "policy": policy_record()}


def _same_drawn_size(records, units):
    """Evidence only, never a release: a held opening drawn at the same width, foot and jamb height on the same
    elevation as a measured one is listed against it (a QS may ask the designer to confirm the same height)."""
    done = [r for r in records if r["status"] == MEASURED and r["evidence"].get("view")]
    for r in records:
        if r["status"] != HELD or r["reason"] not in ("NO_PRINTED_HEIGHT", "ARCH_TOP_NOT_PRINTED"):
            continue
        for vid, n in (r["evidence"].get("elevations") or {}).items():
            if "jamb_top_du" not in n:
                continue
            t = TOL_M / units[vid]
            same = [m["id"] + "@" + m["floor"] for m in done if m["evidence"]["view"] == vid
                    and abs(m["evidence"]["foot_du"] - n["foot_du"]) <= t
                    and abs(m["evidence"]["jamb_top_du"] - n["jamb_top_du"]) <= t
                    and m.get("plan_width_m") is not None and r.get("width_m") is not None
                    and abs(m["plan_width_m"] - r["width_m"]) <= TOL_M]
            if same:
                n["same_drawn_size_as"] = same
                n["note"] = "evidence only: not released (no printed height for THIS opening)"


def summary(records):
    out = {"by_status": dict(Counter(r["status"] for r in records)),
           "held_reasons": dict(Counter(r["reason"] for r in records if r["status"] == HELD)),
           "measured_m2": {}}
    for r in records:
        if r["status"] == MEASURED:
            k = f"{r['kind']}:{r.get('material')}"
            out["measured_m2"][k] = round(out["measured_m2"].get(k, 0.0) + r["area_m2"], 3)
    return out


def policy_record():
    return {"policy": POLICY_ID, "tol_m": TOL_M, "axis_deg": AXIS_DEG, "rules": list(RULES),
            "never": ["a default or usual height", "a benchmark figure", "an area of 0 for a held opening",
                      "a position bound by one width match", "a stale dimension", "the owner-standard and as-drawn "
                      "views added together", "an arch top that no printed dimension reaches"]}


# ------------------------------------------------------------------------------------------ DXF view reader
def read_view(doc, box, unit_m, view_id):
    """One elevation frame of a DXF (ezdxf document) -> a view for measure(). box = (x0, y0, x1, y1) drawing units.
    Lines, polylines (bulges flattened), arcs and block contents (exploded) whose points all lie in the box; the
    DIMENSION records of model space whose witness origins lie in the box."""
    from ezdxf import path as ezpath                                    # lazy: the core above stays stdlib-only

    def inb(x, y):
        return box[0] <= x <= box[2] and box[1] <= y <= box[3]

    segs = []

    def take(e, depth=0):
        kind = e.dxftype()
        if kind == "INSERT" and depth < 4:
            try:
                for v in e.virtual_entities():
                    take(v, depth + 1)
            except Exception:                                           # noqa: BLE001 - unreadable block counted
                segs.append(None)
            return
        if kind == "LINE":
            pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        elif kind in ("LWPOLYLINE", "POLYLINE", "ARC"):
            try:
                pts = [(q.x, q.y) for q in ezpath.make_path(e).flattening(0.005 / unit_m)]
            except Exception:                                           # noqa: BLE001
                segs.append(None)
                return
        else:
            return
        if all(inb(*q) for q in pts):
            for a, b in zip(pts, pts[1:]):
                if a != b:
                    segs.append((a[0], a[1], b[0], b[1], f"{kind}:{e.dxf.handle}"))

    msp = doc.modelspace()
    for e in msp:
        if e.dxftype() in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC", "INSERT"):
            take(e)
    hdr = doc.header.get("$DIMLFAC")
    dims = []
    types = {0: "LINEAR", 1: "ALIGNED"}
    for d in msp.query("DIMENSION"):
        p2, p3 = d.dxf.get("defpoint2"), d.dxf.get("defpoint3")
        if p2 is None or p3 is None or not (inb(p2[0], p2[1]) and inb(p3[0], p3[1])):
            continue
        try:
            dt = d.dimtype
        except Exception:                                               # noqa: BLE001
            continue
        style = doc.dimstyles.get(d.dxf.get("dimstyle")) if d.dxf.get("dimstyle") else None
        try:
            ov = d.override().dimstyle_attribs.get("dimlfac")
        except Exception:                                               # noqa: BLE001
            ov = None
        shown = None
        blk = doc.blocks.get(d.dxf.get("geometry")) if d.dxf.get("geometry") else None
        for x in (blk or ()):
            if x.dxftype() in ("MTEXT", "TEXT"):
                shown = x.plain_text() if x.dxftype() == "MTEXT" else x.dxf.text
                break
        dims.append({"handle": d.dxf.handle, "type": types.get(dt, str(dt)), "p2": [p2[0], p2[1]],
                     "p3": [p3[0], p3[1]], "angle": float(d.dxf.get("angle", 0.0) or 0.0),
                     "style_dimlfac": style.dxf.get("dimlfac") if style is not None else None,
                     "override_dimlfac": ov, "measurement": d.dxf.get("actual_measurement"),
                     "text": d.dxf.get("text", "") or "", "shown_text": shown})
    return {"view_id": view_id, "unit_m": unit_m, "header_dimlfac": float(hdr) if hdr is not None else None,
            "dims": dims, "segments": [s for s in segs if s is not None], "unreadable": sum(1 for s in segs if s is None)}
