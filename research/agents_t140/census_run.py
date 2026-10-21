"""T-140 read-only runs: census V1 (1.0.0 map) and census V2 (BOQ_FAMILY_MASTER 1.1.0) of the released ARCH_TAKEOFF_V2.9
+ route G and of the opt-in ARCH_TAKEOFF_V3.0.1 candidate on the development villa's Drive copies. Every output goes
to --out (outside the repository); the tables carry codes, units, states and quantities only (no names, no
coordinates).

    # 1. the two runs (the released one exactly as 1.1.0 'run_evidence.released_run' records it: no facts, no profile;
    #    the candidate as research/agents_t133/v301_run.py, plus the route G profile, Gate B defect D1)
    python3 -I research/agents_t140/census_run.py runs <plan.dxf> <structural.dxf> --profile <profile.json> --out <dir>
    # 2. census V1 and V2 of each run folder (a folder holding BOQ_LINES.json, MATERIAL_RESULTS.json, COVERAGE.json
    #    and structural/FAMILY_COVERAGE.csv)
    python3 -I research/agents_t140/census_run.py census <dir>/released=released <dir>/cand/v301=candidate \
        --out <dir>/census
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

CONV = ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"


def runs(a):
    sys.path.insert(0, str(ROOT / "research" / "agents_t131"))
    import alsenan_v30_run as T131
    from tools import urban_boq_m9 as M
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    M.main(["arch", "--drawings", a.plan, "--out", str(out / "released"), "--method", "ARCH_TAKEOFF_V2.9",
            "--structural", a.structural, "--conventions", str(CONV), "--no-svg"])
    c = out / "cand"
    c.mkdir(exist_ok=True)
    (c / "facts.json").write_text(json.dumps(T131.facts(Path(a.plan).name), ensure_ascii=False), encoding="utf-8")
    common = ["--drawings", a.plan, "--structural", a.structural, "--conventions", str(T131.CONV), "--profile",
              a.profile, "--facts", str(c / "facts.json"), "--project", T131.PID, "--no-svg"]
    M.main(["arch", "--out", str(c / "v29"), "--method", "ARCH_TAKEOFF_V2.9"] + common)
    extra, hist = ["--v30-released", str(c / "v29" / "BOQ_LINES.json")], []
    for m in ("ARCH_TAKEOFF_V2.10", "ARCH_TAKEOFF_V2.11", "ARCH_TAKEOFF_V2.12"):
        tag = "v" + m.split("_V")[-1].replace(".", "")
        M.main(["arch", "--out", str(c / tag), "--method", m] + common)
        hist.append(f"{m}={c / tag / 'BOQ_LINES.json'}")
    (c / "decisions.json").write_text(json.dumps(T131.DECISIONS), encoding="utf-8")
    extra += ["--v30-history"] + hist + ["--v30-decisions", str(c / "decisions.json")]
    M.main(["arch", "--out", str(c / "v301"), "--method", "ARCH_TAKEOFF_V3.0.1"] + common + extra)


def load_run(d, lines_file="BOQ_LINES.json"):
    d = Path(d)
    lines = json.loads((d / lines_file).read_text(encoding="utf-8"))
    lines = lines["lines"] if isinstance(lines, dict) else lines
    mats = json.loads((d / "MATERIAL_RESULTS.json").read_text(encoding="utf-8"))["results"]
    fc = d / "structural" / "FAMILY_COVERAGE.csv"
    cov = list(csv.DictReader(fc.open(encoding="utf-8"))) if fc.exists() else None
    v1_written = json.loads((d / "COVERAGE.json").read_text(encoding="utf-8"))["families"]
    return lines, mats, cov, v1_written


def fmt_units(by_unit):
    parts = []
    for u, c in by_unit.items():
        s = f"{u}: "
        s += f"found {c['found_lines']} = {c['found_qty']:.3f}" if c["found_lines"] else "found 0"
        if c["held_lines"]:
            r = c["held_range"]
            rs = (f" (bounded {c['held_bounded_lines']}: {r['low']:.3f} .. {r['high']:.3f}"
                  f"{'' if r['complete'] else ', +' + str(c['held_unbounded_lines']) + ' unbounded'})") if r else \
                f" ({c['held_unbounded_lines']} unbounded)"
            s += f"; held {c['held_lines']} UNKNOWN{rs}"
        if c["excluded_lines"]:
            s += f"; excluded {c['excluded_lines']}"
        if c["not_summed_lines"]:
            s += f"; not summed {c['not_summed_lines']}"
        parts.append(s)
    return " | ".join(parts) or "-"


def per_code(lines, code, unit):
    """the T-130 build's per-code figures recomputed from the run's lines (released = quantity states)."""
    from engine.source import boq_line as BL
    ls = [ln for ln in lines if ln["item_code"] == code and ln["unit"] == unit]
    q = [ln for ln in ls if ln["evidence_state"] in BL.QUANTITY_STATES]
    b = [ln for ln in ls if ln["evidence_state"] == "BOUNDED_EXPOSURE"]
    h = [ln for ln in ls if ln["evidence_state"] in ("BOUNDED_EXPOSURE", "BLOCKED_RFI")]
    na = [ln for ln in ls if ln["evidence_state"] in ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE")]
    return {"lines": len(ls), "released_lines": len(q), "released_qty": round(sum(ln["measured_net"] for ln in q), 3),
            "held_lines": len(h),
            "held_bounded_low": round(sum(ln["bounded_range"]["low"] for ln in b), 3) if b else None,
            "held_bounded_high": round(sum(ln["bounded_range"]["high"] for ln in b), 3) if b else None,
            "not_applicable_lines": len(na)}


def crosscheck(master, rows, lines):
    """census V2 per family and unit vs the figures 1.1.0 recorded for the released run (development_villa)."""
    out = []
    for f in master["families"]:
        rec = (f.get("development_villa") or {}).get("released_run") or []
        row = next(r for r in rows if r["code"] == f["code"])
        for e in rec:
            mine = per_code(lines, e["item_code"], e["unit"])
            want = {k: e.get(k) for k in mine}
            ok = all((mine[k] is None and want[k] is None) or (mine[k] is not None and want[k] is not None and
                     abs(mine[k] - want[k]) <= 5e-4) for k in mine)
            out.append({"family": f["code"], "item_code": e["item_code"], "unit": e["unit"], "match": ok,
                        "recorded": want, "recomputed": mine, "census_v2_state": row["run_state"]})
    return out


def census(a):
    from engine.source import coverage_census as CS1
    from engine.source import coverage_census_v2 as CS2
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    master = CS2.load_master()
    for spec in a.dirs:
        d, _, kind = spec.partition("=")
        kind, _, lines_file = kind.partition("@")
        lines_file = lines_file or "BOQ_LINES.json"
        name = Path(d).name + ("" if lines_file == "BOQ_LINES.json" else "_" + lines_file.split("_BOQ_LINES")[0])
        lines, mats, cov, v1_written = load_run(d, lines_file)
        has_st = any(ln["item_code"].startswith("STR.") for ln in lines)
        v1 = CS1.census(lines, family_coverage=cov, structural_run=has_st or cov is not None, rooms_run=False,
                        material_results=mats, arch_run=True)
        # the census inputs read back from the folder reproduce the census the run itself wrote
        # (the run writes its census of BOQ_LINES.json only; another lines file has no written census to compare)
        same_v1 = ([(r["code"], r["run_state"], r["lines"]) for r in v1] ==
                   [(r["code"], r["run_state"], r["lines"]) for r in v1_written]) if lines_file == "BOQ_LINES.json" \
            else "n/a"
        rows, meta = CS2.census(lines, master=master, family_coverage=cov, material_results=mats,
                                run_kind=kind or None)
        cmp = {c["code"]: c for c in CS2.compare(v1, rows)}
        res = {"run": str(name), "run_kind": kind or None, "lines": len(lines), "v1_reproduced_from_folder": same_v1,
               "meta": meta,
               "summary_v1": CS1.summary(v1), "summary_v2": CS2.summary(rows, meta), "rows": rows,
               "compare": list(cmp.values())}
        if kind == "released":
            res["crosscheck_1_1_0_released_run"] = cc = crosscheck(master, rows, lines)
            print("1.1.0 released-run figures reproduced:", sum(c["match"] for c in cc), "/", len(cc),
                  [(c["family"], c["item_code"]) for c in cc if not c["match"]])
        (out / f"{name}_CENSUS_V2.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        md = [f"# census V2 of {name}: {len(lines)} lines; V1 reproduced from the folder: {same_v1}", "",
              f"V1 {res['summary_v1']['by_run_state']}", f"V2 {res['summary_v2']['by_run_state']}",
              f"codes without family {meta['codes_without_family']}; unowned {meta['unowned_codes']}", "",
              "| family | unit | capability | V1 state (lines) | V2 state (lines) | quantity per unit | flags |",
              "|---|---|---|---|---|---|---|"]
        for r in rows:
            c = cmp[r["code"]]
            md.append(f"| {r['code']} | {r['family_unit']} | {r['capability']} | {c['v1_state']} ({c['v1_lines']}) | "
                      f"{r['run_state']} ({r['lines']}) | {fmt_units(r['by_unit'])} | {'; '.join(r['flags']) or '-'} |")
        (out / f"{name}_CENSUS_V2.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print(name, len(lines), "v1 reproduced:", same_v1, res["summary_v2"]["by_run_state"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("runs")
    r.add_argument("plan")
    r.add_argument("structural")
    r.add_argument("--profile", required=True)
    r.add_argument("--out", required=True)
    c = sub.add_parser("census")
    c.add_argument("dirs", nargs="+", help="<run folder>[=released|candidate][@<lines file>]")
    c.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    runs(a) if a.cmd == "runs" else census(a)


if __name__ == "__main__":
    main()
