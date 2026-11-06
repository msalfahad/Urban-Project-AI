"""T-571: PRECAST LINTEL COUNT BY STANDARD LENGTH (owner lintel rule 2026-11-02, UPC-LINTEL-001) per storey, and its
reconciliation in nr with a second opening list (research rule proposal R-T571-1; research only: nothing in engine/ or
tools/ imports it; no candidate line moves; V2.9 + route G and V3.0.58 untouched).

Physical element (ERS s.2.1). One precast lintel (atab) over each masonry opening, resting on built masonry at both ends:
  required length = masonry opening width w + 2 x bearing b (b = 0.15 m company minimum unless a larger approved project
  bearing is named), piece = the SHORTEST stock length >= required among 1.20 / 1.50 / 2.50 / 3.00 / 4.00 m, ONE piece
  per opening, counted in pieces (nr) by length; required > 4.00 m -> FLAGGED (cast-in-situ or design), never forced
  into a 4.00 m piece. The arithmetic is engine.source.company_rulebook_v1.lintel (read only, unchanged).

What this count is and is not.
  - It is the OWNER MANUAL METHOD count. Where a project lintel schedule is printed, the drawing-derived system governs
    (R-T487-1 (1), R-T519-1: PROJECT_RC, cast to length, no stock length): the precast count is then BESIDE, never the
    governing quantity, and the governing precast count is NOT_APPLICABLE (not 0).
  - An opening the engine holds (head not established, held wall / piece) counts only 'at most 1' (column AT_MOST);
    only REQUIRED openings enter the ESTABLISHED column. Held is never 0 and never silently established.
  - An opening that is not in a masonry wall (glazing line, RC, gate, unresolved) takes no lintel (NO_LINTEL, 0 nr by
    cause, listed by name).
  - nr and lm are never mixed: the lm beside each length is nr x stock length, printed apart.

R-T571-1 (every villa; scope: comparing two opening lists through the owner precast rule; provenance UPC-LINTEL-001,
Q-32 A (printed width over drawn), Q-73 (only masonry that physically exists), R-T487-1, R-T519-1, R-T544-1 (one record
per opening), ERS s.3-4):
  (1) each opening id is carried once on each side; a quantity typed in lm where nr is counted, a fractional count, a
      piece longer than the rule allows, or a 4.00 m piece for a FLAGGED opening is refused;
  (2) the two lists are paired inside a comparison group (storey x wall class; a side that does not split a class by
      storey offers its rows to every storey of that class, last), in this order: (a) a verified census key with its
      width and height, certain keys before uncertain ('?') ones; (b) the same width (to 5 mm) on the same storey; (c) the
      same width on an unsplit row; (d) the remaining rows by ascending width on the same storey, then unsplit
      (WIDTH_READ: the pair is one physical opening read at two widths); (e) whatever is left is ONE_LIST_ONLY;
  (3) every pair and leftover gets one signed cause in nr per stock length (ours minus theirs): SAME_PIECE (0),
      WIDTH_READ (the width moves the piece to another length: +1 / -1, total 0), NOT_IN_MASONRY (ours 0 by cause),
      ENGINE_ONLY / OTHER_ONLY (+1 / -1), FLAGGED (no piece on one side), HELD (established column only); the causes sum
      exactly to the difference of the two count tables, length by length (asserted). Steps (b)-(e) are an attribution
      device, not a quantity: they never change either count.
Nothing here names a client, a sheet or a coordinate; the training-villa inputs are pinned by sha and read from the
merged ledgers; the freelancer list is read from .work/private (git-excluded) and only its counts are written.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import company_rulebook_v1 as C  # noqa: E402

RULE_ID = "R-T571-1"
NR, LM = "nr", "lm"
OK, FLAGGED, HELD = "OK", "FLAGGED", "HELD"
REQUIRED, NO_LINTEL = "REQUIRED", "NO_LINTEL"
STATES = (REQUIRED, HELD, FLAGGED, NO_LINTEL)
WIDTH_TOL = 0.005
MAX_W = 12.0
STOCK = tuple(float(x) for x in C.param("UPC-LINTEL-001", "stock_lengths_m")["value"])
UNSPLIT = "UNSPLIT"
CAUSES = ("SAME_PIECE", "WIDTH_READ", "NOT_IN_MASONRY", "ENGINE_ONLY", "OTHER_ONLY", "FLAGGED")


class CountError(ValueError):
    pass


def _num(x, what, hi=MAX_W):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or x != x:
        raise CountError(f"{what}: {x!r} is not a number")
    if x <= 0:
        raise CountError(f"{what}: {x!r} is not positive (held is never 0)")
    if x > hi:
        raise CountError(f"{what}: {x} m is above {hi} m (not a width in metres: mm / cm refused)")
    return float(x)


# ------------------------------------------------------------------------------------------------ the owner rule
def piece(width_m, bearing_m=None, bearing_source=None):
    """one opening -> {'status' OK / FLAGGED / HELD, 'piece_m', 'required_m', 'count'} by UPC-LINTEL-001."""
    if width_m is None:
        return {"status": HELD, "piece_m": None, "required_m": None, "count": None,
                "why": "masonry opening width not established (never 0)"}
    w = _num(width_m, "masonry opening width")
    b = None
    if bearing_m is not None:
        if not str(bearing_source or "").strip():
            raise CountError("a project bearing needs its source (drawing, note or supplier table)")
        b = {"m": bearing_m, "source": bearing_source}
    r = C.lintel(w, bearing=b)
    if r["status"] == FLAGGED:
        return {"status": FLAGGED, "piece_m": None, "required_m": r.get("required_m"), "count": None,
                "why": r["why"]}
    return {"status": OK, "piece_m": r["piece_m"], "required_m": r["required_m"], "count": 1,
            "bearing_m": r["bearing_m"]}


def check_asserted(rec, bearing_m=None, bearing_source=None):
    """a record that ASSERTS a piece / unit is checked against the rule (R-T571-1 (1)); returns the rule's piece."""
    p = piece(rec.get("width_m"), bearing_m, bearing_source)
    unit = rec.get("unit", NR)
    if unit != NR:
        raise CountError(f"{rec.get('id')}: a lintel count is in pieces (nr); {unit!r} refused (nr and lm never mixed)")
    q = rec.get("qty", 1)
    if not isinstance(q, int) or isinstance(q, bool) or q < 1:
        raise CountError(f"{rec.get('id')}: count {q!r} is not a whole number of pieces")
    if "piece_m" in rec and rec["piece_m"] is not None:
        if p["status"] == FLAGGED:
            raise CountError(f"{rec.get('id')}: FLAGGED (needs {p['required_m']} m > {STOCK[-1]} m): no stock piece "
                             f"may be given ({rec['piece_m']} m refused)")
        if abs(float(rec["piece_m"]) - p["piece_m"]) > 1e-9:
            raise CountError(f"{rec.get('id')}: piece {rec['piece_m']} m is not the rule's {p['piece_m']} m")
    return p


# ------------------------------------------------------------------------------------------------ count table
def _blank_table(storeys):
    return OrderedDict((L, OrderedDict((s, 0) for s in storeys)) for L in STOCK)


def count_table(records, storeys, bearing_m=None, bearing_source=None):
    """records [{'id', 'storey', 'width_m', 'state' (REQUIRED / HELD / FLAGGED / NO_LINTEL), optional 'unit', 'qty',
    'piece_m'}] -> {'at_most': {L: {storey: nr}}, 'established': ..., 'flagged': [...], 'no_width': [...],
    'no_lintel': [...], totals, 'lm_beside'}. Each id once; qty expands identical rows of one list (ids id#1..)."""
    seen = set()
    at_most, est = _blank_table(storeys), _blank_table(storeys)
    flagged, no_width, no_lintel, per = [], [], [], []
    for r in records:
        rid = r.get("id")
        if not rid:
            raise CountError("a record without an id")
        if rid in seen:
            raise CountError(f"{rid}: opening named twice (one opening, one lintel)")
        seen.add(rid)
        st = r.get("state", REQUIRED)
        if st not in STATES:
            raise CountError(f"{rid}: state {st!r} is not one of {STATES}")
        if r.get("storey") not in storeys:
            raise CountError(f"{rid}: storey {r.get('storey')!r} is not a column of the table {storeys}")
        p = check_asserted(r, bearing_m, bearing_source)
        q = r.get("qty", 1)
        if st == NO_LINTEL:
            no_lintel.append(rid)
            per.append(dict(r, piece=None, state=st))
            continue
        if p["status"] == HELD:
            no_width.append(rid)
            per.append(dict(r, piece=None, state=st))
            continue
        if p["status"] == FLAGGED:
            flagged.append({"id": rid, "storey": r["storey"], "required_m": p["required_m"], "qty": q})
            per.append(dict(r, piece=None, state=st, rule=FLAGGED))
            continue
        at_most[p["piece_m"]][r["storey"]] += q
        if st == REQUIRED:
            est[p["piece_m"]][r["storey"]] += q
        per.append(dict(r, piece=p["piece_m"], state=st))
    tot = lambda t: sum(sum(v.values()) for v in t.values())  # noqa: E731
    out = {"at_most": at_most, "established": est, "flagged": flagged, "no_width": no_width,
           "no_lintel": no_lintel, "total_at_most_nr": tot(at_most), "total_established_nr": tot(est),
           "lm_beside_at_most": OrderedDict((L, round(L * sum(at_most[L].values()), 6)) for L in STOCK),
           "per_opening": per}
    for t in (at_most, est):
        col = {s: sum(t[L][s] for L in STOCK) for s in storeys}
        assert sum(col.values()) == tot(t)
    return out


def expand(rows, prefix):
    """[(storey, class, n, w, h[, wall_t_m])] of one list -> one record per piece (ids '<prefix>-<storey>-<class>-<k>')."""
    out, k = [], Counter()
    for row in rows:
        storey, cls, n, w, h = row[:5]
        wt = row[5] if len(row) > 5 else None
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise CountError(f"{prefix} {storey} {cls}: row count {n!r} is not a whole number")
        for _ in range(n):
            k[(storey, cls)] += 1
            out.append({"id": f"{prefix}-{storey}-{cls}-{k[(storey, cls)]:02d}", "storey": storey,
                        "wall_class": cls, "width_m": _num(w, f"{prefix} width"), "height_m": h,
                        "wall_t_m": wt, "state": REQUIRED})
    return out


# ------------------------------------------------------------------------------------------------ reconciliation
def _close(a, b):
    return abs(a - b) <= WIDTH_TOL + 1e-12


def _t_ok(o, t):
    a, b = o.get("wall_t_m"), t.get("wall_t_m")
    return a is None or b is None or abs(a - b) < 1e-9


def reconcile(ours, theirs, bearing_m=None, bearing_source=None):
    """ours / theirs: records with 'id', 'storey', 'wall_class', 'width_m', 'state', ours optionally 'key' =
    {'w', 'h', 'certain'}; theirs optionally 'height_m'. Returns pairs, leftovers and the signed causes in nr by
    stock length (ours minus theirs, AT_MOST basis) plus the HELD gap of the ESTABLISHED basis."""
    def pc(r):
        if r["state"] == NO_LINTEL:
            return None
        p = piece(r.get("width_m"), bearing_m, bearing_source)
        return p["piece_m"] if p["status"] == OK else FLAGGED
    groups = sorted({r["wall_class"] for r in ours} | {r["wall_class"] for r in theirs})
    pairs, free_t = [], {r["id"]: r for r in theirs}
    free_o = {r["id"]: r for r in ours}

    def take(o, t, step):
        pairs.append((o, t, step))
        del free_o[o["id"]]
        del free_t[t["id"]]

    for g in groups:
        O = lambda: [r for r in free_o.values() if r["wall_class"] == g]  # noqa: E731
        T = lambda: [r for r in free_t.values() if r["wall_class"] == g]  # noqa: E731
        # (a) census keys, certain first
        for certain in (True, False):
            for o in sorted(O(), key=lambda r: r["id"]):
                k = o.get("key")
                if not k or bool(k.get("certain")) != certain:
                    continue
                cand = [t for t in T() if t["storey"] in (o["storey"], UNSPLIT) and _close(t["width_m"], k["w"])
                        and (k.get("h") is None or t.get("height_m") is None or _close(t["height_m"], k["h"]))]
                cand.sort(key=lambda t: (t["storey"] == UNSPLIT, t["id"]))
                if cand:
                    take(o, cand[0], "a_census_key" if certain else "a_census_key_uncertain")
        # (b) / (c) same width, same storey then unsplit; (d) ascending widths. Each step first among rows whose wall
        # thickness agrees (where both sides state it: same storey, then unsplit), then among any.
        for where, strict in (("same", True), (UNSPLIT, True), ("same", False), (UNSPLIT, False)):
            for o in sorted(O(), key=lambda r: (r["width_m"] if r.get("width_m") else 99, r["id"])):
                if o.get("width_m") is None:
                    continue
                cand = [t for t in T() if _close(t["width_m"], o["width_m"]) and (not strict or _t_ok(o, t))
                        and (t["storey"] == o["storey"] if where == "same" else t["storey"] == UNSPLIT)]
                cand.sort(key=lambda t: t["id"])
                if cand:
                    take(o, cand[0], "b_same_width" if where == "same" else "c_same_width_unsplit")
        for where, strict in (("same", True), (UNSPLIT, True), ("same", False), (UNSPLIT, False)):
            for s in sorted({r["storey"] for r in O()}):
                oo = sorted([r for r in O() if r["storey"] == s and r["state"] != NO_LINTEL
                             and r.get("width_m") is not None], key=lambda r: (r["width_m"], r["id"]))
                tt = sorted([t for t in T() if (t["storey"] == s if where == "same" else t["storey"] == UNSPLIT)],
                            key=lambda t: (t["width_m"], t["id"]))
                for o in oo:
                    t = next((t for t in tt if t["id"] in free_t and (not strict or _t_ok(o, t))), None)
                    if t is not None:
                        take(o, t, "d_width_read" if where == "same" else "d_width_read_unsplit")
    causes = OrderedDict((c, OrderedDict((L, 0) for L in STOCK)) for c in CAUSES)
    flag_nr = {"ours": 0, "theirs": 0}
    rows = []

    def add(cause, L, v):
        if L in causes[cause]:
            causes[cause][L] += v

    for o, t, step in pairs:
        po, pt = pc(o), pc(t)
        if po is None:
            cause = "NOT_IN_MASONRY"
            if pt not in (None, FLAGGED):
                add(cause, pt, -1)
            elif pt == FLAGGED:
                flag_nr["theirs"] += 1
        elif FLAGGED in (po, pt):
            cause = "FLAGGED"
            if po == FLAGGED:
                flag_nr["ours"] += 1
            else:
                add(cause, po, +1)
            if pt == FLAGGED:
                flag_nr["theirs"] += 1
            else:
                add(cause, pt, -1)
        elif po == pt:
            cause = "SAME_PIECE"
        else:
            cause = "WIDTH_READ"
            add(cause, po, +1)
            add(cause, pt, -1)
        rows.append({"ours": o["id"], "theirs": t["id"], "step": step, "storey": o["storey"],
                     "their_storey": t["storey"], "wall_class": o["wall_class"], "w_ours": o.get("width_m"),
                     "w_theirs": t["width_m"], "piece_ours": po, "piece_theirs": pt, "state_ours": o["state"],
                     "cause": cause})
    for o in sorted(free_o.values(), key=lambda r: r["id"]):
        po = pc(o)
        cause = "NOT_IN_MASONRY" if po is None else ("FLAGGED" if po == FLAGGED else "ENGINE_ONLY")
        if po not in (None, FLAGGED):
            add("ENGINE_ONLY", po, +1)
        elif po == FLAGGED:
            flag_nr["ours"] += 1
        rows.append({"ours": o["id"], "theirs": None, "step": "e_one_list_only", "storey": o["storey"],
                     "wall_class": o["wall_class"], "w_ours": o.get("width_m"), "piece_ours": po,
                     "state_ours": o["state"], "cause": cause})
    for t in sorted(free_t.values(), key=lambda r: r["id"]):
        pt = pc(t)
        if pt == FLAGGED:
            flag_nr["theirs"] += 1
        else:
            add("OTHER_ONLY", pt, -1)
        rows.append({"ours": None, "theirs": t["id"], "step": "e_one_list_only", "storey": t["storey"],
                     "wall_class": t["wall_class"], "w_theirs": t["width_m"], "piece_theirs": pt,
                     "cause": "FLAGGED" if pt == FLAGGED else "OTHER_ONLY"})
    # closure: causes sum to the difference of the AT_MOST tables, length by length
    so = sorted({r["storey"] for r in ours} | {UNSPLIT})
    st = sorted({r["storey"] for r in theirs} | {UNSPLIT} | set(so))
    a = count_table([dict(r, wall_class=None, key=None) for r in ours], st, bearing_m, bearing_source)
    b = count_table(theirs, st, bearing_m, bearing_source)
    diff = OrderedDict((L, sum(a["at_most"][L].values()) - sum(b["at_most"][L].values())) for L in STOCK)
    summed = OrderedDict((L, sum(causes[c][L] for c in CAUSES)) for L in STOCK)
    if diff != summed:
        raise CountError(f"reconciliation does not close: table difference {dict(diff)} vs causes {dict(summed)}")
    held_matched = sum(1 for r in rows if r.get("theirs") and r.get("state_ours") in (HELD, FLAGGED)
                       and r["cause"] != "NOT_IN_MASONRY")
    return {"pairs": rows, "causes_nr_by_length": causes, "table_difference_nr_by_length": diff,
            "flagged_no_piece_nr": flag_nr, "ours": a, "theirs": b, "held_or_flagged_in_pairs_nr": held_matched,
            "closes": True}


# ------------------------------------------------------------------------------------------------ training villa
LEDGER = ROOT / "research" / "agents_t453" / "out" / "MATERIAL_LEDGER_T453.json"
CENSUS = ROOT / "research" / "agents_t198" / "OPENINGS_T198.csv"
PINS = {"ledger_sha16": "ad9bceee3bfdbc12", "census_sha16": "d79e6aa5d23edc0e"}
PROJECT_MIN_BEARING = (0.40, "project LINTEL DETAIL 'MIN.40cm' (S8.6 transcription; a minimum, not the built bearing)")


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def wall_class(block_type, t):
    """EXT = white (outer) wall (Q-60: outer white); INT = black block wall (15 or 20 cm)."""
    if block_type == "WHITE":
        return "EXT"
    if block_type == "BLACK":
        return "INT"
    raise CountError(f"block type {block_type!r} unknown")


def engine_records():
    """the V3.0.58 lintel lines' openings (= T-453 r2 ledger, 60 masonry openings: REQUIRED 16, HELD 42, FLAGGED 2)
    plus the census openings not in a masonry wall (NO_LINTEL), each with its census freelancer key."""
    for p, k in ((LEDGER, "ledger_sha16"), (CENSUS, "census_sha16")):
        if sha16(p) != PINS[k]:
            raise CountError(f"{p.name}: sha {sha16(p)} is not the pinned {PINS[k]} (stale input)")
    led = json.loads(LEDGER.read_text())
    cen = {r["ID"]: r for r in csv.DictReader(CENSUS.open(encoding="utf-8"))}
    recs = []

    def key(c):
        fk = (c.get("FREELANCER_KEY") or "").strip()
        if not fk or fk == "none" or not c.get("FREELANCER_W"):
            return None
        return {"w": float(c["FREELANCER_W"]), "h": float(c["FREELANCER_H"]) if c.get("FREELANCER_H") else None,
                "certain": not fk.endswith("?"), "census_key": fk}
    for x in led["lintels"]:
        c = cen[x["opening_id"]]
        recs.append({"id": x["opening_id"], "storey": x["floor"], "wall_class": wall_class(x["block_type"],
                     x["wall_t_m"]), "width_m": x["width_m"], "state": x["decision"], "kind": x["kind"],
                     "wall_t_m": x["wall_t_m"], "why": (x.get("why") or "")[:60], "key": key(c)})
    for n in led["lintel_reconciliation"]["census_openings_not_in_a_masonry_wall"]:
        c = cen[n["opening_id"]]
        w = float(c["WIDTH_M"]) if c.get("WIDTH_M") else None
        recs.append({"id": n["opening_id"], "storey": c["FLOOR"], "wall_class": "EXT" if (c.get("WALL_T_M") or "")
                     in ("0.20", "") else "INT", "width_m": w, "state": NO_LINTEL, "kind": n["kind"],
                     "why": n["why"][:60], "key": key(c)})
    return recs


def freelancer_records(path):
    doc = json.loads(Path(path).read_text())
    if doc.get("schema") != "T571_FREELANCER_OPENINGS_V1":
        raise CountError("freelancer openings: schema T571_FREELANCER_OPENINGS_V1 expected")
    rows = []
    for g in doc["groups"]:
        cls = "EXT" if g["wall_class"] == "EXT" else "INT"
        t = {"INT15": 0.15, "INT20": 0.20}.get(g["wall_class"])
        tot = 0.0
        for n, w, h in g["rows"]:
            rows.append((g["storey"], cls, n, w, h, t))
            tot += n * w * h
        if "printed_total_m2" in g and abs(round(tot, 2) - g["printed_total_m2"]) > 0.006:
            raise CountError(f"freelancer {g['storey']} {g['wall_class']}: rows {tot:.2f} m2 != his total")
    return expand(rows, "FL"), sha16(path)


def build(freelancer_path=None):
    ours = engine_records()
    storeys = ["GF", "1F", "2F", UNSPLIT]
    out = OrderedDict(rule=RULE_ID, pins=PINS, stock_m=list(STOCK))
    for tag, b, src in (("owner_0.15", None, None), ("project_min_0.40", *PROJECT_MIN_BEARING)):
        out[f"engine_{tag}"] = _strip(count_table(ours, storeys, b, src))
    out["governing_precast_on_this_villa"] = ("NOT_APPLICABLE (not 0): the printed project lintel schedule governs "
                                              "every block-wall lintel (R-T487-1 (1), R-T519-1: PROJECT_RC 16 / 16 "
                                              "REQUIRED); this count is the owner manual method BESIDE")
    if freelancer_path and Path(freelancer_path).exists():
        theirs, fsha = freelancer_records(freelancer_path)
        out["freelancer_input_sha16"] = fsha
        for tag, b, src in (("owner_0.15", None, None), ("project_min_0.40", *PROJECT_MIN_BEARING)):
            rc = reconcile(ours, theirs, b, src)
            out[f"freelancer_{tag}"] = _strip(rc["theirs"])
            out[f"reconciliation_{tag}"] = {k: rc[k] for k in ("causes_nr_by_length", "table_difference_nr_by_length",
                                                                "flagged_no_piece_nr", "held_or_flagged_in_pairs_nr")}
            out[f"pairs_{tag}"] = rc["pairs"]
    return out


def _strip(t):
    return {k: v for k, v in t.items() if k != "per_opening"}


def _keyfix(o):
    if isinstance(o, dict):
        return {(str(k) if not isinstance(k, str) else k): _keyfix(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_keyfix(v) for v in o]
    return o


if __name__ == "__main__":
    fp = sys.argv[1] if len(sys.argv) > 1 else None
    res = build(fp)
    dst = Path(__file__).resolve().parent / "out" / "T571_LINTEL_COUNT.json"
    dst.parent.mkdir(exist_ok=True)
    dst.write_text(json.dumps(_keyfix(res), indent=1, ensure_ascii=False) + "\n")
    print(dst)
