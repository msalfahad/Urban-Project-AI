"""T-480: the URBAN_V3054_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.54 (engine.source.arch_v3054), built ONLY from
pinned, merged files (an edited file stops the build):

  research/agents_t476/FLIGHT_CENSUS_T476.csv   T-476 per-flight census (MERGED 88e70ffe, Verifier Gate A 2026-11-02
      18:40, own re-measure ST-01 MS2-L 3.782209 lm AGREE 0.000 %): every flight side with kind, family, status, plan,
      rise, pitch-line length, run and the reason a piece is held;
  research/agents_t476/READER_BINDING_T476.csv  the same task's binding of the 14 per-flight plan-reader FIN.RAILING
      lines to their 9 physical flights (all RETIRE) and the run lines that carry them.

Nothing is typed: every length is recomputed by arch_v3054 from plan and rise and asserted equal to the census. The run
actions are the merged T-476 proposal (B7-09 17.366 -> 33.319 lm: RL-07 15.953 lm added; RL-05 / RL-08 / RL-06 re-measured
AGREE; RL-09 / RL-11 held unchanged); arch_v3054 refuses an action the candidate line's state does not allow.

    python3 -I research/agents_t480/t480_inputs.py [project_id]      # prints the inputs summary
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CENSUS = ROOT / "research/agents_t476/FLIGHT_CENSUS_T476.csv"
BINDING = ROOT / "research/agents_t476/READER_BINDING_T476.csv"
PINS = {CENSUS: "77f5fc462a71e2530af5f8822df75f86829a8716c31a38579f6ad651ce2ad688",
        BINDING: "bb69fddf48e17fe1fdd099874f60e39064f111a31bbb3a86b9c0db202ebcd223"}
CHECKER = ("Verifier 2026-11-02T18:40Z Gate A PASS on 0aaeaf27 (session_01E6cPnbMXo9W57mVzHxdcHr): own scan of the "
           "architectural DXF, 1F plan dimension 3300, 12 riser positions step 300, levels +5.50 / +9.70, 4.20 / 25 = "
           "0.168, MS2-L hypot(3.300, 1.848) = 3.782209 lm AGREE 0.000 %; 1 of 14 pieces own-measured")
SOURCES = {
    "T-476": {"task": "T-476", "file": "research/agents_t476/FLIGHT_CENSUS_T476.csv", "sha256": PINS[CENSUS],
              "merge_commit": "88e70ffe", "checker_run": CHECKER},
    "T-476 binding": {"task": "T-476 binding", "file": "research/agents_t476/READER_BINDING_T476.csv",
                      "sha256": PINS[BINDING], "merge_commit": "88e70ffe", "checker_run": CHECKER},
}
# the merged T-476 proposal (row handoff and summary.json 'proposal'), per run
RUN_ACTIONS = {"RL-07": "VALUE", "RL-05": "CONFIRM", "RL-08": "CONFIRM", "RL-06": "CONFIRM", "RL-09": "KEEP",
               "RL-11": "KEEP"}
RUN_RE = re.compile(r"RL-\d{2}")


def _load(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.name}: sha256 differs from the pinned file (edited input)")
    return list(csv.DictReader(io.StringIO(b.decode("utf-8"))))


def _f(x):
    return None if x in (None, "") else float(x)


def census():
    rows = _load(CENSUS)
    seen, out = {}, []
    for r in rows:                     # a wall side with no rail (NOT_APPLICABLE) takes no piece id
        k = f"{r['STAIR']}:{r['FLIGHT']}"
        seen[k] = seen.get(k, 0) + (r["STATUS"] != "NOT_APPLICABLE")
    for r in rows:
        k = f"{r['STAIR']}:{r['FLIGHT']}"
        pid = k if seen[k] == 1 else f"{k}:{r['SIDE']}"
        out.append(dict(r, piece_id=pid))
    return out


def build(project_id=None):
    runs, unknowns, no_rail = {}, [], []
    for r in census():
        p = {"piece_id": r["piece_id"], "stair": r["STAIR"], "flight": r["FLIGHT"], "side": r["SIDE"],
             "kind": r["KIND"], "status": r["STATUS"], "plan_m": _f(r["PLAN_M"]), "rise_m": _f(r["RISE_M"]),
             "length_lm": _f(r["LENGTH_LM"]), "source": r["SOURCE"]}
        if "per going" in r["SOURCE"]:
            p["pitch"] = "PER_GOING"
        if r["MISSING"]:
            p["missing"] = r["MISSING"]
        if r["STATUS"] == "NOT_APPLICABLE":
            no_rail.append({"stair": r["STAIR"], "flight": r["FLIGHT"], "side": r["SIDE"], "why": r["SOURCE"]})
            continue
        if r["STATUS"] != "DRAWING-CONFIRMED" and not r["MISSING"]:
            p["missing"] = r["SOURCE"]
        if r["RUN"] in RUN_ACTIONS:
            runs.setdefault(r["RUN"], []).append(p)
        elif r["RUN"] == "none" and r["STATUS"] == "UNKNOWN":
            unknowns.append(dict(p, floor="GF" if r["FLIGHT"].startswith("GF ") else None, source_tasks=["T-476"]))
        else:
            raise SystemExit(f"census row {r['piece_id']}: run {r['RUN']!r} has no merged action")
    retire = []
    for b in _load(BINDING):
        if b["ACTION"] != "RETIRE":
            raise SystemExit(f"binding {b['LINE_ID']}: action {b['ACTION']} (only RETIRE is merged)")
        retire.append({"line_id": b["LINE_ID"], "floor": b["FLOOR"], "reader_flight": b["READER_FLIGHT"],
                       "physical_flight": b["PHYSICAL_FLIGHT"], "reading": b["READING"],
                       "homes": sorted(set(RUN_RE.findall(b["HOMES"]))), "why": b["NOTE"],
                       "source_tasks": ["T-476 binding"]})
    return {"schema": "URBAN_V3054_INPUTS_V1", "project_id": project_id, "sources": list(SOURCES.values()),
            "runs": [{"run": k, "action": RUN_ACTIONS[k], "pieces": v, "source_tasks": ["T-476"]}
                     for k, v in sorted(runs.items())],
            "unknowns": unknowns, "retire": retire, "no_rail_sides": no_rail}


if __name__ == "__main__":
    d = build(sys.argv[1] if len(sys.argv) > 1 else None)
    from engine.source import arch_v3054 as A
    v = A.load_inputs(d)
    print(json.dumps({"runs": {r["run"]: [r["action"], r["_L"], len(r["_pieces"])] for r in v["_runs"]},
                      "unknowns": [p["piece_id"] for p in v["_unknowns"]], "retire": len(v["_retire"]),
                      "no_rail_sides": len(v["_no_rail"])}, indent=1))
