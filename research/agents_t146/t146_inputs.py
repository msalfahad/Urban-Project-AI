"""T-146 + T-247 (V3.0.12): the project inputs of ARCH_TAKEOFF_V3.0.12 (URBAN_V3012_INPUTS_V1) for the development villa.
Research code; it reads the checker-merged ledgers as committed and changes none of their quantities. No coordinates,
no names, no drawing content.

BEAM_LEDGER (T-247): the CONC.BEAM ledger r2 (T-252, MERGED b37be82d, Verifier 2026-10-24 05:37 UTC: Gate A PASS,
'every CALCULATED run is now own-measured incl. both corrections'; built on T-241 MERGED f0250164, Verifier 00:06, and
the Checker's T-180 beam batches 01:24 (2F), 02:02 / 02:08 (GF), 03:12 (upstands)). 137 live runs: measured 66.320598,
CONFLICT 5.144829 .. 6.111010, HELD 4.1277 .. 8.5682 + 4 runs with no value. Each candidate STR.CONC.BEAM line (one
route band) is mapped to the run(s) whose pieces are that band (band ids of the ledger's band set = the run's, with the
T-110 span suffix '.1' where the run's band set has one span; two spans of one band = two runs of one line) or, for the
two candidate bands the ledger names by face, by the identity table below. A line that already carries its run (one
line, one run, same figure) is kept byte-identical; every other line of a run is superseded by that run's line.
RING OVERLAP (Verifier 05:37 named residual; Lead 2026-10-24 06:15 'removed once'): route bands GF BAND0003 (B8),
BAND0006 (B7) and BAND0041.2 (CB1) overlap the drawn B7 void ring by 0.00178 / 0.00047 / 0.00117 m2 (T-252 summary
'sliver_residual_m2' 0.00342; per band from the T-252 ring reconciliation); the ring is measured between its own drawn
edges (R-BEAM-CURVED-AREA-2), so the overlap is removed once from the three band runs at their depth 0.75 m.

SLAB_FACE_HOME (T-146): the 13 candidate slab faces that the checker-merged slab ledger (T-234, MERGED 3224f68a,
Verifier 2026-10-23 23:01 UTC: 62 panels 60.2804 m3 = own re-measure 0.000 %; 'released / candidate ENGINE_WRONG
+1.2710 / +0.6388 -> T-146') classes as not slab, each with its home: a run of the beam ledger above, or no concrete
(a drafting break mark, T-145 / T-234). Slab left per floor = T-234's hand figure (GF 33.069520, 1F 19.756576,
2F 7.454300) within 0.0005 m3; the 1F residual -0.000243 is T-234's own (panel areas rounded to 4 dp in its ledger).
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
T252 = ROOT / "research/agents_t252"
T234 = ROOT / "research/agents_t234"
SNAP = HERE / "CANDIDATE_V3011_BEAM_SLAB.json"
T252_LEDGER_SHA = "dd12f12a6357dae58c349991642de6436d45617aabc9d1fbf8e3655c489d0805"
T252_SUMMARY_SHA = "57153e8429f6eb990629b50c50c0efe9d4b074ec92634603b639cba19e516463"
T234_SUMMARY_SHA = "a38e88ad89f6853eb9bb635d8ccf27f965fe3f07366895ed782915676c540b19"
SNAP_SHA = "b7975d39b2311fee44c589e9345afd67a7119040b13f87f33786adc31f41c76a"
BEAM, SLAB = "STR.CONC.BEAM", "STR.CONC.SLAB"
FLOORS = ["GF", "1F", "2F"]
DEPTH_RING_BANDS = 0.75
# T-252 ring reconciliation (T-252 report s.2 'Other beams' bands in the ring: B8 0.00178, CB1 0.00117, the straight
# B7 BAND0006 0.00047 = 0.00342 m2'); the Checker 05:37 names the same three bands (3, 6, 41.2)
RING_OVERLAP_M2 = {"BM-GF-003#BAND0003": 0.00178, "BM-GF-006#BAND0006": 0.00047, "BM-GF-042#BAND0041.2": 0.00117}
RING_RUN = "BM-GF-050.r2#RING-B7"
# candidate bands the ledger names by its partition face, settled by identity (worker 3, T-146 run): the band's
# printed dimensions on the candidate line and its position (the route's exception register, shifted by the fixed
# sheet-frame offset common to every GF / 1F band) equal the face of the T-139 partition named by the run.
IDENTITY = {
    ("GF", "GF:BAND0030.2"): ("BM-GF-062#GF-112", "route band 0.20 x 0.50 (0.10 m2, UNLABELLED_SPAN_ACROSS_SUPPORT, "
                              "collinear B4) at the centre of T-139 face GF-112 (0.20 x 0.50 north of the CB6 support "
                              "column in line with B4): the same piece; T-241 recorded 'no route G band' for it from "
                              "its older band set, the candidate carries it once, at the run's own range 0.04 .. 0.12"),
    ("1F", "1F:BAND0029"): ("BM-1F-037", "route band 0.40 x 0.60 (0.24 m2, UNBOUND, no mark) at the centre of T-139 "
                            "face 1F-069 (the rounded box outside CB12 at mid length, 0.405 x 1.005): the same box; "
                            "depth not printed (D-26), the run carries no value (Q-16: never a copied depth)"),
}
# the 1F dome rings: the candidate carries them as the V3.0.5 ring lines (T-160 / T-179; the route's four west arc
# bands already retired by V3.0.5): west = run BM-1F-028 (B4, VERIFIED 0.7552 = 1.5105 m2 x 0.50, Verifier 2026-10-22
# 06:25; the ledger's 0.7553 is the same 0.75525 rounded the other way), east = run BM-1F-039 (no mark, depth 'as per
# arch': the candidate holds it with no value, Q-61 C(3); the ledger's 0.8997 is the B4-size candidate, information)
RING_LINES = {"HL:DOME_RING:DOME-1F-W:RING:RING_BEAM_B4_IN_BAY": "BM-1F-028#BAND0033",
              "HL:DOME_RING:DOME-1F-E:RING:RING_BEAM_IN_BAY": "BM-1F-039"}
NOT_CONCRETE = "a stepped drafting line (0.025 m steps joined by 0.025 m arcs) beside the stair, no tag, no bars, no " \
               "mark (T-145 s.4; T-234 'break mark'; T-139 class NOT_SLAB)"
# T-234 RELEASED['not_slab_faces'] (engine face suffix -> T-139 face) and the home of each (T-241 named faces, T-252)
FACE_HOME = {
    "f9b0c2": ("GF", "GF-063", {"kind": "BEAM_RUN", "run": "BM-GF-058#BAND0031.1"},
               "0.20 strip north of B20 round the street corner (D-05, Q-61 C(5)): beam lane, HELD"),
    "b355ef": ("GF", "GF-106", {"kind": "BEAM_RUN", "run": "BM-GF-061"},
               "0.200 junction piece of the outer west strip (T-241 named face GF-106 -> BM-GF-061, D-26): beam lane, "
               "HELD"),
    "8805bf": ("GF", "GF-062", {"kind": "BEAM_RUN", "run": "BM-GF-061"},
               "0.200 junction piece of the outer west strip (T-241 named face GF-062 -> BM-GF-061, D-26): beam lane, "
               "HELD"),
    "5708ae": ("GF", "GF-096", {"kind": "BEAM_RUN", "run": "BM-GF-061"},
               "outer west strip 0.20 (D-26): beam lane, HELD"),
    "8754c1": ("GF", "GF-014", {"kind": "NOT_CONCRETE", "evidence": NOT_CONCRETE}, "drafting break mark"),
    "57ec39": ("GF", "GF-040", {"kind": "BEAM_RUN", "run": RING_RUN},
               "piece of the B7 void ring (released band 53 area): inside the drawn ring between its own arcs; the "
               "ring is billed once by the beam (T-252 R-BEAM-CURVED-AREA-2, Q-44 A)"),
    "4868d6": ("GF", "GF-097", {"kind": "BEAM_RUN", "run": "BM-GF-035.2#CB5-span2"},
               "CB5 span 2 band 0.20 x 3.70 (T-145): beam CB5 20 x 40, measured in the beam ledger"),
    "d54a5a": ("1F", "(unplaced)", {"kind": "BEAM_RUN", "run": "BM-1F-032#BAND0005.1"},
               "unlabelled span past a column east of the stair (D-04, Q-61 C(4)): beam lane, HELD"),
    "cf20e8": ("1F", "(unplaced)", {"kind": "NOT_CONCRETE", "evidence": NOT_CONCRETE}, "drafting break mark"),
    "4c7ca8": ("1F", "(unplaced)", {"kind": "BEAM_RUN", "run": "BM-1F-035#BAND0023"},
               "south-east box / 0.10 strip outside CB12 (D-05 / D-26): beam lane, HELD"),
    "cfe47b": ("1F", "1F-028", {"kind": "BEAM_RUN", "run": "BM-1F-036#BAND0025"},
               "strip outside CB12, north part (D-05): beam lane, HELD"),
    "ae2689": ("2F", "2F-008", {"kind": "NOT_CONCRETE", "evidence": NOT_CONCRETE}, "drafting break mark"),
    "5a1792": ("2F", "2F-031", {"kind": "BEAM_RUN", "run": "BM-2F-019#2F-031"},
               "0.10 strip west of B15 (T-241 BM-2F-019, D-26 family): beam lane, HELD with no value"),
}
# T-234 t234_alsenan_check.RELEASED['not_slab_faces'] net m2 (used only to re-find a face whose site hash moved)
NOT_SLAB_M2 = {"f9b0c2": 0.857337}
CHECKER_BEAM = ("Verifier 2026-10-24 05:37 UTC (T-252 Gate A: every CALCULATED run own-measured) + T-180 beam "
                "batches 01:24 / 02:02 / 02:08 / 03:12 UTC")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _pin(p, want):
    got = _sha(p)
    if got != want:
        raise SystemExit(f"{p} changed (sha256 {got[:12]}): re-check the inputs before integrating")
    return got


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def ledger():
    _pin(T252 / "LEDGER_T252.csv", T252_LEDGER_SHA)
    _pin(T252 / "summary.json", T252_SUMMARY_SHA)
    allr = list(csv.DictReader(open(T252 / "LEDGER_T252.csv", encoding="utf-8")))
    rows = [r for r in allr if r["status"] != "SUPERSEDED_R2"]
    # an r2 row whose pieces are not bands (the drawn ring) takes the bands of the r1 rows it supersedes
    extra = {}
    for r in allr:
        if r["status"] == "SUPERSEDED_R2" and r["superseded_by"] and not r["superseded_by"].startswith(r["run"]):
            extra.setdefault(r["superseded_by"], []).extend(_bands_of(r))
    for r in rows:
        if r["run"] in extra:
            r["pieces"] = "|".join(extra[r["run"]]) + " | " + r["pieces"]
    return rows, json.loads((T252 / "summary.json").read_text(encoding="utf-8"))


def snapshot():
    _pin(SNAP, SNAP_SHA)
    return json.loads(SNAP.read_text(encoding="utf-8"))


def _band(eid):
    m = re.match(r"^[PU]-C:BEAMS:(GF|1F|2F):(BAND\d{4}(?:\.\d)?)$", eid or "")
    return None if m is None else f"{m.group(1)}:{m.group(2)}"


def _bands_of(r):
    return [p.strip() for p in r["pieces"].split("|") if re.match(r"^(GF|1F|2F):BAND\d{4}(\.\d)?$", p.strip())]


def beam_mapping(rows, snap):
    """{candidate element id: [runs]}, {run: [candidate element ids]}, the ring line, and every line accounted."""
    cand = [x for x in snap["lines"] if x["item_code"] == BEAM]
    by_band = {}
    for x in cand:
        b = _band(x["element_id"])
        if b is not None:
            by_band[(x["floor"], b)] = x
    line_runs, run_lines = {}, {}
    for r in rows:
        for p in _bands_of(r):
            key = (r["storey"], p)
            if key not in by_band and p.endswith(".1") and (r["storey"], p[:-2]) in by_band:
                key = (r["storey"], p[:-2])           # one span of a band the route did not split
            elif key not in by_band and re.search(r"\.\d$", p) and (r["storey"], p[:-2]) in by_band:
                key = (r["storey"], p[:-2])           # a further span of the same band
            x = by_band.get(key)
            if x is None:
                continue
            line_runs.setdefault(x["element_id"], []).append(r["run"])
            run_lines.setdefault(r["run"], []).append(x["element_id"])
    for (fl, b), (run, _why) in IDENTITY.items():
        x = by_band[(fl, b)]
        if x["element_id"] in line_runs:
            raise SystemExit(f"identity {b}: already mapped to {line_runs[x['element_id']]}")
        line_runs[x["element_id"]] = [run]
        run_lines.setdefault(run, []).append(x["element_id"])
    ring = [x for x in cand if x["floor"] == "1F" and _band(x["element_id"]) is None
            and x["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE"]
    for x in ring:
        run = RING_LINES[x["element_id"]]
        line_runs[x["element_id"]] = [run]
        run_lines.setdefault(run, []).append(x["element_id"])
    return cand, line_runs, run_lines, ring


def _state(x):
    return x["value"] if x["evidence_state"] != "BOUNDED_EXPOSURE" else x["range"]


def beam_piece():
    rows, summ = ledger()
    snap = snapshot()
    cand, line_runs, run_lines, ring = beam_mapping(rows, snap)
    byid = {x["element_id"]: x for x in cand}
    na = {e for e, x in byid.items() if x["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE"}
    keep, sup, recs = [], [], []
    for r in rows:
        run = r["run"]
        st = r["status"]
        lines = [e for e in run_lines.get(run, []) if e not in na]
        m3, lo, hi = _f(r["m3"]), _f(r["m3_low"]), _f(r["m3_high"])
        one = len(lines) == 1 and len(line_runs[lines[0]]) == 1
        x = byid[lines[0]] if one else None
        adj = []
        if run in RING_OVERLAP_M2:
            a = RING_OVERLAP_M2[run]
            adj = [{"what": f"overlap with the drawn B7 void ring {a} m2 x D {DEPTH_RING_BANDS}",
                    "m3": round(a * DEPTH_RING_BANDS, 6),
                    "why": "the ring is measured between its own drawn edges (T-252, R-BEAM-CURVED-AREA-2); this "
                           "route band's fit reaches into it at the shared face: the intersection is removed once "
                           "(R-CONC-OWN-1; Verifier 05:37 named residual 0.00342 m2, Lead 06:15)"}]
        if one and not adj:
            live = x["evidence_state"] in ("PROVISIONAL", "SOURCE_DERIVED", "MEASURED")
            if st == "CALCULATED" and live and abs(x["value"] - m3) <= 1.000001e-4:
                keep.append({"element_id": x["element_id"], "floor": x["floor"], "run": run, "run_status": st,
                             "carried": x["value"], "ledger": m3,
                             "why": f"already carries run {run} ({r['mark']}) of the beam ledger: {m3} m3"})
                continue
            if st != "CALCULATED" and x["evidence_state"] == "BOUNDED_EXPOSURE" and lo is not None and \
                    abs(x["range"][0] - lo) <= 1.000001e-4 and abs(x["range"][1] - hi) <= 1.000001e-4:
                keep.append({"element_id": x["element_id"], "floor": x["floor"], "run": run, "run_status": st,
                             "carried": x["range"], "ledger": [lo, hi],
                             "why": f"already carries run {run} ({r['mark']}) as its range {lo} .. {hi} m3 ({st})"})
                continue
            if st == "HELD" and x["evidence_state"] == "BLOCKED_RFI":
                keep.append({"element_id": x["element_id"], "floor": x["floor"], "run": run, "run_status": st,
                             "carried": "BLOCKED", "ledger": [lo, hi] if lo is not None else "NO_VALUE",
                             "ledger_info": f"ledger candidate {lo} .. {hi} m3 kept as information only: "
                                            f"{r['reason'] or r['designer']}",
                             "why": f"the candidate already holds run {run} ({r['mark']}) with no value (never 0)"})
                continue
        reasons = [s for s in (r["designer"] and f"designer item {r['designer']}", r["reason"]) if s]
        rec = {"run": run, "floor": r["storey"], "mark": r["mark"], "member": r["member"], "status": st,
               "supersedes": list(lines),
               "source": f"{r['source']} | ledger T-252 r2 run {run} (pieces {r['pieces'][:120]})",
               "guard_element": {"element_id": f"BEAM-RUN:{r['storey']}:{run}", "part": "WHOLE"},
               "info": {"length_m": _f(r["length_m"]), "b_drawn_m": _f(r["b_drawn_m"]), "depth_m": _f(r["depth_m"]),
                        "ledger_adds": r["adds"], "ledger_deducts": r["deducts"], "basis": r["basis"],
                        "released_a_m3": _f(r["released_m3"]), "released_a_bounded": r["released_bounded"]}}
        if st == "CALCULATED":
            rec.update(base=m3, adjust=adj, value=round(m3 - sum(a["m3"] for a in adj), 6),
                       verified_by=CHECKER_BEAM)
        else:
            rec.update(reasons=reasons or [f"{st}: see the ledger row"], evidence_status="HELD",
                       range=[lo, hi] if lo is not None and hi is not None and hi > 0 else None)
        recs.append(rec)
    used = {e for rr in recs for e in rr["supersedes"]}
    for e, runs in sorted(line_runs.items()):
        x = byid[e]
        if x["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" or any(k["element_id"] == e for k in keep):
            continue
        if e not in used:
            raise SystemExit(f"line {e} is mapped to {runs} but superseded by none")
        sup.append({"element_id": e, "floor": x["floor"], "carried": _state(x),
                    "why": f"band of run(s) {', '.join(runs)} of the beam ledger (figure or state differs, or the "
                           "run carries more than this band)"})
    unmapped = [x["element_id"] for x in cand if x["element_id"] not in line_runs
                and x["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE"]
    return {"keep": keep, "sup": sup, "recs": recs, "unmapped": unmapped, "summary": summ, "ring": ring}


def slab_piece():
    _pin(T234 / "summary.json", T234_SUMMARY_SHA)
    s234 = json.loads((T234 / "summary.json").read_text(encoding="utf-8"))
    snap = snapshot()
    slabs = [x for x in snap["lines"] if x["item_code"] == SLAB]
    faces = []
    for suf, (fl, face, home, why) in FACE_HOME.items():
        hit = [x for x in slabs if x["floor"] == fl and x["element_id"].endswith(suf)]
        how = "engine face id"
        if not hit:   # the route's site hash moved since T-234's run: the same face by its net area (unique)
            m2 = NOT_SLAB_M2[suf]
            hit = [x for x in slabs if x["floor"] == fl and x["value"] is not None
                   and abs(x["value"] - m2 * 0.16) <= 1e-6]
            how = f"net area {m2} m2 x 0.16 (unique on the floor; T-234 engine face {suf})"
        if len(hit) != 1:
            raise SystemExit(f"slab face {suf}: {len(hit)} candidate lines")
        x = hit[0]
        faces.append({"element_id": x["element_id"], "floor": fl, "face": suf, "t139_face": face,
                      "carried": x["value"], "why": why + f" (identified by {how})", "home": home,
                      "drawing_reference": "ST7757 dxf.dxf slab sheets (ST p.4 / p.5 / p.6); T-139 partition face "
                                           f"{face}; T-234 LEDGER_T234.csv (not a panel)"})
    after = {fl: {"drawing": s234["by_storey"][fl]["m3"], "tol_m3": 0.0005,
                  "residual_why": "T-234 ledger panel areas rounded to 4 dp (its own residual -0.000243 on 1F)"}
             for fl in FLOORS}
    return faces, after, s234


def inputs(project_id):
    b = beam_piece()
    if b["unmapped"]:
        raise SystemExit(f"candidate beam line(s) in no run: {b['unmapped']}")
    summ = b["summary"]
    adj = sum(a["m3"] for r in b["recs"] for a in r.get("adjust") or ())
    # a held run the candidate already holds with no value (the east dome ring): the ledger's candidate range is
    # information, so the declared held range leaves it and the run is counted with no value (never 0)
    blocked = [k for k in b["keep"] if k["carried"] == "BLOCKED"]
    blk = [sum(k["ledger"][0] for k in blocked if isinstance(k["ledger"], list)),
           sum(k["ledger"][1] for k in blocked if isinstance(k["ledger"], list))]
    faces, after, _s234 = slab_piece()
    src = lambda f, task, mc, run: {"file": f, "sha256": _sha(ROOT / f), "task": task, "merge_commit": mc,  # noqa
                                    "checker_run": run}
    beam = {"piece": "BEAM_LEDGER", "item_code": BEAM, "unit": "m3",
            "source": src("research/agents_t252/LEDGER_T252.csv", "T-252", "b37be82d",
                          "Verifier 2026-10-24 05:37 UTC (Gate A PASS)"),
            "sources": [src("research/agents_t241/LEDGER_T241.csv", "T-241", "f0250164",
                            "Verifier 2026-10-24 00:06 UTC (Gate A PASS)"),
                        src("research/agents_t252/summary.json", "T-252", "b37be82d",
                            "Verifier 2026-10-24 05:37 UTC"),
                        src("research/agents_t146/CANDIDATE_V3011_BEAM_SLAB.json", "T-146 / T-247",
                            "this package", "worker 3 snapshot of the V3.0.11 run (figures re-checked live)")],
            "scope": {"floors": FLOORS, "keep_lines": b["keep"], "supersede_lines": b["sup"]},
            "records": b["recs"],
            "declared_totals": {"measured": round(summ["measured_m3"] - adj, 6), "conflict": summ["conflict"],
                                "held": [round(summ["held"][0] - blk[0], 6), round(summ["held"][1] - blk[1], 6)],
                                "held_no_value": sorted(summ["held_no_value"] + [k["run"] for k in blocked])}}
    slab = {"piece": "SLAB_FACE_HOME", "item_code": SLAB, "unit": "m3",
            "source": src("research/agents_t234/summary.json", "T-234", "3224f68a",
                          "Verifier 2026-10-23 23:01 UTC (Gate A PASS, 62 panels own re-measure 0.000 %)"),
            "sources": [src("research/agents_t234/LEDGER_T234.csv", "T-234", "3224f68a",
                            "Verifier 2026-10-23 23:01 UTC"),
                        src("research/agents_t145/ITEMS.csv", "T-145", "merged", "Verifier (T-145 MERGED)")],
            "faces": faces, "declared_after": after}
    sys.path.insert(0, str(ROOT / "research/agents_t193"))
    import t193_inputs as L7   # noqa: E402  (the V3.0.7 guard inputs, unchanged, as V3.0.8 .. V3.0.11)
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V3012_INPUTS_V1", "project": project_id, "pieces": [beam, slab], "guard": g}


if __name__ == "__main__":
    b = beam_piece()
    print("keep", len(b["keep"]), "supersede", len(b["sup"]), "records", len(b["recs"]), "unmapped", b["unmapped"])
    print("ring lines", [(x["element_id"], x["evidence_state"], x["value"]) for x in b["ring"]])
    for p in (T252 / "LEDGER_T252.csv", T252 / "summary.json", T234 / "summary.json", SNAP):
        print(p.name, _sha(p))
