"""T-254: the URBAN_V3017_INPUTS_V1 of the development villa, built from checker-merged files only, line id by line id:

  research/agents_t289/BASIS_LEDGER_T289.csv          T-289 MERGED 455c93c4 (Verifier 2026-10-25 09:33): per line the
                                                       printed support, the drawing value / range and the status
  research/agents_t289/CANDIDATE_V3015_BASIS_LINES.json  the same lines as the candidate carries them (evidence state,
                                                       unrounded quantity): the 'before' asserted on every record
  research/agents_t253/LEDGER_T253.csv                T-253 MERGED dff9cb79 (Verifier 2026-10-24 07:20): the boundary
                                                       ground beam the candidate omits (added HELD on M4)
  T-287 MERGED 542b64c7 (Verifier 2026-10-25 07:58 / 07:59 own 1.430 m3): the CB5 columns C5 / C3 base +0.25, h 5.20

Nothing is re-derived here: every figure is read from those files (the CB5 values are the T-289 ledger's own drawing
high ends 0.650 / 0.780, which T-287 settled). ST-03 is named and left to T-266 (Lead 2026-10-25 08:15).

    python3 -I research/agents_t254/t254_inputs.py > <scratch>/v3017_inputs.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "research/agents_t289/BASIS_LEDGER_T289.csv"
CAND = ROOT / "research/agents_t289/CANDIDATE_V3015_BASIS_LINES.json"
T253 = ROOT / "research/agents_t253/LEDGER_T253.csv"
T287 = ROOT / "research/agents_t287/T-287_DESIGNER_GAP_SEARCH.md"
T248 = ROOT / "research/agents_t248/LEDGER_T248.csv"
T256 = ROOT / "research/agents_t256/ALSENAN_T256_EVIDENCE.json"
# the one modal frame translation between the T-248 register and the candidate's element ids (T-289 s.2: dx 75 968,
# dy 14 448 mm, 29 votes, every binding within 2 mm); a NOT_DRAWN stack binds to the candidate column line of the same
# mark and storey at the translated position, within 2 mm, or the build stops
FRAME = (75968.0, 14448.0)
BIND_TOL_MM = 2.0
# the five stacks as V3.0.16 carries them (asserted by the module against each line: a stale state refuses the run)
NOT_DRAWN_BEFORE = {"evidence_state": "BLOCKED_RFI", "measured_net": None}
# the candidate column lines the binding gives on the V3.0.16 run (v3017_direct.py re-binds them against every candidate
# column line and stops if the set differs)
NOT_DRAWN_IDS = {"L-7d98b1c0ac80787d0b51": "P-C:COL:SH12:C5@243102,55481|2F",
                 "L-eb3bd5ba496a207f04f7": "P-C:COL:SH12:C3@243004,52949|2F",
                 "L-73e82692ffb24059d95b": "P-C:COL:SH12:C8@256160,53630|2F",
                 "L-99e7e45631f6ddf3c7e2": "P-C:COL:SH12:C3@254464,51322|1F",
                 "L-2bf336912a62859834b3": "P-C:COL:SH12:C3@254464,51322|2F"}

GB, COL = "STR.CONC.GROUND_BEAM", "STR.CONC.COLUMN"
CB5 = {"L-7d70692d03102a2dc306": "C3 (365)", "L-84bf7fb482a98fdbe482": "C5 (35F)"}
# T-254 (i): run 107+7CE#1 (line BAND0009). The merged T-242 / T-253 plan 0.1118 m2 carries a 'beam strip beside neck
# COL:17BD' of 0.0026 m2. By entity handle: the neck outline 17BD spans BOTH face lines (107 and 7CE) across the full
# 0.300 m width and 0.300 m along the run; the run's face lines end inside it (7CE 0.0261 m, 107 0.2911 m past the neck
# face) and neither reaches past its far face, so no part of the strip lies outside the neck: it is neck concrete
# (counted once, in the neck), never beam. Dropped: 0.3639 x 0.30 = 0.10917 m2 x D 0.95 = 0.1037115 m3, as the
# Checker's own T-180 slot found (Verifier 2026-10-24 12:10: 'the neck covers the full 0.30 width').
STUB = {"L-ff727b2a52e39509a659": {
    "ledger": 0.1062, "value": 0.103712,
    "own_check": "Verifier 2026-10-24 12:10 (T-180 slot): the neck covers the full 0.30 width; T-254 (i) by handle: "
                 "neck 17BD spans face lines 107 / 7CE over 0.300 x 0.300, the strip lies inside it",
    "formula": "run 107+7CE#1 face to face 0.3639 m x 0.30 x D 0.95 (top +0.95, N.G. +-0.00) = 0.103712 m3; the "
               "0.0026 m2 strip beside neck 17BD lies inside the neck (dropped, T-254 (i))"}}
ANNEX_READINGS = ("literal 'FOLLOW ARCH.' from the annex +0.25 to N.G. +-0.00 = 0.25 m (shown, never adopted)",
                  "the printed exterior section 'Ground Beams for exterior walls' (three bar zones) cannot be built in "
                  "0.25 m: depth not printed (designer D-35 annex)")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _f(x):
    return float(x) if x not in ("", None) else None


def sources():
    return [{"file": "research/agents_t289/BASIS_LEDGER_T289.csv", "sha256": sha(LEDGER), "task": "T-289",
             "merge_commit": "455c93c4a13a46c198a3144889ee2d221bd551c0",
             "checker_run": "Verifier 2026-10-25 09:33 UTC (Gate A PASS; 3 interior-typed exterior lines confirmed by "
                            "own re-derive)"},
            {"file": "research/agents_t287/T-287_DESIGNER_GAP_SEARCH.md", "sha256": sha(T287), "task": "T-287",
             "merge_commit": "542b64c7cd6f924fa0435677af59e484bd8aa598",
             "checker_run": "Verifier 2026-10-25 07:58 UTC (Gate A PASS; 07:59 restatement: own 1.430 m3 "
                            "DRAWING-DERIVED for C5 / C3)"},
            {"file": "research/agents_t256/ALSENAN_T256_EVIDENCE.json", "sha256": sha(T256), "task": "T-256",
             "merge_commit": "74c966b1955a55ae2ad81322fdb60ab85c9a35bc",
             "checker_run": "Verifier 2026-10-24 07:52 UTC (Gate A PASS; 5 upper column lines NOT_PRESENT, "
                            "DRAWING-CONFIRMED absence)"},
            {"file": "research/agents_t253/LEDGER_T253.csv", "sha256": sha(T253), "task": "T-253",
             "merge_commit": "dff9cb798da523510b5aece3b40c95887bdd01d7",
             "checker_run": "Verifier 2026-10-24 07:20 UTC (Gate A PASS; own 8.8140 m2 x 0.40)"}]


def _before(cand):
    out = {}
    for g in cand["groups"].values():
        for ln in g:
            out[ln["line_id"]] = {"evidence_state": ln["evidence_state"], "measured_net": ln["measured_net"]}
    return out


def _literal(reason):
    # 'EXTERIOR_ANNEX run(s): T-253 s.3 CONFLICT: literal reading 0.1725 m3 at 0.25, never adopted'
    tok = reason.split("literal reading ")
    if len(tok) < 2:
        return None
    v = float(tok[1].split(" m3")[0])
    return v if v > 0 else None


def record(row, before):
    lid = row["line_id"]
    base = {"line_id": lid, "item_code": row["item_code"], "element_id": row["element_id"],
            "group": row["group"], "task": "T-289", "physical_element": row["physical_element"],
            "before": before[lid], "engine_basis": row["engine_basis"]}
    st = row["status"]
    if lid in CB5:
        v = _f(row["drawing_high_m3"])
        return dict(base, task="T-287", action="REBASE", value=v,
                    support={"kind": "PRINTED_LEVELS_AND_FLOOR_CONTINUITY",
                             "printed": f"GF column {CB5[lid]}: base = ground-beam top +0.25 (T-214; the floors printed "
                                        "beside it are the annex +0.30 and the court +0.15, no +1.00 reaches it), top "
                                        "the 1F structure, h 5.20 (T-287 G1, rule R-COL-BASE-ADJ-1 proposed)",
                             "sheets": "ST p.1 - p.6 (no neck end printed at the column), ST p.3, arch GF"},
                    status="DRAWING-CONFIRMED",
                    own_check="Verifier 2026-10-25 07:59 own C5 + C3 = 1.430 m3 DRAWING-DERIVED (not VERIFIED)",
                    formula=f"section x 5.20 m (base +0.25 to the 1F structure) = {v:.4f} m3 (T-287 G1)")
    if lid in STUB:
        x = STUB[lid]
        assert abs(_f(row["drawing_qty_m3"]) - x["ledger"]) < 1e-9, "the ledger moved: re-read the stub"
        return dict(base, action="REBASE", value=x["value"],
                    support={"kind": "TWO_PRINTED_LEVELS", "printed": row["printed_support"][:600],
                             "sheets": row["sheets_searched"]},
                    status="DRAWING-CONFIRMED", own_check=x["own_check"], formula=x["formula"])
    if st == "DRAWING-CONFIRMED":
        v = _f(row["drawing_qty_m3"])
        return dict(base, action="REBASE", value=v,
                    support={"kind": "TWO_PRINTED_LEVELS", "printed": row["printed_support"][:600],
                             "sheets": row["sheets_searched"]},
                    status="DRAWING-CONFIRMED",
                    formula=f"{row['reason']} [{row['evidence']}]"[:400])
    if st == "CONFLICT":
        lit = _literal(row["reason"])
        return dict(base, action="CONFLICT", held_item=row["held_item"], reasons=[row["reason"], row["evidence"]],
                    readings_named=list(ANNEX_READINGS),
                    scenario=({"readings": {"literal_0_25_m": lit}, "basis": "literal 0.25 m reading, never adopted"}
                              if lit else None))
    if st in ("HELD", "PENDING-VERIFICATION"):
        rd = {}
        if _f(row["drawing_low_m3"]):
            rd["low"] = _f(row["drawing_low_m3"])
        if _f(row["drawing_high_m3"]):
            rd["high"] = _f(row["drawing_high_m3"])
        return dict(base, action="HOLD", held_item=row["held_item"], reasons=[row["reason"], row["evidence"]],
                    scenario=({"readings": rd, "basis": "ledger range / upper bound (T-289); never a BOQ quantity"}
                              if rd else None))
    raise SystemExit(f"{lid}: status {st} not handled")


def boundary_add(rows):
    band = sum(float(r["value_m3"]) for r in rows if r["component"] == "BOUNDARY-GB at N.G.")
    return {"id": "T253-BOUNDARY-GB", "item_code": GB, "unit": "m3", "floor": "GROUND",
            "element": "GROUND_BEAMS:GROUND:BOUNDARY_GB_NG", "physical_element": "GROUND_BEAM (boundary wall, 20 x 40, "
            "at natural ground)", "task": "T-253",
            "item_en": "Ground beam: boundary wall beam 20 x 40 at natural ground",
            "item_ar": "ميدة سور حدودي ٢٠×٤٠ عند منسوب الأرض الطبيعية", "trade": "CONCRETE",
            "like_line_id": "L-1146bdecd41491ce9382", "state": "HELD",
            "held_item": "M4: boundary-wall columns 20 x 30 ('SEE ARCH PLAN', none drawn): count and positions",
            "reasons": ["the band 5 runs 44.07 m x 0.20 x 0.40 is DRAWING-CONFIRMED (T-253, Checker own 8.8140 m2 "
                        "x 0.40); the beam line is the band less 0.024 m3 per boundary column, and the columns are "
                        "not drawn: HELD (never the band, never 0)"],
            "printed": "ST p.14 TYPICAL BOUNDARY WALL plan + section A-A 'GROUND BEAM (20x40)'; ST p.3",
            "scenario": {"readings": {"band_upper_bound": round(band, 6)},
                         "basis": "band 3.5256 m3 = beam line + 0.024 m3 x (column count, not printed)"},
            "downstream": ["boundary G.B bars (2 d14 + 3 d16, d8/20 p.14), formwork and excavation: other tasks"]}


def _xy(eid):
    # 'P-C:COL:SH12:C5@167134,41033|2F' -> ('C5', 167134.0, 41033.0, '2F')
    head, storey = eid.split("|")
    mark, pos = head.split(":")[-1].split("@")
    x, y = pos.split(",")
    return mark, float(x), float(y), storey


def not_present(candidate_ids):
    """the T-256 NOT_PRESENT stacks bound to candidate column element ids (T-248 route G line + the T-289 frame)."""
    ev = {x["line"]: x for x in json.loads(T256.read_text(encoding="utf-8"))["not_drawn_lines"]}
    rows = [r for r in csv.DictReader(T248.open(encoding="utf-8")) if r["member"].startswith("NOT_DRAWN:")]
    out = []
    for r in rows:
        mark, x, y, storey = _xy(r["route_g_line"])
        hits = []
        for lid, eid in candidate_ids.items():
            m2, x2, y2, s2 = _xy(eid)
            if m2 == mark and s2 == storey and abs(x2 - x - FRAME[0]) <= BIND_TOL_MM and abs(y2 - y - FRAME[1]) <= BIND_TOL_MM:
                hits.append((lid, eid))
        if len(hits) != 1:
            raise SystemExit(f"{r['member']}: {len(hits)} candidate lines bind (one required)")
        e = ev[r["member"]]
        out.append({"line_id": hits[0][0], "item_code": COL, "element_id": hits[0][1], "group": "COL_NOT_PRESENT",
                    "task": "T-256", "physical_element": f"COLUMN {mark} {storey} on neck {r['fp_neck']} (type-table band only)", "before": dict(NOT_DRAWN_BEFORE), "action": "NOT_PRESENT",
                    "engine_basis": f"route G / released A {r['route_g_m3']} m3 on a type-table band (D-65)",
                    "absence_evidence": "; ".join(f"{k}: {v}" for k, v in sorted(e["searched"].items()))
                    + f"; texts within 0.6 m: 0; start / stop symbol on the plan below: none (T-256 s.4)",
                    "sheets_searched": ", ".join(sorted(e["searched"]))})
    return out


def build(candidate_ids=None):
    cand = json.loads(CAND.read_text(encoding="utf-8"))
    before = _before(cand)
    rows = list(csv.DictReader(LEDGER.open(encoding="utf-8")))
    recs, left = [], []
    for row in rows:
        if row["group"] == "ST03":
            left.append({"line_id": row["line_id"], "why": "ST-03 is corrected by T-266 (Lead 2026-10-25 08:15: the "
                                                           "T-289 row is its input); byte-identical here"})
            continue
        recs.append(record(row, before))
    recs += not_present(candidate_ids or NOT_DRAWN_IDS)
    groups = {}
    for r in recs:
        d = groups.setdefault(r["group"], {"lines": 0, "before": 0.0, "released_after": 0.0, "held_lines": 0})
        d["lines"] += 1
        d["before"] += r["before"]["measured_net"] or 0.0
        if r["action"] == "REBASE":
            d["released_after"] += r["value"]
        elif r["action"] in ("HOLD", "CONFLICT"):
            d["held_lines"] += 1
    groups = {g: {k: (round(v, 6) if isinstance(v, float) else v) for k, v in d.items()} for g, d in groups.items()}
    t253 = list(csv.DictReader(T253.open(encoding="utf-8")))
    return {"schema": "URBAN_V3017_INPUTS_V1", "project": None, "sources": sources(), "records": recs,
            "adds": [boundary_add(t253)], "groups": groups, "not_in_this_package": left,
            "binding": {"cls": "EXTERIOR", "source": "research/agents_t289/BAND_PAIRING_T289.json (T-289: every drawn "
                                                     "T-242 / T-253 run bound to its band line by face-line geometry)",
                        "holding_line_ids": sorted(r["line_id"] for r in recs
                                                   if r["group"] == "GB_MAIN_EXTERIOR_IN_INTERIOR_LINES")}}


if __name__ == "__main__":
    json.dump(build(), sys.stdout, ensure_ascii=False, indent=1, sort_keys=True)
    sys.stdout.write("\n")
