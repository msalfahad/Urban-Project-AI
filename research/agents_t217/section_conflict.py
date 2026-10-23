"""SECTION_CONFLICT_V1 (T-217, unwired, stdlib only): printed vs drawn column / neck sections as CONFLICT records.

Rule proposal R-SECTION-CONFLICT-1 (any villa; provenance: owner directive 2026-10-20 X6 = Q-61 (1), ERS s.2.2 / s.3,
T-205, T-100 / D-16). For one physical member on one storey (a neck, a column), every source that gives its section is
listed with its KIND:

    SCHEDULE   the printed schedule entry for the member's type and storey band (printed)
    TEXT       a size text printed on a plan at that member, e.g. '30X80' (printed)
    DIM        a dimension chain printed on a plan that spans the member on both axes (printed)
    DRAWN      a drawn outline with no printed value (drawing geometry)

Classification (orientation free: a section is the sorted pair; units mm / cm / m normalised to m):

    HELD           no printed source at all (SECTION_NOT_PRINTED); a drawn outline alone is not a section; never 0
    AGREE          every source gives the same section
    DRAFTING_NOTE  every PRINTED source agrees, the drawing itself prints that section at the member (a TEXT or a DIM),
                   and only undimensioned DRAWN lines differ: the printed value of the same drawing governs, the line
                   is a drafting slip (evidence: which printed sources, which drawn lines)
    CONFLICT       two printed sources differ (PRINTED_VS_PRINTED), or the only printed source is the schedule and the
                   drawing draws another section without printing one (PRINTED_VS_DRAWN; X6: a schedule / drawing
                   conflict is a CONFLICT plus a designer request, never resolved by picking the printed one)

A CONFLICT carries every candidate section with its sources and the area range [min, max]; it is never collapsed to one
end (not the larger, not the schedule, not the one closer to another estimate). Volumes: per metre of height always;
at a height only when the height is given (an unprinted height stays HELD, never 0 and never a default).
"""
from __future__ import annotations

from dataclasses import dataclass, field

METHOD = "SECTION_CONFLICT_V1"
RULE = "R-SECTION-CONFLICT-1 (proposed)"
PRINTED = ("SCHEDULE", "TEXT", "DIM")
KINDS = PRINTED + ("DRAWN",)
_UNIT = {"m": 1.0, "cm": 0.01, "mm": 0.001}
_EPS = 1e-9


class ConflictUnresolved(ValueError):
    """A single value was asked of a record that is CONFLICT or HELD."""


class PreferenceRefused(ValueError):
    """A shortcut that resolves a conflict by source preference (schedule wins, larger wins, ...) was asked for."""


@dataclass(frozen=True)
class Source:
    kind: str
    W: float
    D: float
    units: str
    ref: str = ""            # sheet / handle (never coordinates)

    def section_m(self):
        if self.kind not in KINDS:
            raise ValueError(f"unknown source kind {self.kind!r}")
        if self.units not in _UNIT:
            raise ValueError(f"unknown units {self.units!r}")
        if self.W is None or self.D is None or self.W <= 0 or self.D <= 0:
            raise ValueError(f"section sides must be positive ({self.ref})")
        f = _UNIT[self.units]
        a, b = sorted((round(self.W * f, 6), round(self.D * f, 6)))
        return (a, b)


@dataclass
class Record:
    member: str
    storey: str
    status: str
    basis: str
    candidates: list = field(default_factory=list)   # [{"section_m": (a, b), "area_m2": x, "sources": [...]}]
    governing: tuple | None = None
    codes: list = field(default_factory=list)
    evidence: list = field(default_factory=list)

    @property
    def range_m2(self):
        if not self.candidates:
            return None
        areas = [c["area_m2"] for c in self.candidates]
        return (min(areas), max(areas))

    def area_m2(self):
        """The one section area; refused unless AGREE or DRAFTING_NOTE."""
        if self.status in ("AGREE", "DRAFTING_NOTE"):
            return round(self.governing[0] * self.governing[1], 6)
        raise ConflictUnresolved(f"{self.member} {self.storey}: {self.status} has no single area")

    def volume_m3(self, height_m=None):
        """(low, high) m3; per metre of height when height_m is None. HELD -> None (never 0)."""
        if self.status == "HELD":
            return None
        h = 1.0 if height_m is None else height_m
        if h <= 0:
            raise ValueError("height must be positive")
        if self.status in ("AGREE", "DRAFTING_NOTE"):
            lo = hi = self.area_m2()        # a drafting slip is evidence, never a volume end
        else:
            lo, hi = self.range_m2
        return (round(lo * h, 6), round(hi * h, 6))

    def as_dict(self):
        return {"member": self.member, "storey": self.storey, "status": self.status, "basis": self.basis,
                "candidates": [{"section_m": list(c["section_m"]), "area_m2": c["area_m2"], "sources": c["sources"]}
                               for c in self.candidates],
                "range_m2": list(self.range_m2) if self.range_m2 else None,
                "governing_m": list(self.governing) if self.governing else None,
                "codes": list(self.codes), "evidence": list(self.evidence), "method": METHOD}


def classify(member: str, storey: str, sources) -> Record:
    srcs = [s if isinstance(s, Source) else Source(**s) for s in sources]
    groups = {}
    for s in srcs:
        groups.setdefault(s.section_m(), []).append(s)
    cands = [{"section_m": k, "area_m2": round(k[0] * k[1], 6),
              "sources": [f"{s.kind}:{s.ref}" for s in v]} for k, v in sorted(groups.items())]
    printed = {s.section_m() for s in srcs if s.kind in PRINTED}
    drawn = {s.section_m() for s in srcs if s.kind == "DRAWN"}
    if not printed:
        return Record(member, storey, "HELD", "SECTION_NOT_PRINTED", cands, None, ["SECTION_NOT_PRINTED"],
                      ["no schedule entry, size text or dimension; a drawn outline alone is not a section"])
    if len(printed) > 1:
        return Record(member, storey, "CONFLICT", "PRINTED_VS_PRINTED", cands, None, ["SECTION_CONFLICT"],
                      [f"printed sections differ: {sorted(printed)}"])
    p = next(iter(printed))
    other = drawn - {p}
    if not other:
        return Record(member, storey, "AGREE", "ALL_SOURCES_AGREE", cands, p, [], [])
    own_print = [s for s in srcs if s.kind in ("TEXT", "DIM") and s.section_m() == p]
    if own_print:
        slips = [f"DRAWN:{s.ref}" for s in srcs if s.kind == "DRAWN" and s.section_m() != p]
        return Record(member, storey, "DRAFTING_NOTE", "DRAWING_PRINTS_THE_SECTION", cands, p, ["DRAFTING_NOTE"],
                      [f"printed at the member by {[f'{s.kind}:{s.ref}' for s in own_print]}; "
                       f"undimensioned lines drawn otherwise: {slips}"])
    return Record(member, storey, "CONFLICT", "PRINTED_VS_DRAWN", cands, None, ["SECTION_CONFLICT"],
                  [f"schedule only prints {p}; the drawing draws {sorted(other)} and prints no size (X6)"])


def resolve(record: Record, prefer: str):
    """Refused by construction: a conflict is never resolved by a source preference (X6, ERS s.3)."""
    raise PreferenceRefused(f"{record.member} {record.storey}: resolution by preference {prefer!r} is refused; "
                            "a CONFLICT stays a range with a designer request")


def matching_band(section_m, bands: dict):
    """Names of the schedule bands of the same type whose section equals a drawn section (evidence only)."""
    out = []
    for name, b in bands.items():
        if b is None:
            continue
        if Source("SCHEDULE", b["W"], b["D"], b.get("units", "cm")).section_m() == tuple(section_m):
            out.append(name)
    return out
