"""Overlays. Meaning is carried by label and line style, never by colour
alone.

Drawn as SVG straight from the frozen chain coordinates, so nothing is
re-derived and no sheet registration is needed. No area is computed.

    python3 -m research.qs_measurement_region_experiment_01.overlays
"""

from __future__ import annotations

import json
from pathlib import Path

from research.qs_measurement_region_experiment_01 import protocol as P
from research.qs_measurement_region_experiment_01.build import (
    CHAIN_ELEMENT_TO_TOPOLOGICAL_ROLE, OUT, load, write)

# stroke, dash, width, marker glyph, label. The glyph and the label are
# what carry the meaning; colour is an aid, never the only channel.
STYLE = {
    "PHYSICAL_BOUNDARY": ("#1a1a1a", "none", 3.0, "",
                          "physical material boundary"),
    "OPENING": ("#b8860b", "2,3", 2.0, "O", "confirmed opening"),
    "SYNTHETIC_MEASUREMENT_BOUNDARY": ("#0b6fa4", "9,4,2,4", 2.0, "S",
                                       "synthetic measurement closure"),
    "OPEN_PHYSICAL_EDGE": ("#7a7a7a", "1,4", 2.0, "E",
                           "open physical edge"),
    "UNRESOLVED_EDGE": ("#b00020", "5,5", 3.0, "U", "unresolved gap"),
}
PAD = 900.0


def _svg(cid, identity, chain, status_phys, status_meas) -> str:
    pts = [p for e in chain for p in (e.get("start_mm"), e.get("end_mm"))
           if p]
    if not pts:
        return ""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1 = min(xs) - PAD, max(xs) + PAD
    y0, y1 = min(ys) - PAD, max(ys) + PAD
    w, h = x1 - x0, y1 - y0
    sc = 1100.0 / max(w, h)
    W, H = w * sc, h * sc

    def X(x):
        return (x - x0) * sc

    def Y(y):
        return (y1 - y) * sc        # flip: CAD y grows up, SVG grows down

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" '
           f'height="{H + 170:.0f}" viewBox="0 0 {W:.0f} {H + 170:.0f}">',
           f'<rect width="{W:.0f}" height="{H + 170:.0f}" fill="#fdfdfb"/>',
           '<g font-family="monospace">']
    used = []
    for e in chain:
        a, b = e.get("start_mm"), e.get("end_mm")
        if not a or not b:
            continue
        role = CHAIN_ELEMENT_TO_TOPOLOGICAL_ROLE.get(
            e["CHAIN_ELEMENT"], "UNRESOLVED_EDGE")
        if role == "OPENING":
            role = "SYNTHETIC_MEASUREMENT_BOUNDARY"
        col, dash, wd, glyph, lab = STYLE[role]
        if role not in used:
            used.append(role)
        out.append(
            f'<line x1="{X(a[0]):.1f}" y1="{Y(a[1]):.1f}" '
            f'x2="{X(b[0]):.1f}" y2="{Y(b[1]):.1f}" stroke="{col}" '
            f'stroke-width="{wd}" stroke-dasharray="{dash}" '
            f'stroke-linecap="round"/>')
        if glyph:
            mx, my = X((a[0] + b[0]) / 2), Y((a[1] + b[1]) / 2)
            out.append(
                f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="8.5" '
                f'fill="#fdfdfb" stroke="{col}" stroke-width="1.4"/>'
                f'<text x="{mx:.1f}" y="{my + 4:.1f}" font-size="11" '
                f'text-anchor="middle" fill="{col}">{glyph}</text>')

    yb = H + 22
    out.append(f'<text x="10" y="{yb:.0f}" font-size="15" fill="#111">'
               f'{cid} &#183; {identity}</text>')
    out.append(f'<text x="10" y="{yb + 20:.0f}" font-size="12" fill="#444">'
               f'PHYSICAL_REGION_STATUS = {status_phys}</text>')
    out.append(f'<text x="10" y="{yb + 37:.0f}" font-size="12" fill="#444">'
               f'MEASUREMENT_REGION_STATUS = {status_meas}</text>')
    for i, role in enumerate(used):
        col, dash, wd, glyph, lab = STYLE[role]
        ly = yb + 60 + i * 18
        out.append(f'<line x1="12" y1="{ly - 4:.0f}" x2="52" '
                   f'y2="{ly - 4:.0f}" stroke="{col}" stroke-width="{wd}" '
                   f'stroke-dasharray="{dash}"/>')
        tag = f"[{glyph}] " if glyph else "     "
        out.append(f'<text x="60" y="{ly:.0f}" font-size="11" fill="#333">'
                   f'{tag}{lab} &#183; {role}</text>')
    out.append('<text x="10" y="%.0f" font-size="10" fill="#777">'
               'no area is computed anywhere in this experiment</text>'
               % (yb + 60 + len(used) * 18 + 14))
    out.append("</g></svg>")
    return "\n".join(out)


def main() -> int:
    chains = load("E1_4_PHYSICAL_BOUNDARY_CHAIN_REGISTER.json")
    regions = json.loads(
        (OUT / "MEASUREMENT_REGION_REGISTER.json").read_text("utf-8"))
    st = {r["CANDIDATE_ID"]: r for r in regions["ROWS"]}

    d = OUT / "OVERLAYS"
    d.mkdir(parents=True, exist_ok=True)
    made = []
    for c in chains["CANDIDATES"]:
        cid = c["CANDIDATE_ID"]
        chain = (c.get("CHAIN") or {}).get("CHAIN") or []
        r = st.get(cid, {})
        svg = _svg(cid, c.get("IDENTITY_AS_DRAWN") or "",
                   chain, r.get("PHYSICAL_REGION_STATUS", "?"),
                   r.get("MEASUREMENT_REGION_STATUS", "?"))
        if not svg:
            continue
        p = d / f"{cid}.svg"
        p.write_text(svg, encoding="utf-8")
        made.append(p.name)

    write(OUT / "OVERLAY_INDEX.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "PROTOCOL_HASH": P.protocol_hash(),
        "MEANING_IS_NOT_CARRIED_BY_COLOUR_ALONE": (
            "every class has its own line style and, where it is not the "
            "plain physical boundary, a lettered glyph on the edge and a "
            "named entry in the key. The drawing reads correctly in "
            "greyscale and to a reader who cannot separate the hues"),
        "CLASSES_SHOWN": {k: {"line_style": v[1] or "solid",
                              "glyph": v[3] or "(none)", "label": v[4]}
                          for k, v in STYLE.items()},
        "NO_AREA_IS_COMPUTED": P.NO_AREA_IS_COMPUTED,
        "overlays": len(made),
        "FILES": made,
    })
    print(json.dumps({"overlays": len(made), "dir": str(d)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
