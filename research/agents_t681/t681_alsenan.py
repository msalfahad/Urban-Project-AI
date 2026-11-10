"""T-681 builder: tiles and adhesive HELD census of candidate ARCH_TAKEOFF_V3.0.65 (development villa), R-T681-1 .. -3.
Research only: reads merged, sha256-pinned outputs; writes out/ only; wires nothing.

    python3 -I research/agents_t681/t681_alsenan.py [--check]

Reads: research/agents_t671/out/LINE_INDEX_V3_0_65.json (the candidate's lines), research/agents_t654/out/
TRIAL_BOQ_R4_T654.json (the committed cause of every HELD line and the WIRING MANIFEST V20 overlay values). The own DXF
read of this run (P7757, private, not in the repo) is recorded as terms with their source text only (shaft-local
stations in metres, no drawing coordinates).
"""
from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t681_rules as R  # noqa: E402

CAND = ROOT / "research/agents_t671/out/LINE_INDEX_V3_0_65.json"
TRIAL = ROOT / "research/agents_t654/out/TRIAL_BOQ_R4_T654.json"
OUT = HERE / "out"
SHA = {"candidate": "e1887c34362b9d2f6558eab7bf825be958ee87206403995abef42be62a335ce1"}  # lines sha 38af7909

# Sources of the measured stretches (R-T681-2). OWN = own read this run of 'P7757_DXF_COMPRESSED.zip' (P7757.dxf sha
# ab54dd55, private copy); INHERITED = a merged, Checker-verified record used as a source reference, never as an
# expected value.
SRC = {
    "shaft_1f": "OWN 1F plan: W inner face solid W 0 .. 1.050 (layer 1), window frame lines (layer W) W 1.050 .. 2.250 "
                "(1.200 = W13), solid again from 2.250; N inner face solid N 0 .. 1.400, window W 1.400 .. 2.400 "
                "(1.000 = W25), solid 2.400 .. 2.500; landing south edge (layer 5) at W 1.200; 12 riser faces "
                "(layer 5) W 4.500 .. 1.200 at 0.300 going",
    "shaft_gf": "OWN GF plan: W inner face window frame lines (layer W) W 1.050 .. 2.250 (1.200, stacked under W13), "
                "riser faces (layer 5) W 3.900 .. 2.100 at 0.300 and nosings (layer 2) to W 1.150: 10 risers to W 1.200",
    "se_chain": "OWN SE elevation dimension chain beside the stair-hall windows, from the '+0.15' mark: 1850 / 2000 / "
                "2500 / 2300 / 2000 -> +2.00 / +4.00 (W01) and +6.50 / +8.80 (W13): AGREE with T-083 (printed "
                "185 / 200 and 250 / 230 / 200); window attribution INHERITED (T-083, T-201 CONSEQUENCES)",
    "w25": "INHERITED T-201 (MERGED, DWF SW elevation vector) W25 +5.50 / +7.00; adverse reading T-680 F-T680-1 "
           "(section A-A raster) +5.6 .. +7.36",
    "levels": "INHERITED T-493 / T-501 (MERGED, Checker re-measure AGREE): MS1-L +1.00 -> +2.667 (10 risers), MS2-L "
              "+5.50 -> +7.516 (12 risers 0.168), MS2-LD west part +7.516, east part (N 1.300 .. 2.500) +7.684",
    "n_wall": "INHERITED T-680 (MERGED): the shaft N wall runs solid from the W25 head to the W27 sill +9.70",
}
R1, R2 = Decimal("1.667") / 10, Decimal("2.016") / 12  # riser heights MS1-L / MS2-L
MEASURE = {
    "L-760bfa8dd00061361695": dict(stretch="MS2-LD.W25 (N 1.400 .. 2.400)", z_min="7.684", z_max="7.684", sill="5.50",
                                   head="7.00", plan_length="1.000", wall_above_head=True,
                                   adverse_head="7.36", srcs=["shaft_1f", "w25", "levels", "n_wall"]),
    "L-33f2018c987f782d1c91": dict(stretch="MS2-LD.W13 (W 1.050 .. 1.200)", z_min="7.516", z_max="7.516",
                                   sill="6.50", head="8.80", plan_length="0.150", srcs=["shaft_1f", "se_chain", "levels"]),
    "L-4ff56def5b73b558afbe": dict(stretch="MS2-L.W2 sloped (W 2.250 .. 1.200)", z_min=str(Decimal("5.50") + 8 * R2),
                                   z_max="7.516", sill="6.50", head="8.80", plan_length="1.050",
                                   srcs=["shaft_1f", "se_chain", "levels"]),
    "L-f45c2e6d46b0cc6a7e53": dict(stretch="MS2-L.W2 zigzag (W 2.250 .. 1.200)", z_min=str(Decimal("5.50") + 8 * R2),
                                   z_max="7.516", sill="6.50", head="8.80", plan_length="1.050",
                                   srcs=["shaft_1f", "se_chain", "levels"]),
    "L-18efa069acded71c81e7": dict(stretch="MS1-L.W2 sloped (W 2.250 .. 1.200)", z_min=str(Decimal("1.00") + 6 * R1),
                                   z_max="2.667", sill="2.00", head="4.00", plan_length="1.050",
                                   srcs=["shaft_gf", "se_chain", "levels"], boundary=True),
    "L-76748b7b62ab2d52b4e2": dict(stretch="MS1-L.W2 zigzag (W 2.250 .. 1.200)", z_min=str(Decimal("1.00") + 6 * R1),
                                   z_max="2.667", sill="2.00", head="4.00", plan_length="1.050",
                                   srcs=["shaft_gf", "se_chain", "levels"], boundary=True),
}
WIRING = {"L-6ff876aefb5a3631565c": "FR-T601-2 (T-601 / T-604 manifest V12, merged; restated in manifest V20 / trial "
                                    "R4 as EXCLUDED NOT_APPLICABLE, Q-06 A wet side): the candidate still carries HELD"}
SKIRT_SUB = {
    "L-47fa825d197d32754240": "Q-S6-4 stair-hall finish scope (0.200 lm GF-ST-CN north face unread, T-574)",
    "L-4e7d3bef5e6ac89252ff": "RFI a: divider band skirting printed on no sheet",
    "L-d589222eace010fefa69": "RFI c: back-lobby west face skirting printed on no sheet",
    "L-5273c35e05acc8ebeb59": "door 3FF in the N face below the +3.50 landing: its floor and head are printed nowhere "
                              "(the landing datum needs the head below the landing soffit)",
}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def classify(l, c, overlay):
    lid, code = l["line_id"], l["item_code"]
    cause = (c or {}).get("cause") or "no committed cause in trial R4"
    e = {"cause": cause, "source": (c or {}).get("cause_source", ""), "wires_in": "tiles Gate B row (owner order "
         "step 5, to be rowed by the Lead)"}
    if lid in MEASURE:
        m = dict(MEASURE[lid])
        srcs = m.pop("srcs")
        adv, bnd = m.pop("adverse_head", None), m.pop("boundary", False)
        stretch = m.pop("stretch")
        r = R.skirting_at_opening(**m)
        fix = {"stretch": stretch, "terms": {k: m[k] for k in ("z_min", "z_max", "sill", "head", "plan_length")},
               "sources": [SRC[s] for s in srcs], **r,
               "status": "DRAWING-CONFIRMED" if r["state"] != "HELD" else "HELD", "wired": False}
        if adv:
            ra = R.skirting_at_opening(**{**m, "head": adv})
            fix["adverse"] = {"head": adv, "state": ra["state"], "length_lm": ra["length_lm"]}
        if bnd:
            fix["boundary_note"] = ("the tread beside the sill sits at the sill level (+2.000 vs +2.00, within "
                                    f"{R.TOL} m): the opening starts at the junction; a drawn sill above the tread "
                                    "would make this stretch HELD (band clearance), never FULL")
        e.update({"class": "MEASURABLE_NOW", "fix": fix})
        if code.startswith("FIN.STAIR"):
            e["also"] = ("ORR-007 (payable form) no longer matters for this piece: both forms are NOT_APPLICABLE")
    elif lid in WIRING:
        e.update({"class": "WIRING_GAP", "also": WIRING[lid]})
    elif code.startswith("FIN.FLOOR.BED"):
        e.update({"class": "OPEN_BOUND", "also": "owner thickness band Q-45 (3-4 cm floors / 4-6 cm wet rooms) on a "
                  "released area; settles only with a printed floor build-up (D-39 family) or an owner choice"})
    elif code == "EXT.FLOOR.OUTDOOR":
        e.update({"class": "OWNER_OPEN", "owner_ref": "OD-1 (OWNER_RULE_OUTDOOR_FLOORS_2026-10-21)",
                  "also": "area DRAWING-CONFIRMED; interlock or ceramic not decided: adhesive / bed HELD"})
    elif code == "FIN.FLOOR.FINISH_HELD":
        e.update({"class": "DESIGNER_ITEM", "also": "floor material (porcelain or landing marble) printed on no "
                  "sheet; no finishes schedule"})
    elif code == "FIN.WALL.TILE" and "annex height" in cause:
        e.update({"class": "OWNER_OPEN", "owner_ref": "Q-54 B HOLD", "also": "annex +4.30 datum (D-06 / D-17 / D-39)"})
    elif code == "FIN.WALL.TILE":
        e.update({"class": "DESIGNER_ITEM", "also": "stair-core wet-room floor +0.30 / +1.00 not drawn (T-088, "
                  "T-173 C-SH-2): the tile band has no start level"})
    elif code.startswith("FIN.STAIR.SKIRTING"):
        e.update({"class": "OWNER_OPEN", "owner_ref": "ORR-007 (payable form zigzag / sloped)",
                  "also": "one blank line per form, never additive"})
    elif lid in SKIRT_SUB:
        e.update({"class": "DESIGNER_ITEM", "also": SKIRT_SUB[lid]})
    else:
        raise R.RuleError(f"{lid}: no class rule for {code} cause {cause[:80]!r}")
    if overlay is not None and (overlay.get("held_low"), overlay.get("held_high"), overlay["class"]) != \
            (l["held_low"], l["held_high"], l["class"]):
        e["overlay_v20"] = {"class": overlay["class"], "low": R.S(overlay.get("held_low")),
                            "high": R.S(overlay.get("held_high"))}
    return e


def materials(cand):
    """R-T681-3 beside the m2: adhesive by code (size not sourced), bed cement / sand; RELEASED + HELD bounded."""
    tile = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.WALL.TILE", "EXT.FLOOR.PORCELAIN")
    out, rows = {}, []
    keys = []
    for code in tile + ("FIN.FLOOR.BED.DRY", "FIN.FLOOR.BED.WET", "FIN.FLOOR.FINISH_HELD", "EXT.FLOOR.OUTDOOR",
                        "FIN.SKIRTING"):
        units = sorted({l["unit"] for l in cand["lines"] if l["item_code"] == code})
        keys += [(code, u) for u in units]
    for code, unit in keys:  # never sum across units (a bed has an m2 area line and an m3 volume line)
        ls = [l for l in cand["lines"] if l["item_code"] == code and l["unit"] == unit
              and l["class"] in ("RELEASED", "HELD")]
        rel = sum((R.D(l["measured_net"]) for l in ls if l["class"] == "RELEASED"), Decimal(0))
        hl = [l for l in ls if l["class"] == "HELD" and l["held_low"] is not None]
        lo = rel + sum((R.D(l["held_low"]) for l in hl), Decimal(0))
        hi = rel + sum((R.D(l["held_high"]) for l in hl), Decimal(0))
        blank = sum(1 for l in ls if l["class"] == "HELD" and l["held_low"] is None)
        t = {"unit": unit, "released_lines": sum(1 for l in ls if l["class"] == "RELEASED"), "released": R.S(rel),
             "held_bounded": len(hl), "held_blank": blank, "total_low": R.S(lo), "total_high": R.S(hi)}
        if code in tile:
            a = R.adhesive(lo, hi, None)
            rows.append(a)
            t["adhesive"] = a
        elif code.startswith("FIN.FLOOR.BED") and unit == "m3":
            t["bed_1_4"] = R.bed_materials(lo, hi) if not blank else {"status": "HELD", "cement_bags": None,
                                                                      "sand_m3": None}
        elif code.startswith("FIN.FLOOR.BED"):
            t["materials"] = {"status": "AREA", "why": "bed area (m2); its cement / sand ride on the m3 line"}
        else:
            t["materials"] = {"status": "HELD", "why": {
                "FIN.FLOOR.FINISH_HELD": "material not named (porcelain or marble)",
                "EXT.FLOOR.OUTDOOR": "OD-1 open: interlock (no adhesive) or ceramic",
                "FIN.SKIRTING": "no owner coverage rule per lm for skirting adhesive"}[code]}
        out[f"{code} [{unit}]"] = t
    out["ADHESIVE, the four tile codes as one purchasing group (group not decided: per code shown above)"] = \
        R.group_bags(rows)
    return out


def build():
    if sha(CAND) != SHA["candidate"]:
        raise R.RuleError("candidate line index sha256 changed")
    cand = json.loads(CAND.read_text())
    trial = json.loads(TRIAL.read_text())
    per = {o["line_id"]: o for o in trial["per_line"] if isinstance(o, dict) and o.get("line_id")}
    held = [l for l in cand["lines"] if l["class"] == "HELD" and R.code_in_scope(l["item_code"])]
    entries = []
    for l in sorted(held, key=lambda x: (x["item_code"], x["element_id"])):
        o = per.get(l["line_id"])
        e = {"line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"], "element_id": l["element_id"],
             "held_low": R.S(l["held_low"]), "held_high": R.S(l["held_high"])}
        e.update(classify(l, o if o and o.get("cause") else None, o))
        entries.append(e)
    tot = R.census(entries, [l["line_id"] for l in held])
    cids = {l["line_id"] for l in cand["lines"]}
    overlay_only = [{"line_id": o["line_id"], "item_code": o["item_code"], "class": o["class"],
                     "low": R.S(o.get("held_low")), "high": R.S(o.get("held_high")), "net": R.S(o.get("measured_net"))}
                    for o in trial["per_line"] if o.get("item_code") in R.SCOPE and o["line_id"] not in cids]
    fixes = [{"line_id": e["line_id"], "item_code": e["item_code"], "before": "blank", **e["fix"]}
             for e in entries if e.get("fix")]
    by_class = {}
    for e in entries:
        by_class[e["class"]] = by_class.get(e["class"], 0) + 1
    return {"schema": "URBAN_T681_TILES_CENSUS_V1", "task": "T-681", "rules": ["R-T681-1", "R-T681-2", "R-T681-3"],
            "candidate": cand["candidate_version"], "filter": "class HELD and item_code in " + ", ".join(R.SCOPE),
            "inputs": {"candidate_line_index": SHA["candidate"], "trial_r4": sha(TRIAL)},
            "count": len(entries), "by_class": dict(sorted(by_class.items())), "totals": tot,
            "materials": materials(cand), "fix_rows": fixes, "overlay_only_lines_v20": overlay_only,
            "not_in_scope": "marble (FIN.MARBLE.*: stair / threshold / lift, other rows), roof screed, WP screeds; "
                            "wet-wall spatter dash and levelling render are plaster-scope coats (T-676 / T-364)",
            "entries": entries}


def md(r):
    L = ["# T-681 tiles and adhesive HELD census (V3.0.65)", "",
         f"Candidate {r['candidate']}; {r['count']} HELD lines = filter '{r['filter']}'. Research only, nothing wired.",
         "", "| class | lines |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in r["by_class"].items()]
    L += ["", "| code [unit] | lines | bounded low .. high | blank | by class |", "|---|---|---|---|---|"]
    for k, t in r["totals"].items():
        b = "none bounded" if t["low"] is None else f"{t['low']} .. {t['high']} ({t['bounded']})"
        L.append(f"| {k} | {t['lines']} | {b} | {t['blank']} | "
                 + ", ".join(f"{a} {n}" for a, n in t["by_class"].items()) + " |")
    L += ["", "Materials beside the quantity (released + HELD bounded; blank lines counted, never 0):", "",
          "| code | unit | released (lines) | held bounded / blank | total low .. high | material |",
          "|---|---|---|---|---|---|"]
    for k, t in r["materials"].items():
        if "unit" not in t:
            L.append(f"| {k} | bags | | | | {t['status']}: exact {t['exact_low']} .. {t['exact_high']} -> "
                     f"{t['bags_low']} .. {t['bags_high']} bags (one ceil) |")
            continue
        if "adhesive" in t:
            a = t["adhesive"]
            mat = f"adhesive {a['status']} {a['bags'][0]} .. {a['bags'][1]} bags ({a['why']})"
        elif "bed_1_4" in t:
            b = t["bed_1_4"]
            mat = f"1:4 {b['status']}: cement {b['cement_bags'][0]} .. {b['cement_bags'][1]} bags, sand " \
                  f"{b['sand_m3'][0]} .. {b['sand_m3'][1]} m3 (waste separate)"
        else:
            mat = f"{t['materials']['status']}: {t['materials']['why']}"
        L.append(f"| {k} | {t['unit']} | {t['released']} ({t['released_lines']}) | {t['held_bounded']} / "
                 f"{t['held_blank']} | {t['total_low']} .. {t['total_high']} | {mat} |")
    L += ["", "MEASURABLE NOW (R-T681-2):"]
    for f in r["fix_rows"]:
        s = f"- {f['line_id']} {f['stretch']}: blank -> {f['state']} {f['length_lm']} lm ({f['status']}); {f['why']}"
        if f.get("adverse"):
            s += f"; adverse head {f['adverse']['head']}: {f['adverse']['state']} {f['adverse']['length_lm']}"
        L.append(s)
    L += ["", f"Overlay-only lines in manifest V20 (not candidate lines, not in the census): "
          f"{len(r['overlay_only_lines_v20'])}", "", "| line | code | element | bound | class | ref |",
          "|---|---|---|---|---|---|"]
    for e in r["entries"]:
        b = "blank" if e["held_low"] is None else f"{e['held_low']} .. {e['held_high']}"
        L.append(f"| {e['line_id']} | {e['item_code']} | {e['element_id']} | {b} | {e['class']} | "
                 f"{e.get('owner_ref', '')} |")
    return "\n".join(L) + "\n"


def main(argv):
    r = build()
    js = json.dumps(r, indent=1, sort_keys=True) + "\n"
    mdt = md(r)
    pj, pm = OUT / "T681_TILES_CENSUS.json", OUT / "T681_TILES_CENSUS.md"
    if "--check" in argv:
        ok = pj.read_text() == js and pm.read_text() == mdt
        print("T-681 outputs", "MATCH" if ok else "DIFFER")
        return 0 if ok else 1
    OUT.mkdir(exist_ok=True)
    pj.write_text(js)
    pm.write_text(mdt)
    print(f"T-681: {r['count']} lines, {r['by_class']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
