"""BAND GAP CLASSES V1 (T-510, follow-up of the Checker-verified T-460 C5 / R-T460-1): every gap of a wall band is
reported once and classified by its BOUNDING ELEMENTS (column face, masonry jamb, closure line, crossing wall), never
by a width minimum. NEW version beside wall_bands.py; UNWIRED (no candidate, released method or frozen file changes;
a later stream F row wires it into an ARCH_TAKEOFF V3.0.x opening list).

DEFECT IT REPLACES (engine read only): the band path behind arch_rooms.spaces()["openings"] (lintel_measure.openings /
robust_geometry.openings) keeps a gap only when g >= min_gap_m = 0.50 m (opening_gaps.band_gaps) and drops every
column-cut piece under 0.50 m (lintel_measure._split_at_columns, whose comment reads 'the wall reach between a jamb and
a column face is not an opening'). A real 0.467 m window between a column face and a masonry jamb (development villa
1F W18) therefore has no engine opening; only per-project ledgers restored it. Any other villa loses such openings
silently (Q-73: deduct every actual opening).

PHYSICAL ELEMENT: a hole through a wall's masonry between two bounding elements, at any width; versus (a) a wall
junction, where a crossing wall runs through the band and both band faces stop at its faces although masonry is
continuous, (b) a column drawn in pieces, whose pieces leave slivers between them, (c) a face break with nothing
bounding it.

    classify(segments, unit_m, wall_layers, columns=(), *, column_polys=(), window_layers=(), swings=None,
             heights=None, t_m=(0.10, 0.45), tol="UNIT_RELATIVE", geom=None) -> {"records", "summary"}

Method, per wall layer and wall band (the same face lines, bands, merge tolerance and jamb tests as the engine path):
 1. every band gap down to the numerical floor FLOOR_M (2 mm = twice the 1 mm cover merge tolerance; not an
    engineering threshold) with its end jambs from opening_gaps.band_gaps;
 2. COLUMN PIECES JOINED FIRST: the column obstacles crossing the band strip inside the gap are projected on the band
    axis and joined into one column wherever their pieces overlap or stand within the engine's 30 mm jamb tolerance
    (one column drawn as several boxes / hatch pieces), BEFORE any piece is measured; the gap is then cut at each
    joined column's faces (each cut end a COLUMN_FACE). No piece is dropped for its width;
 3. each end is bounded by COLUMN_FACE, MASONRY_JAMB, CLOSURE_JAMB, WALL_JUNCTION (a masonry jamb whose face is a
    crossing wall face running on past BOTH band faces by more than 30 mm: R-T460-1's junction test) or NONE;
 4. class, first that holds:
      NO_BOUNDING_ELEMENT  an end with no bounding element                          -> HELD (never 0, never dropped)
      OPENING / WINDOW     WINDOW-layer glazing >= 0.5 x width (arch_rooms' own test) -> an actual opening
      OPENING / DOOR       a door swing fits (arch_rooms.match_swings)               -> an actual opening
      WALL_JUNCTION        both ends WALL_JUNCTION                                    -> NOT_AN_OPENING
      COINCIDENT_FACES     width under FLOOR_M (a column face on a jamb)              -> NOT_AN_OPENING (listed)
      NO_DISTINCT_JAMBS    width under the 30 mm jamb tolerance: its two jambs cannot be told apart -> HELD
      OPENING / UNMARKED   two distinct bounding elements, no symbol                  -> an actual opening
 5. status: an OPENING the released engine path already lists (both ends within 1 mm of an engine opening on the
    same band) is ENGINE (unchanged: its height and deductions stay the engine's); any other OPENING is
    DEDUCT_MEASURED (width x printed height, heights keyed by gap id) or DEDUCT_HEIGHT_HELD (width measured, area
    HELD, never 0). The width decides nothing about the class: a 0.499 m and a 0.501 m window are both OPENING /
    WINDOW; only the 'engine_opening' flag (what the released path keeps) differs. A gap of 0.50 m or more with an
    unbounded end is one the released path already refuses: it stays ENGINE_REJECTED (unchanged, listed), so the
    version changes no band the engine already decided; under 0.50 m the same class is HELD (it was dropped before).
General: no layer, block, room or project name is coded; mirrored, rotated, mm and m plans read alike (vectors and
distances only). Gap ids: SG-nnn over the non-engine records in (band, position) order, as in T-460.
"""

from __future__ import annotations

import math

from engine.source import lintel_measure as LM
from engine.source import member_detection as MD
from engine.source import opening_census as OC
from engine.source import opening_gaps as OG

POLICY = "BAND_GAP_CLASSES_V1"
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"  # T-212 / T-512: opening deduction m2 + net wall area; imported by no method or CLI
RULES = ("Q-73", "UP-WALL-GEOM-001", "UP-REF-COLUMN-001", "UP-SKIRT-001", "UP-QTY-STATUS-001", "R-T460-1", "R-T510-1")
ENGINE_MIN_GAP_M = 0.50        # the released band path's minimum (lintel_measure / robust_geometry openings default)
FLOOR_M = 0.002                # numerical floor: twice the 1 mm cover merge tolerance (T-460)
JAMB_TOL_M = 0.030             # the engine's jamb tolerance (band_gaps jamb_tol = 30 mm)
COLUMN_REACH_M = 0.060         # the engine's column reach (band_gaps column_reach = 60 mm)
GLAZING_SHARE = 0.5            # arch_rooms.spaces: kind WINDOW when glazing >= 0.5 x width
JUNCTION_REACH_M = 0.030       # a crossing face counts when it runs beyond the band face by more than 30 mm
PERP_COS = 0.02                # a jamb face is across the band axis within about 1.1 degrees
SAME_M = 0.001                 # a gap and an engine opening are one gap when both ends agree within 1 mm

COLUMN_FACE, MASONRY_JAMB, CLOSURE_JAMB, WALL_JUNCTION, NONE = (
    "COLUMN_FACE", "MASONRY_JAMB", "CLOSURE_JAMB", "WALL_JUNCTION", "NONE")
_END = {OC.COLUMN_JAMB: COLUMN_FACE, OC.MASONRY_JAMB: MASONRY_JAMB, OC.CLOSURE_JAMB: CLOSURE_JAMB,
        OC.UNBOUNDED: NONE}


def _frame(u, n, p):
    return (p[0] * u[0] + p[1] * u[1], p[0] * n[0] + p[1] * n[1])


def joined_columns(g, band, obst, join_tol):
    """the column obstacles standing inside gap g, projected on the band axis, joined where their pieces overlap or
    stand within join_tol: [(a, b, [obstacle ids])] sorted along the band (one entry per physical column)."""
    u, n = band["u"], band["n"]
    lo, hi = sorted((band["A"]["off"], band["B"]["off"]))
    cuts = []
    for oid, poly in obst:
        ss = [p[0] * u[0] + p[1] * u[1] for p in poly]
        oo = [p[0] * n[0] + p[1] * n[1] for p in poly]
        if max(oo) <= lo or min(oo) >= hi:
            continue
        a, b = max(min(ss), g["s0"]), min(max(ss), g["s1"])
        if b - a > 1e-9:
            cuts.append([a, b, [oid]])
    cuts.sort(key=lambda c: (c[0], c[1]))
    out = []
    for a, b, ids in cuts:
        if out and a - out[-1][1] <= join_tol:
            out[-1][1] = max(out[-1][1], b)
            out[-1][2] = out[-1][2] + ids
        else:
            out.append([a, b, list(ids)])
    return [(a, b, sorted(ids)) for a, b, ids in out]


def pieces(g, band, obst, join_tol):
    """gap g cut at every joined column (step 2): every piece, none dropped for its width."""
    cols = joined_columns(g, band, obst, join_tol)
    if not cols:
        return [dict(g, split_at_column=False, column_pieces=[])]
    out, s, jamb, prev = [], g["s0"], g["start_jamb"], []
    for a, b, ids in cols + [(g["s1"], g["s1"], [])]:
        end = g["end_jamb"] if a >= g["s1"] else OC.COLUMN_JAMB
        if a - s > 1e-12:
            out.append(dict(g, s0=s, s1=a, width=a - s, start_jamb=jamb, end_jamb=end, split_at_column=True,
                            column_pieces=sorted(set(prev) | set(ids))))
        s, jamb, prev = max(s, b), OC.COLUMN_JAMB, ids
    return out


def _junction_end(u, n, lo, hi, s_at, segments, wall_layers, unit_m):
    """face ids of a crossing wall at s_at that runs on past BOTH band faces (R-T460-1), else None"""
    tol = JAMB_TOL_M / unit_m
    reach = JUNCTION_REACH_M / unit_m
    ids = []
    for s in segments:
        if s["layer"] not in wall_layers:
            continue
        (sa, oa), (sb, ob) = _frame(u, n, s["a"]), _frame(u, n, s["b"])
        L = math.dist(s["a"], s["b"])
        if L <= 0 or abs(sb - sa) > PERP_COS * L or abs((sa + sb) / 2 - s_at) > tol:
            continue
        ids.append((s["id"], min(oa, ob), max(oa, ob)))
    below = [sid for sid, a, b in ids if a <= lo - reach and b >= lo - tol]
    above = [sid for sid, a, b in ids if b >= hi + reach and a <= hi + tol]
    if not below or not above:
        return None
    return sorted(set(below) | set(above))


def _glazing(u, n, s0, s1, o0, o1, segments, window_layers, unit_m):
    eps = 0.5e-3 / unit_m
    tot, ids = 0.0, []
    for s in segments:
        if s["layer"] not in window_layers:
            continue
        m = ((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2)
        su, so = _frame(u, n, m)
        if s0 - eps <= su <= s1 + eps and o0 - eps <= so <= o1 + eps:
            tot += math.dist(s["a"], s["b"]) * unit_m
            ids.append(s["id"])
    return tot, sorted(ids)


def _engine_openings(segments, unit_m, wall_layers, columns, column_polys, t_m, tol, geom):
    if geom is None:
        return LM.openings(segments, unit_m, wall_layers, columns, t_m=t_m, tol=tol, min_gap_m=ENGINE_MIN_GAP_M)[0]
    from engine.source import robust_geometry as RG
    return RG.openings(segments, unit_m, wall_layers, columns, t_m=t_m, tol=tol, geom=geom,
                       min_gap_m=ENGINE_MIN_GAP_M, column_polys=column_polys)[0]


def _raw_gaps(segments, unit_m, wall_layers, columns, column_polys, t_m, tol, geom):
    """(layer, band, obst, gaps at the floor) on the engine's own band path"""
    k = 1.0 / unit_m / 1000.0
    merge_tol = 1.0 if tol == "LEGACY" else 1e-3 / unit_m
    closures = [(s["id"], tuple(s["a"]), tuple(s["b"])) for s in segments
                if MD._layer_role(s["layer"]) not in MD.ANNOTATION_ROLES]
    obst = [(f"COL{i}", MD.box_poly(c)) for i, c in enumerate(columns)]
    obst += [(f"CPOLY{i}", [tuple(p) for p in poly]) for i, poly in enumerate(column_polys)]
    kw = dict(jamb_tol=30.0 * k, obstacles=obst, column_reach=60.0 * k, closures=closures, merge_tol=merge_tol)
    for lay in wall_layers:
        ss = [s for s in segments if s["layer"] == lay]
        if geom is None:
            fl = OC.face_lines([(s["id"], tuple(s["a"]), tuple(s["b"])) for s in ss], ang_res_deg=0.5,
                               off_tol=2.0 * k, join_tol=5.0 * k, min_len=100.0 * k)
            bands = OC.wall_bands(fl, t_m[0] / unit_m, t_m[1] / unit_m, min_overlap=0.3 / unit_m)
            for b in bands:
                yield lay, b, obst, OG.band_gaps(b, min_gap=FLOOR_M / unit_m, **kw)
        else:
            ctx0 = geom.context
            geom.context = f"{ctx0 or ''}|band_gap_classes|{lay}".lstrip("|")
            bands, mg = geom.bands(ss, t_m=t_m)
            for b in bands:
                yield lay, b, obst, geom.band_gaps(b, min_gap=FLOOR_M / unit_m, mg=mg, **kw)
            geom.context = ctx0


def classify(segments, unit_m, wall_layers, columns=(), *, column_polys=(), window_layers=(), swings=None,
             heights=None, t_m=(0.10, 0.45), tol="UNIT_RELATIVE", geom=None):
    if unit_m is None or not unit_m > 0:
        raise ValueError("UNITS_MISSING: metres per drawing unit not established; nothing is measured")
    heights = dict(heights or {})
    wall_layers = sorted(wall_layers)
    wl = set(wall_layers)
    window_layers = set(window_layers)
    eng = _engine_openings(segments, unit_m, wall_layers, columns, column_polys, t_m, tol, geom)
    same = SAME_M / unit_m
    join_tol = JAMB_TOL_M / unit_m
    raw = []
    for lay, b, obst, gaps in _raw_gaps(segments, unit_m, wall_layers, columns, column_polys, t_m, tol, geom):
        lo, hi = sorted((b["A"]["off"], b["B"]["off"]))
        for g0 in gaps:
            for g in pieces(g0, b, obst, join_tol):
                raw.append((lay, b, lo, hi, g))
    # one gap seen on two wall layers is kept once (the engine's own duplicate test: centre 0.2 m, width 0.05 m)
    kept, dup = [], 0
    for lay, b, lo, hi, g in raw:
        u, n = b["u"], b["n"]
        sm, om = (g["s0"] + g["s1"]) / 2, (lo + hi) / 2
        c = (u[0] * sm + n[0] * om, u[1] * sm + n[1] * om)
        if any(math.dist(c, k_["centre"]) * unit_m <= 0.2 and abs(k_["w"] - g["width"]) * unit_m <= 0.05
               for k_ in kept):
            dup += 1
            continue
        kept.append({"lay": lay, "b": b, "lo": lo, "hi": hi, "g": g, "centre": c, "w": g["width"]})
    served = {}
    if swings:
        from engine.source import arch_rooms as AR
        probe = [{"opening_id": f"P{i}", "u": k_["b"]["u"], "n": k_["b"]["n"], "s0": k_["g"]["s0"], "s1": k_["g"]["s1"],
                  "o0": k_["lo"], "o1": k_["hi"]} for i, k_ in enumerate(kept)]
        served = AR.match_swings(probe, swings, unit_m)
    recs = []
    for i, k_ in enumerate(kept):
        b, g, lo, hi = k_["b"], k_["g"], k_["lo"], k_["hi"]
        u, n = b["u"], b["n"]
        w = g["width"] * unit_m
        bounds, faces = [], {}
        for side, j, s_at in (("start", g["start_jamb"], g["s0"]), ("end", g["end_jamb"], g["s1"])):
            e = _END[j]
            if e == MASONRY_JAMB:
                jn = _junction_end(u, n, lo, hi, s_at, segments, wl, unit_m)
                if jn is not None:
                    e, faces[side] = WALL_JUNCTION, jn
            bounds.append(e)
        glz, gids = _glazing(u, n, g["s0"], g["s1"], lo, hi, segments, window_layers, unit_m)
        door = (served.get(f"P{i}") or [None])[0]
        ev = {}
        if NONE in bounds:
            cls, kind = "NO_BOUNDING_ELEMENT", None
        elif glz > 0 and glz >= GLAZING_SHARE * w:
            cls, kind, ev = "OPENING", "WINDOW", {"glazing_m": round(glz, 6), "glazing_ids": gids}
        elif door is not None:
            cls, kind, ev = "OPENING", "DOOR", {"swing": door}
        elif bounds == [WALL_JUNCTION, WALL_JUNCTION]:
            cls, kind, ev = "WALL_JUNCTION", None, {"crossing_faces": faces}
        elif w < FLOOR_M:
            cls, kind = "COINCIDENT_FACES", None
        elif w < JAMB_TOL_M:
            cls, kind = "NO_DISTINCT_JAMBS", None
        else:
            cls, kind = "OPENING", "UNMARKED"
        hits = [max(abs(e["s0"] - g["s0"]), abs(e["s1"] - g["s1"])) for e in eng
                if e["band_id"] == b["band_id"] and abs(e["s0"] - g["s0"]) <= same and abs(e["s1"] - g["s1"]) <= same]
        is_eng = bool(hits)
        recs.append({"band_id": b["band_id"], "layer": k_["lay"], "s0": g["s0"], "s1": g["s1"],
                     "width_m": round(w, 6), "wall_t_m": round(g["t"] * unit_m, 6),
                     "start_bound": bounds[0], "end_bound": bounds[1], "split_at_column": g["split_at_column"],
                     "column_pieces": g["column_pieces"], "cls": cls, "kind": kind, "evidence": ev,
                     "engine_opening": is_eng, "engine_end_diff_m": round(min(hits) * unit_m, 9) if hits else None})
    recs.sort(key=lambda r: (r["band_id"], r["s0"]))
    m = 0
    for r in recs:
        r["differs_from_engine"] = (r["cls"] == "OPENING") != r["engine_opening"] and r["width_m"] >= ENGINE_MIN_GAP_M
        if r["engine_opening"] and r["cls"] == "OPENING":
            r.update(gap_id=None, status="ENGINE", height_m=None, deduct_m2=None)
            continue
        if r["cls"] == "NO_BOUNDING_ELEMENT" and not r["engine_opening"] and r["width_m"] >= ENGINE_MIN_GAP_M:
            # a gap the released path already refuses (an UNBOUNDED end at >= 0.50 m): its decision is kept unchanged
            # and listed, so the new version changes no band the engine already decided
            r.update(gap_id=None, status="ENGINE_REJECTED", height_m=None, deduct_m2=None,
                     reason="released band path refuses it (unbounded end); unchanged, listed for review")
            continue
        m += 1
        gid = f"SG-{m:03d}"
        r.update(gap_id=gid, height_m=None, deduct_m2=None)
        if r["cls"] == "OPENING":
            h = heights.get(gid)
            if h is None:
                r.update(status="DEDUCT_HEIGHT_HELD", reason="opening height not printed / scheduled: area HELD, "
                                                            "width measured; never 0")
            else:
                r.update(status="DEDUCT_MEASURED", height_m=float(h), deduct_m2=round(r["width_m"] * float(h), 6))
        elif r["cls"] in ("WALL_JUNCTION", "COINCIDENT_FACES"):
            r.update(status="NOT_AN_OPENING", reason="continuous masonry: crossing wall faces / a column face on the "
                                                     "jamb")
        else:
            r.update(status="HELD", reason="no bounding element or no distinct jambs: masonry over this width is a "
                                           "named range, never deducted, never kept silently")
    own = [r for r in recs if r["gap_id"]]
    summ = {"policy": POLICY, "floor_m": FLOOR_M, "engine_min_gap_m": ENGINE_MIN_GAP_M,
            "engine_openings": len(eng), "records": len(recs), "duplicates_on_another_layer": dup,
            "engine_kept": sum(r["status"] == "ENGINE" for r in recs),
            "engine_rejected_listed": sum(r["status"] == "ENGINE_REJECTED" for r in recs),
            "engine_not_matched": len(eng) - sum(r["status"] == "ENGINE" for r in recs),
            "differs_from_engine": sum(r["differs_from_engine"] for r in recs),
            "engine_max_end_diff_m": max((r["engine_end_diff_m"] for r in recs if r["status"] == "ENGINE"), default=0.0),
            "by_class": {c: sum(r["cls"] == c for r in own) for c in
                         ("OPENING", "WALL_JUNCTION", "COINCIDENT_FACES", "NO_DISTINCT_JAMBS", "NO_BOUNDING_ELEMENT")},
            "new_openings": sum(r["cls"] == "OPENING" for r in own),
            "deduct_measured_m2": round(sum(r["deduct_m2"] for r in own if r["deduct_m2"] is not None), 6),
            "deduct_height_held_width_m": round(sum(r["width_m"] for r in own
                                                    if r["status"] == "DEDUCT_HEIGHT_HELD"), 6)}
    return {"records": recs, "summary": summ}


def wall_deduction(gross_m2, records, faces=1):
    """net masonry / finish area of one wall after its non-engine openings (per face for finishes): a height-HELD
    opening or a HELD gap keeps the net a range with no low end (state HELD), never 0."""
    if gross_m2 is None:
        return {"net_m2": None, "net_low_m2": None, "state": "HELD", "held": []}
    own = [r for r in records if r.get("gap_id")]
    known = sum(r["deduct_m2"] for r in own if r.get("status") == "DEDUCT_MEASURED") * faces
    held = [r["gap_id"] for r in own if r.get("status") in ("DEDUCT_HEIGHT_HELD", "HELD")]
    net = round(gross_m2 - known, 6)
    if held:
        return {"net_m2": net, "net_low_m2": None, "state": "HELD", "held": held}
    return {"net_m2": net, "net_low_m2": net, "state": "MEASURED", "held": []}


def policy_record() -> dict:
    return {"policy": POLICY, "rules": list(RULES), "wired": False,
            "rule": "R-T510-1: a wall-band gap is classified by its bounding elements (column face, masonry jamb, "
                    "closure, crossing wall) after the pieces of one column are joined; no width minimum decides that "
                    "an opening does not exist; a gap with no bounding element is HELD, never 0",
            "floor_m": FLOOR_M, "jamb_tol_m": JAMB_TOL_M, "replaces_minimum_m": ENGINE_MIN_GAP_M}
