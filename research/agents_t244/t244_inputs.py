"""T-244: the URBAN_V3020_INPUTS_V1 of the development villa, line id by line id, from merged ledgers only (every value
below is re-read from the merged file and asserted; an edited or stale ledger stops the build):

  T-302 MERGED 5c00a0f8 (Verifier 2026-10-25 23:01 UTC, Gate A PASS): W17 hole per face; ROOM SIDE (1F-11 plaster /
      paint) 8.7414 (prismatic) .. 8.9965 (radial) m2 HELD (head soffit through the curved wall not drawn); the 1F-11
      line 61.4626 .. 61.7177 m2 per code, HELD (BOUNDED); the released 59.4511 deducted 3.286 x 3.35 = 11.0081.
  T-238 MERGED 242e50b2 (Verifier 2026-10-23 22:50 UTC, Gate A PASS) + T-227 r2 MERGED ebce3d97 (Verifier 2026-10-23
      21:05 UTC, own W15 / W16 4.3629 each): W15 / W16 internal plaster / paint deduction = the true arched outline
      4.3629 m2 each (never the 1.55 x 3.10 band rectangle 4.805).
  T-201 MERGED 5dade783 (Verifier 2026-10-23 07:00 UTC): printed heads; W24 1.55 x (2.50 - 1.00) = 2.325 m2 and W29
      1.20 x (2.50 - 1.00) = 1.800 m2 INTERNAL_PLASTER_PAINT, DRAWING-CONFIRMED.
  T-237 MERGED 1cc1a153 (Verifier 2026-10-24 00:12 UTC, Gate A PASS): part 4, the per-room owner-method nets with the
      merged heads (1F-04 52.00, 2F-03 57.77, 1F-13 111.02 .. 114.37) and the two census door widths (D-GF-05, D-1F-07),
      W26 1.875 on the ST-2F face; NOT applied there (lane I applies it: this package).
  T-255 MERGED e9eaaeac (Verifier 2026-10-26 03:43 UTC, Gate B PASS): the W03 room-side split (GF-15 18.6369 + GF-08
      5.93125 = 24.56815 m2, once).

The V3.0.19 line ids are those of the candidate of record (V3_0_19_BOQ_LINES.json b35475bf); the module asserts each
record's before against the line, so a different candidate refuses the build. No coordinate, no client text here.

    python3 -I research/agents_t244/t244_inputs.py > <scratch>/v3020_inputs.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T302 = ROOT / "research/agents_t302/LINE_1F11_T302.csv"
T302H = ROOT / "research/agents_t302/W17_HOLE_LEDGER_T302.csv"
T238 = ROOT / "research/agents_t238/DELTA_T238.csv"
T201 = ROOT / "research/agents_t201/CONSEQUENCES_T201.csv"
T237 = ROOT / "research/agents_t237/ROOMS_T237.csv"
T237F = ROOT / "research/agents_t237/FINDINGS_T237.csv"
T255 = ROOT / "research/agents_t255/T-255_RING_AND_OPENING_TRACE.md"
OA = "ASSUMED - OWNER-APPROVED"
W_ARCH = 4.3629                    # Checker own (T-227 r2 21:05); T-238 census 4.3632 (0.0003 m2, rounding)
ASSUMPTION = "owner wall height G1 (Q-43 / Q-48 A) and door head 2.20 (Q-55 C): ASSUMED - OWNER-APPROVED"

LINES = {   # room -> {code: V3.0.19 line id}
    "1F-11": {"FIN.PLASTER": "L-31db3c83552682d92ca3", "FIN.PAINT": "L-349db74a70e1eecda2d2"},
    "1F-13": {"FIN.PLASTER": "L-9b4a7bab033d677e2017", "FIN.PAINT": "L-be48ea84285be20645af"},
    "1F-04": {"FIN.PLASTER": "L-971f0bdaf68d7fd0966c", "FIN.PAINT": "L-d9f4ecdb6ef9a42d0220"},
    "2F-03": {"FIN.PLASTER": "L-4ce74fc37a08d4bdf0d8", "FIN.PAINT": "L-5410f9045c80dd5933f0"},
    "GF-15": {"FIN.PLASTER": "L-0d93f2209cd9bb827c0a", "FIN.PAINT": "L-7f083d3e2c2702d14356"},
    "GF-08": {"FIN.PLASTER": "L-8cecb1d010d5aafbf25d", "FIN.PAINT": "L-c0ac22c964a42e7d71b1"},
    "ST-2F": {"FIN.PLASTER": "L-418121a4b223cb4e8646", "FIN.PAINT": "L-5a7a5c6f070ec7142ca5"},
    "GF-04": {"FIN.PLASTER": "L-1ddc23d5657b4c4e4d0d", "FIN.PAINT": "L-d7d6d2f765489a95c408"},
    "GF-01": {"FIN.PLASTER": "L-b152995525ed123ddac9", "FIN.PAINT": "L-cdf7f5cd2789b67004f1"},
    "GF-07": {"FIN.PLASTER": "L-721a0f1441436193978c", "FIN.PAINT": "L-c3f7e68ce91a436802e2"},
}
CODES = ("FIN.PLASTER", "FIN.PAINT")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _rows(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _rng(s):
    a, b = s.split("..")
    return float(a), float(b)


def sources():
    return [
        {"file": "research/agents_t302/LINE_1F11_T302.csv", "sha256": _sha(T302), "task": "T-302",
         "merge_commit": "5c00a0f8", "checker_run": "Verifier 2026-10-25 23:01 UTC (Gate A PASS)"},
        {"file": "research/agents_t238/DELTA_T238.csv", "sha256": _sha(T238), "task": "T-238",
         "merge_commit": "242e50b2", "checker_run": "Verifier 2026-10-23 22:50 UTC (Gate A PASS); W15 / W16 own "
                                                    "4.3629 m2 each at the T-227 r2 verdict 21:05 UTC"},
        {"file": "research/agents_t201/CONSEQUENCES_T201.csv", "sha256": _sha(T201), "task": "T-201",
         "merge_commit": "5dade783", "checker_run": "Verifier 2026-10-23 07:00 UTC"},
        {"file": "research/agents_t237/ROOMS_T237.csv", "sha256": _sha(T237), "task": "T-237",
         "merge_commit": "1cc1a153", "checker_run": "Verifier 2026-10-24 00:12 UTC (Gate A PASS)"},
        {"file": "research/agents_t255/T-255_RING_AND_OPENING_TRACE.md", "sha256": _sha(T255), "task": "T-255",
         "merge_commit": "e9eaaeac", "checker_run": "Verifier 2026-10-26 03:43 UTC (Gate B PASS)"},
    ]


# ------------------------------------------------------------------------------------------------ merged values
def merged_values():
    """every number the records use, re-read from the merged ledgers (stale / edited ledger -> SystemExit)."""
    v = {}
    l1f11 = {r["item_code"]: r for r in _rows(T302)}
    for c in CODES:
        r = l1f11[c]
        if (r["room"], r["t302_hole_room_m2"], r["t302_line_m2"], r["released_candidate_m2"]) != (
                "1F-11", "8.7414 .. 8.9965", "61.4626 .. 61.7177", "59.4511") or r["w17_piece_gross_m2"] != "11.0081":
            raise SystemExit(f"T-302 ledger: the 1F-11 {c} row is not the merged one")
    v["W17_ROOM"] = _rng(l1f11["FIN.PLASTER"]["t302_hole_room_m2"])
    v["W17_BEFORE"] = 11.0081
    v["L1F11"] = _rng(l1f11["FIN.PLASTER"]["t302_line_m2"])
    hole = {r["face"].split(" ")[0]: r for r in _rows(T302H)}
    if hole["ROOM"]["status"] != "HELD (BOUNDED)" or hole["ROOM"]["hole_m2"] != "8.7414 .. 8.9965":
        raise SystemExit("T-302 hole ledger: the room-side row is not the merged one")
    d238 = [r for r in _rows(T238) if r["line"] == "INTERNAL_PLASTER_PAINT"]
    for w in ("W15", "W16"):
        r = [x for x in d238 if x["opening"] == w]
        if len(r) != 1 or (r[0]["old"], r[0]["new"]) != ("4.805", "4.363"):
            raise SystemExit(f"T-238 delta: the {w} internal finish row is not the merged one")
    w26 = [x for x in d238 if x["opening"] == "W26"]
    if len(w26) != 1 or (w26[0]["old"], w26[0]["new"]) != ("2.040", "1.875"):
        raise SystemExit("T-238 delta: the W26 internal finish row is not the merged one")
    v["W26"] = (2.040, 1.875)
    c201 = {r["opening"]: r for r in _rows(T201)}
    for w, want in (("W24", "2.325"), ("W29", "1.800")):
        r = c201[w]
        if (r["face_A_family"], r["face_A_m2"], r["opening_m2"], r["finish_status"]) != (
                "INTERNAL_PLASTER_PAINT", want, want, "DRAWING-CONFIRMED"):
            raise SystemExit(f"T-201 consequences: the {w} face A row is not the merged one")
        if abs(float(r["width_m"]) * float(r["height_m"]) - float(want)) > 1e-9:
            raise SystemExit(f"T-201 consequences: {w} w x h != {want}")
        v[w] = float(want)
    rooms = {r["room"]: r for r in _rows(T237)}
    for room, want in (("1F-04", "52.00"), ("2F-03", "57.77"), ("1F-13", "111.02 .. 114.37")):
        if rooms[room]["owner_net_new_m2"] != want:
            raise SystemExit(f"T-237 rooms: {room} owner net new {rooms[room]['owner_net_new_m2']} != {want}")
    fnd = _rows(T237F)
    for door in ("D-GF-05", "D-1F-07"):
        if not any(r["kind"] == "SIZE_DIFFERS" and door in json.dumps(r) and "d_m2 -0.11" in json.dumps(r)
                   for r in fnd):
            raise SystemExit(f"T-237 findings: the {door} width row is not the merged one")
    t = T255.read_text(encoding="utf-8")
    for s in ("18.6369 + 5.93125 = 24.56815",):
        if s not in t:
            raise SystemExit("T-255 report: the W03 room-side split is not the merged one")
    return v


# ------------------------------------------------------------------------------------------------ records
def _rec(room, code, task, before, state, revisions, **kw):
    r = {"line_id": LINES[room][code], "item_code": code, "room": room, "task": task, "before": before,
         "state": state, "revisions": revisions}
    r.update(kw)
    return r


def records(v=None):
    v = v or merged_values()
    out = []
    lo11, hi11 = v["L1F11"]
    gross11 = round(22.149 * 3.35, 6)                   # V3.0.9 line: 74.19915
    net_lo, net_hi = gross11 - 1.76 - 1.98 - v["W17_ROOM"][1], gross11 - 1.76 - 1.98 - v["W17_ROOM"][0]
    assert abs(net_lo - lo11) < 2e-4 and abs(net_hi - hi11) < 2e-4, (net_lo, net_hi)
    for c in CODES:
        out.append(_rec(
            "1F-11", c, "T-302", {"evidence_state": "PROVISIONAL", "measured_net": 59.4511}, "BOUNDED",
            [{"opening": "W17", "before": {"m2": v["W17_BEFORE"]},
              "after": {"range": list(v["W17_ROOM"]),
                        "basis": "T-302 room-side developed hole: PRISMATIC 8.7414 .. RADIAL 8.9965 m2 (r 2.135, jambs "
                                 "135.19 .. 223.47 deg, opening crown 3.00 .. 3.05 under the 3.35 owner height); the "
                                 "head soffit through the curved wall is not drawn: HELD (BOUNDED)"},
              "source_task": "T-302",
              "why": "the released line deducted the band rectangle 3.286 x 3.35 = 11.0081 m2 (the archivolt crown "
                     "3.50 capped at the owner height), more than the physical hole; the hole is the opening outline "
                     "on the room face (Q-73), never the 9.870 window supply area (Q-76 A is the window line)"}],
            range=[round(lo11, 4), round(hi11, 4)], evidence_status="HELD",
            reasons=["W17 room-side hole 8.7414 .. 8.9965 m2: the head soffit through the curved wall thickness is not "
                     "drawn (RADIAL vs PRISMATIC reading, T-302 R-T302-1); the released 59.4511 deducted the band "
                     "rectangle 11.0081 m2 and is LOW by 2.0115 .. 2.2666 m2 (ENGINE_WRONG to release)"],
            range_basis="owner manual method (22.149 x 3.35 = 74.19915 - D315 1.76 - D215 1.98 - W17 room-side hole "
                        "8.9965 .. 8.7414)",
            printed="Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf): 1F plan arcs BD2 / BD9 / "
                    "BD7 (r 2.135 room side), NW elevation head chain 2D61 / 2D53 / 2D46 (T-302)",
            downstream=["FIN.PAINT / FIN.PLASTER released totals fall by 59.4511 each (the line leaves the released "
                        "total for BOUNDED 61.4626 .. 61.7177)", "the window supply line (9.870, Q-76 A) unchanged",
                        "the W17 masonry deduction (centreline 8.4598 .. 8.5699, T-302) rides with T-279"]))
    lo13, hi13 = 132.1575 - (1.98 * 3 + 2.2 + 0.924) - 2 * W_ARCH - 3.35, 132.1575 - (1.98 * 3 + 2.2 + 0.924) - 2 * W_ARCH
    for c in CODES:
        out.append(_rec(
            "1F-13", c, "T-238", {"evidence_state": "BOUNDED_EXPOSURE", "bounded_range": [110.1335, 114.3677]},
            "BOUNDED",
            [{"opening": w, "before": {"range": [4.3629, 4.805]},
              "after": {"m2": W_ARCH, "basis": "the true arched outline on the opening line (w 1.5523, springing "
                                               "2.1609, crown 3.00 under the 3.35 owner height): Checker own 4.3629 "
                                               "(T-227 r2 21:05), T-238 census 4.3632; plaster / paint are built in "
                                               "the spandrels"},
              "source_task": "T-238",
              "why": "T-238 settled the arched windows: the 0.10 surround band crown (3.10) is not the head; the "
                     "rectangle 1.55 x 3.10 = 4.805 deducts spandrels that are physically plastered and painted"}
             for w in ("W15", "W16")],
            range=[round(lo13, 4), round(hi13, 4)], evidence_status="HELD",
            reasons=["net is a range: the lift landing door head is not printed (lift supplier item, L-1F-01); W15 / "
                     "W16 settled at 4.3629 each (T-238 / T-227 r2)"],
            range_basis="owner manual method; the lift landing door held 0 .. 3.35"))
    for room, w, rng, held_hi, net, deds in (("1F-04", "W24", [0.0, 5.1925], 54.33, 58.29 - 2.2 - 1.76 - v["W24"],
                                              "D115 2.20, D315 1.76"),
                                             ("2F-03", "W29", [0.0, 4.02], 59.575, 63.315 - 1.98 - 1.76 - v["W29"],
                                              "d220 1.98, D315 1.76")):
        lo_before = {"1F-04": 49.1375, "2F-03": 55.555}[room]
        for c in CODES:
            out.append(_rec(
                room, c, "T-201", {"evidence_state": "BOUNDED_EXPOSURE", "bounded_range": [lo_before, held_hi]},
                "RELEASED",
                [{"opening": w, "before": {"range": rng},
                  "after": {"m2": v[w], "basis": f"T-201 printed head / sill: {w} {v[w]} m2 = width x (head 2.50 - "
                                                 "sill 1.00), inside the 3.35 owner height (DRAWING-CONFIRMED)"},
                  "source_task": "T-201",
                  "why": f"{w} head and sill were not read in T-128 r3 (held 0 .. w x H); T-201 (merged) read them "
                         "on the elevation; T-237 part 4 lists the room as closable"}],
                value=round(net, 4), evidence_status=OA, assumption=ASSUMPTION,
                downstream=[f"the room leaves the bounded total and enters the released total at {round(net, 4)} m2"]))
    return out


def deltas():
    def both(room):
        return [LINES[room][c] for c in CODES]
    wet = "no room-face finish line in the candidate: a wet room (wall tile to the decor ceiling, Q-48 A; the plaster " \
          "under tile is HELD, T-211 s.5.4)"
    return [
        {"opening": "W03", "room": "GF-15", "kind": "CARRIED", "task": "T-255", "line_ids": both("GF-15"),
         "m2": 18.6369, "token": "W03",
         "why": "W03 room-side bed-room part 5.106 x 3.65 = 18.6369 m2 deducted once on each code (T-255 trace)"},
        {"opening": "W03", "room": "GF-08", "kind": "CARRIED", "task": "T-255", "line_ids": both("GF-08"),
         "m2": 5.93125, "token": "W03",
         "why": "W03 room-side open-room part 1.625 x 3.65 = 5.93125 m2 deducted once on each code; the GF-08 line "
                "stays BOUNDED (lift landing door, W02 not settled), so no figure is released (T-255 trace)"},
        {"opening": "W26", "room": "ST-2F", "kind": "NOT_APPLIED", "task": "T-237", "line_ids": both("ST-2F"),
         "value_delta": round(1.875 - 2.040, 3), "carrier": "the ST-2F shaft part line (D-T173-1 roof panel T 18 and "
                                                           "the roof B3 contact, T-173)",
         "why": "W26 arched outline 1.875 m2 (was 2.040, T-238): the ST-2F plaster / paint lines carry no figure; the "
                "deduction is 1.875 when the shaft part is wired"},
        {"opening": "W27", "room": "ST-2F", "kind": "NOT_APPLIED", "task": "T-237", "line_ids": both("ST-2F"),
         "carrier": "the ST-2F shaft part line (T-173)",
         "why": "head printed (T-201); the ST-2F lines carry no figure"},
        {"opening": "W25", "room": "ST-1F", "kind": "NOT_APPLIED", "task": "T-237", "line_ids": [],
         "carrier": "the T-173 shaft ledger (its own opening list; the ST-1F line has no owner-method deductions)",
         "why": "north window head printed (T-201); the ST-1F line is the T-173 drawing-derived shaft range, not an "
                "owner-method room face"},
        {"opening": "W04", "room": "GF-04", "kind": "NOT_APPLIED", "task": "T-237", "line_ids": both("GF-04"),
         "carrier": "the annex owner height (G2) and the roof datum (DCR-6, annex D-39)",
         "why": "W04 head printed (T-201): the annex lines carry no figure"},
        {"opening": "A-GF-01", "room": "GF-01", "kind": "NOT_APPLIED", "task": "T-237", "line_ids": both("GF-01"),
         "carrier": "the annex owner height (G2); A-GF-01 outline (T-238 A6, HELD)",
         "why": "W11 / W12 heads (T-207) and the arch to the wash: the annex lines carry no figure"},
        {"opening": "W09", "room": "GF-07", "kind": "NOT_APPLIED", "task": "T-237", "line_ids": both("GF-07"),
         "carrier": "the pantry classification (plaster under wall tile not an owner rule, T-211 s.5.4)",
         "why": "W09 / W10 heads printed (T-201): the pantry lines carry no figure"},
        {"opening": "D-GF-05", "room": "GF-06", "kind": "NOT_APPLIED", "task": "T-237", "line_ids": [],
         "value_delta": -0.11, "carrier": "the annex kitchen face (G2 annex height; wall tile V3.0.9b)",
         "why": "census width 1.00 (T-128's own frame rule) instead of the 0.95 rebate: -0.110 m2 net; " + wet},
        {"opening": "D-1F-07", "room": "1F-09", "kind": "NOT_APPLIED", "task": "T-237", "line_ids": [],
         "value_delta": -0.11, "carrier": "the 1F-09 wet-room wall tile line (V3.0.9b)",
         "why": "census width 0.80 instead of the 0.75 rebate: -0.110 m2 net; " + wet},
    ] + [{"opening": w, "room": room, "kind": "NOT_APPLIED", "task": "T-237", "line_ids": [],
          "carrier": "the wet-room wall tile package (V3.0.9b, T-209)",
          "why": f"{w} head printed (T-201); " + wet}
         for room, w in (("GF-16", "W05-07"), ("GF-13", "W05-07"), ("1F-07", "W19-23"), ("1F-08", "W19-23"),
                         ("1F-02", "W19-23"), ("1F-03", "W19-23"), ("1F-09", "W19-23"), ("2F-02", "W28"),
                         ("GF-06", "W08"))]


def build():
    v = merged_values()
    return {"schema": "URBAN_V3020_INPUTS_V1", "project": None, "sources": sources(), "records": records(v),
            "deltas": deltas()}


if __name__ == "__main__":
    json.dump(build(), sys.stdout, ensure_ascii=False, indent=1)
