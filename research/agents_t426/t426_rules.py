"""T-426 ground-beam SECTION CLASS census: pure rules (stdlib only; every villa).

The physical question (ERS s.2.1): what cross-section b x D does each ground-beam run have, by what the drawings PRINT
for that run, and does the candidate line carry that section?

What a drawing set can print for a ground-beam section (read on Alsenan ST p.13, the only place; the GROUND BEAMS PLAN
p.3 prints no section mark on any run, own census, R-T426-1):

    interior (slab inside on both sides)  title by the run's own clear span:
        'More than 5m length / without concentrated load'   30 x 60
        'Less than 5m length / without concentrated load'   30 x 40
        'Less than 2.5m length'                              30 x 30   (no load qualifier printed under this title)
    exterior (slab one side, outside ground the other)  'for exterior walls': 30 wide, depth 'FOLLOW ARCH.' from the
        GF slab level to the outer normal ground level (D printed only through two levels of the element)
    court (outside ground both sides)  no printed section

Rules (research, provenance T-426; a rule change is a new rule version):

R-T426-1  A run's section comes from the run's OWN drawn clear span (support face to support face on the band; a
          founded neck / column cut by the band is a support, a beam landing on the run is not) and the run's OWN
          position. It is never borrowed from a neighbouring run, from the band's total length, or from the line that
          bills it. A line that bills several runs carries each run's printed section, run by run.
R-T426-2  Titles are read literally on the span: > 5 m -> GT5M; < 5 m -> LT5M; < 2.5 m -> LT2_5M AND LT5M both hold
          (D-34, unanswered: both depths kept, a range); exactly 5.000 m (within 0.5 mm) -> neither title holds
          literally -> ON_LIMIT, both depths kept, HELD.
R-T426-3  Frames and readings that disagree on the span (a neck drawn at another place on the foundation / column plan,
          a band end drawn short of / beside a column) give one class per frame / reading; when they give different
          titles the section is a RANGE over those titles, never one chosen frame.
R-T426-4  m3 at stake on a line = b x L_run x (D_line - D_printed) per run, summed; a RANGE when the printed depth is a
          range. A run with no printed section (court; exterior with no printed depth; source conflict) has no printed
          depth: its stake is HELD and never 0.
R-T426-5  The load qualifier ('without concentrated load') is reported beside the class as its own status: a run that
          receives another beam between its faces (D-33) keeps its class from R-T426-1 but its section is HELD by D-33
          (printed for the unloaded case only); a title that prints no qualifier (< 2.5 m) is not held by D-33.
"""
from __future__ import annotations

import math

LIMIT_HI = 5.0
LIMIT_LO = 2.5
ON_LIMIT_TOL_M = 0.0005
DEPTH_TOL_M = 0.0005          # a line depth derived as value / plan within 0.5 mm of a printed depth IS that depth

INTERIOR_DEPTH_M = {"GT5M": 0.60, "LT5M": 0.40, "LT2_5M": 0.30}
LOAD_QUALIFIED = {"GT5M": True, "LT5M": True, "LT2_5M": False}     # own read of ST p.13 titles
B_PRINTED_M = 0.30


class CensusError(ValueError):
    pass


def _num(x, what):
    if x is None or isinstance(x, bool) or not isinstance(x, (int, float)) or math.isnan(x):
        raise CensusError(f"{what}: missing or not a number (never 0)")
    return float(x)


def titles_for_span(span_m):
    """R-T426-2: the p.13 interior titles that hold literally on a clear span in metres."""
    s = _num(span_m, "span")
    if s <= 0:
        raise CensusError("span must be positive")
    if s > 50:
        raise CensusError("span over 50 m: the value is not in metres")
    if abs(s - LIMIT_HI) <= ON_LIMIT_TOL_M:
        return ("ON_LIMIT",)
    if s > LIMIT_HI:
        return ("GT5M",)
    if s < LIMIT_LO:
        return ("LT2_5M", "LT5M")
    return ("LT5M",)


def depths_for_titles(titles):
    out = set()
    for t in titles:
        if t == "ON_LIMIT":
            out |= {INTERIOR_DEPTH_M["GT5M"], INTERIOR_DEPTH_M["LT5M"]}
        else:
            out.add(INTERIOR_DEPTH_M[t])
    return tuple(sorted(out))


def run_section(position, spans_by_frame, exterior_depth=None, loaded=False):
    """Printed section of ONE run (R-T426-1 .. 3, 5).

    position: 'INTERIOR' | 'EXTERIOR' | 'COURT'
    spans_by_frame: {frame or reading: clear span m} (interior only; one entry or more)
    exterior_depth: printed depth of an exterior run as (lo, hi) in m, or None when not printed / in conflict
    """
    if position == "INTERIOR":
        if not spans_by_frame:
            raise CensusError("interior run without a span: no class")
        titles, per = set(), {}
        for k, s in sorted(spans_by_frame.items()):
            t = titles_for_span(s)
            per[k] = t
            titles |= set(t)
        depths = depths_for_titles(titles)
        status = "PRINTED" if len(depths) == 1 else ("ON_LIMIT" if "ON_LIMIT" in titles else "RANGE")
        frames_differ = len({per[k] for k in per}) > 1
        d33 = bool(loaded) and any(LOAD_QUALIFIED.get(t, True) for t in titles)
        return {"position": position, "titles": tuple(sorted(titles)), "titles_by_frame": per,
                "frames_differ": frames_differ, "b_m": B_PRINTED_M, "D_m": depths, "status": status,
                "d33_held": d33}
    if position == "EXTERIOR":
        if exterior_depth is None:
            return {"position": position, "titles": ("EXTERIOR",), "titles_by_frame": {}, "frames_differ": False,
                    "b_m": B_PRINTED_M, "D_m": None, "status": "NOT_PRINTED", "d33_held": False}
        lo, hi = (_num(exterior_depth[0], "exterior depth"), _num(exterior_depth[1], "exterior depth"))
        if lo > 5 or hi > 5:
            raise CensusError("exterior depth over 5 m: the value is not in metres")
        d = (lo,) if abs(lo - hi) < 1e-9 else (min(lo, hi), max(lo, hi))
        return {"position": position, "titles": ("EXTERIOR",), "titles_by_frame": {}, "frames_differ": False,
                "b_m": B_PRINTED_M, "D_m": d, "status": "PRINTED" if len(d) == 1 else "RANGE", "d33_held": False}
    if position == "COURT":
        return {"position": position, "titles": (), "titles_by_frame": {}, "frames_differ": False, "b_m": None,
                "D_m": None, "status": "NOT_PRINTED", "d33_held": False}
    raise CensusError(f"unknown position {position!r}")


def line_stake(line_b_m, line_D_m, runs):
    """R-T426-4: m3 at stake on one candidate line = sum over its runs of b x L_run x (D_line - D_printed).

    runs: [{'L_m': run length billed by the line, 'section': run_section(...)}]
    Returns (lo, hi) in m3, or None when any run has no printed depth (HELD, never 0), plus a verdict word.
    A held line (line_D_m None) is never valued here: its stake is None and its verdict HELD_LINE.
    """
    if not runs:
        raise CensusError("a line bills at least one run")
    if line_D_m is None:
        return None, "HELD_LINE"
    b = _num(line_b_m, "line width")
    D = _num(line_D_m, "line depth")
    if b > 3 or D > 5:
        raise CensusError("line section not in metres")
    lo = hi = 0.0
    printed_all = True
    agree = True
    for r in runs:
        L = _num(r["L_m"], "run length")
        sec = r["section"]
        if sec["D_m"] is None:
            printed_all = False
            continue
        bp = sec["b_m"]
        if abs(bp - b) > 1e-9:
            agree = False
        Dr = next((d for d in sec["D_m"] if abs(d - D) <= DEPTH_TOL_M), D)
        ds = [b * L * Dr - bp * L * d for d in sec["D_m"]]
        lo += min(ds)
        hi += max(ds)
        if len(sec["D_m"]) > 1 or abs(sec["D_m"][0] - Dr) > 1e-9:
            agree = False
    if not printed_all:
        return None, "NO_PRINTED_SECTION"
    lo, hi = round(lo, 6) + 0.0, round(hi, 6) + 0.0
    if agree:
        return (lo, hi), "AGREE"
    if lo <= 0.0 <= hi:
        return (lo, hi), "INSIDE_RANGE"
    return (lo, hi), "DIFFERS"


def borrowed_section_refused(run_span_m, neighbour_span_m, line_D_m):
    """Adverse guard (R-T426-1): a depth that matches only the neighbour's (or the whole band's) class while the run's
    own class differs is a borrowed section."""
    own = depths_for_titles(titles_for_span(run_span_m))
    other = depths_for_titles(titles_for_span(neighbour_span_m))
    D = _num(line_D_m, "line depth")
    return (D not in own) and (D in other)
