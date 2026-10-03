"""R8.17 lab: the BLIND Qortuba run of the frozen WALL_FACE_SURFACE_POLICY_V1 + QORTUBA-NEW-WALL-FACE-METHOD@v1
(physical wall surfaces, openings, reveals; trade rows only where every authority exists).

    python3 research/external_engine_lab/r8_17_wall_blind.py <work> <out.json>

The trade / height authority map is DATA in the freeze record (never typed here). No expected value, no historical
plaster / paint / tile quantity is read. Topology is the R8.16 closure-V2 run, untouched.
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
import r8_15_qortuba as R15                                                                   # noqa: E402
import r8_15_skirting_blind as SB                                                             # noqa: E402
import r8_17_blind as B17                                                                     # noqa: E402
from engine.source import owner_facts as OF, owner_method_facts as MF                         # noqa: E402
from engine.source import wall_contact_path as WC, wall_faces as WF                           # noqa: E402

FZ_FILE = ROOT / "tests/r8_17/registers/R8_17_WALL_FACE_FREEZE.json"
handle = R14.handle


def heads(res, inp):
    pfact, b_new, _per, _dom = R14.R12.compare_fact(R14.OF11.load()[0], inp, res)
    owner_passage = R14.OF11.hall_lobby_passage(inp, res, {"fact": pfact.ref, "state": b_new["binding"]})
    mfacts = R14.method_facts()
    binds = [(f, MF.bind(f, inp)) for f in mfacts.values()]
    pbinds = [(f, OF.bind(f, inp)) for f in SB.physical_facts()]
    h, why = R15.heads_for(res, inp, owner_passage, mfacts, binds, pbinds)
    return h, why, pfact


def contact_all(res, inp, smap, wm):
    """Floor contact for EVERY site's glazing: the bound door first, else the sill fact v2 (wall-face scope) for
    hosted glazing, else unproven. `windows` holds GLAZING entities only (an entity that also bounds a site on a
    non-glazing edge is the hosting wall, never a window)."""
    w = next(MF.from_record(x) for x in json.loads(R14.METHOD.read_text())["facts"]
             if (x["fact_id"], x["version"]) == tuple(wm["window_sill_fact"]))
    wb = MF.bind(w, inp)
    edges = [e for s in res["sites"] for e in WC.site_edges(res["_arr"], s)]
    wall_entities = {WC._entity(x) for e in edges if WC.GLAZING_ROLE not in e["roles"] for x in e["sources"]}
    out, windows = dict(smap), {}
    for e in edges:
        if WC.GLAZING_ROLE not in e["roles"] or any(x.startswith("CLOSURE|") for x in e["sources"]):
            continue
        if any(smap.get(x) or smap.get(WC._entity(x)) for x in e["sources"]):
            continue
        walls = set(e["roles"]) - {WC.GLAZING_ROLE}
        if walls and walls <= set(WC.WALL_ROLES) and wb["binding"] == "APPLIES":
            st = WC.opening_contact(sill_m=w.statement["sill_height_m"], sill_authority=w.ref)
            for x in e["sources"]:
                out.setdefault(WC._entity(x), st)
                if WC._entity(x) not in wall_entities:
                    windows.setdefault(WC._entity(x), st)
    return out, windows, wb["binding"]


def run(res, inp, fz):
    wm = fz["qortuba_wall_face_method"]
    eps = R14.Q11.TP.tolerances(R14.Q11.RT.max_abs_coordinate(inp.parts), inp.unit_native_to_mm)["eps_r"]
    u = inp.unit_native_to_mm / 1000
    dry, wet = SB.dry_and_wet_sites(res)
    classes = {sid: "DRY_INTERNAL_ROOM" for sid, _z in dry} | {sid: why.split()[0] for sid, _z, why in wet}
    zones = {sid: z for sid, z in dry} | {sid: z for sid, z, _w in wet}
    _, states = SB.obstacle_states(res, inp)
    bands = {b["band_id"]: b for b in res["wall_bands"]["bands"]}
    sf, sb, smap = B17.slide_contact(inp)
    gj = WC.glazed_door_jambs(res["closures"], {k: v for k, v in smap.items() if k.startswith("GLAZED|")})
    pj = [j for p in res["passages"] for j in WC.passage_jambs(p, bands, eps)]
    dj = WC.door_jambs(res["openings"], res["closures"])
    jambs = pj + dj + gj
    fcm, win_contact, wbind = contact_all(res, inp, smap, wm)
    oh_door = wm["opening_heights"]["DOOR"]
    oh_slide = wm["opening_heights"]["SLIDING_GLAZED_DOOR"]
    oh_win = wm["opening_heights"]["WINDOW"]
    opening_heights = {occ: {"height_m": oh_door["height_m"], "authority": oh_door["authority"]}
                       for occ in res["openings"]}
    if sb["binding"] == "APPLIES":
        for k in smap:
            opening_heights[k] = {"height_m": oh_slide["height_m"], "authority": oh_slide["authority"]}
    for k, st in win_contact.items():
        opening_heights[k] = {"height_m": oh_win["height_m"], "authority": oh_win["authority"],
                              "sill_m": st["sill_m"], "sill_authority": st["authority"]}
    hd, hwhy, pfact = heads(res, inp)
    head_m = {"OPEN_PASSAGE_WITH_HEAD": WF.WITH_HEAD, "OPEN_PASSAGE_FULL_HEIGHT": WF.FULL_HEIGHT}
    sites = {s["site_id"]: s for s in res["sites"]}
    per, trade_rows = {}, {}
    for sid, cls in classes.items():
        rules = WF.trade_assignment(cls, wm["trade_rules"])
        psg = [{"passage_id": p["passage_id"], "width_m": round(p["width_mm"] / 1000, 6),
                "head": head_m.get(hd.get(p["passage_id"]) or "", None),
                "head_height_m": pfact.statement.get("clear_height_m") if hd.get(p["passage_id"]) ==
                "OPEN_PASSAGE_WITH_HEAD" else None,
                "head_authority": hwhy.get(p["passage_id"]) if hd.get(p["passage_id"]) else None}
               for p in res["passages"] if p["strip_in_site"] == sid]
        rec = {"zones": zones[sid], "class": cls, "trades": rules, "passages_in_site": psg, "faces": {}}
        for trade, r in rules.items():
            if r["state"] != "APPLIES":
                continue
            f = WF.site_faces(WC.site_edges(res["_arr"], sites[sid]), u=u, height_m=r.get("height_m"),
                              height_authority=r.get("authority"), jambs=jambs, eps=eps, obstacle_authority=states,
                              floor_contact_by_entity=fcm, opening_heights=opening_heights, passages=psg)
            rec["faces"][trade] = f
            cf = wm.get("counterfactual_heights", {}).get(trade)
            if f["state"] != WF.COMPUTED and cf:
                c = WF.site_faces(WC.site_edges(res["_arr"], sites[sid]), u=u, height_m=cf["height_m"],
                                  height_authority=cf["authority"], jambs=jambs, eps=eps, obstacle_authority=states,
                                  floor_contact_by_entity=fcm, opening_heights=opening_heights, passages=psg)
                rec.setdefault("counterfactual", {})[trade] = {"height": cf, "state": c["state"],
                                                               "areas_m2": c.get("areas_m2"), "blockers": c["blockers"],
                                                               "NOT_PUBLISHED": True}
        per[sid] = rec
    # ---------------------------------------------------------------- reveals (one identity per opening)
    door_sites = {}
    for sid, s in sites.items():
        for e in WC.site_edges(res["_arr"], s):
            for k in WF.opening_keys(e["sources"]):
                if k in res["openings"] or k in smap:
                    door_sites.setdefault(k, set()).add(sid)
    reveals = []
    for occ, st in sorted(res["openings"].items()):
        js = [j for j in dj if j["opening"] == occ]
        if not js:
            continue
        rooms = {classes.get(x, "OUTSIDE_MEASURED_UNIT") for x in door_sites.get(occ, ())}
        rv = WF.opening_reveals(occ, width_m=round(st["width"] * u, 6), depth_m=round(max(j["length"] for j in js) * u, 6),
                                depth_basis="SOURCE (door strip thickness)", height_m=oh_door["height_m"])
        for x in rv:
            x.update(kind="DOOR", rooms=sorted(rooms), height_authority=oh_door["authority"],
                     trade=wm["reveal_trades"]["DRY_ONLY" if rooms == {"DRY_INTERNAL_ROOM"} else "OTHER"])
        reveals += rv
    if gj:
        oid = gj[0]["opening"]
        width = max(math.dist(c.geometry[:2], c.geometry[2:4]) for c in res["closures"]
                    if c.source_id.startswith(f"CLOSURE|{oid}|"))
        rooms = {classes.get(x, "OUTSIDE_MEASURED_UNIT") for k in smap for x in door_sites.get(k, ())}
        rv = WF.opening_reveals(oid, width_m=round(width * u, 6), depth_m=round(max(j["length"] for j in gj) * u, 6),
                                depth_basis="SOURCE (glazed strip thickness)", height_m=oh_slide["height_m"])
        for x in rv:
            x.update(kind="SLIDING_GLAZED_DOOR", rooms=sorted(rooms), height_authority=oh_slide["authority"],
                     trade=wm["reveal_trades"]["OTHER" if rooms - {"DRY_INTERNAL_ROOM"} else "DRY_ONLY"])
        reveals += rv
    for p in res["passages"]:
        sid = p["strip_in_site"]
        if sid not in classes:
            continue
        phys = [j for j in pj if j["opening"] == p["passage_id"] and WC.is_physical_jamb(j)]
        sides = tuple(f"{j['side']}_JAMB" for j in phys)
        head = hd.get(p["passage_id"])
        ht = pfact.statement.get("clear_height_m") if head == "OPEN_PASSAGE_WITH_HEAD" else \
            (wm["trade_rules"][classes[sid]].get("PLASTER", {}).get("height_m") if head == "OPEN_PASSAGE_FULL_HEIGHT"
             else None)
        rv = WF.opening_reveals(p["passage_id"], width_m=round(p["width_mm"] / 1000, 6),
                                depth_m=round(p["thickness_mm"] / 1000, 6), depth_basis="SOURCE (band thickness)",
                                height_m=ht, head=head == "OPEN_PASSAGE_WITH_HEAD", sides=sides)
        for x in rv:
            x.update(kind=head or "PASSAGE_HEAD_NOT_ESTABLISHED", rooms=[classes[sid]],
                     height_authority=hwhy.get(p["passage_id"]), trade=wm["reveal_trades"]["DRY_ONLY"],
                     non_physical_sides=[j["side"] for j in pj if j["opening"] == p["passage_id"] and
                                         not WC.is_physical_jamb(j)])
        reveals += rv
    for k, stc in sorted(win_contact.items()):
        sids = [sid for sid in classes if any(WC._entity(x) == k for e in WC.site_edges(res["_arr"], sites[sid])
                                              for x in e["sources"])]
        width = max((e["length"] for sid in sids for e in WC.site_edges(res["_arr"], sites[sid])
                     if any(WC._entity(x) == k for x in e["sources"])), default=None)
        if width is None:                                     # glazing bounding no measured site: out of scope
            continue
        rv = WF.opening_reveals(k, width_m=None if width is None else round(width * u, 6),
                                depth_m=wm["window_reveal_depth"]["depth_m"],
                                depth_basis=wm["window_reveal_depth"]["basis"], height_m=oh_win["height_m"])
        for x in rv:
            rooms = {classes[s] for s in sids}
            x.update(kind="WINDOW", rooms=sorted(rooms), height_authority=oh_win["authority"],
                     trade=wm["reveal_trades"]["DRY_ONLY" if rooms == {"DRY_INTERNAL_ROOM"} else "OTHER"])
        reveals += rv
    guard = WF.double_count_guard({sid: next(iter(v["faces"].values())) for sid, v in per.items() if v["faces"]},
                                  reveals)
    # ---------------------------------------------------------------- trade rows
    for trade in ("WALL_TILE", "PLASTER", "PAINT"):
        sites_t = {sid: v["faces"][trade] for sid, v in per.items() if trade in v["faces"]}
        blk = sorted({b for f in sites_t.values() for b in f["blockers"]})
        ok = sites_t and all(f["state"] == WF.COMPUTED for f in sites_t.values())
        cols = wm["column_faces"].get(trade) == "INCLUDED"
        obst = wm["obstacle_faces"].get(trade) == "INCLUDED"
        val = None
        if ok:
            val = round(math.fsum(f["areas_m2"]["WALL_FACE_NET"] + (f["areas_m2"]["COLUMN_FACE"] if cols else 0.0) +
                                  (f["areas_m2"]["OBSTACLE_FACE"] if obst else 0.0) for f in sites_t.values()), 6)
        trade_rows[trade] = {"state": "COMPUTED_SHADOW" if ok else "BLOCKED", "value_m2": val,
                             "sites": sorted(sites_t), "blockers": blk,
                             "column_faces": wm["column_faces"].get(trade), "obstacle_faces":
                             wm["obstacle_faces"].get(trade), "reveals": wm["reveal_inclusion"].get(trade)}
    return {"per_site": per, "reveals": reveals, "double_count_guard": guard, "trade_rows": trade_rows,
            "sliding_door": {"fact": sf.ref, "binding": sb["binding"]}, "window_sill_fact_binding": wbind,
            "glazed_door_jambs": len(gj), "physical_passage_jambs": sum(1 for j in pj if WC.is_physical_jamb(j)),
            "non_physical_passage_sides": sum(1 for j in pj if not WC.is_physical_jamb(j))}


def main(work, out):
    fz = json.loads(FZ_FILE.read_text())
    R = R14.R13.runs(work, None)
    new, inp_new = R["new"], R["inputs"]["NEW_K2"]
    rec = {"SCHEMA": "URBAN_R8_17_WALL_FACE_BLIND_RESULT_V1", "freeze": fz["frozen_commit"],
           "wall_face_policy": fz["wall_face_policy"], "method": fz["qortuba_wall_face_method"]["ref"],
           "blind": {"expected_value_given": False, "historical_quantities_used": False},
           "run_input_digest": new["run_manifest"]["RUN_INPUT_DIGEST"], **run(new, inp_new, fz)}
    Path(out).write_text(json.dumps(rec, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({"trade_rows": {k: (v["state"], v["value_m2"], v["blockers"][:3]) for k, v in
                                     rec["trade_rows"].items()}, "guard": rec["double_count_guard"]["state"]}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:3])
