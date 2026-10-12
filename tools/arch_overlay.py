"""ARCH OVERLAY (M9 S2, S3, S4) - one SVG per plan region: the wall layers, every measured space coloured by class, the
openings and the room ids, the recognised stair treads (S3: orange; a flight seen through a void, counted on the plan
below, hatched) and the wall-band centrelines by thickness (S3), so a reviewer can see what the architectural route
measured (stdlib only). S4 (floor_area = the floor's arch_floor record): the outlined voids (blue hatch, never floor),
shafts (dark grey), the first-pass cells a room took in through an open passage (dashed outline: the functional
allocation to confirm), spaces shared by several rooms (red dashed) and the floor's area balance in the title.

    svg(intake, region, rooms, openings, walls=None, floor_area=None) -> SVG text (drawing coordinates, y flipped)
"""

from __future__ import annotations

from xml.sax.saxutils import escape

FILL = {"ROOM": "#cfe8cf", "MIXED": "#fff2b3", "MERGED": "#f5b7b1", "UNLABELLED": "#e0e0e0"}
SHAFT_FILL = "#8c8c8c"
ROLE_STROKE = {"WALL": "#333333", "COLUMN": "#7b3f00", "WINDOW": "#1f77b4", "DOOR": "#9467bd"}


def _pts(poly, X, Y):
    return " ".join(f"{X(p[0]):.1f},{Y(p[1]):.1f}" for p in poly)


WALL_STROKE = {"0.10": "#17becf", "0.15": "#2ca02c", "0.20": "#1f77b4", "0.25": "#9467bd", "0.30": "#8c564b"}


def svg(intake, region, rooms, openings, width=1600, walls=None, floor_area=None):
    x0, y0, x1, y1 = region["box"]
    s = width / max(x1 - x0, 1e-9)
    H = (y1 - y0) * s
    X = lambda x: (x - x0) * s                                  # noqa: E731
    Y = lambda y: (y1 - y) * s                                  # noqa: E731
    roles = region.get("layer_roles") or {}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{H:.0f}" viewBox="0 0 {width} {H:.0f}" '
           f'font-family="Arial">', f'<rect width="100%" height="100%" fill="#ffffff"/>',
           '<defs><pattern id="voidhatch" patternUnits="userSpaceOnUse" width="8" height="8" '
           'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="8" stroke="#1f77b4" stroke-width="2"/>'
           '</pattern></defs>']
    for rm in rooms:
        d = "M " + _pts(rm["polygon"], X, Y) + " Z"
        for h in rm.get("hole_polygons") or ():
            d += " M " + _pts(h, X, Y) + " Z"
        fill = SHAFT_FILL if (rm.get("kind") in ("SHAFT",)) else FILL.get(rm["class"], "#eeeeee")
        out.append(f'<path d="{d}" fill="{fill}" fill-rule="evenodd" stroke="none">'
                   f'<title>{escape(rm["room_id"] + " " + rm["name_en"] + " " + rm["class"])}</title></path>')
    fa = floor_area or {}
    shared_cells = {x for s_ in fa.get("shared_open_spaces") or () for x in s_["cells"]}
    for c in fa.get("cell_outlines") or ():
        col = "#d62728" if c["face_id"] in shared_cells else "#2ca02c"
        out.append(f'<polygon points="{_pts(c["polygon"], X, Y)}" fill="none" stroke="{col}" stroke-width="1.6" '
                   f'stroke-dasharray="6,3"><title>{escape(c["face_id"])} cell {c["area_m2"]:.2f} m2 ' +
                   ("shared by several rooms (review)" if c["face_id"] in shared_cells else
                    "taken in through an open passage (confirm)") + '</title></polygon>')
    for v in fa.get("voids") or ():
        if not v.get("corners") or v.get("state") != "OUTLINED":
            continue
        out.append(f'<polygon points="{_pts(v["corners"], X, Y)}" fill="url(#voidhatch)" fill-opacity="0.6" '
                   f'stroke="#1f77b4" stroke-width="1.6"><title>{escape(v["void_id"])} void {v["area_m2"]:.2f} m2 '
                   f'({escape(v["evidence"])}): open to below, never floor</title></polygon>')
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
               f'(MACHINE_ONLY) - green ROOM, yellow MIXED, red MERGED, grey UNLABELLED, dark grey SHAFT; blue hatch '
               f'VOID (never floor); dashed green: cells taken in through an open passage; orange stair treads (dashed: '
               f'seen through a void); wall centrelines by thickness; {len(openings)} openings</text>')
    if fa:
        nf = fa.get("not_floor_m2") or {}
        ow = fa.get("of_which") or {}
        out.append(f'<text x="10" y="40" font-size="13" fill="#333">floor {escape(str(fa.get("floor")))}: gross plate '
                   f'{fa.get("gross_floor_plate_m2", 0):.2f} m2 = internal floor {fa.get("internal_physical_floor_m2", 0):.2f} '
                   f'(rooms {ow.get("rooms_single_label_m2", 0):.2f}, open plan {ow.get("open_plan_m2", 0):.2f}, '
                   f'unallocated {ow.get("unallocated_m2", 0):.2f}, stairs {ow.get("stairs_and_landings_m2", 0):.2f}, '
                   f'doorways {ow.get("doorway_strips_m2", 0):.2f}) + voids {nf.get("voids", 0):.2f} + shafts '
                   f'{nf.get("shafts", 0):.2f} + stair below {nf.get("stair_below_seen", 0):.2f} + walls / columns '
                   f'{nf.get("wall_and_column_mass", 0):.2f} + slivers {nf.get("slivers", 0):.2f} + external '
                   f'{fa.get("external_m2", 0):.2f}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"
