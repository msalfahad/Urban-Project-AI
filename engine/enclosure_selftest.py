"""E98 — prove the enclosure ignores the ink it should ignore.

§6. Each fixture is checked three ways:

  1. THE RASTER CONTOUR IS WRONG ON PURPOSE. The mask is traced with the
     same tracer Round 2 used, and the area that contour encloses is
     reported. For a bathroom with a bath, a WC and a basin the contour
     misses a fifth of the room — which is precisely why matching contour
     runs to wall lines could never measure it.

  2. THE ENCLOSURE IS ARITHMETICALLY RIGHT. It must return the area the
     fixture was built with, to the millimetre.

  3. THE REFUSALS REFUSE. A missing wall side, an unvalidated opening, a
     face stopping 50 mm short, or a corner with only one side supported
     must all come back incomplete.

Run before any real drawing is evaluated, and re-run on every change.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np

from engine import space_enclosure as se
from engine.enclosure_fixtures import PX_MM, fixtures
from engine.frames import IDENTITY, Frame
from engine.region_boundary import simplify, trace

# What a failure looks like, named so a regression says what broke.
FAIL_WRONG_AREA = "ENCLOSED_THE_WRONG_AREA"
FAIL_SHOULD_HAVE_REFUSED = "COMPLETED_AN_ENCLOSURE_IT_SHOULD_HAVE_REFUSED"
FAIL_SHOULD_HAVE_CLOSED = "REFUSED_AN_ENCLOSURE_THE_DRAWING_SUPPORTS"
FAIL_FOLLOWED_THE_INK = "FOLLOWED_A_FIXTURE_DETOUR_INTO_THE_ROOM"
FAIL_UNSUPPORTED_EDGE = "AN_EDGE_OF_THE_RESULT_IS_NOT_ON_A_DRAWN_LINE"
FAIL_INVALID = "PRODUCED_AN_INVALID_POLYGON"


@dataclass(frozen=True)
class Outcome:
    fixture: str
    passed: bool
    failures: tuple[str, ...]
    expected_area_m2: float | None
    enclosed_area_m2: float | None
    raster_contour_area_m2: float | None
    raster_contour_runs: int
    verdict: str
    vector_support_pct: float
    corners: int
    note: str = ""

    @property
    def contour_error_m2(self) -> float | None:
        if (self.raster_contour_area_m2 is None
                or self.expected_area_m2 is None):
            return None
        return self.raster_contour_area_m2 - self.expected_area_m2

    def record(self) -> dict:
        return {
            "fixture": self.fixture,
            "passed": self.passed,
            "failures": list(self.failures),
            "expected_area_m2": self.expected_area_m2,
            "ENCLOSED_area_m2": self.enclosed_area_m2,
            "what_the_raster_contour_would_have_given_m2":
                self.raster_contour_area_m2,
            "raster_contour_error_m2": (
                None if self.contour_error_m2 is None
                else round(self.contour_error_m2, 3)),
            "raster_contour_runs": self.raster_contour_runs,
            "verdict": self.verdict,
            "vector_support_pct": self.vector_support_pct,
            "corners_constructed": self.corners,
            "note": self.note,
        }


def _contour(fixture) -> tuple:
    """Area and run count of the traced raster contour, for comparison."""
    mask = fixture.mask()
    lab = mask.astype(np.int32)
    h, w = mask.shape
    frame = Frame(IDENTITY, raster_w_mm=w * PX_MM, raster_h_mm=h * PX_MM,
                  fit=1.0)
    runs = simplify(trace(lab, 1, frame, PX_MM, min_run_px=1))
    if not runs:
        return None, 0
    # The contour's enclosed area, from the mask it was traced from: the
    # pixel count IS what a contour-following measurement would report.
    return float(mask.sum()) * (PX_MM / 1000.0) ** 2, len(runs)


def run(fixture) -> Outcome:
    """Check one fixture three ways."""
    enc = se.enclose(fixture.name, fixture.seed_mm, fixture.candidates,
                     extent=fixture.extent_mm)
    contour_area, contour_runs = _contour(fixture)
    failures = []

    if fixture.expect_complete:
        if not enc.is_complete:
            failures.append(FAIL_SHOULD_HAVE_CLOSED)
        elif abs((enc.area_m2 or 0.0) - fixture.expected_area_m2) > 0.002:
            failures.append(FAIL_WRONG_AREA)
        if enc.is_complete and enc.vector_support_pct < 99.99:
            failures.append(FAIL_UNSUPPORTED_EDGE)
        # Following the ink would produce the CONTOUR's area, not the
        # room's. This is the fixture-detour test, stated as a number.
        if (enc.is_complete and contour_area is not None
                and abs((enc.area_m2 or 0.0) - contour_area) < 1e-9
                and abs(contour_area - fixture.expected_area_m2) > 0.002):
            failures.append(FAIL_FOLLOWED_THE_INK)
        if enc.is_complete:
            from shapely.wkt import loads
            poly = loads(enc.polygon_wkt)
            if not (poly.is_valid and poly.is_simple):
                failures.append(FAIL_INVALID)
    elif enc.is_complete:
        failures.append(FAIL_SHOULD_HAVE_REFUSED)

    return Outcome(
        fixture=fixture.name, passed=not failures,
        failures=tuple(failures),
        expected_area_m2=fixture.expected_area_m2,
        enclosed_area_m2=(None if enc.area_m2 is None
                          else round(enc.area_m2, 4)),
        raster_contour_area_m2=(None if contour_area is None
                                else round(contour_area, 4)),
        raster_contour_runs=contour_runs,
        verdict=enc.verdict,
        vector_support_pct=enc.vector_support_pct,
        corners=len(enc.corners_constructed),
        note=fixture.note)


def run_all() -> list:
    return [run(f) for f in fixtures()]


def report(outcomes=None) -> dict:
    outs = list(outcomes) if outcomes is not None else run_all()
    passed = [o for o in outs if o.passed]
    misled = [o for o in outs
              if o.contour_error_m2 is not None
              and abs(o.contour_error_m2) > 0.002]
    return {
        "ALGORITHM_FREEZE_HASH": se.freeze_hash(),
        "algorithm": se.ALGORITHM,
        "fixtures": len(outs),
        "passed": len(passed),
        "failed": len(outs) - len(passed),
        "failures_by_kind": dict(Counter(
            f for o in outs for f in o.failures)),
        "refusals_expected": sum(1 for o in outs
                                 if o.expected_area_m2 is None),
        "refusals_delivered": sum(
            1 for o in outs
            if o.expected_area_m2 is None and o.passed),
        "fixtures_where_the_raster_contour_is_wrong": len(misled),
        "worst_raster_contour_error_m2": (
            None if not misled else round(max(
                abs(o.contour_error_m2) for o in misled), 3)),
        "total_raster_contour_error_m2": round(sum(
            abs(o.contour_error_m2) for o in misled), 3),
        "outcomes": [o.record() for o in outs],
        "what_this_proves": (
            "the enclosure returns the area each room was BUILT with, "
            "while the traced raster contour of the same room does not. "
            "The contour is wrong by a measured amount on most fixtures "
            "because it follows baths, wardrobes, nosings and door leaves; "
            "the enclosure never sees them, because a fixture is not a "
            "boundary candidate"),
        "what_this_does_not_prove": (
            "anything about a real drawing. These rooms were built to have "
            "known answers, which is what makes them safe to set "
            "thresholds on and useless as evidence of field accuracy"),
    }
