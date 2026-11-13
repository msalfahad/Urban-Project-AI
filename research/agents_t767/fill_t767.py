"""T-767 (F-08, lane S): fix-row set for the WATERPROOFING lines without a figure on ARCH_TAKEOFF_V3.0.78.

DELIVERY MODE (owner 2026-11-13): every line gets a figure by the fallback order with its label
MEASURED / DRAWING-READ / DEFAULT / ESTIMATE / SAFETY and a one-line basis. Nothing is wired here: Worker 3 wires the
set (T-750 / T-770). Inputs are merged repository files only (no drawing, no client data):

  line index   research/agents_t738/out/LINE_INDEX_V3_0_78.json (candidate of record)
  fixtures     research/agents_t743/out/T743_ALSENAN_COUNTS.json (sanitary census, MEASURED counts per engine room)
  footings     research/agents_t233/ALSENAN_FOOTING_INPUT.json (26 outlines + printed schedule L x W x H)
  buried faces research/agents_t263/LEDGER_T263.csv (footing tops, necks, boundary, straps), research/agents_t276/LEDGER_T276.csv
               (ground-beam faces), research/agents_t174/T174_STRAPS.json (strap B x D x run)
  necks        neck concrete held ranges of the same index (height = m3 / schedule section)

Lines another READY set already fills (T-764: L-636fd3ff, L-aac1f35e, L-90b40877) are left to it.

    python3 -I research/agents_t767/fill_t767.py [--check]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
IDX = ROOT / "research/agents_t738/out/LINE_INDEX_V3_0_78.json"
T743 = ROOT / "research/agents_t743/out/T743_ALSENAN_COUNTS.json"
I233 = ROOT / "research/agents_t233/ALSENAN_FOOTING_INPUT.json"
L263 = ROOT / "research/agents_t263/LEDGER_T263.csv"
L276 = ROOT / "research/agents_t276/LEDGER_T276.csv"
T174 = ROOT / "research/agents_t174/T174_STRAPS.json"

LEFT_TO_T764 = {"L-636fd3ff1784a12e653b", "L-aac1f35e08f85b643692", "L-90b40877c8c3da54ba1b",
                "L-3e8fe55da71851816dd4"}   # the last one: MAIN_FILL ROOF_LAYERS (top roof membrane 46.59 m2)
UPTURN_H = 0.20          # owner Q-30 / Q-35: 0.20 m upturn, also the transition across a door (engine high bound)
DOOR_W_WET = 0.80        # T-074 hand table (Q-35 addendum): 12 wet doors 0.80, one 1.00, one 0.90
SCREED_T = 0.05          # printed 5 cm screed under the footings (p.13)
SLAB_T = 0.10            # ground slab printed 10 cm (T-263 'D - slab 0.10')
BEAM_D_DEFAULT = 0.60    # company default beam depth (owner 2026-11-13)
LIFT_WALL_T = 0.20       # company default lift walls 0.20
FOUND_MIN = 1.50         # printed minimum founding below plot level (general note 1)
LIFT_BASE_H = 0.55       # p.14 lift base
LIFT_RING = 2.20         # p.14 ring 2.200 x 2.200
BOUNDARY_FORMATION = 1.67  # T-764 boundary band formation (same as the footings it runs through, S01)
BLINDING_T = 0.10


def r(x, n=3):
    return None if x is None else round(x + 0.0, n)


def load_lines():
    d = json.loads(IDX.read_text(encoding="utf-8"))
    return {l["line_id"]: l for l in d["lines"]}


def needs_figure(l):
    """a WP line with no point figure: BLANK (held, no bounds) or a HELD range; EXCLUDED lines keep their class."""
    return (("WP" in l["item_code"]) and l["class"] == "HELD" and l["line_id"] not in LEFT_TO_T764)


def before(l):
    return {"class": l["class"], "net": l["measured_net"], "low": l["held_low"], "high": l["held_high"]}


def row(l, net, label, basis):
    return {"line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"], "element_id": l["element_id"],
            "before": before(l), "after": {"class": "RELEASED", "net": net}, "label": label, "basis": basis}


# --------------------------------------------------------------------------------------------- wet rooms
def penetrations(lines):
    cen = {x["room_id"]: x for x in json.loads(T743.read_text(encoding="utf-8"))["rows"]}
    out = []
    for l in lines:
        if l["item_code"] != "FIN.WP.PENETRATION":
            continue
        room = l["element_id"].split(":")[0]
        c = cen.get(room)
        if c is None:
            raise SystemExit(f"no sanitary census row for {room}: refuse (never 0)")
        pcs = c["pcs"]
        n = sum(pcs.values())
        parts = " + ".join(f"{k.lower()} {v}" for k, v in sorted(pcs.items()))
        held = c.get("held") or []
        if held:     # a fixture point the sheets do not draw: one penetration by the owner default, never 0
            out.append(row(l, float(n + len(held)), "DEFAULT",
                           f"{room}: {parts} MEASURED (T-743 sanitary sheet) + {len(held)} "
                           f"{'/'.join(h.lower() for h in held)} point not drawn: owner default one WP penetration "
                           f"per fixture = {n + len(held)} pcs"))
        else:
            out.append(row(l, float(n), "MEASURED",
                           f"{room}: {parts} = {n} pcs (T-743 sanitary census, owner default one WP penetration per "
                           f"fixture)"))
    return out


def doorway_transitions(lines):
    out = []
    for l in lines:
        if l["item_code"] != "FIN.WP.DOORWAY_TRANSITION":
            continue
        hi = l["held_high"]
        if hi is not None:   # the engine's high bound = door width x 0.20 (low 0 = 'no transition')
            w = hi / UPTURN_H
            out.append(row(l, r(hi, 4), "ESTIMATE",
                           f"door width {w:.2f} x 0.20 upturn carried across the door (owner Q-30 / Q-35, one transition "
                           f"per door) = the engine high bound {hi:g} m2; low 0 dropped"))
        else:
            out.append(row(l, r(DOOR_W_WET * UPTURN_H, 4), "DRAWING-READ",
                           f"door width 0.80 (T-074 hand table of every wet door, Q-35 addendum; same width as the "
                           f"released FIN.WP.DOORWAY 0.12 m2 = 0.80 x wall 0.15) x 0.20 upturn = 0.16 m2"))
    return out


def terminations(lines):
    out = []
    for l in lines:
        if l["item_code"] != "FIN.WP.TERMINATION" or l["class"] != "HELD":
            continue
        hi = l["held_high"]
        if hi is None:
            raise SystemExit(f"{l['line_id']}: termination without bounds: refuse")
        out.append(row(l, r(hi, 4), "ESTIMATE",
                       f"membrane ends along the open edge / opening it names: run = the engine high bound {hi:g} lm "
                       f"(the drawn width); low 0 = 'not terminated', dropped"
                       + ("; below 1 % of its family (materiality), logged" if hi < 0.05 else "")))
    return out


def wall_upturn_pantry(lines):
    out = []
    for l in lines:
        if l["item_code"] == "FIN.WP.WALL_UPTURN" and l["class"] == "HELD":
            run_lo, gaps = 7.000, 2.500
            net = (run_lo + gaps) * UPTURN_H
            out.append(row(l, r(net, 3), "DEFAULT",
                           f"pantry box 4.50 x 3.00: perimeter 15.00 - open side 4.50 - door 1.00 = 9.50 m wall run "
                           f"(T-750 hand table: 7.00 + window gaps 1.00 + 1.50) x 0.20 = {net:.2f} m2; the upturn runs "
                           f"under both windows because the default sill (0.90 dry / 1.60 wet) is above 0.20"))
    return out


def roof_ledge(lines):
    out = []
    for l in lines:
        if l["item_code"] in ("FIN.WP.ROOF", "FIN.WP.ROOF_UPTURN") and l["class"] == "HELD":
            hi = l["held_high"]
            out.append(row(l, r(hi, 3), "ESTIMATE",
                           f"1F pool-court +5.50 ledge drawn: the engine high bound {hi:g} {l['unit']} (drawn ledge "
                           f"/ window-face run; low 0 = 'not membraned', dropped); below 1 % of the roof WP lines"))
    return out


# --------------------------------------------------------------------------------------------- foundation
def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def footing_sides():
    d = json.loads(I233.read_text(encoding="utf-8"))
    sch = d["schedule"]
    tot, parts = 0.0, []
    for o in d["outlines"]:
        if o["tags"] == ["FF"]:
            continue                      # the lift footing: p.14 lift system owns its faces
        tag = "F10" if o["id"] == "1B1B" else o["tags"][0]
        h = sch[tag]["H"]
        p = 2 * (o["a"] + o["b"])
        tot += p * h
        parts.append(f"{o['id']} {tag} 2x({o['a']}+{o['b']})x{h}")
    return tot, len(parts)


def neck_heights(lines):
    """mean neck height per schedule mark from the neck concrete of the index: (low+high)/2 / section; T-761 base 1.95."""
    sec = {}
    for x in _rows(L263):
        if x["member"] == "NECK":
            m = re.search(r"(C\d*|CN) perimeter 2 x \(([\d.]+) \+ ([\d.]+)\)", x["basis"])
            if m:
                sec[m.group(1)] = float(m.group(2)) * float(m.group(3))
    hs = defaultdict(list)
    for l in lines:
        if l["item_code"] == "STR.CONC.NECK" and l["held_low"] is not None and l["held_high"] is not None:
            mk = re.search(r":(C\d*|CN)@", l["element_id"]).group(1)
            hs[mk].append((l["held_low"] + l["held_high"]) / 2 / sec[mk])
    return sec, {k: sum(v) / len(v) for k, v in hs.items()}


def neck_faces(lines):
    sec, hm = neck_heights(lines)
    allh = [h for h in hm.values()]
    h_all = sum(allh) / len(allh)
    tot, n, used_all = 0.0, 0, 0
    for x in _rows(L263):
        if x["member"] == "NECK" and x["status"] == "HELD":
            per = float(re.search(r"= ([\d.]+) m x neck height", x["basis"]).group(1))
            mk = x["element"].split()[0].split(":")[1]
            h = hm.get(mk)
            if h is None:
                h, used_all = h_all, used_all + 1
            tot += per * h
            n += 1
    return tot, n, hm, h_all, used_all


def footing_tops():
    tot, n = 0.0, 0
    for x in _rows(L263):
        if x["member"] == "FOOTING" and x["status"] == "HELD":
            rd = json.loads(x["readings"])
            if "SINGLE" in rd:
                v = rd["SINGLE"]
            elif "SINGLE_low" in rd:
                v = (rd["SINGLE_low"] + rd["SINGLE_high"]) / 2
            else:   # 1B1B, Q-31 C: bigger (drawn) area 3.25 x 1.40 = 4.55 less necks C10 0.21 + C 0.15
                v = 4.55 - 0.21 - 0.15
            tot += v
            n += 1
    return tot, n


def gb_faces_held():
    tot, n_mid, n_def = 0.0, 0, 0
    for x in _rows(L276):
        if x["member"] == "GROUND_BEAM" and x["status"] == "HELD":
            rd = json.loads(x["readings"] or "{}")
            if "candidate_low" in rd and "candidate_high" in rd:
                tot += (rd["candidate_low"] + rd["candidate_high"]) / 2
                n_mid += 1
            else:
                tot += rd["length_m"] * (BEAM_D_DEFAULT - SLAB_T)
                n_def += 1
    return tot, n_mid, n_def


def straps_faces():
    tot, parts = 0.0, []
    for s in json.loads(T174.read_text(encoding="utf-8")):
        run = s["concrete"]["plan_area_outside_m2"] / s["B_m"]
        f = run * (2 * s["D_m"] + s["B_m"])
        tot += f
        parts.append(f"{s['mark']} {run:.2f} x (2x{s['D_m']}+{s['B_m']}) = {f:.2f}")
    return tot, parts


def foundation(lines, all_lines):
    by = {l["element_id"].split(":", 1)[1] + "|" + l["unit"]: l for l in lines
          if l["item_code"].startswith("WP.FOUNDATION.") and l["class"] == "HELD"}
    out = []
    a1b1b = 3.25 * 1.40
    out.append(row(by["FOOTING_UNDERLAY_MEMBRANE_1B1B|m2"], r(a1b1b, 3), "ESTIMATE",
                   "footing 1B1B (F10 + F, Q-31 C): owner 'you can choose the bigger area' = drawn 3.25 x 1.40 = "
                   "4.55 m2, PROVISIONAL, flagged; schedule reading 2.80 x 1.40 + 0.90 x 0.80 = 4.64 beside"))
    out.append(row(by["FOOTING_PROTECTION_SCREED_1B1B|m2"], r(a1b1b, 3), "ESTIMATE",
                   "same footing 1B1B: 4.55 m2 under the footing (Q-31 bigger area, PROVISIONAL)"))
    out.append(row(by["FOOTING_PROTECTION_SCREED_1B1B|m3"], r(a1b1b * SCREED_T, 4), "ESTIMATE",
                   "4.55 m2 x printed 5 cm screed (p.13) = 0.2275 m3"))
    fs, nf = footing_sides()
    out.append(row(by["FOOTING_SIDE_FACES|m2"], r(fs, 2), "ESTIMATE",
                   f"{nf} footings (lift FF excluded: p.14 system): sum of 2 x (L + W) x schedule H, 1B1B drawn "
                   f"3.25 x 1.40 x F10 H 0.50 = {fs:.2f} m2 (governing p.13 detail not selected, Q-21 C)"))
    ft, nft = footing_tops()
    out.append(row(by["FOOTING_TOPS_OUTSIDE_NECKS|m2"], r(ft, 2), "ESTIMATE",
                   f"{nft} footings: outline area - neck sections (T-263 per footing; 1B1B 4.55 - C10 0.21 - C 0.15; "
                   f"1B1A midpoint) = {ft:.2f} m2"))
    nfc, nn, hm, h_all, used_all = neck_faces(all_lines)
    out.append(row(by["NECK_FACES|m2"], r(nfc, 2), "ESTIMATE",
                   f"{nn} necks: perimeter (T-263, sum 53.40 m) x neck height of the same mark = neck concrete range "
                   f"midpoint / schedule section (mean {h_all:.2f} m, {used_all} without a range at that mean) = "
                   f"{nfc:.2f} m2"))
    gb, nm, nd = gb_faces_held()
    out.append(row(by["BURIED_GROUND_BEAM_FACES_HELD|m2"], r(gb, 2), "ESTIMATE",
                   f"118 held ground-beam faces (T-276): {nm} at the candidate range midpoint, {nd} traced length x "
                   f"(default beam depth 0.60 - slab 0.10) = {gb:.2f} m2"))
    sf, sp = straps_faces()
    bnd = 44.07 * 2 * (BOUNDARY_FORMATION - BLINDING_T)
    out.append(row(by["BOUNDARY_GB_AND_STRAPS|m2"], r(sf + bnd, 2), "ESTIMATE",
                   f"straps 2 sides + top {sf:.2f} ({'; '.join(sp)}) + boundary band 44.07 m (T-263) x 2 faces x "
                   f"buried 1.57 (formation 1.67 as T-764 - blinding 0.10) {bnd:.2f} = {sf + bnd:.2f} m2; p.14 "
                   f"prints no coating on the boundary detail: RULE_DIFFERENCE, line may be struck by the owner"))
    lift_h = FOUND_MIN - BLINDING_T - LIFT_BASE_H     # base top below N.G. 0.00: 1.50 - 0.10 - 0.55 = 0.85 buried
    lift_p = 4 * (LIFT_RING + 2 * LIFT_WALL_T)
    lw = lift_p * lift_h
    for key in ("LIFT_PIT_MEMBRANE_WALLS|m2", "LIFT_PIT_BOARD_WALLS|m2"):
        out.append(row(by[key], r(lw, 2), "DEFAULT",
                       f"pit outer walls (ring 2.20 + 2 x default lift wall 0.20) x 4 = {lift_p:.2f} m x buried "
                       f"height {lift_h:.2f} (printed min founding 1.50 - blinding 0.10 - base 0.55, to N.G.) = "
                       f"{lw:.2f} m2 (pit depth D-43 not printed)"))
    out.append(row(by["FOUNDATION_WP_PROCUREMENT|item"], 1.0, "DEFAULT",
                   "1 item: liquid coating supply for the buried faces of this set (product, coats, coverage not "
                   "printed, UP-WP-MAT-001); priced on the m2 lines"))
    return out, {"footing_sides": fs, "footing_tops": ft, "neck_faces": nfc, "gb_held": gb, "straps": sf,
                 "boundary": bnd, "lift_walls": lw, "neck_height_by_mark": {k: round(v, 3) for k, v in hm.items()}}


def build():
    L = load_lines()
    todo = [l for l in L.values() if needs_figure(l)]
    rows = []
    rows += penetrations(todo)
    rows += doorway_transitions(todo)
    rows += terminations(todo)
    rows += wall_upturn_pantry(todo)
    rows += roof_ledge(todo)
    f, comp = foundation(todo, list(L.values()))
    rows += f
    done = {x["line_id"] for x in rows}
    left = sorted(l["line_id"] for l in todo if l["line_id"] not in done)
    for x in rows:
        assert x["after"]["net"] is not None and x["after"]["net"] > 0, x   # never 0, never blank
        assert x["label"] in ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")
    rows.sort(key=lambda x: (x["item_code"], x["element_id"]))
    wet_floor = sum(l["measured_net"] for l in L.values() if l["item_code"] == "FIN.WP.FLOOR" and l["class"] == "RELEASED")
    summ = {"lines_without_point_before": len(todo), "rows": len(rows), "lines_without_point_after": len(left),
            "left_to_T764": sorted(LEFT_TO_T764),
            "per_item": {}, "components_m2": {k: (round(v, 2) if isinstance(v, float) else v) for k, v in comp.items()},
            "wet_floor_released_m2": round(wet_floor, 2), "freelancer_wet_floor_m2": 72.01,
            "notes": [
                "wet floor 85.58 = 72.12 (T-010 rooms, vs freelancer 72.01: +0.11 m2, +0.15 %) + pantry wet zone "
                "GF-RC99C2A 13.455 m2 (owner Q-30 kitchens / pantry like a bathroom; the freelancer has none): "
                "RULE_DIFFERENCE +13.57 m2 (+18.8 %), not a measurement error",
                "GF-RC99C2A (pantry) has 1 floor drain (T-743) and no FIN.WP.PENETRATION line: a MISSING line of 1 pcs "
                "MEASURED for the wiring package (T-750 adds it); not counted in the 55 pcs",
                "BOUNDARY_GB_AND_STRAPS: 138.38 of its 154.94 m2 is the boundary band, whose p.14 detail prints no "
                "coating: RULE_DIFFERENCE, kept as ESTIMATE with its components so the owner can strike it",
                "FIN.WP.PENETRATION supersedes the T-750 ranges 19 .. 31 pcs (floor outlets only) by the owner default "
                "of 2026-11-13: one per fixture (WC, basin, shower, floor drain)"]}
    for x in rows:
        k = f"{x['item_code']} [{x['unit']}]"
        s = summ["per_item"].setdefault(k, {"lines": 0, "after": 0.0})
        s["lines"] += 1
        s["after"] = round(s["after"] + x["after"]["net"], 4)
    return {"schema": "URBAN_FIX_ROWS_V1", "task": "T-767", "candidate_version": "ARCH_TAKEOFF_V3.0.78",
            "inputs": [str(p.relative_to(ROOT)) for p in (IDX, T743, I233, L263, L276, T174)],
            "summary": summ, "rows": rows, "unresolved": left}


def md(d):
    s = d["summary"]
    out = ["# T-767 fix rows: waterproofing lines without a figure on V3.0.78", "",
           f"Lines without a point figure (WP families; 3 roof lines left to T-764 and 1 to MAIN_FILL): "
           f"{s['lines_without_point_before']} -> {s['lines_without_point_after']}; rows {s['rows']}.", "",
           f"Wet-room membrane floor (released, unchanged): {s['wet_floor_released_m2']} m2 vs freelancer "
           f"{s['freelancer_wet_floor_m2']} m2.", "", "| item | lines | after |", "|---|---|---|"]
    out = out[:4] + [f"- {n}" for n in s["notes"]] + [""] + out[4:]
    out += [f"| {k} | {v['lines']} | {v['after']} |" for k, v in sorted(s["per_item"].items())]
    out += ["", "| line | item | unit | element | before | after | label | basis |", "|---|---|---|---|---|---|---|---|"]
    for x in d["rows"]:
        b = x["before"]
        bs = "BLANK" if b["low"] is None and b["high"] is None else f"HELD {b['low']} .. {b['high']}"
        out.append(f"| {x['line_id']} | {x['item_code']} | {x['unit']} | {x['element_id']} | {bs} | "
                   f"{x['after']['net']} | {x['label']} | {x['basis']} |")
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="rebuild and compare with out/FIX_ROWS.json")
    a = ap.parse_args(argv)
    d = build()
    js = json.dumps(d, indent=1, ensure_ascii=False) + "\n"
    if a.check:
        ok = (OUT / "FIX_ROWS.json").read_text(encoding="utf-8") == js
        print("T-767 check", "PASS" if ok else "FAIL (stale out/FIX_ROWS.json)")
        return 0 if ok else 1
    OUT.mkdir(exist_ok=True)
    (OUT / "FIX_ROWS.json").write_text(js, encoding="utf-8")
    (OUT / "FIX_ROWS.md").write_text(md(d), encoding="utf-8")
    print(json.dumps(d["summary"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
