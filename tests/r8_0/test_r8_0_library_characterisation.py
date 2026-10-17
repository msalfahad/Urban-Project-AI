"""R8.0 — pin what the ezdxf dependency actually does (the future K2 route).

These tests describe the LIBRARY, not Urban. They pass today. If an ezdxf
upgrade changes any of them, the dependency register and the K2 design must
be reviewed before the upgrade is accepted.
"""

from __future__ import annotations

import ezdxf

from . import ezdxf_oracle, scenes as S
from .geometry import match_segment_sets

PINNED_EZDXF = "1.4.4"


def test_ezdxf_version_is_pinned():
    assert ezdxf.__version__ == PINNED_EZDXF


def _doc_with_grid():
    doc = ezdxf.new()
    cell = doc.blocks.new("CELL")
    cell.add_line((0, 0), (100, 0))
    ref = doc.modelspace().add_blockref("CELL", (0, 0))
    ref.grid(size=(2, 3), spacing=(500, 1000))
    return doc, ref


def test_virtual_entities_on_minsert_yields_first_cell_only():
    """Donor claim (U-C4N ezdxf_backend L6797) confirmed: a K2 route that
    calls virtual_entities() on a MINSERT silently loses 5 of 6 cells."""
    _, ref = _doc_with_grid()
    assert ref.mcount == 6
    assert len(list(ref.virtual_entities())) == 1
    assert len(list(ref.multi_insert())) == 6


def test_xref_insert_yields_no_virtual_entities():
    doc = ezdxf.new()
    doc.add_xref_def("ext.dwg", "XR")
    ref = doc.modelspace().add_blockref("XR", (0, 0))
    assert doc.blocks.get("XR").block_record.is_xref
    assert list(ref.virtual_entities()) == []


def test_mirror_is_reencoded_as_negative_extrusion():
    """ezdxf realises a scale(-1,1) ARC by flipping its extrusion to -Z: an
    engine that then reads raw OCS values (beiming audit.py) is wrong."""
    doc = ezdxf.new()
    doc.blocks.new("C").add_arc((1000, 0), 500, 0, 90)
    ref = doc.modelspace().add_blockref("C", (0, 0), dxfattribs={"xscale": -1})
    arc = next(e for e in ref.virtual_entities() if e.dxftype() == "ARC")
    assert tuple(arc.dxf.extrusion) == (0.0, 0.0, -1.0)
    assert tuple(arc.dxf.center)[:2] == (1000.0, 0.0)          # OCS value, NOT the WCS centre (-1000, 0)


def test_nested_minsert_under_reflecting_parent_rows_on_wrong_side():
    """LIBRARY FINDING (this review): a MINSERT nested in a block placed with
    scale(-1,1) is realised by ezdxf with its ROWS on the wrong side
    (y = -500 instead of +500). The mirror is re-encoded as rotation 180 +
    negative y-scale; grid spacing is rotated but not scaled, so the row
    offset flips. Consequence: ezdxf (K2) cannot be the only reference for
    MINSERT under reflection; K1 vs K2 must be judged against hand truth."""
    case = next(c for c in S.MINSERT_CASES if c[1] == "F06_MINSERT_MIRRORED_PARENT")
    segs = ezdxf_oracle.realise(case[3])["segments"]
    ok, missing, extra = match_segment_sets(case[4], segs)
    assert not ok
    ys = sorted({round(a[1], 6) + 0.0 for a, _ in segs})
    assert ys == [-500.0, 0.0]
