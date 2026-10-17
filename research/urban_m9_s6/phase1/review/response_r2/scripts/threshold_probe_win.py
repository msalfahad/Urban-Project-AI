"""Scratch probe (review only; production code untouched): run the ARCH_TAKEOFF CLI in-process on a drawing with the
band-path threshold comparisons replaced by instrumented copies that (a) log every comparison whose value lies within
a relative 1e-6 of its threshold, and (b) optionally apply a slack to selected thresholds.

usage: python3 -I threshold_probe.py SRC PLAN OUT METHOD SLACK_SET [refs...]
  SRC        a source export (engine/, tools/, rules/, data/)
  SLACK_SET  comma list from {none, face, overlap, gap, split, colside, all}: thresholds that get a 1e-9 relative slack
"""
import json, math, sys
SRC, PLAN, OUT, METHOD, SLACK = sys.argv[1:6]
REFS = sys.argv[6:]
sys.path.insert(0, SRC)
from collections import defaultdict
from engine.source import opening_census as OC, arch_plan as AP, lintel_measure as LM
SL = set(SLACK.split(",")) - {"none"}
if "all" in SL:
    SL = {"face", "overlap", "gap", "split", "colside"}
EPS = 1e-9
import os
WIN = float(os.environ.get('PROBE_WIN', '1e-6'))   # relative window around each threshold
EVENTS = []


def lower(thr, key):          # a lower bound, relaxed by the slack when selected
    return thr * (1 - EPS) if key in SL else thr


def log(fn, name, value, thr, kept, **ctx):
    if abs(value - thr) <= WIN * max(abs(thr), 1e-300):
        EVENTS.append({"fn": fn, "threshold": name, "value": value, "limit": thr, "rel_diff": (value - thr) / thr,
                       "kept": kept, **ctx})


def face_lines(segments, ang_res_deg=0.1, off_tol=2.0, join_tol=1.0, min_len=1.0):
    groups = defaultdict(list)
    for sid, a, b in segments:
        L = math.dist(a, b)
        drop = L < lower(min_len, "face")
        log("opening_census.face_lines", "min_len", L, min_len, not drop, seg=sid, a=list(a), b=list(b))
        if drop:
            continue
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0
        ang = round(round(ang / ang_res_deg) * ang_res_deg, 6) % 180.0
        u, n = OC.frame_of(ang)
        off = OC.along(a, n)
        t0, t1 = sorted((OC.along(a, u), OC.along(b, u)))
        groups[ang].append((off, t0, t1, sid))
    lines = []
    for ang in sorted(groups):
        u, n = OC.frame_of(ang)
        items = sorted(groups[ang])
        cur = None
        for off, t0, t1, sid in items:
            if cur is not None and off - cur["_last"] <= off_tol:
                cur["_iv"].append((t0, t1, [sid]))
                cur["_offs"].append(off)
                cur["_last"] = off
            else:
                cur = {"ang": ang, "u": u, "n": n, "_iv": [(t0, t1, [sid])], "_offs": [off], "_last": off}
                lines.append(cur)
    for ln in lines:
        ln["off"] = sum(ln["_offs"]) / len(ln["_offs"])
        ln["cover"] = OC._union(ln.pop("_iv"), join_tol)
        ln["lo"], ln["hi"] = ln["cover"][0][0], ln["cover"][-1][1]
        del ln["_offs"], ln["_last"]
    for i, ln in enumerate(lines):
        ln["line_id"] = f"FL{i + 1:04d}"
    return lines


def wall_bands(lines, t_min, t_max, min_overlap=300.0):
    TOL = OC.TOL
    if t_min <= 0 or t_max < t_min:
        raise OC.OpeningCensusError("band thickness range")
    by_ang = defaultdict(list)
    for ln in lines:
        by_ang[ln["ang"]].append(ln)
    bands = []
    for ang, ls in sorted(by_ang.items()):
        ls = sorted(ls, key=lambda l: l["off"])
        for i, A in enumerate(ls):
            for B in ls[i + 1:]:
                t = B["off"] - A["off"]
                if t > t_max + TOL:
                    break
                if t < t_min - TOL:
                    continue
                lo, hi = max(A["lo"], B["lo"]), min(A["hi"], B["hi"])
                drop = hi - lo < lower(min_overlap, "overlap")
                log("opening_census.wall_bands", "min_overlap", hi - lo, min_overlap, not drop, ang=ang,
                    A=A["line_id"], B=B["line_id"])
                if drop:
                    continue
                between = [C for C in ls if A["off"] + TOL < C["off"] < B["off"] - TOL and
                           min(C["hi"], hi) - max(C["lo"], lo) > TOL]
                if between:
                    continue
                bands.append({"ang": ang, "u": A["u"], "n": A["n"], "A": A, "B": B, "t": t, "lo": lo, "hi": hi,
                              "band_id": f"WB-{A['line_id']}-{B['line_id']}"})
    return bands


_frozen_band_gaps = OC.band_gaps


def band_gaps(band, min_gap=250.0, jamb_tol=30.0, obstacles=(), column_reach=60.0, closures=(), cover_ratio=0.9):
    # the frozen procedure, with the gap threshold instrumented (merge 1.0 as frozen)
    return _gaps(band, min_gap, jamb_tol, obstacles, column_reach, closures, cover_ratio, 1.0)


def _gaps(band, min_gap, jamb_tol, obstacles, column_reach, closures, cover_ratio, merge_tol):
    lo, hi = band["lo"], band["hi"]
    A, B = OC._covers(band["A"]["cover"], lo, hi), OC._covers(band["B"]["cover"], lo, hi)
    both = OC._union([(a, b, ids) for a, b, ids in A + B], merge_tol)
    out = []
    for (_x0, e0, _ids0), (s1, _x1, _ids1) in zip(both, both[1:]):
        g = s1 - e0
        drop = g < lower(min_gap, "gap")
        log("band_gaps", "min_gap", g, min_gap, not drop, band=band["band_id"], s0=e0, s1=s1)
        if drop:
            continue
        ends = {}
        for side, s in ((-1, e0), (1, s1)):
            fa = [t for t in A if (abs(t[1] - s) <= jamb_tol if side < 0 else abs(t[0] - s) <= jamb_tol)]
            fb = [t for t in B if (abs(t[1] - s) <= jamb_tol if side < 0 else abs(t[0] - s) <= jamb_tol)]
            col = OC._obstacle_at(band, s, side, obstacles, column_reach)
            if col is not None:
                ends[side] = (OC.COLUMN_JAMB, col)
            elif fa and fb:
                ends[side] = (OC.MASONRY_JAMB, None)
            else:
                cl = OC._closure_at(band, s, closures, jamb_tol, cover_ratio)
                ends[side] = (OC.CLOSURE_JAMB, cl) if cl is not None else (OC.UNBOUNDED, None)
        state = OC.OPENING if all(v[0] != OC.UNBOUNDED for v in ends.values()) else OC.REJECTED
        out.append({"band_id": band["band_id"], "s0": e0, "s1": s1, "width": g, "t": band["t"],
                    "start_jamb": ends[-1][0], "start_column": ends[-1][1],
                    "end_jamb": ends[1][0], "end_column": ends[1][1], "state": state})
    return out


from engine.source import opening_gaps as OG


def og_band_gaps(band, min_gap=250.0, jamb_tol=30.0, obstacles=(), column_reach=60.0, closures=(), cover_ratio=0.9,
                 merge_tol=OG.LEGACY_MERGE_TOL):
    return _gaps(band, min_gap, jamb_tol, obstacles, column_reach, closures, cover_ratio, merge_tol)


def split_at_columns(g, band, obst, min_gap):
    u, n = band["u"], band["n"]
    lo, hi = sorted((band["A"]["off"], band["B"]["off"]))
    cuts = []
    for _, poly in obst:
        ss = [p[0] * u[0] + p[1] * u[1] for p in poly]
        oo = [p[0] * n[0] + p[1] * n[1] for p in poly]
        if max(oo) <= lo or min(oo) >= hi:
            continue
        a, b = max(min(ss), g["s0"]), min(max(ss), g["s1"])
        if b - a > 1e-9:
            cuts.append((a, b))
    if not cuts:
        return [g]
    cuts.sort()
    out, s, jamb = [], g["s0"], g["start_jamb"]
    for a, b in cuts + [(g["s1"], g["s1"])]:
        end = g["end_jamb"] if a >= g["s1"] else OC.COLUMN_JAMB
        keep = a - s >= lower(min_gap, "split")
        log("lintel_measure._split_at_columns", "min_gap", a - s, min_gap, keep, band=band["band_id"], s0=s, s1=a)
        if keep:
            st = OC.OPENING if OC.UNBOUNDED not in (jamb, end) else OC.REJECTED
            out.append(dict(g, s0=s, s1=a, width=a - s, start_jamb=jamb, end_jamb=end, state=st,
                            split_at_column=True))
        s, jamb = max(s, b), OC.COLUMN_JAMB
    return out


def small_rects(segs, unit_m, tol="LEGACY"):
    out = []
    lo_, hi_ = AP.COLUMN_SIDE_M
    for r in AP.DM.closed_rectangles(segs, eps=AP.unit_tol(unit_m, tol)):
        b = r["box"]
        w, h = (b[2] - b[0]) * unit_m, (b[3] - b[1]) * unit_m
        for v in (w, h):
            log("arch_plan._small_rects", "column_side_min", v, lo_, v >= lower(lo_, "colside"), box=list(b))
        if lower(lo_, "colside") <= w <= hi_ and lower(lo_, "colside") <= h <= hi_:
            out.append(b)
    return out


OC.face_lines, OC.wall_bands, OC.band_gaps = face_lines, wall_bands, band_gaps
OG.band_gaps = og_band_gaps
LM._split_at_columns = split_at_columns
AP._small_rects = small_rects

OPENINGS = []
_lm_openings = LM.openings


def lm_openings(segments, unit_m, layers, columns=(), **kw):
    out, rej = _lm_openings(segments, unit_m, layers, columns, **kw)
    OPENINGS.append([{k: o[k] for k in ("opening_id", "band_id", "layer", "u", "n", "s0", "s1", "o0", "o1", "width_m",
                                         "start_jamb", "end_jamb", "centre")} for o in out])
    return out, rej


LM.openings = lm_openings
from tools import urban_boq_m9 as M9
args = ["arch", "--drawings", PLAN, "--out", OUT, "--method", METHOD, "--no-svg", "--no-m9-xlsx"]
if REFS:
    args += ["--reference-areas", *REFS]
import contextlib, io
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    code = M9.main(args)
json.dump({"exit": code, "slack": sorted(SL), "events": EVENTS, "lm_openings": OPENINGS}, open(OUT + ".events.json", "w"), indent=1)
print(code, len(EVENTS))
