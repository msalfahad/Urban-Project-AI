"""T-479 REGISTRY CENSUS: a fresh, line-level census of one candidate line list against the coverage registry
(rules/coverage/BOQ_FAMILY_MASTER_<v>.json) and the Checker verdict set, family by family.

Read only: imports no engine module that computes a quantity, changes no quantity, writes only --out / --index.

Why (BOARD T-479, three findings of 2 Nov): the registry's per-family candidate blocks are dated by the package that
last moved them (every family is still 'as of' ARCH_TAKEOFF_V3.0.7 / T-193), so a family the candidate has carried
since V3.0.15 (B8-08) or V3.0.30 (B10-13, B7-13) still reads 'in_v3_0_candidate: no'; two candidate lines sat in no
family; and the trade scoreboard counts only WHOLE verdicts, so five Checker-verified B8-08 lines (COMPONENT verdicts,
each covering its whole line) were not visible as verified at all. This tool states each fact from the lines
themselves, so a registry block can be compared with a census instead of with the text of an earlier package.

Definitions (each is a test in tests/t479_registry_refresh):
- OWNER of a line = the family whose item_codes hold the line's item code. A code owned by two families is
  DOUBLY_OWNED_CODE: its lines are listed under EVERY owning family and flagged, never split or dropped. A code no
  family owns is either declared NOT_A_BOQ_LINE by the registry ('not_a_boq_line_codes', each with its evidence: an
  information / register line that is no work item of any family) or NO_FAMILY (a line outside every family). A code
  that is both owned and declared NOT_A_BOQ_LINE is NOT_A_BOQ_LINE_CONFLICT. No line is ever dropped.
- Line class as T-469 (research/agents_t469/t469_trade_scoreboard.line_class): RELEASED / HELD / EXCLUDED; a binding
  Checker downgrade moves RELEASED -> HELD (never promotes).
- Verdict binding as T-469 verdict_bindings (tools/boq_export_v1 content binding, checker within 1 %):
    VERIFIED_WHOLE      the line is bound by a WHOLE record (the group's complete scope): the line and its group are
                        verified;
    VERIFIED_COMPONENT  the line is bound by a COMPONENT record: a COMPONENT record binds exactly ONE line and its
                        engine quantity must equal that line's net (boq_export_v1.verdict_add / bind_verdict), so the
                        LINE's quantity is independently verified, while its GROUP (trade, item code, unit) still holds
                        other, unverified or held lines (owner 20:59: it never adds up to a VERIFIED group);
    UNBOUND             a record of the set names the line but no longer binds it (line absent, own content changed,
                        engine quantity moved, discrepancy above 1 %): reported with the record id, never counted.
  A held or excluded line is never verified. The two verified classes are reported apart, per unit, never summed into
  one figure, and never added to held quantities.
- Quantities per unit, never mixed: released sum, verified whole, verified component, held bounded low .. high, held
  UNKNOWN line count. A held quantity is never 0 and never added to the released figure.
- A family that owns no item code (a register, a file output, or content written under another family's code, e.g.
  stair steel under STR.REBAR) cannot be attributed lines by a line census: in_candidate 'n/a: owns no item code',
  never 'no', and it is not compared.
- Registry block staleness (compare_blocks): a family's 'in_v3_0_candidate' must agree with the census (yes when the
  candidate has at least one line of the family); a disagreement is STALE_IN_CANDIDATE with both values.

    python3 -I research/agents_t479/t479_registry_census.py --lines V3_0_45_BOQ_LINES.json --version V
        --master rules/coverage/BOQ_FAMILY_MASTER_1.41.0.json --verdicts VERDICT_V2_SET.json
        [--downgrades DOWNGRADES.json] --out CENSUS.json [--index LINE_INDEX.json]
    python3 -I research/agents_t479/t479_registry_census.py --from-index LINE_INDEX.json
        --master rules/coverage/BOQ_FAMILY_MASTER_1.41.0.json --out CENSUS.json
        (the committed line index: per line only line id, item code, unit, class, net, bounds and the binding the full
        run gave it; no drawing content; reproduces the census without the private drawings)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "research" / "agents_t469"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import t469_trade_scoreboard as T469  # noqa: E402  (line class, verdict / downgrade binding rules only)

SCHEMA = "URBAN_T479_REGISTRY_CENSUS_V1"
INDEX_SCHEMA = "URBAN_T479_LINE_INDEX_V1"
RELEASED, HELD, EXCLUDED = T469.RELEASED, T469.HELD, T469.EXCLUDED
VERIFIED_WHOLE, VERIFIED_COMPONENT, UNBOUND = "VERIFIED_WHOLE", "VERIFIED_COMPONENT", "UNBOUND"
NO_FAMILY, NOT_A_BOQ_LINE = "NO_FAMILY", "NOT_A_BOQ_LINE"
NOT_LINE_ATTRIBUTABLE = "n/a: owns no item code"


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


def owners(master):
    """-> ({item code: [family codes]}, [issue]) without refusing a doubly owned code (it is reported)."""
    out, issues = {}, []
    for f in master.get("families") or ():
        for c in f.get("item_codes") or ():
            out.setdefault(c, []).append(f["code"])
    for c, fs in sorted(out.items()):
        if len(fs) > 1:
            issues.append({"kind": "DOUBLY_OWNED_CODE", "item_code": c, "families": sorted(fs)})
    nab = master.get("not_a_boq_line_codes") or {}
    for c in sorted(nab):
        if c in out:
            issues.append({"kind": "NOT_A_BOQ_LINE_CONFLICT", "item_code": c, "families": sorted(out[c])})
        ev = (nab[c] or {}).get("evidence") if isinstance(nab[c], dict) else None
        if not ev or not all(isinstance(e, str) and e.strip() for e in ev):
            issues.append({"kind": "NOT_A_BOQ_LINE_WITHOUT_EVIDENCE", "item_code": c})
    return out, issues


def index_lines(lines, verdicts, downgrades, version):
    """-> the line index (one row per line): class after downgrades and the verdict binding of the full run."""
    dg_held, dg_status = T469.applied_downgrades(lines, downgrades)
    whole, comp, v_status = T469.verdict_bindings(lines, verdicts, version)
    bound_ok = {s["verdict_id"] for s in v_status if s.get("status") in ("BINDS", "CARRIED_BY_CONTENT")}
    unbound = {}
    for v in verdicts or ():
        vid = str(v.get("verdict_id"))
        if vid in bound_ok:
            continue
        st = next((s["status"] for s in v_status if s["verdict_id"] == vid), "NOT_EVALUATED")
        for i in v.get("line_ids") or ():
            unbound.setdefault(i, []).append({"verdict_id": vid, "scope": v.get("scope"), "status": st})
    rows = []
    for ln in sorted(lines, key=lambda x: x["line_id"]):
        c = T469.line_class(ln)
        if c == RELEASED and ln["line_id"] in dg_held:
            c = HELD
        lo, hi = (T469._bound(ln) or (None, None)) if c == HELD else (None, None)
        b = None
        if c == RELEASED and ln["line_id"] in whole:
            b = {"binding": VERIFIED_WHOLE, "verdict_id": whole[ln["line_id"]]}
        elif c == RELEASED and ln["line_id"] in comp:
            b = {"binding": VERIFIED_COMPONENT, "verdict_id": comp[ln["line_id"]]}
        rows.append({"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln["unit"], "class": c,
                     "element_id": str((ln.get("location") or {}).get("element_id") or ln.get("element_id") or ""),
                     "measured_net": _r(ln.get("measured_net")) if c == RELEASED else None,
                     "held_low": _r(lo), "held_high": _r(hi), "binding": b,
                     "unbound_records": sorted(unbound.get(ln["line_id"], []), key=lambda x: x["verdict_id"])})
    present = {r["line_id"] for r in rows}
    absent = sorted({(i, u["verdict_id"], u["scope"], u["status"]) for i, us in unbound.items() if i not in present
                     for u in us})
    return {"schema": INDEX_SCHEMA, "candidate_version": version, "lines": rows,
            "records_naming_absent_lines": [{"line_id": a[0], "verdict_id": a[1], "scope": a[2], "status": a[3]}
                                            for a in absent],
            "downgrades": dg_status}


def _blank_unit():
    return {"lines": 0, "released_lines": 0, "released": 0.0, "verified_whole_lines": 0, "verified_whole": 0.0,
            "verified_component_lines": 0, "verified_component": 0.0, "held_lines": 0, "held_low": 0.0,
            "held_high": 0.0, "held_unknown_lines": 0, "excluded_lines": 0}


def _add(agg, row):
    u = agg.setdefault(row["unit"], _blank_unit())
    u["lines"] += 1
    if row["class"] == RELEASED:
        u["released_lines"] += 1
        u["released"] += row["measured_net"]
        b = (row.get("binding") or {}).get("binding")
        if b == VERIFIED_WHOLE:
            u["verified_whole_lines"] += 1
            u["verified_whole"] += row["measured_net"]
        elif b == VERIFIED_COMPONENT:
            u["verified_component_lines"] += 1
            u["verified_component"] += row["measured_net"]
    elif row["class"] == HELD:
        u["held_lines"] += 1
        if row.get("held_low") is None or row.get("held_high") is None:
            u["held_unknown_lines"] += 1
        else:
            u["held_low"] += row["held_low"]
            u["held_high"] += row["held_high"]
    else:
        u["excluded_lines"] += 1


def _round_units(agg):
    return {k: {kk: (_r(vv) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in sorted(agg.items())}


def census(index, master):
    """-> the census document from a line index and a registry (no line dropped, every bucket reported)."""
    own, issues = owners(master)
    nab = master.get("not_a_boq_line_codes") or {}
    fams = {f["code"]: {"lines": [], "units": {}} for f in master.get("families") or ()}
    no_family, not_boq = {}, {}
    for row in index["lines"]:
        fs = own.get(row["item_code"]) or []
        if fs:
            for fc in fs:
                fams[fc]["lines"].append(row["line_id"])
                _add(fams[fc]["units"], row)
            if len(fs) > 1:
                issues.append({"kind": "DOUBLY_MAPPED_LINE", "line_id": row["line_id"], "item_code": row["item_code"],
                               "families": sorted(fs)})
        elif row["item_code"] in nab:
            b = not_boq.setdefault(row["item_code"], {"line_ids": [], "units": {}})
            b["line_ids"].append(row["line_id"])
            _add(b["units"], row)
        else:
            b = no_family.setdefault(row["item_code"], {"line_ids": [], "units": {}})
            b["line_ids"].append(row["line_id"])
            _add(b["units"], row)
            issues.append({"kind": "LINE_OUTSIDE_EVERY_FAMILY", "line_id": row["line_id"],
                           "item_code": row["item_code"]})
        for u in row.get("unbound_records") or ():
            issues.append({"kind": "UNBOUND_VERIFIED_LINE", "line_id": row["line_id"], "item_code": row["item_code"],
                           "verdict_id": u["verdict_id"], "scope": u["scope"], "status": u["status"]})
    for a in index.get("records_naming_absent_lines") or ():
        issues.append({"kind": "UNBOUND_VERIFIED_LINE", "line_id": a["line_id"], "item_code": None,
                       "verdict_id": a["verdict_id"], "scope": a["scope"], "status": a["status"]})
    fam_rows = {}
    coded = {f["code"]: bool(f.get("item_codes")) for f in master.get("families") or ()}
    for code, f in fams.items():
        present = sorted({r["item_code"] for r in index["lines"] if r["line_id"] in set(f["lines"])})
        state = ("yes" if f["lines"] else "no") if coded[code] else NOT_LINE_ATTRIBUTABLE
        fam_rows[code] = {"in_candidate": state, "lines": len(f["lines"]),
                          "item_codes_present": present, "units": _round_units(f["units"])}
    kinds = {}
    for i in issues:
        kinds[i["kind"]] = kinds.get(i["kind"], 0) + 1
    return {"schema": SCHEMA, "candidate_version": index.get("candidate_version"),
            "master_version": master.get("version"), "lines": len(index["lines"]),
            "families": fam_rows,
            "not_a_boq_lines": {c: {"line_ids": sorted(b["line_ids"]), "units": _round_units(b["units"]),
                                    "evidence": (nab[c] or {}).get("evidence")} for c, b in sorted(not_boq.items())},
            "no_family": {c: {"line_ids": sorted(b["line_ids"]), "units": _round_units(b["units"])}
                          for c, b in sorted(no_family.items())},
            "issue_counts": dict(sorted(kinds.items())), "issues": issues,
            "complete_map": not no_family and not any(i["kind"] in ("DOUBLY_MAPPED_LINE", "DOUBLY_OWNED_CODE",
                                                                    "NOT_A_BOQ_LINE_CONFLICT",
                                                                    "NOT_A_BOQ_LINE_WITHOUT_EVIDENCE")
                                                      for i in issues)}


def compare_blocks(doc, master, codes=None):
    """-> [STALE_IN_CANDIDATE rows]: registry 'in_v3_0_candidate' vs the census, for codes (default every family)."""
    out = []
    for f in master.get("families") or ():
        if codes and f["code"] not in codes:
            continue
        c = doc["families"][f["code"]]["in_candidate"]
        if c == NOT_LINE_ATTRIBUTABLE:
            continue
        if f.get("in_v3_0_candidate") != c:
            out.append({"kind": "STALE_IN_CANDIDATE", "family": f["code"], "registry": f.get("in_v3_0_candidate"),
                        "registry_as_of": (f.get("candidate") or {}).get("method_version"),
                        "census": c, "census_version": doc.get("candidate_version"),
                        "census_lines": doc["families"][f["code"]]["lines"]})
    return out


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _dump(obj):
    return json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--lines")
    ap.add_argument("--from-index")
    ap.add_argument("--version")
    ap.add_argument("--master", required=True)
    ap.add_argument("--verdicts")
    ap.add_argument("--downgrades")
    ap.add_argument("--out", required=True)
    ap.add_argument("--index")
    a = ap.parse_args(argv)
    master = _load(a.master)
    if a.from_index:
        index = _load(a.from_index)
    else:
        lines = _load(a.lines)
        lines = lines["lines"] if isinstance(lines, dict) else lines
        ver = _load(a.verdicts) if a.verdicts else []
        ver = ver["verdicts"] if isinstance(ver, dict) else ver
        dg = _load(a.downgrades) if a.downgrades else []
        dg = dg["downgrades"] if isinstance(dg, dict) else dg
        index = index_lines(lines, ver, dg, a.version)
        index["inputs"] = {k: hashlib.sha256(Path(p).read_bytes()).hexdigest() for k, p in
                           (("lines", a.lines), ("verdicts", a.verdicts), ("downgrades", a.downgrades)) if p}
        if a.index:
            Path(a.index).write_text(_dump(index), encoding="utf-8")
    doc = census(index, master)
    doc["stale_blocks"] = compare_blocks(doc, master)
    doc["inputs"] = dict(index.get("inputs") or {}, master=hashlib.sha256(Path(a.master).read_bytes()).hexdigest())
    Path(a.out).write_text(_dump(doc), encoding="utf-8")
    print(f"T-479 census {doc['candidate_version']}: {doc['lines']} lines, issues {doc['issue_counts']}, "
          f"complete_map={doc['complete_map']}, stale blocks {len(doc['stale_blocks'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
