"""T-086 read-only Alsenan run: the owner's room-by-room finishing table (FINISH_MATERIALS_TABLE_V1) built from the
merged pieces only, and compared with the freelancer's tiling rows.

Areas (never the freelancer's):
    dry floors      ARCH_TAKEOFF_V2.9 FIN.FLOOR.PORCELAIN lines of rooms whose V2.9 finish scope is DRY (net of the
                    stair treads V2.9 deducts); doorway strips summed per floor; the open GF room (V2.9 scope REVIEW)
                    HELD with its candidate; unlabelled V2.9 faces that are not one of the hand-table wet areas HELD
    wet floors      the verified wet-area hand table (research/agents_t074, 17 areas, 72.12 m2) + the pantry inside its
                    printed 4.50 x 3.00 (owner Q-37 A)
    wet walls       hand-table boundary - door widths (owner Q-48 A) x the T-088 owner wall height; every wet room is
                    HELD there (beam not 0.60 m: open owner Q-52, or level unclear), so the wall m2 is a candidate only
    stairs          the verified stair hand table (research/agents_t084) with owner Q-46 A (section A-A counts) and Q-47 A
    roofs           research/agents_t071 membrane areas inside the parapet; screed (Q-41) and roof finish HELD
Usage (Python 3.11, the drawing outside the clone):
    python3 -I research/agents_t086/alsenan_finish_table.py --v29 <scratch>/v29.pkl --out <scratch>/t086
    (or <P7757.dxf> instead of --v29; the V2.9 run takes about 40 s)
Writes only to --out. Areas, lengths and engine room ids only."""

from __future__ import annotations

import csv
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import finish_materials_table as F  # noqa: E402

HERE = ROOT / "research"

# T-074 wet-area index -> T-088 room row (same rooms, read by hand on the same sheets)
WET_TO_T088 = ["GF-02", "GF-03", "GF-05", "GF-06", "GF-10", "GF-11", "GF-12", "GF-13", "GF-14", "GF-16",
               "1F-02", "1F-03", "1F-07", "1F-08", "1F-09", "1F-12", "2F-02"]

# freelancer FIN workbook, sheet of tiles: dry floor rows (row, m2) matched to V2.9 rooms by area and perimeter
FREELANCER_DRY = {
    "GF-R7512EA": (16, 24.84), "GF-R75FBAE": (14, 16.66), "GF-R51E127": (17, 7.87),
    "1F-R78C367": (21, 38.96), "1F-R0E919A": (22, 17.29), "1F-R3CFCFD": (23, 19.46), "1F-RED0D19": (24, 18.25),
    "1F-RB72F22": (25, 19.00), "2F-R1DB2D2": (28, 19.58), "2F-LOBBY": (29, 7.70),
    "GF-OPEN": (13, 137.50),   # reception + dining; his entrance row 15 (10.46) has no engine face of its own
}
FREELANCER_TOTALS = {"dry_floors_m2": 337.57, "wet_floors_m2": 72.01, "floors_m2": 409.58, "wet_walls_m2": 433.83,
                     "wet_wall_height_m": 3.00}


def load_v29(a):
    if a.v29:
        boq, arch, _ = pickle.load(open(a.v29, "rb"))
    else:
        from tools import urban_boq_m9 as M
        boq, arch, _ = M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.9")
    return boq, arch


def scope(r):
    fs = r.get("finish_scope")
    return fs.get("scope") if isinstance(fs, dict) else None


def build(boq, arch):
    wet = json.loads((HERE / "agents_t074" / "wet_areas_hand_table.json").read_text(encoding="utf-8"))
    t088 = {r["ROW"]: r for r in csv.DictReader(open(HERE / "agents_t088" / "ROOMS.csv", encoding="utf-8"))}
    stairs = {r["ID"]: r for r in csv.DictReader(open(HERE / "agents_t084" / "STAIRS.csv", encoding="utf-8"))}
    ext = json.loads((HERE / "agents_t071" / "alsenan_exterior_spaces.json").read_text(encoding="utf-8"))
    rooms = {r["room_id"]: r for r in arch["rooms"]}
    porc = [l for l in boq["lines"] if l["item_code"] == "FIN.FLOOR.PORCELAIN"]
    el = []

    # ---- wet floors (hand table) and the faces they explain
    wet_faces = set()
    for i, w in enumerate(wet):
        tid = WET_TO_T088[i]
        el.append({"id": f"WF-{tid}", "floor": w["floor"], "name": w["room_as_printed"], "kind": F.WET_FLOOR,
                   "area_m2": w["floor_m2"], "source": "T-074 wet-area hand table (verified, merged)",
                   "basis": w["outline_source"], "t088": tid, "freelancer_m2": (w.get("freelancer") or {}).get("floor_m2")})
        for r in arch["rooms"]:
            if r["floor"] == w["floor"] and abs(r["area_m2"] - w["floor_m2"]) <= 0.02 and r["class"] in ("ROOM", "UNLABELLED"):
                wet_faces.add(r["room_id"])
    el.append({"id": "WF-GF-07", "floor": "GF", "name": "PANTRY / تحضير (open to the dining)", "kind": F.WET_FLOOR,
               "length": 4.50, "width": 3.00, "source": "owner Q-37 A: inside its printed 4.50 x 3.00",
               "basis": "printed 450 x 300 (sheet 03)", "freelancer_m2": None})

    # ---- dry floors (V2.9 porcelain lines)
    strips = {}
    for l in porc:
        rid, fl = l["location"]["room_id"], l["location"]["floor"]
        if l["physical_element"] == "doorway strip":
            strips.setdefault(fl, []).append(l["measured_net"])
            continue
        r = rooms.get(rid)
        if r is None or rid in wet_faces or scope(r) == "WET":
            continue                                    # the kitchen is a wet area (owner Q-30): bartash, not porcelain
        if scope(r) == "DRY":
            el.append({"id": f"DF-{rid}", "floor": fl, "name": l["location"]["room_name_en"], "kind": F.DRY_FLOOR,
                       "area_m2": l["measured_net"], "source": "ARCH_TAKEOFF_V2.9 FIN.FLOOR.PORCELAIN (MACHINE_ONLY)",
                       "basis": l["calculation"]["formula"], "freelancer": FREELANCER_DRY.get(rid)})
    open_rooms = [l for l in porc if rooms.get(l["location"]["room_id"]) is not None
                  and scope(rooms[l["location"]["room_id"]]) == "REVIEW"]
    cand = sum(l["measured_net"] for l in open_rooms) - 13.50
    el.append({"id": "DF-GF-OPEN", "floor": "GF", "name": "Dining + reception + saloon (open plan)", "kind": F.DRY_FLOOR,
               "area_status": "HELD", "candidate_m2": cand,
               "area_reason": "OPEN_PLAN_ZONE_NOT_CONFIRMED (V2.9 scope REVIEW: the zone is bounded by drawn lines that "
                              "are not walls; candidate = V2.9 porcelain " +
                              " + ".join(f"{l['measured_net']:.2f}" for l in open_rooms) + " - pantry 13.50 (Q-37 A))",
               "source": "ARCH_TAKEOFF_V2.9", "freelancer": FREELANCER_DRY["GF-OPEN"]})
    for fl, v in sorted(strips.items()):
        el.append({"id": f"DF-{fl}-DOORWAY-STRIPS", "floor": fl, "name": f"doorway strips ({len(v)})", "kind": F.DRY_FLOOR,
                   "area_m2": sum(v), "source": "ARCH_TAKEOFF_V2.9 FIN.FLOOR.PORCELAIN doorway strips", "freelancer": None})
    el.append({"id": "DF-2F-LOBBY", "floor": "2F", "name": "stair lobby (printed 450 x 195)", "kind": F.DRY_FLOOR,
               "length": 4.50, "width": 1.95, "source": "T-088 printed lobby 450 x 195 (page 5)",
               "freelancer": FREELANCER_DRY["2F-LOBBY"]})
    for r in arch["rooms"]:
        if r["class"] == "UNLABELLED" and r["room_id"] not in wet_faces:
            el.append({"id": f"DF-{r['room_id']}", "floor": r["floor"], "name": "unlabelled face", "kind": F.DRY_FLOOR,
                       "area_status": "HELD", "candidate_m2": r["area_m2"],
                       "area_reason": "UNLABELLED_FACE (no room label, not a hand-table wet area: finish not known)",
                       "source": "ARCH_TAKEOFF_V2.9", "freelancer": None})
        if r["class"] == "ROOM" and r["codes"] == ["STAIR"] and r["floor"] != "2F":
            el.append({"id": f"DF-{r['room_id']}", "floor": r["floor"], "name": "stair hall floor", "kind": F.DRY_FLOOR,
                       "area_status": "HELD", "candidate_m2": r["area_m2"],
                       "area_reason": "STAIR_HALL_FLOOR_NOT_SEPARATED (V2.9 types the face as a stair; the hall floor "
                                      "beside the flights is not measured)", "source": "ARCH_TAKEOFF_V2.9",
                       "freelancer": None})

    # ---- wet walls (hand-table lengths, T-088 heights)
    for i, w in enumerate(wet):
        tid = WET_TO_T088[i]
        t = t088[tid]
        h = t["OWNER_WALL_HEIGHT_M (0.60 beam; decor 0.15 by owner Q-48 A)"]
        el.append({"id": f"WW-{tid}", "floor": w["floor"], "name": w["room_as_printed"], "kind": F.WET_WALL,
                   "wall_length": w["boundary_lm"], "door_widths": [d["width_m"] for d in w["doorways"]],
                   "height_status": t["STATUS"], "height_reason": f"{t['HELD_REASON'].split(';')[0]} (T-088; owner Q-52 open)",
                   "candidate_height": float(h) if h not in ("-", "", "none") else None,
                   "source": "T-074 boundary - door widths (Q-48 A) x T-088 wall height"})
    el.append({"id": "WW-GF-07", "floor": "GF", "name": "PANTRY walls", "kind": F.WET_WALL, "wall_length": None,
               "source": "T-088 GF-07: NOT CLOSED (no wall on the dining side)"})

    # ---- stairs (T-084 + owner Q-46 A section counts, Q-47 A landings)
    ms1 = 4.50 / 27
    ms2 = 4.20 / 25
    fl = [("E1", "GF", "entrance flight (+0.15 to +1.00)", dict(steps=5, riser=0.85 / 5, tread=0.30, width=2.80)),
          ("D1", "GF", "hall down to the +0.30 lobby", dict(steps=4, riser=0.70 / 4, tread=0.30, width=1.20)),
          ("MS1-L", "GF", "main stair GF-1F lower flight (A-A: 10)", dict(steps=10, riser=ms1, tread=0.30, width=1.20)),
          ("MS1-U", "GF", "main stair GF-1F upper flight (A-A: 12)", dict(steps=12, riser=ms1, tread=0.30, width=1.20)),
          ("MS2-L", "1F", "main stair 1F-2F lower flight (A-A: 12 + closing riser)",
           dict(steps=12, risers=13, riser=ms2, tread=0.30, width=1.20)),
          ("MS2-U", "1F", "main stair 1F-2F upper flight (A-A: 12)", dict(steps=12, riser=ms2, tread=0.30, width=1.20))]
    for sid, f, name, kw in fl:
        el.append(dict(kw, id=f"ST-{sid}", floor=f, name=name, kind=F.STAIR_FLIGHT,
                       source=f"T-084 {sid} (owner Q-46 A: section A-A counts; Q-19 step)"))
    el.append({"id": "ST-MS1-LD", "floor": "GF", "name": "main stair GF-1F landing (printed 120 x 125)",
               "kind": F.STAIR_LANDING, "length": 1.20, "width": 1.25, "source": "T-084 MS1-LD"})
    el.append({"id": "ST-MS2-LD", "floor": "1F", "name": "main stair 1F-2F half landing (printed 250 x 125)",
               "kind": F.STAIR_LANDING, "length": 2.50, "width": 1.25, "source": "T-084 MS2-LD"})
    for sid, reason in [("MS1-T", "WINDER_GEOMETRY_NOT_ESTABLISHED (5 winders on A-A; owner Q-51 open)"),
                        ("RS-C", "RISERS_NOT_COUNTED_ON_A_SECTION + TAPERED_TREAD (owner Q-50, Q-51 open)"),
                        ("RS-S", "RISERS_NOT_COUNTED_ON_A_SECTION (owner Q-50 open)"),
                        ("RS-A", "RISERS_NOT_COUNTED_ON_A_SECTION (owner Q-50 open)"),
                        ("RS-LD", "corner landing size not printed (T-084 RS-A)")]:
        el.append({"id": f"ST-{sid}", "floor": "GF" if sid != "RS-A" else "1F", "name": stairs.get(sid, {}).get(
            "STAIR", "round stair corner landing") + " " + stairs.get(sid, {}).get("FLIGHT", ""),
            "kind": F.STAIR_FLIGHT if sid != "RS-LD" else F.STAIR_LANDING, "area_status": "HELD", "area_reason": reason,
            "source": f"T-084 {sid}"})

    # ---- roofs (T-071 membrane inside the parapet)
    for x in ext:
        reg = x["region"]
        m2 = x["trace_summary"]["membrane_m2_by_code"].get("ROOF")
        held = x["trace_summary"]["by_status"].get("HELD", 0)
        e = {"id": f"RF-{reg}", "floor": "ROOF", "name": f"roof over {reg.split(':')[1]}", "kind": F.ROOF,
             "source": "T-071 exterior spaces (inside the parapet, owner Q-24 A)"}
        if m2:
            e["area_m2"] = m2
        else:
            e.update(area_status="HELD", area_reason=f"T-071: {held} exterior labels HELD on this sheet")
        el.append(e)
    return el


def compare(t, el):
    rows = {r["id"]: r for r in t["rows"]}
    out = {"dry_rooms": [], "totals": {}}
    for e in el:
        fr = e.get("freelancer")
        if e["kind"] == F.DRY_FLOOR and fr:
            r = rows[e["id"]]
            v = r["area_m2"]
            out["dry_rooms"].append({"id": e["id"], "engine_m2": v, "status": r["status"], "candidate_m2": r["candidate_m2"],
                                     "freelancer_row": fr[0], "freelancer_m2": fr[1],
                                     "diff_m2": None if v is None else round(v - fr[1], 3),
                                     "diff_pct": None if v is None else round(100 * (v - fr[1]) / fr[1], 2)})
    matched = [x for x in out["dry_rooms"] if x["engine_m2"] is not None]
    e_sum = sum(x["engine_m2"] for x in matched)
    f_sum = sum(x["freelancer_m2"] for x in matched)
    wf = t["per_kind"][F.WET_FLOOR]
    wf17 = sum(rows[e["id"]]["area_m2"] for e in el if e["kind"] == F.WET_FLOOR and e["id"] != "WF-GF-07")
    ww = [rows[e["id"]] for e in el if e["kind"] == F.WET_WALL]
    ww_cand = sum(r["candidate_m2"] or 0 for r in ww)
    out["totals"] = {
        "dry_matched_rooms": len(matched), "dry_matched_engine_m2": round(e_sum, 3), "dry_matched_freelancer_m2": round(f_sum, 3),
        "dry_matched_diff_pct": round(100 * (e_sum - f_sum) / f_sum, 2),
        "dry_released_m2": t["per_kind"][F.DRY_FLOOR]["area_m2"], "freelancer_dry_m2": FREELANCER_TOTALS["dry_floors_m2"],
        "wet_17_engine_m2": round(wf17, 4), "freelancer_wet_m2": FREELANCER_TOTALS["wet_floors_m2"],
        "wet_17_diff_pct": round(100 * (wf17 - FREELANCER_TOTALS["wet_floors_m2"]) / FREELANCER_TOTALS["wet_floors_m2"], 2),
        "wet_with_pantry_m2": wf["area_m2"],
        "wet_wall_released_m2": t["per_kind"][F.WET_WALL]["area_m2"],
        "wet_wall_candidate_m2_before_windows": round(ww_cand, 3),
        "wet_wall_candidate_rooms": sum(1 for r in ww if r["candidate_m2"]),
        "freelancer_wet_walls_m2": FREELANCER_TOTALS["wet_walls_m2"],
    }
    return out


def face_census(arch, el):
    """Every V2.9 face is in a row or has a stated reason for being outside the table (no silent omission)."""
    used = {e["id"][3:] for e in el if e["id"].startswith("DF-")}
    wet_area = [(e["floor"], e["area_m2"]) for e in el if e["kind"] == F.WET_FLOOR and e.get("area_m2")]
    out = []
    for r in arch["rooms"]:
        rid, codes = r["room_id"], r["codes"]
        if rid in used:
            where = "row DF-" + rid
        elif scope(r) == "REVIEW":
            where = "row DF-GF-OPEN (open-plan zone, HELD)"
        elif any(f == r["floor"] and abs(a - r["area_m2"]) <= 0.02 for f, a in wet_area):
            where = "a wet-area row WF-* (T-074 hand table, matched by floor and area +-0.02 m2)"
        elif codes == ["SHAFT"]:
            where = "excluded: service shaft (no floor finish)"
        elif codes == ["GARDEN"]:
            where = "excluded: exterior court / garden (outside the building finishes; not in the freelancer's tile rows)"
        elif r["class"] == "MERGED":
            where = "excluded: zone shared with its parent face (V2.9 MERGED; counted with the parent)"
        elif codes == ["STAIR"] and r["floor"] == "2F":
            where = "row DF-2F-LOBBY (printed 450 x 195); the rest of the face is the stair well"
        else:
            where = "NOT IN TABLE"
        out.append({"face": rid, "floor": r["floor"], "codes": codes, "class": r["class"], "m2": round(r["area_m2"], 3),
                    "in_table": where})
    return out


def write(t, cmp_, out):
    out.mkdir(parents=True, exist_ok=True)
    (out / "t086_alsenan_table.json").write_text(json.dumps({"table": t, "compare": cmp_}, ensure_ascii=False, indent=1,
                                                            default=str), encoding="utf-8")
    cols = ["floor", "id", "name", "kind", "finish", "status", "area_m2", "candidate_m2", "reason", "bed_low_m",
            "bed_high_m", "mix", "mortar_m3_low", "mortar_m3_high", "cement_bags_low", "cement_bags_high", "sand_m3_low",
            "sand_m3_high", "cement_sand_status", "cement_sand_reason", "adhesive_bags", "adhesive_status",
            "adhesive_reason", "source"]
    with open(out / "t086_alsenan_table.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, cols, extrasaction="ignore")
        w.writeheader()
        for r in t["rows"]:
            w.writerow(r)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing", nargs="?")
    ap.add_argument("--v29")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    boq, arch = load_v29(a)
    el = build(boq, arch)
    t = F.table(el)
    c = compare(t, el)
    c["face_census"] = face_census(arch, el)
    c["faces_not_in_table"] = [x["face"] for x in c["face_census"] if x["in_table"] == "NOT IN TABLE"]
    write(t, c, Path(a.out))
    print(json.dumps({"project": t["project"], "per_kind": {k: {kk: v[kk] for kk in ("area_m2", "mortar_m3_low",
          "mortar_m3_high", "cement_bags_low", "cement_bags_high", "sand_m3_low", "sand_m3_high", "adhesive_bags",
          "held_rows")} for k, v in t["per_kind"].items()}, "compare": {k: v for k, v in c.items() if k != "face_census"}}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
