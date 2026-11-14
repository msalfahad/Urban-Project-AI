"""Blank-lines map: every line of the newest index that still has no figure (BLANK) or only a range (HELD), grouped by
trade, with why it is blank, what fills it, and what the owner can give. Writes BLANK_LINES_<ver>.md and adds a
"Blank lines" sheet to the workbook. Rebar is parked and listed only as a count.

    python3 -I blank_lines.py LINE_INDEX.json MAIN_FILL_ALL.json workbook.xlsx out.md
"""
from __future__ import annotations
import json, sys, collections, re
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# trade, why blank, what fills it (method step), what the owner can give
R = {
 "STR.CONC.GROUND_BEAM": ("Concrete", "ground-beam band with no section read (B x D not on the plan band)", "company default: exterior GB = same mark as the adjacent one; else the GB schedule", "the GB mark / section (B x D) of the bands listed, from the foundation plan or schedule"),
 "STR.CONC.BEAM": ("Concrete", "beam in the ledger with no depth printed", "company default: depth of the same mark, else adjacent span, else 0.60", "the beam schedule (mark -> B x D) for the beams listed"),
 "STR.CONC.LINTEL": ("Concrete", "opening with no width or no height printed", "opening size from the door / window schedule -> standard lintel length", "the door / window schedule sizes (W x H) for the openings listed"),
 "STR.CONC.COLUMN": ("Concrete", "2F column with no section in the schedule read", "schedule governs; else same mark as the floor below", "confirm the 2F column sections C2 / C3 of sheet SH12"),
 "STR.CONC.NECK": ("Concrete", "neck (column below GF) with no height read", "neck height = footing top to ground-beam soffit (default from the foundation section)", "the neck height or the foundation section level (footing top / GB soffit)"),
 "STR.CONC.STAIR": ("Concrete", "stair flight with no section read (waist, risers, width)", "hand calculation from the stair section: waist x width x sloped length + steps", "the stair section: waist thickness, number of risers, flight width"),
 "STR.CONC.PARAPET": ("Concrete", "RC parapet with no height / thickness read", "default parapet 1.20 high x 0.15 x roof-edge length", "confirm parapets are RC (not block) and their height / thickness"),
 "STR.CONC.LIFT": ("Concrete", "lift tie beam / pit walls with no section read", "default lift walls 0.20; tie = nearest printed beam", "the lift shaft section (pit depth, wall thickness, tie beam size)"),
 "STR.CONC.BLINDING": ("Concrete", "blinding under pool base / boundary wall base with no extent read", "plan area x 0.10 (pool base area; boundary wall footing area)", "confirm blinding 10 cm under the pool and the boundary-wall footing"),
 "STR.CONC.POOL": ("Concrete", "pool steps with no geometry read", "hand calculation from the pool section", "the pool section (steps, wall / base thickness)"),
 "STR.CONC.DOME": ("Concrete", "third dome shell with no radius / thickness read", "same as the two measured domes if the same mark", "confirm dome 3 is the same as domes 1 / 2 (radius, thickness)"),
 "STR.CONC.BOUNDARY_PAD": ("Concrete", "boundary-wall pads with no count / size read", "count x pad size from the fence foundation detail", "the fence foundation detail (pad size and spacing)"),
 "STR.CONC.STRAP": ("Concrete", "strap beam range", "section from the foundation schedule", "the strap beam section"),
 "STR.CONC.FOOTING": ("Concrete", "footing range", "footing schedule", "the footing mark"),
 "STR.CONC.BOUNDARY_WALL": ("Concrete", "boundary RC wall range", "height x thickness x length from the fence detail", "the boundary wall height / thickness"),
 "STR.FORMWORK": ("Formwork", "formwork of a concrete line that is itself blank, or a face with no host", "host concrete m3 x the villa's own m2/m3 ratio (6.3 beams, 8.3 columns, 3.8 slabs) once the host has a figure", "allow 'formwork = concrete x villa ratio' for EVERY held formwork line now (one decision clears 198 lines)"),
 "STR.FORMWORK.STAIR": ("Formwork", "stair formwork with no stair concrete", "stair concrete x 3.6 m2/m3", "same decision as formwork"),
 "MAS.BLOCK": ("Blockwork", "wall group (floor, thickness) with no height or no net area: annex height, dome walls, drop panels, wall under members", "T-765 defaults: wall height = storey - slab (GF 4.34, annex 3.84, upper 4.04) minus beam depth where a beam sits on the wall; full opening deduction", "confirm the blockwork wall height rule: storey - slab - beam depth (beam 0.60 default), or slab to slab minus beam only"),
 "ARCH.WALL_PANEL": ("Blockwork", "same wall groups (panel area)", "follows MAS.BLOCK", "same as blockwork"),
 "ARCH.WALL_VOLUME": ("Blockwork", "same wall groups (volume)", "area x thickness", "same as blockwork"),
 "MAS.UNITS.BLACK": ("Blockwork", "block count of a wall group with no area", "area x 12.5", "same as blockwork"),
 "MAS.UNITS.WHITE": ("Blockwork", "white (AAC) block count of a wall group with no area", "area x 12.5 (AAC 60 x 20 face: confirm)", "which walls are white AAC and the AAC block face size"),
 "MAS.MORTAR.BLACK": ("Blockwork", "mortar of a wall group with no area", "area x thickness x mortar share (Q-78)", "same as blockwork"),
 "MAS.MORTAR.BLACK.PERIMETER": ("Blockwork", "perimeter joint mortar of a wall group with no area", "wall length x joint", "same as blockwork"),
 "MAS.MORTAR.BLACK.LINTEL_BEARING": ("Blockwork", "lintel bearing mortar range", "lintel count x 2 x 0.15 bearing", "none"),
 "MAS.GLUE.AAC": ("Blockwork", "AAC glue of a wall group with no area", "area x 3.5 / 4.5 kg", "same as white blocks"),
 "FIN.PLASTER": ("Plaster", "reveal of an arch / door with no height", "opening height x reveal depth", "the opening heights A-GF-01, A-1F-01, D-GF-15"),
 "FIN.PLASTER.BEAD": ("Plaster", "corner bead of a room with no corner count", "count external corners x height", "none (counted from the plan)"),
 "FIN.PAINT": ("Paint", "paint range (wet room backing)", "plaster - tiled", "none"),
 "FIN.PAINT.EDGE": ("Paint", "edge of a reveal with no height", "jambs + head lm", "same opening heights"),
 "FIN.EXT.FINISH": ("External render", "facade with no outline x height", "facade perimeter x storey height - openings (sample method)", "confirm external render = outer perimeter x slab-to-slab height - openings, parapets both faces"),
 "ARCH.FACADE": ("External render", "facade area not computed (plinth too)", "same", "same + plinth height below F.F.L."),
 "ARCH.FACADE_RUN": ("External render", "facade outline length not computed", "outer perimeter per floor", "none"),
 "FIN.EXT.PAINT.EDGE": ("External render", "external edge lm of an opening with no height", "jambs + head + sill lm", "same opening sizes"),
 "EXT.FENCE.FACE": ("Fence / site", "fence face with no length x height", "segment length x height from the site plan", "fence length and height per side (sea, street, north, lower) and the below-ground band"),
 "EXT.FENCE.PLASTER": ("Fence / site", "follows fence face", "face area", "same"),
 "EXT.FENCE.PAINT": ("Fence / site", "follows fence face", "face area", "same"),
 "EXT.FENCE.BLOCK": ("Fence / site", "fence blockwork with no length x height", "length x height - gates", "same"),
 "EXT.FENCE.BLOCK_COUNT": ("Fence / site", "follows fence block", "area x 12.5", "same"),
 "EXT.FENCE.WALL": ("Fence / site", "wall plane not computed", "same", "same"),
 "EXT.FENCE.TOP": ("Fence / site", "fence top lm", "length", "same"),
 "EXT.FENCE.GATE": ("Fence / site", "gate leaves with no size", "count x size", "gate sizes G-01, G-02"),
 "EXT.FENCE.MASONRY_BELOW_NG": ("Fence / site", "fence band below ground with no height", "length x depth", "depth of the fence wall below ground"),
 "EXT.POOL.WATER_FACE": ("Fence / site", "pool water face finish not computed", "pool wall perimeter x depth + base", "pool depth"),
 "FIN.STAIR.SKIRTING.SLOPED": ("Stairs", "sloped skirting of a flight with no length", "flight sloped length from risers / treads", "stair section: risers and treads per flight (or confirm 0.15-0.175 / 0.28-0.30 defaults)"),
 "FIN.STAIR.SKIRTING.ZIGZAG": ("Stairs", "zigzag skirting of a flight with no step count", "steps x (riser + tread)", "same"),
 "FIN.SKIRTING": ("Stairs", "stair hall / landing skirting with no length", "landing perimeter - openings", "same"),
 "FIN.STAIR.FLIGHT": ("Stairs", "flight length not computed", "risers x tread", "same"),
 "FIN.STAIR.STEP_LM": ("Stairs", "step lm range", "steps x width", "same"),
 "FIN.STAIR.SOFFIT": ("Stairs", "stair soffit with no sloped length", "width x sloped length", "same"),
 "FIN.MARBLE.TREAD": ("Stairs", "flight 1 treads not computed", "steps x width x tread", "same"),
 "FIN.MARBLE.RISER": ("Stairs", "riser marble range", "steps x width x riser", "same"),
 "FIN.MARBLE.LANDING": ("Stairs", "landing range", "plan area", "none"),
 "FIN.MARBLE.LIFT_SURROUND": ("Stairs", "lift door surround range", "door size", "lift door size"),
 "FIN.RAILING": ("Stairs", "railing with no run length", "flight sloped length + landing edge", "same stair section; railing type (steel / glass / timber)"),
 "MET.RAILING.GUARD": ("Stairs", "guard rail with no run length", "edge length", "same"),
 "FIN.WP.PENETRATION": ("Waterproofing", "one per sanitary fixture; fixture count of the wet room not read", "count the fixtures on the plan (WC, basin, shower, floor drain)", "the sanitary fixture count per bathroom (or the sanitary schedule)"),
 "FIN.WP.DOORWAY_TRANSITION": ("Waterproofing", "door width of the wet room not read", "door width x 0.30", "door widths OP-010 / 017 / 018"),
 "FIN.WP.WALL_UPTURN": ("Waterproofing", "wet zone perimeter not read", "perimeter x 1.0 upturn (freelancer: x 1.0)", "none"),
 "FIN.WP.ROOF_UPTURN": ("Waterproofing", "top roof parapet length", "roof perimeter x 0.30", "none"),
 "FIN.WP.MEMBRANE_ROLLS": ("Waterproofing", "roll count", "area / 10 m2 per roll + laps", "roll size you buy"),
 "FIN.WP.TERMINATION": ("Waterproofing", "termination lm range", "perimeter", "none"),
 "FIN.WP.ROOF": ("Waterproofing", "roof membrane range", "roof area", "none"),
 "WP.FOUNDATION.BURIED_LIQUID": ("Waterproofing", "foundation WP system: footing tops, GB faces, necks (NOT in the freelancer BOQ)", "faces from the foundation concrete once filled", "DECIDE: is foundation waterproofing in scope? (freelancer has none)"),
 "WP.FOUNDATION.FOOTING_SIDES": ("Waterproofing", "same", "same", "same decision"),
 "WP.FOUNDATION.FOOTING_SCREED": ("Waterproofing", "same", "same", "same decision"),
 "WP.FOUNDATION.FOOTING_MEMBRANE": ("Waterproofing", "same", "same", "same decision"),
 "WP.FOUNDATION.LIFT_PIT_MEMBRANE": ("Waterproofing", "same", "same", "same decision"),
 "WP.FOUNDATION.LIFT_PIT_BOARD": ("Waterproofing", "same", "same", "same decision"),
 "WP.FOUNDATION.PROCUREMENT": ("Waterproofing", "same", "same", "same decision"),
 "STR.EARTH.EXCAVATION": ("Earthworks", "trench / pit zone with no width x depth", "trench = (GB width + 2 x 0.30 working space) x depth; pit = footing + working space", "excavation depth below ground level and working space (default 0.30 each side)"),
 "STR.EARTH.BACKFILL": ("Earthworks", "backfill zone with no excavation figure", "excavation - concrete", "same"),
 "STR.EARTH.DISPOSAL": ("Earthworks", "disposal range", "excavation - backfill", "none"),
 "ARCH.WINDOW_REVEAL": ("Openings", "window reveal with no size (W02, W03, W17)", "jambs + head + sill x reveal depth", "sizes of W02, W03, W17 from the window schedule"),
 "ARCH.THRESHOLD": ("Openings", "threshold strip with no door width", "width x wall thickness", "door widths of the openings listed"),
 "ARCH.SHUTTER": ("Openings", "shutter with no size (W11, W12, W14)", "W x H", "sizes of W11, W12, W14"),
 "ARCH.WINDOW": ("Openings", "GF window with no figure in the schedule", "W x H", "the window schedule row"),
 "ARCH.SPACE": ("Openings", "space area range", "plan area", "none"),
 "DOOR.INTERNAL.PVC": ("Openings", "PVC door range", "schedule", "confirm PVC door count / size"),
 "DOOR.MAIN_ENTRANCE": ("Openings", "main door range", "schedule", "main door size"),
 "FIN.CEILING": ("Ceilings", "stairwell / strip ceiling with no area", "plan area of the stairwell", "confirm stairwell ceilings are gypsum (or plaster + paint only)"),
 "FIN.CEILING.BULKHEAD": ("Ceilings", "bulkhead with no length x drop", "length x 0.30 drop", "none"),
 "FIN.DOME.SOFFIT": ("Ceilings", "dome intrados with no radius", "2 pi r h", "dome radius / rise (same as the concrete)"),
 "FIN.WALL.TILE": ("Tiles", "wet room with no perimeter x tile height", "perimeter x height (to the false ceiling 2.70; sample: 3.00) - openings", "confirm wall-tile height: to the decor ceiling (Q-48) = 2.70 default"),
 "FIN.FLOOR.FINISH_HELD": ("Tiles", "floor finish range", "plan area", "finish of the room"),
 "EXT.FLOOR.OUTDOOR": ("Tiles", "outdoor floor range", "plan area", "none"),
 "STR.REBAR": ("Rebar (parked)", "parked", "approximate tons at the end", "none"),
}
ORDER = ["Concrete", "Formwork", "Blockwork", "Plaster", "Paint", "External render", "Tiles", "Ceilings", "Waterproofing", "Stairs", "Openings", "Earthworks", "Fence / site", "Rebar (parked)", "Other"]


def main(index_path, fill_path, xlsx_path, md_path):
    idx = json.load(open(index_path)); fill = json.load(open(fill_path))
    ver = idx.get("candidate_version", "?")
    # T-796 R-T796-1: the MAIN FILL overlay applies only where the index line still carries the row's 'before' state and
    # no later fill_basis; a newer wired value is never overridden (skips listed in the markdown)
    import importlib.util as _iu, pathlib as _pl
    _s = _iu.spec_from_file_location("boq_overlay", _pl.Path(__file__).resolve().parent / "overlay.py"); O = _iu.module_from_spec(_s); _s.loader.exec_module(O)
    lines = [dict(l) for l in idx["lines"]]
    olog = O.apply_overlay(lines, fill); osum = O.summary(olog)
    rows = []
    for l in lines:
        if l["class"] == "EXCLUDED":
            continue
        if l["class"] != "HELD":
            continue
        blank = l["held_low"] is None and l["held_high"] is None
        t = R.get(l["item_code"], ("Other", "no figure", "to be decided", "?"))
        rows.append(dict(trade=t[0], code=l["item_code"], unit=l["unit"], eid=str(l.get("element_id")), state="BLANK" if blank else "HELD range", low=l["held_low"], high=l["held_high"], why=t[1], fills=t[2], owner=t[3], lid=l["line_id"]))
    rows.sort(key=lambda r: (ORDER.index(r["trade"]), r["code"], r["state"], r["eid"]))
    by = collections.defaultdict(lambda: dict(blank=0, held=0, codes=set(), owner=set()))
    for r in rows:
        b = by[r["trade"]]; b["blank" if r["state"] == "BLANK" else "held"] += 1; b["codes"].add(r["code"]); b["owner"].add(r["owner"])
    # markdown
    md = [f"# Blank lines of {ver} (with MAIN FILL applied): where the figures are missing and what fills them", "",
          "BLANK = no figure at all; HELD range = low..high only. Rebar is parked (count only). Every other line gets a figure by",
          "the fallback order (geometry -> drawing read -> company default -> ratio -> safety); the last column says what the owner can give to", "make it DRAWING-READ instead of DEFAULT.", "",
          "## Per trade", "", "| trade | BLANK | HELD range | what the owner can give |", "|---|---|---|---|"]
    for t in ORDER:
        if t in by:
            b = by[t]; md.append(f"| {t} | {b['blank']} | {b['held']} | {'; '.join(sorted(o for o in b['owner'] if o not in ('none', 'same', '?')))} |")
    sk = [e for e in olog if e["action"].startswith("SKIP")]
    md += ["", f"## MAIN FILL overlay (T-796 precedence): {json.dumps(osum)}", "",
           "A row applies only where the index line still carries the row's before state and no later fill_basis. Rows skipped"
           " (the index value stands):", "", "| line id | item | unit | action | index | MAIN FILL row |", "|---|---|---|---|---|---|"]
    for e in sk:
        md.append(f"| {e['line_id']} | {e['item_code']} | {e['unit']} | {e['action']} | {e['index']} | {e['row_after']} |")
    md += ["", "## Every line (rebar left out)", "", "| trade | item | unit | element | state | low | high | why no figure | what fills it | owner can give |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["trade"].startswith("Rebar"):
            continue
        md.append(f"| {r['trade']} | {r['code']} | {r['unit']} | {r['eid'][:60]} | {r['state']} | {r['low'] if r['low'] is not None else ''} | {r['high'] if r['high'] is not None else ''} | {r['why']} | {r['fills']} | {r['owner']} |")
    open(md_path, "w").write("\n".join(md) + "\n")
    # workbook sheet
    wb = openpyxl.load_workbook(xlsx_path)
    if "Blank lines" in wb.sheetnames:
        del wb["Blank lines"]
    ws = wb.create_sheet("Blank lines", 2)
    F = Font(name="Arial", size=10); FB = Font(name="Arial", size=11, bold=True); FH = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    HF = PatternFill("solid", fgColor="1F4E78"); BR = Border(*(Side(style="thin", color="BBBBBB"),) * 4)
    ws.append([f"Blank lines of {ver} (MAIN FILL applied). BLANK = no figure; HELD range = low..high only. Rebar parked: {by.get('Rebar (parked)', {}).get('blank', 0) + by.get('Rebar (parked)', {}).get('held', 0)} lines not listed."]); ws["A1"].font = FB
    ws.append([])
    ws.append(["Trade", "BLANK", "HELD range", "What the owner can give"])
    for x in ws[3]: x.font = FH; x.fill = HF; x.border = BR
    for t in ORDER:
        if t in by:
            b = by[t]; ws.append([t, b["blank"], b["held"], "; ".join(sorted(o for o in b["owner"] if o not in ("none", "same", "?")))])
    ws.append([])
    hdr = ["Trade", "Item", "Unit", "Element", "State", "Low", "High", "Why no figure", "What fills it", "Owner can give", "Line id"]
    ws.append(hdr); h = ws.max_row
    for x in ws[h]: x.font = FH; x.fill = HF; x.border = BR
    for r in rows:
        if r["trade"].startswith("Rebar"):
            continue
        ws.append([r["trade"], r["code"], r["unit"], r["eid"], r["state"], r["low"], r["high"], r["why"], r["fills"], r["owner"], r["lid"]])
    for rw in ws.iter_rows(min_row=4, max_row=ws.max_row):
        for x in rw: x.font = F; x.border = BR; x.alignment = Alignment(wrap_text=True, vertical="top")
    for i, w in enumerate([16, 30, 6, 44, 11, 9, 9, 48, 44, 44, 24], 1): ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row=h + 1, column=1); ws.auto_filter.ref = f"A{h}:K{ws.max_row}"
    wb.save(xlsx_path)
    print(json.dumps({t: dict(blank=by[t]["blank"], held=by[t]["held"]) for t in ORDER if t in by}))


if __name__ == "__main__":
    main(*sys.argv[1:5])
