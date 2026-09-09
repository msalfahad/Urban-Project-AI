"""Contract for A10 — Content Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContentInput:
    topic: str
    surface: str = "feed"       # feed | story | reel
    date: str = ""              # ISO date, to check the calendar


@dataclass
class ContentOutput:
    hook: str
    caption_ar: str = ""
    caption_en: str = ""
    hashtags: list[str] = field(default_factory=list)
    story_idea: str = ""
    calendar_note: str = "none"

    def validate(self) -> None:
        if not self.hook.strip():
            raise ValueError("hook must not be empty")
        if not self.caption_ar.strip():
            raise ValueError("caption_ar must not be empty")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContentOutput":
        out = cls(
            hook=data.get("hook", ""),
            caption_ar=data.get("caption_ar", ""),
            caption_en=data.get("caption_en", ""),
            hashtags=list(data.get("hashtags", [])),
            story_idea=data.get("story_idea", ""),
            calendar_note=data.get("calendar_note", "none"),
        )
        out.validate()
        return out
