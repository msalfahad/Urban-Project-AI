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

TAG_STEP, TAG_ROOM, TAG_PACK = "F-T609-1", "F-T609-2", "F-T609-3"


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
     "findings": ["F-C-P03-2: B27 / B1 band overlap 0.014761 m2 billed twice: ENGINE_WRONG -0.005295 m3, fix row "
                  "for the Lead, NOT applied (R-T609-1 (c))",
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


def packs_beside(packs: list[dict], ev_moves: list[dict], d589: dict) -> dict:
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
        out.append({"pack": p["pack"], "t589_title": d589["packs"][key]["title"], "scope": p["scope"], "rows": rows,
                    "findings": p["findings"], "verdict": p["verdict"]})
    return {"block_id": "T-180/packs-P01-P03@V10", "kind": "PACK_VERDICT_BESIDE", "report": "T-180 (T-589 packs)",
            "valued": "0", "candidate_line": False, "pct": None, "packs": out,
            "class_moves": 0, "evidence_moves": len(ev_moves),
            "note": "a pack moves evidence only, on a row it covered fully with every mark AGREE and the engine marks "
                    "re-adding to the row (R-T609-1 (b)); classes and deltas unchanged; the joint rows stay UNRESOLVED "
                    "(T-599 r2 not merged); ENGINE_WRONG findings wait for their fix rows"}


# ================================================================================ (c) F-T606-1 pending fix ========
def t606_pending(d606: dict, d604: dict) -> dict:
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
    return {"block_id": "T-606/F-T606-1@V10", "kind": "PENDING_FIX_BESIDE", "report": "T-606", "valued": "0",
            "candidate_line": False, "applied": False, "pct_of_line_family_not_a_verdict": None,
            "line": f["line"], "item": "FIN.SKIRTING", "unit": "lm",
            "worker_lm": f["lm"], "checker_lm": s(chk), "checker_minus_worker": "-0.05 (column 3008 east return "
                                                                                   "faces the 1F floor)",
            "class": "ENGINE_WRONG (Checker CONFIRMED on 11.170)",
            "candidate_v3_0_58": {"before": s(rel), "after_if_wired": s(rel - chk)},
            "after_manifest_v12": {"before": s(after_v12), "after_if_wired": s(after_v12 - chk)},
            "fix_row": "none yet: lane I fix row needed (deduction 'STAIR-OPENING-NO-FLOOR' on the 1F living line)",
            "statement_effect": "none now: the room-skirting section compares his gross with the candidate net; when "
                                "the fix row is wired the engine column falls 11.170 lm and a new ENGINE_RIGHT row (his "
                                "gross along the opening edges, no floor) must be named in the next statement",
            "verification": V606}


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
def expected_v10(sid: str, r: dict, expected_v9) -> str:
    tag = r.get("tag", "")
    if tag == TAG_STEP:
        return CV if r["class"] == "ENGINE_WRONG" else PV
    if tag == TAG_ROOM:
        return T606_EVID[r["t606_cause"]]
    if r.get("tag_v10") == TAG_PACK:
        return CV
    if sid.endswith("@V10"):
        base = {"T-577/marble-lm@V10": "T-577/marble-lm@V8", "T-574/skirting-room@V10": "T-574/skirting-room@V9",
                "T-545/beams@V10": "T-545/beams@V9"}[sid]
        return expected_v9(base, r)
    return expected_v9(sid, r)
