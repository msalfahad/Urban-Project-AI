"""STRUCTURAL N10 (Phase N10) - formwork contact faces, excavation footprints and a reinforcement audit, read from the
route G concrete register (the PROVISIONAL / UNRESOLVED register rows of tools/urban_boq_m2.py: one row per item, its
FAMILY, STOREY, CATEGORY and DIMENSIONS). Generic, stdlib only; it never changes a concrete or steel quantity.

    formwork(rows)                 -> the faces of every concrete element that a form would shape
    excavation(rows, facts)        -> the footprint of every footing pit and ground-beam trench; the volume only with
                                      the excavation depth (or levels) and the working space stated
    rebar_audit(rows, method_cfg)  -> how each reinforcement row was derived (count x length x d^2/162, a physical-
                                      bar model COUNT_X_LENGTH, a RATIO, or UNSTATED - an unresolved row), the unit
                                      mass against d^2/162, and any ratio labelled as a measured quantity

Faces (UP-FW-001, draft) - geometry only; what a contract measures as formwork is an owner decision:
    SLABS (structural)   SOFFIT = the slab's face area (members' overlap already deducted): MEASURED; EDGES (free
                         edges x t) are not in the register: HELD. A ground slab (GROUND_SLAB, on grade) has no
                         soffit form; its edges are HELD.
    BEAMS                SOFFIT = the net plan (width x clear length, columns and junctions out): MEASURED;
                         SIDES = 2 x net length x the depth below the slab: CONDITIONAL on how the schedule depth
                         reads (BELOW_SLAB: depth; TOTAL: depth - the storey's slab thickness) - route G's own
                         BEAM_DEPTH_CONVENTION; an edge beam's outer face over the slab thickness is a slab EDGE.
    COLUMNS              SIDES = perimeter x (storey height - the storey's slab thickness): UPPER_BOUND (the faces
                         covered by framing beams are not deducted: the register does not say which beams frame in).
    FOOTINGS, GROUND_BEAMS  SIDES = perimeter x depth (2 x clear length x depth): CONDITIONAL on FORMED / EARTH_CAST
                         (sides cast against the excavation take no form); the base sits on blinding: no form.
    anything else        (necks without a height, stairs, lintels, blinding, unresolved rows): HELD with the reason.
CONDITIONAL alternatives are reported side by side and never summed; HELD is never zero.

Excavation (UP-EXC-001, draft): a pit per footing (L + 2 ws) x (W + 2 ws), a trench per ground beam clear length x
(width + 2 ws); volume = plan x depth only when the depth (or NGL and founding level) and the working space ws are
stated facts (excavation.depth_m / excavation.ngl_m + excavation.founding_level_m, excavation.working_space_m). Pit
positions are not in the register, so overlapping pits are not merged: a stated volume is an upper bound for
neighbouring pits. Backfill is held (it needs the buried concrete below ground level, necks included).
"""

from __future__ import annotations

import json
import math
from collections import defaultdict

POLICY_ID = "STRUCT_N10_FORMWORK_EXCAVATION_V1"
MEASURED, CONDITIONAL, UPPER_BOUND, HELD = "MEASURED", "CONDITIONAL", "UPPER_BOUND", "HELD"
DECISIONS = {
    "FW-D1": {"question": "footing and ground-beam sides: formed (formwork measured) or cast against the excavation "
                          "(no formwork)?", "alternatives": ["FORMED", "EARTH_CAST"]},
    "FW-D2": {"question": "beam schedule depth: below the slab, or total depth including the slab (route G "
                          "BEAM_DEPTH_CONVENTION)?", "alternatives": ["BELOW_SLAB", "TOTAL"]},
    "FW-D3": {"question": "column faces covered by framing beams: which beams frame into each column (structural "
                          "plan adjacency) - until then the column sides are an upper bound", "alternatives": []},
    "FW-D4": {"question": "slab free edges (building perimeter, openings): edge length per slab", "alternatives": []},
    "EX-D1": {"question": "excavation working space beyond the footing / ground-beam faces (per side)",
              "alternatives": []},
    "EX-D2": {"question": "excavation depth: natural ground level and founding level (bottom of blinding)",
              "alternatives": []},
}
DIAMETERS_MM = (6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32)
STEEL_DENSITY_KG_M3 = 7850.0          # the reference for the d^2/162 comparison only (never used for a quantity)


def _dims(row):
    d = row.get("DIMENSIONS") or row.get("dimensions") or {}
    if isinstance(d, str):
        try:
            d = json.loads(d) if d.strip() else {}
        except ValueError:
            d = {}
    return d if isinstance(d, dict) else {}


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _key(row):
    return {"component_id": row.get("COMPONENT_ID"), "family": row.get("FAMILY"), "storey": row.get("STOREY"),
            "item_id": row.get("ITEM_ID"), "category": row.get("CATEGORY")}


def concrete_rows(rows):
    """the concrete rows of a register, one per component (the first PROVISIONAL row wins over an UNRESOLVED one)."""
    out = {}
    for r in rows:
        if r.get("TRADE") != "CONCRETE":
            continue
        cid = r.get("COMPONENT_ID")
        if cid not in out or (out[cid].get("CATEGORY") == "UNRESOLVED" and r.get("CATEGORY") != "UNRESOLVED"):
            out[cid] = r
    return [out[k] for k in sorted(out)]


def slab_thickness(rows):
    """{storey: (t_min, t_max)} from the structural slab rows."""
    ts = defaultdict(set)
    for r in concrete_rows(rows):
        d = _dims(r)
        if r.get("FAMILY") == "SLABS" and _f(d.get("t_m")) and d.get("region", "STRUCTURAL_SLAB") != "GROUND_SLAB":
            ts[r.get("STOREY")].add(round(_f(d["t_m"]), 4))
    return {k: (min(v), max(v)) for k, v in ts.items()}


def _face(row, face, state, area=None, alternatives=None, formula="", why=None, decision=None):
    rec = dict(_key(row), face=face, state=state, formula=formula)
    if area is not None:
        rec["area_m2"] = round(area, 6)
    if alternatives is not None:
        rec["alternatives_m2"] = {k: round(v, 6) for k, v in alternatives.items()}
    if why:
        rec["why"] = why
    if decision:
        rec["decision"] = decision
    return rec


def element_faces(row, slab_t):
    """the faces of one concrete register row (see the module text). slab_t: slab_thickness()."""
    fam, d = row.get("FAMILY"), _dims(row)
    if row.get("CATEGORY") == "UNRESOLVED":
        return [_face(row, "ALL", HELD, why=f"UNRESOLVED_CONCRETE: {row.get('BLOCKER') or 'no quantity'}")]
    t = slab_t.get(row.get("STOREY"))
    if fam == "GROUND_SLAB":
        return [_face(row, "SOFFIT", MEASURED, area=0.0, formula="a slab on grade has no soffit form"),
                _face(row, "EDGES", HELD, why="SLAB_EDGES_NOT_IN_THE_REGISTER", decision="FW-D4")]
    if fam == "SLABS":
        A, region = _f(d.get("area_m2")), d.get("region", "STRUCTURAL_SLAB")
        if region == "GROUND_SLAB":
            return [_face(row, "SOFFIT", MEASURED, area=0.0, formula="a slab on grade has no soffit form"),
                    _face(row, "EDGES", HELD, why="SLAB_EDGES_NOT_IN_THE_REGISTER", decision="FW-D4")]
        if A is None:
            return [_face(row, "ALL", HELD, why="SLAB_AREA_NOT_IN_THE_REGISTER")]
        return [_face(row, "SOFFIT", MEASURED, area=A, formula="slab face area (members' overlap deducted)"),
                _face(row, "EDGES", HELD, why="SLAB_EDGES_NOT_IN_THE_REGISTER: the free edges (perimeter, openings) "
                                              "x t", decision="FW-D4")]
    if fam in ("BEAMS", "CONTINUOUS_BEAM") or (fam not in ("GROUND_BEAMS",) and
                                               {"width_m", "depth_m", "net_plan_m2"} <= set(d)):
        b, h, plan = _f(d.get("width_m")), _f(d.get("depth_m")), _f(d.get("net_plan_m2"))
        if not (b and h and plan):
            return [_face(row, "ALL", HELD, why="BEAM_SECTION_OR_PLAN_NOT_IN_THE_REGISTER")]
        L = plan / b
        out = [_face(row, "SOFFIT", MEASURED, area=plan, formula="net plan (width x clear length, columns and "
                                                                    "junctions out)")]
        if t is None:
            out.append(_face(row, "SIDES", CONDITIONAL, alternatives={"BELOW_SLAB": 2 * L * h},
                             formula="2 x net length x depth below the slab", decision="FW-D2",
                             why="NO_SLAB_THICKNESS_ON_THE_STOREY: the TOTAL reading cannot be evaluated"))
        else:
            alt = {"BELOW_SLAB": 2 * L * h, "TOTAL_MIN": 2 * L * max(0.0, h - t[1]),
                   "TOTAL_MAX": 2 * L * max(0.0, h - t[0])} if t[0] != t[1] else \
                {"BELOW_SLAB": 2 * L * h, "TOTAL": 2 * L * max(0.0, h - t[0])}
            out.append(_face(row, "SIDES", CONDITIONAL, alternatives=alt, decision="FW-D2",
                             formula="2 x net length x (depth | depth - slab thickness)"))
        return out
    if fam == "COLUMNS":
        sec, H = d.get("section_m") or [], _f(d.get("height_m"))
        a, c = (_f(sec[0]), _f(sec[1])) if len(sec) == 2 else (None, None)
        if not (a and c):
            return [_face(row, "ALL", HELD, why="COLUMN_SECTION_NOT_IN_THE_REGISTER")]
        if H is None:
            return [_face(row, "SIDES", HELD, why="COLUMN_HEIGHT_NOT_IN_THE_REGISTER (a neck: footing top to neck top)")]
        if t is None:
            return [_face(row, "SIDES", HELD, why="NO_SLAB_THICKNESS_ON_THE_STOREY: the height to the soffit is not "
                                                  "known", decision="FW-D3")]
        return [_face(row, "SIDES", UPPER_BOUND, area=2 * (a + c) * max(0.0, H - t[0]), decision="FW-D3",
                      formula="perimeter x (storey height - slab thickness); framing beams' faces not deducted")]
    if fam == "FOOTINGS":
        s = d.get("schedule_m") or []
        L, W, D = (_f(s[0]), _f(s[1]), _f(s[2])) if len(s) == 3 else (None, None, None)
        if not (L and W and D):
            return [_face(row, "ALL", HELD, why="FOOTING_L_W_D_NOT_IN_THE_REGISTER")]
        return [_face(row, "SIDES", CONDITIONAL, alternatives={"FORMED": 2 * (L + W) * D, "EARTH_CAST": 0.0},
                      formula="2 x (L + W) x D", decision="FW-D1"),
                _face(row, "BASE", MEASURED, area=0.0, formula="on blinding: no form")]
    if fam == "GROUND_BEAMS":
        b, h, L = _f(d.get("width_m")), _f(d.get("depth_m")), _f(d.get("clear_length_m"))
        if not (b and h and L):
            return [_face(row, "ALL", HELD, why="GROUND_BEAM_SECTION_OR_LENGTH_NOT_IN_THE_REGISTER")]
        return [_face(row, "SIDES", CONDITIONAL, alternatives={"FORMED": 2 * L * h, "EARTH_CAST": 0.0},
                      formula="2 x clear length x depth", decision="FW-D1"),
                _face(row, "BASE", MEASURED, area=0.0, formula="on blinding: no form")]
    return [_face(row, "ALL", HELD, why=f"NO_FACE_RULE_FOR_{fam}")]


def formwork(rows):
    """-> {"policy", "faces", "totals": {family: {face: {"state", "area_m2" | "alternatives_m2", "rows"}}},
    "held": {family: count}, "decisions", "never"}"""
    slab_t = slab_thickness(rows)
    faces = [f for r in concrete_rows(rows) for f in element_faces(r, slab_t)]
    tot = defaultdict(lambda: defaultdict(lambda: {"state": None, "rows": 0}))
    held = defaultdict(int)
    for f in faces:
        if f["state"] == HELD:
            held[f["family"]] += 1
            continue
        t = tot[f["family"]][f["face"]]
        t["rows"] += 1
        t["state"] = f["state"] if t["state"] in (None, f["state"]) else "MIXED"
        if "area_m2" in f:
            t["area_m2"] = round(t.get("area_m2", 0.0) + f["area_m2"], 6)
        for k, v in (f.get("alternatives_m2") or {}).items():
            t.setdefault("alternatives_m2", {})
            t["alternatives_m2"][k] = round(t["alternatives_m2"].get(k, 0.0) + v, 6)
    return {"policy": POLICY_ID, "faces": faces,
            "totals": {k: {kk: dict(vv) for kk, vv in sorted(v.items())} for k, v in sorted(tot.items())},
            "held": dict(sorted(held.items())), "slab_thickness_m": {k: list(v) for k, v in sorted(slab_t.items())},
            "decisions": {k: v for k, v in DECISIONS.items() if k.startswith("FW")},
            "never": ["a conditional alternative summed with another", "a held face counted as zero",
                      "a formwork convention chosen without the owner"]}


def _fact(facts, key):
    v = ((facts or {}).get("excavation") or {}).get(key)
    return v if isinstance(v, dict) and v.get("value_m") is not None else None


def excavation(rows, facts=None):
    """-> {"policy", "pits": [...], "footprint_m2", "plan_m2", "state", "volume_m3" | None, "backfill", "why"}"""
    ws, dep = _fact(facts, "working_space_m"), _fact(facts, "depth_m")
    ngl, fnd = _fact(facts, "ngl_m"), _fact(facts, "founding_level_m")
    depth = dep["value_m"] if dep else (ngl["value_m"] - fnd["value_m"] if ngl and fnd else None)
    w = ws["value_m"] if ws else None
    pits, held = [], []
    for r in concrete_rows(rows):
        d = _dims(r)
        if r.get("FAMILY") == "FOOTINGS" and r.get("CATEGORY") != "UNRESOLVED":
            s = d.get("schedule_m") or []
            L, W = (_f(s[0]), _f(s[1])) if len(s) == 3 else (None, None)
            if not (L and W):
                held.append(dict(_key(r), why="FOOTING_L_W_NOT_IN_THE_REGISTER"))
                continue
            pits.append(dict(_key(r), kind="PIT", footprint_m2=round(L * W, 6),
                             plan_m2=round((L + 2 * w) * (W + 2 * w), 6) if w is not None else None))
        elif r.get("FAMILY") == "GROUND_BEAMS" and r.get("CATEGORY") != "UNRESOLVED":
            b, L = _f(d.get("width_m")), _f(d.get("clear_length_m"))
            if not (b and L):
                held.append(dict(_key(r), why="GROUND_BEAM_WIDTH_OR_LENGTH_NOT_IN_THE_REGISTER"))
                continue
            pits.append(dict(_key(r), kind="TRENCH", footprint_m2=round(L * b, 6),
                             plan_m2=round(L * (b + 2 * w), 6) if w is not None else None))
    foot = sum(p["footprint_m2"] for p in pits)
    miss = ([] if w is not None else ["the working space (excavation.working_space_m)"]) + \
        ([] if depth is not None else ["the excavation depth (excavation.depth_m, or ngl_m and founding_level_m)"])
    out = {"policy": POLICY_ID, "pits": pits, "held": held, "footprint_m2": round(foot, 6),
           "decisions": {k: v for k, v in DECISIONS.items() if k.startswith("EX")},
           "sources": {k: v for k, v in (("working_space_m", ws), ("depth_m", dep), ("ngl_m", ngl),
                                         ("founding_level_m", fnd)) if v}}
    if miss:
        out.update(state=HELD, volume_m3=None, plan_m2=None, why="EXCAVATION_VOLUME_HELD: " + "; ".join(miss))
    else:
        plan = sum(p["plan_m2"] for p in pits)
        out.update(state=UPPER_BOUND if len(pits) > 1 else MEASURED, plan_m2=round(plan, 6),
                   depth_m=depth, volume_m3=round(plan * depth, 6),
                   why="pit positions are not in the register: overlapping neighbouring pits are not merged"
                   if len(pits) > 1 else None)
    out["backfill"] = {"state": HELD, "why": "BACKFILL_HELD: excavation - the buried concrete below ground level "
                                             "(footings, necks to ground level, ground beams, blinding) - the neck "
                                             "heights and ground level are not in the register"}
    return out


def _derivation(row):
    f = (row.get("FORMULA") or "").lower()
    if "kg/m3" in f or "ratio" in f or "kg per m3" in f:
        return "RATIO"
    if "d^2/162" in f or "d2/162" in f:
        return "D2_OVER_162"
    if any(w in f for w in ("count x", "links", " bars", "x clear span", "x span")):
        return "COUNT_X_LENGTH"                   # a physical-bar model (the unit mass is the project's method)
    return "UNSTATED"


def rebar_audit(rows, method_cfg=None):
    """-> {"policy", "unit_mass": [{d_mm, d2_over_162, method_kg_m, exact_7850, deviation_pct}], "rows": {derivation:
    count}, "kg": {family: {derivation: kg}}, "violations": [...]}"""
    from engine.source import rebar_unit_mass as RM
    cfg = method_cfg or {"method": RM.D2_OVER_162}
    table = []
    for d in DIAMETERS_MM:
        a = d * d / 162.0
        m = RM.kg_per_m(d, cfg)
        ex = math.pi / 4.0 * (d / 1000.0) ** 2 * STEEL_DENSITY_KG_M3
        table.append({"d_mm": d, "d2_over_162": round(a, 6), "method_kg_m": round(m, 6), "exact_7850": round(ex, 6),
                      "method_vs_d2_162_pct": round(100 * (m - a) / a, 4),
                      "d2_162_vs_exact_pct": round(100 * (a - ex) / ex, 4)})
    counts, kg, bad = defaultdict(int), defaultdict(lambda: defaultdict(float)), []
    for r in rows:
        if r.get("TRADE") != "REINFORCEMENT":
            continue
        how = _derivation(r)
        counts[how] += 1
        v = _f(r.get("BASE"))
        if v is not None:
            kg[r.get("FAMILY")][how] += v
        if how == "RATIO" and (r.get("CATEGORY") in ("VERIFIED", "MEASURED") or
                               r.get("SUPPORT") in ("SOURCE_COMPLETE", "SOURCE_COMPLETE_UNREVIEWED")):
            bad.append(dict(_key(r), why="RATIO_LABELLED_AS_A_MEASURED_QUANTITY"))
    return {"policy": POLICY_ID, "method": RM.describe(cfg), "unit_mass": table, "rows": dict(sorted(counts.items())),
            "kg": {k: {kk: round(vv, 6) for kk, vv in sorted(v.items())} for k, v in sorted(kg.items())},
            "violations": bad,
            "never": ["a kg/m3 ratio reported as a measured quantity", "a unit mass other than the project's method"]}


def policy_record():
    return {"policy_id": POLICY_ID, "decisions": DECISIONS, "diameters_mm": list(DIAMETERS_MM),
            "states": [MEASURED, CONDITIONAL, UPPER_BOUND, HELD]}
