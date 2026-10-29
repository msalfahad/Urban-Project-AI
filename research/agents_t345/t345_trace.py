"""T-345 TRACE OF THE ONE UNEXPLAINED T-341 FILL LINE (research, read-only; imported by nothing in engine/). Every villa.

T-341 left one V3.0.22 floor line unfilled: a floor line whose net comes from STAIR_FLOOR_RESIDUE_V1 (T-116, wired by
ARCH_TAKEOFF_V3.0 arch_v30.stair_changes) while its canonical 'deductions' list is still the BASE line's list
(arch_measure / arch_floor.split_face: per-quad convex clipping, flights summed one by one). The piece changes the net,
the formula and calculation.inputs.v3_0, but never the list, so

    face - base list - (V3.0.14 floor-scope rows) != net         (the step the T-341 fill could not name)

This tool names that step from the piece's own record, each item once, in the line's unit:

  1. TREADS   the base list's two tread rows are restated from the piece's exact tread union, flight by flight
              (own flights: union of each flight's quads inside the face, less the void; flights of the plan below:
              the same, less the own flights and every earlier flight below, so an overlap is deducted once);
              the difference to the base rows is reported per flight (a non-convex winder quad clipped as convex
              under-deducts; two flights' overlap summed twice over-deducts)
  2. VOID     the piece's void (exact face inside the outlined void windows)
  3. RESIDUE  every VOID_RESIDUE / STAIR_FOOTPRINT cell of the piece by its piece id (Rnn)
  4. SCOPE    the line's own floor_scope_v3014 rows (NOT_FLOOR pieces, split_out part) as in T-341
  5. SETTLED  held pieces the line's settlement turned to FLOOR are not deducted (they stay in the net)

and checks  face (calculation.inputs.v3_0.face_m2 / conservation face) - sum = measured_net  within TOL. The piece record
must agree with what the line itself carries in calculation.inputs.v3_0 (void, residue, footprint, held, floor before
residue); a disagreement REFUSES the trace (the record is not the line's). A held piece that no settlement decides
keeps the line HELD (no fill), never 0. Statuses: TRACED (closes, every row by id), TRACED_RESIDUAL (closes only with a
named residual above TOL), REFUSED (record mismatch, duplicate row, row in another unit, negative row), NOT_TRACEABLE
(no piece record for the line: kept HELD by name).

    python3 -I research/agents_t345/t345_trace.py --lines V3_0_22_BOQ_LINES.json --v29 <pickle> --out DIR
    (the pickle is (boq, arch, extra) of tools.urban_boq_m9.arch_compute(<plan.dxf>, method="ARCH_TAKEOFF_V2.9"),
    the run STAIR_FLOOR_RESIDUE_V1 reads in the V3.0 candidate; outputs: areas and engine ids only, no coordinates)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import pickle
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_GUARD_CLASS = "TOOLING"
TOL = 0.0005                    # boq_export_v1.QTY_MATCH_TOL (the T-341 tolerance)
REC_TOL = 0.000005              # piece record vs the line's inputs.v3_0 (both written at 6 dp)
DEC = 6
FLOOR_ITEMS = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE")
BASE_TREADS = "stair treads drawn inside the room"
BASE_VOID = "the outlined void inside the face"
BASE_BELOW = "a flight of the plan below seen through the opening"
COLS = ("line_id", "item_code", "floor", "element_id", "unit", "role", "item_id", "category", "amount", "base_amount",
        "change_vs_base", "source", "note")
LINE_COLS = ("line_id", "item_code", "floor", "element_id", "unit", "scope", "status", "gross_used", "measured_net",
             "base_list_sum", "trace_sum", "residual", "step_named", "rows", "cause")


class TraceError(ValueError):
    pass


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _r(x):
    return round(float(x), DEC)


# ---------------------------------------------------------------------------------------------------- geometry part
def flight_split(room, voids, unit_m):
    """per-flight exact tread areas inside the face, each m2 once: [(flight_id, 'own'|'below', m2, quad_sum_m2,
    base_m2)]. Same geometry as STAIR_FLOOR_RESIDUE_V1 (snap grid, own first, below less own and less earlier below);
    base_m2 = what arch_floor._treads (the base list) deducts for that flight."""
    from shapely import set_precision
    from shapely.ops import unary_union

    from engine.source import arch_floor as AF
    from engine.source import stair_floor_residue as SFR
    u = unit_m
    F = set_precision(SFR._face_geom(room, u), SFR.GRID_M)
    by_id = {v.get("void_id"): v for v in voids or ()}
    vids = [v.get("void_id") for v in room.get("voids") or ()]
    V = unary_union([SFR._poly(by_id[i]["corners"], u) for i in vids if i in by_id]) if vids else None
    V = set_precision(V.intersection(F), SFR.GRID_M) if V is not None and not V.is_empty else None
    wins = [[(x * u, y * u) for x, y in by_id[i]["corners"]] for i in vids if i in by_id]
    flights = list((room.get("symbols_inside") or {}).get("stair_flights") or ())
    own = [f for f in flights if not f.get("drawn_on_plan_below")]
    below = [f for f in flights if f.get("drawn_on_plan_below")]
    taken = None
    out = []
    for group, kind in ((own, "own"), (below, "below")):
        for fl in group:
            g = unary_union([SFR._poly(q, u) for q in fl["tread_quads"]]).intersection(F)
            if V is not None:
                g = g.difference(V)
            if taken is not None:
                g = g.difference(taken)
            taken = g if taken is None else unary_union([taken, g])
            qsum = sum(SFR._poly(q, u).intersection(F).area for q in fl["tread_quads"])
            b, bv = AF._treads(room, [fl], wins, u)
            out.append((str(fl.get("flight_id")), kind, _r(g.area), _r(qsum), _r(max(b - bv, 0.0))))
    return out


# -------------------------------------------------------------------------------------------------- record part
def _base_item(ln, prefix):
    for d in ln.get("deductions") or ():
        if isinstance(d, dict) and str(d.get("what", "")).startswith(prefix):
            return float(d.get("m2"))
    return None


def _row(ln, role, iid, cat, amount, source, base=None, note=""):
    loc = ln.get("location") or {}
    return {"line_id": ln["line_id"], "item_code": ln.get("item_code"), "floor": loc.get("floor"),
            "element_id": loc.get("element_id"), "unit": ln.get("unit"), "role": role, "item_id": iid,
            "category": cat, "amount": _r(amount), "base_amount": None if base is None else _r(base),
            "change_vs_base": None if base is None else _r(amount - base), "source": source, "note": note}


def record_matches_line(rec, v30):
    """the piece record is the one the line was built from: every aggregate the line carries agrees."""
    bad = []
    for k in ("void_m2", "void_residue_m2", "stair_footprint_m2", "held_m2", "floor_before_residue_m2"):
        a, b = rec.get(k), (v30 or {}).get(k)
        if not (_num(a) and _num(b)) or abs(a - b) > REC_TOL:
            bad.append(f"{k}: record {a} vs line {b}")
    return bad


def trace_line(ln, rec, flights):
    """-> (line record, rows). ln: the V3.0.x floor line; rec: its STAIR_FLOOR_RESIDUE_V1 record; flights: the
    flight_split() tuples of the same face. Never modifies ln."""
    unit, net = ln.get("unit"), ln.get("measured_net")
    inp = (ln.get("calculation") or {}).get("inputs") or {}
    v30 = inp.get("v3_0") or {}
    loc = ln.get("location") or {}
    cause, rows = [], []
    base_list = sum(float(d.get("m2")) for d in ln.get("deductions") or () if isinstance(d, dict) and
                    _num(d.get("m2")))
    head = {"line_id": ln["line_id"], "item_code": ln.get("item_code"), "floor": loc.get("floor"),
            "element_id": loc.get("element_id"), "unit": unit, "scope": v30.get("scope") or rec and rec.get("scope"),
            "measured_net": net, "base_list_sum": _r(base_list)}
    if rec is None or not v30:
        return dict(head, status="NOT_TRACEABLE", gross_used=None, trace_sum=None, residual=None, step_named=None,
                    rows=0, cause="no STAIR_FLOOR_RESIDUE_V1 record for this line: kept HELD by name"), []
    bad = record_matches_line(rec, v30)
    if bad:
        return dict(head, status="REFUSED", gross_used=None, trace_sum=None, residual=None, step_named=None, rows=0,
                    cause="piece record is not the line's: " + "; ".join(bad)), []
    face = (v30.get("conservation") or {}).get("face_m2")
    face = face if _num(face) else v30.get("face_m2")
    # 1. treads, flight by flight (base rows restated)
    b_own, b_below = _base_item(ln, BASE_TREADS), _base_item(ln, BASE_BELOW)
    own = [f for f in flights if f[1] == "own"]
    below = [f for f in flights if f[1] == "below"]
    for fid, kind, m2, qsum, base in own + below:
        note = ""
        if abs(m2 - base) > TOL:
            note = ("base clipped this flight's quads as convex (arch_floor._treads, PP.region_area_in_convex): "
                    f"exact {m2:.6f} vs base {base:.6f}") if m2 > base else (
                    f"an overlap with an earlier flight deducted once here (quad sum {qsum:.6f}, base {base:.6f})")
        rows.append(_row(ln, "DEDUCTION", fid, "TREADS_OWN" if kind == "own" else "TREADS_BELOW_SEEN", m2,
                         "STAIR_FLOOR_RESIDUE_V1 exact tread union, by flight", base=base, note=note))
    t_own = sum(f[2] for f in own)
    t_below = sum(f[2] for f in below)
    for got, want, what in ((t_own, rec.get("stair_flights_m2"), "own"),
                            (t_below, rec.get("stair_below_seen_m2"), "below")):
        if _num(want) and abs(got - want) > TOL:
            cause.append(f"flight split {what} {got:.6f} vs piece {want:.6f}")
    # 2. void
    if _num(rec.get("void_m2")) and rec["void_m2"] > 0:
        vid = ",".join(v.get("void_id", "") for v in rec.get("voids") or ()) or f"{rec.get('face_id')}:void"
        rows.append(_row(ln, "DEDUCTION", vid, "VOID", rec["void_m2"], "STAIR_FLOOR_RESIDUE_V1 void",
                         base=_base_item(ln, BASE_VOID)))
    # 3. residue cells by piece id
    for p in rec.get("pieces") or ():
        rows.append(_row(ln, "DEDUCTION", f"{rec.get('face_id')}:{p['piece']}", p["category"], p["m2"],
                         "STAIR_FLOOR_RESIDUE_V1 cell", note="touches " + "/".join(
                             str(t).split(":")[-1] for t in p.get("touches_flights") or ()) +
                         f"; bounding {p.get('bounding_rect_m')}"))
    # 4. the line's floor scope (settlement of the held pieces, split-out part)
    fs = inp.get("floor_scope_v3014") or {}
    settled = {}
    for pc in fs.get("pieces") or ():
        if not _num(pc.get("area_m2")):
            continue
        settled[pc.get("piece")] = pc
        if pc.get("to") == "NOT_FLOOR":
            rows.append(_row(ln, "DEDUCTION", pc.get("piece"), "SETTLED_NOT_FLOOR", pc["area_m2"],
                             "FLOOR_SCOPE piece NOT_FLOOR (calculation.inputs.floor_scope_v3014)",
                             note=str(pc.get("why", ""))[:160]))
    held = float(rec.get("held_m2") or 0.0)
    settled_m2 = sum(float(p["area_m2"]) for p in settled.values())
    if held > TOL and abs(settled_m2 - held) > TOL:
        cause.append(f"held pieces {held:.6f} m2 not all settled by the line ({settled_m2:.6f}): line stays HELD")
    so = fs.get("split_out") or {}
    if _num(so.get("area_m2")):
        rows.append(_row(ln, "DEDUCTION", f"{fs.get('id') or fs.get('record') or 'FLOOR_SCOPE'}:{so.get('part')}",
                         "SPLIT_OUT", so["area_m2"], "FLOOR_SCOPE split_out (calculation.inputs.floor_scope_v3014)",
                         note=str(so.get("decision", ""))[:160]))
    # checks
    refused = []
    dup = [k for k, n in Counter((r["item_id"], r["category"]) for r in rows).items() if n > 1]
    if dup:
        refused.append(f"listed twice: {sorted(dup)}")
    if any(r["unit"] != unit for r in rows):
        refused.append("a row in another unit")
    if any(not (r["amount"] >= 0) for r in rows):
        refused.append("a negative / non-numeric row")
    s = sum(r["amount"] for r in rows)
    residual = None if not (_num(face) and _num(net)) else face - s - net
    step = None
    fsum = sum(float((x or {}).get("area_m2") or 0) for x in [so]) + sum(
        float(p["area_m2"]) for p in settled.values() if p.get("to") == "NOT_FLOOR")
    if _num(face) and _num(net):
        step = _r(face - base_list - fsum - net)       # the T-341 'unnamed' step (incl. the settled held part)
    if refused:
        status = "REFUSED"
        cause += refused
    elif residual is None:
        status = "NOT_TRACEABLE"
        cause.append("no face area or no net: kept HELD by name, never 0")
    elif held > TOL and abs(settled_m2 - held) > TOL:
        status = "NOT_TRACEABLE"
    elif abs(residual) > TOL:
        status = "TRACED_RESIDUAL"
        cause.append(f"residual {residual:.6f} {unit} named, not forced")
    else:
        status = "TRACED"
    return dict(head, status=status, gross_used=None if face is None else _r(face), trace_sum=_r(s),
                residual=None if residual is None else _r(residual), step_named=step, rows=len(rows),
                cause="; ".join(cause)), rows


def step_decomposition(rows, base_list_rows):
    """the T-341 step (face - base list - floor scope - net) in named items: per-flight tread changes + void change +
    residue cells. base_list_rows: {category: base m2}."""
    out = []
    for r in rows:
        if r["category"].startswith("TREADS") and r["change_vs_base"] not in (None, 0.0):
            out.append((r["item_id"], r["category"], r["change_vs_base"]))
        elif r["category"] == "VOID" and r["base_amount"] is not None and abs(r["change_vs_base"]) > 0:
            out.append((r["item_id"], "VOID", r["change_vs_base"]))
        elif r["category"] in ("VOID_RESIDUE", "STAIR_FOOTPRINT"):
            out.append((r["item_id"], r["category"], r["amount"]))
    return out


def apply_trace(lines, recs, rows):
    """what T-246 does, on COPIES: a TRACED line gets gross = the face and the traced list (id, qty, unit, category,
    source); every other line is left as it is."""
    ok = {r["line_id"]: r for r in recs if r["status"] == "TRACED"}
    out = []
    for ln in lines:
        if ln["line_id"] not in ok:
            out.append(ln)
            continue
        n = json.loads(json.dumps(ln))
        n["gross"] = ok[ln["line_id"]]["gross_used"]
        n["deductions"] = [{"id": r["item_id"], "qty": r["amount"], "unit": r["unit"], "face": r["category"],
                            "source": r["source"], "what": r["note"]} for r in rows
                           if r["line_id"] == ln["line_id"] and r["role"] == "DEDUCTION"]
        out.append(n)
    return out


# ------------------------------------------------------------------------------------------------------- run part
def _voids_by_floor(arch):
    out = {}
    for v in arch["run"].get("double_height") or ():
        if v.get("state") != "APPLIED":
            continue
        dx, dy = v["offset"]["dx"], v["offset"]["dy"]
        out.setdefault(v["floor"], []).append({"void_id": v["void_id"],
                                               "corners": [(x - dx, y - dy) for x, y in v["window"]]})
    return out


def survey(lines, arch, extra):
    """acceptance (c): every floor line of the candidate, its piece scope and whether its list explains its net."""
    from engine.source import stair_floor_residue as SFR
    u = arch["run"]["unit_m"]
    voids = _voids_by_floor(arch)
    rooms = {r["room_id"]: r for r in arch["rooms"]}
    doors = {}
    for o in arch.get("openings") or ():
        c = (o.get("position") or {}).get("centre_m")
        if c:
            for r in o.get("rooms") or ():
                doors.setdefault(r, []).append((c[0] / u, c[1] / u))
    recs, rows, census = [], [], []
    for ln in lines:
        if ln.get("item_code") not in FLOOR_ITEMS:
            continue
        loc = ln.get("location") or {}
        rid = loc.get("room_id") or (loc.get("element_id") or "").split(":")[0]
        v30 = ((ln.get("calculation") or {}).get("inputs") or {}).get("v3_0")
        room = rooms.get(rid)
        flights = (room or {}).get("symbols_inside", {}).get("stair_flights") or () if room else ()
        void_ids = [v.get("void_id") for v in (room or {}).get("voids") or ()]
        census.append({"line_id": ln["line_id"], "floor": loc.get("floor"), "element_id": loc.get("element_id"),
                       "item_code": ln["item_code"], "flights": len(flights), "voids": len(void_ids),
                       "piece_applied": bool(v30), "scope": (v30 or {}).get("scope"),
                       "base_list_m2": _r(sum(float(d.get("m2")) for d in ln.get("deductions") or ()
                                              if isinstance(d, dict) and _num(d.get("m2")))),
                       "measured_net": ln.get("measured_net"), "gross": ln.get("gross")})
        if not v30 or room is None:
            continue
        rec = SFR.face_residue(room, voids=voids.get(room["floor"], ()), segments=extra["segments"],
                               arcs=extra["arcs"], unit_m=u, floor_points=doors.get(rid, ()))
        rec["voids"] = [{"void_id": i} for i in void_ids]
        lr, rr = trace_line(ln, rec, flight_split(room, voids.get(room["floor"], ()), u))
        recs.append(lr)
        rows += rr
    return recs, rows, census


def _t330(lines, recs, rows):
    """T-330 (tools/t330_deductions_check.py, read only) on the traced lines before / after apply_trace (copies)."""
    from tools import t330_deductions_check as C
    ids = {r["line_id"] for r in recs}
    after = {ln["line_id"]: ln for ln in apply_trace(lines, recs, rows) if ln["line_id"] in ids}
    return {lid: {"before": C.check_line(next(x for x in lines if x["line_id"] == lid))["category"],
                  "after": C.check_line(after[lid])["category"]} for lid in sorted(ids)}


def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.{DEC}f}" if isinstance(r[k], float) else r[k]))
                    for k in cols})
    return buf.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", required=True)
    ap.add_argument("--v29", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    raw = Path(a.lines).read_bytes()
    lines = json.loads(raw)
    lines = lines if isinstance(lines, list) else lines["lines"]
    _boq, arch, extra = pickle.load(open(a.v29, "rb"))
    recs, rows, census = survey(lines, arch, extra)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "TRACE_ROWS_T345.csv").write_text(_csv(rows, COLS), encoding="utf-8")
    (out / "TRACE_LINES_T345.csv").write_text(_csv(recs, LINE_COLS), encoding="utf-8")
    ccols = ("line_id", "floor", "element_id", "item_code", "flights", "voids", "piece_applied", "scope",
             "base_list_m2", "gross", "measured_net")
    (out / "FLOOR_LINE_SURVEY_T345.csv").write_text(_csv(census, ccols), encoding="utf-8")
    summ = {"task": "T-345", "lines_sha256_8": hashlib.sha256(raw).hexdigest()[:8], "lines": len(lines),
            "floor_lines": len(census), "piece_applied": sum(1 for c in census if c["piece_applied"]),
            "traced": [{k: r[k] for k in ("line_id", "status", "gross_used", "measured_net", "base_list_sum",
                                          "trace_sum", "residual", "step_named", "rows", "cause")} for r in recs],
            "t330_on_traced_lines": _t330(lines, recs, rows),
            "step_items": {r["line_id"]: step_decomposition([x for x in rows if x["line_id"] == r["line_id"]], {})
                           for r in recs}}
    (out / "summary.json").write_text(json.dumps(summ, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps(summ, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
