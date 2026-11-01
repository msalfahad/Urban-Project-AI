"""T-433 Alsenan: the r4 concrete roll-up HELD figure (-116.428339 m3, T-428 MERGED ea8f5ae5, Checker-restated basis)
split by the item that holds it. Research only: no line, value, state or released cell changes.

Every part figure is read from a merged summary in this repository and asserted (R-T433-1): T-428 families (HELD per
family), T-406 retraced parts (BW-BAND, GB-BOUNDARY, GS-SLAB cell, CL-GF members, CL-LIFT, SD-*, PL-PUMP), T-397 rows
(the V3.0.33 column CONFLICT moves, per line), T-395 marks (held beam runs, per mark), T-391 (held run length 53.8353 m
at his one section 0.30 x 0.60), T-416 (1.533 m of held annex length fields through necks). Two component splits of
the unchanged T-385 r2 components (CL-NECK / CL-2F) are residual splits in m3 rebuilt by this run from the Drive
workbook with t385_extract.py + t385_alsenan.py (reproduced exactly: residual -114.464428, HELD -77.593, unexplained
-37.123829) and asserted here against the merged family sum; no freelancer row text, dimension or count is printed.

    python3 -I research/agents_t433/t433_alsenan.py [--write]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t433_rules as R  # noqa: E402

HIS_GB_SECTION_M2 = 0.18          # his one ground-beam section 0.30 x 0.60 (T-391 'his section over the held runs')
D34_LINES = ["L-0c5ede7fd2c9e425aa8d", "L-5af89b9f1e5b90daf8f5", "L-81444e222487437e257e", "L-970bac563cbcd69e2a30",
             "L-a8c5c32c7a785c1e3f05", "L-d53e5eb08e2c6c668254", "L-e2134034441cb7db7bd7", "L-f0e25ad2cf73bf2a35ea",
             "L-f24cf117a9ce1e875785"]   # downgrade DG-a31a0d7e9dd564ad (verdicts/V3.0.29/DOWNGRADES.json, board)
# residual splits of two unchanged T-385 r2 components (engine 0 held - other side), from this run's private rebuild
UNCHANGED_SPLIT = {"CL-NECK": -8.805, "CL-2F": -3.381}
HELD_R4 = -116.428339


def _j(p):
    return json.loads((RES / p).read_text(encoding="utf-8"))


def lines():
    d = _j("agents_t332/CANDIDATE_V3021_CONCRETE_LINES.json")["lines"]
    out = {ln["line_id"]: ln for ln in d}
    with open(RES / "agents_t387/BINDING_T387.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["item_code"] == "STR.CONC.PARAPET":
                out[r["line_id"]] = {"line_id": r["line_id"], "item_code": r["item_code"], "element_id": r["element_id"],
                                     "floor": r["floor"], "evidence_state": "BLOCKED_RFI", "measured_net": None,
                                     "formula": "blank (BLOCKED_RFI): parapet RC (T-319)", "dimensions": {}}
    return out


def sel(L, pred):
    return sorted(k for k, ln in L.items() if pred(ln))


def code(ln):
    return ln["item_code"].split(".")[-1]


def build():
    L = lines()
    t428 = _j("agents_t428/summary_t428.json")
    t406 = _j("agents_t406/summary_t406.json")
    t397 = _j("agents_t397/summary_t397.json")
    t395 = _j("agents_t395/summary_t395.json")
    t391 = _j("agents_t391/summary_t391.json")
    fam = {k: v["HELD"] for k, v in t428["families_r4_current"].items()}
    assert abs(t428["totals_r4_current"]["HELD"] - HELD_R4) < 1e-9
    rt = {c["id"]: c for c in t406["retraced_components"]}

    def held_part(cid, needle):
        ps = [p for p in rt[cid]["parts"] if p.get("verdict") == "HELD" and needle in p["cause"]]
        assert len(ps) == 1, (cid, needle)
        return ps[0]["m3"]

    parts, plines = {}, {}

    def add(pid, m3, ids):
        assert pid not in parts
        parts[pid] = round(m3, 6)
        plines[pid] = list(ids)

    # ---- blinding, footing, boundary below N.G.
    add("BL-1", fam["CONC.BLINDING"], sel(L, lambda l: code(l) == "BLINDING"))
    add("FT-F10", fam["CONC.FOOTING"], sel(L, lambda l: code(l) == "FOOTING" and ":T652:" in l["element_id"]))
    add("BW-BAND", held_part("BW-BAND", "lower boundary band"), sel(L, lambda l: code(l) == "BOUNDARY_WALL"))
    add("GB-BOUNDARY", held_part("GB-BOUNDARY", "upper G.B"), ["L-fb7a6431fede62e93fd5"])
    # ---- ground: slab cell + held ground-beam runs at his section
    add("GS-CELL", held_part("GS-SLAB", "HELD cell"), ["L-41cfb82ed733f4d6e3a5"])
    gb = {l["line_id"]: l for l in L.values() if code(l) == "GROUND_BEAM" and "BOUNDARY" not in l["element_id"]}
    d35 = sel(gb, lambda l: "D-35 annex" in (l["formula"] or "") and l["measured_net"] is None)
    court = sel(gb, lambda l: "court section" in (l["formula"] or "") and l["measured_net"] is None)
    lens = {k: gb[k]["dimensions"]["length_m"] for k in d35 + court + D34_LINES}
    m35, mct, m34 = (round(sum(lens[k] for k in s), 4) for s in (d35, court, D34_LINES))
    assert (len(d35), len(court), len(D34_LINES)) == (8, 3, 9)
    assert abs(m35 + mct + m34 - t391["beams"]["held_length_m"]) < 1e-9
    assert abs(HIS_GB_SECTION_M2 * t391["beams"]["held_length_m"] + t391["beams"]["cause_terms_m3"]["held_runs"]) < 1e-6
    add("GB-HELD-D35", -HIS_GB_SECTION_M2 * m35, d35)
    add("GB-HELD-COURT", -HIS_GB_SECTION_M2 * mct, court)
    add("GB-HELD-D34", -HIS_GB_SECTION_M2 * m34, D34_LINES)
    neck_fields = [p for p in t428["restated_components"]["GB-MAIN"]["parts"] if p.get("verdict") == "HELD"
                   and abs(p["m3"] - 0.27594) < 1e-6]
    assert len(neck_fields) == 1
    add("GB-HELD-D35-NECKFIELDS", neck_fields[0]["m3"], [])       # same three D-35 lines, length fields through necks
    # ---- columns
    gf_mem = sel(L, lambda l: code(l) == "COLUMN" and l["floor"] == "GF" and l["evidence_state"] == "BLOCKED_RFI")
    add("CL-GF-MEMBERS", held_part("CL-GF", "held members"), gf_mem)
    mv = {}
    for r in t397["rows"]:
        if r["item_code"] == "STR.CONC.COLUMN" and r.get("record_action") == "CONFLICT_RANGE":
            tag = "D16" if "D-16" in r["after_held_range_v3_0_33"]["basis"] else "BAND"
            mv.setdefault((r["floor"], tag), []).append(r)
    for (fl, tag), rows in sorted(mv.items()):
        add(f"CL-{fl}-MOVE-{tag}", -sum(r["before_v3_0_32"]["value"] for r in rows), [r["line_id"] for r in rows])
    add("CL-LIFT", held_part("CL-LIFT", "net ring"), ["L-684fcad323adc0c8a267"])
    add("CL-NECK", UNCHANGED_SPLIT["CL-NECK"], sel(L, lambda l: code(l) == "NECK"))
    add("CL-2F", UNCHANGED_SPLIT["CL-2F"], sel(L, lambda l: code(l) == "COLUMN" and l["floor"] == "2F"
                                              and l["evidence_state"] == "BLOCKED_RFI"))
    assert len(plines["CL-2F"]) == 9 and len(plines["CL-GF-MEMBERS"]) == 5 and len(plines["CL-NECK"]) == 36
    # ---- beams: held runs per mark (T-395)
    for m in t395["marks"]:
        if m["HELD"]:
            # a ledger run 'BM-1F-032#BAND0005.1' is either the ledger line itself or the held band line of that
            # floor (U-C:BEAMS:1F:BAND0005.1, no value)
            def hit(l, h):
                band = h.split("#")[1]
                return l["element_id"].endswith(h) or (l["element_id"] == f"U-C:BEAMS:{m['floor']}:{band}"
                                                      and l["measured_net"] is None
                                                      and l["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE")
            ids = [k for k, l in L.items() if code(l) == "BEAM" and any(hit(l, h) for h in m["held_runs"])]
            assert len(ids) == len(m["held_runs"]), m
            add(f"BM-{m['floor']}-{m['mark']}", m["HELD"], sorted(ids))
    # ---- stairs / domes / pool
    add("SD-DOME-3", held_part("SD-DOME", "DOME-3"), ["L-d5401fa8986900c66c37"])
    add("SD-ST01-MS1L", held_part("SD-STAIR", "SD-ST01-MS1L"), ["L-7863355dfcb68a681d2d"])
    add("SD-ST01-TURNS", held_part("SD-STAIR", "SD-ST01-TURNS"), ["L-659243ed9fc2831c3ae8"])
    add("SD-ST03-E1", held_part("SD-STAIR", "SD-ST03-E1"), ["L-061e18cf35a4b6b33d68"])
    rsc = [p for p in t428["restated_components"]["SD-STAIR"]["parts"] if p.get("verdict") == "HELD" and "RS-C" in p["cause"]]
    assert len(rsc) == 1
    add("SD-ST02-RSC", rsc[0]["m3"], ["L-b6b0354b7842f0ed6e41"])
    add("PL-PUMP", held_part("PL-PUMP", "pump"), [])
    add("PL-STEPS", fam["CONC.POOL"] - parts["PL-PUMP"], ["L-b62a7065645589011141"])
    assert abs(parts["PL-STEPS"] + 0.228) < 1e-9
    # ---- family closure against the merged r4 table
    fam_of = {"BL": "CONC.BLINDING", "FT": "CONC.FOOTING", "BW": "CONC.BOUNDARY_BELOW_NG", "GB-BOUNDARY":
              "CONC.BOUNDARY_BELOW_NG", "GS": "CONC.GROUND", "GB": "CONC.GROUND", "CL": "CONC.COLUMN", "BM": "CONC.BEAM",
              "SD": "CONC.STAIR_DOME", "PL": "CONC.POOL"}
    got = {}
    for p, v in parts.items():
        f = fam_of["GB-BOUNDARY"] if p == "GB-BOUNDARY" else fam_of[p.split("-")[0]]
        got[f] = round(got.get(f, 0) + v, 6)
    for f, v in fam.items():
        assert abs(got.get(f, 0.0) - v) < 2e-6, (f, got.get(f), v)
    return L, parts, plines, t428


# ---- blocker items (R-T433-2 / -5). drawings: sheet / page searched by this run's sources (merged tasks cited)
ITEMS = [
    dict(id="I-01", parts=["BL-1"], joint=True, route="DESIGNER",
         blockers=["DG-3521554d2fd011b9 footing layer (FF raft projection not printed on p.14, T-322; 8 plot-line "
                   "footings D-14)", "F10 + F outline Q-31 C", "ground-beam blinding: footing detail choice open "
                   "(D-34 / D-35 sections)", "strap blinding not printed D-15"],
         rfi=["RFI-S06", "RFI-S07", "RFI-S08", "RFI-S02", "RFI-S09", "RFI-S11"],
         drawings_searched=["ST p.13 (typical footing / ground-beam blinding)", "ST p.14 (lift raft)", "ST p.2",
                            "ST p.10 (straps)"],
         sources=["T-322 MERGED d3bcd9d4", "T-385 r2 (BL-1)"],
         s27="drawings print blinding under footings and the 4 ground-beam sections only (p.13), no projection under the "
             "lift raft (p.14), none under straps: drawings cannot resolve; his one plain layer over a rectangle is a scope "
             "no sheet prints, so even with every RFI answered a RULE_DIFFERENCE remains (not separable from his one row)",
         beside="engine 4 lines: footing layer 15.179437 (Checker 12.734438 VERIFIED + FF HELD >= 2.070), F10/F 0.552 .. "
                "0.590, ground beams 4.949374 .. 9.422514, straps 0.377803 .. 0.771877"),
    dict(id="I-02", parts=["CL-NECK"], route="DESIGNER", blockers=["Q-21 C founding / neck start level"],
         rfi=["RFI-S01"], drawings_searched=["ST p.13", "ST p.2", "ST p.9 notes 1 / 4"], sources=["T-385 r2", "T-357"],
         s27="p.9 note 1 fixes a minimum excavation only; no sheet prints the footing underside or the neck start level",
         beside="engine 36 necks 3.075 .. 15.375 (+1 unbounded)"),
    dict(id="I-03", parts=["BW-BAND"], route="DESIGNER", blockers=["DG-6dd9f1caba1ca77d lower band depth (Q-28)"],
         rfi=["RFI-S03"], drawings_searched=["ST p.1", "ST p.10", "ST p.14", "ST p.2"], sources=["T-403", "T-356"],
         s27="the band's section and level are printed on no sheet (owner method A carried as the comparison basis)",
         beside="engine range 5.6392 .. 11.0328 (DG-6dd9f1caba1ca77d)"),
    dict(id="I-04", parts=["CL-GF-MOVE-BAND", "CL-1F-MOVE-BAND"], route="DESIGNER",
         blockers=["13 column outlines vs schedule bands (designer list D-66; the V3.0.33 line basis text says D-63)"],
         rfi=["RFI-S20"], drawings_searched=["ST p.4", "ST p.5", "ST p.9 (column schedule)"], sources=["T-397 Gate B 4492fd59"],
         s27="the plan outline and the schedule band of each column differ on the same issued set: two authoritative "
             "documents conflict (ERS s.2.7)", beside="engine CONFLICT ranges per line (T-397 rows)"),
    dict(id="I-05", parts=["GB-HELD-D35", "GB-HELD-D35-NECKFIELDS"], route="DESIGNER",
         blockers=["D-35 exterior / annex ground-beam depth 'FOLLOW ARCH.' with no printed build-up"], rfi=["RFI-S09"],
         drawings_searched=["ST p.13 (ground-beam sections)", "ST ground-beam plan", "arch sections A-A / B-B"],
         sources=["T-391 c3fe8ec8", "T-416 (length fields)", "T-426 1f298735"],
         s27="p.13 ties the depth to the architecture; no sheet prints the annex floor build-up", beside="8 blank lines"),
    dict(id="I-06", parts=["BM-GF-B21", "BM-GF-B29", "BM-GF-CB2"], route="DESIGNER",
         blockers=["D-27 schedule width differs from the drawn width"], rfi=["RFI-S13"],
         drawings_searched=["ST p.10 / p.11 (beam schedules)", "ST p.4", "ST p.5"], sources=["T-395"],
         s27="schedule and plan of the same set disagree (Q-61 C(1): never pick the schedule only because it is printed)",
         beside="engine ranges GF B21 2.262872 .. 2.545691, B29 1.013607 .. 1.266989, CB2 0.347 .. 0.4338 + 0.335 .. 0.4188"),
    dict(id="I-07", parts=["GS-CELL"], route="ENGINE",
         blockers=["engine reads the lift-shaft corner columns as free columns (T-042 ENGINE_MISSED_PRINTED_VALUE)"],
         settle_drawing="ST ground-beam / slab-on-grade plan: own panels OWN-007 / 009 / 010 / 047 = 35.6054 m2 x printed "
                        "T = 0.10 (T-391 MERGED own read)",
         drawings_searched=["ST ground-beam plan (slab-on-grade cells)", "ST p.14 (lift shaft)"],
         sources=["T-391 c3fe8ec8 F1", "T-397 (bound 0 .. 3.56054)"],
         s27="NOT met: the drawing settles the panels; the hold is an engine reading defect, not a designer item",
         beside="engine bound 0 .. 3.56054"),
    dict(id="I-08", parts=["GB-BOUNDARY"], route="DESIGNER",
         blockers=["M4 boundary-wall columns 20 x 30 'SEE ARCH PLAN', none drawn (count and positions)"], rfi=["RFI-S04"],
         drawings_searched=["ST p.14", "arch sheet 03 (GF plan)"], sources=["T-403", "T-400 (V3.0.35 range)"],
         s27="the structural note refers to an architectural plan that draws no such columns",
         beside="engine 0 .. 3.5256 (V3.0.35)"),
    dict(id="I-09", parts=["PL-PUMP"], route="DESIGNER", blockers=["pool pump / plant room drawn on no sheet"],
         rfi=["RFI-B-A14 (T-398 draft; not in the 2026-10-31 RFI register: RFI_MISSING there)"],
         drawings_searched=["ST p.7 (pool detail)", "ST DXF texts / layers", "arch DXF texts (EN / AR)", "sanitary sheets"],
         sources=["T-398 fe6a238d"], s27="absent from every sheet; not a verified absence", beside="no candidate line"),
    dict(id="I-10", parts=["CL-2F"], joint=True, route="DESIGNER",
         blockers=["D-39 roof datum (9 lines)", "D-44 B15 upstand / downstand (2 lines)", "section conflict (2 lines)",
                   "planted column PC-2F section text vs outline (1 line)"],
         rfi=["RFI-S23", "RFI-S22", "RFI_MISSING (PC-2F section)"],
         drawings_searched=["arch sheets 04 / 10 / 11 (roof levels)", "ST p.6", "ST p.10", "ST p.15 (planted columns)"],
         sources=["T-385 r2 (CL-2F)"], s27="roof slab-top level printed on no sheet (finished levels only)",
         beside="9 blank lines"),
    dict(id="I-11", parts=["GB-HELD-D34"], route="DESIGNER",
         blockers=["D-34 length basis / title precedence of the p.13 sections"], rfi=["RFI-S11"],
         drawings_searched=["ST p.13"], sources=["T-391", "T-426", "verdicts/V3.0.29 DG-a31a0d7e9dd564ad"],
         s27="'more / less than 5 m / 2.5 m' without a basis; two titles hold below 2.5 m", beside="9 downgraded lines"),
    dict(id="I-12", parts=["SD-DOME-3"], route="DESIGNER", blockers=["D-21 tower dome over the 2F maid room (Q-27 A)"],
         rfi=["RFI-S28"], drawings_searched=["ST p.6", "ST p.7", "arch 2F plan"], sources=["T-398"],
         s27="architecture draws a dome; the structural slab is flat with no opening or ring", beside="1 blank line"),
    dict(id="I-13", parts=["CL-GF-MEMBERS"], joint=True, route="DESIGNER",
         blockers=["annex roof datum Q-54 B / D-17", "D-39 roof datum", "section conflict (4 of 5 lines)"],
         rfi=["RFI-S23", "RFI-S20"], drawings_searched=["arch section B-B (+4.30)", "ST p.4", "ST p.9"],
         sources=["T-394"], s27="annex slab-top level not printed; outline vs schedule conflict", beside="5 blank lines"),
    dict(id="I-14", parts=["FT-F10"], route="DESIGNER", blockers=["Q-31 C F10 + F one outline, two tags"],
         rfi=["RFI-S02"], drawings_searched=["ST p.2", "ST p.9"], sources=["T-385 r2"],
         s27="one outline carries two schedule tags whose sizes do not match it", beside="engine 2.176 .. 2.275"),
    dict(id="I-15", parts=["BM-GF-B24", "BM-1F-B2", "BM-2F-B1", "BM-2F-B15", "BM-2F-B8"], route="DESIGNER",
         blockers=["D-04 unlabelled beam spans (line formulas: designer item D-04 / UNLABELLED_SPAN_ACROSS_SUPPORT)"],
         rfi=["RFI-S15"], drawings_searched=["ST p.4", "ST p.5", "ST p.6"], sources=["T-395"],
         s27="spans drawn with no mark: type and section unknown", beside="engine bounds per line"),
    dict(id="I-16", parts=["CL-GF-MOVE-D16", "CL-1F-MOVE-D16"], route="DESIGNER",
         blockers=["D-16 column C8 plan 30X80 vs schedule 30 x 90"], rfi=["RFI-S19"],
         drawings_searched=["ST p.1", "ST p.9"], sources=["T-397"], s27="plan and schedule conflict",
         beside="engine GF 0.9 .. 1.0125, 1F 0.756 .. 0.84"),
    dict(id="I-17", parts=["SD-ST01-MS1L"], joint=True, route="DESIGNER",
         blockers=["C-ST-4 MS1-L riser count (structural GF roof slab plan vs architecture)",
                   "MS1-T winder subdivision not drawn (S-9)"], rfi=["RFI-A04", "RFI-S24"],
         drawings_searched=["ST p.4", "ST p.16", "arch sheet 03", "arch sheet 10 (section A-A)"],
         sources=["T-398", "T-434", "OWNER_RULE_STAIRS_2026-10-24 s.4"],
         s27="two issued sheets print different riser counts; winders never generated (owner S-9)", beside="1 blank line"),
    dict(id="I-18", parts=["CL-LIFT"], joint=True, route="SUPPLIER",
         blockers=["lift pit depth below the lowest landing (lift supplier)", "GF floor build-up F.F.L. +1.00 -> "
                   "slab-on-grade top (D-22 / D-40)"],
         rfi=["RFI L-1 (lift supplier, T-401)", "RFI-B-A01 (D-40 floor build-up; mapped by title)"],
         drawings_searched=["ST p.14", "ST p.8 note 19", "arch GF plan"], sources=["T-401", "T-394"],
         s27="neither the pit depth nor the build-up is printed; both are needed (R-T401-2)",
         beside="pit wall plan 1.100 m2 DRAWING-CONFIRMED (Checker T-394); the T-406 / T-428 cause text cites D-43 "
                "(the lift tie-beam size), which does not hold this part (F-T433-1)"),
    dict(id="I-19", parts=["SD-ST03-E1"], route="DESIGNER", blockers=["E1 waist thickness not printed (S-9 / G2-w)"],
         rfi=["RFI-S26"], drawings_searched=["ST p.16", "ST p.3", "arch sheet 03"], sources=["T-398"],
         s27="waist slab or steps on fill: not printed", beside="1 blank line"),
    dict(id="I-20", parts=["SD-ST02-RSC"], route="DESIGNER", blockers=["ST-02 RS-C soffit and waist (Q-50, RFI-S27)"],
         rfi=["RFI-S27"], drawings_searched=["ST p.16", "ST p.4", "arch GF / 1F frames"],
         sources=["T-415", "T-438 63f77c1d"], s27="no section cuts the curved part", beside="drawn plan 4.443096 m2"),
    dict(id="I-21", parts=["GB-HELD-COURT"], route="DESIGNER",
         blockers=["court ground-beam section not printed (GS-16 architect item)"],
         rfi=["RFI_MISSING (no RFI in the 2026-10-31 register names the court ground-beam section)"],
         drawings_searched=["ST p.13", "ST ground-beam plan"], sources=["T-242", "T-253 s.4", "T-391"],
         s27="p.13 prints no section for the court runs", beside="3 blank lines"),
    dict(id="I-22", parts=["BM-1F-CB10"], route="DESIGNER", blockers=["D-02 CB10 schedule 0.25 vs drawn 0.30"],
         rfi=["RFI-S12"], drawings_searched=["ST p.11", "ST p.5", "ST p.12"], sources=["T-395"],
         s27="schedule and plan conflict", beside="engine 0.2875 .. 0.345 + 0.4563 .. 0.5475"),
    dict(id="I-23", parts=["BM-GF-CB3"], route="DESIGNER", blockers=["D-03 CB3 and 'B3 (with stair)' on one line"],
         rfi=["RFI-S14"], drawings_searched=["ST p.16", "ST p.4"], sources=["T-395"], s27="two labels on one line",
         beside="engine 0.212 .. 0.3975"),
    dict(id="I-24", parts=["SD-ST01-TURNS"], joint=True, route="DESIGNER",
         blockers=["MS1-T slab under the winder turn", "MS2-TR turn riser: landing levels scaled, not printed"],
         rfi=["RFI-S24", "RFI-S25"], drawings_searched=["ST p.4", "ST p.5", "ST p.16"], sources=["T-398"],
         s27="landing levels and the turn slab are not printed", beside="1 blank line (MS2-TR); MS1-T slab: named item"),
    dict(id="I-25", parts=["PL-STEPS"], route="DESIGNER", blockers=["pool steps not drawn (consultant item)"],
         rfi=["RFI-A02"], drawings_searched=["arch GF plan", "ST p.7", "sections"], sources=["T-183"],
         s27="not drawn: an absence of evidence, not a verified zero", beside="1 blank line"),
]


def item_m3(parts):
    for it in ITEMS:
        it["m3"] = round(sum(parts[p] for p in it["parts"]), 6)


def held_beside(L, plines, parts):
    """held engine lines with no part of the HELD figure (R-T433-3)."""
    used = {x for v in plines.values() for x in v}
    held = []
    for k, ln in sorted(L.items()):
        if ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE":
            continue
        if (ln["measured_net"] is None) and k not in used:
            held.append({"line_id": k, "item_code": ln["item_code"], "floor": ln["floor"],
                         "blocker": (ln["formula"] or "")[:140]})
    held.append({"line_id": "L-cda8f41522dc6f42b3d6", "item_code": "STR.CONC.BOUNDARY_PAD", "floor": "GROUND",
                 "blocker": "pad count not printed (T-403; V3.0.35 T-400: 0.312 m3 per pad beside, no residual move)"})
    return held


def run():
    L, parts, plines, t428 = build()
    item_m3(parts)
    for it in ITEMS:
        it["lines"] = [x for p in it["parts"] for x in plines[p]]
    beside = held_beside(L, plines, parts)
    tot = R.check_items(ITEMS, parts, HELD_R4, beside)
    inv, rfi, rfi_rank = R.ranked(ITEMS)
    return {"schema": "T433_V1", "basis": "T-428 r4 MERGED ea8f5ae5, Checker-restated basis traced -1.300165 / HELD "
            "-116.428339 / unexplained -5.171754 (O-T428-1 ruled); candidate V3.0.37 = V3.0.38 for valued concrete",
            "held_total_m3": tot, "parts": parts, "part_lines": plines,
            "items": [{k: v for k, v in it.items()} for it in ITEMS],
            "investigation_ranked": [i["id"] for i in inv], "rfi_items_ranked": [i["id"] for i in rfi],
            "rfi_ranked": rfi_rank, "beside_no_comparison_term": beside,
            "engine_side_register_beside": t428["engine_side_register"],
            "by_route": {r: round(sum(i["m3"] for i in ITEMS if i["route"] == r), 6) for r in R.ROUTES}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    s = run()
    print("HELD", s["held_total_m3"], "items", len(s["items"]), "parts", len(s["parts"]), "beside",
          len(s["beside_no_comparison_term"]), "by route", s["by_route"])
    for it in s["items"]:
        print(f"{it['id']} {it['m3']:>11.6f} {it['route']:8s} {len(it['lines']):3d} lines  {'; '.join(it['blockers'])[:90]}")
    print("RFI ranked", s["rfi_ranked"])
    if a.write:
        (HERE / "summary_t433.json").write_text(json.dumps(s, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                                encoding="utf-8")


if __name__ == "__main__":
    main()
