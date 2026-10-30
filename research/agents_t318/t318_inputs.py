"""T-318: the URBAN_V3027_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.27 (engine.source.arch_v3027), built ONLY from
the two Checker-merged slab bar-end ledgers, each file pinned by sha256 (an edited ledger stops the build):

  research/agents_t307/LANE_I_CONSUMER_T307.csv   T-307 (MERGED c48f7062, Verifier 2026-10-26 05:56 UTC Gate A PASS):
      per suspended-slab DEVELOPMENT / ANCHORAGE line (98): every bottom-bar end classified by its support from the
      p.15 TYP. SLAB ON BEAMS DETAIL; proposed status NOT_APPLICABLE_WITH_EVIDENCE (every end continuous: no
      development drawn), BOUND_PART_WITH_HELD (the drawn straight part w - 0.040 at edge-beam ends, count A .. B; the
      up-turn legs and the step / irregular / opening ends HELD) or HELD (no edge-beam end);
  research/agents_t316/TOP_LINE_LEDGER_T316.csv   T-316 (MERGED ebe99ecf, Verifier 2026-10-28 22:18 UTC Gate A PASS):
      per TOP BARS OVER SUPPORTS line (98): status, the p.15 valued part (with F-T316-01 the drawn part across the
      edge beam as [w - 0.040, w] and F-T316-02 the clear-span cap R316-10 applied), note-2 readings, held ends;
  research/agents_t316/TOP_GROUP_LEDGER_T316.csv  the same ledger support group by support group (2,321 rows): the
      note-2 readings are split here between the valued groups and the held groups, by SUMMING the ledger's own rows
      (note2_i_m x n_bars at count A; (note2_ii_m + over_band_m at continuous groups) x n_bars at count B); the
      split is accepted only when the sum over ALL groups reproduces the line ledger's note2_i_A_kg and
      note2_ii_cross_B_kg within the 3 dp storage (0.0015 kg). Nothing is re-measured.

Nothing is typed: every figure is read from the merged files. Units: kg (d10 bar, d^2 / 162 kg/m: the candidate's own
unit mass); t only at the export boundary (OWNER_RULE_REBAR_2026-10-24 s.1).

    python3 -I research/agents_t318/t318_inputs.py          # prints the per-status counts and kg
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEV = ROOT / "research/agents_t307/LANE_I_CONSUMER_T307.csv"
TOPL = ROOT / "research/agents_t316/TOP_LINE_LEDGER_T316.csv"
TOPG = ROOT / "research/agents_t316/TOP_GROUP_LEDGER_T316.csv"
PINS = {DEV: "bd8eb5ef12dbef873feb2564e78cc80e0b4e0e26b525b86a42ff17b98d839d6c",
        TOPL: "5dee5cdc16e6af11c5b2700821ad423bfa2d751d56dd206b9dd9a83a0a0efee5",
        TOPG: "94bb89f1bd75bde385cec12d5aba003c9cbc02a0789e713a581c7b9f6de232d0"}
SOURCES = {
    "T-307": {"merge_commit": "c48f706248ee012906cdc4c78dd27065388d367a",
              "checker_run": "Verifier 2026-10-26 05:56 UTC: T-307 Gate A PASS, MERGED c48f7062 (bar ends classified "
                             "by support from the p.15 typical detail; F-T306-01 confirmed end by end)"},
    "T-316": {"merge_commit": "ebe99ecfcfdcc2f2301d88a4bb26283a46cde6da",
              "checker_run": "Verifier 2026-10-28 22:18 UTC: T-316 Gate A PASS, MERGED ebe99ecf (top-bar extent by "
                             "support from p.15; F-T316-01 across-beam part, F-T316-02 clear-span cap)"},
}
U10 = 100.0 / 162.0          # kg/m of a d10 bar (d^2 / 162), the candidate lines' own unit mass
TOL_3DP = 0.0015
DEV_POP, TOP_POP = "DEVELOPMENT / ANCHORAGE", "TOP BARS OVER SUPPORTS"
VALUED_GROUPS = ("DRAWING_DERIVED", "DRAWING_DERIVED_WITH_HELD")


class PinError(ValueError):
    pass


def _pinned(p):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != PINS[p]:
        raise PinError(f"{p.relative_to(ROOT)}: sha256 {h[:8]} is not the merged {PINS[p][:8]} (edited ledger)")
    return h


def _rows(p):
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _f(v):
    return float(v) if v not in (None, "") else None


def _z(v):
    return float(v) if v not in (None, "") else 0.0


def dev_lines():
    out = []
    for r in _rows(DEV):
        if r["population"] != DEV_POP:
            continue
        st = r["proposed_status"]
        rec = {"line_id": r["line_id"], "element": r["element"], "direction": r["direction"], "population": DEV_POP,
               "status": st, "before": {"low": _f(r["candidate_low_kg"]), "high": _f(r["candidate_high_kg"])},
               "ends_A": r["ends_A"], "ends_B": r["ends_B"], "held_items": r["held_items"], "basis": r["basis"],
               "source_task": "T-307"}
        if st == "BOUND_PART_WITH_HELD":
            rec["valued"] = {"low": _f(r["valued_low_kg"]), "high": _f(r["valued_high_kg"]),
                             "basis": "p.15 straight part w - 0.040 m past the edge beam's inner face (DRAWING-DERIVED "
                                      "length), count A .. B (BOUND)"}
        out.append(rec)
    return out


def top_lines():
    groups = defaultdict(list)
    for g in _rows(TOPG):
        groups[g["line_id"]].append(g)
    out = []
    for r in _rows(TOPL):
        lid = r["line_id"]
        gs = groups.get(lid) or []
        tot = {"i_A": 0.0, "ii_B": 0.0}
        val = {"i_A": 0.0, "ii_B": 0.0}
        held_groups, unresolved = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
        legs = [0, 0]
        for g in gs:
            n = _z(g["n_bars"])
            k = 0 if g["reading"] == "A" else 1
            valued = g["status"] in VALUED_GROUPS
            if g["reading"] == "A":
                m = _z(g["note2_i_m"]) * n
                tot["i_A"] += m
                val["i_A"] += m if valued else 0.0
            else:
                m = (_z(g["note2_ii_m"]) + (_z(g["over_band_m"]) if g["support"] == "CONTINUOUS" else 0.0)) * n
                tot["ii_B"] += m
                val["ii_B"] += m if valued else 0.0
            if g["status"] == "HELD":
                held_groups[g["held"] or g["support"]][k] += int(n)
            if g["support"] == "EDGE_BEAM" and valued:
                legs[k] += int(n)
            if g["unresolved"]:
                unresolved[g["unresolved"]][k] += int(n)
        for key, col in (("i_A", "note2_i_A_kg"), ("ii_B", "note2_ii_cross_B_kg")):
            if abs(tot[key] * U10 - float(r[col])) > TOL_3DP:
                raise ValueError(f"{lid}: the group ledger's note-2 {key} {tot[key] * U10:.4f} kg does not reproduce the "
                                 f"line ledger's {r[col]} (split refused)")
        st = r["proposed_status"]
        rec = {"line_id": lid, "element": r["element"], "direction": r["direction"], "population": TOP_POP,
               "status": st, "before": {"low": _f(r["candidate_low_kg"]), "high": _f(r["candidate_high_kg"])},
               "t306_path": r["t306_path"], "ends_A": r["ends_A"], "ends_B": r["ends_B"],
               "held_items": r["held_items"], "basis": r["basis"], "source_task": "T-316",
               "beyond_span_kg": {"A": _f(r["t152_p15_beyond_span_A_kg"]), "B": _f(r["t152_p15_beyond_span_B_kg"])},
               "note2_all": {"low": round(tot["i_A"] * U10, 6), "high": round(tot["ii_B"] * U10, 6)},
               "held_ends": {k: list(v) for k, v in sorted(held_groups.items())},
               "unresolved_ends": {k: list(v) for k, v in sorted(unresolved.items())},
               "hook_legs_held": legs if any(legs) else None}
        if r["p15_valued_low_kg"] != "":
            if held_groups:   # valued groups only: the ledger rows summed (closure asserted above)
                rec["note2_valued"] = {"low": round(val["i_A"] * U10, 6), "high": round(val["ii_B"] * U10, 6)}
            else:             # every group valued: the line ledger's own figures (no re-rounding)
                rec["note2_valued"] = {"low": float(r["note2_i_A_kg"]), "high": float(r["note2_ii_cross_B_kg"])}
            rec["p15_valued"] = {"low": float(r["p15_valued_low_kg"]), "high": float(r["p15_valued_high_kg"])}
        out.append(rec)
    return out


def build(project_id=None):
    hashes = {str(p.relative_to(ROOT)): _pinned(p) for p in PINS}
    return {"schema": "URBAN_V3027_INPUTS_V1", "project_id": project_id, "task": "T-318",
            "sources": [{"task": t, "file": f, "sha256": hashes[f], **SOURCES[t]}
                        for t, f in (("T-307", str(DEV.relative_to(ROOT))), ("T-316", str(TOPL.relative_to(ROOT))),
                                     ("T-316", str(TOPG.relative_to(ROOT))))],
            "unit": "kg", "unit_mass_kg_per_m": {"10": U10},
            "lines": dev_lines() + top_lines()}


def main():
    d = build()
    from collections import Counter
    c = Counter((x["population"], x["status"]) for x in d["lines"])
    print(json.dumps({f"{k[0]} | {k[1]}": v for k, v in sorted(c.items())}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
