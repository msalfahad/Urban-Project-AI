"""PRIVATE: an SVG crop per unmatched door swing: every segment / arc within 2.2 m of the hinge (by layer), the swing
arc, the closure A segment, the band openings nearby. usage: python3 -I q2_door_crops.py SRC PLAN DOORS_JSON ARCH_PLAN_JSON OUT_DIR"""
import json, math, sys
from pathlib import Path
SRC, PLAN, DJ, PJ, OUT = sys.argv[1:6]
sys.path.insert(0, SRC)
from tools import urban_intake as UI
OUT = Path(OUT); OUT.mkdir(parents=True, exist_ok=True)
it = UI.read(PLAN)
D = json.load(open(DJ)); P = json.load(open(PJ))
rep = {}
for r in P["regions"]:
    for c in (r.get("repairs") or {}).get("items", []):
        rep[c["id"]] = c
pal = {"1": "#c00", "5": "#000", "D": "#06c", "W": "#a50", "2": "#090", "S-COL.BON": "#088"}
R_ = 2200.0
out = {}
for reg in D["regions"]:
    for occ, d in sorted(reg["doors"].items()):
        if d["status"].get("state") == "MATCHED_TO_BAND_OPENING":
            continue
        cx, cy = d["hinge"]
        near = lambda p: abs(p[0] - cx) <= R_ and abs(p[1] - cy) <= R_
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{-R_} {-R_} {2*R_} {2*R_}" width="800" height="800">',
               f'<rect x="{-R_}" y="{-R_}" width="{2*R_}" height="{2*R_}" fill="#fff"/>']
        layers = {}
        for s in it["segments"]:
            if near(s["a"]) or near(s["b"]):
                col = pal.get(s["layer"], "#999"); layers[s["layer"]] = col
                svg.append(f'<line x1="{s["a"][0]-cx}" y1="{-(s["a"][1]-cy)}" x2="{s["b"][0]-cx}" y2="{-(s["b"][1]-cy)}" stroke="{col}" stroke-width="7"/>')
        for a in it["arcs"]:
            if near(a["c"]):
                col = "#f0f" if a["id"] in occ else pal.get(a["layer"], "#999")
                (sx, sy), (ex, ey) = a["s"], a["e"]
                svg.append(f'<path d="M {sx-cx} {-(sy-cy)} A {a["r"]} {a["r"]} 0 0 0 {ex-cx} {-(ey-cy)}" fill="none" stroke="{col}" stroke-width="{12 if col == "#f0f" else 6}"/>')
        ca = rep.get(f"CLOSURE|{occ}|A")
        if ca:
            (ax, ay), (bx, by) = ca["a"], ca["b"]
            svg.append(f'<line x1="{ax-cx}" y1="{-(ay-cy)}" x2="{bx-cx}" y2="{-(by-cy)}" stroke="#0c0" stroke-width="22" stroke-dasharray="60,30"/>')
        y = -R_ + 120
        for lay, col in layers.items():
            svg.append(f'<text x="{-R_+60}" y="{y}" font-size="100" fill="{col}">layer {lay}</text>'); y += 115
        svg.append(f'<text x="{-R_+60}" y="{y}" font-size="100" fill="#f0f">this swing</text>'); y += 115
        svg.append(f'<text x="{-R_+60}" y="{y}" font-size="100" fill="#0c0">closure A (wall to wall)</text>')
        svg.append("</svg>")
        name = f'{reg["region_id"].split(":")[1]}_{occ.split("|")[0].replace(":", "_")}'
        (OUT / f"{name}.svg").write_text("\n".join(svg))
        out[name] = {"occ": occ, "closure_a": ca and {"a": ca["a"], "b": ca["b"], "len_mm": round(math.dist(ca["a"], ca["b"]) * reg["unit_m"] * 1000, 1)}}
(OUT / "crops.json").write_text(json.dumps(out, indent=1))
print(sorted(out))
