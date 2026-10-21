"""Contract for A14 — Instagram Analyst."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IGAnalysisInput:
    period: str                 # e.g. "last_30_days"
    posts: list[dict] = field(default_factory=list)     # per-post metrics
    account: dict = field(default_factory=dict)         # account-level metrics


@dataclass
class IGAnalysis:
    period: str
    headline: str
    best_posts: list[dict] = field(default_factory=list)
    worst_posts: list[dict] = field(default_factory=list)
    best_times_to_post: list[str] = field(default_factory=list)
    content_that_works: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    notes: str = ""

    def validate(self) -> None:
        if not self.headline.strip():
            raise ValueError("headline must not be empty")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IGAnalysis":
        out = cls(
            period=data.get("period", ""),
            headline=data.get("headline", ""),
            best_posts=list(data.get("best_posts", [])),
            worst_posts=list(data.get("worst_posts", [])),
            best_times_to_post=list(data.get("best_times_to_post", [])),
            content_that_works=list(data.get("content_that_works", [])),
            recommendations=list(data.get("recommendations", [])),
            notes=data.get("notes", ""),
        )
        out.validate()
        return out
