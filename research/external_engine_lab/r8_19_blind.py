"""R8.19 lab: the BLIND Qortuba run of the frozen EXPOSED_OBJECT_FINISH_POLICY_V1 + REVEAL_PHYSICALITY_POLICY_V1 +
QORTUBA-NEW-WALL-FACE-METHOD@v3 over the frozen R8.18 surface model (WALL_FACE_SURFACE_POLICY_V2, heights, reveal
ownership / finish, waterproofing).

The wall-plane surfaces, reveal geometry and waterproofing come from the frozen R8.18 run; the reveal-face evidence of
that run is REPLACED by the physicality policy (admitted wall parts or an established band OPENING_JAMB end; a fixture
line never counts). Every trade row is rebuilt from SURFACE RECORDS: wall plane surfaces + exposed object faces +
physically established reveals. No R8.18 total, no diagnostic area, no expected value is read.

    python3 research/external_engine_lab/r8_19_blind.py <work> <out.json>
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_14_qortuba as R14                                                                   # noqa: E402
import r8_15_skirting_blind as SB                                                             # noqa: E402
import r8_17_blind as B17                                                                     # noqa: E402
import r8_18_blind as BL                                                                      # noqa: E402
from engine.source import exposed_finish as EF, reveal_finish as RF, reveal_physicality as RP  # noqa: E402
from engine.source import wall_contact_path as WC, wall_faces_v2 as WF                        # noqa: E402

FZ_FILE = ROOT / "tests/r8_19/registers/R8_19_FREEZE.json"
FZ18_FILE = ROOT / "tests/r8_18/registers/R8_18_FREEZE.json"
DRY = "DRY_INTERNAL_ROOM"


def r6(v):
    return None if v is None else round(v, 6)


def evidence(res, inp):
    """The physicality evidence pools: admitted wall / structural parts, established band ends, everything else."""
    keys = {}
    for e in res["_arr"].edges:
        for s in e["sources"]:
            keys.setdefault(s, set()).update(e["roles"])
    segs = [p for p in inp.parts if p.kind == "SEGMENT"]
    walls = [(p.identity.key, keys.get(p.identity.key, set()), tuple(p.geometry[:4])) for p in segs
             if keys.get(p.identity.key, set()) & set(RP.ADMITTED_ROLES)]
    wk = {w[0] for w in walls}
    others = [(p.identity.key, p.layer, tuple(p.geometry[:4])) for p in segs if p.identity.key not in wk]
    ends = [{"band_id": b["band_id"], "state": b["state"], "kind": e["kind"], "opening": e.get("opening") or [],
             "segment": tuple(e["face_a_end"]) + tuple(e["face_b_end"])}
            for b in res["wall_bands"]["bands"] for e in b["ends"]]
    return walls, ends, others


def object_segments(res, inp, states, u):
    roles = res["roles"]["roles"]
    seg = lambda p: math.dist(p.geometry[:2], p.geometry[2:4]) * u                          # noqa: E731
    col = {p.identity.key: {"object": WC._entity(p.identity.key), "length_m": round(seg(p), 9)} for p in inp.parts
           if p.kind == "SEGMENT" and roles.get(p.identity.key) is not None and
           roles[p.identity.key].role == "STRUCTURAL_OBSTACLE"}
    obs = {p.identity.key: {"object": WC._entity(p.identity.key), "length_m": round(seg(p), 9)} for p in inp.parts
           if p.kind == "SEGMENT" and states.get(WC._entity(p.identity.key))}
    return col, obs


def run(res, inp, fz):
    fz18 = json.loads(FZ18_FILE.read_text())
    wm = fz["qortuba_wall_face_method"]
    eps = R14.Q11.TP.tolerances(R14.Q11.RT.max_abs_coordinate(inp.parts), inp.unit_native_to_mm)["eps_r"]
    u = inp.unit_native_to_mm / 1000
    walls, ends, others = evidence(res, inp)
    sf, sb, smap = B17.slide_contact(inp)
    gj = WC.glazed_door_jambs(res["closures"], {k: v for k, v in smap.items() if k.startswith("GLAZED|")})
    oid = gj[0]["opening"] if gj else None
    log = []

    def drawn(_parts, a, b, _eps):                                    # the R8.18 reveal-face check, replaced
        p = RP.physicality(a, b, depth_m=None, opening=oid, wall_parts=walls, band_ends=ends, other_parts=others,
                           eps=eps)
        log.append(p)
        return p["state"] == RP.ESTABLISHED
    orig = BL.drawn
    BL.drawn = drawn
    try:
        base = BL.run(res, inp, fz18)
    finally:
        BL.drawn = orig
    per, reveals = base["per_site"], base["reveals"]
    classes = {sid: v["class"] for sid, v in per.items()}
    # ---------------------------------------------------------------- reveal physicality (before finish)
    sl = [x for x in reveals if x["kind"] == "SLIDING_GLAZED_DOOR" and x["surface"] != "TOP_REVEAL"]
    if len(sl) != len(log):
        raise RuntimeError("sliding-door reveal / physicality log mismatch")
    basis = {"DOOR": "PHYSICAL_DOOR_STRIP_JAMB (door strip site side; V4 physical jamb record)",
             "OPEN_PASSAGE_WITH_HEAD": "PHYSICAL_PASSAGE_JAMB / PASSAGE_HEAD (physical jamb record; owner head fact)",
             "OPEN_PASSAGE_FULL_HEIGHT": "PHYSICAL_PASSAGE_JAMB (physical jamb record)",
             "WINDOW": "OPENING_IN_ADMITTED_WALL (window span on an admitted wall line; depth US-07)",
             "SLIDING_GLAZED_DOOR": "OPENING_HEAD (wall above the 2.20 m opening in the established band)"}
    for x in reveals:
        if x["state"] == "OUT_OF_MEASURED_SCOPE":
            x["physicality"] = {"state": "OUT_OF_MEASURED_SCOPE"}
        elif any(x is y for y in sl):
            p = log[next(i for i, y in enumerate(sl) if x is y)]
            x["physicality"] = {k: p[k] for k in ("state", "segment", "evidence", "rejected", "why")}
            if p["state"] == RP.ESTABLISHED and x["finish"] == RF.UNRESOLVED:     # never: the frozen run decided on it
                raise RuntimeError("physicality / finish disagreement")
        else:
            x["physicality"] = {"state": RP.ESTABLISHED, "evidence": [{"kind": basis[x["kind"]]}]}
        x["included"] = x["physicality"]["state"] == RP.ESTABLISHED and bool(x["trades"])
    # ---------------------------------------------------------------- exposed object faces
    _, states = SB.obstacle_states(res, inp)
    col, obs = object_segments(res, inp, states, u)
    spans = {sid: next(iter(v["faces"].values()))["spans"] for sid, v in per.items() if v["faces"]}
    xcol, xobs = EF.exposure(col, spans, EF.COLUMN_FACE), EF.exposure(obs, spans, EF.OBSTACLE_FACE)
    rules = wm["object_face_rules"]
    obj_surf, obj_unres = [], []
    for sid, v in per.items():
        room_trades = sorted(v["faces"])
        for cls, x in ((EF.COLUMN_FACE, xcol), (EF.OBSTACLE_FACE, xobs)):
            for obj in sorted({f["object"] for f in x["faces"] if f["site"] == sid}):
                faces = [f for f in x["faces"] if f["site"] == sid and f["object"] == obj]
                auth = cls == EF.COLUMN_FACE or states.get(obj) == WC.OWNER_PHYSICAL_OBSTACLE
                a = EF.assign(cls, v["class"], room_trades, rules[cls], owner_physical_authority=auth)
                for t in room_trades:
                    f_t = v["faces"][t]
                    if a["state"] != EF.INCLUDED:
                        obj_unres += [{"site": sid, "trade": t, "class": cls, "object": obj, "segment": f["segment"],
                                       "length_m": f["length_m"], "why": a["why"]} for f in faces]
                        continue
                    for s in EF.surfaces(faces, site=sid, height_m=f_t["height_m"],
                                         height_authority=f_t["height_authority"], assignment=a):
                        obj_surf.append(dict(s, trade=t))
    for cls, x in ((EF.COLUMN_FACE, xcol), (EF.OBSTACLE_FACE, xobs)):          # fail closed: never dropped
        for e in x["errors"]:
            if e.get("site") in per:
                obj_unres += [{"site": e["site"], "trade": t, "class": cls, "object": None, "segment": None,
                               "length_m": e["span"]["length_m"], "why": e["error"]} for t in per[e["site"]]["faces"]]
    # ---------------------------------------------------------------- trade rows from surface records
    rows = {}
    for row_id, d in wm["rows"].items():
        t, cls_ok = d["trade"], set(d["classes"])
        sids = [sid for sid in per if classes[sid] in cls_ok]
        rooms, blocked, unresolved, surfaces = {}, [], [], []
        for sid in sids:
            v = per[sid]
            f = v["faces"].get(t)
            room = {"zones": v["zones"], "class": v["class"], "height_m": f["height_m"] if f else None,
                    "height_authority": f["height_authority"] if f else None}
            srf = []
            if not d.get("reveals_only"):
                if f is None or f["state"] != WF.COMPUTED:
                    blocked.append({"site": sid, "zones": v["zones"], "blockers": (f or {}).get("blockers")})
                    continue
                srf += [{"id": ["PLANE", sid, s["class"], sorted(s.get("sources", ())), str(s.get("geom")),
                                s.get("opening"), s.get("side")], "kind": "WALL_PLANE", "class": s["class"],
                         "area_m2": s["area_m2"]} for s in f["surfaces"]]
                srf += [{"id": ["OBJECT", sid, s["class"], s["segment"]], "kind": "OBJECT_FACE", "class": s["class"],
                         "object": s["object"], "segment": s["segment"], "length_m": s["length_m"],
                         "height_m": s["height_m"], "area_m2": s["area_m2"], "rule": s["rule"]}
                        for s in obj_surf if s["site"] == sid and s["trade"] == t]
                unresolved += [dict(x, area_m2=r6(x["length_m"] * f["height_m"])) for x in obj_unres
                               if x["site"] == sid and x["trade"] == t]
            srf += [{"id": ["REVEAL", x["opening"], sid, x["surface"]], "kind": "REVEAL", "class": x["surface"],
                     "opening": x["opening"], "finish": x["finish"], "area_m2": x["area_m2"],
                     "physicality": x["physicality"]["state"]}
                    for x in reveals if x["owner_site"] == sid and x["included"] and t in x["trades"]]
            unresolved += [{"site": sid, "class": "REVEAL", "opening": x["opening"], "surface": x["surface"],
                            "physicality": x["physicality"]["state"], "area_m2": None,
                            "why": x["physicality"].get("why")}
                           for x in reveals if x["owner_site"] == sid and
                           (x["physicality"]["state"] == RP.UNRESOLVED or x["finish"] == RF.UNRESOLVED)
                           and t in RF.TRADES[RF.finish_state(ownership_established=True,
                                                              owner_painted_dry=classes[sid] == DRY)]]
            by = {}
            for s in srf:
                by[s["kind"]] = by.get(s["kind"], 0.0) + s["area_m2"]
            room.update({"wall_plane_m2": r6(by.get("WALL_PLANE", 0.0)),
                         "column_face_m2": r6(math.fsum(s["area_m2"] for s in srf if s["class"] == EF.COLUMN_FACE)),
                         "obstacle_face_m2": r6(math.fsum(s["area_m2"] for s in srf
                                                          if s["class"] == EF.OBSTACLE_FACE)),
                         "jamb_reveals_m2": r6(math.fsum(s["area_m2"] for s in srf if s["kind"] == "REVEAL" and
                                                         s["class"] != "TOP_REVEAL")),
                         "head_reveals_m2": r6(math.fsum(s["area_m2"] for s in srf if s["kind"] == "REVEAL" and
                                                         s["class"] == "TOP_REVEAL")),
                         "total_m2": r6(math.fsum(s["area_m2"] for s in srf)), "surfaces": len(srf)})
            rooms[sid] = room
            surfaces += [dict(s, site=sid) for s in srf]
        sub = r6(math.fsum(r["total_m2"] for r in rooms.values())) if not blocked else None
        state = "BLOCKED" if blocked or not rooms else \
            ("COMPUTED_SHADOW_COMPLETE" if not unresolved else "AUTHORISED_SUBTOTAL")
        rows[row_id] = {"trade": t, "classes": sorted(cls_ok), "rooms": rooms, "AUTHORISED_SUBTOTAL_M2": sub,
                        "COMPLETE_M2": sub if state == "COMPUTED_SHADOW_COMPLETE" else None, "state": state,
                        "unresolved_contributors": unresolved, "blocked_rooms": blocked, "surfaces": surfaces}
    ids = [json.dumps(s["id"]) for r in rows.values() for s in r["surfaces"]]
    by_trade = {}
    for r in rows.values():
        for s in r["surfaces"]:
            by_trade.setdefault(r["trade"], []).append(json.dumps(s["id"]))
    dup = sorted({i for t, xs in by_trade.items() for i in xs if xs.count(i) > 1})
    pl = {json.dumps(s["id"]) for s in rows["DRY_WALL_PLASTER"]["surfaces"]}
    pa = {json.dumps(s["id"]) for s in rows["DRY_WALL_PAINT"]["surfaces"]}
    return {"heights": base["heights"], "height_conflicts": base["height_conflicts"],
            "all_sites_reconcile": base["all_sites_reconcile"], "double_count_guard_r8_18": base["double_count_guard"],
            "object_exposure": {"COLUMN_FACE": xcol, "OBSTACLE_FACE": xobs, "obstacle_states": states},
            "reveals": reveals, "sliding_door_split": base["sliding_door_split"],
            "sliding_door_physicality": [{"reveal": [x["opening"], x["owner_site"], x["surface"]],
                                          **x["physicality"]} for x in sl],
            "trade_rows": rows,
            "PLASTER_ALL_SURFACES_M2": r6(math.fsum(s["area_m2"] for r in rows.values() if r["trade"] == "PLASTER"
                                                    for s in r["surfaces"])),
            "paint_vs_plaster": {"same_surface_set": pl == pa, "only_plaster": sorted(pl - pa),
                                 "only_paint": sorted(pa - pl)},
            "surface_guard": {"surfaces": len(ids), "duplicates_within_a_trade": dup,
                              "state": "PASS" if not dup else "FAIL"},
            "waterproofing": base["waterproofing"], "window_sill_fact_binding": base["window_sill_fact_binding"],
            "sliding_door_fact": base["sliding_door_fact"]}


def main(work, out):
    fz = json.loads(FZ_FILE.read_text())
    R = R14.R13.runs(work, None)
    new, inp_new = R["new"], R["inputs"]["NEW_K2"]
    rec = {"SCHEMA": "URBAN_R8_19_BLIND_RESULT_V1", "freeze": fz["frozen_commit"], "policies": fz["policies"],
           "method": fz["qortuba_wall_face_method"]["ref"],
           "blind": {"expected_value_given": False, "historical_quantities_used": False,
                     "r8_18_totals_read": False, "r8_18_diagnostic_areas_read": False},
           "run_input_digest": new["run_manifest"]["RUN_INPUT_DIGEST"], **run(new, inp_new, fz)}
    Path(out).write_text(json.dumps(rec, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({t: (v["state"], v["AUTHORISED_SUBTOTAL_M2"], v["COMPLETE_M2"]) for t, v in
                      rec["trade_rows"].items()} | {"plaster_all": rec["PLASTER_ALL_SURFACES_M2"],
                                                    "paint_vs_plaster": rec["paint_vs_plaster"]["same_surface_set"],
                                                    "guard": rec["surface_guard"]["state"],
                                                    "waterproofing": rec["waterproofing"]["totals"]}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
