"""T-566 extractor: every column position of the development villa with its OWN mark evidence, read independently of
the merged T-205 / T-217 / T-394 bindings (Checker 2026-11-06 11:59: 'the GF column frame is label-free; GF C1 / C2 / C3
per-mark assignment rests on the merged registration, not on a re-measure').

Reads the private copy of Drive "Alsenan chalet project" / 'ST7757 dxf.dxf' (sha256 9f9d1179..., the route G input)
from .work/private and writes POSITION_INPUT_T566.json: handles, marks, sizes (mm / cm), distances rounded to 10 mm;
NO coordinates and no drawing content.

What is read, per sheet (the six plan frames are one drawing repeated at a fixed pitch in x; measured here again from
the outlines, not taken from T-217):
    FP   FOUNDATION PLAN       S-COL.BON neck outlines + column labels 'C3', 'C3/F3', 'CN/FN', block texts 'C/F'
    CAP  COLUMN & AXIS PLAN    neck outlines + column labels + size texts 'WxD' (cm)
    GBP  GROUND BEAMS PLAN     neck outlines + column labels
    GFRS / FFRS / SFRS         column outlines under the GF / 1F / 2F roof slab with their S-COL.HAT hatch
                               (SOLID = the storey's own member); every TEXT / MTEXT of the frame that looks like a
                               column mark is listed with its layer (the one 'C' on GFRS is a section-cut letter)
    schedule                   INSERT CGT rows (COL-T, FOU / GR / 1ST / 2ND W x H, cm); CN = text row (T-075)
Binding: inside each sheet, labels -> outlines by a minimum-total-distance one-to-one assignment (scipy
linear_sum_assignment), so a label is never bound by nearest-first order. Positions = FP outlines; a CAP / GBP / slab
outline is on a position when, after the frame translation, its centre is within 400 mm of the FP outline centre.

    python3 -I research/agents_t566/t566_extract.py <path to ST7757 dxf.dxf> [--write]
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
OUT = HERE / "POSITION_INPUT_T566.json"
SHEETS_BY_TITLE = ("FP", "CAP", "GBP", "GFRS", "FFRS", "SFRS")
LABEL_SHEETS = ("FP", "CAP", "GBP")
SLAB_SHEETS = {"GFRS": "GF", "FFRS": "1F", "SFRS": "2F"}
POS_TOL = 400.0          # mm: outline centre on a position (half the largest section change, T-217 measured <= 152)
CLUSTER_GAP = 6000.0     # mm: gap in x between the outline fields of two side-by-side frames (measured 7.6 .. 9.1 m; inside a field <= 4.6 m)
LABEL_REACH = 3000.0     # mm: a label or size text lies within this of its frame's outline field (max label offset 2.6 m)
LABEL_RE = re.compile(r"(C\d{0,2}|CN)(?:/F[N\d]{0,2})?")
SIZE_RE = re.compile(r"(\d+)\s*[xX]\s*(\d+)")


def _txt(e):
    return (e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text).strip()


def _assign(a, b, dist):
    """Minimum-total-distance one-to-one assignment; returns {i: (j, d)}."""
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    if not a or not b:
        return {}
    m = np.array([[dist(x, y) for y in b] for x in a])
    ri, ci = linear_sum_assignment(m)
    return {int(i): (int(j), float(m[i, j])) for i, j in zip(ri, ci)}


def extract(path: Path) -> dict:
    import ezdxf
    from ezdxf import bbox
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise SystemExit("not the route G input (sha256 differs)")
    msp = ezdxf.readfile(str(path)).modelspace()
    outl = []
    for e in msp.query('LWPOLYLINE[layer=="S-COL.BON"]'):
        b = bbox.extents([e])
        outl.append({"h": e.dxf.handle, "cx": b.center.x, "cy": b.center.y, "w": round(b.size.x), "d": round(b.size.y)})
    # frames: sheet titles are INSERTs named like the sheet code (T-217); frame centre x per title, pitch measured
    titles = {}
    for i in msp.query("INSERT"):
        if i.dxf.name in SHEETS_BY_TITLE:
            titles[i.dxf.name] = i.dxf.insert.x
    if set(titles) != set(SHEETS_BY_TITLE):
        raise SystemExit(f"sheet title blocks missing: {sorted(set(SHEETS_BY_TITLE) - set(titles))}")
    # frames are side by side in x: the column outlines fall into one cluster per frame (gap > CLUSTER_GAP between
    # clusters); each cluster is named by the nearest title block; an entity belongs to a frame when its x lies in the
    # cluster's x range widened by LABEL_REACH. The translation of each frame onto FP is measured from the outlines.
    xs = sorted(outl, key=lambda o: o["cx"])
    clusters, cur = [], [xs[0]]
    for o in xs[1:]:
        if o["cx"] - cur[-1]["cx"] > CLUSTER_GAP:
            clusters.append(cur)
            cur = []
        cur.append(o)
    clusters.append(cur)
    ranges = {}
    for c in clusters:
        lo, hi = min(o["cx"] for o in c), max(o["cx"] for o in c)
        s = min(titles, key=lambda k: abs(titles[k] - (lo + hi) / 2))
        if s in ranges:
            raise SystemExit(f"two outline clusters name the same frame {s}")
        ranges[s] = (lo - LABEL_REACH, hi + LABEL_REACH)
    if set(ranges) != set(SHEETS_BY_TITLE):
        raise SystemExit(f"frames without an outline cluster: {sorted(set(SHEETS_BY_TITLE) - set(ranges))}")

    def frame(x):
        hit = [s for s, (lo, hi) in ranges.items() if lo <= x <= hi]
        return hit[0] if len(hit) == 1 else None

    for o in outl:
        o["fr"] = frame(o["cx"])
    fp0 = [o for o in outl if o["fr"] == "FP"]
    shift = {"FP": 0.0}
    for s in SHEETS_BY_TITLE[1:]:
        votes = {}
        for o in (q for q in outl if q["fr"] == s):
            for f in fp0:
                if abs(o["cy"] - f["cy"]) < 1.0 and sorted([o["w"], o["d"]]) == sorted([f["w"], f["d"]]):
                    k = round(f["cx"] - o["cx"])
                    votes[k] = votes.get(k, 0) + 1
        best = max(votes, key=votes.get)
        near = [k for k in votes if abs(k - best) <= 2]
        shift[s] = sum(k * votes[k] for k in near) / sum(votes[k] for k in near)
        shift[s + "_votes"] = sum(votes[k] for k in near)
    for o in outl:
        o["fx"] = o["cx"] + shift[o["fr"]] if o["fr"] else None
    pitch = abs(shift["CAP"])
    hatches = []
    for e in msp.query('HATCH[layer=="S-COL.HAT"]'):
        b = bbox.extents([e])
        if b.has_data:
            hatches.append((b.center.x, b.center.y, b.size.x, b.size.y, e.dxf.pattern_name))
    for o in outl:
        pats = {h[4] for h in hatches if abs(h[0] - o["cx"]) <= o["w"] / 2 + 5 and abs(h[1] - o["cy"]) <= o["d"] / 2 + 5
                and h[2] <= o["w"] + 10 and h[3] <= o["d"] + 10}
        o["hatch"] = "SOLID" if pats == {"SOLID"} else ("PATTERN" if pats and "SOLID" not in pats else
                                                        ("NONE" if not pats else "MIXED"))
    texts = []

    def take(t, x, y, h, layer):
        fr = frame(x)
        if fr:
            texts.append({"t": t, "x": x, "y": y, "h": h, "layer": layer, "fr": fr})

    for e in msp.query("TEXT MTEXT"):
        take(_txt(e), e.dxf.insert.x, e.dxf.insert.y, e.dxf.handle, e.dxf.layer)
    for i in msp.query("INSERT"):
        for v in i.virtual_entities():
            if v.dxftype() in ("TEXT", "MTEXT"):
                take(_txt(v), v.dxf.insert.x, v.dxf.insert.y, "blk:" + i.dxf.handle, "block " + i.dxf.name)
    schedule = {}
    for i in msp.query('INSERT[name=="CGT"]'):
        a = {x.dxf.tag: x.dxf.text for x in i.attribs}
        schedule[a["COL-T"]] = {"handle": i.dxf.handle, "bands": {
            b: ([int(a[f"{b}.W"]), int(a[f"{b}.H"])] if a.get(f"{b}.W") else None) for b in ("FOU", "GR", "1ST", "2ND")}}
    schedule.setdefault("CN", {"handle": "TEXT row (T-075)", "bands": {"FOU": [30, 30], "GR": None, "1ST": None,
                                                                         "2ND": None}})
    return {"outlines": outl, "texts": texts, "schedule": schedule, "pitch": pitch, "titles": titles, "shift": shift}


def build(path: Path) -> dict:
    ex = extract(path)
    O, T = ex["outlines"], ex["texts"]
    by = {s: [o for o in O if o["fr"] == s] for s in SHEETS_BY_TITLE}
    fp = by["FP"]
    d = lambda a, b: math.hypot(a["fx"] - b["fx"], a["cy"] - b["cy"])
    positions = {f["h"]: {"position": f["h"], "neck_drawn_mm": sorted([f["w"], f["d"]]), "labels": {},
                          "size_text_cm": None, "members": {}} for f in fp}

    def pos_of(o):
        f = min(fp, key=lambda q: d(q, o))
        return f["h"] if d(f, o) <= POS_TOL else None

    unbound = {}
    for s in LABEL_SHEETS:
        labs = [t for t in T if t["fr"] == s and LABEL_RE.fullmatch(t["t"])]
        rs = by[s]
        m = _assign(labs, rs, lambda l, r: math.hypot(r["cx"] - l["x"], r["cy"] - l["y"]))
        unbound[s] = sorted(labs[i]["h"] for i in set(range(len(labs))) - set(m))
        for i, (j, dist) in m.items():
            p = pos_of(rs[j])
            if p is None:
                unbound[s].append(labs[i]["h"])
                continue
            lab = labs[i]
            positions[p]["labels"][s] = {"text": lab["t"], "mark": LABEL_RE.fullmatch(lab["t"]).group(1),
                                         "handle": lab["h"], "outline": rs[j]["h"], "dist_mm": round(dist, -1)}
        for r in rs:
            p = pos_of(r)
            if p:
                positions[p].setdefault("drawn_on", {})[s] = r["h"]
    # CAP size texts -> CAP outlines (own assignment)
    sizes = [t for t in T if t["fr"] == "CAP" and SIZE_RE.fullmatch(t["t"])]
    m = _assign(sizes, by["CAP"], lambda l, r: math.hypot(r["cx"] - l["x"], r["cy"] - l["y"]))
    for i, (j, dist) in m.items():
        p = pos_of(by["CAP"][j])
        if p:
            w, dd = (int(v) for v in SIZE_RE.fullmatch(sizes[i]["t"]).groups())
            positions[p]["size_text_cm"] = {"W": w, "D": dd, "handle": sizes[i]["h"], "dist_mm": round(dist, -1)}
    # storey members: SOLID outline on the storey's roof-slab plan over the position
    planted = []
    for s, st in SLAB_SHEETS.items():
        for r in by[s]:
            p = pos_of(r)
            rec = {"sheet": s, "handle": r["h"], "section_mm": sorted([r["w"], r["d"]]), "hatch": r["hatch"]}
            if p and r["hatch"] == "SOLID":
                if st in positions[p]["members"]:
                    raise SystemExit(f"two SOLID outlines on one position {p} {st}")
                positions[p]["members"][st] = rec
            elif p:
                positions[p].setdefault("starts_here", []).append(rec)
            else:
                planted.append(rec)
    frame_marks = {s: sorted([{"text": t["t"], "handle": t["h"], "layer": t["layer"]} for t in T
                              if t["fr"] == s and LABEL_RE.fullmatch(t["t"])], key=lambda x: x["handle"])
                   for s in SLAB_SHEETS}
    return {"schema": "T566_POSITION_INPUT_V1",
            "source_file": {"ST7757 dxf.dxf": f"sha256 {SHA} (Drive 'Alsenan chalet project')"},
            "binding": "own read: per-sheet minimum-total-distance label -> outline assignment; positions = FP outlines",
            "pitch_mm": round(ex["pitch"], 1),
            "frame_shift_onto_FP_mm": {k: (round(v, 1) if isinstance(v, float) else v) for k, v in ex["shift"].items()},
            "counts": {s: len(by[s]) for s in SHEETS_BY_TITLE},
            "labels_unbound": unbound,
            "slab_frame_mark_like_texts": frame_marks,
            "schedule": ex["schedule"],
            "positions": [positions[k] for k in sorted(positions)],
            "slab_outlines_not_on_a_position": sorted(planted, key=lambda r: (r["sheet"], r["handle"]))}


if __name__ == "__main__":
    out = build(Path(sys.argv[1]))
    if "--write" in sys.argv:
        OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"counts": out["counts"], "pitch": out["pitch_mm"], "unbound": out["labels_unbound"],
                      "slab_texts": out["slab_frame_mark_like_texts"]}, indent=0))
