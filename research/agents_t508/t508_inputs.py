"""T-508: the URBAN_V3056_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.56 (engine.source.arch_v3056), built ONLY from
pinned, merged files (an edited file stops the build):

  research/agents_t501/LINES_T501.csv    T-501 stair-side table (MERGED 5eded7df, Verifier 2026-11-04T10:56Z Gate A,
      own re-measure by handle MS2-LD 3.700 lm and MS2-L W side sloped 2.737 / zigzag 3.694 lm AGREE): every stair /
      landing / step piece with face, stations, risers, returns, levels, status and both form figures;
  research/agents_t501/BINDING_T501.csv  the same task's binding of the 1F living room line's shaft stretches (9.050 lm
      certain + the 2.200 lm held range over W13 / W25) to the pieces at every level (residual 0).

Nothing is typed except what the table cannot carry: the storey label of each stair element (the plan the flight
starts on), the room floor level +5.50 of the retired stretches (T-501 s.1: the 1F floor) and the candidate figures
of the two room lines the stretches leave (asserted against the candidate by arch_v3056; a stale figure is refused).
Every length is recomputed by arch_v3056 (landing = plan + returns; sloped = hypot(plan, level change) + returns where
the stations and levels are in the table; zigzag via one riser per flight) and asserted equal to the table. The form
(ORR-007) is NOT chosen: every flight piece becomes a blank zigzag / sloped pair.

    python3 -I research/agents_t508/t508_inputs.py [project_id]      # prints the inputs summary
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LINES = ROOT / "research/agents_t501/LINES_T501.csv"
BINDING = ROOT / "research/agents_t501/BINDING_T501.csv"
PINS = {LINES: "1551662ca02dbca17add9ebd9201e8de13857d5aed5981cf882108c1996f9bbd",
        BINDING: "140d8136680c1fe75286d1a6f3ee9fb1f4a59fb60f9eed76857d3118dbfa72f8"}
CHECKER = ("Verifier 2026-11-04T10:56Z Gate A PASS on 68f95dc0 (session_01E6cPnkipuHyPu6hipkrg), engine merge "
           "5eded7df: own re-measure from the architectural DXF by handle, MS2-LD level skirting W 1.050 + N 1.400 + "
           "N 0.100 + E 1.150 = 3.700 lm AGREE; MS2-L W side sloped 2.737 / zigzag 3.694 lm AGREE; 1F shaft 9.050 lm at "
           "+5.50 ENGINE_WRONG confirmed")
SOURCES = {
    "T-501": {"task": "T-501", "file": "research/agents_t501/LINES_T501.csv", "sha256": PINS[LINES],
              "merge_commit": "5eded7df", "checker_run": CHECKER},
    "T-501 binding": {"task": "T-501 binding", "file": "research/agents_t501/BINDING_T501.csv",
                      "sha256": PINS[BINDING], "merge_commit": "5eded7df", "checker_run": CHECKER},
}
# the storey of each stair element: the plan its first riser stands on (T-501 s.2; MS1-* / D1 / RS-* / E1 on the GF
# plan, MS2-* on the 1F plan)
FLOOR = {"MS1-L": "GF", "MS1-T": "GF", "MS1-LD": "GF", "MS1-U": "GF", "D1": "GF", "RS-S": "GF", "RS-LD": "GF",
         "RS-C": "GF", "E1": "GF", "MS2-L": "1F", "MS2-LD": "1F", "MS2-TR": "1F", "MS2-U": "1F"}
# the room line the shaft stretches leave and its held range (T-501 s.3 / s.5; candidate figures, asserted by the engine)
ROOM_LINE = "L-ba3599ec2dc82c221617"
RANGE_LINE = "L-079bc7669b2c68d5d11b"
ROOM_FLOOR_LEVEL = 5.50
RANGE_EXPECT = {"low": 0.0, "high": 2.2}
# the room line in the candidate of record V3_0_54 c85c4630 (T-480 merge 1b66b719): gross 52.440 - 11.004640 listed
# openings = net 41.435360 lm (the W13 / W25 bases already listed, held in RANGE_LINE)
ROOM_EXPECT = {"evidence_state": "SOURCE_DERIVED", "gross": 52.44, "measured_net": 41.43536}
COLUMN_RETURNS = {"L-ba3599ec W AF1 2.250 .. 4.500": 0.1}   # column 3005 returns (BINDING status 'certain (+ 3005 ...)')
KIND = {"FLIGHT": "FLIGHT", "LANDING": "LANDING", "STEP": "STEP"}


def _load(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.name}: sha256 differs from the pinned file (edited input)")
    return list(csv.DictReader(io.StringIO(b.decode("utf-8"))))


def _f(x):
    return None if x in (None, "") else float(x)


def pieces():
    out = []
    for r in _load(LINES):
        if r["element"] not in FLOOR:
            raise SystemExit(f"{r['pid']}: element {r['element']} has no storey")
        out.append({"pid": r["pid"], "element": r["element"], "face": r["face"], "kind": KIND[r["kind"]],
                    "cls": r["cls"], "status": r["status"], "floor": FLOOR[r["element"]],
                    "s0": _f(r["s0"]), "s1": _f(r["s1"]), "plan_lm": float(r["plan_lm"]), "risers": int(r["risers"]),
                    "returns_lm": float(r["returns_lm"] or 0), "level0": _f(r["level0"]), "level1": _f(r["level1"]),
                    "value_lm": _f(r["value_lm"]), "zigzag_lm": _f(r["zigzag_lm"]), "sloped_lm": _f(r["sloped_lm"]),
                    "cause": r["cause"], "evidence": r["evidence"], "source_tasks": ["T-501"]})
    return out


def stretches():
    out = []
    for r in _load(BINDING):
        if abs(float(r["residual_lm"])) > 1e-9 or not r["decision"].startswith("NOT_APPLICABLE"):
            raise SystemExit(f"{r['segment']}: the merged binding does not close it")
        out.append({"segment": r["segment"], "face": r["face"], "s0": float(r["s0"]), "s1": float(r["s1"]),
                    "returns_lm": COLUMN_RETURNS.get(r["segment"], 0.0),
                    "status_before": "held range" if r["status_before"] == "held range" else "certain",
                    "owners": r["owners"].split()})
    return out


def build(project_id, room_expect=None):
    """room_expect: {"evidence_state", "gross", "measured_net"} of ROOM_LINE in the base candidate (the runner reads it
    from the candidate of record; the engine refuses it when stale)."""
    ret = {"room_line_id": ROOM_LINE, "floor_level": ROOM_FLOOR_LEVEL, "expect": room_expect or {},
           "stretches": stretches(), "range_line_id": RANGE_LINE, "range_expect": RANGE_EXPECT,
           "source_tasks": ["T-501 binding"]}
    return {"schema": "URBAN_V3056_INPUTS_V1", "project_id": project_id, "sources": list(SOURCES.values()),
            "form": None, "pieces": pieces(), "retire": ret}


if __name__ == "__main__":
    from engine.source import arch_v3056 as A
    pid = sys.argv[1] if len(sys.argv) > 1 else None
    d = build(pid, ROOM_EXPECT)
    v = A.load_inputs(d)
    print(json.dumps({"pieces": len(v["_pieces"]), "risers_by_flight": v["_risers"],
                      "certain_lm": v["_retire"]["_certain"], "range_lm": v["_retire"]["_range"]}, indent=1))
