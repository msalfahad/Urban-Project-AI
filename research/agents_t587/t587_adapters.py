"""T-587: reconciled-quantities statement V7 adapters for the merged T-576 (B10 GF / 1F columns, m3, by signed cause,
both 10E0 readings), T-578 (rails / guards lm; nosing lm and nr as a cross-reference), T-583 (B11 dome / ring /
lift-wall bar components, t, bounds only, beside) and T-584 (stair steps lm / nr; E1 step lm and the external door
steps restated inside T-577/marble-lm), plus the F-C-T586-1 headline label and the F-T586-1 E1 reclass. Research,
unwired: computes no new quantity; reads the committed, sha256-pinned research outputs only (no drawing, workbook or
client data).

Statement sign (as V4 .. V6): reference - engine; + = in the reference only. T-576 and T-584 print ours - his (negated
once here); T-578 prints his - ours (taken as is).

R-T587-1 (proposed, every villa). A statement that takes in a later report:
  (a) EVIDENCE FROM THE VERDICT: every cause row carries its evidence status (CHECKER_VERIFIED / PARTIALLY_VERIFIED /
      WORKER_PROPOSED) assigned from the Checker's verdict line by (report, cause), never from the worker's handoff; a
      row whose stamped status differs from the verdict map is refused; the headline 'by class' column prints each class
      split by evidence status, so a worker-proposed class never reads as a Checker class (F-C-T586-1);
  (b) ONE REFERENCE CELL, ONE SECTION: when two reports compare the same reference cells (his stair-step count x width
      cells in T-577, T-578 nosing and T-584 steps), the cells are owned by exactly one section; every other report's
      comparison of them is a CROSS_REFERENCE beside it, never re-added (census asserted);
  (c) RESTATE, NEVER REWRITE: a later report that re-splits an earlier section (T-576 on the V5 measured columns; T-576
      on the V4 GF B7 beam; T-584 on V6 marble lm) produces a restated section with the SAME reference and engine
      totals and a reclass entry per moved amount (tag, from, to, delta, verdict line); the earlier version stays
      byte-equal and is listed as superseded;
  (d) CONFLICT READINGS: a drawn-mark conflict is shown under every reading (reading of record = the earlier statement's),
      CONFLICT_BOUNDED maps to UNRESOLVED by name, never resolved by majority or by the reference;
  (e) A BOUNDED PART IS NOT A HIGH: a range whose high excludes named components (laps, hooks, anchorage) is printed
      'at least low, high open' with its bounded part beside; a high-open row carried as a range or as a value is
      refused; units never mixed (m3 / lm / m2 / nr / t each their own section).
"""
from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T586 = ROOT / "research/agents_t586"
if str(T586) not in sys.path:
    sys.path.insert(0, str(T586))
import t586_adapters as A6  # noqa: E402  (T-586, read only)

Z = A6.Z
D = Decimal
StatementError = Z.StatementError
s, row, close_section, pct_of, neg = Z.s, Z.row, Z.close_section, Z.pct_of, Z.neg

T576_JSON = ROOT / "research/agents_t576/out/T576_COLUMN_CAUSES.json"
T578_JSON = ROOT / "research/agents_t578/out/T578_RAIL_NOSING_RECONCILE.json"
T583_JSON = ROOT / "research/agents_t583/out/T583_DOME_LIFT_COMPONENTS.json"
T584_JSON = ROOT / "research/agents_t584/out/T584_STEPS.json"
PINS = {
    T576_JSON: "7087c4efbeb3ad60ba4b4d3b8a19e42be2cc267729853820143de3988217b7fd",
    T578_JSON: "75172951bf95cfdd8a857a42c43521daa088a6a210cf95483d18c3fca3432158",
    T583_JSON: "64d827202e4e87fbd457a4a6b9f07664656b07f7db820458c1d4c9d3f5d077aa",
    T584_JSON: "242b8e0d3fdbf271b08b0f2bf1569ce21193f9b560603ee48ccdc8bf018a68b9",
}

# Checker verdicts (board, verifier 2026-11-07), quoted as classes and evidence only
V576 = ("Checker 2026-11-07 02:03 (T-576 Gate A) PARTIALLY VERIFIED: GF COUNT -1.03125 m3 re-derived exactly from his "
        "rows vs the drawn GFRS sections (ENGINE_RIGHT CONFIRMED, own count); GF matched-member head 0.75 x area = 2.100 "
        "= JOINT_HEAD 2.03375 + GLOBAL_DEPTH 0.06625 AGREE (per-member split NOT re-measured); 1F +0.555 m3 = his sum x "
        "0.75 / 3.45 exactly, head ownership RULE_DIFFERENCE CONFIRMED as the whole 1F cause; GLOBAL_DEPTH and BASE "
        "ENGINE_RIGHT PLAUSIBLE (not re-measured); 10E0 C8 / C7 CONFLICT both readings kept, never by majority; GF B7 "
        "THROUGH_SUPPORT RULE_DIFFERENCE accepted on 2 / 14 ends, UNTRACED 0 rests on the worker's 12 other ends")
V578 = ("Checker 2026-11-07 02:06 (T-578 Gate A) PARTIALLY VERIFIED: rails 1 / 5 runs re-measured: RL-07 15.953174 lm "
        "ENGINE_RIGHT on scope CONFIRMED on its length (pitch basis AGREE); RL-01..03 / RL-08 ENGINE_RIGHT PLAUSIBLE "
        "(RL-02 + RL-03 12.888 lm VERIFIED earlier); +0.226 and ST-01 +7 nosing pieces UNRESOLVED (named, his "
        "breakdown absent); causes close exactly; nosing 0 / 3 stairs re-measured; his side rests on the pinned register")
V583 = ("Checker 2026-11-07 04:05 (T-583 Gate A): verticals 62 .. 78, A low 0.156642 t/m, B low 0, shell row low "
        "0.290684 t, east ring row low 0.122518 t, west row low 0.063897 t re-derived AGREE; lift-wall A / B lows "
        "VERIFIED, h HELD (PARTIALLY VERIFIED); highs HELD by name (laps, hooks, ring depth); F-C-T583-1: a per-face "
        "side-bar label would give the tighter east low 0.144289 t (bounded rows 0.789554 t), the stated low stays a "
        "valid strict low")
V584 = ("Checker 2026-11-07 04:05 (T-584 Gate A): E1 ENGINE_OMISSION CONFIRMED, VERIFIED (4 fronts x 2.80 = 11.20 lm, "
        "nr 4); 30A platform edge = landing nosing RULE_DIFFERENCE AGREED; door steps 3.50 lm / 0.390 m2 PARTIALLY "
        "VERIFIED 4 / 5 openings (gate not re-read); stairs ST-01 45 x 1.150 = 51.75, ST-02 14 x 1.150 = 16.10, causes "
        "re-summed and close exactly, flight tread counts not re-measured: PARTIALLY VERIFIED; F-C-T584-1 one length "
        "3.50 vs 3.80 lm; F-C-T584-2 D-GF-09 riser high CONDITIONAL on the plan's lowest printed level")
V586 = ("Checker 2026-11-07 02:05 (T-586 Gate A): F-C-T586-1 the 'By class' column prints T-577 ENGINE_RIGHT -11.6888 "
        "m2 / -49.13 lm / -47 nr without a 'proposed' mark although 0 / 8 engine groups were re-measured; F-T586-1 E1 "
        "step-lm reclass to UNRESOLVED matched the Checker's T-577 'PLAUSIBLE, not confirmed'")

CV, PV, WP = "CHECKER_VERIFIED", "PARTIALLY_VERIFIED", "WORKER_PROPOSED"
EVIDENCE = (CV, PV, WP)
SHORT = {CV: "Checker VERIFIED", PV: "partially verified", WP: "worker-proposed"}
OMISSION_TO = "ENGINE_WRONG"      # a Checker-VERIFIED ENGINE_OMISSION (T-570 (a) precedent: fix row adds the line)


def load(p: Path) -> dict:
    pin = PINS.get(p)
    if pin and Z.sha(p) != pin:
        raise StatementError(f"{p.relative_to(ROOT)}: sha256 differs from its pin")
    return json.loads(p.read_text(encoding="utf-8"))


# ================================================================================ (a) evidence from the verdict ====
def ev_t576(term: str, storey: str, source_class: str) -> str:
    if source_class == "CONFLICT_BOUNDED":
        return WP                   # a conflict reading is kept, never resolved: not a Checker count
    if term == "COUNT":
        return CV if storey == "GF" else WP
    if term == "JOINT_HEAD":
        return PV                   # GF: head + depth sum 2.100 re-derived; 1F: whole 0.555 head; split not re-measured
    return WP                       # GLOBAL_DEPTH / BASE PLAUSIBLE; CONFLICT_BOUNDED kept, not resolved


def ev_t578_rail(label: str, verdict: str) -> str:
    if label.startswith("ST-01 balustrade run RL-07") or label.startswith("pitch vs plan"):
        return CV
    if label.startswith("roof / terrace guards") or verdict == "UNRESOLVED":
        return PV                   # 12.888 of 19.150 lm VERIFIED earlier; the 0.226 closure re-added
    return WP                       # RL-08 PLAUSIBLE; HELD bounds not re-measured


def ev_t584(stair: str, verdict: str, label: str) -> str:
    if stair == "ST-03":
        return CV                   # E1 fronts and the 30A platform edge re-read by handle
    return PV                       # width / count causes re-summed; tread counts not re-measured


def ev_v6(section_id: str, r: dict) -> str:
    """Evidence status of a V6 row from its section's Checker verdict (T-586 headline, F-C-T586-1)."""
    if section_id.startswith("T-571/"):
        return CV                   # counts re-derived by hand both sides, classes as named
    if section_id.startswith("T-574/"):
        return WP if r.get("kind_of_cause") == "DEDUCTION" else PV
    if section_id.startswith("T-577/"):
        return WP                   # engine side 0 / 8 groups re-measured
    raise StatementError(f"{section_id}: no verdict map for its evidence (R-T587-1 (a))")


def stamp(r: dict, status: str, verdict: str) -> dict:
    if status not in EVIDENCE:
        raise StatementError(f"{r['name']}: evidence '{status}' is not a status")
    r["evidence_status"] = status
    r["evidence_verdict"] = verdict
    return r


def audit_evidence(sec: dict, expected) -> None:
    """(a) refuse a row whose stamped status differs from the verdict map (e.g. a worker-proposed row as VERIFIED)."""
    for r in sec["rows"]:
        want = expected(r)
        if r.get("evidence_status") != want:
            raise StatementError(f"{sec['section_id']}: row '{r['name']}' stamped {r.get('evidence_status')}, the "
                                 f"verdict gives {want} (R-T587-1 (a))")


def by_class_evidence(rows: list[dict], unit: str, evid) -> dict:
    out: dict[str, dict[str, D]] = {}
    for r in rows:
        if r["unit"] != unit:
            raise StatementError(f"row '{r['name']}' in {r['unit']} summed into a {unit} headline (R-T587-1 (e))")
        e = evid(r)
        out.setdefault(r["class"], {}).setdefault(e, D(0))
        out[r["class"]][e] += D(r["delta"])
    return {k: {e: s(v) for e, v in sorted(m.items())} for k, m in sorted(out.items())}


# ================================================================================ generic cause rows ===============
def rows_from(causes: list[dict], unit: str, src: str, ver: str, sign: int, evid, prefix: str = "",
              omission_verified: bool = False) -> tuple[list[dict], list[dict], list[dict]]:
    """Cause rows to reference - engine (sign -1 for ours - his, +1 for his - ours); AGREE beside; mapped by name."""
    rows, agree, moves = [], [], []
    asum = D(0)
    for c in causes:
        amt = D(c["amount"]) * sign
        if c["verdict"] == "AGREE":
            asum += amt
            agree.append({"label": prefix + c["label"], "kind": c.get("kind"), "amount": s(amt)})
            continue
        kw = {"source_verdict": c["verdict"], "kind_of_cause": c.get("kind")}
        if c.get("bound") is not None:
            kw["bound"] = c["bound"]
        if c["verdict"] in Z.CLASSES:
            k = c["verdict"]
        elif c["verdict"] == "ENGINE_OMISSION" and omission_verified:
            k = OMISSION_TO
            kw.update(tag="F-T587-3", mapped_because="ENGINE_OMISSION Checker VERIFIED -> ENGINE_WRONG with its fix row")
            moves.append({"tag": "F-T587-3", "section_id": src, "row": prefix + c["label"], "from": c["verdict"],
                          "to": k, "delta": s(amt)})
        elif c["verdict"] == "CONFLICT_BOUNDED":
            k = "UNRESOLVED"
            kw.update(tag="F-T587-4", mapped_because="CONFLICT reading kept, never resolved by majority (R-T566-1)")
        else:
            raise StatementError(f"{src}: verdict '{c['verdict']}' neither a class nor mapped by name (R-T587-1)")
        r = row(prefix + c["label"], amt, k, unit, src, ver, **kw)
        rows.append(stamp(r, evid(c), ver))
    if asum != 0:
        raise StatementError(f"{src}: AGREE terms net {asum}, not 0")
    return rows, agree, moves


# ================================================================================ T-576 columns (m3) ==============
def _reading(d: dict, r10e0: str, r10ae: str = "C3") -> dict:
    hit = [r for r in d["readings"] if r["reading"] == {"10AE": r10ae, "10E0": r10e0}]
    if len(hit) != 1:
        raise StatementError(f"T-576: reading 10AE {r10ae} / 10E0 {r10e0} not found once")
    return hit[0]


def _t576_rows(rd: dict, storey: str, ver: str) -> tuple[list[dict], dict]:
    col = rd["columns"][storey]
    rows, by_term = [], {}
    for m in col["marks_all"]:
        if not m["in_measured_set"]:
            continue
        for t in m["terms"]:
            amt = -D(t["m3"])                            # ours - his -> reference - engine
            if t["class"] in Z.CLASSES:
                k, kw = t["class"], {}
            elif t["class"] == "CONFLICT_BOUNDED":
                k, kw = "UNRESOLVED", {"tag": "F-T587-4", "mapped_because": "CONFLICT_BOUNDED: a reading of a "
                                       "conflicting drawn mark, never resolved by majority (R-T566-1, R-T587-1 (d))"}
            else:
                raise StatementError(f"T-576 {storey} {m['mark']}: class {t['class']} not mapped")
            if t.get("open_below"):
                kw["open_below"] = True
            if t.get("note"):
                kw["note"] = t["note"]
            r = row(f"{storey} {m['mark']}: {t['term']}", amt, k, "m3", f"T-576 {storey} measured set", ver,
                    term=t["term"], source_class=t["class"], **kw)
            rows.append(stamp(r, ev_t576(t["term"], storey, t["class"]), ver))
            by_term[t["term"]] = by_term.get(t["term"], D(0)) + amt
    ms = col["measured_set"]
    if s(sum((D(r["delta"]) for r in rows), D(0))) != neg(ms["diff_m3"]):
        raise StatementError(f"T-576 {storey}: terms do not re-add to the measured-set difference")
    return rows, by_term


def t576_sections(d: dict, v5: dict) -> tuple[list[dict], list[dict]]:
    """Reading of record (V5: 10AE C3 / 10E0 C8) restates V5 T-572/measured-columns_<storey>; 10E0 C7 shown too."""
    rec, alt = _reading(d, "C8"), _reading(d, "C7")
    for st in ("GF", "1F"):                              # 10AE C vs C3 never moves the measured set (asserted)
        if _reading(d, "C8", "C")["columns"][st]["measured_set"] != rec["columns"][st]["measured_set"]:
            raise StatementError(f"T-576 {st}: the 10AE reading moves the measured set")
    secs, moves = [], []
    v5s = {c["section_id"]: c for c in v5["sections_v5"]}
    for st in ("GF", "1F"):
        old = v5s[f"T-572/measured-columns_{st}"]
        ms = rec["columns"][st]["measured_set"]
        if (s(D(ms["his_m3"])), s(D(ms["engine_m3"]))) != (old["reference_total"], old["engine_valued"]):
            raise StatementError(f"T-576 {st}: measured set differs from V5 (restate, never rewrite: R-T587-1 (c))")
        rows, by_term = _t576_rows(rec, st, V576)
        sec = Z.section(f"T-576/columns-{st}", "T-576", f"B10 {st} columns, measured set ({len(ms['marks'])} marks), "
                        "by signed cause", "m3", ms["his_m3"], ms["engine_m3"], rows,
                        basis=old["reference_basis"], kind="LIKE_FOR_LIKE_MEASURED_SET", verification=V576, pct=True,
                        reading="10AE C3 / 10E0 C8 (reading of record, V4 T-551/columns)",
                        restates=old["section_id"])
        sec["beside"] = {"open_counter_terms": ms["open_counter_terms"],
                         "net_of_RULE_DIFFERENCE": {"difference": s(D(sec["difference"]) -
                                                                    D(sec["by_class"]["RULE_DIFFERENCE"])),
                                                    "note": "beside only"}}
        # (c) the V5 split restated: every term equal except the V5 UNRESOLVED amount, now inside JOINT_HEAD
        v5t = {r["name"].split(": ", 1)[1]: (D(r["delta"]), r["class"]) for r in old["rows"]}
        unres = [(n, v) for n, (v, c) in v5t.items() if c == "UNRESOLVED"]
        if len(unres) != 1:
            raise StatementError(f"T-576 {st}: V5 carries {len(unres)} UNRESOLVED terms, expected 1")
        uname, uamt = unres[0]
        for term, amt in by_term.items():
            was = v5t.get(term, (D(0), None))[0]
            if term == "JOINT_HEAD":
                if amt - was != uamt:
                    raise StatementError(f"T-576 {st}: JOINT_HEAD moves {amt - was}, not the V5 UNRESOLVED {uamt}")
            elif amt != was:
                raise StatementError(f"T-576 {st}: term {term} {amt} != V5 {was}")
        moves.append({"tag": "F-T587-1", "section_id": sec["section_id"], "row": f"{st} {uname} (V5 "
                      f"{old['section_id']})", "from": "UNRESOLVED", "to": "RULE_DIFFERENCE", "delta": s(uamt),
                      "why": "T-576: the open head term is the JOINT_HEAD at the printed lower depth D_low of the "
                             "named framing member (D_ctrl open below: JOINT_HEAD / GLOBAL_DEPTH split bounded, the "
                             "total closes)", "verdict": V576})
        secs.append(sec)
    for st in ("GF", "1F"):
        ms = alt["columns"][st]["measured_set"]
        rows, _ = _t576_rows(alt, st, V576)
        sec = Z.section(f"T-576/columns-{st}-reading-10E0-C7", "T-576", f"B10 {st} columns, measured set under the "
                        "10E0 C7 reading (CONFLICT, R-T566-1)", "m3", ms["his_m3"], ms["engine_m3"], rows,
                        basis="the same his rows, measured set under the other reading of the conflicting mark",
                        kind="CONFLICT_READING", verification=V576, reading="10AE C3 / 10E0 C7",
                        reading_of_record=False)
        sec["pct_refused_because"] = "a conflict reading is shown beside the reading of record, never as a verdict"
        secs.append(sec)
    return secs, moves


V4_EVIDENCE = {"CHECKER_CONFIRMED": CV, "WORKER_PROPOSED": WP, PV: PV}


def reclose_v4(sec: dict) -> None:
    """A V4 section (rows without a unit field) re-closed: residual 0, class totals from the rows."""
    diff = D(sec["reference_total"]) - D(sec["engine_valued"])
    tot = sum((D(r["delta"]) for r in sec["rows"]), D(0))
    if tot != diff or s(diff) != sec["difference"]:
        raise StatementError(f"{sec['section_id']}: rows {tot} != reference - engine {diff}")
    bc, bg = Z.zero_classes(), Z.zero_classes()
    for r in sec["rows"]:
        bc[r["class"]] += D(r["delta"])
        bg[r["class"]] += abs(D(r["delta"]))
    sec["by_class"] = {k: s(v) for k, v in bc.items()}
    sec["by_class_gross_abs"] = {k: s(v) for k, v in bg.items()}


def t576_beam_restate(d: dict, v4: dict) -> tuple[dict, dict]:
    """(c) V4 T-545/beams: the GF B7 UNTRACED row (UNRESOLVED) -> RULE_DIFFERENCE THROUGH_SUPPORT (T-576)."""
    old = [c for c in v4["sections"] if c["section_id"] == "T-545/beams"][0]
    b7 = d["beam_gf_b7"]
    if b7["result"]["class"] != "THROUGH_SUPPORT" or D(b7["result"]["UNTRACED_m3"]) != 0:
        raise StatementError("T-576 GF B7: not resolved to THROUGH_SUPPORT")
    sec = copy.deepcopy(old)
    hit = [r for r in sec["rows"] if r["name"] == "GF: UNTRACED -> GF B7 UNRESOLVED"]
    if len(hit) != 1 or hit[0]["class"] != "UNRESOLVED" or hit[0]["delta"] != neg(b7["t545_split_m3"]["UNTRACED"]):
        raise StatementError("T-545/beams: the GF B7 UNTRACED row is not the T-576 amount")
    r = hit[0]
    r.update({"class": "RULE_DIFFERENCE", "tag": "F-T587-2", "was_class": "UNRESOLVED", "source_cause": "THROUGH_SUPPORT",
              "verification": PV, "verification_basis": "T-576 Gate A: THROUGH_SUPPORT accepted on 2 / 14 piece ends "
              "(Checker own read), UNTRACED 0 rests on the worker's 12 other ends",
              "mapped_because": b7["result"]["verdict"]})
    for x in sec["rows"]:                                # V4 vocabulary -> R-T587-1 (a) status, row by row
        if "unit" in x:
            raise StatementError("T-545/beams: a V4 row already carries a unit")
        x["unit"] = sec["unit"]
        stamp(x, V4_EVIDENCE[x["verification"]], x.get("verification_basis") or x["verification"])
    sec["section_id"] = "T-545/beams@V7"
    sec["restates"] = "T-545/beams"
    reclose_v4(sec)
    if (sec["reference_total"], sec["engine_valued"], sec["difference"]) != \
            (old["reference_total"], old["engine_valued"], old["difference"]):
        raise StatementError("T-545/beams@V7: totals moved")
    mv = {"tag": "F-T587-2", "section_id": sec["section_id"], "row": r["name"], "from": "UNRESOLVED",
          "to": "RULE_DIFFERENCE", "delta": r["delta"], "why": "T-576 s.B7: his B7 lengths run into the carriers that "
          "close the curved pieces; allowance 3.55 m covers the 2.363 m excess", "verdict": V576}
    return sec, mv


# ================================================================================ T-578 rails (lm) ================
def t578_rails(d: dict) -> dict:
    r = d["rails_lm"]
    if r["sign"] != "his - ours":
        raise StatementError("T-578: rails sign changed")
    cc = d["code_closure"]
    valued = D(cc["FIN.RAILING"]["valued_lm"]) + D(cc["MET.RAILING.GUARD"]["valued_lm"])
    if s(valued) != r["ours"]["total"]:
        raise StatementError("T-578: rails ours != the candidate railing + guard lines valued")
    rows, agree, _ = rows_from(r["causes"], "lm", "T-578/rails", V578, +1,
                               lambda c: ev_t578_rail(c["label"], c["verdict"]))
    sec = Z.section("T-578/rails", "T-578", "B7-09 / B13-08 railings, balustrades and guards", "lm", r["his"]["value"],
                    r["ours"]["total"], rows, basis=f"his lone typed constant {r['his']['cell']} (label lm, no row "
                    "behind it; register FREELANCER_RAW_ROWS, not re-read by the Checker)", verification=V578)
    sec["pct_refused_because"] = r["pct_withheld"]
    sec["beside"] = {"agree_rows": agree, "held_bound_lm": r["ours"]["held_bound"],
                     "like_for_like_hypothesis_A": r["like_for_like_hypothesis_A"],
                     "by_family_lm": r["ours"]["by_family"],
                     "reader_lines_retired": r["reader_lines_retired"]}
    return sec


# ================================================================================ T-584 steps (lm, nr) ============
STEP_OWNER = {"ST-01": "T-584/stair-steps", "ST-02": "T-584/stair-steps", "ST-03": "T-577/marble-lm@V7"}


def t584_sections(d: dict, d578: dict) -> tuple[list[dict], list[dict]]:
    """ST-01 / ST-02 vs the released FIN.STAIR.STEP_LM lines; ST-03 (E1) cells stay in T-577/marble-lm (b)."""
    if d["sign"] != "ours - his":
        raise StatementError("T-584: sign changed")
    secs, nc = [], []
    for unit in ("lm", "nr"):
        groups = [g for g in d["tables"]["stairs"][unit] if STEP_OWNER[g["id"]] == "T-584/stair-steps"]
        rows, agree = [], []
        for g in groups:
            if sum((D(c["amount"]) for c in g["causes"]), D(0)) != D(g["gap"]):
                raise StatementError(f"T-584 {g['id']} {unit}: causes do not close the gap")
            rr, ag, _ = rows_from(g["causes"], unit, f"T-584/stair-steps-{unit}", V584, -1,
                                  lambda c, sid=g["id"]: ev_t584(sid, c["verdict"], c["label"]), prefix=f"{g['id']}: ")
            rows += rr
            agree += ag
        his = sum((D(g["his"]) for g in groups), D(0))
        ours = sum((D(g["ours"]) for g in groups), D(0))
        if unit == "lm" and ours != D(d578["code_closure"]["FIN.STAIR.STEP_LM"]["valued_lm"]):
            raise StatementError("T-584: ST-01 + ST-02 != the candidate FIN.STAIR.STEP_LM valued")
        sec = Z.section(f"T-584/stair-steps-{unit}", "T-584", f"B7-06 stair steps ST-01 / ST-02 ({unit}, commercial "
                        "step basis per tread, UP-STAIR-008)", unit, his, ours, rows,
                        basis="his marble-sheet step rows of ST-01 / ST-02 (count x width, booked in his area column, "
                              "compared in lm from his own count and width cells); E1 (ST-03) cells are owned by "
                              "T-577/marble-lm@V7", verification=V584)
        sec["pct_refused_because"] = "HELD and UNRESOLVED causes (R-T584-1)"
        sec["beside"] = {"agree_rows": agree, "per_stair": {g["id"]: {"his": g["his"], "ours": g["ours"]}
                                                            for g in groups}}
        secs.append(sec)
    m2 = d["tables"]["stairs"]["m2"][0]
    nc.append({"block_id": "T-584/stair-steps-in-area-column", "report": "T-584", "trade": "his stair-step rows ST-01 / "
               "ST-02 booked in his area column", "unit": "lm (in his m2 column)", "status": "NOT_COMPARABLE",
               "reference_total": s(sum((D(g["his"]) for g in d["tables"]["stairs"]["lm"] if g["id"] != "ST-03"),
                                        D(0))),
               "difference": None, "difference_pct_of_reference": None, "engine_valued": None,
               "information": f"count x length in an area column (UNIT, R-T586-1 (b)); his total {m2['his']} in that "
                              "column also holds the E1 cells already in the T-577 block (never listed twice)",
               "verification": V584})
    return secs, nc


def t584_marble_lm_restate(v6: dict, d: dict) -> tuple[dict, list[dict]]:
    """(c) V6 T-577/marble-lm restated: E1 step lm 11.20 UNRESOLVED (F-T586-1) -> ENGINE_WRONG (Checker VERIFIED
    ENGINE_OMISSION, fix row FR-T584-1); the 30A edge RULE_DIFFERENCE AGREED; door steps beside (FR-T584-2, T-592)."""
    old = [c for c in v6["sections_v6"] if c["section_id"] == "T-577/marble-lm"][0]
    sec = copy.deepcopy(old)
    st3 = [g for g in d["tables"]["stairs"]["lm"] if g["id"] == "ST-03"][0]
    om = [c for c in st3["causes"] if c["verdict"] == "ENGINE_OMISSION"]
    edge = [c for c in st3["causes"] if c["verdict"] == "RULE_DIFFERENCE"]
    if len(om) != 1 or len(edge) != 1 or D(st3["his"]) != sum((D(r["delta"]) for r in sec["rows"]
                                                               if r["name"].startswith("E1_STEPS")), D(0)):
        raise StatementError("T-577/marble-lm: E1 rows are not the T-584 ST-03 cells")
    moves = []
    for r in sec["rows"]:
        if r["name"].startswith("E1_STEPS") and r.get("tag") == "F-T586-1":
            if D(r["delta"]) != -D(om[0]["amount"]) or D(d["e1"]["lm"]) != D(r["delta"]):
                raise StatementError("E1 step lm: V6 row is not the T-584 11.20 lm")
            r.update({"class": OMISSION_TO, "tag": "F-T587-3", "was_class": "UNRESOLVED (F-T586-1)",
                      "mapped_because": "ENGINE_OMISSION Checker VERIFIED (T-584): fix row FR-T584-1, wiring manifest "
                                        "V9 (T-588)"})
            stamp(r, CV, V584)
            moves.append({"tag": "F-T587-3", "section_id": "T-577/marble-lm@V7", "row": r["name"],
                          "from": "UNRESOLVED", "to": OMISSION_TO, "delta": r["delta"], "verdict": V584})
        elif r["name"].startswith("E1_STEPS"):
            if D(r["delta"]) != -D(edge[0]["amount"]):
                raise StatementError("E1 platform edge: V6 row is not the T-584 2.80 lm")
            stamp(r, CV, V584)
        elif r["name"].startswith("EXT:") and r["class"] == "UNRESOLVED":
            if D(r["delta"]) != D(d["tables"]["doors"]["lm"][0]["his"]):
                raise StatementError("EXT door steps: V6 row is not his T-584 door-step cells")
            r["note_v7"] = ("T-584 + ELEMENT_REGISTER EXTERNAL DOOR STEP (Lead 04:15): the drawn edge pair on the wall "
                            "face is ONE element (threshold nosing + riser), owner trade marble / stone thresholds; "
                            "drawn 3.50 lm at D-GF-01 / 03 / 05 / 09, no candidate line yet (FR-T584-2, T-592); his 6 "
                            "pieces carry no door id: UNRESOLVED stands")
            stamp(r, PV, V584)
        else:
            stamp(r, ev_v6("T-577/marble-lm", r), old["verification"])
    if len(moves) != 1:
        raise StatementError("T-577/marble-lm: F-T586-1 row not found once")
    sec["section_id"] = "T-577/marble-lm@V7"
    sec["restates"] = "T-577/marble-lm"
    close_section(sec)
    if (sec["reference_total"], sec["engine_valued"]) != (old["reference_total"], old["engine_valued"]):
        raise StatementError("T-577/marble-lm@V7: totals moved")
    doors = d["tables"]["doors"]
    sec["beside"] = dict(old["beside"], door_steps_t584={
        "element": "threshold nosing + riser, ONE element (FR-T584-3, ELEMENT_REGISTER EXTERNAL DOOR STEP)",
        "drawn_lm": doors["lm"][0]["ours"], "drawn_nr": doors["nr"][0]["ours"], "riser_m2": doors["m2"][0]["ours"],
        "riser_held_m2": [c for c in doors["m2"][0]["causes"] if c["verdict"] == "HELD"][0]["bound"],
        "gate_lm_not_re_read": doors["lm"][1]["ours"],
        "candidate_line": None,
        "status": "the EXT row (+7.7 lm UNRESOLVED) is unchanged: no candidate line yet; his 6 pieces carry no door id; "
                  "FR-T584-2 enters wiring manifest V10 after T-592 settles ONE paid length (visible edge 3.50 vs strip "
                  "3.80 lm, F-C-T584-1); D-GF-09 riser bound CONDITIONAL (F-C-T584-2)"})
    return sec, moves


# ================================================================================ T-578 nosing (cross-reference) ==
def t578_nosing_xref(d: dict, steps: list[dict], marble_lm: dict) -> dict:
    """(b) his step cells are compared once (T-584/stair-steps, T-577/marble-lm@V7); the T-412 nosing census has no
    candidate line (T-424): its T-578 comparison stays beside, never re-added."""
    n, nn = d["nosing_lm"], d["nosing_nr"]
    if d["code_closure"]["nosing_lines_in_candidate"] != 0:
        raise StatementError("T-578: a nosing line exists; the cross-reference would become a section")
    owners, census = {}, []
    lm_sec = [c for c in steps if c["section_id"] == "T-584/stair-steps-lm"][0]
    for g in n["groups"]:
        owner = STEP_OWNER[g["stair"]]
        owners.setdefault(g["his_cells"], set()).add(owner)
        if owner == "T-584/stair-steps":
            ref = lm_sec["beside"]["per_stair"][g["stair"]]["his"]
        else:
            ref =s(sum((D(r["delta"]) for r in marble_lm["rows"] if r["name"].startswith("E1_STEPS")), D(0)))
            # E1 has no step line (engine 0 on these rows): reference - engine = his E1 cells
        if D(ref) != D(g["his"]):
            raise StatementError(f"T-578 nosing {g['stair']}: his {g['his']} != the owning section's cells {ref}")
        census.append({"stair": g["stair"], "his_cells": g["his_cells"], "his_lm": g["his"],
                       "owned_by_section": owner + ("-lm" if owner == "T-584/stair-steps" else ""),
                       "nosing_census_lm": g["ours"], "held_bound": g["held_bound"],
                       "causes_his_minus_census": [{"verdict": c["verdict"], "amount": c["amount"],
                                                    "label": c["label"]} for c in g["causes"]]})
    if any(len(v) != 1 for v in owners.values()):
        raise StatementError("T-578 nosing: a reference cell owned by two sections (R-T587-1 (b))")
    return {"block_id": "T-578/nosing-xref", "kind": "CROSS_REFERENCE", "report": "T-578",
            "units": {"lm": {"his": n["totals"]["his"], "nosing_census": n["totals"]["ours"],
                             "gap": n["totals"]["gap"], "held_n": n["totals"]["held_n"]},
                      "nr": {"his": nn["totals"]["his"], "nosing_census": str(nn["totals"]["ours"]),
                             "gap": nn["totals"]["gap"]}},
            "candidate_line": False, "difference_added": False, "pct": None,
            "census": census,
            "note": "his only lm along the stair edges is each step row's count x width: one set of cells, compared "
                    "once against the released step lines (B7-06); the B7-05 nosing census (T-412, one edge per "
                    "riser, arrival edges included) has no candidate line (T-424): beside only (R-T587-1 (b)). Whether "
                    "B7-05 nosing and B7-06 step lm may both carry one drawn front edge is T-588's cross-trade census "
                    "(ELEMENT_REGISTER NOSING EDGE)",
            "verification": V578}


# ================================================================================ T-583 bar components (t) ========
def check_high_open(r: dict) -> None:
    """(e) HELD_RANGE_HIGH_OPEN: 0 < low, no t_high, a bounded part beside that is never a high."""
    if r.get("unit") != "t":
        raise StatementError(f"{r.get('row_id')}: row in {r.get('unit')} inside a t block (R-T587-1 (e))")
    st = r.get("status")
    if st == "HELD_RANGE_HIGH_OPEN":
        if r.get("t_low") is None or D(str(r["t_low"])) <= 0 or r.get("t_high") is not None:
            raise StatementError(f"{r['row_id']}: high-open row needs 0 < low and no high (R-T587-1 (e))")
        if r.get("t_high_bounded_part") is None or D(str(r["t_high_bounded_part"])) < D(str(r["t_low"])):
            raise StatementError(f"{r['row_id']}: bounded part missing or below the low")
        if r.get("value") is not None or r.get("valued") not in (None, 0, "0"):
            raise StatementError(f"{r['row_id']}: a held row carried as a value")
    elif st == "HELD_BLANK":
        if r.get("t_low") is not None or r.get("t_high") is not None or not r.get("missing"):
            raise StatementError(f"{r['row_id']}: HELD_BLANK with a figure or no named blank")
    else:
        raise StatementError(f"{r.get('row_id')}: status {st} is not HELD_RANGE_HIGH_OPEN / HELD_BLANK")


def t583_beside(d: dict, v6: dict, v8: dict) -> dict:
    prev = v6["beside_v6"][0]
    v8ids = {r["expected_after"]["element_id"]: r for r in v8["rebar_omission"]["rows"]}
    prev_rows = {r["row_id"]: r for r in prev["rows"]}
    rows, lo, part = [], D(0), D(0)
    for r in d["rows"]:
        check_high_open(r)
        if r["row_id"] not in v8ids or r["row_id"] not in prev_rows:
            raise StatementError(f"T-583 {r['row_id']}: not a V8 REBAR_OMISSION row of T-575")
        if v8ids[r["row_id"]]["concrete_line"] != r["concrete_line"]:
            raise StatementError(f"T-583 {r['row_id']}: concrete line differs from V8")
        x = {"row_id": r["row_id"], "status": r["status"], "concrete_line": r["concrete_line"], "unit": "t",
             "t560_group": prev_rows[r["row_id"]]["t560_group"], "t575": prev_rows[r["row_id"]].get("range_t")}
        if r["status"] == "HELD_RANGE_HIGH_OPEN":
            if D(str(r["t_low"])) < D(prev_rows[r["row_id"]]["range_t"][0]):
                raise StatementError(f"T-583 {r['row_id']}: low below the T-575 low (components only add)")
            x["at_least_t"] = s(D(str(r["t_low"])))
            x["bounded_part_t_not_a_high"] = s(D(str(r["t_high_bounded_part"])))
            x["high_excluding"] = json.loads(r["high_excluding"]) if isinstance(r["high_excluding"], str) \
                else r["high_excluding"]
            lo += D(str(r["t_low"]))
            part += D(str(r["t_high_bounded_part"]))
        else:
            x["blank_named"] = r["missing"]
        rows.append(x)
    tt = d["totals"]
    if (s(lo), s(part)) != (s(D(str(tt["t_low"]))), s(D(str(tt["t_high_bounded_part"])))) or tt["valued_t"] != 0.0 \
            or tt["t_high"] is not None:
        raise StatementError("T-583: rows do not re-add to its totals, a high is set, or something is valued")
    e = prev["expected_after_v8_rebar_rows"]
    g5lo = D(e["v5_held_range_t"][0])
    dome_lo = sum((D(x["at_least_t"]) for x in rows if x["t560_group"] == "G5_STAIRS_DOME" and "at_least_t" in x),
                  D(0))
    r560 = [c for c in v6["sections_v5"] if c["section_id"] == "T-560/rebar"][0]
    g5 = [x for x in r560["rows"] if x["name"].startswith("G5_")][0]
    his, val = D(g5["his_t"]), D(g5["engine_valued_t"])
    lift = [r for r in d["rows"] if r["row_id"] == "LIFT_PIT:WALLS:REBAR"][0]
    f = json.loads(lift["formula"]) if isinstance(lift["formula"], str) else lift["formula"]
    return {
        "block_id": "T-583/dome-lift-components", "kind": "HELD_RANGE_HIGH_OPEN_BESIDE", "report": "T-583", "unit": "t",
        "candidate_line": False, "valued_t": "0", "supersedes_beside": prev["block_id"],
        "at_least_t": s(lo), "high": "OPEN (laps, hooks, anchorage, ring depth by name)",
        "bounded_part_t_not_a_high": s(part), "t575_was_t": prev["range_t"],
        "held_blank_rows": sum(1 for x in rows if x["status"] == "HELD_BLANK"), "rows": rows,
        "tighter_low_if_per_face_F_C_T583_1_t": "0.789554",
        "reference": prev["reference"],
        "statement_effect": "none on any column: V8 REBAR_OMISSION manifest rows, not candidate lines (R-T579-1 (c)); "
                            "the T-575 high 1.161932 t was mains only and is no longer a high (R-T587-1 (e))",
        "expected_after_v8_rebar_rows": {
            "group": "G5_STAIRS_DOME", "v5_held_low_t": s(g5lo), "plus_t583_at_least_t": s(dome_lo),
            "held_at_least_t": s(g5lo + dome_lo), "held_high": "OPEN",
            "residual_after_held_at_most_t": s(his - val - g5lo - dome_lo),
            "note": "EXPECTED only, never valued; residual vs his TYPED_LUMP: at most this, no lower figure, no %"},
        "g2_lift_walls": {"status": "HELD_BLANK (h not printed)", "kg_of_h": f["kg(h)"], "A_t_per_m": f["A_t_per_m"],
                          "B_t": f["B_t"], "A_low_was_t575": "0.169284 (F-C-T575-1: not strict, closed by T-583)"},
        "verification": V583,
    }
