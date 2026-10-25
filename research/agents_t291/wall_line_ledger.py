"""R-T291-1: the BLOCKWORK WALL-TO-LINE LEDGER (research rule, any villa; T-291). Pure Python, no drawing access.

Provenance: register v4 (T-288, MERGED 643b310b: R-T288-1 drop term, R-T285-1 revision rules, R-T274-1 piece closure),
the opening host ledgers (T-175 / T-227 / T-261 / T-274, merged), WORKFLOW_CONTROLS s.5 (evidence statuses) and
ENGINEERING_REASONING_STANDARD s.2.4 (reconcile to named causes, never to a plug). Nothing here edits an engine module,
a rule or knowledge file, a candidate line or a released line: lane I (T-279) applies the ledger.

PHYSICAL ELEMENT. A block wall is the masonry between its faces, from its floor to the underside of the member over it,
less the openings built into it. The register measures it wall by wall; the candidate's masonry lines measure the same
masonry as one aggregate per storey and thickness family (no wall key). This ledger states, for every register wall,
which candidate line id carries its masonry, with which status and how much, so the integration is mechanical.

Rules (each refusal code is the first word of the error):
1. BINDING. A wall binds to the candidate line(s) of its storey and thickness family for each masonry item code
   (area items m2, volume items m3). A wall may bind to several lines (its share in each is stated and the shares sum
   to the wall); a line may hold several walls. A wall that binds to no line is LISTED (UNMATCHED_WALL), never
   dropped; a line that holds no wall is LISTED (UNMATCHED_LINE) with its reason.
2. STATUS. Every ledger row carries one status: VERIFIED (with the Checker run, else refused NO_CHECKER_RUN),
   DRAWING-CONFIRMED, ASSUMED - OWNER-APPROVED (with its source), HELD ON DROP (U - L x d: U and L carried, the term
   never evaluated: d = 0 is refused, DROP_EVALUATED), HELD (blank quantity with the named item; a 0 or a figure in
   the quantity column is refused, HELD_AS_ZERO), ESTABLISHED PART + HELD (the established part with its class and the
   held piece named, blank). A width CONFLICT increment is carried by name OUTSIDE every total.
3. CLOSURE. For every item code and status the register total equals the sum of the ledger rows to 0.0000 m2 (m3);
   the U and L of the drop term close separately. A wall twice in one item code (beyond its declared shares) is
   refused (WALL_TWICE).
4. OPENINGS. Each opening deduction is listed once by its opening id with its host wall and its source; a second
   deduction of the same opening id is refused (OPENING_TWICE). The deductions of a wall's established part sum to
   its register deduction (OPENING_SUM). An opening whose host builds no masonry is NOT_APPLICABLE (build before
   deduct, ERS s.3), an opening in a held piece or a held wall is listed with that hold, never deducted as 0.
5. ENGINE VS REGISTER. Per line: engine quantity minus the ledger's carried quantities, split into named parts only:
   (a) walls the register holds (counted by the engine, blank here); (b) the drop term L x d (the engine books the
   normal soffit); (c) opening deductions by opening id (engine w x h_in vs register); (d) the rest, named as the
   storey-panel basis (one panel height and the wall-mass run versus the register's piece heights and census lengths).
   Nothing is plugged: (d) is the arithmetic remainder and is reported as such, with its sign.
"""
from __future__ import annotations

RULE_ID = "R-T291-1"
TOL = 0.00005           # closure tolerance (the register is stated to 0.0001 m2)

VERIFIED = "VERIFIED"
DC = "DRAWING-CONFIRMED"
AOA = "ASSUMED — OWNER-APPROVED"
HELD_ON_DROP = "HELD ON DROP"
HELD = "HELD"
PART_PLUS_HELD = "ESTABLISHED PART + HELD"
STATUSES = (VERIFIED, DC, AOA, HELD_ON_DROP, HELD, PART_PLUS_HELD)
DETERMINATE = (VERIFIED, DC, AOA)

# register v4 class -> evidence status (WORKFLOW_CONTROLS s.5; T-288 s.3: PROJECT-SPECIFIC = the owner-approved class)
CLASS_TO_STATUS = {"VERIFIED": VERIFIED, "SOURCE-SUPPORTED PENDING INDEPENDENT CHECK": DC,
                   "PROJECT-SPECIFIC": AOA}


class LedgerError(ValueError):
    """a ledger row, binding or total the rule refuses (the code is the first word of the message)."""


def family_key(t_m):
    """the thickness family key the candidate uses ('0.2', '0.15', '0.4')."""
    t = float(t_m)
    if not 0.05 <= t <= 1.0:
        raise LedgerError(f"BAD_UNITS: wall thickness {t_m!r} is not metres")
    return f"{t:g}"


def wall_status(w):
    """rule 2: the ledger status of a register wall (dict with state, class, verified_by, completeness, ...)."""
    state = w.get("state") or ""
    if state == HELD_ON_DROP:
        return HELD_ON_DROP
    if state == "HELD" or (w.get("class") == "HELD" and state != "ESTABLISHED_PART_PLUS_HELD"):
        return HELD
    if state == "ESTABLISHED_PART_PLUS_HELD":
        return PART_PLUS_HELD
    st = CLASS_TO_STATUS.get(w.get("class"))
    if st is None:
        raise LedgerError(f"UNKNOWN_CLASS: {w.get('wall_id')} class {w.get('class')!r}")
    if st == VERIFIED and not w.get("verified_by"):
        raise LedgerError(f"NO_CHECKER_RUN: {w.get('wall_id')} is VERIFIED without the Checker run that verified it")
    return st


def check_row(r):
    """rule 2: refuse a ledger row whose quantity contradicts its status."""
    st, wid = r["status"], r["wall_id"]
    if st not in STATUSES:
        raise LedgerError(f"UNKNOWN_STATUS: {wid} {st!r}")
    q = r.get("carried")
    if st in DETERMINATE:
        if q is None or q <= 0:
            raise LedgerError(f"NON_POSITIVE: {wid} {st} carries {q!r}")
        if st == VERIFIED and not r.get("verified_by"):
            raise LedgerError(f"NO_CHECKER_RUN: {wid} VERIFIED without its Checker run")
    elif st == HELD_ON_DROP:
        if q is not None:
            raise LedgerError(f"DROP_EVALUATED: {wid} carries {q!r}; a wall under a sunken panel carries U - L x d only")
        if not r.get("upper") or r["upper"] <= 0 or not r.get("drop_length_m") or r["drop_length_m"] <= 0:
            raise LedgerError(f"HELD_AS_ZERO: {wid} keeps U > 0 and L > 0 (the d = 0 bound is not a quantity)")
    elif st == HELD:
        if q is not None:
            raise LedgerError(f"HELD_AS_ZERO: {wid} is HELD; its quantity is blank with the named item, never {q!r}")
        if not r.get("held_item"):
            raise LedgerError(f"HELD_UNNAMED: {wid} is HELD without its named item")
    elif st == PART_PLUS_HELD:
        if q is None or q <= 0 or not r.get("held_item") or r.get("part_status") not in DETERMINATE:
            raise LedgerError(f"PART_UNNAMED: {wid} carries its established part (with its class) and names the held piece")
    if r.get("conflict_increment") not in (None, 0) and r.get("conflict_in_total"):
        raise LedgerError(f"CONFLICT_IN_TOTAL: {wid} width-conflict increment stays outside every total")
    return True


def evaluate_drop(expression_row, d):
    """the drop term is never evaluated in this ledger (rule 2)."""
    raise LedgerError(f"DROP_EVALUATED: {expression_row.get('wall_id')} U - L x d with d = {d!r}; d is HELD (not printed)")


def bind(walls, lines, shares=None):
    """rule 1. walls: [{wall_id, floor, t_m, ...}]; lines: [{line_id, item_code, floor, family, unit, ...}] (masonry
    lines only); shares: {(wall_id, item_code): {line_id: fraction}} for a wall split over several lines of one item.
    -> {(wall_id, item_code): [(line_id, fraction)]}, unmatched_walls [(wall_id, item_code, reason)],
       unmatched_lines [(line_id, reason)]"""
    shares = shares or {}
    items = sorted({ln["item_code"] for ln in lines})
    by_key = {}
    for ln in lines:
        by_key.setdefault((ln["item_code"], ln["floor"], ln.get("family")), []).append(ln)
    out, unmatched_w, used = {}, [], set()
    seen = set()
    for w in walls:
        if w["wall_id"] in seen:
            raise LedgerError(f"WALL_TWICE: {w['wall_id']} appears twice in the register")
        seen.add(w["wall_id"])
        fam = family_key(w["t_m"])
        for it in items:
            sh = shares.get((w["wall_id"], it))
            if sh:
                if abs(sum(sh.values()) - 1.0) > 1e-9:
                    raise LedgerError(f"SHARES_NOT_CLOSED: {w['wall_id']} {it} shares sum {sum(sh.values())}")
                ids = {ln["line_id"] for ln in lines if ln["item_code"] == it}
                for lid in sh:
                    if lid not in ids:
                        raise LedgerError(f"NO_SUCH_LINE: {w['wall_id']} share in {lid}")
                out[(w["wall_id"], it)] = sorted(sh.items())
                used.update(sh)
                continue
            cands = by_key.get((it, w["floor"], fam), [])
            if len(cands) == 1:
                out[(w["wall_id"], it)] = [(cands[0]["line_id"], 1.0)]
                used.add(cands[0]["line_id"])
            elif not cands:
                unmatched_w.append((w["wall_id"], it, f"no {it} line for storey {w['floor']} thickness {fam} m"))
            else:
                raise LedgerError(f"AMBIGUOUS_LINE: {w['wall_id']} {it}: {len(cands)} lines of one storey and family "
                                  "without declared shares")
    unmatched_l = [(ln["line_id"], ln.get("unmatched_reason") or
                    f"no register wall of storey {ln['floor']} family {ln.get('family')}")
                   for ln in lines if ln["line_id"] not in used]
    return out, unmatched_w, unmatched_l


def _q(v, f):
    return None if v is None else round(v * f, 6)


def ledger_rows(walls, lines, binding, unit_of=None):
    """rules 1 / 2: one row per (wall, line, item). unit_of: item_code -> 'm2' | 'm3' (m3 rows = m2 x t)."""
    unit_of = unit_of or {ln["item_code"]: ln["unit"] for ln in lines}
    W = {w["wall_id"]: w for w in walls}
    rows = []
    for (wid, it), parts in sorted(binding.items()):
        w = W[wid]
        st = wall_status(w)
        k = float(w["t_m"]) if unit_of[it] == "m3" else 1.0
        for lid, fr in parts:
            r = {"line_id": lid, "item_code": it, "unit": unit_of[it], "wall_id": wid, "floor": w["floor"],
                 "family": family_key(w["t_m"]), "block_type": w.get("block_type"), "status": st, "share": fr,
                 "carried": None, "upper": None, "drop_length_m": None, "drop_coefficient": None,
                 "held_item": None, "part_status": None, "verified_by": w.get("verified_by") or None,
                 "conflict_increment": _q(w.get("conflict_increment_m2"), k * fr) if w.get("conflict_increment_m2")
                 else None, "conflict": w.get("conflict") or None}
            if st in DETERMINATE:
                r["carried"] = _q(w["net_m2"], k * fr)
            elif st == HELD_ON_DROP:
                r["upper"] = _q(w["upper_m2"], k * fr)
                r["drop_length_m"] = round(w["drop_length_m"] * fr, 6)
                r["drop_coefficient"] = round(w["drop_length_m"] * k * fr, 6)   # m2 (or m3) per metre of d
                r["held_item"] = w.get("held_items")
                r["part_status"] = CLASS_TO_STATUS.get(w.get("class"))
            elif st == HELD:
                r["held_item"] = w.get("held_items")
            else:
                r["carried"] = _q(w["net_m2"], k * fr)
                r["held_item"] = w.get("held_items")
                r["part_status"] = CLASS_TO_STATUS.get(w.get("class"))
            check_row(r)
            rows.append(r)
    return rows


def register_totals(walls, item_unit="m2"):
    """the register's own totals per status (the reference the ledger must close on)."""
    t = {s: 0.0 for s in STATUSES}
    t["upper"], t["drop_length_m"], t["conflict_increment"] = 0.0, 0.0, 0.0
    for w in walls:
        st = wall_status(w)
        k = float(w["t_m"]) if item_unit == "m3" else 1.0
        if st in DETERMINATE or st == PART_PLUS_HELD:
            t[st] += w["net_m2"] * k
        elif st == HELD_ON_DROP:
            t["upper"] += w["upper_m2"] * k
            t["drop_length_m"] += w["drop_length_m"] * (k if item_unit == "m3" else 1.0)
        t["conflict_increment"] += (w.get("conflict_increment_m2") or 0.0) * k
    return {k: round(v, 6) for k, v in t.items()}


def ledger_totals(rows, item_code):
    t = {s: 0.0 for s in STATUSES}
    t["upper"], t["drop_length_m"], t["conflict_increment"] = 0.0, 0.0, 0.0
    n = {}
    for r in rows:
        if r["item_code"] != item_code:
            continue
        n[r["wall_id"]] = n.get(r["wall_id"], 0.0) + r["share"]
        if r["carried"] is not None:
            t[r["status"]] += r["carried"]
        if r["status"] == HELD_ON_DROP:
            t["upper"] += r["upper"]
            t["drop_length_m"] += r["drop_coefficient"]
        t["conflict_increment"] += r["conflict_increment"] or 0.0
    for wid, s in n.items():
        if abs(s - 1.0) > 1e-9:
            raise LedgerError(f"WALL_TWICE: {wid} carried {s:g} times in {item_code}")
    return {k: round(v, 6) for k, v in t.items()}


def closure(walls, rows, item_code, unit):
    """rule 3: residual register - ledger per status (must be 0 within TOL) -> {status: residual}."""
    a, b = register_totals(walls, unit), ledger_totals(rows, item_code)
    res = {k: round(a[k] - b[k], 6) for k in a}
    bad = {k: v for k, v in res.items() if abs(v) > TOL}
    if bad:
        raise LedgerError(f"NOT_CLOSED: {item_code} residuals {bad}")
    return res


def opening_ledger(openings, walls):
    """rule 4. openings: [{opening_id, host, deduction_m2 or None, state, source}] with state DEDUCTED (in a carried
    net, or in the U of a drop wall), ON_HELD_WALL (the deduction is established but its wall is HELD: shown, summed
    nowhere), IN_HELD_PIECE (in the held piece of an ESTABLISHED PART + HELD wall), HELD (the deduction itself is not
    established), NOT_APPLICABLE (its host builds no masonry) or NO_HOST. Refuses a duplicate id and a wall whose
    deductions (DEDUCTED + ON_HELD_WALL) do not sum to its register deduction ('deductions_m2' where stated)."""
    seen, by_wall = set(), {}
    for o in openings:
        if o["opening_id"] in seen:
            raise LedgerError(f"OPENING_TWICE: {o['opening_id']} is deducted twice")
        seen.add(o["opening_id"])
        if o["state"] in ("DEDUCTED", "ON_HELD_WALL"):
            if o.get("deduction_m2") is None or o["deduction_m2"] <= 0:
                raise LedgerError(f"HELD_AS_ZERO: {o['opening_id']} {o['state']} with {o.get('deduction_m2')!r}")
            by_wall[o["host"]] = by_wall.get(o["host"], 0.0) + o["deduction_m2"]
        elif o["state"] in ("IN_HELD_PIECE", "HELD"):
            if o.get("deduction_m2") == 0:
                raise LedgerError(f"HELD_AS_ZERO: {o['opening_id']} held, never deducted as 0")
        elif o["state"] not in ("NOT_APPLICABLE", "NO_HOST"):
            raise LedgerError(f"UNKNOWN_STATE: {o['opening_id']} {o['state']!r}")
    for w in walls:
        d = w.get("deductions_m2")
        if d is None:
            continue
        s = by_wall.get(w["wall_id"], 0.0)
        if abs(s - d) > 0.0005:
            raise LedgerError(f"OPENING_SUM: {w['wall_id']} openings {s:.4f} vs register deduction {d:.4f} m2")
    return {k: round(v, 6) for k, v in by_wall.items()}


def engine_vs_register(line, rows, walls, openings, engine_openings=None):
    """rule 5 for one candidate area line (m2). line: {line_id, quantity (measured or the stated upper / high),
    basis}; rows: this line's ledger rows; engine_openings: [{opening_id, deduction_m2}] the engine leaves out
    (w x h_in), by census id where bound. -> dict of named parts that sum exactly to engine - carried."""
    W = {w["wall_id"]: w for w in walls}
    q = line.get("quantity")
    if q is None:
        return {"line_id": line["line_id"], "engine": None, "note": "engine line carries no quantity"}
    carried = sum(r["carried"] or 0.0 for r in rows)
    held_walls = [r["wall_id"] for r in rows if r["status"] == HELD]
    drop_upper = sum(r["upper"] or 0.0 for r in rows if r["status"] == HELD_ON_DROP)
    L = sum(r["drop_length_m"] or 0.0 for r in rows if r["status"] == HELD_ON_DROP)
    # (c) openings: register deductions of the walls in this line vs the engine's
    hosts = {r["wall_id"] for r in rows}
    reg_op = sum(o["deduction_m2"] for o in openings if o["host"] in hosts and o["state"] == "DEDUCTED")
    eng_op = sum(o["deduction_m2"] for o in (engine_openings or ()))
    diff = q - carried
    parts = {"line_id": line["line_id"], "engine": round(q, 4), "carried_determinate_and_parts": round(carried, 4),
             "engine_minus_carried": round(diff, 4),
             "a_held_walls": held_walls, "b_drop_upper_at_d0": round(drop_upper, 4), "b_drop_length_m": round(L, 4),
             "c_openings_register_m2": round(reg_op, 4), "c_openings_engine_m2": round(eng_op, 4)}
    parts["d_remainder_storey_panel_basis"] = None   # filled by the caller only where (a) has figures
    return parts
