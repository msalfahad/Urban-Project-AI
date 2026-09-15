"""A CAD source that cannot be opened has not been found empty.

Project 7757's DWG is authored in AutoCAD Architecture, so its walls are AEC
custom objects. A reader without the object enabler sees proxies, and two
readings of that are wrong in opposite directions:

  "the file has no walls"        — invariant 43, in CAD clothing;
  "the proxies are walls"        — geometry asserted from a cache nobody
                                   decoded.

These tests hold the audit between the two: an unopenable file reports
NOT_ESTABLISHED, and a proxy population is counted and named rather than
folded into the entity totals.
"""

from __future__ import annotations

import ezdxf
import pytest

from engine.reference_mapping import SealedReferenceError
from tools.audit_cad_source import (CONVERT_FAILED, INSUNITS, NO_CONVERTER,
                                    READ_OK, audit, to_dxf)


def _dxf(path, *, insunits: int = 4):
    doc = ezdxf.new("R2004", setup=True)
    doc.header["$INSUNITS"] = insunits
    doc.header["$MEASUREMENT"] = 1
    doc.layers.add("A-WALL")
    msp = doc.modelspace()
    msp.add_line((0, 0), (5000, 0), dxfattribs={"layer": "A-WALL"})
    msp.add_lwpolyline([(0, 0), (5000, 0), (5000, 3000), (0, 3000)],
                       dxfattribs={"layer": "A-WALL"})
    msp.add_text("SALOON", dxfattribs={"layer": "A-WALL"})
    doc.saveas(path)
    return str(path)


def _fake_converter(tmp_path, dxf_src: str):
    """A stand-in for the real converter: emits a prepared DXF.

    Named `dwg2dxf` on purpose — the audit picks its argument form from the
    converter's name, so a stand-in under another name would exercise the
    wrong command line and pass for the wrong reason.
    """
    script = tmp_path / "dwg2dxf"
    script.write_text(
        "#!/bin/sh\n"
        "# dwg2dxf form: -o OUT IN\n"
        f'cp "{dxf_src}" "$2"\n', encoding="utf-8")
    script.chmod(0o755)
    return str(script)


def test_no_converter_is_not_an_empty_drawing(tmp_path):
    dwg = tmp_path / "x.dwg"
    dwg.write_bytes(b"AC1018" + b"\0" * 64)
    rec = audit(str(dwg), work_dir=str(tmp_path / "w"),
                converter=str(tmp_path / "does-not-exist"))
    assert rec["conversion"]["status"] == NO_CONVERTER
    assert rec["representation"] == "NOT_ESTABLISHED"
    assert "NOT a finding that the drawing is empty" in rec["why"]
    # No entity counts at all, rather than zeroes that would read as facts.
    assert "entities_by_type" not in rec


def test_a_failed_conversion_is_reported_not_swallowed(tmp_path):
    dwg = tmp_path / "x.dwg"
    dwg.write_bytes(b"AC1018" + b"\0" * 64)
    conv = tmp_path / "failconv"
    conv.write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
    conv.chmod(0o755)
    out = to_dxf(str(dwg), str(tmp_path / "out.dxf"), converter=str(conv))
    assert out["status"] == CONVERT_FAILED
    assert out["exit_code"] == 3


def test_declared_units_are_quoted_as_a_declaration(tmp_path):
    src = _dxf(tmp_path / "src.dxf", insunits=4)
    dwg = tmp_path / "x.dwg"
    dwg.write_bytes(b"AC1018" + b"\0" * 64)
    rec = audit(str(dwg), work_dir=str(tmp_path / "w"),
                converter=_fake_converter(tmp_path, src))
    assert rec["conversion"]["status"] == READ_OK
    assert rec["declared_units"]["insunits_code"] == 4
    assert rec["declared_units"]["insunits_means"] == "millimetres"
    assert "not a measurement" in rec["declared_units"]["this_is"]


def test_unitless_is_not_millimetres(tmp_path):
    """$INSUNITS = 0 is the trap: no declaration, not a metric one."""
    src = _dxf(tmp_path / "src.dxf", insunits=0)
    dwg = tmp_path / "x.dwg"
    dwg.write_bytes(b"AC1018" + b"\0" * 64)
    rec = audit(str(dwg), work_dir=str(tmp_path / "w"),
                converter=_fake_converter(tmp_path, src))
    assert rec["declared_units"]["insunits_code"] == 0
    assert "NO unit" in rec["declared_units"]["insunits_means"]
    assert "not a declaration of millimetres" in INSUNITS[0].lower()


def test_entities_layers_and_annotation_are_counted(tmp_path):
    src = _dxf(tmp_path / "src.dxf")
    dwg = tmp_path / "x.dwg"
    dwg.write_bytes(b"AC1018" + b"\0" * 64)
    rec = audit(str(dwg), work_dir=str(tmp_path / "w"),
                converter=_fake_converter(tmp_path, src))
    assert rec["entity_total"] >= 3
    assert rec["line_representations"]["LINE"] == 1
    assert rec["line_representations"]["LWPOLYLINE"] == 1
    assert rec["annotation"]["TEXT"] == 1
    assert "A-WALL" in rec["layers"]["names"]
    # A drawing with no proxies says so as a count, not by omission.
    assert rec["proxy_population"]["count"] == 0
    assert "NOT an absent wall" in rec["proxy_population"]["what_a_proxy_is"]


def test_the_sealed_take_off_is_refused_here_too(tmp_path):
    with pytest.raises(SealedReferenceError):
        audit("P7757_area_takeoff_benchmark.pdf", work_dir=str(tmp_path))
