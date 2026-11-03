"""T-478 own read (values only): the F10 / F10 + F / drawn-outline blinding scenarios of the two-tag outline 1B1B
with and without the plot-line clip (RFI S06), from the outline file t445_extract.py writes into .work/private
(positions stay there; only m2 / m3 are printed). Uses engine.source.arch_v3045.blinding_pieces (R-T478-1 a, c).

    .work/venv/bin/python -I research/agents_t478/t478_f10_clip.py <.work/private/t445_outlines.json>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.source import arch_v3045 as M  # noqa: E402

T, P = 0.10, 0.10                       # ST p.13 typical isolated footing: '10cm Plain con.', '10 | L x W | 10'
F10 = (2.80, 1.40)                      # schedule F10 (T-233 / T-445 scenario basis)
F = (0.90, 0.80)                        # schedule F


def rect(x0, y0, a, b):
    return [(x0, y0), (x0 + a, y0), (x0 + a, y0 + b), (x0, y0 + b)]


def one(outline, plot):
    r = M.blinding_pieces([{"id": "x", "outline": outline, "depth": 1.0, "t": T, "p": P}], plot)["pits"][0]
    return r["inside_m3"], round(r["inside_m3"] + r["beyond_high_m3"], 6)


def main(src):
    d = json.load(open(src))
    plot = d["plot"]
    v = d["outlines"]["1B1B"]["vertices"]
    xs, ys = [p[0] for p in v], [p[1] for p in v]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    out = {"drawn_outline": one(rect(x0, y0, x1 - x0, y1 - y0), plot)}
    # F10 alone inside the drawn outline's frame: at either end of the long side (the plot-line clip differs)
    f10 = [one(rect(x0, y0, *F10), plot), one(rect(x1 - F10[0], y0, *F10), plot)]
    out["F10_alone"] = (min(a for a, _ in f10), max(a for a, _ in f10), f10[0][1])
    # F rows: F's own grown plan anywhere inside the frame (its position is not printed): clipped 0.090 .. 0.110
    f = [one(rect(x0, y0, *F), plot), one(rect(x1 - F[0], y0, *F), plot), one(rect(x0, y1 - F[1], *F), plot)]
    out["F_rows_part"] = (min(a for a, _ in f), max(a for a, _ in f), f[0][1])
    lo = out["F10_alone"][0] + out["F_rows_part"][0]
    hi = out["F10_alone"][1] + out["F_rows_part"][1]
    out["F10_plus_F_rows"] = (round(lo, 6), round(hi, 6), round(out["F10_alone"][2] + out["F_rows_part"][2], 6))
    print(json.dumps({"outline_m": [round(x1 - x0, 4), round(y1 - y0, 4)], "scenarios_m3 (clipped_low, "
                      "clipped_high, unclipped)": out}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
