"""T-685 builder: waterproofing HELD / blank / MISSING line census of candidate ARCH_TAKEOFF_V3.0.66 (development
villa), R-T685-1 .. -3. Research only: reads merged, sha256-pinned outputs; writes out/ only; wires nothing.

    python3 -I research/agents_t685/t685_alsenan.py [--check] [--dxf <private P7757.dxf>]

Reads: research/agents_t677/out/LINE_INDEX_V3_0_66.json (the candidate's lines), research/agents_t654/out/
TRIAL_BOQ_R4_T654.json (the committed cause of every HELD line and the merged overlay values), research/agents_t336/
WP_PIECES_T336.csv (the Checker-verified wet-area inventory: its ADD_ROW pieces with no candidate line are MISSING).
The own drawing reads of this run (P7757.dxf and sanitary-7757.pdf, private, not in the repo) are recorded as terms
with handles and lengths relative to the room box only; with --dxf the pantry terms are re-read and asserted.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t685_rules as R  # noqa: E402

CAND = ROOT / "research/agents_t677/out/LINE_INDEX_V3_0_66.json"
TRIAL = ROOT / "research/agents_t654/out/TRIAL_BOQ_R4_T654.json"
PIECES = ROOT / "research/agents_t336/WP_PIECES_T336.csv"
OUT = HERE / "out"
SHA = {"candidate": "02065c41e79dd9df0873cd351e13801c809ca6fa1e62e8a04196af4af13724a7",
       "trial_r4": "9e032726257c4961972bd7fd8de2620a3f7e2adc1f32a78802764a5289e91733",
       "t336_pieces": "8a4f3ab75af755b7146940e3eb5cd374095f1471b2e2d4efffc59caaf93c203f"}

PANTRY = "GF-RC99C2A"     # GF-07 open pantry (T-128 room GF-07; Q-37 A)
PANTRY_UPTURN = "L-8090ff20f2b547d1bc96"

# ---- own DXF read this run: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256
# ab54dd55...). Pantry box, lengths in m relative to its south-west corner (x east, y north). Box: west face AE (layer 1),
# east edge B3 + AD (layer 5, no wall), south face A6, north face 158 / 159; DIMENSION 5E1 4500 (N-S), 5D5 3000 (E-W).
PANTRY_READ = {
    "west": {"wall": [("B0", "0.000", "0.100"), ("AF", "1.100", "2.150"), ("AE", "3.650", "4.500")],
             "window": [("W10 (3CC / 3D3 / 3C9, layer W)", "0.100", "1.100"),
                        ("W09 (3BF / 3C6 / 3BC, layer W)", "2.150", "3.650")]},
    "north": {"wall": [("158", "0.000", "1.659"), ("159", "2.659", "3.000")],
              "door": [("D120 insert 33E, rot 180 (gap between 158 and 159)", "1.659", "2.659")],
              "thickness": ("158 / 15A faces 0.200 apart (15A at y 4.700)", "0.200")},
    "south": {"wall": [("A6", "0.000", "3.000")]},
    "east": {"open": [("B3 layer 5 (counter / box edge, no wall)", "0.000", "4.000"),
                      ("AD layer 5 (no wall)", "4.000", "4.500")]},
    "column": "2FAE S-COL.BON 1.100 x 0.250 at x -0.200 .. 0.900, y 4.450 .. 4.700: 0.050 proud of 158 over 0.900; "
              "the boundary steps round it orthogonally, so the wall run length is unchanged (4.45 + 0.90 + 0.05 + "
              "2.10 + 3.00 = 10.50 = 4.50 + 3.00 + 3.00)",
}
# window sills: W09 / W10 HELD (T-175 HEIGHT_STATUS HELD, designer D-45 'opening heights printed on no sheet')
PANTRY_SILLS = {"W10": None, "W09": None}
# ---- own read of sanitary-7757.pdf (Drive 'Alsenan chalet project'), sheet 1 'GROUND FLOOR DRAINAGE PLAN 1:100',
# image read at 220 / 400 dpi: floor drains (legend 'FD FLOOR DRAIN') printed inside the room box.
FD_READ = {
    "GF-07": (1, "one 'FDø3\"' in the pantry box, piped west through the wall to the CO ø4\" (Q-37 names the same FD); "
                 "'SSø4\" F\\A H/L' is a stack from above at high level: no floor penetration"),
    "GF-02": (1, "dewaneya wash: one 'FDø3\"' between the two basins (basin wastes in red to it)"),
    "GF-03": (1, "dewaneya W.C.: one 'FDø4\"'; the W.C. pan has its own drain line (counted beside, not in the floor)"),
    "GF-05": (1, "driver W.C. (under the kitchen): one 'FDø4\"'; W.C. pan drawn (beside, not counted)"),
    "GF-06": (1, "kitchen: one 'FDø4\"'"),
    "GF-10": (1, "W.C. by the stair (west column of the core, upper cell: W.C. + basin): one 'FDø4\"'"),
    "GF-11": (1, "basin space (west column, lower cell): one 'FDø3\"'"),
    "GF-12": (1, "core wedge W.C.: one 'FDø4\"' (each wedge carries exactly one: the A / B naming does not move it)"),
    "GF-13": (1, "core wedge W.C.: one 'FDø4\"' (each wedge carries exactly one)"),
    "GF-14": (1, "wash lobby, 2 basins: one 'FDø3\"'"),
    "GF-16": (1, "master bath (shower tray, W.C., basin): one 'FDø4\"'"),
    # sheet 2 'FIRST FLOOR DRAINAGE PLAN 1:100' (400 dpi)
    "1F-07": (1, "laundry: one 'FDø4\"' piped to 'SSø4\" F\\A-T/B'"),
    "1F-08": (1, "W.C. (narrow cell east of the laundry): one 'FDø4\"'"),
    "1F-09": (1, "bath by the laundry (shower, W.C., basin): one 'FDø4\"'"),
    "1F-02": (1, "west bath pair: the two cells print 1 ('FDø4\"') and 2 ('FDø3\"' + 'FDø4\"') drains; which cell is "
                 "'upper' / 'lower' is not mapped on this sheet, so each takes AT LEAST 1 (pair AT LEAST 3)"),
    "1F-03": (1, "west bath pair: see 1F-02 (each cell AT LEAST 1; pair AT LEAST 3)"),
    "1F-12": (1, "east bath (shower, W.C., basin): one 'FDø4\"'"),
    # sheet 3 '2nd. FLOOR DRAINAGE PLAN 1:100'
    "2F-02": (1, "W.C. by the stair: one 'FDø4\"' beside 'SSø4\" T/B'"),
}
# room code (T-128) -> candidate element prefix, from the T-336 KEEP rows (single-room keys only)
ROOM_OF = {"GF-RC99C2A": "GF-07", "GF-R8496F0": "GF-02", "GF-RB62B55": "GF-03", "GF-RFAD3C4": "GF-05",
           "GF-RA3AD49": "GF-06", "GF-RDF7D28": "GF-10", "GF-RD36087": "GF-11", "GF-RF38DAF": "GF-12",
           "GF-RB28769": "GF-13", "GF-RDBD4F9": "GF-14", "GF-RD6F891": "GF-16", "1F-R26FA0D": "1F-07",
           "1F-R52AC05": "1F-08", "1F-RED23B8": "1F-09", "1F-R48AA46": "1F-02", "1F-R8BDA49": "1F-03",
           "1F-R48CDA5": "1F-12", "2F-RE83BED": "2F-02"}

# merged Checker-verified values on the three pool-court lines (overlay op 'F package', trial R4 per_line)
MERGED_VALUE = {
    "L-2361d6ec13c952bd2ae3": "T-529 R-WP-APPL-EXPOSED-2b (MERGED 5f775ba6): ledge 0.639573 m2 MEASURED, EXPOSED",
    "L-d7d1bf8c5991ccf69ea2": "T-522 / T-529 (MERGED 4777890b / 5f775ba6): ledge wall-end upturn 0.551614 lm; the "
                              "2.976663 lm glazing transition has no m2 / lm line (beside)",
    "L-1954878bb02c91139e1b": "T-522 (MERGED 4777890b): window run upturn 0.500002 lm, sill '84' printed >= 0.20",
}

DESIGNER = (("doorway WP transition", "Q-35 C / UP-WP-DOOR-001: transition detail printed on no sheet"),
            ("membrane edge on the open side", "Q-37 A fixes the pantry only; edge detail printed on no sheet"),
            ("lift pit walls", "D-43 pit height 'as per lift manufacturer'"),
            ("two schedule tags", "Q-31 C: F10 / F outline 1B1B two readings, designer item"),
            ("PRODUCT_NOT_PRINTED", "UP-WP-MAT-001: product / thickness / laps / coats printed on no sheet"),
            ("governing footing detail not selected", "Q-21 C: founding level selects the p.13 detail (designer)"),
            ("footing tops outside the necks", "Q-21 C: founding level selects the p.13 detail (designer)"),
            ("column-neck faces", "Q-21 C: neck height on the formation (designer)"),
            ("boundary ground beam", "boundary details print no coating (designer item)"),
            ("118 traced ground-beam faces", "beam depth / slab-on-fill not established (designer item)"))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def pantry_upturn():
    rd = PANTRY_READ
    walls = [(f"{side}:{h}", R.D(b) - R.D(a)) for side in ("west", "north", "south") for h, a, b in rd[side]["wall"]]
    # windows sit in the west face gaps: the wall run of the face is its full length, the windows are listed apart
    west_len = R.D("4.500")
    run = [("west face (walls + window bays) 4.500", west_len), ("north face 3.000", R.D("3.000")),
           ("south face 3.000", R.D("3.000"))]
    got = sum(m for _, m in walls) + sum(R.D(b) - R.D(a) for _, a, b in rd["west"]["window"]) + \
        sum(R.D(b) - R.D(a) for _, a, b in rd["north"]["door"])
    if got != sum(m for _, m in run):
        raise R.RuleError(f"pantry face pieces {got} != faces {sum(m for _, m in run)}")
    doors = [(h, R.D(b) - R.D(a)) for h, a, b in rd["north"]["door"]]
    wins = [(h.split()[0], R.D(b) - R.D(a), PANTRY_SILLS[h.split()[0]]) for h, a, b in rd["west"]["window"]]
    u = R.upturn_bound(run, doors, wins)
    u["sources"] = {"walls": walls and [w for w, _ in walls], "doors": [d for d, _ in doors],
                    "windows": [w for w, _, _ in wins], "column": rd["column"],
                    "sills": "W09 / W10 HELD: designer D-45 (opening heights printed on no sheet; T-175)"}
    return u


def pantry_missing():
    rd = PANTRY_READ
    dw = rd["north"]["door"][0]
    width = R.D(dw[2]) - R.D(dw[1])
    th = R.D(rd["north"]["thickness"][1])
    term = R.termination([(h, R.D(b) - R.D(a)) for h, a, b in rd["east"]["open"]], "Q-37 A")
    pen = R.penetrations_at_least(FD_READ["GF-07"][0])
    return [
        {"key": "MISSING:FIN.WP.DOORWAY[m2]/DOOR:D-GF-07-PANTRY/THRESHOLD_FLOOR", "item_code": "FIN.WP.DOORWAY",
         "unit": "m2", "element": "DOOR_THRESHOLD", "class": "MEASURABLE_NOW",
         "cause": "T-336 ADD_ROW (DRAWING-CONFIRMED 0.200, merged c4246877); T-310 left it out ('insert not bound')",
         "fix": {"value": R.S(width * th), "status": "DRAWING-CONFIRMED",
                 "terms": f"door gap {R.S(width)} ({dw[0]}) x wall {R.S(th)} ({rd['north']['thickness'][0]})",
                 "agrees_with": "T-336 0.200000"}},
        {"key": "MISSING:FIN.WP.DOORWAY_TRANSITION_NR[pcs]/DOOR:D-GF-07-PANTRY/TRANSITION",
         "item_code": "FIN.WP.DOORWAY_TRANSITION_NR", "unit": "pcs", "element": "DOOR_THRESHOLD",
         "class": "MEASURABLE_NOW", "cause": "T-336 ADD_ROW 1 (one physical door, Q-35 C); no candidate line",
         "fix": {"value": "1", "status": "DRAWING-CONFIRMED", "terms": f"one door: {dw[0]}",
                 "agrees_with": "T-336 1"}},
        {"key": "MISSING:FIN.WP.DOORWAY_TRANSITION[m2]/DOOR:D-GF-07-PANTRY/TRANSITION",
         "item_code": "FIN.WP.DOORWAY_TRANSITION", "unit": "m2", "element": "DOOR_THRESHOLD", "class": "DESIGNER_ITEM",
         "cause": "Q-35 C / UP-WP-DOOR-001: built by detail, detail printed on no sheet (as the 14 candidate lines)"},
        {"key": "MISSING:FIN.WP.TERMINATION[lm]/GF-07:OPEN_SIDE_DINING/MEMBRANE_EDGE", "item_code":
         "FIN.WP.TERMINATION", "unit": "lm", "element": "WET_MEMBRANE_EDGE", "class": "MEASURABLE_NOW",
         "cause": "T-336 ADD_ROW HELD; Q-37 A (owner) fixes the membrane to the printed box with the open side as a "
                  "threshold line, so the edge length is the drawn open side",
         "fix": {"value": term["value_lm"], "status": "ASSUMED - OWNER-APPROVED", "owner_ref": "Q-37 A",
                 "terms": "east side B3 0.000 .. 4.000 + AD 4.000 .. 4.500, layer 5, no wall drawn; = DIMENSION 5E1 "
                          "4500; the candidate cause text says 4.49 (residual 0.010 m, engine polygon rounding, not "
                          "a drawn length)"}},
        {"key": "MISSING:FIN.WP.PENETRATION[pcs]/GF-07/FLOOR_PENETRATIONS", "item_code": "FIN.WP.PENETRATION",
         "unit": "pcs", "element": "WET_FLOOR_PENETRATION", "class": "OPEN_BOUND",
         "cause": "T-336 ADD_ROW HELD; drainage plan prints the drain: AT LEAST that count (UP-WP-004 1.1.0 'counted "
                  "from the drawings'); other pipes need the wet-room detail",
         "fix": {"at_least": pen["at_least"], "value": None, "status": "OPEN_BOUND", "terms": FD_READ["GF-07"][1]}},
    ]


def classify(l, c):
    lid, code = l["line_id"], l["item_code"]
    cause = (c or {}).get("cause") or ""
    e = {"cause": cause, "source": (c or {}).get("cause_source")}
    if lid in MERGED_VALUE:
        e.update({"class": "MEASURED_NOT_WIRED", "fix": {"value": R.S(c["measured_net"]), "status": "MEASURED",
                                                         "source": MERGED_VALUE[lid], "origin": c.get("origin")},
                  "cause": "candidate line HELD; the merged piece's value lives in the overlay (trial R4 op) only"})
        return e
    if lid == PANTRY_UPTURN:
        u = pantry_upturn()
        e.update({"class": "MEASURABLE_NOW", "fix": {"value": None, "low": u["low_m2"], "high": u["high_m2"],
                                                     "status": "OPEN_BOUND", "detail": u},
                  "note": "the wall heights in the old cause do not enter a 0.20 m upturn; the open side is the "
                          "Q-37 A threshold line (no upturn); the only open term is the two window sills (D-45)"})
        return e
    if "ROOF_NOT_DRAWN_ON_ANY_PLAN" in cause or ("2F top roof" in cause and "Q-34" in cause):
        e.update({"class": "OWNER_OPEN", "owner_ref": "Q-34 PARKED (raised at the 12-13 Nov milestone)"})
        return e
    if code == "FIN.WP.PENETRATION":
        room = ROOM_OF.get(l["element_id"].split(":")[0])
        if room in FD_READ:
            p = R.penetrations_at_least(FD_READ[room][0])
            e.update({"class": "OPEN_BOUND", "fix": {"at_least": p["at_least"], "value": None,
                                                    "status": "OPEN_BOUND", "terms": FD_READ[room][1]},
                      "note": "drain bodies printed on sanitary-7757 sheet 1; what else counts waits on a detail"})
        else:
            e.update({"class": "DESIGNER_ITEM", "designer_ref": "wet-room detail (UP-WP-004)",
                      "note": "not read this run: its drains are printed on sanitary-7757 and give an AT LEAST "
                              "count once the room box is mapped on that sheet (follow-up)"})
        return e
    if "no membrane edge exists there" in cause:
        e.update({"class": "NO_PHYSICAL_ELEMENT", "note": "propose EXCLUDED with evidence T-128 r3 / T-303 f5 (the "
                                                          "face is WALL); not changed here"})
        return e
    for k, ref in DESIGNER:
        if k in cause:
            e.update({"class": "DESIGNER_ITEM", "designer_ref": ref})
            return e
    raise R.RuleError(f"{lid}: no class rule for cause {cause[:80]!r}")


def build(dxf=None):
    for k, p in (("candidate", CAND), ("trial_r4", TRIAL), ("t336_pieces", PIECES)):
        if sha(p) != SHA[k]:
            raise R.RuleError(f"{k} sha256 changed")
    if dxf:
        verify_dxf(dxf)
    cand = json.loads(CAND.read_text())
    trial = json.loads(TRIAL.read_text())
    per = {o["line_id"]: o for o in trial["per_line"] if isinstance(o, dict) and o.get("line_id")}
    lines = [l for l in cand["lines"] if R.in_scope(l["item_code"])]
    held = [l for l in lines if l["class"] == "HELD"]
    entries = []
    for l in sorted(held, key=lambda x: (x["item_code"], x["element_id"])):
        c = per.get(l["line_id"])
        if c is None:
            raise R.RuleError(f"{l['line_id']}: no committed cause in trial R4")
        e = {"key": l["line_id"], "line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"],
             "element_id": l["element_id"], "element": R.element_of(l["item_code"]),
             "held_low": R.S(l["held_low"]) if l["held_low"] is not None else None,
             "held_high": R.S(l["held_high"]) if l["held_high"] is not None else None}
        e.update(classify(l, c))
        entries.append(e)
    # MISSING: T-336 ADD_ROW pieces whose room has no candidate line of that code (pantry door, edge, drains)
    missing = pantry_missing()
    pieces = {r["key"] for r in csv.DictReader(PIECES.open()) if r["action"] == "ADD_ROW"}
    for m in missing:
        if m["key"].removeprefix("MISSING:") not in pieces:
            raise R.RuleError(f"{m['key']}: not a T-336 ADD_ROW")
        if any(l["element_id"].startswith(PANTRY) and l["item_code"] == m["item_code"] for l in lines):
            raise R.RuleError(f"{m['key']}: the candidate already has a pantry line of this code")
    entries += missing
    by_class = R.census(entries, [l["line_id"] for l in held], [m["key"] for m in missing])
    excluded = [{"line_id": l["line_id"], "item_code": l["item_code"], "element_id": l["element_id"],
                 "why": "EXCLUDED in the candidate with evidence (T-310: duplicate door side / window sill above "
                        "the upturn); not HELD, listed for completeness"} for l in lines if l["class"] == "EXCLUDED"]
    tot = R.element_totals(lines)
    fix_lo = {}
    for e in entries:
        f = e.get("fix") or {}
        k = f"{e['element']}|{e['unit']}"
        t = fix_lo.setdefault(k, {"measured": R.D(0), "bound_low": R.D(0), "bound_high": R.D(0), "at_least": 0,
                                  "n": 0})
        if f.get("value") is not None:
            t["measured"] += R.D(f["value"])
            t["n"] += 1
        elif f.get("low") is not None:
            t["bound_low"] += R.D(f["low"])
            t["bound_high"] += R.D(f["high"])
            t["n"] += 1
        elif f.get("at_least"):
            t["at_least"] += f["at_least"]
            t["n"] += 1
    fix_lo = {k: {"measured": R.S(v["measured"]), "bound_low": R.S(v["bound_low"]),
                  "bound_high": R.S(v["bound_high"]), "at_least": v["at_least"], "lines": v["n"]}
              for k, v in sorted(fix_lo.items()) if v["n"]}
    systems = {
        "WET_FLOOR / WET_WALL_UPTURN": R.system_status(None),
        "ROOF_FLAT / ROOF_UPTURN": R.system_status(None),
        "POOL": R.system_status(None),
        "SUBSTRUCTURE": dict(R.system_status(None), note="p.13 footing details print two systems (right 'Two layers "
                             "liquid water proofing', left sheet membrane); which one governs is Q-21 C (founding "
                             "level, designer); no product printed"),
    }
    families = [
        {"family": "B8-04", "item": "Shower floor and tanking", "state": "NO LINE BY RULE",
         "why": "UP-WP-004 1.0.0 (library, in force): a shower takes the wet-room floor + 0.20 upturn, so its floor is "
                "inside FIN.WP.FLOOR; higher shower-wall tanking is 'proposed, not in force' (RULES_INDEX): no line "
                "until an owner rule or a printed detail says so"},
        {"family": "B8-07", "item": "Terraces / balconies / planters", "state": "NO LINE (absence established)",
         "why": "T-486 (MERGED e8ee22f0, ENGINE_RIGHT): the 2F terrace is inside FIN.WP.ROOF, ROOF-430 / strip "
                "carried; no planter is drawn on the plans read"},
    ]
    return {"schema": "URBAN_T685_WP_CENSUS_V1", "task": "T-685", "rules": ["R-T685-1", "R-T685-2", "R-T685-3"],
            "candidate": cand["candidate_version"], "inputs": dict(SHA),
            "filter": "item_code starts with 'FIN.WP.' or 'WP.' (EXT.POOL.WATER_FACE is the pool tile face: not WP)",
            "lines_in_scope": len(lines), "held": len(held), "missing": len(missing), "excluded": len(excluded),
            "count": len(entries), "by_class": by_class, "element_totals": tot, "fix_rows_effect": fix_lo,
            "systems": systems, "families_without_lines": families, "excluded_lines": excluded,
            "entries": entries}


def verify_dxf(path):
    """re-read the pantry handles on the private P7757.dxf and assert the recorded lengths (mm, box-relative)."""
    import ezdxf
    doc = ezdxf.readfile(path)
    g = doc.entitydb.get
    x0, y0 = g("AE").dxf.start.x, g("A6").dxf.start.y
    def span_v(h):
        e = g(h)
        return sorted((round((e.dxf.start.y - y0) / 1000, 3), round((e.dxf.end.y - y0) / 1000, 3)))
    def span_h(h):
        e = g(h)
        return sorted((round((e.dxf.start.x - x0) / 1000, 3), round((e.dxf.end.x - x0) / 1000, 3)))
    rd = PANTRY_READ
    for h, a, b in rd["west"]["wall"]:
        assert span_v(h) == [float(a), float(b)], (h, span_v(h))
    for h, a, b in rd["north"]["wall"] + rd["south"]["wall"]:
        assert span_h(h) == [float(a), float(b)], (h, span_h(h))
    assert span_v("B3") == [0.0, 4.0] and span_v("AD") == [4.0, 4.5]
    assert g("33E").dxf.name == "D120" and round(g("15A").dxf.start.y - g("158").dxf.start.y) == 200
    assert round(g("5E1").get_measurement()) == 4500 and round(g("5D5").get_measurement()) == 3000
    return True


def md(r):
    L = [f"# T-685 waterproofing HELD / MISSING census ({r['candidate']})", "",
         f"Filter: {r['filter']}. {r['lines_in_scope']} lines in scope: {r['held']} HELD + {r['missing']} MISSING "
         f"(merged T-336 rows with no line) = {r['count']} census entries; {r['excluded']} EXCLUDED listed apart. "
         "Research only, nothing wired.", "", "| class | entries |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in r["by_class"].items()]
    L += ["", "Element totals of the candidate (flat and upturn apart; installed and procurement apart):", "",
          "| element | unit | kind | released | n | HELD bounded low .. high (n) | HELD blank | EXCLUDED |",
          "|---|---|---|---|---|---|---|---|"]
    for el, us in sorted(r["element_totals"].items()):
        for u, t in sorted(us.items()):
            b = "-" if t["held_low"] is None else f"{t['held_low']} .. {t['held_high']} ({t['held_bounded_n']})"
            L.append(f"| {el} | {u} | {t['kind']} | {t['released']} | {t['released_n']} | {b} | "
                     f"{t['held_blank_n']} | {t['excluded_n']} |")
    L += ["", "Effect of the fix / merged values on the census entries (not wired):", "",
          "| element / unit | measured | bound low .. high | AT LEAST | entries |", "|---|---|---|---|---|"]
    for k, v in r["fix_rows_effect"].items():
        L.append(f"| {k} | {v['measured']} | {v['bound_low']} .. {v['bound_high']} | {v['at_least']} | {v['lines']} |")
    L += ["", "Membrane systems: " + "; ".join(f"{k}: {v['status']}" for k, v in r["systems"].items()), "",
          "Families with no line: " + "; ".join(f"{f['family']} {f['state']}" for f in r["families_without_lines"]),
          "", "| key | code | element | bound | class | fix |", "|---|---|---|---|---|---|"]
    for e in r["entries"]:
        b = "blank" if e.get("held_high") is None else f"{e['held_low']} .. {e['held_high']}"
        f = e.get("fix") or {}
        fx = (f.get("value") or (f"{f['low']} .. {f['high']}" if f.get("low") else "") or
              (f"AT LEAST {f['at_least']}" if f.get("at_least") else ""))
        L.append(f"| {e['key']} | {e['item_code']} | {e.get('element_id', e['element'])} | {b} | {e['class']} | "
                 f"{fx} |")
    return "\n".join(L) + "\n"


def main(argv):
    dxf = argv[argv.index("--dxf") + 1] if "--dxf" in argv else None
    r = build(dxf)
    js = json.dumps(r, indent=1, sort_keys=True) + "\n"
    mdt = md(r)
    pj, pm = OUT / "T685_WP_CENSUS.json", OUT / "T685_WP_CENSUS.md"
    if "--check" in argv:
        ok = pj.read_text() == js and pm.read_text() == mdt
        print("T-685 outputs", "MATCH" if ok else "DIFFER")
        return 0 if ok else 1
    OUT.mkdir(exist_ok=True)
    pj.write_text(js)
    pm.write_text(mdt)
    print(f"T-685: {r['count']} entries, {r['by_class']}" + (" (DXF re-read AGREE)" if dxf else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
