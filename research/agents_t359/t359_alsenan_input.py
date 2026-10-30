"""Builds ALSENAN_BAR_DETAIL_INPUT.json for the T-359 census (development villa; printed readings only).

Sources (Drive 'Alsenan chalet project', private copies in the git-excluded folder, never committed; re-read this run):
  'ST7757 dxf.dxf' (sha256 9f9d1179..): text entities by handle (layers S-TEXT.D, S-TEXT-SLAB).
  'ST7757.pdf' (sha256 74da1523.., 16 pages, no text layer): rendered at 60 / 170 / 200 / 250 / 300 dpi and read by
  eye; p.4 / p.5 / p.6 slab plans, p.7 DETAIL OF SWIMMING POOL + DETAIL OF DOME, p.13 ground-beam sections,
  p.14 DETAIL OF LIFT WITH ISOLATED FOOTING + TYPICAL BOUNDARY WALL (plan, section A-A), p.15, p.16 TYPICAL STEEL
  LAYOUT - STAIR SECTION + TYPICAL DETAIL OF STAIR BEAM.
PDF-only labels carry 'pdf p.N <detail>, <position>' instead of a handle (the detail sheets 13-16 are not in the DXF).
r2 (2026-10-30): every bar label inside each cited detail's extent is listed under "details" (DXF: all TEXT entities in the
p.7 pool / dome extents, swept by coordinates, incl. the exploded bar-shape row; PDF p.14 / p.16 read at 170 - 250 dpi),
each cited by a population; drawn bar shapes are tied to their population (end_shape RULE option B with the shape's
handle: shape drawn, legs not dimensioned); each population names the blank V3.0.16 candidate lines it would fill.

Usage: python -I t359_alsenan_input.py <board docs/agents/rfi folder> ALSENAN_BAR_DETAIL_INPUT.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def P(ref, note=""):
    return {"state": "PRINTED", "ref": ref, **({"note": note} if note else {})}


def N(note):
    return {"state": "NOT_PRINTED", "note": note}


def T(ref, note=""):
    return {"state": "PRINTED_TYPICAL", "ref": ref, **({"note": note} if note else {})}


def NA(note):
    return {"state": "NOT_APPLICABLE", "note": note}


def RULE(rule, note):
    return {"state": "RULE", "rule": rule, "note": note}


OPT_B = "OPTION_B_2026-10-29"   # owner: only drawn / printed bar parts counted, undrawn parts HELD
END_B = RULE(OPT_B, "end drawn without a dimension: the drawn straight part only, the leg / anchorage HELD")


def SHAPE(ref, shape):
    """A bar shape that the set DRAWS (legs, cranks, hooks, returns) without dimensioning its legs."""
    return {"state": "RULE", "rule": OPT_B, "ref": ref,
            "note": f"shape drawn: {shape}; leg / crank lengths not dimensioned: option B holds them"}


def CONFLICT(refs, note):
    return {"state": "CONFLICT", "refs": list(refs), "note": note}


CAND = "HL:STAIR_POOL_TANK_STEEL:"
FLIGHTS_01 = ("MS1-L", "MS1-U", "MS2-L", "MS2-U")
FLIGHTS_02 = ("RS-A", "RS-S")


def fam(flights, family, dev=False, stair="ST-01"):
    out = []
    for f in flights:
        out.append(f"{stair}:{f}:{family}")
        if dev:
            out.append(f"{stair}:{f}:{family}:DEVELOPMENT")
    return out


TYP_BIND = {   # typical p.16 family -> blank candidate lines (V3.0.16) per stair
    "ST-01": {"TOPH": fam(FLIGHTS_01, "TOP_BARS_AT_THE_HEAD"),
              "TOPF": fam(("MS1-U", "MS2-L", "MS2-U"), "TOP_BARS_AT_THE_FOOT"),
              "DIST": fam(FLIGHTS_01, "DISTRIBUTION_UNDER_THE_MAIN_BARS", True),
              "STEP": fam(FLIGHTS_01, "STEP_BARS_TREAD_RISER_SHAPE", True),
              "NOSE": fam(FLIGHTS_01, "NOSING_BAR_ONE_PER_TREAD"),
              "LTOP": [f"ST-01:{s}:LANDING_STRIP_TOP_BARS_ACROSS_THE_STAIR{d}" for s in ("GF-STRIP", "1F-STRIP")
                       for d in ("", ":DEVELOPMENT")]},
    "ST-02": {"TOPH": fam(FLIGHTS_02, "TOP_BARS_AT_THE_HEAD", stair="ST-02"),
              "TOPF": ["ST-02:RS-A:TOP_BARS_AT_THE_FOOT"],
              "DIST": fam(FLIGHTS_02, "DISTRIBUTION_UNDER_THE_MAIN_BARS", True, "ST-02"),
              "STEP": fam(FLIGHTS_02, "STEP_BARS_TREAD_RISER_SHAPE", True, "ST-02"),
              "NOSE": fam(FLIGHTS_02, "NOSING_BAR_ONE_PER_TREAD", stair="ST-02"),
              "LTOP": []},
}
NO_LINE = {
    "TOPG": "no candidate line: the merged T-166 ledger carries no top bar over a flight foot on a ground beam "
            "(F-T359-1, G-T359-1); an integration must not add one before the applicability is answered",
    "LTOP": "no candidate line: the round stair has no landing-top family in the T-166 ledger",
    "LEB": "no candidate line and no member: the Alsenan landings sit on B2 / B3 / walls (T-166 s.5); never counted",
    "GB": "no candidate line here: a ground beam under a flight foot, where one exists, is a ground-beam ledger member",
}
# p.16 TYPICAL STEEL LAYOUT-STAIR SECTION: every bar label, by position (PDF only; read at 170 - 250 dpi)
P16 = "pdf p.16 TYPICAL STEEL LAYOUT-STAIR SECTION"
P16_LABELS = [
    ("U-TOPH", "6%%c14/m", "upper section, top bars at the +4.00 head"),
    ("U-NOSE", "1%%c12", "upper section, nosing"), ("U-STEP", "%%c8/15", "upper section, step bar"),
    ("U-MAIN", "8%%c16/m", "upper section, waist bottom"), ("U-DIST", "%%c12/20cm", "upper section, under the main bars"),
    ("U-TOPF", "6%%c14/m", "upper section, top bars from the S.S.L +2.00 landing (flight foot)"),
    ("U-LEBT", "2%%c12", "upper section, landing edge beam 20 x 40 top"),
    ("U-LTOP", "6%%c12/m", "upper section, landing top dot row"),
    ("U-LEBB", "4%%c16", "upper section, landing edge beam bottom"),
    ("U-LAND", "8%%c16/m", "upper section, landing bottom dot row"),
    ("UX-NOSE", "1%%c12", "upper exploded row, nosing bar at the step bar corner"),
    ("UX-STEP", "%%c8/15", "upper exploded row, step bar (tread + riser L)"),
    ("UX-TOPH", "6%%c14/m", "upper exploded row, head top bar: slope + horizontal + end hook"),
    ("UX-MAINH", "8%%c16/m", "upper exploded row, main bar: slope + horizontal into the head + end hook"),
    ("UX-DIST", "%%c12/20cm", "upper exploded row, distribution dot on the main bar"),
    ("UX-MAINF", "8%%c16/m", "upper exploded row, main bar: slope + horizontal into the landing bottom"),
    ("UX-LTOP", "6%%c12/m", "upper exploded row, landing top bar (straight)"),
    ("UX-TOPF", "6%%c14/m", "upper exploded row, foot top bar: horizontal in the landing top + slope + end hook"),
    ("UX-LAND", "8%%c16/m", "upper exploded row, landing bottom bar: horizontal + slope up the flight"),
    ("L-LEBT", "2%%c12", "lower section, landing edge beam top"), ("L-LTOP", "6%%c12/m", "lower section, landing top"),
    ("L-LEBB", "4%%c16", "lower section, landing edge beam bottom"),
    ("L-LAND", "8%%c16/m", "lower section, landing bottom"),
    ("L-TOPH", "6%%c14/m", "lower section, top bars from the landing into the flight (head)"),
    ("L-NOSE", "1%%c12", "lower section, nosing"), ("L-STEP", "%%c8/15", "lower section, step bar"),
    ("L-MAIN", "8%%c16/m", "lower section, waist bottom"),
    ("L-TOPG", "6%%c16/m", "lower section, top bars over the foot on the G.B"),
    ("L-DIST", "%%c12/20cm", "lower section, under the main bars"),
    ("L-GBT", "3%%c14", "lower section, G.B top"), ("L-GBS", "2%%c14/30cm", "lower section, G.B sides"),
    ("L-GBL", "%%c8/15cm", "lower section, G.B links"), ("L-GBB", "4%%c16", "lower section, G.B bottom"),
    ("LX-LTOP", "6%%c12/m", "lower exploded row, landing top bar (straight)"),
    ("LX-TOPH", "6%%c14/m", "lower exploded row, head top bar: hook + horizontal in the landing top + slope down"),
    ("LX-LAND", "8%%c16/m", "lower exploded row, landing bottom bar: hook + horizontal + slope down the flight"),
    ("LX-DIST", "%%c12/20cm", "lower exploded row, distribution dot on the main bar"),
    ("LX-MAIN", "8%%c16/m", "lower exploded row, main bar: slope + vertical leg down into the G.B"),
    ("LX-STEP", "%%c8/15", "lower exploded row, step bar"), ("LX-NOSE", "1%%c12", "lower exploded row, nosing bar"),
    ("LX-TOPG", "6%%c16/m", "lower exploded row, foot top bar: slope + vertical leg down to the +0.00 T.O.B"),
]
SB = "pdf p.16 TYPICAL DETAIL OF STAIR BEAM"
SB_LABELS = [("SB-T1", "2%%c12", "top bars over the cranked part"), ("SB-L1", "6%%c8/m", "links in the cranked part"),
             ("SB-T2", "2%%c12", "top bars in the straight part"), ("SB-B", "4%%c16", "bottom bars"),
             ("SB-L2", "6%%c8/m", "links in the straight part")]   # 'AS PER SCH.' there is a depth dimension


def p16(code):
    return f"{P16}: {code}"


def pop(pop_id, element, element_id, component, label, source, attrs=None, **kw):
    d = {"pop_id": pop_id, "element": element, "element_id": element_id, "component": component,
         "label": label, "source": source, "attrs": attrs or {}}
    d.update(kw)
    return d


def stairs():
    out = []
    typ = "pdf p.16 TYPICAL STEEL LAYOUT-STAIR SECTION (N.T.S.)"
    # ST-01 GF -> 1F (p.4) and 1F -> 2F (p.5): the plans print the main bars per flight / landing strip
    for el, sheet, hs in (("ST-01 GF->1F", "p.4", ("490", "491", "48F")), ("ST-01 1F->2F", "p.5", ("748", "749", "747"))):
        fl = "GF" if sheet == "p.4" else "1F"
        eid = "ST-01-" + fl
        flights = ("MS1-L", "MS1-U") if fl == "GF" else ("MS2-L", "MS2-U")
        out.append(pop(f"{eid}-MAIN", "STAIR ST-01", eid, "main bottom bars along the flights", "8%%C16/m",
                       f"dxf {hs[0]} / {hs[1]} ({sheet} plan, vertical labels on the two flights)", {
                           "layer": T(typ, "bottom layer only on the typical; the plan label gives no layer"),
                           "direction": P(f"dxf {hs[0]} / {hs[1]}", "label and bar line along the flight"),
                           "extent": P(f"dxf {hs[0]} / {hs[1]} + verified flight concrete (T-184 / T-290)",
                                       "bar line over the straight flights; the winder turn is its own row"),
                           "end_shape": SHAPE(f"{p16('UX-MAINH')} / {p16('UX-MAINF')} / {p16('LX-MAIN')} (typical)",
                                              "typical only: horizontal into the head + hook, horizontal into the "
                                              "landing bottom at a foot, vertical leg into a G.B")},
                       rfi={}, gap="G-T359-1",
                       labels=[f"dxf {hs[0]}", f"dxf {hs[1]}"] + ([p16("U-MAIN"), p16("UX-MAINH"), p16("UX-MAINF"),
                                                                    p16("L-MAIN"), p16("LX-MAIN")] if fl == "GF" else []),
                       candidate_lines=fam(flights, "MAIN_BOTTOM_BARS_ALONG_THE_WAIST", True)
                       + [f"ST-01:{fl}-STRIP:FLIGHT_BARS_RUNNING_THROUGH_THE_STRIP"],
                       note="T 16 waist on the plan (T-184, Q-47 A); layer from the typical only"))
        out.append(pop(f"{eid}-LAND", "STAIR ST-01", eid, "landing strip bottom bars across the shaft", "8%%C16/m",
                       f"dxf {hs[2]} ({sheet} plan, horizontal label over the landing)", {
                           "layer": T(typ, "landing bottom 8ø16/m on the typical"),
                           "direction": P(f"dxf {hs[2]}", "across the shaft"),
                           "extent": P(f"dxf {hs[2]}", "bar line wall to wall of the 2.50 m shaft"),
                           "end_shape": END_B},
                       rfi={}, gap="G-T359-1",
                       labels=[f"dxf {hs[2]}"] + ([p16("U-LAND"), p16("UX-LAND"), p16("L-LAND"), p16("LX-LAND")]
                                                  if fl == "GF" else []),
                       candidate_lines=[f"ST-01:{fl}-STRIP:LANDING_STRIP_BOTTOM_BARS_ACROSS_THE_STAIR{d}"
                                        for d in ("", ":DEVELOPMENT")],
                       note="the typical's landing-bottom shape (UX-LAND / LX-LAND) runs on down the flight as a main "
                            "bar: on the typical the landing bottom and the flight main bars are one cranked bar"))
    # the components that only the typical section prints (no Alsenan plan or section names them)
    tcomp = [
        ("TOPH", "top bars at the head of each flight", "6%%c14/m", ("U-TOPH", "UX-TOPH", "L-TOPH", "LX-TOPH"),
         "slope + horizontal into the head / landing top + end hook"),
        ("TOPF", "top bars at a foot on a landing", "6%%c14/m", ("U-TOPF", "UX-TOPF"),
         "horizontal in the landing top + slope + end hook"),
        ("TOPG", "top bars at a foot on a ground beam (G.B)", "6%%c16/m", ("L-TOPG", "LX-TOPG"),
         "slope + vertical leg down to the +0.00 T.O.B"),
        ("DIST", "distribution bars under the main bars", "%%c12/20cm", ("U-DIST", "UX-DIST", "L-DIST", "LX-DIST"),
         "straight (seen as a dot)"),
        ("STEP", "step bars (tread + riser shape)", "%%c8/15", ("U-STEP", "UX-STEP", "L-STEP", "LX-STEP"),
         "tread + riser L"),
        ("NOSE", "nosing bar, one per tread", "1%%c12", ("U-NOSE", "UX-NOSE", "L-NOSE", "LX-NOSE"),
         "straight (dot at the step-bar corner)"),
        ("LTOP", "landing top bars", "6%%c12/m", ("U-LTOP", "UX-LTOP", "L-LTOP", "LX-LTOP"), "straight"),
    ]
    for el, eid, rfi_id in (("STAIR ST-01", "ST-01", "RFI-S24"), ("STAIR ST-02", "ST-02", "RFI-S27")):
        for code, comp, lab, labs, shape in tcomp:
            src = f"{P16}: " + " / ".join(labs)
            a = {"layer": P(src), "direction": P(src),
                 "extent": N("bar lengths drawn, not dimensioned (N.T.S.)"),
                 "end_shape": SHAPE(f"{P16}: " + " / ".join(x for x in labs if "X-" in x), shape)}
            if code in ("NOSE",):
                a["spacing_or_count"] = NA("one bar per tread")
            lines = TYP_BIND[eid].get(code, [])
            out.append(pop(f"{eid}-T-{code}", el, eid, comp, lab, src, a, typical_only=True,
                           rfi={}, gap="G-T359-1", labels=[p16(x) for x in labs],
                           candidate_lines=lines, **({} if lines else {"no_line_reason": NO_LINE[code]}),
                           note="typical arrangement; no Alsenan print ties it to this stair (family master B7-14: "
                                "'typical-only stair families, p.16 reading not ruled')"))
        out.append(pop(f"{eid}-T-LEB", el, eid, "landing edge beam 20 x 40 of the typical (2ø12 top, 4ø16 bottom)",
                       None, f"{P16}: U-LEBT / U-LEBB / L-LEBT / L-LEBB", not_drawn=True, rfi={}, gap="G-T359-1",
                       labels=[p16(x) for x in ("U-LEBT", "U-LEBB", "L-LEBT", "L-LEBB")],
                       no_line_reason=NO_LINE["LEB"],
                       note="a member of the typical only; no such beam on the Alsenan plans"))
        out.append(pop(f"{eid}-T-GB", el, eid, "ground beam under the typical's flight foot (3ø14 / 2ø14/30cm / "
                       "ø8/15cm / 4ø16)", None, f"{P16}: L-GBT / L-GBS / L-GBL / L-GBB", not_drawn=True, rfi={},
                       gap="G-T359-1", labels=[p16(x) for x in ("L-GBT", "L-GBS", "L-GBL", "L-GBB")],
                       no_line_reason=NO_LINE["GB"],
                       note="the typical's G.B; an Alsenan foot member, where one exists, is a ground-beam ledger "
                            "member with its own schedule: these bars are never added from the typical"))
    # ST-02 round stair: straight part and curved part (p.4)
    out.append(pop("ST-02-MAIN-S", "STAIR ST-02", "ST-02", "main bottom bars along the straight flight", "8%%C16/m",
                   "dxf 53D (p.4 plan, vertical label on the straight flight)", {
                       "layer": T("pdf p.16 typical", "bottom on the typical only"),
                       "direction": P("dxf 53D"), "extent": N("waist profile of the straight part from levels not printed"),
                       "end_shape": END_B},
                   rfi={"extent": "RFI-A03"}, gap="G-T359-1", note="riser count / landing levels asked in RFI-A03",
                   labels=["dxf 53D"], candidate_lines=fam(FLIGHTS_02, "MAIN_BOTTOM_BARS_ALONG_THE_WAIST", True, "ST-02")))
    out.append(pop("ST-02-MAIN-H", "STAIR ST-02", "ST-02", "bars along the straight landing run", "8%%C16/m",
                   "pdf p.4 plan, horizontal label east of column CA (no modelspace text entity found for it)", {
                       "layer": T("pdf p.16 typical"), "direction": P("pdf p.4"),
                       "extent": P("pdf p.4", "bar line drawn from the curve to beam B21"), "end_shape": END_B},
                   rfi={}, gap="G-T359-1", labels=["pdf p.4 ST-02 horizontal 8ø16/m east of column CA"],
                   candidate_lines=["ST-02:RS-LD:BOTTOM_BARS"]))
    out.append(pop("ST-02-MAIN-C", "STAIR ST-02", "ST-02", "main bars along the curved part RS-C", "8%%C16/m",
                   "dxf 5BC (p.4 plan, label on the arc bar line)", {
                       "layer": T("pdf p.16 typical"), "direction": P("dxf 5BC", "along the arc"),
                       "extent": N("soffit form and thickness of the curved part not printed"),
                       "end_shape": END_B},
                   rfi={"extent": "RFI-S27"}, gap="G-T359-1", labels=["dxf 5BC"],
                   candidate_lines=["ST-02:RS-C:ALL_FAMILIES"]))
    # elements owned by other ledgers, listed so that they are never counted twice
    out.append(pop("ST-02-GF126", "STAIR ST-02", "GF-126", "slab bars beside the round stair", "6%%C14/m",
                   "dxf 533 (p.4)", owned_by="slab ledger T-152 panel GF-126 (HELD, RFI-B-S10)", labels=["dxf 533"]))
    for bid in ("BM-GF-015", "BM-1F-001", "BM-GF-057"):
        out.append(pop(f"{bid}-STAIRBEAM", "STAIR ST-01" if bid != "BM-GF-057" else "STAIR ST-02", bid,
                       "stair beam B3 '(With Stair)' (p.16 TYPICAL DETAIL OF STAIR BEAM, cranked)", "",
                       "dxf 6B8 / 6B6 / 1826 '(With Stair)'",
                       labels=[f"{SB}: {c}" for c, _, _ in SB_LABELS],
                       owned_by=f"beam ledger T-149 {bid} (HELD; crank RFI-B-S22)"))
    # entrance flight E1 and stair-hall flight D1: no bar printed anywhere
    out.append(pop("E1-ALL", "STAIR E1", "E1", "every bar", None, "dxf riser lines 18A .. 179 (p.3); no bar text "
                   "within 3 m", not_drawn=True, rfi={"all": "RFI-S26"}, candidate_lines=["ST-03:E1:ALL_FAMILIES"]))
    out.append(pop("D1-ALL", "STAIR D1", "D1", "every bar", None, "dxf riser lines 1C4 .. 1C7 (p.3); no bar text "
                   "within 3 m", not_drawn=True, rfi={"all": "RFI-S26"}, candidate_lines=["ST-01b:D1:ALL_FAMILIES"]))
    out.append(pop("ST-01-WINDER", "STAIR ST-01", "MS1-T", "winder turn bars", None,
                   "p.4 wedge lines; p.16 typical shows no winder", not_drawn=True, rfi={"all": "RFI-S24"},
                   candidate_lines=["ST-01:MS1-T:STEP_NOSING_BARS"]))
    return out


POOL_DET = "dxf p.7 DETAIL OF SWIMMING POOL (title 1864, N.I.S 186A)"
# every TEXT entity inside the pool detail extent (x -77000 .. -56500, y 40000 .. 56500 drawing units), swept by
# coordinates in ST7757 dxf (9f9d1179..): section labels and the exploded bar-shape row under the section
POOL_LABELS = [("1896", "3%%c16"), ("192F", "6%%c12/m"), ("1906", "7%%C12/m"), ("1893", "7%%C14/m"),
               ("191F", "%%c10/20cm"), ("188D", "%%c12/20cm"), ("192E", "%%c10/20cm"), ("18FC", "%%c12/20cm"),
               ("1907", "6%%c12/m"), ("192B", "4%%c16"), ("18D3", "6%%c12/m"), ("18F8", "6%%c12/m"),
               ("18F0", "6%%c12/m"), ("18B0", "7%%c14/m"), ("1881", "3%%c16"), ("18AD", "6%%c14/m"),
               ("19B0", "7%%c14/m"), ("18AA", "7%%c14/m"), ("1874", "5cm SECREED."),
               ("1876", "5cm INSULATION MEMBRANE."), ("1877", "10cm PLAIN CONCRETE."),
               ("1929", "6%%c12/m"), ("18DD", "6%%c12/m"), ("18DB", "6%%c12/m"), ("18D7", "6%%c12/m"),
               ("18A8", "7%%C14/m"), ("187C", "7%%C14/m"), ("1860", "7%%c14/m"), ("1869", "7%%c14/m"),
               ("1864", "%%uDETAIL OF SWIMMING POOL."), ("186A", "(N.I.S)")]
POOL_UNLABELLED_SHAPES = [
    {"ref": "dxf 1868 + 1865 + 1863", "shape": "hook + horizontal in the deep floor + long slope up (no label on it)",
     "tied_to": "POOL-F-SLOPE", "note": "same course as the section's 199F + 189C (deep floor -> slope); diameter and rate "
     "are those of the section labels 18D3 / 1907 only by position: the shape itself prints none"},
    {"ref": "dxf 185D + 18D8 + 18DE", "shape": "slope + horizontal into the shallow floor + end hook (no label on it)",
     "tied_to": "POOL-F-SHALLOW", "note": "the 18DB label sits on the parallel shape 185E + 18DA, not on this one"},
]


def pool():
    out = []
    det = "p.7 DETAIL OF SWIMMING POOL (N.I.S.)"
    face = lambda h, n: P(f"dxf {h}", n)
    wall_ext = N("the detail draws a deep-end (R1) and a shallow-end (R2) wall with different bars; which "
                 "population each wall of the flat 1.15 m pool (owner Q-26 A) takes is not printed; wall 1.20 m to the "
                 "structure line is verified concrete (T-183 r2)")
    shapes = {
        "R1-WV-OUT": SHAPE("dxf 187C on 185B; section 1879 + bend 1886 into 1870",
                           "L-bar: outer-face vertical, foot bent into the floor BOTTOM layer"),
        "R1-WV-IN": SHAPE("dxf 18A8 on 185C; section 18A2 + bend 1904 + cap 186C",
                          "top cap toward the outer face, U at the foot, leg into the floor TOP layer"),
        "R2-WV-IN": SHAPE("dxf 18DD on 18DC; section 189F + bends 1922 / 1924 + cap 1925",
                          "top cap toward the outer face, U at the foot, leg into the floor TOP layer"),
    }
    rows = [  # code, component, label, handle, face, direction, extra shape labels, candidate line
        ("R1-WV-OUT", "deep-end wall, vertical bars, outer face", "7%%C14/m", "1893", "outer face", "vertical",
         ["187C"], "POOL:R1:WALL_VERTICAL_OUTER_FACE"),
        ("R1-WV-IN", "deep-end wall, vertical bars, water face", "7%%C12/m", "1906", "water face", "vertical",
         ["18A8"], "POOL:R1:WALL_VERTICAL_INNER_FACE"),
        ("R1-WH-OUT", "deep-end wall, horizontal bars, outer face", "%%c12/20cm", "188D", "outer face", "horizontal",
         [], "POOL:R1:WALL_HORIZONTAL_HOOPS_OUTER_FACE"),
        ("R1-WH-IN", "deep-end wall, horizontal bars, water face", "%%c12/20cm", "18FC", "water face", "horizontal",
         [], "POOL:R1:WALL_HORIZONTAL_HOOPS_INNER_FACE"),
        ("R2-WV-IN", "shallow-end wall, vertical bars, water face", "6%%c12/m", "192F", "water face", "vertical",
         ["18DD"], "POOL:R2:WALL_VERTICAL_INNER_FACE"),
        ("R2-WH-IN", "shallow-end wall, horizontal bars, water face", "%%c10/20cm", "191F", "water face", "horizontal",
         [], "POOL:R2:WALL_HORIZONTAL_HOOPS_INNER_FACE"),
        ("R2-WH-OUT", "shallow-end wall, horizontal bars, outer face", "%%c10/20cm", "192E", "outer face", "horizontal",
         [], "POOL:R2:WALL_HORIZONTAL_HOOPS_OUTER_FACE"),
    ]
    for code, comp, lab, h, f, d, extra, line in rows:
        attrs = {"layer": face(h, f), "direction": face(h, d), "extent": wall_ext,
                 "end_shape": shapes.get(code, END_B)}
        rfi = {"extent": "RFI-B-S11"}
        kw = {}
        if code == "R1-WV-IN":
            attrs["diameter"] = CONFLICT(["dxf 1906 section label '7ø12/m' at the water-face bar 18A2",
                                          "dxf 18A8 '7ø14/m' on the exploded shape 185C (one polyline: water-face "
                                          "vertical + foot U + floor-top leg)"],
                                         "one bar cannot be both: d 12 (section) vs d 14 (shape row, the floor-top "
                                         "value 18B0); not resolved by choice")
            kw = {"gap": "G-T359-8"}
        out.append(pop(f"POOL-{code}", "POOL", "POOL-WALL", comp, lab, f"dxf {h} ({det})", attrs, rfi=rfi,
                       labels=[f"dxf {x}" for x in [h] + extra], candidate_lines=[line], **kw))
    # r2: the shallow-end OUTER vertical is printed by the exploded shape 1929 (6ø12/m on polyline 184C): its vertical
    # sits at the x of the section's outer-face bar 1928 (-59086 vs -59080 drawing units) and its return runs along the
    # floor BOTTOM layer, as the section's bend 1849 turns 1928 into the floor bottom bar 18E0: an L serving the outer
    # (soil) face, the mirror of the deep-end 187C. The water-face bar is the separate shape 18DD (cap + U + top leg).
    out.append(pop("POOL-R2-WV-OUT", "POOL", "POOL-WALL", "shallow-end wall, vertical bars, outer face", "6%%c12/m",
                   f"dxf 1929 ({det}, exploded bar-shape row) on polyline 184C; section bar 1928", {
                       "layer": P("dxf 1928 (outer-face bar) + 184C at the same x", "outer face"),
                       "direction": P("dxf 1929 / 184C", "vertical"), "extent": wall_ext,
                       "end_shape": SHAPE("dxf 1929 on 184C; section 1928 + bend 1849 into 18E0",
                                          "L-bar: outer-face vertical, foot bent into the floor BOTTOM layer")},
                   rfi={"extent": "RFI-B-S11"}, labels=["dxf 1929"],
                   candidate_lines=["POOL:R2:WALL_VERTICAL_OUTER_FACE"],
                   note="r1 NOT_DRAWN reversed: printed by the shape row (1929); T-166 read it as one U over the top "
                        "serving both faces, the shape row draws two bars (1929 outer L, 18DD water-face U)"))
    for code, comp, lab, h, line, el in (
            ("RIM", "rim bars at the deep-end wall top (3 dots 1899 / 189B / 1903 under the cap)", "3%%c16", "1896",
             "POOL:R1:RIM_BARS_AT_THE_WALL_TOP", "POOL-WALL"),
            ("CORNER", "corner bars at the deep-end wall / floor junction", "3%%c16", "1881",
             "POOL:R1:CORNER_BARS_FLOOR_WALL", "POOL-WALL"),
            ("R2-CORNER", "corner bars at the shallow-end wall / floor junction (dots 18F1 / 18F2 / 18F3)", "4%%c16",
             "192B", "POOL:R2:CORNER_BARS_FLOOR_WALL", "POOL-WALL")):
        out.append(pop(f"POOL-{code}", "POOL", el, comp, lab,
                       f"dxf {h} ({det})", {"layer": NA("bundle at a corner"), "direction": face(h, "along the wall"),
                                            "extent": N("printed on the two-zone section only; which zone's bars run "
                                                        "round the built flat pool (Q-26 A) is not printed"),
                                            "end_shape": END_B},
                       rfi={"extent": "RFI-B-S11"}, labels=[f"dxf {h}"], candidate_lines=[line],
                       note="r1 called 192B 'bars at the floor step'; its leader reaches the dots at the shallow-end "
                            "wall foot" if code == "R2-CORNER" else ""))
    out.append(pop("POOL-R2-RIM", "POOL", "POOL-WALL", "rim bars at the shallow-end wall top (2 dots 1842 / 1923 "
                   "under the cap 1925)", None, f"dxf 1842 / 1923 ({det}): drawn, no label", {
                       "layer": NA("bundle under the cap"), "direction": P("dxf 1842 / 1923", "along the wall (dots)"),
                       "extent": wall_ext, "end_shape": END_B},
                   rfi={"mark": "RFI-B-S11", "diameter": "RFI-B-S11", "spacing_or_count": "RFI-B-S11",
                        "extent": "RFI-B-S11"},
                   candidate_lines=["POOL:R2:RIM_BARS_AT_THE_WALL_TOP"],
                   note="two bars drawn, no notation: diameter and count not printed (2 dots drawn is a drawing, not a "
                        "printed count)"))
    floor = [
        ("F-MAIN-T", "deep floor, main bars, top", "7%%c14/m", ["18B0", "1860"],
         SHAPE("dxf 1860 on 1867 + 1862 + hook 18AB; section 1872 + 189E",
               "horizontal in the deep floor top, crank up into the slope, end hook"),
         ["POOL:R1:FLOOR_TOP_SECTION_LINE_BARS"]),
        ("F-MAIN-B", "deep floor, main bars, bottom", "7%%c14/m", ["18AA", "19B0", "1869"],
         SHAPE("dxf 1869 on 1866 + 1861; section 19A9 + 19A7",
               "horizontal in the deep floor bottom, crank up along the slope"),
         ["POOL:R1:FLOOR_BOTTOM_SECTION_LINE_BARS"]),
        ("F-DIST", "deep floor, distribution bars (dot rows, both mats)", "6%%c14/m", ["18AD"], END_B,
         ["POOL:R1:FLOOR_TOP_DOT_ROW_BARS", "POOL:R1:FLOOR_BOTTOM_DOT_ROW_BARS"]),
        ("F-SLOPE", "sloped floor bars (both mats)", "6%%c12/m", ["1907", "18D3", "18DB"],
         SHAPE("dxf 18DB on 185E + 18DA (and the unlabelled 1868 + 1865 + 1863)",
               "slope, then horizontal into the shallow floor"),
         ["POOL:R2:FLOOR_TOP_SECTION_LINE_BARS", "POOL:R2:FLOOR_BOTTOM_SECTION_LINE_BARS"]),
        ("F-SHALLOW", "shallow floor bars", "6%%c12/m", ["18F0", "18F8", "18D7"],
         SHAPE("dxf 18D7 on hook 186B + 185F + 18D9 (and the unlabelled 185D + 18D8 + 18DE)",
               "hook, slope, then horizontal along the shallow floor"),
         ["POOL:R2:FLOOR_TOP_DOT_ROW_BARS", "POOL:R2:FLOOR_BOTTOM_DOT_ROW_BARS"]),
    ]
    for code, comp, lab, hs, shape, lines in floor:
        out.append(pop(f"POOL-{code}", "POOL", "POOL-FLOOR", comp, lab, f"dxf {' / '.join(hs)} ({det})", {
            "layer": P(f"dxf {hs[0]}", "by position on the section"), "direction": P(f"dxf {hs[0]}"),
            "extent": N("the detail draws a deep zone, a slope and a shallow zone; the built floor is flat at 1.15 m "
                        "(owner Q-26 A): which population the flat floor takes is not printed"),
            "end_shape": shape}, rfi={"extent": "RFI-B-S11"}, labels=[f"dxf {h}" for h in hs],
            candidate_lines=lines,
            note="the shape row shows the slope and shallow 6ø12/m as one cranked bar per mat; which shape is which "
                 "mat is not printed" if code in ("F-SLOPE", "F-SHALLOW") else ""))
    return out


DOME_LABELS = [("1A0E", "%%C12MM/15cm"), ("1A15", "%%C12MM/15cm"), ("1A47", "3%%c16"), ("1A68", "3%%c16"),
               ("1A29", "8%%c8/m"), ("1A58", "8%%c8/m"), ("1A37", "2%%c14/20cm"), ("1A66", "2%%c14/20cm"),
               ("1A4B", "3%%c18"), ("1A6C", "3%%c18"), ("1A18", "%%uDETAIL OF DOME"), ("1A19", "(N.I.S)")]


def domes():
    out = []
    det = "p.7 DETAIL OF DOME (N.I.S.)"
    for dome in ("DOME-A", "DOME-B"):
        for code, h in (("SHELL-MER", "1A0E"), ("SHELL-HOOP", "1A15")):
            out.append(pop(f"{dome}-{code}", "TERRACE DOMES", dome,
                           "shell bars, meridians" if code == "SHELL-MER" else "shell bars, hoops", "%%C12MM/15cm",
                           f"dxf {h} ({det})", {
                               "layer": N("r2 correction: no bar line is drawn in the shell (only the concrete arcs "
                                          "182B / 182E, layer S-EXTL.D); the leaders 1A0E / 1A15 end inside the 10 cm "
                                          "shell: one mat or two, and its position, not printed"),
                               "direction": N("the two labels are identical and neither says meridian or hoop"),
                               "extent": N("shell 10 cm (19B1), span 442 (1A38), rise 190 (1A6D) printed; curtailment "
                                           "of the meridians near the crown and the bar position in the 10 cm shell "
                                           "(cover) not printed"),
                               "end_shape": N("no shell bar drawn: anchorage into the ring and hoop laps not printed")},
                           rfi={}, gap="G-T359-3", labels=["dxf 1A0E", "dxf 1A15"],
                           no_line_reason="no candidate line: the dome shells are not in the V3.0.16 rebar lines"))
    for code, comp, lab, hs in (("RING-T", "edge ring top bars", "3%%c16", ("1A47", "1A68")),
                                ("RING-B", "edge ring bottom bars", "3%%c18", ("1A4B", "1A6C")),
                                ("RING-S", "edge ring side bars", "2%%c14/20cm", ("1A37", "1A66")),
                                ("RING-L", "edge ring links", "8%%c8/m", ("1A29", "1A58"))):
        h = " / ".join(hs)
        labs = [f"dxf {x}" for x in hs]   # the section cuts the ring twice (both edges of one dome)
        out.append(pop(f"DOME-A-{code}", "TERRACE DOMES", "DOME-A-RING", comp, lab, f"dxf {h} ({det})",
                       owned_by="beam ledger T-149 BM-1F-028 (B4, RELEASED with the schedule bars 4ø16 / 2ø12 / "
                                "6ø8/m); the detail's ring bars CONFLICT with it (CF-S8.3-04): never added",
                       labels=labs, note="same physical ring as BM-1F-028"))
        out.append(pop(f"DOME-B-{code}", "TERRACE DOMES", "DOME-B-RING", comp, lab, f"dxf {h} ({det})", {
            "layer": NA("bundle / face position drawn") if code != "RING-L" else NA("closed link"),
            "direction": P(f"dxf {h}"),
            "extent": N("ring section not printed for the east ring (no mark, SEE DETAIL); depth AS PER ARCH (182F)"),
            "end_shape": (SHAPE("dxf links 1A0B / 1A08 (closed rectangles)", "closed link, no hook length")
                          if code == "RING-L" else N("closure / laps of the ring bars not printed"))},
            rfi={"extent": "RFI-S17", "end_shape": "RFI-S17"}, gap="G-T359-3", labels=labs,
            no_line_reason="no candidate line: the east dome ring is not in the V3.0.16 rebar lines"))
    out.append(pop("DOME-T-ALL", "TOWER DOME", "DOME-TOWER", "every bar", None,
                   "ST p.6: flat +13.90 slab panel, no opening / ring; p.7 one generic detail", not_drawn=True,
                   rfi={"all": "RFI-S28"}, no_line_reason="no candidate line: tower dome not drawn"))
    return out


LIFT = "pdf p.14 DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT)"
LIFT_LABELS = [("L-WH", "6%%c12/m", "left wall, leader to the dot row"),
               ("L-WV", "6%%c16/m", "left wall, leader to the vertical bar lines"),
               ("L-BT", "2%%c16", "left wall foot, raft top"), ("L-BB", "2%%c16", "left wall foot, raft bottom"),
               ("RAFT", "AS PER SCH.", "raft bars (three leaders)"), ("R-TOP", "2%%c12", "right wall top"),
               ("R-WH", "6%%c12/m", "right wall, dot row"), ("R-WV", "6%%c16/m", "right wall, vertical lines")]
BW = "pdf p.14 TYPICAL BOUNDARY WALL"
BW_LABELS = [("COL", "COLUMN 4%%c14", "section A-A column 20 x 30"), ("PLAN-COL", "(20x30) R.C COLUMNS 4%%c14", "plan"),
             ("UP-A", "2%%c14 (T&B)", "upper G.B"), ("UP-L", "%%c8/20 STIRRUPS", "upper G.B"),
             ("UP-B", "3%%c16 (T&B)", "upper G.B"), ("LO-A", "2%%c14 (T&B)", "lower G.B"),
             ("LO-L", "%%c8/20 STIRRUPS", "lower G.B"), ("LO-B", "3%%c16 (T&B)", "lower G.B"),
             ("PAD-A", "7%%c12", "pad, bar line across the 80 with up-turned ends"),
             ("PAD-B", "4%%c12 (B.W)", "pad, leader to the four dots")]


def tank_lift_boundary():
    out = []
    out.append(pop("TANK-SLAB", "ROOF WATER TANK", "2F-011", "roof slab under the tank (T 18, T&B)", "7%%C14/m",
                   "dxf 7A7 / 7A8 / 7AF / 7B0 (p.6, 'WATER TANK PLACE' 1A85)",
                   owned_by="slab ledger T-152 panel 2F-011 (HELD 143.382 .. 149.310 kg; RFI-B-S10)"))
    out.append(pop("TANK-STRUCT", "ROOF WATER TANK", "TANK", "tank walls, base and cover", None,
                   "ST p.6 cloud 'WATER TANK PLACE' only; no tank section in either discipline (T-204)",
                   not_drawn=True, rfi={}, gap="G-T359-4", candidate_lines=["TANK:2F:ALL_FAMILIES"]))
    det = LIFT + ", typical"
    for code, comp, lab, labs, d in (
            ("WV", "pit wall vertical bars, both faces", "6%%c16/m", ("L-WV", "R-WV"), "vertical"),
            ("WH", "pit wall horizontal bars, both faces", "6%%c12/m", ("L-WH", "R-WH"), "horizontal"),
            ("TOP", "bars at the wall top", "2%%c12", ("R-TOP",), "along the wall"),
            ("BASE", "bars at the wall foot in the raft (2ø16 at the raft top and 2ø16 at the raft bottom)", "2 %%c16",
             ("L-BT", "L-BB"), "along the wall")):
        pos = " / ".join(labs)
        a = {"layer": P(f"{det}, {pos}", "two faces drawn") if code in ("WV", "WH") else NA("bundle"),
             "direction": P(f"{det}, {pos}", d),
             "extent": N("pit depth 'As per Lift Manufactures recommendations'; vertical embedment in the raft drawn, "
                         "not dimensioned"),
             "end_shape": (SHAPE(f"{det}: vertical lines", "closed over the wall top, both faces run down to the "
                                 "raft bottom bars") if code == "WV" else N("laps / corner anchorage not printed"))}
        out.append(pop(f"LIFT-{code}", "LIFT PIT", "LIFT-PIT-WALL", comp, lab, f"{det}, {pos}", a,
                       rfi={"extent": "L-1"}, gap="" if code == "WV" else "G-T359-5",
                       labels=[f"{LIFT}: {x}" for x in labs],
                       no_line_reason="no candidate line: the lift pit walls are not in the V3.0.16 rebar lines"))
    out.append(pop("LIFT-RAFT", "LIFT PIT", "FF", "lift raft bars ('AS PER SCH.')", "",
                   f"{det}: 'AS PER SCH.' -> p.9 footing schedule FF", labels=[f"{LIFT}: RAFT"],
                   owned_by="footing ledger T-136 FF (HELD, owner 2026-10-25 13:16)"))
    bw = BW + " section A-A (N.I.S.)"
    out.append(pop("BW-COL", "BOUNDARY WALL", "BW-COLUMN", "column 20 x 30 main bars", "4%%c14",
                   f"{bw}, label 'COLUMN 4ø14'; plan '(20x30) R.C COLUMNS 4ø14'", {
                       "layer": NA("corner bars"), "direction": P(bw, "vertical"),
                       "extent": N("column height and positions not printed (spacing 'SEE ARCH PLAN')"),
                       "end_shape": N("starter / anchorage into the ground beam not printed")},
                   rfi={"extent": "RFI-S04"}, gap="G-T359-6", labels=[f"{BW}: COL", f"{BW}: PLAN-COL"],
                   no_line_reason="no candidate line: boundary wall not in the V3.0.16 rebar lines"))
    out.append(pop("BW-COL-LINK", "BOUNDARY WALL", "BW-COLUMN", "column links", None,
                   f"{bw}: ties drawn in the column, no label", not_drawn=True, rfi={}, gap="G-T359-6",
                   no_line_reason="no candidate line: boundary wall not in the V3.0.16 rebar lines"))
    for lvl, lev in (("UP", "upper G.B 20 x 40 at N.G. LEVEL"), ("LO", "lower G.B at excavation depth")):
        for code, comp, lab in (("A", "bars labelled 2ø14 (T&B)", "2%%c14 (T&B)"),
                                ("B", "bars labelled 3ø16 (T&B)", "3%%c16 (T&B)"),
                                ("L", "stirrups", "%%c8/20 STIRRUPS")):
            out.append(pop(f"BW-GB{lvl}-{code}", "BOUNDARY WALL", f"BW-GB-{lvl}", f"{lev}: {comp}", lab, f"{bw}", {
                "layer": N("'(T&B)' on both labels while the section draws 2 bars top and 3 bottom") if code != "L"
                else NA("closed stirrup"),
                "direction": P(bw, "along the wall"),
                "extent": N("wall length and the lower beam level ('AS PER EXCAVATION DEPTH BELOW N.G. LEVEL') not "
                            "printed; section 20 x 40 vs schedule B.W 20 x 60"),
                "end_shape": N("laps / ends at columns not printed")},
                rfi={"extent": "RFI-S03"}, gap="G-T359-7", labels=[f"{BW}: {lvl}-{code}"],
                no_line_reason="no candidate line: boundary wall not in the V3.0.16 rebar lines"))
    for code, comp, lab in (("A", "pad bars labelled 7ø12", "7%%c12"), ("B", "pad bars labelled 4ø12 (B.W)", "4%%c12 (B.W)")):
        out.append(pop(f"BW-PAD-{code}", "BOUNDARY WALL", "BW-PAD", f"pad 130 x 80 x 30: {comp}", lab, bw, {
            "layer": P(bw, "bottom"),
            "direction": N("four dots drawn (bars along the 1.30 m pad), but '(B.W)' is defined nowhere on the sheet "
                           "(both ways would add a second direction)") if code == "B"
            else P(bw, "across the 80 width, up-turned ends drawn"),
            "extent": N("pad positions 'SEE ARCH PLAN', none marked"),
            "end_shape": SHAPE(bw, "U with both ends turned up to the pad top") if code == "A" else END_B},
            rfi={"extent": "RFI-S04"}, gap="G-T359-7" if code == "B" else "", labels=[f"{BW}: PAD-{code}"],
            no_line_reason="no candidate line: boundary wall not in the V3.0.16 rebar lines"))
    return out


ELEMENTS = ["STAIR ST-01", "STAIR ST-02", "STAIR E1", "STAIR D1", "POOL", "TERRACE DOMES", "TOWER DOME",
            "ROOF WATER TANK", "LIFT PIT", "BOUNDARY WALL"]

RELEASED = [  # released STR.REBAR lines that touch these elements (T-149 / T-152 / T-136 ledgers, candidate V3.0.x)
    {"line_id": "BM-1F-028 bottom 4ø16", "element_id": "DOME-A-RING", "component": "beam B4 bottom bars"},
    {"line_id": "BM-1F-028 top 2ø12", "element_id": "DOME-A-RING", "component": "beam B4 top bars"},
]

PLAN_LABELS = [("dxf 490", "8%%C16/m"), ("dxf 491", "8%%C16/m"), ("dxf 48F", "8%%C16/m"), ("dxf 748", "8%%C16/m"),
               ("dxf 749", "8%%C16/m"), ("dxf 747", "8%%C16/m"), ("dxf 53D", "8%%C16/m"), ("dxf 5BC", "8%%C16/m"),
               ("dxf 533", "6%%C14/m"), ("pdf p.4 ST-02 horizontal 8ø16/m east of column CA", "8%%C16/m")]


def details():
    """Every label inside each cited detail (full extent, incl. exploded bar-shape rows). The plan-callout entry lists
    the stair-panel callouts cited from p.4 / p.5 (not a full plan sweep)."""
    return [
        {"detail": POOL_DET, "source": "ST7757 dxf, TEXT sweep of the detail extent",
         "labels": [{"ref": f"dxf {h}", "text": t} for h, t in POOL_LABELS]},
        {"detail": "dxf p.7 DETAIL OF DOME (title 1A18)", "source": "ST7757 dxf, TEXT sweep of the detail extent",
         "labels": [{"ref": f"dxf {h}", "text": t} for h, t in DOME_LABELS]},
        {"detail": P16, "source": "ST7757.pdf p.16 at 170 / 200 dpi (no text layer)",
         "labels": [{"ref": p16(c), "text": t, "position": pos} for c, t, pos in P16_LABELS]},
        {"detail": SB, "source": "ST7757.pdf p.16 at 170 dpi",
         "labels": [{"ref": f"{SB}: {c}", "text": t, "position": pos} for c, t, pos in SB_LABELS]},
        {"detail": LIFT, "source": "ST7757.pdf p.14 at 250 dpi",
         "labels": [{"ref": f"{LIFT}: {c}", "text": t, "position": pos} for c, t, pos in LIFT_LABELS]},
        {"detail": BW, "source": "ST7757.pdf p.14 at 250 dpi",
         "labels": [{"ref": f"{BW}: {c}", "text": t, "position": pos} for c, t, pos in BW_LABELS]},
        {"detail": "stair-panel callouts on the slab plans p.4 / p.5 (cited, not a full plan sweep)",
         "source": "ST7757 dxf + pdf p.4", "labels": [{"ref": r, "text": t} for r, t in PLAN_LABELS]},
    ]


def rfi_register(folder: Path) -> list[str]:
    ids = set()
    for f in ("A_PRIORITY_RFI.md", "B_REMAINING_RFI.md"):
        for line in (folder / f).read_text(encoding="utf-8").splitlines():
            m = re.match(r"### (RFI-[A-Z0-9-]+)", line)
            if m:
                ids.add(m.group(1))
            m = re.match(r"- ([LC]-\d+):", line)
            if m:
                ids.add(m.group(1))
    return sorted(ids)


def build(folder: Path) -> dict:
    pops = stairs() + pool() + domes() + tank_lift_boundary()
    for p in pops:   # an 'all' RFI on a not-drawn element is kept as its after-list
        p.setdefault("rfi", {})
    return {"schema": "T359_BAR_DETAIL_INPUT_V2", "villa": "development villa (Drive folder 'Alsenan chalet project')",
            "rfi_register": rfi_register(folder), "answered_rules": [OPT_B, "Q-71", "Q-26 A", "Q-47 A"],
            "elements_required": ELEMENTS, "released_lines": RELEASED, "populations": pops,
            "details": details(), "unlabelled_shapes": POOL_UNLABELLED_SHAPES,
            "candidate": "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json (ARCH_TAKEOFF_V3.0.16)",
            "candidate_prefix": CAND, "candidate_scope": ["POOL:", "ST-0", "TANK:"]}


if __name__ == "__main__":
    json.dump(build(Path(sys.argv[1])), open(sys.argv[2], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
