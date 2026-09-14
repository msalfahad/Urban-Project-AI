"""E41 — the VECTOR_PATH layer. What it must keep, and what it must not decide."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from engine import vector_source as vs
from engine.vector_source import (AXIS_DIAGONAL, AXIS_H, AXIS_V, FILL, STROKE,
                                  VectorPath, VectorSegment,
                                  VectorSourceError, read)

PDF = Path("data/golden/23010/inputs/AR-00_MAR2023.pdf")


def seg(**kw):
    base = dict(segment_id="VS-1", path_id="VP-1", subpath_index=0, axis=AXIS_H,
                fixed_mm=0.0, start_mm=0.0, end_mm=1000.0, path_type=STROKE,
                stroke_width_pt=1.14, is_dashed=False,
                x0_mm=0.0, y0_mm=0.0, x1_mm=1000.0, y1_mm=0.0)
    base.update(kw)
    return VectorSegment(**base)


def test_a_diagonal_is_kept_and_labelled_never_dropped():
    """A plan with a rotated wing must not lose it to an orthogonal detector."""
    d = seg(axis=AXIS_DIAGONAL, x1_mm=700.0, y1_mm=700.0, angle_deg=45.0)
    assert not d.is_axis_aligned
    assert d.length_mm > 0


def test_a_diagonal_cannot_be_handed_to_the_axis_aligned_engine_silently():
    with pytest.raises(VectorSourceError, match="axis-aligned"):
        seg(axis=AXIS_DIAGONAL).as_line()


def test_stroke_width_is_carried_as_a_source_property_not_a_verdict():
    """A 1.14 pt pen is not a wall. It is a property of the mark, kept for the
    same reason source_object_id is kept: so a later stage can use it as
    evidence. Nothing in this module may classify on it."""
    src = Path(vs.__file__).read_text()
    tree = ast.parse(src)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert "WALL" not in names
    for forbidden in ("is_wall", "looks_like_wall", "WALL_PEN", "wall_width"):
        assert forbidden not in src, forbidden


def test_no_population_band_is_excluded():
    """A band left out of the report is a band quietly declared not-a-wall."""
    segs = [seg(stroke_width_pt=1.14), seg(stroke_width_pt=0.12, end_mm=10.0,
                                           x1_mm=10.0),
            seg(path_type=FILL, stroke_width_pt=0.0)]
    d = vs.VectorDrawing(segments=segs)
    bands = d.population_bands()
    assert len(bands) == 3
    assert sum(b["segments"] for b in bands) == 3


def test_a_solid_stroke_is_not_read_as_dashed():
    """A PDF writes solid as '[] 0'. Reading that as a dash pattern would turn
    every line on the sheet into a topology boundary candidate."""
    solid = VectorPath("VP-1", 1, STROKE, 1.14, (), "[] 0", 1, ())
    fill = VectorPath("VP-2", 2, FILL, 0.0, (), "None", 1, ())
    dashed = VectorPath("VP-3", 3, STROKE, 0.3, (), "[3 2] 0", 1, ())
    assert not solid.is_dashed and not fill.is_dashed and dashed.is_dashed


def test_curves_are_counted_not_linearised():
    """A flattened curve is a different object from a drawn line and must not
    enter the same pool pretending otherwise."""
    src = Path(vs.__file__).read_text()
    assert "skipped[CURVE]" in src
    assert "bezier" not in src.lower()


@pytest.mark.slow
@pytest.mark.skipif(not PDF.exists(), reason="audited input not present")
def test_the_real_sheet_reads_without_losing_an_unrecorded_mark():
    d = read(str(PDF))
    assert len(d.paths) > 10_000
    counted = len(d.segments) + sum(d.skipped.values())
    assert counted > 70_000
    assert d.page_rotation == 270


@pytest.mark.slow
@pytest.mark.skipif(not PDF.exists(), reason="audited input not present")
def test_the_wall_pen_population_is_not_fragmented_on_this_sheet():
    """The review's hypothesis was that flattening broke architectural paths
    into pieces. On AR-00 it is FALSE and the measurement says so: a heavy-pen
    path holds one item, and sub-50 mm marks almost never share a path with a
    long run. Recorded as a measurement because on another drawing it may be
    true."""
    f = read(str(PDF)).path_fragmentation()
    assert f["short_in_a_path_that_also_has_a_long_run"] < (
        f["short_in_a_path_with_no_long_run"] / 10)


@pytest.mark.slow
@pytest.mark.skipif(not PDF.exists(), reason="audited input not present")
def test_the_sheet_is_orthogonal_and_that_is_measured_not_assumed():
    """Stroke length at 0 and 90 degrees dwarfs every other bucket. The off-axis
    marks are short curve flattening, not a rotated wing."""
    bands = read(str(PDF)).angle_bands()
    ortho = bands["0"]["total_length_m"] + bands["90"]["total_length_m"]
    other = sum(v["total_length_m"] for k, v in bands.items()
                if k not in ("0", "90"))
    assert ortho > other * 2
