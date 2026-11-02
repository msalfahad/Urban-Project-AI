"""T-471 BOQ COMPLETENESS MATRIX + COMPONENT REGISTER + COMPONENT -> BOQ LINE MAP (EIMP part 2, quantity part).

Owner follow-up 2026-11-02 (BOARD T-471; MISSION 'understand before calculating'). Independent of the quantity code: this
tool imports no engine module that computes a quantity, changes no quantity and writes only --out / --markdown. It
reads ONE project's EIMP component register (JSON, schema URBAN_T471_EIMP_REGISTER_V1), the candidate line list
(BOQ_LINES.json of any method version), the coverage registry (rules/coverage/BOQ_FAMILY_MASTER_<v>.json) and,
optionally, the Checker verdict / downgrade snapshots, and states every component once.

Definitions (each is a test in tests/t471_completeness):
- COMPONENT: one physical scope item of the project (a family, or a part of one, e.g. pool / lift pit / tank of
  B10-10), with its applicability from the project's own drawings: APPLICABLE / NOT_APPLICABLE / POSSIBLY_APPLICABLE.
  Applicability is never inferred from the candidate; NOT_APPLICABLE and APPLICABLE need drawing evidence (a register
  row without evidence is INVALID, never silently accepted).
- A component SELECTS candidate lines by item code (the codes its family owns in the registry; a code another family
  owns is CODE_NOT_OWNED_BY_FAMILY) and, optionally, by an element-id prefix. Every candidate line must be selected by
  exactly one component: none -> UNMAPPED_LINE, two or more -> DOUBLY_MAPPED_LINE (the line is listed under each
  component and flagged; it is never split or dropped).
- Every registry family must carry at least one component: a family with none is FAMILY_NOT_IN_REGISTER (a dropped
  component is reported, never assumed out of scope). A component id used twice is DUPLICATE_COMPONENT_ID. A physical
  component the project needs but the registry has no family for (family null) is a REGISTRY_GAP: kept in the matrix
  with its state and reported; it may select only item codes that no family owns (the registry's
  item_codes_without_family), so a candidate line written outside the registry is still mapped once and surfaced.
- Line class as T-469 (research/agents_t469/t469_trade_scoreboard.line_class): RELEASED / HELD / EXCLUDED; a binding
  Checker downgrade moves RELEASED -> HELD; a line is VERIFIED only under a binding WHOLE verdict within 1 % (T-469
  verdict_bindings) and not downgraded. COMPONENT / PARTIAL verdicts never verify a line.
- The FIVE STATES (owner row): NOT_APPLICABLE (evidence) / APPLICABLE_VERIFIED (every non-excluded line VERIFIED, at
  least one line) / APPLICABLE_HELD (reason: held lines, or released lines not independently verified) /
  APPLICABLE_UNMEASURED (applicable, no line: MISSING) / POSSIBLY_APPLICABLE (evidence does not settle it). The owner
  gate vocabulary is given beside it (an applicable component marked out_of_scope_freeze says so in its reason): VERIFIED / MEASURED (released, not verified) / HELD / MISSING / NOT_APPLICABLE /
  POSSIBLY_APPLICABLE. MEASURED is never VERIFIED.
- Conflicts reported, never resolved here: NOT_APPLICABLE with a quantity line (NA_WITH_QUANTITY_LINES); APPLICABLE
  whose every line is excluded (APPLICABLE_BUT_ONLY_EXCLUDED).
- Quantities per unit, never mixed: released sum, held bounded low .. high, held UNKNOWN line count. A held quantity is
  never 0 and never added to the released figure.

    python3 -I research/agents_t471/t471_completeness.py --register EIMP_REGISTER.json --lines BOQ_LINES.json
        --master rules/coverage/BOQ_FAMILY_MASTER_1.37.0.json [--verdicts V.json --downgrades D.json]
        [--version ARCH_TAKEOFF_V3.0.42] --out OUT.json [--markdown OUT.md]
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

SCHEMA = "URBAN_T471_COMPLETENESS_V1"
REGISTER_SCHEMA = "URBAN_T471_EIMP_REGISTER_V1"
APPLICABILITY = ("APPLICABLE", "NOT_APPLICABLE", "POSSIBLY_APPLICABLE")
STATES = ("NOT_APPLICABLE", "APPLICABLE_VERIFIED", "APPLICABLE_HELD", "APPLICABLE_UNMEASURED", "POSSIBLY_APPLICABLE")
GATES = ("VERIFIED", "MEASURED", "HELD", "MISSING", "NOT_APPLICABLE", "POSSIBLY_APPLICABLE")
LEVELS = (1, 2, 3, 4, 5)
VERIFIED = "VERIFIED"


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


def _has_evidence(c):
    ev = c.get("evidence")
    if isinstance(ev, str):
        return bool(ev.strip())
    return bool(ev) and all(isinstance(e, str) and e.strip() for e in ev)


def validate_register(reg, master):
    """-> list of issue dicts (structural problems of the register itself)."""
    issues = []
    if reg.get("schema") != REGISTER_SCHEMA:
        issues.append({"kind": "REGISTER_SCHEMA", "detail": f"schema {reg.get('schema')!r} != {REGISTER_SCHEMA}"})
    by_code, fams = T469.family_index(master)
    fam_codes = {f["code"]: f for f in fams}
    seen = {}
    for c in reg.get("components") or ():
        cid = c.get("component_id")
        if cid in seen:
            issues.append({"kind": "DUPLICATE_COMPONENT_ID", "component_id": cid})
        seen[cid] = c
        fam = c.get("family")
        if fam is None:
            # a physical component the registry has no family for: a REGISTRY_GAP, reported, never dropped
            issues.append({"kind": "REGISTRY_GAP", "component_id": cid, "name": c.get("name")})
            for code in c.get("item_codes") or ():
                if code in by_code:   # a gap component may only claim a code that no family owns
                    issues.append({"kind": "CODE_NOT_OWNED_BY_FAMILY", "component_id": cid, "item_code": code,
                                   "owner": by_code[code]["code"]})
            if c.get("applicability") not in APPLICABILITY:
                issues.append({"kind": "INVALID_APPLICABILITY", "component_id": cid, "value": c.get("applicability")})
            continue
        if fam not in fam_codes:
            issues.append({"kind": "UNKNOWN_FAMILY", "component_id": cid, "family": fam})
            continue
        if c.get("applicability") not in APPLICABILITY:
            issues.append({"kind": "INVALID_APPLICABILITY", "component_id": cid, "value": c.get("applicability")})
        elif c["applicability"] in ("APPLICABLE", "NOT_APPLICABLE") and not _has_evidence(c):
            issues.append({"kind": "NO_EVIDENCE", "component_id": cid, "applicability": c["applicability"]})
        if c.get("level") not in LEVELS:
            issues.append({"kind": "INVALID_RULE_LEVEL", "component_id": cid, "value": c.get("level")})
        for code in c.get("item_codes") or ():
            own = by_code.get(code)
            if own is None or own["code"] != fam:
                issues.append({"kind": "CODE_NOT_OWNED_BY_FAMILY", "component_id": cid, "item_code": code,
                               "owner": None if own is None else own["code"]})
    present = {c.get("family") for c in reg.get("components") or ()}
    for f in fams:
        if f["code"] not in present:
            issues.append({"kind": "FAMILY_NOT_IN_REGISTER", "family": f["code"], "item_en": f.get("item_en")})
    return issues


def _selects(c, ln):
    if ln.get("item_code") not in (c.get("item_codes") or ()):
        return False
    pre = c.get("element_prefix")
    if pre:
        el = str((ln.get("location") or {}).get("element_id") or ln.get("element_id") or "")
        return any(el.startswith(p) for p in ([pre] if isinstance(pre, str) else pre))
    return True


def line_states(lines, verdicts, downgrades, version):
    """-> {line_id: RELEASED / VERIFIED / HELD / EXCLUDED} with T-469 binding rules (never promotes a held line)."""
    held_dg, _ = T469.applied_downgrades(lines, downgrades)
    whole, _comp, _st = T469.verdict_bindings(lines, verdicts, version)
    out = {}
    for ln in lines:
        lid = ln["line_id"]
        k = T469.line_class(ln)
        if k == T469.RELEASED and lid in held_dg:
            k = T469.HELD
        if k == T469.RELEASED and lid in whole:
            k = VERIFIED
        out[lid] = k
    return out


def _quantities(sel, cls):
    per = {}
    for ln in sel:
        u = per.setdefault(ln.get("unit"), {"released": 0.0, "verified": 0.0, "held_low": 0.0, "held_high": 0.0,
                                            "held_unknown_lines": 0, "lines": 0})
        u["lines"] += 1
        k = cls[ln["line_id"]]
        if k in (T469.RELEASED, VERIFIED):
            u["released"] += float(ln["measured_net"])
            if k == VERIFIED:
                u["verified"] += float(ln["measured_net"])
        elif k == T469.HELD:
            b = T469._bound(ln)
            if b is None:
                u["held_unknown_lines"] += 1
            else:
                u["held_low"] += b[0]
                u["held_high"] += b[1]
    return {k: {kk: (_r(vv) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in sorted(per.items(),
            key=lambda kv: str(kv[0]))}


def state_of(c, sel, cls):
    """-> (state, gate, reason, conflict or None) for one component and its selected lines."""
    return state_of_kinds(c, [cls[ln["line_id"]] for ln in sel])


def state_of_kinds(c, kinds):
    """-> (state, gate, reason, conflict or None) from the line classes of one component's lines."""
    app = c.get("applicability")
    sel = kinds
    qty = [k for k in kinds if k != T469.EXCLUDED]
    if app == "NOT_APPLICABLE":
        conflict = "NA_WITH_QUANTITY_LINES" if qty else None
        return "NOT_APPLICABLE", "NOT_APPLICABLE", "evidence: see component", conflict
    if app == "POSSIBLY_APPLICABLE":
        return "POSSIBLY_APPLICABLE", "POSSIBLY_APPLICABLE", c.get("exceptions") or "evidence does not settle it", None
    if not sel:
        if c.get("out_of_scope_freeze"):
            return ("APPLICABLE_UNMEASURED", "MISSING", "applicable on the drawings; outside the scope freeze "
                    "(owner recovery plan 2026-11-02): stated, not dropped, no line by that decision", None)
        return "APPLICABLE_UNMEASURED", "MISSING", "applicable, no BOQ line in the candidate", None
    if not qty:
        return ("APPLICABLE_HELD", "HELD", "every line excluded although the component is applicable",
                "APPLICABLE_BUT_ONLY_EXCLUDED")
    n_held = sum(1 for k in qty if k == T469.HELD)
    if n_held:
        return "APPLICABLE_HELD", "HELD", f"{n_held} of {len(qty)} lines held", None
    if all(k == VERIFIED for k in qty):
        return "APPLICABLE_VERIFIED", "VERIFIED", "every line under a binding WHOLE Checker verdict", None
    n_un = sum(1 for k in qty if k == T469.RELEASED)
    return "APPLICABLE_HELD", "MEASURED", f"{n_un} of {len(qty)} released lines not independently verified", None


def code_lines(code_rows):
    """T-469 by_item_code rows (one candidate side) -> pseudo lines, one per counted line, so the line-level map runs
    at item-code granularity when the full line list is not at hand. Quantities stay per code (first pseudo line of a
    class carries the class total); held UNKNOWN lines carry no bound. Never invents a line: counts are the scoreboard's."""
    out, cls = [], {}
    for r in code_rows:
        code, unit = r["item_code"], r["unit"]
        ver = int(r.get("verified_whole_lines") or 0)
        rel = int(r.get("released_lines") or 0)
        held = int(r.get("held_lines") or 0)
        unk = int(r.get("held_unknown_lines") or 0)
        exc = int(r.get("excluded_lines") or 0)
        # the class total rides on the first pseudo line: RELEASED first whenever any released line is unverified, so
        # a verified quantity is never overstated (a mixed code reports verified 0, its lines counted apart)
        seq = [(T469.RELEASED, rel - ver), (VERIFIED, ver), (T469.HELD, held), (T469.EXCLUDED, exc)]
        if min(n for _, n in seq) < 0 or unk > held:
            raise ValueError(f"inconsistent scoreboard row {code!r}")
        bounded_left = held - unk
        first = {}
        for k, n in seq:
            for j in range(n):
                lid = f"{code}|{unit}|{k}|{j}"
                ln = {"line_id": lid, "item_code": code, "unit": unit, "measured_net": None, "bounded_range": None}
                if k in (VERIFIED, T469.RELEASED):
                    ln["measured_net"] = 0.0
                    if not first.get("rel"):
                        ln["measured_net"] = float(r.get("released_qty") or 0.0)
                        first["rel"] = True
                elif k == T469.HELD and bounded_left > 0:
                    bounded_left -= 1
                    lo, hi = (float(r.get("held_low") or 0.0), float(r.get("held_high") or 0.0)) if not first.get(
                        "held") else (0.0, 0.0)
                    first["held"] = True
                    ln["bounded_range"] = {"low": lo, "high": hi}
                out.append(ln)
                cls[lid] = k
    return out, cls


def collapse_code_issues(doc):
    """Item-code mode: one UNMAPPED / DOUBLY_MAPPED issue per item code (with its line count), not per pseudo line."""
    keep, agg = [], {}
    for i in doc["issues"]:
        if i["kind"] in ("UNMAPPED_LINE", "DOUBLY_MAPPED_LINE"):
            code = i["line_id"].split("|")[0]
            k = (i["kind"], code, tuple(i.get("components") or ()))
            agg[k] = agg.get(k, 0) + 1
        else:
            keep.append(i)
    for (kind, code, comps), n in sorted(agg.items()):
        rec = {"kind": kind.replace("_LINE", "_CODE"), "item_code": code, "lines": n}
        if comps:
            rec["components"] = list(comps)
        keep.append(rec)
    doc["issues"] = keep
    kinds = {}
    for i in keep:
        kinds[i["kind"]] = kinds.get(i["kind"], 0) + 1
    doc["issue_counts"] = dict(sorted(kinds.items()))
    for r in doc["rows"]:
        r["item_codes"] = sorted({lid.split("|")[0] for lid in r.pop("line_ids")})
    return doc


def build(reg, lines, master, verdicts=None, downgrades=None, version=None, classes=None):
    issues = validate_register(reg, master)
    comps = list(reg.get("components") or ())
    cls = classes if classes is not None else line_states(lines, verdicts or [], downgrades or [], version)
    claimed = {}
    rows = []
    for c in comps:
        sel = [ln for ln in lines if _selects(c, ln)]
        for ln in sel:
            claimed.setdefault(ln["line_id"], []).append(c.get("component_id"))
        st, gate, reason, conflict = state_of(c, sel, cls)
        if conflict:
            issues.append({"kind": conflict, "component_id": c.get("component_id"), "lines": len(sel)})
        rows.append({"component_id": c.get("component_id"), "family": c.get("family"), "name": c.get("name"),
                     "applicability": c.get("applicability"), "state": st, "gate": gate, "reason": reason,
                     "level": c.get("level"), "line_ids": sorted(ln["line_id"] for ln in sel),
                     "line_classes": {k: sum(1 for ln in sel if cls[ln["line_id"]] == k)
                                      for k in (VERIFIED, T469.RELEASED, T469.HELD, T469.EXCLUDED)},
                     "quantities": _quantities(sel, cls), "row": c.get("row")})
    unmapped = sorted(ln["line_id"] for ln in lines if ln["line_id"] not in claimed)
    doubly = {lid: sorted(cs) for lid, cs in sorted(claimed.items()) if len(cs) > 1}
    by_id = {ln["line_id"]: ln for ln in lines}
    for lid in unmapped:
        issues.append({"kind": "UNMAPPED_LINE", "line_id": lid, "item_code": by_id[lid].get("item_code")})
    for lid, cs in doubly.items():
        issues.append({"kind": "DOUBLY_MAPPED_LINE", "line_id": lid, "components": cs})
    counts = {s: sum(1 for r in rows if r["state"] == s) for s in STATES}
    gates = {g: sum(1 for r in rows if r["gate"] == g) for g in GATES}
    by_row = {r["component_id"]: r for r in rows}
    gate_items = []
    for item, cids in (reg.get("owner_gate") or {}).items():
        miss = [c for c in cids if c not in by_row]
        if miss:
            issues.append({"kind": "OWNER_GATE_UNKNOWN_COMPONENT", "item": item, "components": miss})
        gate_items.append({"item": item, "components": [
            {"component_id": c, "state": by_row[c]["state"], "gate": by_row[c]["gate"]} for c in cids if c in by_row]})
    kinds = {}
    for i in issues:
        kinds[i["kind"]] = kinds.get(i["kind"], 0) + 1
    return {"schema": SCHEMA, "project": reg.get("project"), "owner_gate": gate_items, "register_version": reg.get("version"),
            "candidate_version": version, "master_version": master.get("version"), "lines": len(lines),
            "components": len(rows), "states": counts, "gates": gates, "issue_counts": dict(sorted(kinds.items())),
            "complete_map": not unmapped and not doubly and not any(i["kind"] in (
                "FAMILY_NOT_IN_REGISTER", "DUPLICATE_COMPONENT_ID", "NO_EVIDENCE", "UNKNOWN_FAMILY",
                "INVALID_APPLICABILITY", "CODE_NOT_OWNED_BY_FAMILY") for i in issues),
            "rows": rows, "issues": issues}


def _qtext(q):
    parts = []
    for u, v in q.items():
        s = f"{v['released']:,.3f} {u} released"
        if v["verified"]:
            s += f" ({v['verified']:,.3f} verified)"
        if v["held_high"] or v["held_low"]:
            s += f" + held {v['held_low']:,.3f} .. {v['held_high']:,.3f}"
        if v["held_unknown_lines"]:
            s += f" + {v['held_unknown_lines']} held UNKNOWN"
        parts.append(s)
    return "; ".join(parts) if parts else "-"


def markdown(doc, reg):
    meta = {c["component_id"]: c for c in reg.get("components") or ()}
    out = [f"# T-471 completeness matrix: {doc['project']} ({doc['candidate_version']})", "",
           f"Register {doc['register_version']}, registry {doc['master_version']}, {doc['lines']} candidate lines, "
           f"{doc['components']} components. Complete map: **{doc['complete_map']}**.", "",
           "States: " + ", ".join(f"{k} {v}" for k, v in doc["states"].items()),
           "", "Owner gate: " + ", ".join(f"{k} {v}" for k, v in doc["gates"].items()), "",
           "Issues: " + (", ".join(f"{k} {v}" for k, v in doc["issue_counts"].items()) or "none"), "",
           "| Component | Family | State | Gate | Lines (V/R/H/X) | Quantity (released + held) | Level | Row | Reason |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in doc["rows"]:
        lc = r["line_classes"]
        out.append(f"| {r['component_id']} {meta.get(r['component_id'], {}).get('name', '')} | {r['family']} | "
                   f"{r['state']} | {r['gate']} | {lc[VERIFIED]}/{lc['RELEASED']}/{lc['HELD']}/{lc['EXCLUDED']} | "
                   f"{_qtext(r['quantities'])} | {r['level']} | {r.get('row') or '-'} | {r['reason']} |")
    if doc.get("owner_gate"):
        out += ["", "## Owner gate items (owner 2026-11-02: measured / verified / held / missing / not applicable)", "",
                "| Item | Components (gate) |", "|---|---|"]
        for g in doc["owner_gate"]:
            out.append(f"| {g['item']} | " + "; ".join(f"{c['component_id']} {c['gate']}" for c in g["components"]) + " |")
    if doc["issues"]:
        out += ["", "## Issues (reported, never resolved by this tool)", ""]
        for i in doc["issues"]:
            out.append("- " + ", ".join(f"{k}={v}" for k, v in i.items()))
    return "\n".join(out) + "\n"


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--register", required=True)
    ap.add_argument("--lines", help="BOQ_LINES.json of the candidate (line-level map)")
    ap.add_argument("--scoreboard", help="T-469 scoreboard JSON (item-code-level map) instead of --lines")
    ap.add_argument("--override", help="JSON {version, source, rows}: by_item_code rows replacing the scoreboard rows "
                    "of the same (item_code, unit), for a later candidate version whose deltas are pinned elsewhere")
    ap.add_argument("--side", type=int, default=1, help="scoreboard side index (T-469: 0 released, 1 candidate)")
    ap.add_argument("--master", required=True)
    ap.add_argument("--verdicts")
    ap.add_argument("--downgrades")
    ap.add_argument("--version")
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown")
    a = ap.parse_args(argv)
    reg, master = _load(a.register), _load(a.master)
    classes = None
    if a.scoreboard:
        sd = _load(a.scoreboard)["sides"][a.side]
        rows = list(sd["by_item_code"])
        if a.override:
            ov = _load(a.override)
            keyed = {(r["item_code"], r["unit"]): r for r in ov["rows"]}
            missing = [k for k in keyed if k not in {(r["item_code"], r["unit"]) for r in rows}]
            rows = [keyed.get((r["item_code"], r["unit"]), r) for r in rows] + [keyed[k] for k in missing]
            a.version = a.version or ov.get("version")
        lines, classes = code_lines(rows)
        a.version = a.version or sd.get("version")
        a.lines = a.scoreboard
    else:
        lines = _load(a.lines)
        lines = lines["lines"] if isinstance(lines, dict) else lines
    ver = _load(a.verdicts) if a.verdicts else []
    ver = ver["verdicts"] if isinstance(ver, dict) else ver
    dg = _load(a.downgrades) if a.downgrades else []
    dg = dg["downgrades"] if isinstance(dg, dict) else dg
    doc = build(reg, lines, master, ver, dg, a.version, classes=classes)
    doc["granularity"] = "item_code (T-469 scoreboard counts)" if a.scoreboard else "line"
    if a.scoreboard:
        collapse_code_issues(doc)
    doc["inputs"] = {k: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16] for k, p in
                     (("register", a.register), ("lines", a.lines), ("master", a.master), ("verdicts", a.verdicts),
                      ("override", a.override),
                      ("downgrades", a.downgrades)) if p}
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    if a.markdown:
        Path(a.markdown).write_text(markdown(doc, reg), encoding="utf-8")
    print(f"T-471: {doc['components']} components, states {doc['states']}, issues {doc['issue_counts']}, "
          f"complete_map={doc['complete_map']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
