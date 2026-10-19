"""Run the architectural engine on a synthetic villa and compare its output with the villa's truth (T-019).

    run_engine(path, method)              -> (room_boq, arch, refusal)   urban_boq_m9.arch_compute; refusal is None
                                             or the engine's COMPLETENESS_FAILED record (its partial arch is kept)
    compare(truth, arch, refusal=None)    -> report (rooms, openings, walls by thickness, silent omissions)

Matching is by position, never by name: a truth room is matched to the engine room whose polygon contains the room's
probe point (drawing coordinates, m); a truth opening to the engine opening of the same floor whose centre lies within
OPENING_MATCH_M of it. Status per truth item:
    ANSWERED          the engine has an entry for it (its quantity may still differ: see the diff fields)
    SILENT_OMISSION   the engine has no entry at all (no room contains the probe; no opening near the centre; no wall
                      band of that thickness on the floor)
Engine entries matched to no truth item are listed as unmatched (false positives or duplicates). A missing engine
quantity stays None, never 0. The report is a diagnostic: it does not decide who is right.
"""

from __future__ import annotations

import math

OPENING_MATCH_M = 0.15
AREA_TOL_M2 = 0.005
LEN_TOL_M = 0.005
DEFAULT_METHOD = "ARCH_TAKEOFF_V2.9"


def run_engine(path, method=DEFAULT_METHOD):
    from tools import urban_boq_m9 as M9
    try:
        room, arch, _e = M9.arch_compute(str(path), method=method)
    except M9.CompletenessFailed as ex:            # the engine measured but refuses to release: report, never hide
        unacc = [{"floor": c["floor"], "unaccounted": c["unaccounted"]} for c in ex.arch.get("coverage") or ()
                 if c.get("unaccounted")]
        return ex.room_boq, ex.arch, {"state": "COMPLETENESS_FAILED", "message": str(ex), "unaccounted": unacc}
    return room, arch, None


def _inside(pt, poly):
    """even-odd point in polygon (polygon vertices in m)."""
    x, y = pt
    ins = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xc = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xc > x:
                ins = not ins
    return ins


def _in_room(pt, r):
    poly = r.get("polygon_m") or []
    if len(poly) < 3 or not _inside(pt, poly):
        return False
    return not any(len(h) >= 3 and _inside(pt, h) for h in (r.get("hole_polygons_m") or []))


def _centre(o):
    c = ((o.get("v28") or {}).get("position") or {}).get("centre_m") if isinstance(o.get("v28"), dict) else None
    if c is None:
        c = (o.get("position") or {}).get("centre_m")
    return tuple(c) if c else None


def _family(t):
    return f"{float(t):.2f}"


def compare(truth, arch, refusal=None):
    rep = {"villa_id": truth["villa_id"], "variant": truth["variant"], "engine_refusal": refusal, "floors": {},
           "silent_omissions": [], "summary": {}}
    eng_rooms = arch.get("rooms") or []
    eng_ops = arch.get("openings") or []
    walls = {w["floor"]: w for w in (arch.get("walls") or [])}
    floors_seen = sorted({r["floor"] for r in eng_rooms} | {o["floor"] for o in eng_ops})
    for fl, tf in truth["floors"].items():
        fr = [r for r in eng_rooms if r["floor"] == fl]
        fo = [o for o in eng_ops if o["floor"] == fl]
        rooms, used = [], set()
        for t in tf["rooms"]:
            hits = [r for r in fr if _in_room(t["point_m"], r)]
            row = {"room_id": t["room_id"], "truth_area_m2": t["area_m2"], "truth_code": t["code"], "truth_wet": t["wet"],
                   "labelled": t["labelled"]}
            if not hits:
                row.update(status="SILENT_OMISSION", engine=None)
                rep["silent_omissions"].append({"floor": fl, "what": "ROOM", "id": t["room_id"]})
            else:
                r = hits[0]
                used.add(r["room_id"])
                a = r.get("area_m2")
                g = r.get("gross_m2")
                row.update(status="ANSWERED", engine={
                    "room_id": r["room_id"], "codes": r.get("codes"), "kind": r.get("kind"), "area_m2": a,
                    "gross_m2": g, "doors": len(r.get("doors") or []), "windows": len(r.get("windows") or [])},
                    gross_diff_m2=None if g is None else g - t["area_m2"],
                    gross_agrees=None if g is None else abs(g - t["area_m2"]) <= AREA_TOL_M2,
                    code_agrees=(t["code"] in (r.get("codes") or [])) if t["code"] else (not r.get("codes")),
                    # an unlabelled room's wet / dry is not on the drawing: no agreement is scored, the kind is shown
                    wet_agrees=((r.get("kind") == "WET") == t["wet"]) if t["labelled"] else None,
                    shared_with=[x["room_id"] for x in hits[1:]])
            rooms.append(row)
        ops, used_ops = [], set()
        for t in tf["openings"]:
            near = sorted(((math.dist(t["centre_m"], c), o) for o in fo for c in [_centre(o)] if c),
                          key=lambda x: x[0])
            near = [(d, o) for d, o in near if d <= OPENING_MATCH_M and o["opening_id"] not in used_ops]
            row = {"opening_id": t["opening_id"], "kind": t["kind"], "truth_width_m": t["width_m"]}
            if not near:
                row.update(status="SILENT_OMISSION", engine=None)
                rep["silent_omissions"].append({"floor": fl, "what": t["kind"], "id": t["opening_id"]})
            else:
                d, o = near[0]
                used_ops.add(o["opening_id"])
                w = o.get("width_m")
                row.update(status="ANSWERED", engine={"opening_id": o["opening_id"], "kind": o.get("kind"),
                                                      "width_m": w, "offset_m": d},
                           kind_agrees=o.get("kind") == t["kind"],
                           width_agrees=None if w is None else abs(w - t["width_m"]) <= LEN_TOL_M)
            ops.append(row)
        fam_eng = {b["family"]: b for b in (walls.get(fl) or {}).get("by_thickness") or []}
        wrows = {}
        for fam, tw in tf["walls_by_thickness"].items():
            e = fam_eng.get(_family(fam))
            if e is None:
                wrows[fam] = {"status": "SILENT_OMISSION", "truth": tw, "engine": None}
                rep["silent_omissions"].append({"floor": fl, "what": "WALL_FAMILY", "id": fam})
            else:
                wrows[fam] = {"status": "ANSWERED", "truth": tw,
                              "engine": {"gross_lm": e.get("gross_lm"), "net_lm": e.get("net_lm")},
                              "net_diff_lm": None if e.get("net_lm") is None else e["net_lm"] - tw["net_lm"]}
        rep["floors"][fl] = {
            "engine_floor_found": fl in floors_seen,
            "rooms": rooms, "openings": ops, "walls_by_thickness": wrows,
            "unmatched_engine_rooms": [r["room_id"] for r in fr if r["room_id"] not in used],
            "unmatched_engine_openings": [o["opening_id"] for o in fo if o["opening_id"] not in used_ops],
            "unmatched_engine_wall_families": sorted(set(fam_eng) - {_family(f) for f in tf["walls_by_thickness"]}),
        }
    rep["engine_floors_not_in_truth"] = sorted(set(floors_seen) - set(truth["floors"]))
    allr = [x for f in rep["floors"].values() for x in f["rooms"]]
    allo = [x for f in rep["floors"].values() for x in f["openings"]]
    rep["summary"] = {
        "engine_state": "RELEASED_OR_HELD" if refusal is None else refusal["state"],
        "truth_rooms": len(allr), "truth_openings": len(allo),
        "silent_omissions": len(rep["silent_omissions"]),
        "rooms_answered": sum(x["status"] == "ANSWERED" for x in allr),
        "rooms_labelled": sum(bool(x["labelled"]) for x in allr),
        "room_gross_agrees": sum(bool(x.get("gross_agrees")) for x in allr),
        "room_code_agrees": sum(bool(x.get("code_agrees")) for x in allr),
        "room_wet_agrees": sum(bool(x.get("wet_agrees")) for x in allr),
        "openings_answered": sum(x["status"] == "ANSWERED" for x in allo),
        "opening_kind_agrees": sum(bool(x.get("kind_agrees")) for x in allo),
        "opening_width_agrees": sum(bool(x.get("width_agrees")) for x in allo),
        "unmatched_engine_rooms": sum(len(f["unmatched_engine_rooms"]) for f in rep["floors"].values()),
        "unmatched_engine_openings": sum(len(f["unmatched_engine_openings"]) for f in rep["floors"].values()),
    }
    return rep
