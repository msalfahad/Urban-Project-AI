"""E100 — three recalls, two denominators, and no silent switch between them.

Round 2's report put "27 of 36 topology recall" beside "0 of 17 release
recall" without saying that the denominator had changed underneath. 36 is
every labelled space on the sheet; 17 is the in-scope ones. A reader
comparing 75% with 0% was comparing two different questions about two
different populations.

So every recall is reported twice — ALL and IN_SCOPE — from the same row
set, and the denominators are printed next to the numbers rather than
implied.

§17 is the same discipline applied to precision. Calling 42.9% "topology
precision" implied that the other 36 regions were false-positive rooms.
They are wall cavities, areas outside the building and fixture gaps: things
that were never claimed to be rooms, because CLASSIFICATION COMES AFTER
SEGMENTATION. The count of unclassified regions is reported as a count, not
as a precision penalty.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

ALL = "ALL_LABELLED_SPACES"
IN_SCOPE = "IN_SCOPE_SPACES"


@dataclass
class Matrix:
    spaces: list = field(default_factory=list)
    regions_total: int = 0
    regions_holding_one_label: int = 0
    regions_holding_several_labels: int = 0
    regions_holding_no_label: int = 0
    notes: dict = field(default_factory=dict)

    def _pop(self, in_scope_only: bool) -> list:
        return [s for s in self.spaces
                if (s.get("in_scope") if in_scope_only else True)]

    def _recall(self, key: str, in_scope_only: bool) -> dict:
        pop = self._pop(in_scope_only)
        hits = sum(1 for s in pop if s.get(key))
        return {"found": hits, "of": len(pop),
                "pct": (0.0 if not pop
                        else round(100.0 * hits / len(pop), 1))}

    def record(self) -> dict:
        classified = (self.regions_holding_one_label
                      + self.regions_holding_several_labels)
        return {
            "denominators": {
                ALL: len(self.spaces),
                IN_SCOPE: len(self._pop(True)),
                "why_both": (
                    "every labelled space on the sheet, and the subset the "
                    "job is scoped to. A recall against one is not "
                    "comparable with a recall against the other, so both "
                    "are printed"),
            },
            "TOPOLOGY_RECALL_ALL": self._recall("found_as_one_region", False),
            "TOPOLOGY_RECALL_IN_SCOPE": self._recall("found_as_one_region",
                                                     True),
            "COMPLETE_MEASUREMENT_RECALL_ALL": self._recall(
                "measured_complete", False),
            "COMPLETE_MEASUREMENT_RECALL_IN_SCOPE": self._recall(
                "measured_complete", True),
            "RELEASE_ELIGIBLE_RECALL_ALL": self._recall(
                "release_eligible", False),
            "RELEASE_ELIGIBLE_RECALL_IN_SCOPE": self._recall(
                "release_eligible", True),
            "ROOM_CANDIDATE_PRECISION": {
                "regions_holding_exactly_one_labelled_space":
                    self.regions_holding_one_label,
                "regions_holding_several": self.regions_holding_several_labels,
                "of_regions_that_hold_any_label": classified,
                "pct": (None if not classified else round(
                    100.0 * self.regions_holding_one_label / classified, 1)),
                "basis": ("among the regions that turned out to hold a "
                          "labelled space, how many hold exactly one. This "
                          "is the precision of the ROOM CANDIDATES"),
            },
            "UNCLASSIFIED_REGION_COUNT": {
                "count": self.regions_holding_no_label,
                "of_regions": self.regions_total,
                "what_these_are": (
                    "wall cavities, areas outside the building, fixture "
                    "gaps and other components of the render's free space"),
                "why_not_a_precision_penalty": (
                    "they were never claimed to be rooms. Classification "
                    "comes AFTER segmentation, so an unclassified region "
                    "is unclassified — not a false-positive room"),
            },
            "rows": list(self.spaces),
            "notes": dict(self.notes),
        }


def build(spaces, *, regions_total: int = 0,
          regions_holding_one_label: int = 0,
          regions_holding_several_labels: int = 0,
          regions_holding_no_label: int = 0, notes=None) -> Matrix:
    """`spaces` rows carry space_id, in_scope and the three outcome flags."""
    return Matrix(spaces=list(spaces), regions_total=regions_total,
                  regions_holding_one_label=regions_holding_one_label,
                  regions_holding_several_labels=(
                      regions_holding_several_labels),
                  regions_holding_no_label=regions_holding_no_label,
                  notes=dict(notes or {}))
