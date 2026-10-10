"""A16 grid mode — a set of tiles designed together (offline, stub models)."""

import json

import pytest

from agents.a16_post_designer.agent import run_grid
from agents.a16_post_designer.schema import GridBrief, GridDesign, Photo

LAYOUT_CYCLE = ["cover", "split", "icon_row", "photo_full", "process_steps",
                "text_card", "stat", "split", "cta"]


def _tiles(n=9, photos=None):
    tiles = []
    for i in range(1, n + 1):
        layout = LAYOUT_CYCLE[(i - 1) % len(LAYOUT_CYCLE)]
        t = {
            "position": i, "role": ["who", "what", "why"][(i - 1) // 3 % 3], "layout": layout,
            "headline_ar": f"عنوان {i}", "headline_en": f"HEADLINE {i}",
            "accent_ar": "عنوان", "accent_en": "HEADLINE",
            "body_ar": "نص", "body_en": "text", "photo_ref": None,
            "photo_needs": "site photo, wide, morning light" if layout in ("split", "photo_full") else "",
            "caption_ar": "كابشن", "hashtags": ["#الكويت"],
        }
        if photos and layout in ("split", "photo_full") and photos:
            t["photo_ref"] = photos.pop(0)
            t["photo_needs"] = ""
        tiles.append(t)
    return tiles


def _design(**over):
    data = {"system": {"paper": "#F4EFE8", "accent": "#FBAD46"}, "tiles": _tiles(),
            "questions": ["which projects may we name?"]}
    data.update(over)
    return lambda s, u: json.dumps(data, ensure_ascii=False)


def _brief(**over):
    base = dict(account="@upc.kw", services=["villas", "black structure"],
                facts=["15-year structure warranty"])
    base.update(over)
    return GridBrief(**base)


# ---- happy path ---------------------------------------------------------------
def test_designs_nine_tiles_with_questions():
    out = run_grid(_brief(), model=_design())
    assert len(out.tiles) == 9
    assert out.tiles[0].layout == "cover" and out.tiles[-1].layout == "cta"
    assert out.questions == ["which projects may we name?"]


def test_brief_reaches_the_model_as_json():
    seen = {}

    def model(system, user):
        seen["user"] = user
        return _design()(system, user)

    run_grid(_brief(owner_notes="light theme, no dark panels"), model=model)
    assert "@upc.kw" in seen["user"] and "no dark panels" in seen["user"]
    assert "15-year structure warranty" in seen["user"]


def test_photos_assigned_from_inventory_without_repeats():
    photos = [Photo("qortuba_facade.jpg", "finished villa façade"), Photo("pour_day.jpg", "slab pour")]
    tiles = _tiles(photos=["qortuba_facade.jpg", "pour_day.jpg"])
    out = run_grid(_brief(photos=photos), model=_design(tiles=tiles))
    used = [t.photo_ref for t in out.tiles if t.photo_ref]
    assert used == ["qortuba_facade.jpg", "pour_day.jpg"]


# ---- validation ---------------------------------------------------------------
def test_duplicate_photo_rejected():
    tiles = _tiles()
    tiles[1]["photo_ref"] = tiles[3]["photo_ref"] = "same.jpg"
    with pytest.raises(ValueError, match="reuses photo"):
        run_grid(_brief(photos=[Photo("same.jpg")]), model=_design(tiles=tiles))


def test_photo_outside_inventory_rejected():
    tiles = _tiles()
    tiles[1]["photo_ref"] = "not_given.jpg"
    with pytest.raises(ValueError, match="not in the inventory"):
        run_grid(_brief(photos=[Photo("a.jpg")]), model=_design(tiles=tiles))


def test_empty_inventory_allows_any_ref_but_photo_layouts_need_needs():
    tiles = _tiles()
    tiles[1]["photo_ref"] = None
    tiles[1]["photo_needs"] = ""
    with pytest.raises(ValueError, match="needs photo_ref or photo_needs"):
        run_grid(_brief(), model=_design(tiles=tiles))


def test_wrong_tile_count_rejected():
    with pytest.raises(ValueError, match="exactly 9 tiles"):
        run_grid(_brief(), model=_design(tiles=_tiles(6)))


def test_positions_must_be_contiguous():
    tiles = _tiles()
    tiles[4]["position"] = 11
    with pytest.raises(ValueError, match="positions must be 1..n"):
        run_grid(_brief(), model=_design(tiles=tiles))


def test_bilingual_headlines_required():
    tiles = _tiles()
    tiles[2]["headline_en"] = ""
    with pytest.raises(ValueError, match="headline_en required"):
        run_grid(_brief(), model=_design(tiles=tiles))


def test_arabic_only_grid_does_not_need_english():
    tiles = _tiles()
    for t in tiles:
        t["headline_en"] = ""
    out = run_grid(_brief(languages=["ar"]), model=_design(tiles=tiles))
    assert len(out.tiles) == 9


def test_unknown_layout_rejected():
    tiles = _tiles()
    tiles[0]["layout"] = "carousel3d"
    with pytest.raises(ValueError, match="not renderable"):
        run_grid(_brief(), model=_design(tiles=tiles))


def test_price_on_a_tile_rejected():
    tiles = _tiles()
    tiles[5]["body_ar"] = "ابدأ من 45,000 د.ك"
    with pytest.raises(ValueError, match="no prices"):
        run_grid(_brief(), model=_design(tiles=tiles))


def test_brief_validation():
    with pytest.raises(ValueError, match="multiple of 3"):
        GridBrief(account="x", tiles=8).validate()
    with pytest.raises(ValueError, match="theme"):
        GridBrief(account="x", theme="neon").validate()
    with pytest.raises(ValueError, match="duplicate refs"):
        GridBrief(account="x", photos=[Photo("a"), Photo("a")]).validate()


def test_design_round_trips():
    out = run_grid(_brief(), model=_design())
    from dataclasses import asdict
    again = GridDesign.from_dict(json.loads(json.dumps(asdict(out), ensure_ascii=False)), expected_tiles=9)
    assert again == out
