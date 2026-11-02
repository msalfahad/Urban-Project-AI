"""T-431: the URBAN_V3041_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.41 (engine.source.arch_v3041), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build). Every figure is READ from those files;
typed here are only the column names, the line ids the merged files print (bound to the candidate by the module: a stale
binding stops) and the wording of the held reasons.

  research/agents_t427/summary.json          T-427 (MERGED 65ce8f6d, Verifier 2026-11-01 12:01 UTC Gate A PASS, own
      re-measure on the DXF): the ZONE_EXTENT_V1 rows: the band west face 4.885 m2 and the strip west part 0.760 m2 are
      ROOM_FLOOR (DRAWING-CONFIRMED, finish as the open-room line, ASSUMED — OWNER-APPROVED); the curb strip 0.604 and the
      band proper 9.101 stay HELD (D-48); the cross-trade skirting figure;
  research/agents_t440/summary.json          T-440 (MERGED 3c65489c, Gate A PASS): the open-room skirting line's merged
      net 24.671589 lm and the dining face's own base runs (wall 2.70 + column 1.20 = 3.90 lm, 0 faces in the pantry box);
  research/agents_t283/CEILING_LEDGER_R3_EXPORT.json   T-283 r3 (MERGED 6e141df6, Gate A PASS): face GF-RFD4E1D plan
      area 4.885 m2 under the slab (HELD_CLASS only for its class) and its bulkhead edges 6.5428 m;
  research/agents_t414/ROOM_TABLE_T414.csv + floor_bed_v1.py   T-414 (MERGED 4f81eda1): the owner Q-45 DRY range and the
      GF dry zone build-up b (the bed pair of the new line, R-T420-1).

    python3 -I research/agents_t431/t431_inputs.py [project_id]      # prints the inputs
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

T427 = ROOT / "research/agents_t427/summary.json"
T440 = ROOT / "research/agents_t440/summary.json"
T283 = ROOT / "research/agents_t283/CEILING_LEDGER_R3_EXPORT.json"
T414_TABLE = ROOT / "research/agents_t414/ROOM_TABLE_T414.csv"
FBV1 = ROOT / "research/agents_t414/floor_bed_v1.py"
PINS = {T427: "a87b3b5a3be86fc4bab0ddda8ee704d8c7488c42de14c47a7e76936d1dce4fba",
        T440: "df7982c31fa107b64941f7b179bef926c8ec374fb05c54783ac0758e9971b317",
        T283: "fc8873cf2af6fef861cb12de93b04756939bb2906900672452a4dae820103149",
        T414_TABLE: "7bc3752cd32e7e4a0858fbdbf849c704fd7701ab9abf305192ff30807ddc7baf",
        FBV1: "5238ca1cf2a02ca2edd92f145a5f3ed0a7b65e94794dfa0d596064e2f0d48f41"}
SOURCES = {
    "T-427": {"task": "T-427", "file": "research/agents_t427/summary.json", "sha256": PINS[T427],
              "merge_commit": "65ce8f6da9f434d7c3a55bee77111d9635fb225c",
              "checker_run": "Verifier 2026-11-01 12:01 UTC session_01E6cPnbsgWu8tvY3NBkfoBp (Gate A PASS; own DXF "
                             "re-measure: 4.885 + 0.760 = 5.645 m2 room floor, curb 0.604 HELD)"},
    "T-440": {"task": "T-440", "file": "research/agents_t440/summary.json", "sha256": PINS[T440],
              "merge_commit": "3c65489c5347629f6429a1e75ab37c67886e3b4e",
              "checker_run": "Verifier 2026-11-01T18:35Z session_01E6cPnapSXrmY87Y9zZ1EWi (Gate A PASS on e4983c21: "
                             "over-count 0.000, the +3.90 lm outside the pantry box)"},
    "T-283": {"task": "T-283", "file": "research/agents_t283/CEILING_LEDGER_R3_EXPORT.json", "sha256": PINS[T283],
              "merge_commit": "6e141df67e9bc5559ab9fcc677fb4d97d0cb95f0",
              "checker_run": "Verifier 2026-10-25 05:32 UTC session_01GfxzQEADkKAYhzqGtSarUT (Gate A PASS on c92a24cb)"},
    "T-414": {"task": "T-414", "file": "research/agents_t414/ROOM_TABLE_T414.csv; research/agents_t414/floor_bed_v1.py",
              "sha256": f"{PINS[T414_TABLE]}; {PINS[FBV1]}",
              "merge_commit": "4f81eda1faf6a0cf29caa9285dabbf31c39f0905",
              "checker_run": "Verifier 2026-11-01T05:25Z session_01E6cPnc6Jh7Vm8mD5NE (Gate A PASS on 3439b2b4; "
                             "F-C-T414-1)"},
}
# line ids the merged files print (bound to the candidate by the module; stale binding stops)
OPEN_FLOOR = "L-7625f35c503d9f8e6196"        # GF-RC99C2A:floor (T-427 'open-room line L-7625f35c')
OPEN_SKIRT = "L-71e2e002a3af624097f0"        # GF-RC99C2A:skirting (T-440 host_line)
OPEN_CEIL = "L-eb3be58fc760b39f0e38"         # GF-RC99C2A:ceiling (template of the room's ceiling class)
FACE_LINE = "L-6b6412e885390b434819"         # GF-RFD4E1D:space (T-427: 'L-6b6412e8 4.885')
STRIP_LINE = "L-554a525edce9a9235bee"     # HL:FLOOR_SCOPE:HELD_WITH:GF:GF-OP-003-NO-OPENING:band (T-427: "L-554a525e 1.364")
STRIP_PREFIX = "L-554a525e"
FACE, ROOM = "GF-RFD4E1D", "GF-RC99C2A"
ROW_FACE = "GF-RFD4E1D band west face"
ROW_WEST = "OP-003 band strip, west 3.80 (x 3.00 .. 6.80)"
ROW_CURB = "OP-003 band strip, curb 3.02 (x 6.80 .. 9.82)"
OWNER = "ASSUMED — OWNER-APPROVED"


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


def _zone_b(zone):
    out = None
    for t in csv.DictReader(_read(T414_TABLE).splitlines()):
        if t["kind"] == "DRY" and t["build_up_b"] and f"{t['floor']}-DRY" == zone:
            b = float(t["build_up_b"])
            if out not in (None, b):
                raise SystemExit(f"T-414 table: zone {zone} prints two b values")
            out = b
    if out is None:
        raise SystemExit(f"T-414 table: no b for {zone}")
    return out


def build(project_id=None, strip_line=None):
    s427 = json.loads(_read(T427))
    rows = {r["id"]: r for r in s427["zone_extent"]["rows"]}
    face, west, curb = rows[ROW_FACE], rows[ROW_WEST], rows[ROW_CURB]
    for r in (face, west):
        if r["physical_class"] != "ROOM_FLOOR" or r["status"] != "DRAWING-CONFIRMED":
            raise SystemExit(f"T-427 row {r['id']}: not a DRAWING-CONFIRMED room-floor piece")
    if curb["physical_class"] != "STRIP" or curb["status"] != "HELD":
        raise SystemExit("T-427 curb row is not a HELD strip")
    corr = s427["dry"]["correction"]
    if abs(face["area_m2"] + west["area_m2"] - corr["moved_to_dry_floor_m2"]) > 1e-9:
        raise SystemExit("T-427 rows do not re-add to the moved floor")
    s440 = json.loads(_read(T440))
    add = s440["t431_addition"]
    if add["room"] != FACE or add["edges_inside_pantry_box"] != 0 or add["flags"]:
        raise SystemExit("T-440 t431_addition is not the clear dining face base")
    runs = add["v29_runs_lm"]
    if abs(runs["wall"] + runs["column"] - add["base_lm"]) > 1e-9:
        raise SystemExit("T-440 base runs do not add to base_lm")
    if s440["host_line"] != OPEN_SKIRT:
        raise SystemExit("T-440 host line is not the open-room skirting line")
    led = json.loads(_read(T283))
    fr = [f for f in led["faces"] if f["face_id"] == FACE] if "faces" in led else \
        [f for f in _walk_faces(led) if f.get("face_id") == FACE]
    if len(fr) != 1 or fr[0]["class"] != "HELD_CLASS":
        raise SystemExit(f"T-283 ledger: face {FACE} is not one HELD_CLASS face")
    surf = {s["unit"]: s for s in fr[0]["surfaces"]}
    decor, edge = surf["m2"]["qty"], surf["m"]["qty"]
    if abs(decor - face["area_m2"]) > 1e-9:
        raise SystemExit("T-283 face area is not the T-427 face piece")
    sl = strip_line or STRIP_LINE
    if not sl:
        raise SystemExit("the strip line id (STRIP_LINE) is not bound")
    zone = "GF-DRY"
    piece = {
        "piece": "SOUTH-FACADE-DINING", "room": FACE, "floor": "GF", "joins_room": ROOM,
        "area_status": "DRAWING-CONFIRMED", "finish": "porcelain (URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1, as the open room)",
        "finish_status": OWNER, "zone": zone, "b": _zone_b(zone), "b_upper": None, "template_line": OPEN_FLOOR,
        "parts": [{"id": f"{FACE}:west-face", "area": face["area_m2"], "from_line": FACE_LINE},
                  {"id": f"{FACE}:west-strip", "area": west["area_m2"], "from_line": sl}],
        "zone_lines": [
            {"line_id": FACE_LINE, "action": "RETIRE", "value_before": face["area_m2"], "parts": [f"{FACE}:west-face"]},
            {"line_id": sl, "action": "SHRINK", "value_before": round(west["area_m2"] + curb["area_m2"], 6),
             "parts": [f"{FACE}:west-strip"],
             "keeps": [{"id": "curb-strip", "area": curb["area_m2"],
                        "why": "the curb strip of the garden band (drawn curb, HELD with the band: designer D-48)"}]}],
        "skirting": {"line_id": OPEN_SKIRT, "net_before": s440["candidate_host_net_lm"],
                     "rows": [{"id": f"{FACE}:wall", "kind": "wall", "qty": runs["wall"],
                               "what": f"dining south wall face along the piece {FACE} (wall less the column, drawn)"},
                              {"id": f"{FACE}:column", "kind": "column", "qty": runs["column"],
                               "what": f"column faces exposed to the piece {FACE} (two returns + front, drawn)"}]},
        "ceiling": {"face": FACE, "decor_m2": decor, "decor_status": "DRAWING-CONFIRMED", "template_line": OPEN_CEIL,
                    "class_of": f"{ROOM} (the open dining room's decor ceiling)", "bulkhead_edge_m": edge,
                    "bulkhead_why": ("bulkhead faces of the beam pieces over the piece: the edge is in the ceiling "
                                     "ledger, the face depth / which side carries decor is not decided for this face "
                                     "(R-CEIL-R3-2 not run on it)"),
                    "unread": [{"id": f"{FACE}:west-strip", "area": west["area_m2"],
                                "why": ("no ceiling-ledger reading over the 0.20 m west strip (the T-283 ledger "
                                        "never read it: the engine strip sat outside every ceiling face)")}]},
        "source_tasks": ["T-427", "T-440", "T-283", "T-414"]}
    return {"schema": "URBAN_V3041_INPUTS_V1", "project_id": project_id,
            "sources": [SOURCES[t] for t in ("T-427", "T-440", "T-283", "T-414")],
            "owner_bed": {"DRY": _owner()["DRY"]}, "pieces": [piece]}


def _walk_faces(led):
    for k, v in led.items():
        if isinstance(v, list):
            for x in v:
                if isinstance(x, dict) and "face_id" in x:
                    yield x


if __name__ == "__main__":
    print(json.dumps(build(sys.argv[1] if len(sys.argv) > 1 else None), ensure_ascii=False, indent=1))
