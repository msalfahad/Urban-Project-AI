"""T-611 WIRING MANIFEST V13 + OVERLAY DRY RUN (R-T611-1; lane I, non-candidate, research only).

V13 carries the Checker-merged fix row FR-T606-1 (T-606, merge 1ddf21f4): the 1F living room skirting line runs on the
stair-opening walls where no finished floor stands at +5.50 (Checker own read: 11.170 lm, ENGINE_WRONG). It overlays it
on a COPY of the ARCH_TAKEOFF_V3.0.58 line index AFTER V2 .. V12 (the T-604 order; R-T580-1 / R-T588-1 / R-T593-1 /
R-T596-1 / R-T604-1 code reused read only). Nothing is wired; no candidate, released (V2.9 + route G), rule, knowledge
or registry file is written; no drawing is read: every figure comes from a committed, Checker-merged output or the
Checker's own verdict line, each named.

R-T611-1 (every villa on the engine's line-index scheme):
  (a) MERGED ONLY: a fix row enters only from a task MERGED with a Checker verdict (R-T596-1 (a) code). A task that is
      MERGED but whose verdict changes no quantity (T-605, T-607, T-599 here) carries 0 rows and is listed by name;
      a task not MERGED at claim (T-610) is refused.
  (b) FLOORLESS FACE DEDUCTION: a released room skirting line loses the length of its wall faces that meet no finished
      floor (UP-SKIRT-001 1.4.0: skirting only where a finished floor meets a finished wall). The deducted length is
      the CHECKER's figure, built from named components that re-add to it; the worker's figure is kept beside with each
      named difference (worker - named differences = Checker, exactly). The finding's stated line net must equal the
      line's state before the row (the base the finding measured on); the deduction never exceeds the line and never
      leaves 0 (a whole floorless line is EXCLUDED by its own rule, not SET to 0).
  (c) ABSORB, NOT TWO WRITERS: an earlier TEXT_ONLY op on the same line (V12 FR-T601-3 label) is taken out of its
      package and carried by the V13 row (R-T593-1 (f) precedent): one Gate B unit per line (R1); its stated before
      must equal the V13 row's before.
  (d) ONCE: one deduction id per line; a second row with the same finding id, or a stated before that already carries
      the deduction, is refused (STALE in the overlay, refused here).
  (e) RESTATE ON THE BASE: the after-total is stated on the V12 overlay base AND on the Checker's V3.0.58 base, and the
      two differ by exactly the merged V12 skirting delta (+0.30 lm FR-T601-1).
Rebuild: `python3 -I research/agents_t611/manifest_v13.py` (`--check`).
"""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
T604_DIR = ROOT / "research/agents_t604"
for _p in (ROOT / "research/agents_t580", ROOT / "research/agents_t588", ROOT / "research/agents_t593",
           ROOT / "research/agents_t596", T604_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import manifest_v12 as M12                                            # noqa: E402  (R-T604-1, read only)

M11, M10, M9, OV = M12.M11, M12.M10, M12.M9, M12.OV
D, S = M11.D, M11.S

SCHEMA = "URBAN_T611_WIRING_MANIFEST_V13"
RULE = "R-T611-1"
OUT_JSON = HERE / "out/WIRING_MANIFEST_V13.json"
IN = {
    "T606": ROOT / "research/agents_t606/out/T606_OUTLINE_CAUSES.json",
    "V12": T604_DIR / "out/WIRING_MANIFEST_V12.json",
    "V12_CODE": T604_DIR / "manifest_v12.py",
}
PINS = {
    "T606": "e71d85471859e284a0163d44d4a417b8c79183f92f1cc167dff6a0ae6362c8c5",
    "V12": "3c2d0ec075c2489960c4ab0d1eab1f2eb37430ed4db733f5a57d65eaec748fb7",
    "V12_CODE": "1dd5dbc7e71328e26a994c5853ed556eb18edfc6ed18b14ce74f5c95f8ba99cf",
}

# R-T611-1 (a): board MERGED verdicts at claim (2026-11-07T21:00Z; Verifier text abridged, full text on BOARD.md)
MERGED = {
    "T-606": {"merge": "1ddf21f4",
              "verdict": "BOARD T-606 VERIFIER 2026-11-07T17:59Z (f): F-T606-1 re-measured: west wall AF7 from B74 y to "
                         "AEC = 4.000, south wall AEC from AF7 to the stair-box edge AF5 = 7.020 (5.87 + 1.15), column "
                         "300E inside the span 2 x 0.05 = 0.10, column 3008 straddles AF5: only its west return 0.05 "
                         "faces the void; its east return faces the 1F floor and keeps skirting -> Checker 11.170 lm, "
                         "worker 11.22 (+0.05 = 3008 east return, named). ENGINE_WRONG CONFIRMED on 11.17: candidate "
                         "FIN.SKIRTING 209.428592 -> 198.258592 lm (-5.33 %) on V3.0.58 (198.558592 after V12), lane I "
                         "fix row needed. Line status: room skirting PARTIALLY VERIFIED"},
    "T-605": {"merge": "c2db2962",
              "verdict": "BOARD T-605 VERIFIER 2026-11-07T20:57Z: F9 / FN 180C pair concrete + blinding VERIFIED; "
                         "CONC.FOOTING line unchanged PARTIALLY VERIFIED. No quantity change"},
    "T-607": {"merge": "ad0290c2",
              "verdict": "BOARD T-607 VERIFIER 2026-11-07T20:57Z: steps 7 nr / 8.40 lm and nosing 8.40 lm = ONE cause "
                         "C-T607-1, counted once in totals; ENGINE_RIGHT on the count. No quantity change"},
    "T-599": {"merge": "9dc3c2d3",
              "verdict": "BOARD T-599 VERIFIER 2026-11-07T19:55Z: UP-CONC-JOINT-001 1.0.0 (LEAD_ADOPTED under Q-62 A); "
                         "residuals UNRESOLVED -> T-600, nothing released, no quantity change"},
}
NO_ROW = {"T-605": "footing overlap counted once: candidate CONC.FOOTING unchanged (no fix row in the source)",
          "T-607": "steps / nosing shared residual: one cause C-T607-1 for the statement; no candidate line moves",
          "T-599": "joint rule now citable (UP-CONC-JOINT-001 1.0.0); no manifest V2 .. V12 row writes a joint line: "
                   "the citation belongs to the reconciled statement (T-609 r2), 0 manifest rows"}
NOT_MERGED = {"T-610": "TODO at claim (beam band overlap): its rows are refused until it is MERGED"}

# The Checker's own components of F-T606-1 (verdict line above), lm; they must re-add to CHECKER_LM
FINDING = "F-T606-1"
FIX_ROW = "FR-T606-1"
CHECKER_LM = "11.17"
CHECKER_PARTS = [("AF7 west wall, B74 y to AEC", "4.000"),
                 ("AEC south wall, AF7 to stair-box edge AF5 (5.87 + 1.15)", "7.020"),
                 ("column 300E returns inside the span (2 x 0.05)", "0.100"),
                 ("column 3008 west return (faces the void; straddles AF5)", "0.050")]
WORKER_DIFFS = [("column 3008 east return: faces the 1F floor east of AF5, keeps skirting (Checker)", "0.050")]
V12_SKIRT_DELTA = "0.3"            # FR-T601-1 (T-604 V12): the only V12 move on FIN.SKIRTING|lm
P_FLOOR = "FLOORLESS_FACES (T-606 FR-T606-1; absorbs V12 FR-T601-3 on the same line)"
SKIRT = ("FIN.SKIRTING", "lm")


class ManifestError(Exception):
    pass


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def pins():
    for k, pin in PINS.items():
        if sha256(IN[k]) != pin:
            raise ManifestError(f"PIN: {IN[k].name} sha256 {sha256(IN[k])[:8]} is not the pinned {pin[:8]}")


def require_merged(task, merged=None):
    try:
        return M11.require_merged(task, MERGED if merged is None else merged)
    except M11.ManifestError as e:
        raise ManifestError(str(e)) from None


def no_row_sources(merged=None, no_row=None, not_merged=None):
    """R-T611-1 (a): merged tasks with no fix row are listed (0 rows); unmerged ones refused by name."""
    m = MERGED if merged is None else merged
    out = {}
    for t, why in (NO_ROW if no_row is None else no_row).items():
        require_merged(t, m)
        out[t] = {"merge": m[t]["merge"], "rows": 0, "why": why}
    refused = {}
    for t, why in (NOT_MERGED if not_merged is None else not_merged).items():
        try:
            require_merged(t, m)
            raise ManifestError(f"{t} is listed as not merged but carries a merge: build its rows")
        except ManifestError as e:
            if "listed as not merged" in str(e):
                raise
            refused[t] = {"refusal": str(e), "state": why}
    return out, refused


# ---- R-T611-1 (b): the deducted length ------------------------------------------------------------------------------

def checker_length(parts=None, total=None):
    parts = CHECKER_PARTS if parts is None else parts
    tot = D(CHECKER_LM if total is None else total)
    s = sum((D(v) for _, v in parts), Decimal(0))
    if s != tot:
        raise ManifestError(f"Checker components re-add to {S(s)}, not the verdict {S(tot)}")
    if tot <= 0:
        raise ManifestError("a floorless deduction of 0 or less is no row")
    return tot


def reconcile_worker(finding, checker, diffs=None):
    """worker lm - named differences = Checker lm, exactly; every difference has a name."""
    diffs = WORKER_DIFFS if diffs is None else diffs
    w = D(finding["lm"])
    if any(not n for n, _ in diffs):
        raise ManifestError("an unnamed worker / Checker difference")
    named = sum((D(v) for _, v in diffs), Decimal(0))
    if w - named != checker:
        raise ManifestError(f"worker {S(w)} - named {S(named)} = {S(w - named)} != Checker {S(checker)}")
    return {"worker_lm": S(w), "named_differences": [{"what": n, "lm": v} for n, v in diffs],
            "checker_lm": S(checker), "governs": "Checker (own re-measure, verdict)"}


def floorless_row(finding, idx, checker, source="T-606", merged=None, done=(), parts=None, finding_id=FINDING):
    """one SET on the finding's room line: before = its state, after = released (net - checker)."""
    src = require_merged(source, merged)
    parts = CHECKER_PARTS if parts is None else parts
    if finding.get("id") != finding_id or finding.get("verdict_proposal") != "ENGINE_WRONG":
        raise ManifestError(f"{finding.get('id')}: not the {finding_id} ENGINE_WRONG finding")
    if finding_id in done:
        raise ManifestError(f"{finding_id}: already deducted once (R-T611-1 (d))")
    lid = finding["line"]
    line = idx.get(lid)
    if line is None or (line["item_code"], line.get("unit")) != SKIRT:
        raise ManifestError(f"{lid}: not a FIN.SKIRTING lm line in the index")
    before = OV.state(line)
    if before["class"] != "RELEASED":
        raise ManifestError(f"{lid}: {before['class']}: only a released room line takes a floorless deduction")
    net = D(before["measured_net"])
    if net != D(finding["line_net"]):
        raise ManifestError(f"{lid}: line net {S(net)} is not the finding's base {finding['line_net']} "
                            "(stale or already deducted)")
    after_v = net - checker
    if after_v <= 0:
        raise ManifestError(f"{lid}: {S(net)} - {S(checker)} = {S(after_v)}: a wholly floorless line is EXCLUDED by "
                            "rule, never SET to 0 or below")
    r = M9.row(P_FLOOR, FIX_ROW, "SET", lid, before, M9.released(float(after_v)), "PARTIALLY VERIFIED",
               src["verdict"],
               beside={"finding": finding_id, "deducted_lm": S(checker),
                       "components": [{"what": n, "lm": v} for n, v in parts],
                       "edges_worker": finding["edges"], "net_before": S(net), "net_after": S(after_v),
                       "why": finding["why"], "rule": "UP-SKIRT-001 1.4.0 / R-T606-1",
                       "who_is_right": f"ENGINE_WRONG (Checker CONFIRMED on {S(checker)} lm)"},
               note="R-T611-1 (b): floorless wall faces leave the room line; the line stays RELEASED")
    r["supersedes"] = [f"{finding_id} worker proposal {finding['lm']} lm ({finding.get('released_V3_0_58')} -> "
                       f"{finding.get('if_confirmed')}, {finding.get('pct')} %)",
                       "the Checker's restatement on the candidate base (restated on the overlay base here)"]
    return r


def absorb_label_pkg(order, pkg_name, line_id, before):
    """R-T611-1 (c): pkg_name's TEXT_ONLY op on line_id leaves its package, to be carried by the V13 row."""
    try:
        return M10.absorb(order, pkg_name, line_id, before)
    except M10.ManifestError as e:
        raise ManifestError(str(e)) from None


def absorb_label(order, line_id, before):
    """the V12 FR-T601-3 label op (DOORLESS_JAMBS package) on the 1F living line."""
    return absorb_label_pkg(order, M12.P_JAMB, line_id, before)


# ---- overlay ----------------------------------------------------------------------------------------------------

def v12_state():
    """the T-604 build up to its overlay (read only), so V13 steps from the exact V12 state."""
    idx, order11, rul, after11, rep11, t584 = M12.v11_state()
    t601, t602 = M12._json(M12.IN["T601"]), M12._json(M12.IN["T602"])
    jamb_pkg, _ = M12.pkg_jambs(t601, after11)
    gate_row, _ = M12.gate_step(t602, after11, M12.v10_door_rows(order11))
    order12 = order11 + [jamb_pkg, (M12.P_GATE, [gate_row])]
    after12, rep12 = OV.apply(idx, order12, rul)
    return idx, order12, rul, after12, rep12, t584


def build():
    pins()
    t606, v12j = _json(IN["T606"]), _json(IN["V12"])
    idx, order12, rul, after12, rep12, t584 = v12_state()
    if len(after12) != v12j["overlay"]["lines"]["after_v12"]:
        raise ManifestError("V12 state rebuild differs from the committed V12 line count")
    for r in v12j["rows"]:
        if r["kind"] in ("ADD", "SET") and not OV.same_state(OV.state(after12[r["line_id"]]), r["after"]):
            raise ManifestError(f"{r['line_id']}: V12 rebuild differs from the committed V12 row")
    t12 = OV.totals(after12)
    if t12["FIN.SKIRTING|lm"] != v12j["skirting"]["FIN.SKIRTING|lm"]["v12"]:
        raise ManifestError("V12 FIN.SKIRTING totals rebuild differs from the committed V12")
    sources, refused = no_row_sources()
    checker = checker_length()
    finding = t606["finding"]
    worker = reconcile_worker(finding, checker)
    row = floorless_row(finding, after12, checker)
    order, taken = absorb_label(order12, row["line_id"], row["before"])
    row["absorbs"] = {"op_id": taken["op_id"], "kind": taken["kind"], "note": taken.get("note"),
                      "beside": taken.get("beside"), "rule": "R-T611-1 (c) / R-T593-1 (f)"}
    v13 = [(P_FLOOR, [row])]
    M9.validate_rows([row])
    order13 = order + v13
    after13, rep = OV.apply(idx, order13, rul)
    others = sorted(k for k in set(after12) | set(after13) if k != row["line_id"] and after12.get(k) != after13.get(k))
    if others:
        raise ManifestError(f"lines V13 does not write changed: {others[:5]}")
    t13 = OV.totals(after13)
    dt = OV.diff_totals(t12, t13)
    if sorted(dt) != ["FIN.SKIRTING|lm"]:
        raise ManifestError(f"totals moved on {sorted(dt)}: V13 moves FIN.SKIRTING only")
    sk12, sk13 = t12["FIN.SKIRTING|lm"], t13["FIN.SKIRTING|lm"]
    r12, r13 = D(sk12["released"]), D(sk13["released"])
    if r12 - r13 != checker:
        raise ManifestError(f"FIN.SKIRTING {S(r12)} -> {S(r13)} moved by {S(r12 - r13)}, not {S(checker)}")
    for k in ("released_n", "held_n", "held_blank_n", "held_low", "held_high", "held_high_open_n", "excluded_n"):
        if sk12[k] != sk13[k]:
            raise ManifestError(f"FIN.SKIRTING {k} moved {sk12[k]} -> {sk13[k]}: V13 moves the released sum only")
    # R-T611-1 (e): restate on both bases
    base_c = D(t606["finding"]["released_V3_0_58"])
    if r12 - base_c != D(V12_SKIRT_DELTA) or D(v12j["skirting"]["released_delta_lm"]) != D(V12_SKIRT_DELTA):
        raise ManifestError(f"V12 base {S(r12)} - V3.0.58 {S(base_c)} is not the V12 delta {V12_SKIRT_DELTA}")
    checker_after_c = base_c - checker
    if checker_after_c + D(V12_SKIRT_DELTA) != r13:
        raise ManifestError("the two restatements do not differ by the V12 delta")
    pct = ((r13 - r12) / r12 * 100).quantize(Decimal("0.01"))
    status = {}
    for r in rep["rows"]:
        status.setdefault(r["package"], {}).setdefault(r["status"], 0)
        status[r["package"]][r["status"]] += 1
    flagged = [r for r in rep["rows"] if r["status"] != "APPLIED"]
    if any(r["package"] == P_FLOOR for r in flagged):
        raise ManifestError(f"the V13 row is not APPLIED: {flagged}")
    # the T-412 stair census stays 0 doubles / 0 orphans (V13 writes no step / nosing line)
    t412 = M11.load_t412()
    nrows, _ = M11.nosing_ledger(t412, M11._json(M11.IN["T598"]))
    cen = M9.census_on(after13, M11.census_edges(t412, nrows), t584, {M9.E1_LINE: ("ST-03", "E1")})
    if cen["doubles"] or cen["orphans"]:
        raise ManifestError("stair census doubles / orphans after V13")
    group_his = "43.78"
    net_b, net_a = D(row["before"]["measured_net"]), D(row["after"]["measured_net"])
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-611", "candidate": M9.T580.CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in IN.values()},
        "sources_merged": {k: v["merge"] for k, v in MERGED.items()},
        "sources_no_row": sources, "sources_refused": refused,
        "supersedes": {row["op_id"]: row["supersedes"]},
        "absorbed": {"op_id": taken["op_id"], "into": row["op_id"],
                     "why": "R1: one Gate B unit per line; the V12 FR-T601-3 op writes no quantity and states the same "
                            "before (label PASSAGE -> LIFT LANDING DOOR on 1F OP-007 kept, carried by this row)"},
        "deduction": {"finding": FINDING, "checker": [{"what": n, "lm": v} for n, v in CHECKER_PARTS],
                      "checker_lm": S(checker), "worker": worker},
        "skirting": {"FIN.SKIRTING|lm": {"v12": sk12, "v13": sk13},
                     "released_delta_lm": S(r13 - r12), "pct_vs_v12": format(pct, "f"),
                     "on_v12_base": f"{S(r12)} - {S(checker)} = {S(r13)}",
                     "on_v3_0_58_base": f"{S(base_c)} - {S(checker)} = {S(checker_after_c)} (Checker's restatement)",
                     "bases_differ_by": f"{V12_SKIRT_DELTA} = FR-T601-1 jamb line (V12), both sides of the deduction",
                     "line": {"id": row["line_id"], "net_before": S(net_b), "net_after": S(net_a)},
                     "his": f"1F living group (T-574): ours {S(net_b)} -> {S(net_a)} lm vs his {group_his} lm; the gap "
                            f"widens {S(net_b - D(group_his))} -> {S(net_a - D(group_his))} lm: ENGINE_WRONG on a "
                            "physical cause, freelancer agreement is not the test; his outline cause stays split by "
                            "T-606 (no %)",
                     "held": "held lines and bounds unchanged (6, 0 .. 0); no blank became 0"},
        "rows": [dict(row, package=P_FLOOR)],
        "overlay": {
            "lines": {"base": len(idx), "after_v12": len(after12), "after_v13": len(after13)},
            "order": [{"package": n, "ops": len(o), "status": status.get(n, {})} for n, o in order13],
            "flagged_rows": flagged,
            "stale": sum(r["status"] == "STALE" for r in rep["rows"]),
            "two_package_lines": 0,                    # OV.apply raises R1 otherwise
            "unexplained_conflicts": sum(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]),
            "other_lines_changed_vs_v12_overlay": others,
            "v13_vs_v12_totals": dt,
        },
        "stair_edge_census_after_v13": {"edges": cen["edges"], "doubles": len(cen["doubles"]),
                                        "orphans": len(cen["orphans"])},
        "findings": {
            "F-T611-1": "the 11.17 lm leave the room line only; whether a balustrade / void-edge item takes the stair "
                        "opening edge (his outline walks B74 / B75 / D24 / AF5, 11.02) is not a skirting question and "
                        "is not in the candidate: no line written, none assumed",
        },
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str) + "\n"


def main(argv):
    text = dumps(build())
    if "--check" in argv:
        ok = OUT_JSON.exists() and OUT_JSON.read_text(encoding="utf-8") == text
        print("T-611 manifest V13: committed output", "is the rebuild" if ok else "DIFFERS from the rebuild")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
