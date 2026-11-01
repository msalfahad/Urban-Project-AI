"""T-437 Alsenan: the 'other unexplained concrete parts' of the r4 roll-up (T-428 verdict) tested construction by
construction (research only: no engine, candidate, line, rule version or released cell changes).

Inputs (all committed): research/agents_t437/ALSENAN_T437_INPUT.json (drawing-derived lengths by DXF handle, own read of
'ST7757 dxf.dxf' 9f9d1179 this run; pool levels of merged T-183 r2), tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json
(his rows, read by sheet / row at run time, never retyped), research/agents_t428/summary_t428.json (the parts),
research/agents_t395/summary_t395.json (the beam marks). Output: research/agents_t437/summary_t437.json (m3, m, handles,
classes; no coordinate, no workbook text).

    python3 -I research/agents_t437/t437_alsenan.py [--write]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t437_rules as R  # noqa: E402

RES = HERE.parent
ROOT = HERE.parents[1]
RAW = ROOT / "tests" / "alsenan" / "registers_b1" / "FREELANCER_RAW_ROWS.json"


def load():
    inp = json.loads((HERE / "ALSENAN_T437_INPUT.json").read_text(encoding="utf-8"))
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    rows = {(r["file"], r["sheet"], r["row"]): {k: v["v"] for k, v in r["cells"].items()} for r in raw["rows"]}
    t428 = json.loads((RES / "agents_t428" / "summary_t428.json").read_text(encoding="utf-8"))
    t395 = json.loads((RES / "agents_t395" / "summary_t395.json").read_text(encoding="utf-8"))
    return inp, rows, t428, t395


def cell(rows, sheet, row, col):
    return rows[("RC", sheet, row)][f"{col}{row}"]


def check_parts(inp, t428):
    """Every part figure of this row equals the merged T-428 unexplained-left figure (component, m3)."""
    left = {}
    for p in t428["unexplained_left"]:
        left.setdefault(p["component"], []).append(p["m3"])
    for comp, m3 in inp["parts_t428"].items():
        assert any(abs(m3 - x) < 1e-9 for x in left.get(comp, [])), (comp, m3, left.get(comp))
    tot = sum(v for k, v in inp["parts_t428"].items() if k != "CL-1F")
    assert abs(tot - inp["row_total_m3"]) <= R.TOL_PART + 1e-9, (tot, inp["row_total_m3"])
    return R.r6(tot)


def pool(inp, rows):
    P = inp["pool"]
    sh = P["his_rows"]["sheet"]
    r = P["his_rows"]["walls_row"]
    L, H, t = cell(rows, sh, r, "B"), cell(rows, sh, r, "C"), cell(rows, sh, r, "D")
    pumpH = cell(rows, sh, P["his_rows"]["pump_walls_row"], "C")
    wall = P["rim_level"] - P["base_top_level"]                         # 1.20 RC wall above the base top
    under = P["screed"] + P["membrane"] + P["blinding"]
    upstand_over_deck_structure = P["rim_level"] - P["deck_structure_top_level"]
    cons = [
        {"name": "rim to RC base top (the RC wall, R-POOL-4)", "value": wall, "cls": "ENGINE_BASIS"},
        {"name": "rim to RC base underside (wall + base)", "value": wall + P["base_thickness"], "cls": "BASE_AGAIN"},
        {"name": "rim to the screed underside", "value": wall + P["base_thickness"] + P["screed"], "cls": "NON_RC"},
        {"name": "rim to the membrane underside", "value": wall + P["base_thickness"] + P["screed"] + P["membrane"],
         "cls": "NON_RC"},
        {"name": "rim to formation (base + screed 0.05 + membrane 0.05 + blinding 0.10 = the dig depth below the rim)",
         "value": wall + P["base_thickness"] + under, "cls": "NOT_RC_WALL"},
        {"name": "rim to base underside + the upstand above the deck structure counted again",
         "value": wall + P["base_thickness"] + upstand_over_deck_structure, "cls": "NOT_RC_WALL"},
        {"name": "deck finish to formation", "value": P["deck_finish_level"] - P["base_top_level"] + P["base_thickness"]
         + under, "cls": "NOT_RC_WALL_DECK"},
        {"name": "finished depth 1.15 + build-up 0.05 + base 0.40 (= rim to base underside)",
         "value": (P["rim_level"] - P["finished_floor_level"]) + (P["finished_floor_level"] - P["base_top_level"])
         + P["base_thickness"], "cls": "BASE_AGAIN"},
    ]
    res = R.construction_test(H, cons, tol=R.precision_tol(H))
    rest = H - wall - P["base_thickness"]                                  # 0.20 m beyond rim .. base underside
    part = -R.r6(P["wall_band_m2"] * rest)
    assert abs(part - P["t385_split_m3"]["REST"]) <= R.TOL_PART, (part, P["t385_split_m3"])
    # the T-385 split re-adds to the wall residual
    eng = P["engine_wall_m3"]
    assert abs(sum(P["t385_split_m3"].values()) - (eng - L * H * t)) <= 2e-6
    return {"part": "PL-WALLS", "m3": P["t385_split_m3"]["REST"], "rest_height_m": R.r6(rest),
            "band_m2": P["wall_band_m2"], "construction": res, "his_pump_room_wall_height_equal": pumpH == H,
            "subparts": [{"id": "PLW-H020", "m3": P["t385_split_m3"]["REST"], "verdict": "UNRESOLVED",
                          "proposal": "ENGINE_RIGHT", "why": "0.20 m x wall band 2.356726 m2: two exact constructions "
                          "(rim to formation; rim to base underside + upstand again), both put the 0.20 m outside the "
                          "RC wall above the base top: NOT RC wall concrete either way (cause ambiguous)"}]}


def beams(inp, rows, t395):
    B = inp["beams"]
    sh = B["sheet"]
    mk = {(m["floor"], m["mark"]): m for m in t395["marks"]}
    for fl, d in B["t395_untraced_m3"].items():
        for m, v in d.items():
            assert abs(mk[(fl, m)]["LENGTH_UNTRACED"] - v) < 1e-9, (fl, m)
        assert abs(sum(d.values()) - t395["floors"][fl]["terms_m3"]["LENGTH_UNTRACED"]) <= 2e-6
    for k, v in B["t395_through_m3"].items():
        fl, m = k.split(":")
        assert abs(mk[(fl, m)]["THROUGH_SUPPORT"] - v) < 1e-9, k
    out = {"subparts": [], "tests": {}}

    # STEP rows (R-T437-5)
    for key, d in B["rounding_rows"].items():
        fl, m = key.split(":")
        r = d["rows"][0]
        b, D = d["section"]
        his = cell(rows, sh, r, "D")
        assert (cell(rows, sh, r, "B"), cell(rows, sh, r, "C")) == (b, D), key
        eng = d.get("engine_L_eff_m") or d["engine_L_eff_m_matched"]
        step = 2 * R.precision_tol(his)
        if key == "1F:B6":                                       # his B6 row binds the 4.3722 run (T-395 RUN_COUNT)
            eng = 0.5465228808839456 / (b * D)
            step = 0.01
        else:
            step = 0.05                                          # his lengths printed on a 0.05 m grid on this sheet
        w = R.within_step(engine_len=eng, his_len=his, step=step)
        m3 = R.r6((eng - his) * b * D)
        assert abs(m3 - B["t395_untraced_m3"][fl][m]) <= 2e-6, (key, m3)
        out["tests"][key] = w
        assert w["is_step"], key
        out["subparts"].append({"id": f"BM{fl}-{m}-STEP", "floor": fl, "m3": B["t395_untraced_m3"][fl][m],
                                "verdict": "UNRESOLVED", "proposal": "ENGINE_RIGHT",
                                "why": f"STEP: his row {w['diff_m']} m short of the drawn face-to-face length, inside "
                                       f"one {step} m step of his printing"})

    # 1F CB12 (R-T437-1 / -2)
    C = B["CB12_1F"]
    b, D = C["section"]
    his = cell(rows, sh, C["his_row"], "D")
    assert (cell(rows, sh, C["his_row"], "B"), cell(rows, sh, C["his_row"], "C")) == (b, D)
    cons = [{"name": n, "value": v, "cls": n} for n, v in C["constructions_m"].items()]
    ct = R.construction_test(his, cons, tol=R.precision_tol(his))
    through_claimed = -B["t395_through_m3"]["1F:CB12"] / (b * D)
    tb = R.through_bound(his_len=his, engine_len=C["engine_L_eff_m"], outermost_len=max(C["constructions_m"].values()),
                         allowance_claimed=through_claimed)
    resid = R.r6((C["engine_L_eff_m"] - his) * b * D)
    assert abs(resid - (B["t395_through_m3"]["1F:CB12"] + B["t395_untraced_m3"]["1F"]["CB12"])) <= 2e-6
    out["tests"]["1F:CB12"] = {"construction": ct, "through_bound": tb,
                               "untraced_lower_bound_m3": R.r6(tb["untraced_lower_bound_m"] * b * D),
                               "t395_allowance_over_room_m3": R.r6(tb["allowance_over_room_m"] * b * D),
                               "mark_residual_m3": resid}
    out["subparts"].append({"id": "BM1F-CB12", "floor": "1F", "m3": B["t395_untraced_m3"]["1F"]["CB12"],
                            "verdict": "UNRESOLVED", "proposal": "UNRESOLVED",
                            "why": "his length passes the outermost drawn extent of CB12 (outer faces of the end "
                                   "carriers 5C1 / 5BE, 12.000 m) by 1.000 m: no drawn construction reaches it; the "
                                   "untraced part is at least 0.1875 m3 (T-395's -0.160962 is a lower figure because "
                                   "its allowance passes the drawn room by 0.141544 m, F-T437-2)"})

    # 2F B2 (R-T437-3)
    Q = B["B2_2F"]
    b, D = Q["section"]
    his_rows = []
    for r in Q["his_rows"]:
        assert (cell(rows, sh, r, "B"), cell(rows, sh, r, "C")) == (b, D)
        his_rows.append((cell(rows, sh, r, "D"), cell(rows, sh, r, "F")))
    room = R.r6(sum(Q["through_room_items_m"].values()))
    cb = R.count_binding(his_rows, Q["drawn_runs_m"], through_room=room)
    assert cb["class"] == "COUNT", cb
    mark_resid = R.r6((sum(Q["drawn_runs_m"]) - sum(L * n for L, n in his_rows)) * b * D)
    assert abs(mark_resid - (B["t395_through_m3"]["2F:B2"] + B["t395_untraced_m3"]["2F"]["B2"])) <= 2e-6
    assert abs(mark_resid + cb["left_over_m"] * b * D) <= 2e-6
    out["tests"]["2F:B2"] = {"binding": cb, "mark_residual_m3": mark_resid, "labels": len(Q["labels_on_runs"]),
                             "drawn_runs": len(Q["drawn_runs_m"])}
    out["subparts"].append({"id": "BM2F-B2", "floor": "2F", "m3": B["t395_untraced_m3"]["2F"]["B2"],
                            "verdict": "UNRESOLVED", "proposal": "ENGINE_RIGHT",
                            "why": "COUNT: four labelled B2 runs drawn (2.5 / 3.0 / 1.8 / 3.0), each equal to one of his "
                                   "rows exactly; one 2.500 m row is left over, longer than the whole through-support "
                                   "room of the mark (1.3995 m); the whole mark -0.200 m3 is that row (F-T437-1)"})

    # GF B2 (R-T437-1 per row)
    G = B["B2_GF"]
    b, D = G["section"]
    allc = [{"name": f"{run}: {n}", "value": v, "cls": f"{run}: {n}"} for run, rr in G["runs"].items()
            for n, v in rr.items()]
    per = {}
    for r in G["his_rows"]:
        L = cell(rows, sh, r, "D")
        per[str(r)] = R.construction_test(L, allc, tol=R.precision_tol(L))
    out["tests"]["GF:B2"] = per
    out["subparts"].append({"id": "BMGF-B2", "floor": "GF", "m3": B["t395_untraced_m3"]["GF"]["B2"],
                            "verdict": "UNRESOLVED", "proposal": "UNRESOLVED",
                            "why": "two of his three rows are drawn readings exactly (column 341 face to line 278; edge "
                                   "29E: through-support, inside the T-395 traced term); the third passes the longest "
                                   "drawn reading of the x 57.2 run (edge 286, 4.500 m, which already runs through B1's "
                                   "own 0.80 m run and column 36B) by 0.100 m: untraced 0.008 .. 0.072 m3"})

    # GF B7 (R-T437-1 on subsets)
    S = B["B7_GF"]
    els = S["elements_m"]
    hits = {}
    for r in S["his_rows"]:
        L = cell(rows, sh, r, "D")
        hits[str(r)] = [[h[0], [list(x) for x in h[1]]] for h in R.subset_constructions(els, L, tol=R.precision_tol(L))]
    pairs = []
    for a in hits[str(S["his_rows"][0])]:
        for c in hits[str(S["his_rows"][1])]:
            pa, pc = {x[0] for x in a[1]}, {x[0] for x in c[1]}
            if not pa & pc:
                pairs.append([a, c])
    out["tests"]["GF:B7"] = {"hits_per_row": {k: len(v) for k, v in hits.items()}, "disjoint_pairs": len(pairs),
                             "first_hits": {k: v[:3] for k, v in hits.items()}}
    out["subparts"].append({"id": "BMGF-B7", "floor": "GF", "m3": B["t395_untraced_m3"]["GF"]["B7"],
                            "verdict": "UNRESOLVED", "proposal": "UNRESOLVED",
                            "why": f"each of his two B7 rows alone is reproduced by several drawn sums within his "
                                   f"precision ({len(hits[str(S['his_rows'][0])])} / {len(hits[str(S['his_rows'][1])])}), "
                                   f"but {len(pairs)} pair of them uses disjoint drawn pieces: no consistent "
                                   "construction of both rows (his row with no location, T-252); never the nearest"})
    return out


def boundary(inp, rows):
    Bd = inp["boundary"]
    out = {}
    U = Bd["upper_gb"]
    his = cell(rows, U["his_row"]["sheet"], U["his_row"]["row"], "C")
    seg = U["7FE_segments_m"]
    assert abs(seg[0] + seg[1] + seg[2] - U["constructions_m"]["7FE outer run 2.45 + 31.37 + 8.30"]) < 1e-9
    assert abs(seg[4] + seg[5] + seg[6] - U["constructions_m"]["7FE inner run 2.25 + 30.97 + 8.10"]) < 1e-9
    cls = {"7FE axis (band area 8.344 / 0.20)": "BAND_SOLID", "7FE outer run 2.45 + 31.37 + 8.30": "BAND_SOLID"}
    cons = [{"name": n, "value": v, "cls": cls.get(n, n)} for n, v in U["constructions_m"].items()]
    cons += [{"name": n, "value": v, "cls": n, "mixed_faces": True} for n, v in U["mixed_m"].items()]
    ut = R.construction_test(his, cons, tol=R.precision_tol(his))
    part_gb = R.r6(-(his - U["constructions_m"]["7FE axis (band area 8.344 / 0.20)"]) * U["his_section"][0]
                   * U["his_section"][1])
    assert abs(part_gb - inp["parts_t428"]["GB-BOUNDARY"]) <= 2e-6
    out["upper_gb"] = ut
    Lb = Bd["lower_band"]
    his2 = cell(rows, Lb["his_row"]["sheet"], Lb["his_row"]["row"], "D")
    cons2 = [{"name": n, "value": v, "cls": n} for n, v in Lb["constructions_m"].items()]
    cons2 += [{"name": n, "value": v, "cls": n, "mixed_faces": True} for n, v in Lb["mixed_m"].items()]
    lt = R.construction_test(his2, cons2, tol=R.precision_tol(his2))
    part_bw = R.r6(-(his2 - Lb["constructions_m"]["axis 91.94 less axis crossings 21.45 (owner method A free length)"])
                   * Lb["his_section"][0] * Lb["his_section"][1])
    assert abs(part_bw - inp["parts_t428"]["BW-BAND"]) <= 2e-6
    out["lower_band"] = lt
    out["subparts"] = [
        {"id": "GBB-LEN", "m3": inp["parts_t428"]["GB-BOUNDARY"], "verdict": "UNRESOLVED",
         "proposal": "ENGINE_RIGHT" if ut["status"] == "TRACED" else "UNRESOLVED",
         "why": "his length printed to whole metres: within half a metre the 7FE axis (41.72) and the 7FE outer run "
                "(42.12) both reproduce it; the band solid is its area 8.344 m2 / 0.20 = 41.72 m either way (the outer "
                "run is not the solid's length): not boundary concrete (cause ambiguous)"},
        {"id": "BWB-LEN", "m3": inp["parts_t428"]["BW-BAND"], "verdict": "UNRESOLVED", "proposal": "UNRESOLVED",
         "why": "no construction within 0.05 m on one face (axis free 70.49, inner free 70.09, outer free 72.59); "
                "the only near figures mix the outer face with inner-face crossings (71.69) or the axis with outer-face "
                "crossings (71.79): refused as physical constructions"},
    ]
    return out


def c9(inp):
    C = inp["c9"]
    m3 = R.r6(C["count"] * (C["engine_section_m2"] - C["his_section_m2"]) * C["his_height_m"])
    assert abs(m3 - inp["parts_t428"]["CL-1F"]) <= 2e-6
    return {"id": "C9-SECTION", "m3": inp["parts_t428"]["CL-1F"], "verdict": "UNRESOLVED", "proposal": "UNRESOLVED",
            "restated": True, "why": "2 x (0.18 - 0.20) m2 x 3.45 m (T-394, merged): three readings of one member "
            "(schedule 1ST 20 x 90 = engine, drawn outline 679 0.25 x 1.00, his 0.20 x 1.00); designer item; not "
            "re-measured"}


def build():
    inp, rows, t428, t395 = load()
    tot = check_parts(inp, t428)
    pl = pool(inp, rows)
    bm = beams(inp, rows, t395)
    bd = boundary(inp, rows)
    cc = c9(inp)
    groups = {"PL-WALLS": pl["subparts"],
              "BM-GF": [s for s in bm["subparts"] if s["floor"] == "GF"],
              "BM-1F": [s for s in bm["subparts"] if s["floor"] == "1F"],
              "BM-2F": [s for s in bm["subparts"] if s["floor"] == "2F"],
              "GB-BOUNDARY": [s for s in bd["subparts"] if s["id"] == "GBB-LEN"],
              "BW-BAND": [s for s in bd["subparts"] if s["id"] == "BWB-LEN"],
              "CL-1F": [cc]}
    for comp, subs in groups.items():
        R.check_split(inp["parts_t428"][comp], subs)
    ids = [s["id"] for subs in groups.values() for s in subs]
    assert len(ids) == len(set(ids))
    R.disjoint(list(groups) + ids, inp["other_rows_part_ids"])
    allsub = [s for comp, subs in groups.items() if comp != "CL-1F" for s in subs]
    prop = {}
    for s in allsub:
        prop[s["proposal"]] = R.r6(prop.get(s["proposal"], 0.0) + s["m3"])
    assert abs(sum(prop.values()) - tot) <= 2e-6
    return {
        "schema": "URBAN_T437_SUMMARY_V1",
        "basis": "T-428 r4 unexplained-left parts (MERGED ea8f5ae5) re-read construction by construction; drawing 'ST7757 "
                 "dxf.dxf' 9f9d1179 (own read), pool levels T-183 r2; his rows from the committed raw-rows file",
        "row_total_m3": tot,
        "c9_restated_m3": cc["m3"],
        "parts": {comp: {"m3": inp["parts_t428"][comp], "subparts": subs} for comp, subs in groups.items()},
        "by_proposal_m3": prop,
        "tests": {"pool": pl["construction"], "pool_rest_height_m": pl["rest_height_m"],
                  "pool_pump_walls_same_height": pl["his_pump_room_wall_height_equal"], "beams": bm["tests"],
                  "boundary": {k: v for k, v in bd.items() if k != "subparts"}},
        "findings": {
            "F-T437-1": "2F B2: T-395's THROUGH_SUPPORT -0.112760 m3 on the mark is the same left-over 2.500 m row as "
                        "the untraced -0.087240 (mark -0.200000 = 2.5 x 0.20 x 0.40); his four other rows are the "
                        "drawn face-to-face runs exactly, so no length on this mark runs through a support. Proposal: "
                        "re-class the -0.112760 to COUNT (ENGINE_RIGHT) in the next roll-up; no figure moved here.",
            "F-T437-2": "1F CB12: T-395's through allowance 1.359397 m passes the drawn room between the valued length "
                        "10.782147 m and the outer faces of the end carriers 12.000 m (1.217853 m) by 0.141544 m "
                        "(0.026539 m3): the valued length already holds 0.132147 m of beside-support plan (R-T437-2). "
                        "The untraced part is at least 0.187500 m3, not 0.160962; no figure moved here.",
            "O-T437-1": "GF: B4 edges 2B2 / 2B3 run 0.500 m past column 353 to line 484, where the B7 arc 47D begins; "
                        "that 0.20 x 0.50 m plan is in no beam line (B4 BAND0030.1 stops at 353, the arc band BAND0049 "
                        "starts at 484): 0.050 m3 at B4's 0.50 depth .. 0.075 m3 at B7's 0.75; slab coverage not checked. "
                        "For the Checker / lane I (candidate GAP); no figure moved.",
        },
    }


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    s = build()
    txt = json.dumps(s, indent=1, ensure_ascii=False, sort_keys=True)
    if "--write" in argv:
        (HERE / "summary_t437.json").write_text(txt + "\n", encoding="utf-8")
    print(json.dumps({"row_total_m3": s["row_total_m3"], "by_proposal_m3": s["by_proposal_m3"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
