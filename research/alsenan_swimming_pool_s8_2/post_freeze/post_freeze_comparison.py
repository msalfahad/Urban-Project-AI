"""S8.2 POST-FREEZE COMPARISON (comparison layer; never upstream of a quantity).

    python3 -I research/alsenan_swimming_pool_s8_2/post_freeze/post_freeze_comparison.py

This script refuses to run until three checks pass:
  * 18_S8_2_FREEZE_MANIFEST.json still matches every frozen code, input, drawing and output file;
  * it is the manifest committed at the S8.2 freeze commit;
  * that commit holds no post_freeze file.
Only then does it open the earlier pool figures:
  * old Urban V3b (STRUCTURE_V3B_REGISTER pool row, REBAR_POPULATION_REGISTER pool sets, TECHNICAL_QTO pool lines and
    the raster claim behind its 1.15 m depth);
  * old Urban R4 (REBAR_POPULATION_REGISTER_V4 POP:POOL:SWIM, provisional);
  * the multi-engine tables (freelancer QS, christiannp, U-C4N; the 121 kg/m3 rough ratio, SANITY_CHECK_ONLY);
  * the freelancer's own pool sheet rows (FREELANCER_CATEGORY_LINEAGE).
S8.2 released 0 m3 and 0 kg, so every reference figure is a difference. Each one is split into the classes in CLASSES,
using only the frozen S8.2 geometry and the reference's own inputs, and the classes close exactly on the difference.
A figure that combines S8.2 geometry with a reference depth is a comparison figure only: it is never written to the
S8.2 package and never released. Nothing is tuned. A correction found here needs a new issue, new source evidence, a
new regression and a new version.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parents[1]

FREEZE_COMMIT = "ae6393b"
MANIFEST = PKG / "18_S8_2_FREEZE_MANIFEST.json"
PKG_REL = "research/alsenan_swimming_pool_s8_2"
DRAWINGS = {"ST7757.dxf": "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf",
            "P7757.dxf": "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf",
            "ST7757.pdf": "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3.pdf"}
CLASSES = ("GEOMETRY", "SOURCE_NOT_IN_S8_2", "DEPTH_ASSUMPTION", "SCOPE", "NOTATION_SCOPE", "COUNT_CONVENTION",
           "BAR_LENGTH", "REFERENCE_FORMULA_MISMATCH", "BLOCKED_IN_S8_2", "UNSEPARATED", "SANITY_RATIO",
           "REFERENCE_ROUNDING", "UNKNOWN")
V3B_STRUCT = ROOT / "tests/alsenan/registers_v3b/STRUCTURE_V3B_REGISTER.json"
V3B_REBAR = ROOT / "tests/alsenan/registers_v3b/REBAR_POPULATION_REGISTER.json"
V3B_QTO = ROOT / "tests/alsenan/registers_v3b/TECHNICAL_QTO_REGISTER.json"
V3B_RASTER = ROOT / "tests/alsenan/registers_v3b/RASTER_EVIDENCE_REGISTER.json"
R4 = ROOT / "research/alsenan_rebar_source_exhaustion_04/registers/REBAR_POPULATION_REGISTER_V4.json"
CONCRETE = ROOT / "research/alsenan_multi_engine_comparison/MULTI_ENGINE_CONCRETE_COMPARISON.json"
REBAR_ME = ROOT / "research/alsenan_multi_engine_comparison/MULTI_ENGINE_REBAR_COMPARISON.json"
LINEAGE = ROOT / "research/alsenan_multi_engine_comparison/FREELANCER_CATEGORY_LINEAGE.json"
OUT = {"md": "S8_2_POST_FREEZE_COMPARISON.md", "totals": "S8_2_POST_FREEZE_REFERENCE_TOTALS.csv",
       "causes": "S8_2_POST_FREEZE_DIFFERENCE_CAUSES.csv", "equal": "S8_2_POST_FREEZE_EQUAL_SCOPE.csv",
       "findings": "S8_2_POST_FREEZE_FINDINGS.csv", "summary": "S8_2_POST_FREEZE_SUMMARY.json"}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def _objs(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _objs(v)
    elif isinstance(o, list):
        for v in o:
            yield from _objs(v)


# ------------------------------------------------------------------ freeze first
def verify_freeze():
    m = _j(MANIFEST)
    bad = [k for g, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG)) for k, h in m[g].items()
           if _sha(base / k) != h]
    bad += [k for k, h in m["drawing_sha256"].items() if _sha(ROOT / "data/inputs/by_sha256" / DRAWINGS[k]) != h]
    if bad or m["state"] != "FROZEN_BEFORE_COMPARISON" or m["references_read"]:
        raise SystemExit(f"S8.2 freeze broken - refusing to compare: {bad}")
    full = _git("rev-parse", FREEZE_COMMIT).strip()
    at_freeze = subprocess.run(["git", "show", f"{full}:{PKG_REL}/18_S8_2_FREEZE_MANIFEST.json"], cwd=ROOT,
                               check=True, capture_output=True).stdout
    tree = _git("ls-tree", "-r", "--name-only", full, f"{PKG_REL}/").split()
    if hashlib.sha256(at_freeze).hexdigest() != _sha(MANIFEST) or any("post_freeze" in t for t in tree):
        raise SystemExit("S8.2 freeze commit does not hold this manifest, or already holds a post-freeze file")
    for o in list(m["outputs"]) + ["18_S8_2_FREEZE_MANIFEST.json"]:
        if f"{PKG_REL}/{o}" not in tree:
            raise SystemExit(f"S8.2 output {o} was not committed at the freeze")
    return m, full


# ------------------------------------------------------------------ frozen S8.2
def s8_2():
    s = _j(PKG / "17_S8_2_SUMMARY.json")
    fams = _rows(PKG / "04_BASE_REINFORCEMENT_QTO.csv") + _rows(PKG / "05_WALL_REINFORCEMENT_QTO.csv")
    if s["concrete"]["released_m3"] != 0.0 or s["reinforcement"]["released_kg"] != 0.0:
        raise SystemExit("this comparison is written for a round that released nothing")
    return {"footprint_m2": s["plan_m2"]["structural_footprint"], "water_m2": s["plan_m2"]["water"],
            "band_m2": s["plan_m2"]["wall_band"], "L_out_m": s["perimeter_m"]["outer"],
            "L_in_m": s["perimeter_m"]["water"], "released_m3": 0.0, "released_kg": 0.0,
            "families": {f["FAMILY_ID"]: f for f in fams}, "lanes": s["reinforcement"]["lanes"],
            "summary": s}


# ------------------------------------------------------------------ decomposition helpers
def closed(name, ref_value, s82_value, classes):
    """classes {class: qty}; a REFERENCE_ROUNDING remainder closes the row; it must stay below 1e-6."""
    diff = ref_value - s82_value
    rest = diff - math.fsum(classes.values())
    if abs(rest) > 1e-6:
        raise SystemExit(f"{name}: classes leave {rest} unexplained")
    out = {k: v for k, v in classes.items() if abs(v) > 0}
    if abs(rest) > 1e-9:                                   # below this it is float noise, not reference rounding
        out["REFERENCE_ROUNDING"] = out.get("REFERENCE_ROUNDING", 0.0) + rest
    unknown = set(out) - set(CLASSES)
    if unknown:
        raise SystemExit(f"{name}: unknown classes {unknown}")
    return diff, out


def um(d):
    return d * d / 162.0


# ------------------------------------------------------------------ references
def v3b():
    st = next(o for o in _objs(_j(V3B_STRUCT)) if o.get("swim_block") == "147")
    sets = [o for o in _objs(_j(V3B_REBAR)) if o.get("population") == "POOL" and "element" in o]
    pop = next(o for o in _objs(_j(V3B_REBAR)) if o.get("population") == "POOL" and "sets" in o)
    qto = {o["code"]: o for o in _objs(_j(V3B_QTO)) if str(o.get("code", "")).startswith(("C-POOL", "R-POOL", "T-POOL"))}
    raster = next(o for o in _objs(_j(V3B_RASTER)) if o.get("quantity") == "SUNKEN_ELEMENT_DEPTH")
    return st, sets, pop, qto, raster


def r4():
    d = _j(R4)
    pop = next(o for o in _objs(d) if o.get("pop_id") == "POP:POOL:SWIM")
    comps = [o for o in _objs(d) if o.get("population_id") == "POP:POOL:SWIM" and "comp_id" in o]
    return pop, comps


def multi_engine():
    conc = next(o for o in _objs(_j(CONCRETE)) if o.get("category") == "POOL" and "FREELANCER_QS" in o)
    rb = next(o for o in _objs(_j(REBAR_ME)) if o.get("category") == "SWIMMING_POOL" and "freelancer_steel_t" in o)
    return conc, rb


def freelancer_rows():
    d = _j(LINEAGE)
    leaves = [o for o in _objs(d) if o.get("kind") == "LEAF_ROW" and str(o.get("physical_kind", "")).startswith("POOL")]
    cat = next(o for o in _objs(d) if o.get("category_id") == "SWIMMING_POOL" and "steel_value_t" in o)
    return leaves, cat


# ------------------------------------------------------------------ main
def main():
    m, freeze = verify_freeze()
    s = s8_2()
    st, v3_sets, v3_pop, v3_qto, raster = v3b()
    r4_pop, r4_comps = r4()
    me_conc, me_rb = multi_engine()
    fl_leaves, fl_cat = freelancer_rows()

    A, band, Lout = s["footprint_m2"], s["band_m2"], s["L_out_m"]
    D = st["depth_m"]                                       # the old V3b depth: a raster claim, not an S8.2 source
    totals, causes, equal = [], [], []

    def add(ref, quantity, component, ref_value, origin, classes, note):
        diff, cl = closed(f"{ref}:{component}", ref_value, 0.0, classes)
        totals.append({"REFERENCE": ref, "QUANTITY": quantity, "COMPONENT": component, "REFERENCE_VALUE": ref_value,
                       "S8_2_RELEASED": 0.0, "S8_2_STATE": "BLOCKED (nothing released; total unknown, not 0)",
                       "DIFFERENCE": diff, "REFERENCE_ORIGIN": origin, "NOTE": note})
        for k, v in sorted(cl.items()):
            causes.append({"REFERENCE": ref, "QUANTITY": quantity, "COMPONENT": component, "CLASS": k, "QTY": v})

    # ---- old Urban V3b concrete: base 3.50 x 1.95 x 0.40 + walls 10.10 x 0.20 x 1.15
    base_ref, walls_ref = st["base_m3"], st["walls_m3"]
    v3_base_area, v3_wall_len = 3.50 * 1.95, 10.10
    add("OLD_URBAN_V3B", "CONCRETE_M3", "POOL_BASE", base_ref, "OLD_V3B_CALCULATED (plan rectangle 3.50 x 1.95)",
        {"GEOMETRY": (v3_base_area - A) * st["base_t_m"], "BLOCKED_IN_S8_2": A * st["base_t_m"]},
        "V3b's 3.50 x 1.95 rectangle omits the semicircular west end (S8.2 exact D-shape footprint); the remainder is "
        "footprint x 0.40, which S8.2 holds blocked: the 40 cm is dimensioned on the deep base only and the zone "
        "extents are not printed")
    add("OLD_URBAN_V3B", "CONCRETE_M3", "POOL_WALLS", walls_ref, "OLD_V3B_CALCULATED (perimeter 10.10 x 0.20 x depth)",
        {"GEOMETRY": (v3_wall_len * st["wall_t_m"] - band) * D, "SOURCE_NOT_IN_S8_2": band * D},
        f"V3b's 10.10 m x 0.20 wall against the exact {band:.6f} m2 band; its {D} m height comes from the raster claim "
        f"'{raster['evidence']}' on {raster['sheet_ref']} (architectural PDF sha {raster['sheet_sha256'][:8]}...), bound "
        f"only as '{raster['binds']}'. That PDF is not in the S8.2 source set")
    blind_ref = st["blinding_m3"]
    add("OLD_URBAN_V3B", "PLAIN_CONCRETE_M3", "POOL_BLINDING", blind_ref, "OLD_V3B_CALCULATED ((1.95 + 0.20) x (3.50 + 0.20) x 0.10)",
        {"GEOMETRY": ((1.95 + 0.20) * (3.50 + 0.20) - A) * 0.10, "BLOCKED_IN_S8_2": A * 0.10},
        "the remainder is footprint x 0.10 (S8.2 SEN-08 lower bound); the drawn projection past the walls is not "
        "dimensioned, so S8.2 releases none of it")
    wp = st["external_wp_m2"]
    add("OLD_URBAN_V3B", "WATERPROOFING_M2", "POOL_EXTERNAL_MEMBRANE", wp,
        "OLD_V3B_CALCULATED (outer base + outer walls x (D + base))",
        {"GEOMETRY": wp - (A + Lout * (D + st["base_t_m"])), "SOURCE_NOT_IN_S8_2": Lout * (D + st["base_t_m"]),
         "BLOCKED_IN_S8_2": A},
        "S8.2 keeps '5cm INSULATION MEMBRANE.' as printed, product not established; the wall faces need the depth")
    fin = st["internal_finish_m2"]
    add("OLD_URBAN_V3B", "FINISH_M2", "POOL_INTERNAL_FINISH", fin, "OLD_V3B_CALCULATED (inner base + inner walls x D)",
        {"SCOPE": fin}, "internal tile / mosaic is a finish, outside the S8.2 structural QTO")

    # ---- old Urban V3b reinforcement: five sets, deep-end callouts applied to the whole pool
    # unrounded equivalent count = rate x the reference's own width (perimeter 10.10, depth 1.15, 3.50 / 1.95, both
    # faces / both layers); the reference count above it is its count convention
    width = {"vertical 7Ø14/m outer": (7.0, 10.10, 1), "vertical 7Ø12/m inner": (7.0, 10.10, 1),
             "horizontal Ø12/20 both faces": (5.0, D, 2), "base 7Ø14/m top+bottom long": (7.0, 1.95, 2),
             "base 7Ø14/m top+bottom short": (7.0, 3.50, 2)}
    for z in v3_sets:
        rate, w, layers = width[z["ref"]]
        eq = rate * w * layers
        kg = z["net_kg"]
        conv = (z["count"] - eq) * z["bar_m"] * um(z["dia_mm"])
        first = "SOURCE_NOT_IN_S8_2" if z["element"] == "POOL_WALL" else "NOTATION_SCOPE"
        add("OLD_URBAN_V3B", "REBAR_KG", z["ref"], kg, "OLD_V3B_CALCULATED (DETAIL OF SWIMMING POOL, deep-end values)",
            {"COUNT_CONVENTION": conv, first: kg - conv},
            f"{z['count']} bars x {z['bar_m']} m; unrounded rate x width = {eq:g}. "
            + ("Wall bars need the wall height (V3b: 1.15 m raster claim) and are bound in S8.2 to the deep end wall "
               "section only (shallow wall 6Ø12/m, Ø10/20; side walls not shown: Q-S8.2-06)"
               if z["element"] == "POOL_WALL" else
               "S8.2 binds 7Ø14/m to the deep base only (6Ø14/m transverse, slope and shallow 6Ø12/m; extents "
               "'AS PER ARCH'); V3b spread it over a 3.50 x 1.95 rectangle that is not the plan shape"))
    # ---- old Urban R4 (provisional): the same five sets; its kg do not equal its own printed formulas
    for c in r4_comps:
        n = int(c["formula"].split(" x ")[0])
        by_formula = n * c["provisional_length_m"] * um(c["dia_mm"])
        first = "SOURCE_NOT_IN_S8_2" if c["bar_role"].startswith("WALL") else "NOTATION_SCOPE"
        add("OLD_URBAN_R4", "REBAR_KG", c["bar_role"], c["provisional_kg"], "OLD_R4_PROVISIONAL (AI mapping of the N.I.S detail)",
            {first: by_formula, "REFERENCE_FORMULA_MISMATCH": c["provisional_kg"] - by_formula},
            f"printed formula '{c['formula']}' = {by_formula:.6f} kg; the row carries {c['provisional_kg']} kg")
    # ---- freelancer QS: its own pool sheet rows
    for z in fl_leaves:
        v, lab = z["value"], z["label"]
        if z["physical_kind"] == "POOL" and lab == "الأرضية":                        # pool floor 10.8 x 0.4
            cl = {"GEOMETRY": (z["B"] - A) * z["D"], "BLOCKED_IN_S8_2": A * z["D"]}
            note = f"floor {z['B']} m2 x {z['D']} against the exact {A:.6f} m2 footprint x 0.40"
        elif z["physical_kind"] == "POOL" and lab == "حوائط حمام السباحة":           # pool walls 12 x 1.8 x 0.2
            cl = {"GEOMETRY": (z["B"] * z["D"] - band) * z["C"], "DEPTH_ASSUMPTION": band * z["C"]}
            note = (f"walls {z['B']} m x {z['D']} at {z['C']} m high: no source for 1.8 m is identified (V3b used 1.15); "
                    "S8.2 holds the wall height 'AS PER ARCH'")
        else:                                                                         # pump walls, room floor, steps
            cl = {"SCOPE": v}
            note = {"POOL_PUMP_WALL": "pump-room walls: no pump room on any sheet S8.2 read (PL-PUMP-ROOM)",
                    "POOL_ROOM_FLOOR": "pump-room floor: not shown in the S8.2 sources (PL-PUMP-ROOM)"}.get(
                z["physical_kind"], "pool steps: no step in the S8.2 section or plan (PL-STEPS); the V3b raster note "
                                    "mentions a '70 step' on the architectural elevation")
        add("FREELANCER_QS", "CONCRETE_M3", f"{z['cell']} {lab}", v, f"DONOR_FORMULA {z['formula']}", cl, note)
    add("FREELANCER_QS", "REBAR_KG", "pool + pump room (one figure)", fl_cat["steel_value_t"] * 1000.0,
        "DONOR_HARDCODED (steel cell, not a formula)", {"UNSEPARATED": fl_cat["steel_value_t"] * 1000.0},
        "one figure for pool and pump room, no bar breakdown")
    add("ROUGH_RATIO", "REBAR_KG", f"{me_rb['rough_ratio_kg_per_m3']} kg per m3 x V3b concrete",
        me_rb["rough_reference_kg_modelled"], "SANITY_CHECK_ONLY (never promoted)",
        {"SANITY_RATIO": me_rb["rough_reference_kg_modelled"]}, "a ratio is never a quantity in S8.2")
    no_ref = [{"REFERENCE": k, "QUANTITY": q, "VALUE": None} for k, q in (("CHRISTIANNP", "CONCRETE_M3"),
                                                                          ("U-C4N", "CONCRETE_M3"))
              if me_conc.get("CHRISTIANNP" if k == "CHRISTIANNP" else "UC4N") is None]

    # ---- consistency of the reference totals with their parts
    v3_conc = math.fsum(t["REFERENCE_VALUE"] for t in totals if t["REFERENCE"] == "OLD_URBAN_V3B" and t["QUANTITY"] == "CONCRETE_M3")
    v3_kg = math.fsum(t["REFERENCE_VALUE"] for t in totals if t["REFERENCE"] == "OLD_URBAN_V3B" and t["QUANTITY"] == "REBAR_KG")
    r4_kg = math.fsum(t["REFERENCE_VALUE"] for t in totals if t["REFERENCE"] == "OLD_URBAN_R4")
    fl_conc = math.fsum(t["REFERENCE_VALUE"] for t in totals if t["REFERENCE"] == "FREELANCER_QS" and t["QUANTITY"] == "CONCRETE_M3")
    checks = {"v3b_concrete_parts_vs_line": [v3_conc, v3_qto["C-POOL"]["qty"], abs(v3_conc - v3_qto["C-POOL"]["qty"]) < 1e-3],
              "v3b_rebar_sets_vs_line": [v3_kg, v3_pop["net_kg"], abs(v3_kg - v3_pop["net_kg"]) < 1e-3],
              "r4_components_vs_population": [r4_kg, r4_pop["provisional_kg"], abs(r4_kg - r4_pop["provisional_kg"]) < 1e-3],
              "freelancer_rows_vs_summary": [fl_conc, fl_cat["quantity"], abs(fl_conc - fl_cat["quantity"]) < 1e-3]}
    if not all(v[2] for v in checks.values()):
        raise SystemExit(f"a reference total does not equal its parts: {checks}")

    # ---- equal scope: what S8.2 establishes for the same physical item
    equal += [
        {"ITEM": "pool base footprint", "S8_2": f"{A:.6f} m2 (exact D-shape, CAD_GEOMETRY + stated 350)",
         "OLD_URBAN_V3B": f"{v3_base_area:.4f} m2 (3.50 x 1.95)", "FREELANCER_QS": "10.8 m2",
         "STATE": "S8.2 ESTABLISHED; references differ by geometry"},
        {"ITEM": "wall plan band", "S8_2": f"{band:.6f} m2 (exact; centre-line {band / 0.2:.6f} m)",
         "OLD_URBAN_V3B": "10.10 m x 0.20", "FREELANCER_QS": "12 m x 0.20", "STATE": "S8.2 ESTABLISHED"},
        {"ITEM": "wall height / depth", "S8_2": "NOT_ESTABLISHED ('AS PER ARCH')", "OLD_URBAN_V3B": f"{D} m (raster claim, "
         "POOL CANDIDATE binding)", "FREELANCER_QS": "1.8 m (no source)", "STATE": "BLOCKED in S8.2; references disagree"},
        {"ITEM": "base thickness scope", "S8_2": "40 cm on the deep base only; slope and shallow not dimensioned",
         "OLD_URBAN_V3B": "0.40 everywhere", "FREELANCER_QS": "0.40 everywhere", "STATE": "BLOCKED in S8.2"},
        {"ITEM": "base reinforcement notation", "S8_2": "deep 7Ø14/m (+6Ø14/m transverse), slope 6Ø12/m, shallow 6Ø12/m",
         "OLD_URBAN_V3B": "7Ø14/m top and bottom both ways everywhere", "FREELANCER_QS": "unseparated",
         "STATE": "NOTATION_SCOPE"},
        {"ITEM": "pump room, steps", "S8_2": "NOT_SHOWN_IN_SOURCE", "OLD_URBAN_V3B": "none",
         "FREELANCER_QS": "pump walls 1.08, room floor 2.4, steps 0.228 m3", "STATE": "SCOPE"},
        {"ITEM": "released quantity", "S8_2": "0 m3, 0 kg (totals unknown)", "OLD_URBAN_V3B": "5.053 m3, 585.738 kg",
         "FREELANCER_QS": "12.348 m3, 1.5 t", "STATE": "no equal-scope released quantity exists"}]
    findings = [
        ("F-S8.2-PF-01", "SOURCE_NOT_IN_S8_2", "Old V3b's 1.15 m depth is a raster reading '" + raster["evidence"] +
         f"' on {raster['sheet_ref']} of the architectural PDF (sha {raster['sheet_sha256']}), bound only as a pool "
         "candidate. S8.2 read the architectural DXF (P7757.dxf) but not the architectural PDF elevations. Next round: "
         "restore that PDF, verify the 115 / 70 annotations bind to the pool (vector text, not raster), then release "
         "depth-dependent quantities only if they do.", "OPEN (new source evidence needed; S8.2 unchanged)"),
        ("F-S8.2-PF-02", "GEOMETRY", "Old V3b measured the base as a 3.50 x 1.95 rectangle (6.825 m2) and the blinding "
         "as 2.15 x 3.70; the plan outline is a D-shape of 10.935564 m2. The old figures under-measure the plan by "
         f"{A - v3_base_area:.6f} m2.", "RECORDED (S8.2 geometry stands)"),
        ("F-S8.2-PF-03", "NOTATION_SCOPE", "Old V3b and R4 applied the deep-end callouts to the whole pool; S8.2 binds "
         "each of the 26 labels to its own run or dot row (shallow and slope zones carry 6Ø12/m and 6Ø14/m; the "
         "shallow wall Ø10/20cm).", "RECORDED"),
        ("F-S8.2-PF-04", "REFERENCE_FORMULA_MISMATCH", "R4's pool components carry kg that do not equal their own printed "
         "formulas (e.g. '28 x 3.500 m x 14^2/162' = 118.567901 kg, row 127.037037 kg).", "RECORDED (reference defect)"),
        ("F-S8.2-PF-05", "SCOPE", "The freelancer adds pump-room walls (1.08 m3), a room floor (2.4 m3) and pool steps "
         "(0.228 m3). S8.2 found no pump room or steps on any sheet it read; the V3b raster note's '70 step' points at the "
         "same unread architectural elevation.", "OPEN (with F-S8.2-PF-01)"),
        ("F-S8.2-PF-06", "DEPTH_ASSUMPTION", "The references disagree on the wall height (V3b 1.15 m, freelancer 1.8 m); "
         "neither is a stated dimension in the S8.2 sources.", "RECORDED"),
        ("F-S8.2-PF-07", "NO_REFERENCE_QUANTITY", "christiannp and U-C4N carry no pool figure.", "RECORDED")]

    # ---- outputs (post_freeze/ only; the S8.2 package is never written)
    def csv_out(name, rows, fields):
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{r[k]:.9f}".rstrip("0").rstrip(".") if isinstance(r[k], float) else r[k]) for k in fields})
        (HERE / name).write_text(buf.getvalue(), encoding="utf-8")
    csv_out(OUT["totals"], totals, list(totals[0]))
    csv_out(OUT["causes"], causes, list(causes[0]))
    csv_out(OUT["equal"], equal, list(equal[0]))
    csv_out(OUT["findings"], [dict(zip(("FINDING_ID", "CLASS", "TEXT", "STATUS"), f)) for f in findings],
            ["FINDING_ID", "CLASS", "TEXT", "STATUS"])
    by_class = {}
    for c in causes:
        key = f"{c['REFERENCE']}|{c['QUANTITY']}|{c['CLASS']}"
        by_class[key] = by_class.get(key, 0.0) + c["QTY"]
    ref_tot = {}
    for t in totals:
        key = f"{t['REFERENCE']}|{t['QUANTITY']}"
        ref_tot[key] = ref_tot.get(key, 0.0) + t["REFERENCE_VALUE"]
    summary = {"round": "S8_2_POST_FREEZE", "freeze_commit": freeze, "freeze_manifest_sha256": _sha(MANIFEST),
               "freeze_manifest_verified": True, "frozen_engine_stamp": m["engine_commit_stamp"],
               "references_opened": sorted(str(p.relative_to(ROOT)) for p in (V3B_STRUCT, V3B_REBAR, V3B_QTO, V3B_RASTER,
                                                                              R4, CONCRETE, REBAR_ME, LINEAGE)),
               "s8_2": {"released_m3": 0.0, "released_kg": 0.0, "footprint_m2": A, "band_m2": band,
                        "lanes": s["lanes"]},
               "reference_totals": dict(sorted(ref_tot.items())), "difference_by_class": dict(sorted(by_class.items())),
               "reference_consistency": checks, "no_reference_quantity": no_ref, "classes": list(CLASSES),
               "unknown_rows": [c for c in causes if c["CLASS"] == "UNKNOWN"],
               "findings": [f[0] for f in findings], "tuned": False, "s8_2_outputs_written": False,
               "rule": "comparison only: nothing here changes an S8.2 quantity; a correction needs a new issue, new "
                       "source evidence, a new regression and a new version"}
    (HERE / OUT["summary"]).write_text(json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                       encoding="utf-8")
    (HERE / OUT["md"]).write_text(report(summary, totals, findings, equal), encoding="utf-8")
    print(json.dumps({"reference_totals": summary["reference_totals"], "findings": summary["findings"]}, indent=1,
                     ensure_ascii=False))


def report(s, totals, findings, equal):
    L = ["# S8.2 post-freeze comparison", "",
         f"S8.2 was frozen at `{s['freeze_commit'][:7]}`. The manifest was verified before any reference was opened. S8.2 "
         "released 0 m3 and 0 kg, so every reference figure below is a difference. The classes close exactly on it. "
         "Nothing was tuned, and the S8.2 package was not written.", "",
         "## Reference totals", "", "| reference | quantity | value |", "|---|---|---|"]
    L += [f"| {k.split('|')[0]} | {k.split('|')[1]} | {v:.6f} |" for k, v in s["reference_totals"].items()]
    L += ["", "christiannp and U-C4N carry no pool figure.", "", "## Difference by class", "",
          "| reference | quantity | class | qty |", "|---|---|---|---|"]
    L += [f"| {k.split('|')[0]} | {k.split('|')[1]} | {k.split('|')[2]} | {v:.6f} |" for k, v in s["difference_by_class"].items()]
    L += ["", "## Equal scope", "", "| item | S8.2 | old V3b | freelancer | state |", "|---|---|---|---|---|"]
    L += [f"| {e['ITEM']} | {e['S8_2']} | {e['OLD_URBAN_V3B']} | {e['FREELANCER_QS']} | {e['STATE']} |" for e in equal]
    L += ["", "## Findings", ""] + [f"- **{f[0]}** ({f[1]}, {f[3]}): {f[2]}" for f in findings]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
