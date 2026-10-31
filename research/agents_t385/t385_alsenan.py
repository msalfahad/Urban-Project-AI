"""T-385: concrete reconciliation of the candidate of record ARCH_TAKEOFF_V3.0.29 against the freelancer, family by family
(development villa; research only: no quantity, line or released cell changes). Reads only ALSENAN_T385_INPUT.json (values
only, built by t385_extract.py from the private Drive copies, kept in .work/private) and writes RECON_T385.csv,
FAMILIES_T385.csv, summary_t385.json to a directory OUTSIDE the repository (they print the freelancer's values).

    python3 -I research/agents_t385/t385_alsenan.py [--input <private>/t385/ALSENAN_T385_INPUT.json] --out <private dir>

Families = the eight freelancer summary rows keyed by tests/alsenan/T001C_KEY_MAP.json (sheet 1 rows 15, 17 .. 23); the
candidate's STR.CONC.PARAPET lines have no key and no freelancer row: they are listed as ENGINE_ONLY (HELD).
Contractual view: a line under a Checker downgrade record (verdicts/V3.0.29/DOWNGRADES.json) is HELD, its figure audit only.
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t385_rules as R  # noqa: E402

# The input carries the freelancer's row values (private workbook content): it lives in .work/private, never in a
# tracked file; so do the outputs that print them (owner rule: no workbook content in the public repository).
INPUT = HERE.parents[2] / "private" / "t385" / "ALSENAN_T385_INPUT.json"
ARITH = {"BM-ARITH": (4, 82, list(range(59, 79)))}
S1 = "RC:ورقة1:"
FAMILY_OF = {"BLINDING": "CONC.BLINDING", "FOOTING": "CONC.FOOTING", "STRAP": "CONC.FOOTING",
             "BOUNDARY_WALL": "CONC.FOOTING", "GROUND_BEAM": "CONC.GROUND", "GROUND_SLAB": "CONC.GROUND",
             "NECK": "CONC.COLUMN", "COLUMN": "CONC.COLUMN", "BEAM": "CONC.BEAM", "SLAB": "CONC.SLAB",
             "STAIR": "CONC.STAIR_DOME", "DOME": "CONC.STAIR_DOME", "POOL": "CONC.POOL", "PARAPET": "UNKEYED.PARAPET"}
FAMILY_ROW = {"CONC.BLINDING": 15, "CONC.FOOTING": 17, "CONC.GROUND": 18, "CONC.COLUMN": 19, "CONC.BEAM": 20,
              "CONC.SLAB": 21, "CONC.STAIR_DOME": 22, "CONC.POOL": 23}


def code(ln):
    return ln["item_code"].split(".")[-1]


def eid(ln):
    return ln["element_id"] or ""


def is_na(ln):
    return ln["evidence_state"] in ("NOT_APPLICABLE_WITH_EVIDENCE", "EXCLUDED_WITH_REASON")


# ---- component definitions: (id, family, element, line selector, freelancer (sheet, rows), cause class, cause, verdict,
#      evidence). Selectors are applied in order; a line goes to the FIRST component that selects it.
def footing_mark(m):
    return lambda ln: code(ln) == "FOOTING" and re.search(rf":SH10:{re.escape(m)}:", eid(ln)) is not None


COMPONENTS = [
    # ---------------- CONC.BLINDING (freelancer sheet 1 row 15 = sheet 'footings' row 11)
    ("BL-1", "CONC.BLINDING", "plain concrete under footings, ground beams and straps",
     lambda ln: code(ln) == "BLINDING", (1, [11]), "HELD_ITEM",
     "engine: footing layer 15.179437 under downgrade DG-3521554d2fd011b9 (FF projection inherited from the p.13 typical "
     "detail; Checker footing layer 12.734438 VERIFIED + FF HELD >= 2.070) + F10/F conflict 0.552 .. 0.590 + ground-beam "
     "blinding 4.949374 .. 9.422514 (footing detail choice open) + strap blinding 0.377803 .. 0.771877 (not printed): "
     "contractual valued 0. Freelancer: ONE plain layer over a whole rectangle, "
     "a scope the drawings do not print (blinding is drawn under members, ST p.13 / p.14); the scope difference is "
     "RULE_DIFFERENCE once the engine side is released", "HELD",
     "ST7757.pdf p.13 / p.14; Q-21 C; T-322; verdicts/V3.0.29 DG-3521554d2fd011b9"),
    # ---------------- CONC.FOOTING (sheet 'footings' rows 13 .. 32)
    ("FT-F", "CONC.FOOTING", "F x4 0.80 x 0.90 x 0.30", footing_mark("F"), (1, [13]), "AGREE",
     "same schedule size and count", "AGREE", "ST p.10 schedule"),
    ("FT-F2", "CONC.FOOTING", "F2 x2", footing_mark("F2"), (1, [14]), "AGREE", "same size and count", "AGREE", "ST p.10"),
    ("FT-F3", "CONC.FOOTING", "F3 1.40 x 1.60 x 0.30", footing_mark("F3"), (1, [15]), "COUNT",
     "engine 2 drawn F3 outlines (two outlines labelled F3 on the foundation plan, one carries the SB3 strap end) x 0.672; "
     "freelancer counts one", "ENGINE_RIGHT", "ST7757 dxf.dxf: 2 labels C3/F3 (own count, T-385); T-174 SB3 record"),
    ("FT-F4", "CONC.FOOTING", "F4 x2", footing_mark("F4"), (1, [16]), "AGREE", "same size and count", "AGREE", "ST p.10"),
    ("FT-F5", "CONC.FOOTING", "F5 x2", footing_mark("F5"), (1, [17]), "AGREE", "same size and count", "AGREE", "ST p.10"),
    ("FT-F6", "CONC.FOOTING", "F6", footing_mark("F6"), (1, [18]), "AGREE", "same size", "AGREE", "ST p.10"),
    ("FT-F8", "CONC.FOOTING", "F8", footing_mark("F8"), (1, [19]), "AGREE", "same size", "AGREE", "ST p.10"),
    ("FT-F9", "CONC.FOOTING", "F9", footing_mark("F9"), (1, [20]), "AGREE", "same size", "AGREE", "ST p.10"),
    ("FT-F10", "CONC.FOOTING", "F10 + F one drawn outline (T652)", lambda ln: code(ln) == "FOOTING" and ":T652:" in eid(ln),
     (1, [21]), "HELD_ITEM", "engine HELD 2.176 .. 2.275 (schedule rows vs the drawn outline at the deepest depth, Q-31 C "
     "RFI); freelancer takes the schedule size", "HELD", "Q-31 C; OWNER_RECONCILIATION G3"),
    ("FT-F11", "CONC.FOOTING", "F11", footing_mark("F11"), (1, [22]), "AGREE", "same size", "AGREE", "ST p.10"),
    ("FT-F12", "CONC.FOOTING", "F12", footing_mark("F12"), (1, [23]), "AGREE", "same size", "AGREE", "ST p.10"),
    ("FT-F13", "CONC.FOOTING", "F13", footing_mark("F13"), (1, [24]), "AGREE", "same size", "AGREE", "ST p.10"),
    ("FT-F14", "CONC.FOOTING", "F14", footing_mark("F14"), (1, [25]), "AGREE", "same size", "AGREE", "ST p.10"),
    ("FT-F15", "CONC.FOOTING", "F15", footing_mark("F15"), (1, [26]), "AGREE", "same size", "AGREE", "ST p.10"),
    ("FT-FF", "CONC.FOOTING", "FF raft (lift pit base) 4.50 x 4.60 x 0.55", footing_mark("FF"), (1, [27]), "AGREE",
     "same size", "AGREE", "ST p.10 / p.14"),
    ("FT-FN", "CONC.FOOTING", "FN x4 1.00 x 1.00 x 0.30", footing_mark("FN"), (1, [28]), "DIMENSION",
     "one FN outline is clipped where it meets a neighbouring footing: 0.258 instead of 0.300, the 0.042 overlap owned once "
     "by the neighbour; freelancer counts the overlap in both", "ENGINE_RIGHT",
     "candidate line formula (drawn polygon x D, clipped part belongs to the neighbour)"),
    ("ST-SB1", "CONC.FOOTING", "strap SB1 0.70 x 0.50 on the 4.55 face-to-face axis",
     lambda ln: code(ln) == "STRAP" and eid(ln).endswith("SB1:CONCRETE"), (1, [29]), "AGREE", "same section and length",
     "AGREE", "ST p.10 Schedule of Simple Beams; Q-74"),
    ("ST-SB1-IN", "CONC.FOOTING", "SB1 inside the open F10 + F outline",
     lambda ln: code(ln) == "STRAP" and ":SB1:IN_FOOTING" in eid(ln), None, "HELD_ITEM",
     "held 0 .. 0.385 (strap depth below the shallower footing part; owner of the overlap open with F10, Q-31 C); "
     "freelancer has no row for it", "HELD", "T-174"),
    ("ST-SB2", "CONC.FOOTING", "strap SB2 1.00 x 0.50", lambda ln: code(ln) == "STRAP" and eid(ln).endswith("SB2:CONCRETE"),
     (1, [30]), "DIMENSION", "axis face to face 2.2927 m drawn; freelancer a rounded axis",
     "ENGINE_RIGHT", "ST7757 dxf.dxf strap edges; Q-74"),
    ("ST-SB3", "CONC.FOOTING", "strap SB3 0.50 x 0.40", lambda ln: code(ln) == "STRAP" and eid(ln).endswith("SB3:CONCRETE"),
     (1, [31]), "DIMENSION", "axis 3.258 m drawn; freelancer a rounded axis", "ENGINE_RIGHT",
     "ST7757 dxf.dxf edges 1B26 / 1B27; Q-74"),
    ("ST-SB3-IN", "CONC.FOOTING", "SB3 depth below F3 inside the F3 outline",
     lambda ln: code(ln) == "STRAP" and ":SB3:IN_FOOTING" in eid(ln), None, "HELD_ITEM",
     "held 0.0295 .. 0.1181 (strap level against the footing not printed); no freelancer row", "HELD", "T-174, T-347"),
    ("ST-NA", "CONC.FOOTING", "plot-edge bands booked under STRAP: NOT_APPLICABLE (carried by the ground-beam lines)",
     lambda ln: code(ln) == "STRAP" and is_na(ln), None, "SCOPE",
     "NOT_APPLICABLE_WITH_EVIDENCE lines: no volume here, no freelancer row", "AGREE", "PLOT_EDGE_MEMBERS_V1"),
    ("BW-BAND", "CONC.FOOTING", "boundary-wall lower band 0.20 wide round the plot",
     lambda ln: code(ln) == "BOUNDARY_WALL", (1, [32]), "WRONG_BASIS",
     "engine line 60.17 m x 0.20 x 0.60 = 7.2204 under downgrade DG-6dd9f1caba1ca77d (one plot side lost); band range "
     "5.6392 .. 11.0328 (T-356: 91.94 m drawn centreline / 70.49 m free of 9 footing crossings, sections 0.60 / p.14); "
     "freelancer one length x the 0.20 x 0.60 section (compare against the range)", "HELD",
     "ST7757 dxf.dxf S-BOUN; ST p.10 B.W 20 x 60; T-356; Q-28 A"),
    # ---------------- CONC.GROUND (sheet 'straps / ground' rows 11, 13, 14, 15)
    ("GS-SLAB", "CONC.GROUND", "ground-bearing slab faces (24 site faces + 1 cell between free columns)",
     lambda ln: code(ln) == "GROUND_SLAB", (2, [11]), "SCOPE",
     "engine: 24 faces, face area with the members' overlap deducted x the printed thickness = 17.2407 valued + 1 face "
     "HELD 3.9298 (free-column cell); freelancer one gross area x thickness with no member deduction: the "
     "residual contains the HELD face 3.9298 and the gross-vs-net area difference (not traced face by face here)",
     "UNRESOLVED", "T-347 binding; candidate formulas"),
    ("GB-BOUNDARY", "CONC.GROUND", "boundary-wall ground beam at N.G.",
     lambda ln: code(ln) == "GROUND_BEAM" and eid(ln).startswith("T254:"), (2, [15]), "HELD_ITEM",
     "engine HELD (M4: boundary-wall columns 20 x 30 'SEE ARCH PLAN', none drawn: count and positions); freelancer "
     "one length x section", "HELD", "T-254; M4"),
    ("GB-MAIN", "CONC.GROUND", "ground beams (59 candidate runs incl. D-34 / D-35 / court holds)",
     lambda ln: code(ln) == "GROUND_BEAM", (2, [13, 14]), "HELD_ITEM",
     "engine valued on 38 runs (contractual: 9 D-34 lines 1.943901 downgraded DG-a31a0d7e9dd564ad, range "
     "from 1.643901 (T-356); 8 D-35 annex runs CONFLICT blank; 3 court runs HELD blank); freelancer two lumps (longitudinal, transverse) "
     "with one section for every run; his lengths are not split by run, so the residual is not traced "
     "run by run here", "UNRESOLVED", "T-253, T-254, T-356; D-33 / D-34 / D-35"),
    # ---------------- CONC.COLUMN (sheet 'walls + columns')
    ("CL-LIFT", "CONC.COLUMN", "lift pit walls 0.20", None, (3, [11]), "SCOPE",
     "freelancer one row; no candidate line carries the lift pit walls (T-322 ledger, research, "
     "unwired)", "UNRESOLVED", "ST p.14; T-322"),
    ("CL-NECK", "CONC.COLUMN", "column necks (36)", lambda ln: code(ln) == "NECK", (3, list(range(16, 29))), "HELD_ITEM",
     "engine 36 necks HELD 3.075 .. 15.375 (+1 unbounded): formation / founding level open (Q-21 C, T-357 ground "
     "derived from corner levels only); freelancer one neck height on every neck", "HELD", "Q-21 C; T-357"),
    ("CL-GF", "CONC.COLUMN", "GF columns", lambda ln: code(ln) == "COLUMN" and ln["floor"] == "GF", (3, list(range(36, 48))),
     "DIMENSION", "engine 25 valued 17.9675 (schedule section x member height, Checker component 18.3465 on 28 closable "
     "columns) + 5 HELD blank (D-16 / D-63 / D-64 conflicts); freelancer one storey height on every column; "
     "the residual mixes the HELD 5 and the height basis: not closed per column here", "UNRESOLVED", "ST p.9; T-248, T-256"),
    ("CL-1F", "CONC.COLUMN", "1F columns + planted columns",
     lambda ln: code(ln) == "COLUMN" and ln["floor"] == "1F", (3, list(range(52, 62))), "DIMENSION",
     "engine 18 valued + PC-1F-A 0.588 + PC-1F-B 0.420 = 10.248 m3 = 2.44 m2 of section x 4.20 m (profile 9.65 - 5.45, "
     "every 1F column; the third 1F C3 NOT_PRESENT, no sheet draws it; C6 x1, C8 x2 and C9 x2 at 0.20 x 0.90); "
     "freelancer a lower storey height and another mark population: the m3 split (height basis + marks) closes in the "
     "private notes; the height basis (column through the slab / beam joint vs clear height) is an owner-method "
     "question not yet settled, so UNRESOLVED",
     "UNRESOLVED", "ST p.9 schedule; T-248"),
    ("CL-2F", "CONC.COLUMN", "2F / roof columns", lambda ln: code(ln) == "COLUMN" and ln["floor"] == "2F",
     (3, list(range(66, 72))), "HELD_ITEM",
     "engine 9 HELD blank (2F roof datum D-39 <= 3.155) + 5 NA; freelancer one storey height", "HELD", "D-39"),
    ("CL-UNDRAWN", "CONC.COLUMN", "5 columns no storey plan draws", lambda ln: code(ln) == "COLUMN",
     None, "HELD_ITEM", "engine 5 HELD 1.134 .. 3.483 (D-65 undrawn); no freelancer row", "HELD", "D-65; T-256"),
    # ---------------- CONC.BEAM (sheet 'beams')
    ("BM-GF", "CONC.BEAM", "beams of the GF roof slab", lambda ln: code(ln) == "BEAM" and ln["floor"] == "GF",
     (4, list(range(11, 51))), "HELD_ITEM",
     "engine 39.3291 valued + 10 HELD (CONFLICT runs B29, CB2, B21, B6, CB10; D-27 / D-02 / D-26) + 35 "
     "NA; freelancer one width x depth x length per run: the residual mixes the HELD runs and length basis",
     "UNRESOLVED", "T-252, T-247; ST p.11 schedule"),
    ("BM-1F", "CONC.BEAM", "beams of the 1F roof slab incl. the west dome ring",
     lambda ln: code(ln) == "BEAM" and ln["floor"] == "1F", (4, list(range(59, 79))), "HELD_ITEM",
     "engine 22.6903 valued (incl. DOME-1F-W ring 0.7552; DOME-1F-E ring HELD) + 12 HELD (bounds in the held columns) + 18 NA; "
     "freelancer per-run rows (no dome ring row): not closed per run here",
     "UNRESOLVED", "T-252; Q-61 C(3)"),
    ("BM-2F", "CONC.BEAM", "beams of the 2F roof slab", lambda ln: code(ln) == "BEAM" and ln["floor"] == "2F",
     (4, list(range(86, 96))), "HELD_ITEM",
     "engine 4.2985 valued + 5 HELD (bounds in the held columns) + 1 NA; freelancer per-run rows: "
     "not closed per run here", "UNRESOLVED", "D-39"),
    ("BM-ARITH", "CONC.BEAM", "freelancer 1F beam sub-total", None, None, "FREELANCER_ARITHMETIC",
     "his printed 1F sub-total leaves one of his own 1F rows out, so his family total is below the sum of his "
     "rows by that row (value in the private table only)", "ENGINE_RIGHT", "freelancer sheet 'beams' rows 59 .. 82"),
    # ---------------- CONC.SLAB (sheet 'slabs')
    ("SL-GF", "CONC.SLAB", "GF roof slab panels", lambda ln: code(ln) == "SLAB" and ln["floor"] == "GF", (5, [11]),
     "DIMENSION", "engine 62-panel net (Checker WHOLE-LINE VERIFIED 60.2804 for the three storeys) GF 33.0695; "
     "freelancer one area rounded to the m2 x 0.16", "ENGINE_RIGHT",
     "record V2-c5004423d32f2106; T-146 / T-247"),
    ("SL-1F", "CONC.SLAB", "1F roof slab panels", lambda ln: code(ln) == "SLAB" and ln["floor"] == "1F", (5, [16]),
     "DIMENSION", "engine 19.7563; freelancer one area rounded to the m2 x 0.16", "ENGINE_RIGHT",
     "record V2-c5004423d32f2106"),
    ("SL-2F", "CONC.SLAB", "2F roof slab panels", lambda ln: code(ln) == "SLAB" and ln["floor"] == "2F", (5, [23, 24]),
     "DIMENSION", "engine 7.4543; freelancer two areas x 0.16 / 0.18", "ENGINE_RIGHT",
     "record V2-c5004423d32f2106"),
    # ---------------- CONC.STAIR_DOME (sheet 'stairs')
    ("SD-DOME", "CONC.STAIR_DOME", "three domes (Q-27 A)", lambda ln: code(ln) == "DOME", (6, [13]), "HELD_ITEM",
     "engine DOME-A and DOME-B shells 2 x 2.540681 (spherical cap, chord 4.42, rise 1.90, t 0.10, Q-18) + DOME-3 HELD "
     "(no structural detail) + 2 NA; freelancer three equal domes from one developed area x 0.10: "
     "the two shells differ by his area vs the cap's own; DOME-3 HELD", "UNRESOLVED",
     "Q-18, Q-27 A; T-185; ST p.7"),
    ("SD-STAIR", "CONC.STAIR_DOME", "stairs ST-01 / ST-02 / ST-03 (entrance)", lambda ln: code(ln) == "STAIR",
     (6, [11, 12, 20, 21]), "HELD_ITEM",
     "engine closable pieces 5.3689 (MS2 flights 2.5044, MS1 1.2280, lobby D1 steps 0.1003, ST-02 straight part 1.5362) "
     "+ 6 HELD blank (C-ST-3 / C-ST-4, unprinted waists, ST-02 curved parts Q-50 / Q-51, E1 waist) + 1 NA; freelancer "
     "one plate thickness on plan length x width for every flight + landings: the residual is mostly the HELD flights",
     "UNRESOLVED", "T-258 r2, T-290; OWNER_RULE_STAIRS"),
    # ---------------- CONC.POOL (sheet 'pool')
    ("PL-BASE", "CONC.POOL", "pool base", lambda ln: code(ln) == "POOL" and eid(ln).endswith(":BASE") and not is_na(ln), (7, [11]),
     "DIMENSION", "drawn D outline 3.50 x 1.75 + pi 1.75^2 / 2 = 10.935564 m2 x 0.40 = 4.374226 ; freelancer a rounded "
     "area x 0.40", "ENGINE_RIGHT", "ST p.7; Q-26 A"),
    ("PL-WALLS", "CONC.POOL", "pool walls", lambda ln: code(ln) == "POOL" and eid(ln).endswith(":WALLS") and not is_na(ln), (7, [12]),
     "DEPTH", "engine wall band 2.356726 m2 x 1.20 (rim to the base top, the wall foot measured once in the base) = "
     "2.828071; freelancer a length x 0.20 x a height taken from the base bottom: height (the "
     "base counted again in the wall) and plan length; split in the private table", "ENGINE_RIGHT", "ST p.7; R-POOL-4 r2; Q-26 A"),
    ("PL-STEPS", "CONC.POOL", "pool steps", lambda ln: code(ln) == "POOL" and eid(ln).endswith(":STEPS"), (7, [14]),
     "HELD_ITEM", "not drawn: consultant item (owner 2026-10-22 16:45); freelancer one row", "HELD", "T-183"),
    ("PL-PUMP", "CONC.POOL", "pump room walls and floor", lambda ln: code(ln) == "POOL" and is_na(ln), (7, [13, 15]),
     "SCOPE", "freelancer pump walls + room floor rows; the candidate has only the "
     "two scope lines of the pool outline (NOT_APPLICABLE, carried by POOL-1) and no pump-room line", "UNRESOLVED",
     "ST p.7 (pump room detail to be read)"),
    # ---------------- parapet (no key, no freelancer row)
    ("PA-RC", "UNKEYED.PARAPET", "parapet RC upstands (4 roofs)", lambda ln: code(ln) == "PARAPET", None, "HELD_ITEM",
     "engine 4 HELD blank lines (bounds in their formulas, at least 8.050943 m3 together); no freelancer RC row",
     "HELD", "T-311, T-319"),
]


def load(path=None):
    return json.loads(Path(path or INPUT).read_text(encoding="utf-8"))


def build(doc=None):
    doc = doc or load()
    lines = doc["concrete_lines"]
    by_id = {l["line_id"]: l for l in lines}
    dg = sorted({i for d in doc["downgrades"] for i in d["line_ids"]})
    fl_rows = {r["ref"]: r["m3"] for r in doc["freelancer_rows"]}
    sheet_ref = {(r["sheet"], r["row"]): r["ref"] for r in doc["freelancer_rows"]}
    assign = {}
    comps = []
    for cid, fam, elem, sel, flr, cc, cause, verdict, ev in COMPONENTS:
        ids = []
        if sel is not None:
            for l in lines:
                if l["line_id"] not in assign and FAMILY_OF[code(l)] == fam and sel(l):
                    assign[l["line_id"]] = cid
                    ids.append(l["line_id"])
        refs = [sheet_ref[(flr[0], r)] for r in flr[1] if (flr[0], r) in sheet_ref] if flr else []
        c = {"id": cid, "family": fam, "element": elem, "engine_lines": ids, "freelancer_rows": refs,
             "cause_class": cc, "cause": cause, "verdict": verdict, "evidence": ev}
        if cid in ARITH:                       # his printed sub-total minus the sum of his own rows (from the input)
            sh, total_row, rows = ARITH[cid]
            c["freelancer_arithmetic_m3"] = R.r6(fl_rows[sheet_ref[(sh, total_row)]]
                                                  - sum(fl_rows[sheet_ref[(sh, r)]] for r in rows if (sh, r) in sheet_ref))
        comps.append(c)
    fam_rows, fams = [], []
    for fam in list(FAMILY_ROW) + ["UNKEYED.PARAPET"]:
        fc = [c for c in comps if c["family"] == fam]
        fl_total = doc["freelancer_family_totals"][S1 + str(FAMILY_ROW[fam])] if fam in FAMILY_ROW else 0.0
        fl = [l["line_id"] for l in lines if FAMILY_OF[code(l)] == fam]
        rows, s = R.family(fam, fc, fl, by_id, fl_rows, fl_total, downgraded_ids=dg)
        s["freelancer_row"] = (S1 + str(FAMILY_ROW[fam])) if fam in FAMILY_ROW else "none"
        fam_rows += rows
        fams.append(s)
    return fam_rows, fams, doc


def _csv(rows, cols):
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    return b.getvalue()


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    inp = argv[argv.index("--input") + 1] if "--input" in argv else None
    rows, fams, doc = build(load(inp))
    out = {"RECON_T385.csv": _csv(rows, list(rows[0])), "FAMILIES_T385.csv": _csv(fams, list(fams[0]))}
    keyed = [f for f in fams if f["freelancer_row"] != "none"]
    summ = {"schema": "T385_SUMMARY_V1", "candidate": doc["candidate"],
            "candidate_lines_json_sha256": doc["candidate_lines_json_sha256"],
            "concrete_lines": len(doc["concrete_lines"]), "components": len(rows),
            "engine_valued_m3": R.r6(sum(f["engine_valued_m3"] for f in keyed)),
            "freelancer_m3": R.r6(sum(f["freelancer_m3"] for f in keyed)),
            "residual_m3": R.r6(sum(f["residual_m3"] for f in keyed)),
            "families_closing": sum(1 for f in fams if f["closes"]), "families": len(fams),
            "verdicts": {v: sum(1 for r in rows if r["verdict"] == v) for v in R.VERDICTS},
            "contribution_by_verdict_m3": {v: R.r6(sum(r["contribution_m3"] for r in rows if r["verdict"] == v))
                                           for v in R.VERDICTS}}
    out["summary_t385.json"] = json.dumps(summ, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if "--out" in argv:
        d = Path(argv[argv.index("--out") + 1]).resolve()
        if HERE.parents[1] in d.parents or d == HERE.parents[1]:
            raise SystemExit("--out must be outside the repository (the tables print freelancer values)")
        d.mkdir(parents=True, exist_ok=True)
        for k, v in out.items():
            (d / k).write_text(v, encoding="utf-8")
    return out


if __name__ == "__main__":
    o = main()
    print(o["FAMILIES_T385.csv"])
    print(o["summary_t385.json"])
