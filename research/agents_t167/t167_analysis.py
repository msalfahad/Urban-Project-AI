"""T-167 read-only analysis of the runs (every input is a run directory outside the repository; printed: item codes,
units, states and quantities only).

    python3 -I research/agents_t167/t167_analysis.py --full <T-151 run dir, M4 profile> \
        --restricted <T-151 run dir, profile_st7757_q17a.json> --single KEY=<T-151 run dir, M4 minus KEY> ... \
        [--v304 <v304_run.py out dir>] [--spec ID=<release_baseline out dir> ...] [--json <file>]

1. ablation: per removed profile value (and for the restricted set), the lines whose quantity state moves, at two
   levels: the route G base of the candidate (BOQ_LINES.json = the V2.13 base run) and the V3.0.3 candidate
   (V3_0_3_BOQ_LINES.json); per item code and unit: lines, the full-profile released quantity, the state they move to;
   base lines that move but carry no quantity in V3.0.3 (superseded by a verified hand ledger) are counted apart;
2. V3.0.4 (when given): identity, held lines by cause, totals moved per item code and unit;
3. specs (when given): the 8 figure families of T-165 side by side from the BASELINE_MANIFEST.json of each spec run.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v304 as A304      # noqa: E402

QTY = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
FAMILIES = ("STR.CONC.BLINDING", "STR.CONC.COLUMN", "STR.CONC.GROUND_BEAM", "STR.CONC.GROUND_SLAB", "STR.CONC.NECK",
            "STR.CONC.SLAB", "STR.CONC.STAIR", "STR.REBAR")


def lines(p):
    x = json.loads(Path(p).read_text(encoding="utf-8"))
    return x["lines"] if isinstance(x, dict) else x


def moved(full, other, v303_full=None):
    """per (item, unit): lines whose quantity state differs; the released quantity in the full run; the states they
    move to; with v303_full, how many of them carry no quantity in V3.0.3."""
    ob = {x["line_id"]: x for x in other}
    na = {x["line_id"] for x in v303_full or () if x["evidence_state"] in ("NOT_APPLICABLE_WITH_EVIDENCE",
                                                                          "EXCLUDED_WITH_REASON")}
    out = collections.defaultdict(lambda: {"lines": 0, "released_full": 0.0, "released_other": 0.0, "to": {},
                                           "superseded_in_v3_0_3": 0, "superseded_released_full": 0.0})
    for x in full:
        o = ob.get(x["line_id"])
        if A304.qstate(o) == A304.qstate(x):
            continue
        k = f"{x['item_code']}|{x['unit']}"
        c = out[k]
        c["lines"] += 1
        rel = x["measured_net"] if x["evidence_state"] in QTY else 0.0
        c["released_full"] += rel or 0.0
        if o is not None and o["evidence_state"] in QTY:
            c["released_other"] += o["measured_net"] or 0.0
        to = "ABSENT" if o is None else o["evidence_state"]
        c["to"][f"{x['evidence_state']}->{to}"] = c["to"].get(f"{x['evidence_state']}->{to}", 0) + 1
        if x["line_id"] in na:
            c["superseded_in_v3_0_3"] += 1
            c["superseded_released_full"] += rel or 0.0
    only = len(set(ob) - {x["line_id"] for x in full})
    return {k: {a: round(b, 3) if isinstance(b, float) else b for a, b in v.items()} for k, v in sorted(out.items())}, only


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", required=True)
    ap.add_argument("--restricted", required=True)
    ap.add_argument("--single", nargs="*", default=[])
    ap.add_argument("--v304")
    ap.add_argument("--spec", nargs="*", default=[])
    ap.add_argument("--json")
    a = ap.parse_args(argv)
    full = Path(a.full) / "v303"
    fb, f3 = lines(full / "BOQ_LINES.json"), lines(full / "V3_0_3_BOQ_LINES.json")
    rep = {"ablation": {}}
    for name, d in [("RESTRICTED", a.restricted)] + [tuple(s.split("=", 1)) for s in a.single]:
        d = Path(d) / "v303"
        mb, ob = moved(fb, lines(d / "BOQ_LINES.json"), f3)
        m3, o3 = moved(f3, lines(d / "V3_0_3_BOQ_LINES.json"))
        rep["ablation"][name] = {"base": mb, "base_only_in_ablation": ob, "v3_0_3": m3, "v3_0_3_only_in_ablation": o3}
        print(f"== {name}")
        for lvl, m, o in (("base", mb, ob), ("V3.0.3", m3, o3)):
            for k, v in m.items():
                print(f"  {lvl:6s} {k:24s} {v}")
            print(f"  {lvl:6s} lines only in the ablation run: {o}")
    if a.v304:
        run = json.loads((Path(a.v304) / "v304" / "V3_0_4_RUN.json").read_text(encoding="utf-8"))
        lg = run["piece_logs"][0]
        rep["v304"] = {"identity": run["identity"], "evidence_status_counts": run["evidence_status_counts"],
                       "by_cause": lg.get("by_cause"), "restricted_only": len(lg.get("restricted_only") or ()),
                       "no_quantity_in_v3_0_3": len(lg.get("no_quantity_in_v3_0_3") or ()),
                       "totals_moved_by_code": run["totals_moved_by_code"]}
        print("== V3.0.4", json.dumps(rep["v304"], indent=1))
    if a.spec:
        rep["specs"] = {}
        for s in a.spec:
            sid, d = s.split("=", 1)
            m = json.loads((Path(d) / "BASELINE_MANIFEST.json").read_text(encoding="utf-8"))
            rep["specs"][sid] = {"status": m.get("status"), "line_count": m["run"]["line_count"],
                                 "boq_lines_csv_sha256": m["run"]["outputs_sha256"].get("BOQ_LINES.csv"),
                                 "engine": m.get("engine"),
                                 "figures": {f"{r['item_code']}|{r['unit']}": r for r in m.get("per_code") or ()
                                             if r["item_code"] in FAMILIES}}
        print("== specs")
        for fam in FAMILIES:
            row = []
            for sid, v in rep["specs"].items():
                r = next((x for k, x in v["figures"].items() if k.startswith(fam + "|")), None)
                row.append(f"{sid}: " + ("absent" if r is None else
                                         f"{r['lines']} l, rel {r['released_lines']} = {r['released_qty']}, held "
                                         f"{r['held_lines']} [{r['held_low']} .. {r['held_high']}]"))
            print(f"  {fam:22s} | " + " | ".join(row))
    if a.json:
        Path(a.json).write_text(json.dumps(rep, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    main()
