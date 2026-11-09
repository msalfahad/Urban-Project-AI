"""T-545 development-villa run (research, unwired): B10-07 beam concrete on the candidate of record V3.0.58 against the
freelancer's beam sheet, by component (R-T545-1 .. 3, on top of R-T395-1 .. 5).

    .work/venv/bin/python -I research/agents_t545/t545_alsenan.py \
        --freelancer .work/private/concrete_rebar.xlsx --bands .work/private/t545/bands.json [--write]

bands.json: `python3 -I research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g <out>`.

Engine lines: research/agents_t507/out/LINE_INDEX_V3_0_57.json (V3.0.58 changes FIN.WP.ROOF / ROOF_UPTURN only,
R-T507-1 (e)); joined to the committed V3.0.21 file (dimensions, floor) and checked line by line: 191 STR.CONC.BEAM ids,
element ids equal; values equal to 6 dp except the four T-397 VERIFIED corrections (+0.003174 m3 in total).
Mark / run / support data: T-252 ledger r2, T-110 member register, T-229 support input (as T-395).
Freelancer: Drive "Alsenan chalet project", the concrete + rebar workbook, beam sheet (read with openpyxl, formulas and
values); his rows stay in .work/private/t545. Tracked output: out/T545_BEAM_RECONCILE.json (engine figures and component
terms in m3 per storey, his per-storey row sums; no row, length or count of his).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RES / "agents_t395"))
import t395_alsenan as T  # noqa: E402  (read-only library use of the merged T-395 run)
import t545_rules as R  # noqa: E402

LINE_INDEX = RES / "agents_t507" / "out" / "LINE_INDEX_V3_0_57.json"
OUT = HERE / "out" / "T545_BEAM_RECONCILE.json"
PRIVATE = HERE.parents[2] / "private" / "t545"
FLOORS = ("GF", "1F", "2F")
CLASS_TO_STATUS = {"RELEASED": "VALUED", "HELD": "HELD", "EXCLUDED": "NOT_APPLICABLE"}
T397_CORRECTED = {"L-7c1a1da8004c4272ccba", "L-9270e8b8860414386adb", "L-9a55aadc9f0880ae37a7",
                  "L-cbf53752cfd897c35c2c"}
ENGINE_RELEASED_M3 = Decimal("66.321054")
_LOAD_V3021 = T.load_lines                      # the merged T-395 reader of the V3.0.21 / V3.0.29 lines
HELD_BOUND = (Decimal("8.372829"), Decimal("13.779510"))


def d6(x):
    return Decimal(str(x)).quantize(R.Q6)


def index_lines():
    d = json.loads(LINE_INDEX.read_text(encoding="utf-8"))
    assert d["candidate_version"] == "ARCH_TAKEOFF_V3.0.57"
    return {ln["line_id"]: ln for ln in d["lines"]}


def load_lines_v3058():
    """V3.0.21 line records (dimensions / floor) with the V3.0.58 (= V3.0.57) value, class and held bound."""
    base, status21 = _LOAD_V3021()
    idx = {k: v for k, v in index_lines().items() if v["item_code"] == "STR.CONC.BEAM"}
    assert set(idx) == set(base), "beam line ids differ between V3.0.21 and V3.0.58"
    lines, status = {}, {}
    for k, ln in base.items():
        x = idx[k]
        assert x["element_id"] == ln["element_id"], k
        st = CLASS_TO_STATUS[x["class"]]
        assert st == status21[k], (k, st, status21[k])          # no line changed status since V3.0.29
        rec = dict(ln)
        if st == "VALUED":
            old, new = d6(ln["measured_net"]), d6(x["measured_net"])
            assert (old == new) != (k in T397_CORRECTED), (k, old, new)
            rec["measured_net"] = float(x["measured_net"])
            rec["v3021_m3"] = ln["measured_net"]
        rec["held_low"], rec["held_high"] = x["held_low"], x["held_high"]
        lines[k], status[k] = rec, st
    tot = sum((d6(v["measured_net"]) for k, v in lines.items() if status[k] == "VALUED"), Decimal(0))
    assert tot == ENGINE_RELEASED_M3, tot
    lo = sum((d6(v["held_low"]) for v in lines.values() if v["held_low"] is not None), Decimal(0))
    hi = sum((d6(v["held_high"]) for v in lines.values() if v["held_high"] is not None), Decimal(0))
    assert (lo, hi) == HELD_BOUND, (lo, hi)
    return lines, status


def run_build(freelancer, bands):
    T.load_lines = load_lines_v3058
    try:
        runs, marks, his, sub, his_slab, sup = T.build(freelancer, bands)
        lines, _ = load_lines_v3058()
        db = T.depth_basis(runs, marks, his, his_slab)
    finally:
        T.load_lines = _LOAD_V3021
    for r in runs:
        ln = lines[r["line_id"]]
        r["held_low"], r["held_high"] = ln["held_low"], ln["held_high"]
        r["t397"] = r["line_id"] in T397_CORRECTED
    return runs, marks, his, sub, his_slab, sup, db, lines


def components_by_floor(marks):
    """R-T545-1 component terms per storey (Decimal), from the per-mark R-T395-3 / -4 splits."""
    comp = {f: defaultdict(Decimal) for f in FLOORS}
    eng = {f: Decimal(0) for f in FLOORS}
    hisr = {f: Decimal(0) for f in FLOORS}
    held_share = {f: Decimal(0) for f in FLOORS}
    detail = []
    for m in marks:
        s, ls, f = m["split"], m["length"], m["floor"]
        eng[f] += d6(s["engine"])
        hisr[f] += d6(s["his"])
        row = {"floor": f, "mark": m["mark"]}
        if m["mark"] == "DOME_RING":
            k = {"DOME_RING": d6(s.get("SCOPE", 0))}
        elif m["mark"].endswith(" upstand"):
            k = {"UPSTAND": d6(s["COUNT"])}
        else:
            k = {"COUNT": d6(s["COUNT"]), "SECTION": d6(s["SECTION"]), "HELD": d6(s["HELD"]),
                 "THROUGH_SUPPORT": d6(ls["THROUGH_SUPPORT"]), "RUN_COUNT": d6(ls["RUN_COUNT"]),
                 "UNTRACED": d6(ls["UNTRACED"])}
        # 6-dp bookkeeping: the terms of one mark re-add to its own residual
        resid = d6(s["engine"]) - d6(s["his"])
        gap = resid - sum(k.values(), Decimal(0))
        if gap:
            assert abs(gap) <= Decimal("0.000003"), (m["mark"], gap)
            k["UNTRACED"] = k.get("UNTRACED", Decimal(0)) + gap
        for n, v in k.items():
            comp[f][n] += v
        if s.get("HELD"):
            held_share[f] += -d6(s["HELD"])
        row.update({n: str(v) for n, v in k.items() if v})
        if any(k.values()):
            detail.append(row)
    return comp, eng, hisr, held_share, detail


def held_beside_his(runs, marks):
    """R-T545-3: every held / unknown line, its V3.0.58 bound, his share at his section (when a row of his carries it)."""
    sec = {(m["floor"], m["mark"]): m["split"].get("his_section") for m in marks}
    # a held run that no row of his can be (R-T395-4 RUN_COUNT binding: he prints fewer rows than the drawn runs)
    no_row = {(m["floor"], run) for m in marks for run, st in m["no_row"] if st != "VALUED"}
    out = []
    for r in runs:
        if r["status"] != "HELD":
            continue
        mark = r.get("held_mark") or r["mark"]
        hs = sec.get((r["floor"], mark))
        share = None
        if hs and r["L"] and (r["floor"], r["run"]) not in no_row:
            share = d6(Decimal(str(hs[0])) * Decimal(str(hs[1])) * Decimal(str(r["L"])))
        cls = R.held_bound_class(share, r["held_low"], r["held_high"]) if share is not None else (
            "NO_ROW_OF_HIS" if r["held_low"] is not None else "NO_ROW_OF_HIS, UNBOUNDED")
        out.append({"line_id": r["line_id"], "floor": r["floor"], "run": r["run"], "mark": mark,
                    "engine_low_m3": None if r["held_low"] is None else str(d6(r["held_low"])),
                    "engine_high_m3": None if r["held_high"] is None else str(d6(r["held_high"])),
                    "his_share_m3": None if share is None else str(share), "class": cls,
                    "reason": (r.get("reason") or "")[:160], "designer": (r.get("designer") or "")[:80]})
    return out


def overlap_census(runs, lines, db):
    """R-T545-2 on the candidate: beam / slab basis per storey, beam / column DOUBLE joints owned once, every band
    piece in one line."""
    owners = [{"line_id": r["line_id"], "owns": list(r["pieces"])} for r in runs if r["pieces"]]
    once = R.joints_once(owners)
    led = csv.DictReader((RES / "agents_t252" / "LEDGER_T252.csv").open(encoding="utf-8"))
    joints = []
    for r in led:
        if r["status"] == "SUPERSEDED_R2":
            continue
        for m in re.finditer(r"T-229 DOUBLE column (\w+) \(column owns[^)]*\) (-?\d+\.\d+)", r["deducts"]):
            joints.append({"run": r["run"], "mark": r["mark"], "column_handle": m.group(1),
                           "deducted_from_beam_m3": m.group(2)})
    cols = [j["column_handle"] for j in joints]
    assert len(cols) == len(set(cols)), "one column joint deducted from two beams"
    basis = {f: {"his_slab_basis": db[f]["his_slab_basis"], "engine": "FULL depth, slab NET",
                 "engine_slab_net_m2": db[f]["engine_slab_net_m2"], "beam_plan_m2": db[f]["beam_plan_m2"],
                 "depth_basis_term_m3": db[f]["depth_basis_term_m3"],
                 "exposure_if_one_side_downstand_m3": db[f]["b_L_t_on_valued_runs_m3 (moves only if one side read DOWNSTAND)"]}
             for f in FLOORS}
    return {"pieces_owned_once": once, "beam_column_joints_deducted": joints,
            "beam_column_joints_total_m3": str(sum((Decimal(j["deducted_from_beam_m3"]) for j in joints), Decimal(0))),
            "beam_slab_basis": basis}


def outside_family(idx):
    """Neighbouring families the task names, kept OUT of the beam residual (each has its own owner / line)."""
    fam = defaultdict(lambda: {"released_lines": 0, "released_m3": Decimal(0), "held_lines": 0, "excluded_lines": 0})
    for ln in idx.values():
        code = ln["item_code"]
        if code in ("STR.CONC.LINTEL", "STR.CONC.GROUND_BEAM") or ln["element_id"].startswith("LIFT_TIE_BEAM"):
            key = code if not ln["element_id"].startswith("LIFT_TIE_BEAM") else ln["element_id"] + " " + code
            if ln["class"] == "RELEASED":
                fam[key]["released_lines"] += 1
                fam[key]["released_m3"] += d6(ln["measured_net"])
            elif ln["class"] == "HELD":
                fam[key]["held_lines"] += 1
            else:
                fam[key]["excluded_lines"] += 1
    return {k: {**v, "released_m3": str(v["released_m3"])} for k, v in sorted(fam.items())}


def his_other_sheets(path):
    """Which of his sheets could carry a beam-like solid (names / labels only, no values tracked)."""
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    lab = {}
    for n in wb.sheetnames:
        ws = wb[n]
        lab[n] = [str(ws.cell(r, 1).value).strip() for r in range(1, ws.max_row + 1)
                  if isinstance(ws.cell(r, 1).value, str)]
    hits = {n: [x for x in v if re.search(r"عتب|رباط|حلق|ring|lintel|tie", x, re.I)] for n, v in lab.items()}
    return {"sheets_with_lintel_tie_or_ring_label": {k: len(v) for k, v in hits.items() if v}}


def build(freelancer, bands):
    runs, marks, his, sub, his_slab, sup, db, lines = run_build(freelancer, bands)
    comp, eng, hisr, held_share, detail = components_by_floor(marks)
    floors = {}
    for f in FLOORS:
        tbl = R.component_table(eng[f], hisr[f], {k: v for k, v in comp[f].items()}, held_his_share=held_share[f])
        tbl["his_printed_subtotal_minus_rows_m3"] = str(d6(sub[f]) - hisr[f])
        floors[f] = tbl
    allc = defaultdict(Decimal)
    for f in FLOORS:
        for k, v in comp[f].items():
            allc[k] += v
    E, F = sum(eng.values(), Decimal(0)), sum(hisr.values(), Decimal(0))
    assert E == ENGINE_RELEASED_M3, E
    total = R.component_table(E, F, dict(allc), held_his_share=sum(held_share.values(), Decimal(0)))
    printed = sum((d6(v) for v in sub.values()), Decimal(0))
    total["his_printed_total_m3"] = str(printed)
    total["his_printed_minus_rows_m3 (BM-ARITH, his 1F sub-total leaves his first 1F row out)"] = str(printed - F)
    total["residual_vs_his_printed_m3"] = str(E - printed)
    held = held_beside_his(runs, marks)
    roll = {}
    for name, sel in (("with_his_row", lambda h: h["his_share_m3"] is not None),
                      ("no_row_of_his_bounded", lambda h: h["his_share_m3"] is None and h["engine_low_m3"]),
                      ("no_row_of_his_unbounded", lambda h: h["his_share_m3"] is None and not h["engine_low_m3"])):
        hs = [h for h in held if sel(h)]
        roll[name] = {"lines": len(hs),
                      "engine_low_m3": str(sum((Decimal(h["engine_low_m3"]) for h in hs if h["engine_low_m3"]), Decimal(0))),
                      "engine_high_m3": str(sum((Decimal(h["engine_high_m3"]) for h in hs if h["engine_high_m3"]), Decimal(0))),
                      "his_share_m3": str(sum((Decimal(h["his_share_m3"]) for h in hs if h["his_share_m3"]), Decimal(0))),
                      "classes": sorted({h["class"] for h in hs})}
    assert sum(r["lines"] for r in roll.values()) == len(held)
    assert Decimal(roll["with_his_row"]["his_share_m3"]) == -Decimal(total["components"]["HELD"]["m3"])
    total["held_rollup"] = roll
    t397 = sum((d6(lines[k]["measured_net"]) - d6(lines[k]["v3021_m3"]) for k in T397_CORRECTED), Decimal(0))
    doc = {
        "schema": "T545_BEAM_RECONCILE_V1",
        "candidate": "ARCH_TAKEOFF_V3.0.58 (beam lines = V3.0.57 LINE_INDEX, R-T507-1 (e)); NOT RELEASED",
        "family": "STR.CONC.BEAM (B10-07)",
        "engine": {"released_lines": sum(1 for r in runs if r["status"] == "VALUED"),
                   "released_m3": str(E), "held_lines": sum(1 for r in runs if r["status"] == "HELD"),
                   "held_bound_m3": [str(HELD_BOUND[0]), str(HELD_BOUND[1])],
                   "held_unknown_lines": sum(1 for r in runs if r["status"] == "HELD" and r["held_low"] is None),
                   "excluded_lines": sum(1 for v in index_lines().values()
                                         if v["item_code"] == "STR.CONC.BEAM" and v["class"] == "EXCLUDED"),
                   "since_T395_V3_0_29_m3": str(t397),
                   "since_T395_cause": "T-397 VERIFIED corrections on 4 GF lines (CB8 BAND0039, CB1 BAND0041.2, "
                                       "B8 BAND0003, B7 BAND0006: T-392 R-T392-1 ring-overlap gap restored, T-387 "
                                       "CB8 end DOUBLE / GAP)"},
        "total": total, "floors": floors, "marks": detail, "held_beside_his": held,
        "overlap": overlap_census(runs, lines, db), "outside_family": outside_family(index_lines()),
        "his_sheets": his_other_sheets(freelancer),
        "note": "engine figures and component terms only; his rows / lengths stay in .work/private/t545",
    }
    return doc, runs, marks, his


def write_private(runs, marks, his):
    PRIVATE.mkdir(parents=True, exist_ok=True)
    assert HERE.parents[1].resolve() not in PRIVATE.resolve().parents
    (PRIVATE / "HIS_ROWS_T545.json").write_text(json.dumps(his, ensure_ascii=False, indent=1), encoding="utf-8")
    with (PRIVATE / "MARKS_T545.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["floor", "mark", "engine", "his", "split", "length", "allowance_m", "his_rows", "held_runs"])
        for m in marks:
            w.writerow([m["floor"], m["mark"], m["split"]["engine"], m["split"]["his"], json.dumps(m["split"]),
                        json.dumps(m["length"]), m["allowance_m"], m["his_rows"], json.dumps(m["held_runs"])])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--freelancer", required=True)
    ap.add_argument("--bands", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    doc, runs, marks, his = build(a.freelancer, a.bands)
    print(json.dumps({"total": doc["total"], "floors": doc["floors"], "engine": doc["engine"]}, indent=1,
                     ensure_ascii=False))
    for h in doc["held_beside_his"]:
        print(h)
    print(json.dumps(doc["overlap"], indent=1))
    print(json.dumps(doc["outside_family"], indent=1), doc["his_sheets"])
    if a.write:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        write_private(runs, marks, his)
        print("->", OUT)


if __name__ == "__main__":
    main()
