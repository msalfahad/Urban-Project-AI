"""T-206 (level chain run 2, residential review R5): the structural PDF sections, the sunken wet slabs and the
per-footing chains of the development villa fed into LEVEL_CHAIN_V1 as a NEW evidence set (R2).

The merged module engine/source/level_chain_v1.py is used unchanged (no new link type was needed: wet panels and footing
types are chains with their own links; see T-206_LEVEL_CHAIN_R2.md s.1). The T-200 input stays untouched; R2 = the
T-200 input + the evidence read this run (EVIDENCE_R2 below), each item with its Drive file title, page and the vector
measurement or DXF handle it comes from. Values, titles, layers and handles only: no drawing content is copied.
Nothing here is a BOQ quantity.

Run from the repository root:
    python3 -I research/agents_t206/t206_alsenan_check.py [--write]
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import level_chain_v1 as LC  # noqa: E402

HERE = Path(__file__).resolve().parent
T200_INPUT = ROOT / "research" / "agents_t200" / "ALSENAN_LEVEL_INPUT.json"

STPDF = "Drive 'Alsenan chalet project' / ST7757.pdf"
STDXF = "Drive 'Alsenan chalet project' / ST7757 dxf.dxf"
SAN = "Drive 'Alsenan chalet project' / sanitary-7757.pdf"

# --------------------------------------------------------------------------------------------------- printed evidence
# Footing schedule (ST7757.pdf p.9 'Schedule of Footings', column H in cm; T-042 read the same values from the DXF).
FOOTING_H_CM = {"F": 30, "F2": 35, "F3": 30, "F4": 40, "F5": 40, "F6": 50, "F7": 50, "F8": 50, "F9": 55, "F10": 50,
                "F11": 50, "F12": 70, "F13": 50, "F14": 50, "F15": 40, "FF": 55, "FN": 30}

# Under every isolated footing (ST7757.pdf p.13, BOTH typical details, the same stack): '5cm Screed', a membrane
# dimensioned '2' (cm, the sheet's unit: '5', '10', '10' on the same chain), '10cm Plain con.'. Vector check of the
# right detail: horizontal lines at y = 427.48 / 434.56 / 437.32 / 451.48 pt -> 7.08 / 2.76 / 14.16 pt = 5.0 / 1.95 /
# 10.0 cm at the chain's own scale 1.416 pt per cm (7.08 pt = the printed '5'); left detail 396.88 / 404.08 / 406.84 /
# 421.00 pt -> 5.08 / 1.95 / 10.0 cm. So the '2' T-042 / T-200 left unread is the membrane thickness, 2 cm.
UNDERLAY_FOOTING_M = 0.05 + 0.02
BLINDING_M = 0.10
UNDERLAY_REF = (f"{STPDF} p.13 TYP. DETAIL OF ISOLATED FOOTING (both details): '5cm Screed' + membrane dimensioned '2' "
                "(cm) = 0.07 m; vector: 7.08 + 2.76 pt at 1.416 pt/cm (the printed 5 and 10 on the same chain)")
BLINDING_REF = f"{STPDF} p.13 '10cm Plain con.' under both footing details (vector 14.16 pt = 10.0 cm)"
FORMATION_LIMIT_REF = (f"{STPDF} p.9 boxed note 1: excavation level not less than 1.5 m below the existing plot level "
                       "(a limit, never a value); design bearing 2.20 kg/cm2 (note 2) = the 1.5 m row of the "
                       "depth / B.C table on the same sheet; p.8 note 12 leaves the founding level to the site "
                       "(contractor + supervising engineer); owner Q-21 C")

# Sunken slabs: the slab legend (ST7757.pdf p.3-p.6) has a 'Sunken slab.' hatch (diagonal lines 7.1 pt apart; the
# 'Cantilever-portion.' hatch 2.8 pt, 'Bearing wall.' 3.2 pt). In the DXF the sunken hatch is HATCH ANSI31 scale 2000
# on layer S-HAT.BAT (the cantilever hatch ANSI31 scale 800): 5 on the GF roof slab sheet (= the 1F floor), 1 on the
# 1F roof slab sheet (= the 2F floor), none on the ground-beam or 2F roof sheets. Each lies under a room with a floor
# drain on sanitary-7757.pdf (hand registration on the 31.37 x 15.00 m plot frame, within about 0.5 m). No sheet
# prints the depth of the drop: no text, level or dimension inside or beside any sunken hatch (DXF texts within 0.6 m
# of each hatch: only beam names and slab bar callouts), no section cuts one.
SUNKEN = [  # (chain id, storey, DXF hatch handle, hatch extents mm in the DXF, sanitary room it lies under)
    ("1F-WET-275", "1F", "275", "63657..65563 x 47848..49598", "1F wet room with floor drain, north side (sheet 2)"),
    ("1F-WET-276", "1F", "276", "61967..63472 x 47848..49598", "1F wet room with floor drain, north side (sheet 2)"),
    ("1F-WET-280", "1F", "280", "52893..56437 x 38048..41048", "1F wet rooms with floor drains, south-west (sheet 2)"),
    ("1F-WET-287", "1F", "287", "55341..57153 x 38674..41048", "1F wet rooms with floor drains, south-west (sheet 2)"),
    ("1F-WET-298", "1F", "298", "69513..71713 x 43398..45378", "1F wet room with floor drain, east (sheet 2)"),
    ("2F-WET-5BF", "2F", "5BF", "21269..23069 x 46648..49648", "2F maid-room wet room with floor drain (sheet 3)"),
]
STOREY_FFL = {"1F": (5.50, "P7757 LEVEL '+5.50' (D1B, D16, D1D, D18, 1251); SECTION A-A (T-200)"),
              "2F": (9.70, "P7757 LEVEL '+9.70' (1352, 134E, 1350); SECTION A-A (T-200)")}
WET_LINKS = [["FFL", "SLAB_TOP", "WET_FLOOR_BUILD_UP"], ["SLAB_TOP", "SLAB_SOFFIT", "SLAB_THICKNESS"]]

# Searched for a printed structural level (T.O.S. / soffit / S.S.L) this run, beyond T-200's sheets.
SHEETS_SEARCHED = [
    f"{STPDF} p.1-16 (axis, foundation, ground-beam and three slab plans; notes p.8; schedules p.9-12; details p.13-16)",
    f"{STDXF} every TEXT / MTEXT / ATTRIB / DIMENSION text (nested inserts to depth 4, layout DETAILS too)",
    f"{SAN} sheets 1-3 (GF / 1F / 2F drainage plans)",
]


def _datum(cid, kind, value, status, ref, bound=None):
    d = {"chain_id": cid, "kind": kind, "value": value, "status": status, "ref": ref}
    if bound:
        d["bound"] = bound
    return d


def _layer(cid, layer, t, status, ref, method=None):
    ly = {"chain_id": cid, "layer": layer, "thickness": t, "status": status, "ref": ref}
    if method:
        ly["method"] = method
    return ly


def evidence_r2():
    """The additions of run 2, as LEVEL_CHAIN_V1 input fragments."""
    chains, datums, layers, uses = [], [], [], []
    # (1) the T-200 typical foundation chain gets the screed / membrane layer it held
    layers.append(_layer("GF-EXT-F8", "UNDERLAY", UNDERLAY_FOOTING_M, "DRAWING-CONFIRMED", UNDERLAY_REF))
    datums.append(_datum("GF-EXT-F8", "GB_BOTTOM", None, "HELD",
                         f"{STPDF} p.13 'Ground Beams for exterior walls': underside labelled 'Outer Normal ground "
                         "level' and depth 'FOLLOW ARCH.' (names, no value; whether the existing +-0.00 or the court "
                         "+0.15 is meant is not fixed by the set)"))
    # (2) one foundation chain per footing type
    ftg_links = [["GB_TOP", "FOOTING_TOP", "NECK_RUN"], ["FOOTING_TOP", "FOOTING_BOTTOM", "FOOTING_DEPTH"],
                 ["FOOTING_BOTTOM", "BLINDING_TOP", "UNDERLAY"], ["BLINDING_TOP", "FORMATION", "BLINDING_THICKNESS"],
                 ["EXISTING_GROUND", "FORMATION", "EXCAVATION_DEPTH"]]
    lift_links = [["FFL", "FOOTING_TOP", "LIFT_PIT_DEPTH"]] + ftg_links[1:]
    for t, h in FOOTING_H_CM.items():
        cid = f"FTG-{t}"
        lift = t == "FF"      # the lift footing: its own detail (p.14), the pit base is its top, no neck
        chains.append({"chain_id": cid, "family": "FOUNDATION_LIFT" if lift else "FOUNDATION_FOOTING", "storey": "GF",
                       "element": (f"lift footing {t} under the pit (schedule H {h} cm; ST7757.pdf p.14 DETAIL OF LIFT "
                                   "WITH ISOLATED FOOTING)" if lift else f"isolated footing type {t} (schedule H {h} cm)"),
                       "links": lift_links if lift else ftg_links})
        datums += [
            _datum(cid, "EXISTING_GROUND", 0.0, "DRAWING-CONFIRMED",
                   "existing plot level +-0.00 (P7757 / ST7757 SH08 block LEL; T-200)"),
            _datum(cid, "FORMATION", -1.5, "DRAWING-CONFIRMED", FORMATION_LIMIT_REF, bound="AT_MOST"),
            _datum(cid, "FORMATION", None, "HELD", "founding / formation level: not printed; owner Q-21 C"),
        ]
        if lift:
            datums += [
                _datum(cid, "FFL", 1.0, "DRAWING-CONFIRMED", "GF FFL +1.00 (P7757 LEVEL; T-200); p.14 'F.F.L' at the "
                                                             "lift door"),
                _datum(cid, "FOOTING_TOP", None, "HELD", f"{STPDF} p.14: pit depth 'As Per Lift Manufactures "
                                                         "recommendations' (no value)"),
            ]
        else:
            datums.append(_datum(cid, "GB_TOP", None, "HELD",
                                 "ground-beam top: follows the GF slab top, which no sheet prints (T-200; p.13 "
                                 "exterior detail names it 'Ground Floor slab level')"))
        layers += [
            _layer(cid, "FOOTING_DEPTH", h / 100.0, "DRAWING-CONFIRMED", f"{STPDF} p.9 Schedule of Footings {t} H {h}"
                   + (" (p.14 'AS PER SCHEDULE')" if lift else "")),
            _layer(cid, "BLINDING_THICKNESS", BLINDING_M, "DRAWING-CONFIRMED",
                   f"{STPDF} p.14 '10cm Plain con.' under the lift footing" if lift else BLINDING_REF),
        ]
        if not lift:      # the lift detail prints '5cm Screed' + 'Water proofing membrane' with NO membrane thickness:
            # the p.13 '2' belongs to the isolated-footing details and is not carried to another detail (ERS s.3)
            layers.append(_layer(cid, "UNDERLAY", UNDERLAY_FOOTING_M, "DRAWING-CONFIRMED", UNDERLAY_REF))
    # (3) one floor chain per sunken wet panel
    for cid, storey, handle, ext, room in SUNKEN:
        ffl, ffl_ref = STOREY_FFL[storey]
        chains.append({"chain_id": cid, "family": "FLOOR_SUNKEN_WET", "storey": storey,
                       "element": f"sunken slab panel (DXF HATCH {handle}, {ext} mm) under: {room}",
                       "links": WET_LINKS})
        datums += [
            _datum(cid, "FFL", ffl, "DRAWING-CONFIRMED",
                   f"storey FFL {ffl_ref}; no separate wet-room level is printed on P7757 or {SAN} (searched)"),
            _datum(cid, "SLAB_TOP", None, "HELD",
                   f"{STDXF} HATCH {handle} layer S-HAT.BAT ANSI31 x2000 = legend 'Sunken slab.' (ST7757.pdf p.4 / "
                   "p.5): the slab top is BELOW the storey's slab top by a drop no sheet prints"),
        ]
        layers.append(_layer(cid, "SLAB_THICKNESS", 0.16, "DRAWING-CONFIRMED",
                             f"{STDXF} SH12 S-NOTE / {STPDF} p.8 note 18: all slabs 16 cm unless stated otherwise "
                             "(nothing stated for the sunken panels)"))
        normal = f"{storey}-FLOOR"
        uses.append({"use_id": f"W-{cid}", "quantity": "slab top / soffit of the sunken wet panel taken as the "
                     "storey's normal slab top (concrete, ceiling height of the room below, wet-room screed)",
                     "chain_id": cid, "needs": "SLAB_TOP", "used": {"chain_id": normal, "kind": "SLAB_TOP"},
                     "ref": f"{STDXF} HATCH {handle}; a takeoff that does not split the panel out of {normal}"})
    return {"chains": chains, "datums": datums, "layers": layers, "uses": uses}


def load_t200():
    return json.loads(T200_INPUT.read_text(encoding="utf-8"))


def build_r2(base=None):
    p = copy.deepcopy(base if base is not None else load_t200())
    # the T-183 r2 ruling (structural pool detail governs the base) as in T-200's 'with_t183_ruling' run
    p["datums"] = [d for d in p["datums"] if not (d["chain_id"] == "POOL" and d["kind"] == "POOL_BASE_UNDERSIDE")]
    ev = evidence_r2()
    for k in ("chains", "datums", "layers", "uses"):
        p[k] = p[k] + ev[k]
    p["project"] = p["project"] + "; R2 = T-200 input + T-206 evidence (research/agents_t206)"
    p["sheets_searched_r2"] = SHEETS_SEARCHED
    return p


def relative_stack(h_m, underlay_m=UNDERLAY_FOOTING_M, blinding_m=BLINDING_M):
    """Heights ABOVE the formation (m) of blinding top, footing bottom and footing top: printed layers only. The
    absolute levels need the formation, which is HELD (Q-21 C); this is the relation, not a level."""
    for v, n in ((h_m, "footing depth"), (underlay_m, "underlay"), (blinding_m, "blinding")):
        if v is None:
            raise ValueError(f"{n} missing: nothing is defaulted")
        if v < 0 or v > 5:
            raise ValueError(f"{n} {v} m out of range (cm given as m?)")
    bt = blinding_m
    fb = bt + underlay_m
    return {"blinding_top": round(bt, 4), "footing_bottom": round(fb, 4), "footing_top": round(fb + h_m, 4)}


def footing_table():
    """Per footing type: printed layers, the relation to the formation, and two labelled what-ifs that are NOT values:
    LIMIT = formation at the printed limit -1.50; CONVENTION = the released V2.9 neck convention (footing underside at
    -1.50, h = 1.00 + 1.50 - H), which implies a formation 0.17 m deeper than the limit."""
    rows = []
    for t, h in FOOTING_H_CM.items():
        if t == "FF":
            rows.append({"type": t, "H_m": h / 100.0, "status": "HELD (formation, pit depth and the membrane "
                         "thickness of the lift detail not printed)", "above_formation": None,
                         "detail": "ST7757.pdf p.14 lift detail; screed 0.05 + membrane (no thickness) + blinding 0.10"})
            continue
        s = relative_stack(h / 100.0)
        rows.append({"type": t, "H_m": h / 100.0, "status": "HELD (formation not printed, Q-21 C)",
                     "above_formation": s,
                     "if_formation_at_limit_-1.50": {"footing_bottom": round(-1.5 + s["footing_bottom"], 4),
                                                     "footing_top": round(-1.5 + s["footing_top"], 4)},
                     "released_convention_footing_bottom_-1.50": {
                         "footing_top": round(-1.5 + h / 100.0, 4),
                         "implied_formation": round(-1.5 - s["footing_bottom"], 4)}})
    return rows


def run():
    return LC.check(build_r2())


def _brief(res):
    return {"summary": res["summary"],
            "datums": [(r["chain_id"], r["kind"], r["value"], r["status"], r["basis"]) for r in res["datums"]],
            "links": [(r["chain_id"], r["layer"], r["thickness"], r["status"], r["missing"]) for r in res["links"]],
            "bounds": [(b["chain_id"], b["kind"], b["bound"], b["value"], b["result"]) for b in res["bounds"]],
            "uses": [(u["use_id"], u["code"], u["detail"], u["sensitivity"]) for u in res["uses"]],
            "owner_manual_layers": [(m["chain_id"], m["layer"], m["thickness"]) for m in res["owner_manual_layers"]]}


if __name__ == "__main__":
    out = {"r2": _brief(run()), "footings": footing_table(), "sheets_searched_r2": SHEETS_SEARCHED}
    text = json.dumps(out, indent=1, ensure_ascii=False)
    if "--write" in sys.argv:
        (HERE / "ALSENAN_LEVEL_INPUT_R2.json").write_text(
            json.dumps(build_r2(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        (HERE / "summary_r2.json").write_text(text + "\n", encoding="utf-8")
    print(json.dumps(out["r2"]["summary"], indent=1))
