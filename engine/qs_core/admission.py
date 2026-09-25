"""Admitting openings: deciding what the source says EXISTS, and nothing else.

Two questions were being asked as one, and the answer to the second was being used to retract the first.  "Is
this an opening?" is answered by the source: a door block, a schedule row, a symbol on an opening layer.  "Which
wall is it in?" is answered by geometry, and it can fail.  When one stage answers both, a named door whose host
could not be worked out comes out the other side as an anonymous gap - and thirty-five doors the CAD file names
individually get reported as things nothing in the source names.

So admission decides EXISTENCE only.  Failure to overlap wall material is not evidence against a door: a door
lies in the VOID between two wall ends, and zero material overlap is the normal condition.  Only the source
saying something contradictory - a width finer than the drawing can draw, a duplicate of another object, no
naming evidence of any kind - can keep a candidate out.

A candidate also arrives as the features the source actually has: an insertion point, a span, an orientation, a
block name, a layer, jambs, a swing.  It does NOT arrive as a rectangle, because the rectangle needs a depth and
the depth belongs to the wall that turns out to host it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.qs_core import evidence as EV, geom
from engine.qs_core.entities import (CONFIDENCE_NONE, CONFIDENCE_PROVEN, CONFIDENCE_STRONG, CONFIDENCE_WEAK,
                                     Evidence, Opening)

# ---------------------------------------------------------------- what the source says about existence
EXISTS_CONFIRMED = "EXISTS_CONFIRMED"
EXISTS_UNRESOLVED = "EXISTS_UNRESOLVED"
DOES_NOT_EXIST = "NOT_AN_OPENING"
IS_A_DUPLICATE = "DUPLICATE"

# ---------------------------------------------------------------- the published classifications
OPENING_CONFIRMED_HOST_CONFIRMED = "OPENING_CONFIRMED_HOST_CONFIRMED"
OPENING_CONFIRMED_HOST_UNRESOLVED = "OPENING_CONFIRMED_HOST_UNRESOLVED"
OPENING_CANDIDATE_UNRESOLVED = "OPENING_CANDIDATE_UNRESOLVED"
NON_OPENING_GAP = "NON_OPENING_GAP"
DRAWING_NOISE = "DRAWING_NOISE"
DUPLICATE_OF_CONFIRMED_OPENING = "DUPLICATE_OF_CONFIRMED_OPENING"
CLASSES = (OPENING_CONFIRMED_HOST_CONFIRMED, OPENING_CONFIRMED_HOST_UNRESOLVED,
           OPENING_CANDIDATE_UNRESOLVED, NON_OPENING_GAP, DRAWING_NOISE,
           DUPLICATE_OF_CONFIRMED_OPENING)
# the classes in which a physical opening exists, whatever is known about its host
PHYSICAL_OPENING_CLASSES = (OPENING_CONFIRMED_HOST_CONFIRMED, OPENING_CONFIRMED_HOST_UNRESOLVED)

# ---------------------------------------------------------------- what can vouch for a candidate
PROV_BLOCK = "CAD_BLOCK_IDENTITY"          # the source draws it as a named door or window block
PROV_SCHEDULE = "SCHEDULE_ROW_MATCH"       # a schedule row describes an opening of this type here
PROV_SYMBOL = "SYMBOL_OR_LAYER"            # it sits on a layer, or carries a symbol, that means opening
PROV_SWING = "SWING_OR_LEAF_GEOMETRY"      # a door swing is drawn here
PROV_JAMB = "JAMB_PAIR_GEOMETRY"           # wall material stops either side of it and resumes beyond
PROVENANCE_KINDS = (PROV_BLOCK, PROV_SCHEDULE, PROV_SYMBOL, PROV_SWING, PROV_JAMB)

# These NAME the object as an opening.  Jamb geometry corroborates a named object and, on its own, only says
# that the wall stops - a door, an archway and a forgotten line look identical there.
NAMING_PROVENANCE = (PROV_BLOCK, PROV_SCHEDULE, PROV_SYMBOL, PROV_SWING)

# Two representations of one physical opening sit at the same place on the same line.  Two different openings
# that happen to be the same width do not.
DUPLICATE_SPAN_OVERLAP = 0.50


@dataclass
class Candidate:
    """One thing that might be an opening, described by the features the source actually carries."""
    candidate_ref: str
    floor: str
    source_revision: str
    centre: tuple                                  # insertion point, or the geometric centre of the mark
    span: float                                    # the longitudinal extent: what a surveyor calls the width
    axis: str = None                               # the run the opening lies along, where the source gives it
    rotation: float = None                         # block rotation in degrees, where the source gives it
    opening_type: str = "UNKNOWN"
    origin: str = "EXTRACTED_GEOMETRY"             # EXTRACTED_GEOMETRY / DRAWING_REGISTER / SCHEDULE_ONLY
    block_ref: str = None
    schedule_ref: str = None
    layer: str = None
    symbol: str = None
    swing: dict = None
    jamb_points: list = None                       # [(x, y), (x, y)] where the source draws the reveals
    width_claims: list = field(default_factory=list)
    height_claims: list = field(default_factory=list)
    # filled in by admission
    existence: str = None
    classification: str = None
    duplicate_of: str = None
    admission_evidence: list = field(default_factory=list)
    provenance: list = field(default_factory=list)
    confidence: str = CONFIDENCE_NONE
    # filled in by host resolution, never before
    depth: float = None
    host_record: dict = None

    @property
    def drawn_width(self):
        return self.span

    def interval(self, axis=None):
        """The span this opening occupies along its own run."""
        a = axis or self.axis
        c = self.centre[0] if a == geom.AXIS_X else self.centre[1]
        return (c - self.span / 2.0, c + self.span / 2.0)

    def cross(self, axis=None):
        """The coordinate across the run: the line the opening sits on."""
        a = axis or self.axis
        return self.centre[1] if a == geom.AXIS_X else self.centre[0]

    def footprint(self, depth=None, axis=None):
        """The rectangle of the clear opening - available only once a depth is known.

        Fabricating one before the host is resolved is how an opening acquires the depth of whatever grid cell
        it happened to sit in, which is then compared against wall material and found not to match.
        """
        d = self.depth if depth is None else depth
        if d is None:
            return None
        a = axis or self.axis
        lo, hi = self.interval(a)
        c = self.cross(a)
        if a == geom.AXIS_X:
            return geom.Rect(lo, c - d / 2.0, hi, c + d / 2.0)
        return geom.Rect(c - d / 2.0, lo, c + d / 2.0, hi)


def _provenance(c):
    got = []
    if c.block_ref:
        got.append({"KIND": PROV_BLOCK, "REFERENCE": c.block_ref})
    if c.schedule_ref:
        got.append({"KIND": PROV_SCHEDULE, "REFERENCE": c.schedule_ref})
    if c.symbol or c.layer:
        got.append({"KIND": PROV_SYMBOL, "REFERENCE": c.symbol or c.layer})
    if c.swing:
        got.append({"KIND": PROV_SWING, "REFERENCE": c.swing})
    if c.jamb_points:
        got.append({"KIND": PROV_JAMB, "REFERENCE": c.jamb_points})
    return got


def _match_schedule(c, schedule_rows, tolerance):
    if c.schedule_ref:
        return next((r for r in schedule_rows if r.get("SCHEDULE_REF") == c.schedule_ref), None)
    best = None
    for r in schedule_rows:
        if r.get("FLOOR") not in (None, c.floor):
            continue
        if r.get("TYPE") and c.opening_type not in (None, "UNKNOWN") and r["TYPE"] != c.opening_type:
            continue
        w = r.get("WIDTH_M")
        if w is None or abs(w - c.span) > tolerance:
            continue
        if best is None or abs(w - c.span) < abs(best["WIDTH_M"] - c.span):
            best = r
    return best


def _strength(c):
    kinds = {p["KIND"] for p in c.provenance}
    return (len(kinds & set(NAMING_PROVENANCE)), PROV_BLOCK in kinds, PROV_SCHEDULE in kinds,
            c.origin == "DRAWING_REGISTER", c.span)


def _same_place(a, b, tolerance):
    """Two candidates occupying one place on one line, measured on spans rather than fabricated rectangles."""
    axis = a.axis or b.axis
    if a.axis and b.axis and a.axis != b.axis:
        return 0.0
    if abs(a.cross(axis) - b.cross(axis)) > max(tolerance * 4, 0.10):
        return 0.0
    (alo, ahi), (blo, bhi) = a.interval(axis), b.interval(axis)
    overlap = max(0.0, min(ahi, bhi) - max(alo, blo))
    shortest = min(ahi - alo, bhi - blo)
    return overlap / shortest if shortest > 0 else 0.0


def normalize_opening_population(candidates, schedule_rows, drafting_resolution_m, tolerance):
    """US-20: one physical population out of extracted geometry, the drawing register and the schedule.

    `drafting_resolution_m` is a property of the SOURCE - the finest distance the drawing is authored to.  A gap
    narrower than that cannot be a thing.  It is an argument because only the person who knows how the drawing
    was produced can state it, and a default here would silently delete real narrow openings in a finer source.

    No wall geometry is consulted.  Whether a candidate sits in wall material is a question for host resolution,
    and answering it here is what let a named door be demoted to an anonymous gap.
    """
    schedule_rows = list(schedule_rows or [])
    matched_schedule = {}

    for c in sorted(candidates, key=lambda x: x.candidate_ref):
        c.provenance = _provenance(c)
        row = _match_schedule(c, schedule_rows, tolerance)
        if row is not None and not c.schedule_ref:
            c.schedule_ref = row.get("SCHEDULE_REF")
            c.provenance = _provenance(c)
        if row is not None:
            matched_schedule.setdefault(row.get("SCHEDULE_REF"), []).append(c.candidate_ref)
            if row.get("WIDTH_M") is not None:
                c.width_claims = list(c.width_claims) + [
                    EV.Claim(row["WIDTH_M"], EV.DRAWING_DIMENSION, f"SCHEDULE::{row.get('SCHEDULE_REF')}",
                             {"WHAT": "width stated on the opening schedule"})]
            if row.get("HEIGHT_M") is not None:
                c.height_claims = list(c.height_claims) + [
                    EV.Claim(row["HEIGHT_M"], EV.DRAWING_DIMENSION, f"SCHEDULE::{row.get('SCHEDULE_REF')}",
                             {"WHAT": "height stated on the opening schedule"})]

        names_it = [p for p in c.provenance if p["KIND"] in NAMING_PROVENANCE]
        below_resolution = c.span < drafting_resolution_m

        if below_resolution and not c.provenance:
            c.existence = DOES_NOT_EXIST
            c.classification = DRAWING_NOISE
            c.confidence = CONFIDENCE_PROVEN
            c.admission_evidence = [Evidence("BELOW_THE_SOURCE_DRAFTING_RESOLUTION", {
                "SPAN_M": round(c.span, 6), "DRAFTING_RESOLUTION_M": drafting_resolution_m, "PROVENANCE": [],
                "WHY": "nothing vouches for this candidate and it is narrower than the distance this drawing "
                       "was authored to, so it is two lines that did not meet"})]
        elif below_resolution:
            c.existence = EXISTS_UNRESOLVED
            c.classification = OPENING_CANDIDATE_UNRESOLVED
            c.confidence = CONFIDENCE_WEAK
            c.admission_evidence = [Evidence("VOUCHED_FOR_BUT_BELOW_RESOLUTION", {
                "SPAN_M": round(c.span, 6), "DRAFTING_RESOLUTION_M": drafting_resolution_m,
                "PROVENANCE": c.provenance,
                "WHY": "the source says an opening is here and draws it narrower than it can draw; the two "
                       "statements contradict each other and the engine does not pick one"})]
        elif names_it:
            c.existence = EXISTS_CONFIRMED
            c.classification = OPENING_CONFIRMED_HOST_UNRESOLVED       # until hosting says otherwise
            c.confidence = (CONFIDENCE_PROVEN if len({p["KIND"] for p in names_it}) > 1 else CONFIDENCE_STRONG)
            c.admission_evidence = [Evidence("ADMITTED_ON_PROVENANCE", {
                "NAMED_BY": names_it, "PROVENANCE": c.provenance, "SPAN_M": round(c.span, 6),
                "WHY": "the source identifies this as an opening.  Whether it overlaps wall material is a "
                       "question about its host, not about whether it exists: a door lies in the void between "
                       "two wall ends"})]
        elif c.jamb_points:
            c.existence = EXISTS_UNRESOLVED
            c.classification = OPENING_CANDIDATE_UNRESOLVED
            c.confidence = CONFIDENCE_WEAK
            c.admission_evidence = [Evidence("A_GAP_IN_A_WALL_THAT_NOTHING_NAMES", {
                "JAMBS": c.jamb_points, "SPAN_M": round(c.span, 6), "NAMED_BY": [],
                "WHY": "the wall stops here and nothing says what fills the gap; a door, an archway and a "
                       "missing line look identical at this point, and they are measured differently"})]
        else:
            c.existence = DOES_NOT_EXIST
            c.classification = NON_OPENING_GAP
            c.confidence = CONFIDENCE_STRONG
            c.admission_evidence = [Evidence("NOTHING_NAMES_IT_AND_NOTHING_IS_INTERRUPTED", {
                "SPAN_M": round(c.span, 6), "PROVENANCE": c.provenance,
                "WHY": "no block, schedule row, symbol, swing or pair of jambs says an opening is here"})]

    # ------------------------------------------------ one physical object represented twice
    confirmed = [c for c in candidates if c.existence == EXISTS_CONFIRMED]
    confirmed.sort(key=lambda c: (_strength(c), c.candidate_ref), reverse=True)
    kept = []
    for c in confirmed:
        twin = next((k for k in kept if k.floor == c.floor
                     and _same_place(k, c, tolerance) >= DUPLICATE_SPAN_OVERLAP), None)
        if twin is None:
            kept.append(c)
            continue
        c.existence = IS_A_DUPLICATE
        c.classification = DUPLICATE_OF_CONFIRMED_OPENING
        c.duplicate_of = twin.candidate_ref
        c.confidence = CONFIDENCE_PROVEN
        c.admission_evidence = [Evidence("SAME_PHYSICAL_OPENING_AS_ANOTHER_CANDIDATE", {
            "DUPLICATE_OF": twin.candidate_ref, "SPAN_OVERLAP": round(_same_place(twin, c, tolerance), 6),
            "THRESHOLD": DUPLICATE_SPAN_OVERLAP,
            "KEPT_BECAUSE": {"REF": twin.candidate_ref, "PROVENANCE": twin.provenance},
            "WHY": "two representations occupy the same place on the same line; counting both would deduct one "
                   "hole twice"})]

    counts = {k: sum(1 for c in candidates if c.classification == k) for k in CLASSES}
    physical = [c for c in candidates if c.existence == EXISTS_CONFIRMED]
    named = [c for c in candidates if any(p["KIND"] in NAMING_PROVENANCE for p in c.provenance)]
    return {
        "POPULATION": [as_dict(c) for c in sorted(candidates, key=lambda x: x.candidate_ref)],
        "COUNTS": counts,
        "CANDIDATES_IN": len(candidates),
        "NAMED_BY_THE_SOURCE": sorted(c.candidate_ref for c in named),
        "NAMED_BY_THE_SOURCE_COUNT": len(named),
        "PHYSICAL_OPENING_COUNT": len(physical),
        "PHYSICAL_OPENING_REFS": sorted(c.candidate_ref for c in physical),
        "SCHEDULE_ROWS_IN": len(schedule_rows),
        "SCHEDULE_ROWS_MATCHED": len(matched_schedule),
        "SCHEDULE_ROWS_WITHOUT_GEOMETRY": [{"SCHEDULE_REF": r.get("SCHEDULE_REF"), "FLOOR": r.get("FLOOR"),
                                            "TYPE": r.get("TYPE"), "WIDTH_M": r.get("WIDTH_M"),
                                            "WHY": "the schedule describes this opening and no geometry was "
                                                   "extracted for it; it is a question, not a quantity"}
                                           for r in schedule_rows
                                           if r.get("SCHEDULE_REF") not in matched_schedule],
        "CONFIRMED_WITHOUT_A_SCHEDULE_ROW": sorted(c.candidate_ref for c in physical if not c.schedule_ref),
        "DRAFTING_RESOLUTION_M": drafting_resolution_m,
        "RULE": "admission decides EXISTENCE only, on what the source names.  Failure to overlap wall material "
                "is never evidence against an opening, because a door lies in the void between two wall ends",
        "NAMING_PROVENANCE": list(NAMING_PROVENANCE),
        "CORROBORATING_PROVENANCE": [PROV_JAMB],
        "CLASSES": list(CLASSES),
        "PHYSICAL_OPENING_CLASSES": list(PHYSICAL_OPENING_CLASSES),
    }


def refresh(population, candidates):
    """Re-serialise the population after a later stage has changed what a candidate is known to be."""
    by_ref = {c.candidate_ref: c for c in candidates}
    rows = [as_dict(by_ref[r["CANDIDATE_REF"]]) if r["CANDIDATE_REF"] in by_ref else r
            for r in population["POPULATION"]]
    counts = {k: sum(1 for r in rows if r["CLASSIFICATION"] == k) for k in CLASSES}
    physical = [r for r in rows if r["CLASSIFICATION"] in PHYSICAL_OPENING_CLASSES]
    return dict(population, POPULATION=rows, COUNTS=counts,
                PHYSICAL_OPENING_COUNT=len(physical),
                PHYSICAL_OPENING_REFS=sorted(r["CANDIDATE_REF"] for r in physical))


def as_dict(c):
    return {"CANDIDATE_REF": c.candidate_ref, "FLOOR": c.floor, "ORIGIN": c.origin, "TYPE": c.opening_type,
            "CENTRE": [round(v, 6) for v in c.centre], "SPAN_M": round(c.span, 6), "AXIS": c.axis,
            "ROTATION_DEG": c.rotation, "SWING": c.swing, "JAMB_POINTS": c.jamb_points,
            "EXISTENCE": c.existence, "CLASSIFICATION": c.classification, "DUPLICATE_OF": c.duplicate_of,
            "CONFIDENCE": c.confidence, "PROVENANCE": c.provenance,
            "BLOCK_REF": c.block_ref, "SCHEDULE_REF": c.schedule_ref, "LAYER": c.layer,
            "DEPTH_M": c.depth, "HOST": c.host_record,
            "GEOMETRY": None if c.footprint() is None else c.footprint().as_tuple(),
            "EVIDENCE": [e.as_dict() for e in c.admission_evidence]}


def admitted_openings(candidates, tolerance, subject_of=None, revision=None):
    """The physical population, as engine openings, with width and height resolved through the hierarchy.

    Every confirmed opening leaves this stage whatever its host turns out to be.  An opening whose host is not
    resolved keeps its place in the population and in every coverage check; what it loses is a deduction.
    """
    out = []
    for c in sorted((c for c in candidates if c.existence == EXISTS_CONFIRMED),
                    key=lambda x: x.candidate_ref):
        subject = dict(subject_of(c) if subject_of else {})
        subject.setdefault("OBJECT_KIND", c.opening_type)
        subject.setdefault("HAS_SOURCE_HEIGHT",
                           any(cl.source == EV.DRAWING_DIMENSION for cl in c.height_claims))
        w = EV.resolve("width", list(c.width_claims) + [
            EV.Claim(c.span, EV.MEASURED_GEOMETRY, c.candidate_ref,
                     {"WHAT": "the clear opening as drawn"})], tolerance, subject=subject, revision=revision)
        h = EV.resolve("height", c.height_claims, tolerance, subject=subject, revision=revision)
        o = Opening(c.candidate_ref, c.footprint(), c.floor, c.source_revision, opening_type=c.opening_type,
                    width=w["VALUE"] if EV.established(w) else None,
                    height=h["VALUE"] if EV.established(h) else None,
                    width_source=w["SOURCE"], height_source=h["SOURCE"], axis=c.axis, layer=c.layer)
        o.candidate = c
        o.admission = {"CLASSIFICATION": c.classification, "EXISTENCE": c.existence,
                       "PROVENANCE": c.provenance, "SUBJECT": subject,
                       "WIDTH_EVIDENCE": w, "HEIGHT_EVIDENCE": h}
        out.append(o)
    return out
