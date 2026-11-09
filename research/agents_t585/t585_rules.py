"""T-585 rules (any villa; research, unwired): OUTDOOR / YARD skirting classed face by face, STAIR-FLIGHT skirting
restated along the pitch per wall side, and stair PIECES kept in nr.

R-T585-1 (proposed, every villa; provenance T-585; builds on UP-SKIRT-001 1.4.0 (skirting where it is built, along real
wall faces at floor level; scope dry rooms with a tiled floor; floor glazing not skirted; an unknown sill is a range
[0, L]), R-T574-1 (classes with their own units, pieces never converted), OWNER_RULE_OUTDOOR_FLOORS_2026-10-21 (court
interlock, side walk / sides porcelain; porch and pool deck HELD, OD-1), Q-73 (every actual opening deducted),
ENGINEERING_REASONING_STANDARD s.2-4 (no assumption; unresolved stays HELD, never 0)):
  (a) PHYSICAL ELEMENT. An outdoor skirting is a base strip at the foot of a wall face where a FINISHED outdoor floor
      meets that face. It exists only where (1) the floor's finish is established (printed, or an owner rule) and
      (2) the drawings show a base: a printed note, a base detail or a drawn base band. A face is described by its host:
        FENCE        plot face of a boundary wall
        WALL         house wall or flush column face
        SILL_WINDOW  wall below a window whose sill is not printed: range [0, L] (UP-SKIRT-001 1.4.0)
        DOOR, GATE, OPEN_EDGE, FLOOR_GLAZING   no wall foot: never skirted (0 by geometry, not HELD)
        UNDRAWN      no face line drawn on that stretch: UNRESOLVED, bound [0, L]
  (b) CLASSES of a face with a wall foot:
        DRAWING-CONFIRMED  finish established AND a printed base note / detail: measured = L (a SILL_WINDOW keeps its
                           range)
        NOT_IN_DRAWING     finish established, no base printed or drawn anywhere: measured 0 lm, the physical
                           wall-foot length named beside it (a reference's extra is RULE_DIFFERENCE / FREELANCER_SCOPE,
                           never an engine omission)
        UNRESOLVED         the floor finish itself is HELD by an open owner / designer item: HELD, bound [0, L],
                           never 0 and never a number in a sum
      A face whose floor has NO finish (none printed, no owner rule, none held) carries no skirting class at all:
      counting it is refused. A wall-less host listed as skirted is refused.
  (c) STAIR FLIGHT. Skirting along a flight's wall side follows the stringer: PITCH = hypot(plan going along that side,
      rise of that side), developed per piece; the zigzag form (goings + rises) is a different payable form, kept
      beside, never added (ORR-007 decides which line is paid). One line per WALL side: both sides only where both are
      walls; an open side has no face. A piece whose side length or rise is not established is bounded:
        winder corner with total rise h over wall-side plans L1, L2 and the split unknown: L1 + L2 <= pitch <=
        max(hypot(L1, h) + L2, L1 + hypot(L2, h)) (the pitch sum is convex in the split, so its maximum is at an end);
        a face with an opening of unprinted height: [0, pitch]; no wall drawn: [0, pitch] when the rise is known.
  (d) PIECES. A per-step count is nr; it becomes lm only with a printed piece length (refused otherwise).
  (e) STATUS. VERIFIED is the Checker's word and is refused here; a HELD amount is never summed as a number.
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

HOSTS_WALL = ("FENCE", "WALL", "SILL_WINDOW")
HOSTS_NONE = ("DOOR", "GATE", "OPEN_EDGE", "FLOOR_GLAZING")
HOSTS = HOSTS_WALL + HOSTS_NONE + ("UNDRAWN",)
FINISH = ("ESTABLISHED", "HELD", "NONE")
CLASSES = ("DRAWING-CONFIRMED", "NOT_IN_DRAWING", "UNRESOLVED", "NO_FACE")
LEN_UNITS = {"m": Decimal(1), "mm": Decimal("0.001")}
Q6 = Decimal("0.000001")


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("quantity unknown (None) used as a number: HELD / UNKNOWN is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def L(x, unit="m") -> Decimal:
    if unit not in LEN_UNITS:
        raise RuleError(f"length unit {unit!r} unknown (m or mm only)")
    v = D(x) * LEN_UNITS[unit]
    if v < 0:
        raise RuleError("a length is never negative")
    return v


# ---- (a) / (b) yard faces --------------------------------------------------------------------------------------------
def classify_face(face, unit="m"):
    """face: {id, length, host, finish (ESTABLISHED / HELD / NONE), base_note (sheet ref or None), claimed (optional
    class someone asserts)}. Returns {id, host, length, class, measured, lo, hi, note}."""
    for k in ("id", "length", "host", "finish"):
        if k not in face:
            raise RuleError(f"face {face.get('id')!r}: {k} missing")
    host, fin = face["host"], face["finish"]
    if host not in HOSTS:
        raise RuleError(f"face {face['id']}: host {host!r} unknown")
    if fin not in FINISH:
        raise RuleError(f"face {face['id']}: finish {fin!r} unknown")
    ln = L(face["length"], unit)
    note = face.get("base_note")
    claimed = face.get("claimed")
    if claimed == "VERIFIED":
        raise RuleError("VERIFIED is the Checker's word, refused in research")
    out = {"id": face["id"], "host": host, "length": ln}
    if host in HOSTS_NONE:
        if claimed in ("DRAWING-CONFIRMED", "UNRESOLVED"):
            raise RuleError(f"face {face['id']}: a {host} has no wall foot and is never skirted")
        out.update({"class": "NO_FACE", "measured": Decimal(0), "lo": Decimal(0), "hi": Decimal(0)})
        return out
    if fin == "NONE":
        raise RuleError(f"face {face['id']}: no finished floor (none printed, no owner rule, none held) meets this "
                        "face: a yard skirting is refused here")
    if fin == "HELD" or host == "UNDRAWN":
        if claimed == "DRAWING-CONFIRMED":
            raise RuleError(f"face {face['id']}: floor finish HELD / face undrawn cannot be DRAWING-CONFIRMED")
        out.update({"class": "UNRESOLVED", "measured": None, "lo": Decimal(0), "hi": ln})
        return out
    if note:
        if host == "SILL_WINDOW":
            out.update({"class": "DRAWING-CONFIRMED", "measured": None, "lo": Decimal(0), "hi": ln,
                        "note": "sill not printed: range [0, L]"})
        else:
            out.update({"class": "DRAWING-CONFIRMED", "measured": ln, "lo": ln, "hi": ln})
        out["base_note"] = note
        return out
    if claimed == "DRAWING-CONFIRMED":
        raise RuleError(f"face {face['id']}: no base printed or drawn: DRAWING-CONFIRMED refused")
    out.update({"class": "NOT_IN_DRAWING", "measured": Decimal(0), "lo": Decimal(0), "hi": Decimal(0),
                "physical": ln})
    return out


def yard_totals(faces, unit="m"):
    """Totals per class in lm. NOT_IN_DRAWING carries its physical wall-foot length beside (never a quantity);
    UNRESOLVED carries only its bound. Face ids are used once."""
    seen = set()
    rows = []
    for f in faces:
        if f["id"] in seen:
            raise RuleError(f"face {f['id']} listed twice")
        seen.add(f["id"])
        rows.append(classify_face(f, unit))
    tot = {c: {"faces": 0, "length": Decimal(0)} for c in CLASSES}
    dc_measured = Decimal(0)
    dc_range_hi = Decimal(0)
    unres_hi = Decimal(0)
    nid_phys = Decimal(0)
    for r in rows:
        t = tot[r["class"]]
        t["faces"] += 1
        t["length"] += r["length"]
        if r["class"] == "DRAWING-CONFIRMED":
            if r["measured"] is None:
                dc_range_hi += r["hi"]
            else:
                dc_measured += r["measured"]
        elif r["class"] == "UNRESOLVED":
            unres_hi += r["hi"]
        elif r["class"] == "NOT_IN_DRAWING":
            nid_phys += r["physical"]
    return {"rows": rows, "by_class": tot, "drawing_confirmed_lm": dc_measured,
            "drawing_confirmed_sill_range_hi": dc_range_hi, "not_in_drawing_physical_lm": nid_phys,
            "unresolved_bound": (Decimal(0), unres_hi),
            "perimeter_lm": sum((r["length"] for r in rows), Decimal(0))}


# ---- (c) stair flights -----------------------------------------------------------------------------------------------
def _q(x) -> Decimal:
    return D(x).quantize(Q6)


def pitch(plan, rise, unit="m") -> Decimal:
    """Developed length along the stringer of ONE wall side: hypot(plan going, rise)."""
    p, r = L(plan, unit), L(rise, unit)
    if p == 0:
        raise RuleError("a flight side has a plan going > 0")
    return D(math.hypot(float(p), float(r)))


def zigzag(plan, rise, unit="m") -> Decimal:
    return L(plan, unit) + L(rise, unit)


def flight_sides(plan, rise, sides, unit="m"):
    """sides: tuple of 'WALL' / 'OPEN' per side (one or two). Returns per-side pitch lines (WALL only)."""
    if not sides or len(sides) > 2:
        raise RuleError("a flight has one or two sides")
    out = []
    for i, s in enumerate(sides):
        if s not in ("WALL", "OPEN"):
            raise RuleError(f"side {s!r} unknown")
        if s == "WALL":
            out.append({"side": i, "pitch": pitch(plan, rise, unit), "zigzag": zigzag(plan, rise, unit)})
    return out


def winder_bound(plan1, plan2, total_rise, unit="m"):
    """Two wall sides of a winder corner sharing total_rise with an unknown split: (lo, hi) of the pitch sum."""
    a, b, h = L(plan1, unit), L(plan2, unit), L(total_rise, unit)
    lo = a + b
    hi = max(pitch(a, h) + b, a + pitch(b, h))
    return lo, hi


def flight_line(piece):
    """piece: {pid, status (HELD-FORM / HELD / CONFLICT / UNKNOWN / DRAWING-CONFIRMED), pitch, zigzag, cause}.
    HELD-FORM: both forms measured; the payable form is ORR-007's (two-valued, never averaged, never added).
    HELD / CONFLICT: [0, pitch]; UNKNOWN with no pitch: unbounded (hi None)."""
    st = piece["status"]
    if st == "VERIFIED":
        raise RuleError("VERIFIED is the Checker's word, refused in research")
    pz = piece.get("pitch")
    zz = piece.get("zigzag")
    if st == "HELD-FORM":
        if pz is None or zz is None:
            raise RuleError(f"{piece['pid']}: HELD-FORM needs both forms measured")
        p, z = D(pz), D(zz)
        if p > z:
            raise RuleError(f"{piece['pid']}: a pitch never exceeds its zigzag")
        return {"pid": piece["pid"], "class": "MEASURED_TWO_FORMS", "pitch": p, "zigzag": z, "lo": p, "hi": z}
    if st in ("HELD", "CONFLICT", "UNKNOWN"):
        if pz is None:
            return {"pid": piece["pid"], "class": st, "lo": piece.get("lo", Decimal(0)), "hi": piece.get("hi"),
                    "cause": piece.get("cause")}
        return {"pid": piece["pid"], "class": st, "lo": D(piece.get("lo", 0)), "hi": D(pz),
                "cause": piece.get("cause")}
    raise RuleError(f"{piece['pid']}: status {st!r} unknown for a flight piece")


def flights_total(pieces):
    rows = [flight_line(p) for p in pieces]
    two = [r for r in rows if r["class"] == "MEASURED_TWO_FORMS"]
    pitch_sum = sum((r["pitch"] for r in two), Decimal(0))
    zig_sum = sum((r["zigzag"] for r in two), Decimal(0))
    lo = pitch_sum + sum((D(r["lo"]) for r in rows if r["class"] != "MEASURED_TWO_FORMS"), Decimal(0))
    his = [r["hi"] for r in rows if r["class"] != "MEASURED_TWO_FORMS"]
    hi = None if any(h is None for h in his) else zig_sum + sum((D(h) for h in his), Decimal(0))
    return {"rows": rows, "two_form_pieces": len(two), "pitch_lm": pitch_sum, "zigzag_lm": zig_sum,
            "lo": lo, "hi": hi}


# ---- (d) pieces ------------------------------------------------------------------------------------------------------
def pieces_to_lm(nr, printed_piece_length=None, unit="m"):
    if printed_piece_length is None:
        raise RuleError("pieces (nr) are converted to lm only with a printed piece length")
    n = D(nr)
    if n != n.to_integral_value() or n < 0:
        raise RuleError("a piece count is a whole number")
    return n * L(printed_piece_length, unit)


in_prec40(globals())   # T-653: every function of this module runs in a local 40-digit context
