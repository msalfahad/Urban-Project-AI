"""COLUMN_LINE_V1: whole-line closure of CONC.COLUMN (columns + necks), every member once (T-248; any villa).

Pure rules (stdlib only, unwired; no engine module imports it). Proposed rule R-COLUMN-LINE-1 (provenance T-248; a new
rule version when adopted), built on R-CONC-OWN-1 (column > beam > slab), R-NECK-ENDS-1 (T-205), R-SECTION-CONFLICT-1
(T-217), the T-230 end rule (a member ends only at what it meets in 3-D) and the C1 convention stated by T-234 / T-241
(slab panel between beam faces; beam full depth; column footprints belong to the column line).

THE PHYSICAL ELEMENT. One column member on one storey (or one neck under it) is the concrete solid inside its own
footprint between two STRUCTURAL datums:
  * base: the top of what it stands on: the footing top (neck), the neck / ground-beam top where the column line starts
    (ground-floor column), the slab / beam top of the storey below (upper column, planted column on its beam);
  * top: the slab top of the slab it carries, because under C1 every slab panel stops at the column face and every beam
    run framing into it is billed to the column face (NET); where a beam is billed THROUGH the footprint the beam owns
    that piece and the column stops at the beam soffit.
The owner's Urban method URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 (column = interval - D_ctrl) with
URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1 (joint = A x (D_ctrl - t), head A x t in the plate) splits the SAME solid into
three lines; it is carried beside (`owner_split`), never instead, and its holds (D_ctrl of a held member) do not hold
the solid.

Statuses (WORKFLOW_CONTROLS s.5): DRAWING-CONFIRMED (one section, both datums printed / drawing-confirmed), CONFLICT
(two printed / drawn sections, both datums confirmed: a range, both ends named, never collapsed), HELD (a datum or a
footing depth not printed: a bound where the physics gives one, otherwise no value, never 0), UNKNOWN (existence not
established: a line the drawing does not draw; no value). Release is never decided here (NOT RELEASED).
"""
from __future__ import annotations

from dataclasses import dataclass, field

METHOD = "COLUMN_LINE_V1"
RULE = "R-COLUMN-LINE-1 (proposed, T-248)"
UNITS = {"m": 1.0, "cm": 0.01, "mm": 0.001}

# datum kinds
STRUCTURAL = "STRUCTURAL"      # a structural surface (slab top, beam top / soffit, footing top, neck top)
FINISHED = "FINISHED"          # an architect's finished level (FFL, finished roof): never a concrete end
LIMIT = "LIMIT"                # a printed limit (minimum excavation, minimum founding depth): only a bound


class Refused(ValueError):
    """A rule of R-COLUMN-LINE-1 refuses the input (the reason is the message)."""


@dataclass(frozen=True)
class Level:
    """A structural datum as an interval in metres. lo == hi: one value; None: unbounded on that side."""
    lo: float | None
    hi: float | None
    status: str = "DRAWING-CONFIRMED"   # or HELD
    source: str = ""
    kind: str = STRUCTURAL
    causes: tuple = ()

    def __post_init__(self):
        if self.kind == FINISHED:
            raise Refused(f"FINISHED_AS_STRUCTURAL: {self.source or 'a finished level'} is never a concrete end")
        if not self.source:
            raise Refused("DEFAULT_DATUM: a datum without a drawing source is a default, never a level")
        if self.kind == LIMIT and self.lo is not None and self.hi is not None and self.lo == self.hi:
            raise Refused("LIMIT_AS_LENGTH: a printed limit is a bound, never a member end")
        if self.status == "DRAWING-CONFIRMED" and (self.lo is None or self.hi is None or abs(self.lo - self.hi) > 1e-9):
            raise Refused("a DRAWING-CONFIRMED datum has one value")
        if self.lo is not None and self.hi is not None and self.lo > self.hi + 1e-9:
            raise Refused("datum interval reversed")

    @staticmethod
    def at(v, source, unit="m"):
        x = round(v * UNITS[unit], 6)
        return Level(x, x, "DRAWING-CONFIRMED", source)

    @staticmethod
    def held(lo, hi, source, causes, unit="m", kind=STRUCTURAL):
        f = UNITS[unit]
        return Level(None if lo is None else round(lo * f, 6), None if hi is None else round(hi * f, 6), "HELD",
                     source, kind, tuple(causes))

    def minus(self, d, source):
        return Level(None if self.lo is None else round(self.lo - d, 6), None if self.hi is None else round(self.hi - d, 6),
                     self.status, f"{self.source} - {d:g} ({source})", self.kind, self.causes)


@dataclass(frozen=True)
class Section:
    """Plan section of a member (m2 range) with its class from R-SECTION-CONFLICT-1."""
    a_lo: float
    a_hi: float
    cls: str            # AGREE / DRAFTING_NOTE / CONFLICT / HELD
    source: str = ""

    def __post_init__(self):
        if self.cls not in ("AGREE", "DRAFTING_NOTE", "CONFLICT", "HELD"):
            raise Refused(f"unknown section class {self.cls}")
        if self.cls in ("AGREE", "DRAFTING_NOTE") and abs(self.a_lo - self.a_hi) > 1e-9:
            raise Refused("an agreeing section has one area")
        if self.cls == "CONFLICT" and not self.a_hi > self.a_lo:
            raise Refused("COLLAPSED_CONFLICT: a CONFLICT keeps both sections")

    @staticmethod
    def of(w, d, cls="AGREE", unit="m", source=""):
        f = UNITS[unit]
        a = round(w * f * d * f, 6)
        return Section(a, a, cls, source)

    @staticmethod
    def conflict(a_lo, a_hi, source=""):
        return Section(round(min(a_lo, a_hi), 6), round(max(a_lo, a_hi), 6), "CONFLICT", source)


@dataclass
class Member:
    id: str
    storey: str
    mark: str
    kind: str                      # NECK / COLUMN / PLANTED / TURNED
    section: Section
    base: Level
    top: Level
    existence: str = "DRAWN"       # DRAWN / NOT_DRAWN
    top_owner: str = "COLUMN"      # COLUMN (framing members NET of it) / BEAM_THROUGH (top = that beam's soffit)
    framing: tuple = ()            # ((member id, basis NET / THROUGH), ...) at the top
    handles: tuple = ()
    extra_causes: tuple = ()
    owner_split: dict = field(default_factory=dict)


def _sub(a, b):
    return None if a is None or b is None else round(a - b, 6)


def solid(m: Member) -> dict:
    """The member's solid: height and volume ranges, status and causes. Never 0 for an unknown, never a default."""
    if m.existence != "DRAWN":
        return {"id": m.id, "status": "UNKNOWN", "h_lo": None, "h_hi": None, "m3_lo": None, "m3_hi": None,
                "causes": ("EXISTENCE_NOT_DRAWN",) + tuple(m.extra_causes)}
    thru = [f for f, basis in m.framing if basis == "THROUGH"]
    if m.top_owner == "COLUMN" and thru:
        raise Refused(f"DOUBLE: {m.id} taken to the slab top while {thru} is billed through its footprint")
    if m.top_owner == "BEAM_THROUGH" and not thru:
        raise Refused(f"GAP: {m.id} stopped at a beam soffit while every framing member is billed net of it")
    h_lo = _sub(m.top.lo, m.base.hi)
    h_hi = _sub(m.top.hi, m.base.lo)
    if h_lo is not None and h_lo <= 0:
        raise Refused(f"{m.id}: top not above base ({h_lo} m)")
    causes = list(m.base.causes) + list(m.top.causes) + list(m.extra_causes)
    if m.section.cls == "HELD":
        causes.append("SECTION_NOT_PRINTED")
    if m.section.cls == "CONFLICT":
        causes.append("SECTION_CONFLICT")
    if m.base.status == "HELD" or m.top.status == "HELD" or m.section.cls == "HELD" or m.extra_causes:
        status = "HELD"
    elif m.section.cls == "CONFLICT":
        status = "CONFLICT"
    else:
        status = "DRAWING-CONFIRMED"
    v_lo = None if h_lo is None or m.section.cls == "HELD" else round(m.section.a_lo * h_lo, 6)
    v_hi = None if h_hi is None or m.section.cls == "HELD" else round(m.section.a_hi * h_hi, 6)
    if status == "DRAWING-CONFIRMED":
        assert v_lo == v_hi
    return {"id": m.id, "status": status, "h_lo": h_lo, "h_hi": h_hi, "m3_lo": v_lo, "m3_hi": v_hi,
            "causes": tuple(dict.fromkeys(causes))}


def neck_base(formation: Level, underlay_m: float, h_footing_lo: float, h_footing_hi: float, source: str) -> Level:
    """Footing top = formation + printed underlay (screed + membrane + blinding) + footing depth H (R-NECK-ENDS-1)."""
    lo = None if formation.lo is None else round(formation.lo + underlay_m + h_footing_lo, 6)
    hi = None if formation.hi is None else round(formation.hi + underlay_m + h_footing_hi, 6)
    status = "DRAWING-CONFIRMED" if formation.status == "DRAWING-CONFIRMED" and h_footing_lo == h_footing_hi else "HELD"
    causes = tuple(formation.causes) + (() if h_footing_lo == h_footing_hi else ("FOOTING_DEPTH_TWO_READINGS",))
    return Level(lo, hi, status, f"footing top ({source})", STRUCTURAL, causes)


def stack_check(members) -> list:
    """Every member that stands on another (same plan position key) starts at the other's top datum (no gap, no
    double): returns the failures. members: [(key, lower Member, upper Member)]."""
    bad = []
    for key, lower, upper in members:
        if (lower.top.lo, lower.top.hi) != (upper.base.lo, upper.base.hi):
            bad.append((key, lower.id, upper.id, lower.top.lo, lower.top.hi, upper.base.lo, upper.base.hi))
    return bad


def components(rows) -> dict:
    """Split a line into its components; HELD / UNKNOWN never add to a closable total and never count as 0."""
    out = {"DRAWING-CONFIRMED": [0, 0.0], "CONFLICT": [0, 0.0, 0.0], "HELD": [0, 0.0, 0.0, 0],
           "UNKNOWN": [0]}
    for r in rows:
        s = r["status"]
        if s == "DRAWING-CONFIRMED":
            out[s][0] += 1
            out[s][1] = round(out[s][1] + r["m3_lo"], 6)
        elif s == "CONFLICT":
            out[s][0] += 1
            out[s][1] = round(out[s][1] + r["m3_lo"], 6)
            out[s][2] = round(out[s][2] + r["m3_hi"], 6)
        elif s == "HELD":
            out[s][0] += 1
            if r["m3_lo"] is not None:
                out[s][1] = round(out[s][1] + r["m3_lo"], 6)
            if r["m3_hi"] is not None:
                out[s][2] = round(out[s][2] + r["m3_hi"], 6)
            if r["m3_lo"] is None or r["m3_hi"] is None:
                out[s][3] += 1   # members with an open side: the sums are partial bounds
        else:
            out[s][0] += 1
    return out


def ownership(footprints, slab_panels_exclude_columns: bool, beam_basis: dict) -> list:
    """Each intersection once. footprints: {member id: top_owner}; beam_basis: {member id: [(beam, NET|THROUGH)]}.
    A slab panel that includes a column footprint, a column to the slab top under a THROUGH beam, or a column stopped
    at a soffit with only NET beams is a failure."""
    bad = []
    if not slab_panels_exclude_columns:
        bad.append(("SLAB", "slab panels carry column footprints: DOUBLE with the column line"))
    for mid, owner in footprints.items():
        basis = [b for _, b in beam_basis.get(mid, [])]
        if owner == "COLUMN" and "THROUGH" in basis:
            bad.append((mid, "DOUBLE: beam billed through and column to the slab top"))
        if owner == "BEAM_THROUGH" and "THROUGH" not in basis:
            bad.append((mid, "GAP: column stopped at a soffit, no beam billed through"))
    return bad


def reconcile(other_m3: float, steps: list, own_m3: float, tol: float = 5e-4) -> dict:
    """other -> named steps (cause, m3) -> own; the residual is named, never absorbed."""
    s = round(other_m3 + sum(v for _, v in steps), 6)
    resid = round(own_m3 - s, 6)
    return {"from": round(other_m3, 6), "steps": steps, "to": round(own_m3, 6), "residual": resid,
            "closed": abs(resid) <= tol}


def owner_split(a: float, interval: float, d_ctrl_lo: float, d_ctrl_hi: float, t: float) -> dict:
    """URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 + NON-OVERLAPPING model on the same footprint (one section):
    column A x (interval - D_ctrl), joint A x (D_ctrl - t), head A x t; the three re-add to A x interval."""
    col = (round(a * (interval - d_ctrl_hi), 6), round(a * (interval - d_ctrl_lo), 6))
    joint = (round(a * (d_ctrl_lo - t), 6), round(a * (d_ctrl_hi - t), 6))
    head = round(a * t, 6)
    assert abs(col[0] + joint[1] + head - a * interval) < 1e-6 and abs(col[1] + joint[0] + head - a * interval) < 1e-6
    return {"column": col, "joint": joint, "head": head, "whole": round(a * interval, 6)}
