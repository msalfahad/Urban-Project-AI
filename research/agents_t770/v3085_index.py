"""T-770 r8: ARCH_TAKEOFF_V3.0.85 = the candidate of record V3.0.84 (T-770 r7, merge f9159fac, line index
research/agents_t770/out/LINE_INDEX_V3_0_84.json) + three Checker-verified family groups and one recalled line, applied
by line id under R-T770-1 .. R-T770-6 (engine.source.arch_v3085):

  1. T-760 exterior render / paint (merged 89be1473, built on V3.0.79): 81 rows: FIN.EXT.FINISH 18, FIN.EXT.PAINT 18,
     FIN.EXT.PAINT.EDGE 38, ARCH.FACADE 4 (register gross); the 3 ARCH.FACADE_RUN 'outline 2' rows written as label
     NOT_APPLICABLE_WITH_EVIDENCE with 0 become the NOT_APPLICABLE rows (R-T770-6 v: EXCLUDED, never 0);
  2. T-780 roof layers (merged 09f8f0b2, built on V3.0.82): 19 rows restating the roof insulation / protection / finish /
     screed and the top-roof membrane, upturn and rolls (ROOF_LAYER_AREA_V1: face inside the parapet less the dome bases);
  3. T-785 wet-room waterproofing (merged fcdc94cb, built on V3.0.82): 6 sunken-room upturn rows (recess + 0.30 up) + 29
     added lines (18 upturn runs in lm beside the m2 strips, 6 sunken recess linings, 5 pantry lines the candidate lacked);
  4. RECALL (R-T770-6 w) of the T-771 exterior spatter dash line that T-770 r7 deferred by name: its carrier
     FIN.EXT.FINISH is wired by step 1, so it is recomputed from the carrier on the wired candidate (R-T770-5 t).

Reads committed files only (no drawing, no Drive):

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/v3085_index.py [--check]

Writes V3085_PACKAGE.json (the hub's --v3085-inputs), out/LINE_INDEX_V3_0_85.json, out/V3_0_85_DIFF.csv and
out/V3_0_85_SUMMARY.json; --check rebuilds in memory and fails if a committed output differs.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import arch_v3081 as B  # noqa: E402
from engine.source import arch_v3085 as A  # noqa: E402

BASE = HERE / "out/LINE_INDEX_V3_0_84.json"
BASE_SHA = "e07948d2376c1a4e6d3e1a3cf3e332d87f392e15253670b6389e5873d662804c"
SETS = {   # file, pinned sha256 (the merged fix-row sets; each equals the file at its Gate A merge)
    "T-760": (ROOT / "research/agents_t760/out/FIX_ROWS.json",
              "cbf80bb43e6dbcdd65188369eaf6043e30754863868b8e6a45eceaacb1459ca5"),
    "T-780": (ROOT / "research/agents_t780/out/FIX_ROWS.json",
              "7add7e23fae003fcb0fca354a70e7c79dc9406814427d2419d0e3d4261da233a"),
    "T-785": (ROOT / "research/agents_t785/out/FIX_ROWS.json",
              "90c1a3a48c4b64f4e779023dab9a5112e98471e8714f5d7f24edfe4bd46a02f0"),
}
RECALL_SETS = {   # R-T770-6 w: an already-wired set, pinned
    "T-771": (ROOT / "research/agents_t771/out/FIX_ROWS.json",
              "5eb803cdd7c6e16424ef2560c6f194c4d631eb6bb84e8e6ac00c623662cd863f"),
}
RECALL = {
    "T-771": {"element_ids": ["SPATTER:EXTERIOR"],
              "reason": "deferred by name in T-770 r7 (V3.0.84, R-T770-5 u) until its carrier FIN.EXT.FINISH was "
                        "wired; the merged T-760 set wires it in this package"},
}
CARRIERS = {   # R-T770-5 t: the carrier the T-771 line names in its own basis ('recompute at wiring')
    "SPATTER:EXTERIOR": {"carrier": ["FIN.EXT.FINISH", "m2"]},
}
ROW_BASES = ["ARCH_TAKEOFF_V3.0.79", "ARCH_TAKEOFF_V3.0.81", "ARCH_TAKEOFF_V3.0.82"]
PACKAGE = HERE / "V3085_PACKAGE.json"
OUT = HERE / "out"
FAMILIES = ("FIN.EXT.", "ARCH.FACADE", "FIN.ROOF.", "FIN.WP.", "FIN.SPATTER_DASH")


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load(table):
    docs, shas = {}, {}
    for name, (p, want) in table.items():
        got = _sha(p)
        if got != want:
            raise SystemExit(f"{p.name}: sha {got[:8]} is not the pinned {want[:8]}")
        shas[name] = got
        docs[name] = json.loads(p.read_text(encoding="utf-8"))
    return docs, shas


def package():
    sets, shas = _load(SETS)
    rsets, rshas = _load(RECALL_SETS)
    return {"schema": A.PACKAGE_SCHEMA, "method": A.METHOD, "base": A.EXTENDS, "row_bases": ROW_BASES,
            "set_names": list(SETS), "set_sha256": dict(shas, **{f"recall:{k}": v for k, v in rshas.items()}),
            "carriers": CARRIERS, "recall": RECALL, "recall_sets": rsets, "sets": [sets[k] for k in SETS]}


def blank(lines, prefixes=None):
    return sum(1 for ln in lines if ln["class"] == "HELD" and ln.get("held_low") is None
               and ln.get("held_high") is None and ln["item_code"] != "STR.REBAR"
               and (prefixes is None or ln["item_code"].startswith(prefixes)))


def ranged(lines, prefixes=None):
    return sum(1 for ln in lines if ln["class"] == "HELD" and not (ln.get("held_low") is None
               and ln.get("held_high") is None) and ln["item_code"] != "STR.REBAR"
               and (prefixes is None or ln["item_code"].startswith(prefixes)))


def build():
    if _sha(BASE) != BASE_SHA:
        raise SystemExit(f"{BASE.name}: sha {_sha(BASE)[:8]} is not the pinned {BASE_SHA[:8]}")
    base = json.loads(BASE.read_text(encoding="utf-8"))
    pkg = package()
    pkg_text = json.dumps(pkg, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    new, applied, late, report = A.apply_index(base, pkg)
    v4, _ = A.prepare(pkg, base["lines"], "index")
    v3, _, _, _ = A.A84.prepare(v4, base["lines"], "index")
    v1, _, _ = A.A84.A83.prepare(v3, base["lines"], "index")
    added = B.check_package(v1, A.A84.A83.EXTENDS)[1]
    spat = [ln for ln in base["lines"] if ln["item_code"] == "FIN.SPATTER_DASH"
            and "SPATTER:EXTERIOR" in str(ln.get("element_id"))]
    if spat:   # the recalled line is wired once
        raise SystemExit(f"base already carries the exterior spatter line {spat[0]['line_id']}")
    t0, t1 = B.totals_by_code(base["lines"]), B.totals_by_code(new["lines"])
    moved = {}
    for k in sorted(set(t0) | set(t1)):
        a, b = t0.get(k), t1.get(k)
        if a != b:
            moved[f"{k[0]} [{k[1]}]"] = {"before": {f: round(v, 2) if isinstance(v, float) else v
                                                    for f, v in (a or {}).items()},
                                         "after": {f: round(v, 2) if isinstance(v, float) else v
                                                   for f, v in (b or {}).items()}}
    by_set = {}
    for r in applied:
        s = by_set.setdefault(r.get("set_doc") or r["set"], {"rows": 0, "labels": {}})
        s["rows"] += 1
        s["labels"][r["label"]] = s["labels"].get(r["label"], 0) + 1
    new["inputs"] = dict(base.get("inputs") or {}, base_index=BASE_SHA,
                         fix_rows_package=hashlib.sha256(pkg_text.encode()).hexdigest())
    idx_text = json.dumps(new, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    summary = {"method": A.METHOD, "extends": A.EXTENDS, "rule": A.RULES,
               "base_index_sha256": BASE_SHA, "set_sha256": pkg["set_sha256"],
               "package_sha256": hashlib.sha256(pkg_text.encode()).hexdigest(),
               "lines_before": len(base["lines"]), "lines": len(new["lines"]), "applied": len(applied),
               "added": dict({lid: {"item_code": x["item_code"], "unit": x["unit"], "net": x["after"]["net"],
                                    "label": x["label"], "set": x["set"]} for lid, x in added.items()},
                             **{x["new_line_id"]: {"item_code": x["item_code"], "unit": x["unit"], "net": x.get("net"),
                                                   "low": x.get("low"), "high": x.get("high"), "label": x["label"],
                                                   "set": x["set"], "kind": x["kind"],
                                                   "set_figure": x.get("set_figure")} for x in late}),
               "report": report, "by_set": by_set,
               "blank_non_rebar_before": blank(base["lines"]), "blank_non_rebar_after": blank(new["lines"]),
               "ranged_non_rebar_before": ranged(base["lines"]), "ranged_non_rebar_after": ranged(new["lines"]),
               "blank_in_package_families_before": blank(base["lines"], FAMILIES),
               "blank_in_package_families_after": blank(new["lines"], FAMILIES),
               "ranged_in_package_families_before": ranged(base["lines"], FAMILIES),
               "ranged_in_package_families_after": ranged(new["lines"], FAMILIES),
               "outside_lines_identical": True,
               "index_sha256": hashlib.sha256(idx_text.encode()).hexdigest(), "totals_moved": moved}
    buf = io.StringIO()
    d = A.diff_rows(applied, added, late)
    w = csv.DictWriter(buf, fieldnames=list(d[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(d)
    return {PACKAGE: pkg_text,
            OUT / "LINE_INDEX_V3_0_85.json": idx_text,
            OUT / "V3_0_85_SUMMARY.json": json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            OUT / "V3_0_85_DIFF.csv": buf.getvalue()}, summary


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    files, s = build()
    if "--check" in argv:
        bad = [p.name for p, t in files.items() if not p.exists() or p.read_text(encoding="utf-8") != t]
        print("check:", "OK" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    OUT.mkdir(exist_ok=True)
    for p, t in files.items():
        p.write_text(t, encoding="utf-8")
    print("V3.0.85:", s["lines_before"], "->", s["lines"], "lines,", s["applied"], "applied,", len(s["added"]),
          "added | blank non-rebar", s["blank_non_rebar_before"], "->", s["blank_non_rebar_after"],
          "| ranged non-rebar", s["ranged_non_rebar_before"], "->", s["ranged_non_rebar_after"],
          "| package families blank", s["blank_in_package_families_before"], "->",
          s["blank_in_package_families_after"], "ranged", s["ranged_in_package_families_before"], "->",
          s["ranged_in_package_families_after"])
    print("by set", json.dumps(s["by_set"], sort_keys=True))
    print("report na/recalled", json.dumps({k: s["report"][k] for k in ("na_label_rows", "recalled")}))
    for k, v in s["totals_moved"].items():
        print(k, "before", json.dumps(v["before"], sort_keys=True), "after", json.dumps(v["after"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
