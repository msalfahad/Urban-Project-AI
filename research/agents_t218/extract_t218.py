"""T-218 input extractor: reads two finished engine runs of the development villa (outside the repository) and writes
ALSENAN_T218_INPUT.json with item codes, units, states, quantities, room / opening / line ids, lengths and areas only
(no coordinates, no names beyond the engine's room-type words).

    python3 -I research/agents_t218/extract_t218.py <released V2.9 run dir> <candidate-base V2.13 run dir> \
        --out research/agents_t218/ALSENAN_T218_INPUT.json

Released run: tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json (REPRODUCED,
BOQ_LINES.csv b96185d4...). Candidate base: tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V2.13 (the base method
of the V3.0.x candidates; arch_v30.BASE_METHOD), same drawings and conventions as research/agents_t208.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

KITCHEN_CODE = "KITCHEN"
FLOORS = ("1F", "2F")
ROOM_KEYS = ("room_id", "floor", "codes", "kind", "finish_scope", "area_m2", "perimeter_lm", "runs_lm", "doors",
             "passages", "level_m")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _lines(run):
    out = []
    with open(Path(run) / "BOQ_LINES.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out.append(r)
    return out


def _num(x):
    return None if x in ("", None) else float(x)


def _line(r):
    return {"line_id": r["line_id"], "floor": r["floor"], "room_id": r["room_id"], "item_code": r["item_code"],
            "unit": r["unit"], "qty": _num(r["measured_net"]), "low": _num(r["bounded_low"]),
            "high": _num(r["bounded_high"]), "state": r["evidence_state"], "rule_id": r["rule_id"]}


def _room(r):
    d = {k: r.get(k) for k in ROOM_KEYS}
    d["attached_cells"] = [{"area_m2": a["area_m2"], "passages": a["passages"], "rule": a["rule"]}
                           for a in r.get("attached_cells") or ()]
    d["windows"] = r.get("windows")
    return d


def run_part(run):
    run = Path(run)
    rooms = json.loads((run / "ARCH_ROOMS.json").read_text(encoding="utf-8"))["rooms"]
    lines = _lines(run)
    opens = json.loads((run / "ARCH_OPENINGS.json").read_text(encoding="utf-8"))["openings"]
    fa = json.loads((run / "ARCH_FLOOR_AREAS.json").read_text(encoding="utf-8"))["floors"]
    kit = [r for r in rooms if KITCHEN_CODE in (r.get("codes") or ())]
    kit_ids = {r["room_id"] for r in kit}
    door_ids = {(r["floor"], d) for r in kit for d in r.get("doors") or ()}
    upper_rooms = [r for r in rooms if r["floor"] in FLOORS]
    keep_open = {(o["floor"], o["opening_id"]) for o in opens if o["floor"] in FLOORS} | door_ids
    op = [{"floor": o["floor"], "opening_id": o["opening_id"], "kind": o.get("kind"), "type": o.get("type"),
           "width_m": o.get("width_m") if o.get("width_m") is not None else (o.get("opening_v27") or {}).get(
               "wall_gap_m"), "wall_t_m": o.get("wall_t_m"), "rooms": o.get("rooms")}
          for o in opens if (o["floor"], o["opening_id"]) in keep_open]
    neighbours = {rid for o in op for rid in o["rooms"] or ()} - kit_ids
    nb = [{"room_id": r["room_id"], "floor": r["floor"], "codes": r.get("codes"), "kind": r.get("kind"),
           "class": r.get("class")} for r in rooms if r["room_id"] in neighbours and r["floor"] not in FLOORS]
    strip_lines = [_line(r) for r in lines if r["floor"] in FLOORS and "-STRIP-" in r["room_id"]
                   and r["item_code"] != "ARCH.WINDOW_REVEAL"]
    kit_lines = [_line(r) for r in lines if r["room_id"] in kit_ids or
                 any(r["room_id"] == f"{f}-STRIP-{d}" for f, d in door_ids)]
    floor_lines = [_line(r) for r in lines if r["floor"] in FLOORS and r["item_code"] in
                   ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE") and "-STRIP-" not in r["room_id"]]
    fa_strips = []
    for f in fa:
        if f["floor"] not in FLOORS:
            continue
        for s in f.get("strips") or ():
            if s.get("class") == "WINDOW_REVEAL":
                continue
            g = s.get("geometry") or {}
            fa_strips.append({"floor": f["floor"], "strip_id": s.get("strip_id"), "class": s.get("class"),
                              "area_m2": s.get("area_m2"), "opening_ids": s.get("opening_ids"),
                              "opening_kinds": s.get("opening_kinds"), "disposition": s.get("disposition"),
                              "opening_width_m": g.get("opening_width_m"), "depth_m": g.get("depth_m")})
    return {"boq_lines_sha256": _sha(run / "BOQ_LINES.csv"), "kitchen_rooms": [_room(r) for r in kit],
            "kitchen_lines": kit_lines, "kitchen_neighbours": nb, "openings": op,
            "upper_rooms": [_room(r) for r in upper_rooms], "upper_floor_lines": floor_lines,
            "upper_strip_lines": strip_lines, "upper_floor_area_strips": fa_strips}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("released")
    ap.add_argument("candidate_base")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc = {"schema": "T218_INPUT_V1",
           "runs": {"released": dict(method="ARCH_TAKEOFF_V2.9 + route G (V29_ROUTEG_NO_PROFILE)",
                                     **run_part(a.released)),
                    "candidate_base": dict(method="ARCH_TAKEOFF_V2.13 (base of V3.0.x, arch_v30.BASE_METHOD)",
                                           **run_part(a.candidate_base))}}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
