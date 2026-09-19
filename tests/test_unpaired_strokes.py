"""851 m of wall-pen stroke is not 851 m of wall.

The claim being retired is `SINGLE_LINE_WALL`, applied to the whole
population because it was drawn with the wall pen. A pen weight says a mark
was made with a particular tool. An architect uses one pen for more than one
thing, so every class below has to be earned from evidence — and the classes
that matter most are the ones that tell a genuinely missing wall apart from a
fixture outline that was never a wall at all.
"""

import pytest

from engine import unpaired_strokes as us


def _one(**kw):
    base = dict(length=2000.0, dup=False, near_gap=None, support=None,
                peers=0)
    base.update(kw)
    return us._classify_one(**base)


def test_the_population_is_named_for_what_is_known_about_it():
    assert us.POPULATION == "UNPAIRED_WALL_STYLE_STROKE"
    assert "SINGLE_LINE_WALL" not in us.POPULATION


def test_the_wall_pen_alone_classifies_nothing():
    # No pen weight reaches the decision at all: _classify_one cannot see it.
    cls, _ = _one()
    assert cls == us.STROKE_UNRESOLVED


def test_a_short_mark_is_a_detail_whatever_pen_drew_it():
    cls, why = _one(length=150.0)
    assert cls == us.ANNOTATION_OR_DETAIL
    assert "150" in why


def test_the_same_mark_found_twice_is_not_two_walls():
    assert _one(dup=True)[0] == us.DUPLICATE


def test_a_duplicate_is_settled_before_length():
    # Order matters: a short duplicate is still a duplicate, and counting it
    # as an annotation would hide that the extractor saw one mark twice.
    assert _one(dup=True, length=100.0)[0] == us.DUPLICATE


def test_a_fragment_beside_an_accepted_band_face_is_that_wall_s_mate():
    cls, why = _one(near_gap=12.0)
    assert cls == us.FRAGMENTED_MATE
    assert "extend an existing band" in why


def test_no_raster_support_means_the_stroke_is_not_masonry():
    assert _one(support=0.1)[0] == us.NON_WALL_GEOMETRY


def test_a_lone_supported_run_is_the_class_the_band_engine_cannot_express():
    cls, why = _one(support=0.9, peers=0)
    assert cls == us.CONFIRMED_SINGLE_LINE_WALL
    assert "no mate" in why


def test_a_supported_run_sharing_its_line_with_others_is_a_fixture():
    assert _one(support=0.9, peers=3)[0] == us.FIXTURE_OR_SYMBOL


def test_unmeasured_support_is_unresolved_not_a_wall():
    # A guess here becomes a wall, and a wall becomes a quantity.
    cls, why = _one(support=None, peers=1)
    assert cls == us.STROKE_UNRESOLVED
    assert "unmeasured" in why


def test_only_three_classes_are_candidates_for_a_missing_wall():
    assert set(us.WALL_LIKE_CLASSES) == {
        us.CONFIRMED_SINGLE_LINE_WALL, us.FRAGMENTED_MATE,
        us.DIFFERENT_WALL_REPRESENTATION}
    for cls in (us.FIXTURE_OR_SYMBOL, us.DUPLICATE, us.ANNOTATION_OR_DETAIL,
                us.NON_WALL_GEOMETRY, us.STROKE_UNRESOLVED):
        assert cls not in us.WALL_LIKE_CLASSES


def test_every_class_carries_a_reason():
    for kw in ({}, {"dup": True}, {"length": 100.0}, {"near_gap": 5.0},
               {"support": 0.1}, {"support": 0.9},
               {"support": 0.9, "peers": 4}):
        cls, why = _one(**kw)
        assert cls in us.CLASSES
        assert len(why) > 20


# --- the end-to-end shape -------------------------------------------------

class _Face:
    def __init__(self, i, axis, fixed, a, b, w=1.14):
        self.segment_id, self.axis, self.fixed_mm = i, axis, fixed
        self.start_mm, self.end_mm, self.stroke_width_pt = a, b, w


class _Band:
    def __init__(self, i, axis, fa, fb):
        self.wall_band_id, self.axis = i, axis
        self.face_a_mm, self.face_b_mm = fa, fb
        self.wall_face_separation_mm = abs(fb - fa)


def test_a_stroke_beside_a_band_face_is_matched_to_that_band():
    faces = [_Face("VS-1", "H", 1020.0, 0.0, 3000.0)]
    bands = [_Band("WB-1", "H", 800.0, 1000.0)]
    got = us.classify(faces, bands)
    assert got[0].nearest_band_id == "WB-1"
    assert got[0].nearest_band_gap_mm == pytest.approx(20.0)
    assert got[0].stroke_class == us.FRAGMENTED_MATE


def test_raster_support_is_recorded_as_evidence_when_it_is_measured():
    faces = [_Face("VS-1", "H", 5000.0, 0.0, 3000.0)]
    got = us.classify(faces, [], raster_support=lambda *a: 0.92)
    assert "RASTER_SHOWS_SOLID_HERE" in got[0].evidence
    assert got[0].raster_support == 0.92
    # …and raster support ALONE no longer supports a wall's existence. A
    # run nothing meets is not part of a wall network.
    assert got[0].stroke_class == us.NON_WALL_GEOMETRY


def test_raster_support_plus_a_wall_network_supports_existence():
    # A perpendicular face meets the run, so it is part of a network.
    faces = [_Face("VS-1", "H", 5000.0, 0.0, 3000.0),
             _Face("VS-2", "V", 1500.0, 4000.0, 6000.0)]
    got = {g.stroke_id: g for g in us.classify(
        faces, [], raster_support=lambda *a: 0.92, wall_pen=1.14)}
    assert got["VS-1"].stroke_class == us.SINGLE_LINE_EXISTENCE_SUPPORTED


def test_the_wall_pen_is_evidence_but_not_a_classification():
    faces = [_Face("VS-1", "H", 5000.0, 0.0, 3000.0, w=1.14),
             _Face("VS-2", "V", 1500.0, 4000.0, 6000.0, w=1.14)]
    got = {g.stroke_id: g for g in us.classify(faces, [], wall_pen=1.14)}
    assert "DRAWN_WITH_THE_WALL_PEN" in got["VS-1"].evidence
    # …and with no raster measurement it still is not called a wall.
    assert got["VS-1"].stroke_class == us.STROKE_UNRESOLVED


def test_the_wrong_pen_leaves_a_stroke_unresolved_not_non_wall():
    faces = [_Face("VS-1", "H", 5000.0, 0.0, 3000.0, w=0.36),
             _Face("VS-2", "V", 1500.0, 4000.0, 6000.0, w=0.36)]
    got = {g.stroke_id: g for g in us.classify(
        faces, [], raster_support=lambda *a: 0.92, wall_pen=1.14)}
    assert got["VS-1"].stroke_class == us.STROKE_UNRESOLVED
    assert "UNRESOLVED and not non-wall" in got["VS-1"].why


def test_the_summary_never_totals_the_population_as_wall():
    faces = [_Face("VS-1", "H", 5000.0, 0.0, 3000.0),
             _Face("VS-2", "H", 9000.0, 0.0, 100.0)]
    s = us.summary(us.classify(faces, []))
    assert s["strokes"] == 2
    assert us.CONFIRMED_SINGLE_LINE_WALL not in str(s.get("population", ""))


# --- what the source audit may and may not claim from this ----------------

def test_the_audit_names_the_population_not_the_guess():
    from engine import source_audit as sa
    assert sa.UNPAIRED_WALL_STYLE_STROKE in sa.WALL_REPRESENTATIONS
    # And the old field name, which asserted the guess, is gone.
    assert not hasattr(sa.SourceAudit("d", "r", "h"), "single_face_length_m")


def test_drawing_wall_coverage_is_refused_without_source_normalised_totals():
    # The retired figure divided a BAND length by a SOURCE-STROKE length.
    # It is not repaired, it is refused; engine.source_coverage computes
    # the real thing from one primitive.
    from engine.source_audit import SourceAudit
    got = SourceAudit("AR-00", "r1", "h", paired_face_length_m=615.1
                      )._coverage_claim()
    assert got["status"] == "NOT_ESTABLISHED"
    assert "same primitive on" in got["why"]
    assert "band length over source-stroke length" in \
        got["never_compute_here"]


def test_the_polygonization_metric_names_its_own_denominator():
    from engine.wall_solid import WallSolid
    got = WallSolid(input_polygons=243, valid=243).record()
    assert got["accepted_band_polygonization_coverage_pct"] == 100.0
    assert got["coverage_denominator"] == "ACCEPTED_WALL_BANDS_ONLY"
    # 100% of the accepted bands is compatible with a drawing whose walls are
    # largely missing from that set, so the drawing-level claim stays open.
    assert got["drawing_wall_representation_coverage"] == "NOT_ESTABLISHED"
    assert "source_coverage_pct" not in got
