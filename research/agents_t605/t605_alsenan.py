"""T-605 on the development villa: every footing pair that overlaps or touches, from the structural DXF (Drive
'Alsenan chalet project' / 'ST7757 dxf.dxf', decoded into .work/private; sha256 prefix 9f9d1179 checked by the
T-597 reader, which this script reuses for the FOUNDATION PLAN outlines and the FT / FTB schedule).

Own reads: drawn outline per footing (the EXACT closed polyline where it is not a rectangle, e.g. the notched FN
180C; T-597 carried that one as its bounding box, which was harmless for a union but not for a per-footing plan),
schedule L x W x H. Printed relations cited (not re-read): ST p.13 blinding projection 0.10 (T-170 / T-206) and the
common footing bottom stack (formation + 0.10 blinding + 0.07 underlay = footing bottom for every isolated type,
T-206 r2 table). The lift raft FF (D-43) and the open outline F10 + F 1B1B (Q-31 C) stay HELD.

    .work/venv/bin/python -I research/agents_t605/t605_alsenan.py .work/private/st7757.dxf
      -> research/agents_t605/out/T605_FOOTING_PAIRS.json (handles, sizes, m2 / m3 only; no client data)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "agents_t597"))

import footing_overlap_v1 as FO  # noqa: E402
import t597_alsenan as R  # noqa: E402

PROJ = 0.10
BOTTOM_ABOVE_FORMATION = 0.17          # T-206 r2: same for every isolated footing type
HELD_IDS = {"1B1B": "F10 + F open outline (Q-31 C)", "1B2B": "FF lift raft (D-43): bottom not in the stack"}

# candidate of record (ARCH_TAKEOFF_V3.0.58; structural lines = research/agents_t507/out/LINE_INDEX_V3_0_57.json,
# unchanged by V3.0.58): footing lines by outline, blinding per footing (T-478 s.6), footing formwork class
ENGINE = {
    "footing_m3": {"180F": 5.049, "180C": 0.258, "1B24": 7.2, "10F0": 0.3},
    "footing_lines": {"180F": "L-35da88665bf36b89a8fc", "180C": "L-d2c75eb10451e4dd1db5",
                      "1B24": "L-10f3cd1eb0f81a3892f2", "10F0": "L-f6af8a29e2c1b5fdcfd0"},
    "footing_pads_total_m3": 64.304,
    "blinding_footings_m3": 12.734438, "blinding_in_plot_m2": 127.344375,
    "blinding_per_footing_m3": {"180F": 1.044, "180C": 0.111},
    "footing_formwork": "HELD (OQ10 formed / earth-cast; every footing FW line HELD blank)",
}
FREELANCER = {"FN_rows_m3": 4 * 1.0 * 1.0 * 0.30, "note": "four FN rows at the schedule 1.00 x 1.00 x 0.30 (T-551)"}


def footings(d):
    out = {}
    for h, o in d["outlines"].items():
        lab, _ = R.label_of(d, h, o["geom"])
        typ = "/".join(lab) if lab else None
        if typ is None or (typ not in d["sched"] and typ != "F10/F"):
            continue
        g = o.get("exact") if o.get("exact") is not None else o["geom"]
        sched = d["sched"].get(typ)
        held = h in HELD_IDS
        out[h] = (typ, FO.Footing(fid=h, outline=None if h == "1B1B" else list(g.exterior.coords)[:-1],
                                  depth=None if sched is None else sched[2],
                                  bottom=None if held else BOTTOM_ABOVE_FORMATION,
                                  sched_LW=None if sched is None else sched[:2], unit="m"))
    return out


def run(dxf):
    d = R.read(dxf)
    F = footings(d)
    ids = sorted(F)
    rows = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            fa, fb = F[a][1], F[b][1]
            ga, gb = FO.polygon(fa), FO.polygon(fb)
            if ga is None or gb is None:
                ref = ga if ga is not None else gb
                # the open outline's bounding box is used ONLY to find neighbours, never as a plan
                bb = d["outlines"][a if ga is None else b]["geom"]
                if ref is not None and ref.distance(bb) <= 2 * PROJ + 1e-9:
                    rows.append({"pair": [a, b], "types": [F[a][0], F[b][0]],
                                 "status": "HELD: " + HELD_IDS.get(a if ga is None else b, "outline not drawn"),
                                 "bbox_gap_m": round(ref.distance(bb), 6)})
                continue
            if ga.distance(gb) > 2 * PROJ + 1e-9:
                continue
            r = FO.pair(fa, fb, PROJ)
            r["types"] = [F[a][0], F[b][0]]
            for h in (a, b):
                if h in HELD_IDS:
                    r.setdefault("held", []).append(HELD_IDS[h])
            sched = [F[h][1].sched_LW for h in (a, b)]
            r["schedule_m2"] = [round(s[0] * s[1], 6) for s in sched]
            rows.append(r)
    valued = [F[h][1] for h in ids if h not in HELD_IDS]
    # concrete: every drawn closed outline with a scheduled depth (the FF raft too: its plan and H are drawn /
    # scheduled; only its bottom is outside the stack, and it has no neighbour within 2p)
    conc = FO.footing_concrete(valued + [F["1B2B"][1]])
    bl_union, bl_sum, bl_held = FO.blinding_plan(valued, PROJ)
    # the in-plot clip (R-T597-3) for the engine comparison
    from shapely.ops import unary_union
    gun = unary_union([FO.grown(FO.polygon(f), PROJ) for f in valued])
    bl_in = gun.intersection(d["plot"]).area
    # notched pair: per-footing blinding (owner rule R-T605-3)
    g9, gN = FO.polygon(F["180F"][1]), FO.polygon(F["180C"][1])
    G9, GN = FO.grown(g9, PROJ), FO.grown(gN, PROJ)
    pair_9n = [r for r in rows if set(r["pair"]) == {"180F", "180C"}][0]
    pair_8n = [r for r in rows if set(r["pair"]) == {"1B24", "10F0"}][0]
    nb = {"180F": round(G9.area * 0.10, 6), "180C": round(GN.difference(G9).area * 0.10, 6)}
    # side forms of the notched pair: summed faces vs each interface once / none
    pair_forms = {"summed_faces_m2": round(g9.length * 0.55 + gN.length * 0.30, 6),
                  "interface_once_m2": FO.side_forms([F["180F"][1], F["180C"][1]], True),
                  "interface_none_m2": FO.side_forms([F["180F"][1], F["180C"][1]], False),
                  "schedule_rectangle_FN_faces_m2": round(4 * 1.0 * 0.30, 6)}
    pads = round(sum(v for k, v in conc.items() if v is not None and "|" not in k), 6)
    schedule_sum = round(sum(F[h][1].sched_LW[0] * F[h][1].sched_LW[1] * F[h][1].depth for h in ids
                             if h != "1B1B"), 6)
    out = {
        "schema": "T-605 footing overlap: handles, sizes, m2 / m3 only (no client data)",
        "drawing": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' sha256 " + d["sha8"],
        "footings_valued": len(valued), "held": HELD_IDS,
        "concrete_outlines": len([k for k in conc if "|" not in k]),
        "pairs_within_2p": rows,
        "concrete": {"pads_drawn_once_m3": pads, "pads_schedule_rect_sum_m3": schedule_sum,
                     "schedule_minus_drawn_m3": round(schedule_sum - pads, 6), "engine_pads_m3": ENGINE["footing_pads_total_m3"],
                     "engine_minus_own_m3": round(ENGINE["footing_pads_total_m3"] - pads, 6),
                     "per_pair": {"180F": conc["180F"], "180C": conc["180C"], "1B24": conc["1B24"], "10F0": conc["10F0"]}},
        "blinding": {"union_m2": bl_union, "sum_m2": bl_sum, "overlap_m2": round(bl_sum - bl_union, 6),
                     "in_plot_m2": round(bl_in, 6), "in_plot_m3": round(bl_in * 0.10, 6),
                     "engine_m3": ENGINE["blinding_footings_m3"],
                     "engine_minus_own_m3": round(ENGINE["blinding_footings_m3"] - bl_in * 0.10, 6),
                     "notched_pair_per_footing_m3": nb, "engine_notched_pair_m3": ENGINE["blinding_per_footing_m3"]},
        "formwork_notched_pair": pair_forms,
        "engine": ENGINE, "freelancer": FREELANCER,
    }
    out["verdicts"] = [
        {"pair": "F9 180F / FN 180C", "item": "footing concrete", "engine_m3": 5.307, "own_m3": round(conc["180F"] + conc["180C"], 6),
         "his_m3": round(5.049 + 0.30, 6), "verdict": "ENGINE_RIGHT (AGREE with the drawing); his FN row bills the "
         "0.40 x 0.35 x 0.30 = 0.042 m3 piece F9 already holds"},
        {"pair": "F9 180F / FN 180C", "item": "blinding", "engine_m3": 1.155, "own_m3": round(nb["180F"] + nb["180C"], 6),
         "verdict": "AGREE (union, F9 owns 0.19 m2: drawn whole and deeper); his plate is a RULE_DIFFERENCE (T-478)"},
        {"pair": "F9 180F / FN 180C", "item": "footing side forms", "engine": "HELD OQ10",
         "own_m2": [pair_forms["interface_none_m2"], pair_forms["interface_once_m2"]],
         "verdict": "NO_COMPARISON (engine HELD); summed faces %.4f refused (interface twice)" % pair_forms["summed_faces_m2"]},
        {"pair": "F8 1B24 / FN 10F0", "item": "concrete / forms", "verdict": "NO_COMMON_PRISM: neat outlines %.3f m apart"
         % pair_8n["gap_m"]},
        {"pair": "F8 1B24 / FN 10F0", "item": "blinding", "overlap_m2": pair_8n["blinding"]["overlap_m2"],
         "verdict": "AGREE (union); owner F8 (deeper 0.50 vs 0.30, T-478)"},
    ]
    return out


def main(argv):
    if len(argv) != 2:
        raise SystemExit(__doc__)
    out = run(argv[1])
    od = HERE / "out"
    od.mkdir(exist_ok=True)
    (od / "T605_FOOTING_PAIRS.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: out[k] for k in ("concrete", "blinding", "formwork_notched_pair")}, indent=1))
    for r in out["pairs_within_2p"]:
        print(json.dumps(r))


if __name__ == "__main__":
    main(sys.argv)
