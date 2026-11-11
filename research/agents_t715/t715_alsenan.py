"""T-715 stair finishes HELD on ARCH_TAKEOFF_V3.0.70: the 85 HELD FIN.STAIR.* / FIN.MARBLE.* stair lines (skirting
sloped 22 / zigzag 22, flight 14, step 5, riser 13, tread 5, landing 2, soffit 2) by cause, each measured, bounded,
NOT_APPLICABLE with its carrier, or blank with its item (R-T715-1 .. 4). Research only: nothing wired, nothing released.

Committed inputs only (no drawing opened by this script; every printed value cited to the merged task that read it):
  line index   research/agents_t693/out/LINE_INDEX_V3_0_70.json (candidate V3.0.70 line ids and classes)
  flights      research/agents_t184/ALSENAN_STAIR_INPUT.json (levels, section / plan riser counts, goings; T-184 MERGED)
  bindings     research/agents_t412/CANDIDATE_BINDING_T412.json (engine reading -> drawn flight; T-412 MERGED)
  skirting     research/agents_t508/summary_t508.json (the 44 pair lines and their pieces; T-508 MERGED Gate B) on
               research/agents_t410/SIDE_TABLE_T410.csv (T-410 MERGED); T-690 MERGED (W2 pieces NOT_APPLICABLE)
  landings     T-493 MERGED (landing census: GF bound holds no landing; 2F bound = 2F arrival 4.865 + MS2-LD 2.9325)
  soffits      research/agents_t281/summary.json (T-281 MERGED: methods O / D per piece)
  turn         T-493 itemised winder region 1.3225 m2; T-684 MERGED (1F flight 5 = the GF winders seen through)
Owner rules: UP-STAIR-006 tread marble 0.030 (URBAN_RULES 1.6.0), Q-46 A, Q-50 A cond, S-9, ORR-007 (open).

    python3 -I research/agents_t715/t715_alsenan.py [--write]
"""
from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t715_rules as R  # noqa: E402

BR = R.BR
D = Decimal
INDEX = RES / "agents_t693" / "out" / "LINE_INDEX_V3_0_70.json"
T184 = RES / "agents_t184" / "ALSENAN_STAIR_INPUT.json"
T412 = RES / "agents_t412" / "CANDIDATE_BINDING_T412.json"
T508 = RES / "agents_t508" / "summary_t508.json"
T410 = RES / "agents_t410" / "SIDE_TABLE_T410.csv"
T281 = RES / "agents_t281" / "summary.json"
OUT_JSON = HERE / "out" / "T715_LEDGER.json"
OUT_MD = HERE / "out" / "T715_CENSUS.md"

TARGET = {"FIN.STAIR.SKIRTING.SLOPED": 22, "FIN.STAIR.SKIRTING.ZIGZAG": 22, "FIN.STAIR.FLIGHT": 14,
          "FIN.STAIR.STEP_LM": 5, "FIN.MARBLE.RISER": 13, "FIN.MARBLE.TREAD": 5, "FIN.MARBLE.LANDING": 2,
          "FIN.STAIR.SOFFIT": 2}
T_TREAD = D("0.030")       # UP-STAIR-006 (owner, URBAN_RULES 1.6.0): tread marble 0.030 unless drawing / spec / owner
W = D("1.150")             # marble front-edge width of every ST-01 / D1 / ST-02 flight (T-412: drawn front edges)
GOING = D("0.300")
OA = "ASSUMED - OWNER-APPROVED"
# RS-C summed nosing / riser-line length, two readings of the same 12 drawn lines (R-T711-2: the floor is the smaller):
# T-415 own handle read 12 x 1.150 = 13.800; the engine's RADIAL reading 13.7964 (T-412 binding, PROVISIONAL on V3.0.35)
RS_C_WIDTHS_MIN = min(D("12") * D("1.150"), D("13.7964"))
DC = "DRAWING-CONFIRMED"

# drawn flight -> (storey rise, storey risers [section or plan], risers of the flight, goings (straight), source status)
# rise / count printed: GF +1.00 -> 1F +5.50 = 4.50 / 27 (A-A, Q-46 A); 1F -> 2F 4.20 / 25 (A-A); D1 +0.30 -> +1.00 / 4;
# ST-02 4.50 / 28 plan count (Q-50 A cond: OA). Goings: straight goings drawn (T-184 'goings', T-412 front edges).
FLIGHTS = {
    "MS1-L": ((D("4.50"), 27), 10, 9, DC),
    "MS1-U": ((D("4.50"), 27), 12, 11, DC),
    "MS2-L": ((D("4.20"), 25), 12, 11, DC),
    "MS2-U": ((D("4.20"), 25), 12, 11, DC),
    "D1": ((D("0.70"), 4), 4, 3, DC),
    "RS-S": ((D("4.50"), 28), 11, 10, OA + " (Q-50 A cond: plan count 28, no section)"),
    "RS-A": ((D("4.50"), 28), 5, 4, OA + " (Q-50 A cond: plan count 28, no section)"),
}
# engine reading (element prefix) -> drawn flight, carrier reading of that drawn flight
READING = {
    "GF-R31F8AE:flight 1": ("MS1-L", None), "GF-R31F8AE:flight 2": ("D1", None),
    "1F-R78C367:flight 2": ("MS2-L", None), "1F-R78C367:flight 3": ("MS1-U", None),
    "2F-R4D1B62:flight 2": ("MS2-U", None), "GF-RC99C2A:flight 1": ("RS-C", None),
    "GF-RC99C2A:flight 2": ("RS-S", None), "GF-RC99C2A:flight 4": ("RS-A", None),
    "1F-R78C367:flight 5": ("MS1-T", None),
    # duplicates (R-T715-3): seen through the void / stacked / remainder of a reading
    "1F-R78C367:flight 1": ("RS-C", "GF-RC99C2A:flight 1"), "1F-R78C367:flight 4": ("RS-S", "GF-RC99C2A:flight 2"),
    "1F-R78C367:flight 6": ("RS-A", "GF-RC99C2A:flight 4"), "2F-R4D1B62:flight 1": ("MS2-L", "1F-R78C367:flight 2"),
    "GF-RC99C2A:flight 3": ("RS-S", "GF-RC99C2A:flight 2"),
}
DUP_BASIS = {
    "1F-R78C367:flight 1": "RS-C seen through the void from 1F (T-412 binding: exposure measured on GF F1)",
    "1F-R78C367:flight 4": "RS-S seen through the void from 1F (T-412: exposure measured on GF F2)",
    "1F-R78C367:flight 6": "RS-A seen through the void from 1F (T-412: exposure measured on GF F4)",
    "2F-R4D1B62:flight 1": "MS2-L stacked under 2F (T-184 R-STAIR-CONT-1, T-129; its tread / step / riser EXCLUDED)",
    "GF-RC99C2A:flight 3": "the rest of the GF reading of RS-S (T-412 by elimination; its tread / step EXCLUDED)",
}


def load_index():
    d = json.loads(INDEX.read_text())
    assert d["candidate_version"] == "ARCH_TAKEOFF_V3.0.70"
    allc = {(l["element_id"], l["item_code"]): l["class"] for l in d["lines"]}
    held = [l for l in d["lines"] if l["item_code"] in TARGET and l["class"] == "HELD"]
    for k, n in TARGET.items():
        got = sum(1 for l in held if l["item_code"] == k)
        assert got == n, (k, got)
    return held, allc


def riser_of(f):
    (rise, n), *_ = FLIGHTS[f]
    return R.riser(rise, n)


def check_inputs():
    """the committed facts this script carries agree with the merged ledgers (asserted, never silently trusted)."""
    t184 = json.loads(T184.read_text())
    fl = {f["id"]: f for s in t184["stairs"] for f in s.get("flights", [])}
    for k, ((rise, n), risers, goings, _) in FLIGHTS.items():
        assert fl[k]["risers"] == risers, k
        assert fl[k]["goings"] == goings, k
        assert abs(D(str(fl[k]["riser"])) - rise / n) < D("0.000001"), k
    b = json.loads(T412.read_text())
    drawn = {f["element_id"]: f["drawn_flight"] for f in b["flights"]}
    for el, (fname, _) in READING.items():
        want = None if fname == "MS1-T" else fname
        assert drawn[el] == want, (el, drawn[el], fname)


# ------------------------------------------------------------------ per item
def flight_rows(held, allc):
    out = []
    for l in held:
        code, el = l["item_code"], l["element_id"]
        if code not in ("FIN.MARBLE.RISER", "FIN.STAIR.FLIGHT", "FIN.STAIR.STEP_LM", "FIN.MARBLE.TREAD"):
            continue
        fname, carrier = READING[el]
        base = {"line_id": l["line_id"], "item_code": code, "element_id": el, "drawn_flight": fname, "unit": l["unit"],
                "before": {"low": l["held_low"], "high": l["held_high"], "net": l["measured_net"]}}
        if carrier:
            c = R.carrier_check(el, carrier, code, allc)
            st = R.statement(l["line_id"], "NOT_APPLICABLE", status=DC, carrier=carrier,
                             cause=f"R-T715-3: {DUP_BASIS[el]}; carrier {carrier} {code} ({c['carrier_class']})")
        elif fname in FLIGHTS:
            (rise, n), risers, goings, status = FLIGHTS[fname]
            f = R.straight_flight(rise_m=(rise, n), risers=risers, goings=goings, width_m=W, going_m=GOING,
                                  tread_t_m=T_TREAD)
            if code == "FIN.MARBLE.RISER":
                v, why = f["riser_m2"], f"{risers} risers x {W} x ({rise}/{n} - {T_TREAD})"
            elif code == "FIN.STAIR.FLIGHT":
                v, why = f["pitch_lm"], f"{goings} goings x hypot({GOING}, {rise}/{n})"
            else:
                raise AssertionError((el, code))          # straight-flight treads / steps are not in the held set
            st = R.statement(l["line_id"], "MEASURED", value=v, status=status + "; t " + OA + " (UP-STAIR-006)"
                             if code == "FIN.MARBLE.RISER" else status, cause="R-T715-1: " + why)
        elif fname == "MS1-T":
            r = riser_of("MS1-L")
            t = R.turn_region(region_m2=D("1.3225"), risers_section=5, risers_plan=4, treads=5, lane_width_m=W,
                              riser_m=r, tread_t_m=T_TREAD)
            item = "D-67 (winder subdivision not drawn; S-9, C-ST-3)"
            if code == "FIN.MARBLE.TREAD":
                st = R.statement(l["line_id"], "MEASURED", value=t["tread_m2"], status=DC + " (T-493 itemised region)",
                                 cause="R-T715-2: the 5 winder treads tile the turn region 1.3225 m2 (1.150 x 1.150 "
                                       "inside the finishes) whatever the subdivision; D-67 holds the split, not "
                                       "the area")
            elif code == "FIN.STAIR.STEP_LM":
                st = R.statement(l["line_id"], "AT_LEAST", low=t["step_lm_at_least"], status=DC, item=item,
                                 cause="R-T715-2: 5 winder treads (A-A 5 turn risers, the 5th onto MS1-LD) x lane "
                                       "1.150; each winder nosing spans inner corner -> outer wall >= 1.150")
            elif code == "FIN.MARBLE.RISER":
                st = R.statement(l["line_id"], "AT_LEAST", low=t["riser_m2_at_least"], status=DC + "; t " + OA,
                                 item=item, cause="R-T715-2: 5 turn risers (A-A) x >= 1.150 x (4.50/27 - 0.030)")
            else:
                st = R.statement(l["line_id"], "BLANK_NAMED", status="HELD", item=item,
                                 cause="walking line of the turn not drawn: no pitch line (R-T715-2)")
        elif fname == "RS-C":
            r = riser_of("RS-S")
            item = "D-08 / RFI-S27 (curved flight: outer band role, curtail; Q-50 A cond curved part HELD)"
            if code == "FIN.MARBLE.RISER":
                st = R.statement(l["line_id"], "AT_LEAST", low=BR.mul(RS_C_WIDTHS_MIN, r - T_TREAD), item=item,
                                 status=OA + " (riser 4.50/28) on " + DC + " riser lines (T-415 / T-412)",
                                 cause=f"12 drawn curved riser lines: smaller of the two readings of their summed "
                                       f"length ({RS_C_WIDTHS_MIN} lm, R-T711-2) x (4.50/28 - 0.030); marble may "
                                       "extend over the 0.050 band / curtail (open), never shorter")
            elif code == "FIN.STAIR.STEP_LM":
                st = R.statement(l["line_id"], "AT_LEAST", low=RS_C_WIDTHS_MIN, item=item, status=DC + " (T-415 / T-412)",
                                 cause="12 curved steps, each nosing a drawn riser line: smaller reading (T-415 12 x "
                                       "1.150 = 13.800, engine RADIAL 13.7964); curtail steps 1-3 may add, never less")
            elif code == "FIN.MARBLE.TREAD":
                st = R.statement(l["line_id"], "BLANK_NAMED", status="HELD", item=item,
                                 cause="marble edge (1.150 front edge vs 1.250 lane, curtail 0.090129 beyond the lane) "
                                       "not detailed; the drawn treads give no floor without the junction tread split")
            else:
                st = R.statement(l["line_id"], "BLANK_NAMED", status="HELD", item=item,
                                 cause="curved pitch line on the walking line needs the junction tread (T-415 tread "
                                       "12 curved + 0.0846 straight); curved parts HELD (Q-50 A cond)")
        else:
            raise AssertionError(el)
        out.append({**base, "after": st})
    return out


def landing_rows(held):
    out = []
    for l in held:
        if l["item_code"] != "FIN.MARBLE.LANDING":
            continue
        if l["element_id"].startswith("GF-"):
            st = R.statement(l["line_id"], "NOT_APPLICABLE", status=DC + " (T-493 MERGED)",
                             cause="T-493: the bound 0 .. 2.9225 holds no landing: 0.690 MS1-L / D1 treads (now in "
                                   "the released tread lines), 1.3225 winders (-> 1F flight 5 tread, R-T715-2), "
                                   "0.680 divider, 0.230 unread strip")
        else:
            st = R.statement(l["line_id"], "WIRING_GAP", status=DC + " (T-493 MERGED)",
                             cause="T-493: the bound 0 .. 9.225 = 2F arrival 4.8650 + MS2-LD 2.9325 (own lines, "
                                   "unwired) + 1.4275 not landing; NOT_APPLICABLE once those two lines are wired")
        out.append({"line_id": l["line_id"], "item_code": l["item_code"], "element_id": l["element_id"],
                    "unit": l["unit"], "before": {"low": l["held_low"], "high": l["held_high"],
                                                  "net": l["measured_net"]}, "after": st})
    return out


def soffit_rows(held):
    s = json.loads(T281.read_text())
    tot = s["totals"]
    ms1l = s["MS1-L CONFLICT"]
    ms1l_min = min(D(str(v[k])) for v in ms1l.values() for k in ("true_O", "true_D"))
    st01 = BR.add(min(D(str(tot["ST-01"]["true_O_measured"])), D(str(tot["ST-01"]["true_D_measured"]))), ms1l_min)
    st02 = min(D(str(tot["ST-02"]["true_O_measured"])), D(str(tot["ST-02"]["true_D_measured"])))
    out = []
    for l in held:
        if l["item_code"] != "FIN.STAIR.SOFFIT":
            continue
        if "ST-01" in l["element_id"]:
            st = R.statement(l["line_id"], "AT_LEAST", low=st01, status=DC + " (T-281 MERGED)",
                             item="C-ST-3 / D-67 (winder + junction 1.500 m2 plan), O vs D soffit method (no owner rule)",
                             cause=f"min(O, D) of the measured rows {min(D(str(tot['ST-01']['true_O_measured'])), D(str(tot['ST-01']['true_D_measured'])))}"
                                   f" + MS1-L CONFLICT smallest reading {ms1l_min}; held rows >= 0")
        else:
            st = R.statement(l["line_id"], "AT_LEAST", low=st02, status=OA + " (riser 4.50/28) (T-281 MERGED)",
                             item="D-08 / RFI-S27 (RS-C waist not printed: helical soffit HELD)",
                             cause="min(O, D) of the measured RS-S / RS-LD / RS-A rows; RS-C, members and unknown "
                                   "sub-pieces >= 0")
        out.append({"line_id": l["line_id"], "item_code": l["item_code"], "element_id": l["element_id"],
                    "unit": l["unit"], "before": {"low": l["held_low"], "high": l["held_high"],
                                                  "net": l["measured_net"]}, "after": st})
    return out


# ------------------------------------------------------------------ skirting
PIECE_FLIGHT = {"MS1-L": "MS1-L", "MS1-U": "MS1-U", "MS2-L": "MS2-L", "MS2-U": "MS2-U", "D1": "D1", "E1": "E1",
                "RS-S": "RS-S"}
EXTRA_FLIGHTS = {"E1": ((D("0.85"), 5), D("1.20"))}         # ST-03 +0.15 -> +1.00, 5 risers, run 1.20 (T-184)
AT_MOST_PIECES = {
    "MS1-U.E2": "designer (T-410): hidden opening 33C / 33D (0.90 m) in the lift wall above the cut: its sill against the flight "
                "(+4.0 .. +4.5) not printed (T-410)",
    "MS1-U.E3b": "CONFLICT: the top 0.300 of MS1-U (architectural plan vs ST p.4; T-508 / C-ST-4)",
    "RS-S.S0": "RFI-S27: the 0.050 outer band A7 / A9 (RL-09) guard or string not established; no wall face (T-410)",
    "RS-C.OUT": "RFI-S27 / D-08: outer band 23D / 23E guard or string not established, curved flight (T-410)",
}
NA_T690 = {"MS1-L.W2", "MS2-L.W2"}


def flight_run_rise(f):
    if f in EXTRA_FLIGHTS:
        (rise, n), run = EXTRA_FLIGHTS[f]
        return run, rise, R.riser(rise, n)
    (rise, n), risers, goings, _ = FLIGHTS[f]
    r = R.riser(rise, n)
    return BR.mul(goings, GOING), BR.mul(risers, r), r       # run = drawn goings x 0.300; rise = flight risers x r


def skirting_rows(held):
    pairs = {}
    for r in json.loads(T508.read_text())["rows"]:
        if r["item_code"].startswith("FIN.STAIR.SKIRTING"):
            pairs[r["line_id"]] = r
    out, conf = [], {"zig": D(0), "slo": D(0), "n": 0}
    corner = R.corner_turn(plan_a_m="1.20", plan_b_m="1.15", turn_rise_m=BR.mul(5, riser_of("MS1-L")))
    for l in held:
        if not l["item_code"].startswith("FIN.STAIR.SKIRTING"):
            continue
        p = pairs[l["line_id"]]
        piece = p["piece"]
        form = "ZIGZAG" if l["item_code"].endswith("ZIGZAG") else "SLOPED"
        key = "zigzag_lm" if form == "ZIGZAG" else "sloped_lm"
        flight = piece.split(".")[0]
        base = {"line_id": l["line_id"], "item_code": l["item_code"], "element_id": l["element_id"], "piece": piece,
                "form": form, "unit": "lm", "before": {"low": None, "high": None, "net": None},
                "t410_figure": p["figure_beside_lm"]}
        if piece in NA_T690:
            st = R.statement(l["line_id"], "NOT_APPLICABLE", status=DC + " (T-690 MERGED, Checker AGREE)",
                             cause="T-690: no wall face against the flight over this stretch (the shaft window "
                                   "reaches below the flight); unwired")
            out.append({**base, "after": st})
            continue
        if flight == "MS1-T":
            lo, hi = (corner["zig_a"] if piece.endswith(".W") else corner["zig_b"]) if form == "ZIGZAG" else \
                (corner["slo_a"] if piece.endswith(".W") else corner["slo_b"])
            st = R.statement(l["line_id"], "RANGE", low=lo, high=hi, status=DC + " (plan T-410, rise A-A 5 risers)",
                             item="D-67 (which wall each winder riser meets) + ORR-007 (form)",
                             cause=f"R-T715-4 corner turn: this wall in [plan, plan + 5 x 4.50/27]; pair W + N zigzag "
                                   f"{BR.round_point(corner['zig_pair'])} exact, sloped pair "
                                   f"{BR.round_low(corner['slo_pair'][0])} .. {BR.round_high(corner['slo_pair'][1])}")
            out.append({**base, "after": st, "pair_zigzag_exact": str(BR.round_point(corner["zig_pair"]))})
            continue
        if flight == "MS2-TR":
            r = riser_of("MS2-L")
            if form == "ZIGZAG":
                st = R.statement(l["line_id"], "CONDITIONAL_ON_FORM", value=r, status=DC + " (T-684 / T-690: riser "
                                 "position drawn on 1F + 2F; 4.20/25)", cause="R-T715-4: lone closing step on the "
                                 "north wall face: zigzag = 1 x 0.168 (plan 0)", item="ORR-007 (form)")
            else:
                st = R.statement(l["line_id"], "AT_LEAST", low=r, status=DC, item="ORR-007 + UP-STAIR-011 at zero run",
                                 cause="sloped rake undefined over a zero run; any form must rise the 0.168 step")
            out.append({**base, "after": st})
            continue
        if flight == "RS-C":
            plan = D(str(p["plan_lm"]))
            rr = riser_of("RS-S")
            zig, slo = BR.add(plan, BR.mul(12, rr)), R.hyp(plan, BR.mul(12, rr))
            f = {"zigzag_lm": zig, "sloped_lm": slo}
        else:
            run, rise, r = flight_run_rise(flight)
            f = R.skirt_forms(plan_m=str(p["plan_lm"]), risers_in=p["risers"], riser_m=r, run_m=run, rise_m=rise,
                              returns_m=str(p["returns_lm"]))
            fig = D(str(p["figure_beside_lm"])) if p["figure_beside_lm"] is not None else None
            assert fig is not None and abs(BR.round_point(f[key]) - fig) <= D("0.000002"), (piece, form, f[key], fig)
        if piece in AT_MOST_PIECES:
            st = R.statement(l["line_id"], "AT_MOST", high=f[key], status="HELD", item=AT_MOST_PIECES[piece],
                             cause="R-T715-4: full-wall figure of this form; 0 if no wall face (open side)")
        else:
            st = R.statement(l["line_id"], "CONDITIONAL_ON_FORM", value=f[key], item="ORR-007 (payable form)",
                             status=DC + " (T-410 / T-508 MERGED, recomputed)",
                             cause=f"R-T715-4 {form.lower()}: plan {p['plan_lm']} + {p['risers']} risers, returns "
                                   f"{p['returns_lm']}; never additive with its sibling form line")
            conf["zig" if form == "ZIGZAG" else "slo"] += f[key]
            conf["n"] += 1
        out.append({**base, "after": st})
    return out, conf


def build():
    check_inputs()
    held, allc = load_index()
    rows = flight_rows(held, allc) + landing_rows(held) + soffit_rows(held)
    sk, conf = skirting_rows(held)
    rows += sk
    assert len(rows) == 85 and len({r["line_id"] for r in rows}) == 85
    by = {}
    for r in rows:
        k = (r["item_code"], r["after"]["class"])
        by[k] = by.get(k, 0) + 1
    new_lines = [{
        "proposed": "FIN.MARBLE.RISER ST-01 MS2-TR closing riser (no candidate line)",
        "value_m2": str(BR.round_point(BR.mul(1, W, riser_of("MS2-L") - T_TREAD))),
        "status": DC + "; t " + OA, "basis": "1 riser (A-A) x 1.150 (T-684 / T-690 drawn line) x (4.20/25 - 0.030)"}]
    return {"schema": "T715_STAIR_FINISH_LEDGER_V1", "candidate": "ARCH_TAKEOFF_V3.0.70", "rules": R.RULES,
            "lines": sorted(rows, key=lambda r: (r["item_code"], r["element_id"], r["line_id"])),
            "class_counts": {f"{k[0]}|{k[1]}": v for k, v in sorted(by.items())},
            "skirting_form_pair": {"pieces_x_forms": conf["n"], "sum_zigzag_lm": str(BR.round_point(conf["zig"])),
                                   "sum_sloped_lm": str(BR.round_point(conf["slo"])),
                                   "payable_bound_lm": [str(BR.round_low(conf["slo"])), str(BR.round_high(conf["zig"]))]},
            "new_lines_proposed": new_lines}


def write_md(led):
    L = ["# T-715 stair finishes HELD on ARCH_TAKEOFF_V3.0.70 (research, unwired)", "",
         "| line | item | element | before | after | value / bound | status | cause |", "|---|---|---|---|---|---|---|---|"]
    for r in led["lines"]:
        a, b = r["after"], r["before"]
        bef = "blank" if b["low"] is None and b["net"] is None else f"{b['low']} .. {b['high']}"
        val = a["value"] or (f">= {a['low']}" if a["low"] and not a["high"] else "") or \
            (f"<= {a['high']}" if a["high"] and not a["low"] else "") or \
            (f"{a['low']} .. {a['high']}" if a["low"] else "")
        L.append(f"| {r['line_id']} | {r['item_code']} | {r['element_id']} | {bef} | {a['class']} | {val} | "
                 f"{a['status']} | {a['cause']}{' ; carrier ' + a['carrier'] if a['carrier'] else ''}"
                 f"{' ; item ' + a['item'] if a['item'] else ''} |")
    L += ["", "Class counts: " + json.dumps(led["class_counts"]), "",
          "Skirting form pair: " + json.dumps(led["skirting_form_pair"]), "",
          "New line proposed: " + json.dumps(led["new_lines_proposed"])]
    return "\n".join(L) + "\n"


def main(argv):
    led = build()
    js = json.dumps(led, indent=1, sort_keys=True) + "\n"
    md = write_md(led)
    if "--write" in argv:
        OUT_JSON.parent.mkdir(exist_ok=True)
        OUT_JSON.write_text(js)
        OUT_MD.write_text(md)
    elif "--check" in argv:
        assert OUT_JSON.read_text() == js, "ledger differs from the committed out/T715_LEDGER.json"
        print("REPRODUCED")
    print(json.dumps(led["class_counts"], indent=1))
    print(json.dumps(led["skirting_form_pair"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
