"""T-187: the project inputs of ARCH_TAKEOFF_V3.0.6 (URBAN_V306_INPUTS_V1) for the development villa. Research code,
stdlib only; it reads the merged files as committed and changes none of their quantities. Every choice cites its source:

STAIR_CONCRETE (ST-01 1F -> 2F, the storey the candidate folds away: D-T184-1, T-184 MERGED 924c2bd, Checker 15:00):
  ledger = research/agents_t192/T192_STAIR_LEDGER_REV3.json (T-192, MERGED 86fd5f42, Verifier 2026-10-23 01:57; it
  supersedes rev2 of T-189 and rev1 of T-184, which stay unchanged; T-192 s.7 item 2: "any V3.0.x stair ledger wiring:
  take rev3"). One record per 1F -> 2F piece of ST-01:
    MS2-L  RELEASED rev3_net 1.033445 m3, VERIFIED: Verifier 01:57 "MS2-L rev3 1.0334 m3 VERIFIED (geometry T-184
           verdict + foot boundary own)"; the 0.025448 waist below the 1F floor inside B20 is owned by B20 (R-CONC-OWN-1a)
    MS2-U  RELEASED rev3_net 1.001373 m3, DRAWING-CONFIRMED: the ledger row says "rev2 = Checker quantity 1.0014 (17:18,
           D-CHK-T180-1); Checker to confirm on rev2"; the T-189 merge verdict (20:15) compared it with the Checker's own
           17:18 geometry, but no verdict states it VERIFIED: integration does not upgrade a status
    MS2-LD HELD_RANGE 0.4696 .. 0.4800 m3: ledger row 0.480 "PARTLY VERIFIED: east half 0.240 VERIFIED, west half
           0.2304 .. 0.240 not verified (Checker 17:18)"; T-192 s.9 reads west 1.30 x 1.15 = 1.495 m2 (incl. the 0.10 m
           well strip, Q-51 cond) -> 0.2392 and east 1.20 x 1.20 -> 0.2304, total 0.4696, confirmed for the west part by
           the Verifier 01:57, "the ledger row 0.480 not changed by this task, stays PARTIALLY VERIFIED". Two readings
           of the same landing, unresolved: held over both, never one chosen
    MS2-TR UNQUANTIFIED: rev3 held_unchanged "landing levels scaled, not printed"
  Not in the stair (rev3 / T-184): the 1F and 2F floor-arrival landings (owner FLOOR_SLAB, R-STAIR-LAND-1), the heads
  inside B20 / B23 (owned by the beams, T-189), the HEAD-CLASH item (settled by T-189: B23 owns it).

DEFAULT_GUARD (T-186, MERGED 18b12176, Verifier 2026-10-22 17:00; firewall declaration T-190 MERGED 465e0015):
  evidence = research/agents_t186/dev_villa_guard_evidence.json as merged (document register, printed records with
  their sources, drawn inventory, engine element -> register mapping), convention set
  engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json (the set route G runs on, as t186_apply.py). Holding checks
  DG-1, DG-3, DG-4, DG-5, DG-6, DG-7, DG-8; DG-2 (documents searched) is RECORDED only: every route G line cites one
  source document, so DG-2 alone would hold all 820 convention lines; T-186 s.3 calls that a line-format gap, not 820
  defects, and the row's acceptance names the substantive findings (14.554 m3 / 1,885.36 kg on baseline A). The Lead /
  Checker may move DG-2 to holding: one word in this file, nothing else.
  equal_value_rebase: a convention value EQUAL to the printed one is not a convention defect (T-186 s.3: blinding
  projection 0.10 convention = 0.10 printed, "re-basis on the printed record"): listed REBASED_ON_PRINTED, not held.
  Placeholders (DG-5) for drawn parts no candidate line carries, each with its item code, floor and physical element:
  ST-01 LOBBY (the lobby flight D1, T-184 ST-01b, on the GROUND sheet) and DOME-3 (upper-roof dome, Q-27 A, on 2F). The
  1F -> 2F part of ST-01 is carried by the ledger lines above, so it has no placeholder.
  Mapping additions: the evidence mapping was built on baseline A (V2.9 route G, no profile); the candidate (V2.13 base,
  M4 profile) names two stairs with other engine ids (ST-02 round stair, ST-03 entrance flight): bound by their own
  geometry (MAPPING_ADDITIONS, each with its reason), so the guard sees ST-02's printed T 16 and counts both as carried.

SCOPE OF ITEM STR.CONC.STAIR ON 1F / 2F in the candidate (T-179 lesson, refused unless every line is accounted for): one
line, P-C:STAIRS:1F:SITE-b845e1e78b1f74a8 (4.451 m3, winder convention); the route's own face record shows its 18 lines
radiating 360 deg from one point to r 2.211 m: dome ribs, not a stair (MISREAD below): HELD, never summed, for T-193.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T192 = "research/agents_t192/T192_STAIR_LEDGER_REV3.json"
EVIDENCE = "research/agents_t186/dev_villa_guard_evidence.json"
CONVENTIONS = "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
HOLD = ["DG-1", "DG-3", "DG-4", "DG-5", "DG-6", "DG-7", "DG-8"]
RECORD = ["DG-2"]
# every candidate line of item STR.CONC.STAIR on 1F / 2F, accounted for (T-179 lesson; established on the V3.0.5 run of
# this task, route G face record of the structural DXF read in this run, nothing scaled):
OTHER_ELEMENTS: list = []
SUPERSEDE: list = []          # no candidate line carries ST-01 1F -> 2F (D-T184-1 holds on the candidate too)
MISREAD = [{"element_id": "P-C:STAIRS:1F:SITE-b845e1e78b1f74a8", "floor": "1F",
            "why": "route G STAIR_ZONE on the 1F slab sheet (SH04, 17.127 m2): all 18 'tread' lines start at ONE point "
                   "and end on a circle of radius 2.211 m, spread over 360 deg (the route's own face record, read this "
                   "run); a flight cannot wind 360 deg about one point inside a 4.42 m circle: these are the ribs of a "
                   "dome of diameter 4.42 m (ST7757.pdf p.7 DETAIL OF DOME 442; the two 2F dome lines read the same "
                   "r 2.211 m with 19 / 20 ribs). ST-01's 1F -> 2F flights are straight 12-riser flights 1.20 m wide "
                   "(T-184); T-196 found no T-184 flight for this line. Not stair concrete: held as information "
                   "(4.451 m3 winder convention), the dome itself is T-193's (scenario S0 / S1, T-185)"}]
MISREAD_DOWNSTREAM = [{"to": "T-193 (domes into the candidate)", "what": "the SH04 radial zone is a dome drawn on the 1F "
                       "slab plan: establish which of the T-185 domes it is and that the 2F dome lines do not count "
                       "the same dome twice"}]
# engine element ids of the candidate (V2.13 base) that the T-186 evidence (built on baseline A) does not know
MAPPING_ADDITIONS = {
    "P-C:STAIRS:GROUND:SITE-4df8fcd99d130701": {
        "element_id": "ST-02", "element_kind": "STAIR", "part": "WHOLE",
        "why": "route G stair zone on the ground-beam sheet (SH08): 8 fanning tread lines (a curved run), zone "
               "8.3723 m2 = the 8.37 m2 round-stair zone T-192 s.7 item 4 names for ST-02 on baseline A; ST-02 is "
               "the only part-curved stair of the inventory (T-184)"},
    "P-C:SCOPE:STAIRS:GROUND:CC-5ab1872c70:FLIGHTS": {
        "element_id": "ST-03", "element_kind": "STAIR", "part": "WHOLE",
        "why": "one straight run of 5 risers, 2.80 m wide, 0.948267 m3 = the engine E1 line of baseline A "
               "(L-5493f3e0cc5801512838, T-192 s.7 item 3; T-184 ST03 engine 0.9483); entrance 2.8 m (T-111)"},
}
PLACEHOLDERS = {
    "ST-01:LOBBY": {"item_code": "STR.CONC.STAIR", "floor": "GROUND", "physical_element": "STAIRS",
                    "why": "lobby flight D1 (court door lobby +0.30 -> GF hall +1.00) inside the ST-01 shaft, T-184 "
                           "ST-01b 0.126 m3 steps (waist not printed, HELD); no candidate line carries it"},
    "DOME-3:SHELL": {"item_code": "STR.CONC.DOME", "floor": "2F", "physical_element": "DOMES",
                     "why": "third dome on the upper roof (owner Q-27 A: three domes; architecture only, no "
                            "structural detail; T-185 scenario S0)"},
}


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def stair_records():
    led = json.loads((ROOT / T192).read_text(encoding="utf-8"))
    rows = {r["piece"]: r for r in led["st01_rows"]}
    held = {h["id"]: h for h in led["held_unchanged"]}
    ge = {"element_id": "ST-01", "part": "1F-2F"}
    sec = "ST7757.pdf p.5 1F roof slab (riser lines, widths, 'T 16'); p7757_arch_sheet10.pdf section A-A (risers, levels)"
    ms2l, ms2u, ms2ld = rows["MS2-L"], rows["MS2-U"], rows["MS2-LD"]
    assert abs(ms2l["rev3_net_m3"] - 1.033445) < 1e-6 and abs(ms2u["rev3_net_m3"] - 1.001373) < 1e-6
    assert abs(ms2ld["rev3_net_m3"] - 0.48) < 1e-9 and held["MS2-TR"]["candidate_m3"] is None
    return [
        {"element": "ST-01", "component": "MS2-L", "floor": "1F", "state": "RELEASED", "value": ms2l["rev3_net_m3"],
         "verified_by": "Verifier 2026-10-23 01:57 (T-192 MERGED 86fd5f42): MS2-L rev3 1.0334 m3 VERIFIED",
         "printed": sec, "geometry_source": "CAD_VECTOR", "guard_element": ge,
         "formula": "owner Q-19 steps + Q-47 A waist (T 16 / cos) between the first and last riser line - Q-62 A wedge "
                    f"{ms2l['q62_wedge_m3']} - waist below the 1F floor inside B20 {ms2l['foot_in_full_depth_beam_m3']}",
         "info": {"gross_m3": ms2l["gross_m3"], "rev2_net_m3": ms2l["rev2_net_m3"]}},
        {"element": "ST-01", "component": "MS2-U", "floor": "1F", "state": "RELEASED", "value": ms2u["rev3_net_m3"],
         "printed": sec, "geometry_source": "CAD_VECTOR", "guard_element": ge,
         "formula": "owner Q-19 steps + Q-47 A waist - Q-62 A wedge "
                    f"{ms2u['q62_wedge_m3']} - head inside B23 {ms2u['head_in_full_depth_beam_m3']} (owned by B23)",
         "info": {"gross_m3": ms2u["gross_m3"], "ledger_status": ms2u["status"], "ledger_why": ms2u["why"]}},
        {"element": "ST-01", "component": "MS2-LD", "floor": "1F", "state": "HELD_RANGE", "low": 0.4696, "high": 0.48,
         "range_basis": "T-192 s.9 drawn west 1.495 m2 + east 1.44 m2 x 0.16 = 0.4696 .. ledger row 0.480",
         "reasons": ["MS2-LD PARTLY VERIFIED: ledger 0.480 (Checker 17:18 east 0.240 verified, west 0.2304 .. 0.240 "
                     "not verified) vs drawn west 1.30 x 1.15 incl. the 0.10 well strip (Verifier 01:57) 0.2392 + east "
                     "1.20 x 1.20 0.2304 = 0.4696; well strip assignment Q-51 cond"],
         "printed": sec, "geometry_source": "CAD_VECTOR", "guard_element": ge},
        {"element": "ST-01", "component": "MS2-TR", "floor": "1F", "state": "UNQUANTIFIED",
         "reasons": [held["MS2-TR"]["why"]], "printed": sec, "guard_element": ge},
    ]


def inputs(project_id):
    recs = stair_records()
    ev = json.loads((ROOT / EVIDENCE).read_text(encoding="utf-8"))
    conv = json.loads((ROOT / CONVENTIONS).read_text(encoding="utf-8"))["conventions"]
    rel = sum(r["value"] for r in recs if r["state"] == "RELEASED")
    return {"schema": "URBAN_V306_INPUTS_V1", "project": project_id,
            "stair": {"piece": "STAIR_CONCRETE", "item_code": "STR.CONC.STAIR", "unit": "m3",
                      "source": {"file": T192, "sha256": sha(T192), "task": "T-192 (ledger rev3 over T-189 rev2 / "
                                 "T-184 rev1)", "merge_commit": "86fd5f42",
                                 "checker_run": "Verifier 2026-10-23 01:57 UTC (T-192 MERGED, Gate A all PASS)"},
                      "scope": {"physical_element": "STAIRS", "floors": ["1F", "2F"],
                                "supersede_lines": SUPERSEDE, "other_elements": OTHER_ELEMENTS,
                                "misread_lines": MISREAD},
                      "misread_downstream": MISREAD_DOWNSTREAM,
                      "drawing_reference": "ST7757.pdf p.4 / p.5 (riser lines, B20 / B23 bands), section A-A",
                      "records": recs,
                      "declared_totals": {"released": round(rel, 6), "held_low": 0.4696, "held_high": 0.48}},
            "guard": {"source": {"file": "engine/source/default_guard.py", "sha256": sha("engine/source/default_guard.py"),
                                 "task": "T-186 (default guard)", "merge_commit": "18b12176",
                                 "checker_run": "Verifier 2026-10-22 17:00 UTC (T-186 MERGED); T-190 465e0015"},
                      "evidence": ev, "evidence_file": EVIDENCE, "evidence_sha256": sha(EVIDENCE),
                      "conventions": conv, "conventions_file": CONVENTIONS, "conventions_sha256": sha(CONVENTIONS),
                      "holding_checks": HOLD, "recorded_checks": RECORD, "equal_value_rebase": True,
                      "mapping_additions": MAPPING_ADDITIONS,
                      "placeholders": PLACEHOLDERS}}
