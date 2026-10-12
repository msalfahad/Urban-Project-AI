"""ARCH OVERLAY (M9 S2, S3) - one SVG per plan region: the wall layers, every measured space coloured by class, the
openings and the room ids, the recognised stair treads (S3: orange; a flight seen through a void, counted on the plan
below, hatched) and the wall-band centrelines by thickness (S3), so a reviewer can see what the architectural route
measured (stdlib only).

    svg(intake, region, rooms, openings, walls=None) -> SVG text (drawing coordinates, y flipped)
"""

from __future__ import annotations

from xml.sax.saxutils import escape

FILL = {"ROOM": "#cfe8cf", "MIXED": "#fff2b3", "MERGED": "#f5b7b1", "UNLABELLED": "#e0e0e0"}
ROLE_STROKE = {"WALL": "#333333", "COLUMN": "#7b3f00", "WINDOW": "#1f77b4", "DOOR": "#9467bd"}


def _pts(poly, X, Y):
    return " ".join(f"{X(p[0]):.1f},{Y(p[1]):.1f}" for p in poly)


WALL_STROKE = {"0.10": "#17becf", "0.15": "#2ca02c", "0.20": "#1f77b4", "0.25": "#9467bd", "0.30": "#8c564b"}


def svg(intake, region, rooms, openings, width=1600, walls=None):
    x0, y0, x1, y1 = region["box"]
    s = width / max(x1 - x0, 1e-9)
    H = (y1 - y0) * s
    X = lambda x: (x - x0) * s                                  # noqa: E731
    Y = lambda y: (y1 - y) * s                                  # noqa: E731
    roles = region.get("layer_roles") or {}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{H:.0f}" viewBox="0 0 {width} {H:.0f}" '
           f'font-family="Arial">', f'<rect width="100%" height="100%" fill="#ffffff"/>']
    for rm in rooms:
        d = "M " + _pts(rm["polygon"], X, Y) + " Z"
        for h in rm.get("hole_polygons") or ():
            d += " M " + _pts(h, X, Y) + " Z"
        out.append(f'<path d="{d}" fill="{FILL.get(rm["class"], "#eeeeee")}" fill-rule="evenodd" stroke="none">'
                   f'<title>{escape(rm["room_id"] + " " + rm["name_en"] + " " + rm["class"])}</title></path>')
    for sg in intake["segments"]:
        r = roles.get(sg["layer"])
        if r not in ROLE_STROKE:
            continue
        a, b = sg["a"], sg["b"]
        if not (x0 <= a[0] <= x1 and y0 <= a[1] <= y1 and x0 <= b[0] <= x1 and y0 <= b[1] <= y1):
            continue
        out.append(f'<line x1="{X(a[0]):.1f}" y1="{Y(a[1]):.1f}" x2="{X(b[0]):.1f}" y2="{Y(b[1]):.1f}" '
                   f'stroke="{ROLE_STROKE[r]}" stroke-width="{1.4 if r == "WALL" else 0.9}"/>')
    for rm in rooms:
        for fl in (rm.get("symbols_inside") or {}).get("stair_flights") or ():
            seen = bool(fl.get("drawn_on_plan_below"))
            fill = "none" if seen else "#ffbb78"
            dash = ' stroke-dasharray="3,2"' if seen else ""
            title = escape(f"{fl.get('flight_id')} {fl['kind']}" + (" seen through a void" if seen else ""))
            for q in fl.get("tread_quads") or ():
                out.append(f'<polygon points="{_pts(q, X, Y)}" fill="{fill}" stroke="#d62728" stroke-width="0.8"'
                           f'{dash}><title>{title}</title></polygon>')
    for w in (walls or {}).get("walls") or ():
        (ax, ay), (bx, by) = w["centreline"]
        out.append(f'<line x1="{X(ax):.1f}" y1="{Y(ay):.1f}" x2="{X(bx):.1f}" y2="{Y(by):.1f}" '
                   f'stroke="{WALL_STROKE.get(w["family"], "#7f7f7f")}" stroke-width="2.2" stroke-opacity="0.55">'
                   f'<title>{escape(w["wall_id"] + " t=" + w["family"] + " " + w["kind"])}</title></line>')
    for rm in rooms:
        p = rm.get("point")
        if not p:
            continue
        lab = f'{rm["room_id"]} {rm["name_en"]}'
        out.append(f'<text x="{X(p[0]):.1f}" y="{Y(p[1]):.1f}" font-size="11" text-anchor="middle" fill="#000">'
                   f'{escape(lab)}</text>')
        out.append(f'<text x="{X(p[0]):.1f}" y="{Y(p[1]) + 13:.1f}" font-size="10" text-anchor="middle" '
                   f'fill="#333">{rm["area_m2"]:.2f} m2 ({escape(rm["class"])})</text>')
    out.append(f'<text x="10" y="20" font-size="14" fill="#c00000">{escape(region["region_id"])}: machine overlay '
               f'(MACHINE_ONLY) - green ROOM, yellow MIXED, red MERGED, grey UNLABELLED; orange stair treads (dashed: '
               f'seen through a void); wall centrelines by thickness; {len(openings)} openings</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"
