"""T-442: summary of an ARCH_TAKEOFF_V3.0.42 run (research/agents_t442/v3042_run.py) for the Gate B integration package.
Reads ONLY the run's own files (V3_0_41_* / V3_0_42_* beside each other, the released V2.9 lines of the T-167 run) and
writes research/agents_t442/summary_t442.json: line ids, item codes, units, states and quantities only (no coordinate, no
room name, no drawing content).

    python3 -I research/agents_t442/t442_summary.py <run>/v3042 <t167 dir> [--write]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402

VALUED = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
CONC = "STR.CONC."


def _lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d["lines"] if isinstance(d, dict) else d


def _q(ln):
    if ln is None:
        return None
    br = ln.get("bounded_range") or {}
    return {"state": ln["evidence_state"], "net": ln.get("measured_net"), "low": br.get("low"), "high": br.get("high")}


def _fam(lines, code):
    v = [x for x in lines if x["item_code"] == code and x["unit"] == "m3"]
    val = [x for x in v if x["evidence_state"] in VALUED and x.get("measured_net") is not None]
    held = [x for x in v if x not in val]
    return {"lines": len(v), "valued_lines": len(val), "valued_m3": round(sum(x["measured_net"] for x in val), 6),
            "held_lines": len(held),
            "held_high_m3": round(sum((x.get("bounded_range") or {}).get("high") or 0.0 for x in held), 6),
            "held_blank_lines": sum(1 for x in held if not (x.get("bounded_range") or {}).get("high"))}


def build(run, t167):
    run, t167 = Path(run), Path(t167)
    l41, l42 = _lines(run / "V3_0_41_BOQ_LINES.json"), _lines(run / "V3_0_42_BOQ_LINES.json")
    rel = _lines(t167 / "v29" / "BOQ_LINES.json")
    rk = {A30._key(x): x for x in rel}
    led = json.loads((run / "V3_0_42_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    rj = json.loads((run / "V3_0_42_RUN.json").read_text(encoding="utf-8"))
    b41 = {x["line_id"]: x for x in l41}
    rows = []
    for r in led["rows"]:
        a = next(x for x in l42 if x["line_id"] == r["line_id"])
        rows.append({"action": r["action"], "line_id": r["line_id"], "item_code": r["item_code"], "unit": r["unit"],
                     "element_id": str(r["element_id"] or "").split("@")[0], "v2_9": _q(rk.get(A30._key(a))),
                     "v3_0_41": _q(b41.get(a["line_id"])), "v3_0_42": _q(a), "evidence_status": r["evidence_status"],
                     "hits": (r["record"] or {}).get("hits")})
    t41, t42 = A304.code_totals(l41), A304.code_totals(l42)
    sha = {f"V3_0_{v}": hashlib.sha256((run / f"V3_0_{v}_BOQ_LINES.json").read_bytes()).hexdigest()[:8]
           for v in ("36", "37", "38", "39", "40", "41", "42")}
    codes = sorted({x["item_code"] for x in l42 if x["item_code"].startswith(CONC) and x["unit"] == "m3"})
    out = {"task": "T-442", "method": "ARCH_TAKEOFF_V3.0.42", "lines_json_sha256_8": sha,
           "identity": {k: rj["identity"][k] for k in ("v3_0_41_lines", "v3_0_42_lines", "added", "replaced",
                                                         "outside_rows_identical_to_v3_0_41", "slab", "diff")},
           "rows": rows, "exclusions_retired": led.get("exclusions_retired"),
           "totals_moved_by_code": rj["totals_moved_by_code"],
           "concrete_by_code": {c: {"v3_0_41": _fam(l41, c), "v3_0_42": _fam(l42, c)} for c in codes},
           "concrete_valued_m3": {"v3_0_41": round(sum(_fam(l41, c)["valued_m3"] for c in codes), 6),
                                  "v3_0_42": round(sum(_fam(l42, c)["valued_m3"] for c in codes), 6)}}
    out["code_totals_check"] = sorted(k for k in set(t41) | set(t42) if t41.get(k) != t42.get(k))
    return out


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    s = build(argv[1], argv[2])
    text = json.dumps(s, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        (HERE / "summary_t442.json").write_text(text, encoding="utf-8")
        print("written research/agents_t442/summary_t442.json")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
