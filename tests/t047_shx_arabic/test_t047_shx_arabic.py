"""T-047: SHX_ARABIC_INTAKE_V1 - Arabic text drawn with legacy SHX fonts (engine.source.cad.shx_arabic).

Hand truth. Each coded string below was typed by hand from the Arabic (101) keyboard (key -> letter), never produced
by the module or by inverting its table. Synthetic drawings only (not a client drawing); style names and font files
are invented for this fixture.

  plhl    p=ح l=م h=ا l=م            -> حمام        (bath)
  l'fo    l=م '=ط f=ب o=خ            -> مطبخ        (kitchen)
  lks,f   l=م k=ن s=س ,=و f=ب        -> منسوب       (level)
  yvtm k,l  y=غ v=ر t=ف m=ة / k=ن ,=و l=م -> غرفة نوم (bedroom)
  whgm    w=ص h=ا g=ل m=ة            -> صالة        (hall)
  lo.k    l=م o=خ .=ز k=ن            -> مخزن        (store; '.' between letters is ز)
  ]v[     ]=د v=ر [=ج                -> درج         (stair)
  s'p     s=س '=ط p=ح                -> سطح         (roof)
  ]d,hkdm ]=د d=ي ,=و h=ا k=ن d=ي m=ة -> ديوانية    (diwaniya)
  lsfp    l=م s=س f=ب p=ح            -> مسبح        (pool)
  X-ARAB glyph family: HMaM  H=ح M=م a=ا M=م -> حمام

Held cases: '.' between two digits (decimal point or ز: no reviewed source) and '<' (in no reviewed map) keep a '?'
and their index; an unknown font with Latin codes is never decoded.

Block geometry (mm drawing): block TAG holds a TEXT at (100, 0). INSERT at (5000, 0), xscale -1, rotation 90:
  mirror x -> (-100, 0); rotate 90 -> (0, -100); + insert -> world (5000, -100).
"""

from __future__ import annotations

import ezdxf
import pytest

from engine.source.cad import shx_arabic as S

KB = "xarb.shx"

WORDS = [
    ("plhl", "حمام"), ("l'fo", "مطبخ"), ("lks,f", "منسوب"), ("yvtm k,l", "غرفة نوم"), ("whgm", "صالة"),
    ("lo.k", "مخزن"), ("]v[", "درج"), ("s'p", "سطح"), ("]d,hkdm", "ديوانية"), ("lsfp", "مسبح"),
]


@pytest.mark.parametrize("raw,expected", WORDS)
def test_keyboard_words_decode_exactly(raw, expected):
    r = S.decode_text(raw, KB)
    assert r["text"] == expected
    assert r["status"] == S.DECODED and r["release"] == S.RELEASED and r["issues"] == []


def test_upper_case_keys_are_the_same_letter():
    assert S.decode_text("PLHL", "XARB2.SHX")["text"] == "حمام"


def test_glyph_family_font():
    r = S.decode_text("HMaM", "x-arab1b.shx")
    assert r["text"] == "حمام" and r["status"] == S.DECODED


def test_numbers_mixed_with_arabic():
    r = S.decode_text("lks,f 350", KB)
    assert r["text"] == "منسوب 350" and r["status"] == S.DECODED


def test_decimal_point_between_digits_is_held_not_guessed():
    r = S.decode_text("lks,f 3.50", KB)
    assert r["status"] == S.PARTIAL and r["release"] == S.HELD
    assert r["text"] == "منسوب 3?50"
    assert r["issues"] == [{"index": 7, "code": ".", "reason": "DIGIT_SEPARATOR_OR_LETTER_NOT_ESTABLISHED"}]


def test_unmapped_code_is_held_with_index():
    r = S.decode_text("lks<,f", KB)
    assert r["status"] == S.PARTIAL and r["text"] == "منس?وب"
    assert r["issues"][0]["index"] == 3 and r["issues"][0]["code"] == "<"


def test_unknown_font_with_latin_codes_is_held_and_untouched():
    r = S.decode_text("plhl", "kufi_custom.shx")
    assert r["status"] == S.UNDECODED and r["release"] == S.HELD and r["text"] == "plhl"


def test_unknown_font_without_letter_codes_is_still_held():
    r = S.decode_text("350", "kufi_custom.shx")
    assert r["status"] == S.UNKNOWN_NO_CODES and r["release"] == S.HELD and r["text"] == "350"


@pytest.mark.parametrize("font", ["simplex.shx", "txt", "C:\\Fonts\\ROMANS.SHX", "isocp.shx"])
def test_latin_text_on_latin_font_untouched(font):
    r = S.decode_text("KITCHEN 4.20", font)
    assert r["text"] == "KITCHEN 4.20" and r["status"] == S.LATIN and r["release"] == S.NOT_APPLICABLE


@pytest.mark.parametrize("raw", ["حمام", "plhl"])
def test_truetype_text_is_unicode_and_untouched(raw):
    r = S.decode_text(raw, "tahoma.ttf")
    assert r["text"] == raw and r["status"] == S.UNICODE


def test_arabic_unicode_inside_keyboard_font_passes_through():
    r = S.decode_text("حمام plhl", KB)
    assert r["text"] == "حمام حمام" and r["status"] == S.DECODED


def test_text_control_codes():
    assert S.decode_text("%%c200", "simplex.shx")["text"] == "\u2300200"
    assert S.decode_text("plhl %%d", KB)["text"] == "حمام \u00b0"


def test_mtext_font_switches_and_groups():
    raw = r"{\Fxarb.shx;plhl}\P KITCHEN \fArial|b0|i0|c0|p34;حمام"
    r = S.decode_text(raw, "romans.shx", entity="MTEXT")
    assert r["text"] == "حمام\n KITCHEN حمام" and r["status"] == S.DECODED
    assert [x["kind"] for x in r["runs"]] == [S.ARABIC_SHX, S.LATIN_SHX, S.UNICODE_FONT]


def test_mtext_unknown_switch_holds_whole_text():
    r = S.decode_text(r"{\Fkufi_custom.shx;plhl} \H2.5;lks,f", KB, entity="MTEXT")
    assert r["status"] == S.UNDECODED and r["release"] == S.HELD
    assert r["text"] == "plhl منسوب"


def test_font_table_has_a_source_per_entry():
    for row in S.FONT_TABLE:
        assert row["source"]
    assert S.font_class("xarb.shx")["kind"] == S.ARABIC_SHX
    assert S.font_class("nothing.shx")["kind"] == S.UNKNOWN
    assert S.font_class("")["kind"] == S.UNKNOWN


# ---------------------------------------------------------------- synthetic DXF

def _doc(units):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = units
    for name, font in (("NOTE-AR", "xarb.shx"), ("LBL", "X-ARABIC1.shx"), ("EN", "simplex.shx"),
                       ("UNI", "tahoma.ttf"), ("ODD", "kufi_custom.shx")):
        doc.styles.new(name, dxfattribs={"font": font})
    return doc


def _build(tmp_path, units, scale):
    doc = _doc(units)
    msp = doc.modelspace()
    msp.add_text("plhl", dxfattribs={"style": "NOTE-AR", "insert": (1 * scale, 2 * scale), "rotation": 37})
    t = msp.add_text("lks,f 350", dxfattribs={"style": "NOTE-AR", "insert": (3 * scale, 0)})
    t.dxf.text_generation_flag = 2 | 4
    msp.add_text("HMaM", dxfattribs={"style": "LBL", "insert": (0, 0)})
    msp.add_text("KITCHEN", dxfattribs={"style": "EN", "insert": (0, 0)})
    msp.add_text("حمام", dxfattribs={"style": "UNI", "insert": (0, 0)})
    msp.add_text("lsfp", dxfattribs={"style": "ODD", "insert": (0, 0)})
    msp.add_text("s'p", dxfattribs={"style": "NO-SUCH-STYLE", "insert": (0, 0)})
    tag = doc.blocks.new("TAG")
    tag.add_text("l'fo", dxfattribs={"style": "NOTE-AR", "insert": (0.1 * scale, 0)})
    ins = msp.add_blockref("TAG", (5 * scale, 0), dxfattribs={"xscale": -1, "rotation": 90})
    ins.add_attrib("ROOM", "]v[", insert=(5 * scale, 0), dxfattribs={"style": "NOTE-AR"})
    outer = doc.blocks.new("OUTER")
    outer.add_blockref("TAG", (0, 0), dxfattribs={"rotation": 180})
    msp.add_blockref("OUTER", (10 * scale, 0))
    doc.paperspace().add_mtext(r"{\Fxarb.shx;yvtm k,l}\PBEDROOM", dxfattribs={"style": "EN"})
    p = tmp_path / f"fixture_{units}.dxf"
    doc.saveas(p)
    return ezdxf.readfile(p)


@pytest.mark.parametrize("units,scale", [(4, 1000.0), (6, 1.0)])
def test_dxf_intake_every_text_reported(tmp_path, units, scale):
    recs = S.records_from_doc(_build(tmp_path, units, scale))
    got = {(r["raw"], r["layout"]): r for r in recs}
    assert len(recs) == 11
    assert all(r["insunits"] == units for r in recs)
    r = got[("plhl", "Model")]
    assert r["text"] == "حمام" and r["rotation_deg_ocs"] == pytest.approx(37)
    r = got[("lks,f 350", "Model")]
    assert r["text"] == "منسوب 350" and r["backward"] and r["upside_down"]
    assert got[("HMaM", "Model")]["text"] == "حمام"
    assert got[("KITCHEN", "Model")]["status"] == S.LATIN
    assert got[("حمام", "Model")]["status"] == S.UNICODE
    assert got[("lsfp", "Model")]["status"] == S.UNDECODED
    r = got[("s'p", "Model")]
    assert r["status"] == S.UNDECODED and r["style_problem"] == "STYLE_NOT_FOUND"
    assert got[("]v[", "Model")]["text"] == "درج" and got[("]v[", "Model")]["mirrored_by_block"]
    kitchens = [r for r in recs if r["raw"] == "l'fo"]
    assert len(kitchens) == 2 and all(r["text"] == "مطبخ" for r in kitchens)
    mirrored = [r for r in kitchens if r["mirrored_by_block"]]
    assert len(mirrored) == 1
    x, y = mirrored[0]["insert"]
    assert x == pytest.approx(5 * scale) and y == pytest.approx(-0.1 * scale)
    nested = [r for r in kitchens if not r["mirrored_by_block"]][0]
    assert nested["insert"][0] == pytest.approx(10 * scale - 0.1 * scale)
    ps = [r for r in recs if r["layout"] != "Model"]
    assert len(ps) == 1 and ps[0]["text"] == "غرفة نوم\nBEDROOM" and ps[0]["status"] == S.DECODED
    c = S.census(recs)
    assert c["total"] == 11 and len(c["held"]) == 2


def test_policy_record_lists_sources():
    p = S.policy_record()
    assert p["id"] == S.POLICY_ID and all(r["source"] for r in p["font_table"])


def test_ocs_minus_z_maps_x_to_minus_x():
    # arbitrary axis algorithm, extrusion (0, 0, -1): Ax = (-1, 0, 0), Ay = (0, 1, 0) -> OCS (3, 4) is world (-3, 4)
    x, y = S._ocs_to_wcs((3.0, 4.0, 0.0), (0, 0, -1))
    assert x == pytest.approx(-3.0) and y == pytest.approx(4.0)
