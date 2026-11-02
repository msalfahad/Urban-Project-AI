"""T-431: summary of an ARCH_TAKEOFF_V3.0.41 run (research/agents_t431/v3041_run.py) for the Gate B integration package.
Reads ONLY the run's own files (V3_0_40_* / V3_0_41_* beside each other, the released V2.9 lines of the T-167 run) and
writes research/agents_t431/summary_t431.json: line ids, item codes, units, states and quantities only (no coordinate, no
room name, no drawing content).

    python3 -I research/agents_t431/t431_summary.py <run>/v3041 <t167 dir> [--write]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, HERE, ROOT / "research" / "agents_t446", ROOT / "research" / "agents_t435"):
    sys.path.insert(0, str(p))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402

DRY = ("FIN.FLOOR.PORCELAIN",)
VALUED = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
CODES = ("FIN.FLOOR.PORCELAIN", "ARCH.SPACE", "FIN.FLOOR.BED.DRY", "FIN.SKIRTING", "FIN.CEILING", "FIN.PAINT.CEILING",
         "FIN.CEILING.BULKHEAD")


def _lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d["lines"] if isinstance(d, dict) else d


def _q(ln):
    if ln is None:
        return None
    br = ln.get("bounded_range") or {}
    return {"state": ln["evidence_state"], "net": ln.get("measured_net"), "low": br.get("low"), "high": br.get("high")}


def _sum(lines, code, unit="m2", states=VALUED):
    return round(sum(x["measured_net"] for x in lines if x["item_code"] == code and x["unit"] == unit
                     and x["evidence_state"] in states and x.get("measured_net") is not None), 6)


def join_rows(raw, extra_dining):
    """the T-446 join (R-T446-1) on these lines; the dining piece as EXTRA (V3.0.40) or with its skirting host reason
    (V3.0.41: the +3.90 lm lives on the open-room line by named rows)."""
    import t446_alsenan as T
    keep_extra, keep_pr = T.EXTRA, T.pantry_reasons
    try:
        if extra_dining:
            T.EXTRA = keep_extra
        else:
            T.EXTRA = []
            T.pantry_reasons = lambda: keep_pr() + [{
                "space_id": "GF-RFD4E1D", "layer": T.J.SKIRTING, "code": "SKIRTING_ON_HOST_FACE",
                "line_id": "L-71e2e002", "evidence": "V3.0.41 addition rows GF-RFD4E1D:wall / :column on the "
                                                     "open-room skirting line (one room, one line)"}]
        rows = T.build(raw)[2]
    finally:
        T.EXTRA, T.pantry_reasons = keep_extra, keep_pr
    sil = [{"space_id": r["space_id"], "layer": r["layer"], "omission": (r.get("omission") or {}).get("value")}
           for r in rows if r["status"] == "SILENT_OMISSION"]
    dining = [{"space_id": r["space_id"], "layer": r["layer"], "status": r["status"],
               "line_ids": [x[:10] for x in r["line_ids"]], "line_qty": r["line_qty"], "reasons": r["reasons"]}
              for r in rows if r["space_id"].startswith("GF-RFD4E1D")]
    return {"silent": sil, "dining": dining}


def build(run, t167):
    run, t167 = Path(run), Path(t167)
    l40, l41 = _lines(run / "V3_0_40_BOQ_LINES.json"), _lines(run / "V3_0_41_BOQ_LINES.json")
    rel = _lines(t167 / "v29" / "BOQ_LINES.json")
    rk = {A30._key(x): x for x in rel}
    led = json.loads((run / "V3_0_41_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    rj = json.loads((run / "V3_0_41_RUN.json").read_text(encoding="utf-8"))
    b40 = {x["line_id"]: x for x in l40}
    rows = []
    for r in led["rows"]:
        a = next(x for x in l41 if x["line_id"] == r["line_id"])
        rows.append({"action": r["action"], "line_id": r["line_id"], "item_code": r["item_code"], "unit": r["unit"],
                     "element_id": r["element_id"], "v2_9": _q(rk.get(A30._key(a))), "v3_0_40": _q(b40.get(a["line_id"])),
                     "v3_0_41": _q(a), "evidence_status": r["evidence_status"]})
    t40, t41 = A304.code_totals(l40), A304.code_totals(l41)
    sha = {f"V3_0_{v}": hashlib.sha256((run / f"V3_0_{v}_BOQ_LINES.json").read_bytes()).hexdigest()[:8]
           for v in ("36", "37", "38", "39", "40", "41")}
    out = {"task": "T-431", "method": "ARCH_TAKEOFF_V3.0.41", "lines_json_sha256_8": sha,
           "identity": {k: rj["identity"][k] for k in ("v3_0_40_lines", "v3_0_41_lines", "added", "replaced",
                                                         "outside_rows_identical_to_v3_0_40", "pieces", "diff")},
           "rows": rows,
           "totals_moved_by_code": rj["totals_moved_by_code"],
           "valued_sums": {c: {"v3_0_40": _sum(l40, c, "lm" if c == "FIN.SKIRTING" else "m2"),
                               "v3_0_41": _sum(l41, c, "lm" if c == "FIN.SKIRTING" else "m2")} for c in CODES},
           "dry_floor_lines_m2": {"v3_0_40": _sum(l40, "FIN.FLOOR.PORCELAIN"), "v3_0_41": _sum(l41, "FIN.FLOOR.PORCELAIN")},
           "join_v3_0_40": join_rows(l40, True), "join_v3_0_41": join_rows(l41, False)}
    out["code_totals_check"] = sorted(k for k in set(t40) | set(t41) if t40.get(k) != t41.get(k))
    return out


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    s = build(argv[1], argv[2])
    text = json.dumps(s, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        (HERE / "summary_t431.json").write_text(text, encoding="utf-8")
        print("written research/agents_t431/summary_t431.json")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
