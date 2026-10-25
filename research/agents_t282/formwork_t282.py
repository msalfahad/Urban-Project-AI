"""T-282 (research only, NOT engine code, nothing wired, no BOQ line changed): the side forms of every ground-beam run
of the merged formwork r4 ledger (T-264 MERGED) re-traced on each run's OWN drawn edge lines, each edge closed on its
carrier's drawn face (R-FACE-CLOSE-1 .. R-FACE-END-1 in face_trace.py), as a DELTA ledger against r4.

Two drawing-derived methods side by side (ERS s.2.2; there is no owner manual method for formwork):
  W  edge walk: each edge line walked from mid-span to the carrier V2 names at that end (t282_extract.py `edges`);
  T  traced faces: the boundary of the union of the drawn members (face_trace.trace), each piece to one owner.
r4 used ONE length per run for both sides: the T-242 run length (V2 face to face, cut square at the support's
outermost station, or the T-242 end-adjusted length), with tee covers 0.30 x min(D_in, D) as separate rows.

Per run and side: comparable length T' = traced side + the junction gaps on that side (r4 deducts tees on its own
rows); delta = T' - L_r4 (m); x the run's r4 depth (CALC / FORMED value, or the HELD depth range; annex CONFLICT runs
carry no depth: m only). Free-end faces (FOOTING_FACE / GAP_TO_COLUMN / FREE_END) are NEW faces; end pieces at a
junction are HELD by name. Tee covers: drawn width on the carrier vs the 0.30 r4 used.

Usage:
  python3 -I research/agents_t282/formwork_t282.py --check       synthetic villa Q (not Alsenan): hand values asserted
  python3 -I research/agents_t282/formwork_t282.py <out_dir>      Alsenan delta from committed inputs only"""
from __future__ import annotations

import csv
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import face_trace as FT  # noqa: E402

TOL_AGREE_M = 0.0025      # W and T' agree within 2.5 mm: the walk reads a 45-degree carrier on a +-1 mm strip
#                           (<= 1 mm per end), the trace exactly; 0.5 mm rounding
B_TEE_R4 = 0.30


# ------------------------------------------------------------------------------------------------ villa Q (--check)

def check():
    """villa Q (not Alsenan; mm; every value by hand in the comments). Members 300 wide, depth D = 0.60 m.
    (1) beam G1 along x, edges y = 0 (A) and y = 300 (B), from a column C1 (0..400 x -50..350) to an oblique carrier
        G2 at 45 deg: G2's near face is the line x - y = 4000 (so A ends at x 4000, B at x 4300): A 3.600 m, B 3.900 m;
        a square cut at the shorter edge would bill 2 x 3.600 and leave an 'end face' 0.300 and a pocket.
    (2) the same beam's B edge drawn 0.100 m short of the carrier (x 4200): closed on the carrier (0.100), no end face.
    (3) a column C3 through G1 whose face lies 0.05 mm inside G1's B edge over 0.500 m (x 2000 .. 2500, y 299.95 .. 600):
        the 0.500 m is C3's face (snap), never a 0.05 mm beam strip; B carries 3.900 - 0.500 = 3.400 m.
    (4) a curved band K (ring R 2000 / 2300 about (10000, 0), 0 .. 90 deg) and a straight band G3 (300 wide, along y,
        x 11000 .. 11300, free end at y 5000) framing into it from outside: G3's edges end ON the arc at r = 2300 (two stations:
        y = sqrt(2300^2 - 1000^2) = 2071.232 and sqrt(2300^2 - 1300^2) = 1897.367); the arc between the hits
        = 2300 x (asin(1300/2300) - asin(1000/2300)) = 2300 x (0.600697 - 0.449797) = 0.347070 m is the tee cover on
        the ring (not 0.300); the ring's outer face = 2300 x pi/2 - 0.347070 = 3.265762 m; no earth pocket.
    (5) r2, R-FACE-END-2 (the Verifier's 00:04 case, mirrored on villa Q): G1 ends beside a PARTIAL column P
        (x 4000..4600, y -50..150) that reaches edge A only; edge A stops on P's face (x 4000), edge B runs on 0.300 to
        column Q (x 4300..4700, y 150..400). The strip between P's top face (y 150), edge B and Q's west face is beam:
        END 0.000 (the hull diagonal (4000, 0) -> (4300, 300) would book its part outside P, 0.150 x sqrt2 = 0.2121 m,
        as an end face). A 3.600, B 3.900; P's exposed faces 1.600 - top 0.600 - west 0.150 = 0.850 m, Q's 1.300 -
        bottom 0.300 - west 0.150 = 0.850 m.
    (6) normal: both edges end square at x 4000 beside P alone: the drawn end above P (y 150 .. 300) is a real end
        face, END 0.150 kept; A = B = 3.600.
    (7) adverse: edges end at x 4000 / 4300 with nothing drawn there (a drawn oblique free end): the zone between the
        stations is not closed by any outline, so the drawn end line stands: FREE_END 0.300 x sqrt2 = 0.4243 m, never a
        rectangle invented beyond it."""
    def close(a, b, tol=1e-4):
        assert abs(a - b) <= tol, (a, b)

    col = {"C1": [(0, -50), (400, -50), (400, 350), (0, 350)]}
    # G2: a 45-degree carrier band, near edge x - y = 4000 from (4000, 0)...(4300, 300) extended, far edge 424.26 off
    g2 = {"edges": {"A": ((3700, -300), (4600, 600)), "B": ((4124.26, -300 - 424.26 + 424.26), (5024.26, 600))},
          "width": 300.0}
    # recompute G2's far edge exactly: offset 300 along its normal (1/sqrt2, -1/sqrt2) * 300 = (212.13, -212.13)
    g2["edges"]["B"] = ((3700 + 212.132, -300 - 212.132), (4600 + 212.132, 600 - 212.132))
    g2.update(spans=[(0.0, 1.0, "G2#1")], ends={"start": {"kind": "FREE_END", "carriers": []},
                                                 "end": {"kind": "FREE_END", "carriers": []}})
    g1 = {"edges": {"A": ((400, 0), (4000, 0)), "B": ((400, 300), (4300, 300))}, "width": 300.0,
          "spans": [(0.4, 4.0, "G1#1")],
          "ends": {"start": {"kind": "COLUMN", "carriers": ["C1"]}, "end": {"kind": "BEAM_JUNCTION", "carriers": ["G2"]}}}
    t = FT.trace({"G1": g1, "G2": g2}, col)
    close(t["sides"][("G1#1", "A")], 3.6)
    close(t["sides"][("G1#1", "B")], 3.9)
    assert not [k for k in t["ends"] if k[0] == "G1#1"], t["ends"]    # no end face at the oblique carrier
    FT.square_cut_refused(3.6, 3.9, 3.6, 3.9)
    try:                                                                 # square cut at the shorter edge refused
        FT.square_cut_refused(3.6, 3.9, 3.6, 3.6)
        raise AssertionError("square cut accepted")
    except FT.Refused:
        pass
    # (2) B drawn 0.100 short: closed on the carrier, same faces, no end face
    g1s = dict(g1, edges={"A": ((400, 0), (4000, 0)), "B": ((400, 300), (4200, 300))})
    t2 = FT.trace({"G1": g1s, "G2": g2}, col)
    close(t2["sides"][("G1#1", "B")], 3.9)
    assert [c["closed_m"] for c in t2["closed"]] == [0.1], t2["closed"]
    assert not [k for k in t2["ends"] if k[0] == "G1#1"], t2["ends"]
    # adverse: the B edge drawn 0.700 short (> 2 x the width): not closed, HELD by name, never invented
    g1h = dict(g1, edges={"A": ((400, 0), (4000, 0)), "B": ((400, 300), (3600, 300))})
    t3 = FT.trace({"G1": g1h, "G2": g2}, col)
    assert t3["held"] and t3["held"][0]["side"] == "B", t3["held"]
    # (3) a column 0.05 mm inside the B edge: its face, not a beam strip
    col3 = dict(col, C3=[(2000, -50), (2500, -50), (2500, 299.95), (2000, 299.95)])
    t4 = FT.trace({"G1": g1, "G2": g2}, col3)
    close(t4["sides"][("G1#1", "B")], 3.4)                            # 3.900 - C3's 0.500 (its face, snapped)
    close(t4["sides"][("G1#1", "A")], 3.1)                            # 3.600 - 0.500 where C3 crosses edge A
    close(t4["columns"]["C3"], 0.5 + 2 * 0.05 + 0.5, 1e-4)            # A side 0.5 + two 0.05 returns + B side 0.5
    # adverse: without the snap (0.01 mm) the 0.05 mm sliver turns C3's face into 0.500 m of beam face
    t4x = FT.trace({"G1": g1, "G2": g2}, col3, snap=0.01)
    close(t4x["sides"][("G1#1", "B")], 3.9)
    assert FT.snap_owner(-0.05) == "COLUMN_FACE" and FT.snap_owner(1.2) == "TWO_FACES"
    for bad in (0.0, 5.0, -1.0):
        try:
            FT.snap_owner(0.3, tol=bad)
            raise AssertionError("tolerance %r accepted" % bad)
        except FT.Refused:
            pass
    # (4) a band framing into a ring at two stations
    arcs = {"K": {"cx": 10000.0, "cy": 0.0, "radii": {"o": 2300.0, "i": 2000.0}, "ranges": {"o": (0.0, 90.0),
                                                                                            "i": (0.0, 90.0)}}}
    ya, yb = math.sqrt(2300 ** 2 - 1000 ** 2), math.sqrt(2300 ** 2 - 1300 ** 2)
    g3 = {"edges": {"A": ((11000, 5000), (11000, ya)), "B": ((11300, 5000), (11300, yb))}, "width": 300.0,
          # G3 runs along -y (u = (0, -1)): stations = -y in m; the span from the free end (y 5.000) to the arc
          "spans": [(-5.0, -ya / 1000.0, "G3#1")],
          "ends": {"start": {"kind": "FREE_END", "carriers": []}, "end": {"kind": "BEAM_JUNCTION", "carriers": ["K"]}}}
    t5 = FT.trace({"G3": g3}, {}, arcs)
    cover = 2300 * (math.asin(1300 / 2300) - math.asin(1000 / 2300)) / 1000.0
    close(cover, 0.347070, 1e-6)
    close(t5["arcs"][("K", "o")], 2.3 * math.pi / 2 - cover, 2e-4)
    close(t5["arcs"][("K", "i")], 2.0 * math.pi / 2, 2e-4)
    close(t5["sides"][("G3#1", "A")], 5.0 - ya / 1000.0, 2e-4)        # 2.928768
    close(t5["sides"][("G3#1", "B")], 5.0 - yb / 1000.0, 2e-4)        # 3.102633 (the longer edge, not cut square)
    assert set(t5["ends"]) == {("G3#1", "FREE_END"), ("K", "ARC_END")}, t5["ends"]
    close(t5["ends"][("K", "ARC_END")], 0.6, 1e-4)                    # the ring's two radial ends (0.300 each)
    close(t5["ends"][("G3#1", "FREE_END")], 0.3, 1e-4)                # G3's own free end (y 5000), a real face
    close(FT.tee_width_on_carrier(0.30, 45.0), 0.424264, 1e-6)
    # (5) - (7) R-FACE-END-2: unequal edge ends beside a partial column; square end; drawn oblique free end
    P = [(4000, -50), (4600, -50), (4600, 150), (4000, 150)]
    Q = [(4300, 150), (4700, 150), (4700, 400), (4300, 400)]

    def g1e(b_end, kind, car):
        return dict(g1, edges={"A": ((400, 0), (4000, 0)), "B": ((400, 300), (b_end, 300))},
                    ends={"start": {"kind": "COLUMN", "carriers": ["C1"]}, "end": {"kind": kind, "carriers": car}})
    t6 = FT.trace({"G1": g1e(4300, "COLUMN", ["P", "Q"])}, dict(col, P=P, Q=Q))
    close(t6["sides"][("G1#1", "A")], 3.6)
    close(t6["sides"][("G1#1", "B")], 3.9)
    assert not t6["ends"], t6["ends"]                                  # no end face on an undrawn diagonal
    close(t6["columns"]["P"], 0.85)
    close(t6["columns"]["Q"], 0.85)
    assert [(e["end"], e["m"]) for e in t6["extended"]] == [("end", 0.3)], t6["extended"]
    t7 = FT.trace({"G1": g1e(4000, "COLUMN", ["P"])}, dict(col, P=P))
    assert t7["ends"] == {("G1#1", "COLUMN"): 0.15}, t7["ends"]          # square end beside a partial column: kept
    close(t7["sides"][("G1#1", "B")], 3.6)
    t8 = FT.trace({"G1": g1e(4300, "FREE_END", [])}, col)
    close(t8["ends"][("G1#1", "FREE_END")], 0.3 * math.sqrt(2.0))        # drawn oblique end stands
    assert not t8["extended"], t8["extended"]
    print("formwork_t282 --check: villa Q OK (oblique carrier per edge, short line closed, held beyond cap, "
          "0.05 mm column face, band into a ring at two stations, free end, unequal edge ends beside a partial column)")
    return True


# ------------------------------------------------------------------------------------------------ Alsenan delta

def _rd(rel):
    with open(os.path.join(RES, rel), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(v):
    return None if v in ("", None) else float(v)


def r4_by_span():
    """the r4 ground-beam rows per span: L, per-side values (or both sides), status."""
    out = {}
    for r in _rd("agents_t264/FORMWORK_LINES_R4.csv"):
        if r["element"] != "GROUND_BEAM" or not r["item"].startswith("span "):
            continue
        sid = r["item"].split()[1]
        d = out.setdefault(sid, {"L": None, "rows": []})
        m = re.search(r" L ([0-9.]+)", r["item"])
        if m:
            d["L"] = float(m.group(1))
        side = re.search(r" side ([AB]) ", r["item"] + " ")
        d["rows"].append(dict(status=r["status"], m2=_f(r["m2"]), lo=_f(r["held_lo"]), hi=_f(r["held_hi"]),
                              side=side.group(1) if side else "AB", item=r["item"]))
    return out


def depth_of(d, side):
    """-> (kind, D_lo, D_hi): from the r4 row of that side (or the both-sides row)."""
    L = d["L"]
    for r in d["rows"]:
        if "EARTH_CAST" in r["item"]:
            continue
        if r["side"] == side or r["side"] == "AB":
            k = 1.0 if r["side"] == side else 2.0
            if r["m2"] is not None:
                return ("CALC" if r["status"] == "CALCULATED" else "FORMED"), r["m2"] / (k * L), r["m2"] / (k * L)
            if r["hi"] is not None:
                return "HELD", r["lo"] / (k * L), r["hi"] / (k * L)
            return "CONFLICT", None, None
    return "NONE", None, None


def build():
    with open(os.path.join(HERE, "ALSENAN_EDGE_INPUT.json"), encoding="utf-8") as fh:
        inp = json.load(fh)
    r4 = r4_by_span()
    tr = inp["traced"]
    side_len = {(x["span_id"], x["side"]): x["length_m"] for x in tr["sides"]}
    gaps = {}
    for g in tr["gaps"]:
        gaps.setdefault((g["span_id"], g["side"]), []).append(g["gap_m"])
    ends = {x["span_id"]: x for x in tr["ends"]}             # ring end lookup below
    closed = {(c["member"], c["side"]): c["closed_m"] for c in tr["closed_on_carrier"]}
    rows = []
    for sp in inp["spans"]:
        sid = sp["span_id"]
        d = r4.get(sid)
        if d is None or d["L"] is None:
            raise FT.Refused("span %s has no r4 row" % sid)
        L = d["L"]
        for side in ("A", "B"):
            T = side_len.get((sid, side), 0.0)
            G = round(sum(gaps.get((sid, side), [])), 4)
            Tp = round(T + G, 4)
            W = sp["edges"][side]["length_m"]
            ends_ = sp["edges"][side]["ends"]
            dl = round(Tp - L, 4)
            kind, Dlo, Dhi = depth_of(d, side)
            agree = W is not None and abs(W - Tp) <= TOL_AGREE_M
            run_on = sum(max(0.0, (e.get("drawn_minus_face_mm") or 0.0)) / 1000.0 for e in ends_.values()
                         if e["status"] == "CARRIER_FACE" and e["carrier"] and not e["carrier"].startswith("COL:"))
            if abs(dl) <= TOL_AGREE_M:
                st, cause = "AGREES", "both methods = the r4 length"
            elif W is None:
                st = "DRAWING-CONFIRMED"
                cause = "the carrier V2 names (%s) does not reach this edge (partial-width support); the edge runs " \
                        "on beside it to %s" % (
                            "/".join(e["carrier"] for e in ends_.values() if e["status"] == "NOT_REACHED"),
                            "/".join(x for e in ends_.values() for x in (e.get("drawn_end_touches") or [])
                                     if not x.startswith("FTG:")) or "its drawn end")
            elif agree:
                st = "DRAWING-CONFIRMED"
                cause = "both methods: the edge closes on its carrier's drawn face %+.4f m from the r4 station " \
                        "(the r4 span is cut square at one station)" % dl
            elif Tp > W and abs((Tp - W) - run_on) <= TOL_AGREE_M:
                st = "DRAWING-CONFIRMED"
                cause = "corner: the drawn edge line runs %.4f m past the carrier's near face to the outer corner " \
                        "(the carrier's end lies on this face line)" % run_on
            elif Tp < W:
                st = "DRAWING-CONFIRMED"
                cause = "the edge meets another drawn member %.4f m before the carrier V2 names (walk %.4f): no " \
                        "face there (traced)" % (W - Tp, W)
            else:
                st = "HELD"
                cause = "walk %.4f vs traced %.4f differ: not settled by the drawing reading" % (W, Tp)
            if (sp["band_id"], side) in closed:
                cause += "; drawn line stops %.4f m short of the carrier: closed on it (R-FACE-END-1)" % \
                    closed[(sp["band_id"], side)]
            dm2 = None if Dlo is None else (round(dl * Dlo, 4), round(dl * Dhi, 4))
            rows.append(dict(span_id=sid, side=side, r4_L_m=L, walk_m=W, traced_m=T, gaps_m=G, traced_plus_gaps_m=Tp,
                             delta_m=dl, r4_kind=kind, D_lo=None if Dlo is None else round(Dlo, 4),
                             D_hi=None if Dhi is None else round(Dhi, 4),
                             delta_m2_lo=None if dm2 is None else dm2[0], delta_m2_hi=None if dm2 is None else dm2[1],
                             status=st, cause=cause))
        for e in [x for x in tr["ends"] if x["span_id"] == sid]:
            kind, Dlo, Dhi = depth_of(d, "A")
            real = e["end_kind"] in ("FOOTING_FACE", "GAP_TO_COLUMN", "FREE_END")
            beside_col = e["end_kind"] == "COLUMN"
            rows.append(dict(span_id=sid, side="END", r4_L_m=0.0, walk_m=None, traced_m=e["length_m"], gaps_m=0.0,
                             traced_plus_gaps_m=e["length_m"], delta_m=e["length_m"], r4_kind=kind,
                             D_lo=None if Dlo is None else round(Dlo, 4), D_hi=None if Dhi is None else round(Dhi, 4),
                             delta_m2_lo=None if Dlo is None else round(e["length_m"] * Dlo, 4),
                             delta_m2_hi=None if Dhi is None else round(e["length_m"] * Dhi, 4),
                             status="DRAWING-CONFIRMED" if (real or beside_col) else "HELD",
                             cause=("free end face (%s end): the band stops with nothing drawn against it; in no r4 "
                                    "row" % e["end_kind"]) if real else (
                                 "end beside a partial-width column: the part of the band's drawn end the column does "
                                 "not cover; in no r4 row" if beside_col else
                                 "end piece at a %s end, not settled" % e["end_kind"])))
    # the ring ARC:157+158 (r4: inner 6.5674 CALC, outer 6.2775 FORMED incl. the band-framing zone, cover 0.30)
    arcs = {(a["arc_band"], a["arc"]): a for a in tr["arcs"]}
    fr = next(f for f in inp["arc_framing"] if f["carrier"].startswith("ARC:157+158"))
    o = arcs[(fr["carrier"], "158")]
    i_ = arcs[(fr["carrier"], "157")]
    ring = dict(inner_traced_m=i_["length_m"], inner_r4_m=6.5674, outer_traced_m=o["length_m"],
                framing_arc_m=fr["arc_between_m"], outer_traced_plus_framing_m=round(o["length_m"] +
                                                                                     fr["arc_between_m"], 4),
                outer_r4_m=6.2775, cover_width_r4_m=B_TEE_R4, cover_width_drawn_m=fr["arc_between_m"],
                ring_end_piece=ends.get(fr["carrier"], {}).get("length_m"))
    tees = []
    for g in tr["gaps"]:
        if abs(g["gap_m"] - B_TEE_R4) > TOL_AGREE_M:
            tees.append(dict(g))
    return rows, ring, tees, inp


def totals(rows):
    t = {"delta_m_by_status": {}, "delta_m2": {}}
    for r in rows:
        if r["status"] == "AGREES":
            continue
        k = r["status"] + ("_END" if r["side"] == "END" else "")
        t["delta_m_by_status"][k] = round(t["delta_m_by_status"].get(k, 0.0) + r["delta_m"], 4)
        if r["delta_m2_lo"] is not None:
            kk = "%s %s" % (r["status"], r["r4_kind"])
            lo, hi = t["delta_m2"].get(kk, (0.0, 0.0))
            t["delta_m2"][kk] = (round(lo + r["delta_m2_lo"], 4), round(hi + r["delta_m2_hi"], 4))
        else:
            t["delta_m2"]["%s no depth (annex CONFLICT): m only" % r["status"]] = round(
                t["delta_m2"].get("%s no depth (annex CONFLICT): m only" % r["status"], 0.0) + r["delta_m"], 4)
    return t


def write(outdir):
    rows, ring, tees, inp = build()
    keys = ["span_id", "side", "r4_L_m", "walk_m", "traced_m", "gaps_m", "traced_plus_gaps_m", "delta_m", "r4_kind",
            "D_lo", "D_hi", "delta_m2_lo", "delta_m2_hi", "status", "cause"]
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "DELTA_T282_GROUND_BEAM_SIDES.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r[k] is None else r[k]) for k in keys})
    summ = dict(schema="T282_FORMWORK_EDGE_DELTA", against="T-264 formwork r4 (FORMWORK_LINES_R4.csv), ground-beam "
                "side rows; no BOQ line changed", snap_mm=inp["snap_mm"], rows=len(rows),
                agrees=sum(1 for r in rows if r["status"] == "AGREES"),
                changed=[(r["span_id"], r["side"], r["delta_m"], r["status"]) for r in rows if r["status"] != "AGREES"],
                totals=totals(rows), ring=ring, tee_widths_not_0_30=tees, slivers=inp["slivers"],
                closed_on_carrier=inp["traced"]["closed_on_carrier"], unattributed=inp["traced"]["unattributed"])
    with open(os.path.join(outdir, "summary_t282.json"), "w", encoding="utf-8") as fh:
        json.dump(summ, fh, indent=1, sort_keys=True)
    print(json.dumps(dict(agrees=summ["agrees"], rows=summ["rows"], totals=summ["totals"], ring=ring), indent=1))
    return summ


if __name__ == "__main__":
    if sys.argv[1:2] == ["--check"]:
        check()
    else:
        write(sys.argv[1] if len(sys.argv) > 1 else HERE)
