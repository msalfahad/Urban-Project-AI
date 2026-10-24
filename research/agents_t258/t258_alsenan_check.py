"""T-258 development-villa ledger: CONC.STAIR_DOME, every component once, from ALSENAN_STAIR_DOME_INPUT.json.

    python3 -I research/agents_t258/t258_alsenan_check.py [--write]

stdlib only; reads no drawing (the printed values and handles are in the input file). --write regenerates
LEDGER_T258.csv and summary.json next to this file.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("t258_stair_dome_line", HERE / "t258_stair_dome_line.py")
SD = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("t258_stair_dome_line", SD)
_spec.loader.exec_module(SD)

AOA = "ASSUMED — OWNER-APPROVED"


def load(path=HERE / "ALSENAN_STAIR_DOME_INPUT.json"):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build(data):
    C = SD.component
    out = []
    fl = data["flights"]

    # ---------------- ST-01 dog-leg beside the lift (GF +1.00 -> +3.50 -> 1F +5.50 -> +7.516 / +7.684 -> 2F +9.70)
    mc = data["flight_conflicts"]["MS1-L"]
    rd = {k: SD.flight_m3(v["n_steps"], v["r"], v["g"], v["goings"], v["w"], v["t"])["net"]
          for k, v in mc["readings"].items()}
    out.append(C("ST01-MS1-L", "ST-01", "GF -> turn lower flight (straight part)", "CONFLICT", "HELD", "STAIR",
                 readings=rd, bound=[min(rd.values()), max(rd.values())], blocker=mc["blocker"],
                 source="ST p.4 45A .. 25E, 2F6 / 2F4 / 2F5 / 2F3; ARCH GF; section A-A", is_flight=True,
                 arrival=SD.arrival("HELD_JUNCTION", "winder turn MS1-T", rows=["ST01-MS1-T"],
                                    note="the straight part arrives into the held winders: its top triangle is inside "
                                         "the held turn, never released")))
    out.append(C("ST01-MS1-T", "ST-01", "winder turn treads", "HELD", "HELD", "STAIR", bound=[0.12, 0.13],
                 blocker="Q-51 cond: well strip 0.10 x 1.20 unassigned; C-ST-3 no winder detail (soffit not drawn)",
                 geometry_drawn=False, source="ST p.4 winder lines 2F6 / 2F4 / 2F5, closing line 2F3"))
    out.append(C("ST01-MS1-T-SLAB", "ST-01", "slab under the winder turn", "HELD", "HELD", "STAIR",
                 bound=[0.2304, 0.2496], geometry_drawn=False,
                 blocker="C-ST-3: soffit not drawn; plan 1.30 x 1.15 = 1.495 m2 (2F3 / 5E3-line wall 284 / 279 / 25E) "
                         "lies inside the projection range 1.44 .. 1.56 m2; the warped soffit has no drawn geometry",
                 source="ST p.4"))
    for lid in ("MS1-LD",):
        L = data["landings"][lid]
        out.append(C(f"ST01-{lid}", "ST-01", f"half landing {L['level']}", "CLOSABLE", L["evidence"], "STAIR",
                     value=SD.landing_m3(L["length"], L["width"], L["t"]), source=L["src"], note=L["verified_by"]))
    for fid in ("MS1-U", "MS2-L", "MS2-U"):
        f = fl[fid]
        p = SD.flight_m3(f["n_steps"], f["r"], f["g"], f["goings"], f["w"], f["t"], wedges=f["wedges"],
                         head_a=f.get("head_a"), foot_a=f.get("foot_a"))
        into = f["head_member"].split(" (")[0] + " (head, billed through)" if f.get("head_member") else \
            "half landing plate ST01-MS2-LD-W (T 0.16)"
        out.append(C(f"ST01-{fid}", "ST-01", "flight (owner method, net)", "CLOSABLE", f["evidence"], "STAIR",
                     value=p["net"], source=f["src"], note=f"{f['verified_by']}; steps {p['steps']:.6f} + waist "
                     f"{p['waist']:.6f} - Q-62 wedge {p['wedges']:.6f} - owned elsewhere "
                     f"{p['head_owned_elsewhere'] + p['foot_owned_elsewhere']:.6f}", is_flight=True,
                     arrival=SD.arrival("DEDUCTED", into, value=p["wedges"])))
        if p["head_owned_elsewhere"]:
            out.append(C(f"ST01-{fid}-HEAD", "ST-01", f"{fid} head inside {f['head_member']}", "OWNED_ELSEWHERE",
                         "VERIFIED", "BEAM", value=p["head_owned_elsewhere"], source=f["src"],
                         note="R-CONC-OWN-1 (T-189): the beam billed through the junction owns it, counted once there"))
        if p["foot_owned_elsewhere"]:
            out.append(C(f"ST01-{fid}-FOOT", "ST-01", f"{fid} waist below the floor inside {f['foot_member']}",
                         "OWNED_ELSEWHERE", "VERIFIED", "BEAM", value=p["foot_owned_elsewhere"], source=f["src"],
                         note="R-CONC-OWN-1a (T-192)"))
    for lid in ("MS2-LD-W", "MS2-LD-E"):
        L = data["landings"][lid]
        out.append(C(f"ST01-{lid}", "ST-01", f"half landing {L['level']}", "CLOSABLE", L["evidence"], "STAIR",
                     value=SD.landing_m3(L["length"], L["width"], L["t"]), source=L["src"], note=L["verified_by"]))
    out.append(C("ST01-MS2-TR", "ST-01", "turn riser between the two half landings (+7.516 / +7.684) and the 0.10 x "
                 "0.05 well end", "HELD", "HELD", "STAIR", bound=None, geometry_drawn=False,
                 blocker="C-ST-3: the junction section of the two plates 0.168 apart is not drawn (step line 5E2 only)",
                 source="ST p.5 5E2, 633; section A-A 25 risers"))
    out.append(C("ST01-ARR-1F", "ST-01", "1F floor-arrival landing 2.50 x 1.95", "OWNED_ELSEWHERE", "DRAWING-CONFIRMED",
                 "SLAB", value=None, region="SLAB:GF-077+B20", floor_level_landing=True,
                 source="T-234 panel GF-077 (1.55 m) + B20 band 0.40", note="R-STAIR-LAND-1: slab + beam, once"))
    out.append(C("ST01-ARR-2F", "ST-01", "2F floor-arrival landing 2.50 x 1.95", "OWNED_ELSEWHERE", "DRAWING-CONFIRMED",
                 "SLAB", value=None, region="SLAB:1F-062+B23", floor_level_landing=True,
                 source="T-234 panel 1F-062 (1.50 m) + B23 band 0.45", note="R-STAIR-LAND-1"))
    out.append(C("ST01-B3", "ST-01", "'B3 (With Stair)' members at the landings' north edges", "OWNED_ELSEWHERE",
                 "HELD", "BEAM", value=None, source="ST p.4 / p.5 'B3 (With Stair)'; p.16 typical stair beam",
                 note="owner Q-61 (2): HOLD in the beam line, never duplicated with flight concrete"))
    sf = data["shaft_floor"]
    out.append(C("ST01-SHAFT-FLOOR", "ST-01", f"stair-hall floor at +0.30 / +1.00 = ground slab panel {sf['panel']}",
                 "OWNED_ELSEWHERE", "DRAWING-CONFIRMED", "GROUND_SLAB", value=None, region="SLAB:GS-08",
                 source=sf["src"], note="r2: the T-192 s.9 'scope UNKNOWN' is superseded by T-242 GS-08 "
                 f"({sf['m2']} m2 x {sf['t']} = {sf['m3']} m3, billed there; listed here, not valued, so the D1 "
                 "arrival part ST01b-D1-SLAB inside it is not listed twice); never stair"))
    out.append(C("ST01-COL691", "ST-01", "column 691 (1F C3) 0.05 into the MS2-L lane", "OWNED_ELSEWHERE", "HELD",
                 "COLUMN", value=None, region="COL:691xMS2-L",
                 source="ST p.5 S-COL.BON 691 (drawn 0.25) vs schedule 0.20 x 0.50",
                 note="exposure 0 .. 0.006684 m3 stays inside the MS2-L value until the column section CONFLICT (T-248, "
                      "D-16) closes; then deducted from MS2-L, never in both"))

    # ---------------- ST-01b lobby flight and ST-03 entrance (steps drawn, waist not printed)
    for sid, el in (("D1", "ST-01b"), ("E1", "ST-03")):
        s = data["steps_only"][sid]
        pre = el.replace('-', '')
        gross = SD.steps_m3(s["n_steps"], s["r"], s["g"], s["w"])
        if "arrival_into" in s:
            # r2 (Verifier 12:58): the top triangle beyond the last riser line lies inside the +1.00 ground slab panel;
            # Q-62 A cond with the printed slab T: the part inside the slab is the slab's, the sliver below its soffit
            # stays with the steps (the T-111 / T-184 plate rule, as MS2-L into its 0.16 plate)
            ai = s["arrival_into"]
            owned = SD.wedge_in_plate_m3(s["r"], s["g"], s["w"], ai["t"])
            arr = SD.arrival("OWNED_ELSEWHERE", f"ground slab panel {ai['panel']} at +1.00 (T {ai['t']})",
                             rows=[f"{pre}-{sid}-SLAB"], value=owned,
                             note=f"sliver below the slab soffit {SD.wedge_m3(s['r'], s['g'], s['w']) - owned:.6f} "
                                  "stays in the steps")
        else:
            owned = s.get("slab_owned_m3", 0.0)
            arr = SD.arrival("OWNED_ELSEWHERE", "ground slab face (tip) + ground-beam band 178 / 7DB",
                             rows=[f"{pre}-{sid}-SLAB", f"{pre}-{sid}-GB"], value=owned,
                             note="slab tip deducted; the GB band part is an unvalued exposure kept in the steps")
        out.append(C(f"{pre}-{sid}-STEPS", el, "steps", "CLOSABLE", s["evidence"], "STAIR", value=gross - owned,
                     source=s["src"], is_flight=True, arrival=arr,
                     note=f"{s['n_steps']} triangles {gross:.6f} - arrival part owned elsewhere {owned:.6f}"))
        try:
            SD.flight_m3(s["n_steps"], s["r"], s["g"], s["n_steps"] - 1, s["w"], None)
        except SD.LedgerError as e:
            why = str(e)
        out.append(C(f"{el.replace('-', '')}-{sid}-WAIST", el, "waist / support under the steps", "HELD", "HELD", "STAIR",
                     bound=None, blocker=f"no thickness or support printed ({why})", source=s["src"]))
        if "arrival_into" in s:
            ai = s["arrival_into"]
            out.append(C(f"{pre}-{sid}-SLAB", el, f"arrival wedge inside ground slab panel {ai['panel']} (top "
                         f"{ai['t']} m)", "OWNED_ELSEWHERE", "DRAWING-CONFIRMED", "GROUND_SLAB", value=owned,
                         region=f"SLAB:{ai['panel']}:{sid}-ARRIVAL", source=ai["src"],
                         note="Q-62 A cond (plate thinner than the riser): 1/2 r g w x (1 - ((r - T) / r)^2); "
                              "billed once, in the slab panel"))
        elif s.get("slab_owned_m3"):
            out.append(C(f"{pre}-{sid}-SLAB", el, "arrival wedge inside the ground slab face",
                         "OWNED_ELSEWHERE", "VERIFIED", "GROUND_SLAB", value=s["slab_owned_m3"],
                         source="T-192 (Checker 2026-10-23 01:57 own 0.001983)",
                         note="Q-62 A cond: slab owns; " + s.get("slab_panel", "")))
    out.append(C("ST03-E1-GB", "ST-03", "last riser 0.05 inside the ground-beam band 178 / 7DB", "OWNED_ELSEWHERE",
                 "HELD", "GROUND_BEAM", value=None, source="ST p.3",
                 note="exposure 0 .. 0.0714 m3 stays in the steps until a ground-beam line bills through (levels "
                      "not printed, T-242 / T-253)"))

    # ---------------- ST-02 round reception stair (GF +1.00 -> 1F +5.50)
    out.append(C("ST02-RS-C", "ST-02", "12 curved treads +1.00 -> +2.929", "HELD", "HELD", "STAIR", bound=None,
                 geometry_drawn=False, blocker="owner Q-50 / Q-51: curved parts HELD; CAD tread areas 4.1077 m2, "
                 "candidate steps 0.330 is information only", source="ST p.4 arcs / lines CC-13011ac02f; ARCH GF",
                 is_flight=True, arrival=SD.arrival("CONTINUES", "ST02-RS-S",
                                                    note="no landing between the curved and the straight flight")))
    out.append(C("ST02-RS-C-SOFFIT", "ST-02", "helicoid waist under the curved treads", "HELD", "HELD", "STAIR",
                 bound=None, geometry_drawn=False, blocker="not drawn (Q-51 step 5, C-ST-3)", source="ST p.4"))
    for fid in ("RS-S", "RS-A"):
        f = fl[fid]
        p = SD.flight_m3(f["n_steps"], f["r"], f["g"], f["goings"], f["w"], f["t"], wedges=f["wedges"])
        out.append(C(f"ST02-{fid}", "ST-02", f"flight, wedge into {f['wedge_into']}", "CLOSABLE", f["evidence"],
                     "STAIR", value=p["net"], source=f["src"], note=f"{f['verified_by']}; steps {p['steps']:.6f} + "
                     f"waist {p['waist']:.6f} - wedge {p['wedges']:.6f}", is_flight=True,
                     arrival=SD.arrival("DEDUCTED", f["wedge_into"] + " (T 0.16)", value=p["wedges"])))
    L = data["landings"]["RS-LD"]
    out.append(C("ST02-RS-LD", "ST-02", f"corner landing {L['level']}", "CLOSABLE", L["evidence"], "STAIR",
                 value=SD.landing_m3(L["length"], L["width"], L["t"], L["deduct_m2"]), source=L["src"],
                 note=L["verified_by"]))
    out.append(C("ST02-COL374", "ST-02", "column 374 corner inside the corner landing", "OWNED_ELSEWHERE",
                 "DRAWING-CONFIRMED", "COLUMN", value=L["deduct_m2"] * L["t"], source="ST p.4 S-COL.BON 374",
                 note="column > stair (R-CONC-OWN-1a column corollary); deducted from RS-LD"))
    out.append(C("ST02-CA", "ST-02", "beam CA junction under the straight flight", "HELD", "HELD", "STAIR",
                 bound=[0.0, 0.09], blocker="CA level not stated (T-184)", source="ST p.4 hidden pair 535 / 536"))
    out.append(C("ST02-2CC", "ST-02", "hidden double line 2CC / 2CD across RS-LD / RS-A / plate", "UNKNOWN", "UNKNOWN",
                 "STAIR", blocker="layer-5 pair 0.10 apart, no mark, no schedule row (designer item)", source="ST p.4"))
    out.append(C("ST02-PLATE", "ST-02", "arrival plate C-T1 at +5.50", "OWNED_ELSEWHERE", "DRAWING-CONFIRMED", "SLAB",
                 value=None, region="SLAB:C-T1", floor_level_landing=True, source="T-234 (light-well / plate panels)",
                 note="floor level inside the slab: slab"))

    # ---------------- knees: drawing-derived, not in the owner method (T-192 s.5)
    for kid, v in (("KNEE-MS2L-TOP", 0.039242), ("KNEE-RSS-TOP", 0.037169), ("KNEE-RSA-TOP", 0.038754),
                   ("KNEE-MS1U-BOTTOM", -0.000573), ("KNEE-MS2U-BOTTOM", -0.000586), ("KNEE-RSA-BOTTOM", -0.00054)):
        out.append(C(kid, "ST-02" if "RS" in kid else "ST-01", "soffit knee beyond the plumb cut", "BESIDE",
                     "DRAWING-CONFIRMED", "STAIR", value=v, source="T-192 s.5 (MERGED 86fd5f42)",
                     note="owner method Q-47 A stops the waist at the riser line; shown beside, never summed"))

    # ---------------- domes, approved design S0 (Q-27 A, Q-29: the client request is S1 beside, never in the line)
    for did in ("DOME-A", "DOME-B"):
        d = data["domes"][did]
        out.append(C(f"{did}-SHELL", did, "shell 442 / 190 / 10", "CLOSABLE", d["evidence"], "DOME",
                     value=SD.shell_m3(d["chord"], d["rise"], d["t"]), source=d["src"], note=d["verified_by"]))
        out.append(C(f"{did}-RING", did, "ring under the shell edge", "OWNED_ELSEWHERE", "HELD", "BEAM", value=None,
                     source="ST p.5 band r 2.211 .. 2.411 vs p.7 ring r 2.011 .. 2.211, depth 'AS PER ARCH'",
                     note="beam line (T-241 / T-252 ring bands); S0 CONFLICT (A 0.7552 .. 1.1422, B 0.8997 .. 1.3108, "
                          "T-185), S1 B4 edge beam 0.7552 is the client scenario"))
        out.append(C(f"{did}-DRUM", did, "drum +9.70 -> springing +11.00", "HELD", "HELD", "DOME", bound=None,
                     blocker="section B-B '130' draws a thin unhatched wall: material and thickness not printed "
                             "(consultant RFI T-185 item 7)", source="ARCH Pages_11-12 p.1 section B-B"))
    out.append(C("DOME-3-SHELL", "DOME-3", "upper-roof (tower) dome", "HELD", "HELD", "DOME", bound=None,
                 blocker="Q-27 A: it exists; no structural detail and a flat +13.90 slab on ST p.6 (T-185); "
                         "designer D-21", source="ARCH SE elevation '441' / '215'; P7757 circle 1300 (hidden)"))
    return out


def retired(data):
    out = []
    fl = data["flights"]
    for k, r in data["retired_readings"].items():
        if r["type"] == "lane_width":
            res = SD.resolve_lane_width(r["declared"], r["lane_from"], r["lane_to"])
            el = r["element"]
            if el in fl:
                f = fl[el]
                lane_v = SD.flight_m3(f["n_steps"], f["r"], f["g"], f["goings"], res["lane"], f["t"],
                                      wedges=f["wedges"])["net"]
                decl_v = SD.flight_m3(f["n_steps"], f["r"], f["g"], f["goings"], r["declared"], f["t"],
                                      wedges=f["wedges"])["net"]
            else:
                L = data["landings"][el]
                lane_v = SD.landing_m3(r["length"], res["lane"], L["t"], L["deduct_m2"])
                decl_v = SD.landing_m3(r["length"], r["declared"], L["t"], L["deduct_m2"])
            out.append(dict(reading=k, accepted=res["accepted"], structural_lane_m=res["lane"],
                            overlap_width_m=res["overlap_width"], overlap_with_slab_m3=decl_v - lane_v,
                            value_on_declared_m3=decl_v, value_on_lane_m3=lane_v, why=r["why"]))
            continue
        res = SD.resolve_landing_edge(r["landing_from"], r["flight_last_riser"], r["flight_width"])
        well = r["flight_last_riser"] * r["well_width"]
        out.append(dict(reading=k, accepted=res["accepted"], overlap_with_flight_m2=res["overlap_m2"],
                        overlap_with_flight_m3=res["overlap_m2"] * 0.16, well_end_m2=well, well_end_m3=well * 0.16,
                        why=r["why"]))
    return out


def reconcile(data, comps):
    fr = data["freelancer"]
    v = {c["id"]: c for c in comps}
    val = lambda i: v[i]["value"]  # noqa: E731
    # ST-01: his 4 x 1.2 x 5.3 x 0.28 flights + 3 x 1.2 x 1.4 x 0.20 landings vs own (T-184 terms, then ownership)
    ms1l_a = v["ST01-MS1-L"]["readings"]["A_section_and_arch_plan"]
    fl = data["flights"]
    import math
    sloped = [math.hypot(9 * 0.30, 9 * 0.166667)] + [math.hypot(fl[f]["goings"] * fl[f]["g"], fl[f]["goings"] * fl[f]["r"])
                                                     for f in ("MS1-U", "MS2-L", "MS2-U")]
    own_gross_net_q62 = ms1l_a + sum(SD.flight_m3(fl[f]["n_steps"], fl[f]["r"], fl[f]["g"], fl[f]["goings"],
                                                  fl[f]["w"], fl[f]["t"], wedges=fl[f]["wedges"])["net"]
                                     for f in ("MS1-U", "MS2-L", "MS2-U"))
    length_term = 1.20 * 0.28 * (4 * 5.3 - sum(sloped))
    t_eq = own_gross_net_q62 / (1.20 * sum(sloped))
    thick_term = 1.20 * sum(sloped) * (0.28 - t_eq)
    owned = sum(c["value"] for c in comps if c["element"] == "ST-01" and c["cls"] == "OWNED_ELSEWHERE"
                and c["owner_line"] == "BEAM" and c["value"])
    own_flights = ms1l_a + val("ST01-MS1-U") + val("ST01-MS2-L") + val("ST01-MS2-U")
    lands = val("ST01-MS1-LD") + val("ST01-MS2-LD-W") + val("ST01-MS2-LD-E")
    his_land_area, drawn_area = 3 * 1.2 * 1.4, 1.44 + 1.495 + 1.44
    st01 = dict(
        freelancer=fr["main_flights"]["m3"] + fr["main_landings"]["m3"],
        flights=dict(his=fr["main_flights"]["m3"], length_5_3_vs_drawn_sloped=length_term,
                     thickness_0_28_vs_drawn_equivalent=thick_term, own_owner_method=own_gross_net_q62,
                     heads_and_foot_owned_by_beams=-owned, own_after_ownership=own_flights,
                     of_which_MS1L_reading_A_held=ms1l_a,
                     residual=fr["main_flights"]["m3"] - length_term - thick_term - owned - own_flights),
        landings=dict(his=fr["main_landings"]["m3"], area_5_04_vs_drawn=(his_land_area - drawn_area) * 0.20,
                      thickness_0_20_vs_T16=drawn_area * (0.20 - 0.16), own=lands,
                      residual=fr["main_landings"]["m3"] - (his_land_area - drawn_area) * 0.20
                      - drawn_area * 0.04 - lands))
    # ST-02 and ST-03: the held parts have no value, so the comparison closes only to a named, unvalued residual
    st02_closable = val("ST02-RS-S") + val("ST02-RS-A") + val("ST02-RS-LD")
    st02 = dict(freelancer=fr["stair_2"]["m3"], own_closable=st02_closable,
                his_length_on_no_drawing_m=16.4 - 10.863176856838756,
                his_length_on_no_drawing_m3=1.2 * 0.28 * (16.4 - 10.863176856838756),
                remaining=fr["stair_2"]["m3"] - st02_closable - 1.2 * 0.28 * (16.4 - 10.863176856838756),
                remaining_is="the 12 curved treads, the helicoid waist, the CA junction (all HELD, no value) and his "
                             "flat 0.28 m (T 16 printed): UNRESOLVED until Q-50 / Q-51 and C-ST-3 close")
    e1 = val("ST03-E1-STEPS") + v["ST03-E1-SLAB"]["value"]
    st03 = dict(freelancer=fr["entrance"]["m3"], own_closable=val("ST03-E1-STEPS"),
                his_run_1_8_vs_drawn_1_2_m3=0.6 * 2.8 * 0.28,
                his_0_28_on_the_drawn_run_vs_drawn_steps=1.2 * 2.8 * 0.28 - e1,
                slab_owned=v["ST03-E1-SLAB"]["value"],
                residual=fr["entrance"]["m3"] - 0.6 * 2.8 * 0.28 - (1.2 * 2.8 * 0.28 - e1) - e1,
                note="the second term is his 0.28 m 'slab + step' over steps only: the waist is HELD (not printed), "
                     "so this term is not an error size")
    shell = val("DOME-A-SHELL")
    domes = dict(freelancer=fr["domes"]["m3"], own_closable=2 * shell, third_dome_his=2.26,
                 area_22_6_vs_mid_surface=2 * (2.26 - shell),
                 residual=fr["domes"]["m3"] - 2.26 - 2 * shell - 2 * (2.26 - shell),
                 note="third dome HELD (no structure), not compared; his typed 22.6 m2 vs drawn mid-surface")
    return dict(ST01=st01, ST02=st02, ST03=st03, ST01b=dict(freelancer=None, own_closable=val("ST01b-D1-STEPS")),
                DOMES=domes, total_freelancer=fr["total"]["m3"])


FIELDS = ("id", "element", "part", "cls", "evidence", "owner_line", "value_m3", "low_m3", "high_m3", "readings",
          "blocker", "source", "note")


def rows(comps):
    out = []
    for c in comps:
        b = c["bound"] or [None, None]
        out.append(dict(id=c["id"], element=c["element"], part=c["part"], cls=c["cls"], evidence=c["evidence"],
                        owner_line=c["owner_line"],
                        value_m3="" if c["value"] is None else f"{c['value']:.6f}",
                        low_m3="" if b[0] is None else f"{b[0]:.6f}", high_m3="" if b[1] is None else f"{b[1]:.6f}",
                        readings="" if not c["readings"] else "; ".join(f"{k} {x:.6f}" for k, x in c["readings"].items()),
                        blocker=c["blocker"], source=c["source"], note=c["note"]))
    return out


def summary(data):
    comps = build(data)
    slab_regions = ("SLAB:GF-077+B20", "SLAB:1F-062+B23", "SLAB:C-T1", "SLAB:GS-08")
    SD.check_line(comps, slab_regions)
    arrivals = SD.check_arrivals(comps)
    t = SD.totals(comps)
    r = {k: (round(x, 6) if isinstance(x, float) else x) for k, x in t.items()}
    r["closable"] = {k: round(x, 6) for k, x in t["closable"].items()}
    r["conflict"] = [round(x, 6) for x in t["conflict"]]
    r["owned_elsewhere"] = {k: round(x, 6) for k, x in t["owned_elsewhere"].items()}
    r["by_element"] = {k: dict(closable=round(e["closable"], 6), conflict=[round(x, 6) for x in e["conflict"]],
                               held_open=e["held_open"]) for k, e in t["by_element"].items()}
    return dict(schema="T258_SUMMARY", rule=SD.SCHEMA, components=len(comps),
                by_class={c: sum(1 for x in comps if x["cls"] == c) for c in SD.CLASSES}, totals=r,
                retired_readings=retired(data), arrivals=arrivals, reconciliation=reconcile(data, comps)), comps


def _round(o):
    if isinstance(o, float):
        return round(o, 6)
    if isinstance(o, dict):
        return {k: _round(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_round(v) for v in o]
    return o


def render(data):
    s, comps = summary(data)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows(comps))
    return json.dumps(_round(s), indent=1, ensure_ascii=False) + "\n", buf.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    js, cs = render(load())
    if a.write:
        (HERE / "summary.json").write_text(js, encoding="utf-8")
        (HERE / "LEDGER_T258.csv").write_text(cs, encoding="utf-8")
    print(js)


if __name__ == "__main__":
    main()
