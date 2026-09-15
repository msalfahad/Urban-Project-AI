"""Coverage must divide like by like, and unknown must stay unknown.

The figure being retired was 45.9%: a WALL-BAND length over a SOURCE-STROKE
length. A two-face wall contributes about two source-face lengths and one
band length, so the numerator was deduplicated and the denominator was not.
The ratio understated capture by roughly a factor of two on exactly the
population it claimed to measure — and it looked like a careful number.
"""

import pytest

from engine import source_coverage as sc
from engine import unpaired_strokes as us


class _Face:
    def __init__(self, i, a, b, axis="H", fixed=0.0):
        self.segment_id, self.axis, self.fixed_mm = i, axis, fixed
        self.start_mm, self.end_mm = a, b


class _Band:
    def __init__(self, i, a, b, faces):
        self.wall_band_id = i
        self.start_mm, self.end_mm = a, b
        self.face_a_ids, self.face_b_ids = (faces[0],), (faces[1],)


class _Stroke:
    def __init__(self, i, a, b, cls):
        self.stroke_id, self.start_mm, self.end_mm = i, a, b
        self.stroke_class = cls

    @property
    def length_mm(self):
        return self.end_mm - self.start_mm

    @property
    def is_wall_like(self):
        return self.stroke_class in us.WALL_LIKE_CLASSES


def _fixture():
    """Two faces paired into one band, plus three unpaired strokes."""
    faces = [_Face("F-1", 0.0, 4000.0), _Face("F-2", 0.0, 4000.0),
             _Face("F-3", 0.0, 1000.0), _Face("F-4", 0.0, 500.0),
             _Face("F-5", 0.0, 300.0)]
    bands = [_Band("WB-1", 0.0, 4000.0, ("F-1", "F-2"))]
    strokes = [_Stroke("F-3", 0.0, 1000.0, us.CONFIRMED_SINGLE_LINE_WALL),
               _Stroke("F-4", 0.0, 500.0, us.FIXTURE_OR_SYMBOL),
               _Stroke("F-5", 0.0, 300.0, us.STROKE_UNRESOLVED)]
    return faces, bands, strokes


# --- the primitive --------------------------------------------------------

def test_both_sides_of_every_division_are_source_stroke_length():
    cov = sc.measure(*_fixture())
    # Two 4000 mm faces went into one 4000 mm band. The SOURCE figure is
    # 8000 mm, not 4000: that is the whole point.
    assert cov.used_in_bands_mm == pytest.approx(8000.0)
    assert cov.accepted_band_length_mm == pytest.approx(4000.0)


def test_the_physical_length_is_reported_separately_and_deduplicated():
    r = sc.measure(*_fixture()).record()
    phys = r["physical_wall_length"]
    assert phys["length_m"] == pytest.approx(4.0)
    assert phys["deduplication_basis"] == "TWO_DRAWN_FACES_ARE_ONE_WALL"
    assert "may never be divided into one another" in \
        phys["why_this_is_separate"]


def test_no_physical_length_is_derived_for_unpaired_strokes():
    r = sc.measure(*_fixture()).record()
    assert "NEVER INVENT THE MISSING HALF" in \
        r["physical_wall_length"]["not_derived_for"]


def test_the_record_says_why_one_primitive_is_required():
    r = sc.measure(*_fixture()).record()
    assert "factor of two" in r["why_one_primitive"]
    assert r["primitive"] == sc.PRIMITIVE


# --- the accounting identity ---------------------------------------------

def test_the_parts_add_to_the_total():
    cov = sc.measure(*_fixture())
    assert cov.total_mm == pytest.approx(9800.0)
    assert cov.accounted_mm == pytest.approx(cov.total_mm)
    assert cov.identity_closes
    assert cov.unaccounted_mm == pytest.approx(0.0)


def test_a_face_in_neither_a_band_nor_a_classified_stroke_is_named():
    # An identity nobody checks is where a missing population hides.
    faces, bands, strokes = _fixture()
    faces.append(_Face("F-orphan", 0.0, 2000.0))
    cov = sc.measure(faces, bands, strokes)
    assert not cov.identity_closes
    assert cov.unaccounted_mm == pytest.approx(2000.0)
    assert "unnamed" in cov.notes["identity_warning"]
    assert cov.record()["accounting_identity"]["closes"] is False


# --- unknown stays unknown ------------------------------------------------

def test_unresolved_is_in_neither_the_wall_like_nor_the_non_wall_figure():
    cov = sc.measure(*_fixture())
    assert cov.unresolved_mm == pytest.approx(300.0)
    assert cov.non_wall_mm == pytest.approx(500.0)
    # …and it is excluded from wall-like too.
    assert cov.wall_like_mm == pytest.approx(9000.0)


def test_a_duplicate_is_not_counted_as_non_wall():
    faces, bands, strokes = _fixture()
    faces.append(_Face("F-6", 0.0, 700.0))
    strokes.append(_Stroke("F-6", 0.0, 700.0, us.DUPLICATE))
    cov = sc.measure(faces, bands, strokes)
    assert cov.duplicate_mm == pytest.approx(700.0)
    assert cov.non_wall_mm == pytest.approx(500.0)


def test_the_stroke_summary_keeps_the_three_groups_apart():
    # An earlier report added non-wall, duplicate and unresolved together
    # and called the sum "never a wall", which converted UNRESOLVED from
    # unknown into false.
    faces, bands, strokes = _fixture()
    got = us.summary(strokes)["not_wall_like_length_m"]
    assert got == {"classified_non_wall": 0.5, "duplicate": 0.0,
                   "unresolved": 0.3}


def test_the_summary_says_unresolved_is_not_proven_non_wall():
    what = us.summary([])["what_each_group_means"]
    assert "NOT proven non-wall" in what["unresolved"]
    assert "not an ADDITIONAL wall" in what["duplicate"]


def test_capture_against_wall_like_excludes_unresolved_from_both_terms():
    r = sc.measure(*_fixture()).record()
    cap = r["source_stroke_capture"]
    # 8000 of 9000 wall-like, not 8000 of 9300.
    assert cap["of_wall_like_source_stroke_pct"] == pytest.approx(88.89,
                                                                  abs=0.01)
    assert "leaves UNRESOLVED out of both terms" in cap["basis"]


# --- what the audit refuses to compute -----------------------------------

def test_the_audit_refuses_a_coverage_figure_without_source_totals():
    from engine.source_audit import SourceAudit
    got = SourceAudit("AR-00", "r1", "h",
                      paired_face_length_m=615.1)._coverage_claim()
    assert got["status"] == "NOT_ESTABLISHED"
    assert "band length over source-stroke length" in got["never_compute_here"]


def test_the_audit_reports_the_source_normalised_figure_when_given_one():
    from engine.source_audit import SourceAudit
    cov = sc.measure(*_fixture()).record()
    got = SourceAudit("AR-00", "r1", "h",
                      source_coverage=cov)._coverage_claim()
    assert got["status"] == "ESTABLISHED_IN_SOURCE_STROKE_LENGTH"
    assert got["primitive"] == sc.PRIMITIVE
    assert "ARCHITECTURAL walls" in got["still_not_a_claim_that"]
