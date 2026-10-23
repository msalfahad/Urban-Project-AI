"""T-231 read-only run: ARCH_TAKEOFF_V3.0.8 on the development villa's Drive copies (the architectural DXF from
P7757_DXF_COMPRESSED.zip and the structural "ST7757 dxf.dxf"). Every output goes to --out (outside the repository);
printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).

    python3 -I research/agents_t231/v308_run.py <plan.dxf> <structural.dxf> --out <scratch>/t231 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

As research/agents_t193/v307_run.py (its inputs unchanged) with --method ARCH_TAKEOFF_V3.0.8 and --v308-inputs
(t231_inputs.py); the V3_0_5_* .. V3_0_7_* files of this run are V3.0.5 .. V3.0.7 reproduced.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t131", ROOT / "research" / "agents_t142", ROOT / "research" / "agents_t151",
          ROOT / "research" / "agents_t167", ROOT / "research" / "agents_t179", ROOT / "research" / "agents_t187",
          ROOT / "research" / "agents_t193", HERE):
    sys.path.insert(0, str(p))

import alsenan_v30_run as T131  # noqa: E402
import t151_ledgers as LG       # noqa: E402
import t179_ledgers as L5       # noqa: E402
import t187_inputs as L6        # noqa: E402
import t193_inputs as L7        # noqa: E402
import t231_inputs as L8        # noqa: E402
import v302_run as T142         # noqa: E402

M4 = ROOT / "research/urban_engine_m4_correctness/profile_st7757_m4.json"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("structural")
    ap.add_argument("--out", required=True)
    ap.add_argument("--t167", required=True, help="a finished T-167 v304_run.py directory (same drawings)")
    a = ap.parse_args(argv)
    from tools import urban_boq_m9 as M
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    src = Path(a.t167).resolve()
    a.profile = str(M4)
    a.reuse = str(src)
    (out / "facts.json").write_text(json.dumps(T131.facts(Path(a.plan).name), ensure_ascii=False), encoding="utf-8")
    common = T131.common_args(a, out)
    hist = [f"{m}={src / ('v' + m.split('_V')[-1].replace('.', '')) / 'BOQ_LINES.json'}"
            for m in ("ARCH_TAKEOFF_V2.10", "ARCH_TAKEOFF_V2.11", "ARCH_TAKEOFF_V2.12")]
    (out / "decisions.json").write_text(json.dumps(T131.DECISIONS), encoding="utf-8")
    (out / "v302_inputs.json").write_text(json.dumps(T142.INPUTS, ensure_ascii=False), encoding="utf-8")
    (out / "v303_inputs.json").write_text(json.dumps(LG.inputs(T131.PID), ensure_ascii=False), encoding="utf-8")
    (out / "v305_inputs.json").write_text(json.dumps(L5.inputs(T131.PID), ensure_ascii=False), encoding="utf-8")
    (out / "v306_inputs.json").write_text(json.dumps(L6.inputs(T131.PID), ensure_ascii=False), encoding="utf-8")
    (out / "v307_inputs.json").write_text(json.dumps(L7.inputs(T131.PID), ensure_ascii=False), encoding="utf-8")
    (out / "v308_inputs.json").write_text(json.dumps(L8.inputs(T131.PID), ensure_ascii=False), encoding="utf-8")
    extra = ["--v30-released", str(src / "v29" / "BOQ_LINES.json"), "--v30-history"] + hist + [
        "--v30-decisions", str(out / "decisions.json"), "--v302-inputs", str(out / "v302_inputs.json"),
        "--v303-inputs", str(out / "v303_inputs.json"), "--v304-inputs", str(src / "v304_inputs.json"),
        "--v305-inputs", str(out / "v305_inputs.json"), "--v306-inputs", str(out / "v306_inputs.json"),
        "--v307-inputs", str(out / "v307_inputs.json"), "--v308-inputs", str(out / "v308_inputs.json")]
    M.main(["arch", "--out", str(out / "v308"), "--method", "ARCH_TAKEOFF_V3.0.8"] + common + extra)
    run = json.loads((out / "v308" / "V3_0_8_RUN.json").read_text(encoding="utf-8"))
    print("identity:", json.dumps(run["identity"], indent=1))
    print("evidence status:", run["evidence_status_counts"])
    for lg in run["piece_logs"]:
        print(lg["piece"], json.dumps({k: lg.get(k) for k in (
            "state", "totals", "evidence_status", "records", "held", "held_total_info", "findings_by_code",
            "held_live_new", "rebased_on_printed", "line_group")}, indent=1))
    for k, v in run["totals_moved_by_code"].items():
        print(f"{k:28s} V3.0.7 {v['v3_0_7']} | V3.0.8 {v['v3_0_8']}")
    return 0


if __name__ == "__main__":
    main()
