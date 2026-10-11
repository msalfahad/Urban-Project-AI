"""M3 WP4: the detail-evidence rules (stdlib) and the PDF adapter (native text, raster OCR; the ST7757 vector-glyph
page when the private PDF, pymupdf and tesseract are present).

Real bug behind the glyph check: on ST7757 p.13 tesseract reads the CAD-font '3' as '5' in some page
segmentations - two reads AGREED on '5Ø16' where the crop shows '3Ø16'. Agreement of reads is therefore not enough;
on a vector-glyph page each glyph shape votes page-wide, and a read that contradicts its glyphs is rejected.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from engine.source import detail_evidence as DE

ROOT = Path(__file__).resolve().parents[2]
ST_PDF = ROOT / "data/inputs/by_sha256/74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3.pdf"


@pytest.mark.parametrize("text,expect", [
    ("3Ø16", (3, 16, None)), ("3616", (3, 16, None)), ("3014", (3, 14, None)), ("6916", (6, 16, None)),
    ("08/15cm", (None, 8, 0.15)), ("¢8/15cm", (None, 8, 0.15)), ("$8/15cm", (None, 8, 0.15)),
    ("2612/30cm", (2, 12, 0.30)), ("2912/30em", (2, 12, 0.30)), ("5Ø8/M", (None, 8, 0.2)),
])
def test_notation_parses(text, expect):
    p = DE.parse_notation(text)
    assert p["state"] == "PARSED" and (p["count"], p["dia_mm"], p["spacing_m"]) == expect


@pytest.mark.parametrize("text", ["31616", "0816", "3Ø15", "98/150m", "1d", "30", "10cm", "4", "Ø16"])
def test_notation_rejects(text):
    assert DE.parse_notation(text)["state"] in ("UNPARSED", "AMBIGUOUS")


def test_glyph_votes_settle_the_3_5_confusion():
    obs = [(1, "3")] * 8 + [(1, "5")] * 2 + [(2, "0")] * 5 + [(2, "6")] * 4 + [(2, "9")] * 2 + [(3, "1")] * 11 + \
        [(4, "6")] * 6 + [(5, "5")] * 2
    g = DE.glyph_votes(obs)
    assert g == {1: "3", 2: "Ø", 3: "1", 4: "6", 5: None}            # class 5: too few votes
    assert DE.glyph_check("3616", [1, 2, 3, 4], g) == "VERIFIED"
    assert DE.glyph_check("5016", [1, 2, 3, 4], g) == "CONTRADICTED"
    assert DE.glyph_check("5616", [5, 2, 3, 4], g) == "UNCHECKED"      # the count glyph is not known
    assert DE.glyph_check("3616", [1, 2, 3], g) == "UNCHECKED"         # segmentation does not match


def test_captions_and_assembly_roles():
    assert DE.caption_of("Ground Beams. More than 5m length (1:20)")["min_span_m"] == 5.0
    assert DE.caption_of("Ground Beams. Less than 2.5m length (1:20)")["max_span_m"] == 2.5
    assert DE.caption_of("Ground Beams. for exterior walls (1:20)")["condition"] == "EXTERIOR"
    assert DE.caption_of("DRAWING TITLE:") is None
    cap = [{"caption_id": "C1", "box": (0, 100, 100, 110), "caption": DE.caption_of("Ground Beams. Less than 5m")},
           {"caption_id": "C2", "box": (300, 100, 400, 110), "caption": DE.caption_of("Ground Beams. exterior")}]
    tok = lambda rid, x, y, t: {"record_id": rid, "box": (x, y, x + 20, y + 5), "parsed": DE.parse_notation(t)}
    toks = [tok("A", 40, 20, "3Ø14"), tok("B", 40, 40, "Ø8/15"), tok("C", 40, 60, "3Ø14"), tok("D", 40, 70, "3Ø14"),
            tok("E", 340, 20, "3Ø16"), tok("F", 340, 90, "6Ø16")]
    det = {d["caption_id"]: d for d in DE.assemble(toks, cap, rejected=[{"record_id": "R", "box": (340, 50, 360, 55)}])}
    s1 = DE.summarize_bars(det["C1"]["bars"])
    assert s1 == {"TOP": [(3, 14, None)], "LINKS": [(None, 8, 0.15)], "BOTTOM": [(6, 14, None)]}
    assert det["C2"]["rejected_records"] == ["R"] and det["C1"]["rejected_records"] == []
    one = DE.assemble([tok("G", 40, 20, "3Ø14")], cap[:1])[0]
    assert one["state"] == "ROLE_UNRESOLVED"          # one count only: no defensible top / bottom split


def test_validation_and_redaction():
    ok = DE.manual_record("EV-1", page=1, region=(0, 0, 1, 1), text="3Ø16", by="QS", on="2026-10-11")
    bad_who = DE.manual_record("EV-2", page=1, region=(0, 0, 1, 1), text="3Ø16", by="", on="")
    ocr_one = dict(ok, record_id="EV-3", method="OCR_TESSERACT", state="OCR_UNREVIEWED", reads=[{"text": "3Ø16"}])
    owner = dict(ok, record_id="EV-4", raw_text="YEARS 2013")
    ev = {"schema": DE.SCHEMA, "records": [ok, bad_who, ocr_one, owner], "details": []}
    probs = " ".join(DE.validate(ev))
    assert "EV-1" not in probs and "EV-2: a confirmation" in probs and "EV-3: an accepted OCR" in probs
    assert "EV-4: raw text" in probs
    assert DE.redact(r"\\server\job\T7757.dwg") and DE.redact("x", [r"^x$"]) and not DE.redact("3Ø16")


def _pdf_tools():
    pymupdf = pytest.importorskip("pymupdf")
    from tools import pdf_evidence as PEV
    return pymupdf, PEV


def _detail_page(pymupdf, path, raster=False):
    doc = pymupdf.open()
    pg = doc.new_page(width=600, height=420)
    rows = [(60, 60, "3Ø16"), (60, 90, "Ø8/15cm"), (60, 120, "3Ø16"), (60, 135, "3Ø16")]
    for x, y, t in rows:
        pg.insert_text((x, y), t, fontsize=14)
    pg.insert_text((40, 175), "Ground Beams. More than 5m length (1:20)", fontsize=12)
    if raster:
        pix = pg.get_pixmap(dpi=300)
        doc2 = pymupdf.open()
        p2 = doc2.new_page(width=600, height=420)
        p2.insert_image(p2.rect, pixmap=pix)
        doc2.save(str(path))
    else:
        doc.save(str(path))
    return path


def test_native_text_pdf_needs_no_ocr(tmp_path):
    pymupdf, PEV = _pdf_tools()
    pdf = _detail_page(pymupdf, tmp_path / "native.pdf")
    ev = PEV.extract(pdf, tmp_path / "out", use_ocr=False)
    assert not ev["validation"] and ev["pages"][0]["method"] == "NATIVE_TEXT"
    assert {r["state"] for r in ev["records"]} == {"NATIVE_TEXT"}
    det = DE.ground_beam_details(ev)
    assert len(det) == 1 and det[0]["condition"] == "SPAN_MIN" and not det[0]["ocr"]
    assert det[0]["bars"] == {"TOP": [(3, 16, None)], "LINKS": [(None, 8, 0.15)], "BOTTOM": [(6, 16, None)]}


def test_raster_pdf_without_ocr_goes_to_manual(tmp_path):
    pymupdf, PEV = _pdf_tools()
    pdf = _detail_page(pymupdf, tmp_path / "raster.pdf", raster=True)
    ev = PEV.extract(pdf, tmp_path / "out", use_ocr=False)
    assert ev["pages"][0]["method"] == "OCR_UNAVAILABLE" and not ev["records"]
    assert DE.ground_beam_details(ev) == []


@pytest.mark.skipif(not shutil.which("tesseract"), reason="tesseract not installed")
def test_raster_pdf_ocr_needs_unanimous_reads(tmp_path):
    pymupdf, PEV = _pdf_tools()
    pdf = _detail_page(pymupdf, tmp_path / "raster.pdf", raster=True)
    ev = PEV.extract(pdf, tmp_path / "out")
    assert not ev["validation"]
    for r in ev["records"]:
        assert r["method"] == "OCR_TESSERACT" and len(r["reads"]) == 4
        if r["state"] == "OCR_UNREVIEWED":
            assert r["validation"] == "UNANIMOUS_READS" and all(DE.agree(r["parsed"], x["parsed"]) for x in r["reads"])
            assert (tmp_path / "out" / r["crop"]).exists()


@pytest.mark.skipif(not (ST_PDF.exists() and shutil.which("tesseract")), reason="private ST7757 PDF / tesseract")
def test_st7757_ground_beam_details(tmp_path):
    pymupdf, PEV = _pdf_tools()
    ev = PEV.extract(ST_PDF, tmp_path / "ev", pages=[13], redact_patterns=[r"(?i)ALS[EY]?N[YA]?AN"])
    assert not ev["validation"]
    text = json.dumps(ev, ensure_ascii=False)
    assert not DE.HYGIENE.search(text) and "dwg" not in text.lower()
    # the 3 / 5 confusion: no accepted record says 5 bars, and every accepted count read was glyph-verified
    acc = [r for r in ev["records"] if r["state"] == "OCR_UNREVIEWED"]
    assert not any(r["parsed"].get("count") == 5 for r in acc)
    assert all(r["validation"] == "VECTOR_GLYPH_CONSENSUS" for r in acc if r["parsed"]["kind"] == "BARS")
    det = {(d["condition"], d["min_span_m"], d["max_span_m"]): d for d in DE.ground_beam_details(ev)}
    assert det[("SPAN_MIN", 5.0, None)]["bars"] == {"TOP": [(3, 16, None)], "LINKS": [(None, 8, 0.15)],
                                                     "BOTTOM": [(6, 16, None)]}
    assert det[("SPAN_MAX", None, 5.0)]["bars"]["TOP"] == [(3, 14, None)]
    assert det[("SPAN_MAX", None, 5.0)]["bars"]["BOTTOM"] == [(6, 14, None)]
    assert det[("SPAN_MAX", None, 2.5)]["bars"] == {"TOP": [(3, 14, None)], "BOTTOM": [(6, 14, None)]}
    ext = det[("EXTERIOR", None, None)]["bars"]
    assert ext["TOP"] == [(3, 16, None)] and ext["BOTTOM"] == [(6, 16, None)] and ext["SIDE"] == [(2, 12, 0.3)]
    assert all(d["ocr"] for d in det.values())
