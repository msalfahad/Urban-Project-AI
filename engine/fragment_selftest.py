"""E82 — a known-answer test, built by breaking walls we already accepted.

The resolver has no ground truth to check itself against on a real drawing,
and room areas must not become one. But a known answer can be manufactured
without any room at all: take a wall the pairing engine ALREADY accepted,
cut one of its faces into fragments, hide the original grouping, and see
whether the resolver puts it back.

The answer is the band that was there before. Not a room, not an area, not a
count of walls anybody expected.

Four things must hold for every reconstruction, and three of them are
failures the resolver could plausibly commit:

    IT MUST NOT BRIDGE THE SYNTHETIC OPENING
    IT MUST NOT INVENT MATERIAL the fragments do not cover
    IT MUST NOT CHANGE THE WALL'S THICKNESS
    IT MUST NOT MOVE EITHER FACE
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

# The scenarios, each a way a draughtsman really does break a face.
TWO_EQUAL = "TWO_EQUAL_FRAGMENTS"
THREE_EQUAL = "THREE_EQUAL_FRAGMENTS"
FIVE_EQUAL = "FIVE_EQUAL_FRAGMENTS"
UNEQUAL = "UNEQUAL_FRAGMENTS"
AROUND_AN_OPENING = "FRAGMENTS_AROUND_A_REAL_OPENING"
AT_A_T_JUNCTION = "FRAGMENTS_AT_A_T_JUNCTION"
AT_AN_L_JUNCTION = "FRAGMENTS_AT_AN_L_JUNCTION"

SCENARIOS = (TWO_EQUAL, THREE_EQUAL, FIVE_EQUAL, UNEQUAL,
             AROUND_AN_OPENING, AT_A_T_JUNCTION, AT_AN_L_JUNCTION)

# How exactly the reconstruction must match the original.
THICKNESS_TOLERANCE_MM = 0.5
FACE_POSITION_TOLERANCE_MM = 0.5
# Paired length may fall short of the original by the synthetic gaps, but
# may never EXCEED it: that would be invented material.
INVENTION_TOLERANCE_MM = 1.0


class _Face:
    """A source face, as the resolver sees one."""

    def __init__(self, i, axis, fixed, a, b, pen=1.14):
        self.segment_id, self.axis, self.fixed_mm = i, axis, fixed
        self.start_mm, self.end_mm, self.stroke_width_pt = a, b, pen


class _Portal:
    def __init__(self, i, axis, fixed, a, b, exists=True):
        self.portal_id, self.axis, self.fixed_mm = i, axis, fixed
        self.start_mm, self.end_mm, self.exists = a, b, exists


class _Band:
    def __init__(self, i, axis, centre, a, b):
        self.wall_band_id, self.axis = i, axis
        self.centreline_mm, self.start_mm, self.end_mm = centre, a, b
        self.wall_face_separation_mm = 200.0


@dataclass(frozen=True)
class Case:
    """One fragmented wall with its answer kept out of the resolver."""

    case_id: str
    scenario: str
    faces: tuple
    portals: tuple = ()
    caps: tuple = ()
    bands: tuple = ()
    # The hidden answer.
    true_axis: str = "H"
    true_face_a_mm: float = 0.0
    true_face_b_mm: float = 0.0
    true_paired_intervals: tuple = ()
    opening_mm: tuple | None = None

    @property
    def true_thickness_mm(self) -> float:
        return abs(self.true_face_b_mm - self.true_face_a_mm)

    @property
    def true_paired_length_mm(self) -> float:
        return sum(e - s for s, e in self.true_paired_intervals)


@dataclass(frozen=True)
class Outcome:
    case_id: str
    scenario: str
    reconstructed: bool
    validation_status: str = ""
    failures: tuple[str, ...] = ()
    paired_length_mm: float = 0.0
    true_paired_length_mm: float = 0.0
    thickness_mm: float = 0.0
    true_thickness_mm: float = 0.0
    fragments: int = 0
    why: str = ""

    @property
    def passed(self) -> bool:
        return not self.failures

    def record(self) -> dict:
        return {"case_id": self.case_id, "scenario": self.scenario,
                "reconstructed": self.reconstructed,
                "validation_status": self.validation_status,
                "passed": self.passed, "failures": list(self.failures),
                "paired_length_mm": round(self.paired_length_mm, 1),
                "true_paired_length_mm": round(
                    self.true_paired_length_mm, 1),
                "thickness_mm": round(self.thickness_mm, 1),
                "true_thickness_mm": round(self.true_thickness_mm, 1),
                "fragments": self.fragments, "why": self.why}


def _cut(lo: float, hi: float, parts) -> list:
    """Cut [lo, hi] into the given proportions."""
    total = sum(parts)
    out, cur = [], lo
    for w in parts:
        nxt = cur + (hi - lo) * w / total
        out.append((cur, nxt))
        cur = nxt
    return out


def cases(bands, *, limit: int = 3) -> list:
    """Build the scenarios from REAL accepted bands, deterministically."""
    usable = sorted(
        (b for b in bands
         if getattr(b, "wall_face_separation_mm", None)
         and b.face_a_mm is not None and b.face_b_mm is not None
         and abs(b.end_mm - b.start_mm) >= 3000.0),
        key=lambda b: (-abs(b.end_mm - b.start_mm), b.wall_band_id))[:limit]

    out, n = [], 0
    for b in usable:
        lo, hi = min(b.start_mm, b.end_mm), max(b.start_mm, b.end_mm)
        a_at, b_at = b.face_a_mm, b.face_b_mm
        for scenario in SCENARIOS:
            n += 1
            out.append(_case(f"SC-{n:04d}", scenario, b.axis, a_at, b_at,
                             lo, hi))
    return out


def _case(cid, scenario, axis, a_at, b_at, lo, hi) -> Case:
    """One scenario, with the continuous face A and a fragmented face B."""
    faces = [_Face(f"{cid}-A", axis, a_at, lo, hi)]
    portals, caps, bands = [], [], []
    opening = None

    if scenario == TWO_EQUAL:
        parts = _cut(lo, hi, [1, 1])
    elif scenario == THREE_EQUAL:
        parts = _cut(lo, hi, [1, 1, 1])
    elif scenario == FIVE_EQUAL:
        parts = _cut(lo, hi, [1, 1, 1, 1, 1])
    elif scenario == UNEQUAL:
        parts = _cut(lo, hi, [5, 1, 3, 1])
    elif scenario == AROUND_AN_OPENING:
        # The realistic case, and the one that matters: face A runs
        # CONTINUOUSLY past a real 900 mm door while face B is broken by
        # it. If the resolver unions B's fragments and pairs the whole of
        # A against them, it has just built a wall across a doorway.
        #
        # (Cutting BOTH faces at the opening is not this test: that is two
        # ordinary 1-to-1 pairs, which the existing pairing engine handles
        # and this resolver correctly declines.)
        mid = 0.5 * (lo + hi)
        o_lo, o_hi = mid - 450.0, mid + 450.0
        opening = (o_lo, o_hi)
        parts = [(lo, o_lo), (o_hi, hi)]
        portals.append(_Portal(f"{cid}-PT", axis,
                               0.5 * (a_at + b_at), o_lo, o_hi))
    elif scenario == AT_A_T_JUNCTION:
        # A wall on the other axis lands mid-run and breaks face B.
        mid = 0.5 * (lo + hi)
        parts = [(lo, mid - 100.0), (mid + 100.0, hi)]
        bands.append(_Band(f"{cid}-T", "V" if axis == "H" else "H",
                           mid, min(a_at, b_at) - 2000.0,
                           min(a_at, b_at)))
    else:                                     # AT_AN_L_JUNCTION
        parts = [(lo, hi - 1200.0), (hi - 1000.0, hi)]
        bands.append(_Band(f"{cid}-L", "V" if axis == "H" else "H",
                           hi - 1100.0, min(a_at, b_at) - 2000.0,
                           min(a_at, b_at)))

    for i, (s, e) in enumerate(parts, 1):
        if e - s <= 0:
            continue
        faces.append(_Face(f"{cid}-B{i}", axis, b_at, s, e))

    a_runs = [(min(f.start_mm, f.end_mm), max(f.start_mm, f.end_mm))
              for f in faces if f.fixed_mm == a_at]
    true = []
    for a_lo, a_hi in a_runs:
        for s, e in parts:
            x, y = max(a_lo, s), min(a_hi, e)
            if y > x:
                true.append((x, y))

    return Case(case_id=cid, scenario=scenario, faces=tuple(faces),
                portals=tuple(portals), caps=tuple(caps),
                bands=tuple(bands), true_axis=axis, true_face_a_mm=a_at,
                true_face_b_mm=b_at, true_paired_intervals=tuple(true),
                opening_mm=opening)


def run(case: Case) -> Outcome:
    """Hand the resolver the fragments ONLY, then check its answer."""
    from engine.fragment_recovery import resolve

    groups = resolve(list(case.faces), portals=list(case.portals),
                     caps=list(case.caps), bands=list(case.bands),
                     drawing_id="SELFTEST")
    if not groups:
        return Outcome(case.case_id, case.scenario, reconstructed=False,
                       true_paired_length_mm=case.true_paired_length_mm,
                       true_thickness_mm=case.true_thickness_mm,
                       failures=("NO_GROUP_PROPOSED",),
                       why=("the resolver proposed nothing for a wall the "
                            "pairing engine had already accepted"))

    g = max(groups, key=lambda x: x.paired_length_mm)
    failures = []

    if abs(g.thickness_mm - case.true_thickness_mm) > THICKNESS_TOLERANCE_MM:
        failures.append("CHANGED_THE_WALL_THICKNESS")
    for got, want in ((g.side_a_mm, case.true_face_a_mm),
                      (g.side_b_mm, case.true_face_b_mm)):
        if abs(got - want) > FACE_POSITION_TOLERANCE_MM:
            failures.append("MOVED_A_WALL_FACE")
            break
    if (g.paired_length_mm
            > case.true_paired_length_mm + INVENTION_TOLERANCE_MM):
        failures.append("INVENTED_MATERIAL")
    if case.opening_mm is not None:
        o_lo, o_hi = case.opening_mm
        covered = sum(max(0.0, min(e, o_hi) - max(s, o_lo))
                      for s, e in g.paired_intervals)
        if covered > INVENTION_TOLERANCE_MM:
            failures.append("BRIDGED_THE_SYNTHETIC_OPENING")

    return Outcome(
        case_id=case.case_id, scenario=case.scenario, reconstructed=True,
        validation_status=g.validation_status, failures=tuple(failures),
        paired_length_mm=g.paired_length_mm,
        true_paired_length_mm=case.true_paired_length_mm,
        thickness_mm=g.thickness_mm,
        true_thickness_mm=case.true_thickness_mm,
        fragments=len(g.side_b_source_ids),
        why=g.why)


def report(outcomes) -> dict:
    failed = [o for o in outcomes if not o.passed]
    return {
        "cases": len(outcomes),
        "passed": sum(1 for o in outcomes if o.passed),
        "failed": len(failed),
        "by_scenario": dict(Counter(o.scenario for o in outcomes)),
        "failures_by_kind": dict(Counter(
            f for o in outcomes for f in o.failures)),
        "by_validation_status": dict(Counter(
            o.validation_status for o in outcomes if o.reconstructed)),
        "the_answer_is": (
            "the band the pairing engine already accepted, before one of "
            "its faces was cut up. NOT a room, an area, or a count of walls "
            "anybody expected"),
        "what_must_hold": [
            "must not bridge the synthetic opening",
            "must not invent material the fragments do not cover",
            "must not change the wall's thickness",
            "must not move either face",
        ],
        "detail": [o.record() for o in outcomes],
        "failed_detail": [o.record() for o in failed],
    }
