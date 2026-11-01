"""T-416 rules (pure, stdlib): what length of a ground beam is its own concrete, frame by frame, and how a lump length of
the other side is reconciled to it (every villa; provenance T-416, built on T-391 R-T391-4 and T-407 O-T407-1).

R-T416-1  NET OF SUPPORTS, EACH SUPPORT ONCE. A ground-beam band is the interval where both of its drawn face lines
          exist (DRAWN). The band centreline is cut by what it passes through: column / neck outlines (the neck owns the
          joint to the beam top, R-CONC-OWN-1; route G neck top = the beam top, T-200), S-BW rings, and junction
          squares owned by another band. NET = DRAWN - union of the cuts: the beam's own face-to-face concrete (Q-61 C).
          A support listed twice on one band (same handle, or two cuts that are one solid) is refused; overlapping
          cuts are taken as their union, never added.
R-T416-2  A JUNCTION SQUARE ONCE. Where two bands overlap, the square is owned by one of them (X over Y, straight
          over curved / oblique; any fixed order, stated); a square deducted from both, or kept in both, is refused.
R-T416-3  FRAMES GIVE A RANGE. The neck through the beam is drawn on the ground-beam plan, the foundation plan and the
          column & axis plan; where their outlines differ along the run, NET is a RANGE [min, max] over those frames,
          never one frame's figure without a printed reason. The ground-floor roof-slab frame draws the column ABOVE
          the slab: it is shown, never used for the beam deduction (refused as a neck frame).
R-T416-4  LUMP LENGTH vs DRAWN READINGS. On one set of bands: NET <= DRAWN (through the supports inside the face
          lines) <= AXIS (+ half of each end support) <= GROSS (+ every end support to its far face; a support shared by
          two collinear bands counted once). A lump length of the other side is placed between these readings. The
          length term -b D (L_other - L_engine) splits EXACTLY into
            + b D (L_engine - NET)       engine length beyond the drawn net, named band by band;
            - b D (L_other  - NET)       the other side beyond the drawn net:
                 within DRAWN - NET + END_GROSS  -> BOUNDED_THROUGH_SUPPORTS (mechanism named, the per-support split
                                                    not recoverable from a lump; never closed by its sign);
                 beyond it                      -> that excess UNRESOLVED (no drawn element carries it);
                 below NET                      -> SHORT (the other side omits drawn runs: UNRESOLVED).
          A per-run or per-support figure derived from a lump is refused.
R-T416-5  ONE BAND, ONE OWNER. A run of the house ground-beam set and a run of the boundary / fence band partition
          (T-403 / T-407: fence 44.07 / pool 3.50 / house 44.37 = 91.94 m) never share length; a shared length > 0 is
          refused. Footings and straps lie below the beam soffit (levels, T-253 / T-407): their plan overlap with a
          beam band is not a deduction from the beam length (0 shared volume).
"""

from __future__ import annotations

NECK_FRAMES = ("GBP", "FP", "CAP")
ABOVE_SLAB_FRAMES = ("GFRS",)
RANK = {"X": 0, "Y": 1, "O": 2, "C": 3}
MAX_RUN_M = 200.0     # a single run longer than this is a unit error (mm passed as m)
MAX_SET_M = 5000.0    # a set total / lump longer than this is a unit error
TOL = 1e-6


class RefusedT416(ValueError):
    pass


def _r(x, n=6):
    return round(float(x) + 0.0, n)


def _check_len(x, what, cap=MAX_RUN_M):
    if x is None:
        raise RefusedT416(f"{what}: missing (HELD, never 0)")
    if x < 0 or x > cap:
        raise RefusedT416(f"{what}: {x} m is not a run length in m (unit error)")


def net_of_supports(drawn_m, cuts):
    """drawn_m: band length; cuts: [{"id", "kind": COLUMN|RING|JUNCTION, "a_m", "b_m"}] along the centreline.
    Returns {"net_m", "cut_m", "by_kind"}. R-T416-1."""
    _check_len(drawn_m, "drawn length")
    seen = set()
    iv = []
    by_kind = {}
    for c in cuts:
        key = (c["kind"], c["id"])
        if key in seen:
            raise RefusedT416(f"support {c['id']} deducted twice on one band (DOUBLE)")
        seen.add(key)
        a, b = sorted((float(c["a_m"]), float(c["b_m"])))
        if a < -TOL or b > drawn_m + TOL:
            raise RefusedT416(f"support {c['id']} lies outside the drawn band")
        iv.append((a, b, c["kind"]))
        by_kind[c["kind"]] = by_kind.get(c["kind"], 0.0) + (b - a)
    iv.sort()
    cut, cur = 0.0, None
    for a, b, _ in iv:
        if cur is None or a > cur[1]:
            if cur:
                cut += cur[1] - cur[0]
            cur = [a, b]
        else:
            cur[1] = max(cur[1], b)
    if cur:
        cut += cur[1] - cur[0]
    return {"net_m": _r(drawn_m - cut), "cut_m": _r(cut), "by_kind": {k: _r(v) for k, v in sorted(by_kind.items())}}


def junction_owner(dir_a, dir_b):
    """the band that keeps a shared square (R-T416-2)."""
    if dir_a not in RANK or dir_b not in RANK:
        raise RefusedT416("unknown band direction")
    return "a" if RANK[dir_a] <= RANK[dir_b] else "b"


def check_junctions(squares):
    """squares: [{"id", "kept_in": [band ids]}]: each shared square is kept in exactly one band."""
    for s in squares:
        k = len(set(s["kept_in"]))
        if k != 1:
            raise RefusedT416(f"junction {s['id']} kept in {k} bands (must be exactly one)")
    return True


def frame_range(nets, chosen=None, reason=None):
    """nets: {frame: net_m}. Returns [lo, hi] over the neck frames (R-T416-3). A chosen single frame needs a reason
    when the frames differ; an above-slab frame is never a neck frame."""
    if chosen in ABOVE_SLAB_FRAMES:
        raise RefusedT416(f"{chosen} draws the column above the slab, not the neck through the beam")
    vals = {k: v for k, v in nets.items() if k in NECK_FRAMES}
    if not vals:
        raise RefusedT416("no neck frame read")
    for k, v in vals.items():
        _check_len(v, f"net on {k}")
    lo, hi = min(vals.values()), max(vals.values())
    if chosen is not None:
        if hi - lo > TOL and not reason:
            raise RefusedT416("frames differ: one frame chosen without a printed reason")
        return [_r(vals[chosen]), _r(vals[chosen])]
    return [_r(lo), _r(hi)]


def readings(net_m, in_band_m, end_supports):
    """end_supports: [{"m", "shared": bool}] at the band ends (rings excluded by the caller). R-T416-4."""
    _check_len(net_m, "net", MAX_SET_M)
    drawn = net_m + in_band_m
    axis = drawn + sum(e["m"] * 0.5 for e in end_supports)
    gross = drawn + sum(e["m"] * (0.5 if e["shared"] else 1.0) for e in end_supports)
    return {"net_m": _r(net_m), "drawn_m": _r(drawn), "axis_m": _r(axis), "gross_m": _r(gross)}


def place_lump(lump_m, r):
    """where a lump length sits among the drawn readings of the same set."""
    _check_len(lump_m, "lump length", MAX_SET_M)
    if lump_m < r["net_m"] - TOL:
        return "SHORT_OF_NET"
    if lump_m <= r["drawn_m"] + TOL:
        return "NET..DRAWN"
    if lump_m <= r["axis_m"] + TOL:
        return "DRAWN..AXIS"
    if lump_m <= r["gross_m"] + TOL:
        return "AXIS..GROSS"
    return "BEYOND_GROSS"


def length_term_split(b_m, d_m, lump_m, engine_len_m, r):
    """R-T416-4: the other side's section b x d over lump_m against the engine's lengths (sum engine_len_m) on the set
    whose drawn readings are r. Terms in m3 (engine - other); they re-add to the whole length term."""
    for v, w in ((b_m, "width"), (d_m, "depth")):
        if v is None or v <= 0 or v > 3:
            raise RefusedT416(f"{w} {v} m not a section dimension")
    _check_len(engine_len_m, "engine length", MAX_SET_M)
    whole = -b_m * d_m * (lump_m - engine_len_m)
    eng = b_m * d_m * (engine_len_m - r["net_m"])
    other_excess = lump_m - r["net_m"]
    allowance = r["gross_m"] - r["net_m"]
    pos = place_lump(lump_m, r)
    if pos == "SHORT_OF_NET":
        bounded, unresolved = 0.0, -b_m * d_m * other_excess
    elif pos == "BEYOND_GROSS":
        bounded, unresolved = -b_m * d_m * allowance, -b_m * d_m * (lump_m - r["gross_m"])
    else:
        bounded, unresolved = -b_m * d_m * other_excess, 0.0
    terms = {"engine_beyond_net_m3": _r(eng), "other_bounded_through_supports_m3": _r(bounded),
             "other_unresolved_m3": _r(unresolved)}
    rem = whole - sum(terms.values())
    if abs(rem) > 1e-6:
        raise RefusedT416(f"terms do not re-add to the length term ({rem:.6f} m3)")
    return {"length_term_m3": _r(whole), "terms_m3": terms, "position": pos,
            "other_beyond_net_m": _r(other_excess), "through_support_allowance_m": _r(allowance)}


def per_support_from_lump(*_a, **_k):
    """R-T416-4: a lump length is never split support by support."""
    raise RefusedT416("a per-run / per-support figure cannot be derived from a lump length")


def band_partition_overlap(house_runs, band_runs):
    """R-T416-5: [(id, [a, b] along one shared axis)] of the house GB runs and the fence / pool band runs."""
    shared = 0.0
    for hid, (a1, b1) in house_runs:
        for fid, (a2, b2) in band_runs:
            o = min(b1, b2) - max(a1, a2)
            if o > TOL:
                raise RefusedT416(f"{hid} and band {fid} share {o:.3f} m (one band, one owner)")
            shared += max(0.0, o)
    return _r(shared)
