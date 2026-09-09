"""Contract for A7 — Quotation Writer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BOQLine:
    description: str
    quantity: float
    unit: str
    rate: float
    line_total: float


@dataclass
class QuotationInput:
    client_name: str
    project: str
    contract_form: str
    boq: list[BOQLine]
    grand_total: float
    currency: str = "KWD"


@dataclass
class QuotationOutput:
    quotation_ar: str
    exclusions: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    draft_contract_ar: str = ""
    missing: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.quotation_ar.strip():
            raise ValueError("quotation_ar must not be empty")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QuotationOutput":
        out = cls(
            quotation_ar=data.get("quotation_ar", ""),
            exclusions=list(data.get("exclusions", [])),
            assumptions=list(data.get("assumptions", [])),
            draft_contract_ar=data.get("draft_contract_ar", ""),
            missing=list(data.get("missing", [])),
        )
        out.validate()
        return out
