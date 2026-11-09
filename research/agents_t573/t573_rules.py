"""T-573 rules (any villa; research, unwired): ceilings reconciled against a reference takeoff BY ROOM GROUP AND FACE
CLASS, m2 and lm kept apart, every candidate line and every reference row used once.

R-T573-1 (proposed, every villa; provenance T-573; builds on R-T284-1 / R-T335-1 (one surface, one layer, one line),
R-T547-1 (bound every HELD element before any %), R-T561-1 (stair soffits are CEILING class, not wall paint) and the
lessons row 'gross vs gross'):
  (a) PHYSICAL ELEMENT FIRST. Under each slab face the built ceiling is split into face classes, each its own unit:
        BOARD            the horizontal decor (gypsum) ceiling at the finished-ceiling level, m2 = the room polygon
                         less what the slab plan above opens (light well, shaft, pocket) and less the faces of another
                         class (stair zone, open dome position)
        BULKHEAD         the vertical faces of a drop on a free beam edge, m2 = run x drop; NEVER inside BOARD (the
                         board under a bulkhead is still BOARD: the room area does not grow or shrink with a drop)
        STAIR_SOFFIT     the underside of a flight / landing (a stair finish), m2, never BOARD, never wall paint
        DOME             the intrados of an open dome position, m2, never BOARD
        EXTERIOR_SOFFIT  a soffit over outside air (an exterior finish), m2, never an interior BOARD row
        NO_CEILING       an opening in the slab above: no finish at all (never priced as BOARD)
        COVE             a cove / cornice run at the wall, lm; an area only from an approved detail, never a
                         '0.10 m strip' by convention inside BOARD
        PAINT            the paint system on the ceiling = BOARD + BULKHEAD of the room (owner Q-57 A mod (6)); his
                         paint statement may add his cove strips: a separate signed term, never a BOARD term
  (b) GROUPS. The reference rows carry no ids; a group joins candidate lines and reference rows that cover the same
      physical space (named rooms, an adjacency stated with its source, or a storey + class set when the rooms cannot
      be paired one by one). Every candidate line and every reference row sits in exactly one group (refused
      otherwise). A group is one unit (m2 or lm): an lm row in an m2 group is refused.
  (c) CAUSES (signed ours - his, as R-T559-1 / R-T568-1) close EXACTLY: gap = sum of causes. Verdicts: AGREE,
      TOLERANCE, ENGINE_RIGHT, ENGINE_WRONG, ENGINE_OMISSION, FREELANCER_WRONG, RULE_DIFFERENCE, HELD, NOT_IN_HIS_ROWS,
      UNRESOLVED. A HELD cause carries its bound (lo .. hi, the hi may be None = unbounded); its closing amount is
      stated and must lie inside -hi .. -lo. The remainder is a named cause (UNRESOLVED or TOLERANCE with its text),
      never an unnamed residual.
  (d) %. A like-for-like % is printed only for a group with NO HELD cause, no NOT_IN_HIS_ROWS (scope) cause and his
      total > 0; a group with a HELD cause prints its gap and its HELD bound, never a % (R-T547-1). Totals are summed
      per unit; m2 and lm never meet; different face classes are never summed into one comparison total.
  (e) STATUS. A research line status is one of DRAWING-CONFIRMED, ASSUMED - OWNER-APPROVED, ESTIMATED, PROVISIONAL,
      HELD; VERIFIED is the Checker's word and is refused here. HELD is never 0 and never a number in a sum.
"""
from __future__ import annotations

import functools
import inspect
import types
from decimal import Context, Decimal, localcontext

# T-653 (F-T648-2): 40 digits are used only INSIDE this module's functions, through a local Decimal context; importing
# this module never changes the process-global context (it used to set getcontext().prec = 40 at import, which changed
# every later Decimal result in the same process). in_prec40() at the end of the module applies the local context.
PREC = 40


def ctx40():
    """a local 40-digit Decimal context: `with ctx40(): ...`; the caller's context is restored on exit."""
    return localcontext(Context(prec=PREC))


def in_prec40(namespace: dict) -> None:
    """run every plain function DEFINED in the module of `namespace` (its globals()) inside ctx40(); generator
    functions, classes and names imported from other modules are left as they are. Marks each wrapper
    `_t653_prec40 = True`. Called once, at the end of the module (here and in its builder)."""
    mod = namespace["__name__"]
    for name, fn in list(namespace.items()):
        if (isinstance(fn, types.FunctionType) and fn.__module__ == mod and not getattr(fn, "_t653_prec40", False)
                and not inspect.isgeneratorfunction(fn) and name not in ("ctx40", "in_prec40")):
            namespace[name] = _wrap40(fn)


def _wrap40(fn):
    @functools.wraps(fn)
    def run40(*args, **kwargs):
        with ctx40():
            return fn(*args, **kwargs)
    run40._t653_prec40 = True
    return run40
CLASSES = ("BOARD", "BULKHEAD", "STAIR_SOFFIT", "DOME", "EXTERIOR_SOFFIT", "NO_CEILING", "COVE", "PAINT")
UNIT_OF = {c: ("lm" if c == "COVE" else "m2") for c in CLASSES}
VERDICTS = ("AGREE", "TOLERANCE", "ENGINE_RIGHT", "ENGINE_WRONG", "ENGINE_OMISSION", "FREELANCER_WRONG",
            "RULE_DIFFERENCE", "HELD", "NOT_IN_HIS_ROWS", "UNRESOLVED", "BY_TABLE")
STATUSES = ("DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "ESTIMATED", "PROVISIONAL", "HELD")
LEN_UNITS = {"m": Decimal(1), "mm": Decimal("0.001")}


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("quantity unknown (None) used as a number: HELD / UNKNOWN is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


# ---- geometry (any orientation; units explicit) ---------------------------------------------------------------------
def poly_area(coords, unit="m") -> Decimal:
    """Shoelace area in m2 of a simple polygon given in `unit` ('m' or 'mm'); orientation (mirror / rotation) free."""
    if unit not in LEN_UNITS:
        raise RuleError(f"length unit {unit!r} unknown (m or mm only)")
    k = LEN_UNITS[unit]
    pts = [(D(x) * k, D(y) * k) for x, y in coords]
    if len(pts) < 3:
        raise RuleError("a polygon needs 3 points")
    s = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    return abs(s) / 2


def board_area(room, openings=(), other_class=(), unit="m") -> Decimal:
    """BOARD m2 = room polygon - NO_CEILING openings - faces of another class (stair zone, dome), each polygon inside the
    room. A bulkhead is not a parameter: its vertical face is never added here (R-T573-1 (a))."""
    a = poly_area(room, unit)
    for p in list(openings) + list(other_class):
        a -= poly_area(p, unit)
    if a < 0:
        raise RuleError("deductions exceed the room area")
    return a


def bulkhead_face(run, drop, unit="m") -> Decimal:
    """BULKHEAD m2 = free beam-edge run x drop below the board (vertical face; its own class)."""
    if unit not in LEN_UNITS:
        raise RuleError(f"length unit {unit!r} unknown")
    r, d = D(run) * LEN_UNITS[unit], D(drop) * LEN_UNITS[unit]
    if r <= 0 or d <= 0:
        raise RuleError("bulkhead run and drop must be positive")
    return r * d


def board_line(value, parts):
    """A BOARD line's value must equal its BOARD parts; any BULKHEAD / COVE / STAIR_SOFFIT / DOME / NO_CEILING part
    inside it is refused (the bulkhead vertical added into the ceiling area, a cove strip by convention, ...)."""
    tot = Decimal(0)
    for cls, q in parts:
        if cls != "BOARD":
            raise RuleError(f"a {cls} face inside a BOARD (ceiling area) line: its own class, never the board")
        tot += D(q)
    if tot != D(value):
        raise RuleError(f"BOARD line {value} != its parts {tot}")
    return tot


def paint_of(board, bulkhead=None):
    """Ceiling paint of a room = BOARD + BULKHEAD (Q-57 A mod (6)); a HELD bulkhead keeps the paint figure at the
    board part with the bulkhead named HELD (never 0)."""
    return D(board) + (D(bulkhead) if bulkhead is not None else 0)


# ---- reconciliation --------------------------------------------------------------------------------------------------
def _cause(c, unit):
    lab, verdict, amount = c["label"], c["verdict"], D(c["amount"])
    if verdict not in VERDICTS:
        raise RuleError(f"verdict {verdict!r} unknown")
    if c.get("unit", unit) != unit:
        raise RuleError(f"cause {lab!r} in {c.get('unit')} inside an {unit} group: m2 and lm never mixed")
    if not str(lab).strip():
        raise RuleError("a cause without its name (an unnamed residual is refused)")
    if verdict == "HELD":
        lo, hi = c.get("bound", (None, None))
        if lo is None:
            raise RuleError(f"HELD cause {lab!r} without a lower bound")
        if hi is not None and not (-D(hi) <= amount <= -D(lo)):
            raise RuleError(f"HELD cause {lab!r}: amount {amount} outside its bound -{hi} .. -{lo}")
    elif "bound" in c:
        raise RuleError(f"a bound on a non-HELD cause {lab!r}")
    return amount


def reconcile(groups, lines, rows):
    """groups: [{id, unit, lines: [line_id], rows: [row_id], causes: [{label, verdict, amount, bound?, source}]}];
    lines: {line_id: {class, unit, value (None = HELD), status}}; rows: {row_id: {unit, value}}. -> table dict."""
    used_l, used_r, out, totals = {}, {}, [], {}
    for lid, ln in lines.items():
        if ln["status"] not in STATUSES:
            raise RuleError(f"line {lid}: status {ln['status']!r} refused (VERIFIED is the Checker's word)")
        if ln["status"] == "HELD" and ln["value"] is not None:
            raise RuleError(f"line {lid}: HELD with a value")
        if ln["status"] != "HELD" and ln["value"] is None:
            raise RuleError(f"line {lid}: no value but not HELD (missing never becomes 0)")
        if UNIT_OF[ln["class"]] != ln["unit"]:
            raise RuleError(f"line {lid}: class {ln['class']} is measured in {UNIT_OF[ln['class']]}, not {ln['unit']}")
    for g in groups:
        unit = g["unit"]
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
        h_hi = (None if any(c["bound"][1] is None for c in held)
                else sum((D(c["bound"][1]) for c in held), Decimal(0)))
        pct = None
        scope = [c for c in g["causes"] if c["verdict"] == "NOT_IN_HIS_ROWS"]
        if not held and not scope and his > 0:
            pct = (gap / his * 100).quantize(Decimal("0.01"))
        if g.get("pct") is not None and held:
            raise RuleError(f"group {g['id']}: a % asked on a group with a HELD cause (bound HELD before %)")
        t = totals.setdefault(unit, {"ours": Decimal(0), "his": Decimal(0)})
        t["ours"] += ours
        t["his"] += his
        out.append({"id": g["id"], "unit": unit, "ours": ours, "his": his, "gap": gap, "pct": pct,
                    "held_bound": [h_lo, h_hi], "causes": g["causes"], "lines": g["lines"], "rows": g["rows"]})
    missing_l = set(lines) - set(used_l)
    missing_r = set(rows) - set(used_r)
    if missing_l or missing_r:
        raise RuleError(f"not every item used once: lines {sorted(missing_l)} rows {sorted(missing_r)}")
    return {"groups": out, "totals": totals}


def like_for_like(table, unit="m2"):
    """Sum of the groups with a % (no HELD cause) in one unit -> (ours, his, gap, pct)."""
    gs = [g for g in table["groups"] if g["unit"] == unit and g["pct"] is not None]
    o = sum((g["ours"] for g in gs), Decimal(0))
    h = sum((g["his"] for g in gs), Decimal(0))
    return o, h, o - h, ((o - h) / h * 100).quantize(Decimal("0.01")) if h else None


def compare_units(a_unit, b_unit):
    if a_unit != b_unit:
        raise RuleError(f"{a_unit} compared with {b_unit}: m2 and lm never mixed")
    return True


in_prec40(globals())   # T-653: every function of this module runs in a local 40-digit context
