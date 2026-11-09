"""T-574 rules (any villa; research, unwired): SKIRTING reconciled against a reference takeoff by room / stair group and
by class, in lm (and nr for pieces), every candidate line and every reference row used once.

R-T574-1 (proposed, every villa; provenance T-574; builds on UP-SKIRT-001 / UP-CER-003 (doors and passages deducted),
the owner wet-area rule 2026-11-02 (no skirting on tiled faces), the register rulings STAIR vs ROOM SKIRTING and LIFT
DOOR GAP IN SKIRTING, R-T546-1 (a row's own unit label decides its unit), R-T547-1 (bound every HELD element before any
%), R-T573-1 (classes with their own units; causes close exactly) and the lessons row 'gross vs gross'):
  (a) PHYSICAL ELEMENT FIRST. A skirting is a strip at the foot of a finished, DRY, UNTILED wall or column face, at the
      level of the floor that stands against it. Classes, each its own comparison:
        ROOM          level skirting of a floored room, a stair-room floor part or a landing (FIN.SKIRTING), lm =
                      the room outline at floor level less every door, lift and passage opening, less every face where
                      no wall base exists (floor glazing, an open side, a slab opening / shaft at that level), less every
                      tiled face (wet room, wet pantry); door jambs / reveals take no skirting
        STAIR_FLIGHT  skirting along a flight's raking side (B7-07 zigzag / B7-08 sloped), lm developed along the
                      pitch, never the plan length; one piece has one line per form, never additive: a piece whose form
                      is not chosen is HELD with the bound min(form) .. max(form)
        OUTDOOR       a court / yard base, lm, only on a drawn wall face beside an outdoor finish
        PIECES        stair-side pieces counted per step, nr; never converted into lm (no printed piece size)
  (b) UNITS. lm and nr never meet; a reference row is taken in the unit its own label states (R-T546-1): an m2 row (or
      a row whose label is not lm) compared in an lm group is refused, and an lm row is never read as m2.
  (c) GROUPS. A group joins candidate lines and reference rows that cover the same physical space; every candidate line
      and every reference row sits in exactly one group (refused otherwise).
  (d) CAUSES (signed ours - his) close EXACTLY: gap = sum of causes. Each cause is an OUTLINE term (outline drawn vs his
      perimeter, faces added) or a DEDUCTION term (an opening or a face without a skirting). Verdicts: AGREE,
      TOLERANCE, ENGINE_RIGHT, ENGINE_WRONG, ENGINE_OMISSION, RULE_DIFFERENCE, HELD, NOT_IN_HIS_ROWS, UNRESOLVED. A HELD
      cause carries its bound (lo .. hi, hi None = unbounded); its amount lies inside -hi .. -lo; the remainder is a
      named cause, never an unnamed residual.
  (e) %. Only for a group with no HELD, no NOT_IN_HIS_ROWS, no SCOPE and no UNIT cause and his total > 0 (a unit
      total only when every group in that unit qualifies); gross vs gross (the OUTLINE
      terms) is reported beside the net; a % is never an accuracy figure.
  (f) STATUS. A research line status is DRAWING-CONFIRMED, ASSUMED - OWNER-APPROVED, ESTIMATED, PROVISIONAL, HELD or
      NOT_APPLICABLE; VERIFIED is the Checker's word and is refused here. HELD and NOT_APPLICABLE are never a number in a
      sum and never 0.
"""
from __future__ import annotations

from decimal import Decimal, getcontext

getcontext().prec = 40
UNITS = ("lm", "nr")
CLASSES = {"ROOM": "lm", "STAIR_FLIGHT": "lm", "OUTDOOR": "lm", "PIECES": "nr"}
VERDICTS = ("AGREE", "TOLERANCE", "ENGINE_RIGHT", "ENGINE_WRONG", "ENGINE_OMISSION", "RULE_DIFFERENCE", "HELD",
            "NOT_IN_HIS_ROWS", "UNRESOLVED")
KINDS = ("OUTLINE", "DEDUCTION", "HELD", "SCOPE", "UNIT")
STATUSES = ("DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "ESTIMATED", "PROVISIONAL", "HELD", "NOT_APPLICABLE")
FACE_CLASSES = ("DRY", "TILED", "NO_WALL")
LEN_UNITS = {"m": Decimal(1), "mm": Decimal("0.001")}


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("quantity unknown (None) used as a number: HELD / UNKNOWN is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def _len(x, unit):
    if unit not in LEN_UNITS:
        raise RuleError(f"length unit {unit!r} unknown (m or mm only)")
    v = D(x) * LEN_UNITS[unit]
    if v < 0:
        raise RuleError("a length is never negative")
    return v


# ---- the physical element (any villa) --------------------------------------------------------------------------------
def room_skirting(faces, openings=(), unit="m"):
    """ROOM skirting lm. faces: [(length, face_class)] around the room at floor level (DRY, TILED or NO_WALL);
    openings: [(id, width)] doors / lift / passages standing in DRY faces, each deducted whole, once, never with jamb
    returns. A TILED face (wet room / wet pantry, owner 2026-11-02) or a NO_WALL face (floor glazing, open side, slab
    opening) carries no skirting: listing one as skirted is refused by skirt_face."""
    dry = Decimal(0)
    for ln, cls in faces:
        if cls not in FACE_CLASSES:
            raise RuleError(f"face class {cls!r} unknown")
        if cls == "DRY":
            dry += _len(ln, unit)
    seen = set()
    ded = Decimal(0)
    for oid, w in openings:
        if not str(oid).strip():
            raise RuleError("an opening without its id")
        if oid in seen:
            raise RuleError(f"opening {oid} deducted twice")
        seen.add(oid)
        ded += _len(w, unit)
    if ded > dry:
        raise RuleError("openings exceed the dry faces")
    return dry - ded


def skirt_face(length, face_class, unit="m"):
    """One face's skirting: only a DRY face takes one; a tiled face (no paint or skirting on tiled faces) or a face with
    no wall base is refused."""
    if face_class == "TILED":
        raise RuleError("skirting on a tiled face refused (owner wet-area rule 2026-11-02: the tile owns the base)")
    if face_class == "NO_WALL":
        raise RuleError("skirting where no wall base stands refused (floor glazing / open side / slab opening)")
    if face_class != "DRY":
        raise RuleError(f"face class {face_class!r} unknown")
    return _len(length, unit)


def jamb_return(width):
    """Door / arch jambs take no skirting (R-T443-1, UP-SKIRT-001): any return is refused."""
    raise RuleError("a door or arch jamb return given a skirting refused")


def flight_bound(zigzag=None, sloped=None, status="HELD-FORM"):
    """A flight piece's held bound in lm (form not chosen: one of the two forms is built). HELD-FORM: min .. max of the
    two developed lengths; HELD with figures (a window or opening may cut it): 0 .. max; UNKNOWN / CONFLICT: 0 .. the
    figure if any, else unbounded. A plan length is never a flight figure (use flight_length)."""
    figs = [D(v) for v in (zigzag, sloped) if v is not None]
    if status == "HELD-FORM":
        if len(figs) != 2:
            raise RuleError("a HELD-FORM piece needs both developed lengths")
        return min(figs), max(figs)
    if status in ("HELD", "UNKNOWN", "CONFLICT"):
        return Decimal(0), (max(figs) if figs else None)
    raise RuleError(f"flight piece status {status!r} unknown")


def flight_length(going, rise, risers=None, form="sloped", unit="m"):
    """Developed skirting length of a straight flight side: sloped = hypot(going, rise); zigzag = going + rise.
    form 'plan' (the going alone) is refused for a flight."""
    g, r = _len(going, unit), _len(rise, unit)
    if form == "plan":
        raise RuleError("a plan length used for a flight skirting refused (developed length along the pitch)")
    if form == "sloped":
        return (g * g + r * r).sqrt()
    if form == "zigzag":
        return g + r
    raise RuleError(f"form {form!r} unknown")


# ---- reconciliation --------------------------------------------------------------------------------------------------
def _cause(c, unit):
    lab, verdict, kind = c["label"], c["verdict"], c.get("kind")
    amount = D(c["amount"])
    if verdict not in VERDICTS:
        raise RuleError(f"verdict {verdict!r} unknown")
    if kind not in KINDS:
        raise RuleError(f"cause {lab!r}: kind {kind!r} unknown")
    if c.get("unit", unit) != unit:
        raise RuleError(f"cause {lab!r} in {c.get('unit')} inside an {unit} group: lm and nr never mixed")
    if not str(lab).strip():
        raise RuleError("a cause without its name (an unnamed residual is refused)")
    if verdict == "HELD":
        lo, hi = c.get("bound", (None, None))
        if lo is None:
            raise RuleError(f"HELD cause {lab!r} without a lower bound")
        if hi is not None and D(hi) < D(lo):
            raise RuleError(f"HELD cause {lab!r}: bound hi < lo")
        if not ((hi is None or -D(hi) <= amount) and amount <= -D(lo)):
            raise RuleError(f"HELD cause {lab!r}: amount {amount} outside its bound -{hi} .. -{lo}")
    elif "bound" in c:
        raise RuleError(f"a bound on a non-HELD cause {lab!r}")
    return amount


def reconcile(groups, lines, rows):
    """groups: [{id, unit, lines, rows, causes}]; lines: {id: {class, unit, value (None = HELD / NA), status}};
    rows: {id: {unit, value}} (unit from the row's own label). -> {groups, totals}."""
    used_l, used_r, out, totals = {}, {}, [], {}
    for lid, ln in lines.items():
        if ln["status"] not in STATUSES:
            raise RuleError(f"line {lid}: status {ln['status']!r} refused (VERIFIED is the Checker's word)")
        if ln["status"] in ("HELD", "NOT_APPLICABLE") and ln["value"] is not None:
            raise RuleError(f"line {lid}: {ln['status']} with a value")
        if ln["status"] not in ("HELD", "NOT_APPLICABLE") and ln["value"] is None:
            raise RuleError(f"line {lid}: no value but not HELD (missing never becomes 0)")
        if CLASSES.get(ln["class"]) != ln["unit"]:
            raise RuleError(f"line {lid}: class {ln['class']} is measured in {CLASSES.get(ln['class'])}, "
                            f"not {ln['unit']}")
    for rid, r in rows.items():
        if r["unit"] not in UNITS:
            raise RuleError(f"his row {rid} in {r['unit']}: a skirting row is lm (or nr pieces), never m2")
    for g in groups:
        unit = g["unit"]
        if unit not in UNITS:
            raise RuleError(f"group {g['id']}: unit {unit} refused")
        ours, his = Decimal(0), Decimal(0)
        for lid in g["lines"]:
            if lid in used_l:
                raise RuleError(f"line {lid} in two groups ({used_l[lid]}, {g['id']})")
            used_l[lid] = g["id"]
            ln = lines[lid]
            if ln["unit"] != unit:
                raise RuleError(f"line {lid} ({ln['unit']}) in an {unit} group")
            if ln["value"] is not None:
                ours += D(ln["value"])
        for rid in g["rows"]:
            if rid in used_r:
                raise RuleError(f"his row {rid} in two groups ({used_r[rid]}, {g['id']})")
            used_r[rid] = g["id"]
            if rows[rid]["unit"] != unit:
                raise RuleError(f"his row {rid} in {rows[rid]['unit']} compared in an {unit} group")
            his += D(rows[rid]["value"])
        gap = ours - his
        amounts = [_cause(c, unit) for c in g["causes"]]
        if sum(amounts, Decimal(0)) != gap:
            raise RuleError(f"group {g['id']}: causes {sum(amounts, Decimal(0))} != gap {gap} (must close exactly)")
        held = [c for c in g["causes"] if c["verdict"] == "HELD"]
        h_lo = sum((D(c["bound"][0]) for c in held), Decimal(0))
        h_hi = None if any(c["bound"][1] is None for c in held) else sum((D(c["bound"][1]) for c in held), Decimal(0))
        scope = [c for c in g["causes"] if c["verdict"] == "NOT_IN_HIS_ROWS" or c["kind"] in ("SCOPE", "UNIT")]
        comparable = not held and not scope
        pct = (gap / his * 100).quantize(Decimal("0.01")) if (comparable and his > 0) else None
        outline = sum((D(c["amount"]) for c in g["causes"] if c["kind"] == "OUTLINE"), Decimal(0))
        t = totals.setdefault(unit, {"ours": Decimal(0), "his": Decimal(0), "comparable": True})
        t["ours"] += ours
        t["his"] += his
        t["comparable"] = t["comparable"] and comparable
        out.append({"id": g["id"], "unit": unit, "ours": ours, "his": his, "gap": gap, "pct": pct,
                    "outline_gap": outline, "held_bound": [h_lo, h_hi], "causes": g["causes"], "lines": g["lines"],
                    "rows": g["rows"], "note": g.get("note", "")})
    missing_l = set(lines) - set(used_l)
    missing_r = set(rows) - set(used_r)
    if missing_l or missing_r:
        raise RuleError(f"not every item used once: lines {sorted(missing_l)} rows {sorted(missing_r)}")
    return {"groups": out, "totals": totals}


def by_verdict(table):
    out = {}
    for g in table["groups"]:
        for c in g["causes"]:
            k = (g["unit"], c["verdict"])
            out[k] = out.get(k, Decimal(0)) + D(c["amount"])
    return out


def like_for_like(table, unit="lm"):
    gs = [g for g in table["groups"] if g["unit"] == unit and g["pct"] is not None]
    o = sum((g["ours"] for g in gs), Decimal(0))
    h = sum((g["his"] for g in gs), Decimal(0))
    return o, h, o - h, ((o - h) / h * 100).quantize(Decimal("0.01")) if h else None


def compare_units(a_unit, b_unit):
    if a_unit != b_unit:
        raise RuleError(f"{a_unit} compared with {b_unit}: lm, nr and m2 never mixed")
    return True
