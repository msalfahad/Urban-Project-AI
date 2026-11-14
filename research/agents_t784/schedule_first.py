"""T-784 schedule-first structure on the Alsenan ST DXF (research only; no candidate line changes).

Reads the structural DXF from the private folder (path argument; never stored in the repo), takes the footing and the
column schedules with the frozen SCHEDULE_READER_V1 (attribute rows), binds the marks to the plan symbols with
SCHEDULE_TABLES_V1 (drawn outlines counted, not tags) and puts count x B x D x H beside the T-778 per-element figures.

Plans (drawing units mm, regions by the drawn member clusters of the sheet):
  FOUNDATION  footings (S-FOOTINGS outlines) + C/F tags        x 119000 .. 165000
  SETOUT      column setting-out plan (S-COL.BON at the 0.30 neck width, C.. tags): the TAG SOURCE x 80000 .. 113000
  NECK        neck plan ('30X..' section tags, C.. tags)        x 168000 .. 190000
  GF / 1F / 2F_COLS  the slab plans: column outlines drawn UNTAGGED at the storey section; the setting-out tags are
              carried over by the grid translation (align_offset), then bound to the storey band of the schedule.
Heights: storey frame slab top to slab top 4.50 / 4.20 / 4.20 m (owner storey rule Q-72; DEFAULT label, the T-778 /
candidate frame); footings: the schedule thickness; necks: HELD (founding datum, owner Q-21), section and count only.

usage: python3 -I research/agents_t784/schedule_first.py <ST dxf> [--out research/agents_t784/out]
       python3 -I research/agents_t784/schedule_first.py --check   (re-derives the md from the json)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from engine.source import schedule_reader as SR          # noqa: E402  (frozen, read only)
from engine.source import schedule_tables_v1 as ST       # noqa: E402

UNIT_M = 0.001
REGIONS = {"FOUNDATION": (119000, 165000), "SETOUT": (80000, 113000), "NECK": (168000, 190000),
           "GF_COLS": (42000, 74000), "1F_COLS": (13000, 34000), "2F_COLS": (-21000, -12000)}
STOREYS = (("GF", "GF_COLS", 4.50), ("1F", "1F_COLS", 4.20), ("2F", "2F_COLS", 4.20))
Y_RANGE = (35000, 51000)
T778 = {  # research/agents_t778/out/NONBEAM_CAUSES.md (merged eff624c2): engine per element / per mark
    "FOOTING_m3": 66.5790, "NECK_m3": 10.3413,
    "NECK_n": {"C1": 1, "C2": 4, "C3": 6, "C4": 2, "C5": 3, "C6": 1, "C7": 1, "C8": 2, "C9": 2, "C10": 1, "C11": 2,
               "C": 5, "CN": 6},
    "GF_n": {"C": 5, "C1": 1, "C10": 1, "C11": 2, "C2": 4, "C3": 6, "C4": 2, "C5": 3, "C6": 1, "C7": 1, "C8": 2,
             "C9": 2},
    "1F_n": {"C1": 1, "C2": 4, "C3": 2, "C4": 2, "C5": 3, "C6": 1, "C7": 1, "C8": 2, "C9": 2, "PC1": 1, "PC2": 1},
    "1F_m3": {"C1": 0.42, "C2": 1.68, "C3": 0.84, "C4": 0.84, "C5": 1.26, "C6": 0.504, "C7": 0.672, "C8": 1.596,
              "C9": 1.512, "PC1": 0.42, "PC2": 0.588},
    "2F_n": {"C1": 1, "C2": 4, "C3": 1, "C5": 1, "C9": 1, "PC": 1},
    "2F_m3": {"C1": 0.4075, "C2": 1.6425, "C3": 0.42, "C5": 0.4075, "C9": 0.5705, "PC": 0.3325},
    "GF_m3": {"C": 2.0625, "C1": 0.45, "C10": 0.7875, "C11": 2.475, "C2": 1.8, "C3": 3.1319, "C4": 1.125,
              "C5": 2.13, "C6": 0.7875, "C7": 0.9, "C8": 1.9125, "C9": 2.25},
}

# named causes of (schedule-first - T-778 engine) per element, m3 (closed to 5e-5: T-778 prints 4 decimals); each from the candidate V3.0.84 line records of the
# T-778 families (element ids by position) against the rows above. The md check asserts they close the difference.
CAUSES = {
    "FOOTING": [
        ("F10 + F one drawn outline 3.25 x 1.40 x 0.50 (owner Q-31 C 'bigger area' = the outline) vs schedule rows "
         "F10 1.96 + F 0.216", -0.099, "RULE_DIFFERENCE (Q-31 C governs the candidate)"),
        ("FN clipped by F9: notch 0.40 x 0.35 x 0.30 owned by F9 (R-CONC-OWN-1); schedule-first counts the full FN",
         +0.042, "ENGINE_RIGHT (T-233)")],
    "GF": [
        ("10AE annex position (C3 / C CONFLICT, T-566): the setting-out plan tags it C (a symbol block) and draws it "
         "0.20 x 0.40; schedule-first takes mark C at the schedule GF 20 x 50 (schedule governs a column) vs engine C3 "
         "drawn 0.08 m2: section (0.10 - 0.08) x 3.875", +0.0775, "SCHEDULE_RIGHT on the section (company default); "
         "the drawn 0.20 x 0.40 goes to the designer list"),
        ("storey frame: engine drawing-read bases (annex 3.875 on 4 C / C3 members incl. 10AE, +0.25 base 5.20 on C3 "
         "and C5) vs the flat 4.50 DEFAULT here", +0.135625, "ENGINE_RIGHT (T-576 BASE; heights are not in the "
         "schedule)"),
        ("10E0 mark: setting-out tag C7 and drawn 0.25 x 0.80 agree on C7; engine labels it C8 at the same volume",
         0.0, "mark only (C7 +0.90 / C8 -0.90)")],
    "1F": [
        ("PC1 / PC2: no row in the column schedule (1ST band); engine carries them", -1.008,
         "UNRESOLVED (designer list: NOT_IN_SCHEDULE)"),
        ("10E0 1F: engine takes the drawn 0.25 x 0.80; schedule 1ST C7 20 x 80 governs (company default)", -0.168,
         "SCHEDULE_RIGHT (company default 'schedule governs a column')")],
    "2F": [
        ("PC: no row in the column schedule (2ND band)", -0.3325, "UNRESOLVED (designer list)"),
        ("storey 4.20 DEFAULT here vs engine 4.075 (13.90 - 0.175 roof DEFAULT - 9.65) on C1, C2 x3, C5, C9", +0.08,
         "ENGINE_RIGHT (closer drawing read; both carry a DEFAULT)")],
}


def _in(region, x, y):
    a, b = REGIONS[region]
    return a <= x <= b and Y_RANGE[0] <= y <= Y_RANGE[1]


def load(path):
    import ezdxf
    d = ezdxf.readfile(path)
    m = d.modelspace()
    attrs, texts, polys, lines = [], [], [], []
    for i, e in enumerate(m.query("INSERT")):
        for a in e.attribs:
            attrs.append({"owner": i, "tag": a.dxf.tag, "value": a.dxf.text, "x": e.dxf.insert.x, "y": e.dxf.insert.y})
    # symbol blocks: a block of ONE closed polyline (a footing drawn as a scaled unit square) is an outline; a block
    # of ONE text (a 'C/F' or 'C11/F11' label) is a tag. Both exploded into model space at their insert transform.
    for e in m.query("INSERT"):
        if e.attribs:
            continue
        ve = list(e.virtual_entities())
        if len(ve) != 1:
            continue
        v = ve[0]
        if v.dxftype() == "TEXT":
            texts.append({"value": v.dxf.text.strip(), "x": v.dxf.insert.x, "y": v.dxf.insert.y, "layer": v.dxf.layer,
                          "block": e.dxf.name})
        elif v.dxftype() == "LWPOLYLINE" and v.closed:
            polys.append({"layer": v.dxf.layer, "pts": [(p[0], p[1]) for p in v.get_points()], "closed": True,
                          "h": "B" + e.dxf.handle})
    for e in m.query("TEXT"):
        texts.append({"value": e.dxf.text.strip(), "x": e.dxf.insert.x, "y": e.dxf.insert.y, "layer": e.dxf.layer})
    for e in m.query("LWPOLYLINE"):
        polys.append({"layer": e.dxf.layer, "pts": [(p[0], p[1]) for p in e.get_points()], "closed": e.closed,
                      "h": e.dxf.handle})
    for e in m.query("LINE"):
        lines.append({"layer": e.dxf.layer, "a": (e.dxf.start.x, e.dxf.start.y), "b": (e.dxf.end.x, e.dxf.end.y),
                      "h": e.dxf.handle})
    return attrs, texts, polys, lines


def _boxes(polys, lines, layer, eps=1.0):
    """axis-aligned rectangles: 4-corner polylines + rectangles closed by four separate LINEs of the layer."""
    out = {}
    for p in polys:
        if p["layer"] != layer:
            continue
        pts = p["pts"][:-1] if len(p["pts"]) == 5 and p["pts"][0] == p["pts"][-1] else p["pts"]
        xs = sorted({round(q[0]) for q in pts})
        ys = sorted({round(q[1]) for q in pts})
        if len(pts) == 4 and len(xs) == 2 and len(ys) == 2:
            out[(xs[0], ys[0], xs[1], ys[1])] = "P" + p["h"]
    H, V = [], []
    for ln in lines:
        if ln["layer"] != layer:
            continue
        (x1, y1), (x2, y2) = ln["a"], ln["b"]
        if abs(y1 - y2) <= eps:
            H.append((min(x1, x2), max(x1, x2), (y1 + y2) / 2))
        elif abs(x1 - x2) <= eps:
            V.append((min(y1, y2), max(y1, y2), (x1 + x2) / 2))
    for i, h1 in enumerate(H):
        for h2 in H[i + 1:]:
            if abs(h1[0] - h2[0]) > eps or abs(h1[1] - h2[1]) > eps or abs(h1[2] - h2[2]) <= eps:
                continue
            y0, y1 = sorted((h1[2], h2[2]))
            left = any(abs(v[2] - h1[0]) <= eps and v[0] <= y0 + eps and v[1] >= y1 - eps for v in V)
            right = any(abs(v[2] - h1[1]) <= eps and v[0] <= y0 + eps and v[1] >= y1 - eps for v in V)
            if left and right:
                out.setdefault((round(h1[0]), round(y0), round(h1[1]), round(y1)), f"L{len(out)}")
    return [{"id": f"{v}@{k[0]},{k[1]}", "cx": (k[0] + k[2]) / 2, "cy": (k[1] + k[3]) / 2, "a": k[2] - k[0],
             "b": k[3] - k[1]} for k, v in sorted(out.items())]


def _tags(texts, region, rx):
    return [{"mark": t["value"], "x": t["x"], "y": t["y"]} for t in texts
            if _in(region, t["x"], t["y"]) and re.fullmatch(rx, t["value"].replace(" ", ""))]


def run(path):
    attrs, texts, polys, lines = load(path)
    S = SR.from_attribute_rows(attrs)
    res = {"policy": ST.POLICY_ID, "schedule_conflicts": S["conflicts"], "units": {k: v["unit"] for k, v in
                                                                                      S["families"].items()}}
    # FOOTINGS
    frows = ST.rows_from_reader(S, families={"FOOTING"})
    fo = [o for o in _boxes(polys, lines, "S-FOOTINGS") if _in("FOUNDATION", o["cx"], o["cy"])]
    ftags = [t for t in _tags(texts, "FOUNDATION", r"(C[0-9]*N?/)?F[0-9NF]*") if re.search(r"F", t["mark"])]
    ftags = [dict(t, mark=t["mark"].split("/")[-1]) for t in ftags]
    fb = ST.bind(frows, ftags, fo, tol=2500, size_tol=0.02, unit_m=UNIT_M)
    fq = ST.quantities(frows, fb)
    res["FOOTING"] = {"bind": _slim(fb), "q": fq, "t778_m3": T778["FOOTING_m3"]}
    # NECKS: the setting-out plan draws the members at the FOU band section with its own tags; the neck plan
    # (own '30X..' + C tags) is the cross-check count
    crows = [r for r in ST.rows_from_reader(S, band="FOUNDATION", families={"COLUMN"}) if "B" in r["dims_m"]]
    for key, region in (("NECK", "SETOUT"), ("NECK_PLAN_CHECK", "NECK")):
        co = [o for o in _boxes(polys, lines, "S-COL.BON") if _in(region, o["cx"], o["cy"])]
        ctags = [dict(t, mark=t["mark"].split("/")[0]) for t in _tags(texts, region, r"C[0-9]*N?(/F[0-9N]*)?")]
        cb = ST.bind(crows, ctags, co, tol=1200, size_tol=0.02, unit_m=UNIT_M)
        res[key] = {"bind": _slim(cb), "q": ST.quantities(crows, cb), "t778_n": T778["NECK_n"],
                    "n_outlines": len(co), "n_tags": len(ctags)}
    # STOREY COLUMNS: setting-out tags carried onto each slab plan
    so = [o for o in _boxes(polys, lines, "S-COL.BON") if _in("SETOUT", o["cx"], o["cy"])]
    stags = [dict(t, mark=t["mark"].split("/")[0]) for t in _tags(texts, "SETOUT", r"C[0-9]*N?(/F[0-9N]*)?")]
    band_of = {"GF": "GF", "1F": "1F", "2F": "2F"}
    for st, region, h in STOREYS:
        rows = [r for r in ST.rows_from_reader(S, band=band_of[st], families={"COLUMN"}) if "B" in r["dims_m"]]
        dst = [o for o in _boxes(polys, lines, "S-COL.BON") if _in(region, o["cx"], o["cy"])]
        off = ST.align_offset(so, dst, snap=100.0)
        tags = [dict(t, x=t["x"] + off["dx"], y=t["y"] + off["dy"]) for t in stags] if off else []
        b = ST.bind(rows, tags, dst, tol=1200, size_tol=0.02, unit_m=UNIT_M, carried=True)
        res[st + "_COLUMN"] = {"bind": _slim(b), "q": ST.quantities(rows, b, height_m=h), "offset": off, "H": h,
                               "t778_n": T778[st + "_n"], "t778_m3": T778[st + "_m3"], "n_outlines": len(dst),
                               "n_tags": len(tags)}
    return res


def _slim(b):
    return {"by_mark": b["by_mark"], "designer": [{k: v for k, v in d.items() if k != "tag_xy"} for d in
                                                   b["designer"]]}


def md(res):
    L = ["# T-784 SCHEDULE-FIRST STRUCTURE (Alsenan; method every villa): footings, GF columns, necks", "",
         "Schedule (frozen SCHEDULE_READER_V1, attribute rows) -> SCHEDULE_TABLES_V1 bind (drawn outlines counted, "
         "not tags) -> count x B x D x H. Research only: no candidate line changed. Units inferred: "
         + ", ".join(f"{k} {v}" for k, v in sorted(res["units"].items())) + ".", ""]
    f = res["FOOTING"]
    L += ["## Footings", "", f"Schedule-first **{f['q']['total_m3']:.4f} m3** (held marks: "
          f"{', '.join(f['q']['held_marks']) or 'none'}) vs T-778 engine **{f['t778_m3']:.4f} m3**: "
          f"**{f['q']['total_m3'] - f['t778_m3']:+.4f} m3 ({(f['q']['total_m3'] / f['t778_m3'] - 1) * 100:+.1f} %)**.",
          "", "| mark | count | by status | B | D | H | m3 |", "|---|---|---|---|---|---|---|"]
    L += [_row(l) for l in f["q"]["lines"]]
    for st, _, _ in STOREYS:
        g = res[st + "_COLUMN"]
        t = sum(g["t778_m3"].values())
        L += ["", f"## {st} columns (H {g['H']:.2f} DEFAULT storey frame; tags carried by offset {g['offset']})", "",
              f"Schedule-first **{g['q']['total_m3']:.4f} m3** vs T-778 {st} **{t:.4f} m3**: "
              f"**{g['q']['total_m3'] - t:+.4f} m3 ({(g['q']['total_m3'] / t - 1) * 100:+.1f} %)**. "
              f"Outlines {g['n_outlines']}, tags {g['n_tags']}; held marks {', '.join(g['q']['held_marks']) or 'none'}.",
              "", "| mark | count | T-778 n | by status | B | D | H | m3 | T-778 m3 |", "|---|---|---|---|---|---|---|---|---|"]
        for l in g["q"]["lines"]:
            L.append(_row(l, g["t778_n"].get(l["mark"], 0), g["t778_m3"].get(l["mark"], 0.0)))
        for mk in sorted(set(g["t778_m3"]) - {l["mark"] for l in g["q"]["lines"]}):
            L.append(f"| {mk} | - | {g['t778_n'][mk]} | NOT_IN_SCHEDULE_BAND | - | - | - | - | {g['t778_m3'][mk]} |")
    n, nc = res["NECK"], res["NECK_PLAN_CHECK"]
    cc = {l["mark"]: l["count"] for l in nc["q"]["lines"]}
    L += ["", "## Necks (setting-out plan at the FOU band; section and count; heights HELD: founding datum Q-21)", "",
          f"Outlines {n['n_outlines']}, tags {n['n_tags']}; neck-plan cross-check outlines {nc['n_outlines']}, tags "
          f"{nc['n_tags']}. T-778 engine {T778['NECK_m3']:.4f} m3. Plan area by schedule (count x B x D): "
          f"{sum((l['count'] or 0) * l['B'] * l['D'] for l in n['q']['lines'] if l['B']):.4f} m2.", "",
          "| mark | count | T-778 n | by status | B | D | H | m3 | neck-plan count |", "|---|---|---|---|---|---|---|---|---|"]
    for l in n["q"]["lines"]:
        L.append(_row(l, n["t778_n"].get(l["mark"], 0), cc.get(l["mark"]) or "-"))
    L += ["", "## Named differences (schedule-first - T-778 engine, m3)", "", "| element | cause | m3 | verdict |",
          "|---|---|---|---|"]
    diffs = {"FOOTING": res["FOOTING"]["q"]["total_m3"] - res["FOOTING"]["t778_m3"]}
    for st, _, _ in STOREYS:
        diffs[st] = res[st + "_COLUMN"]["q"]["total_m3"] - sum(res[st + "_COLUMN"]["t778_m3"].values())
    for el, cs in CAUSES.items():
        for c, v, verdict in cs:
            L.append(f"| {el} | {c} | {v:+.6f} | {verdict} |")
        r = diffs[el] - sum(v for _, v, _ in cs)
        L.append(f"| {el} | residual | {r:+.6f} | {'CLOSED' if abs(r) < 5e-5 else 'OPEN'} |")
    L += ["", "## Designer list (outline vs schedule; no owner question)", "", "| element | mark | status | detail |",
          "|---|---|---|---|"]
    for el in ("FOOTING", "GF_COLUMN", "1F_COLUMN", "2F_COLUMN", "NECK", "NECK_PLAN_CHECK"):
        for d in res[el]["bind"]["designer"]:
            det = {k: v for k, v in d.items() if k not in ("mark", "status")}
            L.append(f"| {el} | {d.get('mark') or '-'} | {d['status']} | {json.dumps(det, sort_keys=True)} |")
    return "\n".join(L) + "\n"


def _row(l, n778=None, m778=None):
    v = "HELD" if l["volume_m3"] is None else f"{l['volume_m3']:.4f}"
    b = ", ".join(f"{k} {c}" for k, c in sorted(l["by_status"].items())) or l["status"]
    s = (f"| {l['mark']} | {l['count'] or '-'} |" + (f" {n778 if n778 is not None else '-'} |"
                                                     if n778 is not None or m778 is not None else "")
         + f" {b} | {l['B']} | {l['D']} | {l['H']} | {v} |")
    if m778 is not None:
        s += f" {m778} |"
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf", nargs="?")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "out"))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    jp, mp = os.path.join(a.out, "SCHEDULE_FIRST.json"), os.path.join(a.out, "SCHEDULE_FIRST.md")
    if a.check:
        res = json.load(open(jp))
        ok = open(mp).read() == md(res)
        print("CHECK", "OK" if ok else "MISMATCH")
        sys.exit(0 if ok else 1)
    res = run(a.dxf)
    os.makedirs(a.out, exist_ok=True)
    json.dump(res, open(jp, "w"), indent=1, sort_keys=True, default=list)
    open(mp, "w").write(md(json.loads(json.dumps(res, default=list))))
    print(open(mp).read())


if __name__ == "__main__":
    main()
