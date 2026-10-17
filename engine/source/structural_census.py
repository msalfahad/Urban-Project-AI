"""STRUCTURAL_CENSUS_V1 - source rules + occurrence census, before any reinforcement calculation.

Project-agnostic rules for the structural-QS workflow

    SOURCE RULES -> OCCURRENCE CENSUS -> SCHEDULE DEFINITIONS -> STOREY CONTINUITY -> MEMBER GEOMETRY -> (rebar later)

    * The PLAN decides occurrence; the SCHEDULE only defines a type. A schedule row never creates an occurrence.
    * Every plan object ends in one terminal state: COUNTED_AND_DEFINED / COUNTED_DEFINITION_PARTIAL / COUNTED_BLOCKED /
      NOT_IN_SCOPE. Nothing disappears.
    * Rules carry a precedence (LOCAL PANEL NOTE > FLOOR-SPECIFIC NOTE > PROJECT DEFAULT); a default never overrides a
      local note and a value is never rounded into a table row it does not match.
    * Column identity is physical: one plan position followed floor by floor (VERTICAL CHAIN). A type change, a stop or a
      start on a slab is recorded as an event of the chain - never inferred from the schedule.

No kg, no lengths of bars: this module only counts, binds and classifies. Stdlib only.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

POLICY_ID = "STRUCTURAL_CENSUS_V1"

TERMINAL_STATES = ("COUNTED_AND_DEFINED", "COUNTED_DEFINITION_PARTIAL", "COUNTED_BLOCKED", "NOT_IN_SCOPE")
RULE_STATES = ("EXACT_RULE", "RULE_NOT_EXACT_MATCH", "BLOCKED_METHOD")
CB_STATES = ("MATCH_CONFIRMED", "SPAN_LENGTH_CONFLICT", "SPAN_COUNT_CONFLICT", "TAG_WITH_NO_MEMBER",
             "MEMBER_WITH_NO_TAG", "BLOCKED")
PRECEDENCE = ("LOCAL_PANEL_NOTE", "FLOOR_SPECIFIC_NOTE", "PROJECT_DEFAULT")


# ============================================================================================ rule precedence
def effective_value(*, local=None, floor=None, project=None):
    """Resolve one parameter by precedence LOCAL_PANEL_NOTE > FLOOR_SPECIFIC_NOTE > PROJECT_DEFAULT.
    Each argument is None or {"value": v, "source": ...}. Returns {value, authority, source, overridden}."""
    chain = [("LOCAL_PANEL_NOTE", local), ("FLOOR_SPECIFIC_NOTE", floor), ("PROJECT_DEFAULT", project)]
    present = [(k, v) for k, v in chain if v is not None and v.get("value") is not None]
    if not present:
        return {"value": None, "authority": "BLOCKED", "source": None, "overridden": []}
    k, v = present[0]
    return {"value": v["value"], "authority": k, "source": v.get("source"),
            "overridden": [{"authority": k2, "value": v2["value"], "source": v2.get("source")}
                           for k2, v2 in present[1:] if v2["value"] != v["value"]]}


def table_lookup_exact(value, table):
    """A table rule applies only to an exact row. table: {row_key: payload}. Returns (state, payload)."""
    if value in table:
        return "EXACT_RULE", table[value]
    return "RULE_NOT_EXACT_MATCH", None


# ============================================================================================ column tie topology
def tie_band(L_cm, bands):
    """Pick the column tie-topology band for long dimension L (cm). bands: [{band_id, lo, lo_incl, hi, hi_incl, ...}]
    (None = unbounded). A value on a boundary that no band includes is BOUNDARY_GAP - never snapped to a neighbour."""
    hits = []
    for b in bands:
        lo_ok = b["lo"] is None or (L_cm > b["lo"] or (b["lo_incl"] and L_cm == b["lo"]))
        hi_ok = b["hi"] is None or (L_cm < b["hi"] or (b["hi_incl"] and L_cm == b["hi"]))
        if lo_ok and hi_ok:
            hits.append(b)
    if len(hits) == 1:
        return {"state": "EXACT_RULE", "band": hits[0]["band_id"]}
    if len(hits) > 1:
        return {"state": "SOURCE_CONFLICT", "band": [b["band_id"] for b in hits]}
    lows = [b["lo"] for b in bands if b["lo"] is not None] + [b["hi"] for b in bands if b["hi"] is not None]
    if L_cm in lows:
        return {"state": "BOUNDARY_GAP", "band": None}
    return {"state": "OUT_OF_RANGE", "band": None}


def min_thickness_check(H_m, T_cm, table):
    """table: [{lo, lo_incl, hi, hi_incl, t_min_cm}] on storey height H (m). Returns PASS / BELOW_MINIMUM /
    NOT_COVERED (H falls in no row) / SOURCE_OVERLAP (H in two rows with different minima -> stricter reported)."""
    rows = [r for r in table if (r["lo"] is None or H_m > r["lo"] or (r["lo_incl"] and H_m == r["lo"]))
            and (r["hi"] is None or H_m < r["hi"] or (r["hi_incl"] and H_m == r["hi"]))]
    if not rows:
        return {"state": "NOT_COVERED", "t_min_cm": None}
    mins = sorted({r["t_min_cm"] for r in rows})
    tmin = mins[-1]
    st = "PASS" if T_cm >= tmin else "BELOW_MINIMUM"
    return {"state": st if len(mins) == 1 else st + "_SOURCE_OVERLAP", "t_min_cm": tmin, "candidates": mins}


# ============================================================================================ geometry helpers
def bbox_overlap(a, b, tol=0.0):
    """a, b = (xmin, ymin, xmax, ymax). Overlap area of the boxes grown by tol (0 when disjoint)."""
    w = min(a[2], b[2]) + tol - (max(a[0], b[0]) - tol)
    h = min(a[3], b[3]) + tol - (max(a[1], b[1]) - tol)
    return w * h if w > 0 and h > 0 else 0.0


def point_in_ring(p, ring):
    x, y = p
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xi > x:
                inside = not inside
    return inside


def ring_area(ring):
    return abs(sum(ring[i][0] * ring[(i + 1) % len(ring)][1] - ring[(i + 1) % len(ring)][0] * ring[i][1]
                   for i in range(len(ring)))) / 2.0


# ============================================================================================ vertical chains
def vertical_chains(levels, occ, *, tol=0.0, max_skip=1):
    """Follow plan positions floor by floor.

    levels: ordered level names bottom -> top.
    occ: {level: [{id, bbox, type|None, starts_here(bool, e.g. planted), labels}]}.
    Two occurrences on adjacent levels belong to one chain when their boxes overlap (grown by tol) and each is the
    other's best overlap; up to max_skip intermediate levels may omit the position (GAP_IN_CHAIN event). Returns chains [{chain_id, members{level: id}, types{level: type}, events}] and
    the per-level ids that started a chain without support below (starts) - every occurrence is in exactly one chain.
    """
    chains = []
    occ_by = {(lv, o["id"]): o for lv in levels for o in occ.get(lv, [])}
    for li, lv in enumerate(levels):
        cur = sorted(occ.get(lv, []), key=lambda o: (o["bbox"][1], o["bbox"][0], str(o["id"])))
        # open chains: top member one level below (or, with max_skip, a few levels below - a plan that omits the
        # position is a GAP, recorded, never a new column)
        open_ch = []
        for ci, ch in enumerate(chains):
            top = max(ch["members"], key=levels.index)
            k = levels.index(top)
            top_o = occ_by[(top, ch["members"][top])]
            if top_o.get("ends_here"):
                continue
            if 1 <= li - k <= 1 + max_skip:
                open_ch.append((li - k, ci, top_o))
        links = defaultdict(list)
        back = defaultdict(list)
        for o in cur:
            if o.get("starts_here"):
                continue
            for dist, ci, p in open_ch:
                a = bbox_overlap(o["bbox"], p["bbox"], tol)
                if a > 1.0:
                    links[o["id"]].append((-dist, a, ci))
                    back[ci].append((-dist, a, o["id"]))
        for o in cur:
            cand = sorted(links.get(o["id"], []), reverse=True)
            chosen = None
            if cand:
                ci = cand[0][2]
                rivals = sorted(back[ci], reverse=True)
                if rivals[0][2] == o["id"]:          # mutual best overlap -> same physical position
                    chosen = ci
            if chosen is not None and lv not in chains[chosen]["members"]:
                ch = chains[chosen]
                below = max(ch["members"], key=levels.index)
                skipped = levels[levels.index(below) + 1:li]
                ch["members"][lv] = o["id"]
                ch["types"][lv] = o.get("type")
                if skipped:
                    ch["events"].append({"level": lv, "event": "GAP_IN_CHAIN", "levels": skipped})
                if len(cand) > 1 or len(back[chosen]) > 1:
                    ch["events"].append({"level": lv, "event": "AMBIGUOUS_LINK",
                                         "candidates_below": [chains[c[2]]["members"] for c in cand],
                                         "candidates_above": [c[2] for c in back[chosen]]})
            else:
                chains.append({"chain_id": None, "members": {lv: o["id"]}, "types": {lv: o.get("type")}, "events": []})
                if o.get("starts_here"):
                    chains[-1]["events"].append({"level": lv, "event": "STARTS_ON_SLAB"})
                elif li and cand:
                    chains[-1]["events"].append({"level": lv, "event": "OVERLAPS_BELOW_NOT_LINKED",
                                                 "candidates_below": [chains[c[2]]["members"] for c in cand]})
                elif li:
                    chains[-1]["events"].append({"level": lv, "event": "NO_SUPPORT_BELOW"})
    for ch in chains:
        present = [lv for lv in levels if lv in ch["members"]]
        ch["starts_at"] = present[0]
        ch["terminates_at"] = present[-1]
        ch["continues_through"] = present
        typed = [(lv, ch["types"][lv]) for lv in present if ch["types"].get(lv)]
        for (l0, t0), (l1, t1) in zip(typed, typed[1:]):
            if t0 != t1:
                ch["events"].append({"event": "TYPE_CHANGE", "from_level": l0, "to_level": l1, "from": t0, "to": t1})
    return chains


def chain_check(chains, levels, occ):
    """Hard invariant: every occurrence is in exactly one chain; every chain member on level k that is not the chain's
    top was checked on level k+1 (a stop is explicit: terminates_at)."""
    seen = defaultdict(int)
    for ch in chains:
        for lv, oid in ch["members"].items():
            seen[(lv, oid)] += 1
    viol = []
    for lv in levels:
        for o in occ.get(lv, []):
            n = seen.get((lv, o["id"]), 0)
            if n != 1:
                viol.append({"level": lv, "id": o["id"], "chains": n})
    return viol


# ============================================================================================ footings vs columns
def footing_column_check(footings, columns):
    """footings: [{id, ring, type}]; columns: [{id, centre, needs_footing(bool)}].
    Returns column -> footings, footing -> columns and the mismatch list."""
    col_f = defaultdict(list)
    f_col = defaultdict(list)
    for f in footings:
        for c in columns:
            if point_in_ring(c["centre"], f["ring"]):
                col_f[c["id"]].append(f["id"])
                f_col[f["id"]].append(c["id"])
    mis = []
    for c in columns:
        n = len(col_f.get(c["id"], []))
        if c.get("needs_footing", True) and n == 0:
            mis.append({"kind": "COLUMN_WITHOUT_FOOTING", "column": c["id"]})
        elif n > 1:
            mis.append({"kind": "COLUMN_IN_SEVERAL_FOOTINGS", "column": c["id"], "footings": col_f[c["id"]]})
    for f in footings:
        if not f_col.get(f["id"]):
            mis.append({"kind": "FOOTING_WITHOUT_COLUMN", "footing": f["id"], "type": f.get("type")})
    by_ring = defaultdict(list)
    for f in footings:
        key = tuple(sorted((round(x), round(y)) for x, y in f["ring"]))
        by_ring[key].append(f["id"])
    for ids in by_ring.values():
        if len(ids) > 1:
            mis.append({"kind": "DUPLICATE_FOOTING", "footings": ids})
    return dict(col_f), dict(f_col), mis


# ============================================================================================ continuous beams
def cb_match_state(schedule_spans_m, plan_spans_m, *, tol_m=0.25, tol_rel=0.08, has_member=True, has_tag=True):
    """Compare a CB schedule row with one plan occurrence. Never forces a match."""
    if not has_tag:
        return "MEMBER_WITH_NO_TAG"
    if not has_member:
        return "TAG_WITH_NO_MEMBER"
    if schedule_spans_m is None or plan_spans_m is None or any(v is None for v in plan_spans_m):
        return "BLOCKED"
    if len(schedule_spans_m) != len(plan_spans_m):
        return "SPAN_COUNT_CONFLICT"
    for s, p in zip(schedule_spans_m, plan_spans_m):
        if abs(s - p) > max(tol_m, tol_rel * s):
            # a reversed drawing direction is still the same member
            break
    else:
        return "MATCH_CONFIRMED"
    for s, p in zip(schedule_spans_m, list(reversed(plan_spans_m))):
        if abs(s - p) > max(tol_m, tol_rel * s):
            return "SPAN_LENGTH_CONFLICT"
    return "MATCH_CONFIRMED"


# ============================================================================================ slab annotations
_SLAB_TXT = re.compile(r"^\s*(?P<n>\d+)\s*(?:%%[cC]|Ø|Φ|ø)\s*(?P<d>\d+)\s*(?P<pm>/\s*m)?\s*(?P<q>/\s*top|/\s*bot)?\s*$",
                       re.I)
_SPACING_TXT = re.compile(r"^\s*(?:%%[cC]|Ø|ø)\s*(?P<d>\d+)\s*/\s*(?P<s>\d+)\s*cm\s*$", re.I)


def parse_slab_rebar(raw):
    """'5%%c10/m' -> 5 bars/m Ø10; '3%%c16/Top' -> 3 Ø16 TOP (absolute); 'Ø12/20cm' -> Ø12 @ 200 mm.
    Returns None when the text is not a bar annotation."""
    t = raw.strip()
    m = _SLAB_TXT.match(t)
    if m:
        q = (m.group("q") or "").replace(" ", "").lower()
        return {"count": int(m.group("n")), "dia_mm": int(m.group("d")),
                "count_mode": "BARS_PER_METRE" if m.group("pm") else "ABSOLUTE_COUNT",
                "layer_qualifier": "TOP" if q == "/top" else ("BOTTOM" if q == "/bot" else None)}
    m = _SPACING_TXT.match(t)
    if m:
        return {"count": None, "dia_mm": int(m.group("d")), "spacing_mm": int(m.group("s")) * 10,
                "count_mode": "SPACING", "layer_qualifier": None}
    return None


def bind_to_panel(point, panels, *, near=None):
    """point -> the one panel whose ring contains it. panels: [{id, ring}]. A point inside no panel is UNBOUND; inside
    several (overlapping faces) AMBIGUOUS. `near` (mm) also tries the panels within that distance of the point."""
    hits = [p["id"] for p in panels if point_in_ring(point, p["ring"])]
    if len(hits) == 1:
        return "BOUND", hits
    if len(hits) > 1:
        return "AMBIGUOUS", hits
    if near:
        close = []
        for p in panels:
            d = min(_dist_seg(point, p["ring"][i], p["ring"][(i + 1) % len(p["ring"])]) for i in range(len(p["ring"])))
            if d <= near:
                close.append((d, p["id"]))
        if len(close) == 1:
            return "BOUND_NEAR_EDGE", [close[0][1]]
        if close:
            return "AMBIGUOUS", [c[1] for c in sorted(close)]
    return "UNBOUND", []


def _dist_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if not L2 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


# ============================================================================================ conservation
def conservation(source_objects, register_rows):
    """source_objects: [{source_id, family}]; register_rows: [{source_id, register, terminal_state}].
    Every source object must appear exactly once with a terminal state. Returns {violations, by_state, by_family}."""
    rows = defaultdict(list)
    for r in register_rows:
        rows[r["source_id"]].append(r)
    viol = []
    by_state = defaultdict(int)
    by_family = defaultdict(lambda: defaultdict(int))
    for s in source_objects:
        rs = rows.get(s["source_id"], [])
        if not rs:
            viol.append({"kind": "SILENT_DISAPPEARANCE", "source_id": s["source_id"], "family": s["family"]})
            continue
        if len(rs) > 1:
            viol.append({"kind": "DOUBLE_COUNTED", "source_id": s["source_id"], "registers": [r["register"] for r in rs]})
        st = rs[0]["terminal_state"]
        if st not in TERMINAL_STATES:
            viol.append({"kind": "NON_TERMINAL_STATE", "source_id": s["source_id"], "state": st})
        by_state[st] += 1
        by_family[s["family"]][st] += 1
    known = {s["source_id"] for s in source_objects}
    for sid in rows:
        if sid not in known:
            viol.append({"kind": "ROW_WITHOUT_SOURCE", "source_id": sid})
    return {"violations": viol, "by_state": dict(by_state),
            "by_family": {k: dict(v) for k, v in by_family.items()}}


def terminal_state(*, counted, definition):
    """counted: bool (a plan occurrence exists with geometry); definition: 'FULL' | 'PARTIAL' | 'NONE' | 'NIS'."""
    if definition == "NIS":
        return "NOT_IN_SCOPE"
    if not counted:
        return "COUNTED_BLOCKED"
    return {"FULL": "COUNTED_AND_DEFINED", "PARTIAL": "COUNTED_DEFINITION_PARTIAL"}.get(definition, "COUNTED_BLOCKED")


def policy_record():
    return {"policy_id": POLICY_ID, "terminal_states": list(TERMINAL_STATES), "rule_states": list(RULE_STATES),
            "cb_states": list(CB_STATES), "precedence": list(PRECEDENCE),
            "principles": ["plan decides occurrence; schedule only defines", "no default overrides a local note",
                           "a value is never rounded into a table row it does not match",
                           "every plan object ends in one terminal state"]}
