"""E94 — ask the document and the geometry the same question, separately.

§18. The printed dimension and the vector measurement are two answers to
one question about SIZE. The valuable thing is whether they agree; the
worthless thing — and the dangerous one — is their average.

    AGREE       the drawing says what the geometry measures
    DISAGREE    one of them is wrong and nobody yet knows which
    AMBIGUOUS   more than one reading fits, or the pairing is unclear
    NOT_PRESENT nothing was printed near this edge

NEVER AVERAGE THEM. A mean of a printed 1850 and a measured 1902 is a
number that appears on no drawing and describes no building. A material
disagreement is a BLOCK, to be resolved by a human or a better source, and
this is a far stronger use of a document reading than letting it measure.

Also enforced here: a dimension agreement supports the GEOMETRY and never
the IDENTITY. `document_observations.require_use` raises if anybody tries,
and this module only ever asks for SIZE_EVIDENCE.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from engine.document_observations import USE_FOR_SIZE

AGREE = "AGREE"
DISAGREE = "DISAGREE"
AMBIGUOUS = "AMBIGUOUS"
NOT_PRESENT = "NOT_PRESENT"

# How close counts as agreement. Set from what the instruments can do, not
# from what makes more rows agree: the printed value is rounded to the
# nearest 50 mm on this sheet, the vector faces are measured to ~0.01 mm,
# and the finish-face convention can legitimately differ by a plaster coat.
AGREE_TOLERANCE_MM = 30.0
# Beyond this the two are not describing the same edge at all.
MATERIAL_DISAGREEMENT_MM = 100.0
# A printed dimension must sit this close to the edge it dimensions.
ANCHOR_REACH_MM = 1500.0


@dataclass(frozen=True)
class Comparison:
    subject: str                 # what was compared (a candidate, an edge)
    verdict: str
    printed_mm: float | None = None
    measured_mm: float | None = None
    difference_mm: float | None = None
    observation_ids: tuple[str, ...] = ()
    blocks_release: bool = False
    why: str = ""

    def record(self) -> dict:
        return {
            "subject": self.subject,
            "verdict": self.verdict,
            "printed_mm": self.printed_mm,
            "vector_measured_mm": (None if self.measured_mm is None
                                   else round(self.measured_mm, 1)),
            "difference_mm": (None if self.difference_mm is None
                              else round(self.difference_mm, 1)),
            "observation_ids": list(self.observation_ids),
            "blocks_release": self.blocks_release,
            "never_averaged": (
                "the two values are reported side by side. Their mean "
                "would be a number that appears on no drawing and "
                "describes no building"),
            "supports": "GEOMETRY_VALIDATION_ONLY_NOT_IDENTITY",
            "why": self.why,
        }


@dataclass
class Report:
    rows: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def record(self) -> dict:
        by = Counter(r.verdict for r in self.rows)
        return {
            "comparisons": len(self.rows),
            "by_verdict": dict(by),
            "AGREE": by.get(AGREE, 0),
            "DISAGREE": by.get(DISAGREE, 0),
            "AMBIGUOUS": by.get(AMBIGUOUS, 0),
            "NOT_PRESENT": by.get(NOT_PRESENT, 0),
            "material_disagreements_blocking_release": sum(
                1 for r in self.rows if r.blocks_release),
            "agreement_tolerance_mm": AGREE_TOLERANCE_MM,
            "material_disagreement_mm": MATERIAL_DISAGREEMENT_MM,
            "tolerance_basis": (
                "the printed values on this sheet are rounded to the "
                "nearest 50 mm, the vector faces are measured to ~0.01 mm, "
                "and a finish-face convention can legitimately differ by a "
                "plaster coat. Set from the instruments, not from what "
                "makes more rows agree"),
            "rows": [r.record() for r in self.rows],
            "what_this_is_for": (
                "asking the document and the geometry the same question "
                "about SIZE and reporting whether they agree. It is a much "
                "stronger use of a document reading than letting it "
                "measure"),
            "what_this_may_never_do": (
                "average the two, or lift a room's identity. A printed "
                "3.50 matching a measured 3497 proves the SIZE is right "
                "and says nothing about WHICH ROOM it is"),
            "notes": dict(self.notes),
        }


def clear_extents(candidate) -> dict:
    """The room's clear width and depth, from its MATCHED faces only.

    This is what a printed dimension on a plan actually dimensions: the
    distance between two opposite finish faces, not the length of one
    fragment of one face. Comparing a printed 3850 against each matched
    interval's own length — which an earlier version of this module did —
    produced 137 "material disagreements" that were an artefact of the
    pairing, because a room's side is routinely matched as three separate
    drawn intervals.
    """
    out: dict = {}
    for axis, key in (("H", "depth"), ("V", "width")):
        fixed = sorted({round(i.fixed_mm, 3) for i in candidate.intervals
                        if i.axis == axis and i.is_measured})
        if len(fixed) >= 2:
            out[key] = {
                "axis": axis,
                "value_mm": fixed[-1] - fixed[0],
                "between_faces_mm": [fixed[0], fixed[-1]],
                "faces_on_this_axis": len(fixed),
            }
    return out


def compare_extents(candidate, observations, *, subject: str = "",
                    anchor_reach_mm: float = ANCHOR_REACH_MM) -> list:
    """Compare the room's clear extents against the dimensions printed on it.

    A printed dimension is matched to an extent by ORIENTATION and by
    sitting near the room: a dimension string running across the room's
    width is a candidate reading of that width. Where several fit, the
    verdict is AMBIGUOUS rather than the closest one — picking the nearest
    is how a wrong pairing becomes a confident agreement.
    """
    out = []
    extents = clear_extents(candidate)
    if not extents:
        return out

    # The room's own footprint, for deciding which dimensions are "near".
    xs = [i.fixed_mm for i in candidate.intervals
          if i.axis == "V" and i.is_measured]
    ys = [i.fixed_mm for i in candidate.intervals
          if i.axis == "H" and i.is_measured]
    if not xs or not ys:
        return out
    box = (min(xs), min(ys), max(xs), max(ys))

    for key, ext in sorted(extents.items()):
        measured = ext["value_mm"]
        near = []
        for obs in observations:
            if obs.parsed_value_mm is None or obs.anchor_mm is None:
                continue
            obs.require_use(USE_FOR_SIZE)          # raises on misuse
            ax, ay = obs.anchor_mm
            if not (box[0] - anchor_reach_mm <= ax <= box[2] + anchor_reach_mm
                    and box[1] - anchor_reach_mm <= ay
                    <= box[3] + anchor_reach_mm):
                continue
            # A distance is dimensioned by a string written ALONG it. The
            # drawing's x and y are the PDF's own (unrotated) axes, the
            # same ones the glyph localiser measures its bounding boxes
            # in, so an x-extent pairs with a string that is wide —
            # HORIZONTAL — and a y-extent with a tall one. Getting this
            # backwards paired every room's width against its own depth
            # and reported the whole sheet as disagreeing.
            want = "HORIZONTAL" if ext["axis"] == "V" else "VERTICAL"
            if getattr(obs, "orientation", "") not in ("", want):
                continue
            near.append(obs)

        label = f"{subject}/{key}" if subject else key
        if not near:
            out.append(Comparison(
                subject=label, verdict=NOT_PRESENT, measured_mm=measured,
                why=("no parsed printed dimension of the right orientation "
                     f"sits within {anchor_reach_mm:.0f} mm of this room. "
                     "Nothing to cross-check against — which is not a "
                     "disagreement")))
            continue

        fits = [o for o in near
                if abs(o.parsed_value_mm - measured) <= AGREE_TOLERANCE_MM]
        if len(fits) >= 1:
            obs = min(fits, key=lambda o: abs(o.parsed_value_mm - measured))
            diff = obs.parsed_value_mm - measured
            out.append(Comparison(
                subject=label, verdict=AGREE,
                printed_mm=obs.parsed_value_mm, measured_mm=measured,
                difference_mm=diff,
                observation_ids=tuple(o.observation_id for o in fits),
                why=(f"the drawing prints {obs.parsed_value_mm:.0f} and the "
                     f"vector faces measure {measured:.0f} — "
                     f"{abs(diff):.0f} mm apart, within the stated "
                     "tolerance. Two instruments, one answer")))
            continue

        best = min(near, key=lambda o: abs(o.parsed_value_mm - measured))
        diff = best.parsed_value_mm - measured
        material = abs(diff) >= MATERIAL_DISAGREEMENT_MM
        # A DISAGREEMENT REQUIRES AN UNAMBIGUOUS PAIRING. A room on a busy
        # sheet has several dimension strings of the right orientation
        # near it, most of them dimensioning the wall, the window or the
        # next room along; measured on AR-00, BTH-01's depth was paired
        # against the 2350 belonging to the dressing room beside it. With
        # more than one candidate and none agreeing, which string belongs
        # to this extent is simply not established, and that is AMBIGUOUS.
        unpaired = (len(near) > 1
                    or abs(diff) > max(measured, 1.0) * 0.5)
        out.append(Comparison(
            subject=label,
            verdict=AMBIGUOUS if unpaired else
            (DISAGREE if material else AGREE),
            printed_mm=best.parsed_value_mm, measured_mm=measured,
            difference_mm=diff,
            observation_ids=(best.observation_id,),
            blocks_release=material and not unpaired,
            why=(f"the closest printed dimension is "
                 f"{best.parsed_value_mm:.0f} and the clear extent measures "
                 f"{measured:.0f}: {abs(diff):.0f} mm apart. "
                 + (f"{len(near)} printed dimension(s) of this "
                    "orientation sit near the room and none agrees, so "
                    "which one dimensions this extent is not established. "
                    "AMBIGUOUS rather than a disagreement about size"
                    if unpaired else
                    "Material — one of them is wrong and nobody yet knows "
                    "which, so release is BLOCKED and a human or a better "
                    "source must resolve it"))))
    return out


def assess(pairs, observations) -> Report:
    """`pairs` is an iterable of (subject_label, MeasuredSpaceCandidate)."""
    obs = list(observations)
    rep = Report()
    for label, cand in pairs:
        rep.rows.extend(compare_extents(cand, obs, subject=label))
    rep.notes["observations_available"] = len(obs)
    rep.notes["what_is_compared"] = (
        "the room's CLEAR EXTENT between opposite matched faces, against "
        "the dimensions printed on that room. Not each matched interval's "
        "own length: a room's side is routinely drawn as three separate "
        "intervals, and comparing a printed 3850 against each of them "
        "manufactures disagreements")
    return rep
