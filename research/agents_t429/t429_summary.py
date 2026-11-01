"""T-429: the package summary from a finished research/agents_t429/v3039_run.py directory (outside the repository).

    python3 -I research/agents_t429/t429_summary.py <out dir of v3039_run.py> [--write]   # prints (writes summary_t429.json)
    python3 -I research/agents_t429/t429_summary.py --check                               # the committed summary closes

It checks that the run reproduced the candidate of record V3.0.38 (json 57cca61c, T-421 Gate B), then reports every
V3.0.39 line this package changes (engine ids, line ids, item codes, states and quantities only; no coordinates, no
names) with its V3.0.38 and V2.9 quantity, the identity block, the diff counts, the totals moved by code and the B7
valued / held totals before and after.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "summary_t429.json"
V3038_SHA = "57cca61c"     # T-421 Gate B (merged bc9f293c): the first 8 hex of V3_0_38_BOQ_LINES.json
CODES = ("FIN.MARBLE.TREAD", "FIN.STAIR.STEP_LM", "FIN.MARBLE.RISER")
VALUED = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")


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


def _fam(lines):
    out = {}
    for c in CODES:
        ls = [x for x in lines if x["item_code"] == c]
        v = [x for x in ls if x["evidence_state"] in VALUED]
        b = [x for x in ls if x["evidence_state"] == "BOUNDED_EXPOSURE"]
        out[c] = {"lines": len(ls), "valued_lines": len(v), "valued": round(sum(x["measured_net"] for x in v), 6),
                  "bounded_lines": len(b), "bounded_high": round(sum(x["bounded_range"]["high"] for x in b), 6),
                  "blocked_lines": sum(1 for x in ls if x["evidence_state"] == "BLOCKED_RFI"),
                  "not_applicable_lines": sum(1 for x in ls if x["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE")}
    return out


def build(d):
    d = Path(d) / "v3039"
    s38 = _sha(d / "V3_0_38_BOQ_LINES.json")
    if not s38.startswith(V3038_SHA):
        raise SystemExit(f"V3.0.38 not reproduced: {s38[:8]} != {V3038_SHA}")
    l38 = _lines(d / "V3_0_38_BOQ_LINES.json")
    b38 = {ln["line_id"]: ln for ln in l38}
    l39 = _lines(d / "V3_0_39_BOQ_LINES.json")
    run = json.loads((d / "V3_0_39_RUN.json").read_text(encoding="utf-8"))
    led = json.loads((d / "V3_0_39_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    diff = list(csv.DictReader((d / "V3_0_39_DIFF.csv").read_text(encoding="utf-8").splitlines()))
    by = {ln["line_id"]: ln for ln in l39}
    rows = []
    for r in led["rows"]:
        ln = by[r["line_id"]]
        rec = r["record"]
        rows.append({"action": r["action"], "line_id": r["line_id"], "item_code": r["item_code"], "floor": r["floor"],
                     "element_id": r["element_id"], "unit": r["unit"], "flight": r["flight"], "role": r["role"],
                     "flight_id": (b38[r["line_id"]]["calculation"]["inputs"] or {}).get("flight_id"),
                     "v3_0_38": _q(b38.get(r["line_id"])), "v3_0_39": _q(ln), "v2_9": r.get("before_released_v2_9"),
                     "evidence_status": r["evidence_status"], "owned_by": rec.get("owned_by"),
                     "kind": rec.get("kind"), "held_count": rec.get("held_count"),
                     "beside": [x["value"] for x in rec.get("beside") or ()] or None,
                     "held_beside": (rec.get("held_beside") or {}).get("value")})
    ident = run["identity"]
    changed = sorted(x["line_id"] for x in diff if x["vs_v3_0_38"] == "CHANGED")
    return {"task": "T-429", "method": run["method"], "extends": run["extends"],
            "v3_0_38_boq_lines_sha256": s38, "v3_0_39_boq_lines_sha256": _sha(d / "V3_0_39_BOQ_LINES.json"),
            "v3_0_38_lines": ident["v3_0_38_lines"], "v3_0_39_lines": ident["v3_0_39_lines"],
            "added": ident["added"], "replaced": ident["replaced"],
            "outside_rows_identical_to_v3_0_38": ident["outside_rows_identical_to_v3_0_38"],
            "outside_rows_sha256": ident["outside_rows_sha256"], "diff": ident["diff"], "changed_line_ids": changed,
            "flights_check": ident["flights"], "by_action": run["piece_logs"][0]["by_action"],
            "lines_kept": run["piece_logs"][0]["lines_kept"], "totals_moved_by_code": run["totals_moved_by_code"],
            "b7_before": _fam(l38), "b7_after": _fam(l39), "rows": rows, "released_default": run["released_default"]}


def main(argv):
    if argv[:1] == ["--check"]:
        s = json.loads(OUT.read_text(encoding="utf-8"))
        assert s["added"] == 0 and s["v3_0_39_lines"] == s["v3_0_38_lines"]
        assert s["replaced"] == len(s["rows"]) == len(s["changed_line_ids"])
        assert s["outside_rows_identical_to_v3_0_38"] == s["v3_0_38_lines"] - s["replaced"]
        fl = s["flights_check"]["valued_by_flight"]       # the 14 flight readings (E1 is a separate line, 3.3594 m2)
        assert round(sum(v for k, v in fl.items() if k.endswith("TREAD")), 3) == 20.010
        assert round(sum(v for k, v in fl.items() if k.endswith("STEP_LM")), 3) == 67.850
        assert round(s["b7_after"]["FIN.MARBLE.TREAD"]["valued"] - 20.010, 4) == 3.3594
        print(json.dumps({k: s[k] for k in ("replaced", "by_action", "b7_before", "b7_after")}, indent=1))
        return 0
    s = build(argv[0])
    if "--write" in argv:
        OUT.write_text(json.dumps(s, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in s.items() if k != "rows"}, indent=1, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
