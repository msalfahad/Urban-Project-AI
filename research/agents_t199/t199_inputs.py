"""T-199: the URBAN_V3030_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.30 (engine.source.arch_v3030), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build); nothing is typed:

  research/agents_t332/T199_FILL_T332.csv  T-332 r2 (MERGED 61d5597e, Verifier 2026-10-29 22:02 UTC Gate A PASS: own
      re-aggregation of all 678 FILL rows from the face ledger, HELD blank): the formwork r5 faces (T-163 r3 + T-264 r4
      + T-293 parts 1-3 + T-308 r5 rules: CB5 span 2 once, BAND0049 HELD) bound to the V3.0.21 concrete line ids, one
      row per (line, status, alternative, method);
  research/agents_t332/FORMWORK_T332_BY_FACE.csv  the same task: every face, incl. the faces tied to NO line (24
      parapet runs from T-311, 2 lift-pit faces, 12 r5 pieces), the 69 SPLIT_UNRESOLVED faces, the named aggregates
      (R4-339 stair sides: SUPERSEDED by T-352), INFO and the S1 scenario rows (never in the candidate);
  research/agents_t332/CANDIDATE_V3021_CONCRETE_LINES.json  the same task: the bound concrete lines as they stood
      (id, item, element, state, quantity): the engine re-checks each on the candidate of record (stale binding);
  research/agents_t352/T199_FILL_T352_ADDENDUM.csv + STAIR_FORMWORK_T352_BY_FACE.csv  T-352 (MERGED b12e10de,
      Verifier 2026-10-30 00:09 UTC Gate A PASS: own re-measure of the 7 valued faces): the stair SIDE faces, 27 faces on
      8 STR.CONC.STAIR lines;
  research/agents_t164/RAILINGS_T164.csv + SHUTTERS_T164.csv  T-164 (MERGED 390fabf4, Verifier 2026-10-22 20:21 UTC
      Gate A PASS: own re-measure RL-02 4.921 / RL-03 7.967 lm, 0.0 %): railing runs (lm, installed path) and shutters.

Records (rows of the inputs; the engine decides the line state from them, never a value of its own):
  formwork      one per FILL row with method G or E=G (E is the comparison method: carried beside, never a line);
  alternatives  OQ-10 FORMED / EARTH_CAST pairs (owner question open): one BLANK line, both figures beside, never summed;
  untied        HELD faces with no candidate concrete line: one BLANK line per face (parapet / lift pit / r5 pieces /
                SPLIT_UNRESOLVED / named aggregates), never inside a concrete line's total;
  stair_sides   the T-352 addendum rows (R4-339 superseded);
  railings      one per T-164 run (lm, segments summed, corners once as T-164 measured them);
  shutters      one per drawn window pair (pcs), m2 HELD.

    python3 -I research/agents_t199/t199_inputs.py [project_id]      # prints the counts and totals
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
FILL = ROOT / "research/agents_t332/T199_FILL_T332.csv"
FACE = ROOT / "research/agents_t332/FORMWORK_T332_BY_FACE.csv"
CONC = ROOT / "research/agents_t332/CANDIDATE_V3021_CONCRETE_LINES.json"
ADD = ROOT / "research/agents_t352/T199_FILL_T352_ADDENDUM.csv"
SFACE = ROOT / "research/agents_t352/STAIR_FORMWORK_T352_BY_FACE.csv"
RAIL = ROOT / "research/agents_t164/RAILINGS_T164.csv"
SHUT = ROOT / "research/agents_t164/SHUTTERS_T164.csv"
DGB = ROOT / "research/agents_t199/DOWNGRADE_BOUND_V3029.json"     # t199_downgrades.py from the board record file
PINS = {FILL: "8a36cf9a54a755c6f6e7b9639ecfa66a5edad824494c771f3863fd07b5a502a6",
        FACE: "15c188724a60d58030feddc554a5a63df31ada636d5dc40853f6130c1a3700b3",
        CONC: "60e642193f0c77f8ea9199ee7a20c1bc876e870d2ce7d58fb73765ffe93928d2",
        ADD: "848f11be89d92fbb10318761c59735f083ab2c6efb68beabd89c7945099d7541",
        SFACE: "049fbd000f6614d99bc4257f6352f1618bc046508c877d2875a1abd87f7618c2",
        RAIL: "2d7e8b4d03552e5249b95c70c5a23cefec21565d1fc5a27810aa8ef8b613d64b",
        SHUT: "8707d128e408af84d28c100e5c7769ae986166fd24d4476d88ba0abe24a333ce",
        DGB: "eef007d6eda0e016a7a2cab4a618460c112ada8f9ece0c31b3f7dfd3777a7586"}
SOURCES = {
    "T-332": {"file": "research/agents_t332/T199_FILL_T332.csv", "pin": FILL,
              "merge_commit": "61d5597e4a38bdcc29f206bf514101cfa455da98",
              "checker_run": "Verifier 2026-10-29 22:02 UTC: T-332 r2 Gate A PASS, MERGED 61d5597e (own "
                             "re-aggregation of all 678 FILL rows from the face ledger: HELD m2 blank, 0 mismatches)"},
    "T-352": {"file": "research/agents_t352/T199_FILL_T352_ADDENDUM.csv", "pin": ADD,
              "merge_commit": "b12e10de30a70708b9ad32ffaff57503c44f0c31",
              "checker_run": "Verifier 2026-10-30 00:09 UTC: T-352 Gate A PASS, MERGED b12e10de (own re-measure of the "
                             "7 valued stair side faces by handle)"},
    "T-164": {"file": "research/agents_t164/RAILINGS_T164.csv", "pin": RAIL,
              "merge_commit": "390fabf4acd2c882eb736f2abdd8855ae783eb24",
              "checker_run": "Verifier 2026-10-22 20:21 UTC: T-164 Gate A PASS, MERGED 390fabf4 (own re-measure RL-02 "
                             "4.921 lm and RL-03 7.967 lm on P7757.dxf, 0.0 %; the other runs DRAWING-CONFIRMED)"},
}
VERIFIED_RUNS = ("RL-02", "RL-03")          # the Checker's own T-164 re-measure (verdict e / f)
STAIR_LINE_ITEM = "STR.CONC.STAIR"
NOT_LINES = {   # untied faces that are not a quantity of this package (named in the ledger, never a line)
    "INFO_NOT_A_QUANTITY": "information row of the face ledger (not a face)",
    "SCENARIO_NOT_IN_CANDIDATE": "S1 scenario face: never in the candidate (ScenarioLeak guard)",
}
NOTES_T352 = {   # Checker T-352 verdict (Verifier 2026-10-30 00:09 UTC), carried as a note on the face, never a deduction
    "T352-27": "N-T352-1 (Checker T-352 verdict): RS-A east side faces a V-slot to B21 closing to 0, about 0.08 m2 "
               "impractical to form; a note, never a deduction by convention"}
SUPERSEDED = {"R4-339": "T-352 (MERGED b12e10de) measures the stair side faces face by face (27 faces, "
                        "STAIR_FORMWORK_T352_V1): the R4-339 aggregate is superseded, never carried beside them"}


class PinError(ValueError):
    pass


def _bytes(p):
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    if h != PINS[p]:
        raise PinError(f"{p.name}: sha256 {h[:12]} is not the merged {PINS[p][:12]} (edited ledger)")
    return b


def _csv(p):
    return list(csv.DictReader(_bytes(p).decode("utf-8").splitlines()))


def _f(x):
    return None if x in (None, "") else float(x)


def _src(t):
    s = dict(SOURCES[t], task=t, sha256=PINS[SOURCES[t]["pin"]])
    s.pop("pin")
    return s


def build(project_id):
    fill, face, add, sface, rail, shut = (_csv(p) for p in (FILL, FACE, ADD, SFACE, RAIL, SHUT))
    conc = json.loads(_bytes(CONC).decode("utf-8"))
    conc_by = {c["line_id"]: c for c in conc["lines"]}
    dgb = json.loads(_bytes(DGB).decode("utf-8"))
    dg_lines = sorted({lid for r in dgb["records"] for lid in r["line_ids"]})
    bound = {}
    formwork, alternatives, comparison, not_applicable = [], [], {}, []
    alt = {}
    for r in fill:
        lid = r["line_id"]
        c = conc_by.get(lid)
        if c is None or c["item_code"] != r["item_code"] or c["evidence_state"] != r["line_state"]:
            raise PinError(f"FILL {lid}: not the T-332 concrete line it names ({r['item_code']} {r['line_state']})")
        bound[lid] = {k: c.get(k) for k in ("line_id", "item_code", "element_id", "evidence_state", "measured_net",
                                            "bounded_low", "bounded_high", "floor")}
        rec = {"line_id": lid, "item_code": r["item_code"], "line_state": r["line_state"], "status": r["status"],
               "alternative": r["alternative"] or None, "method": r["method"], "faces": int(r["faces"]),
               "m2": _f(r["m2"]), "lo": _f(r["lo"]), "hi": _f(r["hi"]), "held_from": _f(r["held_from"]),
               "bound_classes": r["bound_classes"], "face_ids": r["face_ids"].split(), "source_task": "T-332"}
        if r["method"] == "E":
            if r["status"] != "CALCULATED" or rec["m2"] is None:
                raise PinError(f"FILL {lid}: an E row is the comparison method (CALCULATED, valued)")
            comparison[lid] = round(comparison.get(lid, 0.0) + rec["m2"], 6)
        elif r["status"] == "ALTERNATIVE":
            alt.setdefault((lid, r["method"]), []).append(rec)
        elif r["status"] == "NOT_APPLICABLE":
            not_applicable.append(rec)
        else:
            formwork.append(rec)
    for (lid, meth), rows in sorted(alt.items()):
        kinds = sorted(x["alternative"] for x in rows)
        if kinds != ["OQ10_EARTH_CAST", "OQ10_FORMED"] and kinds != ["OQ10_FORMED"]:
            raise PinError(f"FILL {lid} {meth}: OQ-10 alternatives {kinds} (FORMED with its EARTH_CAST twin)")
        alternatives.append({"line_id": lid, "method": meth, "item_code": rows[0]["item_code"],
                             "line_state": rows[0]["line_state"], "source_task": "T-332",
                             "alternatives": {x["alternative"]: {"m2": x["m2"], "faces": x["faces"],
                                                                 "face_ids": x["face_ids"]} for x in rows}})
    fb = {r["face_id"]: r for r in face}
    for nf in not_applicable:   # the reason of each NOT_APPLICABLE face, from the face ledger
        nf["basis"] = "; ".join(fb[f]["basis_note"] or fb[f]["tie_reason"] for f in nf["face_ids"])
    untied, named = [], []
    for r in face:
        tie, st = r["tie"], r["status"]
        if tie == "SAME" and st != "REMOVED":
            continue                      # tied: in the FILL table (bound to its line)
        if r["face_id"] in SUPERSEDED:
            named.append({"face_id": r["face_id"], "why": SUPERSEDED[r["face_id"]], "class": "SUPERSEDED"})
        elif tie in NOT_LINES:
            named.append({"face_id": r["face_id"], "why": NOT_LINES[tie], "class": tie})
        elif st in ("REMOVED", "NOT_APPLICABLE", "OWNED_BY_OTHER_LINE"):
            named.append({"face_id": r["face_id"], "why": f"{st}: {r['tie_reason'] or r['basis_note']}"[:300],
                          "class": st})
        elif st == "HELD":
            untied.append({"face_id": r["face_id"], "element": r["element"], "floor": r["floor"] or None,
                           "item": r["item"], "tie": tie, "method": r["method"], "alternative": r["alternative"] or None,
                           "lo": _f(r["lo"]), "hi": _f(r["hi"]), "held_from": _f(r["held_from"]),
                           "reason": r["tie_reason"] or r["basis_note"], "source_task": "T-332"})
        else:
            raise PinError(f"face {r['face_id']}: untied {tie} {st} not handled")
    sf = {r["face_id"]: r for r in sface}
    stair_sides = []
    for r in add:
        lid = r["line_id"]
        c = conc_by.get(lid)
        if c is None or c["item_code"] != STAIR_LINE_ITEM:
            raise PinError(f"T-352 {lid}: not a V3.0.21 stair concrete line")
        bound[lid] = {k: c.get(k) for k in ("line_id", "item_code", "element_id", "evidence_state", "measured_net",
                                            "bounded_low", "bounded_high", "floor")}
        ids = r["face_ids"].split()
        for f in ids:
            if sf[f]["line_id"] != lid:
                raise PinError(f"T-352 {f}: face ledger line {sf[f]['line_id']} != addendum {lid}")
        vals = [_f(sf[f]["m2"]) for f in ids]
        if r["status"] == "CALCULATED" and abs(sum(vals) - float(r["m2"])) > 1e-6:
            raise PinError(f"T-352 {lid}: {r['m2']} is not the sum of its faces {sum(vals)}")
        stair_sides.append({"line_id": lid, "item_code": STAIR_LINE_ITEM, "line_state": c["evidence_state"],
                            "status": r["status"], "faces": int(r["faces"]), "m2": _f(r["m2"]), "lo": _f(r["lo"]),
                            "hi": _f(r["hi"]), "face_ids": ids, "source_task": "T-352",
                            "face_evidence": {f: sf[f]["evidence"] for f in ids},
                            "notes": [f"{f}: {NOTES_T352[f]}" for f in ids if f in NOTES_T352]})
    runs = {}
    for r in rail:
        runs.setdefault(r["RUN"], []).append(r)
    railings = []
    for run, segs in runs.items():
        sts = {s["RUN_STATUS"] for s in segs}
        lengths = [_f(s["LENGTH_LM"]) for s in segs]
        st = "EXCLUDED" if sts == {"EXCLUDED"} else ("UNKNOWN" if "UNKNOWN" in sts else
                                                     ("HELD" if "HELD" in sts else "DRAWING-CONFIRMED"))
        if st == "DRAWING-CONFIRMED" and any(x is None for x in lengths):
            raise PinError(f"{run}: a confirmed run with an unmeasured segment")
        measured = [x for x in lengths if x is not None]
        railings.append({"run": run, "kind": segs[0]["KIND"], "status": st,
                         "verified": run in VERIFIED_RUNS and st == "DRAWING-CONFIRMED",
                         "lm": round(sum(measured), 6) if st == "DRAWING-CONFIRMED" else None,
                         "measured_part_lm": round(sum(measured), 6) if measured and st != "DRAWING-CONFIRMED"
                         else None, "unmeasured_segments": sum(1 for x in lengths if x is None),
                         "height_printed_m": _f(segs[0]["HEIGHT_PRINTED_M"]),
                         "segments": [{"segment": s["SEGMENT"], "lm": _f(s["LENGTH_LM"]), "status": s["RUN_STATUS"]}
                                      for s in segs],
                         "source": segs[0]["SOURCE"], "note": segs[0]["NOTE"], "source_task": "T-164"})
    shutters = []
    for r in shut:
        n = int(r["LEAVES_PCS"])
        if n == 0:
            continue
        shutters.append({"opening": r["OPENING"], "pcs": n, "leaf_size_m": r["LEAF_SIZE_M"] or None,
                         "status": "DRAWING-CONFIRMED (count)", "m2": None, "m2_state": "HELD",
                         "source": r["SOURCE"], "source_task": "T-164"})
    return {"schema": "URBAN_V3030_INPUTS_V1", "project_id": project_id,
            "sources": [_src(t) for t in ("T-332", "T-352", "T-164")],
            "downgrade_bound_lines": dg_lines,
            "downgrade_records": [{k: r[k] for k in ("downgrade_id", "unit", "candidate_version")} for r in
                                  dgb["records"]], "downgrade_source_sha256": dgb["source_sha256"],
            "bound_concrete_lines": sorted(bound.values(), key=lambda x: x["line_id"]),
            "formwork": formwork, "alternatives": alternatives, "comparison_e_m2": dict(sorted(comparison.items())),
            "not_applicable": not_applicable, "untied": untied, "named_not_lines": named,
            "stair_sides": stair_sides, "railings": railings, "shutters": shutters}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    pid = argv[0] if argv else "development-villa-t131"
    d = build(pid)
    calc = sum(r["m2"] for r in d["formwork"] if r["status"] == "CALCULATED")
    print(json.dumps({"formwork_rows": len(d["formwork"]), "calculated_m2": round(calc, 6),
                      "alternatives": len(d["alternatives"]), "untied": len(d["untied"]),
                      "not_applicable": len(d["not_applicable"]), "named": len(d["named_not_lines"]),
                      "stair_sides": len(d["stair_sides"]),
                      "stair_sides_m2": round(sum(r["m2"] or 0 for r in d["stair_sides"]), 6),
                      "railings": [(r["run"], r["status"], r["lm"], r["measured_part_lm"]) for r in d["railings"]],
                      "shutters": [(s["opening"], s["pcs"]) for s in d["shutters"]]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
