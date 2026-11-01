"""T-430: the package summary and the downgrade-only PROPOSAL for the four D-34 short runs, from a finished
research/agents_t430/v3040_run.py run (values, ids and states only; no coordinate, no drawing text).

    python3 -I research/agents_t430/t430_summary.py <run>/v3040 [--write]

Writes (with --write) research/agents_t430/summary_t430.json and research/agents_t430/DOWNGRADE_PROPOSAL_T430.json.
The proposal is NOT a downgrade record: only the Checker issues one (owner 2026-10-24 23:57); it is bound to the four
lines' content in V3.0.40 with the export's own LINE_CONTENT_V1 hash (tools/boq_export_v1.line_content_sha256).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from tools import boq_export_v1 as EX  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
import t430_inputs as TI  # noqa: E402

GB = "STR.CONC.GROUND_BEAM"
D34 = ["L-0bb78accf8c0a0fbdbaf", "L-0e852cca42fb8b765c58", "L-1487bdda099006e0c4ba", "L-c0b7102a36344a0349f5"]
VALUED = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _gb(lines):
    v = [x for x in lines if x["item_code"] == GB and x["evidence_state"] in VALUED]
    return {"lines": sum(1 for x in lines if x["item_code"] == GB), "valued_lines": len(v),
            "valued_m3": round(sum(x["measured_net"] for x in v), 6),
            "held_lines": sum(1 for x in lines if x["item_code"] == GB and x["evidence_state"] not in VALUED)}


def proposal(l40):
    by = {x["line_id"]: x for x in l40}
    census = {x["line_id"]: x for x in json.loads(TI.CENSUS.read_text(encoding="utf-8"))["lines"]}
    own = [by[i] for i in D34]
    hi = lo = 0.0
    for ln in own:
        c = census[ln["line_id"]]
        if ln["evidence_state"] not in VALUED or abs(ln["measured_net"] - c["candidate_value_m3"]) > 1.5e-6:
            raise SystemExit(f"{ln['line_id']}: not the census value (stale)")
        (r,) = c["runs"]
        if r["section_status"] != "RANGE" or sorted(r["printed_D_m"]) != [0.3, 0.4]:
            raise SystemExit(f"{ln['line_id']}: not a D-34 pair")
        hi += ln["measured_net"]
        lo += c["candidate_b_m"] * 0.3 * c["candidate_L_m"]
    return {"schema": "URBAN_T430_DOWNGRADE_PROPOSAL_V1",
            "proposal_id": "DGP-T430-GB-D34-SHORT",
            "issued_by": "PROPOSAL (Worker 3, T-430, from finding F-T426-1 accepted at the T-426 Gate A): the Checker "
                         "issues or refuses; never a promotion",
            "extends": "DG-a31a0d7e9dd564ad (V3.0.29 DOWNGRADES.json; the same D-34 reason with the titles swapped)",
            "candidate_version": "ARCH_TAKEOFF_V3.0.40", "binding": EX.LINE_BINDING,
            "line_content_sha256": EX.line_content_sha256(own), "line_ids": sorted(D34), "unit": "m3",
            "engine_qty": round(hi, 6), "audit_range_m3": [round(lo, 6), round(hi, 6)],
            "basis_label": "UNSUPPORTED BASIS", "proposed_state": "HELD",
            "evidence": [{"sheet": "ST7757.pdf p.13", "printed_value": "ground-beam sections titled 'Less than 5m length' "
                          "30 x 40 and 'Less than 2.5m length' 30 x 30; no precedence printed"},
                         {"sheet": "research/agents_t426/CENSUS_T426.json", "printed_value": "spans 2.325 / 2.400 / "
                          "2.450 / 2.4668 (2.4269) m on every frame: both titles hold literally (INSIDE_RANGE)"}],
            "reason": ("UNSUPPORTED BASIS: each of the 4 ground-beam lines shows the depth of the ST p.13 section titled "
                       "'less than 5m length' (0.40) as its value although the 'less than 2.5m length' title (0.30) also "
                       "holds literally on its span; the sheet prints no precedence (D-34, designer item RFI S08-S11 "
                       "group). DG-a31a0d7e holds the 9 lines that show the other end of the same pair; these 4 were left "
                       "out (F-T426-1). The lines would be HELD with the audit range beside; candidate and released V2.9 "
                       "unchanged."),
            "resolved": False}


def summary(run):
    l39 = json.loads((run / "V3_0_39_BOQ_LINES.json").read_text(encoding="utf-8"))
    l40 = json.loads((run / "V3_0_40_BOQ_LINES.json").read_text(encoding="utf-8"))
    rj = json.loads((run / "V3_0_40_RUN.json").read_text(encoding="utf-8"))
    led = json.loads((run / "V3_0_40_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    rows = [{"line_id": r["line_id"], "element_id": r["element_id"], "action": r["action"], "change": r["change"],
             "run": r["run"], "v2_9": r["before_released_v2_9"], "v3_0_39": r["before_v3_0_39"],
             "v3_0_40": r["after_v3_0_40"], "evidence_status": r["evidence_status"],
             "beside": (r["record"] or {}).get("beside")} for r in led["rows"]]
    t39, t40 = A304.code_totals(l39), A304.code_totals(l40)
    return {"schema": "URBAN_T430_SUMMARY_V1",
            "files_sha256": {n: _sha(run / n) for n in ("V3_0_39_BOQ_LINES.json", "V3_0_40_BOQ_LINES.json",
                                                         "V3_0_40_INTEGRATION_LEDGER.json", "V3_0_40_DIFF.csv",
                                                         "V3_0_40_RUN.json")},
            "lines": {"v3_0_39": len(l39), "v3_0_40": len(l40)}, "identity": {k: v for k, v in rj["identity"].items()
                                                                             if k in ("replaced", "added",
                                                                                      "outside_rows",
                                                                                      "outside_rows_identical_to_v3_0_39",
                                                                                      "outside_rows_sha256", "diff",
                                                                                      "gb_runs")},
            "ground_beam": {"v3_0_39": _gb(l39), "v3_0_40": _gb(l40)},
            "totals_moved_by_code": rj["totals_moved_by_code"],
            "code_totals_other_than_gb_identical": all(t39.get(k) == t40.get(k) for k in set(t39) | set(t40)
                                                       if not k.startswith(GB)),
            "rows": rows, "piece_log": {k: v for k, v in rj["piece_logs"][0].items() if k != "sources"}}


def main(argv):
    run = Path(argv[1]).resolve()
    s = summary(run)
    l40 = json.loads((run / "V3_0_40_BOQ_LINES.json").read_text(encoding="utf-8"))
    p = proposal(l40)
    s["downgrade_proposal"] = {k: p[k] for k in ("proposal_id", "line_ids", "line_content_sha256", "engine_qty",
                                                 "audit_range_m3")}
    if "--write" in argv:
        (HERE / "summary_t430.json").write_text(json.dumps(s, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        (HERE / "DOWNGRADE_PROPOSAL_T430.json").write_text(json.dumps(p, indent=1, sort_keys=True) + "\n",
                                                           encoding="utf-8")
    print(json.dumps({"lines": s["lines"], "ground_beam": s["ground_beam"], "diff": s["identity"]["diff"],
                      "moved": s["totals_moved_by_code"], "proposal": s["downgrade_proposal"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
