"""python3 -m tools.synth_villa OUT_DIR [--engine] [--method M]: write the T-019 first-run villas (DXF + truth JSON)
into OUT_DIR and, with --engine, the engine-vs-truth report of each (report_<villa>.json) and a summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.synth_villa import build as B
from tools.synth_villa import compare as C
from tools.synth_villa import villas as V


def first_run(out, *, engine=False, method=C.DEFAULT_METHOD):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    summary = {}
    for vid, var in V.FIRST_RUN.items():
        p = out / f"{vid}.dxf"
        got = B.write_villa(vid, p, **var)
        (out / f"{vid}.truth.json").write_text(json.dumps(got["truth"], ensure_ascii=False, indent=1))
        if engine:
            _room, arch, refusal = C.run_engine(p, method)
            rep = C.compare(got["truth"], arch, refusal)
            (out / f"report_{vid}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
            summary[vid] = {"variant": var, **rep["summary"], "omitted": rep["silent_omissions"]}
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m tools.synth_villa")
    ap.add_argument("out")
    ap.add_argument("--engine", action="store_true")
    ap.add_argument("--method", default=C.DEFAULT_METHOD)
    a = ap.parse_args(argv)
    s = first_run(a.out, engine=a.engine, method=a.method)
    if s:
        print(json.dumps(s, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
