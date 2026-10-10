"""A source the vector reader cannot see must stop the run, not score zero.

Project 2 arrived as a 400 dpi scan of a stamped municipality submission:
ten sheets, zero vector paths, zero text objects. The pipeline stopped at
stage 1. That is the correct behaviour and these tests hold it there, because
the tempting failures are both silent:

  1. an empty stroke population read as "a drawing with no walls", which
     would report 0% recall on a sheet nobody measured;
  2. an absent human label set read as "no rooms expected", which would turn
     a missing denominator into a perfect or a hopeless score depending on
     which way the division fell.

Both are the project's oldest error in new clothes: an UNESTABLISHED value
and a MEASURED ZERO are different facts.
"""

from __future__ import annotations

import pymupdf
import pytest

from engine.frames import FrameError
from engine.frames import fit as fit_frame
from engine.reference_mapping import SEALED, SealedReferenceError, refuse_if_sealed
from tools.audit_submission_set import (EMPTY, RASTER_IMAGE_ONLY,
                                        VECTOR_LINEWORK, census)
from tools.run_pipeline import NoSpaceMap, load_space_map


def _scan_pdf(tmp_path, pages: int = 2):
    """A PDF whose pages are images — the shape of a scanned submission."""
    import numpy as np

    doc = pymupdf.open()
    arr = np.full((120, 90, 3), 250, np.uint8)
    arr[40:44, 10:80] = 20                      # a "wall" in ink
    pix = pymupdf.Pixmap(pymupdf.csRGB, 90, 120, arr.tobytes(), False)
    for _ in range(pages):
        pg = doc.new_page(width=842, height=1192)
        pg.insert_image(pg.rect, pixmap=pix)
    out = tmp_path / "scan.pdf"
    doc.save(out)
    doc.close()
    return out


def _vector_pdf(tmp_path):
    doc = pymupdf.open()
    pg = doc.new_page(width=842, height=1192)
    pg.draw_line(pymupdf.Point(100, 100), pymupdf.Point(700, 100))
    pg.insert_text(pymupdf.Point(100, 200), "ROOM")
    out = tmp_path / "vector.pdf"
    doc.save(out)
    doc.close()
    return out


def test_a_scanned_sheet_is_named_raster_not_empty(tmp_path):
    rec = census(str(_scan_pdf(tmp_path)))
    assert rec["pages_by_representation"] == {RASTER_IMAGE_ONLY: 2}
    assert rec["document_carries_any_vector_linework"] is False
    assert rec["document_carries_any_text_object"] is False
    # The distinction that matters: a page with ink on it is not EMPTY.
    for page in rec["pages"]:
        assert page["representation"] != EMPTY
        assert page["images"], "the ink is there; it is just not vector"


def test_a_plotted_sheet_is_named_vector(tmp_path):
    rec = census(str(_vector_pdf(tmp_path)))
    assert rec["pages_by_representation"] == {VECTOR_LINEWORK: 1}
    assert rec["document_carries_any_vector_linework"] is True


def test_no_strokes_stops_the_frame_rather_than_asserting_one():
    """The frame is a MEASUREMENT. With nothing to measure it must refuse."""
    import numpy as np

    mask = np.zeros((40, 40), bool)
    with pytest.raises(FrameError):
        fit_frame([], mask, 10.0)


def test_an_absent_space_map_is_not_an_empty_one():
    sm = load_space_map("")
    assert isinstance(sm, NoSpaceMap)
    assert sm["labels_supplied"] is False
    assert sm["spaces"] == []
    assert sm["label_source"] == "NOT_SUPPLIED"
    # The reason travels with the object, so a downstream reader cannot
    # count `len(spaces)` and call the answer a denominator.
    assert "NOT_ESTABLISHED" in sm.why
    assert "not zero" in sm.why


def test_a_supplied_space_map_says_so(tmp_path):
    import json

    path = tmp_path / "sm.json"
    path.write_text(json.dumps({"project_id": "X", "drawing_id": "Y",
                                "drawing_revision": "Z", "spaces": []}))
    sm = load_space_map(str(path))
    assert sm["labels_supplied"] is True
    assert not isinstance(sm, NoSpaceMap)


def test_the_project_2_take_off_is_sealed_by_name():
    """The architect's own area table is a KNOWN TOTAL, refused like a BOQ."""
    assert "P7757_area_takeoff_benchmark.pdf" in SEALED
    with pytest.raises(SealedReferenceError):
        refuse_if_sealed("data/golden/7757/sealed/"
                         "P7757_area_takeoff_benchmark.pdf")
    # And the guard is by file name, so a copy elsewhere is refused too.
    with pytest.raises(SealedReferenceError):
        refuse_if_sealed("/tmp/P7757_area_takeoff_benchmark.pdf")


def test_the_drawings_part_is_not_sealed():
    refuse_if_sealed("data/golden/7757/inputs/P7757_DRAWINGS.pdf")
