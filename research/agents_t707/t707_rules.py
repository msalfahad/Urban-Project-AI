"""T-707 rules (project-agnostic; scope: every villa whose roof-storey column lines are HELD on an unprinted slab top).
Research only, unwired. Built on R-T689-1 / -2 (t689_rules), R-T682-1 (t682_rules), R-T678-2 (t678_rules) and
R-T669-2 (t669_rules); none of those files is edited.

R-T707-1 1.0.0  ONE TOP PLANE WITH PRINTED THICKNESS ZONES (settles Finding F-T689-1; for slab-TOP bounds only).
    Physical element: the top surface of one cast roof slab. A level mark or a drawn step prints a change of the TOP;
    a thickness text prints a DEPTH. R-T678-2 1.0.0 / R-T682-1 1.0.0 (b) refuse 'one plane' on any thickness text
    inside the outline, while R-T669-2 1.0.0 (ii) REQUIRES a printed thickness: on a plate that prints its thickness
    the two rules contradict each other (F-T689-1). Neither is edited; this rule states what a printed thickness can
    and cannot do to a top-of-slab bound:
    (a) Refused as before (R-T682-1 kept): no outline; a LEVEL or STEP text inside; a section step inside the plane or
        of unstated position; a drawn non-continuous (hidden / dashed) line or a section mark inside the outline.
    (b) Every panel of the plate has a PRINTED thickness: its own panel text, or a printed general note that covers it
        ('all slabs t unless stated'). A panel with neither -> refused (its thickness is never borrowed from another
        panel). Two different values printed in one panel -> refused (CONFLICT).
    (c) The drawing set prints level marks where a level changes (the convention record names them); the absence of a
        level text inside the outline is evidence only with that record. Missing record -> refused.
    Then the only top change the drawings admit between panels i and j is the one their printed thickness difference
    can produce (flush soffit, thicker panel higher; or flush top):  top_j - top_i in [min(0, t_j - t_i),
    max(0, t_j - t_i)]. So from a bound top >= s_lo on a member whose adjacent panels' largest thickness is t_src:
        top_P >= s_lo - max(0, t_src - t_P)          for every panel P of the plate,
    and a column (one joint node, UP-CONC-JOINT-001) takes top >= max over the panels it touches. With one printed
    thickness everywhere this is R-T678-2 exactly; with zones the bound drops by the thickness difference on the
    thinner panels, never by a default. A bound above the printed finished mark is a contradiction: FLAGGED.

R-T707-2 1.0.0  COLUMN FRAMED BY A BEAM WHOSE UP / DOWN-STAND IS OPEN: ONE-SIDED.
    The column's top is the slab top (down-stand) or the beam top (up-stand); both are >= the slab top of the panels
    it touches, so its LOW end is the R-T707-1 / R-T689-1 slab-top bound minus its base, and its HIGH end stays OPEN by
    the designer item (the alternatives' ceilings are named beside, never applied). m3 low = least section reading x
    h_lo (a section CONFLICT keeps both readings; the smaller bounds the low). Class LOWER_ONLY: never 0, never closed,
    never a ceiling invented.

Provenance: T-707 (2026-11-11, worker 1) on F-T689-1 (T-689) and the Lead ruling 2026-11-11 12:25 (a rule conflict is
settled by what the drawings print, then by the rule whose scope fits the element); UP-CONC-JOINT-001, R-CONC-OWN-1,
UP-QTY-STATUS-001, ERS s.2.1 / s.2.3. Scope: every villa (the Alsenan figures are one application).
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

_R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_R / "agents_t689"))
sys.path.insert(0, str(_R / "agents_t682"))
import t682_rules as R82  # noqa: E402
import t689_rules as R89  # noqa: E402

Refused = R89.Refused
q6 = R89.q6
RULE_1, RULE_2 = "R-T707-1 1.0.0", "R-T707-2 1.0.0"
FLAGGED = "FLAGGED"


def N(v, what, lo=Decimal("0"), hi=Decimal("30")):
    """A required number in metres; missing is refused (never 0)."""
    if v is None:
        raise Refused(f"{what}: not printed / not drawn: HELD, never 0")
    if isinstance(v, bool) or not isinstance(v, (int, float, str, Decimal)):
        raise Refused(f"{what}: {v!r} is not a number")
    d = Decimal(str(v))
    if d.is_nan() or d <= lo or d > hi:
        raise Refused(f"{what} {v}: outside ({lo}, {hi}] m (a value in cm / mm is refused)")
    return d


# ---------------------------------------------------------------------------------------------------- R-T707-1
def check_plate(plate):
    """plate: {outline, plan_texts_inside: [{kind, text}], section_steps: [...] (R-T682-1), noncontinuous_inside: int,
    section_marks_inside: int, panels: {id: {thickness_texts_m: [..], general_note_m: t | None}},
    level_convention: [evidence, ...]} -> {state: ONE_TOP_PLANE, t: {panel: t}} or Refused."""
    if not isinstance(plate, dict) or not plate.get("outline"):
        raise Refused("R-T707-1: the plate is stated as a record with its outline")
    for t in plate.get("plan_texts_inside") or ():
        if t.get("kind") in ("LEVEL", "STEP"):
            raise Refused(f"R-T707-1: plan text {t.get('text')!r} ({t['kind']}) inside the outline: two planes")
        if t.get("kind") != "THICKNESS":
            raise Refused(f"R-T707-1: plan text kind {t.get('kind')!r} not classified")
    if plate.get("noncontinuous_inside") or plate.get("section_marks_inside"):
        raise Refused("R-T707-1: a hidden / dashed line or a section mark inside the outline: a step is not excluded")
    # R-T682-1 (b) / (c) for the section steps, with the thickness texts handled here (not as 'two planes')
    sec = R82.check_plane({"outline": plate["outline"], "plan_texts_inside": [],
                           "section_steps": plate.get("section_steps") or ()})
    if not plate.get("level_convention"):
        raise Refused("R-T707-1: no record that the set prints level changes: absence of a level text proves nothing")
    panels = plate.get("panels") or {}
    if not panels:
        raise Refused("R-T707-1: no panels stated")
    t = {}
    for pid, p in panels.items():
        own = sorted({N(v, f"{pid} printed thickness", hi=Decimal("1.0")) for v in p.get("thickness_texts_m") or ()})
        if len(own) > 1:
            raise Refused(f"R-T707-1: panel {pid} prints two thicknesses {own}: CONFLICT")
        if own:
            t[pid] = own[0]
        elif p.get("general_note_m") is not None:
            t[pid] = N(p["general_note_m"], f"{pid} general-note thickness", hi=Decimal("1.0"))
        else:
            raise Refused(f"R-T707-1: panel {pid} has no printed thickness (no panel text, no general note): "
                          f"never borrowed from another panel")
    return {"state": "ONE_TOP_PLANE", "t": t, "sections": sec, "rule": RULE_1}


def panel_top_lo(*, s_lo, source_panels, plate_rec, panel):
    """top_P >= s_lo - max(0, t_src - t_P), t_src = the largest thickness among the source member's panels."""
    t = plate_rec["t"]
    if not source_panels or any(p not in t for p in source_panels):
        raise Refused("R-T707-1: the source member's adjacent panels are not all stated in the plate")
    if panel not in t:
        raise Refused(f"R-T707-1: panel {panel} not in the plate")
    t_src = max(t[p] for p in source_panels)
    return q6(N(s_lo, "slab-top bound") - max(Decimal(0), t_src - t[panel]))


def column_top_lo(*, s_lo, source_panels, plate_rec, touched, finished_mark=None):
    """A column touches panels `touched`; its top (one node) >= the largest of their bounds."""
    if not touched:
        raise Refused("R-T707-1: the column touches no panel of the plate: no transfer")
    tops = {p: panel_top_lo(s_lo=s_lo, source_panels=source_panels, plate_rec=plate_rec, panel=p) for p in touched}
    gov = max(tops, key=lambda p: (tops[p], p))
    top = tops[gov]
    if finished_mark is not None and top > N(finished_mark, "finished mark"):
        return {"state": FLAGGED, "top_lo": top, "why": "bound above the printed finished mark: contradiction"}
    return {"state": "BOUNDED", "top_lo": top, "governing_panel": gov, "panel_tops": tops, "rule": RULE_1}


def column_height_lo(*, top_lo, base, offset=Decimal(0)):
    """h_lo = top_lo - offset - base (offset: a printed support depth under a planted column, else 0)."""
    h = N(top_lo, "top") - Decimal(str(offset)) - N(base, "base")
    if h <= 0:
        raise Refused("non-positive column height")
    return q6(h)


# ---------------------------------------------------------------------------------------------------- R-T707-2
def one_sided_low(*, areas, h_lo, item, alternatives=None):
    """R-T707-2: LOWER_ONLY m3 = least section reading x h_lo; the high end OPEN by the named item."""
    if not item:
        raise Refused("R-T707-2: the open end names its designer item")
    if not areas or any(a is None for a in areas):
        raise Refused("R-T707-2: a section reading is missing: the line stays blank, HELD by name")
    a = min(N(x, "section area", hi=Decimal("5")) for x in areas)
    low = q6(a * N(h_lo, "h_lo"))
    return {"state": "HELD", "class": "LOWER_ONLY", "low": low, "high": None, "item": item,
            "alternatives_beside_not_applied": alternatives or {}, "rule": RULE_2}


def formwork_sides(*, perimeters, h, t, method="UP-FW-001 draft (struct_n10): perimeter x (height - slab t)"):
    """Column side forms under the engine's method (UPPER_BOUND by construction, FW-D3: framing beams' faces not
    deducted). perimeters: (min, max) readings; h: (lo, hi | None); t: (t_min, t_max) of the touched panels.
    Low = P_min x (h_lo - t_max); high = P_max x (h_hi - t_min) or OPEN. Stays HELD with the column."""
    pmin, pmax = (N(p, "perimeter", hi=Decimal("20")) for p in perimeters)
    tmin, tmax = (N(x, "slab t", hi=Decimal("1.0")) for x in t)
    lo = q6(pmin * (N(h[0], "h_lo") - tmax))
    hi = None if h[1] is None else q6(pmax * (N(h[1], "h_hi") - tmin))
    if lo <= 0 or (hi is not None and hi < lo):
        raise Refused("formwork: non-positive face or low above high")
    return {"state": "HELD", "basis": "UPPER_BOUND method (FW-D3)", "low_m2": lo, "high_m2": hi, "method": method}
