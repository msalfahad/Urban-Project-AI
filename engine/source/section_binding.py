"""SECTION BINDING V1 (T-013) - bind the level bands of sections / elevations to the plan floors, and report per floor
the level KIND of every printed level with its source (owner answer Q-14, 2026-10-19). Read-only, additive: no method
version reads this module yet, so no quantity changes; a later method version wires it (UP-HGT-001 rank 3 evidence).

Why: ARCH_TAKEOFF_V2.8 (arch_v28.read_views) binds a band only when a floor name lies INSIDE the band (by a level-text
y fit) or an F.F.L.-labelled level equals the plan's dominant level. Real sheets break both: the floor name sits beside
or under its level tag (outside the band), the level marks are bare numbers ('+5.50', '%%p0.00', no F.F.L. word), the
upper levels are printed only as a vertical dimension chain, and a storey can have two floor levels (a split level).
The development villa's elevations bound no band at all (FACADE / MASONRY: "no section band of this floor").

Binding (a band = one floor level of one view), in this order; each binding keeps its evidence:
  1 NAME_NEAREST_LEVEL_LABEL   a floor-name text (GROUND FLOOR / FIRST FLOOR / الدور الاول ...) binds to the level
                               label nearest to it (any direction, within NAME_REACH_M; a second label of another
                               value within NAME_AMBIGUOUS_M of the same distance -> NAME_AMBIGUOUS, no binding).
                               Level cross-check: when the plan prints room levels for that floor, the label value
                               must be one of them, else NAME_LEVEL_CONFLICT (no binding, a finding).
  2 LEVEL_EQUALS_A_ROOM_LEVEL  a level of the view (a labelled F.F.L., a bare mark, or a dimension-chain end once the
                               view is calibrated) equals a level printed INSIDE a labelled room of exactly one plan
                               floor. A value printed in rooms of two floors binds nothing (VALUE_ON_TWO_FLOORS).
                               A bare dimension end binds by value only: its evidence says UNLABELLED_DIMENSION_END
                               (an unrelated line at the same level, e.g. a pool rim, can carry the same value).
  3 LEVEL_EQUALS_THE_PLAN_DOMINANT_LEVEL   only for a floor whose rooms print no level (V2.8's plan-level binding).
  A floor's own levels are the level texts printed inside its identified rooms (a room with a kind; EXTERIOR / VOID /
  SHAFT and unidentified spaces do not count): a storey with two such values is a SPLIT_LEVEL floor (each value is a zone,
  with the rooms that print it). Only when no room prints a level is the plan's dominant level used, and then as
  PLAN_DOMINANT_LEVEL (flagged); a dominant level that is not one of the room levels is a finding
  (PLAN_DOMINANT_LEVEL_IS_NOT_A_ROOM_LEVEL: e.g. the ground-plot corner marks outnumber the floor's own marks).

Calibration of a view (needed only for the dimension-chain ends): the view is full size, y up. The datum y0 (level
0.00) is the one that puts the most distinct level-text values on a vertical dimension end (|end - (y0 + v/unit)| <=
AGREE_M, the text within TEXT_REACH_M of that line); at least two values, and no second datum with the same count.
Every end of a usable vertical dimension (dimension_evidence.resolve: shown value = defpoints) then has a level.
A rotated, mirrored-upside-down or undimensioned view is not calibrated (VIEW_NOT_CALIBRATED): its texts still bind
by value, its dimension ends give nothing.

Per floor (plan order, lowest first) the report gives, each with state and source, never a guessed value:
  ffl_zones          the floor's levels (PRINTED in rooms) and which views confirm each
  floor_to_floor     PRINTED_DIMENSION when a usable vertical dimension joins this floor's level to the next floor's
                     level; else DERIVED_FROM_PRINTED_LEVELS (next level - this level) only when both floors have ONE
                     zone; else HELD (SPLIT_LEVEL_ZONE). Never a wall height (Q-14).
  level_above        for a zone with no floor-to-floor (the top floor, a split-level zone): the levels a printed
                     dimension reaches from it, kind NOT printed -> HELD with the candidates (LEVEL_ABOVE_KIND_NOT_PRINTED)
  soffit / false_ceiling / slab_top
                     U/S SLAB, F.C.L., T.O.S. labelled levels of a bound view between this floor's level and the next
                     (heights above the F.F.L.); a floor with two zones in that view -> HELD (SPLIT_LEVEL_ZONE)
  slab_thickness     T.O.S. of the next floor - U/S SLAB of this floor when both are printed (PRINTED_LEVELS); else
                     the owner rule Q-14 0.16 m (OWNER_RULE, structural slab only: never for stairs, balconies,
                     depressed slabs, landings or special elements)
  clear_height       a printed CLEAR HEIGHT / C.H. text in the band only; else NOT_PRINTED
Never: an assumed floor build-up or false-ceiling depth subtracted (Q-14); a floor-to-floor taken as a wall height;
a missing value as 0. Project-agnostic: no layer names, coordinates or project values. Stdlib only.

    floor_levels(texts, plan_floors)                  -> {floor: {"zones": [...], "how", "findings"}}
    bind(texts, dims, header_dimlfac, frames, unit_m, plan_floors) -> {"policy", "views", "floors", "findings"}
plan_floors: [{"floor", "box", "dominant_level_m", "rooms": [{"room_id", "kind", "polygon"}]}] (any order;
sorted by storey order). dims: tools/arch_dimensions records.
"""

from __future__ import annotations

import math
import re

from engine.source import arch_v28 as V28
from engine.source import dimension_evidence as DE
from engine.source import storey_vocab as SV

POLICY_ID = "SECTION_BINDING_V1"
OWNER_SLAB_M = 0.16                  # owner Q-14: the structural slab is 0.16 m unless a drawing or detail says otherwise
AGREE_M = V28.AGREE_M                # two levels agree within 5 mm
TEXT_REACH_M = V28.TAG_REACH_M       # a level text stands within 1.20 m of its level line (tag above / below the line)
NAME_REACH_M = 3.0                   # a floor name stands within 3.0 m of its level label
NAME_AMBIGUOUS_M = 0.30              # ... and no other label value is within 0.30 m of the same distance
NOT_A_ROOM = (None, "EXTERIOR", "VOID", "SHAFT")
ORDER = SV.ORDER

# floor names written in a section band (no PLAN word): English (arch_v28.FLOOR_NAMES) + Arabic (folded forms)
_AR_ORD = ("الاول", "الثاني", "الثالث")
BAND_NAMES = tuple((fl, rx, False) for fl, rx in V28.FLOOR_NAMES) + (
    ("BASEMENT", r"السرداب|القبو|البدروم", True), ("GF", r"(الدور|الطابق)\s*الارضي", True),
    ("MEZZANINE", r"الميزانين", True),
    ("1F", r"(الدور|الطابق)\s*الاول", True), ("2F", r"(الدور|الطابق)\s*الثاني(?!\s*عشر)", True),
    ("3F", r"(الدور|الطابق)\s*الثالث(?!\s*عشر)", True), ("ROOF", r"السطح", True))
_TITLE_WORDS = re.compile(r"PLAN|SECTION|ELEVATION|مسقط|قطاع|واجه")
CLEAR_RE = re.compile(r"(?:CLEAR\s+HEIGHT|\bC\.?\s?H\b\.?)\s*[=:]?\s*(" + V28._N + r")" + r"(?:" + V28._U + r")?")


def _norm_level_text(s):
    return (s or "").replace("%%p", "±").replace("%%P", "±")


def level_of(text):
    """(kind, value_m) of a level text (arch_v28.parse_level after decoding the CAD '%%p' plus-minus sign)."""
    return V28.parse_level(_norm_level_text(text))


def floor_name(text):
    """the storey a band name names, or None (a title, a level or a long note is not a band name)."""
    raw = text or ""
    if len(raw) > 40 or level_of(raw) or _TITLE_WORDS.search(V28.norm(raw)) or _TITLE_WORDS.search(SV.fold(raw)):
        return None
    u, f = V28.norm(raw), SV.fold(raw)
    for fl, rx, arabic in BAND_NAMES:
        if re.search(rx, f if arabic else u):
            return fl
    return None


def _src(t, **kw):
    return dict({"text_id": t.get("id"), "text": t.get("value"), "layer": t.get("layer")}, **kw)


# ============================================================================================== plan floor levels
def floor_levels(texts, plan_floors):
    """-> {floor: {"zones": [{"level_m", "rooms": [room ids], "source": [...]}], "how", "findings"}}."""
    out = {}
    lv = [(t, level_of(t["value"])) for t in texts]
    lv = [(t, p[1]) for t, p in lv if p and p[0] in ("FFL", "MARK")]
    for pf in plan_floors:
        b = pf.get("box")
        zones = {}
        for r in pf.get("rooms") or ():
            if r.get("kind") in NOT_A_ROOM:
                continue
            poly = r["polygon"]
            for t, v in lv:
                if b and not V28._in_box((t["x"], t["y"]), b):
                    continue
                if V28._inside((t["x"], t["y"]), poly):
                    z = zones.setdefault(round(v, 3), {"level_m": round(v, 3), "rooms": [], "source": []})
                    if r["room_id"] not in z["rooms"]:
                        z["rooms"].append(r["room_id"])
                    z["source"].append(_src(t, room_id=r["room_id"]))
        findings = []
        dom = pf.get("dominant_level_m")
        if zones:
            how = "ROOM_LEVELS" if len(zones) == 1 else "SPLIT_LEVEL"
            if dom is not None and all(abs(dom - v) > AGREE_M for v in zones):
                findings.append({"code": "PLAN_DOMINANT_LEVEL_IS_NOT_A_ROOM_LEVEL", "floor": pf["floor"],
                                 "dominant_level_m": dom, "room_levels_m": sorted(zones)})
        elif dom is not None:
            zones = {round(dom, 3): {"level_m": round(dom, 3), "rooms": [], "source": [{"plan": "DOMINANT_LEVEL"}]}}
            how = "PLAN_DOMINANT_LEVEL"
            findings.append({"code": "NO_LEVEL_IN_A_ROOM", "floor": pf["floor"], "dominant_level_m": dom})
        else:
            how = "NOT_PRINTED"
            findings.append({"code": "FLOOR_LEVEL_NOT_PRINTED", "floor": pf["floor"]})
        out[pf["floor"]] = {"zones": [zones[k] for k in sorted(zones)], "how": how, "findings": findings}
    return out


# ============================================================================================== one view
def _vertical_dims(dims, header, unit_m, box):
    out = []
    for d in dims:
        r = DE.resolve(d, header, unit_m)
        if not r.get("usable") or not r.get("dir"):
            continue
        if abs(r["dir"][0]) > 1e-6:                   # not vertical (a rotated view's level dimensions are not read)
            continue
        p2, p3 = r["p2"], r["p3"]
        mid = ((p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2)
        if not V28._in_box(mid, box):
            continue
        lo, hi = sorted((p2[1], p3[1]))
        out.append({"handle": r.get("handle"), "layer": r.get("layer"), "lo_y": lo, "hi_y": hi, "x": mid[0],
                    "value_m": round(r["value_du"] * unit_m, 6)})
    return out


def _calibrate(levels, vdims, unit_m):
    """the datum y0 that puts the most distinct level-text values on a dimension end -> (y0, matched) or None."""
    k = 1.0 / unit_m
    tol, reach = AGREE_M * k, TEXT_REACH_M * k
    ends = sorted({round(y, 6) for d in vdims for y in (d["lo_y"], d["hi_y"])})
    if not ends or not levels:
        return None, "NO_VERTICAL_DIMENSION" if not ends else "NO_LEVEL_TEXT"

    def matched(y0):
        vals = set()
        for x in levels:
            line = y0 + x["value_m"] * k
            if abs(x["y"] - line) <= reach and any(abs(e - line) <= tol for e in ends):
                vals.add(round(x["value_m"], 3))
        return vals

    cands = []
    for x in levels:
        for e in ends:
            if abs(x["y"] - e) <= reach:
                y0 = e - x["value_m"] * k
                if not any(abs(y0 - c) <= tol for c in cands):
                    cands.append(y0)
    scored = sorted(((len(matched(y0)), y0) for y0 in cands), key=lambda s: -s[0])
    if not scored or scored[0][0] < 2:
        return None, "FEWER_THAN_TWO_LEVELS_ON_A_DIMENSION_END"
    best = [s for s in scored if s[0] == scored[0][0]]
    if len(best) > 1:
        return None, "TWO_DATUMS_FIT_EQUALLY"
    return best[0][1], sorted(matched(best[0][1]))


def read_view(view_id, kind, title, box, texts, vdims, unit_m):
    """the levels of one view: its level texts, its dimension-chain ends (once calibrated), its floor names."""
    k = 1.0 / unit_m
    tx = [t for t in texts if V28._in_box((t["x"], t["y"]), box)]
    levels = []
    for t in tx:
        p = level_of(t["value"])
        if p:
            levels.append({"kind": p[0], "value_m": p[1], "x": t["x"], "y": t["y"], "text": t})
    names = [(floor_name(t["value"]), t) for t in tx]
    names = [(f, t) for f, t in names if f]
    y0, why = _calibrate(levels, vdims, unit_m)
    view = {"view_id": view_id, "kind": kind, "title": _src(title), "box": box,
            "levels": [{"kind": x["kind"], "value_m": x["value_m"], "source": "TEXT", "text": _src(x["text"])}
                       for x in levels],
            "floor_names": [{"floor": f, "text": _src(t)} for f, t in names],
            "calibration": ({"state": "CALIBRATED", "datum_y": round(y0, 6), "values_on_dimension_ends": why}
                            if y0 is not None else {"state": "VIEW_NOT_CALIBRATED", "why": why}),
            "dimensions": []}
    if y0 is not None:
        for d in vdims:
            lo, hi = round((d["lo_y"] - y0) / k, 4), round((d["hi_y"] - y0) / k, 4)
            view["dimensions"].append(dict(d, lo_m=lo, hi_m=hi))
        known = {round(x["value_m"], 3) for x in levels}
        ends = {}
        for d in view["dimensions"]:
            for v in (d["lo_m"], d["hi_m"]):
                if not any(abs(v - q) <= AGREE_M for q in known):
                    ends.setdefault(round(v, 3), []).append(d["handle"])
        for v, hs in sorted(ends.items()):
            view["levels"].append({"kind": "DIMENSION_END", "value_m": v, "source": "DIMENSION_CHAIN",
                                   "dimensions": sorted(set(hs))})
    view["clear_heights"] = [{"value_m": v, "how": how, "text": src,
                              "at_level_m": (round((src_y - y0) / k, 4) if y0 is not None else None)}
                             for v, how, src, src_y in clear_heights(tx, box, unit_m)]
    return view, levels, names


def _bind_view(view, levels, names, fl_levels, unit_m):
    k = 1.0 / unit_m
    bands, findings = {}, []
    # 1 floor name -> nearest level label, cross-checked with the floor's room levels
    for fl, t in names:
        ds = sorted((math.hypot(x["x"] - t["x"], x["y"] - t["y"]) / k, i) for i, x in enumerate(levels))
        ds = [(d, i) for d, i in ds if d <= NAME_REACH_M]
        if not ds:
            findings.append({"code": "NAME_WITHOUT_A_LEVEL_LABEL", "view": view["view_id"], "floor": fl,
                             "text": _src(t)})
            continue
        d0, i0 = ds[0]
        v0 = levels[i0]["value_m"]
        rival = [levels[i]["value_m"] for d, i in ds[1:] if d - d0 <= NAME_AMBIGUOUS_M
                 and abs(levels[i]["value_m"] - v0) > AGREE_M]
        if rival:
            findings.append({"code": "NAME_AMBIGUOUS", "view": view["view_id"], "floor": fl, "text": _src(t),
                             "values_m": sorted({v0, *rival})})
            continue
        own = [z["level_m"] for z in (fl_levels.get(fl) or {}).get("zones") or ()]
        if own and all(abs(v0 - z) > AGREE_M for z in own):
            findings.append({"code": "NAME_LEVEL_CONFLICT", "view": view["view_id"], "floor": fl, "text": _src(t),
                             "label_value_m": v0, "plan_room_levels_m": own})
            continue
        key = round(v0, 3)
        prev = bands.get(key)
        if prev and prev["floor"] != fl:
            findings.append({"code": "TWO_NAMES_ON_ONE_LEVEL", "view": view["view_id"], "ffl_m": key,
                             "floors": sorted({prev["floor"], fl})})
            bands[key] = dict(prev, floor=None, binding="CONFLICT")
            continue
        bands[key] = {"ffl_m": key, "floor": fl, "binding": "NAME_NEAREST_LEVEL_LABEL",
                      "evidence": {"name": _src(t), "label": _src(levels[i0]["text"]),
                                   "distance_m": round(d0, 3),
                                   "plan_check": "AGREES_WITH_A_ROOM_LEVEL" if own else "NO_ROOM_LEVEL_ON_THE_PLAN"}}
    # 2 a level of the view equals a room level of exactly one floor
    for x in view["levels"]:
        if x["kind"] not in ("FFL", "MARK", "DIMENSION_END"):
            continue
        key = round(x["value_m"], 3)
        if key in bands:
            continue
        hits = [fl for fl, f in fl_levels.items() if f["how"] != "NOT_PRINTED"
                and any(abs(z["level_m"] - key) <= AGREE_M for z in f["zones"])]
        if len(hits) > 1:
            findings.append({"code": "VALUE_ON_TWO_FLOORS", "view": view["view_id"], "value_m": key,
                             "floors": sorted(hits)})
            continue
        if hits:
            how = ("LEVEL_EQUALS_THE_PLAN_DOMINANT_LEVEL" if fl_levels[hits[0]]["how"] == "PLAN_DOMINANT_LEVEL" else
                   "LEVEL_EQUALS_A_ROOM_LEVEL")
            bands[key] = {"ffl_m": key, "floor": hits[0], "binding": how,
                          "evidence": {"level": x.get("text") or {"dimensions": x.get("dimensions")},
                                       "level_kind_printed": ("UNLABELLED_DIMENSION_END" if x["kind"] == "DIMENSION_END"
                                                              else x["kind"])}}
    view["bands"] = [bands[k_] for k_ in sorted(bands)]
    return findings


# ============================================================================================== all views, per floor
def bind(texts, dims, header_dimlfac, frames, unit_m, plan_floors):
    pfs = sorted(plan_floors, key=lambda p: ORDER.get(p["floor"], 10 ** 6))
    order = [p["floor"] for p in pfs]
    fl_levels = floor_levels(texts, pfs)
    findings = [f for v in fl_levels.values() for f in v["findings"]]
    views = []
    for fr in frames:
        box = fr["box"]
        tx = [t for t in texts if V28._in_box((t["x"], t["y"]), box)]
        titles = [t for t in tx if V28.VIEW_TITLE_RE.search(V28.norm(t["value"])) and not level_of(t["value"])]
        if not titles:
            continue
        kind = "SECTION" if any("SECTION" in V28.norm(t["value"]) for t in titles) else "ELEVATION"
        if len(titles) > 1:
            findings.append({"code": "TWO_VIEW_TITLES_IN_ONE_FRAME", "titles": [_src(t) for t in titles]})
        vdims = _vertical_dims(dims, header_dimlfac, unit_m, box)
        view, levels, names = read_view(f"{kind}:{titles[0].get('id')}", kind, titles[0], box, texts, vdims, unit_m)
        findings += _bind_view(view, levels, names, fl_levels, unit_m)
        if view["calibration"]["state"] != "CALIBRATED":
            findings.append({"code": "VIEW_NOT_CALIBRATED", "view": view["view_id"],
                             "why": view["calibration"]["why"]})
        if not view["bands"]:
            findings.append({"code": "SECTION_BAND_NOT_BOUND", "view": view["view_id"]})
        views.append(view)
    floors = {}
    for i, fl in enumerate(order):
        nxt = order[i + 1] if i + 1 < len(order) else None
        floors[fl] = _floor_report(fl, nxt, fl_levels, views)
    return {"policy": policy_record(), "views": views, "floor_levels": fl_levels, "floors": floors,
            "findings": findings}


def _joining_dims(views, lo, hi):
    out = []
    for v in views:
        for d in v["dimensions"]:
            if abs(d["lo_m"] - lo) <= AGREE_M and abs(d["hi_m"] - hi) <= AGREE_M:
                out.append({"view": v["view_id"], "dimension": d["handle"], "value_m": d["value_m"]})
    return out


def _floor_report(fl, nxt, fl_levels, views):
    me = fl_levels[fl]
    zones = me["zones"]
    nz = fl_levels[nxt]["zones"] if nxt else []
    rep = {"floor": fl, "next_floor": nxt, "how": me["how"], "zones": []}
    if not zones:
        rep.update(state="HELD", why="FLOOR_LEVEL_NOT_PRINTED: no level in a room and no plan level; every height "
                                     "of this floor is held")
    for z in zones:
        v = z["level_m"]
        conf = [{"view": w["view_id"], "binding": b["binding"]} for w in views for b in w["bands"]
                if b["floor"] == fl and abs(b["ffl_m"] - v) <= AGREE_M]
        zr = {"ffl": {"value_m": v, "state": "PRINTED" if z["rooms"] else "PLAN_DOMINANT_LEVEL",
                      "rooms": z["rooms"], "source": z["source"][:6], "confirmed_by_views": conf}}
        # floor to floor
        f2f = None
        for n in nz:
            j = _joining_dims(views, v, n["level_m"])
            if j:
                f2f = {"value_m": j[0]["value_m"], "state": "PRINTED_DIMENSION", "to_level_m": n["level_m"],
                       "source": j, "never_wall_height": True}
                break
        if f2f is None and nxt and len(zones) == 1 and len(nz) == 1:
            f2f = {"value_m": round(nz[0]["level_m"] - v, 6), "state": "DERIVED_FROM_PRINTED_LEVELS",
                   "to_level_m": nz[0]["level_m"], "formula": f"{nxt} {nz[0]['level_m']:+.2f} - {fl} {v:+.2f}",
                   "never_wall_height": True}
        if f2f is None:
            f2f = {"value_m": None, "state": "HELD",
                   "why": ("NO_FLOOR_ABOVE" if not nxt else
                           "NEXT_FLOOR_LEVEL_NOT_PRINTED" if not nz else
                           "SPLIT_LEVEL_ZONE: no printed dimension joins this zone to the floor above, and a "
                           "level difference is not taken for a split-level storey")}
        zr["floor_to_floor"] = f2f
        # level above (the top floor, a split-level zone): candidates a printed dimension reaches
        if f2f["value_m"] is None:
            same_or_next = {round(x["level_m"], 3) for x in zones + nz}
            cands = {}
            for w in views:
                for d in w["dimensions"]:
                    if abs(d["lo_m"] - v) <= AGREE_M and not any(abs(d["hi_m"] - q) <= AGREE_M
                                                                    for q in same_or_next):
                        cands.setdefault(round(d["hi_m"], 3), []).append(
                            {"view": w["view_id"], "dimension": d["handle"], "value_m": d["value_m"]})
            zr["level_above"] = {"value_m": None, "state": "HELD" if cands else "NOT_PRINTED",
                                 "why": "LEVEL_ABOVE_KIND_NOT_PRINTED: a dimension reaches it, no label says what "
                                        "level it is (roof slab top, parapet, roof finish)" if cands else
                                        "no printed dimension starts at this level",
                                 "candidates": [{"level_m": k_, "height_m": round(k_ - v, 6), "source": s}
                                                for k_, s in sorted(cands.items())]}
        # labelled levels of a bound view between this level and the next floor
        top = min((n["level_m"] for n in nz if n["level_m"] > v + AGREE_M), default=None)
        for q, kind in (("soffit", "SOFFIT"), ("false_ceiling", "FCL"), ("next_slab_top", "TOS")):
            hits, split = [], False
            for w in views:
                if not any(b["floor"] == fl and abs(b["ffl_m"] - v) <= AGREE_M for b in w["bands"]):
                    continue
                if sum(1 for b in w["bands"] if b["floor"] == fl) > 1:
                    split = True
                    continue
                for x in w["levels"]:
                    if x["kind"] == kind and v + AGREE_M < x["value_m"] and (top is None or x["value_m"] <=
                                                                            top + AGREE_M):
                        hits.append({"level_m": x["value_m"], "height_m": round(x["value_m"] - v, 6),
                                     "view": w["view_id"], "text": x.get("text")})
            vals = {round(h["height_m"], 3) for h in hits}
            if len(vals) == 1:
                zr[q] = {"value_m": hits[0]["height_m"], "state": "PRINTED", "source": hits}
            elif len(vals) > 1:
                zr[q] = {"value_m": None, "state": "CONFLICT", "source": hits}
            else:
                zr[q] = {"value_m": None, "state": "HELD" if split else "NOT_PRINTED",
                         **({"why": "SPLIT_LEVEL_ZONE: two zones of this floor in the view"} if split else {})}
        if zr["soffit"]["value_m"] is not None and zr["next_slab_top"]["value_m"] is not None:
            t_ = round(zr["next_slab_top"]["value_m"] - zr["soffit"]["value_m"], 6)
            zr["slab_thickness"] = {"value_m": t_, "state": "PRINTED_LEVELS",
                                    "formula": "T.O.S. of the floor above - U/S SLAB"}
        else:
            zr["slab_thickness"] = {"value_m": OWNER_SLAB_M, "state": "OWNER_RULE",
                                    "source": "owner answer Q-14 (2026-10-19): structural slab 0.16 m unless a "
                                              "drawing or detail says otherwise",
                                    "not_for": ["stairs", "balconies", "depressed slabs", "landings",
                                                "special elements"]}
        ch = [dict(c, view=w["view_id"]) for w in views
              if sum(1 for b in w["bands"] if b["floor"] == fl) == 1
              and any(b["floor"] == fl and abs(b["ffl_m"] - v) <= AGREE_M for b in w["bands"])
              for c in w.get("clear_heights") or () if c["at_level_m"] is not None and c["value_m"] is not None
              and v - AGREE_M <= c["at_level_m"] < (top if top is not None else v + 100.0)]
        cv = {round(c["value_m"], 3) for c in ch}
        zr["clear_height"] = ({"value_m": ch[0]["value_m"], "state": "PRINTED", "source": ch} if len(cv) == 1 else
                              {"value_m": None, "state": "CONFLICT", "source": ch} if cv else
                              {"value_m": None, "state": "NOT_PRINTED"})
        zr["never"] = ["floor build-up or false-ceiling depth subtracted", "floor-to-floor taken as a wall height"]
        rep["zones"].append(zr)
    return rep


def clear_heights(texts, box, unit_m):
    """printed CLEAR HEIGHT / C.H. texts inside a box -> [(value_m, how, source, y)] (arch_v28.to_m unit reading)."""
    out = []
    for t in texts:
        if not V28._in_box((t["x"], t["y"]), box):
            continue
        m = CLEAR_RE.search(V28.norm(t["value"]))
        if m:
            v, how = V28.to_m(m.group(1), m.group(2) if m.lastindex and m.lastindex >= 2 else None, "ROOM_HEIGHT")
            out.append((v, how, _src(t), t["y"]))
    return out


def policy_record():
    return {"policy_id": POLICY_ID, "agree_m": AGREE_M, "text_reach_m": TEXT_REACH_M, "name_reach_m": NAME_REACH_M,
            "name_ambiguous_m": NAME_AMBIGUOUS_M, "owner_slab_m": OWNER_SLAB_M, "not_a_room": [str(k) for k in
                                                                                             NOT_A_ROOM],
            "bindings": ["NAME_NEAREST_LEVEL_LABEL", "LEVEL_EQUALS_A_ROOM_LEVEL",
                         "LEVEL_EQUALS_THE_PLAN_DOMINANT_LEVEL"],
            "rules": ["UP-HGT-001", "owner Q-14"],
            "never": ["an assumed floor build-up or false-ceiling depth subtracted",
                      "a floor-to-floor height taken as a wall height", "a missing level as 0",
                      "a level difference taken as floor-to-floor on a split-level storey"]}
