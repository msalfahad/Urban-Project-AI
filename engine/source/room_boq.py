"""ROOM BOQ (M9 S1) - canonical lines and material results per room from a ROOM SCHEDULE (generic; stdlib only).

    load(path_or_dict)          -> a validated room schedule (URBAN_ROOM_INPUT_V1)
    check(schedule)             -> the rooms diagnostic: area, perimeter, shape, flags per room - no BOQ lines
    build(schedule)             -> {"lines", "materials", "comparisons", "unresolved", "rules", "assumptions"}

S1 takes rooms from a schedule (a synthetic fixture or an owner-supplied room list); reading rooms from drawings
(TS01 / room_slice, which still carry the v1.0.0 waterproofing rules) is S2. Per room:

    floor finish      FIN.FLOOR.PORCELAIN (dry) / FIN.FLOOR.WET_TILE (wet), m2 = the floor polygon     UP-CER-001
                      material: tile_layout (rectangle exact) for the selected size; the owner sizes compared
                      as recommendations only                                                          UP-CER-010
    waterproofing     wet rooms: FIN.WP.FLOOR, FIN.WP.DOORWAY (per door), FIN.WP.UPTURN               UP-WP-001/002/003
                      material: membrane_layout (rectangle exact) on the selected membrane             UP-WP-005

A value the schedule does not give is never filled in: the line or the material result it feeds is BLOCKED with the
question that unlocks it. A polygon room keeps its exact net area (shoelace) while its layout is BLOCKED (S2).
"""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

from engine.source import boq_line as BL
from engine.source import material_spec as MS
from engine.source import membrane_layout as ML
from engine.source import rule_store as RS
from engine.source import tile_layout as TL
from engine.source import material_result as WP

SCHEMA = "URBAN_ROOM_INPUT_V1"
RULE_SET = RS.LATEST_APPROVED
REQUIRED_ASSUMPTIONS = ("joint_m",)


class RoomError(ValueError):
    pass


def load(src):
    s = json.loads(Path(src).read_text(encoding="utf-8")) if not isinstance(src, dict) else copy.deepcopy(src)
    if s.get("schema") != SCHEMA:
        raise RoomError(f"room schedule schema must be {SCHEMA}")
    for k in ("project_id", "revision_set_sha256", "geometry_source", "rooms"):
        if not s.get(k):
            raise RoomError(f"room schedule needs {k}")
    if s["geometry_source"] not in BL.GEOMETRY_SOURCE:
        raise RoomError(f"geometry_source {s['geometry_source']}")
    ids = [r.get("room_id") for r in s["rooms"]]
    if len(set(ids)) != len(ids) or None in ids:
        raise RoomError("every room needs a unique room_id")
    s.setdefault("assumptions", {})
    return s


def _poly_area_perimeter(poly):
    pts = [tuple(map(float, p)) for p in poly]
    if len(pts) > 1 and math.dist(pts[0], pts[-1]) < 1e-9:
        pts = pts[:-1]
    a = sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts))) / 2.0
    p = sum(math.dist(pts[i - 1], pts[i]) for i in range(len(pts)))
    return abs(a), p


def geometry(room):
    """-> {"shape": RECT | POLYGON | MISSING, "area_m2", "perimeter_lm", "sides"}"""
    ab = TL.rectangle(room) if (room.get("polygon") or room.get("length_m") is not None) else None
    if ab is not None:
        return {"shape": "RECT", "area_m2": ab[0] * ab[1], "perimeter_lm": 2 * (ab[0] + ab[1]), "sides": list(ab)}
    if room.get("polygon") and len(room["polygon"]) >= 3:
        a, p = _poly_area_perimeter(room["polygon"])
        return {"shape": "POLYGON", "area_m2": a, "perimeter_lm": p, "sides": None}
    return {"shape": "MISSING", "area_m2": None, "perimeter_lm": None, "sides": None}


def check(schedule):
    s = load(schedule)
    out = []
    for r in s["rooms"]:
        g = geometry(r)
        flags = []
        if g["shape"] == "MISSING":
            flags.append("ROOM_GEOMETRY_NOT_ESTABLISHED")
        if g["shape"] == "POLYGON":
            flags.append("LAYOUT_BLOCKED_POLYGON (S2)")
        if not r.get("name_en") and not r.get("name_ar"):
            flags.append("ROOM_NAME_MISSING")
        if r.get("wet") and not (r.get("waterproofing") or {}).get("doorways"):
            flags.append("WET_ROOM_WITHOUT_DOORWAY_DATA")
        if not (r.get("floor_finish") or {}).get("spec_id"):
            flags.append("FLOOR_FINISH_SPEC_NOT_ESTABLISHED")
        out.append({"room_id": r["room_id"], "floor": r.get("floor"), "name_en": r.get("name_en"),
                    "name_ar": r.get("name_ar"), "wet": bool(r.get("wet")), **{k: g[k] for k in ("shape", "area_m2",
                                                                                                  "perimeter_lm")},
                    "flags": flags})
    return {"schema": "URBAN_ROOMS_DIAGNOSTIC_V1", "project_id": s["project_id"], "rooms": out,
            "note": "diagnostic only: no BOQ line is produced by this check"}


def _ref(rule_id):
    return RS.rule_ref(rule_id, RULE_SET)


def _line(s, r, *, item_code, element, net, formula, inputs, rule_id, ev=None, rfi=None, notes="", gross=None):
    ref = _ref(rule_id)
    ev = ev or ("SOURCE_DERIVED" if net is not None else "BLOCKED_RFI")
    return BL.make_line(project_id=s["project_id"], revision_set_sha256=s["revision_set_sha256"], item_code=item_code,
                        unit="m2", evidence_state=ev, measured_net=net if ev in BL.QUANTITY_STATES else None,
                        element_id=f"{r['room_id']}:{element}", floor=r.get("floor"), room_id=r["room_id"],
                        room_name_en=r.get("name_en"), room_name_ar=r.get("name_ar"), physical_element=element,
                        gross=gross, formula=formula, inputs=inputs, documents=s.get("documents", ()),
                        geometry_source=s["geometry_source"],
                        geometry_confidence="EXACT_INPUT" if ev in BL.QUANTITY_STATES else "NOT_ESTABLISHED",
                        rule_id=ref["rule_id"], rule_version=ref["version"], rule_set=ref["rule_set"],
                        rule_set_digest=ref["rule_set_digest"], rfi=rfi, notes=notes)


def _tile_constraints(s, r):
    a = dict(s.get("assumptions") or {})
    a.update((r.get("floor_finish") or {}).get("constraints") or {})
    c = {k: a.get(k) for k in ("joint_m", "min_cut_m", "min_reusable_m", "kerf_m", "rotation_allowed", "orientations",
                               "alignments", "objective") if a.get(k) is not None}
    c["wet_room"] = bool(r.get("wet"))
    c["rule_refs"] = [_ref("UP-CER-010"), _ref("UP-CER-001")]
    sp = a.get("spare_allowance")
    if sp:
        c["spare_allowance"] = WP.spare(sp.get("pct"), sp.get("source"))
    return c


def _tile_spec(ff):
    sid = ff.get("spec_id")
    if sid and sid.startswith("TILE-CUSTOM"):
        cs = ff.get("custom") or {}
        spec = MS.custom_tile(cs["length_m"], cs["width_m"], pieces_per_box=cs.get("pieces_per_box"),
                              name_en=cs.get("name_en"), name_ar=cs.get("name_ar"))
    else:
        spec = MS.tile(sid)
    if ff.get("pieces_per_box"):
        spec = MS.with_packaging(spec, pieces_per_box=ff["pieces_per_box"], source=ff.get("packaging_source") or "")
    return spec


def build(schedule):
    s = load(schedule)
    lines, mats, comps, unresolved, assumptions = [], [], [], [], []
    for k, v in sorted((s.get("assumptions") or {}).items()):
        assumptions.append({"scope": "project", "name": k, "value": v,
                            "source": (s.get("assumption_sources") or {}).get(k, "room schedule (caller input)")})
    up_rule = RS.rule("UP-WP-002", RULE_SET)
    assumptions.append({"scope": "project", "name": "upturn_h_m", "value": up_rule["value"],
                        "source": f"UP-WP-002@{up_rule['version']} (rule set {RULE_SET})"})
    for r in s["rooms"]:
        g = geometry(r)
        wet = bool(r.get("wet"))
        ff = r.get("floor_finish") or {}
        code = "FIN.FLOOR.WET_TILE" if wet else "FIN.FLOOR.PORCELAIN"
        if g["shape"] == "MISSING":
            ln = _line(s, r, item_code=code, element="floor", net=None, formula="floor polygon area",
                       inputs={}, rule_id="UP-CER-001",
                       rfi={"question": "ROOM_GEOMETRY_NOT_ESTABLISHED: room dimensions / polygon", "unlocks": r["room_id"]})
            lines.append(ln)
            unresolved.append({"room_id": r["room_id"], "item": code, "reason": ln["rfi"]["question"]})
        else:
            ln = _line(s, r, item_code=code, element="floor", net=g["area_m2"],
                       formula="length x width" if g["shape"] == "RECT" else "polygon area (shoelace)",
                       inputs={"sides_m": g["sides"]} if g["sides"] else {"polygon": r.get("polygon")},
                       rule_id="UP-CER-001")
            lines.append(ln)
            room = dict(r, line_id=ln["line_id"], net_area_m2=g["area_m2"])
            if not ff.get("spec_id"):
                res = WP.blocked(method=TL.METHOD, spec=None, reason="FLOOR_FINISH_SPEC_NOT_ESTABLISHED: tile size not "
                                 "given for this room", net_installed_m2=g["area_m2"], line_id=ln["line_id"],
                                 location=TL._loc(r))
                mats.append(res)
                unresolved.append({"room_id": r["room_id"], "item": code, "reason": res["blocked_by"]})
            else:
                spec = _tile_spec(ff)
                c = _tile_constraints(s, r)
                if c.get("joint_m") is None:
                    res = WP.blocked(method=TL.METHOD, spec=spec, reason="JOINT_WIDTH_NOT_ESTABLISHED: the joint width "
                                     "is a design input", net_installed_m2=g["area_m2"], line_id=ln["line_id"],
                                     location=TL._loc(r))
                    mats.append(res)
                    unresolved.append({"room_id": r["room_id"], "item": code, "reason": res["blocked_by"]})
                else:
                    b = TL.best(room, spec, c)
                    res = b["selected"]
                    res["search"] = {"objective": b.get("objective"), "feasible": b["feasible"], "tried": b["tried"]}
                    mats.append(res)
                    if res["state"] == "BLOCKED":
                        unresolved.append({"room_id": r["room_id"], "item": code, "reason": res["blocked_by"]})
                    elif res["packaging"]["state"] == "UNRESOLVED":
                        unresolved.append({"room_id": r["room_id"], "item": code + " (boxes)",
                                           "reason": res["packaging"]["reason"]})
                    cands = [spec] + [MS.tile(x) for x in (ff.get("candidates") or MS.OWNER_TILE_SIZES)
                                      if x != spec["spec_id"]]
                    if res["state"] != "BLOCKED":
                        rows = TL.compare(room, cands, spec["spec_id"], c)
                        for x in rows:
                            x.pop("result", None)
                            x.pop("tried", None)
                            x.update(room_id=r["room_id"], floor=r.get("floor"), line_id=ln["line_id"])
                        comps.extend(rows)
        if wet:
            wp = r.get("waterproofing") or {}
            dws = wp.get("doorways") or []
            sf = None
            if g["shape"] == "RECT":
                missing = [d.get("door_id") or "?" for d in dws if d.get("width_m") is None or d.get("depth_m") is None]
                if missing:
                    unresolved.append({"room_id": r["room_id"], "item": "FIN.WP.DOORWAY",
                                       "reason": f"DOORWAY_DIMENSIONS_NOT_ESTABLISHED: {missing}"})
                    dws = [d for d in dws if d.get("door_id") not in missing]
                sf = ML.surfaces(r, upturn_h=up_rule["value"], doorways=dws,
                                 doorway_detail=wp.get("doorway_detail", "NOT_ESTABLISHED"))
            wl = {}
            if sf is None:
                q = ("ROOM_GEOMETRY_NOT_ESTABLISHED" if g["shape"] == "MISSING" else
                     "UPTURN_RUN_NOT_ESTABLISHED: polygon wet rooms are S2 (the perimeter is known, the doorway "
                     "segments and roll plan are not)")
                for ic, rid in (("FIN.WP.FLOOR", "UP-WP-001"), ("FIN.WP.UPTURN", "UP-WP-002")):
                    net = g["area_m2"] if ic == "FIN.WP.FLOOR" and g["area_m2"] is not None else None
                    ln = _line(s, r, item_code=ic, element=ic.split(".")[-1].lower(), net=net,
                               formula="floor polygon area" if net is not None else "not established", inputs={},
                               rule_id=rid, rfi=None if net is not None else {"question": q, "unlocks": r["room_id"]})
                    lines.append(ln)
                    wl[ic] = ln
                    if net is None:
                        unresolved.append({"room_id": r["room_id"], "item": ic, "reason": q})
                mats.append(WP.blocked(method=ML.METHOD, spec=MS.membrane(wp.get("spec_id") or MS.DEFAULT_MEMBRANE),
                                       reason=ML.POLYGON_BLOCK if g["shape"] == "POLYGON" else q,
                                       line_id=wl["FIN.WP.FLOOR"]["line_id"], location=TL._loc(r)))
                continue
            for row in sf["rows"]:
                rid = {"FIN.WP.FLOOR": "UP-WP-001", "FIN.WP.DOORWAY": "UP-WP-003", "FIN.WP.UPTURN": "UP-WP-002"}[row["item_code"]]
                el = row.get("doorway") and f"doorway {row['doorway']}" or row["item_code"].split(".")[-1].lower()
                notes = "; ".join(sf["flags"]) if row["item_code"] != "FIN.WP.FLOOR" and sf["flags"] else ""
                ln = _line(s, r, item_code=row["item_code"], element=el, net=row["net_m2"], formula=row["formula"],
                           inputs=row["inputs"], rule_id=rid, notes=notes)
                lines.append(ln)
                wl.setdefault(row["item_code"], ln)
            spec = MS.membrane(wp.get("spec_id") or MS.DEFAULT_MEMBRANE, **(wp.get("overrides") or {}))
            if wp.get("data_sheet"):
                spec = MS.apply_data_sheet(spec, wp["data_sheet"])
            c = {"upturn_h_m": up_rule["value"], "doorways": dws, "doorway_detail": wp.get("doorway_detail", "NOT_ESTABLISHED"),
                 "direction": wp.get("direction", "MIN_MATERIAL"), "penetrations": wp.get("penetrations", 0),
                 "min_reusable_m": (s.get("assumptions") or {}).get("membrane_min_reusable_m"),
                 "rule_refs": [_ref("UP-WP-005"), _ref("UP-WP-002"), _ref("UP-WP-003")]}
            res = ML.plan(dict(r, line_id=wl["FIN.WP.FLOOR"]["line_id"]), spec, constraints=c)
            for comp in res["components"]:
                comp["line_ids"] = [x["line_id"] for x in lines if x["location"]["room_id"] == r["room_id"]
                                    and x["item_code"] == comp["item_code"]]
            mats.append(res)
            for f in sf["flags"]:
                if f.startswith("DOORWAY_UPTURN_DETAIL") or f.startswith("DOORWAY_DOUBLE"):
                    unresolved.append({"room_id": r["room_id"], "item": "FIN.WP.DOORWAY / FIN.WP.UPTURN",
                                       "reason": f"{f}: Q-WP-1 how the doorway 0.20 m is built and whether it is billed "
                                                 f"in addition to the doorway floor piece (UP-WP-003 v1.1.0)"})
            for cn in res["concerns"]:
                if cn.startswith(("CORNER_", "PENETRATION_")):
                    unresolved.append({"room_id": r["room_id"], "item": "FIN.WP (detailing)", "reason": cn})
    return {"schema": "URBAN_ROOM_BOQ_V1", "project_id": s["project_id"], "rule_set": RULE_SET,
            "rule_set_digest": RS.rule_set(RULE_SET)["digest"], "lines": lines, "materials": mats,
            "comparisons": comps, "unresolved": unresolved, "assumptions": assumptions,
            "geometry_source": s["geometry_source"]}
