"""DRY RUN of the blind-test scorer on the synthetic villa (tools/arch_synth: every quantity is known by construction).

It proves the scoring machinery before any blind drawing exists: the benchmark is built from the hand-written truth
of the synthetic villa (never from the engine), the prediction (ARCH_TAKEOFF_V2.2 by default) is frozen (sha256 of the published files) before
the benchmark is opened, then six controlled faults are injected into a copy of the prediction and the scorer must
report each one exactly once, in the right category (silent omission, flagged omission, duplicate, quantity error,
false-positive area, false-positive door). Synthetic data only - no client drawing, no benchmark number.

    python3 research/urban_m9_p2a_acceptance/blind_test/dry_run.py [OUT.json]
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
_spec = importlib.util.spec_from_file_location("blind_score", Path(__file__).with_name("blind_score.py"))
BS = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(BS)


def synthetic_benchmark():
    """the sealed answer of the synthetic villa, from tools/arch_synth constants and TRUTH (metres)."""
    from tools import arch_synth as AS
    T = AS.TRUTH
    o1 = AS.FRAMES["1F"][2]
    rooms, qty = [], []
    gf = {"LIVING": ("LIVING", "DRY"), "BEDROOM": ("BEDROOM", "DRY"), "BATH": ("BATHROOM", "BATHROOM"),
          "KITCHEN": ("KITCHEN", "KITCHEN")}
    f1 = {"MASTER": ("MASTER_BEDROOM", "DRY"), "STAIR": ("STAIR", "STAIR"), "BATH2": ("BATHROOM", "BATHROOM"),
          "LOBBY": ("CORRIDOR", "DRY")}
    for floor, table, labels, origin in (("GF", gf, AS.GF_LABELS, (0.0, 0.0)), ("1F", f1, AS.F1_LABELS, o1)):
        for key, (truth_key, cat) in table.items():
            t = T[floor]["rooms"][truth_key]
            bid = f"B-{floor}-{key}"
            x, y = labels[key]
            rooms.append({"bench_room_id": bid, "floor": floor, "name": key, "category": cat,
                          "ref_xy_m": [(x + origin[0]) / 1000.0, (y + origin[1]) / 1000.0]})
            qty.append({"bench_room_id": bid, "trade": "FLOOR_AREA", "qty": round(t["net_m2"], 6), "unit": "m2"})
            if t["kind"] in ("DRY", "CIRCULATION"):
                qty.append({"bench_room_id": bid, "trade": "FLOOR_FINISH_DRY", "qty": round(t["net_m2"], 6),
                            "unit": "m2"})
                qty.append({"bench_room_id": bid, "trade": "SKIRTING", "unit": "lm",
                            "qty": round(t["boundary_lm"] - t["doors_lm"] - t["passages_lm"], 6)})
            elif t["kind"] == "WET":
                qty.append({"bench_room_id": bid, "trade": "FLOOR_FINISH_WET", "qty": round(t["net_m2"], 6),
                            "unit": "m2"})
                qty.append({"bench_room_id": bid, "trade": "WATERPROOFING_FLOOR", "qty": round(t["net_m2"], 6),
                            "unit": "m2"})
    elements = []
    for floor, ops, origin, cls in (("GF", AS.GF_OPENINGS, (0.0, 0.0), ["PVC", "PVC", "PVC", "MAIN"]),
                                    ("1F", AS.F1_OPENINGS, o1, ["PVC", "PVC"])):
        k = 0
        for kind, axis, lo, hi, s0, s1, _ins in ops:
            c_wall, c_gap = (lo + hi) / 2.0, (s0 + s1) / 2.0
            x, y = (c_wall, c_gap) if axis == "x" else (c_gap, c_wall)
            xy = [(x + origin[0]) / 1000.0, (y + origin[1]) / 1000.0]
            if kind == "DOOR":
                elements.append({"family": "DOOR", "floor": floor, "class": cls[k], "width_m": (s1 - s0) / 1000.0,
                                 "xy_m": xy})
                k += 1
            elif kind == "WINDOW":
                elements.append({"family": "WINDOW", "floor": floor, "class": None, "width_m": (s1 - s0) / 1000.0,
                                 "xy_m": xy})
    return {"protocol": BS.PROTOCOL, "unit": "m", "rooms": rooms, "room_quantities": qty, "elements": elements}


def _trade(res, trade):
    return res["trades"][trade]


def run(out=None, method="ARCH_TAKEOFF_V2.2"):
    from tools import arch_synth as AS
    from tools import urban_boq_m9 as M9
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "villa.dxf"
        AS.villa(str(p))
        room, arch, _E = M9.arch_compute(str(p), method=method)
        pred = BS.export_from_memory(room, arch)
        pred_file = Path(d) / "PREDICTION.json"
        pred_file.write_text(json.dumps(pred, sort_keys=True), encoding="utf-8")
        freeze = BS.freeze_record(d, method=method, drawing="synthetic villa (tools/arch_synth)")
        bench = synthetic_benchmark()                      # opened only after the freeze record exists
        bfile = Path(d) / "BENCHMARK.json"
        bfile.write_text(json.dumps(bench, sort_keys=True), encoding="utf-8")
        seal = BS.commitment(bfile, "dry-run-salt")
        assert BS.commitment(bfile, "dry-run-salt") == seal
    base = BS.score(pred, bench)
    checks = []

    def rid(name, floor):
        b = next(x for x in bench["rooms"] if x["name"] == name and x["floor"] == floor)
        return BS.match_rooms(pred, bench)[0][b["bench_room_id"]], b

    def check(name, cond, detail):
        checks.append({"fault": name, "pass": bool(cond), "detail": detail})

    # F1 silent omission: the kitchen floor finish disappears without a flag
    k_id, _ = rid("KITCHEN", "GF")
    f = copy.deepcopy(pred)
    f["rows"] = [r for r in f["rows"] if not (r["room_id"] == k_id and r["trade"] == "FLOOR_FINISH_DRY")]
    r1 = BS.score(f, bench)
    a, b = _trade(base, "FLOOR_FINISH_DRY"), _trade(r1, "FLOOR_FINISH_DRY")
    check("F1_SILENT_OMISSION", b["silent_omissions"] == a["silent_omissions"] + 1
          and b["released_matched"] == a["released_matched"] - 1 and b["coverage_qty"] < a["coverage_qty"],
          {"silent": [a["silent_omissions"], b["silent_omissions"]], "coverage": [a["coverage_qty"], b["coverage_qty"]]})
    # F2 duplicate: the bedroom skirting is emitted twice
    bd_id, _ = rid("BEDROOM", "GF")
    f = copy.deepcopy(pred)
    dup = next(r for r in f["rows"] if r["room_id"] == bd_id and r["trade"] == "SKIRTING" and r["status"] == "RELEASED")
    f["rows"].append(dict(dup, line_id=dup["line_id"] + "-DUP"))
    r2 = BS.score(f, bench)
    a, b = _trade(base, "SKIRTING"), _trade(r2, "SKIRTING")
    want = round(100.0 * dup["qty"] / a["bench_total"], 4)
    check("F2_DUPLICATE", b["duplicates"] == a["duplicates"] + 1
          and abs((b["total_error_pct"] - a["total_error_pct"]) - want) < 1e-3,
          {"duplicates": [a["duplicates"], b["duplicates"]], "total_error_pct": [a["total_error_pct"],
                                                                                 b["total_error_pct"]]})
    # F3 false-positive door: a released PVC door where the benchmark has none
    f = copy.deepcopy(pred)
    f["elements"].append({"family": "DOOR", "floor": "GF", "id": "FAKE", "class": "PVC", "width_m": 0.9,
                          "xy_m": [-50.0, -50.0], "status": "RELEASED", "height_m": None, "area_m2": None})
    r3 = BS.score(f, bench)
    a, b = base["elements"]["DOOR"]["GF"], r3["elements"]["DOOR"]["GF"]
    check("F3_FALSE_POSITIVE_DOOR", b["false_positives_released"] == a["false_positives_released"] + 1
          and b["omissions"] == a["omissions"], {"fp": [a["false_positives_released"], b["false_positives_released"]]})
    # F4 quantity error: the living floor finish is 10 % high
    lv_id, _ = rid("LIVING", "GF")
    f = copy.deepcopy(pred)
    row = next(r for r in f["rows"] if r["room_id"] == lv_id and r["trade"] == "FLOOR_FINISH_DRY"
               and r["status"] == "RELEASED")
    extra = 0.10 * row["qty"]
    row["qty"] *= 1.10
    r4 = BS.score(f, bench)
    a, b = _trade(base, "FLOOR_FINISH_DRY"), _trade(r4, "FLOOR_FINISH_DRY")
    check("F4_QUANTITY_ERROR", abs((b["pred_released_total"] - a["pred_released_total"]) - extra) < 1e-6
          and b["within_tolerance"] == a["within_tolerance"] - 1,
          {"within_tolerance": [a["within_tolerance"], b["within_tolerance"]], "wape": [a["wape_released_matched"],
                                                                                        b["wape_released_matched"]]})
    # F5 flagged omission: the GF bathroom wet floor becomes an RFI (not released, but not silent)
    bt_id, _ = rid("BATH", "GF")
    f = copy.deepcopy(pred)
    for r in f["rows"]:
        if r["room_id"] == bt_id and r["trade"] == "FLOOR_FINISH_WET":
            r["status"] = "FLAGGED"
    r5 = BS.score(f, bench)
    a, b = _trade(base, "FLOOR_FINISH_WET"), _trade(r5, "FLOOR_FINISH_WET")
    check("F5_FLAGGED_OMISSION", b["flagged_omissions"] == a["flagged_omissions"] + 1
          and b["silent_omissions"] == a["silent_omissions"],
          {"flagged": [a["flagged_omissions"], b["flagged_omissions"]]})
    # F6 false-positive area: a released floor finish on a predicted room the benchmark does not have
    f = copy.deepcopy(pred)
    f["rows"].append({"floor": "GF", "room_id": "GF-PHANTOM", "trade": "FLOOR_FINISH_DRY", "item_code": "X",
                      "unit": "m2", "qty": 5.0, "status": "RELEASED", "line_id": "PHANTOM", "element": None,
                      "never_additive_with": []})
    r6 = BS.score(f, bench)
    a, b = _trade(base, "FLOOR_FINISH_DRY"), _trade(r6, "FLOOR_FINISH_DRY")
    check("F6_FALSE_POSITIVE_AREA", b["false_positive_items"] == a["false_positive_items"] + 1
          and abs(b["false_positive_qty"] - a["false_positive_qty"] - 5.0) < 1e-9,
          {"fp_qty": [a["false_positive_qty"], b["false_positive_qty"]]})
    summary = {
        "protocol": BS.PROTOCOL,
        "method": method,
        "what": "scorer dry run on the synthetic villa (no client data); the engine score below is information, the "
                "fault checks are the test",
        "freeze_digest_before_benchmark_opened": freeze["digest"],
        "benchmark_commitment": seal,
        "faults": checks,
        "all_faults_detected": all(c["pass"] for c in checks),
        "engine_on_synthetic_villa": {
            "rooms": {k: base["rooms"][k] for k in ("bench_rooms", "matched", "unmatched_bench_rooms",
                                                     "merged_predicted_rooms", "category_confusion")},
            "trades": {t: {k: v[k] for k in ("bench_items", "released_matched", "flagged_omissions",
                                              "silent_omissions", "false_positive_items", "duplicates",
                                              "coverage_qty", "wape_released_matched", "total_error_pct")}
                       for t, v in base["trades"].items()},
            "elements": base["elements"],
            "claims": base["claims"],
        },
    }
    if out:
        Path(out).write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    s = run(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({"all_faults_detected": s["all_faults_detected"],
                      "faults": [(c["fault"], c["pass"]) for c in s["faults"]]}, indent=1))
    sys.exit(0 if s["all_faults_detected"] else 1)
