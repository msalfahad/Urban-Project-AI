"""E92 — two questions, two scores, never one number.

    CAN IT FIND THE ROOM?     topology recall / precision, splits, merges
    CAN IT MEASURE THE ROOM?  boundary-source coverage, IoU, area delta

Mixing them is how a system reports "78% accurate" while being unable to
produce a single releasable polygon. They are computed here by two separate
functions that share no term, and the record refuses to combine them.

THE ORDER MATTERS. Topology is scored only AFTER the automatic output is
frozen — the hash is taken first and carried into the score, so a metric
cannot be improved by adjusting the thing it measures. The human/golden
regions may score the automatic result and may never build it.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# What happened to each expected space.
FOUND_ONE_TO_ONE = "FOUND_AS_ONE_REGION"
SPLIT = "SPLIT_ACROSS_SEVERAL_REGIONS"
MERGED = "MERGED_WITH_OTHER_SPACES"
MISSING = "NOT_FOUND_IN_ANY_REGION"

# What each automatic region turned out to hold.
REGION_ONE_SPACE = "HOLDS_EXACTLY_ONE_EXPECTED_SPACE"
REGION_MANY_SPACES = "HOLDS_SEVERAL_EXPECTED_SPACES"
REGION_NO_SPACE = "HOLDS_NO_EXPECTED_SPACE"


@dataclass
class TopologyScore:
    """§16. Scored against a frozen automatic result."""

    frozen_hash: str = ""
    expected: tuple = ()
    per_space: dict = field(default_factory=dict)
    per_region: dict = field(default_factory=dict)
    notes: dict = field(default_factory=dict)

    def record(self) -> dict:
        s = Counter(self.per_space.values())
        r = Counter(v["verdict"] for v in self.per_region.values())
        n = len(self.expected) or 1
        found = s.get(FOUND_ONE_TO_ONE, 0)
        regions = len(self.per_region) or 1
        return {
            "SCORED_AGAINST_FROZEN_AUTOMATIC_OUTPUT_HASH": self.frozen_hash,
            "expected_spaces": len(self.expected),
            "automatic_regions": len(self.per_region),
            "REGION_RECALL_PCT": round(100.0 * found / n, 1),
            "REGION_PRECISION_PCT": round(
                100.0 * r.get(REGION_ONE_SPACE, 0) / regions, 1),
            "recall_basis": (
                "expected spaces found as EXACTLY ONE region, over all "
                "expected spaces. A space split in two is not found"),
            "precision_basis": (
                "automatic regions holding exactly one expected space, "
                "over all automatic regions"),
            "split_errors": s.get(SPLIT, 0),
            "merge_errors": s.get(MERGED, 0),
            "missing": s.get(MISSING, 0),
            "over_segmentation": {
                "spaces_split": s.get(SPLIT, 0),
                "what_it_means": ("one physical space came back as several "
                                  "regions. A wall was seen that is not "
                                  "there, or a fitting cut the room"),
            },
            "under_segmentation": {
                "regions_holding_several_spaces": r.get(
                    REGION_MANY_SPACES, 0),
                "spaces_merged": s.get(MERGED, 0),
                "what_it_means": ("several physical spaces came back as one "
                                  "region. A separator was missed, or the "
                                  "opening between them is genuinely open"),
            },
            "regions_holding_no_expected_space": r.get(REGION_NO_SPACE, 0),
            "per_space": dict(self.per_space),
            "per_region": dict(self.per_region),
            "adjacency": self.notes.get("adjacency", {}),
            "this_is_not_measurement_accuracy": (
                "finding a room and measuring it are different questions "
                "with different evidence. No figure here says anything "
                "about millimetres"),
            "notes": {k: v for k, v in self.notes.items()
                      if k != "adjacency"},
        }


def score_topology(topology, *, labels_in_region, expected_spaces,
                   expected_adjacency=None) -> TopologyScore:
    """Score a FROZEN automatic topology against the human/golden spaces.

    `labels_in_region` maps region_id -> the expected space ids whose
    positions fall inside it. That mapping is the only place the human
    answer enters, and it enters AFTER the hash is taken.
    """
    frozen = topology.output_hash
    expected = tuple(sorted(expected_spaces))

    holds: dict = {r.region_id: sorted(labels_in_region.get(r.region_id, ()))
                   for r in topology.regions}
    where: dict = {}
    for rid, ids in holds.items():
        for sid in ids:
            where.setdefault(sid, []).append(rid)

    per_space = {}
    for sid in expected:
        regions = where.get(sid, [])
        if not regions:
            per_space[sid] = MISSING
        elif len(regions) > 1:
            per_space[sid] = SPLIT
        elif len(holds[regions[0]]) > 1:
            per_space[sid] = MERGED
        else:
            per_space[sid] = FOUND_ONE_TO_ONE

    per_region = {}
    for rid, ids in holds.items():
        verdict = (REGION_NO_SPACE if not ids
                   else REGION_ONE_SPACE if len(ids) == 1
                   else REGION_MANY_SPACES)
        per_region[rid] = {"verdict": verdict, "expected_spaces": ids}

    notes: dict = {
        "how_the_human_answer_entered": (
            "only as which expected space positions fall inside which "
            "automatic region, and only after the automatic output hash "
            "was taken. Nothing human was available while the regions "
            "were being built"),
    }
    if expected_adjacency is not None:
        notes["adjacency"] = _score_adjacency(
            topology, holds, expected_adjacency)

    return TopologyScore(frozen_hash=frozen, expected=expected,
                         per_space=per_space, per_region=per_region,
                         notes=notes)


def _score_adjacency(topology, holds: dict, expected_pairs) -> dict:
    """Did the automatic result see the right rooms as neighbours?

    Only pairs whose BOTH spaces were found one-to-one can be scored: if a
    space is merged into a blob, asking whether it is adjacent to its
    neighbour is meaningless — they are the same region.
    """
    single = {rid: ids[0] for rid, ids in holds.items() if len(ids) == 1}
    region_of = {sid: rid for rid, sid in single.items()}
    got = set()
    for a in topology.adjacencies:
        sa, sb = single.get(a.region_a), single.get(a.region_b)
        if sa and sb:
            got.add(tuple(sorted((sa, sb))))

    want = {tuple(sorted(p)) for p in expected_pairs}
    scorable = {p for p in want if p[0] in region_of and p[1] in region_of}
    hit = scorable & got
    spurious = {p for p in got if p not in want}
    return {
        "expected_pairs": len(want),
        "scorable_pairs": len(scorable),
        "unscorable_pairs": len(want) - len(scorable),
        "correct_adjacencies": len(hit),
        "missed_adjacencies": len(scorable - hit),
        "spurious_adjacencies": len(spurious),
        "ADJACENCY_ACCURACY_PCT": (
            None if not scorable
            else round(100.0 * len(hit) / len(scorable), 1)),
        "why_some_pairs_cannot_be_scored": (
            "a pair whose spaces landed in one merged region cannot be "
            "asked about adjacency: they are the same region, so the "
            "question has no answer rather than a wrong one"),
    }


# ------------------------------------------------------ §17 measurement

@dataclass
class MeasurementScore:
    """§17. Nothing here is a topology figure."""

    rows: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def record(self) -> dict:
        comparable = [r for r in self.rows if r.get("iou") is not None]
        return {
            "regions_with_a_measured_candidate": len(self.rows),
            "complete_measured_polygons": sum(
                1 for r in self.rows if r["polygon_closed"]),
            "diagnostic_complete": sum(
                1 for r in self.rows
                if r["measurement_status"].endswith("DIAGNOSTIC")),
            "production_eligible_complete": sum(
                1 for r in self.rows
                if r["measurement_status"].endswith("PRODUCTION_ELIGIBLE")),
            "partial": sum(1 for r in self.rows
                           if r["measurement_status"].endswith("PARTIAL")),
            "boundary_source_coverage_pct": {
                "measured_mean": _mean(
                    [r["measured_pct"] for r in self.rows]),
                "production_eligible_mean": _mean(
                    [r["production_pct"] for r in self.rows]),
                "unresolved_mean": _mean(
                    [r["unresolved_pct"] for r in self.rows]),
            },
            "vector_vs_raster": {
                "comparable_regions": len(comparable),
                "IOU_mean": _mean([r["iou"] for r in comparable]),
                "area_difference_m2_mean": _mean(
                    [abs(r["area_difference_m2"]) for r in comparable
                     if r.get("area_difference_m2") is not None]),
                "what_the_raster_is_here": (
                    "COMPARISON DATA, not released geometry. A difference "
                    "between the vector polygon and the pixel mask does "
                    "not say which is right: the mask is a ragged "
                    "approximation and the polygon is built from drawn "
                    "lines"),
                "perimeter_is_not_compared_to_the_mask": (
                    "a pixel mask's perimeter is a staircase — measured at "
                    "4.7x the equivalent square on this project — so "
                    "comparing perimeters would report the raster's "
                    "raggedness as the engine's error"),
            },
            "rows": list(self.rows),
            "this_is_not_topology_recall": (
                "every figure here is about regions that were already "
                "found. How many rooms the system finds is §16's question"),
            "notes": dict(self.notes),
        }


def score_measurement(pairs) -> MeasurementScore:
    """`pairs` is an iterable of (TopologyRegion, MeasuredSpaceCandidate)."""
    rep = MeasurementScore()
    for region, cand in pairs:
        iou = area_diff = None
        if cand.polygon_closed and cand.area_m2 is not None:
            approx = region.approximate_area_m2
            area_diff = cand.area_m2 - approx
            # Deliberately an AREA ratio, not a polygon intersection with
            # the mask: intersecting a measured polygon with a pixel mask
            # would let the mask's raggedness set the score.
            iou = (round(min(cand.area_m2, approx)
                         / max(cand.area_m2, approx), 4)
                   if max(cand.area_m2, approx) > 0 else None)
        rep.rows.append({
            "region_id": region.region_id,
            "candidate_id": cand.candidate_id,
            "measurement_status": cand.measurement_status,
            "polygon_closed": cand.polygon_closed,
            "measured_pct": cand.measured_pct,
            "production_pct": cand.production_pct,
            "unresolved_pct": cand.unresolved_pct,
            "unresolved_intervals": len(cand.unresolved_intervals),
            "vector_area_m2": (None if cand.area_m2 is None
                               else round(cand.area_m2, 3)),
            "raster_APPROXIMATE_area_m2": round(
                region.approximate_area_m2, 3),
            "area_difference_m2": (None if area_diff is None
                                   else round(area_diff, 3)),
            "iou": iou,
        })
    rep.notes["basis"] = (
        "IoU here is the ratio of the smaller area to the larger, between "
        "the vector polygon and the raster mask's approximate area. It is "
        "an agreement indicator between two different kinds of object, not "
        "an accuracy figure against ground truth")
    return rep


def _mean(values) -> float | None:
    vals = [v for v in values if v is not None]
    return None if not vals else round(sum(vals) / len(vals), 4)
