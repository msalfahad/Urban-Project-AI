"""E38 — Height registry.

A trade height is a project decision, never a number the engine knows. The Test 1
takeoff applied one 3.30 m height to an entire floor and every wall quantity on
that job was wrong by a constant; this module exists so that cannot be expressed.

Eight heights, independently sourced. Plaster runs to 3.20 m on project 23010 and
ceramic to 3.00 m, so a single `roomHeight` field cannot state the truth and is
not offered. Ceiling height and clear height are different questions again.

Every height carries where it came from, and `ASSUMED` is a first-class source
type precisely so that an assumption can be written down and then refused: an
assumed height may be recorded, may be reviewed, may be discussed — and can never
produce a releasable quantity. The alternative, which every estimating system
falls into eventually, is that a plausible number with no provenance becomes
indistinguishable from a measured one.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

# The eight heights, kept apart because they answer different questions.
STRUCTURAL_WALL = "structural_wall_height"
BLOCKWORK = "blockwork_height"
PLASTER = "plaster_height"
PAINT = "paint_height"
CERAMIC = "ceramic_height"
WATERPROOFING = "waterproofing_height"
CLEAR = "clear_height"
CEILING = "ceiling_height"

HEIGHT_NAMES = (STRUCTURAL_WALL, BLOCKWORK, PLASTER, PAINT, CERAMIC,
                WATERPROOFING, CLEAR, CEILING)

# TRUTH DOMAINS. A height is not one fact with several possible sources: a
# design height and a site height are different facts about different things, and
# ranking them on one ladder would let a site measurement silently overwrite the
# design intent. Both are kept, and E30 reports the variance between them.
DESIGN = "DESIGN"
SITE = "SITE"
COMMERCIAL = "COMMERCIAL"
DOMAINS = (DESIGN, SITE, COMMERCIAL)

# Where a height may come from, by domain. Within a domain the order is a
# hierarchy: a weaker source never overrides a stronger one silently. Across
# domains there is no hierarchy at all, because they are not answering the same
# question.
SECTION_DRAWING = "SECTION_DRAWING"
SPECIFICATION = "SPECIFICATION"
APPROVED_PROJECT_RULE = "APPROVED_PROJECT_RULE"
SITE_MEASURED = "SITE_MEASURED"
AS_BUILT_SURVEY = "AS_BUILT_SURVEY"
CONTRACT_BASIS = "CONTRACT_BASIS"
BOQ_BASIS = "BOQ_BASIS"
ASSUMED = "ASSUMED"

DOMAIN_SOURCES = {
    DESIGN: (SECTION_DRAWING, SPECIFICATION, APPROVED_PROJECT_RULE),
    SITE: (SITE_MEASURED, AS_BUILT_SURVEY),
    COMMERCIAL: (CONTRACT_BASIS, BOQ_BASIS),
}
SOURCE_DOMAIN = {s: d for d, ss in DOMAIN_SOURCES.items() for s in ss}

SOURCE_TYPES = tuple(SOURCE_DOMAIN) + (ASSUMED,)
# Rank WITHIN a domain only. Comparing SECTION_DRAWING to SITE_MEASURED is a
# category error, so the rank is scoped and nothing offers a global one.
SOURCE_RANK = {s: i for ss in DOMAIN_SOURCES.values()
               for i, s in enumerate(ss)}

# ASSUMED is deliberately absent. It is a source type so an assumption can be
# recorded honestly; it is not a source that may produce money.
RELEASABLE_SOURCES = frozenset(SOURCE_DOMAIN)

# A project rule is a human decision. A model may propose one; it may not sign
# one, so these fields are required before such a height can be released.
APPROVED = "APPROVED"
PROPOSED = "PROPOSED"
APPROVAL_STATES = (APPROVED, PROPOSED)

VALIDATED = "VALIDATED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
REJECTED = "REJECTED"
VALIDATION_STATES = (VALIDATED, REVIEW_REQUIRED, REJECTED)

# Why a height cannot be used, in a form a router can act on.
HEIGHT_REQUIRED = "HEIGHT_REQUIRED"


class HeightError(RuntimeError):
    """A height was asked for and no defensible one exists."""


@dataclass(frozen=True)
class Height:
    """One named height for one project, with its whole provenance."""

    height_id: str
    name: str
    value_m: Decimal
    source_type: str
    source: str                       # the human-readable citation
    drawing_id: str = ""
    revision: str = ""
    validation_status: str = REVIEW_REQUIRED
    unit: str = "m"
    note: str = ""
    # Only for APPROVED_PROJECT_RULE. A rule nobody signed is a suggestion.
    approved_by: str = ""
    approval_status: str = PROPOSED
    approved_on: str = ""
    rule_version: str = ""

    @property
    def domain(self) -> str:
        """DESIGN, SITE, COMMERCIAL — or none, for an assumption."""
        return SOURCE_DOMAIN.get(self.source_type, "")

    def __post_init__(self) -> None:
        if self.name not in HEIGHT_NAMES:
            raise HeightError(
                f"{self.height_id}: {self.name!r} is not one of the eight named "
                f"heights {HEIGHT_NAMES}. A generic room height is the mistake "
                "this registry exists to prevent.")
        if self.source_type not in SOURCE_TYPES:
            raise HeightError(
                f"{self.height_id}: source_type {self.source_type!r} is not one of "
                f"{SOURCE_TYPES}")
        if self.validation_status not in VALIDATION_STATES:
            raise HeightError(
                f"{self.height_id}: validation_status {self.validation_status!r} "
                f"is not one of {VALIDATION_STATES}")
        if self.unit != "m":
            raise HeightError(
                f"{self.height_id}: heights are stored in metres, not {self.unit!r}")
        if self.value_m <= 0:
            raise HeightError(f"{self.height_id}: non-physical height {self.value_m}")
        if not self.source.strip():
            raise HeightError(
                f"{self.height_id}: a height with no citation is an assumption "
                "wearing a measurement's clothes — say where it came from.")
        if self.source_type in (SECTION_DRAWING,) and not self.drawing_id.strip():
            raise HeightError(
                f"{self.height_id}: source_type {SECTION_DRAWING} must name the "
                "drawing it was read from.")
        if self.source_type == ASSUMED and self.validation_status == VALIDATED:
            raise HeightError(
                f"{self.height_id}: an ASSUMED height cannot be VALIDATED. "
                "Recording the assumption is right; blessing it is not.")
        if self.approval_status not in APPROVAL_STATES:
            raise HeightError(
                f"{self.height_id}: approval_status {self.approval_status!r} is "
                f"not one of {APPROVAL_STATES}")
        if self.source_type == APPROVED_PROJECT_RULE:
            missing = [f for f in ("approved_by", "approved_on", "rule_version")
                       if not getattr(self, f).strip()]
            if missing or self.approval_status != APPROVED:
                raise HeightError(
                    f"{self.height_id}: an {APPROVED_PROJECT_RULE} needs "
                    f"approval_status={APPROVED} plus {missing or 'all of'} "
                    "approved_by, approved_on and rule_version. A model may "
                    "propose a project rule; it may not sign one.")

    @property
    def releasable(self) -> bool:
        """May a quantity built on this height be released without a human?"""
        return (self.source_type in RELEASABLE_SOURCES
                and self.validation_status == VALIDATED
                and (self.source_type != APPROVED_PROJECT_RULE
                     or self.approval_status == APPROVED))

    @property
    def block_reason(self) -> str:
        if self.releasable:
            return ""
        if self.source_type == ASSUMED:
            return (f"{self.height_id} is ASSUMED ({self.value_m} m, {self.source}). "
                    "An assumed height may be recorded and reviewed; it may never "
                    "produce a released quantity.")
        return (f"{self.height_id} is {self.validation_status} — "
                f"{self.value_m} m from {self.source_type}. An engineer validates "
                "it before it can carry a quantity.")

    def provenance(self) -> dict:
        return {
            "height_id": self.height_id, "name": self.name,
            "value_m": str(self.value_m), "unit": self.unit,
            "source_type": self.source_type, "source": self.source,
            "drawing_id": self.drawing_id, "revision": self.revision,
            "validation_status": self.validation_status,
            "domain": self.domain,
            "approved_by": self.approved_by,
            "approval_status": self.approval_status,
            "approved_on": self.approved_on,
            "rule_version": self.rule_version,
            "releasable": self.releasable, "note": self.note,
        }


@dataclass
class HeightRegistry:
    """Every named height for one project, per truth domain.

    Keyed on (domain, name), not name, so a design height and a site
    measurement of the same thing coexist rather than one overwriting the other.
    Production quantities read DESIGN; E30 compares DESIGN against SITE and
    reports the variance. A site tape does not edit the architect's intent.
    """

    project: str
    heights: dict[tuple[str, str], Height]
    version: str = "1.0"
    effective_from: str = ""

    def __post_init__(self) -> None:
        fixed: dict[tuple[str, str], Height] = {}
        for key, h in self.heights.items():
            # Accept a bare name for callers written before domains existed.
            domain, name = key if isinstance(key, tuple) else (h.domain or DESIGN, key)
            if name != h.name:
                raise HeightError(f"{name} is filed under the wrong name ({h.name})")
            if h.domain and h.domain != domain:
                raise HeightError(
                    f"{h.height_id}: filed under {domain} but its source "
                    f"{h.source_type} belongs to {h.domain}. A site measurement "
                    "is not a design height.")
            fixed[(domain, name)] = h
        self.heights = fixed

    def missing(self, domain: str = DESIGN) -> list[str]:
        return [n for n in HEIGHT_NAMES if (domain, n) not in self.heights]

    def get(self, name: str, domain: str = DESIGN) -> Height:
        """The height, or a named refusal. Never 3.0, 3.2 or 3.3."""
        if name not in HEIGHT_NAMES:
            raise HeightError(f"{name!r} is not one of the eight named heights")
        if domain not in DOMAINS:
            raise HeightError(f"{domain!r} is not one of {DOMAINS}")
        if (domain, name) not in self.heights:
            raise HeightError(
                f"{HEIGHT_REQUIRED}: project {self.project} has no {domain} "
                f"{name}. No generic height is substituted — the Test 1 takeoff "
                "applied 3.30 m to a whole floor for exactly this reason.")
        return self.heights[(domain, name)]

    def for_release(self, name: str, domain: str = DESIGN) -> Height:
        """The height, only if a quantity may actually be released on it."""
        h = self.get(name, domain)
        if not h.releasable:
            raise HeightError(h.block_reason)
        return h

    def variance(self, name: str) -> dict:
        """DESIGN vs SITE for one height, with both preserved.

        This is what the domains are for. Neither figure is corrected toward the
        other and neither is discarded.
        """
        out: dict = {"name": name}
        for d in (DESIGN, SITE):
            try:
                out[d.lower()] = str(self.get(name, d).value_m)
            except HeightError:
                out[d.lower()] = None
        if out.get("design") and out.get("site"):
            out["variance_m"] = str(Decimal(out["site"]) - Decimal(out["design"]))
        return out

    def status(self, domain: str = DESIGN) -> dict[str, str]:
        """What every trade would find if it asked right now."""
        out = {}
        for n in HEIGHT_NAMES:
            h = self.heights.get((domain, n))
            if h is None:
                out[n] = HEIGHT_REQUIRED
            else:
                out[n] = "RELEASABLE" if h.releasable else h.validation_status
        return out

    @classmethod
    def from_dict(cls, data: dict) -> "HeightRegistry":
        heights = {}
        for domain, block in data.get("domains", {}).items():
          for name, h in block.items():
            heights[(domain, name)] = Height(
                height_id=h.get("height_id", f"{data['project']}:{domain}:{name}"),
                name=name,
                value_m=Decimal(str(h["value_m"])),
                source_type=h.get("source_type", ASSUMED),
                source=h.get("source", ""),
                drawing_id=h.get("drawing_id", ""),
                revision=h.get("revision", ""),
                validation_status=h.get("validation_status", REVIEW_REQUIRED),
                unit=h.get("unit", "m"),
                note=h.get("note", ""),
                approved_by=h.get("approved_by", ""),
                approval_status=h.get("approval_status", PROPOSED),
                approved_on=h.get("approved_on", ""),
                rule_version=h.get("rule_version", ""),
            )
        return cls(project=data["project"], heights=heights,
                   version=data.get("version", "1.0"),
                   effective_from=data.get("effective_from", ""))

    @classmethod
    def load(cls, path: str | Path) -> "HeightRegistry":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
