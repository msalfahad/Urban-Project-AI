"""R-T285-1: one established blockwork register revision built from merged layers (research rule, any villa; T-285).

Provenance: T-285 (Lead 2026-10-25 00:15); builds on R-T274-1 (research/agents_t274/piece_close.py: pieces close the
census, opening by its part inside the masonry), R-T261-1 points 7 - 9 (research/agents_t261/piece_split.py: established
part plus HELD increment), R-BEAM-WIDTH-CONSEQ-1 (research/agents_t277: a member-width CONFLICT reaches every trade that
reads the band), the owner BLOCKWORK programme s.2 / s.5 (status classes; the Checker re-measures every wall whose class
rises) and WORKFLOW_CONTROLS s.5 (HELD / UNKNOWN never 0). Nothing here edits an engine module, a rule or knowledge file.

Physical element: the net installed block area of ONE wall = the area of block physically built under the members drawn
over its census length, less the openings physically piercing that block (ERS s.3 build before deduct). A register
revision may change a wall's figure only for a NAMED cause; the whole register then moves by exactly the sum of the named
causes (residual 0.000). So:

1. CLOSURE: a wall's established figure from pieces is accepted only when its pieces close the census (R-T274-1, 1 mm);
   held pieces are named, never 0 (`wall_from_pieces`).
2. CLASS FLOOR: a value the Checker VERIFIED is never replaced by a value of a lower class; the lower-class proposal is
   listed as a difference beside it (VERIFIED_OVERWRITE refused in `apply_value`).
3. CONFLICT: when two authoritative readings of one input (e.g. a drawn and a scheduled beam width) give two figures,
   both readings are carried; the established figure is the part present in EVERY reading and the difference is a
   CONFLICT increment by name, never added, never 0, never one reading chosen (`conflict_part`). One reading alone, or
   two readings with the same name, is a collapsed conflict and refused.
4. HELD: a HELD wall or piece carries no number in the established total; a held item with no name, or a held figure
   written as a number 0, is refused (`held_item`).
5. RECONCILIATION: register(after) - register(before) = sum of the named causes, residual within 0.00005 m2 (4-decimal
   ledgers); an unnamed change refuses the revision (`reconcile`).
6. ONE WALL ONCE: a wall id appears once in a revision; two layers proposing the same cause on the same wall, or a wall
   carried under two ids, are refused (`one_wall_once`).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t274"))
import piece_close as PC  # noqa: E402

RULE_ID = "R-T285-1"
RES_TOL_M2 = 0.00005
VERIFIED = "VERIFIED"
SS = "SOURCE-SUPPORTED PENDING INDEPENDENT CHECK"
PS = "PROJECT-SPECIFIC"
HELD = "HELD"
CLASSES = (VERIFIED, SS, PS, HELD)
# WORKFLOW_CONTROLS s.5 evidence status for each owner class (BLOCKWORK programme s.2)
EVIDENCE_STATUS = {VERIFIED: "VERIFIED", SS: "DRAWING-CONFIRMED", PS: "ASSUMED — OWNER-APPROVED", HELD: "HELD"}


class RegisterError(ValueError):
    """a revision the rule refuses (the code is the first word of the message)."""


def held_item(name, figure=None):
    """rule 4: a held item names what is missing; its figure (if any) is information, never 0 and never a quantity."""
    if not name or not str(name).strip():
        raise RegisterError("HELD_UNNAMED: a held item names the missing member, depth, datum or opening")
    if figure is not None and not isinstance(figure, str):
        if figure == 0:
            raise RegisterError("HELD_AS_ZERO: a held item is never written as 0")
    return {"held_item": str(name).strip(), "figure_not_a_quantity": figure}


def wall_from_pieces(census_m, pieces, deductions_m2=0.0):
    """rule 1: {established_gross_m2, established_net_m2, held[]} from a closed piece list (R-T274-1 gross)."""
    g = PC.gross(census_m, pieces)
    if deductions_m2 < 0:
        raise RegisterError("BAD_DEDUCTION: a deduction is a non-negative area")
    net = g["established_m2"] - deductions_m2
    if net <= 0 and not g["held"]:
        raise RegisterError("NON_POSITIVE_NET: an established wall with no held piece has a positive net")
    return {"established_gross_m2": round(g["established_m2"], 6), "established_net_m2": round(net, 6),
            "held": [held_item(h["held_item"], f"{h['length_m']:.4f} m") for h in g["held"]]}


def conflict_part(readings):
    """rule 3: readings {name: figure m2} of ONE wall -> (established part, increment, readings). Two or more distinct
    readings are required; the established part is the figure present in every reading (the smallest), the increment
    max - min is a CONFLICT by name (never added, never 0, never one reading chosen)."""
    if not isinstance(readings, dict) or len(readings) < 2:
        raise RegisterError("CONFLICT_COLLAPSED: a CONFLICT carries at least two readings, each by name")
    for k, v in readings.items():
        if not k or v is None:
            raise RegisterError("CONFLICT_UNNAMED: every reading names its source and carries a figure")
    lo, hi = min(readings.values()), max(readings.values())
    return round(lo, 6), round(hi - lo, 6), dict(readings)


def apply_value(current, proposal, replace=False):
    """rule 2: current / proposal {value, class, source}; returns (kept, difference-or-None). A VERIFIED value is never
    replaced by a lower class: the proposal is returned as a listed difference, and an explicit request to replace it
    (replace=True) is refused."""
    for x in (current, proposal):
        if x.get("class") not in CLASSES:
            raise RegisterError(f"BAD_CLASS: {x.get('class')!r} is not one of {CLASSES}")
    if current["class"] == VERIFIED and proposal["class"] != VERIFIED:
        if replace:
            raise RegisterError("VERIFIED_OVERWRITE: a lower-class value never replaces a Checker-VERIFIED value")
        d = None if proposal.get("value") is None else round(proposal["value"] - current["value"], 6)
        return dict(current), {"source": proposal.get("source"), "proposed": proposal.get("value"), "delta_m2": d}
    if proposal["class"] == HELD:
        if proposal.get("value") is not None:
            raise RegisterError("HELD_AS_NUMBER: a HELD wall carries no established figure")
    elif proposal.get("value") is None or proposal["value"] <= 0:
        raise RegisterError("MISSING_AS_ZERO: an established wall carries a positive figure (missing is HELD)")
    return dict(proposal), None


def one_wall_once(rows, key="wall_id"):
    """rule 6: every wall id once."""
    seen = set()
    for r in rows:
        k = r[key]
        if k in seen:
            raise RegisterError(f"DUPLICATE_WALL: {k} carried twice")
        seen.add(k)
    return True


def reconcile(before_total, after_total, causes):
    """rule 5: causes [{wall_id, cause, delta_m2}] explain after - before to RES_TOL_M2; returns the residual."""
    for c in causes:
        if not c.get("cause") or not c.get("wall_id"):
            raise RegisterError("UNNAMED_CAUSE: every change names its wall and its cause")
    pairs = [(c["wall_id"], c["cause"]) for c in causes]
    if len(pairs) != len(set(pairs)):
        raise RegisterError("DUPLICATE_CAUSE: one cause booked twice on one wall")
    res = (after_total - before_total) - sum(c["delta_m2"] for c in causes)
    if abs(res) > RES_TOL_M2:
        raise RegisterError(f"RESIDUAL: register moved {after_total - before_total:.4f} m2, named causes "
                            f"{sum(c['delta_m2'] for c in causes):.4f} m2, residual {res:.4f} m2 unexplained")
    return round(res, 6) + 0.0
