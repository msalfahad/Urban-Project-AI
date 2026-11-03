"""T-491 Alsenan site preparation check: applies SITE_PREPARATION_V1 to the committed values-only input and writes
SITE_PREP_T491.csv, summary.json and the PROPOSED T-471 completeness-matrix rows (T471_PROPOSAL_T491.json).
Run: python3 -I research/agents_t491/t491_alsenan_check.py [--write]"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import site_preparation_v1 as S  # noqa: E402

INPUT = HERE / "ALSENAN_SITE_PREP_INPUT.json"


def t471_proposal(rows):
    """Rows for the NEXT T-471 matrix / EIMP register version (PROPOSED here; the registry file belongs to T-350 r3)."""
    out = [{
        "component_id": "C-B1-01",
        "change": "applicability NOT_APPLICABLE -> APPLICABLE (owner 2026-11-02 17:20 (6) puts site clearance in scope "
                  "for every villa; R-T491-CLR-1 supersedes the T-357 R-CLR-1 scope outcome, not its convention-extent "
                  "refusal)",
        "formula": "shoelace area of the printed plot boundary unless a clearance limit is printed",
        "unit": "m2",
    }]
    for r in rows:
        if r["family"] != "B1-07":
            continue
        out.append({
            "component_id": f"C-B1-07-{r['component']}",
            "change": "new component (owner 2026-11-02 17:20 (6)); listed present or HELD, no price",
            "formula": r["formula"],
            "unit": r["unit"],
            "status_this_villa": r["status"],
            "missing": r["missing"],
        })
    return out


def main(write=False):
    inp = json.loads(INPUT.read_text(encoding="utf-8"))
    rows = S.site_preparation(inp)
    by = {r["component"]: r for r in rows}
    summary = {
        "method": "SITE_PREPARATION_V1 (research, unwired)",
        "rules": S.RULES_SOURCE,
        "plot_area_m2": round(S.shoelace_area(inp["plot_polygon"], inp["unit"]), 6),
        "boundary_lm": round(S.perimeter(inp["plot_polygon"], inp["unit"]), 6),
        "dxf_sides_sum_lm": round(sum(s["sum_m"] for s in inp["boundary_sides_dxf"]), 6),
        "quantified_not_released": {k: r["quantity"] for k, r in by.items() if r["quantity"] is not None},
        "held": sorted(k for k, r in by.items() if r["status"] == "HELD"),
        "counts": {s: sum(1 for r in rows if r["status"] == s) for s in sorted({r["status"] for r in rows})},
    }
    proposal = t471_proposal(rows)
    if write:
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: (";".join(v) if isinstance(v, list) else v) for k, v in r.items()})
        (HERE / "SITE_PREP_T491.csv").write_text(buf.getvalue(), encoding="utf-8")
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        (HERE / "T471_PROPOSAL_T491.json").write_text(json.dumps(proposal, indent=1) + "\n", encoding="utf-8")
    return rows, summary, proposal


if __name__ == "__main__":
    rows, summary, _ = main(write="--write" in sys.argv)
    print(json.dumps(summary, indent=1, sort_keys=True))
