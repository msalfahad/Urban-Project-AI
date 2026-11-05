"""T-538 WIRING MANIFEST V3: the T-536 manifest (V2, pinned) extended by the pieces merged after it, on the candidate of
record ARCH_TAKEOFF_V3.0.58. Research / integration preparation only (lane I, non-candidate): nothing here writes a
candidate, released, rule, knowledge or registry file; nothing is wired.

What V3 adds over V2, each from the merged piece's own committed output (no quantity typed here):
  - T-531 (R-T531-1) lintel bars: PRODUCED / FLAGGED parts, each AT_LEAST, against the candidate STR.REBAR lines.
  - T-532 (R-T532-1) END_CENSUS_V3: the 12 + 1 column run ends on the T-274 piece kinds, set-equal to T-526.
  - F-C-T532-1 as a check (R-T538-1): a joint head is never taken from a masonry piece shorter than one joint.
  - T-535 (R-T535-1..4) sand in loose m3 and the T-523 stair-binding correction; T-540 (R-T540-1..4) t / loads HELD.
  - T-534 (stair bed area): NOT a source in this tree (READY, merge-blocked by F-C-T536-1). The manifest states both
    branches statically, so the committed file never depends on live board state (the F-C-T536-1 lesson).
Every source commit must be an ancestor of HEAD (manifest_t536.check_sources); out of order / unmerged -> refused.
No private drawing is read here: every input is a committed, numbers-only output of a merged piece.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
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


M2 = _load("tests/t536_wiring_manifest/manifest_t536.py", "manifest_t536_v2")      # read only
M1 = M2.M1
ManifestError = M2.ManifestError
_r, sha256 = M1._r, M1.sha256

SCHEMA = "URBAN_T538_WIRING_MANIFEST_V3"
OUT_JSON = ROOT / "research/agents_t538/WIRING_MANIFEST_V3.json"
V2_JSON = ROOT / "research/agents_t536/WIRING_MANIFEST_V2.json"
T531 = ROOT / "research/agents_t531/out/LINTEL_BARS_T531.json"
T532_SUM = ROOT / "research/agents_t532/out/SUMMARY_T532.json"
T532_JUN = ROOT / "research/agents_t532/out/JUNCTIONS_V3_T532.csv"
T532_KIND = ROOT / "research/agents_t532/out/KIND_MAP_T532.csv"
T274_PIECES = ROOT / "research/agents_t274/T274_RUN_PIECES.csv"
T520_SUM = ROOT / "research/agents_t520/out/SUMMARY_T520.json"
T535 = ROOT / "research/agents_t535/out/SAND_PROCUREMENT_T535.json"
T540 = ROOT / "research/agents_t540/out/SAND_LOAD_DENSITY_T540.json"
PINS = {V2_JSON: "305c2cf0c712824ea3cd6ceaa7aee2781642deb0274d193554c846d49febacf3"}     # the merged V2 (5953b91f)

NEW_PIECES = {
    "T-531": {"merge": "d9051cce", "gate": "A", "rules": ["R-T531-1"],
              "verdict": "Verifier 2026-11-05T18:05Z GATE A PASS a-h (own re-measure ST7757); freelancer lintel bars "
                         "UNRESOLVED (no row); RFI lintel cover / bend / anchorage stands"},
    "T-532": {"merge": "ba9eba77", "gate": "A", "rules": ["R-T532-1"],
              "verdict": "Verifier 2026-11-05T19:55Z GATE A PASS a-h: 12 + 1 ends set-equal to T-526, 117 / 117 "
                         "interior junctions AGREE; F-C-T532-1 sub-5 mm slivers (GF-W10 end 1, 1F-W09 piece 1)"},
    "T-535": {"merge": "c4a34358", "gate": "A", "rules": ["R-T535-1", "R-T535-2", "R-T535-3", "R-T535-4"],
              "verdict": "Verifier 2026-11-05T19:00Z GATE A PASS a-h: sand unit loose m3, pack / density HELD; "
                         "FX-535 hand-checked"},
    "T-536": {"merge": "5953b91f", "gate": "A", "rules": [],
              "verdict": "Verifier 2026-11-05T18:05Z GATE A PASS a-h: WIRING MANIFEST V2; F-C-T536-1 (fixed by T-538)"},
    "T-540": {"merge": "509deaf7", "gate": "A", "rules": ["R-T540-1", "R-T540-2", "R-T540-3", "R-T540-4"],
              "verdict": "Verifier 2026-11-05T21:05Z GATE A PASS: sand load size and bulk density both HELD"},
}
PIECES = dict(M2.PIECES, **NEW_PIECES)
NOT_SOURCES = {
    "T-534": "READY f97634e0 (Gate A PASS 18:05, merge-blocked by F-C-T536-1 until T-538): not a source in this tree",
    "T-537": "TODO r2 (R-T498-2 ranged host faces, REJECTED 19:56 on one binding): not a source",
    "T-498": "agents/task-T-498 @ e3e2ebb5 stage (BLOCKED on the wrapper allow-list): line ids only, no figure read",
}

RULE_SLIVER = (
    "R-T538-1 (every villa; provenance F-C-T532-1, T-538): a masonry piece of a run census shorter than one bed / "
    "perimeter joint (j, the joint the perimeter ledger uses: R-T520-1, owner provisional 10 mm where no drawing prints "
    "one) holds no block unit, so it carries no joint head of its own. The head of a junction on such a piece is the "
    "head of the nearest full masonry piece of the same run on the far side from the column (walking only across "
    "masonry slivers); if a concrete piece or the run end comes first, the head is HELD by name. Never a guessed or "
    "default head; a sliver head is refused.")

HEAD_FIELDS = ("kind", "member_id", "mark", "depth_m", "face_id", "face_cls", "slab_t_m")


def _csv(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def v2_manifest():
    if sha256(V2_JSON) != PINS[V2_JSON]:
        raise ManifestError(f"PIN: {V2_JSON.name} sha256 {sha256(V2_JSON)[:8]} is not the pinned {PINS[V2_JSON][:8]}")
    return json.loads(V2_JSON.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------- T-531 lintel bars
def lintel_bar_rows(idx, v2):
    """T-531 parts against the candidate: which STR.REBAR line carries lintel bars today (expected none), the two
    proposed added lines (HELD, AT_LEAST low, no high), and the part / line-state agreement with the V2 lintel rows."""
    t = json.loads(T531.read_text(encoding="utf-8"))
    lin = {r["element_id"].split(":", 1)[1]: r for r in v2["stream_S"]["lintel_lines"]}
    ops = set(lin)
    hosts = [k for k, l in idx.items() if l["item_code"] == "STR.REBAR"
             and ("LINTEL" in l["element_id"].upper() or ops & set(l["element_id"].replace(":", " ").split()))]
    if hosts:
        raise ManifestError(f"T-531: STR.REBAR lines already carry lintel bars {hosts[:3]}: a second line would double "
                            "count")
    unit = M2.line_unit("STR.REBAR", "kg", idx, {})
    parts, seen = [], set()
    expect = {"PRODUCED": "BOUNDED_MIN_BEARING", "FLAGGED": "HELD_BY_NAME"}
    for part in ("produced", "flagged"):
        p = t["line"][part]
        if p["state"] != "AT_LEAST" or p["kg"] is not None:
            raise ManifestError(f"T-531 {part}: a part with HELD components must stay AT_LEAST with no kg")
        bad = [o for o in p["lintels"] if lin[o]["after"]["state"] != expect[part.upper()]]
        if bad:
            raise ManifestError(f"T-531 {part} lintels {bad} disagree with the V2 lintel line state")
        if seen & set(p["lintels"]):
            raise ManifestError("T-531: a lintel in both parts")
        seen |= set(p["lintels"])
        parts.append({
            "line_id": f"NEW:STR.REBAR:LINTEL_BARS:{part.upper()}", "item_code": "STR.REBAR", "unit": unit,
            "element_id": f"LINTEL_BARS:{part.upper()}", "before": None,
            "after": {"class": "HELD", "state": "AT_LEAST", "held_low": p["at_least_kg"], "held_high": None,
                      "value": None, "held_parts": p["held_parts"],
                      "straight_ceiling_kg_beside": p["ceiling_straight_kg_where_known_beside"],
                      "ceiling_held_on": p["ceiling_held_on"], "links_count_lo_beside": p["links_count_lo"]},
            "lintels": p["lintels"], "lintel_lines": [lin[o]["line_id"] for o in p["lintels"]],
            "source": M2.M1_piece("T-531") if "T-531" in M2.PIECES else
                      [{"task": "T-531", "merge": PIECES["T-531"]["merge"], "checker": PIECES["T-531"]["verdict"]}],
            "rules": ["R-T531-1", "R-T515-1"], "owner_trade": "B9-02 RC lintel reinforcement (STR.REBAR)",
            "evidence_status": "DRAWING-CONFIRMED span (ST7757 p.13 schedule); extensions / bends / laps / links HELD "
                               "(no cover, bend, hook or first-link printed: designer RFI)"})
    if seen != ops:
        raise ManifestError(f"T-531 parts {sorted(seen)} are not the 16 REQUIRED lintels {sorted(ops)}")
    rec = t["reconciliation_total"]
    return {"rule": t["rule"], "candidate_lines_carrying_lintel_bars": hosts, "added_lines": parts,
            "never_summed": "two parts, each AT_LEAST: no single line value while any part is HELD (T-531 line note)",
            "t515_to_t531": {"t515_at_least_kg": rec["t515_at_least_kg"], "t531_at_least_kg": rec["t531_at_least_kg"],
                             "delta_kg": rec["delta_kg"],
                             "cause": [{"lintel": r["opening_id"], "delta_kg": r["delta_kg"], "cause": r["cause"]}
                                       for r in t["reconciliation"] if r["delta_kg"]]},
            "code_view": {"STR.REBAR released_change_kg": 0.0, "STR.REBAR lines_added": len(parts),
                          "STR.REBAR held_lines_added": len(parts)},
            "freelancer": t["freelancer"]}


# ------------------------------------------------------------------------------------------------- T-532 + sliver
def joint_m():
    j = json.loads(T520_SUM.read_text(encoding="utf-8")).get("joint_m")
    if not isinstance(j, (int, float)) or not 0 < j < 0.05:
        raise ManifestError(f"joint thickness {j!r} not a metre value from the T-520 ledger")
    return float(j)


def roles():
    return {r["kind"]: r["plan_role"] for r in _csv(T532_KIND)}


def run_pieces():
    by = {}
    for x in _csv(T274_PIECES):
        by.setdefault(x["run_key"], []).append(x)
    for k in by:
        by[k].sort(key=lambda x: int(x["seq"]))
    return by


def head_of(piece, j):
    """the joint head a masonry piece carries; a sliver (shorter than one joint) is refused."""
    if float(piece["len_m"]) < j:
        raise ManifestError(f"SLIVER: piece {piece['run_key']}#{piece['seq']} is {float(piece['len_m']):.6f} m < joint "
                            f"{j} m: it carries no head of its own (R-T538-1)")
    return {f: (piece.get(f) or None) for f in HEAD_FIELDS}


def resolve_head(pieces, i, step, j, role):
    """head for the masonry piece i of one run; step = +1 / -1 is the direction AWAY from the column."""
    if role.get(pieces[i]["kind"]) != "MASONRY":
        raise ManifestError(f"piece {i} is {pieces[i]['kind']}: not masonry")
    if float(pieces[i]["len_m"]) >= j:
        return {"state": "OWN", "piece": i, "head": head_of(pieces[i], j)}
    k = i
    while 0 <= k < len(pieces) and role.get(pieces[k]["kind"]) == "MASONRY" and float(pieces[k]["len_m"]) < j:
        k += step
    if not (0 <= k < len(pieces)) or role.get(pieces[k]["kind"]) != "MASONRY":
        return {"state": "HELD", "piece": None, "head": None,
                "held": "no full masonry piece before the next column / run end (R-T538-1): head HELD by name"}
    h = head_of(pieces[k], j)
    own = {f: (pieces[i].get(f) or None) for f in HEAD_FIELDS}
    return {"state": "FROM_ADJACENT_SAME" if own == h else "FROM_ADJACENT_CHANGED", "piece": k, "head": h,
            "sliver": {"piece": i, "len_m": float(pieces[i]["len_m"]), "own_fields": own}}


def junction_masonry_piece(row, n):
    at = row["at"]
    if at.startswith("end "):
        e = int(at.split()[1])
        return (0, +1) if e == 0 else (n - 1, -1)
    a, b = (int(x) for x in at.split()[1].split("/"))
    if row["face"] == "column_start":          # the column is piece b: masonry at a, away = towards a - 1
        return a, -1
    if row["face"] == "column_end":            # the column is piece a: masonry at b, away = towards b + 1
        return b, +1
    raise ManifestError(f"{row['run']} {at}: junction face {row['face']!r} unknown")


def sliver_check(j=None, threshold_alt=0.005):
    j = joint_m() if j is None else j
    role, P = roles(), run_pieces()
    out = []
    for r in _csv(T532_JUN):
        if r["state"] != "LISTED":
            continue
        ps = P[r["run"]]
        i, step = junction_masonry_piece(r, len(ps))
        res = resolve_head(ps, i, step, j, role)
        out.append({"run": r["run"], "wall": r["wall_id"], "at": r["at"], "class": r["class"], "source": r["source"],
                    "masonry_piece": i, "piece_len_m": float(ps[i]["len_m"]), **res})
    sl = [x for x in out if x["state"] != "OWN"]
    alt = [x for x in out if (x["piece_len_m"] < threshold_alt) != (x["piece_len_m"] < j)]
    return {"rule": RULE_SLIVER, "joint_m": j, "junctions_listed": len(out),
            "by_state": {s: len([x for x in out if x["state"] == s]) for s in
                         ("OWN", "FROM_ADJACENT_SAME", "FROM_ADJACENT_CHANGED", "HELD")},
            "sliver_junctions": sl,
            "checker_5mm_vs_joint": {"threshold_m": threshold_alt, "classified_differently": len(alt),
                                     "rows": [(x["run"], x["at"], x["piece_len_m"]) for x in alt]},
            "quantity_effect": "none: no wired or proposed figure in this manifest uses a junction head; the head is "
                               "the input the T-539 tie / mesh ledgers and the S package read"}


def end_census_rows(v2):
    s = json.loads(T532_SUM.read_text(encoding="utf-8"))
    rec = s["reconcile_t526"]
    if not (rec["listed_equal"] and rec["held_equal"] and not rec["only_v3"] and not rec["only_t526"]):
        raise ManifestError("T-532 ends are not set-equal to T-526")
    v2c = v2["stream_S"]["column_end_census"]
    d = rec["carried_deltas"]
    tm = v2c["ties_and_mesh"]
    if (d["d_ties_nr"], d["d_mesh_owner_ml"], d["d_mesh_drawing_ml"]) != \
            (tm["d_ties_nr_measured"], tm["d_mesh_owner_ml"], tm["d_mesh_drawing_ml"]):
        raise ManifestError("T-532 carried tie / mesh deltas differ from the V2 (T-526) figures")
    if any(d[k] != 0.0 for k in ("d_length_m", "d_blockwork_m2", "d_blocks_nr")):
        raise ManifestError("T-532 moves a MAS.BLOCK quantity")
    (w09,) = v2c["perimeter_mortar"]
    per = [p for p in v2["stream_S"]["perimeter_lines"] if p["host_line_id"] == w09["perimeter_line_host"]]
    return {"rule": s["rule"], "source": [{"task": "T-532", "merge": PIECES["T-532"]["merge"],
                                           "checker": PIECES["T-532"]["verdict"]}],
            "end_junctions_by_class": s["end_junctions_by_class"], "interior_listed_by_class":
                s["interior_listed_by_class"], "interior_vs_t355": s["interior_vs_t355"],
            "set_equal_to_t526": {"listed_n": rec["listed_n"], "held_n": rec["held_n"]},
            "candidate_lines_moved": 0,
            "perimeter_1F_W09": {"host_line": w09["perimeter_line_host"], "after_m3": w09["t526_after_m3"],
                                 "perimeter_line": per[0]["line_id"] if per else None,
                                 "state": "UNCHANGED V2 -> V3 (T-532 re-reads the same end: one write)"},
            "ties_and_mesh": {"d_ties_nr": d["d_ties_nr"], "d_mesh_owner_ml": d["d_mesh_owner_ml"],
                              "d_mesh_drawing_ml": d["d_mesh_drawing_ml"],
                              "state": "NO LINE: still no tie / crack-mesh line in V3.0.58 or the T-498 stage; the "
                                       "ends are now wireable without raising (T-532); ledger versions and the line "
                                       "family are T-539"}}


# ------------------------------------------------------------------------------------------------- sand
def sand_rows(idx):
    a, b = json.loads(T535.read_text(encoding="utf-8")), json.loads(T540.read_text(encoding="utf-8"))
    codes = sorted({l["item_code"] for l in idx.values() if "SAND" in l["item_code"]})
    g, g2 = a["group"], b["group"]
    if list(g["procurement_at_least_m3"]) != list(g2["m3"]):
        raise ManifestError("T-540 group m3 is not the T-535 group")
    if g2["t"] is not None or g2["loads"] is not None:
        raise ManifestError("T-540: tonnes / loads valued without a sourced density / load size")
    before, after = a["t523_group_at_least_m3"], g["procurement_at_least_m3"]
    delta = [_r(y - x) for x, y in zip(before, after)]
    if delta != [_r(x) for x in a["delta_vs_t523_m3"]]:
        raise ManifestError("T-535 delta does not reproduce")
    st = a["stair_allowance_beside"]
    return {"candidate_sand_lines": codes, "candidate_lines_moved": 0,
            "binding_group": {"key": "SAND_LOOSE", "unit": g["unit"], "villa": g["villa"],
                              "before_t523_at_least_m3": before, "after_t535_at_least_m3": after,
                              "delta_m3": delta, "status": g["status"], "open_members": len(g["open"]),
                              "members": g["members"],
                              "cause": [
                                  {"what": "stair bed members: procurement = V7 installed x (1 + Q-45 5 %)",
                                   "before_m3": st["t523_bound_procurement_m3"], "after_m3": st["v7_procurement_m3"],
                                   "rule": "R-T535-2 (rounded-rate allowance is a layer, never procurement)"},
                                  {"what": "T-520 perimeter joint key joins the group (own key, absent from T-523)",
                                   "rule": "R-T535-1 / R-T523-1"}],
                              "allowance_beside": st["layer"]},
            "tonnes": g2["t_status"], "loads": g2["loads_status"],
            "source": [{"task": t, "merge": PIECES[t]["merge"], "checker": PIECES[t]["verdict"]}
                       for t in ("T-535", "T-540")],
            "state": "NO LINE: sand is a material-group key (T-523 binding), not a candidate line; the group stays "
                     "AT_LEAST / HELD (194 open members); to-buy loads and tonnes HELD (pack / density unsourced)"}


# ------------------------------------------------------------------------------------------------- T-534 stair area
STAIR_BED_CODES = ("FIN.MARBLE.TREAD", "FIN.MARBLE.RISER", "FIN.MARBLE.LANDING")


def stair_area(idx, v2):
    """the stair bed area the V7 keys sit on: the RELEASED stair marble lines of the candidate (T-511 census: 8 treads,
    1 riser, 2 landings), cross-checked against the V7 mortar (area x 0.03 m bed)."""
    ls = sorted((k, l) for k, l in idx.items() if l["item_code"] in STAIR_BED_CODES and l["class"] == "RELEASED")
    a = _r(sum(l["measured_net"] for _, l in ls), 4)
    v7 = v2["finish_v6_v7"]["v7_stair_bed"]
    if abs(a * 0.03 - v7["mortar_m3_from_cement"]) > 1e-5:
        raise ManifestError(f"stair area {a} x 0.03 is not the V7 mortar {v7['mortar_m3_from_cement']}")
    return {"area_m2": a, "lines": [k for k, _ in ls], "lines_by_code": {c: len([1 for _, l in ls if l["item_code"] == c])
                                                                        for c in STAIR_BED_CODES},
            "state": "HELD BY NAME in this tree: T-534 is not a source (READY f97634e0)",
            "once_t534_merges": stair_area_state(True, a),
            "until_then": stair_area_state(False, a),
            "t534_gate_a": "Verifier 2026-11-05T18:05Z GATE A PASS: Q-53 39.485 -> 35.4313 m2 reconciled, residual 0 "
                           "(RULE_DIFFERENCE scope + ENGINE_RIGHT); riser bed Q-45 B PROVISIONAL",
            "v7_on_it": {"mortar_m3": v7["mortar_m3_from_cement"], "cement_bags": v7["installed_cement_bags"],
                         "sand_m3": v7["installed_sand_m3"], "wiring_after": v7["wiring_after"]},
            "rule": "the manifest states both branches; it never reads the live merge state of a READY piece "
                    "(F-C-T536-1)"}


def stair_area_state(t534_merged, area):
    """the state the S / F package applies; t534_merged is decided by the PACKAGE run (merge-base), never here."""
    if t534_merged:
        return {"state": "AT_LEAST", "value_m2": area, "source": "T-534"}
    return {"state": "HELD_BY_NAME", "value_m2": None, "why": "T-534 (stair bed area) not merged"}


# ------------------------------------------------------------------------------------------------- build
def build():
    v2 = v2_manifest()
    M2.check_sources(PIECES)
    idx = M1.line_index()
    bars = lintel_bar_rows(idx, v2)
    man = {
        "schema": SCHEMA, "candidate": M1.CANDIDATE, "task": "T-538",
        "supersedes": "T-536 WIRING_MANIFEST_V2.json (V2; every V2 line move carried unchanged)",
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in
                   (V2_JSON, T531, T532_SUM, T532_JUN, T532_KIND, T274_PIECES, T520_SUM, T535, T540)},
        "pieces_new": {k: dict(v) for k, v in sorted(NEW_PIECES.items())},
        "not_sources": NOT_SOURCES,
        "v2_line_moves_carried": len(v2["line_moves"] or []),
        "lintel_bars": bars,
        "end_census_v3": end_census_rows(v2),
        "sliver_check": sliver_check(),
        "sand": sand_rows(idx),
        "stair_bed_area": stair_area(idx, v2),
        "v2_to_v3": [
            {"line_id": a["line_id"], "change": "ADDED (proposed, HELD AT_LEAST)", "after": a["after"],
             "cause": "T-531 R-T531-1"} for a in bars["added_lines"]],
        "candidate_lines_moved_v2_to_v3": 0,
        "findings": [
            "F-C-T536-1 closed: the t536 unmerged-source case runs on a synthetic repository (T-538)",
            "F-C-T532-1 closed as a check: R-T538-1 (head from the adjacent full piece or HELD); see sliver_check",
            "F-T538-1: no candidate STR.REBAR line carries lintel bars: the S package ADDS two HELD AT_LEAST lines "
            "(PRODUCED / FLAGGED), never one summed value",
            "F-T538-2: ties +30 nr / mesh +40.90 m.l (owner band) / +44.10 (drawing band) still no line (T-539)",
        ],
        "released_quantities_changed": 0, "candidate_files_touched": 0,
    }
    return man


def dumps(man):
    return M1.dumps(man)


if __name__ == "__main__":
    m = build()
    if "--check" in sys.argv:
        ok = dumps(m) == OUT_JSON.read_text(encoding="utf-8")
        print("CHECK", "OK" if ok else "DIFFERS")
        sys.exit(0 if ok else 1)
    OUT_JSON.write_text(dumps(m), encoding="utf-8")
    print("written", OUT_JSON.relative_to(ROOT))
