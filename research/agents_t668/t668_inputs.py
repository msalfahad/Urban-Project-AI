"""T-668: the URBAN_V3064_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.64 (engine.source.arch_v3064), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build):

  research/agents_t666/out/T666_LEDGER.json   T-666 (MERGED 06e2e736, Verifier 2026-11-10 05:56 Gate A PASS, own DXF
      re-measure of 3 of the 5 lengths): 5 unlabelled beam pieces restated to the drawn edge lengths with one owner
      per junction square (R-T666-1) and two depth exposures beside; the boundary band drawn under every building
      stretch at a disjoint level: owned once, bound unchanged (R-T666-2);
  research/agents_t659/out/T659_LEDGER.json   T-659 (MERGED 907ace46, Verifier 2026-11-09T21:54Z Gate A PASS): the
      band's drawn bound 5.6392 .. 11.0328 m3 (its open residual closed by T-666);
  research/agents_t667/out/T667_LEDGER.json   T-667 (MERGED b89ea23f, Verifier 2026-11-10 05:05 Gate A PASS, own pool
      outline / footing overlap re-measure): the NEW pool blinding line LOWER_ONLY >= 0.915529 m3, the pool steps
      HELD blank;
  research/agents_t665/out/LINE_INDEX_V3_0_63.json  T-665 (Gate B PASS, MERGED 12acd3d4): the class and range each
      line carries on the candidate V3.0.63 (the binding; asserted again on the live run);
  research/agents_t669/out/T669_LEDGER.json   T-669 (MERGED 8cb64551, Verifier 2026-11-10 09:56Z Gate A PASS, own
      DXF re-read of the corner): F-T665-1, the annex SE ground-beam corner square owned by run #1 BAND0012.1 (its
      AT_LEAST floor 0.090 -> 0.1125 m3); its roof-column part (b) is not this row's and is not wired;
  research/agents_t469/DOWNGRADES_SNAPSHOT.json  the Checker downgrade DG-6dd9f1caba1ca77d (APPLIED on V3.0.63) that
      holds the RELEASED band point 7.2204 at export: materialised whole (one line) by the restatement (R-T665-1 (g)).

Typed here are only the RFI question of each held class (the designer items the ledgers name; ERS s.2.7 not met: no
owner question) and the reasons. F-C-T667-1 (Checker residual 0.00005 m3 on the pool floor): the ledger's figure is
wired and the method is stated (the shared pit-layer area is the T-597 integral that values the VERIFIED pit line
itself, so the netting uses the same measure as the line it nets against); the Checker's sampled 0.915479 is beside.

    python3 -I research/agents_t668/t668_inputs.py [project_id]      # prints the inputs summary
"""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

T666 = ROOT / "research/agents_t666/out/T666_LEDGER.json"
T659 = ROOT / "research/agents_t659/out/T659_LEDGER.json"
T667 = ROOT / "research/agents_t667/out/T667_LEDGER.json"
INDEX = ROOT / "research/agents_t665/out/LINE_INDEX_V3_0_63.json"
DGS = ROOT / "research/agents_t469/DOWNGRADES_SNAPSHOT.json"
T669 = ROOT / "research/agents_t669/out/T669_LEDGER.json"
PINS = {T669: "e3f2dd96b133de85ee2bae7b9bb2667dce6a478bcf3e707746f9851ec828ef3a",
        T666: "99a906c2d2dd1804d6996d961396a4b5d5e59c9ed03d6d8829b2f98e0374a720",
        T659: "50e51242f4c39bc74ec34f370db67e50297c6bcc18c1038dc3fdeb20797a743f",
        T667: "4adfc23d76b7be32f5da98cbda5db7822c9b8b7dc3ed75dea91d92a50b6309b9",
        INDEX: "cd062bfe777af2393228f31893b71ae7032c8d0e6c1bcbe41b0194e36a8fe8d8",
        DGS: "817326399e5b9ffff1d727b9599dff46d1f917c930e759c37e1d5721f0f85766"}
SOURCES = {
    "T-666": {"task": "T-666", "file": "research/agents_t666/out/T666_LEDGER.json", "sha256": PINS[T666],
              "merge_commit": "06e2e73699033818664aa15d919cffd871da5b68",
              "checker_run": "Verifier 2026-11-10 05:56 (Gate A PASS: own ST7757 dxf re-measure BAND0008.1 1.400, "
                             "BAND0001.3 1.130, BAND0006.1 3.100 AGREE; bounds L x 0.20 x 0.40 .. 1.20 0.6264 .. "
                             "1.8792 AGREE; beside 0.014 / 0.0405 AGREE; band under all four stretches 43.60 m, levels "
                             "disjoint, deduction 0 AGREE)"},
    "T-659": {"task": "T-659", "file": "research/agents_t659/out/T659_LEDGER.json", "sha256": PINS[T659],
              "merge_commit": "907ace4674b91de176419d3fd02628fde6d86b45",
              "checker_run": "Verifier 2026-11-09T21:54Z (Gate A PASS: own read ST p.10 B.W 20x60, p.14 G.B 20x40, "
                             "91.94 m closed, 21.45 m in footings; band 5.6392 .. 11.0328 AGREE; stretch residual "
                             "named, closed by T-666)"},
    "T-667": {"task": "T-667", "file": "research/agents_t667/out/T667_LEDGER.json", "sha256": PINS[T667],
              "merge_commit": "b89ea23f65816117cc8be82189a92aaddbccb770",
              "checker_run": "Verifier 2026-11-10 05:05 (Gate A PASS: own pool outline 10.935562 m2, grown in plot "
                             "11.851050 AGREE; pit-layer share own 2.696261 vs 2.695761 m2, F-C-T667-1 residual "
                             "0.00005 m3 named; steps HELD blank AGREE; 6 HELD blinding lines untouched)"},
    "T-669": {"task": "T-669", "file": "research/agents_t669/out/T669_LEDGER.json", "sha256": PINS[T669],
              "merge_commit": "8cb64551ce8b27223a9fa9c5fd20f67974d3609a",
              "checker_run": "Verifier 2026-11-10 09:56Z (Gate A PASS: own ST7757 dxf entities on the annex SE corner "
                             "square: 10B and 7D1 reach F8, 7D4 ends on 7D1, no column: the square is in run #1 "
                             "BAND0012.1, 1.50 x 0.30 x 0.25 = 0.1125 m3, residual 0 AGREE)"},
}
SCHEMA = "URBAN_V3064_INPUTS_V1"
BAND = "L-6290a9f3d93f38cd46d6"
BAND_DG = "DG-6dd9f1caba1ca77d"
STEPS = "L-b62a7065645589011141"
TEMPLATE = "L-98eb2d58075c9eddf1b4"          # the candidate's footing (pit) blinding line, the shared-plan line
COLUMNS = {"418": "L-53f223b06db14ac41d47", "41E": "L-33a9b7728781fcba12e2", "424": "L-c10e2945d582b5a03126"}
B23_1F = "L-5ca0573b64ee1cb22e0e"            # P-C:BEAMS:1F:BAND0031.2 (B23 45x75), RELEASED
Q_PIECE = ("Q-61 C(4): the unlabelled piece past a support has no mark: which breadth-0.20 schedule row (depth "
           "0.40 .. 1.20) governs it (designer; D-04)")
Q_BAND = ("Q-28: the boundary band section (B.W 20x60, ST p.10, vs typical G.B 20x40, ST p.14) and its founding level "
          "'AS PER EXCAVATION DEPTH' (whether the 21.45 m inside footings shares their elevation) are not printed "
          "(designer)")
Q_POOL = ("C4 / C6: the pool blinding projection beyond the printed 5 + 5 cm wrap is drawn, not dimensioned (ST p.7 "
          "N.I.S.); the founding levels of the footings under the pool vs the pool formation are not printed: one "
          "blinding layer or two (designer)")
CORNER = "L-6bf14711798e5af93594"            # P-C:GROUND_BEAMS:GROUND:BAND0012.1 (the census row's full id)
CORNER_NEIGHBOURS = ("L-3284f44000c02179ace7", "L-402dbe61d1c924144a3c")   # BAND0012.2 / BAND0015, unchanged
Q_D35 = ("D-35: the annex exterior ground-beam depth: the literal +0.25 .. N.G. reading cannot hold the printed "
         "exterior section (designer)")
Q_STEPS = "no pool step drawn or dimensioned on the pool detail, plan or section: designer item (access to the water)"


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load():
    for p, s in PINS.items():
        if _sha(p) != s:
            raise SystemExit(f"{p.relative_to(ROOT)}: sha256 {_sha(p)[:8]} is not the pinned {s[:8]} (edited file)")
    return tuple(json.loads(p.read_text(encoding="utf-8")) for p in (T666, T659, T667, INDEX, DGS, T669))


def _f(x):
    return None if x in (None, "") else float(Decimal(str(x)))


def _expect(ix):
    return {"item_code": ix["item_code"], "element_id": ix["element_id"], "unit": ix["unit"], "class": ix["class"],
            "low": ix["held_low"], "high": ix["held_high"]}


def _owner_line(sq):
    if sq["owner_kind"] == "PIECE":
        return sq["owner"]
    if sq["owner_kind"] == "COLUMN":
        col = sq["owner"].split(" ")[0]
        return COLUMNS[col]
    if sq["owner_kind"] == "THROUGH":
        if not sq["owner"].startswith("BAND0031.2"):
            raise SystemExit(f"through owner {sq['owner']} is not the bound B23 1F span")
        return B23_1F
    raise SystemExit(f"owner kind {sq['owner_kind']}")


def _junction(p, sq):
    """the physical square, named once whoever owns it: a column's own outline, a through member's crossing, or the
    piece's own end"""
    if sq["owner_kind"] == "COLUMN":
        return f"column {sq['owner'].split(' ')[0]} outline"
    if sq["owner_kind"] == "THROUGH":
        return f"{sq['owner'].split(' ')[0]} x {p['element']}"
    return f"{p['element']} {sq['square']}"


def _piece(p, ix):
    lo, hi = _f(p["after"][0]), _f(p["after"][1])
    if abs(ix["held_low"] - p["before_V3_0_62"][0]) > 1e-6 or abs(ix["held_high"] - p["before_V3_0_62"][1]) > 1e-6:
        raise SystemExit(f"{p['line_id']}: the ledger's before {p['before_V3_0_62']} is not the candidate's range")
    L = _f(p["owned_length_m"])
    if abs(L * 0.20 * 0.40 - lo) > 1e-6 or abs(L * 0.20 * 1.20 - hi) > 1e-6:
        raise SystemExit(f"{p['line_id']}: {lo} .. {hi} is not {L} x 0.20 x 0.40 .. 1.20")
    squares = [{"square": s["square"], "owner": s["owner"], "owner_kind": s["owner_kind"],
                "owner_line": _owner_line(s), "junction": _junction(p, s), "area_m2": _f(s["area_m2"])}
               for s in p["squares"]]
    exps = [{"what": x["what"], "low": _f(x["m3"][0]), "high": _f(x["m3"][1]),
             "why": "closes with the piece depth (D-04); beside, never in the range (R-T666-1)"}
            for x in p["exposures_beside"]]
    return {"action": "BOUND", "line_id": p["line_id"], "source_tasks": ["T-666"],
            "member": f"beam {p['element']} (unlabelled piece, R-T660-2)", "expect": _expect(ix),
            "after": {"low": lo, "high": hi},
            "basis": (f"drawn edge length {p['owned_length_m']} m ({p['length_term']}) x 0.20 x 0.40 .. 1.20; "
                      f"junction squares: " + "; ".join(f"{s['square']} -> {s['owner']}" for s in p["squares"]))[:900],
            "why_held": "unlabelled piece past a support: breadth-0.20 schedule rows 0.40 .. 1.20 deep x the drawn "
                        "length to the square it owns (R-T660-2, R-T666-1)",
            "question": Q_PIECE, "squares": squares, "exposures_beside": exps}


def _band(t666, t659, ix, dg):
    b, row = t666["band"], next(r for r in t659["rows"] if r["line_id"] == BAND)
    lo, hi = _f(row["low"]), _f(row["high"])
    if [_f(x) for x in b["after"]] != [lo, hi] or [_f(x) for x in b["T659_bound"]] != [lo, hi]:
        raise SystemExit("band: the T-666 'after' is not the T-659 bound")
    if ix["class"] != "HELD" or ix["held_low"] != 7.2204 or ix["held_high"] != 7.2204:
        raise SystemExit(f"band: the index no longer carries the downgraded point 7.2204 ({ix})")
    shared = "; ".join(f"{s['stretch']} {s['band_centre_line_m']} m {s['relation']} deduction {s['deduction_m3']}"
                       for s in b["stretches"])
    return {"action": "BOUND", "line_id": BAND, "source_tasks": ["T-659", "T-666"],
            "member": "boundary wall foundation band (closed round the plot)",
            "expect": dict(_expect(ix), **{"class": "RELEASED"}),
            "after": {"low": lo, "high": hi},
            "basis": (f"low: {row['low_basis']}; high: {row['high_basis']}; drawn under every building stretch "
                      f"({b['shared_centre_line_m']} m: {shared}), {b['owned_once']}")[:900],
            "why_held": "section (B.W 20x60 vs typical 20x40) and founding level not printed: bounded, not a value "
                        "(T-659); the released 7.2204 point (one plot side lost, Checker downgrade) is restated to "
                        "the drawn bound, the downgrade materialised whole",
            "question": Q_BAND, "downgrade": _dg(dg),
            "freelancer_beside": {"m3": 8.604, "class": "WITHIN", "owner_provisional_Q28A_m3": 8.459}}


def _dg(d):
    return {"downgrade_id": d["downgrade_id"], "verdict_commit": d["checker"]["verdict_commit"],
            "checker_run": f"{d['checker']['routine']} {d['checker']['run_token']} ({d['time']})",
            "file": "research/agents_t469/DOWNGRADES_SNAPSHOT.json", "sha256": PINS[DGS],
            "line_ids": list(d["line_ids"]), "line_content_sha256": d["line_content_sha256"],
            "engine_qty": d["engine_qty"], "reason": d["reason"][:300]}


def _pool(t667, ix):
    pc, row = t667["piece"], t667["rows"][0]
    assert row["line_id"].startswith("NEW:") and row["status"] == "LOWER_ONLY" and row["value"] is None, row
    lo = _f(row["low"])
    net = _f(pc["plan_distinct_m2"])
    if abs(_f(pc["own_layer_in_plot_m2"]) - _f(pc["counted_overlap_m2"]) - net) > 1e-6 or \
            abs(net * _f(pc["t_m"]) - lo) > 1e-6:
        raise SystemExit("pool blinding: plan net x t is not the ledger's floor")
    if pc["counted_line"] != TEMPLATE:
        raise SystemExit(f"pool blinding: the shared-plan line is {pc['counted_line']}, not {TEMPLATE}")
    t = ix[TEMPLATE]
    also = [{"what": b["what"], "m3": b["m3"], "status": b["status"]} for b in row["beside"]
            if not b["what"].startswith("T-183")]
    also.append({"what": "Checker own pit-layer share 2.696261 m2 (sampled grown arc): floor 0.915479",
                 "m3": "0.915479", "status": "F-C-T667-1, residual 0.00005 m3 (-0.005 %), not the line's figure: the "
                                             "netting uses the T-597 integral that values the pit line itself"})
    return {"action": "ADD_LOWER_ONLY", "key": "POOL-1-BLINDING", "source_tasks": ["T-667"],
            "template_line": TEMPLATE,
            "add": {"item_code": row["item_code"], "unit": row["unit"], "element_id": row["element_id"],
                    "floor": row["floor"], "physical_element": "10 cm plain concrete blinding under the pool base "
                                                               "(ST p.7 '10cm PLAIN CONCRETE.')"},
            "basis": row["low_basis"][:600],
            "why_held": row["item"][:600], "question": Q_POOL,
            "beside": {"kind": "AT_LEAST_M3", "value": lo, "basis": (
                f"{pc['own_layer_in_plot_m2']} m2 own layer in plot - {pc['counted_overlap_m2']} m2 shared with the "
                f"VERIFIED pit layer = {pc['plan_distinct_m2']} m2 x {pc['t_m']} m (Q-26 A flat floor)")},
            "beside_also": also,
            "netted_against": [{"line_id": TEMPLATE, "item_code": t["item_code"], "class": t["class"],
                                "value": t["measured_net"], "overlap_m2": _f(pc["counted_overlap_m2"]),
                                "why": "one blinding layer in plan: the pit layer under F8 / F4 / FN is already in "
                                       "the footing blinding line (R-T478-1 b, R-T667)"}],
            "freelancer_beside": {"class": "NOT_LIKE_FOR_LIKE", "note": "no pool row (a plot plate)"}}


def _steps(t667, ix):
    row = t667["rows"][1]
    assert row["line_id"] == STEPS and row["status"] == "HELD_BLANK", row
    if ix["class"] != "HELD" or ix["held_low"] is not None:
        raise SystemExit(f"steps: {ix}")
    return {"action": "CONFIRM", "line_id": STEPS, "source_tasks": ["T-667"], "member": "pool steps",
            "expect": _expect(ix), "basis": f"{row['item']} ({Q_STEPS})"[:600]}


def _column(col, lid, ix):
    if ix["class"] != "HELD" or ix["held_low"] is not None:
        raise SystemExit(f"column {col}: {ix}")
    return {"action": "CONFIRM", "line_id": lid, "source_tasks": ["T-666"], "member": f"column {col} (2F)",
            "expect": _expect(ix),
            "basis": f"owns the crossing-band junction square inside its outline to the slab top (UP-CONC-JOINT-001, "
                     f"R-T666-1); its line stays as the candidate carries it"}


def _corner(t669, ix):
    """F-T665-1 (T-669 (a), R-T669-1): the annex SE corner square belongs to run #1 BAND0012.1: its AT_LEAST floor
    1.20 -> 1.50 m x 0.30 x 0.25. The ledger's owner id (a_corner_square.owner.line_id) is not a candidate id (its
    8-character prefix and member agree with the candidate line; F-T668-1): the line is bound by the census row's id."""
    a = t669["a_corner_square"]
    row = next(r for r in t669["c_census"]["rows"] if r["line_id"] == CORNER)
    own = a["owner"]
    if own["line_id"][:10] != CORNER[:10] or not ix[CORNER]["element_id"].endswith(own["member"].split(" ")[-1]):
        raise SystemExit(f"corner owner {own} is not the candidate line {CORNER} {ix[CORNER]['element_id']}")
    lo0, lo = _f(a["floor_m3"]["before_V3_0_63"]), _f(a["floor_m3"]["after"])
    if _f(row["beside"]["AT_LEAST_M3"]) != lo0 or _f(row["beside_after_T669"]["AT_LEAST_M3"]) != lo:
        raise SystemExit("corner: ledger floor and census row disagree")
    span = _f(a["span_m"][1])
    if abs(span * 0.30 * 0.25 - lo) > 1e-9 or abs(_f(a["span_m"][0]) * 0.30 * 0.25 - lo0) > 1e-9:
        raise SystemExit("corner: floor is not span x 0.30 x 0.25")
    if ix[CORNER]["class"] != "HELD" or ix[CORNER]["held_low"] is not None:
        raise SystemExit(f"corner: {ix[CORNER]}")
    return {"action": "LOWER_ONLY", "line_id": CORNER, "source_tasks": ["T-669"],
            "member": "ground beam BAND0012.1 (annex exterior, run #1)", "expect": _expect(ix[CORNER]), "after": {},
            "basis": (f"run #1 {a['owner']['run']}: drawn span {a['span_m'][1]} m to the outer corner (was "
                      f"{a['span_m'][0]}) x 0.30 x 0.25 literal floor; {a['why']}")[:900],
            "why_held": "D-35 annex exterior depth: the high end is open (R-T658-3); only the literal floor is drawn",
            "question": Q_D35,
            "beside": {"kind": "AT_LEAST_M3", "value": lo,
                       "basis": f"{a['span_m'][1]} x 0.30 x 0.25 (R-T669-1: owns the annex SE corner square)"},
            "squares": [{"square": "annex SE corner", "owner": CORNER, "owner_kind": "PIECE", "owner_line": CORNER,
                         "junction": "annex SE G.B corner", "area_m2": 0.09}]}


def _neighbour(lid, ix):
    if ix["class"] != "HELD" or ix["held_low"] is not None:
        raise SystemExit(f"corner neighbour {lid}: {ix}")
    return {"action": "CONFIRM", "line_id": lid, "source_tasks": ["T-669"], "member": f"ground beam {ix['element_id']}",
            "expect": _expect(ix), "basis": "meets the annex SE corner square without owning it (T-669 (a)): unchanged"}


def build(project_id=None):
    t666, t659, t667, index, dgs, t669 = _load()
    if index["candidate_version"] != "ARCH_TAKEOFF_V3.0.63":
        raise SystemExit(f"index is {index['candidate_version']}")
    ix = {ln["line_id"]: ln for ln in index["lines"]}
    applied = {d["downgrade_id"] for d in index["downgrades"] if d.get("status") == "APPLIED"}
    dg = next(d for d in (dgs["downgrades"] if isinstance(dgs, dict) else dgs) if d["downgrade_id"] == BAND_DG)
    if BAND_DG not in applied or dg["line_ids"] != [BAND]:
        raise SystemExit(f"{BAND_DG} is not an APPLIED one-line downgrade of the band on V3.0.63")
    ents = [_piece(p, ix[p["line_id"]]) for p in t666["pieces"]]
    ents.append(_band(t666, t659, ix[BAND], dg))
    ents.append(_pool(t667, ix))
    ents.append(_steps(t667, ix[STEPS]))
    ents += [_column(c, lid, ix[lid]) for c, lid in sorted(COLUMNS.items())]
    ents.append(_corner(t669, ix))
    ents += [_neighbour(lid, ix[lid]) for lid in CORNER_NEIGHBOURS]
    if ix[B23_1F]["class"] != "RELEASED" or ix[B23_1F]["item_code"] != "STR.CONC.BEAM":
        raise SystemExit(f"B23 1F span {ix[B23_1F]}")
    _assert_ledger_totals(ents, t666)
    return {"schema": SCHEMA, "project_id": project_id, "sources": list(SOURCES.values()), "entries": ents,
            "index_sha256": PINS[INDEX],
            "not_wired": [{"what": "T-669 (b) roof-column lower ends (5 2F columns 1.6362 .. 2.295 m3, R-T669-2)",
                           "task": "T-669", "why": "outside this row (junction / band / pool / corner square): the 6 "
                           "upper-only column lines keep their V3.0.63 state; a lane I row wires them"}]}


def _assert_ledger_totals(ents, t666):
    ps = [e for e in ents if e["source_tasks"] == ["T-666"] and e["action"] == "BOUND"]
    lo, hi = round(sum(e["after"]["low"] for e in ps), 6), round(sum(e["after"]["high"] for e in ps), 6)
    want = tuple(_f(x) for x in t666["pieces_totals"]["after"])
    assert (lo, hi) == want, ((lo, hi), want)
    b4 = round(sum(e["expect"]["low"] for e in ps), 6), round(sum(e["expect"]["high"] for e in ps), 6)
    assert b4 == tuple(_f(x) for x in t666["pieces_totals"]["before"]), b4


def summary(doc):
    from collections import Counter
    c = Counter((e.get("expect", e.get("add"))["item_code"], e["action"]) for e in doc["entries"])
    return {"entries": len(doc["entries"]), "by_code_action": {f"{k[0]} {k[1]}": v for k, v in sorted(c.items())},
            "not_wired": doc["not_wired"]}


if __name__ == "__main__":
    print(json.dumps(summary(build(sys.argv[1] if len(sys.argv) > 1 else None)), indent=1))
