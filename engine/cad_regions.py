"""Find the separate drawings inside one model space, without guessing a gap.

P7757's model space is 808 m wide and holds twelve drawings side by side.
There are no pages to select: which entities belong to the ground-floor plan
is a question about coordinates.

THE THRESHOLD PROBLEM, AND WHY THIS DOES NOT SOLVE IT BY CHOOSING ONE

Clustering geometry needs a distance at which two marks count as "the same
drawing". Pick 5 m and a dimension string detaches from its plan; pick 50 m
and two sheets merge. Picking the value that makes P7757 come out in twelve
pieces would be tuning against the source under test — the exact move this
project has refused all along.

So no distance is chosen. The clustering is run across a whole LADDER of
distances and the result reports where the answer is STABLE: a partition
that survives a wide range of thresholds is a property of the drawing, and
one that appears at a single threshold is a property of the threshold.

    A PLATEAU IS EVIDENCE. A CHOSEN THRESHOLD IS NOT.

The caller gets candidate partitions with their stability, and picks on
evidence — or declines to pick, which is a legitimate answer.

WHAT A CLUSTER IS NOT

It is not a floor, not a plan, and not a sheet. It is a connected group of
marks. Deciding that one cluster is the ground-floor plan needs its text,
its dimension population and its symbols — `label` below gathers that
evidence and states what it does NOT establish.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field

ALGORITHM = "MULTI_SCALE_OCCUPANCY_CLUSTERING_V1"

# The ladder of clustering distances, in millimetres. Geometric, so it
# spans four orders of magnitude in twelve steps: from a tenth of a metre
# (tighter than any drafting gap) to a hundred metres (wider than any single
# architectural sheet at any plotting scale). The LADDER is fixed; no rung
# is privileged, and the data decides which rungs agree.
LADDER_MM = (100.0, 200.0, 400.0, 800.0, 1600.0, 3200.0, 6400.0,
             12800.0, 25600.0, 51200.0, 102400.0)

# A cluster holding less than this share of the drawing's marks is noise
# for the purpose of counting partitions — a stray leader line, a lone
# marker. It is still reported, never deleted.
MINOR_CLUSTER_SHARE = 0.002


@dataclass(frozen=True)
class Cluster:
    """One connected group of marks, at one clustering distance."""

    cluster_id: str
    object_ids: tuple
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width_mm(self) -> float:
        return self.x1 - self.x0

    @property
    def height_mm(self) -> float:
        return self.y1 - self.y0

    @property
    def marks(self) -> int:
        return len(self.object_ids)

    def contains(self, x: float, y: float, *, pad: float = 0.0) -> bool:
        return (self.x0 - pad <= x <= self.x1 + pad
                and self.y0 - pad <= y <= self.y1 + pad)

    def record(self) -> dict:
        return {"cluster_id": self.cluster_id, "marks": self.marks,
                "extent_mm": [round(self.x0, 1), round(self.y0, 1),
                              round(self.x1, 1), round(self.y1, 1)],
                "size_mm": [round(self.width_mm, 1),
                            round(self.height_mm, 1)]}


@dataclass
class Partition:
    """The clustering at one distance on the ladder."""

    distance_mm: float
    clusters: list = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.clusters)

    def major(self, total_marks: int) -> list:
        floor = max(1, int(total_marks * MINOR_CLUSTER_SHARE))
        return [c for c in self.clusters if c.marks >= floor]

    def record(self, total_marks: int) -> dict:
        maj = self.major(total_marks)
        return {"distance_mm": self.distance_mm,
                "clusters": self.count,
                "major_clusters": len(maj),
                "largest_cluster_marks": max(
                    (c.marks for c in self.clusters), default=0)}


@dataclass
class Plateau:
    """A cluster count that survived a run of consecutive distances."""

    major_count: int
    from_mm: float
    to_mm: float
    rungs: int

    @property
    def stability(self) -> float:
        """How many octaves of threshold the answer survived."""
        if self.from_mm <= 0:
            return 0.0
        return round(math.log2(self.to_mm / self.from_mm), 3)

    def record(self) -> dict:
        return {"major_clusters": self.major_count,
                "stable_from_mm": self.from_mm, "stable_to_mm": self.to_mm,
                "rungs_on_the_ladder": self.rungs,
                "octaves_of_stability": self.stability}


def _bboxes(primitives) -> list:
    rows = []
    for p in primitives:
        if p.kind == "SEGMENT":
            x0, x1 = sorted((p.x1, p.x2))
            y0, y1 = sorted((p.y1, p.y2))
        elif p.kind in ("ARC", "CIRCLE"):
            x0, x1 = p.cx - p.radius, p.cx + p.radius
            y0, y1 = p.cy - p.radius, p.cy + p.radius
        else:
            continue          # a hatch carries no extent in this model
        rows.append((p.object_id, x0, y0, x1, y1))
    return rows


def _cluster_at(rows, distance_mm: float) -> list:
    """Connected components of marks whose bboxes share or touch a cell.

    An occupancy grid at cell size `distance_mm`, 8-connected. Linear in the
    number of marks and their cell coverage, which keeps a sweep over the
    whole ladder affordable on a drawing of 10,000 entities.
    """
    if not rows:
        return []
    cell = distance_mm
    owners: dict = defaultdict(list)
    for idx, (_oid, x0, y0, x1, y1) in enumerate(rows):
        i0, i1 = int(math.floor(x0 / cell)), int(math.floor(x1 / cell))
        j0, j1 = int(math.floor(y0 / cell)), int(math.floor(y1 / cell))
        # A very long mark (a title-block rule spanning the sheet) would
        # cover thousands of cells; its ENDS and a coarse walk along it are
        # enough to connect what it touches.
        step_i = max(1, (i1 - i0) // 64 or 1)
        step_j = max(1, (j1 - j0) // 64 or 1)
        for i in list(range(i0, i1 + 1, step_i)) + [i1]:
            for j in list(range(j0, j1 + 1, step_j)) + [j1]:
                owners[(i, j)].append(idx)

    parent = list(range(len(rows)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for (i, j), members in owners.items():
        first = members[0]
        for m in members[1:]:
            union(first, m)
        for di, dj in ((1, 0), (0, 1), (1, 1), (1, -1)):
            nb = owners.get((i + di, j + dj))
            if nb:
                union(first, nb[0])

    groups: dict = defaultdict(list)
    for idx in range(len(rows)):
        groups[find(idx)].append(idx)

    out = []
    for n, (_root, members) in enumerate(
            sorted(groups.items(), key=lambda kv: -len(kv[1])), 1):
        xs0 = min(rows[m][1] for m in members)
        ys0 = min(rows[m][2] for m in members)
        xs1 = max(rows[m][3] for m in members)
        ys1 = max(rows[m][4] for m in members)
        out.append(Cluster(
            cluster_id=f"REG-{int(distance_mm)}-{n:03d}",
            object_ids=tuple(rows[m][0] for m in members),
            x0=xs0, y0=ys0, x1=xs1, y1=ys1))
    return out


def sweep(primitives, *, ladder=LADDER_MM) -> dict:
    """Cluster at every distance on the ladder and find the plateaus."""
    rows = _bboxes(primitives)
    total = len(rows)
    parts = [Partition(d, _cluster_at(rows, d)) for d in ladder]

    counts = [(p.distance_mm, len(p.major(total))) for p in parts]
    plateaus, run = [], []
    for d, n in counts:
        if run and run[-1][1] == n:
            run.append((d, n))
            continue
        if len(run) >= 2:
            plateaus.append(Plateau(run[0][1], run[0][0], run[-1][0],
                                    len(run)))
        run = [(d, n)]
    if len(run) >= 2:
        plateaus.append(Plateau(run[0][1], run[0][0], run[-1][0], len(run)))

    plateaus.sort(key=lambda p: (-p.stability, p.major_count))
    return {"algorithm": ALGORITHM, "total_marks": total,
            "ladder_mm": list(ladder), "partitions": parts,
            "counts": counts, "plateaus": plateaus}


def label(cluster, *, texts=(), dimensions=(), instances=(), primitives=()
          ) -> dict:
    """Gather the evidence that says what one cluster is. Decides nothing.

    A cluster is a group of marks. Whether it is the ground-floor plan is
    settled by its text, its dimension population and its symbols — all of
    which are reported here, with the explicit statement that none of them
    is an identity.
    """
    pad = max(cluster.width_mm, cluster.height_mm) * 0.02
    inside_t = [t for t in texts if cluster.contains(t.x, t.y, pad=pad)]
    inside_d = [d for d in dimensions
                if cluster.contains(d.x1, d.y1, pad=pad)]
    inside_i = [i for i in instances
                if cluster.contains(*i.insertion_mm, pad=pad)]
    ids = set(cluster.object_ids)
    inside_p = [p for p in primitives if p.object_id in ids]

    by_layer = Counter(p.provenance.layer for p in inside_p)
    axes = Counter(p.axis for p in inside_p if p.kind == "SEGMENT")
    # Text that is short and upper-case behaves like a room stamp; text with
    # a scale note behaves like a title. Both are OBSERVATIONS about the
    # string, not conclusions about the cluster.
    shortish = [t.value for t in inside_t if len(t.value) <= 24]
    titleish = [t.value for t in inside_t
                if ":" in t.value or "PLAN" in t.value.upper()
                or "ELEVATION" in t.value.upper()
                or "SECTION" in t.value.upper()]
    return {
        **cluster.record(),
        "marks_by_layer": dict(by_layer.most_common(12)),
        "segment_axes": dict(axes),
        "texts": len(inside_t),
        "text_samples": shortish[:30],
        "title_like_text": titleish[:10],
        "dimensions": len(inside_d),
        "block_instances": len(inside_i),
        "blocks_present": dict(
            Counter(i.block_name for i in inside_i).most_common(20)),
        "what_this_evidence_is_not": (
            "an identity. A cluster with the word PLAN in it is a cluster "
            "with the word PLAN in it. Naming a floor is a decision made on "
            "this evidence and recorded as such, never inferred here"),
    }


def frozen_parameters() -> dict:
    return {
        "ALGORITHM": ALGORITHM,
        "LADDER_MM": list(LADDER_MM),
        "MINOR_CLUSTER_SHARE": MINOR_CLUSTER_SHARE,
        "why": {
            "LADDER_MM": (
                "no clustering distance is chosen. The ladder spans a tenth "
                "of a metre to a hundred metres — tighter than any drafting "
                "gap to wider than any architectural sheet — and the answer "
                "is read from where the partition is STABLE across rungs"),
            "MINOR_CLUSTER_SHARE": (
                "a group holding under 0.2% of the marks does not change "
                "the partition count. It is still reported, never deleted"),
        },
    }


def freeze_hash() -> str:
    parts = [ALGORITHM, ",".join(str(d) for d in LADDER_MM),
             str(MINOR_CLUSTER_SHARE)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
