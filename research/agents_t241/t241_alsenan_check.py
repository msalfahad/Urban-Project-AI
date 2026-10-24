"""T-241 Alsenan check: CONC.BEAM whole line, every beam run once (development villa; no accuracy claim).

Builds LEDGER_T241.csv (one row per beam run) and summary.json from committed inputs only:
  research/agents_t110/BEAM_MEMBER_REGISTER.csv  (merged 575df66: 137 span records, widths re-measured from edge lines)
  research/agents_t229/summary.json              (merged 3803684e: beam runs at supports / carried members, doubles)
  research/agents_t145 CB5 span 2                (merged: 0.20 x 0.40 x 3.700, BM-GF-035.2 proposed)
  research/agents_t241/ALSENAN_PARTITION_INPUT.json (this task, t241_extract.py on 'ST7757 dxf.dxf' 9f9d1179)
  research/urban_engine_m4_correctness/st7757_route_g (the released route G beam lines: PROVISIONAL / UNRESOLVED)
  tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (sheet 'كمرات', his cells and formulas)
Nothing is wired; no engine, candidate or released line changes.

    python3 -I research/agents_t241/t241_alsenan_check.py [--write]
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import beam_line as BL  # noqa: E402

STOREYS = ("GF", "1F", "2F")
DEPTH_RANGE = (0.40, 1.20)   # shallowest / deepest printed beam depth on the schedules (B1 20x40 .. B15 20x120): the
                             # T-110 candidate convention for an unlabelled drawn piece (Q-16: never one copied depth)

# released ARCH_TAKEOFF_V2.9 + route G, own run on working head 48d1d846 (tools/release_baseline.py
# V29_ROUTEG_NO_PROFILE: REPRODUCED, 1,455 lines, BOQ_LINES.csv b96185d4): STR.CONC.BEAM per floor
RELEASED = {"GF": dict(measured=39.138, n=61, bounded=(3.7554, 5.2934), nb=9),
            "1F": dict(measured=21.3831, n=36, bounded=(4.1313, 7.453), nb=11),
            "2F": dict(measured=4.2985, n=15, bounded=(0.5624, 1.6872), nb=4)}
# candidate ARCH_TAKEOFF_V3.0.5 .. V3.0.9a (merged package reports: T-179 'STR.CONC.BEAM 64.8196 -> 65.2937 = west ring
# 0.7552 - route arc bands 0.2811'; T-187 / T-193 / T-231 / T-211 code totals move no beam line): NOT an own run
CANDIDATE = dict(measured=65.2937, held=(8.224, 13.759), blocked=1,
                 change="1F west dome ring B4 in-bay 0.7552 (VERIFIED T-160 / T-179) replaces route G arc bands 0.2811")


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def route_g():
    base = ROOT / "research/urban_engine_m4_correctness/st7757_route_g"
    rel = {r["COMPONENT_ID"]: float(r["BASE"]) for r in csv.DictReader(open(base / "PROVISIONAL_REGISTER.csv",
                                                                               encoding="utf-8"))
           if r["COMPONENT_ID"].startswith("BEAMS:") and r["UNIT"] == "m3"}
    held = {r["COMPONENT_ID"]: (float(r["EXPOSURE_LOW_M3"]), float(r["EXPOSURE_HIGH_M3"]), r["BLOCKER"])
            for r in csv.DictReader(open(base / "UNRESOLVED_CONCRETE_EXCEPTIONS.csv", encoding="utf-8"))
            if r["COMPONENT_ID"].startswith("BEAMS")}
    return rel, held


def pieces_of(component):
    """'BEAMS:GF:BAND0047.1+.2' -> ['GF:BAND0047.1', 'GF:BAND0047.2']"""
    m = re.match(r"RING:(\w+):\w+ \(BAND(\d+)-(\d+)\)", component)
    if m:   # a ring row of T-110 that replaces the route G arc bands BANDa..BANDb
        return ["%s:BAND%04d" % (m.group(1), i) for i in range(int(m.group(2)), int(m.group(3)) + 1)]
    if not component.startswith("BEAMS:"):
        return []
    _b, st, b = component.split(":")
    head = b.split(".")[0]
    out = []
    for p in b.split("+"):
        out.append(st + ":" + (p if p.startswith("BAND") else head + p))
    return out


def t229():
    s = json.load(open(ROOT / "research/agents_t229/summary.json", encoding="utf-8"))
    short = defaultdict(list)     # piece -> [(class, m3)]
    for e in s["ends"]:
        if e.get("short_m3"):
            short[e["piece"]].append((e["cls"], e["short_m3"]))
    for g in s["gaps"]:
        if g.get("short_m3"):
            short[g["a"]].append((g["cls"] + " (to " + g["b"] + ")", g["short_m3"]))
    double = defaultdict(list)
    for d in s["double"]["lines"]:
        if d["released"]["double_m3"]:
            double[d["piece"]].append((d["outline"], d["released"]["result"], d["released"]["double_m3"]))
    beams = {b["beam"]: b for b in s["beams"]}
    return short, double, beams, s


def ledger():
    reg = list(csv.DictReader(open(ROOT / "research/agents_t110/BEAM_MEMBER_REGISTER.csv", encoding="utf-8")))
    rel, held = route_g()
    short, double, beams, s229 = t229()
    rows = []
    used_short, used_double = set(), set()
    for r in reg:
        pcs = pieces_of(r["component"])
        comp_ids = ["BEAMS:" + p for p in pcs]
        run = r["member_id"] + ("#" + pcs[0].split(":")[1] if pcs else "")
        L = _f(r["length_m"])
        w = _f(r["width_m"])
        D = _f(r["depth_m"])
        st = r["floor"]
        released = sum(rel.get(c, 0.0) for c in comp_ids)
        released_bounded = [held[c] for c in comp_ids if c in held]
        row = dict(run=run, storey=st, mark=r["mark"], member=r["member_id"], pieces="|".join(pcs),
                   length_m=L, b_schedule_m=None, b_drawn_m=w, depth_m=D, status=r["status"],
                   m3=None, m3_low=_f(r["m3_low"]), m3_high=_f(r["m3_high"]), released_m3=round(released, 6),
                   released_bounded="|".join("%.4f..%.4f %s" % b for b in released_bounded), adds=[], deducts=[],
                   designer=r["designer"], source="T-110 " + r["section"][:60], reason=r["conflict"][:120])
        if r["status"] == "CALCULATED":
            row["m3"] = _f(r["m3"])
        # T-229: B26 / B27 / B28 runs (T-110 measured B26 / B27 through the carried P.C; T-229 adds the ends)
        for name, b in beams.items():
            if b["pieces"] and set(b["pieces"]) <= set(pcs) and b["drawing_derived_m3"] and name.startswith("GF B2") \
                    and name.split()[1] in ("B26", "B27"):
                row["adds"].append(("T-229 run %s %.4f replaces T-110 %.4f" % (name, b["drawing_derived_m3"],
                                                                                row["m3"]), b["drawing_derived_m3"]
                                    - row["m3"]))
                for p in b["pieces"]:
                    used_short.add(p)
        for p in pcs:
            if p in short and p not in used_short:
                for cls, v in short[p]:
                    row["adds"].append(("T-229 " + cls, v))
                used_short.add(p)
            if p in double and p not in used_double:
                for outline, res, v in double[p]:
                    row["deducts"].append(("T-229 %s column %s (column owns, R-CONC-OWN-1)" % (res, outline), v))
                used_double.add(p)
        add = sum(v for _n, v in row["adds"])
        ded = sum(v for _n, v in row["deducts"])
        if row["status"] == "CALCULATED":
            row["m3"] = round(row["m3"] + add - ded, 6)
            row["m3_low"] = row["m3_high"] = row["m3"]
        elif row["status"] == "CONFLICT" and (add or ded):
            # the T-229 strip is measured at the DRAWN width; at the other reading it scales with the width
            ws = [_f(x) for x in r["width_m"].replace("schedule", "").replace("drawn", "").split("/")
                  if _f(x.strip()) is not None]
            lo_add = hi_add = add - ded
            if len(ws) == 2:
                ratio = ws[0] / ws[1]
                other = (add - ded) * ratio
                lo_add, hi_add = sorted((add - ded, other)) if row["m3_low"] <= row["m3_high"] else (add, other)
                # the low end is the narrower reading
                lo_add, hi_add = (min(add - ded, other), max(add - ded, other))
            row["m3_low"] = round(row["m3_low"] + lo_add, 6)
            row["m3_high"] = round(row["m3_high"] + hi_add, 6)
        elif row["status"] == "HELD" and (add or ded):
            row["reason"] = (row["reason"] + "; " if row["reason"] else "") + "T-229 strip %.4f stays with the hold" % (
                add - ded)
        rows.append(row)
    # new runs (no T-110 record)
    cb5 = BL.run_row("BM-GF-035.2#CB5-span2", "GF", "CB5", 3.700, b_schedule=0.20, b_drawn=0.200, depth=0.40,
                     sources=("ST p.11 2-span schedule CB5 B 20 H 40", "ST p.4 edges x 52.693 / 52.893, label y 42.680",
                              "T-145 merged; T-139 face GF-097 0.74 m2"))
    cb5.update(member="BM-GF-035.2", pieces="GF-097 (no route G band)", status="CALCULATED", released_m3=0.0,
               released_bounded="", adds=[], deducts=[], designer="", source="T-145 (merged) + partition GF-097",
               reason="in no beam line of released A or the candidate; released A bills its 0.1184 as slab (T-234)")
    rows.append(cb5)
    gf112 = dict(run="BM-GF-062#GF-112", storey="GF", mark="(none; in line with B4)", member="BM-GF-062",
                 pieces="GF-112 (no route G band)", length_m=0.5, b_schedule_m=None, b_drawn_m=0.2, depth_m=None,
                 status="HELD", m3=None, m3_low=round(0.2 * 0.5 * DEPTH_RANGE[0], 6),
                 m3_high=round(0.2 * 0.5 * DEPTH_RANGE[1], 6), released_m3=0.0, released_bounded="", adds=[],
                 deducts=[], designer="D-04 (new piece)", source="this task: partition face GF-112 0.20 x 0.50",
                 reason="drawn 0.20 x 0.50 piece north of the CB6 support column, in line with B4, up to the B7 void "
                        "ring; no label, no band in any line (Q-16: candidate range, never the neighbour's depth)")
    rows.append(gf112)
    f2031 = dict(run="BM-2F-019#2F-031", storey="2F", mark="(none)", member="BM-2F-019", pieces="2F-031 (no band)",
                 length_m=4.35, b_schedule_m=None, b_drawn_m=0.10, depth_m=None, status="HELD", m3=None,
                 m3_low=None, m3_high=None, released_m3=0.0, released_bounded="", adds=[], deducts=[],
                 designer="D-26 (as the GF / 1F projection strips)",
                 source="this task: partition face 2F-031 0.10 x 4.35 (T-234: released A bills 0.0489 as slab)",
                 reason="0.10 strip west of the B15 band: no tag, no bars, depth not printed; HELD, no m3, never 0")
    rows.append(f2031)
    leftovers = dict(short=sorted(set(short) - used_short), double=sorted(set(double) - used_double))
    return rows, leftovers, s229


def partition_check(rows, s229):
    """Area partition of every beam-lane face of the three slab sheets (m2): band-covered + column-covered +
    uncovered = face + double; each uncovered part is assigned to a ledger run or named."""
    d = json.load(open(HERE / "ALSENAN_PARTITION_INPUT.json", encoding="utf-8"))
    beam_cls = ("BEAM", "BEAM_OR_COLUMN", "BEAM_HELD", "EDGE_HELD")
    out = {}
    named_faces = {"GF-097": "BM-GF-035.2 CB5 span 2 (new run)", "GF-112": "BM-GF-062 (new HELD run)",
                   "GF-062": "BM-GF-061 outer west strip (D-26 HELD)", "GF-106": "BM-GF-061 outer west strip (D-26 HELD)",
                   "GF-096": "BM-GF-061 outer west strip (D-26 HELD)", "GF-159": "BM-GF-057 'B3 (With Stair)' (D-03 HELD)",
                   "GF-161": "BM-GF-057 'B3 (With Stair)' strip (D-03 HELD)", "2F-031": "BM-2F-019 (new HELD run)",
                   "1F-028": "BM-1F-036 strip outside CB12 (D-05 HELD)", "1F-069": "BM-1F-037 SE box (D-26 HELD)",
                   "1F-072": "CB10 beside its support (T-229, HELD D-02 width CONFLICT)",
                   "GF-035": "GF void ring B7 arc piece: route G arc band short of the drawn ring face (not cut-checked)",
                   "GF-060": "GF void ring B7 arc piece: route G arc band short of the drawn ring face (not cut-checked)"}
    for st in STOREYS:
        fs = [f for f in d["faces"] if f["storey"] == st]
        slab_x_band = sum(a for f in fs if f["cls"] == "SLAB" for _b, a in f["bands"])
        slab_perim_faces = sum(1 for f in fs if f["cls"] == "SLAB" and f["bands"])
        bf = [f for f in fs if f["cls"] in beam_cls]
        area = sum(f["area_m2"] for f in bf)
        band = sum(a for f in bf for _b, a in f["bands"])
        col = sum(a for f in bf for *_x, a in f["columns"])
        unc = sum(f["uncovered_m2"] for f in bf)
        dbl_solid, dbl_pattern = [], []
        for f in bf:
            b = sum(a for _b, a in f["bands"])
            for h, hatch, a in f["columns"]:
                ov = min(a, b)
                if ov > 1e-3 and b > 1e-3:
                    (dbl_solid if hatch == "SOLID" else dbl_pattern).append((f["id"], h, hatch, round(ov, 5),
                                                                             [x for x, y in f["bands"] if y > 1e-3]))
        named = {f["id"]: (named_faces[f["id"]], f["uncovered_m2"]) for f in bf if f["id"] in named_faces}
        edge = {f["id"]: f["uncovered_m2"] for f in bf if f["cls"] in ("EDGE_HELD", "BEAM_HELD")
                and f["id"] not in named_faces and f["uncovered_m2"] > 1e-3}
        rest = [(f["id"], f["uncovered_m2"]) for f in bf if f["id"] not in named_faces and f["id"] not in edge
                and f["uncovered_m2"] > 1e-3]
        # a carried member's outline (PATTERN hatch) with no band over it: the beam is cut there (CUT_AT_CARRIED)
        pattern_unbanded = sum(max(a - sum(y for _x, y in f["bands"]), 0.0) for f in bf for _h, hatch, a in f["columns"]
                               if hatch == "PATTERN")
        t229_plan = 0.0
        for e in s229["ends"] + s229["gaps"]:
            if e.get("short_m3") and e.get("storey") == st and e.get("depth_m"):
                t229_plan += e["short_m3"] / e["depth_m"]
        out[st] = dict(faces=len(bf), pattern_outline_unbanded_m2=round(pattern_unbanded, 4),
                       t229_short_plan_m2=round(t229_plan, 4), face_m2=round(area, 4), band_m2=round(band, 4), column_m2=round(col, 4),
                       uncovered_m2=round(unc, 4),
                       named_uncovered={k: (v[0], round(v[1], 4)) for k, v in named.items()},
                       held_edge_uncovered_m2=round(sum(edge.values()), 4),
                       beam_end_and_beside_uncovered_m2=round(sum(a for _i, a in rest), 4),
                       beam_end_faces=len(rest),
                       end_residual_m2=round(sum(a for _i, a in rest) + pattern_unbanded - t229_plan, 4),
                       double_solid_column=dbl_solid, carried_member_under_beam=dbl_pattern,
                       slab_x_band_m2=round(slab_x_band, 4), slab_faces_touching_bands=slab_perim_faces)
    return out


def freelancer():
    raw = json.load(open(ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json", encoding="utf-8"))
    cells = {int(x["row"]): x["cells"] for x in raw["rows"] if x.get("sheet") == "كمرات"}
    v = lambda r, c: cells[r][c + str(r)]["v"]  # noqa: E731
    gf, f1_total, f1_page, f2, tot = v(54, "I"), v(82, "I"), v(79, "I"), v(96, "I"), v(100, "I")
    rows = []
    storey = None
    for r in sorted(cells):
        c = cells[r]
        if r in (10,):
            storey = "GF"
        if r == 56:
            storey = "1F"
        if r == 83:
            storey = "2F"
        if ("I%d" % r) in c and ("B%d" % r) in c and isinstance(c["B%d" % r]["v"], (int, float)):
            rows.append(dict(row=r, storey=storey, mark=(c.get("A%d" % r) or {}).get("v"), b=c["B%d" % r]["v"],
                             d=c["C%d" % r]["v"], L=c["D%d" % r]["v"], n=(c.get("F%d" % r) or {}).get("v"),
                             m3=c["I%d" % r]["v"]))
    return dict(GF=gf, F1_total_cell=f1_total, F1_page_cell=f1_page, F2=f2, total=tot,
                f1_slip="I82 = SUM(I60:I78) leaves out row 59 (1F B1 0.20 x 0.40 x 1.60 = 0.128) that his own page "
                        "sum I79 = SUM(I59:I78) = 17.155 carries; his total I100 uses I82",
                rows=rows)


def by_mark(rows, fr):
    """Per storey and mark: drawing-derived (measured + CONFLICT range, HELD counted apart) vs his cells."""
    norm = lambda m: re.sub(r"^(BCB|GCB)", "CB", (m or "").strip())  # noqa: E731  his 'BCB5' / 'GCB9' = CB5 / CB9
    mine = defaultdict(lambda: [0, 0.0, 0.0, 0])
    his = defaultdict(lambda: [0, 0.0, 0.0])
    for r in rows:
        if r["status"] == "HELD" or not r["mark"] or r["mark"].startswith("("):
            continue
        k = (r["storey"], norm(r["mark"].split()[0]))
        v = mine[k]
        v[0] += 1
        if r["status"] == "CONFLICT":
            v[1] += r["m3_low"]
            v[2] += r["m3_high"]
            v[3] += 1
        else:
            v[1] += r["m3"]
            v[2] += r["m3"]
    last = None
    for x in fr["rows"]:
        m = norm(x["mark"]) if x["mark"] else last
        last = m
        k = (x["storey"], m)
        his[k][0] += 1
        his[k][1] += x["m3"]
        his[k][2] += x["L"] * (x["n"] or 1)
    out = []
    for k in sorted(set(mine) | set(his)):
        a, b = mine.get(k), his.get(k)
        cls = "BOTH" if a and b else ("DRAWN_NOT_IN_HIS_SHEET_UNDER_THIS_MARK" if a else "HIS_ONLY")
        out.append(dict(storey=k[0], mark=k[1], cls=cls, runs=a[0] if a else 0,
                        mine_low=round(a[1], 4) if a else 0.0, mine_high=round(a[2], 4) if a else 0.0,
                        conflict_runs=a[3] if a else 0, his_rows=b[0] if b else 0,
                        his_m3=round(b[1], 4) if b else 0.0, his_length_m=round(b[2], 3) if b else 0.0))
    return out


def build():
    rows, leftovers, s229 = ledger()
    tot = BL.line_total([dict(run=r["run"], storey=r["storey"], status=r["status"], m3=r["m3"], m3_low=r["m3_low"],
                              m3_high=r["m3_high"], reason=r["reason"]) for r in rows])
    part = partition_check(rows, s229)
    fr = freelancer()
    measured = round(sum(t["measured_m3"] for t in tot.values()), 6)
    # reconciliation per storey: drawing-derived measured vs released measured, by named row-level causes
    rec = {}
    for st in STOREYS:
        comps = defaultdict(float)
        for r in rows:
            if r["storey"] != st:
                continue
            mine = r["m3"] if r["status"] in BL.MEASURED else 0.0
            delta = mine - r["released_m3"]
            if abs(delta) < 1e-9:
                continue
            if r["status"] == "CONFLICT":
                comps["released at the schedule width, now CONFLICT (D-02 / D-27; range kept apart)"] -= r["released_m3"]
            elif r["status"] == "HELD":
                comps["released, now HELD (Q-61 C: unlabelled / contested)"] -= r["released_m3"]
            else:
                t229 = sum(v for _n, v in r["adds"] if not _n.startswith("T-229 run ")) - sum(
                    v for _n, v in r["deducts"])
                base = mine - t229 - r["released_m3"]
                if abs(t229) > 1e-9:
                    comps["T-229 strips no line bills (oblique / carried ends, beside narrower supports) net of "
                          "the column joints billed twice"] += t229
                if abs(base) > 1e-9:
                    if r["member"] == "BM-GF-035.2":
                        key = "CB5 span 2 in no beam line (T-145; released bills its band 0.1184 as slab)"
                    elif r["mark"] in ("B26", "B27"):
                        key = "B26 / B27 continuous under the carried P.C (route G held pieces + cut at carried; T-229)"
                    elif "RING" in r["pieces"] or r["member"] == "BM-1F-028":
                        key = "1F west dome ring B4 0.7553 replaces the route G arc bands (T-110 / T-160)"
                    elif r["released_bounded"] or r["released_m3"] == 0.0:
                        key = ("route G HELD / no-band pieces measured from printed sections and schedule (B20 / B23 "
                               "west spans, B7 strip, B20 / B23 upstands; T-110)")
                    else:
                        key = "T-110 re-derivation of a released route G piece"
                    comps[key] += base
        rec[st] = BL.reconcile(tot[st]["measured_m3"], RELEASED[st]["measured"], sorted(comps.items()))
    # vs freelancer per storey (his cells), by mark
    fr_st = {"GF": fr["GF"], "1F": fr["F1_total_cell"], "2F": fr["F2"]}
    marks = by_mark(rows, fr)
    mark_sum = defaultdict(lambda: [0, 0.0, 0.0, 0.0])
    for m in marks:
        v = mark_sum[m["cls"]]
        v[0] += 1
        v[1] += m["mine_low"]
        v[2] += m["mine_high"]
        v[3] += m["his_m3"]
    summary = dict(
        schema="T241_BEAM_LINE_V1", module=BL.SCHEMA, convention="C1_PANEL_BETWEEN_BEAM_FACES",
        source_dxf_sha256="9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079",
        runs=len(rows), by_storey=tot, measured_m3=measured,
        conflict=(round(sum(t["conflict_low"] for t in tot.values()), 6),
                  round(sum(t["conflict_high"] for t in tot.values()), 6)),
        held=(round(sum(t["held_low"] for t in tot.values()), 6), round(sum(t["held_high"] for t in tot.values()), 6)),
        held_no_value=[x for t in tot.values() for x in t["held_no_value"]],
        t229_leftovers=leftovers, partition=part,
        released=dict(per_floor=RELEASED, measured=round(sum(v["measured"] for v in RELEASED.values()), 4),
                      reconcile=rec),
        candidate=CANDIDATE,
        freelancer=dict(per_floor=fr_st, total=fr["total"], f1_page_cell=fr["F1_page_cell"], slip=fr["f1_slip"],
                        rows=len(fr["rows"]),
                        by_class={k: dict(marks=v[0], mine_low=round(v[1], 4), mine_high=round(v[2], 4),
                                          his_m3=round(v[3], 4)) for k, v in mark_sum.items()}),
    )
    return summary, rows, marks, tot, part, rec, fr_st


def main(argv):
    summary, rows, marks, tot, part, rec, fr_st = build()
    fr = dict(total=summary["freelancer"]["total"])
    print(json.dumps({k: summary[k] for k in ("runs", "measured_m3", "conflict", "held", "held_no_value",
                                              "t229_leftovers")}, ensure_ascii=False))
    for st in STOREYS:
        print(st, json.dumps(tot[st]), "| released", RELEASED[st]["measured"], "| reconcile", json.dumps(rec[st]))
        p = part[st]
        print("   partition", json.dumps({k: v for k, v in p.items() if k not in ("double_solid_column",
                                                                                  "carried_member_under_beam")}))
        print("   double SOLID", p["double_solid_column"])
        print("   carried", p["carried_member_under_beam"])
    print("freelancer", fr_st, fr["total"])
    print("by mark", json.dumps(summary["freelancer"]["by_class"]))
    if "--write" in argv:
        cols = ["run", "storey", "mark", "member", "pieces", "status", "length_m", "b_drawn_m", "depth_m", "m3",
                "m3_low", "m3_high", "released_m3", "released_bounded", "adds", "deducts", "designer", "source",
                "reason"]
        with open(HERE / "LEDGER_T241.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                r = dict(r)
                r["adds"] = "; ".join("%s %+.4f" % (n, v) for n, v in r["adds"])
                r["deducts"] = "; ".join("%s -%.4f" % (n, v) for n, v in r["deducts"])
                w.writerow(r)
        with open(HERE / "BY_MARK_T241.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(marks[0]))
            w.writeheader()
            w.writerows(marks)
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
        print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
