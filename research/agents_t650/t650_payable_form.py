"""T-650: B9-02 LINTEL PAYABLE FORM restated per opening (research rule proposal R-T650-1; research only, nothing in
engine/ or tools/ imports it; no candidate line moves).

Lead system ruling F-T644-1 (register PRECAST LINTEL PAYABLE FORM RESTATED, 2026-11-09 00:15): the AGENT_BRIEF resolution
order puts the drawings before the OWNER CONFIRMED company rules. Physical element: the lintel over one masonry opening.
Per opening, exactly ONE payable form and ONE owner line:

  1. The head sits in a curved wall band (chord sagitta > 0), or neither jamb has masonry  -> STRUCTURAL_LINE (FLAGGED:
     the structural line that carries the band / head owns it; no lintel line, no piece).
  2. A printed project lintel schedule covers the host wall's block type and a printed band covers the width (a width
     bound must fall inside printed bands at both ends)                                      -> RC_CAST_M3 on the
     opening's STR.CONC.LINTEL line (B9-02): m3 + its bars, cast to length; NO stock piece, NO pcs.
  3. The schedule covers the block type but no band covers the width (gap / above the last)   -> SYSTEM_HELD
     (SCHEDULE_SILENT: never the nearest band and never the precast rule by default; designer item).
  4. No schedule covers the wall: WHITE -> PRECAST_PCS (owner rule UPC-LINTEL-001, pcs by stock length at 0.15 m, read
     from the R-T644-1 class); a precast class FLAGGED_* (> 4.00 m, no bearing, shared pier, head room) -> STRUCTURAL_LINE;
     BLACK -> SYSTEM_HELD (company rule: black walls 'as the drawings require'; drawings silent; Q-60 atab white only).

For RC_CAST_M3 the quantity state comes from the printed MIN bearing (0.40 m) against the measured masonry beside each
jamb (merged R-T516-1 end_state on the merged T-644 jamb evidence) and from the merged R-T524-1 end ownership:
  REQUIRED + both ends BOUNDED     -> BOUNDED m3 [B D (w + 2 b_min), B D (w + a_s + a_e)] (hi OPEN when an end is capped)
  REQUIRED + an end FLAGGED_DEFICIT -> HELD BY NAME with the R-T524-1 range (inside-column part owned by the column line)
  REQUIRED + an end HELD           -> HELD blank (never 0)
  existence HELD / register / head-room -> HELD blank with the existence cause; the RC end check is listed beside only.
A FLAGGED precast class on an RC-governed opening is NOT a payable flag (the precast piece is not the payable form there):
it is kept beside, never moves the opening to a structural line.

Refused: a width that is not metres, a bound whose ends straddle a band gap treated as covered, an unknown block type,
an opening in both pcs and m3, a second record for one opening, HELD treated as 0, a freelancer figure as a cause.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import OrderedDict
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "research" / "agents_t516", ROOT / "research" / "agents_t519", ROOT / "research" / "agents_t524"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t516_jamb_bearing as T516  # noqa: E402  (read only)

RULE_ID = "R-T650-1"
RULE_VERSION = "1.0.0"
RC, PCS, STRUCT, SYS_HELD = "RC_CAST_M3", "PRECAST_PCS", "STRUCTURAL_LINE", "SYSTEM_HELD"
FORMS = (RC, PCS, STRUCT, SYS_HELD)
BLOCKS = ("WHITE", "BLACK")
EXIST = ("REQUIRED", "HELD", "HELD_REGISTER", "FLAGGED_HEAD_ROOM")
PRECAST_PIECE = ("PIECE", "PIECE_IF_BUILT")
PRECAST_FLAGGED = ("FLAGGED_OVER_4M", "FLAGGED_NO_BEARING", "FLAGGED_SHORT", "FLAGGED_SHARED_PIER", "FLAGGED_HEAD_ROOM")
PRECAST_HELD = ("HELD_WIDTH", "HELD_ENDS", "HELD_REGISTER")
BOUNDED, HELD_NAME, HELD_BLANK = "BOUNDED", "HELD_BY_NAME", "HELD"
EPS = 1e-9


class PayableFormError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


def _w(v, oid):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v:
        raise PayableFormError(f"{oid}: width {v!r} is not a number")
    if not 0 < v <= 20.0:
        raise PayableFormError(f"{oid}: width {v!r} is not a width in metres (mm / cm entry, or not positive)")
    return float(v)


def band_of(schedule, w):
    """the printed band whose inclusive integer-cm interval holds w, or None (gap / above the last band)."""
    cm = w * 100.0
    for b in schedule["bands"]:
        if b["lo_cm"] - 1e-6 <= cm <= b["hi_cm"] + 1e-6:
            return b
    return None


def bands_for(op, schedule):
    """-> list of printed bands covering the width (one for a width; one or two for a bound), or None if any part of a
    bound falls outside every band (a straddled gap is not covered)."""
    if op.get("width_m") is not None:
        b = band_of(schedule, op["width_m"])
        return None if b is None else [b]
    lo, hi = op["width_bound_m"]
    bl, bh = band_of(schedule, lo), band_of(schedule, hi)
    if bl is None or bh is None:
        return None
    if bl["row"] != bh["row"]:
        # both ends printed but in different bands: every printed gap (a.hi, c.lo) between them lies inside the bound,
        # so a width the schedule does not cover is admissible: covered only if the bands touch with no gap
        rows = [b["row"] for b in schedule["bands"]]
        i, j = rows.index(bl["row"]), rows.index(bh["row"])
        seq = schedule["bands"][i:j + 1]
        if any(c["lo_cm"] > a["hi_cm"] + 1e-6 for a, c in zip(seq, seq[1:])):
            return None
        return seq
    return [bl]


def _check(op):
    oid = op.get("id")
    if op.get("block_type") not in BLOCKS:
        raise PayableFormError(f"{oid}: block type {op.get('block_type')!r} is not WHITE / BLACK")
    if op.get("existence") not in EXIST:
        raise PayableFormError(f"{oid}: existence {op.get('existence')!r} unknown")
    if (op.get("width_m") is None) == (op.get("width_bound_m") is None):
        raise PayableFormError(f"{oid}: exactly one of width_m / width_bound_m is needed (never 0)")
    if op.get("width_m") is not None:
        op["width_m"] = _w(op["width_m"], oid)
    else:
        lo, hi = op["width_bound_m"]
        lo, hi = _w(lo, oid), _w(hi, oid)
        if lo > hi + EPS:
            raise PayableFormError(f"{oid}: width bound {lo} > {hi}")
        op["width_bound_m"] = [lo, hi]
    for k in ("cause",):
        if "freelancer" in str(op.get(k) or "").lower():
            raise PayableFormError(f"{oid}: a freelancer figure is not a cause")
    return op


def payable_form(op, schedule):
    """-> (form, band rows or None, why). op: id, block_type, width_m | width_bound_m, existence, curved_band,
    masonry_ends (0, 1 or 2), precast_cls (R-T644-1 class, needed only when the precast rule governs)."""
    op = _check(dict(op))
    oid = op["id"]
    if op.get("curved_band"):
        return STRUCT, None, ("FLAGGED: head in a curved wall band (register CURVED-BAND OPENING HEAD): owned by the "
                              "structural line that carries the band; no lintel line, no piece")
    if op.get("masonry_ends", 2) == 0:
        return STRUCT, None, "FLAGGED: no masonry at either jamb: the head is carried by the structural frame"
    if schedule and op["block_type"] in schedule["scope"]:
        bs = bands_for(op, schedule)
        if bs is None:
            return SYS_HELD, None, (f"SCHEDULE_SILENT: {schedule['source']} covers {op['block_type']} walls but no "
                                    f"printed band covers this width: never the nearest band, never the precast rule "
                                    f"by default (designer item)")
        rows = [b["row"] for b in bs]
        return RC, rows, (f"printed {schedule['source']} row {'/'.join(rows)} covers {op['block_type']} walls and this "
                          f"width: drawings before company rules (AGENT_BRIEF resolution order; register PRECAST "
                          f"LINTEL PAYABLE FORM RESTATED): RC lintel cast to length, m3 + bars on STR.CONC.LINTEL")
    if op["block_type"] == "BLACK":
        return SYS_HELD, None, ("BLACK wall, no printed schedule covers it: company rule 'black precast or RC as the "
                                "drawings require'; drawings silent: system HELD (Q-60: atab only for white blocks)")
    cls = op.get("precast_cls")
    if cls in PRECAST_FLAGGED:
        return STRUCT, None, f"FLAGGED under the governing owner precast rule ({cls}): owned by the structural line"
    if cls in PRECAST_PIECE or cls in PRECAST_HELD:
        return PCS, None, f"WHITE wall, no printed schedule: owner precast rule UPC-LINTEL-001 governs ({cls})"
    raise PayableFormError(f"{oid}: precast class {cls!r} needed where the owner precast rule governs")


def rc_ends(op, evidence, b_min, neighbours):
    """R-T516-1 end states (merged module, read only) of one opening from its two jamb evidence rows."""
    ends = []
    for side in ("START", "END"):
        e = evidence.get(side)
        if e is None:
            raise PayableFormError(f"{op['id']}: no {side} jamb evidence")
        sid = e.get("stopper_id") or ""
        stopper = e["stopper"]
        nd = None
        if stopper == "OPENING":
            if sid in neighbours:
                nd = neighbours[sid]
            else:      # a crossing wall / non-wall marked as the stopper: the masonry ends there (as R-T519-1 reads it)
                stopper = "END_OF_MASONRY"
        x = {"side": side, "available_m": e["available_m"], "own_band_m": e["own_band_m"], "stopper": stopper,
             "stopper_id": sid, "beyond_band_end": e.get("beyond_band_end") or "",
             "search_capped": e.get("search_capped") or "", "opening_id": op["id"]}
        ends.append(T516.end_state(x, b_min, nd))
    return ends


def rc_quantity(op, ends, B, D, b_min, t524):
    """-> dict(state, low_m3, high_m3, why) for an RC_CAST_M3 opening."""
    states = [e["state"] for e in ends]
    beside = {"end_states": states, "end_hi_m": [e.get("bearing_hi_m") for e in ends]}
    if op["existence"] != "REQUIRED":
        return dict(beside, state=HELD_BLANK, low_m3=None, high_m3=None,
                    why=f"existence {op['existence']}: {op.get('cause') or 'not established'} (at most 1 lintel; the RC "
                        f"end check is beside only, never a quantity)")
    if T516.DEFICIT in states:
        if op["id"] not in t524:
            raise PayableFormError(f"{op['id']}: FLAGGED_DEFICIT end but no merged R-T524-1 record")
        r = t524[op["id"]]
        return dict(beside, state=HELD_NAME, low_m3=r["low_m3"], high_m3=r["high_m3"], pair=r.get("pair"),
                    why=f"FLAGGED_DEFICIT end(s) against the printed MIN {b_min} m: R-T524-1 range (part inside a column "
                        f"is column concrete; pier occupied once); connection is a designer item")
    if T516.HELD in states:
        return dict(beside, state=HELD_BLANK, low_m3=None, high_m3=None, why="an end is HELD (masonry not resolved)")
    if op.get("width_m") is None:
        return dict(beside, state=HELD_BLANK, low_m3=None, high_m3=None,
                    why=f"width UNRESOLVED {op.get('width_bound_m')} (drawing conflict): length HELD, never one end")
    W = Fraction(str(op["width_m"]))
    lo = _r(Fraction(str(B)) * Fraction(str(D)) * (W + 2 * Fraction(str(b_min))))
    his = [e.get("bearing_hi_m") for e in ends]
    hi = None if any(h is None for h in his) else _r(Fraction(str(B)) * Fraction(str(D)) *
                                                     (W + sum(Fraction(str(h)) for h in his)))
    return dict(beside, state=BOUNDED, low_m3=lo, high_m3=hi,
                why=f"BEARING_OK both ends: cast to length, L in [w + 2 x {b_min}, w + a_s + a_e]"
                    + ("" if hi is not None else " (an end search capped: high OPEN)"))


def restate(openings, schedule, evidence, t524, lines, B_of, D_of, b_min):
    """per opening: one form, one owner line, one quantity state. lines: {opening id: candidate line record}."""
    seen = set()
    for o in openings:
        if o["id"] in seen:
            raise PayableFormError(f"{o['id']}: a second record for one opening")
        seen.add(o["id"])
    if set(lines) != seen:
        raise PayableFormError(f"candidate line set != opening set: {sorted(set(lines) ^ seen)}")
    neighbours = {o["id"]: ("REQUIRED" if o["existence"] == "REQUIRED" else "HELD") for o in openings}
    out = OrderedDict()
    for o in sorted(openings, key=lambda x: x["id"]):
        form, rows, why = payable_form(o, schedule)
        ln = lines[o["id"]]
        rec = OrderedDict(id=o["id"], storey=o.get("storey"), block_type=o["block_type"], width_m=o.get("width_m"),
                          width_bound_m=o.get("width_bound_m"), existence=o["existence"], form=form, form_why=why,
                          schedule_rows=rows, precast_cls_beside=o.get("precast_cls"),
                          precast_piece_beside_m=o.get("precast_piece_m"), line_id=ln["line_id"],
                          line_class_now=ln["class_now"], line_low_now=ln["held_low_m3"],
                          line_high_now=ln["held_high_m3"])
        if form == RC:
            if len(rows) != 1:
                rec.update(owner_line=f"STR.CONC.LINTEL {ln['line_id']} (B9-02)", pcs=None, state=HELD_BLANK,
                           low_m3=None, high_m3=None, why="width bound spans two printed bands: D HELD")
            else:
                q = rc_quantity(o, rc_ends(o, evidence[o["id"]], b_min, neighbours), B_of[o["id"]],
                                D_of[rows[0]], b_min, t524) if o["id"] in evidence else \
                    dict(state=HELD_BLANK, low_m3=None, high_m3=None, why="no jamb evidence (never 0)")
                rec.update(owner_line=f"STR.CONC.LINTEL {ln['line_id']} (B9-02)", pcs=None, B_m=B_of[o["id"]],
                           D_m=D_of[rows[0]], **q)
        elif form == PCS:
            rec.update(owner_line="B9-02 precast lintel pcs line", pcs=o.get("precast_piece_m"),
                       state=("ESTABLISHED" if o.get("precast_cls") == "PIECE" else
                              "AT_MOST" if o.get("precast_cls") == "PIECE_IF_BUILT" else HELD_BLANK),
                       low_m3=None, high_m3=None,
                       why="pcs by stock length; the STR.CONC.LINTEL line is not the payable form (HELD, never 0)")
        elif form == STRUCT:
            rec.update(owner_line="the structural line that carries the head", pcs=None, state="FLAGGED",
                       low_m3=None, high_m3=None, why=why)
        else:
            rec.update(owner_line=f"STR.CONC.LINTEL {ln['line_id']} (B9-02), system HELD", pcs=None,
                       state=HELD_BLANK, low_m3=None, high_m3=None, why=why)
        if rec.get("pcs") is not None and rec.get("low_m3") is not None:
            raise PayableFormError(f"{o['id']}: an opening in both pcs and m3")
        if rec["state"] in (BOUNDED, HELD_NAME) and rec.get("low_m3") is None and not rec.get("pair"):
            raise PayableFormError(f"{o['id']}: a bounded line without a low value")
        rec["change"] = _change(rec)
        out[o["id"]] = rec
    return out


def check_asserted(oid, per, pcs_m=None, m3=None):
    """refuse a quantity asserted against the restated form: a piece on an RC / structural / held opening, m3 on a
    precast or structural opening, a 0 for a HELD / FLAGGED line, m3 outside a bounded line's range."""
    r = per.get(oid)
    if r is None:
        raise PayableFormError(f"{oid}: not in the restated set")
    if pcs_m is not None and r["form"] != PCS:
        raise PayableFormError(f"{oid}: a precast piece asserted but the payable form is {r['form']} (never both)")
    if m3 is not None:
        if isinstance(m3, bool) or not isinstance(m3, (int, float)):
            raise PayableFormError(f"{oid}: m3 {m3!r} is not a number")
        if r["form"] != RC:
            raise PayableFormError(f"{oid}: m3 asserted but the payable form is {r['form']}")
        if r["state"] in (HELD_BLANK, "FLAGGED") or (r["state"] == HELD_NAME and r.get("pair")):
            raise PayableFormError(f"{oid}: {m3} m3 asserted on a {r['state']} line (HELD is never a value, never 0)")
        lo, hi = r.get("low_m3"), r.get("high_m3")
        if m3 < lo - EPS or (hi is not None and m3 > hi + EPS):
            raise PayableFormError(f"{oid}: {m3} m3 outside [{lo}, {hi}]")
    return True


def _change(rec):
    if rec["form"] != RC:
        return "FORM: " + rec["form"]
    now = (rec["line_low_now"], rec["line_high_now"])
    new = (rec.get("low_m3"), rec.get("high_m3"))
    if rec.get("pair"):
        return "NEW_BOUND (pair, R-T524-1)" if now == (None, None) else "PAIR_RESTATED"
    if now == new:
        return "UNCHANGED" if new != (None, None) else "CAUSE_RESTATED (still HELD blank)"
    if now == (None, None):
        return "NEW_BOUND"
    return f"BOUND_CHANGED {now} -> {new}"


def summary(per, pairs):
    forms = OrderedDict((f, sorted(k for k, r in per.items() if r["form"] == f)) for f in FORMS)
    rc = [r for r in per.values() if r["form"] == RC]
    st = OrderedDict((s, sorted(r["id"] for r in rc if r["state"] == s)) for s in (BOUNDED, HELD_NAME, HELD_BLANK))
    lo = sum(Fraction(str(r["low_m3"])) for r in rc if r.get("low_m3") is not None)
    hi_open = [r["id"] for r in rc if r["state"] in (BOUNDED, HELD_NAME) and r.get("high_m3") is None and
               not r.get("pair")]
    hi = sum(Fraction(str(r["high_m3"])) for r in rc if r.get("high_m3") is not None)
    for p in pairs.values():
        lo += Fraction(str(p["low_m3"]))
        hi += Fraction(str(p["high_m3"]))
    pcs = [r for r in per.values() if r["form"] == PCS]
    by_len = OrderedDict()
    for r in pcs:
        by_len.setdefault(f"{r['pcs']:.2f}" if r["pcs"] else "HELD", {"ESTABLISHED": [], "AT_MOST": [], "HELD": []})
        by_len[f"{r['pcs']:.2f}" if r["pcs"] else "HELD"][r["state"]].append(r["id"])
    return OrderedDict(
        openings=len(per), forms={k: len(v) for k, v in forms.items()}, forms_ids=forms,
        rc_states={k: len(v) for k, v in st.items()}, rc_state_ids=st,
        m3_bounded_set=OrderedDict(low_m3=_r(lo), high_m3=None if hi_open else _r(hi),
                                   high_known_part_m3=_r(hi), high_open_on=hi_open,
                                   note="re-added once (D-GF-11 / D-GF-12 as one pair); HELD blank lines are not in "
                                        "it and are never 0; nothing here is released or VERIFIED"),
        pcs_governing=(OrderedDict(label="NOT_APPLICABLE (no opening has the precast payable form on this villa; "
                                         "not a zero count)", openings=[])
                       if not pcs else OrderedDict(label="PRECAST_PCS", by_stock=by_len)),
        both_pcs_and_m3=[r["id"] for r in per.values() if r.get("pcs") is not None and r.get("low_m3") is not None])


# ------------------------------------------------------------------------------------- training-villa builder
T644 = ROOT / "research" / "agents_t644" / "out" / "T644_LINTEL_PIECES.json"
EVID = ROOT / "research" / "agents_t644" / "out" / "JAMB_EVIDENCE_T644.csv"
T453 = ROOT / "research" / "agents_t453" / "out" / "LINTELS_T453.csv"
SCHEDULE = ROOT / "research" / "alsenan_lintels_s8_6" / "02_LINTEL_SCHEDULE_TRANSCRIPTION.csv"
PINS = {T644: "705568360c5f6958", EVID: "8b72cfb16ad6fcf8", T453: "8f9e515f9b95f8cf",
        SCHEDULE: "5d5baf166700d1d5"}
B_MIN = 0.40    # printed LINTEL DETAIL 'MIN.40cm' (ST7757 p.13, S8.6 transcription), scope every block-wall lintel


def sha16(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def _pinned(p):
    if PINS.get(p) and sha16(p) != PINS[p]:
        raise PayableFormError(f"{p.name}: sha256 {sha16(p)} differs from the pinned {PINS[p]} (edited input)")
    return p.read_text(encoding="utf-8")


def training_schedule():
    rows = list(csv.DictReader(io.StringIO(_pinned(SCHEDULE))))
    bands = [{"row": r["ROW_ID"], "lo_cm": int(r["WIDTH_LO_CM"]), "hi_cm": int(r["WIDTH_HI_CM"]),
              "d_cm": int(r["D_CM"])} for r in rows if r["RECORD"] == "SCHEDULE_ROW"]
    if len(bands) != 5:
        raise PayableFormError("schedule transcription: 5 printed rows expected")
    return {"source": "ST7757 p.13 LINTEL SCHEDULE", "scope": ("WHITE", "BLACK"),
            "scope_basis": "printed note 'B-WIDTH OF THE BLOCK WALL': block walls, no block type excluded (R-T519-1)",
            "bands": bands}


def training_inputs():
    t644 = json.loads(_pinned(T644))
    per644 = t644["per_opening"]
    t453 = {r["opening_id"]: r for r in csv.DictReader(io.StringIO(_pinned(T453)))}
    ev = {}
    for r in csv.DictReader(io.StringIO(_pinned(EVID))):
        ev.setdefault(r["opening_id"], {})[r["side"]] = {
            "available_m": float(r["available_m"]), "own_band_m": float(r["own_band_m"]), "stopper": r["stopper"],
            "stopper_id": r["stopper_id"], "beyond_band_end": r["beyond_band_end"], "search_capped": r["search_capped"]}
    ops = []
    for oid, p in per644.items():
        w = p.get("wall") or {}
        if t453[oid]["block_type"] != w.get("block") or abs(float(t453[oid]["wall_t_m"]) - w.get("t_m")) > EPS:
            raise PayableFormError(f"{oid}: T-453 and T-644 disagree on the host wall")
        ends = ev.get(oid)
        ops.append({"id": oid, "storey": p["storey"], "block_type": w["block"], "width_m": p.get("width_m"),
                    "width_bound_m": p.get("width_bound_m"), "existence": p["existence"], "cause": p.get("cause"),
                    "curved_band": False,
                    "masonry_ends": (None if ends is None else sum(1 for s in ends.values() if s["available_m"] > 0)),
                    "precast_cls": p["cls"], "precast_piece_m": p.get("piece_m")})
    for o in ops:
        if o["masonry_ends"] is None:
            o.pop("masonry_ends")
    B_of = {oid: float(r["wall_t_m"]) for oid, r in t453.items()}
    lines = {k: v for k, v in t644["m3_lines"].items()}
    return ops, ev, B_of, lines, t644


def training_t524():
    import t524_lintel_end_ownership as T524
    d = T524.build()
    pair_ids = {i for p in d["pairs"] for i in p["pair"]}
    out = {}
    for k, r in d["lintels"].items():
        if k in pair_ids:
            out[k] = {"low_m3": None, "high_m3": None, "pair": "+".join(next(p["pair"] for p in d["pairs"]
                                                                              if k in p["pair"]))}
        else:
            out[k] = {"low_m3": r["concrete_lo_m3"], "high_m3": r["concrete_hi_m3"]}
    pairs = {"+".join(p["pair"]): {"ids": p["pair"], "low_m3": p["concrete_lo_m3"], "high_m3": p["concrete_hi_m3"],
                                   "pier_m": p["pier_m"]} for p in d["pairs"]}
    return out, pairs, d["summary"]


def training_t519():
    import t519_lintel_pieces as T519
    return {r["opening_id"]: r for r in T519.build()["rows"]}


def control_t519(per, t519):
    """the RC state of every R-T519-1 REQUIRED opening must agree with this run's end check (same rule, newer reader)."""
    rows = []
    for oid, r in t519.items():
        if r.get("decision") != "REQUIRED":
            continue
        mine = per[oid]
        theirs = r["state"]
        mine_s = {"BOUNDED": "PRODUCED", "HELD_BY_NAME": "HELD", "HELD": "HELD"}.get(mine["state"])
        rows.append({"id": oid, "t519_state": theirs, "t519_system": r.get("system"), "t650_state": mine["state"],
                     "agree": mine_s == theirs and r.get("system") == "PROJECT_RC" and mine["form"] == RC})
    return rows


def build():
    sched = training_schedule()
    ops, ev, B_of, lines, t644 = training_inputs()
    t524, pairs, t524_sum = training_t524()
    D_of = {b["row"]: b["d_cm"] / 100.0 for b in sched["bands"]}
    per = restate(ops, sched, ev, t524, lines, B_of, D_of, B_MIN)
    s = summary(per, pairs)
    ctrl = control_t519(per, training_t519())
    if not all(c["agree"] for c in ctrl):
        raise PayableFormError(f"R-T519-1 control disagrees: {[c for c in ctrl if not c['agree']]}")
    # conservation against R-T524-1: the deficit set restated here equals its corrected set
    dset = [r for r in per.values() if r["state"] == HELD_NAME]
    lo = sum(Fraction(str(r["low_m3"])) for r in dset if r.get("low_m3") is not None) + \
        sum(Fraction(str(p["low_m3"])) for p in pairs.values())
    hi = sum(Fraction(str(r["high_m3"])) for r in dset if r.get("high_m3") is not None) + \
        sum(Fraction(str(p["high_m3"])) for p in pairs.values())
    if (_r(lo), _r(hi)) != (t524_sum["corrected_lo_m3"], t524_sum["corrected_hi_m3"]):
        raise PayableFormError(f"deficit set {_r(lo)} .. {_r(hi)} != R-T524-1 {t524_sum['corrected_lo_m3']} .. "
                               f"{t524_sum['corrected_hi_m3']}")
    beside = OrderedDict(
        label="owner precast method BESIDE (R-T644-1 at 0.15 m): not payable on this villa; substitution reference "
              "only; Q-60 gives a precast alternative to WHITE walls only",
        t644_established_nr=t644["tables"]["established_total_nr"], t644_at_most_nr=t644["tables"]["at_most_total_nr"],
        white_wall_pieces=OrderedDict(sorted((k, r["precast_piece_beside_m"]) for k, r in per.items()
                                             if r["block_type"] == "WHITE" and r["precast_piece_beside_m"])))
    return OrderedDict(
        rule=RULE_ID, version=RULE_VERSION, ruling="register PRECAST LINTEL PAYABLE FORM RESTATED (Lead 2026-11-09 "
                                                   "00:15, F-T644-1)",
        inputs={"t644_sha16": sha16(T644), "jamb_evidence_t644_sha16": sha16(EVID), "lintels_t453_sha16": sha16(T453),
                "schedule_sha16": sha16(SCHEDULE)},
        min_bearing_m=B_MIN, schedule=sched, per_opening=per, pairs=pairs, summary=s,
        control_t519=ctrl, t524_conservation={"low_m3": _r(lo), "high_m3": _r(hi), "t524": [
            t524_sum["corrected_lo_m3"], t524_sum["corrected_hi_m3"]]},
        outside_the_60=t644["no_stock_piece_outside_the_60"], precast_beside=beside)


if __name__ == "__main__":
    res = build()
    dst = HERE / "out" / "T650_PAYABLE_FORM.json"
    dst.parent.mkdir(exist_ok=True)
    dst.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
    s = res["summary"]
    print(dst)
    print("forms", s["forms"])
    print("rc states", s["rc_states"])
    print("m3 set", dict(s["m3_bounded_set"]))
    print("pcs", s["pcs_governing"]["label"])
