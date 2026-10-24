"""T-252 Alsenan check: CONC.BEAM ledger r2 (development villa; no accuracy claim, nothing wired or released).

Inputs (committed only):
  research/agents_t241/LEDGER_T241.csv      merged r1 ledger (140 runs, 66.0161 m3), read-only
  research/agents_t252/ALSENAN_R2_INPUT.json t252_extract.py on Drive 'ST7757 dxf.dxf' sha 9f9d1179 (lengths, widths,
                                            areas and handles only)
  research/agents_t234/LEDGER_T234.csv      merged slab ledger (which T-139 faces the slab line bills)
  research/agents_t241/t241_alsenan_check.py freelancer cells + by-mark comparison (imported, unchanged)
Writes (with --write): LEDGER_T252.csv (r1 rows carried, superseded rows marked, r2 rows added), BY_MARK_T252.csv,
summary.json.

    python3 -I research/agents_t252/t252_alsenan_check.py [--write]
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(ROOT / "research" / "agents_t241"))
import beam_ledger_r2 as R2  # noqa: E402
import t241_alsenan_check as T241  # noqa: E402  (freelancer cells, by-mark comparison; read-only)

STOREYS = ("GF", "1F", "2F")
NUM = ("length_m", "b_drawn_m", "depth_m", "m3", "m3_low", "m3_high", "released_m3")
RING_R1 = ("BM-GF-050#BAND0050", "BM-GF-051#BAND0051", "BM-GF-052#BAND0052", "BM-GF-060#BAND0053")
RING_DEPTH = 0.75     # B7 20 x 75: schedule ST p.10, the four printed B7 marks 46E / 46F / 470 / 471 around the ring
RING_B = 0.20


def _num(v):
    if v in (None, ""):
        return None
    return float(v)


def r1_rows():
    rows = []
    for r in csv.DictReader(open(ROOT / "research/agents_t241/LEDGER_T241.csv", encoding="utf-8")):
        r = dict(r)
        for k in NUM:
            r[k] = _num(r[k])
        rows.append(r)
    return rows


def slab_panels():
    return {r["panel"] for r in csv.DictReader(open(ROOT / "research/agents_t234/LEDGER_T234.csv", encoding="utf-8"))}


def corrections(rows, inp):
    by = {r["run"]: r for r in rows}
    checks, corr = [], []
    # (a) R-BEAM-END-OBLIQUE-2: members ending on the east face of the oblique B27 (S-BEAM 325)
    for rid, o in sorted(inp["oblique_runs"].items()):
        r = by[rid]
        run = dict(La_m=o["La_m"], Lb_m=o["Lb_m"], mean_length_m=(o["La_m"] + o["Lb_m"]) / 2.0)
        c = R2.check_billed_end(r["length_m"], run)
        if abs(o["b_drawn_m"] - r["b_drawn_m"]) > 0.005 or abs(o["depth_m"] - r["depth_m"]) > 1e-9:
            raise R2.Refused("SECTION_CHANGED: %s" % rid)
        checks.append(dict(run=rid, mark=o["mark"], billed_length_m=r["length_m"], La_m=o["La_m"], Lb_m=o["Lb_m"],
                           result=c["result"], delta_length_m=round(c["delta_length_m"], 5),
                           delta_m3=round(c["delta_length_m"] * r["b_drawn_m"] * r["depth_m"], 6),
                           edges=o["edges"], carrier=o["carrier_face"], start=o["start_face"]))
        if c["result"] == "ONE_FACE_END":
            corr.append(dict(kind="replace_length", run=rid, length_m=run["mean_length_m"], b=r["b_drawn_m"],
                             depth=r["depth_m"],
                             basis="R-BEAM-END-OBLIQUE-2: ends on the B27 east face (S-BEAM 325) on both edges %s / "
                                   "%s (%.4f / %.4f m), mean %.4f; r1 billed the short edge only (T-229 end check "
                                   "passed it; Checker 02:02)" % (o["edges"][0], o["edges"][1], o["La_m"], o["Lb_m"],
                                                                 run["mean_length_m"])))
    # (b) R-BEAM-CURVED-AREA-2: GF void ring B7 from its own drawn arcs
    ring = inp["void_ring"]
    replaced = sum(ring["route_g_bands_in_ring"][b]["in_ring_m2"] for b in ring["replaced_bands"])
    others = sum(v["in_ring_m2"] for k, v in ring["route_g_bands_in_ring"].items() if k not in ring["replaced_bands"])
    slab = sum(a for f, a in ring["t139_faces_in_ring_m2"].items() if f in slab_panels())
    once = R2.ring_counted_once(ring["area_m2"], replaced, slab, others)
    for rid in RING_R1:
        if rid not in by:
            raise R2.Refused("RING_PIECE_MISSING: %s" % rid)
    r1_ring_m3 = sum(by[x]["m3"] for x in RING_R1 if by[x]["status"] in R2.MEASURED)
    m3 = round(ring["area_m2"] * RING_DEPTH, 6)
    new = dict(run="BM-GF-050.r2#RING-B7", storey="GF", mark="B7", member="BM-GF-050.r2",
               pieces="ring between arcs %s; void %s" % ("/".join(ring["outer_handles"]),
                                                         "/".join(ring["void_handles"])),
               status="CALCULATED", length_m=None, b_drawn_m=RING_B, depth_m=RING_DEPTH, m3=m3, m3_low=m3, m3_high=m3,
               released_m3=sum(by[x]["released_m3"] or 0.0 for x in RING_R1), released_bounded="",
               adds="", deducts="", designer="", source="T-252 R-BEAM-CURVED-AREA-2 (Checker 02:08)",
               reason="GF void ring B7: plan %.6f m2 between its own drawn edges (exact arcs; widths %s m = schedule "
                      "0.20), x D 0.75 (B7 20 x 75, marks %s); replaces route G bands 50 / 51 / 52 (CALCULATED) "
                      "and 53 (HELD 'contested', inside the same ring between the same B7 edges)"
                      % (ring["area_m2"], ring["widths_m"], "/".join(ring["marks"])))
    corr.append(dict(kind="supersede", runs=list(RING_R1), new=new,
                     basis="R-BEAM-CURVED-AREA-2: one ring row from the drawn edges; band set under-covered it by "
                           "%.5f m2 (Checker 02:08)" % once["missed_m2"]))
    ring_rec = dict(area_m2=ring["area_m2"], polygon_check_m2=ring["polygon_check_m2"], parts_m2=ring["parts_m2"],
                    replaced_band_m2=round(replaced, 5), missed_m2=round(once["missed_m2"], 5),
                    sliver_residual_m2=round(others, 5), slab_ledger_in_ring_m2=round(slab, 5),
                    t139_faces=ring["t139_faces_in_ring_m2"], m3=m3, r1_measured_m3=round(r1_ring_m3, 6),
                    r1_held=[by["BM-GF-060#BAND0053"]["m3_low"], by["BM-GF-060#BAND0053"]["m3_high"]],
                    delta_measured_m3=round(m3 - r1_ring_m3, 6))
    return corr, checks, ring_rec


def build():
    rows = r1_rows()
    inp = json.load(open(HERE / "ALSENAN_R2_INPUT.json", encoding="utf-8"))
    if inp["source_dxf_sha256"] != "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079":
        raise R2.Refused("INPUT_FROM_ANOTHER_DRAWING")
    corr, checks, ring = corrections(rows, inp)
    r2 = R2.revise(rows, corr)
    t1, t2 = R2.totals(rows), R2.totals(r2)
    m1 = round(sum(t["measured_m3"] for t in t1.values()), 6)
    m2 = round(sum(t["measured_m3"] for t in t2.values()), 6)
    causes = [("R-BEAM-END-OBLIQUE-2: %s %s end on the B27 east face, both edges" % (c["mark"], c["run"]),
               c["delta_m3"]) for c in checks if c["result"] == "ONE_FACE_END"]
    causes.append(("R-BEAM-CURVED-AREA-2: GF void ring B7 from its drawn edges replaces bands 50 / 51 / 52",
                   ring["delta_measured_m3"]))
    explained = round(sum(v for _k, v in causes), 6)
    fr = T241.freelancer()
    live = [r for r in r2 if r["status"] != "SUPERSEDED_R2"]
    marks = T241.by_mark(live, fr)
    marks_r1 = {(m["storey"], m["mark"]): m for m in T241.by_mark(rows, fr)}
    moved = [dict(m, r1_low=marks_r1[(m["storey"], m["mark"])]["mine_low"]) for m in marks
             if (m["storey"], m["mark"]) in marks_r1
             and abs(m["mine_low"] - marks_r1[(m["storey"], m["mark"])]["mine_low"]) > 1e-6]
    fr_st = {"GF": fr["GF"], "1F": fr["F1_total_cell"], "2F": fr["F2"]}
    summary = dict(
        schema="T252_BEAM_LEDGER_R2", module=R2.SCHEMA, rules=list(R2.RULES), revises="T241_BEAM_LINE_V1 (merged)",
        convention="C1_PANEL_BETWEEN_BEAM_FACES",
        source_dxf_sha256=inp["source_dxf_sha256"], runs_r1=len(rows), runs_live=len(live),
        superseded=[r["run"] for r in r2 if r["status"] == "SUPERSEDED_R2"],
        added=[r["run"] for r in r2 if r.get("supersedes")],
        by_storey=t2, measured_m3_r1=m1, measured_m3=m2, delta_m3=round(m2 - m1, 6),
        delta_explained=causes, residual_m3=round(m2 - m1 - explained, 6),
        conflict=(round(sum(t["conflict_low"] for t in t2.values()), 6),
                  round(sum(t["conflict_high"] for t in t2.values()), 6)),
        held=(round(sum(t["held_low"] for t in t2.values()), 6), round(sum(t["held_high"] for t in t2.values()), 6)),
        held_r1=(round(sum(t["held_low"] for t in t1.values()), 6), round(sum(t["held_high"] for t in t1.values()), 6)),
        held_no_value=[x for t in t2.values() for x in t["held_no_value"]],
        oblique_end_checks=checks, void_ring=ring,
        released=dict(measured=round(sum(v["measured"] for v in T241.RELEASED.values()), 4),
                      per_floor={k: v["measured"] for k, v in T241.RELEASED.items()}),
        freelancer=dict(per_floor=fr_st, total=fr["total"]), marks_moved=moved,
    )
    return summary, r2, marks


def main(argv):
    summary, rows, marks = build()
    print(json.dumps({k: summary[k] for k in ("runs_r1", "runs_live", "measured_m3_r1", "measured_m3", "delta_m3",
                                              "residual_m3", "conflict", "held_r1", "held", "held_no_value")}))
    for c in summary["oblique_end_checks"]:
        print("end", json.dumps(c))
    print("ring", json.dumps(summary["void_ring"]))
    for st in STOREYS:
        print(st, json.dumps(summary["by_storey"][st]), "| freelancer", summary["freelancer"]["per_floor"][st],
              "| released", summary["released"]["per_floor"][st])
    for m in summary["marks_moved"]:
        print("mark", json.dumps(m))
    if "--write" in argv:
        cols = ["run", "storey", "mark", "member", "pieces", "status", "length_m", "b_drawn_m", "depth_m", "m3",
                "m3_low", "m3_high", "released_m3", "released_bounded", "adds", "deducts", "designer", "source",
                "reason", "supersedes", "superseded_by", "basis"]
        with open(HERE / "LEDGER_T252.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        with open(HERE / "BY_MARK_T252.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(marks[0]))
            w.writeheader()
            w.writerows(marks)
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
