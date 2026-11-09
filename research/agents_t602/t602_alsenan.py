"""T-602 development-villa build (research, unwired): the census of every exterior opening with its printed levels and
step decision (R-T602-1), the census of every drawn step-edge pair, and the reconciliation of his door-step pieces
(7.70 lm / 6 nr, no opening id) whose UNRESOLVED 2.90 lm the statement V8 carries; candidate of record
ARCH_TAKEOFF_V3.0.58, no line changed.

    .work/venv/bin/python -I research/agents_t602/t602_alsenan.py [--check]

Reads only repository files (sha256-pinned): T602_DRAWN.json (this task's own read of the architectural DXF by
handle, t602_extract.py), the merged T-592 output (house doors and sea gate: payable piece, region levels), the merged
T-361 gate table (G-01 opening width), the merged T-150 opening census (exterior opening list) and his marble sheet
cells (numbers only, keyed by a sheet hash). Writes out/T602_DOOR_STEPS.json; --check rebuilds it byte-identical.
Signs: ours - his."""
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
import t602_rules as R  # noqa: E402

DRAWN = "research/agents_t602/T602_DRAWN.json"
T592 = "research/agents_t592/out/T592_DOOR_STEPS.json"
GATES = "research/agents_t361/GATES_T361.csv"
CENSUS = "research/agents_t150/OPENINGS_T150.csv"
RAW = "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
PINS = {DRAWN: None, T592: None, GATES: None, CENSUS: None, RAW: None}
PIN_FILE = HERE / "PINS.json"
OUT = HERE / "out" / "T602_DOOR_STEPS.json"
D = R.D
MRB = ("FIN", "3a9d8cc3e07d")          # his marble + court sheet (sha256[:12] of the sheet name)
DOOR_STEP_ROWS = (36, 37, 38, 39, 40, 41)
HOUSE = ("D-GF-01", "D-GF-03", "D-GF-05", "D-GF-09")
SEA_GATE = "D-GF-15"
# exterior openings of the merged census whose one side is outdoors (T-150 SIDE_A / SIDE_B), plus the boundary gap
EXTERIOR_CENSUS = ("D-GF-01", "D-GF-03", "D-GF-05", "D-GF-06", "D-GF-07", "D-GF-09", "D-GF-15", "D-2F-01",
                   "SX-01", "SX-03", "W15", "W16", "W17")
BOUNDARY = ("G-01",)
# a figure printed in the same open space but outside the strict region read: evidence only (never a riser)
FALLBACK = {
    "D-GF-06": ("+1.00", "E1 entrance landing: no figure printed on it; +1.00 by the merged T-260 ruling (T-584 s.2)"),
    "D-GF-07": ("+1.00", "E1 entrance landing: as D-GF-06 (T-260 ruling, T-584 s.2)"),
    "SX-01": ("+0.15", "pool court figure 40D (+0.15) on the court side"),
    "SX-03": ("+0.15", "pool court figure 40D (+0.15) on the court side"),
    "W15": ("+5.50", "sea-side roof terrace figures 1251 / D1D (+5.50) outside the window"),
    "W16": ("+5.50", "sea-side roof terrace figures 1251 / D1D (+5.50) outside the window"),
}
NOT_PASSABLE = {
    "SX-01": "low wall drawn THROUGH the 4.521 opening (layer-5 faces 8D / B7 run uninterrupted; T-154 / T-161 F09: "
             "an arch over a low wall with a railing; filling HELD on D-53): no walk-through, no step",
    "W17": "window over the void above the pool (T-150: outside 'over the pool'; no walking surface beyond)",
}
# printed figures of outdoor ground on this villa (court / walk +0.15, the +-0.00 datum outside the plot)
OUTDOOR = {"+0.15", "+-0.00"}


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins(write=False):
    got = {p: _sha(p) for p in PINS}
    if write:
        PIN_FILE.write_text(json.dumps(got, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        return got
    want = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    for p, h in want.items():
        if got.get(p) != h:
            raise R.RuleError(f"input {p} changed ({got.get(p)} != {h}): restate the inputs")
    return got


def S(x):
    return None if x is None else str(x)


def his_pieces():
    d = json.loads((ROOT / RAW).read_text(encoding="utf-8"))
    cells = {}
    for x in d["rows"]:
        if (x["file"], hashlib.sha256(x["sheet"].encode()).hexdigest()[:12]) == MRB:
            for c, v in x["cells"].items():
                cells[c] = v["v"]
    out = []
    for r in DOOR_STEP_ROWS:
        n, ln, area = cells.get(f"B{r}"), cells.get(f"C{r}"), cells.get(f"H{r}")
        if n is None or ln is None:
            raise R.RuleError(f"his row {r}: count or length missing")
        if D(n) != 1 or D(area) != D(n) * D(ln):
            raise R.RuleError(f"his row {r}: not one piece of count x length")
        out.append({"row": r, "nr": int(n), "lm": D(ln)})
    return out


def census_ids():
    ids = set()
    with open(ROOT / CENSUS, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            sides = (r["SIDE_A"] + " " + r["SIDE_B"]).lower()
            if not any(w in sides for w in ("outdoors", "outside", "roof", "passage (q-67)", "sea frontage")):
                continue
            if r["KIND"] in ("DOOR", "GATE", "OPENING"):
                ids.add(r["ID"])
            elif r["KIND"] == "WINDOW" and (r["SILL_M"] == "0.00" or (r["SILL_M"] == "" and "terrace" in sides)):
                ids.add(r["ID"])          # floor-level window, or sill not printed onto a terrace (W16, D-45)
    return ids


def build():
    pins()
    drawn = json.loads((ROOT / DRAWN).read_text(encoding="utf-8"))
    t592 = json.loads((ROOT / T592).read_text(encoding="utf-8"))
    gates = {r["id"]: r for r in csv.DictReader(open(ROOT / GATES, encoding="utf-8"))}
    # (a) the census list itself is the merged census's exterior set (doors, gates, leafless openings, sill-0 windows)
    ids = census_ids()
    if ids != set(EXTERIOR_CENSUS):
        raise R.RuleError(f"exterior opening set differs from the census: {sorted(ids ^ set(EXTERIOR_CENSUS))}")
    pairs = drawn["pairs"]
    at = {}
    for p in pairs:
        n = p["nearest_exterior_opening"]
        if R.at_opening(n["distance_m"]):
            at.setdefault(n["id"], []).append(p)
    away = [p for p in pairs if not R.at_opening(p["nearest_exterior_opening"]["distance_m"])]
    if any((set(p["levels_low_side"]) | set(p["levels_high_side"])) & OUTDOOR for p in away):
        raise R.RuleError("an edge pair away from every exterior opening reaches an outdoor figure: an outdoor step "
                          "candidate, HELD by name")
    min_away = min(D(p["nearest_exterior_opening"]["distance_m"]) for p in away)
    recs = []
    for oid in EXTERIOR_CENSUS + BOUNDARY:
        o = drawn["openings"][oid]
        if o["kind"] == "DOOR_INSERT":
            s0, s1 = list(o["levels_side_face0"]), list(o["levels_side_face_depth"])
        else:
            s0, s1 = list(o["levels_side_a"]), list(o["levels_side_b"])
        pr = at.get(oid, [])
        if len(pr) > 1:
            raise R.RuleError(f"{oid}: two edge pairs at one opening: HELD")
        base = {"opening": oid, "storey": o["storey"], "handles": o["handles"],
                "edge_pair": None if not pr else {"edge": pr[0]["edge"], "companion": pr[0]["companion"],
                                                   "low_side": pr[0]["levels_low_side"],
                                                   "high_side": pr[0]["levels_high_side"]}}
        if oid in HOUSE + (SEA_GATE,):
            r592 = t592["openings"][oid]
            hi = r592["inside_level"]
            lo = list(r592["outside_region_levels"])
            # own cross-check: the pair's low side reads the same single figure as T-592's region
            if not pr or list(pr[0]["levels_low_side"]) != lo:
                raise R.RuleError(f"{oid}: own pair read of the low side differs from T-592: HELD")
            d = R.decide(oid, [hi], lo, edge_pair={"high_side": "in", "distance_m":
                                                   pr[0]["nearest_exterior_opening"]["distance_m"]},
                         gap_m=r592["payable_lm"])
            if S(d["payable_lm"]) != r592["payable_lm"] or S(d["riser_m2"]) != r592["riser_m2"]:
                raise R.RuleError(f"{oid}: decision differs from the merged T-592 piece: HELD")
            base.update(levels_in=[hi], levels_out=lo, source="T-592 (merged) region read; own pair read agrees on "
                        "the low side", gap_basis=r592["wall_gap_source"])
        elif oid == "G-01":
            g = gates["G-01"]
            if not pr or pr[0]["companion"].split("#")[0] != "110" or pr[0]["edge"] != "10F":
                raise R.RuleError("G-01: the edge pair 10F / 110 is not read at the gap: HELD")
            comp = D(pr[0]["companion_m"])
            if comp != D(g["opening_width_m"]):
                raise R.RuleError("G-01: companion length differs from the T-361 opening width: HELD")
            if list(pr[0]["levels_low_side"]) != s1 or list(pr[0]["levels_high_side"]) != s0:
                raise R.RuleError("G-01: pair sides and opening sides disagree: HELD")
            d = R.decide(oid, s0, s1, edge_pair={"high_side": "in",
                                                 "distance_m": pr[0]["nearest_exterior_opening"]["distance_m"]},
                         gap_m=comp)
            base.update(levels_in=s0, levels_out=s1, source="own read: plot line 10F (layer 5) runs through the gap; "
                        "companion 110 (layer 2) 0.050 on the plot side, 2.500 long = T-361 opening (p.12 '250')",
                        gap_basis="companion 110 = gap between the fence cap 10B and the annex corner (T-361)")
        else:
            fb = FALLBACK.get(oid)
            passable = oid not in NOT_PASSABLE
            if pr:
                raise R.RuleError(f"{oid}: an edge pair is drawn at an opening the census treats as stepless: HELD")
            d = R.decide(oid, s0, s1, edge_pair=None, passable=passable,
                         fallback_out=None if fb is None or R.one_figure(s1) is not None else fb[0],
                         fallback_in=None if fb is None or R.one_figure(s0) is not None or
                         R.one_figure(s1) is None else fb[0])
            base.update(levels_in=s0, levels_out=s1, source="own region read" + ("" if fb is None else
                        f"; beside: {fb[1]}"), not_passable=NOT_PASSABLE.get(oid))
        base.update(decision=d["decision"], why=d.get("why"), nr=d.get("nr"), payable_lm=S(d.get("payable_lm")),
                    riser_m=S(d.get("riser_m")), riser_m2=S(d.get("riser_m2")),
                    status=d.get("status", "DRAWING-CONFIRMED" if d["decision"] == "NO_STEP" else "HELD"))
        recs.append(base)
    steps = [r for r in recs if r["decision"] == "STEP"]
    held = [r for r in recs if r["decision"] == "HELD"]
    if held:
        raise R.RuleError(f"HELD openings in the census: {[r['opening'] for r in held]}")
    his = his_pieces()
    rc = R.reconcile([p["lm"] for p in his], [{"opening": r["opening"], "decision": r["decision"],
                                               "payable_lm": D(r["payable_lm"])} for r in steps])
    before_ours = D(t592["totals"]["house_payable_lm"]) + D(t592["totals"]["gate_payable_lm"])
    before_unres = rc["his_lm"] - before_ours
    g01 = next(r for r in recs if r["opening"] == "G-01")
    after_unres = before_unres - D(g01["payable_lm"])
    if after_unres != -rc["residual_lm_ours_minus_his"]:
        raise R.RuleError("closure: V8 unresolved - G-01 != his - ours")
    pct = (rc["residual_lm_ours_minus_his"] / rc["his_lm"] * 100).quantize(D("0.01"))
    return {
        "schema": "URBAN_T602_DOOR_STEPS_V1", "sign": "ours - his", "rule": "R-T602-1 (t602_rules.py)",
        "candidate": "ARCH_TAKEOFF_V3.0.58 (no line changed)", "released": "ARCH_TAKEOFF_V2.9 + route G (unchanged)",
        "pins": pins(),
        "openings": recs,
        "pair_census": {
            "pairs": len(pairs), "at_exterior_openings": sorted(f"{k}: {v[0]['edge']} / {v[0]['companion']}"
                                                                for k, v in at.items()),
            "away_from_every_exterior_opening": len(away),
            "away_with_t412_flight_handle": sum(1 for p in away if p["flight_handle"]),
            "away_without_flight_handle_max_distance_to_a_flight_edge_m":
                S(max((D(p["nearest_t412_flight_edge_m"]) for p in away if not p["flight_handle"]), default=None)),
            "min_distance_away_pair_to_an_exterior_opening_m": S(min_away),
            "away_reaching_an_outdoor_figure": sorted(
                p["edge"] for p in away if (set(p["levels_low_side"]) | set(p["levels_high_side"])) & OUTDOOR),
            "ruling": "R-T602-1 (c): none of the pairs away from the exterior openings is a door step (stair-zone "
                      "edges owned by B7 / T-412 / T-598); none of them reaches an outdoor figure"},
        "his": {"rows": [{"row": p["row"], "nr": p["nr"], "lm": S(p["lm"])} for p in his],
                "lm": S(rc["his_lm"]), "nr": rc["his_nr"], "ids": "none (no door / gate id on any row)"},
        "reconciliation": {
            "ours_steps": [{"opening": r["opening"], "lm": r["payable_lm"], "riser_m": r["riser_m"],
                            "riser_m2": r["riser_m2"]} for r in steps],
            "ours_lm": S(rc["ours_lm"]), "ours_nr": rc["ours_nr"],
            "ours_riser_m2": S(sum((D(r["riser_m2"]) for r in steps), D(0))),
            "residual_lm": S(rc["residual_lm_ours_minus_his"]), "residual_nr": rc["residual_nr_ours_minus_his"],
            "residual_pct_of_his_lm": S(pct),
            "attribution": rc["attribution"],
            "v8_before": {"ours_lm": S(before_ours), "ours_nr": 5, "unresolved_lm": S(before_unres)},
            "v8_unresolved_split": [
                {"part": "G-01 street gate step (ENGINE_OMISSION: drawn edge pair 10F / 110, +0.15 / +-0.00, no "
                         "candidate line)", "lm": g01["payable_lm"], "status": "DRAWING-CONFIRMED"},
                {"part": "residual, his lengths exceed the drawn gaps in aggregate (count equal, 6 = 6)",
                 "lm": S(after_unres), "status": "UNRESOLVED",
                 "candidate_causes_not_attributed": [
                     "D-GF-09: door block drawn 1.000 over a 0.900 masonry gap (T-592 named conflict): +0.10 if the "
                     "block was read",
                     "D-GF-15: the NW elevation draws the gate zone as a 1.30 panel (27FA, T-361) against the plan's "
                     "1.000 gap: +0.30 if the elevation panel was read"],
                 "why_not_closed": "his rows carry no id; equal figures are not evidence (R-T602-1 (d))"}]},
        "verdicts": {
            "G-01 step 2.500 lm / riser 0.15 m / 0.375 m2": "ENGINE_OMISSION (drawing, own read); his count of 6 "
                                                           "pieces = 6 drawn steps: FREELANCER_RIGHT on the count",
            "residual 0.40 lm": "UNRESOLVED (two candidate causes named, neither attributable)"},
        "fix_rows": [
            {"id": "FR-T602-1", "row": "B7 external step at the street gate G-01 (boundary opening, no threshold "
                     "line exists): payable 2.500 lm, nr 1, riser 0.15 m = 0.375 m2 beside, DRAWING-CONFIRMED "
                     "geometry; stone / finish HELD (not printed); owning trade with the gate family (FR-T592-2) "
                     "for the Lead; the gate leaf stays HELD (T-361) and does not change the step"}],
        "e1": "the E1 entrance flight (his H16 5 x 2.80) is not in his door-step rows; FR-T584-1 owns it",
    }


def main(argv):
    if "--pin" in argv:
        print(pins(write=True))
        return
    out = json.dumps(build(), indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    if "--check" in argv:
        print("REPRODUCED" if OUT.exists() and OUT.read_text(encoding="utf-8") == out else "DIFFERS")
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(out, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


# T-653: this builder's functions run in the same local 40-digit context as its rules (before T-653 they ran
# at 40 only because importing the rules changed the process-global context).
R.in_prec40(globals())


if __name__ == "__main__":
    main(sys.argv[1:])
