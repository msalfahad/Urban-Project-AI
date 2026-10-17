"""E51 — a boundary interval has SEVERAL lengths, and they are not the same.

The previous round said:

    "material_length_mm is the only length a quantity engine may read"

That is right for actual material present and wrong for professional QS
practice. Project 23010's own manual benchmark measures GROSS wall perimeter
and applies opening deductions LATER, so a doorway belongs to the gross
host-wall line even though no wall material stands in it.

A DOORWAY IS FOUR FACTS AT ONCE:

    zero actual wall material
    a real opening
    a valid space-closure boundary
    part of the gross host-wall measurement line

Collapsing them into one number makes at least three trades wrong. So an
interval carries a set of named LENGTH BASES, every quantity engine declares
which basis it consumes, and asking for the wrong one raises rather than
silently returning a plausible number.

    NEVER COMPARE UNLIKE BASES. The 102.70 m site benchmark is a GROSS
    perimeter; comparing it against a length that already removed doors is
    comparing two different measurements that happen to share a unit.
"""

from __future__ import annotations

from dataclasses import dataclass

# The length that encloses the physical space: physical wall plus supported
# portal closures. Room polygon, floor area, room perimeter.
SPACE_BOUNDARY_LENGTH = "SPACE_BOUNDARY_LENGTH"

# The gross wall reference line, running THROUGH a wall-hosted opening because
# the host wall continues conceptually across it. Gross plaster, gross ceramic,
# gross blockwork — every trade whose approved rule is gross first, deduct
# later.
HOST_WALL_GROSS_LENGTH = "HOST_WALL_GROSS_LENGTH"

# Actual wall material standing on the line. Excludes doors and windows.
MATERIAL_PRESENT_LENGTH = "MATERIAL_PRESENT_LENGTH"

# The width of a supported opening. Deductions, lintels, frames, thresholds.
OPENING_LENGTH = "OPENING_LENGTH"

# Derived from the approved skirting rule. Usually NOT the space boundary and
# NOT automatically the material present length: a doorway removes skirting,
# and fixed joinery may too, depending on the project rule.
SKIRTING_ELIGIBLE_LENGTH = "SKIRTING_ELIGIBLE_LENGTH"

BASES = (SPACE_BOUNDARY_LENGTH, HOST_WALL_GROSS_LENGTH,
         MATERIAL_PRESENT_LENGTH, OPENING_LENGTH, SKIRTING_ELIGIBLE_LENGTH)

# A basis that cannot be established without a rule nobody has signed.
RULE_REQUIRED = "RULE_REQUIRED"


class LengthBasisError(RuntimeError):
    """A quantity asked for a basis that does not apply, or was not declared."""


@dataclass(frozen=True)
class LengthSet:
    """Every length one boundary interval has, by basis.

    `None` means NOT ESTABLISHED — never zero. Zero is a measured result:
    a doorway genuinely has zero material present, and a wall genuinely has
    zero opening. Those are answers. `None` is the absence of one.
    """

    space_boundary_mm: float | None = None
    host_wall_gross_mm: float | None = None
    material_present_mm: float | None = None
    opening_mm: float | None = None
    skirting_eligible_mm: float | None = None
    skirting_basis: str = RULE_REQUIRED

    def of(self, basis: str) -> float | None:
        if basis not in BASES:
            raise LengthBasisError(
                f"unknown length basis {basis!r}. Known: {BASES}. A quantity "
                "whose measurement basis nobody declared cannot be released")
        return {
            SPACE_BOUNDARY_LENGTH: self.space_boundary_mm,
            HOST_WALL_GROSS_LENGTH: self.host_wall_gross_mm,
            MATERIAL_PRESENT_LENGTH: self.material_present_mm,
            OPENING_LENGTH: self.opening_mm,
            SKIRTING_ELIGIBLE_LENGTH: self.skirting_eligible_mm,
        }[basis]

    def require(self, basis: str) -> float:
        """The length for this basis, or a refusal naming what is missing."""
        v = self.of(basis)
        if v is None:
            raise LengthBasisError(
                f"{basis} is not established for this interval. It is NOT "
                "zero — an unestablished basis and a measured zero are "
                "different facts, and a quantity built on the wrong one is "
                "wrong in a way nobody notices")
        return v

    def record(self) -> dict:
        return {"space_boundary_mm": self.space_boundary_mm,
                "host_wall_gross_mm": self.host_wall_gross_mm,
                "material_present_mm": self.material_present_mm,
                "opening_mm": self.opening_mm,
                "skirting_eligible_mm": self.skirting_eligible_mm,
                "skirting_basis": self.skirting_basis}


def total(intervals, basis: str) -> float:
    """Sum one basis across intervals, in metres.

    Intervals for which the basis is not established are EXCLUDED from the sum
    and counted by `coverage()`. Treating them as zero would quietly understate
    the total, which is the failure mode this whole module exists to prevent.
    """
    return sum(i.lengths.of(basis) or 0.0 for i in intervals) / 1000


def coverage(intervals, basis: str) -> dict:
    """How much of this basis is actually established, so a total can be read.

    A total is only as trustworthy as the share of intervals that could
    supply it.
    """
    have = [i for i in intervals if i.lengths.of(basis) is not None]
    return {"basis": basis, "intervals": len(intervals),
            "established": len(have),
            "not_established": len(intervals) - len(have),
            "total_m": round(total(intervals, basis), 3),
            "complete": len(have) == len(intervals)}


# --------------------------------------------------- what each use consumes

# Every deterministic quantity engine declares its basis. One universal
# wall-length field cannot serve every trade: floor area follows the space
# boundary, gross plaster follows the host wall THROUGH the door, and skirting
# follows neither.
USE_BASIS = {
    "GROSS_PERIMETER": SPACE_BOUNDARY_LENGTH,
    "FLOOR_AREA": SPACE_BOUNDARY_LENGTH,
    "GROSS_WALL_AREA": HOST_WALL_GROSS_LENGTH,
    "GROSS_PLASTER": HOST_WALL_GROSS_LENGTH,
    "NET_PLASTER": HOST_WALL_GROSS_LENGTH,        # minus approved deductions
    "GROSS_CERAMIC_WALL": HOST_WALL_GROSS_LENGTH,
    "NET_CERAMIC_WALL": HOST_WALL_GROSS_LENGTH,   # minus approved deductions
    "PAINT": HOST_WALL_GROSS_LENGTH,
    "BLOCKWORK": HOST_WALL_GROSS_LENGTH,          # gross, then deductions
    "EXTERNAL_FINISH": HOST_WALL_GROSS_LENGTH,
    "WATERPROOFING_VERTICAL": HOST_WALL_GROSS_LENGTH,
    "WATERPROOFING_HORIZONTAL": SPACE_BOUNDARY_LENGTH,
    "CEILING": SPACE_BOUNDARY_LENGTH,
    "SKIRTING": SKIRTING_ELIGIBLE_LENGTH,
    "PHYSICAL_WALL_MATERIAL": MATERIAL_PRESENT_LENGTH,
}

# Which uses subtract openings from their gross basis, and therefore need the
# opening length established before they can be net.
NET_USES = ("NET_PLASTER", "NET_CERAMIC_WALL", "PAINT", "SKIRTING",
            "BLOCKWORK")


def basis_for(use: str) -> str:
    if use not in USE_BASIS:
        raise LengthBasisError(
            f"{use!r} has not declared a measurement basis. Every quantity "
            "engine must say which length it consumes before it may release "
            "a number")
    return USE_BASIS[use]


def deducts_openings(use: str) -> bool:
    return use in NET_USES
