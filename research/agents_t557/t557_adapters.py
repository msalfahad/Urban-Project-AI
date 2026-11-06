"""T-557: reconciled-quantities statement adapters for the merged T-545 (B10-07 beams, m3), T-547 (B4 wet-room wall
tile, m2), T-552 (B5 wall plaster internal / external, m2) and the T-550 restatement of the T-543 blockwork section
(research, unwired; computes no new quantity; reads committed research outputs and the V3.0.57 line index only).

The T-548 builder (statement.py, R-T548-1) and the T-554 adapters (statement_adapters.py, R-T554-1) are IMPORTED READ
ONLY; every section is closed by the T-548 builder. This module adds R-T557-1:

R-T557-1 (proposed, every villa). A statement adapter carries a source report's classes AS THE CHECKER CLASSED THEM:
  (a) VERIFICATION LABEL: every row it adds carries 'verification' = CHECKER_CONFIRMED (the Checker's verdict re-measured
      or re-derived that class) or WORKER_PROPOSED (the worker's class, not independently confirmed), with the verdict
      it rests on; a statement row is never VERIFIED by being in the statement;
  (b) ENGINE SIDE FIRST: a component whose engine element is a HELD line is class HELD whatever the report called it
      (R-T548-1 (e)); its source cause is kept beside ('source_cause'); every such move rides on its row
      ('reclass');
      a component whose element has NO candidate line is UNRESOLVED with engine status NONE (R-T554-1 (d));
  (c) ENGINE_WRONG IS NEVER AGREEMENT: a Checker-confirmed ENGINE_WRONG (ENGINE_WRONG_CONFIRMED) must land in the
      ENGINE_WRONG column with its fix row; a statement in which such a row is classed ENGINE_RIGHT / TOLERANCE /
      RULE_DIFFERENCE (or is missing) is refused; the wrong lines' restated quantity is printed beside as a HELD
      (BOUNDED) range, never added to the engine valued or bounded columns;
  (d) A BOUND IS A RANGE: every bound printed beside (a HELD line's drawing-derived bound, a restated ENGINE_WRONG
      line) is a pair [low, high] with low <= high, each end named; a point value, a missing end or a reversed pair is
      refused (a HELD bound is never a point value, never 0);
  (e) A RESTATEMENT REPLACES ONLY ITS TARGET: a later report that splits an earlier report's row (T-550 on the T-543
      parapet residual) replaces that row only when its parts sum exactly to it; every other row stays byte-identical
      and the class totals move exactly by the restatement's own by-cause change (plus the listed (b) moves).
"""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T554 = ROOT / "research/agents_t554"
for p in (T554, ROOT / "research/agents_t548"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import statement_adapters as SA  # noqa: E402  (T-554, read only)

S = SA.S
A = SA.A
D = S.D

T545_JSON = ROOT / "research/agents_t545/out/T545_BEAM_RECONCILE.json"
T547_JSON = ROOT / "research/agents_t547/out/WALL_TILE_RECONCILE_T547.json"
T550_JSON = ROOT / "research/agents_t550/out/T550_UNRESOLVED_RESTATED.json"
T552_JSON = ROOT / "research/agents_t552/out/T552_PLASTER_RECONCILE.json"
T552_INPUTS = ROOT / "research/agents_t552/t552_inputs.py"

VERIF = ("CHECKER_CONFIRMED", "WORKER_PROPOSED")


class AdapterError(ValueError):
    pass


def require_range(b, what: str) -> tuple[Decimal, Decimal]:
    """R-T557-1 (d): a bound is a pair [low, high], both given, low <= high."""
    if not isinstance(b, (list, tuple)) or len(b) != 2:
        raise AdapterError(f"{what}: bound {b!r} is not a [low, high] pair (a HELD bound is never a point value)")
    if b[0] is None or b[1] is None:
        raise AdapterError(f"{what}: bound {b!r} has a missing end (unknown is never 0)")
    lo, hi = D(b[0], f"{what} low"), D(b[1], f"{what} high")
    if hi < lo:
        raise AdapterError(f"{what}: bound high {hi} < low {lo}")
    return lo, hi


def label(row: dict, verification: str, basis: str) -> dict:
    if verification not in VERIF:
        raise AdapterError(f"{row['name']}: verification {verification!r} not in {VERIF}")
    row["verification"] = verification
    row["verification_basis"] = basis
    return row


def _index_lines(index: dict, item_codes) -> dict:
    out = {"RELEASED": [], "HELD": [], "EXCLUDED": []}
    for ln in index.values():
        if ln["item_code"] in item_codes:
            out[ln["class"]].append(ln)
    for k in out:
        out[k].sort(key=lambda x: x["line_id"])
    return out


def _held_entry(ln: dict, reason: str) -> dict:
    lo, hi = ln.get("held_low"), ln.get("held_high")
    return {"line_id": ln["line_id"], "low": None if lo is None else S.s(D(lo)),
            "high": None if hi is None else S.s(D(hi)), "reason": reason}


# ============================================================================================ T-545 beams (m3) =====
T545_TRADE = "B10-07 beam concrete"
T545_VERDICT = ("Checker 2026-11-06 05:58 (T-545 Gate A): PARTIALLY VERIFIED; COUNT ENGINE_RIGHT by own B27 re-measure "
                "(4.1927 vs 4.1918 m3) and his rows read (no B27 / B28 / CA (GF), B25 / B19 / B5 (1F) row)")
T545_WORKER = "T-545 worker class (RUN_COUNT, THROUGH_SUPPORT, UNTRACED, HELD bounds not re-measured by the Checker)"
T545_STATUS = {"COUNT": "VALUED", "RUN_COUNT": "VALUED", "THROUGH_SUPPORT": "VALUED", "UNTRACED": "VALUED",
               "UPSTAND": "VALUED", "DOME_RING": "VALUED", "SECTION": "VALUED", "HELD": "HELD"}


def t545_section(index: dict, json_path: Path = T545_JSON) -> dict:
    return t545_from(json.loads(json_path.read_text(encoding="utf-8")), index)


def t545_from(d: dict, index: dict) -> dict:
    """Rows: floor x component (engine - his in the report; negated here). HELD rows name the floor's held lines that
    carry a share of his (R-T545-3 'INSIDE' / 'ABOVE'); every held line keeps its own index bound."""
    lines = _index_lines(index, {"STR.CONC.BEAM"})
    valued = [{"line_id": x["line_id"], "qty": S.s(D(x["measured_net"])), "unit": "m3"} for x in lines["RELEASED"]]
    if S.s(sum((D(x["qty"]) for x in valued), Decimal(0))) != S.s(D(d["engine"]["released_m3"])):
        raise AdapterError("T-545: index released beam total differs from the report")
    if len(valued) != d["engine"]["released_lines"] or len(lines["HELD"]) != d["engine"]["held_lines"]:
        raise AdapterError("T-545: line counts differ from the report")
    beside = {h["line_id"]: h for h in d["held_beside_his"]}
    for ln in lines["HELD"]:
        h = beside.get(ln["line_id"])
        if h is None:
            raise AdapterError(f"T-545: held line {ln['line_id']} not in the report's held table")
        for end, key in (("held_low", "engine_low_m3"), ("held_high", "engine_high_m3")):
            a, b = ln[end], h[key]
            if (a is None) != (b is None) or (a is not None and D(a) != D(b)):
                raise AdapterError(f"T-545: {ln['line_id']} {end} index {a} != report {b}")
    held = [_held_entry(ln, f"{beside[ln['line_id']]['class']}: {beside[ln['line_id']].get('reason') or ''}")
            for ln in lines["HELD"]]
    rows, zero = [], []
    for fl, fv in d["floors"].items():
        acc = Decimal(0)
        for comp, c in fv["components"].items():
            part = D(c["m3"])
            acc += part
            if part == 0:
                zero.append(f"{fl} {comp}")
                continue
            if comp not in T545_STATUS:
                raise AdapterError(f"T-545: component {comp!r} not in the adapter table")
            est = T545_STATUS[comp]
            ids = []
            note = ""
            if comp == "HELD":
                hs = [h for h in d["held_beside_his"] if h["floor"] == fl and h["his_share_m3"] not in (None, "0")]
                share = sum((D(h["his_share_m3"]) for h in hs), Decimal(0))
                if share != -part:
                    raise AdapterError(f"T-545 {fl}: his held share {share} != -HELD component {part}")
                ids = sorted(h["line_id"] for h in hs)
                above = [h["mark"] for h in hs if h["class"] == "ABOVE"]
                note = ("his share inside the HELD lines (R-T545-3); engine bounds per line beside"
                        + (f"; his share ABOVE the engine high on {', '.join(above)} (F-T545-1: bound on 1.500 vs "
                           "drawn 1.501 m)" if above else ""))
            if c["verdict"] not in S.CLASSES:
                raise AdapterError(f"T-545: verdict {c['verdict']!r} is not a class")
            row = {"name": f"{fl}: {comp}", "delta": S.s(-part), "class": c["verdict"], "source_cause": comp,
                   "engine_status": est, "held_line_ids": ids, "source": "T-545 floors table (R-T545-1)",
                   "note": note}
            label(row, "CHECKER_CONFIRMED" if comp == "COUNT" else "WORKER_PROPOSED",
                  T545_VERDICT if comp == "COUNT" else T545_WORKER)
            rows.append(row)
        if acc != D(fv["engine_m3"]) - D(fv["his_m3"]):
            raise AdapterError(f"T-545 {fl}: components {acc} != engine - his")
    return {
        "section_id": "T-545/beams", "report": "T-545", "trade": T545_TRADE, "item_codes": ["STR.CONC.BEAM"],
        "unit": "m3",
        "reference": {"kind": "FREELANCER", "total": d["total"]["his_m3"], "unit": "m3",
                      "basis": "freelancer concrete workbook, beam sheet: exact sum of his rows GF 42.882875 + 1F "
                               "17.155 + 2F 6.056 (Checker AGREE); his printed total 65.965875 leaves his first 1F row "
                               "out of the 1F sub-total (BM-ARITH -0.128, beside) (Drive 'Alsenan chalet project')"},
        "engine": {"valued_total": d["engine"]["released_m3"], "valued_lines": valued, "held_lines": held,
                   "excluded_lines": [{"line_id": x["line_id"]} for x in lines["EXCLUDED"]]},
        "rows": rows,
        "beside": {"his_printed_total_m3": d["total"]["his_printed_total_m3"],
                   "his_printed_minus_rows_m3": d["total"]["his_printed_minus_rows_m3 (BM-ARITH, his 1F sub-total "
                                                          "leaves his first 1F row out)"],
                   "zero_components_not_listed": zero,
                   "held_rollup": d["total"]["held_rollup"]},
    }


# ============================================================================================ T-547 wall tile (m2) ==
T547_TRADE = "B4 wet-room wall tile"
T547_VERDICT = ("Checker 2026-11-06 06:56 (T-547 Gate A) WHO IS RIGHT: height RULE_DIFFERENCE (Q-48 A), openings / open "
                "side / length ENGINE_RIGHT, pantry RULE_DIFFERENCE (Q-37 A), HELD bounded; FIN.WALL.TILE PARTIALLY "
                "VERIFIED (1F-08 own re-measure, 1 of 11 rooms)")


def t547_section(index: dict, json_path: Path = T547_JSON) -> dict:
    return t547_from(json.loads(json_path.read_text(encoding="utf-8")), index)


def t547_from(d: dict, index: dict) -> dict:
    valued, held, rows, beside = [], [], [], []
    lo_t, hi_t = Decimal(0), Decimal(0)
    for r in d["rows"]:
        if r["state"] in ("VALUED", "SCOPE"):
            valued.append({"line_id": r["line_id"], "qty": r["engine"], "unit": "m2"})
        elif r["state"] == "HELD":
            if r.get("engine") is not None:
                raise AdapterError(f"T-547 {r['room']}: HELD line carries a quantity (HELD is never 0)")
            ix = index.get(r["line_id"]) or {}
            held.append(_held_entry({"line_id": r["line_id"], "held_low": ix.get("held_low"),
                                     "held_high": ix.get("held_high")}, r["held_fact"]))
            b = r.get("bound") or {}
            lo, hi = require_range([b.get("lo"), b.get("hi")], f"T-547 {r['room']} drawing-derived bound")
            lo_t, hi_t = lo_t + lo, hi_t + hi
            beside.append({"line_id": r["line_id"], "room": r["room"], "drawing_derived_bound_m2": [S.s(lo), S.s(hi)],
                           "low_source": b.get("lo_source"), "high_source": b.get("hi_source")})
        else:
            raise AdapterError(f"T-547 {r['room']}: state {r['state']!r}")
        acc = Decimal(0)
        for c in r["components"]:
            part = D(c["delta"])
            acc += part
            est = "HELD" if r["state"] == "HELD" else "VALUED"
            row = {"name": f"{r['room']}: {c['name']}", "delta": S.s(-part), "class": c["cause"],
                   "source_cause": c["cause"], "engine_status": est,
                   "held_line_ids": [r["line_id"]] if est == "HELD" else [], "source": "T-547 room table (R-T547-1)",
                   "note": c.get("basis", "") if r["state"] != "HELD" else r["held_fact"]}
            rows.append(label(row, "CHECKER_CONFIRMED", T547_VERDICT))
        if acc != D(r["delta"]):
            raise AdapterError(f"T-547 {r['room']}: components {acc} != row delta {r['delta']}")
    if (S.s(lo_t), S.s(hi_t)) != (S.s(D(d["held_bound_total"]["lo"])), S.s(D(d["held_bound_total"]["hi"]))):
        raise AdapterError("T-547: held bound total differs from the report")
    return {
        "section_id": "T-547/wall-tile", "report": "T-547", "trade": T547_TRADE, "item_codes": ["FIN.WALL.TILE"],
        "unit": "m2",
        "reference": {"kind": "FREELANCER", "total": d["freelancer_total"], "unit": "m2",
                      "basis": "freelancer ceramic sheet, 17 room rows: lm 144.61 x his flat 3.00 = 433.83 (Checker "
                               "AGREE) (Drive 'Alsenan chalet project')"},
        "engine": {"valued_total": d["engine_total"], "valued_lines": valued, "held_lines": held,
                   "excluded_lines": []},
        "rows": rows,
        "beside": {"held_drawing_derived_bounds": beside,
                   "held_drawing_derived_total_m2": [S.s(lo_t), S.s(hi_t)],
                   "note": "drawing-derived bounds of the HELD lines (T-547, Checker AGREE on GF-02): NOT engine "
                           "bounds, never in the engine bounded range (R-T548-1 (f)); engine + these bounds = "
                           f"{d['engine_with_held_bounds']['lo']} .. {d['engine_with_held_bounds']['hi']} m2 "
                           f"({d['engine_with_held_bounds']['lo_pct']} .. {d['engine_with_held_bounds']['hi_pct']} % "
                           "over his), shown beside only"},
    }


# ============================================================================================ T-552 plaster (m2) ===
T552_TRADE = "B5 wall plaster"
T552_VERDICT = ("Checker 2026-11-06 05:58 (T-552 Gate A) WHO IS RIGHT: height basis ENGINE_WRONG (own check: every "
                "FIN.PLASTER room line = its FIN.PAINT line; GF-15 restated 68.7200 .. 70.8737 AGREE); lengths "
                "ENGINE_RIGHT on the verified rooms; returns -7.11 / shaft 54.00 / external 93.15 UNRESOLVED")
T552_WORKER = ("T-552 worker value (7 HELD dry rooms, T-173 shaft components, external T-337 faces not re-measured by "
               "the Checker)")
F_C_T552_1 = ("F-C-T552-1 (wording): his row 9 is 6.75 x 3.60 = 24.30; the report's '7.20 x 3.60' is the DRAWN face at his "
              "height; the -1.62 sits in the length row (the JSON closes; no number moves)")
# Checker-confirmed ENGINE_WRONG rows: (section, row-name prefix) -> fix row. R-T557-1 (c).
ENGINE_WRONG_CONFIRMED = {
    ("T-552/plaster-internal", "GF-15 height:"): "T-556",
    ("T-552/plaster-internal", "1F-01 height:"): "T-556",
    ("T-552/plaster-internal", "1F-04 height:"): "T-556",
    ("T-552/plaster-internal", "2F-03 height:"): "T-556",
}


def _reclass(row: dict, cls: str, est: str, ids: list, why: str, tag: str) -> None:
    """R-T557-1 (b): move a component to the class its engine side allows; the move rides on the row ('reclass')."""
    if row["class"] != cls:
        row["reclass"] = {"tag": tag, "from": row["class"], "to": cls, "delta": row["delta"], "why": why}
    row.update({"class": cls, "engine_status": est, "held_line_ids": ids})
    row["note"] = (row.get("note") or "") + ("; " if row.get("note") else "") + f"{tag}: {why}"


def _plaster_lines(index: dict) -> dict:
    inp = A._load_module(T552_INPUTS, "t557_t552_inputs")
    lines = [ln for ln in index.values() if ln["item_code"] == "FIN.PLASTER"]
    by10 = {ln["line_id"][:10]: ln for ln in lines}
    dry = {key: by10[lid] for key, _, (lid, _, _), *_ in inp.DRY}
    shaft = {el: by10[lid] for lid, el, _ in inp.SHAFT_LINES}
    ret = [ln for ln in lines if ("OPENING" in ln["element_id"] or "REVEAL" in ln["element_id"])]
    return {"inp": inp, "all": lines, "dry": dry, "shaft": shaft, "return": ret}


def t552_sections(index: dict, json_path: Path = T552_JSON) -> list[dict]:
    return t552_from(json.loads(json_path.read_text(encoding="utf-8")), index)


def t552_from(d: dict, index: dict, P: dict | None = None, ew_table: dict | None = None) -> list[dict]:
    """Pure adapter: a T-552-format report + the index + the plaster line split P (dry {room: line}, shaft {element:
    line}, return [lines], all [lines]) + the Checker ENGINE_WRONG table (any villa)."""
    P = _plaster_lines(index) if P is None else P
    ew_table = ENGINE_WRONG_CONFIRMED if ew_table is None else ew_table
    dry, shaft, ret = P["dry"], P["shaft"], P["return"]
    dry_ids = {ln["line_id"] for ln in dry.values()}
    # ---------------- internal: DRY + SHAFT + RETURN against his gross J27 ----------------
    valued = [{"line_id": ln["line_id"], "qty": S.s(D(ln["measured_net"])), "unit": "m2"}
              for ln in list(dry.values()) + ret if ln["class"] == "RELEASED"]
    held_lines = [ln for ln in list(dry.values()) + list(shaft.values()) + ret if ln["class"] == "HELD"]
    held = [_held_entry(ln, f"{ln['element_id']} HELD") for ln in held_lines]
    excluded = [{"line_id": ln["line_id"]} for ln in P["all"] if ln["class"] == "EXCLUDED"]
    v_total = sum((D(x["qty"]) for x in valued), Decimal(0))
    if S.s(v_total) != S.s(D(d["internal"]["engine_valued_dry_plus_returns"])):
        raise AdapterError(f"T-552: dry + return valued {v_total} != report")
    room_line = {}
    for r in d["internal"]["pairs"]["DRY"]["rooms"]:
        room_line[r["room"]] = r["line_id"]
    rows = []
    for r in d["internal"]["pairs"]["DRY"]["rows"]:
        room = r["name"].split()[0]
        lid = room_line.get(room)
        ln = index.get(lid) if lid else None
        row = {"name": r["name"], "delta": r["delta"], "class": r["cause"], "source_cause": r["cause"],
               "engine_status": "VALUED", "held_line_ids": [], "source": r["source"], "note": r.get("note", "")}
        if ln is None:                                   # GF-02: a wet space priced in his dry rows
            row["engine_status"] = "NONE"
            row["note"] = (row["note"] + "; " if row["note"] else "") + F_C_T552_1
            label(row, "CHECKER_CONFIRMED", T552_VERDICT + "; " + F_C_T552_1)
        elif ln["class"] == "HELD":
            if r["cause"] != "HELD":
                _reclass(row, "HELD", "HELD", [ln["line_id"]],
                         f"component on the HELD line {ln['line_id']} (R-T548-1 (e)); its height basis is also the "
                         "G1 paint height (ENGINE_WRONG basis, fix T-556)", "F-T557-1")
            else:
                row.update({"engine_status": "HELD", "held_line_ids": [ln["line_id"]]})
            label(row, "WORKER_PROPOSED", T552_WORKER)
        else:
            fix = [v for (sid, pre), v in ew_table.items()
                   if sid == "T-552/plaster-internal" and r["name"].startswith(pre)]
            if fix:
                row["fix_row"] = fix[0]
                _reclass(row, "ENGINE_WRONG", "VALUED", [],
                         f"the released line's height is the G1 paint height; Q-72 / owner 2026-11-02 takes plaster "
                         f"to the slab / roof underside: ENGINE_WRONG (Checker own check), fix row {fix[0]}; the "
                         "difference shown is against the WRONG engine height, the restated line is HELD (BOUNDED) "
                         "beside", "F-T557-2")
            label(row, "CHECKER_CONFIRMED", T552_VERDICT)
        rows.append(row)
    sh_ids = sorted(ln["line_id"] for ln in shaft.values())
    for r in d["internal"]["pairs"]["SHAFT"]["rows"]:
        row = {"name": f"SHAFT: {r['name']}", "delta": r["delta"], "class": r["cause"], "source_cause": r["cause"],
               "engine_status": "HELD", "held_line_ids": sh_ids, "source": r["source"], "note": r.get("note", "")}
        if r["cause"] == "UNRESOLVED":
            row.update({"engine_status": "NONE", "held_line_ids": []})
            label(row, "CHECKER_CONFIRMED", T552_VERDICT + " (his rows 24 / 8 read: 13.50 + 40.50)")
        else:
            if r["cause"] != "HELD":
                _reclass(row, "HELD", "HELD", sh_ids, "his shaft box vs the drawing (T-173) on the 3 HELD shaft "
                         "lines: the engine values no shaft face (R-T548-1 (e))", "F-T557-3")
            label(row, "WORKER_PROPOSED", T552_WORKER)
        rows.append(row)
    for r in d["internal"]["pairs"]["RETURN"]["rows"]:
        rows.append(label({"name": r["name"], "delta": r["delta"], "class": r["cause"], "source_cause": r["cause"],
                           "engine_status": "VALUED", "held_line_ids": [], "source": r["source"],
                           "note": "his 14 doors x 0.20 x 5.70 not listed by id; 4 return lines HELD outside the "
                                   "row (never 0)"}, "CHECKER_CONFIRMED", T552_VERDICT))
    # restated ENGINE_WRONG lines beside (R-T557-1 (c), (d))
    restated, rel_lo, rel_hi, all_lo, all_hi = [], Decimal(0), Decimal(0), Decimal(0), Decimal(0)
    q72 = d["q72_dry_plaster_height"]
    for q in q72["rows"]:
        if q["line_id"] not in dry_ids:
            raise AdapterError(f"T-552 q72: {q['line_id']} is not a dry plaster line")
        lo, hi = require_range(q["corrected_net"], f"T-552 restated {q['room']}")
        mlo, mhi = require_range(q["missing_m2"], f"T-552 missing {q['room']}")
        all_lo, all_hi = all_lo + mlo, all_hi + mhi
        ent = {"line_id": q["line_id"], "room": q["room"], "candidate_class": index[q["line_id"]]["class"],
               "candidate_m2": None if index[q["line_id"]]["measured_net"] is None
               else S.s(D(index[q["line_id"]]["measured_net"])),
               "restated_HELD_BOUNDED_m2": [S.s(lo), S.s(hi)], "plaster_height_m": q["plaster_height"],
               "status": q["status"], "beam_end_sections_held": q["beam_end_sections_held"]}
        if ent["candidate_class"] == "RELEASED":
            if D(ent["candidate_m2"]) + mlo != lo or D(ent["candidate_m2"]) + mhi != hi:
                raise AdapterError(f"T-552 q72 {q['room']}: candidate + missing != restated")
            rel_lo, rel_hi = rel_lo + lo, rel_hi + hi
        restated.append(ent)
    if [S.s(all_lo), S.s(all_hi)] != [S.s(D(x)) for x in q72["missing_total"]]:
        raise AdapterError("T-552 q72: missing total differs from the report")
    rel_now = sum((D(e["candidate_m2"]) for e in restated if e["candidate_class"] == "RELEASED"), Decimal(0))
    internal = {
        "section_id": "T-552/plaster-internal", "report": "T-552", "trade": T552_TRADE, "item_codes": ["FIN.PLASTER"],
        "unit": "m2",
        "reference": {"kind": "FREELANCER", "total": d["internal"]["freelancer_gross"], "unit": "m2",
                      "basis": "freelancer plaster workbook, internal statement rows 4-26 gross J27 1,209.385 (Checker "
                               "AGREE: 452.88 + 441.265 + 94.86 + 204.42 + 15.96); dry rooms 948.505 + shaft 244.92 + "
                               "returns 15.96; his net 1,151.1375 (half of his opening list, his own step) beside "
                               "(Drive 'Alsenan chalet project')"},
        "engine": {"valued_total": S.s(v_total), "valued_lines": valued, "held_lines": held,
                   "excluded_lines": excluded},
        "rows": rows,
        "beside": {
            "his_net_m2": d["internal"]["freelancer_net"], "his_half_deduction_m2": d["internal"]["his_half_deduction"],
            "engine_bounded_note": "the engine bounded low adds the candidate's own held bounds; on the 5 bounded dry "
                                   "room lines those bounds are at the G1 paint height (the ENGINE_WRONG basis), so "
                                   "the low end is itself under the Q-72 restatement (T-556)",
            "net_view_difference_m2": d["internal"]["gap_net"],
            "wet_render_not_here": f"WET render lines ({d['internal']['WET']['valued_m2']} m2 valued) are the tiler's "
                                   "levelling render: owned by T-547 (tile faces) / T-317 / T-349 (spatter), never "
                                   "reconciled against his dry plaster",
            "engine_wrong_restated": {
                "verdict": q72["verdict"], "rule": q72["rule"], "fix_row": "T-556",
                "released_lines_now_m2": S.s(rel_now),
                "released_lines_restated_HELD_BOUNDED_m2": [S.s(rel_lo), S.s(rel_hi)],
                "all_11_dry_lines_missing_m2": [S.s(all_lo), S.s(all_hi)],
                "lines": restated,
                "note": "the restated quantity is HELD (BOUNDED on the floor build-up b, D-39 under roofs): never "
                        "added to the engine valued or bounded columns, never agreement"}},
    }
    # ---------------- external: his gross J93 against FIN.EXT.FINISH / ARCH.FACADE / EXT.FENCE.PLASTER held ------
    ext_codes = ["FIN.EXT.FINISH", "ARCH.FACADE", "EXT.FENCE.PLASTER"]
    el = _index_lines(index, set(ext_codes))
    if el["RELEASED"]:
        raise AdapterError("T-552 external: a valued external finish line exists; the report says engine 0")
    facade = sorted(x["line_id"] for x in el["HELD"] if x["item_code"] in ("FIN.EXT.FINISH", "ARCH.FACADE"))
    fence = sorted(x["line_id"] for x in el["HELD"] if x["item_code"] == "EXT.FENCE.PLASTER")
    lo_rows, hi_rows = d["external"]["bridge_lo"]["rows"], d["external"]["bridge_hi"]["rows"]
    if [r["name"] for r in lo_rows] != [r["name"] for r in hi_rows]:
        raise AdapterError("T-552 external: the two bridges list different rows")
    erows, i = [], 0
    while i < len(lo_rows):
        r, rh = lo_rows[i], hi_rows[i]
        nm = r["name"]
        if ": drawn faces (" in nm:
            nxt, nxth = lo_rows[i + 1], hi_rows[i + 1]
            key = nm.split(":")[0]
            if not nxt["name"].startswith(key + " vs the drawn faces"):
                raise AdapterError(f"T-552 external: {nm!r} has no 'vs the drawn faces' row")
            tot_lo, tot_hi = D(r["delta"]) + D(nxt["delta"]), D(rh["delta"]) + D(nxth["delta"])
            if tot_lo != tot_hi:
                raise AdapterError(f"T-552 external {key}: the two bridges differ in the row total")
            face = require_range(sorted([D(r["delta"]), D(rh["delta"])]), f"T-552 external {key} drawn faces")
            row = {"name": f"{key}: drawn faces + his vs the drawn faces", "delta": S.s(tot_lo), "class": "HELD",
                   "source_cause": f"HELD + {nxt['cause']}", "engine_status": "HELD", "held_line_ids": facade,
                   "source": r["source"],
                   "note": f"drawn faces {S.s(face[0])} .. {S.s(face[1])} m2 (T-337 / T-159, not in the candidate: "
                           f"T-314) + his vs drawn {nxt['cause']}; the split is a range, the row total is exact in "
                           "both bridges"}
            if nxt["cause"] != "HELD":
                row["reclass"] = {"tag": "F-T557-4", "from": nxt["cause"], "to": "HELD", "delta": nxt["delta"],
                                  "delta_bridge_hi": nxth["delta"],
                                  "why": "his row vs the drawn faces on HELD facade lines (R-T548-1 (e)); merged "
                                         "with its drawn-face row so no bridge is picked"}
            erows.append(label(row, "WORKER_PROPOSED", T552_WORKER))
            i += 2
            continue
        if r["delta"] != rh["delta"] or r["cause"] != rh["cause"]:
            raise AdapterError(f"T-552 external {nm}: bridges differ")
        row = {"name": nm, "delta": r["delta"], "class": r["cause"], "source_cause": r["cause"],
               "engine_status": "NONE", "held_line_ids": [], "source": r["source"], "note": r.get("note", "")}
        if r["cause"] == "HELD":
            if "HELD_Q-65" in nm:
                row.update({"engine_status": "HELD", "held_line_ids": fence})
                row["note"] = "owner Q-65 C: the boundary wall is another trade; its plaster lines EXT.FENCE.PLASTER " \
                              "(8, HELD blank) hold it"
            else:
                why = ("frame bands: the T-337 register family FIN.EXT.FRAME has no candidate line"
                       if "NOT_IN_T159" in nm else
                       "drip edge: FIN.EXT.DRIP (owner note item 3 unanswered) has no candidate line")
                _reclass(row, "UNRESOLVED", "NONE", [], why + " (R-T554-1 (d): no line is never HELD)", "F-T557-5")
        elif "pool-court soffit" in nm:
            row["note"] = "the engine's CEILING line L-23072352a28aeca7b051 (FIN.CEILING, another family) holds it"
        erows.append(label(row, "CHECKER_CONFIRMED" if r["cause"] == "UNRESOLVED" else "WORKER_PROPOSED",
                           T552_VERDICT if r["cause"] == "UNRESOLVED" else T552_WORKER))
        i += 1
    external = {
        "section_id": "T-552/plaster-external", "report": "T-552", "trade": T552_TRADE + " external",
        "item_codes": ext_codes, "unit": "m2",
        "reference": {"kind": "FREELANCER", "total": d["external"]["freelancer_gross"], "unit": "m2",
                      "basis": "freelancer plaster workbook, external + Sigma rows 51-92 gross J93 1,502.84 (Checker "
                               "AGREE); his net 1,469.9675 (half of J97 65.745) beside (Drive 'Alsenan chalet "
                               "project')"},
        "engine": {"valued_total": "0", "valued_lines": [],
                   "held_lines": [_held_entry(x, f"{x['item_code']} {x['element_id']} HELD blank") for x in el["HELD"]],
                   "excluded_lines": []},
        "rows": erows,
        "beside": {"his_net_m2": d["external"]["freelancer_net"],
                   "his_half_deduction_m2": d["external"]["his_half_deduction"],
                   "note": "no external finish line is valued in the candidate (T-314): the whole difference is in "
                           "the reference only; ENGINE_RIGHT of the report (his lengths vs the DRAWING) is shown "
                           "inside HELD rows, never as engine agreement"},
    }
    return [internal, external]


# ============================================================================================ T-550 on T-543 ========
T550_VERDICT = ("Checker 2026-11-06 08:05 (T-550 Gate A): H1 MEASURED confirmed (own P7757.dxf read, 0 mm); "
                "below-finish 68.4188 m2 ENGINE_RIGHT by own geometry; +13.90 0.75 RULE_DIFFERENCE; projections "
                "41.25 element not found (own DIMENSION scan)")
T550_WORKER = "T-550 worker class (1F per-run printed heights 7.6307 and the held runs -1.29 not re-measured)"
F_C_T550_1 = ("F-C-T550-1 (wording): the class rests on GEOMETRY, not the hatch (the hatch covers the part above the "
              "finish the same way): a 0.20 member running 0.35 below the slab soffit at the slab edge is a downstand "
              "edge beam, so masonry ends at its soffit: ENGINE_RIGHT for the blockwork line; NOT checked: that a "
              "released beam line carries that edge downstand (if none does it is a concrete scope gap, never "
              "blockwork; Lead to name the owning beam ids)")
T543_PARAPET_RESIDUAL = "parapets: RESIDUAL: parapet height below the finished roof"


def t550_restate(sec: dict, d: dict, parapet_ids: list[str]) -> dict:
    """R-T557-1 (e): replace the T-543 parapet residual row by the T-550 parts (exact), annotate the rows T-550 names."""
    sec = copy.deepcopy(sec)
    hits = [i for i, r in enumerate(sec["rows"]) if r["name"].startswith(T543_PARAPET_RESIDUAL)]
    if len(hits) != 1:
        raise AdapterError(f"T-550: target row found {len(hits)} times")
    i = hits[0]
    old = sec["rows"][i]
    if D(old["delta"]) != D(d["parapet_residual_t543"]) or old["class"] != "UNRESOLVED":
        raise AdapterError(f"T-550: target row is {old['class']} {old['delta']}, T-550 restates "
                           f"{d['parapet_residual_t543']}")
    new = []
    for ch in d["parapet_split"]:
        acc = Decimal(0)
        for r in ch["rows"]:
            part = D(r["delta"])
            acc += part
            if part == 0:
                continue
            nm = r["name"]
            row = {"name": f"parapets: {nm}", "delta": S.s(part), "class": r["cause"], "source_cause": r["cause"],
                   "engine_status": "HELD", "held_line_ids": list(parapet_ids), "source": "T-550 parapet split "
                   "(R-T550-1)", "note": r["basis"], "correction": "T-550"}
            if "below the finished roof" in nm:          # concrete below finish: no masonry by scope
                row.update({"engine_status": "NONE", "held_line_ids": [],
                            "note": f"{F_C_T550_1}; source basis (T-550): {r['basis']}"})
                label(row, "CHECKER_CONFIRMED", T550_VERDICT)
            elif r["cause"] == "UNRESOLVED":
                label(row, "CHECKER_CONFIRMED", T550_VERDICT + "; length census stays UNRESOLVED (named)")
            elif r["cause"] == "RULE_DIFFERENCE":
                _reclass(row, "HELD", "HELD", list(parapet_ids),
                         "length convention (his outer dimensions vs the engine centreline) on the parapet face whose "
                         "block alternative is HELD (material Q-65 C) with STR.CONC.PARAPET (R-T548-1 (e), as "
                         "F-T554-2); RULE_DIFFERENCE once the material is decided", "F-T557-6")
                label(row, "CHECKER_CONFIRMED", T550_VERDICT + " (cause confirmed; class HELD on the engine side)")
            else:
                if r["cause"] != "HELD":
                    _reclass(row, "HELD", "HELD", list(parapet_ids),
                             "his flat height vs each run's printed height on the parapet face above the upstand, "
                             "whose block alternative is HELD (material Q-65 C) with STR.CONC.PARAPET (R-T548-1 (e)); "
                             "ENGINE_RIGHT on the geometry once the material is decided", "F-T557-6")
                label(row, "WORKER_PROPOSED", T550_WORKER)
            new.append(row)
        if acc != D(ch["difference_m2"]):
            raise AdapterError(f"T-550 {ch['chain']}: parts {acc} != chain difference {ch['difference_m2']}")
    if sum((D(r["delta"]) for r in new), Decimal(0)) != D(old["delta"]):
        raise AdapterError("T-550: parts do not sum to the replaced row")
    sec["rows"][i:i + 1] = new
    for r in sec["rows"]:
        if r["name"].startswith("1F 'projections' row"):
            r["note"] = f"T-550: {d['projections_note']}"
            label(r, "CHECKER_CONFIRMED", T550_VERDICT)
        elif r["name"].startswith("his 20 cm openings with no floor") or "openings census" in r["name"]:
            r["note"] = (r.get("note") or "") + f"; T-550 openings (rows l + his 20 cm): {d['openings_note']}"
        elif r["name"].startswith("parapets: RC upstand 0.30 m above the slab"):
            r["note"] = (r.get("note") or "") + ("; H1 MEASURED by T-550 (Checker 08:05, own P7757.dxf read, 0 mm): his "
                                                 "base is the edge-member soffit 0.55 below the finish, so the whole "
                                                 "upstand lies inside his face; the alternative 'his base is the "
                                                 "finish' does not arise")
            r["h1_status"] = "MEASURED (T-550)"
    return sec


def t550_expected_by_class(t554_by_class: dict, d: dict, restated_rows: list[dict]) -> dict:
    """Class totals after the restatement: T-554 + (T-550 restated - T-543) per class + the F-T557-6 moves."""
    out = {c: D(t554_by_class.get(c, "0")) for c in S.CLASSES}
    for c in S.CLASSES:
        out[c] += D(d["restated_by_cause"].get(c, "0")) - D(d["t543_by_cause"].get(c, "0"))
    for r in restated_rows:
        m = r.get("reclass")
        if m and m["tag"] == "F-T557-6":
            out[m["from"]] -= D(m["delta"])
            out[m["to"]] += D(m["delta"])
    return {c: S.s(v) for c, v in out.items()}


# ============================================================================================ guards ==============
def verify_engine_wrong(st: dict, table: dict = ENGINE_WRONG_CONFIRMED) -> None:
    """R-T557-1 (c): a Checker-confirmed ENGINE_WRONG row is in the ENGINE_WRONG column with its fix row."""
    secs = {c["section_id"]: c for c in st["sections"]}
    for (sid, pre), fix in table.items():
        sec = secs.get(sid)
        if sec is None:
            raise AdapterError(f"ENGINE_WRONG {pre}: section {sid} missing")
        rows = [r for r in sec["rows"] if r["name"].startswith(pre)]
        if len(rows) != 1:
            raise AdapterError(f"ENGINE_WRONG {pre}: found {len(rows)} rows in {sid}")
        if rows[0]["class"] != "ENGINE_WRONG":
            raise AdapterError(f"ENGINE_WRONG {pre} in {sid} is classed {rows[0]['class']}: an engine error never "
                               "lands in an agreement column")
        if rows[0].get("fix_row") != fix:
            raise AdapterError(f"ENGINE_WRONG {pre}: fix row {rows[0].get('fix_row')} != {fix}")


def verify_labels(st: dict, sections: tuple = ("T-545/beams", "T-547/wall-tile", "T-552/plaster-internal",
                                               "T-552/plaster-external")) -> None:
    for c in st["sections"]:
        if c["section_id"] in sections:
            for r in c["rows"]:
                if r.get("verification") not in VERIF:
                    raise AdapterError(f"{c['section_id']} / {r['name']}: no verification label")
