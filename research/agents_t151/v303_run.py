"""T-151 read-only run: ARCH_TAKEOFF_V3.0.3 on the development villa's Drive copies (the architectural DXF from
P7757_DXF_COMPRESSED.zip and the structural "ST7757 dxf.dxf"), with the same project inputs, decisions and history
runs as research/agents_t142/v302_run.py, the route G profile (required: Gate B defect D1 of T-133) and the V3.0.3
steel ledgers (research/agents_t151/t151_ledgers.py). Prints the V3.0.3 totals per piece and storey (quantities,
units, states and engine ids only: no coordinates, no names). Every output goes to --out (outside the repository).

    python3 -I research/agents_t151/v303_run.py <plan.dxf> <structural.dxf> --out <scratch>/t151 \
        --profile research/urban_engine_m4_correctness/profile_st7757_m4.json [--reuse <dir with v29 / v210 .. v212>]

--reuse takes the released V2.9 and the V2.10 .. V2.12 history runs from an earlier run of the same inputs (their
BOQ_LINES.json are checked to exist); without it they are run here.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t131"))
sys.path.insert(0, str(ROOT / "research" / "agents_t142"))
sys.path.insert(0, str(HERE))

import alsenan_v30_run as T131  # noqa: E402
import t151_ledgers as LG       # noqa: E402
import v302_run as T142         # noqa: E402

# the ledgers' own published totals (their summaries / reports), re-added by the typed records
OWN = {"COLUMN_STEEL": {"released": 1887.131, "held_defined": 1552.435},
       "GROUND_SYSTEM_STEEL": {"released": 1479.86 - 168.63 - 58.32},   # T-138 net less SB1 / SB3 (Q-74 held)
       "BEAM_STEEL": {"released": 5171.03}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("structural")
    ap.add_argument("--out", required=True)
    ap.add_argument("--profile", required=True, help="route G drawing profile (Gate B defect D1)")
    ap.add_argument("--reuse", help="an earlier run directory holding v29 / v210 / v211 / v212")
    a = ap.parse_args(argv)
    from tools import urban_boq_m9 as M
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    src = Path(a.reuse) if a.reuse else out
    (out / "facts.json").write_text(json.dumps(T131.facts(Path(a.plan).name), ensure_ascii=False), encoding="utf-8")
    common = T131.common_args(a, out)
    if not a.reuse:
        M.main(["arch", "--out", str(out / "v29"), "--method", "ARCH_TAKEOFF_V2.9"] + common)
    extra = ["--v30-released", str(src / "v29" / "BOQ_LINES.json")]
    hist = []
    for m in ("ARCH_TAKEOFF_V2.10", "ARCH_TAKEOFF_V2.11", "ARCH_TAKEOFF_V2.12"):
        tag = "v" + m.split("_V")[-1].replace(".", "")
        if not a.reuse:
            M.main(["arch", "--out", str(out / tag), "--method", m] + common)
        hist.append(f"{m}={src / tag / 'BOQ_LINES.json'}")
    for h in [src / "v29" / "BOQ_LINES.json"] + [Path(x.split("=", 1)[1]) for x in hist]:
        if not h.exists():
            raise SystemExit(f"missing {h}")
    inp3 = LG.inputs(T131.PID)
    for lg in inp3["ledgers"]:
        for k, v in OWN[lg["piece"]].items():
            got = lg["declared_totals"][k]
            if abs(got - v) > 0.01:
                raise SystemExit(f"{lg['piece']} {k}: typed records {got} != the ledger's own total {v}")
    (out / "decisions.json").write_text(json.dumps(T131.DECISIONS), encoding="utf-8")
    (out / "v302_inputs.json").write_text(json.dumps(T142.INPUTS, ensure_ascii=False), encoding="utf-8")
    (out / "v303_inputs.json").write_text(json.dumps(inp3, ensure_ascii=False), encoding="utf-8")
    extra += ["--v30-history"] + hist + ["--v30-decisions", str(out / "decisions.json"),
                                         "--v302-inputs", str(out / "v302_inputs.json"),
                                         "--v303-inputs", str(out / "v303_inputs.json")]
    M.main(["arch", "--out", str(out / "v303"), "--method", "ARCH_TAKEOFF_V3.0.3"] + common + extra)
    run = json.loads((out / "v303" / "V3_0_3_RUN.json").read_text(encoding="utf-8"))
    print("identity:", json.dumps(run["identity"], indent=1))
    print("evidence status:", run["evidence_status_counts"])
    for lg in run["piece_logs"]:
        print(lg["piece"], json.dumps({k: lg.get(k) for k in ("state", "route_lines", "route_kg", "route_by_floor",
                                                               "superseded_not_present", "totals", "by_floor",
                                                               "evidence_status", "end_leg_lines")}, default=str))
    for k in sorted(set(run["steel_v3_0_2"]) | set(run["steel_v3_0_3"])):
        print(f"{k:28s} V3.0.2 {run['steel_v3_0_2'].get(k)} | V3.0.3 {run['steel_v3_0_3'].get(k)}")
    return 0


if __name__ == "__main__":
    main()
