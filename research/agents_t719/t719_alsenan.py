"""T-719 development-villa builder: VOID REGISTER (missing family B2-05 voids / double height / shafts) on the candidate of
record ARCH_TAKEOFF_V3.0.71 (research, unwired; no quantity moved).

Reads only repository files, each sha256-pinned (an edited input stops the build):
  research/agents_t719/T719_DRAWN.json                 own DXF read by handle this run (t719_extract.py) + the released
                                                       engine's split of the same faces (areas only)
  research/agents_t704/out/LINE_INDEX_V3_0_71.json     candidate of record V3.0.71 (T-704)
  research/agents_t283/CEILINGS_T283.csv               ceiling ledger R3 (T-283, merged; wired by T-284)
  research/agents_t283/DOMES_T283.csv                  dome openings over the 1F faces (T-283)
Typed here (cited, not re-measured this run): T-116 opening residue inside the light well 3.453 (2.035 VOID_RESIDUE +
1.418 STAIR_FOOTPRINT, T-116 table row 'Opening residue + round-stair quarter landing and arrival edge'), carried into
the candidate's 1F living floor by T-122 / T-129; the ST-01 stair box at 1F 2.50 x 4.29 (T-283 stair zone 10.725).

    python3 -I research/agents_t719/t719_alsenan.py           # writes out/T719_VOIDS.json and .md
    python3 -I research/agents_t719/t719_alsenan.py --check   # rebuilds in memory, compares byte for byte
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t719_rules as R  # noqa: E402

D, q6 = R.D, R.q6
DRAWN = HERE / "T719_DRAWN.json"
INDEX = ROOT / "research/agents_t704/out/LINE_INDEX_V3_0_71.json"
CEIL = ROOT / "research/agents_t283/CEILINGS_T283.csv"
DOMES = ROOT / "research/agents_t283/DOMES_T283.csv"
PINS = {DRAWN: "e23d7523d8cce1b3468abb1427b8891601fae65899b6754d51d89087ab3ab644",
        INDEX: "eaea9f7e8cc838497bfe20a4454fab081af18717e1bc670a8473a74f5a81da6a",
        CEIL: "10214b3dbffcf57a5327130edd65794646864c60cb11abb090e1f1906d30d522",
        DOMES: "b15b51c3c8e372e514f6518ffb6377724737cfa315902ced66bb3707e4b88953"}
OUT_JSON = HERE / "out" / "T719_VOIDS.json"
OUT_MD = HERE / "out" / "T719_VOIDS.md"

T116_RESIDUE = (D("2.035"), D("1.418"))      # VOID_RESIDUE + STAIR_FOOTPRINT inside the light well (T-116)
ST01_BOX_1F = (D("2.50"), D("4.29"))          # ST-01 stair box at 1F (T-283 stair zone 10.725; printed 250 x 429)
EL = {  # element id -> role (candidate lines read by id)
    "1F-R78C367:floor": "1F living porcelain (pierced storey of V-01)",
    "1F-R78C367:ceiling#DECOR_GROUP": "1F living decor ceiling (top of V-01)",
    "1F-R78C367:ceiling over void": "1F living 'ceiling over void' (V2.9 base line)",
    "1F-R78C367:ceiling": "1F living ceiling parent",
    "GF-RC99C2A:ceiling": "GF open-plan ceiling (storey below V-01)",
    "1F-RB72F22:ceiling": "1F west master ceiling (under V-05)", "1F-R8BDA49:ceiling": "1F bath ceiling (under V-05)",
    "1F-R48AA46:ceiling": "1F bath ceiling (under V-05)", "1F-R3CFCFD:ceiling": "1F east master ceiling (under V-06)",
    "1F-R48CDA5:ceiling": "1F bath ceiling (under V-06)", "DOME:WEST:intrados": "west dome soffit (top of V-05)",
    "DOME:EAST:intrados": "east dome soffit (top of V-06)", "2F-R1DB2D2:ceiling": "2F maid ceiling (under dome 3)",
    "2F-RE83BED:ceiling": "2F bath ceiling (under dome 3)", "GF-R31F8AE:stairwell ceiling": "ST-01 GF stairwell",
    "2F-R4D1B62:stairwell ceiling": "ST-01 2F stairwell"}


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load():
    for p, h in PINS.items():
        if _sha(p) != h:
            raise SystemExit(f"input changed: {p.relative_to(ROOT)} {_sha(p)[:12]} != {h[:12]}")
    drawn = json.loads(DRAWN.read_text(encoding="utf-8"))
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    lines = {}
    for ln in idx["lines"]:
        if ln["element_id"] in EL and ln["item_code"] in ("FIN.FLOOR.PORCELAIN", "FIN.CEILING", "FIN.DOME.SOFFIT"):
            lines[ln["element_id"]] = {"line_id": ln["line_id"], "class": ln["class"],
                                       "value": None if ln["measured_net"] is None else str(q6(ln["measured_net"])),
                                       "role": EL[ln["element_id"]]}
    ceil = list(csv.DictReader(io.StringIO(CEIL.read_text(encoding="utf-8"))))
    domes = {r["DOME"]: r for r in csv.DictReader(io.StringIO(DOMES.read_text(encoding="utf-8")))}
    return drawn, idx["candidate_version"], lines, ceil, domes


def _ceil(rows, face, surface_start):
    hit = [r for r in rows if r["FACE"] == face and r["SURFACE"].startswith(surface_start)]
    assert len(hit) == 1, (face, surface_start, len(hit))
    return hit[0]


def build():
    dr, cand, L, ceil, domes = _load()
    v1 = dr["V-01"]
    e1 = v1["engine"]
    rows, flags = [], []

    # ---- V-01 light well --------------------------------------------------------------------------------------------
    pierces, below = R.placement({"pierces": "1F", "below": "GF"})
    sp = e1["split_face_parts_m2"]
    t116 = sum(T116_RESIDUE, D(0))
    fl_ded = [("engine VOID (X-marked rectangle)", sp["VOID"]), ("engine STAIR_BELOW_SEEN (ST-02 F1 + F4 + F6)",
              sp["STAIR_BELOW_SEEN"]), ("T-116 opening residue (VOID_RESIDUE + STAIR_FOOTPRINT)", str(t116))]
    fres, fr = R.floor_check(e1["face_in_well_m2"], fl_ded)
    ov = e1["below_seen_footprint_overlaps_m2"]
    excess, twice = R.overlap_excess([e1["below_seen_treads_m2"]], e1["below_seen_union_m2"])  # tread lines
    excess = q6(sum(D(str(o[2])) for o in ov))                         # footprint overlaps the split summed
    after = q6(fr + excess) if fr is not None else None
    gf_ded = [("T-283 GF 'no ceiling: opening in the slab above'",
               _ceil(ceil, "GF-RC99C2A/open", "no ceiling")["QTY"]),
              ("T-283 GF stair zone (stair face of the slab plan)", _ceil(ceil, "GF-RC99C2A/open", "stair zone (")["QTY"]),
              ("T-283 GF-159 (flight under a beam band), bound by sum only", "1.3756")]
    gres, gr = R.floor_check(e1["gf_face_in_well_m2"], gf_ded)
    top = R.ceiling_top_lines([("1F-R78C367:ceiling#DECOR_GROUP", L["1F-R78C367:ceiling#DECOR_GROUP"]["value"]),
                               ("1F-R78C367:ceiling over void", L["1F-R78C367:ceiling over void"]["value"])])
    rows.append(R.register_row("V-01", pierces, below, v1["well_m2"], "1F plan by handle: wall faces " +
                               "AF7 / AEC, slab edges AF5 / D24 / B75 / B74; X-rect B77-B79 with the VOID word B7A; GF " +
                               "draws the rectangle 'above' (4B0) and the same treads (0.000 m apart)",
                               ["L-b06400d46d252f242018", "L-eb3be58fc760b39f0e38", "L-43bf1f869e1588f1d3bd",
                                "L-35341ff2e6a848b9436b"]))
    rows[-1].update({
        "name": "ST-02 light well over the GF reception (double height GF + 1F)",
        "outline": f"{v1['dims_m']['west_to_east_edge']} x {v1['dims_m']['south_face_to_north_edge']} - "
                   f"{v1['dims_m']['corner_landing_w']} x {D(str(v1['dims_m']['south_face_to_north_edge'])) - D(str(v1['dims_m']['south_face_to_arrival_edge']))}"
                   " (arrival floor NE of the east flight)",
        "parts_m2": {"X-marked rectangle": v1["xrect_m2"], "ST-02 corner landing +4.696": v1["corner_landing_m2"],
                     "flights, pocket and 0.05 edge strips": str(q6(D(str(v1["well_m2"])) - D(str(v1["xrect_m2"])) -
                                                                  D(str(v1["corner_landing_m2"]))))},
        "walls_double_height": {"west AF7": v1["dims_m"]["south_face_to_north_edge"],
                                "south AEC": v1["dims_m"]["west_to_east_edge"]},
        "floor_1F": {"face_in_outline_m2": e1["face_in_well_m2"], "outline_outside_face_m2": e1["well_outside_face_m2"],
                     "deductions": fl_ded, "result": fres, "residual_m2": str(fr),
                     "cause": f"ST-02 F1 (radial) and F4 footprints overlap {ov[0][2]} m2 on the 1F plan "
                              f"(F4 read from 2.82, F1 box to 2.87); the engine sums footprints, so the strip is deducted "
                              f"twice; the T-116 residue {t116} = the geometric remainder {e1['carried_in_well_m2']}",
                     "residual_after_overlap_m2": str(after)},
        "ceiling_GF": {"face_in_outline_m2": e1["gf_face_in_well_m2"], "deductions": gf_ded, "result": gres,
                       "residual_m2": str(gr), "engine_V2.9_double_height_m2": e1["gf_double_height_m2"]},
        "ceiling_top": {"lines": ["1F-R78C367:ceiling#DECOR_GROUP", "1F-R78C367:ceiling over void"], "result": top,
                        "east_dome_overlap_m2": dr["DOMES"]["east"]["overlap_with_light_well_m2"],
                        "note": "the decor group 51.0496 = face 75.983 - ST-01 stair zone 10.725 - 0.1725 - east dome "
                                "14.0359 holds the well top; the blank 'ceiling over void' line names 16.005 of it again"},
    })
    if fres == "DEDUCTED_TWICE":
        flags.append({"void": "V-01", "line": "L-b06400d46d252f242018", "verdict": "ENGINE_WRONG (candidate)",
                      "m2": str(-fr), "what": "1F living porcelain deducts one 1.15 x 0.05 strip of the light well "
                      "twice (two ST-02 flight footprints summed where they overlap)",
                      "if_corrected": str(q6(D(L["1F-R78C367:floor"]["value"]) - fr))})
    if top == "DOUBLE_COUNT_RISK":
        flags.append({"void": "V-01", "line": "L-35341ff2e6a848b9436b", "verdict": "DOUBLE_COUNT_RISK",
                      "m2": str(q6(e1["ceiling_over_void_m2"])), "what": "blank 'ceiling over void' line names m2 the "
                      "decor group line L-43bf1f86 already carries; it must never be valued beside it",
                      "if_corrected": "line stays blank / EXCLUDED; no value moves"})

    # ---- V-02 oval opening (exterior) -------------------------------------------------------------------------------
    v2 = dr["V-02"]
    r2, _ = R.floor_check(0 if not v2["engine_faces_1f_m2"] else sum(v2["engine_faces_1f_m2"].values()), [])
    row = R.register_row("V-02", "1F (slab east of the curved glazing)", "GF (pool court, exterior)", v2["outline_m2"],
                         "1F layer-5 outline BCF / 2F1C / C7A / 2F1B (joints 0.000); GF draws it 'above' on the same "
                         "centres (20A / 299)", [])
    row.update({"name": "oval opening beside the 1F east bay", "result": r2, "span_m": v2["span_m"],
                "engine_faces_1f_m2": v2["engine_faces_1f_m2"], "engine_faces_gf_m2": v2["engine_faces_gf_m2"],
                "cross_check": "T-071: '1F void: layer 5 oval 3.820 m2' (+0.004 here)",
                "note": "outside every internal face on both plans: no internal floor / ceiling line; the slab-top / "
                        "soffit / edge lines of the 1F projection are not in the candidate (named, not valued)"})
    rows.append(row)

    # ---- V-03 lift shaft --------------------------------------------------------------------------------------------
    v3 = dr["V-03"]
    row = R.register_row("V-03", "1F and 2F slabs (stacked GF / 1F / 2F)", "pit / GF", v3["stacked_shafts"][0]["m2_each"],
                         "engine stacked shaft (three plans aligned on the column grid), own SHAFT spaces", [])
    row.update({"name": "lift shaft 1.80 x 1.80", "result": "DEDUCTED_ONCE",
                "per_floor": v3["shaft_rooms"], "note": "its own space on every plan: no room floor or ceiling line "
                "includes it (EXCLUDED, NO_FINISH); shaft lining / top: no line (needs a specification), named"})
    rows.append(row)

    # ---- V-04 ST-01 dog-leg stair shaft -----------------------------------------------------------------------------
    v4 = dr["V-04"]
    box = q6(ST01_BOX_1F[0] * ST01_BOX_1F[1])
    stz = _ceil(ceil, "1F-R78C367", "stair zone (")["QTY"]
    row = R.register_row("V-04", "1F and 2F slabs", "GF / 1F (stair continuous to the 2F stair hall)", str(box),
                         "ST-01 box 2.50 x 4.29 at 1F (printed; T-283 stair zone); well between flights 0.20 x 3.40 "
                         "(1F A8D / A8E, 2F 1356 .. 1359): an open balustrade gap, not a wall (T-709)",
                         ["L-2175a965bb7c48a50e6c", "L-dd6930fd19ca1b908c56", "L-b06400d46d252f242018"], status="DRAWING-CONFIRMED")
    row.update({"name": "ST-01 dog-leg stair shaft (GF -> 2F)",
                "ceiling_1F": {"t283_stair_zone_m2": stz, "box_m2": str(box),
                               "result": "DEDUCTED_ONCE" if abs(D(stz) - box) <= R.TOL_M2 else "NOT_DEDUCTED"},
                "floor_1F": "flights F2 / F3 / F5 treads 8.336981 (engine STAIR_FLIGHTS), arrival landing 4.865 to "
                            "marble (T-122), dog-leg well / turning landing 2.142 (T-116): cited, not re-measured here",
                "per_floor": v4,
                "note": "GF / 2F are STAIR spaces (no room floor finish); their stairwell ceilings stay HELD (Q-72 "
                        "investigation, stair box top 12.974 at 2F): one line each, no double count"})
    rows.append(row)

    # ---- V-05 / V-06 dome openings in the 1F roof slab --------------------------------------------------------------
    dm = dr["DOMES"]
    for vid, key, hi, lines_under, top_el in (
            ("V-05", "west", "12EB", {"1F-RB72F22:ceiling": ("19.05", "11.5808"), "1F-R8BDA49:ceiling": ("5.0225", "1.4227"),
                                     "1F-R48AA46:ceiling": ("5.0225", "1.2410")}, "DOME:WEST:intrados"),
            ("V-06", "east", "2F33", {"1F-R3CFCFD:ceiling": ("19.016545", "0.3418"), "1F-R48CDA5:ceiling": ("4.725", "0.4472")},
             "DOME:EAST:intrados")):
        chk = []
        for el, (face, part) in lines_under.items():
            got = D(L[el]["value"])
            chk.append({"line": L[el]["line_id"], "element": el, "face_m2": face, "dome_part_m2": part,
                        "candidate_m2": str(got), "result": "DEDUCTED_ONCE" if abs(D(face) - D(part) - got) <= R.TOL_M2
                        else "NOT_DEDUCTED"})
        row = R.register_row(vid, "1F roof slab (2F plan, roof terrace)", "1F rooms", dm[key]["disc_m2"],
                             f"2F plan layer-5 circle {hi} r {dm[key]['r_m']} (Q-44 A; S0 concrete dome, S1 open skylight)",
                             [c["line"] for c in chk] + [L[top_el]["line_id"]])
        row.update({"name": f"{key} dome opening", "ceiling_below": chk,
                    "t283": {k: domes[key][k] for k in ("OPEN_DISC_M2", "OVER_FLOOR_PIECES_M2", "OVER_WALLS_OR_OUTSIDE_M2")},
                    "ceiling_top": {"line": L[top_el]["line_id"], "class": L[top_el]["class"],
                                    "result": R.ceiling_top_lines([(top_el, L[top_el]["value"])])},
                    "own_overlap_living_m2": dm[key].get("overlap_with_living_face_m2"),
                    "cuts_2f_faces_m2": dm[key]["overlap_with_2f_faces_m2"]})
        if key == "east":
            row["ceiling_below"].append({"element": "1F-R78C367 (inside the decor group)", "dome_part_m2": "14.0359",
                                         "own_m2": str(dm[key]["overlap_with_living_face_m2"]),
                                         "residual_m2": str(q6(D(str(dm[key]["overlap_with_living_face_m2"])) - D("14.0359"))),
                                         "result": "DEDUCTED_ONCE (HELD part); 0.030 m2 named residual: own circle vs "
                                                   "T-283's arc pieces"})
        rows.append(row)

    # ---- V-07 the third dome (upper roof) ---------------------------------------------------------------------------
    t3 = dm["third_above"]
    row = R.register_row("V-07", "top roof slab (+13.90)", "2F rooms", None,
                         f"2F plan layer-2 circle 1300 r {t3['r_m']} drawn 'above'; no opening line on any plan and no "
                         "structural drawing", [L["2F-R1DB2D2:ceiling"]["line_id"], L["2F-RE83BED:ceiling"]["line_id"]])
    row.update({"name": "third dome (upper roof)", "status": "HELD", "result": "NOT A DRAWN VOID (S0)",
                "disc_if_opened_m2": t3["disc_m2"], "over_2f_faces_m2": t3["overlap_with_2f_faces_m2"],
                "note": "S0 (approved design): no opening: 2F ceilings full (maid 19.350, bath 5.550) are right; under "
                        "the client's S1 open skylight the 2F maid / bath / shaft ceilings would lose the overlaps "
                        "listed: HELD by scenario, never 0, never applied here"})
    rows.append(row)

    return {"task": "T-719", "candidate": cand, "rule": "R-T719-1 .. -5 (t719_rules.py)", "tol_m2": str(R.TOL_M2),
            "register": rows, "flags": flags, "lines": L,
            "moved": "none (research; no candidate line changed)"}


def md(doc):
    o = [f"# T-719 void register on {doc['candidate']} (research, unwired)", "",
         "| void | name | pierces | below | outline m2 | status | floor (pierced storey) | ceiling below | top |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in doc["register"]:
        fl = r.get("floor_1F")
        fl = (f"{fl['result']} {fl['residual_m2']}" if isinstance(fl, dict) else (r.get("result") or "-"))
        cb = r.get("ceiling_GF") or r.get("ceiling_1F")
        cb = (f"{cb['result']} {cb.get('residual_m2', '')}".strip() if isinstance(cb, dict) else
              ("; ".join(f"{c['element']} {c['result']}" for c in r.get("ceiling_below", [])) or "-"))
        tp = r.get("ceiling_top")
        tp = tp["result"] if isinstance(tp, dict) else "-"
        o.append(f"| {r['void']} | {r.get('name', '')} | {r['pierces']} | {r['below']} | {r['outline_m2']} | "
                 f"{r['status']} | {fl} | {cb} | {tp} |")
    o += ["", "## Flags (no quantity moved)", ""]
    for f in doc["flags"]:
        o.append(f"- {f['void']} {f['line']}: **{f['verdict']}** {f['m2']} m2: {f['what']} (if corrected: "
                 f"{f['if_corrected']})")
    o += ["", "## Candidate lines read", ""]
    for el, v in sorted(doc["lines"].items()):
        o.append(f"- {v['line_id']} {el}: {v['class']} {v['value']} ({v['role']})")
    return "\n".join(o) + "\n"


def main(argv):
    doc = build()
    js = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n"
    mt = md(doc)
    if "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == js and OUT_MD.read_text(encoding="utf-8") == mt
        print("T719 outputs identical:", ok)
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(js, encoding="utf-8")
    OUT_MD.write_text(mt, encoding="utf-8")
    print(mt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
