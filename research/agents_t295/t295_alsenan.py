"""T-295 Alsenan (development villa) CEILING FACE-TO-LINE LEDGER: every face of the merged ceiling ledgers (T-283 r3
decor + owner bulkheads + held pieces + domes, T-271 r2b VOID, T-281 stair soffits) against the ARCH_TAKEOFF_V3.0.15
candidate's ceiling line ids (= the T-245 V3.0.16 lines, byte-identical), with each face's status and the line's own
state carried. Research only: no engine module, candidate line or released line changes; lane I (T-284) applies it.

    python3 -I research/agents_t295/t295_alsenan.py --extract <run>/v3015   # writes CANDIDATE_V3015_CEILING_LINES.json
    python3 -I research/agents_t295/t295_alsenan.py --write                 # writes the ledger files
    python3 -I research/agents_t295/t295_alsenan.py --check                 # rebuilds in memory, compares bytes

Inputs (committed): research/agents_t283/CEILING_LEDGER_R3_EXPORT.json (39 pieces), research/agents_t281/LEDGER_T281.csv
+ summary.json (stair soffit rows and the zone reconciliations), CANDIDATE_V3015_CEILING_LINES.json (line id, item code,
room / element id, unit, state, quantity, gross, deductions, RFI text; no coordinates, no names) and the Checker's
one-owner rulings of the T-281 / T-283 batch (Verifier 2026-10-25 05:32 / 05:34, BOARD rows T-281 / T-283), cited below.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import ceiling_line_ledger as R  # noqa: E402

T283 = ROOT / "research" / "agents_t283" / "CEILING_LEDGER_R3_EXPORT.json"
T281 = ROOT / "research" / "agents_t281" / "LEDGER_T281.csv"
T281S = ROOT / "research" / "agents_t281" / "summary.json"
CANDIDATE = HERE / "CANDIDATE_V3015_CEILING_LINES.json"
SCHEMA = "T295_CEILING_FACE_TO_LINE_LEDGER_V1"
SCOPE_ITEMS = ("FIN.CEILING",)              # the candidate's ceiling line family
LISTED_ITEMS = ("FIN.STAIR.FLIGHT", "STR.CONC.STAIR", "STR.CONC.DOME")  # read to prove no soffit / dome finish line

CHK = "Checker T-281 / T-283 batch, Verifier 2026-10-25 05:32 / 05:34 (BOARD rows T-281, T-283)"
SRC283 = "T-283 r3 MERGED 6e141df6 (CEILING_LEDGER_R3_EXPORT.json)"
SRC281 = "T-281 MERGED 40518c58 (LEDGER_T281.csv)"
SRC271 = "T-271 r2b MERGED 789ebbb4"
OWNER_BULKHEAD = "owner Q-48 A + Q-43 (bulkhead faces, owner method, decor side only R-CEIL-R3-2)"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# --- candidate lines -----------------------------------------------------------------------------------------
def extract(run_dir):
    run = Path(run_dir)
    src = run / "V3_0_15_BOQ_LINES.json"
    d = json.loads(src.read_text(encoding="utf-8"))
    L = d if isinstance(d, list) else d["lines"]
    keep = []
    for l in L:
        if l["item_code"] not in SCOPE_ITEMS + LISTED_ITEMS:
            continue
        c = l.get("calculation") or {}
        loc = l.get("location") or {}
        keep.append({"line_id": l["line_id"], "item_code": l["item_code"], "trade": l.get("trade"),
                     "floor": loc.get("floor"), "room_id": loc.get("room_id"), "element_id": loc.get("element_id"),
                     "unit": l["unit"], "evidence_state": l["evidence_state"], "measured_net": l.get("measured_net"),
                     "gross": l.get("gross"), "bounded_range": l.get("bounded_range"),
                     "deductions": [{"m2": x.get("m2"), "what": x.get("what")} for x in (l.get("deductions") or [])],
                     "formula": c.get("formula"), "ceiling_type": (c.get("inputs") or {}).get("ceiling_type"),
                     "rfi_question": (l.get("rfi") or {}).get("question"),
                     "project_id": (l.get("project") or {}).get("project_id"),
                     "revision_set_sha256": (l.get("project") or {}).get("revision_set_sha256")})
    keep.sort(key=lambda x: (x["item_code"], x["floor"] or "", x["element_id"] or "", x["line_id"]))
    csv_p = run / "V3_0_15_BOQ_LINES.csv"
    out = {"task": "T-295", "candidate": "ARCH_TAKEOFF_V3.0.15",
           "candidate_lines_json_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
           "candidate_lines_csv_sha256": hashlib.sha256(csv_p.read_bytes()).hexdigest() if csv_p.exists() else None,
           "lines_total": len(L), "lines": keep}
    CANDIDATE.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def candidate():
    return json.loads(CANDIDATE.read_text(encoding="utf-8"))


# --- faces ---------------------------------------------------------------------------------------------------
def _st(s):
    return R.AOA if s.startswith("ASSUMED") else s


def _face(fid, piece, room, floor, owner, plan, status, source, carried="plan", held_item=None, **kw):
    f = {"face_id": fid, "physical_id": kw.pop("physical_id", fid), "piece": piece, "room_id": room, "floor": floor,
         "owner": owner, "unit": "m2", "plan_m2": None if plan is None else round(plan, 6), "status": status,
         "source": source, "held_item": held_item, "verified_by": None, "range": None, "alternative_of": None,
         "plan_status": None, "basis": "plan area", "note": None}
    f.update(kw)
    if status in R.DETERMINATE:
        f["carried"] = f["plan_m2"] if carried == "plan" else round(carried, 6)
    else:
        f["carried"] = None
    return f


def t281_rows():
    return {r["id"]: r for r in csv.DictReader(io.StringIO(T281.read_text(encoding="utf-8")))}


def _num(v):
    return None if v in (None, "") else float(v)


def _soffit_face(fid_prefix, row, piece, room, floor, plan_override=None, note=None):
    """one T-281 stair soffit piece as a ceiling-ledger face: its PLAN (the piece) and, as the soffit quantity, the
    true area only where both methods agree (O = D) and it is measured; otherwise HELD with both readings (no owner
    soffit rule: method O vs D is a RULE_DIFFERENCE, T-281 s.4) or HELD by its own T-281 hold."""
    plan = plan_override if plan_override is not None else _num(row["plan_O"])
    tO, tD = _num(row["true_O"]), _num(row["true_D"])
    pst = _st(row["status"]) if row["status"] in (R.DC, ) or row["status"].startswith("ASSUMED") else row["status"]
    if row["status"].startswith("CONFLICT"):
        pst = "CONFLICT (C-ST-4)"
    kw = dict(plan_status=pst, basis="plan = the piece; carried = true soffit area along the pitch", note=note)
    if tO is not None and tD is not None and abs(tO - tD) <= 1e-9 and row["status"] in (R.DC,):
        return _face(f"{fid_prefix}{row['id']}", piece, room, floor, R.STAIR_SOFFIT, plan, R.DC, SRC281,
                     carried=tO, **kw)
    if tO is not None and tD is not None:
        return _face(f"{fid_prefix}{row['id']}", piece, room, floor, R.STAIR_SOFFIT, plan, R.HELD, SRC281,
                     held_item="stair soffit true area: method O vs D RULE_DIFFERENCE (no owner soffit rule)",
                     range=(round(min(tO, tD), 6), round(max(tO, tD), 6)), **kw)
    return _face(f"{fid_prefix}{row['id']}", piece, room, floor, R.STAIR_SOFFIT, plan, R.HELD, SRC281,
                 held_item="stair soffit true area HELD in T-281: " + (row["held"] or row["status"])[:120], **kw)


def faces():
    ex = json.loads(T283.read_text(encoding="utf-8"))
    t81 = t281_rows()
    out, edges, alts, pieces = [], [], [], {}
    for rec in ex["records"]:
        pid, room, fl = rec["face_id"], rec["supersedes_engine"]["room_id"], rec["floor"]
        pieces[pid] = (rec["floor_piece_m2"], None)
        for s in rec["surfaces"]:
            name, q, unit, st = s["surface"], s["qty"], s["unit"], _st(s["status"])
            low = name.lower()
            if unit != "m2" or low.startswith("paintable") or low.startswith("ceiling board type") \
                    or low.startswith("concrete ceiling plaster") or low.startswith("beam / column junction"):
                if unit in ("m", "nr"):
                    edges.append({"piece": pid, "room_id": room, "item": name, "unit": unit, "qty": q,
                                  "status": st, "basis": s["basis"], "candidate_line": None,
                                  "reason": "the candidate measures no ceiling edge, cove or junction (no line)"})
                continue
            if low.startswith("bulkhead vertical faces, drawing-derived"):
                alts.append({"piece": pid, "room_id": room, "item": name, "unit": unit, "qty": q, "status": st,
                             "basis": s["basis"], "rule": "D-40: drawing-derived candidate, never in a total; the "
                                                          "owner method is the carried bulkhead"})
                continue
            if low.startswith("horizontal decor"):
                out.append(_face(f"{pid}|decor", pid, room, fl, R.DECOR, q, st, SRC283))
            elif low.startswith("bulkhead vertical faces, owner"):
                out.append(_face(f"{pid}|bulkhead", None, room, fl, R.BULKHEAD, q, st, OWNER_BULKHEAD,
                                 basis="vertical face (not a plan piece)"))
            elif low.startswith("no ceiling"):
                out.append(_face(f"{pid}|void", pid, room, fl, R.VOID, q, st, SRC283 + "; " + SRC271
                                 if "opening in the slab" in low else SRC283, note=name))
            elif low.startswith("under an open dome"):
                out.append(_face(f"{pid}|dome", pid, room, fl, R.DOME, q, R.HELD, SRC283,
                                 held_item="open dome position (Q-44 A; designer DCR-4: what closes the opening)"))
            elif low.startswith("held part of the ceiling"):
                out.append(_face(f"{pid}|held-part", pid, room, fl, R.HELD_CEILING, q, R.HELD, SRC283,
                                 held_item="2F stair box top 12.974 (Q-72 investigation, T-271)"))
            elif low.startswith("plan area under the slab, ceiling type"):
                out.append(_face(f"{pid}|class-held", pid, room, fl, R.HELD_CEILING, q, R.HELD, SRC283,
                                 held_item="ceiling type not decidable (class HELD, P-2)"))
            elif low.startswith("shaft top under the slab") or low.startswith("stair top under the slab"):
                out.append(_face(f"{pid}|top", pid, room, fl, R.STAIR_TOP, q, R.HELD, SRC283,
                                 held_item=name.split(" (")[0] + " (landing / shaft top, owner trade not decided)"))
            elif low.startswith("stair soffit over the flights"):
                # GF stair room GF-R31F8AE: slab-plan face GF-025 = the ST-01 MS1 pieces (T-281 reconciliation)
                for rid in ("ST01-MS1-U", "ST01-MS1-LD", "ST01-MS1-T"):
                    out.append(_soffit_face("", t81[rid], pid, room, fl))
                out.append(_ms1l(t81["ST01-MS1-L"], pid, room, fl))
                out.append(_face("ST01-WELL-GF", pid, room, fl, R.VOID, _num(t81["ST01-WELL-GF"]["plan_O"]), R.DC,
                                 SRC281, note="stair well GF -> 1F (open to above): no ceiling, no soffit"))
            elif low.startswith("stair zone (stair face") and fl == "1F":
                # 1F living: slab-plan face 1F-016 = the ST-01 MS2 pieces (T-281 reconciliation, residual 0)
                for rid in ("ST01-MS2-L", "ST01-MS2-U", "ST01-MS2-LD-W", "ST01-MS2-LD-E", "ST01-MS2-TR"):
                    out.append(_soffit_face("", t81[rid], pid, room, fl))
                out.append(_face("ST01-WELL-1F", pid, room, fl, R.VOID, _num(t81["ST01-WELL-1F"]["plan_O"]), R.DC,
                                 SRC281, note="stair well 1F -> 2F (open to above): no ceiling, no soffit"))
            elif low.startswith("stair zone (stair face") and fl == "GF":
                out.extend(_gf_stair_zone(pid, room, fl, q))
            elif low.startswith("stair zone beyond") and fl == "GF":
                out.append(_face(f"{pid}|beyond", pid, room, fl, R.STAIR_SOFFIT, q, R.HELD, SRC283 + "; " + CHK,
                                 held_item="ST-02 flight under band 'B3 (With Stair)' / CA BM-GF-039 (GF-159, GF-144, "
                                           "GF-158, GF-143, GF-161): carried ONCE in the stair-soffit HELD rows "
                                           "(Checker); decor vs soffit RULE_DIFFERENCE pending the height test",
                                 plan_status=R.DC))
                alts.append({"piece": pid, "room_id": room, "item": "T-281 member rows under the ST-02 lanes "
                             "(B3 band RS-S 1.100 + RS-LD 0.275625, CA 0.345, column 380 0.040)", "unit": "m2",
                             "qty": 1.760625, "status": R.HELD, "basis": SRC281,
                             "rule": f"the SAME plan area as {pid}|beyond 1.7719 (Checker: carried once); "
                                     "difference 0.011275 m2 = the two ledgers' piece sets (T-283 slab-plan pieces "
                                     "vs T-281 member outlines; column 380 0.040 vs GF-156 0.036), not summed"})
            elif low.startswith("stair zone beyond") and fl == "1F":
                out.append(_face(f"{pid}|b23-foot", pid, room, fl, R.HELD_CEILING, q, R.HELD, SRC283 + "; " + CHK,
                                 held_item="B23 underside over the MS2-L foot (ceiling trade, shaft finish "
                                           "undecided; Checker: not a stair soffit)", plan_status=R.DC))
            else:
                raise R.LedgerError(f"UNMAPPED_SURFACE: {pid} {name!r}")
    out.extend(_domes_outside(ex))
    return out, edges, alts, pieces


def _ms1l(row, piece, room, fl):
    """MS1-L lower flight, CONFLICT C-ST-4 (designer): the lane inside face GF-025 is 3.755 m2 (T-281 reconciliation);
    reading B (structural) = soffit over all of it, reading A (architectural) = 3.215 soffit + 0.540 open to the shaft.
    Plan carried as the piece; the soffit quantity is HELD with both readings (true area, both methods)."""
    s = json.loads(T281S.read_text(encoding="utf-8"))["MS1-L CONFLICT"]
    lo = min(s["A_architectural"]["true_O"], s["A_architectural"]["true_D"])
    hi = max(s["B_structural"]["true_O"], s["B_structural"]["true_D"])
    return _face(row["id"], piece, room, fl, R.STAIR_SOFFIT, 3.755, R.HELD, SRC281,
                 held_item="CONFLICT C-ST-4 (designer): structural 12 riser lines vs architectural 10; soffit plan "
                           "3.215 (A, + 0.540 open to the shaft) .. 3.755 in the face (B, + 0.180 under B20 outside "
                           "it)", range=(round(lo, 6), round(hi, 6)), plan_status="CONFLICT (C-ST-4)",
                 basis="plan = the lane inside face GF-025; range = true soffit area, readings A .. B, methods O / D")


def _gf_stair_zone(pid, room, fl, q):
    """GF open piece stair zone 9.8536 (T-283 = T-271 9.853618) split by T-281's reconciliation 'T271-GF' and the
    Checker's rulings: ST-02 soffit pieces inside the T-271 stair faces 9.013781 (stair soffit, HELD: RS-C curved true
    area HELD, hidden pairs UNKNOWN, the per-row split inside the faces is not decomposed by T-281), the slab north of
    the top riser 315 0.777392 (DECOR: Checker 'T-281 RIGHT', 1F arrival slab), the bottom-step strip inside the
    light-well outline 0.062506 (VOID), residual -0.000061 named (T-271 arcs 1024 segments vs 2048 in T-281)."""
    rec = json.loads(T281S.read_text(encoding="utf-8"))["reconciliation"]["T271-GF"]
    st02 = rec["ST-02 pieces inside the T-271 stair faces"]
    slab = rec["slab north of the top riser 315 (GF-131 / GF-132 parts; plate C-T1)"]
    strip = rec["bottom-step strip inside the light-well outline (no soffit: no ceiling)"]
    return [
        _face(f"{pid}|st02-soffit", pid, room, fl, R.STAIR_SOFFIT, st02, R.HELD, SRC281 + " reconciliation T271-GF",
              held_item="ST-02 soffit pieces (RS-S, RS-A, RS-LD, RS-C) inside the T-271 stair faces: RS-C helicoid true "
                        "area HELD (C-ST-3), hidden pairs 535/536 + 2CC/2CD UNKNOWN, O vs D RULE_DIFFERENCE",
              plan_status=R.DC),
        _face(f"{pid}|slab-n315", pid, room, fl, R.DECOR, slab, R.DC, SRC281 + "; " + CHK,
              note="slab north of the top riser 315: decor ceiling (Checker: T-281 RIGHT); not in T-283's 91.4047"),
        _face(f"{pid}|lw-strip", pid, room, fl, R.VOID, strip, R.DC, SRC281 + "; " + CHK,
              note="bottom-step strip inside the light-well outline: no ceiling"),
    ]


def _domes_outside(ex):
    out = []
    for d in ex["domes"]:
        out.append(_face(f"DOME-{d['DOME']}|over-walls", None, None, "1F", R.DOME, float(d["OVER_WALLS_OR_OUTSIDE_M2"]),
                         R.HELD, SRC283 + " DOMES_T283.csv",
                         held_item="open disc part over walls / outside the floor pieces (DCR-4)",
                         note=f"disc {d['OPEN_DISC_M2']} = over pieces {d['OVER_FLOOR_PIECES_M2']} + this"))
    return out


# --- binding -------------------------------------------------------------------------------------------------
def ceiling_lines(cand):
    return [l for l in cand["lines"] if l["item_code"] in SCOPE_ITEMS]


def plan_bindings(fs, lines):
    """the binding decision per face (rule 2), from the room's candidate ceiling line(s) and the owner surface; and
    what the engine line books today (`engine_books_in`)."""
    by_room = {}
    for l in lines:
        by_room.setdefault(l["room_id"], []).append(l)
    plan, books = {}, {}
    for f in fs:
        ls = sorted(by_room.get(f["room_id"], []), key=lambda x: x["line_id"])
        key = None
        if len(ls) == 1:
            key = ls[0]["line_id"]
        elif len(ls) > 1:
            key = " + ".join(l["line_id"] for l in ls)
        books[f["face_id"]] = key
        if f["owner"] in R.NO_LINE_OWNERS:
            plan[f["face_id"]] = None
        elif f["owner"] == R.STAIR_SOFFIT:
            # the only candidate slot for a soffit: a 'stairwell ceiling / soffit' line of the stair room itself
            sw = [l for l in ls if l.get("ceiling_type") == "STAIRWELL"]
            plan[f["face_id"]] = sw[0]["line_id"] if len(sw) == 1 else None
        elif not ls:
            plan[f["face_id"]] = None
        elif len(ls) == 1:
            plan[f["face_id"]] = ls[0]["line_id"]
        else:
            plan[f["face_id"]] = [l["line_id"] for l in ls]
    # the engine deducts what it does not ceil: a line deduction not re-measured by another line of the same key
    return plan, books


def engine_excluded(lines, key):
    lids = key.split(" + ")
    ls = [l for l in lines if l["line_id"] in lids]
    nets = [l["measured_net"] for l in ls if l["measured_net"] is not None]
    exc = []
    for l in ls:
        for d in l["deductions"]:
            if not any(abs((d["m2"] or 0) - n) <= R.TOL for n in nets):
                exc.append({"line_id": l["line_id"], "m2": d["m2"], "what": d["what"]})
    return exc


# --- build ---------------------------------------------------------------------------------------------------
def build():
    cand = candidate()
    lines = ceiling_lines(cand)
    fs, edges, alts, pieces = faces()
    for f in fs:
        R.check_face(f)
    R.one_owner(fs)
    plan, books = plan_bindings(fs, lines)
    rows, unmatched = R.bind(fs, lines, plan)
    for r in rows:
        r["engine_books_in"] = books[r["face_id"]] if not r.get("alternative_of") else None
    closure = R.piece_closure(fs, {p: (a, NAMED.get(p)) for p, (a, _) in pieces.items()})
    comps = []
    for key in sorted({r["engine_books_in"] for r in rows if r.get("engine_books_in")} | set(R.line_keys(rows))):
        c = R.line_compare(rows, lines, key)
        exc = engine_excluded(lines, key)
        c["engine_excluded"] = exc
        if c["engine_m2"] is not None:
            c["remainder_m2"] = round(c["engine_m2"] + sum(x["m2"] for x in exc) - c["booked_total_m2"], 6)
        comps.append(c)
    return {"candidate": cand, "lines": lines, "faces": fs, "rows": rows, "unmatched_lines": unmatched,
            "edges": edges, "alternatives": alts, "pieces": pieces, "closure": closure, "compare": comps}


# named piece residuals (rule 4), each with its cause
T271R = ROOT / "research" / "agents_t271" / "RECONCILE_T271.csv"


def named_residuals():
    """piece (T-283 floor_piece_m2 = the slab-overlay geometry) minus its faces: the T-271 overlay chord residual
    (RECONCILE_T271.csv CHORD_RESIDUAL_M2: drafting gaps of the structural linework, kept in the ceiling), and on the GF
    open piece the T-281 arc residual -0.000061 (T-271 arcs at 1024 segments vs 2048) plus T-283's 4-decimal rounding of
    the stair zone (9.8536 vs 9.853618)."""
    out = {}
    for r in csv.DictReader(io.StringIO(T271R.read_text(encoding="utf-8"))):
        c = float(r["CHORD_RESIDUAL_M2"] or 0)
        if c:
            out[r["FACE"]] = (c, "T-271 overlay chord residual (RECONCILE_T271.csv), kept in the ceiling")
    out["GF-RC99C2A/open"] = (round(-0.000061 + (9.8536 - 9.853618), 6),
                              "T-281 arc residual -0.000061 + T-283 rounding of the stair zone -0.000018")
    return out


NAMED = {k: v[0] for k, v in named_residuals().items()}


# --- outputs -------------------------------------------------------------------------------------------------
ROW_COLS = ("face_id", "physical_id", "piece", "room_id", "floor", "owner", "unit", "plan_m2", "carried", "status",
            "plan_status", "range_lo", "range_hi", "held_item", "binding", "line_id", "line_group", "share",
            "engine_books_in", "basis", "source", "note")


def _fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6f}"
    return str(v)


def _csv(cols, rows):
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\n")
    w.writerow(cols)
    for r in rows:
        w.writerow([_fmt(r.get(c)) for c in cols])
    return b.getvalue()


def status_totals(rows):
    """plan and carried by status and owner (m2); HELD and UNKNOWN carry no total (plan shown, carried blank)."""
    out = {}
    for r in rows:
        if r.get("alternative_of"):
            continue
        k = f"{r['owner']} / {r['status']}"
        t = out.setdefault(k, {"faces": 0, "plan_m2": 0.0, "carried_m2": None})
        t["faces"] += 1
        t["plan_m2"] = round(t["plan_m2"] + (r.get("plan_m2") or 0.0), 6)
        if r["status"] in R.DETERMINATE:
            t["carried_m2"] = round((t["carried_m2"] or 0.0) + r["carried"], 6)
    return dict(sorted(out.items()))


def source_closure(B):
    """rule 4 by status against the source ledgers: T-283 decor + Checker's slab north of 315 = the ledger's DECOR /
    DRAWING-CONFIRMED; T-283 owner bulkheads = BULKHEAD / AOA; T-283 'no ceiling' + T-281 wells + light-well strip =
    VOID / DC; T-283 dome surfaces + DOMES_T283 over-walls = DOME / HELD."""
    ex = json.loads(T283.read_text(encoding="utf-8"))
    summ = json.loads((ROOT / "research" / "agents_t283" / "summary.json").read_text(encoding="utf-8"))
    rows = [r for r in B["rows"] if not r.get("alternative_of")]

    def plan(owner, st=None):
        return round(sum(r["plan_m2"] or 0 for r in rows if r["owner"] == owner and (st is None or r["status"] == st)),
                     6)
    t81 = json.loads(T281S.read_text(encoding="utf-8"))["reconciliation"]
    nc283 = sum(s["qty"] for rec in ex["records"] for s in rec["surfaces"] if s["surface"].startswith("no ceiling"))
    dome283 = sum(float(d["OPEN_DISC_M2"]) for d in ex["domes"])
    checks = {
        "decor = T-283 horizontal 361.2287 + slab north of riser 315 (Checker)":
            (plan(R.DECOR, R.DC), summ["totals"]["horizontal_m2"]["villa"] +
             t81["T271-GF"]["slab north of the top riser 315 (GF-131 / GF-132 parts; plate C-T1)"]),
        "owner bulkheads = T-283 27.9345": (plan(R.BULKHEAD, R.AOA), summ["totals"]["owner_bulkhead_m2"]["villa"]),
        "no ceiling = T-283 'no ceiling' + T-281 wells GF 0.315 / 1F 0.310 + light-well strip":
            (plan(R.VOID, R.DC), nc283 + 0.315 + 0.310 +
             t81["T271-GF"]["bottom-step strip inside the light-well outline (no soffit: no ceiling)"]),
        "domes = two open discs (DOMES_T283.csv)": (plan(R.DOME, R.HELD), dome283),
        "stair zones = T-283 GF 9.8536 + 1F 10.725 + GF stair soffit 10.725 + beyond GF 1.7719 (soffit + wells + "
        "decor slab + strip, residual named)":
            (plan(R.STAIR_SOFFIT) + 0.315 + 0.310 + 0.777392 + 0.062506 - 0.000079,
             9.8536 + 10.725 + 10.725 + 1.7719),
    }
    return {k: {"ledger": round(a, 6), "source": round(b, 6), "residual": round(a - b, 6)} for k, (a, b) in
            checks.items()}


POSSIBLE_OVERLAP = {
    "GF": "T-271 s.2: the HELD-class GF garden band 9.101 + merged band 4.885 (GF-R9A05AA, GF-RFD4E1D) 'may be one of "
          "the T-127 candidate soffits: not added, no double count'; both are HELD blank here, so nothing is counted "
          "twice today; the class decision (P-2) must be checked against PL-01 / PL-02 / PL-03 before either is "
          "carried",
}


def unmatched_reason(l):
    """why a candidate ceiling line holds no face of the interior ceiling ledgers (rule 2: listed, never dropped)."""
    if (l.get("element_id") or "").startswith("SOFFIT:"):
        r = ("exterior soffit over outside air, typed record (T-121 / T-127 PLACES.csv; finish HELD Q-68 C): outside "
             "every interior floor piece of T-271 / T-283; owned by the exterior-soffit line, not the room ceilings")
        if l.get("floor") in POSSIBLE_OVERLAP:
            r += "; POSSIBLE OVERLAP: " + POSSIBLE_OVERLAP[l["floor"]]
        return r
    return "no face of the merged ceiling ledgers lies in this line's room (investigate before T-284)"


def villa_reconciliation(B):
    """the released / candidate FIN.CEILING total vs the decor ceiling this ledger carries, in named parts (rule 5):
    engine (lines with a quantity) = decor carried in them + the other faces they book (by owner / status) - what the
    lines deduct and re-measure nowhere + remainder; then the decor in BLOCKED lines and in no line."""
    lines = {l["line_id"]: l for l in B["lines"]}
    measured = [c for c in B["compare"] if c["engine_m2"] is not None]
    eng = round(sum(c["engine_m2"] for c in measured), 6)
    decor_in = round(sum(v for c in measured for k, v in c["carried_m2"].items() if k.startswith("DECOR")), 6)
    other = {}
    for c in measured:
        for k, v in c["booked_m2"].items():
            if not k.startswith("DECOR"):
                other[k] = round(other.get(k, 0.0) + v, 6)
    exc = round(sum(x["m2"] for c in measured for x in c["engine_excluded"]), 6)
    rem = round(sum(c["remainder_m2"] for c in measured), 6)
    blocked = [c for c in B["compare"] if c["engine_m2"] is None]
    decor_blocked = round(sum(v for c in blocked for k, v in c["carried_m2"].items() if k.startswith("DECOR")), 6)
    decor_noline = round(sum(r["carried"] for r in B["rows"] if r["owner"] == R.DECOR and r["binding"].startswith(
        "NO_LINE")), 6)
    check = round(eng - decor_in - sum(other.values()) + exc - rem, 6)
    return {"engine_FIN_CEILING_with_quantity": eng, "lines_with_quantity": sum(len(c["lines"]) for c in measured),
            "decor_carried_in_them": decor_in, "other_faces_booked_in_them_by_owner_status": dict(sorted(other.items())),
            "engine_deductions_not_remeasured": exc, "remainder_chord_rounding": rem, "identity_residual": check,
            "decor_in_BLOCKED_lines (engine BLANK)": decor_blocked,
            "BLOCKED_lines": [x for c in blocked for x in c["lines"]],
            "decor_in_no_candidate_line": decor_noline,
            "decor_total": round(decor_in + decor_blocked + decor_noline, 6),
            "engine_minus_decor_total": round(eng - decor_in - decor_blocked - decor_noline, 6)}


def outputs(B):
    rows = sorted(B["rows"], key=lambda r: (r["floor"] or "", r["room_id"] or "~", r["face_id"]))
    out_rows = []
    for r in rows:
        rr = dict(r)
        rr["range_lo"], rr["range_hi"] = (r["range"] or (None, None))
        out_rows.append(rr)
    ledger = _csv(ROW_COLS, out_rows)
    by_id = {l["line_id"]: l for l in B["lines"]}
    lrows = []
    for c in B["compare"]:
        ls = [by_id[x] for x in c["lines"]]
        lrows.append({"line_key": c["key"], "elements": " + ".join(l["element_id"] for l in ls),
                      "engine_state": " + ".join(c["engine_states"]), "engine_m2": c["engine_m2"],
                      "engine_excluded_m2": round(sum(x["m2"] for x in c["engine_excluded"]), 6) or None,
                      "booked_faces_m2": c["booked_total_m2"],
                      "booked_by_owner": "; ".join(f"{k} {v:.6f}" for k, v in c["booked_m2"].items()),
                      "remainder_m2": c["remainder_m2"],
                      "carried_by_owner": "; ".join(f"{k} {v:.6f}" for k, v in c["carried_m2"].items()),
                      "carried_total_m2": c["carried_total_m2"],
                      "faces_bound": sum(1 for r in B["rows"] if r.get("line_id") == c["key"]
                                         or r.get("line_group") == c["key"])})
    for l in B["unmatched_lines"]:
        lrows.append({"line_key": l["line_id"], "elements": l["element_id"], "engine_state": l["evidence_state"],
                      "engine_m2": l["measured_net"], "faces_bound": 0,
                      "booked_by_owner": "UNMATCHED_LINE: " + unmatched_reason(l)})
    lcols = ("line_key", "elements", "engine_state", "engine_m2", "engine_excluded_m2", "booked_faces_m2",
             "booked_by_owner", "remainder_m2", "carried_by_owner", "carried_total_m2", "faces_bound")
    side = [dict(e, kind="EDGE / COUNT (no candidate line)") for e in B["edges"]] + \
           [dict(a, kind="ALTERNATIVE (outside every total)") for a in B["alternatives"]]
    scols = ("kind", "piece", "room_id", "item", "unit", "qty", "status", "basis", "rule", "reason")
    cand = B["candidate"]
    summary = {
        "schema": SCHEMA, "rule": R.RULE_ID, "candidate": cand["candidate"],
        "candidate_lines_csv_sha256": cand["candidate_lines_csv_sha256"],
        "candidate_lines_json_sha256": cand["candidate_lines_json_sha256"], "lines_total": cand["lines_total"],
        "ceiling_lines": len(B["lines"]),
        "listed_other_lines": {k: sum(1 for l in cand["lines"] if l["item_code"] == k) for k in LISTED_ITEMS},
        "inputs_sha256": {"T-283 export": _sha(T283), "T-281 ledger": _sha(T281), "T-281 summary": _sha(T281S)},
        "faces": len([r for r in B["rows"] if not r.get("alternative_of")]),
        "edges_and_counts": len(B["edges"]), "alternatives": len(B["alternatives"]),
        "unmatched_lines": {l["line_id"]: {"element_id": l["element_id"], "state": l["evidence_state"],
                                           "m2": l["measured_net"], "reason": unmatched_reason(l)}
                            for l in B["unmatched_lines"]},
        "no_line_faces": {r["face_id"]: r["engine_books_in"] for r in B["rows"]
                          if r["binding"].startswith("NO_LINE") and r["owner"] not in R.NO_LINE_OWNERS},
        "by_owner_status": status_totals(B["rows"]),
        "piece_closure_residual_m2": {k: v for k, v in B["closure"].items() if v},
        "named_piece_residuals_m2": {k: v for k, v in sorted(named_residuals().items())},
        "source_closure": source_closure(B),
        "villa_reconciliation_m2": villa_reconciliation(B),
        "max_abs_line_remainder_m2": max(abs(c["remainder_m2"]) for c in B["compare"] if c["remainder_m2"] is not None),
        "released": False,
        "statement": "research ledger; NOT RELEASED; no candidate or released line changed; HELD faces carried blank "
                     "with the plan area shown; ranges never summed",
    }
    return {"CEILING_FACE_LINE_LEDGER_T295.csv": ledger, "LINE_SUMMARY_T295.csv": _csv(lcols, lrows),
            "EDGES_AND_ALTERNATIVES_T295.csv": _csv(scols, side),
            "summary.json": json.dumps(summary, indent=1, ensure_ascii=False, sort_keys=False) + "\n"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--extract")
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.extract:
        c = extract(a.extract)
        print(f"extracted {len(c['lines'])} of {c['lines_total']} lines; csv {str(c['candidate_lines_csv_sha256'])[:8]}")
        return 0
    F = outputs(build())
    if a.write:
        for n, t in F.items():
            (HERE / n).write_text(t, encoding="utf-8")
        print("written:", ", ".join(F))
        return 0
    bad = [n for n, t in F.items() if not (HERE / n).exists() or (HERE / n).read_text(encoding="utf-8") != t]
    print("check:", "OK" if not bad else f"DIFFERS {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
