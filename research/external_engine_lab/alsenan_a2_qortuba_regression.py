"""Qortuba regression for Alsenan Phase A2: compare Qortuba RC1 registers rebuilt by the CURRENT engine (rc1_qortuba.py
into a scratch directory) with the frozen tests/rc1/registers, key by key. Qortuba files are never edited.

    python3 research/external_engine_lab/alsenan_a2_qortuba_regression.py <rebuilt_register_dir> <a2_register_dir>

Writes QORTUBA_REGRESSION.json into the A2 register directory."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / "tests/rc1/registers"


def _diff(a, b, path="", out=None, limit=60):
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append({"path": f"{path}/{k}", "change": "ADDED" if k not in a else "REMOVED"})
            else:
                _diff(a[k], b[k], f"{path}/{k}", out, limit)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            _diff(x, y, f"{path}[{i}]", out, limit)
    elif a != b:
        out.append({"path": path, "frozen": str(a)[:160], "rebuilt": str(b)[:160]})
    return out


def compare(rebuilt: Path) -> dict:
    files = sorted(p.name for p in FROZEN.glob("*.json"))
    per, changed = {}, []
    for n in files:
        q = rebuilt / n
        if not q.exists():
            per[n] = {"state": "MISSING_IN_REBUILD"}
            changed.append(n)
            continue
        a, b = json.loads((FROZEN / n).read_text()), json.loads(q.read_text())
        d = _diff(a, b)
        per[n] = {"state": "IDENTICAL" if not d else "DIFFERENT", "differences": d}
        if d:
            changed.append(n)
    extra = sorted(p.name for p in rebuilt.glob("*.json") if not (FROZEN / p.name).exists())
    only_inventory = all(all(("ENGINE_INVENTORY" in n) or any(k in x["path"] for k in ("sha256", "digest", "commit",
                                                                                     "inventory"))
                             for x in per[n].get("differences", [])) for n in changed)
    return {"SCHEMA": "URBAN_ALSENAN_A2_QORTUBA_REGRESSION_V1", "frozen_dir": "tests/rc1/registers",
            "registers": len(files), "identical": len(files) - len(changed), "changed": changed, "extra": extra,
            "per_register": per,
            "state": "UNCHANGED" if not changed else ("PROVENANCE_ONLY" if only_inventory else "QUANTITY_OR_ROLE_CHANGE"),
            "rule": "Qortuba is frozen as RC1_REFERENCE; the A2 engine defaults (no inference claims, no inferred doors) "
                    "must leave every Qortuba quantity unchanged; Qortuba files are never edited"}


def main(rebuilt, a2dir):
    rec = compare(Path(rebuilt))
    Path(a2dir, "QORTUBA_REGRESSION.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: rec[k] for k in ("state", "registers", "identical", "changed", "extra")}, indent=1))
    return rec


if __name__ == "__main__":
    main(*sys.argv[1:3])
