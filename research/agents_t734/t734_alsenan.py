"""T-734 WATERPROOFING H4 EVIDENCE on ARCH_TAKEOFF_V3.0.73 (development villa; research, unwired; nothing released).

    python3 -I research/agents_t734/t734_alsenan.py            # write out/T734_WP_H4_EVIDENCE.{json,md}
    python3 -I research/agents_t734/t734_alsenan.py --check    # compare with the committed outputs
    python3 -I research/agents_t734/t734_alsenan.py --dxf <private P7757.dxf>   # re-measure from named handles

(a) the evidence pack for a Checker-issued downgrade-only record on the released +9.70 roof membrane
    L-636fd3ff1784a12e653b (115.832 m2, above its own band 115.656474 .. 115.813974): the face rebuilt from its named
    carrier lines (R-T734-2, no buffer / flood fill: independent of T-321 / T-691), the two dome CIRCLEs, the engine
    figure reconstructed to its exact cause, the draft fields for `tools/boq_export_v1.py downgrade-add`;
(b) the T-710 census (58 = 53 HELD + 5 MISSING) restated by line id on V3.0.73 (R-T734-3), with the 8 MEASURABLE_NOW
    entries and the 5 MISSING ones by cause;
(c) the D-41 sunken-panel recess membrane, HELD 0 .. 13.335040 m2, its hosts re-checked on V3.0.73, designer item
    named.
Drawings by Drive title only: 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55...,
re-checked this run). The --dxf mode reads named entity handles and prints lengths / areas only (no coordinates); no
drawing content is written to the repository.
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "agents_t691"))
import t734_rules as R  # noqa: E402
import t691_rules as R691  # noqa: E402

OUT = HERE / "out"
CANDIDATE = "ARCH_TAKEOFF_V3.0.73"
IDX70 = ROOT / "research/agents_t693/out/LINE_INDEX_V3_0_70.json"
IDX73 = ROOT / "research/agents_t722/out/LINE_INDEX_V3_0_73.json"
T710 = ROOT / "research/agents_t710/out/T710_WP_ROUND3.json"
T730 = ROOT / "research/agents_t730/out/T730_READINESS.json"

# ------------------------------------------------------------------------------ (a) own re-measure, pinned this run
# Own read 2026-11-12 (`--dxf`): every carrier asserted straight and axis-parallel; 1280 / 1281 / 12E6 on one y; the
# wall-face x = 1280's west end = 12E6's east end. Turtle walk (m) from the 12E2 x 1280-line corner, D-band reading.
ROOF = {
    "line": "L-636fd3ff1784a12e653b", "item": "FIN.WP.ROOF", "element": "2F-ROOF-AT379:wp_membrane",
    "released_m2": "115.832",
    "upturn_line": "L-5ce5ba49792e8f9d1f6f", "released_upturn_lm": "92.922",
    "rolls_line": "L-2ecffd1f396ede3b5eb4", "released_rolls_pcs": "17",
    "carriers": [   # (carrier, handles on it, kind, signed edge length m on the D-band ring)
        ("C1", "12E6 + 1280 + door gap 1.000 (1280 east end .. 1281 west end) + 1281", "H", "8.175"),
        ("C2", "1291 (2F block east wall outer face)", "V", "6.600"),
        ("C3", "1278 (north parapet inner face)", "H", "6.570"),
        ("C4", "12A7 (east parapet inner face)", "V", "-11.600"),
        ("C5", "1285 (south parapet inner face)", "H", "-18.870"),
        ("C6", "12C9 (west parapet inner face)", "V", "7.100"),
        ("C7", "12B9 (west-wing north parapet inner face)", "H", "4.125"),
        ("C8", "12E2 (layer D band line, D-band reading) / the 2F west wall outer face (wall-face reading)", "V",
         "-2.100"),
    ],
    "handle_lengths_m": {"1278": "6.570", "1280": "0.6158", "1281": "6.4842", "1285": "18.870", "1291": "6.800",
                         "12A7": "11.600", "12B9": "4.125", "12C9": "7.100", "12E2": "2.7684", "12E6": "0.075"},
    "dband_offset_m": "0.075",          # 12E6: 12E2 to the wall face
    "face_dband_m2": "146.374500", "face_wallface_m2": "146.532000", "perimeter_m": "65.140000",
    "dome_handles": ("12EB", "2F33"), "dome_r_mm": "2211.091523535753",    # CIRCLE, layer 5, both
    "dome_tangent_to": {"12EB": "12C9 (west parapet, clearance 0.0000 m)", "2F33": "12A7 (east parapet, 0.0000 m)"},
    "sagitta_m": "0.001",               # engine EXTERIOR_SPACES_V1 SAGITTA_M
    "band_t321": ("115.65646", "115.81396"),
    "dband_profile": "12E2 continues a stepped layer-D profile on the 2F west wall (12E0 / 12DF / 12DD / 12DC / 12D3 / "
                     "12CB / 12D5 / 12D6 / 12D8 / 12D9 / 12DB: 25 / 50 / 75 mm steps off the wall face) drawn at the "
                     "plan cut: a projecting facade feature 0.075 proud over 2.7684 m, not a base. Layer D also holds "
                     "elevation titles; no text, hatch, schedule or detail names the feature",
}


def roof():
    r_m = R.D(ROOF["dome_r_mm"]) / 1000
    n = R691.chords_for_sagitta(float(r_m), float(ROOF["sagitta_m"]))
    true, poly = R691.circle_true(float(r_m)), R691.circle_inscribed(float(r_m), n)
    # R-T734-2 on the pinned turtle walk (the --dxf mode builds the same carriers from the handles' own coordinates)
    x = y = Decimal(0)
    car = []
    for _cid, _h, kind, ln in ROOF["carriers"]:
        car.append(("H", y) if kind == "H" else ("V", x))
        if kind == "H":
            x += R.D(ln)
        else:
            y += R.D(ln)
    if (x, y) != (0, 0):
        raise R.RuleError("turtle walk does not close")
    fd = R.face(car)
    wf = list(car)
    wf[-1] = ("V", wf[-1][1] + R.D(ROOF["dband_offset_m"]))
    fw = R.face(wf)
    if (str(fd["area_m2"]), str(fw["area_m2"])) != (ROOF["face_dband_m2"], ROOF["face_wallface_m2"]):
        raise R.RuleError("pinned faces disagree with the carrier walk")
    disc = [str(r_m), str(r_m)]
    lo = R.net_membrane(fd["area_m2"], disc)
    hi = R.net_membrane(fw["area_m2"], disc)
    eng = R.net_membrane(fw["area_m2"], disc, chords=n)
    eng_lo = R.net_membrane(fd["area_m2"], disc, chords=n)
    rel = R.D(ROOF["released_m2"])
    elig = R.eligibility(rel, lo, hi)
    chord_m2 = R.q6(2 * (R.D(true["area_m2"]) - R.D(poly["area_m2"])))
    up_true = R.q6(fd["perimeter_m"] + 2 * R.D(true["ring_m"]))
    up_chord = R.q6(fd["perimeter_m"] + 2 * R.D(poly["ring_m"]))
    t321 = tuple(R.D(v) for v in ROOF["band_t321"])
    reason = (f"UNSUPPORTED BASIS: the released +9.70 roof membrane {ROOF['released_m2']} m2 lies "
              f"{elig['excess']} m2 ABOVE its own same-basis band {lo} .. {hi} m2: the trace deducts the two dome "
              f"CIRCLEs 12EB / 2F33 (r {R.q6(r_m)} m) as inscribed {n}-chord polygons (1 mm sagitta), "
              f"{R.q6(poly['area_m2'])} instead of {R.q6(true['area_m2'])} m2 each (under-deduction {chord_m2} m2, "
              f"R-T691-1); the face is closed on named lines (wall-face reading {fw['area_m2']} m2, D-band reading "
              f"{fd['area_m2']} m2: the 0.075 layer-D feature at the 2F west wall foot is unprinted, D-BAND 0.1575 m2). "
              "Downgrade only: the line goes HELD; the candidate figure stays in the audit rows; the H4 package then "
              "carries the drawing band (R-T734-1 c), never a chosen end")
    evidence = [
        "Alsenan chalet project / P7757.dxf (2F plan, +9.70 roof) CIRCLE 12EB and CIRCLE 2F33 = radius 2211.0915 mm "
        "each (pi r^2 = 15.359013 m2; 105-chord polygon 15.349849 m2)",
        "Alsenan chalet project / P7757.dxf (2F plan) LINE 1281 / 1291 / 1278 / 12A7 / 1285 / 12C9 / 12B9 / 12E2 / "
        "12E6 / 1280 + door gap 1.000 = closed face 146.374500 m2 (12E2) .. 146.532000 m2 (2F wall face), perimeter "
        "65.140 m",
        "ARCH_TAKEOFF_V3.0.73 L-636fd3ff1784a12e653b = 115.832 m2 = 146.532000 - 2 x 15.349849 = 115.832303 "
        "(3-decimal rounding 0.000303)",
    ]
    draft = R.record_draft(candidate_version=CANDIDATE, line_ids=[ROOF["line"]], unit="m2", engine_qty=rel,
                           state="HELD", basis_label="UNSUPPORTED BASIS", reason=reason, evidence=evidence)
    if R.validate_draft(draft):
        raise R.RuleError("draft invalid")
    after = R.after_state(rel, (lo, hi), draft)
    return {
        "element": "flat membrane of the +9.70 terraces round the 2F block, inside the parapet / wall faces where it "
                   "turns up 0.20 (UP-WP-ROOF-001, Q-24), the two dome discs open (Q-24 / Q-29: membrane stops at the "
                   "dome circle with an upturn); flat m2, upturn lm and rolls pcs kept apart",
        "method": "R-T734-2: the face rebuilt from its 8 named carrier lines (vertex = carrier x carrier, shoelace); "
                  "independent of the T-321 / T-691 buffered flood fill",
        "carriers": [{"carrier": c, "handles": h, "kind": k, "edge_m": e} for c, h, k, e in ROOF["carriers"]],
        "handle_lengths_m": ROOF["handle_lengths_m"],
        "per_component": [
            {"component": "face, D-band reading (C8 on 12E2)", "m2": str(fd["area_m2"])},
            {"component": "face, wall-face reading (C8 on the 2F west wall face)", "m2": str(fw["area_m2"])},
            {"component": "D-BAND strip 0.075 x 2.100 (12E6 x 12E2 below C7)", "m2": str(fw["area_m2"] - fd["area_m2"])},
            {"component": "dome 12EB true pi r^2", "m2": str(R.q6(true["area_m2"]))},
            {"component": "dome 2F33 true pi r^2", "m2": str(R.q6(true["area_m2"]))},
            {"component": f"each dome as the engine's {n}-chord polygon", "m2": str(R.q6(poly["area_m2"]))},
        ],
        "dome": {"r_m": str(R.q6(r_m)), "chords": n, "true_m2": str(R.q6(true["area_m2"])),
                 "inscribed_m2": str(R.q6(poly["area_m2"])), "under_deduction_two_m2": str(chord_m2),
                 "ring_true_m": str(R.q6(true["ring_m"])), "ring_chord_m": str(R.q6(poly["ring_m"])),
                 "tangent": ROOF["dome_tangent_to"]},
        "band_own": [str(lo), str(hi)], "band_t321": list(ROOF["band_t321"]),
        "band_agree": {"low": str(R.q6(lo - t321[0])), "high": str(R.q6(hi - t321[1]))},
        "released": ROOF["released_m2"],
        "engine_reconstruction": {"wall_face_chord": str(eng), "dband_chord": str(eng_lo),
                                  "rounded": str(eng.quantize(Decimal("0.001"))),
                                  "residual_to_released": str(R.q6(R.D(ROOF["released_m2"]) - eng)),
                                  "basis": "the engine closed the face on the 2F wall face (wall-face reading) and "
                                           "deducted 105-chord polygons: 146.532000 - 2 x 15.349849 = 115.832303"},
        "eligibility": {k: str(v) for k, v in elig.items()},
        "released_vs_band": {"above_high_m2": str(R.q6(rel - hi)), "above_high_pct": str(R.q6((rel - hi) / hi * 100)),
                             "above_low_m2": str(R.q6(rel - lo)), "above_low_pct": str(R.q6((rel - lo) / lo * 100))},
        "dband": {"m2": str(fw["area_m2"] - fd["area_m2"]), "pct_of_high": str(R.q6((fw["area_m2"] - fd["area_m2"]) / hi * 100)),
                  "evidence": ROOF["dband_profile"],
                  "physical_alternatives": [
                      "built before the membrane (a masonry pilaster / thickened wall): the membrane stops at its face "
                      "and turns up there -> D-band reading (low)",
                      "applied after the membrane (cladding / moulding): the membrane runs to the wall face under it "
                      "-> wall-face reading (high)"],
                  "settled_by": "an elevation / wall section or finishes schedule naming the 2F west wall feature "
                                "(designer item, proposed for DESIGNER_QUESTIONS; ERS s.2.7 not met: no owner rule)"},
        "downgrade_record_draft": draft,
        "downgrade_cli": ("python3 -I tools/boq_export_v1.py downgrade-add --lines <V3_0_73_BOQ_LINES.json> "
                          f"--candidate-version {CANDIDATE} --line-ids {ROOF['line']} --state HELD "
                          "--basis-label 'UNSUPPORTED BASIS' --reason <reason> --evidence <each evidence item> "
                          "--lock-file <Checker lock> --verdict-commit <Checker commit> --out <DOWNGRADE_V1_SET>"),
        "which_figure_the_downgrade_keeps": (
            "the record keeps NO figure of its own (owner 2026-10-24 23:57: never a Checker measurement). It binds the "
            "released 115.832 (engine_qty), which stays only in the audit rows ('Audit (unsupported basis)'). The "
            f"line becomes HELD; the H4 package then writes the drawing band {lo} .. {hi} m2 (both ends measured; "
            "neither chosen). 115.813974 is NOT released: its high end rests on the unprinted D-BAND reading"),
        "after_state": {k: str(v) for k, v in after.items()},
        "upturn": {"line": ROOF["upturn_line"], "released_lm": ROOF["released_upturn_lm"],
                   "true_lm": str(up_true), "chord_reconstruction_lm": str(up_chord),
                   "residual_lm": str(R.q6(R.D(ROOF["released_upturn_lm"]) - up_chord)),
                   "dband_effect_lm": "0.000 (both readings give perimeter 65.140: the strip trades 12E6 0.075 for "
                                      "its 0.075 top edge)",
                   "class": "NOT A DOWNGRADE (R-T734-1 d): 92.922 -> 92.925 raises a released value; a Gate B "
                            "change with its own re-measure, needing no record; the T-730 H4 blocker 'WAITS T-734' on "
                            "this row can be lifted",
                   "open": "a +0.000750 lm residual between the released 92.922 and the 105-chord reconstruction "
                           "92.921250 is not named in this run (above the 0.0005 rounding half-step): the Gate B "
                           "re-measure of the upturn change names it before wiring"},
        "rolls": {"line": ROOF["rolls_line"], "released_pcs": ROOF["released_rolls_pcs"],
                  "statement": "not named by the record (another line, unit pcs): the procurement count is KEEP in "
                               "T-730; the strip count's sensitivity to the 0.075 D-BAND and to 0.018 m2 was not "
                               "re-run here (the roof layout inputs live in the engine trace)"},
    }


# ------------------------------------------------------------------------------ (b) census restated on V3.0.73
PANTRY_ROOM = "GF-RC99C2A"


def census():
    i70 = {ln["line_id"]: ln for ln in json.loads(IDX70.read_text(encoding="utf-8"))["lines"]}
    l73 = json.loads(IDX73.read_text(encoding="utf-8"))["lines"]
    i73 = {ln["line_id"]: ln for ln in l73}
    wp70 = sorted(k for k, v in i70.items() if "WP" in v["item_code"])
    wp73 = sorted(k for k, v in i73.items() if "WP" in v["item_code"])
    t710 = json.loads(T710.read_text(encoding="utf-8"))["census"]
    rows, stale, gone = [], [], []
    for e in t710["rows"]:
        key = e["key"]
        if key.startswith("MISSING:"):
            still = R.missing_still_missing(e["code"], PANTRY_ROOM, l73)
            st = {"state": "MISSING" if still else "LINE_NOW_EXISTS", "changed": []}
        else:
            st = R.restate(i70.get(key), i73.get(key))
            if st["state"] == "STALE":
                stale.append(key)
            if st["state"] == "GONE":
                gone.append(key)
        cause = e["cause"]
        after = e.get("after")
        if e["code"] == "FIN.WP.PENETRATION" and isinstance(after, str) and " pcs" in after:
            lo, hi = after.split(" pcs")[0].split(" .. ")
            cause = R.penetration_cause(lo, hi)
        ln = i73.get(key)
        rows.append({"key": key, "code": e["code"], "unit": e["unit"], "element": e["element"],
                     "on_v3073": (ln["class"] if ln else "NO LINE"),
                     "v3073_value": (None if not ln else ln["measured_net"]),
                     "v3073_bounds": (None if not ln or ln["held_high"] is None else [ln["held_low"], ln["held_high"]]),
                     "restate": st["state"], "changed": st["changed"], "cause_t710": e["cause"], "cause": cause,
                     "after": after if isinstance(after, str) or after is None else json.dumps(after, sort_keys=True)})
    by = R.census_counts([{"key": r["key"], "cause": r["cause"], "status": "HELD"} for r in rows])
    by710 = R.census_counts([{"key": r["key"], "cause": r["cause_t710"], "status": "HELD"} for r in rows])
    moved = [r["key"] for r in rows if r["cause"] != r["cause_t710"]]
    return {"wp_lines_v3070": len(wp70), "wp_lines_v3073": len(wp73), "wp_line_ids_equal": wp70 == wp73,
            "wp_entries_differing": sum(i70[k] != i73[k] for k in wp73 if k in i70),
            "rows": rows, "held": sum(1 for r in rows if not r["key"].startswith("MISSING:")),
            "missing": sum(1 for r in rows if r["key"].startswith("MISSING:")),
            "stale": stale, "gone": gone, "by_cause_t710": by710, "by_cause": by, "cause_moved": moved,
            "measurable_now": [r for r in rows if r["cause"] == "MEASURABLE_NOW"],
            "missing_rows": [r for r in rows if r["key"].startswith("MISSING:")]}


# ------------------------------------------------------------------------------ (c) D-41 recess, hosts on V3.0.73
D41_ROOMS = {"1F-RED23B8": "L-a93486d24647a9e14445", "1F-R52AC05": "L-ace6533512ada47d1352",
             "1F-R48AA46": "L-ba15212ec9887e6d4f73", "1F-R8BDA49": "L-6e6daedebef2db6a83bd",
             "1F-R48CDA5": "L-60f100105399a9bdfb08", "2F-RE83BED": "L-b842beb71b67af783cd7"}


def d41():
    i70 = {ln["line_id"]: ln for ln in json.loads(IDX70.read_text(encoding="utf-8"))["lines"]}
    i73 = {ln["line_id"]: ln for ln in json.loads(IDX73.read_text(encoding="utf-8"))["lines"]}
    s = json.loads(T710.read_text(encoding="utf-8"))["sunken"]
    hosts = []
    for room, lid in D41_ROOMS.items():
        st = R.restate(i70.get(lid), i73.get(lid))
        ln = i73[lid]
        if not ln["element_id"].startswith(room + ":") or ln["item_code"] != "FIN.WP.WALL_UPTURN":
            raise R.RuleError(f"{lid}: not the wall upturn of {room}")
        hosts.append({"room": room, "upturn_line": lid, "class": ln["class"], "m2": ln["measured_net"],
                      "restate": st["state"]})
    hi = R.D(s["extra_high_total_m2"])
    if hi <= 0:
        raise R.RuleError("D-41 high end must be positive")
    rel = sum(R.D(h["m2"]) for h in hosts)
    return {"status": "HELD", "low_m2": "0", "high_m2": str(R.q6(hi)), "recess_loop_m": s["recess_loop_total_m"],
            "hosts": hosts, "hosts_released_m2": str(R.q6(rel)),
            "designer_item": "DESIGNER_QUESTIONS.md item 9 'Sunken wet-room slab panels: membrane position' (D-41): "
                             "membrane on the structural slab (tray: + loop x d) or on the fill under the tile (+0); "
                             "d unprinted, bounded by the boundary beams (d_max 0.24 / 0.34 m)",
            "statement": "no candidate line: a HELD component beside the six released wall-upturn hosts (all LIVE on "
                         "V3.0.73); low 0 is a physical alternative (membrane on the fill), never a default; nothing "
                         "moves in this task"}


def build():
    return {"schema": "URBAN_T734_WP_H4_EVIDENCE_V1", "task": "T-734", "candidate": CANDIDATE,
            "rules": ["R-T734-1", "R-T734-2", "R-T734-3"],
            "inputs": {"line_index_v3073": str(IDX73.relative_to(ROOT)), "line_index_v3070": str(IDX70.relative_to(ROOT)),
                       "t710": str(T710.relative_to(ROOT))},
            "roof": roof(), "census": census(), "d41": d41(),
            "released_moved": "none (research, unwired; V2.9 + route G unchanged)"}


def md(d):
    r, c, x = d["roof"], d["census"], d["d41"]
    L = ["# T-734 waterproofing H4 evidence on " + d["candidate"], "",
         "## (a) Roof membrane L-636fd3ff1784a12e653b: downgrade-record evidence", "",
         r["method"] + ".", "", "| carrier | handles | kind | edge m (D-band ring) |", "|---|---|---|---|"]
    L += [f"| {k['carrier']} | {k['handles']} | {k['kind']} | {k['edge_m']} |" for k in r["carriers"]]
    L += ["", "| component | m2 |", "|---|---|"] + [f"| {p['component']} | {p['m2']} |" for p in r["per_component"]]
    L += ["", f"Own band {r['band_own'][0]} .. {r['band_own'][1]} m2 (T-321 {r['band_t321'][0]} .. {r['band_t321'][1]}: "
          f"low {r['band_agree']['low']}, high {r['band_agree']['high']}). Released {r['released']} = "
          f"{r['engine_reconstruction']['basis']} (residual {r['engine_reconstruction']['residual_to_released']}, "
          f"rounding). Above the high end {r['released_vs_band']['above_high_m2']} m2 "
          f"({r['released_vs_band']['above_high_pct']} %): {r['eligibility']['state']}.", "",
          f"Domes tangent to the parapet faces: {r['dome']['tangent']}.", "",
          f"D-BAND {r['dband']['m2']} m2 ({r['dband']['pct_of_high']} %): {r['dband']['evidence']}. Alternatives: "
          + " | ".join(r["dband"]["physical_alternatives"]) + f". Settled by: {r['dband']['settled_by']}.", "",
          "Draft record (Checker types it with `downgrade-add`; the tool binds project, revision set and line "
          "content):", "", "```", json.dumps(r["downgrade_record_draft"], indent=1, ensure_ascii=False), "```", "",
          "Which figure: " + r["which_figure_the_downgrade_keeps"] + ".", "",
          f"Upturn {r['upturn']['line']}: {r['upturn']['released_lm']} -> {r['upturn']['true_lm']} lm. "
          f"{r['upturn']['class']}. Open: {r['upturn']['open']}.", "",
          f"Rolls {r['rolls']['line']} {r['rolls']['released_pcs']} pcs: {r['rolls']['statement']}.", "",
          "## (b) Census on V3.0.73 (R-T734-3)", "",
          f"WP lines {c['wp_lines_v3070']} (V3.0.70) = {c['wp_lines_v3073']} (V3.0.73), ids equal "
          f"{c['wp_line_ids_equal']}, entries differing {c['wp_entries_differing']}; {c['held']} HELD + "
          f"{c['missing']} MISSING; stale {len(c['stale'])}, gone {len(c['gone'])}.", "",
          f"By cause T-710 {c['by_cause_t710']} -> restated {c['by_cause']} (moved: {len(c['cause_moved'])}).", "",
          "| key | code | unit | V3.0.73 | restate | cause | after |", "|---|---|---|---|---|---|---|"]
    for row in c["measurable_now"] + [m for m in c["missing_rows"] if m["cause"] != "MEASURABLE_NOW"]:
        L.append(f"| {row['key']} | {row['code']} | {row['unit']} | {row['on_v3073']} | {row['restate']} | "
                 f"{row['cause']} | {str(row['after'])[:90]} |")
    L += ["", "## (c) D-41 sunken panels", "",
          f"HELD {x['low_m2']} .. {x['high_m2']} m2 (loop {x['recess_loop_m']} m); hosts "
          + ", ".join(f"{h['room']} {h['upturn_line']} {h['m2']} {h['restate']}" for h in x["hosts"])
          + f" (sum {x['hosts_released_m2']} m2). Designer: {x['designer_item']}. {x['statement']}.", "",
          f"Released quantities moved: {d['released_moved']}.", ""]
    return "\n".join(L)


# ------------------------------------------------------------------------------ --dxf re-measure (private drawing)
def remeasure(path):
    import ezdxf
    doc = ezdxf.readfile(path)
    db = doc.entitydb

    def se(h):
        e = db[h]
        return e.dxf.start, e.dxf.end

    def hy(h):
        s, e = se(h)
        if abs(s.y - e.y) > 1e-6:
            raise R.RuleError(f"{h} is not horizontal")
        return Decimal(repr(s.y))

    def vx(h):
        s, e = se(h)
        if abs(s.x - e.x) > 1e-6:
            raise R.RuleError(f"{h} is not vertical")
        return Decimal(repr(s.x))
    ay = hy("1280")
    if hy("1281") != ay or hy("12E6") != ay:
        raise R.RuleError("1280 / 1281 / 12E6 are not on one line")
    xw = Decimal(repr(max(se("12E6")[0].x, se("12E6")[1].x)))
    car_d = [("H", ay), ("V", vx("1291")), ("H", hy("1278")), ("V", vx("12A7")), ("H", hy("1285")),
             ("V", vx("12C9")), ("H", hy("12B9")), ("V", vx("12E2"))]
    car_w = car_d[:-1] + [("V", xw)]
    fd, fw = R.face(car_d, "0.001"), R.face(car_w, "0.001")
    r1, r2 = db["12EB"].dxf.radius, db["2F33"].dxf.radius
    if abs(r1 - r2) > 1e-6:
        raise R.RuleError("the two domes differ in radius")
    gap = (min(se("1281")[0].x, se("1281")[1].x) - max(se("1280")[0].x, se("1280")[1].x)) / 1000
    return {"face_dband_m2": str(fd["area_m2"]), "face_wallface_m2": str(fw["area_m2"]),
            "perimeter_m": str(fd["perimeter_m"]), "dome_r_mm": repr(r1), "door_gap_m": round(gap, 4),
            "handle_lengths_m": {h: round(se(h)[0].distance(se(h)[1]) / 1000, 4) for h in ROOF["handle_lengths_m"]}}


def main(argv):
    if "--dxf" in argv:
        print(json.dumps(remeasure(argv[argv.index("--dxf") + 1]), indent=1))
        return 0
    d = build()
    js = json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True, default=str) + "\n"
    m = md(d)
    if "--check" in argv:
        ok = (OUT / "T734_WP_H4_EVIDENCE.json").read_text(encoding="utf-8") == js and \
            (OUT / "T734_WP_H4_EVIDENCE.md").read_text(encoding="utf-8") == m
        print("T734 outputs", "AGREE" if ok else "DIFFER")
        return 0 if ok else 1
    OUT.mkdir(exist_ok=True)
    (OUT / "T734_WP_H4_EVIDENCE.json").write_text(js, encoding="utf-8")
    (OUT / "T734_WP_H4_EVIDENCE.md").write_text(m, encoding="utf-8")
    print(m)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
