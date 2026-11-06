"""T-545 rules (research, unwired): B10-07 beam concrete reconciled against a freelancer by COMPONENT, for any villa.

R-T545-1 COMPONENT TABLE. engine valued - his rows = sum of named components, exactly (Decimal, 6 dp). Components are
    COUNT (engine marks with no row of his), RUN_COUNT (drawn runs beyond his rows), UPSTAND (drawn upstand lines with
    no row), DOME_RING (a drawn ring beam with no row on his beam or dome sheet; T-398: ring and shell never meet),
    THROUGH_SUPPORT (his length through the support footprint the engine leaves to the support), SCOPE (a solid he
    books in another family), HELD (engine blank, his rows at his section on the held runs), SECTION (b x D differs
    on a common mark), UNTRACED. A component given as a ratio / percentage, a HELD component closed as 0 when his rows carry it, or a table
    that does not re-add to the residual is refused.
R-T545-2 OVERLAP ONCE. Beam / slab: FULL depth with the slab NET of the beam plan, or DOWNSTAND (D - t) with the slab
    GROSS; any other pairing bills b x L x t twice or nowhere (R-T395-1). Beam / column: the joint b x c x D is owned by
    one element id; an element id billed by two lines is refused.
R-T545-3 HELD BOUND BESIDE HIS ROW. For each held run his share (his b x D x drawn length) is printed beside the engine
    bound [low, high] and classed INSIDE / BELOW / ABOVE / UNBOUNDED; the class is information for the Checker, never a
    reason to release, raise or lower the engine figure (no 'closer to the freelancer').

Provenance: T-545 (2026-11-06), building on R-T395-1 .. 5 (T-395, merged) and R-CONC-OWN-1. Scope: every villa.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

Q6 = Decimal("0.000001")
COMPONENTS = ("COUNT", "RUN_COUNT", "UPSTAND", "DOME_RING", "THROUGH_SUPPORT", "SCOPE", "HELD", "SECTION",
              "UNTRACED")
VERDICT = {"COUNT": "ENGINE_RIGHT", "RUN_COUNT": "ENGINE_RIGHT", "UPSTAND": "ENGINE_RIGHT", "DOME_RING": "ENGINE_RIGHT",
           "THROUGH_SUPPORT": "RULE_DIFFERENCE", "SCOPE": "SCOPE", "HELD": "HELD", "SECTION": "UNRESOLVED",
           "UNTRACED": "UNRESOLVED"}


class Refused(ValueError):
    """A reading the rules refuse."""


def d6(x) -> Decimal:
    if isinstance(x, str) and x.strip().endswith("%"):
        raise Refused("a component given as a percentage is not a quantity")
    if x is None:
        raise Refused("missing value: carry it HELD, never 0")
    return Decimal(str(x)).quantize(Q6, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------------------------------------- R-T545-1
def component_table(engine_m3, his_m3, components: dict, *, held_his_share=None) -> dict:
    """components: name -> m3 (engine - his). Returns the table with the residual; refuses an open sum."""
    E, F = d6(engine_m3), d6(his_m3)
    out = {}
    for k, v in components.items():
        if k not in COMPONENTS:
            raise Refused(f"unknown component {k}")
        out[k] = d6(v)
    if held_his_share is not None and d6(held_his_share) != 0 and out.get("HELD", Decimal(0)) == 0:
        raise Refused("his rows carry the held runs: the HELD component cannot be closed as 0")
    res = E - F
    s = sum(out.values(), Decimal(0))
    if s != res:
        raise Refused(f"components {s} do not re-add to the residual {res}")
    return {"engine_m3": str(E), "his_m3": str(F), "residual_m3": str(res),
            "components": {k: {"m3": str(v), "verdict": VERDICT[k]} for k, v in out.items()}}


# ---------------------------------------------------------------------------------------------------------- R-T545-2
def beam_slab_volumes(*, b, L, D, t, slab_area_gross, depth_basis, slab_basis):
    """One beam under one slab: returns (beam m3, slab m3, total). Mixed pairings refused (R-T395-1)."""
    b, L, D, t, A = (Decimal(str(v)) for v in (b, L, D, t, slab_area_gross))
    if min(b, L, D, t, A) <= 0:
        raise Refused("non-positive dimension")
    if max(b, D, t) > 5 or L > 100:
        raise Refused("dimension looks like mm: give metres")
    if D <= t:
        raise Refused("beam depth not greater than slab thickness")
    pair = (depth_basis, slab_basis)
    if pair == ("FULL", "NET"):
        beam, slab = b * L * D, (A - b * L) * t
    elif pair == ("DOWNSTAND", "GROSS"):
        beam, slab = b * L * (D - t), A * t
    elif pair == ("FULL", "GROSS"):
        raise Refused("FULL depth with a GROSS slab bills b x L x t twice")
    elif pair == ("DOWNSTAND", "NET"):
        raise Refused("DOWNSTAND with a NET slab bills b x L x t nowhere")
    else:
        raise Refused(f"unknown basis {pair}")
    return beam, slab, beam + slab


def joints_once(lines: list[dict]) -> dict:
    """lines = [{'line_id', 'owns': [element ids]}]: every owned element id (beam piece, column joint) in ONE line."""
    seen: dict[str, str] = {}
    for ln in lines:
        for e in ln["owns"]:
            if e in seen and seen[e] != ln["line_id"]:
                raise Refused(f"element {e} billed by {seen[e]} and {ln['line_id']}")
            seen[e] = ln["line_id"]
    return {"elements": len(seen), "lines": len(lines)}


def beam_between_columns(*, b, D, L_f2f, col_along, col_across, col_height_to_soffit, t, slab_area_gross):
    """Hand fixture helper: one beam between two equal columns under one slab, both length conventions.

    ENGINE (R-CONC-OWN-1 + T-394): beam face to face, columns own the joint to the slab top, slab NET of beam and column
    heads. THROUGH (his reading): beam over the column footprint (L + 2 x along), columns stop at the beam soffit.
    The physical solid is the same; both totals must be equal (else the joint is billed twice or nowhere)."""
    b, D, L, ca, cx, h, t, A = (Decimal(str(v)) for v in (b, D, L_f2f, col_along, col_across, col_height_to_soffit,
                                                            t, slab_area_gross))
    if min(b, D, L, ca, cx, h, t, A) <= 0:
        raise Refused("non-positive or missing dimension")
    if max(b, D, ca, cx, t) > 5:
        raise Refused("dimension looks like mm: give metres")
    slab_net = (A - b * L - 2 * ca * cx) * t
    eng = {"beam": b * L * D, "columns": 2 * ca * cx * (h + D), "slab": slab_net}
    # his: the beam runs through the column footprint; b == cx here so the joint solid is b x ca x D
    if b != cx:
        raise Refused("fixture needs the beam width equal to the column side across it")
    thr = {"beam": b * (L + 2 * ca) * D, "columns": 2 * ca * cx * h, "slab": slab_net}
    te, tt = sum(eng.values()), sum(thr.values())
    if te != tt:
        raise Refused(f"conventions disagree on the physical solid: {te} vs {tt}")
    return {"engine": eng, "through": thr, "total": te, "beam_difference": eng["beam"] - thr["beam"]}


# ---------------------------------------------------------------------------------------------------------- R-T545-3
def held_bound_class(his_share, low, high) -> str:
    if low is None or high is None:
        return "UNBOUNDED"
    s, lo, hi = d6(his_share), d6(low), d6(high)
    if lo > hi:
        raise Refused("held bound low > high")
    if s < lo:
        return "BELOW"
    if s > hi:
        return "ABOVE"
    return "INSIDE"


def held_value(v):
    if v is not None and Decimal(str(v)) == 0:
        raise Refused("a HELD quantity stays blank: 0 is refused")
    return v
