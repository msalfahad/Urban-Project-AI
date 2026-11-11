"""T-711 concrete blank tail: the 15 HELD BLANK STR.CONC lines of STAIR (5), PARAPET (4), LIFT (2) and NECK (4) on the
candidate of record ARCH_TAKEOFF_V3.0.70, each given a one-sided AT_LEAST the drawings support (R-T711-1 / -2, the
T-319 parapet floor) or kept HELD BLANK with its designer item and its quantity per unit of the missing dimension
(R-T711-3). Research only: nothing wired, nothing released, no AT_MOST stated, no line summed into a total.

Committed inputs only (no drawing is opened here; each printed value is cited to the sheet and the merged task):
  line index   research/agents_t693/out/LINE_INDEX_V3_0_70.json (V3.0.70 line ids, classes)
  necks        research/agents_t657/out/T657_NECK_LEDGER.json (T-657 MERGED d96a2958, Gate A PASS)
  parapets     research/agents_t319/t319_inputs.py build() over the T-311 / T-324 ledgers (MERGED, Checker p.14 read)
  stairs       research/agents_t258/LEDGER_T258.csv (component readings), T-673 ledger (census causes)
  lift ring    research/agents_t401/COMPONENTS_T401.csv PIT_WALL:PLAN 1.100 m2 (T-394 Checker, DRAWING-CONFIRMED)
Own reads this run (Drive 'Alsenan chalet project', read-only, private copies only): ST7757.pdf p.14 lift detail (wall
'20' from the raft top to the slab-on-grade top, F.F.L. above it, 5 cm screed / membrane / 10 cm plain concrete under
the raft, pit depth 'As Per Lift Manufactures recommendations'), p.8 note 19 (tie beams at 3.00 m round the lift where
the storey exceeds 4.30 m; no section), p.14 parapet details; p7757_arch_sheet03.pdf (GF plan): the lift (1.80 x 1.80)
is bounded by the hall and the stair hall, both marked '+1.00'; the '+0.30' mark is east of the stair, not at the lift.

    python3 -I research/agents_t711/t711_alsenan.py [--write]
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
sys.path.insert(0, str(RES / "agents_t319"))
import t711_rules as R  # noqa: E402

D = Decimal
INDEX = RES / "agents_t693" / "out" / "LINE_INDEX_V3_0_70.json"
T657 = RES / "agents_t657" / "out" / "T657_NECK_LEDGER.json"
T258 = RES / "agents_t258" / "LEDGER_T258.csv"
T673 = RES / "agents_t673" / "out" / "T673_LEDGER.json"
T401 = RES / "agents_t401" / "COMPONENTS_T401.csv"
OUT_JSON = HERE / "out" / "T711_LEDGER.json"
OUT_MD = HERE / "out" / "T711_CENSUS.md"

# printed facts (sheet, merged task)
MIN_DEPTH = D("1.50")    # ST p.9 note 1: excavation not less than 1.5 m below the existing plot level (T-357, T-657)
STACK = D("0.17")        # 5 cm screed + 2 cm membrane + 10 cm plain concrete (ST p.13, T-657 datums; p.14 same layers)
FF_H = D("0.55")         # lift raft FF, footing schedule (T-205, T-657 footing_H_m)
GF_TOP = D("0.95")       # GF column base / slab-on-grade top at the lift: F.F.L. +1.00 (own GF-plan read; GB-plan
                         # LEVEL marks T-700) - 0.05 build-up (T-214 DRAWING-CONFIRMED); = lift column base +0.95 (T-394)
UPSTAND = D("0.30")      # ST p.14 P1: RC upstand '30' above the structural slab top (T-311 Checker, F-T311-C1 floor)
TURN_A_MIN = D("1.44")   # ST p.4 MS1 turn region, smallest projection reading (T-258 MS1-T-SLAB: 1.44 .. 1.56 m2)
T_STAIR = D("0.16")      # 'T 16' (ST p.4, Q-47 A)
H_GF_1F = D("4.50")      # GF +1.00 -> 1F +5.50 (Q-46 A)

TARGET = {
    "STR.CONC.NECK": 4, "STR.CONC.LIFT": 2, "STR.CONC.PARAPET": 4, "STR.CONC.STAIR": 5,
}


def _index():
    d = json.loads(INDEX.read_text())
    assert d["candidate_version"] == "ARCH_TAKEOFF_V3.0.70"
    rows = [l for l in d["lines"] if l["item_code"] in TARGET and l["class"] == "HELD"
            and l["held_low"] is None and l["held_high"] is None and l["measured_net"] is None]
    by = {}
    for l in rows:
        by.setdefault(l["item_code"], []).append(l)
    for k, n in TARGET.items():
        assert len(by.get(k, [])) == n, (k, len(by.get(k, [])))
    return {l["line_id"]: l for l in rows}


def _t258():
    with T258.open(newline="") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def necks(idx):
    led = json.loads(T657.read_text())
    out = []
    for n in led["necks"]:
        if n["status"] != "HELD_LOWER_ONLY":
            continue
        assert n["line_id"] in idx, n["line_id"]
        assert D(n["footing_H_m"][0]) == FF_H and D(n["top_low_m"]) == GF_TOP
        b = R.below_supplier_raft(top_level=GF_TOP, areas_m2=n["section_candidates_m2"], min_depth=MIN_DEPTH,
                                  stack=STACK, H=FF_H, supplier_item="D-43 (lift raft / pit depth, supplier) + D-63")
        assert b["at_least"] == D(n["m3_low"]), (n["line_id"], b["at_least"], n["m3_low"])   # = T-657 (merged)
        out.append({**R.statement(n["line_id"], idx[n["line_id"]]["element_id"], "AT_LEAST", at_least=b["at_least"],
                                  item="D-43 / D-63 (upper end open: supplier raft depth)"),
                    "member": f"lift neck {n['mark']} {n['position']} on raft FF",
                    "hand": f"min section {b['area_min_m2']} m2 (D-63: plan GR vs schedule FOUNDATION) x h "
                            f"{b['h_low_m']} = +0.95 - ({b['raft_top_highest_m']}) [raft top <= -1.50 + 0.17 + 0.55]",
                    "source": "T-657 ledger (MERGED d96a2958, Gate A PASS) restated under R-T711-1"})
    assert len(out) == 4
    return out


def pit_walls(idx):
    comp = {r["component_id"]: r for r in csv.DictReader(T401.open(newline=""))}
    ring = D(comp["PIT_WALL:PLAN"]["value"])
    assert ring == D("1.1")
    lid = "L-684fcad323adc0c8a267"
    b = R.below_supplier_raft(top_level=GF_TOP, areas_m2=[ring], min_depth=MIN_DEPTH, stack=STACK, H=FF_H,
                              supplier_item="D-43 (pit depth 'As Per Lift Manufactures recommendations', ST p.14)")
    return {**R.statement(lid, idx[lid]["element_id"], "AT_LEAST", at_least=b["at_least"],
                          item="D-43 (upper end open: supplier pit depth)"),
            "member": "lift pit walls '20', ring net of the four lift columns, raft top -> slab-on-grade top",
            "hand": f"ring 1.600 - columns 0.500 = {ring} m2 (T-394; column long sides run along the ring, so the D-63 "
                    f"short-side readings 0.20 / 0.30 and 0.25 / 0.30 leave the overlap 0.20 x (0.50 x 3 + 1.00) = 0.500 "
                    f"unchanged) x h {b['h_low_m']} (top +0.95, raft top <= {b['raft_top_highest_m']})",
            "ownership": "starts on the raft top (footing owns the raft); columns own their pieces (necks); the ground "
                         "slab L-41cfb82e (3.56054, own panels only) excludes the ring (T-401 / T-397); ground beams end "
                         "on the ring's outer face: intersection once (R-CONC-OWN-1)",
            "freelancer": "lift walls 8.00 x 0.20 x 1.50 = 2.400 m3 incl. the column pieces 0.750 (also in his necks); "
                          "his net 1.650 < drawn floor 1.903: ENGINE_RIGHT proposal on the low end (his flat 1.50 m is "
                          "not a printed height; the drawn minimum is 1.73 m)"}


def tie_beam(idx):
    lid = "L-5ae06fda7d729d54c033"
    b = R.blank_named(item="D-43 (tie-beam section not printed; ST p.8 note 19 gives only the level 3.00 m)",
                      why="no width or depth printed on any sheet; the wall thickness '20' (p.8 note 20: walls round "
                          "columns as thick as the column) does not fix a beam section",
                      per_unit="5.500 m (runs 1.80 / 1.80 / 1.20 / 0.70 between column faces, T-401) x section: "
                               "5.500 m3 per m2 of section")
    return {**R.statement(lid, idx[lid]["element_id"], "BLANK_NAMED", item=b["item"]), "why": b["why"],
            "per_unit": b["per_unit"], "member": "GF lift tie beam at +3.00 m above GF (note 19: 4.50 > 4.30)"}


def parapets(idx):
    import t319_inputs as T319
    inp = T319.build()
    assert inp["upstand"]["floor_m"] == float(UPSTAND)
    out, tot = [], D(0)
    for c in inp["chains"]:
        lid = next(k for k, v in idx.items() if v["element_id"] == c["element_id"])
        f = R.parapet_floor(c["runs"], UPSTAND)
        tot += f["at_least"]
        held = [r["run"] for r in c["runs"] if r["geometry_status"] != "DRAWING-CONFIRMED"]
        out.append({**R.statement(lid, c["element_id"], "AT_LEAST", at_least=f["at_least"],
                                  item="Q-65 C (material above the upstand) + D-39 (b_edge, roof build-up)"),
                    "member": f"{c['chain']} roof parapet RC above the structural slab top ({len(c['runs'])} runs)",
                    "hand": f"sum of smallest drawn tops {f['top_lo_m2']} m2 x upstand 0.30",
                    "runs_geometry_held_at_min": held,
                    "why_no_at_most": "all-RC alternative (P2 / P3 / sections) = top x (h + b_edge), b_edge not printed"})
    assert R.BR.round_low(tot) == D("8.050942"), tot   # T-319 declared floor 8.0509428 (floored per line: 8.050942)
    return out


def stairs(idx, t258):
    def v(i, k):
        x = t258[i][k]
        assert x not in ("", None), (i, k)
        return D(x)

    out = []
    # ST-03 E1: steps part (5 drawn risers) floors the line; waist S-9 open
    lid = "L-061e18cf35a4b6b33d68"
    st = v("ST03-E1-STEPS", "value_m3")
    assert st == D("0.355017")
    out.append({**R.statement(lid, idx[lid]["element_id"], "AT_LEAST", at_least=st,
                              item="S-9 (E1 waist / support not printed)"),
                "member": "ST-03 entrance flight E1 (steps + waist)",
                "hand": "5 x 1/2 x 0.30 x 0.17 x 2.80 = 0.357000 - arrival wedge owned by the ground slab 0.001983",
                "source": "T-258 ST03-E1-STEPS DRAWING-CONFIRMED; T-673 / T-677 Checker AGREE 0.357"})
    # ST-01 GF remainder: MS1-L conflict (A arch + section 27 risers / B structural 28), winder treads, turn slab
    lid = "L-7863355dfcb68a681d2d"
    rA, rB = H_GF_1F / 27, H_GF_1F / 28
    readings = {
        "A_section_arch_27": {"MS1-L": v("ST01-MS1-L", "low_m3"),
                              "MS1-T": TURN_A_MIN * rA / 2,
                              "MS1-T-SLAB": TURN_A_MIN * T_STAIR},
        "B_structural_28": {"MS1-L": v("ST01-MS1-L", "high_m3"),
                            "MS1-T": TURN_A_MIN * rB / 2,
                            "MS1-T-SLAB": TURN_A_MIN * T_STAIR},
    }
    assert R.BR.round_low(readings["A_section_arch_27"]["MS1-T"]) == v("ST01-MS1-T", "low_m3")
    assert readings["A_section_arch_27"]["MS1-T-SLAB"] == v("ST01-MS1-T-SLAB", "low_m3")
    m = R.min_over_readings(readings)
    assert m["at_least"] == D("1.213429") and m["governing_reading"] == "A_section_arch_27"
    out.append({**R.statement(lid, idx[lid]["element_id"], "AT_LEAST", at_least=m["at_least"],
                              item="C-ST-4 / RFI-A04 (MS1-L 10 vs 12 fronts), D-67 / C-ST-3 (winders, turn soffit)"),
                "member": "ST-01 GF -> 1F remainder (MS1-L + winder treads + turn slab)",
                "hand": "reading A 0.863029 + 1/2 x (4.50/27) x 1.44 + 1.44 x 0.16 = 1.213429; reading B 1.054813 + "
                        "1/2 x (4.50/28) x 1.44 + 0.2304 = 1.400927 (min = A)",
                "reading_sums": {k: str(x) for k, x in m["reading_sums"].items()},
                "componentwise_min": str(m["componentwise_min"]),
                "why_floor_holds": "winder treads: the sum of wedges = 1/2 r x the turn area whatever the subdivision "
                                   "(D-67); under a warped soffit the waist is >= 0.16 normal (>= 0.16 vertical) over "
                                   ">= 1.44 m2, under a flat turn slab the winders stack higher than wedges: either "
                                   "build is >= wedges + 1.44 x 0.16",
                "why_no_at_most": "the turn soffit is not drawn (C-ST-3): a warped soffit's vertical thickness exceeds "
                                  "0.16, so the census high 1.434413 is not a bound"})
    # three blanks
    for lid, mem, item, why, pu in (
        ("L-659243ed9fc2831c3ae8", "ST-01 MS2 turn riser between the half landings +7.516 / +7.684",
         "C-ST-3 (section through the MS2 half-landing junction)",
         "the plates (T 0.16) are 0.168 apart in level: the upper soffit +7.524 clears the lower top +7.516 by 0.008, so "
         "a junction member must exist, but its thickness and depth are drawn nowhere (step line 5E2 only)",
         "0.328 m3 per m of riser thickness per m of length (depth 0.168 + 0.16), plus the 0.10 x 0.05 well end"),
        ("L-821032bc04a0b0d02133", "ST-01b lobby D1 waist / support under the 4 drawn steps (+0.30 -> +1.00, on grade)",
         "S-9 (D1 waist thickness / support)",
         "the steps (0.100286, released elsewhere) stand on the ground-slab zone: a waist may not exist (steps on "
         "compacted fill) or be any thickness; an AT_LEAST would be 0, an AT_MOST is unbounded",
         "about 1.15 x 0.90 = 1.035 m2 plan per m of vertical waist thickness, if a waist is built"),
        ("L-b6b0354b7842f0ed6e41", "ST-02 round stair remainder (12 curved treads, helicoid soffit, CA, 2CC)",
         "D-08 / owner Q-50 / Q-51 (curved parts HELD), C-ST-3",
         "the curved part's rise is printed nowhere (no section cuts ST-02; the uniform 4.50 / 28 is a reconstruction, "
         "ASSUMED - OWNER-APPROVED for the straight flights only) and the helicoid soffit and the CA level are not drawn",
         "wedges 1/2 x r x 4.1077 m2 = 2.05385 m3 per m of riser (0.330 at r 0.1607, information only) + helicoid "
         "waist + CA 0 .. 0.09"),
    ):
        b = R.blank_named(item=item, why=why, per_unit=pu)
        out.append({**R.statement(lid, idx[lid]["element_id"], "BLANK_NAMED", item=item), "member": mem,
                    "why": why, "per_unit": pu})
    return out


def build():
    idx = _index()
    t258 = _t258()
    t673 = json.loads(T673.read_text())
    rows = necks(idx) + [pit_walls(idx), tie_beam(idx)] + parapets(idx) + stairs(idx, t258)
    assert sorted(r["line_id"] for r in rows) == sorted(idx), "census 15 / 15 by id"
    fam = {}
    for r in rows:
        code = idx[r["line_id"]]["item_code"]
        f = fam.setdefault(code, {"lines": 0, "at_least_lines": 0, "at_least_m3": D(0), "blank_named": 0})
        f["lines"] += 1
        if r["bound"] == "AT_LEAST":
            f["at_least_lines"] += 1
            f["at_least_m3"] += D(r["at_least_m3"])
        else:
            f["blank_named"] += 1
    for f in fam.values():
        f["at_least_m3"] = str(f["at_least_m3"])
    return {
        "schema": "T711_LEDGER_V1", "task": "T-711", "candidate": "ARCH_TAKEOFF_V3.0.70",
        "rules": R.RULES, "not_claimed": "nothing wired, released or VERIFIED; no AT_MOST; never summed into a total",
        "census": {"lines": len(rows), "at_least": sum(1 for r in rows if r["bound"] == "AT_LEAST"),
                   "blank_named": sum(1 for r in rows if r["bound"] == "BLANK_NAMED")},
        "families": fam,
        "t673_ledger_sha_input": "research/agents_t673/out/T673_LEDGER.json (causes of the 5 stair lines, read)",
        "lines": rows,
    }


def _md(d):
    L = ["# T-711 census (V3.0.70, 15 HELD blank STR.CONC lines)", "",
         f"{d['census']['at_least']} AT_LEAST, {d['census']['blank_named']} BLANK_NAMED; nothing summed.", "",
         "| line | element | after | AT_LEAST m3 | item |", "|---|---|---|---|---|"]
    for r in d["lines"]:
        L.append(f"| {r['line_id']} | {r['element_id']} | {r['bound']} | {r['at_least_m3'] or '-'} | {r['item']} |")
    L += ["", "| family | lines | AT_LEAST lines | AT_LEAST m3 (beside) | blank named |", "|---|---|---|---|---|"]
    for k, f in sorted(d["families"].items()):
        L.append(f"| {k} | {f['lines']} | {f['at_least_lines']} | {f['at_least_m3']} | {f['blank_named']} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    d = build()
    s = json.dumps(d, indent=1, sort_keys=True, default=str)
    if "--write" in sys.argv:
        OUT_JSON.parent.mkdir(exist_ok=True)
        OUT_JSON.write_text(s + "\n")
        OUT_MD.write_text(_md(d))
    print(json.dumps({"census": d["census"], "families": d["families"]}, indent=1))
