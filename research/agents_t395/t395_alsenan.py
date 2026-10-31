"""T-395 Alsenan: BM-GF, BM-1F and BM-2F of T-385 r2 traced to depth basis / length basis / section / count / held
(research only: no quantity, line, state or released cell changes).

Inputs (committed unless marked):
  research/agents_t332/CANDIDATE_V3021_CONCRETE_LINES.json  beam lines; asserted equal (ids, element ids, values) to the
      V3.0.29 binding research/agents_t387/BINDING_T387.csv of the reproduced candidate of record
  research/agents_t252/LEDGER_T252.csv      beam ledger r2 (runs, marks, pieces, drawn b, D, length, held ranges)
  research/agents_t110/BEAM_MEMBER_REGISTER.csv  band -> member / mark for the route G lines the ledger shares
  research/agents_t229/ALSENAN_BEAM_SUPPORT_INPUT.json  piece ends (support / carrier), support gaps, column outlines
  research/agents_t234/LEDGER_T234.csv     slab panels (net of the beam plan) for the depth-basis check
  .work/private/t395/SPANS_T395.json        own face-to-face spans of the 5 largest beams per floor (t395_spans.py) [private]
  the concrete + rebar workbook, sheets 'كمرات' (rows 11 .. 50, 59 .. 78, 86 .. 95) and 'بلاطات ' (rows 11, 16, 23, 24)
                                                                                                        [private]
Outputs: .work/private/t395/RECON_T395.csv (per storey x mark, his rows and lengths beside the engine) and RUNS_T395.csv
(per engine run); the engine-side summary research/agents_t395/summary_t395.json (engine figures and cause terms in m3 per
storey; no row, count, length or dimension of the workbook).

    python3 -I research/agents_t395/t395_alsenan.py --freelancer <private>/concrete_rebar.xlsx [--write]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t395_rules as R  # noqa: E402

RES = HERE.parent
PRIVATE = HERE.parents[2] / "private" / "t395"
SHEET = "كمرات"
SLAB_SHEET = "بلاطات "
HIS_ROWS = {"GF": range(11, 51), "1F": range(59, 79), "2F": range(86, 96)}
HIS_SUBTOTAL = {"GF": 54, "1F": 82, "2F": 96}
HIS_SLAB_ROWS = {"GF": (11,), "1F": (16,), "2F": (23, 24)}
SLAB_T = {"GF": 0.16, "1F": 0.16, "2F": 0.16}       # printed slab thickness of the roof slabs over the beams (S.S 16 CM)
FLOORS = ("GF", "1F", "2F")
CAND = re.compile(r"candidates? (C?B\d+)")


def load_lines():
    d = json.loads((RES / "agents_t332" / "CANDIDATE_V3021_CONCRETE_LINES.json").read_text(encoding="utf-8"))
    lines = {ln["line_id"]: ln for ln in d["lines"] if ln["item_code"] == "STR.CONC.BEAM"}
    b = {r["line_id"]: r for r in csv.DictReader((RES / "agents_t387" / "BINDING_T387.csv").open(encoding="utf-8"))
         if r["item_code"] == "STR.CONC.BEAM"}
    assert set(b) == set(lines), "beam line ids differ from the V3.0.29 binding"
    for k, r in b.items():
        ln = lines[k]
        assert r["element_id"] == ln["element_id"]
        if r["status"] == "VALUED":
            assert abs(float(r["valued_m3"]) - ln["measured_net"]) < 1e-6
        else:
            assert ln["measured_net"] is None
    return lines, {k: r["status"] for k, r in b.items()}


def load_support():
    led = {r["run"]: r for r in csv.DictReader((RES / "agents_t252" / "LEDGER_T252.csv").open(encoding="utf-8"))}
    reg = list(csv.DictReader((RES / "agents_t110" / "BEAM_MEMBER_REGISTER.csv").open(encoding="utf-8")))
    sup = json.loads((RES / "agents_t229" / "ALSENAN_BEAM_SUPPORT_INPUT.json").read_text(encoding="utf-8"))
    return led, reg, sup


def _piece_key(storey, band, known):
    k = f"{storey}:{band}"
    if k in known:
        return k
    sub = [x for x in known if x.startswith(k + ".")]
    return sub[0] if len(sub) == 1 else k


def runs_from_lines(lines, status, led, reg, sup):
    """One record per candidate beam line that is not superseded: run, mark, pieces, section, length, value / held."""
    pieces = sup["pieces"]
    led_by_piece = {}
    for r in led.values():
        if r["status"] == "SUPERSEDED_R2":
            continue
        for p in re.split(r"[;|]", r["pieces"]):
            led_by_piece.setdefault(p.strip(), []).append(r)
    reg_by_comp = defaultdict(list)
    for r in reg:
        reg_by_comp[r["component"]].append(r)
    out = []
    for lid, ln in sorted(lines.items()):
        if status[lid] == "NOT_APPLICABLE":
            continue
        eid, fl = ln["element_id"], ln["floor"]
        rec = {"line_id": lid, "element_id": eid, "floor": fl, "status": status[lid], "m3": ln["measured_net"],
               "state": ln["evidence_state"]}
        if eid.startswith("HL:BEAM_LEDGER:"):
            r = led[eid.split(":", 3)[3]]
            pcs = [p.strip() for p in re.split(r"[;|]", r["pieces"]) if re.match(r"^(GF|1F|2F):BAND", p.strip())]
            rec.update(run=r["run"], mark=r["mark"], pieces=pcs, b=r["b_drawn_m"], D=r["depth_m"], L=r["length_m"],
                       low=r["m3_low"], high=r["m3_high"], designer=r["designer"], reason=r["reason"])
        elif eid.startswith(("P-C:BEAMS:", "U-C:BEAMS:")):
            _, _, f, band = eid.split(":")
            key = _piece_key(f, band, set(led_by_piece) | set(pieces))
            rs = led_by_piece.get(key, [])
            rg = reg_by_comp.get("BEAMS:" + key, [])
            mark = rs[0]["mark"] if rs else (rg[0]["mark"] if rg else "(none)")
            dm = ln.get("dimensions") or {}
            rec.update(run=rs[0]["run"] if rs else key, mark=mark, pieces=[key], b=dm.get("width_m"),
                       D=dm.get("depth_m"), L=dm.get("length_m"), low="", high="",
                       designer=rs[0]["designer"] if rs else "", reason=rs[0]["reason"] if rs else "")
            if rg and rec["status"] != "VALUED":
                m = CAND.search(rg[0].get("evidence", "") + " " + rg[0].get("conflict", ""))
                rec["candidate_mark"] = m.group(1) if m else ""
        else:                                    # dome ring lines: stair / dome family scope (T-398)
            rec.update(run=eid, mark="DOME_RING", pieces=[], b=None, D=None, L=None, low="", high="")
        for k in ("b", "D", "L"):
            rec[k] = float(rec[k]) if rec[k] not in ("", None) else None
        if rec["status"] == "VALUED" and rec["b"] and rec["D"]:
            rec["L_eff"] = rec["m3"] / (rec["b"] * rec["D"])      # net plan / b: the billed face-to-face length
        out.append(rec)
    return out


def assign_held_marks(runs, sup):
    """A held run with no printed mark gets the ledger's candidate mark, else the mark of the labelled piece it shares
    a support gap with (same storey). Its value stays HELD; the mark only says which of his rows may carry it."""
    piece_mark = {}
    for r in runs:
        if r["mark"] not in ("(none)", "DOME_RING"):
            for p in r["pieces"]:
                piece_mark[p] = r["mark"]
    for r in runs:
        r["held_mark"] = ""
        if r["status"] == "VALUED" or r["mark"] == "DOME_RING":
            continue
        if r["mark"] != "(none)" and not r["mark"].startswith("CB3 and"):
            continue
        if r.get("candidate_mark"):
            r["held_mark"] = r["candidate_mark"]
            continue
        for g in sup["gaps"]:
            for a, b in ((g["a"], g["b"]), (g["b"], g["a"])):
                if a in r["pieces"] and piece_mark.get(b):
                    r["held_mark"] = r["held_mark"] or piece_mark[b]
        if r["mark"].startswith("CB3 and") and not r["held_mark"]:
            r["held_mark"] = "CB3"


def allowance(pcs, sup, piece_width):
    """R-T395-4 support allowance (m) of a set of pieces: interior gaps + end support extents along the axis."""
    if not pcs:
        return 0.0, []
    O = sup["outlines"]
    items = []
    seen = set()
    for g in sup["gaps"]:
        if g["a"] in pcs or g["b"] in pcs:
            k = (g["a"], g["b"])
            if k not in seen:
                seen.add(k)
                items.append(("GAP", f"{g['a']}|{g['b']}", g["members"][0][0], g["length_m"]))
    for e in sup["ends"]:
        if e["piece"] not in pcs:
            continue
        if e["touch"] in ("SUPPORT", "CARRIED"):
            cols = [m[0] for m in e["members"] if m[0] in O]
            if not cols:
                continue
            o = O[cols[0]]
            ax = e.get("axis")
            ext = (o["w_mm"] if ax == "X" else o["d_mm"] if ax == "Y" else max(o["w_mm"], o["d_mm"])) / 1000.0
            items.append(("END_COLUMN", e["piece"], cols[0], ext))
        elif e["touch"] == "BEAM":
            ws = [piece_width.get(m[0]) for m in e["members"] if m[1] == "BEAM" and piece_width.get(m[0])]
            if ws:
                items.append(("END_BEAM", e["piece"], e["members"][0][0], max(ws)))
    return round(sum(x[3] for x in items), 6), items


def his_rows(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[SHEET]
    rows = []
    for fl, rng in HIS_ROWS.items():
        mark = None
        for r in rng:
            a = ws.cell(r, 1).value
            b, c, d, n = (ws.cell(r, k).value for k in (2, 3, 4, 6))
            if isinstance(a, str) and a.strip():
                mark = re.sub(r"^[BG](?=CB)", "", a.strip())       # his 'BCB1' / 'GCB9' = schedule CB1 / CB9
            if not isinstance(b, (int, float)):
                continue
            # his columns B / C / D read on the rows: width, overall depth, length (header words 'length' /
            # 'height' do not match the values: C equals the schedule depth on every row)
            rows.append({"floor": fl, "row": r, "mark": mark, "b": float(b), "D": float(c), "L": float(d),
                         "n": int(n or 1), "m3": float(ws.cell(r, 9).value)})
    sub = {fl: float(ws.cell(r, 9).value) for fl, r in HIS_SUBTOTAL.items()}
    sl = wb[SLAB_SHEET]
    slab = {fl: {"area": sum(float(sl.cell(r, 2).value) for r in rr),
                 "m3": sum(float(sl.cell(r, 9).value) for r in rr)} for fl, rr in HIS_SLAB_ROWS.items()}
    return rows, sub, slab


def slab_net_area():
    """Engine slab panels per floor (T-234 ledger, net of the beam plan) in m2."""
    p = RES / "agents_t234" / "LEDGER_T234.csv"
    if not p.exists():
        return {}
    tot = defaultdict(float)
    for r in csv.DictReader(p.open(encoding="utf-8")):
        try:
            tot[r.get("storey") or r.get("floor")] += float(r.get("area_m2") or r.get("net_m2") or 0)
        except ValueError:
            pass
    return dict(tot)


def axis_of_ends(sup, bands):
    """Annotate each support end with its axis (X / Y) from the band polygon, so a column's extent along the beam is
    read from its own outline (w = x extent, d = y extent: checked on the 36 support gaps, T-395 s.3)."""
    import math
    for e in sup["ends"]:
        st, band = e["piece"].split(":")
        p = bands.get(f"{band}@{st}")
        if not p:
            continue
        pts = p["pts"]
        best = max(((pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))),
                   key=lambda s: math.dist(s[0], s[1]))
        dx, dy = abs(best[1][0] - best[0][0]), abs(best[1][1] - best[0][1])
        e["axis"] = "X" if dx > 5 * dy else "Y" if dy > 5 * dx else "OBLIQUE"


def build(freelancer, bands_path):
    lines, status = load_lines()
    led, reg, sup = load_support()
    bands = json.loads(Path(bands_path).read_text(encoding="utf-8"))
    axis_of_ends(sup, bands)
    runs = runs_from_lines(lines, status, led, reg, sup)
    assign_held_marks(runs, sup)
    piece_width = {k: v["width_m"] for k, v in sup["pieces"].items() if v.get("width_m")}
    his, sub, his_slab = his_rows(freelancer)
    groups = defaultdict(lambda: {"valued": [], "held": [], "held_open": [], "his": []})
    for r in runs:
        if r["status"] == "VALUED":
            groups[(r["floor"], r["mark"])]["valued"].append(r)
        else:
            m = r["held_mark"] or r["mark"]
            groups[(r["floor"], m)]["held" if r["L"] else "held_open"].append(r)
    for h in his:
        groups[(h["floor"], h["mark"])]["his"].append(h)
    marks = []
    for (fl, mark), g in sorted(groups.items()):
        val = [(r["b"], r["D"], r["L_eff"]) for r in g["valued"] if r.get("L_eff")]
        extra = [r for r in g["valued"] if not r.get("L_eff")]        # valued lines without a section (dome ring)
        hisr = [(h["b"], h["D"], h["L"], h["n"]) for h in g["his"]]
        pcs = sorted({p for r in g["valued"] + g["held"] for p in r["pieces"]})
        allow, items = allowance(pcs, sup, piece_width)
        held_runs = list(g["held"])
        no_row = []
        if g["his"] and not extra:
            no_row = unmatched_runs(g)
            held_runs = [r for r in held_runs if r not in no_row]
        if mark == "DOME_RING" or (extra and not val):
            sp = {"engine": round(sum(r["m3"] for r in extra), 6), "his": 0.0, "residual": round(sum(r["m3"] for r in extra), 6),
                  "SECTION": 0.0, "HELD": 0.0, "LENGTH": 0.0, "COUNT": 0.0, "SCOPE": round(sum(r["m3"] for r in extra), 6)}
        else:
            sp = R.mark_split(val, [r["L"] for r in held_runs], hisr)
        ls = {"THROUGH_SUPPORT": 0.0, "RUN_COUNT": 0.0, "UNTRACED": 0.0}
        if sp.get("his_section") and sp["LENGTH"]:
            bh, Dh = sp["his_section"]
            run_count = round(min(sum(bh * Dh * r["L_eff"] for r in no_row if r["status"] == "VALUED"),
                                  max(sp["LENGTH"], 0.0)), 6)
            ls = R.length_split(sp["LENGTH"], bh, Dh, allow, run_count_m3=run_count)
        marks.append({"floor": fl, "mark": mark, "split": sp, "length": ls, "allowance_m": allow,
                      "allow_items": items, "n_valued": len(g["valued"]), "n_held": len(g["held"]) + len(g["held_open"]),
                      "held_open": [r["run"] for r in g["held_open"]],
                      "no_row": [(r["run"], r["status"]) for r in no_row],
                      "held_runs": [(r["run"], r["low"], r["high"], r.get("designer", "")) for r in g["held"] + g["held_open"]],
                      "his_rows": [h["row"] for h in g["his"]], "his_n": sum(h["n"] for h in g["his"])})
    return runs, marks, his, sub, his_slab, sup


def unmatched_runs(g):
    """Engine runs of the mark that no row of his can be (R-T395-4 RUN_COUNT): only when he prints fewer rows than the
    drawn runs. Each of his rows (longest first) takes the drawn run closest to it in length; continuous marks (CB..)
    are one run (his rows run over all spans). A held run left over has no row on either side: it leaves the HELD term
    (it is carried as HELD, open) instead of being charged against his rows."""
    eng = [r for r in g["valued"] if r.get("L_eff")] + g["held"]
    hisL = sorted([h["L"] for h in g["his"] for _ in range(h["n"])], reverse=True)
    if not eng or len(hisL) >= len(eng) or (g["his"] and g["his"][0]["mark"].startswith("CB")):
        return []
    left = list(eng)

    def ln(r):
        return r.get("L_eff") or r["L"]
    for L in hisL:
        if not left:
            break
        best = min(left, key=lambda r: abs(ln(r) - L))
        left.remove(best)
        took = ln(best)
        # one row of his may run over several drawn runs of the mark (through the supports between them)
        for r in sorted(left, key=ln, reverse=True):
            if took + ln(r) <= L + 0.05:
                left.remove(r)
                took += ln(r)
    return left


def depth_basis(runs, marks, his, his_slab):
    """R-T395-1 on Alsenan: which depth basis each side uses, from the drawn / printed figures.

    Engine: beam lines at the printed overall depth (ledger D = schedule D) and slab lines NET of the beam plan (face
    area, members' overlap deducted). His side: his beam rows carry the schedule's overall depth in column C on every
    row, and his slab area per floor is compared with the engine's NET and GROSS (net + beam plan) slab areas."""
    d = json.loads((RES / "agents_t332" / "CANDIDATE_V3021_CONCRETE_LINES.json").read_text(encoding="utf-8"))
    net = defaultdict(float)
    for ln in d["lines"]:
        if ln["item_code"] == "STR.CONC.SLAB" and ln.get("measured_net") is not None:
            net[ln["floor"]] += (ln.get("dimensions") or {}).get("area_m2") or 0.0
    plan = defaultdict(float)
    for r in runs:
        if r["status"] == "VALUED" and r.get("L_eff"):
            plan[r["floor"]] += r["b"] * r["L_eff"]
        elif r["status"] != "VALUED" and r["b"] and r["L"]:
            plan[r["floor"]] += r["b"] * r["L"]
    sched = {}
    for m in marks:
        if m["split"].get("his_section"):
            sched[(m["floor"], m["mark"])] = m["split"]["his_section"]
    eng_depth = defaultdict(set)
    for r in runs:
        if r["D"]:
            eng_depth[(r["floor"], r["mark"])].add(r["D"])
    same = all(sched[k][1] in eng_depth[k] for k in sched if eng_depth.get(k))
    out = {}
    for fl in FLOORS:
        gross = net[fl] + plan[fl]
        basis = R.slab_basis_from_area(his_slab[fl]["area"], net[fl], gross)
        runs_t = [(r["b"], r.get("L_eff") or r["L"], SLAB_T[fl]) for r in runs
                  if r["floor"] == fl and r["status"] == "VALUED" and r.get("L_eff")]
        if_downstand = R.depth_basis_term(runs_t, "FULL", "DOWNSTAND")
        out[fl] = {"engine_slab_net_m2": round(net[fl], 3), "beam_plan_m2": round(plan[fl], 3),
                   "engine_slab_gross_m2": round(gross, 3), "his_slab_basis": basis,
                   "his_beam_depth_equals_schedule_on_every_common_mark": same,
                   "depth_basis_term_m3": R.depth_basis_term(runs_t, "FULL", "FULL" if (basis == "NET" and same) else "DOWNSTAND"),
                   "b_L_t_on_valued_runs_m3 (moves only if one side read DOWNSTAND)": if_downstand}
    return out


def top_spans(marks, spans):
    """Own face-to-face (edge lines) of the 5 largest valued runs per floor, beside the engine's billed length, and the
    class his row of that mark is: FACE_TO_FACE (|his - drawn| <= 0.05 m), THROUGH_SUPPORT (within the allowance), or
    BEYOND (longer than the allowance) / SHORTER; private detail keeps his lengths."""
    mk = {(m["floor"], m["mark"]): m for m in marks}
    out = []
    for lid, sp in spans.items():
        m = mk.get((sp["floor"], sp["mark"]))
        cls = "NO_ROW"
        if m and m["split"].get("L_his") is not None:
            s = m["split"]
            drawn = s["L_engine_valued"] + s["L_held"]
            y = s["L_his"] - drawn
            cls = ("FACE_TO_FACE" if abs(y) <= 0.05 else "THROUGH_SUPPORT" if 0 < y <= m["allowance_m"] + 0.01
                   else "BEYOND_ALLOWANCE" if y > 0 else "SHORTER")
        out.append({"floor": sp["floor"], "mark": sp["mark"], "run": sp["run"], "line_id": lid,
                    "engine_m3": round(sp["engine_m3"], 6), "engine_L_m": round(sp["engine_L_eff"], 4),
                    "own_edge_f2f_m": sp["f2f_m"], "edge_handles": sorted({e["handle"] for p in sp["pieces"]
                                                                           for e in p.get("edges", [])}),
                    "end_supports": sorted({(x["handle"], x["along_axis_m"]) for x in sp["supports"]}),
                    "engine_minus_edges_m": round(sp["engine_L_eff"] - sp["f2f_m"], 4), "his_mark_class": cls})
    return out


def totals(marks):
    t = defaultdict(lambda: defaultdict(float))
    for m in marks:
        s, ls, f = m["split"], m["length"], m["floor"]
        t[f]["engine"] += s["engine"]
        t[f]["his_rows"] += s["his"]
        t[f]["SECTION"] += s["SECTION"]
        t[f]["HELD"] += s["HELD"]
        t[f]["SCOPE"] += s.get("SCOPE", 0.0)
        t[f]["THROUGH_SUPPORT"] += ls["THROUGH_SUPPORT"]
        t[f]["RUN_COUNT"] += ls["RUN_COUNT"]
        t[f]["LENGTH_UNTRACED"] += ls["UNTRACED"]
        if s["COUNT"] > 0:
            t[f]["COUNT_ENGINE_ONLY"] += s["COUNT"]
        elif s["COUNT"] < 0:
            t[f]["COUNT_HIS_ONLY"] += s["COUNT"]
    return {f: {k: round(v, 6) for k, v in d.items()} for f, d in t.items()}


def summary(marks, tot, db, spans, sub):
    """Engine-side summary (tracked): engine figures and cause terms in m3; no row, count, length or dimension of his."""
    per = {}
    for fl in FLOORS:
        t = tot[fl]
        res = round(t["engine"] - t["his_rows"], 6)
        traced = round(t["SECTION"] + t["THROUGH_SUPPORT"] + t["RUN_COUNT"] + t.get("COUNT_ENGINE_ONLY", 0.0)
                       + t.get("COUNT_HIS_ONLY", 0.0) + t["SCOPE"], 6)
        un = round(res - traced - t["HELD"], 6)
        per[fl] = {"engine_valued_m3": round(t["engine"], 6),
                   "residual_vs_his_rows_m3": res,
                   "his_printed_subtotal_minus_rows_m3 (BM-ARITH)": round(sub[fl] - t["his_rows"], 6),
                   "terms_m3": {k: t.get(k, 0.0) for k in ("SECTION", "THROUGH_SUPPORT", "RUN_COUNT", "COUNT_ENGINE_ONLY",
                                                         "COUNT_HIS_ONLY", "SCOPE", "HELD", "LENGTH_UNTRACED")},
                   "closure_m3": {"traced": traced, "held": round(t["HELD"], 6), "untraced": un},
                   "depth_basis": db[fl]}
    marks_out = []
    for m in marks:
        s, ls = m["split"], m["length"]
        if not (s["engine"] or s["his"] or m["n_held"]):
            continue
        marks_out.append({"floor": m["floor"], "mark": m["mark"], "engine_valued_m3": s["engine"],
                          "SECTION": s["SECTION"], "HELD": s["HELD"], "COUNT": s["COUNT"], "SCOPE": s.get("SCOPE", 0.0),
                          "THROUGH_SUPPORT": ls["THROUGH_SUPPORT"], "RUN_COUNT": ls["RUN_COUNT"],
                          "LENGTH_UNTRACED": ls["UNTRACED"], "support_allowance_m": m["allowance_m"],
                          "held_runs": [x[0] for x in m["held_runs"]], "held_no_row": [x[0] for x in m["no_row"]
                                                                                       if x[1] != "VALUED"]})
    doc = {"schema": "T395_SUMMARY_V1", "candidate": "ARCH_TAKEOFF_V3.0.29 beam lines (= committed V3.0.21 file, asserted)",
           "family": "STR.CONC.BEAM", "floors": per, "marks": marks_out, "top_spans": spans,
           "note": "engine-side figures and cause terms only; his rows, counts and lengths are in .work/private/t395"}
    (HERE / "summary_t395.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--freelancer", required=True)
    ap.add_argument("--bands", required=True, help="route G bands json (research/agents_t110/scripts/bands.py)")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    runs, marks, his, sub, his_slab, sup = build(a.freelancer, a.bands)
    tot = totals(marks)
    for f in FLOORS:
        print(f, json.dumps(tot[f]))
    for m in marks:
        print(m["floor"], m["mark"], json.dumps(m["split"]), json.dumps(m["length"]), m["allowance_m"], m["his_rows"],
              m["held_open"])
    db = depth_basis(runs, marks, his, his_slab)
    print(json.dumps(db, indent=1))
    sp_path = PRIVATE / "SPANS_T395.json"
    spans = top_spans(marks, json.loads(sp_path.read_text(encoding="utf-8"))) if sp_path.exists() else []
    for x in spans:
        print(x)
    if a.write:
        write(runs, marks, his, sub, his_slab, tot)
        summary(marks, tot, db, spans, sub)


def write(runs, marks, his, sub, his_slab, tot):
    PRIVATE.mkdir(parents=True, exist_ok=True)
    root = HERE.parents[1].resolve()
    assert root not in PRIVATE.resolve().parents, "private output inside the worktree refused"
    with (PRIVATE / "RUNS_T395.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["line_id", "floor", "run", "mark", "held_mark", "status", "state", "b", "D", "L", "L_eff", "m3",
                    "low", "high", "pieces"])
        for r in runs:
            w.writerow([r["line_id"], r["floor"], r["run"], r["mark"], r.get("held_mark", ""), r["status"], r["state"],
                        r["b"], r["D"], r["L"], round(r.get("L_eff") or 0, 6), r["m3"], r["low"], r["high"],
                        ";".join(r["pieces"])])
    with (PRIVATE / "RECON_T395.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["floor", "mark", "engine_m3", "his_m3", "residual", "SECTION", "HELD", "LENGTH", "COUNT", "SCOPE",
                    "THROUGH_SUPPORT", "RUN_COUNT", "LENGTH_UNTRACED", "L_engine_valued", "L_held", "L_his",
                    "allowance_m", "his_rows", "held_runs"])
        for m in marks:
            s, ls = m["split"], m["length"]
            w.writerow([m["floor"], m["mark"], s["engine"], s["his"], s["residual"], s["SECTION"], s["HELD"],
                        s["LENGTH"], s["COUNT"], s.get("SCOPE", 0), ls["THROUGH_SUPPORT"], ls["RUN_COUNT"],
                        ls["UNTRACED"], s.get("L_engine_valued", ""), s.get("L_held", ""), s.get("L_his", ""),
                        m["allowance_m"], " ".join(map(str, m["his_rows"])), json.dumps(m["held_runs"])])
    (PRIVATE / "HIS_T395.json").write_text(json.dumps({"rows": his, "subtotals": sub, "slab": his_slab},
                                                       ensure_ascii=False, indent=1), encoding="utf-8")
    print("private outputs ->", PRIVATE)


if __name__ == "__main__":
    main()
