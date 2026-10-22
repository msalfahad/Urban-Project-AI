"""T-186 read-only application: the default guard on a released-baseline run (BOQ_LINES.json of a
tools/release_baseline.py run, e.g. spec V29_ROUTEG_NO_PROFILE) with the development villa's guard evidence
(dev_villa_guard_evidence.json: document register, printed records from merged / answered sources, drawn inventory,
engine element -> register element mapping). Changes no quantity, writes only to --out (outside the repository).

    python3 -I research/agents_t186/t186_apply.py <run dir>/BOQ_LINES.json --out <scratch>/t186_apply.json

Two passes: all checks, and all but DG-2 (every route G line cites one source document, so DG-2 alone holds
them all; the second pass shows what the substantive checks hold). Prints: lines resting on a convention, findings by code with line count and quantity per trade / unit, the
quantity the guard holds per trade / unit, and every DG-1 / DG-3 / DG-5 / DG-7 finding in full (ids and values only).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine.source import default_guard as DG  # noqa: E402

CONVENTIONS = ROOT / "engine" / "profiles" / "URBAN_M8_GENERIC_CONVENTIONS_V6.json"


def analyse(boq_lines, ev, conventions, disabled=()):
    glines = DG.lines_from_canonical(boq_lines, conventions, mapping=ev["mapping"], doc_alias=ev["doc_alias"])
    # route G lines with no convention are not guard lines, but the drawn inventory is checked against EVERY line
    carried = [{"id": "C:" + l["line_id"], "element_id": ev["mapping"].get(l["location"]["element_id"], {}).get(
        "element_id", l["location"]["element_id"]), "part": ev["mapping"].get(l["location"]["element_id"], {}).get(
        "part", "WHOLE"), "trade": l["trade"], "unit": l["unit"], "qty": None, "state": "EXCLUDED", "values": {}}
        for l in boq_lines if not (l.get("rule") or {}).get("conventions_used")]
    res = DG.guard(glines + carried, documents=ev["documents"], printed=ev["printed"], inventory=ev["inventory"],
                   disabled=disabled)
    by = {g["id"]: g for g in glines}
    codes = defaultdict(lambda: {"findings": 0, "lines": set(), "qty": defaultdict(float)})
    for f in res["findings"]:
        c = codes[f["code"]]
        c["findings"] += 1
        g = by.get(f["line_id"])
        if g is None or g["id"] in c["lines"]:
            continue
        c["lines"].add(g["id"])
        if g.get("qty") is not None:
            c["qty"][f"{g['trade']} {g['unit']}"] += g["qty"]
    held = defaultdict(float)
    live_before = defaultdict(float)
    for g in glines:
        if g["state"] == "PROVISIONAL":
            live_before[f"{g['trade']} {g['unit']}"] += g["qty"]
    for g in res["baseline"]:
        if g.get("info_qty") is not None:
            held[f"{g['trade']} {g['unit']}"] += g["info_qty"]
    detail = [dict(f, item_code=by.get(f["line_id"], {}).get("item_code"),
                   qty=by.get(f["line_id"], {}).get("qty")) for f in res["findings"]
              if f["check"] in ("DG-1", "DG-3", "DG-5", "DG-7")]
    pass_lines = [g["id"] for g in res["baseline"] if g.get("guard", {}).get("status") == "PASS"
                  and not g["id"].startswith("C:")]
    return {"convention_lines": len(glines),
            "live_convention_qty": {k: round(v, 3) for k, v in sorted(live_before.items())},
            "findings_by_code": {k: {"findings": v["findings"], "lines": len(v["lines"]),
                                     "qty": {q: round(x, 3) for q, x in sorted(v["qty"].items())}}
                                 for k, v in sorted(codes.items())},
            "held_by_guard": {k: round(v, 3) for k, v in sorted(held.items())},
            "pass_lines": len(pass_lines), "detail": detail}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("boq_lines")
    ap.add_argument("--out", required=True)
    ap.add_argument("--evidence", default=str(HERE / "dev_villa_guard_evidence.json"))
    a = ap.parse_args(argv)
    lines = json.loads(Path(a.boq_lines).read_text(encoding="utf-8"))
    ev = json.loads(Path(a.evidence).read_text(encoding="utf-8"))
    conv = json.loads(CONVENTIONS.read_text(encoding="utf-8"))["conventions"]
    out = {"all_checks": analyse(lines, ev, conv),
           "without_search_check": analyse(lines, ev, conv, disabled=("DG-2",))}
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for k, r in out.items():
        print(k, json.dumps({x: v for x, v in r.items() if x != "detail"}, indent=1))
    for d in out["all_checks"]["detail"]:
        print(d["code"], d["item_code"], d["line_id"], d["element_id"], d["qty"], "|", d["detail"][:220])


if __name__ == "__main__":
    main()
