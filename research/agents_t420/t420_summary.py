"""T-420: the package summary from a finished research/agents_t420/v3037_run.py directory (outside the repository).

    python3 -I research/agents_t420/t420_summary.py <out dir of v3037_run.py> [--write]   # prints (writes summary_t420.json)
    python3 -I research/agents_t420/t420_summary.py --check                               # the committed summary closes

It checks that the run reproduced the candidate of record V3.0.36 (json d462203f), then reports, per kind and per bed,
the V3.0.37 bed lines (engine ids, line ids, item codes, states and quantities only; no coordinates, no names), the
identity block, the diff counts against V3.0.36 and V2.9, and the totals moved by code.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "summary_t420.json"
V3036_SHA = "d462203f10eb52aed0c630901ff7298397ec71483c3aa6b661fe04807ee400f2"   # T-246 Gate B (merged 61b78fe8)
BED = ("FIN.FLOOR.BED.DRY", "FIN.FLOOR.BED.WET")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _lines(p):
    raw = json.loads(Path(p).read_text(encoding="utf-8"))
    return raw["lines"] if isinstance(raw, dict) else raw


def build(d):
    d = Path(d) / "v3037"
    s36 = _sha(d / "V3_0_36_BOQ_LINES.json")
    if s36 != V3036_SHA:
        raise SystemExit(f"V3.0.36 not reproduced: {s36[:8]} != {V3036_SHA[:8]}")
    l37 = _lines(d / "V3_0_37_BOQ_LINES.json")
    run = json.loads((d / "V3_0_37_RUN.json").read_text(encoding="utf-8"))
    beds = {}
    for ln in l37:
        if ln["item_code"] not in BED:
            continue
        rec = ln["calculation"]["inputs"]["floor_bed_v3037"]
        b = beds.setdefault(ln["location"]["element_id"], {"item_code": ln["item_code"], "floor": ln["location"]["floor"],
                                                            "finish_line": rec["finish_line"], "kind": rec["kind"],
                                                            "area_status": rec["area_status"]})
        if ln["unit"] == "m2":
            b.update(m2_line=ln["line_id"], m2=ln["measured_net"], m2_state=ln["evidence_state"])
        else:
            db = rec["drawing_bound"]
            b.update(m3_line=ln["line_id"], m3_owner=[ln["bounded_range"]["low"], ln["bounded_range"]["high"]],
                     m3_drawing_bound=None if db["high"] is None else [db["low"], db["high"]],
                     b=db["b"], b_upper=db["b_upper"], owner_check=db["owner_check"])
    tot = {}
    for b in beds.values():
        t = tot.setdefault(b["kind"], {"beds": 0, "m2": 0.0, "m3_owner_low": 0.0, "m3_owner_high": 0.0,
                                       "m3_drawing_bound_high": 0.0, "beds_with_bound": 0, "area_owner_approved": 0})
        t["beds"] += 1
        t["m2"] += b["m2"]
        t["m3_owner_low"] += b["m3_owner"][0]
        t["m3_owner_high"] += b["m3_owner"][1]
        if b["m3_drawing_bound"]:
            t["m3_drawing_bound_high"] += b["m3_drawing_bound"][1]
            t["beds_with_bound"] += 1
        t["area_owner_approved"] += b["area_status"].startswith("ASSUMED")
    tot = {k: {a: round(v, 4) if isinstance(v, float) else v for a, v in t.items()} for k, t in sorted(tot.items())}
    log = run["piece_logs"][0]
    ident = run["identity"]
    return {"task": "T-420", "method": run["method"], "extends": run["extends"],
            "v3_0_36_boq_lines_sha256": s36, "v3_0_37_boq_lines_sha256": _sha(d / "V3_0_37_BOQ_LINES.json"),
            "v3_0_36_lines": ident["v3_0_36_lines"], "v3_0_37_lines": ident["v3_0_37_lines"],
            "added": ident["added"], "outside_rows_identical_to_v3_0_36": ident["outside_rows_identical_to_v3_0_36"],
            "outside_rows_sha256": ident["outside_rows_sha256"], "diff": ident["diff"], "beds_check": ident["beds"],
            "not_applicable_finish_lines": log["not_applicable"], "totals_by_kind": tot,
            "totals_moved_by_code": run["totals_moved_by_code"], "beds": dict(sorted(beds.items())),
            "released_default": run["released_default"]}


def main(argv):
    if argv[:1] == ["--check"]:
        s = json.loads(OUT.read_text(encoding="utf-8"))
        n = sum(t["beds"] for t in s["totals_by_kind"].values())
        assert n == len(s["beds"]) and s["added"] == 2 * n, "beds / lines disagree"
        for k, t in s["totals_by_kind"].items():
            bs = [b for b in s["beds"].values() if b["kind"] == k]
            assert abs(sum(b["m2"] for b in bs) - t["m2"]) < 1e-3
            assert abs(sum(b["m3_owner"][1] for b in bs) - t["m3_owner_high"]) < 1e-3
        print(json.dumps(s["totals_by_kind"], indent=1))
        return 0
    s = build(argv[0])
    if "--write" in argv:
        OUT.write_text(json.dumps(s, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in s.items() if k != "beds"}, indent=1, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
