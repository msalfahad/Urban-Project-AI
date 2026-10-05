"""ALSENAN CONTROL-PLANE ROUND 2 - build and freeze the ALSENAN_CONTROL_V2 candidate (never overwrites V3b).

    python3 research/alsenan_control_plane_02/build_control_v2.py <work_dir | ctx.pkl> [--twice]

1. rebuild the Alsenan context with the round-2 production code (alsenan_v3b.build) or load a pickled context
   built by that code; 2. rebuild the V3b registers on it in memory (alsenan_v3b_registers.registers - nothing is
   written to tests/alsenan/registers_v3b); 3. read ST7757.dxf with the structural source reader V2; 4. build the
   control registers (alsenan_control_v2.build) and write them to registers/ with INDEX.json (sha256 per register).
--twice builds the control registers a second time from the same inputs and refuses to write if any hash differs.
The benchmark comparison is a separate, later step (post_freeze_compare.py) that only runs against a frozen INDEX.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "external_engine_lab"))
sys.path.insert(0, str(ROOT))

import alsenan_control_v2 as CV2  # noqa: E402
import alsenan_structural_source_v2 as SRC  # noqa: E402
import alsenan_v3b_registers as V3BR  # noqa: E402

sys.path.insert(0, str(HERE))
import static_registers as STATIC  # noqa: E402

OUT = HERE / "registers"
FROZEN = ROOT / "tests/alsenan/registers_v3b/BOQ_LINES_V3B.json"
FROZEN_V3A = ROOT / "tests/alsenan/registers_v3/BOQ_LINES.json"


def _text(o):
    return json.dumps(o, indent=1, ensure_ascii=False, sort_keys=False, default=V3BR.jdefault) + "\n"


def load(src):
    p = Path(src)
    if p.is_file():
        return pickle.load(open(p, "rb"))
    import alsenan_v3b as V3B
    return V3B.build(p, "control-plane-round-2")


def build(ctx):
    v3b = V3BR.registers(ctx)
    frozen = json.loads(FROZEN.read_text())["lines"]
    src = SRC.read()
    regs = CV2.build(ctx, v3b, frozen, src, json.loads(FROZEN_V3A.read_text())["lines"])
    regs["LEGACY_CAD_MIGRATION_REGISTER"] = STATIC.legacy_cad()
    regs["GATE_TRANSITION_REGISTER"] = STATIC.gates()
    return regs, v3b


def main(src, twice=False):
    ctx = load(src)
    regs, v3b = build(ctx)
    texts = {k: _text(v) for k, v in regs.items()}
    if twice:
        again, _ = build(ctx)
        diff = [k for k, v in again.items() if _text(v) != texts[k]]
        if diff:
            raise SystemExit(f"NON-DETERMINISTIC: {diff}")
    OUT.mkdir(parents=True, exist_ok=True)
    idx = {}
    for k, t in texts.items():
        (OUT / f"{k}.json").write_text(t)
        idx[k] = hashlib.sha256(t.encode()).hexdigest()
    doc = {"SCHEMA": "URBAN_ALSENAN_CONTROL_V2_INDEX_V1", "registers": idx, "built_twice_identical": bool(twice),
           "v3b_rebuilt_qa": v3b["FINAL_QA_V3B"]["state"],
           "frozen_v3b_lines_sha256": hashlib.sha256(FROZEN.read_bytes()).hexdigest(),
           "st7757_sha256": regs["STRUCTURAL_SOURCE_COVERAGE_V2"]["source_sha256"],
           "rule": "frozen before the benchmark comparison; post_freeze_compare.py refuses to run if a hash differs"}
    (OUT / "INDEX.json").write_text(json.dumps(doc, indent=1) + "\n")
    for k, h in idx.items():
        print(f"{k:42s} {h[:12]}")


if __name__ == "__main__":
    main(sys.argv[1], "--twice" in sys.argv)
