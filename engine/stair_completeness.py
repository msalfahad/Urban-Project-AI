"""E1.1 §I — every stair on the floor is DETECTED or EXPLICITLY UNRESOLVED.

E1 v1 looked for evenly pitched parallel lines and found two straight
flights. The sheet plainly holds more than that: a curved flight winding
up beside the reception, external steps into the garden, and treads that
turn a corner. A stair that is simply absent from the register is worse
than one recorded as unresolved, because nothing downstream can tell the
difference between "there is no stair here" and "nobody looked".

So this pass is a COMPLETENESS pass. It reads tread-like repetition of
every kind the drawing can hold:

    STRAIGHT_FLIGHT     parallel treads, evenly pitched
    L_SHAPED            two straight flights meeting at a right angle
    U_SHAPED            two straight flights parallel and opposed
    CURVED              treads on a common centre, evenly pitched in angle
    WINDER              a straight flight with radial treads at one end
    SPIRAL_OR_RADIAL    radial treads only, about one centre
    EXTERNAL_STEPS      a short flight outside the built envelope
    UNRESOLVED_STAIR    repetition that reads as treads and fits none of
                        the above, or a stair label with no assembly found

No riser height is inferred and no marble is calculated. A riser needs a
section, and E1.1 does not have one.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

MODEL = "A_STAIR_IS_DETECTED_OR_EXPLICITLY_UNRESOLVED_NEVER_ABSENT_V1"

STRAIGHT_FLIGHT = "STRAIGHT_FLIGHT"
L_SHAPED = "L_SHAPED"
U_SHAPED = "U_SHAPED"
CURVED = "CURVED"
WINDER = "WINDER"
SPIRAL_OR_RADIAL = "SPIRAL_OR_RADIAL"
EXTERNAL_STEPS = "EXTERNAL_STEPS"
UNRESOLVED_STAIR = "UNRESOLVED_STAIR"
STAIR_TYPES = (STRAIGHT_FLIGHT, L_SHAPED, U_SHAPED, CURVED, WINDER,
               SPIRAL_OR_RADIAL, EXTERNAL_STEPS, UNRESOLVED_STAIR)

DETECTED = "DETECTED"
EXPLICITLY_UNRESOLVED = "EXPLICITLY_UNRESOLVED"

NEVER_SILENTLY_ABSENT = (
    "a stair the drawing shows must appear in this register as DETECTED or "
    "as EXPLICITLY_UNRESOLVED. Silence would let a later stage believe the "
    "floor has no stair there")

NO_RISER_WITHOUT_A_SECTION = (
    "rise, riser height and the number of risers need a section. None is "
    "inferred here, and no stair quantity is computed")

# --- GENERAL stair geometry ---------------------------------------------
# Ordinary going for a tread, in any building.
TREAD_PITCH_MIN_MM = 200.0
TREAD_PITCH_MAX_MM = 400.0
MIN_TREADS = 3
MIN_TREAD_WIDTH_MM = 600.0
PITCH_TOL_MM = 40.0
# A radial tread family sweeps evenly about one centre.
ANGLE_PITCH_MIN_DEG = 5.0
ANGLE_PITCH_MAX_DEG = 45.0
ANGLE_TOL_DEG = 6.0
RADIAL_CENTRE_TOL_MM = 200.0
FLIGHT_JOIN_MM = 2500.0
# A fan of treads is a fan: at least four of them, of comparable going,
# with their far ends on a common circle. Three lines whose ends happen to
# meet is a wall corner, and the first version of this rule called
# twenty-one of those a staircase.
MIN_RADIAL_TREADS = 4
RADIAL_LENGTH_RATIO = 0.55
RADIAL_RADIUS_RATIO = 0.80
# A WINDER TREAD POINTS AT THE CENTRE BUT DOES NOT REACH IT: it runs from
# an inner radius to an outer one, between two concentric arcs. A SETTING
# OUT LINE runs from the centre. That one ratio is what keeps a pool's
# radial construction lines out of the stair register, and the pool's
# wedges out of the room register.
RADIAL_LINE_TOL_MM = 150.0
MIN_INNER_RADIUS_SHARE = 0.15

SCOPE = ("GENERAL stair geometry. No project coordinate or storey height "
         "appears here")


def model_hash() -> str:
    parts = ([MODEL] + list(STAIR_TYPES)
             + [f"{TREAD_PITCH_MIN_MM}", f"{TREAD_PITCH_MAX_MM}",
                f"{MIN_TREADS}", f"{MIN_TREAD_WIDTH_MM}",
                f"{ANGLE_PITCH_MIN_DEG}", f"{ANGLE_PITCH_MAX_DEG}"])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


@dataclass
class Assembly:
    assembly_id: str = ""
    stair_type: str = UNRESOLVED_STAIR
    status: str = DETECTED
    treads: tuple = ()
    pitches: tuple = ()
    centre: tuple = ()
    evidence: tuple = ()
    why: str = ""

    def extent(self) -> tuple:
        xs, ys = [], []
        for t in self.treads:
            xs += [t.x1, t.x2]
            ys += [t.y1, t.y2]
        if not xs:
            return (0.0, 0.0, 0.0, 0.0)
        return (min(xs), min(ys), max(xs), max(ys))

    def record(self) -> dict:
        x0, y0, x1, y1 = self.extent()
        return {
            "STAIR_ASSEMBLY": self.assembly_id,
            "STAIR_TYPE": self.stair_type,
            "STATUS": self.status,
            "tread_count": len(self.treads),
            "TREAD": [{"tread_id": f"{self.assembly_id}-T{i + 1:02d}",
                       "entity": t.provenance.record(),
                       "line_mm": [round(t.x1, 3), round(t.y1, 3),
                                   round(t.x2, 3), round(t.y2, 3)],
                       "width_mm": round(t.length_mm, 2)}
                      for i, t in enumerate(self.treads)],
            "pitches_mm_or_deg": [round(p, 3) for p in self.pitches],
            "centre_mm": ([round(self.centre[0], 2),
                           round(self.centre[1], 2)] if self.centre else None),
            "extent_for_indexing_only_mm": [round(x0, 2), round(y0, 2),
                                            round(x1, 2), round(y1, 2)],
            "evidence": list(self.evidence),
            "RISER": NO_RISER_WITHOUT_A_SECTION,
            "LANDING": "NOT_ESTABLISHED_IN_E1_1",
            "SOLID_VISIBLE_GEOMETRY": "NOT_DISTINGUISHED",
            "DASHED_BEYOND_CUT_PLANE": "NOT_DISTINGUISHED",
            "why": self.why,
            "not_a_flooring_zone": ("a stair polygon is not a flooring "
                                    "measurement zone and no marble is "
                                    "computed here"),
        }


def _axis_runs(segs):
    """Groups of parallel, evenly pitched, similar-length lines."""
    out = []
    by_dir = {}
    for p in segs:
        dx, dy = p.x2 - p.x1, p.y2 - p.y1
        n = math.hypot(dx, dy)
        if n < MIN_TREAD_WIDTH_MM:
            continue
        a = int(round((math.degrees(math.atan2(dy, dx)) % 180.0) / 2.0))
        by_dir.setdefault(a, []).append((p, (dx / n, dy / n), n))
    for a, items in by_dir.items():
        rows = {}
        for p, u, n in items:
            nx, ny = -u[1], u[0]
            off = p.x1 * nx + p.y1 * ny
            rows.setdefault(round(n / 100.0), []).append((off, p))
        for width_key, group in rows.items():
            if len(group) < MIN_TREADS:
                continue
            group.sort(key=lambda r: r[0])
            run, prev = [], None
            pitches = []
            for off, p in group:
                if prev is None:
                    run, pitches = [p], []
                elif TREAD_PITCH_MIN_MM <= abs(off - prev) \
                        <= TREAD_PITCH_MAX_MM and (
                            not pitches
                            or abs(abs(off - prev) - pitches[-1])
                            <= PITCH_TOL_MM):
                    run.append(p)
                    pitches.append(abs(off - prev))
                else:
                    if len(run) >= MIN_TREADS:
                        out.append((tuple(run), tuple(pitches)))
                    run, pitches = [p], []
                prev = off
            if len(run) >= MIN_TREADS:
                out.append((tuple(run), tuple(pitches)))
    return out


def _radial_runs(segs, centres=(), rejected=None):
    """Treads that fan about a common centre, evenly pitched in angle.

    A candidate centre comes from the drawing's own concentric curve
    families - the arcs a curved flight is drawn between. A line belongs
    to the fan when it POINTS AT that centre and STOPS SHORT OF IT: a
    winder tread spans from the inner arc to the outer one, while a
    setting-out line runs from the centre itself and is excluded here.
    """
    cands = [p for p in segs
             if math.hypot(p.x2 - p.x1, p.y2 - p.y1) >= MIN_TREAD_WIDTH_MM]
    used, out = set(), []
    for (cx, cy, outer) in centres:
        fam = []
        for q in cands:
            if q.object_id in used:
                continue
            dx, dy = q.x2 - q.x1, q.y2 - q.y1
            n = math.hypot(dx, dy) or 1.0
            perp = abs((dx * (cy - q.y1) - dy * (cx - q.x1)) / n)
            if perp > RADIAL_LINE_TOL_MM:
                continue
            r1 = math.hypot(q.x1 - cx, q.y1 - cy)
            r2 = math.hypot(q.x2 - cx, q.y2 - cy)
            r_in, r_out = min(r1, r2), max(r1, r2)
            if r_out > outer * 1.25 or r_out <= 0:
                continue
            if r_in / r_out < MIN_INNER_RADIUS_SHARE:
                continue                      # it reaches the centre
            far = (q.x1, q.y1) if r1 >= r2 else (q.x2, q.y2)
            fam.append((q, far, r_out, n))
        if len(fam) < MIN_RADIAL_TREADS:
            continue
        # TREADS OF ONE FLIGHT ARE ALIKE. Keep the largest group of
        # members that share an outer radius and a going, so one stray
        # dimension line pointing at the same centre cannot disqualify a
        # whole staircase - which is exactly what it did first time.
        raw = len(fam)
        med_r = sorted(row[2] for row in fam)[len(fam) // 2]
        med_n = sorted(row[3] for row in fam)[len(fam) // 2]
        fam = [row for row in fam
               if abs(row[2] - med_r) <= 0.10 * med_r
               and abs(row[3] - med_n) <= 0.10 * med_n]
        if len(fam) < MIN_RADIAL_TREADS:
            if rejected is not None and raw >= MIN_RADIAL_TREADS:
                rejected.append(((cx, cy), raw,
                                 "TREADS_ABOUT_THIS_CENTRE_ARE_NOT_ALIKE"))
            continue
        radii = [r for _q, _f, r, _n in fam]
        lens = [n for _q, _f, _r, n in fam]
        if min(radii) / max(radii) < RADIAL_RADIUS_RATIO or \
                min(lens) / max(lens) < RADIAL_LENGTH_RATIO:
            if rejected is not None:
                rejected.append(((cx, cy), len(fam),
                                 "RADIAL_LINES_ABOUT_ONE_CENTRE_THAT_ARE_"
                                 "NOT_A_FLIGHT_OF_ALIKE_TREADS"))
            continue
        angs = sorted(
            ((math.degrees(math.atan2(f[1] - cy, f[0] - cx)) % 360.0, q)
             for q, f, _r, _n in fam), key=lambda row: row[0])
        # A tread is often drawn twice - a nosing beside its edge - at the
        # same angle. Two lines at the same angle are one tread.
        deduped, last = [], None
        for a, q in angs:
            if last is not None and (a - last) < ANGLE_PITCH_MIN_DEG:
                continue
            deduped.append((a, q))
            last = a
        angs = deduped
        run, pitches, prev = [], [], None
        for a, q in angs:
            if prev is None:
                run, pitches = [q], []
            elif ANGLE_PITCH_MIN_DEG <= (a - prev) <= ANGLE_PITCH_MAX_DEG \
                    and (not pitches
                         or abs((a - prev) - pitches[-1]) <= ANGLE_TOL_DEG):
                run.append(q)
                pitches.append(a - prev)
            else:
                if len(run) >= MIN_RADIAL_TREADS:
                    out.append((tuple(run), tuple(pitches), (cx, cy)))
                    used.update(x.object_id for x in run)
                run, pitches = [q], []
            prev = a
        if len(run) >= MIN_RADIAL_TREADS:
            out.append((tuple(run), tuple(pitches), (cx, cy)))
            used.update(x.object_id for x in run)
        elif rejected is not None and len(angs) >= MIN_RADIAL_TREADS:
            rejected.append(((cx, cy), len(angs),
                             "TREAD_LIKE_LINES_ABOUT_ONE_CENTRE_WITH_NO_"
                             "EVEN_ANGULAR_PITCH"))
    return out


def _bbox(run):
    xs = [v for t in run for v in (t.x1, t.x2)]
    ys = [v for t in run for v in (t.y1, t.y2)]
    return (min(xs), min(ys), max(xs), max(ys))


def _near(a, b, tol=FLIGHT_JOIN_MM):
    return not (a[2] + tol < b[0] or b[2] + tol < a[0]
                or a[3] + tol < b[1] or b[3] + tol < a[1])


def detect(primitives, *, inside_envelope=None, stair_label_points=(),
           exclude_object_ids=(), radial_centres=(),
           label_terms=("STAIR", "STAIRS", "STAIRCASE", "STEPS",
                        "STAIR CASE")) -> dict:
    """Every stair assembly the CAD supports, by type, plus what is not
    resolved.

    `exclude_object_ids` are entities whose role is already established as
    something a tread cannot be - a wall face, a cabinet front, a
    dimension, a door. Without that exclusion a pair of wall faces 200 mm
    apart reads as two treads, and a wall corner reads as a fan.

    `inside_envelope(x, y) -> bool` decides external steps.
    """
    skip = set(exclude_object_ids or ())
    segs = [p for p in primitives
            if p.kind == "SEGMENT" and p.object_id not in skip]
    straight = _axis_runs(segs)
    radial_rejected = []
    radial = _radial_runs(segs, centres=tuple(radial_centres),
                          rejected=radial_rejected)

    used = set()
    assemblies = []

    def add(kind, run, pitches, centre=(), evidence=(), why=""):
        n = len(assemblies) + 1
        a = Assembly(assembly_id=f"E1_1-STAIR-{n:02d}", stair_type=kind,
                     treads=tuple(run), pitches=tuple(pitches),
                     centre=tuple(centre), evidence=tuple(evidence), why=why)
        assemblies.append(a)
        used.update(t.object_id for t in run)
        return a

    # --- radial families first: they also make winders ------------------
    radial_boxes = []
    for run, pitches, anchor in radial:
        if any(t.object_id in used for t in run):
            continue
        radial_boxes.append((run, pitches, anchor, _bbox(run)))

    straight_left = []
    for run, pitches in straight:
        if any(t.object_id in used for t in run):
            continue
        straight_left.append((run, pitches, _bbox(run)))

    # a straight flight adjoining a radial family is a winder
    for run, pitches, anchor, box in radial_boxes:
        mate = None
        for s_run, s_pitch, s_box in straight_left:
            if _near(box, s_box):
                mate = (s_run, s_pitch, s_box)
                break
        if mate is not None:
            add(WINDER, tuple(run) + tuple(mate[0]),
                tuple(pitches) + tuple(mate[1]), centre=anchor,
                evidence=("RADIAL_TREADS_ABOUT_ONE_CENTRE",
                          "A_STRAIGHT_FLIGHT_ADJOINS_THEM"),
                why=("treads fan evenly about a point and a straight flight "
                     "runs on from them, which is a winder"))
            straight_left = [x for x in straight_left if x is not mate]
        else:
            sweep = sum(pitches)
            add(SPIRAL_OR_RADIAL if sweep >= 180.0 else CURVED,
                run, pitches, centre=anchor,
                evidence=("RADIAL_TREADS_ABOUT_ONE_CENTRE",
                          f"SWEEP_DEG={round(sweep, 1)}"),
                why=("treads fan evenly about one point, so the flight "
                     "turns as it rises"))

    # --- straight flights, then L and U ---------------------------------
    placed = []
    for run, pitches, box in straight_left:
        if any(t.object_id in used for t in run):
            continue
        placed.append((run, pitches, box))
    merged = set()
    for i, (run, pitches, box) in enumerate(placed):
        if i in merged:
            continue
        partner = None
        for j in range(i + 1, len(placed)):
            if j in merged:
                continue
            run2, p2, box2 = placed[j]
            if not _near(box, box2):
                continue
            u1 = _unit(run[0])
            u2 = _unit(run2[0])
            turn = abs(math.degrees(math.acos(
                max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1])))))
            turn = min(turn, 180.0 - turn)
            partner = (j, run2, p2, turn)
            break
        if partner is None:
            outside = (inside_envelope is not None
                       and not inside_envelope(*_centre_of(run)))
            add(EXTERNAL_STEPS if outside else STRAIGHT_FLIGHT,
                run, pitches,
                evidence=("PARALLEL_EVENLY_PITCHED_TREADS",)
                + (("THE_FLIGHT_LIES_OUTSIDE_THE_BUILT_ENVELOPE",)
                   if outside else ()),
                why=("evenly pitched parallel treads of similar width"))
            continue
        j, run2, p2, turn = partner
        merged.add(j)
        kind = L_SHAPED if turn >= 45.0 else U_SHAPED
        add(kind, tuple(run) + tuple(run2), tuple(pitches) + tuple(p2),
            evidence=("TWO_STRAIGHT_FLIGHTS_MEET",
                      f"TURN_DEG={round(turn, 1)}"),
            why=("two flights of treads adjoin, turning "
                 f"{turn:.0f} degrees between them"))

    # --- tread-like repetition that resolved into nothing ---------------
    for (centre, n, why) in radial_rejected:
        if any(_near((centre[0], centre[1], centre[0], centre[1]),
                     a.extent(), FLIGHT_JOIN_MM) for a in assemblies):
            continue
        k = len(assemblies) + 1
        assemblies.append(Assembly(
            assembly_id=f"E1_1-STAIR-{k:02d}", stair_type=UNRESOLVED_STAIR,
            status=EXPLICITLY_UNRESOLVED, centre=tuple(centre),
            evidence=(why, f"LINES_ABOUT_THIS_CENTRE={n}"),
            why=("lines about one centre read as tread-like repetition and "
                 "did not resolve into a flight. Recorded as unresolved "
                 "rather than left out")))

    # --- labelled stairs with no assembly -------------------------------
    terms = tuple(t.upper() for t in label_terms)
    unresolved = []
    for (x, y, token) in stair_label_points:
        if str(token).upper() not in terms:
            continue
        hit = any(_near((x, y, x, y), a.extent(), FLIGHT_JOIN_MM)
                  for a in assemblies)
        if not hit:
            n = len(assemblies) + 1
            a = Assembly(assembly_id=f"E1_1-STAIR-{n:02d}",
                         stair_type=UNRESOLVED_STAIR,
                         status=EXPLICITLY_UNRESOLVED,
                         evidence=("A_STAIR_LABEL_WITH_NO_TREAD_FAMILY",),
                         why=("the drawing names a stair here and no tread "
                              "family was established. Recorded as "
                              "unresolved rather than left out"))
            assemblies.append(a)
            unresolved.append(a.assembly_id)

    return {
        "assemblies": assemblies,
        "count": len(assemblies),
        "by_type": {t: sum(1 for a in assemblies if a.stair_type == t)
                    for t in STAIR_TYPES},
        "detected": sum(1 for a in assemblies if a.status == DETECTED),
        "explicitly_unresolved": sum(1 for a in assemblies
                                     if a.status == EXPLICITLY_UNRESOLVED),
        "tread_object_ids": tuple(t.object_id for a in assemblies
                                  for t in a.treads),
        "never_silently_absent": NEVER_SILENTLY_ABSENT,
        "no_riser_without_a_section": NO_RISER_WITHOUT_A_SECTION,
    }


def _unit(p):
    dx, dy = p.x2 - p.x1, p.y2 - p.y1
    n = math.hypot(dx, dy) or 1.0
    return (dx / n, dy / n)


def _centre_of(run):
    xs = [v for t in run for v in (t.x1, t.x2)]
    ys = [v for t in run for v in (t.y1, t.y2)]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "STAIR_TYPES": list(STAIR_TYPES),
        "STATUSES": [DETECTED, EXPLICITLY_UNRESOLVED],
        "TREAD_PITCH_MIN_MM": TREAD_PITCH_MIN_MM,
        "TREAD_PITCH_MAX_MM": TREAD_PITCH_MAX_MM,
        "MIN_TREADS": MIN_TREADS,
        "MIN_TREAD_WIDTH_MM": MIN_TREAD_WIDTH_MM,
        "PITCH_TOL_MM": PITCH_TOL_MM,
        "ANGLE_PITCH_MIN_DEG": ANGLE_PITCH_MIN_DEG,
        "ANGLE_PITCH_MAX_DEG": ANGLE_PITCH_MAX_DEG,
        "RADIAL_CENTRE_TOL_MM": RADIAL_CENTRE_TOL_MM,
        "SCOPE": SCOPE,
        "why": {"never_silently_absent": NEVER_SILENTLY_ABSENT,
                "no_riser_without_a_section": NO_RISER_WITHOUT_A_SECTION},
    }
