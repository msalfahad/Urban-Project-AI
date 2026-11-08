"""T-608: LIFT LANDING OPENINGS SCOPE BY TRADE on the training villa (Alsenan), by R-T608-1.

GF OP-011 (T-175 L-GF-01) and 1F OP-007 (L-1F-01) are framed lift landing doors (T-601 FR-T601-3, Checker 13:58); the
2F one (OP-002, L-2F-01) is carried beside as the cross-check the passage count needs (T-604 F-T604-1). For every line
family the table says whether a candidate line takes the opening, with which kind, whether that is right, the owner
trade and the quantity effect (units apart, HELD never 0).

Reads only committed, sha256-pinned inputs (T608_DRAWN.json = this run's drawing read; the candidate line index; the
merged T-175 / T-128 / T-292 / T-453 / T-487 / T-559 / T-568 / T-511 / T-604 / T-611 records); writes
out/T608_SCOPE_TABLE.json / .md. No candidate, engine, rule, knowledge or registry file touched, nothing released.

  python3 -I research/agents_t608/t608_alsenan.py --write
  python3 -I research/agents_t608/t608_alsenan.py --check
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t608_rules as R  # noqa: E402

D = Decimal
OUT = HERE / "out"
JSON_OUT = OUT / "T608_SCOPE_TABLE.json"
MD_OUT = OUT / "T608_SCOPE_TABLE.md"
IN = {
    "DRAWN": "research/agents_t608/T608_DRAWN.json",
    "INDEX": "research/agents_t507/out/LINE_INDEX_V3_0_57.json",
    "T175_CONS": "research/agents_t175/T175_OPENING_CONSEQUENCES.csv",
    "T175_NET": "research/agents_t175/T175_NET_BLOCK_BY_WALL.csv",
    "T128": "research/agents_t128/ROOMS_T128_R3.csv",
    "T292": "research/agents_t292/LINE_SUMMARY_T292.csv",
    "T453": "research/agents_t453/out/MATERIAL_LEDGER_T453.json",
    "T487": "research/agents_t487/summary_t487.json",
    "T559": "research/agents_t559/out/T559_LEFTOVER.json",
    "T568": "research/agents_t568/T-568_DOORS_WINDOWS_BY_TYPE.md",
    "T511": "research/agents_t511/t511_cement_sand_census.py",
    "V12": "research/agents_t604/out/WIRING_MANIFEST_V12.json",
    "V13": "research/agents_t611/out/WIRING_MANIFEST_V13.json",
}

# Per storey: the opening, its host room line pair, the face height the host line uses (owner G1), and the candidate lines
# of every family (ids read from the V3.0.57 index; the builder refuses a missing id or a changed class).
OPENINGS = {
    "GF": {"engine": "GF OP-011", "record": "L-GF-01", "host_wall": "GF-W08", "room": "GF-08", "face_h": "3.65",
           "passage": "L-77a427c89787ef3480a7", "threshold_arch": "L-6f5806adbacba9118497",
           "strip": "L-2621372661b2eb15b748", "lift_thr": ["L-c32effca1d7eae7f36f8", "L-f2b76041971aa9e86acb"],
           "surround": "L-b66b8e76425d81ff9f19", "skirting": "L-71e2e002a3af624097f0",
           "lintel": "L-8f69c40749d579c14bf1", "block": "L-4165954ce4871eda30cc",
           "plaster": "L-8cecb1d010d5aafbf25d", "paint": "L-c0ac22c964a42e7d71b1",
           "other_held": [("W02 saloon glazing", "6.33")]},
    "1F": {"engine": "1F OP-007", "record": "L-1F-01", "host_wall": "1F-W07", "room": "1F-13", "face_h": "3.35",
           "passage": "L-32d90a7a3cff7e9feb2a", "threshold_arch": "L-084df97d3d41525a65c2",
           "strip": "L-bb09715ec8ccdd5d11a8", "lift_thr": ["L-9840d1da235dd7583427", "L-64dd750f95ead1a38c9a"],
           "surround": "L-d788f643b290e8f92558", "skirting": "L-ba3599ec2dc82c221617",
           "lintel": "L-a500f10eedbd63a147ab", "block": "L-5ffa7157a2fe483dd008",
           "plaster": "L-9b4a7bab033d677e2017", "paint": "L-be48ea84285be20645af", "other_held": []},
    "2F": {"engine": "2F OP-002", "record": "L-2F-01", "host_wall": "2F-W00", "room": "2F-01", "face_h": "3.35",
           "passage": "L-c91732d6f75d440d677e", "threshold_arch": "L-3c5a3be22e861d9d4cfb",
           "strip": "L-17a56dfafc5504f41a28", "lift_thr": ["L-eba7ac43f3fce9bbd0b5", "L-e29e57482abbca2266b0"],
           "surround": "L-fdbd9636828f045aae5a", "skirting": None,
           "lintel": "L-fd8aaedc3457d6648f18", "block": "L-afe984a62285e133ec2f",
           "plaster": "L-ae0cdd794cc5fdbe0c29", "paint": "L-c74cfb4e07bcc47bc5d6", "other_held": []},
}
# Every text-census hit, read by the worker in the private copy (2026-11-07); a hit not listed here stops the build.
REVIEWED_HITS = {
    ("ST7757 dxf.dxf", "lift_words", "1C64"): "the lift BASE label on the foundation plan (pit / raft): not a landing-door "
                                              "note",
    ("ST7757 dxf.dxf", "supply_or_schedule", "1B3A"): "column schedule title (structural members)",
    ("ST7757 dxf.dxf", "supply_or_schedule", "1C32"): "footing schedule title (structural members)",
    ("ST7757 dxf.dxf", "supply_or_schedule", "1E47"): "simple-beam schedule title (structural members)",
    ("ST7757 dxf.dxf", "supply_or_schedule", "2035"): "continuous-beam schedule title (structural members)",
    ("ST7757 dxf.dxf", "supply_or_schedule", "206B"): "continuous-beam schedule title (structural members)",
    ("ST7757 dxf.dxf", "supply_or_schedule", "272B"): "continuous-beam schedule title (structural members)",
}
SCOPE = ("GF", "1F")          # the task's two openings; 2F is the cross-check row set
DOOR_TRADE = R.DOOR_TRADE_SUPPLY


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def _json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _csv(rel):
    with open(ROOT / rel, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def q(x):
    return None if x is None else format(D(str(x)).normalize(), "f")


def line(idx, lid, want_class=None, want_code=None):
    if lid not in idx:
        raise SystemExit(f"{lid}: not in the candidate index")
    l = idx[lid]
    if want_class and l["class"] != want_class:
        raise SystemExit(f"{lid}: class {l['class']}, expected {want_class}")
    if want_code and not l["item_code"].startswith(want_code):
        raise SystemExit(f"{lid}: item {l['item_code']}, expected {want_code}")
    return l


def state(l):
    return {"line_id": l["line_id"], "item_code": l["item_code"], "element_id": l["element_id"], "unit": l["unit"],
            "class": l["class"], "measured_net": q(l["measured_net"]), "held_low": q(l["held_low"]),
            "held_high": q(l["held_high"])}


def build():
    drawn = _json(IN["DRAWN"])
    idx = {l["line_id"]: l for l in _json(IN["INDEX"])["lines"]}
    cons = {r["opening"]: r for r in _csv(IN["T175_CONS"])}
    net = {r["row_id"]: r for r in _csv(IN["T175_NET"])}
    t128 = {r["ROW"]: r for r in _csv(IN["T128"])}
    t292 = {r["line_id"]: r for r in _csv(IN["T292"])}
    t487 = {r["opening_id"]: r for r in _json(IN["T487"])["lintels"]}
    v12 = _json(IN["V12"])
    v13 = _json(IN["V13"])
    t559 = json.dumps(_json(IN["T559"]))
    t568 = (ROOT / IN["T568"]).read_text(encoding="utf-8")
    t511 = (ROOT / IN["T511"]).read_text(encoding="utf-8")
    tc = drawn["text_census"]
    reviewed = []
    for src, cen in sorted(tc.items()):
        if not isinstance(cen, dict) or "hits" not in cen:
            continue
        for k, hs in sorted(cen["hits"].items()):
            for h in hs:
                why = REVIEWED_HITS.get((src, k, h))
                if why is None:
                    raise SystemExit(f"{src} {k} {h}: an unreviewed text hit: read it before any trade / height decision")
                reviewed.append({"source": src, "pattern": k, "handle": h, "reading": why})
    lift_note = False      # no reviewed hit names the landing-door supply or a landing-door height
    n_texts = sum(c["text_entities"] for c in tc.values() if isinstance(c, dict) and "text_entities" in c)
    blob12 = json.dumps(v12)
    v13_after = {r["line_id"]: r["after"] for r in v13["rows"] if r.get("line_id")}

    rows, fixes, findings = [], [], []
    passage_released = sum(D(str(l["measured_net"])) for l in idx.values()
                           if l["item_code"] == "ARCH.PASSAGE" and l["class"] == "RELEASED")
    for st, o in OPENINGS.items():
        g = drawn["lift_gaps"][st]
        evidence = list(g["evidence"])
        kind = R.kind_of(evidence)
        if kind != "LIFT_LANDING_DOOR":
            raise SystemExit(f"{st}: drawn kind {kind}, not a lift landing door")
        c = cons[o["record"]]
        if c["height_status"] != "HELD" or c["height_m"]:
            raise SystemExit(f"{o['record']}: T-175 height is no longer HELD: re-read before using this table")
        if D(c["width_m"]) != D(str(g["width_m"])) or D(c["wall_t_m"] if c.get("wall_t_m") else "0.2") != D("0.2"):
            raise SystemExit(f"{o['record']}: width differs between the drawing read and T-175")
        lint = t487[o["record"]]
        op = {"evidence": evidence, "width_m": str(g["width_m"]), "height_m": None, "wall_h_m": o["face_h"],
              "lift_package_note": lift_note, "head_established": False,
              "lintel_if_built_m3": q(lint["if_built_at_least_m3"])}
        w = D(str(g["width_m"]))
        fh = D(o["face_h"])
        ev = {"panel_lines_mm_from_shaft_face": [p["offset_from_shaft_face_mm"] for p in g["panel_lines"]],
              "panel_handles": [p["handle"] for p in g["panel_lines"]], "shaft_cross": g["shaft_cross_handles"],
              "width_m": q(g["width_m"]), "wall_t_m": q(g["wall_t_m"])}

        def add(family, lines_, takes, kind_label, note, effect, extra=None):
            ls = [line(idx, x) for x in lines_ if x]
            ln = {"line_id": ls[0]["line_id"] if ls else None, "item_code": ls[0]["item_code"] if ls else None,
                  "takes": takes, "class": ls[0]["class"] if ls else "NONE",
                  "value": q(ls[0]["measured_net"]) if ls and ls[0]["class"] == "HELD" else None,
                  "kind_label": kind_label, "height_used_m": None, "jamb_lm": "0" if family == "SKIRTING" else None}
            verdict, fix = R.audit(op, family, ln)
            exp = R.expected(op, family)
            row = {"storey": st, "opening": f"{o['engine']} ({o['record']})", "family": family,
                   "lines": [state(x) for x in ls], "takes_it": takes, "kind_on_line": kind_label,
                   "expected": {k: exp[k] for k in ("status", "owner_trade", "bound", "value", "why")},
                   "verdict": verdict, "fix": fix, "quantity_effect": effect, "note": note,
                   "in_task_scope": st in SCOPE}
            if extra:
                row.update(extra)
            rows.append(row)
            return row

        # OPENING_COUNT
        pl = line(idx, o["passage"], "RELEASED", "ARCH.PASSAGE")
        if D(str(pl["measured_net"])) != 1:
            raise SystemExit(f"{o['passage']}: passage line is not 1 pcs")
        add("OPENING_COUNT", [o["passage"]], True, "PASSAGE",
            "the engine counts the framed landing door as a doorless passage (T-604 F-T604-1)",
            {"unit": "pcs", "before": "1", "after": "0 (EXCLUDED; the element moves to the landing-door family)"})
        # DOOR_SUPPLY: no candidate line names a landing door; door-trade lines do not carry it (T-568)
        door_lines = [l for l in idx.values() if l["item_code"] in DOOR_TRADE and o["record"] in l["element_id"]]
        if door_lines:
            raise SystemExit(f"{st}: a door-trade line names {o['record']}")
        add("DOOR_SUPPLY", [], False, None,
            "no line holds the landing-door assembly; T-568 lists the three as 'excluded: lift supply' with no printed "
            f"note (text census of the architectural + structural DXF: {n_texts} text entities, Arabic decoded; {len(reviewed)} "
            "hits, all read: the lift BASE label and member schedules, none names the landing door; Q-55 census: no door "
            "schedule; ST p.14 'as per lift manufacturer' prints the PIT depth only and is not extended to the door)",
            {"unit": "nr", "before": "none", "after": "1 beside a HELD-blank line (count DRAWING-CONFIRMED, trade HELD)"})
        # THRESHOLD
        for lid in (o["threshold_arch"], o["strip"]):
            line(idx, lid, "EXCLUDED")
        for lid in o["lift_thr"]:
            line(idx, lid, "RELEASED", "FIN.MARBLE.LIFT_THRESHOLD")
        thr = [line(idx, x) for x in o["lift_thr"]]
        add("THRESHOLD", [o["lift_thr"][0], o["lift_thr"][1], o["threshold_arch"], o["strip"]], True, "LIFT (B6-07)",
            "B6-07 piece RELEASED (depth ASSUMED - OWNER-APPROVED UP-ELEV-005); ARCH.THRESHOLD band and porcelain strip "
            "EXCLUDED inside its footprint; its bed is named 'not stated, no table' (T-511), unchanged"
            if "lift threshold marble bed: not stated" in t511 else "bed record missing",
            {"unit": "m2 / lm", "before": f"{q(thr[0]['measured_net'])} m2 + {q(thr[1]['measured_net'])} lm",
             "after": "unchanged"})
        # SURROUND
        line(idx, o["surround"], "HELD", "FIN.MARBLE.LIFT_SURROUND")
        returns = [l for l in idx.values() if l["item_code"] in ("FIN.PLASTER", "FIN.PAINT")
                   and l["element_id"].startswith(f"{st}-OPENING-") and o["engine"].split()[1] in l["element_id"]]
        if returns:
            raise SystemExit(f"{st}: a plaster / paint return line names the lift opening")
        add("SURROUND", [o["surround"]], True, "LIFT (B6-06)",
            "B6-06 HELD (door height not printed); no plaster / paint 'door jambs and head' line names the opening and no "
            "corner bead line exists: correct by the LIFT ENTRANCE register",
            {"unit": "m2", "before": "HELD blank (register range 2.750 .. 13.980 for the three)", "after": "unchanged"})
        # SKIRTING
        if o["skirting"]:
            sk = line(idx, o["skirting"], "RELEASED", "FIN.SKIRTING")
            if f"{o['engine']}" not in blob12:
                raise SystemExit(f"{st}: no V12 label row for {o['engine']}")
            aft = v13_after.get(o["skirting"])
            add("SKIRTING", [o["skirting"]], True, "LIFT LANDING DOOR (V12 FR-T601-3 label; T-296 deducted 1.00)",
                "the whole 1.00 is deducted, no jamb skirting (LIFT DOOR GAP register); the label was fixed in V12 and, "
                "on 1F, absorbed by the V13 FR-T606-1 row (R1)",
                {"unit": "lm", "before": q(sk["measured_net"]),
                 "after": f"unchanged by T-608 (V13 line state {q(aft['measured_net'])})" if aft else "unchanged"})
        else:
            rows.append({"storey": st, "opening": f"{o['engine']} ({o['record']})", "family": "SKIRTING", "lines": [],
                         "takes_it": True, "kind_on_line": "LIFT (T-443 deduction)", "verdict": "CORRECT", "fix": None,
                         "expected": {"status": "DEDUCT_WHOLE", "owner_trade": "skirting (deduction only)",
                                      "bound": None, "value": q(w), "why": "T-443 deducts OP-002 as a lift opening"},
                         "quantity_effect": {"unit": "lm", "before": "T-443", "after": "unchanged"},
                         "note": "2F lobby skirting: deducted as a lift by T-443 (MERGED 92a38a14)",
                         "in_task_scope": False})
        # BLOCKWORK
        nr = net[o["host_wall"]]
        if nr["s5_status"] != "HELD" or o["record"] not in nr["held_openings"]:
            raise SystemExit(f"{o['host_wall']}: T-175 no longer holds the wall on {o['record']}")
        line(idx, o["block"], "HELD", "MAS.BLOCK")
        his = f"20CM {o['record']} vs his 1.00 x 2.40"
        if his not in t559:
            raise SystemExit(f"T-559 row '{his}' missing")
        add("BLOCKWORK", [o["block"]], True, "LIFT (T-175 SHAFT row; deduction HELD)",
            f"host wall {o['host_wall']} HELD (T-175 net bounds {nr['net_bounds_m2']} m2); his deduction 1.00 x 2.40 = "
            "2.40 m2 (T-559) rests on a height printed nowhere: UNRESOLVED on his side, ours HELD",
            {"unit": "m2", "before": "HELD (deduction 1.00 x h, h not printed)", "after": "unchanged; settles with h"},
            {"his_m2": "2.40", "his_basis": "flat 2.40 m height (printed nowhere; Q-55 refuses it without evidence)"})
        # LINTEL
        ll = line(idx, o["lintel"], "HELD", "STR.CONC.LINTEL")
        add("LINTEL", [o["lintel"]], True, "LIFT (T-453 / T-487 L1 row)",
            f"L1 schedule {lint['schedule_row']} 0.20 x 0.20, if built at least {q(lint['if_built_at_least_m3'])} m3 "
            "(T-487); printed schedule governs over the owner precast lengths (RC LINTEL register ruling); count 0 .. 1 "
            "HELD on the head",
            {"unit": "m3", "before": "HELD blank", "after": "unchanged; 0 .. 1 x "
             f"{q(lint['if_built_at_least_m3'])} m3 beside"})
        # WALL_FACES (plaster + paint of the host room)
        pla, pai = line(idx, o["plaster"], "HELD", "FIN.PLASTER"), line(idx, o["paint"], "HELD", "FIN.PAINT")
        for a in (pla, pai):
            if (a["held_low"], a["held_high"]) != (pla["held_low"], pla["held_high"]):
                raise SystemExit(f"{a['line_id']}: plaster / paint ranges differ")
        width = D(str(pla["held_high"])) - D(str(pla["held_low"]))
        lift_part = w * fh
        others = sum(D(x[1]) * fh for x in o["other_held"])
        if width != lift_part + others:
            raise SystemExit(f"{o['room']}: range width {width} != lift {lift_part} + other held {others}")
        t128r = t128[o["room"]]
        if "lift landing door" not in t128r["OWNER_STATUS"]:
            raise SystemExit(f"{o['room']}: T-128 r3 no longer names the lift landing door")
        t292r = t292[o["plaster"]]
        sole = not o["other_held"]
        add("WALL_FACES", [o["plaster"], o["paint"]], True, "held opening (T-128 r3 opening table)",
            (f"{o['room']} plaster + paint HELD {q(pla['held_low'])} .. {q(pla['held_high'])} m2 each; range width "
             f"{q(width)} = lift 1.00 x 0 .. {o['face_h']}"
             + (" (the ONLY open term: the line is held by the landing-door height alone; W15 / W16 settled by "
                "T-238, T-292 ledger)" if sole else
                f" ({q(lift_part)}) + {', '.join(n for n, _ in o['other_held'])} ({q(others)})")),
            {"unit": "m2", "before": f"HELD {q(pla['held_low'])} .. {q(pla['held_high'])} (x2 lines)",
             "after": "unchanged; with a printed h: " + (f"{q(pla['held_high'])} - 1.00 x h each, RELEASABLE"
                                                         if sole else "still HELD on the other open term")},
            {"sole_blocker": sole, "t292_ledger": f"{t292r['ledger_owner_lo_m2']} .. {t292r['ledger_owner_hi_m2']}"})
        # WET_TRADES
        wet = [l for l in idx.values() if l["item_code"].startswith(("FIN.WP", "FIN.WALL.TILE"))
               and o["engine"].split()[1] in l["element_id"] and l["element_id"].startswith(st)]
        if wet:
            raise SystemExit(f"{st}: a wet-trade line names the lift opening")
        add("WET_TRADES", [], False, None, "both sides dry room / shaft: no wall tile, doorway WP or transition line names "
            "the opening (correct)", {"unit": "-", "before": "none", "after": "none"})

    # fix rows
    pas = [r for r in rows if r["family"] == "OPENING_COUNT"]
    fixes.append({"id": "FR-T608-1", "kind": "SET", "family": "OPENING_COUNT", "item_code": "ARCH.PASSAGE",
                  "lines": [r["lines"][0]["line_id"] for r in pas],
                  "openings": [r["opening"] for r in pas],
                  "before": "RELEASED 1 pcs each", "after": "EXCLUDED (kind LIFT_LANDING_DOOR, R-T608-1)",
                  "family_total": {"unit": "pcs", "before": q(passage_released),
                                   "after": q(passage_released - len(pas)), "delta": f"-{len(pas)}"},
                  "evidence": "DRAWING-CONFIRMED (T608_DRAWN: 4 panel lines at 0 / 50 / 100 / 200 mm from the shaft face "
                              "+ shaft cross, every storey; Checker T-601 13:58 own read GF / 1F)",
                  "scope": "GF OP-011 / 1F OP-007 (task) + 2F OP-002 (F-T604-1, same element on the same drawing)"})
    sup = [r for r in rows if r["family"] == "DOOR_SUPPLY"]
    fixes.append({"id": "FR-T608-2", "kind": "ADD", "family": "DOOR_SUPPLY",
                  "item_code": "proposed DOOR.LIFT_LANDING (code to the Lead / integration)",
                  "lines": [f"new: {r['opening']}" for r in sup], "before": "no line",
                  "after": "class HELD, measured_net blank, count 1 beside per storey (frame + leaves + sill), owner trade "
                           "HELD (no printed note names the lift package); never priced in DOOR.INTERNAL.PVC, never "
                           "EXCLUDED as 'by others' until a note / spec says so",
                  "family_total": {"unit": "nr", "before": "0 (omitted)", "after": "3 HELD (count established)"}})
    if "Lift landing openings | nr | 3 (excluded: lift supply)" in t568:
        findings.append({"id": "F-T608-1", "what": "T-568 type table labels the 3 lift landing openings 'excluded: lift "
                         "supply'; no printed note supports the exclusion: restate as 'trade HELD (no printed note)' in "
                         "the next type / statement table (label only, no quantity)"})
    findings.append({"id": "F-T608-2", "what": "the landing-entrance structural opening height is printed nowhere (text "
                     "census 0 height notations; Q-55 census: only the main entrance height); it alone holds the 1F-13 "
                     "and 2F-01 plaster + paint lines (4 lines, ranges 3.35 m2 wide each) and shares GF-08 with W02; it "
                     "also holds 3 blockwork deductions, 3 lintel counts and the B6-06 surrounds. Source: the lift "
                     "supplier (as the pit depth, CLARIFICATIONS S14) or the architect: proposed for the RFI package "
                     "with the landing-door supply scope (Lead decides; not an owner question: a project fact, ERS s.2.7)"})
    findings.append({"id": "F-T608-3", "what": "Q-55's 2.20 m fallback is scoped to doors of the door trade; extending it "
                     "to a lift entrance (height fixed by the lift product) would be a borrowed value: not applied. If the "
                     "owner wishes a provisional lift-entrance height, that is a new owner rule (none requested here)"})
    in_scope = [r for r in rows if r["in_task_scope"]]
    vt, names = R.tally([(f"{r['storey']} {r['family']}", r["verdict"], r["fix"],
                          "-1" if r["verdict"] == "FIX_ROW" and r["family"] == "OPENING_COUNT" else None)
                         for r in in_scope])
    return {"schema": "URBAN_T608_LIFT_LANDING_SCOPE_V1", "task": "T-608", "rule": R.RULE_ID,
            "governing": R.GOVERNING, "candidate": "ARCH_TAKEOFF_V3.0.58 (V3.0.57 line index, T-507)",
            "inputs": {k: sha(v) for k, v in sorted(IN.items())},
            "drawing": {"text_census": tc, "reviewed_hits": reviewed,
                        "openings": {st: drawn["lift_gaps"][st] for st in OPENINGS}},
            "rows": rows, "fix_rows": fixes, "findings": findings,
            "summary": {"task_rows": len(in_scope), "task_non_correct": names, "passage_pcs_delta_task": q(vt),
                        "passage_pcs_delta_with_2F": f"-{len(pas)}", "released_quantities_changed": 0,
                        "candidate_files_touched": 0}}


def md(data):
    out = ["# T-608 lift landing openings: scope by trade (generated; see T-608_LIFT_LANDING_SCOPE.md)", "",
           "| Storey | Family | Lines (class) | Takes | Kind on line | Verdict | Owner trade | Effect |",
           "|---|---|---|---|---|---|---|---|"]
    for r in data["rows"]:
        ls = "; ".join(f"{x['line_id'][:10]} {x['item_code']} {x['class']}" for x in r["lines"]) or "none"
        e = r["quantity_effect"]
        out.append(f"| {r['storey']} | {r['family']} | {ls} | {'yes' if r['takes_it'] else 'no'} | "
                   f"{r['kind_on_line'] or '-'} | {r['verdict']}{' -> ' + r['fix'] if r['fix'] else ''} | "
                   f"{r['expected']['owner_trade']} | {e['unit']}: {e['before']} -> {e['after']} |")
    out += ["", "## Fix rows", ""] + [f"- {f['id']} {f['kind']} {f['item_code']}: {f['before']} -> {f['after']} "
                                     f"({f['family_total']['unit']} {f['family_total']['before']} -> "
                                     f"{f['family_total']['after']})" for f in data["fix_rows"]]
    out += ["", "## Findings", ""] + [f"- {f['id']}: {f['what']}" for f in data["findings"]]
    return "\n".join(out) + "\n"


def main(argv):
    mode = argv[0] if argv else "--check"
    data = build()
    j = json.dumps(data, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    m = md(data)
    if mode == "--write":
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(j, encoding="utf-8")
        MD_OUT.write_text(m, encoding="utf-8")
        print(f"written {JSON_OUT.name}, {MD_OUT.name}")
        return 0
    same = JSON_OUT.read_text(encoding="utf-8") == j and MD_OUT.read_text(encoding="utf-8") == m
    print("byte-identical" if same else "DIFFERS")
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
