"""T-217 extractor: every column instance x storey, the printed / drawn section sources (values and DXF handles only).

Reads the private copy of Drive "Alsenan chalet project" / 'ST7757 dxf.dxf' (sha256 9f9d1179...) from .work/private and
writes ALSENAN_SECTION_INPUT.json (no coordinates, no drawing content: handles, marks, sizes in mm / cm).

Sheets (frame titles are blocks FP / CAP / GBP / GFRS / FFRS / SFRS). The six plan frames are one drawing repeated at a
fixed pitch (one translation per frame onto the FOUNDATION PLAN, every outline of CAP / GBP / FP on each other, T-205):
    FP   FOUNDATION PLAN           neck outlines (S-COL.BON), labels           storey FOUNDATION (schedule band FOU)
    CAP  COLUMN & AXIS PLAN        neck outlines, labels, size texts 'WxD', locating dimension chains (S-DIM1)  FOU
    GBP  GROUND BEAMS PLAN         neck outlines                                FOU
    GFRS GROUND FLOOR ROOF SLAB    outlines of the columns under that slab      GF  (band GR)
    FFRS FIRST FLOOR ROOF SLAB     outlines of the columns under that slab      1F  (band 1ST)
    SFRS SECOND FLOOR ROOF SLAB    outlines of the columns under that slab      2F  (band 2ND)
Mark of each instance: the FP label -> outline binding of T-205 (merged 5f40dfdb, Checker 11:52), file
research/agents_t205/ALSENAN_NECK_INPUT.json; CAP labels re-bound here one to one (every CAP mark = the FP mark).

    python3 -I research/agents_t217/t217_extract.py <path to ST7757 dxf> [--write]
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
PITCH = 38724.406108773          # frame pitch in drawing units (mm), measured: CAP / GBP outlines 34-36 / 36 coincide
FRAME_INDEX = {0: "FP", -1: "CAP", 1: "GBP", 2: "GFRS", 3: "FFRS", 4: "SFRS"}
STOREY = {"FP": "FOUNDATION", "CAP": "FOUNDATION", "GBP": "FOUNDATION", "GFRS": "GF", "FFRS": "1F", "SFRS": "2F"}
BAND = {"FOUNDATION": "FOU", "GF": "GR", "1F": "1ST", "2F": "2ND"}
FP_CENTRE_X = 135500.0           # inside the FOUNDATION PLAN column field; frame index = round((FP_CENTRE_X - x) / PITCH)
MATCH_TOL = 400.0                # mm: a column outline above a neck is centred within half the section change
DIM_TOL = 60.0                   # mm: a dimension defpoint belongs to a face when within this of the outline


def _txt(e):
    return e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text


def extract(path: Path) -> dict:
    import ezdxf
    from ezdxf import bbox
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise SystemExit("not the route G input (sha256 differs)")
    msp = ezdxf.readfile(str(path)).modelspace()
    rects = []
    for e in msp.query('LWPOLYLINE[layer=="S-COL.BON"]'):
        b = bbox.extents([e])
        fr = FRAME_INDEX.get(round((FP_CENTRE_X - b.center.x) / PITCH))
        if fr:
            rects.append({"h": e.dxf.handle, "fr": fr, "cx": b.center.x, "cy": b.center.y,
                          "w": round(b.size.x), "d": round(b.size.y)})
    for r in rects:  # position on the FOUNDATION PLAN
        n = [k for k, v in FRAME_INDEX.items() if v == r["fr"]][0]
        r["fx"], r["fy"] = r["cx"] + n * PITCH, r["cy"]
    # column hatch inside each outline: SOLID = the member of this plan's storey (the column under the slab);
    # a pattern (ANSI35, legend 'Planted column (P.C)' / the turned part of a 'T.C') = a member that STARTS on this slab
    hatches = []
    for e in msp.query('HATCH[layer=="S-COL.HAT"]'):
        b = bbox.extents([e])
        if b.has_data:
            hatches.append((b.center.x, b.center.y, b.size.x, b.size.y, e.dxf.pattern_name))
    for r in rects:
        pats = {h[4] for h in hatches if abs(h[0] - r["cx"]) <= r["w"] / 2 + 5 and abs(h[1] - r["cy"]) <= r["d"] / 2 + 5
                and h[2] <= r["w"] + 10 and h[3] <= r["d"] + 10}
        r["hatch"] = "SOLID" if pats == {"SOLID"} else ("PATTERN" if pats and "SOLID" not in pats else
                                                          ("NONE" if not pats else "MIXED"))
    dims = []
    for d in msp.query("DIMENSION"):
        a, b = d.dxf.get("defpoint2"), d.dxf.get("defpoint3")
        if a is None or b is None:
            continue
        dims.append({"h": d.dxf.handle, "m": d.get_measurement(), "a": (a.x, a.y), "b": (b.x, b.y)})
    labels, sizes = [], []
    def take(e, h):
        t = _txt(e).strip()
        p = e.dxf.insert
        if FRAME_INDEX.get(round((FP_CENTRE_X - p.x) / PITCH)) != "CAP":
            return
        if re.fullmatch(r"C\d{0,2}|CN", t):
            labels.append({"t": t, "h": h, "x": p.x, "y": p.y})
        m = re.fullmatch(r"(\d+)\s*[xX]\s*(\d+)", t)
        if m:
            sizes.append({"W": int(m[1]), "D": int(m[2]), "h": h, "x": p.x, "y": p.y})
    notes = []
    for e in msp.query("TEXT MTEXT"):
        take(e, e.dxf.handle)
        fr = FRAME_INDEX.get(round((FP_CENTRE_X - e.dxf.insert.x) / PITCH))
        t = _txt(e).strip()
        m = re.fullmatch(r"(P\.C|T\.C|D\.C|C\.S|F\.C)\s*(?:(\d+)\s*[xX]\s*(\d+))?", t)
        if fr in ("GFRS", "FFRS", "SFRS") and m:
            notes.append({"sheet": fr, "handle": e.dxf.handle, "kind": m[1], "W_cm": int(m[2]) if m[2] else None,
                          "D_cm": int(m[3]) if m[3] else None, "x": e.dxf.insert.x, "y": e.dxf.insert.y})
    for i in msp.query("INSERT"):
        for v in i.virtual_entities():
            if v.dxftype() in ("TEXT", "MTEXT"):
                take(v, "blk:" + i.dxf.handle)
    schedule = {}
    for i in msp.query('INSERT[name=="CGT"]'):
        a = {x.dxf.tag: x.dxf.text for x in i.attribs}
        schedule[a["COL-T"]] = {"handle": i.dxf.handle, "bands": {
            b: ({"W": int(a[f"{b}.W"]), "D": int(a[f"{b}.H"])} if a.get(f"{b}.W") else None)
            for b in ("FOU", "GR", "1ST", "2ND")}}
    # CN: neck-only text row of the schedule (T-075): 30 x 30, FOUNDATION only
    schedule.setdefault("CN", {"handle": "TEXT row (T-075)", "bands": {"FOU": {"W": 30, "D": 30}, "GR": None,
                                                                         "1ST": None, "2ND": None}})
    return {"rects": rects, "dims": dims, "labels": labels, "sizes": sizes, "schedule": schedule, "notes": notes}


def _one_to_one(items_a, items_b, dist):
    pairs = sorted((dist(a, b), i, j) for i, a in enumerate(items_a) for j, b in enumerate(items_b))
    ua, ub, out = set(), set(), {}
    for d, i, j in pairs:
        if i in ua or j in ub:
            continue
        ua.add(i), ub.add(j)
        out[i] = (j, d)
    return out


def printed_dims(r, dims):
    """Printed extent of a column outline along X and Y from the dimension chains touching it (mm), else None."""
    x0, x1 = r["cx"] - r["w"] / 2, r["cx"] + r["w"] / 2
    y0, y1 = r["cy"] - r["d"] / 2, r["cy"] + r["d"] / 2
    inside = lambda p: x0 - DIM_TOL <= p[0] <= x1 + DIM_TOL and y0 - DIM_TOL <= p[1] <= y1 + DIM_TOL
    out, used = {}, {}
    for ax, k in (("X", 0), ("Y", 1)):
        ds = [d for d in dims if inside(d["a"]) and inside(d["b"])
              and abs(d["a"][k] - d["b"][k]) > abs(d["a"][1 - k] - d["b"][1 - k])]
        if not ds:
            out[ax] = None
            continue
        segs = sorted(sorted((d["a"][k], d["b"][k])) for d in ds)
        lo, hi, ok = segs[0][0], segs[0][1], True
        for s in segs[1:]:
            if s[0] > hi + 1.0:
                ok = False
            hi = max(hi, s[1])
        out[ax] = round(hi - lo) if ok else None
        used[ax] = [d["h"] for d in ds]
    return out, used


def build(path: Path) -> dict:
    ex = extract(path)
    neck = json.loads((ROOT / "research/agents_t205/ALSENAN_NECK_INPUT.json").read_text(encoding="utf-8"))
    mark = {n["outline_handle"]: n for n in neck["necks"]}
    R = ex["rects"]
    by = {k: [r for r in R if r["fr"] == k] for k in FRAME_INDEX.values()}
    fp = by["FP"]
    assert len(fp) == 36 and all(r["h"] in mark for r in fp), "FP outline set differs from T-205"
    # CAP labels -> CAP outlines (one to one), size text = the text printed under its label (offset +362, -418)
    L2R = _one_to_one(ex["labels"], by["CAP"], lambda l, r: math.hypot(r["cx"] - l["x"], r["cy"] - l["y"]))
    S2L = _one_to_one(ex["sizes"], ex["labels"], lambda s, l: math.hypot(s["x"] - l["x"] - 362, s["y"] - l["y"] + 418))
    lab_size = {li: ex["sizes"][si] for si, (li, _) in S2L.items()}
    cap_info = {}
    for li, (rj, _) in L2R.items():
        r = by["CAP"][rj]
        lab = ex["labels"][li]
        cap_info[r["h"]] = {"label": lab["t"], "label_handle": lab["h"],
                            # engine id of the released storey column lines (route G register 'P-C:COL:SH12:<mark>@x,y')
                            "engine_col_id": f"COL:SH12:{lab['t']}@{round(lab['x'])},{round(lab['y'])}",
                            "text": lab_size.get(li)}
    instances = []
    for f in sorted(fp, key=lambda r: (mark[r["h"]]["type"], r["h"])):
        n = mark[f["h"]]
        inst = {"id": n["id"], "mark": n["type"], "fp_label_handle": n["label_handle"], "fp_outline": f["h"],
                "footing": n["footing"].get("type"), "pit_raft": bool(n["footing"].get("pit_raft")), "storeys": {}}
        for fr in ("FP", "CAP", "GBP", "GFRS", "FFRS", "SFRS"):
            cand = by[fr] if fr in ("FP", "CAP", "GBP") else [r for r in by[fr] if r["hatch"] == "SOLID"]
            b = min(cand, key=lambda r: math.hypot(r["fx"] - f["fx"], r["fy"] - f["fy"]))
            dd = math.hypot(b["fx"] - f["fx"], b["fy"] - f["fy"])
            st = inst["storeys"].setdefault(STOREY[fr], {"drawn": [], "texts": [], "dims": []})
            if dd > MATCH_TOL:
                st.setdefault("not_drawn_on", []).append(fr)
                continue
            st["drawn"].append({"sheet": fr, "handle": b["h"], "W_mm": min(b["w"], b["d"]), "D_mm": max(b["w"], b["d"]),
                                "hatch": b["hatch"]})
            pdm, used = printed_dims(b, ex["dims"])
            if pdm["X"] and pdm["Y"]:
                st["dims"].append({"sheet": fr, "handles": used["X"] + used["Y"],
                                   "W_mm": min(pdm["X"], pdm["Y"]), "D_mm": max(pdm["X"], pdm["Y"])})
            if fr == "CAP":
                ci = cap_info.get(b["h"])
                assert ci and ci["label"] == n["type"], ("CAP label differs", b["h"])
                inst["engine_col_id"] = ci["engine_col_id"]
                if ci["text"]:
                    st["texts"].append({"sheet": "CAP", "handle": ci["text"]["h"], "label_handle": ci["label_handle"],
                                        "W_cm": ci["text"]["W"], "D_cm": ci["text"]["D"]})
        instances.append(inst)
    claimed = {d["handle"] for i in instances for s in i["storeys"].values() for d in s["drawn"]}
    # members with no neck: a PATTERN outline (starts on this slab) + the SOLID outline at the same place on the plan
    # of the storey above + the P.C size text whose leader ends there (bound to the nearest PATTERN outline)
    nxt = {"GFRS": "FFRS", "FFRS": "SFRS", "SFRS": None}
    planted = []
    for fr in ("GFRS", "FFRS"):
        pcs = [n for n in ex["notes"] if n["sheet"] == fr and n["kind"] == "P.C"]
        starts = [r for r in by[fr] if r["hatch"] == "PATTERN"]
        P2S = _one_to_one(pcs, starts, lambda n, r: math.hypot(r["cx"] - n["x"], r["cy"] - n["y"]))
        pc_for = {starts[j]["h"]: pcs[i] for i, (j, _) in P2S.items()}
        for r in starts:
            above = [a for a in by[nxt[fr]] if a["hatch"] == "SOLID"
                     and math.hypot(a["fx"] - r["fx"], a["fy"] - r["fy"]) <= MATCH_TOL]
            neck = min(fp, key=lambda f: math.hypot(f["fx"] - r["fx"], f["fy"] - r["fy"]))
            on_neck = math.hypot(neck["fx"] - r["fx"], neck["fy"] - r["fy"]) <= MATCH_TOL
            pc = pc_for.get(r["h"])
            planted.append({"start_sheet": fr, "start_handle": r["h"], "W_mm": min(r["w"], r["d"]),
                            "D_mm": max(r["w"], r["d"]), "storey": STOREY[nxt[fr]],
                            "on_neck": neck["h"] if on_neck else None,
                            "pc_text": ({"handle": pc["handle"], "W_cm": pc["W_cm"], "D_cm": pc["D_cm"]} if pc else None),
                            "own_outline": ({"sheet": nxt[fr], "handle": above[0]["h"], "W_mm": min(above[0]["w"], above[0]["d"]),
                                             "D_mm": max(above[0]["w"], above[0]["d"])} if above else None)})
    in_planted = {p["own_outline"]["handle"] for p in planted if p["own_outline"]} | {p["start_handle"] for p in planted}
    extra = {fr: [{"handle": r["h"], "W_mm": min(r["w"], r["d"]), "D_mm": max(r["w"], r["d"]), "hatch": r["hatch"]}
                  for r in sorted(by[fr], key=lambda r: r["h"]) if r["h"] not in claimed and r["h"] not in in_planted]
             for fr in ("GFRS", "FFRS", "SFRS")}
    notes_out = [{k: v for k, v in n.items() if k not in ("x", "y")} for n in ex["notes"]]
    return {"schema": "T217_SECTION_INPUT_V1",
            "source_file": {"ST7757 dxf.dxf": f"sha256 {SHA} (Drive 'Alsenan chalet project')"},
            "binding": "FP label -> outline from research/agents_t205/ALSENAN_NECK_INPUT.json (T-205, merged 5f40dfdb)",
            "schedule": ex["schedule"], "instances": instances,
            "members_starting_on_a_slab": planted,
            "slab_plan_notes": notes_out,
            "outlines_not_over_a_neck": extra,
            "counts": {k: len(v) for k, v in by.items()}}


if __name__ == "__main__":
    out = build(Path(sys.argv[1]))
    if "--write" in sys.argv:
        (HERE / "ALSENAN_SECTION_INPUT.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                                                         encoding="utf-8")
    print(json.dumps({"counts": out["counts"], "extra": out["outlines_not_over_a_neck"]}, indent=0))
