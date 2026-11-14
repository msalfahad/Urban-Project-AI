"""T-777 (lane S, DELIVERY MODE F-15): STR.CONC.BEAM candidate vs freelancer, split by named cause (Alsenan; every villa).

    python3 -I research/agents_t777/beam_vs_freelancer.py            # writes research/agents_t777/out/BEAM_CAUSES.{json,md}
    python3 -I research/agents_t777/beam_vs_freelancer.py --check    # synthetic self-test + rebuild must equal the files

Inputs (committed only; no private file is read):
  research/agents_t770/out/LINE_INDEX_V3_0_81.json   newest candidate index (STR.CONC.BEAM lines)
  research/agents_t761/out/FIX_ROWS.json             merged blank-line fill (DEFAULT depths)
  research/agents_t757/out/FIX_ROWS.json             merged ranged-line points
  research/agents_t241/LEDGER_T241.csv               every beam run once (storey, mark, b, D, L, status, designer item)
  tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json his 'كمرات' cells (already committed by T-241; only per storey and
                                                     mark aggregates are written by this script)

Generic rule (BEAM_COMPARE_V1, proposed): a beam total is compared with another takeoff only per storey AND mark, after
(1) the convention of the joint (C1: beam between support faces at full printed depth, slab panel stops at the beam
face) is stated for both sides, (2) the other side's own arithmetic is re-added row by row, (3) each per-mark
difference is split into width, depth and length effects in that order (dV_b = (b_h - b_o) d_o L_o; dV_d = b_h (d_h -
d_o) L_o; dV_L = b_h d_h (L_h - L_o)), so the three effects sum exactly to the difference, and (4) pieces one side has
under no mark are kept as their own cause, never folded into a neighbour to make totals agree.
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
OUT = HERE / "out"
INDEX = "research/agents_t770/out/LINE_INDEX_V3_0_81.json"
FIXES = ("research/agents_t761/out/FIX_ROWS.json", "research/agents_t757/out/FIX_ROWS.json")
LEDGER = "research/agents_t241/LEDGER_T241.csv"
RAW = "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
ITEM = "STR.CONC.BEAM"
MATERIALITY = 0.01      # owner: nothing below 1 % of the line is worked on (DELIVERY_MODE s.3)
TOL = 1e-6


# ------------------------------------------------------------------------------------------------ generic rules (any villa)
def norm_mark(m):
    """'BCB5' / 'GCB9' (his storey-prefixed chain beams) = CB5 / CB9; 'B20 upstand' -> 'B20'."""
    m = (m or "").strip()
    m = re.sub(r"^(BCB|GCB)", "CB", m)
    if not m:
        return m
    return m.split()[0] + (" upstand" if "upstand" in m else "")


def split_effects(b_o, d_o, L_o, b_h, d_h, L_h):
    """Exact split of V_h - V_o into width, depth, length effects (sequential substitution; sums to the difference)."""
    for v in (b_o, d_o, L_o, b_h, d_h, L_h):
        if v is None or v < 0:
            raise ValueError("a dimension is missing or negative: no effect split (never 0 by absence)")
    db = (b_h - b_o) * d_o * L_o
    dd = b_h * (d_h - d_o) * L_o
    dl = b_h * d_h * (L_h - L_o)
    return db, dd, dl


def his_rows_resum(rows):
    """Re-add his rows; return (row sum, rows by storey/mark). His own total is compared separately (arithmetic check)."""
    by = defaultdict(list)
    last = None
    for x in rows:
        m = norm_mark(x["mark"]) if x["mark"] else last
        last = m
        by[(x["storey"], m)].append(x)
    return round(sum(x["m3"] for x in rows), 6), by


def run_dims(r, m3=None):
    """b, D, L of one ledger run. A width CONFLICT run carries the DRAWN width (the T-757 point, geometry first);
    a missing depth is read back from the run's own figure (m3 / (b L)), never defaulted here."""
    b = float(r["b_drawn_m"]) if r.get("b_drawn_m") else None
    if b is None:
        mm = re.search(r"drawn (\d+(?:\.\d+)?)", r.get("reason", ""))
        b = float(mm.group(1)) if mm else None
    L = float(r["length_m"]) if r.get("length_m") else None
    d = float(r["depth_m"]) if r.get("depth_m") else (round(m3 / (b * L), 4) if (m3 and b and L) else None)
    if L is None and m3 and b and d:
        L = round(m3 / (b * d), 4)      # a ring / arc run prints no straight length: its centre length from b, D, m3
    return b, d, L


def classify(storey_mark_engine, storey_mark_his):
    """Per (storey, mark): BOTH / ENGINE_ONLY / HIS_ONLY."""
    out = {}
    for k in set(storey_mark_engine) | set(storey_mark_his):
        a, b = k in storey_mark_engine, k in storey_mark_his
        out[k] = "BOTH" if a and b else ("ENGINE_ONLY" if a else "HIS_ONLY")
    return out


# ------------------------------------------------------------------------------------------------ Alsenan inputs
def _load():
    L = json.load(open(ROOT / INDEX))
    fx = {}
    for f in FIXES:
        for r in json.load(open(ROOT / f))["rows"]:
            if r["item_code"] == ITEM:
                fx[r["line_id"]] = (f.split("/")[1].replace("agents_", "").upper(), r)
    led = list(csv.DictReader(open(ROOT / LEDGER)))
    raw = json.load(open(ROOT / RAW, encoding="utf-8"))
    return L, fx, led, raw


def freelancer(raw):
    cells = {int(x["row"]): x["cells"] for x in raw["rows"] if x.get("sheet") == "كمرات"}
    v = lambda r, c: cells[r][c + str(r)]["v"]  # noqa: E731
    rows, storey = [], None
    for r in sorted(cells):
        storey = {10: "GF", 56: "1F", 83: "2F"}.get(r, storey)
        c = cells[r]
        if ("I%d" % r) in c and ("B%d" % r) in c and isinstance(c["B%d" % r]["v"], (int, float)):
            # his columns: B width, C depth, D length (header text says B width / C length / D height; values and
            # formulas E = B x C x D show C is the depth: 0.40 / 0.50 / 0.75 / 1.20 are the schedule depths)
            n = (c.get("F%d" % r) or {}).get("v")
            rows.append(dict(row=r, storey=storey, mark=(c.get("A%d" % r) or {}).get("v"), b=c["B%d" % r]["v"],
                             d=c["C%d" % r]["v"], L=c["D%d" % r]["v"], n=n if isinstance(n, (int, float)) and n > 1 else 1,
                             m3=c["I%d" % r]["v"]))
    return dict(total=v(100, "I"), gf=v(54, "I"), f1=v(82, "I"), f1_page=v(79, "I"), f2=v(96, "I"), rows=rows)


def resolve_run(line, by_member, by_piece, by_run=None):
    e = line["element_id"]
    m = re.search(r"BEAM_LEDGER:(?:GF|1F|2F):(BM-[^#\s]+#[A-Z0-9.\-]+?)(?:\.r\d+)?$", e)
    if by_run and m and m.group(1) in by_run:
        return by_run[m.group(1)]
    if "DOME-1F-W" in e:
        return by_member["BM-1F-028"]          # the 1F west dome ring = one B4 run (Q-44 A, T-160)
    if "GF:BAND0030.2" in e:
        return by_member["BM-GF-062"]          # T-642: face GF-112 north of column 353 = T-241 BM-GF-062
    if "DOME-1F-E" in e:
        return by_member["BM-1F-039"]
    m = re.search(r"(BM-(?:GF|1F|2F)-\d+(?:\.\d+)?)", e)
    if m and m.group(1) in by_member:
        return by_member[m.group(1)]
    m = re.search(r"BEAMS:(GF|1F|2F):(BAND\d+)(\.\d+)?", e)
    if m:
        k = f"{m.group(1)}:{m.group(2)}{m.group(3) or ''}"
        for c in (k, k + ".1", f"{m.group(1)}:{m.group(2)}"):
            if c in by_piece:
                return by_piece[c]
    raise KeyError(f"{line['line_id']} {e}: no run in the T-241 ledger")


def engine_lines(L, fx, led):
    by_member = {r["member"]: r for r in led}
    by_run = {r["run"]: r for r in led}
    by_piece = {}
    for r in led:
        for p in re.split(r"[;|+ ]+", r["pieces"]):
            if p and ":" in p:
                by_piece.setdefault(p, r)
    out = []
    for l in L["lines"]:
        if l["item_code"] != ITEM or l["class"] == "EXCLUDED":
            continue
        src, r = fx.get(l["line_id"], (None, None))
        if r:
            a = r["after"]
            if "net" not in a:
                raise ValueError(f"{l['line_id']}: fix row leaves the line HELD")
            v, label = a["net"], r["label"]
        elif l["class"] == "RELEASED":
            v, label, src = l["measured_net"], "MEASURED", "INDEX"
        else:
            raise ValueError(f"{l['line_id']}: HELD with no fix row (never 0)")
        run = resolve_run(l, by_member, by_piece, by_run)
        out.append(dict(line_id=l["line_id"], element_id=l["element_id"], m3=v, label=label, src=src, run=run["run"],
                        storey=run["storey"], mark=run["mark"], status=run["status"], member=run["member"],
                        designer=run.get("designer", ""), b=run.get("b_drawn_m"), d=run.get("depth_m"),
                        L=run.get("length_m")))
    return out


def engine_key(x):
    m = x["mark"]
    if x["status"] == "HELD" and (m.startswith("(") or m.startswith("CB3 and")):
        return (x["storey"], "(unlabelled / held piece)")
    if m.startswith("("):
        return (x["storey"], "(unlabelled / held piece)")
    return (x["storey"], norm_mark(m))


# ------------------------------------------------------------------------------------------------ build
def build():
    L, fx, led, raw = _load()
    eng = engine_lines(L, fx, led)
    fr = freelancer(raw)
    his_sum, his_by = his_rows_resum(fr["rows"])
    e_by = defaultdict(list)
    for x in eng:
        e_by[engine_key(x)].append(x)
    cls = classify(e_by, his_by)
    led_by = defaultdict(list)
    for r in led:
        if r["status"] in ("CALCULATED", "CONFLICT") and not r["mark"].startswith("("):
            led_by[(r["storey"], norm_mark(r["mark"]))].append(r)

    rows = []
    for k in sorted(cls, key=lambda k: ({"GF": 0, "1F": 1, "2F": 2}[k[0]], k[1])):
        es, hs = e_by.get(k, []), his_by.get(k, [])
        e_m3, h_m3 = sum(x["m3"] for x in es), sum(x["m3"] for x in hs)
        # dimensions: engine = the ledger runs of this mark (b drawn, D printed, L between support faces)
        lr = led_by.get(k, [])
        eL = sum(float(r["length_m"] or 0) for r in lr)
        e_bd = {(r["b_drawn_m"], r["depth_m"]) for r in lr}
        hL = sum(x["L"] * x["n"] for x in hs)
        h_bd = {(x["b"], x["d"]) for x in hs}
        rows.append(dict(storey=k[0], mark=k[1], cls=cls[k], engine_lines=len(es), engine_m3=round(e_m3, 4),
                         engine_labels=sorted({x["label"] for x in es}), his_rows=len(hs), his_m3=round(h_m3, 4),
                         diff_m3=round(e_m3 - h_m3, 4), engine_L=round(eL, 3), his_L=round(hL, 3),
                         engine_b_d=sorted(e_bd), his_b_d=sorted(h_bd)))

    # ---- named causes (engine - freelancer), each a sum over the per-mark rows; residual is what no cause explains
    causes = defaultdict(float)
    detail = defaultdict(list)
    for r in rows:
        k = (r["storey"], r["mark"])
        if r["cls"] == "ENGINE_ONLY" and r["mark"].startswith("("):
            # split the unlabelled pieces by the label of their figure
            for x in e_by[k]:
                key = ("C4_UNLABELLED_PIECES_DEFAULT_DEPTH" if x["label"] == "DEFAULT" else
                       "C4b_UNLABELLED_PIECES_DRAWING_READ" if x["label"] in ("DRAWING-READ", "MEASURED") else
                       "C4c_UNLABELLED_PIECES_OTHER")
                causes[key] += x["m3"]
                detail[key].append(f"{x['storey']} {x['member']} {x['designer']} {x['m3']:.4f} {x['label']}")
            continue
        if r["cls"] == "ENGINE_ONLY":
            causes["C1_MARKS_DRAWN_NOT_IN_HIS_SHEET"] += r["engine_m3"]
            detail["C1_MARKS_DRAWN_NOT_IN_HIS_SHEET"].append(f"{r['storey']} {r['mark']} {r['engine_m3']:.4f}")
            continue
        if r["cls"] == "HIS_ONLY":
            causes["C5_HIS_ONLY_MARKS"] -= r["his_m3"]
            detail["C5_HIS_ONLY_MARKS"].append(f"{r['storey']} {r['mark']} -{r['his_m3']:.4f}")
            continue
        # BOTH: exact split per mark on aggregate dimensions; the engine's own figure differs from b x D x L of the
        # ledger where a run carries end strips / joint deductions (T-229): that part is its own cause (C2d)
        lr = led_by.get(k, [])
        hs = his_by[k]
        em = defaultdict(float)
        for x in e_by[k]:
            em[x["run"]] += x["m3"]
        dims = [run_dims(x, em.get(x["run"])) for x in lr]
        db = dd = dl = 0.0
        # per-run pairing is not printed on his sheet: split on the mark as a whole with length-weighted b and D
        if dims and all(None not in t for t in dims):
            Lo = sum(t[2] for t in dims)
            bo = sum(t[0] * t[2] for t in dims) / Lo
            do = sum(t[1] * t[0] * t[2] for t in dims) / (bo * Lo)
            Lh = sum(x["L"] * x["n"] for x in hs)
            bh = sum(x["b"] * x["L"] * x["n"] for x in hs) / Lh
            dh = sum(x["d"] * x["b"] * x["L"] * x["n"] for x in hs) / (bh * Lh)
            db, dd, dl = split_effects(bo, do, Lo, bh, dh, Lh)
            db, dd, dl = -db, -dd, -dl          # sign: engine - his
            other = r["diff_m3"] - (db + dd + dl)
        else:
            other = r["diff_m3"]
            detail["C2d_ENDS_JOINTS_AND_POINTS"].append(f"{r['storey']} {r['mark']} no dims")
        causes["C2a_WIDTH"] += db
        causes["C2b_DEPTH"] += dd
        lname = "C2c1_LENGTH_ENGINE_LONGER" if dl > 0 else "C2c2_LENGTH_HIS_LONGER"
        causes[lname] += dl
        causes["C2d_ENDS_JOINTS_AND_POINTS"] += other
        for nm, v in (("C2a_WIDTH", db), ("C2b_DEPTH", dd), (lname, dl), ("C2d_ENDS_JOINTS_AND_POINTS", other)):
            if abs(v) >= 0.02:
                detail[nm].append(f"{r['storey']} {r['mark']} {v:+.4f}")

    e_total = round(sum(x["m3"] for x in eng), 4)
    slip = round(his_sum - fr["total"], 4)
    causes["C3_HIS_SHEET_ARITHMETIC"] = slip   # engine - his total includes + (his rows - his total)
    explained = sum(causes.values())
    diff = round(e_total - fr["total"], 4)
    resid = round(diff - explained, 6)
    return dict(
        schema="T777_BEAM_CAUSES_V1", candidate=INDEX, fixes=list(FIXES), ledger=LEDGER,
        engine_m3=e_total, engine_lines=len(eng),
        engine_by_label={lb: round(sum(x["m3"] for x in eng if x["label"] == lb), 4)
                         for lb in sorted({x["label"] for x in eng})},
        engine_by_storey={s: round(sum(x["m3"] for x in eng if x["storey"] == s), 4) for s in ("GF", "1F", "2F")},
        freelancer_total_cell=fr["total"], freelancer_rows_sum=his_sum,
        freelancer_by_storey=dict(GF=fr["gf"], F1=fr["f1"], F1_page=fr["f1_page"], F2=fr["f2"]),
        diff_m3=diff, diff_pct=round(100 * diff / fr["total"], 2),
        causes={k: round(v, 4) for k, v in sorted(causes.items())}, residual_m3=resid,
        residual_pct_of_line=round(100 * abs(resid) / fr["total"], 4),
        verdicts={k: VERDICTS.get(k, ("UNRESOLVED", "unnamed"))[0] for k in causes},
        detail={k: v for k, v in sorted(detail.items())}, per_mark=rows, lines=eng)


# ------------------------------------------------------------------------------------------------ self-test (synthetic)
def selftest():
    # normal: width / depth / length effects sum exactly to the difference
    db, dd, dl = split_effects(0.20, 0.50, 4.00, 0.25, 0.60, 4.40)
    assert abs((db + dd + dl) - (0.25 * 0.60 * 4.40 - 0.20 * 0.50 * 4.00)) < 1e-12
    assert abs(db - 0.05 * 0.5 * 4.0) < 1e-12 and abs(dl - 0.25 * 0.6 * 0.4) < 1e-12
    # mirror / rotation do not enter (scalar dims); unit trap: mm entered as m is not silently accepted by the totals
    db2, dd2, dl2 = split_effects(200, 500, 4000, 250, 600, 4400)
    assert abs((db2 + dd2 + dl2) / 1e9 - (db + dd + dl)) < 1e-9
    # adverse: a missing dimension is refused, never 0
    for bad in ((None, 0.5, 4, 0.2, 0.5, 4), (0.2, -0.5, 4, 0.2, 0.5, 4)):
        try:
            split_effects(*bad)
        except ValueError:
            pass
        else:
            raise AssertionError("missing / negative dimension accepted")
    # marks: storey prefixes on chain beams, upstand suffix
    assert norm_mark("BCB5") == "CB5" and norm_mark("GCB12") == "CB12" and norm_mark("B20 upstand") == "B20 upstand"
    assert run_dims(dict(b_drawn_m="", depth_m="0.75", length_m="6.7412", reason="schedule width 0.25 vs drawn 0.2: x"),
                    1.0) == (0.2, 0.75, 6.7412)
    # his blank-mark continuation rows belong to the mark above
    s, by = his_rows_resum([dict(storey="GF", mark="B1", m3=0.3), dict(storey="GF", mark=None, m3=0.2),
                            dict(storey="1F", mark="B1", m3=0.1)])
    assert abs(s - 0.6) < 1e-12 and len(by[("GF", "B1")]) == 2 and len(by[("1F", "B1")]) == 1
    # adverse: an unlabelled engine piece is never paired with a neighbour mark of his
    c = classify({("GF", "(unlabelled / held piece)"): 1, ("GF", "B24"): 1}, {("GF", "B24"): 1})
    assert c[("GF", "(unlabelled / held piece)")] == "ENGINE_ONLY" and c[("GF", "B24")] == "BOTH"
    return True


VERDICTS = {
    "C1_MARKS_DRAWN_NOT_IN_HIS_SHEET": ("ENGINE_RIGHT", "8 labelled items on the slab plans absent from his sheet (no 'B27 / B25 / B19' text in his 17 sheets, T-241): GF B27 0.90 x 0.85 x 4.9505 = 3.787 + 0.405 continuous under the carried P.C (T-229) = 4.192; 1F B25 0.55 x 0.75 x 6.875 = 2.836; B20 / B23 upstands 0.20 x 0.20 x 3.00 = 0.120 each (sections A-A / B-B)"),
    "C2c1_LENGTH_ENGINE_LONGER": ("ENGINE_RIGHT", "runs of a mark he lists short: 1F B6 5 runs 21.41 m vs his one row 4.37 m; 1F B4 incl. the west dome ring (Q-44 A) 12.21 m vs 8.90 m; GF B1 16.76 vs 14.15 m"),
    "C2c2_LENGTH_HIS_LONGER": ("RULE_DIFFERENCE", "joint ownership: his columns stop under the beams (GF column height 3.75 = 4.50 - 0.75) so his beams run through the supports; the candidate's columns run the full storey and its beams stop at the support faces (C1, R-CONC-OWN-1). The joint volume moves between the beam and column lines; compare beams + columns together. Inside it: his B24 5.75 m and 2F B15 6.80 m fold the unlabelled cantilever / adjacent piece the candidate carries as its own lines (C4 / C4b)"),
    "C2a_WIDTH": ("UNRESOLVED", "D-27 / D-02: drawn width (T-757 point, geometry first, Q-61) vs his schedule width on B21 / B29 / CB2 / 1F B6 / CB10"),
    "C2b_DEPTH": ("AGREE", "every paired mark has the same printed depth on both sides"),
    "C2d_ENDS_JOINTS_AND_POINTS": ("ENGINE_RIGHT", "T-229 end strips beside narrower supports and the 7 column-joint deductions (measured), not in a b x D x L of the run"),
    "C3_HIS_SHEET_ARITHMETIC": ("ENGINE_RIGHT", "his 1F total I82 = SUM(I60:I78) drops row 59 (B1 0.20 x 0.40 x 1.60 = 0.128) that his page sum I79 carries"),
    "C4_UNLABELLED_PIECES_DEFAULT_DEPTH": ("UNRESOLVED", "no mark, no section, no schedule row: not replaceable by a schedule reading. Projection strips D-05 / D-26 4.36 m3 at the 0.60 company default (on the slab sheets the strips carry the 'cantilever portion' / 'bearing wall (B.W)' 45-degree hatch, which the legend does not separate; read as cantilever slab at 0.16 they give 1.16, -3.20 m3); D-04 adjacent-span depths 1.20; D-03 'CB3 and B3 (With Stair)' 0.40; D-28 east dome ring at the twin ring depth 0.90"),
    "C4b_UNLABELLED_PIECES_DRAWING_READ": ("UNRESOLVED", "GF B24 cantilever piece (D-04) 0.55 and face GF-112 0.05: drawn, no mark; his B24 length carries the cantilever"),
    "C5_HIS_ONLY_MARKS": ("NONE", "no mark of his is missing from the drawing ledger"),
}


def write_md(d):
    o = [f"# T-777 STR.CONC.BEAM: candidate vs freelancer by named cause (Alsenan; every villa)", "",
         f"Candidate {d['candidate']} + T-761 / T-757 fix rows: **{d['engine_m3']:.2f} m3** ({d['engine_lines']} lines; "
         + ", ".join(f"{k} {v:.2f}" for k, v in d["engine_by_label"].items()) + "). Freelancer total cell "
         f"**{d['freelancer_total_cell']:.2f} m3** (his rows re-added {d['freelancer_rows_sum']:.3f}). Difference "
         f"**{d['diff_m3']:+.2f} m3 ({d['diff_pct']:+.1f} %)**; residual after the named causes "
         f"**{d['residual_m3']:+.4f} m3** ({d['residual_pct_of_line']:.3f} % of the line).", "",
         "Convention both sides: C1 (beam b x D x L at full printed depth, slab panel stops at the beam face): his "
         "rows are W x D x L with schedule depths, his slab is area x 0.16; no slab thickness is deducted on either side.", "",
         "| cause | m3 (engine - freelancer) |", "|---|---|"]
    for k, v in d["causes"].items():
        o.append(f"| {k} | {v:+.4f} |")
    o += [f"| residual | {d['residual_m3']:+.6f} |", "", "## Verdict proposals per cause", "",
          "| cause | m3 | verdict | reason |", "|---|---|---|---|"]
    for k, v in d["causes"].items():
        vd, why = VERDICTS.get(k, ("UNRESOLVED", "unnamed"))
        o.append(f"| {k} | {v:+.4f} | {vd} | {why} |")
    o += ["", "## Detail per cause", ""]
    for k, v in d["detail"].items():
        o.append(f"- **{k}**: " + "; ".join(v))
    o += ["", "## Per storey and mark", "",
          "| storey | mark | class | engine m3 | labels | his m3 | engine - his | engine L | his L | engine b,D | his b,D |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in d["per_mark"]:
        o.append(f"| {r['storey']} | {r['mark']} | {r['cls']} | {r['engine_m3']:.4f} | {'/'.join(r['engine_labels'])} | "
                 f"{r['his_m3']:.4f} | {r['diff_m3']:+.4f} | {r['engine_L']:.3f} | {r['his_L']:.3f} | "
                 f"{r['engine_b_d']} | {r['his_b_d']} |")
    return "\n".join(o) + "\n"


def main(argv):
    selftest()
    d = build()
    js = json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    md = write_md(d)
    if "--check" in argv:
        ok = (OUT / "BEAM_CAUSES.json").read_text(encoding="utf-8") == js and \
             (OUT / "BEAM_CAUSES.md").read_text(encoding="utf-8") == md
        print("T777 check", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    OUT.mkdir(exist_ok=True)
    (OUT / "BEAM_CAUSES.json").write_text(js, encoding="utf-8")
    (OUT / "BEAM_CAUSES.md").write_text(md, encoding="utf-8")
    print(json.dumps({k: d[k] for k in ("engine_m3", "freelancer_total_cell", "diff_m3", "diff_pct", "causes",
                                        "residual_m3", "engine_by_storey", "freelancer_by_storey")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
