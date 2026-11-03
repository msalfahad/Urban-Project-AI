"""T-350 r4: ARCH_TAKEOFF_V3.0.48 (the HELD BLANK V3.0.43 earthworks zone lines valued / ranged from the merged
calculated quantities; backfill gap zones added HELD BLANK) on the hand-calculated NON-Alsenan villa E350 of the T-350
r1 tests (its V3.0.43 zone lines are built first by engine.source.arch_v3043, unchanged).

Villa E350, by hand (own figures). Level basis (a scenario, ESTIMATED): footing underside at the printed 1.20 m minimum,
blinding 0.10 under it -> formation 1.30 below the existing ground +-0.00.
  B1-02 pits: union 6.56 m2 (P1 2.00 x 2.00 + P2 1.80 x 1.60 - overlap 0.20 x 1.60) x 1.30 = 8.528 m3 ESTIMATED
        -> PROVISIONAL; +-0.10 m: 7.872 / 9.184 beside.
  B1-03 pits: 8.528 - displacement once: blinding 6.56 x 0.10 = 0.656 + footings 1.600 + 1.152 - overlap 0.32 x 0.40
        (0.128) = 2.624 -> verified 3.280; ground-beam solid over the pits 0.10 .. 0.25 (section open)
        -> backfill 8.528 - 3.280 - 0.25 = 4.998 .. 8.528 - 3.280 - 0.10 = 5.148 m3, PARTIALLY VERIFIED 2 / 3;
        layers ceil((1.30 - 0.10) / 0.15) = 8.
  B1-03 lift zone: no line in V3.0.43 -> added HELD BLANK.  Lift excavation, T1 ZERO zone, disposal: unchanged HELD.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v3043 as A43  # noqa: E402
from engine.source import arch_v3048 as A  # noqa: E402
from tests.t350_earthworks_integration import test_arch_v3043 as R1  # noqa: E402

PID = R1.PID


def base():
    l42 = R1.lines_3042()
    d = A43.load_inputs(R1.inputs(l42), PID)
    ch, _ = A43.changes_for(d, l42)
    return A43.integrate(l42, ch)[0]


def _src(t):
    return {"task": t, "file": f"research/e350/{t}.csv", "sha256": t[-1] * 64, "merge_commit": "b" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def zones():
    return [
        {"action": "VALUE", "family": "B1-02", "zone": "Z1-PITS (2 pits, overlap once)", "element_id": "EW:B1-02:Z1-PITS",
         "value": 8.528, "evidence_status": "ESTIMATED", "basis": "union 6.56 m2 x 1.30 (S-scenario founding)",
         "sensitivity": "-0.10: 7.872; +0.10: 9.184", "printed_minimum_bound": "7.872 at the printed 1.20",
         "held_items": "working space not printed", "source_tasks": ["T-C"]},
        {"action": "RANGE", "family": "B1-03", "zone": "Z1-PITS", "element_id": "EW:B1-03:Z1-PITS",
         "low": 4.998, "high": 5.148, "evidence_status": "PARTIALLY VERIFIED 2 / 3",
         "basis": "8.528 - blinding 0.656 - footings net 2.624 - beam solid 0.10 .. 0.25",
         "held_items": "beam section open; working space", "excavation_element_id": "EW:B1-02:Z1-PITS",
         "displacement": {"verified_m3": 3.28, "remeasured_low_m3": 0.10, "remeasured_high_m3": 0.25,
                          "residual": "beam section 0.15"},
         "layers": {"depth_m": 1.20, "lift_m": 0.15, "status": "OWNER-PROVISIONAL", "count": 8},
         "source_tasks": ["T-C", "T-D"]},
        {"action": "ADD_HELD", "family": "B1-03", "zone": "Z1-LIFT", "element_id": "EW:B1-03:Z1-LIFT",
         "evidence_status": "HELD", "basis": "coverage gap", "held_items": "pit floor as per manufacturer",
         "source_tasks": ["T-C"]},
    ]


def doc(z=None):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-C"), _src("T-D")],
            "zones": zones() if z is None else z}


def run(d=None, prev=None):
    prev = prev or base()
    ch, log = A.changes_for(A.load_inputs(d or doc(), PID), prev)
    return prev, ch, log


def _el(lines, code, eid):
    return next(x for x in lines if x["item_code"] == code and x["location"]["element_id"] == eid)


# ================================================================================================ normal case
def test_hand_villa_values():
    prev, ch, log = run()
    new, ident = A.integrate(prev, ch)
    exc = _el(new, A.EXC, "EW:B1-02:Z1-PITS")
    assert exc["evidence_state"] == "PROVISIONAL" and exc["measured_net"] == pytest.approx(6.56 * 1.30)
    assert exc["bounded_range"] is None and exc["line_id"] == _el(prev, A.EXC, "EW:B1-02:Z1-PITS")["line_id"]
    bkf = _el(new, A.BKF, "EW:B1-03:Z1-PITS")
    lo = 6.56 * 1.30 - (0.656 + 1.6 + 1.152 - 0.32 * 0.40) - 0.25
    assert bkf["evidence_state"] == "BOUNDED_EXPOSURE" and bkf["measured_net"] is None
    assert (bkf["bounded_range"]["low"], bkf["bounded_range"]["high"]) == (pytest.approx(lo), pytest.approx(lo + 0.15))
    rec = bkf["calculation"]["inputs"][A.REC_KEY]
    assert rec["layers"]["count"] == 8 and rec["displacement"]["excavation_line"] == exc["line_id"]
    assert rec["evidence_status"] == "PARTIALLY VERIFIED 2 / 3"
    assert bkf["calculation"]["inputs"][A.PRIOR_KEY]["action"] == "ADD_ZONE"     # the V3.0.43 record is kept
    add = _el(new, A.BKF, "EW:B1-03:Z1-LIFT")
    assert add["evidence_state"] == "BLOCKED_RFI" and add["measured_net"] is None and add["rfi"]["question"]
    e = ident["earthworks"]
    assert (e["valued"], e["ranged"], e["added_held"], e["held_blank"]) == (1, 1, 1, 3)
    assert log["by_action"] == {"ADD_HELD": 1, "RANGE": 1, "VALUE": 1}


def test_drawing_confirmed_maps_to_source_derived():
    z = zones()
    z[0]["evidence_status"] = "DRAWING-CONFIRMED"
    prev, ch, _ = run(doc(z))
    new, _ = A.integrate(prev, ch)
    assert _el(new, A.EXC, "EW:B1-02:Z1-PITS")["evidence_state"] == "SOURCE_DERIVED"


def test_every_other_line_byte_identical_and_totals(tmp_path):
    prev, ch, log = run()
    names, ident, led = A.write(tmp_path, prev, ch, log)
    assert ident["outside_rows_identical_to_base"] == len(prev) - 2 and ident["added"] == 1
    moved = json.loads((tmp_path / "V3_0_48_RUN.json").read_text(encoding="utf-8"))["totals_moved_by_code"]
    assert set(moved) == {"STR.EARTH.EXCAVATION|m3", "STR.EARTH.BACKFILL|m3"}
    assert led["integration_package"] is True and all(r["release_status"] == "NOT RELEASED" for r in led["rows"])
    diff = (tmp_path / "V3_0_48_DIFF.csv").read_text(encoding="utf-8")
    assert diff.count(",CHANGED,") == 2 and diff.count(",ADDED,") == 1


# ================================================================================================ adverse cases
@pytest.mark.parametrize("mutate,msg", [
    (lambda z: z[1].update(low=5.0), "does not close"),
    (lambda z: z[1]["displacement"].update(verified_m3=-3.28), "negative"),
    (lambda z: z.pop(0), "not valued in the same inputs"),
    (lambda z: z[2].update(value=0.0), "HELD_WITH_VALUE"),
    (lambda z: z[0].update(value=0), "not positive"),
    (lambda z: z[0].update(value=8528000.0), "not a quantity in m3"),
    (lambda z: z[0].update(evidence_status="VERIFIED"), "not admissible"),
    (lambda z: z[1].update(evidence_status="PARTIALLY VERIFIED 3 / 3"), "partial count"),
    (lambda z: z[0].update(low=8.0, high=9.0), "carries no range"),
    (lambda z: z[1]["layers"].update(lift_m=0.20), "150 mm"),
    (lambda z: z[1]["layers"].update(count=7), "layer count"),
    (lambda z: z.append(dict(z[0])), "named twice"),
    (lambda z: z.append({"action": "VALUE", "family": "B1-04", "zone": "ALL", "element_id": "EW:B1-04:ALL",
                         "value": 3.0, "evidence_status": "ESTIMATED", "basis": "b", "held_items": "h",
                         "source_tasks": ["T-C"]}), "disposal is never valued"),
    (lambda z: z[0].update(source_tasks=["T-X"]), "no merged source"),
])
def test_inputs_refused(mutate, msg):
    z = zones()
    mutate(z)
    with pytest.raises(A.InputsError, match=msg):
        run(doc(z))


def test_stale_binding_and_applied_once():
    z = zones()
    z[0]["element_id"] = "EW:B1-02:Z1-NOPE"
    with pytest.raises(A.InputsError, match="stale binding"):
        run(doc(z))
    prev, ch, _ = run()
    new, _ = A.integrate(prev, ch)
    with pytest.raises(A.InputsError, match="applied once"):
        run(prev=new)


def test_add_over_an_existing_zone_refused():
    z = zones()
    z[2]["element_id"] = "EW:B1-03:Z1-PITS"
    z.pop(1)
    with pytest.raises(A.InputsError, match="already has this zone line"):
        run(doc(z))


def test_check_refuses_tampered_lines():
    prev, ch, _ = run()
    new, _ = A.integrate(prev, ch)
    bad = copy.deepcopy(new)
    exc = _el(bad, A.EXC, "EW:B1-02:Z1-PITS")
    exc["measured_net"] = 9.0
    with pytest.raises(ValueError, match="does not carry its record"):
        A.check_earthworks(bad)
    bad = copy.deepcopy(new)
    bkf = _el(bad, A.BKF, "EW:B1-03:Z1-PITS")
    bkf["bounded_range"]["high"] = 9.0
    bkf["calculation"]["inputs"][A.REC_KEY]["high_m3"] = 9.0
    with pytest.raises(ValueError, match="exceeds its excavation"):
        A.check_earthworks(bad)
    bad = copy.deepcopy(new)
    held = _el(bad, A.DSP, "EW:B1-04:ALL")
    held["evidence_state"], held["measured_net"] = "PROVISIONAL", 0.0
    with pytest.raises(ValueError, match="not HELD BLANK"):
        A.check_earthworks(bad)


def test_only_earthworks_codes_may_change():
    prev, ch, _ = run()
    c = copy.deepcopy(ch[0])
    c["after"]["item_code"] = "STR.CONC.FOOTING"
    with pytest.raises(ValueError, match="not a code this version"):
        A.integrate(prev, [c])


def test_policy_and_hub_name():
    p = A.policy_record()
    assert p["method"] == "ARCH_TAKEOFF_V3.0.48" and p["extends"] == "ARCH_TAKEOFF_V3.0.47"
    assert p["released_default"] is False
    hub = (ROOT / "tools/urban_boq_m9.py").read_text(encoding="utf-8")
    assert '"ARCH_TAKEOFF_V3.0.48"' in hub and "--v3048-inputs" in hub
