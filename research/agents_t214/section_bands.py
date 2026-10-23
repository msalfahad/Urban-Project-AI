"""T-214: measure the floor bands of an architect's cut sections in a DWF 6 plot (reproducible reading, any villa).

What it measures, per section view and per printed level: the drawn lines just below the level line (the band top), the
next line below it (the build-up line, if one is drawn) and the band bottom, and the vertical span of the hatch strokes
inside the band (hatched = cut concrete in these sections, T-201 s.7). Values are metres relative to the level line of
the same view; the view's own level texts fix the datum (a single translation must reproduce every printed level to
TOL_LEVEL, else the view is refused). Nothing is scaled off a raster here; the current issue is checked separately.

Run (Python 3.11, from the repository root; the DWF stays in .work/private, nothing of it is written to the tree):
    python3 -I research/agents_t214/section_bands.py <path to the architectural .dwf>
Prints JSON: per section, the datum fit and per level {top, build_up_line, bottom, hatch_span} in metres below the level.
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_t201"))
import w2d_reader as W  # noqa: E402

TOL_LEVEL = 0.005       # m: printed levels are to the centimetre
MIN_LEN = 2.5           # m: a band line is a long horizontal line of the cut (not a glyph, tick or hatch)
# Search windows relative to each section title text, model millimetres (x0, x1); the vertical window is the
# whole view (levels -1.0 .. +16.0 m around the datum). Set from the plot's layout; a title not listed is skipped.
WINDOWS = {"SECTION A-A": (-7700, 22300), "SECTION B-B": (-17700, 22300)}
LEVEL_RE = re.compile(r"^[+-]\d+\.\d\d$")


def _segments(pl, x0, x1):
    for poly in pl:
        for a, b in zip(poly, poly[1:]):
            if x0 <= min(a[0], b[0]) and max(a[0], b[0]) <= x1:
                yield a, b


def measure(dwf_path):
    graphics = W.read_dwf_graphics(dwf_path)
    out = {}
    for _, g in graphics:
        tr = g["units"]
        pl = [[W.to_model(q, tr) for q in poly] for poly in g["polylines"]]
        texts = [(W.to_model((t[0], t[1]), tr), t[2] if isinstance(t[2], str) else t[2].decode("latin1"))
                 for t in g["texts"]]
        for (tx, ty), s in texts:
            title = s.strip()
            if title not in WINDOWS:
                continue
            x0, x1 = tx + WINDOWS[title][0], tx + WINDOWS[title][1]
            segs = list(_segments(pl, x0, x1))
            hz = collections.defaultdict(float)
            for a, b in segs:
                if abs(a[1] - b[1]) < 1.0 and abs(a[0] - b[0]) > 50:
                    hz[round((a[1] + b[1]) / 2)] += abs(a[0] - b[0])
            lines = sorted(y for y, L in hz.items() if L >= MIN_LEN * 1000)
            # datum: each printed level text carries its marker, a closed triangle whose apex (lowest vertex) sits
            # on the level line; one translation must put every marker of the view on its printed value
            apex = {}
            for (x2, y2), s2 in texts:
                if not (x0 <= x2 <= x1 and abs(y2 - ty) < 20000 and LEVEL_RE.match(s2.strip())):
                    continue
                tri = [poly for poly in pl if 3 <= len(poly) <= 4 and all(
                    -200 <= q[0] - x2 <= 700 and -1000 <= q[1] - y2 <= -500 for q in poly)]
                if tri:
                    apex[float(s2)] = min(q[1] for poly in tri for q in poly)
            if len(apex) < 3:
                out[title] = {"refused": "fewer than 3 level markers found"}
                continue
            y0s = [y - v * 1000 for v, y in apex.items()]
            spread = max(y0s) - min(y0s)
            if spread > TOL_LEVEL * 1000:
                out[title] = {"refused": f"level markers disagree by {spread / 1000:.3f} m (one translation)"}
                continue
            y0 = sum(y0s) / len(y0s)
            hit = sorted(apex)
            rows = {}
            for v in hit:
                top = y0 + v * 1000
                below = [ln for ln in lines if top - 260 <= ln < top - 1]
                spans = collections.Counter()
                for a, b in segs:
                    lo, hi = min(a[1], b[1]), max(a[1], b[1])
                    if lo >= top - 260 and hi <= top + 60 and abs(a[0] - b[0]) > 5 and hi - lo > 5:
                        spans[(round(top - hi), round(top - lo))] += 1
                hatch = spans.most_common(1)[0] if spans else None
                rows[f"{v:+.2f}"] = {
                    "lines_below_m": [round((top - ln) / 1000, 3) for ln in sorted(below, reverse=True)],
                    "hatch_span_m": None if not hatch or hatch[1] < 10 else
                    [round(hatch[0][0] / 1000, 3), round(hatch[0][1] / 1000, 3)],
                    "hatch_strokes": 0 if not hatch else hatch[1]}
            out[title] = {"levels_with_marker": [f"{v:+.2f}" for v in hit], "marker_spread_m": round(spread / 1000, 4),
                          "bands": rows}
    return out


if __name__ == "__main__":
    print(json.dumps(measure(sys.argv[1]), indent=1, sort_keys=True))
