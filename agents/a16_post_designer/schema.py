"""Contract for A16 — Post Designer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

INTERACTIVE_KINDS = {"none", "qa", "poll_ab", "poll_abc"}


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
