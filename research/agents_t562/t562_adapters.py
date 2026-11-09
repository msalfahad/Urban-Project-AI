"""T-562: reconciled-quantities statement adapters V3 for the merged T-551 (B10 columns / necks / lift pit walls /
footing line / blinding, m3), T-553 (B3 floor tile, m2), the T-559 restatement of the B9 blockwork leftover (m2) and the
T-556 supersession of the B5 dry-plaster restatement (m2) (research, unwired; computes no new quantity; reads committed
research outputs and the V3.0.57 line index only; no drawing, workbook or client data).

The T-548 builder (R-T548-1), the T-554 adapters (R-T554-1) and the T-557 adapters (R-T557-1) are IMPORTED READ ONLY;
every section is still closed by the T-548 builder. This module adds R-T562-1:

R-T562-1 (proposed, every villa). A statement that takes in a later report:
  (a) SUPERSESSION IS EXPLICIT: when a later merged report restates a figure the statement already prints beside a
      section (T-556 on the T-552 / T-557 plaster restatement), the new figure is printed as the CURRENT block with
      its source, and the old block is kept, labelled SUPERSEDED with the report that superseded it; a statement in
      which a SUPERSEDED block sits in the current place, the current block carries the superseded figures, or the old
      block has lost its label, is refused;
  (b) ENGINE SIDE BY ELEMENT ID: a report row split to element level (one opening, one column mark) takes its engine
      status from that element's own candidate state (the host wall's line, the mark's held lines), never from the
      floor or family it was summed in before; an element on a HELD line is HELD whatever the report called it
      (R-T548-1 (e), R-T557-1 (b)); the move rides on the row ('reclass');
  (c) A REPORT VERDICT THAT IS NOT A CLASS is mapped once, by name (TRACED_SPLIT_OPEN -> UNRESOLVED, named), and the
      mapping rides on the row; a component split as a RANGE between two classes (blinding: HELD .. RULE_DIFFERENCE
      on the held ends) is one row classed by its engine side (HELD) with both ends of the split printed beside;
  (d) GROSS BESIDE NET (T-545 lesson): every section and every total prints the absolute sum of its rows (overall and
      per class) beside the net difference, so a small net never reads as agreement;
  (e) a plain-concrete (blinding) section never shares a trade with a structural RC section (R-T551-3), so no total
      adds them.
"""
from __future__ import annotations

import copy
import csv
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T557 = ROOT / "research/agents_t557"
for p in (T557, ROOT / "research/agents_t554", ROOT / "research/agents_t548"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t557_adapters as X  # noqa: E402  (T-557, read only)

SA, S, A, D = X.SA, X.S, X.A, X.D
label, require_range, _held_entry, _index_lines = X.label, X.require_range, X._held_entry, X._index_lines

T551_JSON = ROOT / "research/agents_t551/out/T551_COLUMN_FOOTING_RECONCILE.json"
T553_JSON = ROOT / "research/agents_t553/out/FLOOR_TILE_RECONCILE_T553.json"
T556_JSON = ROOT / "research/agents_t556/out/T556_PLASTER_HEIGHT.json"
T559_JSON = ROOT / "research/agents_t559/out/T559_LEFTOVER.json"
T292_CSV = ROOT / "research/agents_t292/OPENING_DEDUCTIONS_T292.csv"


AdapterError = X.AdapterError          # one refusal type across the T-557 / T-562 adapters


def _neg(x) -> str:
    return S.s(-D(x))


def _row(name, delta, cls, src, est, ids, source, note="") -> dict:
    return {"name": name, "delta": S.s(D(delta)), "class": cls, "source_cause": src, "engine_status": est,
            "held_line_ids": sorted(ids), "source": source, "note": note}


def _move(row: dict, to: str, est: str, ids: list, why: str, tag: str) -> dict:
    """R-T562-1 (b) / (c): the class the engine side (or the class list) allows; the move rides on the row."""
    if row["class"] != to:
        row["reclass"] = {"tag": tag, "from": row["class"], "to": to, "delta": row["delta"], "why": why}
    row.update({"class": to, "engine_status": est, "held_line_ids": sorted(ids)})
    row["note"] = (row.get("note") or "") + ("; " if row.get("note") else "") + f"{tag}: {why}"
    return row


def expected_by_class(source_totals: dict, rows: list[dict]) -> dict:
    """Class totals = the report's own totals (statement sign; non-class verdicts in their own bucket) moved exactly by
    the rows' reclasses; every non-class bucket must end at 0."""
    exp = {c: Decimal(0) for c in S.CLASSES}
    for c, v in source_totals.items():
        exp[c] = exp.get(c, Decimal(0)) + D(v)
    for r in rows:
        m = r.get("reclass")
        if m:
            exp[m["from"]] = exp.get(m["from"], Decimal(0)) - D(m.get("delta_source", m["delta"]))
            exp[m["to"]] = exp.get(m["to"], Decimal(0)) + D(m.get("delta_source", m["delta"]))
    left = {c: v for c, v in exp.items() if c not in S.CLASSES and v != 0}
    if left:
        raise AdapterError(f"non-class verdicts left unmapped: {left}")
    return {c: S.s(exp[c]) for c in S.CLASSES}


# ============================================================================================ T-551 (m3) ===========
T551_VERDICT = ("Checker 2026-11-06 11:59 (T-551 Gate A) PARTIALLY VERIFIED: WHO IS RIGHT F3 count, FN / F9 notch, lift "
                "ring double, column COUNT (C11, C9) ENGINE_RIGHT by own hand; JOINT_HEAD and blinding plate "
                "RULE_DIFFERENCE; F10 + F, band, necks, held columns HELD; HEIGHT_OPEN traced")
T551_WORKER = ("T-551 worker class (not re-measured by the Checker: GF C1 / C2 / C3 per-mark assignment, BASE, "
               "GLOBAL_DEPTH, strap LENGTH, held bounds)")
T551_C3 = ("GF C3 +1 rests on the merged T-217 / T-394 mark registration, not on the Checker (GF frame label-free; neck "
           "frames carry C3 x5 and x6): T-566 registers the GF marks")
# COUNT per mark (T-551 report s.2, COUNT column; engine - his, m3). The storey sums are asserted against the JSON.
T551_COUNT_MARKS = {
    "GF": [("C1", "-0.375"), ("C2", "-0.750"), ("C9", "-0.9375"), ("C3", "0.46875"), ("C11", "1.03125")],
    "1F": [("C3", "-0.345"), ("C7", "-0.552"), ("C8", "0.621"), ("C9", "0.690")],
}
# Marks whose COUNT term is a HELD drawn member beyond his count (R-T394-2: 1.77975 = GF C3 + 1F C8 + 1F C9).
T551_COUNT_ON_HELD = {("GF", "C3"), ("1F", "C8"), ("1F", "C9")}
T551_COUNT_HELD_SUM = "1.77975"
T551_COUNT_CHECKER = {("GF", "C11"), ("GF", "C9"), ("1F", "C9")}   # named in the Checker's own counts
T551_STATUS = {"COUNT": "VALUED", "JOINT_HEAD": "VALUED", "BASE": "VALUED", "GLOBAL_DEPTH": "VALUED",
               "HEIGHT_OPEN": "VALUED", "HELD": "HELD"}
T551_TRADES = {"columns": "B10 column concrete", "necks": "B10 neck concrete", "lift": "B10 lift pit wall concrete",
               "footing": "B10 footing line concrete (pads + straps + boundary band)",
               "blinding": "B10 blinding (plain concrete, never structural)"}
T551_REF = "freelancer concrete workbook (Drive 'Alsenan chalet project'), Checker own read AGREE: "


def _col_storey(ln: dict) -> str | None:
    el = ln["element_id"]
    if "|" in el:
        return el.rsplit("|", 1)[1]
    m = re.search(r"PLANTED_COLUMN:PC-(GF|1F|2F)", el)
    return m.group(1) if m else None


def _col_mark(ln: dict) -> str | None:
    m = re.search(r":COL:SH\d+:([A-Z0-9.]+)@", ln["element_id"])
    return m.group(1) if m else None


def t551_sections(index: dict, json_path: Path = T551_JSON) -> list[dict]:
    return t551_from(json.loads(json_path.read_text(encoding="utf-8")), index)


T551_FOOTING_HELD = [("HELD F10 + F outline (his F10 row alone; engine bound 2.176 .. 2.275, his share BELOW)", "1.960",
                      "FOOTING"),
                     ("HELD boundary band (his row vs the held line bound 7.2204: his share ABOVE; Q-28 A range)", "8.604",
                      "BAND")]


def t551_from(d: dict, index: dict, count_marks: dict | None = None, count_on_held: set | None = None,
              count_held_sum: str | None = None, count_checker: set | None = None,
              footing_held: list | None = None) -> list[dict]:
    """Five m3 sections from a T-551-format report + the index (any villa); statement sign = his - engine. The
    per-mark COUNT table, the marks whose COUNT is a held drawn member (and their R-T394-2 sum), the Checker-counted
    marks and the footing HELD split are the villa's own tables (defaults: the training villa, T-551 s.2)."""
    count_marks = T551_COUNT_MARKS if count_marks is None else count_marks
    count_on_held = T551_COUNT_ON_HELD if count_on_held is None else count_on_held
    count_held_sum = T551_COUNT_HELD_SUM if count_held_sum is None else count_held_sum
    count_checker = T551_COUNT_CHECKER if count_checker is None else count_checker
    footing_held = T551_FOOTING_HELD if footing_held is None else footing_held
    out = []
    # ---------------- columns ----------------
    cl = _index_lines(index, {"STR.CONC.COLUMN"})
    valued = [{"line_id": x["line_id"], "qty": S.s(D(x["measured_net"])), "unit": "m3"} for x in cl["RELEASED"]]
    v_tot = sum((D(x["qty"]) for x in valued), Decimal(0))
    e_tot = sum((D(f["engine_m3"]) for f in d["columns"].values()), Decimal(0))
    if v_tot != e_tot:
        raise AdapterError(f"T-551 columns: index released {v_tot} != report engine {e_tot}")
    held_by = {}
    for x in cl["HELD"]:
        held_by.setdefault(_col_storey(x), []).append(x)
    rows, src = [], {}
    on_held = Decimal(0)
    for fl, fv in d["columns"].items():
        acc = Decimal(0)
        for comp, c in fv["components"].items():
            part = D(c["m3"])
            acc += part
            src[c["verdict"]] = src.get(c["verdict"], Decimal(0)) - part
            if part == 0:
                continue
            if comp == "COUNT":
                marks = count_marks.get(fl)
                if marks is None or sum((D(v) for _, v in marks), Decimal(0)) != part:
                    raise AdapterError(f"T-551 {fl} COUNT: per-mark table does not sum to {part}")
                for mk, v in marks:
                    r = _row(f"columns {fl}: COUNT {mk}", -D(v), c["verdict"], "COUNT", "VALUED", [],
                             "T-551 s.2 columns COUNT by mark (R-T551-1)",
                             T551_C3 if (fl, mk) == ("GF", "C3") else "")
                    if (fl, mk) in count_on_held:
                        ids = [x["line_id"] for x in held_by.get(fl, []) if _col_mark(x) == mk]
                        if not ids:
                            raise AdapterError(f"T-551 {fl} {mk}: no held column line of the mark")
                        on_held += D(v)
                        _move(r, "HELD", "HELD", ids, "the drawn member beyond his count of the mark is a HELD "
                              "column line (R-T394-2 carries it back by COUNT): the count is drawing evidence, the "
                              "engine side values nothing of it (R-T548-1 (e))", "F-T562-2")
                    label(r, "CHECKER_CONFIRMED" if (fl, mk) in count_checker else "WORKER_PROPOSED",
                          T551_VERDICT if (fl, mk) in count_checker else T551_WORKER)
                    rows.append(r)
                continue
            if comp not in T551_STATUS:
                raise AdapterError(f"T-551 columns: component {comp!r} not in the adapter table")
            est = T551_STATUS[comp]
            ids = [x["line_id"] for x in held_by.get(fl, [])] if est == "HELD" else []
            if est == "HELD" and not ids:
                raise AdapterError(f"T-551 columns {fl}: HELD component with no held line on the storey")
            r = _row(f"columns {fl}: {comp}", -part, c["verdict"], comp, est, ids, "T-551 s.2 columns (R-T551-1)")
            if c["verdict"] == "TRACED_SPLIT_OPEN":
                _move(r, "UNRESOLVED", "VALUED", [], "report verdict TRACED_SPLIT_OPEN (D_ctrl not settled on the "
                      "named members) is not a class: UNRESOLVED, named (R-T562-1 (c))", "F-T562-4")
            conf = comp in ("JOINT_HEAD", "HELD", "HEIGHT_OPEN")
            label(r, "CHECKER_CONFIRMED" if conf else "WORKER_PROPOSED", T551_VERDICT if conf else T551_WORKER)
            rows.append(r)
        if acc != D(fv["engine_m3"]) - D(fv["his_m3"]):
            raise AdapterError(f"T-551 columns {fl}: components {acc} != engine - his")
    if on_held != D(count_held_sum):
        raise AdapterError(f"T-551: COUNT on held members {on_held} != {count_held_sum} (R-T394-2)")
    his_cols = sum((D(f["his_m3"]) for f in d["columns"].values()), Decimal(0))
    no_storey = sorted(x["line_id"] for x in cl["HELD"] if _col_storey(x) is None)
    out.append({"section_id": "T-551/columns", "report": "T-551", "trade": T551_TRADES["columns"],
                "item_codes": ["STR.CONC.COLUMN"], "unit": "m3",
                "reference": {"kind": "FREELANCER", "total": S.s(his_cols), "unit": "m3",
                              "basis": T551_REF + "columns GF 17.4375 + 1F 7.728 + 2F 3.381"},
                "engine": {"valued_total": S.s(v_tot), "valued_lines": valued,
                           "held_lines": [_held_entry(x, f"{x['element_id']} HELD") for x in cl["HELD"]],
                           "excluded_lines": [{"line_id": x["line_id"]} for x in cl["EXCLUDED"]]},
                "rows": rows, "source_by_class": {k: S.s(v) for k, v in src.items()},
                "beside": {"held_without_storey_no_row_of_his": no_storey,
                           "column_beam_pairing_m3": d.get("column_beam_pairing", {}),
                           "note": "HELD rows follow R-T394-2: his share on held lines plus held drawn members "
                                   "beyond his count (carried back by COUNT, here HELD by F-T562-2); the storey-less "
                                   "CN columns have no row of his (held, never 0)"}})
    # ---------------- necks ----------------
    nk = _index_lines(index, {"STR.CONC.NECK"})
    n = d["necks"]
    if nk["RELEASED"] or D(n["engine_m3"]) != 0 or len(nk["HELD"]) != n["engine_held_lines"]:
        raise AdapterError("T-551 necks: index differs from the report (36 HELD, 0 valued)")
    nrows, nsrc = [], {}
    for comp, c in n["components"].items():
        nsrc[c["verdict"]] = nsrc.get(c["verdict"], Decimal(0)) - D(c["m3"])
        nrows.append(label(_row(f"necks: {comp}", -D(c["m3"]), c["verdict"], comp, "HELD",
                                [x["line_id"] for x in nk["HELD"]], "T-551 s.2 necks",
                                "his share inside the engine bound on every held line his rows carry; the engine draws "
                                "one C3 and one C11 neck more than his rows (NO_ROW_OF_HIS)"),
                           "CHECKER_CONFIRMED", T551_VERDICT))
    out.append({"section_id": "T-551/necks", "report": "T-551", "trade": T551_TRADES["necks"],
                "item_codes": ["STR.CONC.NECK"], "unit": "m3",
                "reference": {"kind": "FREELANCER", "total": n["his_m3"], "unit": "m3", "basis": T551_REF + "necks 8.805"},
                "engine": {"valued_total": "0", "valued_lines": [],
                           "held_lines": [_held_entry(x, "neck HELD on the formation / founding depth") for x in nk["HELD"]],
                           "excluded_lines": []},
                "rows": nrows, "source_by_class": {k: S.s(v) for k, v in nsrc.items()},
                "beside": {"report_held_bound_m3": n["engine_held_bound_m3"]}})
    # ---------------- lift pit walls ----------------
    lf = d["lift_walls"]
    pit = [x for x in index.values() if x["item_code"] == "STR.CONC.LIFT" and x["element_id"] == "LIFT_PIT:WALLS"]
    if len(pit) != 1 or pit[0]["class"] != "HELD" or D(lf["engine_m3"]) != 0:
        raise AdapterError("T-551 lift: LIFT_PIT:WALLS is not one HELD line")
    lrows, lsrc = [], {}
    for comp, c in lf["components"].items():
        lsrc[c["verdict"]] = lsrc.get(c["verdict"], Decimal(0)) - D(c["m3"])
        if comp == "SCOPE_DOUBLE":
            r = _row("lift pit walls: SCOPE_DOUBLE (four column pieces in his ring, also in his neck rows)",
                     -D(c["m3"]), c["verdict"], comp, "NONE", [], "T-551 s.2 lift (R-T394-6)",
                     "the lift necks own the four column pieces; no lift-wall element by scope")
        else:
            r = _row(f"lift pit walls: {comp} (net ring 1.10 m2 x his depth)", -D(c["m3"]), c["verdict"], comp,
                     "HELD", [pit[0]["line_id"]], "T-551 s.2 lift", "depth 'as per lift manufacturer' (D-43)")
        lrows.append(label(r, "CHECKER_CONFIRMED", T551_VERDICT))
    tie = [x["line_id"] for x in index.values() if x["item_code"] == "STR.CONC.LIFT" and x["line_id"] != pit[0]["line_id"]]
    out.append({"section_id": "T-551/lift-walls", "report": "T-551", "trade": T551_TRADES["lift"],
                "item_codes": ["STR.CONC.LIFT (LIFT_PIT:WALLS)"], "unit": "m3",
                "reference": {"kind": "FREELANCER", "total": lf["his_m3"], "unit": "m3",
                              "basis": T551_REF + "lift walls 8 x 0.20 x 1.50 = 2.40"},
                "engine": {"valued_total": "0", "valued_lines": [],
                           "held_lines": [_held_entry(pit[0], "LIFT_PIT:WALLS HELD blank (D-43)")], "excluded_lines": []},
                "rows": lrows, "source_by_class": {k: S.s(v) for k, v in lsrc.items()},
                "beside": {"not_in_this_section": tie,
                           "note": "LIFT_TIE_BEAM:GF (STR.CONC.LIFT, HELD) is the tie-beam element, not the pit wall"}})
    # ---------------- footing line (pads + straps + boundary band) ----------------
    fo = d["footing_line"]
    fl_ = _index_lines(index, {"STR.CONC.FOOTING", "STR.CONC.STRAP"})
    band = [x for x in index.values() if x["item_code"] == "STR.CONC.BOUNDARY_WALL" and x["class"] == "HELD"
            and x["element_id"].endswith(":BEAM") and "FOUNDATION" in x["element_id"]]
    if len(band) != 1:
        raise AdapterError("T-551 footing: the boundary band line is not one HELD STR.CONC.BOUNDARY_WALL foundation beam")
    fval = [{"line_id": x["line_id"], "qty": S.s(D(x["measured_net"])), "unit": "m3"} for x in fl_["RELEASED"]]
    f_tot = sum((D(x["qty"]) for x in fval), Decimal(0))
    if f_tot != D(fo["engine_m3"]):
        raise AdapterError(f"T-551 footing: index pads + straps {f_tot} != report {fo['engine_m3']}")
    f10 = [x["line_id"] for x in fl_["HELD"] if x["item_code"] == "STR.CONC.FOOTING"]
    frows, fsrc = [], {}
    names = {"COUNT": ("COUNT F3 (two drawn outlines both tagged F3)", "VALUED", []),
             "OVERLAP": ("OVERLAP FN notch 0.40 x 0.35 x 0.30 owned by F9 (his FN rows bill it again)", "VALUED", []),
             "LENGTH": ("LENGTH SB2 -0.0036 / SB3 +0.0016 (drawn 2.2927 / 3.2580 m vs his rounded)", "VALUED", [])}
    held_parts = [(nm, v, f10 if kind == "FOOTING" else [band[0]["line_id"]]) for nm, v, kind in footing_held]
    for comp, c in fo["components"].items():
        part = D(c["m3"])
        fsrc[c["verdict"]] = fsrc.get(c["verdict"], Decimal(0)) - part
        if comp == "HELD":
            if sum((D(v) for _, v, _ in held_parts), Decimal(0)) != -part:
                raise AdapterError(f"T-551 footing HELD parts != {-part}")
            for nm, v, ids in held_parts:
                frows.append(label(_row(f"footing line: {nm}", v, "HELD", "HELD", "HELD", ids, "T-551 s.2 footing "
                                        "(R-T551-2)"), "CHECKER_CONFIRMED", T551_VERDICT))
            continue
        nm, est, ids = names[comp]
        conf = comp in ("COUNT", "OVERLAP")
        frows.append(label(_row(f"footing line: {nm}", -part, c["verdict"], comp, est, ids, "T-551 s.2 footing "
                                "(R-T551-2)"), "CHECKER_CONFIRMED" if conf else "WORKER_PROPOSED",
                           T551_VERDICT if conf else T551_WORKER))
    out.append({"section_id": "T-551/footing-line", "report": "T-551", "trade": T551_TRADES["footing"],
                "item_codes": ["STR.CONC.FOOTING", "STR.CONC.STRAP", "STR.CONC.BOUNDARY_WALL (foundation band)"],
                "unit": "m3",
                "reference": {"kind": "FREELANCER", "total": fo["his_m3"], "unit": "m3",
                              "basis": T551_REF + "footings sheet pads 65.634 + straps 3.3925 + band 8.604 = 77.6305 "
                                                  "(his 0.10 plate 47.055 is outside it: blinding section)"},
                "engine": {"valued_total": S.s(f_tot), "valued_lines": fval,
                           "held_lines": [_held_entry(x, f"{x['element_id']} HELD") for x in fl_["HELD"] + band],
                           "excluded_lines": [{"line_id": x["line_id"]} for x in fl_["EXCLUDED"]]},
                "rows": frows, "source_by_class": {k: S.s(v) for k, v in fsrc.items()},
                "beside": {"zero_components_not_listed": ["SB1 in F10 + F (0 .. 0.385), SB3 in F3 (0.0295 .. 0.2683): "
                                                          "held strap pieces, no row of his (held lines listed)"],
                           "closed_by_name": "the 20 Oct 'footing -0.37 UNRESOLVED' (released 77.265 vs 77.631) is "
                                             "closed by name on V3.0.58 (T-551 s.2)"}})
    # ---------------- blinding (plain concrete) ----------------
    b = d["blinding"]
    bl = _index_lines(index, {"STR.CONC.BLINDING"})
    bval = [{"line_id": x["line_id"], "qty": S.s(D(x["measured_net"])), "unit": "m3"} for x in bl["RELEASED"]]
    b_tot = sum((D(x["qty"]) for x in bval), Decimal(0))
    if b_tot != D(b["engine_released_m3"]):
        raise AdapterError("T-551 blinding: index released differs from the report")
    lo_end, hi_end = b["held_low_end"], b["held_high_end"]
    for e in (lo_end, hi_end):
        if D(e["HELD"]) + D(e["RULE_DIFFERENCE"]) != D(b["residual_m3"]):
            raise AdapterError("T-551 blinding: a held end does not close")
    held_split = require_range(sorted([-D(lo_end["HELD"]), -D(hi_end["HELD"])]), "T-551 blinding HELD share")
    rd_split = require_range(sorted([-D(lo_end["RULE_DIFFERENCE"]), -D(hi_end["RULE_DIFFERENCE"])]),
                             "T-551 blinding RULE_DIFFERENCE share")
    r = _row("blinding: his one 0.10 plate over the plot rectangle vs the engine pits + held blinding elements",
             -D(b["residual_m3"]), "HELD", "HELD + RULE_DIFFERENCE", "HELD", [x["line_id"] for x in bl["HELD"]],
             "T-551 s.2 blinding (T-478 restated)",
             f"split is a RANGE on the held ends: HELD {S.s(held_split[0])} .. {S.s(held_split[1])} + RULE_DIFFERENCE "
             f"{S.s(rd_split[0])} .. {S.s(rd_split[1])} (one layer under the whole plot that no sheet draws); the row "
             "total is exact at both ends")
    r["reclass"] = {"tag": "F-T562-5", "from": "RULE_DIFFERENCE", "to": "HELD", "delta": _neg(lo_end["RULE_DIFFERENCE"]),
                    "delta_bridge_hi": _neg(hi_end["RULE_DIFFERENCE"]),
                    "why": "the split between HELD and RULE_DIFFERENCE moves with the held lines' value: one row, "
                           "classed by its engine side (HELD), both ends beside (R-T562-1 (c)); RULE_DIFFERENCE once "
                           "the held blinding elements are valued"}
    label(r, "CHECKER_CONFIRMED", T551_VERDICT)
    out.append({"section_id": "T-551/blinding", "report": "T-551", "trade": T551_TRADES["blinding"],
                "item_codes": ["STR.CONC.BLINDING"], "unit": "m3",
                "reference": {"kind": "FREELANCER", "total": b["his_m3"], "unit": "m3",
                              "basis": T551_REF + "plain 0.10 plate 15 x 31.37 = 47.055 (outside his footing total)"},
                "engine": {"valued_total": S.s(b_tot), "valued_lines": bval,
                           "held_lines": [_held_entry(x, f"{x['element_id']} HELD") for x in bl["HELD"]],
                           "excluded_lines": []},
                "rows": [r],
                "source_by_class": {"HELD": _neg(lo_end["HELD"]), "RULE_DIFFERENCE": _neg(lo_end["RULE_DIFFERENCE"])},
                "beside": {"held_share_range_m3": [S.s(held_split[0]), S.s(held_split[1])],
                           "rule_difference_share_range_m3": [S.s(rd_split[0]), S.s(rd_split[1])],
                           "report_held_bound_m3": b["engine_held_bound_m3"],
                           "note": "blinding is plain concrete: its own trade, never in a structural RC total "
                                   "(R-T551-3, R-T562-1 (e))"}})
    return out


# ============================================================================================ T-553 floor tile =====
T553_TRADE = "B3 floor tile (installed)"
T553_VERDICT = ("Checker 2026-11-06 12:01 (T-553 Gate A) PARTIALLY VERIFIED: totals both sides AGREE, ENGINE_WRONG 2 / 2 "
                "confirmed (dressing own P7757.dxf re-measure 1.65 x 1.80 = 2.970), rooms 2 / 25 (dressing, dewaneya); "
                "WHO IS RIGHT stair / arrivals / lift / strips RULE_DIFFERENCE, band HELD (D-48), curved room / GF "
                "stair room / 2F corridor UNRESOLVED")
T553_WORKER = "T-553 worker class (room ENGINE_RIGHT / TOLERANCE terms other than the dewaneya not re-measured)"
T553_CODES = ["FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.FLOOR.FINISH_HELD"]
T553_FIX = "T-564"
T553_CONFIRMED_UNRES = ("GF stair room", "1F curved", "2F lobby")


def t553_section(index: dict, json_path: Path = T553_JSON) -> dict:
    return t553_from(json.loads(json_path.read_text(encoding="utf-8")), index)


def t553_from(d: dict, index: dict, fix_row: str = T553_FIX) -> dict:
    t = d["table"]
    ll = _index_lines(index, set(T553_CODES))
    valued = [{"line_id": x["line_id"], "qty": S.s(D(x["measured_net"])), "unit": "m2"} for x in ll["RELEASED"]]
    v_tot = sum((D(x["qty"]) for x in valued), Decimal(0))
    if v_tot != D(t["engine_total"]):
        raise AdapterError(f"T-553: index floor tile {v_tot} != report {t['engine_total']}")
    if D(t["freelancer_total"]) != D(d["freelancer_dry"]) + D(d["freelancer_wet"]):
        raise AdapterError("T-553: his total != dry + wet")
    held_ids = {x["line_id"] for x in ll["HELD"]}
    for h in t["held_lines"]:
        if h["line_id"] not in held_ids:
            raise AdapterError(f"T-553: held line {h['line_id']} is not a held floor tile line")
    rows, acc_all = [], Decimal(0)
    for rr in t["rows"]:
        acc = Decimal(0)
        for c in rr["components"]:
            part = D(c["delta"])
            acc += part
            if part == 0:
                continue
            nm = f"{rr['room']}: {c['name']}"
            own = c.get("owned_by")
            oln = index.get(own) if own else None
            est, note = "VALUED", c.get("basis", "")
            if c["cause"] == "ENGINE_WRONG":
                r = _row(nm, -part, "ENGINE_WRONG", "ENGINE_WRONG", "NONE", [], "T-553 room table (R-T553-1)", note)
                r["fix_row"] = fix_row
                r["note"] += (f"; F-T553-1: the space has ARCH.SPACE / FIN.CEILING / FIN.PAINT.CEILING / FIN.SKIRTING "
                              f"lines and no FIN.FLOOR line: fix row {fix_row} (add the floor line, finish class HELD by "
                              "name, never 0)")
                rows.append(label(r, "CHECKER_CONFIRMED", T553_VERDICT))
                continue
            if oln is not None:
                note += f"; owned by {own} ({oln['item_code']} {oln['class']}, another family)"
            if c["cause"] == "RULE_DIFFERENCE" and oln is not None:
                est = "NONE"                          # no floor tile by the owner rule; another trade owns it
            r = _row(nm, -part, c["cause"], c["cause"], est, [], "T-553 room table (R-T553-1)", note)
            if c["cause"] == "HELD":
                if any(own == h for h in held_ids):
                    r.update({"engine_status": "HELD", "held_line_ids": [own]})
                else:
                    _move(r, "UNRESOLVED", "NONE", [], "the element (garden band / curb, D-48 planter or floor) has no "
                          "floor-tile candidate line, own or cross-family (its ARCH lines are of the same unit): never "
                          "HELD without a line (R-T554-1 (d)); D-48 stays the designer item; element-register question "
                          "for the Lead, not an owner question", "F-T562-3")
            confirmed = (c["cause"] in ("ENGINE_WRONG", "HELD")
                         or (c["cause"] == "RULE_DIFFERENCE" and (oln is not None or "strip" in nm.lower()))
                         or (c["cause"] == "UNRESOLVED" and rr["room"].startswith(T553_CONFIRMED_UNRES))
                         or rr["room"].startswith("GF dewaneya"))
            rows.append(label(r, "CHECKER_CONFIRMED" if confirmed else "WORKER_PROPOSED",
                              T553_VERDICT if confirmed else T553_WORKER))
        if acc != D(rr["delta"]):
            raise AdapterError(f"T-553 {rr['room']}: components {acc} != row delta {rr['delta']}")
        acc_all += acc
    if acc_all != D(t["gap_engine_minus_freelancer"]):
        raise AdapterError("T-553: rows do not close to the report gap")
    miss = d["missing_floor_lines"]
    ew_area = sum((D(str(m["area"])) for m in miss), Decimal(0))
    return {
        "section_id": "T-553/floor-tile", "report": "T-553", "trade": T553_TRADE, "item_codes": T553_CODES,
        "unit": "m2",
        "reference": {"kind": "FREELANCER", "total": t["freelancer_total"], "unit": "m2",
                      "basis": "freelancer floors workbook, tiles sheet H70 = dry D31 337.57 + wet H65 72.01 (Checker "
                               "AGREE; installed m2, no waste) (Drive 'Alsenan chalet project')"},
        "engine": {"valued_total": S.s(v_tot), "valued_lines": valued,
                   "held_lines": [_held_entry(x, f"{x['element_id']} finish material HELD") for x in ll["HELD"]],
                   "excluded_lines": [{"line_id": x["line_id"]} for x in ll["EXCLUDED"]]},
        "rows": rows,
        "source_by_class": {k: _neg(v) for k, v in t["by_cause"].items()},
        "beside": {
            "engine_wrong_restated": {
                "finding": "F-T553-1", "fix_row": fix_row, "missing_floor_lines": miss,
                "corrected_area_m2": S.s(ew_area), "area_status": "DRAWING-CONFIRMED (Checker own re-measure)",
                "finish_class": "HELD (no finish printed; FIN.FLOOR.FINISH_HELD by name, never 0)",
                "engine_with_correction_m2": S.s(v_tot + ew_area),
                "note": "beside only: never added to the engine valued or bounded columns until wired"},
            "class_defect": {"finding": "F-T553-2", "fix_row": fix_row, "m2_effect": "0",
                             "what": "GF kitchen floor L-83609efc coded FIN.FLOOR.PORCELAIN while its bed, membrane and "
                                     "threshold are WET: recode to FIN.FLOOR.WET_TILE (adhesive group per Q-45)"},
            "class_moves_zero_area": t["class_moves"],
            "tile_size": t["by_size"],
            "outdoor_outside_his_total": d["outdoor"],
            "note": "stair marble is owned once by its B7 / B6 lines (RULE_DIFFERENCE rows name them, engine status "
                    "NONE for floor tile); adhesive and boxes stay HELD by size (TILE_SIZE_NOT_GIVEN both sides)"},
    }


# ============================================================================================ T-559 on B9 ==========
T559_VERDICT = ("Checker 2026-11-06 10:20 (T-559 Gate A) PARTIALLY VERIFIED: HELD -23.37 and door head -3.90 rebuilt "
                "from his rows; counts +6.30 UNRESOLVED by name; edge ownership 32 / 32 by id")
T559_WORKER = ("T-559 worker class (printed heads / arched outlines from the T-201 / T-175 / T-207 prints and width "
               "tolerances not re-measured by the Checker; engine opening sizes reused from T-292)")
T559_TARGETS = ("GF: openings census", "1F: openings census", "2F: openings census", "his 20 cm openings with no floor")
PER_RUN_ROW = "parapets: 1F ROOF +9.70 (his roof-page row 'الدروه' 42.85 x 1.80): his flat printed height 1.30 m vs each run"
BELOW_FINISH = "his height below the finished roof"
OPEN_ID = re.compile(r"\b(D-(?:GF|1F|2F)-\d+|L-(?:GF|1F|2F)-\d+|W\d+)\b")


def _host_walls(csv_path: Path = T292_CSV) -> dict:
    out = {}
    for r in csv.DictReader(csv_path.open(encoding="utf-8")):
        out.setdefault(r["opening_id"], set()).add((r["host_wall"], r["held"] == "yes"))
    return out


def t559_restate(sec: dict, d: dict, walls_list: list[dict], held_lines: list[dict], hosts: dict | None = None) -> dict:
    """R-T557-1 (e) + R-T562-1 (b): replace the four openings rows (sum = T-559's openings total) by T-559's
    opening-by-opening rows, each with the engine status of its own host wall; annotate the rows T-559 names."""
    sec = copy.deepcopy(sec)
    hosts = _host_walls() if hosts is None else hosts
    walls = {w["wall_id"]: w for w in walls_list}
    idx = [i for i, r in enumerate(sec["rows"]) if r["name"].startswith(T559_TARGETS)]
    if len(idx) != len(T559_TARGETS):
        raise AdapterError(f"T-559: {len(idx)} target rows found, {len(T559_TARGETS)} expected")
    old = [sec["rows"][i] for i in idx]
    if any(r["class"] != "UNRESOLVED" for r in old):
        raise AdapterError("T-559: a target row is no longer UNRESOLVED: re-read before restating")
    old_sum = sum((D(r["delta"]) for r in old), Decimal(0))
    if old_sum != D(d["openings"]["total"]) or old_sum != D(d["openings_t550_m2"]):
        raise AdapterError(f"T-559: target rows {old_sum} != T-559 openings {d['openings']['total']}")

    def held_ids(floor: str, wid: str) -> list[str]:
        w = walls.get(wid)
        if w is None or w["floor"] != floor:
            raise AdapterError(f"T-559: wall {wid} not in the {floor} register")
        t = D(w["t_m"]).normalize()
        out = [x["line_id"] for x in held_lines
               if x["element_id"].startswith(f"{floor}-WALLS:walls t=")
               and D(x["element_id"].split("t=")[1].split("#")[0]).normalize() == t]
        if not out:
            raise AdapterError(f"T-559: no held {floor} masonry line of t {t} for {wid}")
        return sorted(out)

    new, src = [], {}
    for g in d["openings"]["groups"]:
        acc = Decimal(0)
        for r in g["rows"]:
            part = D(r["delta"])
            acc += part
            src[r["cause"]] = src.get(r["cause"], Decimal(0)) + part
            if part == 0:
                continue
            nm = f"openings {g['floor']}: {r['name']} / {r['term']}"
            m = OPEN_ID.search(r["name"])
            row = _row(nm, part, r["cause"], r["cause"], "VALUED", [], "T-559 s.1 openings by id (R-T559-1)",
                       r.get("note", ""))
            row["correction"] = "T-559"
            if m is None:                                        # his-only unit: no engine opening
                if r["cause"] != "UNRESOLVED":
                    raise AdapterError(f"T-559 {nm}: an unpaired unit must be UNRESOLVED")
                row["engine_status"] = "NONE"
            else:
                oid = m.group(1)
                hs = hosts.get(oid)
                if not hs or len({h for h, _ in hs}) != 1:
                    raise AdapterError(f"T-559 {oid}: host wall not unique in the T-292 ledger")
                wid = next(iter(hs))[0]
                held_open = any(h for _, h in hs)
                w = walls[wid]
                fl = w["floor"]
                on_held = w["valued_m2"] is None or held_open
                row["note"] = (row["note"] + "; " if row["note"] else "") + \
                    f"host wall {wid} ({w['state_v3_0_58']}{', opening HELD' if held_open else ''})"
                if on_held:
                    ids = held_ids(fl, wid)
                    if r["cause"] in ("HELD", "UNRESOLVED"):
                        row.update({"engine_status": "HELD", "held_line_ids": ids})
                    else:
                        _move(row, "HELD", "HELD", ids, f"the opening's host wall {wid} is a HELD masonry line (or the "
                              "opening itself is held): its size term values nothing in the engine (R-T548-1 (e), "
                              "R-T562-1 (b)); source class kept", "F-T562-1")
            conf = r["cause"] in ("HELD", "UNRESOLVED") or (r["cause"] == "RULE_DIFFERENCE" and r["term"] == "height")
            new.append(label(row, "CHECKER_CONFIRMED" if conf else "WORKER_PROPOSED",
                             T559_VERDICT if conf else T559_WORKER))
        if acc != D(g["delta"]):
            raise AdapterError(f"T-559 group {g['floor']}: rows {acc} != group {g['delta']}")
    grouped = [x for g in d["openings"]["groups"] for x in g["rows"]]
    tail = list(d["openings"]["rows"])
    for x in grouped:
        tail.remove(x)                                   # ValueError if a group row is not in the report's row list
    for r in tail:                                       # register print rows outside the groups
        part = D(r["delta"])
        src[r["cause"]] = src.get(r["cause"], Decimal(0)) + part
        row = _row(f"openings GF: {r['name']} / {r['term']}", part, r["cause"], r["cause"], "VALUED", [],
                   "T-559 s.1 openings (R-T559-1)", r.get("note", ""))
        row["correction"] = "T-559"
        if "GF-W04" in r["name"] and walls["GF-W04"]["valued_m2"] is None:
            _move(row, "HELD", "HELD", held_ids("GF", "GF-W04"), "the printed wall total belongs to the HELD wall "
                  "GF-W04 (R-T548-1 (e))", "F-T562-1")
        new.append(label(row, "WORKER_PROPOSED", T559_WORKER))
    if sum((D(r["delta"]) for r in new), Decimal(0)) != old_sum:
        raise AdapterError("T-559: the opening rows do not sum to the replaced rows")
    # the report's by-cause covers the whole 25.92 leftover: its UNRESOLVED also holds the non-opening parts, which the
    # statement already carries as their own rows (T-550 unresolved - T-550 openings)
    rest = D(d["t550_unresolved_m2"]) - D(d["openings_t550_m2"])
    for c in S.CLASSES:
        want = D(d["by_cause"].get(c, "0")) - (rest if c == "UNRESOLVED" else 0)
        if src.get(c, Decimal(0)) != want:
            raise AdapterError(f"T-559: openings {c} {src.get(c, 0)} != report {want}")
    keep = [r for i, r in enumerate(sec["rows"]) if i not in idx]
    first = idx[0]
    sec["rows"] = keep[:first] + new + keep[first:]
    # annotations on the rows T-559 names (no number moves)
    per = [r for r in sec["rows"] if r["name"].startswith(PER_RUN_ROW)]
    if len(per) != 1 or D(per[0]["delta"]) != D(d["per_run_sum_m2"]):
        raise AdapterError("T-559: the per-run heights row is missing or differs from T-559's 7.63068050")
    runs = "; ".join(f"{p['run']} {p['centreline_m']} x {p['h_status']}" for p in d["per_run_heights_1F"])
    per[0]["note"] += (f"; T-559 per-run table (h printed vs his 1.30): {runs}; T-559 keeps these ENGINE_RIGHT in its own "
                       "B9 table, the statement keeps HELD (R-T548-1 (e): parapet face block alternative HELD, material "
                       "Q-65 C; Checker 10:20 note)")
    es = d["edge_summary"]
    for r in sec["rows"]:
        if BELOW_FINISH in r["name"]:
            r["note"] += (f"; T-559 edge members (R-T559-2): {es['CARRIED_ONCE']} ST bands under the four roofs' "
                          f"parapets, each carried once by a live STR.CONC.BEAM line, {es['OMITTED']} omitted (Checker "
                          "10:20 own handle read, ST geometry reused): the F-C-T550-1 unchecked point is answered")
        elif r["name"].startswith("1F 'projections' row"):
            r["note"] += "; T-559: no projections element found (T-550 search stands), still UNRESOLVED by name"
        elif "RESIDUAL: wall-length census" in r["name"]:
            r["note"] += ("; T-559 wall-length census beside (net per floor GF +1.438 / 1F +3.064 / 2F -0.50 m, 1F "
                          "external +4.157 m): not matched run by run, UNRESOLVED")
    sec["t559"] = {"replaced_rows": [{"name": r["name"], "delta": r["delta"]} for r in old],
                   "openings_by_cause_report": {c: S.s(v) for c, v in src.items()},
                   "edge_summary": es, "unresolved_gross_abs_report_m2": d["unresolved_gross_abs_m2"]}
    return sec


def t559_expected_by_class(prev_by_class: dict, sec: dict) -> dict:
    """B9 class totals = the previous statement's + T-559's openings by cause - the replaced UNRESOLVED rows + the
    F-T562-1 moves."""
    out = {c: D(prev_by_class[c]) for c in S.CLASSES}
    for r in sec["t559"]["replaced_rows"]:
        out["UNRESOLVED"] -= D(r["delta"])
    for c, v in sec["t559"]["openings_by_cause_report"].items():
        out[c] += D(v)
    for r in sec["rows"]:
        m = r.get("reclass")
        if m and m["tag"] == "F-T562-1":
            out[m["from"]] -= D(m["delta"])
            out[m["to"]] += D(m["delta"])
    return {c: S.s(v) for c, v in out.items()}


def verify_per_run_held(st: dict) -> None:
    """Acceptance: the 1F per-run parapet heights stay HELD in the statement (R-T548-1 (e)), never ENGINE_RIGHT."""
    sec = [c for c in st["sections"] if c["section_id"] == "T-543/blockwork"][0]
    rows = [r for r in sec["rows"] if r["name"].startswith(PER_RUN_ROW)]
    if len(rows) != 1 or rows[0]["class"] != "HELD" or rows[0]["engine_status"] != "HELD":
        raise AdapterError("B9 per-run parapet heights are not HELD: a HELD engine side counted as agreement")


# ============================================================================================ T-556 supersession ====
T556_SOURCE = ("T-556 PLASTER_HEIGHT_METHOD_V1 (R-T556-1), MERGED 431ac67f; Checker 10:20 PARTIALLY VERIFIED 2 / 11 "
               "rooms (1F-04 63.141, 2F-03 69.775 own re-measure; GF-15 66.529 confirmed by hand)")


def t556_supersede(sec: dict, d: dict, index: dict) -> dict:
    """R-T562-1 (a): the T-556 restatement is CURRENT, the T-557 block is kept and labelled SUPERSEDED."""
    sec = copy.deepcopy(sec)
    old = sec["beside"].get("engine_wrong_restated")
    if old is None or old.get("status") == "SUPERSEDED":
        raise AdapterError("T-556: no current T-557 restatement to supersede")
    lines, rel_now, rel = [], Decimal(0), [Decimal(0), Decimal(0)]
    al = [Decimal(0), Decimal(0)]
    for r in d["rows"]:
        ix = index.get(r["line_id"])
        if ix is None or ix["item_code"] != "FIN.PLASTER" or ix["class"] != r["candidate_class"]:
            raise AdapterError(f"T-556 {r['room']}: line {r['line_id']} is not that candidate plaster line")
        lo, hi = require_range([r["new_lo"], r["new_hi"]], f"T-556 {r['room']} restated")
        al = [al[0] + lo, al[1] + hi]
        if ix["class"] == "RELEASED":
            if D(ix["measured_net"]) != D(r["old_paint_height_basis"]["value"][0]):
                raise AdapterError(f"T-556 {r['room']}: candidate value differs from the report's old value")
            rel_now += D(ix["measured_net"])
            rel = [rel[0] + lo, rel[1] + hi]
        lines.append({"line_id": r["line_id"], "room": r["room"], "candidate_class": ix["class"],
                      "candidate_m2": None if ix["measured_net"] is None else S.s(D(ix["measured_net"])),
                      "restated_HELD_BOUNDED_m2": [S.s(lo), S.s(hi)], "t552_t557_restated_m2": r["t552_restated"],
                      "zone": r["zone"], "status": r["status"]})
    if [S.s(x) for x in rel] != [S.s(D(x)) for x in d["released_4_lines"]["new"]] or \
            S.s(rel_now) != S.s(D(d["released_4_lines"]["old"])):
        raise AdapterError("T-556: released-line totals differ from the report")
    if [S.s(x) for x in al] != [S.s(D(x)) for x in d["totals"]["new"]]:
        raise AdapterError("T-556: 11-line totals differ from the report")
    if S.s(rel_now) != old["released_lines_now_m2"]:
        raise AdapterError("T-556: the released lines changed under the T-557 restatement")
    fr = d["freelancer_same_rooms"]
    cur = {"status": "CURRENT", "source": T556_SOURCE, "fix_row": "T-556", "rule": "R-T556-1 (Q-72, Q-14, Q-73)",
           "verdict": old["verdict"], "released_lines_now_m2": S.s(rel_now),
           "released_lines_restated_HELD_BOUNDED_m2": [S.s(rel[0]), S.s(rel[1])],
           "all_11_dry_lines_restated_HELD_BOUNDED_m2": [S.s(al[0]), S.s(al[1])],
           "lines": lines,
           "corrections_to_t552": ["W03 head 4.30 above the paint height 3.65 is re-cut at the plaster height: GF-15 "
                                   "66.529 (not 68.720 .. 70.874: -3.268 m2, Checker error recorded), GF-08 -1.040",
                                   "under a roof the term is the ROOF build-up (D-39 / DCR-6): drawn-section scenario, "
                                   "ESTIMATED, sensitivity per cm; no lower bound printed",
                                   "a hole of known height is deducted in full at the soffit height (W11 / W12 h 2.20)",
                                   "beam ends quantified (closed rooms 2 ends, open rooms 0 .. 2)"],
           "method_vs_freelancer_same_11_rooms": {"engine_method_gross_m2": fr["engine_gross_at_plaster_height"],
                                                  "his_gross_m2": fr["his_gross"], "delta_m2": fr["delta"],
                                                  "delta_pct": fr["delta_pct"], "cause": fr["cause"],
                                                  "label": "method figure on HELD lines (unwired): not an engine "
                                                           "valued figure, never in the engine columns"},
           "wiring": "T-558 manifest / T-563 integration package (BLOCKED, wrapper allow-list): the candidate still "
                     "carries the paint height, so the four ENGINE_WRONG rows stay",
           "note": "the restated quantity is HELD (BOUNDED on the roof build-up, D-39): never added to the engine "
                   "valued or bounded columns, never agreement"}
    sup = dict(old)
    sup.update({"status": "SUPERSEDED", "superseded_by": "T-556 (MERGED 431ac67f; Checker 10:20)",
                "why": "T-552 / T-557 kept W03 capped at the paint height and used the floor build-up under roofs"})
    sec["beside"]["engine_wrong_restated"] = cur
    sec["beside"]["engine_wrong_restated_superseded_T557"] = sup
    return sec


def current_restatement(beside: dict) -> dict:
    """R-T562-1 (a): the block quoted as current must be CURRENT; a SUPERSEDED block quoted as current is refused."""
    cur = beside.get("engine_wrong_restated")
    if cur is None or cur.get("status") != "CURRENT":
        raise AdapterError(f"restatement quoted as current has status {None if cur is None else cur.get('status')!r}: "
                           "a SUPERSEDED figure is never current")
    return cur


def verify_supersession(st: dict, d556: dict) -> None:
    sec = [c for c in st["sections"] if c["section_id"] == "T-552/plaster-internal"][0]
    cur = current_restatement(sec["beside"])
    old = sec["beside"].get("engine_wrong_restated_superseded_T557")
    if old is None or old.get("status") != "SUPERSEDED" or not old.get("superseded_by"):
        raise AdapterError("the T-557 plaster restatement lost its SUPERSEDED label")
    if cur["released_lines_restated_HELD_BOUNDED_m2"] != [S.s(D(x)) for x in d556["released_4_lines"]["new"]]:
        raise AdapterError("current plaster restatement is not T-556's")
    if cur["released_lines_restated_HELD_BOUNDED_m2"] == old["released_lines_restated_HELD_BOUNDED_m2"]:
        raise AdapterError("current plaster restatement carries the superseded figures")


# ============================================================================================ gross beside net ======
def add_gross(st: dict) -> None:
    """R-T562-1 (d): absolute sums beside every net (sections and totals)."""
    by_sec = {}
    for c in st["sections"]:
        g = {k: Decimal(0) for k in S.CLASSES}
        for r in c["rows"]:
            g[r["class"]] += abs(D(r["delta"]))
        tot = sum(g.values(), Decimal(0))
        if tot < abs(D(c["difference"])):
            raise AdapterError(f"{c['section_id']}: gross below net")
        c["gross_abs"] = S.s(tot)
        c["by_class_gross_abs"] = {k: S.s(v) for k, v in g.items()}
        by_sec[c["section_id"]] = g
    for t in st["totals"]:
        g = {k: Decimal(0) for k in S.CLASSES}
        for sid in t["sections"]:
            for k in S.CLASSES:
                g[k] += by_sec[sid][k]
        t["gross_abs"] = S.s(sum(g.values(), Decimal(0)))
        t["by_class_gross_abs"] = {k: S.s(v) for k, v in g.items()}


def verify_gross(st: dict) -> None:
    for blk in st["sections"] + st["totals"]:
        if "gross_abs" not in blk or "by_class_gross_abs" not in blk:
            raise AdapterError(f"{blk.get('section_id', blk.get('trade'))}: net printed without its gross")


def verify_blinding_apart(st: dict) -> None:
    """R-T562-1 (e): the blinding section's trade is shared by no structural section."""
    bl = [c for c in st["sections"] if c["section_id"] == "T-551/blinding"]
    if len(bl) != 1:
        raise AdapterError("blinding section missing")
    for t in st["totals"]:
        if "T-551/blinding" in t["sections"] and len(t["sections"]) != 1:
            raise AdapterError("blinding (plain concrete) added into a structural total")
