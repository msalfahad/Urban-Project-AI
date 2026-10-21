"""Thin outline icons for tiles, as SVG path data on a 24×24 grid.

Kept as code so every tile draws the same icon the same way; an image model
would draw eighteen different cranes.
"""

from __future__ import annotations

from markupsafe import Markup

_PATHS: dict[str, str] = {
    "villa": "M3 11 12 4l9 7M5 10v10h14V10M10 20v-6h4v6",
    "chalet": "M2 12 12 3l10 9M6 11v9h12v-9M9 20v-5h6v5M12 3v3",
    "structure": "M4 21V8h5v13M10 21V4h4v17M15 21V11h5v10M2 21h20",
    "finishing": "M4 4h16v16H4zM4 12h16M12 4v16M8 8h2M14 16h2",
    "waterproofing": "M3 18c3-3 6-3 9 0s6 3 9 0M3 12c3-3 6-3 9 0s6 3 9 0M12 3v3M8 6l4-3 4 3",
    "plumbing": "M4 6h6a4 4 0 0 1 4 4v10M4 4v4M12 20h4M12 17h4M16 9h4v4",
    "plan": "M4 3h12l4 4v14H4zM16 3v4h4M8 12h8M8 16h5M8 8h3",
    "engineering": "M12 3l9 16H3zM12 9v6M9 15h6M12 3v3",
    "crane": "M4 21h16M6 21V7l10-3M6 7h10M16 4v5M16 9l2 2M12 5.5V13M12 13a1.5 1.5 0 1 0 0 3",
    "shield": "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6zM9 12l2 2 4-4",
    "key": "M14 4a5 5 0 1 0 1.5 9.8L20 18v3h-3v-2h-2v-2h-2l-1.6-1.6A5 5 0 0 0 14 4zM14 8h.01",
    "team": "M8 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM16 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM2 20c0-3 3-5 6-5s6 2 6 5M12 20c0-3 2-5 4-5s6 2 6 5",
    "clock": "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2",
    "handshake": "M2 10h4l3 3M22 10h-4l-3 3M7 13l4 4c1 1 2 1 3 0l1-1M11 17l2 2c1 1 2 1 3 0M8 8l4-2 4 2",
    "phone": "M6 3h4l2 5-2.5 1.5a11 11 0 0 0 5 5L16 12l5 2v4a2 2 0 0 1-2 2A17 17 0 0 1 4 5a2 2 0 0 1 2-2z",
    "location": "M12 21s7-6 7-12a7 7 0 0 0-14 0c0 6 7 12 7 12zM12 12a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
    "instagram": "M4 4h16v16H4zM12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM17 7h.01",
    "whatsapp": "M12 3a9 9 0 0 0-7.8 13.5L3 21l4.6-1.2A9 9 0 1 0 12 3zM9 9c0 4 3 6 6 6l1-2-2-1-1 1c-1 0-2-1-2-2l1-1-1-2z",
    "quality": "M12 3l2.5 5 5.5.8-4 3.9.9 5.5-4.9-2.6L7.1 18.2l.9-5.5-4-3.9L9.5 8z",
    "camera": "M4 8h4l2-3h4l2 3h4v11H4zM12 17a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z",
}

ALIASES = {
    "villas": "villa", "chalets": "chalet", "black_structure": "structure",
    "process": "plan", "design": "plan", "warranty": "shield", "handover": "key",
    "delivery": "clock", "trust": "handshake", "call": "phone", "map": "location",
}


def names() -> list[str]:
    return sorted(_PATHS)


def icon_svg(name: str, size: int = 48, stroke: str = "currentColor") -> Markup:
    """An outline icon; an unknown name draws the crane so a tile never breaks."""
    key = ALIASES.get(name, name)
    d = _PATHS.get(key, _PATHS["crane"])
    return Markup(
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{stroke}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="{d}"/></svg>'
    )
