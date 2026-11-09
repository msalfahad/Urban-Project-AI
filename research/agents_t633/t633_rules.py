"""R-T633-1 (research, unwired; every villa): per-row evidence for a blockwork reconciliation statement.

Physical element: a laid block panel between columns, from the top of the plate under it to the soffit of the member
over it (Q-72 / Q-60 A), net of every actual opening deducted in full (Q-73); lintels, bond beams and the beam band are
not blockwork.

(a) panel_net: net laid area of one panel = clear length x clear height - sum(opening w x h). Refused: an opening that
    lies on the panel but is not deducted (Q-73), a height taken to the slab where a beam is drawn over the panel
    (Q-72: soffit of the member over the wall), a negative net, an opening wider than the panel, missing values
    (never 0).
(b) opening row delta, in wall m2, signed his - engine: a wider / taller opening in his sheet means LESS wall in his
    sheet. Width row: -(w_his - w_own) x h_his; height row: -(h_his - h_own) x w_own; the two rows of one opening sum
    to the identity -(w_his h_his - w_own h_own). Count rows: an opening only the engine deducts -> + w_own h_own; an
    opening only he deducts -> - w_his h_his (only after an own census shows no drawn opening). Outline rows (arched):
    -(w_his h_his - own outline area).
(c) the own value replaces the statement's value; the residual (own - statement) is TOLERANCE when it comes only from
    a drawn width differing from the engine's nominal by <= 5 mm, else it is reported as a finding, never absorbed.
(d) a row's class is kept unless the own evidence contradicts it; a proposal is never made on cited evidence alone
    without saying so (evidence level per row: OWN_DXF, OWN_DXF+CITED, OWNER_RULE, REPRODUCED, CITED).
"""
from __future__ import annotations

from decimal import Decimal

D = Decimal
CLASSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD", "TOLERANCE", "UNRESOLVED")
EVIDENCE = ("OWN_DXF", "OWN_DXF+CITED", "OWNER_RULE", "REPRODUCED", "CITED")
NOMINAL_TOL_M = D("0.005")


class RuleError(ValueError):
    pass


def _need(*vals):
    for v in vals:
        if v is None:
            raise RuleError("missing value: held, never 0")


def _d(v) -> D:
    return v if isinstance(v, D) else D(str(v))


def panel_net(length, floor_level, soffit_beam, soffit_slab, beam_drawn: bool, openings, on_panel_ids=None,
              height_to: str = "member"):
    """(a): returns (net m2, gross m2, deducted m2). openings: [(id, w, h)]; on_panel_ids: ids drawn on the panel."""
    _need(length, floor_level, soffit_slab)
    if beam_drawn:
        _need(soffit_beam)
        if height_to == "slab":
            raise RuleError("height to the slab soffit refused: a beam is drawn over this panel (Q-72)")
        top = _d(soffit_beam)
    else:
        top = _d(soffit_slab)
    L, H = _d(length), top - _d(floor_level)
    if L <= 0 or H <= 0:
        raise RuleError("non-positive panel length or height")
    ids = {o[0] for o in openings}
    for oid in on_panel_ids or ():
        if oid not in ids:
            raise RuleError(f"opening {oid} lies on the panel but is not deducted (Q-73)")
    ded = D(0)
    for oid, w, h in openings:
        _need(w, h)
        w, h = _d(w), _d(h)
        if w <= 0 or h <= 0:
            raise RuleError(f"opening {oid}: non-positive size")
        if w > L:
            raise RuleError(f"opening {oid} wider than the panel")
        if h > H:
            raise RuleError(f"opening {oid} taller than the clear height")
        ded += w * h
    gross = L * H
    net = gross - ded
    if net < 0:
        raise RuleError("negative net area")
    return net, gross, ded


def opening_delta(kind: str, w_his=None, h_his=None, w_own=None, h_own=None, own_area=None, census_has_opening=None):
    """(b): wall-m2 delta his - engine for one statement row."""
    if kind == "width":
        _need(w_his, h_his, w_own)
        return -(_d(w_his) - _d(w_own)) * _d(h_his)
    if kind == "height":
        _need(h_his, h_own, w_own)
        return -(_d(h_his) - _d(h_own)) * _d(w_own)
    if kind == "engine_only":
        _need(w_own, h_own)
        return _d(w_own) * _d(h_own)
    if kind == "his_only":
        _need(w_his, h_his)
        if census_has_opening is not False:
            raise RuleError("his-only opening needs an own census showing no drawn opening")
        return -_d(w_his) * _d(h_his)
    if kind == "outline":
        _need(w_his, h_his, own_area)
        return -(_d(w_his) * _d(h_his) - _d(own_area))
    raise RuleError(f"unknown row kind {kind}")


def residual_class(own: D, stated: D, width_drift_m: D | None, rounding_bound: D | None = None):
    """(c): TOLERANCE only for a nominal-vs-drawn width drift <= 5 mm, or within the stated rounding bound of the
    stored inputs (e.g. 6 dp mean heights x length); else a FINDING."""
    r = own - stated
    if r == 0:
        return r, None
    if width_drift_m is not None and abs(width_drift_m) <= NOMINAL_TOL_M:
        return r, "TOLERANCE"
    if rounding_bound is not None and abs(r) <= rounding_bound:
        return r, "TOLERANCE"
    return r, "FINDING"


def split(rows):
    """signed totals by class and by evidence level; exact (Decimal)."""
    by_c, by_e, tot = {}, {}, D(0)
    for r in rows:
        if r["class"] not in CLASSES:
            raise RuleError(f"bad class {r['class']}")
        if r["evidence"] not in EVIDENCE:
            raise RuleError(f"bad evidence {r['evidence']}")
        v = _d(r["own_delta"])
        by_c[r["class"]] = by_c.get(r["class"], D(0)) + v
        by_e[r["evidence"]] = by_e.get(r["evidence"], D(0)) + v
        tot += v
    return tot, by_c, by_e
