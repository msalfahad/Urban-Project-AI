"""T-388 (development villa): the wall-face table of the candidate's finish families, built read-only from the
Checker-merged ledgers the candidate's own input modules pin (no drawing opened, nothing typed, no quantity changed).

    python3 -I research/agents_t388/alsenan_t388.py [--out research/agents_t388]

Sources (all MERGED; the candidate input module that pins each is named):
  faces      research/agents_t250/FACE_LENGTH_T250.csv (T-250: every room face on every wall run, metres named)
  block      research/agents_t333/OPENING_HEIGHT_BASIS_T333.csv + FILL_T333.csv (T-333 r2 -> t279_inputs, V3.0.26)
             block top per wall: research/agents_t237/FACES_T237.csv (T-237, register v1 + deltas)
  plaster /  research/agents_t128/ROOMS_T128_R3.csv (heights per room), agents_t237/CROSSWALK_T237.csv (opening ->
  paint      room face -> host wall), agents_t237/OPENING_SIZES_T237.csv (merged sizes) and the T-244 revisions
             (W15 / W16 4.3629, W17 room-side hole HELD 8.7414 .. 8.9965, W24 2.325, W29 1.800) (t211 / t244 inputs)
  tile       research/agents_t312/FACE_LEDGER_T312.csv + OPENINGS_T312.csv (T-312 -> t315_inputs, V3.0.21)
  backing    research/agents_t329/BACKING_FACE_LEDGER_T329.csv + PLASTER_LINE_MAP_T329.csv (T-329 -> t331, V3.0.22)
  reveals    research/agents_t313/REVEAL_LEDGER_T313.csv (T-313 r2 -> t326_inputs, V3.0.28), T-250 ROOM_CLOSURE
  thresholds research/agents_t325/STRIP_FLOOR_OVERLAP_T325.csv (T-325 -> t326 / t327 inputs, V3.0.28 / V3.0.29)
  paint lines research/agents_t211/t211_inputs.py records (the candidate's FIN.PAINT room lines)
Values, room / wall / opening ids and line ids only: no coordinate, no name, no drawing content.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
R = ROOT / "research"
sys.path.insert(0, str(HERE))
import face_check as FC  # noqa: E402


def rd(p):
    with open(R / p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# T-244 revisions of the room-face hole (merged T-238 / T-227 r2 / T-302 / T-201), applied as the candidate applies them
T244_HOLE = {"W15": 4.3629, "W16": 4.3629, "W17": None, "W24": 2.325, "W29": 1.8}
T244_HOLE_RANGE = {"W17": (8.7414, 8.9965)}


TOL_EXPLAINED = 0.1  # a T-312 residual row above this is a documented outline choice (GF-16: T-074 VERIFIED outline)

# merged explanation of a block deduction smaller than the face hole (T-333 r2 s.5 / T-285, Checker handle 2FD8)
BLOCK_PART = {"W18": (1.08, "T-333 r2 s.5 (T-285; Checker 2FD8): 0.0327 m of the 0.500 m width lies inside the column "
                            "outline the masonry run excludes; block 0.4673 x 2.160 = 1.0094, the finished face "
                            "(column plastered as wall, T-250 WALL+COLUMN) keeps the 0.50 x 2.16 hole")}


def build():
    wet_faces = rd("agents_t312/FACE_LEDGER_T312.csv")
    wet_rooms = {r["room"] for r in wet_faces}
    back = {r["face_id"]: r for r in rd("agents_t329/BACKING_FACE_LEDGER_T329.csv")}
    rooms = {r["ROW"]: r for r in rd("agents_t128/ROOMS_T128_R3.csv")}
    t237 = rd("agents_t237/FACES_T237.csv")
    block_top = {}
    for r in t237:
        h = num(r["block_h_m"])
        block_top.setdefault(r["wall_id"], h)
    # face spine: T-250 room faces aggregated per room|wall
    spine = defaultdict(lambda: {"length_m": 0.0, "runs": []})
    for r in rd("agents_t250/FACE_LENGTH_T250.csv"):
        k = f"{r['room']}|{r['wall_id']}"
        spine[k]["length_m"] += float(r["face_m"])
        spine[k]["door_m"] = spine[k].get("door_m", 0.0) + float(r["door_m"] or 0)
        spine[k]["gap_m"] = spine[k].get("gap_m", 0.0) + float(r["gap_m"] or 0)
        spine[k]["runs"].append(r["run_id"])
        spine[k]["room"], spine[k]["wall"] = r["room"], r["wall_id"]
    for r in t237:  # opening-hosting faces off a straight run (curved glazing, a run with no T-250 row)
        k = f"{r['room']}|{r['wall_id']}"
        if k not in spine:
            spine[k]["room"], spine[k]["wall"] = r["room"], r["wall_id"]
            spine[k]["length_m"] = None
    faces = []
    for fid in sorted(set(spine) | {r["face_id"] for r in wet_faces if r["scope"] == "TILED"}):
        room, wall = fid.split("|", 1)
        rr = rooms.get(room, {})
        f = {"face_id": fid, "room": room, "wall": wall, "room_class": "WET" if room in wet_rooms else
             ("SHAFT" if rr.get("KIND") == "SHAFT" else "DRY"),
             "length_m": (round(spine[fid]["length_m"], 4) if spine[fid]["length_m"] is not None else None)
             if fid in spine else None, "tops": {}, "states": {},
             "drawing_tops": {}, "door_m": spine.get(fid, {}).get("door_m"), "gap_m": spine.get(fid, {}).get("gap_m")}
        f["tops"]["block"] = block_top.get(wall)
        if f["room_class"] == "WET":
            w = [x for x in wet_faces if x["face_id"] == fid]
            b = back.get(fid, {})
            f["tops"]["tile"] = num(w[0]["owner_h_m"]) if w else None
            f["tops"]["backing"] = num(b.get("owner_plaster_top_m"))
            f["states"]["tile"] = w[0]["owner_status"] if w else "NO_TILE_FACE"
            f["states"]["backing"] = b.get("owner_status", "NO_BACKING_FACE")
            if w and f["length_m"] is None:
                f["length_m"] = round(sum(float(x["length_m"]) for x in w), 4)
            f["tile_length_m"] = round(sum(float(x["length_m"]) for x in w), 4) if w else None
        else:
            oh = num(rr.get("OWNER_H_M"))
            f["tops"]["plaster"] = oh
            f["tops"]["paint"] = oh
            f["drawing_tops"] = {"plaster": rr.get("DWG_PLASTER_H_TOP_M"), "paint": rr.get("DWG_PAINT_TILE_H_M")}
            f["states"]["plaster"] = rr.get("OWNER_STATUS", "")[:60]
        faces.append(f)

    # deductions
    ded = []
    curved = {r["opening"]: float(r["t128_walked_m"]) for r in rd("agents_t250/CURVED_ROOM_SIDE_T250.csv")}
    sizes = {(r["room"], r["census_id"]): r for r in rd("agents_t237/OPENING_SIZES_T237.csv")}
    for r in rd("agents_t237/CROSSWALK_T237.csv"):
        if r["room"] in wet_rooms or not r["census_id"] or not r["host_wall"]:
            continue
        s = sizes.get((r["room"], r["census_id"]), {})
        m2 = num(s.get("merged_fixed_m2"))
        if m2 is None and s.get("merged_status", "").upper().startswith(("ASSUMED", "DRAWING")):
            w, h = num(s.get("merged_w")), num(s.get("merged_head"))
            sill = num(s.get("merged_sill")) or 0.0
            if w is not None and h is not None:
                m2 = round(w * (h - sill), 4)
        op = r["census_id"]
        if op in T244_HOLE:
            m2 = T244_HOLE[op]
        extra = {}
        if s.get("code", "").startswith("SPLIT_FACE"):
            tw, mw = num(s.get("t128_w")), num(s.get("merged_w"))
            if op in curved:  # the finishes' opening width is the developed room-side line (T-250 R-T250-2)
                mw = curved[op]
            H = num(rooms.get(r["room"], {}).get("OWNER_H_M"))
            head = num(s.get("merged_head")) or 0.0
            h = (min(head, H) if H else head) - (num(s.get("merged_sill")) or 0.0)
            extra = {"split_w": tw, "full_w": mw, "full_m2": round(mw * h, 4) if mw and h else None}
            m2 = round(tw * h, 4) if tw and h else None
        for fam in ("plaster", "paint"):
            ded.append({"family": fam, "face_id": f"{r['room']}|{r['host_wall']}", "opening": op, "m2": m2,
                        "w": num(s.get("merged_w")), "kind": r["t128_class"], "source": "T-237 crosswalk + sizes (T-244 revisions)", **extra})
    for r in rd("agents_t312/OPENINGS_T312.csv"):
        for fam in ("tile", "backing"):
            ms = r["merged_size"].split()
            wv = num(ms[1]) if len(ms) > 1 and ms[0] == "w" else None
            ded.append({"family": fam, "face_id": r["face_id"], "opening": r["opening_id"], "w": wv, "kind": r["kind"],
                        "m2": num(r["band_m2"]) if r["state"] == "DETERMINATE" else None, "source": "T-312 OPENINGS"})
    block = []
    for r in rd("agents_t333/FILL_T333.csv"):
        if r["item_code"] != "MAS.BLOCK" or not r["opening_deductions"]:
            continue
        for part in r["opening_deductions"].split(";"):
            p = part.split()
            if not p:
                continue
            m2 = num(p[1]) if len(p) > 1 else None
            b = {"wall": r["wall_id"], "opening": p[0], "m2": m2, "block_state": p[-1]}
            if p[0] in BLOCK_PART:
                b["full_hole_m2"], b["reason"] = BLOCK_PART[p[0]]
            block.append(b)

    # reveals: door / arch / gate reveals carried by a line (FIN.PLASTER jambs + head); the room face's jamb returns
    closure = {r["room"]: r for r in rd("agents_t250/ROOM_CLOSURE_T250.csv")}
    t128_ops = defaultdict(list)
    for r in rd("agents_t128/OPENINGS_T128_R3.csv"):
        t128_ops[r["ROOM_ROW"]].append(r)
    jamb_excess = {}
    for room, c in closure.items():
        off = float(c["off: DOOR+GAP"] or 0)
        doors = sum(float(o["WIDTH_M"]) for o in t128_ops[room] if o["CLASS"] in ("door", "arch", "gate", "opening"))
        jamb_excess[room] = {"off_door_gap_m": off, "door_widths_m": round(doors, 4),
                             "excess_m": round(max(0.0, off - doors), 4)}
    reveals = []
    rv = rd("agents_t313/REVEAL_LEDGER_T313.csv")
    for r in rv:
        if r["side"] == "THROUGH" and r["component"] == "JAMBS" and r["line_id"] not in ("", "NO_LINE"):
            room = r["room"]
            ex = jamb_excess.get(room, {}).get("excess_m", 0.0)
            reveals.append({"opening": r["opening"], "room": room, "carrier": r["line_id"], "jamb_return_m": ex,
                            "h_m": 2.2})
    window_room_side = [r for r in rv if r["kind"] in ("WINDOW", "FLOOR_GLAZING") and r["side"] == "IN"]
    thresholds = [{"opening": r["openings"], "strip_m2": r["strip_m2"],
                   "floor_overlap_m2": r["overlap_with_room_floors_m2"]}
                  for r in rd("agents_t325/STRIP_FLOOR_OVERLAP_T325.csv")]

    # room closure: each family's face length against the T-250 geometric face (contour less its open sides)
    closures = []
    t312_len = defaultdict(float)
    t312_expl = defaultdict(list)
    for r in wet_faces:
        if r["scope"] == "TILED":
            t312_len[r["room"]] += float(r["length_m"])
            if r["piece"] == "WALK CLASS RESIDUAL":
                t312_expl[r["room"]].append((float(r["length_m"]), r["length_source"]))
    for room, c in closure.items():
        geo = float(c["walk_contour_m (T-128 r3)"]) - float(c["off: VIRTUAL (open side)"])
        rr = rooms.get(room, {})
        top = num(rr.get("OWNER_H_M")) if not rr.get("OWNER_STATUS", "").startswith("HELD (G2") else None
        if room in wet_rooms:
            fl = t312_len[room]
            ex = [e for e in t312_expl[room] if abs(e[0]) > TOL_EXPLAINED and "VERIFIED" in e[1]]
            for fam in ("tile", "backing"):
                closures.append({"room": room, "family": fam, "family_length_m": round(fl, 4),
                                 "geometric_length_m": round(geo, 4), "top_m": top, "explained": bool(ex),
                                 "cause": "T-128 r3 open side %s m vs T-250 virtual %s m" % (rr.get("OPEN_SIDES_M"),
                                                                                           c["off: VIRTUAL (open side)"])})
        else:
            fl = float(rr.get("FACE_M") or 0)
            for fam in ("plaster", "paint"):
                closures.append({"room": room, "family": fam, "family_length_m": round(fl, 4),
                                 "geometric_length_m": round(geo, 4), "top_m": top, "explained": False,
                                 "cause": "T-128 r3 open side %s m vs T-250 virtual %s m" % (rr.get("OPEN_SIDES_M"),
                                                                                           c["off: VIRTUAL (open side)"])})
    # tile / backing above the block top: the coat and tile sit on the concrete band of the member over the wall
    over_band = []
    for f in faces:
        t, b, L = f["tops"].get("tile"), f["tops"].get("block"), f["length_m"]
        if f["room_class"] == "WET" and t is not None and b is not None and t > b + 1e-6:
            over_band.append({"face_id": f["face_id"], "tile_top": t, "block_top": b,
                              "m2": round((t - b) * L, 4) if L else None})
    return {"closures": closures, "over_band": over_band, "faces": faces, "deductions": ded, "block": block, "reveals": reveals, "thresholds": thresholds,
            "jamb_excess": jamb_excess, "window_room_side": window_room_side, "wet_rooms": sorted(wet_rooms)}


def paint_line_states():
    """The candidate's FIN.PAINT room lines as t211_inputs prints them (item, room, state, ...)."""
    import subprocess
    out = subprocess.run([sys.executable, "-I", str(R / "agents_t211" / "t211_inputs.py")], capture_output=True,
                         text=True, check=True, cwd=str(ROOT)).stdout
    res = []
    for line in out.splitlines():
        p = line.split()
        if len(p) >= 3 and p[0] == "FIN.PAINT":
            res.append({"room": p[1], "state": p[2], "evidence": p[-1]})
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    d = build()
    d["paint_lines"] = paint_line_states()
    fnd = FC.check(d["faces"], d["deductions"], d["block"], d["reveals"], d["thresholds"], d["paint_lines"],
                   d["closures"])
    summary = {"faces": len(d["faces"]), "by_class": {}, "deductions": len(d["deductions"]),
               "block_deductions": len(d["block"]), "reveal_carriers": len(d["reveals"]),
               "thresholds": len(d["thresholds"]), "findings": {}}
    for f in d["faces"]:
        summary["by_class"][f["room_class"]] = summary["by_class"].get(f["room_class"], 0) + 1
    for x in fnd:
        summary["findings"].setdefault(x["kind"], {"n": 0, "m2": 0.0})
        summary["findings"][x["kind"]]["n"] += 1
        summary["findings"][x["kind"]]["m2"] = round(summary["findings"][x["kind"]]["m2"] + (x["m2"] or 0.0), 4)
    summary["max_threshold_floor_overlap_m2"] = max(float(t["floor_overlap_m2"] or 0) for t in d["thresholds"])
    summary["window_room_side_reveal_m2"] = round(sum(float(r["m2"] or 0) for r in d["window_room_side"]), 4)
    summary["tile_over_block_top"] = {"faces": len(d["over_band"]),
                                      "m2": round(sum(x["m2"] or 0 for x in d["over_band"]), 4)}
    summary["jamb_excess_rooms"] = {k: v for k, v in d["jamb_excess"].items() if v["excess_m"] > 0}
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "FACES_T388.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["face_id", "room", "wall", "room_class", "length_m", "block_top_m", "plaster_top_m",
                        "paint_top_m", "tile_top_m", "backing_top_m", "dwg_plaster_top_m", "dwg_paint_top_m",
                        "states", "plaster_paint_ded", "tile_backing_ded", "block_ded_on_wall"])
            byf = defaultdict(lambda: defaultdict(list))
            for x in d["deductions"]:
                byf[x["face_id"]][x["family"]].append(f"{x['opening']} {x['m2'] if x['m2'] is not None else 'HELD'}")
            bw = defaultdict(list)
            for b in d["block"]:
                bw[b["wall"]].append(f"{b['opening']} {b['m2'] if b['m2'] is not None else 'HELD'}")
            for f in d["faces"]:
                t = f["tops"]
                w.writerow([f["face_id"], f["room"], f["wall"], f["room_class"], f["length_m"], t.get("block"),
                            t.get("plaster"), t.get("paint"), t.get("tile"), t.get("backing"),
                            f["drawing_tops"].get("plaster"), f["drawing_tops"].get("paint"),
                            "; ".join(f"{k}={v}" for k, v in f["states"].items()),
                            "; ".join(byf[f["face_id"]]["plaster"]), "; ".join(byf[f["face_id"]]["tile"]),
                            "; ".join(bw.get(f["wall"], []))])
        with open(out / "FINDINGS_T388.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["kind", "m2", "detail"])
            for x in fnd:
                w.writerow([x["kind"], "" if x["m2"] is None else x["m2"],
                            json.dumps({k: v for k, v in x.items() if k not in ("kind", "m2")}, sort_keys=True)])
        st = defaultdict(list)
        for r in rd("agents_t325/SILL_THRESHOLD_LEDGER_T325.csv"):
            st[r["opening"]].append(r)
        rv = defaultdict(list)
        for r in rd("agents_t313/REVEAL_LEDGER_T313.csv"):
            rv[r["opening"]].append(r)
        ops = sorted({x["opening"] for x in d["deductions"]} | {b["opening"] for b in d["block"]} | set(rv))
        with open(out / "OPENINGS_T388.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["opening", "block", "plaster_paint_faces", "tile_backing_faces", "reveals (side component m2 "
                        "state line)", "sill_threshold (component m2 state line)", "deducted_once_per_family_face"])
            bad = {(x.get("opening"), x["kind"]) for x in fnd}
            for op in ops:
                bl = [f"{b['wall']} {b['m2'] if b['m2'] is not None else 'HELD'} {b['block_state']}"
                      for b in d["block"] if b["opening"] == op]
                pp = sorted({f"{x['face_id']} {x['m2'] if x['m2'] is not None else 'HELD'}" for x in d["deductions"]
                             if x["opening"] == op and x["family"] == "plaster"})
                tb = sorted({f"{x['face_id']} {x['m2'] if x['m2'] is not None else 'HELD'}" for x in d["deductions"]
                             if x["opening"] == op and x["family"] == "tile"})
                rr = [f"{r['side']} {r['component']} {r['m2']} {r['state']} {r['line_id']}" for r in rv.get(op, [])]
                tt = "; ".join(f"{t['component']} {t['m2']} {t['state']} {t['line_id']}" for t in st.get(op, []))
                once = "NO" if any(k in ("DUPLICATE_DEDUCTION", "OPENING_ON_TOO_MANY_FACES") for o, k in bad
                                   if o == op) else "YES"
                w.writerow([op, "; ".join(bl), "; ".join(pp), "; ".join(tb), "; ".join(rr), tt, once])
        (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, sort_keys=True))
    for x in fnd:
        print(x)
    return d, fnd


if __name__ == "__main__":
    main()
