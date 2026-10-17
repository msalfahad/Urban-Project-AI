"""Contract for A5 — FAQ Agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CATEGORIES = {
    "permits", "timeline", "process", "finishing_options",
    "documents", "payment", "other",
}
CONFIDENCE = {"high", "medium", "low"}


@dataclass
class FAQInput:
    question: str
    language: str = "ar"  # "ar" or "en"


@dataclass
class FAQOutput:
    category: str
    answer_ar: str = ""
    answer_en: str = ""
    needs_human: bool = False
    confidence: str = "medium"

    def validate(self) -> None:
        if self.category not in CATEGORIES:
            raise ValueError(f"category {self.category!r} invalid")
        if self.confidence not in CONFIDENCE:
            raise ValueError(f"confidence {self.confidence!r} invalid")
        if not self.needs_human and not (self.answer_ar.strip() or self.answer_en.strip()):
            raise ValueError("an answer is required unless needs_human is true")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FAQOutput":
        out = cls(
            category=data.get("category", "other"),
            answer_ar=data.get("answer_ar", ""),
            answer_en=data.get("answer_en", ""),
            needs_human=bool(data.get("needs_human", False)),
            confidence=data.get("confidence", "medium"),
        )
        out.validate()
        return out
