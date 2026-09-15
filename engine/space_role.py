"""E93 — a name is not a wall, and a label is not an identity.

Two separations, both of which this project has already paid for once:

  §13  PHYSICAL_SPACE vs FUNCTIONAL_ZONE. Raster and vision can correctly
       see DINING, SALOON and CIRCULATION inside one larger room. Those are
       three functional zones in ONE physical space, and the thing that
       decides which is the case is a vector BARRIER between them — never
       the fact that somebody wrote three names.

  §14  TOPOLOGY_REGION vs SEMANTIC_IDENTITY. The WSH-01 failure: a shaft
       was named WASHROOM because the label sat next to it and the geometry
       agreed on size. Raster topology may isolate a shaft perfectly and
       vision may still call it a washroom. So a region's ROLE is decided
       on physical evidence — hatch, fixtures, size, enclosure, adjacency —
       and a label is one input among several, with no casting vote.

WSH-01 may not regain WASHROOM without independent support. That is
enforced here, not remembered.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# What a region physically is.
ROLE_ROOM = "OCCUPIABLE_ROOM"
ROLE_SHAFT = "SHAFT_OR_DUCT"
ROLE_VOID = "VOID_OR_OPENING_IN_SLAB"
ROLE_SERVICE = "SERVICE_SPACE"
ROLE_CIRCULATION = "CIRCULATION"
ROLE_OTHER = "OTHER_OR_NOT_A_SPACE"
ROLE_UNRESOLVED = "ROLE_UNRESOLVED"

ROLES = (ROLE_ROOM, ROLE_SHAFT, ROLE_VOID, ROLE_SERVICE, ROLE_CIRCULATION,
         ROLE_OTHER, ROLE_UNRESOLVED)

# Physical evidence for a role. A LABEL IS NOT IN THIS LIST.
EV_HATCHED = "REGION_IS_HATCHED"
EV_NO_DOOR = "NO_PORTAL_CONNECTS_THIS_REGION"
EV_TINY = "TOO_SMALL_TO_OCCUPY"
EV_FIXTURES = "PLUMBING_OR_FIXTURE_SYMBOLS_PRESENT"
EV_ENCLOSED = "FULLY_ENCLOSED_BY_WALL_MATERIAL"
# Recorded as evidence, and deliberately NOT a role decider. Inferring
# CIRCULATION from adjacency count put 47 of AR-00's 63 regions — BED-01
# among them — into circulation, because a bedroom beside a bathroom, a
# corridor and a dressing room connects three regions too. Whether a space
# functions as circulation is a FUNCTIONAL ZONE question (§13), not a
# physical property of the region.
EV_THROUGH = "CONNECTS_THREE_OR_MORE_REGIONS"

# The smallest thing a person can stand in and use. Below this a region is
# a duct, a pipe shaft or a slab void — whatever the label says.
MIN_OCCUPIABLE_M2 = 1.2

# Spaces whose identity was wrong before and may not be re-asserted from a
# label alone. The value is what it may NOT become without independent
# support (a source outside this drawing).
IDENTITY_QUARANTINE = {
    "WSH-01": ("WASHROOM", "a shaft was named WASHROOM because the label "
                           "sat beside it and the size agreed. Size is not "
                           "identity"),
}


@dataclass(frozen=True)
class RoleVerdict:
    region_id: str
    role: str
    evidence: tuple[str, ...] = ()
    label_observations: tuple[str, ...] = ()
    label_influence: str = "NONE"
    quarantined: tuple[str, ...] = ()
    why: str = ""

    def record(self) -> dict:
        return {
            "region_id": self.region_id,
            "physical_role": self.role,
            "physical_evidence": list(self.evidence),
            "labels_observed_here": list(self.label_observations),
            "what_the_label_decided": self.label_influence,
            "identity_quarantine_applied": list(self.quarantined),
            "why": self.why,
        }


def classify_role(region, *, hatched: bool = False,
                  portals: int = 0, connects: int = 0,
                  fixtures: int = 0, labels=(),
                  enclosed: bool = False) -> RoleVerdict:
    """Decide what a region physically IS, on physical evidence.

    `labels` is recorded and reported. It does not choose the role: that is
    the whole point of §14. The one thing a label does is let a human see
    the disagreement.
    """
    area = region.approximate_area_m2
    ev: list[str] = []
    if hatched:
        ev.append(EV_HATCHED)
    if portals == 0:
        ev.append(EV_NO_DOOR)
    if area < MIN_OCCUPIABLE_M2:
        ev.append(EV_TINY)
    if fixtures:
        ev.append(EV_FIXTURES)
    if enclosed:
        ev.append(EV_ENCLOSED)
    if connects >= 3:
        ev.append(EV_THROUGH)

    seen = tuple(sorted({str(x).strip().upper() for x in labels if x}))

    if EV_TINY in ev and EV_NO_DOOR in ev:
        role = ROLE_SHAFT
        why = (f"{area:.2f} m² with no portal connecting it. Nobody can "
               "enter it, so it is a shaft or a duct whatever is written "
               "beside it")
    elif EV_TINY in ev:
        role = ROLE_VOID
        why = (f"{area:.2f} m² is below the smallest space a person can "
               "occupy, so this is a void or a slab opening rather than a "
               "room")
    elif EV_NO_DOOR in ev and EV_ENCLOSED in ev:
        role = ROLE_SHAFT
        why = ("fully enclosed by wall material with no portal. A space "
               "nobody can reach is not an occupiable room")
    elif area >= MIN_OCCUPIABLE_M2 and portals >= 1:
        role = ROLE_ROOM
        why = (f"{area:.2f} m², reachable through {portals} portal "
               "candidate(s). Occupiable as far as the geometry goes")
    else:
        role = ROLE_UNRESOLVED
        why = ("the physical evidence does not settle what this region is. "
               "UNRESOLVED is the honest answer and does not decay into "
               "ROOM")

    quarantined = []
    influence = "NONE"
    if seen:
        influence = ("RECORDED_ONLY. The role above was decided on "
                     "physical evidence; the label is reported so a human "
                     "can see any disagreement")
        for sid, (forbidden, reason) in IDENTITY_QUARANTINE.items():
            if any(forbidden in lbl for lbl in seen):
                quarantined.append(f"{sid}:{forbidden}")
                why += (f". The label {forbidden} is QUARANTINED for {sid}: "
                        f"{reason}. It may not be asserted again without "
                        "support from a source outside this drawing")

    return RoleVerdict(region_id=region.region_id, role=role,
                       evidence=tuple(ev), label_observations=seen,
                       label_influence=influence,
                       quarantined=tuple(quarantined), why=why)


# ------------------------------------------- §13 zones inside one space

@dataclass
class ZoneReport:
    """Which named zones share one physical space."""

    groups: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def record(self) -> dict:
        multi = [g for g in self.groups if len(g["zones"]) > 1]
        return {
            "physical_spaces_examined": len(self.groups),
            "physical_spaces_holding_several_named_zones": len(multi),
            "open_plan_groups": multi,
            "groups": list(self.groups),
            "rule": (
                "several names inside one region are FUNCTIONAL ZONES of "
                "one PHYSICAL SPACE unless vector barrier material "
                "separates them. Room labels do not imply walls"),
            "what_would_change_a_zone_into_a_room": (
                "established wall material between the two names, or a "
                "validated portal implying a wall. Not a second label, and "
                "not a raster boundary"),
            "notes": dict(self.notes),
        }


def zones(regions, *, labels_inside, separated_by_material=None
          ) -> ZoneReport:
    """Group the names in each region into zones of one physical space.

    `separated_by_material(region_id, label_a, label_b)` answers whether
    established material lies between two names. Absent, nothing is
    separated — which is the conservative answer: without evidence of a
    wall, two names in one region are two zones, not two rooms.
    """
    rep = ZoneReport()
    for r in regions:
        names = sorted(labels_inside.get(r.region_id, ()))
        split_pairs = []
        if separated_by_material is not None:
            for i, a in enumerate(names):
                for b in names[i + 1:]:
                    if separated_by_material(r.region_id, a, b):
                        split_pairs.append([a, b])
        rep.groups.append({
            "region_id": r.region_id,
            "zones": names,
            "physical_space_count_implied": 1 + len(split_pairs),
            "pairs_separated_by_established_material": split_pairs,
            "verdict": ("ONE_PHYSICAL_SPACE_SEVERAL_FUNCTIONAL_ZONES"
                        if len(names) > 1 and not split_pairs
                        else "SEPARATE_PHYSICAL_ROOMS" if split_pairs
                        else "ONE_PHYSICAL_SPACE"),
            "why": ("no established material separates these names, so "
                    "they are zones of one space"
                    if len(names) > 1 and not split_pairs else
                    "established material separates at least one pair"
                    if split_pairs else "one name, one space"),
        })
    rep.notes["regions"] = len(rep.groups)
    return rep


def summary(verdicts) -> dict:
    v = list(verdicts)
    return {
        "regions_classified": len(v),
        "by_physical_role": dict(Counter(x.role for x in v)),
        "quarantine_hits": [x.record() for x in v if x.quarantined],
        "roles": list(ROLES),
        "physical_evidence_used": [
            EV_HATCHED, EV_NO_DOOR, EV_TINY, EV_FIXTURES, EV_ENCLOSED,
            EV_THROUGH],
        "why_adjacency_does_not_decide_a_role": (
            "connecting three or more regions is recorded and does not "
            "make a space circulation: a bedroom beside a bathroom, a "
            "corridor and a dressing room connects three too. Function is "
            "a zone question, not a physical property"),
        "a_label_is_not_evidence_of_role": (
            "every role above was decided without reading a name. Labels "
            "are recorded beside the verdict so a human can see "
            "disagreement — which is how the WSH-01 error was found, and "
            "how it stays found"),
        "min_occupiable_m2": MIN_OCCUPIABLE_M2,
    }
