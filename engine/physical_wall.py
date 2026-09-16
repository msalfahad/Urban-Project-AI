"""A wall is a physical object. Its faces are drawings of it, and they break.

Round 4 closed 36 faces on P7757 and one of them was 194 m² holding every
room stamp on the plan. The partitions ARE drawn; they are drawn in pieces,
and a piece missing anywhere on either face lets two rooms merge into one.

The chain this module sits in the middle of is kept whole, and no link may
be skipped:

    CAD primitives
        -> wall-face OBSERVATIONS          (the drawn lines)
        -> wall-BAND hypothesis            (two faces, a thickness)
        -> PHYSICAL WALL hypothesis        (this module)
        -> opening subtraction             (round 4)
        -> room-partition boundary         (the graph)

    NEVER: two collinear lines -> invent a wall.
    NEVER: a gap -> bridge the gap.

WHAT A PHYSICAL WALL IS ALLOWED TO SURVIVE

One built partition can reach this engine as: two continuous parallel
faces; one continuous face and a fragmented opposite; fragments on both
sides; a run broken at every T-junction it passes; a run broken by doors
and windows; or a run broken for no reason at all by whoever drew it.

    THE WALL'S IDENTITY MUST SURVIVE THE FRAGMENTATION OF ITS FACES.

ROUND 6 ADDS THE OTHER HALF OF THAT SENTENCE

The round-5 model asked each pair of parallel lines, in isolation, "are you
a wall?" — and on P7757 845 drawn lines answered yes 3,272 times. 713 of
them belonged to more than one band and one belonged to eight, because
inside any 600 mm band a wall face sits beside its own finish line, a door
frame, a fixture edge and the next room's wall. The phantom partitions that
followed sliced the floor, and four wrong rooms released.

    ONE SOURCE LINE MAY SERVE SEVERAL WALLS ONLY WHERE THOSE WALLS OCCUPY
    DISJOINT STRETCHES OF IT.

That is the explicit geometric evidence, and it is the whole of the new
rule. Which partner a line takes on a contested stretch is settled by NAMED
EVIDENCE in a stated order — an opening hosted, a reveal capping both ends,
mutual agreement — and only then by a thickness the DRAWING ITSELF repeats.

    A THICKNESS MODE IS SUPPORTING EVIDENCE. IT NEVER DEFINES A WALL.

There is no universal "50 mm is not a wall" here and there may not be: a
50 mm feature is usually a detail line and sometimes it is a partition, and
the difference is what it does, not what it measures.

So a wall is assembled from PAIRED evidence — two faces a consistent
distance apart, overlapping along their length — and then its own extent is
described in three separate registers, which are never merged:

    OBSERVED_FACE                 what is actually drawn, per face
    INFERRED_PHYSICAL_WALL_EXTENT what the wall appears to occupy
    MATERIAL_QUANTITY_AUTHORITY   whether blockwork may be measured from it

A span this module can infer for TOPOLOGY is not thereby a span anybody may
take blockwork from. That separation is the whole point of §6, and it is
why the third register exists at all.

NOTHING HERE DECIDES WHETHER A GAP IS CLOSED. That is
`partition_continuity`'s question, and its default answer is UNRESOLVED.
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from engine import cad_profile as cprofile
from engine import space_enclosure as enc

MODEL = "SPACE_BOUNDED_ONE_LINE_ONE_WALL_PHYSICAL_BAND_V3"

# The wall band and the overlap rule are the profile's own, unchanged: they
# are what defined "wall" on this project in the first place.
MIN_WALL_MM = cprofile.MIN_WALL_THICKNESS_MM
MAX_WALL_MM = cprofile.MAX_WALL_THICKNESS_MM
MIN_FACE_OVERLAP_MM = cprofile.MIN_FACE_OVERLAP_MM

# Two drawn pieces on one line are one piece when the enclosure itself
# would not distinguish them. `space_enclosure.JUNCTION_REACH_MM`.
JOIN_MM = enc.JUNCTION_REACH_MM
COLLINEAR_TOL_MM = enc.COLLINEAR_JOIN_MM

# ---------------------------------------------------- pairing evidence
# ROUND 6A. Open space outside each face, and none between them. This is
# what a wall IS, and it is read off the drawn coordinates rather than off
# a layer or a depth. It ranks BELOW the reveals and a hosted opening on
# purpose: those are evidence about one specific pair, while this is also
# true of a pair that straddles a wall AND the detail line drawn beside
# it. It outranks nearness, the repeated thickness and a junction, which
# is where it settles the cases round 6A exists for.
EV_SPACES_STOP_AT_BOTH_FACES = (
    "OPEN_SPACE_LIES_OUTSIDE_EACH_FACE_AND_NONE_BETWEEN_THEM")
EV_HOSTS_AN_OPENING = "AN_OPENING_IS_HOSTED_BETWEEN_THESE_TWO_FACES"
EV_CAPPED_BOTH_ENDS = "A_REVEAL_CLOSES_THE_BAND_AT_BOTH_ENDS"
EV_CAPPED_ONE_END = "A_REVEAL_CLOSES_THE_BAND_AT_ONE_END"
EV_MUTUAL_NEAREST = "EACH_FACE_IS_THE_OTHER_S_NEAREST_ADMISSIBLE_PARTNER"
EV_THICKNESS_MODE = "THE_SEPARATION_IS_A_THICKNESS_THIS_DRAWING_REPEATS"
EV_JUNCTION = "ANOTHER_WALL_MEETS_THIS_BAND"
EV_OVERLAP = "THE_FACES_RUN_ALONGSIDE_EACH_OTHER"

PAIRING_EVIDENCE = (EV_SPACES_STOP_AT_BOTH_FACES, EV_HOSTS_AN_OPENING,
                    EV_CAPPED_BOTH_ENDS, EV_CAPPED_ONE_END,
                    EV_MUTUAL_NEAREST, EV_THICKNESS_MODE, EV_JUNCTION,
                    EV_OVERLAP)

# The order the evidence is read in. NOT a weighted sum — a pair beats
# another pair on the first token where they differ, and the last two are
# tie-breakers rather than evidence.
PRIORITY = (EV_HOSTS_AN_OPENING, EV_CAPPED_BOTH_ENDS, EV_CAPPED_ONE_END,
            EV_SPACES_STOP_AT_BOTH_FACES, EV_MUTUAL_NEAREST,
            EV_THICKNESS_MODE, EV_JUNCTION)

# A separation is a thickness THIS DRAWING REPEATS when it occurs at least
# this many times among the walls established without needing it. One
# occurrence is a measurement; two is a convention.
MODE_MIN_SUPPORT = 2


# How a span of a wall is covered by what is drawn.
BOTH_FACES = "BOTH_FACES_DRAWN"
ONE_FACE_ONLY = "ONE_FACE_DRAWN"
NEITHER_FACE = "NEITHER_FACE_DRAWN"

COVERAGE = (BOTH_FACES, ONE_FACE_ONLY, NEITHER_FACE)

WHAT_EACH_COVERAGE_IS = {
    BOTH_FACES: ("the wall is drawn here. Nothing is inferred, and material "
                 "may be measured from it"),
    ONE_FACE_ONLY: ("one face runs across this span and the other does not. "
                    "The wall MAY be continuous here — that is §5's "
                    "question, and it is asked elsewhere. The missing face "
                    "is never fabricated"),
    NEITHER_FACE: ("neither face is drawn across this span. It may be an "
                   "opening, a missing face, a drafting break, an open-plan "
                   "connection or the wall simply ending. Nothing here "
                   "guesses which"),
}


@dataclass(frozen=True)
class FaceRun:
    """One continuous stretch of ONE drawn face, and what drew it."""

    lo: float
    hi: float
    object_ids: tuple

    @property
    def length_mm(self) -> float:
        return self.hi - self.lo

    def record(self) -> dict:
        return {"interval_mm": [round(self.lo, 2), round(self.hi, 2)],
                "length_mm": round(self.length_mm, 1),
                "cad_provenance": list(self.object_ids)}


@dataclass(frozen=True)
class Span:
    """One stretch of a wall, and how much of it is actually drawn."""

    lo: float
    hi: float
    coverage: str
    face: str = ""            # which face, when only one is drawn
    object_ids: tuple = ()

    @property
    def length_mm(self) -> float:
        return self.hi - self.lo

    def record(self) -> dict:
        return {"interval_mm": [round(self.lo, 2), round(self.hi, 2)],
                "length_mm": round(self.length_mm, 1),
                "coverage": self.coverage,
                "drawn_face": self.face,
                "cad_provenance": list(self.object_ids),
                "what_this_means": WHAT_EACH_COVERAGE_IS[self.coverage]}


@dataclass(frozen=True)
class PhysicalWall:
    """One built partition, however many pieces its faces arrived in."""

    wall_id: str
    region_id: str
    axis: str
    face_a_mm: float
    face_b_mm: float
    face_a: tuple = ()        # FaceRun
    face_b: tuple = ()
    spans: tuple = ()         # Span, in order along the wall
    evidence: tuple = ()      # why these two lines are one wall
    overlap_mm: tuple = ()    # the stretch of each line this wall uses

    @property
    def thickness_mm(self) -> float:
        return abs(self.face_b_mm - self.face_a_mm)

    @property
    def has_pairing_evidence(self) -> bool:
        """Is there any reason to call these two lines a wall but nearness?

        Running alongside each other is what made 3,272 bands out of 845
        lines. A band with nothing else behind it may still be reported —
        it may well be a wall — but it has not earned the right to lend a
        face it never drew to the room topology.
        """
        return any(t != EV_OVERLAP for t in self.evidence)

    @property
    def centre_mm(self) -> float:
        return (self.face_a_mm + self.face_b_mm) / 2.0

    @property
    def observed_extent(self) -> tuple:
        """The first and last millimetre anything of this wall is drawn."""
        runs = list(self.face_a) + list(self.face_b)
        if not runs:
            return (0.0, 0.0)
        return (min(r.lo for r in runs), max(r.hi for r in runs))

    @property
    def drawn_length_mm(self) -> float:
        return sum(s.length_mm for s in self.spans
                   if s.coverage != NEITHER_FACE)

    @property
    def one_face_length_mm(self) -> float:
        return sum(s.length_mm for s in self.spans
                   if s.coverage == ONE_FACE_ONLY)

    @property
    def undrawn_length_mm(self) -> float:
        return sum(s.length_mm for s in self.spans
                   if s.coverage == NEITHER_FACE)

    def gaps(self) -> list:
        """Spans where NEITHER face is drawn. Questions, not conclusions."""
        return [s for s in self.spans if s.coverage == NEITHER_FACE]

    def half_drawn(self) -> list:
        """Spans where exactly one face is drawn. §5's candidates."""
        return [s for s in self.spans if s.coverage == ONE_FACE_ONLY]

    def covers(self, at: float) -> bool:
        lo, hi = self.observed_extent
        return lo - JOIN_MM <= at <= hi + JOIN_MM

    def record(self) -> dict:
        lo, hi = self.observed_extent
        return {
            "wall_id": self.wall_id,
            "drawing_region_id": self.region_id,
            "axis": self.axis,
            "faces_mm": [round(self.face_a_mm, 2), round(self.face_b_mm, 2)],
            "thickness_mm": round(self.thickness_mm, 1),
            "OBSERVED_FACE": {
                "face_a": [r.record() for r in self.face_a],
                "face_b": [r.record() for r in self.face_b],
                "this_is": "what is drawn. Nothing below adds to it"},
            "INFERRED_PHYSICAL_WALL_EXTENT": {
                "interval_mm": [round(lo, 2), round(hi, 2)],
                "length_mm": round(hi - lo, 1),
                "drawn_length_mm": round(self.drawn_length_mm, 1),
                "one_face_only_length_mm": round(self.one_face_length_mm, 1),
                "undrawn_length_mm": round(self.undrawn_length_mm, 1),
                "this_is": ("the extent this wall APPEARS to occupy. It is "
                            "a hypothesis about a physical object, not a "
                            "claim that anything was drawn there")},
            "MATERIAL_QUANTITY_AUTHORITY": {
                "established_length_mm": round(sum(
                    s.length_mm for s in self.spans
                    if s.coverage == BOTH_FACES), 1),
                "this_is": ("only the spans where BOTH faces are drawn. A "
                            "span inferred for topology is not a span "
                            "anybody may take blockwork from")},
            "spans": [s.record() for s in self.spans],
            "PAIRING_EVIDENCE": list(self.evidence),
            "uses_the_lines_over_mm": [round(v, 2)
                                       for v in self.overlap_mm],
            "why_these_two_lines": (
                "named evidence in a stated order, and a line may serve "
                "another wall only over a DISJOINT stretch of itself"),
        }


@dataclass
class WallReport:
    region_id: str = ""
    walls: list = field(default_factory=list)
    unpaired_lines: int = 0
    pairs_offered: int = 0
    pairs_refused_for_overlap: int = 0
    thickness_modes: tuple = ()
    notes: dict = field(default_factory=dict)

    def counts(self) -> dict:
        return {
            "physical_wall_bands": len(self.walls),
            "unpaired_face_lines": self.unpaired_lines,
            "pairs_offered": self.pairs_offered,
            "pairs_refused_because_the_line_was_taken":
                self.pairs_refused_for_overlap,
            "THICKNESSES_THIS_DRAWING_REPEATS": list(self.thickness_modes),
            "walls_with_a_half_drawn_span": sum(
                1 for w in self.walls if w.half_drawn()),
            "walls_with_an_undrawn_gap": sum(
                1 for w in self.walls if w.gaps()),
            "half_drawn_spans": sum(len(w.half_drawn()) for w in self.walls),
            "undrawn_gaps": sum(len(w.gaps()) for w in self.walls),
            "thickness_mm": dict(Counter(
                round(w.thickness_mm) for w in self.walls).most_common(8)),
        }

    def record(self, *, limit: int = 30) -> dict:
        return {
            "model": MODEL,
            "PHYSICAL_WALL_BAND_HASH": wall_band_hash(),
            "drawing_region_id": self.region_id,
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "walls": [w.record() for w in self.walls[:limit]],
            "three_registers": {
                "OBSERVED_FACE": "what is drawn",
                "INFERRED_PHYSICAL_WALL_EXTENT": "what the wall appears "
                                                 "to occupy",
                "MATERIAL_QUANTITY_AUTHORITY": "where blockwork may be "
                                               "measured",
            },
            "never": ("a single unpaired line is not a wall here, however "
                      "long or however collinear with another. Pairing is "
                      "what makes a face a wall, and it is the profile's "
                      "own test"),
            "notes": dict(self.notes),
        }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "MIN_WALL_MM": MIN_WALL_MM,
        "MAX_WALL_MM": MAX_WALL_MM,
        "MIN_FACE_OVERLAP_MM": MIN_FACE_OVERLAP_MM,
        "JOIN_MM": JOIN_MM,
        "COLLINEAR_TOL_MM": COLLINEAR_TOL_MM,
        "PRIORITY": list(PRIORITY),
        "MODE_MIN_SUPPORT": MODE_MIN_SUPPORT,
        "why": {
            "no_new_number": (
                "the wall band and the overlap rule are the profile's, and "
                "the join and collinearity tolerances are the enclosure's. "
                "This module introduces no constant of its own"),
            "one_line_one_wall": (
                "the only structural rule round 6 adds. A line may face "
                "two walls over disjoint stretches and never over the same "
                "stretch — which is explicit geometric evidence, not a "
                "tolerance"),
            "thickness_never_defines": (
                "a separation that the drawing repeats RANKS a contested "
                "pair. It never admits or rejects one, and there is no "
                "universal rule that any particular millimetre figure is "
                "or is not a wall"),
            "pairing_is_required": (
                "a wall is two faces a consistent distance apart. One line "
                "is a line. This is the same structural test the profile "
                "used to decide which layers are wall-like at all"),
        },
    }


def wall_band_hash() -> str:
    parts = [MODEL, str(MIN_WALL_MM), str(MAX_WALL_MM),
             str(MIN_FACE_OVERLAP_MM), str(JOIN_MM), str(COLLINEAR_TOL_MM),
             "|".join(COVERAGE), "|".join(PRIORITY), str(MODE_MIN_SUPPORT)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------------- assembly

def _lines(candidates) -> dict:
    """Every drawn face, merged onto its own line."""
    by_line: dict = defaultdict(list)
    for c in candidates:
        lo, hi = sorted((c.start_mm, c.end_mm))
        key = (c.axis, round(c.fixed_mm / COLLINEAR_TOL_MM))
        by_line[key].append((lo, hi, c.object_id, c.fixed_mm))
    out = {}
    for key, rows in by_line.items():
        rows.sort()
        runs, fixed = [], rows[0][3]
        for lo, hi, oid, f in rows:
            if runs and lo - runs[-1].hi <= JOIN_MM:
                prev = runs[-1]
                runs[-1] = FaceRun(prev.lo, max(prev.hi, hi),
                                   prev.object_ids + (oid,))
            else:
                runs.append(FaceRun(lo, hi, (oid,)))
        out[key] = (key[0], fixed, runs)
    return out


def _union(runs) -> list:
    out = []
    for r in sorted(runs, key=lambda r: r.lo):
        if out and r.lo - out[-1][1] <= JOIN_MM:
            out[-1] = (out[-1][0], max(out[-1][1], r.hi))
        else:
            out.append((r.lo, r.hi))
    return out


def _overlap(a, b) -> float:
    total = 0.0
    for lo1, hi1 in a:
        for lo2, hi2 in b:
            total += max(0.0, min(hi1, hi2) - max(lo1, lo2))
    return total


def _spans(face_a, face_b, thickness_mm: float = 0.0, owned=None) -> tuple:
    """Walk the wall once and say, for every stretch, what is drawn.

    A SHORT OVERHANG IS A CORNER, NOT A MISSING FACE. Where a ring's outer
    face wraps past its inner one, the overhang is the wall's own
    thickness, and treating it as a stretch of wall with a face missing
    would have this module "recovering" every corner of every building.

    A face that runs METRES past its partner is a different thing: that is
    the wall, with its other face not drawn, and it is exactly the case §5
    exists for. The boundary between the two is the wall's own thickness,
    measured here.
    """
    ua, ub = _union(face_a), _union(face_b)
    if not ua or not ub:
        return ()
    lo_a, hi_a = min(iv[0] for iv in ua), max(iv[1] for iv in ua)
    lo_b, hi_b = min(iv[0] for iv in ub), max(iv[1] for iv in ub)
    # An OVERHANG no longer than the wall's own thickness is a corner
    # return and is trimmed. A face that runs metres past its partner is
    # not an overhang — it is the wall, with its other face missing, and
    # that IS a continuity question.
    t = max(thickness_mm, JOIN_MM)
    span_lo = max(lo_a, lo_b) if abs(lo_a - lo_b) <= t else min(lo_a, lo_b)
    span_hi = min(hi_a, hi_b) if abs(hi_a - hi_b) <= t else max(hi_a, hi_b)
    if owned is not None:
        span_lo = max(span_lo, min(owned))
        span_hi = min(span_hi, max(owned))
    if span_hi - span_lo <= JOIN_MM:
        return ()
    edges = sorted({min(max(v, span_lo), span_hi)
                    for iv in ua + ub for v in iv} | {span_lo, span_hi})
    out = []
    for lo, hi in zip(edges, edges[1:]):
        if hi - lo <= JOIN_MM:
            continue
        mid = (lo + hi) / 2.0
        in_a = any(x <= mid <= y for x, y in ua)
        in_b = any(x <= mid <= y for x, y in ub)
        if in_a and in_b:
            cov, face = BOTH_FACES, ""
            ids = tuple(
                oid for r in list(face_a) + list(face_b)
                if r.lo <= mid <= r.hi for oid in r.object_ids)
        elif in_a or in_b:
            cov = ONE_FACE_ONLY
            face = "A" if in_a else "B"
            src = face_a if in_a else face_b
            ids = tuple(oid for r in src if r.lo <= mid <= r.hi
                        for oid in r.object_ids)
        else:
            cov, face, ids = NEITHER_FACE, "", ()
        if out and out[-1].coverage == cov and out[-1].face == face:
            prev = out[-1]
            out[-1] = Span(prev.lo, hi, cov, face,
                           prev.object_ids + tuple(ids))
        else:
            out.append(Span(lo, hi, cov, face, tuple(ids)))
    return tuple(out)


def _capped(candidates, axis, f_lo, f_hi, station) -> bool:
    """Is the band closed across its faces at this station?

    A reveal — the short perpendicular piece that closes a wall at a door,
    at a corner or at its end — is the strongest cheap evidence that two
    lines are the two faces of one wall. Two unrelated parallel lines have
    nothing across them.
    """
    for c in candidates:
        if c.axis == axis or c.axis not in ("H", "V"):
            continue
        if abs(c.fixed_mm - station) > COLLINEAR_TOL_MM:
            continue
        lo, hi = sorted((c.start_mm, c.end_mm))
        if lo <= f_lo + COLLINEAR_TOL_MM and hi >= f_hi - COLLINEAR_TOL_MM:
            return True
    return False


def _hosted_openings(openings) -> set:
    """The face pairs an already-classified opening says are one wall."""
    out = set()
    for o in openings or ():
        faces = o.wall_faces_mm or ()
        if len(faces) < 2:
            continue
        out.add((o.axis, round(min(faces), 1), round(max(faces), 1)))
    return out


def _intersect(a, b) -> list:
    """Every stretch where BOTH lines are actually drawn.

    A SET, not a hull. P7757 draws its east wall as one line from the
    kitchen to the corridor and another from the corridor to the stair,
    and taking the outer hull made a single pair claim nine metres of a
    line it is only alongside for three — which then robbed the wall that
    really is drawn there.
    """
    out = []
    for lo1, hi1 in a:
        for lo2, hi2 in b:
            lo, hi = max(lo1, lo2), min(hi1, hi2)
            if hi - lo > JOIN_MM:
                out.append((lo, hi))
    return sorted(out)


def _subtract(ivs, blocks) -> list:
    """What is left of these stretches once those are taken away."""
    cur = list(ivs)
    for blo, bhi in blocks:
        nxt = []
        for lo, hi in cur:
            if bhi <= lo + JOIN_MM or blo >= hi - JOIN_MM:
                nxt.append((lo, hi))
                continue
            if blo - lo > JOIN_MM:
                nxt.append((lo, blo))
            if hi - bhi > JOIN_MM:
                nxt.append((bhi, hi))
        cur = nxt
    return cur


def _total(ivs) -> float:
    return sum(hi - lo for lo, hi in ivs)


def build(candidates, *, region_id: str = "DR-001", openings=(),
          topology=None) -> WallReport:
    """Assemble this region's physical walls from its drawn faces.

    TWO PASSES, and the second is the one round 6 exists for.

    The first accepts only pairs that need no thickness argument at all —
    a band hosting an opening, or closed by a reveal at both ends. Those
    are walls on their own evidence, and the separations they show ARE this
    drawing's wall thicknesses.

    The second offers every remaining pair, ranked by named evidence in a
    stated order, and accepts one only where BOTH its lines are still free
    over that stretch. A line already spoken for between y=0 and y=4000 may
    still be a face of another wall between y=6000 and y=10000; it may not
    be a face of two walls over the same 4 metres.
    """
    rep = WallReport(region_id=region_id)
    lines = _lines(candidates)
    keys = sorted(lines)
    unions = {k: _union(lines[k][2]) for k in keys}
    hosted = _hosted_openings(openings)

    # ---- every admissible pair, with its evidence ---------------------
    pairs = []
    for i, ka in enumerate(keys):
        axis_a, fa, runs_a = lines[ka]
        for kb in keys[i + 1:]:
            axis_b, fb, runs_b = lines[kb]
            if axis_b != axis_a:
                continue
            sep = abs(fb - fa)
            if sep < MIN_WALL_MM or sep > MAX_WALL_MM:
                continue
            ivs = _intersect(unions[ka], unions[kb])
            if _total(ivs) < MIN_FACE_OVERLAP_MM:
                continue
            iv = (ivs[0][0], ivs[-1][1])
            f_lo, f_hi = min(fa, fb), max(fa, fb)
            ev = [EV_OVERLAP]
            if topology is not None and topology(axis_a, fa, fb, iv):
                ev.append(EV_SPACES_STOP_AT_BOTH_FACES)
            if (axis_a, round(f_lo, 1), round(f_hi, 1)) in hosted:
                ev.append(EV_HOSTS_AN_OPENING)
            caps = sum(1 for st in (ivs[0][0], ivs[-1][1])
                       if _capped(candidates, axis_a, f_lo, f_hi, st))
            if caps >= 2:
                ev.append(EV_CAPPED_BOTH_ENDS)
            elif caps == 1:
                ev.append(EV_CAPPED_ONE_END)
            spans = _spans(runs_a, runs_b, sep)
            if not spans:
                continue
            # ROUND 6A. The stretch this pair would SPEAK about — not just
            # the stretch its two faces run alongside. Continuity recovers
            # from the spans, so one-line-one-wall has to be decided over
            # them: a 400 mm band accepted north of P7757's kitchen was
            # otherwise recovering a face straight through the kitchen.
            pairs.append({"a": ka, "b": kb, "sep": sep, "iv": iv,
                          "ivs": ivs, "spans": spans,
                          "overlap": _total(ivs),
                          "ev": ev, "axis": axis_a, "fa": fa, "fb": fb,
                          "runs_a": runs_a, "runs_b": runs_b})

    # mutual nearest, computed once over the admissible set
    nearest = {}
    for pr in pairs:
        for x, y in ((pr["a"], pr), (pr["b"], pr)):
            cur = nearest.get(x)
            if cur is None or (pr["sep"], -pr["overlap"]) < \
                    (cur["sep"], -cur["overlap"]):
                nearest[x] = pr
    for pr in pairs:
        if nearest.get(pr["a"]) is pr and nearest.get(pr["b"]) is pr:
            pr["ev"].append(EV_MUTUAL_NEAREST)

    # ---- pass one: walls that need no thickness argument --------------
    taken: dict = {}

    def _parts(pr) -> list:
        """The stretches of this pair still free on BOTH of its lines."""
        free = _subtract(pr["ivs"], taken.get(pr["a"], ()))
        return _subtract(free, taken.get(pr["b"], ()))

    def _long_enough(parts) -> bool:
        """Is what is left of this pair still a wall's worth of overlap?

        The TOTAL, because a partition drawn in two 400 mm stubs either
        side of a doorway is one wall — that is round 5's case W and the
        whole point of merging faces into runs before pairing.
        """
        return _total(parts) >= MIN_FACE_OVERLAP_MM

    def _accept(pr, parts) -> None:
        pr["parts"] = parts
        pr["iv"] = (parts[0][0], parts[-1][1])
        for key in (pr["a"], pr["b"]):
            taken.setdefault(key, []).extend(parts)
        accepted.append(pr)

    accepted: list = []
    certain = [pr for pr in pairs
               if EV_SPACES_STOP_AT_BOTH_FACES in pr["ev"]
               or EV_HOSTS_AN_OPENING in pr["ev"]
               or EV_CAPPED_BOTH_ENDS in pr["ev"]]
    certain.sort(key=lambda pr: (-_rank(pr), -pr["overlap"], pr["sep"]))
    for pr in certain:
        parts = _parts(pr)
        if _long_enough(parts):
            _accept(pr, parts)

    # ---- the drawing's own thicknesses, read off those walls ----------
    support = Counter(round(pr["sep"], 1) for pr in accepted)
    modes = tuple(sorted(t for t, n in support.items()
                         if n >= MODE_MIN_SUPPORT))
    rep.thickness_modes = modes
    for pr in pairs:
        if round(pr["sep"], 1) in modes and EV_THICKNESS_MODE not in pr["ev"]:
            pr["ev"].append(EV_THICKNESS_MODE)

    # ---- pass two: everything else, ranked, one stretch per line ------
    rest = [pr for pr in pairs if pr not in accepted]
    rest.sort(key=lambda pr: (-_rank(pr), -pr["overlap"], pr["sep"]))
    for pr in rest:
        parts = _parts(pr)
        if _long_enough(parts):
            _accept(pr, parts)

    # ---- ROUND 6A: a wall speaks only where no other wall does --------
    #
    # A band whose two faces are drawn over four metres used to SPAN the
    # nine metres one of its faces happens to run, and continuity then
    # recovered a face right through the room next door. So each accepted
    # wall's spans are trimmed at the first stretch either of its lines
    # already gives to a different wall. The wall keeps everything up to
    # that point — which is what §5 needs — and nothing past it.
    for pr in accepted:
        lo, hi = float("-inf"), float("inf")
        for other in accepted:
            if other is pr:
                continue
            if other["a"] not in (pr["a"], pr["b"]) and \
                    other["b"] not in (pr["a"], pr["b"]):
                continue
            for o_lo, o_hi in other["parts"]:
                if o_hi <= pr["iv"][0] + JOIN_MM:
                    lo = max(lo, o_hi)
                elif o_lo >= pr["iv"][1] - JOIN_MM:
                    hi = min(hi, o_lo)
        pr["allowed"] = (lo, hi)
    for pr in accepted:
        pr["spans"] = _spans(pr["runs_a"], pr["runs_b"], pr["sep"],
                             owned=pr["allowed"])

    for pr in accepted:
        sep = pr["sep"]
        wall_id = (f"PW-{region_id}-{pr['axis']}-"
                   f"{round(min(pr['fa'], pr['fb']), 1)}-{round(sep, 1)}")
        rep.walls.append(PhysicalWall(
            wall_id=wall_id, region_id=region_id, axis=pr["axis"],
            face_a_mm=pr["fa"], face_b_mm=pr["fb"],
            face_a=tuple(pr["runs_a"]), face_b=tuple(pr["runs_b"]),
            spans=pr["spans"],
            evidence=tuple(pr["ev"]), overlap_mm=pr["iv"]))

    rep.unpaired_lines = len(keys) - len({k for pr in accepted
                                          for k in (pr["a"], pr["b"])})
    rep.pairs_offered = len(pairs)
    rep.pairs_refused_for_overlap = len(pairs) - len(accepted)
    rep.notes["what_pairing_means"] = (
        "two faces a consistent distance apart, overlapping along their "
        "length, chosen by named evidence in a stated order. A line with "
        "no partner stays a line")
    rep.notes["where_the_spaces_stop"] = (
        "a pair whose faces have open space outside each of them and none "
        "between them is a wall on the drawing's own evidence. A counter "
        "front has floor on BOTH sides and a glazing line has wall on "
        "both, and neither is where a room ends"
        if topology is not None else
        "not asked: no arrangement was supplied to this build")
    rep.notes["one_line_one_wall"] = (
        "a line may serve several walls only over DISJOINT stretches of "
        "itself. On a contested stretch the better-evidenced pair wins and "
        "the other is refused — which is the round-5 defect, closed")
    rep.notes["thickness_is_evidence_not_a_definition"] = (
        f"the thicknesses this drawing repeats are {list(modes)} mm, read "
        "off the walls that needed no thickness argument. They RANK a "
        "contested pair and they never admit or reject one on their own")
    rep.notes["fragmentation"] = (
        "faces are merged into runs before pairing, so a wall drawn in "
        "eleven pieces is one wall. Where the runs leave a hole, the hole "
        "is RECORDED as a span and nothing is concluded about it here")
    return rep


def _rank(pr) -> int:
    """Where this pair sits in the stated evidence order. Not a score.

    Each token is worth more than everything below it put together, so a
    pair beats another on the FIRST token where they differ. That is an
    ordering, not a weighted sum, and no total is compared to a threshold.
    """
    value = 0
    for n, token in enumerate(reversed(PRIORITY)):
        if token in pr["ev"]:
            value |= 1 << n
    return value
