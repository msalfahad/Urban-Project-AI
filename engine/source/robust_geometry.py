"""ROBUST GEOMETRY (M9 Phase 2A, ARCH_TAKEOFF_V2.1 only) - the reviewed robust predicate at the three band-path
threshold sites, and a face-line projection that is correct at any wall angle. Opt-in: V1 and V2 never reach this
module; route G and every historical freeze are untouched (opening_census.py is frozen by the S8.6 code pin and is
not edited: this module calls it).

Policy ROBUST_PREDICATE_V1 (round 2, Q1; owner decision: the three reviewed sites only, no global rewrite)

    keep  <=>  value >= T - m,     m = max(eps_abs, eps_fp)
        eps_abs = 1e-6 mm (in drawing units)
        eps_fp  = 16 u M (d + 1),  u = 2**-53, M = the largest |coordinate| of the inputs, d = the insert depth
    |value - T| <= m          -> the decision is recorded (AT_THRESHOLD: site, value, T, m)
    eps_fp > 1e-3 mm          -> a recorded decision is UNDECIDABLE (REVIEW): kept, never silently
    eps_fp > eps_abs          -> a PRECISION_WIDENED review finding names the widened band

    the sites (the only ones in Phase 2A):
        FACE_PIECE      opening_census.face_lines   `L < min_len`          100 mm
        BAND_OVERLAP    opening_census.wall_bands   `hi - lo < min_overlap` 300 mm
        OPENING_GAP     band_gaps                   `g < min_gap`           500 mm (openings) / 400 mm (window gaps)

    Each frozen function compares its threshold once, strictly, so calling it with T - m IS the robust predicate
    (research/freeze_integrity/stage2_threshold_shift_check.py: 648 / 648). The recorded decisions are the
    difference between the frozen function at T - m and at T + m: no comparison is re-implemented here.

Policy MEAN_AXIS_V1 (round 2, finding F-3)
    opening_census.face_lines measures along the 0.5-degree BIN axis: across a wall of thickness t the far face's
    positions shift by t sin(dtheta), and at an arbitrary angle a door gap is lost. face_lines() here keeps the bin for
    grouping only and measures along the bin's length-weighted doubled-angle mean direction, kept in the bin's
    half-plane (no direction flips). Everything after the axis (offset grouping, interval union) is the frozen
    procedure, built from opening_census's own helpers.

    Geometry(unit_m)                    the V2.1 geometry with a decision recorder
    Geometry.frozen(unit_m)             the frozen V1 / V2 geometry (no margin, bin axis, no records): the equivalence
                                        reference of the tests
    g.face_lines / g.wall_bands / g.band_gaps / g.bands(segs)
    openings(segments, unit_m, layers, columns, geom=...)
                                        lintel_measure.openings with the geometry injected (frozen geometry ->
                                        identical results; lintel_measure.py itself is not edited)
    threshold_census()                  every strict comparison against a drafted length on the V2 path and its
                                        reviewed decision (AT-Q1-08)

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from engine.source import lintel_measure as LM
from engine.source import member_detection as MD
from engine.source import opening_census as OC
from engine.source import opening_gaps as OG

POLICY_ID = "ROBUST_PREDICATE_V1"
AXIS_POLICY_ID = "MEAN_AXIS_V1"
U = 2.0 ** -53
EPS_ABS_MM = 1e-6
UNDECIDABLE_MM = 1e-3
SITES = ("FACE_PIECE", "BAND_OVERLAP", "OPENING_GAP")
AT_THRESHOLD, UNDECIDABLE = "AT_THRESHOLD", "UNDECIDABLE"


class Geometry:
    """the band-path geometry of one run. robust=False with mean_axis=False is the frozen geometry, call for call."""

    def __init__(self, unit_m, *, robust=True, mean_axis=True, eps_abs_mm=EPS_ABS_MM, undecidable_mm=UNDECIDABLE_MM):
        self.unit_m = unit_m
        self.k = 1.0 / unit_m / 1000.0                 # drawing units per mm
        self.robust, self.mean_axis = robust, mean_axis
        self.eps_abs_mm, self.undecidable_mm = eps_abs_mm, undecidable_mm
        self.records, self.findings = [], []
        self._widened = set()
        self.context = None                            # a label (region, layer) written into each record

    @classmethod
    def frozen(cls, unit_m):
        return cls(unit_m, robust=False, mean_axis=False)

    @property
    def policy(self):
        return {"predicate": POLICY_ID if self.robust else "FROZEN_STRICT", "axis": AXIS_POLICY_ID if self.mean_axis
                else "BIN_AXIS (frozen)", "eps_abs_mm": self.eps_abs_mm if self.robust else None,
                "undecidable_mm": self.undecidable_mm if self.robust else None, "sites": list(SITES)}

    # ------------------------------------------------------------- margin
    def margin(self, segments):
        """{m, eps_abs, eps_fp (drawing units), M, d, undecidable} for these segments [(id, a, b[, depth])]."""
        M = max((abs(v) for s in segments for p in (s[1], s[2]) for v in p), default=0.0)
        d = max((s[3] if len(s) > 3 else 1 for s in segments), default=1)
        eps_abs = self.eps_abs_mm * self.k
        eps_fp = 16.0 * U * M * (d + 1)
        m = max(eps_abs, eps_fp) if self.robust else 0.0
        und = self.robust and eps_fp > self.undecidable_mm * self.k
        if self.robust and eps_fp > eps_abs and (round(M), d) not in self._widened:
            self._widened.add((round(M), d))
            self.findings.append({"level": "REVIEW", "code": "PRECISION_WIDENED", "context": self.context,
                                  "M_drawing_units": M, "insert_depth": d,
                                  "band_mm": round(eps_fp / self.k, 12), "undecidable": und,
                                  "message": f"coordinates up to {M:.6g} drawing units at insert depth {d}: the "
                                             f"threshold decision band widens to +/-{eps_fp / self.k:.3g} mm"
                                             + (" (beyond 1e-3 mm: decisions inside it are UNDECIDABLE)" if und else "")})
        return {"m": m, "eps_abs": eps_abs, "eps_fp": eps_fp, "M": M, "d": d, "undecidable": und}

    def _record(self, site, value, T, mg, where, ids):
        st = UNDECIDABLE if mg["undecidable"] else AT_THRESHOLD
        rec = {"site": site, "state": st, "decision": "KEPT", "context": self.context,
               "value_mm": value / self.k, "threshold_mm": T / self.k, "delta_mm": (value - T) / self.k,
               "margin_mm": mg["m"] / self.k, "where": where, "ids": ids}
        self.records.append(rec)
        if st == UNDECIDABLE:
            self.findings.append({"level": "REVIEW", "code": "UNDECIDABLE_THRESHOLD", "context": self.context,
                                  "site": site, "ids": ids, "message": f"{site}: {value / self.k:.9g} mm against "
                                  f"{T / self.k:g} mm is inside the float error bound (+/-{mg['eps_fp'] / self.k:.3g} "
                                  "mm): kept, and the decision needs review"})
        return rec

    # ------------------------------------------------------------- the three sites
    def face_lines(self, segments, *, ang_res_deg=0.5, off_tol, join_tol, min_len):
        """segments [(id, a, b) or (id, a, b, depth)] -> face lines (FACE_PIECE site at min_len)."""
        segs = [s[:3] for s in segments]
        if not self.robust and not self.mean_axis:
            return OC.face_lines(segs, ang_res_deg=ang_res_deg, off_tol=off_tol, join_tol=join_tol, min_len=min_len)
        mg = self.margin(segments)
        T = min_len
        if self.robust:
            for sid, a, b in segs:
                L = math.dist(a, b)
                if abs(L - T) <= mg["m"]:
                    self._record("FACE_PIECE", L, T, mg, [list(a), list(b)], [sid])
        fn = face_lines_mean_axis if self.mean_axis else OC.face_lines
        return fn(segs, ang_res_deg=ang_res_deg, off_tol=off_tol, join_tol=join_tol, min_len=T - mg["m"])

    def wall_bands(self, lines, t_min, t_max, *, min_overlap, mg=None):
        if not self.robust:
            return OC.wall_bands(lines, t_min, t_max, min_overlap=min_overlap)
        mg = mg or self._margin_of_lines(lines)
        kept = OC.wall_bands(lines, t_min, t_max, min_overlap=min_overlap - mg["m"])
        strict = {b["band_id"] for b in OC.wall_bands(lines, t_min, t_max, min_overlap=min_overlap + mg["m"])}
        for b in kept:
            if b["band_id"] not in strict:
                self._record("BAND_OVERLAP", b["hi"] - b["lo"], min_overlap, mg, _band_point(b),
                             [b["band_id"], b["A"]["line_id"], b["B"]["line_id"]])
        return kept

    def band_gaps(self, band, *, min_gap, mg=None, **kw):
        """opening_gaps.band_gaps (merge_tol and the other keywords passed through) at the OPENING_GAP site."""
        if not self.robust:
            return OG.band_gaps(band, min_gap=min_gap, **kw)
        mg = mg or self._margin_of_lines([band["A"], band["B"]])
        kept = OG.band_gaps(band, min_gap=min_gap - mg["m"], **kw)
        strict = {(g["s0"], g["s1"]) for g in OG.band_gaps(band, min_gap=min_gap + mg["m"], **kw)}
        for g in kept:
            if (g["s0"], g["s1"]) not in strict:
                u, n = band["u"], band["n"]
                om = (band["A"]["off"] + band["B"]["off"]) / 2
                sm = (g["s0"] + g["s1"]) / 2
                self._record("OPENING_GAP", g["width"], min_gap, mg, [u[0] * sm + n[0] * om, u[1] * sm + n[1] * om],
                             [band["band_id"]])
        return kept

    def _margin_of_lines(self, lines):
        pts = []
        for ln in lines:
            u, n = ln["u"], ln["n"]
            for t in (ln["lo"], ln["hi"]):
                pts.append((u[0] * t + n[0] * ln["off"], u[1] * t + n[1] * ln["off"]))
        d = max((ln.get("_depth", 1) for ln in lines), default=1)
        return self.margin([("L", p, p, d) for p in pts])

    def bands(self, segs, *, t_m=(0.10, 0.45)):
        """arch_plan._bands / lintel_measure's band step: face lines then wall bands, one margin for both."""
        k, u = self.k, self.unit_m
        tup = [_tuple(s) for s in segs]
        fl = self.face_lines(tup, ang_res_deg=0.5, off_tol=2.0 * k, join_tol=5.0 * k, min_len=100.0 * k)
        mg = self.margin(tup) if self.robust else None
        return self.wall_bands(fl, t_m[0] / u, t_m[1] / u, min_overlap=0.3 / u, mg=mg), mg

    # ------------------------------------------------------------- report
    def decisions(self):
        """the recorded decisions, one per (site, element ids, value): the same band met again by a later step
        (wall caps, wall runs) adds its context to the first record."""
        out, at = [], {}
        for r in self.records:
            key = (r["site"], tuple(r["ids"]), round(r["value_mm"], 9))
            if key in at:
                if r["context"] not in at[key]["contexts"]:
                    at[key]["contexts"].append(r["context"])
                continue
            at[key] = dict({k: v for k, v in r.items() if k != "context"}, contexts=[r["context"]])
            out.append(at[key])
        return out

    def report(self):
        recs = self.decisions()
        return {"policy": self.policy, "decisions": len(recs),
                "by_site_state": dict(sorted(Counter(f"{r['site']}:{r['state']}" for r in recs).items())),
                "records": recs, "findings": self.findings}


def _tuple(s):
    """an intake segment -> (id, a, b, insert depth); the depth is the length of its insert path (1 = model space)."""
    return (s["id"], tuple(s["a"]), tuple(s["b"]), max(1, len(s.get("path") or ())))


def _band_point(b):
    u, n = b["u"], b["n"]
    t, o = (b["lo"] + b["hi"]) / 2, (b["A"]["off"] + b["B"]["off"]) / 2
    return [u[0] * t + n[0] * o, u[1] * t + n[1] * o]


def face_lines_mean_axis(segments, ang_res_deg=0.1, off_tol=2.0, join_tol=1.0, min_len=1.0):
    """opening_census.face_lines with each bin measured along its length-weighted doubled-angle mean direction."""
    bins = defaultdict(list)
    for sid, a, b in segments:
        L = math.dist(a, b)
        if L < min_len:
            continue
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0
        key = round(round(ang / ang_res_deg) * ang_res_deg, 6) % 180.0
        bins[key].append((sid, a, b, L, ang))
    lines = []
    for key in sorted(bins):
        mem = bins[key]
        cx = sum(L * math.cos(math.radians(2.0 * ang)) for *_x, L, ang in mem)
        cy = sum(L * math.sin(math.radians(2.0 * ang)) for *_x, L, ang in mem)
        th = math.degrees(math.atan2(cy, cx)) / 2.0
        uk, _nk = OC.frame_of(key)
        u, n = OC.frame_of(th)
        if u[0] * uk[0] + u[1] * uk[1] < 0.0:          # keep the bin's half-plane: no direction flips
            u, n = (-u[0], -u[1]), (-n[0], -n[1])
        items = sorted((OC.along(a, n), *sorted((OC.along(a, u), OC.along(b, u))), sid) for sid, a, b, _L, _g in mem)
        cur = None
        for off, t0, t1, sid in items:
            if cur is not None and off - cur["_last"] <= off_tol:
                cur["_iv"].append((t0, t1, [sid]))
                cur["_offs"].append(off)
                cur["_last"] = off
            else:
                cur = {"ang": key, "u": u, "n": n, "_iv": [(t0, t1, [sid])], "_offs": [off], "_last": off}
                lines.append(cur)
    for ln in lines:
        ln["off"] = sum(ln["_offs"]) / len(ln["_offs"])
        ln["cover"] = OC._union(ln.pop("_iv"), join_tol)
        ln["lo"], ln["hi"] = ln["cover"][0][0], ln["cover"][-1][1]
        del ln["_offs"], ln["_last"]
    for i, ln in enumerate(lines):
        ln["line_id"] = f"FL{i + 1:04d}"
    return lines


def openings(segments, unit_m, layers, columns=(), *, t_m=(0.10, 0.45), min_gap_m=0.5, tol="LEGACY", geom=None,
             column_polys=()):
    """lintel_measure.openings with the band geometry injected. geom=Geometry.frozen(unit_m) reproduces
    lintel_measure.openings exactly (the delegation test); the column split keeps its frozen comparison (it is not a
    reviewed site). column_polys (ARCH_TAKEOFF_V2.7.1 only, UP-COL-ORIENT-001): column rectangles of any orientation
    as polygons, obstacles like the boxes; () is the V2.1 .. V2.7 path, unchanged."""
    geom = geom or Geometry.frozen(unit_m)
    k = 1.0 / unit_m / 1000.0
    merge_tol = 1.0 if tol == "LEGACY" else 1e-3 / unit_m
    closures = [(s["id"], tuple(s["a"]), tuple(s["b"])) for s in segments
                if MD._layer_role(s["layer"]) not in MD.ANNOTATION_ROLES]
    obst = [(f"COL{i}", MD.box_poly(c)) for i, c in enumerate(columns)]
    obst += [(f"CPOLY{i}", [tuple(p) for p in poly]) for i, poly in enumerate(column_polys)]
    out, rej = [], Counter()
    for lay in layers:
        ctx0 = geom.context
        geom.context = f"{ctx0 or ''}|openings|{lay}".lstrip("|")
        bands, mg = geom.bands([s for s in segments if s["layer"] == lay], t_m=t_m)
        for b in bands:
            gaps = geom.band_gaps(b, min_gap=min_gap_m / unit_m, mg=mg, jamb_tol=30.0 * k, obstacles=obst,
                                  column_reach=60.0 * k, closures=closures, merge_tol=merge_tol)
            for g in [x for g0 in gaps for x in LM._split_at_columns(g0, b, obst, min_gap_m / unit_m)]:
                if g["state"] != OC.OPENING:
                    rej[g["state"]] += 1
                    continue
                lo, hi = sorted((b["A"]["off"], b["B"]["off"]))
                u, n = b["u"], b["n"]
                sm, om = (g["s0"] + g["s1"]) / 2, (lo + hi) / 2
                c = (u[0] * sm + n[0] * om, u[1] * sm + n[1] * om)
                if any(math.dist(c, o["centre"]) * unit_m <= 0.2 and abs(o["width_m"] - g["width"] * unit_m) <= 0.05
                       for o in out):
                    rej["DUPLICATE_ON_ANOTHER_LAYER"] += 1
                    continue
                out.append({"opening_id": f"OP-{len(out) + 1:03d}", "band_id": b["band_id"], "layer": lay,
                            "u": u, "n": n, "s0": g["s0"], "s1": g["s1"], "o0": lo, "o1": hi,
                            "width_m": g["width"] * unit_m, "wall_t_m": g["t"] * unit_m,
                            "start_jamb": g["start_jamb"], "end_jamb": g["end_jamb"], "centre": c,
                            "split_at_column": g.get("split_at_column", False)})
        geom.context = ctx0
    return out, dict(rej)


# every strict comparison against a drafted length constant on the V2 band path, with its reviewed decision
THRESHOLD_CENSUS = (
    ("engine/source/opening_census.py", "face_lines", "L < min_len", "100 mm", "FACE_PIECE", "ROBUST_MARGIN"),
    ("engine/source/opening_census.py", "wall_bands", "hi - lo < min_overlap", "300 mm", "BAND_OVERLAP", "ROBUST_MARGIN"),
    ("engine/source/opening_census.py", "band_gaps", "g < min_gap", "500 / 400 mm", "OPENING_GAP", "ROBUST_MARGIN"),
    ("engine/source/opening_gaps.py", "band_gaps", "g < min_gap", "500 / 400 mm", "OPENING_GAP", "ROBUST_MARGIN"),
    ("engine/source/opening_census.py", "wall_bands", "t > t_max + TOL / t < t_min - TOL", "100 / 450 mm",
     "BAND_THICKNESS", "UNCHANGED (thickness range with its own 1e-9 tolerance; not reviewed)"),
    ("engine/source/opening_census.py", "face_lines", "off - last <= off_tol / t0 <= end + join_tol", "2 / 5 mm",
     "FACE_GROUPING", "UNCHANGED (tolerances, not thresholds on a drafted value)"),
    ("engine/source/opening_census.py", "arc_gaps", "g < min_gap_mm", "500 mm", "ARC_GAP",
     "UNCHANGED (curved walls; listed for individual review)"),
    ("engine/source/lintel_measure.py", "_split_at_columns", "a - s >= min_gap", "500 mm", "COLUMN_SPLIT_PIECE",
     "UNCHANGED (same constant, separate comparison; not reviewed)"),
    ("engine/source/arch_plan.py", "layer_roles", "long band >= LONG_BAND_M", "1.5 m", "LONG_BAND",
     "UNCHANGED (a layer-role score, not a measured quantity)"),
    ("engine/source/arch_rooms.py", "match_swings", "dj > T / r > w + fit", "300 / 150 mm", "SWING_FIT",
     "UNCHANGED (fit tolerances)"),
)


def threshold_census():
    return [dict(zip(("file", "function", "comparison", "constant", "site", "decision"), r)) for r in THRESHOLD_CENSUS]


def policy_record():
    return {"policy": POLICY_ID, "axis_policy": AXIS_POLICY_ID, "eps_abs_mm": EPS_ABS_MM,
            "undecidable_mm": UNDECIDABLE_MM, "margin": "max(eps_abs, 16 u M (d + 1))", "sites": list(SITES),
            "census": threshold_census(),
            "never": ["a threshold value changed", "a site outside the three reviewed ones given a margin",
                      "an UNDECIDABLE decision kept or dropped silently", "opening_census.py edited"]}
