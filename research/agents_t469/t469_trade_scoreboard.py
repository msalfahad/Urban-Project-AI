"""T-469 TRADE SCOREBOARD (owner decisions 2026-11-02, SCOREBOARD restatement): per trade, the eight owner categories
(1) expected BOQ lines, (2) measured, (3) independently verified whole lines, (4) held, (5) unmeasured, (6) provisional
material quantities, (7) fully verified procurement quantities, (8) priced / unpriced, for one candidate line list and
(optionally) the released V2.9 + route G run beside it, plus the per-family concrete statement of both sides.

Read only: imports no engine module that computes a quantity, changes no quantity, writes only --out / --markdown.

Definitions (each is a test in tests/t469_trade_scoreboard):
- EXPECTED BOQ LINE = one family of the coverage registry (rules/coverage/BOQ_FAMILY_MASTER_<v>.json, 102 families in
  1.36.0), grouped into trades by the registry's own group (B1 Site .. B13 Other). The registry is the expected scope
  until the completeness matrix (T-471) states per project which families are NOT_APPLICABLE; no family is dropped.
- A canonical line answers the family that owns its item code (the registry's item_code_scan makes that unique); a
  line whose item code no family owns is listed under NO_FAMILY, never dropped.
- Line class: a quantity state (MEASURED / SOURCE_DERIVED / PROVISIONAL) with measured_net -> RELEASED; NOT_APPLICABLE
  / EXCLUDED -> EXCLUDED (not a quantity); anything else -> HELD (BOUNDED when its bounded_range has numeric low and
  high, else UNKNOWN). A held quantity is never 0 and never summed into the released figure.
- A Checker downgrade record (URBAN_CHECKER_DOWNGRADE_V1) moves its lines RELEASED -> HELD (UNKNOWN unless the line
  carries a bound) only when it binds them (tools/boq_export_v1 rules: same project / revision set, every line present,
  own line content byte-identical, same unit and engine quantity, not resolved); it never promotes.
- Family state per side: NO_LINE (UNMEASURED: no line of the family), EXCLUDED_ONLY (every line excluded), HELD (any
  held line), MEASURED (every non-excluded line released). Quantities are kept per unit, never mixed.
- VERIFIED WHOLE LINE: a family whose every released line lies inside URBAN_CHECKER_VERDICT_V2 records of scope WHOLE
  that still bind by content (boq_export_v1.own_content_status is None on this side's lines), whose checker vs engine
  quantity is within 1 % (WORKFLOW_CONTROLS s.1), with no held line and no active downgrade. COMPONENT / PARTIAL
  records are counted apart and never make a line verified. A record bound to another candidate version is reported as
  CARRIED_BY_CONTENT (the Checker re-binds it; this tool never writes a verdict).
- MATERIAL (procurement layer) = the registry families named in MATERIAL_FAMILIES plus item codes holding a term of
  MATERIAL_CODE_TERMS; provisional = released material lines not under a binding WHOLE verdict; fully verified = under one.
- PRICED: a canonical line carries no money field (engine/source/boq_line.py refuses one), so every line is UNPRICED
  until the pricing framework (T-472) supplies approved, dated rates; priced is 0 by construction, never assumed.
- FREELANCER: only a 1:1 pair declared in the pair file (family item codes <-> freelancer cover rows of the SAME unit
  and physical element) is compared, as a DIAGNOSTIC range: (released + held low .. released + held high - ref) / ref;
  a pair with an UNKNOWN held line gives "released + UNKNOWN", never a single %, and a unit difference is refused
  (never converted). The scored keyed lines stay those of tools/alsenan_keymap.py (key map T001C).

    python3 -I research/agents_t469/t469_trade_scoreboard.py --candidate V3_0_41_BOQ_LINES.json --candidate-label L
        [--released A/BOQ_LINES.json --released-label L] --master rules/coverage/BOQ_FAMILY_MASTER_1.36.0.json
        --verdicts VERDICT_SET.json --downgrades DOWNGRADE_SET.json --reference BENCHMARK_NORMALISED.json
        --pairs FREELANCER_PAIRS.json --out OUT.json [--markdown OUT.md]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import alsenan_scoreboard as S   # noqa: E402  (unit aliases only)
from tools import boq_export_v1 as EX       # noqa: E402  (verdict / downgrade binding rules only)

SCHEMA = "URBAN_T469_TRADE_SCOREBOARD_V1"
QUANTITY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
EXCLUDED_STATES = ("NOT_APPLICABLE_WITH_EVIDENCE", "EXCLUDED_WITH_REASON")
MATERIAL_FAMILIES = ("B8-05", "B9-04", "B11-04")
MATERIAL_CODE_TERMS = ("PROCUREMENT", "ROLLS", "_COUNT", "BAGS", "PALLET")
DISCREPANCY_PCT = 1.0
RELEASED, HELD, EXCLUDED = "RELEASED", "HELD", "EXCLUDED"
NO_LINE, EXCLUDED_ONLY, FAM_HELD, MEASURED = "NO_LINE", "EXCLUDED_ONLY", "HELD", "MEASURED"


def _r(x, n=4):
    return None if x is None else round(float(x) + 0.0, n)


def _bound(ln):
    b = ln.get("bounded_range")
    if isinstance(b, dict):
        lo, hi = b.get("low"), b.get("high")
        if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and math.isfinite(lo) and math.isfinite(hi):
            return float(lo), float(hi)
    return None


def line_class(ln):
    ev = ln.get("evidence_state")
    if ev in EXCLUDED_STATES:
        return EXCLUDED
    if ev in QUANTITY_STATES and ln.get("measured_net") is not None:
        return RELEASED
    return HELD


def is_material(code, family):
    return family in MATERIAL_FAMILIES or any(t in str(code) for t in MATERIAL_CODE_TERMS)


def family_index(master):
    by_code, fams = {}, []
    for f in master["families"]:
        fams.append(f)
        for c in f.get("item_codes") or ():
            if c in by_code:
                raise ValueError(f"item code {c!r} owned by two families ({by_code[c]['code']}, {f['code']})")
            by_code[c] = f
    return by_code, fams


def applied_downgrades(lines, records):
    """-> ({line_id: downgrade_id}, [status rows]) under tools/boq_export_v1 binding rules; never promotes."""
    by_id = {ln["line_id"]: ln for ln in lines}
    pids = {(ln["project"]["project_id"], ln["project"]["revision_set_sha256"]) for ln in lines}
    held, status = {}, []
    for d in sorted(records or (), key=lambda x: str(x.get("downgrade_id"))):
        did = str(d.get("downgrade_id"))
        probs = EX.validate_downgrade(d)
        if probs:
            status.append({"downgrade_id": did, "status": "INVALID"})
            continue
        if (d["project_id"], d["revision_set_sha256"]) not in pids:
            status.append({"downgrade_id": did, "status": "OTHER_PROJECT_OR_REVISION_SET"})
            continue
        if d.get("resolved") is True:
            status.append({"downgrade_id": did, "status": "RESOLVED"})
            continue
        sel = [by_id.get(i) for i in d["line_ids"]]
        if any(x is None for x in sel):
            status.append({"downgrade_id": did, "status": "NO_LINE (not applied)"})
            continue
        if EX.line_bound(d) and EX.own_content_status(d, {x["line_id"]: x for x in sel}):
            status.append({"downgrade_id": did, "status": "STALE_CONTENT (not applied)"})
            continue
        eq = sum(float(x["measured_net"] or 0.0) for x in sel)
        if any(x["unit"] != d["unit"] for x in sel) or abs(eq - float(d["engine_qty"])) > EX.QTY_MATCH_TOL:
            status.append({"downgrade_id": did, "status": "STALE_QTY_OR_UNIT (not applied)"})
            continue
        n = 0
        for x in sel:
            if line_class(x) == RELEASED:
                held[x["line_id"]] = did
                n += 1
        status.append({"downgrade_id": did, "status": "APPLIED", "lines_to_held": n, "unit": d["unit"],
                       "engine_qty": _r(eq, 6)})
    return held, status


def verdict_bindings(lines, records, version):
    """-> ({line_id: record id} of binding WHOLE records within 1 %, {line_id: id} COMPONENT/PARTIAL, [status])."""
    by_id = {ln["line_id"]: ln for ln in lines}
    whole, comp, status = {}, {}, []
    for v in sorted(records or (), key=lambda x: str(x.get("verdict_id"))):
        vid = str(v.get("verdict_id"))
        ids = list(v.get("line_ids") or ())
        if not ids or any(i not in by_id for i in ids):
            status.append({"verdict_id": vid, "scope": v.get("scope"), "status": "STALE (a line absent)"})
            continue
        if not EX.line_bound(v) or EX.own_content_status(v, by_id):
            status.append({"verdict_id": vid, "scope": v.get("scope"), "status": "STALE (own line content changed)"})
            continue
        try:
            cq, eq = float(v["checker_qty"]), float(v["engine_qty"])
        except (TypeError, ValueError, KeyError):
            status.append({"verdict_id": vid, "scope": v.get("scope"), "status": "NO_NUMERIC_CHECKER_QTY"})
            continue
        if eq == 0 or abs(cq - eq) / abs(eq) * 100.0 > DISCREPANCY_PCT:
            status.append({"verdict_id": vid, "scope": v.get("scope"), "status": "DISCREPANCY (> 1 %)"})
            continue
        own = sum(float(by_id[i]["measured_net"] or 0.0) for i in ids)
        if abs(own - eq) > EX.QTY_MATCH_TOL:
            status.append({"verdict_id": vid, "scope": v.get("scope"), "status": "STALE (engine qty moved)"})
            continue
        tag = "BINDS" if v.get("candidate_version") == version else "CARRIED_BY_CONTENT"
        status.append({"verdict_id": vid, "scope": v.get("scope"), "status": tag, "unit": v.get("unit"),
                       "engine_qty": _r(eq, 6), "checker_qty": _r(cq, 6), "lines": len(ids),
                       "bound_to": v.get("candidate_version")})
        tgt = whole if v.get("scope") == "WHOLE" else comp
        for i in ids:
            tgt.setdefault(i, vid)
    return whole, comp, status


def side(lines, label, version, master, verdicts, downgrades):
    by_code, fams = family_index(master)
    dg_held, dg_status = applied_downgrades(lines, downgrades)
    whole, comp, v_status = verdict_bindings(lines, verdicts, version)
    fam_lines = {f["code"]: [] for f in fams}
    no_family = {}
    for ln in lines:
        f = by_code.get(ln["item_code"])
        if f is None:
            no_family.setdefault((ln["item_code"], ln["unit"]), []).append(ln)
        else:
            fam_lines[f["code"]].append(ln)
    code_agg = {}
    for ln in lines:
        c = line_class(ln)
        if c == RELEASED and ln["line_id"] in dg_held:
            c = HELD
        a = code_agg.setdefault((ln["item_code"], ln["unit"]), {"released_qty": 0.0, "released_lines": 0,
                                                                "held_lines": 0, "held_low": 0.0, "held_high": 0.0,
                                                                "held_unknown_lines": 0, "excluded_lines": 0,
                                                                "verified_whole_lines": 0})
        if c == RELEASED:
            a["released_qty"] += float(ln["measured_net"])
            a["released_lines"] += 1
            a["verified_whole_lines"] += ln["line_id"] in whole
        elif c == HELD:
            a["held_lines"] += 1
            b = _bound(ln)
            if b:
                a["held_low"] += b[0]
                a["held_high"] += b[1]
            else:
                a["held_unknown_lines"] += 1
        else:
            a["excluded_lines"] += 1
    fam_rows = []
    for f in fams:
        rows = fam_lines[f["code"]]
        per_unit = {}
        for ln in rows:
            c = line_class(ln)
            if c == RELEASED and ln["line_id"] in dg_held:
                c = HELD
            u = per_unit.setdefault(ln["unit"], {"released_lines": 0, "released_qty": 0.0, "held_lines": 0,
                                                 "held_bounded_lines": 0, "held_low": 0.0, "held_high": 0.0,
                                                 "held_unknown_lines": 0, "downgraded_lines": 0,
                                                 "excluded_lines": 0, "verified_whole_lines": 0,
                                                 "verified_whole_qty": 0.0, "component_lines": 0,
                                                 "open_range_lines": 0, "material_released_qty": 0.0,
                                                 "material_verified_qty": 0.0, "material_lines": 0,
                                                 "material_held_lines": 0})
            mat = is_material(ln["item_code"], f["code"])
            if c == EXCLUDED:
                u["excluded_lines"] += 1
            elif c == RELEASED:
                q = float(ln["measured_net"])
                u["released_lines"] += 1
                u["released_qty"] += q
                b = _bound(ln)
                if b and b[0] < b[1]:
                    u["open_range_lines"] += 1
                if ln["line_id"] in whole:
                    u["verified_whole_lines"] += 1
                    u["verified_whole_qty"] += q
                elif ln["line_id"] in comp:
                    u["component_lines"] += 1
                if mat:
                    u["material_lines"] += 1
                    u["material_released_qty"] += q
                    if ln["line_id"] in whole:
                        u["material_verified_qty"] += q
            else:
                u["held_lines"] += 1
                if ln["line_id"] in dg_held:
                    u["downgraded_lines"] += 1
                b = _bound(ln)
                if b:
                    u["held_bounded_lines"] += 1
                    u["held_low"] += b[0]
                    u["held_high"] += b[1]
                else:
                    u["held_unknown_lines"] += 1
                if mat:
                    u["material_lines"] += 1
                    u["material_held_lines"] += 1
        for u in per_unit.values():
            for k in ("released_qty", "held_low", "held_high", "verified_whole_qty", "material_released_qty",
                      "material_verified_qty"):
                u[k] = _r(u[k])
        tot = lambda k: sum(u[k] for u in per_unit.values())   # noqa: E731
        if not rows:
            st = NO_LINE
        elif tot("excluded_lines") == len(rows):
            st = EXCLUDED_ONLY
        elif tot("held_lines"):
            st = FAM_HELD
        else:
            st = MEASURED
        verified = (st == MEASURED and tot("released_lines") > 0
                    and tot("verified_whole_lines") == tot("released_lines"))
        fam_rows.append({"family": f["code"], "group": f["group"], "item_en": f["item_en"], "unit": f["unit"],
                         "item_codes": list(f.get("item_codes") or ()),
                         "capability": f.get("capability"), "state": st, "verified_whole": verified,
                         "material": f["code"] in MATERIAL_FAMILIES or any(
                             is_material(c, f["code"]) for c in (f.get("item_codes") or ())),
                         "lines": len(rows), "per_unit": dict(sorted(per_unit.items()))})
    groups = {}
    for fr in fam_rows:
        g = groups.setdefault(fr["group"], {"group": fr["group"], "expected": 0, "measured": 0, "verified_whole": 0,
                                            "held": 0, "unmeasured": 0, "excluded_only": 0, "lines": 0,
                                            "unpriced_lines": 0, "priced_lines": 0, "per_unit": {},
                                            "material_families": 0, "material_provisional": {},
                                            "material_verified": {}})
        g["expected"] += 1
        g["lines"] += fr["lines"]
        g["unpriced_lines"] += fr["lines"]
        g["measured"] += fr["state"] == MEASURED
        g["verified_whole"] += fr["verified_whole"]
        g["held"] += fr["state"] == FAM_HELD
        g["unmeasured"] += fr["state"] == NO_LINE
        g["excluded_only"] += fr["state"] == EXCLUDED_ONLY
        g["material_families"] += fr["material"]
        for unit, u in fr["per_unit"].items():
            gu = g["per_unit"].setdefault(unit, {"released_qty": 0.0, "verified_whole_qty": 0.0, "held_low": 0.0,
                                                 "held_high": 0.0, "held_unknown_lines": 0, "held_lines": 0,
                                                 "released_lines": 0})
            for k in list(gu):
                gu[k] += u[k]
            g["material_held_lines"] = g.get("material_held_lines", 0) + u["material_held_lines"]
            if u["material_lines"] - u["material_held_lines"]:
                g["material_provisional"][unit] = _r(g["material_provisional"].get(unit, 0.0)
                                                     + u["material_released_qty"] - u["material_verified_qty"])
                g["material_verified"][unit] = _r(g["material_verified"].get(unit, 0.0) + u["material_verified_qty"])
    for g in groups.values():
        for gu in g["per_unit"].values():
            for k in ("released_qty", "verified_whole_qty", "held_low", "held_high"):
                gu[k] = _r(gu[k])
        g["per_unit"] = dict(sorted(g["per_unit"].items()))
    for (c, u), a in code_agg.items():
        f = by_code.get(c)
        if f is None:
            continue
        g = groups[f["group"]]
        g["item_lines"] = g.get("item_lines", 0) + 1
        if a["released_lines"] and not a["held_lines"] and a["verified_whole_lines"] == a["released_lines"]:
            g["verified_item_lines"] = g.get("verified_item_lines", 0) + 1
            g.setdefault("verified_item_line_codes", []).append(f"{c} ({u})")
    nf = [{"item_code": c, "unit": u, "lines": len(v),
           "released_qty": _r(sum(float(x["measured_net"]) for x in v if line_class(x) == RELEASED)),
           "held_lines": sum(1 for x in v if line_class(x) == HELD)} for (c, u), v in sorted(no_family.items())]
    return {"label": label, "version": version, "lines": len(lines),
            "boq_lines_sha256": EX.lines_sha256(lines), "families": fam_rows,
            "groups": [groups[k] for k in sorted(groups, key=_group_order)], "no_family": nf,
            "by_item_code": [{"item_code": c, "unit": u, **{k: (_r(v) if isinstance(v, float) else v)
                                                             for k, v in a.items()}}
                             for (c, u), a in sorted(code_agg.items())],
            "downgrades": dg_status, "verdicts": v_status}


def _group_order(g):
    head = g.split()[0]
    return int(head[1:]) if head[1:].isdigit() else 999


def concrete_statement(sd, reference, master):
    """Per concrete family (item code): released / held / unknown of one side, never one total."""
    by_code, _ = family_index(master)
    out = []
    for fr in sd["families"]:
        if not (fr["group"].startswith("B10 ") or fr["family"] == "B7-12" or fr["family"] == "B9-02"):
            continue
        u = fr["per_unit"].get("m3")
        out.append({"family": fr["family"], "item_en": fr["item_en"], "state": fr["state"],
                    "verified_whole": fr["verified_whole"],
                    "released_qty": u["released_qty"] if u else None,
                    "released_lines": u["released_lines"] if u else 0,
                    "held_lines": u["held_lines"] if u else 0,
                    "held_low": u["held_low"] if u and u["held_bounded_lines"] else None,
                    "held_high": u["held_high"] if u and u["held_bounded_lines"] else None,
                    "held_unknown_lines": u["held_unknown_lines"] if u else 0,
                    "downgraded_lines": u["downgraded_lines"] if u else 0,
                    "verified_whole_qty": u["verified_whole_qty"] if u else None})
    return out


def ref_rows(reference):
    return {r["id"]: r for r in reference["records"]}


def pair_diag(sd, pairs, reference):
    """DIAGNOSTIC 1:1 pairs (declared, same unit and physical element), as ranges; never one % with held lines."""
    refs = ref_rows(reference)
    out = []
    lines_by_code = {fr["family"]: fr for fr in sd["families"]}
    for p in pairs["pairs"]:
        rr = [refs[i] for i in p["reference_ids"]]
        runits = {S.norm_unit(r.get("unit") or p.get("reference_unit") or "") for r in rr}
        ref_qty = sum(float(r["qty"]) for r in rr)
        fam = lines_by_code[p["family"]]
        sel = [a for a in sd["by_item_code"] if a["item_code"] in p["item_codes"] and a["unit"] == p["unit"]]
        u = None
        if sel:
            u = {k: sum(a[k] for a in sel) for k in ("released_qty", "released_lines", "held_lines", "held_low",
                                                    "held_high", "held_unknown_lines")}
            u = {k: (_r(v) if isinstance(v, float) else v) for k, v in u.items()}
        bad = [c for c in p["item_codes"] if c not in (fam["item_codes"] if "item_codes" in fam else ())]
        if bad:
            raise ValueError(f"pair {p['pair']!r}: item code(s) {bad} are not owned by family {p['family']}")
        row = {"pair": p["pair"], "family": p["family"], "item_codes": p["item_codes"], "unit": p["unit"],
               "reference_ids": p["reference_ids"], "reference_qty": _r(ref_qty), "boundary": p["boundary"]}
        if runits != {S.norm_unit(p["unit"])}:
            row.update(outcome="UNIT_MISMATCH (refused, never converted)", reference_unit=sorted(runits))
        elif u is None:
            row.update(outcome="NO_ENGINE_LINE (silent at family level)")
        else:
            rel = u["released_qty"]
            row.update(released_qty=rel, released_lines=u["released_lines"], held_lines=u["held_lines"],
                       held_unknown_lines=u["held_unknown_lines"])
            if u["held_lines"] == 0:
                row.update(outcome="ALL_RELEASED", engine_qty=rel, variance_pct=_r((rel - ref_qty) / ref_qty * 100, 2))
            elif u["held_unknown_lines"]:
                row.update(outcome="RANGE_OPEN (released + UNKNOWN held: no %)", held_low=u["held_low"],
                           held_high=u["held_high"], engine_low=_r(rel + u["held_low"]), engine_high=None)
            else:
                lo, hi = rel + u["held_low"], rel + u["held_high"]
                row.update(outcome="RANGE", engine_low=_r(lo), engine_high=_r(hi),
                           variance_low_pct=_r((lo - ref_qty) / ref_qty * 100, 2),
                           variance_high_pct=_r((hi - ref_qty) / ref_qty * 100, 2))
        out.append(row)
    return out


def keyed_ranges(sd, key_map, reference):
    """Per key of a key map without typed selectors: freelancer quantity beside this side's released + held range of
    the key's item codes (same unit only), as a range; never one % while a held line is in the key."""
    refs = ref_rows(reference)
    out = []
    for k in key_map["keys"]:
        r = refs[k["reference_id"]]
        runit = S.norm_unit(r.get("unit") or k.get("reference_unit") or "")
        row = {"key": k["key"], "trade": k["trade"], "reference_id": k["reference_id"], "reference_qty": r["qty"],
               "reference_unit": runit, "item_codes": k["item_codes"]}
        if k.get("typed_lines"):
            row["outcome"] = "TYPED_KEY (scored by tools/alsenan_keymap.py only)"
            out.append(row)
            continue
        sel = [a for a in sd["by_item_code"] if a["item_code"] in k["item_codes"]]
        same = [a for a in sel if S.norm_unit(a["unit"]) == runit]
        other = sorted({a["unit"] for a in sel if S.norm_unit(a["unit"]) != runit})
        if not same:
            row["outcome"] = f"NO_SAME_UNIT_LINE (engine units {other})" if other else "SILENT (no engine line)"
            out.append(row)
            continue
        agg = {x: sum(a[x] for a in same) for x in ("released_qty", "released_lines", "held_lines", "held_low",
                                                     "held_high", "held_unknown_lines")}
        rel, ref = agg["released_qty"], float(r["qty"])
        row.update({x: (_r(v) if isinstance(v, float) else v) for x, v in agg.items()})
        if agg["held_lines"] == 0:
            row.update(outcome="ALL_RELEASED", variance_pct=_r((rel - ref) / ref * 100, 2))
        elif agg["held_unknown_lines"]:
            row.update(outcome="RANGE_OPEN", variance_low_pct=_r((rel + agg["held_low"] - ref) / ref * 100, 2))
        else:
            row.update(outcome="RANGE", variance_low_pct=_r((rel + agg["held_low"] - ref) / ref * 100, 2),
                       variance_high_pct=_r((rel + agg["held_high"] - ref) / ref * 100, 2))
        out.append(row)
    return out


def _q(x, n=3):
    return "-" if x is None else f"{x:,.{n}f}"


def _units_text(per_unit, key):
    parts = [f"{_q(u[key])} {k}" for k, u in per_unit.items() if u.get(key)]
    return "; ".join(parts) if parts else "-"


def _held_text(per_unit):
    parts = []
    for k, u in per_unit.items():
        if not u["held_lines"]:
            continue
        b = u["held_lines"] - u["held_unknown_lines"]
        t = f"{u['held_lines']} lines {k}"
        if b:
            t += f": {b} bounded {_q(u['held_low'])} .. {_q(u['held_high'])}"
        if u["held_unknown_lines"]:
            t += f"{',' if b else ':'} {u['held_unknown_lines']} UNKNOWN"
        parts.append(t)
    return "; ".join(parts) if parts else "none"


def markdown(doc):
    out = []
    for sd in doc["sides"]:
        out.append(f"#### Eight owner categories per trade: {sd['label']} (BOQ lines sha256 {sd['boq_lines_sha256'][:8]}, "
                   f"{sd['lines']:,} canonical lines)")
        out.append("")
        out.append("| Trade (registry group) | (1) expected BOQ lines | (2) measured (families fully released; released qty of all "
                   "families) | (3) independently verified whole lines | (4) held (families with a held line) "
                   "| (5) unmeasured (family without a line) | (6) provisional material qty | (7) verified procurement qty "
                   "| (8) priced / unpriced |")
        out.append("|---|---|---|---|---|---|---|---|---|")
        for g in sd["groups"]:
            pu = g["per_unit"]
            mh = g.get("material_held_lines", 0)
            mp = "; ".join(f"{_q(v)} {k}" for k, v in g["material_provisional"].items())
            if mp and mh:
                mp += f" (+{mh} held material lines, no qty)"
            mp = mp or (f"0 released; {mh} held material lines (no qty)" if mh else None) or (
                f"0 ({g['material_families']} material families, no released material line)"
                if g["material_families"] else "n/a (no material family)")
            mv = "; ".join(f"{_q(v)} {k}" for k, v in g["material_verified"].items() if v) or (
                "0" if g["material_families"] else "n/a")
            excl = f" (+{g['excluded_only']} excluded only)" if g["excluded_only"] else ""
            out.append(f"| {g['group']} | {g['expected']} families, {g['lines']:,} lines | {g['measured']}{excl}: "
                       f"released {_units_text(pu, 'released_qty')} | {g['verified_whole']} / {g['expected']} families; "
                       f"{g.get('verified_item_lines', 0)} / {g.get('item_lines', 0)} item lines"
                       + (f" ({', '.join(g['verified_item_line_codes'])})" if g.get("verified_item_line_codes") else "")
                       + f"; verified qty {_units_text(pu, 'verified_whole_qty')} | {g['held']}: {_held_text(pu)} "
                       f"| {g['unmeasured']} | {mp} | {mv} | 0 priced / {g['unpriced_lines']:,} lines UNPRICED |")
        out.append("")
    if doc.get("concrete"):
        out.append("#### Per-family concrete statement (m3; released, held range and UNKNOWN never summed into one figure)")
        out.append("")
        sides = [s["label"] for s in doc["sides"]]
        out.append("| Family | " + " | ".join(sides) + " |")
        out.append("|---|" + "---|" * len(sides))
        fams = [r["family"] for r in doc["concrete"][0]["rows"]]
        for i, fcode in enumerate(fams):
            cells = []
            for cs in doc["concrete"]:
                r = cs["rows"][i]
                t = f"{r['state']}"
                if r["released_lines"]:
                    t += f": released {_q(r['released_qty'])} on {r['released_lines']}"
                if r["held_lines"]:
                    t += f"; held {r['held_lines']}"
                    if r["held_low"] is not None:
                        t += f" (bounded {_q(r['held_low'])} .. {_q(r['held_high'])})"
                    if r["held_unknown_lines"]:
                        t += f", {r['held_unknown_lines']} UNKNOWN"
                    if r["downgraded_lines"]:
                        t += f", {r['downgraded_lines']} by downgrade"
                if r["verified_whole"]:
                    t += " — WHOLE LINE VERIFIED"
                cells.append(t)
            r0 = doc["concrete"][0]["rows"][i]
            out.append(f"| {fcode} {r0['item_en']} | " + " | ".join(cells) + " |")
        out.append("")
    if doc.get("keyed"):
        out.append("#### Keyed reference lines as RANGES (key map T001C item codes; released + held low .. high; "
                   "UNKNOWN keeps the range open: no single %)")
        out.append("")
        labels = [k["label"] for k in doc["keyed"]]
        out.append("| Key | Freelancer | " + " | ".join(labels) + " |")
        out.append("|---|---|" + "---|" * len(labels))
        for i, r0 in enumerate(doc["keyed"][0]["rows"]):
            cells = []
            for ks in doc["keyed"]:
                r = ks["rows"][i]
                if "released_qty" not in r:
                    cells.append(r["outcome"])
                    continue
                # T-512 (F-C-T508-1 class): no released line -> 'released none', never a printed 0.000
                t = (f"released {_q(r['released_qty'])} on {r['released_lines']}" if r["released_lines"]
                     else "released none (0 lines)")
                if r["held_lines"]:
                    b = r["held_lines"] - r["held_unknown_lines"]
                    if b:
                        t += f" + held {_q(r['held_low'])} .. {_q(r['held_high'])} ({b})"
                    if r["held_unknown_lines"]:
                        t += f" + {r['held_unknown_lines']} UNKNOWN"
                if r["outcome"] == "ALL_RELEASED":
                    t += f" = {r['variance_pct']:+.2f} %"
                elif r["outcome"] == "RANGE":
                    t += f" = {r['variance_low_pct']:+.2f} .. {r['variance_high_pct']:+.2f} %"
                else:
                    t += f" = at least {r['variance_low_pct']:+.2f} %, upper end open"
                cells.append(t)
            out.append(f"| {r0['key']} | {_q(float(r0['reference_qty']))} {r0['reference_unit']} | "
                       + " | ".join(cells) + " |")
        out.append("")
    if doc.get("pairs"):
        for pd in doc["pairs"]:
            out.append(f"#### Freelancer DIAGNOSTIC pairs, {pd['label']} (declared 1:1, same unit and element; not a "
                       "score: boundary not Checker-reconciled)")
            out.append("")
            out.append("| Pair | Unit | Freelancer | Engine | Outcome | Variance |")
            out.append("|---|---|---|---|---|---|")
            for r in pd["rows"]:
                eng = (_q(r.get("engine_qty")) if r.get("engine_qty") is not None else
                       (f"{_q(r.get('engine_low'))} .. {_q(r.get('engine_high'))}" if r.get("engine_high") is not None
                        else (f"released {_q(r.get('released_qty'))}"
                              + (f" + bounded {_q(r['held_low'])} .. {_q(r['held_high'])}"
                                 if r.get("held_high") else "")
                              + f" + {r.get('held_unknown_lines')} UNKNOWN"
                              if r.get("released_qty") is not None else "-")))
                var = (f"{r['variance_pct']:+.2f} %" if r.get("variance_pct") is not None else
                       (f"{r['variance_low_pct']:+.2f} .. {r['variance_high_pct']:+.2f} %"
                        if r.get("variance_low_pct") is not None else "no % (range open or refused)"))
                out.append(f"| {r['pair']} | {r['unit']} | {_q(r['reference_qty'])} | {eng} | {r['outcome']} | {var} |")
            out.append("")
    return "\n".join(out) + "\n"


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build(cand, cand_label, cand_version, master, verdicts, downgrades, reference=None, pairs=None,
          released=None, released_label=None, key_map=None):
    sides = [side(cand, cand_label, cand_version, master, verdicts, downgrades)]
    if released is not None:
        sides.insert(0, side(released, released_label, "RELEASED_V29_ROUTEG", master, verdicts, downgrades))
    doc = {"schema": SCHEMA, "master_version": master.get("version"), "sides": sides,
           "concrete": [{"label": s["label"], "rows": concrete_statement(s, reference, master)} for s in sides]}
    if key_map is not None and reference is not None:
        doc["keyed"] = [{"label": s["label"], "rows": keyed_ranges(s, key_map, reference)} for s in sides]
    if pairs is not None and reference is not None:
        doc["pairs"] = [{"label": s["label"], "rows": pair_diag(s, pairs, reference)} for s in sides]
    return doc


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--candidate-label", required=True)
    ap.add_argument("--candidate-version", required=True)
    ap.add_argument("--released")
    ap.add_argument("--released-label")
    ap.add_argument("--master", required=True)
    ap.add_argument("--verdicts", required=True)
    ap.add_argument("--downgrades", required=True)
    ap.add_argument("--reference")
    ap.add_argument("--pairs")
    ap.add_argument("--key-map")
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown")
    a = ap.parse_args(argv)
    doc = build(_load(a.candidate), a.candidate_label, a.candidate_version, _load(a.master),
                _load(a.verdicts)["verdicts"], _load(a.downgrades)["downgrades"],
                reference=_load(a.reference) if a.reference else None, pairs=_load(a.pairs) if a.pairs else None,
                released=_load(a.released) if a.released else None, released_label=a.released_label,
                key_map=_load(a.key_map) if a.key_map else None)
    doc["inputs"] = {k: _sha(v)[:16] for k, v in (("candidate", a.candidate), ("released", a.released),
                                                  ("master", a.master), ("verdicts", a.verdicts),
                                                  ("downgrades", a.downgrades), ("reference", a.reference),
                                                  ("pairs", a.pairs), ("key_map", a.key_map)) if v}
    Path(a.out).write_text(json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    if a.markdown:
        Path(a.markdown).write_text(markdown(doc), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
