"""T-478 rebase check (read-only, private run outputs only): after the rebase on the merged V3.0.44, prove that
(1) the hub run reproduces V3.0.43 6f534d5e and V3.0.44 8b2fe2b6, (2) the V3.0.45 blinding lines are byte-identical
whether the package is applied to V3.0.43 (the READY dd3fe478 result e1f4310a, reproduced here) or to V3.0.44, and
(3) V3.0.45 differs from V3.0.43 only by the 10 V3.0.44 skirting lines (carried byte-identical) and the 6 blinding
lines. Prints hashes, counts and codes only.

    .work/venv/bin/python -I research/agents_t478/t478_rebase_check.py <out of v3045_run.py>/v3045
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import t478_inputs as IN  # noqa: E402
from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v3045 as M  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402


def main(argv):
    d = Path(argv[1])
    sha = {v: hashlib.sha256((d / f"V3_0_{v}_BOQ_LINES.json").read_bytes()).hexdigest()[:8] for v in (43, 44, 45)}
    ls = {v: json.loads((d / f"V3_0_{v}_BOQ_LINES.json").read_text(encoding="utf-8")) for v in (43, 44, 45)}
    pid = ls[43][0]["project"]["project_id"]
    doc = M.load_inputs(IN.build(pid), pid)
    ch, _ = M.changes_for(doc, ls[43])
    alt, _ = M.integrate(ls[43], ch)
    h = {v: {x["line_id"]: A30.line_sha(x) for x in ls[v]} for v in ls}
    ha = {x["line_id"]: A30.line_sha(x) for x in alt}
    bl = [c["after"]["line_id"] for c in ch]
    code = {x["line_id"]: x["item_code"] for x in ls[45]}
    d45 = [i for i in h[45] if h[45][i] != h[43].get(i)]
    sk = [i for i in h[44] if h[44][i] != h[43].get(i)]
    out = {"v3_0_43": sha[43], "v3_0_44": sha[44], "v3_0_45": sha[45],
           "v3_0_45_on_v3_0_43_base": hashlib.sha256(BL.dumps(alt).encode()).hexdigest()[:8],
           "blinding_lines": len(bl), "blinding_identical_on_both_bases": all(ha[i] == h[45][i] for i in bl),
           "v3_0_45_vs_v3_0_43_differing_by_code": dict(Counter(code[i] for i in d45)),
           "v3_0_44_lines_carried": len(sk), "v3_0_44_lines_identical": all(h[45][i] == h[44][i] for i in sk)}
    print(json.dumps(out, indent=1, sort_keys=True))
    ok = (out["blinding_identical_on_both_bases"] and out["v3_0_44_lines_identical"]
          and set(out["v3_0_45_vs_v3_0_43_differing_by_code"]) <= {"FIN.SKIRTING", M.BL_CODE})
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
