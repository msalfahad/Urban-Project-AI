"""T-657 per-neck ledger: the 36 HELD B10-03 STR.CONC.NECK lines of the trial BOQ (T-636 r4, candidate V3.0.58 line
ids) restated from the generic T-167 0.50 .. 2.50 m height to the bounds the structural drawings support
(R-T572-2 low end, R-T657-1 .. 4 high end). Research only: nothing wired, nothing released.

Committed inputs (no drawing is opened here; each printed value is cited to the sheet that prints it):
  trial lines   research/agents_t636/out/TRIAL_BOQ_T636.json (per_line, item STR.CONC.NECK: line ids + candidate range)
  neck bounds   research/agents_t572/out/T572_HELD_BOUNDS.json (mark, position, footing, sections, drawn low end)
  neck input    research/agents_t205/ALSENAN_NECK_INPUT.json (footing H per neck, printed schedule; T-205)
Printed facts added by T-657 (ST7757 PDF, Drive 'Alsenan chalet project', read-only; re-read this run):
  ST p.13 isolated-footing detail: dimension 'LESS THAN 2.5m' from the footing underside (top of the 5 cm screed) up
    to the ground-beam / GF slab line; second detail '(When the level difference between upper ground beam and
    footing is more than 2.5m)' adds a lower ground-beam row. ST p.9 note 1: excavation level not less than 1.5 m below
    the existing plot level; the footing schedule H values equal T-205's (re-read, 17 types). One ground-beam plan,
    one row (no 'lower' beam label in the dxf; T-572 / T-350).

    python3 -I research/agents_t657/t657_necks.py [--write]
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t657_rules as R  # noqa: E402

T636 = RES / "agents_t636" / "out" / "TRIAL_BOQ_T636.json"
T572 = RES / "agents_t572" / "out" / "T572_HELD_BOUNDS.json"
T205 = RES / "agents_t205" / "ALSENAN_NECK_INPUT.json"
OUT = HERE / "out" / "T657_NECK_LEDGER.json"
D = Decimal

MIN_DEPTH = D("1.50")   # ST p.9 note 1 (printed minimum, below EG +-0.00, T-357)
STACK = D("0.17")       # ST p.13: 5 cm screed + 2 cm membrane + 10 cm plain concrete under the footing (T-206 / T-572)
D_MAX = D("2.50")       # ST p.13 'LESS THAN 2.5m' footing underside .. upper ground-beam line (single-row detail)
TOPS = (D("0.95"), D("0.25"))   # drawn neck tops in T-572 (GF column base T-394 / T-214; annex +0.25 T-287)
F10F_H = (D("0.50"), D("0.30"))  # Q-31 C: one outline tagged F10 (0.50) and F (0.30)
LIFT_ITEM = "D-43 lift pit raft depth 'as per lift manufacturer' (ST p.14); D-63 section"
SCENARIO = ("DESIGN_CHANGE_BESIDE: formation deeper than the single-row condition brings the ST p.13 second detail "
            "(lower ground-beam row, drawn on no plan) and needs engineering approval (Q-21 answer C); not in the "
            "drawn neck")


def _trial_lines():
    d = json.loads(T636.read_text(encoding="utf-8"))
    return {x["line_id"]: x for x in d["per_line"] if x.get("item_code") == "STR.CONC.NECK"}


def _h205():
    out = {}
    for n in json.loads(T205.read_text(encoding="utf-8"))["necks"]:
        out[n["outline_handle"]] = n["footing"]
    return out


def ledger():
    trial = _trial_lines()
    h205 = _h205()
    comps = [c for c in json.loads(T572.read_text(encoding="utf-8"))["components"] if c["family"] == "B10 NECK"]
    assert len(comps) == 36 and {c["line_id"] for c in comps} == set(trial), "the 36 neck line ids must agree"
    rows = []
    for c in sorted(comps, key=lambda c: (c["mark"], c["position"])):
        f = h205[c["position"]]
        ft = c["footing"]
        H = F10F_H if ft == "F10|F" else (D(str(f["H"])),)
        assert ft == f["type"] or (ft == "F10|F"), c["position"]
        secs = [D(s) for s in c["section_candidates_m2"]]
        top = D(c["h_low_m"]) - MIN_DEPTH + STACK + max(H)          # back out the drawn top T-572 used
        assert top in TOPS, (c["position"], top)
        pit = ft == "FF"
        hl, hh, lo, hi, why = R.neck_range(top, MIN_DEPTH, STACK, H, secs, D_MAX, one_gb_row_drawn=True,
                                           pit_raft_unprinted=pit)
        assert lo == D(c["low"]), (c["position"], lo, c["low"])     # T-572 low end reproduced
        t = trial[c["line_id"]]
        cand = None if t["held_low"] is None else [str(D(str(t["held_low"])).quantize(R.Q6)),
                                                   str(D(str(t["held_high"])).quantize(R.Q6))]
        flags = [x for x in c["flags"]] + (["SECTION_RANGE_MIN_MAX"] if len(set(secs)) > 1 else [])
        rows.append({
            "line_id": c["line_id"], "element_id": c["element_id"], "mark": c["mark"], "position": c["position"],
            "footing": ft, "footing_H_m": [str(x) for x in H], "section_candidates_m2": [str(x) for x in secs],
            "top_low_m": str(top), "footing_underside_highest_m": str(-(MIN_DEPTH - STACK)),
            "h_low_m": str(hl), "h_high_m": None if hh is None else str(hh),
            "m3_low": str(lo), "m3_high": None if hi is None else str(hi),
            "status": "HELD_BOUNDED_AS_DRAWN" if hi is not None else "HELD_LOWER_ONLY",
            "low_basis": c["low_basis"],
            "high_basis": None if hh is None else (
                f"ST p.13 'LESS THAN 2.5m' footing underside .. upper ground-beam line, one GB row drawn "
                f"(R-T657-1): h <= {D_MAX} - H_min {min(H)} = {hh}; x largest section {max(secs)} m2"),
            "high_item": (why + "; " + LIFT_ITEM) if hh is None else None,
            "high_scenario_beside": SCENARIO if hh is not None else None,
            "candidate_range_generic_T167": cand, "flags": flags})
    return rows


def totals(rows):
    lo = sum((D(r["m3_low"]) for r in rows), D(0))
    hb = [r for r in rows if r["m3_high"] is not None]
    hi_part = sum((D(r["m3_high"]) for r in hb), D(0))
    lo_part = sum((D(r["m3_low"]) for r in hb), D(0))
    cl = sum((D(r["candidate_range_generic_T167"][0]) for r in rows if r["candidate_range_generic_T167"]), D(0))
    ch = sum((D(r["candidate_range_generic_T167"][1]) for r in rows if r["candidate_range_generic_T167"]), D(0))
    lift = [r for r in rows if r["m3_high"] is None]
    return {"lines": len(rows), "valued": 0, "bounded_as_drawn": len(hb), "lower_only": len(lift),
            "family_low_m3": str(lo.quantize(R.Q6)), "family_high_m3": None,
            "family_high_blocked_by": sorted({r["high_item"] for r in lift}),
            "bounded_part": {"lines": len(hb), "low_m3": str(lo_part.quantize(R.Q6)),
                             "high_m3": str(hi_part.quantize(R.Q6))},
            "lift_lower_only_m3": str(sum((D(r["m3_low"]) for r in lift), D(0)).quantize(R.Q6)),
            "before_candidate_generic": {"low_m3": str(cl.quantize(R.Q6)), "high_m3": str(ch.quantize(R.Q6)),
                                         "lines_with_range": sum(1 for r in rows if r["candidate_range_generic_T167"]),
                                         "blank_lines": sum(1 for r in rows if not r["candidate_range_generic_T167"])}}


def build():
    rows = ledger()
    return {"schema": "T657_NECK_LEDGER_V1",
            "candidate": "trial BOQ T-636 r4 per_line (candidate V3.0.58 line ids); NOT RELEASED, nothing wired",
            "datums": {"min_depth_m": str(MIN_DEPTH), "stack_m": str(STACK), "d_max_m": str(D_MAX)},
            "note": "engine figures, bounds and bases only; no freelancer row or count",
            "totals": totals(rows), "necks": rows}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    doc = build()
    if a.write:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(doc["totals"], indent=1))


if __name__ == "__main__":
    main()
