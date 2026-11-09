"""T-555 WIRING MANIFEST V5: the T-549 manifest (V4, pinned) extended by EVERY piece merged after it, up to the pinned
V5 base, on the candidate of record ARCH_TAKEOFF_V3.0.58. Research / integration preparation only (lane I,
non-candidate): nothing here writes a candidate, released, rule, knowledge or registry file; nothing is wired.

Coverage by R-T549-1 (reused, V4's own check_coverage): range (V4 base 3f3b580c, V5 base 47d74505] on the first-parent
line of the working branch; every 'Merge agents/task-T-<n>' in it is a source with that merge commit, or a declared
NO_WIRING piece with its reason. The range is pinned: a later merge belongs to V6.

What V5 changes against V4, each from the merged piece's own committed output or its own function (no quantity typed):
  - T-544 R-T544-1 (part 1): the 1F white AAC 0.20 glue host L-2fdc0f97 goes from HELD blank (AT_MOST 451.60893 kg) to
    BOUNDED_EXPOSURE 437.88303 .. 451.60893 kg; the AAC glue group from AT_LEAST 17.643906 .. 18.16227 to a larger
    known part.
  - T-544 part 2: the legacy R-T498-1 low ends of GF L-541cf721 and 1F L-b7b4d784 are no bound (F-T537-1); their T-453
    glue bindings and their T-498 stage glue lines go stale; 2F L-bbb82de2 stays HELD (contract HELD, STALE_CLASS).
    Group with every FRESH host moved: AT_LEAST 34.891351 .. 36.226627 bags, HELD.
  - T-544 lintel ends: the 4 (+13) HELD lintels stay HELD (existence, D-45); their concrete ceilings sit beside.
  - T-552: candidate DRY FIN.PLASTER room lines are at the PAINT height (ENGINE_WRONG vs owner Q-72 / 2 Nov): a
    correction with no owning package yet; the T-454 / T-489 plaster material bindings that read them go stale.
  - T-545 / T-546 / T-547 / T-554: reconciliations / statement, no line moves; each engine side re-checked against the
    candidate (F-T549-1 lesson: a reconciliation names whether its engine side is the candidate).
  - T-549: the V4 manifest itself, superseded here.
Every source commit must be an ancestor of HEAD (manifest_t536.check_sources). No private drawing is read here.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(rel, name):
    p = ROOT / rel
    if str(p.parent) not in sys.path:
        sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M4 = _load("research/agents_t549/manifest_v4.py", "manifest_v4_t555")             # read only
M3, M2, M1 = M4.M3, M4.M2, M4.M1
ManifestError = M4.ManifestError
_r, sha256 = M1._r, M1.sha256

SCHEMA = "URBAN_T555_WIRING_MANIFEST_V5"
OUT_JSON = ROOT / "research/agents_t555/WIRING_MANIFEST_V5.json"
V4_JSON = M4.OUT_JSON
V4_PIN = "b0a8c6736122522e44690f9b49d2781eb1508cf8be3514f472cc169d5e5fc387"     # the merged V4 (f91e917f)

T544_APPLY = "research/agents_t544/t544_apply.py"
T545 = ROOT / "research/agents_t545/out/T545_BEAM_RECONCILE.json"
T546_INPUTS = "research/agents_t546/t546_inputs.py"
T547 = ROOT / "research/agents_t547/out/WALL_TILE_RECONCILE_T547.json"
T552 = ROOT / "research/agents_t552/out/T552_PLASTER_RECONCILE.json"
T554 = ROOT / "research/agents_t554/out/RECONCILED_STATEMENT_T554.json"
T523_MAP = "research/agents_t523/t523_binding_map_v2.py"

V4_BASE = M4.V4_BASE          # 3f3b580c Merge agents/task-T-542
V5_BASE = "47d74505"          # Merge agents/task-T-547 (the newest merge when T-555 was claimed)

NEW_PIECES = {
    "T-544": {"merge": "2dbfaf95", "gate": "A", "rules": ["R-T544-1"],
              "verdict": "Verifier 2026-11-06 ~04:00Z GATE A PASS: own raw-DXF re-measure 8 / 8 ends AGREE <= 0.1 mm "
                         "(1F), GF part 2 8 / 8 AGREE; 1F glue host RANGE, line stays HELD; PARTIAL 16 / 34 ends"},
    "T-545": {"merge": "e533bc87", "gate": "A", "rules": ["R-T545-1", "R-T545-2", "R-T545-3"],
              "verdict": "Verifier 2026-11-06 05:58Z GATE A PASS: beam concrete vs the freelancer by component; COUNT "
                         "ENGINE_RIGHT (B27 own hand); no line status changes"},
    "T-546": {"merge": "a615fa41", "gate": "A", "rules": ["R-T546-1"],
              "verdict": "Verifier 2026-11-06 ~04:15Z GATE A PASS: wet-room floor WP room by room; engine side from "
                         "LINE_INDEX_V3_0_57 AGREE; his upturn is a length (F-T546-1)"},
    "T-547": {"merge": "47d74505", "gate": "A", "rules": ["R-T547-1"],
              "verdict": "Verifier 2026-11-06 06:56Z GATE A PASS: wall tile 340.3038 vs 433.83 m2, residual 0; "
                         "FIN.WALL.TILE PARTIALLY VERIFIED"},
    "T-549": {"merge": "f91e917f", "gate": "A", "rules": ["R-T549-1"],
              "verdict": "Verifier 2026-11-06 ~04:10Z GATE A PASS: WIRING MANIFEST V4; STALE ON MERGE for T-544 -> V5"},
    "T-552": {"merge": "0106dbfb", "gate": "A", "rules": ["R-T552-1"],
              "verdict": "Verifier 2026-11-06 05:58Z GATE A PASS: wall plaster by face class; height basis ENGINE_WRONG "
                         "(candidate plaster = paint height, own check); +146.41 .. +171.23 m2 HELD"},
    "T-554": {"merge": "82136421", "gate": "A", "rules": ["R-T554-1"],
              "verdict": "Verifier 2026-11-06 05:58Z GATE A PASS: statement adapters T-543 / T-546 / T-542 + "
                         "F-C-T548-1 / F-C-T543-1 corrections; no quantity moves"},
}
NO_WIRING = {
    "T-545": "reconciliation vs the freelancer: moves no line; engine side = the candidate STR.CONC.BEAM lines (checked)",
    "T-546": "reconciliation vs the freelancer: moves no line; engine side = the candidate FIN.WP.FLOOR / WALL_UPTURN",
    "T-547": "reconciliation vs the freelancer: moves no line; engine side = the candidate FIN.WALL.TILE lines",
    "T-549": "the V4 manifest itself: superseded by this V5 (every V4 statement carried unless listed in v4_to_v5)",
    "T-554": "statement builder adapters: moves no line; its F-C-T548-1 ENGINE_WRONG is the V4 MS1-LD landing (T-502)",
}
PIECES = dict(M4.PIECES, **NEW_PIECES)

# T-498 stage glue lines on the five white AAC hosts: ids only, from agents/task-T-498 @ e3e2ebb5
# (research/agents_t498/summary_t498.json; no figure read). Checked by stage_ids_check when the branch is fetched.
STAGE_GLUE = {"L-2fdc0f971a94348ec855": "L-4b9a29d424ea40e0af8a", "L-a3f88ecda2402f67c500": "L-d14c6c9b738045c797ec",
              "L-541cf7210e52db0498bb": "L-6989349aef1cd4fa0940", "L-b7b4d784fbe7fdbebe84": "L-aa5532bb971eceac1b76",
              "L-bbb82de298fecbafa11d": "L-4ccc5dc26bd2472b03ad"}
STAGE_REF = "e3e2ebb5"
LINTEL_LINES = {"W16": "L-53ef44d8c490d1341b93", "W19": "L-6057028f3f666538a007", "W20": "L-6692d02cd6cd25120300",
                "W24": "L-40e8c2597de12644e8e2"}


def v4_manifest():
    if sha256(V4_JSON) != V4_PIN:
        raise ManifestError(f"PIN: {V4_JSON.name} sha256 {sha256(V4_JSON)[:8]} is not the pinned {V4_PIN[:8]}")
    return json.loads(V4_JSON.read_text(encoding="utf-8"))


def _src(*tids):
    return [{"task": t, "merge": PIECES[t]["merge"], "checker": PIECES[t]["verdict"]} for t in tids]


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _t523():
    return _load(T523_MAP, "t523_for_t555").run()


# ------------------------------------------------------------------------------------------------- T-544 glue hosts
def glue_hosts(v4, t544=None):
    """V4 -> V5 per white AAC glue host (contract line, its T-498 stage line): T-544 part 1 + part 2 + the group."""
    t = t544 if t544 is not None else _load(T544_APPLY, "t544_apply_t555").build_all()
    p1 = t["part1"]
    v4h = {h["host_line_id"]: h for h in v4["host_faces"]["hosts"]}
    host = p1["host_line_id"]
    if v4h[host]["v4_expected_after"]["glue_kg"]["state"] != "HELD":
        raise ManifestError(f"{host}: V4 did not hold the 1F host blank (T-544 'before' disagrees)")
    if p1["before_t537_r2"]["glue_kg"] != v4h[host]["v4_expected_after"]["glue_kg"]:
        raise ManifestError(f"{host}: T-544 'before' is not the V4 expectation")
    rows = []
    g1 = p1["after"]["glue_kg"]
    if g1["state"] == "HELD" or g1["range"] is None or g1["range"][0] > g1["range"][1]:
        raise ManifestError(f"{host}: T-544 after is not a bounded range")
    rows.append({"host_line_id": host, "t498_stage_line": STAGE_GLUE[host], "contract_net_m2": p1["contract_net_m2"],
                 "kg_per_m2": p1["kg_per_m2"], "v4_expected_after": v4h[host]["v4_expected_after"]["glue_kg"],
                 "v5_expected_after": {"base_m2": p1["after"]["base"]["base_m2"], "glue_kg": g1,
                                       "bags_25kg_net": p1["after"]["bags_25kg_net"]},
                 "face_sum_m2": p1["after"]["base"]["face_sum_m2"], "stale": True, "part": 1,
                 "cause": "R-T544-1: the 4 held lintel ends measured (ceilings rounded up, shared piers once)"})
    gf = [h for k, h in v4h.items() if k != host]
    for h in gf:
        rows.append({"host_line_id": h["host_line_id"], "t498_stage_line": STAGE_GLUE[h["host_line_id"]],
                     "contract_net_m2": h["contract_net_m2"], "kg_per_m2": h["kg_per_m2"],
                     "v4_expected_after": h["v4_expected_after"]["glue_kg"],
                     "v5_expected_after": {"base_m2": h["v4_expected_after"]["base_m2"],
                                           "glue_kg": h["v4_expected_after"]["glue_kg"],
                                           "bags_25kg_net": h["v4_expected_after"]["bags_25kg_net"]},
                     "stale": False, "part": None, "cause": "unchanged by V5 pieces (T-537 r2 as in V4)"})
    for r in t["part2"]:
        lid = r["host_line_id"]
        moved = r["group_member_moved"]
        a = r["after"]
        if a["glue_kg"]["range"][1] != r["before_t453_r1"]["glue_kg"][1]:
            raise ManifestError(f"{lid}: T-544 part 2 moved the HIGH end (only the legacy low end may move)")
        rows.append({"host_line_id": lid, "t498_stage_line": STAGE_GLUE[lid], "contract_net_m2": r["contract_net_m2"],
                     "kg_per_m2": r["kg_per_m2"],
                     "v4_expected_after": {"state": "NOT_STATED", "value": None,
                                           "carried": "T-453 r1 legacy range (R-T498-1) via the T-523 binding",
                                           "legacy_kg_range": r["before_t453_r1"]["glue_kg"]},
                     "v5_expected_after": ({"base_m2": a["base"]["base_m2"], "glue_kg": a["glue_kg"],
                                            "bags_25kg_net": a["bags_25kg_net"]} if moved else
                                           {"glue_kg": {"state": "HELD", "value": None, "range": None,
                                                        "conditional_range_beside": a["glue_kg"]["range"],
                                                        "why": "contract line HELD in the candidate (T-523 "
                                                               "STALE_CLASS, 2F D-39): never a valued group member"}}),
                     "t523_fresh": r["t523_fresh"], "stale": moved, "part": 2,
                     "cause": ("R-T544-1 part 2: the legacy D x (w + 0.80) low end is no bound (F-T537-1); "
                               "high end unchanged" if moved else "stays HELD by name; range beside only")})
    grp = t["glue_group_all"]
    if grp["status"] != "HELD":
        raise ManifestError("the AAC glue group became VALUED: an open member was dropped")
    stale_b = sorted(f"T-453|{r['host_line_id']}|{k}" for r in rows if r["stale"]
                     for k in ("glue_bags_25kg_net", "glue_kg"))
    return {"rule": f"R-T544-1 1.0.0 on R-T498-2 1.0.0 r2", "hosts": rows,
            "glue_group": {"v4_expected_after": v4["host_faces"]["glue_group"]["v4_expected_after"],
                           "v5_expected_after": {k: grp[k] for k in ("status", "at_least", "to_buy_at_least")},
                           "v5_part1_only": {k: p1["glue_group"]["after"][k] for k in ("status", "at_least",
                                                                                        "to_buy_at_least")},
                           "open_members": grp["open"],
                           "why": "the known part grows because the 1F host is bounded and the two FRESH part-2 hosts "
                                  "lose a low end that was no bound; still HELD (losses and open members)"},
            "bindings_stale": stale_b,
            "bindings_stale_new_vs_v4": sorted(set(stale_b) - set(v4["host_faces"]["bindings_stale"])),
            "stage_lines_stale": sorted(r["t498_stage_line"] for r in rows if r["stale"]),
            "source": _src("T-544")}


def lintel_ends(idx, t544=None):
    """the HELD lintel lines whose ends T-544 measured: they stay HELD (existence, D-45); concrete AT_MOST beside."""
    t = t544 if t544 is not None else _load(T544_APPLY, "t544_apply_t555").build_all()
    conc = t["part1"]["beside_concrete_if_built"]
    out = []
    for oid, lid in sorted(LINTEL_LINES.items()):
        l = idx[lid]
        if l["item_code"] != "STR.CONC.LINTEL" or l["element_id"] != f"LINTEL:{oid}" or l["class"] != "HELD":
            raise ManifestError(f"{lid}: not the HELD lintel line of {oid}")
        c = conc[oid]
        out.append({"opening_id": oid, "line_id": lid, "before": {"class": "HELD", "value": None},
                    "after": {"class": "HELD", "value": None, "at_most_beside_m3": c["concrete_m3"][1],
                              "L_ceil_m": c["L_ceil_m"], "B_D_m": c["B_D_m"]},
                    "why": "existence not established (head not printed, D-45): the ceiling bounds a lintel if built; "
                           "never released, never 0"})
    p2 = []
    for r in t["part2"]:
        for oid, s in sorted(r["held_lintels"].items()):
            p2.append({"host_line_id": r["host_line_id"], "opening_id": oid, "L_ceil_m": s["L_ceil_m"],
                       "face_hi_m2": s["face_m2"][1]})
    return {"part1": out, "part2_ceilings": p2, "candidate_lines_moved": 0,
            "why_named": "V2 - V4 stated only the 16 released lintel lines; T-544 bounds 17 held ones beside",
            "source": _src("T-544")}


def stage_ids_check(stage_rows):
    """the T-498 stage glue line on each host is the one STAGE_GLUE names (ids / items only)."""
    found = {r["source_line_id"]: r["line_id"] for r in stage_rows if r["item_code"] == "MAS.GLUE.AAC"}
    bad = sorted(h for h, s in STAGE_GLUE.items() if found.get(h) != s)
    if bad:
        raise ManifestError(f"STAGE: the T-498 glue line of {bad} is not the one this manifest names")
    return sorted(STAGE_GLUE.values())


# ------------------------------------------------------------------------------------------------- T-552 plaster
def plaster_height(idx, bindings=None):
    """T-552 ENGINE_WRONG: the DRY FIN.PLASTER room lines carry the PAINT height. Per line the expected after is T-552's
    corrected net range, HELD (BOUNDED) (build-up b not printed); the plaster material bindings reading them go stale."""
    t = _json(T552)
    q = t["q72_dry_plaster_height"]
    if not q["verdict"].startswith("ENGINE_WRONG"):
        raise ManifestError("T-552 verdict is not ENGINE_WRONG")
    rooms = {r["line_id"]: r for r in t["internal"]["pairs"]["DRY"]["rooms"]}
    rows, rel_before = [], Decimal(0)
    lo_after, hi_after = Decimal(0), Decimal(0)
    for r in q["rows"]:
        lid = r["line_id"]
        l = idx[lid]
        if l["item_code"] != "FIN.PLASTER" or l["class"] != r["state"]:
            raise ManifestError(f"{lid}: not the {r['state']} FIN.PLASTER line T-552 names")
        lo, hi = Decimal(r["corrected_net"][0]), Decimal(r["corrected_net"][1])
        if lo > hi:
            raise ManifestError(f"{lid}: corrected range inverted")
        if l["class"] == "RELEASED":
            net = Decimal(str(l["measured_net"]))
            if Decimal(rooms[lid]["net"]) != net:
                raise ManifestError(f"{lid}: T-552 net is not the candidate line")
            if not (lo - net == Decimal(r["missing_m2"][0]) and hi - net == Decimal(r["missing_m2"][1])):
                raise ManifestError(f"{lid}: corrected range is not net + missing")
            rel_before += net
            lo_after += lo
            hi_after += hi
            before = {"class": "RELEASED", "value": float(net), "basis": r["line_height_basis"]}
        else:
            before = {"class": "HELD", "value": None, "basis": r["line_height_basis"]}
        rows.append({"line_id": lid, "room": r["room"], "before": before,
                     "after": {"class": "HELD", "state": "HELD (BOUNDED)", "value": None,
                               "bound_m2": [float(lo), float(hi)], "plaster_height_m": r["plaster_height"],
                               "beam_end_sections_held": r["beam_end_sections_held"]},
                     "status": r["status"]})
    paint_rel = sum((Decimal(str(l["measured_net"])) for l in idx.values()
                     if l["item_code"] == "FIN.PAINT" and l["class"] == "RELEASED"), Decimal(0))
    if paint_rel != rel_before:
        raise ManifestError(f"released dry plaster {rel_before} is not the released paint {paint_rel}: cause unproven")
    ids = {r["line_id"]: r["before"]["class"] for r in rows}
    bs = bindings if bindings is not None else _t523()["bindings"]
    mine = [b for b in bs if b["line_id"] in ids]
    stale = sorted(f"{b['table']}|{b['row']}|{b['kind']}" for b in mine
                   if b["read"]["net_read"] is not None or b["bound"] is not None)
    blank = sorted(f"{b['table']}|{b['row']}|{b['kind']}" for b in mine
                   if b["read"]["net_read"] is None and b["bound"] is None)
    if any(b["value"] is not None for b in mine):
        raise ManifestError("a plaster binding on a paint-height line carries a released value")
    plaster_rel = sum((Decimal(str(l["measured_net"])) for l in idx.values()
                       if l["item_code"] == "FIN.PLASTER" and l["class"] == "RELEASED"), Decimal(0))
    return {"finding": "T-552 ENGINE_WRONG (Q-72; owner 2026-11-02 plaster to the slab underside)", "rows": rows,
            "released_lines": sum(1 for v in ids.values() if v == "RELEASED"),
            "held_lines": sum(1 for v in ids.values() if v == "HELD"),
            "released_before_m2": float(rel_before), "equals_released_paint_m2": float(paint_rel),
            "released_after_bound_m2": [float(lo_after), float(hi_after)],
            "code_view": {"FIN.PLASTER_released_now_m2": float(plaster_rel),
                          "FIN.PLASTER_released_after_m2": float(plaster_rel - rel_before),
                          "moved_to_bounded_m2": [float(lo_after), float(hi_after)]},
            "missing_total_m2": q["missing_total"],
            "bindings_stale": stale, "bindings_held_blank_unchanged": len(blank),
            "owning_package": None,
            "owning_package_state": "NONE: no board row wires the T-552 correction (Lead to name it; a released "
                                    "line moving to HELD (BOUNDED) is a Gate B change of its own, never inside "
                                    "another package)",
            "one_owner": "the FIN.PAINT lines keep the paint height (G1): only FIN.PLASTER moves; T-423 r2 (paint) "
                         "must not carry this correction",
            "source": _src("T-552")}


# ------------------------------------------------------------------------------------------------- consistency
def _code(idx, code):
    rel = [l for l in idx.values() if l["item_code"] == code and l["class"] == "RELEASED"]
    return (sum((Decimal(str(l["measured_net"])) for l in rel), Decimal(0)), len(rel),
            sum(1 for l in idx.values() if l["item_code"] == code and l["class"] == "HELD"),
            sum(1 for l in idx.values() if l["item_code"] == code and l["class"] == "EXCLUDED"))


def reconciliation_consistency(idx, v4):
    out = {}
    b = _json(T545)["engine"]
    s, n, h, x = _code(idx, "STR.CONC.BEAM")
    if (Decimal(b["released_m3"]), b["released_lines"], b["held_lines"], b["excluded_lines"]) != (s, n, h, x):
        raise ManifestError("T-545 engine side is not the candidate STR.CONC.BEAM lines")
    out["T-545"] = {"code": "STR.CONC.BEAM", "engine_m3": float(s), "released": n, "held": h, "excluded": x,
                    "freelancer_m3": float(Decimal(_json(T545)["total"]["his_m3"])), "candidate_lines_moved": 0}
    m = _load(T546_INPUTS, "t546_inputs_t555")
    fs, fn, fh, _ = _code(idx, "FIN.WP.FLOOR")
    us, un, uh, _ = _code(idx, "FIN.WP.WALL_UPTURN")
    if Decimal(m.engine_floor_total()) != fs:
        raise ManifestError("T-546 floor engine total is not the candidate FIN.WP.FLOOR lines")
    up_m2 = sum((Decimal(v) for _l, v in m.UPTURN.values() if v is not None), Decimal(0))
    if up_m2 != us:
        raise ManifestError("T-546 upturn engine m2 is not the candidate FIN.WP.WALL_UPTURN lines")
    out["T-546"] = {"codes": ["FIN.WP.FLOOR", "FIN.WP.WALL_UPTURN"], "floor_m2": float(fs), "floor_lines": fn,
                    "upturn_m2": float(us), "upturn_lines": un, "upturn_held": uh,
                    "upturn_lm_at_rule_height": float(Decimal(m.engine_upturn_lm_total())),
                    "freelancer_upturn_lm": float(Decimal(m.FREELANCER_UPTURN_LM)), "candidate_lines_moved": 0}
    t = _json(T547)
    ws, wn, wh, _ = _code(idx, "FIN.WALL.TILE")
    if Decimal(t["engine_total"]) != ws:
        raise ManifestError("T-547 engine total is not the candidate FIN.WALL.TILE lines")
    out["T-547"] = {"code": "FIN.WALL.TILE", "engine_m2": float(ws), "released": wn, "held": wh,
                    "held_bound_m2": [float(Decimal(t["held_bound_total"]["lo"])),
                                      float(Decimal(t["held_bound_total"]["hi"]))],
                    "freelancer_m2": float(Decimal(t["freelancer_total"])), "candidate_lines_moved": 0}
    p = _json(T552)
    ps, pn, ph, px = _code(idx, "FIN.PLASTER")
    if Decimal(p["candidate_valued_FIN_PLASTER_m2"]) != ps:
        raise ManifestError("T-552 candidate plaster is not the candidate FIN.PLASTER lines")
    out["T-552"] = {"code": "FIN.PLASTER", "engine_m2": float(ps), "released": pn, "held": ph, "excluded": px,
                    "candidate_lines_moved": 0, "pending_correction": "plaster_height"}
    st = _json(T554)
    if st["released_quantities_changed"] != 0:
        raise ManifestError("T-554 statement changed a released quantity")
    landing = {(r["key"], r["surface"]): r for r in v4["stair_beyond"]["parts"]}[("MS1-LD", "LANDING")]
    secs = {s_["section_id"]: s_ for s_ in st["sections"]}
    sec = secs.get("T-534/stair-bed")
    ew = None if sec is None else sum((Decimal(r["delta"]) for r in sec["rows"] if r["class"] == "ENGINE_WRONG"),
                                      Decimal(0))
    if ew is None or ew != Decimal(str(landing["bed_m2"])):
        raise ManifestError("T-554 stair ENGINE_WRONG is not the V4 MS1-LD landing part")
    if Decimal(secs["T-546/floor"]["engine_valued"]) != fs:
        raise ManifestError("T-554 T-546/floor engine side is not the candidate FIN.WP.FLOOR lines")
    out["T-554"] = {"reports_covered": st["reports_covered"], "reports_pending": st["reports_pending"],
                    "stair_engine_wrong_m2": float(ew), "is_v4_part": "stair_beyond MS1-LD LANDING (T-502)",
                    "roof_sections": "engine side = the F package expected after (F-T549-1, V4), not V3.0.58",
                    "candidate_lines_moved": 0}
    return out


# ------------------------------------------------------------------------------------------------- packages / build
def packages(gh, ph):
    g = gh["glue_group"]["v5_expected_after"]
    h1 = gh["hosts"][0]["v5_expected_after"]["glue_kg"]["range"]
    return {
        "T-498 (S package, stream S)": {
            "v5_changes": [
                f"step 5 host faces: 1F L-4b9a29d4 BOUNDED_EXPOSURE {h1} kg (V4: HELD blank, AT_MOST beside)",
                "step 5 (new): stage glue lines L-6989349a (GF L-541cf721) and L-aa5532bb (1F L-b7b4d784) carry the "
                "T-544 part 2 ranges, not the legacy R-T498-1 low ends; L-4ccc5dc2 (2F L-bbb82de2) stays HELD",
                f"step 7 groups: AAC glue AT_LEAST {g['at_least']} bags HELD, >= {g['to_buy_at_least']} "
                "(V4: 17.643906 .. 18.16227, >= 18 .. 19)",
                "lintel lines: the 17 HELD lintels stay HELD; T-544 ceilings beside only"],
            "unchanged": "steps 1-4, 6, 8 as V4", "blocked_by": "wrapper allow-list (T-498 / T-525)"},
        "T-509 (B1-04 disposal, stream S)": {"v5_changes": [], "why": "no V5 piece touches B1 earthworks lines",
                                             "blocked_by": "after T-498 (one candidate package at a time)"},
        "T-423 r2 (stream F, paint / skirting)": {
            "v5_changes": [],
            "why": "no V5 piece moves its F1 / F3 lines; T-552 corrects FIN.PLASTER only, never the FIN.PAINT lines "
                   "T-423 touches (one owner)", "blocked_by": "wrapper allow-list"},
        "T-363 / T-372 / T-513": {"v5_changes": [], "why": "no V5 piece moves masonry accessories, joints or band gaps"},
        "F package (V7 stair bed)": {"v5_changes": [],
                                     "why": "T-554 F-C-T548-1 ENGINE_WRONG 1.4375 m2 is the V4 MS1-LD landing part"},
        "plaster height correction (NO ROW)": {
            "needs": ["plaster_height"],
            "order": [f"{ph['released_lines']} RELEASED dry FIN.PLASTER lines {ph['released_before_m2']} m2 -> HELD "
                      f"(BOUNDED) {ph['released_after_bound_m2']} m2", f"{ph['held_lines']} HELD lines keep HELD, "
                      "bounds from T-552", f"{len(ph['bindings_stale'])} T-454 / T-489 plaster bindings rebound"],
            "blocked_by": "no board row (Lead); wrapper allow-list"},
    }


def v4_to_v5(gh, le, ph):
    rows = []
    for h in gh["hosts"]:
        if h["stale"]:
            rows.append({"what": f"glue host {h['host_line_id']} (stage {h['t498_stage_line']})",
                         "v4": h["v4_expected_after"], "v5": h["v5_expected_after"]["glue_kg"], "cause": "T-544"})
    rows.append({"what": "AAC glue group", "v4": gh["glue_group"]["v4_expected_after"],
                 "v5": gh["glue_group"]["v5_expected_after"], "cause": "T-544 part 1 + 2"})
    for l in le["part1"]:
        rows.append({"what": f"lintel {l['opening_id']} {l['line_id']}", "v4": {"class": "HELD", "stated": False},
                     "v5": l["after"], "cause": "T-544 (ceiling beside; line unchanged)"})
    for r in ph["rows"]:
        if r["before"]["class"] == "RELEASED":
            rows.append({"what": f"plaster {r['room']} {r['line_id']}", "v4": {"stated": False, **r["before"]},
                         "v5": r["after"], "cause": "T-552 ENGINE_WRONG (no owning package)"})
    return rows


def build(stage_rows=None, t544=None):
    v4 = v4_manifest()
    M2.check_sources(PIECES)
    cov = M4.check_coverage(NEW_PIECES, V4_BASE, V5_BASE)
    if not set(NO_WIRING) <= set(NEW_PIECES):
        raise ManifestError("a NO_WIRING piece is not a piece of this manifest")
    idx = M1.line_index()
    t = t544 if t544 is not None else _load(T544_APPLY, "t544_apply_t555").build_all()
    gh = glue_hosts(v4, t)
    le = lintel_ends(idx, t)
    ph = plaster_height(idx)
    man = {
        "schema": SCHEMA, "candidate": M1.CANDIDATE, "task": "T-555",
        "supersedes": "T-549 WIRING_MANIFEST_V4.json (every V4 / V3 / V2 statement carried unless listed in v4_to_v5)",
        "rule": M4.RULE_COVERAGE, "coverage": cov,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in
                   (V4_JSON, ROOT / T544_APPLY, T545, ROOT / T546_INPUTS, T547, T552, T554, ROOT / T523_MAP)},
        "pieces_new": {k: dict(v) for k, v in sorted(NEW_PIECES.items())},
        "no_wiring": NO_WIRING, "stage_ref": STAGE_REF,
        "glue_hosts": gh, "lintel_ends": le, "plaster_height": ph,
        "reconciliation_consistency": reconciliation_consistency(idx, v4),
        "packages": packages(gh, ph),
        "candidate_lines_moved_v4_to_v5": 0, "released_quantities_changed": 0, "candidate_files_touched": 0,
    }
    if stage_rows is not None:
        man["stage_glue_lines_checked"] = stage_ids_check(stage_rows)
    man["v4_to_v5"] = v4_to_v5(gh, le, ph)
    man["findings"] = [
        "F-T555-1: V4's 1F glue host (HELD blank) and AAC glue group (17.643906 .. 18.16227) are stale after T-544; a "
        "package wiring V4 would hold a host the drawing now bounds",
        "F-T555-2: T-544 part 2 makes the staged glue ranges of L-6989349a / L-aa5532bb (legacy low ends) stale; V2 - V4 "
        "never named them, so no package would have rebound them",
        "F-T555-3: T-552's ENGINE_WRONG on the dry FIN.PLASTER height has no owning wiring row; the plaster material "
        "bindings that read those lines are stale until it is wired",
    ]
    return man


def stage_rows_from_ref(ref=STAGE_REF):
    return M4.stage_rows_from_branch(ref)


def dumps(man):
    return M1.dumps(man)


if __name__ == "__main__":
    m = build()
    if "--check" in sys.argv:
        ok = dumps(m) == OUT_JSON.read_text(encoding="utf-8")
        print("CHECK", "OK" if ok else "DIFFERS")
        sys.exit(0 if ok else 1)
    if "--stage" in sys.argv:
        print(json.dumps(stage_ids_check(stage_rows_from_ref() or [])))
        sys.exit(0)
    OUT_JSON.write_text(dumps(m), encoding="utf-8")
    print("written", OUT_JSON.relative_to(ROOT))
