"""T-760 F-01 EXTERNAL RENDER + EXTERNAL PAINT to figures (DELIVERY MODE fix-row set; worker 2, 2026-11-13).

Reads the candidate line index ARCH_TAKEOFF_V3.0.79 (T-314 r3, agents/task-T-314 @ 597d2820, READY with the Checker;
stacked on V3.0.78) and writes out/FIX_ROWS.json: one row per line of FIN.EXT.FINISH, FIN.EXT.PAINT,
FIN.EXT.PAINT.EDGE, ARCH.FACADE, ARCH.FACADE_RUN (ARCH.EXTERIOR already carries a figure) that is not yet a released
figure, with before / after / label / basis.

Every figure below comes from merged, Checker-passed face ledgers (T-305, T-324, T-337, T-737, T-751, T-754, T-756)
plus the owner's company defaults of 2026-11-13 (AGENT_BRIEF table). No drawing was opened in this run and no client
data is held here.

  python3 -I research/agents_t760/t760_fill.py <LINE_INDEX_V3_0_79.json> [--check]
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "FIX_ROWS.json")
INDEX_SHA16 = "0582aac58defff74"            # sha256[:16] of LINE_INDEX_V3_0_79.json at agents/task-T-314 597d2820
FAMILIES = ("FIN.EXT.FINISH", "FIN.EXT.PAINT", "FIN.EXT.PAINT.EDGE", "ARCH.FACADE", "ARCH.FACADE_RUN")
LABELS = ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY", "NOT_APPLICABLE_WITH_EVIDENCE")

# Company defaults used (owner 2026-11-13, AGENT_BRIEF 'Company defaults'):
EDGE_DEPTH = 0.60        # beam depth default 0.60 (no slab-edge / edge-beam depth printed, Q-68 C)
PARAPET_H = 1.20         # parapet 1.20 where its height is not printed
COVER_ABOVE_MEMBRANE = 0.10   # roof build-up default: membrane + 5 cm insulation + 5 cm protection above it
UPTURN_H = 0.20          # UP-WP-003 (owner approved) membrane upturn; R-T324-1: exposed upturn e = 0.20 - c = 0.10

r6 = lambda x: round(x + 0.0, 6)

# ---------------------------------------------------------------------------------------------------------------------
# Render lines (m2). Each entry: (after, label, basis). Face-level arithmetic is written out so the Checker can re-derive.
# ---------------------------------------------------------------------------------------------------------------------
W02_HOLE = 6.33 * 2.20                       # width '633' printed (8F1), head drawn at section B-B +1.00 / +3.20 (T-201)
GF_NW7 = 35.55 - W02_HOLE                    # face GF/NW-7 gross 7.90 x 4.50 = 35.55 (T-305)
GF_STOREY = 376.694149 + (GF_NW7 - 7.065)    # low bound carries W02 hole cap 28.485 and D-GF-07 hole 5.000
PAR1F_OUTER = 54.651307 + 2 * (0.08 * PARAPET_H - 0.087968) + (4.40 * PARAPET_H - 1.694)
SLAB_1F = {"NW-2": 2.675 * EDGE_DEPTH,       # void-ring landward arc 2.675 (T-348 r2)
           "NE-1": 0.08 * EDGE_DEPTH, "SW-1": 0.08 * EDGE_DEPTH, "SW-2": 3.00 * EDGE_DEPTH,   # T-305 runs
           "NW-4": 0.4673 * EDGE_DEPTH, "NW-5": 0.325 * EDGE_DEPTH,
           "SE-1": 2.30 * 0.80 + 1.80 * EDGE_DEPTH}   # T-754 porch-mouth band 2.30 x 0.80 + 1.80 behind the annex
SLAB_GF = 0.96154 + 4.4636 * EDGE_DEPTH      # pool-court front (point) + void ring inner 4.4636 m (0.89272 / 0.20)
PLINTH = 72.749795 - (5.659045 - 4.660390)   # NW-4 arc on the pool rim +0.30; NW-3 / NW-5 / SW-8 on the court +0.15


def inner(lo, hi):
    """R-T324-1 with c = 0.10 (company roof build-up default): e = 0.10 = half the 0.20 upturn cap -> the midpoint."""
    return (lo + hi) / 2


RENDER = {
    # storey bands
    "GF-FACADE:facade": (GF_STOREY, "DRAWING-READ",
        "376.694 low + (GF/NW-7 35.550 - W02 6.33 x 2.20 = 13.926 -> 21.624) - 7.065; D-GF-07 hole 2.00 x 2.50 = 5.000 "
        "printed plan tag (plan dimension governs a facade, company default; F-T737-1)"),
    "1F-FACADE:facade": (249.954348, "DRAWING-READ",
        "high bound: the three arched step returns 1F/NW-2 1.776 m2 (T-348 r2 geometry) are built and rendered"),
    "2F-FACADE:facade": (117.305, "DEFAULT",
        "125.160 gross (T-737 handle re-measure) - 7.855 holes; D-2F-01 head 2.20 (company default head)"),
    # parapet outer
    "GF-FACADE:PARAPET_OUTER:ANNEX_ROOF": (15.271022, "ESTIMATE",
        "14.671 + NE-6x outer face 0.600 m2 (T-324 C5): an outer face is rendered like every outer face; "
        "Q-65 C holds its block material, not its render; < 1 % of the line"),
    "GF-FACADE:PARAPET_OUTER:GF_ROOF": (14.385, "MEASURED", "T-305 / T-337 DRAWING-CONFIRMED faces"),
    "1F-FACADE:PARAPET_OUTER:1F_ROOF": (PAR1F_OUTER, "DEFAULT",
        "54.651 low + NE-1 / SW-1 0.08 x 1.20 + SW-2 4.40 x 1.20 = 5.280 (parapet 1.20 company default; range "
        "1.10 .. 1.30 / 0.385 .. 1.60)"),
    "2F-FACADE:PARAPET_OUTER:2F_ROOF": (14.9, "MEASURED", "T-305 / T-337 DRAWING-CONFIRMED faces"),
    # parapet inner (above the upturn)
    "GF-FACADE:PARAPET_INNER:ANNEX_ROOF": (inner(8.88843, 14.91405), "DEFAULT",
        "R-T324-1 split at c = 0.10 (roof build-up default: 5 cm insulation + 5 cm protection above the membrane): "
        "upturn exposed 0.10 of 0.20 -> midpoint; D-band end at mid (0.02 m2)"),
    "GF-FACADE:PARAPET_INNER:GF_ROOF": (inner(8.209433, 13.88495), "DEFAULT", "R-T324-1 at c = 0.10 (as annex)"),
    "1F-FACADE:PARAPET_INNER:1F_ROOF": (inner(41.82353, 56.608545), "ESTIMATE",
        "R-T324-1 at c = 0.10 + 1F exposed height 1.07 .. 1.17 HELD (D-39 roof datum) at its midpoint"),
    "2F-FACADE:PARAPET_INNER:2F_ROOF": (inner(8.49, 14.15), "DEFAULT", "R-T324-1 at c = 0.10 (28.30 m x 0.40)"),
    # parapet top
    "GF-FACADE:PARAPET_TOP:ANNEX_ROOF": (inner(5.99701, 6.03701), "ESTIMATE", "x 0.30 drawn; D-band end 0.20 m at mid"),
    "GF-FACADE:PARAPET_TOP:GF_ROOF": (inner(5.592956, 5.67398), "ESTIMATE", "x 0.20 / 0.30 drawn; D-band end at mid"),
    "1F-FACADE:PARAPET_TOP:1F_ROOF": (inner(9.83151, 9.84653), "ESTIMATE", "drawn widths; D-band end 0.075 m at mid"),
    "2F-FACADE:PARAPET_TOP:2F_ROOF": (5.415, "MEASURED", "18.05 m x 0.30 DRAWING-CONFIRMED (T-722 concrete agrees)"),
    # plinth and slab edges
    "GF-FACADE:PLINTH": (PLINTH, "DRAWING-READ",
        "72.750 high - NW-4 (6.6577 x 0.85 -> x 0.70: the arc stands on the pool rim +0.30, lines 2861 / 285C, T-751) "
        "; NW-3 / NW-5 ends on the court +0.15 (285E / 283E), SW-8 +0.15 as every covered plinth"),
    "GF-FACADE:SLAB_EDGE": (SLAB_GF, "DEFAULT",
        "pool-court front 0.962 + void ring inner 4.4636 m x 0.60 (beam depth default; T-348 r2 0.20 .. 0.75)"),
    "1F-FACADE:SLAB_EDGE": (sum(SLAB_1F.values()), "DEFAULT",
        "runs x 0.60 default depth: NW-2 2.675, NE-1 0.08, SW-1 0.08, SW-2 3.00, NW-4 0.467, NW-5 0.325 (T-305 / "
        "T-348) + SE-1 porch-mouth band 2.30 x 0.80 = 1.840 (T-754) + 1.80 behind the annex x 0.60"),
}

# Window outside edges = 2 jambs + head (T-747 / T-751 convention, e.g. W19 0.60 + 2 x 0.80 = 2.20)
EDGE_BLANK = {
    "GF-FACADE:PAINT_EDGE:W02": (6.33 + 2 * 2.20, "DRAWING-READ", "6.33 printed + 2 x 2.20 drawn at B-B (T-201)"),
    "GF-FACADE:PAINT_EDGE:W03": (6.657684 + 2 * 4.30, "DRAWING-READ",
        "glazed line NW-4 developed 6.6577 head + 2 frame-end jambs +1.00 .. +5.30 (T-305 W03)"),
    "1F-FACADE:PAINT_EDGE:W17": (3.29 + 2 * 3.00, "DRAWING-READ", "owner Q-76 A window 3.29 x 3.00 (T-627)"),
}
EDGE_RANGE = {
    "GF-FACADE:CORNER_EDGE:PARAPET-OUTER_GF_5.50": (2.2, "ESTIMATE",
        "1.0 + stop-end 2 x 0.50 + 0.20 = 1.20: the GF parapet ends at the open passage mouth, nothing to abut (T-754)"),
}
FACADE_GROSS = {   # ARCH.FACADE m2 = geometry register of the storey face gross (F-T737-3: never added to render)
    "GF-FACADE:facade": (469.329, "MEASURED", "= GF render 391.253 + holes 59.150 + W02 13.926 + D-GF-07 5.000 = T-337 gross (register; render counted once)"),
    "1F-FACADE:facade": (249.954348 + 30.783772, "DRAWING-READ",
        "= 1F render 249.954 + its holes 30.784 (T-305 OPENING_HOLES; T-756 stage faces incl.; register)"),
    "2F-FACADE:facade": (125.16, "MEASURED", "29.80 x 4.20 (T-737 handle re-measure, register)"),
    "GF-FACADE:facade below F.F.L. (plinth)": (PLINTH, "DRAWING-READ", "= plinth render faces (register)"),
}
RUN2 = (0.0, "NOT_APPLICABLE_WITH_EVIDENCE",
        "the thin 10.84 m second outline around 0.66 m2 on a wall layer is a drawing element (defect L-N10-01): no face "
        "in the T-305 / T-756 ledgers (every drawn face once, residual 0); the run is the released outline")


def build(index_path):
    raw = open(index_path, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()[:16]
    if sha != INDEX_SHA16:
        raise SystemExit(f"index sha {sha} != pinned {INDEX_SHA16}: rebuild the table on the new index")
    L = json.loads(raw)
    rows = []
    render_by_el = {}
    for l in sorted(L["lines"], key=lambda l: l["line_id"]):
        code = l["item_code"]
        if code not in FAMILIES or l["class"] == "RELEASED":
            continue
        el = l["element_id"]
        lo, hi = l["held_low"], l["held_high"]
        if code in ("FIN.EXT.FINISH", "FIN.EXT.PAINT"):
            val, lab, basis = RENDER[el]
            if code == "FIN.EXT.PAINT":
                basis = "= render of the same faces (UP-FIN-PAINT-002); " + basis
        elif code == "FIN.EXT.PAINT.EDGE":
            if el in EDGE_BLANK:
                val, lab, basis = EDGE_BLANK[el]
            elif el in EDGE_RANGE:
                val, lab, basis = EDGE_RANGE[el]
            elif lo is not None and hi is not None and abs(hi - lo) < 1e-9:
                val, lab, basis = lo, "MEASURED", "HELD point of the merged edge ledger (T-751 / T-754 / T-756)"
            else:
                raise SystemExit(f"edge {el} {lo} .. {hi}: no rule")
        elif code == "ARCH.FACADE":
            val, lab, basis = FACADE_GROSS[el]
        elif code == "ARCH.FACADE_RUN":
            if not el.endswith("facade outline 2"):
                raise SystemExit(f"{el}: unexpected run line")
            val, lab, basis = RUN2
        val = r6(val)
        if lo is not None and hi is not None and not (lo - 1e-6 <= val <= hi + 1e-6):
            raise SystemExit(f"{l['line_id']} {el}: {val} outside its bound {lo} .. {hi}")
        if code == "FIN.EXT.FINISH":
            render_by_el[el] = val
        rows.append({"set": "EXT_RENDER_PAINT", "line_id": l["line_id"], "item_code": code, "unit": l["unit"],
                     "element_id": el,
                     "before": {"class": l["class"], "net": l["measured_net"], "low": lo, "high": hi},
                     "after": {"class": "RELEASED", "net": val}, "label": lab, "basis": basis})
    for r in rows:   # paint = render face by face
        if r["item_code"] == "FIN.EXT.PAINT":
            assert r["after"]["net"] == render_by_el[r["element_id"]], r["element_id"]
        assert r["label"] in LABELS and r["basis"]
    return sha, rows


def summary(rows):
    s = {}
    for r in rows:
        k = r["item_code"]
        a = s.setdefault(k, {"lines": 0, "blank_before": 0, "blank_after": 0, "after": 0.0, "low_before": 0.0,
                             "high_before": 0.0, "labels": {}})
        a["lines"] += 1
        b = r["before"]
        if b["low"] is None and b["high"] is None:
            a["blank_before"] += 1
        else:
            a["low_before"] += b["low"]; a["high_before"] += b["high"]
        a["after"] += r["after"]["net"]
        a["labels"][r["label"]] = a["labels"].get(r["label"], 0) + 1
    for a in s.values():
        for k in ("after", "low_before", "high_before"):
            a[k] = round(a[k], 2)
    return s


def main(argv):
    sha, rows = build(argv[1])
    doc = {"schema": "T760_FIX_ROWS_V1", "candidate_version": "ARCH_TAKEOFF_V3.0.79", "index_sha16": sha,
           "base": "agents/task-T-314 597d2820 (T-314 r3 READY, stacked on V3.0.78)", "sets": ["EXT_RENDER_PAINT"],
           "summary": summary(rows), "rows": rows}
    text = json.dumps(doc, indent=1, sort_keys=False) + "\n"
    if "--check" in argv:
        if open(OUT).read() != text:
            raise SystemExit("FIX_ROWS.json is stale: rerun without --check")
        print("check OK", len(rows), "rows")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write(text)
    print(json.dumps(doc["summary"], indent=1))


if __name__ == "__main__":
    main(sys.argv)
