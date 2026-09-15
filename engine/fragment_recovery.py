"""E81 — one face opposite MANY: recover the wall that is actually drawn.

289.0 m of source stroke is classified FRAGMENTED_MATE: wall-pen runs lying
along an accepted band's own face line, too short or too broken to have
paired. The pairing engine assumed one face meets one face. A draughtsman
does not work that way — a single continuous face is routinely drawn
opposite several collinear fragments, because the opposite side is
interrupted by a door, a return, a column or simply a new polyline.

So a face group may be 1 ↔ N, and where the evidence genuinely supports it,
M ↔ N. What it may never be is a guess.

    WALL TOPOLOGY IS DOWNSTREAM EVIDENCE ONLY.

No group is chosen because it improves room closure. Nothing in this module
can see a room, a label, an area or a raster millimetre. That is deliberate:
a resolver that optimises for closed rooms will close doors, and a resolver
that closes doors is worse than no resolver at all.

The output is INTERVALS, not a verdict on a pair:

    paired_intervals             both sides drawn. Material is established.
    unpaired_intervals           one side only. Reported, never material.
    supported_fragment_gaps      a gap between fragments that something
                                 explains — a portal, a cap, a jamb, a
                                 crossing wall.
    unsupported_fragment_gaps    a gap nothing explains. NOT bridged.

A wall polygon may occupy only the paired intervals.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

GROUP_1_TO_N = "ONE_FACE_TO_MANY_FRAGMENTS"
GROUP_M_TO_N = "MANY_FRAGMENTS_TO_MANY_FRAGMENTS"
GROUP_1_TO_1 = "ONE_TO_ONE"

RECOVERY_VALIDATED = "FRAGMENT_RECOVERY_VALIDATED"
RECOVERY_DIAGNOSTIC = "FRAGMENT_RECOVERY_DIAGNOSTIC_ONLY"
RECOVERY_REJECTED = "FRAGMENT_RECOVERY_REJECTED"

# Why a gap between fragments is explained.
GAP_PORTAL = "A_SUPPORTED_PORTAL_OCCUPIES_THIS_GAP"
GAP_CROSSING_WALL = "A_WALL_ON_THE_OTHER_AXIS_CROSSES_HERE"
GAP_END_CAP = "AN_END_CAP_CLOSES_A_FRAGMENT_AT_THIS_GAP"
GAP_UNEXPLAINED = "NOTHING_EXPLAINS_THIS_GAP"

# Why a group was rejected.
REJECT_AXIS = "FRAGMENTS_ARE_NOT_ON_A_COMPATIBLE_AXIS"
REJECT_COLLINEAR = "FRAGMENTS_ARE_NOT_COLLINEAR_WITHIN_TOLERANCE"
REJECT_SEPARATION = "FACE_SEPARATION_IS_NOT_STABLE_ALONG_THE_RUN"
REJECT_COVERAGE = "TOO_LITTLE_OF_THE_RUN_IS_ACTUALLY_PAIRED"
REJECT_CONFLICT = "A_CONFLICTING_WALL_CANDIDATE_OCCUPIES_THE_SAME_LINE"
REJECT_OPENING = "THE_GROUP_WOULD_BRIDGE_A_SUPPORTED_OPENING"
REJECT_THIN = "SEPARATION_IS_BELOW_THE_MINIMUM_WALL_THICKNESS"

# --- tolerances, all measured or stated ---------------------------------
# Collinearity: fragments on "the same line" may differ by this much. It is
# the measured coordinate-noise floor's decade, not a chosen smoothing.
COLLINEAR_TOLERANCE_MM = 1.0
# The face separation must not wander by more than this along the run. A
# wall has one thickness; a varying gap is two different things.
SEPARATION_STABILITY_MM = 25.0
# At least this share of the continuous face's run must actually be paired,
# or the "wall" is mostly gap.
MIN_PAIRED_COVERAGE = 0.5
# A fragment shorter than this is not a wall face.
MIN_FRAGMENT_MM = 100.0
# A gap shorter than this is the join between two polylines, not an opening.
MIN_GAP_MM = 50.0
MIN_WALL_THICKNESS_MM = 40.0
MAX_WALL_THICKNESS_MM = 600.0
# How far from a gap a cap or crossing wall may be and still explain it.
EXPLANATION_REACH_MM = 100.0


class FragmentRecoveryError(RuntimeError):
    """A recovery was asked to do something it may not do."""


@dataclass(frozen=True)
class Gap:
    start_mm: float
    end_mm: float
    reason: str = GAP_UNEXPLAINED
    evidence_ids: tuple[str, ...] = ()

    @property
    def length_mm(self) -> float:
        return self.end_mm - self.start_mm

    @property
    def is_supported(self) -> bool:
        return self.reason != GAP_UNEXPLAINED

    def record(self) -> dict:
        return {"from_mm": round(self.start_mm, 1),
                "to_mm": round(self.end_mm, 1),
                "length_mm": round(self.length_mm, 1),
                "reason": self.reason, "supported": self.is_supported,
                "evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class FragmentGroup:
    """One recovered wall, as intervals, with everything that decided it."""

    fragment_group_id: str
    axis: str
    side_a_source_ids: tuple[str, ...]
    side_b_source_ids: tuple[str, ...]
    side_a_mm: float
    side_b_mm: float
    group_kind: str = GROUP_1_TO_N
    paired_intervals: tuple = ()
    unpaired_intervals: tuple = ()
    gaps: tuple = ()
    separation_mean_mm: float = 0.0
    separation_spread_mm: float = 0.0
    validation_status: str = RECOVERY_REJECTED
    reject_reason: str = ""
    evidence: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    drawing_id: str = ""
    drawing_revision: str = ""
    provenance: dict = field(default_factory=dict)
    why: str = ""

    @property
    def paired_length_mm(self) -> float:
        return sum(e - s for s, e in self.paired_intervals)

    @property
    def unpaired_length_mm(self) -> float:
        return sum(e - s for s, e in self.unpaired_intervals)

    @property
    def supported_gap_length_mm(self) -> float:
        return sum(g.length_mm for g in self.gaps if g.is_supported)

    @property
    def unsupported_gap_length_mm(self) -> float:
        return sum(g.length_mm for g in self.gaps if not g.is_supported)

    @property
    def is_validated(self) -> bool:
        return self.validation_status == RECOVERY_VALIDATED

    @property
    def thickness_mm(self) -> float:
        return abs(self.side_b_mm - self.side_a_mm)

    def record(self) -> dict:
        return {
            "fragment_group_id": self.fragment_group_id,
            "axis": self.axis,
            "side_a_source_ids": list(self.side_a_source_ids),
            "side_b_source_ids": list(self.side_b_source_ids),
            "group_kind": self.group_kind,
            "side_a_mm": round(self.side_a_mm, 1),
            "side_b_mm": round(self.side_b_mm, 1),
            "thickness_mm": round(self.thickness_mm, 1),
            "separation_mean_mm": round(self.separation_mean_mm, 2),
            "separation_spread_mm": round(self.separation_spread_mm, 2),
            "paired_intervals": [[round(s, 1), round(e, 1)]
                                 for s, e in self.paired_intervals],
            "unpaired_intervals": [[round(s, 1), round(e, 1)]
                                   for s, e in self.unpaired_intervals],
            "paired_interval_length_mm": round(self.paired_length_mm, 1),
            "unpaired_interval_length_mm": round(self.unpaired_length_mm, 1),
            "supported_fragment_gaps": [
                g.record() for g in self.gaps if g.is_supported],
            "unsupported_fragment_gaps": [
                g.record() for g in self.gaps if not g.is_supported],
            "supported_gap_length_mm": round(
                self.supported_gap_length_mm, 1),
            "unsupported_gap_length_mm": round(
                self.unsupported_gap_length_mm, 1),
            "validation_status": self.validation_status,
            "reject_reason": self.reject_reason,
            "evidence": list(self.evidence),
            "conflicts": list(self.conflicts),
            "drawing_id": self.drawing_id,
            "drawing_revision": self.drawing_revision,
            "provenance": dict(self.provenance),
            "why": self.why,
            "material_occupies": (
                "the paired intervals ONLY. An unpaired interval is one "
                "side drawn and the other unknown, and a gap is not "
                "bridged whether or not something explains it"),
        }


# ------------------------------------------------------------- intervals

def _union(spans) -> list:
    out = [(min(a, b), max(a, b)) for a, b in spans if max(a, b) > min(a, b)]
    if not out:
        return []
    out.sort()
    merged = [list(out[0])]
    for s, e in out[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]


def _intersect(a_runs, b_runs) -> list:
    out = []
    for a0, a1 in a_runs:
        for b0, b1 in b_runs:
            s, e = max(a0, b0), min(a1, b1)
            if e > s:
                out.append((s, e))
    return _union(out)


def _subtract(a_runs, b_runs) -> list:
    out = []
    for lo, hi in a_runs:
        cur = lo
        for s, e in _union(b_runs):
            s, e = max(s, lo), min(e, hi)
            # Clamping a b-run that lies wholly outside [lo, hi] leaves an
            # INVERTED range. Using it appended a span reaching all the way
            # to that distant run's start, which silently overlapped a
            # neighbouring interval — a paired stretch was re-emitted as an
            # unpaired one and the interval total stopped adding up.
            if e <= s:
                continue
            if e <= cur:
                continue
            if s > cur:
                out.append((cur, s))
            cur = max(cur, e)
            if cur >= hi:
                break
        if cur < hi:
            out.append((cur, hi))
    return _union(out)


def _measure(runs) -> float:
    return sum(e - s for s, e in runs)


# ---------------------------------------------------------- the resolver

def _explain_gap(lo: float, hi: float, axis: str, at_a: float, at_b: float,
                 *, portals=(), caps=(), crossing=()) -> Gap:
    """Does anything in the DRAWING account for this break in a face?

    Only the drawing may answer. A gap explained by "the rooms would close
    nicely" is not explained.
    """
    span = (lo - EXPLANATION_REACH_MM, hi + EXPLANATION_REACH_MM)

    hits = tuple(sorted(
        p.portal_id for p in portals
        if getattr(p, "axis", "") == axis
        and min(p.start_mm, p.end_mm) < span[1]
        and max(p.start_mm, p.end_mm) > span[0]
        and min(at_a, at_b) - MAX_WALL_THICKNESS_MM
        <= getattr(p, "fixed_mm", 1e12)
        <= max(at_a, at_b) + MAX_WALL_THICKNESS_MM))
    if hits:
        return Gap(lo, hi, GAP_PORTAL, hits)

    cross = tuple(sorted(
        b.wall_band_id for b in crossing
        if b.axis != axis
        and min(b.start_mm, b.end_mm) - EXPLANATION_REACH_MM
        <= min(at_a, at_b)
        and max(b.start_mm, b.end_mm) + EXPLANATION_REACH_MM
        >= max(at_a, at_b)
        and span[0] <= b.centreline_mm <= span[1]))
    if cross:
        return Gap(lo, hi, GAP_CROSSING_WALL, cross)

    cap_ids = tuple(sorted(
        str(getattr(c, "cap_id", "") or getattr(c, "segment_id", ""))
        for c in caps
        if getattr(c, "axis", "") != axis
        and span[0] <= getattr(c, "fixed_mm", 1e12) <= span[1]))
    if cap_ids:
        return Gap(lo, hi, GAP_END_CAP, cap_ids)

    return Gap(lo, hi, GAP_UNEXPLAINED, ())


def _opening_conflict(paired, axis: str, at_a: float, at_b: float,
                      portals) -> tuple:
    """HARD INVARIANT: no recovered interval may cover a supported opening.

    A fragmented-mate resolver that closes doors is worse than no resolver.
    """
    bad = []
    for p in portals:
        if getattr(p, "axis", "") != axis:
            continue
        if not getattr(p, "exists", False):
            continue
        fixed = getattr(p, "fixed_mm", None)
        if fixed is None:
            continue
        if not (min(at_a, at_b) - MAX_WALL_THICKNESS_MM <= fixed
                <= max(at_a, at_b) + MAX_WALL_THICKNESS_MM):
            continue
        p_lo, p_hi = min(p.start_mm, p.end_mm), max(p.start_mm, p.end_mm)
        if _measure(_intersect(paired, [(p_lo, p_hi)])) > MIN_GAP_MM:
            bad.append(p.portal_id)
    return tuple(sorted(bad))


def resolve(faces, *, portals=(), caps=(), bands=(), drawing_id: str = "",
            revision: str = "", used_face_ids=(),
            collinear_tolerance_mm: float = COLLINEAR_TOLERANCE_MM
            ) -> list:
    """Group a continuous face with the collinear fragments opposite it.

    Deterministic: faces are ordered by id, the longest unconsumed face on
    a line seeds a group, and each face joins at most one group. Nothing
    here can see a room.
    """
    used = set(used_face_ids)
    pool = [f for f in faces
            if getattr(f, "segment_id", "") not in used
            and abs(f.end_mm - f.start_mm) >= MIN_FRAGMENT_MM]

    by_axis: dict = {}
    for f in pool:
        by_axis.setdefault(f.axis, []).append(f)

    out, n, consumed = [], 0, set()
    for axis in sorted(by_axis):
        here = sorted(by_axis[axis],
                      key=lambda f: (-abs(f.end_mm - f.start_mm),
                                     getattr(f, "segment_id", "")))
        for seed in here:
            sid = getattr(seed, "segment_id", "")
            if sid in consumed:
                continue
            s_lo = min(seed.start_mm, seed.end_mm)
            s_hi = max(seed.start_mm, seed.end_mm)

            # Candidate mates: anything on a DIFFERENT line, a plausible
            # wall thickness away, whose run overlaps the seed's.
            mates = []
            for g in here:
                gid = getattr(g, "segment_id", "")
                if gid == sid or gid in consumed:
                    continue
                sep = abs(g.fixed_mm - seed.fixed_mm)
                if sep < MIN_WALL_THICKNESS_MM or sep > MAX_WALL_THICKNESS_MM:
                    continue
                g_lo = min(g.start_mm, g.end_mm)
                g_hi = max(g.start_mm, g.end_mm)
                if g_hi <= s_lo or g_lo >= s_hi:
                    continue
                mates.append(g)
            if not mates:
                continue

            # Collinear fragments share a line within tolerance. Group them
            # by their fixed coordinate and take the line with the most
            # overlap — never the one that would close the most room.
            lines = _collinear_clusters(mates, collinear_tolerance_mm)
            best = max(
                lines,
                key=lambda grp: (_measure(_intersect(
                    [(s_lo, s_hi)],
                    [(min(x.start_mm, x.end_mm), max(x.start_mm, x.end_mm))
                     for x in grp])), -len(grp)))
            if len(best) < 2:
                continue        # 1-to-1 is the existing pairing engine's job

            n += 1
            group = _build_group(
                seed, best, axis=axis, gid=f"FG-{n:04d}",
                portals=portals, caps=caps, bands=bands,
                drawing_id=drawing_id, revision=revision)
            out.append(group)
            if group.is_validated:
                consumed.add(sid)
                consumed.update(getattr(g, "segment_id", "") for g in best)
    return out


def _collinear_clusters(faces, tolerance_mm: float) -> list:
    """Fragments that lie on ONE line, by proximity rather than by bucket.

    A fixed-coordinate bucket (round(fixed / tol)) splits at its own
    boundaries: two fragments 0.6 mm apart straddle 200.5 and are declared
    non-collinear, while two 0.9 mm apart inside one bucket are not. Single
    linkage asks the only question the drawing can answer — is the next
    fragment within tolerance of the last one on this line.

    Chaining means a cluster's total spread can exceed the tolerance, which
    is exactly why _judge still measures separation stability across the
    whole run: a chain of drifting fragments is not one wall.
    """
    ordered = sorted(faces, key=lambda f: (f.fixed_mm,
                                           getattr(f, "segment_id", "")))
    out: list = []
    for f in ordered:
        if out and abs(f.fixed_mm - out[-1][-1].fixed_mm) <= tolerance_mm:
            out[-1].append(f)
        else:
            out.append([f])
    return out


def _build_group(seed, mates, *, axis, gid, portals, caps, bands,
                 drawing_id, revision) -> FragmentGroup:
    """Everything the evidence says about one candidate group."""
    s_lo = min(seed.start_mm, seed.end_mm)
    s_hi = max(seed.start_mm, seed.end_mm)
    seed_runs = [(s_lo, s_hi)]
    mate_runs = _union([(min(g.start_mm, g.end_mm), max(g.start_mm, g.end_mm))
                        for g in mates])

    seps = [abs(g.fixed_mm - seed.fixed_mm) for g in mates]
    mean = sum(seps) / len(seps)
    spread = max(seps) - min(seps)
    a_ids = (getattr(seed, "segment_id", ""),)
    b_ids = tuple(sorted(getattr(g, "segment_id", "") for g in mates))

    paired = _intersect(seed_runs, mate_runs)
    unpaired = _subtract(seed_runs, mate_runs)
    # Gaps are the unpaired stretches BETWEEN fragments, not the tails.
    inner_lo = min(lo for lo, _ in mate_runs)
    inner_hi = max(hi for _, hi in mate_runs)
    gaps = [
        _explain_gap(lo, hi, axis, seed.fixed_mm,
                     seed.fixed_mm + (mean if mates[0].fixed_mm
                                      > seed.fixed_mm else -mean),
                     portals=portals, caps=caps, crossing=bands)
        for lo, hi in _subtract([(inner_lo, inner_hi)], mate_runs)
        if hi - lo >= MIN_GAP_MM]

    ev, conflicts = ["FRAGMENTS_ARE_COLLINEAR_WITHIN_TOLERANCE"], []
    if spread <= SEPARATION_STABILITY_MM:
        ev.append("FACE_SEPARATION_IS_STABLE_ALONG_THE_RUN")
    coverage = (_measure(paired) / (s_hi - s_lo)) if s_hi > s_lo else 0.0
    if coverage >= MIN_PAIRED_COVERAGE:
        ev.append(f"{coverage * 100:.0f}_PCT_OF_THE_RUN_IS_PAIRED")
    pens = {getattr(g, "stroke_width_pt", None) for g in mates}
    pens.add(getattr(seed, "stroke_width_pt", None))
    if len(pens) == 1 and None not in pens:
        ev.append("ALL_FRAGMENTS_SHARE_ONE_PEN_WEIGHT")
    if all(g.is_supported for g in gaps) and gaps:
        ev.append("EVERY_GAP_BETWEEN_FRAGMENTS_IS_EXPLAINED")

    bridged = _opening_conflict(paired, axis, seed.fixed_mm,
                                seed.fixed_mm + mean, portals)
    status, reason, why = _judge(
        mean=mean, spread=spread, coverage=coverage, gaps=gaps,
        bridged=bridged, fragments=len(mates))
    if bridged:
        conflicts.extend(f"WOULD_BRIDGE_SUPPORTED_OPENING_{i}"
                         for i in bridged)

    return FragmentGroup(
        fragment_group_id=gid, axis=axis,
        side_a_source_ids=a_ids, side_b_source_ids=b_ids,
        side_a_mm=seed.fixed_mm,
        side_b_mm=(seed.fixed_mm + mean if mates[0].fixed_mm > seed.fixed_mm
                   else seed.fixed_mm - mean),
        group_kind=(GROUP_1_TO_N if len(a_ids) == 1 else GROUP_M_TO_N),
        paired_intervals=tuple(paired), unpaired_intervals=tuple(unpaired),
        gaps=tuple(gaps), separation_mean_mm=mean,
        separation_spread_mm=spread,
        validation_status=status, reject_reason=reason,
        evidence=tuple(ev), conflicts=tuple(conflicts),
        drawing_id=drawing_id, drawing_revision=revision,
        provenance={"seed_face": a_ids[0], "fragments": len(mates),
                    "seed_run_mm": [round(s_lo, 1), round(s_hi, 1)]},
        why=why)


def _judge(*, mean, spread, coverage, gaps, bridged, fragments):
    """The decision. Room topology is not an input to it."""
    if bridged:
        return RECOVERY_REJECTED, REJECT_OPENING, (
            f"this group's paired material would cover supported "
            f"opening(s) {', '.join(bridged)}. A fragmented-mate resolver "
            "that closes doors is worse than no resolver, so the group is "
            "refused outright rather than trimmed")
    if mean < MIN_WALL_THICKNESS_MM:
        return RECOVERY_REJECTED, REJECT_THIN, (
            f"a {mean:.0f} mm separation is below the minimum wall "
            "thickness: these two lines are not the faces of a wall")
    if spread > SEPARATION_STABILITY_MM:
        return RECOVERY_REJECTED, REJECT_SEPARATION, (
            f"the separation wanders by {spread:.0f} mm along the run. A "
            "wall has one thickness; a varying gap is two different things "
            "being grouped")
    if coverage < MIN_PAIRED_COVERAGE:
        return RECOVERY_REJECTED, REJECT_COVERAGE, (
            f"only {coverage * 100:.0f}% of the continuous face is actually "
            "paired. Most of this 'wall' is gap, and the group is an "
            "assertion rather than a reading")
    unsupported = [g for g in gaps if not g.is_supported]
    if unsupported:
        worst = max(unsupported, key=lambda g: g.length_mm)
        return RECOVERY_DIAGNOSTIC, "", (
            f"{fragments} collinear fragments at a stable {mean:.0f} mm "
            f"separation, {coverage * 100:.0f}% paired — but "
            f"{len(unsupported)} gap(s) totalling "
            f"{sum(g.length_mm for g in unsupported):.0f} mm have nothing "
            f"to explain them (largest {worst.length_mm:.0f} mm). The "
            "paired intervals are real; the gaps are NOT bridged, and "
            "until something accounts for them this group is diagnostic")
    return RECOVERY_VALIDATED, "", (
        f"{fragments} collinear fragments at a stable {mean:.0f} mm "
        f"separation, {coverage * 100:.0f}% of the run paired, and every "
        "gap between fragments explained by the drawing. Material occupies "
        "the paired intervals only")


def summary(groups) -> dict:
    validated = [g for g in groups if g.is_validated]
    diag = [g for g in groups
            if g.validation_status == RECOVERY_DIAGNOSTIC]
    rejected = [g for g in groups
                if g.validation_status == RECOVERY_REJECTED]
    return {
        "groups_attempted": len(groups),
        "validated": len(validated),
        "diagnostic_only": len(diag),
        "rejected": len(rejected),
        "by_group_kind": dict(Counter(g.group_kind for g in groups)),
        "by_reject_reason": dict(Counter(
            g.reject_reason for g in rejected if g.reject_reason)),
        "validated_paired_length_m": round(
            sum(g.paired_length_mm for g in validated) / 1000, 3),
        "diagnostic_paired_length_m": round(
            sum(g.paired_length_mm for g in diag) / 1000, 3),
        "unsupported_gap_length_m": round(
            sum(g.unsupported_gap_length_mm for g in groups) / 1000, 3),
        "supported_gap_length_m": round(
            sum(g.supported_gap_length_mm for g in groups) / 1000, 3),
        "openings_protected": sum(
            1 for g in rejected if g.reject_reason == REJECT_OPENING),
        "source_faces_consumed": len({
            i for g in validated
            for i in g.side_a_source_ids + g.side_b_source_ids}),
        "groups": [g.record() for g in groups],
        "what_decided_acceptance": (
            "axis, collinearity, separation stability, paired coverage, "
            "pen consistency, gap explanation and opening conflict. NOT "
            "room area, room count, a benchmark or a raster millimetre — "
            "none of which this module can see"),
        "hard_invariant": (
            "NO RECOVERED WALL INTERVAL MAY OVERLAP A SUPPORTED OPENING "
            "INTERVAL. A group that would is refused outright, not trimmed "
            "to fit"),
    }


# ------------------------------------------- recovering band extensions

EXTENSION_RECOVERED = "UNRESOLVED_EXTENSION_NOW_PAIRED"
EXTENSION_STILL_UNRESOLVED = "EXTENSION_STILL_UNRESOLVED"

# How far off the opposite face's line a fragment may sit and still be that
# face. The band's own separation is known exactly, so this is tight.
OPPOSITE_LINE_TOLERANCE_MM = 25.0
# A recovered stretch shorter than this is not worth a record.
MIN_RECOVERY_MM = 100.0


@dataclass(frozen=True)
class ExtensionRecovery:
    """One stretch of an accepted band that a fragment turns into material.

    This is the case the round is really about. A band is accepted because
    face A paired with ONE fragment of face B. Face A keeps running; the
    band's polygon runs with it; and the stretch beyond the paired interval
    is recorded UNRESOLVED_EXTENSION — *not established material*. But the
    rest of face B is often drawn, as further collinear fragments that
    never paired with anything.

    Finding them converts hypothesis into established material without
    inventing anything: the second face was drawn all along.
    """

    recovery_id: str
    wall_band_id: str
    axis: str
    side_a_mm: float
    side_b_mm: float
    interval: tuple
    recovered_intervals: tuple = ()
    still_unresolved_intervals: tuple = ()
    fragment_ids: tuple[str, ...] = ()
    separation_mean_mm: float = 0.0
    separation_spread_mm: float = 0.0
    status: str = EXTENSION_STILL_UNRESOLVED
    opening_conflicts: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    drawing_id: str = ""
    drawing_revision: str = ""
    why: str = ""

    @property
    def recovered_mm(self) -> float:
        return sum(e - s for s, e in self.recovered_intervals)

    @property
    def is_recovered(self) -> bool:
        return self.status == EXTENSION_RECOVERED and self.recovered_mm > 0.0

    def record(self) -> dict:
        return {"recovery_id": self.recovery_id,
                "wall_band_id": self.wall_band_id, "axis": self.axis,
                "unresolved_interval": [round(v, 1) for v in self.interval],
                "recovered_intervals": [[round(s, 1), round(e, 1)]
                                        for s, e in
                                        self.recovered_intervals],
                "still_unresolved_intervals": [
                    [round(s, 1), round(e, 1)]
                    for s, e in self.still_unresolved_intervals],
                "recovered_mm": round(self.recovered_mm, 1),
                "fragment_source_ids": list(self.fragment_ids),
                "separation_mean_mm": round(self.separation_mean_mm, 2),
                "separation_spread_mm": round(self.separation_spread_mm, 2),
                "status": self.status,
                "opening_conflicts": list(self.opening_conflicts),
                "evidence": list(self.evidence),
                "drawing_id": self.drawing_id,
                "drawing_revision": self.drawing_revision,
                "why": self.why}


def recover_extensions(admissions, wall_polys, faces, *, portals=(),
                       used_face_ids=(), drawing_id: str = "",
                       revision: str = "") -> list:
    """Turn UNRESOLVED_EXTENSION intervals into material where B was drawn.

    Only intervals the wall authority refused are examined, and only
    fragments on the OPPOSITE face's own line are accepted. Nothing here
    moves a face or changes a thickness: the band's geometry is already
    fixed, and the only question is whether the second face exists there.
    """
    from engine.wall_authority import UNRESOLVED_EXTENSION

    used = set(used_face_ids)
    by_band = {wp.wall_band_id: wp for wp in wall_polys if wp.is_resolved}
    pool: dict = {}
    for f in faces:
        if getattr(f, "segment_id", "") in used:
            continue
        if abs(f.end_mm - f.start_mm) < MIN_FRAGMENT_MM:
            continue
        pool.setdefault(f.axis, []).append(f)

    out, n = [], 0
    for a in admissions:
        if a.grounds != UNRESOLVED_EXTENSION:
            continue
        wp = by_band.get(a.wall_band_id)
        if wp is None or wp.face_a_mm is None or wp.face_b_mm is None:
            continue
        lo, hi = a.start_mm, a.end_mm
        n += 1

        # Which face line is the one that stopped short? The interval is
        # unpaired, so whichever face's recorded intervals do not cover it.
        a_runs = _union(list(getattr(wp, "face_a_intervals", ()) or ()))
        b_runs = _union(list(getattr(wp, "face_b_intervals", ()) or ()))
        a_here = _measure(_intersect([(lo, hi)], a_runs))
        b_here = _measure(_intersect([(lo, hi)], b_runs))
        if a_here >= b_here:
            missing_at, present_at = wp.face_b_mm, wp.face_a_mm
        else:
            missing_at, present_at = wp.face_a_mm, wp.face_b_mm

        found = [f for f in pool.get(wp.axis, ())
                 if abs(f.fixed_mm - missing_at) <= OPPOSITE_LINE_TOLERANCE_MM
                 and max(f.start_mm, f.end_mm) > lo
                 and min(f.start_mm, f.end_mm) < hi]
        covered = _intersect(
            [(lo, hi)],
            _union([(min(f.start_mm, f.end_mm), max(f.start_mm, f.end_mm))
                    for f in found]))
        covered = [(s, e) for s, e in covered if e - s >= MIN_RECOVERY_MM]
        still = _subtract([(lo, hi)], covered)

        seps = [abs(f.fixed_mm - present_at) for f in found]
        mean = sum(seps) / len(seps) if seps else 0.0
        spread = (max(seps) - min(seps)) if seps else 0.0

        bridged = _opening_conflict(covered, wp.axis, present_at,
                                    missing_at, portals)
        ev = []
        if found:
            ev.append("THE_SECOND_FACE_IS_DRAWN_HERE_AS_COLLINEAR_FRAGMENTS")
        if spread <= SEPARATION_STABILITY_MM and found:
            ev.append("SEPARATION_MATCHES_THE_BANDS_OWN_THICKNESS")

        if bridged:
            status, why = EXTENSION_STILL_UNRESOLVED, (
                f"fragments cover this stretch, but the recovered material "
                f"would cross supported opening(s) {', '.join(bridged)}. "
                "Refused: closing a door is worse than leaving a wall "
                "unrecovered")
            covered, still = [], [(lo, hi)]
        elif not covered:
            status, why = EXTENSION_STILL_UNRESOLVED, (
                f"the band's second face is not drawn anywhere along this "
                f"{hi - lo:.0f} mm stretch, so nothing establishes material "
                "here. NEVER INVENT THE MISSING HALF")
        elif spread > SEPARATION_STABILITY_MM:
            status, why = EXTENSION_STILL_UNRESOLVED, (
                f"fragments are present but their distance from the drawn "
                f"face wanders by {spread:.0f} mm, so they are not this "
                "wall's second face")
            covered, still = [], [(lo, hi)]
        else:
            status, why = EXTENSION_RECOVERED, (
                f"{len(found)} collinear fragment(s) on the band's own "
                f"second-face line cover {_measure(covered):.0f} mm of this "
                f"{hi - lo:.0f} mm unresolved stretch at a stable "
                f"{mean:.0f} mm separation. The second face was drawn all "
                "along; nothing is invented, no face moves, and the "
                f"remaining {_measure(still):.0f} mm stays unresolved")

        out.append(ExtensionRecovery(
            recovery_id=f"XR-{n:04d}", wall_band_id=a.wall_band_id,
            axis=wp.axis, side_a_mm=present_at, side_b_mm=missing_at,
            interval=(lo, hi), recovered_intervals=tuple(covered),
            still_unresolved_intervals=tuple(still),
            fragment_ids=tuple(sorted(
                getattr(f, "segment_id", "") for f in found)),
            separation_mean_mm=mean, separation_spread_mm=spread,
            status=status, opening_conflicts=bridged, evidence=tuple(ev),
            drawing_id=drawing_id, drawing_revision=revision, why=why))
    return out


def extension_summary(recoveries) -> dict:
    got = [r for r in recoveries if r.is_recovered]
    return {
        "unresolved_intervals_examined": len(recoveries),
        "intervals_recovered": len(got),
        "recovered_length_m": round(
            sum(r.recovered_mm for r in got) / 1000, 3),
        "still_unresolved_length_m": round(sum(
            sum(e - s for s, e in r.still_unresolved_intervals)
            for r in recoveries) / 1000, 3),
        "refused_for_opening_conflict": sum(
            1 for r in recoveries if r.opening_conflicts),
        "fragments_used": len({i for r in got for i in r.fragment_ids}),
        "by_status": dict(Counter(r.status for r in recoveries)),
        "recoveries": [r.record() for r in recoveries],
        "what_this_converts": (
            "an UNRESOLVED_EXTENSION interval — material the band engine "
            "itself says is not established — into established material, "
            "by finding that the second face was drawn there as fragments "
            "all along. Nothing is invented and no face moves"),
    }


def polygons(groups, *, validated_only: bool = True) -> list:
    """Wall polygons for recovered groups, over the PAIRED intervals only.

    One polygon per paired interval, not one per group: a group whose
    fragments leave a gap must leave that gap in the material too. The
    faces are the two lines the drawing already contains, so nothing moves
    and no thickness is manufactured.
    """
    from shapely.geometry import box

    out = []
    for g in groups:
        if validated_only and not g.is_validated:
            continue
        if g.validation_status == RECOVERY_REJECTED:
            continue
        lo_f, hi_f = sorted((g.side_a_mm, g.side_b_mm))
        for s, e in g.paired_intervals:
            if e - s <= 0.0:
                continue
            out.append(box(s, lo_f, e, hi_f) if g.axis == "H"
                       else box(lo_f, s, hi_f, e))
    return out
