"""T-603: reconciled-quantities statement V9 adapters. V9 = statement V8 (T-594, rebuilt read only, every V8 key
byte-equal) + restated sections for the merged provenance audits T-590 (structural, R-T590-1) and T-591 (finishes,
R-T591-1), a beside restatement of the stair nosing cross-reference on T-598, and the F-C-T593-1 guard (the two stair
skirting forms are ONE element). Research, unwired: computes no new quantity; reads the committed, sha256-pinned
research outputs only (no drawing, workbook or client data). Sign as V4 .. V8: reference - engine; + = in the
reference only.

R-T603-1 (proposed, every villa). A statement restating sections on a merged provenance audit:
  (a) RECLASS, NEVER REWRITE: a provenance outcome moves a row's CLASS only; the row is found exactly once by name in
      the section of record (the supersession chain is followed), its class before must be the audited class
      (RULE_DIFFERENCE) and its delta must equal the audited delta; name, delta and unit are kept; the section totals
      are unchanged and its rows re-add to reference - engine (a section whose total moved is refused);
  (b) POINTER, NOT PROMOTION: a row whose convention waits for a rule version of an unmerged task stays UNRESOLVED
      with a pointer to that task; it may return to RULE_DIFFERENCE SOURCED only when that task is MERGED and its rule
      id is listed in docs/RULES_INDEX.md (a MERGED pointer without the rule is refused);
  (c) COUNTED APART: a row the audit reclasses but which is not the convention (F-C-T590-2) is a separate group,
      never inside the convention total;
  (d) A CITATION IS AN ANNOTATION: a corrected citation (SOURCED_RECITE) is written beside the row of record with the
      governing source(s) and the refused citation; it never changes a class or a delta; an audited row the later
      statement already restated is listed as OVERTAKEN with the class it now has, never re-applied;
  (e) EVIDENCE STAYS: a reclass keeps the row's evidence status from its own verdict; the audit verdict is recorded as
      the class basis (a provenance verdict never promotes a measurement);
  (f) TWO FORMS, ONE ELEMENT (F-C-T593-1): a physical element measured under two forms (stair skirting SLOPED / ZIGZAG,
      ORR-007 open) enters the statement as ONE element: per piece [min, max] over its forms, element range [sum of
      minima, sum of maxima]; a statement row's low must be the element low of its stair and its high, when stated,
      at least the element high; a figure equal to the sum over forms anywhere in the statement is refused.
"""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T594 = ROOT / "research/agents_t594"
if str(T594) not in sys.path:
    sys.path.insert(0, str(T594))
import t594_adapters as A8  # noqa: E402  (T-594, read only)

A7 = A8.A7
Z = A8.Z
D = Decimal
StatementError = Z.StatementError
s = Z.s
CV, PV, WP = A8.CV, A8.PV, A8.WP

T590_JSON = ROOT / "research/agents_t590/out/T590_RULE_DIFF_PROVENANCE.json"
T591_JSON = ROOT / "research/agents_t591/out/T591_RULE_DIFF_PROVENANCE.json"
T598_JSON = ROOT / "research/agents_t598/ALSENAN_EDGES_T598.json"
T593_JSON = A8.T593_JSON
RULES_INDEX = ROOT / "docs/RULES_INDEX.md"
PINS = {
    T590_JSON: "21427d9a68fec6e8b784b34183e9f4cebc341ea8482e288741d8dd9ac60bca58",
    T591_JSON: "2df92af2c25d5a90158af4ca2147b9fee72e0c9b5ae074c777beb4fc092510b7",
    T598_JSON: "2ee67610d6abe69a6ca5dea4ef4a554f9cc2fc9ac9bfc6ad847b22c7e57149b6",
    T593_JSON: A8.PINS[A8.T593_JSON],
}

# Checker verdicts (board, 2026-11-07), quoted as classes and evidence only
V590 = ("Checker 2026-11-07 11:58 (T-590 Gate A): provenance checked from the registers themselves: RULES_INDEX holds "
        "neither R-CONC-OWN-1 nor R-T394-1; R-CONC-OWN-1 PROPOSED, not in force; Q-62 A cond a REQUIREMENT (chooses no "
        "owner); ERS s.7 2026-10-31 (column owns) vs ELEMENT_REGISTER 2026-11-06 20:14 (beam owns): "
        "CONVENTION_RECORD_CONFLICT CONFIRMED; 12 headline rows +2.369278 m3 signed / 7.701778 gross, 34.814694 t AGREE; "
        "his rebar 44.19 t typed lump: HIS_SIDE_UNREADABLE AGREE; F-C-T590-1 cite the V7 2F reading; F-C-T590-2 the "
        "GF UNTRACED -> GF B7 0.120452 m3 row is not a joint convention: count it apart")
V591 = ("Checker 2026-11-07 09:56 (T-591 Gate A): rule text read: UP-SKIRT-001 1.4.0 'doorless_opening_jambs: "
        "included'; Q-73 is the block-wall opening question: plaster / paint deductions re-cite UP-OPEN-SCHED-001 1.4.0 "
        "(F-T591-2 CONFIRMED); domes re-cite Q-24; own DXF read A-1F-01 arch120: real jambs 0.15 deep, no leaf, no "
        "frame -> 2 x 0.15 = 0.30 lm AGREE: ENGINE_WRONG 0.30 lm PARTIALLY VERIFIED (floor finish on records); every "
        "RD row names its governing rule")
V598 = ("Checker 2026-11-07 12:02 (T-598 Gate A): own read both DXFs: RS-C radials 1.150, curtail arcs 0.949440 / "
        "0.672000 lm (+1.621440), MS1-U floor edge 1.150 DRAWING-CONFIRMED; 88.500 + 3.450 + 15.421440 = 107.371440 "
        "lm; his 63 x 1.20 + 28 x 1.20 + 5 x 2.80 = 123.20; causes 8.400 + 4.800 + 4.000 + 0.250 - 1.621440 = "
        "15.828560, residual 0 AGREE; F-C-T598-1 MS2-U floor edge ASSUMED - OWNER-APPROVED (Q-46 A), not "
        "DRAWING-CONFIRMED; RS-C 12 ASSUMED - OWNER-APPROVED (Q-50 A cond); N01 .. N04 HELD 4.600 .. 6.943, band 0 .. "
        "0.050 HELD")
V593 = ("Checker 2026-11-07 09:56 (T-593 Gate A) F-C-T593-1: FIN.STAIR.SKIRTING.SLOPED and .ZIGZAG both carry HELD "
        "lows (17.009049 / 23.300481 lm) for the SAME physical skirting (ORR-007 open); a statement sum adding both "
        "double counts: take one form or the range min..max over forms, with a test")

# Pointer for the column / beam joint convention (R-T603-1 (b)); board state at the claim (2026-11-07T15:01Z)
JOINT_RULE = {"task": "T-599", "status": "REJECTED", "status_line": "REJECTED (Verifier 2026-11-07T13:58Z, gates F + H: "
              "the restatement promoted whole rows the rule does not explain)", "rule_id": "UP-CONC-JOINT-001"}
TAG_JOINT, TAG_APART, TAG_REBAR, TAG_JAMB = "F-T603-1", "F-T603-2", "F-T603-3", "F-T603-4"


def load(p: Path) -> dict:
    pin = PINS.get(p)
    if pin and Z.sha(p) != pin:
        raise StatementError(f"{p.relative_to(ROOT)}: sha256 differs from its pin")
    return json.loads(p.read_text(encoding="utf-8"))


# ================================================================================ section of record ===============
LEVELS = ("sections", "sections_v5", "sections_v6", "sections_v7", "sections_v8")


def all_sections(st: dict) -> dict:
    out = {}
    for lv in LEVELS:
        for c in st.get(lv, []):
            if c["section_id"] in out:
                raise StatementError(f"{c['section_id']}: section id twice in the statement")
            out[c["section_id"]] = c
    return out


def supersession(st: dict) -> dict:
    sup = {}
    for k in ("supersedes_v7", "supersedes_v8"):
        sup.update({a: b for a, b in st.get(k, {}).items() if not a.startswith("beside")})
    return sup


def of_record(sid: str, sup: dict) -> str:
    seen = set()
    while sid in sup:
        if sid in seen:
            raise StatementError(f"{sid}: supersession loop")
        seen.add(sid)
        sid = sup[sid]
    return sid


# ================================================================================ (a) (e) reclass ================
def _reclose(sec: dict, old: dict) -> None:
    diff = D(sec["reference_total"]) - D(sec["engine_valued"])
    tot = sum((D(r["delta"]) for r in sec["rows"]), D(0))
    if tot != diff or D(old["difference"]) != D(old["reference_total"]) - D(old["engine_valued"]):
        raise StatementError(f"{sec['section_id']}: rows {tot} != reference - engine {diff} (R-T603-1 (a))")
    bc, bg = Z.zero_classes(), Z.zero_classes()
    for r in sec["rows"]:
        if r["unit"] != sec["unit"]:
            raise StatementError(f"{sec['section_id']}: row '{r['name'][:60]}' in {r['unit']}")
        bc[r["class"]] += D(r["delta"])
        bg[r["class"]] += abs(D(r["delta"]))
    sec["by_class"] = {k: s(v) for k, v in bc.items()}
    sec["by_class_gross_abs"] = {k: s(v) for k, v in bg.items()}


def reclass(old: dict, new_id: str, moves: dict, verdict: str, evid) -> tuple[dict, list]:
    """moves: row name -> {to, tag, delta (audited), set: {...}}. Every row gets a unit and an evidence status (from
    `evid`, its own verdict map); moved rows keep delta and evidence, change class only (R-T603-1 (a) / (e))."""
    sec = copy.deepcopy(old)
    names = [r["name"] for r in sec["rows"]]
    for n in moves:
        if names.count(n) != 1:
            raise StatementError(f"{old['section_id']}: row '{n[:60]}' found {names.count(n)} times, not once")
    out = []
    for r in sec["rows"]:
        r.setdefault("unit", sec["unit"])
        if "evidence_status" not in r:
            A7.stamp(r, evid(r), r.get("verification_basis") or r.get("verification", ""))
        m = moves.get(r["name"])
        if m:
            if r["class"] != "RULE_DIFFERENCE":
                raise StatementError(f"{old['section_id']}: row '{r['name'][:60]}' is {r['class']}, the audit read "
                                     "RULE_DIFFERENCE (R-T603-1 (a))")
            if D(r["delta"]) != D(m["delta"]):
                raise StatementError(f"{old['section_id']}: row '{r['name'][:60]}' delta {r['delta']} != audited "
                                     f"{m['delta']} (R-T603-1 (a))")
            if "delta" in m.get("set", {}) or "name" in m.get("set", {}):
                raise StatementError(f"{old['section_id']}: a reclass may not change a delta or a name")
            out.append({"tag": m["tag"], "section_id": new_id, "row": r["name"][:120], "from": r["class"],
                        "to": m["to"], "delta": r["delta"], "verdict": verdict})
            r.update(m.get("set", {}))
            r["was_class"], r["class"], r["tag"], r["class_basis"] = r["class"], m["to"], m["tag"], verdict
        if r["class"] not in Z.CLASSES:
            raise StatementError(f"{old['section_id']}: '{r['class']}' is not a statement class")
    sec["section_id"], sec["restates"] = new_id, old["section_id"]
    _reclose(sec, old)
    if sec.get("difference_pct_of_reference") is not None and (any(r["class"] == "HELD" for r in sec["rows"]) or
                                                              sec.get("engine_held")):
        sec["pct_was"] = sec["difference_pct_of_reference"]      # F-T603-6: R-T579-1 (e), no % with HELD parts
        sec["difference_pct_of_reference"] = None
    if (sec["reference_total"], sec["engine_valued"], sec["difference"]) != \
            (old["reference_total"], old["engine_valued"], old["difference"]):
        raise StatementError(f"{new_id}: totals moved (reclass, never rewrite: R-T603-1 (a))")
    return sec, out


def check_section_totals(old: dict, new: dict) -> None:
    """Refuse a restated section whose totals were edited instead of its rows split / reclassed."""
    for k in ("reference_total", "engine_valued", "difference"):
        if D(old[k]) != D(new[k]):
            raise StatementError(f"{new['section_id']}: {k} {old[k]} -> {new[k]}: a total edited, not split "
                                 "(R-T594-1 (a) / R-T603-1 (a))")
    if sum((D(r["delta"]) for r in new["rows"]), D(0)) != D(new["reference_total"]) - D(new["engine_valued"]):
        raise StatementError(f"{new['section_id']}: rows do not re-add to reference - engine")


# ================================================================================ (b) joint pointer ===============
def joint_class(rule: dict, rules_index_text: str) -> str:
    if rule["status"] == "MERGED":
        if f"| {rule['rule_id']} |" not in rules_index_text:
            raise StatementError(f"{rule['task']} MERGED but {rule['rule_id']} is not in docs/RULES_INDEX.md "
                                 "(R-T603-1 (b))")
        return "RULE_DIFFERENCE"
    return "UNRESOLVED"


def _joint_set(rule: dict) -> dict:
    if rule["status"] == "MERGED":
        return {"kind_of_cause": "CONVENTION", "provenance_v9": f"SOURCED: {rule['rule_id']} ({rule['task']})"}
    return {"kind_of_cause": "CONVENTION_RECORD_CONFLICT",
            "provenance_v9": f"NONE -> UNRESOLVED (R-T590-1): no adopted ownership rule; pointer {rule['task']} "
                             f"{rule['status_line']}; returns to RULE_DIFFERENCE SOURCED only when {rule['task']} is "
                             f"MERGED with {rule['rule_id']} in RULES_INDEX"}


# ================================================================================ T-590 structural ===============
V9_EVID = {"CHECKER_CONFIRMED": CV, "WORKER_PROPOSED": WP, PV: PV}


def evid_structural(sid: str, r: dict) -> str:
    if sid.startswith("T-576/"):
        return A7.ev_t576(r["term"], r["name"].split(" ", 1)[0], r["source_class"])
    if sid.startswith(("T-551/", "T-545/", "T-560/")):
        return V9_EVID[r["verification"]]
    raise StatementError(f"{sid}: no evidence map")


def _kind(r590: dict) -> str:
    if r590["unit"] == "t":
        return "REBAR"
    if "UNTRACED" in r590["name"]:
        return "APART"
    if "JOINT_HEAD" in r590["name"] or "THROUGH_SUPPORT" in r590["name"]:
        return "JOINT"
    raise StatementError(f"T-590 row '{r590['name']}': not a joint, untraced or rebar row")


def t590_sections(st8: dict, d590: dict, rules_index_text: str, rule: dict = JOINT_RULE) -> dict:
    secs, sup = all_sections(st8), supersession(st8)
    jc = joint_class(rule, rules_index_text)
    by_sec: dict[str, dict] = {}
    superseded = []
    for r in d590["rows"]:
        if r["outcome"] not in ("NONE", "HIS_SIDE_UNREADABLE") or r["class_after"] != "UNRESOLVED":
            raise StatementError(f"T-590 row '{r['name']}': outcome {r['outcome']} not mapped")
        cur = of_record(r["section_id"], sup)
        if cur != r["section_id"]:
            superseded.append({"section_id": r["section_id"], "of_record": cur, "row": r["name"], "delta": r["delta"],
                               "unit": r["unit"]})
            continue
        k = _kind(r)
        if k == "JOINT":
            m = {"to": jc, "tag": TAG_JOINT, "delta": r["delta"], "set": _joint_set(rule)}
        elif k == "APART":
            m = {"to": "UNRESOLVED", "tag": TAG_APART, "delta": r["delta"], "set": {
                "kind_of_cause": "UNTRACED_COUNTED_APART",
                "provenance_v9": "F-C-T590-2: not a joint convention (UNRESOLVED in T-545, THROUGH_SUPPORT on 2 / 14 "
                                 "ends only, T-587 F-T587-2): UNRESOLVED, counted apart from the joint rows"}}
        else:
            m = {"to": "UNRESOLVED", "tag": TAG_REBAR, "delta": r["delta"], "set": {
                "kind_of_cause": "HIS_SIDE_UNREADABLE",
                "provenance_v9": "ours SOURCED (URBAN-REBAR-NET-AND-PROCUREMENT@v1, Q-71, OWNER_RULE_REBAR_2026-10-24 "
                                 "s.1); his side a typed lump (44.19 t, no bar row): no convention readable -> "
                                 "UNRESOLVED (R-T590-1 (j))"}}
        by_sec.setdefault(cur, {})[r["name"]] = m
        m["_kind"], m["_live"] = k, r["live"]
    for x in superseded:     # a superseded audited row: the section of record carries audited rows of the same term
        term = x["row"].rsplit(": ", 1)[-1]
        if not any(n.rsplit(": ", 1)[-1] == term for n in by_sec.get(x["of_record"], {})):
            raise StatementError(f"T-590 superseded row '{x['row']}' ({x['section_id']}) has no audited {term} row "
                                 f"in {x['of_record']}")
    out, moves, groups = [], [], {"JOINT": [], "APART": [], "REBAR": []}
    for sid in sorted(by_sec):
        old = secs[sid]
        mv = {n: {k: v for k, v in m.items() if not k.startswith("_")} for n, m in by_sec[sid].items()}
        sec, mvs = reclass(old, sid.split("@", 1)[0] + "@V9", mv, V590, lambda x, sid=sid: evid_structural(sid, x))
        if sid == "T-551/columns":         # the T-566 conflict readings: the joint term moves class in every reading
            rng = old["beside"]["conflict_t566"]["by_class_range_over_readings"]
            mvd = sum((D(m["delta"]) for m in mv.values()), D(0))
            if [D(x) for x in rng["RULE_DIFFERENCE"]] != [mvd, mvd]:
                raise StatementError("T-551 beside: the reading RULE_DIFFERENCE range is not the reclassed joint rows")
            sec["beside_v9"] = {"conflict_t566_range_over_readings_v9": dict(
                rng, RULE_DIFFERENCE=["0", "0"], UNRESOLVED=[s(D(x) + mvd) for x in rng["UNRESOLVED"]]),
                "note": "the joint rows are the same in every T-566 reading (R-T566-1): RULE_DIFFERENCE -> "
                        "UNRESOLVED in each; the V4 beside kept as it was"}
        out.append(sec)
        moves += mvs
        for n, m in by_sec[sid].items():
            groups[m["_kind"]].append({"section_id": sec["section_id"], "row": n, "delta": m["delta"],
                                       "unit": sec["unit"], "reading_of_record": m["_live"]})
    return {"sections": out, "moves": moves, "groups": groups, "superseded_audited": superseded}


def joint_pairs(st8: dict) -> dict:
    """Per storey, reference - engine (the statement sign): beam THROUGH_SUPPORT (T-545/beams@V7) + column JOINT_HEAD
    (T-551/columns). F-C-T590-1: the 2F beam term is the V7 reading (+0.42), not T-551's beside (-0.532760, which is
    also printed engine - reference)."""
    secs = all_sections(st8)
    beams = {r["name"].split(":")[0]: D(r["delta"]) for r in secs["T-545/beams@V7"]["rows"]
             if r["name"].endswith(": THROUGH_SUPPORT")}
    cols = {r["name"].split(" ")[1].rstrip(":"): D(r["delta"]) for r in secs["T-551/columns"]["rows"]
            if r["name"].endswith(": JOINT_HEAD")}
    out = {}
    for f in ("GF", "1F", "2F"):
        b, c = beams.get(f, D(0)), cols.get(f, D(0))
        out[f] = {"beam_THROUGH_SUPPORT_m3": s(b), "column_JOINT_HEAD_m3": s(c), "net_m3": s(b + c)}
    old = secs["T-551/columns"]["beside"]["column_beam_pairing_m3"]
    for f in ("GF", "1F"):
        if D(old[f]["net_m3"]) != -D(out[f]["net_m3"]):
            raise StatementError(f"T-551 beside pair {f} is not the negated statement-sign pair")
    return {"sign": "reference - engine (statement sign)", "by_storey": out,
            "was_t551_beside_engine_minus_reference": old,
            "note": "F-T603-5: T-551's beside pair (copied by T-590 as 'reference - engine') is engine - reference: "
                    "negated here; 2F takes the T-545@V7 reading +0.42 (F-C-T590-1). The pair does not cancel per "
                    "storey: the unmatched part is its own residual (T-600), never a convention by default"}


# ================================================================================ T-591 finishes =================
def t591_provenance(st8: dict, d591: dict) -> dict:
    secs, sup = all_sections(st8), supersession(st8)
    applied, overtaken, none_rows = [], [], []
    counts = {}
    for r in d591["rows"]:
        if not r["live"]:
            continue
        counts.setdefault(r["unit"], {}).setdefault(r["outcome"], [0, D(0), D(0)])
        c = counts[r["unit"]][r["outcome"]]
        c[0] += 1
        c[1] += D(r["delta"])
        c[2] += abs(D(r["delta"]))
        cur = of_record(r["section_id"], sup)
        hit = [x for x in secs[cur]["rows"] if x["name"] == r["name"]]
        if len(hit) > 1:
            raise StatementError(f"{cur}: T-591 row '{r['name'][:60]}' found {len(hit)} times")
        entry = {"section_audited": r["section_id"], "section_of_record": cur, "row": r["name"][:160],
                 "unit": r["unit"], "delta": r["delta"], "outcome": r["outcome"],
                 "governing": [o["source"] for o in r["our_side"]],
                 "refused_citations": r["cited_not_governing"], "provisional": r["provisional"]}
        if not hit or hit[0]["class"] != "RULE_DIFFERENCE" or D(hit[0]["delta"]) != D(r["delta"]):
            entry["overtaken"] = ("row restated in a later version" if not hit else
                                  f"now {hit[0]['class']} {hit[0]['delta']} in {cur}")
            overtaken.append(entry)
            continue
        if r["outcome"] == "NONE":
            none_rows.append(entry)
        else:
            applied.append(entry)
    out = {u: {o: {"n": v[0], "signed": s(v[1]), "gross": s(v[2])} for o, v in sorted(m.items())}
           for u, m in sorted(counts.items())}
    if out != d591["per_unit_live"]:
        raise StatementError("T-591 live rows do not re-add to its per-unit counts")
    return {"applied": applied, "overtaken": overtaken, "none": none_rows, "per_unit_live": out}


def check_t591_findings(prov: dict) -> dict:
    rows = prov["applied"] + prov["overtaken"]
    f2 = [e for e in rows if "Q-73" in e["refused_citations"]]
    if len(f2) != 8 or any("UP-OPEN-SCHED-001" not in e["governing"] for e in f2) or \
            {e["section_audited"] for e in f2} != {"T-552/plaster-internal", "T-561/paint-internal"}:
        raise StatementError("F-T591-2: the 8 plaster / paint rows do not re-cite UP-OPEN-SCHED-001 for Q-73")
    f3 = [e for e in rows if "Q-29" in e["refused_citations"]]
    if len(f3) != 2 or any(e["governing"] != ["Q-24"] for e in f3):
        raise StatementError("F-T591-3: the dome rows do not re-cite Q-24 for Q-29")
    if any(g.startswith("Q-73") for e in rows for g in e["governing"]
           if e["section_audited"].startswith(("T-552/", "T-561/"))):
        raise StatementError("Q-73 accepted for a plaster / paint deduction")
    return {"F-T591-2": {"rows": 8, "signed_m2_per_section": s(sum((D(e["delta"]) for e in f2), D(0)) / 2),
                         "governing": "UP-OPEN-SCHED-001 1.4.0 (+ UP-GEN-003)", "refused": "Q-73 (blockwork)"},
            "F-T591-3": {"rows": 2, "signed_m2": s(sum((D(e["delta"]) for e in f3), D(0))), "governing": "Q-24",
                         "refused": "Q-29 (scenario S1 only)"}}


def t591_jamb_section(st8: dict, none_rows: list) -> tuple[dict, list]:
    if len(none_rows) != 1 or none_rows[0]["section_of_record"] != "T-574/skirting-room" or \
            D(none_rows[0]["delta"]) != D("0.30"):
        raise StatementError("T-591: the one NONE row is not the T-574 skirting-room 0.30 lm arch jamb row")
    old = all_sections(st8)["T-574/skirting-room"]
    n = [r["name"] for r in old["rows"] if r["name"].startswith(none_rows[0]["row"][:120])]
    if len(n) != 1:
        raise StatementError("T-574/skirting-room: the jamb row is not found once")
    mv = {n[0]: {"to": "ENGINE_WRONG", "tag": TAG_JAMB, "delta": "0.30", "set": {
        "provenance_v9": "NONE on our side (R-T443-1 'door jambs never' is a worker record; the owner method "
                         "URBAN-SKIRTING-OPENING-METHOD / UP-SKIRT-001 1.4.0 INCLUDES doorless-opening jambs): his 2 x "
                         "0.15 = 0.30 lm is the A-1F-01 arch's two real jambs; Checker ENGINE_WRONG 0.30 lm PARTIALLY "
                         "VERIFIED (T-591; T-601 own read AGREE); fix row FR-T601-1 applies when wired (T-604)"}}}
    return reclass(old, "T-574/skirting-room@V9", mv, V591,
                   lambda x: A7.ev_v6("T-574/", x) if x.get("tag") != TAG_JAMB else PV)


# ================================================================================ T-598 nosing (beside) ==========
def t598_nosing(st8: dict, d598: dict) -> dict:
    prev = [b for b in st8["beside_v7"] if b["block_id"] == "T-578/nosing-xref"]
    if len(prev) != 1:
        raise StatementError("V7 T-578 nosing cross-reference not found once")
    prev = prev[0]
    res = d598["result"]
    rec = res["reconciliation"]
    his = sum((D(str(v["his_lm"])) for v in rec.values()), D(0))
    ours = sum((D(str(v["ours_lm"])) for v in rec.values()), D(0))
    if his != D(prev["units"]["lm"]["his"]) or s(ours) != s(D(str(res["nosing_after"]["valued_lm"]))):
        raise StatementError("T-598: his / our nosing totals are not the T-578 reference and the T-598 valued lm")
    cls = {"COUNT": "UNRESOLVED", "HELD": "HELD", "WIDTH": "ENGINE_RIGHT", "NOTCH": "ENGINE_RIGHT",
           "CURTAIL": "ENGINE_RIGHT"}
    causes, by_cls = [], {}
    for stair, v in rec.items():
        tot = D(0)
        for c in v["causes"]:
            term = c["cause"].split(" ", 1)[0]
            amt = D(str(c["lm"]))
            tot += amt
            causes.append({"stair": stair, "term": term, "class": cls[term], "lm": s(amt), "label": c["cause"]})
            by_cls[cls[term]] = by_cls.get(cls[term], D(0)) + amt
        if tot != D(str(v["his_minus_ours"])) or D(str(v["unexplained"])) != 0 or \
                D(str(v["his_lm"])) - D(str(v["ours_lm"])) != D(str(v["his_minus_ours"])):
            raise StatementError(f"T-598 {stair}: causes do not close his - ours")
    gap = his - ours
    if gap != D(str(res["his_minus_ours_total"])) or sum(by_cls.values(), D(0)) != gap:
        raise StatementError("T-598: causes do not re-add to his - ours")
    vb = {k: D(str(v)) for k, v in res["value_lm_by_status"].items()}
    ms2u = [e for e in res["edges"] if e["id"] == "ST01-MS2U-FLOOR"]
    if len(ms2u) != 1 or D(str(ms2u[0]["lm"])) != D("1.15"):
        raise StatementError("T-598: MS2-U floor edge not found at 1.150")
    status_v9 = {"DRAWING-CONFIRMED": s(vb["DRAWING-CONFIRMED"] - D("1.15")),
                 "ASSUMED - OWNER-APPROVED": s(vb["ASSUMED - OWNER-APPROVED"] + D("1.15"))}
    nr_his = sum(v["his_pieces"] for v in rec.values())
    nr_val = sum(v["ours_edges_valued"] for v in rec.values())
    nr_held = sum(v["ours_edges_held"] for v in rec.values())
    if nr_his != prev["units"]["nr"]["his"] and str(nr_his) != prev["units"]["nr"]["his"]:
        raise StatementError("T-598: his nosing pieces are not the T-578 nr reference")
    hb = [s(D(str(x))) for x in res["held_bound_lm"]]
    return {"block_id": "T-598/nosing@V9", "kind": "CROSS_REFERENCE", "report": "T-598", "candidate_line": False,
            "difference_added": False, "valued": "0", "supersedes_beside": prev["block_id"], "pct": None,
            "units": {"lm": {"his": s(his), "ours_valued": s(ours), "gap_his_minus_ours": s(gap),
                             "gap_was": prev["units"]["lm"]["gap"], "held_bound_lm": hb,
                             "by_class": {k: s(v) for k, v in sorted(by_cls.items())}, "residual": s(gap - sum(
                                 by_cls.values(), D(0)))},
                      "nr": {"his": nr_his, "ours_valued": nr_val, "ours_held": nr_held,
                             "gap_his_minus_ours": nr_his - nr_val - nr_held,
                             "gap_class": "UNRESOLVED (ST-01 pieces beyond the 56 drawn risers, T-434)",
                             "gap_was": prev["units"]["nr"]["gap"]}},
            "causes": causes,
            "added_by_t598_lm_by_status": status_v9,
            "status_correction": "F-C-T598-1: MS2-U floor edge 1.150 lm ASSUMED - OWNER-APPROVED (Q-46 A), not "
                                 "DRAWING-CONFIRMED (T-598 json kept as merged; restated here)",
            "note": "compared once against his step rows (count x width); no candidate line (T-424); never added to "
                    "a column; B7-05 nosing vs B7-06 step lm on one front edge stays the ELEMENT_REGISTER NOSING EDGE "
                    "question", "verification": V598}


# ================================================================================ (f) two forms, one element =====
def stair_of(piece: str) -> str:
    if piece.startswith("E1."):
        return "ST-03"
    if piece.startswith("RS-"):
        return "ST-02"
    return "ST-01"


def skirting_element(manifest_rows: list[dict]) -> dict:
    pieces: dict[str, dict] = {}
    for r in manifest_rows:
        b = r.get("beside")
        if not isinstance(b, dict) or b.get("form") not in ("SLOPED", "ZIGZAG"):
            continue
        f = b["form"]
        if f in pieces.setdefault(b["piece"], {}):
            raise StatementError(f"{b['piece']}: form {f} twice")
        pieces[b["piece"]][f] = (D(str(r["after"]["held_low"])), D(str(r["after"]["held_high"])), r["line_id"])
    two, held = {}, {}
    for p, forms in sorted(pieces.items()):
        if len(forms) == 2:
            lo, hi = forms["SLOPED"], forms["ZIGZAG"]
            if lo[0] != lo[1] or hi[0] != hi[1] or lo[0] > hi[0]:
                raise StatementError(f"{p}: a two-form piece is not exact pitch <= zigzag")
            two[p] = {"stair": stair_of(p), "range": [s(lo[0]), s(hi[0])], "lines": [lo[2], hi[2]]}
        else:
            (f, v), = forms.items()
            held[p] = {"stair": stair_of(p), "form": f, "bound": [s(v[0]), s(v[1])], "line": v[2]}
    by_stair = {}
    for p, x in two.items():
        b = by_stair.setdefault(x["stair"], [D(0), D(0), 0])
        b[0] += D(x["range"][0])
        b[1] += D(x["range"][1])
        b[2] += 1
    lo = sum((b[0] for b in by_stair.values()), D(0))
    hi = sum((b[1] for b in by_stair.values()), D(0))
    return {"element": "stair flight skirting (one physical skirting per flight wall piece, two measurement forms)",
            "forms": ["SLOPED (pitch)", "ZIGZAG (riser + going)"], "payable_form": "OPEN (ORR-007)",
            "two_form_pieces": len(two), "range_lm": [s(lo), s(hi)],
            "by_stair": {k: {"pieces": v[2], "range_lm": [s(v[0]), s(v[1])]} for k, v in sorted(by_stair.items())},
            "held_one_form_pieces": held, "sum_over_forms_refused_lm": s(lo + hi), "summed": False,
            "pieces": two, "verification": V593}


def _numbers(x, path=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from _numbers(v, f"{path}.{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _numbers(v, f"{path}[{i}]")
    elif isinstance(x, str):
        try:
            yield path, D(x)
        except Exception:  # noqa: BLE001  (text, not a figure)
            return


def refuse_form_sum(st: dict, element: dict) -> None:
    """(f) the sum over forms appears nowhere; each stair flight row low = its stair's element low."""
    bad = D(element["sum_over_forms_refused_lm"])
    for path, v in _numbers({k: v for k, v in st.items() if k != "stair_skirting_element_v9"}):
        if v == bad:
            raise StatementError(f"{path}: {v} lm = SLOPED + ZIGZAG of one skirting (F-C-T593-1, R-T603-1 (f))")
    sec = all_sections(st)[of_record("T-574/skirting-stairs", supersession(st))]
    for stair, b in element["by_stair"].items():
        rows = [r for r in sec["rows"] if r["name"].startswith(stair) and r["class"] == "HELD"
                and ("form not chosen" in r["name"] or "two-form pieces" in r["name"])]
        if len(rows) != 1:
            raise StatementError(f"{sec['section_id']}: {stair} has {len(rows)} flight form rows, not 1")
        r = rows[0]
        if D(r["delta"]) != D(b["range_lm"][0]) or D(r["bound"][0]) != D(b["range_lm"][0]):
            raise StatementError(f"{stair}: flight row low {r['delta']} != element low {b['range_lm'][0]}")
        if r["bound"][1] is not None and D(r["bound"][1]) < D(b["range_lm"][1]):
            raise StatementError(f"{stair}: flight row high {r['bound'][1]} below the element high")
