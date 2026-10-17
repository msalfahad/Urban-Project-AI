"""ENGINE ADAPTER - Phase 2B-5: runs the ARCH_TAKEOFF_V2.6 waterproofing (waterproofing_system.build_area(v26=True))
on the worked examples and reads back

    figures(area)          the engine's own figures, keyed like the cases' expected values
    plan(area[, trace])    the engine's cutting plan written as a plan of the independent reference calculator
                           (construct_reference format, millimetres), so that the reference rebuilds it piece by piece
    shared(areas)          the procurement cutting plans of several areas (one inventory per membrane system)

This is the only file of the Phase 2B-5 library that imports the engine; it holds no expected value. The rooms are
the cases' synthetic source drawings, fed through the Phase 2B-2 feature builder exactly as the Phase 2B-3 proof
library does.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "tests" / "m9_p2b2")]

import p2b2_fixtures as F                                     # noqa: E402
from engine.source import knowledge as K                      # noqa: E402
from engine.source import plane_poly as PP                    # noqa: E402
from engine.source import waterproofing_system as WS          # noqa: E402
from engine.source import wp_geometry as WG                   # noqa: E402
from engine.source import wp_install as WI                    # noqa: E402

U = 1e-3


class NotSupported(Exception):
    pass


def area(room, room_id="IX", floor="GF"):
    """the V2.6 area of a case room (millimetres)."""
    ring = [(x * U, y * U) for x, y in room["poly"]]
    holes = [[(x * U, y * U) for x, y in h] for h in room.get("holes", ())]
    gaps = [(d["edge"], d["t0"] * U, d["t1"] * U, "DOOR", d["id"]) for d in room.get("doors", ())] + \
        [(b["edge"], b["t0"] * U, b["t1"] * U, "PASSAGE" if b["kind"] == "PASSAGE" else "OTHER", b["id"])
         for b in room.get("breaks", ())]
    feats = F.walls(ring, gaps)
    for h in holes:
        feats += F.walls(h)
    doors = room.get("doors", ())
    pieces = [{"opening_id": d["id"], "width_m": (d["t1"] - d["t0"]) * U, "depth_m": d["depth"] * U} for d in doors]
    doorways = [dict(p, other_side=d["other_side"]) for p, d in zip(pieces, doors)]
    drain = "ROOF DRAIN" if "ROOF" in room["codes"] else "FLOOR DRAIN"
    ents = {"inserts": [{"id": d["id"], "name": drain, "x": d["x"], "y": d["y"]} for d in room.get("drains", ())],
            "texts": [{"id": p["id"], "value": "PIPE SLEEVE", "x": p["x"], "y": p["y"]} for p in room.get("pipes", ())]}
    rm = {"room_id": room_id, "floor": floor, "name_en": room_id, "codes": list(room["codes"]), "polygon_m": ring,
          "hole_polygons_m": holes, "polygon": list(room["poly"]), "hole_polygons": [list(h) for h in
                                                                                     room.get("holes", ())]}
    net = abs(WG.signed_area(ring)) - sum(abs(WG.signed_area(h)) for h in holes)
    with K.using("1.1.0"):
        a = WS.make_area(rm, feats, scope=room["scope"], net_m2=net, continuation_pieces=pieces, doorways=doorways,
                         ents=ents, unit_m=U, keep_segments=True)
        return WS.build_area(a, F.resolver(), v26=True)


def _mm(x):
    return int(round(x * 1000))


def _r(x, n=6):
    return None if x is None else round(x, n)


def plan(a, trace=None):
    """the engine's cutting plan (or the plan of one of its junction alternatives, given its trace) as a reference
    plan."""
    v = a["v26"]
    if trace is None:
        pp, runs = v["piece_plan"], [[p["id"] for p in rn["pieces"]] for rn in v["installation"]["runs"]]
        tr = a["layout"]["layout"]["trace"]
    else:
        spec = {"min_end_lap_m": a["layout"]["layout"]["seams"]["upturn_end_laps"]["lap_m"]}
        pp = WI.piece_plan(trace, a, spec, None)
        topo = WS._v25_band_topology(a, a["transitions"]) is not None
        paths, why = WI.run_paths(a, a["layout"]["layout"]["band_runs"], a["transitions"], topo)
        if paths is None:
            raise NotSupported(why)
        runs = [[pid for pid, *_ in row] for row in WI.place_band(paths, trace["band_pieces"],
                                                                     spec["min_end_lap_m"])]
        tr = trace
    tree = {n["id"]: n for n in pp["tree"]}
    kids = {}
    for n in pp["tree"]:
        if n["from"] is not None:
            kids.setdefault(n["from"], []).append(n["id"])
    rolls, rip, cross = [], {}, {}
    for r in pp["rolls"]:
        row = []
        for c in r["cuts"]:
            if c["cut"] == "WHOLE":
                row.append((c["parts"][0]["id"], _mm(c["length_m"])))
            else:
                row.append((c["id"], _mm(c["length_m"])))
                rip[c["id"]] = [(p["id"], _mm(p["w_m"])) for p in c["parts"] if not p["id"].endswith("~w")]
        rolls.append(row)
    for nid, n in tree.items():
        if n["kind"] == "LANE" and nid in kids:
            cross[nid] = [(k, _mm(tree[k]["l_m"])) for k in kids[nid] if not k.endswith("~l")]
        elif n["kind"] == "CROSS_CUT":
            rip[nid] = [(k, _mm(tree[k]["w_m"])) for k in kids[nid] if not k.endswith("~t")]
    strips = {}
    for p in pp["pieces"]:
        if p["kind"] == "FLOOR":
            m = re.fullmatch(r"S(\d+)(\.\d+)?", p["id"])
            if m is None:
                raise NotSupported(f"floor piece {p['id']}: a strip with several runs of the room")
            strips.setdefault(int(m.group(1)), []).append(p["id"])
    floor = [ids[0] if len(ids) == 1 else sorted(ids, key=lambda x: int(x.split(".")[1]))
             for _, ids in sorted(strips.items())]
    doorways = {p["id"][3:]: p["id"] for p in pp["pieces"] if p["kind"] == "DOORWAY"}
    direction = a["layout"]["layout"]["direction"] if trace is None else \
        next(s["place"]["direction"] for s in tr["segments"] if s.get("place"))
    return {"method": "A", "along": "X" if direction == "ALONG_X" else "Y", "j": _mm(tr["junction_flange_m"]),
            "rolls": rolls, "rip": rip, "cross": cross, "floor": floor, "runs": runs, "doorways": doorways}


def _end_lap_area(a):
    """the end-lap (splice) zones of the floor inside the room (the engine's own zones)."""
    inst = a["v26"]["installation"]
    fl = WI.floor_pieces(a["layout"]["layout"]["trace"])
    if not fl:
        return 0.0
    to = WI._frame(fl[0]["theta"], fl[0]["direction"])
    P = [to(q) for q in a["polygon_m"]]
    H = [[to(q) for q in h] for h in a["hole_polygons_m"]]
    return sum(PP.region_area_in_rect(P, H, tuple(z["rect_frame_m"])) for z in inst["floor_seams"]
               if z["kind"] == "END")


def figures(a):
    """the engine's figures for one area, keyed like the cases' expected values."""
    row, lay, v = a["row"], a["layout"], a["v26"]
    L, inst, pp, jun = lay["layout"], v["installation"], v["piece_plan"], v["junction"]
    comp = {c["component"]: c for c in lay["components"]}
    s = L["seams"]
    runs = inst.get("runs") or []
    mlp = inst.get("multi_layer_points") or {}
    end_a = _end_lap_area(a)
    out = {"direction": "X" if L["direction"] == "ALONG_X" else "Y",
           "proven_subtotal_m2": a["v25"]["proven_subtotal"]["total_m2"], "consumed_m2": row["consumed_m2"],
           "installed_m2": row["B_installed_m2"],
           "laps_total_m2": _r(row["B_installed_m2"] - a["v25"]["proven_subtotal"]["total_m2"]),
           "laps_side_m2": _r(comp["floor"]["overlap_m2"] - end_a), "laps_floor_end_m2": _r(end_a),
           "laps_junction_m2": _r(s["upturn_to_floor_lap"]["lap_m"] * s["upturn_to_floor_lap"]["running_lm"]),
           "laps_band_end_m2": _r(s["upturn_end_laps"]["running_lm"] * s["upturn_end_laps"]["lap_m"]),
           "laps_doorway_m2": comp["doorway"]["overlap_m2"], "true_waste_m2": pp["balance"]["true_waste_m2"],
           "reusable_m2": pp["balance"]["reusable_m2"], "stock_m2": pp["balance"]["roll_stock_m2"],
           "rolls": row["rolls_if_installed_alone"], "floor_seams": s["longitudinal"]["count"],
           "floor_end_laps": s["transverse_floor"]["count"], "band_joints": inst.get("band_joints"),
           "seams": s["longitudinal"]["count"] + s["transverse_floor"]["count"] + s["upturn_end_laps"]["count"],
           "band_pieces_m": sorted(L["band_pieces_m"]), "min_joint_corner_m": row.get("min_joint_corner_m"),
           "min_joint_seam_end_m": row.get("min_joint_seam_end_m"),
           "run_min_joint_corner_m": [r["min_joint_corner_m"] for r in runs],
           "run_min_joint_seam_end_m": [r["min_joint_seam_end_m"] for r in runs],
           "joints_stacked_on_seam_ends": sum(r["joints_stacked_on_seam_ends"] for r in runs),
           "jamb_butt_joints": sum(1 for r in runs for e in r["ends"] if e["state"] == "BUTT_JOINT_OPEN"),
           "terminations": sum(1 for r in runs for e in r["ends"] if e["state"] == "TERMINATION_OPEN"),
           "corners_internal": inst["corners"]["internal"], "corners_external": inst["corners"]["external"],
           "flange_pleats_m2": inst["corners"]["flange_pleats_m2"], "flange_gaps_m2": inst["corners"]["flange_gaps_m2"],
           "t_flange_over_seam_end": mlp.get("flange_over_seam_end"),
           "t_doorway_lap_over_seam_end": mlp.get("doorway_lap_over_seam_end"),
           "t_seam_end_at_break": mlp.get("seam_end_at_termination"),
           "seams_along_walls": mlp.get("seams_along_walls"),
           "best_corner_m": row.get("best_order_min_corner_m"), "best_seam_end_m": row.get("best_order_min_seam_end_m"),
           "min_end_lap_stagger_m": min((x["stagger_m"] for x in inst.get("end_lap_stagger") or ()), default=None),
           "lay_order": inst["lay_order"]["order"] if inst["lay_order"]["state"] == "FROM_THE_DRAIN" else None,
           "shortest_band_piece_m": min(L["band_pieces_m"]) if L["band_pieces_m"] else None,
           "flags": v["flags"]}
    on_seam = set(inst["lay_order"].get("drain_on_seam") or ())
    for it in inst["penetrations"]["items"]:
        what = "drain" if it["kind"] in WI.DRAIN_KINDS else "pipe"
        out[f"{what}_{it['ref']}_clear_m"] = it["clear_m"]
        if what == "drain":
            out[f"drain_{it['ref']}_on_seam"] = it["ref"] in on_seam
    fold = jun["continuous_fold"]
    out["fold"] = "BLOCKED" if fold["state"] != "COMPUTED" else {
        "rolls": fold["rolls"], "consumed_m2": fold["consumed_m2"], "installed_m2": fold["installed_m2"],
        "laps_m2": fold["laps_m2"], "corner_excess_m2": fold["corner_excess_m2"], "seams": fold["seams"]}
    out["junction_rolls"] = jun["rolls_range"]
    more = [x for x in jun["alternatives"] if x["method"] == "SEPARATE_UPSTAND" and x["rolls"] > jun["alternatives"][0]
            ["rolls"]]
    out["junction_roll_change_flange_m"] = more[0]["flange_m"] if more else None
    return out


def shared(areas):
    """the procurement cutting plans (V2.6: exact packing, cut ids) of several areas."""
    return WS.cutting_plan(areas, exact=True, cut_ids=True)
