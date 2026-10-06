"""Alsenan coverage-recovery round - BLIND build (no reference-QS or oracle value is available here).

Reads only frozen Urban registers (V3 / V3b / A3 / S1 / S3.1 / B2A1) and the two geometry extracts of this round, runs
the generic recovery engines and writes the scenario registers, then a freeze record. The post-freeze comparison
(post_freeze_comparison.py) runs only after the freeze and is the only place donor figures appear.

    python research/coverage_recovery_round/build_coverage_recovery.py [--twice]
"""

from __future__ import annotations

import hashlib
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from engine.source import beam_occurrence_recovery as BR  # noqa: E402,F401
from engine.source import blocker_remediation as BRM  # noqa: E402
from engine.source import column_concrete_geometry as CC  # noqa: E402
from engine.source import coverage_anomaly as CA  # noqa: E402
from engine.source import coverage_metrics as CM  # noqa: E402
from engine.source import evidence_ladder as EL  # noqa: E402
from engine.source import ground_beam_recovery as GB  # noqa: E402
from engine.source import ground_slab_recovery as GS  # noqa: E402
from engine.source import physical_measurement_state as PM  # noqa: E402
from engine.source import physical_wall_faces as WF  # noqa: E402
from engine.source import population_conservation as PC  # noqa: E402
from engine.source import quantity_scenarios as QS  # noqa: E402
from engine.source import slab_opening_reconciliation as SO  # noqa: E402
from engine.source import wall_band_reconciliation as WB  # noqa: E402

INPUTS = {
    "V3B_LINES": "tests/alsenan/registers_v3b/BOQ_LINES_V3B.json",
    "V3B_STRUCTURE": "tests/alsenan/registers_v3b/STRUCTURE_V3B_REGISTER.json",
    "V3_GROUND": "tests/alsenan/registers_v3/GROUND_STRUCTURE_REGISTER.json",
    "V3_BLOCKWORK": "tests/alsenan/registers_v3/BLOCKWORK_REGISTER.json",
    "A3_WALL_BANDS": "tests/alsenan/registers_a3/WALL_BAND_REGISTER.json",
    "S1_COLUMNS": "research/alsenan_structural_census_s1/COLUMN_OCCURRENCE_REGISTER.json",
    "S1_BEAMS": "research/alsenan_structural_census_s1/BEAM_OCCURRENCE_REGISTER.json",
    "S31_MAIN_BARS": "research/alsenan_column_rebar_s3_1/COLUMN_MAIN_BAR_REGISTER.json",
    "B2A1_SLABS": "data/reports/URBAN_QTO_ALSENAN_PHASE_B2A1_GENERIC_QA_PATCH/registers/SLAB_REGION_REGISTER.json",
    "GROUND_CELLS": "research/coverage_recovery_round/GROUND_SLAB_CELL_EXTRACT.json",
    "WALL_PAIRS": "research/coverage_recovery_round/WALL_FACE_PAIR_EXTRACT.json",
}
FLOORS = ("GF", "1F", "2F")
SLAB_T = {"FOUNDATION": 0.0, "GF": 0.16, "1F": 0.16, "2F": 0.18}       # printed sheet thickness tags (B2A1)
STOREY = {"GF": 4.5, "1F": 4.2, "2F": 4.2}                                # printed floor-to-floor (S1 levels)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def r3(x):
    return None if x is None else round(x, 3)


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n"


def load():
    data, hashes = {}, {}
    for k, rel in INPUTS.items():
        b = (ROOT / rel).read_bytes()
        hashes[rel] = sha(b)
        data[k] = json.loads(b)
    return data, hashes


def qsr(q):
    return QS.rounded(q)


# ------------------------------------------------------------------------------------------- dual-layer baseline
CONCRETE_TRADE = (
    ("C-FTG", "FOOTINGS"), ("C-STR", "STRAPS"), ("C-NECK", "NECKS"), ("C-GB-", "GROUND_BEAMS"),
    ("C-BWALL", "GROUND_BEAMS"), ("C-GSLAB", "GROUND_SLAB"), ("C-COL", "COLUMNS"), ("C-JNT", "COLUMNS"),
    ("C-BEAM", "BEAMS"), ("C-SLAB", "SLABS"), ("C-LINT", "LINTELS"), ("C-STAIR", "STAIRS"), ("C-DOME", "DOMES"),
    ("C-POOL-BLD", "BLINDING_PLAIN"), ("C-POOL", "POOL"), ("C-BLD", "BLINDING_PLAIN"), ("C-SWALL", "SPECIAL_RC"))


def concrete_trade(code):
    return next((t for p, t in CONCRETE_TRADE if code.startswith(p)), "OTHER_CONCRETE")


def baseline(lines):
    """Per concrete trade: TECHNICAL (what was published as Urban) and the DUAL-LAYER scenario V3b already held."""
    by = defaultdict(list)
    for ln in lines:
        if ln["trade"] != "CONCRETE":
            continue
        by[concrete_trade(ln["code"])].append(ln)
    out = {}
    for t, ls in sorted(by.items()):
        tech = sum(ln["release"]["technical"]["qty"] or 0.0 for ln in ls if ln["release"]["technical"].get("in_total"))
        parts = [p for ln in ls for p in QS.parts_from_release(ln["code"], ln["release"]["technical"],
                                                               ln["release"]["commercial"])]
        out[t] = {"lines": [ln["code"] for ln in ls], "technical_m3": r3(tech),
                  "technical_blocked_lines": [ln["code"] for ln in ls if ln["release"]["technical"]["qty"] is None],
                  "dual_layer": qsr(QS.combine(parts, unit="m3"))}
    return out


# ------------------------------------------------------------------------------------------------ ground beams
def ground_beams(D, lines):
    items = D["V3_GROUND"]["items"]["beams"]
    extD = D["V3B_STRUCTURE"]["ext_gb"]["D"]
    spans, resolvers = [], {}
    for b in items:
        s = {"span_id": b["id"], "length_m": b["length_m"], "B_m": b["B_m"], "kind": b["kind"],
             "source_handles": [b["id"]], "candidate_definitions": []}
        spans.append(s)
        if b["kind"] == "INTERIOR" and b.get("D_m"):
            d = b["D_m"]
            resolvers[b["id"]] = {"LOCAL_DIMENSION": lambda c: None, "SCHEDULE": lambda c: None,
                                  "DETAIL": (lambda dd: (lambda c: {"value": dd, "ref": "p.13 typical GB sections "
                                                                    "(span-length rule)"}))(d)}
        else:
            resolvers[b["id"]] = {"LOCAL_DIMENSION": lambda c: None, "SCHEDULE": lambda c: None,
                                  "DETAIL": lambda c: None, "SAME_MARK_ELSEWHERE": lambda c: None,
                                  "PAIRED_FACES_SECTION_GEOMETRY": lambda c: None, "PROJECT_TYPICAL": lambda c: None,
                                  "BOUNDED_CANDIDATE": lambda c: {"value": extD["qty"], "low": extD["low"],
                                                                  "high": extD["high"],
                                                                  "ref": "ground +-0.00 to GF +1.00 on all elevations"}}
    rec = GB.recover(spans, lambda s: resolvers[s["span_id"]])
    bw = next(ln for ln in lines if ln["code"] == "C-BWALL")
    bparts = QS.parts_from_release("C-BWALL", bw["release"]["technical"], bw["release"]["commercial"])
    vol = QS.combine([r["part"] for r in rec["spans"]] + bparts, unit="m3")
    ext = [r for r in rec["spans"] if r["terminal"]["known_geometry"]["kind"] == "EXTERIOR"]
    remed = BRM.remediate(
        {"flag_id": "GB-EXT-DEPTH", "kind": "MISSING_DEPTH", "element": f"{len(ext)} exterior ground-beam spans",
         "known_facts": {"spans": len(ext), "length_m": r3(sum(r["length_m"] for r in ext)), "B_m": 0.30},
         "unknown_fact": "exterior ground-beam depth ('FOLLOW ARCH.' - outer ground to GF slab level, not printed)",
         "current_quantity": 0.0, "why_blocked": "depth not dimensioned on the plan or in the schedule",
         "where_to_look": "ST7757 p.13 typical ground-beam sections; architectural elevations (ground +-0.00, GF +1.00)",
         "search_text": "FOLLOW ARCH / GROUND BEAM / G.B", "consultant_question":
             "Please confirm the exterior ground-beam depth (and embedment below natural ground) for the spans marked "
             "'FOLLOW ARCH.'"},
        {"LOCAL_DIMENSION": lambda c: None, "SCHEDULE": lambda c: None, "DETAIL": lambda c: None,
         "SAME_MARK_ELSEWHERE": lambda c: None, "PAIRED_FACES_SECTION_GEOMETRY": lambda c: None,
         "PROJECT_TYPICAL": lambda c: None,
         "BOUNDED_CANDIDATE": lambda c: {"value": extD["qty"], "low": extD["low"], "high": extD["high"]}},
        quantity_fn=lambda d: sum(r["length_m"] for r in ext) * 0.30 * d)
    return {"spans": [{"span": r["span"], "kind": r["terminal"]["known_geometry"]["kind"], "length_m": r3(r["length_m"]),
                       "B_m": r["B_m"], "depth_level": r["depth"]["level"], "depth_authority": r["depth"]["authority"],
                       "depth_m": r["depth"]["value"], "terminal": r["terminal"]["terminal_state"],
                       "part": r["part"]} for r in rec["spans"]],
            "conservation": rec["conservation"], "volume": qsr(vol), "remediation": [remed],
            "length_m": r3(rec["length_m"]), "boundary_beam_line": "C-BWALL"}


# ------------------------------------------------------------------------------------------------- ground slab
def ground_slab(D):
    cells = D["GROUND_CELLS"]["cells"]
    official = [c["cell_id"] for c in cells if c["part"] == "RELEASED_ZONE_PART"]
    cl = GS.classify(cells, is_thickness_label=lambda t: t.replace(" ", "").upper().startswith("T="),
                     official_cell_ids=official)
    labels = sorted({t for c in cells for t in c["labels"] if t.replace(" ", "").upper().startswith("T=")})
    tmm = sorted({int(m.group(1)) for t in labels for m in [re.search(r"T=\s*(\d+)\s*CM", t.upper())] if m})
    t_m = tmm[0] / 100.0 if len(tmm) == 1 else None
    th = EL.resolve("SLAB_THICKNESS", {"PRINTED_IN_REGION": lambda c: None, "SECTION_OR_DETAIL": lambda c: None,
                                       "SAME_SHEET_TYPICAL_LABEL": lambda c: None if t_m is None else
                                       {"value": t_m, "ref": f"{labels} printed in the released zones of the sheet"}})
    q = GS.quantities(cl, th, labelled_t_m=t_m)
    fp_cells = sum(c["area_m2"] for c in cl if c["role"] in (GS.LABELLED_OFFICIAL, GS.UNLABELLED_CANDIDATE))
    remed = BRM.remediate(
        {"flag_id": "GSLAB-LABEL-SCOPE", "kind": "LABEL_SCOPE", "element": "ground-slab cells without a T= label",
         "known_facts": {"candidate_cells": sum(1 for c in cl if c["role"] == GS.UNLABELLED_CANDIDATE),
                         "candidate_area_m2": r3(sum(c["area_m2"] for c in cl if c["role"] == GS.UNLABELLED_CANDIDATE)),
                         "labels_on_sheet": labels},
         "unknown_fact": "whether the printed slab note applies to every cell between ground beams",
         "current_quantity": r3(q["volume"]["VERIFIED_QUANTITY"]),
         "why_blocked": "the thickness / mesh note is printed inside two zones only",
         "where_to_look": "ST7757 GROUND BEAMS PLAN (zone notes), general notes, GF architectural plan (floor build-up)",
         "search_text": "T=10cm / E.W. / GROUND SLAB / SLAB ON GRADE",
         "consultant_question": "Does 'T=10cm, 5Ø10/m E.W.' apply to every ground-floor slab panel between the "
                                "ground beams, or only to the two labelled zones?"},
        {"PRINTED_IN_REGION": lambda c: None, "SECTION_OR_DETAIL": lambda c: None,
         "SAME_SHEET_TYPICAL_LABEL": lambda c: None if t_m is None else {"value": t_m}},
        quantity_fn=lambda t: fp_cells * t)
    return {"cells": [{k: c[k] for k in ("cell_id", "footprint_id", "part", "area_m2", "eff_width_mm", "labels", "role",
                                         "why")} for c in cl],
            "area": qsr(q["area"]), "volume": qsr(q["volume"]), "excluded": q["excluded"], "thickness": q["thickness"],
            "footprint_cells_m2": r3(fp_cells), "remediation": [remed],
            "released_zones": D["GROUND_CELLS"]["released_zones"]}


# ----------------------------------------------------------------------------------------------------- columns
def columns(D):
    mb = {r["occurrence_id"]: r for r in D["S31_MAIN_BARS"]["rows"] if r["length_kind"] == "CORE_VERTICAL_RUN"}
    recs, occs = [], []
    for o in D["S1_COLUMNS"]["rows"]:
        sec = o.get("schedule_section_cm") or o.get("drawn_section_cm")
        iv = mb[o["column_id"]]["interval"]
        H = iv["length_mm"] / 1000.0
        occ = {"occurrence_id": o["column_id"], "floor": o["floor"], "B_m": sec[0] / 100.0 if sec else None,
               "D_m": sec[1] / 100.0 if sec else None, "interval_m": H,
               "interval_state": "ESTABLISHED" if iv["state"] == "ESTABLISHED" else "LOWER_BOUND",
               "source_handles": (o.get("plan_source") or {}).get("handles", [])}
        occs.append(occ)
        kw = {"slab_t_m": SLAB_T[o["floor"]]}
        if iv["state"] != "ESTABLISHED":          # founding level unknown: Urban provisional range -1.0 .. -2.0
            kw["interval_low_m"], kw["interval_high_m"] = H, H + 0.5
        r = CC.record(occ, **kw)
        r["interval_basis"] = iv["basis"]
        r["interval_state"] = iv["state"]
        recs.append(r)
    cons = CC.conserve(occs, recs)
    per = {}
    for fl in ("FOUNDATION",) + FLOORS:
        rr = [r for r in recs if r["floor"] == fl]
        per[fl] = {"occurrences": len(rr), "gross_interval_m3": r3(sum(r["gross_m3"] or 0 for r in rr)),
                   "column_plus_joint": qsr(QS.combine([r["part"] for r in rr], unit="m3")),
                   "terminal_states": dict(Counter(r["terminal"]["terminal_state"] for r in rr))}
    return {"records": [{k: (r3(v) if isinstance(v, float) else v) for k, v in r.items() if k not in ("terminal",)}
                        | {"terminal_state": r["terminal"]["terminal_state"]} for r in recs],
            "per_floor": per, "conservation": cons,
            "volume": qsr(QS.combine([r["part"] for r in recs], unit="m3")),
            "basis": "B x D x (storey interval - slab thickness above); joints included; FOUNDATION storey from footing "
                     "top to GF FFL (ground beams and ground slab exclude the column footprint - no double count)"}


# ------------------------------------------------------------------------------------------------------- beams
def beams(D, lines):
    res = D["V3B_STRUCTURE"]["residue"]["beams"]
    tech = {ln["code"]: ln for ln in lines if ln["code"].startswith("C-BEAM")}
    parts, objs, occs, dup = [], [], [], []
    for ln in sorted(tech.values(), key=lambda x: x["code"]):
        if ln["code"].endswith("-RES"):
            continue
        q = ln["release"]["technical"]["qty"]
        parts.append(QS.part(ln["code"], "VERIFIED" if ln["release"]["technical"]["class"] in ("COMPUTED", "DERIVED")
                             else "LOWER_BOUND", q, origin="SOURCE_FACT"))
    for i, b in enumerate(res):
        oid = f"RES-{b['floor']}-{i:02d}-{b['type']}"
        if b.get("superseded_by"):
            dup.append({"occurrence_id": oid, "duplicate_of": b["superseded_by"], "why": b["why_v3a"]})
            continue
        occ = {"occurrence_id": oid, "source_handles": [b["id"]], "position": None, "count": 1,
               "known_geometry": {"type": b["type"], "length_m": b["length_m"], "B_m": b["B_m"], "D_m": b["D_m"]},
               "candidate_definitions": [b["type"]]}
        occs.append({"occurrence_id": oid})
        c = b.get("commercial")
        attempts = EL.resolve("MEMBER_BINDING", {
            "NEARBY_TAG": lambda x: None,
            "PAIRED_FACES": (lambda bb: (lambda x: {"value": bb["length_m"]} if bb["length_m"] and
                                         bb["why_v3a"] in ("SPAN_COUNT_MISMATCH", "BAND_TYPE_CONFLICT",
                                                           "TAG_INSIDE_SUPPORT") else None))(b),
            "COLUMN_ENDPOINTS": lambda x: None,
            "CONTINUITY_WITH_ADJACENT_SPAN": lambda x: None,
            "SCHEDULE_WIDTH_MATCH": (lambda bb: (lambda x: {"value": bb["length_m"]} if bb["length_m"] else None))(b),
            "SAME_TYPE_MEDIAN_LENGTH": (lambda cc: (lambda x: {"low": cc["low"], "high": cc["high"]} if cc else None))(c)})
        if c and c.get("qty") is not None:
            p = QS.part(oid, "CANDIDATE", c["qty"], min(c["low"], c["qty"]), max(c["high"], c["qty"]),
                        origin="CANDIDATE", why=f"{b['why_v3a']}: {c['method']}")
            term = PC.terminal(occ, "CANDIDATE_QUANTIFIED", quantity=c["qty"], unresolved=["BINDING"], why=b["why_v3a"])
        else:
            p = QS.part(oid, "UNQUANTIFIED", why=f"{b['why_v3a']}: tag without a measurable band")
            term = PC.terminal(occ, "UNQUANTIFIED", unresolved=["GEOMETRY"], why=b["why_v3a"])
        parts.append(p)
        objs.append({"occurrence_id": oid, "floor": b["floor"], "type": b["type"], "why_v3a": b["why_v3a"],
                     "length_m": b["length_m"], "terminal": term["terminal_state"], "part": p,
                     "binding_attempts": attempts["attempts"], "binding_level": attempts["level"]})
    cons = PC.require_conserved(occs, [PC.terminal({"occurrence_id": o["occurrence_id"], "source_handles": ["x"]},
                                                   o["terminal"], quantity=o["part"]["best"],
                                                   unresolved=["B"] if o["terminal"] != "MEASURED_COMPLETE" else [])
                                       for o in objs])
    counts = {}
    for ln in tech.values():
        m = re.search(r"(\d+) computed, (\d+) blocked", ln.get("formula") or "")
        if m:
            counts[ln["level"]] = {"computed": int(m.group(1)), "blocked": int(m.group(2))}
    census = Counter((r["floor"], r["terminal_state"]) for r in D["S1_BEAMS"]["rows"])
    return {"residue_objects": objs, "duplicates_removed": dup, "conservation": cons,
            "volume": qsr(QS.combine(parts, unit="m3")), "v3b_counts": counts,
            "s1_tag_census": {f"{k[0]}|{k[1]}": v for k, v in sorted(census.items())}}


# ------------------------------------------------------------------------------------------------------- slabs
def slabs(D):
    out, parts = {}, []
    for fl in FLOORS:
        sh = D["B2A1_SLABS"]["sheets"][fl]
        r = SO.reconcile(sh["gross_outline_area_m2"], sh["faces"], sheet=fl)
        t = SLAB_T[fl]
        out[fl] = {"gross_m2": r3(r["gross_m2"]), "plate_m2": r3(r["plate_m2"]), "openings_m2": r3(r["openings_m2"]),
                   "conflict_openings_m2": r3(r["conflict_openings_m2"]),
                   "openings": [{k: (r3(v) if isinstance(v, float) else v) for k, v in o.items()} for o in r["openings"]],
                   "net_area": qsr(r["net_area"]), "t_m": t}
        parts.append(QS.part(f"{fl}:PLATE", "VERIFIED", r["plate_m2"] * t, origin="SOURCE_FACT"))
        if r["conflict_openings_m2"]:
            parts.append(QS.part(f"{fl}:CONFLICT", "SOURCE_CONFLICT", 0.0, 0.0, r["conflict_openings_m2"] * t,
                                 why="opening with a printed thickness tag inside"))
    return {"sheets": out, "volume": qsr(QS.combine(parts, unit="m3")),
            "area": qsr(QS.combine([QS.part(f"{fl}:A", "VERIFIED", out[fl]["plate_m2"]) for fl in FLOORS] +
                                   [QS.part(f"{fl}:AC", "SOURCE_CONFLICT", 0.0, 0.0, out[fl]["conflict_openings_m2"])
                                    for fl in FLOORS if out[fl]["conflict_openings_m2"]], unit="m2"))}


# ------------------------------------------------------------------------------------------------------- walls
def walls(D):
    bands = D["A3_WALL_BANDS"]["bands"]
    pairs = D["WALL_PAIRS"]["floors"]
    rows = D["V3_BLOCKWORK"]["rows"]
    recon, length = {}, {}
    for fl in FLOORS:
        b = bands[fl]
        for w in (150, 200):
            est = [x for x in b if x["thickness_mm"] == w and x["state"] == "WALL_BAND_ESTABLISHED"]
            amb = [x for x in b if x["thickness_mm"] == w and x["state"] != "WALL_BAND_ESTABLISHED"]
            A = {"established_m": r3(sum(x["length_m"] for x in est)), "ambiguous_m": r3(sum(x["length_m"] for x in amb)),
                 "column_overlap_m": r3(sum(x["column_overlap_m"] or 0 for x in est + amb)),
                 "bands_established": len(est), "bands_ambiguous": len(amb)}
            ivs = [dict(x, p0=tuple(x["p0"]), p1=tuple(x["p1"])) for x in pairs[fl]["pairs"][str(w)]]
            cl = WB.classify(ivs, column_boxes=[tuple(c) for c in pairs[fl]["column_boxes"]],
                             opening_boxes=[tuple(c) for c in pairs[fl]["opening_boxes"]])
            Bt = WB.totals(cl)
            recon[f"{fl}|{w}"] = {"method_a": A, "method_b": Bt, "method_b_pairs": len(cl),
                                  "method_c": "NOT_RUN (room-adjacency reconstruction needs the V3 space graph, not in "
                                              "the frozen registers)",
                                  "method_d_widths": dict(Counter(round(x["width"]) for x in ivs)),
                                  "explain": WB.explain(A, Bt)}
            length[f"{fl}|{w}"] = QS.combine(
                [QS.part(f"{fl}|{w}|{x['band']}", "VERIFIED", x["length_m"], origin="DERIVED") for x in est] +
                [QS.part(f"{fl}|{w}|{x['band']}", "CANDIDATE", x["length_m"], 0.0, x["length_m"], origin="CANDIDATE",
                         why="WALL_BAND_AMBIGUOUS - reported, previously never measured") for x in amb], unit="m")
    by_w = {}
    for w in (150, 200):
        by_w[str(w)] = qsr(QS.combine([QS.part(k, "VERIFIED", v["VERIFIED_QUANTITY"]) for k, v in length.items()
                                       if k.endswith(f"|{w}") and v["VERIFIED_QUANTITY"]] +
                                      [QS.part(k + ":amb", "CANDIDATE", v["BEST_PROVISIONAL_QUANTITY"] -
                                               v["LOWER_BOUND_QUANTITY"], 0.0,
                                               v["BEST_PROVISIONAL_QUANTITY"] - v["LOWER_BOUND_QUANTITY"])
                                       for k, v in length.items() if k.endswith(f"|{w}") and
                                       v["BEST_PROVISIONAL_QUANTITY"] > v["LOWER_BOUND_QUANTITY"]], unit="m"))
    # physical wall faces (finish-independent): established masonry rows + ambiguous bands
    heights = defaultdict(list)
    walls_in = []
    for r in rows:
        if r["position"] == "NOT_MASONRY" or not r["length_m"]:
            continue
        h = r["area_m2"] / r["length_m"] if r.get("area_m2") else None
        if h:
            heights[r["floor"]].append(h)
        walls_in.append({"wall_id": r["band"], "floor": r["floor"], "length_m": r["length_m"],
                         "thickness_mm": r["thickness_mm"], "position": r["position"], "net_of_openings": True,
                         "finish": None, "plaster_rule": None, "_h": h})
    for fl in FLOORS:
        for x in bands[fl]:
            if x["state"] != "WALL_BAND_ESTABLISHED" and x["thickness_mm"] in (150.0, 200.0):
                walls_in.append({"wall_id": x["band"], "floor": fl, "length_m": x["length_m"],
                                 "thickness_mm": x["thickness_mm"], "position": "INTERNAL", "net_of_openings": True,
                                 "finish": None, "plaster_rule": None, "_h": None, "_ambiguous": True})

    def height_for(w):
        if w.get("_h"):
            return EL.resolve("WALL_HEIGHT", {"EXPLICIT_LOCAL_HEIGHT": lambda c: None,
                                              "ARCHITECTURAL_LEVEL_ELEVATION": lambda c: None,
                                              "STRUCTURAL_INTERVAL_MINUS_MEMBER": lambda c: {"value": w["_h"]}})
        med = statistics.median(heights[w["floor"]])
        return EL.resolve("WALL_HEIGHT", {"EXPLICIT_LOCAL_HEIGHT": lambda c: None,
                                          "ARCHITECTURAL_LEVEL_ELEVATION": lambda c: None,
                                          "STRUCTURAL_INTERVAL_MINUS_MEMBER": lambda c: None,
                                          "URBAN_PROVISIONAL_SCENARIO": lambda c: {
                                              "best": med, "low": STOREY[w["floor"]] - 0.16 - 0.75,
                                              "high": STOREY[w["floor"]] - 0.16}})

    reg = WF.register(walls_in, height_for)
    face_area = defaultdict(float)
    for f in reg["faces"]:
        face_area[(f["floor"], f["face_role"])] += f.get("PHYSICAL_WALL_FACE_AREA") or 0.0
    return {"reconciliation": recon, "length_by_thickness": by_w,
            "length_floor_thickness": {k: qsr(v) for k, v in length.items()},
            "physical_faces": {"faces": len(reg["faces"]), "physical_area": qsr(reg["physical_area"]),
                               "by_floor_role": {f"{k[0]}|{k[1]}": r3(v) for k, v in sorted(face_area.items())},
                               "finish_unassigned_faces": reg["finish_unassigned_faces"],
                               "basis": "two faces per masonry band; height = structural interval - terminating member "
                                        "(DERIVED) or, for ambiguous bands, a floor-median provisional scenario; bands "
                                        "are net of openings"}}


# -------------------------------------------------------------------------------------------------- dashboard
def dashboard(base, gb, gs, col, bm, sl, wl, lines):
    def tech(t):
        return base.get(t, {}).get("technical_m3") or 0.0

    rows = []

    def row(trade, unit, official_before, q, unq, top, fix, cov):
        rows.append({"trade": trade, "unit": unit, "official_before": r3(official_before),
                     "verified": q["VERIFIED_QUANTITY"], "lower_bound": q["LOWER_BOUND_QUANTITY"],
                     "best_provisional": q["BEST_PROVISIONAL_QUANTITY"], "low": q["LOW_SCENARIO"],
                     "high": q["HIGH_SCENARIO"], "unquantified": unq, "coverage_pct": cov,
                     "release": QS.release_label(q), "top_blocker": top, "how_to_fix": fix})

    pct = lambda a, b: None if not b else round(100.0 * a / b, 1)  # noqa: E731
    row("GROUND_BEAMS", "m3", tech("GROUND_BEAMS"), gb["volume"], len(gb["volume"]["UNQUANTIFIED_COMPONENTS"]),
        "exterior depth 'FOLLOW ARCH.' not dimensioned (28 spans, length and width measured)",
        "bind the p.13 exterior section / elevation depth, or consultant confirmation",
        pct(sum(1 for s in gb["spans"] if s["terminal"] != "UNQUANTIFIED"), len(gb["spans"])))
    row("GROUND_SLAB", "m3", tech("GROUND_SLAB"), gs["volume"], 0,
        "thickness note printed in two zones only; unlabelled cells were never measured",
        "confirm the T=10cm note applies to all ground-slab panels",
        pct(gs["volume"]["VERIFIED_QUANTITY"], gs["volume"]["BEST_PROVISIONAL_QUANTITY"]))
    row("COLUMNS_AND_JOINTS", "m3", tech("COLUMNS") + tech("NECKS"), col["volume"], 0,
        "foundation storey founding level not printed (interval is a lower bound)",
        "founding level / neck height from the consultant (note 12 leaves it to site)",
        pct(col["conservation"]["terminal_records"], col["conservation"]["occurrences_in"]))
    row("BEAMS", "m3", tech("BEAMS"), bm["volume"], len(bm["volume"]["UNQUANTIFIED_COMPONENTS"]),
        "unbound tags / span-count mismatches / type conflict",
        "bind tags to bands (continuity + endpoints), confirm CB8 span count and the B3/CB3 band",
        pct(sum(1 for o in bm["residue_objects"] if o["terminal"] != "UNQUANTIFIED"), len(bm["residue_objects"])))
    row("SLABS", "m3", tech("SLABS"), sl["volume"], 0,
        "one GF 'VOID' face carries a printed T16 tag (conflicting evidence)",
        "confirm whether the GF void face is open or slab", 100.0)
    for w in ("150", "200"):
        q = wl["length_by_thickness"][w]
        row(f"BLOCKWORK_{w}_LENGTH", "m", q["VERIFIED_QUANTITY"], q, 0,
            "WALL_BAND_AMBIGUOUS bands were reported but never measured",
            "confirm wall identity of ambiguous bands (wall vs kerb / parapet / duplicate face)",
            pct(q["VERIFIED_QUANTITY"], q["BEST_PROVISIONAL_QUANTITY"]))
    pf = wl["physical_faces"]["physical_area"]
    plaster_tech = sum(ln["release"]["technical"]["qty"] or 0 for ln in lines
                       if ln["trade"] == "PLASTER_PAINT" and ln["unit"] == "m2" and ln["release"]["technical"].get("in_total"))
    row("PHYSICAL_WALL_FACES", "m2", plaster_tech, pf, len(pf["UNQUANTIFIED_COMPONENTS"]),
        "finish material / room certification were required before any face was released",
        "release physical faces first; finish assignment afterwards", None)
    return rows


# ------------------------------------------------------------------------------------------------- coverage
def coverage(base, gb, gs, col, bm, sl, wl, D):
    m = []
    occ_gb = [{"terminal_state": s["terminal"], "known": {"length": True, "width": True,
                                                          "depth": s["depth_authority"] == "VERIFIED"},
               "semantic_established": True, "source_only": s["depth_authority"] == "VERIFIED"} for s in gb["spans"]]
    occ_gb_before = [dict(o, terminal_state="MEASURED_COMPLETE" if o["source_only"] else "UNQUANTIFIED") for o in occ_gb]
    for name, occ, off, best in (("GROUND_BEAMS_BEFORE", occ_gb_before, base["GROUND_BEAMS"]["technical_m3"],
                                  gb["volume"]["BEST_PROVISIONAL_QUANTITY"]),
                                 ("GROUND_BEAMS_AFTER", occ_gb, gb["volume"]["VERIFIED_QUANTITY"],
                                  gb["volume"]["BEST_PROVISIONAL_QUANTITY"])):
        m.append(CM.trade_coverage(name, occ, official_qty=off, best_qty=best, dimensions=("length", "width", "depth")))
    cells = [c for c in gs["cells"] if c["role"] in (GS.LABELLED_OFFICIAL, GS.UNLABELLED_CANDIDATE)]
    m.append(CM.trade_coverage("GROUND_SLAB_AFTER", [{"terminal_state": "MEASURED_COMPLETE" if c["role"] == GS.LABELLED_OFFICIAL
                                                      else "CANDIDATE_QUANTIFIED", "known": {"area": True,
                                                      "thickness": c["role"] == GS.LABELLED_OFFICIAL},
                                                      "semantic_established": c["role"] == GS.LABELLED_OFFICIAL,
                                                      "source_only": c["role"] == GS.LABELLED_OFFICIAL} for c in cells],
                                 official_qty=gs["volume"]["VERIFIED_QUANTITY"], best_qty=gs["volume"]["BEST_PROVISIONAL_QUANTITY"],
                                 dimensions=("area", "thickness")))
    recs = col["records"]
    m.append(CM.trade_coverage("COLUMNS_AFTER", [{"terminal_state": r["terminal_state"], "known": {
        "section": True, "interval": r["interval_state"] == "ESTABLISHED"}, "semantic_established": True,
        "source_only": r["interval_state"] == "ESTABLISHED"} for r in recs],
        official_qty=col["volume"]["VERIFIED_QUANTITY"], best_qty=col["volume"]["BEST_PROVISIONAL_QUANTITY"],
        dimensions=("section", "interval")))
    m.append(CM.trade_coverage("BEAM_RESIDUE_AFTER", [{"terminal_state": o["terminal"], "known": {
        "length": bool(o["length_m"])}, "semantic_established": False} for o in bm["residue_objects"]],
        dimensions=("length",)))
    anomalies = [CA.ground_slab_vs_footprint(base["GROUND_SLAB"]["technical_m3"] / 0.10, gs["footprint_cells_m2"]),
                 dict(CA.ground_slab_vs_footprint(gs["area"]["BEST_PROVISIONAL_QUANTITY"], gs["footprint_cells_m2"]),
                      check_id="GROUND_SLAB_FOOTPRINT_AFTER")]
    v3b = {"GF": (25, 30), "1F": (15, 20), "2F": (8, 9), "FOUNDATION": (0, 36)}
    for fl, (emitted, n) in v3b.items():
        anomalies.append(CA.count_conservation(f"COLUMN_CONCRETE_{fl}_BEFORE", n, emitted,
                                               what="V3b technical column concrete records vs S1 occurrences"))
        anomalies.append(CA.count_conservation(f"COLUMN_CONCRETE_{fl}_AFTER", n, col["per_floor"][fl]["occurrences"],
                                               what="concrete geometry records vs S1 occurrences"))
    for k, r in wl["reconciliation"].items():
        anomalies.append(dict(CA.walls_vs_paired_faces(r["method_a"]["established_m"],
                                                       r["method_b"].get(WB.PAIRED_WALL, 0.0)), check_id=f"WALLS_{k}"))
    for fl, c in bm["v3b_counts"].items():
        anomalies.append(dict(CA.beams_vs_tags(c["computed"], c["computed"] + c["blocked"]), check_id=f"BEAMS_{fl}"))
    return {"trades": m, "anomalies": CA.summarise(anomalies)}


# ------------------------------------------------------------------------------------------------------ build
def build():
    D, hashes = load()
    lines = D["V3B_LINES"]["lines"]
    base = baseline(lines)
    gb, gs, col = ground_beams(D, lines), ground_slab(D), columns(D)
    bm, sl, wl = beams(D, lines), slabs(D), walls(D)
    dash = dashboard(base, gb, gs, col, bm, sl, wl, lines)
    cov = coverage(base, gb, gs, col, bm, sl, wl, D)
    blocked = {
        "ground_beam_exterior_spans": {"before": "BLOCKED (technical 0)", "count": sum(1 for s in gb["spans"]
                                                                                        if s["kind"] == "EXTERIOR"),
                                       "after": dict(Counter(s["terminal"] for s in gb["spans"] if s["kind"] == "EXTERIOR"))},
        "ground_slab_unlabelled_cells": {"before": "not measured", "count": sum(1 for c in gs["cells"]
                                                                               if c["role"] == GS.UNLABELLED_CANDIDATE),
                                         "after": "CANDIDATE_QUANTIFIED"},
        "column_occurrences_without_technical_concrete": {
            "before": 95 - (25 + 15 + 8), "after": dict(Counter(r["terminal_state"] for r in col["records"]))},
        "beam_residue": {"before": "BLOCKED (technical 0; GF / 1F residue BUDGET only)",
                         "count": len(bm["residue_objects"]), "duplicates_removed": len(bm["duplicates_removed"]),
                         "after": dict(Counter(o["terminal"] for o in bm["residue_objects"]))},
        "wall_bands_ambiguous": {"before": "reported, never measured",
                                 "count": sum(v["method_a"]["bands_ambiguous"] for v in wl["reconciliation"].values()),
                                 "after": "CANDIDATE length + provisional face area"},
        "slab_conflict_openings": {"count": sum(1 for fl in FLOORS for o in sl["sheets"][fl]["openings"]
                                                if o["state"] == SO.OPENING_CONFLICT), "after": "SOURCE_CONFLICT scenario"},
    }
    recovered = (blocked["ground_beam_exterior_spans"]["count"] + blocked["ground_slab_unlabelled_cells"]["count"] +
                 blocked["column_occurrences_without_technical_concrete"]["before"] +
                 sum(v for k, v in blocked["beam_residue"]["after"].items() if k != "UNQUANTIFIED") +
                 blocked["wall_bands_ambiguous"]["count"] + blocked["slab_conflict_openings"]["count"])
    still = (len(gb["volume"]["UNQUANTIFIED_COMPONENTS"]) + blocked["beam_residue"]["after"].get("UNQUANTIFIED", 0))
    remed = gb["remediation"] + gs["remediation"]
    remed.append(BRM.remediate(
        {"flag_id": "COL-FOUNDATION-INTERVAL", "kind": "MISSING_HEIGHT", "element": "36 foundation-storey columns / necks",
         "known_facts": {"interval_basis": "GF FFL +1.00 minus founding level <= -1.50 minus footing depth"},
         "unknown_fact": "founding level", "current_quantity": 0.0,
         "why_blocked": "general note leaves the founding level to site", "where_to_look": "ST7757 general notes (p.1/p.8)",
         "search_text": "FOUNDING LEVEL / SOIL REPORT", "consultant_question":
             "Please confirm the founding level (or neck height) used for the foundation-storey columns."},
        {"EXPLICIT_LOCAL_HEIGHT": lambda c: None, "ARCHITECTURAL_LEVEL_ELEVATION": lambda c: None,
         "STRUCTURAL_INTERVAL_MINUS_MEMBER": lambda c: None,
         "FLOOR_TO_FLOOR_MINUS_STRUCTURE": lambda c: None, "ROOM_HEIGHT_NOTE": lambda c: None,
         "PROJECT_DEFAULT_FINISH_HEIGHT": lambda c: None,
         "URBAN_PROVISIONAL_SCENARIO": lambda c: {"best": 0.0, "low": 0.0, "high": 0.5}},
        quantity_fn=lambda dh: col["per_floor"]["FOUNDATION"]["column_plus_joint"]["BEST_PROVISIONAL_QUANTITY"] +
        dh * sum(r["A_m2"] for r in col["records"] if r["floor"] == "FOUNDATION")))
    for o in bm["residue_objects"]:
        remed.append({"flag_id": f"BEAM-{o['occurrence_id']}", "kind": "UNBOUND_MEMBER", "element": o["type"],
                      "known_facts": {"floor": o["floor"], "length_m": o["length_m"]}, "unknown_fact": "binding",
                      "current_quantity": 0.0, "provisional_quantity": o["part"]["best"],
                      "low_scenario": o["part"]["low"], "high_scenario": o["part"]["high"],
                      "quantity_impact": o["part"]["best"], "why_blocked": o["why_v3a"],
                      "attempts": o["binding_attempts"], "successful_method": o["binding_level"],
                      "authority": "PROVISIONAL" if o["part"]["best"] else "BLOCKED", "fact_origin": "CANDIDATE",
                      "next_automated_method": "CONTINUITY_WITH_ADJACENT_SPAN", "where_to_look": "ST7757 beam plans",
                      "search_text": o["type"], "consultant_question": None, "needs_consultant": False,
                      "result": "RESOLVED_PROVISIONAL" if o["part"]["best"] else "STILL_BLOCKED"})
    files = {
        "COVERAGE_BASELINE.json": {"concrete_by_trade": base, "rule": "technical = what was published as Urban; "
                                   "dual_layer = the same lines read through quantity_scenarios.parts_from_release"},
        "BLOCKED_OCCURRENCE_ANALYSIS.json": {"populations": blocked, "previously_blocked_recovered": recovered,
                                             "still_unquantified": still},
        "REMEDIATION_ATTEMPTS.json": {"records": remed},
        "QUANTITY_SCENARIOS.json": {"ground_beams": gb, "ground_slab": gs, "columns": col, "beams": bm, "slabs": sl,
                                    "walls": wl},
        "COVERAGE_METRICS.json": cov,
        "QUANTITY_COVERAGE_DASHBOARD.json": {"rows": dash, "rule": "official / lower bound / best provisional / low / "
                                             "high are separate layers; provisional values are not procurement values"},
    }
    return files, hashes


def main(write=True):
    files, hashes = build()
    blobs = {k: dumps(v).encode() for k, v in files.items()}
    if write:
        for k, b in blobs.items():
            (HERE / k).write_bytes(b)
        freeze = {"round": "COVERAGE_RECOVERY", "inputs": hashes, "outputs": {k: sha(b) for k, b in sorted(blobs.items())},
                  "donor_values_read": False, "reference_qs_read": False,
                  "rule": "written before post_freeze_comparison.py; the comparison refuses to run if any hash differs"}
        (HERE / "COVERAGE_RECOVERY_FREEZE.json").write_text(dumps(freeze), encoding="utf-8")
    return files, blobs


if __name__ == "__main__":
    files, b1 = main()
    if "--twice" in sys.argv:
        _, b2 = main(write=False)
        print("built twice identical:", all(b1[k] == b2[k] for k in b1))
    for r in files["QUANTITY_COVERAGE_DASHBOARD.json"]["rows"]:
        print(f"{r['trade']:22s} {r['unit']:3s} before {r['official_before']!s:>9} | V {r['verified']!s:>9} LB "
              f"{r['lower_bound']!s:>9} BEST {r['best_provisional']!s:>9} [{r['low']!s} - {r['high']!s}] "
              f"unq {r['unquantified']} {r['release']}")
    print(json.dumps(files["BLOCKED_OCCURRENCE_ANALYSIS.json"], indent=0)[:1500])
