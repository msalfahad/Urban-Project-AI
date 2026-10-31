"""T-397: the URBAN_V3033_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.33 (engine.source.arch_v3033), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build); nothing is typed but the line binding
(engine ids, checked against the candidate by the module: a stale binding stops) and the named causes:

  research/agents_t391/summary_t391.json  T-391 (MERGED c3fe8ec8, Verifier 2026-10-31 13:01 UTC Gate A PASS, own
      re-measure of the held-cell panels 35.6054 m2 and the lift shaft 3.24 m2): F1 the held ground-slab cell's bound;
  research/agents_t392/summary_t392.json  T-392 (MERGED cc3c7f08, Verifier 2026-10-31 13:01 UTC Gate A PASS, own
      re-measure of the B8 cell 0.704028 m2 disjoint from the ring and of the CB8 end DOUBLE 0.002767 / GAP 0.00336):
      the T-146 ring-overlap GAP on B8 / B7 / CB1 span 2 and the CB8 drawn net;
  research/agents_t394/summary_t394.json  T-394 (MERGED e27c5d78, Verifier 2026-10-31 14:05 UTC Gate A PASS, own
      re-measure GF CONFLICT drawn 2.070, lift ring 1.600 - 0.500 = 1.100 m2): the line binding of the 15 CONFLICT
      column lines (P1) and the lift ring (P2);
  research/agents_t256/LEDGER_T256.csv  T-256 (MERGED 74c966b1, Verifier 2026-10-24 07:52 UTC Gate A PASS, 15 / 15
      outlines own = drawn sizes, range 8.034 .. 10.119 m3): per member the schedule and drawn section and both m3.

    python3 -I research/agents_t397/t397_inputs.py [project_id]      # prints the rows and the totals
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

T391 = ROOT / "research/agents_t391/summary_t391.json"
T392 = ROOT / "research/agents_t392/summary_t392.json"
T394 = ROOT / "research/agents_t394/summary_t394.json"
T256 = ROOT / "research/agents_t256/LEDGER_T256.csv"
PINS = {T391: "fb953272a9a9510ede588e8a2212bac6e644f50e3e15babb260080ce435ab8a7",
        T392: "59535b8ee8e50c01c154b7a6c76737bcf32df0141c8e7c775c51bf56efef1f61",
        T394: "a4a9223ade3b79184a80dccc4ba2f55348cbe52548806b735beb541a35f248e8",
        T256: "59c4700e826107fbf1f3f1176054f233bb267d4988629b84769b90b1b690e5ea"}
SOURCES = {
    "T-391": {"task": "T-391", "file": "research/agents_t391/summary_t391.json", "sha256": PINS[T391],
              "merge_commit": "c3fe8ec8768e11af522033889102d95c3a56fe92",
              "checker_run": "Verifier 2026-10-31 13:01 UTC session_01E6cPnbviNB76qpeDiEEvMxV (Gate A PASS; F1 held "
                             "bound 0 .. 3.560540 ACCEPTED as a lane I held-range proposal)"},
    "T-392": {"task": "T-392", "file": "research/agents_t392/summary_t392.json", "sha256": PINS[T392],
              "merge_commit": "cc3c7f08128f180a3dad3df50fcf3bb85d7ddfac",
              "checker_run": "Verifier 2026-10-31 13:01 UTC (Gate A PASS; ENGINE_WRONG proposals CB8 0.716937 and "
                             "the T-146 GAP 0.002566 go to lane I)"},
    "T-394": {"task": "T-394", "file": "research/agents_t394/summary_t394.json", "sha256": PINS[T394],
              "merge_commit": "e27c5d784dee4fc91eb0158a53a2b08fabae43fa",
              "checker_run": "Verifier 2026-10-31 14:05 UTC session_01E6cPnaMLNPxb5oviV8rveH (Gate A PASS; P1 and P2 "
                             "go to lane I)"},
    "T-256": {"task": "T-256", "file": "research/agents_t256/LEDGER_T256.csv", "sha256": PINS[T256],
              "merge_commit": "74c966b1955a55ae2ad81322fdb60ab85c9a35bc",
              "checker_run": "Verifier 2026-10-24 07:52 UTC (Gate A PASS: 15 / 15 outlines own = drawn sizes, own "
                             "range 8.034 .. 10.119 m3)"},
}

# the line binding: engine ids of the candidate lines the ledgers name (checked by the module against the candidate;
# a line not standing exactly as bound stops the run). Filled from the V3.0.32 run of record (V3_0_32_BOQ_LINES.json).
BINDING = {}   # line_id -> {"item_code", "element_id", "floor", "evidence_state"}
BINDING_FILE = Path(__file__).resolve().parent / "BINDING_V3032_T397.json"

GS_CAUSE = ("R-T391-5: the held cell's gross holds the 1.80 x 1.80 lift shaft (a pit, T-063) and beam / column strips "
            "round it (not slab, 6.2283 m2); its own slab panels are 35.6054 m2 x the printed T=10cm; the cell stays "
            "HELD (the shaft-corner columns read as free columns, T-042)")
DESIGNER = {"D-16": "D-16 (column C8 section, designer list)",
            "NEW": "column-band item (printed schedule vs drawn outline, T-256 designer list; D-63)"}


def _pinned(p):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != PINS[p]:
        raise SystemExit(f"{p.relative_to(ROOT)}: sha256 differs from the merged file (edited input: stop)")
    return b.decode("utf-8")


def _binding():
    if not BINDING:
        BINDING.update(json.loads(BINDING_FILE.read_text(encoding="utf-8"))["lines"])
    return BINDING


def _expect(lid, **kw):
    b = _binding().get(lid)
    if b is None:
        raise SystemExit(f"{lid}: not in the committed binding {BINDING_FILE.name}")
    return dict({k: b[k] for k in ("item_code", "element_id", "floor", "evidence_state") if k in b}, **kw)


def _area(txt):
    """'GR 25x50' (cm) or '250x500' (mm) -> m2"""
    m = re.search(r"(\d+)x(\d+)", txt)
    a, b = int(m.group(1)), int(m.group(2))
    k = 1e-4 if "x" in txt and re.search(r"[A-Z]", txt) else 1e-6
    return round(a * b * k, 6)


def rows_t391():
    s = json.loads(_pinned(T391))["slab"]
    lid, hi = s["engine_held_line"], s["held_cell_own"]["high_m3"]
    assert abs(s["held_cell_own"]["slab_m2"] * 0.10 - hi) < 1e-6, "T-391: slab panels x 0.10 is not the high"
    return [{"action": "HELD_BOUND", "line_id": lid, "expect": _expect(lid, high=s["engine_held_bound_m3"]),
             "low": 0.0, "high": hi, "source_tasks": ["T-391"], "evidence_status": "HELD", "cause": GS_CAUSE,
             "removed": {"not_slab_m2": s["held_cell_own"]["not_slab_m2"],
                         "m3": round(s["engine_held_bound_m3"] - hi, 6)},
             "kept": {"slab_m2": s["held_cell_own"]["slab_m2"], "thickness_m": 0.10}}]


def rows_t392():
    d = json.loads(_pinned(T392))
    out = []
    for mark, m in d["B_t146_ring_overlap"]["members"].items():
        lid = {"B8 BAND0003": "L-9a55aadc9f0880ae37a7", "B7 BAND0006": "L-cbf53752cfd897c35c2c",
               "CB1 BAND0041.2": "L-9270e8b8860414386adb"}[mark]
        gap = m["rule_R_T392_1"]
        terms = [{"kind": "GAP", "m3": gap["m3"], "name": gap["name"] + " (R-T392-1: no drawn cell overlap)"}]
        rest = round(m["proposed_minus_line_m3"] - gap["m3"], 6)
        if abs(rest) > 1e-9:
            terms.append({"kind": "LEDGER_PRINT", "m3": rest,
                          "name": "the merged beam ledger's 4-decimal print restored to the drawn band (R-T387-7)"})
        out.append({"action": "GAP_RESTORE", "line_id": lid, "expect": _expect(lid, measured_net=m["line_m3"]),
                    "value": m["proposed_m3"], "named_terms": terms, "source_tasks": ["T-392"],
                    "evidence_status": "VERIFIED" if mark.startswith("B8") else "DRAWING-CONFIRMED",
                    "cause": f"{mark.split()[0]} drawn band {m['band_m2']} m2 x 0.75 = {m['drawn_band_m3']} m3; the "
                             f"T-146 ring-overlap deduction came from a band set fitted to an overlay (0.6 mm), the "
                             f"drawn cells hold 0 m2 of the B7 ring (RING-B7 closed BY the B8 face)"})
    c = d["C_small_residuals"]["members"]["CB8 BAND0039"]
    r2 = c["rule_R_T392_2"]
    out.append({"action": "GAP_RESTORE", "line_id": "L-7c1a1da8004c4272ccba",
                "expect": _expect("L-7c1a1da8004c4272ccba", measured_net=c["line_m3"]), "value": c["proposed_m3"],
                "named_terms": [{"kind": "GAP", "m3": r2["gap_m3"],
                                 "name": "CB8 drawn cell short of the band end before the B27 face 326 (less column "
                                         "37D's corner)"},
                                {"kind": "DOUBLE", "m3": r2["double_m3"],
                                 "name": "CB8 band beyond the B27 face 326 inside B27's drawn cell (B27 owns it)"},
                                {"kind": "LEDGER_PRINT", "m3": round(c["proposed_minus_line_m3"] - r2["gap_m3"] +
                                                                     r2["double_m3"], 6),
                                 "name": "the line's 4-decimal print restored to the drawn net"}],
                "source_tasks": ["T-392"], "evidence_status": "VERIFIED",
                "cause": f"CB8 drawn net to the carrier face 326 = cell {c['drawn_cell_to_face_326_m2']} - column 359 "
                         f"{c['column_359_m2']} - column 37D {c['column_37D_in_cell_m2']} m2, x 0.75 (R-T392-2: "
                         f"DOUBLE {r2['double_m3']} and GAP {r2['gap_m3']} m3 reported apart, never netted)"})
    for r in out:   # drop a zero ledger-print term (nothing to name)
        r["named_terms"] = [t for t in r["named_terms"] if abs(t["m3"]) > 1e-9]
    return out


def rows_t394():
    s = json.loads(_pinned(T394))
    led = {r["member"]: r for r in csv.DictReader(_pinned(T256).splitlines())}
    out = []
    for p in s["per_line_engine"]:
        if p["section_status"] != "CONFLICT" or p["state"] != "VALUED":
            continue
        L = led[p["member"]]
        h = float(L["h"])
        sch, drn = round(_area(L["schedule_cm"]) * h, 6), round(_area(L["drawn_mm"]) * h, 6)
        assert {round(float(L["m3_lo"]), 6), round(float(L["m3_hi"]), 6)} == {sch, drn}, p["member"]
        assert abs(p["engine_m3"] - sch) < 1e-6, (p["member"], "candidate not at the schedule end")
        di = DESIGNER["D-16"] if L["designer_item"].startswith("D-16") else DESIGNER["NEW"]
        out.append({"action": "CONFLICT_RANGE", "line_id": p["line_id"],
                    "expect": _expect(p["line_id"], measured_net=p["engine_m3"]),
                    "readings": {"SCHEDULE": sch, "DRAWN": drn}, "member": p["member"], "designer_item": di,
                    "schedule_print": L["schedule_cm"], "drawn_print": f"{L['drawn_mm']} mm", "height_m": h,
                    "source_tasks": ["T-394", "T-256"], "evidence_status": "HELD",
                    "cause": f"{p['storey']} {p['mark']} {p['member']}: schedule {L['schedule_cm']} vs drawn outline "
                             f"{L['drawn_mm']} mm ({L['differs_in']}), x {h} m storey height (T-214 datums); "
                             f"R-COLUMN-EVIDENCE-1: a range, never the schedule end"})
    lift = s["lift"]
    out.append({"action": "MISSING_HELD", "item_code": "STR.CONC.LIFT", "element_id": "LIFT_PIT:WALLS",
                "floor": "FOUNDATION", "physical_element": "lift pit walls (ring between the S-BW outer and inner "
                                                           "faces, net of the four lift column pieces)",
                "beside": lift["net_m2"], "beside_unit": "m2 plan ring net", "source_tasks": ["T-394"],
                "evidence_status": "HELD",
                "held_reason": "the pit depth is printed 'as per lift manufacturer' (ST p.14 lift detail; lift-supplier "
                               "RFI item 1; board refs D-43 / D-63): no height, so no volume; never 0, never a typical "
                               "depth",
                "cause": f"R-T394-6: gross ring {lift['gross_m2']} m2 - lift column pieces {lift['column_pieces_m2']} "
                         f"m2 (owned by the lift neck lines) = {lift['net_m2']} m2",
                "owner_trade": "STRUCTURAL CONCRETE (lane S, ELEMENT_REGISTER); never also a blockwork or WP line",
                "not_this_line": "pit base slab; the pit membrane / protection (T-353, FIN.WP lines); the lift "
                                 "column pieces (neck lines)"})
    return out


def build(project_id=None):
    rows = rows_t391() + rows_t392() + rows_t394()
    return {"schema": "URBAN_V3033_INPUTS_V1", "project_id": project_id,
            "sources": [SOURCES[k] for k in ("T-391", "T-392", "T-394", "T-256")], "rows": rows}


if __name__ == "__main__":
    d = build(sys.argv[1] if len(sys.argv) > 1 else None)
    for r in d["rows"]:
        print(r["action"], r.get("line_id") or r.get("element_id"), r.get("value") or r.get("readings") or
              (r.get("low"), r.get("high")) or r.get("beside"))
