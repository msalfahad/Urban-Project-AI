"""T-081 rework, read-only development-villa run: room levels V2 (owner Q-43) and the owner wall height (UP-HGT-001
1.8.0, owner Q-43 / Q-48) on the ARCH_TAKEOFF_V2.9 rooms of the architectural DXF, per room and per floor, against
the freelancer's plaster / paint totals. Diagnostic: nothing is wired, no released quantity moves. The output holds
engine room ids, kinds, levels, heights, lengths and areas only (no client data).

    python3 -I research/agents_t081/alsenan_t081_run.py <P7757.dxf> --out <scratch>/t081_alsenan.json

Inputs that are not in the DXF are given here with their source, never typed as drawing values:
  * the floor-to-floor of the top floor: owner Q-43 answer ("the final floor is +13.9, so 9.7 to 13.9 = 4.2 m"),
    as a PROJECT_FACT with authority and source;
  * the beams over each room: NOT read in this run (the structural slab plans are the hand table T-088), so every
    owner height is HELD BEAM_OVER_ROOM_NOT_CHECKED and shown as the diagnostic `owner_rule_height_m`.
Wall m2 (diagnostic) = the room's wall + column + door + window runs of V2.9 (open passages and glazing edges are not
wall) x the diagnostic height; door and window areas are NOT deducted (their heights are not established)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FREELANCER = {"PLASTER_INTERNAL_m2": 1151.14, "PAINT_INTERNAL_m2": 1191.13}     # scoreboard reference (T-001b)
TOP_FLOOR_FACT = {"value_m": 4.20, "state": "PROJECT_FACT",
                  "authority": "owner Q-43 answer 2026-10-19 21:40 (docs/agents/OWNER_QUESTIONS.md)",
                  "source": "architectural section sheet 10: +9.70 to +13.90 ('the final floor is +13.9')"}
WALL_RUNS = ("wall", "column", "door", "window_threshold")


def _blocks(sym):
    out = set()
    for tok in re.split(r"[|@]", sym or ""):
        parts = tok.split(":")
        if len(parts) >= 2:
            out.add(":".join(parts[:2]))
    return sorted(out)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from engine.source import finish_height as FH1
    from engine.source import finish_height_v2 as FH
    from engine.source import room_levels as RL
    from engine.source import section_binding as SB
    from tools import urban_boq_m9 as M
    _, au, x = M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.9")
    u = x["unit_m"]
    texts, segs = x["texts"], x["segments"]
    rule = FH.owner_wall_rule()
    out = {"method": "ARCH_TAKEOFF_V2.9 rooms + ROOM_LEVELS_V2 + finish heights V2 (owner rule UP-HGT-001 1.8.0)",
           "owner_rule": {k: rule[k] for k in ("rule_ref", "beam_m", "decor_ceiling_m", "floor_finishing_m")},
           "floors": {}, "rooms": [], "doorways": []}
    plan_floors, reps = [], {}
    for reg in au["regions"]:
        fl = reg["floor"]
        rooms = [{"room_id": r["room_id"], "kind": r["kind"], "polygon": r["polygon"],
                  "holes": r.get("hole_polygons") or [], "codes": r["codes"]}
                 for r in au["rooms"] if r["floor"] == fl]
        skip = tuple(k for k, v in reg["layer_roles"].items() if v in ("DOOR", "WINDOW"))
        links = []
        for o in au["openings"]:
            if o["floor"] != fl or o["kind"] == "WINDOW" or len(o["rooms"]) < 2:
                continue
            rd = RL.doorway_reading({"centre_m": o["position"]["centre_m"], "axis": o["position"]["wall_axis"],
                                     "width_m": o["width_m"], "wall_t_m": o["wall_t_m"],
                                     "symbol_blocks": _blocks(o.get("door_symbol"))}, segs, u, skip_layers=skip)
            links.append({"opening_id": o["opening_id"], "rooms": o["rooms"], "doorway": rd["state"]})
            out["doorways"].append({"floor": fl, "opening_id": o["opening_id"], "kind": o["kind"],
                                    "rooms": o["rooms"], "doorway": rd["state"], "lines": len(rd["lines"])})
        rep = RL.room_levels_v2(texts, rooms, floor=fl, box=reg["box"], links=links)
        reps[fl] = rep
        plan_floors.append({"floor": fl, "box": reg["box"], "dominant_level_m": rep["storey"]["plan_dominant_level_m"],
                            "rooms": rooms})
    import ezdxf
    from tools import arch_dimensions as ADIM
    doc = ezdxf.readfile(a.drawing)
    dims = ADIM.read_doc(doc)                     # every authored dimension of the file (the views' level chains)
    sb = SB.bind(texts, dims["dimensions"], dims["header_dimlfac"],
                 au["other_frames"], u, plan_floors)
    term = FH1.termination(inside_plate=True, plate_t_cm=16)            # plaster / paint do not use it under the rule
    per_floor = defaultdict(lambda: {"rooms": 0, "levelled": 0, "height_diag": 0, "wall_lm": 0.0, "wall_m2_diag": 0.0,
                                     "dry_wall_m2_diag": 0.0, "wet_wall_m2_diag": 0.0, "held": []})
    meta = {r["room_id"]: r for r in au["rooms"]}
    for fl, rep in reps.items():
        frep = sb["floors"].get(fl) or {}
        out["floors"][fl] = {"storey": rep["storey"], "zones": [
            {"level_m": z["level_m"], "rooms_printed": z["rooms"], "rooms_by_rule": z.get("rooms_by_rule", [])}
            for z in rep["zones"]], "findings": rep["findings"],
            "section_binding": [{"ffl_m": z["ffl"]["value_m"], "floor_to_floor": {
                k: z["floor_to_floor"].get(k) for k in ("value_m", "state", "why", "to_level_m")},
                "level_above": z.get("level_above")} for z in frep.get("zones", ())]}
        for r in rep["rooms"]:
            if r["state"] == "NOT_A_FLOOR_ROOM":
                continue
            m = meta[r["room_id"]]
            zone = RL.zone_of_v2(r, frep)
            if zone.get("state") == "BOUND" and zone["floor_to_floor"].get("value_m") is None and \
                    fl == max(reps, key=lambda f: SB.ORDER.get(f, 0)):
                zone = dict(zone, floor_to_floor=TOP_FLOOR_FACT)
            wet = m["kind"] == "WET"
            h = FH.room_heights(room=r, zone=zone, term=term, wet=wet, owner_rule=rule)
            q = h["WALL_TILE"] if wet else h["PAINT"]
            hd = q.get("height_m") if q.get("height_m") is not None else q.get("owner_rule_height_m")
            runs = m.get("runs_lm") or {}
            wall_lm = round(sum(runs.get(k, 0.0) for k in WALL_RUNS), 3)
            rec = {"floor": fl, "room_id": r["room_id"], "kind": m["kind"], "codes": m["codes"],
                   "area_m2": round(m["area_m2"], 2), "level_state": r["state"], "level_m": r["level_m"],
                   "level_why": r.get("why"), "level_source": r.get("source"),
                   "floor_to_floor": (zone.get("floor_to_floor") or {}).get("value_m") if zone.get("state") ==
                   "BOUND" else None,
                   "floor_to_floor_state": (zone.get("floor_to_floor") or {}).get("state") if zone.get("state") ==
                   "BOUND" else zone.get("why"),
                   "height_state": q["state"], "height_why": q.get("why"), "height_diag_m": hd,
                   "wall_lm": wall_lm, "runs_lm": {k: round(v, 3) for k, v in runs.items()},
                   "wall_m2_diag": round(wall_lm * hd, 2) if hd is not None else None}
            out["rooms"].append(rec)
            pf = per_floor[fl]
            pf["rooms"] += 1
            pf["levelled"] += r["state"] in RL.LEVELLED
            pf["wall_lm"] += wall_lm
            if hd is not None:
                pf["height_diag"] += 1
                pf["wall_m2_diag"] += rec["wall_m2_diag"]
                pf["wet_wall_m2_diag" if wet else "dry_wall_m2_diag"] += rec["wall_m2_diag"]
            else:
                pf["held"].append(f"{r['room_id']} {m['codes']}: " + str(rec["height_why"] or rec["level_why"])[:90])
    tot = {k: round(sum(v[k] for v in per_floor.values()), 2) for k in ("wall_m2_diag", "dry_wall_m2_diag",
                                                                         "wet_wall_m2_diag", "wall_lm")}
    out["per_floor"] = {k: dict(v, wall_lm=round(v["wall_lm"], 2), wall_m2_diag=round(v["wall_m2_diag"], 2),
                                dry_wall_m2_diag=round(v["dry_wall_m2_diag"], 2),
                                wet_wall_m2_diag=round(v["wet_wall_m2_diag"], 2)) for k, v in per_floor.items()}
    out["totals_diag"] = tot
    out["freelancer"] = FREELANCER
    out["note"] = ("diagnostic only: every owner height is HELD (BEAM_OVER_ROOM_NOT_CHECKED) in this run; areas are "
                   "gross (no door / window deduction); plaster = dry + wet walls (substrate behind tiles), paint = "
                   "dry walls only (UP-FIN-PAINT-001)")
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps({"per_floor": {k: {kk: vv for kk, vv in v.items() if kk != "held"}
                                    for k, v in out["per_floor"].items()}, "totals_diag": tot}, indent=1))


if __name__ == "__main__":
    main()
