"""T-449 round 1 (CONCRETE): the A1 correction register of every concrete-trade entry of the V3.0.16+ project inputs.

Owner follow-up directive 2026-11-02 (MISSION.md, A1): every project-specific correction is
  (A) a DRAWING-DERIVED RULE (reusable logic with tests),
  (B) a DECLARED PROJECT FACT (per-project config, URBAN_PROJECT_CONFIG_V1, engine/project_config.py), or
  (C) an UNEXPLAINED PATCH (made only to match the freelancer or an earlier engine result): removed.

Scope of this round: the concrete entries (item codes STR.CONC.*) of the merged input builders of
  V3.0.17 (T-254, URBAN_V3017_INPUTS_V1), V3.0.18 (T-266, V3018), V3.0.23 (T-319, V3023), V3.0.33 (T-397, V3033)
  and V3.0.40 (T-430, V3040). V3.0.16 (T-245) is the project identity (class B, carried by T-450 part 2); V3.0.30
  formwork rides the concrete members and is a later round; non-concrete records of these builders are listed as
  out of scope (another trade's round).

For every entry the register records: version, schema, line, action, the patch (value / state / range), class, the
general rule, the facts it uses, and, where the rule is implemented (engine/source/concrete_basis_rules_v1.py), the
rule's result from the declared facts plus the Checker-merged drawing geometry beside the patch:
  A-REPRODUCED   the generic rule + declared facts give the patch's state and quantity (residual named)
  A-SPECIFIED    drawing-derived and Checker-verified, the rule is named, its generic code is not written yet:
                 the per-line input stays until it is (it is NOT an unexplained patch)
  B              the entry is itself a declared project fact (none in the concrete round: facts are in the config)
  C              its basis is a freelancer / benchmark / earlier engine figure: removed (none found)

Read-only: imports the merged builders (each pins its own ledgers by sha256), writes only where it is told to.

    python3 -I research/agents_t449/t449_concrete_register.py [out_dir]
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.project_config import load_project_config  # noqa: E402
from engine.source import concrete_basis_rules_v1 as R  # noqa: E402

HERE = Path(__file__).resolve().parent
FACTS = HERE / "DEVELOPMENT-VILLA-T131.concrete_facts.json"
T253 = ROOT / "research/agents_t253/LEDGER_T253.csv"
T256 = ROOT / "research/agents_t256/LEDGER_T256.csv"
PAIR = ROOT / "research/agents_t289/BAND_PAIRING_T289.json"
PINS = {T253: None, T256: "59c4700e826107fbf1f3f1176054f233bb267d4988629b84769b90b1b690e5ea", PAIR: None}
BUILDERS = {  # version -> (task, path)
    "ARCH_TAKEOFF_V3.0.17": ("T-254", "research/agents_t254/t254_inputs.py"),
    "ARCH_TAKEOFF_V3.0.18": ("T-266", "research/agents_t266/t266_inputs.py"),
    "ARCH_TAKEOFF_V3.0.23": ("T-319", "research/agents_t319/t319_inputs.py"),
    "ARCH_TAKEOFF_V3.0.33": ("T-397", "research/agents_t397/t397_inputs.py"),
    "ARCH_TAKEOFF_V3.0.40": ("T-430", "research/agents_t430/t430_inputs.py"),
}
PRINT_TOL = 0.00005    # the merged ledgers print m3 to 4 decimals: a residual up to half a unit is that print
EXACT_TOL = 1e-6
C_WORDS = re.compile(r"freelancer|workbook|benchmark|reference boq|to match", re.I)

# held items named by the ledgers -> the declared fact that would release them (absent in the config = HELD)
# undeclared on purpose: each is an open item; declaring one is the owner's / designer's answer
HELD_ITEM_FACT = {"D-39_ROOF_DATUM": "LEVEL.STRUCTURAL_TOP.ROOF.MAIN",
                  "Q-54B_ANNEX_ROOF_DATUM": "LEVEL.STRUCTURAL_TOP.ROOF.ANNEX",
                  "court section not printed": "GB.EXTERIOR.DEPTH_BASIS.COURT"}
STOREY_LEVELS = {"GF": ("LEVEL.STRUCTURAL_TOP.GF.MAIN", "LEVEL.STRUCTURAL_TOP.1F.MAIN"),
                 "1F": ("LEVEL.STRUCTURAL_TOP.1F.MAIN", "LEVEL.STRUCTURAL_TOP.2F.MAIN")}
SPECIFIED_RULES = {
    "NOT_PRESENT": ("R-COL-ABSENCE-1", "a type-table column band with no outline, text or start / stop symbol on any "
                                       "searched sheet is NOT_PRESENT with its absence evidence (T-256 s.4)"),
    "BOUNDARY_ADD": ("R-GB-BOUNDARY-SHARE-1", "boundary ground beam = drawn band less the boundary-column share; the "
                                              "column count is not printed -> HELD with the band as upper bound"),
    "SPLIT": ("R-STAIR-PIECES-1", "a stair line = the sum of its drawn pieces by status (T-258 r2 ledger); held "
                                  "pieces blank by name, never summed into a closable part"),
    "STAIR_REBASE": ("R-STAIR-PIECES-1", "the landing line rebased to its drawn plates (T-258 / T-290)"),
    "STAIR_HOLD": ("R-STAIR-PIECES-1", "a flight with no printed basis stays HELD by name"),
    "HELD_BOUND": ("R-HELD-BOUND-PIECES-1", "a held cell's bound is its own slab panels x printed thickness, the shaft "
                                            "and strips that are not slab removed (R-T391-5)"),
    "GAP_RESTORE": ("R-T392-1 / R-T392-2", "a deduction is only the drawn-cell overlap: the ring-overlap GAP from an "
                                           "overlay-fitted band set restored, DOUBLE and GAP reported apart (a defect "
                                           "of the band-subtraction code, to be fixed there)"),
    "MISSING_HELD": ("R-COMPLETENESS-DRAWN-ELEMENT-1", "a drawn element with no line gets one HELD line with its plan "
                                                      "figure beside (lift pit walls: depth 'as per manufacturer')"),
    "NECK_SPLIT": ("R-GB-NECK-CUT-1", "a band crossed by a founded neck is split into runs; the unloaded run takes its "
                                     "printed section, a run under a concentrated load (D-33) is HELD with its range"),
    "NECK_HOLD": ("R-GB-NECK-CUT-1", "a picked end of a printed range, or a run with no printed section, is HELD"),
}


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load(path):
    spec = importlib.util.spec_from_file_location(Path(path).stem + "_t449", ROOT / path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _csv(p):
    return list(csv.DictReader(io.StringIO(p.read_text(encoding="utf-8"))))


def _entry(version, task, schema, line, item, action, patch, cls, rule, rule_text, **kw):
    e = {"version": version, "task": task, "schema": schema, "line_id": line, "item_code": item, "action": action,
         "patch": patch, "class": cls, "rule": rule, "rule_text": rule_text}
    e.update(kw)
    return e


def _cls_c(rec):
    """Class C test: a basis that names a freelancer / benchmark / earlier-result figure."""
    return bool(C_WORDS.search(json.dumps(rec, ensure_ascii=False)))


def _reproduce(e, res, *, want_state, want_value=None, tol=PRINT_TOL, want_readings=None, readings_block=True):
    e["rule_result"] = {"state": res.state, "value": res.value, "low": res.low, "high": res.high,
                        "formula": res.formula, "facts_used": list(res.facts_used), "held_reason": res.held_reason,
                        "readings": dict(res.readings)}
    ok = res.state == want_state
    why = []
    if not ok:
        why.append(f"state {res.state} vs patch {want_state}")
    if want_value is not None:
        diff = None if res.value is None else round(res.value - want_value, 6)
        e["rule_minus_patch_m3"] = diff
        if diff is None or abs(diff) > tol:
            ok = False
            why.append(f"value {res.value} vs patch {want_value}")
        elif abs(diff) > EXACT_TOL:
            e["residual"] = f"{diff:+.6f} m3 = the merged ledger's 4-decimal print (rule unrounded)"
    for k, v in (want_readings or {}).items():
        got = (res.readings or {}).get(k)
        if got is None or abs(got - v) > tol:
            d = None if got is None else round(got - v, 6)
            msg = f"shown reading {k}: rule {got} vs merged ledger {v} (diff {d})"
            if readings_block:
                ok = False
                why.append(msg)
            else:   # a reading shown beside a CONFLICT line, never adopted: a finding, not a quantity
                e.setdefault("reading_findings", []).append(msg)
    e["class"] = "A-REPRODUCED" if ok else "A-SPECIFIED"
    if not ok:
        e["not_reproduced"] = "; ".join(why)
    return e


def concrete_t254(m, cfg, runs253, pairing):
    d = m.build()
    out, outside = [], []
    v, task, sch = "ARCH_TAKEOFF_V3.0.17", "T-254", d["schema"]
    for r in d["records"]:
        if not r["item_code"].startswith("STR.CONC."):
            outside.append((v, r["line_id"], r["item_code"]))
            continue
        act, lid, item = r["action"], r["line_id"], r["item_code"]
        if _cls_c(r):
            out.append(_entry(v, task, sch, lid, item, act, r.get("value"), "C", None,
                              "basis names a reference figure"))
            continue
        patch = {"value": r.get("value"), "state": r.get("status") or act, "held_item": r.get("held_item")}
        ev = {"before": r["before"], "source_task": r["task"], "physical_element": r["physical_element"]}
        if item == "STR.CONC.GROUND_BEAM":
            band = r["element_id"].rsplit(":", 1)[1]
            rids = [x["run"] for x in pairing["bands"][band]["runs"]]
            named = set(re.findall(r"runs? ([0-9A-Z:+#]+) ", r.get("formula", ""))) | set(
                re.findall(r"; ([0-9A-Z:+#]+) EXTERIOR", r.get("formula", "")))
            rids = [x for x in rids if x in runs253 and (not named or x in named)]
            runs = [R.Run(x, float(runs253[x]["L_m"]), float(runs253[x]["b_m"])) for x in rids]
            ev["runs"] = [{"run": x.run_id, "L_m": x.length_m, "b_m": x.width_m} for x in runs]
            if act == "REBASE":
                res = R.ground_beam_exterior(cfg, runs, top_level="LEVEL.STRUCTURAL_TOP.GF.MAIN",
                                             outer_ground_level="LEVEL.NATURAL_GROUND.OUTER",
                                             depth_basis="GB.EXTERIOR.DEPTH_BASIS.MAIN")
                e = _entry(v, task, sch, lid, item, act, patch, None, "R-GB-EXT-DEPTH-1",
                           "exterior ground beam: depth = structural top - outer natural ground; L x b x D per run",
                           evidence=ev)
                out.append(_reproduce(e, res, want_state=R.VALUED, want_value=r["value"]))
            elif act == "CONFLICT":
                lit = (r.get("scenario") or {}).get("readings", {}).get("literal_0_25_m")
                res = R.ground_beam_exterior(cfg, runs, top_level="LEVEL.STRUCTURAL_TOP.GF.ANNEX",
                                             outer_ground_level="LEVEL.NATURAL_GROUND.OUTER",
                                             depth_basis="GB.EXTERIOR.DEPTH_BASIS.ANNEX")
                e = _entry(v, task, sch, lid, item, act, patch, None, "R-GB-EXT-DEPTH-1",
                           "annex zone: depth basis an open designer item (D-35) -> CONFLICT, literal reading beside",
                           evidence=ev)
                out.append(_reproduce(e, res, want_state=R.CONFLICT, readings_block=False,
                                      want_readings={"literal_two_levels_m3": lit} if lit is not None else None))
            else:   # HOLD: court section not printed (neither its top nor its underside datum is printed)
                res = R.ground_beam_exterior(cfg, runs, top_level="LEVEL.STRUCTURAL_TOP.GF.COURT",
                                             outer_ground_level="LEVEL.GROUND.COURT",
                                             depth_basis=HELD_ITEM_FACT["court section not printed"])
                e = _entry(v, task, sch, lid, item, act, patch, None, "R-GB-EXT-DEPTH-1",
                           "court zone: no printed section -> its depth basis is not declared -> HELD", evidence=ev)
                out.append(_reproduce(e, res, want_state=R.HELD))
        elif act == "NOT_PRESENT":
            rule, txt = SPECIFIED_RULES["NOT_PRESENT"]
            out.append(_entry(v, task, sch, lid, item, act, {"state": "NOT_PRESENT"}, "A-SPECIFIED", rule, txt,
                              evidence=dict(ev, absence=r["absence_evidence"])))
        elif act == "HOLD":   # columns at an unprinted roof datum
            fids = [HELD_ITEM_FACT[k] for k in HELD_ITEM_FACT if k in (r.get("held_item") or "")]
            lk = [(f, cfg.lookup(f)) for f in fids]
            e = _entry(v, task, sch, lid, item, act, patch, None, "R-COL-LEVEL-HEIGHT-1",
                       "a column whose top level is not declared stays HELD", evidence=ev,
                       rule_result={"state": "HELD" if lk and all(not x.usable for _, x in lk) else "NOT_EVALUATED",
                                    "facts_used": fids, "held_reason": "; ".join(f"{f}: {x.reason}" for f, x in lk)})
            e["class"] = "A-REPRODUCED" if e["rule_result"]["state"] == "HELD" else "A-SPECIFIED"
            out.append(e)
        elif act == "REBASE":   # columns between two printed levels
            if r["group"] == "COL_ANNEX_7":
                g0, g1 = (cfg.lookup(f).base_value() for f in STOREY_LEVELS["GF"])
                section = r["before"]["measured_net"] / (g1 - g0)   # the candidate's schedule B x H x GF storey
                base, top = "LEVEL.STRUCTURAL_TOP.GF.ANNEX", "LEVEL.STRUCTURAL_TOP.1F.MAIN"
                ev["section_basis"] = (f"schedule B x H read back from the candidate line {r['before']['measured_net']}"
                                       f" m3 / main GF storey {g1 - g0:.2f} m = {section:.6f} m2")
            else:
                a, b = re.search(r"(\d\.\d+) x (\d\.\d+) =", r["formula"]).groups()
                section = float(a) * float(b)
                base, top = STOREY_LEVELS["1F"]
                ev["section_basis"] = f"printed P.C {a} x {b} (T-248)"
            res = R.column_between_levels(cfg, section, base_level=base, top_level=top)
            e = _entry(v, task, sch, lid, item, act, patch, None, "R-COL-LEVEL-HEIGHT-1",
                       "column = section x (top level - base level)", evidence=ev)
            out.append(_reproduce(e, res, want_state=R.VALUED, want_value=r["value"]))
        else:
            out.append(_entry(v, task, sch, lid, item, act, patch, "A-SPECIFIED", None, "unclassified action",
                              evidence=ev))
    for a in d.get("adds", []):
        rule, txt = SPECIFIED_RULES["BOUNDARY_ADD"]
        out.append(_entry(v, task, sch, a["id"], a["item_code"], "ADD_HELD",
                          {"state": a["state"], "upper_bound": a["scenario"]["readings"]["band_upper_bound"]},
                          "A-SPECIFIED", rule, txt, evidence={"held_item": a["held_item"]}))
    return out, outside


def concrete_t266(m):
    d = m.build()
    out, outside = [], []
    v, task, sch = "ARCH_TAKEOFF_V3.0.18", "T-266", d["schema"]
    for r in d["records"]:
        if not r["item_code"].startswith("STR.CONC."):
            outside.append((v, r["line_id"], r["item_code"]))
            continue
        key = {"SPLIT": "SPLIT", "REBASE": "STAIR_REBASE", "HOLD": "STAIR_HOLD"}[r["kind"]]
        rule, txt = SPECIFIED_RULES[key]
        out.append(_entry(v, task, sch, r["line_id"], r["item_code"], r["kind"],
                          {"before": r["before"], "group": r["group"]},
                          "C" if _cls_c(r) else "A-SPECIFIED", rule, txt,
                          evidence={"physical_element": r["physical_element"], "source_task": r["task"]}))
    return out, outside


def concrete_t319(m, cfg):
    d = m.build()
    out = []
    v, task, sch = "ARCH_TAKEOFF_V3.0.23", "T-319", d["schema"]
    for c in d["chains"]:
        res = R.parapet_rc_bounds(cfg, c["runs"], upstand_min="PARAPET.RC_UPSTAND.MIN_ABOVE_SLAB",
                                  material_item=c["material_item"])
        lo = sum(u["top_lo_m2"] * d["upstand"]["floor_m"] for u in c["runs"])
        hi = sum(u["top_hi_m2"] * u["h_hi_m"] for u in c["runs"])
        e = _entry(v, task, sch, None, "STR.CONC.PARAPET", "ADD_HELD_RANGE",
                   {"state": "HELD", "low": round(lo, 6), "high": round(hi, 6)}, None, "R-PARAPET-RC-FLOOR-1",
                   "parapet RC: low = top x printed upstand minimum, high = top x printed height; HELD on material",
                   element_id=c["element_id"], evidence={"chain": c["chain"], "runs": len(c["runs"]),
                                                         "source_task": c["task"]})
        e["rule_result"] = {"state": res.state, "low": res.low, "high": res.high, "formula": res.formula,
                            "facts_used": list(res.facts_used)}
        ok = res.state == "HELD" and abs(res.low - lo) <= EXACT_TOL and abs(res.high - hi) <= EXACT_TOL
        e["class"] = "A-REPRODUCED" if ok else "A-SPECIFIED"
        out.append(e)
    return out, []


def concrete_t397(m, cfg, led256):
    d = m.build()
    out = []
    v, task, sch = "ARCH_TAKEOFF_V3.0.33", "T-397", d["schema"]
    for r in d["rows"]:
        act = r["action"]
        if act != "CONFLICT_RANGE":
            rule, txt = SPECIFIED_RULES[act]
            patch = {k: r.get(k) for k in ("value", "low", "high", "beside") if r.get(k) is not None}
            out.append(_entry(v, task, sch, r.get("line_id"), r.get("item_code") or (r.get("expect") or {}).get(
                "item_code"), act, patch, "C" if _cls_c(r) else "A-SPECIFIED", rule, txt,
                element_id=r.get("element_id"), evidence={"source_tasks": r["source_tasks"],
                                                          "status": r["evidence_status"]}))
            continue
        L = led256[r["member"]]
        b0, b1 = (cfg.lookup(f).base_value() for f in STOREY_LEVELS[L["storey"]])
        h = round(b1 - b0, 6)
        res = R.column_section_conflict(m._area(L["schedule_cm"]), m._area(L["drawn_mm"]), h,
                                        designer_item=r["designer_item"])
        e = _entry(v, task, sch, r["line_id"], r["expect"]["item_code"], act,
                   {"state": "HELD", "readings": r["readings"]}, None, "R-COL-SECTION-CONFLICT-1",
                   "schedule vs drawn section -> CONFLICT range x storey height (declared levels)",
                   evidence={"member": r["member"], "storey": L["storey"], "ledger_h": float(L["h"]),
                             "facts_h": h, "levels": list(STOREY_LEVELS[L["storey"]])})
        _reproduce(e, res, want_state=R.CONFLICT, want_readings=r["readings"], tol=EXACT_TOL)
        if abs(float(L["h"]) - h) > EXACT_TOL:
            e["class"] = "A-SPECIFIED"
            e["not_reproduced"] = f"storey h {L['h']} vs declared levels {h}"
        out.append(e)
    return out, []


def concrete_t430(m):
    """The V3.0.40 neck cut. Its method (arch_v3040) already applies the rule to drawing readings; the register re-runs
    R-GB-NECK-CUT-1 from the same census readings and ties the unloaded runs to the Checker's own figure."""
    d = m.build()
    v, task, sch = "ARCH_TAKEOFF_V3.0.40", "T-430", d["schema"]
    rule, txt = SPECIFIED_RULES["NECK_SPLIT"]
    out = []
    for s in d["splits"]:
        b, c = s["b"], s["candidate"]
        runs = []
        for r in s["runs"]:
            res = R.ground_beam_split_run(b, r["spans"][0], r["spans"][1], r["printed_D"], r["loaded"], r["held_D"])
            want = R.HELD if r["loaded"] else R.VALUED
            row = {"run": r["run"], "loaded": r["loaded"], "state": res.state, "value": res.value, "low": res.low,
                   "high": res.high, "formula": res.formula, "ok": res.state == want}
            if res.state == R.VALUED:   # Checker T-426: 'unloaded halves 0.06 x 3.525 = 0.2115 each ENGINE_WRONG'
                row["candidate_minus_rule_m3"] = round(b * c["D"] * r["spans"][0] - res.value, 6)
                row["ok"] = row["ok"] and abs(row["candidate_minus_rule_m3"] - 0.2115) <= EXACT_TOL
            runs.append(row)
        cons = R.split_conserves_band(c["L"], [r["spans"][0] for r in s["runs"]], [n["length"] for n in s["necks"]])
        e = _entry(v, task, sch, s["line_id"], "STR.CONC.GROUND_BEAM", "NECK_SPLIT",
                   {"candidate": c, "runs": [r["run"] for r in s["runs"]],
                    "dispositions": {r["run"]: ("HELD" if r["loaded"] else "VALUED") for r in s["runs"]}},
                   None, rule, txt, evidence={"source_tasks": s["source_tasks"], "status": s["evidence_status"],
                                              "method": "engine/source/arch_v3040.py GB_RUN_SECTION"},
                   rule_result={"runs": runs, "band_conserved": cons, "facts_used": []})
        e["class"] = "C" if _cls_c(s) else ("A-REPRODUCED" if cons and all(x["ok"] for x in runs) else "A-SPECIFIED")
        out.append(e)
    for h in d["holds"]:
        rule2, txt2 = SPECIFIED_RULES["NECK_HOLD"]
        e = _entry(v, task, sch, h["line_id"], "STR.CONC.GROUND_BEAM", "HOLD_" + h["kind"],
                   {"candidate": h["candidate"], "range": h["range"]}, None, rule2, txt2,
                   evidence={"source_tasks": h["source_tasks"], "items": h["items"]})
        cand = h["candidate"]
        width = round(cand["value"] / (cand["D"] * cand["L"]), 6)   # the candidate's own drawn band width
        if h["kind"] == "RANGE":
            rg = h["range"]
            ds = [float(x) for x in re.findall(r"x (\d\.\d+) x", rg["low_basis"] + " " + rg["high_basis"])]
            ls = [float(x) for x in re.findall(r"x (\d+\.\d+) \(", rg["low_basis"] + " " + rg["high_basis"])]
            res = R.ground_beam_split_run(width, min(ls), max(ls), ds, False)
            ok = (res.state == R.HELD and abs(res.low - rg["low"]) <= EXACT_TOL
                  and abs(res.high - rg["high"]) <= EXACT_TOL)
        else:
            res = R.ground_beam_split_run(width, cand["L"], cand["L"], [], False)
            ok = res.state == R.HELD and res.value is None
        e["rule_result"] = {"state": res.state, "value": res.value, "low": res.low, "high": res.high,
                            "formula": res.formula, "held_reason": res.held_reason, "facts_used": []}
        e["class"] = "C" if _cls_c(h) else ("A-REPRODUCED" if ok else "A-SPECIFIED")
        out.append(e)
    return out, []


def fact_usage(entries):
    use = {}
    for e in entries:
        if e["class"] != "A-REPRODUCED":
            continue
        for f in (e.get("rule_result") or {}).get("facts_used", []):
            use.setdefault(f, set()).add(e["line_id"] or e["item_code"])
        for f in (e.get("evidence") or {}).get("levels", []):
            use.setdefault(f, set()).add(e["line_id"])
    return {k: sorted(v) for k, v in sorted(use.items())}


def build():
    cfg = load_project_config(FACTS)
    if _sha(T256) != PINS[T256]:
        raise SystemExit("T-256 ledger differs from the merged file")
    runs253 = {r["item"]: r for r in _csv(T253)}
    led256 = {r["member"]: r for r in _csv(T256)}
    pairing = json.loads(PAIR.read_text(encoding="utf-8"))
    mods = {v: _load(p) for v, (_, p) in BUILDERS.items()}
    entries, outside = [], []
    for part in (concrete_t254(mods["ARCH_TAKEOFF_V3.0.17"], cfg, runs253, pairing),
                 concrete_t266(mods["ARCH_TAKEOFF_V3.0.18"]),
                 concrete_t319(mods["ARCH_TAKEOFF_V3.0.23"], cfg),
                 concrete_t397(mods["ARCH_TAKEOFF_V3.0.33"], cfg, led256),
                 concrete_t430(mods["ARCH_TAKEOFF_V3.0.40"])):
        entries += part[0]
        outside += part[1]
    counts = {}
    for e in entries:
        counts[e["class"]] = counts.get(e["class"], 0) + 1
    by_rule = {}
    for e in entries:
        k = (e["rule"] or "-", e["class"])
        by_rule[f"{k[0]} | {k[1]}"] = by_rule.get(f"{k[0]} | {k[1]}", 0) + 1
    valued = [e for e in entries if e["class"] == "A-REPRODUCED" and e.get("rule_minus_patch_m3") is not None]
    return {
        "schema": "T449_CORRECTION_REGISTER_V1", "round": "1 CONCRETE", "project_config": {
            "file": str(FACTS.relative_to(ROOT)) if FACTS.is_relative_to(ROOT) else str(FACTS),
            "project_id": cfg.project_id, "config_version": cfg.config_version, "content_sha256": cfg.content_sha256},
        "rules_module": {"file": "engine/source/concrete_basis_rules_v1.py", "version": R.RULE_VERSION},
        "builders": {v: {"task": t, "file": p} for v, (t, p) in BUILDERS.items()},
        "counts": dict(sorted(counts.items())), "by_rule": dict(sorted(by_rule.items())),
        "valued_reproduced": {"lines": len(valued),
                              "patch_m3": round(sum(e["patch"]["value"] for e in valued), 6),
                              "rule_m3": round(sum(e["rule_result"]["value"] for e in valued), 6)},
        "fact_usage": {k: v for k, v in fact_usage(entries).items() if cfg.history(k)},
        "held_by_undeclared_fact": {k: v for k, v in fact_usage(entries).items() if not cfg.history(k)},
        "out_of_scope": [{"version": v, "line_id": l, "item_code": i, "why": "not a concrete line: its trade's round"}
                         for v, l, i in outside] + [
            {"version": "ARCH_TAKEOFF_V3.0.16", "why": "project identity + revision set: class B identity, T-450 "
                                                       "part 2"},
            {"version": "ARCH_TAKEOFF_V3.0.30", "why": "formwork faces beside the concrete members: a later round"}],
        "entries": entries,
    }


CSV_COLS = ("version", "task", "line_id", "item_code", "action", "class", "rule", "patch_value", "patch_state",
            "rule_state", "rule_value", "rule_low", "rule_high", "rule_minus_patch_m3", "facts_used", "residual",
            "not_reproduced")


def to_csv(reg):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_COLS)
    for e in reg["entries"]:
        p, rr = e["patch"] if isinstance(e["patch"], dict) else {"value": e["patch"]}, e.get("rule_result") or {}
        w.writerow([e["version"], e["task"], e["line_id"] or e.get("element_id") or "", e["item_code"], e["action"],
                    e["class"], e["rule"] or "", p.get("value", ""), p.get("state", ""), rr.get("state", ""),
                    rr.get("value", ""), rr.get("low", ""), rr.get("high", ""), e.get("rule_minus_patch_m3", ""),
                    ";".join(rr.get("facts_used", [])), e.get("residual", ""), e.get("not_reproduced", "")])
    return buf.getvalue()


if __name__ == "__main__":
    reg = build()
    if len(sys.argv) > 1:
        out = Path(sys.argv[1])
        out.mkdir(parents=True, exist_ok=True)
        (out / "CORRECTION_REGISTER_CONCRETE_T449.json").write_text(
            json.dumps(reg, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        (out / "CORRECTION_REGISTER_CONCRETE_T449.csv").write_text(to_csv(reg), encoding="utf-8")
    print(json.dumps({k: reg[k] for k in ("counts", "by_rule", "valued_reproduced")}, indent=1))
