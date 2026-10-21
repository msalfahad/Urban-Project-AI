"""Contract for A16 — Post Designer.

Two units of work: one post (`PostBrief` -> `PostDesign`) and a whole grid
(`GridBrief` -> `GridDesign`) — a set of tiles designed together so the
profile reads as one page: a launch grid, a campaign block.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

INTERACTIVE_KINDS = {"none", "qa", "poll_ab", "poll_abc"}

# Tile layouts the renderer knows how to draw. A layout the renderer cannot
# draw is a design that never becomes a post.
LAYOUTS = {
    "cover",            # logo, big headline, service icon row
    "photo_full",       # photo fills the tile, text on a paper card
    "split",            # photo one side, text the other
    "text_card",        # text only, on paper
    "icon_row",         # headline + a row of icon+label pairs
    "process_steps",    # numbered steps across the tile
    "stat",             # one big number or fact
    "cta",              # closing tile: how to reach us
}
ROLES = {"who", "what", "why"}
THEMES = {"light", "dark"}

_CURRENCY = re.compile(r"د\.\s?ك|\b(?:و|ال|وال|ب|بال)?(?:دينار|دنانير|فلس)\w*|\bK\.?D\b|\bKWD\b", re.IGNORECASE)


@dataclass
class PostBrief:
    type: str                    # reel | carousel | story | poll
    topic: str
    goal: str = ""
    cta: str = ""
    photo_refs: list[str] = field(default_factory=list)


@dataclass
class PostDesign:
    image_brief: str
    caption_ar: str = ""
    caption_en: str = ""
    hashtags: list[str] = field(default_factory=list)
    interactive: dict = field(default_factory=lambda: {"kind": "none"})
    story_frames: list[str] = field(default_factory=list)
    notes: str = ""

    def validate(self) -> None:
        if not self.image_brief.strip():
            raise ValueError("image_brief must not be empty")
        if not self.caption_ar.strip():
            raise ValueError("caption_ar must not be empty")
        kind = self.interactive.get("kind", "none")
        if kind not in INTERACTIVE_KINDS:
            raise ValueError(f"interactive kind {kind!r} invalid")
        if kind == "poll_abc" and len(self.interactive.get("options", [])) != 3:
            raise ValueError("poll_abc needs exactly 3 options")
        if kind == "poll_ab" and len(self.interactive.get("options", [])) != 2:
            raise ValueError("poll_ab needs exactly 2 options")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PostDesign":
        out = cls(
            image_brief=data.get("image_brief", ""),
            caption_ar=data.get("caption_ar", ""),
            caption_en=data.get("caption_en", ""),
            hashtags=list(data.get("hashtags", [])),
            interactive=data.get("interactive", {"kind": "none"}) or {"kind": "none"},
            story_frames=list(data.get("story_frames", [])),
            notes=data.get("notes", ""),
        )
        out.validate()
        return out


# ---- grid ---------------------------------------------------------------------
@dataclass
class Photo:
    ref: str                     # file name or id the owner will supply
    description: str = ""        # what is in it, so the designer can place it


@dataclass
class GridBrief:
    account: str
    purpose: str = "launch"
    tiles: int = 9
    theme: str = "light"
    languages: list[str] = field(default_factory=lambda: ["ar", "en"])
    narrative: list[str] = field(default_factory=lambda: ["who we are", "what we do", "why trust us"])
    services: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)     # verifiable claims the owner supplies
    photos: list[Photo] = field(default_factory=list)  # inventory; empty means "tell me what to shoot"
    owner_notes: str = ""

    def validate(self) -> None:
        if self.tiles < 1 or self.tiles % 3:
            raise ValueError("an Instagram grid is three tiles wide; tiles must be a multiple of 3")
        if self.theme not in THEMES:
            raise ValueError(f"theme must be one of {sorted(THEMES)}")
        if not self.languages:
            raise ValueError("at least one language required")
        refs = [p.ref for p in self.photos]
        if len(refs) != len(set(refs)):
            raise ValueError("photo inventory has duplicate refs")


@dataclass
class Tile:
    position: int                # 1 = top-left as the profile shows it
    role: str                    # who | what | why
    layout: str
    headline_ar: str
    headline_en: str
    body_ar: str = ""
    body_en: str = ""
    accent_ar: str = ""          # the one word set in brand orange
    accent_en: str = ""
    photo_ref: str | None = None
    photo_needs: str = ""        # what to shoot if no photo is assigned
    photo_side: str = "left"     # split layout: which half the photo takes
    icons: list[dict] = field(default_factory=list)   # {icon, label_ar, label_en}
    steps: list[dict] = field(default_factory=list)   # {n, label_ar, label_en}
    caption_ar: str = ""
    caption_en: str = ""
    hashtags: list[str] = field(default_factory=list)


@dataclass
class GridDesign:
    system: dict                 # palette, type, rules the tiles share
    tiles: list[Tile]
    questions: list[str] = field(default_factory=list)   # what the designer needs from the owner
    notes: str = ""

    def validate(self, expected_tiles: int | None = None, inventory: set[str] | None = None,
                 languages: list[str] | None = None) -> None:
        if not self.tiles:
            raise ValueError("a grid needs tiles")
        if expected_tiles is not None and len(self.tiles) != expected_tiles:
            raise ValueError(f"grid must have exactly {expected_tiles} tiles, got {len(self.tiles)}")

        positions = sorted(t.position for t in self.tiles)
        if positions != list(range(1, len(self.tiles) + 1)):
            raise ValueError("tile positions must be 1..n with no gaps or repeats")

        langs = set(languages or ["ar", "en"])
        used: dict[str, int] = {}
        for t in self.tiles:
            if t.role not in ROLES:
                raise ValueError(f"tile {t.position}: role {t.role!r} invalid")
            if t.layout not in LAYOUTS:
                raise ValueError(f"tile {t.position}: layout {t.layout!r} not renderable")
            if "ar" in langs and not t.headline_ar.strip():
                raise ValueError(f"tile {t.position}: headline_ar required")
            if "en" in langs and not t.headline_en.strip():
                raise ValueError(f"tile {t.position}: headline_en required")
            if t.layout in ("photo_full", "split") and not (t.photo_ref or t.photo_needs.strip()):
                raise ValueError(f"tile {t.position}: a photo layout needs photo_ref or photo_needs")
            if t.photo_side not in ("left", "right"):
                raise ValueError(f"tile {t.position}: photo_side must be left or right")
            if t.photo_ref:
                if t.photo_ref in used:
                    raise ValueError(
                        f"tile {t.position} reuses photo {t.photo_ref!r} from tile {used[t.photo_ref]}")
                used[t.photo_ref] = t.position
                if inventory is not None and t.photo_ref not in inventory:
                    raise ValueError(f"tile {t.position}: photo {t.photo_ref!r} is not in the inventory")
            for text in (t.headline_ar, t.headline_en, t.body_ar, t.body_en, t.caption_ar, t.caption_en):
                if _CURRENCY.search(text):
                    raise ValueError(f"tile {t.position}: no prices on posts: {text[:60]!r}")

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, expected_tiles: int | None = None,
                  inventory: set[str] | None = None, languages: list[str] | None = None) -> "GridDesign":
        tiles = [
            Tile(
                position=int(t.get("position", 0)),
                role=t.get("role", ""),
                layout=t.get("layout", ""),
                headline_ar=t.get("headline_ar", ""),
                headline_en=t.get("headline_en", ""),
                body_ar=t.get("body_ar", ""),
                body_en=t.get("body_en", ""),
                accent_ar=t.get("accent_ar", ""),
                accent_en=t.get("accent_en", ""),
                photo_ref=t.get("photo_ref") or None,
                photo_needs=t.get("photo_needs", ""),
                photo_side=t.get("photo_side") or "left",
                icons=list(t.get("icons", [])),
                steps=list(t.get("steps", [])),
                caption_ar=t.get("caption_ar", ""),
                caption_en=t.get("caption_en", ""),
                hashtags=list(t.get("hashtags", [])),
            )
            for t in data.get("tiles", [])
        ]
        out = cls(
            system=dict(data.get("system", {})),
            tiles=tiles,
            questions=[str(q) for q in data.get("questions", [])],
            notes=data.get("notes", ""),
        )
        out.validate(expected_tiles=expected_tiles, inventory=inventory, languages=languages)
        return out
