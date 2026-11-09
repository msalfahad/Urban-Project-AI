"""T-662 development-villa build (research, unwired): REBAR BY OWNER-APPROVED RATIO (R-T662-1, t662_rules.py) on the
B11-01 STR.REBAR lines of the trial BOQ r4 (T-654: candidate ARCH_TAKEOFF_V3.0.61 + overlay WIRING MANIFEST V20).

Inputs (repository files only, pinned): the r4 per-line record (class, quantity, bounds after the overlay) and the
V3.0.61 line index (element ids). Member of a bar line = the engine's member key in its element id. Concrete binding by
recorded ids only (the T-639 bindings, re-read here on V3.0.61): column hand-ledger id -> formwork R4 row -> T-332 face
concrete line; beam -> its HL:BEAM_LEDGER concrete lines, else the T-110 beam member register component -> the
P-C / U-C beam band line of exactly that id; footing / neck / ground slab -> the concrete line of the same route id;
stair part -> HL:STAIR_CONCRETE of the same part; lift tie beam -> its T-419 concrete line. Anything else NOT_BOUND.

Rebuild (wrapper only): `URBAN_T662_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-662
tests/t662_rebar_ratio/test_t662.py::test_write_outputs`; check: `... pytest --tree task-T-662 tests/t662_rebar_ratio`.
Writes out/T662_REBAR_RATIO.json and .md. No coordinate (member labels drop the '@x,y' part; line ids keep the trace),
no drawing text, no client name."""
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
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t662_rules as R  # noqa: E402

D, S, q = R.D, R.S, R.q
SCHEMA = "URBAN_T662_REBAR_RATIO_V1"
TRIAL = "research/agents_t654/out/TRIAL_BOQ_R4_T654.json"
INDEX = "research/agents_t655/out/LINE_INDEX_V3_0_61.json"
R4 = "research/agents_t264/FORMWORK_LINES_R4.csv"
T332 = "research/agents_t332/FORMWORK_T332_BY_FACE.csv"
BREG = "research/agents_t110/BEAM_MEMBER_REGISTER.csv"
PINS = {TRIAL: "9e032726257c4961", INDEX: "10e5f116d30af67f", R4: "8681948753f37c81", T332: "15c188724a60d580",
        BREG: "368d0fa2d690fb02"}
LIFT_TIE_CONCRETE = "L-5ae06fda7d729d54c033"      # STR.CONC.LIFT LIFT_TIE_BEAM:GF (T-419), as T-639
OUT_JSON = HERE / "out" / "T662_REBAR_RATIO.json"
OUT_MD = HERE / "out" / "T662_REBAR_RATIO.md"


def sha16(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def check_pins():
    bad = {p: (sha16(p), v) for p, v in PINS.items() if sha16(p) != v}
    if bad:
        raise R.RuleError(f"input drift (sha256[:16] now, pinned): {bad}")


def _csv(p):
    with open(ROOT / p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _json(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def label(key):
    """Member label without coordinates (the '@x,y' part and route hashes dropped)."""
    return re.sub(r"@[\d,]+(\|\w+)?", "", key)


def load():
    check_pins()
    per = _json(TRIAL)["per_line"]
    idx = {x["line_id"]: x for x in _json(INDEX)["lines"]}
    for p in per:
        lid = p["line_id"]
        if lid in idx:
            p["element_id"] = idx[lid]["element_id"]
        elif lid.startswith("NEW:"):
            p["element_id"] = lid.split(":", 2)[2]
        else:
            raise R.RuleError(f"{lid}: in r4 but not in the V3.0.61 index and not an overlay line")
    r4 = _csv(R4)
    faces = {f["face_id"]: f for f in _csv(T332)}
    col = {}
    for i, row in enumerate(r4):
        m = re.match(r"(COL-\w+-\d+) ", row["item"])
        if m and row["element"] == "COLUMN" and f"R4-{i}" in faces:
            col.setdefault(m.group(1), faces[f"R4-{i}"]["line_id"])
    breg = {r["member_id"]: r["component"] for r in _csv(BREG)}
    return {"per": per, "col": col, "breg": breg}


# ---- member key and type ---------------------------------------------------------------------------------------------
def member_of(eid):
    p = eid.split(":")
    if eid.startswith("HL:SLAB_STEEL:"):
        return "SLAB:" + p[3], "SLAB"
    if eid.startswith("HL:BEAM_STEEL:"):
        return "BEAM:" + p[2], "BEAM"
    if eid.startswith("HL:COLUMN_STEEL:"):
        return "COLUMN:" + p[2], "COLUMN"
    if eid.startswith("HL:GROUND_SYSTEM_STEEL:"):
        return "GROUND_SYSTEM:" + p[2], "GROUND_BEAM"
    if eid.startswith("HL:STAIR_POOL_TANK_STEEL:"):
        t = "POOL_TANK_WALL" if p[2].startswith("POOL") else "STAIR"
        return f"{t}:{p[2]}:{p[3]}", t
    if eid.startswith("FRP:FTG:"):
        return "FOOTING:" + ":".join(p[2:5]), "FOOTING"
    if eid.startswith("P-S:NECK:"):
        return "NECK:" + ":".join(p[2:5]), "NECK"
    if eid.startswith("P-S:GROUND_SLAB:"):
        return "GROUND_SLAB:" + p[3], "GROUND_SLAB"
    if eid.startswith("LIFT_TIE_BEAM:"):
        return "BEAM:LIFT_TIE_BEAM:GF", "BEAM"
    return "OTHER:" + eid, "OTHER"


def concrete_of(key, typ, eid, data, conc):
    """(list of concrete per-line records, binding basis)."""
    p = eid.split(":")
    by_el = data["by_el"]
    if typ == "COLUMN":
        cl = data["col"].get(p[2])
        return ([data["P"][cl]] if cl else []), (f"{p[2]} -> formwork R4 row -> T-332 face concrete line" if cl else
                                                  "no formwork R4 / T-332 face concrete line for the column")
    if typ == "BEAM" and eid.startswith("LIFT_TIE_BEAM:"):
        return [data["P"][LIFT_TIE_CONCRETE]], "lift tie beam -> STR.CONC.LIFT LIFT_TIE_BEAM:GF (T-419)"
    if typ == "BEAM":
        bm = p[2]
        hl = [x for x in conc if x["item_code"] == "STR.CONC.BEAM" and x["element_id"].startswith("HL:BEAM_LEDGER:")
              and re.search(rf":{re.escape(bm)}(#|$)", x["element_id"])]
        if [x for x in hl if x["class"] != "EXCLUDED"]:
            return hl, f"{bm} -> HL:BEAM_LEDGER concrete line(s) of the member"
        c = data["breg"].get(bm)
        pc = [x for pre in ("P-C:", "U-C:") for x in by_el.get(pre + c, [])] if c else []
        if pc:
            return pc, f"{bm} -> T-110 register component {c} -> beam band line of that id"
        return hl, f"{bm}: no live HL:BEAM_LEDGER line and no register band line"
    if typ == "FOOTING":
        return by_el.get("P-C:FTG:" + ":".join(p[2:-1]), []), "footing route id -> P-C:FTG line of the same id"
    if typ == "NECK":
        return by_el.get("P-C:NECK:" + ":".join(p[2:5]), []), "neck route id -> P-C:NECK line of the same id"
    if typ == "GROUND_SLAB":
        sid = ":".join(p[2:4])
        return ([x for pre in ("P-C:", "U-C:", "GS-T442:") for x in by_el.get(pre + "GROUND_SLAB:" + sid, [])],
                "ground slab site id -> its GROUND_SLAB concrete line")
    if typ == "STAIR" and len(p) > 3:
        return by_el.get(f"HL:STAIR_CONCRETE:{p[2]}:{p[3]}", []), "stair part -> HL:STAIR_CONCRETE of the same part"
    why = {"SLAB": "slab panel steel has no per-panel concrete line (slab concrete lines are route G sites; the "
                   "T-639 binding is family-level only)",
           "GROUND_BEAM": "ground-system span ids carry no recorded concrete line id (T-639 binding gap)",
           "POOL_TANK_WALL": "pool bar row carries no recorded concrete line id",
           "OTHER": "element type not in the owner's ratio list (dome shell / ring, lintel bars)"}.get(typ, "none")
    return [], "NOT_BOUND: " + why


def build():
    data = load()
    P = {x["line_id"]: x for x in data["per"]}
    data["P"] = P
    conc = [x for x in data["per"] if x["item_code"].startswith("STR.CONC.")]
    by_el = collections.defaultdict(list)
    for x in conc:
        by_el[x["element_id"]].append(x)
    data["by_el"] = by_el
    bars = [x for x in data["per"] if x["family"] == "B11-01" and x["item_code"] == "STR.REBAR"]
    members = collections.OrderedDict()
    for x in sorted(bars, key=lambda z: z["line_id"]):
        key, typ = member_of(x["element_id"])
        members.setdefault(key, {"type": typ, "lines": [], "eid": x["element_id"]})["lines"].append(x)
    # ---- per member: state, concrete
    rows = {}
    for key, m in members.items():
        live = [x for x in m["lines"] if x["class"] != "EXCLUDED"]
        if not live:
            continue
        st = R.member_state(live)
        cl, basis = concrete_of(key, m["type"], m["eid"], data, conc)
        cs = R.concrete_state(cl)
        rows[key] = {"member": label(key), "type": m["type"], "state": st, "lines": [x["line_id"] for x in live],
                     "concrete_lines": [x["line_id"] for x in cl], "binding": basis, "concrete_state": cs[0],
                     "m3_low": S(cs[1]) if cs[1] is not None else None,
                     "m3_high": S(cs[2]) if cs[2] is not None else None, "_live": live, "_cs": cs}
        if st in ("FULL", "BOUNDED"):
            lo, hi = R.detailed_kg(live)
            rows[key]["detailed_kg"] = [S(lo), S(hi)]
        elif st == "PARTIAL":
            rel = sum((D(str(x["measured_net"])) for x in live if x["class"] == "RELEASED"), D(0))
            rows[key]["released_kg"] = S(rel)
    # ---- calibration per type
    cal = {}
    for t in R.TYPES + ("OTHER",):
        cal[t] = R.calibrate(R.calibration_set(rows.values(), t))
    # ---- route every member
    for r in rows.values():
        r.update(R.assign(r["state"], cal[r["type"]], r["_cs"]))
        if r["state"] == "PARTIAL" and cal[r["type"]] and r["concrete_state"] in ("RELEASED", "HELD_BOUNDED"):
            alt = R.ratio_kg(cal[r["type"]], r["_cs"])
            r["whole_member_ratio_NOT_APPLIED"] = [alt["kg_low"], alt["kg_high"]]
    # ---- no member both ways; every live line once
    seen = collections.Counter(lid for r in rows.values() for lid in r["lines"])
    if any(v != 1 for v in seen.values()):
        raise R.RuleError("a bar line sits in two members")
    for r in rows.values():
        if r["route"] == "RATIO" and any(x["class"] == "RELEASED" or x.get("held_low") is not None for x in r["_live"]):
            raise R.RuleError(f"{r['member']}: ratio on a member with detailed kg (both ways)")
    # ---- per HELD line ledger
    per_line = []
    for r in rows.values():
        for x in r["_live"]:
            if x["class"] != "HELD":
                continue
            per_line.append({"line_id": x["line_id"], "member": r["member"], "type": r["type"],
                             "member_state": r["state"], "route": r["route"],
                             "own_held": [S(x["held_low"]) if x["held_low"] is not None else None,
                                          S(x["held_high"]) if x["held_high"] is not None else None],
                             "concrete": {"lines": r["concrete_lines"], "state": r["concrete_state"],
                                          "m3": [r["m3_low"], r["m3_high"]]},
                             "member_ratio_kg": ([r["kg_low"], r["kg_high"]] if r["route"] == "RATIO" else None),
                             "cause": r.get("cause") or r["status"]})
    # ---- subtotals
    rel_lines = [x for x in bars if x["class"] == "RELEASED"]
    rel_kg = sum((D(str(x["measured_net"])) for x in rel_lines), D(0))
    rat = [r for r in rows.values() if r["route"] == "RATIO"]
    by_t = collections.defaultdict(lambda: {"members": 0, "lines": 0, "kg_low": D(0), "kg_high": D(0),
                                            "m3_low": D(0), "m3_high": D(0)})
    for r in rat:
        b = by_t[r["type"]]
        b["members"] += 1
        b["lines"] += len(r["lines"])
        b["kg_low"] += D(r["kg_low"])
        b["kg_high"] += D(r["kg_high"])
        b["m3_low"] += D(r["m3_low"])
        b["m3_high"] += D(r["m3_high"])
    routes = collections.Counter((r["type"], r["route"]) for r in rows.values())
    routes_lines = collections.Counter((r["type"], r["route"]) for r in rows.values() for _ in r["lines"])
    held_causes = collections.Counter((r["type"], r.get("cause") or r["status"]) for r in rows.values()
                                      if r["route"] in ("RATIO_HELD", "PARTIAL_HELD"))
    alt = collections.defaultdict(lambda: [0, D(0), D(0), D(0)])
    for r in rows.values():
        if r.get("whole_member_ratio_NOT_APPLIED"):
            a = alt[r["type"]]
            a[0] += 1
            a[1] += D(r["whole_member_ratio_NOT_APPLIED"][0])
            a[2] += D(r["whole_member_ratio_NOT_APPLIED"][1])
            a[3] += D(r["released_kg"])
    blank_groups = collections.defaultdict(collections.Counter)
    for r in rows.values():
        if r["state"] == "PARTIAL":
            for g in {re.sub(r"\d", "#", x["element_id"].split(":")[-1]) for x in r["_live"]
                      if x["class"] == "HELD" and (x["held_low"] is None or x["held_high"] is None)}:
                blank_groups[r["type"]][g] += 1
    findings = {
        "F-T662-1": {"what": "PARTIAL members (some detailed kg, some blank / open-high bar groups) take NO ratio: the "
                             "owner rule covers a member WITHOUT a detailed takeoff and says keep the detailed takeoff "
                             "already done; a whole-member ratio would be the second way on the same member. Shown, NOT "
                             "applied, for the Lead: the whole-member ratio of the PARTIAL members whose type is "
                             "calibrated and whose concrete is valued, beside their released detailed kg.",
                     "members_by_type": {t: n for t, n in collections.Counter(
                         r["type"] for r in rows.values() if r["state"] == "PARTIAL").items()},
                     "whole_member_ratio_not_applied": {t: {"members": a[0], "ratio_kg": [S(a[1]), S(a[2])],
                                                            "their_released_detailed_kg": S(a[3])}
                                                        for t, a in sorted(alt.items())},
                     "blank_or_open_groups_keeping_them_partial": {t: dict(c.most_common(6))
                                                                   for t, c in sorted(blank_groups.items())}},
        "F-T662-2": {"what": "types with no calibration member on this villa: no member of the type has a complete "
                             "(FULL or BOUNDED) count on RELEASED concrete, so the type has no ratio and its NONE members "
                             "stay HELD (no borrowed ratio)",
                     "types": [t for t in R.TYPES if cal[t] is None]},
        "F-T662-3": {"what": "weak calibration: a type whose ratio rests on fewer than 3 members (shown, not refused; "
                             "Checker review before wiring)",
                     "types": {t: c["n"] for t, c in cal.items() if c is not None and c["n"] < 3}},
        "F-T662-4": {"what": "binding gaps: bar members with no recorded concrete line id (slab panels: per-panel "
                             "concrete not in the candidate; ground-system spans; pool rows; dome / lintel rows)",
                     "members_by_type": {t: n for t, n in collections.Counter(
                         r["type"] for r in rows.values() if r["concrete_state"] == "NOT_BOUND").items()}},
    }
    out_rows = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows.values()]
    held_n = sum(1 for x in bars if x["class"] == "HELD")
    if len(per_line) != held_n:
        raise R.RuleError(f"held lines in the ledger {len(per_line)} != r4 HELD {held_n}")
    return {
        "schema": SCHEMA, "rule": R.RULE, "task": "T-662",
        "candidate": "ARCH_TAKEOFF_V3.0.61 + WIRING MANIFEST V20 (trial BOQ r4, T-654)",
        "released": "NOTHING RELEASED; research table, unwired; no candidate, engine, rule / knowledge version or "
                    "registry file changed; the ratio rows are proposals for a later Gate B row",
        "label": R.LABEL, "pins": PINS,
        "counts": {"bar_lines": len(bars), "released_lines": len(rel_lines), "held_lines": held_n,
                   "excluded_lines": sum(1 for x in bars if x["class"] == "EXCLUDED"), "members": len(rows),
                   "members_by_type_route": {f"{t}|{k}": v for (t, k), v in sorted(routes.items())},
                   "lines_by_type_route": {f"{t}|{k}": v for (t, k), v in sorted(routes_lines.items())}},
        "calibration": {t: c for t, c in cal.items()},
        "subtotals": {
            "released_detailed_kg": S(rel_kg), "released_detailed_t": S(rel_kg / 1000),
            "ratio_by_type": {t: {"members": b["members"], "lines": b["lines"], "m3": [S(b["m3_low"]), S(b["m3_high"])],
                                  "kg": [S(b["kg_low"]), S(b["kg_high"])]} for t, b in sorted(by_t.items())},
            "ratio_total_kg": [S(sum((b["kg_low"] for b in by_t.values()), D(0))),
                               S(sum((b["kg_high"] for b in by_t.values()), D(0)))],
            "note": "detailed (released) and ratio (ESTIMATE) subtotals are separate and never summed into one figure "
                    "here; the members routed to RATIO carry no detailed kg (asserted)"},
        "held_causes": {f"{t}|{c}": v for (t, c), v in sorted(held_causes.items())},
        "findings": findings,
        "reference_range_check": "NOT DONE: no page of a Drive engineering reference book printing kg/m3 ranges was "
                                 "located in this run (the ACI / IBC books found are over the connector's size limit); "
                                 "no range is invented; open for the Lead / Checker",
        "members": out_rows, "per_held_line": per_line,
    }


def md(o):
    L = [f"# T-662 rebar by owner-approved ratio (R-T662-1; generated)", "",
         f"Candidate {o['candidate']}. {o['released']}. Label of every ratio quantity: {o['label']}.", "",
         "## 1. Calibration per element type (counted kg / their concrete m3; FULL or BOUNDED members on RELEASED "
         "concrete)", "", "| type | n | m3 | kg low .. high | kg/m3 low .. high | member spread (low) | outliers |",
         "|---|---|---|---|---|---|---|"]
    for t, c in o["calibration"].items():
        if c is None:
            L.append(f"| {t} | 0 | - | - | NO RATIO (no counted member) | - | - |")
        else:
            L.append(f"| {t} | {c['n']} | {c['m3']} | {c['kg_low']} .. {c['kg_high']} | {c['ratio_low']} .. "
                     f"{c['ratio_high']} | {c['spread_low'][0]} .. {c['spread_low'][1]} | "
                     f"{', '.join(c['outliers']) or 'none'} |")
    L += ["", "Calibration members:", ""]
    for t, c in o["calibration"].items():
        if c:
            for m in c["members"]:
                L.append(f"- {t} {m['member']}: {m['m3']} m3, {m['kg_low']} .. {m['kg_high']} kg = {m['ratio_low']} .. "
                         f"{m['ratio_high']} kg/m3{' OUTLIER' if m['outlier'] else ''}")
    s = o["subtotals"]
    L += ["", "## 2. Subtotals (never summed together)", "",
          f"- Released detailed: {s['released_detailed_kg']} kg ({s['released_detailed_t']} t).",
          f"- Ratio ESTIMATE total: {s['ratio_total_kg'][0]} .. {s['ratio_total_kg'][1]} kg.", "",
          "| type | members | bar lines | m3 | ratio kg low .. high |", "|---|---|---|---|---|"]
    for t, b in s["ratio_by_type"].items():
        L.append(f"| {t} | {b['members']} | {b['lines']} | {b['m3'][0]} .. {b['m3'][1]} | {b['kg'][0]} .. {b['kg'][1]} |")
    L += ["", "## 3. Members by type and route", "", "| type / route | members | bar lines |", "|---|---|---|"]
    for k, v in o["counts"]["members_by_type_route"].items():
        L.append(f"| {k} | {v} | {o['counts']['lines_by_type_route'][k]} |")
    L += ["", "## 4. Why the rest stays HELD (members)", ""]
    for k, v in o["held_causes"].items():
        L.append(f"- {k}: {v}")
    L += ["", "## 5. Ratio members", "", "| member | type | concrete | m3 | kg low .. high |", "|---|---|---|---|---|"]
    for r in o["members"]:
        if r["route"] == "RATIO":
            L.append(f"| {r['member']} | {r['type']} | {r['concrete_state']} {', '.join(r['concrete_lines'])} | "
                     f"{r['m3_low']} .. {r['m3_high']} | {r['kg_low']} .. {r['kg_high']} |")
    L += ["", "## 6. Findings for the Lead / Checker (nothing applied)", ""]
    for k, f in o["findings"].items():
        L.append(f"- {k}: {f['what']}.")
        for kk, vv in f.items():
            if kk != "what":
                L.append(f"  - {kk}: {json.dumps(vv, ensure_ascii=False)}")
    L += ["", f"Reference range check: {o['reference_range_check']}.", ""]
    return "\n".join(L) + "\n"


def write():
    o = build()
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps(o, indent=1, ensure_ascii=False, sort_keys=False) + "\n", encoding="utf-8")
    OUT_MD.write_text(md(o), encoding="utf-8")
    return o
