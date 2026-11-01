"""T-426: clear spans of every ground-beam run, frame by frame, from the merged T-416 band read (Checker-verified,
Gate A b7bb914a; geometry reused with that citation, WORKFLOW_CONTROLS s.10.5), with the Checker's finding
F-C-T416-1 applied: the T-416 cuts were taken on outlines buffered by 0.5 mm, so every cut boundary inside a band is
moved back by 0.5 mm here (exact cuts, no buffer).

A run = a segment of a band between two consecutive SPLITTING cuts: a column / neck outline of the frame read, an S-BW
ring, or a junction square at the band's own end (the band stops at the other band's face). A junction in the middle
of the band (a beam landing on it, a crossing) never splits it (T-141 V2, R-T426-1). The end-column shift of a frame
(O-T407-1: the neck drawn with its near face elsewhere on the foundation / column plan) is added to the end segment.
GFRS (p.4, columns ABOVE the slab) is never a neck frame (R-T416-3): not read here.
"""
from __future__ import annotations

FRAMES = ("GBP", "FP", "CAP")
BUF_M = 0.0005


def _union(iv):
    out = []
    for a, b in sorted(iv):
        if out and a <= out[-1][1] + 1e-9:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def band_segments(band, frame):
    """Segments (start_m, end_m, length_m) of a straight / oblique band on one frame, exact cuts."""
    L = band["drawn_m"]
    cuts = []
    for c in band["frames"][frame]["columns"]:
        cuts.append((c["a_m"], c["b_m"]))
    for r in band["supports"]["rings"]:
        cuts.append((r["a_m"], r["b_m"]))
    for j in band["supports"]["junctions"]:
        if j["at_end"]:
            cuts.append((j["a_m"], j["b_m"]))
    exact = []
    for a, b in cuts:
        a2 = a + BUF_M if a > 0.002 else max(a, 0.0)
        b2 = b - BUF_M if b < L - 0.002 else min(b, L)
        exact.append((max(a2, 0.0), min(b2, L)))
    u = _union(exact)
    segs, pos = [], 0.0
    for a, b in u:
        if a - pos > 0.010:
            segs.append([pos, a])
        pos = max(pos, b)
    if L - pos > 0.010:
        segs.append([pos, L])
    # end-column shift on this frame (+ = the face recedes, the end segment grows)
    for ec in band.get("end_columns", []):
        d = 0.0 if frame == "GBP" else (ec["net_shift_m"].get(frame) or 0.0)
        if not segs or not d:
            continue
        if ec["end"] == 0 and segs[0][0] <= 0.002:
            segs[0][0] -= d
        elif ec["end"] == 1 and segs[-1][1] >= L - 0.002:
            segs[-1][1] += d
    return [(round(a, 4) + 0.0, round(b, 4) + 0.0, round(b - a, 4) + 0.0) for a, b in segs]


def spans_by_frame(band):
    return {k: band_segments(band, k) for k in FRAMES}
