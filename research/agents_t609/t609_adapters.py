"""T-609: reconciled-quantities statement V10 adapters. V10 = statement V9 (T-603, rebuilt read only, every V9 key
byte-equal) + restated sections for the merged T-602 (door steps: his UNRESOLVED 2.90 lm = G-01 street-gate step 2.50
ENGINE_OMISSION + 0.40 UNRESOLVED), T-606 (room skirting: the 1F living -8.66 lm outline row split by cause) and the
T-180 pack verdicts P01 / P02 / P03 (beam components: evidence only), plus beside blocks for T-597 (B1 plan side,
beside the T-565 NOT_COMPARABLE earthworks), the T-180 packs and the pending fix F-T606-1. Research, unwired: computes
no new quantity; reads the committed, sha256-pinned research outputs only (no drawing, workbook or client data). Sign as
V4 .. V9: reference - engine; + = in the reference only.

R-T609-1 (proposed, every villa). A statement restating sections on later merged verdicts:
  (a) A MERGED SPLIT ENTERS AS IT WAS MERGED: a residual row the merged report split is split (R-T594-1 (a)) into the
      report's own parts, each with the class the merged verdict states and the evidence its verdict line gives; the
      report's sign is converted to the statement sign and checked (the parts re-add to the row's delta, and the
      report's 'before' figure is that row's delta); a part whose class differs from the merged report is refused;
  (b) A PACK MOVES EVIDENCE, NEVER CLASS OR DELTA: a Checker re-measure pack promotes a row's evidence to
      CHECKER_VERIFIED only when it covered every mark of that row, recorded AGREE on each, and the engine figures of
      those marks re-add to the row's delta exactly; a partial pack (marks open), a pack with an ENGINE_WRONG finding
      on the row, or a row already CHECKER_VERIFIED moves nothing and is recorded beside; a class never moves on a pack;
  (c) PENDING IS BESIDE: a confirmed finding whose fix row is not merged (F-T606-1, F-C-P03-2) is a beside record valued
      0 with its before / after on the candidate; it never changes an engine column, a delta or a class;
  (d) NOT_COMPARABLE STAYS: plan-side statuses of a family the reference does not carry (his NO_ROW) are beside the
      NOT_COMPARABLE block, units apart, never a % and never a delta; a Checker figure correction (F-C-T597-1) is
      restated with its arithmetic, the merged json kept as merged;
  (e) HELD STAYS HELD: an ENGINE_OMISSION on an element whose material is unprinted (G-01 stone) is ENGINE_WRONG in the
      statement now and becomes a HELD line at its point bound when its fix row is wired, never a valued line by
      default; no HELD or UNRESOLVED row becomes 0, and no % is printed beside a HELD row.
  (f) A MERGED RULE SPLITS ONLY ITS MATCHED MAGNITUDE (r2, T-599 r2): every UNRESOLVED joint row (JOINT_HEAD /
      THROUGH_SUPPORT) of a section of record, nested set or alternative reading must carry the merged rule's record;
      a 'whole' SOURCED record reclasses the row to RULE_DIFFERENCE (evidence unchanged); a matched + residual record
      splits it (matched RULE_DIFFERENCE, PARTIALLY VERIFIED as its verdict states; residual UNRESOLVED, worker-proposed,
      to its residual task); a record whose row is not in the section of record is audited beside, never added; the
      of-record moves must re-add to the rule's own headline (RULE_DIFFERENCE n / signed / gross) and nested or
      alternative moves are reported apart, never in the class shift of record;
  (g) ONE CAUSE, ONCE (r2, T-607): a cause the merged verdict says feeds several lines is restated in each line it
      feeds with the same class, and the lines are never summed across (steps lm / nr and the nosing beside);
  (h) A PRE-REGIME SECTION TAKES A VERDICT BESIDE (r2, T-605): a merged verdict on a row of a section that predates the
      evidence stamps (R-T587-1, V6+) is a beside record with the row unchanged; no stamp is invented for it.
"""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T603 = ROOT / "research/agents_t603"
if str(T603) not in sys.path:
    sys.path.insert(0, str(T603))
import t603_adapters as A9  # noqa: E402  (T-603, read only)

A8, A7, Z = A9.A8, A9.A7, A9.Z
D = Decimal
StatementError = Z.StatementError
s = Z.s
CV, PV, WP = A9.CV, A9.PV, A9.WP

T597_JSON = ROOT / "research/agents_t597/out/T597_PLAN_SIDE.json"
T602_JSON = ROOT / "research/agents_t602/out/T602_DOOR_STEPS.json"
T604_JSON = ROOT / "research/agents_t604/out/WIRING_MANIFEST_V12.json"
T606_JSON = ROOT / "research/agents_t606/out/T606_OUTLINE_CAUSES.json"
T589_JSON = A8.T589_JSON
PINS = {
    T597_JSON: "8fca6911b12751e6aaa75bbc248adc6e11758fc67b899778d9eeb967985b7e16",
    T602_JSON: "c7cb2f106e7b2039482582c7b95688fd003368928b38b04d325b79f1cc92db40",
    T604_JSON: "3c2d0ec075c2489960c4ab0d1eab1f2eb37430ed4db733f5a57d65eaec748fb7",
    T606_JSON: "e71d85471859e284a0163d44d4a417b8c79183f92f1cc167dff6a0ae6362c8c5",
    T589_JSON: A8.PINS[A8.T589_JSON],
}
# r2 inputs (merged after the r1 claim; committed research outputs only)
T599_JSON = ROOT / "research/agents_t599/out/T599_JOINT_RULE_RESTATEMENT.json"
T605_JSON = ROOT / "research/agents_t605/out/T605_FOOTING_PAIRS.json"
T607_JSON = ROOT / "research/agents_t607/out/T607_SHARED_RESIDUAL.json"
T610_JSON = ROOT / "research/agents_t610/out/T610_BEAM_OVERLAP_CENSUS.json"
T611_JSON = ROOT / "research/agents_t611/out/WIRING_MANIFEST_V13.json"
T612_JSON = ROOT / "research/agents_t612/out/T612_REMAINDER_CAUSES.json"
PINS.update({
    T599_JSON: "dacbb62ffd6db39f4b161e43729cac796484065bd1f932ba0e422ef5a73d92ac",
    T605_JSON: "593489f45e65985dd522cf8c2a53b5304e18549a909b874e7dd3ea1f2bfd3541",
    T607_JSON: "7a8867153e6d885b3d258e4347ac9851022cdc7d87f60f4e63e829efbee129a2",
    T610_JSON: "8a146a0e2a9df2a8b91ac5373ef9ad341eef63cbad9a38a3c6f9c122cb985483",
    T611_JSON: "a78e73d770a4429eed1a62dce7d65cfffa781fb86db11c1bf35f84e9072990f9",
    T612_JSON: "fce519c7124ace028e47ef9e453e658100353de15bc38659763cc50d3e89a4ce",
})

# Checker verdicts (board / RUN_LOG, 2026-11-07), quoted as classes, figures and evidence only
V602 = ("Checker 2026-11-07T15:02Z (T-602 Gate A, merge 6d211198): INDEPENDENT RE-MEASURE of G-01 from the architectural "
        "DXF: boundary wall gap 2.500 m, court +0.15 / street +-0.00, step 2.500 lm, riser 0.375 m2 AGREE; ours 7.30 lm "
        "vs his 7.70 (-0.40); G-01 DRAWING-CONFIRMED geometry, stone / finish HELD; G-01 ENGINE_OMISSION (FR-T602-1); "
        "count FREELANCER_RIGHT; 0.40 lm UNRESOLVED (not attributed by equal figures: correct)")
V604 = ("Checker 2026-11-07T17:58Z (T-604 Gate A, merge 54a713ee): manifest V12 step family 4.800 -> 7.300 lm / 0.720 "
        "-> 1.095 m2 / nr 5 -> 6; G-01 gap 2.500 lm AGREE (own P7757 read); FIN.SKIRTING 209.428592 -> 209.728592 lm "
        "(+0.30 only); no quantity released")
V606 = ("Checker 2026-11-07T17:59Z (T-606 Gate A, merge 1ddf21f4): own P7757 read, largest cause 1F living +8.40: the "
        "dog-leg stair enclosure 11.250 gross vs his chord 2.850 = 8.400 AGREE, ENGINE_RIGHT 8.40 CONFIRMED (our net "
        "removes the enclosure exactly: shaft 9.05 + W13 1.20 + W25 1.00); F-T606-1 re-measured 11.170 lm (worker "
        "11.22; column 3008 east return 0.05 faces the 1F floor and keeps skirting): ENGINE_WRONG CONFIRMED on 11.17, "
        "FIN.SKIRTING 209.428592 -> 198.258592 lm (V3.0.58; 198.558592 after V12), lane I fix row needed, NOT applied; "
        "the +0.20 gross cause and the 0.06 UNRESOLVED stay as split; GF open room -16.913904, curved room -0.73933, "
        "2F corridor -0.70 not re-measured (UNRESOLVED as handed); room skirting PARTIALLY VERIFIED")
V597 = ("Checker 2026-11-07T15:59Z (T-597 Gate A, merge 072e920f): own ST7757.dxf read: 24 pits union 129.234375, beyond "
        "plot 1.890000, in plot 127.344375, pool share 2.695761, zone owned 124.648614 m2 AGREE to 1e-6; pool shell "
        "10.935564, envelope in plot 11.851050 / beyond 0.365708 m2 AGREE; ENGINE_WRONG -0.000941 m2 (polygonised arc) "
        "immaterial; F-C-T597-1: FN 180C drawn outline notched 0.40 x 0.35 under F9: drawn sum 129.43, overlap 0.195625, "
        "union identical; trench not re-measured by the Checker: PARTIALLY VERIFIED; pits zone / pool plan VERIFIED "
        "(plan only), depths HELD S01; FF / F10F HELD; his side NO_ROW: no WHO-IS-RIGHT verdict")
VP01 = ("Checker 2026-11-07T12:57Z (T-180 slot, T-589 P01, RUN_LOG): own ST7757.dxf read: GF B28 0.211849 / CA 0.172500, "
        "1F B25 2.849834 / B19 1.624427 / B5 0.832500 m3 vs engine 5.690657 total, +0.000453 (+0.008 %), every mark <= "
        "0.13 % AGREE; GF and 1F COUNT components VERIFIED; beam line stays PARTIALLY VERIFIED")
VP02_2F = ("Checker 2026-11-07T15:00Z (T-180 slot, T-589 P02 2F, RUN_LOG): 2F through-support VERIFIED by own ST7757.dxf "
           "read: B3 0.028 / B8 0.120 / B15 0.240 m3 pure column footprints AGREE; B1 0.032 = footprint 0.176 netted "
           "with an un-rowed drawn B1 run 0.144 (F-C-P02-1 split, no quantity change)")
VP02_1F = ("Checker 2026-11-07T18:05Z (T-180 slot, T-589 P02 1F, RUN_LOG): own ST7757 read 6 / 9 marks: CB9 / B7 / B2 "
           "AGREE by cause, B23 +0.26 %, B1 / CB13 in sum only (F-C-P02-2); CB10 / CB11 / CB12 open")
VP03_1F = ("Checker 2026-11-07T16:04Z (T-180 slot, T-589 P03 1F, RUN_LOG): B6 1.577750 vs engine 1.577773, B4 net "
           "+0.3312 vs 0.331173 m3 AGREE (F-C-P03-1 split, binding-invariant net)")
VP03_GF = ("Checker 2026-11-07T16:57Z (T-180 slot, T-589 P03 GF, RUN_LOG): GF B1 12 labels = 12 runs; 11 AGREE; "
           "BAND0029.4 0.146096 vs engine 0.151391: B27 face crosses B1, overlap 0.014761 m2 billed in B27 and B1 -> "
           "F-C-P03-2 ENGINE_WRONG -0.005295 m3, fix row for the Lead; GF B1 total 1.337040 vs 1.342119; residual by "
           "cause F-C-P03-3 (spans the RUN_COUNT and UNTRACED rows)")

V599 = ("Checker 2026-11-07T19:55Z (T-599 r2 Gate A, merge 9dc3c2d3): split re-added by hand GF 2.901714 - 2.28125 = "
        "0.620464, 1F 1.593362 - 0.385 = 1.208362, 2F 0.42 - 0 = 0.42; residual 2.248826 + B7 0.120452 = 2.369278 = "
        "headline signed (unchanged); RD n4 signed 0 / gross 5.3325 AGREE; own ST7757 read 1F C1 0.075 + C2 0.205 = "
        "0.280 m3 AGREE: PARTIALLY VERIFIED 2 / 4 1F marks (GF marks not re-measured this run); UP-CONC-JOINT-001 1.0.0 "
        "LEAD_ADOPTED under Q-62 A (not owner-approved); residuals UNRESOLVED -> T-600; nothing released")
V605 = ("Checker 2026-11-07T20:57Z (T-605 Gate A, merge c2db2962): own ST7757 read by handle: 180C 1.00 x 1.00 less "
        "notch 0.40 x 0.35 = 0.86 m2, 180F 3.40 x 2.70; concrete F9 5.049 + FN 0.258 = 5.307 m3 AGREE engine; notch "
        "0.042 m3 = his FN row excess ENGINE_RIGHT (own calc); blinding F9 10.44 / FN 1.30 / overlap 0.19 / union 11.55 m2 "
        "AGREE; side forms 7.46 .. 7.685 m2 AGREE, stays HELD (OQ10); F8 1B24 / FN 10F0 pair not re-measured; F9 / FN "
        "pair concrete + blinding VERIFIED (2 / 2); CONC.FOOTING line PARTIALLY VERIFIED; no quantity change")
V607 = ("Checker 2026-11-07T20:57Z (T-607 Gate A, merge ad0290c2): own recount ST7757 ST p.4 / p.5: at most 50 fronts + "
        "2 closings, no ST-01 front beyond the 56-edge census, his +7 has no drawn ST basis; R2 storey estimate +1 / +3 "
        "/ +3 = 7 x 1.20 = 8.40 lm AGREE; steps 7 nr / 8.40 lm and nosing 8.40 lm = ONE cause C-T607-1, counted once; "
        "ENGINE_RIGHT on the count; mechanism R1 / R2 named, not chosen; the 56 census split per flight on the 3 "
        "architectural plans not re-proved (merged T-434 / T-598 basis reused)")
V610 = ("Checker 2026-11-07T21:59Z (T-610 Gate A, merge 14cf2579): own ST7757 read GF B1 x B27 zone 0.014761 m2 AGREE; "
        "B27 ledger 4.931529 m2 = drawn band - triangle - 0.001077: 'billed twice' NOT supported, billed once at B1 0.40: "
        "ENGINE_WRONG_UNDER; B1 component -0.005295 VERIFIED, B27 +0.011252 .. +0.012547 bounded: FR-T610-1 net -0.005957 "
        ".. -0.007252 m3 PARTIALLY VERIFIED; FR-T610-2 / -3 / -4 worker-measured; nothing wired")
V611 = ("Checker 2026-11-07T21:56Z (T-611 Gate A, engine push a930d8f2): FR-T606-1 = 4.000 + 7.020 + 2 x 0.05 + 0.05 = "
        "11.170 lm VERIFIED (4 / 4 components); manifest V13 FIN.SKIRTING 209.728592 - 11.170 = 198.558592 lm AGREE; "
        "candidate unchanged (manifest only)")
V612 = ("Checker 2026-11-07T22:02Z (T-612 Gate A, merge 66d3ad9c): own P7757 read: GF gross outline 55.906096 lm, face "
        "56.006096 lm = engine gross: +0.10 face vs outline ENGINE_RIGHT VERIFIED (2 / 2 readings); 72.92 - 55.906096 = "
        "17.013904 and split bound 3.056952 .. 8.506952 AGREE: GF -17.013904 UNRESOLVED (undrawn split CANDIDATE, never a "
        "reading); 1F curved -0.73933 / 2F -0.70 stay UNRESOLVED")

TAG_STEP, TAG_ROOM, TAG_PACK = "F-T609-1", "F-T609-2", "F-T609-3"
TAG_JOINT, TAG_STAIR, TAG_ROOM2 = "F-T609-4", "F-T609-5", "F-T609-6"


def load(p: Path) -> dict:
    pin = PINS.get(p)
    if pin and Z.sha(p) != pin:
        raise StatementError(f"{p.relative_to(ROOT)}: sha256 differs from its pin")
    return json.loads(p.read_text(encoding="utf-8"))


# ================================================================================ section of record ===============
LEVELS = A9.LEVELS + ("sections_v9",)


def all_sections(st: dict) -> dict:
    out = {}
    for lv in LEVELS + ("sections_v10",):
        for c in st.get(lv, []):
            if c["section_id"] in out:
                raise StatementError(f"{c['section_id']}: section id twice in the statement")
            out[c["section_id"]] = c
    return out


def supersession(st: dict) -> dict:
    sup = {}
    for k in ("supersedes_v7", "supersedes_v8", "supersedes_v9", "supersedes_v10"):
        sup.update({a: b for a, b in st.get(k, {}).items() if not a.startswith("beside")})
    return sup


def section_of_record(st: dict, sid: str) -> dict:
    return all_sections(st)[A9.of_record(sid, supersession(st))]


def _one(rows: list[dict], pred, what: str) -> dict:
    hit = [r for r in rows if pred(r)]
    if len(hit) != 1:
        raise StatementError(f"{what}: found {len(hit)} rows, not 1")
    return hit[0]


def _no_pct_beside_held(sec: dict) -> None:
    if sec.get("difference_pct_of_reference") is not None and any(r["class"] == "HELD" for r in sec["rows"]):
        raise StatementError(f"{sec['section_id']}: a % beside a HELD row (R-T609-1 (e))")


# ================================================================================ (a) T-602 door steps (lm) ========
def t602_marble_lm(st9: dict, d602: dict, d604: dict, verdict: str = V602) -> tuple[dict, list]:
    old = section_of_record(st9, "T-577/marble-lm")
    rec = d602["reconciliation"]
    if d602["sign"] != "ours - his":
        raise StatementError("T-602 sign is not 'ours - his'")
    row = _one(old["rows"], lambda r: r["class"] == "UNRESOLVED" and r["name"].startswith("EXT: his ") and
               "door-step pieces" in r["name"], "marble lm door-step UNRESOLVED row")
    if D(row["delta"]) != D(rec["v8_before"]["unresolved_lm"]):
        raise StatementError("T-602 'v8_before' unresolved is not the statement row's delta (R-T609-1 (a))")
    split = rec["v8_unresolved_split"]
    om = _one(split, lambda p: "ENGINE_OMISSION" in p["part"], "T-602 omission part")
    rest = [p for p in split if p is not om]
    if len(rest) != 1 or om["status"] != "DRAWING-CONFIRMED" or rest[0]["status"] != "UNRESOLVED":
        raise StatementError("T-602 split is not one DRAWING-CONFIRMED ENGINE_OMISSION + one UNRESOLVED residual")
    oid = om["part"].split(" ", 1)[0]
    # T-602 sign ours - his: residual -0.40 -> statement (reference - engine) +0.40; the omitted step is in his block
    if -D(rec["residual_lm"]) != D(rest[0]["lm"]) or D(om["lm"]) + D(rest[0]["lm"]) != D(row["delta"]):
        raise StatementError("T-602 parts do not re-add to the row in the statement sign")
    step = _one(rec["ours_steps"], lambda x: x["opening"] == oid, f"T-602 step {oid}")
    if D(step["lm"]) != D(om["lm"]):
        raise StatementError(f"{oid}: omitted part is not its drawn step length")
    fr = _one(d602["fix_rows"], lambda f: oid in f["row"], f"fix row for {oid}")
    ds = d604["door_steps"]
    v11, dl = ds["v11_family"], ds["delta"]
    if D(v11["lm"]) + D(dl["lm"]) != D(rec["ours_lm"]) or v11["nr"] + dl["nr"] != rec["ours_nr"] or \
            D(v11["riser_m2"]) + D(dl["riser_m2"]) != D(rec["ours_riser_m2"]) or D(dl["lm"]) != D(om["lm"]) or \
            D(dl["riser_m2"]) != D(step["riser_m2"]):
        raise StatementError("manifest V12 door-step family is not V11 + the omitted step (R-T609-1 (a))")
    his = d602["his"]
    if D(his["lm"]) - D(v11["lm"]) != D(row["delta"]):
        raise StatementError("his door-step lm less the V11 family is not the statement row")
    splits = {row["name"]: [
        {"name": f"EXT {oid} step (drawn edge pair at its gap {step['lm']}, riser {step['riser_m']}): in his "
                 f"{his['lm']} lm block, no line on our side: ENGINE_OMISSION ({fr['id']} in manifest V12 beside; "
                 f"stone / finish HELD, so it becomes a HELD line at its point bound {step['lm']} when wired, never "
                 "valued by default)",
         "delta": D(om["lm"]), "class": "ENGINE_WRONG", "evidence": CV, "tag": TAG_STEP,
         "kind_of_cause": "ENGINE_OMISSION", "fix_row": fr["id"], "when_wired": f"HELD point bound {step['lm']} lm"},
        {"name": f"EXT: his {his['nr']} door-step pieces {his['lm']} lm vs our {rec['ours_nr']} step elements "
                 f"{rec['ours_lm']} lm (V11 family {v11['lm']} + {oid} {step['lm']}): his rows carry no door id, "
                 "matching by figure refused (R-T577-1): UNRESOLVED (candidate causes named by T-602, none "
                 "attributable)",
         "delta": D(rest[0]["lm"]), "class": "UNRESOLVED", "evidence": PV, "tag": TAG_STEP, "kind_of_cause": "SCOPE",
         "candidate_causes_not_attributed": rest[0].get("candidate_causes_not_attributed", [])}]}
    new_id = old["section_id"].split("@", 1)[0] + "@V10"
    sec, moves, pairs = A8.restate(old, new_id, splits, {}, verdict, lambda x: x["evidence_status"])
    if pairs:
        raise StatementError("T-602 restatement produced PAIRED parts")
    by = {b["opening"]: b for b in ds["v12_family"]["by_opening"]}
    if set(by) != {x["opening"] for x in rec["ours_steps"]} or \
            sum((D(str(b["lm"])) for b in by.values()), D(0)) != D(rec["ours_lm"]):
        raise StatementError("manifest V12 step family is not the T-602 openings")
    prev = old["beside"]["door_steps_t592"]
    sec["beside"] = dict(old["beside"])
    sec["beside"]["door_steps_t602"] = {
        "element": prev["element"], "was": {"ours_lm": s(D(v11["lm"])), "nr": v11["nr"],
                                             "his_minus_ours_lm": row["delta"]},
        "ours_lm": rec["ours_lm"], "ours_nr": rec["ours_nr"], "ours_riser_m2": rec["ours_riser_m2"],
        "his_lm": his["lm"], "his_nr": his["nr"], "his_minus_ours_lm": s(-D(rec["residual_lm"])),
        "count": (f"his {his['nr']} = ours {rec['ours_nr']}: FREELANCER_RIGHT on the count" if his["nr"] ==
                  rec["ours_nr"] else f"his {his['nr']} vs ours {rec['ours_nr']}: UNRESOLVED"),
        "omitted_step": {"opening": oid, "lm": step["lm"], "riser_m2": step["riser_m2"],
                         "status": "DRAWING-CONFIRMED geometry; stone / finish HELD", "fix_row": fr["id"],
                         "manifest": "V12 beside (F-T604-2: no payable line yet)"},
        "manifest_family_v11_to_v12": {"lm": [v11["lm"], rec["ours_lm"]], "nr": [v11["nr"], rec["ours_nr"]],
                                       "riser_m2": [v11["riser_m2"], rec["ours_riser_m2"]]},
        "pct": None, "verification": V604}
    _no_pct_beside_held(sec)
    return sec, moves


# ================================================================================ (a) T-606 room skirting (lm) ======
T606_EVID = {"LIV-WELL": CV, "LIV-VOID": WP, "residual": PV}
T606_NAMES = {
    "LIV-WELL": "1F living / open stair hall: dog-leg well walls above the drawn landing edge (E 4.15, N 2.50, W 4.50, "
                "column returns 0.10) in our gross; his outline closes on the landing edge 2.85; no floor at +5.50, our "
                "net already removes the enclosure (shaft 9.05 + W13 / W25): ENGINE_RIGHT (T-606, Checker CONFIRMED)",
    "LIV-VOID": "1F living / open stair hall: stair-opening zone, column notch faces 0.20 (our gross walks the walls "
                "along the opening with columns 300E / 3008, his the opening edges 11.02): the merged split, ENGINE_WRONG "
                "proposed; the 11.17 lm wall face itself is F-T606-1 (beside, fix row pending); Checker: column 3008 "
                "east return 0.05 faces the 1F floor (not re-split here)",
    "residual": "1F living / open stair hall: no drawn reading reproduces his 43.78 / 38.96 (closest floor-only outline "
                "43.84 / 38.988): UNRESOLVED residual (his row carries no dimensions)"}


def t606_skirting_room(st9: dict, d606: dict) -> tuple[dict, list]:
    old = section_of_record(st9, "T-574/skirting-room")
    if old["section_id"] != "T-574/skirting-room@V9":
        raise StatementError(f"room skirting of record is {old['section_id']}, not the V9 restatement")
    row = _one(old["rows"], lambda r: r["name"].startswith("1F living / open stair hall: engine room outline"),
               "1F living outline row")
    room = _one(d606["rooms"], lambda r: r["room"].startswith("1F living"), "T-606 1F living")
    # T-606 sign ours - his; statement sign his - ours
    if -D(room["gap"]) != D(row["delta"]) or row["class"] != "UNRESOLVED":
        raise StatementError("T-606 1F living gap is not the statement's UNRESOLVED outline row (R-T609-1 (a))")
    parts = []
    for c in room["causes"]:
        cls = c["verdict"]
        want = {"LIV-WELL": "ENGINE_RIGHT", "LIV-VOID": "ENGINE_WRONG", "residual": "UNRESOLVED"}[c["id"]]
        if cls != want:
            raise StatementError(f"T-606 {c['id']}: merged class {cls}, statement map {want} (R-T609-1 (a))")
        parts.append({"name": T606_NAMES[c["id"]], "delta": -D(c["lm"]), "class": cls, "evidence": T606_EVID[c["id"]],
                      "tag": TAG_ROOM, "kind_of_cause": "OUTLINE", "t606_cause": c["id"]})
    if sum((p["delta"] for p in parts), D(0)) != D(row["delta"]):
        raise StatementError("T-606 causes do not re-add to the 1F living row")
    # the other T-606 rooms are already their own UNRESOLVED rows in V9: checked, not moved
    others = {"GF open room": "GF open room", "1F curved": "1F curved east bed room", "2F corridor": "2F corridor"}
    for k, pre in others.items():
        rm = _one(d606["rooms"], lambda r, k=k: r["room"].startswith(k), f"T-606 {k}")
        hit = [r for r in old["rows"] if r["name"].startswith(pre) and r["class"] == "UNRESOLVED"]
        if len(hit) != 1 or -D(rm["gap"]) != D(hit[0]["delta"]):
            raise StatementError(f"T-606 {k}: its residual is not the statement's UNRESOLVED row")
    if s(sum((-D(r["gap"]) for r in d606["rooms"]), D(0))) != s(-D(d606["t574_unresolved"])):
        raise StatementError("T-606 rooms do not re-add to the T-574 residual")
    sec, moves, _ = A8.restate(old, "T-574/skirting-room@V10", {row["name"]: parts}, {}, V606,
                               lambda x: x["evidence_status"])
    _no_pct_beside_held(sec)
    return sec, moves


# ================================================================================ (b) T-180 packs (m3) ===========
# Each pack: the beam rows (T-545/beams@V9 names) it covered, the marks, the Checker's per-mark state and the engine
# figure per mark as the Checker quoted it (the pack's own record), the verdict line. Only 'full' rows move evidence.
PACKS = [
    {"pack": "P01", "scope": "GF / 1F COUNT marks (B28, CA; B25, B19, B5)", "verdict": VP01,
     "rows": {"GF: COUNT": {"state": "ALREADY_VERIFIED"}, "1F: COUNT": {"state": "ALREADY_VERIFIED"}},
     "findings": []},
    {"pack": "P02 2F", "scope": "2F THROUGH_SUPPORT per mark", "verdict": VP02_2F,
     "rows": {"2F: THROUGH_SUPPORT": {"state": "FULL", "marks": {"B3": ("0.028", "AGREE"), "B8": ("0.120", "AGREE"),
                                                                    "B15": ("0.240", "AGREE"), "B1": ("0.032", "AGREE")}}},
     "findings": ["F-C-P02-1: 2F B1 0.032 = column footprint 0.176 netted with an un-rowed drawn B1 run 0.144 (no "
                  "quantity change; names the cause of the 2F 0.420 m3 the joint rows leave UNRESOLVED, T-600 input)"]},
    {"pack": "P02 1F", "scope": "1F THROUGH_SUPPORT per mark", "verdict": VP02_1F,
     "rows": {"1F: THROUGH_SUPPORT": {"state": "PARTIAL", "open": ["CB10", "CB11", "CB12"]}},
     "findings": ["F-C-P02-2: 1F B1 / CB13 agree in sum only"]},
    {"pack": "P02 GF", "scope": "GF THROUGH_SUPPORT per mark", "verdict": "not read (T-180 slot open)",
     "rows": {"GF: THROUGH_SUPPORT": {"state": "NOT_READ"}}, "findings": []},
    {"pack": "P03 1F", "scope": "1F RUN_COUNT (B4 + B6)", "verdict": VP03_1F,
     "rows": {"1F: RUN_COUNT": {"state": "FULL", "marks": {"B6": ("1.577773", "AGREE"), "B4": ("0.331173", "AGREE")}}},
     "findings": ["F-C-P03-1: B4 run / ring split restated, net binding-invariant"]},
    {"pack": "P03 GF", "scope": "GF RUN_COUNT (B1 runs)", "verdict": VP03_GF,
     "rows": {"GF: RUN_COUNT": {"state": "ENGINE_WRONG_FINDING", "finding": "F-C-P03-2", "m3": "-0.005295"}},
     "findings": ["F-C-P03-2 (Checker 16:57 reading): B27 / B1 band overlap 0.014761 m2 'billed twice', B1 component "
                  "-0.005295 m3; restated by T-610 (MERGED 14cf2579): billed ONCE at B1 0.40 where B27 0.85 is drawn, "
                  "ENGINE_WRONG_UNDER, FR-T610-1 net -0.005957 .. -0.007252 m3 PARTIALLY VERIFIED; fix rows not wired, "
                  "NOT applied (R-T609-1 (c))",
                  "F-C-P03-3: GF B1 residual by cause spans the RUN_COUNT and UNTRACED rows: no statement row is split "
                  "on it (not re-derivable from committed data)"]},
]


def pack_amends(sec: dict, packs: list[dict] = PACKS) -> tuple[dict, list]:
    """(b): evidence-only amends for rows a pack fully covered; every other covered row stays as it is."""
    amends, ev_moves, seen = {}, [], set()
    rows = {r["name"]: r for r in sec["rows"]}
    for p in packs:
        for name, cov in p["rows"].items():
            if name not in rows:
                raise StatementError(f"{p['pack']}: row '{name}' not in {sec['section_id']}")
            if name in seen and cov["state"] == "FULL":
                raise StatementError(f"{name}: promoted by two packs")
            seen.add(name)
            r = rows[name]
            if cov["state"] == "ALREADY_VERIFIED":
                if r["evidence_status"] != CV:
                    raise StatementError(f"{name}: recorded as already verified but stamped {r['evidence_status']}")
                continue
            if cov["state"] != "FULL":
                continue
            if any(st != "AGREE" for _, st in cov["marks"].values()):
                raise StatementError(f"{p['pack']} {name}: a mark not AGREE cannot promote (R-T609-1 (b))")
            tot = sum((D(v) for v, _ in cov["marks"].values()), D(0))
            if tot != abs(D(r["delta"])):
                raise StatementError(f"{p['pack']} {name}: marks re-add to {tot}, row {r['delta']} (R-T609-1 (b))")
            if set(cov) - {"state", "marks"}:
                raise StatementError(f"{p['pack']} {name}: a pack may not set {sorted(set(cov) - {'state', 'marks'})}")
            if r["evidence_status"] == CV:
                raise StatementError(f"{name}: already CHECKER_VERIFIED, nothing to promote")
            amends[name] = {"tag": TAG_PACK, "evidence": CV, "set": {
                "evidence_pack": p["pack"], "evidence_was": r["evidence_status"]}}
            ev_moves.append({"tag": TAG_PACK, "section_id": "T-545/beams@V10", "row": name, "class": r["class"],
                             "delta": r["delta"], "from": r["evidence_status"], "to": CV, "pack": p["pack"],
                             "verdict": p["verdict"]})
    return amends, ev_moves


def t180_beams(st9: dict, packs: list[dict] = PACKS) -> tuple[dict, list, list]:
    old = section_of_record(st9, "T-545/beams")
    if old["section_id"] != "T-545/beams@V9":
        raise StatementError(f"beams of record is {old['section_id']}, not the V9 restatement")
    amends, ev_moves = pack_amends(old, packs)
    verdicts = {n: next(p["verdict"] for p in packs if n in p["rows"]) for n in amends}
    sec = copy.deepcopy(old)
    out_rows = []
    for r in sec["rows"]:
        if r["name"] in amends:
            a = amends[r["name"]]
            r.update(a["set"])
            r["tag_v10"] = a["tag"]
            A7.stamp(r, a["evidence"], verdicts[r["name"]])
        out_rows.append(r)
    sec["rows"], sec["section_id"], sec["restates"] = out_rows, "T-545/beams@V10", old["section_id"]
    for r_old, r_new in zip(old["rows"], sec["rows"]):
        if (r_old["name"], r_old["delta"], r_old["class"]) != (r_new["name"], r_new["delta"], r_new["class"]):
            raise StatementError(f"{r_new['name']}: a pack moved a name, delta or class (R-T609-1 (b))")
    Z.close_section(sec)
    if (sec["reference_total"], sec["engine_valued"], sec["difference"]) != \
            (old["reference_total"], old["engine_valued"], old["difference"]):
        raise StatementError("T-545/beams@V10: totals moved")
    return sec, ev_moves, [{k: v for k, v in p.items()} for p in packs]


def t610_restatement(d610: dict) -> dict:
    """F-C-P03-2 as T-610 merged it: billed once (UNDER), B1 component the Checker's -0.005295 m3; nothing wired."""
    f = d610["F_C_P03_2"]
    fr = {x["id"]: x for x in d610["fix_rows"]}
    if f["verdict"] != "ENGINE_WRONG_UNDER" or D(str(f["checker_B1_m3"])) != D("0.005295") or \
            D(str(f["zone_m2"])) != D("0.014761") or D(str(fr["FR-T610-1"]["engine_minus_physical_m3"])) != \
            D(str(f["engine_minus_physical_m3"])):
        raise StatementError("T-610: F-C-P03-2 is not the merged UNDER restatement (B1 0.005295, zone 0.014761)")
    return {"finding": "F-C-P03-2", "restated_by": "T-610", "billed": "ONCE (UNDER, not double)",
            "zone_m2": s(D(str(f["zone_m2"]))), "physical_m3": s(D(str(f["physical_m3"]))),
            "fix_rows_m3": {k: s(D(str(v["engine_minus_physical_m3"]))) for k, v in sorted(fr.items())},
            "fr_t610_1_bound_m3": ["-0.005957", "-0.007252"], "applied": False, "evidence_moved": False,
            "verification": V610}


def packs_beside(packs: list[dict], ev_moves: list[dict], d589: dict, d610: dict | None = None) -> dict:
    out = []
    for p in packs:
        key = p["pack"].split(" ", 1)[0]
        if key not in d589["packs"]:
            raise StatementError(f"{key}: not a T-589 pack")
        rows = {}
        for n, cov in p["rows"].items():
            mv = [m for m in ev_moves if m["row"] == n]
            rows[n] = {"state": cov["state"], "evidence_moved": bool(mv),
                       **({"marks_m3": {k: v for k, (v, _) in cov["marks"].items()}} if "marks" in cov else {}),
                       **({"open_marks": cov["open"]} if "open" in cov else {}),
                       **({"finding": cov["finding"], "finding_m3": cov["m3"], "applied": False}
                          if "finding" in cov else {})}
        e = {"pack": p["pack"], "t589_title": d589["packs"][key]["title"], "scope": p["scope"], "rows": rows,
             "findings": p["findings"], "verdict": p["verdict"]}
        if d610 is not None and any(cov.get("finding") == "F-C-P03-2" for cov in p["rows"].values()):
            e["t610_restatement"] = t610_restatement(d610)
        out.append(e)
    return {"block_id": "T-180/packs-P01-P03@V10", "kind": "PACK_VERDICT_BESIDE", "report": "T-180 (T-589 packs)",
            "valued": "0", "candidate_line": False, "pct": None, "packs": out,
            "class_moves": 0, "evidence_moves": len(ev_moves),
            "note": "a pack moves evidence only, on a row it covered fully with every mark AGREE and the engine marks "
                    "re-adding to the row (R-T609-1 (b)); classes and deltas unchanged by a pack; the joint rows take the "
                    "merged T-599 r2 split separately (R-T609-1 (f)); ENGINE_WRONG findings wait for their fix rows"}


# ================================================================================ (c) F-T606-1 pending fix ========
def t606_pending(d606: dict, d604: dict, d611: dict | None = None) -> dict:
    f = d606["finding"]
    rel, ifc = D(f["released_V3_0_58"]), D(f["if_confirmed"])
    if rel - D(f["lm"]) != ifc:
        raise StatementError("F-T606-1: worker after-figure does not re-add")
    chk = D("11.170")                   # Checker re-measure: worker 11.22 less column 3008 east return 0.05
    if D(f["lm"]) - D("0.05") != chk:
        raise StatementError("F-T606-1: Checker 11.170 is not the worker figure less the 3008 east return 0.05")
    v12 = d604["overlay"]["v12_vs_v11_totals"]["FIN.SKIRTING|lm"]
    if D(v12["before"]["released"]) != rel:
        raise StatementError("F-T606-1: manifest V11 FIN.SKIRTING is not the T-606 released figure")
    after_v12 = D(v12["after"]["released"])
    v13 = None
    if d611 is not None:
        t = d611["overlay"]["v13_vs_v12_totals"]["FIN.SKIRTING|lm"]
        if D(t["before"]["released"]) != after_v12 or D(t["after"]["released"]) != after_v12 - chk or \
                (t["before"]["held_n"], t["before"]["excluded_n"]) != (t["after"]["held_n"], t["after"]["excluded_n"]):
            raise StatementError("F-T606-1: manifest V13 FIN.SKIRTING is not V12 - 11.170 with HELD / excluded unchanged")
        v13 = {"before": s(D(t["before"]["released"])), "after": s(D(t["after"]["released"])),
               "held_n": t["after"]["held_n"], "excluded_n": t["after"]["excluded_n"], "verification": V611}
    out = {"block_id": "T-606/F-T606-1@V10", "kind": "PENDING_FIX_BESIDE", "report": "T-606", "valued": "0",
            "candidate_line": False, "applied": False, "pct_of_line_family_not_a_verdict": None,
            "line": f["line"], "item": "FIN.SKIRTING", "unit": "lm",
            "worker_lm": f["lm"], "checker_lm": s(chk), "checker_minus_worker": "-0.05 (column 3008 east return "
                                                                                   "faces the 1F floor)",
            "class": "ENGINE_WRONG (Checker CONFIRMED on 11.170)",
            "candidate_v3_0_58": {"before": s(rel), "after_if_wired": s(rel - chk)},
            "after_manifest_v12": {"before": s(after_v12), "after_if_wired": s(after_v12 - chk)},
            "fix_row": ("none yet: lane I fix row needed (deduction 'STAIR-OPENING-NO-FLOOR' on the 1F living line)"
                        if v13 is None else "FR-T606-1 in manifest V13 (T-611 MERGED a930d8f2; deduction VERIFIED 4 / 4 "
                                            "components); manifest only: candidate V3.0.58 unchanged, so not applied "
                                            "here"),
            "statement_effect": "none now: the room-skirting section compares his gross with the candidate net; when "
                                "the fix row is wired the engine column falls 11.170 lm and a new ENGINE_RIGHT row (his "
                                "gross along the opening edges, no floor) must be named in the next statement",
            "verification": V606}
    if v13 is not None:
        out["manifest_v13"] = v13
    return out


# ================================================================================ (d) T-597 B1 plan side =========
def t597_beside(st9: dict, d597: dict) -> dict:
    nc = _one(st9["not_comparable"], lambda b: b.get("block_id") == "T-565/earthworks", "T-565 NOT_COMPARABLE")
    exc = _one(nc["families"], lambda f: f["item_code"] == "STR.EARTH.EXCAVATION", "B1-02 excavation family")
    if exc["his"] != "NO_ROW" or exc["class"] != "NOT_COMPARABLE":
        raise StatementError("B1-02 excavation is not NOT_COMPARABLE with his NO_ROW")
    rows = {r["id"]: r for r in d597["b1_rows"]}
    pits = rows["B1-02 valued excavation: Z1-PITS-24"]
    pool = rows["B1-02 valued excavation: Z1-POOL"]
    if s(D(str(pits["engine_m3"])) + D(str(pool["engine_m3"]))) != s(D(exc["engine_valued"])):
        raise StatementError("T-597 pits + pool engine m3 are not the B1-02 valued excavation")
    z = d597["pits_zone"]
    union, ssum, own = D(str(z["union_m2"])), D(str(z["sum_m2"])), D(str(z["own_in_plot_m2"]))
    if D(str(z["in_plot_m2"])) + D(str(z["beyond_plot_m2"])) != union or \
            D(str(z["in_plot_m2"])) - D(str(z["given_up_m2"]["Z1-POOL envelope"])) != own or \
            ssum - union != D(str(z["overlap_m2"])):
        raise StatementError("T-597 pit zone does not re-add (union = in plot + beyond; own = in plot - pool share)")
    notch = D("0.40") * D("0.35")
    drawn_sum = (ssum - notch).normalize()
    if (drawn_sum, drawn_sum - union) != (D("129.43"), D("0.195625")):
        raise StatementError("F-C-T597-1: drawn sum / overlap are not 129.43 / 0.195625")
    if D(str(pits["plan_delta_m2"])) != own - D(str(pits["engine_plan_m2"])):
        raise StatementError("T-597: pits plan delta is not plan - engine plan")
    plan = []
    for r in d597["b1_rows"]:
        e = {"id": r["id"], "plan_m2": r.get("plan_m2"), "plan_status": r["plan_status"], "depth": r["depth"]}
        if "engine_plan_m2" in r:
            e["engine_plan_m2"] = r["engine_plan_m2"]
        if r.get("plan_m2") is None and "HELD" not in r["plan_status"]:
            raise StatementError(f"{r['id']}: blank plan without HELD (never 0)")
        plan.append(e)
    status = {"Z1-PITS-24": "VERIFIED (plan only; Checker own read)", "Z1-POOL": "VERIFIED (plan only; Checker own read)",
              "Z1-TRENCH-EXT-GB-MAIN": "PARTIALLY VERIFIED (worker + T-484 read; not re-measured by the Checker)",
              "Z1-PIT-FF": "HELD", "Z1-PIT-F10F": "HELD", "depth (pits)": "HELD S01 (ESTIMATED founding, RFI-S01)"}
    return {"block_id": "T-597/b1-plan-side@V10", "kind": "PLAN_SIDE_BESIDE", "report": "T-597",
            "beside_not_comparable": "T-565/earthworks", "his": "NO_ROW", "class": "NOT_COMPARABLE (unchanged)",
            "valued": "0", "candidate_line": False, "pct": None, "unit_plan": "m2", "unit_volume": "m3",
            "plan_rows": plan, "statuses": status,
            "pits_zone_m2": {"union": s(union), "in_plot": s(D(str(z["in_plot_m2"]))),
                             "beyond_plot": s(D(str(z["beyond_plot_m2"]))),
                             "pool_share_given_up": s(D(str(z["given_up_m2"]["Z1-POOL envelope"]))),
                             "own_in_plot": s(own), "sum_json": s(ssum), "overlap_json": s(ssum - union),
                             "sum_drawn_F_C_T597_1": s(drawn_sum), "overlap_drawn_F_C_T597_1": s(drawn_sum - union),
                             "note": "F-C-T597-1: FN 180C drawn notched 0.40 x 0.35 under F9 (sum 129.57 took its 1.00 "
                                     "x 1.00 box); the union is identical; the T-597 json is kept as merged"},
            "pool_envelope_m2": {"in_plot": s(D(str(d597["pool"]["envelope_in_plot_m2"]))),
                                 "beyond_plot": s(D(str(d597["pool"]["envelope_beyond_plot_m2"])))},
            "engine_difference": {"plan_m2": s(D(str(pits["plan_delta_m2"]))),
                                  "m3_at_S01": s(D(str(pits["m3_delta_at_S01"]))), "class": "ENGINE_WRONG immaterial "
                                  "(pool arc polygonised); no row moves: the family stays NOT_COMPARABLE, valued line "
                                  "unchanged"},
            "verification": V597}


# ================================================================================ (e) evidence audit ===============
V10_BASE = {"T-577/marble-lm@V10": "T-577/marble-lm@V8", "T-574/skirting-room@V10": "T-574/skirting-room@V9",
            "T-545/beams@V10": "T-545/beams@V9", "T-551/columns@V10": "T-551/columns@V9",
            "T-576/columns-GF@V10": "T-576/columns-GF@V9", "T-576/columns-1F@V10": "T-576/columns-1F@V9",
            "T-576/columns-GF-reading-10E0-C7@V10": "T-576/columns-GF-reading-10E0-C7@V9",
            "T-576/columns-1F-reading-10E0-C7@V10": "T-576/columns-1F-reading-10E0-C7@V9",
            "T-584/stair-steps-lm@V10": "T-584/stair-steps-lm", "T-584/stair-steps-nr@V10": "T-584/stair-steps-nr"}
JOINT_SUB_EVID = {"matched": PV, "residual": WP}
T612_EVID = {"GF-FACE-VS-OUTLINE": CV, "residual": PV}


def expected_v10(sid: str, r: dict, expected_v9) -> str:
    """The verdict map for V10 rows, independent of the stamps the adapters wrote (R-T587-1 (a))."""
    tag = r.get("tag", "")
    if tag == TAG_STEP:
        return CV if r["class"] == "ENGINE_WRONG" else PV
    if tag == TAG_ROOM:
        return T606_EVID[r["t606_cause"]]
    if tag == TAG_ROOM2:
        return T612_EVID[r["t612_cause"]]
    if tag == TAG_STAIR:
        return PV                       # T-607: ST recount own; the 56 census split per flight reused, not re-proved
    if tag == TAG_JOINT and "joint_sub" in r:
        return JOINT_SUB_EVID[r["joint_sub"]]
    if r.get("tag_v10") == TAG_PACK:
        return CV
    if sid.endswith("@V10"):
        return expected_v9(V10_BASE[sid], r)   # amended joint rows keep the evidence their V9 verdict gives
    return expected_v9(sid, r)


# ================================================================================ (f) T-599 r2 joint rule (m3) =====
JOINT_TERMS = (": JOINT_HEAD", ": THROUGH_SUPPORT")
JOINT_SECTIONS_V9 = ("T-551/columns@V9", "T-576/columns-GF@V9", "T-576/columns-1F@V9",
                     "T-576/columns-GF-reading-10E0-C7@V9", "T-576/columns-1F-reading-10E0-C7@V9")
NESTED_OR_ALT_V10 = ("T-576/columns-GF@V10", "T-576/columns-1F@V10", "T-576/columns-GF-reading-10E0-C7@V10",
                     "T-576/columns-1F-reading-10E0-C7@V10")
JOINT_RULE_TXT = "UP-CONC-JOINT-001@1.0.0 (LEAD_ADOPTED under Q-62 A; not owner-approved)"


def _is_joint(r: dict) -> bool:
    return r["name"].endswith(JOINT_TERMS) and r["class"] == "UNRESOLVED"


def t599_index(st9: dict, d599: dict) -> tuple[dict, list]:
    """T-599 rows keyed by (section of record in V9, row name); a record whose row is not in its section of record is
    audited beside (a superseded reading), never added (R-T609-1 (f))."""
    if d599["rules_index"]["status"] != "LEAD_ADOPTED" or not d599["rule"].startswith("UP-CONC-JOINT-001@1.0.0"):
        raise StatementError("T-599: rule is not UP-CONC-JOINT-001@1.0.0 LEAD_ADOPTED")
    sup, secs = supersession(st9), all_sections(st9)
    idx: dict = {}
    beside = []
    for r in d599["rows"]:
        rec = A9.of_record(r["section_id"], sup)
        if r["name"] not in [x["name"] for x in secs[rec]["rows"]]:
            beside.append({"t599_section": r["section_id"], "row": r["name"], "sub": r["sub"], "delta_m3": r["delta_m3"],
                           "outcome": r["outcome"], "of_record": rec,
                           "why": "superseded reading: its row is not in the section of record (audited, never added)"})
            continue
        val = (r["sub"], D(r["delta_m3"]), r["outcome"], r["class_after"])
        lst = idx.setdefault((rec, r["name"]), [])
        if val not in lst:
            lst.append(val)
    for k, lst in idx.items():
        if len({v[0] for v in lst}) != len(lst):
            raise StatementError(f"T-599 {k}: two different records for one sub-row (levels disagree)")
    return idx, beside


def _joint_plan(sid9: str, src: dict, idx: dict) -> tuple[dict, dict, list]:
    splits, amends, kept = {}, {}, []
    for r in src["rows"]:
        recs = idx.get((sid9, r["name"]))
        if not _is_joint(r):
            if recs and any(v[2] != "UNRESOLVED_APART" or v[3] != r["class"] for v in recs):
                raise StatementError(f"{sid9} '{r['name']}': a T-599 record on a non-joint row moves it")
            continue
        if not recs:
            raise StatementError(f"{sid9} '{r['name']}': UNRESOLVED joint row with no T-599 record (R-T609-1 (f))")
        sub = {v[0]: v for v in recs}
        if set(sub) == {"whole"}:
            _, d, outc, ca = sub["whole"]
            if (outc, ca) != ("SOURCED", "RULE_DIFFERENCE") or d != D(r["delta"]):
                raise StatementError(f"{sid9} '{r['name']}': whole record {outc} {d} is not SOURCED at the row's delta")
            amends[r["name"]] = {"tag": TAG_JOINT, "evidence": r["evidence_status"], "set": {
                "class": "RULE_DIFFERENCE", "joint_outcome": "SOURCED", "joint_rule": JOINT_RULE_TXT,
                "tag_v9": r.get("tag")}}
        elif set(sub) == {"matched", "residual"}:
            m, res = sub["matched"], sub["residual"]
            if m[1] + res[1] != D(r["delta"]) or (m[2], m[3]) != ("SOURCED", "RULE_DIFFERENCE") or \
                    (res[2], res[3]) != ("UNRESOLVED_RESIDUAL", "UNRESOLVED"):
                raise StatementError(f"{sid9} '{r['name']}': matched + residual do not re-add to the row, or a part is "
                                     "promoted beyond its record (R-T609-1 (f))")
            if m[1] > D(r["delta"]) or m[1] <= 0:
                raise StatementError(f"{sid9} '{r['name']}': matched joint outside 0 .. the row")
            if r["evidence_status"] != WP:
                raise StatementError(f"{sid9} '{r['name']}': beam joint row not worker-proposed in V9")
            st = r["name"].split(":", 1)[0]
            splits[r["name"]] = [
                {"name": f"{st}: THROUGH_SUPPORT matched joint: his beam rows run through the column heads; our column "
                         f"owns the joint to the slab top, beam face to face ({JOINT_RULE_TXT}); equal to the {st} "
                         "column JOINT_HEAD of record (T-551, statement V9): RULE_DIFFERENCE SOURCED (T-599 r2)",
                 "delta": m[1], "class": "RULE_DIFFERENCE", "evidence": JOINT_SUB_EVID["matched"], "tag": TAG_JOINT,
                 "joint_sub": "matched", "joint_outcome": "SOURCED", "joint_rule": JOINT_RULE_TXT},
                {"name": f"{st}: THROUGH_SUPPORT residual beyond the matched joint: not explained by the rule "
                         "(UNRESOLVED, T-600; alternative column readings named in T-599, never chosen)",
                 "delta": res[1], "class": "UNRESOLVED", "evidence": JOINT_SUB_EVID["residual"], "tag": TAG_JOINT,
                 "joint_sub": "residual", "to_task": "T-600"}]
        elif set(sub) == {"residual"}:
            if sub["residual"][1] != D(r["delta"]) or sub["residual"][3] != "UNRESOLVED":
                raise StatementError(f"{sid9} '{r['name']}': residual-only record is not the whole row")
            kept.append({"section_id": sid9, "row": r["name"], "delta_m3": r["delta"],
                         "kept": "matched joint 0: the whole row is the residual, UNRESOLVED -> T-600, row unchanged"})
        else:
            raise StatementError(f"{sid9} '{r['name']}': T-599 subs {sorted(sub)} not mapped")
    return splits, amends, kept


def t599_joint(st9: dict, d599: dict, beams_packs: dict) -> tuple[list, list, list, dict]:
    """(f): the beam section after the packs and the five column sections restated on the merged T-599 r2 split.
    Returns (sections, moves of record, moves nested / alternative, joint record)."""
    idx, beside = t599_index(st9, d599)
    secs9 = all_sections(st9)
    targets = [("T-545/beams@V9", beams_packs)] + [(sid, secs9[sid]) for sid in JOINT_SECTIONS_V9]
    out, mv_rec, mv_alt, kept = [], [], [], []
    for sid9, src in targets:
        splits, amends, k = _joint_plan(sid9, src, idx)
        kept += k
        new_id = sid9[:-3] + "@V10"
        # A8.restate compares the totals as strings; V9 printed one difference unnormalised ('8.77' for 8.7700):
        # compare on the normalised form, then keep V9's own text (value equal, checked)
        src_n = copy.deepcopy(src)
        src_n["difference"] = s(D(src["reference_total"]) - D(src["engine_valued"]))
        if D(src_n["difference"]) != D(src["difference"]):
            raise StatementError(f"{sid9}: V9 difference is not reference - engine")
        sec, mv, pairs = A8.restate(src_n, new_id, splits, amends, V599, lambda x: x["evidence_status"])
        sec["difference"] = src["difference"]
        if pairs:
            raise StatementError(f"{new_id}: the joint restatement produced PAIRED parts")
        sec["restates"] = sid9
        _no_pct_beside_held(sec)
        (mv_alt if new_id in NESTED_OR_ALT_V10 else mv_rec).extend(dict(m, unit=sec["unit"]) for m in mv)
        out.append(sec)
    used = {(sid, r["name"]) for sid, src in targets for r in src["rows"]}
    if set(idx) - used:
        raise StatementError(f"T-599 records with no statement row: {sorted(set(idx) - used)}")
    rd = [m for m in mv_rec if m["to"] == "RULE_DIFFERENCE"]
    want = d599["headline_after"]["m3"]["RULE_DIFFERENCE"]
    got = (len(rd), sum((D(m["delta"]) for m in rd), D(0)), sum((abs(D(m["delta"])) for m in rd), D(0)))
    if got != (want["n"], D(want["signed"]), D(want["gross"])) or len(mv_rec) != len(rd):
        raise StatementError(f"T-599: of-record moves {got} are not the rule's headline RULE_DIFFERENCE {want}")
    of_rec = [c for c in out if c["section_id"] not in NESTED_OR_ALT_V10]
    res = sum((D(r["delta"]) for c in of_rec for r in c["rows"] if r["class"] == "UNRESOLVED" and
               (r.get("joint_sub") == "residual" or r["name"] == "2F: THROUGH_SUPPORT")), D(0))
    if res != D(d599["headline_by_cause_m3"]["UNRESOLVED_pair_residual_T600"]["signed"]):
        raise StatementError(f"T-599: residual of record {res} is not the rule's pair residual")
    old = st9["structural_provenance_v9"]["joint_rule_pointer"]
    if (old["rule_id"], old["status"], old["in_rules_index"]) != ("UP-CONC-JOINT-001", "REJECTED", True):
        raise StatementError("V9 joint pointer is not the REJECTED pointer T-599 r2 left for V10 to restate")
    record = {"rule_id": "UP-CONC-JOINT-001", "version": d599["rules_index"]["version"],
              "rules_index_status": d599["rules_index"]["status"], "task": "T-599 r2", "merge": "9dc3c2d3",
              "status": "MERGED (rule LEAD_ADOPTED under Q-62 A; not owner-approved)", "status_line": V599,
              "v9_pointer": "structural_provenance_v9.joint_rule_pointer (REJECTED 13:58Z) carried byte-equal in V9 and "
                            "superseded by this record",
              "residual_of_record_m3": s(res), "residual_to": "T-600",
              "untraced_apart_m3": "0.120452 (GF B7, unchanged UNRESOLVED)",
              "rows_kept_whole_residual": kept, "superseded_audited_beside": beside,
              "nested_alternative_note": "nested measured sets and alternative readings take the same outcome; their "
                                         "moves are reported apart and never added to the sections of record"}
    return out, mv_rec, mv_alt, record


# ================================================================================ (g) T-607 one cause, once ========
STAIR_ROWS = {"T-584/stair-steps-lm": lambda r: r["name"].startswith("ST-01: 7 pieces beyond every reading of his count"),
              "T-584/stair-steps-nr": lambda r: r["name"] == "ST-01: pieces beyond every reading of his count"}


def t607_steps(st9: dict, d607: dict) -> tuple[list, list, dict]:
    c = _one(d607["causes"], lambda x: x["id"] == "C-T607-1", "T-607 cause C-T607-1")
    if c["verdict"] != "ENGINE_RIGHT" or c["edges_in_governing_count"] != 0 or d607["sign"] != "his - ours":
        raise StatementError("T-607: C-T607-1 is not ENGINE_RIGHT with no governing edge (his - ours)")
    per, once = d607["shared"]["per_line"], d607["shared"]["total_once"]
    out, moves = [], []
    for sid, pred in STAIR_ROWS.items():
        old = section_of_record(st9, sid)
        if old["section_id"] != sid:
            raise StatementError(f"{sid}: section of record is {old['section_id']}")
        r = _one(old["rows"], pred, f"{sid} ST-01 beyond-count row")
        q, unit = per[sid]
        if unit != old["unit"] or D(str(q)) != D(r["delta"]) or r["class"] != "UNRESOLVED":
            raise StatementError(f"{sid}: T-607 {q} {unit} is not the statement's UNRESOLVED row (R-T609-1 (a))")
        am = {r["name"]: {"tag": TAG_STAIR, "evidence": PV, "set": {
            "class": "ENGINE_RIGHT", "cause_id": "C-T607-1", "his_mechanism": c["his_mechanism"],
            "once": "C-T607-1 feeds steps lm / nr and the nosing beside: one cause, restated in each line, never "
                    "summed across lines (R-T609-1 (g))"}}}
        sec, mv, _ = A8.restate(old, sid + "@V10", {}, am, V607, lambda x: x["evidence_status"])
        _no_pct_beside_held(sec)
        out.append(sec)
        moves += [dict(m, unit=sec["unit"]) for m in mv]
    if (once[0], D(str(once[1]))) != (int(per["T-584/stair-steps-nr"][0]), D(per["T-584/stair-steps-lm"][0])):
        raise StatementError("T-607: total once is not the per-line figure")
    nos = _one(st9["beside_v9"], lambda b: b.get("report") == "T-598" and "units" in b, "V9 T-598 nosing beside")
    lm, nr = nos["units"]["lm"], nos["units"]["nr"]
    q_lm, q_nr = D(per["T-598/nosing@V9 lm"][0]), int(per["T-598/nosing@V9 nr"][0])
    if D(lm["by_class"]["UNRESOLVED"]) != q_lm or nr["gap_his_minus_ours"] != q_nr or D(lm["residual"]) != 0:
        raise StatementError("T-607: the V9 nosing beside does not carry C-T607-1 as its UNRESOLVED")
    bc = {k: D(v) for k, v in lm["by_class"].items()}
    bc["ENGINE_RIGHT"] = bc.get("ENGINE_RIGHT", D(0)) + bc.pop("UNRESOLVED")
    if sum(bc.values(), D(0)) != D(lm["gap_his_minus_ours"]):
        raise StatementError("T-607: nosing classes do not re-add to its gap")
    beside = {"block_id": "T-598/nosing@V10", "kind": "CROSS_REFERENCE", "report": "T-598 + T-607",
              "supersedes_beside": nos.get("block_id", "T-598 nosing beside (V9)"), "valued": "0",
              "candidate_line": False, "difference_added": False, "pct": None, "cause_id": "C-T607-1",
              "units": {"lm": {"his": lm["his"], "ours_valued": lm["ours_valued"],
                               "gap_his_minus_ours": lm["gap_his_minus_ours"],
                               "by_class": {k: s(v) for k, v in sorted(bc.items())}, "residual": "0",
                               "was_by_class": lm["by_class"]},
                        "nr": {"his": nr["his"], "ours_valued": nr["ours_valued"], "gap_his_minus_ours": q_nr,
                               "gap_class": "ENGINE_RIGHT (C-T607-1: no drawn piece beyond the 56 governing risers)",
                               "was_gap_class": nr["gap_class"]}},
              "once": "the same 7 nr / 8.4 lm as T-584/stair-steps-lm@V10 / -nr@V10; summing over the lines (16.8 lm / "
                      "14 nr) refused",
              "also_feeds": d607["shared"]["also_feeds"], "verification": V607}
    return out, moves, beside


def refuse_cause_summed(st: dict, cause: str = "C-T607-1") -> None:
    """(g): a shared cause appears once per line; a headline or beside total that adds its lines is refused."""
    hits = [(c["section_id"], r["unit"]) for c in st.get("sections_v10", []) for r in c["rows"]
            if r.get("cause_id") == cause]
    if len(hits) != len(set(hits)):
        raise StatementError(f"{cause}: entered twice in one line (R-T609-1 (g))")
    for b in st.get("beside_v10", []):
        if b.get("cause_id") == cause and b.get("difference_added") is not False:
            raise StatementError(f"{cause}: a beside block adds the shared cause to a column (R-T609-1 (g))")


# ================================================================================ (a) T-612 GF open room (lm) =====
T612_NAMES = {
    "GF-FACE-VS-OUTLINE": "engine face 56.006096 vs the drawn gross outline 55.906096 (face on the band / curb line "
                          "with columns notched, outline on the south facade and west wall): +0.10 lm in our gross on "
                          "virtual edges that carry no skirting: ENGINE_RIGHT (T-612, Checker VERIFIED 2 / 2 readings)",
    "residual": "his rows 58.16 + 14.76 = 72.92 vs the drawn gross outline 55.906096: no drawn reading reproduces both; "
                "an undrawn split counted in both rows would explain 3.056952 .. 8.506952 lm (CANDIDATE, never a "
                "reading; his rows carry no dimensions): UNRESOLVED (T-612)"}


def t612_room(sec10: dict, d612: dict) -> tuple[dict, list]:
    rm = _one(d612["rooms"], lambda r: r["room"].startswith("GF open room"), "T-612 GF open room")
    row = _one(sec10["rows"], lambda r: r["name"].startswith("GF open room") and r["class"] == "UNRESOLVED" and
               r.get("kind_of_cause") == "OUTLINE", "GF open room UNRESOLVED outline row")
    # T-612 sign ours - his (as T-606); statement sign his - ours
    if -D(rm["gap"]) != D(row["delta"]) or D(d612["t606_remainder"]["GF open room"]) != D(rm["gap"]):
        raise StatementError("T-612 GF gap is not the statement's UNRESOLVED outline row (R-T609-1 (a))")
    pre = row["name"].split(":", 1)[0] + ": "
    parts = []
    for c in rm["causes"]:
        want = {"GF-FACE-VS-OUTLINE": "ENGINE_RIGHT", "residual": "UNRESOLVED"}[c["id"]]
        if c["verdict"] != want:
            raise StatementError(f"T-612 {c['id']}: merged class {c['verdict']}, statement map {want} (R-T609-1 (a))")
        parts.append({"name": pre + T612_NAMES[c["id"]], "delta": -D(c["lm"]), "class": want,
                      "evidence": T612_EVID[c["id"]], "tag": TAG_ROOM2, "kind_of_cause": "OUTLINE",
                      "t612_cause": c["id"]})
    if sum((p["delta"] for p in parts), D(0)) != D(row["delta"]):
        raise StatementError("T-612 causes do not re-add to the GF open room row")
    for k in ("1F curved", "2F corridor"):
        rr = _one(d612["rooms"], lambda r, k=k: r["room"].startswith(k), f"T-612 {k}")
        hit = [r for r in sec10["rows"] if r["name"].startswith(k) and r["class"] == "UNRESOLVED"]
        if len(hit) != 1 or -D(rr["gap"]) != D(hit[0]["delta"]):
            raise StatementError(f"T-612 {k}: its residual is not the statement's UNRESOLVED row")
    sec, moves, _ = A8.restate(sec10, sec10["section_id"], {row["name"]: parts}, {}, V612,
                               lambda x: x["evidence_status"])
    sec["restates"] = sec10["restates"]
    _no_pct_beside_held(sec)
    return sec, moves


# ================================================================================ (h) T-605 footing overlap =======
def t605_beside(st9: dict, d605: dict) -> dict:
    sec = section_of_record(st9, "T-551/footing-line")
    if "headline_v9" in st9 and any(h["section_id"] == sec["section_id"] for h in st9["headline_v9"]):
        raise StatementError("T-551/footing-line is in the evidence regime: restate it, not beside (R-T609-1 (h))")
    r = _one(sec["rows"], lambda x: x["name"].startswith("footing line: OVERLAP FN notch"), "footing overlap row")
    notch = D("0.40") * D("0.35") * D("0.30")
    v = _one(d605["verdicts"], lambda x: x["item"] == "footing concrete", "T-605 footing concrete verdict")
    c = d605["concrete"]
    if D(r["delta"]) != notch or r["class"] != "ENGINE_RIGHT" or D(str(c["schedule_minus_drawn_m3"])) != notch or \
            D(str(v["engine_m3"])) != D(str(v["own_m3"])) or D(str(v["his_m3"])) - D(str(v["engine_m3"])) != notch \
            or D(str(c["engine_pads_m3"])) != D(str(c["pads_drawn_once_m3"])):
        raise StatementError("T-605: the 0.042 m3 notch is not the statement row, his excess and engine = own")
    b = d605["blinding"]
    if D(str(b["sum_m2"])) - D(str(b["overlap_m2"])) != D(str(b["union_m2"])) or \
            D(str(b["engine_minus_own_m3"])) != 0:
        raise StatementError("T-605: blinding union does not re-add or engine differs from own")
    fw = d605["formwork_notched_pair"]
    return {"block_id": "T-605/footing-overlap@V10", "kind": "VERDICT_BESIDE", "report": "T-605", "valued": "0",
            "candidate_line": False, "pct": None, "section_of_record": sec["section_id"], "row": r["name"],
            "row_class": r["class"] + " (unchanged)", "row_delta_m3": r["delta"],
            "evidence": "F9 / FN 180C pair concrete + blinding VERIFIED (2 / 2 components, Checker own read); the "
                        "section predates the evidence stamps (R-T587-1 covers V6+ sections): no stamp is invented, "
                        "the row is unchanged (R-T609-1 (h)); CONC.FOOTING line PARTIALLY VERIFIED",
            "concrete_m3": {"engine": s(D(str(v["engine_m3"]))), "own": s(D(str(v["own_m3"]))),
                            "his": s(D(str(v["his_m3"]))), "notch": s(notch),
                            "pads_engine": s(D(str(c["engine_pads_m3"]))),
                            "pads_schedule_rect_sum_refused": s(D(str(c["pads_schedule_rect_sum_m3"])))},
            "blinding_m2": {"union": s(D(str(b["union_m2"]))), "sum": s(D(str(b["sum_m2"]))),
                            "overlap": s(D(str(b["overlap_m2"]))), "in_plot": s(D(str(b["in_plot_m2"])))},
            "side_forms_m2": {"bound": [s(D(str(fw["interface_none_m2"]))), s(D(str(fw["interface_once_m2"])))],
                              "status": "HELD (OQ10 pour sequence; engine footing FW lines HELD blank, never 0)"},
            "not_remeasured": "F8 1B24 / FN 10F0 blinding overlap 0.005625 m2 (worker-measured)",
            "verification": V605}
