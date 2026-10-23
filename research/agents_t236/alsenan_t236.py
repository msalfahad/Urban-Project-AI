"""T-236 on the development villa (P7757; the active development case, owner 19:00 (2)): trade completeness of a BOQ
lines file against the INDEPENDENT inventories already merged in the repository. Reads only; prints and writes counts,
statuses, printed marks and DXF handles (no coordinate, no name, no drawing content).

    python3 -I research/agents_t236/alsenan_t236.py <BOQ_LINES.json> --label <run label> [--out DIR] [--input-only]

<BOQ_LINES.json> is a run on the Drive copies (Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip,
"ST7757 dxf.dxf"): the released ARCH_TAKEOFF_V2.9 run (v29/BOQ_LINES.json of research/agents_t167/v304_run.py) or the
opt-in candidate ARCH_TAKEOFF_V3.0.8 (v308/V3_0_8_BOQ_LINES.json of research/agents_t231/v308_run.py).

Independent inventories (each built from the drawings without the engine's element register, merged, checker-cited):
  CONCRETE.FOOTING  research/agents_t233/LEDGER_T233.csv CONC.FOOTING rows: one row per drawn footing outline of the
                    FOUNDATION PLAN (DXF handle, type from its tag; T-233 MERGED 2ecb5bf0, Checker 20:14)
  CONCRETE.NECK     research/agents_t217/LEDGER_T217.csv storey FOUNDATION, existence DRAWN (neck outline handle on FP /
                    CAP / GBP; T-217 MERGED 65fef8fa, Checker 13:53)
  CONCRETE.COLUMN   the same ledger, storeys GF / 1F / 2F, existence DRAWN on that storey's roof-slab plan (a
                    SCHEDULE_TYPE_ONLY row is a type printed in the schedule, not drawn on the plan: not an element)
  DOORS / WINDOWS   research/agents_t198/OPENINGS_T198.csv KIND DOOR / WINDOW (census r3, MERGED; residual risk named:
                    the census was seeded from the engine's opening list and then corrected by drawing reads, so an
                    opening that BOTH missed is not excluded by it)
Every other principal trade has no merged independent inventory on the working head: its row says
NO_INDEPENDENT_INVENTORY or NOT_MEASURED, with the source that would supply it in NEXT_SOURCE below.

Joins (stated, never guessed):
  footings, necks, columns  MARK COUNT per storey: key <storey>:<printed mark>#k, k = 1 .. n per mark on each side
                   independently. The engine element id carries the printed mark and a position in the run's own frame
                   (the same column is 'C11@246481,..' in this run and 'C11@170513,..' in the committed route G
                   register: one constant translation), so an id join across runs is not stable; a count join says
                   HOW MANY of a mark are missing or extra on a storey, never WHICH occurrence;
  planted columns  EXACT by handle where the line is a checker-merged planted-column record (HL:PLANTED_COLUMN) that
                   prints the start / own-outline handles of the T-217 member; a route G line SUPERSEDED by such a
                   record is the same physical element and is not joined again (listed as superseded);
  openings         EXACT by token: an ENGINE_REF token 'DOOR-<storey>-<hash>' equals a door line's element id, a token
                   'OP-nnn' / 'COP-nnn' equals the opening part of a window / passage line's element id on that storey.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import trade_completeness_v1 as TC  # noqa: E402
from tools import trade_completeness as R  # noqa: E402

STOREY = {"FOUNDATION": "FDN", "GF": "GF", "1F": "1F", "2F": "2F"}
NEXT_SOURCE = {
    "CONCRETE.BEAM": "T-241 beam table per storey (T-229 CENSUS.csv binds route G bands: engine-derived, not used)",
    "CONCRETE.SLAB": "T-234 LEDGER_T234.csv (READY 352925c3, not merged)",
    "CONCRETE.GROUND_BEAM": "T-242 ground-beam table", "CONCRETE.STRAP": "T-242 / T-174 strap census",
    "CONCRETE.BLINDING": "T-233 CONC.BLINDING rows (one per footing pad; not joined: the engine bills blinding as one "
                         "line per plan, not per pad)",
    "MASONRY.100": "T-017 masonry census (READY, not merged)", "MASONRY.150": "T-017", "MASONRY.200": "T-017",
    "PLASTER": "a room-face census independent of the room model", "PAINT": "as PLASTER",
    "FLOOR_FINISH": "a room census from the printed room labels", "CEILING": "as FLOOR_FINISH",
    "WALL_FINISH": "a wet-room wall-face census", "WATERPROOFING": "a wet-room / roof zone census",
    "STAIRS": "T-184 stair ledger (flight census)", "RAILINGS": "T-164 railing ledger",
    "FORMWORK": "no formwork line exists in any run", "REBAR": "per-member bar schedules (T-171 / T-191 ledgers)",
}


def _csv(path):
    with open(ROOT / path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def footing_inventory():
    rows = [r for r in _csv("research/agents_t233/LEDGER_T233.csv") if r["line"] == "CONC.FOOTING"]
    n = Counter()
    els = []
    for r in sorted(rows, key=lambda r: (r["type"], r["outline"])):
        n[r["type"]] += 1
        els.append({"floor": "FDN", "label": f"{r['type']}#{n[r['type']]}", "ref": f"outline {r['outline']}"})
    return {"source": "T-233 footing outlines (FOUNDATION PLAN, MERGED 2ecb5bf0)", "basis": "CENSUS",
            "trade": "CONCRETE.FOOTING", "floors": ["FDN"], "elements": els}


ID_RE = re.compile(r"(?:^|:)(?P<kind>COL|NECK:COL):(?P<sheet>SH\d+):(?P<mark>[A-Z0-9]+)@(?P<x>-?\d+),(?P<y>-?\d+)"
                   r"(?:\|(?P<st>\w+))?$")


def _parse(eid):
    m = ID_RE.search(eid or "")
    if not m:
        return None
    return (m["kind"], m["sheet"], m["mark"], int(m["x"]), int(m["y"]), m["st"])


def column_inventories():
    """necks and columns from T-217; also the engine ids the ledger names for each element (in the committed route G
    frame), used by solve_offsets() for an exact join."""
    rows = _csv("research/agents_t217/LEDGER_T217.csv")
    sec = json.loads((ROOT / "research/agents_t217/ALSENAN_SECTION_INPUT.json").read_text(encoding="utf-8"))
    inst = {i["fp_outline"]: i["id"] for i in sec["instances"]}
    n = Counter()
    neck, col, named = [], [], {}
    for r in sorted(rows, key=lambda r: (r["storey"], r["mark"], r["member"])):
        if r["existence"] != "DRAWN":        # SCHEDULE_TYPE_ONLY: a type printed in the schedule, not a drawn member
            continue
        st = STOREY[r["storey"]]
        n[(st, r["mark"])] += 1
        key = f"{st}:{r['mark']}#{n[(st, r['mark'])]}"
        el = {"floor": st, "label": key.split(":", 1)[1], "ref": f"outline {r['member']}"}
        (neck if st == "FDN" else col).append(el)
        ident = r["released_line"] if st != "FDN" else (f"NECK:{inst[r['member']]}" if r["member"] in inst else "")
        p = _parse(ident.replace("NECK:NECK:", "NECK:"))
        if p:
            named[(p[0], p[1], p[2], p[3], p[4], st)] = key
    for m in sorted(sec["members_starting_on_a_slab"], key=lambda m: (m["storey"], m["start_handle"])):
        if m.get("on_neck"):                 # over a neck: the column of that neck, already a ledger row (one element)
            continue
        st = STOREY[m["storey"]]
        n[(st, "PC")] += 1                   # planted column (T-220): starts on a slab, own outline on the storey
        col.append({"floor": st, "label": f"PC#{n[(st, 'PC')]}",
                    "ref": f"start {m['start_sheet']} {m['start_handle']}, own outline {m['own_outline']['sheet']} "
                           f"{m['own_outline']['handle']}"})
    return [{"source": "T-217 neck outlines (FP / CAP / GBP, MERGED 65fef8fa)", "basis": "CENSUS",
             "trade": "CONCRETE.NECK", "floors": ["FDN"], "elements": neck},
            {"source": "T-217 columns drawn on each roof-slab plan + T-217 / T-220 members starting on a slab "
                       "(MERGED 65fef8fa)", "basis": "CENSUS", "trade": "CONCRETE.COLUMN",
             "floors": ["GF", "1F", "2F"], "elements": col}], named


def solve_offsets(named, engine_ids, tol=2):
    """per sheet, the one plan translation between the ledger's id frame and this run's id frame: the most common
    (dx, dy) over pairs of the same kind, sheet and mark, accepted only when it maps at least 90 % of the ledger ids of
    that sheet onto an engine id within tol units. Returns {sheet: (dx, dy)} and a log; a sheet without an accepted
    translation keeps the count join."""
    eng = [p for p in (_parse(e) for e in engine_ids) if p]
    out, log = {}, {}
    for sheet in sorted({k[1] for k in named}):
        cand = Counter()
        for k in named:
            if k[1] != sheet:
                continue
            for p in eng:
                if p[0] == k[0] and p[1] == sheet and p[2] == k[2]:
                    cand[(p[3] - k[3], p[4] - k[4])] += 1
        if not cand:
            log[sheet] = "no candidate"
            continue
        (dx, dy), _c = cand.most_common(1)[0]
        mine = [k for k in named if k[1] == sheet]
        hit = sum(1 for k in mine if any(p[0] == k[0] and p[2] == k[2] and abs(p[3] - k[3] - dx) <= tol and
                                          abs(p[4] - k[4] - dy) <= tol for p in eng if p[1] == sheet))
        ok = hit >= 0.9 * len(mine)
        log[sheet] = f"translation ({dx}, {dy}) maps {hit} / {len(mine)} ledger ids: {'EXACT' if ok else 'not used'}"
        if ok:
            out[sheet] = (dx, dy)
    return out, log


def opening_inventories():
    rows = _csv("research/agents_t198/OPENINGS_T198.csv")
    inv = {"DOOR": [], "WINDOW": []}
    tokens = {}
    for r in rows:
        if r["KIND"] not in inv:
            continue
        key = f"{r['FLOOR']}:{r['ID']}"
        inv[r["KIND"]].append({"floor": r["FLOOR"], "label": r["ID"], "ref": r["ENGINE_REF"] or "census only"})
        for t in (x.strip() for x in (r["ENGINE_REF"] or "").split("/")):
            if t:
                tokens[(r["FLOOR"], t)] = (("DOORS" if r["KIND"] == "DOOR" else "WINDOWS"), key)
    out = [{"source": "T-198 opening census r3 (MERGED)", "basis": "CENSUS", "trade": "DOORS",
            "floors": ["GF", "1F", "2F"], "elements": inv["DOOR"]},
           {"source": "T-198 opening census r3 (MERGED)", "basis": "CENSUS", "trade": "WINDOWS",
            "floors": ["GF", "1F", "2F"], "elements": inv["WINDOW"]}]
    return out, tokens, sorted(r["ID"] for r in rows)


MARK_RE = {"CONCRETE.FOOTING": re.compile(r":FTG:[^:]+:([A-Z0-9+]+)@"),
           "CONCRETE.NECK": re.compile(r"NECK:COL:[^:]+:([A-Z0-9]+)@"),
           "CONCRETE.COLUMN": re.compile(r":COL:[^:]+:([A-Z0-9]+)@")}


def storey_levels():
    """storey finished-floor levels as printed, one row per source sheet (T-206 r2 level chain, MERGED): the FFL datums of
    the storey floor chains and of the GF exterior chain. A level is compared only with the same storey and datum."""
    d = json.loads((ROOT / "research/agents_t206/ALSENAN_LEVEL_INPUT_R2.json").read_text(encoding="utf-8"))
    ch = {c["chain_id"]: c for c in d["chains"]}
    out = []
    for x in d["datums"]:
        c = ch[x["chain_id"]]
        if x["kind"] != "FFL" or c["family"] not in ("FLOOR", "FOUNDATION") or not isinstance(x.get("value"), (int, float)):
            continue
        for part in x["ref"].split(";"):          # each printed source of the value is its own row
            part = part.strip()
            if not part or ("LEVEL" not in part and "DIMENSION" not in part and "SECTION" not in part):
                continue
            sheet = part.split(" LEVEL")[0].split(" DIMENSION")[0].strip()
            sheet = {"P7757_DXF_COMPRESSED.zip": "P7757", "ST7757 SH08": "ST7757 dxf.dxf SH08"}.get(sheet, sheet)
            out.append({"sheet": sheet, "storey": c["storey"], "datum": "FFL", "level_m": x["value"],
                        "ref": x["chain_id"]})
    # one row per (sheet, storey, value): the same print read for two chains is one print
    uniq = {(r["sheet"], r["storey"], r["level_m"]): r for r in out}
    return [uniq[k] for k in sorted(uniq)]


def door_register(path, tokens):
    """the run's own door schedule (DOOR_SCHEDULE.json beside the lines): a door element the engine knows but does not
    release carries no BOQ line; it is entered in the register as HELD with the schedule's own section and state as the
    reason (an engine hold outside the BOQ, named, never a quantity)."""
    if not path or not Path(path).exists():
        return []
    els = json.loads(Path(path).read_text(encoding="utf-8"))["doors"]["elements"]
    out = []
    for e in els:
        hit = tokens.get((e["floor"], e["element_id"]))
        if hit and hit[0] == "DOORS" and not e.get("released"):
            fl, lab = hit[1].split(":", 1)
            out.append({"trade": "DOORS", "floor": fl, "label": lab, "status": "HELD",
                        "reason": f"engine door schedule {e['section']} (state {e['state']}, class {e['class']}): no "
                                  "BOQ line"})
    return out


def build_input(lines, door_schedule=None):
    finv = footing_inventory()
    cinv, named = column_inventories()
    offsets, offset_log = solve_offsets(named, [ln["location"]["element_id"] for ln in lines])
    oinv, tokens, census_ids = opening_inventories()
    links, unbound, exact = {}, Counter(), Counter()
    n = Counter()
    pc_by_handles = [(f"{e['floor']}:{e['label']}", re.findall(r"(?:start [A-Z]+ |outline [A-Z]+ )([0-9A-F]+)", e["ref"]))
                     for e in cinv[1]["elements"] if e["label"].startswith("PC#")]
    for ln in sorted(lines, key=lambda x: x["location"]["element_id"] or x["line_id"]):
        eid = ln["location"]["element_id"] or ""
        tr = TC.line_trade(ln)
        st = STOREY.get(ln["location"].get("floor"), ln["location"].get("floor"))
        k = None
        if ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and "SUPERSEDED" in (ln.get("notes") or ""):
            unbound[f"{tr} superseded line (its replacement carries the element)"] += 1
            continue                                         # the same physical element as its replacement line
        if eid.startswith("HL:PLANTED_COLUMN:"):
            printed = str((ln["calculation"].get("inputs") or {}).get("printed") or "")
            hit = [e for e in pc_by_handles if any(re.search(rf"\b{h}\b", printed) for h in e[1])]
            if len(hit) == 1:
                links[ln["line_id"]] = [hit[0][0]]          # EXACT: the record prints the inventory's handles
                continue
            unbound[f"{tr} planted record not bound by handle"] += 1
        p = _parse(eid) if tr in ("CONCRETE.COLUMN", "CONCRETE.NECK") else None
        if p and p[1] in offsets:
            dx, dy = offsets[p[1]]
            st2 = "FDN" if tr == "CONCRETE.NECK" else st
            hit = [key for kk, key in named.items() if kk[0] == p[0] and kk[1] == p[1] and kk[2] == p[2] and
                   abs(p[3] - kk[3] - dx) <= 2 and abs(p[4] - kk[4] - dy) <= 2 and kk[5] == st2]
            if len(hit) == 1:
                links[ln["line_id"]] = hit
                exact[tr] += 1
                continue
        if tr in MARK_RE:
            if tr != "CONCRETE.COLUMN":
                st = "FDN"
            m = MARK_RE[tr].search(eid)
            if m:
                n[(tr, st, m.group(1))] += 1
                k = f"{st}:{m.group(1)}#{n[(tr, st, m.group(1))]}"
                if tr in ("CONCRETE.COLUMN", "CONCRETE.NECK") and p and p[1] in offsets:
                    k = f"{st}:{m.group(1)}#unjoined-{ln['line_id'][-8:]}"   # the exact join found no ledger element
            else:
                unbound[f"{tr} (no printed mark in the engine id)"] += 1
                k = f"{st}:?{ln['line_id'][-8:]}"
        elif tr in ("DOORS", "WINDOWS") or ln["item_code"] == "ARCH.PASSAGE":
            part = eid.rsplit(":", 1)[-1]
            hit = tokens.get((st, eid)) or tokens.get((st, part))
            if hit and hit[0] == tr:
                k = hit[1]
            elif hit:
                unbound[f"{tr} line on a census {hit[0]} row"] += 1
            elif tr in ("DOORS", "WINDOWS"):
                unbound[tr] += 1
                k = f"{st}:?{ln['line_id'][-8:]}"            # no census row names this engine element
        if k:
            links[ln["line_id"]] = [k]
    return {"inventories": [finv] + cinv + oinv, "lines": lines, "line_links": links,
            "register": door_register(door_schedule, tokens), "opening_census": census_ids,
            "levels": storey_levels()}, {"unbound": dict(unbound), "exact_join": dict(exact), "offsets": offset_log}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("lines")
    ap.add_argument("--label", required=True)
    ap.add_argument("--out")
    ap.add_argument("--door-schedule", help="the run's DOOR_SCHEDULE.json (engine holds outside the BOQ)")
    a = ap.parse_args(argv)
    raw = json.loads(Path(a.lines).read_text(encoding="utf-8"))
    lines = raw["lines"] if isinstance(raw, dict) else raw
    inp, unbound = build_input(lines, a.door_schedule)
    rep = R.run(inp)
    rows = list(R.trade_rows(rep))
    print(f"== {a.label}: {len(lines)} lines; join: {unbound}")
    for r in rows:
        if r["lines"] or r["found"] or r["trade"] in TC.PRINCIPAL_SET:
            print(f"{r['trade']:<24} {r['status']:<27} found {r['found']:>3}  compl {r['completeness_n_d']:>8}  "
                  f"verif {r['verified_n_d']:>8}  miss {r['missing']:>2}  dup {r['duplicated']:>2}  held {r['held']:>2}  "
                  f"reg_only {r['register_only']:>2}  lines {r['lines']:>4}")
    for lv in rep["levels"]:
        print("level", lv["storey"], lv["datum"], lv["status"], lv["sheets"])
    ded = Counter(d["status"] for d in rep["deductions"])
    print("deduction rows:", dict(ded))
    for d in rep["deductions"]:
        if d["status"] == "REFUSED":
            print("  REFUSED", d["trade"], d["line_id"], d["problems"])
    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        R.write(rep, out)
        summ = {"label": a.label, "lines": len(lines), "unbound_engine_elements": unbound,
                "trades": rows, "deductions": dict(ded), "levels": rep["levels"],
                "refused_deductions": [d for d in rep["deductions"] if d["status"] == "REFUSED"],
                "next_source": NEXT_SOURCE,
                "findings": {t: [{"key": e["key"], "status": e["status"], "refs": e["refs"], "reason": e["reason"],
                                  "duplicate_lines": e["duplicate_lines"]}
                                 for e in rep["elements"] if e["trade"] == t and
                                 (e["status"] in ("MISSING", "REGISTER_ONLY", "CONFLICT", "UNRESOLVED") or e["duplicated"])]
                             for t in ("CONCRETE.FOOTING", "CONCRETE.NECK", "CONCRETE.COLUMN", "DOORS", "WINDOWS")}}
        (out / "SUMMARY.json").write_text(json.dumps(summ, indent=1, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
