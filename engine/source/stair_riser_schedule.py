"""STAIR RISER SCHEDULE - riser counts from drawn lines, uniform finished risers, finished and structural levels,
first / last concrete risers (generic).

Nothing here chooses a riser count, a level or a finish. Every function takes what it is given and says what follows;
whether each input has authority is the caller's record.

Counting
    pair_lines(lines, pair_tol=60.0)
        drawn lines -> risers. lines: (offset_mm, line_id) along the walking direction. Lines closer than pair_tol
        are ONE riser: a visible nosing and the hidden riser face behind it, or the same riser drawn twice. Returns
        [(mean_offset, [ids])] sorted by offset.
    pitches(positions)
        the goings between consecutive risers (a drawing fact: irregular goings are reported, not corrected).

Uniform finished risers
    uniform_riser(rise_mm, n)            rise / n.
    counts_in_range(rise_mm, lo, hi)     every whole count whose uniform riser lies in [lo, hi].
    schedule(ffl_bottom_m, ffl_top_m, segments, finishes=None)
        segments: [(segment_id, kind, n_risers)] in walking order; kind FLIGHT, WINDERS or LANDING (0 risers).
        The finished riser h = rise / (sum of risers) is uniform. For every riser: its index, segment, the finished
        level of the tread or landing it rises onto, the concrete level beneath it, and the finished and concrete
        riser heights. finishes = {"floor_bottom": f_b, "floor_top": f_t, "tread": s, "landing": s_l} in mm:
          f_b, f_t  finished floor level - structural slab level at the bottom / top floor
          s         stair finish on a tread (finish + bedding)
          s_l       finish on an intermediate landing (defaults to s)
        A missing finish leaves every concrete value that depends on it as None.
    first_last(h, f_b, f_t, s)
        the closed form: first concrete riser = h + f_b - s, last = h - f_t + s, every other riser = h (when the
        landings carry the tread finish). The concrete risers always sum to rise - f_t + f_b.
    offsets_for(h, first, last, s)
        the floor build-ups that a stated first / last concrete riser would require: f_b = first - h + s,
        f_t = h + s - last. A stated pair is only consistent with the drawings if these build-ups are.

Volumes and bars
    winder_plane_volume(plan_area_m2, riser_mm, going_mm, waist_mm)
        A x (t / cos(pitch) + h / 2) (m3): the volume of a winder turn whose soffit follows the walking-line pitch,
        the same expression a straight flight between plumb cuts gives exactly. For winders it is an approximation
        and is labelled so by the caller.
    bar_length_rate(rate_per_m, width_mm, length_mm)
        rate x width x length (m): the equivalent length of an n / m bar rate over a width, each bar length long.

Stdlib only. No project data.
"""

from __future__ import annotations

import math

TOL = 1e-9
FLIGHT, WINDERS, LANDING = "FLIGHT", "WINDERS", "LANDING"


class RiserScheduleError(ValueError):
    pass


def pair_lines(lines, pair_tol=60.0):
    if pair_tol < 0:
        raise RiserScheduleError("pair tolerance must not be negative")
    out = []
    for off, lid in sorted(lines, key=lambda x: (x[0], str(x[1]))):
        if out and off - out[-1][2] <= pair_tol + TOL:
            out[-1][1].append(lid)
            out[-1][2] = off
            out[-1][3].append(off)
        else:
            out.append([off, [lid], off, [off]])
    return [(sum(g[3]) / len(g[3]), g[1]) for g in out]


def pitches(positions):
    p = sorted(positions)
    return [b - a for a, b in zip(p, p[1:])]


def uniform_riser(rise_mm, n):
    if n < 1 or int(n) != n:
        raise RiserScheduleError("risers must be a whole number")
    if rise_mm <= 0:
        raise RiserScheduleError("rise must be positive")
    return rise_mm / n


def counts_in_range(rise_mm, lo, hi):
    if not 0 < lo <= hi:
        raise RiserScheduleError("riser range must be positive and ordered")
    return [n for n in range(int(math.ceil(rise_mm / hi - TOL)), int(math.floor(rise_mm / lo + TOL)) + 1)
            if lo - TOL <= rise_mm / n <= hi + TOL]


def first_last(h, f_b, f_t, s):
    if None in (h, f_b, f_t, s):
        return None, None
    return h + f_b - s, h - f_t + s


def offsets_for(h, first, last, s):
    return first - h + s, h + s - last


def schedule(ffl_bottom_m, ffl_top_m, segments, finishes=None):
    segs = list(segments)
    if not segs:
        raise RiserScheduleError("no segments")
    for sid, kind, n in segs:
        if kind not in (FLIGHT, WINDERS, LANDING):
            raise RiserScheduleError(f"unknown segment kind {kind!r}")
        if int(n) != n or n < 0 or (kind == LANDING and n != 0) or (kind != LANDING and n < 1):
            raise RiserScheduleError(f"segment {sid}: a landing has no riser, a flight or a turn at least one")
    total = sum(n for _, _, n in segs)
    rise = (ffl_top_m - ffl_bottom_m) * 1000.0
    h = uniform_riser(rise, total)
    f = dict(finishes or {})
    f_b, f_t, s = f.get("floor_bottom"), f.get("floor_top"), f.get("tread")
    s_l = f.get("landing", s)
    rows, landings = [], []
    k = 0
    prev_conc = None if f_b is None else ffl_bottom_m * 1000.0 - f_b
    for i, (sid, kind, n) in enumerate(segs):
        if kind == LANDING:
            fin = ffl_bottom_m * 1000.0 + k * h
            landings.append({"segment": sid, "after_riser": k, "finished_mm": fin,
                             "concrete_mm": None if s_l is None else fin - s_l})
            continue
        before_landing = i + 1 < len(segs) and segs[i + 1][1] == LANDING
        for j in range(int(n)):
            k += 1
            fin = ffl_bottom_m * 1000.0 + k * h
            if k == total:
                onto, fin_off = "TOP_FLOOR", f_t
            elif j == n - 1 and before_landing:
                onto, fin_off = "LANDING", s_l
            else:
                onto, fin_off = "TREAD", s
            conc = None if fin_off is None else fin - fin_off
            rows.append({"riser": k, "segment": sid, "kind": kind, "onto": onto, "finished_mm": fin,
                         "finished_riser_mm": h, "concrete_mm": conc,
                         "concrete_riser_mm": None if (conc is None or prev_conc is None) else conc - prev_conc})
            prev_conc = conc
    return {"n": total, "riser_mm": h, "rise_mm": rise, "rows": rows, "landings": landings}


def winder_plane_volume(plan_area_m2, riser_mm, going_mm, waist_mm):
    for v, nm in ((plan_area_m2, "plan area"), (riser_mm, "riser"), (going_mm, "going"), (waist_mm, "waist")):
        if v is None or v <= 0:
            raise RiserScheduleError(f"{nm} must be positive")
    cos = going_mm / math.hypot(going_mm, riser_mm)
    return plan_area_m2 * (waist_mm / cos + riser_mm / 2.0) / 1000.0


def bar_length_rate(rate_per_m, width_mm, length_mm):
    if rate_per_m <= 0 or width_mm < 0 or length_mm < 0:
        raise RiserScheduleError("rate positive, width and length not negative")
    return rate_per_m * width_mm / 1000.0 * length_mm / 1000.0
