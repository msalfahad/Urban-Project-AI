"""T-179: the three checker-merged hand ledgers of the development villa, typed into the project inputs of
ARCH_TAKEOFF_V3.0.5 (URBAN_V305_VERIFIED_LEDGERS_V1). Research code, stdlib only; it reads the ledgers as committed
and changes none of their quantities. What it decides, and why (every choice cites its source):

SLAB_STEEL (T-152, MERGED 798e3b9, checker 2026-10-22 00:35):
  * one BOTTOM MESH record per panel and direction: HELD_RANGE over the two COUNT readings A = ceil(rate x width) and
    B = A + 1, each with its own crossing half (kg_A + kg_cross_A .. kg_B + kg_cross_B, min .. max: on a skewed panel B
    can be below A, T-152 finding). Why held: the meaning of 'n o d/m' was established (T-171, MERGED 701d227) for the
    FOOTINGS ONLY; ENGINEERING_REASONING_STANDARD s.3 forbids extending it to slabs without its own evidence. Reading C
    (rate x width unrounded) is not a bar population (a count is an integer under either meaning): kept as information;
  * the three labels printed without '/m' (status HELD_LABEL): HELD_RANGE over the '5 bars in all' reading and A / B;
  * one TOP BARS record per panel and direction: HELD_RANGE over the ledger's three readings (sheet note 2 'one third of
    the span', whole bar or each side, vs the p.15 0.30 L / 0.25 L detail): a conflict between two drawings, designer;
  * one DEVELOPMENT record per panel and direction: HELD_RANGE over note 9 (2 x 40 d .. 2 x 70 d per bar);
  * UNQUANTIFIED, never 0: the 13 slab panels with no printed bars (T-139 register ids), the GF-126 '6o14/m' zone (not
    delimited), the 1F-084 corner bars 12 x o14 (length not printed), temperature bars per floor (the p.15 schedule has
    no 160 mm row);
  * supersedes every route G slab steel line (item STR.REBAR, physical element SLABS, GF / 1F / 2F).

STAIR_POOL_TANK_STEEL (T-166, MERGED a9e1d63, checker 2026-10-22 06:25):
  * plan-printed main bars and landing strips (count HELD on the same notation) -> HELD_RANGE A .. B (C information);
    the round-stair rows are CALCULATED geometry (Q-50 A cond) and say so;
  * p.16 typical-only families -> HELD_RANGE A .. B with the reason TYPICAL_ONLY (no plan reference ties the N.I.S.
    section to these stairs; T-184 (MERGED 924c2bd) calls it the typical arrangement of the 'T 16' stair panels: that
    reading is for the checker / Lead to rule on, not for integration to settle);
  * top bars without a length, the corner landing whose bar direction is not drawn, the curved flight, the winders,
    the entrance and lobby flights, the water-tank walls -> UNQUANTIFIED (the ledger's candidate figures kept as
    information only);
  * development of every ranged record -> its own HELD_RANGE record (note 9);
  * POOL (R1 / R2): UNQUANTIFIED, both readings and their development kept as information. Two causes: (1) designer
    item D-57 (two-zone p.7 detail vs owner Q-26 A flat floor); (2) the T-166 bar lengths and hoop counts rest on a
    wall height of 1.15 m + 0.40 m floor = 1.55 m, and T-183 r2 (checker-merged 2026-10-22 16:14, lesson register s.7)
    established 1.15 m as the FINISHED water depth and the RC wall height as 1.20 m to the structure line: the ranges
    are known to rest on a superseded dimension, so they are not integrated as ranges until re-derived;
  * the GF landing strip over A1-L1 (18.204 kg at C = the frozen S8.7 figure) is owned ONCE by this ledger's line
    (register ruling 2026-10-22 04:20): the candidate has no route G stair steel line, so nothing else carries it.

DOME_RING (T-160, MERGED b5da75b, checker 2026-10-22 06:25):
  * west ring: RELEASED 0.7552 m3 = in-bay annulus 1.5105 m2 x 0.50 m (B4 20 x 50; two B4 labels in the bay), VERIFIED
    (the checker's own numerical integration 1.5105 m2 -> 0.7553 m3, 0.01 %);
  * east ring: UNQUANTIFIED (no mark within 3.2 m, p.7 depth 'as per architect': Q-61 C(3), designer D-28); its in-bay
    area 1.7994 m2 and the B4-if-confirmed candidate 0.8997 m3 kept as information;
  * supersedes, by name, the four route G arc band pieces of the west ring (1F BAND0033 / BAND0034 measured as B4,
    BAND0035 / BAND0036 unbound): the same physical ring, measured by route G only over its drawn arc bands; keeping
    them beside the hand line would count the ring twice (Q-61 C(2)). Identified on the route G 1F slab overlay: the
    four arc polygons lie between the two B6 bands and west of CB13, i.e. inside the west dome bay; no band exists in
    the east bay.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

T152 = {"file": "research/agents_t152/T152_SLAB_STEEL.csv", "task": "T-152 (suspended-slab steel by bar population)",
        "merge_commit": "798e3b9", "checker_run": "verifier 2026-10-22 00:35 UTC (MERGED 798e3b9; re-read GF-098 x "
        "90.825 m / y 104.988 m, 1F-084 x 39 x 4.30 / y 31 x 4.85, tank 2F-013 / 2F-011 T&B, 0.0 %)"}
T166 = {"file": "research/agents_t166/T166_STEEL.csv", "task": "T-166 (stair / pool / tank steel)",
        "merge_commit": "a9e1d63", "checker_run": "verifier 2026-10-22 06:25 UTC (MERGED a9e1d63; re-counted MS1-U "
        "main 10 x 3.7751 m = 59.656 kg 0.0 %, pool R1 outer verticals 88 x 1.55 m = 165.03 kg 0.0 %)"}
T160 = {"file": "research/agents_t160/DOME_RINGS.csv", "task": "T-160 (dome ring in-bay concrete)",
        "merge_commit": "b5da75b", "checker_run": "verifier 2026-10-22 06:25 UTC (MERGED b5da75b; own numerical "
        "integration west in-bay 1.5105 m2 x 0.50 = 0.7553 m3, 0.01 %; east HELD confirmed, in-bay 1.7995 m2)"}
T139_PANELS = "research/agents_t139/PANELS.csv"
# checker re-measures named in the T-152 / T-166 verdicts (the record keeps its HELD status: the count reading is open)
SLAB_REMEASURED = {("GF-098", "x"): "verifier 00:35: 23 x 4.20 m, p.15 length 90.825 m = 56.065 kg (0.0 %)",
                   ("GF-098", "y"): "verifier 00:35: 30 x 3.70 m, p.15 length 104.9875 m = 64.807 kg (0.0 %)",
                   ("1F-084", "x"): "verifier 00:35: 39 x 4.30 = 167.70 m face to face (0.0 %)",
                   ("1F-084", "y"): "verifier 00:35: 31 x 4.85 = 150.35 m face to face (0.0 %)",
                   ("2F-013", "x"): "verifier 00:35: tank T&B uncurtailed 116.27 kg with y (0.0 %)",
                   ("2F-013", "y"): "verifier 00:35: tank T&B uncurtailed 116.27 kg with x (0.0 %)",
                   ("2F-011", "x"): "verifier 00:35: tank T&B 119.80 m x 1.209877 = 144.94 kg with y (0.0 %)",
                   ("2F-011", "y"): "verifier 00:35: tank T&B 119.80 m x 1.209877 = 144.94 kg with x (0.0 %)"}
STAIR_REMEASURED = {"MS1-U": "verifier 06:25: 10 x 3.7751 m x 1.5802 = 59.656 kg at A (0.0 %)"}
# T-184 (MERGED 924c2bd) stair ids and the storey each T-166 element starts on
STAIR_ID = {"MS1-L": ("ST-01", "GF"), "MS1-U": ("ST-01", "GF"), "MS1-T": ("ST-01", "GF"),
            "GF-STRIP": ("ST-01", "GF"), "MS2-L": ("ST-01", "1F"), "MS2-U": ("ST-01", "1F"),
            "1F-STRIP": ("ST-01", "1F"), "RS-S": ("ST-02", "GF"), "RS-A": ("ST-02", "GF"),
            "RS-LD": ("ST-02", "GF"), "RS-C": ("ST-02", "GF"), "D1": ("ST-01b", "GF"), "E1": ("ST-03", "GROUND")}
RING_BANDS = [("P-C:BEAMS:1F:BAND0033", "B4 arc band (route G P-C) of the west dome ring"),
              ("P-C:BEAMS:1F:BAND0034", "B4 arc band (route G P-C; CB10 label conflict) of the west dome ring"),
              ("U-C:BEAMS:1F:BAND0035", "unbound arc band (route G U-C) of the west dome ring"),
              ("U-C:BEAMS:1F:BAND0036", "unbound arc band (route G U-C) of the west dome ring")]
NOTATION = ("COUNT_READING_HELD: the bars are printed 'n o d/m'; count A = ceil(rate x width), B = A + 1; the meaning "
            "of the notation is established for footings only (T-171, MERGED 701d227: maximum c/c spacing, N = "
            "ceil(L/s) + 1) and is not extended to {what} without its own evidence (ERS s.3); lengths measured")


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def rows(p):
    with open(ROOT / p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def f(x):
    return float(x) if x not in (None, "") else None


def rng(text):
    """'a..b' (first token) -> (min, max)"""
    a, b = (float(v) for v in str(text).split()[0].split(".."))
    return min(a, b), max(a, b)


def r6(x):
    return round(x, 6)


# ================================================================================================ slab steel (T-152)
def slab_records(t152_rows, panels):
    recs = []
    for r in t152_rows:
        pnl, fl, dr, d = r["panel"], r["floor"], r["direction"], int(r["d_mm"])
        a = f(r["kg_A"]) + f(r["kg_cross_A"])
        b = f(r["kg_B"]) + f(r["kg_cross_B"])
        readings = {"A_count": int(r["bars_A"]), "B_count": int(r["bars_B"]), "A_kg": r6(a), "B_kg": r6(b),
                    "C_info_kg": f(r["kg_C_info"]), "layers": int(r["layers"]), "spread_m": f(r["spread_m"]),
                    "len_p15_A_m": f(r["len_p15_A_m"]), "len_p15_B_m": f(r["len_p15_B_m"])}
        base = {"element": f"SLAB:{pnl}", "floor": fl, "dia_mm": d, "printed": f"{r['printed']} (panel {pnl}, {dr})"}
        if r["status"] == "HELD_LABEL":
            m = re.search(r"count reading (\d+) bars = ([\d.]+) kg", r["note"])
            five = float(m.group(2))
            readings["label_count_reading_kg"] = five
            lo, hi = min(five, a, b), max(five, a, b)
            reasons = [f"LABEL_WITHOUT_PER_METRE: {r['note']}; readings {m.group(1)} bars in all {five} kg, A {a:.3f}, "
                       f"B {b:.3f} kg"]
        elif r["status"] == "MEASURED_NET_COUNT_HELD_Q71":
            lo, hi = min(a, b), max(a, b)
            reasons = [NOTATION.format(what="suspended slabs") + f": A {a:.3f} kg, B {b:.3f} kg (C {r['kg_C_info']} "
                       "information: an unrounded count is not a bar population)"]
        else:
            raise ValueError(f"T-152 row {pnl} {dr}: status {r['status']!r} not mapped")
        if r["note"] and r["status"] != "HELD_LABEL":
            reasons.append(f"ledger note: {r['note']}")
        rec = dict(base, component="BOTTOM MESH", part=dr, state="HELD_RANGE", low=r6(lo), high=r6(hi),
                   readings=readings, reasons=reasons,
                   range_basis="count readings A .. B with their crossing halves (p.15 curtailment)",
                   formula=f"count x bar length (p.15 curtailment) x {d}^2/162 + crossing half; "
                           f"A {readings['A_count']} / B {readings['B_count']} bars")
        if (pnl, dr) in SLAB_REMEASURED:
            rec["info"] = {"checker_remeasure": SLAB_REMEASURED[(pnl, dr)]}
        recs.append(rec)
        tlo, thi = rng(r["top_held_kg"])
        m = re.search(r"crossing ([\d.]+)\.\.([\d.]+)", r["top_held_kg"])
        cross = max(float(m.group(1)), float(m.group(2))) if m else 0.0
        thi = r6(thi + cross)       # the half that crosses the beam exists only under the 'each side' readings (T-152)
        recs.append(dict(base, component="TOP BARS OVER SUPPORTS", part=dr, state="HELD_RANGE", low=tlo, high=thi,
                         readings={"ledger": r["top_held_kg"]},
                         reasons=["TOP_EXTENT_CONFLICT: sheet note 2 'top 5o10/m over beams for one third of the span' "
                                  "(whole bar or each side) vs the p.15 typical detail (0.30 max(L1, L2), 0.25 L1 at a "
                                  "non-continuous support): two drawings disagree, designer item; three readings "
                                  "+ crossings"],
                         range_basis="reading i (no crossing) .. max(ii, p.15) + the crossing half"))
        dlo, dhi = rng(r["dev_held_kg"])
        recs.append(dict(base, component="DEVELOPMENT / ANCHORAGE", part=dr, state="HELD_RANGE", low=dlo, high=dhi,
                         readings={"ledger": r["dev_held_kg"]},
                         reasons=["DEVELOPMENT_NOT_DIMENSIONED: note 9 prints 40 d .. 70 d per bar end (which applies "
                                  "where is not drawn): 2 x 40 d .. 2 x 70 d per bar"],
                         range_basis="note 9 2 x 40 d .. 2 x 70 d per bar"))
    have = {r["panel"] for r in t152_rows}
    for p in panels:
        if p["cls"] == "SLAB" and p["id"] not in have:
            recs.append({"element": f"SLAB:{p['id']}", "floor": p["floor"], "component": "ALL BARS",
                         "state": "UNQUANTIFIED",
                         "reasons": [f"NO_BARS_PRINTED: slab panel {p['id']} ({p['area']} m2, {p['evidence']}) carries "
                                     "no bar label on its roof-slab plan (p.4 / p.5 / p.7 / p.16 searched): designer "
                                     "item, never 0"]})
    return recs


def slab_held_extras():
    """the development villa's held slab-steel items that have no ledger row (T-152 section 1 'HELD, never 0')."""
    recs = [
        {"element": "SLAB:GF-126", "floor": "GF", "component": "SECOND BAR 6o14/m ZONE", "state": "UNQUANTIFIED",
         "dia_mm": 14, "reasons": ["ZONE_NOT_DELIMITED: a second horizontal bar '6o14/m' (hooked at its west end) is "
                                   "drawn in the south part of the panel by the round stair; its zone is not delimited "
                                   "(designer item)"]},
        {"element": "SLAB:1F-084", "floor": "1F", "component": "CORNER BARS 12 o14", "state": "UNQUANTIFIED",
         "dia_mm": 14, "reasons": ["LENGTH_NOT_PRINTED: 12 corner bars o14 are printed; their length is not "
                                   "dimensioned (designer item)"]}]
    for fl in ("GF", "1F", "2F"):
        recs.append({"element": f"SLAB:{fl}", "floor": fl, "component": "TEMPERATURE BARS", "state": "UNQUANTIFIED",
                     "reasons": ["TEMPERATURE_ROW_NOT_PRINTED: the p.15 temperature-reinforcement schedule prints rows "
                                 "100 / 125 / 150 / 175 / 200 / 250 / 300 mm and none for the 160 mm slabs"]})
    return recs


# ================================================================================================ stair / pool / tank (T-166)
def _sid(el):
    key = el.split(" ")[0]
    if key not in STAIR_ID:
        raise ValueError(f"T-166 element {el!r}: no stair id")
    return STAIR_ID[key]


def stair_development(r):
    """note 9 development of one T-166 bar family as a held range whose ends follow the held count (T-179 r2,
    D-T179-1): low = count A x 2 x 40 d, high = count B x 2 x 70 d, x d^2/162 kg/m, rounded to the ledger's 0.01 kg.

    Why not the ledger's high: the merged T-166 column 'dev_held_kg' typed 2 x 70 d x count A at the high end although
    the count itself is held A .. B (the slab lines of this package already use count B). A held range must contain
    every physical reading, so the high end takes the highest count. The ledger text is kept as a reading. The ledger
    low must equal count A x 2 x 40 d and the ledger high must be one of the two count readings at 2 x 70 d; any other
    ledger value is refused (re-type the row), never silently overwritten."""
    d = int(r["d"])
    na, nb = f(r["n_A"]), f(r["n_B"])
    if na is None or nb is None:
        raise ValueError(f"T-166 row {r['element']} {r['part']}: development without both count readings")
    kgm = d * d / 162.0
    lo_calc = round(min(na, nb) * 2 * 0.040 * d * kgm, 2)
    hi_a, hi_b = (round(n * 2 * 0.070 * d * kgm, 2) for n in (na, nb))
    hi_calc = max(hi_a, hi_b)
    lo_led, hi_led = rng(r["dev_held_kg"])
    if abs(lo_led - lo_calc) > 0.011 or min(abs(hi_led - hi_a), abs(hi_led - hi_b)) > 0.011:
        raise ValueError(f"T-166 row {r['element']} {r['part']}: development {r['dev_held_kg']} is not note 9 on "
                         f"counts {na:g} .. {nb:g} (expected {lo_calc} .. {hi_a} / {hi_b}): re-type the row")
    why = []
    if abs(hi_led - hi_calc) > 0.011:
        why = [f"HIGH_FROM_COUNT_B: ledger high {hi_led} kg = count {min(na, nb):g} x 2 x 70 d; the count is held "
               f"{na:g} .. {nb:g}, so the high end is {max(na, nb):g} x 2 x 70 d = {hi_calc} kg (T-179 r2, D-T179-1)"]
    return lo_led, hi_calc, why


def stair_records(t166_rows):
    recs = []
    for r in t166_rows:
        el, part, st = r["element"], r["part"], r["status"]
        d = int(r["d"])
        a, b, c = f(r["kg_A"]), f(r["kg_B"]), f(r["kg_C"])
        info = {"ledger_status": st, "count_A": f(r["n_A"]), "count_B": f(r["n_B"]), "count_C": f(r["n_C"]),
                "length_m": r["length_m"] or None, "A_kg": a, "B_kg": b, "C_info_kg": c,
                "development_kg": r["dev_held_kg"] if r["dev_held_kg"] not in ("", "-") else None,
                "ledger_note": r["note"]}
        if el.startswith("POOL"):
            pe, fl, eid = "POOL", "GROUND", "POOL:" + ("R1" if " R1 " in f" {el} " else "R2")
        elif el.startswith("WATER TANK"):
            pe, fl, eid = "WATER_TANK", "2F", "TANK:2F"
        else:
            sid, fl = _sid(el)
            pe, eid = "STAIRS", f"{sid}:{el.split(' ')[0]}"
        base = {"element": eid, "floor": fl, "component": part, "physical_element": pe, "dia_mm": d,
                "printed": r["mark"] + (f" ({r['page']})" if r.get("page") else "")}
        if st in ("MEASURED_NET_COUNT_HELD_Q71", "CALCULATED_COUNT_HELD_Q71", "HELD_TYPICAL_ONLY"):
            why = (NOTATION.format(what="stairs") if st != "HELD_TYPICAL_ONLY" else
                   "TYPICAL_ONLY: the family exists only on the p.16 TYPICAL STEEL LAYOUT - STAIR SECTION (N.I.S.); no "
                   "plan callout ties it to this flight (T-166); T-184 (MERGED 924c2bd) reads p.16 as the typical "
                   "arrangement of the 'T 16' stair panels: for the checker / Lead to rule, not settled here")
            if st == "CALCULATED_COUNT_HELD_Q71":
                why += "; geometry CALCULATED (round stair, owner Q-50 A cond)"
            rec = dict(base, state="HELD_RANGE", low=min(a, b), high=max(a, b),
                       readings={"A_kg": a, "B_kg": b, "C_info_kg": c}, reasons=[why + f": A {a} kg, B {b} kg"],
                       range_basis="count readings A .. B (C unrounded: information)",
                       formula=f"count x {r['length_m']} m x {d}^2/162", info=info)
            if el.split(" ")[0] in STAIR_REMEASURED and part.startswith("main"):
                rec["info"] = dict(info, checker_remeasure=STAIR_REMEASURED[el.split(" ")[0]])
            if el.startswith("GF-STRIP") and "bottom" in part:
                rec["info"] = dict(rec["info"], register="owned once here (register 2026-10-22 04:20): the frozen "
                                   "S8.7 GF strip 18.204 kg (= C) is not a candidate line; no route G stair steel line "
                                   "exists to supersede")
            recs.append(rec)
            if r["dev_held_kg"] not in ("", "-"):
                lo, hi, why_hi = stair_development(r)
                recs.append(dict(base, component=part, part="DEVELOPMENT", state="HELD_RANGE", low=lo, high=hi,
                                 readings={"ledger": r["dev_held_kg"], "count_A": f(r["n_A"]), "count_B": f(r["n_B"])},
                                 reasons=["DEVELOPMENT_NOT_DIMENSIONED: note 9 (2 x 40 d .. 2 x 70 d per bar)"]
                                 + (["TYPICAL_ONLY family"] if st == "HELD_TYPICAL_ONLY" else []) + why_hi,
                                 range_basis="note 9: count A x 2 x 40 d .. count B x 2 x 70 d per bar (the count is "
                                             "held A .. B, so each end takes its own count reading)"))
            continue
        if st.startswith("HELD_DESIGNER"):
            reasons = ["POOL_POPULATION_DESIGNER: p.7 prints two zones (deep-end R1 / shallow-end R2) for a pool the "
                       "owner ruled flat (Q-26 A): which population serves the floor is designer item D-57",
                       "POOL_GEOMETRY_SUPERSEDED: the bar lengths and hoop counts rest on wall 1.15 + floor 0.40 = 1.55 m; "
                       "T-183 r2 (checker-merged 2026-10-22 16:14) fixes the RC wall height at 1.20 m to the structure "
                       "line (1.15 m is the finished water depth): re-derive before any range is integrated"]
        elif st == "HELD_LENGTH":
            reasons = [f"LENGTH_NOT_DIMENSIONED: {r['note']}"]
        elif st == "HELD_DIRECTION":
            reasons = [f"BAR_DIRECTION_NOT_DRAWN: {r['note']}"]
        elif st == "NOT_PRINTED":
            reasons = [f"NOT_PRINTED: {r['note']}"]
        elif st == "HELD":
            reasons = [f"NOT_DRAWN_OR_HELD: {r['note']}"]
        else:
            raise ValueError(f"T-166 row {el} {part}: status {st!r} not mapped")
        recs.append(dict(base, state="UNQUANTIFIED", reasons=reasons, info=info))
    return recs


# ================================================================================================ dome ring (T-160)
def ring_records(t160_rows):
    recs = []
    for r in t160_rows:
        if r["part"] != "DOME":
            continue
        if r["dome"].endswith("-W"):
            if r["status"] != "CALCULATED" or f(r["ring_depth_m"]) != 0.5:
                raise ValueError("T-160 west ring row changed: re-type it")
            recs.append({"element": f"{r['dome']}:RING", "floor": "1F", "component": "RING BEAM B4 IN BAY",
                         "state": "RELEASED", "value": f(r["ring_m3"]), "geometry_source": "CAD_VECTOR",
                         "printed": "B4 20 x 50 (two B4 labels inside the bay, 1F roof-slab plan; Q-44 A)",
                         "formula": f"in-bay annulus {r['ring_in_bay_m2']} m2 (full {r['annulus_full_m2']} m2 less the "
                                    f"parts inside the framing beams / beyond them) x {r['ring_depth_m']} m",
                         "verified_by": "verifier 2026-10-22 06:25 UTC: own numerical integration 1.5105 m2 x 0.50 = "
                                        "0.7553 m3 (0.01 %)",
                         "info": {"in_bay_m2": f(r["ring_in_bay_m2"]), "full_annulus_m2": f(r["annulus_full_m2"]),
                                  "double_count_avoided_m3": f(r["double_count_avoided_m3"]),
                                  "steel": "the same ring is beam BM-1F-028 (B4, clear length 7.553 m = 1.5105 m2 / "
                                           "0.20) in the T-149 beam steel ledger, integrated in V3.0.3: its steel is "
                                           "there, never added again here"}})
        else:
            recs.append({"element": f"{r['dome']}:RING", "floor": "1F", "component": "RING BEAM IN BAY",
                         "state": "UNQUANTIFIED", "geometry_source": "CAD_VECTOR",
                         "reasons": ["RING_SECTION_NOT_PRINTED: no B4 (or other) mark on or near this ring and the "
                                     "dome detail says depth 'as per architect' (owner Q-61 C(3); designer D-28)"],
                         "info": {"in_bay_m2": f(r["ring_in_bay_m2"]), "candidate_if_b4_m3": f(r["candidate_m3"])}})
    return recs


# ================================================================================================ inputs
def _sum(recs, state, key):
    return round(sum(r[key] for r in recs if r["state"] == state), 6)


def inputs(project_id):
    panels = rows(T139_PANELS)
    s = slab_records(rows(T152["file"]), panels) + slab_held_extras()
    t = stair_records(rows(T166["file"]))
    g = ring_records(rows(T160["file"]))
    led = [
        {"piece": "SLAB_STEEL", "item_code": "STR.REBAR", "unit": "kg", "source": dict(T152, sha256=sha(T152["file"])),
         "scope": {"physical_element": "SLABS", "floors": ["GF", "1F", "2F"], "supersede": "ELEMENT_AND_FLOORS"},
         "drawing_reference": "structural set p.4 / p.5 / p.6 roof-slab plans, p.15 TYP. SLAB ON BEAMS + temperature "
                              "schedule, p.8 notes 9 / 22", "records": s,
         "declared_totals": {"held_low": _sum(s, "HELD_RANGE", "low"), "held_high": _sum(s, "HELD_RANGE", "high")}},
        {"piece": "STAIR_POOL_TANK_STEEL", "item_code": "STR.REBAR", "unit": "kg",
         "source": dict(T166, sha256=sha(T166["file"])),
         "scope": {"physical_element": "STAIRS", "floors": ["GROUND", "GF", "1F", "2F"],
                   "supersede": "ELEMENT_AND_FLOORS"},
         "drawing_reference": "structural set p.4 / p.5 stair callouts, p.16 typical stair section, p.7 pool detail, "
                              "p.6 tank place", "records": t,
         "declared_totals": {"held_low": _sum(t, "HELD_RANGE", "low"), "held_high": _sum(t, "HELD_RANGE", "high")}},
        {"piece": "DOME_RING", "item_code": "STR.CONC.BEAM", "unit": "m3", "source": dict(T160, sha256=sha(T160["file"])),
         "scope": {"physical_element": "BEAMS", "floors": ["1F"], "supersede": "NAMED_LINES",
                   "lines": [{"element_id": e, "floor": "1F", "why": w + " (T-160: one ring, measured once)"}
                             for e, w in RING_BANDS]},
         "drawing_reference": "structural set p.5 1F roof slab (dome bays, B4 labels), p.7 dome detail", "records": g,
         "declared_totals": {"released": _sum(g, "RELEASED", "value")}},
    ]
    return {"schema": "URBAN_V305_VERIFIED_LEDGERS_V1", "project": project_id, "ledgers": led}


def summary(doc):
    out = {}
    for lg in doc["ledgers"]:
        c = {}
        for r in lg["records"]:
            k = c.setdefault(r["state"], {"records": 0, "value": 0.0, "low": 0.0, "high": 0.0})
            k["records"] += 1
            for x in ("value", "low", "high"):
                if r.get(x) is not None:
                    k[x] = round(k[x] + r[x], 6)
        out[lg["piece"]] = c
    return out


if __name__ == "__main__":
    import sys
    d = inputs(sys.argv[1] if len(sys.argv) > 1 else "ST7757 villa (structural set)")
    print(json.dumps(summary(d), indent=1))
