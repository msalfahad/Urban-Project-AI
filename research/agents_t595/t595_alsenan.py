"""T-595 development-villa restatements, as NEW row versions (the merged T-583 / T-572 rows and files untouched):

(1) DOME_LIFT_REBAR_COMPONENTS_V2 (R-T595-1): the dome-ring DETAIL side bars counted from the drawn section, 2 levels
    x 2 vertical faces = 4 d14 (T-583 counted the 2 bars of one level / face); the B4 reading has no side bars (p.10 +
    note 21, unchanged). Row low = the smaller reading low (R-T575-5), so the west row keeps its B4 low.
(2) T572 HELD BOUNDS V2 (R-T595-2): the F10 + F footing component (held line L-164ae9d3) bound over the three
    owner-accepted S02 scenarios (owner 2026-11-02 RFI re-review (4)): F10 alone 2.80 x 1.40 x 0.50 = 1.960 / F10 + F
    = 1.960 + 0.90 x 0.80 x 0.30 = 2.176 / drawn outline 3.25 x 1.40 x 0.50 = 2.275 m3.

Inputs: values only. Own read this run of Drive 'Alsenan chalet project' / 'ST7757.pdf' (sha256 74da1523..., the
T-575 / T-583 file), p.7 DETAIL OF DOME, both ring cuts rendered at 600 dpi into .work/private: in each cut the
section draws 3 top dots (3 d16), 3 bottom dots (3 d18) and, between them, two dots on the left face and two on the
right face at two levels; the '2 d14 / 20cm' leader runs through the lower level only; '8 d8 / m' links; depth 'AS
PER ARCH' (not printed). Footing dimensions: T-233 / T-572 committed basis texts and the owner text cited above.
Run: .work/venv/bin/python -I research/agents_t595/t595_alsenan.py [--check]
"""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t583"))
sys.path.insert(0, str(ROOT / "research" / "agents_t572"))
import t595_rules as R  # noqa: E402
import t583_alsenan as A583  # noqa: E402  (read only)
import t572_alsenan as A572  # noqa: E402  (read only)
import t572_rules as R572  # noqa: E402  (read only)

OUT = HERE / "out" / "T595_RESTATEMENTS.json"
D = Decimal

# ST p.7 DETAIL OF DOME ring section, own read this run (both cuts identical)
RING_SIDE_DRAWN = {"levels": 2, "faces": 2, "label_n": 2, "d_mm": 14,
                   "src": "ST p.7 DETAIL OF DOME, both ring cuts: 2 + 2 dots on the two vertical faces at two levels; "
                          "leader '2 d14/20cm' through the lower level"}
# T-583 committed outputs pinned (the restatement is checked against them)
T583_PIN = {"DOME-B east ring low": 0.122518, "DOME-A west ring low": 0.063897, "bounded rows low": 0.767783}
T572_PIN = {"F10 + F low": "2.176000", "F10 + F high": "2.275000", "footing line bounded low": "7.844500",
            "footing line bounded high": "13.961300"}
F10_KEY = "P-C:FTG:SH10:T652:10A5"
S02 = {  # owner 2026-11-02 RFI re-review (4), accepted PROVISIONAL; each a box from the printed / drawn dimensions
    "S02-1 F10 alone": [("F10", "2.80", "1.40", "0.50")],
    "S02-2 F10 + F": [("F10", "2.80", "1.40", "0.50"), ("F", "0.90", "0.80", "0.30")],
    "S02-3 drawn outline": [("outline 1B1B at the deepest tagged depth", "3.25", "1.40", "0.50")],
}


def t(kg):
    return A583.M.to_t(kg)


# ---- (1) dome rings ------------------------------------------------------------------------------------------------
def ring_restate(row: dict) -> dict:
    new = copy.deepcopy(row)
    pop = R.side_bar_population(RING_SIDE_DRAWN["levels"], RING_SIDE_DRAWN["faces"], label_n=RING_SIDE_DRAWN["label_n"])
    reads = []
    for rd in new["readings"]:
        g = [x for x in rd["groups"] if x["group"].startswith("RING_SIDE[")]
        assert len(g) == 1
        g = g[0]
        if rd["reading"] == "DETAIL":
            old_kg = g["kg_low"]
            # T-583 basis: n_per_face (2) bars over the in-bay length = one level / one face pair as drawn
            dome = "DOME-A" if "DOME-1F-W" in row["row_id"] or len(new["readings"]) > 1 else "DOME-B"
            mains = A583.R575.ring_mains(A583.A575.RING_DETAIL["layers"], A583.A575.ring_readings(dome))
            inbay = min(x["inbay_m"] for x in mains["readings"])
            assert abs(old_kg - 2 * inbay * R.kgm(14)) < 1e-9, (old_kg, inbay)
            g["kg_low"] = R.side_bar_low_kg(pop, inbay, RING_SIDE_DRAWN["d_mm"])
            g["t"] = [t(g["kg_low"]), None]
            g["population"] = pop
            g["t583_kg_low"] = old_kg
            g["why"] = (f"R-T595-1: {pop['n']} d14 drawn ({pop['levels']} levels x {pop['faces']} faces, own read ST "
                        f"p.7) over the in-bay length {inbay:.4f} m; T-583 counted 2 (one face, F-C-T583-1); further "
                        "rows at the printed spacing over the unprinted ring depth: HELD")
        lo = sum(x["kg_low"] for x in rd["groups"])
        rd["t583_t_low"] = rd["t_low"]
        rd["t_low"] = t(lo)
        reads.append((rd["reading"], lo))
    new["t583_t_low"] = row["t_low"]
    new["t_low"] = t(min(lo for _, lo in reads))
    new["low_reading"] = min(reads, key=lambda x: x[1])[0]
    new["version"] = "DOME_LIFT_REBAR_COMPONENTS_V2 (R-T595-1)"
    return new


def rebar_rows():
    src = A583.build()
    rows = []
    for r in src["rows"]:
        if r["row_id"].startswith("HL:DOME_RING") or "RING" in r["row_id"] and "readings" in r:
            rows.append(ring_restate(r))
        else:
            rows.append(dict(copy.deepcopy(r), version="DOME_LIFT_REBAR_COMPONENTS_V1 (T-583, unchanged)"))
    rng = [r for r in rows if r.get("t_low") is not None]
    tot_lo = round(sum(r["t_low"] for r in rng), 6)
    assert round(src["totals"]["t_low"], 6) == T583_PIN["bounded rows low"]
    return {"rows": rows, "totals": {"rows": len(rows), "bounded_low_rows": len(rng), "t_low": tot_lo,
                                     "t583_t_low": src["totals"]["t_low"],
                                     "t_high_bounded_part": round(sum(r["t_high_bounded_part"] for r in rng), 6),
                                     "t_high": None, "high_status": src["totals"]["high_status"], "valued_t": 0.0}}


# ---- (2) F10 + F footing ---------------------------------------------------------------------------------------------
def s02_values():
    out = {}
    for sid, parts in S02.items():
        out[sid] = sum((R.box(L, B, H) for _, L, B, H in parts), D(0))
    return out


def footing_restate():
    doc = A572.build()
    comps = copy.deepcopy(doc["components"])
    old = [c for c in comps if c["element_id"] == F10_KEY]
    assert len(old) == 1
    old = old[0]
    vals = s02_values()
    sb = R.scenario_bound(vals, stated_high=old["high"])
    try:
        R.scenario_bound(vals, stated_low=old["low"])
        t572_low_strict = True
    except R.T595Error:
        t572_low_strict = False
    new = R572.component(F10_KEY, "B10 FOOTING LINE", "m3", low=sb["low"], high=sb["high"],
                         low_basis=f"R-T595-2: min of the owner-accepted S02 scenarios = {sb['low_scenario']} "
                                   "2.80 x 1.40 x 0.50 (owner 2026-11-02 RFI re-review (4))",
                         high_basis=f"R-T595-2: max = {sb['high_scenario']} 3.25 x 1.40 x 0.50 (T-233 reading B)")
    new.update(line_id=old["line_id"], scenarios=sb["values"], t572_low=old["low"], t572_high=old["high"],
               status_label="ESTIMATED range, owner PROVISIONAL; never VERIFIED (owner 2026-11-02)")
    comps = [new if c["element_id"] == F10_KEY else c for c in comps]
    fam_comps = [c for c in comps if c["family"] == "B10 FOOTING LINE"]
    fam = R572.family_total(doc["families"]["B10 FOOTING LINE"]["valued"], fam_comps)
    his = A572.his_family_totals()["F10"]
    beside = {"his_m3": str(his), "engine": [new["low"], new["high"]],
              "class": R572.against_bound(his, new["low"], new["high"]),
              "t572_class": doc["beside_his"]["F10 + F"]["class"]}
    # scenario consistency: other families of the same element, their existing basis and which scenario it serves
    others = {}
    for c in comps:
        if c["element_id"].endswith("10A5") and c["family"] != "B10 FOOTING LINE" or "F10F" in c["element_id"] \
                or c["element_id"].endswith("SB1:IN_FOOTING:F10_F"):
            others[c["element_id"]] = {"family": c["family"], "low": c["low"], "high": c["high"],
                                       "low_basis": c.get("low_basis"), "high_basis": c.get("high_basis"),
                                       "low_item": c.get("low_item")}
    consistency = {
        "concrete (this row)": "low = S02-1 F10 alone, high = S02-3 drawn outline",
        "excavation B1-02 PIT-F10F": "low already the S02-1 in-plot plan 4.350 m2 x 1.50 (T-572); high HELD",
        "blinding 10A5": "low 0.435 = 4.350 m2 x 0.10 (the same S02-1 in-plot plan); high 0.590 under the T-233 "
                         "readings: per-scenario split not measured here (SCENARIO_SPLIT_OPEN)",
        "SB1 in footing": "0 (existence open) .. 0.385: unchanged",
        "backfill B1-03 PIT-F10F": "UNBOUNDED (Q-31 C, Q-21 C): unchanged",
        "reinforcement / formwork": "not in T-572; per-scenario split open (T-560 / T-474 owners)",
    }
    return {"component": new, "t572_component": old, "family_v2": fam,
            "family_t572": doc["families"]["B10 FOOTING LINE"], "beside_his": beside,
            "t572_low_was_strict": t572_low_strict, "other_families_same_element": others,
            "scenario_consistency": consistency}


def build() -> dict:
    rb = rebar_rows()
    ft = footing_restate()
    assert ft["family_t572"]["bounded_part_low"] == T572_PIN["footing line bounded low"]
    return {"schema": "URBAN_T595_RESTATEMENTS_V1", "task": "T-595",
            "candidate": "ARCH_TAKEOFF_V3.0.58 (unchanged; nothing wired, valued or released)",
            "rules": ["R-T595-1 SIDE-BAR POPULATION FROM THE DRAWN SECTION", "R-T595-2 SCENARIO-SET BOUND"],
            "ring_side_drawn": RING_SIDE_DRAWN,
            "rebar": {"version": "DOME_LIFT_REBAR_COMPONENTS_V2 on T-583 V1", **rb},
            "footing": {"version": "T572_HELD_BOUNDS_V2 (F10 + F component only) on T572_HELD_BOUNDS_V1", **ft},
            "freelancer": {"rebar": "TYPED_LUMP 44.19 t (T-560): NOT_COMPARABLE, no %",
                           "F10 + F": "his 1.960 m3 (T-551 family total): now AT the low, class WITHIN; no %"}}


def main():
    res = build()
    txt = json.dumps(res, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n"
    if "--check" in sys.argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == txt
        print("CHECK", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(txt, encoding="utf-8")
    for r in res["rebar"]["rows"]:
        print(r["row_id"], r.get("version"), r.get("t583_t_low"), "->", r.get("t_low"))
    print(res["rebar"]["totals"])
    f = res["footing"]
    print("F10+F", f["t572_component"]["low"], "->", f["component"]["low"], f["component"]["high"])
    print("family bounded", f["family_t572"]["bounded_part_low"], "->", f["family_v2"]["bounded_part_low"],
          f["family_v2"]["bounded_part_high"])
    print("his", f["beside_his"])


if __name__ == "__main__":
    main()
