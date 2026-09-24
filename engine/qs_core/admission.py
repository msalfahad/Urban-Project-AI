"""Admitting openings: deciding what is actually there before deciding which wall it is in.

Host assignment answers "which wall is this opening in".  It cannot answer "is this an opening at all", and if
it is asked to, it answers confidently about a two-millimetre drafting gap.  Three populations reach the engine
from any real source - the extracted geometry, the drawing's own opening register, and the schedule - and they
are never the same list.  One physical door can appear in all three; a hairline gap between two polylines
appears only in the first; a door on the schedule that nobody drew appears only in the third.

So US-20: normalise all three to one physical population FIRST, with every admission decision carrying the
provenance that supports it.  A candidate is admitted because something says it is a door - a block, a schedule
row, a symbol, a pair of jambs - and never because it is the right size.  Size can only reject, and only below
the resolution the source was drawn at.

Nothing here deletes anything.  Every candidate keeps its reference and leaves with a classification and a
reason, so a reviewer can disagree with any one of them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from engine.qs_core import evidence as EV, geom
from engine.qs_core.entities import (CONFIDENCE_NONE, CONFIDENCE_PROVEN, CONFIDENCE_STRONG, CONFIDENCE_WEAK,
                                     Evidence, Opening)

# ---------------------------------------------------------------- the classifications, and nothing else
CONFIRMED_OPENING = "CONFIRMED_OPENING"
DUPLICATE_OF_CONFIRMED_OPENING = "DUPLICATE_OF_CONFIRMED_OPENING"
DRAWING_NOISE = "DRAWING_NOISE"
NON_OPENING_GAP = "NON_OPENING_GAP"
OPENING_CANDIDATE_UNRESOLVED = "OPENING_CANDIDATE_UNRESOLVED"
CLASSES = (CONFIRMED_OPENING, DUPLICATE_OF_CONFIRMED_OPENING, DRAWING_NOISE, NON_OPENING_GAP,
           OPENING_CANDIDATE_UNRESOLVED)

# ---------------------------------------------------------------- what can vouch for a candidate
PROV_BLOCK = "CAD_BLOCK_IDENTITY"          # the source draws it as a named door or window block
PROV_SCHEDULE = "SCHEDULE_ROW_MATCH"       # a schedule row describes an opening of this type here
PROV_SYMBOL = "SYMBOL_OR_LAYER"            # it sits on a layer, or carries a symbol, that means opening
PROV_JAMB = "JAMB_PAIR_GEOMETRY"           # wall material stops either side of it and resumes beyond
PROVENANCE_KINDS = (PROV_BLOCK, PROV_SCHEDULE, PROV_SYMBOL, PROV_JAMB)

# Only these NAME the object as an opening.  Jamb geometry is corroborating: it establishes that the candidate
# lies in a wall line rather than in open space, and it raises confidence once something else has named the
# object - but a gap between two jambs is equally a door, an archway and a line the draughtsman forgot, and
# those are measured differently.  Admitting on jambs alone is how an archway becomes a deduction.
NAMING_PROVENANCE = (PROV_BLOCK, PROV_SCHEDULE, PROV_SYMBOL)

# Two representations of one physical opening overlap almost entirely.  Two different openings that happen to be
# the same width do not overlap at all.  This is a statement about geometry, not about a drawing convention.
DUPLICATE_OVERLAP = 0.50

# A candidate has to be mostly inside wall material before "which wall is it in" is even a question.
WALL_INTERSECTION_SHARE = 0.10


@dataclass
class Candidate:
    """One thing that might be an opening, and everything that vouches for it."""
    candidate_ref: str
    rect: geom.Rect
    floor: str
    source_revision: str
    axis: str = None
    opening_type: str = "UNKNOWN"
    origin: str = "EXTRACTED_GEOMETRY"          # EXTRACTED_GEOMETRY / DRAWING_REGISTER / SCHEDULE_ONLY
    block_ref: str = None
    schedule_ref: str = None
    layer: str = None
    symbol: str = None
    jamb_evidence: dict = None
    width_claims: list = field(default_factory=list)      # evidence.Claim
    height_claims: list = field(default_factory=list)     # evidence.Claim
    # filled in by the admission stage
    classification: str = None
    duplicate_of: str = None
    admission_evidence: list = field(default_factory=list)
    provenance: list = field(default_factory=list)
    confidence: str = CONFIDENCE_NONE

    @property
    def drawn_width(self):
        """The extent along the candidate's own run: what a surveyor would call its width."""
        if self.axis == geom.AXIS_X:
            return self.rect.width
        if self.axis == geom.AXIS_Y:
            return self.rect.height
        return min(self.rect.width, self.rect.height)

    @property
    def drawn_depth(self):
        if self.axis == geom.AXIS_X:
            return self.rect.height
        if self.axis == geom.AXIS_Y:
            return self.rect.width
        return max(self.rect.width, self.rect.height)


def _provenance(c):
    got = []
    if c.block_ref:
        got.append({"KIND": PROV_BLOCK, "REFERENCE": c.block_ref})
    if c.schedule_ref:
        got.append({"KIND": PROV_SCHEDULE, "REFERENCE": c.schedule_ref})
    if c.symbol or c.layer:
        got.append({"KIND": PROV_SYMBOL, "REFERENCE": c.symbol or c.layer})
    if c.jamb_evidence:
        got.append({"KIND": PROV_JAMB, "REFERENCE": c.jamb_evidence})
    return got


def _jamb_pair(c, wall_bands, tolerance):
    """Wall material stopping either side of the candidate, along its own run: a reveal.

    This says the candidate is a break IN something.  It does not say what fills the break.
    """
    if c.axis not in (geom.AXIS_X, geom.AXIS_Y):
        return None
    r = c.rect
    lo, hi = (r.x0, r.x1) if c.axis == geom.AXIS_X else (r.y0, r.y1)
    before, after = [], []
    for b in wall_bands:
        if b.floor != c.floor:
            continue
        bb = b.bbox
        if c.axis == geom.AXIS_X:
            if min(bb.y1, r.y1) - max(bb.y0, r.y0) <= 0:
                continue
            blo, bhi = bb.x0, bb.x1
        else:
            if min(bb.x1, r.x1) - max(bb.x0, r.x0) <= 0:
                continue
            blo, bhi = bb.y0, bb.y1
        if abs(bhi - lo) <= tolerance:
            before.append(b.component_ref)
        if abs(blo - hi) <= tolerance:
            after.append(b.component_ref)
    if before and after:
        return {"BEFORE": sorted(before), "AFTER": sorted(after),
                "WHY": "wall material stops at one edge of this candidate and resumes at the other, so it is "
                       "a break in a wall line"}
    return None


def _wall_share(c, wall_bands):
    """How much of the candidate lies in wall material.  An opening is a hole in something."""
    if c.rect.area <= 0:
        return 0.0
    inter = 0.0
    for b in wall_bands:
        if b.floor != c.floor:
            continue
        for r in b.rects:
            i = c.rect.intersection(r)
            if i:
                inter += i.area
    return min(1.0, inter / c.rect.area)


def _match_schedule(c, schedule_rows, tolerance):
    """A schedule row for this candidate: same floor, compatible type, a width the schedule states."""
    if c.schedule_ref:
        return next((r for r in schedule_rows if r.get("SCHEDULE_REF") == c.schedule_ref), None)
    best = None
    for r in schedule_rows:
        if r.get("FLOOR") not in (None, c.floor):
            continue
        if r.get("TYPE") and c.opening_type not in (None, "UNKNOWN") and r["TYPE"] != c.opening_type:
            continue
        w = r.get("WIDTH_M")
        if w is None or abs(w - c.drawn_width) > tolerance:
            continue
        if best is None or abs(w - c.drawn_width) < abs(best["WIDTH_M"] - c.drawn_width):
            best = r
    return best


def _strength(c):
    """How strongly a candidate is vouched for, used only to decide which of two duplicates is the original."""
    kinds = {p["KIND"] for p in c.provenance}
    return (len(kinds & set(PROVENANCE_KINDS)),
            PROV_BLOCK in kinds, PROV_SCHEDULE in kinds,
            c.origin == "DRAWING_REGISTER", c.rect.area)


def _overlap_share(a, b):
    i = a.rect.intersection(b.rect)
    if not i:
        return 0.0
    return i.area / min(a.rect.area, b.rect.area) if min(a.rect.area, b.rect.area) > 0 else 0.0


def normalize_opening_population(candidates, wall_bands, schedule_rows, drafting_resolution_m, tolerance):
    """US-20: one physical population out of extracted geometry, the drawing register and the schedule.

    `drafting_resolution_m` is a property of the SOURCE - the finest distance the drawing is authored to.  A gap
    narrower than that cannot be a thing; it is two lines that did not meet.  It is an argument because only the
    person who knows how the drawing was produced can state it, and a default here would silently delete real
    narrow openings in a source drawn more finely.
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

        share = _wall_share(c, wall_bands)
        if not c.jamb_evidence:
            c.jamb_evidence = _jamb_pair(c, wall_bands, tolerance)
            if c.jamb_evidence:
                c.provenance = _provenance(c)
        in_a_wall = share >= WALL_INTERSECTION_SHARE or bool(c.jamb_evidence)
        names_it = [p for p in c.provenance if p["KIND"] in NAMING_PROVENANCE]
        below_resolution = c.drawn_width < drafting_resolution_m

        if below_resolution and not c.provenance:
            c.classification = DRAWING_NOISE
            c.confidence = CONFIDENCE_PROVEN
            c.admission_evidence = [Evidence("BELOW_THE_SOURCE_DRAFTING_RESOLUTION", {
                "DRAWN_WIDTH_M": round(c.drawn_width, 6), "DRAFTING_RESOLUTION_M": drafting_resolution_m,
                "PROVENANCE": [], "WHY": "nothing vouches for this candidate and it is narrower than the "
                                         "distance this drawing was authored to, so it is two lines that did "
                                         "not meet rather than a hole in a wall"})]
        elif below_resolution:
            c.classification = OPENING_CANDIDATE_UNRESOLVED
            c.confidence = CONFIDENCE_WEAK
            c.admission_evidence = [Evidence("VOUCHED_FOR_BUT_BELOW_RESOLUTION", {
                "DRAWN_WIDTH_M": round(c.drawn_width, 6), "DRAFTING_RESOLUTION_M": drafting_resolution_m,
                "PROVENANCE": c.provenance,
                "WHY": "the source says an opening is here and draws it narrower than it can draw; the two "
                       "statements contradict each other and the engine does not pick one"})]
        elif not in_a_wall and not names_it:
            c.classification = NON_OPENING_GAP
            c.confidence = CONFIDENCE_STRONG
            c.admission_evidence = [Evidence("NOT_A_HOLE_IN_ANYTHING", {
                "WALL_MATERIAL_SHARE": round(share, 6), "REQUIRED_SHARE": WALL_INTERSECTION_SHARE,
                "PROVENANCE": c.provenance,
                "WHY": "this candidate does not sit in wall material and nothing names it as an opening; a gap "
                       "in open space is not an opening and has nothing to be deducted from"})]
        elif not in_a_wall:
            c.classification = OPENING_CANDIDATE_UNRESOLVED
            c.confidence = CONFIDENCE_WEAK
            c.admission_evidence = [Evidence("NAMED_AS_AN_OPENING_BUT_NOT_IN_A_WALL", {
                "WALL_MATERIAL_SHARE": round(share, 6), "PROVENANCE": c.provenance,
                "WHY": "a block or a schedule row says there is an opening here, and no wall material is here; "
                       "either the wall is missing from the extraction or the opening is misplaced"})]
        elif names_it:
            c.classification = CONFIRMED_OPENING
            c.confidence = (CONFIDENCE_PROVEN if len({p["KIND"] for p in c.provenance}) > 1
                            else CONFIDENCE_STRONG)
            c.admission_evidence = [Evidence("ADMITTED_ON_PROVENANCE", {
                "PROVENANCE": c.provenance, "WALL_MATERIAL_SHARE": round(share, 6),
                "DRAWN_WIDTH_M": round(c.drawn_width, 6),
                "WHY": "the source identifies this as an opening and it sits in wall material"})]
        else:
            c.classification = OPENING_CANDIDATE_UNRESOLVED
            c.confidence = CONFIDENCE_WEAK
            c.admission_evidence = [Evidence("A_GAP_IN_A_WALL_THAT_NOTHING_NAMES", {
                "WALL_MATERIAL_SHARE": round(share, 6), "DRAWN_WIDTH_M": round(c.drawn_width, 6),
                "JAMBS": c.jamb_evidence, "PROVENANCE": c.provenance,
                "NAMED_BY": [],
                "WHY": "the wall stops here and nothing says what fills the gap; a door, an archway and a "
                       "missing line look identical at this point, and they are measured differently"})]

    # ------------------------------------------------ one physical object represented twice
    confirmed = [c for c in candidates if c.classification == CONFIRMED_OPENING]
    confirmed.sort(key=lambda c: (_strength(c), c.candidate_ref), reverse=True)
    kept = []
    for c in confirmed:
        twin = next((k for k in kept if k.floor == c.floor
                     and _overlap_share(k, c) >= DUPLICATE_OVERLAP), None)
        if twin is None:
            kept.append(c)
            continue
        c.classification = DUPLICATE_OF_CONFIRMED_OPENING
        c.duplicate_of = twin.candidate_ref
        c.confidence = CONFIDENCE_PROVEN
        c.admission_evidence = [Evidence("SAME_PHYSICAL_OPENING_AS_ANOTHER_CANDIDATE", {
            "DUPLICATE_OF": twin.candidate_ref, "OVERLAP_SHARE": round(_overlap_share(twin, c), 6),
            "THRESHOLD": DUPLICATE_OVERLAP, "KEPT_BECAUSE": {"REF": twin.candidate_ref,
                                                            "PROVENANCE": twin.provenance},
            "WHY": "two representations occupy the same place in the same wall; counting both would deduct one "
                   "hole twice"})]

    schedule_without_geometry = [r for r in schedule_rows
                                 if r.get("SCHEDULE_REF") not in matched_schedule]
    counts = {k: sum(1 for c in candidates if c.classification == k) for k in CLASSES}
    return {
        "POPULATION": [as_dict(c) for c in sorted(candidates, key=lambda x: x.candidate_ref)],
        "COUNTS": counts,
        "CANDIDATES_IN": len(candidates),
        "PHYSICAL_OPENING_COUNT": counts[CONFIRMED_OPENING],
        "SCHEDULE_ROWS_IN": len(schedule_rows),
        "SCHEDULE_ROWS_MATCHED": len(matched_schedule),
        "SCHEDULE_ROWS_WITHOUT_GEOMETRY": [{"SCHEDULE_REF": r.get("SCHEDULE_REF"), "FLOOR": r.get("FLOOR"),
                                            "TYPE": r.get("TYPE"), "WIDTH_M": r.get("WIDTH_M"),
                                            "WHY": "the schedule describes this opening and no geometry was "
                                                   "extracted for it; it is a question, not a quantity"}
                                           for r in schedule_rows
                                           if r.get("SCHEDULE_REF") not in matched_schedule],
        "CONFIRMED_WITHOUT_A_SCHEDULE_ROW": sorted(c.candidate_ref for c in candidates
                                                   if c.classification == CONFIRMED_OPENING
                                                   and not c.schedule_ref),
        "DRAFTING_RESOLUTION_M": drafting_resolution_m,
        "RULE": "a candidate is admitted on provenance, never on size; size only rejects below the resolution "
                "the source was drawn at; every candidate keeps its reference and leaves with a reason",
        "NAMING_PROVENANCE": list(NAMING_PROVENANCE),
        "CORROBORATING_PROVENANCE": [PROV_JAMB],
        "CLASSES": list(CLASSES),
    }


def as_dict(c):
    return {"CANDIDATE_REF": c.candidate_ref, "FLOOR": c.floor, "ORIGIN": c.origin,
            "TYPE": c.opening_type, "GEOMETRY": c.rect.as_tuple(), "AXIS": c.axis,
            "DRAWN_WIDTH_M": round(c.drawn_width, 6), "DRAWN_DEPTH_M": round(c.drawn_depth, 6),
            "CLASSIFICATION": c.classification, "DUPLICATE_OF": c.duplicate_of,
            "CONFIDENCE": c.confidence, "PROVENANCE": c.provenance,
            "BLOCK_REF": c.block_ref, "SCHEDULE_REF": c.schedule_ref, "LAYER": c.layer,
            "EVIDENCE": [e.as_dict() for e in c.admission_evidence]}


def admitted_openings(candidates, tolerance):
    """The confirmed population, as engine openings, with width and height resolved through the hierarchy.

    An opening leaves this stage carrying the evidence record for each of its two dimensions.  A deduction can
    then be traced to width evidence and height evidence independently, and one that cannot is not computed.
    """
    out = []
    for c in sorted((c for c in candidates if c.classification == CONFIRMED_OPENING),
                    key=lambda x: x.candidate_ref):
        w = EV.resolve("width", list(c.width_claims) + [
            EV.Claim(c.drawn_width, EV.MEASURED_GEOMETRY, c.candidate_ref,
                     {"WHAT": "the clear opening as drawn"})], tolerance)
        h = EV.resolve("height", c.height_claims, tolerance)
        o = Opening(c.candidate_ref, c.rect, c.floor, c.source_revision, opening_type=c.opening_type,
                    width=w["VALUE"] if EV.established(w) else None,
                    height=h["VALUE"] if EV.established(h) else None,
                    width_source=w["SOURCE"], height_source=h["SOURCE"], axis=c.axis, layer=c.layer)
        o.admission = {"CLASSIFICATION": c.classification, "PROVENANCE": c.provenance,
                       "WIDTH_EVIDENCE": w, "HEIGHT_EVIDENCE": h}
        out.append(o)
    return out
