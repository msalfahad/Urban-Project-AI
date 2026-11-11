"""T-710 development-villa builder: WATERPROOFING ROUND 3 on ARCH_TAKEOFF_V3.0.70 (research, unwired).

    python3 -I research/agents_t710/t710_alsenan.py [--check]

(a) census of the 58 WP entries (53 HELD + 5 MISSING) on V3.0.70 by cause (R-T710-3), each with its drawing basis;
(b) the six sunken wet-room panels (T-213, designer item D-41) laid over the 1F / 2F plans by this run's own overlay
    (t710_probe.py): which wet room each lies under, the recess loop, the drop bound from the boundary beams, and the
    extra membrane as HELD bounds (R-T710-1); the six suspended wet rooms' floors and upturns re-measured by face line;
(c) the 5 MISSING families: element, unit, what the drawings print;
(d) penetrations: the W.C. outlet datum and which sheet could settle it.
Inputs: merged repository files pinned by sha256; own-read constants below (relative metres / entity handles only).
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
import t710_rules as R  # noqa: E402

P = {
    "v3070": ("research/agents_t693/out/LINE_INDEX_V3_0_70.json", "6c12da077200db17"),
    "v3066": ("research/agents_t677/out/LINE_INDEX_V3_0_66.json", None),
    "t685": ("research/agents_t685/out/T685_WP_CENSUS.json", "1d073b7909e24080"),
    "t691": ("research/agents_t691/out/T691_WP_ROUND2.json", "2e190feefd0bd16c"),
    "t213": ("research/agents_t213/SUNKEN_PANELS_T213.json", "e2831f55abcb7d09"),
}
OUT = HERE / "out"
WP = ("FIN.WP.", "WP.")

# ---------------------------------------------------------------- own read this run (t710_probe.py stages 1-5)
OWN = {
    "drawings": "Drive 'Alsenan chalet project': P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55) and "
                "'ST7757 dxf.dxf' (sha256 9f9d1179), own decode this run into the private folder",
    "overlay": "ST S-COL.BON 35C -> arch S-COL.BON 2FAE (the T-702 GF fit), then the arch plan-to-plan translation found "
               "by column votes (GF -> 1F 14 columns, GF -> 2F 6); ST 1F-roof sheet -> GF-roof sheet 19 column votes. "
               "Checked: GF-roof sheet -> 1F plan 18 of 27 ST columns within 12 m land on an arch column (worst 0.3 mm); "
               "1F-roof sheet -> 2F plan 7 of 21 (worst 0.1 mm); the others change size between storeys",
    "beams": "boundary beams per panel as T-213 (merged); depths from the ST7757.pdf p.10 / p.11 schedules as read in "
             "research/qs_wall_treatment_01/pa04/structural.py: B1 20x40, B2 20x40, B4 20x50, B5 20x50, CB4 20x50, "
             "CB5 20x40, B11 20x75, B17 45x75, B27 90x85, B28 25x75; slab t 0.16 (note 18; 'T 16' in 280)",
}
# room cells: four face lines (W, E, S, N), box, engine floor / upturn, door gap and window gap on the face walk
ROOMS = {
    "1F-RED23B8": {"faces": "B09 / B01 / AD6 / B1F", "box": ("2.0000", "1.8000"), "column_in_box_m2": "0.0225",
                   "door_m": "0.800", "windows": "0.600 (N)", "engine_floor": "3.5775", "engine_upturn": "1.36"},
    "1F-R52AC05": {"faces": "B05 / B0E / AD7 / CC5", "box": ("1.4700", "1.8000"), "column_in_box_m2": "0",
                   "door_m": "0.800", "windows": "0.600 (N)", "engine_floor": "2.646", "engine_upturn": "1.148"},
    "1F-R48AA46": {"faces": "B3E / C23 / AE4 / C28", "box": ("2.0500", "2.4500"), "column_in_box_m2": "0",
                   "door_m": "0.800", "windows": "0.600 (S)", "engine_floor": "5.0225", "engine_upturn": "1.64"},
    "1F-R8BDA49": {"faces": "C22 / C1C / C25 / C26", "box": ("2.0500", "2.4500"), "column_in_box_m2": "0",
                   "door_m": "0.800", "windows": "0.600 (S)", "engine_floor": "5.0225", "engine_upturn": "1.64"},
    "1F-R48CDA5": {"faces": "C0D / B69 / B1B / C0C", "box": ("2.2500", "2.1000"), "column_in_box_m2": "0",
                   "door_m": "0.800", "windows": "0.4643 (E)", "engine_floor": "4.725", "engine_upturn": "1.58"},
    "2F-RE83BED": {"faces": "1296 / 128F / 1298 / 127B", "box": ("1.8500", "3.0000"), "column_in_box_m2": "0",
                   "door_m": "0.800", "windows": "0.600 (N)", "engine_floor": "5.55", "engine_upturn": "1.78"},
}
# panel n room (stage 4): area in the room, recess loop = along the room faces + free step inside the room
PIECES = [
    # room, panel, in-room m2, loop m, along faces m, free step m
    ("1F-RED23B8", "275", "3.3316", "7.3121", "1.9020", "5.4101"),
    ("1F-R52AC05", "276", "2.5721", "6.4400", "4.9720", "1.4680"),
    ("1F-R48AA46", "280", "4.9551", "8.7884", "8.2602", "0.5282"),
    ("1F-R8BDA49", "280", "1.2216", "5.4235", "3.1652", "2.2584"),
    ("1F-R8BDA49", "287", "1.2835", "5.5390", "2.4479", "3.0911"),
    ("1F-R48CDA5", "298", "4.1089", "8.7952", "3.9644", "4.8308"),
    ("2F-RE83BED", "5BF", "5.3997", "9.5998", "6.6018", "2.9980"),
]
# panel parts outside every wet room (stage 4): the dry cell north of the 1F twins, faces B3F / C1F / C29 / C24
# (box 4.25 x 4.50 = 19.125 m2; engine room id not bound this run), and wall footprints
OUTSIDE = {"1F-DRY-NORTH (B3F / C1F / C29 / C24)": {"280": "0.5831", "287": "0.6419"}}
# own hatch areas (union of the region loops); T-213 prints 275 3.3250 / 276 2.5725 / 287 2.0804 / 298 4.1076:
# the own read takes edge-path vertices as segment starts (rounded corners squared): +0.0066 / +0.0323 / +0.0652 /
# +0.0020 m2, named; the WP quantities use the part inside each room, so the residual reaches no released line
PANEL_HATCH = {"275": "3.3316", "276": "2.6048", "280": "7.3009", "287": "2.1456", "298": "4.1096", "5BF": "5.4000"}
BOUNDARY = {  # T-213 boundary beams -> scheduled depth (m)
    "275": {"B1": "0.40", "B4": "0.50", "B11": "0.75"},
    "276": {"B1": "0.40", "B11": "0.75"},
    "280": {"B1": "0.40", "B5": "0.50", "CB5": "0.40", "B27": "0.85"},
    "287": {"B1": "0.40", "CB4": "0.50", "B27": "0.85"},
    "298": {"B4": "0.50", "B17": "0.75", "B28": "0.75"},
    "5BF": {"B2": "0.40"},
}
T_SLAB = "0.16"
UPTURN_H = "0.20"  # UP-WP-003 1.7.0 (OWNER_APPROVED)

MISSING_FAMILIES = {
    "MISSING:FIN.WP.DOORWAY[m2]/DOOR:D-GF-07-PANTRY/THRESHOLD_FLOOR":
        ("the membrane continued through the pantry door D-GF-07 over the wall thickness (UP-WP-003 v1.1 floor piece)",
         "m2", "PRINTED: gap 1.000 (D120 33E) x wall 0.200 (158 / 15A) = 0.200", "MEASURABLE_NOW", "0.200"),
    "MISSING:FIN.WP.DOORWAY_TRANSITION_NR[pcs]/DOOR:D-GF-07-PANTRY/TRANSITION":
        ("one doorway transition per physical door (UP-WP-DOOR-001, Q-35 C)", "pcs",
         "PRINTED: one door D120 33E", "MEASURABLE_NOW", "1"),
    "MISSING:FIN.WP.DOORWAY_TRANSITION[m2]/DOOR:D-GF-07-PANTRY/TRANSITION":
        ("the transition built by its detail at that door (Q-35 C)", "m2",
         "NOT PRINTED: no wet-room / threshold detail issued (T-195 register)", "DESIGNER", None),
    "MISSING:FIN.WP.TERMINATION[lm]/GF-07:OPEN_SIDE_DINING/MEMBRANE_EDGE":
        ("the membrane edge where the pantry opens to the dining room (no wall)", "lm",
         "PRINTED box line B3 4.000 + AD 0.500 = DIMENSION 5E1 4500; the stop line itself by owner Q-37 A",
         "MEASURABLE_NOW", "4.500"),
    "MISSING:FIN.WP.PENETRATION[pcs]/GF-07/FLOOR_PENETRATIONS":
        ("membrane penetrations in the pantry floor (UP-WP-004)", "pcs",
         "PRINTED: one floor drain on sanitary-7757 GF; no W.C.; the stack is at high level", "MEASURABLE_NOW", "1"),
}
CAUSE_OF_CLASS = {"DESIGNER_ITEM": "DESIGNER", "OPEN_BOUND": "DESIGNER", "OWNER_OPEN": "NEEDS_OWNER_RULE",
                  "MEASURABLE_NOW": "MEASURABLE_NOW", "MEASURED_NOT_WIRED": "MEASURABLE_NOW",
                  "NO_PHYSICAL_ELEMENT": "NO_PHYSICAL_ELEMENT"}


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()[:16]


def load(k):
    rel, want = P[k]
    if want is not None and sha(rel) != want:
        raise SystemExit(f"input {rel} changed: sha {sha(rel)} != pinned {want}")
    return json.loads((ROOT / rel).read_text())


def drawing_of(e):
    code = e["item_code"]
    if code == "FIN.WP.PENETRATION":
        return "sanitary-7757.pdf (floor drains printed; W.C. pan outlet type printed on no sheet)"
    if code.startswith("FIN.WP.DOORWAY_TRANSITION"):
        return "P7757 plans print the door; no threshold / wet-room detail issued (T-195 register)"
    if code.startswith("WP.FOUNDATION"):
        return "ST7757.pdf p.13 foundation details / schedules: " + (e.get("designer_ref") or "")
    if e.get("owner_ref") or "2F-ROOF-TOP" in (e.get("element_id") or ""):
        return "no plan draws the 2F top roof outline (Q-34 parked)"
    if "POOLCOURT" in (e.get("element_id") or ""):
        return "P7757 1F pool-court ledge (T-522 / T-529 measured, overlay only)"
    if code == "FIN.WP.TERMINATION":
        return "P7757 plan: " + (e.get("designer_ref") or "membrane edge at an opening; stop detail not issued")
    return e.get("designer_ref") or e.get("source", "")


def census(v70, t685, t691):
    idx = {l["line_id"]: l for l in v70["lines"] if l["item_code"].startswith(WP)}
    pen = {r["line"]: r for r in t691["penetrations"]["rows"]}
    rows = []
    for e in t685["entries"]:
        key = e["key"]
        line = idx.get(key)
        if key.startswith("MISSING:"):
            elem, unit, printed, cause, val = MISSING_FAMILIES[key]
            assert line is None
            row = {"key": key, "code": e["item_code"], "unit": unit, "on_v3070": "NO LINE", "cause": cause,
                   "element": elem, "drawing": printed, "status": "MEASURED_UNWIRED" if val else "HELD",
                   "after": val}
            if "PENETRATION" in key:
                row["after"] = "1 .. 1 (T-691: 1 FD, no W.C.)"
        else:
            assert line is not None and line["class"] == "HELD", key
            cause = CAUSE_OF_CLASS[e["class"]]
            after = None
            if key in pen:
                r = pen[key]
                after = f"{r['after_low']} .. {r['after_high']} pcs (FD {r['fd_printed']} firm + W.C. {r['wc_drawn']} open)"
            elif e["class"] in ("MEASURABLE_NOW", "MEASURED_NOT_WIRED"):
                after = e.get("fix")
            row = {"key": key, "code": e["item_code"], "unit": e["unit"], "on_v3070": "HELD", "cause": cause,
                   "element": e["element_id"], "bound": f"{e.get('held_low')} .. {e.get('held_high')}"
                   if e.get("held_low") is not None else "blank", "drawing": drawing_of(e),
                   "status": "HELD", "after": after}
            if e["class"] == "NO_PHYSICAL_ELEMENT":
                row["proposal"] = "EXCLUDED with its reason (T-303 finding 5: the face is WALL); never a 0 in a total"
        rows.append(row)
    by = R.census_check([{"key": r["key"], "cause": r["cause"], "status": r["status"], "value": None} for r in rows],
                        len(t685["entries"]))
    held = sum(1 for l in idx.values() if l["class"] == "HELD")
    assert held == 53 and len(rows) - held == 5, (held, len(rows))
    return rows, by, len(idx), held


def sunken():
    rooms = []
    per_panel_dmax = {h: R.d_max([Decimal(x) for x in b.values()], Decimal(T_SLAB)) for h, b in BOUNDARY.items()}
    for rid, rm in ROOMS.items():
        w, h = (Decimal(x) for x in rm["box"])
        floor = w * h - Decimal(rm["column_in_box_m2"])
        perim = 2 * (w + h)
        up = R.upturn(perim - Decimal(rm["door_m"]), Decimal(UPTURN_H))
        pcs = [p for p in PIECES if p[0] == rid]
        extra_low = Decimal("0")
        extra_high = Decimal("0")
        parts = []
        for _, ph, a, loop, along, free in pcs:
            assert abs(Decimal(along) + Decimal(free) - Decimal(loop)) <= Decimal("0.0002")
            x = R.recess_wp(Decimal(loop), drop_max_m=per_panel_dmax[ph])
            extra_high += x["high"]
            parts.append({"panel": ph, "in_room_m2": a, "loop_m": loop, "along_faces_m": along, "free_step_m": free,
                          "d_max_m": str(per_panel_dmax[ph]), "extra_m2": f"{x['low']} .. {x['high']}",
                          "status": x["status"]})
        cover = sum(Decimal(p[2]) for p in pcs)
        rooms.append({
            "room": rid, "faces": rm["faces"], "floor_m2_own": str(R.q6(floor)), "floor_m2_engine": rm["engine_floor"],
            "floor_verdict": "AGREE" if abs(floor - Decimal(rm["engine_floor"])) < Decimal("0.0005") else "DIFFERS",
            "upturn_run_m": str(up["run_m"]), "upturn_m2_own": str(up["value"]), "upturn_m2_engine": rm["engine_upturn"],
            "upturn_verdict": "AGREE" if abs(up["value"] - Decimal(rm["engine_upturn"])) < Decimal("0.0005") else "DIFFERS",
            "door_m": rm["door_m"], "windows": rm["windows"],
            "panel_cover_m2": str(cover), "panel_cover_pct": str((cover / floor * 100).quantize(Decimal("0.1"))),
            "recess": parts,
            "recess_wp_extra_m2": {"status": "HELD (D-41: drop d and membrane position unprinted)",
                                   "low": str(extra_low), "high": str(R.q6(extra_high))},
        })
    outside = []
    for cell, m in OUTSIDE.items():
        for ph, a in m.items():
            outside.append({"cell": cell, "panel": ph, "m2": a, "scope": "floor bed of that room (HELD d), NOT waterproofing"})
    # panel area closure: hatch = in wet rooms + outside wet rooms + wall footprints / gaps (named)
    closure = {}
    for ph, A in PANEL_HATCH.items():
        inw = sum(Decimal(p[2]) for p in PIECES if p[1] == ph)
        out = sum(Decimal(m.get(ph, "0")) for m in OUTSIDE.values())
        sp = R.split_panel(Decimal(A), inw)
        closure[ph] = {"hatch_m2": A, "in_wet_rooms_m2": str(sp["wp_scope_m2"]), "in_dry_cell_m2": str(out),
                       "walls_and_gaps_m2": str(R.q6(Decimal(A) - inw - out)), "d_max_m": str(per_panel_dmax[ph]),
                       "boundary_beams": BOUNDARY[ph]}
    tot_high = sum(Decimal(r["recess_wp_extra_m2"]["high"]) for r in rooms)
    tot_loop = sum(Decimal(p[3]) for p in PIECES)
    return rooms, outside, closure, R.q6(tot_high), tot_loop


def main(argv):
    v70, t685, t691 = load("v3070"), load("t685"), load("t691")
    load("t213")
    v66 = json.loads((ROOT / P["v3066"][0]).read_text())
    f = lambda d: {l["line_id"]: l for l in d["lines"] if l["item_code"].startswith(WP)}  # noqa: E731
    a66, a70 = f(v66), f(v70)
    unchanged = set(a66) == set(a70) and all(a66[k] == a70[k] for k in a66)
    rows, by, n_lines, held = census(v70, t685, t691)
    rooms, outside, closure, tot_high, tot_loop = sunken()
    released_upturn = sum(Decimal(str(l["measured_net"])) for l in a70.values()
                          if l["item_code"] == "FIN.WP.WALL_UPTURN" and l["class"] == "RELEASED")
    out = {
        "schema": "URBAN_T710_WP_ROUND3_V1", "task": "T-710", "candidate": v70["candidate_version"],
        "wp_lines_on_candidate": n_lines, "wp_lines_unchanged_since_v3066": unchanged,
        "census": {"held": held, "missing": len(rows) - held, "by_cause": by, "rows": rows},
        "sunken": {"rooms": rooms, "outside_wet_rooms": outside, "panel_closure": closure,
                   "recess_loop_total_m": str(tot_loop), "extra_high_total_m2": str(tot_high),
                   "released_wall_upturn_m2": str(R.q6(released_upturn)),
                   "rooms_without_panel": ["1F-R26FA0D (laundry, no W.C.)"]},
        "penetrations": {"low": t691["penetrations"]["low_pcs"], "high": t691["penetrations"]["high_pcs"],
                         "datum": "W.C. pan outlet (floor S-trap through the membrane / slab or wall P-trap)",
                         "settled_by": "a wet-room / W.C. installation detail or a sanitary fixture schedule giving the "
                                       "pan outlet; the issued sanitary-7757 sheets are plans only (no section, no "
                                       "trap detail; T-206 / T-691)",
                         "evidence_this_run": "every W.C. room on a suspended floor (6 of 6: 1F-RED23B8, 1F-R52AC05, "
                                              "1F-R48AA46, 1F-R8BDA49, 1F-R48CDA5, 2F-RE83BED) lies over a sunken "
                                              "panel, and the one suspended wet room without a W.C. (1F laundry) has "
                                              "none: consistent with floor-outlet pans drained through a recess, NOT "
                                              "proof (a recess also serves a shower fall); high ends stay open"},
        "own": OWN, "rules": ["R-T710-1", "R-T710-2", "R-T710-3"],
    }
    OUT.mkdir(exist_ok=True)
    js = json.dumps(out, indent=1, sort_keys=True, default=str) + "\n"
    md = render(out)
    if "--check" in argv:
        ok = (OUT / "T710_WP_ROUND3.json").read_text() == js and (OUT / "T710_WP_ROUND3.md").read_text() == md
        print("check", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    (OUT / "T710_WP_ROUND3.json").write_text(js)
    (OUT / "T710_WP_ROUND3.md").write_text(md)
    print("written", by, "extra high", tot_high)
    return 0


def render(o):
    s = o["sunken"]
    L = [f"# T-710 waterproofing round 3 on {o['candidate']} (generated; research, unwired)", "",
         f"WP lines on the candidate {o['wp_lines_on_candidate']} (unchanged since V3.0.66: {o['wp_lines_unchanged_since_v3066']}); "
         f"census {o['census']['held']} HELD + {o['census']['missing']} MISSING by cause: {o['census']['by_cause']}", "",
         "## (a) census", "", "| key | code | unit | cause | bound / after | drawing |", "|---|---|---|---|---|---|"]
    for r in o["census"]["rows"]:
        L.append(f"| {r['key'][:60]} | {r['code']} | {r['unit']} | {r['cause']} | {r.get('bound', '')} -> {r.get('after')} "
                 f"{r.get('proposal', '')} | {r['drawing'][:110]} |")
    L += ["", "## (b) suspended wet rooms: floor / upturn re-measured, sunken panels (D-41)", "",
          "| room | faces W/E/S/N | floor own / engine | upturn run, own / engine m2 | panel cover | recess loop (faces + free) | d_max | extra WP m2 HELD |",
          "|---|---|---|---|---|---|---|---|"]
    for r in s["rooms"]:
        loops = "; ".join(f"{p['panel']}: {p['loop_m']} ({p['along_faces_m']} + {p['free_step_m']})" for p in r["recess"])
        dm = "/".join(p["d_max_m"] for p in r["recess"])
        L.append(f"| {r['room']} | {r['faces']} | {r['floor_m2_own']} / {r['floor_m2_engine']} {r['floor_verdict']} | "
                 f"{r['upturn_run_m']}: {r['upturn_m2_own']} / {r['upturn_m2_engine']} {r['upturn_verdict']} | "
                 f"{r['panel_cover_m2']} ({r['panel_cover_pct']} %) | {loops} | {dm} | "
                 f"{r['recess_wp_extra_m2']['low']} .. {r['recess_wp_extra_m2']['high']} |")
    L += ["", f"Recess loop total {s['recess_loop_total_m']} m; extra membrane HELD 0 .. {s['extra_high_total_m2']} m2 "
          f"(released wall upturn {s['released_wall_upturn_m2']} m2); rooms without a panel: {s['rooms_without_panel']}", "",
          "Panel closure (hatch = in wet rooms + dry cell + walls / gaps):", "",
          "| panel | hatch | in wet rooms | in the dry cell | walls / gaps | d_max | boundary beams |", "|---|---|---|---|---|---|---|"]
    for h, c in s["panel_closure"].items():
        L.append(f"| {h} | {c['hatch_m2']} | {c['in_wet_rooms_m2']} | {c['in_dry_cell_m2']} | {c['walls_and_gaps_m2']} | "
                 f"{c['d_max_m']} | {c['boundary_beams']} |")
    p = o["penetrations"]
    L += ["", "## (d) penetrations", "", f"{p['low']} .. {p['high']} pcs; datum: {p['datum']}; settled by: {p['settled_by']}.",
          f"Evidence this run: {p['evidence_this_run']}.", ""]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main(sys.argv))
