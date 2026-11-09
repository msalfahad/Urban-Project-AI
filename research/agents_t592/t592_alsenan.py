"""T-592 development-villa build (research, unwired): the EXTERNAL DOOR STEP as ONE payable quantity (R-T592-1) at the 4
house doors and the fence gate, on the candidate of record ARCH_TAKEOFF_V3.0.58 (no line changed).

    .work/venv/bin/python -I research/agents_t592/t592_alsenan.py [--check]

Reads only repository files (sha256-pinned): T592_DRAWN.json (this task's own read of the architectural DXF by handle,
t592_extract.py), the T-325 sill / threshold ledger (strip widths and owning lines), and the merged T-584 output (the
before figures and his door-step totals as numbers). Writes out/T592_DOOR_STEPS.json; --check rebuilds it
byte-identical. Signs: ours - his."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t592_rules as R  # noqa: E402

DRAWN = "research/agents_t592/T592_DRAWN.json"
LEDGER = "research/agents_t325/SILL_THRESHOLD_LEDGER_T325.csv"
T584 = "research/agents_t584/out/T584_STEPS.json"
PINS = {DRAWN: "7589369898adf162", LEDGER: "ef6f2cb0c0d7619e", T584: "242b8e0d3fdbf271"}
OUT = HERE / "out" / "T592_DOOR_STEPS.json"
D = R.D
# the owning line per opening (T-325 ledger / T-584 openings); the gate has no strip line (T-325: NO_LINE, UNBOUND)
HOUSE = ("D-GF-01", "D-GF-03", "D-GF-05", "D-GF-09")
GATE = "D-GF-15"
TOL = D("0.010")         # drafting tolerance between a drawn edge and the gap less the jambs (m)


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    for p, h in PINS.items():
        if _sha(p) != h:
            raise R.RuleError(f"input {p} changed ({_sha(p)} != {h}): restate the inputs")


def S(x):
    return None if x is None else str(x)


def _ledger():
    out = {}
    with open(ROOT / LEDGER, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["component"] == "THRESHOLD":
                out[r["opening"]] = r
    return out


def _region(levels):
    return [t for t in levels]                      # figure strings; handles carried beside


def opening(oid, o, led, t584):
    """One opening -> its record (R-T592-1)."""
    face = o["wall_gap_face0"]
    other = o["wall_gap_face_depth"]
    if face["gap_m"] is not None:
        gap, gap_src = face["gap_m"], f"step face: wall-line ends {face['ends'][0]} / {face['ends'][1]}"
        if other["gap_m"] is not None and other["gap_m"] != face["gap_m"]:
            raise R.RuleError(f"{oid}: wall gap differs between the faces ({face['gap_m']} / {other['gap_m']}): HELD")
    elif other["gap_m"] is not None:
        gap = other["gap_m"]
        gap_src = (f"step face carries a line through the opening ({', '.join(face['through'])}); gap from the other "
                   f"face: wall-line ends {other['ends'][0]} / {other['ends'][1]}")
    else:
        raise R.RuleError(f"{oid}: no wall gap on either face: HELD")
    front = [e for e in o["edges_on_face0"] if e["layer"] == "5" and abs(e["offset_from_face_m"]) <= 0.01]
    comp = [e for e in o["edges_on_face0"] if e["layer"] == "2" and abs(e["offset_from_face_m"] - 0.05) <= 0.01]
    if len(comp) != 1:
        raise R.RuleError(f"{oid}: companion edge not single: HELD")
    if front:
        if len(front) != 1 or front[0]["length_m"] != comp[0]["length_m"]:
            raise R.RuleError(f"{oid}: front edge and companion differ: HELD")
        nose, nose_src = front[0]["length_m"], f"front edge {front[0]['handle']} (layer 5) = companion {comp[0]['handle']}"
    else:
        nose = comp[0]["length_m"]
        nose_src = (f"face line runs through the opening; visible edge from the companion {comp[0]['handle']} "
                    "(layer 2, 0.050 uphill; equal to the front edge at every house door)")
    hi = o["levels_reachable_high"]
    lo = o["levels_reachable_low"]
    if len(hi) != 1:
        raise R.RuleError(f"{oid}: inside level not single in its region: HELD")
    high = next(iter(hi))
    outside = R.outside_level(list(lo))
    rec = R.door_step(oid, gap, nose, high, outside)
    if outside["status"] == "DRAWING-CONFIRMED":
        R.riser_from(high, next(iter(lo)), list(lo))      # the riser's low figure is in the low-side region
    # frame jambs inside the wall gap: jamb width less the part of it drawn over the masonry (block wider than the gap)
    g = face if face["gap_m"] is not None else other
    inside = [max(D(j) - D(ov), D(0)) for j, ov in zip(o["jambs_m"], g["ends_vs_block_span_m"])]
    residual = rec["piece_minus_edge"] = rec["jambs_lm"] - sum(inside)
    if abs(residual) > TOL:
        raise R.RuleError(f"{oid}: piece - edge {rec['jambs_lm']} != jambs inside the gap {sum(inside)}: HELD")
    conflict = None
    if any(D(ov) != 0 for ov in g["ends_vs_block_span_m"]):
        conflict = (f"door block span {S(D(o['block_span_m']))} drawn in a wall gap of {S(D(gap))} (block over the "
                    f"masonry {g['ends_vs_block_span_m'][0]} / {g['ends_vs_block_span_m'][1]}): the stone fills the wall "
                    f"gap; the door size is the door schedule's question, not the stone's; edge vs gap - jambs residual "
                    f"{S(residual)} m named as drafting (within {S(TOL)})")
    lg = led.get(oid)
    strip_w = None if lg is None or not lg["width_m"] else D(lg["width_m"])
    if strip_w is not None and strip_w != rec["payable_lm"]:
        raise R.RuleError(f"{oid}: piece length {rec['payable_lm']} != T-325 strip width {strip_w}: HELD")
    before = t584["openings"].get(oid, {}).get("piece", {})
    return {
        "opening": oid, "insert": o["insert"], "block": o["block"],
        "owning_line": t584["openings"].get(oid, {}).get("line") if oid != GATE else None,
        "t325_strip_width_m": S(strip_w), "t325_state": None if lg is None else lg["state"],
        "payable_lm": S(rec["payable_lm"]), "payable_basis": rec["payable_basis"], "wall_gap_source": gap_src,
        "nosing_lm": S(rec["nosing_lm"]), "nosing_basis": rec["nosing_basis"], "nosing_source": nose_src,
        "frame_jambs_m": [S(D(j)) for j in o["jambs_m"]], "jambs_inside_gap_m": [S(x) for x in inside],
        "edge_vs_gap_residual_m": S(residual), "drawing_conflict": conflict, "wall_depth_m": S(D(o["wall_depth_m"])),
        "inside_level": high, "inside_handles": hi[high],
        "outside_region_levels": {k: v for k, v in lo.items()}, "outside_status": outside["status"],
        "riser_m": S(rec["riser_m"]), "riser_m2": S(rec["riser_m2"]),
        "riser_m2_bound": None if rec["riser_m2_bound"] is None else [S(x) for x in rec["riser_m2_bound"]],
        "nr": rec["nr"], "status": rec["status"],
        "before_T584": {"lm": before.get("lm"), "riser_m": before.get("riser_m"), "m2": before.get("m2"),
                        "status": before.get("status"), "bound": before.get("bound")},
    }


def build():
    pins()
    drawn = json.loads((ROOT / DRAWN).read_text(encoding="utf-8"))
    t584 = json.loads((ROOT / T584).read_text(encoding="utf-8"))
    led = _ledger()
    recs = {oid: opening(oid, drawn["openings"][oid], led, t584) for oid in HOUSE + (GATE,)}
    house = [recs[k] for k in HOUSE]
    tot = {
        "house_payable_lm": S(sum(D(r["payable_lm"]) for r in house)),
        "house_nosing_lm_attribute": S(sum(D(r["nosing_lm"]) for r in house)),
        "house_riser_m2": S(sum(D(r["riser_m2"]) for r in house)),
        "house_nr": sum(r["nr"] for r in house),
        "gate_payable_lm": recs[GATE]["payable_lm"], "gate_nosing_lm_attribute": recs[GATE]["nosing_lm"],
        "gate_riser_m2": recs[GATE]["riser_m2"],
    }
    # the payable line refuses a double booking (asserted on the built records)
    R.payable_line([{"opening": r["opening"], "payable_lm": D(r["payable_lm"])} for r in recs.values()])
    door_his = [t for t in t584["tables"]["doors"]["lm"] if t["id"] == "DOOR_STEPS"][0]
    nr_his = [t for t in t584["tables"]["doors"]["nr"] if t["id"] == "DOOR_STEPS"][0]
    his_lm, his_nr = D(door_his["his"]), D(nr_his["his"])
    ours_lm = D(tot["house_payable_lm"]) + D(tot["gate_payable_lm"])
    compare = {
        "unit": "lm", "his_door_steps_lm": S(his_lm), "his_nr": S(his_nr),
        "ours_house_lm": tot["house_payable_lm"], "ours_gate_lm": tot["gate_payable_lm"], "ours_total_lm": S(ours_lm),
        "gap_house_lm": S(D(tot["house_payable_lm"]) - his_lm), "gap_with_gate_lm": S(ours_lm - his_lm),
        "nr_ours_with_gate": tot["house_nr"] + recs[GATE]["nr"],
        "pct": None,
        "verdict": "UNRESOLVED (SCOPE): his 6 pieces carry no door id; matching by figure stays refused (R-T577-1). "
                   "The basis question is closed on OUR side: one payable lm = the installed piece (wall gap)",
        "his_m2_column": "count x length in an area column (UNIT, T-584): never compared as m2",
    }
    before_after = {
        "house_lm": {"before": "3.5 (visible edge, T-584)", "after": tot["house_payable_lm"], "delta": S(D(tot["house_payable_lm"]) - D("3.5")),
                     "cause": "the 4 x 2 frame jambs of 0.05 under which the stone runs (piece = wall gap)"},
        "house_riser_m2": {"before": "0.390 + D-GF-09 HELD 0 .. 0.270", "after": tot["house_riser_m2"],
                           "cause": "riser x piece length (not the edge); D-GF-09 outside level +0.15 now read in "
                                    "its region (R-T592-1 (d))"},
        "gate": {"before": "0.900 lm / 0.135 m2 (edge basis)", "after": f"{tot['gate_payable_lm']} lm / {tot['gate_riser_m2']} m2",
                 "cause": "gate re-read: wall gap 1.000 on the fence's inner face (the outer face line runs through), "
                          "companion 0.900, low region +-0.00 (3 datum marks), high region +0.15"},
    }
    fix_rows = [
        {"id": "FR-T592-1", "replaces": "FR-T584-2",
         "what": "on each owning threshold line (D-GF-01 L-b3933a51bd95e9bc542b, D-GF-03 L-74cd61b430eec9933d15, "
                 "D-GF-05 L-c8b5c7f742b22388339e, D-GF-09 L-8111095f6db78f0e674b): step payable lm = the line's own "
                 "strip width (1.000 / 0.900 / 1.000 / 0.900 = 3.800 lm, nr 4) + riser m2 beside (0.570 m2); visible "
                 "nosing 3.500 lm as an attribute only; no second step line; material by the strip's specification (HELD)",
         "status": "DRAWING-CONFIRMED quantities; material HELD"},
        {"id": "FR-T592-2", "what": "gate D-GF-15: NO_LINE today (T-325 UNBOUND). Strip evidence: wall gap 1.000 x fence "
                                     "depth 0.200 = 0.200 m2; step 1.000 lm, riser 0.150 m2, nosing 0.900 attribute; owner "
                                     "trade and material HELD (B13 boundary vs threshold family: Lead ruling)",
         "status": "DRAWING-CONFIRMED geometry; line and material HELD"},
    ]
    observations = [
        {"id": "OBS-T592-1", "what": "T-325 strip depth 0.18 at D-GF-03 / D-GF-09 vs 0.200 between the drawn wall faces "
                                      "and the 0.200 frame depth (T-150 wall thickness basis): not this task's measure; "
                                      "named for the threshold m2 owner"},
    ]
    return {"schema": "T592_DOOR_STEPS_V1", "rule": "R-T592-1 (t592_rules.py)", "candidate": "ARCH_TAKEOFF_V3.0.58",
            "sign": "ours - his", "pins": dict(PINS), "openings": recs, "totals": tot, "compare": compare,
            "before_after": before_after, "fix_rows": fix_rows, "observations": observations,
            "detail_sheets": drawn["detail_sheets"], "released": "nothing: research, unwired"}


def main(argv):
    txt = json.dumps(build(), indent=1, sort_keys=True) + "\n"
    if "--check" in argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == txt
        print("REPRODUCED" if ok else "DIFFERS")
        return 0 if ok else 1
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(txt, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
