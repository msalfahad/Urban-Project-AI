"""M1 BOQ REPORT - the printable HTML summary of one urban_structural_boq run (a view; it computes nothing new).

Self-contained (inline CSS and SVG, no script, no external asset), deterministic (the caller passes the as-of date),
printable on A4 portrait. Two series colours only, validated for colour-vision deficiency: VERIFIED (blue) and
PROVISIONAL (orange); UNRESOLVED is never drawn as a quantity, only counted. Every bar has a text value next to it and
a table underneath, so nothing is carried by colour alone.
"""

from __future__ import annotations

import html as H
import json

BLOCKER_TEXT = {
    "BEAM_DEPTH_CONVENTION": "State whether the beam schedule depth H includes the slab (RFI-A01).",
    "GB_EXTERIOR_DEPTH": "Dimension the exterior ground beams ('FOLLOW ARCH.') or confirm the plinth levels.",
    "FOUNDING_LEVEL": "Print the founding level of the footings (necks and lift pit hang on it).",
    "NOTE_SCOPE": "Confirm the slab-on-grade note covers every ground-slab face.",
    "RELEASE_RULE_APPROVAL": "Approve the release of columns whose drawn section equals the schedule.",
    "TIE_LINK_HOOK_RULE": "Print the link / tie hook length, bend radius and closure (RFI-A02).",
    "LAP_ANCHORAGE_RULE": "Confirm the lap and anchorage rule applied to column bars.",
    "GB_TITLES_AND_LENGTH_BASIS": "Say whether the p.13 ground-beam titles are exclusive and which span length selects them.",
    "GB_MISSING_DETAIL": "Issue a section for ground beams carrying concentrated loads.",
    "SECTION_CONFLICT": "Resolve drawn-vs-schedule section conflicts.",
    "BEARING_NOT_CONFIRMED": "Confirm lintel bearings (lintel or beam head).",
    "STAIR_LEVELS_AND_WAIST": "Print the stair waist thickness and landing levels.",
    "DOME_RING_DEPTH": "Dimension the dome ring beam depth and position.",
    "CANTILEVER_THICKNESS": "Confirm the thickness of the hatched cantilever portions (RFI-A08).",
    "ARCH_DEPTHS": "Dimension the pool base and wall depths.",
    "MISSING_REBAR_DETAIL": "Issue bar details where only a typical note exists.",
    "MISSING_SECTION": "Tag the untagged beam spans and schedule them.",
    "NOT_PRINTED": "Print the blinding extent and thickness.",
    "COLUMN_SECTION_OR_LEVEL": "Resolve the column section / level conflict.",
    "NOT_REVIEWED": "Review the source-complete quantities under the release rules.",
    "PROFILE_INCOMPLETE": "Complete the drawing profile (layers, sheets, schedule, units).",
    "NO_GENERIC_EXTRACTOR_M1": "This family needs a project stage or a generic extractor (not in M1).",
}


def _e(v):
    return H.escape("" if v is None else str(v))


def _n(v, d=3):
    return "" if v is None else f"{v:,.{d}f}"


def _bar_chart(rows, *, unit, label_key, width=680, decimals=1):
    """Horizontal stacked bars (verified + provisional base) with a low - high whisker, values as text."""
    rows = [r for r in rows if (r["PLANNING_HIGH"] or 0) > 0]
    if not rows:
        return "<p class='muted'>No quantity to draw.</p>"
    lab_w, val_w, bar_h, gap = 210, 150, 16, 10
    plot_w = width - lab_w - val_w
    vmax = max(r["PLANNING_HIGH"] for r in rows) or 1.0
    sx = plot_w / vmax
    h = len(rows) * (bar_h + gap) + 30
    out = [f"<svg class='chart' viewBox='0 0 {width} {h}' role='img' aria-label='{_e(unit)} by {_e(label_key)}'>"]
    for k in range(5):
        x = lab_w + plot_w * k / 4
        out.append(f"<line x1='{x:.1f}' y1='4' x2='{x:.1f}' y2='{h - 22}' class='grid'/>"
                   f"<text x='{x:.1f}' y='{h - 8}' class='tick' text-anchor='middle'>{vmax * k / 4:,.0f}</text>")
    for i, r in enumerate(rows):
        y = 6 + i * (bar_h + gap)
        v, p = r["VERIFIED"] or 0.0, r["PROVISIONAL_BASE"] or 0.0
        lo, hi = r["PLANNING_LOW"], r["PLANNING_HIGH"]
        name = _e(r[label_key])
        tip = (f"{name}: verified {_n(v, decimals)} + provisional {_n(p, decimals)} = planning "
               f"{_n(v + p, decimals)} {unit} (range {_n(lo, decimals)} to {_n(hi, decimals)})")
        out.append(f"<g><title>{tip}</title>")
        out.append(f"<text x='{lab_w - 8}' y='{y + bar_h - 4}' class='lab' text-anchor='end'>{name}</text>")
        if v > 0:
            out.append(f"<rect x='{lab_w}' y='{y}' width='{max(v * sx - 1, 0.5):.2f}' height='{bar_h}' "
                       f"class='s-ver' rx='2'/>")
        if p > 0:
            out.append(f"<rect x='{lab_w + v * sx + (1 if v > 0 else 0):.2f}' y='{y}' "
                       f"width='{max(p * sx - (1 if v > 0 else 0), 0.5):.2f}' height='{bar_h}' class='s-pro' rx='2'/>")
        if hi - lo > 1e-9:
            yc = y + bar_h / 2
            out.append(f"<line x1='{lab_w + lo * sx:.2f}' y1='{yc}' x2='{lab_w + hi * sx:.2f}' y2='{yc}' "
                       f"class='whisk'/><line x1='{lab_w + lo * sx:.2f}' y1='{yc - 5}' x2='{lab_w + lo * sx:.2f}' "
                       f"y2='{yc + 5}' class='whisk'/><line x1='{lab_w + hi * sx:.2f}' y1='{yc - 5}' "
                       f"x2='{lab_w + hi * sx:.2f}' y2='{yc + 5}' class='whisk'/>")
        out.append(f"<text x='{width - val_w + 8}' y='{y + bar_h - 4}' class='val'>{_n(v + p, decimals)} "
                   f"<tspan class='muted'>({_n(lo, decimals)} to {_n(hi, decimals)})</tspan></text></g>")
    out.append("</svg>")
    return "".join(out)


def _table(head, rows, cls="", num=(), widths=None):
    cg = ("<colgroup>" + "".join(f"<col style='width:{w}%'>" for w in widths) + "</colgroup>") if widths else ""
    t = [f"<table class='{cls}{' fixed' if widths else ''}'>{cg}<thead><tr>" +
         "".join(f"<th class='{'num' if j in num else ''}'>{_e(h)}</th>" for j, h in enumerate(head)) +
         "</tr></thead><tbody>"]
    for r in rows:
        t.append("<tr>" + "".join(f"<td class='{'num' if j in num else ''}'>{c}</td>" for j, c in enumerate(r))
                 + "</tr>")
    t.append("</tbody></table>")
    return "".join(t)


def html(R, *, as_of, banner):
    s = R["summary"]
    tot = s["totals"]
    C, S = tot.get("CONCRETE", {}), tot.get("REINFORCEMENT", {})
    RC, PL = s.get("concrete_rc", C), s.get("plain_concrete", {})
    conc = [b for b in R["boq"] if b["SECTION"].startswith("A")]
    steel = [b for b in R["boq"] if b["SECTION"].startswith("B") and b["ITEM"] != "B.UN"]
    st_rows = [dict(b, LABEL=f"{b['DIA_MM']:g} mm") for b in steel]
    fam_rows = [dict(b, LABEL=b["FAMILY"].replace("_", " ").lower()) for b in conc]
    unres_c, unres_s = C.get("N_UNRESOLVED", 0), S.get("N_UNRESOLVED", 0)
    exp = (f"{_n(C.get('UNRESOLVED_EXPOSURE_LOW'), 1)} to {_n(C.get('UNRESOLVED_EXPOSURE_HIGH'), 1)} m3 indicative "
           f"exposure on {C.get('N_UNRESOLVED_WITH_EXPOSURE', 0)} of them" if C.get("N_UNRESOLVED_WITH_EXPOSURE")
           else "no exposure quantified")
    p = []
    p.append(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Structural BOQ estimate</title>
<style>
:root {{ color-scheme: light; --bg:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#8a8984; --rule:#e4e3df;
  --ver:#2a78d6; --pro:#eb6834; --tile:#f3f2ef; --warn:#8a4b00; --warnbg:#fff4e0; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ color-scheme: dark; --bg:#1a1a19;
  --ink:#f0efec; --ink2:#c3c2b7; --muted:#9a998f; --rule:#3a3a37; --ver:#3987e5; --pro:#d95926; --tile:#252523;
  --warn:#ffcf8a; --warnbg:#3a2a10; }} }}
:root[data-theme="dark"] {{ color-scheme: dark; --bg:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --muted:#9a998f;
  --rule:#3a3a37; --ver:#3987e5; --pro:#d95926; --tile:#252523; --warn:#ffcf8a; --warnbg:#3a2a10; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:13px/1.45 Arial, Helvetica, sans-serif; }}
main {{ max-width: 960px; margin: 0 auto; padding: 20px 16px 40px; }}
h1 {{ font-size: 22px; margin: 0 0 4px; }} h2 {{ font-size: 16px; margin: 26px 0 8px; border-bottom: 1px solid var(--rule);
  padding-bottom: 4px; }} h3 {{ font-size: 13px; margin: 14px 0 6px; }}
.muted {{ color: var(--muted); }} .sub {{ color: var(--ink2); margin: 0 0 12px; }}
.banner {{ background: var(--warnbg); color: var(--warn); border-radius: 6px; padding: 8px 12px; font-weight: bold;
  font-size: 12px; }}
.tiles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; margin: 14px 0; }}
.tile {{ background: var(--tile); border-radius: 8px; padding: 10px 12px; }}
.tile .k {{ color: var(--ink2); font-size: 11px; text-transform: uppercase; letter-spacing: .03em; }}
.tile .v {{ font-size: 22px; font-weight: bold; margin-top: 2px; }} .tile .r {{ color: var(--ink2); font-size: 12px; }}
.legend {{ display:flex; gap:16px; font-size:12px; color:var(--ink2); margin: 4px 0 6px; flex-wrap: wrap; }}
.sw {{ display:inline-block; width:12px; height:12px; border-radius:2px; vertical-align:-2px; margin-right:5px; }}
.chart {{ width: 100%; height: auto; display:block; }}
.chart .grid {{ stroke: var(--rule); stroke-width: 1; }} .chart .tick {{ fill: var(--muted); font-size: 10px; }}
.chart .lab {{ fill: var(--ink); font-size: 11px; }} .chart .val {{ fill: var(--ink); font-size: 11px; }}
.chart .muted {{ fill: var(--muted); }} .s-ver {{ fill: var(--ver); }} .s-pro {{ fill: var(--pro); }}
.whisk {{ stroke: var(--ink2); stroke-width: 1.5; }}
.scroll {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; font-size: 11.5px; margin: 6px 0 10px; }}
table.fixed {{ table-layout: fixed; }} table.fixed td {{ overflow-wrap: anywhere; }}
tr {{ break-inside: avoid; }}
th, td {{ border-bottom: 1px solid var(--rule); padding: 4px 6px; text-align: left; vertical-align: top; }}
th {{ color: var(--ink2); font-weight: bold; background: var(--tile); }}
td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
tr.total td {{ font-weight: bold; border-top: 2px solid var(--ink2); }}
.small {{ font-size: 10.5px; }}
ul {{ margin: 4px 0 8px 18px; padding: 0; }}
@media print {{ main {{ max-width: none; padding: 0; }} h2 {{ break-after: avoid; }} svg {{ break-inside: avoid; }}
  .pb {{ break-before: page; }} }}
</style></head><body><main>
<h1>Structural BOQ: planning estimate</h1>
<p class="sub">{_e(s['project'])} &middot; route {_e(s['route'])} &middot; as of {_e(as_of)} &middot; convention set
{_e(s['conventions']['set'])} ({_e(s['conventions']['digest'][:12])})</p>
<div class="banner">{_e(banner)}</div>
<div class="tiles">
 <div class="tile"><div class="k">RC concrete, planning base</div><div class="v">{_n(RC.get('PLANNING_BASE'), 1)} m3</div>
  <div class="r">range {_n(RC.get('PLANNING_LOW'), 1)} to {_n(RC.get('PLANNING_HIGH'), 1)}; plus
  {_n(PL.get('PLANNING_BASE') or 0, 1)} m3 plain blinding</div></div>
 <div class="tile"><div class="k">Concrete, verified</div><div class="v">{_n(C.get('VERIFIED'), 1)} m3</div>
  <div class="r">{C.get('N_VERIFIED', 0)} released items</div></div>
 <div class="tile"><div class="k">Steel, planning base</div><div class="v">{_n((S.get('PLANNING_BASE') or 0) / 1000, 2)} t</div>
  <div class="r">range {_n((S.get('PLANNING_LOW') or 0) / 1000, 2)} to {_n((S.get('PLANNING_HIGH') or 0) / 1000, 2)} t</div></div>
 <div class="tile"><div class="k">Steel, verified</div><div class="v">{_n((S.get('VERIFIED') or 0) / 1000, 2)} t</div>
  <div class="r">{S.get('N_VERIFIED', 0)} released bar rows</div></div>
 <div class="tile"><div class="k">Unresolved, not in totals</div><div class="v">{unres_c + unres_s}</div>
  <div class="r">{unres_c} concrete, {unres_s} steel</div></div>
</div>
<p><b>How to read it.</b> <b>Verified</b> is the only quantity released under the strict rules. <b>Provisional</b> is
calculated from drawn or printed geometry with the assumptions listed below; each provisional item carries one reading
as its base and the others as its range. The <b>planning estimate</b> is verified + provisional base; its low and high
add each item's own low and high (a bracket, not a probability). <b>Unresolved</b> items have no defensible quantity
and are never added: {_e(unres_c)} concrete items ({_e(exp)}) and {_e(unres_s)} reinforcement items. The planning
estimate is therefore <b>not complete</b>.</p>
""")
    p.append("<h2>Concrete by family</h2><div class='legend'><span><span class='sw' style='background:var(--ver)'>"
             "</span>Verified</span><span><span class='sw' style='background:var(--pro)'></span>Provisional (base)"
             "</span><span>&#9500;&#9472;&#9508; planning low to high</span></div>")
    p.append(_bar_chart(fam_rows, unit="m3", label_key="LABEL"))
    body = []
    for b in conc:
        body.append([_e(b["ITEM"]), _e(b["DESCRIPTION"]), _n(b["VERIFIED"]), _n(b["PROVISIONAL_BASE"]),
                     _n(b["PLANNING_LOW"]), f"<b>{_n(b['PLANNING_BASE'])}</b>", _n(b["PLANNING_HIGH"]),
                     _e(b["N_UNRESOLVED"])])
    body.append(["", "<b>Total (RC and plain)</b>", _n(C.get("VERIFIED")), _n(C.get("PROVISIONAL_BASE")), _n(C.get("PLANNING_LOW")),
                 f"<b>{_n(C.get('PLANNING_BASE'))}</b>", _n(C.get("PLANNING_HIGH")), _e(unres_c)])
    p.append("<div class='scroll'>" + _table(["Item", "Description", "Verified m3", "Provisional m3", "Planning low",
                                              "Planning base", "Planning high", "Unresolved"], body,
                                             num=(2, 3, 4, 5, 6, 7)).replace("<tr><td class=''></td><td class=''><b>"
                                                                             "Total", "<tr class='total'><td class=''>"
                                                                             "</td><td class=''><b>Total") + "</div>")
    p.append("<h2 class='pb'>Reinforcement by bar diameter</h2><p class='muted small'>Bar models only (counts, cut "
             "lengths, unit mass d&sup2;/162). No kg/m3 ratio is used anywhere.</p>")
    p.append(_bar_chart(st_rows, unit="kg", label_key="LABEL", decimals=0))
    body = [[_e(f"{b['DIA_MM']:g}"), _n(b["VERIFIED"], 1), _n(b["PROVISIONAL_BASE"], 1), _n(b["PLANNING_LOW"], 1),
             f"<b>{_n(b['PLANNING_BASE'], 1)}</b>", _n(b["PLANNING_HIGH"], 1), _n(b["PLANNING_BASE"] / 1000, 3)]
            for b in steel]
    body.append(["<b>Total</b>", _n(S.get("VERIFIED"), 1), _n(S.get("PROVISIONAL_BASE"), 1),
                 _n(S.get("PLANNING_LOW"), 1), f"<b>{_n(S.get('PLANNING_BASE'), 1)}</b>",
                 _n(S.get("PLANNING_HIGH"), 1), _n((S.get("PLANNING_BASE") or 0) / 1000, 3)])
    p.append(_table(["Diameter mm", "Verified kg", "Provisional kg", "Planning low kg", "Planning base kg",
                     "Planning high kg", "Planning base t"], body, num=(1, 2, 3, 4, 5, 6)))
    p.append(f"<p class='muted small'>{_e(unres_s)} reinforcement items have no bar model (unresolved) and are not "
             "in this table.</p>")
    fl = [r for r in R["floor"] if r["trade"] == "CONCRETE"]
    by = {}
    for r in fl:
        a = by.setdefault(r["storey"], [0.0, 0.0, 0.0, 0.0, 0])
        a[0] += r["VERIFIED"]
        a[1] += r["PROVISIONAL_BASE"]
        a[2] += r["PLANNING_LOW"]
        a[3] += r["PLANNING_HIGH"]
        a[4] += r["N_UNRESOLVED"]
    p.append("<h2>Concrete by storey</h2>")
    p.append(_table(["Storey", "Verified m3", "Provisional m3", "Planning base m3", "Range", "Unresolved"],
                    [[_e(k), _n(v[0]), _n(v[1]), f"<b>{_n(v[0] + v[1])}</b>", f"{_n(v[2], 1)} to {_n(v[3], 1)}",
                      _e(v[4])] for k, v in by.items()], num=(1, 2, 3, 4, 5)))
    p.append("<p class='muted small'>Storey ALL holds items not split by storey (corner squares, aggregated bars).</p>")
    p.append("<h2 class='pb'>What holds the rest back</h2><p class='muted small'>Ranked by provisional and unresolved "
             "upper quantity (m3 + kg / 100). Each line is a question for the designer.</p>")
    rows = []
    for b in R["blockers"][:12]:
        rows.append([_e(b["BLOCKER"]), _e(BLOCKER_TEXT.get(b["BLOCKER"], "")), _e(", ".join(b["FAMILIES"])[:60]),
                     _n(b["PROVISIONAL_M3_BASE"], 1), _n(b["M3_UPPER"], 1), _n(b["PROVISIONAL_KG_BASE"], 0),
                     _e(b["N_PROVISIONAL"]), _e(b["N_UNRESOLVED"])])
    p.append("<div class='scroll'>" + _table(["Blocker", "What would unlock it", "Families", "Prov. m3", "Upper m3",
                                              "Prov. kg", "Prov. items", "Unres. items"], rows, cls="small",
                                             num=(3, 4, 5, 6, 7), widths=(19, 31, 18, 7, 7, 7, 5.5, 5.5)) + "</div>")
    if R["sensitivity"]:
        sens = sorted(R["sensitivity"], key=lambda r: (-abs(r["CONCRETE_M3_DELTA"]) - abs(r["STEEL_KG_DELTA"]) / 100,
                                                        r["CONVENTION_ID"], str(r["ALTERNATIVE"])))
        p.append("<h2>Sensitivity: one assumption at a time</h2><p class='muted small'>Change of the planning base "
                 "when one assumption takes its alternative and every other stays at base.</p>")
        p.append(_table(["Assumption", "Base", "Alternative", "Items", "Concrete m3", "Steel kg"],
                        [[_e(r["CONVENTION_ID"]), _e(r["BASE"]), _e(r["ALTERNATIVE"]), _e(r["ITEMS_USING"]),
                          f"{r['CONCRETE_M3_DELTA']:+,.3f}", f"{r['STEEL_KG_DELTA']:+,.1f}"] for r in sens[:16]],
                        cls="small", num=(3, 4, 5)))
    used = {a for i in R["items"] for a in i["assumptions"]}
    conv = sorted(R["conv"].items.values(), key=lambda c: c["id"])
    p.append("<h2 class='pb'>Assumptions in force</h2><p class='muted small'>Every provisional quantity names the "
             "assumptions it uses. Change one with <code>--set ID=VALUE</code> and re-run; nothing is edited by hand."
             "</p>")
    rows = []
    for c in conv:
        if c["id"] not in used:
            continue
        rng = (" / ".join(str(o) for o in c["options"]) if c["kind"] == "choice"
               else f"{c['low']:g} to {c['high']:g} {c.get('unit', '')}")
        rows.append([_e(c["id"]), _e(c["base"]), _e(rng), _e(c["provenance"].replace("_", " ").lower()),
                     _e(c["rationale"])])
    p.append(_table(["Assumption", "Base", "Alternatives / range", "Provenance", "Why"], rows, cls="small",
                    widths=(21, 12, 17, 11, 39)))
    ek = {}
    for e in R["exceptions"]:
        ek[e["KIND"]] = ek.get(e["KIND"], 0) + 1
    p.append("<h2>Exceptions</h2>")
    p.append(_table(["Kind", "Count"], [[_e(k), _e(v)] for k, v in sorted(ek.items())], num=(1,)))
    p.append("<p class='muted small'>The full list, with each item's source and limitation, is EXCEPTIONS.csv and the "
             "EXCEPTIONS sheet of the workbook.</p>")
    p.append("<h2>Inputs and checks</h2>")
    p.append(_table(["File", "Kind", "sha256", "Note"],
                    [[_e(i["file"]), _e(i["kind"]), f"<code>{_e(i['sha256'][:16])}</code>",
                      _e(i.get("error") or (f"{i['pages']} pages" if "pages" in i else ""))] for i in s["inputs"]],
                    cls="small"))
    if s.get("frozen_manifests_verified"):
        p.append(f"<p class='small'>{len(s['frozen_manifests_verified'])} frozen stage manifests verified unchanged "
                 "before the estimate was built.</p>")
    if R.get("coverage"):
        cov = {}
        for r in R["coverage"]:
            cov[r["M1"]] = cov.get(r["M1"], 0) + 1
        p.append("<p class='small'>Coverage of the frozen component inventory: " +
                 ", ".join(f"{_e(k)} {v}" for k, v in sorted(cov.items())) + ".</p>")
    p.append("<p class='muted small'>Generated by tools/urban_structural_boq.py. Summary: " +
             _e(json.dumps({k: s[k] for k in ("route", "n_items", "n_exceptions")})) + "</p>")
    p.append("</main></body></html>\n")
    return "".join(p)
