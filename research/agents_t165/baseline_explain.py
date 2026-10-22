"""T-165 read-only explanation of the two "released V2.9 + route G" runs on the development villa (Drive copies only;
every output goes to --out, outside the repository; tables carry item codes, units, states and quantities only).

    # 1. the two pinned baselines (tools/release_baseline.py; refuses on any sha difference)
    python3 -I tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_NO_PROFILE.json \
        --plan <plan.dxf> --structural <structural.dxf> --out <dir>/V29_ROUTEG_NO_PROFILE
    python3 -I tools/release_baseline.py run research/agents_t165/baselines/V29_ROUTEG_PROFILED.json \
        --plan <plan.dxf> --structural <structural.dxf> --out <dir>/V29_ROUTEG_PROFILED
    # 2. the cause of each difference: the profiled baseline once per profile value, with that one value removed
    python3 -I research/agents_t165/baseline_explain.py ablate <plan.dxf> <structural.dxf> --out <dir>/ablation \
        --pair GF_FLOOR_LEVEL_M,OUTER_GROUND_LEVEL_M
    # 3. the side-by-side table and the attribution of every differing figure to profile values
    python3 -I research/agents_t165/baseline_explain.py table <dir>/V29_ROUTEG_NO_PROFILE <dir>/V29_ROUTEG_PROFILED \
        --ablation <dir>/ablation [--json <dir>/explain.json]

Attribution rule: a profile value CAUSES a figure difference when removing that one value from the profiled run moves
that figure (lines, released lines, released quantity, held lines or the held range of the item code) away from the
profiled run. A figure no single removal moves is reported as NO_SINGLE_VALUE (it needs two values together)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import release_baseline as RB  # noqa: E402

BASE = Path(__file__).resolve().parent / "baselines"
FIG = ("lines", "released_lines", "released_qty", "held_lines", "held_low", "held_high")


def per_code(run_dir):
    raw = json.loads((Path(run_dir) / "BOQ_LINES.json").read_text(encoding="utf-8"))
    lines = raw["lines"] if isinstance(raw, dict) else raw
    return {(r["item_code"], r["unit"]): r for r in RB.per_code(lines)}, lines


def ablate(a):
    spec = json.loads((BASE / "V29_ROUTEG_PROFILED.json").read_text(encoding="utf-8"))
    prof = json.loads((ROOT / spec["profile"]["path"]).read_text(encoding="utf-8"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sets = [[c["id"]] for c in prof["conventions"]] + [x.split(",") for x in (a.pair or ())]
    for drop in sets:
        key = "_AND_".join(drop)
        p = out / f"profile_minus_{key}.json"
        p.write_text(json.dumps(dict(prof, conventions=[x for x in prof["conventions"] if x["id"] not in drop])),
                     encoding="utf-8")
        s = dict(spec, baseline_id=f"ABLATION_MINUS_{key}", profile={"path": str(p), "sha256": RB.sha256_file(p)})
        s.pop("expected", None)
        s.pop("description", None)
        sp = out / f"spec_minus_{key}.json"
        sp.write_text(json.dumps(s, indent=1), encoding="utf-8")
        code, m = RB.run(sp, a.plan, a.structural, out / key)
        print(key, code, m["status"], m["run"]["line_count"], flush=True)


def fmt(r):
    if r is None:
        return "absent"
    q = "-" if r["released_qty"] is None else f"{r['released_qty']:.3f}"
    h = f"held {r['held_lines']}"
    if r["held_bounded_lines"]:
        h += f" [{r['held_low']:.3f} .. {r['held_high']:.3f}]"
    return f"{r['lines']} lines; released {r['released_lines']} = {q}; {h}"


def table(a):
    u, lu = per_code(a.no_profile)
    p, lp = per_code(a.profiled)
    rows = []
    for k in sorted(set(u) | set(p)):
        if tuple((u.get(k) or {}).get(f) for f in FIG) != tuple((p.get(k) or {}).get(f) for f in FIG):
            rows.append({"item_code": k[0], "unit": k[1], "no_profile": u.get(k), "profiled": p.get(k), "causes": {}})
    # every non-structural line identical apart from the project id and the line id hash
    strip = lambda x: {kk: v for kk, v in x.items() if kk not in ("line_id", "project")}  # noqa: E731
    nu = [strip(x) for x in lu if not x["item_code"].startswith("STR.")]
    npf = [strip(x) for x in lp if not x["item_code"].startswith("STR.")]
    arch_same = nu == npf
    abl = {}
    if a.ablation:
        for d in sorted(Path(a.ablation).iterdir()):
            if d.is_dir() and (d / "BOQ_LINES.json").is_file():
                abl[d.name] = per_code(d)[0]
        for r in rows:
            k = (r["item_code"], r["unit"])
            for key, pc in abl.items():
                moved = [f for f in FIG if (pc.get(k) or {}).get(f) != (p.get(k) or {}).get(f)]
                if moved:
                    r["causes"][key] = {"moved": moved, "figures_without_it": pc.get(k)}
    print(f"no profile: {len(lu)} lines; profiled: {len(lp)} lines; non-structural lines identical apart from "
          f"project id / line id: {arch_same} ({len(nu)} vs {len(npf)})")
    print(f"{len(rows)} item code / unit figure sets differ")
    for r in rows:
        print(f"\n{r['item_code']} {r['unit']}\n  no profile: {fmt(r['no_profile'])}\n  profiled:   {fmt(r['profiled'])}")
        for key, c in r["causes"].items():
            print(f"    without {key}: {fmt(c['figures_without_it'])}  (moves {', '.join(c['moved'])})")
        if a.ablation and not r["causes"]:
            print("    NO_SINGLE_VALUE")
    if a.json:
        Path(a.json).write_text(json.dumps({"arch_lines_identical": arch_same, "rows": rows}, indent=1,
                                           sort_keys=True, default=str) + "\n", encoding="utf-8")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("ablate")
    x.add_argument("plan")
    x.add_argument("structural")
    x.add_argument("--out", required=True)
    x.add_argument("--pair", action="append", help="also remove these values together, e.g. "
                   "GF_FLOOR_LEVEL_M,OUTER_GROUND_LEVEL_M (repeatable)")
    t = sub.add_parser("table")
    t.add_argument("no_profile")
    t.add_argument("profiled")
    t.add_argument("--ablation")
    t.add_argument("--json")
    a = ap.parse_args(argv)
    return ablate(a) if a.cmd == "ablate" else table(a)


if __name__ == "__main__":
    sys.exit(main())
