"""A file that arrived processed is not the source, and must not be read as one.

The compressed P7757 architectural PDF was audited as though it were the
source. It was not — it had been recompressed to fit a 30 MB limit — and the
audit's conclusion ("this project is a scan") would have been worthless if
the compression had been what flattened it.

The comparison must separate those two cases on evidence:

  VECTOR -> RASTER   the transformation destroyed linework. The engine's
                     stop is a fact about the copy, not the drawing;
  RASTER -> RASTER   the drawing was pixels before anything touched it.

These tests build both cases and assert the verdict, because guessing from
file size — the intuitive test — gets the interesting case backwards.
"""

from __future__ import annotations

import numpy as np
import pymupdf

from tools.compare_source_provenance import (BOTH_VECTOR, FLATTENED,
                                             RECOMPRESSED, UNDECIDED, compare)


def _vector_doc(path, pages: int = 2):
    doc = pymupdf.open()
    for _ in range(pages):
        pg = doc.new_page(width=842, height=1192)
        pg.draw_line(pymupdf.Point(100, 100), pymupdf.Point(700, 100))
        pg.draw_rect(pymupdf.Rect(100, 200, 700, 800))
    doc.save(path)
    doc.close()
    return str(path)


def _raster_doc(path, pages: int = 2, *, quality: int = 80, seed: int = 0):
    """Pages carrying a JPEG, at a chosen quality. Same pixel grid each time."""
    rng = np.random.default_rng(seed)
    arr = np.full((600, 420, 3), 250, np.uint8)
    arr[200:210, 40:380] = 20
    arr[:] = np.clip(arr.astype(np.int16)
                     + rng.integers(-3, 4, arr.shape), 0, 255).astype(np.uint8)
    pix = pymupdf.Pixmap(pymupdf.csRGB, 420, 600, arr.tobytes(), False)
    img = pix.tobytes("jpeg", jpg_quality=quality)
    doc = pymupdf.open()
    for _ in range(pages):
        pg = doc.new_page(width=842, height=1192)
        pg.insert_image(pg.rect, stream=img)
    doc.save(path)
    doc.close()
    return str(path)


def test_flattening_is_detected(tmp_path):
    a = _vector_doc(tmp_path / "original.pdf")
    b = _raster_doc(tmp_path / "flattened.pdf")
    rec = compare([a], b, label_a="ORIG", label_b="PROCESSED")
    assert rec["verdict"] == FLATTENED
    assert rec["ORIG"]["vector_paths_total"] > 0
    assert rec["PROCESSED"]["vector_paths_total"] == 0


def test_recompression_of_a_scan_is_not_mistaken_for_flattening(tmp_path):
    """The case that actually occurred: both sides were always pixels."""
    a = _raster_doc(tmp_path / "original.pdf", quality=95)
    b = _raster_doc(tmp_path / "compressed.pdf", quality=40)
    rec = compare([a], b, label_a="ORIG", label_b="COMPRESSED")
    assert rec["verdict"] == RECOMPRESSED
    assert rec["ORIG"]["vector_paths_total"] == 0
    assert rec["COMPRESSED"]["vector_paths_total"] == 0
    # Size alone is the tempting test and it is not the one used: the
    # verdict is driven by path counts, not by which file is bigger.
    assert rec["ORIG"]["total_bytes"] > rec["COMPRESSED"]["total_bytes"]
    assert "property of the SOURCE" in rec["what_that_means"]


def test_a_split_rendition_is_compared_as_one_source(tmp_path):
    """The original arrived as two halves; the comparison must join them."""
    a1 = _raster_doc(tmp_path / "half1.pdf", pages=2, quality=95)
    a2 = _raster_doc(tmp_path / "half2.pdf", pages=2, quality=95)
    b = _raster_doc(tmp_path / "whole.pdf", pages=4, quality=40)
    rec = compare([a1, a2], b, label_a="SPLIT", label_b="WHOLE")
    assert rec["SPLIT"]["pages"] == 4
    assert rec["verdict"] == RECOMPRESSED


def test_mismatched_page_counts_decide_nothing(tmp_path):
    a = _raster_doc(tmp_path / "a.pdf", pages=2)
    b = _raster_doc(tmp_path / "b.pdf", pages=3)
    rec = compare([a], b, label_a="A", label_b="B")
    assert rec["verdict"] == UNDECIDED
    assert rec["pixel_agreement_sample"] == {}


def test_two_vector_renditions_are_both_readable(tmp_path):
    a = _vector_doc(tmp_path / "a.pdf")
    b = _vector_doc(tmp_path / "b.pdf")
    assert compare([a], b, label_a="A", label_b="B")["verdict"] == BOTH_VECTOR


def test_a_coarser_quantisation_table_is_reported(tmp_path):
    """The recompression signal, read off the DQT marker without decoding."""
    a = _raster_doc(tmp_path / "fine.pdf", quality=95)
    b = _raster_doc(tmp_path / "coarse.pdf", quality=25)
    rec = compare([a], b, label_a="FINE", label_b="COARSE")
    fine = rec["FINE"]["mean_jpeg_quantisation_step"]
    coarse = rec["COARSE"]["mean_jpeg_quantisation_step"]
    assert fine is not None and coarse is not None
    assert coarse > fine
