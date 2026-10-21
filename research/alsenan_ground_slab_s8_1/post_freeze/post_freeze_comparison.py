"""S8.1 POST-FREEZE COMPARISON (comparison layer; never upstream of a quantity).

    python3 -I research/alsenan_ground_slab_s8_1/post_freeze/post_freeze_comparison.py [<CHRISTIANNP_FORENSIC_RERUN dir>]

This script refuses to run until three checks pass:
  * 11_S8_1_FREEZE_MANIFEST.json still matches every frozen code, input, drawing and output file;
  * it is the manifest committed at the S8.1 freeze commit;
  * that commit holds no post_freeze file.
Only then does it open the earlier ground-slab figures. It compares them with the frozen S8.1 slab on equal scope
(the two marker cells) and on each reference's own scope:
  * old Urban CR (coverage recovery round: the cell split of the V3a / V3b zones, lower bound and best);
  * old Urban R3 / R4 (POP:GROUND_SLAB:ZONE-1 / ZONE-2 mesh, area x rate);
  * old Urban V3b (REBAR_POPULATION_REGISTER ground-slab rows; the multi-engine concrete row);
  * christiannp's frozen forensic rerun (09_slabs/GBP vector faces, 13_rebar GROUND_SLAB rows), read-only data;
  * christiannp (original), U-C4N and the freelancer QS (one ground-slab figure each);
  * the rough 130 kg/m3 GROUND_BEAMS_AND_GROUND_SLAB ratio (SANITY_CHECK_ONLY, never promoted).
Each reference cell or face is placed on an S8.1 record by point-in-polygon. Every difference is split into the
classes in CLASSES, and the classes close exactly on the difference. Nothing is tuned: the S8.1 outputs are never
written here. A correction found here needs a new issue, new source evidence, a new regression and a new version.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parents[1]
for _p in (ROOT, ROOT / "research" / "external_engine_lab"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

FREEZE_COMMIT = "201f441"
MANIFEST = PKG / "11_S8_1_FREEZE_MANIFEST.json"
PKG_REL = "research/alsenan_ground_slab_s8_1"
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
SHEET = "GBP"
MARKER_CLASSES = ("MARKER_CELL_GEOMETRY",)
CLASSES = ("MARKER_CELL_GEOMETRY", "ZONE_EXTENT_SCOPE", "OTHER_OWNER_CELL", "POPULATION_GAP", "ZONE_POLYGON_RESIDUAL",
           "COUNT_CONVENTION", "GROSS_AREA_UNSEPARATED", "SCOPE_UNSEPARATED", "REFERENCE_ROUNDING", "SANITY_RATIO",
           "UNKNOWN")
CR_CELLS = ROOT / "research/coverage_recovery_round/GROUND_SLAB_CELL_EXTRACT.json"
CR_DASH = ROOT / "research/coverage_recovery_round/QUANTITY_COVERAGE_DASHBOARD.json"
R4 = ROOT / "research/alsenan_rebar_source_exhaustion_04/registers/REBAR_POPULATION_REGISTER_V4.json"
R3 = ROOT / "research/alsenan_rebar_truth_03/registers/SLAB_REBAR_AUDIT.json"
V3B = ROOT / "tests/alsenan/registers_v3b/REBAR_POPULATION_REGISTER.json"
V3B_STRUCT = ROOT / "tests/alsenan/registers_v3b/STRUCTURE_V3B_REGISTER.json"
CONCRETE = ROOT / "research/alsenan_multi_engine_comparison/MULTI_ENGINE_CONCRETE_COMPARISON.json"
REBAR_ME = ROOT / "research/alsenan_multi_engine_comparison/MULTI_ENGINE_REBAR_COMPARISON.json"
LINEAGE = ROOT / "research/alsenan_multi_engine_comparison/FREELANCER_CATEGORY_LINEAGE.json"
ROUGH = ROOT / "engine/profiles/URBAN_ROUGH_REBAR_PROFILE_V1.json"
SLIVER_EFF_WIDTH_MM = 450.0          # the old V3b zone rule: strips narrower than 450 mm effective width excluded


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _f(v):
    return float(v) if v not in ("", None) else 0.0


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def _rel(p):
    return str(Path(p).relative_to(ROOT))


# ------------------------------------------------------------------ freeze first
def verify_freeze():
    m = _j(MANIFEST)
    bad = [k for g, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG)) for k, h in m[g].items()
           if _sha(base / k) != h]
    bad += [k for k, h in m["drawing_sha256"].items() if _sha(DXF) != h]
    if bad or m["state"] != "FROZEN_BEFORE_COMPARISON" or m["references_read"]:
        raise SystemExit(f"S8.1 freeze broken - refusing to compare: {bad}")
    full = _git("rev-parse", FREEZE_COMMIT).strip()
    at_freeze = subprocess.run(["git", "show", f"{full}:{PKG_REL}/11_S8_1_FREEZE_MANIFEST.json"], cwd=ROOT,
                               check=True, capture_output=True).stdout
    tree = _git("ls-tree", "-r", "--name-only", full, f"{PKG_REL}/").split()
    if hashlib.sha256(at_freeze).hexdigest() != _sha(MANIFEST) or any("post_freeze" in t for t in tree):
        raise SystemExit("S8.1 freeze commit does not hold this manifest, or already holds a post-freeze file")
    for o in list(m["outputs"]) + ["11_S8_1_FREEZE_MANIFEST.json"]:
        if f"{PKG_REL}/{o}" not in tree:
            raise SystemExit(f"S8.1 output {o} was not committed at the freeze")
    return m, full


# ------------------------------------------------------------------ frozen S8.1
def s8_1():
    reg = _rows(PKG / "01_GROUND_SLAB_POPULATION_AND_ZONE_REGISTER.csv")
    conc = {r["PANEL_ID"]: r for r in _rows(PKG / "03_CONCRETE_QTO.csv")}
    xy = _rows(PKG / "04_REINFORCEMENT_XY_QTO.csv")
    summ = _j(PKG / "10_S8_1_SUMMARY.json")
    kg = defaultdict(float)
    for r in xy:
        kg[r["PANEL_ID"]] += _f(r["KG"])
    recs = {}
    for r in reg:
        if not r["POLYGON_MM"]:
            continue
        recs[r["ROW_ID"]] = {"row_kind": r["ROW_KIND"], "state": r["TERMINAL_STATE"], "zone": r["ZONE_ID"],
                             "polygon": json.loads(r["POLYGON_MM"]),
                             "holes": json.loads(r["HOLES_MM"]) if r["HOLES_MM"] else [],
                             "area_m2": _f(r["AREA_M2_EXACT"]),
                             "concrete_m3": _f(conc[r["ROW_ID"]]["VOLUME_M3"]) if r["ROW_ID"] in conc else None,
                             "kg": kg.get(r["ROW_ID"]), "owner": r["PRE_S8_OWNER"]}
    return recs, summ


def record_class(rec):
    """How S8.1 holds the record a reference item lands on."""
    if rec is None:
        return "POPULATION_GAP"
    if rec["zone"]:
        return "MARKER_CELL_GEOMETRY"
    if rec["row_kind"] == "FACE":
        return "ZONE_EXTENT_SCOPE"
    if rec["state"].startswith("OTHER_OWNER"):
        return "OTHER_OWNER_CELL"
    raise SystemExit(f"a reference item lands on {rec['state']}: no class for it")


def locator(recs):
    from shapely.geometry import Point, Polygon
    polys = {k: Polygon(v["polygon"], v["holes"]) for k, v in recs.items()}

    def where(x, y):
        hits = [k for k, p in polys.items() if p.contains(Point(x, y))]
        if len(hits) > 1:
            raise SystemExit(f"point {x, y} lies in two S8.1 records {hits}")
        return hits[0] if hits else None
    return where


def frame_origin():
    import alsenan_structural_s1 as S1M
    return tuple(S1M.Source(DXF).sheets[SHEET]["frame"][:2])


# ------------------------------------------------------------------ decomposition
def area_classes(items, recs, marker_ids):
    """items = [(ref_id, area_m2, s8_1_row_id | None)] -> {class: m2}. The marker-cell class is the reference area in
    the two marker cells minus the S8.1 exact area there (equal scope); every other item takes the class of the S8.1
    record it lands on."""
    out = defaultdict(float)
    for _, a, rid in items:
        out[record_class(recs.get(rid) if rid else None)] += a
    out["MARKER_CELL_GEOMETRY"] -= math.fsum(recs[k]["area_m2"] for k in marker_ids)
    return dict(out)


def scaled(cls_m2, factor):
    return {k: v * factor for k, v in cls_m2.items()}


def close(classes, diff, name):
    got = math.fsum(classes.values())
    if diff is not None and abs(got - diff) > 1e-6:
        raise SystemExit(f"{name}: classes {got} do not close on the difference {diff}")


# ------------------------------------------------------------------ references
def cr_cells(where, fx, fy):
    d = _j(CR_CELLS)
    out = []
    for c in d["cells"]:
        x, y = map(float, c["parent_cell"].split("-C")[1].split("_"))
        out.append({"id": c["cell_id"], "area_m2": c["area_m2"], "part": c["part"], "footprint": c["footprint_id"],
                    "labels": c["labels"], "eff_width_mm": c["eff_width_mm"], "s8_1": where(x - fx, y - fy)})
    return out, d


def v3b_ground_slab_rows():
    def walk(o):
        if isinstance(o, dict):
            yield o
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)
    d = _j(V3B)
    rows = [r for r in walk(d) if r.get("element") == "GROUND_SLAB" and "net_kg" in r and "ref" in r]
    pop = next(r for r in walk(d) if r.get("population") == "GROUND_SLAB" and "sets" in r)
    return rows, pop


def christiannp(cdir, where):
    if not cdir:
        return None
    cdir = Path(cdir)
    faces_p = cdir / "09_slabs" / "GBP" / "GBP_VECTOR_FACES.csv"
    vec_p = cdir / "09_slabs" / "GBP" / "GBP_SLAB_INPUTS_AND_VECTOR.json"
    ev_p = cdir / "13_rebar" / "REBAR_EVIDENCE.csv"
    faces = []
    for r in _rows(faces_p):
        x, y = json.loads(r["INTERIOR_PT"])
        faces.append({"id": r["FACE_ID"], "class": r["CLASS"], "slab_m2": _f(r["SAMPLED_SLAB_M2"]),
                      "net_m2": _f(r["NET_AREA_M2"]), "markers": r["MARKERS"], "s8_1": where(x, y)})
    vec = _j(vec_p)
    gs = [r for r in _rows(ev_p) if r["ELEMENT"] == "GROUND_SLAB"]
    return {"faces": faces, "slab_m2": vec["vector"]["VECTOR_NET_SLAB_SAMPLED_APPORTIONED_M2"],
            "openings_m2": vec["vector"]["VECTOR_OPENINGS_M2"], "gross_m2": vec["vector"]["VECTOR_GROSS_ENCLOSED_M2"],
            "rebar_rows": gs, "kg": math.fsum(_f(r["KG"]) for r in gs if r["INCLUDED_EXCLUDED"].startswith("INCL")),
            "sha256": {"GBP_VECTOR_FACES.csv": _sha(faces_p), "GBP_SLAB_INPUTS_AND_VECTOR.json": _sha(vec_p),
                       "REBAR_EVIDENCE.csv": _sha(ev_p)}}


# ------------------------------------------------------------------ main
def main():
    m, full_commit = verify_freeze()
    recs, summ = s8_1()
    s81_origin = sorted({r["MEASUREMENT_ORIGIN"] for r in _rows(PKG / "03_CONCRETE_QTO.csv")})
    A = summ["included_area_m2"]
    V = summ["concrete_m3"]
    K = summ["total_kg"]
    T_M = 0.100                                         # every reference applies the printed 'T=10cm'
    UM = 10 ** 2 / 162.0
    KG_PER_M2 = 2 * 5 * UM                              # 5Ø10/m each way, both directions, area x rate
    markers = sorted(k for k, r in recs.items() if r["zone"])
    if abs(math.fsum(recs[k]["area_m2"] for k in markers) - A) > 1e-9 or \
            abs(A * KG_PER_M2 - K) > 1e-9 or abs(A * T_M - V) > 1e-9:
        raise SystemExit("frozen S8.1 totals do not reproduce from its own register")
    fx, fy = frame_origin()
    where = locator(recs)
    refs, tot, eq, causes, findings = {}, [], [], [], []

    def add(ref, qty, matching, origin, ref_val, scope, classes, eq_val=None, note=""):
        s_val = V if qty == "CONCRETE_M3" else K
        diff = None if ref_val is None else ref_val - s_val
        classes = {k: v for k, v in classes.items() if abs(v) > 1e-12}
        if diff is not None:
            close(classes, diff, f"{ref} {qty}")
        for c in classes:
            if c not in CLASSES:
                raise SystemExit(f"unknown class {c}")
        tot.append({"REFERENCE": ref, "QUANTITY": qty, "MATCHING": matching, "MEASUREMENT_ORIGIN": origin,
                    "S8_1_MEASUREMENT_ORIGIN": "SOURCE_VERIFIED_CURRENT_MEASUREMENT",
                    "REFERENCE_SCOPE": scope, "REFERENCE_VALUE": ref_val, "S8_1_VALUE": s_val, "DIFF": diff,
                    "REFERENCE_ON_S8_1_SCOPE": eq_val,
                    "EQUAL_SCOPE_DIFF": None if eq_val is None else eq_val - s_val,
                    "CLASSES": classes, "CLASSES_CLOSE": True, "NOTE": note})
        for c, v in classes.items():
            causes.append({"REFERENCE": ref, "QUANTITY": qty, "CLASS": c, "VALUE_REFERENCE_MINUS_S8_1": v,
                           "BASIS": BASIS[c]})

    # ---------------------------------------------------- A: old Urban CR, cell by cell
    cells, crd = cr_cells(where, fx, fy)
    refs["OLD_URBAN_CR"] = {"path": _rel(CR_CELLS), "sha256": _sha(CR_CELLS), "dashboard": _rel(CR_DASH),
                            "dashboard_sha256": _sha(CR_DASH)}
    dash = next(r for r in _j(CR_DASH)["rows"] if r["trade"] == "GROUND_SLAB")
    marker_cells = [c for c in cells if any(t.startswith("T=") for t in c["labels"])]
    if sorted(c["s8_1"] for c in marker_cells) != markers:
        raise SystemExit("the old Urban marker cells do not land on the S8.1 zones: frame or mapping wrong")
    released = [c for c in cells if c["part"] == "RELEASED_ZONE_PART"]
    best = [c for c in cells if c["eff_width_mm"] >= SLIVER_EFF_WIDTH_MM]
    for name, sel, rep, scope in (
            ("OLD_URBAN_CR_LOWER_BOUND", released, dash["lower_bound"],
             "cells inside the V3a / V3b T= zones (RELEASED_ZONE_PART) x 0.10"),
            ("OLD_URBAN_CR_BEST", best, dash["best_provisional"],
             "every cell between ground beams >= 450 mm effective width x 0.10 (T=10cm applied to all)")):
        items = [(c["id"], c["area_m2"], c["s8_1"]) for c in sel]
        cls = scaled(area_classes(items, recs, markers), T_M)
        cls["REFERENCE_ROUNDING"] = rep - math.fsum(c["area_m2"] for c in sel) * T_M
        eqv = math.fsum(c["area_m2"] for c in marker_cells) * T_M
        add(name, "CONCRETE_M3", "CELL", "OLD_URBAN_CALCULATED (cell = footprint - 300 mm bands - columns - single "
            "lines)", rep, scope, cls, eqv, f"{len(sel)} cells")

    # ---------------------------------------------------- B: old Urban R3 / R4 zones (area x rate)
    r4 = _j(R4)
    zc = {c["comp_id"]: c for c in r4["components"] if c["population_id"].startswith("POP:GROUND_SLAB:")}
    zpop = {p["pop_id"]: p for p in r4["populations"] if p["pop_id"].startswith("POP:GROUND_SLAB:")}
    r3pop = {p["pop_id"]: p for p in _j(R3)["populations"] if p["pop_id"].startswith("POP:GROUND_SLAB:")}
    refs["OLD_URBAN_R4"] = {"path": _rel(R4), "sha256": _sha(R4)}
    refs["OLD_URBAN_R3"] = {"path": _rel(R3), "sha256": _sha(R3)}
    zone_area = {z: zc[f"POP:GROUND_SLAB:{z}|MESH_X"]["provisional_length_m"] / 5.0 for z in ("ZONE-1", "ZONE-2")}
    cr_zone = {"ZONE-1": [c for c in released if c["footprint"] == "FP-1"],
               "ZONE-2": [c for c in released if c["footprint"] == "FP-2"]}
    cr_zone_area = {z["kind"]: z["area_m2"] for z in crd["released_zones"]}
    if abs(zone_area["ZONE-1"] - cr_zone_area["V3A_ZONE"]) > 1e-3 or \
            abs(zone_area["ZONE-2"] - cr_zone_area["V3B_ZONE"]) > 1e-3:
        raise SystemExit("R4 zone areas are not the V3a / V3b zones the CR cells split")
    zone_items = [(c["id"], c["area_m2"], c["s8_1"]) for z in ("ZONE-1", "ZONE-2") for c in cr_zone[z]]
    zone_cls_m2 = area_classes(zone_items, recs, markers)
    zone_cls_m2["ZONE_POLYGON_RESIDUAL"] = math.fsum(zone_area.values()) - math.fsum(a for _, a, _ in zone_items)
    eq_kg = math.fsum(c["area_m2"] for c in marker_cells) * KG_PER_M2
    for name, pops in (("OLD_URBAN_R4", zpop), ("OLD_URBAN_R3", r3pop)):
        ref_kg = math.fsum(p["lower_bound_kg"] + p["provisional_kg"] for p in pops.values())
        cls = scaled(zone_cls_m2, KG_PER_M2)
        cls["REFERENCE_ROUNDING"] = ref_kg - math.fsum(zone_area.values()) * KG_PER_M2
        add(name, "REBAR_KG", "ZONE_VIA_CR_CELL_SPLIT", "OLD_URBAN_CALCULATED (zone area x 5 m/m2 each way, "
            "PROVISIONAL)", ref_kg, "ZONE-1 (V3a closed zone round marker 1690) + ZONE-2 (V3b closed footprint round "
            "marker 169D)", cls, eq_kg,
            "; ".join(f"{z} {zone_area[z]:.5f} m2 ({pops[f'POP:GROUND_SLAB:{z}']['occurrence_why']})"
                      for z in ("ZONE-1", "ZONE-2")))

    # ---------------------------------------------------- C: old Urban V3b
    vrows, vpop = v3b_ground_slab_rows()
    refs["OLD_URBAN_V3B"] = {"path": _rel(V3B), "sha256": _sha(V3B), "structure": _rel(V3B_STRUCT),
                             "structure_sha256": _sha(V3B_STRUCT)}
    um_v = vrows[0]["net_kg"] / (vrows[0]["count"] * vrows[0]["straight_m"])
    v_kg = math.fsum(r["net_kg"] for r in vrows)
    z2 = [r for r in vrows if r["ref"].startswith("ZONE-2")]
    z1 = [r for r in vrows if r["ref"].startswith("ZONE-1")]
    a2 = z2[0]["straight_m"] * (z2[0]["count"] - 1) * 0.2               # V3b: L = a / ((n - 1) x 0.2)
    a1 = z1[0]["straight_m"] / 5.0
    count_conv = math.fsum(r["net_kg"] for r in z2) - 2 * 5 * a2 * um_v
    cls = scaled(zone_cls_m2, KG_PER_M2)
    cls["ZONE_POLYGON_RESIDUAL"] = (a1 + a2 - math.fsum(a for _, a, _ in zone_items)) * KG_PER_M2
    cls["COUNT_CONVENTION"] = count_conv
    cls["REFERENCE_ROUNDING"] = v_kg - count_conv - (a1 + a2) * KG_PER_M2
    lap_kg = math.fsum(r.get("lap_kg") or 0.0 for r in vrows)
    add("OLD_URBAN_V3B", "REBAR_KG", "ZONE_VIA_CR_CELL_SPLIT",
        "OLD_V3B_CALCULATED (ZONE-2: n = floor(sqrt(A)/0.2) + 1 equivalent square bars; ZONE-1 area x 5)", v_kg,
        "ZONE-1 mesh X/Y (GROUND population) + ZONE-2 mesh X/Y (GROUND_SLAB population)", cls, eq_kg,
        f"population row GROUND_SLAB = {vpop['net_kg']} kg (ZONE-2 only); procurement laps {lap_kg:.3f} kg "
        "not in net, not compared")
    me = _j(CONCRETE)
    refs["MULTI_ENGINE_CONCRETE"] = {"path": _rel(CONCRETE), "sha256": _sha(CONCRETE)}
    gsrow = next(r for r in me["rows"] if r["category"] == "GROUND_SLAB")
    cls = scaled(zone_cls_m2, T_M)
    cls["ZONE_POLYGON_RESIDUAL"] = (a1 + a2 - math.fsum(a for _, a, _ in zone_items)) * T_M
    cls["REFERENCE_ROUNDING"] = gsrow["URBAN"] - (a1 + a2) * T_M
    add("OLD_URBAN_V3B", "CONCRETE_M3", "ZONE_VIA_CR_CELL_SPLIT",
        "OLD_V3B_CALCULATED (zones minus beam bands / columns x 0.10, LOWER_BOUND)", gsrow["URBAN"],
        "C-GSLAB-ZONE-1 + C-GSLAB-ZONE-2", cls, math.fsum(c["area_m2"] for c in marker_cells) * T_M)

    # ---------------------------------------------------- D: christiannp forensic rerun (read-only data)
    ch = christiannp(sys.argv[1] if len(sys.argv) > 1 else None, where)
    if ch:
        refs["CHRISTIANNP_FORENSIC"] = {"path": "CHRISTIANNP_FORENSIC_RERUN (external, read-only)",
                                        "sha256": ch["sha256"]}
        items = [(f["id"], f["slab_m2"], f["s8_1"]) for f in ch["faces"] if f["slab_m2"] > 0]
        cls_m2 = area_classes(items, recs, markers)
        ch_marker = math.fsum(a for _, a, rid in items if rid in markers)
        cls = scaled(cls_m2, T_M)
        cls["REFERENCE_ROUNDING"] = ch["slab_m2"] * T_M - math.fsum(a for _, a, _ in items) * T_M
        add("CHRISTIANNP_FORENSIC", "CONCRETE_M3", "CELL", "DONOR_CALCULATED (vector planar faces, sampled "
            "apportioning; T=10cm applied to all faces)", ch["slab_m2"] * T_M,
            "every vector slab face between ground beams, net of beams / columns / lift pit", cls, ch_marker * T_M,
            f"{len(items)} faces with slab area; openings {ch['openings_m2']} m2 (PIT_7BE)")
        cls = scaled(cls_m2, KG_PER_M2)
        cls["REFERENCE_ROUNDING"] = ch["kg"] - math.fsum(a for _, a, _ in items) * KG_PER_M2
        add("CHRISTIANNP_FORENSIC", "REBAR_KG", "CELL", "DONOR_CALCULATED (5 m/m2 x area each way, single mesh, "
            "laps / cover excluded)", ch["kg"], "same faces as its concrete", cls, ch_marker * KG_PER_M2,
            "; ".join(f"{r['COMPONENT']} {r['KG']} kg ({r['GEOMETRY_LENGTH']})" for r in ch["rebar_rows"]))

    # ---------------------------------------------------- E: one-figure references
    lin = _j(LINEAGE)
    refs["FREELANCER"] = {"path": _rel(LINEAGE), "sha256": _sha(LINEAGE), "workbook_sha256": lin.get("workbook_sha256")}
    gcat = next(c for c in lin["categories"] if "GROUND_SLAB" in c.get("quantity_by_physical_kind", {}))
    leaf = next(s for s in gcat["subcomponents"] if s.get("physical_kind") == "GROUND_SLAB")
    fr_m3 = leaf["value"]
    blocked_m2 = summ["blocked_area_m2"]
    cls = {"ZONE_EXTENT_SCOPE": blocked_m2 * leaf["D"],
           "GROSS_AREA_UNSEPARATED": fr_m3 - A * leaf["D"] - blocked_m2 * leaf["D"],
           "MARKER_CELL_GEOMETRY": A * leaf["D"] - V}
    add("FREELANCER", "CONCRETE_M3", "CATEGORY", "REFERENCE_QS (one gross ground-slab area x thickness)", fr_m3,
        f"one row: {leaf['B']} m2 x {leaf['D']} m (gross outline, beams not deducted)", cls, None,
        "ZONE_EXTENT_SCOPE attributes S8.1's 19 blocked faces at the reference's own 0.10 m; the rest of the gross "
        "area (beam / column footprints, the stair cell, the unfaced lift-pit core) is one row and not separable")
    me_r = _j(REBAR_ME)
    refs["MULTI_ENGINE_REBAR"] = {"path": _rel(REBAR_ME), "sha256": _sha(REBAR_ME)}
    gb = next(r for r in me_r["rows"] if r["category"] == "GROUND_BEAMS_AND_GROUND_SLAB")
    add("FREELANCER", "REBAR_KG", "NOT_COMPARABLE", "REFERENCE_QS", None,
        "one steel lump for ground beams + ground slab + boundary ground beam", {}, None,
        f"{gb['freelancer_steel_t']} t over {gb['freelancer_concrete_m3']} m3: no ground-slab steel line")
    for name, key, origin in (("UC4N", "UC4N", "ORACLE_CALCULATED"),
                              ("CHRISTIANNP_ORIGINAL", "CHRISTIANNP", "DONOR_CALCULATED (original run)")):
        add(name, "CONCRETE_M3", "CATEGORY", origin, gsrow[key], "one ground-slab figure, extent not itemised",
            {"SCOPE_UNSEPARATED": gsrow[key] - V}, None, "no cell list behind the figure")
    add("UC4N", "REBAR_KG", "NOT_COMPARABLE", "ORACLE_CALCULATED", None, "project net rebar total only", {}, None,
        "no ground-slab steel figure")
    rough = _j(ROUGH)
    refs["ROUGH_PROFILE"] = {"path": _rel(ROUGH), "sha256": _sha(ROUGH)}
    ratio = rough["ratios_kg_per_m3"]["GROUND_BEAMS_AND_GROUND_SLAB"]
    add("ROUGH_130_KG_PER_M3", "REBAR_KG", "SANITY_ONLY", "SANITY_HEURISTIC", ratio * V,
        "S8.1 concrete x the GROUND_BEAMS_AND_GROUND_SLAB ratio (SANITY_CHECK_ONLY)",
        {"SANITY_RATIO": ratio * V - K}, None,
        f"S8.1 intensity {K / V:.3f} kg/m3 = 2 x 5 x 0.617 kg/m / 0.10 m; the 130 ratio is a category ratio over ground "
        "beams and slab together; never promoted")

    # ---------------------------------------------------- equal scope: the two marker cells
    for k in markers:
        r = recs[k]
        crc = [c for c in marker_cells if c["s8_1"] == k]
        chf = [f for f in ch["faces"] if f["s8_1"] == k and f["slab_m2"] > 0] if ch else []
        eq.append({"S8_1_ROW_ID": k, "ZONE_ID": r["zone"], "S8_1_AREA_M2": r["area_m2"],
                   "S8_1_CONCRETE_M3": r["concrete_m3"], "S8_1_KG": r["kg"],
                   "OLD_URBAN_CELL": [c["id"] for c in crc], "OLD_URBAN_AREA_M2": math.fsum(c["area_m2"] for c in crc),
                   "OLD_URBAN_MINUS_S8_1_M2": math.fsum(c["area_m2"] for c in crc) - r["area_m2"],
                   "OLD_URBAN_KG_AREA_X_RATE": math.fsum(c["area_m2"] for c in crc) * KG_PER_M2,
                   "CHRISTIANNP_FACE": [f["id"] for f in chf] if ch else None,
                   "CHRISTIANNP_AREA_M2": math.fsum(f["slab_m2"] for f in chf) if ch else None,
                   "CHRISTIANNP_MINUS_S8_1_M2": (math.fsum(f["slab_m2"] for f in chf) - r["area_m2"]) if ch else None,
                   "THICKNESS_ALL_MM": 100, "RATE_ALL": "5Ø10/m E.W., one mesh", "CLASS": "MARKER_CELL_GEOMETRY"})

    # ---------------------------------------------------- cell crosswalk
    cross = []
    for k, r in sorted(recs.items()):
        crc = [c for c in cells if c["s8_1"] == k]
        chf = [f for f in ch["faces"] if f["s8_1"] == k and f["slab_m2"] > 0] if ch else []
        zone = sorted({("ZONE-1 (V3a)" if c["footprint"] == "FP-1" else "ZONE-2 (V3b)") for c in crc
                       if c["part"] == "RELEASED_ZONE_PART"})
        cross.append({"S8_1_ROW_ID": k, "S8_1_ROW_KIND": r["row_kind"], "S8_1_STATE": r["state"],
                      "S8_1_ZONE_ID": r["zone"], "S8_1_AREA_M2": r["area_m2"], "S8_1_CONCRETE_M3": r["concrete_m3"],
                      "S8_1_KG": r["kg"], "OLD_URBAN_CELLS": [c["id"] for c in crc],
                      "OLD_URBAN_AREA_M2": math.fsum(c["area_m2"] for c in crc) if crc else None,
                      "OLD_URBAN_PART": sorted({c["part"] for c in crc}), "OLD_URBAN_ZONE": zone,
                      "CHRISTIANNP_FACES": [f["id"] for f in chf] if ch else None,
                      "CHRISTIANNP_SLAB_M2": math.fsum(f["slab_m2"] for f in chf) if chf else None,
                      "CLASS_IF_A_REFERENCE_QUANTIFIES_IT": record_class(r) if (crc or chf) else "",
                      "NOTE": ("marker cell: equal scope" if r["zone"] else r["state"] if r["row_kind"] != "FACE"
                               else "no marker in this cell: S8.1 holds it BLOCKED (unknown, not zero)")})
    for c in cells:
        if c["s8_1"] is None:
            cross.append({"S8_1_ROW_ID": "", "S8_1_ROW_KIND": "NO_S8_1_RECORD", "OLD_URBAN_CELLS": [c["id"]],
                          "OLD_URBAN_AREA_M2": c["area_m2"], "OLD_URBAN_PART": [c["part"]],
                          "CLASS_IF_A_REFERENCE_QUANTIFIES_IT": "POPULATION_GAP",
                          "NOTE": ("lift-pit core cell (contains S-BW 7BE; old Urban counted the pit as slab)"
                                   if c["area_m2"] > 1.0 else "sliver / beam-band remnant")})
    for f in (ch["faces"] if ch else []):
        if f["s8_1"] is None and (f["slab_m2"] > 0 or f["class"] == "OPENING"):
            cross.append({"S8_1_ROW_ID": "", "S8_1_ROW_KIND": "NO_S8_1_RECORD", "CHRISTIANNP_FACES": [f["id"]],
                          "CHRISTIANNP_SLAB_M2": f["slab_m2"], "CLASS_IF_A_REFERENCE_QUANTIFIES_IT": "POPULATION_GAP",
                          "NOTE": f"christiannp {f['class']} face{' ' + f['markers'] if f['markers'] else ''}"})

    # ---------------------------------------------------- findings (new issues; nothing applied here)
    gap_cr = [c for c in cells if c["s8_1"] is None and c["area_m2"] > 1.0]
    gap_ch = [f for f in (ch["faces"] if ch else []) if f["s8_1"] is None and f["class"] == "SLAB"]
    findings += [
        {"ID": "S8.1-PF-01", "KIND": "POPULATION_GAP",
         "WHAT": "a region round lift pit 7BE has no S1 / PRE-S8 / S8.1 ground-slab face, so S8.1 neither measures nor "
                 "blocks it",
         "EVIDENCE": f"old Urban cell {[c['id'] for c in gap_cr]} {math.fsum(c['area_m2'] for c in gap_cr):.4f} m2; "
                     + (f"christiannp {len(gap_ch)} slab faces {math.fsum(f['slab_m2'] for f in gap_ch):.4f} m2 + "
                        f"pit opening {ch['openings_m2']} m2" if ch else "christiannp not supplied"),
         "EFFECT_ON_S8_1": "none on the two-zone quantities (no TT1 marker there); the blocked register under-states "
                           "the unquantified ground slab",
         "NEXT": "new issue: face the GBP core with the S-BW pit lines as barriers, register the cells as BLOCKED "
                 "(no thickness / mesh) and the pit as an opening; new regression; new version"},
        {"ID": "S8.1-PF-02", "KIND": "ZONE_EXTENT_INTERPRETATION",
         "WHAT": "old Urban extended each TT1 marker to a multi-cell zone (V3a ZONE-1: 7 cells; V3b ZONE-2: the whole "
                 "FP-2 footprint, 7 cells); christiannp and the freelancer apply T=10cm to every cell",
         "EVIDENCE": "no printed zone boundary, hatch extent or note ties TT1 to more than the cell that holds it "
                     "(S8.1 02 rules / 06 blocked)",
         "EFFECT_ON_S8_1": "none; the 19 other cells stay BLOCKED",
         "NEXT": "owner / engineer question: does 'T=10cm 5Ø10/m E.W.' apply to the whole ground slab? An answer is "
                 "new source evidence for a new version"},
        {"ID": "S8.1-PF-03", "KIND": "OWNERSHIP_OVERLAP",
         "WHAT": "old Urban (V3a ZONE-1) and christiannp both counted stair-flight cell SP-GBP-12 as ground slab",
         "EVIDENCE": "; ".join(f"{x['OLD_URBAN_CELLS']} {x['OLD_URBAN_AREA_M2']} m2 / christiannp "
                               f"{x['CHRISTIANNP_FACES']} {x['CHRISTIANNP_SLAB_M2']} m2"
                               for x in cross if x["S8_1_ROW_ID"] == "SP-GBP-12"),
         "EFFECT_ON_S8_1": "none; PRE-S8 gives the cell to the S8 stair family, S8.1 never measures it",
         "NEXT": "keep it with the stair family; no ground-slab item there"},
        {"ID": "S8.1-PF-04", "KIND": "COUNT_CONVENTION",
         "WHAT": "V3b ZONE-2 uses n = floor(sqrt(A)/0.2) + 1 equivalent square bars per direction",
         "EVIDENCE": f"+{count_conv:.3f} kg over area x rate", "EFFECT_ON_S8_1": "none (S8.1 never adds +1)",
         "NEXT": "none"}]

    # ---------------------------------------------------- write
    unknown = [c for c in causes if c["CLASS"] == "UNKNOWN"]
    _csv("S8_1_POST_FREEZE_REFERENCE_TOTALS.csv", tot, list(tot[0]))
    _csv("S8_1_POST_FREEZE_EQUAL_SCOPE.csv", eq, list(eq[0]))
    _csv("S8_1_POST_FREEZE_CELL_CROSSWALK.csv", cross, list(cross[0]))
    _csv("S8_1_POST_FREEZE_DIFFERENCE_CAUSES.csv", causes, list(causes[0]))
    _csv("S8_1_POST_FREEZE_FINDINGS.csv", findings, list(findings[0]))
    s = {"round": "S8_1_POST_FREEZE", "freeze_manifest_verified": True, "freeze_commit": full_commit,
         "freeze_manifest_sha256": _sha(MANIFEST), "frozen_engine_stamp": m["engine_commit_stamp"],
         "classes": list(CLASSES), "unknown_rows": unknown, "references": refs, "frame_origin": [fx, fy],
         "s8_1": {"included_area_m2": A, "concrete_m3": V, "total_kg": K, "kg_per_m2": KG_PER_M2,
                  "kg_per_m3": K / V, "blocked_area_m2": summ["blocked_area_m2"], "marker_cells": markers,
                  "measurement_origin": "SOURCE_VERIFIED_CURRENT_MEASUREMENT", "frozen_origin_text": s81_origin},
         "reference_totals": tot, "equal_scope": eq, "findings": findings,
         "old_urban": {"zone_area_m2": zone_area, "cr_released_m2": math.fsum(c["area_m2"] for c in released),
                       "cr_best_m2": math.fsum(c["area_m2"] for c in best),
                       "zone_cells": {z: [c["s8_1"] for c in cr_zone[z]] for z in cr_zone},
                       "v3b_count_convention_kg": count_conv, "v3b_lap_kg_not_compared": lap_kg},
         "christiannp": None if not ch else {"slab_m2": ch["slab_m2"], "kg": ch["kg"],
                                             "openings_m2": ch["openings_m2"], "gross_m2": ch["gross_m2"],
                                             "faces_without_s8_1_record": len([f for f in ch["faces"]
                                                                               if f["s8_1"] is None]),
                                             "slab_faces_without_s8_1_record": len(gap_ch)},
         "rough": {"ratio_kg_per_m3": ratio, "use": rough["use"], "reference_kg_on_s8_1_scope": ratio * V,
                   "promoted": False},
         "tuned": False, "s8_1_outputs_written": False,
         "rule": "comparison only: nothing here changes an S8.1 quantity; a correction needs a new issue, new source "
                 "evidence, a new regression and a new version"}
    _json("S8_1_POST_FREEZE_SUMMARY.json", s)
    (HERE / "S8_1_POST_FREEZE_COMPARISON.md").write_text(report(s), encoding="utf-8")
    print(json.dumps({f"{t['REFERENCE']} {t['QUANTITY']}": (t["REFERENCE_VALUE"], t["DIFF"],
                                                             t["REFERENCE_ON_S8_1_SCOPE"]) for t in tot}, indent=1))


BASIS = {
    "MARKER_CELL_GEOMETRY": "same marker cell, different boundary: S8.1 measures the drawn ground-beam inner faces with "
                            "the arc as an arc; old Urban subtracts 300 mm bands and single lines from a founded "
                            "footprint; christiannp samples vector faces",
    "ZONE_EXTENT_SCOPE": "the reference quantifies cells with no TT1 marker; S8.1 binds each marker to the cell that "
                         "holds it and keeps the other cells BLOCKED (unknown is not zero)",
    "OTHER_OWNER_CELL": "the reference counts the stair-flight cell SP-GBP-12 as ground slab; PRE-S8 gives it to the "
                        "S8 stair family",
    "POPULATION_GAP": "reference area at points no S1 / PRE-S8 / S8.1 face covers: the lift-pit core round S-BW 7BE "
                      "(old Urban counted the pit inside one cell) and slivers / beam-band remnants",
    "ZONE_POLYGON_RESIDUAL": "the old zone polygon (V3a ZONE-1 / V3b ZONE-2) against its own coverage-round cell split",
    "COUNT_CONVENTION": "V3b ZONE-2: n = floor(sqrt(A)/0.2) + 1 bars of A / ((n - 1) x 0.2) m; S8.1 = rate x area, "
                        "never +1",
    "GROSS_AREA_UNSEPARATED": "one gross area row: beam / column footprints, the stair cell and the unfaced core are "
                              "not separable",
    "SCOPE_UNSEPARATED": "one ground-slab figure with no cell list: whole-slab scope against two marker cells",
    "REFERENCE_ROUNDING": "the reference's printed rounding of its own area / kg",
    "SANITY_RATIO": "a category kg/m3 heuristic (ground beams + slab together) against a restricted rate x area QTO",
    "UNKNOWN": "not explained"}


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:.9f}".rstrip("0").rstrip(".") if v == v else "nan"
    if isinstance(v, (list, tuple, dict, set)):
        return json.dumps(sorted(v) if isinstance(v, set) else v, ensure_ascii=False, sort_keys=True, default=str)
    return str(v)


def _csv(name, rows, fields):
    keys = list(fields)
    for r in rows:
        keys += [k for k in r if k not in keys]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=keys, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in keys})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def _json(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n",
                             encoding="utf-8")


def report(s):
    def n(v, d=3):
        return "n/a" if v is None else f"{v:,.{d}f}"
    S = s["s8_1"]
    L = [
        "# S8.1 post-freeze comparison (ground slab, two source-zoned cells)",
        "",
        f"S8.1 was frozen at `{s['freeze_commit'][:7]}`. The manifest sha256 is `{s['freeze_manifest_sha256'][:16]}...`.",
        "This script refused to open any earlier figure until three checks passed:",
        "- every frozen hash still matches;",
        "- the manifest is the one committed at the freeze;",
        "- that commit holds no post-freeze file.",
        "",
        f"Nothing here changes S8.1. It stays **{n(S['included_area_m2'])} m2, {n(S['concrete_m3'])} m3, "
        f"{n(S['total_kg'])} kg** (two marker cells {', '.join(S['marker_cells'])}; "
        f"{S['kg_per_m2']:.4f} kg/m2, {S['kg_per_m3']:.2f} kg/m3). The other 19 faces "
        f"({n(S['blocked_area_m2'])} m2) stay BLOCKED.",
        "",
        "## Equal scope: the two marker cells",
        "",
        "| cell | S8.1 m2 | old Urban cell m2 | diff | christiannp face m2 | diff |",
        "|---|---|---|---|---|---|"]
    for e in s["equal_scope"]:
        L.append(f"| {e['S8_1_ROW_ID']} ({e['ZONE_ID']}) | {n(e['S8_1_AREA_M2'], 4)} | {n(e['OLD_URBAN_AREA_M2'], 4)} | "
                 f"{n(e['OLD_URBAN_MINUS_S8_1_M2'], 4)} | {n(e['CHRISTIANNP_AREA_M2'], 4)} | "
                 f"{n(e['CHRISTIANNP_MINUS_S8_1_M2'], 4)} |")
    L += ["", "Every reference uses the same thickness (0.10 m) and the same mesh (5Ø10/m each way, one layer) on "
              "these two cells. On equal scope the only difference is the cell boundary.", "",
          "## Reference totals", "",
          "| reference | quantity | matching | reference | S8.1 | reference - S8.1 | on S8.1 scope | classes |",
          "|---|---|---|---|---|---|---|---|"]
    for t in s["reference_totals"]:
        cl = ", ".join(f"{c} {v:+,.3f}" for c, v in sorted(t["CLASSES"].items(), key=lambda kv: -abs(kv[1]))) or "-"
        L.append(f"| {t['REFERENCE']} | {t['QUANTITY']} | {t['MATCHING']} | {n(t['REFERENCE_VALUE'])} | "
                 f"{n(t['S8_1_VALUE'])} | {n(t['DIFF'])} | {n(t['REFERENCE_ON_S8_1_SCOPE'])} | {cl} |")
    L += ["", "MEASUREMENT_ORIGIN is on every row of `S8_1_POST_FREEZE_REFERENCE_TOTALS.csv`. The old V3b figures "
              "are `OLD_V3B_CALCULATED`; S8.1 is the source-verified current measurement.", "",
          "## Findings (new issues; nothing applied)", ""]
    for f in s["findings"]:
        L.append(f"- **{f['ID']} {f['KIND']}**: {f['WHAT']}. Evidence: {f['EVIDENCE']}. Effect on S8.1: "
                 f"{f['EFFECT_ON_S8_1']}. Next: {f['NEXT']}.")
    L += ["", "## Class meanings", ""]
    for c in s["classes"]:
        L.append(f"- `{c}`: {BASIS[c]}.")
    L += ["", "The rough 130 kg/m3 ratio is `SANITY_CHECK_ONLY`. It is shown, not used. No S8.1 quantity is tuned, "
              "scaled or promoted towards any reference.", "",
          f"UNKNOWN rows: {len(s['unknown_rows'])}."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
