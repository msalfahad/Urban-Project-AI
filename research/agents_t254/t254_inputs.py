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

GB, COL = "STR.CONC.GROUND_BEAM", "STR.CONC.COLUMN"
CB5 = {"L-7d70692d03102a2dc306": "C3 (365)", "L-84bf7fb482a98fdbe482": "C5 (35F)"}
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


def build():
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
    groups = {}
    for r in recs:
        d = groups.setdefault(r["group"], {"lines": 0, "before": 0.0, "released_after": 0.0, "held_lines": 0})
        d["lines"] += 1
        d["before"] += r["before"]["measured_net"] or 0.0
        if r["action"] == "REBASE":
            d["released_after"] += r["value"]
        else:
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
