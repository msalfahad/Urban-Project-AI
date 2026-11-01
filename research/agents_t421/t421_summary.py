"""T-421: the package summary from a finished research/agents_t421/v3038_run.py directory (outside the repository).

    python3 -I research/agents_t421/t421_summary.py <out dir of v3038_run.py> [--write]   # prints (writes summary_t421.json)
    python3 -I research/agents_t421/t421_summary.py --check                               # the committed summary closes

It checks that the run reproduced the candidate of record V3.0.37 (json 733f2efb), then reports every V3.0.38 line
this package adds or changes (engine ids, line ids, item codes, states and quantities only; no coordinates, no names)
with its V3.0.37 and V2.9 quantity, the identity block, the diff counts and the totals moved by code.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "summary_t421.json"
V3037_SHA = "733f2efb"     # T-420 Gate B (merged 4c01fe06): the first 8 hex of V3_0_37_BOQ_LINES.json


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _lines(p):
    raw = json.loads(Path(p).read_text(encoding="utf-8"))
    return raw["lines"] if isinstance(raw, dict) else raw


def _q(ln):
    if ln is None:
        return None
    if ln.get("measured_net") is not None:
        return {"state": ln["evidence_state"], "value": round(ln["measured_net"], 6)}
    br = ln.get("bounded_range")
    if br:
        return {"state": ln["evidence_state"], "low": round(br["low"], 6), "high": round(br["high"], 6)}
    return {"state": ln["evidence_state"]}


def build(d):
    d = Path(d) / "v3038"
    s37 = _sha(d / "V3_0_37_BOQ_LINES.json")
    if not s37.startswith(V3037_SHA):
        raise SystemExit(f"V3.0.37 not reproduced: {s37[:8]} != {V3037_SHA}")
    l37 = {ln["line_id"]: ln for ln in _lines(d / "V3_0_37_BOQ_LINES.json")}
    l38 = _lines(d / "V3_0_38_BOQ_LINES.json")
    run = json.loads((d / "V3_0_38_RUN.json").read_text(encoding="utf-8"))
    led = json.loads((d / "V3_0_38_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    diff = list(csv.DictReader((d / "V3_0_38_DIFF.csv").read_text(encoding="utf-8").splitlines()))
    by = {ln["line_id"]: ln for ln in l38}
    rows = []
    for r in led["rows"]:
        ln = by[r["line_id"]]
        rows.append({"piece": r["piece"], "action": r["action"], "change": r["change"], "line_id": r["line_id"],
                     "item_code": r["item_code"], "floor": r["floor"], "element_id": r["element_id"], "unit": r["unit"],
                     "v3_0_37": _q(l37.get(r["line_id"])), "v3_0_38": _q(ln),
                     "v2_9": r.get("before_released_v2_9"), "evidence_status": r["evidence_status"],
                     "deductions": [{"id": x["id"], "qty": x["qty"]} for x in ln.get("deductions") or []
                                    if x.get("id", "").startswith("L-") and "threshold" in str(x.get("what"))],
                     "still_held": [{"what": x["what"], "range": x["range"]} for x in r.get("still_held") or ()]})
    ident = run["identity"]
    changed = sorted(x["line_id"] for x in diff if x["vs_v3_0_37"] == "CHANGED")
    return {"task": "T-421", "method": run["method"], "extends": run["extends"],
            "v3_0_37_boq_lines_sha256": s37, "v3_0_38_boq_lines_sha256": _sha(d / "V3_0_38_BOQ_LINES.json"),
            "v3_0_37_lines": ident["v3_0_37_lines"], "v3_0_38_lines": ident["v3_0_38_lines"],
            "added": ident["added"], "replaced": ident["replaced"],
            "outside_rows_identical_to_v3_0_37": ident["outside_rows_identical_to_v3_0_37"],
            "outside_rows_sha256": ident["outside_rows_sha256"], "diff": ident["diff"], "changed_line_ids": changed,
            "beds_check": ident["beds"], "lift_check": ident["lift"], "landing_check": ident["landing"],
            "by_action": run["piece_logs"][0]["by_action"], "totals_moved_by_code": run["totals_moved_by_code"],
            "rows": rows, "released_default": run["released_default"]}


def main(argv):
    if argv[:1] == ["--check"]:
        s = json.loads(OUT.read_text(encoding="utf-8"))
        assert s["added"] == sum(1 for r in s["rows"] if r["change"] == "ADD")
        assert s["replaced"] == sum(1 for r in s["rows"] if r["change"] == "CHANGE") == len(s["changed_line_ids"])
        assert s["v3_0_38_lines"] == s["v3_0_37_lines"] + s["added"]
        print(json.dumps({k: s[k] for k in ("added", "replaced", "lift_check", "landing_check", "by_action")}, indent=1))
        return 0
    s = build(argv[0])
    if "--write" in argv:
        OUT.write_text(json.dumps(s, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in s.items() if k != "rows"}, indent=1, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
