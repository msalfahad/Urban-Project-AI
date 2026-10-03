"""R8.6A: an entity whose ezdxf class lacks a common attribute (RTEXT has no 'layer') reaches the UNHANDLED
finding; it does not stop the K2 route for the whole document. Synthetic DXF written under pytest's tmp_path."""

from __future__ import annotations

import io

import ezdxf

from engine.source.cad import kernel_ezdxf as K2

RTEXT = ("  0\nRTEXT\n  5\nABCD\n330\n1F\n100\nAcDbEntity\n  8\n0\n100\nRText\n 10\n1.0\n 20\n2.0\n 30\n0.0\n"
         " 40\n2.5\n  7\nStandard\n 70\n0\n  1\nhello\n")


def _doc_with_rtext(tmp_path):
    doc = ezdxf.new("R2018")
    doc.modelspace().add_line((0, 0), (10, 0))
    s = io.StringIO()
    doc.write(s)
    t = s.getvalue()
    end = t.index("ENDSEC", t.index("ENTITIES"))
    cut = t.rindex("  0\n", 0, end)
    p = tmp_path / "rtext.dxf"
    p.write_text(t[:cut] + RTEXT + t[cut:])
    return p


def test_rtext_reaches_unhandled_and_the_route_continues(tmp_path):
    doc, findings = K2.load(_doc_with_rtext(tmp_path))
    assert not findings
    rt = [e for e in doc.modelspace() if e.dxftype() == "RTEXT"]
    assert rt and not rt[0].dxf.is_supported("layer")          # the condition that used to raise
    rg = K2.realise(doc)
    assert len(rg.segments) == 1
    assert [(f.code, f.obs_id) for f in rg.findings] == [("UNHANDLED", f"D2:{0xABCD}")]          # obs ids carry the decimal handle


def test_attr_reads_supported_attributes_unchanged(tmp_path):
    doc, _ = K2.load(_doc_with_rtext(tmp_path))
    line = next(e for e in doc.modelspace() if e.dxftype() == "LINE")
    assert K2._attr(line, "layer") == "0" and K2._attr(line, "invisible", 0) == 0
    rt = next(e for e in doc.modelspace() if e.dxftype() == "RTEXT")
    assert K2._attr(rt, "layer") is None and K2._attr(rt, "invisible", 7) == 7
