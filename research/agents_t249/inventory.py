"""T-249: an engine-independent opening inventory (any villa).

An opening is ONE physical element: a gap in a wall closed by a leaf (door), by glazing (window) or by nothing (passage).
Its EXISTENCE is established only by what the drawings draw or print: a plan symbol (door leaf block / swing, glazing
lines in a wall gap), a plan tag, an elevation feature, a schedule row. The engine's own opening list is never a source of
existence: it is used only AFTER the inventory is built, to crosswalk (agree / missing / extra).

Rules (proposed UP-OPEN-INV-001 v1.0.0, provenance: ERS s.2 step 3 'reconstruct from first principles, not from the
engine', the T-236 lesson and the T-017 lesson 'handles, not capture ids'):
  R1 an observation whose only source is the engine (or any derived list) is refused;
  R2 one physical location = one opening, however many tags / sheets show it (two tags on one opening: counted once,
     flagged TWO_TAGS; producing two rows for one location is refused);
  R3 a tag is a label, not an identity: the same tag at two locations is two openings, flagged DUPLICATE_TAG;
  R4 an elevation feature bound to no plan opening is listed ELEVATION_ONLY (pcs HELD), never added to the settled count
     and never measured;
  R5 every plan opening carries the entity handles it was read from;
  R6 positions read off a sheet bind identity only; widths come from the drawn symbol extent or a printed dimension.

Units: metres throughout (callers convert drawing units first).
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict

ALLOWED_SOURCES = ("PLAN_SYMBOL", "PLAN_TAG", "ELEVATION", "SECTION", "SCHEDULE")
REFUSED_SOURCES = ("ENGINE", "DERIVED_LIST")


class InventoryError(ValueError):
    pass


# ---------------------------------------------------------------- plan symbols

def cluster(items, tol):
    """items: [{'handle', 'bbox': (x0, y0, x1, y1), 'curved': bool}] in metres. Union of items whose boxes touch within
    tol. Returns clusters as {'handles', 'bbox', 'curved', 'n'} sorted by (bbox y0, x0)."""
    n = len(items)
    par = list(range(n))

    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i

    for i in range(n):
        a = items[i]["bbox"]
        for j in range(i + 1, n):
            b = items[j]["bbox"]
            if a[0] - tol <= b[2] and b[0] - tol <= a[2] and a[1] - tol <= b[3] and b[1] - tol <= a[3]:
                par[f(i)] = f(j)
    groups = defaultdict(list)
    for i in range(n):
        groups[f(i)].append(items[i])
    out = []
    for g in groups.values():
        x0 = min(it["bbox"][0] for it in g)
        y0 = min(it["bbox"][1] for it in g)
        x1 = max(it["bbox"][2] for it in g)
        y1 = max(it["bbox"][3] for it in g)
        out.append({"handles": sorted(it["handle"] for it in g), "bbox": (x0, y0, x1, y1),
                    "curved": any(it.get("curved") for it in g), "n": len(g)})
    return sorted(out, key=lambda c: (round(c["bbox"][1], 3), round(c["bbox"][0], 3)))


def window_symbol(c, max_depth=0.35, min_width=0.30):
    """a glazing cluster -> a plan window symbol, or None when it is not one (too shallow / too deep). Straight symbols:
    width = the long extent (the symbol spans jamb to jamb), axis = the long direction. Curved symbols: width is NOT the
    box (a curved window's width is a named arc or a printed dimension, Q-38 / Q-39): width None, axis None."""
    x0, y0, x1, y1 = c["bbox"]
    dx, dy = x1 - x0, y1 - y0
    centre = ((x0 + x1) / 2.0, (y0 + y1) / 2.0)
    if c["curved"]:
        return {"handles": c["handles"], "centre": centre, "axis": None, "width_m": None, "depth_m": None,
                "curved": True, "n": c["n"]}
    long_, short = (dx, dy) if dx >= dy else (dy, dx)
    if long_ < min_width or short > max_depth:
        return None
    return {"handles": c["handles"], "centre": centre, "axis": "X" if dx >= dy else "Y", "width_m": round(long_, 4),
            "depth_m": round(short, 4), "curved": False, "n": c["n"]}


def merge_parallel_triples(symbols, gap=0.06):
    """three loose glass lines drawn without end ticks come out as three zero-depth clusters 0.05 m apart: one window.
    Merge zero-depth straight symbols of equal width, same axis, whose offsets are within gap of a neighbour."""
    thin = [s for s in symbols if not s["curved"] and s["depth_m"] == 0.0]
    rest = [s for s in symbols if s not in thin]
    used = set()
    out = list(rest)
    for i, s in enumerate(thin):
        if i in used:
            continue
        grp = [i]
        changed = True
        while changed:
            changed = False
            for j, t in enumerate(thin):
                if j in used or j in grp or t["axis"] != s["axis"] or abs(t["width_m"] - s["width_m"]) > 1e-3:
                    continue
                k = 1 if s["axis"] == "Y" else 0          # along-axis coordinate must coincide
                o = 1 - k                                # offset coordinate (across the wall)
                if abs(t["centre"][k] - s["centre"][k]) > 1e-3:
                    continue
                if any(abs(t["centre"][o] - thin[g]["centre"][o]) <= gap for g in grp):
                    grp.append(j)
                    changed = True
        used.update(grp)
        g = [thin[j] for j in grp]
        o = 1 if s["axis"] == "X" else 0
        offs = [x["centre"][o] for x in g]
        c = list(s["centre"])
        c[o] = (min(offs) + max(offs)) / 2.0
        out.append({"handles": sorted(h for x in g for h in x["handles"]), "centre": tuple(c), "axis": s["axis"],
                    "width_m": s["width_m"], "depth_m": round(max(offs) - min(offs), 4), "curved": False,
                    "n": sum(x["n"] for x in g)})
    return out


# ---------------------------------------------------------------- elevation binding

def facade_coordinate(symbol, facade):
    """facade = {'axis': 'X' | 'Y', 'sign': +1 | -1}: the plan coordinate measured along the facade, signed so that it
    grows left to right as the elevation is seen from outside."""
    k = 0 if facade["axis"] == "X" else 1
    return facade["sign"] * symbol["centre"][k]


def bind_elevation(symbols, features, facade, tol=0.05):
    """symbols: plan symbols that may lie on ONE facade, each with 'storey' and a centre registered to a point common to
    every storey plan; features: that facade's elevation features [{'ref', 'storey', 'pos_m', 'width_m' (optional)}].
    A feature binds only to a symbol of its own storey. The offset between the elevation's origin and the plans is ONE
    value per facade, solved from the data: the candidate offset (feature pos - symbol coord over every same-storey pair)
    that binds the most features within tol, ties broken by the smaller summed residual (a facade with a single feature
    cannot be solved: everything unbound). A feature within tol of two symbols is AMBIGUOUS (bound to neither); a symbol
    claimed by two features keeps the nearer. A printed feature width must agree with the symbol width within 0.05 m.
    Returns (bindings {ref: (symbol index, residual m)}, unbound [ref], ambiguous [ref], offset)."""
    coords = [facade_coordinate(s, facade) for s in symbols]

    def cands(f, off):
        out = []
        for i, c in enumerate(coords):
            if symbols[i]["storey"] != f["storey"]:
                continue
            d = abs(f["pos_m"] - off - c)
            if d > tol:
                continue
            if f.get("width_m") and symbols[i]["width_m"] is not None and abs(symbols[i]["width_m"] - f["width_m"]) > 0.05:
                continue
            out.append((d, i))
        return out

    if len(features) < 2 or not symbols:
        return {}, [f["ref"] for f in features], [], None
    best = None
    for f in features:
        for i, c in enumerate(coords):
            if symbols[i]["storey"] != f["storey"]:
                continue
            off = f["pos_m"] - c
            hits, res = 0, 0.0
            for g in features:
                cg = cands(g, off)
                if cg:
                    hits += 1
                    res += min(cg)[0]
            key = (-hits, round(res, 6))
            if best is None or key < best[0]:
                best = (key, off)
    off = best[1]
    bind, unbound, amb, claim = {}, [], [], {}
    for f in features:
        near = cands(f, off)
        if not near:
            unbound.append(f["ref"])
        elif len(near) > 1:
            amb.append(f["ref"])
        else:
            d, i = near[0]
            if i in claim and claim[i][0] <= d:
                unbound.append(f["ref"])
                continue
            if i in claim:
                unbound.append(claim[i][1])
                del bind[claim[i][1]]
            claim[i] = (d, f["ref"])
            bind[f["ref"]] = (i, round(d, 4))
    return bind, unbound, amb, off


# ---------------------------------------------------------------- inventory

def build(observations, loc_tol=0.15):
    """observations: [{'source': one of ALLOWED_SOURCES, 'kind': DOOR | WINDOW | OPENING, 'storey', 'loc': (x, y) or
    None, 'tag': str or None, 'handles': [..], 'ref': str, 'width_m': float or None}].
    Observations at one storey within loc_tol are ONE opening (R2). Observations without a location (elevation-only,
    schedule-only) stay their own ELEVATION_ONLY / SCHEDULE_ONLY rows (R4). Returns rows sorted by storey, kind, tag."""
    for o in observations:
        if o["source"] in REFUSED_SOURCES:
            raise InventoryError(f"R1: {o['ref']}: an opening taken from the engine's list (or a derived list) only is "
                                 f"refused: existence needs a drawing source")
        if o["source"] not in ALLOWED_SOURCES:
            raise InventoryError(f"unknown source {o['source']!r} ({o['ref']})")
        if o["source"] == "PLAN_SYMBOL" and not o.get("handles"):
            raise InventoryError(f"R5: plan symbol {o['ref']} carries no entity handle")
    located = [o for o in observations if o.get("loc") is not None]
    loose = [o for o in observations if o.get("loc") is None]
    groups = []
    for o in located:
        for g in groups:
            if g[0]["storey"] == o["storey"] and any(math.dist(o["loc"], x["loc"]) <= loc_tol for x in g):
                g.append(o)
                break
        else:
            groups.append([o])
    rows = []
    for g in groups:
        kinds = {x["kind"] for x in g}
        if len(kinds) > 1:
            raise InventoryError(f"one location, two kinds {sorted(kinds)}: {[x['ref'] for x in g]}")
        tags = sorted({x["tag"] for x in g if x.get("tag")})
        src = sorted({x["source"] for x in g})
        flags = []
        if len(tags) > 1:
            flags.append("TWO_TAGS")
        if "PLAN_SYMBOL" not in src and "PLAN_TAG" not in src:
            flags.append("NO_PLAN_SOURCE")
        widths = sorted({round(x["width_m"], 4) for x in g if x.get("width_m")})
        rows.append({"storey": g[0]["storey"], "kind": g[0]["kind"], "tags": tags, "sources": src,
                     "handles": sorted({h for x in g for h in (x.get("handles") or [])}),
                     "refs": sorted(x["ref"] for x in g), "width_m": widths[0] if len(widths) == 1 else None,
                     "widths_seen": widths, "loc": g[0]["loc"], "flags": flags, "state": "LOCATED"})
    for o in loose:
        st = "ELEVATION_ONLY" if o["source"] in ("ELEVATION", "SECTION") else "SCHEDULE_ONLY"
        rows.append({"storey": o["storey"], "kind": o["kind"], "tags": [o["tag"]] if o.get("tag") else [],
                     "sources": [o["source"]], "handles": sorted(o.get("handles") or []), "refs": [o["ref"]],
                     "width_m": o.get("width_m"), "widths_seen": [o["width_m"]] if o.get("width_m") else [],
                     "loc": None, "flags": [], "state": st})
    tagcount = Counter(t for r in rows if r["state"] == "LOCATED" for t in r["tags"])
    for r in rows:
        if any(tagcount[t] > 1 for t in r["tags"]):
            r["flags"].append("DUPLICATE_TAG")
    check_counted_once(rows, loc_tol)
    return sorted(rows, key=lambda r: (r["storey"], r["kind"], r["tags"], r["refs"]))


def check_counted_once(rows, loc_tol=0.15):
    """R2 guard: two LOCATED rows at one storey within loc_tol are one opening counted twice -> refused."""
    loc = [r for r in rows if r["state"] == "LOCATED"]
    for i, a in enumerate(loc):
        for b in loc[i + 1:]:
            if a["storey"] == b["storey"] and math.dist(a["loc"], b["loc"]) <= loc_tol:
                raise InventoryError(f"R2: one opening counted twice: {a['refs']} and {b['refs']}")
    seen = Counter(h for r in loc for h in r["handles"])
    dup = [h for h, n in seen.items() if n > 1]
    if dup:
        raise InventoryError(f"R2: entity handles in two openings: {sorted(dup)}")


def settled_count(rows, kind):
    """pcs of a kind that the drawings settle: LOCATED rows only; ELEVATION_ONLY / SCHEDULE_ONLY are reported apart."""
    loc = sum(1 for r in rows if r["kind"] == kind and r["state"] == "LOCATED")
    held = sum(1 for r in rows if r["kind"] == kind and r["state"] != "LOCATED")
    return {"settled": loc, "held": held}


def crosswalk(inventory_ids, list_ids):
    """inventory_ids: ids of the engine-independent inventory; list_ids: ids of a list built otherwise (a census seeded
    from the engine, an integration input). Never settled by the list: AGREE / MISSING_FROM_LIST / EXTRA_IN_LIST."""
    inv, lst = set(inventory_ids), set(list_ids)
    if len(inv) != len(list(inventory_ids)) or len(lst) != len(list(list_ids)):
        raise InventoryError("duplicate id in a crosswalk input")
    return {"AGREE": sorted(inv & lst), "MISSING_FROM_LIST": sorted(inv - lst), "EXTRA_IN_LIST": sorted(lst - inv)}
