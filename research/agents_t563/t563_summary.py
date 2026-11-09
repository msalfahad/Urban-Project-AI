"""T-563 (read-only): the integration package summary of ARCH_TAKEOFF_V3.0.61 from a finished v3061_run.py run on the
Drive copies (numbers only: line ids, item codes, units, states, quantities; no coordinate, no name):

  1. per restated line: before (V3.0.60) -> after (V3.0.61) class / value / range, room, paint pair before = after;
  2. the line-by-line diff V3.0.60 -> V3.0.61 (SAME / CHANGED / ADDED) and the code totals that moved;
  3. the binding re-read (T-558 manifest step 3): the merged T-454 table (research/agents_t454, unchanged) is built on
     a line index of each candidate; only rows of the 11 lines may differ, and each of the 132 bindings must be the
     manifest's expected_after (22 WALL_PLASTER mortar bounds = held range x 0.020 m, rounded 9; 110 stay blank);
     the merged T-489 mix table is built the same way (it reads the T-454 mortar m3: one physical mortar, never added);
  4. the released V2.9 + route G comparison counts from the run's diff.

    .work/venv/bin/python -I research/agents_t563/t563_summary.py <run dir> [--write]
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, HERE, ROOT / "research" / "agents_t469", ROOT / "research" / "agents_t454",
          ROOT / "research" / "agents_t489"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t469_trade_scoreboard as T469  # noqa: E402
import t454_plaster_materials as T454  # noqa: E402
import t489_plaster_mix as T489  # noqa: E402
import t563_inputs as L  # noqa: E402
from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402

OUT = HERE / "summary_t563.json"


def _r(x, n=6):
    return None if x is None else round(float(x), n)


def index(lines, version):
    rows = []
    for ln in sorted(lines, key=lambda x: x["line_id"]):
        c = T469.line_class(ln)
        lo, hi = (T469._bound(ln) or (None, None)) if c == "HELD" else (None, None)
        rows.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln["unit"], "class": c,
                     "element_id": str((ln.get("location") or {}).get("element_id") or ""),
                     "measured_net": _r(ln.get("measured_net")) if c == "RELEASED" else None,
                     "held_low": _r(lo), "held_high": _r(hi), "binding": None, "unbound_records": []})
    return {"schema": "URBAN_T479_LINE_INDEX_V1", "candidate_version": version, "lines": rows}


BUILD = {"T-454": T454.build, "T-489": T489.build}


def table_rows(table, idx):
    with tempfile.TemporaryDirectory() as t:
        f = Path(t) / "idx.json"
        f.write_text(json.dumps(idx), encoding="utf-8")
        return {r["id"]: r for r in BUILD[table](line_index=f)["table"]["rows"]}


def binding_check(i60, i61, man, moved):
    out = {}
    for table in ("T-454", "T-489"):
        out[table] = _binding_check(table, i60, i61, man, moved)
    if out["T-454"]["wall_plaster_mortar_bound_m3"] != out["T-489"]["wall_plaster_mortar_bound_m3"]:
        raise SystemExit("T-489 does not read the T-454 mortar m3 1:1")
    out["bindings_checked"] = sum(v["bindings_checked"] for v in out.values())
    out["all_equal_manifest"] = True
    return out


def _binding_check(table, i60, i61, man, moved):
    a, b = table_rows(table, i60), table_rows(table, i61)
    if set(a) != set(b):
        raise SystemExit(f"{table} table rows differ in membership")
    diff = sorted(k for k in a if json.dumps(a[k], sort_keys=True) != json.dumps(b[k], sort_keys=True))
    if set(diff) - moved:
        raise SystemExit(f"{table} rows moved outside the 11 lines: {sorted(set(diff) - moved)}")
    exp = {r["key"]: r for r in man["bindings"]["rows"] if r["table"] == table}
    got, bad = [], []
    for key, r in sorted(exp.items()):
        _t, lid, layer, kind = key.split("|")
        x = next(y for y in b[lid]["layers"] if y["layer"] == layer)
        bound = x.get("mortar_m3_bound_beside") if kind == "mortar_m3" else None
        val = x.get(kind)
        ok = (bound == r["expected_after"]["bound"] and val is None and
              [b[lid]["held_low"], b[lid]["held_high"]] == r["expected_after"]["held_read"] and
              b[lid]["line_class"] == "HELD")
        got.append({"key": key, "bound": bound, "value": val, "expected_bound": r["expected_after"]["bound"],
                    "ok": ok, "change": r["change"]})
        if not ok:
            bad.append(key)
    if bad:
        raise SystemExit(f"{table} bindings not the manifest's expected_after: {bad[:4]}")
    fig = [g for g in got if g["change"] == "FIGURE"]
    lo = sum(g["bound"][0] for g in fig)
    hi = sum(g["bound"][1] for g in fig)
    return {"rows_moved": len(diff), "bindings_checked": len(got), "figure_rows": len(fig),
            "wall_plaster_mortar_bound_m3": [_r(lo, 7), _r(hi, 7)],
            "values_after": sum(1 for g in got if g["value"] is not None)}


def summary(d):
    l60 = json.loads((d / "V3_0_60_BOQ_LINES.json").read_text(encoding="utf-8"))
    l61 = json.loads((d / "V3_0_61_BOQ_LINES.json").read_text(encoding="utf-8"))
    l60 = l60["lines"] if isinstance(l60, dict) else l60
    l61 = l61["lines"] if isinstance(l61, dict) else l61
    run = json.loads((d / "V3_0_61_RUN.json").read_text(encoding="utf-8"))
    led = json.loads((d / "V3_0_61_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    rs, man = L.rows()
    moved = {r["line_id"] for r in rs}
    b60, b61 = {x["line_id"]: x for x in l60}, {x["line_id"]: x for x in l61}
    diff = {}
    for k, x in b61.items():
        s = "ADDED" if k not in b60 else ("SAME" if A30.line_sha(b60[k]) == A30.line_sha(x) else "CHANGED")
        diff[s] = diff.get(s, 0) + 1
    changed = sorted(k for k in b61 if k in b60 and A30.line_sha(b60[k]) != A30.line_sha(b61[k]))
    if set(changed) != moved:
        raise SystemExit(f"changed lines {len(changed)} are not the 11 restated lines")
    rows = []
    for r in rs:
        a, z = b60[r["line_id"]], b61[r["line_id"]]
        p0, p1 = b60[r["paint_line_id"]], b61[r["paint_line_id"]]
        rows.append({"room": r["room"], "line_id": r["line_id"], "before": A30._qty(a), "after": A30._qty(z),
                     "class": [T469.line_class(a), T469.line_class(z)], "paint_line_id": r["paint_line_id"],
                     "paint": A30._qty(p0), "paint_byte_identical": A30.line_sha(p0) == A30.line_sha(p1),
                     "manifest_after": [r["low"], r["high"]]})
    if not all(x["paint_byte_identical"] for x in rows):
        raise SystemExit("a paint pair moved")
    paint0 = [x for x in l60 if x["item_code"] == "FIN.PAINT"]
    paint_same = sum(1 for x in paint0 if A30.line_sha(x) == A30.line_sha(b61[x["line_id"]]))
    t0, t1 = A304.code_totals(l60), A304.code_totals(l61)
    i60, i61 = index(l60, "ARCH_TAKEOFF_V3.0.60"), index(l61, "ARCH_TAKEOFF_V3.0.61")
    return {"schema": "URBAN_T563_SUMMARY_V1", "method": run["method"], "extends": run["extends"],
            "v3_0_60_sha256_8": hashlib.sha256((d / "V3_0_60_BOQ_LINES.json").read_bytes()).hexdigest()[:8],
            "v3_0_61_sha256_8": hashlib.sha256((d / "V3_0_61_BOQ_LINES.json").read_bytes()).hexdigest()[:8],
            "lines": {"v3_0_60": len(l60), "v3_0_61": len(l61)}, "diff_vs_v3_0_60": diff,
            "identity": {k: run["identity"][k] for k in ("replaced", "added", "outside_rows",
                                                         "outside_rows_identical_to_base", "plaster_height",
                                                         "restated", "diff")},
            "totals_moved_by_code": run["totals_moved_by_code"],
            "fin_plaster": {"v3_0_60": t0["FIN.PLASTER|m2"], "v3_0_61": t1["FIN.PLASTER|m2"]},
            "fin_paint": {"lines": len(paint0), "byte_identical": paint_same, "totals_equal":
                          t0["FIN.PAINT|m2"] == t1["FIN.PAINT|m2"], "v3_0_61": t1["FIN.PAINT|m2"]},
            "rows": rows, "bindings": binding_check(i60, i61, man, moved),
            "ledger_rows": len(led["rows"])}


def main(argv):
    s = summary(Path(argv[1]))
    text = json.dumps(s, indent=1, sort_keys=True) + "\n"
    if "--write" in argv:
        OUT.write_text(text, encoding="utf-8")
        print("written", OUT.relative_to(ROOT))
    print(json.dumps({k: s[k] for k in ("diff_vs_v3_0_60", "totals_moved_by_code", "fin_plaster", "fin_paint",
                                        "bindings", "v3_0_60_sha256_8", "v3_0_61_sha256_8")}, indent=1))
    for r in s["rows"]:
        print(r["room"], r["line_id"], r["class"], r["before"], "->", r["after"]["low"], r["after"]["high"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
