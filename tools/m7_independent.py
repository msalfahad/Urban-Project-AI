"""M7 PER-ITEM INDEPENDENT CHECKS - a second method for each measured concrete item of a route-G run, so the release
policy (engine.source.quantity_release) can tell a checked quantity from an unchecked one.

    item_checks(D, items) -> {item_id: {result, method, shared, engine, independent, tolerance, note}}

The second geometry method is shapely (GEOS), which the generic route never uses. What each check SHARES with the
engine is stated: the detected polygons (detection is not re-done), the printed values and the conventions' depth.
    FOOTINGS   drawn outline area (shapely) x printed depth when the outline confirmed the type; otherwise the
               schedule L x W x D (ARITHMETIC: shares every value - a formula check, not a geometry check)
    SLABS      shapely (face less holes) - union(beam bands, column outlines) x printed / sheet thickness, less a
               drawn flight's footprint the engine held unresolved
    BEAMS      shapely (band polygon - union(column outlines)) - the junction squares the engine gave another band,
               x the depth the item used; arc bands are NOT_COMPARABLE (their ring is a chord polygon)
    COLUMNS    B x H x storey height (ARITHMETIC)
PASS within max(1 %, 0.001 m3); DIFFERS otherwise; NOT_COMPARABLE when the geometry is not found or not straight.
"""

from __future__ import annotations

from collections import defaultdict

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

TOL_REL, TOL_ABS = 0.01, 0.001


def _poly(p):
    g = Polygon(p)
    return g if g.is_valid else g.buffer(0)


def _face(f):
    g = Polygon(f["polygon"], [h for h in (f.get("hole_polygons") or []) if len(h) >= 3])
    return g if g.is_valid else g.buffer(0)


def _row(method, shared, eng, ind, note=""):
    if eng is None or ind is None:
        return {"result": "NOT_COMPARABLE", "method": method, "shared": shared, "engine": eng, "independent": ind,
                "tolerance": None, "note": note}
    tol = max(TOL_REL * abs(ind), TOL_ABS)
    return {"result": "PASS" if abs(eng - ind) <= tol else "DIFFERS", "method": method, "shared": shared,
            "engine": round(eng, 6), "independent": round(ind, 6), "tolerance": round(tol, 6), "note": note}


def _sheets_by_storey(D):
    out = defaultdict(list)
    for s in D["model"]["sheets"]:
        if s["sheet_id"] in D["sheets"]:
            out[s.get("storey")].append(s["sheet_id"])
    return out


def item_checks(D, items):
    u = D["unit_m"]
    u2 = u * u
    by_st = _sheets_by_storey(D)
    footings = {f["member_id"]: f for r in D["sheets"].values() for f in r.get("footings", [])}
    stair_hull = {i["component_id"][:-len(":STAIR")]: (i.get("dimensions") or {}).get("area_m2") or 0.0
                  for i in items if i["item_id"].endswith(":STAIR_FOOTPRINT")}
    members_cache = {}

    def members(sid):
        if sid not in members_cache:
            rec = D["sheets"][sid]
            m = [_poly(b["polygon"]) for b in rec.get("bands", []) if b.get("kind") == "STRAIGHT"]
            m += [box(*c) for c in rec.get("slab_column_boxes", rec.get("column_boxes", []))]
            members_cache[sid] = unary_union(m) if m else Polygon()
        return members_cache[sid]

    out = {}
    for it in items:
        if it["trade"] != "CONCRETE" or it["category"] not in ("PROVISIONAL", "VERIFIED") or it.get("base") is None:
            continue
        fam, d, cid = it["family"], it.get("dimensions") or {}, it.get("component_id") or ""
        if fam == "FOOTINGS":
            f = footings.get(cid) or {}
            dims = d.get("schedule_m") or f.get("schedule_m")
            if not dims or len(dims) < 3:
                out[it["item_id"]] = _row("NONE", "", it["base"], None, "no printed L x W x D")
                continue
            if f.get("state") == "CONFIRMED" and (f.get("polygon") or f.get("box")):
                g = _poly(f["polygon"]) if f.get("polygon") else box(*f["box"])
                v = g.area * u2 * dims[2] - (d.get("overlap_deducted_m3") or 0.0)
                out[it["item_id"]] = _row("SHAPELY_OUTLINE_x_PRINTED_DEPTH", "outline polygon, printed depth",
                                          it["base"], v)
            else:
                v = dims[0] * dims[1] * dims[2] - (d.get("overlap_deducted_m3") or 0.0)
                out[it["item_id"]] = _row("ARITHMETIC", "every value", it["base"], v)
        elif fam in ("SLABS", "GROUND_SLAB") and ":SITE-" in cid:
            st, site = it.get("storey"), cid.split(":")[-1]
            hit = [(sid, f) for sid in by_st.get(st, ()) for f in (D["sheets"][sid].get("slab") or {}).get("faces", [])
                   if f["face_id"] == site]
            if len(hit) != 1 or not d.get("t_m"):
                out[it["item_id"]] = _row("SHAPELY_FACE_LESS_MEMBERS", "", it["base"], None,
                                          "face not found once on the storey's plans" if len(hit) != 1 else
                                          "no thickness")
                continue
            sid, f = hit[0]
            if f.get("arc_edges"):
                out[it["item_id"]] = _row("SHAPELY_FACE_LESS_MEMBERS", "", it["base"], None,
                                          "arc-bounded face: its ring is a chord polygon")
                continue
            if d.get("recovered_from_open_boundary") or f["class"] != "PANEL":
                out[it["item_id"]] = _row("SHAPELY_FACE_LESS_MEMBERS", "", it["base"], None,
                                          f"{f['class']} face (recovered panel): another formula")
                continue
            a = _face(f).difference(members(sid)).area * u2 - stair_hull.get(cid, 0.0)
            out[it["item_id"]] = _row("SHAPELY_FACE_LESS_MEMBERS", "face / hole / band / column polygons, thickness",
                                      it["base"], a * d["t_m"])
        elif fam == "BEAMS" and cid.count(":") >= 2:
            st, bid = it.get("storey"), cid.split(":", 2)[2]
            hit = [(sid, b) for sid in by_st.get(st, ()) for b in D["sheets"][sid].get("bands", [])
                   if b["band_id"] == bid]
            if len(hit) != 1 or not d.get("depth_m") or d.get("net_plan_m2") in (None, 0):
                out[it["item_id"]] = _row("SHAPELY_BAND_LESS_COLUMNS", "", it["base"], None,
                                          "band not found once on the storey's plans" if len(hit) != 1 else
                                          "no depth / plan")
                continue
            sid, b = hit[0]
            if b.get("kind") != "STRAIGHT":
                out[it["item_id"]] = _row("SHAPELY_BAND_LESS_COLUMNS", "", it["base"], None,
                                          "arc band: its ring is a chord polygon")
                continue
            cols = [box(*c) for c in D["sheets"][sid].get("column_boxes", [])]
            g = _poly(b["polygon"])
            if cols:
                g = g.difference(unary_union(cols))
            q = [r for r in D["sheets"][sid].get("beams") or [] if r.get("band_id") == bid]
            junc = sum(x["area_m2"] for x in (q[0].get("junction_deductions") or [])) if q else 0.0
            plan = g.area * u2 - junc
            depth = it["base"] / d["net_plan_m2"]          # the depth reading the item used (H or H + t)
            out[it["item_id"]] = _row("SHAPELY_BAND_LESS_COLUMNS", "band / column polygons, junction ownership, "
                                      "the item's depth reading", it["base"], plan * depth,
                                      "the depth is the item's own (base / plan); the check is on the plan area")
        elif fam == "COLUMNS":
            sec, h = d.get("section_m") or [None, None], d.get("height_m")
            if not (sec and sec[0] and sec[1] and h):
                out[it["item_id"]] = _row("ARITHMETIC", "", it["base"], None, "no section / height")
                continue
            out[it["item_id"]] = _row("ARITHMETIC", "every value", it["base"], sec[0] * sec[1] * h)
    return out


def summary(checks):
    out = defaultdict(lambda: defaultdict(int))
    for k, c in checks.items():
        out[c["method"]][c["result"]] += 1
    return {m: dict(v) for m, v in sorted(out.items())}
