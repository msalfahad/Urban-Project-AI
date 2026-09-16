"""Which wall does this door belong to — asked locally, or not answered.

"Nearest wall" is the wrong question. On a drawing at 1:100 a door symbol
can be nearer to a wall it has nothing to do with than to the one it
pierces, and on a model space holding twelve drawings the nearest wall can
belong to a different building altogether.

    DO NOT USE GLOBAL NEAREST-WALL MATCHING.
    IF MULTIPLE HOSTS ARE PLAUSIBLE: PORTAL_HOST_AMBIGUOUS, AND NOTHING
    IS RELEASED THROUGH IT.

So a host is established only by CORRESPONDENCE, and every check is named:

    the opening runs along the host's own axis
    its ends coincide with the ends of the host's two runs
    it lies inside the host wall's extent
    the door geometry occupies the interruption rather than sitting beside
      it
    no second opening claims the same door geometry
    host, symbol and opening all belong to ONE drawing region

The last one is §1 made unavoidable. A door forty metres away in a section
drawing cannot host a plan's opening, however near some line of it falls.

AMBIGUITY IS AN ANSWER. It is recorded, it blocks release through that
portal, and it does not decay into a guess.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from engine import cad_openings as openings_mod

MATCHER = "LOCAL_PORTAL_HOST_CORRESPONDENCE_V1"

HOST_ESTABLISHED = "HOST_ESTABLISHED"
HOST_AMBIGUOUS = "PORTAL_HOST_AMBIGUOUS"
HOST_NOT_FOUND = "PORTAL_HOST_NOT_FOUND"
HOST_CROSSES_REGION = "PORTAL_WOULD_CROSS_A_DRAWING_REGION"
HOST_NOT_ROOM_ELIGIBLE = "HOST_IS_NOT_A_ROOM_BOUNDARY"

STATUSES = (HOST_ESTABLISHED, HOST_AMBIGUOUS, HOST_NOT_FOUND,
            HOST_CROSSES_REGION, HOST_NOT_ROOM_ELIGIBLE)

# The correspondence tolerance is the classifier's own — the smallest
# separation this engine calls a wall. No new number is introduced here.
REACH_MM = openings_mod.JAMB_REACH_MM

CHECKS = (
    "COMPATIBLE_WALL_ORIENTATION",
    "ENDS_COINCIDE_WITH_THE_HOST_RUNS",
    "WITHIN_THE_HOST_WALL_EXTENT",
    "GEOMETRY_OCCUPIES_THE_INTERRUPTION",
    "NO_COMPETING_HOST",
    "ONE_DRAWING_REGION",
)


@dataclass(frozen=True)
class Match:
    """One opening and the host it was or was not matched to."""

    opening_id: str
    region_id: str
    host_bands: tuple
    status: str
    checks: dict = field(default_factory=dict)
    competing: tuple = ()
    why: str = ""

    @property
    def is_established(self) -> bool:
        return self.status == HOST_ESTABLISHED

    def record(self) -> dict:
        return {"opening_id": self.opening_id,
                "drawing_region_id": self.region_id,
                "host_wall_bands": list(self.host_bands),
                "host_status": self.status,
                "checks": dict(self.checks),
                "competing_hosts": list(self.competing),
                "why": self.why}


@dataclass
class MatchReport:
    matches: list = field(default_factory=list)
    portals: list = field(default_factory=list)      # openings with a host
    notes: dict = field(default_factory=dict)

    def by_status(self) -> dict:
        return dict(Counter(m.status for m in self.matches).most_common())

    def established(self) -> list:
        return [m for m in self.matches if m.is_established]

    def ambiguous(self) -> list:
        return [m for m in self.matches if m.status == HOST_AMBIGUOUS]

    def status_of(self) -> dict:
        return {m.opening_id: m.status for m in self.matches}

    def counts(self) -> dict:
        return {
            "openings_offered": len(self.matches),
            "hosts_established": len(self.established()),
            "ambiguous_portal_hosts": len(self.ambiguous()),
            "hosts_not_found": sum(1 for m in self.matches
                                   if m.status == HOST_NOT_FOUND),
            "would_cross_a_drawing_region": sum(
                1 for m in self.matches if m.status == HOST_CROSSES_REGION),
            "host_not_room_eligible": sum(
                1 for m in self.matches
                if m.status == HOST_NOT_ROOM_ELIGIBLE),
            "portals_available_to_close_a_boundary": len(self.portals),
            "by_status": self.by_status(),
        }

    def record(self, *, limit: int = 40) -> dict:
        return {
            "matcher": MATCHER,
            "PORTAL_MATCHER_HASH": matcher_hash(),
            "checks_applied": list(CHECKS),
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "matches": [m.record() for m in self.matches[:limit]],
            "never": ("no global nearest-wall search takes place here. A "
                      "host is established by correspondence or it is not "
                      "established at all"),
            "ambiguity_is_an_answer": (
                "PORTAL_HOST_AMBIGUOUS blocks release through that portal "
                "and does not decay into a guess. Only hypotheses that "
                "could close a boundary compete for one: a grade-D gap is "
                "not a rival portal"),
            "notes": dict(self.notes),
        }


def frozen_parameters() -> dict:
    return {"MATCHER": MATCHER, "REACH_MM": REACH_MM,
            "CHECKS": list(CHECKS),
            "why": {
                "REACH_MM": ("the opening classifier's own correspondence "
                             "reach, which is the profile's minimum wall "
                             "thickness. No new tolerance is introduced"),
                "no_global_search": (
                    "every check is between an opening and the wall it "
                    "already interrupts. Nothing searches outwards for a "
                    "wall to attach to")}}


def matcher_hash() -> str:
    parts = [MATCHER, "|".join(CHECKS), "|".join(STATUSES), str(REACH_MM)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _band_index(candidates) -> dict:
    out = {}
    for c in candidates:
        lo, hi = sorted((c.start_mm, c.end_mm))
        out[c.object_id] = (c.axis, c.fixed_mm, lo, hi)
    return out


def match(openings, candidates, *, region=None, region_report=None,
          eligible_bands=None) -> MatchReport:
    """Give every opening a host, an ambiguity, or nothing.

    `openings` and `candidates` must already belong to ONE drawing region.
    The region is still passed so the crossing test can be made rather
    than assumed — an invariant nobody checks is an invariant nobody has.
    """
    rep = MatchReport()
    bands = _band_index(candidates)
    region_id = getattr(region, "region_id", "DR-001")
    eligible = None if eligible_bands is None else set(eligible_bands)

    # Which openings claim which door geometry. A symbol claimed twice is
    # exactly §12's "multiple plausible hosts".
    #
    # ONLY A CANDIDATE PORTAL COMPETES. A hypothesis that closes nothing —
    # a grade-D wall gap — is not a rival for a door: asking "which wall
    # does this portal pierce" presupposes a portal. Letting gaps compete
    # cost a real door its host wherever a gap's end happened to fall on
    # that door's hinge, and the room behind it never closed.
    claimed = defaultdict(list)
    for o in openings:
        if not o.may_close_boundary:
            continue
        for s in o.symbol_ids:
            claimed[s].append(o.opening_id)

    for o in openings:
        checks, why = {}, ""
        competing = sorted({other for s in o.symbol_ids
                            for other in claimed[s]
                            if other != o.opening_id})

        host_rows = [bands[b] for b in o.host_bands if b in bands]
        checks["COMPATIBLE_WALL_ORIENTATION"] = bool(host_rows) and all(
            r[0] == o.axis for r in host_rows)
        checks["ENDS_COINCIDE_WITH_THE_HOST_RUNS"] = any(
            abs(r[3] - o.start_mm) <= REACH_MM or abs(r[2] - o.end_mm)
            <= REACH_MM for r in host_rows)
        checks["WITHIN_THE_HOST_WALL_EXTENT"] = bool(host_rows) and (
            min(r[2] for r in host_rows) <= o.start_mm + REACH_MM
            and max(r[3] for r in host_rows) >= o.end_mm - REACH_MM)
        checks["GEOMETRY_OCCUPIES_THE_INTERRUPTION"] = (
            openings_mod.E_FACE_INTERRUPTION in o.evidence)
        checks["NO_COMPETING_HOST"] = not competing

        same_region = True
        if region is not None:
            same_region = all(region.holds(b) for b in o.host_bands)
            if region_report is not None:
                for s in o.symbol_ids:
                    owner = region_report.of_object(s)
                    if owner is not None and owner.region_id != region_id:
                        same_region = False
        checks["ONE_DRAWING_REGION"] = same_region

        if not host_rows:
            status = HOST_NOT_FOUND
            why = ("no wall band of this region hosts the interruption, so "
                   "there is nothing for a portal to pierce")
        elif not same_region:
            status = HOST_CROSSES_REGION
            why = ("the host or the door geometry belongs to a different "
                   "drawing. §1 forbids the relationship outright")
        elif competing:
            status = HOST_AMBIGUOUS
            n = len(competing) + 1
            why = (f"the same door geometry is claimed by {n} openings. "
                   "Which wall it pierces is not established, and nothing "
                   "is released through it")
        elif eligible is not None and not all(b in eligible
                                              for b in o.host_bands):
            status = HOST_NOT_ROOM_ELIGIBLE
            why = ("the host band may not close a room — a gate in a plot "
                   "wall is not an internal room separator")
        elif not all(checks[k] for k in (
                "COMPATIBLE_WALL_ORIENTATION",
                "WITHIN_THE_HOST_WALL_EXTENT",
                "GEOMETRY_OCCUPIES_THE_INTERRUPTION")):
            status = HOST_NOT_FOUND
            failed = [k for k in CHECKS if not checks.get(k, True)]
            why = ("correspondence failed on " + ", ".join(failed))
        else:
            status = HOST_ESTABLISHED
            why = ("the opening runs along this wall, inside its extent, "
                   "between its own two runs, and no other opening claims "
                   "its geometry")

        rep.matches.append(Match(
            opening_id=o.opening_id, region_id=region_id,
            host_bands=tuple(o.host_bands), status=status,
            checks=checks, competing=tuple(competing), why=why))

    ok = {m.opening_id for m in rep.established()}
    rep.portals = [o for o in openings
                   if o.opening_id in ok and o.may_close_boundary]
    rep.notes["what_a_host_is_for"] = (
        "a portal with no established host may not close a room boundary, "
        "whatever its evidence grade. Grade answers 'is this an opening'; "
        "the host answers 'an opening in WHAT'")
    return rep
