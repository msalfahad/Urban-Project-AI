"""T-786 (DELIVERY MODE fix-row set, lane S): the two UNRESOLVED concrete residuals left by merged T-777 / T-778.

Beams (+7.46 m3 UNRESOLVED in T-777 = C4 6.86 DEFAULT depths + C4b 0.60 drawn unlabelled): every piece re-read.
  * ROOF-EDGE PROJECTION BANDS (11 lines, D-05 / D-26), carried at the 0.60 beam default since T-761. ST sections A-A
    (GF, B20) and B-B (1F, B23) CUT the 0.20 bands north of B20 / B23 (cut lines on the slab plans cross the bands) and
    draw only the beam (40 x 75 / 45 x 75) with its 20 x 20 upstand: no concrete in the band. Owner Q-61 (5): not a
    beam. The other bands are the SAME drawn type (unhatched band outside the edge beam, roof edge, rounded corners on
    the facade line, the slab note 'check architectural detail of parapet before casting'): same reading by element
    type. A band is the roof slab carried to the facade line: depth = printed slab thickness 0.16 (ST note 18), DEFAULT
    (UNMARKED_PIECE_DEPTH_V1, t786_rules.py); D-26 replaces it.
  * D-04 adjacent-span pieces, D-03 CB3 / 'B3 (with stair)', D-28 east dome ring: already on the ladder's adjacent-span
    step (no printed depth exists; T-761 / T-757): kept, named.
  * GF BM-GF-059 (B24 past its support, 1.501 x 0.50 x 0.75, measured 0.5496): the freelancer's B24 row 5.75 m carries it
    (engine B24 3.55 + 1.50 = 5.05 m): RULE_DIFFERENCE of line attribution, not unresolved.
Non-beam (-5.84 m3 UNRESOLVED in T-778): every cause named with its drawing reference and designer item; no printed
section or schedule replaces any of them (T-778 search confirmed here for the ground beams: their depths are the ST p.13
typical class by clear span; the open items are D-33 loaded spans, D-34 length basis, D-35 exterior depth).

    python3 -I research/agents_t786/fill_t786.py [--write | --check]
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import t786_rules as R  # noqa: E402

IDX = os.path.join(ROOT, "research/agents_t770/out/LINE_INDEX_V3_0_85.json")
T777 = os.path.join(ROOT, "research/agents_t777/out/BEAM_CAUSES.json")
T778 = os.path.join(ROOT, "research/agents_t778/out/NONBEAM_CAUSES.json")
SLAB_T = 0.16                 # ST note 18: slab thickness 0.16 (printed)
FL_BEAM = 65.965875           # his beam total cell (T-777)
FL_RC_TOTAL = 352.44          # his RC total (T-778); 1 % = 3.52 m3

CUT = "section_cut"           # the band is cut by a printed section that shows no concrete in it
TYPE = "same_type"            # same drawn type as a cut band
BANDS = {
    # line: (storey, where, evidence, plan m2 from the T-721 DXF read in the line basis, sheet reference)
    "L-634cefe5e8a7fb458e16": ("GF", "0.20 band north of B20, run 1 (edges 2C6 / 2C7)", CUT, 0.5998,
                               "ST GF roof slab plan, cut A-A crosses it; SECTION A-A = B20 40 x 75 + upstand 20 x 20"),
    "L-331d4bbef719a7f0bbca": ("GF", "0.20 band north of B20, run 2 (edges 2C6 / 2C7)", CUT, 0.1050,
                               "ST GF roof slab plan, same band as run 1 (cut A-A)"),
    "L-67f3d325019e618328eb": ("1F", "0.20 band north of B23, run 1 (edges 5E1 / 5E6)", CUT, 0.5997,
                               "ST 1F roof slab plan, cut B-B crosses it; SECTION B-B = B23 45 x 75 + upstand 20 x 20"),
    "L-54e397fe7b1485b2e8fe": ("1F", "0.20 band north of B23, run 2 (edges 5E1 / 5E6)", CUT, 0.1048,
                               "ST 1F roof slab plan, same band as run 1 (cut B-B)"),
    "L-aba59a2157a48a69e2fb": ("GF", "0.20 west outer band outside CB5, 4.10 m", TYPE, 0.8200,
                               "ST GF roof slab plan, west edge, continues the B20 band round its rounded corner"),
    "L-a9d5e7dc22013e24d691": ("1F", "0.20 west outer band outside CB10, 7.50 m (edges 5E7 / 5E5)", TYPE, 1.4999,
                               "ST 1F roof slab plan, west edge, continues the B23 band round its rounded corner"),
    "L-56d278bedc8dda2837a9": ("1F", "0.30 band outside CB12 north part, 4.28 m (edges 5DE / 629)", TYPE, 1.5441,
                               "ST 1F roof slab plan, east edge, rounded NE corner"),
    "L-bb49e831f053bd30a6ce": ("1F", "0.30 x 0.90 SE box outside CB11 / CB12 (edges 5C1 / 619)", TYPE, 0.2698,
                               "ST 1F roof slab plan, SE corner, rounded"),
    "L-377cb988b2271c2e2e4d": ("1F", "0.10 band outside CB12 south part, 5.69 m", TYPE, 0.5690,
                               "ST 1F roof slab plan, east edge"),
    "L-fbb65dfd2a66a16714ac": ("1F", "0.40 x 1.00 rounded box outside CB12 at the east column", TYPE, 0.4000,
                               "ST 1F roof slab plan, east edge, rounded"),
    "L-17c4238c0ef76656d06e": ("2F", "0.10 edge band 4.35 m", TYPE, 0.4350,
                               "ST 2F roof slab plan, roof edge"),
}
KEPT = {
    # beam pieces kept on the ladder (no printed depth exists): line -> (designer item, why kept)
    "L-56c49c3c2596a0869533": ("D-05", "1F strip at the column at B23's end (0.16 m2, T-724 census; not the outside "
                                       "projection band): beam piece, company 0.60 kept"),
    "L-f113ed57f7875fed9a67": ("D-05", "GF strip at the column at B20's end (0.16 m2, T-724 census; not the outside "
                                       "projection band): beam piece, company 0.60 kept"),
    "L-7c3edce23ec8faa3d674": ("D-04", "2F span past a column, adjacent span B1 20 x 40 (ladder step 2)"),
    "L-dc8cbfc119d006ff3927": ("D-04", "2F span past a column, adjacent span B1 20 x 40 (ladder step 2)"),
    "L-8d031491396379f0cbb1": ("D-04", "2F perimeter piece, adjacent span B8 20 x 75 (ladder step 2)"),
    "L-d62d2fcf3d0023ad1ad1": ("D-04", "2F span past a column, adjacent span B15 20 x 120 (ladder step 2; B15 stand D-44)"),
    "L-f83c4a469845c7e14dfa": ("D-04", "1F span past a column, adjacent span B2 20 x 40 (ladder step 2)"),
    "L-88ccf8d4505411deb9e5": ("D-03", "GF CB3 / 'B3 (with stair)' one beam counted once at CB3 20 x 75 both sides"),
    "L-ab37afa17f2ac5b0efd1": ("D-28", "east dome ring at the twin west ring B4 depth 0.50 (same ST p.7 dome detail)"),
}
RULE_DIFF_LINES = {
    "L-8ea71184fff91b4357b7": "GF BM-GF-059 B24 past its support 1.501 x 0.50 x 0.75 (measured 0.5496): his B24 row "
                              "5.75 m = engine B24 3.55 + this 1.50 + 0.70; the same concrete on his B24 line",
}


def r6(x):
    return round(x + 0.0, 6)


def build():
    idx = json.load(open(IDX))
    by = {l["line_id"]: l for l in idx["lines"]}
    beams = [l for l in idx["lines"] if l["item_code"] == "STR.CONC.BEAM" and l["class"] == "RELEASED"]
    beam_before = sum(l["measured_net"] or 0.0 for l in beams)
    rows, d_beam = [], 0.0
    for lid, (st, where, ev, a, ref) in BANDS.items():
        l = by[lid]
        assert l["item_code"] == "STR.CONC.BEAM" and l["class"] == "RELEASED" and l.get("method_label") == "DEFAULT"
        old = l["measured_net"]
        assert abs(old - round(a * R.BEAM_DEFAULT_DEPTH_M, 4)) < 6e-4, (lid, old, a)
        kind = R.classify(True, True, ev == CUT, False if ev == CUT else None, ev == TYPE)
        assert kind == "PROJECTION_BAND"
        v = R.piece_m3(a, kind, slab_thickness=SLAB_T)
        net = round(v["net"], 4)
        d_beam += net - old
        why = ("cut by the section, which draws no concrete in it (owner Q-61 (5): not a beam)" if ev == CUT else
               "same drawn type as the bands cut by sections A-A / B-B (unhatched band outside the edge beam on the "
               "roof edge, rounded facade corners): same element, not a beam")
        rows.append({"line_id": lid, "item_code": "STR.CONC.BEAM", "unit": "m3", "element_id": l["element_id"],
                     "before": {"class": "RELEASED", "net": old, "label": "DEFAULT"},
                     "after": {"class": "RELEASED", "net": net}, "label": "DEFAULT", "designer_item": "D-26",
                     "basis": f"{st} roof-edge projection band: {where}: plan {a:.4f} m2 (T-721 DXF) x {SLAB_T:.2f} "
                              f"printed slab thickness (ST note 18; band = roof slab carried to the facade line, cast "
                              f"with the slab; UNMARKED_PIECE_DEPTH_V1) = {net:.4f} m3; was {old:.4f} at the 0.60 beam "
                              f"default; {why}; {ref}; D-26 replaces it",
                     "evidence": ev, "beside": {"beam_default_0.60": old, "no_concrete_low": 0.0}})
    beam_after = beam_before + d_beam
    # ---- beam residual after the fix, named piece by piece ---------------------------------------------------------
    t777 = json.load(open(T777))
    unresolved_beam = []
    for lid, (di, why) in KEPT.items():
        l = by[lid]
        unresolved_beam.append({"line_id": lid, "m3": l["measured_net"], "label": l.get("method_label"),
                                "designer": di, "reference": why})
    for r in rows:
        unresolved_beam.append({"line_id": r["line_id"], "m3": r["after"]["net"], "label": "DEFAULT",
                                "designer": "D-26", "reference": "projection band at the printed slab thickness: his "
                                "beam rows omit it; whether his slab area (x 0.16) runs to the facade line is not "
                                "readable from his rows"})
    c2a = t777["causes"]["C2a_WIDTH"]
    unresolved_beam.append({"line_id": "T-777 C2a", "m3": c2a, "label": "MEASURED / DRAWING-READ",
                            "designer": "D-27 / D-02", "reference": "drawn width vs his schedule width: GF B21 / B29 / "
                            "CB2, 1F B6 / CB10 (ST GF and 1F roof slab plans vs schedule)"})
    beam_unres = sum(u["m3"] for u in unresolved_beam)
    rule_diff = [{"line_id": k, "m3": by[k]["measured_net"], "verdict": "RULE_DIFFERENCE", "reference": v}
                 for k, v in RULE_DIFF_LINES.items()]
    # ---- non-beam: named from T-778 ---------------------------------------------------------------------------------
    t778 = json.load(open(T778))
    refs = {"N-4": "ST p.9 n.1 founding; lift raft level D-43", "C-1": "ST p.9 schedule CGT 1ST C6; D-66",
            "C-2 COUNT 1F": "ST 1F column plan mark assignment C3 / C6 / C7 / C8 / C9; D-66 / T-566",
            "C-3": "C8 10E0 drawn 0.25 x 0.80 vs schedule; D-66 / T-566", "C-5": "2F roof section not printed; "
            "roof build-up DEFAULT 0.175", "G-1": "ST p.13 typical GB sections by clear span; D-33 loaded spans, "
            "D-34 length basis, D-35 exterior depth 'FOLLOW ARCH.'", "G-2": "his two lumps 100 + 111 m vs the "
            "engine's bound runs (T-391 envelope 193.76 .. 231.91 m)", "G-3": "BAND0009 no T-170 footprint",
            "GS-3": "T-391 F3 small reads", "ST-6": "ST-02 curved stair no section; D-08", "ST-8": "ST-03 no waist "
            "printed; S-9 / D-56", "ST-10": "ST-01 turn pieces; T-711 DEFAULT", "L-2": "ST p.8 n.19 tie beam size "
            "not printed; D-43"}
    unresolved_non = []
    for f in t778["families"]:
        for c, v in f["verdicts"].items():
            if v == "UNRESOLVED":
                ref = next((rv for rk, rv in refs.items() if c.startswith(rk)), "")
                assert ref, c
                unresolved_non.append({"family": f["family"], "cause": c, "m3": f["causes"][c], "reference": ref})
    non_unres = sum(u["m3"] for u in unresolved_non)
    assert abs(non_unres - t778["verdict_totals"]["UNRESOLVED"]) < 1e-3
    summary = {
        "lines_changed": len(rows), "lines_new": 0,
        "beam_m3_before": r6(beam_before), "beam_m3_after": r6(beam_after), "beam_delta_m3": r6(d_beam),
        "freelancer_beam_m3": FL_BEAM,
        "beam_vs_freelancer_before": f"{beam_before - FL_BEAM:+.2f} m3 ({100 * (beam_before - FL_BEAM) / FL_BEAM:+.1f} %)",
        "beam_vs_freelancer_after": f"{beam_after - FL_BEAM:+.2f} m3 ({100 * (beam_after - FL_BEAM) / FL_BEAM:+.1f} %)",
        "beam_unresolved_before_m3": r6(t777["causes"]["C4_UNLABELLED_PIECES_DEFAULT_DEPTH"]
                                        + t777["causes"]["C4b_UNLABELLED_PIECES_DRAWING_READ"] + c2a),
        "beam_unresolved_after_m3": r6(beam_unres),
        "beam_rule_difference_moved_m3": r6(sum(x["m3"] for x in rule_diff)),
        "nonbeam_unresolved_m3": r6(non_unres),
        "nonbeam_unresolved_gross_m3": r6(sum(abs(u["m3"]) for u in unresolved_non)),
        "one_pct_of_his_rc_total_m3": round(FL_RC_TOTAL / 100, 2),
        "acceptance": "every remaining UNRESOLVED m3 named with its drawing reference and designer item (beam and "
                      "non-beam tables); none is replaceable by a printed schedule or section",
    }
    return idx, {"schema": "URBAN_FIX_ROWS_V1", "task": "T-786", "candidate_version": idx["candidate_version"],
                 "rule": "UNMARKED_PIECE_DEPTH_V1 (proposed, research/agents_t786/t786_rules.py)",
                 "inputs": {"index": "LINE_INDEX_V3_0_85.json", "t777": "research/agents_t777/out/BEAM_CAUSES.json",
                            "t778": "research/agents_t778/out/NONBEAM_CAUSES.json",
                            "drawings": "Drive 'Alsenan chalet project' ST7757 dxf.dxf: SECTION A-A / B-B, GF / 1F roof "
                                        "slab plans (cut lines A / B, edges 2C6 2C7 5E1 5E6 5E5 5E7 5DE 629 5C1 619), "
                                        "slab notes 'check architectural detail of parapet before casting'; "
                                        "P7757_DXF_COMPRESSED.zip SE / NW elevations (dimensions only)"},
                 "summary": summary, "rows": rows, "new_lines": [],
                 "beam_unresolved_named": unresolved_beam, "beam_rule_difference": rule_diff,
                 "nonbeam_unresolved_named": unresolved_non,
                 "ignored_small": "GF-NW-CORNER / 1F-NW-CORNER (0.0293 m2 each) stay EXCLUDED: at 0.16 they are "
                                  "0.0047 m3 each, still < 0.05"}


def md(out):
    s = out["summary"]
    L = [f"# T-786 fix rows on {out['candidate_version']}: concrete UNRESOLVED residuals", "", "Rule: " + out["rule"],
         "", "## Summary", "", "```", json.dumps(s, indent=1), "```", "", "## Changed lines", "",
         "| line | before | after | label | basis |", "|---|---|---|---|---|"]
    L += [f"| {r['line_id']} | {r['before']['net']:.4f} | {r['after']['net']:.4f} | {r['label']} | {r['basis']} |"
          for r in out["rows"]]
    L += ["", "## Beam UNRESOLVED after this set (named)", "", "| line | m3 | label | designer | reference |",
          "|---|---|---|---|---|"]
    L += [f"| {u['line_id']} | {u['m3']:+.4f} | {u['label']} | {u['designer']} | {u['reference']} |"
          for u in out["beam_unresolved_named"]]
    L += ["", "## Moved to RULE_DIFFERENCE", ""] + [f"- {x['line_id']} {x['m3']:.4f}: {x['reference']}"
                                                     for x in out["beam_rule_difference"]]
    L += ["", "## Non-beam UNRESOLVED (T-778 causes, named)", "", "| family | cause | m3 | reference |",
          "|---|---|---|---|"]
    L += [f"| {u['family']} | {u['cause']} | {u['m3']:+.4f} | {u['reference']} |" for u in out["nonbeam_unresolved_named"]]
    L += ["", "Ignored small: " + out["ignored_small"]]
    return "\n".join(L) + "\n"


def main(argv):
    _, out = build()
    d = os.path.join(HERE, "out")
    pj, pm = os.path.join(d, "FIX_ROWS.json"), os.path.join(d, "FIX_ROWS.md")
    txt = json.dumps(out, indent=1) + "\n"
    if "--check" in argv:
        ok = open(pj).read() == txt and open(pm).read() == md(out)
        print("CHECK OK" if ok else "CHECK FAILED: out/ differs from a fresh build")
        return 0 if ok else 1
    print(json.dumps(out["summary"], indent=1))
    if "--write" in argv:
        os.makedirs(d, exist_ok=True)
        open(pj, "w").write(txt)
        open(pm, "w").write(md(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
