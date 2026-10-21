"""T-105 depth check of STAIR_CONCRETE_V1 on three NEW synthetic stairs (not the T-056 test censuses, not a client
drawing). Hand truth is written below BEFORE the run, from the census numbers only:

A  straight dog-leg, mm units: levels 0 / 2975 printed, 17 risers on the section -> riser 2.975 / 17 = 0.175 m
   F1 9 risers 8 goings, landing 1.20 x 1.30 T16 (panel tag), F2 8 risers 7 goings, tread 300, width 1200, T16
   steps  (9 + 8) x 1/2 x 0.175 x 0.30 x 1.20 = 17 x 0.0315 = 0.5355
   waist  F1 1.20 x hypot(2.40, 1.575) x 0.16 = 0.192 x 2.870649 = 0.551165 ; F2 0.192 x hypot(2.10, 1.40) = 0.192 x
          2.523886 = 0.484586
   landing 1.20 x 1.30 x 0.16 = 0.2496 ; total 1.820851 m3
   checks: riser 0.175 outside 0.155 - 0.165 (diagnostic); F1 arrival wedge in the T16 landing (riser > plate):
          [1/2 x .175 x .30 - 1/2 x .015 x (.015 x .30 / .175)] x 1.20 = 0.031269 m3 (shown, never deducted)
   the same stair in metres must give the same lines
B  winder corner: 0 / 3.20 m, 20 on the section, F 17 risers 16 goings + WINDER 3 risers, plan area 1.44 m2
   -> TURNING_STEPS HELD (Q-51), candidate 1/2 x 0.16 x 1.44 = 0.1152 shown, NOT in the total;
   flight steps 17 x 1/2 x 0.16 x 0.28 x 1.00 = 0.3808 measured
C  top level not printed -> every flight line (steps, waist) HELD RISER_HEIGHT_NOT_ESTABLISHED, no number; the landing
   needs no riser and stays 1.20 x 1.30 x 0.16 = 0.2496 (the run is never 0, its held lines are listed)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.source import stair_steps_concrete as S  # noqa: E402

T16 = lambda k: {"value": 160 * k, "source": "panel tag T 16", "basis": "PANEL_TAG"}  # noqa: E731


def census_a(k, unit):
    return {"id": "A", "unit": unit, "runs": [{
        "id": "R", "bottom_level": {"value": 0.0, "source": "sec +0.00"},
        "top_level": {"value": 2975 * k, "source": "sec +2.975"},
        "section_risers": {"value": 17, "source": "section X-X"},
        "parts": [
            {"id": "F1", "kind": "FLIGHT", "risers": 9, "goings": 8, "tread": {"value": 300 * k, "source": "p"},
             "width": {"value": 1200 * k, "source": "p"}, "thickness": T16(k)},
            {"id": "L1", "kind": "LANDING", "length": {"value": 1200 * k, "source": "p"},
             "width": {"value": 1300 * k, "source": "p"}, "thickness": T16(k)},
            {"id": "F2", "kind": "FLIGHT", "risers": 8, "goings": 7, "tread": {"value": 300 * k, "source": "p"},
             "width": {"value": 1200 * k, "source": "p"}, "thickness": T16(k)},
            {"id": "FL", "kind": "FLOOR_LANDING"}]}]}


def main():
    ok = True

    def eq(name, got, want, tol=1e-6):
        nonlocal ok
        good = (got is None and want is None) or (got is not None and want is not None and abs(got - want) <= tol)
        ok &= good
        print(f"  {name}: engine {got} hand {want} {'OK' if good else 'DIFF'}")

    for k, unit in ((1.0, "mm"), (0.001, "m")):
        r = S.measure(census_a(k, unit))
        t = r["totals"]
        print(f"A ({unit})")
        eq("steps", t["measured_by_element_m3"]["STEPS"], 0.5355)
        eq("waist", t["measured_by_element_m3"]["WAIST"], 0.551165 + 0.484586, 2e-6)
        eq("landing", t["measured_by_element_m3"]["LANDING"], 0.2496)
        eq("total", t["measured_m3"], 1.820851, 2e-6)
        w = [c for c in r["checks"] if c["check"] == "ARRIVAL_WEDGE_IN_LANDING"]
        eq("arrival wedge F1 (check)", w[0]["overlap_m3"] if w else None, 0.031269, 2e-6)
        ok &= any(c["check"] == "RISER_SANITY" for c in r["checks"])
    rb = S.measure({"id": "B", "unit": "m", "runs": [{
        "id": "R", "bottom_level": 0.0, "top_level": 3.2, "section_risers": {"value": 20, "source": "sec"},
        "parts": [{"id": "F", "kind": "FLIGHT", "risers": 17, "goings": 16, "tread": {"value": 0.28, "source": "p"},
                   "width": {"value": 1.0, "source": "p"}},
                  {"id": "W", "kind": "WINDER", "risers": 3, "plan_area": {"value": 1.44, "source": "drawn"}}]}]})
    print("B (winder)")
    wl = next(x for x in rb["lines"] if x["element"] == "TURNING_STEPS")
    print(f"  winder status {wl['status']} reason {wl['reason']} quantity {wl['quantity_m3']}")
    ok &= wl["status"] == "HELD" and wl["quantity_m3"] is None
    eq("winder candidate (not released)", wl["candidate_m3_option_A"], 0.1152)
    eq("steps", rb["totals"]["measured_by_element_m3"]["STEPS"], 0.3808)
    eq("total = steps only (waist: no thickness)", rb["totals"]["measured_m3"], 0.3808)
    c = census_a(1.0, "mm")
    c["runs"][0]["top_level"] = None
    rc = S.measure(c)
    print("C (no top level)")
    fl = [x for x in rc["lines"] if x["part"] in ("F1", "F2")]
    print("  flight lines:", sorted({(x["element"], x["status"], x["reason"]) for x in fl}))
    ok &= all(x["status"] == "HELD" and x["quantity_m3"] is None for x in fl)
    eq("total of measured (landing only, it needs no riser)", rc["totals"]["measured_m3"], 0.2496)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
