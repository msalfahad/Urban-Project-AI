"""E84 — which of the 214.5 m UNRESOLVED strokes would actually matter.

The temptation is to rank the unresolved population by length and work down
the list. A 12 m stroke in the site plan's hatching is worth nothing; a
300 mm stroke sitting in the aperture that merges two bedrooms is worth a
room. LENGTH IS NOT IMPACT, and this module never sorts by it.

Impact here means one thing only: does this stroke lie in a place where a
separation the drawing expects did not happen. That question is already
answered by the leak maps, which name the strokes found at each aperture
and at each frontier. So the ranking is inherited from measured topology,
not invented.

Nothing here recovers, admits or promotes any stroke. An UNRESOLVED stroke
stays UNRESOLVED: this is a work list for a later round, and a stroke's
presence on it is not evidence that it is a wall.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# Why a stroke earned a place, strongest first.
IMPACT_UNLOCKS_A_FROZEN_CONTROL = "SITS_IN_AN_APERTURE_THAT_MERGES_A_FROZEN_CONTROL"
IMPACT_IN_AN_APERTURE = "SITS_IN_AN_APERTURE_BETWEEN_TWO_LABELLED_SPACES"
IMPACT_ON_A_CONTROL_FRONTIER = (
    "LIES_ON_A_FRONTIER_THAT_DID_NOT_SEPARATE_A_FROZEN_CONTROL")
IMPACT_ON_A_FRONTIER = "LIES_ON_A_FRONTIER_THAT_DID_NOT_SEPARATE"
IMPACT_NONE = "NOT_AT_ANY_MEASURED_SEPARATION_FAILURE"

# A frontier hit is weaker than an aperture hit: it says the stroke is near
# the failed separation, not that it is in the hole. But a frontier hit on a
# frozen control still outranks a frontier hit on two ordinary rooms, or the
# list would not be ranked by what it unlocks.
_RANK = {IMPACT_UNLOCKS_A_FROZEN_CONTROL: 0, IMPACT_IN_AN_APERTURE: 1,
         IMPACT_ON_A_CONTROL_FRONTIER: 2, IMPACT_ON_A_FRONTIER: 3,
         IMPACT_NONE: 4}


@dataclass(frozen=True)
class ImpactRow:
    stroke_id: str
    stroke_class: str
    length_mm: float
    impact: str
    leak_ids: tuple[str, ...] = ()
    spaces_separated: tuple[str, ...] = ()
    frozen_controls: tuple[str, ...] = ()
    aperture_width_mm: float | None = None
    why: str = ""

    @property
    def rank(self) -> int:
        return _RANK.get(self.impact, len(_RANK))

    def record(self) -> dict:
        return {
            "stroke_id": self.stroke_id,
            "stroke_class": self.stroke_class,
            "length_m": round(self.length_mm / 1000, 3),
            "impact": self.impact,
            "leak_ids": list(self.leak_ids),
            "spaces_separated": list(self.spaces_separated),
            "frozen_controls_affected": list(self.frozen_controls),
            "widest_aperture_here_mm": (
                None if self.aperture_width_mm is None
                else round(self.aperture_width_mm, 1)),
            "why": self.why,
        }


@dataclass
class Report:
    rows: list = field(default_factory=list)
    population_length_mm: float = 0.0
    notes: dict = field(default_factory=dict)

    def record(self) -> dict:
        ranked = sorted(self.rows, key=lambda r: (
            r.rank, -(r.aperture_width_mm or 0.0), r.stroke_id))
        worth = [r for r in ranked if r.impact != IMPACT_NONE]
        return {
            "population_length_m": round(self.population_length_mm / 1000, 1),
            "strokes_in_population": len(self.rows),
            "strokes_at_a_measured_separation_failure": len(worth),
            "length_at_a_measured_separation_failure_m": round(
                sum(r.length_mm for r in worth) / 1000, 3),
            "by_impact": dict(Counter(r.impact for r in ranked)),
            "length_by_impact_m": {
                k: round(sum(r.length_mm for r in ranked if r.impact == k)
                         / 1000, 3)
                for k in sorted({r.impact for r in ranked})},
            "work_list": [r.record() for r in worth],
            "ranked_by": (
                "whether the stroke sits where a separation the drawing "
                "expects did not happen, strongest first: an aperture that "
                "merges a frozen control, then any aperture between two "
                "labelled spaces, then a frozen control's frontier, then "
                "any frontier. NOT by length"),
            "tiers_with_no_members_here": sorted(
                k for k in _RANK
                if k != IMPACT_NONE
                and not any(r.impact == k for r in ranked)),
            "what_an_empty_aperture_tier_means": (
                "no UNRESOLVED stroke on this sheet lies inside the widest "
                "unwalled stretch of any failed separation. The missing "
                "separators are not sitting there unrecognised as stray "
                "wall-pen marks — where the partition is open, nothing is "
                "drawn at all"),
            "why_not_length": (
                "a long stroke in site hatching is worth nothing and a "
                "300 mm stroke in the aperture between two bedrooms is "
                "worth a room. Ranking the unresolved population by length "
                "would spend the next round on the wrong 200 m"),
            "what_a_place_on_this_list_is_not": (
                "it is NOT evidence that the stroke is a wall. Every stroke "
                "here remains UNRESOLVED, with no thickness, no finish-face "
                "position and no admission to any wall solid. The list says "
                "where to look next, and nothing about what will be found"),
            "scope": (
                "this round resolves none of them. The population is "
                "reported so the next round can be chosen on measured "
                "topology rather than on the size of the number"),
            "notes": dict(self.notes),
        }


def assess(strokes, leaks, *, controls=(), stroke_class: str = "UNRESOLVED"
           ) -> Report:
    """Rank one stroke class by the separation failures it sits in."""
    here = [s for s in strokes
            if getattr(s, "stroke_class", "") == stroke_class]
    rep = Report(population_length_mm=sum(s.length_mm for s in here))
    frozen = set(controls)

    # Which leaks name each stroke, and in what position.
    at_aperture: dict = {}
    at_frontier: dict = {}
    for lk in leaks:
        for sid in getattr(lk, "strokes_at_aperture", ()):
            at_aperture.setdefault(sid, []).append(lk)
        for sid in getattr(lk, "unpaired_strokes_at_frontier", ()):
            at_frontier.setdefault(sid, []).append(lk)

    for s in here:
        sid = s.stroke_id
        ap, fr = at_aperture.get(sid, []), at_frontier.get(sid, [])
        mine = ap or fr
        spaces = tuple(sorted({
            x for lk in mine
            for x in (getattr(lk, "labels_a", ()) or ())
            + (getattr(lk, "labels_b", ()) or ())}))
        hit_controls = tuple(sorted(frozen & set(spaces)))
        widest = max((getattr(lk, "aperture_length_mm", 0.0) for lk in ap),
                     default=None)

        if ap and hit_controls:
            impact = IMPACT_UNLOCKS_A_FROZEN_CONTROL
            why = (f"this stroke lies inside the widest unwalled stretch of "
                   f"a frontier that failed to separate "
                   f"{', '.join(hit_controls)}. If it turns out to be a "
                   "wall, a frozen control stops being merged — and if it "
                   "turns out not to be, that is equally worth knowing")
        elif ap:
            impact = IMPACT_IN_AN_APERTURE
            why = ("this stroke lies inside an aperture between labelled "
                   "spaces that were expected to be separate. It is where "
                   "a missing separator would have to be")
        elif fr and hit_controls:
            impact = IMPACT_ON_A_CONTROL_FRONTIER
            why = (f"this stroke lies along a frontier that failed to "
                   f"separate {', '.join(hit_controls)}, though not inside "
                   "the widest hole. Weaker than an aperture hit, and "
                   "still the strongest signal this sheet offers")
        elif fr:
            impact = IMPACT_ON_A_FRONTIER
            why = ("this stroke lies along a frontier that did not "
                   "separate, but not in the hole itself. It may be part "
                   "of the separator or beside it")
        else:
            impact = IMPACT_NONE
            why = ("no leak map places this stroke at a separation that "
                   "failed. Nothing measured says working on it would "
                   "change the partition")

        rep.rows.append(ImpactRow(
            stroke_id=sid, stroke_class=s.stroke_class,
            length_mm=s.length_mm, impact=impact,
            leak_ids=tuple(sorted(lk.leak_id for lk in mine)),
            spaces_separated=spaces, frozen_controls=hit_controls,
            aperture_width_mm=widest, why=why))

    rep.notes["leaks_examined"] = len(leaks)
    rep.notes["controls_in_scope"] = sorted(frozen)
    return rep
