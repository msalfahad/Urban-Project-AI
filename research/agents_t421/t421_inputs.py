"""T-421: the URBAN_V3038_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.38 (engine.source.arch_v3038), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build). Every figure and id is READ from those
files; nothing is typed here except the column names, the register rulings' wiring choices and the line ids that the
merged tables print.

  research/agents_t418/SPACE_TABLE_T418.csv + summary.json   T-418 (MERGED 361f6e47, Verifier 2026-11-01T05:41Z Gate A
      PASS on e5116bbc): stair-room parts (FLOOR rows -> B3-01 lines, the UNREAD row -> a HELD bound line), the
      landing-bound overlap (the FIN.MARBLE.LANDING bounds shrink by the parts inside them; Checker condition);
  research/agents_t413/STATION_TABLE_T413.csv + summary.json   T-413 (MERGED ae87deb1, Verifier 2026-11-01T07:57Z Gate A
      PASS on 62faa889): per lift landing door the clear width (drawn), the threshold m2 (depth = m2 / width, UP-ELEV-005),
      the floor-overlap range (wall band = depth - overlap low / width), the surround bound, the band / floor lines;
  research/agents_t414/floor_bed_v1.py + ROOM_TABLE_T414.csv   T-414 (MERGED 4f81eda1): the owner Q-45 bed ranges and the
      build-up b of each storey's DRY zone (the stair hall +1.00 and the 2F lobby +9.70 sit at their storey's FFL; the
      GF back lobby +0.30 is a sub-level with no printed structural top: no b);
  Checker F-C-T414-1 (b upper 0.051 for 1F-DRY, the T-420 inputs).

Wiring choices from the register (ELEMENT_REGISTER 2026-11-01 08:15): LIFT LANDING THRESHOLD (band listed without a
quantity; landing floor deducts the footprint), STAIR-ROOM FLOOR PART vs LANDING BOUND, ROOM WITH NO FLOOR-FINISH LINE.
The 2F lift threshold lands on the NEW 2F lobby line (T-413 s.7.4: 'the 2F lobby ... is the face it lands on at 2F').

    python3 -I research/agents_t421/t421_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

T418_TABLE = ROOT / "research/agents_t418/SPACE_TABLE_T418.csv"
T418_SUM = ROOT / "research/agents_t418/summary.json"
T413_TABLE = ROOT / "research/agents_t413/STATION_TABLE_T413.csv"
T413_SUM = ROOT / "research/agents_t413/summary.json"
T414_TABLE = ROOT / "research/agents_t414/ROOM_TABLE_T414.csv"
FBV1 = ROOT / "research/agents_t414/floor_bed_v1.py"
PINS = {T418_TABLE: "627f4ecec21f086b8ff7997763f8f862e511f69326fdae2de7c79fd8c519444d",
        T418_SUM: "72fa6b5cc15a73465769bf82e252651a31972ef6cab02a13c74bd267690fff77",
        T413_TABLE: "e93cc1e61c97c018880e248b47f9c6edef203fb1cee6c93a41fb90399f81f086",
        T413_SUM: "eaf88637d66ff416d8dd5ae005805ae12a1cd05d6a7bd4fb2cbca15f50c2d7d0",
        T414_TABLE: "7bc3752cd32e7e4a0858fbdbf849c704fd7701ab9abf305192ff30807ddc7baf",
        FBV1: "5238ca1cf2a02ca2edd92f145a5f3ed0a7b65e94794dfa0d596064e2f0d48f41"}
SOURCES = {
    "T-418": {"task": "T-418", "file": "research/agents_t418/SPACE_TABLE_T418.csv; research/agents_t418/summary.json",
              "sha256": f"{PINS[T418_TABLE]}; {PINS[T418_SUM]}",
              "merge_commit": "361f6e47ee9f262df957ee63a31e9e6601ce619e",
              "checker_run": "Verifier 2026-11-01T05:41Z session_01E6cPnc6Jh7Vm8mD5NE (Gate A PASS on e5116bbc; "
                             "condition: landing bounds reduced in the same package)"},
    "T-413": {"task": "T-413", "file": "research/agents_t413/STATION_TABLE_T413.csv; research/agents_t413/summary.json",
              "sha256": f"{PINS[T413_TABLE]}; {PINS[T413_SUM]}",
              "merge_commit": "ae87deb1b7815799fee3fb6e5360dfc09425a0d1",
              "checker_run": "Verifier 2026-11-01T07:57Z session_01E6cPncuBazTqhpuf19bAmo (Gate A PASS on 62faa889; "
                             "band owner: register LIFT LANDING THRESHOLD 08:15)"},
    "T-414": {"task": "T-414", "file": "research/agents_t414/ROOM_TABLE_T414.csv; research/agents_t414/floor_bed_v1.py",
              "sha256": f"{PINS[T414_TABLE]}; {PINS[FBV1]}",
              "merge_commit": "4f81eda1faf6a0cf29caa9285dabbf31c39f0905",
              "checker_run": "Verifier 2026-11-01T05:25Z session_01E6cPnc6Jh7Vm8mD5NE (Gate A PASS on 3439b2b4; "
                             "F-C-T414-1)"},
}
B_UPPER = {"1F-DRY": {"b": 0.051, "source": "Checker F-C-T414-1 (T-214: 1F b 0.049 .. 0.051; an upper bound takes "
                                            "0.051)"}}
# floor part -> the storey zone whose printed FFL it sits at (None: a sub-level with no printed structural top)
LEVEL_ZONE = {"+1.00": "GF-DRY", "+9.70": "2F-DRY"}
OWNER_DEPTH_SOURCE = "UP-ELEV-005 v1.1.0 (owner_confirmed; drawn width, 0.50 m depth borrowed)"


def _rel(p):
    return str(p.relative_to(ROOT))


def _read(p):
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    if h != PINS[p]:
        raise SystemExit(f"{_rel(p)}: sha256 {h[:12]} is not the merged {PINS[p][:12]} (an edited ledger stops)")
    return b.decode("utf-8")


def _owner():
    _read(FBV1)
    spec = importlib.util.spec_from_file_location("t414_floor_bed_v1", FBV1)
    fb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fb)
    return {k: {"lo": v["lo"], "hi": v["hi"], "rule": v["rule"]} for k, v in fb.OWNER_BED.items()}


def _zone_b():
    out = {}
    for t in csv.DictReader(_read(T414_TABLE).splitlines()):
        if t["kind"] == "DRY" and t["build_up_b"]:
            z = f"{t['floor']}-DRY"
            b = float(t["build_up_b"])
            if out.setdefault(z, b) != b:
                raise SystemExit(f"T-414 table: zone {z} prints two b values")
    return out


def _f(x):
    return None if x in (None, "") else float(x)


def _rng(s):
    lo, hi = (float(x) for x in s.split(".."))
    return lo, hi


def build(project_id=None):
    parts_in = list(csv.DictReader(_read(T418_TABLE).splitlines()))
    s418 = json.loads(_read(T418_SUM))
    st_in = list(csv.DictReader(_read(T413_TABLE).splitlines()))
    s413 = json.loads(_read(T413_SUM))
    if s413.get("station_count") != len(st_in):
        raise SystemExit("STATION_TABLE_T413.csv and summary.json disagree on the station count")
    zb = _zone_b()
    # the stair room's landing bound line = the template for its floor parts (same room, same documents)
    bound_of = {r["room"]: r for r in s418["landing_bound_overlap"]}
    floor_parts, held_parts = [], []
    for t in parts_in:
        if t["kind"] == "FLOOR" and t["family"] == "B3-01":
            settled = t["finish"] == "PORCELAIN"
            z = LEVEL_ZONE.get(t["level"])
            floor_parts.append({
                "part": t["part"], "room": t["room"], "floor": t["room"][:2], "level": t["level"],
                "area": _f(t["area_m2"]), "item_code": "FIN.FLOOR.PORCELAIN" if settled else "FIN.FLOOR.FINISH_HELD",
                "finish": "porcelain (owner Q-70 A)" if settled else t["finish"].replace("HELD: ", ""),
                "finish_status": t["finish_status"], "area_status": t["status"],
                "zone": z or f"{t['room'][:2]}-SUBLEVEL {t['level']}", "b": zb.get(z) if z else None,
                "template_line": bound_of[t["room"]]["line_id"], "source_tasks": ["T-418", "T-414"]})
        elif t["kind"] == "UNREAD":
            held_parts.append({"part": t["part"], "room": t["room"], "floor": t["room"][:2],
                               "low": _f(t["held_low"]), "high": _f(t["held_high"]), "why": t["note"],
                               "template_line": bound_of[t["room"]]["line_id"], "source_tasks": ["T-418"]})
    bounds = []
    for r in s418["landing_bound_overlap"]:
        inside = [p["part"] for p in floor_parts if p["room"] == r["room"]]
        if abs(sum(p["area"] for p in floor_parts if p["room"] == r["room"]) - r["floor_parts_inside_m2"]) > 1e-6:
            raise SystemExit(f"T-418 summary: the floor parts of {r['room']} do not add to its overlap")
        bounds.append({"line_id": r["line_id"], "high_before": r["bound_high_m2"], "parts": inside,
                       "high_after_table": r["bound_high_after_m2"], "source_tasks": ["T-418"]})
    lobby_2f = {p["room"]: p["part"] for p in floor_parts if p["floor"] == "2F"}
    stations = []
    for t in st_in:
        w = float(t["CLEAR_WIDTH_M"])
        thr = float(t["THRESHOLD_M2"])
        d = round(thr / w, 6)
        olo, ohi = _rng(t["FLOOR_OVERLAP_M2"])
        if abs(ohi - thr) > 1e-9:
            raise SystemExit(f"{t['STATION']}: overlap high {ohi} is not the threshold {thr}")
        band = round(d - olo / w, 6)
        slo, shi = s413["surround_B6_06"]["per_station_bound_m2"][t["STATION"]]
        fl = t["FLOOR_LINE"] if t["FLOOR_LINE"].startswith("L-") else None
        st = {"station": t["STATION"], "floor": t["FLOOR"], "opening": t["ENGINE_OPENING"], "width": w,
              "width_status": t["WIDTH_STATUS"], "depth": d,
              "depth_status": "ASSUMED — OWNER-APPROVED" if "depth ASSUMED" in t["THRESHOLD_STATUS"] else "DRAWING-CONFIRMED",
              "depth_source": OWNER_DEPTH_SOURCE, "band": band, "front_edge": float(t["FRONT_EDGE_LM"]),
              "surround_low": slo, "surround_high": shi, "surround_formula": t["SURROUND_FORMULA"],
              "surround_held": (f"door clear height {t['CLEAR_HEIGHT']}"
                                + (f"; right band {t['RIGHT_M']}" if t["RIGHT_STATUS"] == "HELD" else "")),
              "band_line": t["BAND_LINE"], "floor_line": fl,
              "floor_part": None if fl else lobby_2f[t["LANDING_FACE"]],
              "template_line": t["OPENING_LINE"], "source_tasks": ["T-413"]}
        stations.append(st)
    restate = [{"finish_line": s["floor_line"], "zone": f"{s['floor']}-DRY"} for s in stations if s["floor_line"]]
    return {"schema": "URBAN_V3038_INPUTS_V1", "project_id": project_id, "sources": list(SOURCES.values()),
            "owner_bed": _owner(), "b_upper": B_UPPER, "floor_parts": floor_parts, "held_parts": held_parts,
            "landing_bounds": bounds, "stations": stations, "restate_beds": restate}


def main(argv):
    doc = build(argv[0] if argv else None)
    print(json.dumps({k: v for k, v in doc.items() if k not in ("sources",)}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
