"""R8.18 lab: the BLIND Qortuba run of the frozen WALL_FACE_SURFACE_POLICY_V2 + WALL_HEIGHT_AUTHORITY_POLICY_V1 +
REVEAL_FINISH_POLICY_V1 + WATERPROOFING_POLICY_V1 + QORTUBA-NEW-WALL-FACE-METHOD@v2 (wall surfaces, heights, reveal
ownership / finish, plaster / paint / wall tile / tile-prep rows, waterproofing rows).

    python3 research/external_engine_lab/r8_18_blind.py <work> <out.json>

All authority data comes from the freeze record. No expected value, no historical quantity is read.
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
import r8_17_wall_blind as W17                                                                # noqa: E402
from engine.source import opening_reveals as OR, reveal_finish as RF, wall_contact_path as WC  # noqa: E402
from engine.source import wall_faces as V1, wall_faces_v2 as WF, wall_height as WH            # noqa: E402
from engine.source import waterproofing as WP                                                 # noqa: E402

FZ_FILE = ROOT / "tests/r8_18/registers/R8_18_FREEZE.json"
HEAD_MAP = {OR.WITH_HEAD: WF.WITH_HEAD, OR.FULL_HEIGHT: WF.FULL_HEIGHT}
DRY = "DRY_INTERNAL_ROOM"


def heights(wm):
    out = {}
    for key, cands in wm["height_scopes"].items():
        cs = []
        for c in cands:
            if c["kind"] == "DERIVED_CLEAR_HEIGHT":
                d = WH.derive(c["gross_m"], c["gross_authority"], c["components"])
                cs.append(dict(WH.candidate("DERIVED_CLEAR_HEIGHT", d["value_m"],
                                            d["gross_authority"] if d["state"] == WH.ESTABLISHED else None),
                               derivation=d))
            else:
                cs.append(WH.candidate(c["kind"], c["value_m"], c["authority"]))
        cls, trade = key.split("|")
        out[key] = WH.resolve({"class": cls, "trade": trade, **wm["scope"]}, cs)
    return out


def drawn(parts, a, b, eps):
    L = math.dist(a, b)
    return L > eps and any(p.kind == "SEGMENT" and WC._overlap(a, b, tuple(p.geometry[:2]), tuple(p.geometry[2:4]),
                                                                eps) >= L - 2 * eps for p in parts)


def run(res, inp, fz):
    wm = fz["qortuba_wall_face_method"]
    eps = R14.Q11.TP.tolerances(R14.Q11.RT.max_abs_coordinate(inp.parts), inp.unit_native_to_mm)["eps_r"]
    u = inp.unit_native_to_mm / 1000
    dry, wet = SB.dry_and_wet_sites(res)
    classes = {sid: DRY for sid, _z in dry} | {sid: why.split()[0] for sid, _z, why in wet}
    zones = {sid: z for sid, z in dry} | {sid: z for sid, z, _w in wet}
    sites = {s["site_id"]: s for s in res["sites"]}
    _, states = SB.obstacle_states(res, inp)
    bands = {b["band_id"]: b for b in res["wall_bands"]["bands"]}
    sf, sb, smap = B17.slide_contact(inp)
    gj = WC.glazed_door_jambs(res["closures"], {k: v for k, v in smap.items() if k.startswith("GLAZED|")})
    pj = [j for p in res["passages"] for j in WC.passage_jambs(p, bands, eps)]
    dj = WC.door_jambs(res["openings"], res["closures"])
    jambs = pj + dj + gj
    fcm, win_contact, wbind = W17.contact_all(res, inp, smap, wm)
    oh = wm["opening_heights"]
    oheights = {occ: {"height_m": oh["DOOR"]["height_m"], "authority": oh["DOOR"]["authority"]}
                for occ in res["openings"]}
    if sb["binding"] == "APPLIES":
        oheights |= {k: {"height_m": oh["SLIDING_GLAZED_DOOR"]["height_m"],
                         "authority": oh["SLIDING_GLAZED_DOOR"]["authority"]} for k in smap}
    for k, st in win_contact.items():
        oheights[k] = {"height_m": oh["WINDOW"]["height_m"], "authority": oh["WINDOW"]["authority"],
                       "sill_m": st["sill_m"], "sill_authority": st["authority"]}
    hd, hwhy, pfact = W17.heads(res, inp)
    H = heights(wm)
    # ---------------------------------------------------------------- wall surfaces per site and trade height
    per = {}
    for sid, cls in classes.items():
        trades = {t: r for t, r in wm["trade_rules"][cls].items()}
        psg = [{"passage_id": p["passage_id"], "width_m": round(p["width_mm"] / 1000, 6),
                "head": HEAD_MAP.get(hd.get(p["passage_id"])),
                "head_height_m": pfact.statement.get("clear_height_m") if hd.get(p["passage_id"]) == OR.WITH_HEAD
                else None, "head_authority": hwhy.get(p["passage_id"]) if hd.get(p["passage_id"]) else None}
               for p in res["passages"] if p["strip_in_site"] == sid]
        rec = {"zones": zones[sid], "class": cls, "trades": trades, "passages_in_site": psg, "faces": {}}
        for t, r in trades.items():
            if r["state"] != "APPLIES":
                continue
            h = H[f"{cls}|{r['height_scope']}"]
            rec["faces"][t] = WF.site_faces(WC.site_edges(res["_arr"], sites[sid]), u=u, height_m=h["value_m"],
                                            height_authority=h["authority"], jambs=jambs, eps=eps,
                                            obstacle_authority=states, floor_contact_by_entity=fcm,
                                            opening_heights=oheights, passages=psg)
        per[sid] = rec
    # ---------------------------------------------------------------- reveals: ownership from frame position, finish
    closure_site = {}
    for sid in classes:
        for e in WC.site_edges(res["_arr"], sites[sid]):
            for s in e["sources"]:
                if s.startswith("CLOSURE|"):
                    closure_site.setdefault(s, sid)
    reveals = []

    def finish(owner_sid, explicit=None):
        cls = classes.get(owner_sid)
        if cls is None:
            return "OUT_OF_MEASURED_SCOPE", ()
        st = RF.finish_state(ownership_established=True, owner_painted_dry=cls == DRY, explicit=explicit)
        return st, RF.TRADES[st]

    def add(opening, kind, surface, owner, depth, size, size_key, basis, authority, explicit=None, state=None):
        if state == RF.UNRESOLVED:
            reveals.append({"opening": opening, "kind": kind, "surface": surface, "owner_site": owner,
                            "owner_zones": zones.get(owner), "finish": RF.UNRESOLVED, "trades": [], "area_m2": None,
                            "depth_m": depth, "depth_basis": basis, "authority": authority, "state": "UNRESOLVED"})
            return
        fs, tr = finish(owner, explicit)
        reveals.append({"opening": opening, "kind": kind, "surface": surface, "owner_site": owner,
                        "owner_zones": zones.get(owner), "owner_class": classes.get(owner), "finish": fs,
                        "trades": list(tr), "depth_m": round(depth, 6), size_key: round(size, 6),
                        "area_m2": round(depth * size, 6), "depth_basis": basis, "authority": authority,
                        "state": "COMPUTED" if fs != "OUT_OF_MEASURED_SCOPE" else fs})
    geo = {c.source_id: c.geometry for c in res["closures"]}
    for occ, st in sorted(res["openings"].items()):
        js = [j for j in dj if j["opening"] == occ]
        if not js or not st.get("closure_a"):
            continue
        a_site, b_site = closure_site.get(st["closure_a"]), closure_site.get(st["closure_b"])
        depth = max(j["length"] for j in js) * u
        split = RF.frame_split(depth, [0.0], side_a=a_site or "OUTSIDE_A", side_b=b_site or "OUTSIDE_B")
        owner = b_site if (b_site and split[b_site or "OUTSIDE_B"]) else None
        basis = "SOURCE: closed-leaf line (closure A) on the strip face -> the full depth faces the other room"
        w = st["width"] * u
        for s in ("LEFT_JAMB", "RIGHT_JAMB"):
            add(occ, "DOOR", s, owner, depth, oh["DOOR"]["height_m"], "height_m", basis, oh["DOOR"]["authority"],
                state=None)
        add(occ, "DOOR", "TOP_REVEAL", owner, depth, w, "width_m", basis, oh["DOOR"]["authority"])
    if gj and sb["binding"] == "APPLIES":
        oid = gj[0]["opening"]
        f1, f2 = geo[f"CLOSURE|{oid}|F1"], geo[f"CLOSURE|{oid}|F2"]
        p1 = [(f1[0], f1[1]), (f1[2], f1[3])]
        p2 = [(f2[0], f2[1]), (f2[2], f2[3])]
        depth_n = math.dist(p1[0], min(p2, key=lambda z: math.dist(p1[0], z)))
        q = min(p2, key=lambda z: math.dist(p1[0], z))
        nx, ny = (q[0] - p1[0][0]) / depth_n, (q[1] - p1[0][1]) / depth_n
        parts = {p.identity.key: p for p in inp.parts}
        offs = [((parts[k].geometry[0] - p1[0][0]) * nx + (parts[k].geometry[1] - p1[0][1]) * ny) * u
                for k, _fp, _r in sf.parts if k in parts]
        a_site, b_site = closure_site.get(f"CLOSURE|{oid}|F1"), closure_site.get(f"CLOSURE|{oid}|F2")
        split = RF.frame_split(depth_n * u, offs, side_a=a_site, side_b=b_site)
        basis = "SOURCE: aluminium track lines (the bound glazing parts) inside the wall"
        width = math.dist(*p1) * u
        for side, face_pts, sign in ((a_site, p1, 1.0), (b_site, p2, -1.0)):
            d = split[side]
            if not d:
                continue                                               # frame flush with this face: no reveal
            for end, surf in ((face_pts[0], "LEFT_JAMB"), (face_pts[1], "RIGHT_JAMB")):
                tip = (end[0] + sign * nx * d / u, end[1] + sign * ny * d / u)
                ok = drawn(inp.parts, end, tip, eps)
                add(oid, "SLIDING_GLAZED_DOOR", surf, side, d, oh["SLIDING_GLAZED_DOOR"]["height_m"], "height_m",
                    basis + ("; reveal face drawn" if ok else "; NO reveal face drawn on this side (wall cavity)"),
                    oh["SLIDING_GLAZED_DOOR"]["authority"], state=None if ok else RF.UNRESOLVED)
            add(oid, "SLIDING_GLAZED_DOOR", "TOP_REVEAL", side, d, width, "width_m", basis,
                oh["SLIDING_GLAZED_DOOR"]["authority"])
        sliding_split = split
    else:
        sliding_split = None
    for p in res["passages"]:
        sid = p["strip_in_site"]
        if sid not in classes:
            continue
        head = hd.get(p["passage_id"])
        phys = [j for j in pj if j["opening"] == p["passage_id"] and WC.is_physical_jamb(j)]
        ht = pfact.statement.get("clear_height_m") if head == OR.WITH_HEAD else \
            H[f"{classes[sid]}|PLASTER"]["value_m"] if head == OR.FULL_HEIGHT else None
        depth = p["thickness_mm"] / 1000
        explicit = None                                        # plaster is the default; only porcelain / other is "explicit"
        for j in phys:
            add(p["passage_id"], HEAD_MAP.get(head, "PASSAGE"), f"{j['side']}_JAMB", sid, depth, ht or 0.0, "height_m",
                "SOURCE (band thickness)", hwhy.get(p["passage_id"]), explicit=explicit,
                state=None if ht else RF.UNRESOLVED)
        if head == OR.WITH_HEAD:
            add(p["passage_id"], WF.WITH_HEAD, "TOP_REVEAL", sid, depth, p["width_mm"] / 1000, "width_m",
                "SOURCE (band thickness)", hwhy.get(p["passage_id"]), explicit=explicit)
    for k in sorted(win_contact):
        sids = [sid for sid in classes if any(WC._entity(x) == k for e in WC.site_edges(res["_arr"], sites[sid])
                                              for x in e["sources"])]
        width = max((e["length"] for sid in sids for e in WC.site_edges(res["_arr"], sites[sid])
                     if any(WC._entity(x) == k for x in e["sources"])), default=None)
        if width is None or len(sids) != 1:
            continue
        d = wm["window_reveal_depth"]["depth_m"]
        for s in ("LEFT_JAMB", "RIGHT_JAMB"):
            add(k, "WINDOW", s, sids[0], d, oh["WINDOW"]["height_m"], "height_m", wm["window_reveal_depth"]["basis"],
                oh["WINDOW"]["authority"])
        add(k, "WINDOW", "TOP_REVEAL", sids[0], d, width * u, "width_m", wm["window_reveal_depth"]["basis"],
            oh["WINDOW"]["authority"])
    guard = WF.double_count_guard({sid: next(iter(v["faces"].values())) for sid, v in per.items() if v["faces"]},
                                  reveals)
    # ---------------------------------------------------------------- trade rows
    rows = {}
    for trade in ("PLASTER", "PAINT", "WALL_TILE", "WET_WALL_TILE_PREP"):
        rooms, unresolved, blocked = {}, [], []
        for sid, v in per.items():
            f = v["faces"].get(trade)
            if f is None:
                continue
            if f["state"] != WF.COMPUTED:
                blocked.append({"site": sid, "zones": v["zones"], "blockers": f["blockers"]})
                continue
            a = f["areas_m2"]
            rv = [x for x in reveals if x["owner_site"] == sid and trade in x["trades"]]
            room = {"zones": v["zones"], "class": v["class"], "height_m": f["height_m"],
                    "height_authority": f["height_authority"], "wall_plane_net_m2": a["WALL_PLANE_NET"],
                    "opening_rectangles_m2": a["opening_rectangles"], "passage_head_faces_m2": a["passage_head_faces"],
                    "jamb_reveals_m2": round(math.fsum(x["area_m2"] for x in rv if x["surface"] != "TOP_REVEAL"), 6),
                    "head_reveals_m2": round(math.fsum(x["area_m2"] for x in rv if x["surface"] == "TOP_REVEAL"), 6),
                    "reconciliation": f["reconciliation"]["state"]}
            room["authorised_m2"] = round(room["wall_plane_net_m2"] + room["jamb_reveals_m2"] + room["head_reveals_m2"],
                                          6)
            for cls_key, rule in (("COLUMN_FACE", wm["column_faces"][trade]), ("OBSTACLE_FACE",
                                                                                  wm["obstacle_faces"][trade])):
                if a[cls_key]:
                    if rule == "INCLUDED":
                        room["authorised_m2"] = round(room["authorised_m2"] + a[cls_key], 6)
                        room[cls_key.lower() + "_m2"] = a[cls_key]
                    else:
                        unresolved.append({"site": sid, "zones": v["zones"], "class": cls_key, "area_m2": a[cls_key],
                                           "why": wm["unresolved_why"][cls_key]})
            rooms[sid] = room
        wet_rv = [x for x in reveals if trade == "PLASTER" and "PLASTER" in x["trades"] and
                  classes.get(x["owner_site"]) not in (None, DRY)]
        un_rv = [x for x in reveals if x["finish"] == RF.UNRESOLVED and trade in ("PLASTER", "PAINT") and
                 classes.get(x["owner_site"]) == DRY]
        sub = round(math.fsum(r["authorised_m2"] for r in rooms.values()), 6)
        rows[trade] = {"rooms": rooms, "AUTHORISED_SUBTOTAL_M2": sub if not blocked else None,
                       "COMPLETE_M2": sub if not (blocked or unresolved or un_rv) else None,
                       "unresolved_contributors": unresolved,
                       "unresolved_reveals": [{k: x[k] for k in ("opening", "surface", "owner_zones", "depth_basis")}
                                              for x in un_rv],
                       "blocked_rooms": blocked,
                       "state": "BLOCKED" if blocked or not rooms else
                       ("COMPUTED_SHADOW" if not (unresolved or un_rv) else "COMPUTED_SHADOW_WITH_UNRESOLVED")}
        if trade == "PLASTER":
            rows[trade]["wet_service_owned_reveal_plaster_m2"] = round(math.fsum(x["area_m2"] for x in wet_rv), 6)
            rows[trade]["wet_service_owned_reveals"] = [{k: x[k] for k in ("opening", "surface", "owner_zones",
                                                                           "area_m2")} for x in wet_rv]
            rows[trade]["wet_service_owned_unresolved_reveals"] = [
                {k: x[k] for k in ("opening", "surface", "owner_zones", "depth_basis")} for x in reveals
                if x["finish"] == RF.UNRESOLVED and classes.get(x["owner_site"]) not in (None, DRY)]
    # ---------------------------------------------------------------- waterproofing
    wpm = wm["waterproofing"]
    wpr = {}
    for sid, cls in classes.items():
        if cls not in wpm["classes"]:
            continue
        s = sites[sid]
        wpr[sid] = dict(WP.wet_room(WC.site_edges(res["_arr"], s), area_m2=s["area_m2"], u=u,
                                    upturn_height_m=wpm["upturn_height_m"], upturn_authority=wpm["upturn_authority"],
                                    include_holes=wpm["include_holes"]), zones=zones[sid], class_=cls,
                        authority=wpm["classes"][cls])
    wtot = {WP.FLOOR: round(math.fsum(v[WP.FLOOR] for v in wpr.values()), 6),
            WP.UPTURN: round(math.fsum(v[WP.UPTURN] for v in wpr.values()), 6)}
    conflicts = WH.conflict({"WALL_TILE": H["WET_SERVICE_ROOM|WALL_TILE"]["value_m"]},
                            {"value_m": H[f"{DRY}|PLASTER"]["value_m"], "proven": False,
                             "basis": "the owner's DRY rationale (4.00 - 0.60 - 0.15 - 0.10): components not source"})
    return {"heights": H, "height_conflicts": conflicts, "per_site": per, "reveals": reveals,
            "sliding_door_split": sliding_split, "double_count_guard": guard, "trade_rows": rows,
            "waterproofing": {"rooms": wpr, "totals": wtot}, "window_sill_fact_binding": wbind,
            "sliding_door_fact": {"fact": sf.ref, "binding": sb["binding"]},
            "all_sites_reconcile": all(f.get("reconciliation", {}).get("state") == "PASS" for v in per.values()
                                       for f in v["faces"].values())}


def main(work, out):
    fz = json.loads(FZ_FILE.read_text())
    R = R14.R13.runs(work, None)
    new, inp_new = R["new"], R["inputs"]["NEW_K2"]
    rec = {"SCHEMA": "URBAN_R8_18_WALL_FACE_V2_BLIND_RESULT_V1", "freeze": fz["frozen_commit"],
           "policies": fz["policies"], "method": fz["qortuba_wall_face_method"]["ref"],
           "blind": {"expected_value_given": False, "historical_quantities_used": False, "r8_17_values_read": False},
           "run_input_digest": new["run_manifest"]["RUN_INPUT_DIGEST"], **run(new, inp_new, fz)}
    Path(out).write_text(json.dumps(rec, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({t: (v["state"], v["AUTHORISED_SUBTOTAL_M2"], v["COMPLETE_M2"]) for t, v in
                      rec["trade_rows"].items()} | {"waterproofing": rec["waterproofing"]["totals"],
                                                    "reconcile": rec["all_sites_reconcile"],
                                                    "guard": rec["double_count_guard"]["state"]}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
