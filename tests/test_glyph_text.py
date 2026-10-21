"""§7: find the text on a drawing that has no text objects."""

import pymupdf
import pytest

from engine import glyph_text as gt


@pytest.fixture
def sheet(tmp_path):
    """A page whose 'text' is small BLACK FILLED marks, plus decoys.

    Mirrors what AR-00 actually contains: letters as filled outlines,
    dimension arrowheads as dark-red fills, and wall/dimension lines as
    zero-thickness strokes.
    """
    doc = pymupdf.open()
    page = doc.new_page(width=300, height=300)
    # A "word": six small black filled marks in a row.
    for i in range(6):
        page.draw_rect(pymupdf.Rect(20 + i * 3, 40, 22 + i * 3, 45),
                       fill=(0, 0, 0), color=None)
    # A second word, far away.
    for i in range(4):
        page.draw_rect(pymupdf.Rect(200 + i * 3, 200, 202 + i * 3, 205),
                       fill=(0, 0, 0), color=None)
    # A dark-red arrowhead: a fill, but not ink.
    page.draw_rect(pymupdf.Rect(100, 100, 104, 104),
                   fill=(0.541, 0, 0), color=None)
    # A wall line: a long zero-thickness stroke.
    page.draw_line(pymupdf.Point(10, 150), pymupdf.Point(290, 150),
                   color=(0, 0, 0), width=1.14)
    out = tmp_path / "sheet.pdf"
    doc.save(out)
    return str(out)


def test_two_words_are_two_runs(sheet):
    got = gt.locate(sheet, run_gap_pt=2.0)
    assert len(got.runs) == 2
    assert {r.marks for r in got.runs} == {6, 4}


def test_a_red_arrowhead_is_not_ink(sheet):
    """Measured on AR-00: letters are (0,0,0), arrowheads (0.54,0,0)."""
    for run in gt.locate(sheet, run_gap_pt=2.0).runs:
        x0, y0, x1, y1 = run.bbox_pt
        assert not (95 < x0 < 110 and 95 < y0 < 110), "matched an arrowhead"


def test_a_wall_line_is_not_a_glyph(sheet):
    """A zero-thickness stroke has no height: the discriminator that
    stopped every wall segment near a label scoring as a letter."""
    for run in gt.locate(sheet, run_gap_pt=2.0).runs:
        assert not (145 < run.bbox_pt[1] < 155)


def test_the_run_reports_that_it_was_located_not_read(sheet):
    rec = gt.locate(sheet, run_gap_pt=2.0).runs[0].record()
    assert rec["raw_text"] == ""
    assert rec["text_status"] == "LOCATED_NOT_READ"
    assert "needs a reader" in rec["why_no_text"]


def test_the_report_says_the_text_is_vector_outlines(sheet):
    rec = gt.locate(sheet, run_gap_pt=2.0).record()
    assert rec["pdf_text_objects"] == 0
    assert rec["text_representation"] == "VECTOR_GLYPH_OUTLINE"
    assert "only way to find text is its geometry" in rec["notes"][
        "why_geometric"]


def test_it_may_not_supply_an_identity_or_a_dimension(sheet):
    rec = gt.locate(sheet, run_gap_pt=2.0).record()
    assert "room identity" in rec["what_this_may_not_do"]
    assert "released millimetre" in rec["what_this_may_not_do"]
    assert "Not what it says" in rec["what_this_establishes"]


def test_a_bigger_gap_merges_the_two_words(sheet):
    """Why the gap is a stated choice: at 6 pt a label and its dimensions
    became one run, which destroys the per-string anchor."""
    tight = gt.locate(sheet, run_gap_pt=2.0)
    loose = gt.locate(sheet, run_gap_pt=200.0)
    assert len(tight.runs) > len(loose.runs)


def test_the_sensitivity_sweep_records_the_choice(sheet):
    got = gt.sensitivity(sheet, gaps=(2.0, 6.0))
    assert got["in_use_pt"] == gt.RUN_GAP_PT
    assert [r["run_gap_pt"] for r in got["rows"]] == [2.0, 6.0]
    # The key carries the negation: this_is_not = "a physical constant…"
    assert got["this_is_not"].startswith("a physical constant")
    assert "clustering choice" in got["this_is_not"]


def test_the_output_hash_is_stable(sheet):
    assert gt.locate(sheet).output_hash == gt.locate(sheet).output_hash


def test_a_crop_renders_through_the_page_rotation(tmp_path):
    """get_drawings() returns UNROTATED coordinates; get_pixmap(clip=)
    wants rotated ones. On a 270-degree sheet, clipping with the raw
    drawing rect renders blank paper."""
    doc = pymupdf.open()
    page = doc.new_page(width=200, height=300)
    page.draw_rect(pymupdf.Rect(20, 40, 24, 46), fill=(0, 0, 0), color=None)
    page.draw_rect(pymupdf.Rect(26, 40, 30, 46), fill=(0, 0, 0), color=None)
    page.set_rotation(270)
    out = tmp_path / "rot.pdf"
    doc.save(out)

    runs = gt.locate(str(out), run_gap_pt=4.0).runs
    assert runs, "no run located on a rotated page"
    png = gt.render_crop(str(out), runs[0], dpi=150)
    assert png[:4] == b"\x89PNG"
    # The crop must contain ink: a blank render is the rotation bug.
    import numpy as np
    from PIL import Image
    import io
    arr = np.asarray(Image.open(io.BytesIO(png)).convert("L"))
    assert (arr < 128).any(), "rendered blank paper — rotation not applied"
