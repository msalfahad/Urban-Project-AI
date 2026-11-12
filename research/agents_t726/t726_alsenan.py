"""T-726 development-villa builder: the PLASTER SHAFT RESIDUAL 13.50 m2 (UNRESOLVED since T-173) reconciled against the
T-719 void register and an own handle read of the stair-house family (research, unwired; no quantity moved).

Reads only repository files, each sha256-pinned (an edited input stops the build):
  research/agents_t726/T726_DRAWN.json               own DXF read by handle this run (t726_extract.py)
  tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json his plaster (PLS) / paint (PNT) statements as parsed cells: only
                                                     the numeric I / J / F / H cells are read (no text is copied)
  research/agents_t703/out/LINE_INDEX_V3_0_72.json   candidate of record V3.0.72 (T-703)
  research/agents_t709/out/T709_RESIDUALS.json       merged T-709 chain perimeters / room face lengths (1F-13, 2F-01)
Typed here (cited, merged, not re-measured): T-173 face heights (N 12.74 .. 13.44, S-GF +1.00 .. +5.34 - b) and its
freelancer bridge (south +20.11, north -2.64, west / east -3.62); section A-A level marks (T-709 list); T-701 room
plaster heights 1F 3.99 / 2F 3.79 and the like-for-like totals; T-709 ST-02 well runs 4.00 / 7.02; T-680 pier returns.

    python3 -I research/agents_t726/t726_alsenan.py           # writes out/T726_SHAFT_RESIDUAL.json and .md
    python3 -I research/agents_t726/t726_alsenan.py --check   # rebuilds in memory, compares byte for byte
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t726_rules as R  # noqa: E402

D, q6 = R.D, R.q6
DRAWN = HERE / "T726_DRAWN.json"
RAW = ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
INDEX = ROOT / "research/agents_t703/out/LINE_INDEX_V3_0_72.json"
T709 = ROOT / "research/agents_t709/out/T709_RESIDUALS.json"
PINS = {DRAWN: "44141756bcfe1206c166fc284234408fb5d6cff076e75c3956ff8390eb4f68ab",
        RAW: "752c9f4e0c4546d00ab9707c19dc5c3761187ba56b9e96a674d68a39edf8adea",
        INDEX: "8e753204d90ebf75d8fa5fe3de120f235bdb16e06a7d677e6aeb615e84ef5d2b",
        T709: "fcbd5aa7d9a12018358a757a284fa746302f44b9ddb122f51c9ad7a53bd82151"}
OUT_JSON = HERE / "out" / "T726_SHAFT_RESIDUAL.json"
OUT_MD = HERE / "out" / "T726_SHAFT_RESIDUAL.md"

ROW = {"PLS": (23, 24), "PNT": (24, 25)}          # his stair-house row and the row after it, per statement
SECTION_AA = ["+0.30", "+1.00", "+3.50", "+5.34", "+5.50", "+7.516", "+7.684", "+9.70", "+13.74", "+13.90"]
T173_BRIDGE = {"south side (open above +5.50, his box wall over 12.90)": D("20.11"),
               "north (his 2.40 / +1.00 vs printed 2.50 / +0.30 lobby, heights)": D("-2.64"),
               "west / east (his 5.00 x 12.90 x 2 vs faces to 5.20, lobby, soffit)": D("-3.62")}
T173_ENGINE_GROSS = D("177.07")
LIKE_FOR_LIKE = {"engine": (D("984.250"), D("1053.666")), "his_gross": D("1169.125")}      # T-701 s.2 (plaster)
SHAFT_LINES = {"HL:WALL_FINISH:ST_GF:PLASTER", "HL:WALL_FINISH:ST_1F:PLASTER", "HL:WALL_FINISH:ST_2F:PLASTER",
               "HL:WALL_FINISH:ST_GF:PAINT", "HL:WALL_FINISH:ST_1F:PAINT", "HL:WALL_FINISH:ST_2F:PAINT",
               "HL:WALL_FINISH:1F_13:PLASTER", "HL:WALL_FINISH:1F_13:PAINT", "HL:WALL_FINISH:2F_01:PLASTER",
               "HL:WALL_FINISH:2F_01:PAINT", "GF-R31F8AE:stair hall plaster", "GF-R31F8AE:stair hall paint",
               "2F-R4D1B62:stair hall plaster", "2F-R4D1B62:stair hall paint"}


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _statement_rows(raw, file):
    """the measurement sheet of one statement = the sheet of that file with the most numeric H (length) cells."""
    by = {}
    for r in raw["rows"]:
        if r["file"] == file:
            by.setdefault(r["sheet"], []).append(r)
    sheet = max(by, key=lambda s: sum(1 for r in by[s] if isinstance((r["cells"].get(f"H{r['row']}") or {}).get("v"),
                                                                      (int, float))))
    out = {}
    for r in by[sheet]:
        c = r["cells"]
        n = r["row"]
        g = {k: (c.get(f"{k}{n}") or {}).get("v") for k in "EFGHIJ"}
        out[n] = {k: (v if isinstance(v, (int, float)) and not isinstance(v, bool) else None) for k, v in g.items()}
    return out


def build():
    for p, s in PINS.items():
        if _sha(p) != s:
            raise SystemExit(f"input changed: {p.relative_to(ROOT)}")
    dr = json.loads(DRAWN.read_text(encoding="utf-8"))
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    t709 = json.loads(T709.read_text(encoding="utf-8"))
    res = {"schema": "T726_SHAFT_RESIDUAL_V1", "candidate": idx["candidate_version"], "status": "RESEARCH, UNWIRED"}

    # ---- (1) R-T726-1: which element his 2.50 x 5.40 row belongs to --------------------------------------------------
    stm = {}
    for f, (r0, r1) in ROW.items():
        rows = _statement_rows(raw, f)
        seq = [(n, rows[n]["I"], rows[n]["J"]) for n in sorted(rows)]
        g = R.group_of(seq, r1)
        stm[f] = {"row": r1, "width_m": str(D(str(rows[r1]["H"]))), "height_m": str(D(str(rows[r1]["F"]))),
                  "m2": str(q6(rows[r1]["I"])), "group_rows": g["rows"], "group_sum_I": str(g["sum_I"]),
                  "group_J": str(g["J"]), "group_status": g["status"], "first_row_of_group": g["rows"][0],
                  "first_row": {"length_m": str(D(str(rows[r0]["H"]))), "height_m": str(D(str(rows[r0]["F"]))),
                                "m2": str(q6(rows[r0]["I"]))}}
        if g["rows"] != [r0, r1] or g["status"] != "ESTABLISHED":
            raise SystemExit(f"{f}: row {r1} is not in the stair-house group {r0}-{r1}")
    res["his_row"] = stm

    # ---- (2) R-T726-2: every face of the stair-house family against 2.50 x 5.40 ---------------------------------------
    box, lift = dr["box"], dr["lift"]
    faces = [
        {"id": "ST-01 N face (26E / ADE / 127E)", "width": box["GF"]["width_m"], "h_lo": "12.74", "h_hi": "13.44",
         "line": "ST_GF / ST_1F / ST_2F bands"},
        {"id": "ST-01 S face, GF only (220)", "width": box["GF"]["width_m"], "h_lo": "4.24", "h_hi": "4.34",
         "line": "ST_GF band"},
        {"id": "ST-01 W face u 0 .. 5.20 (298 / AF1 / 12B7)", "width": box["GF"]["n_to_s_outer_m"], "h_lo": "12.74",
         "h_hi": "12.90", "line": "ST bands"},
        {"id": "ST-01 E face = lift wall, stair side (21C / B16 / 129A)", "width": box["GF"]["n_to_s_outer_m"],
         "h_lo": "12.74", "h_hi": "13.44", "line": "ST bands"},
        {"id": "1F arrival wall across the landing (AEA / AEB)", "width": box["1F"]["width_m"], "h_lo": "3.99",
         "h_hi": "4.04", "line": "1F-13"},
        {"id": "2F arrival wall across the landing (1282 / 1283)", "width": box["2F"]["width_m"], "h_lo": "3.79",
         "h_hi": "4.04", "line": "2F-01"},
        {"id": "W face south of u 5.20, 1F / 2F (C21 / 12B7)",
         "width": str(q6(D(str(box["1F"]["n_to_s_m"])) - D(str(box["GF"]["n_to_s_outer_m"])))), "h_lo": "3.79",
         "h_hi": "4.04", "line": "1F-13 / 2F-01"},
        {"id": "lift shaft V-03 inner face (each of 4, every floor)", "width": lift["GF"]["inner_w_m"], "h_lo": None,
         "h_hi": None, "line": "none (lining needs a specification, T-719)"},
        {"id": "lift shaft outer width, GF (21C .. 222)", "width": box["GF"]["lift_outer_width_m"], "h_lo": None,
         "h_hi": None, "line": "neighbouring rooms"},
        {"id": "ST-02 well west run (T-709 E3E)", "width": "4.00", "h_lo": "3.99", "h_hi": "4.29", "line": "1F-13"},
        {"id": "ST-02 well south run (T-709 D7B)", "width": "7.02", "h_lo": "3.99", "h_hi": "4.29", "line": "1F-13"},
    ]
    lv = dr["levels"]
    lin = sorted({l["value"] for l in lv if l["inside_st01_box"]} | set(SECTION_AA), key=lambda s: D(s))
    lout = sorted({l["value"] for l in lv if not l["inside_st01_box"]} - set(lin), key=lambda s: D(s))
    w, h = stm["PLS"]["width_m"], stm["PLS"]["height_m"]
    result, detail = R.bind(w, h, faces, lin, lout)
    # who printed the out-of-scope levels
    where = {}
    for l in lv:
        if not l["inside_st01_box"]:
            k = l["value"]
            tag = l["frame"] + (" beside the annex 'ROOF' block (B8D)" if l["beside_annex_roof_block"] else
                                (" outside the ST-01 box" if l["frame"] in ("GF", "1F", "2F") else ""))
            where.setdefault(k, set()).add(f"{l['handle']} {tag}")
    used = {D(x) for p in detail["out_of_scope_level_intervals"] for x in p}
    detail["out_of_scope_level_sources"] = {k: sorted(v) for k, v in sorted(where.items()) if D(k) in used}
    res["binding"] = {"row": f"{w} x {h}", "result": result, "levels_in_scope": lin, "levels_out_of_scope": lout,
                      "faces": faces, **detail}

    # ---- (3) R-T726-3: the shaft faces are carried once between the shaft line and the rooms beside it ---------------
    rooms = {}

    def walk(o):
        if isinstance(o, dict):
            if "room" in o and "drawn_chain_perimeter" in o:
                rooms[o["room"]] = o
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(t709)
    b1, b2 = box["1F"], box["2F"]
    u52 = D(str(box["GF"]["n_to_s_outer_m"]))
    walked_1f = [str(u52), str(b1["width_m"]), str(u52), "0.10"]       # E, N, W u 0 .. 5.20, two 0.05 pier returns
    walked_2f = [str(q6(u52 - D(str(b2["slab_edge_u_from_n_m"])))) for _ in (0, 1)]    # W and E over the 2F landing
    open_2f = [str(b2["width_m"])]                                                     # slab edge 138B, no wall
    o1, d1 = R.once(rooms["1F-13"]["drawn_chain_perimeter"], rooms["1F-13"]["engine_face_lm"], walked_1f, [])
    o2, d2 = R.once(rooms["2F-01"]["drawn_chain_perimeter"], rooms["2F-01"]["engine_face_lm"], walked_2f, open_2f)
    res["once"] = {
        "1F-13": {"chain": rooms["1F-13"]["chain_source"], "chain_lm": rooms["1F-13"]["drawn_chain_perimeter"],
                  "room_face_lm": rooms["1F-13"]["engine_face_lm"], "shaft_faces_walked_lm": walked_1f,
                  "open_edges_lm": [], "result": o1, **d1},
        "2F-01": {"chain": rooms["2F-01"]["chain_source"], "chain_lm": rooms["2F-01"]["drawn_chain_perimeter"],
                  "room_face_lm": rooms["2F-01"]["engine_face_lm"], "shaft_faces_walked_lm": walked_2f,
                  "open_edges_lm": open_2f, "result": o2, **d2},
        "GF": {"result": "ONCE", "why": "the GF stair-hall lines (GF-R31F8AE) are EXCLUDED on the candidate; the ST_GF "
                                        "shaft lines alone carry the GF band"}}
    lines = []
    for r in idx["lines"]:
        if r["element_id"] in SHAFT_LINES:
            lines.append({"line": r["line_id"][:10], "code": r["item_code"], "element": r["element_id"],
                          "class": r["class"], "low": r["held_low"] if r["held_low"] is not None else r["measured_net"],
                          "high": r["held_high"] if r["held_high"] is not None else r["measured_net"]})
    res["candidate_lines"] = sorted(lines, key=lambda x: (x["code"], x["element"]))

    # ---- (4) reconciliation in units ---------------------------------------------------------------------------------
    his_total = D(stm["PLS"]["group_J"])
    bridge = dict(T173_BRIDGE)
    bridge[f"his row {stm['PLS']['row']} {w} x {h}: {result}"] = D(stm["PLS"]["m2"])
    s = sum(bridge.values(), D(0))
    gap = his_total - T173_ENGINE_GROSS
    if abs(s - gap) > D("0.005"):
        raise SystemExit(f"bridge does not close: {s} vs {gap}")
    lo, hi = LIKE_FOR_LIKE["engine"]
    his = LIKE_FOR_LIKE["his_gross"]
    his_wo = his - D(stm["PLS"]["m2"])
    res["reconciliation"] = {
        "his_stair_house_gross": str(his_total), "engine_shaft_gross_T173": str(T173_ENGINE_GROSS),
        "his_minus_engine": str(q6(gap)), "bridge": {k: str(v) for k, v in bridge.items()}, "bridge_sum": str(q6(s)),
        "like_for_like_plaster_pct": [str(R.pct(lo, his)), str(R.pct(hi, his))],
        "like_for_like_plaster_pct_row_named_apart": [str(R.pct(lo, his_wo)), str(R.pct(hi, his_wo))],
        "engine_change_m2": "0", "paint_row": f"PNT row {stm['PNT']['row']} {stm['PNT']['m2']} m2: the same row "
                                              f"(group {stm['PNT']['group_rows']}), same result"}
    return res


def render_md(r):
    b = r["binding"]
    L = [f"# T-726 plaster shaft residual 13.50 m2 on {r['candidate']} (generated; research, unwired)", ""]
    p = r["his_row"]["PLS"]
    L += ["## (1) Which element the row belongs to (R-T726-1)", "",
          f"PLS row {p['row']} {p['width_m']} x {p['height_m']} = {p['m2']} is in group rows {p['group_rows']} "
          f"(sum I {p['group_sum_I']} = J {p['group_J']}: {p['group_status']}); the group's first row is "
          f"{p['first_row']['length_m']} x {p['first_row']['height_m']} = {p['first_row']['m2']} (stair-house walls). "
          f"PNT row {r['his_row']['PNT']['row']}: group {r['his_row']['PNT']['group_rows']}, J "
          f"{r['his_row']['PNT']['group_J']}.", "",
          "## (2) Faces of the stair-house family against the row (R-T726-2)", "",
          f"Result: **{b['result']}** (width tol {b['tol_w']} m, height tol {b['tol_h']} m).", "",
          "| face | width m | exposed height m | carried by |", "|---|---|---|---|"]
    for f in b["faces"]:
        hh = "HELD" if f["h_lo"] is None else f"{f['h_lo']} .. {f['h_hi']}"
        L.append(f"| {f['id']} | {f['width']} | {hh} | {f['line']} |")
    L += ["", f"Width matches: {b['width_matches']}; nearest heights: "
          + "; ".join(f"{n['face']} gap {n.get('gap_m')}" for n in b["nearest"]), "",
          f"Printed levels inside the element: {b['levels_in_scope']}; intervals of {r['binding']['row'].split(' x ')[1]}"
          f" inside: {b['in_scope_level_intervals'] or 'none'}.",
          f"Intervals using a level outside the element: {b['out_of_scope_level_intervals']} "
          f"(sources {b['out_of_scope_level_sources']}).", "",
          "## (3) Shaft faces carried once (R-T726-3)", "", "| room | chain lm | room face lm | shaft faces walked | "
          "open edges | expected | room - expected | result |", "|---|---|---|---|---|---|---|---|"]
    for k in ("1F-13", "2F-01"):
        o = r["once"][k]
        L.append(f"| {k} | {o['chain_lm']} | {o['room_face_lm']} | {' + '.join(o['shaft_faces_walked_lm'])} | "
                 f"{' + '.join(o['open_edges_lm']) or '-'} | {o['expected_room_face_lm']} | "
                 f"{o['room_minus_expected_lm']} | {o['result']} |")
    L += [f"| GF | - | - | - | - | - | - | {r['once']['GF']['result']}: {r['once']['GF']['why']} |", "",
          "Candidate lines read (V3.0.72):", "", "| line | code | element | class | low | high |", "|---|---|---|---|---|---|"]
    for x in r["candidate_lines"]:
        L.append(f"| {x['line']} | {x['code']} | {x['element']} | {x['class']} | {x['low']} | {x['high']} |")
    c = r["reconciliation"]
    L += ["", "## (4) Reconciliation in units", "",
          f"His stair-house gross {c['his_stair_house_gross']} - engine gross {c['engine_shaft_gross_T173']} (T-173) = "
          f"{c['his_minus_engine']}:", ""]
    for k, v in c["bridge"].items():
        L.append(f"- {k}: {v}")
    L += [f"- sum {c['bridge_sum']} (closes)", "",
          f"Like for like plaster (T-701): engine vs his {c['like_for_like_plaster_pct']} %; with the unbound row named "
          f"apart {c['like_for_like_plaster_pct_row_named_apart']} %. Engine change: {c['engine_change_m2']} m2. "
          f"{c['paint_row']}.", ""]
    return "\n".join(L)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    r = build()
    js = json.dumps(r, indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    md = render_md(r) + "\n"
    if "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == js and OUT_MD.read_text(encoding="utf-8") == md
        print("T-726 outputs", "IDENTICAL" if ok else "DIFFER")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(js, encoding="utf-8")
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"wrote {OUT_JSON.name} / {OUT_MD.name}: {r['binding']['result']}; once 1F {r['once']['1F-13']['result']} "
          f"2F {r['once']['2F-01']['result']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
