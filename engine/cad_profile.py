"""What one source's layers and blocks appear to mean, on evidence.

Project 7757 has a layer called `W` carrying 2,430 lines, and it is almost
certainly the wall layer. Writing `if layer == "W": wall` would make the
engine right about this drawing and wrong about the next one — the same
mistake as AR-00's 1.14 pt pen, which was a fact about one plot that nearly
became a production assumption.

So there are two separate things, and this module is the second:

    THE ADAPTER   source-independent. Knows entity types, transforms and
                  coordinates. Knows nothing about any naming convention.
    THE PROFILE   per source. Observes what each layer and block CONTAINS,
                  proposes what it appears to represent, records the
                  evidence, and states the status of that proposal.

A profile is an OBSERVATION RECORD, not a rule set. It may conclude that
`W` strongly represents walls on P7757. It may never conclude that a layer
called `W` represents walls.

HOW A ROLE IS PROPOSED WITHOUT A TUNED THRESHOLD

The wall test is structural, not nominal: a wall drawn in plan is two
roughly parallel faces a consistent distance apart, overlapping along their
length. So for each layer the profile measures how much of its axis-aligned
length PARTICIPATES IN SUCH A PAIR. The bar is a majority — more of the
layer's length is paired than is not — which is an argument rather than a
number chosen by trying values.

The thickness band is likewise structural: a partition thinner than 50 mm
is not built and one thicker than 600 mm is a retaining wall or a shaft
rather than a room divider. Both ends are set from construction, not from
this drawing.

Everything else — doors, fixtures, columns, labels — is reported as an
observation with its evidence and left UNRESOLVED unless the geometry
itself says otherwise. A block named `WC` is a block named `WC`.
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field

PROFILE = "SOURCE_OBSERVATION_PROFILE_V1"

# --- structural constants, from construction rather than from a drawing ---

# A pair of parallel faces closer than this is not a built partition; wider
# than this is a retaining wall, a shaft or a plot boundary rather than a
# room divider. Both ends come from what gets built, not from P7757.
MIN_WALL_THICKNESS_MM = 50.0
MAX_WALL_THICKNESS_MM = 600.0

# Two faces must overlap along their length by at least this to be the two
# sides of one wall rather than two unrelated lines that happen to be
# parallel. Half a metre is shorter than any wall worth measuring.
MIN_FACE_OVERLAP_MM = 500.0

# The bar for proposing a role: more of the layer's length supports it than
# does not. A majority is an argument; 0.63 would be a tuned number.
MAJORITY = 0.5

# Roles a layer may be PROPOSED to play. Every one is a proposal about ONE
# source, carrying its evidence.
ROLE_WALL_LIKE = "WALL_LIKE_PAIRED_FACES"
ROLE_LINEWORK = "LINEWORK_ROLE_UNRESOLVED"
ROLE_ANNOTATION = "ANNOTATION_BEARING"
ROLE_DIMENSIONING = "DIMENSION_BEARING"
ROLE_SYMBOL = "SYMBOL_BEARING"
ROLE_FILL = "FILLED_REGION_BEARING"

# Statuses. A proposal is never a fact.
OBSERVED = "OBSERVED"
PROPOSED = "PROPOSED_FOR_THIS_SOURCE_ONLY"
UNRESOLVED = "ROLE_UNRESOLVED"


@dataclass(frozen=True)
class LayerObservation:
    """What one layer holds, and what that suggests it is for — here."""

    layer: str
    entities: int
    by_kind: dict
    axis_counts: dict
    total_length_mm: float
    paired_length_mm: float
    thicknesses_mm: tuple
    texts: int
    dimensions: int
    instances: int
    proposed_role: str
    status: str
    evidence: tuple

    @property
    def paired_share(self) -> float:
        if not self.total_length_mm:
            return 0.0
        return round(self.paired_length_mm / self.total_length_mm, 4)

    def record(self) -> dict:
        return {
            "source_layer": self.layer,
            "entities": self.entities,
            "entity_types": dict(self.by_kind),
            "segment_axes": dict(self.axis_counts),
            "geometry_characteristics": {
                "axis_aligned_length_m": round(self.total_length_mm / 1000, 2),
                "length_in_parallel_face_pairs_m": round(
                    self.paired_length_mm / 1000, 2),
                "paired_share": self.paired_share,
                "face_separations_mm": list(self.thicknesses_mm[:12]),
                "distinct_separations": len(self.thicknesses_mm),
            },
            "text_evidence": self.texts,
            "dimension_evidence": self.dimensions,
            "block_instances": self.instances,
            "proposed_semantic_role": self.proposed_role,
            "evidence": list(self.evidence),
            "status": self.status,
            "scope": ("an observation about THIS source. It is not a rule "
                      "about layers of this name in any other drawing"),
        }


@dataclass(frozen=True)
class BlockObservation:
    """What one block definition contains and where it was placed."""

    block_name: str
    instances: int
    contains: dict
    texts: tuple
    proposed_role: str
    status: str
    evidence: tuple

    def record(self) -> dict:
        return {
            "block_name": self.block_name,
            "instances_placed": self.instances,
            "definition_contains": dict(self.contains),
            "text_inside_definition": list(self.texts),
            "proposed_semantic_role": self.proposed_role,
            "evidence": list(self.evidence),
            "status": self.status,
            "scope": ("an observation about THIS source. A block named WC "
                      "is a block named WC"),
        }


@dataclass
class Profile:
    source_file: str = ""
    source_hash: str = ""
    layers: list = field(default_factory=list)
    blocks: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def wall_like_layers(self) -> list:
        return [o.layer for o in self.layers
                if o.proposed_role == ROLE_WALL_LIKE]

    def profile_hash(self) -> str:
        rows = sorted(
            f"{o.layer}|{o.proposed_role}|{o.status}|{o.paired_share}"
            for o in self.layers)
        rows += sorted(f"B|{b.block_name}|{b.proposed_role}|{b.instances}"
                       for b in self.blocks)
        return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()[:24]

    def record(self) -> dict:
        return {
            "profile": PROFILE,
            "SOURCE_PROFILE_HASH": self.profile_hash(),
            "source_file": self.source_file,
            "source_sha256_16": self.source_hash,
            "layers": [o.record() for o in self.layers],
            "blocks": [b.record() for b in self.blocks],
            "layers_proposed_wall_like": self.wall_like_layers(),
            "frozen_parameters": frozen_parameters(),
            "notes": dict(self.notes),
            "what_this_is": (
                "an observation record for ONE source. Nothing in it is a "
                "universal rule, and the generic adapter does not read it"),
        }


def frozen_parameters() -> dict:
    return {
        "PROFILE": PROFILE,
        "MIN_WALL_THICKNESS_MM": MIN_WALL_THICKNESS_MM,
        "MAX_WALL_THICKNESS_MM": MAX_WALL_THICKNESS_MM,
        "MIN_FACE_OVERLAP_MM": MIN_FACE_OVERLAP_MM,
        "MAJORITY": MAJORITY,
        "why": {
            "thickness_band": (
                "a partition thinner than 50 mm is not built; thicker than "
                "600 mm is a retaining wall or a shaft, not a room divider. "
                "Set from construction, not from any drawing"),
            "MIN_FACE_OVERLAP_MM": (
                "two faces must run alongside each other to be one wall. "
                "Half a metre is shorter than any wall worth measuring"),
            "MAJORITY": (
                "more of the layer's length is paired than is not. A "
                "majority is an argument; a tuned fraction is not"),
        },
    }


def _pairs(segments) -> tuple:
    """Length participating in parallel face pairs, and the separations."""
    by_axis: dict = defaultdict(list)
    for s in segments:
        if s.axis in ("H", "V"):
            by_axis[s.axis].append(s)

    paired_ids, seps = set(), Counter()
    for axis, segs in by_axis.items():
        # Bucket by the coordinate the face holds constant, so only nearby
        # faces are compared: O(n log n) rather than every pair.
        rows = []
        for s in segs:
            fixed = s.y1 if axis == "H" else s.x1
            lo, hi = sorted((s.x1, s.x2) if axis == "H" else (s.y1, s.y2))
            rows.append((fixed, lo, hi, s))
        rows.sort(key=lambda r: r[0])
        for i, (f1, lo1, hi1, s1) in enumerate(rows):
            for f2, lo2, hi2, s2 in rows[i + 1:]:
                gap = f2 - f1
                if gap > MAX_WALL_THICKNESS_MM:
                    break              # sorted: nothing further is closer
                if gap < MIN_WALL_THICKNESS_MM:
                    continue
                if min(hi1, hi2) - max(lo1, lo2) < MIN_FACE_OVERLAP_MM:
                    continue
                paired_ids.add(s1.object_id)
                paired_ids.add(s2.object_id)
                seps[round(gap, 1)] += 1
    return paired_ids, seps


def build(normalized, *, source_file: str = "", source_hash: str = ""
          ) -> Profile:
    """Observe every layer and block of one source. Decides no universal."""
    prof = Profile(source_file=source_file or normalized.source_file,
                   source_hash=source_hash or normalized.source_hash)

    by_layer: dict = defaultdict(list)
    for p in normalized.primitives:
        by_layer[p.provenance.layer].append(p)
    texts_by_layer = Counter(t.provenance.layer for t in normalized.texts)
    dims_by_layer = Counter(d.provenance.layer for d in normalized.dimensions)
    inst_by_layer = Counter(i.provenance.layer for i in normalized.instances)

    for layer, prims in sorted(by_layer.items()):
        segs = [p for p in prims if p.kind == "SEGMENT"]
        axis_segs = [s for s in segs if s.axis in ("H", "V")]
        total = sum(s.length_mm for s in axis_segs)
        paired_ids, seps = _pairs(axis_segs)
        paired = sum(s.length_mm for s in axis_segs
                     if s.object_id in paired_ids)
        share = (paired / total) if total else 0.0

        ev, role, status = [], ROLE_LINEWORK, UNRESOLVED
        ev.append(f"{len(prims)} entities, {len(axis_segs)} axis-aligned "
                  f"segments totalling {total / 1000:.1f} m")
        if seps:
            common = seps.most_common(4)
            ev.append("parallel face pairs at separations "
                      + ", ".join(f"{s} mm x{n}" for s, n in common))
        if total and share >= MAJORITY:
            role, status = ROLE_WALL_LIKE, PROPOSED
            ev.append(f"{share:.0%} of axis-aligned length runs as one side "
                      f"of a parallel pair {MIN_WALL_THICKNESS_MM:.0f}-"
                      f"{MAX_WALL_THICKNESS_MM:.0f} mm apart — a majority, "
                      "which is the structural signature of a wall drawn as "
                      "two faces")
        elif total:
            ev.append(f"only {share:.0%} of axis-aligned length is paired, "
                      "below a majority, so no wall role is proposed")

        if dims_by_layer.get(layer) and dims_by_layer[layer] >= len(prims) / 4:
            role, status = ROLE_DIMENSIONING, OBSERVED
            ev.append(f"{dims_by_layer[layer]} dimension entities sit on "
                      "this layer, so it carries dimensioning")
        elif texts_by_layer.get(layer) and not axis_segs:
            role, status = ROLE_ANNOTATION, OBSERVED
            ev.append(f"{texts_by_layer[layer]} text observations and no "
                      "axis-aligned linework")
        elif (sum(1 for p in prims if p.kind == "HATCH")
              > len(prims) / 3 and prims):
            role, status = ROLE_FILL, OBSERVED
            ev.append("more than a third of this layer is filled regions")
        elif inst_by_layer.get(layer, 0) > len(prims) and role == ROLE_LINEWORK:
            role, status = ROLE_SYMBOL, OBSERVED
            ev.append(f"{inst_by_layer[layer]} block placements against "
                      f"{len(prims)} primitives — it carries symbols")

        prof.layers.append(LayerObservation(
            layer=layer, entities=len(prims),
            by_kind=dict(Counter(p.kind for p in prims).most_common()),
            axis_counts=dict(Counter(s.axis for s in segs).most_common()),
            total_length_mm=total, paired_length_mm=paired,
            thicknesses_mm=tuple(s for s, _ in seps.most_common()),
            texts=texts_by_layer.get(layer, 0),
            dimensions=dims_by_layer.get(layer, 0),
            instances=inst_by_layer.get(layer, 0),
            proposed_role=role, status=status, evidence=tuple(ev)))

    # Blocks: what the definition holds, and how often it was placed.
    contents: dict = defaultdict(Counter)
    inside_text: dict = defaultdict(list)
    for p in normalized.primitives:
        if p.provenance.block_path:
            contents[p.provenance.block_path[-1]][p.kind] += 1
    for t in normalized.texts:
        if t.provenance.block_path:
            inside_text[t.provenance.block_path[-1]].append(t.value)
    placed = Counter(i.block_name for i in normalized.instances)

    for name in sorted(set(normalized.block_definitions.values())):
        n = placed.get(name, 0)
        holds = dict(contents.get(name, {}))
        words = tuple(inside_text.get(name, ()))
        ev = [f"placed {n} time(s)",
              f"definition holds {holds or 'no geometry this adapter emits'}"]
        role, status = "BLOCK_ROLE_UNRESOLVED", UNRESOLVED
        if words:
            ev.append("carries text: " + ", ".join(repr(w) for w in words[:4]))
            role, status = "LABEL_BEARING_SYMBOL", OBSERVED
        if holds.get("ARC") and holds.get("SEGMENT"):
            ev.append("definition combines an arc with straight linework, "
                      "the shape of a leaf-and-swing door symbol — an "
                      "observation about its geometry, not an identification")
            role, status = "ARC_AND_LINE_SYMBOL", OBSERVED
        prof.blocks.append(BlockObservation(
            block_name=name, instances=n, contains=holds, texts=words,
            proposed_role=role, status=status, evidence=tuple(ev)))

    prof.notes["how_roles_were_proposed"] = (
        "from geometry and from what each layer contains. No layer or block "
        "NAME influenced any proposal, and a name that happens to describe "
        "its contents is a coincidence this module cannot and must not use")
    return prof
