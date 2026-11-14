"""T-795 F-27 fix rows on ARCH_TAKEOFF_V3.0.86: the four HELD ranges of Tiles / Openings / Other to points (worker 2).

    bash scripts/agent_env.sh run --tree task-T-795 research/agents_t781/geometry_t781.py <P7757.dxf> --out <priv>/geo
    bash scripts/agent_env.sh run --tree task-T-795 research/agents_t795/fill_t795.py --geo <priv>/geo --write
    bash scripts/agent_env.sh run --tree task-T-795 research/agents_t795/fill_t795.py            # rebuild from the CSV

Door faces: every door / doorway / arch on a tiled face of the merged T-312 opening ledger (OPENINGS_T312.csv, one row
per room side, engine room from FACE_LEDGER_T312.csv) bound to the merged T-781 opening table (OPENING_TABLE_V1 on
the V2.13 plan read: same floor, the opening's rooms include the engine room, same width +-0.01). A door the V2.13 reader
does not detect (T-781 'closure-only doors') keeps its T-312 measured face width and the 2.20 company head. The binding
is written to DOOR_FACES_T795.csv (engine ids and sizes only; no coordinates, no names) and the rows are rebuilt from it.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t795_rules as R  # noqa: E402

IDX = RES / "agents_t770/out/LINE_INDEX_V3_0_86.json"
T312 = RES / "agents_t312"
T781 = RES / "agents_t781/out/OPENING_TABLE_ALSENAN.json"
FACES = HERE / "DOOR_FACES_T795.csv"
COLS = ["room", "engine_room", "opening", "kind", "t781_id", "W", "W_label", "H", "H_label", "tile_line_state"]
JAMB_LINE = "L-41b2f150f7779382b976"
CN_LINE = "L-a788de4672b1f0d2e6c1"
SPACE_LINES = {  # ARCH.SPACE register lines (room-area record, not a finish line): the area was never in doubt
    "L-554a525edce9a9235bee": ("GF-OP-003 band: the 6.82 x 0.20 strip inside the south facade held with the garden band "
                               "(T-343 cross-check P-2; V3.0.14 FLOOR_SCOPE HELD_WITH); its finish stays with that band"),
    "L-6485382cd3b6f09c192c": ("GF open-room floor under the flights drawn below the cut (V3.0.14 FLOOR_SCOPE "
                               "UNDER_STAIR_HELD); the floor finish under it stays its own designer item")}


def _lines():
    return {l["line_id"]: l for l in json.load(open(IDX))["lines"]}


def bind(geo):
    eng = {}
    for r in csv.DictReader(open(T312 / "FACE_LEDGER_T312.csv")):
        if r["engine_room"]:
            eng.setdefault(r["room"], r["engine_room"])
    ops = {(o["floor"], o["opening_id"]): o for o in json.load(open(pathlib.Path(geo) / "ARCH_OPENINGS.json"))["openings"]}
    tab = {r["id"]: r for r in json.load(open(T781))["rows"]}
    tiles = {l["element_id"].split(":")[0].split("#")[0]: l for l in _lines().values() if l["item_code"] == "FIN.WALL.TILE"}
    out = []
    t312 = [r for r in csv.DictReader(open(T312 / "OPENINGS_T312.csv")) if r["kind"] in ("door", "doorway", "arch")]
    for r in t312:
        er = eng[r["room"]]
        fl = r["room"][:2]
        w = float(r["merged_size"].split()[1])
        hit = [k for k, o in ops.items() if k[0] == fl and er in (o.get("rooms") or [])
               and o["kind"] in ("DOOR", "PASSAGE") and abs((o.get("width_m") or 0) - w) <= 0.01]
        if len(hit) > 1:   # two equal doors in one room: the room on the far side (same door id in T-312) decides
            other = {eng[x["room"]] for x in t312 if x["opening_id"] == r["opening_id"] and x["room"] != r["room"]}
            hit = [k for k in hit if other & set(ops[k].get("rooms") or [])]
        if len(hit) > 1:
            raise SystemExit(f"{r['room']} {r['opening_id']}: {len(hit)} table rows bind")
        if hit:
            t = tab[f"{fl}:{hit[0][1]}"]
            row = [r["room"], er, r["opening_id"], r["kind"], t["id"], t["W"], t["W_label"], t["H"], t["H_label"]]
        else:
            row = [r["room"], er, r["opening_id"], r["kind"], "", w, "MEASURED (T-128 r3 door face, T-312)",
                   R.DEFAULT_DOOR_HEAD_M, "DEFAULT (Q-55 C)"]
        out.append(row + [tiles[er]["class"]])
    with open(FACES, "w", newline="") as f:
        wr = csv.writer(f, lineterminator="\n")
        wr.writerow(COLS)
        wr.writerows(out)


def build():
    faces = [dict(r, W=float(r["W"]), H=float(r["H"])) for r in csv.DictReader(open(FACES))]
    lines = _lines()
    tot, jambs, heads = R.faces_total(faces)
    per = {}
    for f in faces:
        per.setdefault(f["room"], 0.0)
        per[f["room"]] += R.door_edge_lm(f["W"], f["H"], R.WET_TILE_TOP_M)[0]
    released_rooms = sum(R.door_edge_lm(f["W"], f["H"], R.WET_TILE_TOP_M)[0] for f in faces
                         if f["tile_line_state"] == "RELEASED")
    j = lines[JAMB_LINE]
    assert (j["class"], j["held_low"], j["held_high"]) == ("HELD", 0.0, 73.1), "jamb line moved: re-base"
    rows = [{
        "line_id": JAMB_LINE, "item_code": "FIN.WALL.TILE.EDGE", "unit": "lm", "element_id": j["element_id"],
        "before": {"class": "HELD", "low": 0.0, "high": 73.1, "label": "ESTIMATE"},
        "after": {"class": "RELEASED", "net": tot}, "label": "DEFAULT",
        "basis": (f"R-T795-1: {len(faces)} tiled door faces (T-312 opening ledger, bound to OPENING_TABLE_V1 where the "
                  f"plan reader detects the door) x (2 x min(H, 3.00) + W): jambs {jambs} + heads {heads} = {tot} lm; "
                  f"W MEASURED, H 2.20 DEFAULT (Q-55 C, no door head printed); tile top 3.00 (owner 13 Nov); doors "
                  f"between two tiled rooms counted on both faces; rooms with a RELEASED wall-tile line "
                  f"{round(released_rooms, 2)}, rooms whose wall-tile area is still HELD (annex / level) "
                  f"{round(tot - released_rooms, 2)}; arch A-GF-01 head on its 1.00 chord (crown not printed); edge form (frame cover / 45-degree / profile) = designer item"),
        "per_room_lm": {k: round(v, 4) for k, v in sorted(per.items())},
    }]
    c = lines[CN_LINE]
    assert (c["class"], c["held_low"], c["held_high"]) == ("HELD", 0.0, 0.23), "stair-corner line moved: re-base"
    rows.append({
        "line_id": CN_LINE, "item_code": "FIN.FLOOR.FINISH_HELD", "unit": "m2", "element_id": c["element_id"],
        "before": {"class": "HELD", "low": 0.0, "high": 0.23},
        "after": {"class": "RELEASED", "net": R.range_to_point(0.0, 0.23, cut_plane_clear=True)}, "label": "DRAWING-READ",
        "basis": ("R-T795-2: stair-room strip 0.200 x 1.150 = 0.230 m2 (T-418 GF-ST-CN, room-local x 1.15 .. 1.35, "
                  "y 3.85 .. 5.00) re-read on the arch DXF this run: at the cut plane nothing crosses or bounds it on "
                  "layers 1 / 5 / S-COL.BON (only HIDDEN layer-2 lines 2C6 / 49C / 49D at 0.10 / 0.15 from its west "
                  "edge = the winder edge / balustrade ABOVE, and the winder radials meeting at its SW corner); the "
                  "D1 bottom riser 481 and the divider end 4A6 stop at y 3.85; the north wall 26E closes it at y 5.00; "
                  "the '+0.30' LEVEL mark is in the same open area: floor of the +0.30 back-door lobby, finish as "
                  "GF-ST-LOBBY030 (porcelain / marble choice stays HELD by finish, not by area)"),
    })
    for lid, what in SPACE_LINES.items():
        s = lines[lid]
        assert s["class"] == "HELD" and s["held_low"] == s["held_high"], f"{lid} moved: re-base"
        rows.append({
            "line_id": lid, "item_code": "ARCH.SPACE", "unit": "m2", "element_id": s["element_id"],
            "before": {"class": "HELD", "low": s["held_low"], "high": s["held_high"]},
            "after": {"class": "RELEASED", "net": R.range_to_point(s["held_low"], s["held_high"], False)},
            "label": "MEASURED",
            "basis": f"R-T795-2: {what}; plan polygon area, low = high = {s['held_high']} m2 (a range of zero width)",
        })
    out = {
        "schema": "URBAN_FIX_ROWS_V1", "task": "T-795", "candidate_version": "ARCH_TAKEOFF_V3.0.86",
        "rule": "R-T795-1 .. 2 (research/agents_t795/t795_rules.py, every villa)",
        "inputs": {"index": "LINE_INDEX_V3_0_86.json", "door_faces": "research/agents_t795/DOOR_FACES_T795.csv",
                   "t312": "research/agents_t312/OPENINGS_T312.csv + FACE_LEDGER_T312.csv (merged)",
                   "t781": "research/agents_t781/out/OPENING_TABLE_ALSENAN.json (merged OPENING_TABLE_V1)",
                   "drawings": "Drive 'Alsenan chalet project' P7757_DXF_COMPRESSED.zip (V2.13 plan read, own run)"},
        "summary": {
            "held_ranges_before": 4, "held_ranges_after": 0,
            "door_faces": len(faces), "bound_to_opening_table": sum(1 for f in faces if f["t781_id"]),
            "jamb_edge_lm": tot, "jambs_lm": jambs, "heads_lm": heads,
            "jamb_edge_lm_old_range": [0.0, 73.1],
            "old_range_high_restated": "73.1 = the 14 faces of the 12 rooms with a determinate band in T-368 (14 x 4.40 "
                                       "+ heads 11.50); the 8 annex / level faces were HELD by band height, which the "
                                       "owner's 3.00 tile top now settles (door head 2.20 < 3.00)",
            "freelancer": "B4-10 tile edges: no row in his finishes workbook (T-368: 0 rows) -> RULE_DIFFERENCE (scope)",
            "hand_check_largest_door": "1.00 x 2.20 door / arch on one tiled face: 2 x 2.20 + 1.00 = 5.40 lm "
                                       "(GF-06 kitchen D-GF-05, GF-07 pantry D-GF-06, GF-02 arch A-GF-01)",
        },
        "rows": rows,
    }
    (HERE / "out").mkdir(exist_ok=True)
    (HERE / "out/FIX_ROWS.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    md = ["# T-795 fix rows on ARCH_TAKEOFF_V3.0.86 (unwired)", "",
          "| line | item | unit | before | after | label |", "|---|---|---|---|---|---|"]
    for r in rows:
        b = r["before"]
        md.append(f"| {r['line_id']} | {r['item_code']} | {r['unit']} | HELD {b['low']} .. {b['high']} | "
                  f"{r['after']['net']} | {r['label']} |")
    md += ["", "Door faces (R-T795-1, 2 x min(H, 3.00) + W):", "",
           "| room | opening | kind | table row | W | H | lm |", "|---|---|---|---|---|---|---|"]
    for f in faces:
        md.append(f"| {f['room']} | {f['opening']} | {f['kind']} | {f['t781_id'] or '-'} | {f['W']} | {f['H']} | "
                  f"{R.door_edge_lm(f['W'], f['H'], R.WET_TILE_TOP_M)[0]} |")
    md.append(f"| total | {len(faces)} faces | | | heads {heads} | jambs {jambs} | **{tot}** |")
    (HERE / "out/FIX_ROWS.md").write_text("\n".join(md) + "\n")
    print(json.dumps(out["summary"], indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    if a.write:
        bind(a.geo)
    build()


if __name__ == "__main__":
    main()
