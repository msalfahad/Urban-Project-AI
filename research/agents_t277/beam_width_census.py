"""BEAM_WIDTH_CENSUS_V1 (T-277, unwired, stdlib only; rollback: delete the folder).

Drawn-vs-scheduled beam width census over the roof-slab plans of a structural set (any villa).

Physical element (ERS s.2.1): a beam's plan width b is ONE physical dimension that two documents of the same set state
independently: the slab plan draws it (the distance between the member's two drawn edge lines, measured normal to the
member axis, or the difference of the radii of two concentric drawn arcs for a curved member) and the beam schedule
prints it (the 'W' / 'B-(Bredth)' column, in cm). Where the two disagree the width is a CONFLICT for the designer
(owner Q-61 C(1): never the schedule only because it is printed, never the larger, never the drawn by habit either).
The census decides nothing; it finds every instance and states what each reading means for each trade.

Notation before arithmetic (ERS s.3): the schedule W is a number in cm (header 'B-(Bredth)' / attribute 'W'): it is
converted once, with the unit stated; a value that only makes sense in another unit (W 20 read as 20 m, or 0.20 read
as cm) is refused, never coerced.

Rules (proposed, this task):
R-BEAM-WIDTH-CENSUS-1  Every labelled band of every slab plan is compared. The label binds to its band by geometry
    only (bind_label; the schedule takes no part): its direction (within 2 deg) finds the edges crossing its normal;
    INSIDE = the label is centred on a band (centre within 30 mm of its axis, text box inside both edges; a line of
    another layer class inside the span does not split the member); otherwise BESIDE = the nearest band from the text
    box edge, a gap that holds the label uncentred being the panel strip between two members; a label outside the
    slab with a strip between it and an edge beam, or two bands within 50 mm clear, has two readings. The drawn width
    is the normal distance between two edges parallel to EACH OTHER within 0.5 deg (a band whose edges are not
    parallel has no single drawn width: NON_PARALLEL), or the difference of two concentric radii. Classes over all
    readings (classify_readings): AGREE (every reading within 2 mm of the schedule W), CONFLICT (none), AMBIGUOUS
    (they split), NO_SCHEDULE, NO_BAND, NON_PARALLEL; two labels of different marks on one band are flagged
    (clash_check).
R-BEAM-WIDTH-CONSEQ-1  A CONFLICT carries BOTH readings in every trade it moves, kept apart per trade, never resolved:
    CONC.BEAM m3 = b x D x L at each reading; FORMWORK beam soffit m2 = b x L at each reading (beam sides (D - t) x L
    per side do not depend on b); slab soffit / slab concrete = the complementary change (- delta_b x L, x t for m3)
    when the moving face borders a slab panel, 0 when it is a free edge: stated as the range 0 .. - delta_b x L because
    which face would move is itself the designer's answer; BLOCKWORK m2 of a wall crossing under the band = the strip
    of wall length delta_b x (D - t) changes height (under the beam soffit vs under the slab soffit); a wall running
    along the band is unaffected only if it lies inside the narrower width (otherwise up to piece length x (D - t)),
    which a census without the wall overlay states as a bound, never as 0.
"""
from __future__ import annotations

import math

SCHEMA = "BEAM_WIDTH_CENSUS_V1"
RULES = ("R-BEAM-WIDTH-CENSUS-1", "R-BEAM-WIDTH-CONSEQ-1")
UNIT_TO_M = {"m": 1.0, "cm": 0.01, "mm": 0.001}
PARALLEL_TOL_DEG = 0.5     # two edge lines are parallel to EACH OTHER within 0.5 deg (drafting precision; T-252)
LABEL_ALIGN_DEG = 2.0      # a label is written along its band within 2 deg (it finds the edges; it never sets width)
NEAR_PARALLEL_DEG = 10.0   # a line 2 .. 10 deg off the label direction crossing the label normal: NON_PARALLEL edge
MERGE_TOL_M = 0.001        # two collinear edge lines within 1 mm are one drawn edge (layers drawn on top of each other)
AGREE_TOL_M = 0.002        # drawn = schedule within 2 mm (far below the 50 mm module of beam widths)
BAND_MIN_M = 0.08          # narrowest member band considered (0.10 strips exist on Alsenan)
BAND_MAX_M = 1.20          # widest (B27 0.90 on Alsenan); a wider gap is a slab panel, not a member band
SEARCH_M = 1.50            # a label binds to a band at most 1.50 m away on its normal
AMBIG_M = 0.05             # two bands whose clear distances to the label differ by less than 50 mm: AMBIGUOUS
OUTSIDE_SEARCH_M = 100.0   # "outside the slab": no parallel member edge on the label's side anywhere on the sheet
TEXT_HALF_H_M = 0.15       # half the label height (0.30 m on the Alsenan slab plans; passed per label when known)
CENTRED_TOL_M = 0.03       # a label inside a band is centred on it within 30 mm (Alsenan: inside 0.001 .. 0.018,
                           # a label in a gap without being centred 0.066 .. 0.367; see the report s.2)
W_SCHED_RANGE_M = (0.05, 2.00)
CLASSES = ("AGREE", "CONFLICT", "NO_SCHEDULE", "NO_BAND", "AMBIGUOUS", "NON_PARALLEL")


class Refused(ValueError):
    """A request the rules refuse (the message names the rule)."""


# ------------------------------------------------------------------------------------------------- schedule width
def schedule_width_m(value, unit):
    """Schedule W with its unit stated -> metres. A unit is never guessed; a result outside 0.05 .. 2.00 m means the
    unit was misread (W 20 taken as m, 0.20 taken as cm) and is refused."""
    if unit not in UNIT_TO_M:
        raise Refused("UNIT_UNKNOWN: %r (the schedule unit must be stated)" % (unit,))
    if value is None or str(value).strip() == "":
        return None
    try:
        v = float(str(value).strip())
    except ValueError:
        raise Refused("SCHEDULE_W_NOT_A_NUMBER: %r" % (value,))
    w = v * UNIT_TO_M[unit]
    if not (W_SCHED_RANGE_M[0] <= w <= W_SCHED_RANGE_M[1]):
        raise Refused("SCHEDULE_W_UNIT_MISREAD: %r %s = %.4f m is not a beam width" % (value, unit, w))
    return w


def schedule_table(rows):
    """rows: [(mark, W, H, unit, source_handle)] -> {mark: dict(w_m, d_m, handles, conflict)}; a mark printed twice
    with different sizes is a SCHEDULE_DUPLICATE conflict kept with both rows (never the first, never the larger)."""
    out = {}
    for mark, w, h, unit, src in rows:
        rec = dict(w_m=schedule_width_m(w, unit), d_m=schedule_width_m(h, unit) if h not in (None, "") else None,
                   handles=[src], sizes=[(w, h)])
        if mark in out:
            o = out[mark]
            o["handles"].append(src)
            o["sizes"].append((w, h))
            if (o["w_m"], o["d_m"]) != (rec["w_m"], rec["d_m"]):
                o["duplicate_conflict"] = True
        else:
            rec["duplicate_conflict"] = False
            out[mark] = rec
    return out


# --------------------------------------------------------------------------------------------------- band finding
def _unit(deg):
    a = math.radians(deg)
    return (math.cos(a), math.sin(a))


def _angle_between(u, d):
    """acute angle in degrees between two directions (lines are undirected)."""
    c = abs(u[0] * d[0] + u[1] * d[1]) / (math.hypot(*u) * math.hypot(*d))
    return math.degrees(math.acos(min(1.0, c)))


def edges_at_station(c, deg, lines, arcs=(), search=None):
    """Drawn edges crossing the normal through station c of a label with direction `deg`.

    lines: [(handle, (x1, y1), (x2, y2))] in m; arcs: [(handle, (cx, cy), R, a0_deg, a1_deg)] (ccw sweep a0 -> a1).
    Returns (parallel, skew): parallel = [(offset_m, handle, kind)] sorted by offset along the normal (straight edges
    parallel within PARALLEL_TOL_DEG whose extent contains the station; concentric arcs whose sweep contains the
    station's angle and whose tangent there is parallel to the label), skew = [(handle, angle_deg)] for lines 0.5 .. 10
    deg off the label direction that cross the normal within SEARCH_M (a band edge that is not parallel)."""
    u = _unit(deg)
    n = (-u[1], u[0])
    lim = SEARCH_M if search is None else search
    par, skew = [], []
    for ln in lines:
        h, p, q = ln[0], ln[1], ln[2]
        lay = ln[3] if len(ln) > 3 else None
        d = (q[0] - p[0], q[1] - p[1])
        if math.hypot(*d) < 1e-6:
            continue
        ang = _angle_between(u, d)
        sang = math.degrees(math.atan2(u[0] * d[1] - u[1] * d[0], u[0] * d[0] + u[1] * d[1]))
        sang = (sang + 90.0) % 180.0 - 90.0              # signed angle to the label, folded to [-90, 90)
        s1 = (p[0] - c[0]) * u[0] + (p[1] - c[1]) * u[1]
        s2 = (q[0] - c[0]) * u[0] + (q[1] - c[1]) * u[1]
        o1 = (p[0] - c[0]) * n[0] + (p[1] - c[1]) * n[1]
        o2 = (q[0] - c[0]) * n[0] + (q[1] - c[1]) * n[1]
        if ang <= LABEL_ALIGN_DEG:
            if min(s1, s2) <= 0.0 <= max(s1, s2) and abs((o1 + o2) / 2.0) <= lim:
                # offset on the label normal at the station (interpolated: the line may be up to 2 deg off the label)
                t = 0.0 if s2 == s1 else (0.0 - s1) / (s2 - s1)
                par.append((o1 + t * (o2 - o1), h, "line", lay, sang))
        elif ang <= NEAR_PARALLEL_DEG:          # 2 .. 10 deg: a crossing line that is nearly a band edge
            if min(s1, s2) <= 0.0 <= max(s1, s2):
                t = (0.0 - s1) / (s2 - s1)
                o = o1 + t * (o2 - o1)
                if abs(o) <= lim:
                    skew.append((h, round(ang, 3), o))
    for ar in arcs:
        h, cc, R, a0, a1 = ar[:5]
        lay = ar[5] if len(ar) > 5 else None
        vx, vy = c[0] - cc[0], c[1] - cc[1]
        r = math.hypot(vx, vy)
        if r < 1e-6:
            continue
        a = math.degrees(math.atan2(vy, vx)) % 360.0
        sweep = (a1 - a0) % 360.0
        if (a - a0) % 360.0 > sweep:
            continue
        tangent = (-vy / r, vx / r)
        if _angle_between(u, tangent) > NEAR_PARALLEL_DEG:
            continue
        o_rad = R - r                            # + outward from the label along the radius
        if abs(o_rad) > lim:
            continue
        # express on the label normal: sign of the radial direction projected on n
        sgn = 1.0 if (vx * n[0] + vy * n[1]) >= 0 else -1.0
        par.append((sgn * o_rad, h, "arc", lay, 0.0))
    par.sort(key=lambda x: (x[0], x[1]))
    merged = []
    for o, h, k, lay, sa in par:
        if merged and abs(o - merged[-1][0]) <= MERGE_TOL_M and abs(sa - merged[-1][4]) <= PARALLEL_TOL_DEG:
            merged[-1][1].append(h)
            merged[-1][3].add(lay)
            if k == "arc":
                merged[-1][2] = "arc"
            continue
        merged.append([o, [h], k, {lay}, sa])
    return [(round(o, 6), hs, k, frozenset(ls), round(sa, 4)) for o, hs, k, ls, sa in merged], skew


def _dist(band, hh=0.0):
    """clear distance from the label's text box (half-height hh on the normal) to the band; 0 if they touch."""
    lo, hi = band[0], band[1]
    if lo <= 0.0 <= hi:
        return 0.0
    return max(0.0, min(abs(lo), abs(hi)) - hh)


def bind_label(c, deg, lines, arcs=(), hh=TEXT_HALF_H_M):
    """The band(s) a label can name, by geometry only (no schedule value takes part). Returns dict(status, readings,
    placement, skew, dist_m); readings = [(lo, hi, width, handles_lo, handles_hi, kind, interior_handles)].

    Drafting convention read off the set (R-BEAM-WIDTH-CENSUS-1):
    INSIDE  a label written inside a member band is centred on it: its centre within CENTRED_TOL_M of the band axis,
            its text box inside both edges. The band is the span between two drawn edges; a drawn line INSIDE it (a
            hidden upstand / drop line) does not split the member (flagged as interior, read on the section).
    BESIDE  any other label is written beside its band, in the panel next to it, and names the nearest band from its
            text box edge. A gap that contains the label without it being centred is the panel strip between two
            members, never its band. Where the nearest band is a strip with another band stacked right behind it
            (sharing its far edge) AND the label stands outside the outermost drawn edge on its own side (outside
            the slab: projection strips between the label and the edge beam), the label can name either: both are
            readings. A second band on the other side within AMBIG_M is a reading too.
    A line of the same layer class as the edges inside an INSIDE span means two members, not one band.
    The status of the width is then decided over ALL readings (classify_readings): one reading is never preferred."""
    edges, skew = edges_at_station(c, deg, lines, arcs)
    if len(edges) < 2:
        return dict(status="NON_PARALLEL" if skew else "NO_BAND", readings=[], placement=None, skew=skew)

    def span(i, j):
        lo, hi = edges[i][0], edges[j][0]
        kind = "arc" if "arc" in (edges[i][2], edges[j][2]) else "line"
        inner = [h for k in range(i + 1, j) for h in edges[k][1]]
        ai, aj = edges[i][4], edges[j][4]
        if abs(ai - aj) > PARALLEL_TOL_DEG:
            return (lo, hi, None, edges[i][1], edges[j][1], "nonparallel", inner)
        # normal distance between the two parallel edges (the label may be up to 2 deg off them)
        w = (hi - lo) * math.cos(math.radians((ai + aj) / 2.0))
        return (lo, hi, round(w, 6), edges[i][1], edges[j][1], kind, inner)

    def skewed(lo, hi):
        return any(lo - 0.05 <= s_[2] <= hi + 0.05 for s_ in skew)

    inside = []
    for i in range(len(edges)):
        for j in range(i + 1, min(i + 4, len(edges))):
            lo, hi = edges[i][0], edges[j][0]
            if hi - lo > BAND_MAX_M + 1e-9:
                break
            if (hi - lo >= BAND_MIN_M - 1e-9 and lo <= -hh and hi >= hh
                    and abs((lo + hi) / 2.0) <= CENTRED_TOL_M):
                inner_layers = set().union(*[edges[k][3] for k in range(i + 1, j)]) if j > i + 1 else set()
                if inner_layers & (edges[i][3] | edges[j][3]):
                    continue          # a line of the edges' own class inside: two members, not one band
                inside.append(span(i, j))
    if inside:
        if any(r[2] is None for r in inside) or skewed(min(r[0] for r in inside), max(r[1] for r in inside)):
            return dict(status="NON_PARALLEL", readings=inside, placement="INSIDE", skew=skew)
        return dict(status="BOUND", readings=inside, placement="INSIDE", skew=skew, dist_m=0.0)
    bands = [span(i, i + 1) for i in range(len(edges) - 1)
             if BAND_MIN_M - 1e-9 <= edges[i + 1][0] - edges[i][0] <= BAND_MAX_M + 1e-9]
    beside = [b for b in bands if not (b[0] < 0.0 < b[1] and b[0] < -hh and b[1] > hh)]
    if not beside:
        return dict(status="NON_PARALLEL" if skew else "NO_BAND", readings=[], placement=None, skew=skew)
    ranked = sorted(beside, key=lambda b: _dist(b, hh))
    best = ranked[0]
    readings = [best]
    placement = "BESIDE"
    for b in ranked[1:]:
        if abs(_dist(b, hh) - _dist(best, hh)) < AMBIG_M:
            readings.append(b)
            placement = "BESIDE_TIE"
    far = best[1] if best[0] >= 0.0 else best[0]          # the edge of the best band away from the label
    # outside: on the label's own side the normal meets NO parallel edge of the members' own line class (the layers
    # of the best band's edges) anywhere on the sheet; a boundary / plot line of another class does not count
    far_edges, _sk = edges_at_station(c, deg, lines, arcs, search=OUTSIDE_SEARCH_M)
    cls = set(best_layers(best, edges))
    outside = not any(((e[0] < -hh) if best[0] >= 0.0 else (e[0] > hh)) and (e[3] & cls) for e in far_edges)
    for b in (bands if outside else []):
        if b is not best and b not in readings and (abs(b[0] - far) <= MERGE_TOL_M or abs(b[1] - far) <= MERGE_TOL_M) \
                and (b[0] >= best[1] - MERGE_TOL_M if best[0] >= 0.0 else b[1] <= best[0] + MERGE_TOL_M):
            readings.append(b)
            placement = "BESIDE_STACKED" if placement == "BESIDE" else placement + "+STACKED"
    if any(r[2] is None for r in readings) or \
            skewed(min(min(r[0] for r in readings), 0.0), max(max(r[1] for r in readings), 0.0)):
        return dict(status="NON_PARALLEL", readings=readings, placement=placement, skew=skew)
    return dict(status="BOUND", readings=readings, placement=placement, skew=skew, dist_m=round(_dist(best, hh), 6))


def best_layers(band, edges):
    """layer classes of a band's two edges (looked up by handle in the station's edge list)."""
    hs = set(band[3]) | set(band[4])
    out = set()
    for e in edges:
        if hs & set(e[1]):
            out |= set(e[3])
    return out


def classify_readings(widths, sched_w):
    """All drawn readings of one label against its schedule W: AGREE only when EVERY reading agrees, CONFLICT when
    none does, AMBIGUOUS when they split (the binding, not the width, is then the open question)."""
    if sched_w is None:
        return "NO_SCHEDULE"
    if not widths:
        raise Refused("NO_DRAWN_WIDTH: classify only a bound label")
    ok = [abs(w - sched_w) <= AGREE_TOL_M for w in widths]
    return "AGREE" if all(ok) else ("CONFLICT" if not any(ok) else "AMBIGUOUS")


def clash_check(bindings):
    """bindings: [(label_id, mark, band_key)]; a band claimed by labels of two different marks -> those labels are
    AMBIGUOUS (a label on the wrong band). Returns the set of label ids to downgrade."""
    by = {}
    for lid, mark, key in bindings:
        if key is None:
            continue
        by.setdefault(key, []).append((lid, mark))
    bad = set()
    for key, v in by.items():
        if len({m for _l, m in v}) > 1:
            bad.update(l for l, _m in v)
    return bad


# ------------------------------------------------------------------------------------------------ classification
def classify(drawn_w, sched_w):
    if sched_w is None:
        return "NO_SCHEDULE"
    if drawn_w is None:
        raise Refused("NO_DRAWN_WIDTH: classify only a bound band")
    return "AGREE" if abs(drawn_w - sched_w) <= AGREE_TOL_M else "CONFLICT"


def governing_width(status, drawn_w, sched_w, pick=None):
    """The width a quantity may be computed on. AGREE -> the one width. CONFLICT -> refused whatever is asked:
    'larger', 'smaller', 'schedule' and 'drawn' are each a choice the designer has not made (Q-61 C(1))."""
    if status == "AGREE":
        return drawn_w
    if status == "CONFLICT":
        raise Refused("WIDTH_CONFLICT_NOT_RESOLVED_BY_CHOICE: %r refused (drawn %.3f / schedule %.3f): designer item"
                      % (pick, drawn_w, sched_w))
    raise Refused("NO_WIDTH: status %s" % status)


# -------------------------------------------------------------------------------------------------- consequences
def consequence(L, D, t, w_drawn, w_sched, wall_pieces=()):
    """Per-trade readings of one CONFLICT run (both readings, never resolved).

    L run length (m, between supporting faces), D beam depth (m, schedule / section), t thickness of the slab beside
    it (m). wall_pieces: [(wall_id, piece_length_m, kind)] with kind 'crossing' or 'along'.
    Returns a dict of (at_drawn, at_schedule) pairs and ranges, all in m3 / m2."""
    for v, nm in ((L, "L"), (D, "D"), (t, "t"), (w_drawn, "w_drawn"), (w_sched, "w_sched")):
        if v is None:
            raise Refused("MISSING_%s: no consequence on a missing dimension (never 0)" % nm)
    if not (0 < t < D):
        raise Refused("SLAB_T_NOT_BELOW_D: t %.3f vs D %.3f" % (t, D))
    dw = w_drawn - w_sched
    out = dict(
        delta_b_m=round(dw, 6),
        conc_beam_m3=(round(w_drawn * D * L, 6), round(w_sched * D * L, 6)),
        fw_beam_soffit_m2=(round(w_drawn * L, 6), round(w_sched * L, 6)),
        fw_beam_sides_m2=round(2 * (D - t) * L, 6),            # unchanged by b (interior beam, slab both sides)
        slab_soffit_delta_m2=(0.0, round(dw * L, 6)),          # schedule reading vs drawn: + dw L of slab soffit if
        slab_conc_delta_m3=(0.0, round(dw * L * t, 6)),         # the moving face borders a panel, 0 if a free edge
        blockwork=[],
    )
    for wid, plen, kind in wall_pieces:
        if kind == "crossing":
            out["blockwork"].append(dict(wall=wid, kind=kind, strip_m=round(abs(dw), 6),
                                         m2_range=(0.0, round(abs(dw) * (D - t), 6)) if abs(dw) > 0 else (0.0, 0.0),
                                         note="strip under the band at one reading, under the slab at the other"))
        elif kind == "along":
            out["blockwork"].append(dict(wall=wid, kind=kind, piece_m=plen,
                                         m2_range=(0.0, round(plen * (D - t), 6)),
                                         note="0 if the wall lies inside the narrower width; wall overlay not "
                                              "checked by the census: bound only"))
        else:
            raise Refused("WALL_KIND_UNKNOWN: %r" % (kind,))
    return out
