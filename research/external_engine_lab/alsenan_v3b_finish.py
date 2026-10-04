"""ALSENAN V3b - openings, NET finishes, reveals, finish sequences, angle beads, facades (lab adapter).

Opening heights: alsenan_v3b_openings.heights (plan width x calibrated raster elevations / sections); printed values
override (salon glazing 3.65 owner fact V3a, curved glazing 4.30 printed NW elevation).
Room faces: the V3a room boundary edges (alsenan_v3_layers._cycle_edges); an OPENING edge carries its door closure id
(CLOSURE|<occ>|A/B), a GLAZING edge its glazing parts - so every opening is matched to the room face it sits in.
NET (OD-V3B-3) = gross eligible face - full opening (its overlap with the finish band) + reveals.
Reveal depth per face: URBAN_FALLBACK = half the host wall thickness (frame centred), labelled (OD-V3B-9).
Sequences: dry face SPATTER -> ROUGH -> SMOOTH -> PAINT (OD-V3B-5); tiled face SPATTER -> TILE_PREP -> TILE (OD-V3B-4);
external Sigma SPATTER -> ROUGH -> SMOOTH -> SIGMA (OD-V3B-7; the elevations draw rendered plaster faces).
Angle beads: engine.source.corner_bead over the plastered faces only (OD-V3B-8).
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict

from shapely.geometry import Polygon
from shapely.ops import unary_union

import alsenan_v3_layers as L
import alsenan_v3b_openings as O
from engine.source import corner_bead as CB

FLOORS = ("GF", "1F", "2F")
LEVELS = {"GF": (0.0, 5.50), "1F": (5.50, 9.70), "2F": (9.70, 13.90)}      # printed level chain (m)
PARAPET_H = 0.50
REVEAL_RULE = "URBAN_FALLBACK reveal depth = half the host wall thickness per face (frame centred), labelled"


def _r(v, n=3):
    return None if v is None else round(float(v), n)


# ================================================================== heights and opening areas
def opening_heights(ctx, raster) -> dict:
    rows = [r for r in ctx["v3"]["openings"]["rows"]]
    printed = {"GF-W09": {"value_m": 3.65, "source": "OWNER FACT V3a (salon glazing 6.33 x 3.65)"}}
    H = {h["id"]: h for h in O.heights(rows, raster["raster_openings"], printed)}
    # sill per opening (median of the candidates' sills; doors 0)
    for h in H.values():
        c = h.get("candidates") or []
        if h["kind"] == "WINDOW":
            h["sill_m"] = round(statistics.median([x["sill_cm"] for x in c]) / 100.0 - _floor_level(h["floor"]), 3) \
                if c else None
        else:
            h["sill_m"] = 0.0
    return H


def _floor_level(fl):
    return {"GF": 1.00, "1F": 5.50, "2F": 9.70}[fl]


def _cls(h):
    """technical / commercial classes of an opening height record."""
    if h["state"] == "PRINTED":
        return "RASTER_DERIVED", None, "H"
    if h["state"] == "RASTER_TYPE_MATCH":
        return "RASTER_DERIVED", None, "M"
    if h.get("height_m") is None:
        return "BLOCKED", None, None
    return "BLOCKED", h["commercial"], h["confidence"]


def opening_areas(ctx, H) -> list:
    out = []
    for r in ctx["v3"]["openings"]["rows"]:
        h = H.get(r["id"])
        if not h or r.get("width_m") is None:
            out.append({"id": r["id"], "floor": r["floor"], "kind": r["kind"], "state": "NO_WIDTH"})
            continue
        t, c, conf = _cls(h)
        hm = h.get("height_m")
        a = r["width_m"] * hm if hm else None
        rng = h.get("range_m")
        out.append({"id": r["id"], "floor": r["floor"], "kind": r["kind"], "width_m": r["width_m"], "height_m": hm,
                    "sill_m": h.get("sill_m"), "area_m2": _r(a, 4), "technical": t, "commercial": c, "confidence": conf,
                    "state": h["state"], "low_m2": _r(r["width_m"] * rng[0], 4) if rng else _r(a, 4),
                    "high_m2": _r(r["width_m"] * rng[1], 4) if rng else _r(a, 4), "source": h.get("source"),
                    "candidates": len(h.get("candidates") or [])})
    return out


# ================================================================== room faces with their openings
def _window_by_part(ctx, fl):
    out = {}
    for i, w in enumerate(ctx["a2_raw"][fl]["eri"]["glazing"]["windows"]):
        for p in w["parts"]:
            out[p] = (f"{fl}-W{i + 1:02d}", w)
    return out


def _edge_openings(ctx, fl, srcs, wins):
    ids = set()
    for s in srcs:
        if s.startswith("CLOSURE|GLAZED|"):
            part = s[len("CLOSURE|GLAZED|"):].rsplit("|", 1)[0]
            if part in wins:
                ids.add(wins[part][0])
        elif s.startswith("CLOSURE|"):
            occ = s.split("|")[1]
            ids.add(f"{fl}-D-{occ}")
    for s in srcs:
        if s in wins:
            ids.add(wins[s][0])
    return ids


def net_finishes(ctx, H, oa) -> dict:
    fin = {r["room"]: r for r in ctx["v3"]["finishes"]["rows"]}
    faces = defaultdict(list)
    for f in ctx["v3"]["finishes"]["faces"]:
        faces[f["room"]].append(f)
    orow = {o["id"]: o for o in ctx["v3"]["openings"]["rows"]}
    area = {o["id"]: o for o in oa}
    rooms = [r for r in ctx["v3"]["rooms"]["rows"] if r["id"] in fin]
    out, beads_all = [], []
    for r in rooms:
        fl = r["floor"]
        res = ctx["a2_raw"][fl]["res"]
        u = ctx["a2_raw"][fl]["inp"].unit_native_to_mm or 1.0
        s = next(x for x in res["sites"] if x["site_id"] == r["site"])
        wins = _window_by_part(ctx, fl)
        on = defaultdict(float)
        for pts, roles, srcs, Lm in L._cycle_edges(res, s, u):
            k = L._edge_kind(roles, srcs)
            if k in ("OPENING", "GLAZING"):
                for oid in _edge_openings(ctx, fl, srcs, wins):
                    on[oid] += Lm
        f = fin[r["id"]]
        wet = f["room_class"] in ("WET", "SERVICE")
        fc = faces[r["id"]]
        ph = _mode([x["plaster_h_m"] for x in fc if x.get("plaster_h_m")])
        pa = _mode([x["paint_h_m"] for x in fc if x.get("paint_h_m")])
        th = _mode([x["wall_tile_h_m"] for x in fc if x.get("wall_tile_h_m")]) if wet else None
        ded = defaultdict(float)
        ded_lo = defaultdict(float)
        ded_hi = defaultdict(float)
        rev = defaultdict(float)
        prov, blocked, ops = False, [], []
        for oid, Lm in sorted(on.items()):
            o, a = orow.get(oid), area.get(oid)
            if not o or not a or a.get("height_m") is None:
                blocked.append(oid)
                continue
            w = min(o["width_m"], Lm) if Lm > 0.05 else 0.0
            if w <= 0:
                continue
            hgt, sill = a["height_m"], a.get("sill_m") or 0.0
            if sill is None:
                sill = 0.0
            if a["technical"] != "RASTER_DERIVED":
                prov = True
            lo_h = a["low_m2"] / o["width_m"] if a.get("low_m2") else hgt
            hi_h = a["high_m2"] / o["width_m"] if a.get("high_m2") else hgt
            for band, top in (("PLASTER", ph), ("PAINT", pa), ("TILE", th)):
                if top is None:
                    continue
                ded[band] += w * max(0.0, min(sill + hgt, top) - sill)
                ded_lo[band] += w * max(0.0, min(sill + lo_h, top) - sill)
                ded_hi[band] += w * max(0.0, min(sill + hi_h, top) - sill)
            d = (o.get("wall_t_m") or 0.20) / 2.0
            jamb = 2 * hgt * d
            head = w * d
            if o["kind"] == "WINDOW":
                rev["WINDOW_REVEAL"] += jamb + head
                rev["WINDOW_SILL_LM"] += w
            else:
                rev["DOOR_REVEAL"] += jamb + head
            ops.append({"id": oid, "width_on_face_m": _r(w), "height_m": hgt, "sill_m": sill, "kind": o["kind"],
                        "class": a["technical"] if a["technical"] == "RASTER_DERIVED" else a["commercial"]})
            # beads: this room's face of the opening, plastered unless tiled (wet)
            face = {"face": r["id"], "plaster": None if wet else (0.0, ph or 0.0),
                    "finish_population": "TILE" if wet else "PLASTER"}
            beads_all += [dict(sg, floor=fl) for sg in CB.segments([{"id": oid, "kind": "WINDOW" if o["kind"] == "WINDOW"
                                                                      else "DOOR", "width_m": w, "height_m": hgt,
                                                                      "sill_m": sill, "faces": [face],
                                                                      "source": a["state"]}])]
        gross = {"PLASTER": f["plaster_gross_m2"], "PAINT": f["paint_gross_m2"], "TILE": f["wall_tile_gross_m2"]}
        net = {}
        for band in ("PLASTER", "PAINT", "TILE"):
            g = gross[band]
            if g is None:
                net[band] = None
                continue
            rv = (rev["DOOR_REVEAL"] + rev["WINDOW_REVEAL"]) if (band != "PLASTER" or not wet) else 0.0
            net[band] = {"gross": g, "openings": ded[band], "reveals": rv, "net": g - ded[band] + rv,
                         "net_low": g - ded_hi[band] + rv, "net_high": g - ded_lo[band] + rv}
        # corners: V3a projecting corners x plaster height (dry rooms, both faces plastered in the same room)
        if not wet and f.get("corner_beads_nr") and ph:
            beads_all += [dict(sg, floor=fl) for sg in CB.segments([], [
                {"id": f"{r['id']}-C{k + 1}", "z0": 0.0, "z1": ph, "faces": [(0.0, ph), (0.0, ph)],
                 "finish_population": "PLASTER", "source": "room polygon projecting corner (V3a)"}
                for k in range(f["corner_beads_nr"])])]
        seq = _sequence(wet, net)
        out.append({"room": r["id"], "floor": fl, "name": f["name_en"] or f["name_ar"], "room_class": f["room_class"],
                    "wet": wet, "plaster_h_m": ph, "paint_h_m": pa, "tile_h_m": th, "openings": ops,
                    "openings_unmatched": blocked, "reveals": {k: _r(v) for k, v in rev.items()},
                    "net": {k: (None if v is None else {kk: _r(vv) for kk, vv in v.items()}) for k, v in net.items()},
                    "sequence": seq, "provisional": prov or bool(blocked), "wall_state": f["wall_state"],
                    "faces_blocked_length_m": f["faces_blocked_length_m"], "paint_blocked_length_m": f["paint_blocked_length_m"]})
    return {"rooms": out, "beads": beads_all, "bead_total": CB.total(beads_all), "reveal_rule": REVEAL_RULE,
            "bead_policy": CB.policy_record()}


def _mode(v):
    v = [round(x, 3) for x in v if x]
    return max(set(v), key=v.count) if v else None


def _sequence(wet, net):
    """Separate items on the same geometric population (OD-V3B-4 / 5)."""
    if wet:
        t = net.get("TILE")
        q = t["net"] if t else None
        return {"SPATTER_DASH_WET": q, "TILE_PREP": q, "WALL_TILE_NET": q, "GENERAL_PLASTER": 0.0,
                "HIDDEN_ABOVE_TILE": (net["PLASTER"]["gross"] - t["gross"]) if (t and net.get("PLASTER")) else None,
                "method": "WET_ROOM_SPATTER_ONLY_BEFORE_TILE"}
    p, a = net.get("PLASTER"), net.get("PAINT")
    q = p["net"] if p else None
    return {"SPATTER_DASH_INTERNAL": q, "ROUGH_PLASTER_INTERNAL": q, "SMOOTH_PLASTER_INTERNAL": q,
            "PAINT_INTERNAL_NET": a["net"] if a else None, "method": "DRY_INTERNAL_SPATTER_ROUGH_SMOOTH"}


# ================================================================== facades
def facades(ctx, H, oa) -> dict:
    """External faces per floor band: outline of the floor's rooms closed across the walls (outer face = inner face +
    the wall band), perimeter x the printed level-chain band, minus the external openings (windows + E-doors) + their
    external reveals; GF adds the +1.00 plinth band; parapets (V3a lengths) both faces."""
    rooms = defaultdict(list)
    for r in ctx["v3"]["rooms"]["rows"]:
        if r["room_class"] in ("EXTERNAL", "ROOF") or len(r.get("_polygon") or []) < 3:
            continue
        p = Polygon(r["_polygon"]).buffer(0)
        if p.area > 0:
            rooms[r["floor"]].append(p)
    out = []
    area_o = {o["id"]: o for o in oa}
    for fl in FLOORS:
        u = unary_union([p.buffer(250.0, join_style=2) for p in rooms[fl]]).buffer(-50.0, join_style=2)
        polys = list(getattr(u, "geoms", [u]))
        per = 0.0
        for p in polys:
            per += p.exterior.length
            per += sum(i.length for i in p.interiors if Polygon(i).area > 4e6)
        per /= 1000.0
        z0, z1 = LEVELS[fl]
        band = z1 - z0 + (0.0 if fl != "GF" else 0.0)
        gross = per * band
        ext = [o for o in oa if o["floor"] == fl and o.get("area_m2") and (o["kind"] == "WINDOW" or "-D-E" in o["id"])]
        ded = sum(o["area_m2"] for o in ext)
        rev = sum((2 * o["height_m"] + o["width_m"]) * 0.10 for o in ext)
        out.append({"floor": fl, "outline_perimeter_m": _r(per), "band_m": band, "band_levels": [z0, z1],
                    "gross_m2": _r(gross), "external_openings": len(ext), "openings_m2": _r(ded),
                    "external_reveals_m2": _r(rev), "net_m2": _r(gross - ded + rev),
                    "provisional_openings": sum(1 for o in ext if o["technical"] != "RASTER_DERIVED")})
    par = [l for l in ctx["v3"]["blockwork"].get("parapets", [])] if isinstance(ctx["v3"]["blockwork"], dict) else []
    return {"floors": out, "parapets": par, "method": "SIGMA_EXTERNAL_SPATTER_ROUGH_SMOOTH_SIGMA",
            "finish_evidence": "elevations draw rendered plaster faces (no cladding hatch except the stone arch voussoirs)",
            "rule": "outline = rooms of the floor closed across walls (buffer 250 / -50 mm), courtyard rings > 4 m2 "
                    "included; band = printed level chain (GF 0.00-5.50 incl. the +1.00 plinth, 1F 5.50-9.70, 2F "
                    "9.70-13.90); external reveal depth 0.10 (half a 200 wall)"}


# ================================================================== B-OVER-OPEN, paint under unbound beams (B12), parapets
def over_openings(ctx, oa) -> dict:
    """Blockwork above each opening (wall height - head - lintel depth) and below each window (sill), opening by
    opening; the V3a wall lengths exclude the opening gaps."""
    import alsenan_v3_structure as V3S
    hb = defaultdict(list)
    for f in ctx["v3"]["finishes"]["faces"]:
        if f.get("blockwork_h_m"):
            hb[f["floor"]].append(f["blockwork_h_m"])
    Hw = {fl: _mode(v) for fl, v in hb.items()}
    tech = com = lo = hi = 0.0
    det = []
    for a in oa:
        if not a.get("height_m") or not a.get("width_m"):
            continue
        w, h, s = a["width_m"], a["height_m"], a.get("sill_m") or 0.0
        sch = next((x for x in V3S.LINTELS if w * 100 <= x[0] + 0.5), V3S.LINTELS[-1])
        D = sch[1] / 100.0
        H = Hw.get(a["floor"])
        if not H:
            continue
        def area(hh):
            return w * (max(0.0, H - (s + hh) - D) + (s if a["kind"] == "WINDOW" else 0.0))
        q = area(h)
        r_lo = a["low_m2"] / w if a.get("low_m2") else h
        r_hi = a["high_m2"] / w if a.get("high_m2") else h
        com += q
        lo += area(r_hi)
        hi += area(r_lo)
        if a.get("technical") == "RASTER_DERIVED":
            tech += q
        det.append({"ref": a["id"], "formula": f"{w} x ({H} - ({s} + {h}) - {D})" + (f" + {w} x {s}" if a["kind"] == "WINDOW"
                                                                                  else ""), "qty": _r(q, 4),
                    "status": a.get("technical") or a.get("commercial")})
    return {"qty": com, "low": lo, "high": hi, "technical": tech, "class": "PROVISIONAL_SOURCE_DERIVED",
            "confidence": "M", "method": "per opening: w x (wall height - head - lintel depth) + w x sill (windows)",
            "assumption": "wall height = the floor's modal blockwork height; lintel depth by the p.13 schedule",
            "formula": f"{len(det)} openings; technical part {tech:.3f} m2 (raster-derived heights)", "details": det}


def paint_blocked(ctx, nf) -> dict:
    """B12: rooms whose paint V3a blocked (an unbound beam band over the room): the blocked pieces take the room's
    modal known paint height (else the floor's), labelled PROVISIONAL_GEOMETRIC_INFERENCE."""
    fin = {r["room"]: r for r in ctx["v3"]["finishes"]["rows"]}
    faces = defaultdict(list)
    for f in ctx["v3"]["finishes"]["faces"]:
        faces[f["room"]].append(f)
    floor_mode = defaultdict(list)
    for f in ctx["v3"]["finishes"]["faces"]:
        if f.get("paint_h_m"):
            floor_mode[f["floor"]].append(f["paint_h_m"])
    netr = {r["room"]: r for r in nf["rooms"]}
    out = {}
    for rid, f in fin.items():
        if f["room_class"] in ("WET", "SERVICE") or f["paint_gross_m2"] is not None or not faces[rid]:
            continue
        fc = faces[rid]
        known = [x["paint_h_m"] for x in fc if x.get("paint_h_m")]
        h = _mode(known) or _mode(floor_mode[f["floor"]])
        hs = known or floor_mode[f["floor"]]
        g = sum(x["length_m"] * (x["paint_h_m"] or h) for x in fc)
        glo = sum(x["length_m"] * (x["paint_h_m"] or min(hs)) for x in fc)
        ghi = sum(x["length_m"] * (x["paint_h_m"] or max(hs)) for x in fc)
        r = netr.get(rid)
        ded = sum(o["width_on_face_m"] * min(o["height_m"], h) for o in (r["openings"] if r else []))
        rev = (r["reveals"].get("DOOR_REVEAL") or 0) + (r["reveals"].get("WINDOW_REVEAL") or 0) if r else 0.0
        blocked_len = sum(x["length_m"] for x in fc if not x.get("paint_h_m"))
        out[rid] = {"net": g - ded + rev, "low": glo - ded + rev, "high": ghi - ded + rev,
                    "method": "blocked pieces at the room's modal known paint height",
                    "assumption": f"{blocked_len:.2f} m of faces under an unbound band at {h} m (range {min(hs)}..{max(hs)})",
                    "formula": f"gross {g:.3f} - openings {ded:.3f} + reveals {rev:.3f}"}
    return out


def parapet_faces(v3a) -> list:
    out = []
    for ln in v3a:
        if ln["code"].startswith("B-PAR-") and ln.get("qty"):
            L_ = ln["qty"] / PARAPET_H
            q = L_ * PARAPET_H * 2 + L_ * 0.20
            out.append((ln["level"], q, f"{L_:.3f} x 0.50 x 2 + {L_:.3f} x 0.20 ({ln['code']})"))
    return out
