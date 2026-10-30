"""Builds ALSENAN_BAR_DETAIL_INPUT.json for the T-359 census (development villa; printed readings only).

Sources (Drive 'Alsenan chalet project', private copies in the git-excluded folder, never committed; re-read this run):
  'ST7757 dxf.dxf' (sha256 9f9d1179..): text entities by handle (layers S-TEXT.D, S-TEXT-SLAB).
  'ST7757.pdf' (sha256 74da1523.., 16 pages, no text layer): rendered at 60 / 170 / 200 / 250 / 300 dpi and read by
  eye; p.4 / p.5 / p.6 slab plans, p.7 DETAIL OF SWIMMING POOL + DETAIL OF DOME, p.13 ground-beam sections,
  p.14 DETAIL OF LIFT WITH ISOLATED FOOTING + TYPICAL BOUNDARY WALL (plan, section A-A), p.15, p.16 TYPICAL STEEL
  LAYOUT - STAIR SECTION + TYPICAL DETAIL OF STAIR BEAM.
PDF-only labels carry 'pdf p.N <detail>, <position>' instead of a handle (the detail sheets 13-16 are not in the DXF).

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
        eid = "ST-01-" + ("GF" if sheet == "p.4" else "1F")
        out.append(pop(f"{eid}-MAIN", "STAIR ST-01", eid, "main bottom bars along the flights", "8%%C16/m",
                       f"dxf {hs[0]} / {hs[1]} ({sheet} plan, vertical labels on the two flights)", {
                           "layer": T(typ, "bottom layer only on the typical; the plan label gives no layer"),
                           "direction": P(f"dxf {hs[0]} / {hs[1]}", "label and bar line along the flight"),
                           "extent": P(f"dxf {hs[0]} / {hs[1]} + verified flight concrete (T-184 / T-290)",
                                       "bar line over the straight flights; the winder turn is its own row"),
                           "end_shape": END_B},
                       rfi={}, gap="G-T359-1",
                       note="T 16 waist on the plan (T-184, Q-47 A); layer from the typical only"))
        out.append(pop(f"{eid}-LAND", "STAIR ST-01", eid, "landing strip bottom bars across the shaft", "8%%C16/m",
                       f"dxf {hs[2]} ({sheet} plan, horizontal label over the landing)", {
                           "layer": T(typ, "landing bottom 8ø16/m on the typical"),
                           "direction": P(f"dxf {hs[2]}", "across the shaft"),
                           "extent": P(f"dxf {hs[2]}", "bar line wall to wall of the 2.50 m shaft"),
                           "end_shape": END_B},
                       rfi={}, gap="G-T359-1"))
    # the components that only the typical section prints (no Alsenan plan or section names them)
    tcomp = [
        ("TOPH", "top bars at the head of each flight", "6%%c14/m", "pdf p.16 upper and lower sections, label at the +4.00 head and at the +2.00 landing"),
        ("TOPF", "top bars at a foot on a landing", "6%%c14/m", "pdf p.16 upper section, label at the S.S.L +2.00 landing"),
        ("TOPG", "top bars at a foot on a ground beam (G.B)", "6%%c16/m", "pdf p.16 lower section, label above the 3ø14 G.B and the exploded bar with the leg into the G.B"),
        ("DIST", "distribution bars under the main bars", "%%c12/20cm", "pdf p.16 both sections and the exploded views"),
        ("STEP", "step bars (tread + riser shape)", "%%c8/15", "pdf p.16 both sections, one per step"),
        ("NOSE", "nosing bar, one per tread", "1%%c12", "pdf p.16 both sections"),
        ("LTOP", "landing top bars", "6%%c12/m", "pdf p.16 landing S.S.L +2.00"),
    ]
    for el, eid, rfi_id in (("STAIR ST-01", "ST-01", "RFI-S24"), ("STAIR ST-02", "ST-02", "RFI-S27")):
        for code, comp, lab, src in tcomp:
            a = {"layer": P(src), "direction": P(src),
                 "extent": N("bar lengths drawn, not dimensioned (N.T.S.)"),
                 "end_shape": N("bends / legs drawn, not dimensioned")}
            if code in ("NOSE",):
                a["spacing_or_count"] = NA("one bar per tread")
            out.append(pop(f"{eid}-T-{code}", el, eid, comp, lab, src, a, typical_only=True,
                           rfi={}, gap="G-T359-1",
                           note="typical arrangement; no Alsenan print ties it to this stair (family master B7-14: "
                                "'typical-only stair families, p.16 reading not ruled')"))
    # ST-02 round stair: straight part and curved part (p.4)
    out.append(pop("ST-02-MAIN-S", "STAIR ST-02", "ST-02", "main bottom bars along the straight flight", "8%%C16/m",
                   "dxf 53D (p.4 plan, vertical label on the straight flight)", {
                       "layer": T("pdf p.16 typical", "bottom on the typical only"),
                       "direction": P("dxf 53D"), "extent": N("waist profile of the straight part from levels not printed"),
                       "end_shape": END_B},
                   rfi={"extent": "RFI-A03"}, gap="G-T359-1", note="riser count / landing levels asked in RFI-A03"))
    out.append(pop("ST-02-MAIN-H", "STAIR ST-02", "ST-02", "bars along the straight landing run", "8%%C16/m",
                   "pdf p.4 plan, horizontal label east of column CA (no modelspace text entity found for it)", {
                       "layer": T("pdf p.16 typical"), "direction": P("pdf p.4"),
                       "extent": P("pdf p.4", "bar line drawn from the curve to beam B21"), "end_shape": END_B},
                   rfi={}, gap="G-T359-1"))
    out.append(pop("ST-02-MAIN-C", "STAIR ST-02", "ST-02", "main bars along the curved part RS-C", "8%%C16/m",
                   "dxf 5BC (p.4 plan, label on the arc bar line)", {
                       "layer": T("pdf p.16 typical"), "direction": P("dxf 5BC", "along the arc"),
                       "extent": N("soffit form and thickness of the curved part not printed"),
                       "end_shape": END_B},
                   rfi={"extent": "RFI-S27"}, gap="G-T359-1"))
    # elements owned by other ledgers, listed so that they are never counted twice
    out.append(pop("ST-02-GF126", "STAIR ST-02", "GF-126", "slab bars beside the round stair", "6%%C14/m",
                   "dxf 533 (p.4)", owned_by="slab ledger T-152 panel GF-126 (HELD, RFI-B-S10)"))
    for bid in ("BM-GF-015", "BM-1F-001", "BM-GF-057"):
        out.append(pop(f"{bid}-STAIRBEAM", "STAIR ST-01" if bid != "BM-GF-057" else "STAIR ST-02", bid,
                       "stair beam B3 '(With Stair)' (p.16 TYPICAL DETAIL OF STAIR BEAM, cranked)", "",
                       "dxf 6B8 / 6B6 / 1826 '(With Stair)'",
                       owned_by=f"beam ledger T-149 {bid} (HELD; crank RFI-B-S22)"))
    # entrance flight E1 and stair-hall flight D1: no bar printed anywhere
    out.append(pop("E1-ALL", "STAIR E1", "E1", "every bar", None, "dxf riser lines 18A .. 179 (p.3); no bar text "
                   "within 3 m", not_drawn=True, rfi={"all": "RFI-S26"}))
    out.append(pop("D1-ALL", "STAIR D1", "D1", "every bar", None, "dxf riser lines 1C4 .. 1C7 (p.3); no bar text "
                   "within 3 m", not_drawn=True, rfi={"all": "RFI-S26"}))
    out.append(pop("ST-01-WINDER", "STAIR ST-01", "MS1-T", "winder turn bars", None,
                   "p.4 wedge lines; p.16 typical shows no winder", not_drawn=True, rfi={"all": "RFI-S24"}))
    return out


def pool():
    out = []
    det = "p.7 DETAIL OF SWIMMING POOL (N.I.S.)"
    face = lambda h, n: P(f"dxf {h}", n)
    wall_ext = N("the detail draws a deep-end (R1) and a shallow-end (R2) wall with different bars; which "
                 "population each wall of the flat 1.15 m pool (owner Q-26 A) takes is not printed; wall 1.20 m to the "
                 "structure line is verified concrete (T-183 r2)")
    rows = [
        ("R1-WV-OUT", "deep-end wall, vertical bars, outer face", "7%%C14/m", "1893", "outer face", "vertical"),
        ("R1-WV-IN", "deep-end wall, vertical bars, water face", "7%%C12/m", "1906", "water face", "vertical"),
        ("R1-WH-OUT", "deep-end wall, horizontal bars, outer face", "%%c12/20cm", "188D", "outer face", "horizontal"),
        ("R1-WH-IN", "deep-end wall, horizontal bars, water face", "%%c12/20cm", "18FC", "water face", "horizontal"),
        ("R2-WV-IN", "shallow-end wall, vertical bars, water face", "6%%c12/m", "192F", "water face", "vertical"),
        ("R2-WH-IN", "shallow-end wall, horizontal bars, water face", "%%c10/20cm", "191F", "water face", "horizontal"),
        ("R2-WH-OUT", "shallow-end wall, horizontal bars, outer face", "%%c10/20cm", "192E", "outer face", "horizontal"),
    ]
    for code, comp, lab, h, f, d in rows:
        out.append(pop(f"POOL-{code}", "POOL", "POOL-WALL", comp, lab, f"dxf {h} ({det})",
                       {"layer": face(h, f), "direction": face(h, d), "extent": wall_ext, "end_shape": END_B},
                       rfi={"extent": "RFI-B-S11"},
                       note="R2 outer vertical: no separate label (the 6ø12/m 192F leader reaches the water face only)"
                       if code == "R2-WV-IN" else ""))
    out.append(pop("POOL-R2-WV-OUT", "POOL", "POOL-WALL", "shallow-end wall, vertical bars, outer face", None,
                   f"{det}: bars drawn on the outer face, no label of their own", not_drawn=True,
                   rfi={"all": "RFI-B-S11"}))
    for code, comp, lab, h in (("RIM", "rim bars at the wall top", "3%%c16", "1896"),
                               ("CORNER", "corner bars at the base / wall junction", "3%%c16", "1881"),
                               ("STEP", "bars at the floor step", "4%%c16", "192B")):
        out.append(pop(f"POOL-{code}", "POOL", "POOL-WALL" if code != "STEP" else "POOL-FLOOR", comp, lab,
                       f"dxf {h} ({det})", {"layer": NA("bundle at a corner"), "direction": face(h, "along the wall"),
                                            "extent": N("printed at the deep-end (R1) section only; the flat floor has no step (Q-26 A): "
                                   "which applies round the built pool is not printed"),
                                            "end_shape": END_B},
                       rfi={"extent": "RFI-B-S11"}))
    floor = [
        ("F-MAIN-T", "deep floor, main bars, top", "7%%c14/m", "18B0"),
        ("F-MAIN-B", "deep floor, main bars, bottom", "7%%c14/m", "18AA / 19B0"),
        ("F-DIST", "deep floor, distribution bars", "6%%c14/m", "18AD"),
        ("F-SLOPE", "sloped floor bars (both mats)", "6%%c12/m", "1907 / 18D3"),
        ("F-SHALLOW", "shallow floor bars", "6%%c12/m", "18F0 / 18F8"),
    ]
    for code, comp, lab, h in floor:
        out.append(pop(f"POOL-{code}", "POOL", "POOL-FLOOR", comp, lab, f"dxf {h} ({det})", {
            "layer": P(f"dxf {h}", "by position on the section"), "direction": P(f"dxf {h}"),
            "extent": N("the detail draws a deep zone, a slope and a shallow zone; the built floor is flat at 1.15 m "
                        "(owner Q-26 A): which population the flat floor takes is not printed"),
            "end_shape": END_B}, rfi={"extent": "RFI-B-S11"}))
    return out


def domes():
    out = []
    det = "p.7 DETAIL OF DOME (N.I.S.)"
    for dome in ("DOME-A", "DOME-B"):
        for code, h in (("SHELL-MER", "1A0E"), ("SHELL-HOOP", "1A15")):
            out.append(pop(f"{dome}-{code}", "TERRACE DOMES", dome,
                           "shell bars, meridians" if code == "SHELL-MER" else "shell bars, hoops", "%%C12MM/15cm",
                           f"dxf {h} ({det})", {
                               "layer": P("dxf shell bar line between arcs 182B / 182E", "one mat drawn"),
                               "direction": P(f"dxf {h}"),
                               "extent": N("shell 10 cm (19B1), span 442 (1A38), rise 190 (1A6D) printed; curtailment "
                                           "of the meridians near the crown and the bar position in the 10 cm shell "
                                           "(cover) not printed"),
                               "end_shape": N("anchorage of the shell bars into the ring and hoop laps not printed")},
                           rfi={}, gap="G-T359-3"))
    for code, comp, lab, h in (("RING-T", "edge ring top bars", "3%%c16", "1A47 / 1A68"),
                               ("RING-B", "edge ring bottom bars", "3%%c18", "1A4B / 1A6C"),
                               ("RING-S", "edge ring side bars", "2%%c14/20cm", "1A37 / 1A66"),
                               ("RING-L", "edge ring links", "8%%c8/m", "1A29 / 1A58")):
        out.append(pop(f"DOME-A-{code}", "TERRACE DOMES", "DOME-A-RING", comp, lab, f"dxf {h} ({det})",
                       owned_by="beam ledger T-149 BM-1F-028 (B4, RELEASED with the schedule bars 4ø16 / 2ø12 / "
                                "6ø8/m); the detail's ring bars CONFLICT with it (CF-S8.3-04): never added",
                       note="same physical ring as BM-1F-028"))
        out.append(pop(f"DOME-B-{code}", "TERRACE DOMES", "DOME-B-RING", comp, lab, f"dxf {h} ({det})", {
            "layer": NA("bundle / face position drawn") if code != "RING-L" else NA("closed link"),
            "direction": P(f"dxf {h}"),
            "extent": N("ring section not printed for the east ring (no mark, SEE DETAIL); depth AS PER ARCH (182F)"),
            "end_shape": N("closure of the ring bars not printed")},
            rfi={"extent": "RFI-S17", "end_shape": "RFI-S17"}, gap="G-T359-3",
            same_physical_bars_as=[["DOME-A-RING", "beam B4 bottom bars"]] if code == "RING-X" else []))
    out.append(pop("DOME-T-ALL", "TOWER DOME", "DOME-TOWER", "every bar", None,
                   "ST p.6: flat +13.90 slab panel, no opening / ring; p.7 one generic detail", not_drawn=True,
                   rfi={"all": "RFI-S28"}))
    return out


def tank_lift_boundary():
    out = []
    out.append(pop("TANK-SLAB", "ROOF WATER TANK", "2F-011", "roof slab under the tank (T 18, T&B)", "7%%C14/m",
                   "dxf 7A7 / 7A8 / 7AF / 7B0 (p.6, 'WATER TANK PLACE' 1A85)",
                   owned_by="slab ledger T-152 panel 2F-011 (HELD 143.382 .. 149.310 kg; RFI-B-S10)"))
    out.append(pop("TANK-STRUCT", "ROOF WATER TANK", "TANK", "tank walls, base and cover", None,
                   "ST p.6 cloud 'WATER TANK PLACE' only; no tank section in either discipline (T-204)",
                   not_drawn=True, rfi={}, gap="G-T359-4"))
    det = "pdf p.14 DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT), typical"
    for code, comp, lab, pos, d in (
            ("WV", "pit wall vertical bars, both faces", "6%%c16/m", "labels left and right wall", "vertical"),
            ("WH", "pit wall horizontal bars, both faces", "6%%c12/m", "labels left and right wall", "horizontal"),
            ("TOP", "bars at the wall top", "2%%c12", "label right wall top", "along the wall"),
            ("BASE", "bars at the wall foot in the raft", "2 %%c16", "two labels left wall foot", "along the wall")):
        a = {"layer": P(f"{det}, {pos}", "two faces drawn") if code in ("WV", "WH") else NA("bundle"),
             "direction": P(f"{det}, {pos}", d),
             "extent": N("pit depth 'As per Lift Manufactures recommendations'; vertical embedment in the raft drawn, "
                         "not dimensioned"),
             "end_shape": N("laps / corner anchorage not printed")}
        out.append(pop(f"LIFT-{code}", "LIFT PIT", "LIFT-PIT-WALL", comp, lab, f"{det}, {pos}", a,
                       rfi={"extent": "L-1"}, gap="G-T359-5"))
    out.append(pop("LIFT-RAFT", "LIFT PIT", "FF", "lift raft bars ('AS PER SCH.')", "",
                   f"{det}: 'AS PER SCH.' -> p.9 footing schedule FF",
                   owned_by="footing ledger T-136 FF (HELD, owner 2026-10-25 13:16)"))
    bw = "pdf p.14 TYPICAL BOUNDARY WALL section A-A (N.I.S.)"
    out.append(pop("BW-COL", "BOUNDARY WALL", "BW-COLUMN", "column 20 x 30 main bars", "4%%c14",
                   f"{bw}, label 'COLUMN 4ø14'; plan '(20x30) R.C COLUMNS 4ø14'", {
                       "layer": NA("corner bars"), "direction": P(bw, "vertical"),
                       "extent": N("column height and positions not printed (spacing 'SEE ARCH PLAN')"),
                       "end_shape": N("starter / anchorage into the ground beam not printed")},
                   rfi={"extent": "RFI-S04"}, gap="G-T359-6"))
    out.append(pop("BW-COL-LINK", "BOUNDARY WALL", "BW-COLUMN", "column links", None,
                   f"{bw}: ties drawn in the column, no label", not_drawn=True, rfi={}, gap="G-T359-6"))
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
                rfi={"extent": "RFI-S03"}, gap="G-T359-7"))
    for code, comp, lab in (("A", "pad bars labelled 7ø12", "7%%c12"), ("B", "pad bars labelled 4ø12 (B.W)", "4%%c12 (B.W)")):
        out.append(pop(f"BW-PAD-{code}", "BOUNDARY WALL", "BW-PAD", f"pad 130 x 80 x 30: {comp}", lab, bw, {
            "layer": P(bw, "bottom"),
            "direction": N("'(B.W)' not defined on the sheet (both ways? the B.W beam row?); 7ø12 drawn across the 80 "
                           "with up-turned ends") if code == "B" else P(bw, "across the 80 width, hooked ends drawn"),
            "extent": N("pad positions 'SEE ARCH PLAN', none marked"),
            "end_shape": END_B}, rfi={"extent": "RFI-S04"}, gap="G-T359-7" if code == "B" else ""))
    return out


ELEMENTS = ["STAIR ST-01", "STAIR ST-02", "STAIR E1", "STAIR D1", "POOL", "TERRACE DOMES", "TOWER DOME",
            "ROOF WATER TANK", "LIFT PIT", "BOUNDARY WALL"]

RELEASED = [  # released STR.REBAR lines that touch these elements (T-149 / T-152 / T-136 ledgers, candidate V3.0.x)
    {"line_id": "BM-1F-028 bottom 4ø16", "element_id": "DOME-A-RING", "component": "beam B4 bottom bars"},
    {"line_id": "BM-1F-028 top 2ø12", "element_id": "DOME-A-RING", "component": "beam B4 top bars"},
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
    return {"schema": "T359_BAR_DETAIL_INPUT_V1", "villa": "development villa (Drive folder 'Alsenan chalet project')",
            "rfi_register": rfi_register(folder), "answered_rules": [OPT_B, "Q-71", "Q-26 A", "Q-47 A"],
            "elements_required": ELEMENTS, "released_lines": RELEASED, "populations": pops}


if __name__ == "__main__":
    json.dump(build(Path(sys.argv[1])), open(sys.argv[2], "w", encoding="utf-8"), indent=1, ensure_ascii=False)
