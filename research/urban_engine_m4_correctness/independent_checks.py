"""M4 independent checks: a second method for the geometry and the arithmetic of a generic-route run, and the
conservation rules (no region, support or bar counted twice or lost).

The second geometry method is shapely (GEOS), which the generic engine never uses: areas, differences, unions and
intersections are recomputed from the detected polygons. What is SHARED with the engine is stated per check: the
detected polygons themselves (the detection is not re-done here), and for arithmetic checks the convention values.

    checks(D, items, reg, conv, arch) -> rows {CHECK_ID, SUBJECT, METHOD, SHARED_WITH_ENGINE, ENGINE, INDEPENDENT,
                                               DIFF, TOLERANCE, RESULT, NOTE}
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from shapely.geometry import Polygon, box
from shapely.ops import unary_union


def _poly(p):
    g = Polygon(p)
    return g if g.is_valid else g.buffer(0)


def _row(cid, subject, method, shared, eng, ind, tol, note=""):
    diff = None if eng is None or ind is None else eng - ind
    ok = diff is not None and abs(diff) <= tol
    return {"CHECK_ID": cid, "SUBJECT": subject, "METHOD": method, "SHARED_WITH_ENGINE": shared,
            "ENGINE": eng, "INDEPENDENT": ind, "DIFF": diff, "TOLERANCE": tol,
            "RESULT": "PASS" if ok else ("NOT_COMPARABLE" if diff is None else "DIFFERS"), "NOTE": note}


def _face(f):
    g = Polygon(f["polygon"], [h for h in (f.get("hole_polygons") or []) if len(h) >= 3])
    return g if g.is_valid else g.buffer(0)


def slab_net_area(D):
    """IC-01: per sheet, the engine's net panel area (face less member overlap) against shapely's
    face - union(beam bands, column outlines); IC-02: the overlap the engine deducted against shapely's."""
    u2 = D["unit_m"] ** 2
    out = []
    for sid, rec in sorted(D["sheets"].items()):
        faces = [f for f in (rec.get("slab") or {}).get("faces", []) if f["class"] == "PANEL"]
        if not faces:
            continue
        members = [_poly(b["polygon"]) for b in rec.get("bands", []) if b["kind"] == "STRAIGHT"]
        members += [box(*c) for c in rec.get("slab_column_boxes", rec.get("column_boxes", []))]
        M = unary_union(members) if members else Polygon()
        straight = [f for f in faces if not f.get("arc_edges")]       # an arc-bounded face's ring is a chord polygon
        arcs = [f for f in faces if f.get("arc_edges")]
        shp = {f["face_id"]: _face(f) for f in faces}
        e_net = sum(f["area_m2"] for f in straight)
        i_net = sum(shp[f["face_id"]].difference(M).area * u2 for f in straight)
        e_ov = sum(f.get("member_overlap_m2", 0.0) for f in faces)
        i_ov = sum(shp[f["face_id"]].intersection(M).area * u2 for f in faces)
        out.append(_row("IC-01", f"{sid} slab panels: net area m2 (straight-edged)", "shapely (outer ring - hole "
                        "rings) - union(members)", "detected face / hole / band / column polygons", e_net, i_net,
                        max(0.01, 1e-4 * i_net), f"{len(straight)} panels; {len(arcs)} arc-bounded panels "
                        f"({sum(f['area_m2'] for f in arcs):.2f} m2) not compared: their ring is a chord polygon"))
        out.append(_row("IC-02", f"{sid} slab panels: member overlap m2", "shapely (face less holes) ∩ "
                        "union(members)", "detected polygons", e_ov, i_ov, 0.01,
                        "engine: inclusion-exclusion over overlapping members, hole parts excluded"))
    return out


def band_conservation(D):
    """IC-03: per sheet, the engine's sum of beam net plan areas against shapely's union(bands) - union(columns): a
    region in two bands (or a junction owned twice) makes the sum exceed the union."""
    u2 = D["unit_m"] ** 2
    out = []
    for sid, rec in sorted(D["sheets"].items()):
        beams = rec.get("beams") or []
        if not beams:
            continue
        straight = [b for b in beams if b.get("kind", "STRAIGHT") == "STRAIGHT" and b.get("polygon")]
        U = unary_union([_poly(b["polygon"]) for b in straight])
        C = unary_union([box(*c) for c in rec.get("column_boxes", [])] or [Polygon()])
        out.append(_row("IC-03", f"{sid} beam bands: net plan m2 (straight)", "shapely union(bands) - union(columns)",
                        "detected band and column polygons", sum(b["net_plan_m2"] for b in straight),
                        U.difference(C).area * u2, max(0.02, 2e-3 * U.area * u2),
                        f"{len(straight)} bands; footing overlap of straps is outside this check"))
    return out


def footing_volumes(D, items, conv):
    """IC-04: footing concrete from the outline (shapely area of the drawn polygon, or its box) x the printed depth;
    a label-only footing from the schedule L x W x D; a footing labelled with two types from the candidate the
    convention FOOTING_LABEL_CONFLICT picks."""
    u2 = D["unit_m"] ** 2
    boxes = {f["member_id"]: f for r in D["sheets"].values() for f in r.get("footings", [])}
    pick = max if (conv.base("FOOTING_LABEL_CONFLICT") if "FOOTING_LABEL_CONFLICT" in conv.items else "LARGER") \
        == "LARGER" else min
    e = i_ = 0.0
    n, worst, worst_id = 0, 0.0, ""
    for it in items:
        if it["family"] != "FOOTINGS" or it["trade"] != "CONCRETE" or it["category"] != "PROVISIONAL":
            continue
        d = it.get("dimensions") or {}
        f = boxes.get(it["component_id"]) or {}
        dims = d.get("schedule_m") or f.get("schedule_m")
        if f.get("state") == "LABEL_TYPE_CONFLICT" and f.get("candidates"):
            v = pick(c["schedule_m"][0] * c["schedule_m"][1] * c["schedule_m"][2] for c in f["candidates"].values()
                     if c.get("schedule_m"))
        elif not dims or len(dims) < 3:
            continue
        elif f.get("state") == "CONFIRMED" and (f.get("polygon") or f.get("box")):
            g = _poly(f["polygon"]) if f.get("polygon") else box(*f["box"])
            v = g.area * u2 * dims[2]
        else:
            v = dims[0] * dims[1] * dims[2]
        v -= (d.get("overlap_deducted_m3") or 0.0)
        e += it["base"]
        i_ += v
        n += 1
        if abs(it["base"] - v) > worst:
            worst, worst_id = abs(it["base"] - v), it["component_id"]
    return [_row("IC-04", "footings: concrete m3", "outline area (shapely) x printed depth; schedule L x W x D; the "
                 "conflict candidate by convention", "the footing's type binding and printed depth", e, i_,
                 max(0.01, 1e-3 * i_), f"{n} footings; worst single difference {worst:.4f} m3 ({worst_id})")]


def cb_bars(D, conv):
    """IC-05: every continuous-beam bar group recomputed by hand from its line's spans: bottom = clear span +
    extension each side (support width + extension at an interior support, anchorage at an end), support top =
    support width + fraction x span basis each side; mass = count x length x d^2 / 162. IC-06: the mass shared to
    the pieces equals the mass of the groups (per line)."""
    anch = conv.base("BEAM_BAR_ANCHORAGE_D")
    out = []
    n = bad = 0
    worst = 0.0
    tot_g = tot_p = 0.0
    for rec in D["sheets"].values():
        for ln in rec.get("cb_lines", []):
            for g in ln.get("groups") or []:
                if g["role"] == "STIRRUP" or not g.get("length_m"):
                    continue
                kg = g["count"] * g["length_m"][1] * g["dia_mm"] ** 2 / 162.0
                n += 1
                worst = max(worst, abs(kg - (g.get("mass_kg") or (0, 0, 0))[1]))
                bad += abs(kg - (g.get("mass_kg") or (0, 0, 0))[1]) > 1e-6
                tot_g += (g.get("mass_kg") or (0, 0, 0))[1]
            for g in ln.get("groups") or []:
                if g["role"] == "BOTTOM" and g.get("length_m"):
                    s = next((x for x in ln["spans"] if x["index"] == g["k"]), None)
                    if s:
                        L = g["length_m"][1]
                        # the span's own clear length is inside the bar: the bar is never shorter than the span
                        bad += L + 1e-9 < s["clear_m"]
    out.append(_row("IC-05", "continuous-beam bar groups: mass = count x length x d^2/162", "hand arithmetic per "
                    "group; bottom bars never shorter than their clear span", "the group lengths (the convention "
                    "values: anchorage %g d)" % anch, float(bad), 0.0, 0.0, f"{n} groups; worst {worst:.2e} kg"))
    return out


def cb_allocation(D, items):
    out = []
    pieces = defaultdict(float)
    for i in items:
        if i["trade"] == "REINFORCEMENT" and i["category"] == "PROVISIONAL" and ":CB_" in i["item_id"]:
            pieces[i["component_id"].split(":")[-1]] += i["base"]
        elif i["trade"] == "REINFORCEMENT" and i.get("blocker") == "CB_SPAN_SECTION_UNRESOLVED":
            pieces[i["component_id"].split(":")[-1]] += (i.get("dimensions") or {}).get("allocated_kg_base", 0.0)
    for rec in D["sheets"].values():
        for ln in rec.get("cb_lines", []):
            if not ln.get("groups"):
                continue
            g = sum((x.get("mass_kg") or (0, 0, 0))[1] for x in ln["groups"])
            p = sum(pieces.get(pid, 0.0) for pid in {q for s in ln["spans"] for q in s["pieces"]})
            out.append(_row("IC-06", f"{ln['line_id']}: bar mass shared to the pieces", "sum over piece items (measured "
                            "+ held as exposure on an unresolved span) vs sum over physical groups", "allocation shares",
                            p, g, 1e-6))
    return out


def item_conservation(items, reg):
    """IC-07: unique item ids; one measured concrete item per component; every concrete component in the rebar
    register; no component both measured and unresolved."""
    ids = Counter(i["item_id"] for i in items)
    dup = sum(1 for v in ids.values() if v > 1)
    conc = defaultdict(Counter)
    for i in items:
        if i["trade"] == "CONCRETE":
            conc[i["component_id"]][i["category"]] += 1
    twice = sum(1 for c in conc.values() if c["PROVISIONAL"] + c["VERIFIED"] > 1)
    both = sum(1 for c in conc.values() if (c["PROVISIONAL"] or c["VERIFIED"]) and c["UNRESOLVED"])
    regd = {r["COMPONENT_ID"] for r in reg}
    noreg = sum(1 for k in conc if k not in regd)
    return [_row("IC-07a", "duplicate item ids", "count", "none", float(dup), 0.0, 0.0),
            _row("IC-07b", "components with two measured concrete items", "count", "none", float(twice), 0.0, 0.0),
            _row("IC-07c", "components both measured and unresolved", "count", "none", float(both), 0.0, 0.0),
            _row("IC-07d", "concrete components without a rebar register row", "count", "none", float(noreg), 0.0,
                 0.0)]


def blinding(D, items, conv):
    """IC-08 / IC-09: the blinding plan is the union of the placed footing outlines (+ p) and beam strips (band +- p):
    the engine's inclusion-exclusion union against shapely's union of the same outlines (the outline construction
    is the engine's generic_route._strip_outline; the union is computed independently)."""
    from engine.source import generic_route as GR
    out = []
    ov = D.get("blinding_overlap") or {}
    if "BLINDING_PROJECTION_M" not in conv.items or ov.get("state") != "REGISTERED" or "placed_union_m2" not in ov:
        return out
    fp = next((r for r in D["sheets"].values() if r["sheet"]["role"] == "FOUNDATION_PLAN"), None)
    u = D["unit_m"]
    p = conv.base("BLINDING_PROJECTION_M") / u
    placed = [f["box"] for f in fp.get("footings", []) if f.get("box") and f.get("drawn_m")]
    F = unary_union([box(b[0] - p, b[1] - p, b[2] + p, b[3] + p) for b in placed])
    S = []
    for sid, rec in D["sheets"].items():
        if sid not in ov["shift"]:
            continue
        bp = {x["band_id"]: x for x in rec.get("bands", [])}
        src = [(b, bp.get(b["band_id"])) for b in rec.get("beams", [])] if rec["sheet"]["role"] == "GROUND_BEAM_PLAN" \
            else []
        src += [(b, b if b.get("u") else None) for b in (rec.get("straps") or {}).get("bands", [])]
        for b, band in src:
            q = GR._strip_outline(b, band, p, *ov["shift"][sid])
            if q:
                S.append(_poly(q))
    U = unary_union([F] + S)
    out.append(_row("IC-08", "footing blinding: union of the placed footing outlines + p, m2", "shapely union",
                    "footing outlines, projection convention", ov["placed_footing_union_m2"][1], F.area * u * u, 0.01,
                    f"{len(placed)} placed outlines"))
    out.append(_row("IC-09", "all blinding: union of footing outlines and beam strips, m2", "shapely union",
                    "outline construction (generic_route._strip_outline), registration shift",
                    ov["placed_union_m2"][1], U.area * u * u, 0.01,
                    f"{len(S)} strips; at most {ov.get('most_outlines_at_one_place')} outlines meet at one place"))
    return out


def lintel_arith(arch, items, conv):
    """IC-10: lintel concrete = wall thickness x printed depth x (opening + a bearing per masonry jamb)."""
    bear = conv.base("LINTEL_BEARING_M") if "LINTEL_BEARING_M" in conv.items else None
    e = i_ = 0.0
    n = 0
    ops = {f"LINTELS:{st}:{o['opening_id']}": o for st, L in ((arch or {}).get("lintels") or {}).items()
           for o in L["openings"]}
    for it in items:
        if it["family"] != "LINTELS" or it["trade"] != "CONCRETE" or it["category"] != "PROVISIONAL":
            continue
        o, d = ops.get(it["component_id"]), it.get("dimensions") or {}
        if not o or bear is None:
            continue
        ends = sum(1 for j in (o["start_jamb"], o["end_jamb"]) if j != "COLUMN_JAMB")
        e += it["base"]
        i_ += o["wall_t_m"] * d["D_m"] * (o["width_m"] + ends * bear)
        n += 1
    return [_row("IC-10", "lintels: concrete m3", "hand arithmetic from the opening and the schedule depth",
                 "the opening census and the row binding", e, i_, 1e-6, f"{n} lintels")] if n else []


def gb_exterior_arith(D, items, conv, arch):
    """IC-11: an evidenced exterior ground beam = net plan x (inside floor level - build-up - outer ground)."""
    bands = (arch or {}).get("bands") or {}
    net = {f"GROUND_BEAMS:{r['sheet']['storey']}:{b['band_id']}": (b["net_plan_m2"], b["band_id"])
           for r in D["sheets"].values() if r["sheet"]["role"] == "GROUND_BEAM_PLAN" for b in r.get("beams", [])}
    bu, g = conv.base("GB_EXTERIOR_BUILDUP_M"), conv.base("OUTER_GROUND_LEVEL_M")
    e = i_ = 0.0
    n = 0
    for it in items:
        if it["family"] != "GROUND_BEAMS" or it["trade"] != "CONCRETE" or it["blocker"] != "GB_EXTERIOR_DEPTH":
            continue
        a, bid = net.get(it["component_id"], (None, None))
        fl = (bands.get(bid) or {}).get("floor_level_m")
        if a is None or fl is None:
            continue
        e += it["base"]
        i_ += a * (fl - bu - g)
        n += 1
    return [_row("IC-11", "evidenced exterior ground beams: concrete m3", "net plan x (inside level - build-up - "
                 "outer ground)", "net plan areas and the level reading", e, i_, 1e-6, f"{n} bands")] if n else []


def checks(D, items, reg, conv, arch=None):
    return (slab_net_area(D) + band_conservation(D) + footing_volumes(D, items, conv) + cb_bars(D, conv) +
            cb_allocation(D, items) + item_conservation(items, reg) + blinding(D, items, conv) +
            lintel_arith(arch, items, conv) + gb_exterior_arith(D, items, conv, arch))
