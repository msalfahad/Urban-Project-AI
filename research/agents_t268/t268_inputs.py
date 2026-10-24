"""T-268 (V3.0.13): the project inputs of ARCH_TAKEOFF_V3.0.13 (URBAN_V3013_INPUTS_V1) for the development villa.
Research code; values, opening ids and BOQ ids only (no coordinates, no names, no drawing content).

DOOR_RULING: the four doors the candidate (V3.0.10, T-232) holds in its door lines - D-GF-01 (class ALUMINIUM vs MAIN
ENTRANCE), D-GF-05 and D-GF-06 (class ALUMINIUM vs PVC), D-GF-09 (width 0.90 .. 1.00) - as the CHECKER RULED them in
its Gate A verdict on T-260 (Verifier 2026-10-24 11:57 UTC, run session_01LG9LiytEf6dC9TntHiigNK, MERGED c6732efe):
  widths (own re-measure, layer-1 wall-face line ends on BOTH faces at each insert): D-GF-01 / -05 / -06 1.000,
  D-GF-09 0.900 (the D120 block frame 0 .. 1.000 overlaps the masonry ends: a symbol) -> VERIFIED;
  classes (own plot of both side spaces): D-GF-01 exterior court, no entrance evidence (UP-DOOR-CLS-004 MAIN not met)
  -> ALUMINIUM; D-GF-05 the side passage open at its mouth on the plan and on the SW elevation (Q-67 A met) ->
  ALUMINIUM; D-GF-06 the open entrance landing -> ALUMINIUM; D-GF-09 ALUMINIUM (unchanged) -> DRAWING-CONFIRMED;
  heights: no sheet prints a door head -> Q-55 C 2.20 ASSUMED - OWNER-APPROVED (unchanged from V3.0.10).
The T-260 worker's ledger (research/agents_t260/LEDGER_T260.csv) is the source file; every value below is asserted
against it AND equals the Checker's own figure (the ruling, never the worker's proposal).
Cross-trade: each ruled width equals the census width T-198 (the id the masonry / plaster / paint deductions carry,
T-228 GF-W10 uses D-GF-09 0.90): no deduction changes, nothing to T-261 / T-244.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t232"))

import t232_inputs as L10  # noqa: E402  (the V3.0.10 opening records, unchanged)

ALU, PVC, MAIN = L10.ALU, L10.PVC, L10.MAIN
CODES = [ALU, PVC, MAIN]
CHECKER = "Verifier 2026-10-24 11:57 UTC (run session_01LG9LiytEf6dC9TntHiigNK)"
T260 = ("research/agents_t260/LEDGER_T260.csv", "T-260", "c6732efe", CHECKER)
# the Checker's ruling per door: class, width, the candidate classes it is held in, the side-space evidence
RULED = {
    "D-GF-01": {"cls": ALU, "width": 1.000, "held_in": [ALU, MAIN],
                "verdict": "class ALUMINIUM: leaf into the annex room, outside = court bounded only by the plot line; "
                           "no label / schedule / entrance mark (UP-DOOR-CLS-004 MAIN not met: adjacency is not "
                           "entrance evidence); width 1.000 on both wall faces"},
    "D-GF-05": {"cls": ALU, "width": 1.000, "held_in": [ALU, PVC],
                "verdict": "class ALUMINIUM: outside = the 1.20 m side passage, nothing drawn across its mouth on the "
                           "plan or the SW elevation (Q-67 A condition met on two sheets; identification on the "
                           "elevation by position, moderate confidence, the plan unambiguous); width 1.000 both faces"},
    "D-GF-06": {"cls": ALU, "width": 1.000, "held_in": [ALU, PVC],
                "verdict": "class ALUMINIUM: outside = the open +1.00 entrance landing, flight to the court, no wall / "
                           "glazing / door; width 1.000 on both wall faces"},
    "D-GF-09": {"cls": ALU, "width": 0.900, "held_in": [ALU],
                "verdict": "width 0.900 on both wall faces (the 1.000 D120 block frame overlaps the masonry ends by "
                           "0.047 / 0.053: a symbol, not the opening); class ALUMINIUM unchanged"},
}


def _ledger():
    with open(ROOT / T260[0], encoding="utf-8") as fh:
        return {r["id"]: r for r in csv.DictReader(fh)}


def ruling(oid, census_row, led_row):
    rv = RULED[oid]
    assert led_row["class"] == rv["cls"] and led_row["outcome"] == "SETTLED", (oid, led_row)
    assert abs(float(led_row["width_m"]) - rv["width"]) < 1e-9, (oid, led_row["width_m"])
    o = L10.door_record(census_row)
    o.pop("engine_element", None)
    w, h = rv["width"], o["height"]["value"]
    assert abs(h - L10.DOOR_H) < 1e-9 and o["height"]["status"] == L10.AS, oid
    assert abs(float(led_row["m2"]) - round(w * h, 4)) < 1e-9, (oid, led_row["m2"])
    o.update(classes=[rv["cls"]], class_status="DRAWING-CONFIRMED")
    o.pop("class_hold", None)
    o["width"] = {"value": w, "status": "VERIFIED", "verified_by": CHECKER,
                  "source": "wall-face line ends on both faces at the door insert (T-260 evidence; Checker own "
                            "re-measure)"}
    o["pcs"] = {"state": "SETTLED", "count": 1}
    o["m2"] = {"state": "RELEASED", "value": round(w * h, 4), "evidence_status": L10.AS}
    o["sources"] = [L10._src("T-198"), _src_t260()]
    return {"id": oid, "ruled_class": rv["cls"], "held_in": rv["held_in"], "verdict": rv["verdict"],
            "verified_by": CHECKER, "census_width": float(census_row["WIDTH_M"]), "record": o}


def _src_t260():
    f, task, mc, run = T260
    return {"file": f, "sha256": L10.sha(ROOT / f), "task": task, "merge_commit": mc, "checker_run": run}


def piece():
    c, led = L10.census(), _ledger()
    rulings = [ruling(oid, c[oid], led[oid]) for oid in sorted(RULED)]
    # declared after the ruling, per code over every floor (the V3.0.10 totals with the four doors moved)
    tot = {ALU: {"pcs": {"settled": 6.0, "held": [0.0, 0.0], "no_figure": 0},
                 "m2": {"released": 12.76, "bounded": [0.0, 0.0], "unquantified": 0}}}
    return {"piece": "DOOR_RULING", "item_codes": CODES, "source": _src_t260(),
            "sources": [L10._src("T-198")], "base": {"task": L10.SRC["T-198"][1], "merge_commit": L10.SRC["T-198"][2]},
            # the source the V3.0.10 door lines were written from (T-232 MERGED a0cd9bbc, its opening piece source)
            "scope": {"floors": L10.FLOORS}, "rulings": rulings, "declared_totals": tot}


def inputs(project_id=None):
    sys.path.insert(0, str(ROOT / "research" / "agents_t193"))
    import t193_inputs as L7   # noqa: E402  (the V3.0.7 guard inputs, unchanged, as V3.0.8 .. V3.0.12)
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V3013_INPUTS_V1", "project": project_id, "pieces": [piece()], "guard": g}


if __name__ == "__main__":
    import json
    pc = piece()
    for r in pc["rulings"]:
        print(r["id"], r["ruled_class"], r["held_in"], r["record"]["width"]["value"], r["record"]["m2"]["value"])
    print(json.dumps(pc["declared_totals"], indent=1))
