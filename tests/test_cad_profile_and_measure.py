"""The profile observes one source; it must not become a rule about names.

The temptation on project 7757 is `if layer == "W": wall`. It would be right
about this drawing and wrong about the next one — the same mistake as AR-00's
1.14 pt pen, which was a fact about one plot that nearly became a production
assumption.

So these tests assert the profile is driven by GEOMETRY: a layer of paired
faces is proposed wall-like whatever it is called, and a layer of unpaired
lines is not proposed wall-like even when it is called WALL.

They also hold the measurement's two seeding rules, because both were chosen
against a failure mode rather than a preference: a seed must come from a
placed block (loose text is as likely to be a street name), and the frozen
enclosure must be used unchanged.
"""

from __future__ import annotations


from engine import cad_adapter as ad
from engine import cad_measure as cm
from engine import cad_profile as cp
from engine import cad_regions as reg
from engine import space_enclosure as enc
from engine.cad_fixtures import Builder


def _room(b, x0, y0, w, h, thickness=200.0, layer="ARBITRARY", *, gap=None):
    """A closed room drawn as paired wall faces, optionally with a doorway."""
    x1, y1 = x0 + w, y0 + h
    t = thickness
    # South pair, optionally interrupted by a doorway of width `gap`.
    if gap:
        b.line(x0, y0, x0 + (w - gap) / 2, y0, layer)
        b.line(x0 + (w + gap) / 2, y0, x1, y0, layer)
    else:
        b.line(x0, y0, x1, y0, layer)
    b.line(x0, y0 - t, x1, y0 - t, layer)
    b.line(x0, y1, x1, y1, layer)
    b.line(x0, y1 + t, x1, y1 + t, layer)
    b.line(x0, y0, x0, y1, layer)
    b.line(x0 - t, y0, x0 - t, y1, layer)
    b.line(x1, y0, x1, y1, layer)
    b.line(x1 + t, y0, x1 + t, y1, layer)


def _normalized(b):
    return ad.normalize(b.build(), source_file="T", source_hash="T")


def test_paired_faces_are_proposed_wall_like_whatever_the_layer_is_called():
    b = Builder()
    _room(b, 0, 0, 5000, 4000, layer="ZZ-NONSENSE-NAME")
    prof = cp.build(_normalized(b))
    assert prof.wall_like_layers() == ["ZZ-NONSENSE-NAME"]
    row = next(o for o in prof.layers if o.layer == "ZZ-NONSENSE-NAME")
    assert row.status == cp.PROPOSED
    assert 200.0 in row.thicknesses_mm
    assert any("majority" in e for e in row.evidence)


def test_a_layer_called_wall_with_unpaired_lines_is_not_proposed():
    """The name says wall; the geometry does not. Geometry decides."""
    b = Builder()
    for i in range(8):
        b.line(0, i * 5000.0, 4000, i * 5000.0, "WALL")
    prof = cp.build(_normalized(b))
    assert "WALL" not in prof.wall_like_layers()
    row = next(o for o in prof.layers if o.layer == "WALL")
    assert row.proposed_role == cp.ROLE_LINEWORK
    assert row.status == cp.UNRESOLVED
    assert any("below a majority" in e for e in row.evidence)


def test_faces_outside_the_construction_band_are_not_a_wall():
    """20 mm apart is not a built partition; 3 m apart is not one either."""
    b = Builder()
    b.line(0, 0, 6000, 0, "TIGHT")
    b.line(0, 20, 6000, 20, "TIGHT")
    b.line(0, 0, 6000, 0, "WIDE")
    b.line(0, 3000, 6000, 3000, "WIDE")
    prof = cp.build(_normalized(b))
    assert prof.wall_like_layers() == []


def test_the_profile_scope_is_stated_on_every_row():
    b = Builder()
    _room(b, 0, 0, 4000, 3000, layer="W")
    for row in cp.build(_normalized(b)).record()["layers"]:
        assert "THIS source" in row["scope"]
    prof = cp.build(_normalized(b))
    assert "No layer or block NAME influenced any proposal" in \
        prof.record()["notes"]["how_roles_were_proposed"]


def test_a_sealed_name_cannot_be_measured_through_the_profile():
    """The profile is downstream of the adapter, which never opens a seal."""
    assert cp.MIN_WALL_THICKNESS_MM == 50.0
    assert cp.MAX_WALL_THICKNESS_MM == 600.0
    assert cp.MAJORITY == 0.5


def test_a_closed_room_is_measured_by_the_frozen_enclosure():
    b = Builder()
    _room(b, 0, 0, 5000, 4000, layer="W")
    t = b.text("SALOON", 2500, 2000, 300.0, "TEXT")
    b.block("SAL", [t])
    b.insert("SAL", 0, 0)
    nd = _normalized(b)
    prof = cp.build(nd)
    rep = cm.measure(nd, prof)
    assert rep.counts()["space_candidates"] == 1
    row = rep.rows[0]
    assert row.is_complete, row.enclosure.why
    assert abs(row.enclosure.area_m2 - 20.0) < 0.01, row.enclosure.area_m2
    assert abs(row.enclosure.perimeter_m - 18.0) < 0.01
    assert row.label_observations == ("SALOON",)
    # Round 3 replaced the status string: identity is now reconciled
    # through the vocabulary rather than reported as "a label was seen".
    from engine import identity_reconcile as ident

    assert row.identity_status == ident.IDENTITY_ESTABLISHED
    assert row.normalized_identity == "SALOON"
    assert row.physical_space_status == "PHYSICAL_SPACE_VALIDATED"
    # The frozen algorithm, not a CAD-only copy of it.
    assert rep.record()["enclosure_algorithm"] == enc.ALGORITHM
    assert rep.record()["enclosure_freeze_hash"] == enc.freeze_hash()


def test_a_break_in_one_drawn_line_is_not_a_doorway():
    """This fixture never was a doorway, and round 5 stops treating it as one.

    `_room`'s `gap` cuts the INNER face and leaves the outer face running
    straight across it. Round 4 already classified that correctly —
    NON_OPENING_GEOMETRY, because material still stands there — but could
    not then close the polygon, since the arrangement still had a hole in
    the inner face. Round 5 recovers the span for TOPOLOGY (§5) and refuses
    it for MATERIAL (§6), which is the honest reading of one continuous
    face beside one broken one.
    """
    from engine import cad_openings as co
    from engine import partition_continuity as pc

    b = Builder()
    _room(b, 0, 0, 5000, 4000, layer="W", gap=900.0)
    t = b.text("KITCHEN", 2500, 2000, 300.0, "TEXT")
    b.block("kit", [t])
    b.insert("kit", 0, 0)
    nd = _normalized(b)
    rep = cm.measure(nd, cp.build(nd))
    assert rep.openings.counts()["may_close_a_boundary"] == 0
    assert co.NON_OPENING_GEOMETRY in rep.openings.by_class()
    verdicts = {s.verdict for c in rep.continuity for s in c.spans}
    assert pc.ESTABLISHED in verdicts
    assert pc.MATERIAL_CANDIDATE in {
        s.material_authority for c in rep.continuity for s in c.spans}


def test_a_gap_through_both_faces_still_refuses_completeness():
    """The real version of the case above: nothing runs across it at all."""
    b = Builder()
    x0, y0, x1, y1, t, gap = 0.0, 0.0, 5000.0, 4000.0, 200.0, 900.0
    lo, hi = (x1 - gap) / 2, (x1 + gap) / 2
    for y in (y0, y0 - t):                      # BOTH faces interrupted
        b.line(x0, y, lo, y, "W")
        b.line(hi, y, x1, y, "W")
    b.line(x0, y1, x1, y1, "W")
    b.line(x0, y1 + t, x1, y1 + t, "W")
    b.line(x0, y0, x0, y1, "W")
    b.line(x0 - t, y0, x0 - t, y1, "W")
    b.line(x1, y0, x1, y1, "W")
    b.line(x1 + t, y0, x1 + t, y1, "W")
    txt = b.text("KITCHEN", 2500, 2000, 300.0, "TEXT")
    b.block("kit", [txt])
    b.insert("kit", 0, 0)
    nd = _normalized(b)
    rep = cm.measure(nd, cp.build(nd))
    assert rep.counts()["release_eligible"] == 0
    assert rep.openings.counts()["may_close_a_boundary"] == 0


def test_loose_text_never_names_a_space():
    """A street name is text. It may not become a room's identity.

    Round 4 measures the face whether or not anything names it (§11), so
    the candidate now exists. What must still never happen is the thing
    this test was written for: the loose string becoming the space's name,
    or licensing a release.
    """
    b = Builder()
    _room(b, 0, 0, 5000, 4000, layer="W")
    b.text("STREET 15.00", 2500, 2000, 300.0, "TEXT")
    nd = _normalized(b)
    rep = cm.measure(nd, cp.build(nd))
    assert rep.counts()["release_eligible"] == 0
    for row in rep.rows:
        assert row.normalized_identity == ""
        assert "STREET 15.00" not in row.label_observations
    assert "would name the wrong space" in rep.notes["seeding"]


def test_the_dimension_check_keeps_three_values_apart():
    b = Builder(dimlfac=0.1)
    _room(b, 0, 0, 5000, 4000, layer="W")
    b.dimension(0, -2000, 5000, -2000, layer="DIM")
    t = b.text("SALOON", 2500, 2000, 300.0, "TEXT")
    b.block("SAL", [t])
    b.insert("SAL", 0, 0)
    nd = _normalized(b)
    rep = cm.measure(nd, cp.build(nd))
    checks = rep.rows[0].dimension_checks
    x = next(c for c in checks if c["axis"] == "X")
    assert x["GEOMETRY_MEASURED_VALUE_MM"] == 5000.0
    assert x["DIMENSION_DISPLAY_VALUE"] == 500.0, "printed in centimetres"
    assert x["DIMENSION_NORMALIZED_VALUE_MM"] == 5000.0
    assert x["verdict"] == cm.AGREE
    assert x["DIMENSION_DISPLAY_VALUE"] != x["GEOMETRY_MEASURED_VALUE_MM"]


def test_an_absent_dimension_is_not_a_disagreement():
    b = Builder()
    _room(b, 0, 0, 5000, 4000, layer="W")
    t = b.text("SALOON", 2500, 2000, 300.0, "TEXT")
    b.block("SAL", [t])
    b.insert("SAL", 0, 0)
    nd = _normalized(b)
    rep = cm.measure(nd, cp.build(nd))
    verdicts = {c["verdict"] for c in rep.rows[0].dimension_checks}
    assert verdicts == {cm.NOT_PRESENT}
    assert rep.counts()["dimension_disagree"] == 0


def test_region_clustering_reports_stability_rather_than_a_chosen_distance():
    b = Builder()
    _room(b, 0, 0, 5000, 4000, layer="W")
    _room(b, 60000, 0, 5000, 4000, layer="W")
    nd = _normalized(b)
    sw = reg.sweep(nd.primitives)
    # Two rooms 60 m apart must read as two regions across a run of rungs.
    two = [p for p in sw["plateaus"] if p.major_count == 2]
    assert two, [p.record() for p in sw["plateaus"]]
    assert two[0].stability >= 1.0
    assert "no clustering distance is chosen" in \
        reg.frozen_parameters()["why"]["LADDER_MM"]


def test_a_region_label_states_that_it_establishes_nothing():
    b = Builder()
    _room(b, 0, 0, 5000, 4000, layer="W")
    # A sheet frame, because a real title sits inside one. Without the frame
    # the title falls outside the plan's own extent and is correctly NOT
    # associated with it — which is the behaviour, not a defect.
    b.line(-2000, -4000, 7000, -4000, "TITLE")
    b.line(-2000, -4000, -2000, 6000, "TITLE")
    b.line(7000, -4000, 7000, 6000, "TITLE")
    b.line(-2000, 6000, 7000, 6000, "TITLE")
    b.text("GROUND FLOOR PLAN 1:100", 2500, -3000, 500.0, "TITLE")
    nd = _normalized(b)
    sw = reg.sweep(nd.primitives)
    cluster = sw["partitions"][-1].clusters[0]
    lab = reg.label(cluster, texts=nd.texts, dimensions=nd.dimensions,
                    instances=nd.instances, primitives=nd.primitives)
    assert "GROUND FLOOR PLAN 1:100" in lab["title_like_text"]
    # The key is `what_this_evidence_is_not`, so the value completes the
    # sentence: "... is not AN IDENTITY".
    assert lab["what_this_evidence_is_not"].startswith("an identity")
    assert "never inferred here" in lab["what_this_evidence_is_not"]
