"""T-430: the URBAN_V3040_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.40 (engine.source.arch_v3040), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build). Every line id, candidate figure, run,
span per frame, printed depth and D-33 flag is READ from the T-426 census; typed here are only the column wiring, the
neck length (the Checker's own exact cut, below) and which lines take which disposition (the T-426 Gate A verdict).

  research/agents_t426/CENSUS_T426.json   T-426 (MERGED 1f298735, Verifier 2026-11-01 11:59 UTC Gate A PASS on
      37ca8f28): per candidate ground-beam line its runs, spans per frame (GBP / FP / CAP) and per reading, printed
      titles and depths (ST p.13), D-33 flag. Verdict: 7DC+7DD and 7E7+7E8 runs 3.525 (3.575) / 3.525 re-measured;
      'unloaded halves 0.06 x 3.525 = 0.2115 each ENGINE_WRONG (VERIFIED, own hand), loaded halves HELD on D-33, never
      the band's 0.60 and never 0'; 177+7CD#1 'a RANGE, never a chosen reading'; F-T426-1 accepted (D-34 short runs).
  research/agents_t416/summary_t416.json  T-416 (MERGED b7bb914a, Verifier 2026-11-01T07:54Z Gate A PASS on b0fe163d):
      the necks 7F5 / 7ED cut the bands; Checker F-C-T416-1: 'neck 7F5 0.300 x 0.300 exactly the band width' / '7.350 -
      7ED 0.300 = 7.050', the through-neck term exactly 0.600 m / 0.054000 m3 per band (cuts exact, no buffer); the necks
      are CN on FN footings (T-205 ledger): FOUNDED.

    python3 -I research/agents_t430/t430_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CENSUS = ROOT / "research/agents_t426/CENSUS_T426.json"
T416 = ROOT / "research/agents_t416/summary_t416.json"
PINS = {CENSUS: "b297bb1402f5394298e63302e6e73758306dc7c519a564a8e27efa340a59b815",
        T416: "37934957428456ab1f9b76f4747d928b08719fd43173cafa1f2e456042137575"}
SOURCES = {
    "T-426": {"task": "T-426", "file": "research/agents_t426/CENSUS_T426.json", "sha256": PINS[CENSUS],
              "merge_commit": "1f298735",
              "checker_run": "Verifier 2026-11-01 11:59 UTC session_01E6cPnbsgWu8tvY3NBkfoBp (Gate A PASS on 37ca8f28; "
                             "own re-measure 7DC+7DD #1/#2, 7E7+7E8 #1/#2, 177+7CD #1 on 'ST7757 dxf.dxf' + ST p.13)"},
    "T-416": {"task": "T-416", "file": "research/agents_t416/summary_t416.json", "sha256": PINS[T416],
              "merge_commit": "b7bb914a",
              "checker_run": "Verifier 2026-11-01T07:54Z session_01E6cPncuBazTqhpuf19bAmo (Gate A PASS on b0fe163d; "
                             "F-C-T416-1 exact cuts: necks 7F5 / 7ED 0.300 x 0.300, founded CN on FN)"},
}
# the necks crossing the two split bands (T-416 Checker own read, exact cut; founded: T-205 ledger, T-416 verdict)
NECKS = {"L-fe78ae283abfb6256358": [{"id": "7F5 (FP 10F6, CAP 892)", "length": 0.300, "founded": True}],
         "L-0e30aadba2eebc6c3ede": [{"id": "7ED (FP 10EE, CAP 88F)", "length": 0.300, "founded": True}]}
HOLD_RANGE = {"L-e24946df436cbc25fca6"}   # 177+7CD#1: titles GT5M / LT5M by reading (4.97 / 5.02) + D-33
HOLD_BLANK = {"L-be6708e07b40efa02779"}   # 0.10 m annex-arc sliver: no printed section (D-35 annex CONFLICT)


def _read(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.name}: sha256 differs from the merged file (edited input)")
    return b.decode("utf-8")


def build(project_id=None):
    census = json.loads(_read(CENSUS))
    _read(T416)                                # pinned: the neck read the cut lengths come from
    lines = {ln["line_id"]: ln for ln in census["lines"]}
    splits, holds = [], []
    for lid, necks in NECKS.items():
        ln = lines[lid]
        if ln["verdict"] != "DIFFERS" or len(ln["runs"]) != 2:
            raise SystemExit(f"{lid}: not the merged DIFFERS line with two runs")
        runs = []
        for r in ln["runs"]:
            sp = [v for k, v in r["spans_by_frame_m"].items() if k in ("GBP", "FP", "CAP")]
            loaded = bool(r["d33_held"])
            runs.append({"run": r["run"], "spans": [min(sp), max(sp)], "printed_D": list(r["printed_D_m"]),
                         "loaded": loaded,
                         "held_D": [r["printed_D_m"][0], ln["candidate_D_m"]] if loaded else None,
                         "cause": (f"beam(s) {r['d33_tees']} land on the run (D-33: the printed title is 'without "
                                   f"concentrated load')" if loaded else "nothing lands on the run")})
        splits.append({"line_id": lid, "band": ln["drawn_band"], "b": ln["candidate_b_m"],
                       "candidate": {"D": ln["candidate_D_m"], "L": ln["candidate_L_m"],
                                     "value": ln["candidate_value_m3"]},
                       "necks": necks, "runs": runs, "evidence_status": "VERIFIED",
                       "source_tasks": ["T-426", "T-416"]})
    for lid in sorted(HOLD_RANGE):
        ln = lines[lid]
        (r,) = ln["runs"]
        sp = r["spans_by_frame_m"]
        lo_l, hi_l = min(sp.values()), max(sp.values())
        lo_d, hi_d = min(r["printed_D_m"]), max(r["printed_D_m"])
        b = ln["candidate_b_m"]
        holds.append({"line_id": lid, "kind": "RANGE",
                      "candidate": {"D": ln["candidate_D_m"], "L": ln["candidate_L_m"], "value": ln["candidate_value_m3"]},
                      "range": {"low": round(b * lo_d * lo_l, 6), "high": round(b * hi_d * hi_l, 6),
                                "low_basis": f"{b} x {lo_d} x {lo_l} (column 1EC face reading, 'less than 5 m')",
                                "high_basis": f"{b} x {hi_d} x {hi_l} (band end reading, 'more than 5 m')"},
                      "cause": (f"run {r['run']}: span {lo_l} m (face of column 1EC) or {hi_l} m (band end) by reading: "
                                f"ST p.13 titles 'less than 5 m' 30 x 40 or 'more than 5 m' 30 x 60; and beam(s) "
                                f"{r['d33_tees']} land on it (D-33); a picked end of a printed range is not a value"),
                      "items": ["D-33", "T-141 GAP_TO_COLUMN reading"], "source_tasks": ["T-426"]})
    for lid in sorted(HOLD_BLANK):
        ln = lines[lid]
        holds.append({"line_id": lid, "kind": "BLANK",
                      "candidate": {"D": ln["candidate_D_m"], "L": ln["candidate_L_m"], "value": ln["candidate_value_m3"]},
                      "range": None,
                      "cause": ("0.10 m sliver of the annex exterior arc run: no printed section (annex exterior depth "
                                "D-35 source CONFLICT); the sliver's ownership UNRESOLVED (T-416)"),
                      "items": ["D-35"], "source_tasks": ["T-426", "T-416"]})
    return {"schema": "URBAN_V3040_INPUTS_V1", "project_id": project_id,
            "sources": [SOURCES["T-426"], SOURCES["T-416"]], "splits": splits, "holds": holds}


if __name__ == "__main__":
    doc = build(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({"splits": [(s["line_id"], [(r["run"], r["spans"], r["loaded"]) for r in s["runs"]])
                                 for s in doc["splits"]],
                      "holds": [(h["line_id"], h["kind"], h["range"] and (h["range"]["low"], h["range"]["high"]))
                                for h in doc["holds"]]}, indent=1))
