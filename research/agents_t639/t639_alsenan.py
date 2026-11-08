"""T-639 development-villa build (research, unwired): the B11-01 STR.REBAR lines of the 10 Nov trial BOQ dry run (T-630:
candidate ARCH_TAKEOFF_V3.0.58 = V3.0.57 line index + 5 roof WP lines, overlay V15) that are HELD BLANK (801) or HELD
with an OPEN high end (6), classed one by one under R-T639-1 (t639_rules.py): A concrete HELD, B input not given,
C owner-gated, D computable now (fix rows FR-T639-n in kg, display t).

Cause provenance per line (the latest record that states it, never re-typed):
  1. the T-449 round-2 register entry of the line where the candidate re-based it at ARCH_TAKEOFF_V3.0.27 (slab bar ends,
     T-318): rule_result.held_reason;
  2. an APPLIED Checker downgrade record of the V3.0.57 line index (DOWNGRADES_SNAPSHOT, status from the index);
  3. the line's own candidate record (reasons) as extracted by T-297 from the candidate BOQ lines (V3.0.16);
     the V3.0.45 .. V3.0.57 line indexes show every such line HELD blank unchanged (asserted on V3.0.57 here);
  4. overlay lines (NEW:...): their wiring-manifest row (V11 for the dome / lift rows, V3 for the lintel rows),
     values asserted equal to the T-630 per-line record.
Concrete binding per line: column hand-ledger id -> its formwork R4 row -> the T-332 face's concrete line; beam ledger
id -> HL:BEAM_LEDGER concrete lines of the member; footing / neck route ids -> the P-C line of the same id; the lift tie
beam and overlay lines -> the concrete line their record names; else a concrete line id the T-297 basis row names;
else NOT_BOUND (classed by its own hold text, the binding gap stated).

Rebuild (wrapper only): `URBAN_T639_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-639 tests/t639/test_t639.py::
test_write_outputs`; check: `bash scripts/agent_env.sh pytest --tree task-T-639 tests/t639`.
Writes out/REBAR_HOLD_CENSUS_T639.json and .md. No coordinate, no drawing text beyond the recorded hold reasons, no
client name."""
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
import t639_rules as R  # noqa: E402

D, S, q = R.D, R.S, R.q
SCHEMA, RULE = "URBAN_T639_REBAR_HOLD_CENSUS_V1", "R-T639-1"
T630 = "research/agents_t630/out/E2E_BOQ_DRY_RUN_T630.json"
INDEX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
V16 = "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json"
T449 = "research/agents_t449/round2/out/CORRECTION_REGISTER_REBAR_T449.json"
DGS = "research/agents_t469/DOWNGRADES_SNAPSHOT.json"
T297 = "research/agents_t297/LINE_BASIS_T297.csv"
T119 = "research/agents_t119/COLUMNS_TO_CONTROLLING_MEMBER.csv"
R4 = "research/agents_t264/FORMWORK_LINES_R4.csv"
T332 = "research/agents_t332/FORMWORK_T332_BY_FACE.csv"
MV11 = "research/agents_t596/out/WIRING_MANIFEST_V11.json"
MV3 = "research/agents_t538/WIRING_MANIFEST_V3.json"
PINS = {T630: "e5dde7867c8fe6ad", INDEX: "fed5141ea31bfdd9", V16: "2f28367b81fe362d", T449: "179fe80a1cd4463e",
        DGS: "817326399e5b9fff", T297: "fc36ca1973452863", T119: "dbe1ce155c7d7356", R4: "8681948753f37c81",
        T332: "15c188724a60d580", MV11: "d909fa02db13e3fd", MV3: "8d524c53e952ba91"}
OUT_JSON = HERE / "out" / "REBAR_HOLD_CENSUS_T639.json"
OUT_MD = HERE / "out" / "REBAR_HOLD_CENSUS_T639.md"
LIFT_TIE_CONCRETE = "L-5ae06fda7d729d54c033"      # STR.CONC.LIFT LIFT_TIE_BEAM:GF (T-419 ADD_HELD)
EXPECT = {"blank": 801, "open_high": 6}


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


def _manifest_rows(m):
    out = {}

    def walk(o):
        if isinstance(o, dict):
            if str(o.get("line_id", "")).startswith("NEW:STR.REBAR") and "after" in o:
                out[o["line_id"]] = o
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(m)
    return out


def load():
    check_pins()
    idx = _json(INDEX)
    reg = collections.defaultdict(list)
    for e in _json(T449)["entries"]:
        if e.get("line_id"):
            reg[e["line_id"]].append(e)
    status = {x["downgrade_id"]: x["status"] for x in idx["downgrades"]}
    dg = collections.defaultdict(list)
    for r in _json(DGS)["downgrades"]:
        if status.get(r["downgrade_id"]) == "APPLIED":
            for lid in r["line_ids"]:
                dg[lid].append(r)
    r4 = _csv(R4)
    faces = {f["face_id"]: f for f in _csv(T332)}
    col_concrete = {}
    for i, row in enumerate(r4):
        m = re.match(r"(COL-\w+-\d+) ", row["item"])
        if m and row["element"] == "COLUMN" and f"R4-{i}" in faces:
            col_concrete.setdefault(m.group(1), faces[f"R4-{i}"]["line_id"])
    nrows = dict(_manifest_rows(_json(MV3)))
    nrows.update(_manifest_rows(_json(MV11)))
    return {"t630": _json(T630), "lines": {x["line_id"]: x for x in idx["lines"]},
            "v16": {x["line_id"]: x for x in _json(V16)["lines"]}, "reg": reg, "dg": dg,
            "basis": {r["line_id"]: r for r in _csv(T297)}, "t119": {r["id"]: r for r in _csv(T119)},
            "col_concrete": col_concrete, "new": nrows}


# ---- targets --------------------------------------------------------------------------------------------------------
def targets(data):
    pl = [x for x in data["t630"]["per_line"] if x["family"] == "B11-01" and x["item_code"] == "STR.REBAR"]
    blank = [x for x in pl if x["class"] == "HELD" and x["held_low"] is None and x["held_high"] is None]
    open_hi = [x for x in pl if x["class"] == "HELD" and x["held_low"] is not None and x["held_high"] is None]
    if len(blank) != EXPECT["blank"] or len(open_hi) != EXPECT["open_high"]:
        raise R.RuleError(f"target counts {len(blank)} / {len(open_hi)} differ from the T-630 801 / 6")
    rel = [x for x in pl if x["class"] == "RELEASED"]
    return blank, open_hi, rel


# ---- concrete binding -----------------------------------------------------------------------------------------------
def concrete_of(eid, lid, data):
    """(concrete line id or None, binding basis)."""
    L = data["lines"]
    p = eid.split(":")
    if eid.startswith("HL:COLUMN_STEEL:"):
        cl = data["col_concrete"].get(p[2])
        if cl:
            ce, t = L[cl]["element_id"], data["t119"][p[2]]
            m = re.match(r".*:(C\w*)@[\d,]+\|(GF|1F|2F)$", ce)
            planted = ce.startswith("HL:PLANTED_COLUMN:") and t["mark"].startswith("P.C")
            if not planted and not (m and m.group(1) == t["mark"] and m.group(2) == t["storey"]):
                raise R.RuleError(f"{p[2]}: bound concrete {ce} does not carry mark {t['mark']} / {t['storey']}")
            return cl, f"{p[2]} -> formwork R4 row -> T-332 face concrete line (mark + storey checked)"
    if eid.startswith("HL:BEAM_STEEL:"):
        bm = p[2]
        cls = [x["line_id"] for x in L.values() if x["item_code"] == "STR.CONC.BEAM"
               and re.search(rf":{re.escape(bm)}(#|$)", x["element_id"] or "")]
        if cls:
            return cls, f"{bm} -> HL:BEAM_LEDGER concrete line(s) of the member"
    if eid.startswith("FRP:FTG:"):
        cid = "P-C:FTG:" + ":".join(p[2:-1])
        m = [x["line_id"] for x in L.values() if x["element_id"] == cid]
        if m:
            return m[0], "footing route id -> P-C:FTG line of the same id"
    if eid.startswith("P-S:NECK:"):
        cid = "P-C:NECK:" + ":".join(p[2:5])
        m = [x["line_id"] for x in L.values() if x["element_id"] == cid]
        if m:
            return m[0], "neck route id -> P-C:NECK line of the same id"
    if eid.startswith("HL:STAIR_POOL_TANK_STEEL:") and len(p) > 3:
        if p[2].startswith("POOL-") and "STEP" not in eid:
            m = [x["line_id"] for x in L.values() if x["element_id"] in (f"HL:POOL_CONCRETE:{p[2]}:WALLS",
                                                                          f"HL:POOL_CONCRETE:{p[2]}:BASE")]
            if len(m) == 2:
                return m, f"{p[2]} -> HL:POOL_CONCRETE walls + base"
        m = [x["line_id"] for x in L.values() if x["element_id"] == f"HL:STAIR_CONCRETE:{p[2]}:{p[3]}"]
        if m:
            return m[0], "stair part -> HL:STAIR_CONCRETE line of the same part"
    if eid.startswith("HL:SLAB_STEEL:"):
        slabs = [x for x in L.values() if x["item_code"] == "STR.CONC.SLAB"]
        if slabs and not any(x["class"] == "HELD" for x in slabs):
            return "FAMILY:STR.CONC.SLAB", ("family binding: no STR.CONC.SLAB line of the candidate is HELD "
                                            f"({sum(x['class'] == 'RELEASED' for x in slabs)} RELEASED, "
                                            f"{sum(x['class'] == 'EXCLUDED' for x in slabs)} EXCLUDED readings), so "
                                            "a slab bar line cannot be class A")
    if eid.startswith("LIFT_TIE_BEAM:"):
        return LIFT_TIE_CONCRETE, "lift tie beam -> STR.CONC.LIFT LIFT_TIE_BEAM:GF (T-419)"
    if lid.startswith("NEW:"):
        cl = (data["new"][lid].get("beside") or {}).get("concrete_line")
        if cl:
            return cl, "overlay row names its concrete line"
    b = data["basis"].get(lid)
    if b:
        ids = re.findall(r"concrete line (L-[0-9a-f]{20})", " ".join(b.values()))
        if ids:
            return ids[0], "T-297 basis row names the concrete line"
    return None, "NOT_BOUND: no concrete line id is recorded for this element (classed by its own hold text)"


def concrete_class(cl, data):
    if cl is None:
        return None
    if cl == "FAMILY:STR.CONC.SLAB":
        return "RELEASED"
    ids = cl if isinstance(cl, list) else [cl]
    cs = []
    for c in ids:
        x = data["lines"].get(c)
        if x is None:
            raise R.RuleError(f"bound concrete line {c} is not in the V3.0.57 index")
        cs.append(x["class"])
    for k in ("EXCLUDED", "HELD"):
        if k in cs:
            return k
    return "RELEASED"


# ---- hold text -------------------------------------------------------------------------------------------------------
def hold_text(x, eid, data):
    lid = x["line_id"]
    if lid.startswith("NEW:"):
        row = data["new"][lid]
        a = row["after"]
        if (a.get("held_low") is None) != (x["held_low"] is None) or (
                a.get("held_low") is not None and D(str(a["held_low"])) != D(str(x["held_low"]))):
            raise R.RuleError(f"{lid}: manifest row {a.get('held_low')} != T-630 {x['held_low']}")
        b = row.get("beside") or {}
        if x["held_low"] is not None:
            parts = b.get("high_open_by_name") or a.get("held_parts") or []
            return ("OPEN_HIGH: low " + S(D(str(x["held_low"]))) + " kg measured; high open by name: " +
                    ", ".join(parts)), "wiring manifest row (" + (row.get("op_id") or "")[:60] + ")"
        return (b.get("missing") or "HELD"), "wiring manifest row (" + (row.get("op_id") or "")[:60] + ")"
    if eid.startswith("LIFT_TIE_BEAM:"):
        return ("lift tie beam: 5.500 m DRAWING-CONFIRMED, section D-43 not printed (T-419): bars of an unsized beam "
                "not printed"), "T-419 ADD_HELD record"
    for e in data["reg"].get(lid, []):
        if e["class"] != "SUPERSEDED" and e["version"] == "ARCH_TAKEOFF_V3.0.27":
            return (e["rule_result"].get("held_reason") or "HELD"), "T-449 register, ARCH_TAKEOFF_V3.0.27 re-base"
    dgs = data["dg"].get(lid)
    if dgs:
        return dgs[0]["reason"], "Checker downgrade " + " / ".join(sorted(d["downgrade_id"] for d in dgs))
    r = data["v16"].get(lid)
    if r:
        rs = r["inputs"].get("reasons") or []
        return "; ".join(rs) if rs else (r.get("rfi") or r["formula"]), "candidate record (T-297 extract, V3.0.16)"
    raise R.RuleError(f"{lid}: no record states its hold")


def bar_group(eid):
    return eid.split(":")[-1].split("#")[0] if not eid.startswith("FRP:") else eid.split(":")[-1]


# ---- classify --------------------------------------------------------------------------------------------------------
def released_sibling(storey, interval, data, rel_ids):
    for lid in rel_ids:
        x = data["lines"].get(lid)
        if not x:
            continue
        e = x["element_id"] or ""
        m = re.match(r"HL:COLUMN_STEEL:(COL-(GF|1F|2F)-\d+):MAIN_BARS_NET$", e)
        if m and m.group(2) == storey and x["measured_net"] is not None:
            rv = data["v16"].get(lid)
            if rv and D(str(rv["inputs"]["length_m"])) == D(interval):
                got = R.population_kg(rv["inputs"]["count"], rv["inputs"]["length_m"], 16)
                if abs(q(got, "0.001") - D(str(x["measured_net"]))) > D("0.001"):
                    raise R.RuleError(f"sibling {m.group(1)} released {x['measured_net']} != method {got}")
                return {"column": m.group(1), "line_id": lid, "storey": storey, "interval": interval,
                        "released_kg": S(D(str(x["measured_net"]))), "method_kg": S(q(got))}
    return None


def classify(x, data, rel_ids):
    lid = x["line_id"]
    eid = (data["lines"].get(lid) or {}).get("element_id") or lid[len("NEW:STR.REBAR:"):]
    text, src = hold_text(x, eid, data)
    cl, basis = concrete_of(eid, lid, data)
    cc = concrete_class(cl, data)
    row = {"line_id": lid, "element_id": eid, "bar_group": bar_group(eid),
           "state": "OPEN_HIGH" if x["held_low"] is not None else "BLANK",
           "held_low_kg": S(D(str(x["held_low"]))) if x["held_low"] is not None else None,
           "hold_text": text, "hold_source": src, "concrete_line": cl, "concrete_class": cc, "binding": basis}
    if cc in ("HELD", "EXCLUDED"):
        own_kind = None
        try:
            own_kind = R.cause_kind(text)[0]
        except R.RuleError:
            pass
        return dict(row, **{"class": "A", "kind": "A_CONCRETE_" + cc,
                            "cause": f"its concrete element is {cc} in the candidate ({', '.join(cl) if isinstance(cl, list) else cl}): "
                                     "the bars follow that cause; own hold beside it: " + text[:200],
                            "own_kind": own_kind})
    rec = data["v16"].get(lid)
    if eid.startswith("HL:COLUMN_STEEL:") and eid.endswith(":MAIN_BARS_NET") and rec and \
            "D_ctrl settled" in text and cc == "RELEASED":
        col = eid.split(":")[2]
        t = data["t119"][col]
        sib = released_sibling(col.split("-")[1], str(rec["inputs"]["length_m"]), data, rel_ids)
        try:
            if sib is None:
                raise R.RuleError("no released sibling")
            fix = R.d_column_main({"bar_group": "MAIN_BARS_NET", "reasons": rec["inputs"]["reasons"],
                                   "printed": rec["inputs"]["printed"], "count": rec["inputs"]["count"],
                                   "length_m": rec["inputs"]["length_m"]}, t, cc, sib)
            return dict(row, **{"class": "D", "kind": "D_COLUMN_MAIN_D_SETTLED",
                                "cause": R.D_KINDS["D_COLUMN_MAIN_D_SETTLED"] + "; held member: " +
                                         t["framing"].split("| held:")[-1].strip(),
                                "fix": dict(fix, column=col, sibling=sib, t119_interval=t["interval"],
                                            t119_D_ctrl=t["D_ctrl"], printed=rec["inputs"]["printed"],
                                            ledger=rec["inputs"].get("ledger"))})
        except R.RuleError as why:
            row["d_refused"] = str(why)
    kind, cls, meaning = R.cause_kind(text)
    return dict(row, **{"class": cls, "kind": kind, "cause": meaning + ": " + text[:240]})


def build():
    data = load()
    blank, open_hi, rel = targets(data)
    rel_ids = [x["line_id"] for x in rel]
    rows = [classify(x, data, rel_ids) for x in blank + open_hi]
    if len({r["line_id"] for r in rows}) != len(rows) or any(not r["cause"] for r in rows):
        raise R.RuleError("a line is doubled or has no cause")
    fixes = [r for r in rows if r["class"] == "D"]
    for n, r in enumerate(sorted(fixes, key=lambda r: r["fix"]["column"]), 1):
        r["fix"]["fix_row"] = f"FR-T639-{n}"
    by_cls = collections.Counter(r["class"] for r in rows)
    by_kind = collections.Counter((r["class"], r["kind"]) for r in rows)
    by_state = collections.Counter((r["class"], r["state"]) for r in rows)
    fam = collections.Counter((r["class"], ":".join(r["element_id"].split(":")[:2])) for r in rows)
    d_kg = sum((R.population_kg(r["fix"]["count"], r["fix"]["length_m"], r["fix"]["dia_mm"]) for r in fixes), D(0))
    open_low = sum((D(r["held_low_kg"]) for r in rows if r["held_low_kg"]), D(0))
    released = sum((D(str(x["measured_net"])) for x in rel), D(0))
    # finding F-T639-1: RELEASED bar lines whose own bound concrete line is HELD (the class A principle, reversed)
    rel_on_held = []
    for x in rel:
        e = data["lines"][x["line_id"]]["element_id"]
        cl, basis = concrete_of(e, x["line_id"], data)
        cc = concrete_class(cl, data)
        if cc in ("HELD", "EXCLUDED"):
            rel_on_held.append({"line_id": x["line_id"], "element_id": e, "kg": S(D(str(x["measured_net"]))),
                                "concrete_line": cl, "concrete_class": cc, "binding": basis})
    out = {
        "schema": SCHEMA, "rule": RULE, "task": "T-639",
        "candidate": data["t630"]["candidate"], "overlay": "V15 (as T-630)", "pins": PINS,
        "scope": "B11-01 STR.REBAR lines HELD BLANK (801) or HELD with an OPEN high end (6) in the T-630 dry run",
        "counts": {"lines": len(rows), "by_class": dict(sorted(by_cls.items())),
                   "by_class_state": {f"{c}|{s}": n for (c, s), n in sorted(by_state.items())},
                   "by_kind": {f"{c}|{k}": n for (c, k), n in sorted(by_kind.items())},
                   "by_class_family": {f"{c}|{f}": n for (c, f), n in sorted(fam.items())}},
        "totals_kg": {"A": None, "B": None, "C": None,
                      "D": S(q(d_kg)), "D_t": S(q(d_kg / 1000)),
                      "note": "A, B and C carry no computed quantity (R-T639-1); open-high lows stay their own "
                              "HELD lows (" + S(open_low) + " kg) and are not summed into any class",
                      "released_before_kg": S(released), "released_if_D_wired_kg": S(released + q(d_kg)),
                      "released_if_D_wired_t": S(q((released + q(d_kg)) / 1000))},
        "fix_rows": [dict(r["fix"], line_id=r["line_id"], element_id=r["element_id"]) for r in
                     sorted(fixes, key=lambda r: r["fix"]["fix_row"])],
        "open_high": [{"line_id": r["line_id"], "low_kg": r["held_low_kg"], "class": r["class"],
                       "what_keeps_the_high_open": r["hold_text"], "concrete": r["concrete_class"]}
                      for r in rows if r["state"] == "OPEN_HIGH"],
        "d_refused": [{"line_id": r["line_id"], "element_id": r["element_id"], "why": r["d_refused"]}
                      for r in rows if r.get("d_refused")],
        "not_bound": sum(1 for r in rows if r["concrete_line"] is None),
        "finding_F_T639_1": {
            "what": "RELEASED STR.REBAR lines whose own bound concrete line is HELD / EXCLUDED in the same candidate "
                    "(bars released ahead of their concrete); not changed here: Checker downgrade review proposed",
            "lines": rel_on_held, "n": len(rel_on_held),
            "kg": S(sum((D(r["kg"]) for r in rel_on_held), D(0)))},
        "lines": sorted(rows, key=lambda r: (r["class"], r["kind"], r["element_id"])),
        "released": "NOTHING RELEASED; no candidate, engine, rule / knowledge version or registry file changed; "
                    "fix rows are proposals for the wiring manifest (lane I)",
    }
    return out


def write():
    out = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(out), encoding="utf-8")
    return out


def render_md(o):
    c = o["counts"]
    L = [f"# T-639 rebar hold census ({o['rule']}; {o['candidate']}, overlay {o['overlay']})", "",
         f"Lines classed: {c['lines']} (801 HELD blank + 6 open-high). By class: {c['by_class']}.", "",
         "## By class and cause kind", "", "| class | kind | lines |", "|---|---|---|"]
    L += [f"| {k.split('|')[0]} | {k.split('|')[1]} | {n} |" for k, n in c["by_kind"].items()]
    L += ["", "## By class and element family", "", "| class | family | lines |", "|---|---|---|"]
    L += [f"| {k.split('|')[0]} | {k.split('|')[1]} | {n} |" for k, n in c["by_class_family"].items()]
    t = o["totals_kg"]
    L += ["", "## Class D fix rows (kg; display t)", "",
          f"Total D {t['D']} kg = {t['D_t']} t. Released before {t['released_before_kg']} kg; with D wired "
          f"{t['released_if_D_wired_kg']} kg = {t['released_if_D_wired_t']} t.", "",
          "| fix row | column | storey | n | d | L m | kg | t | released sibling (method check) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for f in o["fix_rows"]:
        s = f["sibling"]
        L.append(f"| {f['fix_row']} | {f['column']} | {f['storey']} | {f['count']} | {f['dia_mm']} | {f['length_m']} "
                 f"| {f['kg']} | {f['t']} | {s['column']} {s['released_kg']} kg = {s['method_kg']} |")
    L += ["", "## The 6 open-high lines", "", "| line | low kg | class | what keeps the high end open |", "|---|---|---|---|"]
    L += [f"| {r['line_id']} | {r['low_kg']} | {r['class']} | {r['what_keeps_the_high_open'][:200]} |"
          for r in o["open_high"]]
    L += ["", "## D refused (column D_ctrl-settled main bars not freed)", ""]
    L += [f"- {r['element_id']}: {r['why']}" for r in o["d_refused"]] or ["- none"]
    f1 = o["finding_F_T639_1"]
    L += ["", f"## Finding F-T639-1: {f1['n']} RELEASED bar lines on a HELD concrete line ({f1['kg']} kg)", ""]
    L += [f"- {r['element_id']} {r['kg']} kg on {r['concrete_line']} ({r['concrete_class']})" for r in f1["lines"]]
    L += ["", f"Lines with no recorded concrete binding (classed by own hold text): {o['not_bound']}.", "",
          o["released"], ""]
    return "\n".join(L)


if __name__ == "__main__":
    o = build()
    print(json.dumps({k: o[k] for k in ("counts", "totals_kg", "not_bound")}, indent=1))
