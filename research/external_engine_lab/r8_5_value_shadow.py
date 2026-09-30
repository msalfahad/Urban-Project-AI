"""R8.5 §15-§21, §26-§28 — VALUE-level shadow: canonical remeasurement where technically valid.

Research lab only. Reads current rows (never writes them) and produces canonical SHADOW quantities from
canonical source geometry (D1 -> K1 realised segments), the canonical frame (URBAN_FRAME_RELEASE_V3,
UNCONFIRMED declaration used only as a PREVIEW scale), the canonical CAD profile (V3: capability
signatures + source exceptions) and existing deterministic methods only. No status is raised to make a
value comparable; no project rule is ported.

  Qortuba   room floor areas and gross room perimeters re-derived from canonical segments: every room
            edge coordinate (QS01 cut line) must be carried by a canonical axis-parallel segment of the
            room within half the printed precision of the current input; widths, areas and the union
            perimeter are then recomputed from the canonical coordinates. The room decomposition and
            identity (which cells form which named room) are the QS01 method's, recorded as such.
  P7757     canonical status after the source exceptions are resolved; no current value exists and the
            height / identity / space inputs are not established -> VALUE_NOT_COMPUTABLE.
  Al Rashed unit context CONFLICT -> every physical value VALUE_NOT_COMPUTABLE. Native (unit-free)
            cross-check: the adapter's own deterministic room method run twice, on its own decode reading
            and on canonical K1 segments; differences are source-geometry differences.

    python3 research/external_engine_lab/r8_5_value_shadow.py <out_dir>
"""

from __future__ import annotations

import importlib.util
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

from shapely.geometry import box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from engine.source import cad_profile as P, decoder_pins as PINS, frame as FR          # noqa: E402
from engine.source import qualification as Q, region_candidates as RC                  # noqa: E402
from engine.source import source_exceptions as SX                                       # noqa: E402
from engine.source.cad import unit_evidence as UE                                       # noqa: E402

from r8_5_source_exceptions import Source                                               # noqa: E402

EXP = ROOT / "data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01"
QROWS = EXP / "pa08_qortuba_boq/APPROVED_QUANTITIES.json"
QS01 = EXP / "pa08_qortuba_qs01/QORTUBA_QS01_FLOOR_CALCULATIONS.json"
AROWS = EXP / "pa09_alrashed/ALRASHED_DETAILED_QUANTITY_EXPORT.json"
ATAKE = EXP / "pa09_alrashed/ALRASHED_FIRST_PLAN_AREA_TAKEOFF.json"
PROWS = EXP / "pa07r3/PA07_QUANTITY_SAFETY_REGISTER.json"
R84 = ROOT / "research/external_engine_lab/outputs/r8_4/SHADOW_ROW_DIFF.json"
ADAPTER = ROOT / "research/qs_wall_treatment_01/pa09/alrashed/geometry.py"
METHOD_ROOM = "URBAN_SHADOW_ROOM_FROM_CANONICAL_EDGES_V1"

VALUE_CLASSES = ("VALUE_EXACT_MATCH", "VALUE_WITHIN_NUMERIC_TOLERANCE", "VALUE_CHANGED_SOURCE_GEOMETRY",
                 "VALUE_CHANGED_FRAME", "VALUE_NOT_COMPUTABLE", "VALUE_METHOD_NOT_MIGRATED", "VALUE_SOURCE_BLOCKED",
                 "VALUE_TRADE_RULE_UNDECIDED")

# rows whose logic lives in project code the canonical path has not migrated (reason recorded per row)
NOT_MIGRATED = {
    "HIDDEN_SKIRTING": "opening-width deductions per wall line (QP-09) from the active opening register",
    "HIDDEN_PROFILE_ABOVE_SKIRTING": "same path as the skirting (QP-09, QP-11)",
    "WALL_CERAMIC_BATHROOMS": "door-area deduction from the active opening register (door widths)",
    "WALL_CERAMIC_SERVICE_ROOM": "door-area deduction from the active opening register",
    "BLOCKWORK_200": "masonry identity from the material band register (project classification)",
    "BLOCKWORK_150": "masonry identity from the material band register (project classification)",
    "INTERNAL_PLASTER": "door deductions and reveal logic (US-07 reveals per opening) from the active path",
    "WALL_PAINT": "door deductions and reveal logic from the active path",
    "TILE_PREPARATION_TARTUSHA": "door deductions from the active opening register",
    "ALUMINIUM_EXTERNAL_WINDOWS": "window widths from the active opening register",
    "PVC_INTERNAL_DOORS": "door widths from the active opening register",
}
TRADE_UNDECIDED = {"INTERNAL_GLAZED_OPENING": "trade classification pending (row status TRADE_CLASSIFICATION_PENDING)"}


def jl(p):
    return json.loads(Path(p).read_text())


def decimals(v):
    s = repr(float(v))
    return len(s.split(".")[1].rstrip("0")) if "." in s else 0


def compare(current, canonical):
    """(class, abs delta, rel delta). EXACT: equal at the current value's own printed precision.
    WITHIN_NUMERIC_TOLERANCE: within one unit of that precision (rounding / float accumulation)."""
    if canonical is None:
        return "VALUE_NOT_COMPUTABLE", None, None
    d = decimals(current)
    delta = canonical - current
    rel = delta / current if current else None
    if round(canonical, d) == round(current, d):
        return "VALUE_EXACT_MATCH", delta, rel
    if abs(delta) <= 10 ** (-d) + 1e-12:
        return "VALUE_WITHIN_NUMERIC_TOLERANCE", delta, rel
    return "VALUE_CHANGED_SOURCE_GEOMETRY", delta, rel


# ====================================================================== canonical evaluation context
def canonical_context(src: Source, cand, designation=None):
    ex = UE.extract(src.decode, src.src)
    uc = FR.unit_context(src.src, "MODEL_SPACE", FR.MODEL_SPACE, ex["evidence"],
                         insunits=src.decode.get("HEADER", {}).get("INSUNITS"), policy=FR.RELEASE_V3)
    if cand is None:
        rt = FR.region_transform(uc, "UNMAPPED", FR.MODEL_SPACE_UNKNOWN, policy=FR.RELEASE_V3)
    else:
        rt = FR.region_transform(uc, cand.candidate_id, cand.region_kind, bounds=cand.bounds, policy=FR.RELEASE_V3,
                                 reference=designation is not None, designation=designation)
    mf = FR.measurement_frame(uc, rt, policy=FR.RELEASE_V3)
    exc = src.classify(cand.candidate_id if cand else None, cand.bounds if cand else None)
    rfind = SX.region_findings(exc) + list(ex["findings"])
    sigs = Q.capability_signatures(src.doc)
    ctx = P.SourceValidationContext(True, PINS.decode_status(Q_sha(src.path)), PINS.PINS["LIBREDWG_DWGREAD"][0]["sha256"],
                                    tuple(f for f in src.doc.findings if f.obs_id is None), capability_signatures=sigs)
    res = P.evaluate("LINE", "REGION_REPRESENTATIVE", (), P.MeasurementMethod("SCALE_DEPENDENT", True), ctx, mf, uc, rt,
                     region_findings=rfind, parser_policy=P.PARSER_POLICY_V3)
    return {"unit": uc, "region": rt, "frame": mf, "profile": res, "release": P.region_release(res),
            "v_cad": P.v_cad_view(res, rfind), "signature_count": len(sigs),
            "blockers": [f"{r[0]}: {r[2][:140]}" for r in res.blocking]}


def Q_sha(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ====================================================================== Qortuba
def axis_lines(real, bounds, pad):
    """Canonical axis-parallel segments inside the region: {'V': [(x, lo, hi, obs, layer)], 'H': [...]}."""
    out = {"V": [], "H": []}
    x0, y0, x1, y1 = bounds
    for s in real.segments:
        (ax, ay), (bx, by) = s.a, s.b
        if not (x0 - pad <= min(ax, bx) and max(ax, bx) <= x1 + pad and y0 - pad <= min(ay, by) and max(ay, by) <= y1 + pad):
            continue
        if abs(bx - ax) < 1e-9 and abs(by - ay) > 1e-9:
            out["V"].append((ax, min(ay, by), max(ay, by), s.lineage.obs_id, s.lineage.layer))
        elif abs(by - ay) < 1e-9 and abs(bx - ax) > 1e-9:
            out["H"].append((ay, min(ax, bx), max(ax, bx), s.lineage.obs_id, s.lineage.layer))
    return out


def rederive(value_native, lines, span, tol):
    """Canonical coordinate for one current edge coordinate: segments on that line whose extent meets the
    room's span on the other axis."""
    lo, hi = span
    hits = [l for l in lines if abs(l[0] - value_native) <= tol and l[2] >= lo - tol and l[1] <= hi + tol]
    if not hits:
        return None, []
    return sum(h[0] for h in hits) / len(hits), hits


def qortuba(src: Source):
    rows = jl(QROWS)["ROWS"]
    rooms = jl(QS01)["ROWS"]
    cand = next(c for c in src.cands.values() if any("SECOND FLOOR PLAN" in e[2] for e in c.role_evidence))
    label = next(e for e in cand.role_evidence if "SECOND FLOOR PLAN" in e[2])
    ctx = canonical_context(src, cand)
    mm = ctx["frame"].mm_per_native or ctx["unit"].native_to_mm          # PREVIEW scale (declaration)
    lines = axis_lines(src.real, cand.bounds, 0.0)
    tol = 0.05 / mm            # current cut lines are printed to 0.1 mm: half the printed precision, in native
    canon_rooms, qty = {}, []
    for r in rooms:
        rects = r["RECTANGLES"]
        xs_cur, ys_cur = r["CUT_LINES_X_MM"], r["CUT_LINES_Y_MM"]
        span_x = (min(xs_cur) / mm, max(xs_cur) / mm)
        span_y = (min(ys_cur) / mm, max(ys_cur) / mm)
        cx, cy, obs, missing, resid = {}, {}, set(), [], []
        for X in xs_cur:
            v, hits = rederive(X / mm, lines["V"], span_y, tol)
            if v is None:
                missing.append(f"X={X}")
            else:
                cx[X] = v
                obs |= {h[3] for h in hits}
                resid.append(abs(v - X / mm) * mm)
        for Y in ys_cur:
            v, hits = rederive(Y / mm, lines["H"], span_x, tol)
            if v is None:
                missing.append(f"Y={Y}")
            else:
                cy[Y] = v
                obs |= {h[3] for h in hits}
                resid.append(abs(v - Y / mm) * mm)
        cur_poly = unary_union([box(q["X_MM"][0], q["Y_MM"][0], q["X_MM"][1], q["Y_MM"][1]) for q in rects])
        cur_perim = round(cur_poly.length / 1000.0, 4)
        rec = {"room_id": r["ROOM_ID"], "room": r["ROOM"], "wet_or_dry": r["WET_OR_DRY"],
               "current_area_m2": r["METHOD_A_CAD_POLYGON_AREA_M2"], "current_rectangles": rects,
               "current_perimeter_from_current_rectangles_m": cur_perim,
               "current_inputs": {"CUT_LINES_X_MM": xs_cur, "CUT_LINES_Y_MM": ys_cur},
               "canonical_inputs": None, "canonical_area_m2": None, "canonical_perimeter_m": None,
               "missing_edges": missing, "max_edge_residual_mm": round(max(resid), 6) if resid else None,
               "source_observation_ids": sorted(obs)}
        if not missing:
            crects = [(cx[q["X_MM"][0]], cy[q["Y_MM"][0]], cx[q["X_MM"][1]], cy[q["Y_MM"][1]]) for q in rects]
            area = sum((c[2] - c[0]) * (c[3] - c[1]) for c in crects) * mm * mm / 1e6
            perim = unary_union([box(*c) for c in crects]).length * mm / 1000.0
            rec.update(canonical_inputs={"CUT_LINES_X_NATIVE": [cx[X] for X in xs_cur],
                                         "CUT_LINES_Y_NATIVE": [cy[Y] for Y in ys_cur],
                                         "RECT_DIMS_MM": [[round((c[2] - c[0]) * mm, 4), round((c[3] - c[1]) * mm, 4)]
                                                          for c in crects], "MM_PER_NATIVE": mm},
                       canonical_area_m2=area, canonical_perimeter_m=perim,
                       canonical_formula=" + ".join(f"{(c[2] - c[0]) * mm / 1000:.4f} x {(c[3] - c[1]) * mm / 1000:.4f}"
                                                   for c in crects) + f" = {area:.4f} m2")
        canon_rooms[r["ROOM_ID"]] = rec
        qty.append({"quantity_id": f"CQ:QORTUBA:{r['ROOM_ID']}:AREA", "kind": "ROOM_FLOOR_AREA",
                    "source_observation_ids": sorted(obs), "geometry_ids": [r["ROOM_ID"]],
                    "frame_id": ctx["frame"].frame_id, "evidence_version": ctx["frame"].evidence_digest,
                    "method_id": METHOD_ROOM, "formula": rec.get("canonical_formula"),
                    "inputs": rec["canonical_inputs"], "value": rec["canonical_area_m2"], "unit": "m2",
                    "status": ctx["release"], "blockers": ctx["blockers"],
                    "room_identity_basis": "QS01 room decomposition and name (identity not re-derived)"})
        qty.append({"quantity_id": f"CQ:QORTUBA:{r['ROOM_ID']}:PERIMETER", "kind": "ROOM_GROSS_PERIMETER",
                    "source_observation_ids": sorted(obs), "geometry_ids": [r["ROOM_ID"]],
                    "frame_id": ctx["frame"].frame_id, "evidence_version": ctx["frame"].evidence_digest,
                    "method_id": METHOD_ROOM, "formula": "boundary length of the union of the canonical rectangles",
                    "inputs": rec["canonical_inputs"], "value": rec["canonical_perimeter_m"], "unit": "m",
                    "status": ctx["release"], "blockers": ctx["blockers"],
                    "room_identity_basis": "QS01 room decomposition and name (identity not re-derived)"})

    def match(name, value, field):
        pool = [c for c in canon_rooms.values() if c["room"] == name]
        return min(pool, key=lambda c: abs(c[field] - value)) if pool else None

    diffs = []
    for row in rows:
        item, cur = row["ITEM"], row["MEASURED_QUANTITY"]
        base = {"row_id": f"{row['SUBITEM']}|{item}", "current_status": row["STATUS"], "current_value": cur,
                "unit": row["MEASURED_UNIT"], "rules": row["RULE_ID"], "current_formula": row["FORMULA"]}
        f = row.get("FORMULA") or ""
        terms = re.findall(r"([A-Z][A-Z./ _a-z]*?)\s+(\d+\.?\d*)\s*(?=\+|=)", f)
        worded = re.match(r"the (?:(\w+) )?(\w+) floor polygons?, unchanged", f.strip(), re.I)
        if not terms and worded:
            # the row names its rooms in words ("the three bathroom floor polygons", "the PAINTRY floor polygon")
            count_word, what = worded.group(1), worded.group(2)
            name = "BATH" if what.lower() == "bathroom" else what.upper()
            pool = [c for c in canon_rooms.values() if c["room"] == name]
            n = {"one": 1, "two": 2, "three": 3, "four": 4}.get((count_word or "one").lower(), len(pool))
            if len(pool) == n:
                terms = [(c["room"], str(c["current_area_m2"])) for c in pool]
        if item in TRADE_UNDECIDED:
            diffs.append({**base, "value_class": "VALUE_TRADE_RULE_UNDECIDED", "reason": TRADE_UNDECIDED[item]})
            continue
        if cur is None:
            diffs.append({**base, "value_class": "VALUE_NOT_COMPUTABLE",
                          "reason": f"current row {row['STATUS']}: no quantity to compare"})
            continue
        if item in NOT_MIGRATED:
            chk = {}
            if item == "WALL_CERAMIC_BATHROOMS":
                chk["gross_perimeter_input_lm"] = 30.225
            diffs.append({**base, "value_class": "VALUE_METHOD_NOT_MIGRATED", "reason": NOT_MIGRATED[item]})
            continue
        m2 = row["MEASURED_UNIT"] == "M2"
        factor = re.search(r"x\s*(0\.\d+)\s*m\s*=", f)
        if factor and "derived from" in (row.get("SOURCE") or ""):
            parent = re.search(r"derived from (Q-\S+)", row["SOURCE"]).group(1)
            prow = next(p for p in rows if p["SUBITEM"] == parent)
            pterms = re.findall(r"([A-Z][A-Z./ _a-z]*?)\s+(\d+\.?\d*)\s*(?=\+|=)", prow["FORMULA"])
            used = [match(n.strip(), float(v), "current_perimeter_from_current_rectangles_m") for n, v in pterms]
            parent_diff = next((x for x in diffs if x["row_id"].startswith(parent + "|")), None)
            if parent_diff and parent_diff["value_class"] == "VALUE_METHOD_NOT_MIGRATED":
                diffs.append({**base, "value_class": "VALUE_METHOD_NOT_MIGRATED",
                              "reason": f"derived from {parent}, whose method is not migrated"})
                continue
            if any(u is None or u["canonical_perimeter_m"] is None for u in used):
                diffs.append({**base, "value_class": "VALUE_NOT_COMPUTABLE", "reason": "a parent room edge is not canonical"})
                continue
            k = float(factor.group(1))
            canon = sum(u["canonical_perimeter_m"] for u in used) * k
            cls, d, rel = compare(cur, canon)
            diffs.append({**base, "value_class": cls, "canonical_preview_value": canon, "abs_delta": d, "rel_delta": rel,
                          "canonical_inputs": {"rooms": [u["room_id"] for u in used], "factor_m": k,
                                               "factor_basis": row["RULE_ID"]},
                          "current_inputs": {"parent_row": parent, "factor_m": k},
                          "cause": "rounding only" if cls != "VALUE_EXACT_MATCH" else "none"})
            continue
        field_cur = "current_area_m2" if m2 else "current_perimeter_from_current_rectangles_m"
        field_can = "canonical_area_m2" if m2 else "canonical_perimeter_m"
        used = [(n.strip(), float(v), match(n.strip(), float(v), field_cur)) for n, v in terms]
        if not used or any(u[2] is None for u in used):
            diffs.append({**base, "value_class": "VALUE_METHOD_NOT_MIGRATED",
                          "reason": "row formula does not name QS01 rooms; not a room area / perimeter row"})
            continue
        if any(u[2][field_can] is None for u in used):
            diffs.append({**base, "value_class": "VALUE_NOT_COMPUTABLE",
                          "reason": "room edge not carried by canonical geometry: " +
                                    "; ".join(",".join(u[2]["missing_edges"]) for u in used if u[2]["missing_edges"])})
            continue
        method_check = [(n, v, u[field_cur]) for n, v, u in used if round(u[field_cur], decimals(v)) != round(v, decimals(v))]
        if method_check:
            # the canonical method does not reproduce the current value FROM THE CURRENT INPUTS: the difference
            # would be a method difference, not a source-geometry one -> not remeasured
            canon = sum(u[2][field_can] for u in used)
            diffs.append({**base, "value_class": "VALUE_METHOD_NOT_MIGRATED",
                          "reason": ("current per-room values are not the clear-polygon perimeter even on the current "
                                     "rectangles: the current 'gross wall line' sums classified wall-boundary segments "
                                     "(open / glazed edges excluded) from the active seal register"),
                          "method_reproduction_mismatch": [{"room": n, "current_row_value": v,
                                                             "clear_polygon_value_on_current_rectangles": c}
                                                            for n, v, c in method_check],
                          "canonical_clear_polygon_value_not_used": canon})
            continue
        canon = sum(u[2][field_can] for u in used)
        cls, d, rel = compare(cur, canon)
        diffs.append({**base, "value_class": cls, "canonical_preview_value": canon, "abs_delta": d, "rel_delta": rel,
                      "current_inputs": [{"room": n, "value": v} for n, v, _ in used],
                      "canonical_inputs": [{"room_id": u["room_id"], "room": n, "value": u[field_can],
                                            "max_edge_residual_mm": u["max_edge_residual_mm"]} for n, _, u in used],
                      "method_reproduction_mismatch": method_check,
                      "cause": ("none" if cls == "VALUE_EXACT_MATCH" else
                                "sub-precision rounding of 0.1 mm-printed current edges" if cls ==
                                "VALUE_WITHIN_NUMERIC_TOLERANCE" else "canonical edge coordinates differ")})
    designation = {"label_detected": {"handle": label[1], "literal": label[2], "candidate": cand.candidate_id},
                   "designation": FR.ReferenceRegionDesignation(
                       f"DES:QORTUBA:{cand.candidate_id}", src.src, "MODEL_SPACE", cand.candidate_id,
                       FR.SOURCE_PLAN_LABEL, f"TEXT handle {label[1]} {label[2]!r}", FR.ENGINE, "PENDING_REVIEW",
                       notes="label detected by the role parser; acceptance is a review act, not a parser output").as_dict(),
                   "accepted": False,
                   "effect_if_accepted": None}
    acc = FR.ReferenceRegionDesignation(f"DES:QORTUBA:{cand.candidate_id}", src.src, "MODEL_SPACE", cand.candidate_id,
                                        FR.SOURCE_PLAN_LABEL, f"TEXT handle {label[1]}", FR.ENGINE, FR.ACCEPTED)
    what_if = canonical_context(src, cand, acc)
    designation["effect_if_accepted"] = {"region": what_if["region"].status, "frame": what_if["frame"].status,
                                         "release": what_if["release"]}
    return {"context": ctx, "rooms": list(canon_rooms.values()), "quantities": qty, "diffs": diffs,
            "designation_review": designation}


# ====================================================================== P7757
def p7757(src: Source):
    rows = jl(PROWS)["ROWS"]
    r84 = {r["row_id"]: r for r in jl(R84)["projects"]["P7757"]["rows"]}
    cache, out = {}, []
    for row in rows:
        prev = r84.get(row["SAFETY_ID"], {})
        cid = prev.get("region_candidate")
        role = prev.get("region_role_candidate")
        if cid not in cache:
            cand = src.cands.get(cid)
            if cand is not None and role == RC.PLAN and cand.role_candidate == RC.UNKNOWN:
                cand = RC.RegionCandidate(cand.candidate_id, cand.coordinate_space_id, cand.bounds, RC.PLAN,
                                          cand.role_evidence, cand.scale_notes, cand.sample_count,
                                          notes="PLAN from the active-path view-role hint (candidate only)")
            cache[cid] = canonical_context(src, cand)
        c = cache[cid]
        out.append({"row_id": row["SAFETY_ID"], "current_status": row["QUANTITY_STATUS"], "current_value": None,
                    "region_candidate": cid, "region_role_candidate": role,
                    "r8_4_eligibility": prev.get("eligibility"),
                    "r8_4_sensitivity_eligibility": prev.get("eligibility_if_unplaceable_unrealised_excluded"),
                    "canonical_eligibility": c["release"], "V-CAD-5": c["v_cad"]["V-CAD-5"],
                    "value_class": "VALUE_NOT_COMPUTABLE",
                    "reason": "no current value; active-path inputs not established: " + ", ".join(sorted(row["BLOCKED_BY"])),
                    "canonical_blockers": c["blockers"]})
    return {"rows": out, "regions": {k: {"release": v["release"], "V-CAD-5": v["v_cad"]["V-CAD-5"],
                                         "region": v["region"].status, "frame": v["frame"].status,
                                         "blockers": v["blockers"]} for k, v in cache.items()}}


# ====================================================================== Al Rashed
def adapter_module():
    spec = importlib.util.spec_from_file_location("alrashed_geometry_readonly", ADAPTER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def canonical_barriers(real, layers, window, tol, lineage_out=None):
    x0, x1, y0, y1 = window
    out = []
    for s in real.segments:
        if s.lineage.layer not in layers:
            continue
        (ax, ay), (bx, by) = s.a, s.b
        if not (x0 <= ax <= x1 and y0 <= ay <= y1 and x0 <= bx <= x1 and y0 <= by <= y1):
            continue
        dx, dy = bx - ax, by - ay
        if abs(dx) < tol and abs(dy) < tol:
            continue
        if abs(dx) < tol:
            out.append(("V", ax, min(ay, by), max(ay, by)))
        elif abs(dy) < tol:
            out.append(("H", ay, min(ax, bx), max(ax, bx)))
        else:
            continue
        if lineage_out is not None:
            k = out[-1]
            lineage_out[(k[0], round(k[1], 6), round(k[2], 6), round(k[3], 6))] = (s.lineage, s.a, s.b)
    return out


def closing_edge(doc, lineage, a, b):
    """True when the canonical segment is the closing edge (last vertex -> first) of a closed LWPOLYLINE."""
    obs = next((o for o in doc.entities if o.obs_id == lineage.obs_id), None)
    if obs is None or obs.kind != "LWPOLYLINE" or not getattr(obs.geometry, "closed", False):
        return False
    v = obs.geometry.vertices
    ends = {tuple(round(c, 6) for c in v[0][:2]), tuple(round(c, 6) for c in v[-1][:2])}
    return {tuple(round(c, 6) for c in a), tuple(round(c, 6) for c in b)} == ends


def alrashed(src: Source):
    G = adapter_module()
    import os
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        ents = G.load()
    finally:
        os.chdir(cwd)
    floors = {}
    for floor, win in G.WINDOWS.items():
        g_own = G.grid(ents, win)
        lin = {}
        walls = canonical_barriers(src.real, set(G.WALL_LAYERS), win, G.TOL, lin)
        cols = canonical_barriers(src.real, set(G.COLUMN_LAYERS), win, G.TOL, lin)
        clos = G.closures(walls)
        bars = walls + cols + clos
        xs = G._snap([s[1] for s in bars if s[0] == "V"], G.SNAP_MM / 1000.0)
        ys = G._snap([s[1] for s in bars if s[0] == "H"], G.SNAP_MM / 1000.0)
        g_can = {"XS": xs, "YS": ys, "BARRIERS": bars, "WALLS": walls, "COLUMNS": cols, "CLOSURES": clos, "WINDOW": win}
        r_own = {tuple(round(v, 4) for v in c["BBOX"]): c for c in G.rooms(g_own)}
        r_can = {tuple(round(v, 4) for v in c["BBOX"]): c for c in G.rooms(g_can)}
        seg_own = Counter((s[0], round(s[1], 6), round(s[2], 6), round(s[3], 6)) for s in g_own["WALLS"] + g_own["COLUMNS"])
        seg_can = Counter((s[0], round(s[1], 6), round(s[2], 6), round(s[3], 6)) for s in walls + cols)
        only_can = seg_can - seg_own
        attributed = Counter()
        for k in only_can.elements():
            l, a, b = lin.get(k, (None, None, None))
            attributed["CLOSING_EDGE_OF_CLOSED_LWPOLYLINE:" + (l.layer if l else "?")
                       if l and closing_edge(src.doc, l, a, b) else "OTHER"] += 1
        both = set(r_own) & set(r_can)
        area_diff = [k for k in both if abs(r_own[k]["AREA_M2"] - r_can[k]["AREA_M2"]) > 1e-9]
        floors[floor] = {
            "window_native": win,
            "segments": {"adapter_reading": sum(seg_own.values()), "canonical_k1": sum(seg_can.values()),
                         "only_adapter": sum((seg_own - seg_can).values()), "only_canonical": sum((seg_can - seg_own).values()),
                         "examples_only_adapter": [list(k) for k in list((seg_own - seg_can))[:5]],
                         "examples_only_canonical": [list(k) for k in list((seg_can - seg_own))[:5]],
                         "only_canonical_attribution": dict(attributed),
                         "cause": ("the adapter reads the LWPOLYLINE closed flag as `flag & 1`; the decode marks closed "
                                   "polylines with bit 512, so the adapter drops each closing edge")},
            "rooms": {"adapter_reading": len(r_own), "canonical_k1": len(r_can), "same_bbox": len(both),
                      "same_bbox_same_native_area": len(both) - len(area_diff),
                      "only_adapter": len(set(r_own) - set(r_can)), "only_canonical": len(set(r_can) - set(r_own)),
                      "native_area_adapter_total": round(sum(c["AREA_M2"] for c in r_own.values()), 4),
                      "native_area_canonical_total": round(sum(c["AREA_M2"] for c in r_can.values()), 4)},
            "_own": r_own, "_can": r_can}
    take = jl(ATAKE)
    room_native = []
    for fl in take["FLOORS"]:
        f = floors.get(fl["FLOOR"])
        for rm in fl.get("ROOMS", []):
            if f is None:
                room_native.append({"room_ref": rm["ROOM_REF"], "floor": fl["FLOOR"], "native_check": "NO_ADAPTER_WINDOW"})
                continue
            key_own = next((k for k, c in f["_own"].items() if abs(c["AREA_M2"] - rm["AREA_M2"]) < 1e-4
                            and abs(c["WIDTH_M"] - rm["WIDTH_M"]) < 1e-4 and abs(c["DEPTH_M"] - rm["DEPTH_M"]) < 1e-4), None)
            can = f["_can"].get(key_own) if key_own else None
            room_native.append({"room_ref": rm["ROOM_REF"], "floor": fl["FLOOR"], "current_native_area": rm["AREA_M2"],
                                "reproduced_by_adapter_reading": key_own is not None,
                                "canonical_native_area": can["AREA_M2"] if can else None,
                                "native_check": ("SAME_NATIVE_AREA" if can and abs(can["AREA_M2"] - rm["AREA_M2"]) < 1e-9 else
                                                 "CHANGED_NATIVE_AREA" if can else
                                                 "CHANGED_NATIVE_TOPOLOGY" if key_own else "NOT_REPRODUCED"),
                                "native_delta": (can["AREA_M2"] - rm["AREA_M2"]) if can else None})
    for f in floors.values():
        f.pop("_own")
        f.pop("_can")
    rows = jl(AROWS)["RECORDS"]
    ctx = canonical_context(src, None)
    by_ref = {r["room_ref"]: r for r in room_native}
    out = []
    for i, r in enumerate(rows):
        nat = by_ref.get(r.get("COMPONENT_REF"))
        out.append({"row_id": f"{r.get('ITEM_CODE')}|{r.get('COMPONENT_REF')}|{r.get('TRADE')}|{i}",
                    "current_status": r["STATUS"], "current_value": r["MEASURED_QUANTITY"], "unit": r["MEASURED_UNIT"],
                    "value_class": "VALUE_NOT_COMPUTABLE",
                    "reason": "UNIT_CONTEXT CONFLICT (INSUNITS inch vs candidate display families); no unit authority",
                    "native_geometry_check": nat["native_check"] if nat else "NO_NATIVE_ROOM_FACT",
                    "native_area_current": nat.get("current_native_area") if nat else None,
                    "native_area_canonical": nat.get("canonical_native_area") if nat else None})
    return {"floors": floors, "rooms": room_native, "rows": out, "unit": ctx["unit"].status,
            "frame": ctx["frame"].status, "column_trade_deduction": "UNDECIDED (kept)"}


def main(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    qs = qortuba(Source("QORTUBA"))
    pv = p7757(Source("P7757"))
    ar = alrashed(Source("ALRASHED"))
    qc = qs.pop("context")
    diff = {"SCHEMA": "URBAN_R8_5_SHADOW_VALUE_DIFF_V1", "value_classes": list(VALUE_CLASSES), "outputs_modified": False,
            "QORTUBA": {"rows": qs["diffs"], "summary": dict(Counter(d["value_class"] for d in qs["diffs"])),
                        "rooms": qs["rooms"]},
            "P7757": {"rows": pv["rows"], "summary": dict(Counter(d["value_class"] for d in pv["rows"])),
                      "eligibility": dict(Counter(d["canonical_eligibility"] for d in pv["rows"])), "regions": pv["regions"]},
            "ALRASHED": {"rows": ar["rows"], "summary": dict(Counter(d["value_class"] for d in ar["rows"])),
                         "native_checks": dict(Counter(d["native_geometry_check"] for d in ar["rows"])),
                         "floors": ar["floors"], "rooms": ar["rooms"]}}
    quantities = {"SCHEMA": "URBAN_R8_5_CANONICAL_SHADOW_QUANTITIES_V1", "rule": "no naked quantity: every value "
                  "carries observation ids, geometry ids, frame id, evidence version, method, formula, inputs, unit, "
                  "status and blockers", "QORTUBA": qs["quantities"]}
    status = {"SCHEMA": "URBAN_R8_5_REAL_PROJECT_STATUS_V1", "policies": {
        "frame": FR.DEFAULT_POLICY.policy_id, "cad_profile": P.DEFAULT_CAD_PROFILE.profile_id,
        "parser": P.DEFAULT_PARSER_POLICY.policy_id},
        "QORTUBA": {"unit": qc["unit"].status, "region": qc["region"].status, "frame": qc["frame"].status,
                    "release": qc["release"], "V-CAD-5": qc["v_cad"]["V-CAD-5"], "blockers": qc["blockers"],
                    "capability_signatures": qc["signature_count"], "designation_review": qs["designation_review"]},
        "P7757": {"regions": pv["regions"]},
        "ALRASHED": {"unit": ar["unit"], "frame": ar["frame"], "column_trade_deduction": ar["column_trade_deduction"]}}
    for fn, obj in (("SHADOW_VALUE_DIFF.json", diff), ("CANONICAL_SHADOW_QUANTITIES.json", quantities),
                    ("REAL_PROJECT_R8_5_STATUS.json", status)):
        (out_dir / fn).write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str))
    print("QORTUBA", diff["QORTUBA"]["summary"])
    print("P7757", diff["P7757"]["summary"], diff["P7757"]["eligibility"])
    print("ALRASHED", diff["ALRASHED"]["summary"], diff["ALRASHED"]["native_checks"])
    print({k: v["rooms"] for k, v in ar["floors"].items()})
    print({k: v["segments"]["only_adapter"] for k, v in ar["floors"].items()},
          {k: v["segments"]["only_canonical"] for k, v in ar["floors"].items()})


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "research/external_engine_lab/outputs/r8_5")
