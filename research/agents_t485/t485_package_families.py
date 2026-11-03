"""T-485 PACKAGE -> FAMILY ATTRIBUTION by line diff: which BOQ families each merged candidate package actually changed.

Read only: imports no engine module, changes no quantity. Input: one finished candidate chain run (e.g.
research/agents_t478/v3045_run.py, whose output directory holds V3_0_<n>_BOQ_LINES.json for every version V3.0.5 ..
V3.0.45, each reproduced) and a registry for item-code ownership. Output (committed): per version, the lines sha256,
the line count and, per item code, how many lines the package ADDED, REMOVED or CHANGED against the previous version.
No drawing content, no coordinates, no names: item codes, counts and hashes only.

Why (BOARD T-485, from T-479 finding F-T479-1): the registry's pending packages carry 'changes_families_by_item_code'
only for some versions (empty for V3.0.16 .. V3.0.36), and a source scan of a package module over- or under-states it
(a module quotes codes it only filters by, or writes lines through imported constants). A family's candidate state is
a statement about LINES, so the attribution is read from the lines themselves: package V3.0.n changed family F when
at least one line of an item code F owns is added, removed or not byte-identical (canonical JSON) between V3.0.(n-1)
and V3.0.n. Each Gate B asserts every other line byte-identical, so the diff is exactly the package's rows.

    python3 -I research/agents_t485/t485_package_families.py --run <dir with V3_0_<n>_BOQ_LINES.json>
        --master rules/coverage/BOQ_FAMILY_MASTER_1.41.0.json --from 7 --to 45 --out PACKAGE_FAMILIES.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCHEMA = "URBAN_T485_PACKAGE_FAMILIES_V1"
# A line CHANGED in quantity or state: one of these fields differs (the quantity, its bound, its evidence / approval /
# material state, its unit, code or measure pair). Any other field (notes, calculation text, rfi text, source, project
# identity, deduction listing, gross / additions records, physical element, review, rule) is a RECORD change: counted
# apart ('record'), it never raises a family's candidate state (T-245 identity, T-338 line text, T-246 listings).
QTY_FIELDS = ("measured_net", "bounded_range", "evidence_state", "approval_state", "material_state", "unit",
              "item_code", "measure_pair")


def _canon(line):
    return json.dumps(line, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _lines(doc):
    """BOQ_LINES.json is a list of lines or {'lines': [...]}"""
    return doc["lines"] if isinstance(doc, dict) else doc


def diff_versions(prev, new):
    """-> {item code: {'added': n, 'removed': n, 'changed': n, 'record': n}} between two line lists (by line_id; a line
    id present in both whose QTY_FIELDS differ is CHANGED, one whose other fields only differ is RECORD). A duplicate
    line id in one list is refused (never merged)."""
    def by_id(ls):
        out = {}
        for ln in ls:
            if ln["line_id"] in out:
                raise ValueError(f"duplicate line_id {ln['line_id']}")
            out[ln["line_id"]] = ln
        return out
    a, b = by_id(prev), by_id(new)
    codes = {}

    def bump(code, k):
        codes.setdefault(code, {"added": 0, "removed": 0, "changed": 0, "record": 0})[k] += 1
    for i in sorted(set(b) - set(a)):
        bump(b[i]["item_code"], "added")
    for i in sorted(set(a) - set(b)):
        bump(a[i]["item_code"], "removed")
    for i in sorted(set(a) & set(b)):
        if _canon(a[i]) != _canon(b[i]):
            k = "changed" if any(_canon(a[i].get(f)) != _canon(b[i].get(f)) for f in QTY_FIELDS) else "record"
            bump(b[i]["item_code"], k)
            if a[i]["item_code"] != b[i]["item_code"]:        # same id, other code (never expected): both counted
                bump(a[i]["item_code"], k)
    return {c: codes[c] for c in sorted(codes)}


def owners(master):
    out = {}
    for f in master.get("families") or ():
        for c in f.get("item_codes") or ():
            out.setdefault(c, []).append(f["code"])
    return out


def families_changed(code_diff, master, record=False):
    """-> ({family: {item code: counts}}, [codes owned by no family]); a code owned by two families is listed under
    both (never split). record=False: only codes with a line added, removed or changed in quantity / state;
    record=True: only codes whose lines changed in record fields alone."""
    own, nab = owners(master), set(master.get("not_a_boq_line_codes") or {})
    fams, apart = {}, []
    for code, n in code_diff.items():
        moved = n["added"] + n["removed"] + n["changed"]
        if (not record and not moved) or (record and (moved or not n["record"])):
            continue
        fs = own.get(code)
        if not fs:
            apart.append({"item_code": code, "kind": "NOT_A_BOQ_LINE" if code in nab else "NO_FAMILY", **n})
            continue
        for f in fs:
            fams.setdefault(f, {})[code] = dict(n)
    return {f: fams[f] for f in sorted(fams)}, apart


def version_file(run, n):
    return Path(run) / f"V3_0_{n}_BOQ_LINES.json"


def attribute(run, master, first, last):
    """Diff V3.0.(n-1) -> V3.0.n for n in first+1 .. last."""
    out = {"schema": SCHEMA, "registry": master.get("version"), "versions": {}}
    prev = None
    for n in range(first, last + 1):
        p = version_file(run, n)
        raw = p.read_bytes()
        lines = _lines(json.loads(raw))
        rec = {"lines": len(lines), "lines_sha256": hashlib.sha256(raw).hexdigest()}
        if prev is not None:
            d = diff_versions(prev, lines)
            fams, apart = families_changed(d, master)
            rfams, rapart = families_changed(d, master, record=True)
            rec.update(item_codes=d, families=fams, apart=apart, record_families=sorted(rfams),
                       record_apart=rapart,
                       touched=sum(v["added"] + v["removed"] + v["changed"] for v in d.values()),
                       record_only=sum(v["record"] for v in d.values()))
        out["versions"][f"ARCH_TAKEOFF_V3.0.{n}"] = rec
        for code in {ln["item_code"] for ln in lines}:
            out.setdefault("item_code_presence", {}).setdefault(code, []).append(n)
        prev = lines
    out["item_code_presence"] = {c: out["item_code_presence"][c] for c in sorted(out.get("item_code_presence", {}))}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--master", required=True)
    ap.add_argument("--from", dest="first", type=int, default=7)
    ap.add_argument("--to", dest="last", type=int, default=45)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    master = json.loads(Path(a.master).read_text(encoding="utf-8"))
    doc = attribute(a.run, master, a.first, a.last)
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for v, r in doc["versions"].items():
        print(v, r["lines"], r["lines_sha256"][:8], r.get("touched"), sorted(r.get("families", {})), "record:",
              r.get("record_only"), r.get("record_families"), len(r.get("apart", [])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
