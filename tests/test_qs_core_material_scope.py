"""A material answer travels exactly as far as the document that gives it says it does.

R6 removed the inference that shape proves material, and then made the same inference in the other direction:
it grouped every material question by thickness family and assumed one answer covered every wall of that
thickness.  External walls, internal partitions, structural walls and service enclosures are routinely drawn
at one thickness and built of different things.
"""

from __future__ import annotations

from engine.qs_core import evidence as EV, masonry as MA, openings as OP, synthetic as S

TOL, SPAN = S.TOL, S.MAX_OPENING_SPAN


def claim(material, reference, scope, source=EV.APPROVED_GUIDE, evidence_source="SPECIFICATION"):
    """A specification clause, with the scope it states for itself carried on the claim."""
    return EV.Claim(1.0, source, reference,
                    {"MATERIAL": material, "EVIDENCE_SOURCE": evidence_source, "SCOPE": scope})


def classify(bands, **kw):
    lines, _gaps = OP.build_wall_lines(bands, TOL, SPAN, openings=[])
    reg = MA.classify_wall_identity(lines, TOL, material_map=S.MASONRY_MAP, **kw)
    return {r["COMPONENT_REF"]: r for r in reg["REGISTER"]}, reg


def test_two_walls_of_one_thickness_may_be_two_materials():
    bands = S.two_walls_of_one_thickness_and_two_materials()
    scopes = [claim("BLOCKWORK", "SPEC-7::EXTERNAL", {"LAYER": "A-WALL-EXTERNAL"}),
              claim("CONCRETE", "SPEC-7::SERVICE", {"LAYER": "A-WALL-SERVICE"})]
    by_ref, _reg = classify(bands, material_scopes=scopes)
    materials = {r: v["MATERIAL_IDENTITY"] for r, v in by_ref.items()}
    assert len(set(materials.values())) == 2, materials
    assert MA.MASONRY_CONFIRMED in materials.values()
    assert MA.CONCRETE_CONFIRMED in materials.values()


def test_a_claim_scoped_to_one_layer_does_not_answer_the_other():
    bands = S.two_walls_of_one_thickness_and_two_materials()
    by_ref, _reg = classify(bands, material_scopes=[
        claim("BLOCKWORK", "SPEC-7::EXTERNAL", {"LAYER": "A-WALL-EXTERNAL"})])
    answered = [v for v in by_ref.values() if v["MATERIAL_IDENTITY"] != MA.MATERIAL_UNKNOWN]
    unanswered = [v for v in by_ref.values() if v["MATERIAL_IDENTITY"] == MA.MATERIAL_UNKNOWN]
    assert len(answered) == 1 and len(unanswered) == 1
    assert any("SCOPE_LAYER" in str(w) for w in unanswered[0]["MATERIAL_SCOPES_OUT_OF_SCOPE"])


def test_an_unscoped_claim_travels_only_when_the_evidence_says_it_is_project_wide():
    bands = S.two_walls_of_one_thickness_and_two_materials()
    silent, _ = classify(bands, material_scopes=[claim("BLOCKWORK", "SPEC-7", {})])
    assert all(v["MATERIAL_IDENTITY"] == MA.MATERIAL_UNKNOWN for v in silent.values())
    stated, _ = classify(bands, material_scopes=[
        claim("BLOCKWORK", "SPEC-7", {MA.SCOPE_STATED: True})])
    assert all(v["MATERIAL_IDENTITY"] == MA.MASONRY_CONFIRMED for v in stated.values())


def test_a_thickness_scoped_claim_covers_that_thickness_and_no_other():
    bands = S.two_walls_of_one_thickness_and_two_materials() + [
        S.wall_band("W-THIN", (0.0, 9.0, 8.0, 9.1), 0.10, "X", layer="A-WALL-EXTERNAL")]
    by_ref, _reg = classify(bands, material_scopes=[
        claim("BLOCKWORK", "SPEC-7::200", {"THICKNESS_FAMILY_M": 0.2})])
    answered = {r for r, v in by_ref.items() if v["MATERIAL_IDENTITY"] != MA.MATERIAL_UNKNOWN}
    assert len(answered) == 2
    thin = next(v for r, v in by_ref.items() if v["THICKNESS_M"] == 0.10)
    assert thin["MATERIAL_IDENTITY"] == MA.MATERIAL_UNKNOWN


def test_the_question_group_is_finer_than_thickness_and_says_it_is_not_a_wall_type():
    bands = S.two_walls_of_one_thickness_and_two_materials()
    by_ref, reg = classify(bands)
    keys = {v["MATERIAL_SCOPE_KEY"] for v in by_ref.values()}
    assert len(keys) == 2, "two layers are two question groups, whatever their thickness"
    for v in by_ref.values():
        assert v["THICKNESS_FAMILY_PROVES_MATERIAL"] is False
        assert "may be built of different things" in v["THICKNESS_FAMILY_IS_NOT_A_WALL_TYPE"]
    scope_reg = MA.material_scope_register(reg["REGISTER"])
    assert scope_reg["GROUP_COUNT"] == 2
    assert scope_reg["WHAT_A_GROUP_IS_NOT"].startswith("a wall type")


def test_a_superseded_specification_cannot_answer_even_inside_its_scope():
    bands = S.two_walls_of_one_thickness_and_two_materials()
    retired = EV.Claim(1.0, EV.APPROVED_GUIDE, "SPEC-6::EXTERNAL",
                       {"MATERIAL": "BLOCKWORK", "EVIDENCE_SOURCE": "SPECIFICATION",
                        "SCOPE": {"LAYER": "A-WALL-EXTERNAL"}},
                       status=EV.SUPERSEDED, superseded_by="SPEC-7", superseded_reason="reissued")
    by_ref, _reg = classify(bands, material_scopes=[retired])
    assert all(v["MATERIAL_IDENTITY"] == MA.MATERIAL_UNKNOWN for v in by_ref.values())
