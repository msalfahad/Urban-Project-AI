"""T-663 development-villa build (research, unwired): the four Checker wiring conditions on the T-662 ratio table
(R-T663-1 .. 4, t663_rules.py), on the same inputs T-662 pinned (trial BOQ r4 = ARCH_TAKEOFF_V3.0.61 + WIRING MANIFEST
V20), plus four committed registers, pinned:
  - research/agents_t366/ALSENAN_LAP_AUTHORITY_INPUT.json  splice need per bar population (T-366, MERGED)
  - research/agents_t149/T149_BEAMS.csv                     beam steel ledger rows: simple / continuous per row id
  - research/urban_engine_m2_generalization/05_REINFORCEMENT_COMPLETENESS_89.csv  ground-beam span -> generic band id
    (face-handle match, with the span's own M1 concrete m3: the second measure of R-T663-4 (d))
  - research/agents_t151/t151_ledgers.py D4_CLOSED          the footings whose top ends are drawn closed (T-155 r2)

Rebuild (wrapper only): `URBAN_T663_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-663
tests/t663_rebar_ratio_wiring/test_t663.py::test_write_outputs`; check: `... pytest --tree task-T-663
tests/t663_rebar_ratio_wiring`. Writes out/T663_RATIO_WIRING.json and .md. No coordinates, no drawing text beyond the
notation needed to name a gap, no client name."""
from __future__ import annotations

import collections
import csv
import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT / "research" / "agents_t662", ROOT / "research" / "agents_t151"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import t663_rules as R  # noqa: E402
import t662_rules as R2  # noqa: E402
import t662_alsenan as A2  # noqa: E402

D, S = Decimal, R.S
SCHEMA = "URBAN_T663_RATIO_WIRING_V1"
T366 = "research/agents_t366/ALSENAN_LAP_AUTHORITY_INPUT.json"
T149 = "research/agents_t149/T149_BEAMS.csv"
M2MAP = "research/urban_engine_m2_generalization/05_REINFORCEMENT_COMPLETENESS_89.csv"
T151 = "research/agents_t151/t151_ledgers.py"
T662OUT = "research/agents_t662/out/T662_REBAR_RATIO.json"
PINS = {T366: "5231307b3a9f611e", T149: "31740b20a42813fc", M2MAP: "7889dd08a8016b10", T662OUT: "ac44f8a568887b85"}
OUT_JSON = HERE / "out" / "T663_RATIO_WIRING.json"
OUT_MD = HERE / "out" / "T663_RATIO_WIRING.md"

# ---- (1) the reference books searched this run (Drive, read-only). No printed kg/m3 range was found: none is cited. ----
REFERENCES = []          # admissible {type, book, folder, page, low, high}: none located
SOURCES_SEARCHED = [
    {"folder": "Engineering Sources - Urban Projects / 01 Kuwait References",
     "title": "Kuwait Society of Engineers home-building guide 2023 (Arabic, 2.6 MB)",
     "result": "read in full through the connector: contract templates and MEP clauses; no reinforcement kg/m3 table"},
    {"folder": "Engineering Sources - Urban Projects / 02 Construction Books",
     "title": "reinforced-concrete design summary to the 2020 code (Arabic, 5.2 MB)",
     "result": "connector text is glyph-encoded (unreadable): SOURCE NOT READ"},
    {"folder": "Engineering Sources - Urban Projects / 02 Construction Books",
     "title": "code summary, site-supervision, finishes, construction-mistakes and project-management books",
     "result": "over the connector size limit (7.6 .. 82 MB): SOURCE NOT READ"},
    {"folder": "Engineering Sources - Urban Projects / 03 International Codes",
     "title": "ACI 318-2025, ACI 318-2014 Arabic, IBC 2009 / 2018 / 2021, IPC 2006",
     "result": "over the connector size limit (9.7 .. 45 MB): SOURCE NOT READ; design codes print minimum / maximum "
               "reinforcement percentages, not estimating kg/m3 per element type"},
    {"folder": "Engineering Sources - Urban Projects / 04 Regional Codes",
     "title": "QCS 2014, Dubai Building Code, Saudi codes, Egyptian code update",
     "result": "over the connector size limit or not a quantity reference: SOURCE NOT READ"},
    {"folder": "Urban Projects - Kuwait Engineering References (1rr88a1t...)",
     "title": "folder listing", "result": "no file listed under this folder id by the connector"},
    {"folder": "Drive full-text search", "title": "'kg/m3' + 'reinforcement'; 'كجم/م3'; 'steel per cubic meter'",
     "result": "hits only in code books (units of other quantities) and project notes; no estimating ratio table"},
]

# ---- (2) the footing top end legs: what the structural set prints (read this run from the structural PDF) ----------------
FOOTING_LEG_READING = {
    "printed": {},       # no leg length printed for any of F12 / F13 / F14 / FF
    "evidence": [
        "ST p.9 footing schedule: F12, F13, F14 and FF carry a closed cage symbol in REMARKS and TOP / BOT rows "
        "(n ø14/m TOP, n ø14 or ø16/m BOT); no leg length, no bar-shape code",
        "ST p.13 typical isolated footing (both variants): 'Boxed bars' drawn as an inverted U whose legs run down to the "
        "bottom mesh; no leg dimension",
        "ST p.14 lift footing (FF): closed cage, depth 'AS PER SCHEDULE' (H 55 cm on p.9); no leg dimension, no cover",
        "ST p.8 note 22: cover NOT LESS THAN 7 cm against soil (a minimum: a leg <= H - 2 x 7 cm is an upper bound only; "
        "no lower bound is printed)"],
    "decision": "R-T663-3: TOP_END_LEGS stay HELD blank by name; the four footings stay PARTIAL (no ratio, no "
                "calibration); FOOTING calibration stays n = 1 (F8, WEAK)",
}


def sha16(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def check_pins():
    bad = {p: (sha16(p), v) for p, v in PINS.items() if sha16(p) != v}
    if bad:
        raise R.RuleError(f"input drift (sha256[:16] now, pinned): {bad}")


def _csv(p):
    with open(ROOT / p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def group_of(eid):
    return eid.split(":")[-1].split("#")[0]


def splice_need_of(typ, key, eid, t149_kind, pops):
    """The splice need of the bar population governing the member's end groups."""
    if typ == "BEAM":
        m = re.search(r":(R\d+):", eid)
        kind = t149_kind.get(m.group(1)) if m else None
        return pops["BEAM-SIMPLE-MAIN"] if kind == "simple" else pops["CB-BOTTOM"] if kind == "continuous" else None
    if typ == "FOOTING":
        return pops["FTG-BOTTOM"]
    if typ == "GROUND_SLAB":
        return pops["GROUND-SLAB-MESH"]
    return None


def build():
    check_pins()
    base = A2.build()                               # T-662's own build (its pins are checked inside)
    committed = json.loads((ROOT / T662OUT).read_text(encoding="utf-8"))
    if base["subtotals"] != committed["subtotals"] or base["calibration"] != committed["calibration"]:
        raise R.RuleError("T-662 rebuild differs from its committed output")
    data = A2.load()
    per = {x["line_id"]: x for x in data["per"]}
    pops = {p["id"]: p["splice_need"] for p in json.loads((ROOT / T366).read_text(encoding="utf-8"))["populations"]}
    t149_kind = {r["row_id"]: r["kind"] for r in _csv(T149)}
    members = base["members"]

    # ---- (3) lap audit of every calibration member
    cal_members = {t: {m["member"] for m in c["members"]} for t, c in base["calibration"].items() if c}
    audits = []
    for r in members:
        if r["member"] not in cal_members.get(r["type"], ()):
            continue
        groups = []
        need = None
        for lid in r["lines"]:
            x = per[lid]
            eid = x["element_id"]
            need = need or splice_need_of(r["type"], r["member"], eid, t149_kind, pops)
            lo = x["measured_net"] if x["class"] == "RELEASED" else x["held_low"]
            hi = x["measured_net"] if x["class"] == "RELEASED" else x["held_high"]
            groups.append((group_of(eid), lo, hi))
        a = R.lap_audit(groups, need)
        audits.append({"member": r["member"], "type": r["type"], **a})
    by_type = collections.defaultdict(lambda: {"n": 0, "lap": [D(0), D(0)], "anch": [D(0), D(0)], "pass": 0})
    for a in audits:
        b = by_type[a["type"]]
        b["n"] += 1
        b["pass"] += a["passes"]
        for k, f in (("lap", "lap_kg"), ("anch", "anchorage_kg")):
            b[k][0] += D(a[f][0])
            b[k][1] += D(a[f][1])
    lap_summary = {t: {"members": b["n"], "passing": b["pass"], "lap_kg": [S(b["lap"][0]), S(b["lap"][1])],
                       "anchorage_kg_kept": [S(b["anch"][0]), S(b["anch"][1])], "laps_ok": b["pass"] == b["n"]}
                   for t, b in sorted(by_type.items())}
    # sensitivity (shown, NOT applied): BEAM ratio without the anchorage groups
    bc = base["calibration"]["BEAM"]
    an = lap_summary["BEAM"]["anchorage_kg_kept"]
    sens = {"what": "BEAM ratio if the end-anchorage groups were left out (NOT applied: anchorage of a simple-beam bar "
                    "is installed bar inside the support, not a lap)",
            "ratio": [S((D(bc["kg_low"]) - D(an[0])) / D(bc["m3"])), S((D(bc["kg_high"]) - D(an[1])) / D(bc["m3"]))]}
    # ground slab: the mesh kg is the bare mesh (no lap): 2 directions x 5 bars / m x d10 kg/m / thickness
    gs = base["calibration"]["GROUND_SLAB"]
    gs_proof = {"ratio_low": gs["ratio_low"], "bare_mesh_kg_per_m3_at_0_10_m": S(D(2) * 5 * D(100) / 162 / D("0.10")),
                "note": "ratio = 2 x 5 bars/m x 0.617284 kg/m (d10) / 0.10 m slab: the bare mesh, no lap kg inside"}

    # ---- (2) footing PARTIAL members
    ftg = []
    for r in members:
        if r["type"] == "FOOTING" and r["state"] == "PARTIAL":
            blank = sorted({group_of(per[l]["element_id"]) for l in r["lines"]
                            if per[l]["class"] == "HELD" and (per[l]["held_low"] is None or per[l]["held_high"] is None)})
            st, miss = R.partial_resolution(blank, FOOTING_LEG_READING["printed"])
            mark = r["member"].split(":")[2]
            ftg.append({"member": r["member"], "mark": mark, "blank_groups": blank, "state_after": st,
                        "held_by_name": miss, "m3": r["m3_low"],
                        "whole_member_ratio_NOT_APPLIED": r.get("whole_member_ratio_NOT_APPLIED")})

    # ---- (4) binding of the NOT_BOUND members
    reg = collections.defaultdict(list)
    owners = collections.defaultdict(set)
    for row in _csv(M2MAP):
        if row["GENERIC_COMPONENT_ID"]:
            owners[row["GENERIC_COMPONENT_ID"]].add("GROUND_SYSTEM:" + row["M1_COMPONENT_ID"]
                                                   if row["FAMILY"] == "GROUND_BEAMS" else row["M1_COMPONENT_ID"])
        if row["FAMILY"] == "GROUND_BEAMS":
            reg["GROUND_SYSTEM:" + row["M1_COMPONENT_ID"]].append(
                {"component": row["GENERIC_COMPONENT_ID"], "m3": row["M1_CONCRETE_M3_BASE"] or None})
    conc_by_id = collections.defaultdict(list)
    for x in data["per"]:
        if x["item_code"].startswith("STR.CONC.") and x["class"] != "EXCLUDED":
            conc_by_id[x["element_id"]].append(x)
    stair_ids = collections.defaultdict(list)
    for eid, xs in conc_by_id.items():
        if eid.startswith("HL:STAIR_CONCRETE:"):
            stair_ids[eid.split(":", 2)[2].replace("_", "-")] += xs
    bindings = []
    for r in members:
        if r["concrete_state"] != "NOT_BOUND":
            continue
        rec = {"member": r["member"], "type": r["type"], "state": r["state"], "route_T662": r["route"]}
        if r["type"] == "GROUND_BEAM":
            rec.update(R.bind(r["member"], reg.get(r["member"], []), conc_by_id, owners))
        elif r["type"] == "STAIR":
            part = ":".join(r["member"].split(":")[1:3])
            xs = stair_ids.get(part, [])
            if len(xs) == 1:
                rec.update({"bound": True, "concrete_id": "HL:STAIR_CONCRETE:" + xs[0]["element_id"].split(":", 2)[2],
                            "line_id": xs[0]["line_id"], "grade": "ID_ONLY",
                            "reason": "(a)-(c) the same stair part id in both hand ledgers (separator '-' / '_' "
                                      "normalised), one live line; (d) no second m3 measure for the steel row: "
                                      "binding by id only"})
            else:
                rec.update({"bound": False, "reason": f"(b) {len(xs)} HL:STAIR_CONCRETE lines for part {part} "
                                                      "(composite or absent concrete part)"})
        else:
            rec.update({"bound": False, "reason": {
                "SLAB": "(a) no committed register maps a slab steel panel (T-139 panel id) to a route G slab site line",
                "BEAM": "(a) T-110 register / HL:BEAM_LEDGER give no live line; the M2 beam register uses other ids",
                "POOL_TANK_WALL": "(a) pool bar rows R1 / R2 each mix wall and floor bars; the pool concrete is split "
                                  "WALLS / BASE: no one-to-one id",
                "OTHER": "type outside the owner's ratio list (dome shell / ring, lintel bars)"}.get(
                    r["type"], "(a) no register")})
        if rec.get("bound"):
            x = per[rec["line_id"]]
            cs = R2.concrete_state([x])
            rec.update({"concrete_state": cs[0], "m3": [S(cs[1]) if cs[1] is not None else None,
                                                        S(cs[2]) if cs[2] is not None else None]})
            cal = base["calibration"].get(r["type"])
            rec["ratio_after_binding"] = (R2.assign(r["state"], cal, cs)["route"])
        bindings.append(rec)
    bind_sum = collections.Counter((b["type"], "BOUND" if b.get("bound") else "NOT_BOUND") for b in bindings)
    new_ratio = [b for b in bindings if b.get("ratio_after_binding") == "RATIO"]
    if new_ratio:
        raise R.RuleError(f"binding created ratio members on an uncalibrated type: {[b['member'] for b in new_ratio]}")

    # ---- (1) range check per calibrated type
    rng = {t: R.range_check(t, c["ratio_low"], c["ratio_high"], REFERENCES, [s["title"] for s in SOURCES_SEARCHED])
           for t, c in base["calibration"].items() if c}

    # ---- Gate-B-ready ratio table
    table = []
    for r in members:
        if r["route"] != "RATIO":
            continue
        R.wiring_route_guard(r["route"], r["member"])
        cal = base["calibration"][r["type"]]
        g = R.gate(rng[r["type"]]["status"], cal["n"], lap_summary[r["type"]]["laps_ok"])
        table.append({"member": r["member"], "type": r["type"], "concrete_lines": r["concrete_lines"],
                      "concrete_state": r["concrete_state"], "m3": [r["m3_low"], r["m3_high"]],
                      "ratio_kg_per_m3": [cal["ratio_low"], cal["ratio_high"]], "kg_estimate": [r["kg_low"], r["kg_high"]],
                      "includes": "+3 .. 5 % laps and offcuts (low x 1.03, high x 1.05)", "label": R.LABEL,
                      "bar_lines_replaced": r["lines"], **g})
    tot = collections.defaultdict(lambda: [0, D(0), D(0)])
    for t in table:
        b = tot[t["type"]]
        b[0] += 1
        b[1] += D(t["kg_estimate"][0])
        b[2] += D(t["kg_estimate"][1])
    if [S(sum((b[1] for b in tot.values()), D(0))), S(sum((b[2] for b in tot.values()), D(0)))] != \
            base["subtotals"]["ratio_total_kg"]:
        raise R.RuleError("ratio table total differs from T-662")
    ready = sum(1 for t in table if t["wiring_ready"])
    return {
        "schema": SCHEMA, "rules": list(R.RULES), "task": "T-663", "candidate": base["candidate"],
        "released": "NOTHING RELEASED; research, unwired; no candidate / engine / rule-version / knowledge / registry "
                    "file changed; R-T662-1 used as it is",
        "pins": PINS,
        "condition_1_range_check": {"by_type": rng, "sources_searched": SOURCES_SEARCHED,
                                    "finding": "no Drive engineering book that the connector can read prints a kg/m3 "
                                               "range per element type; owner question Q-81 alternative B (cited book "
                                               "ranges) has no source today"},
        "condition_2_footing_partial": {"reading": FOOTING_LEG_READING, "members": ftg,
                                        "footing_calibration_n": base["calibration"]["FOOTING"]["n"]},
        "condition_3_laps": {"by_type": lap_summary, "members": audits, "beam_sensitivity_not_applied": sens,
                             "ground_slab_proof": gs_proof,
                             "populations": {k: pops[k] for k in ("BEAM-SIMPLE-MAIN", "CB-BOTTOM", "FTG-BOTTOM",
                                                                  "FTG-TOP", "GROUND-SLAB-MESH")}},
        "condition_4_binding": {"summary": {f"{t}|{k}": v for (t, k), v in sorted(bind_sum.items())},
                                "members": bindings},
        "gate_b_ratio_table": {"rows": table, "rows_n": len(table), "wiring_ready_n": ready,
                               "by_type": {t: {"members": b[0], "kg": [S(b[1]), S(b[2])]} for t, b in sorted(tot.items())},
                               "total_kg": base["subtotals"]["ratio_total_kg"],
                               "released_detailed_kg_unchanged": base["subtotals"]["released_detailed_kg"]},
    }


def md(o):
    c1, c2, c3, c4, t = (o["condition_1_range_check"], o["condition_2_footing_partial"], o["condition_3_laps"],
                         o["condition_4_binding"], o["gate_b_ratio_table"])
    L = ["# T-663 rebar ratio: the four wiring conditions (R-T663-1 .. 4; generated)", "",
         f"Candidate {o['candidate']}. {o['released']}.", "",
         "## (1) Range check (R-T663-1)", "", "| type | calibrated kg/m3 | status |", "|---|---|---|"]
    for k, v in c1["by_type"].items():
        L.append(f"| {k} | {v['ratio'][0]} .. {v['ratio'][1]} | {v['status']} |")
    L += ["", f"Finding: {c1['finding']}.", "", "Sources searched:", ""]
    L += [f"- {s['folder']}: {s['title']}: {s['result']}" for s in c1["sources_searched"]]
    L += ["", "## (2) Footing PARTIAL members (R-T663-3)", ""]
    L += [f"- {e}" for e in c2["reading"]["evidence"]]
    L += ["", f"Decision: {c2['reading']['decision']}.", "", "| member | blank groups | state | m3 | whole-member ratio (NOT applied) |",
          "|---|---|---|---|---|"]
    for m in c2["members"]:
        L.append(f"| {m['member']} | {', '.join(m['blank_groups'])} | {m['state_after']} | {m['m3']} | "
                 f"{' .. '.join(m['whole_member_ratio_NOT_APPLIED'] or ['-'])} |")
    L += ["", "## (3) Laps in the calibration kg (R-T663-2)", "",
          "| type | members | passing | lap kg | end anchorage kg kept |", "|---|---|---|---|---|"]
    for k, v in c3["by_type"].items():
        L.append(f"| {k} | {v['members']} | {v['passing']} | {v['lap_kg'][0]} .. {v['lap_kg'][1]} | "
                 f"{v['anchorage_kg_kept'][0]} .. {v['anchorage_kg_kept'][1]} |")
    L += ["", f"Splice need (T-366): {json.dumps(c3['populations'])}.",
          f"BEAM sensitivity (shown, not applied): {c3['beam_sensitivity_not_applied']['ratio'][0]} .. "
          f"{c3['beam_sensitivity_not_applied']['ratio'][1]} kg/m3 without the end anchorage.",
          f"Ground slab: {c3['ground_slab_proof']['note']} ({c3['ground_slab_proof']['bare_mesh_kg_per_m3_at_0_10_m']}).", "",
          "## (4) Binding of the NOT_BOUND members (R-T663-4)", "", "| type / result | members |", "|---|---|"]
    for k, v in c4["summary"].items():
        L.append(f"| {k} | {v} |")
    L += ["", "| member | state | bound | concrete | reason |", "|---|---|---|---|---|"]
    for b in c4["members"]:
        L.append(f"| {b['member']} | {b['state']} | {'yes' if b.get('bound') else 'no'} | "
                 f"{b.get('concrete_id', '-')} {b.get('m3', '')} | {b['reason']} |")
    L += ["", "## Gate-B ratio table for T-664", "",
          f"{t['rows_n']} rows, wiring-ready {t['wiring_ready_n']}; total {t['total_kg'][0]} .. {t['total_kg'][1]} kg "
          f"ESTIMATE (released detailed {t['released_detailed_kg_unchanged']} kg unchanged, kept apart).", "",
          "| member | type | concrete | m3 | kg/m3 | kg ESTIMATE | ready | blockers |", "|---|---|---|---|---|---|---|---|"]
    for r in t["rows"]:
        L.append(f"| {r['member']} | {r['type']} | {r['concrete_state']} {', '.join(r['concrete_lines'])} | "
                 f"{r['m3'][0]} .. {r['m3'][1]} | {r['ratio_kg_per_m3'][0]} .. {r['ratio_kg_per_m3'][1]} | "
                 f"{r['kg_estimate'][0]} .. {r['kg_estimate'][1]} | {'yes' if r['wiring_ready'] else 'no'} | "
                 f"{'; '.join(r['blockers'])} |")
    return "\n".join(L) + "\n"


def write():
    o = build()
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps(o, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT_MD.write_text(md(o), encoding="utf-8")
    return o
