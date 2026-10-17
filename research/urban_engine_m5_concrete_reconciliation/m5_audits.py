"""M5 family audits A - G: ground beams + ground slab, suspended slabs, beams / foundations / columns, stairs / domes
/ pool, blinding. Every number comes from the M4 drawing model, the frozen registers or the source records."""

from __future__ import annotations

from collections import defaultdict

from shapely.geometry import Polygon
from shapely.ops import unary_union

import m5_reconcile as M
import m5_tables as T


def _r(x, n=3):
    return None if x is None else round(float(x) + 0.0, n) + 0.0


# ------------------------------------------------------------------ A. ground beams + ground slab
def gs_audit(D, U, F, MC):
    sl = D["sheets"]["SH08"]["slab"]
    faces = [f for f in sl["faces"] if len(f["polygon"]) >= 3]
    union = unary_union([Polygon(f["polygon"]).buffer(0) for f in faces])
    parts = list(getattr(union, "geoms", [union]))
    by_region = defaultdict(float)
    for f in faces:
        by_region[f["region"]] += f["area_m2"]
    gs_items = [u for u in U if u["ORIGIN"] == "M4" and u["FAMILY"] == "GROUND_SLAB"]
    meas = sum(u["DIMS"]["area_m2"] for u in gs_items if u["CATEGORY"] == "PROVISIONAL")
    unres = sum(u["DIMS"]["area_m2"] for u in gs_items if u["CATEGORY"] == "UNRESOLVED")
    flr = [r for r in F["rows"] if r["FAMILY"] == "GROUND_SLAB"][0]
    fp = union.area * 1e-6
    out = {"fl_area_m2": flr["B"], "t_m": flr["D"], "fl_m3": flr["VALUE_M3"], "footprint_m2": fp,
           "footprint_parts": [{"area_m2": p.area * 1e-6, "bounds_m": [round(v / 1000, 3) for v in p.bounds],
                                "outer_perimeter_m": p.exterior.length / 1000} for p in parts],
           "measured_m2": meas, "unresolved_m2": unres, "members_inside_m2": fp - meas - unres,
           "regions_m2": dict(by_region), "beam_strip_m2": by_region.get("BEAM_STRIP", 0.0),
           "column_m2": by_region.get("COLUMN", 0.0),
           "christiannp_area_m2": MC["christiannp_explicit"].get("GROUND_SLAB_AREA_m2"),
           "christiannp_t_m": MC["christiannp_explicit"].get("GROUND_SLAB_T_m")}
    cells = []
    fpoly = {f["face_id"]: f for f in faces}
    for u in gs_items:
        fid = u["UID"].split(":")[-1]
        f = fpoly.get(fid, {})
        c = T.contrib(u)
        P = Polygon(f["polygon"]) if f else None
        cells.append({"CELL_ID": fid, "M4_ITEM": u["UID"], "REGION": f.get("region"), "AREA_M2": _r(u["DIMS"]["area_m2"], 4),
                      "AREA_GROSS_M2": _r(u["DIMS"].get("area_gross_m2") or f.get("area_gross_m2"), 4),
                      "MEMBER_OVERLAP_M2": _r(u["DIMS"].get("member_overlap_deducted_m2") or f.get("member_overlap_m2"), 4),
                      "T_M": u["DIMS"].get("t_m"), "T_BASIS": u["DIMS"].get("t_basis") or "",
                      "M4_CATEGORY": u["CATEGORY"], "M5_STATE": c["STATE"], "MEASURED_M3": _r(c["MB"], 4),
                      "CONDITIONAL_LOW_M3": _r(c["CL"], 4), "CONDITIONAL_HIGH_M3": _r(c["CH"], 4),
                      "CENTROID_X_M": _r(P.centroid.x / 1000) if P else None,
                      "CENTROID_Y_M": _r(P.centroid.y / 1000) if P else None,
                      "NOTE": u.get("M5_NOTE") or (f.get("region_reason") or "")})
    return out, cells


def gb_audit(D, U, F):
    rows = defaultdict(lambda: {"N": 0, "L": 0.0, "PLAN": 0.0, "LOW": 0.0, "BASE": 0.0, "HIGH": 0.0})
    for u in U:
        if u["ORIGIN"] != "M4" or u["FAMILY"] not in ("GROUND_BEAMS", "STRAPS") or u["CATEGORY"] != "PROVISIONAL":
            continue
        d = u["DIMS"]
        npl = d.get("net_plan_m2") or 0.0
        cls = "STRAP " + u["MARK"] if u["FAMILY"] == "STRAPS" else (d.get("arch_class") or "INTERIOR")
        lvl = d.get("arch_floor_level_m")
        key = (cls, d.get("width_m"), _r((u["BASE"] or 0) / npl, 2) if npl else None,
               _r((u["LOW"] or 0) / npl, 2) if npl else None, _r((u["HIGH"] or 0) / npl, 2) if npl else None,
               f"{lvl:+.2f}" if lvl is not None else "", u["BLOCKER"])
        R = rows[key]
        R["N"] += 1
        R["L"] += d.get("length_m") or d.get("clear_length_m") or 0.0
        R["PLAN"] += npl
        R["LOW"] += u["LOW"] or 0.0
        R["BASE"] += u["BASE"] or 0.0
        R["HIGH"] += u["HIGH"] or 0.0
    out = []
    for k, R in sorted(rows.items(), key=lambda kv: str(kv[0])):
        out.append({"CLASS": k[0], "WIDTH_M": k[1], "DEPTH_BASE_M": k[2], "DEPTH_LOW_M": k[3], "DEPTH_HIGH_M": k[4],
                    "ARCH_FLOOR_LEVEL": k[5], "BLOCKER": k[6], "N_SPANS": R["N"], "LENGTH_M": _r(R["L"]),
                    "NET_PLAN_M2": _r(R["PLAN"]), "LOW_M3": _r(R["LOW"]), "BASE_M3": _r(R["BASE"]),
                    "HIGH_M3": _r(R["HIGH"])})
    return out


# ------------------------------------------------------------------ B. suspended slabs
def slab_audit(D, U, F, MC):
    sheet = {"GF": "SH06", "1F": "SH04", "2F": "SH02"}
    faces = {st: {f["face_id"]: f for f in D["sheets"][sh]["slab"]["faces"]} for st, sh in sheet.items()}
    rows = []
    for u in U:
        if u["ORIGIN"] != "M4" or u["FAMILY"] != "SLABS":
            continue
        fid = u["UID"].split(":")[-1]
        f = faces.get(u["FLOOR"], {}).get(fid, {})
        holes = [Polygon(h).area * 1e-6 for h in (f.get("hole_polygons") or []) if len(h) >= 3]
        d = u["DIMS"]
        c = T.contrib(u)
        gross = d.get("area_gross_m2") or (d.get("area_m2") or 0.0) + (d.get("member_overlap_deducted_m2") or 0.0)
        rows.append({"PANEL_ID": fid, "FLOOR": u["FLOOR"], "SHEET": sheet[u["FLOOR"]],
                     "GROSS_AREA_M2": _r(gross + sum(holes), 4), "OPENINGS_M2": _r(sum(holes), 4),
                     "N_OPENINGS": len(holes), "BEAM_COLUMN_OVERLAP_M2": _r(d.get("member_overlap_deducted_m2") or 0.0, 4),
                     "NET_AREA_M2": _r(d.get("area_m2"), 4), "THICKNESS_M": d.get("t_m"),
                     "THICKNESS_BASIS": d.get("t_basis") or d.get("region") or "", "M4_CATEGORY": u["CATEGORY"],
                     "M5_STATE": c["STATE"], "VOLUME_M3": _r(c["MB"], 4), "CONDITIONAL_HIGH_M3": _r(c["CH"], 4),
                     "SOURCE": T.S_loc(u), "NOTE": u.get("M5_NOTE") or ""})
    floors = []
    ce = MC["christiannp_explicit"]
    flr = defaultdict(lambda: [0.0, 0.0])
    for r in F["rows"]:
        if r["FAMILY"] == "SLABS":
            flr[r["FLOOR"]][0] += r["B"]
            flr[r["FLOOR"]][1] += r["VALUE_M3"]
    for st in ("GF", "1F", "2F"):
        pr = [r for r in rows if r["FLOOR"] == st and r["M5_STATE"] == "MEASURED"]
        a = sum(r["NET_AREA_M2"] for r in pr)
        v = sum(r["VOLUME_M3"] for r in pr)
        dflt = sum(r["NET_AREA_M2"] for r in pr if r["THICKNESS_BASIS"] == "PROJECT_DEFAULT")
        cn_a, cn_v = ce.get(f"NET_SLAB_{st}_m2"), ce.get(f"SLABS_{st}_m3")
        floors.append({"FLOOR": st, "URBAN_PANELS": len(pr), "URBAN_NET_AREA_M2": _r(a), "URBAN_M3": _r(v),
                       "URBAN_AREA_AT_PROJECT_DEFAULT_M2": _r(dflt), "SENSITIVITY_PER_CM_M3": _r(dflt * 0.01),
                       "FREELANCER_AREA_M2": _r(flr[st][0]), "FREELANCER_M3": _r(flr[st][1]),
                       "AREA_DIFF_FL_MINUS_URBAN_M2": _r(flr[st][0] - a),
                       "CHRISTIANNP_NET_AREA_M2": cn_a, "CHRISTIANNP_M3": cn_v,
                       "CHRISTIANNP_IMPLIED_T_M": _r(cn_v / cn_a) if cn_a else None,
                       "CHRISTIANNP_AREA_MINUS_URBAN_M2": _r(cn_a - a) if cn_a else None})
    return rows, floors


# ------------------------------------------------------------------ C / D. beams, frame per floor, foundations
def frame_per_floor(F, U, MC):
    fl = defaultdict(float)
    for r in F["rows"]:
        if r["FAMILY"] in ("COLUMNS", "BEAMS", "SLABS"):
            fl[(r["FLOOR"], r["FAMILY"])] += r["VALUE_M3"]
    ur = defaultdict(lambda: [0.0, 0.0, 0.0])
    for u in U:
        if u["FAMILY"] not in ("COLUMNS", "BEAMS", "SLABS"):
            continue
        c = T.contrib(u)
        ur[(u["FLOOR"], u["FAMILY"])][0] += c["MB"]
        ur[(u["FLOOR"], u["FAMILY"])][1] += c["CL"]
        ur[(u["FLOOR"], u["FAMILY"])][2] += c["CH"]
    ce = MC["christiannp_explicit"]
    rows = []
    for st in ("GF", "1F", "2F"):
        f = {k: fl[(st, k)] for k in ("COLUMNS", "BEAMS", "SLABS")}
        u = {k: ur[(st, k)][0] for k in ("COLUMNS", "BEAMS", "SLABS")}
        uc = sum(ur[(st, k)][2] for k in ("COLUMNS", "BEAMS", "SLABS"))
        cn = [ce.get(f"COL_{st}_m3"), ce.get(f"BEAMS_{st}_m3"), ce.get(f"SLABS_{st}_m3")]
        rows.append({"FLOOR": st, "FL_COLUMNS": _r(f["COLUMNS"]), "FL_BEAMS": _r(f["BEAMS"]), "FL_SLABS": _r(f["SLABS"]),
                     "FL_FRAME": _r(sum(f.values())), "URBAN_COLUMNS": _r(u["COLUMNS"]), "URBAN_BEAMS": _r(u["BEAMS"]),
                     "URBAN_SLABS": _r(u["SLABS"]), "URBAN_FRAME": _r(sum(u.values())),
                     "URBAN_CONDITIONAL_HIGH": _r(uc), "CHRISTIANNP_FRAME": _r(sum(cn)) if all(cn) else None,
                     "DIFF_FL_MINUS_URBAN_FRAME": _r(sum(f.values()) - sum(u.values()))})
    return rows


def beam_marks(elements):
    out = []
    for r in elements:
        if r["FAMILY"] not in ("BEAMS", "COLUMNS", "FOOTINGS", "NECKS", "STRAPS"):
            continue
        out.append({k: r[k] for k in ("ELEMENT_ID", "FAMILY", "FLOOR", "MARK_OR_PART", "FREELANCER_M3",
                                      "URBAN_MEASURED_BASE_M3", "URBAN_CONDITIONAL_HIGH_M3",
                                      "DIFF_FREELANCER_MINUS_URBAN_BASE_M3", "COST_KWD", "CLASS",
                                      "FREELANCER_DETAIL", "URBAN_STATES")})
    return out


# ------------------------------------------------------------------ G. blinding
def blinding_audit(D, U, F, brief, gs):
    bo = D["blinding_overlap"]
    fl = [r for r in F["rows"] if r["FAMILY"] == "BLINDING"][0]
    m4 = {u["MARK"] or u["UID"]: u for u in U if u["FAMILY"] == "BLINDING"}
    foot = next((u for u in U if u["FAMILY"] == "BLINDING" and u["UID"].endswith("FOOTINGS")), None)
    gb = next((u for u in U if u["FAMILY"] == "BLINDING" and u["UID"].endswith("GROUND_BEAMS")), None)
    t = 0.1
    mcp = brief["values_in_no_other_record"]["MCP_BLINDING_APPROX_M3"]["value"]
    cells = gs["measured_m2"] + gs["unresolved_m2"]
    rows = [
        {"OPTION": "B1 footings only (drawn layer, 10 cm, 10 cm projection)", "AREA_M2": _r(foot["DIMS"]["plan_m2_base"]),
         "M3": _r(foot["BASE"]), "BASIS": "p.13 typical footing details (machine-read, not person-reviewed)",
         "STATUS": "MEASURED (part of B2)"},
        {"OPTION": "B2 footings + ground beams, overlaps once (Urban M4)", "AREA_M2": _r(bo["placed_union_m2"][1]),
         "M3": _r(foot["BASE"] + gb["BASE"]), "BASIS": "p.13 draws the layer under every typical ground-beam "
         "section and both footing details; union of the placed outlines", "STATUS": "MEASURED (Urban base)"},
        {"OPTION": "B3 = B2 + a layer under the ground-slab cells", "AREA_M2": _r(bo["placed_union_m2"][1] + cells),
         "M3": _r(foot["BASE"] + gb["BASE"] + cells * t), "BASIS": "no layer is drawn under the 10 cm ground slab; "
         "only if the specification requires it", "STATUS": "CONDITIONAL ALTERNATIVE"},
        {"OPTION": "B4 full plot plate (freelancer)", "AREA_M2": _r(fl["B"] * fl["C"]), "M3": _r(fl["VALUE_M3"]),
         "BASIS": "15.00 x 31.37 m printed on SH08 x 0.10; covers court, garden and building alike",
         "STATUS": "CONDITIONAL ALTERNATIVE (not drawn)"},
        {"OPTION": "MCP figure (brief, 'about')", "AREA_M2": None, "M3": mcp,
         "BASIS": "christiannp A6: 0.10 thick + 0.10 projection; no file holds the quantity", "STATUS": "COMPARISON"},
    ]
    overlap = {"footings_m2": bo["footings_m2"][1], "beams_m2": bo["beams_m2"][1],
               "footing_beam_overlap_m2": bo["area_m2"][1], "strip_strip_m2": bo["strip_strip_m2"][1],
               "footing_footing_m2": bo["footing_footing_m2"][1], "placed_union_m2": bo["placed_union_m2"][1],
               "state": bo["state"], "matched": bo["matched"]}
    return rows, overlap, m4
