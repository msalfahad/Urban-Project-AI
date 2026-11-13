"""T-752 read-only development-villa run: B13-07 special-metalwork census (t752_metalwork.METALWORK_CENSUS_T752_V1).
Nothing in the repository is written; output goes to --out (outside the repository).

Usage (from the checkout root, through the wrapper):
  bash scripts/agent_env.sh run --tree task-T-752 research/agents_t752/t752_alsenan.py <arch.dxf> <struct.dxf> \
      --out <scratch>/t752_alsenan.json

READING (the person's, by CAD handle; every number below is re-derived from the DXF at run time and asserted):
  * 1F street (SE) face, three PROJECTING MEMBERS (beam ends): 1F plan, overhead layer '2', three closed stubs
    C4A + C51 + C52, C4B + C4F + C50, C4C + C4D + C4E (outer end 0.10 m, two sides 0.30 m) standing outside the 0.20 m
    facade-projection outline C49 (layer 5); SE elevation, three 0.10 x 0.10 squares on layer '1'
    (21F8 21FA 21FC 21FF / 21FB 21FD 21FE 2200 / 21F6 21F7 21F9 2201). Count, spacing and width must agree.
  * annex (dewaneya) street face: six end squares, three over each of W11 / W12, on the FENCE ELEVATION of
    Pages_11-12 p.12 only (raster; not in the DXF; the GF plan draws no overhead stub there): count only, never scaled.
Excluded by id (owned elsewhere), not measured: railings RL-01 .. RL-12 (T-164 / T-393 / T-480), shutters at W14,
W11, W12 (T-164), fence gates G-01 / G-02 = D-GF-15 (T-361 / T-400).

Independent checks: (1) completeness: every overhead-layer LINE of the 1F plan that lies wholly outside the facade
line C49 on that face is one of the nine stub lines; (2) every 0.10 m layer-1 square on the SE elevation at the stub
height band is one of the three squares; (3) a keyword scan of every TEXT / MTEXT / ATTRIB (block contents included)
of both DXFs for metalwork words returns counts only (no text is copied)."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import t752_metalwork as M  # noqa: E402

MM = 1000.0
STUBS = (("C4A", "C51", "C52"), ("C4B", "C4F", "C50"), ("C4C", "C4D", "C4E"))   # (outer end, side, side)
FACADE_OUTLINE = "C49"
SQUARES = (("21F8", "21FA", "21FC", "21FF"), ("21FB", "21FD", "21FE", "2200"), ("21F6", "21F7", "21F9", "2201"))
# SE elevation datum: annex roof line 241A is +4.30 (printed '400' dimension 244D from the +0.30 floor to it)
DATUM_LINE, DATUM_LEVEL, DATUM_DIM = "241A", 4.30, "244D"
W14_DIM = "2B47"                     # W14 printed '160' (sill -> head) on the SE elevation

KEYWORDS = r"canop|pergol|louv|screen|grill|grille|steel|metal|galv|\bSHS\b|\bRHS\b|\bCHS\b|\bIPE\b|\bHE[AB]\b|\bUB\b|" \
           r"\bUC\b|angle|channel|bracket|gate|handrail|balust|ladder|shade|frame|beam end"


def _line(db, h):
    e = db[h]
    if e.dxftype() != "LINE":
        raise ValueError(f"{h} is {e.dxftype()}, expected LINE")
    return (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y), e.dxf.layer


def _len(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1]) / MM


def read_beam_ends(doc):
    db = doc.entitydb
    fa, fb, flay = _line(db, FACADE_OUTLINE)
    if abs(fa[0] - fb[0]) > 0.5:
        raise ValueError("facade outline C49 is expected vertical in the plan's frame")
    fx = fa[0]
    stubs = []
    for end, s1, s2 in STUBS:
        ea, eb, el = _line(db, end)
        sides = [_line(db, s) for s in (s1, s2)]
        if el != "2" or any(s[2] != "2" for s in sides):
            raise ValueError(f"stub {end}: not on the overhead layer '2'")
        width = _len(ea, eb)
        projs = [_len(a, b) for a, b, _ in sides]
        # each side runs from the outer end to the facade outline
        for a, b, _ in sides:
            xs = sorted((a[0], b[0]))
            if abs(xs[1] - fx) > 0.5:
                raise ValueError(f"stub {end}: a side does not stop on C49")
        stubs.append({"refs": [end, s1, s2], "width_m": round(width, 4), "projection_m": round(max(projs), 4),
                      "centre_along_facade": (ea[1] + eb[1]) / 2 / MM, "outer_x": ea[0]})
    # completeness: overhead-layer lines wholly outside C49 within this face's extent
    ylo, yhi = sorted((fa[1], fb[1]))
    side = -1 if stubs[0]["outer_x"] < fx else 1
    found = set()
    for e in doc.modelspace().query("LINE"):
        if e.dxf.layer != "2":
            continue
        a, b = e.dxf.start, e.dxf.end
        if ylo - 1 <= min(a.y, b.y) and max(a.y, b.y) <= yhi + 1 and \
                all(-0.5 <= side * (x - fx) <= 2000.0 for x in (a.x, b.x)) and \
                max(side * (a.x - fx), side * (b.x - fx)) > 1:
            # within 2.0 m outside the face: the plan's own strip (the elevations sit 80+ m away on the sheet)
            found.add(e.dxf.handle)
    expected = {h for s in STUBS for h in s}
    if found != expected:
        raise ValueError(f"overhead lines outside C49 on the 1F SE face: {sorted(found)} != the 9 stub lines")
    return stubs, _len(fa, fb)


def read_squares(doc):
    db = doc.entitydb
    sq = []
    for hs in SQUARES:
        pts = []
        for h in hs:
            a, b, lay = _line(db, h)
            if lay != "1":
                raise ValueError(f"{h}: not layer 1")
            if abs(_len(a, b) - 0.10) > 0.0005:
                raise ValueError(f"{h}: not a 0.10 m side")
            pts += [a, b]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        sq.append({"refs": list(hs), "w_m": round((max(xs) - min(xs)) / MM, 4),
                   "h_m": round((max(ys) - min(ys)) / MM, 4),
                   "centre_x": (max(xs) + min(xs)) / 2 / MM, "y_lo": min(ys), "y_hi": max(ys)})
    # datum
    da, dbb, _ = _line(db, DATUM_LINE)
    dim = db[DATUM_DIM]
    if abs(dim.get_measurement() - 4000.0) > 0.5:
        raise ValueError("datum dimension 244D is not the printed 4.00 m")
    if abs(max(dim.dxf.defpoint2.y, dim.dxf.defpoint3.y) - da[1]) > 0.5:
        raise ValueError("datum line 241A is not the top of the printed 400 dimension")
    lev = lambda y: DATUM_LEVEL + (y - da[1]) / MM  # noqa: E731
    w14 = db[W14_DIM]
    w14_head = lev(max(w14.dxf.defpoint2.y, w14.dxf.defpoint3.y))
    for s in sq:
        s["level_bottom"] = round(lev(s["y_lo"]), 3)
        s["level_top"] = round(lev(s["y_hi"]), 3)
    # completeness: 0.10 m layer-1 squares in the same height band of the SE elevation
    band = (min(s["y_lo"] for s in sq) - 1, max(s["y_hi"] for s in sq) + 1)
    xr = (min(s["centre_x"] for s in sq) * MM - 8000, max(s["centre_x"] for s in sq) * MM + 8000)
    extra = set()
    for e in doc.modelspace().query("LINE"):
        if e.dxf.layer != "1":
            continue
        a, b = e.dxf.start, e.dxf.end
        if band[0] <= min(a.y, b.y) and max(a.y, b.y) <= band[1] and xr[0] <= a.x <= xr[1] and \
                abs(math.dist(a, b) - 100.0) < 0.5:
            extra.add(e.dxf.handle)
    expected = {h for s in SQUARES for h in s}
    if extra != expected:
        raise ValueError(f"0.10 m layer-1 lines in the beam-end band: {sorted(extra)} != the 12 square sides")
    return sq, round(w14_head, 3)


def keyword_counts(doc):
    pat = re.compile(KEYWORDS, re.I)
    n_text, hits = 0, 0
    seen = set()

    def walk(space, depth):
        nonlocal n_text, hits
        for e in space:
            t = e.dxftype()
            if t in ("TEXT", "MTEXT"):
                n_text += 1
                s = e.plain_text() if t == "MTEXT" else e.dxf.text
                hits += bool(pat.search(s or ""))
            elif t == "INSERT":
                for a in e.attribs:
                    n_text += 1
                    hits += bool(pat.search(a.dxf.text or ""))
                name = e.dxf.name
                if depth < 4 and name not in seen:
                    seen.add(name)
                    try:
                        walk(doc.blocks[name], depth + 1)
                    except Exception:  # noqa: BLE001 - a missing block definition is no text
                        pass
    walk(doc.modelspace(), 0)
    return {"texts_scanned": n_text, "metalwork_keyword_hits": hits}


def build(arch_doc, struct_doc):
    stubs, facade_len = read_beam_ends(arch_doc)
    squares, w14_head = read_squares(arch_doc)
    agree = M.plan_elevation_agree([s["centre_along_facade"] for s in stubs], [s["centre_x"] for s in squares],
                                   stubs[0]["width_m"], squares[0]["w_m"])
    if not agree["agree"]:
        raise ValueError(f"plan vs elevation beam ends disagree: {agree}")
    members = []
    for i, s in enumerate(stubs):
        # the visible projection, from the outer end to the facade-projection outline C49 (drawn)
        members.append(M.Member(f"{s['refs'][1]}|{s['refs'][2]}", (0.0, 0.0), (s["projection_m"], 0.0)))
    items = [
        M.Item("MW-1F-SE-BE", M.PROJECTING_MEMBER, "1F", "1F street (SE) face, above W14", 3, M.GEOM_CAD,
               evidence=["1F plan layer 2 stubs " + ", ".join("+".join(s["refs"]) for s in stubs),
                         "SE elevation squares " + ", ".join("/".join(s["refs"]) for s in squares),
                         "SW elevation p.7, NE elevation p.9 and section B-B p.11 draw the end in side view"],
               members=members,
               held_extra=["drawn section 0.10 x 0.10 m but no printed section / designation",
                           "back-span / embedment behind the facade outline not drawn (whole member length HELD)",
                           "fixing and finish not printed"],
               note=f"visible projection beyond the 0.20 m facade outline C49; level by DXF geometry "
                    f"+{squares[0]['level_bottom']:.3f} .. +{squares[0]['level_top']:.3f} (not printed; "
                    f"{squares[0]['level_bottom'] - w14_head:.3f} m above the printed W14 head +{w14_head:.3f})"),
        M.Item("MW-GF-ANX-BE", M.PROJECTING_MEMBER, "GF", "annex (dewaneya) street face, 3 over W11 + 3 over W12",
               6, M.GEOM_RASTER,
               evidence=["Pages_11-12 p.12 FENCE ELEVATION (raster): six end squares; GF plan sheet03 / DXF: no "
                         "overhead stub on that face; no other sheet shows the annex street face"],
               held_extra=["size, projection and section not printed (raster only, never scaled)",
                           "plan does not draw them: projection unknown"]),
    ]
    excluded = [
        M.Item(rid, M.HANDRAIL_FRAME, fl, "railing run", None, M.GEOM_CAD,
               owner_family="B7-09 / B7-11 railing runs (T-164 / T-393 / T-480)", evidence=["RAILINGS_T164.csv"])
        for rid, fl in (("RL-01", "1F roof"), ("RL-02", "1F roof"), ("RL-03", "annex roof"), ("RL-04", "GF roof"),
                        ("RL-05", "GF/1F"), ("RL-06", "1F"), ("RL-07", "GF/1F/2F"), ("RL-08", "GF"),
                        ("RL-09", "GF/1F"), ("RL-10", "fence"), ("RL-11", "GF"), ("RL-12", "GF/1F"))
    ] + [
        M.Item(f"SH-{w}", M.LOUVRE_SCREEN, fl, f"louvred shutter pair at {w}", 2, M.GEOM_CAD,
               owner_family="B6-05 shutters (T-164)", evidence=["T-164 s.1"])
        for w, fl in (("W14", "1F"), ("W11", "GF"), ("W12", "GF"))
    ] + [
        M.Item("G-01", M.GATE, "GF", "street fence gate opening", None, M.GEOM_CAD,
               owner_family="B13-04 boundary fence and gates (T-361 / T-400)", evidence=["GATES_T361.csv"]),
        M.Item("G-02", M.GATE, "GF", "sea-side gate = D-GF-15", 1, M.GEOM_CAD,
               owner_family="B13-04 boundary fence and gates (T-361 / T-400)", evidence=["GATES_T361.csv"]),
    ]
    other_ids = [x.item_id for x in excluded]
    sheets = ("P7757 DXF (GF / 1F / 2F plans, SE + NW elevations), sheet03 (GF), Pages_01-02 (area plans), Pages_05-06 "
              "(2F plan, SE), Pages_07-08 (SW, NW), sheet09 (NE), sheet10 (section A-A), Pages_11-12 (section B-B, "
              "FENCE PLAN / ELEVATION / SECTION), ST7757 DXF (all structural sheets: RC only)")
    not_drawn = [{"kind": k, "searched": sheets, "what": w} for k, w in (
        (M.CANOPY, "no canopy / cantilevered cover outline in any plan (overhead layer included), elevation or "
                   "section; the area plans list no covered area"),
        (M.PERGOLA, "no pergola grid, posts or rafters on any sheet"),
        (M.LOUVRE_SCREEN, "no screen other than the T-164 shutters (EXCLUDED)"),
        (M.HANDRAIL_FRAME, "no handrail frame other than the railing runs (EXCLUDED)"),
        (M.GATE, "no gate other than G-01 / G-02 (EXCLUDED)"))]
    out = M.census(items + excluded, other_family_ids=other_ids, not_drawn=not_drawn)
    out["checks"] = {
        "beam_ends_plan": [{k: v for k, v in s.items() if k in ("refs", "width_m", "projection_m")} for s in stubs],
        "beam_ends_elevation": [{k: v for k, v in s.items() if k in ("refs", "w_m", "h_m", "level_bottom",
                                                                     "level_top")} for s in squares],
        "plan_vs_elevation": agree, "facade_outline_C49_m": round(facade_len, 4), "w14_head_level": w14_head,
        "completeness": "9 overhead stub lines = every layer-2 line outside C49 on the face; 12 square sides = "
                        "every 0.10 m layer-1 line in the band",
        "keywords_arch": keyword_counts(arch_doc), "keywords_struct": keyword_counts(struct_doc)}
    out["not_metalwork"] = [
        {"what": "0.20 m facade-projection outline B3C / B3D / C49 (1F SE face)", "owner": "facade (T-159 / T-162)"},
        {"what": "0.50 m boxes on the annex roof (SE elevation 2428 / 2429 / 242A / 242B / 2426) and on the 1F roof "
                 "(NW elevation 2563 / 27B4 / 27B5)", "owner": "parapets seen beyond (T-162), 0.50 m = parapet height"},
        {"what": "NW pool-court arch glazing (layer W)", "owner": "windows (T-746 frame census)"},
        {"what": "stools 174 / 175 / 176 / 177", "owner": "loose furniture (T-753)"},
        {"what": "'mecvent' blocks A7A / A82 / A85 (text only)", "owner": "B12-04 HVAC: a label, never a unit"},
        {"what": "lift 1.80 x 1.80 shaft", "owner": "lift installation (not B13-07)"}]
    return out


def main(argv=None):
    import ezdxf
    ap = argparse.ArgumentParser()
    ap.add_argument("arch")
    ap.add_argument("struct")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = build(ezdxf.readfile(a.arch), ezdxf.readfile(a.struct))
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    t = out["totals"]
    print(json.dumps({"totals": t, "excluded": len(out["excluded"]), "not_drawn": [x["kind"] for x in out["not_drawn"]],
                      "checks": {k: out["checks"][k] for k in ("plan_vs_elevation", "keywords_arch",
                                                               "keywords_struct", "w14_head_level")},
                      "items": [{k: r[k] for k in ("item_id", "pcs", "member_lm", "kg", "note") if k in r}
                                for r in out["items"]]}, indent=1))


if __name__ == "__main__":
    main()
