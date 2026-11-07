"""T-594: reconciled-quantities statement V8 adapters. V8 = statement V7 (T-587, rebuilt read only, every V7 key
byte-equal) + restated sections for the merged T-581 r2 (lintel width basis: D-GF-09 DRAWING CONFLICT), T-585 (yard
skirting scope; stair-flight forms and the MS1-T winder bound), T-592 (external door / gate steps: one payable length)
and the Lead's register rulings of 2026-11-07 08:15, plus beside blocks for T-589 (structural closure classes per
section) and the T-595 restatements (F-C-T583-1 ring side bars on both faces; F-T589-1 S02 footing bound). Research,
unwired: computes no new quantity; reads the committed, sha256-pinned research outputs only (no drawing, workbook or
client data). Sign as V4 .. V7: reference - engine; + = in the reference only.

R-T594-1 (proposed, every villa). A statement restating a section on a later merged report:
  (a) SPLIT, NEVER EDIT: a moved amount is a split of ONE earlier row into parts that re-add to that row's delta
      exactly; every part names its class, evidence status (from the verdict line, R-T587-1 (a)) and tag; the section
      totals (reference, engine valued) are unchanged and the residual stays 0; a part that would change a total is
      refused;
  (b) PAIRED PARTS: when a later ruling makes one element of OUR side (a valued line in one group) the counterpart of a
      reference cell in another group, both parts are split out as PAIRED and leave the rows for a beside 'agree pair'
      record; the PAIRED parts of a section must net 0, else refused (no amount disappears);
  (c) AMEND = SAME DELTA: a row may change class, name, bound or note with its delta unchanged; a class change is a
      reclass entry (delta = the row delta, 0 for a count-neutral width reading) and a HELD row never becomes 0
      without a bound;
  (d) the earlier section stays byte-equal in its version and is listed as superseded; the restated section carries
      '@V8' and 'restates';
  (e) a beside block restating a beside block (T-583 -> T-595 bar lows, T-572 -> T-595 footing low) states before /
      after and the verdict, is valued 0 and never enters a column.
"""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T587 = ROOT / "research/agents_t587"
if str(T587) not in sys.path:
    sys.path.insert(0, str(T587))
import t587_adapters as A7  # noqa: E402  (T-587, read only)

Z = A7.Z
D = Decimal
StatementError = Z.StatementError
s, row, close_section = Z.s, Z.row, Z.close_section
CV, PV, WP = A7.CV, A7.PV, A7.WP

T581_JSON = ROOT / "research/agents_t581/out/T581_WIDTH_BASIS.json"
T585_JSON = ROOT / "research/agents_t585/out/T585_SKIRTING_FOLLOWUPS.json"
T589_JSON = ROOT / "research/agents_t589/out/T589_CLOSABLE_PACK.json"
T592_JSON = ROOT / "research/agents_t592/out/T592_DOOR_STEPS.json"
T593_JSON = ROOT / "research/agents_t593/out/WIRING_MANIFEST_V10.json"
T595_JSON = ROOT / "research/agents_t595/out/T595_RESTATEMENTS.json"
T577_JSON = ROOT / "research/agents_t577/out/T577_MARBLE_RECONCILE.json"
PINS = {
    T581_JSON: "99682afc4e45666ff3678827201c35cc561c2c7cdbadb8e5187be38bba59b103",
    T585_JSON: "207d4c6a35172786a54caaa1732351cac23947ed3e69228fb815a8538361bb7e",
    T589_JSON: "9f315d706a86997373d8c6e18a6163953ff6ca946694e30e57bdcea722c54aeb",
    T592_JSON: "c32be0ed6d17ff05e3a116fafb3c0bb241a90d9cdfaf602877e16977e256f689",
    T593_JSON: "c05827ef4c27e365e05f565ed89c46493c95ccaf826a490342a96f83e1dcd3fe",
    T595_JSON: "80d32d7051ee9926201b252d761d20ca1c4609465eb992a67583cbbeb1567964",
    T577_JSON: "b1b684a3478982b7c80d6f25a6acf0c8dea4dfaa80449f0866e373cee2ddb320",
}

# Checker verdicts and Lead rulings (board, 2026-11-07), quoted as classes and evidence only
V581 = ("Checker 2026-11-07 05:51 (T-581 r2 Gate A): D-GF-09 wall ends 46.9 / 946.9 mm inside the D120 frame 0 / 1000 "
        "on both faces (own DXF read): DRAWING CONFLICT, UNRESOLVED / HELD 1.20 .. 1.50 (designer item); lintel table "
        "re-summed by hand 91.5 lm (60 nr) low / 91.8 lm high: T-571 AT_MOST 91.5 is NOT an upper bound, restated "
        "91.5 .. 91.8; 25 other openings DRAWING-CONFIRMED; ENGINE_RIGHT vs his 1.00 withdrawn -> UNRESOLVED")
V585 = ("Checker 2026-11-07 05:58 (T-585 Gate A): yard 'no printed base' CONFIRMED on the DXF (83 strings, 0 name a "
        "base), face lengths worker-measured (0 / 46): yard 81.32 lm RULE_DIFFERENCE / FREELANCER_SCOPE ACCEPTED, "
        "PARTIALLY VERIFIED; flights two forms 17.009049 / 23.300481 and winders 2.350 .. 2.620191 arithmetic AGREE "
        "(PARTIALLY VERIFIED); E1 landing 3.500 lm geometry VERIFIED, class open (F-C-T585-1)")
V589 = ("Checker 2026-11-07 07:58 (T-589 Gate A): classification only, no component promoted; B10 59 / B11 13 / B1 19 "
        "components re-add to the V6 sources (beams -0.227179, columns 8.770, footing line 9.936, lift walls 2.400 "
        "m3 AGREE); own read ST p.7: ring side bars on both faces (F-C-T583-1 closed); F-T589-1 S02 low 2.176 -> "
        "1.960 m3 AGREE from the owner text")
V592 = ("Checker 2026-11-07 07:59 (T-592 Gate A): own DXF read: house wall gaps 1.000 / 0.900 / 1.000 / 0.900 = 3.800 "
        "lm nr 4, edges 3.500 attribute, D-GF-09 riser 0.15 DRAWING-CONFIRMED, riser 0.570 m2: VERIFIED research "
        "quantity (not wired); gate gap 1.000 AGREE, outer level not re-read by hand: gate PARTIAL; vs his 7.70 lm "
        "(6 pieces, no door id): UNRESOLVED (SCOPE), no %")
V593 = ("Checker 2026-11-07 09:56 (T-593 Gate A): manifest V10 DOOR_STEPS rows re-derived (house 3.800 lm beside the "
        "4 owning threshold lines, gate own row PARTIAL), E1 landing NO_LINE NOT_IN_DRAWING, stair skirting forms "
        "17.009049 / 23.300481 lm AGREE")
V595 = ("Checker 2026-11-07 09:56 (T-595 Gate A): own read ST7757.dxf DETAIL OF DOME: 4 x d14 side bars per ring "
        "section CONFIRMED; east ring low 0.122518 -> 0.144289 t, bounded rows low 0.767783 -> 0.789554 t (T-595 json "
        "0.789555: unrounded parts); F10 + F S02 1.960 .. 2.275 m3, T-572 footing bounded low 7.8445 -> 7.6285 m3; "
        "highs HELD")
REG0815 = ("Lead 2026-11-07 08:15 ELEMENT_REGISTER: EXTERNAL DOOR STEP payable length CLOSED (one length = stone in "
           "the wall gap = T-325 strip, house 3.800 lm nr 4, nosing 3.500 attribute); GATE STEP owner trade marble / "
           "stone door-step family, 1.000 lm / 0.150 m2 PARTIAL, own row, never folded into the house total; E1 "
           "LANDING SKIRTING NOT_IN_DRAWING (exterior, no printed base; ENGINE_OMISSION proposal withdrawn)")

PAIRED = "PAIRED"


def load(p: Path) -> dict:
    pin = PINS.get(p)
    if pin and Z.sha(p) != pin:
        raise StatementError(f"{p.relative_to(ROOT)}: sha256 differs from its pin")
    return json.loads(p.read_text(encoding="utf-8"))


# ================================================================================ (a)-(d) generic restatement ======
def restate(old: dict, new_id: str, splits: dict, amends: dict, verdict: str, evid_unchanged) -> tuple[dict, list,
                                                                                                         list]:
    """Restate section `old` as `new_id`. splits: row name -> list of parts {name, delta, class, evidence, tag, **kw}
    (class PAIRED leaves the rows); amends: row name -> {tag, evidence, set: {field: value}}. Untouched rows keep their
    content, stamped by evid_unchanged(row) when they carry no evidence status. Returns (section, reclasses, pairs)."""
    sec = copy.deepcopy(old)
    names = [r["name"] for r in sec["rows"]]
    for n in list(splits) + list(amends):
        if names.count(n) != 1:
            raise StatementError(f"{old['section_id']}: row '{n[:60]}' found {names.count(n)} times, not once")
    if set(splits) & set(amends):
        raise StatementError(f"{old['section_id']}: a row both split and amended")
    rows, moves, pairs = [], [], []
    for r in sec["rows"]:
        n = r["name"]
        if n in splits:
            parts = splits[n]
            if sum((D(p["delta"]) for p in parts), D(0)) != D(r["delta"]):
                raise StatementError(f"{old['section_id']}: parts of '{n[:60]}' do not re-add to its delta "
                                     f"{r['delta']} (R-T594-1 (a))")
            for p in parts:
                p = dict(p)
                cls, ev, tag = p.pop("class"), p.pop("evidence"), p.pop("tag")
                pname, pdelta = p.pop("name"), p.pop("delta")
                if cls == PAIRED:
                    pairs.append({"tag": tag, "section_id": new_id, "from_row": n, "name": pname,
                                  "delta": s(D(pdelta)), "evidence_status": ev, "verdict": verdict, **p})
                else:
                    keep = {k: v for k, v in r.items() if k == "kind_of_cause" and k not in p}
                    nr = row(pname, D(pdelta), cls, r["unit"], f"{new_id} (split of: {n[:80]})", verdict, **keep,
                             was_class=r["class"], was_row=n[:120], tag=tag, **p)
                    rows.append(A7.stamp(nr, ev, verdict))
                if cls != r["class"]:
                    moves.append({"tag": tag, "section_id": new_id, "row": pname[:120], "from": r["class"],
                                  "to": cls, "delta": s(D(pdelta)), "verdict": verdict})
        elif n in amends:
            a = amends[n]
            was = r["class"]
            for k, v in a["set"].items():
                if k == "delta":
                    raise StatementError(f"{old['section_id']}: an amend may not change a delta (R-T594-1 (c))")
                r[k] = v
            r["tag"] = a["tag"]
            if r["class"] != was:
                r["was_class"] = was
                moves.append({"tag": a["tag"], "section_id": new_id, "row": r["name"][:120], "from": was,
                              "to": r["class"], "delta": r["delta"], "verdict": verdict})
            rows.append(A7.stamp(r, a["evidence"], verdict))
        else:
            if "evidence_status" not in r:
                A7.stamp(r, evid_unchanged(r), r.get("verification", old.get("verification", "")))
            rows.append(r)
    if sum((D(p["delta"]) for p in pairs), D(0)) != 0:
        raise StatementError(f"{old['section_id']}: PAIRED parts net {sum(D(p['delta']) for p in pairs)}, not 0 "
                             "(R-T594-1 (b))")
    sec["rows"] = rows
    sec["section_id"] = new_id
    sec["restates"] = old["section_id"]
    close_section(sec)
    if (sec["reference_total"], sec["engine_valued"], sec["difference"]) != \
            (old["reference_total"], old["engine_valued"], old["difference"]):
        raise StatementError(f"{new_id}: totals moved (restate, never rewrite: R-T594-1 (a) / R-T587-1 (c))")
    return sec, moves, pairs


def _one(rows: list[dict], pred, what: str) -> dict:
    hit = [r for r in rows if pred(r)]
    if len(hit) != 1:
        raise StatementError(f"{what}: found {len(hit)} rows, not 1")
    return hit[0]


# ================================================================================ T-581 lintels (nr; lm beside) =====
def t581_lintels(v6: dict, d581: dict) -> tuple[dict, list]:
    old = _one(v6["sections_v6"], lambda c: c["section_id"] == "T-571/lintel-count-implied", "V6 T-571 section")
    op = _one(d581["openings"], lambda o: o["id"] == "D-GF-09", "T-581 D-GF-09")
    if op["state"] != "UNRESOLVED" or [D(str(x)) for x in op["bound_m"]] != [D("0.90"), D("1.00")]:
        raise StatementError("T-581: D-GF-09 is not UNRESOLVED with the bound 0.90 .. 1.00")
    others = [o for o in d581["openings"] if o["id"] != "D-GF-09"]
    if any(o["state"] != "DRAWING-CONFIRMED" for o in others):
        raise StatementError("T-581: an opening other than D-GF-09 is not DRAWING-CONFIRMED")
    rs = d581["restated_owner_0.15"]
    lo, hi = rs["table_low"], rs["table_high"]
    tot = {k: (sum(sum(v.values()) for v in t["at_most"].values()),
               s(sum((D(L) * sum(v.values()) for L, v in t["at_most"].items()), D(0)))) for k, t in
           (("low", lo), ("high", hi))}
    if tot["low"] != (60, "91.5") or tot["high"] != (60, "91.8") or rs["census_at_most_is_upper_bound"] is not False \
            or (D(str(rs["lm_low"])), D(str(rs["lm_high"]))) != (D("91.5"), D("91.8")):
        raise StatementError(f"T-581: restated tables {tot} are not 60 nr 91.5 / 91.8 lm")
    eng_v6 = {L: v["engine_at_most"] for L, v in old["by_length"].items()}
    if eng_v6 != {L: sum(v.values()) for L, v in lo["at_most"].items()}:
        raise StatementError("T-581: the low reading is not the V6 engine table (count unchanged at 0.90)")
    name = "D-GF-09 vs FL-GF-EXT-15: WIDTH_READ"
    r = _one(old["rows"], lambda x: x["name"] == name, "T-571 D-GF-09 row")
    if r["class"] != "RULE_DIFFERENCE" or r["by_length_nr"] != {"1.2": -1, "1.5": 1}:
        raise StatementError("T-571 D-GF-09 row is not the V6 RULE_DIFFERENCE 1.20 vs his 1.50")
    amends = {name: {"tag": "F-T594-1", "evidence": CV, "set": {
        "class": "UNRESOLVED", "state_ours": "HELD (DRAWING CONFLICT, bound 1.20 .. 1.50)",
        "by_length_nr_at_low_reading": {"1.2": -1, "1.5": 1},
        "by_length_nr_at_high_reading": {},
        "mapped_because": "T-581 r2: masonry 0.90 (wall ends) vs D120 frame 1.00 drawn over the masonry: DRAWING "
                          "CONFLICT, designer item; at 0.90 ours 1.20 vs his 1.50, at 1.00 SAME_PIECE 1.50; neither "
                          "reading chosen (R-T581-1 1.1.0 (2))"}}}
    sec, moves, _ = restate(old, "T-571/lintel-count-implied@V8", {}, amends, V581,
                            lambda x: A7.ev_v6("T-571/", x))
    sec["by_length_engine_readings"] = {
        "low (D-GF-09 0.90)": {L: sum(v.values()) for L, v in lo["at_most"].items()},
        "high (D-GF-09 1.00)": {L: sum(v.values()) for L, v in hi["at_most"].items()}}
    sec["beside_lm"] = dict(old["beside_lm"], engine_at_most="91.5 .. 91.8", engine_at_most_was="91.5",
                            note_v8="T-571 AT_MOST 91.5 lm is not an upper bound (T-581 r2, Checker): 91.5 at the "
                                    "0.90 reading, 91.8 at the 1.00 reading; count 60 nr at both; beside the nr "
                                    "section, never summed with it")
    sec["refused_bases_beside"] = {"frame_clear_lm": s(D(str(d581["beside_frame_clear_refused"]["diff_lm"]))),
                                   "block_overall_lm": s(D(str(d581["beside_block_overall_refused"]["diff_lm"])))}
    return sec, moves


# ================================================================================ T-585 skirting (lm) =============
def t585_outdoor(v6: dict, d585: dict) -> tuple[dict, list]:
    old = _one(v6["sections_v6"], lambda c: c["section_id"] == "T-574/skirting-outdoor", "V6 outdoor skirting")
    y = d585["yard"]
    if y["totals_lm"]["DRAWING-CONFIRMED"] != "0" or y["reconcile"]["gap"] != "-81.32" or \
            len(y["reconcile"]["causes"]) != 1:
        raise StatementError("T-585: yard reconcile is not one SCOPE cause closing -81.32 with 0 DRAWING-CONFIRMED")
    r = _one(old["rows"], lambda x: x["class"] == "UNRESOLVED", "outdoor UNRESOLVED row")
    splits = {r["name"]: [{"name": "OUTDOOR yard skirting: his 81.32 lm is the perimeter typed for his paving row "
                                   "(G13 = C13), a paving outline; no sheet prints an outdoor base (DXF 0 strings), so "
                                   "0 DRAWING-CONFIRMED on our side (R-T585-1, register YARD SKIRTING)",
                           "delta": r["delta"], "class": "RULE_DIFFERENCE", "evidence": PV, "tag": "F-T594-2",
                           "mapped_because": "T-585 RULE_DIFFERENCE / FREELANCER_SCOPE, Checker ACCEPTED on the "
                                             "basis 'no printed base' (his-side reading unconfirmed)"}]}
    sec, moves, _ = restate(old, "T-574/skirting-outdoor@V8", splits, {}, V585, lambda x: A7.ev_v6("T-574/", x))
    t = y["totals_lm"]
    sec["beside"] = {"wall_foot_not_in_drawing_lm": t["NOT_IN_DRAWING_physical_wall_foot"],
                     "under_unprinted_sills_hi_lm": t["NOT_IN_DRAWING_under_unprinted_sills_range_hi"],
                     "unresolved_bound_lm": t["UNRESOLVED_bound"], "no_face_lm": t["NO_FACE"],
                     "yard_face_perimeter_lm": y["closure"]["yard_face_perimeter_lm"],
                     "note": "named, never valued: wall foot NOT_IN_DRAWING (no base); porch / pool-court faces "
                             "UNRESOLVED 0 .. 11.61 while their floor finish is HELD (OD-1); no line (manifest V10 "
                             "NO_LINE row, F-T593-2)"}
    return sec, moves


def t585_stairs(v6: dict, d585: dict) -> tuple[dict, list]:
    old = _one(v6["sections_v6"], lambda c: c["section_id"] == "T-574/skirting-stairs", "V6 stair skirting")
    st = d585["stairs"]
    if (st["two_form_pitch_lm"], st["two_form_zigzag_lm"], st["flight_lo"], st["t574_flight_lo"]) != \
            ("17.009049", "23.300481", "19.359049", "17.009049"):
        raise StatementError("T-585: flight forms / bounds are not the merged figures")
    s1 = st["by_stair"]["ST-01 main"]
    w = _one(s1["held"], lambda h: h["pid"] == "MS1-T.W + MS1-T.N", "T-585 MS1-T winders")
    wlo, whi = D(w["bound"][0]), D(w["bound"][1])
    flight_hi_ex_w = D(s1["flight_hi"]) - whi
    if D(s1["flight_lo"]) != D(s1["pitch_lm"]) + wlo:
        raise StatementError("T-585 ST-01: flight low != pitch + winder low")
    held = _one(old["rows"], lambda x: x["name"].startswith("ST-01 main: flight skirting"), "ST-01 flight row")
    unres = _one(old["rows"], lambda x: x["name"].startswith("ST-01 main: his main-stair row"), "ST-01 residual")
    e1 = _one(old["rows"], lambda x: x["name"].startswith("ST-03 entrance (E1): his entrance row"), "E1 residual")
    if D(held["delta"]) != D(s1["pitch_lm"]) or held["bound"] != [s1["pitch_lm"], None]:
        raise StatementError("V6 ST-01 flight row is not the T-585 pitch form at an open bound")
    splits = {unres["name"]: [
        {"name": unres["name"] + " (V8: less the bounded winder low)", "delta": D(unres["delta"]) - wlo,
         "class": "UNRESOLVED", "evidence": PV, "tag": "F-T594-3"},
        {"name": "ST-01 main: winder corner MS1-T.W + MS1-T.N, both faces walls, bounded 2.350 .. 2.620191 (pitch sum "
                 "between the plans .. whole rise on one side; S-9 count conflict kept): HELD at its low",
         "delta": wlo, "class": "HELD", "evidence": PV, "tag": "F-T594-3", "bound": [s(wlo), s(whi)],
         "kind_of_cause": "HELD"}]}
    amends = {
        held["name"]: {"tag": "F-T594-3", "evidence": PV, "set": {
            "name": "ST-01 main: flight skirting, 10 two-form pieces (pitch 12.238505 | zigzag 16.793338, ORR-007; never "
                    "additive) + held side pieces MS1-L.W2 / MS1-U.E2 / MS1-U.E3b / MS2-L.W2 0 .. their figure; "
                    "winders on their own row (V8)",
            "bound": [s1["pitch_lm"], s(flight_hi_ex_w)]}},
        e1["name"]: {"tag": "F-T594-4", "evidence": PV, "set": {
            "note_v8": "register E1 LANDING SKIRTING (Lead 08:15): the E1 landing walls (3.500 lm geometry VERIFIED) "
                       "are exterior with no printed base: NOT_IN_DRAWING, no line; the 'possible ENGINE_OMISSION' "
                       "named here is withdrawn; whether his 4.37 includes them stays UNRESOLVED (his row unsplit)"}}}
    sec, moves, _ = restate(old, "T-574/skirting-stairs@V8", splits, amends, V585, lambda x: A7.ev_v6("T-574/", x))
    sec["beside"] = dict(old["beside"], flight_forms_lm={"pitch": st["two_form_pitch_lm"],
                                                          "zigzag": st["two_form_zigzag_lm"],
                                                          "note": "two forms of one skirting (ORR-007 picks one); "
                                                                  "never added, never averaged"},
                         flight_lower_bounds_lm_v8=st["flight_lo"],
                         e1_landing_lm_not_in_drawing=d585["e1_landing"]["landing_lm"])
    return sec, moves


# ================================================================================ T-592 door / gate steps (lm) =====
HOUSE_HELD = ("D-GF-01", "D-GF-03", "D-GF-09")      # ARCH.THRESHOLD lines HELD at a point bound (T-577 EXT group)
HOUSE_VALUED = "D-GF-05"                            # FIN.MARBLE.THRESHOLD, valued, T-577 WET group
NO_STEP = ("D-GF-06", "D-GF-07", "D-2F-01")          # T-584 NO_STEP (same level both sides)


def t592_marble_lm(v7: dict, d592: dict, d577: dict, d593: dict) -> tuple[dict, list, list]:
    old = _one(v7["sections_v7"], lambda c: c["section_id"] == "T-577/marble-lm@V7", "V7 marble lm")
    op, tot = d592["openings"], d592["totals"]
    if (tot["house_payable_lm"], tot["house_nr"], tot["gate_payable_lm"]) != ("3.8", 4, "1.0"):
        raise StatementError("T-592: house 3.800 lm nr 4 / gate 1.000 lm not as merged")
    if set(op) != set(HOUSE_HELD) | {HOUSE_VALUED, "D-GF-15"}:
        raise StatementError("T-592: the step openings are not the 4 house doors + the gate")
    pcs = d577["pieces"]
    held_lm = D(0)
    for oid in HOUSE_HELD:
        p = pcs[oid]
        if p["group"] != "EXT" or p["lm"]["status"] != "HELD" or D(p["lm"]["bound"][0]) != D(op[oid]["payable_lm"]) \
                or p["line"] != op[oid]["owning_line"]:
            raise StatementError(f"{oid}: the T-592 step is not its HELD EXT threshold line at the same length")
        held_lm += D(op[oid]["payable_lm"])
    pv = pcs[HOUSE_VALUED]
    if pv["group"] != "WET" or pv["lm"]["status"] != "DRAWING-CONFIRMED" or D(pv["lm"]["value"]) != \
            D(op[HOUSE_VALUED]["payable_lm"]) or pv["line"] != op[HOUSE_VALUED]["owning_line"]:
        raise StatementError("D-GF-05: the T-592 step is not its valued WET threshold line at the same length")
    gate = pcs["D-GF-15"]
    if gate["group"] != "DRY" or gate["lm"]["status"] != "HELD" or op["D-GF-15"]["owning_line"] is not None:
        raise StatementError("D-GF-15: gate threshold line not the HELD DRY line, or T-592 now owns a line")
    nostep = D(0)
    for oid in NO_STEP:
        if pcs[oid]["group"] != "EXT" or pcs[oid]["lm"]["status"] != "HELD":
            raise StatementError(f"{oid}: not a HELD EXT strip")
        nostep += D(pcs[oid]["lm"]["bound"][0])
    ds = d593["door_steps"]
    if (ds["house"]["house_lm"], ds["gate"]["step_lm"], ds["gate"]["in_house_total"]) != ("3.8", "1.0", False):
        raise StatementError("manifest V10: door-step rows not the T-592 figures")
    his = D(d592["compare"]["his_door_steps_lm"])
    rows = old["rows"]
    ext = _one(rows, lambda x: x["name"].startswith("EXT:") and x["class"] == "UNRESOLVED", "EXT UNRESOLVED row")
    exth = _one(rows, lambda x: x["name"].startswith("EXT:") and x["class"] == "HELD", "EXT HELD strips row")
    wet = _one(rows, lambda x: x["name"].startswith("WET:"), "WET row")
    dry = _one(rows, lambda x: x["name"].startswith("DRY: D-GF-15 gate strip"), "DRY held row")
    if D(ext["delta"]) != his or exth["bound"] != ["6.8", "6.8"] or held_lm + nostep != D("6.8"):
        raise StatementError("marble lm: EXT rows are not his 7.70 and the 6.800 HELD strips")
    v_lm = D(op[HOUSE_VALUED]["payable_lm"])
    g_lm = D(op["D-GF-15"]["payable_lm"])
    resid = his - held_lm - v_lm - g_lm
    if resid != his - D(tot["house_payable_lm"]) - g_lm or -resid != D(d592["compare"]["gap_with_gate_lm"]):
        raise StatementError("door steps: residual is not his - (house + gate)")
    pair_name = (f"D-GF-05 door step = its valued WET marble threshold {pv['line']} ({s(v_lm)} lm, T-592 FR-T592-1): "
                 "one element (ELEMENT_REGISTER EXTERNAL DOOR STEP)")
    splits = {
        ext["name"]: [
            {"name": "EXT door steps D-GF-01 / 03 / 09: one element with their ARCH.THRESHOLD lines (stone in the wall "
                     "gap = T-325 strip), HELD at the point bound 1.000 / 0.900 / 0.900 (T-592 pay length VERIFIED; "
                     "manifest V10 FR-T592-1 beside)", "delta": held_lm, "class": "HELD", "evidence": CV,
             "tag": "F-T594-5", "bound": [s(held_lm), s(held_lm)], "kind_of_cause": "HELD"},
            {"name": "EXT gate step D-GF-15 (register GATE STEP: door-step family, own row): 1.000 lm on the HELD-blank "
                     "threshold line L-56acf345; outer level not re-read by hand: PARTIAL (manifest V10 FR-T592-2)",
             "delta": g_lm, "class": "HELD", "evidence": PV, "tag": "F-T594-5", "bound": [s(g_lm), s(g_lm)],
             "kind_of_cause": "HELD"},
            {"name": pair_name, "delta": v_lm, "class": PAIRED, "evidence": PV, "tag": "F-T594-5",
             "side": "reference (part of his 7.70 block, matched as an element set, never by figure)"},
            {"name": "EXT: his 6 door-step pieces 7.70 lm vs our 5 step elements 4.800 lm (house 3.800 + gate "
                     "1.000): his rows carry no door id, matching by figure refused (R-T577-1): UNRESOLVED (SCOPE)",
             "delta": resid, "class": "UNRESOLVED", "evidence": PV, "tag": "F-T594-5", "kind_of_cause": "SCOPE"}],
        wet["name"]: [
            {"name": wet["name"] + " (V8: 13 strips; D-GF-05 is the door-step element, paired in EXT)",
             "delta": D(wet["delta"]) + v_lm, "class": wet["class"], "evidence": wet["evidence_status"],
             "tag": "F-T594-5"},
            {"name": pair_name, "delta": -v_lm, "class": PAIRED, "evidence": PV, "tag": "F-T594-5",
             "side": "engine (valued line)"}]}
    amends = {
        exth["name"]: {"tag": "F-T594-6", "evidence": exth["evidence_status"], "set": {
            "name": "EXT: external strips with NO step (D-GF-06 / 07, D-2F-01: same level both sides, T-584 NO_STEP), "
                    "HELD at the point bound (never 0); the 3 house step strips moved to their own row (V8)",
            "bound": [s(nostep), s(nostep)]}},
        dry["name"]: {"tag": "F-T594-6", "evidence": dry["evidence_status"], "set": {
            "name": "DRY: A-GF-01 arch strip (held by name, T-377; 1.000 x 0.150 beside, NOT applied, T-327); the "
                    "D-GF-15 gate strip is the gate step element, carried in the EXT gate row (V8, one element one "
                    "row)"}}}
    sec, moves, pairs = restate(old, "T-577/marble-lm@V8", splits, amends, V592, lambda x: x["evidence_status"])
    sec["beside"] = dict(old["beside"])
    sec["beside"]["door_steps_t592"] = {
        "element": "stone in the wall gap = T-325 threshold strip, ONE element (register 08:15); nosing between jambs an "
                   "attribute", "house_lm": tot["house_payable_lm"], "house_nr": tot["house_nr"],
        "house_riser_m2": tot["house_riser_m2"], "house_nosing_attribute_lm": tot["house_nosing_lm_attribute"],
        "gate_lm": tot["gate_payable_lm"], "gate_riser_m2": tot["gate_riser_m2"], "gate_status": "PARTIAL",
        "nr_ours_with_gate": d592["compare"]["nr_ours_with_gate"], "his_nr": d592["compare"]["his_nr"],
        "ours_minus_his_lm": {"house": d592["compare"]["gap_house_lm"], "with_gate": d592["compare"]["gap_with_gate_lm"]},
        "manifest": "V10 DOOR_STEPS FR-T592-1 (4 house lines, beside figures) / FR-T592-2 (gate own row); no line moves",
        "pct": None}
    sec["beside"]["agree_pairs_v8"] = pairs
    return sec, moves, pairs


# ================================================================================ T-589 / T-595 beside (structural) ==
def t589_classes(d589: dict) -> dict:
    out = {}
    for sec_id, t in d589["tables"].items():
        if sum(t["n_by_class"].values()) != t["n"] or t["quantity_added_across_sources"] is not False:
            raise StatementError(f"T-589 {sec_id}: class counts do not re-add, or quantities added across sources")
        out[sec_id] = {"unit": t["unit"], "n": t["n"], "n_by_class": t["n_by_class"],
                       "by_source": {src: {k: v for k, v in b["by_class"].items() if v["n"]}
                                     for src, b in t["by_source"].items()}}
    return {"block_id": "T-589/structural-closure-classes", "kind": "CLASSIFICATION_BESIDE", "report": "T-589",
            "valued": "0", "candidate_line": False, "sections": out, "packs": sorted(d589["packs"]),
            "note": "per V6 structural section: VERIFIED_ON_RECORD / CLOSABLE_FROM_DRAWINGS / DESIGNER_ITEM / "
                    "OWNER_RULE_GAP with quantity per class in its own unit and basis; no component promoted, no "
                    "quantity added across sources; the packs are the Checker's T-180 input, not proof",
            "verification": V589}


def t595_rebar_beside(v7: dict, d595: dict, v6: dict) -> dict:
    prev = _one(v7["beside_v7"], lambda b: b["block_id"] == "T-583/dome-lift-components", "V7 T-583 beside")
    pr = {r["row_id"]: r for r in prev["rows"]}
    rows, lo, moved = [], D(0), []
    for r in d595["rebar"]["rows"]:
        A7.check_high_open(r)
        if r["row_id"] not in pr:
            raise StatementError(f"T-595 {r['row_id']}: not a T-583 row")
        x = {"row_id": r["row_id"], "status": r["status"], "version": r["version"],
             "t560_group": pr[r["row_id"]]["t560_group"]}
        if r["status"] == "HELD_RANGE_HIGH_OPEN":
            new, was = D(str(r["t_low"])), D(pr[r["row_id"]]["at_least_t"])
            if new < was:
                raise StatementError(f"T-595 {r['row_id']}: low below the T-583 low (components only add)")
            x.update(at_least_t=s(new), at_least_was_t=s(was))
            lo += new
            if new != was:
                moved.append({"row_id": r["row_id"], "from_t": s(was), "to_t": s(new), "delta_t": s(new - was)})
        rows.append(x)
    if s(lo) != s(D(str(d595["rebar"]["totals"]["t_low"]))) or d595["rebar"]["totals"]["valued_t"] != 0.0:
        raise StatementError("T-595: rows do not re-add to its low, or something is valued")
    e = prev["expected_after_v8_rebar_rows"]
    g5 = sum((D(x["at_least_t"]) for x in rows if x["t560_group"] == "G5_STAIRS_DOME" and "at_least_t" in x), D(0))
    r560 = _one(v6["sections_v5"], lambda c: c["section_id"] == "T-560/rebar", "V5 T-560")
    g5r = _one(r560["rows"], lambda x: x["name"].startswith("G5_"), "T-560 G5 row")
    held = D(e["v5_held_low_t"]) + g5
    return {"block_id": "T-595/dome-lift-components@V8", "kind": "HELD_RANGE_HIGH_OPEN_BESIDE", "report": "T-595",
            "unit": "t", "candidate_line": False, "valued_t": "0", "supersedes_beside": prev["block_id"],
            "at_least_t": s(lo), "at_least_was_t": prev["at_least_t"], "moved_rows": moved,
            "high": "OPEN (laps, hooks, anchorage, ring depth by name)", "rows": rows,
            "rounding_note": "the Checker's 0.789554 adds rounded parts; T-595 json 0.789555 (unrounded east low "
                             "0.144290): printed as in the json",
            "expected_after_v8_rebar_rows": {
                "group": "G5_STAIRS_DOME", "held_at_least_t": s(held), "held_at_least_was_t": e["held_at_least_t"],
                "residual_after_held_at_most_t": s(D(g5r["his_t"]) - D(g5r["engine_valued_t"]) - held),
                "residual_was_at_most_t": e["residual_after_held_at_most_t"], "held_high": "OPEN",
                "note": "EXPECTED only, never valued; residual vs his TYPED_LUMP at most this, no %"},
            "verification": V595}


def t595_footing_beside(v6: dict, d595: dict) -> dict:
    hb = _one(v6["sections_v5"], lambda c: c["section_id"] == "T-572/held-bounds", "V5 T-572 held bounds")
    fam = _one(hb["families"], lambda f: f["family"] == "B10 FOOTING LINE", "footing family")
    f = d595["footing"]
    if fam["both_ends_drawn"]["range"][0] != f["family_t572"]["bounded_part_low"] or \
            fam["both_ends_drawn"]["range"][1] != f["family_v2"]["bounded_part_high"]:
        raise StatementError("T-595: footing family before is not the V5 T-572 bounded part")
    c = f["component"]
    return {"block_id": "T-595/footing-S02@V8", "kind": "BOUNDS_BESIDE", "report": "T-595", "unit": "m3",
            "candidate_line": False, "valued": "0", "restates_beside_of": "T-572/held-bounds B10 FOOTING LINE",
            "component": {"element_id": c["element_id"], "line_id": c["line_id"],
                          "range_m3": [c["low"], c["high"]], "range_was_m3": [c["t572_low"], c["t572_high"]],
                          "scenarios": c["scenarios"], "status": c["status_label"]},
            "family_bounded_part_m3": {"low": f["family_v2"]["bounded_part_low"],
                                       "low_was": f["family_t572"]["bounded_part_low"],
                                       "high": f["family_v2"]["bounded_part_high"]},
            "his": {"m3": f["beside_his"]["his_m3"], "class": f["beside_his"]["class"],
                    "class_was": f["beside_his"]["t572_class"]},
            "family_total": "NOT STATEABLE (boundary-wall pad count / spacing not printed): unchanged",
            "verification": V595}
