"""R8.17 lab: Qortuba AFTER the frozen R8.17 blind runs - the R8.16 assembly (closure-V2 topology, six rows, marble,
V3 skirting for the regression), the V4 skirting row (recomputed: must equal the blind record), the hidden profile on
the same path, the V3-O1 audit, the sliding glass door, and the wall-face rebuild with the frozen engine and the two
DISCLOSED wiring corrections of the blind script (WF-L1 passage-head constants, WF-L2 door rooms).

    python3 research/external_engine_lab/r8_17_qortuba.py <work> <register_dir> [code_commit]
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_16_qortuba as R16                                                                   # noqa: E402
import r8_17_blind as B17                                                                     # noqa: E402
import r8_17_wall_blind as W17                                                                # noqa: E402
from engine.source import opening_reveals as OR, wall_contact_path as WC, wall_faces as WF     # noqa: E402

REG17 = ROOT / "tests/r8_17/registers"
R15 = R16.R15
SB = W17.SB
R14 = W17.R14
HEAD_MAP = {OR.WITH_HEAD: WF.WITH_HEAD, OR.FULL_HEIGHT: WF.FULL_HEIGHT}        # WF-L1: the opening_reveals constants
DRY_DOOR = "DRY_DRY_CONTINUOUS_PORCELAIN"


def jl(p):
    return json.loads(Path(p).read_text())


def wall_faces(res, inp, fz, thresholds):
    """The frozen WALL_FACE_SURFACE_POLICY_V1 on Qortuba, wired correctly: passage heads mapped from the
    opening_reveals constants (WF-L1) and each door's rooms read from its own threshold classification, never from
    its strip site (WF-L2). Everything else is the blind script's code path."""
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
    fcm, win_contact, _wb = W17.contact_all(res, inp, smap, wm)
    oh = wm["opening_heights"]
    heights = {occ: {"height_m": oh["DOOR"]["height_m"], "authority": oh["DOOR"]["authority"]} for occ in res["openings"]}
    if sb["binding"] == "APPLIES":
        heights |= {k: {"height_m": oh["SLIDING_GLAZED_DOOR"]["height_m"],
                        "authority": oh["SLIDING_GLAZED_DOOR"]["authority"]} for k in smap}
    for k, st in win_contact.items():
        heights[k] = {"height_m": oh["WINDOW"]["height_m"], "authority": oh["WINDOW"]["authority"],
                      "sill_m": st["sill_m"], "sill_authority": st["authority"]}
    hd, hwhy, pfact = W17.heads(res, inp)
    sites = {s["site_id"]: s for s in res["sites"]}
    per = {}
    for sid, cls in classes.items():
        rules = WF.trade_assignment(cls, wm["trade_rules"])
        psg = [{"passage_id": p["passage_id"], "width_m": round(p["width_mm"] / 1000, 6),
                "head": HEAD_MAP.get(hd.get(p["passage_id"])),
                "head_height_m": pfact.statement.get("clear_height_m") if hd.get(p["passage_id"]) == OR.WITH_HEAD
                else None, "head_authority": hwhy.get(p["passage_id"]) if hd.get(p["passage_id"]) else None}
               for p in res["passages"] if p["strip_in_site"] == sid]
        rec = {"zones": zones[sid], "class": cls, "trades": rules, "passages_in_site": psg, "faces": {}}
        for trade, r in rules.items():
            if r["state"] != "APPLIES":
                continue
            kw = dict(u=u, jambs=jambs, eps=eps, obstacle_authority=states, floor_contact_by_entity=fcm,
                      opening_heights=heights, passages=psg)
            f = WF.site_faces(WC.site_edges(res["_arr"], sites[sid]), height_m=r.get("height_m"),
                              height_authority=r.get("authority"), **kw)
            rec["faces"][trade] = f
            cf = wm.get("counterfactual_heights", {}).get(trade)
            if f["state"] != WF.COMPUTED and cf:
                c = WF.site_faces(WC.site_edges(res["_arr"], sites[sid]), height_m=cf["height_m"],
                                  height_authority=cf["authority"], **kw)
                rec.setdefault("counterfactual", {})[trade] = {"height": cf, "state": c["state"],
                                                               "areas_m2": c.get("areas_m2"),
                                                               "blockers": c["blockers"], "NOT_PUBLISHED": True}
        per[sid] = rec
    by_door = {t["door_occurrence"]: t for t in thresholds}
    reveals = []
    for occ, st in sorted(res["openings"].items()):
        js = [j for j in dj if j["opening"] == occ]
        if not js:
            continue
        t = by_door.get(occ, {})
        kind = "DRY_ONLY" if t.get("classification") == DRY_DOOR else "OTHER"
        for x in WF.opening_reveals(occ, width_m=round(st["width"] * u, 6),
                                    depth_m=round(max(j["length"] for j in js) * u, 6),
                                    depth_basis="SOURCE (door strip thickness)", height_m=oh["DOOR"]["height_m"]):
            reveals.append(dict(x, kind="DOOR", threshold_class=t.get("classification"),
                                height_authority=oh["DOOR"]["authority"], trade=wm["reveal_trades"][kind]))
    if gj:
        oid = gj[0]["opening"]
        width = max(math.dist(c.geometry[:2], c.geometry[2:4]) for c in res["closures"]
                    if c.source_id.startswith(f"CLOSURE|{oid}|"))
        for x in WF.opening_reveals(oid, width_m=round(width * u, 6), depth_m=round(max(j["length"] for j in gj) * u,
                                                                                     6),
                                    depth_basis="SOURCE (glazed strip thickness)",
                                    height_m=oh["SLIDING_GLAZED_DOOR"]["height_m"]):
            reveals.append(dict(x, kind="SLIDING_GLAZED_DOOR", rooms=["DRY_INTERNAL_ROOM", "SERVICE_ROOM"],
                                height_authority=oh["SLIDING_GLAZED_DOOR"]["authority"],
                                trade=wm["reveal_trades"]["OTHER"]))
    for p in res["passages"]:
        sid = p["strip_in_site"]
        if sid not in classes:
            continue
        phys = [j for j in pj if j["opening"] == p["passage_id"] and WC.is_physical_jamb(j)]
        head = hd.get(p["passage_id"])
        ht = pfact.statement.get("clear_height_m") if head == OR.WITH_HEAD else \
            (wm["trade_rules"][classes[sid]].get("PLASTER", {}).get("height_m") if head == OR.FULL_HEIGHT else None)
        for x in WF.opening_reveals(p["passage_id"], width_m=round(p["width_mm"] / 1000, 6),
                                    depth_m=round(p["thickness_mm"] / 1000, 6), depth_basis="SOURCE (band thickness)",
                                    height_m=ht, head=head == OR.WITH_HEAD,
                                    sides=tuple(f"{j['side']}_JAMB" for j in phys)):
            reveals.append(dict(x, kind=HEAD_MAP.get(head, "PASSAGE_HEAD_NOT_ESTABLISHED"), rooms=[classes[sid]],
                                height_authority=hwhy.get(p["passage_id"]), trade=wm["reveal_trades"]["DRY_ONLY"],
                                non_physical_sides=[j["side"] for j in pj if j["opening"] == p["passage_id"] and
                                                    not WC.is_physical_jamb(j)]))
    for k in sorted(win_contact):
        sids = [sid for sid in classes if any(WC._entity(x) == k for e in WC.site_edges(res["_arr"], sites[sid])
                                              for x in e["sources"])]
        width = max((e["length"] for sid in sids for e in WC.site_edges(res["_arr"], sites[sid])
                     if any(WC._entity(x) == k for x in e["sources"])), default=None)
        if width is None:
            continue
        rooms = {classes[s] for s in sids}
        for x in WF.opening_reveals(k, width_m=round(width * u, 6), depth_m=wm["window_reveal_depth"]["depth_m"],
                                    depth_basis=wm["window_reveal_depth"]["basis"], height_m=oh["WINDOW"]["height_m"]):
            reveals.append(dict(x, kind="WINDOW", rooms=sorted(rooms), height_authority=oh["WINDOW"]["authority"],
                                trade=wm["reveal_trades"]["DRY_ONLY" if rooms == {"DRY_INTERNAL_ROOM"} else "OTHER"]))
    guard = WF.double_count_guard({sid: next(iter(v["faces"].values())) for sid, v in per.items() if v["faces"]},
                                  reveals)
    return {"per_site": per, "reveals": reveals, "double_count_guard": guard, "classes": classes,
            "glazed_door_jambs": len(gj), "physical_passage_jambs": sum(1 for j in pj if WC.is_physical_jamb(j)),
            "non_physical_passage_sides": sum(1 for j in pj if not WC.is_physical_jamb(j))}


def wf_o1(per):
    """WF-O1 (frozen engine, found by its own fail-closed check): the second form of the two-way area check leaves out
    the wall plane across WINDOW spans; any site with a window fails AREA_RECONCILIATION_FAILED. The primary US-06 form
    (gross plane - full opening areas + head faces) is checked here independently from the recorded lengths."""
    out = []
    for sid, v in per.items():
        for trade, f in v["faces"].items():
            a = f.get("areas_m2")
            if not a or "AREA_RECONCILIATION_FAILED" not in f["blockers"]:
                continue
            H = f["height_m"]
            L = f["lengths_m"]
            win = [o for o in f["openings"] if o["kind"] == WF.WINDOW]
            corrected_b = L.get(WF.WALL_FACE, 0.0) * H + sum(o["width_m"] * H - o["deduction_m2"] for o in win) + \
                a["lintels"] + a["passage_head_faces"]
            out.append({"site": sid, "zones": v["zones"], "trade": trade, "net_primary_m2": a["WALL_FACE_NET"],
                        "net_second_form_corrected_m2": round(corrected_b, 6),
                        "agree_when_the_window_plane_is_included": abs(corrected_b - a["WALL_FACE_NET"]) < 1e-6,
                        "windows": [o["opening"] for o in win]})
    return out


def build(work, commit=None):
    ctx = R16.build(work, commit)
    new, inp = ctx["new"], ctx["inp_new"]
    fz4 = jl(REG17 / "R8_17_V4_FREEZE.json")
    fzw = jl(REG17 / "R8_17_WALL_FACE_FREEZE.json")
    sblind = jl(REG17 / "SKIRTING_V4_BLIND_RESULT.json")
    wblind = jl(REG17 / "WALL_FACE_BLIND_RESULT.json")
    srec = json.loads(json.dumps(B17.skirting_record(new, inp, fz4), default=str))
    ctx["skirting_v4"] = srec
    ctx["reproduces_v4_blind"] = {"payable": srec["PAYABLE_LM"] == sblind["PAYABLE_LM"],
                                  "per_site": srec["per_site"] == sblind["per_site"],
                                  "topology_digest": new["run_manifest"]["RUN_INPUT_DIGEST"] ==
                                  sblind["run_input_digest"]}
    wf = wall_faces(new, inp, fzw, ctx["thresholds_new"])
    ctx["wall_faces"] = wf
    ctx["wf_o1"] = wf_o1(wf["per_site"])
    diffs = []
    for sid, v in wf["per_site"].items():
        b = wblind["per_site"][sid]
        for t, f in v["faces"].items():
            fb = b["faces"][t]
            if (f["state"], f.get("areas_m2"), f["blockers"]) != (fb["state"], fb.get("areas_m2"), fb["blockers"]):
                diffs.append({"site": sid, "trade": t, "blind": {"state": fb["state"], "blockers": fb["blockers"]},
                              "rebuild": {"state": f["state"], "blockers": f["blockers"]}})
    rb = {(x["opening"], x["surface"]): x for x in wblind["reveals"]}
    rdiff = [{"opening": x["opening"], "surface": x["surface"], "blind": {k: rb.get((x["opening"], x["surface"]), {}).get(k)
                                                                          for k in ("area_m2", "trade")},
              "rebuild": {k: x.get(k) for k in ("area_m2", "trade")}}
             for x in wf["reveals"] if {k: rb.get((x["opening"], x["surface"]), {}).get(k) for k in ("area_m2", "trade")}
             != {k: x.get(k) for k in ("area_m2", "trade")}]
    ctx["wall_face_blind_vs_rebuild"] = {"site_differences": diffs, "reveal_differences": rdiff,
                                         "causes": ["WF-L1: the blind script mapped passage heads from the strings "
                                                    "'OPEN_PASSAGE_WITH_HEAD' / 'OPEN_PASSAGE_FULL_HEIGHT' instead of the "
                                                    "opening_reveals constants - both passages read as "
                                                    "PASSAGE_HEAD_NOT_ESTABLISHED",
                                                    "WF-L2: the blind script counted a door's own (unlabelled) strip "
                                                    "site as a room outside the unit - every door reveal read as "
                                                    "NOT_ESTABLISHED; the rebuild reads each door's rooms from its "
                                                    "threshold classification"],
                                         "engine": "identical frozen WALL_FACE_SURFACE_POLICY_V1 in both"}
    ctx["r8_17_v4_freeze"], ctx["r8_17_wall_freeze"] = fz4, fzw
    ctx["skirting_v4_blind"], ctx["wall_face_blind"] = sblind, wblind
    blk = ["SOURCE_ANCHOR: DXF anchored, DWG identity NOT_ESTABLISHED"]
    if srec["withheld"]:
        blk.append(f"WITHHELD_SPAN: {srec['withheld_lm']} lm")
    blk.append("SHADOW_ONLY: no baseline approval, no migration transaction, no release gate passed")
    ctx["skirting_v4_blockers"] = blk
    return ctx


def main(work, regdir, commit=None):
    import r8_17_registers as REGS
    regs, ctx = REGS.registers(build(work, commit))
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: (v["state"], v["value"]) for k, v in ctx["rows_new"].items()} |
                     {"SKIRTING": ctx["skirting_v4"]["PAYABLE_LM"]}, indent=1))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
