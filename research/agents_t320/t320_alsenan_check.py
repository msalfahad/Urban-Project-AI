"""T-320 on the development villa: the buried-structure DISPLACEMENT ledger below the existing ground (zone Z1), built
ONLY from merged, Checker-gated research ledgers (values, DXF handles and coordinates; no drawing content copied):

  T-170 pits (ALSENAN_EXCAVATION_INPUT.json: outlines, schedule H, EG +-0.00, formation limit -1.50, detail p.13)
  T-233 blinding beyond the plot line per outline (D-14), F10 + F (1B1B) ranges, strap / boundary-band holds, FF
  T-205 necks (section, footing outline), T-174 / T-230 straps, T-242 / T-253 ground-beam runs and the N.G. datum,
  T-183 r2 pool (levels, layers, plan), T-189 pool frame (F8 position), T-204 lift pit.

Run: python3 -I research/agents_t320/t320_alsenan_check.py  ->  LEDGER_T320.csv, summary.json beside this file.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import displacement_ledger_v1 as X  # noqa: E402

LIMIT = -1.50                      # ST p.9 note 1 'not less than 1.5 m below the existing plot level' (AT_MOST)
STACK = 0.17                       # blinding 0.10 + underlay 0.07 (T-206 VERIFIED)
MAIN_TOP, ANNEX_TOP = 0.95, 0.25   # structural slab tops on dry floors (T-214 MERGED), ground-beam tops (T-242)
DEPTH_BY_TITLE = {"GB-LT2_5M": 0.30, "GB-LT5M": 0.40, "GB-GT5M": 0.60}   # p.13 interior classes


def _load(p):
    return json.loads((RES / p).read_text())


def _csv(p):
    with open(RES / p, newline="") as f:
        return list(csv.DictReader(f))


def pool_geometry():
    """D-shaped pool (T-183 r2): outer r 1.75 + 3.50 x 1.75, water r 1.55; envelope = outer offset by screed 0.05 +
    membrane 0.05 (p.7: both under the base and up the outer walls), offset area A + P t + pi t^2."""
    r, rw = 1.75, 1.55
    A0 = 3.50 * 1.75 + math.pi * r * r / 2
    P0 = 3.50 + 2 * 1.75 + math.pi * r
    Aw = 3.10 * 1.55 + math.pi * rw * rw / 2
    off = lambda t: A0 + P0 * t + math.pi * t * t  # noqa: E731
    return {"A0": A0, "P0": P0, "Aw": Aw, "band": A0 - Aw, "A05": off(0.05), "A10": off(0.10)}


def f8_in_pool():
    """Plan overlap of F8 (footprint and neat blinding) with the pool envelope A10, in the T-189 pool frame (half
    circle centre = origin, +x towards the straight back). shapely, 256 segments per quarter (chord error < 1e-5 m2)."""
    from shapely.geometry import Point, box
    fr = _load("agents_t189/ALSENAN_OVERLAP_INPUT.json")["pool"]
    r, bx = fr["outline"]["r_outer"], fr["outline"]["back_x"]
    d = Point(0, 0).buffer(r, quad_segs=256).intersection(box(-r, -r, 0, r)).union(box(0, -r, bx, r))
    env = d.buffer(0.10, quad_segs=256)
    (x0, x1), (y0, y1) = fr["F8"]["x"], fr["F8"]["y"]
    ftg, neat = box(x0, y0, x1, y1), box(x0 - 0.1, y0 - 0.1, x1 + 0.1, y1 + 0.1)
    return {"footprint_in_outer_m2": ftg.intersection(d).area, "footprint_in_env_m2": ftg.intersection(env).area,
            "neat_in_env_m2": neat.intersection(env).area, "env_area_numeric_m2": env.area}


def spec():
    inp = _load("agents_t170/ALSENAN_EXCAVATION_INPUT.json")
    t233 = {o["id"]: o for o in _load("agents_t233/ALSENAN_FOOTING_INPUT.json")["outlines"]}
    eg = inp["levels"]["existing_ground"]
    groups, comps, shared, notes = {}, [], [], []
    pit_of_outline, centres = {}, []
    beyond_plot = {}
    for f in inp["footings"]:
        gid = "PIT:" + f["id"]
        h = next(t for t in re.findall(r"[0-9A-F]{3,4}", f["outline"]) if not t.isdigit() or len(t) == 4)
        f["outline"] = h
        pit_of_outline[h] = gid
        centres.append((f["type"], (f["x0_mm"] + f["dx_mm"] / 2) / 1000, (f["y0_mm"] + f["dy_mm"] / 2) / 1000, gid))
        groups[gid] = {"formation": {"limit": LIMIT}, "kind": "PIT"}
        if f["type"] in ("FF", "F10/F") or f["detail"] != "ISOLATED_P13":
            continue                                      # the two held pits are added below by name
        x0, y0 = f["x0_mm"] / 1000, f["y0_mm"] / 1000
        x1, y1 = x0 + f["dx_mm"] / 1000, y0 + f["dy_mm"] / 1000
        H = f["schedule_L_W_H_m"][2]
        src = f"T-170 pit {f['type']} outline {f['outline']} (ST DXF FOUNDATION PLAN); p.13 10 / 7 / H chain"
        comps += [
            {"id": gid + ":BLINDING", "group": gid, "kind": "BLINDING", "rect": [x0 - .1, y0 - .1, x1 + .1, y1 + .1],
             "z": [{"form": 0.0}, {"form": 0.10}], "source": src},
            {"id": gid + ":UNDERLAY", "group": gid, "kind": "UNDERLAY", "rect": [x0, y0, x1, y1],
             "z": [{"form": 0.10}, {"form": STACK}], "source": src + "; underlay 0.07 (T-206, T-219)"},
            {"id": gid + ":FOOTING", "group": gid, "kind": "FOOTING", "rect": [x0, y0, x1, y1],
             "z": [{"form": STACK}, {"form": STACK + H}], "source": src + f"; H {H:.2f} (p.9 schedule)"},
        ]
        out = t233.get(f["outline"], {}).get("blind_outside_m2", 0.0)
        if out:
            beyond_plot[gid] = out
    # F10 + F (1B1B, one open outline, two tags; Q-31 C): every reading lies wholly below EG (top <= -0.83)
    g10 = pit_of_outline["1B1B"]
    for k, rng, why in (("FOOTING", (2.176, 2.275), "(A) schedule rows separately / (B) drawn outline x H 0.50"),
                        ("BLINDING", (0.5025, 0.590), "follows its footing"),
                        ("UNDERLAY", (4.55 * 0.07, (2.80 * 1.40 + 0.90 * 0.80) * 0.07), "outline / rows x 0.07")):
        comps.append({"id": f"{g10}:{k}", "group": g10, "kind": k, "range": list(rng), "status": X.HELD,
                      "held": ["FOOTING_CONFLICT (Q-31 C)"], "source": f"T-233 1B1B: {why}",
                      "info": "wholly below EG in every reading (footing top <= formation + 0.67 <= -0.83)"})
    # FF lift footing: the pit floor is 'as per lift manufacturer' (p.14, T-204); its level vs EG is not printed
    gff = pit_of_outline["1B2B"]
    groups[gff]["formation"] = None
    comps += [
        {"id": gff + ":FOOTING", "group": gff, "kind": "FOOTING", "range": [0.0, 11.385], "status": X.HELD,
         "held": ["PIT_DEPTH_NOT_PRINTED (p.14 'as per lift manufacturer')"],
         "source": "T-233 FF 4.60 x 4.50 x 0.55 = 11.385 (AGREE); below-EG share HELD with the pit floor"},
        {"id": gff + ":BLINDING", "group": gff, "kind": "BLINDING", "range": [0.0, 2.256], "status": X.HELD,
         "held": ["PIT_DEPTH_NOT_PRINTED", "LEDGER_DISAGREEMENT T-233 2.256 (+0.10 projection) vs T-170 HELD "
                  "(p.14 projection not dimensioned)"], "source": "T-233 / T-170"},
        {"id": gff + ":PIT_SHELL_AND_VOID", "group": gff, "kind": "LIFT_PIT", "status": X.HELD,
         "held": ["PIT_DEPTH_NOT_PRINTED"], "source": "T-204: ring 1.60 m2 gross (columns 0.50 inside), envelope "
         "4.89 m2", "info": "4.89 m3 per m of pit below EG (shell + void); FF top level HELD"},
        {"id": gff + ":UNDERLAY", "group": gff, "kind": "UNDERLAY", "status": X.HELD,
         "held": ["UNDERLAY_NOT_PRINTED (p.14)"], "source": "T-170 / T-219"},
    ]
    # necks: below-EG part only, footing top -> EG; top clipped at EG (every neck ends at a ground-beam top >= +0.25)
    nin = {n["id"]: n for n in _load("agents_t205/ALSENAN_NECK_INPUT.json")["necks"]}
    for n in _csv("agents_t205/LEDGER_T205.csv"):
        ft = nin[n["neck_id"]]["footing"]
        gid = pit_of_outline.get(ft.get("outline_handle"))
        if gid is None:                                   # footing without an outline handle (FN of 4 LINEs):
            xy = [float(v) / 1000 for v in n["neck_id"].rsplit("@", 1)[1].split(",")]   # nearest of its type
            gid = min((math.hypot(cx - xy[0], cy - xy[1]), g) for t, cx, cy, g in centres if t == n["footing"])[1]
        base = {"id": "NECK:" + n["neck_id"].split(":", 2)[-1], "group": gid, "kind": "NECK",
                "source": f"T-205 {n['type']} on {n['footing']} (outline {ft.get('outline_handle')})"}
        if n["section_status"] == "DRAWING-CONFIRMED" and n["footing_H_m"] and "|" not in n["footing"]:
            H = float(n["footing_H_m"])
            comps.append(dict(base, plan=float(n["section_m2"]), z=[{"form": STACK + H}, {"abs": 0.0}],
                              info="top clipped at EG: the part above EG (to the GB top) is zone Z2"))
        elif "SECTION_CONFLICT" in n["held_codes"] and n["footing"] not in ("FF",):
            lo, hi = (float(v) for v in n["section_range_m2"].strip("()").split(","))
            h = -LIMIT - STACK - float(n["footing_H_m"])
            comps.append(dict(base, range=[lo * h, hi * h], status=X.CONFLICT,
                              held=["SECTION_CONFLICT", "FORMATION_ONLY_A_LIMIT (range at d = 0, AT_LEAST)"]))
        elif n["footing"] == "F10|F":
            A = float(n["section_m2"])
            comps.append(dict(base, group=g10, range=[A * (-LIMIT - STACK - 0.50), A * (-LIMIT - STACK - 0.30)],
                              status=X.HELD, held=["FOOTING_CONFLICT (Q-31 C)", "FORMATION_ONLY_A_LIMIT"]))
        else:
            comps.append(dict(base, group=gff, status=X.HELD,
                              held=[c for c in n["held_codes"].split("|") if c] or ["HELD"]))
    # straps: merged volumes outside the footings; wholly below EG because each end is cast against a footing face
    trench = {"TRENCH:STRAPS": {"formation": None, "kind": "TRENCH"}}
    groups.update(trench)
    st = {"SB1": 1.5925, "SB2": 1.1464, "SB3": 0.6516}
    basis = ("cast against the footing faces at both ends (T-174), so the strap bottom is below the footing top <= "
             "formation + 0.17 + H <= -0.83 (H 0.50) / -0.93 (H 0.40); top < footing top + D <= -0.33")
    for k, v in st.items():
        comps.append({"id": "STRAP:" + k, "group": "TRENCH:STRAPS", "kind": "STRAP", "value": v,
                      "below_eg_basis": basis, "source": "T-174 / T-230 (MERGED; Checker 14:52 SB2 / SB3)"})
    comps += [
        {"id": "STRAP:SB3_IN_F3", "group": "TRENCH:STRAPS", "kind": "STRAP", "range": [0.0295, 0.2683],
         "status": X.HELD, "held": ["STRAP_SOFFIT_NOT_PRINTED (D-15, T-230)"], "source": "T-233"},
        {"id": "STRAP:SB1_IN_F10F", "group": "TRENCH:STRAPS", "kind": "STRAP", "range": [0.0, 0.385],
         "status": X.HELD, "held": ["FOOTING_CONFLICT (Q-31 C)"], "source": "T-233 / T-231"},
        {"id": "STRAP:BLINDING", "group": "TRENCH:STRAPS", "kind": "BLINDING", "range": [0.0, 0.913],
         "status": X.HELD, "held": ["NONE_PRINTED_UNDER_STRAPS (D-15)"], "source": "T-233 / T-100"},
    ]
    # ground beams: EG = the outer normal ground +-0.00 (T-253 Gate A); below-EG part and blinding (p.13 10 / 30 / 10)
    groups["TRENCH:GB"] = {"formation": None, "kind": "TRENCH"}
    for i, r in enumerate(_csv("agents_t253/LEDGER_T253.csv")):
        L, b = float(r["L_m"] or 0), float(r["b_m"] or 0)
        if r["component"].startswith("GB-EXTERIOR MAIN"):
            rid = f"GB:EXT-MAIN#{i}"
            comps += [
                {"id": rid, "group": "TRENCH:GB", "kind": "GROUND_BEAM", "plan": L * b,
                 "z": [{"abs": 0.0}, {"abs": MAIN_TOP}], "source": "T-253 main exterior run L %.4f" % L},
                {"id": rid + ":BLINDING", "group": "TRENCH:GB", "kind": "BLINDING", "plan": L * (b + 0.20),
                 "z": [{"abs": -0.10}, {"abs": 0.0}], "source": "p.13 exterior section '10 / 30 / 10' (T-253, T-233 "
                 "finding 2: own layer for the drawn beams)"}]
        elif r["component"].startswith("BOUNDARY-GB at N.G."):
            comps.append({"id": f"GB:BOUNDARY-UPPER#{i}", "group": "TRENCH:BOUNDARY", "kind": "GROUND_BEAM",
                          "plan": L * b, "z": [{"abs": -0.40}, {"abs": 0.0}],
                          "source": "T-253 p.14 A-A upper G.B 20 x 40, top at N.G.",
                          "info": "the 20 x 30 columns inside the band (positions not drawn) change the concrete "
                                  "line split, not the displaced solid"})
    groups["TRENCH:BOUNDARY"] = {"formation": None, "kind": "TRENCH"}
    comps += [
        {"id": "BOUNDARY:LOWER_BAND", "group": "TRENCH:BOUNDARY", "kind": "GROUND_BEAM", "range": [5.639, 11.033],
         "status": X.HELD, "held": ["Q-28 A PROVISIONAL (section C1 vs 20 x 40, crossing levels at 10 footings)"],
         "source": "T-233 boundary band"},
        {"id": "BOUNDARY:BRICK_BELOW_NG_AND_PADS", "group": "TRENCH:BOUNDARY", "kind": "WALL_AND_PADS",
         "status": X.HELD, "held": ["'AS PER EXCAVATION DEPTH BELOW N.G. LEVEL' (p.14): depth not printed; "
                                    "pads 130 x 80 x 30 count not printed (Q-28)"], "source": "T-253 / Q-28"},
    ]
    for r in _csv("agents_t242/LEDGER_T242.csv"):
        c, part, L, b = r["component"], r["part"], float(r["L_m"] or 0), float(r["b_m"] or 0)
        rid = "GB:" + r["run"]
        if c.startswith("GB-EXTERIOR") and part == "MAIN":
            continue                                       # taken from T-253 above (same runs, datum applied)
        if c.startswith("GB-EXTERIOR") and part == "ANNEX":
            blind = L * (b + 0.20) * 0.10
            comps.append({"id": rid, "group": "TRENCH:GB", "kind": "GROUND_BEAM", "status": X.CONFLICT,
                          "held": ["D-35 annex: reading L (FOLLOW ARCH., D 0.25, bottom at N.G.) vs reading S "
                                   "(section deeper than 0.25, no value)"], "source": "T-242 / T-253 s.3",
                          "info": f"reading L only (information, not adopted): beam 0 below EG + blinding "
                                  f"{blind:.4f} m3"})
            continue
        if c.startswith("GB-COURT"):
            comps.append({"id": rid, "group": "TRENCH:GB", "kind": "GROUND_BEAM", "status": X.HELD,
                          "held": ["NO_PRINTED_SECTION (court run)"], "source": "T-253 s.4"})
            continue
        if not c.startswith("GB-INTERIOR"):
            continue
        top = MAIN_TOP if part == "MAIN" else ANNEX_TOP
        titles = [t for t in r["titles"].split("+") if t in DEPTH_BY_TITLE]
        d33 = "D-33" in r["reasons"]
        if d33:
            comps.append({"id": rid, "group": "TRENCH:GB", "kind": "GROUND_BEAM", "status": X.HELD,
                          "held": ["D-33: section of a beam receiving another beam not printed"],
                          "source": "T-242 / T-253 s.5",
                          "info": ("zero below EG while D <= 0.85 (top +0.95)" if part == "MAIN" else
                                   "if p.13 applied (D 0.40): beam %.4f + blinding %.4f m3" % (
                                       0.15 * b * L, L * (b + 0.2) * 0.1))})
            continue
        ds = sorted({DEPTH_BY_TITLE[t] for t in titles})
        if part == "MAIN" or len(ds) == 1:
            D = max(ds)                                    # main: the deepest candidate still clears EG
            st = X.ZERO_BY_BOUND if part == "MAIN" else X.DRAWING_CONFIRMED
            cond = (["condition: GB top >= D + 0.10 above EG (b_wet <= 0.30 m under a wet floor; dry b 0.05, "
                     "T-214)"] if part == "MAIN" else [])
            src = "T-242 %s %s run (%s, D %s, top %+.2f)" % (part.lower(), "interior", r["status"], ds, top)
            comps += [
                {"id": rid, "group": "TRENCH:GB", "kind": "GROUND_BEAM", "plan": L * b, "status": st,
                 "held": cond, "z": [{"abs": top - D}, {"abs": top}], "source": src},
                {"id": rid + ":BLINDING", "group": "TRENCH:GB", "kind": "BLINDING", "plan": L * (b + 0.20),
                 "status": st, "held": list(cond), "z": [{"abs": top - D - 0.10}, {"abs": top - D}],
                 "source": src + "; p.13 10 / 30 / 10"}]
        else:
            vals = [b * L * max(0.0, D - top) + L * (b + 0.20) * 0.10 for D in ds]
            comps.append({"id": rid, "group": "TRENCH:GB", "kind": "GROUND_BEAM", "range": [min(vals), max(vals)],
                          "status": X.HELD, "held": ["D-34 title / length basis %s" % ds],
                          "source": "T-242 annex interior (top +0.25): beam below EG + its blinding (wholly below "
                                    "EG, top 0.25 - D <= -0.05)"})
    # lower ground-beam row of the two-beam detail (p.13): exists only if GB top - footing bottom > 2.5 m
    comps.append({"id": "GB:LOWER_ROW_TWO_BEAM_DETAIL", "group": "TRENCH:GB", "kind": "GROUND_BEAM", "status": X.HELD,
                  "held": ["exists iff 2.28 + d > 2.50 (main house, d > 0.22 m below the limit); no plan draws it"],
                  "source": "p.13 / T-205 / T-042 B3"})
    # pool (T-183 r2: formation -1.50 DRAWING-CONFIRMED from rim +0.30 - 1.20 - 0.40 - 0.05 - 0.05 - 0.10)
    pg = pool_geometry()
    groups["PIT:POOL"] = {"formation": {"value": -1.50, "status": X.DRAWING_CONFIRMED}, "kind": "PIT"}
    comps.append({"id": "POOL:ENVELOPE", "group": "PIT:POOL", "kind": "POOL_ENVELOPE", "plan": pg["A10"],
                  "z": [{"form": 0.0}, {"abs": 0.30}], "source": "T-183 r2 (p.7 layers, NW cut levels)",
                  "info": "shell + screed + membrane + blinding (at the membrane line) + water space and floor "
                          "build-up (VOID, not soil); decomposition in summary.json 'pool_decomposition'"})
    comps += [
        {"id": "POOL:BLINDING_BEYOND_MEMBRANE", "group": "PIT:POOL", "kind": "BLINDING", "status": X.HELD,
         "held": ["BLINDING_PROJECTION_NOT_PRINTED (T-183 B, '>= 1.222')"], "source": "T-183"},
    ]
    f8 = f8_in_pool()
    g8 = pit_of_outline["1B24"]
    for k, plan in (("BLINDING", f8["neat_in_env_m2"]), ("UNDERLAY", f8["footprint_in_env_m2"]),
                    ("FOOTING", f8["footprint_in_env_m2"])):
        shared.append({"a": f"{g8}:{k}", "b": "POOL:ENVELOPE", "plan": plan, "status": X.CONFLICT,
                       "why": "F8 drawn under the pool (T-183 interface 1, T-189 UNDETERMINED): at the printed "
                              "limit F8's chain (-1.50 .. -0.83) and the pool base (-1.30 .. -0.90) occupy the "
                              "same space; counted once only when the designer prints F8's founding level"})
    # the upper boundary G.B ends on the pool wall's outer face (7FE#3 2.25 m, 7FC#1 1.15 m, T-253) while p.7 runs
    # screed + membrane 0.10 outside that face: 0.20 x 0.10 per end lies in both unless one stops at the other
    for c in comps:
        if c["id"].startswith("GB:BOUNDARY-UPPER") and any(abs(c["plan"] / 0.20 - L) < 1e-9 for L in (2.25, 1.15)):
            shared.append({"a": c["id"], "b": "POOL:ENVELOPE", "plan": 0.20 * 0.10, "status": X.HELD,
                           "why": "band end on the pool wall vs the p.7 layers outside the wall: which stops at "
                                  "which is not printed"})
    shared.append({"a": "BOUNDARY:LOWER_BAND", "b": "POOL:ENVELOPE", "plan": 0.20 * 3.50, "status": X.HELD,
                   "why": "lower boundary band (S-BOUN 0.20 x 0.60, level not printed) drawn in the back-wall strip "
                          "(T-189: 0 .. 0.280 with the base, 0 .. 0.840 with the walls); part of the Q-28 hold"})
    return {"unit": "m", "eg": eg, "groups": groups, "components": comps, "shared": shared}, {
        "beyond_plot_m2": beyond_plot, "pool": pg, "f8_pool": f8}


def run():
    sp, aux = spec()
    led = X.build(sp)
    comp = {c["id"]: c for c in led["components"]}
    # D-14: the blinding projection beyond the plot line moves from DRAWING-CONFIRMED to HELD (designer item)
    d14 = sum(aux["beyond_plot_m2"].values()) * 0.10
    # pool back face on the boundary-wall line (T-183): the 0.10 of p.7 layers outside it (strip 3.50 x 0.10 + the two
    # rounded back corners) lies beyond the plot line or in the boundary foundation: HELD like D-14, by name
    pool_beyond = (3.50 * 0.10 + 2 * math.pi * 0.10 ** 2 / 4) * 1.50
    tot = X.totals(led)
    kinds = {}
    for c in led["components"]:
        k = kinds.setdefault(c["kind"], {"value_m3": 0.0, "n": 0, "held": 0})
        k["n"] += 1
        if c["value_m3"] is not None:
            k["value_m3"] += c["value_m3"]
        else:
            k["held"] += 1
    netted = {}
    for x in led["shared"]:
        if x["status"] == "NETTED":
            kind = comp[x["a"]]["kind"]
            netted[kind] = netted.get(kind, 0.0) + x["value_m3"]
    pits24 = {k: kinds[k]["value_m3"] - netted.get(k, 0.0) for k in ("BLINDING", "UNDERLAY", "FOOTING")}
    pit_blind = sum(c["value_m3"] for c in led["components"]
                    if c["kind"] == "BLINDING" and c["group"].startswith("PIT:FTG") and c["value_m3"] is not None)
    pits24["BLINDING"] = pit_blind - netted.get("BLINDING", 0.0)
    pit_ftg = sum(c["value_m3"] for c in led["components"] if c["kind"] == "FOOTING" and c["value_m3"] is not None)
    pit_und = sum(c["value_m3"] for c in led["components"] if c["kind"] == "UNDERLAY" and c["value_m3"] is not None)
    pits24["FOOTING"], pits24["UNDERLAY"] = pit_ftg - netted.get("FOOTING", 0), pit_und - netted.get("UNDERLAY", 0)
    pg = aux["pool"]
    deco = {"base": pg["A0"] * 0.40, "walls_below_EG": pg["band"] * 0.90, "water_space_below_EG": pg["Aw"] * 0.85,
            "floor_buildup": pg["Aw"] * 0.05, "screed_under_base": pg["A05"] * 0.05,
            "screed_up_walls_below_EG": (pg["A05"] - pg["A0"]) * 1.30, "membrane_under": pg["A10"] * 0.05,
            "membrane_up_walls_below_EG": (pg["A10"] - pg["A05"]) * 1.35, "blinding_at_membrane_line": pg["A10"] * 0.10}
    necks = [c for c in led["components"] if c["kind"] == "NECK"]
    res = {
        "method": X.METHOD_ID, "eg_m": led["eg_m"], "formation_limit_m": LIMIT,
        "components": len(led["components"]), "totals": tot,
        "pits24_net_m3": {k: round(v, 6) for k, v in pits24.items()},
        "t170_reference_net_m3": {"BLINDING": 12.9234, "UNDERLAY": 7.6895, "FOOTING": 52.919},
        "d14_beyond_plot_m3": round(d14, 6), "pits24_blinding_inside_plot_m3": round(pits24["BLINDING"] - d14, 6),
        "t233_closure": {"footing_line_m3": 64.304, "ours_24_plus_FF": round(pits24["FOOTING"] + 11.385, 6),
                         "blinding_line_m3": 14.990438,
                         "ours_24_inside_plot_plus_FF": round(pits24["BLINDING"] - d14 + 2.256, 6)},
        "necks": {"n": len(necks), "bounded": sum(1 for c in necks if c["value_m3"] is not None),
                  "at_least_m3": round(sum(c["value_m3"] for c in necks if c["value_m3"] is not None), 6),
                  "coef_m3_per_m": round(sum(c["coef_m3_per_m"] or 0 for c in necks), 6),
                  "conflict_or_held": sorted((c["id"], c["status"]) for c in necks if c["value_m3"] is None)},
        "pool_decomposition": {k: round(v, 6) for k, v in deco.items()},
        "pool_envelope_m3": comp["POOL:ENVELOPE"]["value_m3"],
        "pool_rc_check_m3": {"base": round(deco["base"], 6), "walls_full_1_20": round(pg["band"] * 1.20, 6),
                             "walls_above_EG_excluded": round(pg["band"] * 0.30, 6)},
        "f8_pool": {k: round(v, 6) for k, v in aux["f8_pool"].items()},
        "by_kind": {k: {"value_m3": round(v["value_m3"], 6), "n": v["n"], "held": v["held"]} for k, v in kinds.items()},
        "shared": [{k: x[k] for k in ("a", "b", "plan_m2", "value_m3", "range_m3", "status")} for x in led["shared"]],
        "groups": {g: {"value_m3": v["value_m3"], "held": len(v["held"]), "statuses": v["statuses"],
                       "beyond_plot_held_m3": round(aux["beyond_plot_m2"].get(g, 0.0) * 0.10, 6),
                       "value_inside_plot_m3": round(v["value_m3"] - aux["beyond_plot_m2"].get(g, 0.0) * 0.10, 6)}
                   for g, v in X.by_group(led).items()},
    }
    est = tot["established_m3"] - d14 - pool_beyond
    res["pool_layers_beyond_plot_line_m3"] = round(pool_beyond, 6)
    pgp = res["groups"]["PIT:POOL"]
    pgp["beyond_plot_held_m3"] = round(pool_beyond, 6)
    pgp["value_inside_plot_m3"] = round(pgp["value_m3"] - pool_beyond, 6)
    res["z1_by_family_m3"] = {
        "pit blinding (24, inside the plot)": round(pits24["BLINDING"] - d14, 6),
        "pit underlay (24)": round(pits24["UNDERLAY"], 6), "footings (24)": round(pits24["FOOTING"], 6),
        "necks below EG (29, AT_LEAST at d = 0)": res["necks"]["at_least_m3"],
        "straps outside the footings (3)": 3.3905,
        "main-house exterior ground-beam blinding (17 runs)": round(sum(
            c["value_m3"] for c in led["components"] if c["id"].startswith("GB:EXT-MAIN") and
            c["kind"] == "BLINDING"), 6),
        "upper boundary G.B at N.G. (5 runs)": round(sum(
            c["value_m3"] for c in led["components"] if c["id"].startswith("GB:BOUNDARY-UPPER")), 6),
        "pool envelope inside the plot (shell + layers + water space)": round(
            comp["POOL:ENVELOPE"]["value_m3"] - pool_beyond, 6)}
    res["z1_by_family_sum_m3"] = round(sum(res["z1_by_family_m3"].values()), 6)
    res["z1_established_m3"] = round(est, 6)
    res["excavated"] = {"status": X.HELD, "value_m3": None,
                        "held": ["formation only a limit (Q-21 C / OQ-13)", "working space not printed (UP-EXC-001)",
                                 "pits vs bulk dig over the east block (OQ-13, T-170 w*)"],
                        "coefficient_24_neat_pits_m3_per_m": 129.234}
    res["backfill"] = X.backfill(None, est)
    res["disposal"] = X.disposal(None, None)
    return res, led


def write(res, led):
    rows = []
    for c in led["components"]:
        rows.append({"id": c["id"], "group": c["group"], "kind": c["kind"], "plan_m2": c["plan_m2"],
                     "value_m3": c["value_m3"], "coef_m3_per_m": c["coef_m3_per_m"],
                     "range_m3": "" if c["range_m3"] is None else "%s..%s" % tuple(c["range_m3"]),
                     "status": c["status"], "held": "; ".join(c["held"]), "source": c["source"],
                     "above_EG_excluded_m3": c.get("above_ground_m3_excluded", ""), "info": c.get("info", "")})
    with open(HERE / "LEDGER_T320.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (HERE / "summary.json").write_text(json.dumps(res, indent=1, sort_keys=True, default=list) + "\n")


if __name__ == "__main__":
    r, l = run()
    write(r, l)
    print(json.dumps({k: r[k] for k in ("by_kind", "pits24_net_m3", "d14_beyond_plot_m3", "t233_closure", "necks",
                                        "pool_envelope_m3", "f8_pool", "z1_established_m3", "totals")}, indent=1,
                     default=list))
