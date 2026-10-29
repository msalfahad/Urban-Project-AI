"""T-319 read-only run: ARCH_TAKEOFF_V3.0.23 on the development villa's Drive copies (the architectural DXF from
P7757_DXF_COMPRESSED.zip and the structural "ST7757 dxf.dxf"). Every output goes to --out (outside the repository);
printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).

    python3 -I research/agents_t319/v3023_run.py <plan.dxf> <structural.dxf> --out <scratch>/t319 \
        --t167 <dir of a finished research/agents_t167/v304_run.py run on the same drawings>

As research/agents_t331/v3022_run.py (its inputs unchanged) with --method ARCH_TAKEOFF_V3.0.23 and --v3023-inputs
(t319_inputs.py: the parapet RC runs from the merged T-311 / T-324 ledgers); the V3_0_5_* .. V3_0_22_* files of this
run are V3.0.5 .. V3.0.22 reproduced.
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
          ROOT / "research" / "agents_t193", ROOT / "research" / "agents_t231", ROOT / "research" / "agents_t211",
          ROOT / "research" / "agents_t232", ROOT / "research" / "agents_t239", ROOT / "research" / "agents_t146",
          ROOT / "research" / "agents_t268", ROOT / "research" / "agents_t240", ROOT / "research" / "agents_t270", ROOT / "research" / "agents_t245", ROOT / "research" / "agents_t254",
          ROOT / "research" / "agents_t266", ROOT / "research" / "agents_t255", ROOT / "research" / "agents_t244", ROOT / "research" / "agents_t315", ROOT / "research" / "agents_t331", HERE):
    sys.path.insert(0, str(p))

import alsenan_v30_run as T131  # noqa: E402
import t151_ledgers as LG       # noqa: E402
import t179_ledgers as L5       # noqa: E402
import t187_inputs as L6        # noqa: E402
import t193_inputs as L7        # noqa: E402
import t211_inputs as L9        # noqa: E402
import t231_inputs as L8        # noqa: E402
import t232_inputs as L10       # noqa: E402
import t239_inputs as L11       # noqa: E402
import t146_inputs as L12       # noqa: E402
import t268_inputs as L13       # noqa: E402
import t240_inputs as L14       # noqa: E402
import t270_inputs as L15       # noqa: E402
import t245_inputs as L16       # noqa: E402
import t254_inputs as L17       # noqa: E402
import t266_inputs as L18       # noqa: E402
import t255_inputs as L19       # noqa: E402
import t244_inputs as L20       # noqa: E402
import t315_inputs as L21       # noqa: E402
import t331_inputs as L22       # noqa: E402
import t319_inputs as L23       # noqa: E402
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
    (out / "v309_inputs.json").write_text(json.dumps(L9.inputs(T131.PID), ensure_ascii=False), encoding="utf-8")
    (out / "v3010_inputs.json").write_text(json.dumps(L10.inputs(T131.PID), ensure_ascii=False), encoding="utf-8")
    (out / "v3011_inputs.json").write_text(json.dumps(L11.inputs(T131.PID), ensure_ascii=False), encoding="utf-8")
    (out / "v3012_inputs.json").write_text(json.dumps(L12.inputs(T131.PID), ensure_ascii=False), encoding="utf-8")
    (out / "v3013_inputs.json").write_text(json.dumps(L13.inputs(T131.PID), ensure_ascii=False), encoding="utf-8")
    (out / "v3014_inputs.json").write_text(json.dumps(L14.inputs(T131.PID), ensure_ascii=False), encoding="utf-8")
    (out / "v3015_inputs.json").write_text(json.dumps(L15.inputs(T131.PID), ensure_ascii=False), encoding="utf-8")
    (out / "v3016_inputs.json").write_text(json.dumps(L16.inputs(T131.PID), ensure_ascii=False), encoding="utf-8")
    (out / "v3017_inputs.json").write_text(json.dumps(L17.build(), ensure_ascii=False), encoding="utf-8")
    (out / "v3018_inputs.json").write_text(json.dumps(L18.build(), ensure_ascii=False), encoding="utf-8")
    (out / "v3019_inputs.json").write_text(json.dumps(L19.build(), ensure_ascii=False), encoding="utf-8")
    (out / "v3020_inputs.json").write_text(json.dumps(L20.build(), ensure_ascii=False), encoding="utf-8")
    (out / "v3021_inputs.json").write_text(json.dumps(L21.build(T131.PID), ensure_ascii=False), encoding="utf-8")
    (out / "v3022_inputs.json").write_text(json.dumps(L22.build(T131.PID), ensure_ascii=False), encoding="utf-8")
    (out / "v3023_inputs.json").write_text(json.dumps(L23.build(T131.PID), ensure_ascii=False), encoding="utf-8")
    extra = ["--v30-released", str(src / "v29" / "BOQ_LINES.json"), "--v30-history"] + hist + [
        "--v30-decisions", str(out / "decisions.json"), "--v302-inputs", str(out / "v302_inputs.json"),
        "--v303-inputs", str(out / "v303_inputs.json"), "--v304-inputs", str(src / "v304_inputs.json"),
        "--v305-inputs", str(out / "v305_inputs.json"), "--v306-inputs", str(out / "v306_inputs.json"),
        "--v307-inputs", str(out / "v307_inputs.json"), "--v308-inputs", str(out / "v308_inputs.json"),
        "--v309-inputs", str(out / "v309_inputs.json"), "--v3010-inputs", str(out / "v3010_inputs.json"),
        "--v3011-inputs", str(out / "v3011_inputs.json"), "--v3012-inputs", str(out / "v3012_inputs.json"),
        "--v3013-inputs", str(out / "v3013_inputs.json"), "--v3014-inputs", str(out / "v3014_inputs.json"),
        "--v3015-inputs", str(out / "v3015_inputs.json"),
        "--v3016-inputs", str(out / "v3016_inputs.json"), "--v3017-inputs", str(out / "v3017_inputs.json"),
        "--v3018-inputs", str(out / "v3018_inputs.json"), "--v3019-inputs", str(out / "v3019_inputs.json"),
        "--v3020-inputs", str(out / "v3020_inputs.json"), "--v3021-inputs", str(out / "v3021_inputs.json"),
        "--v3022-inputs", str(out / "v3022_inputs.json"), "--v3023-inputs", str(out / "v3023_inputs.json")]
    M.main(["arch", "--out", str(out / "v3023"), "--method", "ARCH_TAKEOFF_V3.0.23"] + common + extra)
    run = json.loads((out / "v3023" / "V3_0_23_RUN.json").read_text(encoding="utf-8"))
    print("identity:", json.dumps(run["identity"], indent=1, sort_keys=True))
    print("piece logs:", json.dumps([{k: v for k, v in lg.items() if k not in ("sources", "new_records")}
                                     for lg in run["piece_logs"]], indent=1, sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
