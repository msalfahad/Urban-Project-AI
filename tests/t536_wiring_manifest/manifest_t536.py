"""T-536 WIRING MANIFEST V2 builder: the T-530 manifest (V1) rebuilt on the pieces merged after it, on the candidate of
record ARCH_TAKEOFF_V3.0.58 (= the V3.0.57 line index 25a8b406 + the 5 T-507 roof WP lines).

Research / integration-preparation only (lane I, non-candidate). Nothing here writes a candidate, released, rule,
knowledge or registry file. V1 (research/agents_t530, merged f05abdd6) is read only: its builder is imported and its
functions are re-run on the newer inputs; its committed JSON is the V1 side of every per-line diff.

What V2 adds over V1, each from the merged piece's own committed output or own code (no quantity typed here):
  - T-527 LINTEL_BEARING_V3 (R-T527-1): the T-516 jamb census, the T-519 pieces and the T-524 deficit volumes re-run
    on the V3 ends (research/agents_t527/t527_effect.py, evidence sha-pinned there); every lintel row is rebuilt on
    that basis (F-C-T530-1: V1 used the V1 bearings).
  - T-529 WP_APPLICABILITY V2 exposure step (R-WP-APPL-EXPOSED-2b): the pool-court ledge membrane and the ledge
    upturn from the drawing at run time (F-C-T529-1: the V1 'unchanged, rule V2 needed' row is superseded).
  - F-T530-4 unit: a line's unit is the unit its item code already carries on the candidate; a measure in another
    unit is never converted with an invented width. The ledge glazing transition (lm) therefore gets NO
    FIN.WP.DOORWAY_TRANSITION (m2) line: it is named beside the zone's membrane line, as the candidate method itself
    does for WINDOW_TRANSITION (engine/source/arch_v3058.py BESIDE, R-T507-1).
  - T-526 COLUMN_END_CENSUS_V2 (R-T526-1): its deltas named against the candidate (which lines exist for them).
  - T-528 FINISH V7: stair bed area HELD by name while T-534 (the area reconciliation) is not merged.
Every move is applied through apply_moves(): each move names its piece, the piece's merge commit (which must be in
this tree: a stale or unmerged source is refused) and the pieces that must have moved the line before it.

Private drawing (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip -> P7757.dxf, decoded into the
git-excluded private folder) is needed for stream F (T-517 / T-522 / T-529 read it at run time); without it the
stream F rows stay HELD 'drawing not read here' (never 0) and the full-manifest test is skipped.
"""

from __future__ import annotations

import copy
import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA = "URBAN_T536_WIRING_MANIFEST_V2"
OUT_JSON = ROOT / "research/agents_t536/WIRING_MANIFEST_V2.json"
V1_JSON = ROOT / "research/agents_t530/WIRING_MANIFEST_T530.json"


def _load(rel, name):
    p = ROOT / rel
    if str(p.parent) not in sys.path:
        sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M1 = _load("tests/t530_wiring_manifest/manifest_t530.py", "manifest_t530_v1")       # read only
ManifestError = M1.ManifestError
_r, sha256, TOL = M1._r, M1.sha256, M1.TOL

PINS = {V1_JSON: "3ec1843a6c857e2d83c207d95bbbeb4fd54a1d2630378e380998599f2b5ce087"}     # the merged V1 (f05abdd6)

# ---- the pieces merged after V1 (identifiers and the Checker's words; numbers come from their outputs) -------------
NEW_PIECES = {
    "T-527": {"merge": "cf8925df", "gate": "A", "rules": ["R-T527-1"],
              "verdict": "Verifier 2026-11-05T16:02Z GATE A PASS: own DXF re-measure W18 END 0.577992 m vs V3 0.577994 "
                         "AGREE (V2 chord 0.478 ENGINE_WRONG); no state moves, T-524 unchanged"},
    "T-529": {"merge": "5f775ba6", "gate": "A", "rules": ["R-WP-APPL-EXPOSED-2a..e"],
              "verdict": "Verifier 2026-11-05T16:02Z GATE A PASS: pool-court ledge 0.639573 m2 AGREE, 100 % under the "
                         "+9.70 cover, EXPOSED by UP-WP-ROOF-001 balcony scope (open sides)"},
    "T-530": {"merge": "f05abdd6", "gate": "A", "rules": [],
              "verdict": "Verifier 2026-11-05T16:02Z GATE A PASS: manifest arithmetic AGREE; F-C-T530-1 lintel ceilings "
                         "on V1 bearings, F-C-T529-1 ledge row superseded (this V2)"},
}
PIECES = dict(M1.PIECES, **NEW_PIECES)
NOT_MERGED = {"T-534": "READY f97634e0 (stair bed area 39.485 -> 35.4313 m2 reconciled), Gate A pending: not a source"}

# T-526 deltas go to ledgers no candidate or staged line carries: the codes searched for them
TIE_MESH_CODES = ("MAS.TIE", "MAS.SHARMAT", "MAS.MESH", "FIN.PLASTER.MESH", "MAS.CRACK_MESH")


# ---------------------------------------------------------------------------------------------------------- sources
def in_tree(commit):
    """True when the merge commit is an ancestor of HEAD (the piece is merged in this tree)."""
    r = subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", commit, "HEAD"], capture_output=True)
    if r.returncode not in (0, 1):
        raise ManifestError(f"STALE_SOURCE: commit {commit} unknown in this tree ({r.stderr.decode().strip()[:80]})")
    return r.returncode == 0


def check_sources(pieces, merged=in_tree):
    for t, p in sorted(pieces.items()):
        if not merged(p["merge"]):
            raise ManifestError(f"STALE_SOURCE: {t} merge {p['merge']} is not in this tree (unmerged or stale piece)")


def apply_moves(line_id, before, moves, merged=in_tree):
    """compose the moves of several pieces on ONE line, in order. Each move: task, merge, after, requires (the tasks
    that must have moved the line before it). Refused: an unmerged / stale source, a move out of order, a repeated
    task. Returns (after, history)."""
    done, hist, cur = [], [], before
    for mv in moves:
        if not merged(mv["merge"]):
            raise ManifestError(f"STALE_SOURCE: {line_id}: {mv['task']} merge {mv['merge']} is not in this tree")
        if mv["task"] in done:
            raise ManifestError(f"ORDER: {line_id}: {mv['task']} moves the line twice")
        miss = [t for t in mv.get("requires", ()) if t not in done]
        if miss:
            raise ManifestError(f"ORDER: {line_id}: {mv['task']} before {miss}")
        if mv["after"] != cur:
            hist.append({"task": mv["task"], "merge": mv["merge"], "from": cur, "to": mv["after"],
                         "cause": mv.get("cause")})
        cur = mv["after"]
        done.append(mv["task"])
    return cur, hist


def _move(task, after, requires=(), cause=None):
    return {"task": task, "merge": PIECES[task]["merge"], "after": after, "requires": list(requires), "cause": cause}


def line_unit(code, measure_unit, idx, t507):
    """the unit of a line is the unit its item code carries on the candidate (one unit per code); a measure in any
    other unit is refused, never converted (F-T530-4)."""
    units = {l["unit"] for l in list(idx.values()) + list(t507.values()) if l["item_code"] == code}
    if len(units) > 1:
        raise ManifestError(f"UNIT: {code} carries {sorted(units)} on the candidate")
    if not units:
        from engine.source import boq_line as BL
        if code in BL.ITEMS:
            units = {BL.ITEMS[code][3]}
    if units and measure_unit not in units:
        raise ManifestError(f"UNIT: {code} is {sorted(units)[0]} on the candidate, the measure is {measure_unit}: never "
                            f"converted with an invented width / depth")
    return measure_unit


def v1_manifest():
    p = V1_JSON
    if sha256(p) != PINS[p]:
        raise ManifestError(f"PIN: {p.name} sha256 {sha256(p)[:8]} is not the pinned {PINS[p][:8]}")
    return json.loads(p.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------------- stream S: lintels
def _t527():
    return _load("research/agents_t527/t527_effect.py", "t527_effect_m")


def lintel_inputs_basis(basis):
    """T-453 ledger rows + the T-516 census / T-519 pieces / T-524 deficit volumes re-run on one bearing basis by the
    T-527 effect code (V1 = the merged T-516 records, V3 = LINTEL_BEARING_V3 ends)."""
    E = _t527()
    doc = E.census(basis)
    t516 = {r["opening_id"]: r for r in doc["rows"]}
    t519 = {r["opening_id"]: r for r in E.t519_census(doc)["rows"]}
    ev = E.evidence() if basis != "V1" else \
        list(csv.DictReader((ROOT / "research/agents_t516/out/JAMB_EVIDENCE_T516.csv").open(encoding="utf-8")))
    T524 = E.T524
    old = (T524.T516, T524.T516_EV)
    with tempfile.TemporaryDirectory() as d:
        j, c = Path(d) / "t516.json", Path(d) / "ev.csv"
        j.write_text(json.dumps(doc), encoding="utf-8")
        with open(c, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["opening_id", "side", "through_walls"], lineterminator="\n",
                               extrasaction="ignore")
            w.writeheader()
            w.writerows(ev)
        try:
            T524.T516, T524.T516_EV = j, c
            lintels, pairs = T524.villa_inputs()
            t524 = T524.assess_set(lintels, pairs)
        finally:
            T524.T516, T524.T516_EV = old
    t453 = {r["opening_id"]: r for r in M1._csv(M1.T453_CSV)}
    return t453, t516, t519, t524


def _with_basis(basis, fn, *a):
    inp = lintel_inputs_basis(basis)
    old = M1.lintel_inputs
    M1.lintel_inputs = lambda: inp
    try:
        return fn(*a)
    finally:
        M1.lintel_inputs = old


def lintel_rows_v2(idx, v1):
    """every REQUIRED lintel line: V1 after (T-516 / T-519 / T-524) then the T-527 V3 basis, composed in order."""
    r1, t524_1 = _with_basis("V1", M1.lintel_rows, idx)
    r3, t524_3 = _with_basis("V3", M1.lintel_rows, idx)
    c1 = {r["line_id"]: r for r in v1["stream_S"]["lintel_lines"]}
    if json.loads(M1.dumps(r1)) != v1["stream_S"]["lintel_lines"]:
        raise ManifestError("CONTROL: the V1 basis re-run does not reproduce the committed V1 lintel rows")
    E = _t527()
    ceil = {b: {r["opening_id"]: r.get("length_hi_m") for r in E.census(b)["rows"]} for b in ("V1", "V3")}
    out = []
    for a, b in zip(r1, r3):
        if a["line_id"] != b["line_id"]:
            raise ManifestError("lintel row order differs between bases")
        first = ["T-516", "T-519"] + (["T-524"] if b["after"]["state"] == "HELD_BY_NAME" else [])
        moves = [_move(t, a["after"], requires=first[:i]) for i, t in enumerate(first)]   # V1: one write
        moves.append(_move("T-527", b["after"], requires=first, cause="R-T527-1 LINTEL_BEARING_V3 ends (F-C-T530-1)"))
        after, hist = apply_moves(a["line_id"], a["before"], moves)
        hist = [h for h in hist if h["task"] == "T-527"]           # the V1 part is the V1 manifest's own record
        row = dict(b, after=after)
        if hist:
            row["source"] = b["source"] + M1_piece("T-527")
            row["rules"] = b["rules"] + ["R-T527-1"]
            row["order"] = b["order"] + ["T-527 (V3 bearing basis)"]
        row["v1_to_v2"] = _diff(c1[a["line_id"]]["after"], after)
        row["v1_to_v2_cause"] = "R-T527-1 V3 ends (T-527 effect)" if row["v1_to_v2"] else None
        oid = a["element_id"].split(":", 1)[1]
        if ceil["V1"][oid] != ceil["V3"][oid]:
            row["t516_length_ceiling_m"] = {
                "v1": ceil["V1"][oid], "v3": ceil["V3"][oid],
                "carried": "in the line's high" if after["state"] == "BOUNDED_MIN_BEARING" else
                           "by no quantity: the line is HELD BY NAME (its bound is the T-524 deficit-end volume, "
                           "unchanged by T-527); the ceiling is the T-531 bar / formwork input"}
        out.append(row)
    return out, t524_3, (r1, t524_1)


def M1_piece(*tids):
    return [{"task": t, "merge": PIECES[t]["merge"], "checker": PIECES[t]["verdict"]} for t in tids]


def _diff(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            out += _diff(a.get(k), b.get(k), f"{path}.{k}" if path else str(k))
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += _diff(x, y, f"{path}[{i}]")
        return out
    return [] if a == b else [{"field": path, "v1": a, "v2": b}]


# --------------------------------------------------------------------------------------------- stream S: T-526
def column_end_census(idx, prows, stage_codes):
    s = M1._json(ROOT / "research/agents_t526/out/SUMMARY_T526.json")
    ends = M1._csv(ROOT / "research/agents_t526/out/MISSED_ENDS_T526.csv")
    codes = {l["item_code"] for l in idx.values()} | set(stage_codes)
    present = sorted(c for c in codes if c in TIE_MESH_CODES)
    tot = s["totals"]
    if any(tot[k] != 0.0 for k in ("d_length_m", "d_blockwork_m2", "d_blocks_nr")):
        raise ManifestError("T-526 moves a run length / blockwork area: MAS.BLOCK lines would move")
    conf = []
    for r in ends:
        if r["perimeter_state"] == "COMPUTED":
            hit = [p for p in prows if r["wall_id"] in p["walls"]]
            conf.append({"wall": r["wall_id"], "end": r["end"], "t526_after_m3": float(r["perimeter_after_m3"]),
                         "perimeter_line_host": hit[0]["host_line_id"] if hit else None,
                         "state": "CONFIRMS the V1 / T-520 perimeter (already the drawn end, one write)" if hit
                         else "NO perimeter line (host not valued): figure beside"})
    return {
        "rule": "R-T526-1 COLUMN_END_CENSUS_V2", "source": M1_piece("T-526"),
        "ends_missed_by_v1": len(s["missed_by_v1"]), "held_ends": s["held_ends"],
        "candidate_lines_moved": 0,
        "mas_block": {"d_length_m": tot["d_length_m"], "d_blockwork_m2": tot["d_blockwork_m2"],
                      "d_blocks_nr": tot["d_blocks_nr"],
                      "why": "every end face IS the column face (gap 0.0 mm): MAS.BLOCK lines unchanged (Q-73 / Q-75)"},
        "perimeter_mortar": conf,
        "ties_and_mesh": {
            "d_ties_nr_measured": tot["d_ties_nr_measured"], "d_mesh_owner_ml": tot["d_mesh_owner_ml"],
            "d_mesh_drawing_ml": tot["d_mesh_drawing_ml"],
            "line_codes_present": present,
            "state": "NO LINE: neither V3.0.58 nor the T-498 stage carries a tie / crack-mesh line; the deltas belong "
                     "to the T-355 (sharmat) and T-317 (mesh) ledgers, which need a version that reads END_CENSUS_V2 "
                     "(F-C-T526-1 -> T-532: piece kinds BEAM / FACE); named here, wired by no package yet"},
    }


# --------------------------------------------------------------------------------------------- stream F
def poolcourt_v2(t507, idx, v1, drawing=True):
    frows, fadd, finfo = M1.poolcourt_rows(t507, drawing)
    if not finfo["drawing_read"]:
        return frows, fadd, finfo, None
    m529 = _load("research/agents_t529/t529_alsenan.py", "t529_m").build()
    if not m529["drawing_read"]:
        raise ManifestError("T-529: drawing not read although T-522 read it")
    from engine.source import arch_v3058 as A58
    from engine.source import wp_applicability_rules_v1 as WPA
    rows = m529["rows"]
    mem = [r for r in rows if r["component"] == "FLAT_MEMBRANE"]
    ups = [r for r in rows if r["component"] == "UPTURN"]
    trs = [r for r in rows if r["component"] == "WINDOW_TRANSITION"]
    if len(mem) != 1 or mem[0]["status"] != WPA.MEASURED:
        raise ManifestError("T-529 ledge membrane not MEASURED")
    if not ups or any(r["status"] != WPA.MEASURED for r in ups):
        raise ManifestError("T-529 ledge upturn not MEASURED")
    up_lm = _r(sum(r["length_lm"] for r in ups))
    up_m2 = _r(sum(r["qty"] for r in ups))
    tr_lm = _r(sum(r["held_bound"] for r in trs))
    by = {r["line_id"]: r for r in frows}
    v1f = {r["line_id"]: r for r in v1["stream_F"]["lines"]}
    led_up, led_mem = by["L-d7d1bf8c5991ccf69ea2"], by["L-2361d6ec13c952bd2ae3"]
    # the T-529 pieces are the T-522 pieces (one discretisation segment at BCE / BD0: <= 2e-6 lm)
    if abs(up_lm - led_up["after"]["held_high"]) > 2e-6:
        raise ManifestError(f"T-529 upturn {up_lm} is not the T-522 wall-end pieces {led_up['after']['held_high']}")
    if abs(mem[0]["qty"] - led_mem["after"]["held_high"]) > TOL:
        raise ManifestError("T-529 ledge area is not the T-522 / T-507 bound")
    v1_tr = [a for a in v1["stream_F"]["added_lines"] if a["item_code"] == "FIN.WP.DOORWAY_TRANSITION"]
    if len(v1_tr) != 1 or abs(v1_tr[0]["after"]["length_beside_lm"] - tr_lm) > TOL:
        raise ManifestError("the T-529 window transition is not the V1 transition length")
    beside = [{"what": r["component"], "run": r.get("run"), "unit": r["unit"], "bound": r.get("held_bound"),
               "status": r["status"], "why": r.get("held_reason"), "basis": r["rule_basis"]}
              for r in rows if r["component"] in A58.BESIDE]
    for b in beside:
        if b["status"] not in (WPA.HELD, WPA.RFI):
            raise ManifestError(f"beside item {b['what']} is {b['status']} (beside is HELD / RFI only)")
    out = []
    for r in frows:
        lid = r["line_id"]
        moves = [_move("T-522", r["after"])]
        cause = None
        if lid == "L-d7d1bf8c5991ccf69ea2":
            a2 = {"state": "MEASURED", "value": up_lm, "m2_at_0_20": up_m2,
                  "runs": [{"run": x.get("run"), "lm": x["length_lm"]} for x in ups],
                  "why": "ledge EXPOSED (R-WP-APPL-EXPOSED-2b, open sides): R-WP-APPL-UPTURN-1 applies to the two "
                         "solid wall-end pieces; the glazing piece is a window transition beside the membrane line"}
            moves.append(_move("T-529", a2, requires=["T-522"], cause="R-WP-APPL-EXPOSED-2b (F-C-T529-1)"))
            cause = "T-529 exposure V2"
        elif lid == "L-2361d6ec13c952bd2ae3":
            a2 = {"state": "MEASURED", "value": _r(mem[0]["qty"]),
                  "held_beside": beside,
                  "why": "covered 100 % by the +9.70 cover but open at the void edge and the court side: balcony "
                         "condition, EXPOSED (R-WP-APPL-EXPOSED-2b, UP-WP-ROOF-001); R-WP-APPL-EXPOSED / ONCE"}
            moves.append(_move("T-529", a2, requires=["T-522"], cause="R-WP-APPL-EXPOSED-2b (F-C-T529-1)"))
            cause = "T-529 exposure V2 (supersedes V1 'unchanged, rule V2 needed')"
        after, hist = apply_moves(lid, r["before"], moves)
        row = dict(r, after=after)
        if any(h["task"] == "T-529" for h in hist):
            row["source"] = r["source"] + M1_piece("T-529")
            row["rules"] = r["rules"] + ["R-WP-APPL-EXPOSED-2b"]
            row["evidence_status"] = "DRAWING-CONFIRMED (T-529 exposure from the drawn sides; Checker re-measure AGREE)"
            row["order"] = ["T-522 (pieces)", "T-529 (exposure decided)"]
        row["v1_to_v2"] = _diff(v1f[lid]["after"], after)
        row["v1_to_v2_cause"] = cause if row["v1_to_v2"] else None
        out.append(row)
    # added lines: every unit from its item code (F-T530-4); the transition has no m2 item and becomes a beside item
    added, removed = [], []
    for a in fadd:
        if a["item_code"] == "FIN.WP.DOORWAY_TRANSITION":
            try:
                line_unit(a["item_code"], "lm", idx, t507)
            except ManifestError as e:
                removed.append({"v1_added_line": a["element_id"], "item_code": a["item_code"], "v1_unit": a["unit"],
                                "measure": {"value_lm": tr_lm, "unit": "lm"}, "refusal": str(e),
                                "v2": "NO LINE: WINDOW_TRANSITION 2.976663 lm named HELD beside the ledge membrane "
                                      "line L-2361d6ec (candidate method arch_v3058 BESIDE, R-T507-1; a doorway on a "
                                      "B8-06 zone is refused by that method: a door makes it B8-07)",
                                "cause": "F-T530-4 (unit decided from the item, never converted)"})
                continue
            raise ManifestError("FIN.WP.DOORWAY_TRANSITION accepted an lm measure")
        line_unit(a["item_code"], a["unit"], idx, t507)
        zone = [x for x in a["after"].get("missing") or [] if x.startswith("ZONE:")]
        if zone and a["element_id"].startswith("1F-POOLCOURT-550-LEDGE:"):
            rest = [x for x in a["after"]["missing"] if not x.startswith("ZONE:")]
            if not rest:
                raise ManifestError(f"{a['element_id']}: exposure was its only gap: the line needs its own measure")
            a = dict(a, after=dict(a["after"], missing=rest,
                                   zone_resolved="T-529 R-WP-APPL-EXPOSED-2b: the ledge is EXPOSED (open sides); the "
                                                 "line stays HELD on its own remaining gaps"),
                     source=a["source"] + M1_piece("T-529"))
        v1a = [x for x in v1["stream_F"]["added_lines"] if x["element_id"] == a["element_id"]]
        a = dict(a, v1_to_v2=_diff(v1a[0]["after"], a["after"]) if v1a else [{"field": "line", "v1": None,
                                                                            "v2": "added"}])
        a["v1_to_v2_cause"] = "T-529 exposure decided (ZONE gap closed)" if a["v1_to_v2"] else None
        added.append(a)
    for b in beside:
        if b["what"] == "WINDOW_TRANSITION" and abs(b["bound"] - tr_lm) > TOL:
            raise ManifestError("beside window transition length moved")
    d = m529["decision"]
    finfo = dict(finfo, t529={"status": d["status"], "basis": d["basis"], "open_sky_m2": d["open_m2"],
                              "covered_m2": d["covered_m2"], "membrane_m2": d["membrane_m2"],
                              "own_area_m2": m529["own_area_m2"], "ledge_area_m2": m529["t486_area_m2"]})
    return out, added, finfo, removed


def roof_code_views_v2(idx, t507, frows, fadd):
    out = {}
    for code in ("FIN.WP.ROOF", "FIN.WP.ROOF_UPTURN", "FIN.ROOF.FINISH", "FIN.ROOF.SCREED", "FIN.ROOF.INSULATION",
                 "FIN.ROOF.PROTECTION", "FIN.WP.DOORWAY_TRANSITION"):
        ls = [dict(l, line_id=k) for k, l in list(idx.items()) + list(t507.items()) if l["item_code"] == code]
        val = [l["measured_net"] for l in ls if l["class"] == "RELEASED"]
        v = _r(sum(val)) if val else None
        dv = sum(r["after"]["value"] for r in frows if r["item_code"] == code and r["after"].get("state") == "MEASURED"
                 and r["before"]["class"] != "RELEASED")
        dv += sum(r["after"]["value"] or 0.0 for r in fadd if r["item_code"] == code)
        nn = len([r for r in fadd if r["item_code"] == code])
        valued_after = v is not None or dv != 0.0
        held_lines = [l["line_id"] for l in ls if l["class"] != "RELEASED"
                      and not any(r["line_id"] == l["line_id"] and r["after"].get("state") == "MEASURED"
                                  for r in frows)]
        out[code] = {"released_before": v, "lines_before": len(ls), "lines_after": len(ls) + nn,
                     "released_after": _r((v or 0.0) + dv) if valued_after else None,
                     "change": _r(dv) if valued_after else None,
                     "change_pct": None if not v else _r(100 * dv / v, 4),
                     "held_lines_after": len(held_lines) + len([r for r in fadd if r["item_code"] == code
                                                                and r["after"].get("value") is None]),
                     "view_after": None if valued_after else f"HELD ({len(ls) + nn} lines, no valued line): never 0.0"}
    return out


# --------------------------------------------------------------------------------------------- FINISH V7
def finish_v6_v7_v2():
    v = M1.finish_v6_v7()
    s = v["v7_stair_bed"]
    s["area_state"] = ("HELD BY NAME: the stair bed AREA under the 11 V7 keys is the T-511 census 35.4313 m2 vs Q-53 "
                       "39.49 m2 (F-C-T528-1); its reconciliation T-534 is " + NOT_MERGED["T-534"] + ". V7 stays "
                       "UNWIRED; installed / procurement figures above are on the T-511 area, named, not moved")
    s["wiring_after"] = ["T-534 Gate A (area)", "F-T518-2 ruling (stair-bed loss scope)",
                         "V7 replaces STAIR_BED_V1 as the one producer of the 11 keys (R-T523-4)"]
    return v


# --------------------------------------------------------------------------------------------- line moves table
def line_moves(srows, hrows, prows, frows, fadd):
    out = []
    for r in srows:
        out.append({"line_id": r["line_id"], "item_code": r["item_code"], "unit": r["unit"], "element_id": r["element_id"],
                    "before": r["before"], "after_v2": r["after"], "pieces": [p["task"] for p in r["source"]],
                    "merges": [p["merge"] for p in r["source"]], "rules": r["rules"],
                    "owner_trade": "B9-02 RC lintel (STR.CONC.LINTEL)", "v1_to_v2": r["v1_to_v2"],
                    "evidence_status": r["evidence_status"]})
    for h in hrows:
        out.append({"line_id": h["t498_stage_line"], "item_code": "MAS.GLUE.AAC", "unit": "kg",
                    "element_id": h["host_element"], "host_line": h["host_line_id"], "before": h["before"],
                    "after_v2": h["after"], "pieces": [p["task"] for p in h["source"]],
                    "merges": [p["merge"] for p in h["source"]], "rules": h["rules"],
                    "owner_trade": "B9-04 masonry material (T-498 staged line)", "v1_to_v2": h.get("v1_to_v2", []),
                    "evidence_status": "BOUNDED (ranged face; rule RG-1 / T-537 pending)"})
    for p in prows:
        out.append({"line_id": p["line_id"], "item_code": p["item_code"], "unit": p["unit"],
                    "element_id": p["host_element"], "host_line": p["host_line_id"], "before": p["before"],
                    "after_v2": p["after"], "pieces": [x["task"] for x in p["source"]],
                    "merges": [x["merge"] for x in p["source"]], "rules": p["rules"],
                    "owner_trade": "B9-04 perimeter joint mortar (own key)", "v1_to_v2": p.get("v1_to_v2", []),
                    "evidence_status": p["evidence_status"]})
    for r in frows:
        out.append({"line_id": r["line_id"], "item_code": r["item_code"], "unit": r["unit"], "element_id": r["element_id"],
                    "before": r["before"], "after_v2": r["after"], "pieces": [x["task"] for x in r.get("source", [])],
                    "merges": [x["merge"] for x in r.get("source", [])], "rules": r.get("rules", []),
                    "owner_trade": "B8-06 exposed slab waterproofing", "v1_to_v2": r.get("v1_to_v2", []),
                    "evidence_status": r.get("evidence_status")})
    for a in fadd:
        out.append({"line_id": a["line_id"], "item_code": a["item_code"], "unit": a["unit"], "element_id": a["element_id"],
                    "before": a["before"], "after_v2": a["after"], "pieces": [x["task"] for x in a["source"]],
                    "merges": [x["merge"] for x in a["source"]], "rules": a["rules"],
                    "owner_trade": "ROOF BUILD-UP (B13-01 / SCREED)", "v1_to_v2": a.get("v1_to_v2", []),
                    "evidence_status": a["evidence_status"]})
    return out


# --------------------------------------------------------------------------------------------- build
def build(drawing=True):
    v1 = v1_manifest()
    check_sources(PIECES)
    idx = M1.line_index()
    t507 = M1._v3058_t507_lines()
    t523 = M1._module("research/agents_t523/t523_binding_map_v2.py", "t523_m").run()
    if t523["failures"]:
        raise ManifestError("T-523 map fails its own checks")
    srows, t524, _ = lintel_rows_v2(idx, v1)
    hrows, hunch = M1.host_material_rows(srows, t524, t523)
    v1h = {h["host_line_id"]: h for h in v1["stream_S"]["host_material_lines"]}
    for h in hrows:
        h["v1_to_v2"] = _diff(v1h[h["host_line_id"]]["after"], h["after"])
        h["v1_to_v2_cause"] = "R-T527-1 faces (T-527)" if h["v1_to_v2"] else None
    prows, pheld = M1.perimeter_rows(idx)
    v1p = {p["host_line_id"]: p for p in v1["stream_S"]["perimeter_lines"]}
    for p in prows:
        p["v1_to_v2"] = _diff(v1p[p["host_line_id"]]["after"], p["after"])
    stage_codes = ("MAS.BLOCK", "MAS.GLUE.AAC", "MAS.MORTAR.BLACK", "MAS.UNITS.BLACK", "MAS.UNITS.WHITE")
    frows, fadd, finfo, removed = poolcourt_v2(t507, idx, v1, drawing)
    lcv = M1.lintel_code_view(srows, t524)
    man = {
        "schema": SCHEMA, "candidate": M1.CANDIDATE, "task": "T-536", "supersedes": "T-530 WIRING_MANIFEST_T530.json (V1)",
        "inputs": dict({str(p.relative_to(ROOT)): sha256(p) for p in sorted(M1.PINS, key=str)},
                       **{str(V1_JSON.relative_to(ROOT)): sha256(V1_JSON),
                          "research/agents_t527/out/JAMB_EVIDENCE_V3_T527.csv":
                              sha256(ROOT / "research/agents_t527/out/JAMB_EVIDENCE_V3_T527.csv"),
                          "research/agents_t526/out/MISSED_ENDS_T526.csv":
                              sha256(ROOT / "research/agents_t526/out/MISSED_ENDS_T526.csv"),
                          "research/agents_t526/out/SUMMARY_T526.json":
                              sha256(ROOT / "research/agents_t526/out/SUMMARY_T526.json")}),
        "pieces": {k: dict(v) for k, v in sorted(PIECES.items())},
        "not_sources": NOT_MERGED,
        "stream_S": {
            "lintel_lines": srows, "lintel_code_view": lcv,
            "lintel_code_view_v1_to_v2": _diff(v1["stream_S"]["lintel_code_view"], lcv),
            "host_material_lines": hrows, "host_material_unchanged": hunch,
            "glue_group": M1.glue_group(t523, hrows),
            "perimeter_lines": prows, "perimeter_held_beside": pheld,
            "cement_group": M1.cement_group(t523, prows),
            "column_end_census": column_end_census(idx, prows, stage_codes),
        },
        "stream_F": {"lines": frows, "added_lines": fadd, "removed_v1_lines": removed, "drawing": finfo,
                     "code_views": roof_code_views_v2(idx, t507, frows, fadd) if finfo["drawing_read"] else None},
        "finish_v6_v7": finish_v6_v7_v2(),
        "stale_bindings": M1.stale_bindings(t523, srows, hrows, idx),
        "line_moves": line_moves(srows, hrows, prows, frows, fadd) if finfo["drawing_read"] else None,
        "findings": [
            "F-C-T530-1 closed: the lintel rows are rebuilt on the V3 ends (T-527); V1 -> V2 per line below",
            "F-C-T529-1 closed: the ledge membrane / upturn rows are rebuilt on the T-529 exposure V2",
            "F-T530-4 closed: no FIN.WP.DOORWAY_TRANSITION (m2) line for an lm measure; the window transition is a "
            "HELD item beside the ledge membrane line, as the candidate method names WINDOW_TRANSITION",
            "F-T536-1: the T-526 tie (+30 nr) and crack-mesh (+40.90 m.l owner band) deltas have no candidate or "
            "staged line: they wait for T-355 / T-317 ledger versions reading END_CENSUS_V2 (T-532)",
            "F-T536-2: FINISH V7 stair stays HELD by name on its area until T-534 passes Gate A (not a source here)",
        ],
        "released_quantities_changed": 0, "candidate_files_touched": 0,
    }
    man["packages"] = packages(man)
    man["v1_to_v2_summary"] = v1_to_v2_summary(man, v1)
    return man


def packages(man):
    S, F = man["stream_S"], man["stream_F"]
    moved_s = len(S["lintel_lines"])
    return {
        "S": {"base": "T-498 r3 stage (agents/task-T-498 @ e3e2ebb5, not merged) after T-525",
              "moves": {"STR.CONC.LINTEL lines": moved_s, "T-498 material lines (host faces)": len(S["host_material_lines"])},
              "adds": {"MAS.MORTAR.BLACK perimeter lines": len(S["perimeter_lines"])},
              "order": ["1 T-525", "2 T-498 (74 staged material lines)", "3 bind the 60 lintel bindings (F-T530-1)",
                        "4 lintel lines on the V3 basis (T-516 / T-519 / T-524 then T-527)",
                        "5 host faces (RG-1: T-537 rule version)", "6 perimeter mortar (T-520 = T-526)",
                        "7 groups (R-T523-1)"],
              "blocked_by": "wrapper allow-list (T-498 / T-525) and T-537 (RG-1) for step 5"},
        "F": {"base": "V3.0.58 (independent of S)",
              "moves": {"FIN.WP.ROOF_UPTURN lines": len([r for r in F["lines"] if r["item_code"] == "FIN.WP.ROOF_UPTURN"
                                                         and r.get("v1_to_v2") is not None]),
                        "FIN.WP.ROOF lines": len([r for r in F["lines"] if r["item_code"] == "FIN.WP.ROOF"])},
              "adds": {"FIN.ROOF.* lines": len(F["added_lines"])},
              "order": ["1 T-522 window run + ledge pieces", "2 T-529 ledge exposure: membrane + upturn MEASURED, "
                        "window transition beside", "3 T-517 build-up lines (C-F1)", "4 FINISH V6 reader only",
                        "5 V7 after T-534 + F-T518-2"],
              "blocked_by": "wrapper allow-list (same)"},
    }


def v1_to_v2_summary(man, v1):
    out = []
    for sec, key in (("stream_S", "lintel_lines"), ("stream_S", "host_material_lines"), ("stream_S", "perimeter_lines"),
                     ("stream_F", "lines")):
        for r in man[sec][key]:
            if r.get("v1_to_v2"):
                out.append({"line_id": r.get("line_id") if key != "host_material_lines" else r["t498_stage_line"],
                            "element": r.get("element_id") or r.get("host_element"),
                            "changes": r["v1_to_v2"], "cause": r.get("v1_to_v2_cause")})
    for a in man["stream_F"]["added_lines"]:
        if a.get("v1_to_v2"):
            out.append({"line_id": a["line_id"], "element": a["element_id"], "changes": a["v1_to_v2"],
                        "cause": a.get("v1_to_v2_cause")})
    for x in man["stream_F"].get("removed_v1_lines") or []:
        out.append({"line_id": "NEW (V1)", "element": x["v1_added_line"], "changes": [{"field": "line", "v1": "added m2 "
                    "blank", "v2": "no line; beside item lm"}], "cause": x["cause"]})
    return out


def dumps(man):
    return M1.dumps(man)
