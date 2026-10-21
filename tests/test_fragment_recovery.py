"""Recover the wall that is drawn, without closing what is drawn open.

The pairing engine assumed one face meets one face. A draughtsman routinely
draws one continuous face opposite several collinear fragments, and 289 m of
this sheet is exactly that. The resolver may group them — and may never
invent the missing half, move a face, change a thickness, or bridge a door.

WALL TOPOLOGY IS DOWNSTREAM EVIDENCE ONLY. Nothing in the resolver can see a
room, and these tests never assert on one.
"""

import pytest

from engine import fragment_recovery as fr
from engine import fragment_selftest as fs


class _Face:
    def __init__(self, i, axis, fixed, a, b, pen=1.14):
        self.segment_id, self.axis, self.fixed_mm = i, axis, fixed
        self.start_mm, self.end_mm, self.stroke_width_pt = a, b, pen


class _Portal:
    def __init__(self, i, axis, fixed, a, b, exists=True):
        self.portal_id, self.axis, self.fixed_mm = i, axis, fixed
        self.start_mm, self.end_mm, self.exists = a, b, exists


class _Band:
    def __init__(self, i, axis, centre, a, b, t=200.0):
        self.wall_band_id, self.axis = i, axis
        self.centreline_mm, self.start_mm, self.end_mm = centre, a, b
        self.wall_face_separation_mm = t


def _abutting():
    """§5's first example: [0,5000] opposite three abutting fragments."""
    return [_Face("A", "H", 0.0, 0.0, 5000.0),
            _Face("B1", "H", 200.0, 0.0, 1800.0),
            _Face("B2", "H", 200.0, 1800.0, 3200.0),
            _Face("B3", "H", 200.0, 3200.0, 5000.0)]


# --- the interval algebra -------------------------------------------------

def test_abutting_fragments_pair_the_whole_run():
    g = fr.resolve(_abutting())[0]
    assert g.validation_status == fr.RECOVERY_VALIDATED
    assert g.paired_length_mm == pytest.approx(5000.0)
    assert g.unpaired_length_mm == pytest.approx(0.0)
    assert g.gaps == ()
    assert g.group_kind == fr.GROUP_1_TO_N


def test_an_unexplained_absence_is_not_silently_unioned_through():
    """§5's second example: a 2000 mm gap nothing accounts for."""
    faces = [_Face("A", "H", 0.0, 0.0, 5000.0),
             _Face("B1", "H", 200.0, 0.0, 1500.0),
             _Face("B2", "H", 200.0, 3500.0, 5000.0)]
    g = fr.resolve(faces)[0]
    assert g.validation_status == fr.RECOVERY_DIAGNOSTIC
    assert g.paired_length_mm == pytest.approx(3000.0)
    assert g.unsupported_gap_length_mm == pytest.approx(2000.0)
    assert [gg.reason for gg in g.gaps] == [fr.GAP_UNEXPLAINED]


def test_material_occupies_the_paired_intervals_only():
    faces = [_Face("A", "H", 0.0, 0.0, 5000.0),
             _Face("B1", "H", 200.0, 0.0, 1500.0),
             _Face("B2", "H", 200.0, 3500.0, 5000.0)]
    g = fr.resolve(faces)[0]
    polys = fr.polygons([g], validated_only=False)
    assert len(polys) == 2
    assert sum(p.area for p in polys) == pytest.approx(3000.0 * 200.0)
    assert "paired intervals ONLY" in g.record()["material_occupies"]


def test_the_four_interval_kinds_are_reported_separately():
    faces = [_Face("A", "H", 0.0, 0.0, 5000.0),
             _Face("B1", "H", 200.0, 500.0, 1500.0),
             _Face("B2", "H", 200.0, 3500.0, 4500.0)]
    r = fr.resolve(faces)[0].record()
    for key in ("paired_intervals", "unpaired_intervals",
                "supported_fragment_gaps", "unsupported_fragment_gaps"):
        assert key in r


# --- gaps: only the DRAWING may explain one -----------------------------

def test_a_portal_explains_a_gap():
    faces = [_Face("A", "H", 0.0, 0.0, 5000.0),
             _Face("B1", "H", 200.0, 0.0, 2000.0),
             _Face("B2", "H", 200.0, 2900.0, 5000.0)]
    ports = [_Portal("PT-1", "H", 100.0, 2000.0, 2900.0)]
    g = fr.resolve(faces, portals=ports)[0]
    assert [gg.reason for gg in g.gaps] == [fr.GAP_PORTAL]
    assert g.supported_gap_length_mm == pytest.approx(900.0)
    assert g.unsupported_gap_length_mm == pytest.approx(0.0)
    assert g.validation_status == fr.RECOVERY_VALIDATED
    # …and the door is still a hole: material never covers it.
    assert all(not (s < 2900.0 and e > 2000.0)
               for s, e in g.paired_intervals)


def test_a_crossing_wall_explains_a_gap():
    faces = [_Face("A", "H", 0.0, 0.0, 5000.0),
             _Face("B1", "H", 200.0, 0.0, 2400.0),
             _Face("B2", "H", 200.0, 2600.0, 5000.0)]
    bands = [_Band("WB-X", "V", 2500.0, -2000.0, 400.0)]
    g = fr.resolve(faces, bands=bands)[0]
    assert [gg.reason for gg in g.gaps] == [fr.GAP_CROSSING_WALL]
    assert g.validation_status == fr.RECOVERY_VALIDATED


def test_room_closure_is_not_an_input_to_any_decision():
    # The resolver takes faces, portals, caps and bands. There is nowhere
    # for a room, a label, an area or a raster millimetre to enter.
    import inspect
    params = set(inspect.signature(fr.resolve).parameters)
    for forbidden in ("regions", "labels", "rooms", "areas", "raster",
                      "free_space", "candidates"):
        assert forbidden not in params
    assert "room area" in fr.summary([])["what_decided_acceptance"]


# --- the hard invariant ---------------------------------------------------

def test_a_group_that_would_bridge_a_supported_opening_is_refused():
    # A fragment spans the door, so the paired material would cover it.
    faces = [_Face("A", "H", 0.0, 0.0, 5000.0),
             _Face("B1", "H", 200.0, 0.0, 3000.0),
             _Face("B2", "H", 200.0, 3000.0, 5000.0)]
    ports = [_Portal("PT-1", "H", 100.0, 1000.0, 1900.0)]
    g = fr.resolve(faces, portals=ports)[0]
    assert g.validation_status == fr.RECOVERY_REJECTED
    assert g.reject_reason == fr.REJECT_OPENING
    assert "worse than no resolver" in g.why
    assert g.conflicts


def test_an_unsupported_portal_does_not_veto_a_group():
    # Splitting portal existence from geometry is pointless if a portal
    # nobody has established can still block a wall.
    faces = [_Face("A", "H", 0.0, 0.0, 5000.0),
             _Face("B1", "H", 200.0, 0.0, 3000.0),
             _Face("B2", "H", 200.0, 3000.0, 5000.0)]
    ports = [_Portal("PT-1", "H", 100.0, 1000.0, 1900.0, exists=False)]
    assert fr.resolve(faces, portals=ports)[0].validation_status != \
        fr.RECOVERY_REJECTED


def test_the_summary_states_the_hard_invariant():
    got = fr.summary([])["hard_invariant"]
    assert "MAY OVERLAP A SUPPORTED OPENING" in got
    assert "not trimmed to fit" in got


# --- the evidence gates ---------------------------------------------------

def test_a_wandering_separation_is_two_things_not_one_wall():
    """Two fragments 120 mm apart in thickness are not one fragmented wall.

    Collinearity is decided first, by proximity: B1 and B2 never land on
    one line, so no group ever claims both. The refusal is the absence of
    a group, not a rejected group — the resolver cannot assert a wall it
    has no line for.
    """
    faces = [_Face("A", "H", 0.0, 0.0, 5000.0),
             _Face("B1", "H", 200.0, 0.0, 2500.0),
             _Face("B2", "H", 320.0, 2500.0, 5000.0)]
    for g in fr.resolve(faces):
        both = set(g.side_b_source_ids)
        assert not {"B1", "B2"} <= both, (
            "grouped two fragments that are not on one line")


def test_a_drifting_chain_of_fragments_is_not_one_wall():
    """Single linkage can chain; separation stability is what stops it.

    Each fragment sits within the 1 mm collinearity tolerance of the last,
    so they form one cluster — but the thickness has drifted far more than
    that end to end, and a wall has one thickness.
    """
    drift = fr.SEPARATION_STABILITY_MM + 10.0
    steps = int(drift / fr.COLLINEAR_TOLERANCE_MM) + 1
    faces = [_Face("A", "H", 0.0, 0.0, float(steps) * 600.0)]
    faces += [_Face(f"B{i}", "H", 200.0 + i * fr.COLLINEAR_TOLERANCE_MM,
                    i * 600.0, i * 600.0 + 550.0)
              for i in range(steps)]
    groups = [g for g in fr.resolve(faces) if len(g.side_b_source_ids) > 2]
    assert groups, "expected the chain to be clustered so it can be judged"
    g = groups[0]
    assert g.separation_spread_mm > fr.SEPARATION_STABILITY_MM
    assert g.validation_status == fr.RECOVERY_REJECTED
    assert g.reject_reason == fr.REJECT_SEPARATION


def test_collinearity_is_not_decided_by_a_bucket_boundary():
    """Two fragments 0.6 mm apart are collinear wherever they happen to sit.

    A round(fixed / tol) bucket splits them when they straddle x.5; the
    drawing does not change because of where a bucket edge fell.
    """
    for base in (200.0, 200.3, 200.49, 200.7):
        faces = [_Face("A", "H", 0.0, 0.0, 5000.0),
                 _Face("B1", "H", base, 0.0, 2500.0),
                 _Face("B2", "H", base + 0.6, 2500.0, 5000.0)]
        groups = fr.resolve(faces)
        assert groups, f"no group at base {base}"
        assert set(groups[0].side_b_source_ids) == {"B1", "B2"}, (
            f"bucket boundary split a collinear pair at base {base}")


def test_a_run_that_is_mostly_gap_is_an_assertion_not_a_reading():
    faces = [_Face("A", "H", 0.0, 0.0, 10000.0),
             _Face("B1", "H", 200.0, 0.0, 1000.0),
             _Face("B2", "H", 200.0, 9000.0, 10000.0)]
    g = fr.resolve(faces)[0]
    assert g.validation_status == fr.RECOVERY_REJECTED
    assert g.reject_reason == fr.REJECT_COVERAGE


def test_a_separation_below_a_wall_thickness_is_not_a_wall():
    faces = [_Face("A", "H", 0.0, 0.0, 5000.0),
             _Face("B1", "H", 20.0, 0.0, 2500.0),
             _Face("B2", "H", 20.0, 2500.0, 5000.0)]
    assert fr.resolve(faces) == []          # never even a candidate


def test_one_to_one_is_left_to_the_existing_pairing_engine():
    faces = [_Face("A", "H", 0.0, 0.0, 5000.0),
             _Face("B", "H", 200.0, 0.0, 5000.0)]
    assert fr.resolve(faces) == []


def test_a_face_already_consumed_by_a_band_is_not_regrouped():
    assert fr.resolve(_abutting(), used_face_ids={"A"}) == []


# --- band extension recovery ---------------------------------------------

class _WP:
    def __init__(self, i, lo, hi, a, b, ext=(), axis="H", fixed=1000.0,
                 t=200.0):
        self.wall_band_id, self.axis = i, axis
        self.start_mm, self.end_mm = lo, hi
        self.face_a_mm, self.face_b_mm = fixed, fixed + t
        self.face_a_intervals, self.face_b_intervals = tuple(a), tuple(b)
        self.extensions = tuple(ext)
        self.source_face_ids = (f"{i}-A", f"{i}-B")
        self.ring = ((lo, fixed), (hi, fixed), (hi, fixed + t),
                     (lo, fixed + t), (lo, fixed))

    @property
    def is_resolved(self):
        return True


def _unresolved_band():
    """A band accepted on [2000,3000] whose face A runs the whole way."""
    return _WP("WB-1", 0.0, 3000.0, [(0.0, 3000.0)], [(2000.0, 3000.0)],
               ext=[{"end": "start", "length_mm": 2000.0,
                     "extension_reason": "UNRESOLVED_EXTENSION"}])


def test_a_second_face_drawn_as_fragments_turns_hypothesis_into_material():
    from engine import wall_authority as wa
    wp = _unresolved_band()
    auth = wa.classify_intervals([wp])
    faces = [_Face("F-1", "H", 1200.0, 200.0, 1100.0),
             _Face("F-2", "H", 1200.0, 1100.0, 1900.0)]
    got = fr.recover_extensions(auth.admissions, [wp], faces)
    assert len(got) == 1
    r = got[0]
    assert r.status == fr.EXTENSION_RECOVERED
    assert r.recovered_mm == pytest.approx(1700.0)
    assert "drawn all along" in r.why
    assert set(r.fragment_ids) == {"F-1", "F-2"}


def test_nothing_drawn_there_stays_unresolved():
    from engine import wall_authority as wa
    wp = _unresolved_band()
    got = fr.recover_extensions(
        wa.classify_intervals([wp]).admissions, [wp], [])
    assert got[0].status == fr.EXTENSION_STILL_UNRESOLVED
    assert "NEVER INVENT THE MISSING HALF" in got[0].why


def test_a_recovery_that_would_cross_an_opening_is_refused():
    from engine import wall_authority as wa
    wp = _unresolved_band()
    faces = [_Face("F-1", "H", 1200.0, 0.0, 2000.0)]
    ports = [_Portal("PT-1", "H", 1100.0, 800.0, 1700.0)]
    got = fr.recover_extensions(
        wa.classify_intervals([wp]).admissions, [wp], faces, portals=ports)
    assert got[0].status == fr.EXTENSION_STILL_UNRESOLVED
    assert got[0].opening_conflicts == ("PT-1",)
    assert "worse than leaving a wall unrecovered" in got[0].why


def test_a_recovered_stretch_becomes_established_and_the_rest_does_not():
    from engine import wall_authority as wa
    wp = _unresolved_band()
    faces = [_Face("F-1", "H", 1200.0, 1000.0, 2000.0)]
    recs = fr.recover_extensions(
        wa.classify_intervals([wp]).admissions, [wp], faces)
    auth = wa.classify_intervals([wp], recoveries=recs)
    grounds = {a.grounds: a.length_mm for a in auth.admissions}
    assert grounds[wa.RECOVERED_FRAGMENTED_MATE] == pytest.approx(1000.0)
    assert grounds[wa.UNRESOLVED_EXTENSION] == pytest.approx(1000.0)
    assert wa.RECOVERED_FRAGMENTED_MATE in wa.ESTABLISHED_GROUNDS


def test_the_interval_total_is_unchanged_by_recovery():
    # The accounting identity that caught a real bug: splitting an
    # interval at a recovery boundary must not change the total length,
    # and a clamped-to-nothing subtraction once made it grow.
    from engine import wall_authority as wa
    wp = _unresolved_band()
    faces = [_Face("F-1", "H", 1200.0, 1000.0, 2000.0)]
    recs = fr.recover_extensions(
        wa.classify_intervals([wp]).admissions, [wp], faces)
    before = wa.classify_intervals([wp]).record()["total_length_m"]
    after = wa.classify_intervals([wp],
                                  recoveries=recs).record()["total_length_m"]
    assert before == pytest.approx(after)


def test_subtracting_a_run_that_lies_outside_the_range_changes_nothing():
    assert fr._subtract([(0.0, 100.0)], [(500.0, 600.0)]) == [(0.0, 100.0)]
    assert fr._subtract([(500.0, 600.0)], [(0.0, 100.0)]) == [(500.0, 600.0)]


# --- the known-answer test -----------------------------------------------

class _RealBand:
    def __init__(self, i, axis, lo, hi, a, b):
        self.wall_band_id, self.axis = i, axis
        self.start_mm, self.end_mm = lo, hi
        self.face_a_mm, self.face_b_mm = a, b
        self.wall_face_separation_mm = abs(b - a)


def _cases():
    return fs.cases([_RealBand("WB-1", "H", 0.0, 8000.0, 1000.0, 1200.0)],
                    limit=1)


def test_every_scenario_reconstructs_the_band_that_was_there():
    outs = [fs.run(c) for c in _cases()]
    rep = fs.report(outs)
    assert rep["failed"] == 0, rep["failed_detail"]
    assert rep["cases"] == len(fs.SCENARIOS)


def test_the_answer_is_the_band_not_a_room():
    assert "NOT a room, an area" in fs.report([])["the_answer_is"]


def test_the_opening_scenario_leaves_the_door_open():
    case = next(c for c in _cases()
                if c.scenario == fs.AROUND_AN_OPENING)
    out = fs.run(case)
    assert out.passed
    assert "BRIDGED_THE_SYNTHETIC_OPENING" not in out.failures
    # 8000 mm wall less a 900 mm door.
    assert out.paired_length_mm == pytest.approx(7100.0, abs=1.0)


def test_thickness_and_face_positions_are_never_changed():
    for out in (fs.run(c) for c in _cases()):
        assert "CHANGED_THE_WALL_THICKNESS" not in out.failures
        assert "MOVED_A_WALL_FACE" not in out.failures


def test_material_is_never_invented_beyond_the_fragments():
    for out in (fs.run(c) for c in _cases()):
        assert "INVENTED_MATERIAL" not in out.failures
        assert out.paired_length_mm <= out.true_paired_length_mm + 1.0
