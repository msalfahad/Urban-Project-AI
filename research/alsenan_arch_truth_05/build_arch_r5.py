"""ALSENAN ROUND 5 - architectural BOQ truth engine: build the frozen registers.

    PYTHONPATH=.:research/external_engine_lab python3 research/alsenan_arch_truth_05/build_arch_r5.py <ctx.pkl> [--twice]

1. load the frozen Alsenan context (P7757 / ST7757 sources, Route A topology, V3 / V3b layers)
2. run alsenan_arch_r5 (physical spaces, Route B shadow, orphans, trade regions, floor conservation, wet completeness,
   wall ledger, blockwork, openings, finishes, facade, stairs, source coverage)
3. write the Round-5 registers + INDEX.json (sha256 per file). --twice rebuilds and refuses on any difference.
No benchmark / human quantity is read (firewall). Rebar registers are not read or written.
"""

from __future__ import annotations

import hashlib
import json
import pickle
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT), str(ROOT / "research" / "external_engine_lab")):
    if p not in sys.path:
        sys.path.insert(0, p)

import alsenan_arch_r5 as A  # noqa: E402
from engine.source import arch_quantity_truth as AQ  # noqa: E402
from engine.source import planar_shadow_topology as PT  # noqa: E402

OUT = HERE / "registers"
R2_OPENINGS = ROOT / "research/alsenan_control_plane_02/registers/OPENING_EVIDENCE_REGISTER_V2.json"
SCHEMA = "URBAN_ALSENAN_ARCH_R5"


def _text(o):
    return json.dumps(A._clean(o), indent=1, ensure_ascii=False, sort_keys=False, default=str) + "\n"


def _sum(rows, key, pred=lambda r: True):
    d = defaultdict(float)
    for r in rows:
        if pred(r) and isinstance(r.get(key), (int, float)):
            d[r.get("state")] += r[key]
    return {k: round(v, 3) for k, v in sorted(d.items())}


def _by_floor(rows, key, pred=lambda r: True):
    d = defaultdict(lambda: defaultdict(float))
    for r in rows:
        if pred(r) and isinstance(r.get(key), (int, float)):
            d[r["floor"]][r.get("state")] += r[key]
    return {fl: {k: round(v, 3) for k, v in sorted(x.items())} for fl, x in sorted(d.items())}


def registers(ctx):
    r2 = json.loads(R2_OPENINGS.read_text())["rows"]
    B = A.build(ctx, r2)
    Fs, regions, fin, ops = B["Fs"], B["regions"], B["fin"], B["ops"]
    reg_by_id = {r["region_id"]: r for r in regions}
    regs = {}

    # ---------------------------------------------------------------------------------- coverage / spaces / shadow
    regs["ARCHITECTURAL_SOURCE_COVERAGE_REGISTER"] = B["coverage"]
    rec_rows = []
    for fl, (rec, rest) in B["recs"].items():
        for r in rec:
            rec_rows.append({"space_id": f"PS:{fl}:{r['id']}", "floor": fl, "route": "B_RECOVERED",
                             "class": "RECOVERED_SPACE", "area_m2": A._r(r["area_m2"]),
                             "route_b_face": r["route_b_face"], "closure_sources": r["closure_sources"],
                             "closure_method": "ROUTE_B planar shadow (source linework + recorded gap / door closures) "
                                               "inside plate area that Route A leaves unclosed",
                             "closure_confidence": "REVIEW_REQUIRED"})
    sp_sum = {}
    for fl in A.FLOORS:
        c = Counter(r["class"] for r in B["ps"] if r["floor"] == fl)
        a = defaultdict(float)
        for r in B["ps"]:
            if r["floor"] == fl:
                a[r["class"]] += r["area_m2"]
        sp_sum[fl] = {"count_by_class": dict(sorted(c.items())), "area_m2_by_class": {k: A._r(v, 3) for k, v in sorted(a.items())},
                      "room_like_spaces": c.get("SPACE", 0), "recovered": sum(1 for r in rec_rows if r["floor"] == fl)}
    regs["PHYSICAL_SPACE_REGISTER"] = {"SCHEMA": SCHEMA + "_PHYSICAL_SPACES", "rows": B["ps"] + rec_rows,
                                       "summary": sp_sum,
                                       "rule": "every Route A site is classified from geometry (plate, obstacle, thin "
                                               "band, sliver, room-like) before any label is read; Route B recovers "
                                               "only plate area Route A leaves open"}
    regs["TOPOLOGY_SHADOW_COMPARISON"] = {
        "SCHEMA": SCHEMA + "_TOPOLOGY_SHADOW", "policy": PT.POLICY_ID,
        "route_a": "room_topology_v3 (production; unchanged)",
        "route_b": "planar_shadow_topology: endpoint merge (1 mm) + T / intersection / collinear splitting + dangling peel "
                   "+ half-edge walk + holes; layers 1, W, S-COL.BON, 5; door-swing closures and facing-gap bridges "
                   "(0.30 - 3.60 m) as recorded zero-material closures",
        "summary": B["shadow_summary"], "rows": B["shadow"],
        "rule": "independent validation, not replacement: a disagreement is recorded, never resolved by picking the route "
                "closer to any benchmark"}
    regs["ORPHAN_SEMANTIC_LABEL_REGISTER"] = {"SCHEMA": SCHEMA + "_ORPHANS", "rows": B["orphans"],
                                              "counts": dict(Counter(o["outcome"] for o in B["orphans"])),
                                              "rule": "a label is never deleted; every label outside a Route A space "
                                                      "terminates in one outcome"}
    regs["SEMANTIC_ZONE_REGISTER_V2"] = {"SCHEMA": SCHEMA + "_SEMANTIC_ZONES", "rows": B["zones"],
                                         "counts": dict(Counter(z["class"] for z in B["zones"]))}
    tr_sum = defaultdict(lambda: defaultdict(float))
    for r in regions:
        tr_sum[r["floor"]][r["class"]] += r["area_m2"]
    regs["TRADE_REGION_REGISTER_V2"] = {
        "SCHEMA": SCHEMA + "_TRADE_REGIONS", "rows": regions,
        "area_m2_by_floor_class": {fl: {k: A._r(v, 3) for k, v in sorted(d.items())} for fl, d in sorted(tr_sum.items())},
        "rule": "physical space != semantic zone != trade region; a mixed space splits only along positive source "
                "boundaries (Route B faces); no wall is invented; unlabelled pieces stay UNASSIGNED"}

    # ---------------------------------------------------------------------------------- floor
    floor_tbl = []
    for f in fin["floor"]:
        r = reg_by_id[f["region"]]
        floor_tbl.append({"floor": f["floor"], "region": f["region"], "room": " / ".join(r["labels"]) or r["class"],
                          "class": r["class"], "raw_area_m2": f["raw_area_m2"], "excluded_m2": f.get("excluded_m2", 0.0),
                          "net_area_m2": f["net_area_m2"], "finish_class": f["finish_class"],
                          "internal": f.get("internal", False), "state": f["state"],
                          "source": f"{f['geometry_method']} / {f['semantic_authority']}"})
    fcv = B["fc"]
    for fl, d in fcv["floors"].items():
        internal_sum = sum(x["net_area_m2"] for x in floor_tbl if x["floor"] == fl and x["internal"])
        d["sum_room_zone_internal_m2"] = A._r(internal_sum)
        d["internal_reconciles"] = abs(internal_sum - d["internal_floor_area_m2"]) < 0.01
    regs["FLOOR_AREA_CONSERVATION_REGISTER"] = {
        "SCHEMA": SCHEMA + "_FLOOR_CONSERVATION", "floors": fcv["floors"], "residuals": fcv["residuals"],
        "components": fcv["components"], "room_table": floor_tbl,
        "external_kept_apart": ["GARDEN", "POOL", "COURT", "ROOF terraces", "VOID", "SHAFT"],
        "rule": "registered floor plate = sum of classified components; residual plate area is UNRESOLVED_BLOCKED (listed), "
                "never dropped; external areas never enter internal floor totals"}

    # ---------------------------------------------------------------------------------- wet
    wet_reg = []
    wp_by = {w["region"]: w for w in fin["wp"]}
    tile_by = {t["region"]: t for t in fin["tile"]}
    fl_by = {f["region"]: f for f in fin["floor"]}
    for r in regions:
        if r["class"] not in ("WET", "SERVICE"):
            continue
        sk = next(s for s in fin["skirting"] if s["region"] == r["region_id"])
        wet_reg.append({"region": r["region_id"], "floor": r["floor"], "labels": r["labels"], "class": r["class"],
                        "floor_area_m2": fl_by[r["region_id"]]["net_area_m2"], "perimeter_m": sk["path_total_m"],
                        "wall_face_m": tile_by.get(r["region_id"], {}).get("face_m_total"),
                        "doors": [o["id"] for o in ops if r["region_id"] in o["room_adjacency"]],
                        "floor_ceramic_eligibility": "ELIGIBLE (URBAN-WET-FLOOR-TILED@v1)",
                        "wall_tile_eligibility": "ELIGIBLE (URBAN-WET-WALL-TILE-FULL-HEIGHT@v1)",
                        "wp_eligibility": wp_by.get(r["region_id"], {}).get("eligibility"),
                        "status": r["semantic_state"]})
    regs["WET_SERVICE_COMPLETENESS_REGISTER"] = {
        "SCHEMA": SCHEMA + "_WET_SERVICE", "labels": B["wet"], "regions": wet_reg,
        "counts": dict(Counter(w["state"] for w in B["wet"])),
        "unaccounted": [w for w in B["wet"] if w["state"] not in ("BOUND", "BLOCKED", "NOT_IN_SCOPE", "STALE_WITH_EVIDENCE")],
        "rule": "every wet / service source label is BOUND / BLOCKED / NOT_IN_SCOPE / STALE_WITH_EVIDENCE; the sanitary "
                "drawing corroborates only (not registered this round)"}

    # ---------------------------------------------------------------------------------- walls / blockwork
    pieces = B["pieces"]
    cand = {}
    for fl in A.FLOORS:
        run = B["run"].get(fl, {})
        clos = defaultdict(float)
        for p in pieces:
            if p["floor"] == fl and p["layer"] == "CLOSURE":
                clos[p["class"]] += p["length_m"]
        glaz_w = sum(o["width"]["m"] or 0.0 for o in ops if o["floor"] == fl and o["type"] in ("WINDOW", "GLAZED_DOOR_CANDIDATE"))
        inside = {k: v for k, v in run.items() if k not in ("EXTERNAL_BOUNDARY_NON_WALL", "NOT_WALL")}
        cand[fl] = {"wall_layer_runs_m": inside, "door_closures_m": A._r(clos.get("DOOR_OPENING", 0.0)),
                    "open_transitions_m": A._r(clos.get("OPEN_TRANSITION", 0.0)),
                    "glazed_openings_width_m": A._r(glaz_w),
                    "TOTAL_ARCHITECTURAL_WALL_CANDIDATE_LENGTH_m": A._r(sum(inside.values()) + clos.get("DOOR_OPENING", 0.0)
                                                                        + clos.get("OPEN_TRANSITION", 0.0) + glaz_w)}
    regs["WALL_SEGMENT_LEDGER_V2"] = {
        "SCHEMA": SCHEMA + "_WALL_LEDGER", "classes": list(AQ.WALL_CLASSES), "ledger_check": B["ledger_check"],
        "admitted_m": {k: A._r(v) for k, v in sorted(B["admitted"].items())},
        "face_line_m_by_floor_class": B["face_by"], "wall_run_centreline_m_by_floor_class": B["run"],
        "total_wall_candidate_by_floor": cand,
        "pieces": [{k: (A._r(v) if isinstance(v, float) else v) for k, v in p.items()
                    if k not in ("a", "b", "centre_a", "centre_b")} for p in pieces],
        "rule": "every admitted candidate (wall / column / glazing / thin-line parts + zero-material closures) is split "
                "into pieces and each piece terminates in exactly one class; masonry needs paired faces + the wall "
                "layer + a structural cross-check (thickness alone = BLOCKED_MATERIAL); unaccounted length = 0"}
    bl = {}
    for fl in A.FLOORS:
        run = B["run"].get(fl, {})
        bl[fl] = {"MASONRY_100_m": A._r(run.get("MASONRY_100", 0.0)), "MASONRY_150_m": A._r(run.get("MASONRY_150", 0.0)),
                  "MASONRY_200_m": A._r(run.get("MASONRY_200", 0.0)), "OTHER_MASONRY_m": A._r(run.get("OTHER_MASONRY", 0.0)),
                  "BLOCKED_MATERIAL_m": A._r(run.get("BLOCKED_MATERIAL", 0.0)),
                  "AMBIGUOUS_BLOCKED_m": A._r(run.get("AMBIGUOUS_BLOCKED", 0.0)),
                  "RC_IN_BAND_m": A._r(run.get("RC_COLUMN_INTERFACE", 0.0)),
                  "EXCLUDED_m": A._r(run.get("EXCLUDED_WITH_REASON", 0.0)),
                  "material_state": AQ.PROV,
                  "material_authority": "ARCH_WALL_LAYER + STRUCTURAL_NEGATIVE (registered, not an RC element) + "
                                        "URBAN_CONVENTION (non-structural villa walls are concrete block) - no block "
                                        "label / legend in the source",
                  "release": AQ.LB if run.get("AMBIGUOUS_BLOCKED") or run.get("BLOCKED_MATERIAL") else AQ.PROV}
    regs["BLOCKWORK_LENGTH_REGISTER_V2"] = {
        "SCHEMA": SCHEMA + "_BLOCKWORK_LENGTH", "floors": bl,
        "reconciliation": "wall-layer run = masonry 100 / 150 / 200 / other + RC in band + blocked material + ambiguous "
                          "+ excluded (inside the plate); openings / transitions / glazing are separate candidates "
                          "(WALL_SEGMENT_LEDGER_V2.total_wall_candidate_by_floor)",
        "rule": "unresolved segments never become blockwork"}
    bw = B["bw"]
    agg = defaultdict(lambda: defaultdict(float))
    for r in bw:
        if r["net_m2"] is not None:
            agg[r["floor"]][f"{r['class']}|{r['state']}"] += r["net_m2"]
        else:
            agg[r["floor"]][f"{r['class']}|BLOCKED_LENGTH_m"] += r["length_m_half_band"]
    regs["BLOCKWORK_AREA_REGISTER_V2"] = {
        "SCHEMA": SCHEMA + "_BLOCKWORK_AREA",
        "by_floor": {fl: {k: A._r(v, 3) for k, v in sorted(d.items())} for fl, d in sorted(agg.items())},
        "over_under_openings": B["over"], "rows": bw,
        "rule": "net masonry = band length x height per piece (storey interval - terminating beam / slab depth from the "
                "registered framing); bands stop at openings and RC (never masonry behind RC); masonry over / under "
                "openings separate (needs the opening height); one global height is never used"}
    regs["OPENING_EVIDENCE_REGISTER_V3"] = {
        "SCHEMA": SCHEMA + "_OPENINGS_V3", "rows": ops, "height_ladder": list(AQ.HEIGHT_LADDER),
        "counts": {k: dict(Counter((o[k]["state"] if isinstance(o[k], dict) else o[k]) for o in ops))
                   for k in ("count", "width", "height", "area", "function", "material")},
        "types": dict(Counter(o["type"] for o in ops)),
        "height_authority": dict(Counter(o["height"]["authority"] for o in ops)),
        "rule": "count / width / height / function / material / host / adjacency each carry their own state; area only "
                "with width AND height; NO DEFAULT WINDOW HEIGHT; a glazed door candidate is never collapsed"}

    # ---------------------------------------------------------------------------------- finishes
    regs["FLOOR_FINISH_REGISTER_V2"] = {
        "SCHEMA": SCHEMA + "_FLOOR_FINISH", "rows": fin["floor"],
        "internal_m2_by_finish_state": {fc_: _sum(fin["floor"], "net_area_m2", lambda r, fc_=fc_: r.get("internal") and
                                                  r["finish_class"] == fc_)
                                        for fc_ in sorted({f["finish_class"] for f in fin["floor"]})},
        "internal_m2_by_floor": _by_floor(fin["floor"], "net_area_m2", lambda r: r.get("internal")),
        "external_m2": _sum(fin["floor"], "net_area_m2", lambda r: not r.get("internal") and r["finish_class"] != "NONE"),
        "rule": "quantity state and material state are separate (an area may be VERIFIED with material BY_SPEC)"}
    regs["CEILING_AREA_REGISTER_V2"] = {
        "SCHEMA": SCHEMA + "_CEILING", "rows": fin["ceiling"], "by_floor": _by_floor(fin["ceiling"], "area_m2"),
        "rule": "a ceiling needs a physical ceiling plane: void / external / shaft / stair well excluded; the part under "
                "a double-height void of the storey above is excluded"}
    regs["SKIRTING_PATH_REGISTER_V3"] = {
        "SCHEMA": SCHEMA + "_SKIRTING", "rows": fin["skirting"],
        "included_m": _sum(fin["skirting"], "included_m"), "blocked_m_total": A._r(sum(s["blocked_m"] for s in fin["skirting"])),
        "rule": "boundary path, not a room perimeter: doors / open passages / full-height glazing / void / zone splits "
                "excluded; windows continuous; wet full-tile rooms none; hidden skirting and hidden profile same path"}
    regs["WATERPROOFING_REGISTER_V2"] = {
        "SCHEMA": SCHEMA + "_WATERPROOFING", "rows": fin["wp"],
        "floor_membrane_m2": _sum(fin["wp"], "floor_membrane_m2"), "upturn_path_m": _sum(fin["wp"], "upturn_path_m"),
        "roof": "separate roof method (URBAN-ROOF-WATERPROOF-UPTURN-200@v1) - not re-measured this round",
        "rule": "verified wet regions only; 0.15 m upturn along the gross boundary; doorways do not interrupt the upturn"}
    regs["WALL_TILE_REGISTER_V2"] = {
        "SCHEMA": SCHEMA + "_WALL_TILE", "rows": fin["tile"], "net_m2": _sum(fin["tile"], "net_m2"),
        "rule": "wet / service regions only; full height to the finished ceiling; established openings deducted; reveals "
                "0.25 m left / right / head (no sill) only where the opening and its host are established"}
    pp = fin["plaster_paint"]
    regs["PLASTER_PAINT_REGISTER_V2"] = {
        "SCHEMA": SCHEMA + "_PLASTER_PAINT", "rows": pp, "faces": fin["faces"],
        "plaster_net_m2": {s: round(sum(r["plaster"]["net_m2"] for r in pp if r["plaster"]["state"] == s and r["plaster"].get("net_m2") is not None), 3)
         for s in sorted({r["plaster"]["state"] for r in pp})},
        "paint_net_m2": {s: round(sum(r["paint"]["net_m2"] for r in pp if r["paint"]["state"] == s and r["paint"].get("net_m2") is not None), 3)
                         for s in sorted({r["paint"]["state"] for r in pp})},
        "METHOD_SENSITIVITY_REGISTER": fin["sensitivity"],
        "external_facade": B["facade"],
        "rule": "plaster to the masonry termination and paint to the finished ceiling (two heights); a full wet-tiled face "
                "gets no plaster / paint; unresolved height publishes MEASURED GEOMETRY x UNRESOLVED HEIGHT"}
    regs["STAIR_ARCHITECTURAL_REGISTER"] = dict({"SCHEMA": SCHEMA + "_STAIRS"}, **B["stairs"])

    # ---------------------------------------------------------------------------------- conservation
    viol = []
    for fl, d in fcv["floors"].items():
        if abs(d["conservation"]["unaccounted_m2"]) > 0.05:
            viol.append(("FLOOR_PLATE_NOT_CONSERVED", fl, d["conservation"]["unaccounted_m2"]))
        if not d["internal_reconciles"]:
            viol.append(("INTERNAL_AREA_NOT_RECONCILED", fl))
    if B["ledger_check"]["violations"] or abs(B["ledger_check"]["unaccounted_m"]) > 1e-3:
        viol.append(("WALL_LENGTH_NOT_CONSERVED", B["ledger_check"]["unaccounted_m"]))
    if len(ops) != len(r2):
        viol.append(("OPENING_COUNT_NOT_CONSERVED", len(ops), len(r2)))
    if regs["WET_SERVICE_COMPLETENESS_REGISTER"]["unaccounted"]:
        viol.append(("WET_LABEL_UNACCOUNTED",))
    for s in fin["skirting"]:
        if abs(s["included_m"] + s["blocked_m"] + sum(s["excluded_m_by_reason"].values()) - s["path_total_m"]) > 1e-4:
            viol.append(("SKIRTING_PATH_NOT_CONSERVED", s["region"]))
    fids = [f["id"] for f in fin["faces"]]
    if len(fids) != len(set(fids)):
        viol.append(("WALL_FACE_DOUBLE_COUNTED",))
    for fl in A.FLOORS:
        rs = [r for r in regions if r["floor"] == fl]
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                if rs[i]["_poly"].intersection(rs[j]["_poly"]).area > 1e4:
                    viol.append(("REGION_OVERLAP", rs[i]["region_id"], rs[j]["region_id"]))
    neg = []
    for name, rows, key in (("floor", fin["floor"], "net_area_m2"), ("ceiling", fin["ceiling"], "area_m2"),
                            ("skirting", fin["skirting"], "included_m"), ("wp", fin["wp"], "floor_membrane_m2"),
                            ("tile", fin["tile"], "net_m2"), ("blockwork", bw, "net_m2")):
        neg += [(name, r.get("region") or r.get("piece")) for r in rows if isinstance(r.get(key), (int, float)) and r[key] < -1e-9]
    viol += [("NEGATIVE_QUANTITY",) + n for n in neg]
    xt = AQ.cross_trade_check(
        regions=[{"id": r["region_id"], "indoor": r["indoor"] and r["class"] not in ("VOID", "SHAFT"),
                  "internal_area_m2": r["area_m2"] if r["indoor"] and r["class"] not in ("VOID", "SHAFT", "EXTERNAL") else 0,
                  "wet": r["class"] in ("WET", "SERVICE"),
                  "trades": {**({"FLOOR_FINISH": {"qty": fl_by[r["region_id"]]["net_area_m2"]}}),
                             **({"CEILING": {"qty": 0}} if any(c["region"] == r["region_id"] for c in fin["ceiling"]) else {}),
                             **({"WATERPROOFING": {"qty": wp_by[r["region_id"]]["floor_membrane_m2"]}}
                                if r["region_id"] in wp_by else {}),
                             **({"WALL_TILE": {"qty": tile_by[r["region_id"]].get("net_m2")}} if r["region_id"] in tile_by else {})}}
                 for r in regions],
        openings=[{"id": o["id"], "count_state": o["count"]["state"], "area_m2": o["area"]["area_m2"],
                   "width_state": o["width"]["state"], "height_state": o["height"]["state"]} for o in ops],
        walls=[{"id": p["piece_id"], "class": p["class"],
                "blockwork_length_m": p["length_m"] if p["class"] in AQ.MASONRY_CLASSES else 0.0} for p in pieces],
        faces=[{"id": f["id"], "treatments": f.get("treatments")} for f in fin["faces"]])
    viol += [("CROSS_TRADE",) + tuple(x) for x in xt]
    wet_src = [f"{fl}|{l['occurrence']}" for fl, F in Fs.items() for l in F.labels
               if l["class"] in ("WET", "SERVICE") or "swimming" in (l["text_en"] or "").lower()]
    mut_checks = {
        "region_class": AQ.region_class_check(regions),
        "wet_label_conservation": AQ.label_conservation(wet_src, [{"occurrence": f"{w['floor']}|{w['occurrence']}"}
                                                                  for w in B["wet"]]),
        "masonry_identity": AQ.masonry_identity_check(pieces),
        "masonry_through_rc": AQ.masonry_rc_check(pieces, lambda p: bool(p.get("rc_at_centre"))),
        "opening_function": AQ.opening_function_check(ops),
        "skirting_segments": AQ.skirting_check([sg for s in fin["skirting"] for sg in s["segments"]]),
        "height_consistency": AQ.height_consistency(fin["faces"]),
        "internal_floor": AQ.internal_floor_check(fin["floor"]),
        "face_uniqueness": AQ.face_uniqueness(fin["faces"])}
    for k, v in mut_checks.items():
        viol += [(k.upper(),) + tuple(x) for x in v]
    prov_rows = [r for r in fin["floor"] + fin["ceiling"] + fin["skirting"] + fin["wp"] + fin["tile"] + pp]
    prov_ok = sum(1 for r in prov_rows if all(r.get(k) for k in ("drawing", "revision", "floor", "region",
                                                                    "semantic_authority", "geometry_method")))
    xdisc = []
    for fl, d in fcv["floors"].items():
        if abs(d["plate_minus_architect_m2"]) > 1.0:
            xdisc.append({"type": "CROSS_DISCIPLINE_FINDING", "floor": fl,
                          "finding": f"structural slab outline {d['plate_m2']} m2 vs architect area sheet "
                                     f"{d['architect_area_sheet_m2']} m2 (difference {d['plate_minus_architect_m2']} m2)",
                          "action": "future structural round: slab edge / cantilever vs the permit area polygon"})
    regs["ARCHITECTURAL_QUANTITY_CONSERVATION_REGISTER"] = {
        "SCHEMA": SCHEMA + "_CONSERVATION", "violations": viol, "pass": not viol,
        "checks": ["floor plate", "internal area reconciliation", "wall length (ledger)", "opening count",
                   "wet-label terminal states", "skirting path conservation", "wall-face single treatment",
                   "no region overlap (no double-counted region)", "no negative quantity", "cross-trade completeness"]
                  + list(mut_checks),
        "mutation_proof_checks": {k: {"violations": v, "pass": not v} for k, v in mut_checks.items()},
        "provenance": {"quantity_rows": len(prov_rows), "rows_with_full_provenance": prov_ok,
                       "coverage_pct": round(100.0 * prov_ok / len(prov_rows), 3) if prov_rows else 100.0},
        "cross_discipline_findings": xdisc,
        "silent_disappearances": len([1 for v in viol if v[0] in ("FLOOR_PLATE_NOT_CONSERVED", "WALL_LENGTH_NOT_CONSERVED",
                                                                   "OPENING_COUNT_NOT_CONSERVED", "WET_LABEL_UNACCOUNTED")])}

    # ---------------------------------------------------------------------------------- review queue
    q = []
    for r in regions:
        if r["class"] == "MIXED_UNRESOLVED":
            q.append({"object": r["region_id"], "impact_m2": r["area_m2"], "kind": "MIXED_ZONE",
                      "decision": f"where does the {' / '.join(sorted(set(r['labels']) & {'Wash'})) or 'wet'} zone end inside "
                                  f"{' / '.join(r['labels'])}? (floor finish, skirting, paint, wall tile)"})
    for u in fcv["residuals"]:
        if u["area_m2"] >= 1.0:
            q.append({"object": u["id"], "impact_m2": u["area_m2"], "kind": "UNCLOSED_PLATE_AREA",
                      "decision": f"close plate area at {u['point']} ({', '.join(u['labels_inside']) or 'unlabelled'}): "
                                  f"which opening / wall bounds it?"})
    un = [r for r in regions if r["class"] in ("UNKNOWN", "UNASSIGNED", "STAIR") and r["area_m2"] >= 1.0]
    for r in sorted(un, key=lambda z: -z["area_m2"])[:6]:
        q.append({"object": r["region_id"], "impact_m2": r["area_m2"], "kind": "UNLABELLED_REGION",
                  "decision": "name / class of this region (corridor, stair hall, lobby ...)"})
    mas = sum(v for d in B["run"].values() for k, v in d.items() if k.startswith("MASONRY"))
    q.append({"object": "ALL_MASONRY_BANDS", "impact_m": round(mas, 2), "impact_m2": round(sum(r["net_m2"] or 0 for r in bw), 2),
              "kind": "MATERIAL_IDENTITY", "decision": "confirm that the paired walls on the architectural wall layer that "
                                                       "are not RC are concrete block (150 / 200) - releases blockwork "
                                                       "from PROVISIONAL"})
    gdc = [o for o in ops if o["type"] == "GLAZED_DOOR_CANDIDATE"]
    q.append({"object": "GLAZED_DOOR_CANDIDATES", "impact_count": len(gdc), "impact_m": round(sum(o["width"]["m"] or 0 for o in gdc), 2),
              "kind": "OPENING_FUNCTION", "decision": "window or full-height glazed door? (skirting continuity, opening area)"})
    nh = [o for o in ops if o["height"]["state"] == AQ.BLK]
    q.append({"object": "OPENINGS_WITHOUT_HEIGHT", "impact_count": len(nh), "impact_m": round(sum(o["width"]["m"] or 0 for o in nh), 2),
              "kind": "OPENING_HEIGHT", "decision": "door / window schedule or elevation dimensions for these openings"})
    q.append({"object": "FINISHED_CEILING_LEVEL", "impact_m2": round(sum(r["paint"].get("net_m2") or 0 for r in pp) +
                                                               sum(t.get("net_m2") or 0 for t in fin["tile"]), 2),
              "kind": "HEIGHT_METHOD", "decision": "finished ceiling level / floor build-up (paint and wall tile heights "
                                                   "use the Urban fallback 0.10 m + 0.150 allowance)"})
    q.sort(key=lambda z: -(z.get("impact_m2") or 0) - (z.get("impact_m") or 0) * 0.5)
    regs["ARCHITECTURAL_REVIEW_QUEUE"] = {"SCHEMA": SCHEMA + "_REVIEW_QUEUE", "items": q[:12],
                                          "rule": "the smallest set of decisions releasing the largest quantity; ranked by "
                                                  "quantity impact"}

    # ---------------------------------------------------------------------------------- scorecard
    plate = sum(d["plate_m2"] for d in fcv["floors"].values())
    unres = sum(u["area_m2"] for u in fcv["residuals"])
    internal = [f for f in fin["floor"] if f.get("internal")]
    ia = sum(f["net_area_m2"] for f in internal)
    sem_ok = sum(f["net_area_m2"] for f in internal if f["cls"] in ("DRY", "WET", "SERVICE", "STAIR"))
    ivc = sum(f["net_area_m2"] for f in internal if f["state"] == AQ.VC)
    cel = [c for c in fin["ceiling"] if c["state"] != AQ.NIS]
    cel_vc = sum(c["area_m2"] or 0 for c in cel if c["state"] == AQ.VC)
    cel_all = sum(reg_by_id[c["region"]]["area_m2"] for c in cel)
    dry_regions = [s for s in fin["skirting"] if s["cls"] == "DRY"]
    sk_tot = sum(s["path_total_m"] for s in dry_regions)
    sk_ok = sum(s["included_m"] + sum(s["excluded_m_by_reason"].values()) for s in dry_regions)
    wetb = [w for w in B["wet"] if w["state"] == "BOUND"]
    face_all = fin["faces"]
    face_ok = [f for f in face_all if (f.get("plaster_h") is not None or f.get("tile_h") is not None) and
               not any(t.endswith("BLOCKED") for t in f.get("treatments") or [])]
    wall_inside = sum(v for d in B["run"].values() for k, v in d.items() if k not in ("EXTERNAL_BOUNDARY_NON_WALL", "NOT_WALL"))
    wall_interp = sum(v for d in B["run"].values() for k, v in d.items()
                      if k not in ("EXTERNAL_BOUNDARY_NON_WALL", "NOT_WALL", "AMBIGUOUS_BLOCKED", "BLOCKED_MATERIAL"))
    blocked_impact = {"floor_area_class_blocked_m2": round(sum(f["net_area_m2"] for f in internal
                                                               if f["cls"] in ("MIXED_UNRESOLVED", "UNASSIGNED", "UNKNOWN")), 3),
                      "unresolved_plate_m2": round(unres, 3),
                      "skirting_blocked_m": regs["SKIRTING_PATH_REGISTER_V3"]["blocked_m_total"],
                      "openings_area_blocked": sum(1 for o in ops if o["area"]["state"] == AQ.BLK),
                      "ambiguous_wall_m": round(sum(d.get("AMBIGUOUS_BLOCKED", 0) for d in B["run"].values()), 3)}
    regs["ARCH_ACCURACY_SCORECARD_V3"] = {
        "SCHEMA": SCHEMA + "_SCORECARD_V3",
        "metrics": {
            "physical_space_accounting_pct": round(100.0 * (plate - unres) / plate, 3),
            "physical_space_accounting_incl_blocked_residual_pct": 100.0,
            "physical_space_geometry_confidence_pct": round(100.0 * sum(r["area_m2"] for r in B["ps"]
                                                                        if r["class"] == "SPACE" and r["closure_confidence"] == "CERTIFIED") /
                                                            max(sum(r["area_m2"] for r in B["ps"] if r["class"] == "SPACE"), 1e-9), 3),
            "semantic_zone_coverage_pct": round(100.0 * sem_ok / ia, 3),
            "trade_region_coverage_pct": round(100.0 * sem_ok / ia, 3),
            "wet_room_accounting_pct": 100.0 if not regs["WET_SERVICE_COMPLETENESS_REGISTER"]["unaccounted"] else 0.0,
            "wet_room_bound_pct": round(100.0 * len(wetb) / max(1, len([w for w in B["wet"] if w["state"] != "NOT_IN_SCOPE"])), 3),
            "wall_length_accounting_pct": round(100.0 * B["ledger_check"]["classified_m"] / B["ledger_check"]["admitted_m"], 3),
            "wall_material_interpretation_pct": round(100.0 * wall_interp / wall_inside, 3),
            "opening_count_coverage_pct": 100.0,
            "opening_area_coverage_pct": round(100.0 * sum(1 for o in ops if o["area"]["area_m2"] is not None) / len(ops), 3),
            "floor_quantity_completeness_pct": round(100.0 * ivc / ia, 3),
            "ceiling_quantity_completeness_pct": round(100.0 * cel_vc / max(cel_all, 1e-9), 3),
            "skirting_path_completeness_pct": round(100.0 * sk_ok / max(sk_tot, 1e-9), 3),
            "wall_tile_completeness_pct": round(100.0 * sum(1 for t in fin["tile"] if t.get("net_m2") is not None) /
                                                max(1, len(fin["tile"])), 3),
            "wp_completeness_pct": round(100.0 * len(fin["wp"]) / max(1, len([r for r in regions if r["class"] in ("WET", "SERVICE")])), 3),
            "plaster_paint_completeness_pct": round(100.0 * len(face_ok) / max(1, len(face_all)), 3),
            "provenance_coverage_pct": regs["ARCHITECTURAL_QUANTITY_CONSERVATION_REGISTER"]["provenance"]["coverage_pct"],
            "blocked_quantity_impact": blocked_impact},
        "rule": "separate metrics; no single aggregate accuracy number"}
    return regs, B


GATES = [
    ("A01", "every admitted architectural source object terminates (coverage register, 5 states)"),
    ("A02", "floor plate conserved per floor; residual listed as UNRESOLVED_BLOCKED"),
    ("A03", "wall ledger: every admitted piece one class, unaccounted length 0"),
    ("A04", "masonry never from thickness alone"),
    ("A05", "mixed zone never fully DRY; split only along positive source boundaries"),
    ("A06", "orphan labels never deleted (terminal outcome each)"),
    ("A07", "opening area only with width AND height; no default window height; glazed door candidate kept"),
    ("A08", "skirting excludes doors / voids / zone splits; wet full-tile rooms none"),
    ("A09", "every wet region has floor + WP + wall-tile records"),
    ("A10", "no face both fully tiled and plastered / painted"),
    ("A11", "external areas never in internal floor totals"),
    ("A12", "Route B is shadow only; disagreements recorded"),
]


def main(src, twice=False):
    ctx = pickle.load(open(src, "rb"))
    regs, B = registers(ctx)
    texts = {k: _text(v) for k, v in regs.items()}
    if twice:
        again, _ = registers(ctx)
        diff = [k for k, v in again.items() if _text(v) != texts[k]]
        if diff:
            raise SystemExit(f"REFUSED: build not deterministic: {diff}")
    OUT.mkdir(parents=True, exist_ok=True)
    for k, t in texts.items():
        (OUT / f"{k}.json").write_text(t)
    idx = {"SCHEMA": SCHEMA + "_INDEX",
           "files": {k: hashlib.sha256(t.encode()).hexdigest() for k, t in texts.items()},
           "gates": [{"gate": g, "statement": s} for g, s in GATES],
           "p7757_dxf_revision": B["Fs"]["GF"].inp.revision.revision_id,
           "p7757_dxf_anchor_sha256": B["Fs"]["GF"].inp.revision.anchor_sha256,
           "frozen_before_benchmark": True, "built_twice_identical": bool(twice)}
    (OUT / "INDEX.json").write_text(json.dumps(idx, indent=1) + "\n")
    print(f"wrote {len(texts)} registers; conservation pass = {regs['ARCHITECTURAL_QUANTITY_CONSERVATION_REGISTER']['pass']}")
    return regs


if __name__ == "__main__":
    main(sys.argv[1], "--twice" in sys.argv)
