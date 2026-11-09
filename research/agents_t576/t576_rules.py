"""T-576 rules (research, unwired): a column measured-set difference restated as signed causes with a verdict class
each, and a beam UNTRACED term tested against a COMPLETE support allowance, for any villa.

R-T576-1 HEIGHT BASIS AND CAUSE CLASSES. On a storey whose datums are drawn (slab top to slab top), engine column h =
    storey interval (+ base drop where the member stands lower, BASE); his h = storey interval - his one head depth
    d_his. Check first that his h + d_his equals the drawn storey interval on every row (STOREY term = 0, else it is a
    term of its own). Then per valued member A x (h_e - h_his) = JOINT_HEAD (A x D_ctrl, the joint + head the column
    line owns to the slab top: RULE_DIFFERENCE, ownership) + BASE (ENGINE_RIGHT, drawn datum) + GLOBAL_DEPTH
    (A x (d_his - D_ctrl): his own clear-height convention applied with one global depth instead of the member's drawn
    controlling depth: ENGINE_RIGHT, either sign). Where D_ctrl is open because a framing member's depth is not printed
    but a SETTLED framing member prints D_low, D_ctrl >= D_low: JOINT_HEAD >= A x D_low (RULE_DIFFERENCE) and the
    counter-term GLOBAL_DEPTH <= A x (d_his - D_low), open below by the unprinted depth; the column's own m3 does not
    depend on D_ctrl (it runs to the slab top), only the split does. COUNT is ENGINE_RIGHT only where the drawn own-member
    count of the mark equals its registered positions and no CONFLICT position can carry the mark; otherwise it is
    CONFLICT-bounded. HELD stays HELD (never 0); an unexplained remainder is UNRESOLVED by name.
R-T576-2 MEASURED SET PER READING. The like-for-like set (marks fully valued with a row of his) depends on which mark a
    CONFLICT position carries: the set, its totals and its percentage are computed for EVERY reading of every conflict
    that moves a line between marks and reported side by side; never one reading by majority of sheets or by section fit.
R-T576-3 COMPLETE SUPPORT ALLOWANCE BEFORE UNTRACED. A beam mark's residual can be called UNTRACED only when every end
    of every piece of the mark carries a closing record: column / carrier extent along the run (carrier = a member of
    ANOTHER mark whose face closes the piece), 0 for a tangent / pinch or a collinear continuation of another mark, and
    a held unlabelled piece listed BESIDE (never inside the allowance). Curved pieces and ledger-only pieces (no route G
    band) need the same records. With an end record missing, the term is NOT_DETERMINABLE, never UNRESOLVED; with the
    allowance complete, his longer length inside it is THROUGH_SUPPORT (RULE_DIFFERENCE; the engine bills each crossing
    once, the carrier owns it).
R-T576-4 OWNERSHIP ONCE. A column-beam joint is billed once: through-height column with net beams, or clear-height
    column with the beam through; the joint in both lines (or in neither) is refused.

Provenance: T-576 (2026-11-07), on R-T551-1 .. 4, R-T566-1 .. 5, R-T572-4, R-T394-1, R-T395-4, R-CONC-OWN-1,
ERS s.2 - 4. Scope: every villa.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

Q6 = Decimal("0.000001")
Q2 = Decimal("0.01")
CLASSES = ("RULE_DIFFERENCE", "ENGINE_RIGHT", "CONFLICT_BOUNDED", "HELD", "UNRESOLVED", "ENGINE_WRONG")
SPLIT_OPEN_LOW = "SPLIT_OPEN_AT_D_LOW"


class Refused(ValueError):
    """A reading the rules refuse."""


def d6(x) -> Decimal:
    if x is None:
        raise Refused("missing value: carry it HELD, never 0")
    if isinstance(x, str):
        s = x.strip().lower()
        if s.endswith("%"):
            raise Refused("a percentage is not a quantity")
        if s.endswith(("mm", "kg", " t", "m2")):
            raise Refused("give metres / m3")
    v = Decimal(str(x))
    return v.quantize(Q6, rounding=ROUND_HALF_UP)


def _pos(v, what):
    v = d6(v)
    if v <= 0:
        raise Refused(f"non-positive {what}")
    if v > 50:
        raise Refused(f"{what} looks like mm: give metres")
    return v


# ---------------------------------------------------------------------------------------------------------- R-T576-1
def storey_term(storey_interval, his_h, his_depth):
    """STOREY term per row of his: (drawn interval) - (his h + his depth); 0 when his frame equals the drawn one."""
    return d6(_pos(storey_interval, "storey interval") - (_pos(his_h, "his h") + _pos(his_depth, "his depth")))


def member_height_split(*, A, h_e, base_drop, his_h, d_ctrl=None, d_low=None):
    """One valued member (his section = drawn section, his height his_h). Returns {term: m3} re-adding to A x (h_e -
    his_h). d_ctrl settled -> JOINT_HEAD / BASE / GLOBAL_DEPTH. d_ctrl open -> split at d_low (the settled framing
    member's printed depth, a LOWER bound of D_ctrl): JOINT_HEAD_AT_D_LOW + GLOBAL_DEPTH_AT_D_LOW, flagged open."""
    A, h_e, his_h = _pos(A, "A"), _pos(h_e, "h_e"), _pos(his_h, "his h")
    bs = d6(A * d6(base_drop))
    tot = d6(A * (h_e - his_h))
    if d_ctrl is not None:
        jh = d6(A * _pos(d_ctrl, "D_ctrl"))
        out = {"JOINT_HEAD": jh, "BASE": bs, "GLOBAL_DEPTH": tot - jh - bs}
    else:
        if d_low is None:
            raise Refused("D_ctrl open and no settled framing depth: the split stays HEIGHT_OPEN, unbounded")
        jh = d6(A * _pos(d_low, "D_low"))
        out = {"JOINT_HEAD": jh, "BASE": bs, "GLOBAL_DEPTH": tot - jh - bs, SPLIT_OPEN_LOW: True}
    if sum(v for k, v in out.items() if k != SPLIT_OPEN_LOW) != tot:
        raise Refused("height split does not re-add")
    return out


def count_verdict(*, drawn_n, registered_n, conflict_positions):
    """COUNT verdict for one storey x mark from the position register."""
    if conflict_positions:
        return "CONFLICT_BOUNDED"
    if drawn_n != registered_n:
        return "UNRESOLVED"
    return "ENGINE_RIGHT"


def classify(term, *, count_class=None):
    if term == "COUNT":
        if count_class is None:
            raise Refused("a COUNT verdict needs the position register")
        return count_class
    return {"JOINT_HEAD": "RULE_DIFFERENCE", "BASE": "ENGINE_RIGHT", "GLOBAL_DEPTH": "ENGINE_RIGHT", "HELD": "HELD",
            "SECTION": "UNRESOLVED", "STOREY": "UNRESOLVED", "HEIGHT_OPEN": "UNRESOLVED"}[term]


def class_table(rows):
    """rows: [{'term', 'class', 'm3'}] -> {class: m3}; refuses an unknown class or a HELD closed as 0 by omission."""
    out = {}
    for r in rows:
        if r["class"] not in CLASSES:
            raise Refused(f"class {r['class']}")
        out[r["class"]] = out.get(r["class"], Decimal(0)) + d6(r["m3"])
    return {k: d6(v) for k, v in out.items()}


def pct(diff, his):
    his = d6(his)
    if his <= 0:
        raise Refused("no row of his: no percentage")
    return (d6(diff) / his * 100).quantize(Q2, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------------------------------------- R-T576-2
def readings(conflicts):
    """conflicts: {position: [mark candidates]} -> every combination as a list of {position: mark}; a majority or a
    section-fit pick is refused by construction (all candidates are kept)."""
    out = [{}]
    for p, cands in sorted(conflicts.items()):
        if len(set(cands)) < 2:
            raise Refused(f"{p}: a CONFLICT needs two printed marks")
        out = [dict(r, **{p: c}) for r in out for c in sorted(set(cands))]
    return out


def refuse_majority(support):
    """support: {mark: [sheets]} at one position. Any pick from it is refused (R-T566-1, R-T576-2)."""
    if len(support) > 1:
        raise Refused("two printed marks at one position: CONFLICT, never resolved by a majority of sheets")
    return next(iter(support))


# ---------------------------------------------------------------------------------------------------------- R-T576-3
END_KINDS = ("COLUMN", "CARRIER", "TANGENT", "COLLINEAR_OTHER_MARK", "SAME_MARK")


def allowance(pieces):
    """pieces: [{'piece', 'ends': [{'kind', 'width_m', 'member'}...] or None}] -> (allowance m, missing pieces).
    SAME_MARK / TANGENT / COLLINEAR ends add 0; a held unlabelled piece is never an end of the allowance."""
    tot, missing = Decimal(0), []
    for p in pieces:
        ends = p.get("ends")
        if not ends:
            missing.append(p["piece"])
            continue
        for e in ends:
            if e["kind"] not in END_KINDS:
                raise Refused(f"end kind {e['kind']}")
            if e["kind"] in ("COLUMN", "CARRIER"):
                tot += _pos(e["width_m"], "carrier width")
    return d6(tot), missing


def untraced_test(*, his_minus_engine_m3, b, D, allowance_m, missing, tol_m=Decimal("0.01")):
    """Mark residual (engine valued - his, his longer) against the allowance. Returns (class, through m3, untraced m3)."""
    r = d6(his_minus_engine_m3)
    bd = _pos(b, "b") * _pos(D, "D")
    if r >= 0:
        return "NOT_HIS_LONGER", Decimal(0), r
    y = -r / bd
    if missing:
        return "NOT_DETERMINABLE", None, None
    a = d6(allowance_m) + tol_m
    if y <= a:
        return "THROUGH_SUPPORT", r, Decimal(0)
    through = -d6(a * bd)
    return "BEYOND_ALLOWANCE", through, r - through


# ---------------------------------------------------------------------------------------------------------- R-T576-4
def joint_once(*, column_to, beam_through):
    """column_to: 'SLAB_TOP' (column owns the joint) or 'SOFFIT'; beam_through: True when the beam line runs through
    the column. Exactly one owner is accepted."""
    if column_to not in ("SLAB_TOP", "SOFFIT"):
        raise Refused("column top datum")
    col_owns = column_to == "SLAB_TOP"
    if col_owns == bool(beam_through):
        raise Refused("joint billed twice or nowhere")
    return "COLUMN" if col_owns else "BEAM"
