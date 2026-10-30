"""T-366 Alsenan input: the lap-authority readings (printed values only) for every released-route bar population, and
the binding of the candidate's reinforcement lines (V3.0.16 extract of T-297, equal line by line to V3.0.17) to them.

Readings were made this run from the private copies of Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256
9f9d1179..) and 'ST7757.pdf' (sha256 74da1523..; no text layer, read by eye at 100 / 200 / 400 dpi). Only notation is
recorded here (sheet, handle or position, value); no drawing, image or client datum is copied.

    python -I research/agents_t366/t366_alsenan_input.py            # writes ALSENAN_LAP_AUTHORITY_INPUT.json + LINE_BINDING_T366.json
    python -I research/agents_t366/t366_alsenan_input.py --check    # rebuilds in memory and compares
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
EXTRACT = os.path.join(REPO, "research", "agents_t297", "CANDIDATE_V3016_REBAR_LINES.json")

# ------------------------------------------------------------------ sources that print anything about laps / splices
SOURCES = {
    "N9": {"sheet": "ST p.8 general notes", "position": "right column, note 9 (Arabic; PDF only, no DXF text)",
           "kind": "NOTE", "category": "STARTER_BARS", "names": ["STARTER_SHALLOW", "STARTER_DEEP"],
           "wording": "tie / development length of the STARTER bars (اشاير) not less than 70 x bar dia in tension "
                      "zones, 40 x bar dia in compression zones",
           "value_d": {"TENSION": 70, "COMPRESSION": 40}, "value_kind": "MINIMUM",
           "zones": {"TENSION": 70, "COMPRESSION": 40}, "typical": False},
    "P15N1": {"sheet": "ST p.15 DETAILS (3)", "position": "NOTE 1 beside the TEMPERATURE REINFORCEMENT SCHEDULE (PDF only)",
              "kind": "NOTE", "category": "LAP_SPLICE", "names": ["SLAB_TEMPERATURE"],
              "wording": "LAP LENGTH FOR ALL TEMPERATURE BARS SHALL BE 40 x DIA",
              "value_d": {"ANY": 40}, "value_kind": "EXACT", "zones": {"ANY": 40}, "typical": False},
    "P13D40": {"sheet": "ST p.13 DETAILS (1)", "position": "TYP. DETAIL OF ISOLATED FOOTING (right; level difference "
                                                           "upper G.B to footing below 2.5 m): vertical dimension '40 ø' from the footing top up "
                                                           "the column, where the drawn starter ends with its crank (PDF only)",
               "kind": "DETAIL", "category": "STARTER_BARS", "names": ["STARTER_SHALLOW"],
               "wording": "starter projection above the footing top dimensioned 40 ø (typical detail)",
               "value_d": {"ANY": 40}, "value_kind": "EXACT", "zones": {"ANY": 40}, "typical": True},
}

# texts / details searched that print NO lap length (recorded per population under checked_not_naming)
CHK = {
    "DXF": "all 1,934 DXF TEXT / MTEXT / ATTRIB entities (model space + blocks) searched for lap / splice / overlap / "
           "dia / anchor / develop / stock / length and Arabic تشريك / رباط / اشاير / طول / وصل / تراكب: one hit, "
           "1BA9 '* L=LENGTH OF COLUMN.' (p.9 link-band notation, not a lap)",
    "P8": "p.8 notes 1-24 (only note 9 concerns bar lengths; note 6 f'c >= 300 kg/cm2, note 8 fy >= 4200 kg/cm2, "
          "note 21 side bars, note 22 cover)",
    "P9": "p.9 schedules of columns (1B3A) and footings (1C32), DETAILS OF COLUMN REINFORCEMENT (1BA5, 1BA9, 1BAA)",
    "P10": "p.10 Schedule of Simple Beams (1E47)",
    "P1112": "p.11 / p.12 continuous-beam schedules (206B, 272B, 2035) and their typical span diagram",
    "P13": "p.13 typical footing details, ground-beam sections, lintel detail / schedule",
    "P14": "p.14 lift, TYPICAL BOUNDARY WALL plan / section A-A, parapets",
    "P15": "p.15 twisted column, beam in casement, TYP. SLAB ON BEAMS DETAIL, notes 1-3, planted-column beam",
}
ALL_CHK = ["DXF", "P8", "P9", "P10", "P1112", "P13", "P14", "P15"]

T273 = "research/agents_t273/T-273_LAPS_AND_TONNES.md s.3 (MERGED)"
T149 = "research/agents_t149/T-149_BEAM_STEEL_BY_POPULATION.md (no bar run over 12 m: longest CB1 / CB8 support bars 5.6 m, B22 7.80 m)"


def P(pid, family, group, desc, need, basis="", auth=(), marks="", finding="", chk=None):
    return {"id": pid, "family": family, "group": group, "description": desc, "splice_need": need,
            "need_basis": basis, "authorities": [{"source": s} for s in auth], "bar_marks": marks,
            "checked_not_naming": chk if chk is not None else ALL_CHK, "finding": finding}


POPULATIONS = [
    P("FTG-BOTTOM", "FOOTINGS", "FOOTING_MESH", "isolated footing bottom short / long bars (F .. F15, FN; F8 / F12-F14 / FF bottom '/m')",
      "NOT_REQUIRED", "largest footing side 4.60 m (FF, p.9) < 12 m stock: one bar spans the footing; p.13 draws each bar whole"),
    P("FTG-TOP", "FOOTINGS", "FOOTING_MESH", "footing top mesh and its end legs (F8, F12 - F14, FF 'TOP' rows)",
      "NOT_REQUIRED", "same footings, sides <= 4.60 m"),
    P("FTG-BOXED", "FOOTINGS", "FOOTING_BOXED", "boxed bars (p.9 'BOXED 3+4' .. '3+8'; p.13 'Boxed bars.')",
      "NOT_ESTABLISHED", finding="the boxed bar is drawn as an open U with end cranks on p.13; whether a closure overlap "
                                 "exists is a shape question (HOOK_BEND, T-371), no lap printed"),
    P("NECK-STARTER-SHALLOW", "COLUMNS", "STARTER_SHALLOW",
      "starter-to-column splice at the footing top, footings whose upper G.B is < 2.5 m above (p.13 right detail)",
      "DRAWN_OVERLAP", auth=["P13D40", "N9"],
      finding="F-T366-1: p.13 DIMENSIONS the starter projection 40 ø (typical detail). T-273 r2 and the column ledger take "
              "their 40 D starter projection from note 9's compression minimum; the printed basis is this detail. Note 9 "
              "(starter bars, >= 70 d in tension zones) also names these bars: the detail's 40 ø equals note 9 only in a "
              "compression zone; the zone is not printed -> applicability CONFLICT for the Checker, lap value printed, "
              "nothing changed"),
    P("NECK-STARTER-DEEP", "COLUMNS", "STARTER_DEEP",
      "starter-to-column splice where the upper G.B is more than 2.5 m above the footing (p.13 left detail, with a lower G.B)",
      "DRAWN_OVERLAP", auth=["N9"],
      finding="p.13 left detail draws the starter cranks at the footing top and the column-bar cranks above the lower "
              "G.B (splice zone drawn), no dimension; only note 9 names these bars, zone not printed -> HELD"),
    P("COL-MAIN", "COLUMNS", "COLUMN_MAIN", "column main bars and their storey-joint splices GF / 1F / 2F (p.9 schedule; "
                                            "bar count changes per storey, e.g. C1 8 -> 6 ø16)",
      "REQUIRED", "a bar change at each storey joint (p.9) and 8 GF-1F-2F stacks of 12.90 m > 12 m (T-148, MERGED)",
      finding="F-T366-2: no note or detail prints a column lap; the candidate's 56 'LAP at storey bottom (reading S/P)' "
              "lines carry note 9 (a STARTER_BARS note) as their basis: category outside its named group (owner "
              "2026-10-24 s.6 (1)); they are BOUNDED_EXPOSURE, never released; the census leaves them as they are"),
    P("COL-LINKS", "COLUMNS", "COLUMN_LINKS", "column links 6 ø8/m (1BAA), closed / overlapping links by L band (p.9)",
      "NOT_REQUIRED", "a link is one closed bar of perimeter < 12 m; its closure is a HOOK_BEND attribute (135-degree hooks "
                      "drawn, no length: T-148), not a lap splice"),
    P("COL-TWIST-EXTRA", "COLUMNS", "COLUMN_TWIST", "twisted-column extra 4 ø16 and spiral 6 ø8/m (p.15)",
      "NOT_ESTABLISHED", finding="p.15 draws the GF and 1F column bars passing the floor with no lap dimension"),
    P("GB-MAIN", "GROUND_BEAMS", "GROUND_BEAM_MAIN", "ground-beam top / bottom / longitudinal bars (p.13 sections; SH08 bands)",
      "REQUIRED", T273 + ": south band 7D0 / FC 18.570 m, north band 170 / 7C3 13.770 m through interior columns > 12 m"),
    P("GB-SIDE", "GROUND_BEAMS", "GROUND_BEAM_SIDE", "ground-beam side bars 2 ø12/30cm (p.13 exterior-wall section)",
      "NOT_ESTABLISHED", "continuity of side bars through the columns not printed (T-273 s.8)"),
    P("GB-STIRRUP", "GROUND_BEAMS", "GROUND_BEAM_LINKS", "ground-beam stirrups ø8/15cm (p.13)",
      "NOT_REQUIRED", "closed link < 12 m; closure is HOOK_BEND (T-272: drawn with no hook or overlap)"),
    P("STRAP-MAIN", "GROUND_BEAMS", "STRAP_MAIN", "strap beams SB1 - SB3 top / bottom (p.10 schedule rows)",
      "NOT_REQUIRED", "route G strap bar 5.70 m + 2 x 40 d at most 7.14 m < 12 m (T-299 s.3)"),
    P("BEAM-SIMPLE-MAIN", "BEAMS", "BEAM_MAIN", "simple beams B1 - B29, CA, B.W top / bottom / corner bars (p.10)",
      "NOT_REQUIRED", T149),
    P("BEAM-SIDE", "BEAMS", "BEAM_SIDE", "beam side bars (p.8 note 21; p.10 REMARKS 2 ø12/30cm, 2 ø14 / 2 ø16/20cm; CB 'MIDDLE REINT.')",
      "NOT_REQUIRED", "run along single beams <= 7.80 m (" + T149 + ")"),
    P("BEAM-LINKS", "BEAMS", "BEAM_LINKS", "beam stirrups n ø8 / ø10 per m (p.10, p.11 / p.12 (STIR) rows)",
      "NOT_REQUIRED", "closed link < 12 m; closure is HOOK_BEND"),
    P("CB-BOTTOM", "BEAMS", "CB_BOTTOM", "continuous-beam bottom bars of adjacent spans (p.11 / p.12)",
      "DRAWN_OVERLAP", finding="F-T366-3: the typical span diagram and every CB row draw the bottom bars of the two spans "
                               "overlapping across the interior support (e.g. CB1 4 ø18 / 5 ø18), the overlap length is not "
                               "dimensioned ('0.15 L' is drawn but tied to no bar: T-149); the candidate's 'bottom ends (note 9, "
                               "40d..70d)' lines use the starter note outside its group -> lap HELD"),
    P("CB-TOP-THROUGH", "BEAMS", "CB_TOP", "continuous-beam top through / corner bars (p.11 / p.12)",
      "NOT_REQUIRED", "longest route G continuous-beam bar run 8.708 m < 12 m (owner rule s.5, instrumented run)"),
    P("CB-SUPPORT-TOP", "BEAMS", "CB_SUPPORT", "continuous-beam support bars 0.22 Ln each side (p.11 / p.12)",
      "NOT_REQUIRED", "0.22 Ln1 + support + 0.22 Ln2 <= 5.6 m (" + T149 + ")"),
    P("PLANTED-COL-BEAM", "BEAMS", "BEAM_PLANTED", "beam carrying a planted column: 4 ø16 (p.15)",
      "NOT_REQUIRED", "inside one beam, drawn whole; beams <= 7.80 m"),
    P("SLAB-BOTTOM-MAIN", "SLABS", "SLAB_MAIN", "suspended-slab bottom mesh (p.4 - p.6 plans; p.15 typical slab detail)",
      "NOT_ESTABLISHED", finding="p.15 prints continuity ('STOP 50% OF BOT. REINF. BALANCE CONTINUOUS') but no lap; whether "
                                 "a continuous bottom bar exceeds 12 m is not established by a merged ledger (T-273: slab "
                                 "transitions HELD); the candidate's 'DEVELOPMENT / ANCHORAGE' lines (note 9) are outside "
                                 "note 9's group (T-307 ENGINE_WRONG in basis)"),
    P("SLAB-TOP-SUPPORT", "SLABS", "SLAB_TOP", "slab top bars over supports (p.15: 0.25 / 0.30 L, 'EXTEND 50% OF TOP "
                                               "REINF. INTO ADJACENT SLAB WHERE POSSIBLE')",
      "NOT_ESTABLISHED", "extension into the next slab printed as a fraction, no lap length"),
    P("SLAB-TEMPERATURE", "SLABS", "SLAB_TEMPERATURE", "slab temperature bars (p.15 schedule Y10 / Y12 ø200 by slab thickness; note 2)",
      "NOT_ESTABLISHED", auth=["P15N1"],
      finding="the lap value is printed and names this group; the group itself is blocked (no 160 mm row in the table "
              "for the 16 cm slabs of note 18: diameter not established, T-273), so the lap length in mm waits on it"),
    P("SLAB-EXTRA", "SLABS", "SLAB_EXTRA", "slab corner bars / second-bar zones (candidate BLOCKED lines)",
      "NOT_ESTABLISHED"),
    P("GROUND-SLAB-MESH", "GROUND_SLAB", "GROUND_SLAB_MESH", "ground slab on grade mesh D10 (route G SLAB_NOTE_MESH_SCOPE)",
      "NOT_ESTABLISHED", finding="mesh sheet / bar lap not printed"),
    P("BW-GB", "BOUNDARY_WALL", "BOUNDARY_GB", "boundary-wall G.B 2 ø14 (T&B) / 3 ø16 (T&B) (p.14 section A-A)",
      "REQUIRED", T273 + ": boundary run 7FE#1 31.370 m continuous through the boundary columns"),
    P("BW-COLUMN", "BOUNDARY_WALL", "BOUNDARY_COLUMN", "boundary-wall columns 20 x 30, 4 ø14 (p.14)",
      "NOT_ESTABLISHED", finding="column height and starters into the G.B not printed (G-T359-6)"),
    P("BW-PAD", "BOUNDARY_WALL", "BOUNDARY_PAD", "boundary-wall pad 130 x 80 x 30, 7 ø12 and 4 ø12 (B.W) (p.14)",
      "NOT_REQUIRED", "pad 1.30 m: bars drawn whole"),
]
REQUIRED = [p["id"] for p in POPULATIONS]

STOCK = {"value_m": 12.0,
         "owner_source": "rules/methods/URBAN_METHOD_REGISTER_V3.json URBAN-REBAR-NET-AND-PROCUREMENT@v1 (owner decision "
                         "OD-V3-3, research/external_engine_lab/alsenan_v3_owner_decisions.json); same 12 m in "
                         "OWNER_RULE_REBAR_2026-10-24 s.2",
         "searched": "no stock / bar length printed on any sheet: " + CHK["DXF"] + "; p.8 notes 1-24; p.13 - p.16 by eye"}

WORKED_RUNS = [
    {"L": "23.8", "S": "12", "lap_d": 40, "d_mm": 12},   # printed lap: p.15 note 1 (40 x DIA), temperature bar Y12 (p.15 table)
    {"L": "35", "S": "12", "lap_d": 40, "d_mm": 12},
    {"L": "23.8", "S": "12", "lap_d": 40, "d_mm": 16},   # printed lap: p.13 '40 ø' starter projection, column bar ø16 (p.9)
    {"L": "35", "S": "12", "lap_d": 40, "d_mm": 16},
]


SHARED_BEAM = "BEAM-SIMPLE-MAIN|CB-BOTTOM|CB-TOP-THROUGH|CB-SUPPORT-TOP"   # route G beam items: mark not on the id


def bind(line):
    """candidate reinforcement line -> population id (or 'OUT:<reason>')."""
    e = line["element_id"]
    inp = line.get("inputs") or {}
    comp = str(inp.get("component") or inp.get("part") or "").lower()
    pre = ":".join(e.split(":")[:2])
    mark = str(inp.get("mark") or "")
    if pre == "HL:STAIR_POOL_TANK_STEEL":
        return "OUT:POOL_STAIR_TANK (T-359 scope, outside the released route)"
    if pre == "FRP:FTG":
        last = e.split(":")[-1]
        return {"BOXED": "FTG-BOXED", "TOP_LONG": "FTG-TOP", "TOP_SHORT": "FTG-TOP", "TOP_END_LEGS": "FTG-TOP"}.get(last, "FTG-BOTTOM")
    if pre == "P-S:NECK":
        return "NECK-STARTER-SHALLOW|NECK-STARTER-DEEP" if e.endswith("D16") else "COL-LINKS"
    if pre == "P-S:COL":
        return "COL-MAIN" if e.endswith("D16") else "COL-LINKS"
    if pre == "HL:COLUMN_STEEL":
        if "links" in comp:
            return "COL-LINKS"
        if "turn" in comp:
            return "COL-TWIST-EXTRA"
        return "COL-MAIN"
    if pre == "HL:GROUND_SYSTEM_STEEL":
        if e.split(":")[2] in ("SB1", "SB2", "SB3"):
            return "STRAP-MAIN"
        if "side" in comp:
            return "GB-SIDE"
        if "stirrup" in comp:
            return "GB-STIRRUP"
        return "GB-MAIN"
    if pre == "P-S:GROUND_BEAMS":
        return "GB-STIRRUP" if e.endswith("D8") else "STRAP-MAIN"
    if pre in ("P-S:BEAMS", "U-S:BEAMS"):
        if e.endswith(":D8") or e.endswith(":D10"):   # beam bars of 8 / 10 mm are links only (p.10 - p.12)
            return "BEAM-LINKS"
        if "CB_TOP_THROUGH" in e:
            return "CB-TOP-THROUGH"
        if "CB_SUPPORT" in e:
            return "CB-SUPPORT-TOP"
        return SHARED_BEAM if pre == "P-S:BEAMS" else "CB-TOP-THROUGH"
    if pre == "HL:BEAM_STEEL":
        cb = mark.startswith("CB")
        if "links" in comp:
            return "BEAM-LINKS"
        if "side" in comp:
            return "BEAM-SIDE"
        if "planted" in comp:
            return "PLANTED-COL-BEAM"
        if "over support" in comp:
            return "CB-SUPPORT-TOP"
        if comp.startswith("bottom"):
            return "CB-BOTTOM" if cb else "BEAM-SIMPLE-MAIN"
        if comp.startswith("top") or comp.startswith("end-support") or comp == "all bars":
            return "CB-TOP-THROUGH" if cb else "BEAM-SIMPLE-MAIN"
        return "BEAM-SIMPLE-MAIN"
    if pre == "HL:SLAB_STEEL":
        if "temperature" in comp or "TEMPERATURE" in e:
            return "SLAB-TEMPERATURE"
        if "top bars" in comp or "TOP_BARS" in e:
            return "SLAB-TOP-SUPPORT"
        if "bottom mesh" in comp or "development" in comp or "BOTTOM" in e or "DEVELOPMENT" in e:
            return "SLAB-BOTTOM-MAIN"
        return "SLAB-EXTRA"
    if pre == "P-S:SLABS":
        return "SLAB-BOTTOM-MAIN"
    if pre == "P-S:GROUND_SLAB":
        return "GROUND-SLAB-MESH"
    return "OUT:UNBOUND " + pre


def build():
    raw = open(EXTRACT, "rb").read()
    lines = json.loads(raw)["lines"]
    binding = collections.defaultdict(list)
    for ln in lines:
        binding[bind(ln)].append(ln["line_id"])
    unbound = [k for k in binding if k.startswith("OUT:UNBOUND")]
    if unbound:
        raise SystemExit(f"unbound candidate lines: {unbound}")
    pops = json.loads(json.dumps(POPULATIONS))
    for p in pops:
        own = [k for k in binding if k.split("|")[0] == p["id"] and "|" not in k]
        shared = [k for k in binding if "|" in k and p["id"] in k.split("|")]
        n_own = sum(len(binding[k]) for k in own)
        n_sh = sum(len(binding[k]) for k in shared)
        txt = f"{n_own} V3.0.16 lines" if n_own else "no own line in the candidate"
        if n_sh:
            txt += f"; plus {n_sh} lines shared with " + " / ".join(sorted({x for k in shared for x in k.split('|')} - {p['id']}))
        p["candidate_lines"] = txt + " (LINE_BINDING_T366.json)"
    data = {"schema": "LAP_AUTHORITY_CENSUS_INPUT_V1", "project": "development villa (Alsenan sample)",
            "sources_read": {"ST7757 dxf.dxf": "9f9d1179", "ST7757.pdf": "74da1523"},
            "checked": CHK, "sources": SOURCES, "populations": pops, "required_populations": REQUIRED,
            "stock": STOCK, "worked_runs": WORKED_RUNS}
    bind_out = {"schema": "LINE_BINDING_T366_V1", "extract": "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json",
                "extract_sha256": hashlib.sha256(raw).hexdigest(), "lines": len(lines),
                "by_population": {k: sorted(v) for k, v in sorted(binding.items())},
                "counts": {k: len(v) for k, v in sorted(binding.items())}}
    return data, bind_out


def _dump(obj):
    return json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv):
    data, b = build()
    p1, p2 = os.path.join(HERE, "ALSENAN_LAP_AUTHORITY_INPUT.json"), os.path.join(HERE, "LINE_BINDING_T366.json")
    if "--check" in argv:
        ok = open(p1, encoding="utf-8").read() == _dump(data) and open(p2, encoding="utf-8").read() == _dump(b)
        print("CHECK", "OK" if ok else "DIFFERS")
        return 0 if ok else 1
    open(p1, "w", encoding="utf-8").write(_dump(data))
    open(p2, "w", encoding="utf-8").write(_dump(b))
    print(json.dumps(b["counts"], indent=0))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
