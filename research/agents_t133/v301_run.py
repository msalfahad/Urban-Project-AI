"""T-133 read-only run for the verifier: ARCH_TAKEOFF_V3.0.1 on the development villa's Drive copies (the architectural
DXF from P7757_DXF_COMPRESSED.zip and the structural "ST7757 dxf.dxf"), with the same project inputs, decision and
history runs as research/agents_t131/alsenan_v30_run.py (route G conventions V6). Prints the V3.0.1 rows (quantities,
units, states, engine ids only: no coordinates, no names) and the family totals. Every output goes to --out (outside
the repository).

    python3 -I research/agents_t133/v301_run.py <plan.dxf> <structural.dxf> --out <scratch>/t133

NOT EXECUTED by the worker (T-133 run of 2026-10-21: running research scripts on the Drive drawings was refused by the
session permission check); the verifier runs it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t131"))

import alsenan_v30_run as T131  # noqa: E402


def q(x):
    if not x or x.get("state") is None:
        return "-"
    if x.get("value") is not None:
        return f"{x['value']:.4f} {x['state']}"
    if x.get("low") is not None:
        return f"{x['low']:.4f}..{x['high']:.4f} {x['state']}"
    return x["state"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("structural")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from tools import urban_boq_m9 as M
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "facts.json").write_text(json.dumps(T131.facts(Path(a.plan).name), ensure_ascii=False), encoding="utf-8")
    common = ["--drawings", a.plan, "--structural", a.structural, "--conventions", str(T131.CONV), "--facts",
              str(out / "facts.json"), "--project", T131.PID, "--no-svg"]
    M.main(["arch", "--out", str(out / "v29"), "--method", "ARCH_TAKEOFF_V2.9"] + common)
    extra = ["--v30-released", str(out / "v29" / "BOQ_LINES.json")]
    hist = []
    for m in ("ARCH_TAKEOFF_V2.10", "ARCH_TAKEOFF_V2.11", "ARCH_TAKEOFF_V2.12"):
        tag = "v" + m.split("_V")[-1].replace(".", "")
        M.main(["arch", "--out", str(out / tag), "--method", m] + common)
        hist.append(f"{m}={out / tag / 'BOQ_LINES.json'}")
    (out / "decisions.json").write_text(json.dumps(T131.DECISIONS), encoding="utf-8")
    extra += ["--v30-history"] + hist + ["--v30-decisions", str(out / "decisions.json")]
    M.main(["arch", "--out", str(out / "v301"), "--method", "ARCH_TAKEOFF_V3.0.1"] + common + extra)
    led = json.loads((out / "v301" / "V3_0_1_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    run = json.loads((out / "v301" / "V3_0_1_RUN.json").read_text(encoding="utf-8"))
    print("identity:", json.dumps(run["identity"], indent=1))
    print("totals:", json.dumps(run["totals"], indent=1))
    for r in led["rows"]:
        if r.get("version") != "ARCH_TAKEOFF_V3.0.1":
            continue
        if r["piece"] == "MEMBRANE_AUDIT_V5":
            continue
        print(f"{r['piece']:14s} {r['action']:8s} {r['item_code']:22s} {r['floor'] or '':10s} {r['unit']:4s} "
              f"{str(r['element_id'])[-48:]:48s} V2.9 {q(r['before_released_v2_9'])} | V3.0 "
              f"{q(r['before_candidate_v3_0'])} | V3.0.1 {q(r['after_v3_0_1'])}")
    for lg in run["piece_logs"]:
        if lg["piece"] == "MEMBRANE_AUDIT_V5":
            for x in lg["lines"]:
                print(f"rolls {x['floor']:4s} {str(x['room_id'])[-28:]:28s} {x['rolls']} audit {x['audit']} "
                      f"{x['agreement']} V5 {x['v5_by_reading']}")
        if lg["piece"] == "ROUTE_G_SCOPE":
            print("columns by storey:", json.dumps(lg.get("columns_by_storey"), indent=1))
            print("blinding:", json.dumps({k: v for k, v in (lg.get("blinding") or {}).items() if k != "records"}))
            for b in (lg.get("blinding") or {}).get("records") or ():
                print("  ", b["family"], b.get("member") or "", b["status"], b.get("m3"), b.get("exposure_m3"),
                      b.get("blocker") or "")
    return 0


if __name__ == "__main__":
    main()
