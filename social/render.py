"""Render A16's grid design to Instagram tiles.

Each tile is an HTML page laid out from the design JSON with the real logo,
the Cairo font and the brand colours, then screenshotted square by Chromium.
The owner's photos are dropped in by file name; a tile whose photo has not
arrived yet renders a dashed placeholder that says what to shoot, so the grid
can be reviewed before a single photo exists.

A contact sheet stitches the tiles three wide, the way the profile shows them,
and `captions.md` lists the copy in **posting order** — reversed, because
Instagram shows the newest post first.
"""

from __future__ import annotations

import base64
import mimetypes
import re
from dataclasses import asdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

from agents.a16_post_designer.schema import GridBrief, GridDesign, Tile
from documents.render import find_chromium, load_company, logo_svg
from social.icons import icon_svg

HERE = Path(__file__).parent
ROOT = HERE.parent
FONT_CAIRO = ROOT / "assets" / "fonts" / "Cairo-Variable.ttf"
SIZE = 1080

DEFAULT_SYSTEM = {"paper": "#F4EFE8", "ink": "#2B2B2B", "accent": "#FBAD46"}
KICKERS = {"who": "WHO WE ARE", "what": "WHAT WE DO", "why": "WHY URBAN"}

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def _colour(system: dict, key: str) -> str:
    value = str(system.get(key, "")).strip()
    return value if _HEX.match(value) else DEFAULT_SYSTEM[key]


def highlight(text: str, accent: str) -> Markup:
    """Wrap the accent word in the headline; everything is escaped first."""
    safe = escape(text)
    word = accent.strip()
    if word and word in text:
        return Markup(str(safe).replace(str(escape(word)), f'<span class="accent">{escape(word)}</span>', 1))
    return safe


def _photo_uri(ref: str | None, photos_dir: Path | None) -> str | None:
    if not ref or photos_dir is None:
        return None
    path = photos_dir / ref
    if not path.is_file():
        return None
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _logo(company: dict, height: int) -> Markup:
    svg = logo_svg(company)
    if not svg:
        return Markup("")
    # Force the logo to a known height; the SVG's own width/height are the PDF page.
    svg = re.sub(r'\swidth="[^"]*"', "", svg, count=1)
    svg = re.sub(r'\sheight="[^"]*"', f' height="{height}"', svg, count=1)
    return Markup(svg)


def _contact_rows(company: dict) -> list[dict]:
    rows = []
    if company.get("instagram"):
        rows.append({"icon": "instagram", "text": company["instagram"]})
    for phone in company.get("phones", [])[:1]:
        rows.append({"icon": "whatsapp", "text": phone})
    if company.get("address_en"):
        rows.append({"icon": "location", "text": company["address_en"]})
    return rows


def tile_context(tile: Tile, design: GridDesign, brief: GridBrief, company: dict,
                 photos_dir: Path | None = None) -> dict:
    system = design.system or {}
    return {
        "size": SIZE,
        "theme": brief.theme,
        "paper": _colour(system, "paper"),
        "ink": _colour(system, "ink"),
        "accent": _colour(system, "accent"),
        "font_cairo": FONT_CAIRO.as_uri(),
        "tile": tile,
        "layout": tile.layout,
        "badge": f"{tile.position:02d}",
        "kicker": KICKERS.get(tile.role, ""),
        "headline_ar": highlight(tile.headline_ar, tile.accent_ar),
        "headline_en": highlight(tile.headline_en, tile.accent_en),
        # A stat tile is sized for a number; a sentence in the same slot overflows.
        "stat_big": len(tile.headline_ar.strip()) <= 8,
        "photo": _photo_uri(tile.photo_ref, photos_dir),
        "logo": _logo(company, 230),
        "logo_small": _logo(company, 110),
        "contact": _contact_rows(company),
        "icon": icon_svg,
    }


def render_tile_html(tile: Tile, design: GridDesign, brief: GridBrief, company: dict | None = None,
                     photos_dir: Path | None = None) -> str:
    env = Environment(loader=FileSystemLoader(str(HERE)), autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    return env.get_template("tile.html").render(
        **tile_context(tile, design, brief, company or load_company(), photos_dir))


def posting_order(design: GridDesign) -> list[Tile]:
    """Instagram shows the newest post top-left, so post the last tile first."""
    return sorted(design.tiles, key=lambda t: -t.position)


def captions_md(design: GridDesign) -> str:
    lines = ["# Posting order (post #1 in this list first)", ""]
    for i, t in enumerate(posting_order(design), start=1):
        lines += [f"## {i}. Tile {t.position:02d} — {t.headline_en}", ""]
        if t.caption_ar:
            lines += [t.caption_ar, ""]
        if t.caption_en:
            lines += [t.caption_en, ""]
        if t.hashtags:
            lines += [" ".join(t.hashtags), ""]
        if not t.photo_ref and t.photo_needs:
            lines += [f"> photo needed: {t.photo_needs}", ""]
    return "\n".join(lines)


def screenshot_tiles(html_paths: list[Path], chromium: str | None = None) -> list[Path]:
    from playwright.sync_api import sync_playwright

    launch: dict = {}
    exe = chromium or find_chromium()
    if exe:
        launch["executable_path"] = exe
    out: list[Path] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": SIZE, "height": SIZE}, device_scale_factor=1)
        for html_path in html_paths:
            page.goto(html_path.resolve().as_uri())
            page.wait_for_timeout(250)
            png = html_path.with_suffix(".png")
            page.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": SIZE, "height": SIZE})
            out.append(png)
        browser.close()
    return out


def contact_sheet(pngs: list[Path], out_path: Path, columns: int = 3, gap: int = 14,
                  thumb: int = 360) -> Path:
    from PIL import Image

    rows = -(-len(pngs) // columns)
    sheet = Image.new("RGB", (columns * thumb + (columns + 1) * gap, rows * thumb + (rows + 1) * gap), "white")
    for i, png in enumerate(pngs):
        im = Image.open(png).convert("RGB").resize((thumb, thumb))
        r, c = divmod(i, columns)
        sheet.paste(im, (gap + c * (thumb + gap), gap + r * (thumb + gap)))
    sheet.save(out_path)
    return out_path


def render_grid(design: GridDesign, brief: GridBrief, out_dir: Path, photos_dir: Path | None = None,
                company: dict | None = None, png: bool = True) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    company = company or load_company()

    html_paths = []
    for tile in sorted(design.tiles, key=lambda t: t.position):
        path = out_dir / f"tile_{tile.position:02d}.html"
        path.write_text(render_tile_html(tile, design, brief, company, photos_dir), encoding="utf-8")
        html_paths.append(path)

    (out_dir / "captions.md").write_text(captions_md(design), encoding="utf-8")

    result = {"html": html_paths, "png": [], "sheet": None, "captions": out_dir / "captions.md"}
    if png:
        result["png"] = screenshot_tiles(html_paths)
        result["sheet"] = contact_sheet(result["png"], out_dir / "grid_preview.png")
    return result
