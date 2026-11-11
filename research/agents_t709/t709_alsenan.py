"""T-709 development-villa builder: PAINT / PLASTER RESIDUALS round 2 on ARCH_TAKEOFF_V3.0.70 (research, unwired).

Reads only repository files, each sha256-pinned (an edited input stops the build):
  research/agents_t693/out/LINE_INDEX_V3_0_70.json      candidate of record V3.0.70 (T-693 Gate B PASS)
  research/agents_t709/T709_DRAWN.json                  own DXF re-read this run (t709_extract.py; handles and lengths)
  research/agents_t701/out/T701_RECONCILE.json          T-701 bridges (MERGED 65083ee7): shaft, returns, dry rooms
  research/agents_t556/out/T556_PLASTER_HEIGHT.json     per-room face lm and opening ledger (T-556, wired by T-563)
  research/agents_t634/out/T634_PLASTER_PAINT_REMEASURE.json  26 door returns re-read by handle (T-634, merged)
  research/agents_t569/WIRING_MANIFEST_V8.json          T-569 return-paint wiring form (merged 5aee8f5a)
  tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json   his plaster (PLS) / paint (PNT) statements as parsed cells
Typed here (cited): printed levels of section A-A (T-173), the GF / 1F heights (T-556 H 4.29; owner G1 3.65, Q-48 A),
the corner-landing top +4.696 (T-184). No coordinate, client name or workbook text is stored.

    python3 -I research/agents_t709/t709_alsenan.py           # writes out/T709_RESIDUALS.json and .md
    python3 -I research/agents_t709/t709_alsenan.py --check   # rebuilds in memory, compares byte for byte
"""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t709_rules as R  # noqa: E402

D, q6 = R.D, R.q6
INDEX = ROOT / "research/agents_t693/out/LINE_INDEX_V3_0_70.json"
DRAWN = HERE / "T709_DRAWN.json"
T701 = ROOT / "research/agents_t701/out/T701_RECONCILE.json"
T556 = ROOT / "research/agents_t556/out/T556_PLASTER_HEIGHT.json"
T634 = ROOT / "research/agents_t634/out/T634_PLASTER_PAINT_REMEASURE.json"
T569 = ROOT / "research/agents_t569/WIRING_MANIFEST_V8.json"
RAW = ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json"
PINS = {INDEX: "6c12da077200db176c6b81e0e869b21e731547f1e3265fb982c0be1ef7b7ec98",
        DRAWN: "f2e5f42b55835af21f0917434ba8ca03158ab7778e553c63473dd6729634f86d",
        T701: "9ef9a219deebd3b44db920e56a4dc204856cca378a12cbfc046d4c6a53b220a2",
        T556: "8169a1953c386ccab7bbd9283404c100dc9d8105e6c10b7244593c9af442cd84",
        T634: "5d678d5458cd2dd5d37f3c0269db9190f4cabacc31ac797e53a0f8c2b3c26139",
        T569: "c71ecdc0eb11cba4e593ce31e3ec2d3bbad89d55fbc86a596f5b5890a474cf6b",
        RAW: "752c9f4e0c4546d00ab9707c19dc5c3761187ba56b9e96a674d68a39edf8adea"}
OUT_JSON = HERE / "out" / "T709_RESIDUALS.json"
OUT_MD = HERE / "out" / "T709_RESIDUALS.md"

# ---- typed, cited inputs -------------------------------------------------------------------------------------------
# Section A-A printed levels (T-173 s.2; T-680): finished floors / landings and the roof mark.
LEVELS = {"lobby": "0.30", "GF": "1.00", "MS1 landing": "3.50", "1F": "5.50", "MS2 landing W": "7.516",
          "MS2 landing E": "7.684", "2F": "9.70", "roof": "13.90"}
SOFFITS = {"1F slab soffit": "5.34", "roof soffit": "13.74"}           # T-173 (slab 0.16)
FFL_1F = "5.50"
GF_PLASTER_TOP = "5.29"     # GF FFL +1.00 + H 4.29 (T-556, GF-08 floor part, DRAWING-CONFIRMED height)
GF_PAINT_TOP = "4.65"       # GF FFL +1.00 + G1 3.65 (owner G1, Q-48 A; the GF-08 paint line's own height)
LANDING_TOP = "4.696"       # ST-02 corner landing (T-184), against the south wall beyond the 5.87 void
# Shaft-side drawn runs a 'stair wall' row could be (R-T709-2 candidates; T-173 faces, T-634 / T-621 pieces).
STAIR_WALL_CANDIDATES = [("ST-01 W + E faces (T-173: 5.20 + 5.20)", "10.40"),
                         ("ST-01 N + W + E faces (T-173: 2.50 + 5.20 + 5.20)", "12.90"),
                         ("GF stair-hall piece outline (T-634, by handle)", "12.30"),
                         ("GF stair-lobby piece outline (T-634, by handle)", "4.60")]
# The 2.50 m faces of the drawing that a 2.50 m row could be (T-173 / T-621, printed 250).
FACES_250 = ["ST-01 N face (whole height)", "ST-01 S face (GF only, +1.00 .. +5.34)",
             "1F arrival 2.50 x 1.95: the wall facing it (in 1F-13)", "2F arrival 2.50 x 1.95: the wall facing it (2F-01)"]
# Door returns with WET rooms on both sides, by V3.0.70 element id (T-634 both_sides_wet; OP ids bound by the T-644
# host map (1F OP-010 = D-1F-06) and by the T-310 wet-door transitions (GF OP-017 / OP-018 = D-GF-11 / D-GF-12)).
BOTH_WET = {"1F-OPENING-OP-010:door jambs and head": "D-1F-06",
            "GF-OPENING-OP-017:door jambs and head": "D-GF-11",
            "GF-OPENING-OP-018:door jambs and head": "D-GF-12",
            "GF-REVEAL-D-GF-10:THROUGH:JAMBS_HEAD:VALUED": "D-GF-10",
            "GF-REVEAL-D-GF-02:THROUGH:JAMBS_HEAD:VALUED": "D-GF-02"}
EXTERNAL_DOOR = "GF-OPENING-OP-009:door jambs and head"   # through-wall reveal of an external door (T-676 / T-701)
# (d) the 9 dry rooms T-701 did not re-measure, with their engine plaster / paint line prefixes and the opening ids of
# the T-556 ledger matched to the drawn gaps by width (w x the ledger's own head gives the ledger area).
OPEN_ZONES = {"GF-08", "1F-13", "2F-01"}   # T-147 clipped face basis: a gross chain is not the face (named)
GAP_TO_LEDGER = {   # room -> [(drawn gap width, ledger id, head m used by the ledger)]
    "GF-01": [("1.0", "D-GF-01", "2.20"), ("1.0", "A-GF-01", None), ("1.95492", "W11", "2.20"),
              ("1.95492", "W12", "2.20")],
    "GF-15": [("1.0", "D-GF-13", "2.20"), ("0.8", "D-GF-14", "2.20")],
    "1F-01": [("0.8", "D-1F-01", "2.20"), ("1.0", "D-1F-02", "2.20"), ("2.449774", "W14", "1.60")],
    "1F-10": [("1.0", "A-1F-01", None), ("0.9", "D-1F-08", "2.20")],
    "1F-11": [("0.9", "D-1F-09", "2.20"), ("0.8", "D-1F-10", "2.20")],
    "2F-03": [("1.2", "W29", "1.50"), ("0.8", "D-2F-03", "2.20"), ("0.9", "D-2F-02", "2.20")],
}
CURVED_GLAZING = {"GF-15": "W03 (arc edge, T-634 by handle)", "1F-11": "W17 (curved, HELD outline range, T-556)"}


def _pinned(p):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != PINS[p]:
        raise SystemExit(f"{p.relative_to(ROOT)}: sha256 {h[:16]} is not the pinned file")
    return json.loads(p.read_text(encoding="utf-8"))


def _cells(raw, file_code, anchor):
    rows = [r for r in raw["rows"] if r["file"] == file_code]
    sheets = {r["sheet"] for r in rows if anchor in r["cells"]}
    if len(sheets) != 1:
        raise SystemExit(f"{file_code}: statement sheet not unique")
    sh = sheets.pop()
    return {k: v["v"] for r in rows if r["sheet"] == sh for k, v in r["cells"].items()}


def _n(c, key):
    v = c.get(key)
    if not isinstance(v, (int, float)):
        raise SystemExit(f"his cell {key} not a number")
    return D(repr(v)).quantize(D("0.0001"))


def s(x):
    return None if x is None else str(q6(x))


def build():
    idx, drawn, t701 = _pinned(INDEX), _pinned(DRAWN), _pinned(T701)
    t556 = {r["room"]: r for r in _pinned(T556)["rows"]}
    t634, t569, raw = _pinned(T634), _pinned(T569), _pinned(RAW)
    pls, pnt = _cells(raw, "PLS", "J27"), _cells(raw, "PNT", "J28")
    lines = [x for x in idx["lines"] if x["item_code"] in ("FIN.PLASTER", "FIN.PAINT")]
    out = {"schema": "URBAN_T709_RESIDUALS_V1", "candidate": idx["candidate_version"],
           "inputs_sha256_16": {str(p.relative_to(ROOT)): PINS[p][:16] for p in PINS}}

    # ---- (a) SHAFT residual 54.00: his two rows -----------------------------------------------------------------
    r8 = {"plaster": (_n(pls, "H8"), _n(pls, "F8"), _n(pls, "I8")), "paint": (_n(pnt, "H8"), _n(pnt, "F8"), _n(pnt, "I8"))}
    r24 = {"plaster": (_n(pls, "H24"), _n(pls, "F24"), _n(pls, "I24")),
           "paint": (_n(pnt, "H25"), _n(pnt, "F25"), _n(pnt, "I25"))}
    for k in ("plaster", "paint"):
        if r8[k][0] * r8[k][1] != r8[k][2] or r24[k][0] * r24[k][1] != r24[k][2]:
            raise SystemExit(f"his {k} rows do not multiply out")
    w = drawn["st02_well"]
    well_lm = D(w["west"]) + D(w["south"]) + D(w["column_returns_lm"])
    cands = STAIR_WALL_CANDIDATES + [("ST-02 round-stair well walls, 1F plan printed 4000 + 7020 (DIMENSION E3E / "
                                      "D7B) + 3 column returns 0.05 proud (300E x 2, 3008)", str(well_lm))]
    b8 = R.bind_row(r8["plaster"][0], cands)
    if b8[0] != "BOUND":
        raise SystemExit(f"his 'stair wall' row does not bind: {b8}")
    b24_len = R.bind_row(r24["plaster"][0], [(f, "2.50") for f in FACES_250])
    lv = sorted({D(v) for v in list(LEVELS.values()) + list(SOFFITS.values())})
    h24 = r24["plaster"][1]
    near = [(str(a), str(b)) for a, b in itertools.combinations(lv, 2) if abs((b - a) - h24) <= D("0.05")]
    shaft_t701 = {k: t701["shaft"][k]["by_cause"]["UNRESOLVED"] for k in ("plaster", "paint")}
    out["a_shaft"] = {
        "element": "ST-01 (stair beside the lift): four faces W / E (the lift-shaft wall's stair side) / N / S (GF only), "
                   "each one face from its lowest floor to the roof soffit (Q-72 owner answer; T-173 / T-680). The lift "
                   "shaft's own inside faces are no finish face (no line, his rows do not price them). The open south "
                   "side above +5.50 is no face. Engine lines unchanged (L-95f2c45c / L-0eac839f / L-418121a4 plaster, "
                   "L-145bd239 / L-2ab93d50 / L-5a7a5c6f paint).",
        "t701_unresolved": shaft_t701,
        "his_row_8": {"plaster_row": 8, "paint_row": 8, "length": str(r8["plaster"][0]), "height": str(r8["plaster"][1]),
                      "m2": str(r8["plaster"][2]), "binding": b8[0], "bound_to": b8[1], "his_minus_drawn_lm": str(b8[2]),
                      "drawn_well_lm": str(well_lm), "candidates": [[n, v] for n, v in cands],
                      "engine_line": "1F-13 (L-9b4a7bab plaster / L-be48ea84 paint): chain 1F-LIV.ours carries the "
                                     "'void zone walls' (T-606) at the 1F heights, once",
                      "verdict": "IDENTIFIED: not a shaft face. His GF 'stair wall' = the round-stair (ST-02) well walls, "
                                 "west 4.00 + south 7.02 + column returns 0.15 = 11.17 lm drawn vs his 11.25 (+0.08 lm), priced by "
                                 "him at one more storey (3.60) above the GF. The engine carries these faces in the 1F "
                                 "living line (1F-13) at the 1F heights: ENGINE_RIGHT on scope; the comparison belongs "
                                 "to 1F-13, not to the shaft. Whether his 1F living row also carries them is not "
                                 "determinable from his rows (no outline): named, no engine effect."},
        "his_row_24": {"plaster_row": 24, "paint_row": 25, "length": str(r24["plaster"][0]),
                       "height": str(r24["plaster"][1]), "m2": str(r24["plaster"][2]),
                       "length_binding": b24_len[0], "length_matches": b24_len[1],
                       "printed_level_intervals_within_0.05_of_his_height": near,
                       "verdict": "UNRESOLVED (13.50): four drawn faces are 2.50 m wide (all already carried: the "
                                  "shaft lines, 1F-13, 2F-01) and no printed level interval is 5.40 m; his row cannot be "
                                  "bound to a physical face. Never added, never 0 on the engine side."},
        "residual_after": {"identified_to_1F_13": str(r8["plaster"][2]), "unresolved": str(r24["plaster"][2])},
    }
    # R-T709-1: the double-height band on the well's south wall where the GF wall is solid under the 1F wall
    solid = D(w["gf_solid_wall_in_zone_lm"]) + D(w["gf_columns_in_zone_lm"])
    beam_s = D(w["gf_overhead_line_in_zone_lm"]) - solid
    contact_hi = (D(LANDING_TOP) - D(GF_PAINT_TOP)) * (D(w["south"]) - D("5.87"))
    ret_lm = D(w["column_returns_lm"])      # proud column returns: inside the band on the solid run at most
    pl = R.double_height_band(solid, FFL_1F, GF_PLASTER_TOP)
    pl_hi = R.double_height_band(solid + ret_lm, FFL_1F, GF_PLASTER_TOP)
    pa_hi = R.double_height_band(solid + ret_lm, FFL_1F, GF_PAINT_TOP)
    pa_lo = R.double_height_band(solid, FFL_1F, GF_PAINT_TOP, [contact_hi])
    out["a_double_height"] = {
        "rule": "R-T709-1 (PROPOSED; scope: walls bounding a slab-free stairwell / void; provenance: owner Q-72 answer "
                "2026-11-02, continuous exposed height through a stairwell)",
        "south_wall_zone_lm": w["south"], "gf_solid_under_lm": s(solid),
        "gf_solid_pieces": {k: v["in_zone_lm"] for k, v in w["gf_pieces"].items() if k != "overhead"},
        "plaster_band": {"levels": [GF_PLASTER_TOP, FFL_1F], "m2": [s(pl), s(pl_hi)], "status": "BOUNDED: face "
                         "run by handle this run, heights T-556 DRAWING-CONFIRMED, FFL printed; high end adds the "
                         "column returns proud 0.05 (" + w["column_returns_lm"] + " lm) if they continue through the band"},
        "paint_band": {"levels": [GF_PAINT_TOP, FFL_1F], "m2": [s(pa_lo), s(pa_hi)],
                       "status": "BOUNDED: high adds the column returns; low takes the ST-02 corner landing (+4.696) against the wall over at most 1.15 m "
                                 "(7.02 - 5.87) takes 0 .. " + s(contact_hi) + " m2 of the band (its length along the "
                                 "wall not read)"},
        "held_beam_faces": [{"face": "south wall over the GF opening / curb (no wall below, overhead line A8)",
                             "lm": s(beam_s), "m2": None, "datum": "depth of the beam under the 1F south wall "
                             "(structural GF roof slab plan; not read this run)"},
                            {"face": "west well wall (1F wall AF7 over the GF dining; GF line 4B1 hidden)",
                             "lm": s(D(w["west"])), "m2": None,
                             "datum": "beam depth under the 1F west well wall (same sheet)"}],
        "engine_effect_if_wired": {"FIN.PLASTER": "+" + s(pl) + " .. " + s(pl_hi) + " m2 (new HELD/RELEASED band line under 1F-13 or GF-08, "
                                   "lane I decides the host)", "FIN.PAINT": "+" + s(pa_lo) + " .. " + s(pa_hi) + " m2"},
        "verdict": "ENGINE_OMISSION (small): GF-08 stops at its own soffit / ceiling and 1F-13 starts at +5.50 on a wall "
                   "that runs through the stairwell; the band in between is built and finished.",
    }

    # ---- (b) RETURNS -8.19 ------------------------------------------------------------------------------------------
    def _ret(x):
        return x["item_code"] == "FIN.PLASTER" and ("-OPENING-" in x["element_id"] or "-REVEAL-" in x["element_id"])
    rets = sorted([x for x in lines if _ret(x)], key=lambda x: x["element_id"])
    valued = [x for x in rets if x["class"] == "RELEASED"]
    blank = [x for x in rets if x["class"] != "RELEASED"]
    if len(rets) != 30 or len(valued) != 27:
        raise SystemExit(f"return census {len(rets)} / {len(valued)} is not 30 / 27")
    hn, ht, hr = _n(pls, "E26"), _n(pls, "F26"), _n(pls, "H26")
    br = R.return_bridge(hn, ht, hr, [repr(x["measured_net"]) for x in valued])
    his_internal_doors = _n(pls, "E44")
    out["b_returns"] = {
        "element": "door return = the plastered faces inside the wall thickness at a door opening: 2 jambs + head, "
                   "t x (2 x head + width) per door (T-634 R-T634-1, re-read by handle on 26 doors; OP-009 by T-676)",
        "his_row": {"row": 26, "count": int(hn), "depth": str(ht), "run": str(hr), "m2": str(q6(hn * ht * hr)),
                    "his_own_internal_door_count_row_44": int(his_internal_doors)},
        "engine": {"valued_lines": len(valued), "valued_m2": br["engine"],
                   "blank_held": [x["line_id"][:10] + " " + x["element_id"] for x in blank]},
        "bridge": br,
        "verdict": "RESOLVED (-8.19 closes exactly, R-T709-3): COUNT " + br["count_term"][0] + " .. " +
                   br["count_term"][1] + " (he prices 14 doors; the drawings carry 27 valued door openings with a "
                   "return and his own deduction list counts " + str(int(his_internal_doors)) + " internal doors: "
                   "FREELANCER omission, ENGINE_RIGHT) and UNIT " + br["unit_term"][0] + " .. " + br["unit_term"][1] +
                   " (his flat 0.20 x 5.70 = 1.14 per door vs the drawn mean " + br["engine_mean"] + ": 19 of the 26 "
                   "re-read doors sit in 0.15 walls and the heads are 2.20 (Q-55 C) / 2.50: RULE_DIFFERENCE). The split "
                   "depends on the order; the total does not. 3 blank returns stay HELD outside, never 0.",
    }

    # ---- (c) T-569 return-paint wiring on V3.0.70 ids -------------------------------------------------------------
    v8 = {r["face_id"]: r for r in t569["return_paint"]["valued"] + t569["return_paint"]["held"]}
    both_wet_ids = {r["id"] for r in t634["returns"]["rows"] if r["both_sides_wet"]}
    if set(BOTH_WET.values()) != both_wet_ids:
        raise SystemExit("both-sides-wet door set differs from T-634")
    rows, hi_all, hi_dry, hi_wet_only = [], D(0), D(0), D(0)
    for x in rets:
        fid = x["element_id"]
        pr = R.return_paint_row(fid, x["class"], x["measured_net"], fid in BOTH_WET)
        was = v8.get(fid)
        rows.append({"plaster_line": x["line_id"], "face_id": fid, "plaster_class": x["class"],
                     "plaster_m2": None if x["measured_net"] is None else s(D(repr(x["measured_net"]))),
                     "paint_row": pr, "v8_form": "same face id" if was else "NEW since V8",
                     "v8_class_then": None if not was else was["plaster_class"]})
        if pr["bound_beside_m2"]:
            hi_all += D(pr["bound_beside_m2"][1])
            if fid not in BOTH_WET:
                hi_wet_only += D(pr["bound_beside_m2"][1])
                if fid != EXTERNAL_DOOR:
                    hi_dry += D(pr["bound_beside_m2"][1])
    changed = [r for r in rows if r["v8_form"] != "same face id" or r["v8_class_then"] != r["plaster_class"]]
    out["c_return_paint"] = {
        "rule": "R-T709-4 (= the T-569 V8 form, restated on V3.0.70 line ids)",
        "rows": rows, "count": len(rows), "valued": sum(1 for r in rows if r["paint_row"]["bound_beside_m2"]),
        "held_by_name": sum(1 for r in rows if not r["paint_row"]["bound_beside_m2"]),
        "changed_since_v8": [{"face_id": r["face_id"], "then": r["v8_class_then"], "now": r["plaster_class"]}
                             for r in changed],
        "bound_sum_m2": [s(0), s(hi_all)],
        "physical_high_without_both_wet_and_external_side": s(hi_dry),
        "physical_high_without_both_wet": s(hi_wet_only),
        "note": "T-701's 'physically painted 19.17 .. 20.25' is these two highs (OP-009: which side of the external "
                "door reveal is facade render is not established); the low end stays 0 until the frame-covered depth "
                "is printed (frame / casing detail): a designer datum, not an owner question",
        "status": "HELD (frame-covered depth not printed); never a value, never 0, never in a released paint line",
    }

    # ---- (d) the 9 dry rooms -----------------------------------------------------------------------------------------
    dry = {r["room"]: r for r in t701["dry_rooms"]}
    rooms = []
    for rid in ["GF-01", "GF-15", "GF-08", "1F-01", "1F-10", "1F-11", "1F-13", "2F-03", "2F-01"]:
        dr, led, t7 = drawn["rooms"][rid], t556[rid], dry[rid]
        face = D(led["face_lm"])
        row = {"room": rid, "engine_face_lm": str(face), "chain_source": dr["chain_source"],
               "drawn_chain_perimeter": dr["perimeter"]}
        if rid in OPEN_ZONES:
            by = {}
            for e in dr["edges"]:
                by[e["layer"]] = str(q6(D(by.get(e["layer"], "0")) + D(e["lm"])))
            row.update({"re_measured": False, "chain_by_layer_lm": by,
                        "note": "open zone: the face is the T-147 region clip (walls outside the shaft box, open sides "
                                "excluded); a gross chain is not that face, so this run does not re-measure it (T-128 r2 "
                                "two traces stand)"})
        else:
            per = D(dr["perimeter"])
            gaps = sorted(str(q6(D(g["width"]))) for e in dr["edges"] for g in e["gaps"])
            want = sorted(str(q6(D(w_))) for w_, _, _ in GAP_TO_LEDGER[rid])
            if gaps != want:
                raise SystemExit(f"{rid}: drawn gaps {gaps} vs declared {want}")
            led_ops = {o["id"]: o for o in led["new"]["openings"]}
            ops = []
            for wd, oid, head in GAP_TO_LEDGER[rid]:
                o = led_ops[oid]
                own = None if head is None else q6(D(wd) * D(head))
                diff = None if own is None else q6(D(o["lo"]) - own)
                ops.append({"id": oid, "drawn_width": wd, "head_used": head, "own_m2": s(own),
                            "ledger_m2": [o["lo"], o["hi"]], "ledger_minus_own": s(diff),
                            "state": "HELD in the ledger (no height)" if own is None else
                            ("AGREE" if abs(diff) <= D("0.010") else "DIFFERS")})
            row.update({"re_measured": True, "drawn_minus_engine_lm": s(per - face), "openings": ops,
                        "curved_glazing": CURVED_GLAZING.get(rid),
                        "length_state": "AGREE" if abs(per - face) <= D("0.005") else "DIFFERS"})
        comp = {}
        for f in ("plaster", "paint"):
            x = t7[f]
            comp[f] = {"his": x["his_gross"], "his_lm": x["his_length_lm"],
                       "LENGTH": x["low"]["LENGTH"], "HEIGHT": [x["low"]["HEIGHT"], x["high"]["HEIGHT"]],
                       "DEDUCTIONS": [x["low"]["DEDUCTIONS"], x["high"]["DEDUCTIONS"]],
                       "engine_net": [x["low"]["net"], x["high"]["net"]]}
        L = D(comp["plaster"]["LENGTH"])
        row["bridge_t701"] = comp
        row["verdict"] = {
            "LENGTH": ("ENGINE_RIGHT (drawn face re-measured this run)" if row["re_measured"] else
                       "ENGINE_RIGHT (T-128 r2 two traces; not re-measured this run)") + (
                           "" if abs(L) > D("0.0001") else "; equal lengths"),
            "HEIGHT": "RULE_DIFFERENCE: his flat storey height vs plaster to the soffit (Q-72) and paint to the "
                      "finished ceiling (owner G1, Q-48 A)" + ("; annex datum bounded (Q-54 B, T-686 / R-T701-2)"
                                                              if rid == "GF-01" else ""),
            "DEDUCTIONS": "RULE_DIFFERENCE: every opening in full per room side (Q-73) vs his half list once; held "
                          "heights / beam ends HELD",
        }
        rooms.append(row)
    out["d_dry_rooms"] = rooms
    fixes = [o for r in rooms for o in r.get("openings", []) if o["state"] == "DIFFERS"]
    out["d_findings"] = [{"room": r["room"], **o} for r in rooms for o in r.get("openings", []) if o["state"] == "DIFFERS"]
    out["d_counts"] = {"re_measured": sum(1 for r in rooms if r["re_measured"]),
                       "not_re_measured_open_zones": sorted(OPEN_ZONES), "opening_differs": len(fixes)}
    # 1F-13 restated with his row 8 moved in (like for like, lengths only)
    t13 = dry["1F-13"]["plaster"]
    out["d_1F13_with_row_8"] = {"his_lm_rows_15_16": t13["his_length_lm"], "his_row_8_lm": str(r8["plaster"][0]),
                                "his_lm_all": str(D(t13["his_length_lm"]) + r8["plaster"][0]),
                                "engine_face_lm": t13["face_lm"],
                                "note": "his three 1F-zone rows vs the one drawn face: his surplus in length is his "
                                        "(T-552 ENGINE_RIGHT stands), the well walls are in the 39.45 once"}
    return out


def md(o):
    a, dh, b, c = o["a_shaft"], o["a_double_height"], o["b_returns"], o["c_return_paint"]
    L = [f"# T-709 residuals on {o['candidate']} (generated; research, unwired)", "",
         "## (a) shaft residual 54.00", "",
         f"- his row 8 {a['his_row_8']['length']} x {a['his_row_8']['height']} = {a['his_row_8']['m2']}: "
         f"{a['his_row_8']['binding']} to '{a['his_row_8']['bound_to']}' (his - drawn {a['his_row_8']['his_minus_drawn_lm']} lm)",
         f"- his row 24 {a['his_row_24']['length']} x {a['his_row_24']['height']} = {a['his_row_24']['m2']}: "
         f"length {a['his_row_24']['length_binding']}, level intervals near {a['his_row_24']['height']}: "
         f"{a['his_row_24']['printed_level_intervals_within_0.05_of_his_height'] or 'none'} -> UNRESOLVED",
         f"- double-height band (R-T709-1): plaster {dh['plaster_band']['m2'][0]} .. {dh['plaster_band']['m2'][1]} m2, paint {dh['paint_band']['m2'][0]} .. "
         f"{dh['paint_band']['m2'][1]} m2 over {dh['gf_solid_under_lm']} lm; beam faces HELD "
         f"{dh['held_beam_faces'][0]['lm']} + {dh['held_beam_faces'][1]['lm']} lm", "",
         "## (b) returns", "",
         f"- his {b['his_row']['count']} x {b['his_row']['depth']} x {b['his_row']['run']} = {b['his_row']['m2']} vs engine "
         f"{b['engine']['valued_lines']} lines {b['bridge']['engine']}: gap {b['bridge']['gap']} = COUNT "
         f"{b['bridge']['count_term']} + UNIT {b['bridge']['unit_term']}", "",
         "## (c) return paint on V3.0.70", "",
         f"- {c['count']} rows: {c['valued']} bounded 0 .. plaster, {c['held_by_name']} HELD by name; bound "
         f"{c['bound_sum_m2'][0]} .. {c['bound_sum_m2'][1]}; physical high without the both-wet doors and the external "
         f"side {c['physical_high_without_both_wet_and_external_side']} (with OP-009 {c['physical_high_without_both_wet']}); changed since V8: {c['changed_since_v8']}", "",
         "| line | face | plaster | paint bound | flag |", "|---|---|---|---|---|"]
    for r in c["rows"]:
        L.append(f"| {r['plaster_line'][:10]} | {r['face_id']} | {r['plaster_m2']} | {r['paint_row']['bound_beside_m2']} "
                 f"| {r['paint_row']['flag']} |")
    L += ["", "## (d) dry rooms", "", "| room | face lm | drawn | openings | LENGTH his-eng (m2) | verdict |",
          "|---|---|---|---|---|---|"]
    for r in o["d_dry_rooms"]:
        ops = "; ".join(f"{x['id']} {x['state']}" for x in r.get("openings", [])) or "-"
        dr = r.get("drawn_minus_engine_lm", "not re-measured (open zone)")
        L.append(f"| {r['room']} | {r['engine_face_lm']} | {dr} | {ops} | {r['bridge_t701']['plaster']['LENGTH']} | "
                 f"{r['verdict']['LENGTH']} |")
    return "\n".join(L) + "\n"


def main(argv):
    o = build()
    js = json.dumps(o, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    m = md(o)
    if "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == js and OUT_MD.read_text(encoding="utf-8") == m
        print("REPRODUCED" if ok else "DIFFERS")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(js, encoding="utf-8")
    OUT_MD.write_text(m, encoding="utf-8")
    print("written")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
