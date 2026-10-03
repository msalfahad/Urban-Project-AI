"""A new project may be frozen and audited. It may not be measured.

The second project is the only thing that can tell us whether the engine
reads DRAWINGS or reads THIS drawing: every tolerance and every
representation assumption was chosen against one sheet. That test is
destroyed the moment its answers are used to adjust the project it exists to
test, so the intake path is deliberately narrow.
"""

import pytest

from tools.freeze_new_source import IntakeError, REFUSED_INPUTS, freeze


def test_a_missing_drawing_is_refused_with_what_is_actually_blocked():
    with pytest.raises(IntakeError) as e:
        freeze("data/space_maps/does_not_exist.pdf", project_id="P2",
               drawing_id="AR-00", revision="r1")
    assert "cannot be frozen until the drawing is supplied" in str(e.value)
    assert "whether the engine generalises" in str(e.value)


def test_the_sealed_benchmark_cannot_enter_through_the_intake_path():
    from engine.reference_mapping import SealedReferenceError
    with pytest.raises(SealedReferenceError):
        freeze("data/golden/23010/site_benchmark.json", project_id="P2",
               drawing_id="AR-00", revision="r1")


@pytest.mark.parametrize("name", ["23010_qiyal.pdf", "old_BOQ.pdf",
                                  "contractor_quantities.pdf",
                                  "Quotation_final.pdf", "cost_export.pdf",
                                  "rate_schedule.pdf", "price_list.pdf"])
def test_a_document_that_carries_answers_is_refused_by_name(name):
    # Manual qiyal, a previous BOQ and any contractor quantity are validation
    # sources at most. An intake path is the last place they should be able
    # to reach the engine.
    with pytest.raises(IntakeError) as e:
        freeze(f"data/space_maps/{name}", project_id="P2",
               drawing_id="AR-00", revision="r1")
    assert "This tool reads DRAWINGS" in str(e.value)


def test_the_refusal_list_covers_every_answer_bearing_document_type():
    for kind in ("site_benchmark", "qiyal", "boq", "contractor",
                 "quotation", "cost", "rate", "price"):
        assert kind in REFUSED_INPUTS


def test_the_refusal_is_by_name_not_by_extension():
    # A .pdf named like a BOQ is still refused; the check is on what the
    # document claims to be.
    with pytest.raises(IntakeError):
        freeze("some/path/PROJECT2_BOQ_rev3.pdf", project_id="P2",
               drawing_id="AR-00", revision="r1")
