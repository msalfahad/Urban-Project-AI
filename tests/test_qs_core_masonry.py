"""A thickness is a measurement.  Being a wall is an identity, and it has to be established separately.

The R4 output billed blockwork at 50 mm, 100 mm and 126 mm.  Nothing in the building has those thicknesses;
they are grid artefacts, junctions and duplicated lines that happen to be measurable.  No whitelist of accepted
thicknesses is used here - the families come from the drawing, so a building that uses other ones classifies
just as well.
"""

from __future__ import annotations

from engine.qs_core import invariants, masonry as MA, openings as OP, quantities as QY, synthetic as S

TOL, SPAN = S.TOL, S.MAX_OPENING_SPAN


def classify(bands, **kw):
    lines, _gaps = OP.build_wall_lines(bands, TOL, SPAN, openings=[])
    reg = MA.classify_wall_identity(lines, TOL, **kw)
    return lines, {r["COMPONENT_REF"]: r for r in reg["REGISTER"]}, reg


def only(by_ref, identity):
    return sorted(r for r, v in by_ref.items() if v["IDENTITY"] == identity)


def test_the_thickness_families_are_discovered_from_the_drawing_not_declared():
    lines, _by_ref, reg = classify(S.a_drawing_with_artefacts_among_its_walls())
    fams = reg["THICKNESS_FAMILIES"]["FAMILIES"]
    proved = sorted(k for k, v in fams.items() if v["PROVED"])
    assert proved == [0.15, 0.2]
    assert fams[0.13]["MEMBER_COUNT"] == 1 and not fams[0.13]["PROVED"]


def test_a_band_with_a_thickness_nothing_else_uses_is_not_billed():
    _lines, by_ref, _reg = classify(S.a_drawing_with_artefacts_among_its_walls())
    odd = next(v for r, v in by_ref.items() if v["THICKNESS_M"] == 0.13)
    assert odd["IDENTITY"] == MA.WALL_IDENTITY_UNRESOLVED
    assert odd["BILLABLE_AS_MASONRY"] is False


def test_the_square_where_two_walls_cross_is_a_junction_not_a_wall():
    _lines, by_ref, _reg = classify(S.a_drawing_with_artefacts_among_its_walls())
    junctions = [v for v in by_ref.values() if v["IDENTITY"] == MA.JUNCTION_ARTEFACT]
    assert junctions, {r: v["IDENTITY"] for r, v in by_ref.items()}
    assert junctions[0]["COVERED_BY_CROSSING_WALLS"] >= MA.JUNCTION_COVERAGE


def test_one_wall_drawn_on_two_layers_is_billed_once():
    _lines, by_ref, _reg = classify(S.the_same_wall_drawn_on_two_layers())
    dups = [v for v in by_ref.values() if v["IDENTITY"] == MA.DUPLICATED_LINE_ARTEFACT]
    assert len(dups) == 1 and dups[0]["DUPLICATE_OF"]


def test_a_band_as_short_as_it_is_thick_is_never_a_run_of_wall():
    stub = S.wall_band("M-STUB", (0.0, 0.0, 0.20, 0.20), 0.20, "X")
    long_a = S.wall_band("M-A", (0.0, 3.0, 8.0, 3.20), 0.20, "X")
    long_b = S.wall_band("M-B", (0.0, 6.0, 8.0, 6.20), 0.20, "X")
    _lines, by_ref, _reg = classify([stub, long_a, long_b])
    stub_rec = next(v for r, v in by_ref.items() if v["MATERIAL_LENGTH_M"] == 0.20)
    assert stub_rec["IDENTITY"] in (MA.COLUMN_OR_STRUCTURE, MA.JUNCTION_ARTEFACT)
    assert stub_rec["ASPECT_LENGTH_OVER_THICKNESS"] < MA.WALL_ASPECT_MIN


def test_what_the_drawing_says_outranks_what_its_shape_suggests():
    walls = S.a_drawing_with_artefacts_among_its_walls()
    lines, _gaps = OP.build_wall_lines(walls, TOL, SPAN, openings=[])
    odd = next(ln for ln in lines if ln.thickness == 0.13)
    reg = MA.classify_wall_identity(lines, TOL,
                                    annotations={odd.component_ref: {"MATERIAL": "BLOCKWORK",
                                                                     "LAYER": "A-WALL-BLK"}},
                                    masonry_materials=("BLOCKWORK",))
    rec = next(r for r in reg["REGISTER"] if r["COMPONENT_REF"] == odd.component_ref)
    assert rec["IDENTITY"] == MA.CONFIRMED_MASONRY_WALL and rec["CONFIDENCE"] == "PROVEN"


def test_real_walls_are_still_confirmed_so_the_rule_is_not_simply_restrictive():
    _lines, by_ref, reg = classify(S.a_drawing_with_artefacts_among_its_walls())
    assert reg["COUNTS"][MA.CONFIRMED_MASONRY_WALL] >= 3


def test_the_invariant_fails_when_an_unproved_band_is_billed():
    lines, by_ref, reg = classify(S.a_drawing_with_artefacts_among_its_walls())
    odd = next(r for r, v in by_ref.items() if v["THICKNESS_M"] == 0.13)
    honest = [{"COMPONENT_REF": r, "STATUS": QY.FINAL} for r, v in by_ref.items()
              if v["BILLABLE_AS_MASONRY"]]
    assert invariants.unusual_band_is_not_billed_on_thickness_alone(reg, honest)["PASS"]
    smuggled = honest + [{"COMPONENT_REF": odd, "STATUS": QY.FINAL}]
    check = invariants.unusual_band_is_not_billed_on_thickness_alone(reg, smuggled)
    assert not check["PASS"]
    assert check["RESULT"]["OFFENDERS"][0]["ROW"] == odd


def test_no_thickness_is_written_into_the_engine():
    """Read the executable code only - comments and prose may discuss thicknesses; the code may not hold one."""
    import io
    import pathlib
    import re
    import tokenize

    source = pathlib.Path("engine/qs_core/masonry.py").read_text("utf-8")
    code = []
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING, tokenize.NL, tokenize.NEWLINE):
            continue
        code.append(tok.string)
    blob = " ".join(code)
    assert not re.search(r"\b0\.1[05]\b|\b0\.2\b|\b150\b|\b200\b", blob), blob[:400]


def test_a_wall_traced_twice_on_one_line_is_not_measured_twice():
    """The union of the material, not the sum of the segments: a doubled length is invisible in any total."""
    lines, _gaps = OP.build_wall_lines(S.a_wall_traced_twice_on_the_same_line(), TOL, SPAN, openings=[])
    assert len(lines) == 1
    assert lines[0].material_length == 8.0
    ev = lines[0].evidence[0].detail
    assert ev["SEGMENT_LENGTH_SUM_M"] == 15.5 and ev["OVERLAPPING_SEGMENT_LENGTH_M"] == 7.5
