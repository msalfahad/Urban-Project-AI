"""ALSENAN PHASE B2A.1 - regression of the rebuilt registers against the frozen B2A registers.

    python3 research/external_engine_lab/alsenan_b2a1_regression.py <frozen_b2a_dir> <b2a1_dir>

Every register present in both directories is flattened to its leaves. Provenance leaves (commits, digests, shas,
policy ids, schemas) are ignored. Old curved basis names are mapped to the explicit names (aliases only). Then:
    QUANTITY_CHANGED   a numeric leaf of the frozen register differs or disappeared       -> FAIL
    STATE_CHANGED      a state / function / closure leaf differs or disappeared           -> FAIL
    TERMINOLOGY        a string leaf renamed through the alias table                      -> allowed
    SCHEMA             any other string change, or a leaf added by B2A.1                  -> allowed
The freeze registers are compared through their summaries. Writes ALSENAN_REGRESSION.json into <b2a1_dir>.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PARENT_FREEZE = "ALSENAN_PHASE_B2A_FREEZE"
FREEZE = "ALSENAN_PHASE_B2A1_REGISTER_FREEZE"
NOT_COMPARED = {"QORTUBA_REGRESSION", "ALSENAN_REGRESSION", "TEST_RESULTS"}     # written after the build / by the package
PROVENANCE = ("commit", "digest", "sha256", "sha", "policy", "SCHEMA", "schema", "recommendation", "phase", "file",
              "review_image", "built_from", "head", "git")
STATE_KEYS = ("state", "closure", "function", "type", "namespace", "role", "basis")
TERMS = {"INNER": "MIN_RADIUS_ARC", "CENTRE": "MID_BAND_ARC", "OUTER": "MAX_RADIUS_ARC"}


def _prov(key) -> bool:
    return any(p in str(key) for p in PROVENANCE)


def flatten(o, path=()) -> dict:
    out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            if _prov(k):
                continue
            out.update(flatten(v, path + (str(k),)))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out.update(flatten(v, path + (str(i),)))
    else:
        out["/".join(path)] = o
    return out


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _is_state(path) -> bool:
    k = path.rsplit("/", 1)[-1]
    return any(k == s or k.endswith("_" + s) for s in STATE_KEYS)


def compare(old, new) -> dict:
    fo, fn = flatten(old), flatten(new)
    rows = []
    for p, v in sorted(fo.items()):
        w = fn.get(p, KeyError)
        if w is KeyError:
            cls = "QUANTITY_CHANGED" if _num(v) else "STATE_CHANGED" if _is_state(p) else "SCHEMA"
            rows.append({"leaf": p, "class": cls, "old": v, "new": "<absent>"})
        elif _num(v) or _num(w):
            if not (_num(v) and _num(w) and abs(v - w) < 1e-9):
                rows.append({"leaf": p, "class": "QUANTITY_CHANGED", "old": v, "new": w})
        elif v != w:
            if isinstance(v, str) and TERMS.get(v) == w:
                cls = "TERMINOLOGY"
            elif _is_state(p) or isinstance(v, bool) or v is None or w is None:
                cls = "STATE_CHANGED"
            else:
                cls = "SCHEMA"
            rows.append({"leaf": p, "class": cls, "old": v, "new": w})
    added = sorted(set(fn) - set(fo))
    return {"rows": rows, "added_leaves": len(added), "added_sample": added[:12]}


def run(parent_dir, new_dir) -> dict:
    parent_dir, new_dir = Path(parent_dir), Path(new_dir)
    R = lambda d, n: json.loads((d / f"{n}.json").read_text())
    names = sorted(p.stem for p in parent_dir.glob("*.json"))
    per, fails = {}, []
    for n in names:
        if n in NOT_COMPARED:
            continue
        if n == PARENT_FREEZE:
            c = compare(R(parent_dir, n)["summary"], R(new_dir, FREEZE)["summary"])
            key = f"{PARENT_FREEZE}.summary -> {FREEZE}.summary"
        elif not (new_dir / f"{n}.json").exists():
            per[n] = {"state": "MISSING_IN_B2A1"}
            fails.append(n)
            continue
        else:
            c, key = compare(R(parent_dir, n), R(new_dir, n)), n
        bad = [r for r in c["rows"] if r["class"] in ("QUANTITY_CHANGED", "STATE_CHANGED")]
        classes = sorted({r["class"] for r in c["rows"]})
        per[key] = {"state": "FAIL" if bad else ("UNCHANGED" if not c["rows"] and not c["added_leaves"] else "SCHEMA_ONLY"),
                    "classes": classes, "changes": c["rows"][:40], "change_count": len(c["rows"]),
                    "added_leaves": c["added_leaves"], "added_sample": c["added_sample"]}
        if bad:
            fails.append(key)
    extra = sorted(p.stem for p in new_dir.glob("*.json") if not (parent_dir / p.name).exists()
                   and p.stem not in (FREEZE,) and p.stem not in NOT_COMPARED)
    rec = {"SCHEMA": "URBAN_ALSENAN_B2A1_REGRESSION_V1",
           "parent_dir": "tests/alsenan/registers_b2a",
           "parent_freeze_sha256": hashlib.sha256((parent_dir / f"{PARENT_FREEZE}.json").read_bytes()).hexdigest(),
           "registers_compared": len(per), "unchanged": sorted(k for k, v in per.items() if v["state"] == "UNCHANGED"),
           "schema_only": sorted(k for k, v in per.items() if v["state"] == "SCHEMA_ONLY"),
           "failed": fails, "new_registers": extra, "per_register": per,
           "state": "PASS" if not fails else "FAIL",
           "rule": "no numeric or state leaf of a frozen B2A register may change; only schema / terminology / provenance"}
    (new_dir / "ALSENAN_REGRESSION.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False, default=str) + "\n")
    return rec


if __name__ == "__main__":
    r = run(sys.argv[1], sys.argv[2])
    print(json.dumps({k: r[k] for k in ("state", "registers_compared", "unchanged", "schema_only", "failed", "new_registers")},
                     indent=1))
    sys.exit(0 if r["state"] == "PASS" else 1)
