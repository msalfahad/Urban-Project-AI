"""§7, §8: read what the sheet SAYS, and keep it out of the geometry.

The reader seam is injected, so every test here runs offline with no key
and no network.
"""

import json

import pytest

from engine import document_reader as dr
from engine.document_observations import (
    GLYPH_OUTLINE, PRINTED_DIMENSION, ROOM_LABEL, USE_FOR_IDENTITY,
    USE_FOR_SIZE, ObservationError)
from engine.glyph_text import TextRun


def _run(rid="TR-0001"):
    return TextRun(run_id=rid, bbox_pt=(10.0, 10.0, 30.0, 18.0),
                   bbox_mm=(450.0, 450.0, 1350.0, 810.0),
                   centre_mm=(900.0, 630.0), marks=8,
                   glyph_height_pt=3.0, orientation="HORIZONTAL",
                   form_guess="LABEL_LIKE_RUN")


def _reader(items):
    def fn(system, user, images):
        assert images and images[0][0] == "image/png"
        return json.dumps({"items": items})
    return fn


@pytest.fixture
def pdf(tmp_path):
    """A one-page PDF with a rectangle, so render_crop has something."""
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page(width=200, height=200)
    page.draw_rect(pymupdf.Rect(20, 20, 60, 40), fill=(0, 0, 0))
    out = tmp_path / "t.pdf"
    doc.save(out)
    return str(out)


# --- the parse ------------------------------------------------------------

def test_a_bare_integer_reads_as_millimetres():
    got, unit, note = dr._parse_dimension("1850")
    assert got == 1850.0 and unit == "mm"
    assert "millimetres" in note


def test_a_decimal_reads_as_metres():
    got, unit, note = dr._parse_dimension("3.50")
    assert got == 3500.0 and unit == "m"
    assert "metres" in note


def test_a_pair_is_not_parsed_to_one_value():
    got, unit, note = dr._parse_dimension("2450 x 1850")
    assert got is None
    assert "which side is which" in note


def test_an_unrecognised_string_is_left_unparsed_not_coerced():
    got, _, note = dr._parse_dimension("approx")
    assert got is None
    assert "rather than coerced" in note


def test_none_is_not_zero():
    """An unparsed dimension's value is UNKNOWN, not zero."""
    from engine.document_observations import PrintedDimensionObservation
    obs = PrintedDimensionObservation("DO-1", "approx")
    assert obs.parsed_value_mm is None
    assert not obs.is_parsed


# --- reading --------------------------------------------------------------

def test_a_dimension_becomes_a_size_observation(pdf):
    rep = dr.read_runs(pdf, [_run()], reader=_reader(
        [{"text": "1850", "kind": "DIMENSION", "confidence": 0.9}]))
    assert len(rep.dimensions) == 1
    obs = rep.dimensions[0]
    assert obs.kind == PRINTED_DIMENSION
    assert obs.parsed_value_mm == 1850.0
    assert obs.text_source == GLYPH_OUTLINE
    assert obs.anchor_mm == (900.0, 630.0)
    assert obs.may_be_used_for(USE_FOR_SIZE)
    assert not obs.may_be_used_for(USE_FOR_IDENTITY)


def test_a_label_becomes_an_identity_observation_with_its_independence(pdf):
    rep = dr.read_runs(pdf, [_run()], reader=_reader(
        [{"text": "غرفة نوم", "kind": "ROOM_LABEL", "confidence": 0.8}]))
    obs = rep.labels[0]
    assert obs.kind == ROOM_LABEL
    assert obs.raw_text == "غرفة نوم"
    assert obs.fields["source_independence_class"] == (
        dr.INDEPENDENCE_SAME_DRAWING)
    assert obs.fields["evidence_family"] == dr.FAMILY_DOCUMENT
    assert obs.may_be_used_for(USE_FOR_IDENTITY)
    assert not obs.may_be_used_for(USE_FOR_SIZE)


def test_a_dimension_may_not_be_used_for_identity(pdf):
    rep = dr.read_runs(pdf, [_run()], reader=_reader(
        [{"text": "1850", "kind": "DIMENSION"}]))
    with pytest.raises(ObservationError):
        rep.dimensions[0].require_use(USE_FOR_IDENTITY)


def test_an_empty_answer_is_a_correct_answer(pdf):
    rep = dr.read_runs(pdf, [_run()], reader=_reader([]))
    assert rep.runs_read == 1
    assert rep.runs_empty == 1
    assert not rep.dimensions and not rep.labels


def test_a_reader_failure_is_recorded_not_swallowed(pdf):
    def boom(system, user, images):
        raise RuntimeError("no network")
    rep = dr.read_runs(pdf, [_run()], reader=boom)
    assert rep.failures and rep.failures[0]["error"] == "RuntimeError"
    assert rep.runs_read == 0


def test_no_reader_and_no_cache_says_nobody_looked(pdf):
    """"No text found" and "nobody looked" are different facts."""
    rep = dr.read_runs(pdf, [_run()])
    assert rep.notes["status"] == "NOT_READ_NO_READER_SUPPLIED"
    assert "not the same as a drawing with no text" in rep.notes["why"]
    assert rep.runs_read == 0


def test_answers_are_cached_on_the_crop_bytes(pdf, tmp_path):
    cache = tmp_path / "cache"
    calls = []

    def counting(system, user, images):
        calls.append(1)
        return json.dumps({"items": [{"text": "1850", "kind": "DIMENSION"}]})

    a = dr.read_runs(pdf, [_run()], reader=counting, cache_dir=str(cache))
    assert a.calls_made == 1 and len(calls) == 1
    b = dr.read_runs(pdf, [_run()], reader=counting, cache_dir=str(cache))
    assert b.calls_cached == 1 and len(calls) == 1
    assert b.dimensions[0].parsed_value_mm == 1850.0


def test_a_cache_alone_replays_with_no_reader(pdf, tmp_path):
    cache = tmp_path / "cache"
    dr.read_runs(pdf, [_run()], cache_dir=str(cache),
                 reader=_reader([{"text": "1850", "kind": "DIMENSION"}]))
    replay = dr.read_runs(pdf, [_run()], cache_dir=str(cache))
    assert replay.calls_made == 0
    assert replay.calls_cached == 1
    assert replay.dimensions[0].parsed_value_mm == 1850.0


def test_unparseable_model_output_yields_no_observations(pdf):
    rep = dr.read_runs(pdf, [_run()],
                       reader=lambda s, u, i: "I cannot read this")
    assert rep.runs_read == 1
    assert not rep.dimensions and not rep.labels


# --- the discipline -------------------------------------------------------

def test_the_prompt_forbids_measuring_and_naming(pdf):
    for phrase in ("Transcribe exactly what is printed",
                   "not measuring", "Never guess a character",
                   "which room a label belongs to"):
        assert phrase in dr.SYSTEM


def test_the_record_states_the_evidence_discipline(pdf):
    rec = dr.read_runs(pdf, [_run()], reader=_reader(
        [{"text": "1850", "kind": "DIMENSION"}])).record()
    d = rec["evidence_discipline"]
    assert "NOT a released millimetre" in d["a_printed_dimension_is"]
    assert "3.50 m wide" in d["a_printed_dimension_is"]
    assert "SAME_DRAWING" in d["independence"]
    assert "what characters are in a crop" in d["the_model_was_asked"]
