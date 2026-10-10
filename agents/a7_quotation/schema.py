"""Contract for A7 — Quotation & Contract Writer.

A7 writes the Arabic clauses of a quotation (عرض سعر) or a contract (عقد
مقاولة). Every figure on the page — prices, totals, durations, dates, the
payment schedule — is rendered by code from the input, so the output here is
words only, and the validator refuses any clause that carries money.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from engine.documents import Milestone, PriceLine

KINDS = {"quotation", "contract"}

# The scopes the clause library knows. A document is built per scope, so an
# unknown scope means there is nothing to build from — fail early.
SCOPES = {
    "black_structure", "basement_waterproofing", "plumbing", "electrical",
    "finishing", "turnkey", "pool", "fitout",
}

# Money must never appear in the model's prose; the renderer places every
# figure. A currency token in a clause is the one thing that can put a wrong
# price in front of a client.
_CURRENCY = re.compile(
    r"د\.\s?ك"                                          # د.ك
    r"|\b(?:و|ال|وال|ب|بال)?(?:دينار|دنانير|فلس)\w*"     # ديناراً، دنانير، فلساً، بالدينار …
    r"|\bK\.?D\b|\bKWD\b|\bfils\b",
    re.IGNORECASE,
)

# The documents are Urban Projects' alone. A former partner's name leaking out
# of an old template would be signed by the wrong company.
_FOREIGN_BRAND = re.compile(r"أوج|\bAWJ\b", re.IGNORECASE)


@dataclass
class Party:
    name: str
    title: str = ""             # الدكتور | السيد | السيدة | المهندس
    civil_id: str = ""
    phone: str = ""
    address: str = ""


@dataclass
class ProjectFacts:
    name: str
    location: str               # e.g. جنوب خيطان
    scopes: list[str]           # subset of SCOPES, in the order the sections go
    description: str = "فيلا سكن خاص"
    plot: str = ""
    floors: list[str] = field(default_factory=list)   # سرداب, أرضي, ميزانين, أول, ثاني, سطح
    built_area_m2: float | None = None

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("project name required")
        if not self.scopes:
            raise ValueError("at least one scope required")
        unknown = [s for s in self.scopes if s not in SCOPES]
        if unknown:
            raise ValueError(f"unknown scope(s) {unknown}; known: {sorted(SCOPES)}")


@dataclass
class ProgrammeLine:
    """A duration from the schedule engine, worded for the document."""

    scope: str
    duration_days: int
    starts_from: str            # Arabic: تاريخ صب اللبشة المسلحة


@dataclass
class OwnerMaterial:
    """A state-subsidised material the owner supplies — a fact, rendered by code."""

    item: str                   # حديد تسليح كويتي
    quantity: str               # 50 طن  |  9,000 د.ك قيمة


@dataclass
class DocumentInput:
    kind: str
    reference: str
    issued: date
    client: Party
    project: ProjectFacts
    price_lines: list[PriceLine]
    programme: list[ProgrammeLine] = field(default_factory=list)
    owner_materials: list[OwnerMaterial] = field(default_factory=list)
    payment_milestones: list[Milestone] = field(default_factory=list)
    special_requests: list[str] = field(default_factory=list)
    extra_exclusions: list[str] = field(default_factory=list)
    validity_days: int = 14

    def validate(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"kind must be one of {sorted(KINDS)}")
        if not self.reference.strip():
            raise ValueError("reference required")
        if not self.client.name.strip():
            raise ValueError("client name required")
        self.project.validate()
        if not self.price_lines:
            raise ValueError("at least one price line required")
        if self.kind == "contract" and not self.payment_milestones:
            raise ValueError("a contract needs payment milestones")


@dataclass
class Group:
    items: list[str]
    heading_ar: str = ""        # e.g. المواصفات الفنية للمواد


@dataclass
class Section:
    title_ar: str
    groups: list[Group]


@dataclass
class DocumentOutput:
    intro_ar: str
    scope_ar: str               # هيكل أسود + عازل سرداب + صحي
    sections: list[Section]
    exclusions_ar: list[str] = field(default_factory=list)
    owner_obligations_intro_ar: str = ""
    contract_terms_ar: list[str] = field(default_factory=list)   # contract only
    closing_ar: str = ""
    missing: list[str] = field(default_factory=list)

    def _prose(self):
        yield self.intro_ar
        yield self.scope_ar
        yield self.owner_obligations_intro_ar
        yield self.closing_ar
        yield from self.exclusions_ar
        yield from self.contract_terms_ar
        for s in self.sections:
            yield s.title_ar
            for g in s.groups:
                yield g.heading_ar
                yield from g.items

    def validate(self) -> None:
        if not self.intro_ar.strip():
            raise ValueError("intro_ar must not be empty")
        if not self.scope_ar.strip():
            raise ValueError("scope_ar must not be empty")
        if not self.sections:
            raise ValueError("a document needs at least one section")
        for i, s in enumerate(self.sections):
            if not s.title_ar.strip():
                raise ValueError(f"sections[{i}] has no title")
            if not any(item.strip() for g in s.groups for item in g.items):
                raise ValueError(f"sections[{i}] ({s.title_ar}) has no items")
        for text in self._prose():
            if _CURRENCY.search(text):
                raise ValueError(f"money in prose is not the agent's job: {text[:80]!r}")
            if _FOREIGN_BRAND.search(text):
                raise ValueError(f"document must be Urban Projects only: {text[:80]!r}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentOutput":
        sections = [
            Section(
                title_ar=s.get("title_ar", ""),
                groups=[
                    Group(items=[str(i) for i in g.get("items", [])],
                          heading_ar=g.get("heading_ar", ""))
                    for g in s.get("groups", [])
                ],
            )
            for s in data.get("sections", [])
        ]
        out = cls(
            intro_ar=data.get("intro_ar", ""),
            scope_ar=data.get("scope_ar", ""),
            sections=sections,
            exclusions_ar=[str(x) for x in data.get("exclusions_ar", [])],
            owner_obligations_intro_ar=data.get("owner_obligations_intro_ar", ""),
            contract_terms_ar=[str(x) for x in data.get("contract_terms_ar", [])],
            closing_ar=data.get("closing_ar", ""),
            missing=[str(x) for x in data.get("missing", [])],
        )
        out.validate()
        return out
