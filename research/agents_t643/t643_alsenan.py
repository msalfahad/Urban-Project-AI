"""T-643 development-villa build (research, unwired), R-T643-1 (t643_rules.py), candidate ARCH_TAKEOFF_V3.0.58 as the
T-630 dry run (V3.0.57 line index + overlay V15):

  part 1  the 14 RELEASED column main-bar lines (754.723 kg) that T-639 (finding F-T639-1) found on HELD concrete
          lines: each decided DOWNGRADE (the concrete hold enters n / L / d) or KEEP (it does not; cited);
  part 2  the 208 T-639 lines with no recorded concrete binding (203 class B + 5 class C): each BOUND by an exact id
          route or UNRESOLVED with the reason.

Inputs (pinned, read only): the T-639 census, the V3.0.57 line index, the T-297 extract of the candidate bar records
(V3.0.16: count, length, printed reading), the T-449 concrete correction register (the hold rule, its facts and the
declared levels per concrete line), T-119 (storey interval per column), T-110 (beam member -> band), T-332 (formwork
face -> concrete line, ground-beam runs by face-handle pair), T-630 (released kg per line).
Independent drawing check: the 'Schedule of Columns' of the structural set (Drive folder 'Alsenan chalet project',
file 'ST7757 dxf.dxf'), bar count and diameter of each mark / storey re-read by hand (SCHEDULE_REREAD below) and, when
the private copy is present in .work/private, re-read by reread_schedule() from the block attributes.

Rebuild (wrapper only): `URBAN_T643_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-643 tests/t643/test_t643.py::
test_write_outputs`; check: `bash scripts/agent_env.sh pytest --tree task-T-643 tests/t643`. No coordinate, no drawing
text beyond marks, counts and recorded hold reasons, no client name."""
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
import t643_rules as R  # noqa: E402

D, q = R.D, R.q
SCHEMA, RULE = "URBAN_T643_REBAR_ON_HELD_CONCRETE_V1", "R-T643-1"
T639 = "research/agents_t639/out/REBAR_HOLD_CENSUS_T639.json"
INDEX = "research/agents_t507/out/LINE_INDEX_V3_0_57.json"
V16 = "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json"
CREG = "research/agents_t449/out/CORRECTION_REGISTER_CONCRETE_T449.json"
T119 = "research/agents_t119/COLUMNS_TO_CONTROLLING_MEMBER.csv"
T110 = "research/agents_t110/BEAM_MEMBER_REGISTER.csv"
T332 = "research/agents_t332/FORMWORK_T332_BY_FACE.csv"
T297J = "research/agents_t297/DATUM_JOIN_T297.json"
T630 = "research/agents_t630/out/E2E_BOQ_DRY_RUN_T630.json"
PINS = {T639: "0555f732893dd7d3", INDEX: "fed5141ea31bfdd9", V16: "2f28367b81fe362d", CREG: "a15bb04b2109e29a",
        T119: "dbe1ce155c7d7356", T110: "368d0fa2d690fb02", T332: "15c188724a60d580", T297J: "af5bba3f98ec6352",
        T630: "e5dde7867c8fe6ad"}
OUT_JSON = HERE / "out" / "REBAR_ON_HELD_CONCRETE_T643.json"
OUT_MD = HERE / "out" / "REBAR_ON_HELD_CONCRETE_T643.md"
PRIVATE_DXF = ROOT.parent / "private" / "ST7757.dxf"
EXPECT = {"inherit": 14, "inherit_kg": D("754.723"), "unbound": 208}

# Own hand re-read of the 'Schedule of Columns' (worker 1, 2026-11-08): (mark, storey) -> (bars, diameter mm).
SCHEDULE_REREAD = {("C", "GF"): (8, 16), ("C3", "GF"): (8, 16), ("C4", "1F"): (8, 16), ("C5", "1F"): (8, 16),
                   ("C6", "1F"): (8, 16), ("C9", "1F"): (12, 16), ("C1", "2F"): (6, 16), ("C2", "2F"): (6, 16)}


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


def load():
    check_pins()
    idx = _json(INDEX)
    by_el = collections.defaultdict(list)
    for x in idx["lines"]:
        by_el[x["element_id"]].append(x["line_id"])
    creg = collections.defaultdict(list)
    for e in _json(CREG)["entries"]:
        if e.get("line_id") and e["class"] != "SUPERSEDED":
            creg[e["line_id"]].append(e)
    t110 = collections.defaultdict(list)
    for r in _csv(T110):
        t110[r["member_id"]].append(r)
    return {"t639": _json(T639), "lines": {x["line_id"]: x for x in idx["lines"]}, "by_el": by_el,
            "v16": {x["line_id"]: x for x in _json(V16)["lines"]}, "creg": creg,
            "t119": {r["id"]: r for r in _csv(T119)}, "t110": t110, "t332": _csv(T332),
            "datum": {r["line_id"]: r for r in _json(T297J)["rows"]},
            "t630": {x["line_id"]: x for x in _json(T630)["per_line"]}}


# ---- part 1: the 14 --------------------------------------------------------------------------------------------------
def effective_hold(cl, data):
    es = data["creg"].get(cl, [])
    if len(es) != 1:
        raise R.RuleError(f"{cl}: {len(es)} effective concrete register entries (one expected)")
    e = es[0]
    rr, ev = e["rule_result"], e.get("evidence") or {}
    return {"rule": e["rule"], "version": e["version"], "task": e["task"], "facts_used": rr.get("facts_used") or [],
            "held_reason": rr.get("held_reason"), "held_item": (e.get("patch") or {}).get("held_item"),
            "facts_h": ev.get("facts_h"), "declared_levels": ev.get("levels") or [],
            "low": rr.get("low"), "high": rr.get("high")}


def bar_inputs(lid, data):
    rec = data["v16"][lid]["inputs"]
    m = re.search(r"p\.9 (C\w*) (GF|1F|2F): (\d+) ø (\d+)", rec["printed"])
    if not m:
        raise R.RuleError(f"{lid}: printed reading not parsed: {rec['printed']}")
    return {"population": "COLUMN_MAIN_BARS_OVER_STOREY_INTERVAL", "mark": m.group(1), "storey": m.group(2),
            "count": int(D(str(rec["count"]))), "dia_mm": int(m.group(4)), "length_m": S(D(str(rec["length_m"]))),
            "printed": rec["printed"], "released_kg": S(D(str(data["t630"][lid]["measured_net"]))),
            "ledger_count_printed": int(m.group(3))}


def S(x):
    return None if x is None else str(D(x).normalize()) if D(x) != D(x).to_integral() else str(int(D(x)))


def part1(data):
    f = data["t639"]["finding_F_T639_1"]
    if f["n"] != EXPECT["inherit"] or D(f["kg"]) != EXPECT["inherit_kg"]:
        raise R.RuleError(f"F-T639-1 is {f['n']} / {f['kg']}, not 14 / 754.723")
    rows = []
    for r in f["lines"]:
        lid, cl = r["line_id"], r["concrete_line"]
        col = r["element_id"].split(":")[2]
        if data["lines"][lid]["class"] != "RELEASED" or data["lines"][cl]["class"] != "HELD":
            raise R.RuleError(f"{col}: states moved (bar {data['lines'][lid]['class']}, concrete {data['lines'][cl]['class']})")
        bar = bar_inputs(lid, data)
        if bar["ledger_count_printed"] != bar["count"]:
            raise R.RuleError(f"{col}: printed {bar['ledger_count_printed']} != count {bar['count']}")
        t = data["t119"][col]
        if (t["mark"], t["storey"]) != (bar["mark"], bar["storey"]) or D(t["interval"]) != D(bar["length_m"]):
            raise R.RuleError(f"{col}: T-119 mark / storey / interval differ from the bar record")
        hold = effective_hold(cl, data)
        sch = SCHEDULE_REREAD.get((bar["mark"], bar["storey"]))
        if sch is None:
            raise R.RuleError(f"{col}: no schedule re-read for {bar['mark']} {bar['storey']}")
        dec = R.decide_inherit(bar, hold, schedule={"count": sch[0], "dia_mm": sch[1]})
        dj = data["datum"].get(cl)
        rows.append({"column": col, "bar_line": lid, "concrete_line": cl,
                     "concrete_element": data["lines"][cl]["element_id"], "mark": bar["mark"], "storey": bar["storey"],
                     "n": bar["count"], "d_mm": bar["dia_mm"], "L_m": bar["length_m"], "released_kg": bar["released_kg"],
                     "t119": {"interval": t["interval"], "height": t["height"], "D_ctrl": t["D_ctrl"],
                              "status": t["status"], "hold_cause": t["hold_cause"]},
                     "schedule_reread": {"bars": sch[0], "d_mm": sch[1], "agrees": True},
                     "concrete_hold": hold,
                     "t297_length_datum": (dj or {}).get("length_datum"),
                     **{k: (S(v) if isinstance(v, D) else v) for k, v in dec.items()}})
    return sorted(rows, key=lambda r: (r["decision"], r["column"]))


def downgrade_records(rows):
    """downgrade-only record proposals (owner 2026-10-24 23:57); the Checker issues or validates them."""
    out = []
    for r in rows:
        if r["decision"] != "DOWNGRADE":
            continue
        h = hashlib.sha256(f"T-643|{r['bar_line']}|{r['concrete_hold']['rule']}".encode()).hexdigest()[:16]
        out.append({"schema": "URBAN_CHECKER_DOWNGRADE_V1 (PROPOSAL, not issued)", "proposal_id": f"DGP-T643-{h}",
                    "line_ids": [r["bar_line"]], "state": "HELD", "unit": "kg", "engine_qty": D(r["released_kg"]),
                    "candidate_version": "ARCH_TAKEOFF_V3.0.58 (T-630 dry run)",
                    "reason": f"UNSUPPORTED BASIS: {r['column']} main bars {r['n']} T{r['d_mm']} x {r['L_m']} m use the "
                              f"storey interval to the roof; {r['concrete_hold']['held_reason']} "
                              f"({r['concrete_hold']['held_item']}); the same member's concrete line {r['concrete_line']} "
                              "is HELD on it (T-297 LB-10: one member, one datum status across trades)",
                    "evidence": [{"sheet": "ST p.9 schedule of columns", "printed_value":
                                  f"{r['mark']} {r['storey']}: {r['n']} ø {r['d_mm']} (count / diameter printed; the "
                                  "length is the interval, not printed)"}],
                    "checker": None, "resolved": False})
    for o in out:
        o["engine_qty"] = str(o["engine_qty"])
    return out


# ---- part 2: the 208 -------------------------------------------------------------------------------------------------
def gb_runs(data):
    """face-handle pair -> {(run key, concrete line id)} from the T-332 ground-beam faces (no 'tee:' cover rows)."""
    runs = collections.defaultdict(set)
    for r in data["t332"]:
        if r["element"] != "GROUND_BEAM" or r["item"].startswith("tee:"):
            continue
        m = re.match(r"(?:span )?((ARC:)?[0-9A-F]+(?:\+[0-9A-F]+)+)(#\d+)?\b", r["item"])
        if not m:
            continue
        ids = {x for x in (r["line_id"], r["new_line_id"]) if x}
        ids |= set(re.findall(r"L-[0-9a-f]{20}", r["tie_reason"] or ""))
        for lid in ids:
            runs[m.group(1)].add(((m.group(1) + (m.group(3) or "")), lid))
    return runs


def _cls(ids, data):
    out = []
    for lid in sorted(set(ids)):
        x = data["lines"].get(lid)
        if x is None:
            raise R.RuleError(f"bound concrete line {lid} is not in the V3.0.57 index")
        out.append((lid, x["class"]))
    return out


def bind_beam(eid, data):
    bm = eid.split(":")[2]
    fl = bm.split("-")[1]
    reg = data["t110"].get(bm)
    if not reg:
        return R.classify_binding([], "", unresolved=f"{bm} is not in the T-110 beam member register")
    ids, notes = [], []
    for m in reg:
        band = m["component"].split(":")[-1]
        hit = data["by_el"].get(f"P-C:BEAMS:{fl}:{band}", []) + data["by_el"].get(f"U-C:BEAMS:{fl}:{band}", [])
        hit += [l for k, v in data["by_el"].items() if k and k.startswith(f"HL:BEAM_LEDGER:{fl}:{bm}#") for l in v]
        if not hit and "." in band:
            parent = band.split(".")[0]
            sibs = [k for k in data["by_el"] if k and re.match(rf"[PU]-C:BEAMS:{fl}:{re.escape(parent)}\.", k)]
            if not sibs:
                hit = data["by_el"].get(f"P-C:BEAMS:{fl}:{parent}", [])
                if hit:
                    notes.append(f"{band} -> parent band {parent} (not split in the candidate)")
        if not hit:
            return R.classify_binding([], "", unresolved=f"{bm} band {band}: no concrete line in V3.0.57")
        ids += hit
    basis = f"{bm} -> T-110 register band(s) -> concrete line(s)" + (f"; {'; '.join(notes)}" if notes else "")
    return R.classify_binding(_cls(ids, data), basis)


def bind_ground(eid, data, runs):
    g = eid.split(":")[2]
    if re.match(r"SB\d$", g):
        ids = [l for k, v in data["by_el"].items() if k and k.startswith(f"HL:STRAP_CONCRETE:{g}:") for l in v]
        return R.classify_binding(_cls(ids, data), f"strap {g} -> HL:STRAP_CONCRETE:{g} (span + in-footing parts; the "
                                                    "bars run over the footings)",
                                  unresolved=f"strap {g}: no HL:STRAP_CONCRETE line")
    m = re.match(r"GSO-(A-)?((?:[0-9A-F]+-)+)(\d+)$", g)
    if not m:
        return R.classify_binding([], "", unresolved=f"{g}: ground-system id not parsed")
    pair = ("ARC:" if m.group(1) else "") + m.group(2).rstrip("-").replace("-", "+")
    rs = runs.get(pair)
    if not rs:
        return R.classify_binding([], "", unresolved=f"{g}: face pair {pair} has no ground-beam run in T-332")
    keys = sorted({k for k, _ in rs})
    basis = (f"{g} -> face-handle pair {pair} -> T-332 run(s) {', '.join(keys)} -> concrete line(s); T-138 span "
             "numbering (-n) is not the T-242 run numbering (#k), so the binding is to the band of the pair")
    return R.classify_binding(_cls([l for _, l in rs], data), basis, mixed_is_unresolved=True)


ST_PARTS = {  # stair part of the bar ledger -> concrete element id that NAMES that part (exact only)
    ("ST-01", "MS2-L"): "HL:STAIR_CONCRETE:ST-01:MS2_L",
    ("ST-01", "MS2-U"): "HL:STAIR_CONCRETE:ST-01:MS2_U",
    ("ST-01", "MS1-U"): "P-C:SCOPE:STAIRS:GF:CC-7390ea1139:FLIGHTS#CLOSABLE:VERIFIED_MS1_LD___MS1_U",
    ("ST-02", "RS-A"): "P-C:STAIRS:GROUND:SITE-4df8fcd99d130701#CLOSABLE:OWNER_APPROVED_RS_S___RS_LD___RS_A",
    ("ST-02", "RS-S"): "P-C:STAIRS:GROUND:SITE-4df8fcd99d130701#CLOSABLE:OWNER_APPROVED_RS_S___RS_LD___RS_A",
    ("ST-02", "RS-LD"): "P-C:STAIRS:GROUND:SITE-4df8fcd99d130701#CLOSABLE:OWNER_APPROVED_RS_S___RS_LD___RS_A",
}
ST_UNRESOLVED = {
    ("ST-01", "MS1-L"): "no concrete line names MS1-L; candidate: the remainder line P-C:SCOPE:STAIRS:GF:"
                        "CC-7390ea1139:FLIGHTS (HELD) after the MS1_LD / MS1_U closure (inferred, not recorded)",
    ("ST-01", "MS1-T"): "turn MS1-T has no concrete line of its own (T-111 turn HELD); MS2_TR is the other flight's",
    ("ST-01", "GF-STRIP"): "landing strip: which concrete line carries it is not recorded",
    ("ST-01", "1F-STRIP"): "landing strip: which concrete line carries it is not recorded",
    ("ST-01b", "D1"): "no line names ST-01b; candidate: DG5:ST-01:LOBBY#CLOSABLE:DRAWING_CONFIRMED_D1_steps "
                      "(RELEASED; lobby D1 steps, stair id differs: inferred, not recorded)",
    ("ST-02", "RS-C"): "curved part (owner Q-50 HELD): candidate the remainder line P-C:STAIRS:GROUND:"
                       "SITE-4df8fcd99d130701 (HELD) after the RS_S / RS_LD / RS_A closure (inferred, not recorded)",
    ("ST-03", "E1"): "court stair on no slab plan: no concrete line in the candidate",
    ("TANK", "2F"): "water tank: only 'WATER TANK PLACE' printed; no concrete element in the candidate",
}


def bind_stair_pool(eid, data):
    p = eid.split(":")
    el, part, grp = p[2], p[3], p[4] if len(p) > 4 else ""
    if el == "POOL":
        pools = sorted({k.split(":")[2] for k in data["by_el"] if k and k.startswith("HL:POOL_CONCRETE:")})
        if len(pools) != 1:
            return R.classify_binding([], "", unresolved=f"{len(pools)} pool elements: zone {part} not attributable")
        parts = ["WALLS"] if grp.startswith(("WALL_", "RIM_")) else ["BASE"] if grp.startswith("FLOOR_") else \
            ["WALLS", "BASE"] if grp.startswith("CORNER_") else []
        if not parts:
            return R.classify_binding([], "", unresolved=f"pool bar group {grp} not mapped to walls / base")
        ids = [l for x in parts for l in data["by_el"].get(f"HL:POOL_CONCRETE:{pools[0]}:{x}", [])]
        return R.classify_binding(_cls(ids, data), f"pool zone {part} ({grp}) -> the one pool {pools[0]}: "
                                                    f"{' + '.join(parts)} (p.7 prints R1 / R2 as zones of one pool)")
    key = (el, part)
    if key in ST_PARTS:
        ids = data["by_el"].get(ST_PARTS[key], [])
        return R.classify_binding(_cls(ids, data), f"{el} {part} -> {ST_PARTS[key]} (the line names the part)",
                                  unresolved=f"{ST_PARTS[key]} not in V3.0.57")
    return R.classify_binding([], "", unresolved=ST_UNRESOLVED.get(key, f"{el} {part}: no concrete line names it"))


def bind_lintel(eid, data):
    lin = [x["class"] for x in data["lines"].values() if x["item_code"] == "STR.CONC.LINTEL"]
    c = collections.Counter(lin)
    return R.classify_binding([], "", unresolved=(
        f"{eid} is one aggregate over the lintel population; the STR.CONC.LINTEL lines are "
        f"{c.get('RELEASED', 0)} RELEASED / {c.get('HELD', 0)} HELD and the line carries no per-lintel split"))


def part2(data):
    runs = gb_runs(data)
    nb = [r for r in data["t639"]["lines"] if r["concrete_line"] is None]
    if len(nb) != EXPECT["unbound"]:
        raise R.RuleError(f"{len(nb)} unbound lines, not 208")
    rows = []
    for r in nb:
        e = r["element_id"]
        if e.startswith("HL:BEAM_STEEL:"):
            b = bind_beam(e, data)
        elif e.startswith("HL:GROUND_SYSTEM_STEEL:"):
            b = bind_ground(e, data, runs)
        elif e.startswith("HL:STAIR_POOL_TANK_STEEL:"):
            b = bind_stair_pool(e, data)
        elif e.startswith("LINTEL_BARS:"):
            b = bind_lintel(e, data)
        else:
            raise R.RuleError(f"{e}: no binding route")
        a_now = b["binding"] == "BOUND" and b["concrete_class"] in ("HELD", "EXCLUDED")
        rows.append({"line_id": r["line_id"], "element_id": e, "t639_class": r["class"], "t639_kind": r["kind"],
                     "state": r["state"], **b,
                     "effect": ("also class A (concrete " + b["concrete_class"] + "); stays HELD on its own cause too"
                                if a_now else "stays HELD on its own T-639 cause (concrete RELEASED)"
                                if b["binding"] == "BOUND" else "stays HELD on its own T-639 cause; binding gap named")})
    return sorted(rows, key=lambda r: (r["binding"], r["element_id"]))


def build():
    data = load()
    p1 = part1(data)
    p2 = part2(data)
    kg = lambda rs, k: sum((D(r["released_kg"]) for r in rs if r["decision"] == k), D(0))  # noqa: E731
    keep, down = kg(p1, "KEEP"), kg(p1, "DOWNGRADE")
    if keep + down != EXPECT["inherit_kg"]:
        raise R.RuleError(f"kg do not re-add: {keep} + {down} != 754.723")
    released_before = sum((D(str(x["measured_net"])) for x in data["t630"].values()
                           if x["family"] == "B11-01" and x["item_code"] == "STR.REBAR" and x["class"] == "RELEASED"),
                          D(0))
    fam = collections.Counter((r["binding"], ":".join(r["element_id"].split(":")[:2]), r["concrete_class"] or "-")
                              for r in p2)
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-643", "candidate": "ARCH_TAKEOFF_V3.0.58 (T-630 dry run, overlay V15)",
        "pins": PINS,
        "part1": {"lines": p1, "n": len(p1),
                  "by_decision": dict(collections.Counter(r["decision"] for r in p1)),
                  "kg_kept_released": str(keep), "kg_proposed_held": str(down), "kg_total": str(keep + down),
                  "released_B11_before_kg": str(released_before),
                  "released_B11_if_downgrades_applied_kg": str(released_before - down),
                  "downgrade_proposals": downgrade_records(p1)},
        "part2": {"lines": p2, "n": len(p2),
                  "by_binding": dict(collections.Counter(r["binding"] for r in p2)),
                  "by_binding_family_class": {"|".join(k): v for k, v in sorted(fam.items())},
                  "newly_class_A": sum(1 for r in p2 if r["binding"] == "BOUND"
                                       and r["concrete_class"] in ("HELD", "EXCLUDED")),
                  "unresolved_reasons": dict(collections.Counter(
                      re.sub(r"GSO-\S+|L-[0-9a-f]{20}|[0-9A-F]+(\+[0-9A-F]+)+(#\d+)?", "*", r["reason"])[:110]
                      for r in p2 if r["binding"] == "UNRESOLVED"))},
        "released": "NOTHING RELEASED OR ADDED; no candidate, engine, rule / knowledge version or registry file changed; "
                    "the DOWNGRADE rows are downgrade-only record proposals for the Checker (owner 2026-10-24 23:57)",
    }


def reread_schedule(dxf_path=PRIVATE_DXF):
    """re-read bar count / diameter per (mark, storey) from the private DXF's 'Schedule of Columns' block attributes:
    rows keyed by the mark attribute, storey columns by the header x-positions of 'GROUND FLOOR' / '1st floor' /
    '2nd floor'. Returns {(mark, storey): (bars, d)} for the cells that print both."""
    import ezdxf  # noqa: PLC0415
    msp = ezdxf.readfile(str(dxf_path)).modelspace()
    T = []
    for e in msp:
        if e.dxftype() in ("TEXT", "MTEXT"):
            t = e.dxf.text if e.dxftype() == "TEXT" else e.plain_text()
            T.append((t.strip(), e.dxf.insert.x, e.dxf.insert.y, e.dxf.layer))
        elif e.dxftype() == "INSERT":
            T += [(a.dxf.text.strip(), a.dxf.insert.x, a.dxf.insert.y, "ATT") for a in e.attribs]
    title = [t for t in T if t[0] == "Schedule  of Columns"]
    if len(title) != 1:
        raise R.RuleError(f"{len(title)} column schedules found")
    tx, ty = title[0][1], title[0][2]
    box = [t for t in T if tx - 6000 < t[1] < tx + 13000 and ty - 11000 < t[2] < ty + 100]
    hdr = {}
    for name, st in (("GROUND FLOOR", "GF"), ("1st  floor", "1F"), ("2nd floor  & Top", "2F")):
        h = [t for t in box if t[0] == name]
        if len(h) != 1:
            raise R.RuleError(f"header {name} not found once")
        hdr[st] = h[0][1]
    reinf = sorted(t[1] for t in box if t[0] == "REINF")
    out = {}
    marks = [t for t in box if t[3] == "ATT" and re.fullmatch(r"C\d?", t[0])]
    for mk in marks:
        row = sorted((t for t in box if t[3] == "ATT" and abs(t[2] - mk[2]) < 60 and t is not mk), key=lambda t: t[1])
        for st in ("GF", "1F", "2F"):
            rx = min((x for x in reinf if x > hdr[st] - 1500), key=lambda x: abs(x - hdr[st] - 1500))
            cell = [t for t in row if rx - 700 < t[1] < rx + 1500 and t[0]]
            if len(cell) == 2:
                out[(mk[0], st)] = (int(cell[0][0]), int(cell[1][0]))
    return out


def write():
    out = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(out), encoding="utf-8")
    return out


def render_md(o):
    p1, p2 = o["part1"], o["part2"]
    L = [f"# T-643 rebar on HELD concrete + unbound bar lines ({o['rule']}; {o['candidate']})", "",
         "## Part 1: the 14 RELEASED column main-bar lines on HELD concrete (F-T639-1)", "",
         f"Decisions {p1['by_decision']}: kept released {p1['kg_kept_released']} kg, proposed HELD "
         f"{p1['kg_proposed_held']} kg, total {p1['kg_total']} kg. Released B11 {p1['released_B11_before_kg']} kg -> "
         f"{p1['released_B11_if_downgrades_applied_kg']} kg if the proposals are applied.", "",
         "| column | mark | storey | n x d | L m | kg | concrete hold rule | enters | decision |", "|---|---|---|---|---|---|---|---|---|"]
    for r in p1["lines"]:
        L.append(f"| {r['column']} | {r['mark']} | {r['storey']} | {r['n']} x T{r['d_mm']} | {r['L_m']} | {r['released_kg']} "
                 f"| {r['concrete_hold']['rule']} | {'/'.join(r['inputs_entered']) or 'none'} | {r['decision']} |")
    L += ["", "Downgrade-only record proposals (Checker to issue / validate):", ""]
    L += [f"- {d['proposal_id']} {d['line_ids'][0]} {d['engine_qty']} kg: {d['reason'][:220]}" for d in p1["downgrade_proposals"]]
    L += ["", f"## Part 2: the {p2['n']} bar lines with no recorded concrete binding", "",
          f"By binding: {p2['by_binding']}; newly also class A: {p2['newly_class_A']}.", "",
          "| binding | family | concrete | lines |", "|---|---|---|---|"]
    L += [f"| {k.split('|')[0]} | {k.split('|')[1]} | {k.split('|')[2]} | {v} |" for k, v in p2["by_binding_family_class"].items()]
    L += ["", "UNRESOLVED reasons:", ""] + [f"- {n} x {k}" for k, n in p2["unresolved_reasons"].items()]
    L += ["", o["released"], ""]
    return "\n".join(L)


if __name__ == "__main__":
    o = build()
    print(json.dumps({"p1": {k: o["part1"][k] for k in ("by_decision", "kg_kept_released", "kg_proposed_held")},
                      "p2": {k: o["part2"][k] for k in ("by_binding", "by_binding_family_class", "newly_class_A")}},
                     indent=1))
