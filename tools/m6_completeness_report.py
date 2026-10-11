"""M6 COMPLETENESS REVIEW - one overlay per plan sheet and a review page for engine.source.concrete_completeness.

    sheet_svgs(D, intake, CR) -> {sheet_id: svg}
    html(CR, svgs, banner="") -> the review page (findings by severity, scope checklist, scores, overlays)

The overlays draw the sheet's linework (grey; annotation layers lighter), the member footprints the takeoff holds
(blue), and every located finding as a numbered box coloured by severity. Only geometry and the engine's own
records are drawn: no drawing text is reproduced. Stdlib only.
"""

from __future__ import annotations

import html as _h

from engine.source import concrete_completeness as CC

SEV_COLOUR = {"HIGH": "#c62828", "MEDIUM": "#ef6c00", "LOW": "#6d6d6d", "INFO": "#9e9e9e"}
KIND_COLOUR = {"BAND": "#2a6fdb", "FACE": "#8ab4f8", "COLUMN": "#1b8a3a", "COLUMN_BOX": "#1b8a3a",
               "FOOTING": "#8d5a00", "STRAP_CANDIDATE": "#7b1fa2"}


def _numbered(CR):
    """the located findings in report order, numbered from 1 (the same number on the overlay and in the table)."""
    out, k = {}, 0
    for f in CR["findings"]:
        if f.get("BOX_M") and f["SHEET"]:
            k += 1
            out[f["FINDING_ID"]] = k
    return out


def sheet_svgs(D, intake, CR, width=1400):
    u = D["unit_m"]
    num = _numbered(CR)
    members = CC._members(D)
    out = {}
    for sid, rec in CC._plan_sheets(D):
        sh = next(s for s in D["model"]["sheets"] if s["sheet_id"] == sid)
        box = sh["box"]
        org = sh.get("origin") or (0.0, 0.0)
        sx = width / max(box[2] - box[0], 1e-9)
        H = int((box[3] - box[1]) * sx)
        X = lambda x: (x - box[0]) * sx                        # noqa: E731
        Y = lambda y: H - (y - box[1]) * sx                    # noqa: E731
        o = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {width} {H}' width='100%' "
             f"style='background:#fff'><title>{sid} {_h.escape(str(sh.get('role')))} "
             f"{_h.escape(str(sh.get('storey')))}</title>"]
        for e in CC._entities(D, intake or {}, sid):
            col = "#d9d9d9" if CC.annotation_layer(e["layer"]) else "#7a7a7a"
            if e["type"] == "LINE":
                o.append(f"<line x1='{X(e['a'][0]):.1f}' y1='{Y(e['a'][1]):.1f}' x2='{X(e['b'][0]):.1f}' "
                         f"y2='{Y(e['b'][1]):.1f}' stroke='{col}' stroke-width='0.6'/>")
            elif e["type"] == "ARC":
                pts = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in e["pts"])
                o.append(f"<polyline points='{pts}' fill='none' stroke='{col}' stroke-width='0.6'/>")
            elif e["type"] == "CIRCLE":
                o.append(f"<circle cx='{X(e['c'][0]):.1f}' cy='{Y(e['c'][1]):.1f}' r='{e['r'] * sx:.1f}' "
                         f"fill='none' stroke='{col}' stroke-width='0.6'/>")
        for m in members.get(sid, []):
            c = KIND_COLOUR.get(m["kind"], "#5c6bc0")
            pts = " ".join(f"{X(x):.1f},{Y(y):.1f}" for x, y in m["poly"])
            fill = "none" if m["kind"] == "FACE" else c
            o.append(f"<polygon points='{pts}' fill='{fill}' fill-opacity='0.15' stroke='{c}' stroke-width='0.8'/>")
        for f in CR["findings"]:
            if f["SHEET"] != sid or not f.get("BOX_M") or f["FINDING_ID"] not in num:
                continue
            b = f["BOX_M"]
            x0, y0 = org[0] + b[0] / u, org[1] + b[1] / u
            x1, y1 = org[0] + b[2] / u, org[1] + b[3] / u
            c = SEV_COLOUR[f["SEVERITY"]]
            n = num[f["FINDING_ID"]]
            o.append(f"<rect x='{X(x0) - 4:.1f}' y='{Y(y1) - 4:.1f}' width='{(x1 - x0) * sx + 8:.1f}' "
                     f"height='{(y1 - y0) * sx + 8:.1f}' fill='none' stroke='{c}' stroke-width='1.8'>"
                     f"<title>{n}: {_h.escape(f['KIND'])} {_h.escape(f['FAMILY'])}</title></rect>")
            o.append(f"<text x='{X(x0) - 4:.1f}' y='{Y(y1) - 7:.1f}' font-family='Arial' font-size='13' "
                     f"font-weight='bold' fill='{c}'>{n}</text>")
        o.append("</svg>")
        out[f"{sid}_{sh.get('storey')}"] = "\n".join(o)
    return out


def html(CR, svgs, banner=""):
    num = _numbered(CR)
    sc = CR["scores"]
    css = ("body{font-family:Arial,sans-serif;margin:24px;color:#1d1d1d;background:#fff}"
           "table{border-collapse:collapse;font-size:12px;margin:8px 0 20px}td,th{border:1px solid #ccc;"
           "padding:4px 6px;vertical-align:top;text-align:left}th{background:#eef2f7}.HIGH{color:#c62828;"
           "font-weight:bold}.MEDIUM{color:#ef6c00;font-weight:bold}.LOW{color:#6d6d6d}.muted{color:#666;"
           "font-size:12px}.sheet{margin:16px 0 28px;border:1px solid #ddd;padding:6px}h2{margin-top:28px}")
    head = (f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' "
            f"content='width=device-width,initial-scale=1'><title>Completeness review</title><style>{css}</style>"
            f"</head><body><h1>Concrete completeness review</h1>")
    if banner:
        head += f"<p class='muted'>{_h.escape(banner)}</p>"
    head += ("<p class='muted'>What the drawing shows that the takeoff does not hold. Every row is a question for a "
             "person, never a quantity: nothing here is in any total. A volume is shown only where a printed "
             "section or thickness binds to drawn geometry (never a ratio). NO_EVIDENCE_CONFIRM_ABSENT is not "
             "absence.</p>")
    sc_rows = "".join(f"<tr><th>{_h.escape(k)}</th><td>{_h.escape(str(v))}</td></tr>" for k, v in sc.items()
                      if k != "basis")
    body = f"<h2>Scores</h2><table>{sc_rows}</table>"
    body += ("<h2>Scope checklist</h2><table><tr><th>Family</th><th>State</th><th>Measured items</th>"
             "<th>Unresolved items</th><th>Open findings</th><th>Finding volume m3 (low - high)</th></tr>")
    for r in CR["scope"]:
        body += (f"<tr><td>{_h.escape(r['FAMILY'])}</td><td>{_h.escape(r['STATE'])}</td>"
                 f"<td>{r['MEASURED_ITEMS']}</td><td>{r['UNRESOLVED_ITEMS']}</td><td>{r['OPEN_FINDINGS']}</td>"
                 f"<td>{r['FINDING_VOLUME_LOW_M3']} - {r['FINDING_VOLUME_HIGH_M3']}"
                 f"{' (+' + str(r['FINDINGS_WITHOUT_VOLUME']) + ' without volume)' if r['FINDINGS_WITHOUT_VOLUME'] else ''}"
                 f"</td></tr>")
    body += "</table><h2>Findings</h2><table><tr><th>#</th><th>Severity</th><th>Kind</th><th>Family</th>" \
            "<th>Sheet / storey</th><th>Evidence</th><th>Volume m3</th><th>Action</th></tr>"
    for f in CR["findings"]:
        if f["KIND"] == "UNRESOLVED_ITEMS" and f["SEVERITY"] not in ("HIGH",):
            continue
        n = num.get(f["FINDING_ID"], "")
        vol = "" if f["VOLUME_HIGH_M3"] is None else f"{f['VOLUME_LOW_M3']} - {f['VOLUME_HIGH_M3']}"
        body += (f"<tr><td>{n}</td><td class='{f['SEVERITY']}'>{f['SEVERITY']}</td><td>{_h.escape(f['KIND'])}</td>"
                 f"<td>{_h.escape(f['FAMILY'])}</td><td>{_h.escape(f['SHEET'])} {_h.escape(f['STOREY'])}</td>"
                 f"<td>{_h.escape(f['EVIDENCE'])}</td><td>{vol}</td><td>{_h.escape(f['ACTION'])}</td></tr>")
    body += "</table><h2>Overlays</h2>"
    for name, svg in svgs.items():
        body += f"<div class='sheet'><h3>{_h.escape(name)}</h3>{svg}</div>"
    return head + body + "</body></html>"
