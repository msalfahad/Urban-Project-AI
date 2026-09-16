"""A CAD source that cannot be decoded has not been found empty.

Project 7757's DWG is the first authored CAD source this engine has read,
and the decode has three traps that these tests hold shut. Each was hit for
real before it was named:

  1. LibreDWG's DXF writer aborted inside BLOCKS and emitted no ENTITIES
     section at all. Reading that as "the drawing has no entities" is
     invariant 43 in CAD clothing;
  2. its JSON writer succeeds but leaves `entity` empty on most records, so
     reading the name alone discards ten thousand well-identified entities;
  3. it emits tens of thousands of spurious BLOCK_BEGIN/BLOCK_END records —
     the same defect that killed the DXF writer — and counting those as
     geometry inflates the drawing thirtyfold.

Plus two unit traps: $INSUNITS = 0 is no declaration rather than a metric
one, and DIMLFAC means the numbers printed on the sheet are not in the
drawing's own unit.
"""

from __future__ import annotations

import pytest

from engine import cad_source as cad
from engine.reference_mapping import SealedReferenceError
from tools.audit_cad_source import NO_CONVERTER, audit


def _decode(*, insunits=4, dimlfac=None, entities=(), delimiters=0,
            measurement=None):
    """A LibreDWG-shaped JSON decode, built to order."""
    objs = [
        {"object": "LAYER", "handle": [0, 1, 10], "name": "W"},
        {"object": "LAYER", "handle": [0, 1, 11], "name": "D"},
        {"object": "BLOCK_HEADER", "handle": [0, 1, 20], "name": "D115"},
        {"object": "BLOCK_HEADER", "handle": [0, 1, 21],
         "name": "*MODEL_SPACE"},
    ]
    for i, (kind_code, layer_h, blk_h) in enumerate(entities):
        row = {"entity": "", "type": kind_code, "handle": [0, 1, 100 + i],
               "_subclass": "AcDbWhatever", "layer": [5, 1, layer_h, layer_h]}
        if blk_h:
            row["block_header"] = [5, 1, blk_h, blk_h]
        objs.append(row)
    for i in range(delimiters):
        objs.append({"entity": "", "type": 4 if i % 2 == 0 else 5,
                     "handle": [0, 1, 900 + i], "_subclass": "AcDbBlockBegin",
                     "layer": [5, 1, 10, 10]})
    hdr = {"INSUNITS": insunits, "LUNITS": 2, "LIMMAX": [84100.0, 59400.0],
           "TILEMODE": 1}
    if dimlfac is not None:
        hdr["DIMLFAC"] = dimlfac
    if measurement is not None:
        hdr["MEASUREMENT"] = measurement
    return {"FILEHEADER": {"version": "AC1018"}, "HEADER": hdr,
            "OBJECTS": objs}


def test_an_unnamed_record_is_named_from_its_type_code():
    """Trap 2: `entity` is empty, and the type code identifies it exactly."""
    dec = _decode(entities=[(19, 10, None), (77, 10, None), (17, 11, None),
                            (44, 11, None), (21, 11, None)])
    cen = cad.census(dec, source_file="x.dwg")
    assert cen.by_kind() == {"LINE": 1, "LWPOLYLINE": 1, "ARC": 1,
                             "MTEXT": 1, "DIMENSION_LINEAR": 1}
    assert len(cen.entities) == 5


def test_spurious_block_delimiters_are_excluded_and_reported():
    """Trap 3: thirty thousand BLOCK/ENDBLK records are not drawing content."""
    dec = _decode(entities=[(19, 10, None)] * 4, delimiters=1000)
    cen = cad.census(dec, source_file="x.dwg")
    assert len(cen.entities) == 4, "only the real entities are counted"
    assert cen.excluded_block_delimiters == 1000
    rec = cen.record()
    assert rec["excluded_block_delimiter_records"] == 1000
    assert "inflate the drawing" in rec["why_those_were_excluded"]
    assert "BLOCK_BEGIN" not in rec["entities_by_kind"]
    assert "BLOCK_END" not in rec["entities_by_kind"]


def test_a_decode_with_no_objects_raises_rather_than_reporting_empty():
    """Trap 1: nothing decoded is not a drawing with nothing in it."""
    with pytest.raises(cad.CadReadError) as exc:
        cad.census({"OBJECTS": []}, source_file="x.dwg")
    assert "not the same as the drawing being empty" in str(exc.value)


def test_no_converter_gives_no_entity_counts_at_all(tmp_path):
    dwg = tmp_path / "x.dwg"
    dwg.write_bytes(b"AC1018" + b"\0" * 64)
    rec = audit(str(dwg), work_dir=str(tmp_path / "w"),
                converter=str(tmp_path / "absent"))
    assert rec["conversion"]["status"] == NO_CONVERTER
    assert rec["representation"] == "NOT_ESTABLISHED"
    assert "NOT a finding that the drawing is empty" in rec["why"]
    assert "census" not in rec


def test_millimetres_are_reported_as_a_declaration():
    cen = cad.census(_decode(insunits=4, entities=[(19, 10, None)]),
                     source_file="x.dwg")
    u = cen.declared_units()
    assert u["insunits_code"] == 4
    assert u["insunits_means"] == "millimetres"
    assert u["unit_is_declared"] is True
    assert "not a measurement" in u["this_is"]


def test_unitless_is_not_millimetres():
    cen = cad.census(_decode(insunits=0, entities=[(19, 10, None)]),
                     source_file="x.dwg")
    u = cen.declared_units()
    assert u["unit_is_declared"] is False
    assert "NO unit" in u["insunits_means"]
    assert "NOT a declaration of millimetres" in cad.INSUNITS[0]


def test_an_absent_variable_is_not_an_unrecognised_one():
    """MEASUREMENT is missing from this decoder's JSON. Absent != garbage."""
    cen = cad.census(_decode(entities=[(19, 10, None)]), source_file="x.dwg")
    u = cen.declared_units()
    assert u["measurement_code"] is None
    assert "NOT_PRESENT_IN_THIS_DECODE" in u["measurement_means"]
    assert "not a reading of it" in u["measurement_means"]
    # And when it IS present, it is read.
    cen2 = cad.census(_decode(entities=[(19, 10, None)], measurement=1),
                      source_file="x.dwg")
    assert cen2.declared_units()["measurement_code"] == 1
    assert "metric" in cen2.declared_units()["measurement_means"]


def test_dimlfac_separates_the_printed_unit_from_the_drawing_unit():
    """The 10x trap: geometry in mm, dimension text in cm."""
    cen = cad.census(_decode(insunits=4, dimlfac=0.1,
                             entities=[(21, 11, None)]), source_file="x.dwg")
    u = cen.declared_units()
    assert u["dimension_text_factor"] == 0.1
    assert "NOT the drawing unit" in u["dimension_text_means"]
    # A factor of 1 is the ordinary case and adds no note to read wrongly.
    plain = cad.census(_decode(insunits=4, dimlfac=1.0,
                               entities=[(21, 11, None)]),
                       source_file="x.dwg")
    assert "dimension_text_factor" not in plain.declared_units()


def test_layers_blocks_and_inserts_are_resolved_by_handle():
    dec = _decode(entities=[(19, 10, None), (19, 10, None), (17, 11, None),
                            (7, 11, 20)])
    cen = cad.census(dec, source_file="x.dwg")
    by_layer = cen.by_layer()
    assert by_layer["W"]["entities"] == 2
    assert by_layer["D"]["entities"] == 2
    assert cen.block_inserts == {"D115": 1}
    assert "D115" in cen.blocks
    assert "*MODEL_SPACE" not in cen.blocks, "block-space records are not blocks"


def test_a_line_on_a_wall_layer_is_not_yet_called_a_wall():
    """The census groups primitives. Naming a wall needs evidence, later."""
    cen = cad.census(_decode(entities=[(19, 10, None)] * 3),
                     source_file="x.dwg")
    rec = cen.record()
    assert rec["group_totals"]["geometry"] == 3
    assert "not yet a wall" in rec["what_is_not_established_here"]
    assert rec["contains_no_measurement"] is True


def test_the_sealed_take_off_is_refused_here_too(tmp_path):
    with pytest.raises(SealedReferenceError):
        audit("P7757_area_takeoff_benchmark.pdf", work_dir=str(tmp_path))
