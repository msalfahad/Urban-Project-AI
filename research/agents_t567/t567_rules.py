"""T-567 rules (research, unwired; any villa): EXTERNAL PLASTER / FACADE FINISH reconciliation against a freelancer
statement BY ELEVATION AND FACE CLASS, exact in m2.

R-T567-1 (one face, one elevation, one class). Every drawn exterior face is booked once under a key; its elevation is
    read from the face itself (its orientation), never from the freelancer's grouping; a key on two elevations, or the
    same key booked twice, is refused. Face classes:
      render faces (the comparable universe): PLINTH, STOREY, PARAPET_OUTER, SLAB_EDGE, PARAPET_INNER_TOP;
      own-family faces, never inside a render total: REVEAL (opening reveals, their own line family), SOFFIT (ceiling
      family, Q-68 C), CLADDING (B4-11 layer: a face clad is not rendered; cladding m2 inside render m2 is refused).
    m.l items (arrises, corners, drips, copings) are never m2.
R-T567-2 (portions). A freelancer row may match a whole face or a length portion of it; the portions of one key sum to
    at most the whole; what is left is a face in no row of his (an OURS_ONLY component), never dropped.
R-T567-3 (exact bridge, two passes). For each pass (lo, hi):
      his gross = sum over his rows of (drawn m2 matched + named terms + his-only parts)          [his statement]
      our gross = sum of drawn m2 matched + sum of OURS_ONLY faces                                  [the drawing]
    so his gross - our gross = terms + his-only - ours-only, residual exactly 0 (exact rationals). His opening deduction (his
    convention, e.g. half) and ours (full holes, Q-73) are their own steps from gross to net, never components.
    A HELD face carries its bound (lo .. hi), never 0; a HELD face with no number stays BLANK by name and is counted,
    never summed as 0. A freelancer figure is never a drawn quantity.
R-T567-4 (elevation matrix). Cells = drawn m2 of our elevation E matched into his group G. Row sums + OURS_ONLY = our
    elevation totals; column sums + terms + his-only = his group totals; both totals close exactly.
R-T567-5 (parapet faces). The inner face of a parapet runs on the inner perimeter (outer run - 8 t on a closed
    rectangle of wall thickness t), its top on the centre-line run (outer run - 4 t) x t: taking the inner face at the
    outer run is refused.
R-T567-6 (projecting elements). A pier or frame band standing in front of a face key measured on its projected
    length: the key holds the fronts; the returns (developed outline - projection) are faces of their own, per band
    in which the plan of that level draws the element; a jamb return is an opening-reveal item; booking the developed
    outline in full on top of the key is refused (projecting_returns, returns_face).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction

D = Fraction    # exact rational arithmetic: length portions such as 6.77 / 14.87 stay exact
RENDER_CLASSES = ("PLINTH", "STOREY", "PARAPET_OUTER", "SLAB_EDGE", "PARAPET_INNER_TOP")
OWN_FAMILY_CLASSES = ("REVEAL", "SOFFIT", "CLADDING")
CAUSES = ("ENGINE_RIGHT", "RULE_DIFFERENCE", "HELD", "UNRESOLVED", "ENGINE_WRONG", "ROUNDING")
STATUSES = ("DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN")


class RuleError(ValueError):
    pass


def d(x) -> Fraction:
    if isinstance(x, Fraction):
        return x
    if isinstance(x, float):
        raise RuleError("floats are refused: pass decimal strings")
    return Fraction(str(x)) if not isinstance(x, Decimal) else Fraction(x)


def fmt(x: Fraction, dp: int = 6) -> str:
    """Exact decimal text when the value terminates within 9 places, else rounded to dp (marked by the caller)."""
    q = Decimal(x.numerator) / Decimal(x.denominator)
    return f"{q.quantize(Decimal(1).scaleb(-dp)):f}"


@dataclass(frozen=True)
class Face:
    key: str
    elevation: str
    face_class: str
    lo: Fraction | None          # None = BLANK (HELD, no number)
    hi: Fraction | None
    status: str
    length: Fraction | None = None
    unit: str = "m2"
    owner_line: str = ""

    def qty(self, pas: str) -> Fraction | None:
        return self.lo if pas == "lo" else self.hi


def face(key, elevation, face_class, lo, hi=None, status="DRAWING-CONFIRMED", length=None, unit="m2",
         owner_line="") -> Face:
    if unit != "m2":
        raise RuleError(f"{key}: an m.l item is never a face (unit {unit})")
    if face_class not in RENDER_CLASSES + OWN_FAMILY_CLASSES:
        raise RuleError(f"{key}: unknown face class {face_class}")
    if status not in STATUSES:
        raise RuleError(f"{key}: unknown status {status}")
    if lo is None and hi is None:
        if status not in ("HELD", "UNKNOWN"):
            raise RuleError(f"{key}: a blank face must be HELD or UNKNOWN")
        return Face(key, elevation, face_class, None, None, status, None if length is None else d(length), unit,
                    owner_line)
    lo = d(lo)
    hi = lo if hi is None else d(hi)
    if hi < lo:
        raise RuleError(f"{key}: bound reversed")
    if status == "DRAWING-CONFIRMED" and lo != hi:
        raise RuleError(f"{key}: a DRAWING-CONFIRMED face has one value, not a range")
    if status == "UNKNOWN":
        raise RuleError(f"{key}: UNKNOWN carries no number")
    if status == "HELD" and hi == 0:
        raise RuleError(f"{key}: a HELD face bounded at 0 .. 0 is a hidden 0: give its bound or leave it blank")
    return Face(key, elevation, face_class, lo, hi, status, None if length is None else d(length), unit,
                owner_line)


class Book:
    """R-T567-1: one key, one elevation, one class; render and own-family faces kept apart."""

    def __init__(self):
        self.faces: dict[str, Face] = {}

    def add(self, f: Face) -> None:
        old = self.faces.get(f.key)
        if old is not None:
            if old.elevation != f.elevation:
                raise RuleError(f"{f.key}: one face on two elevations ({old.elevation} / {f.elevation}) refused")
            raise RuleError(f"{f.key}: face booked twice refused")
        self.faces[f.key] = f

    def replace(self, key: str, f: Face) -> None:
        """A re-measure of a booked face (a later merged ledger): same key, same elevation, new value."""
        old = self.faces[key]
        if old.elevation != f.elevation or old.face_class != f.face_class:
            raise RuleError(f"{key}: a re-measure keeps the face's elevation and class")
        self.faces[key] = f

    def remove(self, key: str, why: str) -> None:
        if not why:
            raise RuleError(f"{key}: a removal needs its physical reason")
        del self.faces[key]

    def render(self):
        return {k: f for k, f in self.faces.items() if f.face_class in RENDER_CLASSES}

    def check_cladding(self, cladding: dict[str, Fraction]) -> None:
        """A clad area is not rendered: cladding m2 recorded on a render key refuses the render total."""
        for k, m in cladding.items():
            if k in self.render() and d(m) > 0:
                raise RuleError(f"{k}: cladding m2 inside render m2 refused (one face, one finish)")


@dataclass
class Portion:
    key: str
    part: Fraction               # fraction of the face (length portion / face length), 0 < part <= 1
    note: str = ""


@dataclass
class Term:
    name: str
    cause: str
    lo: Fraction
    hi: Fraction | None = None
    source: str = ""

    def qty(self, pas):
        return self.lo if (pas == "lo" or self.hi is None) else self.hi


@dataclass
class HisRow:
    row: str                    # his sheet row(s)
    group: str                  # his elevation group as written in his sheet
    his_m2: Fraction
    portions: list = field(default_factory=list)      # Portion
    terms: list = field(default_factory=list)         # Term (his - drawn, by cause)
    his_only: list = field(default_factory=list)      # Term: parts of his row with no drawn face (scope / no face)
    matched_other: list = field(default_factory=list)  # (name, lo, hi): drawn items of another ledger (inner / top)


def term(name, cause, lo, hi=None, source="") -> Term:
    if cause not in CAUSES:
        raise RuleError(f"{name}: cause {cause} not in {CAUSES}")
    if not source:
        raise RuleError(f"{name}: every term names its source")
    return Term(name, cause, d(lo), None if hi is None else d(hi), source)


def portion_m2(f: Face, part: Fraction, pas: str) -> Fraction:
    q = f.qty(pas)
    if q is None:
        raise RuleError(f"{f.key}: a blank HELD face cannot be matched to a freelancer row by m2")
    return q * part


def bridge(book: Book, rows: list[HisRow], his_gross: Fraction, his_deduction: Fraction, our_openings: tuple,
           tolerance: Fraction = D(0)) -> dict:
    """R-T567-2 .. 4. Returns both passes, the elevation matrix, OURS_ONLY faces and the blank faces by name."""
    if tolerance != 0:
        raise RuleError("the bridge is exact: tolerance must be 0")
    faces = book.render()
    used: dict[str, Fraction] = {}
    for r in rows:
        for p in r.portions:
            if p.key not in faces:
                raise RuleError(f"row {r.row}: portion of {p.key}, not a booked render face")
            if not (0 < p.part <= 1):
                raise RuleError(f"row {r.row}: portion {p.part} of {p.key} out of (0, 1]")
            used[p.key] = used.get(p.key, D(0)) + p.part
            if used[p.key] > 1:
                raise RuleError(f"{p.key}: matched by more than its whole (a face counted twice)")
    if sum((r.his_m2 for r in rows), D(0)) != his_gross:
        raise RuleError("his rows do not add up to his gross")
    out = {"passes": {}, "blank_faces": sorted(k for k, f in faces.items() if f.lo is None)}
    for pas in ("lo", "hi"):
        matrix: dict[tuple, Fraction] = {}
        comps = []
        for r in rows:
            drawn = D(0)
            for p in r.portions:
                f = faces[p.key]
                m = portion_m2(f, p.part, pas)
                drawn += m
                matrix[(f.elevation, r.group)] = matrix.get((f.elevation, r.group), D(0)) + m
            for name, lo, hi in r.matched_other:
                m = d(lo) if pas == "lo" else d(hi)
                drawn += m
                matrix[("ROOF (parapet inner + top)", r.group)] = matrix.get(
                    ("ROOF (parapet inner + top)", r.group), D(0)) + m
            t = sum((x.qty(pas) for x in r.terms), D(0))
            h = sum((x.qty(pas) for x in r.his_only), D(0))
            if drawn + t + h != r.his_m2:
                raise RuleError(f"row {r.row} ({pas}): drawn {drawn} + terms {t} + his-only {h} != his {r.his_m2}")
            for x in r.terms:
                comps.append({"row": r.row, "group": r.group, "kind": "TERM", "name": x.name, "cause": x.cause,
                              "m2": x.qty(pas), "source": x.source})
            for x in r.his_only:
                comps.append({"row": r.row, "group": r.group, "kind": "HIS_ONLY", "name": x.name, "cause": x.cause,
                              "m2": x.qty(pas), "source": x.source})
        ours_only = []
        for k, f in faces.items():
            rest = 1 - used.get(k, D(0))
            if rest > 0 and f.lo is not None:
                m = f.qty(pas) * rest
                ours_only.append({"key": k, "elevation": f.elevation, "class": f.face_class, "status": f.status,
                                  "part": rest, "m2": m})
                comps.append({"row": "-", "group": "-", "kind": "OURS_ONLY", "name": k, "cause":
                              "HELD" if f.status == "HELD" else "ENGINE_RIGHT", "m2": -m,
                              "source": "drawn face in no row of his"})
        matched = sum(matrix.values(), D(0))
        ours = matched + sum((x["m2"] for x in ours_only), D(0))
        diff = his_gross - ours
        s = sum((c["m2"] for c in comps), D(0))
        residual = diff - s
        if residual != 0:
            raise RuleError(f"bridge ({pas}) residual {residual} != 0")
        op = d(our_openings[0] if pas == "lo" else our_openings[1])
        out["passes"][pas] = {"our_gross": ours, "his_gross": his_gross, "gross_diff": diff, "components": comps,
                              "matrix": matrix, "ours_only": ours_only, "residual": residual,
                              "his_net": his_gross - his_deduction, "our_openings": op, "our_net": ours - op,
                              "net_diff": (his_gross - his_deduction) - (ours - op)}
    return out


def by_cause(comps) -> dict:
    out: dict[str, Fraction] = {}
    for c in comps:
        out[c["cause"]] = out.get(c["cause"], D(0)) + c["m2"]
    return out


# ---- R-T567-5: a closed rectangular box with a parapet (the fixture shape; any villa's simple block)
def box_faces(length, width, height, parapet_h, t, windows=(), datum="0", elev_names=("SE", "NE", "NW", "SW"),
              unit="m"):
    """Outer dimensions length x width, walls from datum to the roof (height), parapet parapet_h above the roof, wall
    thickness t. Returns a Book: four STOREY faces (gross; openings listed apart), four PARAPET_OUTER faces, one
    PARAPET_INNER_TOP item per side (inner face on the inner run + top on the centre-line run)."""
    k = D("1000") if unit == "mm" else D(1)
    L, W, H, P, T = (d(x) / k for x in (length, width, height, parapet_h, t))
    Z = d(datum) / k
    b = Book()
    sides = [(elev_names[0], L), (elev_names[1], W), (elev_names[2], L), (elev_names[3], W)]
    for e, run in sides:
        b.add(face(f"BOX/{e}/STOREY", e, "STOREY", run * (H - Z), length=run))
        b.add(face(f"BOX/{e}/PARAPET", e, "PARAPET_OUTER", run * P, length=run))
        inner_run, centre_run = run - 2 * T, run - T
        b.add(face(f"BOX/{e}/PARAPET-INNER+TOP", "ROOF (parapet inner + top)", "PARAPET_INNER_TOP",
                   inner_run * P + centre_run * T, length=inner_run))
    holes = sum((d(w) / k * d(h) / k for w, h in windows), D(0))
    return b, holes


def parapet_inner_face(outer_run, t, h, run_basis="INNER"):
    """R-T567-5: inner face of a closed parapet ring. Taking it on the outer run is refused."""
    if run_basis != "INNER":
        raise RuleError("the parapet inner face is measured on its inner run, not the outer run")
    return (d(outer_run) - 8 * d(t)) * d(h)


# ---- R-T567-6: a projecting element (pier, frame band) standing in front of a face key that is measured on its
# projected length. The key's m2 already holds the element's projection (its fronts); the faces it misses are the
# returns: developed outline - projection, over the band(s) in which the plan of that level draws the element.
# A return that frames an opening (a jamb) is an opening-reveal item (REVEAL family), never a render face here.
def projecting_returns(segments, key_span, tolerance="0.000002"):
    """segments: [(developed_m, projected_on_key_m, role)] with role 'face' or 'jamb'. The projections must add up to
    the key span the element occupies (within the 6-dp rounding of the plan lengths, stated); returns
    (render_extra_m, jamb_extra_m)."""
    proj = sum((d(p) for _, p, _ in segments), Fraction(0))
    if abs(proj - d(key_span)) > d(tolerance):
        raise RuleError(f"projections {proj} do not cover the key span {key_span}: outline not closed on the key")
    face_x = sum((d(a) - d(p) for a, p, r in segments if r == "face"), Fraction(0))
    jamb_x = sum((d(a) - d(p) for a, p, r in segments if r == "jamb"), Fraction(0))
    for a, p, r in segments:
        if r not in ("face", "jamb"):
            raise RuleError(f"segment role {r}")
        if d(a) < d(p):
            raise RuleError("a developed segment is never shorter than its projection")
    return face_x, jamb_x


def returns_face(key, elevation, extra_m, band_lo, band_hi=None, status="DRAWING-CONFIRMED", developed_in_full=False):
    """The returns' face on one band: extra_m x band height (a range when the band top is HELD). Booking the whole
    developed outline on top of the key's projected length is refused (it counts the fronts twice)."""
    if developed_in_full:
        raise RuleError(f"{key}: the developed outline in full double-counts the fronts the key already holds")
    lo = d(extra_m) * d(band_lo)
    hi = None if band_hi is None else d(extra_m) * d(band_hi)
    return face(key, elevation, "STOREY" if "storey" in key else "PARAPET_OUTER", lo, hi, status)
