"""T-153 helper (research only): split the labelled exterior face of a ground-floor plan into named pieces.

Input: the faces JSON of research/agents_t147/scripts/rooms.py run with the plot box = the INNER face of the plot
boundary walls widened by 0.035 m (rooms.py shrinks its box by 0.05 m and grows faces back by BUF 0.015 m, so the
widening makes the face reach the boundary-wall face exactly), and a cuts JSON kept with the private inputs (client
coordinates are never committed): {"label": "<label prefix of the yard face>", "inner_box": [x0, y0, x1, y1],
"pieces": {"<name>": [x0, y0, x1, y1], ...} (boxes clipped in order; the remainder is "rest"),
"circles": {"<name>": [cx, cy, r], ...} (measured inside the piece "inside")}.
Prints the area of every piece, the remainder and each circle inside its piece. No coordinates are printed.
Usage: python -I yard_split.py <faces.json> <cuts.json>
"""
import json
import sys
from shapely import wkt
from shapely.geometry import box, Point

faces = json.load(open(sys.argv[1]))["faces"]
cuts = json.load(open(sys.argv[2]))
yard = [wkt.loads(o["wkt"]) for o in faces if cuts["label"] in o["labels"]][0]
g = yard.intersection(box(*cuts["inner_box"]))
print("yard face", round(yard.area, 4), "inside the boundary-wall faces", round(g.area, 4))
rest = g
pieces = {}
for name, b in cuts["pieces"].items():
    p = rest.intersection(box(*b))
    pieces[name] = p
    rest = rest.difference(p)
    print(name, round(p.area, 4))
print("rest", round(rest.area, 4))
for name, (cx, cy, r) in cuts.get("circles", {}).items():
    c = Point(cx, cy).buffer(r, quad_segs=512)
    inside = pieces.get(cuts.get("inside"), g)
    print("circle", name, "r", r, "inside", round(c.intersection(inside).area, 4), "full", round(c.area, 4))
