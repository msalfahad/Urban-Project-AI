"""LINTEL QTO - schedule binding, lintel geometry, bar lengths and counts for masonry-wall lintels (generic).

A lintel schedule states, per band of OPENING WIDTH, a section (B x D, B = wall width) and its bars. This module binds
an opening to exactly one band, builds the lintel's extent from the opening and its supports, and measures straight
bar lengths and stirrup counts. It never invents what a schedule leaves out: bends, hooks, anchorages and laps are
returned as BLOCKED roles, never as lengths.

Schedule
  parse_width_range(text)       '0 -100' / '101 - 200' -> (lo, hi) in the printed unit (closed integer bounds)
  parse_section(text)           'B x 20' -> ('B', 20): the width is the wall's, the depth is printed
  parse_bars(text)              '2Ø12' -> (2, 12); parse_rate(text) '5Ø8/M' -> (5, 8) bars per metre
  check_schedule(rows)          bands in order, never overlapping; the uncovered intervals between bands and the
                                bound above the last band are returned (they are source gaps, never filled)
  row_for_width(rows, w)        IN_ROW (one band holds w, bounds inclusive) / BOUNDARY_GAP (w lies strictly between
                                two bands) / ABOVE_SCHEDULE / NOT_POSITIVE. No rounding moves w into a band.

Geometry (mm, along the wall)
  lintel_extent(s0, s1, start, end, min_bearing, available_start, available_end)
                                start / end: MASONRY (bears on the wall beyond the jamb) or FRAME (abuts a column
                                face: no masonry bearing). The bearing on a masonry side is min(min_bearing,
                                available); a side where less than min_bearing is available is a BEARING_DEFICIT.
  resolve_overlaps(lintels)     lintels on one wall line whose extents overlap are cut at the middle of the pier
                                between their openings (concrete is never counted twice); each cut is reported.
  strip_relation(strip, band)   how a beam band lies over an opening strip: lateral share of the wall thickness and
                                longitudinal share of the opening width -> FULL / PARTIAL / NONE.

Bars
  straight_bar_mm(L, cover)     L - 2 cover (end bends excluded)
  stirrup_core_path_mm(B, D, cover, d)
                                2 (B - 2c - d) + 2 (D - 2c - d): the bar centreline of a closed stirrup with sharp
                                corners (hooks excluded)
  rate_count(rate_per_m, L)     ceil(rate x L / 1000): a '/M' count is a rate per metre over the length
  spacing_count(L, rate_per_m)  ceil(L / (1000 / rate)) + 1: the alternative count with a closing stirrup
                                (sensitivity only)

Stdlib only. No project data.
"""

from __future__ import annotations

import math
import re

TOL = 1e-9
IN_ROW, BOUNDARY_GAP, ABOVE_SCHEDULE, NOT_POSITIVE = "IN_ROW", "BOUNDARY_GAP", "ABOVE_SCHEDULE", "NOT_POSITIVE"
MASONRY, FRAME = "MASONRY", "FRAME"
FULL, PARTIAL, NONE = "FULL", "PARTIAL", "NONE"
BEARING_DEFICIT = "BEARING_DEFICIT"

_RANGE = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")
_SECTION = re.compile(r"^\s*([A-Za-z])\s*[xX×]\s*(\d+(?:\.\d+)?)\s*$")
_BARS = re.compile(r"^\s*(\d+)\s*[Ø∅ΦφT]\s*(\d+)\s*$")
_RATE = re.compile(r"^\s*(\d+)\s*[Ø∅ΦφT]\s*(\d+)\s*/\s*[Mm]\s*$")


class LintelQtoError(ValueError):
    pass


# ------------------------------------------------------------------ schedule
def parse_width_range(text):
    m = _RANGE.match(text or "")
    if not m:
        raise LintelQtoError(f"not a width range: {text!r}")
    lo, hi = int(m.group(1)), int(m.group(2))
    if hi <= lo:
        raise LintelQtoError(f"empty width range: {text!r}")
    return lo, hi


def parse_section(text):
    m = _SECTION.match(text or "")
    if not m:
        raise LintelQtoError(f"not a section: {text!r}")
    return m.group(1).upper(), float(m.group(2))


def parse_bars(text):
    m = _BARS.match(text or "")
    if not m or int(m.group(1)) <= 0:
        raise LintelQtoError(f"not a bar count: {text!r}")
    return int(m.group(1)), int(m.group(2))


def parse_rate(text):
    m = _RATE.match(text or "")
    if not m or int(m.group(1)) <= 0:
        raise LintelQtoError(f"not a rate per metre: {text!r}")
    return int(m.group(1)), int(m.group(2))


def check_schedule(rows):
    """rows: [{'row_id', 'lo', 'hi', ...}] in the printed unit. Returns {'gaps': [(hi_a, lo_b, row_a, row_b)],
    'above': hi_last}; raises when bands are out of order or overlap."""
    if not rows:
        raise LintelQtoError("empty schedule")
    gaps = []
    for a, b in zip(rows, rows[1:]):
        if not a["lo"] < a["hi"] or not b["lo"] < b["hi"]:
            raise LintelQtoError("band bounds out of order")
        if b["lo"] <= a["hi"]:
            raise LintelQtoError(f"bands {a['row_id']} and {b['row_id']} overlap")
        if b["lo"] > a["hi"]:
            gaps.append((a["hi"], b["lo"], a["row_id"], b["row_id"]))
    return {"gaps": gaps, "above": rows[-1]["hi"], "below": rows[0]["lo"]}


def row_for_width(rows, width, unit_per_mm=0.1):
    """width in mm; bands in the printed unit (cm: unit_per_mm 0.1). Bounds are inclusive."""
    if width is None or width <= 0:
        return NOT_POSITIVE, None
    w = width * unit_per_mm
    for r in rows:
        if r["lo"] - TOL <= w <= r["hi"] + TOL:
            return IN_ROW, r
    if w > rows[-1]["hi"] + TOL:
        return ABOVE_SCHEDULE, None
    if w < rows[0]["lo"] - TOL:
        return NOT_POSITIVE, None
    for a, b in zip(rows, rows[1:]):
        if a["hi"] < w < b["lo"]:
            return BOUNDARY_GAP, (a, b)
    raise LintelQtoError("width not placed")  # unreachable for checked schedules


# ------------------------------------------------------------------ geometry
def lintel_extent(s0, s1, start, end, min_bearing, available_start=None, available_end=None):
    """the lintel over the opening [s0, s1]: {'t0', 't1', 'length', 'bearing_start', 'bearing_end', 'flags'}."""
    if s1 <= s0:
        raise LintelQtoError("opening has no width")
    if min_bearing <= 0:
        raise LintelQtoError("min bearing must be positive")
    flags, b = [], {}
    for side, kind, avail in (("start", start, available_start), ("end", end, available_end)):
        if kind == FRAME:
            b[side] = 0.0
        elif kind == MASONRY:
            if avail is None:
                raise LintelQtoError("available masonry bearing required")
            b[side] = min(min_bearing, max(avail, 0.0))
            if avail < min_bearing - TOL:
                flags.append(f"{BEARING_DEFICIT}:{side}")
        else:
            raise LintelQtoError(f"unknown support kind {kind!r}")
    t0, t1 = s0 - b["start"], s1 + b["end"]
    return {"t0": t0, "t1": t1, "length": t1 - t0, "bearing_start": b["start"], "bearing_end": b["end"],
            "flags": flags}


def resolve_overlaps(lintels):
    """lintels: [{'id', 'line', 's0', 's1', 't0', 't1'}] (s = opening, t = lintel extent). Lintels on one line whose
    extents overlap are cut at the middle of the pier between their openings. Returns (new extents by id, cuts)."""
    out = {x["id"]: {"t0": x["t0"], "t1": x["t1"]} for x in lintels}
    cuts = []
    by_line = {}
    for x in lintels:
        by_line.setdefault(x["line"], []).append(x)
    for line in sorted(by_line):
        xs = sorted(by_line[line], key=lambda x: (x["s0"], x["id"]))
        for a, b in zip(xs, xs[1:]):
            if b["s0"] < a["s1"] - TOL:
                raise LintelQtoError(f"openings {a['id']} and {b['id']} overlap")
            if out[a["id"]]["t1"] > out[b["id"]]["t0"] + TOL:
                mid = (a["s1"] + b["s0"]) / 2.0
                out[a["id"]]["t1"] = min(out[a["id"]]["t1"], mid)
                out[b["id"]]["t0"] = max(out[b["id"]]["t0"], mid)
                cuts.append({"line": line, "a": a["id"], "b": b["id"], "pier": b["s0"] - a["s1"], "cut_at": mid})
    for k, v in out.items():
        v["length"] = v["t1"] - v["t0"]
    return out, cuts


def strip_relation(strip, band, lateral_full=0.5, along_full=0.999):
    """strip: {'s0', 's1', 'o0', 'o1'} in a frame (u, n); band: {'s0', 's1', 'o0', 'o1'} in the same frame.
    lateral = share of the strip thickness the band covers; along = share of [s0, s1] it covers."""
    t = strip["o1"] - strip["o0"]
    w = strip["s1"] - strip["s0"]
    if t <= 0 or w <= 0:
        raise LintelQtoError("strip has no extent")
    lat = max(0.0, min(strip["o1"], band["o1"]) - max(strip["o0"], band["o0"])) / t
    alo = max(0.0, min(strip["s1"], band["s1"]) - max(strip["s0"], band["s0"])) / w
    if lat <= TOL or alo <= TOL:
        rel = NONE
    elif lat >= lateral_full - TOL and alo >= along_full - TOL:
        rel = FULL
    else:
        rel = PARTIAL
    return {"relation": rel, "lateral_share": lat, "along_share": alo}


# ------------------------------------------------------------------ bars
def straight_bar_mm(length, cover):
    v = length - 2.0 * cover
    if v <= 0:
        raise LintelQtoError("bar length not positive")
    return v


def stirrup_core_path_mm(B, D, cover, d):
    a, b = B - 2.0 * cover - d, D - 2.0 * cover - d
    if a <= 0 or b <= 0:
        raise LintelQtoError("stirrup does not fit the section")
    return 2.0 * a + 2.0 * b


def rate_count(rate_per_m, length):
    if rate_per_m <= 0 or length <= 0:
        raise LintelQtoError("rate and length must be positive")
    x = rate_per_m * length / 1000.0
    return int(math.ceil(x - 1e-9))


def spacing_count(length, rate_per_m):
    if rate_per_m <= 0 or length <= 0:
        raise LintelQtoError("rate and length must be positive")
    s = 1000.0 / rate_per_m
    return int(math.ceil(length / s - 1e-9)) + 1
