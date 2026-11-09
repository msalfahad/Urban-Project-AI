"""T-630 10 NOV END-TO-END BOQ DRY RUN (R-T630-1; lane I, non-candidate, research only).

Reads the V3.0.58 overlay after WIRING MANIFEST V15 (T-629, rebuilt from its committed sources, every pin checked) and
writes the all-trade BOQ table: one table per trade group of BOQ_FAMILY_MASTER 1.55.0 (B1 .. B13) and per unit, plus
the UNCODED groups (item codes no family owns, NOT_A_BOQ_LINE register codes), with lines present / released /
HELD blank / HELD bounded / excluded, each line's evidence status (WORKFLOW_CONTROLS s.5) and an aggregation proof
component -> line -> family subtotal -> trade subtotal -> unit total, or the exact break. Every family of the master is
listed PRESENT / HELD / EXCLUDED_ONLY / MISSING. Nothing is wired; no candidate, released (V2.9 + route G), rule,
knowledge or registry file is written; no drawing is read.

R-T630-1 (every villa on the engine's line-index scheme; the export-and-coverage method):
  (a) ONE TABLE PER TRADE AND UNIT: a family that carries lines in two units gives two rows; units are never added
      across (kg rebar shows t only at the display boundary, OWNER_RULE_REBAR s.1: kg summed at full precision, then
      / 1000, at least 3 dp, no rounding before aggregation).
  (b) A TOTAL ONLY WHERE EVERY COMPONENT IS VALUED: a family / trade / unit subtotal is printed as a total only when
      it holds no HELD line; otherwise it prints 'NO TOTAL' with the released part, the HELD count (blank / bounded /
      high open) and the bounded HELD low .. high beside, never a sum over a HELD component and never HELD as 0.
  (c) EVIDENCE PER LINE, in this order: HELD class -> HELD; a Checker verdict binding on the line content
      (VERIFIED_WHOLE -> VERIFIED; VERIFIED_COMPONENT -> PARTIALLY VERIFIED, the line aggregation not Checker
      reproduced) unless a manifest op later moved the line's quantity (the binding is by content: stale -> the op's
      status); else the last quantity op's stamp (s.5 status; WORKER-PROPOSED -> UNKNOWN); else UNKNOWN (no stamp).
      EXCLUDED lines are not BOQ lines and carry no status.
  (d) FAMILY OF A LINE = the master family that owns its item code (each code owned by exactly one family, checked);
      a code no family owns goes to UNCODED (NO_FAMILY), a master NOT_A_BOQ_LINE code to UNCODED (NOT_A_BOQ_LINE),
      both reported, never dropped and never summed into a family.
  (e) AGGREGATION RE-ADDS EXACTLY (Decimal): lines -> family -> trade -> unit grand, and the unit grand equals the
      overlay's own per-item-code totals (OV.totals) re-added per unit; any difference is a FAILURE, not a rounding.
  (f) The scorecard / statement sections (V11, T-620) are reconciliation sections keyed by their own trade label;
      they are shown BESIDE the trade they name, never merged into the candidate's line counts.
Rebuild (through the wrapper's pytest, PR #4 not merged): `URBAN_T630_WRITE=1 bash scripts/agent_env.sh pytest
--tree task-T-630 tests/t630/test_t630.py::test_write_outputs`; check: `... pytest --tree task-T-630 tests/t630`.
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
T629_DIR = ROOT / "research/agents_t629"
if str(T629_DIR) not in sys.path:
    sys.path.insert(0, str(T629_DIR))

import manifest_v15 as M15                                            # noqa: E402  (R-T629-1, read only)

OV, M9 = M15.OV, M15.M9

SCHEMA = "URBAN_T630_E2E_BOQ_DRY_RUN"
RULE = "R-T630-1"
OUT_JSON = HERE / "out/E2E_BOQ_DRY_RUN_T630.json"
OUT_MD = HERE / "out/E2E_BOQ_DRY_RUN_T630.md"
MASTER = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json"
SCORECARD = ROOT / "research/agents_t620/out/SCORECARD_T620.json"
V15 = ROOT / "research/agents_t629/out/WIRING_MANIFEST_V15.json"
GROUPS = tuple(f"B{i}" for i in range(1, 14))
UNCODED_NO_FAMILY = "UNCODED (NO_FAMILY)"
UNCODED_NOT_A_LINE = "UNCODED (NOT_A_BOQ_LINE)"
STATUSES = ("VERIFIED", "PARTIALLY VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN")
QTY_KINDS = ("ADD", "SET", "RECODE")
REBAR_UNIT = "kg"
REGISTER_PREFIX = "ARCH."          # the engine's architectural register codes (space, wall panel, opening census ...)
UNCODED_PRESENT_NOTE = {"B9-04": "its masonry material lines (units / mortar / glue) ARE in the overlay, UNCODED "
                                 "(F-T630-1)"}


class DryRunError(Exception):
    pass


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def D(x):
    return None if x is None else Decimal(str(x))


def S(x):
    if x is None:
        return None
    s = format(x.normalize(), "f") if isinstance(x, Decimal) else str(x)
    return "0" if s in ("-0", "0.0") else s


# ---- (a) the V15 overlay, rebuilt -----------------------------------------------------------------------------------

def overlay_v15():
    """the T-629 build up to after15 (same calls, same order); checked against the committed V15 output."""
    M15.pins()
    t615, walls, acc = M15._json(M15.IN["T615"]), M15._csv(M15.IN["T615_WALLS"]), M15._csv(M15.IN["T615_ACC"])
    t617, t556, t622 = M15._json(M15.IN["T617"]), M15._json(M15.IN["T556"]), M15._json(M15.IN["T622"])
    v4 = M15._json(M15.IN["V4"])
    idx, order14, rul14, after14, rep14, _ = M15.v14_state()
    written14 = {op["line_id"] for _, ops in order14 for op in ops}
    after498 = M15._state_after(idx, order14, M15.P498)
    blk, _, _ = M15.block015_rows(t615, walls, v4, after498)
    band, _ = M15.band_rows(t617, t556, dict(order14)[M15.P563])
    pantry = M15.pantry_row(t622, after14, taken=written14)
    order15 = M15.chain_into(M15.chain_into(order14, M15.P498, blk), M15.P563, band) + [(M15.P_PANTRY, [pantry])]
    after15, rep = OV.apply(idx, order15, list(rul14) + M15.RULINGS_V15)
    v15 = _json(V15)
    if len(after15) != v15["overlay"]["lines"]["after_v15"]:
        raise DryRunError("STALE_INPUT: the V15 rebuild differs from the committed V15 line count")
    t15 = OV.totals(after15)
    for k, d in v15["overlay"]["v15_vs_v14_totals"].items():
        if t15.get(k) != d["after"]:
            raise DryRunError(f"STALE_INPUT: V15 rebuild total {k} differs from the committed V15")
    return idx, order15, after15, rep


# ---- (c) evidence per line ------------------------------------------------------------------------------------------

def bindings():
    """line_id -> (binding, its line state) from the pinned LINE_INDEX_V3_0_57 (the overlay base drops the field)."""
    p = M9.T580.INDEX57
    if sha256(p) != M9.T580.PINS[p]:
        raise DryRunError("PIN: LINE_INDEX_V3_0_57 is not the pinned index")
    return {l["line_id"]: (l["binding"], OV.state(l)) for l in _json(p)["lines"] if l.get("binding")}


def last_qty_ops(order):
    """line_id -> the last quantity op (ADD / SET / RECODE) in package order."""
    out = {}
    for _, ops in order:
        for op in ops:
            if op["kind"] in QTY_KINDS:
                out[op["line_id"]] = op
    return out


def evidence_of(line, bound, op):
    if line["class"] == "EXCLUDED":
        return None, "not a BOQ line (EXCLUDED)"
    if line["class"] == "HELD":
        return "HELD", "HELD class"
    b, bstate = bound if bound else (None, None)
    moved = b is not None and not OV.same_state(bstate, OV.state(line))     # bound by content: a moved line is stale
    if b and not moved:
        if b["binding"] == "VERIFIED_WHOLE":
            return "VERIFIED", f"binding VERIFIED_WHOLE {b['verdict_id']}"
        if b["binding"] == "VERIFIED_COMPONENT":
            return "PARTIALLY VERIFIED", f"binding VERIFIED_COMPONENT {b['verdict_id']} (line aggregation not reproduced)"
        raise DryRunError(f"{line['line_id']}: unknown binding {b['binding']!r}")
    if op is not None:
        st = (op.get("evidence") or {}).get("status")
        if st is None:
            return "UNKNOWN", f"op {op['op_id']} carries no evidence stamp"
        if st == "WORKER-PROPOSED":
            return "UNKNOWN", f"op {op['op_id']} WORKER-PROPOSED (not a s.5 status)"
        if st not in STATUSES:
            raise DryRunError(f"{line['line_id']}: op status {st!r} is not a WORKFLOW_CONTROLS s.5 status")
        return st, f"op {op['op_id']}" + (" (binding stale: quantity moved)" if b else "")
    if b:
        return "UNKNOWN", f"binding {b['binding']} stale: the line's quantity moved and no op states its evidence"
    return "UNKNOWN", "no stamp"


# ---- (d) families ---------------------------------------------------------------------------------------------------

def family_map(master):
    owner = {}
    for f in master["families"]:
        for c in f["item_codes"]:
            if c in owner:
                raise DryRunError(f"item code {c} owned by {owner[c]['code']} and {f['code']}")
            owner[c] = f
    return owner


def group_of(fam):
    g = fam["group"].split()[0]
    if g not in GROUPS:
        raise DryRunError(f"family {fam['code']}: group {fam['group']!r} is not B1 .. B13")
    return g


# ---- (b)/(e) aggregation --------------------------------------------------------------------------------------------

def _acc():
    return {"lines": 0, "released_n": 0, "released": Decimal(0), "held_n": 0, "held_blank_n": 0, "held_bounded_n": 0,
            "held_low": Decimal(0), "held_high": Decimal(0), "held_high_open_n": 0, "excluded_n": 0,
            "status": {s: 0 for s in STATUSES}}


def _add(a, line, status):
    a["lines"] += 1
    if line["class"] == "RELEASED":
        a["released_n"] += 1
        a["released"] += D(line["measured_net"])
    elif line["class"] == "HELD":
        a["held_n"] += 1
        lo, hi = D(line.get("held_low")), D(line.get("held_high"))
        if lo is None and hi is None:
            a["held_blank_n"] += 1
        else:
            a["held_bounded_n"] += 1
            a["held_low"] += lo or Decimal(0)
            if hi is None:
                a["held_high_open_n"] += 1
            else:
                a["held_high"] += hi
    else:
        a["excluded_n"] += 1
    if status is not None:
        a["status"][status] += 1


def _merge(into, a):
    for k in ("lines", "released_n", "released", "held_n", "held_blank_n", "held_bounded_n", "held_low", "held_high",
              "held_high_open_n", "excluded_n"):
        into[k] += a[k]
    for s in STATUSES:
        into["status"][s] += a["status"][s]


def _out(a, unit, rebar=False):
    live = a["lines"] - a["excluded_n"]
    o = {"lines": a["lines"], "live_lines": live, "released_n": a["released_n"], "released": S(a["released"]),
         "held_n": a["held_n"], "held_blank_n": a["held_blank_n"], "held_bounded_n": a["held_bounded_n"],
         "held_low": S(a["held_low"]) if a["held_bounded_n"] else None,
         "held_high": (None if a["held_high_open_n"] else S(a["held_high"])) if a["held_bounded_n"] else None,
         "held_high_open_n": a["held_high_open_n"], "excluded_n": a["excluded_n"],
         "status": {s: n for s, n in a["status"].items() if n}}
    if live == 0:
        o["total"], o["total_state"] = None, "NO LIVE LINE"
    elif a["held_n"] == 0:
        o["total"], o["total_state"] = S(a["released"]), "TOTAL (every component valued)"
    else:
        parts = [f"{a['held_blank_n']} HELD blank"] if a["held_blank_n"] else []
        if a["held_bounded_n"]:
            hi = "OPEN" if a["held_high_open_n"] else S(a["held_high"])
            parts.append(f"{a['held_bounded_n']} HELD bounded {S(a['held_low'])} .. {hi}")
        o["total"], o["total_state"] = None, "NO TOTAL: " + "; ".join(parts)
    if rebar and unit == REBAR_UNIT:
        o["released_t_display"] = format((a["released"] / Decimal(1000)).quantize(Decimal("0.000001")), "f")
    return o


def bucket_of(line, owner, not_a_line):
    code = line["item_code"]
    if code in not_a_line:
        return UNCODED_NOT_A_LINE, UNCODED_NOT_A_LINE
    f = owner.get(code)
    if f is None:
        return UNCODED_NO_FAMILY, UNCODED_NO_FAMILY
    return group_of(f), f["code"]


def aggregate(after, bound, order, master):
    owner = family_map(master)
    not_a_line = set(master.get("not_a_boq_line_codes", {}))
    ops = last_qty_ops(order)
    item_acc, fam_acc, grp_acc, unit_acc, per_line = {}, {}, {}, {}, []
    uncoded_codes = {}
    for lid in sorted(after):
        line = after[lid]
        unit = line.get("unit")
        if unit is None:
            raise DryRunError(f"{lid}: line without a unit")
        grp, fam = bucket_of(line, owner, not_a_line)
        st, why = evidence_of(line, bound.get(lid), ops.get(lid))
        _add(item_acc.setdefault((grp, fam, line["item_code"], unit), _acc()), line, st)
        if grp.startswith("UNCODED"):
            uncoded_codes.setdefault((grp, line["item_code"], unit), 0)
            uncoded_codes[(grp, line["item_code"], unit)] += 1
        per_line.append({"line_id": lid, "group": grp, "family": fam, "item_code": line["item_code"], "unit": unit,
                         "class": line["class"], "measured_net": line.get("measured_net"),
                         "held_low": line.get("held_low"), "held_high": line.get("held_high"),
                         "evidence": st, "evidence_basis": why})
    for (grp, fam, code, unit), a in item_acc.items():
        _merge(fam_acc.setdefault((grp, fam, unit), _acc()), a)
    for (grp, fam, unit), a in fam_acc.items():
        _merge(grp_acc.setdefault((grp, unit), _acc()), a)
    for (grp, unit), a in grp_acc.items():
        _merge(unit_acc.setdefault(unit, _acc()), a)
    return owner, item_acc, fam_acc, grp_acc, unit_acc, per_line, uncoded_codes


def proof(after, item_acc, fam_acc, grp_acc, unit_acc):
    """(e): re-add lines -> family -> trade -> unit independently and against OV.totals; returns the checks."""
    checks = []
    by_unit = {}
    for line in after.values():
        u = by_unit.setdefault(line["unit"], {"released": Decimal(0), "lines": 0, "held_n": 0})
        u["lines"] += 1
        if line["class"] == "RELEASED":
            u["released"] += D(line["measured_net"])
        elif line["class"] == "HELD":
            u["held_n"] += 1
    ov = {}
    for k, t in OV.totals(after).items():
        unit = k.split("|", 1)[1]
        o = ov.setdefault(unit, {"released": Decimal(0), "held_n": 0})
        o["released"] += D(t["released"])
        o["held_n"] += t["held_n"]
    for unit in sorted(by_unit):
        item_sum = sum((a["released"] for (g, f, c, u), a in item_acc.items() if u == unit), Decimal(0))
        fam_sum = sum((a["released"] for (g, f, u), a in fam_acc.items() if u == unit), Decimal(0))
        grp_sum = sum((a["released"] for (g, u), a in grp_acc.items() if u == unit), Decimal(0))
        grand = unit_acc[unit]["released"]
        ok = by_unit[unit]["released"] == item_sum == fam_sum == grp_sum == grand == ov[unit]["released"] and \
            by_unit[unit]["held_n"] == unit_acc[unit]["held_n"] == ov[unit]["held_n"] and \
            by_unit[unit]["lines"] == unit_acc[unit]["lines"]
        checks.append({"unit": unit, "lines": by_unit[unit]["lines"], "released_lines_sum": S(by_unit[unit]["released"]),
                       "boq_lines_sum": S(item_sum), "families_sum": S(fam_sum), "trades_sum": S(grp_sum), "unit_grand": S(grand),
                       "overlay_totals_sum": S(ov[unit]["released"]), "held_n": by_unit[unit]["held_n"],
                       "re_adds_exactly": ok})
        if not ok:
            raise DryRunError(f"AGGREGATION BREAK in {unit}: lines {by_unit[unit]['released']} / items {item_sum} / families {fam_sum} / "
                              f"trades {grp_sum} / grand {grand} / overlay {ov[unit]['released']}")
    return checks


def same_quantity_codes(item_acc):
    """two item codes of one family and unit with the same released lines and quantity: a register line and its work
    line on the same elements (e.g. a wall panel register beside the block line); flagged, never summed as work."""
    out, seen = [], {}
    for (g, f, c, u), a in sorted(item_acc.items()):
        if a["released_n"] == 0:
            continue
        key = (g, f, u, a["released_n"], a["released"])
        if key in seen:
            pair = [seen[key], c]
            kind = ("REGISTER_BESIDE_WORK: a re-add over both counts the same elements twice"
                    if any(x.startswith(REGISTER_PREFIX) for x in pair) else
                    "TWO_LAYERS_SAME_AREA: separate works on one area (e.g. membrane and its screed), not a double")
            out.append({"family": f, "unit": u, "codes": pair, "released_n": a["released_n"],
                        "released": S(a["released"]), "kind": kind})
        else:
            seen[key] = c
    return out


# ---- every family listed --------------------------------------------------------------------------------------------

def family_coverage(master, fam_acc):
    out = []
    for f in master["families"]:
        rows = {u: a for (g, fam, u), a in fam_acc.items() if fam == f["code"]}
        live = sum(a["lines"] - a["excluded_n"] for a in rows.values())
        rel = sum(a["released_n"] for a in rows.values())
        if not rows and not f["item_codes"]:
            state = "MISSING (the family owns no item code: no method writes a line of it)"
        elif not rows:
            state = "MISSING (the family owns item codes, none carries a line in the overlay)"
        elif live == 0:
            state = "EXCLUDED_ONLY (lines present, none live)"
        elif rel == 0:
            state = "HELD (every live line HELD)"
        else:
            held = sum(a["held_n"] for a in rows.values())
            state = "PRESENT" + (f" with {held} HELD line(s)" if held else " (every live line valued)")
        out.append({"family": f["code"], "group": group_of(f), "item": f["item_en"], "master_unit": f.get("unit"),
                    "capability": f["capability"], "item_codes": len(f["item_codes"]), "candidate_state_1_55_0": f["candidate"]["state"],
                    "overlay_state": state, "units": sorted(rows), "lines": sum(a["lines"] for a in rows.values()),
                    "live_lines": live, "released_lines": rel})
    return out


def census_crosscheck(master, fam_acc, order, base, after, base_codes_v3058, per_line=()):
    """families whose lines no overlay op writes, and that hold no V3.0.58 (T-507) line, must equal the master's own
    candidate census of V3.0.57 per unit (lines / released lines / released / held lines / excluded lines)."""
    touched = set(base_codes_v3058)
    for _, ops in order:
        for op in ops:
            if op["kind"] in ("TEXT_ONLY", "LEDGER", "BESIDE"):
                continue
            for src in (base, after):
                if op["line_id"] in src:
                    touched.add(src[op["line_id"]]["item_code"])
            if op.get("item_code"):
                touched.add(op["item_code"])
    cen = master["candidate_census"]["families"]
    out = []
    for f in master["families"]:
        c = cen.get(f["code"], {})
        if not f["item_codes"] or touched & set(f["item_codes"]):
            continue
        for unit, u in sorted(c.get("units", {}).items()):
            a = fam_acc.get((group_of(f), f["code"], unit))
            vw = sum(1 for l in per_line if l["family"] == f["code"] and l["unit"] == unit
                     and l["evidence_basis"].startswith("binding VERIFIED_WHOLE"))
            vc = sum(1 for l in per_line if l["family"] == f["code"] and l["unit"] == unit
                     and l["evidence_basis"].startswith("binding VERIFIED_COMPONENT"))
            got = None if a is None else {"lines": a["lines"], "released_lines": a["released_n"],
                                          "released": a["released"], "held_lines": a["held_n"],
                                          "excluded_lines": a["excluded_n"], "verified_whole_lines": vw,
                                          "verified_component_lines": vc}
            ok = got is not None and all(got[k] == u[k] for k in (
                "lines", "released_lines", "held_lines", "excluded_lines", "verified_whole_lines",
                "verified_component_lines")) \
                and abs(got["released"] - Decimal(str(u["released"]))) <= Decimal("0.000001")
            out.append({"family": f["code"], "unit": unit, "census_v3_0_57": {k: u[k] for k in (
                "lines", "released_lines", "released", "held_lines", "excluded_lines", "verified_whole_lines",
                "verified_component_lines")},
                "overlay_v15": None if got is None else dict(got, released=S(got["released"])), "agrees": ok})
    return out


# ---- (f) scorecard beside -------------------------------------------------------------------------------------------

def scorecard_beside(sc):
    out = []
    for r in sc["reference_lines"]:
        out.append({"section": r["section_id"], "trade_label": r["trade"], "trade_code_of_the_section": r["trade_code"],
                    "unit": r["unit"], "line_status": r["line_status"], "reference_total": r["reference_total"],
                    "engine_valued": r["engine_valued"], "difference": r["difference"]})
    return out


def findings_and_contents(trades, cov, uncoded, doubles, grp_acc):
    def g(grp, unit):
        a = grp_acc.get((grp, unit))
        return _out(a, unit) if a else None
    nofam = [f"{c} ({u}) {n}" for (b_, c, u), n in sorted(uncoded.items()) if b_ == UNCODED_NO_FAMILY]
    missing_own = [c["family"] for c in cov if c["overlay_state"].startswith("MISSING (the family owns no")]
    missing_codes = [c["family"] for c in cov if c["overlay_state"].startswith("MISSING (the family owns item")]
    findings = {
        "F-T630-1": "item codes with NO family in BOQ_FAMILY_MASTER 1.55.0 carry live lines: " + ", ".join(nofam) +
                    " lines; B9-04 'Mortar / glue' owns no item code, so it reads MISSING while the overlay carries the "
                    "masonry material lines; the lift landing doors have no family either. A master version that maps "
                    "them (lane I registry row) is needed before the trial BOQ groups them; never dropped here.",
        "F-T630-2": "trade keys differ: the scorecard / statement V11 trade codes (B5 = plaster, B6 = paint, B12 = doors "
                    "and windows) are not the master groups (B4 = plaster and paint, B5 = ceilings, B6 = openings, B12 = "
                    "MEP); a one-to-one key is needed before the 12-13 Nov scorecard is joined to the BOQ.",
        "F-T630-3": "same released quantity on two codes of one family and unit: " + ("; ".join(
            f"{d['family']} {' = '.join(d['codes'])} {d['released']} {d['unit']} [{d['kind'].split(':')[0]}]"
            for d in doubles) or "none") + ". A REGISTER_BESIDE_WORK pair counts the same elements twice in any "
                    "re-add: the BOQ line is the work code; the register code needs a master NOT_A_BOQ_LINE ruling (as "
                    "ARCH.EXTERIOR has) before the trial BOQ prints a family figure. TWO_LAYERS pairs are separate works.",
        "F-T630-4": "no unit grand is a total: every unit carries HELD lines; trade x unit rows with every component "
                    "valued: " + (", ".join(f"{t['trade']} {t['unit']} {t['subtotal']['total']}" for t in trades
                                           if t["subtotal"]["total"] is not None) or "none") + ".",
        "F-T630-5": f"families owning no item code ({len(missing_own)}) read MISSING whatever the overlay holds: "
                    + ", ".join(missing_own) + (f"; owning codes but no line: {', '.join(missing_codes)}"
                                                if missing_codes else "") + ".",
    }
    reb, fw, ew = g("B11", "kg"), g("B10", "m2"), g("B1", "m3")
    contains = [
        "WILL contain (calculated, released in the overlay, evidence per line): " + ", ".join(
            f"{t['trade']} {t['unit']} {t['subtotal']['released_n']} lines" for t in trades
            if t["subtotal"]["released_n"] and not t["trade"].startswith("UNCODED")) + ".",
        "WILL show HELD (never 0, never blank without its cause): every trade x unit with HELD lines (section 2); "
        f"the critical gaps: rebar {reb['held_blank_n']} HELD blank + {reb['held_bounded_n']} bounded "
        f"(low {reb['held_low']} kg, high open on {reb['held_high_open_n']}); formwork {fw['held_blank_n']} HELD blank; "
        f"earthworks {ew['held_blank_n']} HELD blank + {ew['held_bounded_n']} bounded.",
        "will NOT contain a family line for: " + "; ".join(sorted({
            c["group"] + " " + c["item"] + (f" ({UNCODED_PRESENT_NOTE[c['family']]})"
                                            if c["family"] in UNCODED_PRESENT_NOTE else "")
            for c in cov if c["overlay_state"].startswith("MISSING")
            and c["capability"] in ("BLOCKED_BY_SOURCE", "NOT_IMPLEMENTED")})) + " (no source or no method).",
        "method exists but NO line is wired (MISSING with a capability above NOT_IMPLEMENTED / BLOCKED): " + "; ".join(
            f"{c['family']} {c['item']} [{c['capability']}]" for c in cov if c["overlay_state"].startswith("MISSING")
            and c["capability"] not in ("BLOCKED_BY_SOURCE", "NOT_IMPLEMENTED")) + ".",
        "WILL contain outside any family (UNCODED, F-T630-1): " + ", ".join(
            f"{t['unit']} {t['subtotal']['live_lines']} lines ({t['subtotal']['released_n']} released)"
            for t in trades if t["trade"] == UNCODED_NO_FAMILY) + ".",
        "will NOT be a complete BOQ: no trade total is printable; B12 MEP has no line at all; the trial BOQ is a "
        "candidate overlay, not released (V2.9 + route G stays the default) and only the 10 Nov Gate B merges move it.",
    ]
    return findings, contains


# ---- build ----------------------------------------------------------------------------------------------------------

def build():
    master, sc = _json(MASTER), _json(SCORECARD)
    if master.get("version") != "1.55.0":
        raise DryRunError("STALE_INPUT: BOQ_FAMILY_MASTER is not 1.55.0")
    base, order, after, rep = overlay_v15()
    owner, item_acc, fam_acc, grp_acc, unit_acc, per_line, uncoded = aggregate(after, bindings(), order, master)
    checks = proof(after, item_acc, fam_acc, grp_acc, unit_acc)
    doubles = same_quantity_codes(item_acc)
    trades = []
    for grp in list(GROUPS) + [UNCODED_NO_FAMILY, UNCODED_NOT_A_LINE]:
        units = sorted(u for (g, u) in grp_acc if g == grp)
        for unit in units:
            fams = sorted(f for (g, f, u) in fam_acc if g == grp and u == unit)
            trades.append({"trade": grp, "unit": unit, "subtotal": _out(grp_acc[(grp, unit)], unit, grp == "B11"),
                           "families": [dict(family=f, **_out(fam_acc[(grp, f, unit)], unit, grp == "B11"),
                                             boq_lines=[dict(item_code=c, **_out(item_acc[(grp, f, c, unit)], unit,
                                                                                 grp == "B11"))
                                                        for c in sorted(c for (g2, f2, c, u2) in item_acc
                                                                        if (g2, f2, u2) == (grp, f, unit))])
                                        for f in fams]})
    cov = family_coverage(master, fam_acc)
    ids57 = {l["line_id"] for l in _json(M9.T580.INDEX57)["lines"]}
    xcheck = census_crosscheck(master, fam_acc, order, base, after, {l["item_code"] for k, l in base.items() if k not in ids57},
                               per_line)
    if not all(x["agrees"] for x in xcheck):
        raise DryRunError(f"CENSUS DISAGREES: {[x for x in xcheck if not x['agrees']][:3]}")
    cov_count = {}
    for c in cov:
        k = c["overlay_state"].split(" ")[0]
        cov_count[k] = cov_count.get(k, 0) + 1
    st_count = {s: sum(1 for l in per_line if l["evidence"] == s) for s in STATUSES}
    findings, contains = findings_and_contents(trades, cov, uncoded, doubles, grp_acc)
    released_any = sum(1 for l in per_line if l["class"] == "RELEASED")
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-630",
        "candidate": M9.T580.CANDIDATE, "overlay": "WIRING MANIFEST V15 (T-629, merged 65bcbbca)",
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in (MASTER, SCORECARD, V15)},
        "not_claimed": "development villa dry run; nothing wired, nothing released (V3.0.58 NOT RELEASED; V2.9 + "
                       "route G unchanged); no accuracy figure; freelancer agreement is never proof",
        "lines": {"base_v3_0_58": len(base), "after_v15": len(after), "released": released_any,
                  "held": sum(1 for l in per_line if l["class"] == "HELD"),
                  "excluded": sum(1 for l in per_line if l["class"] == "EXCLUDED")},
        "evidence_lines": st_count,
        "verified_whole_lines": st_count["VERIFIED"],
        "trades": trades,
        "unit_grand": {u: _out(a, u) for u, a in sorted(unit_acc.items())},
        "aggregation_proof": checks,
        "census_crosscheck_untouched_families": xcheck,
        "same_quantity_codes_in_one_family": doubles,
        "family_coverage": cov, "family_coverage_count": dict(sorted(cov_count.items())),
        "uncoded_codes": [{"bucket": g, "item_code": c, "unit": u, "lines": n}
                          for (g, c, u), n in sorted(uncoded.items())],
        "scorecard_v11_beside": scorecard_beside(sc),
        "findings": findings, "contains": contains,
        "overlay_flagged_ops": [r for r in rep["rows"] if r["status"] != "APPLIED"],
        "per_line": per_line,
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n"


# ---- report ---------------------------------------------------------------------------------------------------------

def _rng(o):
    if not o["held_bounded_n"]:
        return ""
    return f"{o['held_low']} .. {'OPEN' if o['held_high'] is None else o['held_high']}"


def _st(o):
    return ", ".join(f"{k} {v}" for k, v in o["status"].items())


def render_md(b):
    L = ["# T-630 10 Nov end-to-end BOQ dry run (generated; R-T630-1)", "",
         f"Candidate {b['candidate']}; overlay {b['overlay']}. {b['not_claimed']}. Groups = BOQ_FAMILY_MASTER 1.55.0 "
         "trade groups B1 .. B13 + UNCODED. One row per trade and unit (never mixed). A total is printed only where "
         "every component is valued; HELD is never 0 and never summed into a total.", "",
         "## 1. Headline", "",
         f"- Lines after V15: {b['lines']['after_v15']} (base V3.0.58 {b['lines']['base_v3_0_58']}): released "
         f"{b['lines']['released']}, HELD {b['lines']['held']}, excluded {b['lines']['excluded']} (not BOQ lines).",
         "- Evidence per live line (WORKFLOW_CONTROLS s.5): " + ", ".join(f"{k} {v}" for k, v in
                                                                         b["evidence_lines"].items()) + ".",
         f"- VERIFIED index lines {b['verified_whole_lines']} = one group verdict over the 62 suspended-slab concrete "
         "lines (the scorecard's 1 whole line) + 4 single-line verdicts (2 lift-pit screed, GF-07 pantry wall tile, E1 "
         "steps lm). No trade subtotal is VERIFIED.",
         "- Families (103): " + ", ".join(f"{k} {v}" for k, v in b["family_coverage_count"].items()) + ".", "",
         "## 2. Trade tables (trade x unit)", "",
         "A trade x unit figure re-adds DIFFERENT items (e.g. tile + plaster + paint m2): it is the arithmetic proof "
         "line of the aggregation, not a physical quantity; the BOQ quantity is the BOQ line of section 3.", "",
         "| Trade | Unit | Live lines | Released n | Released re-add | HELD blank | HELD bounded (low .. high) | "
         "Re-add state | Evidence |", "|---|---|---|---|---|---|---|---|---|"]
    for t in b["trades"]:
        o = t["subtotal"]
        tot = o["total"] if o["total"] is not None else o["total_state"]
        L.append(f"| {t['trade']} | {t['unit']} | {o['live_lines']} | {o['released_n']} | {o['released']} | "
                 f"{o['held_blank_n']} | {o['held_bounded_n']} {_rng(o)} | {tot} | {_st(o)} |")
    L += ["", "Rebar is computed in kg at full precision; the display unit is t (OWNER_RULE_REBAR s.1): "
          + "; ".join(f"{t['trade']} released {t['subtotal']['released']} kg = {t['subtotal']['released_t_display']} t "
                      f"(released part only; {t['subtotal']['total_state']})"
                      for t in b["trades"] if "released_t_display" in t["subtotal"]) + ".", "",
          "## 3. BOQ lines (component lines -> BOQ line = family x item code x unit)", "",
          "| Trade | Family | Item code | Unit | Lines (live) | Released n | Released qty | HELD blank | HELD bounded | "
          "BOQ line total | Evidence |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in b["trades"]:
        for f in t["families"]:
            for i in f["boq_lines"]:
                tot = i["total"] if i["total"] is not None else i["total_state"]
                L.append(f"| {t['trade']} | {f['family']} | {i['item_code']} | {t['unit']} | {i['lines']} "
                         f"({i['live_lines']}) | {i['released_n']} | {i['released']} | {i['held_blank_n']} | "
                         f"{i['held_bounded_n']} {_rng(i)} | {tot} | {_st(i)} |")
    L += ["", "## 4. Aggregation proof per unit (lines = families = trades = unit grand = overlay totals)", "",
          "| Unit | Lines | Sum of released lines | BOQ lines | Families | Trades | Unit grand | Overlay OV.totals | "
          "HELD lines | Re-adds |", "|---|---|---|---|---|---|---|---|---|---|"]
    for c in b["aggregation_proof"]:
        L.append(f"| {c['unit']} | {c['lines']} | {c['released_lines_sum']} | {c['boq_lines_sum']} | "
                 f"{c['families_sum']} | {c['trades_sum']} | "
                 f"{c['unit_grand']} | {c['overlay_totals_sum']} | {c['held_n']} | "
                 f"{'EXACT' if c['re_adds_exactly'] else 'BREAK'} |")
    L += ["", "The released sums re-add exactly; every unit grand is NOT a BOQ total, because each unit carries HELD "
          "lines (the break is the HELD count in the last column, never a rounding).",
          f"Independent check: the {len(b['census_crosscheck_untouched_families'])} family x unit rows that no overlay "
          "op writes equal the master 1.55.0 candidate census of V3.0.57 (lines, released lines and quantity, held, "
          "excluded, verified whole / component lines): "
          f"{sum(x['agrees'] for x in b['census_crosscheck_untouched_families'])} agree.",
          "Same released quantity on two codes of one family: " + ("; ".join(
              f"{d['family']} {d['unit']} {' = '.join(d['codes'])} ({d['released_n']} lines, {d['released']}): "
              f"{d['kind']}" for d in b["same_quantity_codes_in_one_family"]) or "none") + ".",
          "",
          "## 5. Family coverage (every family of BOQ_FAMILY_MASTER 1.55.0)", ""]
    for state in ("MISSING", "HELD", "EXCLUDED_ONLY"):
        rows = [c for c in b["family_coverage"] if c["overlay_state"].startswith(state)]
        L.append(f"- {state} ({len(rows)}): " + "; ".join(f"{c['family']} {c['item']} [{c['capability']}]"
                                                         for c in rows) + ".")
    pres = [c for c in b["family_coverage"] if c["overlay_state"].startswith("PRESENT")]
    L.append(f"- PRESENT ({len(pres)}): " + "; ".join(f"{c['family']}" + (" (all valued)" if "every live" in
                                                                         c["overlay_state"] else "") for c in pres) + ".")
    L += ["", "## 6. UNCODED lines (reported, never dropped, never summed into a family)", ""]
    for u in b["uncoded_codes"]:
        L.append(f"- {u['bucket']}: {u['item_code']} ({u['unit']}) {u['lines']} lines")
    L += ["", "## 7. Findings", ""] + [f"- {k}: {v}" for k, v in b["findings"].items()]
    L += ["", "## 8. What the 10 Nov trial BOQ will and will not contain (from this dry run)", ""] + \
        [f"- {x}" for x in b["contains"]]
    L += ["", "Scorecard V11 sections (reconciliation, own trade labels) are listed beside in the JSON "
          "(`scorecard_v11_beside`), never merged into these counts.", ""]
    return "\n".join(L)


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    OUT_MD.write_text(render_md(b), encoding="utf-8")
    return b
