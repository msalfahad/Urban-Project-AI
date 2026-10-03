"""R8.19 lab: Qortuba AFTER the frozen R8.19 blind run - the R8.18 assembly (rows, V4 skirting, waterproofing, the
R8.18 rebuild), the frozen R8.19 run recomputed (must equal the blind record), and the rebuild of the trade rows FROM THE
SAME SURFACE RECORDS with two disclosed wiring corrections of the blind script:

  WF3-L1  the blind script admitted EVERY wall-face V2 surface record as wall plane, but V2 also carries COLUMN_FACE and
          OBSTACLE_FACE records as SEPARATE classes (WALL_FACE_SURFACE_POLICY_V2 "separate_classes") - so every exposed
          column / duct face entered twice (plane copy + exposed object face). The rebuild admits only the V2
          plane classes (WF.PLANE_SURFACES) as wall plane; object faces come only from the exposure policy.
  WF3-L2  the blind surface guard keyed records by id and object faces by (site, class, segment): it missed WF3-L1 (the
          two copies carry different ids) and flagged one object segment exposed as two physical spans. The rebuild
          guard keys every surface by its PHYSICAL identity (site + geometry; reveals by opening / owner / surface).

    python3 research/external_engine_lab/r8_19_qortuba.py <work> <register_dir> [code_commit]
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_18_qortuba as Q18                                                                   # noqa: E402
import r8_19_blind as B19                                                                     # noqa: E402
from engine.source import exposed_finish as EF, wall_contact_path as WC, wall_faces_v2 as WF  # noqa: E402

REG19 = ROOT / "tests/r8_19/registers"
OBJ = (EF.COLUMN_FACE, EF.OBSTACLE_FACE)


def jl(p):
    return json.loads(Path(p).read_text())


def norm(x):
    return json.loads(json.dumps(x, default=str))


def r6(v):
    return None if v is None else round(v, 6)


def physical_key(s, site, geom_of):
    if s["kind"] == "REVEAL":
        return json.dumps(["REVEAL", s["opening"], site, s["class"]])
    if s["kind"] == "OBJECT_FACE":                                        # a full-height face on that plan segment
        return json.dumps(["FACE", site, s["class"], geom_of[(site, s["segment"], s["length_m"])], None, None])
    return json.dumps(["FACE", site, s["class"], s["id"][4], s["id"][5], s["id"][6]])  # vertical band of a segment


def guard(rows, geom_of):
    out = {}
    for row_id, r in rows.items():
        keys = [physical_key(s, s["site"], geom_of) for s in r["surfaces"]]
        out[row_id] = sorted({k for k in keys if keys.count(k) > 1})
    return {"duplicates_by_row": out, "state": "PASS" if not any(out.values()) else "FAIL",
            "key": "site + vertical class + plan geometry + opening / side (wall plane and object faces); opening + "
                   "owner + surface (reveals)"}


def correct(blind):
    """The rebuild: the blind surface records with WF3-L1 applied, every room and row total re-summed from them."""
    geom_of = {(f["site"], f["segment"], f["length_m"]): str(f["geom"])
               for x in blind["object_exposure"].values() if isinstance(x, dict) and "faces" in x for f in x["faces"]}
    rows, removed = {}, {}
    for row_id, r in blind["trade_rows"].items():
        keep = [s for s in r["surfaces"] if s["kind"] != "WALL_PLANE" or s["class"] in WF.PLANE_SURFACES]
        removed[row_id] = [s for s in r["surfaces"] if s["kind"] == "WALL_PLANE" and s["class"] not in WF.PLANE_SURFACES]
        rooms = {}
        for sid, room in r["rooms"].items():
            srf = [s for s in keep if s["site"] == sid]
            rooms[sid] = dict(room, wall_plane_m2=r6(math.fsum(s["area_m2"] for s in srf if s["kind"] == "WALL_PLANE")),
                              column_face_m2=r6(math.fsum(s["area_m2"] for s in srf if s["class"] == EF.COLUMN_FACE)),
                              obstacle_face_m2=r6(math.fsum(s["area_m2"] for s in srf
                                                            if s["class"] == EF.OBSTACLE_FACE)),
                              total_m2=r6(math.fsum(s["area_m2"] for s in srf)), surfaces=len(srf))
        sub = r6(math.fsum(x["total_m2"] for x in rooms.values())) if r["AUTHORISED_SUBTOTAL_M2"] is not None else None
        rows[row_id] = dict(r, rooms=rooms, surfaces=keep, AUTHORISED_SUBTOTAL_M2=sub,
                            COMPLETE_M2=sub if r["state"] == "COMPUTED_SHADOW_COMPLETE" else None)
    pl = {json.dumps(s["id"]) for s in rows["DRY_WALL_PLASTER"]["surfaces"]}
    pa = {json.dumps(s["id"]) for s in rows["DRY_WALL_PAINT"]["surfaces"]}
    out = dict(blind, trade_rows=rows,
               PLASTER_ALL_SURFACES_M2=r6(math.fsum(s["area_m2"] for r in rows.values() if r["trade"] == "PLASTER"
                                                    for s in r["surfaces"])),
               paint_vs_plaster={"same_surface_set": pl == pa, "only_plaster": sorted(pl - pa),
                                 "only_paint": sorted(pa - pl), "surfaces": len(pl)},
               surface_guard=guard(rows, geom_of))
    return out, removed, guard(blind["trade_rows"], geom_of)


def plane_check(rb, r18):
    """Each room's rebuilt wall plane = the R8.18 V2 METHOD B net of the same site and trade."""
    out = {}
    for row_id, r in rb["trade_rows"].items():
        if row_id == "WET_SERVICE_REVEAL_PLASTER":
            continue
        for sid, room in r["rooms"].items():
            f = r18["per_site"][sid]["faces"][r["trade"]]
            out[f"{row_id}|{sid}"] = {"rebuilt_plane_m2": room["wall_plane_m2"],
                                      "r8_18_method_b_m2": f["areas_m2"]["WALL_PLANE_NET_METHOD_B"],
                                      "agree": abs(room["wall_plane_m2"] - f["areas_m2"]["WALL_PLANE_NET_METHOD_B"])
                                      <= f["reconciliation"]["tolerance_m2"]}
    return out


def skirting_check(rb, sk):
    """No duplicate skirting: the exposed dry column / duct faces ARE the V4 skirting faces (same lengths per room)."""
    out = {}
    faces = {cls: rb["object_exposure"][cls]["faces"] for cls in OBJ}
    for sid, v in sk["per_site"].items():
        c = v.get("components_lm") or {}
        col = r6(math.fsum(f["length_m"] for f in faces[EF.COLUMN_FACE] if f["site"] == sid))
        duct = r6(math.fsum(f["length_m"] for f in faces[EF.OBSTACLE_FACE] if f["site"] == sid))
        out[sid] = {"zones": v["zones"], "state": v["state"], "v4_column_lm": c.get(WC.COLUMN_FACE, 0.0),
                    "exposed_column_m": col, "v4_duct_lm": c.get(WC.AUTHORISED_OBSTACLE_FACE, 0.0),
                    "exposed_duct_m": duct, "skirting_payable_lm": v["payable_lm"]}
        out[sid]["same_faces"] = v["state"] == WC.NO_SKIRTING or (
            abs(out[sid]["v4_column_lm"] - col) < 1e-6 and abs(out[sid]["v4_duct_lm"] - duct) < 1e-6)
    return out


def build(work, commit=None):
    ctx = Q18.build(work, commit)
    new, inp = ctx["new"], ctx["inp_new"]
    fz = jl(REG19 / "R8_19_FREEZE.json")
    blind = jl(REG19 / "R8_19_BLIND_RESULT.json")
    again = norm(B19.run(new, inp, fz))
    keys = ("trade_rows", "reveals", "object_exposure", "waterproofing", "heights", "sliding_door_physicality",
            "paint_vs_plaster", "surface_guard")
    ctx["reproduces_r8_19_blind"] = {k: again[k] == blind[k] for k in keys}
    rb, removed, blind_guard_physical = correct(again)
    ctx["r8_19"], ctx["r8_19_blind"], ctx["r8_19_freeze"] = rb, blind, fz
    ctx["blind_vs_rebuild_19"] = {
        "WF3-L1": {"cause": "the blind script admitted every V2 surface record as wall plane; V2 carries COLUMN_FACE / "
                            "OBSTACLE_FACE records as separate classes, so each exposed object face was counted twice",
                   "removed_plane_copies": {k: {"count": len(v), "area_m2": r6(math.fsum(s["area_m2"] for s in v))}
                                            for k, v in removed.items()},
                   "blind_physical_guard": blind_guard_physical},
        "WF3-L2": {"cause": "the blind surface guard keyed records by id (missed WF3-L1) and object faces by "
                            "(site, class, segment) (flagged one segment exposed as two physical spans)",
                   "blind_guard": blind["surface_guard"], "rebuild_guard": rb["surface_guard"]},
        "trade_rows": {k: {"blind": blind["trade_rows"][k]["AUTHORISED_SUBTOTAL_M2"],
                           "rebuild": rb["trade_rows"][k]["AUTHORISED_SUBTOTAL_M2"],
                           "delta": r6(rb["trade_rows"][k]["AUTHORISED_SUBTOTAL_M2"] -
                                       blind["trade_rows"][k]["AUTHORISED_SUBTOTAL_M2"])} for k in rb["trade_rows"]},
        "unchanged": ["reveals and their physicality", "object exposure", "assignments", "row states",
                      "waterproofing", "heights"],
        "engine": "identical frozen policies in both"}
    ctx["plane_check_19"] = plane_check(rb, ctx["r8_18"])
    ctx["skirting_check_19"] = skirting_check(rb, ctx["skirting_v4"])
    return ctx


def main(work, regdir, commit=None):
    import r8_19_registers as REGS
    regs, ctx = REGS.registers(build(work, commit))
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({t: (v["state"], v["AUTHORISED_SUBTOTAL_M2"], v["COMPLETE_M2"])
                      for t, v in ctx["r8_19"]["trade_rows"].items()}, indent=1))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
