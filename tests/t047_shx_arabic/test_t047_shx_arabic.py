"""T-047: SHX Arabic text intake (engine/source/cad/shx_arabic.py) on a hand-made DXF with HAND-WRITTEN truth.

Synthetic drawing (not any project: own style names and font file names). Keys were typed by hand from the Arabic (101)
keyboard (h=ا f=ب j=ت [=ج p=ح o=خ ]=د v=ر .=ز s=س w=ص '=ط y=غ t=ف g=ل l=م k=ن m=ة ,=و), and the expected Arabic is
written by hand, never produced by the module:
    plhl -> حمام      l'fo -> مطبخ      lks,f -> منسوب     whgm -> صالة      yvtm k,l -> غرفة نوم
    ]v[  -> درج       lo.k -> مخزن ("." not between digits is the key of ز)
    lks,f 150 -> منسوب 150         yvtm 2 -> غرفة 2         s'p -> سطح
    PLHL -> حمام (upper-case key = alternate glyph of the same letter, frozen decoder rule)
    HMam on the X-ARAB family -> حمام (frozen glyph table: H=ح M=م a=ا m=م)
Adversarial: rotated 37 deg, backward + upside-down flags, text in a block inserted mirrored (xscale -1), the same
drawing in mm (INSUNITS 4) and in m (INSUNITS 6); "lks,f 1.50" -> the "." between digits is AMBIGUOUS (HELD);
"lks<,f" -> "<" not in the map (HELD, listed); an unknown font with Latin codes -> UNDECODED_SHX_CANDIDATE (HELD);
a style missing from the STYLE table -> unknown font -> HELD, never Latin by default; Latin text on romans.shx and
Unicode Arabic on arial.ttf are returned exactly as stored; a mixed MTEXT decodes its Arabic run only.
"""

from __future__ import annotations

import ezdxf
import pytest

from engine.source.cad import shx_arabic as S

AR_KB, AR_GLYPH, LAT, TTF, ODD = "NOTE-AR-K", "LBL-AR-G", "NOTE-EN", "UNI-AR", "NOTE-AR-Q"
STYLE_FONTS = {AR_KB: r"C:\cad\fonts\XARB2.SHX", AR_GLYPH: "x-arabic1.shx", LAT: "romans.shx", TTF: "arial.ttf",
               ODD: "qalam_ar.shx"}

KB_WORDS = [  # (stored keys, hand-written Arabic)
    ("plhl", "حمام"), ("l'fo", "مطبخ"), ("lks,f", "منسوب"), ("whgm", "صالة"), ("yvtm k,l", "غرفة نوم"),
    ("]v[", "درج"), ("lo.k", "مخزن"), ("lks,f 150", "منسوب 150"), ("yvtm 2", "غرفة 2"), ("s'p", "سطح"),
    ("PLHL", "حمام")]


def _build(path, insunits, scale):
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = insunits
    for name, font in STYLE_FONTS.items():
        doc.styles.add(name, font=font)
    msp = doc.modelspace()
    for i, (keys, _) in enumerate(KB_WORDS):
        t = msp.add_text(keys, dxfattribs={"style": AR_KB, "height": 0.25 * scale, "rotation": 37.0 if i % 2 else 0.0})
        t.dxf.insert = (i * 3 * scale, 0)
        if i == 3:
            t.dxf.text_generation_flag = 2 | 4  # backward + upside down (mirrored text)
        t.dxf.layer = f"W{i:02d}"
    blk = doc.blocks.new("TAG-X")
    blk.add_text("HMam", dxfattribs={"style": AR_GLYPH, "height": 0.2 * scale, "layer": "GLYPH"})
    msp.add_blockref("TAG-X", (0, 10 * scale), dxfattribs={"xscale": -1, "rotation": 37})
    msp.add_text("BED  ROOM 1", dxfattribs={"style": LAT, "layer": "LATIN"})
    msp.add_text("حمام", dxfattribs={"style": TTF, "layer": "UNI"})
    msp.add_text("plhl", dxfattribs={"style": ODD, "layer": "ODD"})
    msp.add_text("plhl", dxfattribs={"style": "NO-SUCH-STYLE", "layer": "MISSING"})
    msp.add_text("lks,f 1.50", dxfattribs={"style": AR_KB, "layer": "DEC"})
    msp.add_text("lks<,f", dxfattribs={"style": AR_KB, "layer": "LT"})
    msp.add_mtext("KITCHEN\\P{\\FXARB2.shx|b0;l'fo}", dxfattribs={"style": LAT, "layer": "MIX"})
    doc.saveas(path)


def _read(path):
    """Lab-side reader (ezdxf): STYLE table + every TEXT / MTEXT in model space and blocks."""
    doc = ezdxf.readfile(str(path))
    styles = {}
    for st in doc.styles:
        styles[st.dxf.name.upper()] = {"font": st.dxf.get("font", "") or "", "bigfont": st.dxf.get("bigfont", "") or ""}
    texts = []
    for space in [doc.modelspace()] + [b for b in doc.blocks if not b.name.startswith("*")]:
        for e in space:
            if e.dxftype() == "TEXT":
                texts.append({"handle": e.dxf.handle, "type": "TEXT", "value": e.dxf.text, "style": e.dxf.style,
                              "layer": e.dxf.layer, "rotation": e.dxf.rotation, "flags": e.dxf.text_generation_flag})
            elif e.dxftype() == "MTEXT":
                texts.append({"handle": e.dxf.handle, "type": "MTEXT", "value": e.text, "style": e.dxf.style,
                              "layer": e.dxf.layer})
    return styles, texts


@pytest.fixture(params=[(4, 1000.0), (6, 1.0)], ids=["mm", "m"])
def run(request, tmp_path):
    p = tmp_path / "synthetic_shx.dxf"
    _build(p, *request.param)
    styles, texts = _read(p)
    out = S.decode_all(texts, styles)
    return texts, out, {r["layer"]: r for r in out["records"]}


def test_ten_plus_words_decode_exactly_whatever_the_rotation_mirror_or_units(run):
    _, _, by = run
    for i, (keys, arabic) in enumerate(KB_WORDS):
        r = by[f"W{i:02d}"]
        assert r["raw"] == keys
        assert r["decoded"] == arabic, (keys, r["decoded"])
        assert (r["state"], r["status"]) == (S.DECODED, S.RELEASED)
        assert r["undecoded"] == [] and r["families"] == ["ARABIC_KEYBOARD_101"]
    assert by["W03"]["flags"] == 6 and by["W01"]["rotation"] == pytest.approx(37.0)  # placement carried through


def test_glyph_family_in_a_mirrored_block():
    styles = {AR_GLYPH: {"font": STYLE_FONTS[AR_GLYPH]}}
    r = S.decode_text({"handle": "A", "type": "TEXT", "value": "HMam", "style": AR_GLYPH}, styles)
    assert (r["decoded"], r["state"]) == ("حمام", S.DECODED)


def test_block_text_decodes(run):
    _, _, by = run
    assert (by["GLYPH"]["decoded"], by["GLYPH"]["state"]) == ("حمام", S.DECODED)


def test_latin_and_unicode_text_untouched(run):
    _, _, by = run
    assert (by["LATIN"]["decoded"], by["LATIN"]["state"], by["LATIN"]["status"]) == ("BED  ROOM 1", S.UNCHANGED,
                                                                                   S.RELEASED)
    assert (by["UNI"]["decoded"], by["UNI"]["state"]) == ("حمام", S.UNCHANGED)
    assert by["LATIN"]["fonts"][0]["class"] == S.LATIN and by["UNI"]["fonts"][0]["class"] == S.UNICODE


def test_unknown_font_and_missing_style_are_held_candidates_never_latin(run):
    _, _, by = run
    for layer in ("ODD", "MISSING"):
        r = by[layer]
        assert (r["state"], r["status"]) == (S.CANDIDATE, S.HELD)
        assert r["decoded"] == "plhl" and r["candidates"]


def test_decimal_separator_and_unmapped_code_are_held_and_listed(run):
    _, _, by = run
    d = by["DEC"]
    assert (d["state"], d["status"]) == (S.PARTIAL, S.HELD)
    assert d["decoded"] == "منسوب 1?50"
    assert d["undecoded"] == [{"index": 7, "char": ".", "reason": S.AMBIGUOUS_SEP}]
    lt = by["LT"]
    assert lt["decoded"] == "منس?وب" and lt["undecoded"] == [{"index": 3, "char": "<", "reason": S.NOT_IN_MAP}]
    assert lt["status"] == S.HELD


def test_mixed_mtext_decodes_its_arabic_run_only(run):
    _, _, by = run
    m = by["MIX"]
    assert m["decoded"] == "KITCHEN\nمطبخ"
    assert (m["state"], m["status"]) == (S.DECODED, S.RELEASED)
    assert [f["class"] for f in m["fonts"]] == [S.LATIN, S.ARABIC_LEGACY]


def test_every_text_reported_once(run):
    texts, out, _ = run
    assert len(out["records"]) == len(texts) == len(KB_WORDS) + 8
    assert sum(out["census"].values()) == len(texts)
    assert sorted(out["held"]) == sorted(r["handle"] for r in out["records"]
                                         if r["layer"] in ("ODD", "MISSING", "DEC", "LT"))


def test_font_table_entries_name_a_source():
    for row in S.policy_record()["font_table"]:
        assert row["source"]
    assert S.classify_font("ROMANS.SHX")["class"] == S.LATIN
    assert S.classify_font("")["class"] == S.UNKNOWN
    assert S.classify_font(r"D:\x\X-ARAB1B.shx")["family"] == "XARAB_GLYPH_V1"


def test_mtext_unsupported_code_is_reported_not_dropped():
    styles = {AR_KB: {"font": "xarb.shx"}}
    r = S.decode_text({"handle": "B", "type": "MTEXT", "value": "plhl\\Zx", "style": AR_KB}, styles)
    assert r["unsupported_codes"] and r["status"] == S.HELD


def test_empty_value_is_reported_unchanged():
    r = S.decode_text({"handle": "C", "type": "TEXT", "value": "", "style": AR_KB}, {AR_KB: {"font": "xarb.shx"}})
    assert r["state"] in (S.DECODED, S.UNCHANGED) and r["decoded"] == ""
