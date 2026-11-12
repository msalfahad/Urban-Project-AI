"""T-720 development-villa builder: GROSS / COVERED FLOOR AREA per storey (missing family B2-03), the drawn denominator
of every per-m2 check (research, unwired; no BOQ quantity moved).

Reads only T720_DRAWN.json (own DXF read by handle this run, t720_extract.py, beside the released V2.9 engine's floor
plate of the same drawing), sha256-pinned (an edited input stops the build). Cited, not re-measured here: T-719 void
register (V-01 26.240, lift shaft 3.240 per storey), Q-67 (side passage; GF-roof panel 1.56), Q-68 (slabs over outside
air), OQ-04 (courts), D-48 (garden band 13.986, designer).

    python3 -I research/agents_t720/t720_alsenan.py           # writes out/T720_GROSS.json and .md
    python3 -I research/agents_t720/t720_alsenan.py --check   # rebuilds in memory, compares byte for byte
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t720_rules as R  # noqa: E402

DRAWN = HERE / "T720_DRAWN.json"
PIN = "4cd59d907ecf6f3d4c189f82d6fafeedbc5ee6e01d821b50c20c8fac8df83ed3"
OUT_JSON = HERE / "out" / "T720_GROSS.json"
OUT_MD = HERE / "out" / "T720_GROSS.md"


def r6(x):
    return None if x is None else round(float(x), 6)


def build():
    raw = DRAWN.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise SystemExit("T720_DRAWN.json differs from its pin: re-read the drawing with t720_extract.py first")
    d = json.loads(raw)
    o, ov, eng = d["outlines"], d["overlay"], d["engine"]
    sym = d["north_arrow"]["GF"]
    # ---- per storey gross (R-T720-1 / -2); the outlines are already areas: rows carry them through the rule
    floors = []
    gf_rows = [{"id": "GF house", "m2": o["GF_MAIN"]["m2"], "handles": o["GF_MAIN"]["handles"]},
               {"id": "GF annex (single storey)", "m2": o["GF_ANNEX"]["m2"], "handles": o["GF_ANNEX"]["handles"]}]
    spec = {"GF": gf_rows,
            "1F": [{"id": "1F", "m2": o["1F"]["m2"], "handles": o["1F"]["handles"]}],
            "2F": [{"id": "2F roof structures (stair, lift, maid room)", "m2": o["2F"]["m2"],
                    "handles": o["2F"]["handles"]}]}
    causes = {"GF": [("engine closes the side passage by two PASSAGE thresholds (OP-001 / OP-007): outside the envelope "
                      "by R-T720-4", -o["GF_PASSAGE"]["m2"])],
              "1F": [("1F east straight opening bridged on the face line B61 (engine follows frame line C37, 80 mm in)",
                      d["reveal_1F_east"]["m2"])],
              "2F": []}
    named_inside = {
        "GF": ["lift shaft 3.240 (T-719 V-03, stacked; not deducted: gross)",
               "garden band 13.986 inside the outer wall line (engine EXTERNAL 9.101 + MERGED 4.885; D-48 designer "
               "classification open; its cover is the GF roof slab per the Q-67 reading, cited)",
               "curved glazing bay on the pool court: outline follows the outermost glazing line 280 (bulge 0.867, "
               "r 2.330 m) as the engine plate does (its arc correction on the same polyline: 6.995 m2 out of the rectangle)"],
        "1F": ["V-01 ST-02 light well 26.240 (T-719; engine VOID 16.005 + flights seen 6.772 + residue 3.453): inside "
               "the 1F gross, not deducted", "lift shaft 3.240 (T-719 V-03)",
               "concave curved wall BD0 / BCD r 1.935 m: opening bridged on the same circle (R-T720-1)"],
        "2F": ["lift shaft 3.240 (T-719 V-03)", "ST-01 stair box inside (T-719 V-04)"]}
    total = 0.0
    for fl in ("GF", "1F", "2F"):
        rows = [{"id": r["id"], "state": "DRAWING-CONFIRMED", "m2": r6(r["m2"]), "handles": r["handles"]}
                for r in spec[fl]]
        own = sum(r["m2"] for r in spec[fl])
        total += own
        e = eng[fl]
        rec = R.reconcile(own, e["gross_floor_plate_m2"], causes[fl])
        floors.append({
            "floor": fl, "rows": rows, "gross_m2": r6(own), "state": "DRAWING-CONFIRMED",
            "engine_plate_m2": e["gross_floor_plate_m2"], "engine_plate_top_level_m2": e["plate_top_level_m2"],
            "engine_symbol_component_m2": r6(e["plate_top_level_m2"] - e["gross_floor_plate_m2"]),
            "reconcile": {k: (r6(v) if isinstance(v, float) else v) for k, v in rec.items()},
            "categories_sum_m2": r6(sum(e["categories_m2"].values())),
            "named_inside_not_deducted": named_inside[fl]})
    # ---- covered vs open (R-T720-3 / -4), GF ground
    p1, p2 = ov["1F_over_outside_GF_pieces"][0], ov["1F_over_outside_GF_pieces"][1]
    ground = {
        "plot_outer_face_m2": o["PLOT"]["m2"],
        "outside_GF_envelope_m2": ov["plot_outside_GF_envelope_m2"],
        "side_passage": {"m2": o["GF_PASSAGE"]["m2"], "rule": R.passage(thresholds=2),
                         "COVERED_BY_FLOOR_m2": ov["passage_under_1F_m2"],
                         "rest_m2": r6(o["GF_PASSAGE"]["m2"] - ov["passage_under_1F_m2"]),
                         "rest_state": "HELD (Q-67 reading: GF-roof slab panel 1.56 to the boundary beam + the 0.24 mouth "
                                       "band under the layer-5 boundary lines 86 / 105 / 106; slab outline not read here)",
                         "vs_Q67_m2": 5.64, "why_differs": "Q-67 5.64 = 1.20 x 4.70 from the inner face of the boundary "
                                                           "wall; here to the outer face line 86 (+1.20 x 0.20)"},
        "COVERED_BY_FLOOR": [
            {"what": "entrance zone under the 1F west wing (porch, entrance stair)", "m2": r6(p1["m2"] - p1["in_passage_m2"]),
             "vs_cited": {"Q-68 porch": 19.181, "why": "Q-68 includes the slab beyond the 1F walls (not read here)"}},
            {"what": "pool court strip and the GF curved bay under the 1F floor", "m2": r6(p2["m2"])}],
        "COVERED_BY_FLOOR_m2": ov["1F_outside_GF_and_passage_m2"],
        "COVERED_BY_SLAB_m2": None,
        "HELD_slabs_named_without_outline": ["Q-68 pool court slab projection (18.393 gross, VOID 4.373: cited)",
                                             "Q-68 1F roof-slab edges 6.791 (cited)", "Q-67 GF-roof panel over the "
                                             "passage 1.56 (cited)"],
        "outside_not_under_1F_m2": ov["plot_outside_GF_not_under_1F_m2"],
        "OPEN_TO_SKY_m2": None,
        "OPEN_TO_SKY_upper_bound_m2": r6(ov["plot_outside_GF_not_under_1F_m2"] - (o["GF_PASSAGE"]["m2"]
                                                                                  - ov["passage_under_1F_m2"])),
        "boundary_wall_band": "the plot outline is the outer face of the boundary walls; the courts of OQ-04 (167.714) "
                              "are measured inside them: not compared here"}
    roof = {"1F_roof_not_under_2F_m2": ov["1F_roof_not_under_2F_m2"], "state": "OPEN_TO_SKY (a roof, not a floor)",
            "GF_roof_not_under_1F_m2": ov["GF_not_under_1F_m2"], "2F_outside_1F_m2": ov["2F_outside_1F_m2"]}
    findings = [
        {"id": "F-T720-1", "verdict": "ENGINE_RIGHT", "what": "GF / 1F / 2F engine plates agree with the own handle read "
         "after the named causes, residual " + ", ".join(f"{f['floor']} {f['reconcile']['residual_m2']:+.6f}"
                                                         for f in floors) + " m2 (engine plate printed to 4 dp)"},
        {"id": "F-T720-2", "verdict": "ENGINE_WRONG (reconciliation only, no BOQ line)", "what":
         f"north-arrow block {sym['block']} (inserts 1612 / 19A2 / 19A3, lines on layers {'/'.join(sym['line_layers'])}) "
         "is read as a wall network on every plan: plate_top_level and the face categories carry 0.6581 m2 per plan "
         "(1.9743 m2 in all) that is not building (R-T720-2)"},
        {"id": "F-T720-3", "verdict": "RULE_DIFFERENCE", "what": "engine plate includes the side passage 5.880 (threshold "
         "closure); R-T720-4 / Q-67 A keep it beside the gross, covered 4.080 by the 1F floor"}]
    out = {"task": "T-720", "family": "B2-03", "status": "research, unwired; no quantity moved",
           "drawn_sha256": PIN, "floors": floors, "gross_all_storeys_m2": r6(total),
           "gf_ground": ground, "roofs": roof, "findings": findings, "align": d["align"],
           "printed_dims": d["printed_dims"]}
    return out


def md(o):
    L = ["# T-720 gross / covered floor area per storey (B2-03; research, unwired)", "",
         "Own read by handle on the architectural DXF beside the released V2.9 floor plate. Areas m2. Gross = to the "
         "outer face of the external envelope (R-T720-1); voids / shafts named, not deducted.", "",
         "| storey | component | gross | engine plate | own - engine | named causes | residual | state |",
         "|---|---|---|---|---|---|---|---|"]
    for f in o["floors"]:
        rc = f["reconcile"]
        comp = " + ".join(f"{r['id']} {r['m2']:.6f}" for r in f["rows"])
        L.append(f"| {f['floor']} | {comp} | {f['gross_m2']:.6f} | {f['engine_plate_m2']:.4f} | "
                 f"{rc['own_minus_engine_m2']:+.6f} | {rc['named_m2']:+.6f} | {rc['residual_m2']:+.6f} | {rc['state']} |")
    L += ["", f"All storeys (enclosed gross): **{o['gross_all_storeys_m2']:.6f}**", "",
          "## GF ground outside the envelope (R-T720-3 / -4)", ""]
    g = o["gf_ground"]
    L.append(f"- plot to the outer face of the boundary walls {g['plot_outer_face_m2']:.3f}; outside the GF envelope "
             f"{g['outside_GF_envelope_m2']:.6f}")
    sp = g["side_passage"]
    L.append(f"- side passage {sp['m2']:.3f} ({sp['rule']}): under the 1F floor {sp['COVERED_BY_FLOOR_m2']:.3f}, rest "
             f"{sp['rest_m2']:.3f} {sp['rest_state']}")
    for c in g["COVERED_BY_FLOOR"]:
        L.append(f"- COVERED_BY_FLOOR: {c['what']} {c['m2']:.6f}")
    L.append(f"- HELD slabs named without an outline: {'; '.join(g['HELD_slabs_named_without_outline'])}")
    L.append(f"- not under the 1F floor {g['outside_not_under_1F_m2']:.6f}; OPEN_TO_SKY HELD (upper bound "
             f"{g['OPEN_TO_SKY_upper_bound_m2']:.6f}) until the slab projections are read")
    r = o["roofs"]
    L += [f"- 1F roof not under the 2F {r['1F_roof_not_under_2F_m2']:.6f} ({r['state']}); GF roof not under the 1F "
          f"{r['GF_roof_not_under_1F_m2']:.6f}", "", "## Named inside, not deducted", ""]
    for f in o["floors"]:
        for n in f["named_inside_not_deducted"]:
            L.append(f"- {f['floor']}: {n}")
    L += ["", "## Second source: printed dimensions on the same sheets", ""]
    for x in o["printed_dims"]:
        L.append(f"- {x['dim']}: faces {' / '.join(x['faces'])} own {x['own_m']:.3f} m vs printed {x['printed_m']:.3f} m "
                 f"({x['diff_mm']:+.3f} mm)")
    L += ["", "## Findings", ""]
    for x in o["findings"]:
        L.append(f"- {x['id']} {x['verdict']}: {x['what']}")
    return "\n".join(L) + "\n"


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    o = build()
    js = json.dumps(o, indent=1, sort_keys=True) + "\n"
    m = md(o)
    if "--check" in argv:
        ok = OUT_JSON.read_text() == js and OUT_MD.read_text() == m
        print("T720 check", "IDENTICAL" if ok else "DIFFERS")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(js)
    OUT_MD.write_text(m)
    print(m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
