"""T-602 rules (any villa; research, unwired): which exterior openings carry an external step, and how a reference
takeoff's door-step pieces that carry no opening id are reconciled.

R-T602-1 (proposed, every villa; provenance T-602; builds on R-T584-1 (a step exists only where its edge is drawn and
the printed levels differ), R-T592-1 (one payable length = the wall gap; outside level from the step's own region),
ERS s.2-4):
  (a) THE CENSUS. Every exterior opening is listed: each door / gate / leafless opening of the opening census whose one
      side is outdoors, AND every opening in the plot boundary (fence gates and gate gaps, with or without a leaf). For
      each: the printed level reachable on each side (R-T592-1 (d) region read) and a step decision. An opening that is
      not listed has no decision; a reconciliation that relies on an unlisted opening is refused.
  (b) THE DECISION per opening:
      - STEP (DRAWING-CONFIRMED) when a drawn edge pair (front edge + companion on the higher side) stands AT the
        opening (touching its own drawn geometry) AND the two sides read one figure each and they differ, the
        companion on the higher one. Payable lm = the wall gap (R-T592-1 (a)); riser m = high - low.
      - HELD (by name, with the bound) when an edge pair is drawn there but a side reads no or two figures; or when the
        levels differ at a PASSABLE opening and no edge is drawn (the form of the level change is not drawn: step,
        ramp or kerb unknown).
      - NO_STEP when the two sides read the same figure (an edge or a step given there is refused: CONFLICT), or when
        no edge is drawn and the levels do not differ, or when the opening is not passable (a low wall drawn through
        it, a window over a void).
  (c) AN EDGE PAIR AWAY FROM EVERY EXTERIOR OPENING is never a door step: it is a flight / landing edge (B7, R-T412-1)
      or an outdoor step (EXT_STEP) and is owned there.
  (d) RECONCILING PIECES WITHOUT IDS. When the reference books door-step pieces with no opening id, the comparison is
      in aggregate: count (nr) and length (lm) against the census's STEP openings; a piece is never assigned to an
      opening because its figure equals one (figure matching is not evidence). The residual is stated in lm and nr;
      a candidate cause (a drawn measure the reference may have read instead) may be named beside it, but it stays
      UNRESOLVED until his rows carry an id or the owner rules.
  (e) Units never meet (lm, m2, nr); HELD is never 0; VERIFIED is the Checker's word.
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
LEN_UNITS = {"m": Decimal(1), "mm": Decimal("0.001")}
DECISIONS = ("STEP", "HELD", "NO_STEP")
AT_OPENING_M = Decimal("0.10")      # an edge pair 'at' an opening touches its own drawn geometry (drafting tolerance)


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("quantity unknown (None) used as a number: HELD / UNKNOWN is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def length(x, unit="m"):
    if unit not in LEN_UNITS:
        raise RuleError(f"length unit {unit!r} unknown (m or mm only)")
    v = D(x) * LEN_UNITS[unit]
    if v <= 0:
        raise RuleError("a piece / gap length is positive")
    return v


def level(txt):
    if txt is None:
        raise RuleError("a level that is not printed is not a figure")
    return D(str(txt).strip().replace("+-", "").replace("%%p", ""))


def one_figure(region):
    """The single printed figure of a side's region, or None (none / two or more figures)."""
    figs = sorted({level(t) for t in (region or [])})
    return figs[0] if len(figs) == 1 else None


def at_opening(distance_m):
    return D(distance_m) <= AT_OPENING_M


def decide(opening, side_in, side_out, edge_pair=None, passable=True, gap_m=None, unit="m", given_step=False,
           fallback_in=None, fallback_out=None):
    """R-T602-1 (b). side_in / side_out: the printed figures reachable on each side (lists of level texts).
    edge_pair: None or {'high_side': 'in' | 'out', 'distance_m': ...} for a pair at the opening. fallback_in / _out:
    a figure printed in the same open space but outside the strict region read (evidence only, never a riser).
    given_step: a step booked there by someone (refused when the levels are equal)."""
    lin, lout = one_figure(side_in), one_figure(side_out)
    fin = lin if lin is not None else (None if fallback_in is None else level(fallback_in))
    fout = lout if lout is not None else (None if fallback_out is None else level(fallback_out))
    if fin is not None and fout is not None and fin == fout:
        if edge_pair is not None or given_step:
            raise RuleError(f"{opening}: a step at an opening with equal printed levels ({fin}) is a CONFLICT: refused")
        return {"opening": opening, "decision": "NO_STEP", "why": "same printed level both sides", "nr": 0,
                "payable_lm": None}
    if not passable:
        if given_step:
            raise RuleError(f"{opening}: a step booked at an opening that is not passable: refused")
        return {"opening": opening, "decision": "NO_STEP", "why": "not passable (drawn through / over a void)",
                "nr": 0, "payable_lm": None}
    if edge_pair is not None:
        if not at_opening(edge_pair["distance_m"]):
            raise RuleError(f"{opening}: the edge pair is not at the opening (R-T602-1 (c)): not a door step")
        if gap_m is None:
            raise RuleError(f"{opening}: a step with no measured wall gap: HELD, never 0")
        gap = length(gap_m, unit)
        if lin is None or lout is None:
            return {"opening": opening, "decision": "HELD", "why": "edge drawn, a side reads no single figure",
                    "nr": 1, "payable_lm": gap, "riser_m": None,
                    "riser_bound": None if fin is None or fout is None else (D(0), abs(fin - fout))}
        hi, lo = (lin, lout) if edge_pair["high_side"] == "in" else (lout, lin)
        if hi <= lo:
            raise RuleError(f"{opening}: the companion lies on the LOWER side: the edge reading is inverted, HELD")
        return {"opening": opening, "decision": "STEP", "status": "DRAWING-CONFIRMED", "nr": 1, "payable_lm": gap,
                "riser_m": hi - lo, "riser_m2": gap * (hi - lo)}
    if fin is not None and fout is not None:
        return {"opening": opening, "decision": "HELD", "why": "levels differ at a passable opening, no edge drawn "
                "(step / ramp / kerb not drawn)", "nr": None, "payable_lm": None,
                "riser_bound": (D(0), abs(fin - fout))}
    return {"opening": opening, "decision": "NO_STEP", "why": "no edge drawn, no level change printed", "nr": 0,
            "payable_lm": None}


def reconcile(his_pieces, census):
    """R-T602-1 (d): his pieces (lengths, no ids) vs the census's STEP / HELD openings, in aggregate only."""
    his = [length(x) for x in his_pieces]
    ours = [r for r in census if r["decision"] in ("STEP", "HELD") and r.get("payable_lm") is not None]
    held = [r for r in census if r["decision"] == "HELD"]
    lm_o = sum((r["payable_lm"] for r in ours), D(0))
    lm_h = sum(his, D(0))
    return {"his_lm": lm_h, "his_nr": len(his), "ours_lm": lm_o, "ours_nr": len(ours),
            "held_openings": [r["opening"] for r in held],
            "residual_lm_ours_minus_his": lm_o - lm_h, "residual_nr_ours_minus_his": len(ours) - len(his),
            "attribution": "AGGREGATE_ONLY (his rows carry no opening id; figure matching refused)"}


def attribute_by_figure(*_a, **_k):
    raise RuleError("assigning a reference piece to an opening because the figures are equal is refused "
                    "(R-T602-1 (d))")


def book(line_unit, value_unit):
    if line_unit != value_unit:
        raise RuleError(f"a {value_unit} quantity booked on a {line_unit} line: refused")
    return True


in_prec40(globals())   # T-653: every function of this module runs in a local 40-digit context
