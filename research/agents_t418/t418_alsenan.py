"""T-418 on the development villa: the floor parts of the two stair-room faces that carry no floor-finish line in the
candidate of record ARCH_TAKEOFF_V3.0.35 (GF stair room GF-R31F8AE 12.475 m2, 2F stair hall 2F-R4D1B62 18.600 m2),
partitioned by STAIR_ROOM_FLOOR_V1 (R-T418-1). Research only; nothing is wired.

    python3 -I research/agents_t418/t418_alsenan.py <dir holding V3_0_35_BOQ_LINES.json> --write   # own run, writes
    python3 -I research/agents_t418/t418_alsenan.py --check                                       # committed closes

Geometry: room-LOCAL dimensions (origin = the room's south-west inner corner, north = +y), read on the architectural
DXF (Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip, sha256 ab54dd55, layers 1 / 2 / 5 / D / LEVEL /
S-COL.BON) and checked against the printed dimensions; no client coordinate, name or drawing content is committed.
GF stair room (2.500 x 5.000 inner, less the 0.050 x 0.500 column S-COL.BON proud of the west wall = 12.475):
  west lane 1.150, central divider 0.200 (layer 2, from y 0.450 to 3.850), east lane 1.150;
  MS1-L: 10 riser lines (layer 2) at 0.300 from y 1.150 to 3.850 (= T-111 '2.700 m first riser to the turn line');
  winders NW above y 3.850 (radial layer-2 lines); D1: 4 riser lines (layer 5) at y 2.950 / 3.250 / 3.550 / 3.850
  (T-111: 4 risers +0.30 -> +1.00, 3 treads, hall floor = 4th tread); level marks '+1.00' at (1.6, 1.3) and '+0.30'
  at (1.3, 4.3); doors in the south wall (0.950, from the open room) and the north wall (0.890, to the north court).
2F stair hall (T-129 MERGED ledger, printed 450 / 250 / 195 / 125, re-read this run on layers 1 / 2 / 5 / D):
  arrival 2.500 x 1.950 (marble, owner Q-70 A, condition met: T-129), floor beyond the stair width 2.000 x 1.250,
  east-lane foot strip 1.150 x 0.350 (inside flight row ST-MS2-U), slab opening over the flights (no floor),
  column 0.050 x 0.500 proud of the west wall at y 2.950 .. 3.450 (S-COL.BON).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stair_room_floor_v1 as SR  # noqa: E402

CANDIDATE = "ARCH_TAKEOFF_V3.0.35"
CANDIDATE_JSON_SHA256 = "b011bace2958f3da42afa00587eb2511afed754a46aba78e8d08346aa2903e10"  # T-400 summary_t400.json
TABLE = HERE / "SPACE_TABLE_T418.csv"
SUMMARY = HERE / "summary.json"
DRY_DEFAULT = "URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1 (no finish schedule on any sheet: T-091 / T-153)"
# the dry default never applies to STAIR (rules/methods/URBAN_METHOD_REGISTER_V3.json) and UP-STAIR-005 makes a landing
# marble; a floor at the foot of a flight with no printed landing depth is settled by neither (Q-70 A: 'if the geometry
# does not support this classification, keep it HELD'): its AREA is a floor-finish m2, its FINISH is HELD
FOOT_FINISH = ("HELD: porcelain (URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1 if a DRY_ROOM_FLOOR) or marble (UP-STAIR-005 if "
               "a landing); no printed landing depth, no finish schedule")
STAIR_ROOMS = {"GF-R31F8AE": "GF", "2F-R4D1B62": "2F"}


def R(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def gf_room():
    face = [(0, 0), (2.5, 0), (2.5, 5.0), (0, 5.0), (0, 2.0), (0.05, 2.0), (0.05, 1.5), (0, 1.5)]
    hall = [(0, 0), (2.5, 0), (2.5, 2.95), (1.35, 2.95), (1.35, 0.45), (1.15, 0.45), (1.15, 1.15), (0, 1.15)]
    treads = [(0, 1.15), (1.15, 1.15), (1.15, 3.85), (0, 3.85), (0, 2.0), (0.05, 2.0), (0.05, 1.5), (0, 1.5)]
    return {"id": "GF-R31F8AE", "storey_ffl": 1.00, "face": face, "parts": [
        {"id": "GF-ST-HALL", "kind": "FLOOR", "poly": hall, "level": 1.00, "level_src": "LEVEL '+1.00' inside (east lane)",
         "finish": FOOT_FINISH, "finish_rule": "UP-STAIR-005 / URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1 / Q-70 A",
         "finish_status": SR.STATUS_HELD,
         "note": "hall at the foot of MS1-L and the top of D1, from the south door (open room) to the D1 top riser; "
                 "the storey floor at +1.00; landing or floor is not settled (no printed landing depth)"},
        {"id": "GF-ST-LOBBY030", "kind": "FLOOR", "poly": R(1.35, 3.85, 2.5, 5.0), "level": 0.30,
         "level_src": "LEVEL '+0.30' inside (NE quarter, under the +3.50 half landing)",
         "finish": FOOT_FINISH, "finish_rule": "UP-STAIR-005 / URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1 / Q-70 A",
         "finish_status": SR.STATUS_HELD,
         "note": "back-door lobby at the foot of D1, inside the north wall (door to the north court +0.15)"},
        {"id": "GF-ST-MS1L", "kind": "B7", "poly": treads, "note": "MS1-L treads below the cut (T-111), less the column"},
        {"id": "GF-ST-WIND", "kind": "B7", "poly": R(0, 3.85, 1.15, 5.0), "note": "MS1-T winders NW quarter (T-111)"},
        {"id": "GF-ST-D1", "kind": "B7", "poly": R(1.35, 2.95, 2.5, 3.85), "note": "D1 3 treads 0.300 x 1.150 (T-111)"},
        {"id": "GF-ST-DIV", "kind": "SOLID", "poly": R(1.15, 0.45, 1.35, 3.85), "note": "central divider 0.200"},
        {"id": "GF-ST-CN", "kind": "UNREAD", "poly": R(1.15, 3.85, 1.35, 5.0),
         "note": "0.200 strip north of the divider end: two layer-2 lines (0.10 / 0.15 from the west edge) not read "
                 "as wall, balustrade or open floor; on the +0.30 lobby side or under the winders"}]}


def f2_room():
    face = [(0, 0), (4.5, 0), (4.5, 1.25), (2.5, 1.25), (2.5, 6.45), (0, 6.45), (0, 3.45), (0.05, 3.45),
            (0.05, 2.95), (0, 2.95)]
    opening = [(0, 1.95), (1.35, 1.95), (1.35, 2.3), (2.5, 2.3), (2.5, 6.45), (0, 6.45), (0, 3.45), (0.05, 3.45),
               (0.05, 2.95), (0, 2.95)]
    return {"id": "2F-R4D1B62", "storey_ffl": 9.70, "face": face, "parts": [
        {"id": "2F-ST-LOBBY", "kind": "FLOOR", "poly": R(2.5, 0, 4.5, 1.25), "level": 9.70,
         "level_src": "LEVEL '+9.70' in the lobby; printed 450 - 250 = 200 by 125 (T-129 LB-2F)",
         "finish": "PORCELAIN", "finish_rule": "owner Q-70 A ('candidate lobby porcelain') + " + DRY_DEFAULT,
         "finish_status": SR.STATUS_OWNER,
         "note": "floor beyond the stair width, between the arrival, the lift box and the maid-room door"},
        {"id": "2F-ST-ARRIVAL", "kind": "B7", "poly": R(0, 0, 2.5, 1.95),
         "note": "arrival 250 x 195 = 4.875 marble (owner Q-70 A, condition met: T-129 AL-2F)"},
        {"id": "2F-ST-FOOT", "kind": "B7", "poly": R(1.35, 1.95, 2.5, 2.3),
         "note": "east-lane foot strip 1.15 x 0.35 inside flight row ST-MS2-U (T-129 H-FS-2F, 0 m2 added)"},
        {"id": "2F-ST-OPEN", "kind": "VOID", "poly": opening, "note": "slab opening over the 1F-2F flights (T-129 O-2F)"}]}


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def candidate_binding(d):
    """read a candidate run: every line on the two stair rooms and the floor-finish codes. <d> holds
    V3_0_35_BOQ_LINES.json (the candidate of record, sha256 pinned) or is a V3.0.4 run directory (BOQ_LINES.json of
    research/agents_t167/v304_run.py on the same drawings: the stair-room lines come from the base floor stage,
    engine/source/arch_floor.py, and V3.0.5 .. V3.0.35 add no floor-finish line on a stair room: T-414 ROOM_TABLE on
    V3.0.34, T-400 identity V3.0.35 = V3.0.34 + 40 fence lines + 1 door line). Ids, codes, states, quantities only."""
    p = Path(d) / "V3_0_35_BOQ_LINES.json"
    if p.exists():
        h = sha256(p)
        if h != CANDIDATE_JSON_SHA256:
            raise SystemExit(f"stale candidate: {p.name} sha256 {h[:8]} is not V3.0.35 {CANDIDATE_JSON_SHA256[:8]}")
        source = {"run": CANDIDATE, "file": p.name, "sha256": h}
    else:
        p = Path(d) / "BOQ_LINES.json"
        h = sha256(p)
        source = {"run": "ARCH_TAKEOFF_V3.0.4 (own run, research/agents_t167/v304_run.py)", "file": "v304/BOQ_LINES.json",
                  "sha256": h, "later_versions": "no floor-finish line on a stair room through V3.0.34 (T-414 table, "
                  "json 4c7f581c); V3.0.35 = V3.0.34 + 40 EXT.FENCE / STR.CONC.BOUNDARY_PAD lines + 1 changed door "
                  "line (T-400 identity)"}
    raw = json.loads(p.read_text(encoding="utf-8"))
    lines = raw["lines"] if isinstance(raw, dict) else raw

    def loc(l):
        lo = l.get("location") or {}
        return lo.get("room_id") or (lo.get("element_id") or "").split(":")[0], lo.get("element_id"), lo.get("floor")

    on_rooms, floor_codes = {r: [] for r in STAIR_ROOMS}, {}
    for l in lines:
        rid, eid, fl = loc(l)
        code = l["item_code"]
        if code.startswith("FIN.FLOOR"):
            floor_codes.setdefault(code, 0)
            floor_codes[code] += 1
        txt = json.dumps(l, ensure_ascii=False)
        for r in STAIR_ROOMS:
            if rid == r or (eid or "").startswith(r) or r in txt:
                br = l.get("bounded_range") or {}
                on_rooms[r].append({"line_id": l["line_id"], "item_code": code, "unit": l.get("unit"),
                                    "state": l.get("evidence_state"), "net": l.get("measured_net"),
                                    "bound_high": br.get("high") if isinstance(br, dict) else None})
    return {"source": source, "lines": len(lines), "floor_line_codes": floor_codes, "lines_on_stair_rooms": on_rooms,
            "floor_finish_lines_on_stair_rooms": {r: [x["line_id"] for x in v if x["item_code"].startswith("FIN.FLOOR")]
                                                  for r, v in on_rooms.items()}}


def build():
    return [SR.partition(gf_room()), SR.partition(f2_room())]


COLS = ["room", "part", "kind", "family", "area_m2", "level", "status", "held_low", "held_high", "finish",
        "finish_status", "candidate_line", "census", "level_src", "note"]


def table_csv(results, census):
    st = {(c["room"], c["part"]): c for c in census}
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(COLS)
    for res in results:
        for r in res["rows"]:
            c = st.get((r["room"], r["part"]), {})
            b = r["bound"] or [None, None]
            w.writerow([r["room"], r["part"], r["kind"], r["family"] or "", f"{r['area_m2']:.4f}",
                        "" if r["level"] is None or r["kind"] != "FLOOR" else f"{r['level']:+.2f}", r["status"],
                        "" if b[0] is None else f"{b[0]:.4f}", "" if b[1] is None else f"{b[1]:.4f}",
                        r["finish"] or "", r.get("finish_status") or "", c.get("line") or "", c.get("state", ""),
                        r["level_src"], r["note"]])
    return s.getvalue()


# freelancer dry floor rows (FIN workbook, sheet 'سيراميك', tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json) against
# the V3.0.35 dry floor-finish lines as T-414 tabulated them (ROOM_TABLE_T414: the same lines in V3.0.34 and V3.0.35,
# T-400 changed no floor line); quantities only. Each component carries its class (TRACED / HELD / UNEXPLAINED).
FREELANCER_DRY = 337.57
CANDIDATE_DRY = 288.1458


def freelancer_restated(floor_add):
    gf_add = floor_add["GF"]
    f2_add = floor_add["2F"]
    comps = [
        ("GF open room: pantry floored wet (owner Q-37 A)", -13.4549, "TRACED", "RULE_DIFFERENCE"),
        ("GF open room: round-stair treads below the cut (stairs B7, UP-STAIR-005)", -6.1244, "TRACED", "RULE_DIFFERENCE"),
        ("GF open room: garden band inside the reception (designer D-48)", -13.986, "HELD", "UNRESOLVED"),
        ("GF stair room floor parts (this task; area DRAWING-CONFIRMED, finish HELD)", round(gf_add, 4),
         "TRACED", "UNRESOLVED (no freelancer floor row; his main-stair landing marble row 6.20 m2 has no breakdown and "
         "may hold the foot hall: a match by figure is refused)"),
        ("GF open room residual (open-room boundary vs his reception + dining + entrance)", -2.5463, "UNEXPLAINED",
         "UNRESOLVED"),
        ("GF master / dewaneya / driver", -0.0051, "TRACED", "T-086 verdicts"),
        ("GF doorway strips valued in the candidate", 0.35, "TRACED", "engine-only strips"),
        ("1F living: arrival landing marble (owner Q-66 B) + T-345 trace", -5.249, "TRACED", "RULE_DIFFERENCE (T-345 / T-086)"),
        ("1F bed rooms (two UNRESOLVED since T-086 / T-153)", -1.3785, "TRACED", "T-086 verdicts"),
        ("1F doorway strips valued in the candidate", 0.72, "TRACED", "engine-only strips"),
        ("2F maid room", -0.23, "TRACED", "T-086 verdict"),
        ("2F corridor: arrival 4.875 marble (owner Q-70 A, stairs B7)", -4.875, "TRACED", "RULE_DIFFERENCE"),
        ("2F corridor residual against his 7.70 (his row has no dimensions)", round(-7.70 + 4.875 + f2_add, 4),
         "UNEXPLAINED", "UNRESOLVED"),
        ("2F doorway strip valued in the candidate", 0.18, "TRACED", "engine-only strip"),
    ]
    engine = round(CANDIDATE_DRY + gf_add + f2_add, 4)
    diff = round(engine - FREELANCER_DRY, 4)
    total = round(sum(c[1] for c in comps), 4)
    if abs(total - diff) > 1e-4:
        raise SystemExit(f"freelancer components {total} do not close on the difference {diff}")
    return {"freelancer_dry_m2": FREELANCER_DRY, "candidate_dry_m2": CANDIDATE_DRY,
            "with_t418_m2": engine, "diff_m2": diff, "diff_pct": round(100 * diff / FREELANCER_DRY, 2),
            "was_diff_m2": round(CANDIDATE_DRY - FREELANCER_DRY, 4),
            "components": [{"component": c[0], "m2": c[1], "class": c[2], "verdict": c[3]} for c in comps],
            "components_sum_m2": total,
            "by_class": {k: round(sum(c[1] for c in comps if c[2] == k), 4) for k in ("TRACED", "HELD", "UNEXPLAINED")}}


def summarize(results, binding=None):
    lines = {}
    census = SR.census(results, lines)
    floor_add = {"GF": results[0]["floor_m2"], "2F": results[1]["floor_m2"]}
    out = {"method": SR.METHOD, "rule": SR.RULE, "candidate": CANDIDATE, "candidate_json_sha256": CANDIDATE_JSON_SHA256,
           "rooms": [{k: res[k] for k in ("room", "face_m2", "closure_m2", "floor_m2", "held_bound")} for res in results],
           "floor_parts_m2": round(sum(floor_add.values()), 4),
           "census": census,
           "b7_m2": round(sum(r["area_m2"] for res in results for r in res["rows"] if r["kind"] == "B7"), 4),
           "freelancer_dry": freelancer_restated(floor_add)}
    if binding is not None:
        out["candidate_binding"] = binding
        # ONE m2 ONE LINE: a landing-marble line whose upper bound is 'enclosure - drawn treads' holds the floor parts
        # inside that bound; when the floor line is integrated the bound loses them (bound only, never a figure)
        ov = []
        for res in results:
            for x in binding["lines_on_stair_rooms"].get(res["room"], []):
                if x["item_code"] == "FIN.MARBLE.LANDING" and x.get("bound_high") is not None:
                    ov.append({"room": res["room"], "line_id": x["line_id"], "bound_high_m2": x["bound_high"],
                               "floor_parts_inside_m2": res["floor_m2"],
                               "bound_high_after_m2": round(x["bound_high"] - res["floor_m2"], 4)})
        out["landing_bound_overlap"] = ov
    return out, census


def main(argv):
    results = build()
    if "--check" in argv:
        s = json.loads(SUMMARY.read_text(encoding="utf-8"))
        new, census = summarize(results, s.get("candidate_binding"))
        assert new == s, "summary.json does not reproduce from the module"
        assert TABLE.read_text(encoding="utf-8") == table_csv(results, census), "table does not reproduce"
        print("check OK")
        return 0
    binding = candidate_binding(argv[0]) if argv and not argv[0].startswith("--") else None
    s, census = summarize(results, binding)
    print(json.dumps(s, indent=1, ensure_ascii=False))
    if "--write" in argv:
        SUMMARY.write_text(json.dumps(s, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        TABLE.write_text(table_csv(results, census), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
