"""T-200: run LEVEL_CHAIN_V1 on the development villa input (ALSENAN_LEVEL_INPUT.json) and write summary.json.

Two runs: AS PRINTED (every printed value, the architectural pool cut included) and WITH THE T-183 r2 RULING (the
architectural cut's 0.15 m pool base is set aside because the structural pool detail governs the RC thickness; Checker
verdict 2026-10-22 16:14). Nothing here is a BOQ quantity. Run from the repository root:
    python3 -I research/agents_t200/t200_alsenan_check.py [--write]
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import level_chain_v1 as LC  # noqa: E402

HERE = Path(__file__).resolve().parent
INPUT = HERE / "ALSENAN_LEVEL_INPUT.json"


def load():
    return json.loads(INPUT.read_text(encoding="utf-8"))


def with_ruling(p):
    q = copy.deepcopy(p)
    q["datums"] = [d for d in q["datums"] if not (d["chain_id"] == "POOL" and d["kind"] == "POOL_BASE_UNDERSIDE")]
    return q


def run():
    p = load()
    return {"as_printed": LC.check(p), "with_t183_ruling": LC.check(with_ruling(p))}


def _brief(res):
    return {"summary": res["summary"],
            "datums": [(r["chain_id"], r["kind"], r["value"], r["status"], r["basis"]) for r in res["datums"]],
            "links": [(r["chain_id"], r["layer"], r["thickness"], r["status"], r["missing"]) for r in res["links"]],
            "bounds": [(b["chain_id"], b["kind"], b["bound"], b["value"], b["result"]) for b in res["bounds"]],
            "uses": [(u["use_id"], u["code"], u["detail"], u["sensitivity"]) for u in res["uses"]],
            "owner_manual_layers": [(m["chain_id"], m["layer"], m["thickness"]) for m in res["owner_manual_layers"]]}


if __name__ == "__main__":
    out = {k: _brief(v) for k, v in run().items()}
    text = json.dumps(out, indent=1, ensure_ascii=False)
    if "--write" in sys.argv:
        (HERE / "summary.json").write_text(text + "\n", encoding="utf-8")
    print(text)
