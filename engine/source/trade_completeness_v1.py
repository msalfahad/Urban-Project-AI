"""TRADE COMPLETENESS V1 (T-236; owner 2026-10-23 19:00 trade completeness rules 1-6, acceptance 19:45): for every
principal trade, which physical elements an INDEPENDENT inventory finds, and for each one whether a BOQ line measures
it, holds it with a named reason, verifies it, misses it or carries it twice. A pure CHECK module: it reads plain data,
writes nothing, moves no quantity and is wired into no method (ARCH_TAKEOFF_V2.9 and V3.0.x are unchanged).

    check(inventories=(), register=(), lines=(), line_links=None, verdicts=(), exclusions=(), opening_census=None,
          levels=(), accuracy=(), level_tol_m=0.0005, net_tol=0.001)      -> report dict (deterministic)
    reconcile_line(line, opening_census=None, net_tol=0.001)             -> the line, or CompletenessError
    reference_line_rows(report)                                          -> one row per trade for T-235 part (3)
    line_trade(line)                                                     -> the principal trade id of a BOQ line
    element_key(floor, label)                                            -> "<floor>:<label>"

Why (ADVERSARIAL_PROBE_2026-10-23.md, probes 1b, 2, 3, 6, 9): the scope crosswalk (T-196) takes its elements from the
engine's own element register, so an element the engine never detects is absent from BOTH the BOQ and the crosswalk; two
engine lines on one element were not flagged; an opening deducted twice was accepted; a whole trade with no line showed
only as NOT_MAPPED; nothing compared one storey's level across sheets. Here the expected population of a trade comes
from inventories built WITHOUT the engine (printed schedules, plan tags, block inserts, censuses read from the drawing),
and the register / BOQ are joined to it, never the other way round.

Inputs (plain data; no drawing is read here)
  inventories  [{"source": id, "basis": INVENTORY_BASES, "trade": principal trade id, "floors": [..] (optional: the
               storeys the source covers; default every storey of its elements), "elements": [{"floor", "label",
               "ref" (handle / printed value / sheet), "tagged": bool (default True)}]}]. An element with tagged False
               is drawn geometry with no printed mark: it is FOUND, but nothing can join it to a line by label, so
               it is INVENTORY_GEOMETRY_ONLY (residual risk named) unless a line links its key explicitly.
               basis ENGINE_* is refused: an inventory derived from the engine's own output is not independent.
  register     [{"trade", "floor", "label", "status" (optional: HELD / NOT_APPLICABLE / ...), "reason"}]: the engine's
               element register projected to trade keys. Used for HELD reasons and REGISTER_ONLY, never as the
               population.
  lines        canonical BOQ lines (engine/source/boq_line.py schema).
  line_links   line_id -> [key or {"key", "component"}]: the element(s) a line measures. A line with no link is
               UNLINKED (listed per trade with its line id; it can neither find nor duplicate an element).
  verdicts     [{"trade", "key", "verdict": "COUNTED", "ref"}]: the Checker's own re-measure (VERIFIED only from here).
  exclusions   [{"trade", "key", "rule_id", "basis"}]: an element an owner rule takes out of a trade: EXCLUDED with the
               rule id, never MISSING, never silently removed (rule_id required).
  opening_census  ids of the openings an independent opening census found (optional): a deduction naming another id
               is refused (OPENING_NOT_IN_CENSUS).
  levels       [{"sheet", "storey", "datum" (FFL / SSL / TOS / ...), "level_m", "ref"}]: one storey and datum printed
               with different values on two sheets is a CONFLICT row (never a pick). Different datums (a finished floor
               level and a structural top) are different physical surfaces and are never compared with each other.
  accuracy     [{"trade", "unit", "row", "engine" (number or None), "reference" (number)}]: reference comparison rows
               (the freelancer). Reported ONLY in the accuracy table, WAPE with 'compared n / d' beside it.

Element statuses (one per trade element; precedence top to bottom)
  EXCLUDED                an exclusion with its rule id, or every line on it EXCLUDED_WITH_REASON / NOT_APPLICABLE
  VERIFIED                a quantity line + a COUNTED verdict (also counted in MEASURED)
  MEASURED                at least one line in a quantity state (MEASURED / SOURCE_DERIVED / PROVISIONAL)
  HELD                    a held line (BOUNDED_EXPOSURE, BLOCKED_RFI with its question) or a register HELD with a reason
  UNRESOLVED              a line / register entry says held but names no reason
  INVENTORY_GEOMETRY_ONLY drawn, untagged, no line links it (residual risk: it may be carried unjoined or omitted)
  CONFLICT                no line, and the inventories that cover its storey disagree on whether it exists
  MISSING                 an inventory element with no line and no hold
  REGISTER_ONLY           in the register or on a line, inside an inventory's storeys, but in no inventory (not in d;
                          decided before the line states: a measured element no inventory finds is a disagreement)
  OUT_OF_INVENTORY_SCOPE  in the register or on a line on a storey no inventory of the trade covers (not in d)
  Each element row also carries "measurement" (EXCLUDED / VERIFIED / MEASURED / HELD / UNRESOLVED / NONE): what its
  lines and register entry say, kept beside the inventory status.
  Flags beside the status: duplicated (two additive lines of one trade on the same element, component and unit;
  a never-additive measure pair is not a duplicate; the same label on two storeys is two keys, never a duplicate),
  inventory_agreement AGREED / SINGLE_SOURCE / CONFLICT (with the sources).

Trade rows: one for EVERY principal trade (PRINCIPAL_TRADES), plus any other trade a line carries; a principal trade
with no line is NOT_MEASURED (never absent); a trade with no independent inventory says NO_INDEPENDENT_INVENTORY and its
completeness is "n/a" (d = 0), never 100 %.

    completeness % = (measured + held) / d      verified % = verified / d
    d = the independent inventory count of the trade (FOUND, excluded elements taken out and listed)

Each in its own table with n / d; accuracy only in its own table; no combined percentage is ever written.

Deductions (every line that states a gross): gross - sum(deductions) + sum(additions) = measured_net within net_tol
(an amount is 'area' or the line's unit key, e.g. {"m2": .., "what": ..}; a deduction names its opening id or says
'what' it is, else DEDUCTION_UNNAMED); each opening id at most once per face (in one line, and across the lines of one trade on the same element and face);
every opening id in the opening census when one is given. A breach is REFUSED with the reasons; reconcile_line raises.

Nothing here names a project, a sheet, a layer or a coordinate; stdlib only.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict

SCHEMA = "URBAN_TRADE_COMPLETENESS_V1"
POLICY_ID = "TRADE_COMPLETENESS_V1"
DEFAULT_GUARD_CLASS = "CHECK_ONLY"     # T-212 property P1: a check module; writes no BOQ quantity

QUANTITY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")      # engine/source/boq_line.py QUANTITY_STATES
HELD_STATES = ("BOUNDED_EXPOSURE", "BLOCKED_RFI")
EXCLUDED_STATES = ("EXCLUDED_WITH_REASON", "NOT_APPLICABLE_WITH_EVIDENCE")
INVENTORY_BASES = ("PRINTED_SCHEDULE", "TEXT_TAG", "BLOCK_INSERT", "CENSUS", "UNTAGGED_GEOMETRY", "HAND_COUNT")
ELEMENT_STATUSES = ("EXCLUDED", "VERIFIED", "MEASURED", "HELD", "UNRESOLVED", "INVENTORY_GEOMETRY_ONLY", "CONFLICT",
                    "MISSING", "REGISTER_ONLY", "OUT_OF_INVENTORY_SCOPE")
IN_D = ("VERIFIED", "MEASURED", "HELD", "UNRESOLVED", "INVENTORY_GEOMETRY_ONLY", "CONFLICT", "MISSING")
GEOMETRY_RISK = ("drawn without a printed mark: no label joins it to a line, so a line may carry it unjoined or it may "
                 "be omitted; a person must bind it or the inventory must tag it")

# principal trades (owner 19:00 rule 1): concrete by member family, masonry by thickness, finishes, openings, stairs,
# railings, formwork, reinforcement. Every one gets a row in every report.
CONCRETE_FAMILIES = ("BLINDING", "FOOTING", "NECK", "STRAP", "GROUND_BEAM", "GROUND_SLAB", "COLUMN", "BEAM", "SLAB",
                     "LINTEL", "STAIR", "DOME", "POOL", "TANK", "LIFT", "BOUNDARY_WALL", "PARAPET", "OTHER")
PRINCIPAL_TRADES = tuple(f"CONCRETE.{f}" for f in CONCRETE_FAMILIES) + (
    "MASONRY.100", "MASONRY.150", "MASONRY.200", "PLASTER", "PAINT", "FLOOR_FINISH", "WALL_FINISH", "CEILING",
    "WATERPROOFING", "DOORS", "WINDOWS", "STAIRS", "RAILINGS", "FORMWORK", "REBAR")
PRINCIPAL_SET = frozenset(PRINCIPAL_TRADES)
MASONRY_THICKNESS = {"100": "MASONRY.100", "150": "MASONRY.150", "200": "MASONRY.200",
                     "0.10": "MASONRY.100", "0.15": "MASONRY.150", "0.20": "MASONRY.200",
                     "10": "MASONRY.100", "15": "MASONRY.150", "20": "MASONRY.200"}
# boq_line trade -> principal trade, where the item code does not decide it
TRADE_MAP = {"PLASTER": "PLASTER", "PAINT": "PAINT", "FLOOR_FINISH": "FLOOR_FINISH", "WALL_FINISH": "WALL_FINISH",
             "CEILING": "CEILING", "WATERPROOFING": "WATERPROOFING", "STAIR_FINISH": "STAIRS", "RAILING": "RAILINGS",
             "FORMWORK": "FORMWORK", "REINFORCEMENT": "REBAR"}


class CompletenessError(ValueError):
    """an input the check refuses (an engine-derived inventory, an exclusion without its rule, a refused line)."""


def element_key(floor, label):
    return f"{floor}:{label}"


_T_RE = re.compile(r"\bt\s*=\s*(\d+(?:\.\d+)?)")


def _thickness(line):
    pe = _T_RE.search(str(line.get("physical_element") or ""))
    for v in ((pe.group(1) if pe else None), line.get("subtrade"), (line.get("calculation") or {}).get("inputs", {}).get("thickness_mm"),
              (line.get("calculation") or {}).get("inputs", {}).get("thickness")):
        if v is None:
            continue
        s = str(v).strip().upper().replace("MM", "").replace("MASONRY.", "")
        if s in MASONRY_THICKNESS:
            return MASONRY_THICKNESS[s]
        try:
            f = float(s)
        except ValueError:
            continue
        for k in (f"{f:g}", f"{f:.2f}"):
            if k in MASONRY_THICKNESS:
                return MASONRY_THICKNESS[k]
    return None


def line_trade(line):
    """the principal trade id of a canonical line; a masonry line takes its thickness from its physical element
    ('walls t=0.15'), its subtrade or its inputs, and with none stated is MASONRY.UNSTATED (reported, never put in a
    thickness it does not state); any other unmapped line keeps 'OTHER:<boq trade>'."""
    code = line.get("item_code") or ""
    if code.startswith("STR.CONC."):
        fam = code[len("STR.CONC."):]
        return f"CONCRETE.{fam}" if fam in CONCRETE_FAMILIES else "CONCRETE.OTHER"
    if code.startswith("STR.REBAR"):
        return "REBAR"
    if code in ("MAS.BLOCK", "ARCH.WALL_RUN") or line.get("trade") == "MASONRY":
        return _thickness(line) or "MASONRY.UNSTATED"
    if code in ("ARCH.DOOR",) or code.startswith("DOOR."):
        return "DOORS"
    if code == "ARCH.WINDOW":
        return "WINDOWS"
    if code.startswith("FIN.MARBLE.TREAD") or code.startswith("FIN.MARBLE.RISER") or \
            code.startswith("FIN.MARBLE.LANDING") or code.startswith("FIN.STAIR."):
        return "STAIRS"
    if code in ("FIN.RAILING", "FIN.HANDRAIL"):
        return "RAILINGS"
    if code.startswith("FIN.WP."):
        return "WATERPROOFING"
    tr = line.get("trade")
    return TRADE_MAP.get(tr, f"OTHER:{tr}")


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _r(x, n=6):
    return None if x is None else round(float(x), n)


def _pct(n, d):
    return None if not d else round(100.0 * n / d, 2)


# ------------------------------------------------------------------------------------------------ deductions
def _amount(item, unit):
    """a deduction / addition amount: 'area' (synthetic and ledger form) or the line's own unit key ('m2', 'lm', 'm3',
    the canonical-line form {"m2": .., "what": ..}); None when neither is a number."""
    for k in ("area", unit, "qty"):
        if _num(item.get(k)):
            return item[k]
    return None


def _deduction_problems(line, opening_census, net_tol):
    probs = []
    seen = set()
    total_d = 0.0
    unit = line.get("unit")
    for d in line.get("deductions") or []:
        oid = d.get("opening")
        face = d.get("face")
        if oid is None:
            if not d.get("what"):
                probs.append("DEDUCTION_UNNAMED")
        else:
            if (oid, face) in seen:
                probs.append(f"DEDUCTION_REPEATED:{oid}" + (f"@{face}" if face is not None else ""))
            seen.add((oid, face))
            if opening_census is not None and oid not in opening_census:
                probs.append(f"OPENING_NOT_IN_CENSUS:{oid}")
        a = _amount(d, unit)
        if a is None:
            probs.append(f"DEDUCTION_UNQUANTIFIED:{oid if oid is not None else d.get('what')}")
        else:
            total_d += a
    total_a = sum(x for x in (_amount(a, unit) for a in line.get("additions") or []) if x is not None)
    gross, net = line.get("gross"), line.get("measured_net")
    if _num(gross) and _num(net) and not any(p.startswith("DEDUCTION_UNQUANTIFIED") for p in probs):
        if abs(gross - total_d + total_a - net) > net_tol:
            probs.append(f"NET_MISMATCH:gross {gross:g} - deductions {total_d:g} + additions {total_a:g} != net {net:g}")
    return sorted(set(probs), key=probs.index), total_d, total_a


def reconcile_line(line, opening_census=None, net_tol=0.001):
    """the line when its gross, deductions and net reconcile and no opening repeats; else CompletenessError."""
    oc = None if opening_census is None else set(opening_census)
    probs, _d, _a = _deduction_problems(line, oc, net_tol)
    if probs:
        raise CompletenessError(f"{line.get('line_id')}: {'; '.join(probs)}")
    return line


# ------------------------------------------------------------------------------------------------ the check
def _links_of(line_links, lid):
    out = []
    for x in (line_links or {}).get(lid) or []:
        if isinstance(x, dict):
            out.append((x["key"], x.get("component")))
        else:
            out.append((x, None))
    return out


def _held_reason(line):
    if line["evidence_state"] == "BLOCKED_RFI":
        return (line.get("rfi") or {}).get("question")
    if line["evidence_state"] == "BOUNDED_EXPOSURE":
        br = line.get("bounded_range") or {}
        why = line.get("notes") or (line.get("rfi") or {}).get("question")
        return why or (f"bounded {br.get('low')} .. {br.get('high')}" if br.get("low") is not None else None)
    return None


def check(inventories=(), register=(), lines=(), line_links=None, verdicts=(), exclusions=(), opening_census=None,
          levels=(), accuracy=(), level_tol_m=0.0005, net_tol=0.001):
    oc = None if opening_census is None else set(opening_census)
    findings = []

    # ---- inventories: per trade, key -> sources; floors covered per source
    inv = defaultdict(lambda: defaultdict(dict))        # trade -> key -> source -> element
    cover = defaultdict(dict)                            # trade -> source -> set(floors)
    basis_of = {}
    for src in inventories:
        b = src.get("basis")
        if b not in INVENTORY_BASES:
            raise CompletenessError(f"inventory {src.get('source')}: basis {b!r} is not an independent inventory basis "
                                    f"{INVENTORY_BASES} (an inventory read from the engine's own output is refused)")
        tr, sid = src["trade"], src["source"]
        if sid in cover[tr]:
            raise CompletenessError(f"inventory {sid} given twice for {tr}")
        basis_of[(tr, sid)] = b
        fl = set(src.get("floors") or [e["floor"] for e in src.get("elements") or []])
        cover[tr][sid] = fl
        for e in src.get("elements") or []:
            k = element_key(e["floor"], e["label"])
            if k in inv[tr] and sid in inv[tr][k]:
                findings.append({"finding": "INVENTORY_REPEAT", "trade": tr, "key": k, "source": sid,
                                 "note": "one source lists the same storey and label twice: an unlabelled second "
                                         "element needs its own label (e.g. .1 / .2 by position)"})
            inv[tr][k][sid] = {"ref": e.get("ref"), "tagged": e.get("tagged", True), "floor": e["floor"]}

    # ---- exclusions
    excl = {}
    for x in exclusions:
        if not x.get("rule_id"):
            raise CompletenessError(f"exclusion {x.get('trade')} {x.get('key')}: an exclusion names its owner rule")
        excl[(x["trade"], x["key"])] = x

    # ---- register
    reg = defaultdict(dict)
    for r in register:
        k = r.get("key") or element_key(r["floor"], r["label"])
        reg[r["trade"]][k] = r

    # ---- lines, grouped per trade and key
    on_key = defaultdict(lambda: defaultdict(list))     # trade -> key -> [(line, component)]
    unlinked = defaultdict(list)
    line_rows = []
    trade_lines = defaultdict(int)
    by_id = {}
    for ln in lines:
        lid = ln["line_id"]
        if lid in by_id and json.dumps(by_id[lid], sort_keys=True) != json.dumps(ln, sort_keys=True):
            raise CompletenessError(f"two different lines carry line id {lid}: one would hide the other")
        by_id[lid] = ln
    for lid in sorted(by_id):
        ln = by_id[lid]
        tr = line_trade(ln)
        trade_lines[tr] += 1
        lk = _links_of(line_links, lid)
        if not lk:
            unlinked[tr].append(lid)
        for k, comp in lk:
            on_key[tr][k].append((ln, comp))
        # deductions
        if ln.get("deductions") or ln.get("gross") is not None:
            probs, td, ta = _deduction_problems(ln, oc, net_tol)
            line_rows.append({"line_id": lid, "trade": tr, "item_code": ln.get("item_code"), "unit": ln.get("unit"),
                              "keys": sorted(k for k, _c in lk), "gross": _r(ln.get("gross")),
                              "deductions": _r(td), "additions": _r(ta), "net": _r(ln.get("measured_net")),
                              "openings": sorted({str(d.get("opening")) for d in ln.get("deductions") or []}),
                              "status": "REFUSED" if probs else ("RECONCILED" if _num(ln.get("gross")) and
                                                                 _num(ln.get("measured_net")) else "NOT_CHECKABLE"),
                              "problems": probs})
    # the same opening deducted on two lines of one trade, same element and face
    seen_open = defaultdict(list)
    for tr in on_key:
        for k, items in on_key[tr].items():
            for ln, comp in items:
                for d in ln.get("deductions") or []:
                    if d.get("opening") is not None:
                        seen_open[(tr, k, d.get("face", comp), d["opening"])].append(ln["line_id"])
    cross = {}
    for (tr, k, face, oid), lids in seen_open.items():
        if len(set(lids)) > 1:
            for lid in set(lids):
                cross.setdefault(lid, []).append(f"DEDUCTION_REPEATED_ACROSS_LINES:{oid}" +
                                                 (f"@{face}" if face is not None else ""))
    for row in line_rows:
        if row["line_id"] in cross:
            row["problems"] = sorted(set(row["problems"] + cross[row["line_id"]]))
            row["status"] = "REFUSED"
    line_rows.sort(key=lambda r: (r["trade"], r["line_id"]))

    ver = {(v["trade"], v["key"]): v for v in verdicts if v.get("verdict") == "COUNTED"}

    # ---- elements
    trades = sorted(set(PRINCIPAL_TRADES) | set(trade_lines) | set(inv) | set(reg),
                    key=lambda t: (PRINCIPAL_TRADES.index(t) if t in PRINCIPAL_SET else len(PRINCIPAL_TRADES), t))
    elements = []
    for tr in trades:
        covered = set().union(*cover[tr].values()) if cover[tr] else set()
        keys = set(inv[tr]) | set(reg[tr]) | set(on_key[tr]) | {k for (t, k) in excl if t == tr}
        for k in sorted(keys):
            floor = k.split(":", 1)[0]
            srcs = inv[tr].get(k, {})
            covering = sorted(s for s, fl in cover[tr].items() if floor in fl)
            if not srcs:
                agree = "NONE"
            elif len(covering) <= 1:
                agree = "SINGLE_SOURCE"
            elif all(s in srcs for s in covering):
                agree = "AGREED"
            else:
                agree = "CONFLICT"
            items = on_key[tr].get(k, [])
            qty = [ln for ln, _c in items if ln["evidence_state"] in QUANTITY_STATES]
            held = [ln for ln, _c in items if ln["evidence_state"] in HELD_STATES]
            exl = [ln for ln, _c in items if ln["evidence_state"] in EXCLUDED_STATES]
            # duplicates: two additive lines on the same component and unit
            groups = defaultdict(list)
            for ln, comp in items:
                if ln["evidence_state"] in EXCLUDED_STATES:
                    continue
                groups[(comp, ln["unit"])].append(ln)
            dup_lines = []
            for (_comp, _u), lns in groups.items():
                ids = {x["line_id"] for x in lns}
                additive = [x for x in lns if not (set(x.get("never_additive_with") or ()) & (ids - {x["line_id"]}))]
                if len(lns) > 1 and len(additive) > 1:
                    dup_lines.extend(sorted(ids))
            r = reg[tr].get(k)
            reason = None
            # what the lines / register say about the element (independent of whether an inventory found it)
            if (tr, k) in excl:
                meas, reason = "EXCLUDED", f"{excl[(tr, k)]['rule_id']}: {excl[(tr, k)].get('basis', '')}".strip()
            elif exl and not qty and not held:
                meas, reason = "EXCLUDED", "; ".join(sorted({x.get("notes") or "" for x in exl}))
            elif qty:
                meas = "VERIFIED" if (tr, k) in ver else "MEASURED"
            elif held or (r and str(r.get("status", "")).upper() == "HELD"):
                why = [w for w in (_held_reason(x) for x in held) if w] + ([r["reason"]] if r and r.get("reason") else [])
                meas, reason = ("HELD", "; ".join(sorted(set(why)))) if why else ("UNRESOLVED", "held without a "
                                                                                  "named reason")
            else:
                meas = "NONE"
            # the element status: an element no independent inventory found is REGISTER_ONLY / OUT_OF_INVENTORY_SCOPE
            # whatever its lines say (an inventory / register disagreement to resolve, never counted in d)
            if meas == "EXCLUDED":
                status = "EXCLUDED"
            elif not srcs:
                if covered and floor in covered:
                    status, reason = "REGISTER_ONLY", ("in the register or on a line, in no independent inventory of "
                                                       "the trade (a misread, an untagged element or an inventory gap)")
                else:
                    status, reason = "OUT_OF_INVENTORY_SCOPE", ("no independent inventory of this trade covers "
                                                                f"storey {floor}")
            elif meas != "NONE":
                status = meas
            elif not any(v["tagged"] for v in srcs.values()):
                status, reason = "INVENTORY_GEOMETRY_ONLY", GEOMETRY_RISK
            elif agree == "CONFLICT":
                status = "CONFLICT"
                reason = (f"found by {sorted(srcs)}, not by {sorted(set(covering) - set(srcs))}: the inventories "
                          "disagree; neither is picked")
            else:
                status = "MISSING"
            elements.append({"trade": tr, "key": k, "status": status, "measurement": meas, "reason": reason,
                             "duplicated": bool(dup_lines), "duplicate_lines": dup_lines,
                             "inventory_agreement": agree, "sources": sorted(srcs),
                             "refs": sorted({str(v["ref"]) for v in srcs.values() if v.get("ref") is not None}),
                             "lines": sorted({ln["line_id"] for ln, _c in items})})

    # ---- trade rows and the separate tables
    per = defaultdict(lambda: defaultdict(int))
    for e in elements:
        per[e["trade"]][e["status"]] += 1
        if e["duplicated"]:
            per[e["trade"]]["DUPLICATED"] += 1
        if e["inventory_agreement"] == "CONFLICT":
            per[e["trade"]]["AGREEMENT_CONFLICT"] += 1
    trade_rows, comp_t, ver_t = [], [], []
    for tr in trades:
        c = per[tr]
        # d: the inventory elements of the trade (FOUND), excluded elements taken out (listed apart)
        d = sum(1 for e in elements if e["trade"] == tr and e["sources"] and e["status"] != "EXCLUDED")
        meas = sum(1 for e in elements if e["trade"] == tr and e["sources"] and e["status"] in ("MEASURED", "VERIFIED"))
        held_n = sum(1 for e in elements if e["trade"] == tr and e["sources"] and e["status"] == "HELD")
        verified = sum(1 for e in elements if e["trade"] == tr and e["sources"] and e["status"] == "VERIFIED")
        if trade_lines[tr] == 0 and not any(e["trade"] == tr and e["status"] == "HELD" for e in elements):
            status = "NOT_MEASURED"
        elif not inv[tr]:
            status = "NO_INDEPENDENT_INVENTORY"
        elif c["MISSING"] or c["CONFLICT"] or c["UNRESOLVED"] or c["INVENTORY_GEOMETRY_ONLY"] or c["DUPLICATED"] or \
                c["REGISTER_ONLY"]:
            status = "GAPS"
        else:
            status = "COMPLETE_AGAINST_INVENTORY"
        sources = sorted(f"{s} ({basis_of[(tr, s)]})" for s in cover[tr])
        trade_rows.append({"trade": tr, "principal": tr in PRINCIPAL_SET, "status": status, "lines": trade_lines[tr],
                           "unlinked_lines": len(unlinked[tr]), "inventory_sources": sources,
                           "found": d, "measured": meas, "held": held_n, "verified": verified,
                           "missing": c["MISSING"], "duplicated": c["DUPLICATED"], "unresolved": c["UNRESOLVED"],
                           "geometry_only": c["INVENTORY_GEOMETRY_ONLY"], "conflict": c["CONFLICT"],
                           "agreement_conflict": c["AGREEMENT_CONFLICT"], "excluded": c["EXCLUDED"],
                           "register_only": c["REGISTER_ONLY"], "out_of_inventory_scope": c["OUT_OF_INVENTORY_SCOPE"]})
        comp_t.append({"trade": tr, "n": meas + held_n, "d": d, "pct": _pct(meas + held_n, d) if d else "n/a"})
        ver_t.append({"trade": tr, "n": verified, "d": d, "pct": _pct(verified, d) if d else "n/a"})

    # ---- storey datum agreement
    lv = defaultdict(list)
    for x in levels:
        if not _num(x.get("level_m")):
            raise CompletenessError(f"level on {x.get('sheet')}: a printed level is a number in metres")
        lv[(x["storey"], x.get("datum") or "UNSTATED")].append(x)
    level_rows = []
    for (st, dt) in sorted(lv):
        xs = sorted(lv[(st, dt)], key=lambda x: (x["level_m"], str(x["sheet"])))
        vals = sorted({round(x["level_m"], 4) for x in xs})
        spread = xs[-1]["level_m"] - xs[0]["level_m"]
        level_rows.append({"storey": st, "datum": dt, "status": "CONFLICT" if spread > level_tol_m else
                           ("AGREED" if len(xs) > 1 else "SINGLE_SHEET"), "values_m": vals,
                           "sheets": [f"{x['sheet']}={x['level_m']:g}" for x in xs]})

    # ---- accuracy, apart
    acc = defaultdict(lambda: {"num": 0.0, "den": 0.0, "n": 0, "d": 0, "unit": set()})
    for a in accuracy:
        t = acc[(a["trade"], a["unit"])]
        t["d"] += 1
        if _num(a.get("engine")) and _num(a.get("reference")):
            t["n"] += 1
            t["num"] += abs(a["engine"] - a["reference"])
            t["den"] += abs(a["reference"])
    acc_t = [{"trade": tr, "unit": u, "compared": f"{v['n']} / {v['d']}",
              "wape_pct": round(100 * v["num"] / v["den"], 2) if v["den"] else "n/a"}
             for (tr, u), v in sorted(acc.items())]

    return {"schema": SCHEMA, "policy_id": POLICY_ID,
            "definitions": {"completeness": "(measured + held) / d, d = independent inventory count (excluded out)",
                            "verified": "verified / d", "accuracy": "WAPE vs the reference rows, compared n / d; "
                            "never combined with completeness or verified"},
            "trades": trade_rows, "completeness_table": comp_t, "verified_table": ver_t, "accuracy_table": acc_t,
            "elements": elements, "deductions": line_rows, "levels": level_rows,
            "unlinked_lines": {t: sorted(v) for t, v in sorted(unlinked.items())},
            "findings": sorted(findings, key=lambda f: json.dumps(f, sort_keys=True))}


def reference_line_rows(report):
    """per trade, the form T-235 part (3) reads: element scope, independent inventory count, MISSING, DUPLICATED,
    HELD (each with its keys), inventory sources, completeness and verified n / d (never one figure)."""
    by = defaultdict(lambda: defaultdict(list))
    for e in report["elements"]:
        by[e["trade"]][e["status"]].append(e["key"])
        if e["duplicated"]:
            by[e["trade"]]["DUPLICATED"].append(e["key"])
    comp = {r["trade"]: r for r in report["completeness_table"]}
    ver = {r["trade"]: r for r in report["verified_table"]}
    out = []
    for t in report["trades"]:
        tr = t["trade"]
        out.append({"element_scope": tr, "status": t["status"], "inventory_count": t["found"],
                    "missing": sorted(by[tr]["MISSING"]), "duplicated": sorted(by[tr]["DUPLICATED"]),
                    "held": sorted(by[tr]["HELD"]), "conflict": sorted(by[tr]["CONFLICT"]),
                    "geometry_only": sorted(by[tr]["INVENTORY_GEOMETRY_ONLY"]),
                    "inventory_sources": t["inventory_sources"],
                    "completeness": f"{comp[tr]['n']} / {comp[tr]['d']}",
                    "verified": f"{ver[tr]['n']} / {ver[tr]['d']}"})
    return out


def dumps(report):
    """canonical bytes of a report (sorted keys; every list is already in canonical order)."""
    return json.dumps(report, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def policy_record():
    return {"policy_id": POLICY_ID, "schema": SCHEMA, "default_guard_class": DEFAULT_GUARD_CLASS,
            "principal_trades": list(PRINCIPAL_TRADES), "inventory_bases": list(INVENTORY_BASES),
            "element_statuses": list(ELEMENT_STATUSES)}


__all__ = ["SCHEMA", "POLICY_ID", "DEFAULT_GUARD_CLASS", "PRINCIPAL_TRADES", "INVENTORY_BASES", "ELEMENT_STATUSES",
           "CompletenessError", "element_key", "line_trade", "reconcile_line", "check", "reference_line_rows", "dumps",
           "policy_record"]
