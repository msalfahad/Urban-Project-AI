"""T-577 rules (any villa; research, unwired): MARBLE / STONE THRESHOLDS, WINDOW SILLS, LIFT and ENTRANCE STONE
reconciled against a reference takeoff by item, one table per unit (lm, m2, nr), every piece and every reference cell
used once per table.

R-T577-1 (proposed, every villa; provenance T-577; builds on UP-THR-001 (threshold = clear door width x wall thickness),
URBAN-WET-SERVICE-MARBLE-THRESHOLD v1, UP-REVEAL-001 (a sill is its own item), UP-ELEV-001..005 (lift threshold /
surround, T-475), R-T325-1 / R-T327-1 (one strip per opening; m2 / lm / nr three measures of one strip), R-T546-1 (a
number's unit is its own column label), R-T547-1 (bound every HELD element before any %), R-T574-1 (causes close
exactly) and ERS s.2-4):
  (a) PHYSICAL ELEMENT FIRST, one piece per opening (or station), each with three measures:
        THRESHOLD       a door strip at floor level: lm = the clear (jamb-gap) width, m2 = width x wall thickness,
                        nr = 1; wet doorway marble, dry the floor porcelain continued, external by specification
        SILL            a window's sill / outside strip: lm = opening width + PRINTED returns only (a return that is not
                        printed is never added), m2 = lm x the drawn depth, nr = 1
        LIFT_THRESHOLD  per landing door (T-475); a SURROUND is m2 only (HELD while the door height is not printed)
        EXT_STEP        a step piece outside an external door: its own element, never the threshold strip in the wall
        STAIR_STEP      an entrance-stair step: tread / riser m2, step lm per tread (width), nr per tread
  (b) ONE OPENING, ONE PIECE. A piece is keyed by its opening id; the same opening read on two plans (or twice on one)
      is refused, never counted twice.
  (c) UNITS (R-T546-1). A reference number enters a unit table only under its own column label. A cell labelled m2 whose
      row has no area / width cell and equals count x length is LENGTH_IN_AREA_COLUMN: it closes his m2 total with a
      UNIT cause and is never compared as m2; it is never read as lm either (an m2-labelled cell compared as lm is
      refused). His lm figure for that row is his own count cell (nr label) x his own length cell (lm label), never a
      conversion. lm, m2 and nr never meet.
  (d) CAUSES (signed ours - his) close EXACTLY: gap = sum of causes. A HELD cause carries amount 0 and the bound of what
      the held pieces would add (lo .. hi, hi None = unbounded); held pieces never enter a sum and are never 0.
  (e) %. Only for a group with no HELD, SCOPE or UNIT cause and his total > 0; never an accuracy figure.
  (f) STATUS. DRAWING-CONFIRMED, ASSUMED - OWNER-APPROVED, ESTIMATED, PROVISIONAL, HELD or NOT_APPLICABLE; VERIFIED is
      the Checker's word and is refused here.
"""
from __future__ import annotations

import math
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
UNITS = ("lm", "m2", "nr")
ELEMENTS = ("THRESHOLD", "SILL", "LIFT_THRESHOLD", "LIFT_SURROUND", "EXT_STEP", "STAIR_STEP", "LANDING")
VERDICTS = ("AGREE", "TOLERANCE", "ENGINE_RIGHT", "ENGINE_WRONG", "ENGINE_OMISSION", "RULE_DIFFERENCE", "HELD",
            "NOT_IN_HIS_ROWS", "UNRESOLVED")
KINDS = ("MEASURE", "HELD", "SCOPE", "UNIT")
STATUSES = ("DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "ESTIMATED", "PROVISIONAL", "HELD", "NOT_APPLICABLE")
CELL_CLASSES = ("AREA", "LENGTH", "COUNT", "LENGTH_IN_AREA_COLUMN")
LEN_UNITS = {"m": Decimal(1), "mm": Decimal("0.001")}


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("quantity unknown (None) used as a number: HELD / UNKNOWN is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def _len(x, unit="m"):
    if unit not in LEN_UNITS:
        raise RuleError(f"length unit {unit!r} unknown (m or mm only)")
    v = D(x) * LEN_UNITS[unit]
    if v < 0:
        raise RuleError("a length is never negative")
    return v


# ---- the physical element (any villa) --------------------------------------------------------------------------------
def jamb_width(p, q, unit="m", places=6):
    """Clear width between two jamb points (x, y) in any rotation or mirror; 6 dp (the ledger precision)."""
    if unit not in LEN_UNITS:
        raise RuleError(f"length unit {unit!r} unknown (m or mm only)")
    d = math.hypot(float(q[0]) - float(p[0]), float(q[1]) - float(p[1]))
    return (D(d) * LEN_UNITS[unit]).quantize(Decimal(1).scaleb(-places))


def threshold(width, wall_t, unit="m"):
    """A door strip: (lm, m2, nr) = (width, width x wall thickness, 1). A missing width or thickness is HELD (refused
    here, never 0)."""
    w, t = _len(width, unit), _len(wall_t, unit)
    if w == 0 or t == 0:
        raise RuleError("a threshold with zero width or depth: the opening or the wall is not established (HELD)")
    return w, w * t, 1


def sill(width, depth, returns=(), unit="m"):
    """A window sill: lm = width + printed returns; returns: [(length, printed: bool)]; an unprinted return is refused
    (never added by default)."""
    w, d = _len(width, unit), _len(depth, unit)
    if w == 0 or d == 0:
        raise RuleError("a sill with zero width or depth: not established (HELD)")
    lm = w
    for ln, printed in returns:
        if not printed:
            raise RuleError("a sill return that is not printed is refused (length = opening + printed returns only)")
        lm += _len(ln, unit)
    return lm, lm * d, 1


def pieces_once(pieces):
    """pieces: [(opening id, plan / sheet)]: the same opening read twice (two plans, or twice on one) is refused."""
    seen = {}
    for oid, plan in pieces:
        if not str(oid).strip():
            raise RuleError("a piece without its opening id")
        if oid in seen:
            raise RuleError(f"opening {oid} read twice ({seen[oid]}, {plan}): one opening, one piece")
        seen[oid] = plan
    return len(seen)


def totals(pieces, unit="m"):
    """Sum (lm, m2, nr) over measured pieces [(opening id, plan, (lm, m2, nr))] after the once check."""
    pieces_once([(p[0], p[1]) for p in pieces])
    lm = sum((D(p[2][0]) for p in pieces), Decimal(0))
    m2 = sum((D(p[2][1]) for p in pieces), Decimal(0))
    return lm, m2, sum(int(p[2][2]) for p in pieces)


# ---- his cells: the unit is the column label (R-T546-1) --------------------------------------------------------------
def classify_cell(label_unit, count=None, length=None, area=None, height=None, value=None):
    """Class of one reference total cell from its own column label and its row's dimension cells.
    An m2-labelled value with no area and no height cell that equals count x length is LENGTH_IN_AREA_COLUMN."""
    if label_unit not in UNITS:
        raise RuleError(f"label unit {label_unit!r} not established: the cell's unit is unknown")
    if label_unit == "nr":
        return "COUNT"
    if label_unit == "lm":
        return "LENGTH"
    if area is not None or height is not None:
        return "AREA"
    if count is not None and length is not None and value is not None and D(count) * D(length) == D(value):
        return "LENGTH_IN_AREA_COLUMN"
    raise RuleError("an m2 cell with no area / height cell and not count x length: its basis is not established")


def his_cell(unit_of_table, label_unit, value):
    """A reference cell offered to a unit table: refused unless its own label is that unit."""
    if label_unit != unit_of_table:
        raise RuleError(f"his {label_unit} cell compared in an {unit_of_table} table refused (R-T546-1)")
    return D(value)


def length_of_row(count, count_label, length, length_label):
    """His lm for a row = his count cell (nr label) x his length cell (lm label): a product of his own cells, never a
    conversion of an area."""
    if count_label != "nr" or length_label != "lm":
        raise RuleError("a row length needs a count cell labelled nr and a length cell labelled lm")
    return D(count) * D(length)


# ---- reconciliation --------------------------------------------------------------------------------------------------
def _cause(c, unit):
    lab, verdict, kind = c["label"], c["verdict"], c.get("kind")
    if verdict not in VERDICTS:
        raise RuleError(f"verdict {verdict!r} unknown")
    if kind not in KINDS:
        raise RuleError(f"cause {lab!r}: kind {kind!r} unknown")
    if not str(lab).strip():
        raise RuleError("a cause without its name (an unnamed residual is refused)")
    amount = D(c["amount"])
    if verdict == "HELD":
        if kind != "HELD":
            raise RuleError(f"HELD cause {lab!r} must be of kind HELD")
        if amount != 0:
            raise RuleError(f"HELD cause {lab!r}: amount must be 0 (the bound carries the range)")
        lo, hi = c.get("bound", (None, None))
        if lo is None:
            raise RuleError(f"HELD cause {lab!r} without a lower bound")
        if hi is not None and D(hi) < D(lo):
            raise RuleError(f"HELD cause {lab!r}: bound hi < lo")
    elif "bound" in c:
        raise RuleError(f"a bound on a non-HELD cause {lab!r}")
    return amount


def reconcile(unit, groups, pieces, cells):
    """unit: lm / m2 / nr. groups: [{id, pieces, cells, causes}]; pieces: {id: {unit, value (None = HELD), status}};
    cells: {id: {label, value, class}}. Every piece and cell of this table used exactly once."""
    if unit not in UNITS:
        raise RuleError(f"unit {unit!r} refused")
    for pid, p in pieces.items():
        if p["unit"] != unit:
            raise RuleError(f"piece {pid} in {p['unit']} inside the {unit} table")
        if p["status"] not in STATUSES:
            raise RuleError(f"piece {pid}: status {p['status']!r} refused (VERIFIED is the Checker's word)")
        if p["status"] in ("HELD", "NOT_APPLICABLE") and p["value"] is not None:
            raise RuleError(f"piece {pid}: {p['status']} with a value")
        if p["status"] not in ("HELD", "NOT_APPLICABLE") and p["value"] is None:
            raise RuleError(f"piece {pid}: no value but not HELD (missing never becomes 0)")
    for cid, c in cells.items():
        if c["class"] not in CELL_CLASSES:
            raise RuleError(f"cell {cid}: class {c['class']!r} unknown")
        if c["label"] != unit:
            raise RuleError(f"his {c['label']} cell {cid} offered to the {unit} table refused (R-T546-1)")
    used_p, used_c, out = {}, {}, []
    tot = {"ours": Decimal(0), "his": Decimal(0), "comparable": True}
    for g in groups:
        ours, his = Decimal(0), Decimal(0)
        for pid in g["pieces"]:
            if pid in used_p:
                raise RuleError(f"piece {pid} in two groups ({used_p[pid]}, {g['id']})")
            used_p[pid] = g["id"]
            if pieces[pid]["value"] is not None:
                ours += D(pieces[pid]["value"])
        for cid in g["cells"]:
            if cid in used_c:
                raise RuleError(f"his cell {cid} in two groups ({used_c[cid]}, {g['id']})")
            used_c[cid] = g["id"]
            his += D(cells[cid]["value"])
        gap = ours - his
        amounts = [_cause(c, unit) for c in g["causes"]]
        if sum(amounts, Decimal(0)) != gap:
            raise RuleError(f"group {g['id']}: causes {sum(amounts, Decimal(0))} != gap {gap} (must close exactly)")
        held = [c for c in g["causes"] if c["verdict"] == "HELD"]
        lo = sum((D(c["bound"][0]) for c in held), Decimal(0))
        hi = None if any(c["bound"][1] is None for c in held) else sum((D(c["bound"][1]) for c in held), Decimal(0))
        comparable = not held and not any(c["kind"] in ("SCOPE", "UNIT") for c in g["causes"])
        pct = (gap / his * 100).quantize(Decimal("0.01")) if (comparable and his > 0) else None
        tot["ours"] += ours
        tot["his"] += his
        tot["comparable"] = tot["comparable"] and comparable
        out.append({"id": g["id"], "unit": unit, "ours": ours, "his": his, "gap": gap, "pct": pct,
                    "held_bound": [lo, hi], "pieces": list(g["pieces"]), "cells": list(g["cells"]),
                    "causes": g["causes"], "note": g.get("note", "")})
    miss_p, miss_c = set(pieces) - set(used_p), set(cells) - set(used_c)
    if miss_p or miss_c:
        raise RuleError(f"not every item used once: pieces {sorted(miss_p)} cells {sorted(miss_c)}")
    if sum((g["ours"] for g in out), Decimal(0)) != tot["ours"] or sum((g["his"] for g in out), Decimal(0)) != tot["his"]:
        raise RuleError("group sums do not close to the table totals")
    return {"unit": unit, "groups": out, "totals": tot}


def partition(total, parts):
    """His cover / sheet total split into named parts [(label, value)] closing exactly (no unnamed remainder)."""
    s = sum((D(v) for _, v in parts), Decimal(0))
    if s != D(total):
        raise RuleError(f"partition {s} != total {total}: an unnamed remainder")
    return s


in_prec40(globals())   # T-653: every function of this module runs in a local 40-digit context
