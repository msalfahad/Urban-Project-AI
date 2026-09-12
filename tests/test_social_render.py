"""Tile renderer — every layout draws, photos drop in by name, posting order reverses."""

from pathlib import Path

import pytest

from agents.a16_post_designer.schema import LAYOUTS, GridBrief, GridDesign, Photo
from social import render
from social.icons import icon_svg, names

COMPANY = {"name_ar": "شركة إيربن بروجكتس", "instagram": "@upc.kw", "phones": ["+965 90000000"],
           "address_en": "Kuwait", "logo": "assets/logo.svg"}


def _tile(position, layout, **over):
    t = {"position": position, "role": "who", "layout": layout,
         "headline_ar": "نبني بثقة", "headline_en": "BUILT ON TRUST",
         "accent_ar": "بثقة", "accent_en": "TRUST", "body_ar": "نص", "caption_ar": "ك"}
    if layout in ("photo_full", "split"):
        t["photo_needs"] = "واجهة الفيلا"
    t.update(over)
    return t


def _design(tiles):
    return GridDesign.from_dict({"system": {"accent": "#FBAD46"}, "tiles": tiles}, expected_tiles=len(tiles))


BRIEF = GridBrief(account="@upc.kw", tiles=3)


@pytest.mark.parametrize("layout", sorted(LAYOUTS))
def test_every_layout_renders(layout):
    design = _design([_tile(1, layout), _tile(2, "text_card"), _tile(3, "cta")])
    html = render.render_tile_html(design.tiles[0], design, BRIEF, COMPANY)
    assert 'class="tile light"' in html
    assert '<div class="badge">01</div>' in html
    assert "Cairo-Variable.ttf" in html


def test_accent_word_is_highlighted_and_escaped():
    assert str(render.highlight("نبني بثقة", "بثقة")) == 'نبني <span class="accent">بثقة</span>'
    assert str(render.highlight("A <b> B", "<b>")) == 'A <span class="accent">&lt;b&gt;</span> B'
    assert str(render.highlight("no match", "zzz")) == "no match"


def test_missing_photo_draws_placeholder_with_needs():
    design = _design([_tile(1, "split", photo_needs="لقطة قريبة للحديد"), _tile(2, "text_card"), _tile(3, "cta")])
    html = render.render_tile_html(design.tiles[0], design, BRIEF, COMPANY)
    assert "placeholder" in html and "لقطة قريبة للحديد" in html and "Photo 01" in html


def test_photo_file_is_embedded_when_present(tmp_path):
    (tmp_path / "facade.jpg").write_bytes(b"\xff\xd8\xff\xdbfakejpeg")
    brief = GridBrief(account="@upc.kw", tiles=3, photos=[Photo("facade.jpg")])
    design = GridDesign.from_dict(
        {"tiles": [_tile(1, "photo_full", photo_ref="facade.jpg", photo_needs=""),
                   _tile(2, "text_card"), _tile(3, "cta")]},
        expected_tiles=3, inventory={"facade.jpg"})
    html = render.render_tile_html(design.tiles[0], design, brief, COMPANY, photos_dir=tmp_path)
    assert "data:image/jpeg;base64," in html and "Photo 01" not in html


def test_split_photo_side():
    design = _design([_tile(1, "split", photo_side="right"), _tile(2, "split"), _tile(3, "cta")])
    right = render.render_tile_html(design.tiles[0], design, BRIEF, COMPANY)
    left = render.render_tile_html(design.tiles[1], design, BRIEF, COMPANY)
    assert 'class="photo right placeholder"' in right and 'class="side text-left"' in right
    assert 'class="photo left placeholder"' in left and 'class="side text-left"' not in left


def test_bad_photo_side_rejected():
    with pytest.raises(ValueError, match="photo_side"):
        _design([_tile(1, "split", photo_side="top"), _tile(2, "text_card"), _tile(3, "cta")])


def test_dark_theme_class():
    brief = GridBrief(account="@upc.kw", tiles=3, theme="dark")
    design = _design([_tile(1, "text_card"), _tile(2, "text_card"), _tile(3, "cta")])
    assert 'class="tile dark"' in render.render_tile_html(design.tiles[0], design, brief, COMPANY)


def test_bad_colour_falls_back_to_defaults():
    design = GridDesign.from_dict({"system": {"paper": "cream", "accent": "#FBAD46"},
                                   "tiles": [_tile(1, "text_card"), _tile(2, "text_card"), _tile(3, "cta")]},
                                  expected_tiles=3)
    ctx = render.tile_context(design.tiles[0], design, BRIEF, COMPANY)
    assert ctx["paper"] == "#F4EFE8" and ctx["accent"] == "#FBAD46"


def test_cta_tile_lists_company_contact():
    design = _design([_tile(1, "cta"), _tile(2, "text_card"), _tile(3, "cta")])
    html = render.render_tile_html(design.tiles[0], design, BRIEF, COMPANY)
    assert "@upc.kw" in html and "+965 90000000" in html


def test_logo_is_inlined_at_fixed_height():
    design = _design([_tile(1, "cover"), _tile(2, "text_card"), _tile(3, "cta")])
    html = render.render_tile_html(design.tiles[0], design, BRIEF, COMPANY)
    assert 'height="230"' in html and "<svg" in html


def test_posting_order_is_reversed_and_captions_say_so():
    design = _design([_tile(1, "cover"), _tile(2, "text_card"), _tile(3, "cta")])
    assert [t.position for t in render.posting_order(design)] == [3, 2, 1]
    md = render.captions_md(design)
    assert md.index("Tile 03") < md.index("Tile 01")


def test_render_grid_writes_html_and_captions_without_browser(tmp_path):
    design = _design([_tile(1, "cover"), _tile(2, "split"), _tile(3, "cta")])
    result = render.render_grid(design, BRIEF, tmp_path, company=COMPANY, png=False)
    assert [p.name for p in result["html"]] == ["tile_01.html", "tile_02.html", "tile_03.html"]
    assert (tmp_path / "captions.md").read_text(encoding="utf-8").startswith("# Posting order")
    assert result["png"] == [] and result["sheet"] is None


def test_icons_known_and_unknown():
    assert "villa" in names()
    assert "<svg" in icon_svg("villa")
    assert icon_svg("no-such-icon") == icon_svg("crane")
    assert icon_svg("black_structure") == icon_svg("structure")     # alias
