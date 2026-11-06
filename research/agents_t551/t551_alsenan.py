"""T-551 development-villa run (research, unwired): B10 column / neck / footing (+ straps + boundary band) / lift wall
and blinding concrete on the candidate of record V3.0.58 against the freelancer's sheets, by component
(R-T551-1 .. 4, on top of R-T394-1 .. 6, T-233, T-478 and R-T545-1 .. 3).

    called by tests/t551_column_footing_reconcile (rebuild check) with the private workbook path:
    build('.work/private/concrete_rebar.xlsx') -> (doc, private_rows)

Engine lines: research/agents_t507/out/LINE_INDEX_V3_0_57.json (V3.0.58 changes FIN.WP.ROOF / ROOF_UPTURN only,
R-T507-1 (e)). Member data of the GF / 1F column lines (mark, A, height, datums, D_ctrl): the merged T-394 per-line
record research/agents_t394/summary_t394.json, joined by line id. Freelancer: Drive "Alsenan chalet project", the
concrete + rebar workbook, sheets 'footings' and 'walls + columns' (read with openpyxl, values AND formulas,
R-T541-1); his rows stay in .work/private/t551. Tracked output: out/T551_COLUMN_FOOTING_RECONCILE.json (engine figures
and component terms in m3, his per-family / per-storey sums; no row, dimension or count of his).
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t551_rules as R  # noqa: E402

LINE_INDEX = RES / "agents_t507" / "out" / "LINE_INDEX_V3_0_57.json"
T394 = RES / "agents_t394" / "summary_t394.json"
T545 = RES / "agents_t545" / "out" / "T545_BEAM_RECONCILE.json"
OUT = HERE / "out" / "T551_COLUMN_FOOTING_RECONCILE.json"
STOREY_BASE = {"GF": Decimal("0.95"), "1F": Decimal("5.45")}      # T-214 / T-394 datums (structural tops)
FOOTING_SHEET, COLUMN_SHEET = "القواعد", "الحوائط + الأعمدة"
# his section headers on the walls + columns sheet -> family / storey
SECTIONS = (("رقاب", "NECK"), ("الأرضي", "GF"), ("الأول", "1F"), ("السطح", "2F"), ("السرداب", "LIFT"))
# footing-sheet labels -> engine marks (his 'F.F' = lift raft FF, 'F.N' = FN, STB = strap SB, perimeter tie = band)
FTG_LABEL = {"F.F": "FF", "F.N": "FN", "STB1": "SB1", "STB2": "SB2", "STB3": "SB3", "الشناج المحيط": "BAND",
             "العاديه": "PLATE"}
# the per-piece remainder of a mark carries a cause read on the drawing (T-233 s.2; T-231 strap lengths)
FTG_CAUSE = {"FN": "OVERLAP", "SB2": "LENGTH", "SB3": "LENGTH"}
FTG_CAUSE_TEXT = {
    "FN": "FN 180C drawn notched 0.40 x 0.35 where F9 (0.55 deep) lies: F9 owns the intersection (R-CONC-OWN-1); "
          "his four FN rows bill it again (T-233)",
    "SB2": "drawn 1.00 x 2.2927 x 0.50 (T-231) against his rounded length",
    "SB3": "drawn 0.50 x 3.2580 x 0.40 (T-231, VERIFIED) against his rounded length"}
# T-233: outline 1B1B carries F10 + F (one rectangle, two tags); held on Q-31 C
F10_ELEMENT = "P-C:FTG:SH10:T652:10A5"
# the 2F planted column: its line note reads text 77C 'P.C 20x50' (section CONFLICT with the drawn 0.20 x 0.40)
PLANTED_MARK = {"HL:PLANTED_COLUMN:PC-2F:CONCRETE": "P.C 20x50"}


def d6(x):
    return R.d6(x)


# ------------------------------------------------------------------------------------------------- engine side
def index_lines():
    d = json.loads(LINE_INDEX.read_text(encoding="utf-8"))
    assert d["candidate_version"] == "ARCH_TAKEOFF_V3.0.57"
    return d["lines"]


def _fam(code):
    return [x for x in index_lines() if x["item_code"] == code]


def column_lines():
    """Every STR.CONC.COLUMN line with storey, mark and (valued) member data; T-394 records joined by line id."""
    rec = {r["line_id"]: r for r in json.loads(T394.read_text(encoding="utf-8"))["per_line_engine"]}
    out = []
    for x in _fam("STR.CONC.COLUMN"):
        e = x["element_id"]
        r = rec.get(x["line_id"])
        m = re.search(r"\|(GF|1F|2F)$", e)
        storey = r["storey"] if r else (m.group(1) if m else ("2F" if "PC-2F" in e else "UNKNOWN"))
        if r and r["mark"]:
            mark = r["mark"]
        elif e in PLANTED_MARK:
            mark = PLANTED_MARK[e]
        else:
            mm = re.search(r":(C\w*|CN)@", e)
            mark = mm.group(1) if mm else e
        ln = {"line_id": x["line_id"], "element_id": e, "storey": storey, "mark": mark, "class": x["class"],
              "m3": x["measured_net"], "low": x["held_low"], "high": x["held_high"]}
        if x["class"] == "RELEASED":
            assert r is not None and r["state"] == "VALUED", e
            assert d6(r["engine_m3"]) == d6(x["measured_net"]), (e, r["engine_m3"], x["measured_net"])
            h = Decimal(str(r["engine_h"]))
            ln.update({"A": Decimal(str(r["engine_m3"])) / h, "h": h, "base": r["base"], "d_ctrl": r["d_ctrl"],
                       "member": r["member"]})
        out.append(ln)
    return out


# ------------------------------------------------------------------------------------------------- his side
def his_rows(path):
    """His footing and column / neck / lift rows (label, b, c, h, n, unit m3, row m3) with a formula check."""
    import openpyxl
    wv = openpyxl.load_workbook(path, data_only=True)
    wf = openpyxl.load_workbook(path, data_only=False)
    rows = {"FOOTING": [], "NECK": [], "GF": [], "1F": [], "2F": [], "LIFT": []}
    sub = {}

    def num(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool)

    for sheet in (FOOTING_SHEET, COLUMN_SHEET):
        ws, wsf = wv[sheet], wf[sheet]
        fam = "FOOTING" if sheet == FOOTING_SHEET else None
        for r in range(1, ws.max_row + 1):
            a = ws.cell(r, 1).value
            if sheet == COLUMN_SHEET and isinstance(a, str):
                for key, f in SECTIONS:
                    if key in a:
                        fam = f
            b, c, h, n, tot = (ws.cell(r, k).value for k in (2, 3, 4, 6, 9))
            if fam and isinstance(a, str) and all(num(v) for v in (b, c, h, n)) and num(tot):
                unit = Decimal(str(b)) * Decimal(str(c)) * Decimal(str(h))
                row_m3 = d6(unit * Decimal(str(n)))
                if abs(row_m3 - d6(tot)) > Decimal("0.000002"):
                    raise R.Refused(f"{sheet} row {r}: b x c x h x n {row_m3} != his cell {tot}")
                rows[fam].append({"label": a.strip(), "b": str(b), "c": str(c), "h": str(h), "n": int(n),
                                  "unit_m3": str(d6(unit)), "row_m3": str(row_m3), "row": r,
                                  "formula": str(wsf.cell(r, 9).value)})
            if isinstance(a, str) and a.strip() in ("إجمالي", "Total") and num(ws.cell(r, 9).value):
                sub[(sheet, fam, r)] = d6(ws.cell(r, 9).value)
    return rows, sub


# ------------------------------------------------------------------------------------------------- columns
def columns_by_storey(cols, his):
    """R-T551-1 per storey (GF, 1F, 2F) and mark; the storey-less CN lines kept as their own group."""
    out, detail, held_rows = {}, [], []
    for st in ("GF", "1F", "2F"):
        hm = defaultdict(list)
        for r in his[st]:
            lab = r["label"]
            if lab.startswith("PC"):                       # his planted columns: matched by the printed section label
                lab = "P.C %dx%d" % (round(float(r["b"]) * 100), round(float(r["c"]) * 100))
            hm[lab].append(r)
        lines = [c for c in cols if c["storey"] == st and c["class"] != "EXCLUDED"]
        marks = sorted({c["mark"] for c in lines} | set(hm))
        comp = defaultdict(Decimal)
        E = F = Decimal(0)
        for mk in marks:
            hr = hm.get(mk, [])
            assert len({(r["b"], r["c"], r["h"]) for r in hr}) <= 1, (st, mk)
            n_h = sum(r["n"] for r in hr)
            v = [{"A": c["A"], "h": c["h"], "base": c["base"], "d_ctrl": c["d_ctrl"], "m3": c["m3"]}
                 for c in lines if c["mark"] == mk and c["class"] == "RELEASED"]
            held = [c for c in lines if c["mark"] == mk and c["class"] == "HELD"]
            k, e, f = R.column_mark_split(his_n=n_h, his_b=hr[0]["b"] if hr else None,
                                          his_c=hr[0]["c"] if hr else None, his_h=hr[0]["h"] if hr else None,
                                          valued=v, held_n=len(held),
                                          storey_base=STOREY_BASE.get(st, Decimal(0)))
            E, F = E + e, F + f
            for n_, x in k.items():
                comp[n_] += x
            row = {"storey": st, "mark": mk, "engine_m3": str(e)}
            row.update({n_: str(x) for n_, x in k.items() if x})
            detail.append(row)
            share = None if not hr else d6(Decimal(hr[0]["b"]) * Decimal(hr[0]["c"]) * Decimal(hr[0]["h"]))
            for i, c in enumerate(held):
                # a held line beyond his count of the mark has no row of his (count binding, not by position)
                has_row = hr and (len(v) + i) < n_h
                cls = R.held_bound_class(share, c["low"], c["high"]) if has_row else (
                    "NO_ROW_OF_HIS" if c["low"] is not None else "NO_ROW_OF_HIS, UNBOUNDED")
                held_rows.append({"line_id": c["line_id"], "storey": st, "mark": mk,
                                  "engine_low_m3": None if c["low"] is None else str(d6(c["low"])),
                                  "engine_high_m3": None if c["high"] is None else str(d6(c["high"])),
                                  "his_share_m3": str(share) if has_row else None, "class": cls})
        held_share = -comp["HELD"]
        out[st] = R.component_table(E, F, dict(comp), held_his_share=held_share)
    rest = [c for c in cols if c["storey"] == "UNKNOWN"]
    for c in rest:
        held_rows.append({"line_id": c["line_id"], "storey": "UNKNOWN", "mark": c["mark"],
                          "engine_low_m3": None if c["low"] is None else str(d6(c["low"])),
                          "engine_high_m3": None if c["high"] is None else str(d6(c["high"])),
                          "his_share_m3": None,
                          "class": "NO_ROW_OF_HIS" if c["low"] is not None else "NO_ROW_OF_HIS, UNBOUNDED"})
    return out, detail, held_rows


# ------------------------------------------------------------------------------------------------- necks / lift
def necks(his):
    lines = _fam("STR.CONC.NECK")
    assert all(x["class"] == "HELD" for x in lines)
    hm = defaultdict(list)
    for r in his["NECK"]:
        hm[r["label"]].append(r)
    by = defaultdict(list)
    for x in lines:
        by[re.search(r":(C\w*|CN)@", x["element_id"]).group(1)].append(x)
    held_rows, F = [], Decimal(0)
    count_diff = {}
    for mk in sorted(set(by) | set(hm)):
        hr = hm.get(mk, [])
        n_h = sum(r["n"] for r in hr)
        share = d6(Decimal(hr[0]["unit_m3"])) if hr else None
        F += sum((Decimal(r["row_m3"]) for r in hr), Decimal(0))
        if len(by[mk]) != n_h:
            count_diff[mk] = len(by[mk]) - n_h
        for i, x in enumerate(sorted(by[mk], key=lambda y: y["element_id"])):
            has = i < n_h
            held_rows.append({"line_id": x["line_id"], "mark": mk,
                              "engine_low_m3": None if x["held_low"] is None else str(d6(x["held_low"])),
                              "engine_high_m3": None if x["held_high"] is None else str(d6(x["held_high"])),
                              "his_share_m3": str(share) if has else None,
                              "class": R.held_bound_class(share, x["held_low"], x["held_high"]) if has else (
                                  "NO_ROW_OF_HIS" if x["held_low"] is not None else "NO_ROW_OF_HIS, UNBOUNDED")})
    his_carried = sum((Decimal(h["his_share_m3"]) for h in held_rows if h["his_share_m3"]), Decimal(0))
    assert his_carried == d6(F), (his_carried, F)
    tbl = R.component_table(0, F, {"HELD": -F}, held_his_share=F)
    lo = sum((Decimal(h["engine_low_m3"]) for h in held_rows if h["engine_low_m3"]), Decimal(0))
    hi = sum((Decimal(h["engine_high_m3"]) for h in held_rows if h["engine_high_m3"]), Decimal(0))
    tbl["engine_held_bound_m3"] = [str(lo), str(hi)]
    tbl["engine_held_lines"] = len(lines)
    tbl["engine_minus_his_count_by_mark"] = count_diff        # counts of the ENGINE side only are drawing facts
    return tbl, held_rows


def lift_walls(his):
    """R-T394-6 on V3.0.58: his ring = the gross 2.20^2 - 1.80^2 = 1.60 m2 through the four lift column pieces
    (0.50 m2, owned by the lift neck lines and in his neck rows too); net ring 1.10 m2 = the HELD LIFT_PIT:WALLS line."""
    pit = [x for x in index_lines() if x["element_id"] == "LIFT_PIT:WALLS"]
    assert len(pit) == 1 and pit[0]["class"] == "HELD" and pit[0]["held_low"] is None
    r = his["LIFT"]
    assert len(r) == 1
    b, c, h = (Decimal(r[0][k]) for k in ("b", "c", "h"))
    plan = b * c                                   # his row: perimeter x wall thickness
    gross, net, cols = Decimal("1.60"), Decimal("1.10"), Decimal("0.50")
    if plan != gross:
        raise R.Refused("his lift wall plan is not the gross ring: R-T394-6 does not apply")
    F = d6(Decimal(r[0]["row_m3"]))
    comp = {"SCOPE_DOUBLE": -cols * h * r[0]["n"], "HELD": -net * h * r[0]["n"]}
    tbl = R.component_table(0, F, comp, held_his_share=net * h)
    tbl["engine_line"] = {"line_id": pit[0]["line_id"], "class": "HELD", "bound": None}
    return tbl


# ------------------------------------------------------------------------------------------------- footing line
def footing_line(his):
    eng = defaultdict(lambda: {"valued": [], "held": []})
    for code in ("STR.CONC.FOOTING", "STR.CONC.STRAP", "STR.CONC.BOUNDARY_WALL"):
        for x in _fam(code):
            e = x["element_id"]
            if x["class"] == "EXCLUDED":
                continue
            if e == F10_ELEMENT:
                mk = "F10"
            elif code == "STR.CONC.FOOTING":
                mk = re.search(r":(F\w*)@", e).group(1)
            elif code == "STR.CONC.STRAP":
                mk = re.search(r":(SB\d)", e).group(1)
                if ":IN_FOOTING:" in e:                    # strap piece inside a footing outline (T-230 / T-233)
                    mk += " in footing"
            else:
                mk = "BAND"
            eng[mk]["valued" if x["class"] == "RELEASED" else "held"].append(x)
    hm = defaultdict(list)
    for r in his["FOOTING"]:
        hm[FTG_LABEL.get(r["label"], r["label"])].append(r)
    plate = hm.pop("PLATE")
    comp = defaultdict(Decimal)
    detail, held_rows = [], []
    E = F = Decimal(0)
    for mk in sorted(set(eng) | set(hm)):
        hr = hm.get(mk, [])
        assert len({r["unit_m3"] for r in hr}) <= 1, mk
        n_h = sum(r["n"] for r in hr)
        vals = [x["measured_net"] for x in eng[mk]["valued"]]
        k, e, f = R.footing_mark_split(his_n=n_h, his_unit_m3=hr[0]["unit_m3"] if hr else None, valued_m3=vals,
                                       held_n=len(eng[mk]["held"]), cause=FTG_CAUSE.get(mk))
        E, F = E + e, F + f
        for n_, x in k.items():
            comp[n_] += x
        row = {"mark": mk, "engine_m3": str(e)}
        row.update({n_: str(x) for n_, x in k.items() if x})
        if mk in FTG_CAUSE_TEXT and any(k[c] for c in ("OVERLAP", "LENGTH")):
            row["cause"] = FTG_CAUSE_TEXT[mk]
        detail.append(row)
        for i, x in enumerate(eng[mk]["held"]):
            has = hr and (len(vals) + i) < n_h
            share = d6(hr[0]["unit_m3"]) if has else None
            held_rows.append({"line_id": x["line_id"], "mark": mk,
                              "engine_low_m3": None if x["held_low"] is None else str(d6(x["held_low"])),
                              "engine_high_m3": None if x["held_high"] is None else str(d6(x["held_high"])),
                              "his_share_m3": None if share is None else str(share),
                              "class": R.held_bound_class(share, x["held_low"], x["held_high"]) if has else (
                                  "NO_ROW_OF_HIS" if x["held_low"] is not None else "NO_ROW_OF_HIS, UNBOUNDED")})
    tbl = R.component_table(E, F, dict(comp), held_his_share=-comp["HELD"])
    return tbl, detail, held_rows, plate


# ------------------------------------------------------------------------------------------------- blinding
def blinding(plate):
    """Restates the T-478 plate split on V3.0.58 (lines unchanged since V3.0.45, asserted): closes at both held ends."""
    L = _fam("STR.CONC.BLINDING")
    rel = [x for x in L if x["class"] == "RELEASED"]
    assert len(rel) == 1 and d6(rel[0]["measured_net"]) == Decimal("12.734438")
    lo = sum((d6(x["held_low"]) for x in L if x["held_low"] is not None), Decimal(0))
    hi = sum((d6(x["held_high"]) for x in L if x["held_high"] is not None), Decimal(0))
    assert (lo, hi) == (Decimal("7.640374"), Decimal("13.466198")), (lo, hi)
    assert len(plate) == 1
    F = d6(plate[0]["row_m3"])
    E = d6(rel[0]["measured_net"])
    # T-478 s.4: pieces inside his rectangle (FF raft, F10 + F inside the plot, ground beams plan-distinct, straps)
    held_in_plate = {"FF raft": ("2.256", "2.352"), "F10 + F inside the plot": ("0.435", "0.560"),
                     "ground beams, plan-distinct of the pit layer": ("4.949374", "5.658835"),
                     "straps": ("0", "0.912684")}
    hl = sum((Decimal(a) for a, _ in held_in_plate.values()), Decimal(0))
    hh = sum((Decimal(b) for _, b in held_in_plate.values()), Decimal(0))
    ends = {}
    for name, h in (("held_low_end", hl), ("held_high_end", hh)):
        ends[name] = R.component_table(E, F, {"HELD": -h, "RULE_DIFFERENCE": -(F - E - h)}, held_his_share=h)
    return {"engine_released_m3": str(E), "engine_held_bound_m3": [str(lo), str(hi)], "his_m3": str(F),
            "residual_m3": str(E - F), "split_at_both_held_ends": ends,
            "held_in_his_plate_m3": {k: list(v) for k, v in held_in_plate.items()},
            "boundary_wall_base": "pad count not printed: held blank, in the remainder by name (T-478)",
            "guard": "plain concrete: never added to the structural RC families (R-T551-3)"}


# ------------------------------------------------------------------------------------------------- cross-family
def column_beam_pairing(col_tables):
    """The joint + head the column lines own (JOINT_HEAD) against T-545's THROUGH_SUPPORT (his beam lengths through
    the column / carrier footprints), per storey: the two families' convention terms side by side and netted."""
    b = json.loads(T545.read_text(encoding="utf-8"))
    out = {}
    for st in ("GF", "1F", "2F"):
        ts = Decimal(b["floors"][st]["components"].get("THROUGH_SUPPORT", {"m3": "0"})["m3"])
        c = col_tables[st]["components"]
        jh = Decimal(c.get("JOINT_HEAD", {"m3": "0"})["m3"])
        out[st] = {"column_JOINT_HEAD_m3": str(jh), "beam_THROUGH_SUPPORT_m3": str(ts), "net_m3": str(jh + ts)}
    return out


def build(freelancer):
    his, sub = his_rows(freelancer)
    cols = column_lines()
    col_tbl, col_detail, col_held = columns_by_storey(cols, his)
    neck_tbl, neck_held = necks(his)
    lift_tbl = lift_walls(his)
    ftg_tbl, ftg_detail, ftg_held, plate = footing_line(his)
    blind = blinding(plate)
    # his printed sub-totals equal his rows (no BM-ARITH on these sheets)
    his_sum = {"NECK": neck_tbl["his_m3"], "GF": col_tbl["GF"]["his_m3"], "1F": col_tbl["1F"]["his_m3"],
               "2F": col_tbl["2F"]["his_m3"], "LIFT": lift_tbl["his_m3"]}
    printed = {fam: str(v) for (sh, fam, r), v in sub.items() if sh == COLUMN_SHEET}
    printed_ftg = [str(v) for (sh, fam, r), v in sub.items() if sh == FOOTING_SHEET]
    for fam, v in his_sum.items():
        assert printed.get(fam) == v, (fam, printed.get(fam), v)
    E_cols = sum((Decimal(col_tbl[s]["engine_m3"]) for s in ("GF", "1F", "2F")), Decimal(0))
    assert E_cols == sum((d6(x["measured_net"]) for x in _fam("STR.CONC.COLUMN") if x["class"] == "RELEASED"),
                         Decimal(0))
    doc = {
        "schema": "T551_COLUMN_FOOTING_RECONCILE_V1",
        "candidate": "ARCH_TAKEOFF_V3.0.58 (structural lines = V3.0.57 LINE_INDEX, R-T507-1 (e)); NOT RELEASED",
        "families": "B10 STR.CONC.COLUMN / NECK / FOOTING + STRAP + BOUNDARY_WALL (keyed footing line) / LIFT pit "
                    "walls; STR.CONC.BLINDING (plain, separate)",
        "columns": {"by_storey": col_tbl, "marks": col_detail, "held_beside_his": col_held},
        "necks": {"table": neck_tbl, "held_beside_his": neck_held},
        "lift_walls": lift_tbl,
        "footing_line": {"table": ftg_tbl, "marks": ftg_detail, "held_beside_his": ftg_held,
                         "his_printed_total_m3": printed_ftg[-1] if printed_ftg else None},
        "blinding": blind,
        "column_beam_pairing": column_beam_pairing(col_tbl),
        "note": "engine figures and component terms only; his rows / dimensions / counts stay in .work/private/t551",
    }
    return doc, his


def summary(doc):
    """The tracked tables (out/T551_COLUMN_FOOTING_RECONCILE.json without its header keys)."""
    b = doc["blinding"]
    ends = {k: {n: c["m3"] for n, c in b["split_at_both_held_ends"][k]["components"].items()}
            for k in ("held_low_end", "held_high_end")}
    return {
        "columns": doc["columns"]["by_storey"],
        "necks": doc["necks"]["table"],
        "lift_walls": {k: v for k, v in doc["lift_walls"].items() if k != "engine_line"},
        "footing_line": {**doc["footing_line"]["table"],
                         "his_printed_total_m3": doc["footing_line"]["his_printed_total_m3"]},
        "blinding": {k: b[k] for k in ("engine_released_m3", "engine_held_bound_m3", "his_m3", "residual_m3")}
        | ends,
        "column_beam_pairing": doc["column_beam_pairing"],
    }


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--freelancer", required=True)
    a = ap.parse_args(argv)
    doc, _ = build(a.freelancer)
    print(json.dumps(doc, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
