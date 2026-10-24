"""T-262 runner for the development villa (Alsenan): every opening of the engine-independent inventory (T-249, merged)
joined to its rooms by geometry (opening_rooms.py), then checked against
  (1) the census side labels (T-198 SIDE_A / SIDE_B, carried from T-144 / T-150 / T-175),
  (2) the T-128 r3 per-room opening table (the plaster / paint and wet-tile ledgers' deductions, merged a6ac2c66),
  (3) the T-237 crosswalk (merged 1cc1a153: room -> census id joined by name / width),
and the room regions that cover a wall strip or an opening reveal (GF-16).

Input: the T-262 capture pickle (coordinates, outside the repository). Outputs (ids, handles, room ids, lengths and
areas only): OPENING_ROOMS_T262.csv, T128_ROOM_CHECK_T262.csv, T237_JOIN_CHECK_T262.csv, REGION_OVERLAP_T262.csv,
summary.json. `--check` recomputes and compares with the committed files instead of writing them.

    python -I research/agents_t262/alsenan_t262.py <scratch>/t262_capture.pkl [--check]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import pickle
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import opening_rooms as J  # noqa: E402

CENSUS = ROOT / "research/agents_t198/OPENINGS_T198.csv"
T128_OPS = ROOT / "research/agents_t128/OPENINGS_T128_R3.csv"
T237_X = ROOT / "research/agents_t237/CROSSWALK_T237.csv"
T209_IN = ROOT / "research/agents_t209/ALSENAN_T209_INPUT.json"

NO = "NO_ROOM"
# What each census side label CLAIMS, read once by the T-128 room names (ROOMS_T128_R3.csv ROOM column); the label is
# a name, so this table is the label's claim, never the opening's room. NO_ROOM = outdoors, or an interior space with
# no walked region (named in UNWALKED).
LABELS = {
    "dewaneya": {"GF-01"}, "wash by the dewaneya": {"GF-02"}, "W.C. by the dewaneya": {"GF-03"},
    "driver room": {"GF-04"}, "driver W.C.": {"GF-05"}, "kitchen": {"GF-06"}, "pantry (open room)": {"GF-07"},
    "dining / entrance (open room)": {"GF-08"}, "saloon (open room)": {"GF-08"},
    "stair passage / basin space": {"ST-GF", "GF-11"}, "stair hall GF": {"ST-GF"}, "GF stair hall": {"ST-GF"},
    "W.C. 175 x 135 by the stair": {"GF-10"}, "basin space 110 x 135": {"GF-11"},
    "W.C. core wedge A": {"GF-12"}, "W.C. core wedge B": {"GF-13"}, "wash lobby": {"GF-14"},
    "GF master bed room": {"GF-15"}, "GF master bed room / pool court": {"GF-15"},
    "bath of the master bed room": {"GF-16"},
    "1F master bed room west 425 x 450": {"1F-01"}, "bath west upper 245 x 205": {"1F-02"},
    "bath west lower 245 x 205": {"1F-03"}, "1F master bed room 500 x 365": {"1F-04"},
    "living / landing (open zone)": {"1F-13"}, "living / corridor (open zone)": {"1F-13"},
    "1F living (open zone)": {"1F-13"}, "stair landing (shaft side)": {"ST-1F"},
    "1F stair hall": {"ST-1F"}, "1F stair hall (north)": {"ST-1F"},
    "laundry": {"1F-07"}, "W.C. 147 x 180": {"1F-08"}, "bath by the laundry 200 x 180": {"1F-09"},
    "1F master bed room 380 x 430": {"1F-10"}, "1F master bed room east (curved W17)": {"1F-11"},
    "1F master bed room east": {"1F-11"}, "bath east 210 x 225": {"1F-12"}, "1F bath east 210 x 225": {"1F-12"},
    "2F stair lobby": {"2F-01"}, "2F stair hall": {"ST-2F"}, "2F stair hall (north)": {"ST-2F"},
    "maid room 300 x 645": {"2F-03"}, "W.C. 300 x 185": {"2F-02"},
    "dressing passage": {NO}, "dressing passage of the 380 x 430 bed room": {NO},
}
UNWALKED = {"dressing passage", "dressing passage of the 380 x 430 bed room"}
OUTDOOR_WORDS = ("outside", "outdoors", "pool", "roof", "side passage")
# one space split only by a clip box (no wall): walk_r2.py GF0 parts, 1F / 2F open faces and their shaft boxes
OPEN_ZONES = [{"GF-07", "GF-08", "GF-14"}, {"1F-13", "ST-1F"}, {"2F-01", "ST-2F"}]
# T-128 opening classes -> inventory kind (doorway P-GF-01 and the lift landing doors are not in the T-249 inventory:
# no leaf / no drawn plan symbol of their own; named, not joined)
T128_KIND = {"door": "DOOR", "main": "DOOR", "arch": "OPENING", "window": "WINDOW"}
T128_NOT_INVENTORY = {"doorway", "lift"}


def claim(label):
    if label in LABELS:
        return LABELS[label], ("UNWALKED_SPACE" if label in UNWALKED else "")
    if any(w in label.lower() for w in OUTDOOR_WORDS):
        return {NO}, ""
    return None, "LABEL_NOT_READ"


def fmt_side(s):
    if s["state"] == "ESTABLISHED":
        return s["room"]
    return s["state"] + ":" + " ".join(f"{k}={v}" for k, v in sorted(s["shares"].items()))


def compute(cap):
    census = {r["ID"]: r for r in csv.DictReader(open(CENSUS, encoding="utf-8"))}
    rows, geo_by_id = [], {}
    for op in cap["openings"]:
        rooms = {k: v for k, v in cap["rooms"].items() if cap["room_floor"][k] == op["floor"]}
        g = J.join_opening(op, rooms)
        geo_by_id[op["id"]] = (op, g)
        c = census.get(op["id"], {})
        la, na = claim(c.get("SIDE_A", ""))
        lb, nb = claim(c.get("SIDE_B", ""))
        if la is None or lb is None:
            verdict = "LABEL_NOT_READ"
        else:
            verdict = J.label_verdict((la, lb), g, OPEN_ZONES)
        geo_rooms = sorted((g["A"]["rooms"] | g["B"]["rooms"]) - {NO})
        rows.append({
            "ID": op["id"], "KIND": op["kind"], "FLOOR": op["floor"], "HANDLES_T249": " ".join(op["handles"]),
            "PROBE_BASIS": op["basis"], "PROBE_LINE_M": op["line_m"], "STATIONS": len(op["stations"]),
            "SIDE_A_STATE": g["A"]["state"], "SIDE_A_GEO": fmt_side(g["A"]),
            "SIDE_B_STATE": g["B"]["state"], "SIDE_B_GEO": fmt_side(g["B"]), "ROOMS_GEO": " ".join(geo_rooms),
            "FLAGS": " ".join(g["flags"]), "DOOR_PAIR": J.door_pair_check(op["kind"], g),
            "CENSUS_SIDE_A": c.get("SIDE_A", ""), "CENSUS_SIDE_B": c.get("SIDE_B", ""),
            "LABEL_CLAIM": " | ".join(" ".join(sorted(x)) if x else "?" for x in (la, lb)),
            "LABEL_NOTE": " ".join(x for x in (na, nb) if x), "VERDICT": verdict})
    return rows, geo_by_id


def t128_check(geo_by_id):
    """per T-128 room: the inventory openings its table deducts (by kind) against the openings whose geometric sides
    include the room. Counts by kind; the widths are T-128's own (one walk, one width per door)."""
    t128 = {}
    for r in csv.DictReader(open(T128_OPS, encoding="utf-8")):
        k = T128_KIND.get(r["CLASS"])
        t128.setdefault(r["ROOM_ROW"], {"DOOR": 0, "OPENING": 0, "WINDOW": 0, "not_inventory": []})
        if k:
            t128[r["ROOM_ROW"]][k] += 1
        elif r["CLASS"] in T128_NOT_INVENTORY:
            t128[r["ROOM_ROW"]]["not_inventory"].append(r["OPENING"])
    geo = {}
    for oid, (op, g) in geo_by_id.items():
        k = "DOOR" if op["kind"] in ("DOOR", "GATE") else op["kind"]
        for rid in (g["A"]["rooms"] | g["B"]["rooms"]) - {NO}:
            geo.setdefault(rid, {"DOOR": [], "OPENING": [], "WINDOW": []})[k].append(oid)
    out = []
    for rid in sorted(set(t128) | set(geo)):
        t = t128.get(rid, {"DOOR": 0, "OPENING": 0, "WINDOW": 0, "not_inventory": []})
        gg = geo.get(rid, {"DOOR": [], "OPENING": [], "WINDOW": []})
        same = all(t[k] == len(gg[k]) for k in ("DOOR", "OPENING", "WINDOW"))
        out.append({"ROOM": rid, "T128_DOORS": t["DOOR"], "GEO_DOORS": " ".join(sorted(gg["DOOR"])),
                    "T128_ARCHES": t["OPENING"], "GEO_ARCHES": " ".join(sorted(gg["OPENING"])),
                    "T128_WINDOWS": t["WINDOW"], "GEO_WINDOWS": " ".join(sorted(gg["WINDOW"])),
                    "T128_NOT_IN_INVENTORY": "; ".join(t["not_inventory"]),
                    "RESULT": "AGREE" if same else "DIFFERS"})
    return out


def t237_check(geo_by_id):
    out = []
    for r in csv.DictReader(open(T237_X, encoding="utf-8")):
        cid = r["census_id"]
        if not cid:
            continue
        if cid not in geo_by_id:
            res, rooms = "NOT_IN_INVENTORY", ""
        else:
            _, g = geo_by_id[cid]
            gr = (g["A"]["rooms"] | g["B"]["rooms"]) - {NO}
            rooms = " ".join(sorted(gr))
            res = "AGREE" if r["room"] in gr else "JOIN_WRONG"
        out.append({"T237_ROOM": r["room"], "T128_OPENING": r["t128_opening"], "CENSUS_ID": cid,
                    "T237_MATCH_BASIS": r["match_basis"], "T237_HOST_WALL": r["host_wall"],
                    "GEO_ROOMS_OF_CENSUS_ID": rooms, "RESULT": res})
    return out


def t209_check(geo_by_id):
    """the T-209 wet-tile input names a census window id per room: is that window geometrically in the room?"""
    inp = json.load(open(T209_IN, encoding="utf-8"))
    out = []
    for r in inp["rooms"]:
        for w in r["windows"]:
            if w["id"] not in geo_by_id:
                continue
            _, g = geo_by_id[w["id"]]
            gr = (g["A"]["rooms"] | g["B"]["rooms"]) - {NO}
            out.append({"ROOM": r["id"], "WINDOW_ID": w["id"], "W": w["w"], "SILL": w.get("sill"),
                        "HEAD": w.get("head"), "GEO_ROOMS": " ".join(sorted(gr)),
                        "RESULT": "AGREE" if r["id"] in gr else "ID_IN_WRONG_ROOM"})
    return out


def overlaps(cap, geo_by_id):
    out = []
    for o in J.strip_overlaps(cap["rooms"], cap["strips"]):
        out.append({"ROOM": o["room"], "KIND": "WALL_STRIP", "HANDLES": " ".join(o["handles"]), "T_M": o["t_m"],
                    "OVERLAP_M2": o["overlap_m2"]})
    for oid, (op, g) in sorted(geo_by_id.items()):
        for f in g["flags"]:
            if f.startswith("REVEAL_IN_REGION:"):
                out.append({"ROOM": f.split(":", 1)[1], "KIND": "OPENING_REVEAL", "HANDLES": " ".join(op["handles"]),
                            "T_M": "", "OVERLAP_M2": "", "OPENING": oid})
    return out


def write_csv(rows, cols=None):
    cols = cols or list(rows[0].keys())
    f = io.StringIO()
    w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return f.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("capture")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    cap = pickle.load(open(a.capture, "rb"))
    rows, geo = compute(cap)
    t128 = t128_check(geo)
    t237 = t237_check(geo)
    t209 = t209_check(geo)
    ov = overlaps(cap, geo)
    count = lambda rs, k: {v: sum(1 for r in rs if r[k] == v) for v in sorted({r[k] for r in rs})}
    summary = {
        "task": "T-262", "drawing": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha ab54dd55)",
        "openings_joined": len(rows), "by_kind": count(rows, "KIND"),
        "side_states": {"A": count(rows, "SIDE_A_STATE"), "B": count(rows, "SIDE_B_STATE")},
        "multi_room_sides": [f"{r['ID']}:{r['SIDE_A_GEO'] if r['SIDE_A_STATE'] != 'ESTABLISHED' else r['SIDE_B_GEO']}"
                             for r in rows if "ESTABLISHED" not in (r["SIDE_A_STATE"], r["SIDE_B_STATE"])
                             or r["SIDE_A_STATE"] != r["SIDE_B_STATE"]],
        "flags": {r["ID"]: r["FLAGS"] for r in rows if r["FLAGS"]},
        "door_pair": count(rows, "DOOR_PAIR"), "census_label_verdicts": count(rows, "VERDICT"),
        "label_wrong": [r["ID"] for r in rows if r["VERDICT"] == "LABEL_WRONG"],
        "label_incomplete": [r["ID"] for r in rows if r["VERDICT"] == "LABEL_INCOMPLETE"],
        "agree_open_zone": [r["ID"] for r in rows if r["VERDICT"] == "AGREE_OPEN_ZONE"],
        "t128_rooms": count(t128, "RESULT"), "t128_differs": [r["ROOM"] for r in t128 if r["RESULT"] != "AGREE"],
        "t237_join": count(t237, "RESULT"),
        "t237_join_wrong": [f"{r['T237_ROOM']}:{r['CENSUS_ID']}" for r in t237 if r["RESULT"] == "JOIN_WRONG"],
        "t209_windows": count(t209, "RESULT"),
        "t209_wrong": [f"{r['ROOM']}:{r['WINDOW_ID']}" for r in t209 if r["RESULT"] != "AGREE"],
        "region_overlaps": [{k: r[k] for k in ("ROOM", "KIND", "HANDLES", "OVERLAP_M2")} for r in ov],
        "walked_area_m2": {k: cap["walked_area_m2"][k] for k in sorted({r["ROOM"] for r in ov})},
    }
    files = {"OPENING_ROOMS_T262.csv": write_csv(rows), "T128_ROOM_CHECK_T262.csv": write_csv(t128),
             "T237_JOIN_CHECK_T262.csv": write_csv(t237), "T209_WINDOW_CHECK_T262.csv": write_csv(t209),
             "REGION_OVERLAP_T262.csv": write_csv(ov, ["ROOM", "KIND", "HANDLES", "T_M", "OVERLAP_M2", "OPENING"]),
             "summary.json": json.dumps(summary, indent=1, sort_keys=True) + "\n"}
    if a.check:
        bad = [n for n, t in files.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("T-262 check:", "all outputs reproduce" if not bad else f"DIFFER: {bad}")
        return 1 if bad else 0
    for n, t in files.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("openings_joined", "side_states", "door_pair", "census_label_verdicts",
                                               "label_wrong", "label_incomplete", "t128_rooms", "t128_differs",
                                               "t237_join", "t237_join_wrong", "t209_windows", "t209_wrong")},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
