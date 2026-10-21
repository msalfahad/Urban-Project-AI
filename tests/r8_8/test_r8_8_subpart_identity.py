"""R8.8 §6-§8: source sub-part identity comes from SOURCE STRUCTURE, not from realisation order."""

from __future__ import annotations

import random
from dataclasses import replace

from engine.source import canonical_build as CB, canonical_input as CI
from engine.source import observations as O
from engine.source.cad import kernel
from engine.source.realised import RealisedGeometry

ANCHOR = O.SourceRevisionAnchor(None, "T", "T")


def poly(h, verts, bulges, closed=False, layer="WALL"):
    return O.SourceEntityObservation(f"D1:{h}", str(h), "T:LWPOLYLINE", O.LWPOLYLINE,
                                     O.PolylineGeom(tuple(verts), tuple(bulges), closed), layer)


def line(h, a, b, layer="WALL"):
    return O.SourceEntityObservation(f"D1:{h}", str(h), "T:LINE", O.LINE, O.LineGeom(a, b), layer)


def doc(entities, blocks=None):
    return O.SourceDocument(ANCHOR, tuple(entities), blocks or {})


# span 0 straight, span 1 bulged, span 2 DEGENERATE (coincident), span 3 straight
PL = poly(10, [(0, 0), (100, 0), (100, 100), (100, 100), (0, 100)], [0.0, 0.5, 0.0, 0.0, 0.0], closed=True)


def keys(real):
    return {p.identity.key: p.geometry for p in CB.parts_from_realised("R", real, lambda path: (), None)}


def test_part_index_is_the_source_span_index():
    k = keys(kernel.realise(doc([PL])))
    idx = sorted((key.split("|")[3], int(key.split("|")[4])) for key in k)
    # span 2 is degenerate and realises nothing; span 3 keeps index 3 (an output ordinal would have said 2)
    assert idx == [("ARC", 1), ("SEGMENT", 0), ("SEGMENT", 3), ("SEGMENT", 4)]


def test_realised_order_shuffle_keeps_every_identity():
    real = kernel.realise(doc([PL, line(11, (0, 0), (50, 50))]))
    base = keys(real)
    for seed in range(5):
        rnd = random.Random(seed)
        sh = RealisedGeometry()
        for attr in ("segments", "arcs", "circles", "elliptical_arcs"):
            lst = list(getattr(real, attr))
            rnd.shuffle(lst)
            getattr(sh, attr).extend(lst)
        assert keys(sh) == base


def test_unrelated_emission_insertion_keeps_every_identity():
    base = keys(kernel.realise(doc([PL])))
    noisy = keys(kernel.realise(doc([line(1, (5, 5), (6, 6)), poly(2, [(0, 0), (1, 0), (1, 1)], [0, 0, 0]), PL])))
    assert {k: v for k, v in noisy.items() if "|H10|" in k} == base


def test_identity_survives_minsert_cells_and_nesting_as_path_entries():
    blk = O.BlockDefinition("HB", "B", (0.0, 0.0), (PL,))
    ins = O.SourceEntityObservation("D1:30", "30", "T:INSERT", O.INSERT,
                                    O.InsertGeom("HB", (0.0, 0.0), (1.0, 1.0, 1.0), 0.0, O.GridSpec(2, 1, 500.0, 0.0)), "0")
    k = keys(kernel.realise(doc([ins], {"HB": blk})))
    cells = sorted({key.split("|")[2] for key in k})
    assert cells == ["30[0,0]", "30[1,0]"] and len(k) == 8


def test_missing_source_sub_part_fails_closed():
    real = kernel.realise(doc([PL]))
    lost = RealisedGeometry()
    lost.segments.extend(replace(s, lineage=replace(s.lineage, sub_part=None)) for s in real.segments)
    lost.arcs.extend(real.arcs)
    parts = CB.parts_from_realised("R", lost, lambda path: (), lambda layer, path: CI.VISIBLE)
    assert any(p.identity.key is None for p in parts)
    inp = CI.CanonicalMeasurementInput(CI.SourceRevision("R", CI.EXACT_SOURCE, "a" * 64), "G", "F", 10.0, "U", parts)
    c = CI.MethodContract("M", "1", part_fields=("source_part_id", "part_index"))
    v = CI.validate(inp, c)
    assert v["state"] == CI.METHOD_INPUT_INCOMPLETE and v["missing_fields"]["parts.source_part_id"] == 3


def test_coordinates_never_become_identity():
    """Two parts with the same coordinates and different sources keep different identities; the same source moved
    keeps its identity (coordinates verify, they never identify)."""
    a = keys(kernel.realise(doc([line(1, (0, 0), (10, 0)), line(2, (0, 0), (10, 0))])))
    assert len(a) == 2
    b = keys(kernel.realise(doc([line(1, (5, 5), (15, 5))])))
    assert set(b) <= set(a) | set(b) and "R|H1||SEGMENT|0" in a and "R|H1||SEGMENT|0" in b


def test_k2_route_names_the_same_span_indices():
    import ezdxf
    from engine.source.cad import kernel_ezdxf as K2R
    d = ezdxf.new()
    pl = d.modelspace().add_lwpolyline([(0, 0, 0, 0, 0), (100, 0, 0, 0, 0.5), (100, 100, 0, 0, 0), (100, 100, 0, 0, 0),
                                        (0, 100, 0, 0, 0)], format="xyseb", close=True)
    real = K2R.realise(d)
    h = str(int(pl.dxf.handle, 16))
    k = keys(real)
    idx = sorted((key.split("|")[3], int(key.split("|")[4])) for key in k if f"|H{h}|" in key)
    assert idx == [("ARC", 1), ("SEGMENT", 0), ("SEGMENT", 3), ("SEGMENT", 4)]
