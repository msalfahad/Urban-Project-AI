"""T-676 builder: the plaster / render / spatter / paint HELD-line census of candidate ARCH_TAKEOFF_V3.0.64 (development
villa), R-T676-1 .. -3. Research only: reads merged, sha256-pinned outputs; writes out/ only; wires nothing.

    python3 -I research/agents_t676/t676_alsenan.py [--check]

Reads: research/agents_t668/out/LINE_INDEX_V3_0_64.json (the candidate's lines), research/agents_t654/out/
TRIAL_BOQ_R4_T654.json (the committed cause of every HELD line), research/agents_t489/out/PLASTER_MIX_T489.csv (the
coat class / layers / thicknesses of each plaster host). The own DXF read of this run (P7757, private, not in the repo)
is recorded as terms with their source text only.
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
import t676_rules as R  # noqa: E402

CAND = ROOT / "research/agents_t668/out/LINE_INDEX_V3_0_64.json"
TRIAL = ROOT / "research/agents_t654/out/TRIAL_BOQ_R4_T654.json"
MIXCSV = ROOT / "research/agents_t489/out/PLASTER_MIX_T489.csv"
OUT = HERE / "out"
SHA = {"candidate": "4403697305f428b11c754e95af5258207d7ce3663fe7de1d687b5e2e5d879548"}  # file sha256 (lines sha d227173a)

# merged overlay bounds for candidate-blank lines (T-640 FR-T640-28 / -29, merged 36f53264; restated in trial R4)
MERGED_BOUND = {
    "L-418121a4b223cb4e8646": ("44.512", "49.872", "overlay FR-T640-29 (T-640, merged 36f53264)"),
    "L-5a7a5c6f070ec7142ca5": ("42.722", "47.932", "overlay FR-T640-28 (T-640, merged 36f53264)"),
}

# R-T676-2 fix row, own DXF read this run (P7757, GF plan frame, mm): block D120 (1000 mm leaf) inserted at the SW
# facade wall; wall faces 200 mm apart (two lines y 0 / -200 relative to the insert), the wall lines stop at x 0 and
# resume at x 1000 (clear opening 1000), run -468 .. 2632 = 3100 mm = facade SW-1 (T-159 3.1000, OP-009 1.000): AGREE
# with T-108 (0.20) / T-194 (1.0) / T-313 (0.20 x 1.00). The GF plan carries ONE D200 (2000 mm leaf) door = the printed
# main entrance 2.00 x 2.50 (Q-55 C; D-GF-07 / OP-021, T-201 / T-237); OP-009 is a 1.00 m door, so it is NOT the main
# entrance and no sheet prints its height (Q-55 record, T-175 D-GF-01 2.200 ASSUMED, T-313): Q-55 C fallback 2.20 m.
FIX_OP009 = {
    "status": "ASSUMED - OWNER-APPROVED", "owner_ref": "Q-55 C", "wired": False,
    "terms": {"thickness": ["0.20", "own DXF read P7757 GF: SW-1 wall faces 200 mm apart (T-108 0.20 AGREE)"],
              "height": ["2.20", "Q-55 C fallback (no sheet prints D-GF-01; not the 2.00 x 2.50 main entrance)"],
              "width": ["1.00", "own DXF read P7757 GF: wall stops 0 / 1000 at the D120 insert (T-194 1.0 AGREE)"]},
    "value": "1.08",
    "note": "2 x 0.20 x 2.20 + 0.20 x 1.00 = 0.88 + 0.20 = 1.08 m2; the bound 1.08 .. 1.20 closes to its low end: the "
            "high end assumed the main-entrance height 2.50 for a door that is not the main entrance",
}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def classify(l, c):
    """-> dict(class, queued_row, designer_ref, owner_ref, cause, source[, fix, merged_bound])."""
    lid, code, el = l["line_id"], l["item_code"], l["element_id"]
    cause, src, ids = c["cause"], c["cause_source"], c.get("cause_ids") or []
    e = {"cause": cause, "source": src, "queued_row": "none"}
    if code.startswith("EXT.FENCE."):
        e.update({"class": "OWNER_OPEN", "owner_ref": "OWNER_NOTES_SIGMA_2026-10-21 item 3",
                  "also": "D-62 (no finishes schedule); face itself HELD (T-646)"})
    elif code == "FIN.EXT.FINISH" or (code == "ARCH.FACADE" and "plinth" not in el):
        e.update({"class": "QUEUED_ROW", "queued_row": "T-314",
                  "also": "measured face by face in T-305 / T-337 / T-348 r2 / T-567; spatter dash under it: T-364"})
    elif code == "ARCH.FACADE":
        e.update({"class": "DESIGNER_ITEM", "designer_ref": "D-62", "queued_row": "T-314",
                  "also": "external ground level not printed; T-314 carries plinth faces only after T-311 names "
                          "their owner trade"})
    elif lid == "L-f4175f9915208dc5f9f7":
        e.update({"class": "MEASURABLE_NOW", "fix": FIX_OP009,
                  "also": "candidate cause JAMB_HEIGHT_CLASS_PENDING closed by the drawing (one D200 main entrance)"})
    elif "annex height" in cause:
        e.update({"class": "OWNER_DECISION_HOLD", "owner_ref": "Q-54 B", "also": "D-06 / D-17 / D-39"})
    elif "HELD on the roof build-up" in cause:
        e.update({"class": "DESIGNER_ITEM", "designer_ref": "D-39",
                  "also": "value at the drawn-section scenario, ESTIMATED (T-563 V3.0.61)"})
    elif "opening heights printed on no sheet" in cause:
        e.update({"class": "DESIGNER_ITEM", "designer_ref": "D-45", "also": "T-561 / T-617 head bounds"})
    elif "stair-shaft" in cause or "shaft faces" in cause:
        e.update({"class": "OPEN_BOUND", "also": "Q-72 full exposed height; open: floor build-up b 0 .. 0.10, "
                                                 "winder / beam-end contacts, W27 / window heads (T-173)"})
        if lid in MERGED_BOUND:
            lo, hi, s = MERGED_BOUND[lid]
            e["merged_bound"] = {"low": lo, "high": hi, "source": s,
                                 "note": "the candidate line is BLANK; the bound lives in the merged overlay only"}
    elif "floor level +0.30 or +1.00 not drawn" in cause:
        e.update({"class": "PRINTED_VALUE_GAP", "also": "T-088 / T-173 C-SH-2: no floor edge or level drawn"})
    elif "A-GF-01" in cause:
        e.update({"class": "DESIGNER_ITEM", "designer_ref": "D-45",
                  "also": "plan terms 1.000 x 0.150 DRAWING-CONFIRMED (T-648 own read); spring / rise not printed"})
    elif "A-1F-01" in cause:
        e.update({"class": "DESIGNER_ITEM", "designer_ref": "D-45",
                  "also": "CORRECTION of the stale cause: the 1F plan DOES draw it (own DXF read P7757, 1F frame: the "
                          "one 1F arch120 block, 1000 x 150; wall faces 150 mm apart stop at -500 / +500 of the "
                          "insert = 1000 clear; T-175 1F-W16 width 1.000 / wall 0.150 DRAWING-CONFIRMED: AGREE); "
                          "only the arch height / rise is printed nowhere (same as A-GF-01): stays HELD"})
    elif "D-GF-15" in cause:
        e.update({"class": "DESIGNER_ITEM", "designer_ref": "D-53", "also": "T-313 UNRESOLVED gate width / wall"})
    else:
        raise R.RuleError(f"{lid}: no class rule for cause {cause[:80]!r}")
    return e


def layers_by_host():
    out = {}
    thick = {}
    for a in csv.DictReader(MIXCSV.open()):
        out.setdefault(a["line_id"], {"class": a["class"], "layers": []})["layers"].append(a["layer"])
        if a["thickness_m"] and a["layer"] not in thick:
            thick[a["layer"]] = (a["thickness_m"], a["thickness_kind"])
    return out, thick


def materials(e, host, thick):
    """R-T676-3 per plaster host; paint codes carry none."""
    code = e["item_code"]
    if code not in ("FIN.PLASTER", "FIN.EXT.FINISH", "EXT.FENCE.PLASTER"):
        return None
    lo, hi = e.get("held_low"), e.get("held_high")
    if e.get("fix"):
        lo = hi = e["fix"]["value"]
    rows = {}
    cls = host["class"] if host else None
    if cls == "DRY_WALL_PLASTER":
        t, k = thick["WALL_PLASTER"]
        rows["WALL_PLASTER (1:4)"] = R.coat_materials(lo, hi, "WALL_PLASTER", t, k)
    elif cls == "WET_WALL_RENDER":
        t, k = thick["LEVELLING_RENDER"]
        rows["LEVELLING_RENDER (1:4)"] = R.coat_materials(lo, hi, "LEVELLING_RENDER", t, k)
    else:
        rows["ALL COATS"] = {"status": "HELD", "cement_bags": None, "sand_m3": None,
                             "why": ("coat class not established (T-489 CLASS_NOT_ESTABLISHED)" if cls else
                                     "no T-489 host row: the face rows come with T-314"),
                             "water": "HELD (no water : cement ratio printed or owner-given)"}
    rows["BOND_COAT spatter dash (1:2)"] = {"status": "HELD", "cement_bags": None, "sand_m3": None,
                                            "why": "spatter dash has no candidate line (MISSING category, T-364) and "
                                                   "no thickness from the project, the owner or the rules",
                                            "water": "HELD"}
    return {"coat_class": cls, "rows": rows}


def build():
    if sha(CAND) != SHA["candidate"]:
        raise R.RuleError("candidate line index sha256 changed")
    cand = json.loads(CAND.read_text())
    trial = json.loads(TRIAL.read_text())
    causes = {o["line_id"]: o for o in trial["per_line"] if isinstance(o, dict) and o.get("line_id")}
    host, thick = layers_by_host()
    held = [l for l in cand["lines"] if l["class"] == "HELD" and R.code_in_scope(l["item_code"])]
    entries = []
    for l in sorted(held, key=lambda x: (x["item_code"], x["element_id"])):
        c = causes.get(l["line_id"])
        if c is None:
            raise R.RuleError(f"{l['line_id']}: no committed cause in trial R4")
        e = {"line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"], "element_id": l["element_id"],
             "held_low": None if l["held_low"] is None else str(l["held_low"]),
             "held_high": None if l["held_high"] is None else str(l["held_high"]), "measured_net": None}
        e.update(classify(l, c))
        e["materials"] = materials(e, host.get(l["line_id"]), thick)
        entries.append(e)
    tot = R.census(entries, [l["line_id"] for l in held])
    mat = {}
    for e in entries:
        m = e["materials"]
        if not m:
            continue
        for layer, r in m["rows"].items():
            k = f"{e['item_code']}|{layer}"
            t = mat.setdefault(k, {"hosts": 0, "bounded": 0, "held_blank": 0, "cement_bags": [0, 0], "sand_m3": [0, 0]})
            t["hosts"] += 1
            if r.get("cement_bags"):
                t["bounded"] += 1
                for i in (0, 1):
                    t["cement_bags"][i] = R.S(R.q(R.D(t["cement_bags"][i]) + R.D(r["cement_bags"][i])))
                    t["sand_m3"][i] = R.S(R.q(R.D(t["sand_m3"][i]) + R.D(r["sand_m3"][i])))
            else:
                t["held_blank"] += 1
    for t in mat.values():
        if not t["bounded"]:
            t["cement_bags"] = t["sand_m3"] = None
    merged_only = [{"line_id": e["line_id"], **e["merged_bound"]} for e in entries if e.get("merged_bound")]
    return {"schema": "URBAN_T676_PLASTER_PAINT_CENSUS_V1", "task": "T-676", "rules": ["R-T676-1", "R-T676-2",
            "R-T676-3"], "candidate": cand["candidate_version"],
            "inputs": {"candidate_line_index": SHA["candidate"], "trial_r4": sha(TRIAL), "t489_mix_csv": sha(MIXCSV)},
            "thickness_from_t489": {k: list(v) for k, v in sorted(thick.items())},
            "conversion": "Q-53 C dry 1.33, cement 1,440 kg/m3, 50 kg bag; mix Q-79 (plaster 1:4, render 1:4, "
                          "spatter 1:2); thickness PLASTER_MATERIALS_TABLE_V1 (KSE 'Bayt Al-Omr' 2023, ESTIMATED)",
            "count": len(entries), "by_class": _count(entries, "class"), "by_queued_row": _count(entries, "queued_row"),
            "totals_m2": tot, "merged_bound_only": merged_only, "materials_totals": dict(sorted(mat.items())),
            "fix_rows": [{"line_id": e["line_id"], "element_id": e["element_id"], "before": [e["held_low"],
                          e["held_high"]], **e["fix"]} for e in entries if e.get("fix")],
            "entries": entries}


def _count(entries, k):
    out = {}
    for e in entries:
        out[e[k]] = out.get(e[k], 0) + 1
    return dict(sorted(out.items()))


def md(r):
    L = ["# T-676 plaster / render / spatter / paint HELD census (V3.0.64)", "",
         f"Candidate {r['candidate']}; {r['count']} HELD lines in scope (= every HELD line of the scope codes). "
         "Research only, nothing wired.", "", "| class | lines |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in r["by_class"].items()]
    L += ["", "| code / unit | lines | bounded sum low .. high | blank | by class |", "|---|---|---|---|---|"]
    for k, t in r["totals_m2"].items():
        b = "none bounded (HELD)" if t["low"] is None else f"{t['low']} .. {t['high']} ({t['bounded']})"
        L.append(f"| {k} | {t['lines']} | {b} | {t['blank']} | "
                 + ", ".join(f"{a} {b}" for a, b in t["by_class"].items()) + " |")
    L += ["", "Merged-overlay bounds on candidate-blank lines (not in the sums above):"]
    L += [f"- {m['line_id']}: {m['low']} .. {m['high']} m2 ({m['source']})" for m in r["merged_bound_only"]]
    L += ["", "Coat materials on the HELD hosts (" + r["conversion"] + "):", "",
          "| code | coat | hosts | bounded | blank | cement bags | sand m3 |", "|---|---|---|---|---|---|---|"]
    for k, t in r["materials_totals"].items():
        code, layer = k.split("|")
        cb = "HELD" if t["cement_bags"] is None else f"{t['cement_bags'][0]} .. {t['cement_bags'][1]}"
        sm = "HELD" if t["sand_m3"] is None else f"{t['sand_m3'][0]} .. {t['sand_m3'][1]}"
        L.append(f"| {code} | {layer} | {t['hosts']} | {t['bounded']} | {t['held_blank']} | {cb} | {sm} |")
    L += ["", "Water: HELD on every coat (no water : cement ratio printed or owner-given).", "", "Fix rows:"]
    for f in r["fix_rows"]:
        L.append(f"- {f['line_id']} {f['element_id']}: {f['before'][0]} .. {f['before'][1]} -> {f['value']} m2 "
                 f"{f['status']} ({f['owner_ref']}); {f['note']}")
    L += ["", "| line | code | element | bound | class | ref | queued |", "|---|---|---|---|---|---|---|"]
    for e in r["entries"]:
        b = "blank" if e["held_low"] is None else f"{e['held_low']} .. {e['held_high']}"
        ref = e.get("designer_ref") or e.get("owner_ref") or ""
        L.append(f"| {e['line_id']} | {e['item_code']} | {e['element_id']} | {b} | {e['class']} | {ref} | "
                 f"{e['queued_row']} |")
    return "\n".join(L) + "\n"


def main(argv):
    r = build()
    js = json.dumps(r, indent=1, sort_keys=True) + "\n"
    mdt = md(r)
    pj, pm = OUT / "T676_PLASTER_PAINT_CENSUS.json", OUT / "T676_PLASTER_PAINT_CENSUS.md"
    if "--check" in argv:
        ok = pj.read_text() == js and pm.read_text() == mdt
        print("T-676 outputs", "MATCH" if ok else "DIFFER")
        return 0 if ok else 1
    OUT.mkdir(exist_ok=True)
    pj.write_text(js)
    pm.write_text(mdt)
    print(f"T-676: {r['count']} lines, {r['by_class']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
