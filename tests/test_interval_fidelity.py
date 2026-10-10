"""A wall polygon must span only what the drawing actually drew.

Every geometric invariant can hold while a polygon puts material across a
doorway: the ring is valid, the union is valid, the area conserves. None of
them knows what the source drew. So the drawn intervals are audited against
the ring directly, and the audit distinguishes three different failures that
a single "coverage" number would merge:

    NEITHER face drawn        the ring crosses nothing
    ONE face, cap-supported   extrapolated, but the band engine can say why
    ONE face, unresolved      the band engine's own note says this extent is
                              NOT established material — and the polygon
                              carries it anyway
"""

import pytest

from engine import interval_fidelity as ifid


class _WP:
    def __init__(self, i, lo, hi, a, b, ext=(), axis="H", fixed=1000.0):
        self.wall_band_id, self.axis = i, axis
        self.start_mm, self.end_mm = lo, hi
        self.face_a_mm, self.face_b_mm = fixed, fixed + 200.0
        self.face_a_intervals, self.face_b_intervals = tuple(a), tuple(b)
        self.extensions = tuple(ext)
        self.ring = ((lo, fixed), (hi, fixed), (hi, fixed + 200.0),
                     (lo, fixed + 200.0), (lo, fixed))

    @property
    def is_resolved(self):
        return True


class _Portal:
    def __init__(self, i, axis, fixed, a, b, exists=True):
        self.portal_id, self.axis, self.fixed_mm = i, axis, fixed
        self.start_mm, self.end_mm, self.exists = a, b, exists


# --- the clean case -------------------------------------------------------

def test_a_band_whose_faces_both_run_its_whole_span_is_clean():
    wp = _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)], [(0.0, 3000.0)])
    rep = ifid.audit([wp])
    assert rep.holds
    assert rep.bridges == []
    assert rep.checked["both_faces_drawn_mm"] == pytest.approx(3000.0)
    assert rep.checked["neither_face_drawn_mm"] == pytest.approx(0.0)


def test_the_three_lengths_add_to_the_span():
    wp = _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)],
             [(0.0, 1000.0), (2000.0, 3000.0)])
    c = ifid.audit([wp]).checked
    assert (c["both_faces_drawn_mm"] + c["one_face_drawn_mm"]
            + c["neither_face_drawn_mm"]) == pytest.approx(c["total_span_mm"])


# --- NEITHER face drawn: the silent bridge -------------------------------

def test_a_ring_spanning_where_neither_face_was_drawn_is_a_defect():
    wp = _WP("WB-1", 0.0, 3000.0,
             [(0.0, 1000.0), (2000.0, 3000.0)],
             [(0.0, 1000.0), (2000.0, 3000.0)])
    rep = ifid.audit([wp])
    assert not rep.holds
    d = rep.defects[0]
    assert d.bridge_class == ifid.BRIDGE_UNEXPLAINED
    assert d.length_mm == pytest.approx(1000.0)
    assert "drawing that does not exist" in d.why


def test_an_established_portal_accounts_for_the_gap():
    wp = _WP("WB-1", 0.0, 3000.0,
             [(0.0, 1000.0), (2000.0, 3000.0)],
             [(0.0, 1000.0), (2000.0, 3000.0)])
    ports = [_Portal("PT-1", "H", 1100.0, 1000.0, 2000.0)]
    rep = ifid.audit([wp], portals=ports, established=lambda p: p.exists)
    assert rep.holds
    b = rep.bridges[0]
    assert b.bridge_class == ifid.BRIDGE_EXPLAINED_BY_PORTAL
    assert b.portal_ids == ("PT-1",)
    # …and the report still says the polygon spans the opening, because the
    # barrier and the solid are then asserting opposite things there.
    assert "the wall solid carries material across the opening" in b.why


def test_a_portal_whose_existence_is_unresolved_explains_nothing():
    # Splitting portal existence from portal geometry is pointless if an
    # unresolved portal can still be used to justify material.
    wp = _WP("WB-1", 0.0, 3000.0,
             [(0.0, 1000.0), (2000.0, 3000.0)],
             [(0.0, 1000.0), (2000.0, 3000.0)])
    ports = [_Portal("PT-1", "H", 1100.0, 1000.0, 2000.0, exists=False)]
    rep = ifid.audit([wp], portals=ports, established=lambda p: p.exists)
    assert not rep.holds
    assert rep.defects[0].bridge_class == ifid.BRIDGE_UNEXPLAINED


def test_a_portal_on_the_other_axis_does_not_explain_this_gap():
    wp = _WP("WB-1", 0.0, 3000.0,
             [(0.0, 1000.0), (2000.0, 3000.0)],
             [(0.0, 1000.0), (2000.0, 3000.0)])
    ports = [_Portal("PT-1", "V", 1100.0, 1000.0, 2000.0)]
    rep = ifid.audit([wp], portals=ports, established=lambda p: p.exists)
    assert not rep.holds


def test_a_discontinuity_smaller_than_the_floor_is_a_numerical_join():
    wp = _WP("WB-1", 0.0, 3000.0,
             [(0.0, 1490.0), (1510.0, 3000.0)],
             [(0.0, 1490.0), (1510.0, 3000.0)])
    assert ifid.audit([wp]).holds


# --- ONE face drawn: three different answers ------------------------------

def test_a_cap_supported_extension_is_reported_and_not_a_defect():
    wp = _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)], [(2000.0, 3000.0)],
             ext=[{"end": "start", "length_mm": 2000.0,
                   "extension_reason": "END_CAP_SUPPORTED"}])
    rep = ifid.audit([wp])
    assert rep.holds
    b = rep.bridges[0]
    assert b.bridge_class == ifid.ONE_FACE_SUPPORTED
    assert b.extension_reason == "END_CAP_SUPPORTED"


def test_an_unresolved_extension_is_a_defect_by_the_engine_s_own_note():
    # The band engine writes "this band's extent beyond the paired interval
    # is NOT established material" — and then the polygon carries it.
    wp = _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)], [(2000.0, 3000.0)],
             ext=[{"end": "start", "length_mm": 2000.0,
                   "extension_reason": "UNRESOLVED_EXTENSION"}])
    rep = ifid.audit([wp])
    assert not rep.holds
    d = rep.defects[0]
    assert d.bridge_class == ifid.ONE_FACE_UNSUPPORTED
    assert "NOT established material" in d.why


def test_one_face_with_no_extension_record_at_all_is_a_defect():
    wp = _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)], [(2000.0, 3000.0)])
    rep = ifid.audit([wp])
    assert not rep.holds
    assert rep.defects[0].bridge_class == ifid.ONE_FACE_UNDECLARED


def test_a_junction_overhang_is_supported():
    wp = _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)], [(0.0, 2900.0)],
             ext=[{"end": "end", "length_mm": 100.0,
                   "extension_reason": "JUNCTION_OVERHANG"}])
    rep = ifid.audit([wp])
    assert rep.holds
    assert rep.bridges[0].bridge_class == ifid.ONE_FACE_SUPPORTED


# --- an audit that cannot run is not a pass -------------------------------

def test_a_polygon_with_no_interval_provenance_cannot_be_passed():
    wp = _WP("WB-1", 0.0, 3000.0, [], [])
    rep = ifid.audit([wp])
    assert not rep.holds
    assert "An audit that cannot run is not a pass" in rep.defects[0].why


def test_an_unresolved_polygon_is_skipped_not_judged():
    class _Refused(_WP):
        @property
        def is_resolved(self):
            return False
    rep = ifid.audit([_Refused("WB-1", 0.0, 3000.0, [], [])])
    assert rep.holds
    assert rep.checked["resolved_wall_polygons"] == 0


# --- the assertion --------------------------------------------------------

def test_assert_no_silent_bridge_names_the_worst_offenders():
    wp = _WP("WB-1", 0.0, 3000.0,
             [(0.0, 1000.0), (2000.0, 3000.0)],
             [(0.0, 1000.0), (2000.0, 3000.0)])
    with pytest.raises(ifid.IntervalFidelityError) as e:
        ifid.assert_no_silent_bridge([wp])
    assert "WB-1" in str(e.value)


def test_defect_classes_are_the_ones_asserting_unestablished_material():
    assert set(ifid.DEFECT_CLASSES) == {
        ifid.BRIDGE_UNEXPLAINED, ifid.ONE_FACE_UNSUPPORTED,
        ifid.ONE_FACE_UNDECLARED}
    assert ifid.ONE_FACE_SUPPORTED not in ifid.DEFECT_CLASSES
    assert ifid.BRIDGE_EXPLAINED_BY_PORTAL not in ifid.DEFECT_CLASSES
