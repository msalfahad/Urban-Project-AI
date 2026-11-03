"""T-490 training-villa census (B3-03 entrance / stair-hall stone floor) with STONE_FLOOR_CENSUS_V1.

Inputs are areas with their source: printed dimensions re-read this run on the GF / 1F plan sheets (Drive folder
"Alsenan chalet project", p7757_arch_sheet03.pdf and p7757_arch_sheet04.pdf), the merged research pieces that measured
them (cited per row) and the candidate line ids of ARCH_TAKEOFF_V3.0.46 (research/agents_t485/out/LINE_INDEX_V3_0_46.json).
No drawing content is copied: only areas, line ids and printed dimension values already used in merged research.

python3 -I t490_alsenan.py            -> prints the census
python3 -I t490_alsenan.py --write D  -> writes CENSUS_T490.csv and summary.json into folder D
python3 -I t490_alsenan.py --check    -> compares with the committed summary.json (exit 1 on any difference)
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import stone_floor_census_v1 as C  # noqa: E402

NO_TEXT = ("architectural DXF text census this run: 276 texts, room labels DINING / RECEPTION / SALOON / PANTRY / ..., "
           "no ENTRANCE / HALL / LOBBY word, no finish word (marble, granite, stone, porcelain, ceramic, tile, floor "
           "finish) in English; the Arabic labels on the plan sheets are room names; no finish schedule or legend "
           "on any sheet (T-091, T-153, T-471 F-4)")
PORCELAIN_DEFAULT = {"kind": "DEFAULT_RULE", "material": "PORCELAIN", "rule": "URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1"}
STAIR_MARBLE = {"kind": "OWNER_RULE", "material": "MARBLE", "rule": "UP-STAIR-001 / UP-STAIR-005 (OWNER-APPROVED)"}


def spaces():
    return [
        {"id": "GF-OPEN-ROOM-ENTRANCE-ZONE", "floor": "GF", "element": "ROOM_FLOOR",
         "name": "entrance zone inside the main door D-GF-07 (open room: dining / reception / saloon)",
         "area_m2": 109.478417, "area_source": "V3.0.46 porcelain net of GF-RC99C2A (T-246 / T-427); the entrance zone "
         "has no drawn edge of its own (sheet03: the D200 double door opens straight into DINING)",
         "material_evidence": [PORCELAIN_DEFAULT],
         "carriers": [{"line_id": "L-7625f35c503d9f8e6196", "family": "B3-01", "material": "PORCELAIN",
                       "area_m2": 109.478417}],
         "evidence": NO_TEXT},
        {"id": "GF-E1-LANDING", "floor": "GF", "element": "STAIR_LANDING",
         "name": "entrance landing outside the main door, top of the entrance flight E1",
         "area_m2": 1.40 * 3.70, "area_source": "printed 140 x 370 (sheet03, re-read this run); drawn 5.1794 (T-343)",
         "material_evidence": [{"kind": "OWNER_RULE", "material": "MARBLE",
                                "rule": "OWNER_RULE_OUTDOOR_FLOORS (outside stairs marble) + UP-STAIR-005"}],
         "openings": [{"id": "OP-021 (D-GF-07)", "width": 2.00, "depth": 0.20}],
         "carriers": [{"line_id": "L-3dd82a576dce1beb4250", "family": "B7", "material": "MARBLE", "area_m2": 5.1794}],
         "evidence": "freelancer 'entrance marble' landing row 5.10 vs 5.1794 (T-343: ENGINE_RIGHT, printed 1.40 x 3.70)"},
        {"id": "GF-E1-TREADS", "floor": "GF", "element": "TREADS", "name": "entrance flight E1, 4 treads",
         "area_m2": 4 * 0.30 * 2.80, "area_source": "printed 280, 4 treads 0.30 (sheet03; T-111 / T-343)",
         "material_evidence": [{"kind": "OWNER_RULE", "material": "MARBLE", "rule": "OWNER_RULE_OUTDOOR_FLOORS"}],
         "carriers": [{"line_id": "L-314c3ac6d45431b687c5", "family": "B7", "material": "MARBLE", "area_m2": 3.3594}],
         "evidence": "freelancer 'entrance marble' step rows (T-471 F-4: steps + one landing = E1)"},
        {"id": "GF-THRESHOLD-D-GF-07", "floor": "GF", "element": "THRESHOLD",
         "name": "main entrance door threshold (OP-021, 2.00 in a 0.20 wall)",
         "area_m2": 2.00 * 0.20, "area_source": "printed 200 door, wall 20 (sheet03; T-175 D-GF-07)",
         "material_evidence": [],
         "carriers": [{"line_id": "L-ad41b065d825c0190b7d", "family": "B3-04", "held": [0.40, 0.40]}],
         "evidence": "ARCH.THRESHOLD HELD 0.40 (material not printed); porcelain doorway strip L-e6e75fa6 EXCLUDED"},
        {"id": "GF-ST-HALL", "floor": "GF", "element": "FLOOR_OR_LANDING",
         "name": "GF stair room hall at +1.00: foot of MS1-L, top of D1",
         "area_m2": 2.50 * 0.45 + 1.15 * 0.70 + 1.15 * 2.50,
         "area_source": "T-418 parts in the printed 250 x 500 stair room (sheet03, re-read this run)",
         "material_evidence": [PORCELAIN_DEFAULT,
                               {"kind": "OWNER_RULE", "material": "MARBLE", "condition_met": False,
                                "rule": "Q-70 A / Q-66 B: stair width x PRINTED landing depth; no depth printed here"}],
         "openings": [{"id": "OP-010", "width": 1.00, "depth": 0.20}],
         "carriers": [{"line_id": "L-f53d498668da3dc7c228", "family": "HELD", "material": None, "area_m2": 4.805}],
         "evidence": "FIN.FLOOR.FINISH_HELD (area released, material HELD); doorway strip OP-010 porcelain L-a3bbe40a 0.20"},
        {"id": "GF-ST-LOBBY030", "floor": "GF", "element": "FLOOR_OR_LANDING",
         "name": "GF back-door lobby at +0.30 under the +3.50 half landing, foot of D1",
         "area_m2": 1.15 * 1.15, "area_source": "T-418 (sheet03)",
         "material_evidence": [PORCELAIN_DEFAULT,
                               {"kind": "OWNER_RULE", "material": "MARBLE", "condition_met": False,
                                "rule": "Q-70 A / Q-66 B: no printed landing depth"}],
         "openings": [{"id": "OP-013", "width": 0.90, "depth": 0.20}],
         "carriers": [{"line_id": "L-b4441a1b55eda53d98ea", "family": "HELD", "material": None, "area_m2": 1.3225}],
         "evidence": "FIN.FLOOR.FINISH_HELD; threshold OP-013 ARCH.THRESHOLD HELD 0.18 (L-8111095f)"},
        {"id": "GF-ST-CN", "floor": "GF", "element": "UNREAD", "name": "0.20 strip north of the divider end",
         "material_evidence": [],
         "carriers": [{"line_id": "L-a788de4672b1f0d2e6c1", "family": "HELD", "held": [0.0, 0.23]}],
         "evidence": "two unread layer-2 lines (T-418): HELD 0 .. 0.2300, never 0"},
        {"id": "GF-ST-LANDINGS", "floor": "GF", "element": "STAIR_LANDING",
         "name": "GF stair room landings bound (winders / half landing in the face)", "material_evidence": [STAIR_MARBLE],
         "carriers": [{"line_id": "L-1983e89d8b619eade1db", "family": "B7", "held": [0.0, 2.9225]}],
         "evidence": "FIN.MARBLE.LANDING HELD 0 .. 2.9225 (T-421)"},
        {"id": "1F-MAIN-ARRIVAL", "floor": "1F", "element": "STAIR_ARRIVAL",
         "name": "1F main-stair arrival landing at +5.50", "area_m2": 2.50 * 1.95,
         "area_source": "printed 250 x 195 (sheet04, re-read this run)",
         "material_evidence": [{"kind": "OWNER_RULE", "material": "MARBLE", "rule": "Q-66 B"}],
         "carriers": [{"line_id": "L-8011889d84788553a6b1", "family": "B7", "material": "MARBLE", "area_m2": 4.9225}],
         "evidence": "drawn 4.9225 = 4.875 - well end 0.010 + nosing band 0.0575 (T-240 / T-269); porcelain L-b06400d4 "
                     "33.411036 already excludes it"},
        {"id": "1F-ROUND-QUARTER-LANDING", "floor": "1F", "element": "STAIR_LANDING",
         "name": "round-stair quarter landing inside the 1F living", "area_m2": 1.352454,
         "area_source": "T-345 piece R04 (drawn; size not printed)", "material_evidence": [STAIR_MARBLE],
         "carriers": [],
         "evidence": "deducted from 1F porcelain (T-345 R04); no released or held B7 line in V3.0.46 names it"},
        {"id": "1F-LIVING", "floor": "1F", "element": "ROOM_FLOOR", "name": "1F living (open stair hall)",
         "area_m2": 33.411036, "area_source": "V3.0.46 porcelain net L-b06400d4 (T-421)",
         "material_evidence": [PORCELAIN_DEFAULT],
         "carriers": [{"line_id": "L-b06400d46d252f242018", "family": "B3-01", "material": "PORCELAIN", "area_m2": 33.411036}],
         "evidence": NO_TEXT},
        {"id": "2F-ST-ARRIVAL", "floor": "2F", "element": "STAIR_ARRIVAL", "name": "2F main-stair arrival at +9.70",
         "area_m2": 2.50 * 1.95, "area_source": "printed 250 x 195 (T-129 AL-2F, T-418)",
         "material_evidence": [{"kind": "OWNER_RULE", "material": "MARBLE", "condition_met": True,
                                "rule": "Q-70 A (condition met: T-129)"}],
         "carriers": [{"line_id": "L-5d2be30dd8d2ffeacc42", "family": "B7", "held": [0.0, 9.225001]}],
         "evidence": "only inside the HELD landings bound 0 .. 9.225 of 2F-R4D1B62: no released B7-04 line of its own"},
        {"id": "2F-ST-LOBBY", "floor": "2F", "element": "ROOM_FLOOR", "name": "2F lobby beyond the stair width",
         "area_m2": (4.50 - 2.50) * 1.25, "area_source": "printed (450 - 250) x 125 (T-129 LB-2F, T-418)",
         "fixed": [{"id": "lift threshold ELV-01-2F (B6-07)", "area_m2": 0.30, "area_source": "T-421 (2.500 - 0.300)"}],
         "material_evidence": [{"kind": "OWNER_RULE", "material": "PORCELAIN", "rule": "Q-70 A (candidate lobby porcelain)"}],
         "openings": [{"id": "OP-001", "width": 1.00, "depth": 0.15}, {"id": "OP-007", "width": 0.90, "depth": 0.20}],
         "carriers": [{"line_id": "L-9bd25c0cec9da3a8f4d2", "family": "B3-01", "material": "PORCELAIN", "area_m2": 2.20}],
         "evidence": "threshold OP-001 HELD 0.15 (L-3e5c6b7a); OP-007 doorway strip porcelain 0.18 (L-dc543495)"},
    ]


def run():
    return C.census(spaces())


FIELDS = ["id", "floor", "element", "name", "area_m2", "area_basis", "fixed_m2", "material", "material_basis",
          "family", "candidate_families", "status", "b3_03_new_m2", "b3_03_move_m2", "b3_03_held",
          "carried_released_m2", "carried_held_high_m2", "carrier_minus_measure_m2", "line_state", "carriers", "thresholds",
          "owner_trade", "material_note", "evidence"]


def write(folder):
    out = run()
    folder = Path(folder)
    with open(folder / "CENSUS_T490.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in out["rows"]:
            w.writerow({k: (json.dumps(r[k]) if isinstance(r[k], (list, dict)) else r[k]) for k in FIELDS})
    (folder / "summary.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--write":
        print(json.dumps(write(sys.argv[2])["totals"], indent=1))
    elif len(sys.argv) > 1 and sys.argv[1] == "--check":
        ok = json.loads((HERE / "summary.json").read_text(encoding="utf-8")) == json.loads(json.dumps(run()))
        print("T-490 census reproduces summary.json:", ok)
        sys.exit(0 if ok else 1)
    else:
        o = run()
        for r in o["rows"]:
            print(r["id"], r["status"], r["family"], r["area_m2"], r["carried_released_m2"], r["carrier_minus_measure_m2"], r["line_state"])
        print(json.dumps(o["totals"], indent=1))
