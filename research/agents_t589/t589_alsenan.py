"""T-589: STRUCTURAL CLOSABLE-COMPONENT PACK for the 12-13 Nov scorecard (development villa; research, unwired).

Every B10 / B11 / B1 component of the reconciled statement V6 (T-586, sha-pinned) that is not VERIFIED, plus the
components restated after V6 by the merged T-576 (columns, GF B7) and T-583 (dome / ring / lift-wall bars), is put in
one closure class under R-T589-1 (t589_rules.py): VERIFIED_ON_RECORD, CLOSABLE_FROM_DRAWINGS (sheet + pack),
DESIGNER_ITEM (D-nn / RFI id), OWNER_RULE_GAP. The structural sheet references are to Drive 'Alsenan chalet project' /
'ST7757.pdf' (sha256 74da1523..) and 'ST7757 dxf.dxf' (sha256 9f9d1179..), by page / detail / handle only.

Also restated here: F-C-T583-1 (east dome-ring side bars on both faces, own read of ST p.7 this run) and F-T589-1
(the S02 range low of the F10 + F footing, owner 2026-11-02 condition 4). No quantity moves; nothing released.

  python3 -I research/agents_t589/t589_alsenan.py --write   # write out/
  python3 -I research/agents_t589/t589_alsenan.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t589_rules as R  # noqa: E402

D = Decimal
RES = HERE.parent
OUT = HERE / "out"
JSON_OUT = OUT / "T589_CLOSABLE_PACK.json"
MD_OUT = OUT / "T589_CLOSABLE_PACK.md"
SOURCES = {
    "V6": (RES / "agents_t586/out/RECONCILED_STATEMENT_T586.json",
           "a50b12b394bb73e85fbd8a1a4068eb89c20d8b713b58a7a9e129fba9071a2694"),
    "T583": (RES / "agents_t583/out/T583_DOME_LIFT_COMPONENTS.json",
             "64d827202e4e87fbd457a4a6b9f07664656b07f7db820458c1d4c9d3f5d077aa"),
    "T576": (RES / "agents_t576/out/T576_COLUMN_CAUSES.json",
             "7087c4efbeb3ad60ba4b4d3b8a19e42be2cc267729853820143de3988217b7fd"),
    "T572": (RES / "agents_t572/out/T572_HELD_BOUNDS.json",
             "a39e7b4b838e3590d6b456327823618e66b023617cb49be39821ad93ccb264f5"),
}
V = "VERIFIED_ON_RECORD"
C = "CLOSABLE_FROM_DRAWINGS"
DS = "DESIGNER_ITEM"
O = "OWNER_RULE_GAP"
STRUCT_SECTIONS = ("T-545/beams", "T-551/columns", "T-551/necks", "T-551/lift-walls", "T-551/footing-line",
                   "T-551/blinding", "T-560/rebar", "T-572/measured-columns_GF", "T-572/measured-columns_1F",
                   "T-572/measured-necks")
CHK_T545 = "Checker 2026-11-06 05:58 (T-545 Gate A): own B27 re-measure 4.1927 vs 4.1918 m3"
CHK_T551 = "Checker 2026-11-06 11:59 (T-551 Gate A): own hand F3 count, FN / F9 notch, lift ring double, C11 / C9"
CHK_T566 = "Checker 2026-11-06 13:55 (T-566 Gate A): own ezdxf read, exactly 4 'B2' labels on the 2F roof sheet"
CHK_T576 = ("Checker 2026-11-07 02:03 (T-576 Gate A): own GFRS count by drawn section, his GF rows C1 2 / C2 6 / C9 3 "
            "/ C11 1 vs drawn 1 / 4 / 2 / 2, COUNT -1.03125 m3 re-derived exactly")

# ---- the re-measure packs (CLOSABLE components point here; expected values from merged, committed sources) --------
PACKS = {
    "P01": {"title": "beam COUNT marks with no row of his, not yet re-measured (B27 is)",
            "sheets": ["ST p.4 GF roof slab plan", "ST p.5 1F roof slab plan", "ST p.10 simple-beam schedule",
                       "ST p.11 / p.12 continuous-beam schedules"],
            "measure": "per mark: drawn face-to-face length x schedule b x D; tag read on the plan; his workbook "
                       "beam sheet has no row of the mark",
            "expected_m3": {"GF B28": "0.2121", "GF CA": "0.1725", "1F B25": "2.8500", "1F B19": "1.6236",
                            "1F B5": "0.8325"},
            "closes": "T-545 GF / 1F COUNT to VERIFIED (GF 4.576422 = B27 4.1918 verified + 0.3846 here)"},
    "P02": {"title": "beam THROUGH_SUPPORT allowance per mark (his lengths through column / carrier footprints)",
            "sheets": ["ST p.4", "ST p.5", "ST p.6 2F roof slab plan", "ST p.9 column schedule"],
            "measure": "per split mark: every support the mark's pieces cross (column extent across the run, "
                       "carrier width at beam ends); his excess length inside the allowance; T-229 support input "
                       "is the engine side",
            "expected_m3": {"GF": "-2.901714 (V6; -3.022166 after T-576 adds GF B7 -0.120452)", "1F": "-1.593362",
                            "2F": "-0.420 (after the T-566 2F B2 re-class)"},
            "closes": "the length-convention RULE_DIFFERENCE quantity (the class itself is owner rule R-CONC-OWN-1)"},
    "P03": {"title": "RUN_COUNT: drawn runs of a mark beyond his rows (bound by length, heuristic)",
            "sheets": ["ST p.4 (GF B1)", "ST p.5 (1F B4 runs 3.812 / 4.100 / 4.300 m, B6)", "ST p.10 rows B1 / B4 / B6"],
            "measure": "count the labelled runs per mark and their lengths; compare his rows run by run (private "
                       "workbook, MARKS_T545.csv); 1F B4 vs the west ring B4 (0.20 x 0.50 both): a ring reading "
                       "moves at most 0.331 m3 between RUN_COUNT and DOME_RING, total unchanged",
            "expected_m3": {"GF B1": "-0.210119", "1F B4 + B6": "-1.908946"},
            "closes": "T-545 RUN_COUNT to VERIFIED"},
    "P04": {"title": "small beam terms named from the drawn runs (T-566)",
            "sheets": ["ST p.4 BAND0001 / BAND0003 / BAND0020.1-.2 (GF B11 / B8 / B2-B1 through column 36B)",
                       "ST p.5 BAND0004 / BAND0021 / BAND0018.1-.2 (1F B11 / B6 / CB12)",
                       "ST p.11 / p.12 CB12 printed spans 6.1 / 5.5"],
            "measure": "GF B2 run continuing collinearly through column 36B (gap 0.498) into the 0.803 m B1 piece; "
                       "1F CB12 outer-face extent 5.626 + 0.899 + 5.025 + 0.20 + 0.25 = 12.00 m vs his row",
            "expected_m3": {"GF B11": "-0.004050", "GF B8": "-0.003021", "GF B2": "+0.011152", "1F B11": "-0.007173",
                            "1F B6": "-0.000273", "1F CB12": "+0.160962"},
            "closes": "five DRAWING_PRECISION / MARK_BOUNDARY / BEYOND_EXTENT proposals (not re-measured by T-566)"},
    "P05": {"title": "GF B7 piece ends (T-576 allowance 3.55 m vs his excess 2.363 m)",
            "sheets": ["ST p.4 / ST7757 dxf: ring arcs handle 2EE / 2EF / 312 / 313, faces handle 437 / 46D / 42D / 2A9, "
                       "quarter arc BAND0049 (line handle 484, GF-112), BAND0006"],
            "measure": "the 12 piece ends the Checker did not re-read (2 / 14 AGREE on BAND0025.1): allowance per end "
                       "as the T-576 s.4 table; the sum must reach >= 2.363 m for UNTRACED 0",
            "expected_m3": {"GF B7 THROUGH_SUPPORT": "-0.354452 (incl. the V6 UNRESOLVED +0.120452)"},
            "closes": "the V6 GF B7 UNRESOLVED row; sensitivity: CB1 ring ends only (2.25 m) leaves 0.015 m3"},
    "P06": {"title": "stair beam upstands B20 / B23 0.20 x 0.20 x 3.00 (GF, 1F)",
            "sheets": ["ST p.4", "ST p.5", "ST p.16 stair beam detail"],
            "measure": "upstand drawn and its length per stair beam; no row of his",
            "expected_m3": {"GF": "-0.120", "1F": "-0.120"},
            "closes": "T-545 UPSTAND to VERIFIED"},
    "P07": {"title": "1F west dome ring B4 in bay (Q-44 A: the ring stays)",
            "sheets": ["ST p.5 west ring with the two B4 texts", "ST p.10 row B4 20 x 50", "ST p.7 DETAIL OF DOME"],
            "measure": "ring in-bay length 7.552 m x 0.20 x 0.50; his dome row is a 0.10 shell plate (T-398)",
            "expected_m3": {"1F DOME_RING": "-0.7552"},
            "closes": "T-545 DOME_RING to VERIFIED"},
    "P08": {"title": "column head split per member: A x D_ctrl (JOINT_HEAD) and A x (0.75 - D_ctrl) (GLOBAL_DEPTH)",
            "sheets": ["ST p.9 column schedule (sections)", "ST p.4 GF roof slab plan (framing beams)",
                       "ST p.5 1F roof slab plan", "ST p.10 / p.11 / p.12 beam depths"],
            "measure": "per measured-set member: the deepest framing beam's printed depth; the Checker confirmed the "
                       "head totals (GF A x 0.75 = 2.100 = 2.03375 + 0.06625; 1F 0.555 = his sum x 0.75 / 3.45) but "
                       "not the per-mark split",
            "expected_m3": {"GF JOINT_HEAD (T-551 all valued)": "-2.28125", "GF JOINT_HEAD (measured set, T-576)":
                            "-2.03375 incl. C7 at D_low 0.75", "GF GLOBAL_DEPTH (T-551 / measured)":
                            "-0.11875 / -0.06625", "1F JOINT_HEAD": "-0.385", "1F GLOBAL_DEPTH": "-0.095"},
            "closes": "JOINT_HEAD / GLOBAL_DEPTH per mark (members whose framing depth is unprinted stay DESIGNER)"},
    "P09": {"title": "GF column BASE drop (CB5-line columns from +0.25, T-287 G1)",
            "sheets": ["ST p.3 GROUND BEAMS PLAN (levels)", "ST p.13 ground-beam sections"],
            "measure": "base datum of the CB5-line columns (35F and its pair) vs +0.95",
            "expected_m3": {"GF BASE (T-551, 2 columns)": "-0.1925", "GF BASE (measured set, 35F)": "-0.105"},
            "closes": "BASE ENGINE_RIGHT (PLAUSIBLE in T-576, not re-measured)"},
    "P10": {"title": "1F C3 count",
            "sheets": ["ST p.5 1F roof slab plan (C3 outlines)", "ST p.9 column schedule row C3 1F"],
            "measure": "drawn 1F C3 outlines vs his rows: one more drawn C3, 0.20 x 0.50 x 3.45",
            "expected_m3": {"1F COUNT C3": "+0.345"},
            "closes": "T-551 1F COUNT C3"},
    "P11": {"title": "strap lengths SB2 / SB3",
            "sheets": ["ST p.2 foundation plan", "ST p.10 rows SB2 / SB3"],
            "measure": "drawn SB2 2.2927 m, SB3 3.2580 m between footing faces",
            "expected_m3": {"footing LENGTH": "+0.002"},
            "closes": "T-551 footing LENGTH"},
    "P12": {"title": "east dome ring side bars on both faces (F-C-T583-1), read this run",
            "sheets": ["ST p.7 DETAIL OF DOME, both ring sections (left and right)"],
            "measure": "the ring section draws side bars on BOTH vertical faces at two levels (2 + 2 dots), label "
                       "'2ø14/20cm' on a leader through both dots of one level; the tight low takes 4 d14 bars over "
                       "the in-bay length 8.9974 m: 4 x 8.9974 x 1.209877 = 43.543 kg",
            "expected_t": {"east ring row low": "0.122518 -> 0.144289", "bounded rows low": "0.767783 -> 0.789554",
                           "west row low": "0.063897 unchanged (B4 reading governs the low)"},
            "closes": "the side-bar part of the east ring row; ring depth, links high, hooks, laps stay DESIGNER"},
    "P13": {"title": "B1 excavation geometry not re-measured (plans only; the depth stays S01 ESTIMATED)",
            "sheets": ["ST p.2 foundation plan / ST7757 dxf layer S-FOOTINGS: the 16 pit footings other than handle "
                       "1B07 1ABF 1ADB 1B1A 1B2A 1B19 1B24 180F", "ST p.7 DETAIL OF SWIMMING POOL (pool envelope)",
                       "ST p.13 exterior ground-beam section (blinding cut 0.50 wide)"],
            "measure": "blinding plan = footing outline + 0.10 each side per pit (8 / 8 AGREE so far); pool envelope "
                       "plan; exterior GB blinding cut L 55.99 x 0.50 x 0.10 less pit run ends",
            "expected_m3": {"pits plan x 1.67": "208.164757 (124.649555 m2)", "pool envelope": "17.776576",
                            "ext GB trench": "1.069269 .. 1.176467"},
            "closes": "the plan side of B1-02; never VERIFIED while the founding level is S01 ESTIMATED"},
    "P14": {"title": "necks on his count against the drawn lower ends",
            "sheets": ["ST p.9 Schedule of Footings (depth H per type)", "ST p.9 column schedule FOUNDATION row",
                       "ST p.3 GROUND BEAMS PLAN (neck marks)"],
            "measure": "his 34 necks / 13 marks vs the his_n smallest drawn lower bounds h >= top + 1.33 - H "
                       "(the 36 lower ends are Checker-recomputed, 9.7239 m3); his workbook read in .work/private",
            "expected_m3": {"drawn lower on his count": ">= 8.8695 vs his 8.805 (8 of 13 marks below)"},
            "closes": "the BELOW_DRAWN_LOWER verdict proposal (his side not re-measured by the Checker)"},
}


def _c(cls, evidence, missing, **kw):
    d = {"closure_class": cls, "evidence": evidence, "missing": missing}
    d.update(kw)
    return d


# ---- per statement component: (section_id, name prefix) -> classification -------------------------------------
CAT = {
    ("T-545/beams", "GF: COUNT"): _c(C, CHK_T545 + "; his rows read (no B27 / B28 / CA row)",
        "B28 0.2121 and CA 0.1725 not re-measured", sheet_refs=PACKS["P01"]["sheets"], pack="P01"),
    ("T-545/beams", "GF: HELD"): _c(DS, "T-545 s.4: 6 held lines (B21, B29, CB2 x2, CB3, B24 ext.), his share inside "
        "the bound on 5, ABOVE on B24 by 0.000375 (F-T545-1)", "schedule vs drawn widths, double label",
        designer_refs=["D-27", "D-03", "RFI-S13", "RFI-S14"]),
    ("T-545/beams", "GF: THROUGH_SUPPORT"): _c(C, "worker class (T-545 R-T395-2 allowance per mark)",
        "allowance per mark not re-measured", sheet_refs=PACKS["P02"]["sheets"], pack="P02"),
    ("T-545/beams", "GF: RUN_COUNT"): _c(C, "worker class, run binding by length", "his rows vs drawn B1 runs",
        sheet_refs=PACKS["P03"]["sheets"], pack="P03"),
    ("T-545/beams", "GF: UNTRACED -> GF B11"): _c(C, "T-566 named DRAWING_PRECISION, not re-measured",
        "run length vs his row", sheet_refs=PACKS["P04"]["sheets"], pack="P04"),
    ("T-545/beams", "GF: UNTRACED -> GF B8"): _c(C, "T-566 named DRAWING_PRECISION, not re-measured",
        "run length vs his row", sheet_refs=PACKS["P04"]["sheets"], pack="P04"),
    ("T-545/beams", "GF: UNTRACED -> GF B2"): _c(C, "T-566 named MARK_BOUNDARY, not re-measured",
        "collinear B2 / B1 piece through column 36B", sheet_refs=PACKS["P04"]["sheets"], pack="P04"),
    ("T-545/beams", "GF: UNTRACED -> GF B7"): _c(C, "after V6: T-576 traced it to THROUGH_SUPPORT -0.354452 "
        "(Checker 02:03: 2 / 14 piece ends re-read AGREE)", "12 piece ends", sheet_refs=PACKS["P05"]["sheets"],
        pack="P05", restated_by="T-576 s.4 (UNRESOLVED 0.000 once the ends are confirmed)"),
    ("T-545/beams", "GF: UPSTAND"): _c(C, "T-189 drawn, worker class", "upstand length per stair beam",
        sheet_refs=PACKS["P06"]["sheets"], pack="P06"),
    ("T-545/beams", "1F: COUNT"): _c(C, "Checker 05:58 read his rows (no B25 / B19 / B5 row): class confirmed",
        "B25 2.8500, B19 1.6236, B5 0.8325 not re-measured", sheet_refs=PACKS["P01"]["sheets"], pack="P01"),
    ("T-545/beams", "1F: HELD"): _c(DS, "T-545 s.4: CB10 x2, B2 ext.", "CB10 width, B2 extension width",
        designer_refs=["D-02", "D-27", "RFI-S12", "RFI-S13"]),
    ("T-545/beams", "1F: THROUGH_SUPPORT"): _c(C, "worker class", "allowance per mark",
        sheet_refs=PACKS["P02"]["sheets"], pack="P02"),
    ("T-545/beams", "1F: RUN_COUNT"): _c(C, "worker class, run binding by length; B4 vs ring open (T-545 s.6)",
        "B4 / B6 rows vs runs", sheet_refs=PACKS["P03"]["sheets"], pack="P03"),
    ("T-545/beams", "1F: UNTRACED -> 1F B11"): _c(C, "T-566 DRAWING_PRECISION, not re-measured", "run vs row",
        sheet_refs=PACKS["P04"]["sheets"], pack="P04"),
    ("T-545/beams", "1F: UNTRACED -> 1F B6"): _c(C, "T-566 DRAWING_PRECISION, not re-measured", "run vs row",
        sheet_refs=PACKS["P04"]["sheets"], pack="P04"),
    ("T-545/beams", "1F: UNTRACED -> 1F CB12"): _c(C, "T-566 BEYOND_EXTENT, not re-measured", "CB12 extent 12.00 m",
        sheet_refs=PACKS["P04"]["sheets"], pack="P04"),
    ("T-545/beams", "1F: UPSTAND"): _c(C, "T-189 drawn, worker class", "upstand length",
        sheet_refs=PACKS["P06"]["sheets"], pack="P06"),
    ("T-545/beams", "1F: DOME_RING"): _c(C, "Q-44 A (owner: ring stays), worker class", "ring in-bay length",
        sheet_refs=PACKS["P07"]["sheets"], pack="P07"),
    ("T-545/beams", "2F: HELD"): _c(DS, "T-545 s.4: B15, B1 x2, B8 ext.", "B15 upstand / downstand, strip sections",
        designer_refs=["D-44", "D-05", "RFI-S22", "RFI-S16"]),
    ("T-545/beams", "2F: THROUGH_SUPPORT ->"): _c(V, "F-T570-4 re-class", "nothing", verified_by=CHK_T566),
    ("T-545/beams", "2F: THROUGH_SUPPORT"): _c(C, "worker class", "allowance per mark",
        sheet_refs=PACKS["P02"]["sheets"], pack="P02"),
    ("T-545/beams", "2F: UNTRACED -> 2F B2"): _c(V, "his fifth 2.5 m B2 row has no drawn run", "nothing",
        verified_by=CHK_T566),
    # columns (V6 T-551 rows; T-576 after V6)
    ("T-551/columns", "columns GF: COUNT C1"): _c(V, "T-576 own GF count", "nothing", verified_by=CHK_T576),
    ("T-551/columns", "columns GF: COUNT C2"): _c(V, "T-576 own GF count", "nothing", verified_by=CHK_T576),
    ("T-551/columns", "columns GF: COUNT C9"): _c(V, "T-551 + T-576 own counts", "nothing", verified_by=CHK_T576),
    ("T-551/columns", "columns GF: COUNT C3"): _c(DS, "T-566 CONFLICT 10AE (FP / CAP 'C3', GBP 'C')",
        "which mark the position carries", designer_refs=["D-63", "RFI-S20"]),
    ("T-551/columns", "columns GF: COUNT C11"): _c(V, "own hand T-551, own count T-576", "nothing",
        verified_by=CHK_T576),
    ("T-551/columns", "columns GF: HELD"): _c(DS, "4 printed-vs-drawn CONFLICT + 5 annex members",
        "column outline vs schedule; annex roof slab-top datum", designer_refs=["RFI-S20", "D-39", "RFI-S23", "D-06"]),
    ("T-551/columns", "columns GF: JOINT_HEAD"): _c(C, "class RULE_DIFFERENCE confirmed (T-551); head total "
        "confirmed (T-576 GF A x 0.75 = 2.100)", "per-mark D_ctrl split", sheet_refs=PACKS["P08"]["sheets"],
        pack="P08"),
    ("T-551/columns", "columns GF: BASE"): _c(C, "worker class; T-576 PLAUSIBLE", "base datum of 2 members",
        sheet_refs=PACKS["P09"]["sheets"], pack="P09"),
    ("T-551/columns", "columns GF: GLOBAL_DEPTH"): _c(C, "worker class; T-576 PLAUSIBLE", "per-mark D_ctrl",
        sheet_refs=PACKS["P08"]["sheets"], pack="P08"),
    ("T-551/columns", "columns GF: HEIGHT_OPEN"): _c(DS, "D_ctrl of GF C7 not settled (BM-GF-058 depth unprinted); "
        "T-576 splits it at the printed lower end 0.75, open below", "framing-beam depth",
        designer_refs=["D-04", "RFI-S15"]),
    ("T-551/columns", "columns 1F: COUNT C3"): _c(C, "worker class", "drawn 1F C3 outlines vs his rows",
        sheet_refs=PACKS["P10"]["sheets"], pack="P10"),
    ("T-551/columns", "columns 1F: COUNT C7"): _c(DS, "T-566 CONFLICT 10E0 (FP / CAP C8, GBP C7): reading of record, "
        "not a resolution", "which mark position 10E0 carries", designer_refs=["D-63", "RFI-S20"]),
    ("T-551/columns", "columns 1F: COUNT C8"): _c(DS, "10E0 CONFLICT; HELD drawn member beyond his count",
        "mark of 10E0", designer_refs=["D-16", "D-63", "RFI-S20"]),
    ("T-551/columns", "columns 1F: COUNT C9"): _c(DS, "two held outlines (667, 679) beyond his count",
        "outline vs schedule", designer_refs=["RFI-S20"]),
    ("T-551/columns", "columns 1F: HELD"): _c(DS, "11 printed-vs-drawn CONFLICT columns", "outline vs schedule",
        designer_refs=["RFI-S20", "D-16"]),
    ("T-551/columns", "columns 1F: JOINT_HEAD"): _c(C, "class confirmed; 1F head total = his sum x 0.75 / 3.45 "
        "confirmed (T-576)", "per-mark D_ctrl", sheet_refs=PACKS["P08"]["sheets"], pack="P08"),
    ("T-551/columns", "columns 1F: GLOBAL_DEPTH"): _c(C, "worker class", "per-mark D_ctrl",
        sheet_refs=PACKS["P08"]["sheets"], pack="P08"),
    ("T-551/columns", "columns 1F: HEIGHT_OPEN"): _c(DS, "D_ctrl not settled on 1F C3 68B, C8 664, P.C 20x50 "
        "(BM-1F-035 / -038 / -037 unprinted)", "framing-beam depths", designer_refs=["D-04", "D-05", "RFI-S15"]),
    ("T-551/columns", "columns 2F: HELD"): _c(DS, "9 2F columns on the roof datum", "main roof slab-top datum",
        designer_refs=["D-39", "RFI-S23", "D-44"]),
    ("T-551/necks", "necks: HELD"): _c(DS, "lower end 9.7239 m3 Checker-recomputed 36 / 36 (T-572); upper end open",
        "founding / formation depth (no printed maximum)", designer_refs=["RFI-S01", "S01"]),
    ("T-551/lift-walls", "lift pit walls: SCOPE_DOUBLE"): _c(V, "four lift column pieces owned by the necks",
        "nothing", verified_by=CHK_T551),
    ("T-551/lift-walls", "lift pit walls: HELD"): _c(DS, "net ring 1.10 m2 drawn; depth 'as per lift manufacturer'",
        "pit depth", designer_refs=["D-43", "RFI-S21"]),
    ("T-551/footing-line", "footing line: COUNT F3"): _c(V, "two drawn outlines tagged F3", "nothing",
        verified_by=CHK_T551),
    ("T-551/footing-line", "footing line: HELD F10 + F"): _c(DS, "S02 ESTIMATED; owner 2026-11-02 range 1.960 .. "
        "2.275 PROVISIONAL (F-T589-1: the statement prints 2.176 .. 2.275)", "the 0.70 m open outline",
        designer_refs=["RFI-S02", "S02"]),
    ("T-551/footing-line", "footing line: HELD boundary band"): _c(DS, "drawn range 5.639 .. 11.033 (T-065 / T-233)",
        "pad count / spacing and band section", designer_refs=["RFI-S03", "RFI-S04"]),
    ("T-551/footing-line", "footing line: OVERLAP FN"): _c(V, "F9 owns the notch", "nothing", verified_by=CHK_T551),
    ("T-551/footing-line", "footing line: LENGTH SB2"): _c(C, "worker class", "two strap lengths",
        sheet_refs=PACKS["P11"]["sheets"], pack="P11"),
    ("T-551/blinding", "blinding: his one 0.10 plate"): _c(DS, "24 pits VERIFIED (T-478); his plate no sheet draws "
        "(RULE_DIFFERENCE 24.837 .. 26.680)", "held blinding elements 7.640 .. 9.484 (FF raft, F10 + F, straps)",
        designer_refs=["RFI-S06", "RFI-S07", "RFI-S08", "D-14", "D-15"]),
    # rebar (t)
    ("T-560/rebar", "G1_SUBSTRUCTURE"): _c(DS, "TYPED_LUMP CONFIRMED (T-560): comparison NOT_COMPARABLE forever; "
        "engine 196 held blank lines", "bar ends / links of ground beams, straps, footings; starters; laps",
        designer_refs=["RFI-B-S09", "RFI-B-S30", "RFI-B-S31", "RFI-B-S32"]),
    ("T-560/rebar", "G2_COLUMNS_NECKS_WALLS"): _c(DS, "238 held blank lines; lift-wall rebar ENGINE_OMISSION "
        "(T-569 fix row)", "column head / section change, starters, laps, lift-wall height",
        designer_refs=["RFI-B-S29", "RFI-B-S31", "RFI-B-S32", "D-43"]),
    ("T-560/rebar", "G3_BEAMS"): _c(DS, "128 held blank lines", "beam bar ends, anchorage, link closure, side bars",
        designer_refs=["RFI-B-S21", "RFI-B-S19", "RFI-B-S20", "RFI-B-S14"]),
    ("T-560/rebar", "G4_SLABS"): _c(DS, "199 held blank lines", "top bars over supports, bar-less panels, sunken "
        "panel drops", designer_refs=["RFI-B-S10", "RFI-B-S13", "D-51"]),
    ("T-560/rebar", "G5_STAIRS_DOME"): _c(DS, "17 held blank lines; dome rebar ENGINE_OMISSION (T-569 fix row)",
        "stair beam crank, dome ring depth, DOME-3", designer_refs=["RFI-B-S22", "D-28", "D-21", "RFI-S28"]),
    ("T-560/rebar", "G6_POOL"): _c(DS, "20 held blank lines", "pool floor bar population",
        designer_refs=["RFI-B-S11"]),
    # T-572 measured sets (V6 section sign reference - engine as printed there)
    ("T-572/measured-columns_GF", "columns_GF: COUNT"): _c(V, "own GF count", "nothing", verified_by=CHK_T576),
    ("T-572/measured-columns_GF", "columns_GF: JOINT_HEAD"): _c(C, "head total confirmed; T-576 restates GF "
        "JOINT_HEAD 2.03375 = this 1.88375 + C7 0.150 at D_low", "per-mark D_ctrl",
        sheet_refs=PACKS["P08"]["sheets"], pack="P08"),
    ("T-572/measured-columns_GF", "columns_GF: GLOBAL_DEPTH"): _c(C, "T-576 PLAUSIBLE", "per-mark D_ctrl",
        sheet_refs=PACKS["P08"]["sheets"], pack="P08"),
    ("T-572/measured-columns_GF", "columns_GF: BASE"): _c(C, "T-576 PLAUSIBLE", "35F base datum",
        sheet_refs=PACKS["P09"]["sheets"], pack="P09"),
    ("T-572/measured-columns_GF", "columns_GF: HEIGHT_OPEN"): _c(DS, "C7 split at D_low 0.75 (T-576), open below",
        "BM-GF-058 depth", designer_refs=["D-04", "RFI-S15"]),
    ("T-572/measured-columns_1F", "columns_1F: JOINT_HEAD"): _c(C, "1F total confirmed (T-576)", "per-mark split",
        sheet_refs=PACKS["P08"]["sheets"], pack="P08"),
    ("T-572/measured-columns_1F", "columns_1F: GLOBAL_DEPTH"): _c(C, "worker class", "per-mark D_ctrl",
        sheet_refs=PACKS["P08"]["sheets"], pack="P08"),
    ("T-572/measured-columns_1F", "columns_1F: HEIGHT_OPEN"): _c(DS, "P.C 20x50 at D_low 0.75 (T-576), open below",
        "BM-1F-035 / -038 depth", designer_refs=["D-05", "RFI-S16"]),
}

# ---- B1 earthworks (T-572 components, engine side; freelancer NO_ROW: NOT_COMPARABLE) -------------------------
B1_CAT = {
    "EW-T350:B1-02:Z1-TRENCH-EXT-GB-MAIN": _c(C, "both ends drawn (T-572)", "L 55.99 cut not re-measured",
        sheet_refs=PACKS["P13"]["sheets"], pack="P13"),
    "EW-T350:B1-02:Z1-LOWER-GB-ROW": _c(DS, "0 at the printed minimum founding", "founding level",
        designer_refs=["RFI-S01", "RFI-S11"]),
    "EW-T350:B1-02:Z1-TRENCH-BOUNDARY": _c(DS, "Q-28 A provisional", "boundary-wall foundation depth",
        designer_refs=["RFI-S03", "RFI-S04"]),
    "EW-T350:B1-02:Z1-TRENCH-ANNEX": _c(DS, "no annex GB section", "annex interior / exterior GB sections",
        designer_refs=["D-33", "D-34", "D-35", "RFI-S09"]),
    "EW-T350:B1-02:Z1-TRENCH-INT-GB-MAIN-ZERO": _c(DS, "13 runs above EG while b_wet <= 0.30", "wet floor build-up",
        designer_refs=["D-40"]),
    "EW-T350:B1-02:Z1-TRENCH-STRAPS": _c(DS, "footprint 7.889 m2 drawn, depth not", "strap soffit",
        designer_refs=["D-15", "RFI-S07"]),
    "EW-T350:B1-02:Z1-PIT-FF": _c(DS, "plan 20.700 m2 DRAWING-CONFIRMED; NOTE1_ON_LIFT_RAFT accepted", "pit depth",
        designer_refs=["D-43", "RFI-S08"]),
    "EW-T350:B1-02:Z1-TRENCH-INT-GB-MAIN-D33": _c(DS, "loaded GB sections not printed", "section",
        designer_refs=["D-33", "RFI-S10"]),
    "EW-T350:B1-02:Z1-PIT-F10F": _c(DS, "lower end 4.350 m2 x 1.50", "F10 + F outline; formation",
        designer_refs=["RFI-S02", "RFI-S01"]),
    "EW-T350:B1-02:Z1-TRENCH-COURT": _c(DS, "no court ground-beam section printed (T-350); F-T589-2: not named on "
        "the RFI list, nearest RFI-S09", "court GB section", designer_refs=["RFI-S09"]),
    "EW-T350:B1-03:Z1-PIT-FF": _c(DS, "as its excavation", "pit depth", designer_refs=["D-43"]),
    "EW-T350:B1-03:Z1-TRENCH-EXT-GB-MAIN": _c(O, "neat cut filled by the blinding, calculated 0.000 (T-350 r2); "
        "WORKING_SPACE_EXCLUDED", "the high end needs a working-space / over-dig rule",
        rule_gap="owner earthworks rules 2026-11-02 17:45 (2): backfill = excavation zone minus permanent volumes; "
                 "no Urban working-space allowance; ERS s.2.7 not met (no owner question)"),
    "EW-T350:B1-03:Z1-OTHER-TRENCHES": _c(DS, "as their excavation zones", "GB sections / depths",
        designer_refs=["D-33", "D-34", "D-35", "D-15", "RFI-S03"]),
    "EW-T350:B1-03:Z1-POOL": _c(O, "neat envelope part calculated 0.000 (T-350 r2)", "working space / blinding high",
        rule_gap="same working-space gap as the exterior GB backfill; ERS s.2.7 not met"),
    "EW-T350:B1-03:Z1-PITS-24": _c(DS, "lower end 99.645011 re-added by the Checker (T-572)",
        "upper end rises with the founding depth", designer_refs=["RFI-S01", "S01"]),
    "EW-T350:B1-03:Z1-PIT-F10F": _c(DS, "Q-31 C outline", "outline, C10 / C necks, formation",
        designer_refs=["RFI-S02", "RFI-S01"]),
    "EW-T350:B1-03:Z2": _c(DS, "Z2 extent", "wet-floor build-up, GB sections", designer_refs=["D-40", "D-33", "D-34"]),
    "EW-T350:B1-04:ALL": _c(O, "excavation and backfill held; densities not sourced", "in-situ / compacted dry "
        "densities with their source",
        rule_gap="owner 2026-11-02 18:00 (3): procurement uses the documented PLACEMENT TARGET density with its "
                 "source; no sourced density exists; ERS s.2.7 not met (the owner already ruled the method)"),
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_sources() -> dict:
    out = {}
    for k, (p, h) in SOURCES.items():
        if sha(p) != h:
            raise R.ClassError(f"{k}: {p.name} sha256 changed: rebuild T-589 on the new source")
        out[k] = json.loads(p.read_text(encoding="utf-8"))
    return out


def statement_components(v6: dict) -> list[dict]:
    secs = {s["section_id"]: s for key in ("sections", "sections_v5") for s in v6[key]}
    comps, used = [], set()
    for sid in STRUCT_SECTIONS:
        s = secs[sid]
        unit = s["unit"]
        if sid == "T-572/measured-necks":
            comps.append(dict(_c(C, s["verdict_proposal"], "his side vs the drawn lower ends on his count",
                                 sheet_refs=PACKS["P14"]["sheets"], pack="P14"),
                              id="T-572/measured-necks", section="B10", source=sid,
                              quantity={"unit": "m3", "basis": "ENGINE_HELD", "low": s["engine"]["at_least"],
                                        "high": None, "held_item": "upper end on the founding depth (RFI-S01)"},
                              reference_m3=s["reference_total"]))
            continue
        for row in s["rows"]:
            keys = [k for k in CAT if k[0] == sid and row["name"].startswith(k[1])]
            keys = sorted(keys, key=lambda k: -len(k[1]))[:1]
            if not keys:
                raise R.ClassError(f"{sid} / {row['name']}: not classified")
            k = keys[0]
            if (k, row["name"]) in used:
                raise R.ClassError(f"{row['name']}: classified twice")
            used.add((k, row["name"]))
            comps.append(dict(CAT[k], id=f"{sid}::{row['name']}", section=("B11" if unit == "t" else "B10"),
                              source=sid, statement_class=row["class"],
                              quantity={"unit": unit, "basis": "DIFFERENCE", "value": row["delta"],
                                        "sign": "reference - engine"}))
    for sid in STRUCT_SECTIONS:  # every statement section re-adds exactly from its classified components
        diff = secs[sid].get("difference")
        if diff is None or not isinstance(secs[sid].get("rows"), list):
            continue
        got = sum(D(c["quantity"]["value"]) for c in comps if c["source"] == sid)
        if got != D(diff):
            raise R.ClassError(f"{sid}: components re-add to {got}, statement prints {diff}")
    unused = set(CAT) - {k for k, _ in used}
    if unused:
        raise R.ClassError(f"catalogue keys matching no component: {sorted(unused)}")
    return comps


def b11_after_v6(t583: dict) -> list[dict]:
    """T-583 rows (after V6) + the F-C-T583-1 restatement of the east ring side bars (own read ST p.7)."""
    rows = {r["row_id"]: r for r in t583["rows"]}
    east = rows["HL:DOME_RING:DOME-1F-E:RING:RING_BEAM_IN_BAY:REBAR"]
    det = east["readings"][0]
    side = [g for g in det["groups"] if g["group"] == "RING_SIDE[DETAIL]"][0]
    add_kg = D(str(side["kg_low"]))  # 2 more d14 bars over the same in-bay length (the other face)
    add_t = (add_kg / 1000).quantize(D("0.000001"))
    east_low_new = (D(str(east["t_low"])) + add_t).quantize(D("0.000001"))
    total_low_new = (D(str(t583["totals"]["t_low"])) + add_t).quantize(D("0.000001"))
    restate = {"finding": "F-C-T583-1", "sheet": "ST p.7 DETAIL OF DOME (both ring sections)",
               "drawn": "side bars on both vertical faces, two levels: 4 d14 (2 per face); label 2ø14/20cm",
               "side_bars_kg_low": [str(D(str(side["kg_low"])).quantize(D("0.001"))),
                                    str((2 * D(str(side["kg_low"]))).quantize(D("0.001")))],
               "east_row_low_t": [str(east["t_low"]), str(east_low_new)],
               "bounded_rows_low_t": [str(t583["totals"]["t_low"]), str(total_low_new)],
               "west_row_low_t": "0.063897 unchanged (B4 reading 0.063897 < detail reading 0.103011 + 0.018275)",
               "status": "PROPOSED (worker own read); Checker to confirm on p.7"}
    m = lambda lo, item: {"unit": "t", "basis": "ENGINE_HELD", "low": lo, "high": None, "held_item": item}  # noqa
    comps = [
        dict(_c(DS, "no structural drawing of the third dome", "the dome itself", designer_refs=["D-21", "RFI-S28"]),
             id="T-583::DOME-3 shell", section="B11", source="T-583",
             quantity={"unit": "t", "basis": "ENGINE_HELD", "low": None, "high": None,
                       "held_item": "no structural drawing (D-21)"}),
        dict(_c(C, "T-583 low 2 bars on one face; p.7 draws both faces (own read this run)",
                "Checker confirmation of the 4-bar reading", sheet_refs=PACKS["P12"]["sheets"], pack="P12"),
             id="T-583::east ring side bars (second face)", section="B11", source="T-583 + F-C-T583-1",
             quantity={"unit": "t", "basis": "ENGINE_HELD", "low": str(add_t), "high": None,
                       "held_item": "further rows over the unprinted ring depth"}),
        dict(_c(DS, "mains / links low bounded (Checker AGREE 04:05)", "ring depth (link path, side-bar rows), hooks, "
                "laps / anchorage", designer_refs=["D-28", "RFI-S17", "RFI-B-S21", "RFI-B-S32"]),
             id="T-583::east ring (remainder)", section="B11", source="T-583",
             quantity=m(str(east["t_low"]), "ring depth, hooks, laps (D-28)")),
        dict(_c(DS, "B4 vs DETAIL conflicting sources; low = B4 reading (Checker AGREE)", "ring depth, which source "
                "governs, hooks, laps", designer_refs=["D-20", "RFI-B-S21", "RFI-B-S32"]),
             id="T-583::west ring", section="B11", source="T-583",
             quantity=m(str(rows["HL:DOME_RING:DOME-1F-W:RING:RING_BEAM_B4_IN_BAY:REBAR"]["t_low"]),
                        "ring depth, hooks, laps")),
        dict(_c(DS, "shell mains low 0.287994 + anchorage 0.002690 (Checker AGREE)", "anchorage high (ring depth), "
                "hoop lap length (>= 24 joints, length not printed)", designer_refs=["RFI-B-S32", "D-20"]),
             id="T-583::DOME-A shell", section="B11", source="T-583",
             quantity=m(str(rows["HL:DOME_SHELL:DOME-A:SHELL:REBAR"]["t_low"]), "anchorage, hoop laps")),
        dict(_c(DS, "as DOME-A", "as DOME-A", designer_refs=["RFI-B-S32", "D-20"]),
             id="T-583::DOME-B shell", section="B11", source="T-583",
             quantity=m(str(rows["HL:DOME_SHELL:DOME-B:SHELL:REBAR"]["t_low"]), "anchorage, hoop laps")),
        dict(_c(DS, "A 0.156642 .. 0.212859 t/m, B 0 .. 0.123221 t VERIFIED lows (Checker 04:05)", "wall height h; "
                "starter anchorage F-T583-1", designer_refs=["D-43", "RFI-B-S14", "RFI-B-S21"]),
             id="T-583::lift-pit walls kg(h)", section="B11", source="T-583",
             quantity={"unit": "t", "basis": "ENGINE_HELD", "low": None, "high": None,
                       "held_item": "kg(h) = A h + B, h not printed (D-43)"}),
    ]
    return comps, restate


def b1_components(t572: dict, v6: dict) -> list[dict]:
    comps = []
    for x in t572["components"]:
        if not x["family"].startswith("B1-"):
            continue
        if x["element_id"] not in B1_CAT:
            raise R.ClassError(f"{x['element_id']}: not classified")
        qt = {"unit": "m3", "basis": "ENGINE_HELD", "low": x["low"], "high": x["high"],
              "held_item": x["low_item"] or x["high_item"] or "upper end open"}
        comps.append(dict(B1_CAT[x["element_id"]], id=x["element_id"], section="B1", source="T-572",
                          kind=x["kind"], quantity=qt))
    if {c["id"] for c in comps} != set(B1_CAT):
        raise R.ClassError("B1 catalogue and T-572 components differ")
    fam = [f for f in v6["sections_v5"] if f["section_id"] == "T-572/held-bounds"][0]["families"]
    exc = [f for f in fam if f["family"] == "B1-02 EXCAVATION"][0]
    R.check_split(exc["engine_valued"], ["208.164757", "17.776576"])
    comps.append(dict(_c(DS, "T-565 Checker: 8 / 24 pit footprints re-measured AGREE, depth chain S01 ESTIMATED "
                            "(never VERIFIED while the founding level is estimated)",
                         "founding level (designer); plan of 16 pits + pool envelope also closable (P13)",
                         designer_refs=["RFI-S01", "S01"], also_closable="P13"),
                      id="B1-02 valued excavation (pits 208.164757 + pool envelope 17.776576)", section="B1",
                      source="T-572 / T-565", quantity={"unit": "m3", "basis": "ENGINE_VALUED",
                                                        "value": exc["engine_valued"]}))
    return comps


def findings(src: dict) -> list[dict]:
    t572 = src["T572"]
    f10 = [x for x in t572["components"] if x["family"] == "B10 FOOTING LINE" and x["low"] is not None
           and D(x["low"]) == D("2.176")]
    low_now = f10[0]["low"] if f10 else None
    return [
        {"id": "F-T589-1", "what": "F10 + F footing (held line L-164ae9d3): the statement and T-572 carry the S02 "
         "bound 2.176 .. 2.275 m3, but the owner (2026-11-02, condition 4, accepted) set the S02 range to 1.960 .. "
         "2.275 m3 (F10 alone 2.80 x 1.40 x 0.50 = 1.960 / F10 + F 2.176 / drawn outline 2.275), one scenario carried "
         "consistently", "quantity": f"low {low_now} -> 1.960 m3 (-0.216); T-572 footing-line bounded part "
         "7.8445 -> 7.6285 m3 low; his 1.960 moves from BELOW to AT the low", "action": "Lead: a lane S fix row "
         "(T-572 bound / statement class); no line changes (the line is HELD)", "owner_question": "none (owner "
         "already ruled)"},
        {"id": "F-T589-2", "what": "the court ground-beam excavation zone (no court GB section printed, T-350) has no "
         "RFI of its own; RFI-S09 (exterior GB depth, main house and annex) is the nearest", "quantity": "zone "
         "UNBOUNDED, m3 HELD", "action": "Lead: add the court GB section to the RFI list (designer, not owner)",
         "owner_question": "none"},
        {"id": "F-C-T583-1 (closed from the drawing, proposed)", "what": "ST p.7 draws the dome-ring side bars on "
         "both faces (2 + 2)", "quantity": "east ring low +0.021771 t (0.122518 -> 0.144289); bounded rows low "
         "0.767783 -> 0.789554 t", "action": "Checker confirm on p.7; lane S updates the T-583 row (method version "
         "or next ring row, not in place)", "owner_question": "none"},
    ]


def build() -> dict:
    src = load_sources()
    b10b11 = statement_components(src["V6"])
    b11x, restate = b11_after_v6(src["T583"])
    b1 = b1_components(src["T572"], src["V6"])
    comps = b10b11 + b11x + b1
    for c in comps:
        R.check_component(c)
    tables = {}
    for sec, unit in (("B10", "m3"), ("B11", "t"), ("B1", "m3")):
        cs = [c for c in comps if c["section"] == sec]
        for c in cs:
            R.check_component(c, unit)
        whole = R.section_table(sec, unit, cs)
        # quantities are added only inside one source section: the T-572 measured sets re-cut the T-551 columns
        # and the T-583 rows sit inside the T-560 G2 / G5 groups, so a cross-source sum would count members twice
        by_src = {s: R.section_table(f"{sec}:{s}", unit, [c for c in cs if c["source"] == s])
                  for s in sorted({c["source"] for c in cs})}
        tables[sec] = {"section": sec, "unit": unit, "n": whole["n"],
                       "n_by_class": {k: v["n"] for k, v in whole["by_class"].items()},
                       "quantity_added_across_sources": False, "by_source": by_src}
    packs_used = sorted({c.get("pack") for c in comps if c.get("pack")} |
                        {c.get("also_closable") for c in comps if c.get("also_closable")})
    if set(packs_used) != set(PACKS):
        raise R.ClassError(f"packs defined vs used differ: {sorted(set(PACKS) ^ set(packs_used))}")
    return {
        "schema": "URBAN_T589_CLOSABLE_PACK_V1",
        "rule": "R-T589-1 (t589_rules.py, proposed, every villa)",
        "candidate": "ARCH_TAKEOFF_V3.0.58 (NOT RELEASED); released default V2.9 + route G unchanged; no quantity moves",
        "sources_sha256": {k: v[1] for k, v in SOURCES.items()},
        "drawing_refs": "Drive 'Alsenan chalet project' / 'ST7757.pdf' sha256 74da1523 (p.7 re-read this run), "
                        "'ST7757 dxf.dxf' sha256 9f9d1179 (handles by reference)",
        "tables": tables,
        "components": comps,
        "packs": PACKS,
        "restatement_F_C_T583_1": restate,
        "findings": findings(src),
        "owner_questions": "none: every DESIGNER item is on the designer / RFI lists; the OWNER_RULE_GAP rows are "
                           "already governed by owner rulings (ERS s.2.7 not met)",
    }


def to_markdown(st: dict) -> str:
    L = ["# T-589 structural closable-component pack (generated by t589_alsenan.py; do not edit)", ""]
    for sec, t in st["tables"].items():
        L.append(f"## {sec} ({t['unit']}): n = {t['n']}, " + ", ".join(f"{k} {v}" for k, v in t["n_by_class"].items()))
        L.append("")
        L.append("Quantities per source section only (never added across sources: overlapping member sets).")
        L.append("")
        L.append("| Source | Class | n | quantity (unit / basis: sum, gross abs, or held low .. high) |")
        L.append("|---|---|---|---|")
        for s, tt in t["by_source"].items():
            for cl, row in tt["by_class"].items():
                if not row["n"]:
                    continue
                qs = "; ".join(f"{k}: " + ", ".join(f"{kk} {vv}" for kk, vv in v.items() if kk != "n")
                               for k, v in row["quantity"].items())
                L.append(f"| {s} | {cl} | {row['n']} | {qs} |")
        L.append("")
    L += ["## Components", "", "| id | class | quantity | missing for VERIFIED | refs |", "|---|---|---|---|---|"]
    for c in st["components"]:
        qt = c["quantity"]
        qv = qt.get("value") if "value" in qt else f"{qt.get('low')} .. {qt.get('high') or 'HELD'}"
        refs = c.get("pack") or ", ".join(c.get("designer_refs", [])) or c.get("verified_by", "")[:40] or \
            c.get("rule_gap", "")[:40]
        L.append(f"| {c['id']} | {c['closure_class']} | {qv} {qt['unit']} | {c['missing']} | {refs} |")
    L += ["", "## Re-measure packs", ""]
    for k, p in st["packs"].items():
        L.append(f"- **{k}** {p['title']}: sheets {'; '.join(p['sheets'])}. Expected: "
                 + ", ".join(f"{a} {b}" for a, b in (p.get('expected_m3') or p.get('expected_t')).items()))
    L += ["", "## Findings", ""]
    for f in st["findings"]:
        L.append(f"- **{f['id']}**: {f['what']}. {f['quantity']}. {f['action']}.")
    L.append("")
    return "\n".join(L)


def main(argv: list[str]) -> int:
    st = build()
    js = json.dumps(st, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    md = to_markdown(st)
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(js, encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
        return 0
    if "--check" in argv:
        ok = JSON_OUT.read_text(encoding="utf-8") == js and MD_OUT.read_text(encoding="utf-8") == md
        print("T-589 rebuild", "IDENTICAL" if ok else "DIFFERS")
        return 0 if ok else 1
    for sec, t in st["tables"].items():
        print(sec, t["n"], t["n_by_class"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
