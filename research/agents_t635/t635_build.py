"""T-635: the reconciled-quantities statement V12 = the T-620 statement V11 (rebuilt read only and checked equal to its
committed JSON and markdown, sha256 pinned as the T-620 scorecard reads it; every V11 key carried byte-equal, lists
extended as a prefix) + EVIDENCE FOLDS of the row-evidence tasks MERGED after V11 and a BESIDE register of the other
merged work (no statement section of its own):

  folds (UNKNOWN rows -> evidence per row; classes, deltas and totals unchanged):
    T-622 B4 wall tile (T-547/wall-tile), T-623 B10 beams / columns (T-545/beams@V11, T-551/columns@V10),
    T-625 B3 floor tile row 0 + open plan (T-553/floor-tile@V11), T-626 B8 waterproofing (T-546/floor, T-541/membrane),
    T-627 B12 opening m2 (T-568/windows-m2, T-568/alu-doors-m2), T-628 B10 footing / lift walls (T-551/footing-line,
    T-551/lift-walls), T-633 B9 blockwork (T-543/blockwork), T-634 B5 / B6 internal plaster / paint
    (T-552/plaster-internal, T-561/paint-internal);
  beside (named, nothing folded): T-624, T-632, T-638 .. T-647, T-649 (trial BOQ r2); T-648 REJECTED: refused.

No private input (committed JSON and quoted Checker verdicts only); no quantity moves; no class moves; nothing released
(ARCH_TAKEOFF_V3.0.59 NOT RELEASED; V2.9 + route G unchanged). Sign as the statement: reference - engine.

R-T635-1 (proposed, every villa: the evidence-fold method):
  (a) BIND BEFORE STAMP: a worker evidence row binds to a statement row only by its own index AND name AND class AND
      delta (Decimal equal); any mismatch refuses the whole fold (a stamp is never carried onto another row);
  (b) STATUS FROM THE STRONGEST ACCEPTED SOURCE: CHECKER_VERIFIED only where the Checker's Gate A text names its own
      re-measure of that row's element (quoted, with its board time and merge) AND the re-measured value equals the
      row's delta at the row's printed precision; a Checker re-measure that differs from the row (a fix row, a split
      correction) or covers only a component (width not height, plan not depth, class not length) is
      PARTIALLY_VERIFIED with the difference named; DRAWING_CONFIRMED where the worker's own drawing re-measure says so
      (status accepted at Gate A, quantity not re-measured by the Checker); REPRODUCED arithmetic, CITED sources,
      owner-rule quantities (ASSUMED-OWNER-APPROVED), DIFFERS and RE-MEASURED-IN-PARTS stay UNKNOWN with the reason
      as an annotation: never promoted;
  (c) NEVER LOWER: a row already stamped higher (CHECKER_VERIFIED > PARTIALLY_VERIFIED > DRAWING_CONFIRMED) keeps its
      stamp; a fold that would lower it is refused;
  (d) CLASS PROPOSALS BESIDE: a class the worker or the Checker proposes that differs from the statement class
      (F-T623-1, F-T627-1, T-622 GF-14, T-633 D-GF-06 ...) is listed beside the section with its source, never applied by
      the statement fold (a class move is its own reviewed fold);
  (e) HELD UNTOUCHED: a HELD row keeps class, delta and bound; a fold never stamps it and never writes 0;
  (f) EXACT RE-ADD and V11 BYTE-EQUAL as R-T620-1 (b) (e).

  python3 -I research/agents_t635/t635_build.py --write   # write out/
  python3 -I research/agents_t635/t635_build.py --check   # rebuild and compare with out/ (exit 1 on a difference)
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T620 = ROOT / "research/agents_t620"
if str(T620) not in sys.path:
    sys.path.insert(0, str(T620))
import t620_build as B620  # noqa: E402  (T-620, read only)

Z = B620.Z
D = Decimal
StatementError = B620.StatementError

OUT = HERE / "out"
JSON_OUT = OUT / "RECONCILED_STATEMENT_T635.json"
MD_OUT = OUT / "RECONCILED_STATEMENT_T635.md"
V11_SHA256 = "db5f7bceb8b6b44b1d9f87c40e83022cdd1123789e4e3be81fe43e9bad298e69"   # = T-620 scorecard pin of V11

SRC = {
    "T-622": ROOT / "research/agents_t622/out/WALL_TILE_REMEASURE_T622.json",
    "T-623": ROOT / "research/agents_t623/out/T623_UNKNOWN_ROWS.json",
    "T-625": ROOT / "research/agents_t625/out/T625_EVIDENCE.json",
    "T-626": ROOT / "research/agents_t626/out/T626_ROW_EVIDENCE.json",
    "T-627": ROOT / "research/agents_t627/out/T627_ROW_EVIDENCE.json",
    "T-628": ROOT / "research/agents_t628/out/T628_FOOTING_LIFT_ROWS.json",
    "T-633": ROOT / "research/agents_t633/out/T633_ROW_EVIDENCE.json",
    "T-634": ROOT / "research/agents_t634/out/T634_PLASTER_PAINT_REMEASURE.json",
}
# (a) the merged register: task -> engine merge / push commit and the Checker Gate A time (BOARD.md, agents/control)
MERGED = {
    "T-622": ("31fe39db", "Verifier 2026-11-08T10:00Z, MERGED (Gate A PASS a-h)"),
    "T-623": ("2d840524", "Verifier 2026-11-08T09:59Z, MERGED (Gate A PASS a-h; engine push 31fe39db)"),
    "T-625": ("47824e04", "Verifier 2026-11-08T12:59Z, MERGED (Gate A PASS)"),
    "T-626": ("74e52c34", "Verifier 2026-11-08T13:59Z, MERGED (Gate A PASS)"),
    "T-627": ("a7ee000d", "Verifier 2026-11-08T15:57Z, MERGED (Gate A PASS)"),
    "T-628": ("a7ee000d", "Verifier 2026-11-08T15:55Z, MERGED (Gate A PASS; head 14f53dcc)"),
    "T-633": ("2f103248", "Verifier 2026-11-09T03:58Z, MERGED (Gate A PASS)"),
    "T-634": ("52230429", "Verifier 2026-11-08T19:59Z, MERGED (Gate A PASS)"),
}
# beside only: merged work with no statement section of its own (candidate HELD-line censuses, manifests, trial BOQ)
BESIDE = {
    "T-624": ("1e38add2", "Verifier 2026-11-08T11:58Z", "research/agents_t624/out/T624_BEAM_END_OPEN_ITEMS.json",
              "beam-end open items: fix rows FR-T624-1 .. -3 (+0.009714 m3, research, unwired); beside T-545/beams@V12"),
    "T-632": ("e90e0f4d", "Verifier 2026-11-08T13:57Z", "research/agents_t632/out/T632_UPSTAND_CENSUS.json",
              "beam upstand extent census (GF B20 / 1F BAND0013): beside T-545/beams@V12 rows GF / 1F UPSTAND"),
    "T-638": ("175443b8", "Verifier 2026-11-08T18:05Z", "research/agents_t638/out/FORMWORK_HOLD_CENSUS_T638.json",
              "B10-13 formwork 370 HELD-blank candidate lines to a quantity or a named cause (no statement section)"),
    "T-639": ("e31e38b5", "Verifier 2026-11-08T19:59Z", "research/agents_t639/out/REBAR_HOLD_CENSUS_T639.json",
              "B11-01 rebar 801 HELD-blank + 6 OPEN-high lines to a named cause (beside T-560/rebar@V9; its 799 / 798 "
              "HELD-blank count of record is unchanged here)"),
    "T-640": ("36f53264", "Verifier 2026-11-08T17:04Z", "research/agents_t640/out/HOLD_CENSUS_T640.json",
              "B4 + B5 wall / ceiling finish HELD-blank lines to a quantity or a named cause"),
    "T-641": ("57620ab8", "Verifier 2026-11-08T21:56Z", "research/agents_t641/out/WIRING_MANIFEST_V17.json",
              "wiring manifest V17 (overlay dry run; non-candidate)"),
    "T-642": ("1c7411a5", "Verifier 2026-11-08T21:54Z", "research/agents_t642/out/T642_FIX_ROWS.json",
              "Checker T-180 fix rows P02 / P04 + B10-12 parapet 4 HELD-blank"),
    "T-643": ("f136248f", "Verifier 2026-11-09T00:05Z", "research/agents_t643/out/REBAR_ON_HELD_CONCRETE_T643.json",
              "B11 rebar on HELD concrete + 208 unbound lines (4 validated downgrades)"),
    "T-644": ("cc7f9a48", "Verifier 2026-11-08T22:04Z", "research/agents_t644/out/T644_LINTEL_PIECES.json",
              "B9-02 lintels: 60 STR.CONC.LINTEL lines to pieces (beside T-571/lintel-count-implied@V11)"),
    "T-645": ("ebc5a76a", "Verifier 2026-11-08T23:03Z", "research/agents_t645/out/STAIR_HOLD_CENSUS_T645.json",
              "B7 stair finishes HELD-blank to a quantity or a named cause"),
    "T-646": ("af50c864", "Verifier 2026-11-09T00:57Z", "research/agents_t646/out/ROOF_FENCE_HOLD_CENSUS_T646.json",
              "B13 roof layers + fence finishes HELD-blank to a quantity or a named cause"),
    "T-647": ("a521da8a", "Verifier 2026-11-09T06:56Z", "research/agents_t647/out/HELD_CAUSE_CENSUS_T647.json",
              "B9 / B10 / B11 HELD lines with no committed cause to a named cause (183 causes; 17 B11 count gaps HELD)"),
    "T-649": ("89afbd85", "Verifier 2026-11-09T06:59Z", "research/agents_t649/out/TRIAL_BOQ_R2_T649.json",
              "wiring manifest V18 + trial BOQ r2 (non-candidate; the delivery document of record, read by T-635 only "
              "for this register: its quantities are not statement rows)"),
}
REFUSED = {"T-648": "REJECTED c4d37ec8 (Verifier 2026-11-09 07:04 UTC; merge 17afac73 reverted by 92d5d1ff): not folded, "
                    "not beside (R-T620-1 (a))"}

# ---------------------------------------------------------------- Checker Gate A verdicts, quoted in part (BOARD.md)
C622 = ("Checker 2026-11-08T10:00Z (T-622 Gate A, merge 31fe39db): OWN RE-MEASURE (P7757.dxf, own ezdxf read of each face "
        "line; heights Q-48 A, doors 2.20 Q-55 C): ")
C622_ROOM = {
    "1F-07": C622 + "1F-07 laundry closed L-chain 16.940 m; gaps W21 0.600, D 0.800, D 0.900: 16.94 x 3.35 - 0.48 - 1.76 - "
                    "1.98 = 52.529 m2 AGREE; 'Statuses: 1F-07 / GF-07 / 2F-02 rows VERIFIED (own re-measure)'",
    "2F-02": C622 + "2F-02 W.C. box 1.850 x 3.000 = 9.700 m; W28 gap 0.600, door gap 0.800: 9.70 x 3.35 - 0.48 - 1.76 = "
                    "30.255 m2 AGREE; 'Statuses: 1F-07 / GF-07 / 2F-02 rows VERIFIED (own re-measure)'",
    "GF-07": C622 + "GF-07 pantry faces 10.500 m x 3.65 - W09 - W10 - door = 32.375 m2 AGREE worker; engine line 32.3422 "
                    "(walk face 10.491) is 0.0328 m2 short: ENGINE_WRONG confirmed (fix row; no candidate line moved)",
}
C623 = ("Checker 2026-11-08T09:59Z (T-623 Gate A, merge 2d840524): OWN RE-MEASURE (ST7757 dxf + concrete workbook, own "
        "ezdxf / shapely read; worker numbers not used as expected values): ")
C623_ROW = {
    ("T-545/beams@V11", 17): C623 + "(1) 1F CB12 outer-face extent 12.000 m; his 0.25 x 0.75 x 13.00 -> BEYOND 1.000 x 0.25 "
                                    "x 0.75 = 0.187500 m3 AGREE F-T623-1; inside the extent 0.228349 AGREE; both re-add to "
                                    "0.415849 (line total unchanged)",
    ("T-545/beams@V11", 19): C623 + "(2) 1F dome ring arcs 5FE / 600 r 2.211092 / 2.411092 clipped to the bay: own 1.510479 "
                                    "m2 x 0.50 = 0.755240 m3 AGREE (-0.755240)",
    ("T-545/beams@V11", 9): C623 + "(3) GF B20 upstand: section A-A 0.40 x 0.75 + 0.20 x 0.20 = 0.340 m2; upstand run hidden "
                                   "line 55F 3.000 m: 0.04 x 3.000 = 0.120 m3 AGREE (-0.120)",
    ("T-551/columns@V10", 1): C623 + "(4) GF C2 COUNT: 4 C2 outlines + 4 tags (column and neck plans); his GF C2 row 6: "
                                     "excess 2 x 0.20 x 0.50 x 3.75 = 0.750 m3 AGREE (+0.750)",
    ("T-551/columns@V10", 0): C623 + "(4) C1 likewise 1 drawn (341, tags 1079 / 1F9) vs his 2 -> +0.375 AGREE",
    ("T-551/columns@V10", 7): C623 + "(5) GF BASE: own outlines 365 0.125 m2, 35F 0.150 m2; x (0.25 - 0.95) = -0.192500 m3 "
                                     "AGREE; base +0.25 a reused verified source reference (T-287 G1)",
}
C625 = ("Checker 2026-11-08T12:59Z (T-625 Gate A, merge 47824e04): OWN RE-MEASURE (P7757.dxf, own ezdxf + shapely read): ")
C625_ROW0 = (C625 + "ROW 0: exact sector 4.044824 + run 2.092860 = own 6.137684 m2 AGREE; engine 6.124412 is 0.013272 short = "
             "ENGINE_WRONG (chord flattening of a drawn arc) -> fix row; row class RULE_DIFFERENCE kept (UP-CER-001)")
C625_OPEN = (C625 + "GF-OPEN.full built from ALL layer 1 / W / S-COL.BON linework + 4 door gaps + 2 printed open sides: "
             "147.657677 vs his 147.657691 AGREE; the only island 0.884381 m2 = the separate deduction row 4 (0.88), "
             "counted once; 'GF-OPEN.full VERIFIED' (the boundary, not this row's his-minus-engine split)")
C626 = ("Checker 2026-11-08T13:59Z (T-626 Gate A, merge 74e52c34): OWN RE-MEASURE of the 3 largest rows from the "
        "architectural entities by handle, before reading his figures: ")
C626_ROW = {
    ("T-546/floor", 17): C626 + "pantry box 3.000 x 4.500 = 13.500, column 2FAE overlap 0.045 -> 13.455 m2 AGREE (wet by "
                                "Q-37 A: RULE_DIFFERENCE stands)",
    ("T-541/membrane", 2): C626 + "+9.70 domes 12EB / 2F33 r 2.211091524 each: 2 x pi r^2 = 30.718026 m2 AGREE",
    ("T-541/membrane", 1): C626 + "third dome 1300 r 2.205018498: 15.274758 AGREE (inside the field)",
}
C626_VALUE = {("T-546/floor", 17): "-13.455", ("T-541/membrane", 2): "30.718026", ("T-541/membrane", 1): "15.274758"}
C627 = ("Checker 2026-11-08T15:57Z (T-627 Gate A, merge a7ee000d): OWN RE-MEASURE from the architectural DXF, DIMENSION "
        "measurement and displayed block text by handle: ")
C627_ROW = {
    ("T-568/windows-m2", 11): ("V", C627 + "W14 plan 1198 '245' x SE 2B47 '160' -> 2.45 x 1.60 = 3.920 m2 AGREE"),
    ("T-568/windows-m2", 12): ("V", C627 + "W13 1126 '120' x 2A9C '230' = 2.760 AGREE"),
    ("T-568/windows-m2", 14): ("V", C627 + "W26 149D '120' x 2AB8 '170' = 2.040 AGREE"),
    ("T-568/windows-m2", 7): ("V", C627 + "W18 11ED '50' x 2EFA '216' = 1.080 AGREE"),
    ("T-568/windows-m2", 8): ("V", C627 + "W18 11ED '50' x 2EFA '216' = 1.080 AGREE"),
    ("T-568/windows-m2", 3): ("P", C627 + "W11 / W12 width A3E / A22 '195' AGREE, HEIGHT 2.20 NOT re-measured (DWF fence "
                                          "elevation) -> W11 / W12 PARTIALLY VERIFIED (1 / 2 dims)"),
    ("T-568/windows-m2", 4): ("P", C627 + "W11 / W12 width A3E / A22 '195' AGREE, HEIGHT 2.20 NOT re-measured (DWF fence "
                                          "elevation) -> W11 / W12 PARTIALLY VERIFIED (1 / 2 dims)"),
}
C628 = ("Checker 2026-11-08T15:55Z (T-628 Gate A, merge a7ee000d chain, head 14f53dcc): OWN RE-MEASURE from the raw "
        "entities by handle (ST7757 dxf): ")
C628_LIFT = (C628 + "Lift ring 10EB less 10EA 1.600 m2, S-COL.BON 1090 0.20 + 1093 / 1096 / 1099 0.10 each = 0.500 in the "
             "ring, net 1.100 m2 AGREE; height unprinted (D-43) HELD; 'lift walls: 0.75 ENGINE_RIGHT on the ring geometry' "
             "(the 0.75 m3 carries his depth: plan component only)")
C633 = ("Checker 2026-11-09T03:58Z (T-633 Gate A, merge 2f103248): OWN RE-MEASURE, 3 largest rows + spot rows: ")
C633_ROW = {
    40: ("V", C633 + "W14 jambs C41 / C46 2449.8 mm + SE dim 2B47 1598.6 (printed 160): row 40 (1.60 - 2.00) x 2.45 = "
                     "-0.98 AGREE"),
    24: ("A", C633 + "D-GF-10 faces 2AF / 2B0 & 2B1 / 2B2 gap 797.0 mm AGREE (width only): this row is the HEIGHT row "
                     "(Q-55 C owner rule), so the width read does not stamp it: stays UNKNOWN"),
    76: ("P", C633 + "row 76 boundary 74.40: his row read; ST p.14 typical boundary wall = masonry booked under "
                     "EXT.FENCE.WALL: RULE_DIFFERENCE AGREE, counted once; length 37.20 NOT re-measured: PARTIALLY VERIFIED "
                     "1/2 (class yes, length no)"),
    78: ("P", C633 + "row 78 RC upstand: ST p.14 parapet section, RC upstand 30 from slab top: 0.30 x 136.83760 = 41.05128 "
                     "ENGINE_RIGHT AGREE (height CHECKER-CONFIRMED; centrelines cited from the T-319 Gate B PASS, not "
                     "re-measured)"),
}
C634 = ("Checker 2026-11-08T19:59Z (T-634 Gate A, merge 52230429): OWN RE-MEASURE, P7757 by box search, not the "
        "worker's chain: ")
C634_1F04 = (C634 + "1F-04 (dry) interior 3.650 x 5.000 = 17.300 + mid-face column 2FFC +0.100 -> 17.400 lm AGREE; openings "
             "1.55232 x 1.50 + 1.0 x 2.20 + 0.8 x 2.20 = 6.28848 AGREE; paint 17.40 x 3.35 - 6.28848 = 52.00152 AGREE "
             "(plaster height basis T-556 reused, not re-derived)")
C634_GF02 = (C634 + "GF-02 (wet: WASH / WASH2 fixtures inside) 1.500 x 2.100 = 7.200 lm; corner column 2FA5 at the corner "
             "-> perimeter unchanged, 7.200 AGREE; paint refused on the wet face agrees with the owner 2026-11-02 rule")
C634_ROW = {   # row index (same index in both sections) -> (grade, text)
    14: ("V", C634_1F04), 16: ("V", C634_1F04), 31: ("V", C634_GF02), 32: ("V", C634_GF02),
}
GATE_A = {t: f"status accepted at Checker Gate A ({MERGED[t][1].split(',')[0]}); quantity not re-measured by the Checker"
          for t in MERGED}

RANK = {None: 0, "WORKER_PROPOSED": 0, "DRAWING_CONFIRMED": 1, "PARTIALLY_VERIFIED": 2, "CHECKER_VERIFIED": 3}
EVIDENCE_KEYS = ("evidence_status", "evidence_verdict")
ANNOTATIONS = ("evidence_v12", "evidence_source_v12", "own_v12")
NEW_REPORTS = ["T-622", "T-623", "T-625", "T-626", "T-627", "T-628", "T-633", "T-634"]
PENDING = [
    "class proposals listed beside (class_proposals_v12): F-T623-1 CB12 split, F-T627-1 door heads, T-622 GF-14 / GF-07, "
    "T-633 D-GF-06 / W25 ..., T-634 plaster heights: a class move is its own reviewed fold, not applied here",
    "fix rows not wired in the candidate (beside only): FR-T624-1 .. -3, T-625 row 0 +0.013272 m2, T-622 GF-07 "
    "-0.0328 m2, T-634 W03 ledger -0.00414 m, and the V11 list",
    "T-648 (REJECTED 2026-11-09 07:04 UTC): B2 / B3 / B4 / B6 / B7 / B8 HELD causes not folded",
    "T-314 / T-423 / T-563 (Gate B integration packages, open): the candidate V3.0.59 lines they move are not statement rows",
]


# ================================================================================ inputs ===========================
def require_merged(task: str, merged: dict = MERGED) -> tuple[str, str]:
    """R-T620-1 (a) as V11: a fold from a task that is not MERGED is refused."""
    if task in REFUSED:
        raise StatementError(f"{task}: {REFUSED[task]}")
    if task not in merged:
        raise StatementError(f"{task}: not in the merged register: a fold from an unmerged task is refused")
    p = SRC.get(task)
    if p is None or not p.exists():
        raise StatementError(f"{task}: merged source file absent from the tree: refused")
    return merged[task]


def load_sources(merged: dict = MERGED) -> dict:
    out = {}
    for t in SRC:
        require_merged(t, merged)
        out[t] = json.loads(SRC[t].read_text(encoding="utf-8"))
    return out


def v11_statement() -> dict:
    raw = B620.JSON_OUT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != V11_SHA256:
        raise StatementError("statement V11 sha256 differs from the pin (the T-620 scorecard reads the same pin)")
    st11 = B620.build()
    if st11 != json.loads(raw) or B620.to_markdown(st11) != B620.MD_OUT.read_text(encoding="utf-8"):
        raise StatementError("T-620 statement V11 does not reproduce: rebuild it before T-635")
    return st11


LEVELS11 = B620.LEVELS10 + ("sections_v11",)
SUP11 = B620.SUP10 + ("supersedes_v11",)


def of_record(st: dict, sid: str) -> dict:
    secs = B620.all_sections(st, LEVELS11)
    sup = B620.supersession(st, SUP11)
    if sid in sup:
        raise StatementError(f"{sid}: superseded by {sup[sid]}, not a section of record")
    if sid not in secs:
        raise StatementError(f"{sid}: no such section")
    return secs[sid]


# ================================================================================ (a) (b) (c) the fold =============
def _eq_at(stated: str, own: str | None) -> bool:
    """own equals stated at the stated row's printed precision."""
    if own is None:
        return False
    s = D(str(stated))
    return D(str(own)).quantize(s) == s if s.as_tuple().exponent < 0 else D(str(own)) == s


def grade(stated: str, own: str | None, wanted: str) -> tuple[str, str | None]:
    """(b) a Checker re-measure that differs from the row's delta is PARTIALLY_VERIFIED with the difference named."""
    if wanted == "CHECKER_VERIFIED" and not _eq_at(stated, own):
        return "PARTIALLY_VERIFIED", f"Checker re-measure {own} differs from the row delta {stated} (named, not absorbed)"
    return wanted, None


def bind(sec: dict, i: int, name: str, cls: str, delta: str, prefix: int | None = None) -> dict:
    """(a) bind by index AND name AND class AND delta."""
    if not 0 <= i < len(sec["rows"]):
        raise StatementError(f"{sec['section_id']}: row {i} absent")
    r = sec["rows"][i]
    nm_ok = r["name"] == name if prefix is None else r["name"][:prefix] == name[:prefix]
    if not nm_ok or r["class"] != cls or D(str(r["delta"])) != D(str(delta)):
        raise StatementError(f"{sec['section_id']} row {i}: worker row ({name[:40]!r}, {cls}, {delta}) does not bind to "
                             f"({r['name'][:40]!r}, {r['class']}, {r['delta']}) (R-T635-1 (a))")
    return r


def stamp(sec: dict, i: int, task: str, status: str | None, verdict: str, own: str | None = None) -> dict:
    """status None = annotation only (UNKNOWN stays UNKNOWN). (c) never lower; (e) HELD untouched."""
    r = sec["rows"][i]
    if r["class"] == "HELD":
        raise StatementError(f"{sec['section_id']} row {i}: a HELD row is never stamped (R-T635-1 (e))")
    was = r.get("evidence_status")
    if status is not None:
        if RANK.get(was, 0) > RANK[status]:
            raise StatementError(f"{sec['section_id']} row {i}: {was} would be lowered to {status} (R-T635-1 (c))")
        if RANK.get(was, 0) == RANK[status] and was == status:
            r["evidence_v12"] = f"{task}: {status} confirmed again: " + verdict[:300]
        else:
            if was and r.get("evidence_verdict"):       # provenance of the lower stamp kept, never overwritten silently
                r["evidence_v12"] = f"was {was}: " + str(r["evidence_verdict"])[:300]
            r["evidence_status"], r["evidence_verdict"] = status, verdict
    else:
        r["evidence_v12"] = verdict
    if own is not None:
        r["own_v12"] = str(own)
    r["evidence_source_v12"] = f"{task} ({MERGED[task][0]})"
    return {"row": i, "name": r["name"][:80], "from": was or (r.get("verification") or "none")[:40],
            "to": r.get("evidence_status") if status is not None else f"{was or 'UNKNOWN'} (annotated)",
            "class": r["class"], "delta": r["delta"]}


def _restate(old: dict, task: str) -> dict:
    require_merged(task)
    new = copy.deepcopy(old)
    new["section_id"] = old["section_id"].split("@")[0] + "@V12"
    new["restates"] = old["section_id"]
    new["fold_v12"] = f"{task} ({MERGED[task][0]})"
    return new


def _close(old: dict, new: dict, moves: list, props: list, note: str) -> tuple[dict, list]:
    new["change_note_v12"] = note
    if props:
        new["class_proposals_v12"] = props
    B620.check_rows_kept(old, new, extra=EVIDENCE_KEYS + ANNOTATIONS)
    for o, n in zip(old["rows"], new["rows"]):
        added = set(n) - set(o) - set(EVIDENCE_KEYS) - set(ANNOTATIONS)
        if added:
            raise StatementError(f"{new['section_id']}: row adds {sorted(added)}")
    B620.check_totals(old, new)
    for m in moves:
        m["section_id"] = new["section_id"]
        m["unit"] = new["unit"]
    return new, moves


def _dc(task: str, what: str, own=None, stated=None) -> str:
    d = "" if own is None else f"; own {own} vs row {stated}"
    return f"{task} worker own drawing re-measure ({what}){d}; {GATE_A[task]}"


# ================================================================================ the eight folds =================
def f622(st: dict, d: dict) -> list:
    old = of_record(st, "T-547/wall-tile")
    if d["section"] != "T-547/wall-tile" or d["unknown_rows"] != 47:
        raise StatementError("T-622 was built on another section")
    new, moves, props = _restate(old, "T-622"), [], []
    for r in d["rows"]:
        i = r["row"]
        if i is None:     # OWN ONLY (CAD noise, no stated row): beside, never a row
            props.append({"row": None, "name": r["name"][:80], "own": r["own"], "statement": "no row", "proposed": r["class"],
                          "source": "T-622 OWN ONLY (no stated row; CAD noise < 0.010 m2): beside, not a row"})
            continue
        bind(new, i, r["name"], r["stated_class"], r["stated"])
        room = next((k for k in C622_ROOM if new["rows"][i]["name"].startswith(k)), None)
        if room:
            s, why = grade(r["stated"], r["own"], "CHECKER_VERIFIED")
            if room == "GF-07":
                s, why = "PARTIALLY_VERIFIED", ("the row carries the engine line 32.3422; the Checker's own 32.375 shows "
                                                "a 0.0328 m2 ENGINE_WRONG part inside this RULE_DIFFERENCE row (split = "
                                                "class proposal beside)")
            moves.append(stamp(new, i, "T-622", s, C622_ROOM[room] + (f"; {why}" if why else ""), r["own"]))
        elif r["evidence"] == "DRAWING-CONFIRMED" and r["class"] == r["stated_class"]:
            moves.append(stamp(new, i, "T-622", "DRAWING_CONFIRMED",
                               _dc("T-622", "face chain by handle", r["own"], r["stated"]), r["own"]))
        else:
            moves.append(stamp(new, i, "T-622", None, f"T-622 {r['evidence']}: own {r['own']} vs row {r['stated']} "
                               f"(diff {r['diff']}); stays UNKNOWN (R-T635-1 (b))", r["own"]))
        if r["class"] != r["stated_class"] or (room == "GF-07"):
            props.append({"row": i, "name": r["name"][:80], "statement": r["stated_class"],
                          "proposed": r["class"] if room != "GF-07" else "RULE_DIFFERENCE -32.375 + ENGINE_WRONG 0.0328",
                          "source": "T-622 worker" + (" + Checker 10:00Z (ENGINE_WRONG confirmed)" if room else "")})
    note = ("evidence only: 1F-07 / 2F-02 rows VERIFIED by the Checker's own re-measure, GF-07 PARTIALLY VERIFIED (0.0328 "
            "m2 ENGINE_WRONG inside), the other worker rows DRAWING-CONFIRMED; 5 DIFFERS rows annotated UNKNOWN; HELD 6 "
            "untouched by name")
    return [_close(old, new, moves, props, note)]


def f623(st: dict, d: dict) -> list:
    out = []
    for key, sid in (("T-545/beams@V10", "T-545/beams@V11"), ("T-551/columns@V10", "T-551/columns@V10")):
        old = of_record(st, sid)
        new, moves, props = _restate(old, "T-623"), [], []
        for r in d["lines"][key]["rows"]:
            i = r["row"]
            bind(new, i, r["name"], r["statement_class"], r["statement_delta"])
            if (sid, i) in C623_ROW:
                s, why = grade(r["statement_delta"], r["own_delta"], "CHECKER_VERIFIED")
                moves.append(stamp(new, i, "T-623", s, C623_ROW[(sid, i)] + (f"; {why}" if why else ""), r["own_delta"]))
            elif r["status"] == "RE-MEASURED":
                moves.append(stamp(new, i, "T-623", "DRAWING_CONFIRMED",
                                   _dc("T-623", f"pieces {', '.join(r['pieces'][:6])}; drift {r['drift']}",
                                       r["own_delta"], r["statement_delta"]), r["own_delta"]))
            else:
                moves.append(stamp(new, i, "T-623", None, f"T-623 {r['status']}: J re-measured, T cited (his lengths, "
                                   "private); the residual stays UNRESOLVED (T-600 r2 bounds, never a point)", r["own_delta"]))
            if r["class"] != r["statement_class"]:
                props.append({"row": i, "name": r["name"][:80], "statement": r["statement_class"], "proposed": r["class"],
                              "source": "T-623 worker"})
            if D(r["drift"]) != 0:
                props.append({"row": i, "name": r["name"][:80], "statement": r["statement_class"],
                              "proposed": f"delta {r['statement_delta']} -> {r['own_delta']} (drift {r['drift']}; "
                                          f"{(r.get('drift_cause') or 'cause in T-623')[:120]})",
                              "source": "T-623 (F-T623-1 where CB12)"})
        note = ("evidence only: Checker own re-measure rows VERIFIED where equal at the row's precision (CB12 PARTIALLY: "
                "0.1875 BEYOND vs row 0.160962, F-T623-1 split beside); other RE-MEASURED rows DRAWING-CONFIRMED; "
                "THROUGH_SUPPORT residuals annotated UNRESOLVED")
        out.append(_close(old, new, moves, props, note))
    return out


def f625(st: dict, d: dict) -> list:
    old = of_record(st, "T-553/floor-tile@V11")
    new, moves, props = _restate(old, "T-625"), [], []
    r0 = d["row0"]
    bind(new, 0, new["rows"][0]["name"], r0["t621_class"], r0["t621_delta"])
    s, why = grade(r0["t621_delta"], r0["own"], "CHECKER_VERIFIED")
    moves.append(stamp(new, 0, "T-625", s, C625_ROW0 + (f"; {why}" if why else ""), r0["own"]))
    props.append({"row": 0, "name": new["rows"][0]["name"][:80], "statement": "RULE_DIFFERENCE 6.124412",
                  "proposed": f"RULE_DIFFERENCE {r0['own']} (+0.013272 ENGINE_WRONG chord loss) and curtail 0.157787 "
                              "(ENGINE_WRONG proposal, worker)", "source": "T-625 + Checker 12:59Z (fix row for V16)"})
    for c in d["carried_rows"]:
        i = c["row"]
        bind(new, i, new["rows"][i]["name"], c["class"], c["delta"])
        if c["boundary"] == "GF-OPEN.full":
            moves.append(stamp(new, i, "T-625", "PARTIALLY_VERIFIED", C625_OPEN))
        else:
            moves.append(stamp(new, i, "T-625", "DRAWING_CONFIRMED",
                               _dc("T-625", f"boundary {c['boundary']}: {c['boundary_status']}")))
    note = ("evidence only: row 0 PARTIALLY VERIFIED (Checker own 6.137684 vs row 6.124412, ENGINE_WRONG 0.013272 named), "
            "the five GF-OPEN.full rows PARTIALLY VERIFIED (boundary re-measured by the Checker), 1F-LIV rows keep "
            "DRAWING-CONFIRMED")
    return [_close(old, new, moves, props, note)]


def f626(st: dict, d: dict) -> list:
    out, idx = [], {}
    for sid in d["statement"]["sections"]:
        old = of_record(st, sid)
        idx[sid] = (old, _restate(old, "T-626"), [], [])
    seen = {sid: 0 for sid in idx}
    for r in d["rows"]:
        old, new, moves, props = idx[r["section"]]
        i = seen[r["section"]]
        seen[r["section"]] += 1
        bind(new, i, r["name"], r["class"], r["delta"])
        if r["class"] == "HELD":
            continue
        if (r["section"], i) in C626_ROW:
            s, why = grade(r["delta"], C626_VALUE[(r["section"], i)], "CHECKER_VERIFIED")
            moves.append(stamp(new, i, "T-626", s, C626_ROW[(r["section"], i)] + (f"; {why}" if why else ""),
                               C626_VALUE[(r["section"], i)]))
        elif r["evidence_status"] == "DRAWING_CONFIRMED":
            moves.append(stamp(new, i, "T-626", "DRAWING_CONFIRMED",
                               _dc("T-626", f"{r['kind']} by handles {', '.join(r.get('handles', [])[:6]) or 'measures ' + ', '.join(map(str, r.get('measures', [])))[:60]}", r.get("own"),
                                   r.get("engine")), r.get("own")))
        else:
            moves.append(stamp(new, i, "T-626", None, f"T-626 {r['evidence_status']}: his lump row, residual split into "
                               "own parts (TOLERANCE arc 0.001332 DRAWING-CONFIRMED + UNRESOLVED 0.521668); stays UNKNOWN"))
    for sid, (old, new, moves, props) in idx.items():
        if seen[sid] != len(old["rows"]):
            raise StatementError(f"T-626: {sid} rows bound {seen[sid]} != {len(old['rows'])}")
        out.append(_close(old, new, moves, props, "evidence only: Checker own re-measure rows VERIFIED (pantry, +9.70 "
                          "domes, third dome); other rows DRAWING-CONFIRMED (worker); top roof HELD untouched (Q-34); "
                          "residual 0.523 annotated UNKNOWN"))
    return out


def f627(st: dict, d: dict) -> list:
    out = []
    for sid, v in d["sections"].items():
        old = of_record(st, sid)
        new, moves, props = _restate(old, "T-627"), [], []
        if len(v["rows"]) != len(old["rows"]):
            raise StatementError(f"T-627 {sid}: row count differs")
        for i, r in enumerate(v["rows"]):
            bind(new, i, r["name"], r["class"], r["delta"])
            if r["class"] == "HELD":
                continue
            own = r.get("expected")
            if (sid, i) in C627_ROW:
                g, txt = C627_ROW[(sid, i)]
                s, why = grade(r["delta"], own, "CHECKER_VERIFIED") if g == "V" else ("PARTIALLY_VERIFIED", None)
                moves.append(stamp(new, i, "T-627", s, txt + (f"; {why}" if why else ""), own))
            elif r["evidence"] == "DRAWING_CONFIRMED":
                moves.append(stamp(new, i, "T-627", "DRAWING_CONFIRMED",
                                   _dc("T-627", f"{r['id']}: {r.get('own_width_basis', '')[:60]}; height "
                                                f"{r.get('own_height_basis', '')[:60]}", own, r["delta"]), own))
            else:
                moves.append(stamp(new, i, "T-627", None, f"T-627 {r['evidence']} ({r['id']}: height Q-55 C owner rule, "
                                   "not a drawn value): stays UNKNOWN (R-T635-1 (b))", own))
            pc = r.get("proposed_class")
            if pc and pc != r["class"]:
                props.append({"row": i, "name": r["name"][:80], "statement": r["class"], "proposed": pc,
                              "source": "T-627 F-T627-1 (not ruled at T-627 Gate A; heads 2.20 ruled by the Verifier "
                                        "17:04 per the T-633 verdict)"})
        out.append(_close(old, new, moves, props, "evidence only: W13 / W14 / W26 / W18 VERIFIED (printed both ways, "
                          "Checker own read), W11 / W12 PARTIALLY VERIFIED (width only), masonry-jamb rows DRAWING-"
                          "CONFIRMED; Q-55 C door heights annotated UNKNOWN; W02 / W17 HELD untouched"))
    return out


def f628(st: dict, d: dict) -> list:
    out = []
    for sid, v in d["lines"].items():
        old = of_record(st, sid)
        new, moves, props = _restate(old, "T-628"), [], []
        for r in v["rows"]:
            i = r["row"]
            bind(new, i, r["name"], r["statement_class"], r["statement_delta"])
            if r["status"] == "HELD":
                continue
            if sid == "T-551/lift-walls" and i == 0:
                moves.append(stamp(new, i, "T-628", "PARTIALLY_VERIFIED", C628_LIFT, r["own_delta"]))
            elif r["status"] == "RE-MEASURED":
                moves.append(stamp(new, i, "T-628", "DRAWING_CONFIRMED",
                                   _dc("T-628", "outlines / schedule by handle; Checker: 'F3 count, FN notch, strap "
                                       "lengths ... stay DRAWING-CONFIRMED until a Checker read'", r["own_delta"],
                                       r["statement_delta"]), r["own_delta"]))
            else:
                raise StatementError(f"T-628 {sid} row {i}: unknown status {r['status']!r}")
        if sid == "T-551/footing-line":
            fr = d["fix_rows"][0]
            props.append({"row": None, "name": "footing section bound", "statement": "HELD band bound 7.2204 (UNSUPPORTED)",
                          "proposed": f"drawing range {' .. '.join(fr['corrected_engine_bounded'])} m3 ({fr['id']})",
                          "source": "T-628 F-T628-1 ACCEPTED by the Checker 15:55Z (for the Lead)"})
        out.append(_close(old, new, moves, props, "evidence only: RE-MEASURED rows DRAWING-CONFIRMED (worker), lift-wall "
                          "SCOPE_DOUBLE PARTIALLY VERIFIED (Checker plan pieces, his depth), HELD rows untouched"))
    return out


def f633(st: dict, d: dict) -> list:
    old = of_record(st, "T-543/blockwork")
    if d["section"] != "T-543/blockwork":
        raise StatementError("T-633 was built on another section")
    new, moves, props = _restate(old, "T-633"), [], []
    for r in d["rows"]:
        i = r["index"]
        bind(new, i, r["name"], r["statement_class"], r["statement_delta"], prefix=40)
        if i in C633_ROW:
            g, txt = C633_ROW[i]
            s, why = grade(r["statement_delta"], r["own_delta"], "CHECKER_VERIFIED") if g == "V" else \
                ("PARTIALLY_VERIFIED", None) if g == "P" else (None, None)
            moves.append(stamp(new, i, "T-633", s, txt + (f"; {why}" if why else ""), r["own_delta"]))
        elif r["evidence"] == "OWN_DXF":
            moves.append(stamp(new, i, "T-633", "DRAWING_CONFIRMED",
                               _dc("T-633", f"own DXF {', '.join(r['handles'][:6])}", r["own_delta"],
                                   r["statement_delta"]), r["own_delta"]))
        else:
            why = {"REPRODUCED": "arithmetic of the T-543 decomposition, not drawing evidence (Checker 03:58Z)",
                   "CITED": "cited source, not re-measured", "OWNER_RULE": "owner-rule quantity (Q-55 C): "
                   "ASSUMED-OWNER-APPROVED, not a drawn value", "OWN_DXF+CITED": "own DXF in part, the rest cited"}
            moves.append(stamp(new, i, "T-633", None, f"T-633 {r['evidence']}: {why[r['evidence']]}; residual "
                               f"{r['residual']}; stays UNKNOWN (R-T635-1 (b))", r["own_delta"]))
        if r["class_proposed"] != r["statement_class"]:
            props.append({"row": i, "name": r["name"][:80], "statement": r["statement_class"],
                          "proposed": r["class_proposed"], "source": "T-633 worker (D-GF-06: consistent with ruled "
                          "F-T627-1, Checker 03:58Z)"})
    return [_close(old, new, moves, props, "evidence only: W14 row 40 VERIFIED (Checker own read), rows 76 / 78 "
                   "PARTIALLY VERIFIED (component), row 24 (height) annotated, OWN_DXF rows DRAWING-CONFIRMED; REPRODUCED / CITED / OWNER_RULE rows "
                   "annotated UNKNOWN; HELD 50 untouched")]


def f634(st: dict, d: dict) -> list:
    out = []
    for sid in ("T-552/plaster-internal", "T-561/paint-internal"):
        old = of_record(st, sid)
        new, moves, props = _restate(old, "T-634"), [], []
        for r in [x for x in d["rows"] if x["section"] == sid]:
            i = r["row_index"]
            bind(new, i, r["name"], r["class"], r["stated"], prefix=30)
            if i in C634_ROW:
                g, txt = C634_ROW[i]
                s, why = grade(new["rows"][i]["delta"], r["own"], "CHECKER_VERIFIED")
                moves.append(stamp(new, i, "T-634", s, txt + (f"; {why}" if why else ""), r["own"]))
            elif r["evidence"] == "DRAWING-CONFIRMED":
                moves.append(stamp(new, i, "T-634", "DRAWING_CONFIRMED",
                                   _dc("T-634", r["basis"][:80], r["own"], r["stated"]), r["own"]))
            else:
                moves.append(stamp(new, i, "T-634", None, f"T-634 {r['evidence']}: own {r['own']} vs row {r['stated']} "
                                   f"({r['basis'][:80]}); stays UNKNOWN", r["own"]))
        out.append(_close(old, new, moves, props, "evidence only: 1F-04 / GF-02 face and opening rows VERIFIED where "
                          "equal at the row's precision (Checker own box search), the other worker rows DRAWING-"
                          "CONFIRMED; DIFFERS annotated UNKNOWN; HELD untouched"))
    return out


FOLDS = (("T-622", f622), ("T-623", f623), ("T-625", f625), ("T-626", f626), ("T-627", f627), ("T-628", f628),
         ("T-633", f633), ("T-634", f634))


# ================================================================================ build ============================
EXTENDED = ("reports_covered", "reports_pending", "rule", "provenance")


def check_v11_unchanged(st: dict, st11: dict) -> None:
    for k in st11:
        if k in EXTENDED:
            continue
        if json.dumps(st[k], sort_keys=True) != json.dumps(st11[k], sort_keys=True):
            raise StatementError(f"V11 key {k} changed in V12")
    if st["reports_covered"][:len(st11["reports_covered"])] != st11["reports_covered"]:
        raise StatementError("V11 reports_covered not carried as its prefix")
    if not st["rule"].startswith(st11["rule"]):
        raise StatementError("V11 rule text not carried as its prefix")
    if {k: v for k, v in st["provenance"].items() if k in st11["provenance"]} != st11["provenance"]:
        raise StatementError("V11 provenance changed")


def beside_register() -> list:
    out = []
    for t, (m, when, path, what) in BESIDE.items():
        p = ROOT / path
        if not p.exists():
            raise StatementError(f"{t}: merged source {path} absent: refused")
        out.append({"task": t, "merge": m, "verdict": f"{when}, MERGED (Gate A PASS)", "source": path,
                    "sha256": Z.sha(p), "what": what,
                    "statement_effect": "none: no statement section restated; quantities stay in the candidate / "
                                        "research outputs of record (never 0, never folded here)"})
    return out


def headline(secs: list) -> list:
    out = []
    for c in secs:
        ev: dict = {}
        for r in c["rows"]:
            e = "HELD" if r["class"] == "HELD" else (r.get("evidence_status") or "UNKNOWN")
            ev.setdefault(e, [0, D(0)])
            ev[e][0] += 1
            ev[e][1] += D(r["delta"])
        out.append({"section_id": c["section_id"], "restates": c["restates"], "fold": c["fold_v12"], "unit": c["unit"],
                    "reference_total": c["reference_total"], "engine_valued": c["engine_valued"],
                    "difference": c["difference"], "by_class": c["by_class"],
                    "rows_by_evidence": {k: [v[0], Z.s(v[1])] for k, v in sorted(ev.items())}})
    return out


def build_from(st11: dict, src: dict) -> dict:
    st = copy.deepcopy(st11)
    secs, shifts = [], []
    for t, fn in FOLDS:
        for new, moves in fn(st11, src[t]):
            secs.append(new)
            shifts += moves
    old_all = B620.all_sections(st11, LEVELS11)
    sup11 = B620.supersession(st11, SUP11)
    for c in secs:
        if c["section_id"] in old_all:
            raise StatementError(f"{c['section_id']}: section id already in V11")
        if c["restates"] in sup11:
            raise StatementError(f"{c['section_id']}: restates a superseded section {c['restates']}")
        B620.readd(c)
    sup12 = {c["restates"]: c["section_id"] for c in secs}
    if len(sup12) != len(secs):
        raise StatementError("two V12 sections restate one section")
    st["sections_v12"] = secs
    st["supersedes_v12"] = sup12
    st["headline_v12"] = headline(secs)
    st["class_shift_v12"] = {"scored": "none: evidence folds only (classes, deltas and totals of every restated section "
                                       "equal to its section of record)", "apart": []}
    st["evidence_shift_v12"] = shifts
    st["class_proposals_v12"] = [dict(p, section_id=c["section_id"]) for c in secs for p in c.get("class_proposals_v12", [])]
    st["beside_v12"] = beside_register()
    st["refused_v12"] = REFUSED
    st["folds_v12"] = {t: {"merge": MERGED[t][0], "verdict": MERGED[t][1]} for t in SRC}
    st["reports_covered"] = st11["reports_covered"] + NEW_REPORTS
    st["reports_pending"] = PENDING
    st["rule"] = st11["rule"] + " + R-T635-1"
    st["schema_v12"] = "URBAN_T635_RECONCILED_STATEMENT_V12"
    st["provenance"]["inputs_v12"] = {str(p.relative_to(ROOT)): Z.sha(p) for p in
                                      list(SRC.values()) + [B620.JSON_OUT, B620.MD_OUT, HERE / "t635_build.py"]}
    st["released_quantities_changed"] = 0
    Z.refuse_manifest_as_line(st)
    out = json.loads(json.dumps(st, sort_keys=True))
    check_v11_unchanged(out, st11)
    return out


def build() -> dict:
    return build_from(v11_statement(), load_sources())


# ================================================================================ markdown =========================
def to_markdown(st: dict) -> str:
    md = ("# T-635 reconciled-quantities statement V12 (generated; reference - engine, + = in the reference only)\n\n"
          "V12 = statement V11 (T-620, rebuilt, equal to its committed output and its sha256 pin; every V11 key carried "
          "byte-equal) + the evidence folds below. Development villa; not an accuracy claim; nothing released "
          "(ARCH_TAKEOFF_V3.0.59 NOT RELEASED; V2.9 + route G unchanged). No class moves, no quantity moves.\n\n")
    md += ("## V12 sections (restated; reference / engine / difference / by class equal to the section of record)\n\n"
           "| Section | Restates | Fold | Unit | Reference | Engine valued | Difference | Rows by evidence (n / signed) |\n"
           "|---|---|---|---|---|---|---|---|\n")
    for h in st["headline_v12"]:
        ev = "; ".join(f"{k} {v[0]} / {v[1]}" for k, v in h["rows_by_evidence"].items())
        md += (f"| {h['section_id']} | {h['restates']} | {h['fold']} | {h['unit']} | {h['reference_total']} | "
               f"{h['engine_valued']} | {h['difference']} | {ev} |\n")
    n = {}
    for m in st["evidence_shift_v12"]:
        n[m["to"]] = n.get(m["to"], 0) + 1
    md += "\n## Evidence moves by target (class and delta unchanged)\n\n" + "".join(
        f"- {k}: {v} rows\n" for k, v in sorted(n.items()))
    md += "\n## Rows stamped VERIFIED or PARTIALLY VERIFIED (Checker own re-measure, quoted in the JSON)\n\n"
    for m in st["evidence_shift_v12"]:
        if m["to"] in ("CHECKER_VERIFIED", "PARTIALLY_VERIFIED"):
            md += f"- {m['section_id']} row {m['row']} ({m['class']} {m['delta']} {m['unit']}): {m['to']}: {m['name'][:70]}\n"
    md += "\n## Class proposals beside (never applied by this fold)\n\n"
    for p in st["class_proposals_v12"]:
        md += (f"- {p['section_id']} row {p['row']}: {p['statement']} -> {p['proposed']} [{p['source']}]: "
               f"{p['name'][:60]}\n")
    md += "\n## Beside: merged work with no statement section (named, nothing folded)\n\n"
    for b in st["beside_v12"]:
        md += f"- {b['task']} ({b['merge']}, {b['verdict']}): {b['what']}.\n"
    md += "\n## Refused\n\n" + "".join(f"- {k}: {v}\n" for k, v in st["refused_v12"].items())
    md += ("\nSuperseded (kept byte-equal in their versions): " +
           "; ".join(f"{k} -> {v}" for k, v in st["supersedes_v12"].items()) + ".\n")
    md += f"\nReports covered (added): {', '.join(NEW_REPORTS)}; pending: {'; '.join(st['reports_pending'])}.\n"
    return md


def main(argv: list[str]) -> int:
    st = build()
    md = to_markdown(st)
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(json.dumps(st, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
    if "--check" in argv:
        old = json.loads(JSON_OUT.read_text(encoding="utf-8"))
        if old != st or MD_OUT.read_text(encoding="utf-8") != md:
            print("T-635 statement differs from out/")
            return 1
        print("T-635 statement reproduces")
    if not argv:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
