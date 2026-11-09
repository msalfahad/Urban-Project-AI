"""T-644: B9-02 lintels as PRECAST PIECES by the owner lintel rule, one class per opening (rule R-T644-1 1.0.0).

Scope: every villa (the rule); the training villa's 60 STR.CONC.LINTEL openings (builder below). Research only: no engine,
rule / knowledge version, registry, frozen, candidate or statement file is changed; nothing is released.

PHYSICAL ELEMENT. One precast lintel over one masonry opening, resting on BUILT masonry at both ends. Owner lintel rule
2026-11-02 (AGENT_BRIEF; company_rulebook_v1 UPC-LINTEL-001, read only): stock 1.20 / 1.50 / 2.50 / 3.00 / 4.00 m, at
least 0.15 m bearing each side, the shortest stock length >= masonry opening + 2 x 0.15, one piece per opening, counted in
pieces; an opening needing more than 4.00 m is FLAGGED (cast-in-situ or design). The piece exists physically only if
  (a) a lintel is required there at all (masonry is built over the head; source: the merged lintel ledger T-453 r2 and
      the T-616 drawn-evidence decisions), and
  (b) the chosen piece can actually rest on >= 0.15 m of built masonry at BOTH ends: with a = the built masonry beside a
      jamb along the wall line (T-516 / T-527 LINTEL_BEARING_V3 reader), the piece of length P over width w needs end
      overhangs o_s + o_e = P - w with 0.15 <= o <= a at each end; a pier shared with a neighbouring opening carries
      both overhangs (o_i + o_j <= pier).

R-T644-1 1.0.0 (every villa; provenance: owner lintel rule 2026-11-02, R-T516-1, R-T527-1, R-T581-1, R-T616-1, register
LINTEL WIDTH BASIS / CURVED-BAND OPENING HEAD / LIFT LANDING DOOR LINTEL / PRECAST LINTEL PAYABLE FORM; no new factor):
  1. Width: the masonry opening (wall-end gap). Not established -> HELD_WIDTH, unless every admissible width is FLAGGED
     by (3)/(4) (then FLAGGED: the class does not depend on the unresolved width). mm / cm and <= 0 refused.
  2. Piece: UPC-LINTEL-001 with the company 0.15 m bearing. > 4.00 m -> FLAGGED_OVER_4M (no piece may be given).
  3. Ends not measured (no masonry capture of the jambs) -> HELD_ENDS (piece length beside, never counted).
     An end < 0.15 m -> FLAGGED_NO_BEARING (a column face, a cross wall or a free end at the jamb: the owner rule's
     minimum cannot be met; the head is owned by the structural line that carries it, register PAYABLE FORM).
     a_s + a_e < P - w -> FLAGGED_SHORT_PIERS (the piece is longer than the masonry between the stoppers).
  4. Shared piers: the minimum overhang an opening must put on a shared pier is max(0.15, (P - w) - cap_other), cap_other
     = the opposite end's a, or (if that end is shared too) its pier minus the neighbour's minimum there (fixpoint).
     Two minima above the pier -> FLAGGED_SHARED_PIER on both (one piece per opening cannot rest on both).
  5. Existence: REQUIRED -> PIECE (counted, ESTABLISHED); HELD with its cause -> PIECE_IF_BUILT (counted only in the
     AT_MOST table); FLAGGED head room (the head leaves no room for a 0.20 piece under some soffits) -> FLAGGED_HEAD_ROOM;
     a register hold (lift landing door) -> HELD_REGISTER (piece beside). A fit FLAG (3)/(4) outranks existence: if the
     lintel is built it is not a stock piece.
  6. Curved band / not in masonry: NO_STOCK_PIECE by name (register CURVED-BAND OPENING HEAD), outside the piece table.
  7. Count: pieces in nr per stock length per storey; lm only beside; every opening in exactly one class; the class
     totals re-add to the number of openings (asserted). A HELD / FLAGGED opening is never 0 and never a piece.
  8. Refusals: a piece asserted for a FLAGGED opening, a piece asserted without both bearings measured, an id twice, a
     non-metre width, a fractional count.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import company_rulebook_v1 as C  # noqa: E402  (read only)

RULE_ID = "R-T644-1"
RULE_VERSION = "1.0.0"
EPS = 1e-6
MAX_W = 12.0
MIN_B = float(C.param("UPC-LINTEL-001", "min_bearing_each_side_m")["value"])
STOCK = tuple(sorted(float(x) for x in C.param("UPC-LINTEL-001", "stock_lengths_m")["value"]))

PIECE, IF_BUILT = "PIECE", "PIECE_IF_BUILT"
F_OVER, F_NOB, F_SHORT, F_SHARED, F_HEAD = ("FLAGGED_OVER_4M", "FLAGGED_NO_BEARING", "FLAGGED_SHORT_PIERS",
                                            "FLAGGED_SHARED_PIER", "FLAGGED_HEAD_ROOM")
H_WIDTH, H_ENDS, H_REG = "HELD_WIDTH", "HELD_ENDS", "HELD_REGISTER"
CLASSES = (PIECE, IF_BUILT, F_OVER, F_NOB, F_SHORT, F_SHARED, F_HEAD, H_WIDTH, H_ENDS, H_REG)
EXIST = ("REQUIRED", "HELD", "FLAGGED_HEAD_ROOM", "HELD_REGISTER")


class PieceError(ValueError):
    pass


def _w(x, what):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise PieceError(f"{what}: {x!r} is not a number")
    if x <= 0:
        raise PieceError(f"{what}: {x!r} is not positive (held is never 0)")
    if x > MAX_W:
        raise PieceError(f"{what}: {x} m is above {MAX_W} m (not metres: mm / cm refused)")
    return float(x)


def stock_piece(width_m):
    """-> (piece_m or None, required_m) by UPC-LINTEL-001 at the company bearing."""
    r = C.lintel(_w(width_m, "masonry opening width"))
    return (r.get("piece_m") if r["status"] == C.OK else None), r["required_m"]


def _end(e, oid, side):
    if e is None:
        return None
    a = e.get("a_m")
    if a is None:
        return None
    if not isinstance(a, (int, float)) or isinstance(a, bool) or a < 0 or a > 50:
        raise PieceError(f"{oid} {side}: available masonry {a!r} m is not a length in metres")
    return {"a": float(a), "shared_with": e.get("shared_with")}


def classify(openings):
    """openings: [{'id', 'storey', 'width_m' (or None) and optional 'width_bound_m' [lo, hi], 'existence' in EXIST,
    'cause', 'ends': {'START': {'a_m', 'shared_with'}, 'END': {...}} or None}] -> per-opening records (rule (1)-(5))."""
    seen, recs = set(), OrderedDict()
    for o in openings:
        oid = o.get("id")
        if not oid:
            raise PieceError("an opening without an id")
        if oid in seen:
            raise PieceError(f"{oid}: named twice (one opening, one lintel)")
        seen.add(oid)
        if o.get("existence") not in EXIST:
            raise PieceError(f"{oid}: existence {o.get('existence')!r} is not one of {EXIST}")
        widths = []
        if o.get("width_m") is not None:
            widths = [_w(o["width_m"], f"{oid} width")]
        elif o.get("width_bound_m"):
            lo, hi = (_w(x, f"{oid} width bound") for x in o["width_bound_m"])
            if lo > hi:
                raise PieceError(f"{oid}: width bound {lo} .. {hi} reversed")
            widths = [lo, hi]
        ends = o.get("ends")
        es = {s: _end((ends or {}).get(s), oid, s) for s in ("START", "END")} if ends else None
        recs[oid] = {"o": o, "widths": widths, "ends": es}
    # piece per admissible width
    for oid, r in recs.items():
        r["pieces"] = [stock_piece(w) for w in r["widths"]]
    # shared piers: neighbour must be in the list and point back
    for oid, r in recs.items():
        for s, e in (r["ends"] or {}).items():
            if e and e["shared_with"]:
                n = recs.get(e["shared_with"])
                back = [x for x in ((n or {}).get("ends") or {}).values() if x and x["shared_with"] == oid]
                if not back:
                    raise PieceError(f"{oid} {s}: shared pier with {e['shared_with']} not recorded on its side")
                if abs(back[0]["a"] - e["a"]) > 0.002:
                    raise PieceError(f"{oid} / {e['shared_with']}: one pier measured twice differently "
                                     f"({e['a']} vs {back[0]['a']})")
    out = OrderedDict()
    for oid, r in recs.items():
        out[oid] = _one(oid, r, recs)
    return out


def _need(r, i):
    """total overhang P - w for admissible width i (None if FLAGGED over 4 m)."""
    p, _req = r["pieces"][i]
    return None if p is None else round(p - r["widths"][i], 6)


def _min_use(oid, side, r, recs, i, depth=0):
    """minimum overhang opening oid must put on its `side` end (rule (4)), for width index i."""
    d = _need(r, i)
    other = "END" if side == "START" else "START"
    eo = r["ends"][other]
    cap = eo["a"]
    if eo["shared_with"] and depth < 8:
        n = recs[eo["shared_with"]]
        nside = [s for s, x in n["ends"].items() if x and x["shared_with"] == oid][0]
        if n["widths"] and n["ends"] and all(n["ends"].values()) and _need(n, 0) is not None:
            cap = eo["a"] - _min_use(eo["shared_with"], nside, n, recs, 0, depth + 1)
    return max(MIN_B, d - cap)


def _fit(oid, r, recs, i):
    """-> None (fits) or a FLAGGED class, for admissible width i."""
    if _need(r, i) is None:
        return F_OVER
    es = r["ends"]
    if es["START"]["a"] < MIN_B - EPS or es["END"]["a"] < MIN_B - EPS:
        return F_NOB
    if es["START"]["a"] + es["END"]["a"] < _need(r, i) - EPS:
        return F_SHORT
    for s, e in es.items():
        if e["shared_with"]:
            n = recs[e["shared_with"]]
            if not (n["widths"] and n["ends"] and all(n["ends"].values())):
                continue          # neighbour unmeasured: its share is not known; checked from its own side when known
            if _need(n, 0) is None:
                continue
            nside = [k for k, x in n["ends"].items() if x and x["shared_with"] == oid][0]
            if (n["ends"]["START"]["a"] < MIN_B - EPS or n["ends"]["END"]["a"] < MIN_B - EPS):
                continue          # the neighbour takes no stock piece (FLAGGED): the pier is this opening's alone
            if _min_use(oid, s, r, recs, i) + _min_use(e["shared_with"], nside, n, recs, 0) > e["a"] + EPS:
                return F_SHARED
    return None


def _one(oid, r, recs):
    o = r["o"]
    base = {"id": oid, "storey": o["storey"], "width_m": o.get("width_m"), "width_bound_m": o.get("width_bound_m"),
            "existence": o["existence"], "cause": o.get("cause") or "", "wall": o.get("wall") or {}}
    pieces = sorted({p for p, _q in r["pieces"] if p is not None})
    base["piece_beside_m"] = pieces
    if r["ends"] is None or not all(r["ends"].values()):
        if not r["widths"]:
            return dict(base, cls=H_WIDTH, why="masonry opening width not established; ends not measured")
        return dict(base, cls=H_ENDS, why=o.get("ends_why") or "jamb ends not measured: bearing not established")
    fits = [_fit(oid, r, recs, i) for i in range(len(r["widths"]))] if r["widths"] else []
    if r["widths"] and all(f is not None for f in fits):
        if len(set(fits)) == 1:
            return dict(base, cls=fits[0], why=_why(fits[0], r))
        return dict(base, cls=F_NOB if F_NOB in fits else fits[0], why=" / ".join(sorted(set(fits))))
    if not r["widths"] or len(r["widths"]) > 1:
        return dict(base, cls=H_WIDTH, why="masonry opening width not established (bound "
                    f"{r['widths']} -> pieces {pieces}); fit differs or not checked across the bound")
    piece = r["pieces"][0][0]
    base["piece_m"] = piece
    ex = o["existence"]
    if ex == "REQUIRED":
        return dict(base, cls=PIECE, why="lintel required (head established) and the piece rests on >= 0.15 m both ends")
    if ex == "HELD":
        return dict(base, cls=IF_BUILT, why="piece fits; whether a lintel is built is HELD: " + base["cause"])
    if ex == "FLAGGED_HEAD_ROOM":
        return dict(base, cls=F_HEAD, piece_m=None, why="piece fits the piers but the head leaves no room for it "
                    "under some soffits: " + base["cause"])
    return dict(base, cls=H_REG, piece_m=None, why="register hold: " + base["cause"])


def _why(cls, r):
    es = r["ends"]
    a = f"ends {es['START']['a']:.3f} / {es['END']['a']:.3f} m"
    return {F_OVER: "needs more than 4.00 m: cast-in-situ or design",
            F_NOB: f"{a}: an end below the 0.15 m minimum bearing (column face / cross wall / free end at the jamb)",
            F_SHORT: f"{a}: the masonry between the stoppers is shorter than the piece",
            F_SHARED: f"{a}: a shared pier cannot carry both neighbours' 0.15 m minimum overhangs"}[cls]


def tables(per, storeys):
    """rule (7): pcs by stock length x storey, ESTABLISHED (PIECE) and AT_MOST (PIECE + PIECE_IF_BUILT)."""
    blank = lambda: OrderedDict((L, OrderedDict((s, 0) for s in storeys)) for L in STOCK)  # noqa: E731
    est, most = blank(), blank()
    by_cls = OrderedDict((c, []) for c in CLASSES)
    for oid, p in per.items():
        if p["cls"] not in by_cls:
            raise PieceError(f"{oid}: class {p['cls']!r} unknown")
        if p["storey"] not in storeys:
            raise PieceError(f"{oid}: storey {p['storey']!r} not a column of {storeys}")
        by_cls[p["cls"]].append(oid)
        if p["cls"] in (PIECE, IF_BUILT):
            L = p.get("piece_m")
            if L not in STOCK:
                raise PieceError(f"{oid}: piece {L!r} is not a stock length")
            most[L][p["storey"]] += 1
            if p["cls"] == PIECE:
                est[L][p["storey"]] += 1
        elif p.get("piece_m") is not None:
            raise PieceError(f"{oid}: {p['cls']} carries a piece (refused: a held / flagged opening is never a piece)")
    tot = lambda t: sum(sum(v.values()) for v in t.values())  # noqa: E731
    assert sum(len(v) for v in by_cls.values()) == len(per), "every opening in exactly one class"
    assert tot(est) == len(by_cls[PIECE]) and tot(most) == len(by_cls[PIECE]) + len(by_cls[IF_BUILT])
    return {"established_nr": est, "at_most_nr": most, "established_total_nr": tot(est), "at_most_total_nr": tot(most),
            "lm_beside_established": OrderedDict((L, round(L * sum(est[L].values()), 6)) for L in STOCK),
            "lm_beside_at_most": OrderedDict((L, round(L * sum(most[L].values()), 6)) for L in STOCK),
            "by_class": by_cls, "class_counts": OrderedDict((c, len(v)) for c, v in by_cls.items())}


def check_asserted_piece(rec, per):
    """rule (8): a record that ASSERTS a piece for an opening is refused unless the class is PIECE / PIECE_IF_BUILT and
    the piece is the rule's."""
    oid = rec.get("id")
    if rec.get("unit", "nr") != "nr":
        raise PieceError(f"{oid}: a lintel count is in pieces (nr); {rec.get('unit')!r} refused")
    q = rec.get("qty", 1)
    if not isinstance(q, int) or isinstance(q, bool) or q != 1:
        raise PieceError(f"{oid}: {q!r} pieces: one piece per opening")
    p = per.get(oid)
    if p is None:
        raise PieceError(f"{oid}: not an opening of the table")
    if p["cls"] not in (PIECE, IF_BUILT):
        raise PieceError(f"{oid}: {p['cls']} ({p['why']}): no stock piece may be given ({rec.get('piece_m')} m refused)")
    if abs(float(rec["piece_m"]) - p["piece_m"]) > EPS:
        raise PieceError(f"{oid}: piece {rec['piece_m']} m is not the rule's {p['piece_m']} m")
    return True


# ============================================================================================ training villa (builder)
LEDGER = ROOT / "research" / "agents_t453" / "out" / "MATERIAL_LEDGER_T453.json"
EVID = HERE / "out" / "JAMB_EVIDENCE_T644.csv"
LINES = ROOT / "research" / "agents_t507" / "out" / "LINE_INDEX_V3_0_57.json"
T630 = ROOT / "research" / "agents_t630" / "out" / "E2E_BOQ_DRY_RUN_T630.json"
T571 = ROOT / "research" / "agents_t571" / "out" / "T571_LINTEL_COUNT.json"
PINS = {"ledger": "ad9bceee3bfdbc12", "t630": None, "lines": None, "t571": None, "evidence": None}
STOREYS = ["GF", "1F", "2F"]

# T-616 R-T616-1 (1) drawn-evidence decisions (MERGED 17559e1b, Checker re-read): lintel REQUIRED where the T-453 ledger
# still says HELD 'head not established'
T616_REQUIRED = {"A-1F-01": "T-616: arch120 BEC, both bearings drawn masonry, no beam band (S8.6 LT-OP-1F-018)",
                 "P-1F-01": "T-616: header lines, L2 under no member (S8.6 LT-OP-1F-021)"}
# register holds
REGISTER_HOLD = {f"L-{s}-01": "register LIFT LANDING DOOR LINTEL (Lead 2026-11-08 00:15): lintel over a lift landing "
                 "door decided per opening (host shaft wall, head vs soffit); supply trade not printed (FR-T608-2)"
                 for s in ("GF", "1F", "2F")}
# R-T581-1 1.1.0: D-GF-09 masonry 0.90 (wall ends) vs D120 frame 1.00 drawn over it: DRAWING CONFLICT, width UNRESOLVED
WIDTH_BOUND = {"D-GF-09": [0.90, 1.00]}
NO_STOCK_PIECE = {"W17": "register CURVED-BAND OPENING HEAD: curved band, chord sagitta 0.711 m > 0 (T-616): no straight "
                  "stock piece; head owned by the structural line carrying the band (FLAGGED, never a piece)"}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def alsenan_openings():
    if sha16(LEDGER) != PINS["ledger"]:
        raise PieceError(f"lintel ledger sha {sha16(LEDGER)} is not the pinned {PINS['ledger']} (stale input)")
    led = json.loads(LEDGER.read_text())["lintels"]
    ev = {}
    for r in csv.DictReader(EVID.open(encoding="utf-8")):
        a = r["v3_available_6dp_m"]
        sw = r["stopper_id"] if r["stopper"] == "OPENING" and r["stopper_id"] in {x["opening_id"] for x in led} else None
        ev.setdefault(r["opening_id"], {})[r["side"]] = {"a_m": float(a) if a else None, "shared_with": sw,
                                                          "stopper": r["stopper"], "stopper_id": r["stopper_id"],
                                                          "measured_gap_m": float(r["clear_width_m"]),
                                                          "band": r["band"], "capped": r["search_capped"] == "YES"}
    ops = []
    for x in led:
        oid = x["opening_id"]
        ex, cause = x["decision"], (x.get("why") or "").strip()
        if oid in T616_REQUIRED and ex == "HELD":
            ex, cause = "REQUIRED", T616_REQUIRED[oid]
        if oid in REGISTER_HOLD:
            ex, cause = "HELD_REGISTER", REGISTER_HOLD[oid]
        if x["decision"] == "FLAGGED":
            ex = "FLAGGED_HEAD_ROOM"
        rec = {"id": oid, "storey": x["floor"], "existence": ex, "cause": cause,
               "wall": {"block": x["block_type"], "t_m": x["wall_t_m"], "kind": x["kind"]}}
        if oid in WIDTH_BOUND:
            rec["width_bound_m"] = WIDTH_BOUND[oid]
            rec["cause"] = (cause + " ; width UNRESOLVED R-T581-1 1.1.0 (frame drawn over masonry)").strip(" ;")
        else:
            rec["width_m"] = x["width_m"]
        e = ev.get(oid)
        if e and "START" in e and "END" in e:
            rec["ends"] = {s: {"a_m": e[s]["a_m"], "shared_with": e[s]["shared_with"]} for s in ("START", "END")}
            rec["evidence"] = e
        else:
            rec["ends"] = None
            rec["ends_why"] = "no V2 band (T-125 MISSING, GF-W30, T-175): jambs not in the masonry capture"
        ops.append(rec)
    return ops


def build():
    ops = alsenan_openings()
    per = classify(ops)
    t = tables(per, STOREYS)
    # the measured gap must give the same piece as the census width (register LINTEL WIDTH BASIS)
    gap_check = []
    for o in ops:
        if o.get("width_m") is not None and o.get("evidence"):
            g = o["evidence"]["START"]["measured_gap_m"]
            p_c, p_g = stock_piece(o["width_m"])[0], stock_piece(g)[0]
            gap_check.append({"id": o["id"], "census_w": o["width_m"], "measured_gap_m": g, "piece_census": p_c,
                              "piece_gap": p_g, "same_piece": p_c == p_g})
    # the 60 candidate lines: element LINTEL:<id>
    idx = {x["line_id"]: x for x in json.loads(LINES.read_text())["lines"]}
    lines = [x for x in json.loads(T630.read_text())["per_line"] if x["item_code"] == "STR.CONC.LINTEL"]
    by_op = {idx[x["line_id"]]["element_id"].split(":", 1)[1]: x for x in lines}
    if set(by_op) != set(per):
        raise PieceError(f"line set != opening set: {sorted(set(by_op) ^ set(per))}")
    m3_cause = OrderedDict()
    for oid, x in by_op.items():
        p = per[oid]
        m3_cause[oid] = {"line_id": x["line_id"], "class_now": x["class"], "held_low_m3": x["held_low"],
                         "held_high_m3": x["held_high"], "piece_class": p["cls"], "piece_m": p.get("piece_m"),
                         "m3_cause_proposed": ("HELD: precast piece governs the payable form under register PRECAST "
                                               "LINTEL PAYABLE FORM (owner lintel rule 2026-11-02); see F-T644-1"
                                               if p["cls"] in (PIECE, IF_BUILT) else
                                               f"HELD: {p['cls']} - {p['why']}")}
    t571 = json.loads(T571.read_text())
    out = OrderedDict(rule=RULE_ID, version=RULE_VERSION, inputs={
        "ledger_T453_sha16": sha16(LEDGER), "jamb_evidence_T644_sha16": sha16(EVID), "line_index_V3_0_57_sha16":
        sha16(LINES), "e2e_T630_sha16": sha16(T630), "t571_sha16": sha16(T571)},
        candidate_lines=len(lines), openings=len(per), stock_m=list(STOCK), min_bearing_m=MIN_B,
        governing_system_note=t571["governing_precast_on_this_villa"],
        tables=t, per_opening=per, no_stock_piece_outside_the_60=NO_STOCK_PIECE, gap_check=gap_check,
        m3_lines=m3_cause,
        appendix_freelancer_implied={"source": "T-571 R-T571-1 (his 54 deducted openings through the same rule; he has "
                                               "no lintel row: implied, not his figure)",
                                     "at_most_nr": t571["freelancer_owner_0.15"]["at_most"]})
    return out


def _keyfix(o):
    if isinstance(o, dict):
        return {(str(k) if not isinstance(k, str) else k): _keyfix(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_keyfix(v) for v in o]
    return o


if __name__ == "__main__":
    res = build()
    dst = HERE / "out" / "T644_LINTEL_PIECES.json"
    dst.write_text(json.dumps(_keyfix(res), indent=1, ensure_ascii=False) + "\n")
    t = res["tables"]
    print(dst)
    print("classes", dict(t["class_counts"]))
    for k in ("established_nr", "at_most_nr"):
        print(k, {L: dict(v) for L, v in t[k].items()}, t[k.replace("_nr", "_total_nr")])
