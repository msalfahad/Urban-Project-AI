"""OWNER REPORT v6 - the PA02 gate report (directive §33 format).

    python3 -m research.qs_wall_treatment_01.owner_report_v6
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)


def build() -> str:
    d1 = json.loads((OUT / "D1_LEVEL_IDENTITY.json").read_text("utf-8"))
    dh = json.loads((OUT / "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json").read_text("utf-8"))
    ref = json.loads((OUT / "ROOF_EDGES_FACADE_FINISH_KERB.json").read_text("utf-8"))
    tw = json.loads((OUT / "TRADES_WET_OPENINGS_FLOORS_COVERAGE.json").read_text("utf-8"))
    gate = json.loads((OUT / "PA02_GATE.json").read_text("utf-8"))
    tr = json.loads((OUT / "PLASTER_QUANTITY_TRACE.json").read_text("utf-8"))
    led = json.loads((OUT / "REVISION_SUPERSESSION_LEDGER.json").read_text("utf-8"))
    cols = json.loads((OUT / "COLUMN_FACE_REGISTER.json").read_text("utf-8"))["COLUMNS"]
    L = ["# P7757 - owner report v6 (PA02 gate)", "",
         "PHASE: PA02 - level identity for D1, column faces, reception void and stair well, SE facade openings, external finish search, kerb profile, remaining roof edges, wet rooms, project openings, profile steel, floor-by-floor, coverage, incremental A22",
         "STATUS: technical work exhausted on the current source set; five owner items, none blocking", "",
         "## WHAT WAS PROVEN", "",
         f"- {d1['CORRECTION']}",
         "- +9.70 is the structural slab top and the parapet base (sections hatch the masonry from the slab top; the structural roof sheet prints +9.70 on the slab). "
         "+9.88 is a level line drawn 0.16-0.18 above the slab on two edges; no build-up is drawn anywhere; its identity stays NOT_ESTABLISHED after the sections, plans, DWG, structural set and (absent) build-up detail were exhausted.",
         f"- The FF void over the RECEPTION is {dh['DOUBLE_HEIGHT_FACE_REGISTER']['VOID']['W_M']} x {dh['DOUBLE_HEIGHT_FACE_REGISTER']['VOID']['D_M']} m (authored X-ed rectangle), bounded by railing line pairs (N, S, E) and the curved stair (W): no wall stands on it, so no double-height wall exists.",
         "- The block stair well prints 120 + 10 + 120 x 645 on the FF sheet; its walls are measured per storey from the level chains (+0.30 / +5.50 / +9.70 / +13.90), interruptions listed, underside not established.",
         "- The NE parapet top is +11.10 on the NE elevation (chain scale); A-A hatches 1.62 above the slab: the 1.40 face is carried, the 0.20 band is NOT_ESTABLISHED on the NE (the two readings disagree by the band).",
         "- The NW sea-view 10 cm x 1.30 element is an X-lattice balustrade on a low curved kerb (NW elevation prints 100 + 10; B-B 130 = lattice + cap): zero plaster for the lattice.",
         "- The SW parapet is seen end-on at the SE elevation's left end (SEG-04): ~1.35 above the base line (PROPOSED_CORRESPONDENCE).",
         "- SE facade: tower 4.41 m wide with a strip of four 1.20 windows (2.00 / 2.30 / 2.00 / 1.70 arched), a base door, the 2.15 x 1.90 grill window on the main block, the 2.50-high annex door; the entrance arch is drawn as stone blocks (cladding).",
         "", "## WHAT CHANGED", "",
         "- engine: level_identity (eight level fields, two bases), column_faces (exposure per face), wall_treatment_matrix (sequential treatments on one area).",
         "- registers: D1_LEVEL_IDENTITY, COLUMN_FACE_REGISTER, DOUBLE_HEIGHT_AND_STAIR_REGISTERS, ROOF_EDGES_FACADE_FINISH_KERB (roof-edge register for SE / NE / NW / SW / annex / tower, SE facade opening register, external finish register, kerb profile), "
         "TRADES_WET_OPENINGS_FLOORS_COVERAGE (trade matrix, wet rooms, project opening register, profile steel, floor-by-floor, coverage matrix), A22 v5 incremental, rebuilt OWNER_DECISION_QUEUE v2, four new visual QA overlays.",
         "- corrections in the ledger (forward-only): " + "; ".join(f"{e['LEDGER_ID']} {e['MARK']}" for e in led["ENTRIES"][7:]) + ".",
         "", "## NEW QUANTITIES AVAILABLE (partial; per unit and state; never a total)", "",
         "| item | unit | state | value |", "|---|---|---|---|"]
    for c, v in tr["BY_CATEGORY"].items():
        for u, states in v["TOTALS_BY_UNIT_AND_STATE"].items():
            for s_, val in states.items():
                L.append(f"| {c} | {u} | {s_} | {val} |")
    st = dh["STAIR_WALL_GROSS_SUBTOTAL_BY_STOREY_M2"]
    for k, v in st.items():
        L.append(f"| STAIR_WALL gross {k} | m2 | PROVISIONAL_QUANTITY | {v} |")
    L.append(f"| WET_ROOM wall length (GF, E1.4 layer) | lm | PROVISIONAL_QUANTITY | {tw['WET_ROOM_REGISTER']['GF_WALL_LENGTH_LM_PROVISIONAL']} |")
    for x in tw["PROFILE_STEEL_REGISTER"]:
        if x["VALUE"]:
            L.append(f"| {x['PROFILE']} | lm | {x['QUANTITY_STATE']} | {x['VALUE']} |")
    for fid, f in ref["SE_FACADE_FACES"].items():
        if f["NET_M2"]:
            L.append(f"| {fid} net of openings | m2 | GEOMETRIC_REFERENCE_ONLY | {f['NET_M2']} |")
    c = next(x for x in cols if x["COLUMN_ID"].startswith("LOOP-059"))
    L += [f"| LOOP-059 exposed girth (4 faces) | lm | {c['GIRTH_STATE']} | {c['EXPOSED_PLASTERABLE_GIRTH_LM']} |",
          f"| D1 SE solid roof-side: visible-finish basis / executed basis | m2 | PROVISIONAL_QUANTITY | {d1['D1_DUAL_BASIS']['CANDIDATES'][0]['AREA_M2']} / {d1['D1_DUAL_BASIS']['CANDIDATES'][1]['AREA_M2']} |",
          "", "## COVERAGE", "", "| floor | zone | trade | status |", "|---|---|---|---|"]
    for r in tw["COVERAGE_MATRIX"]:
        L.append(f"| {r['FLOOR']} | {r['ZONE']} | {r['TRADE']} | {r['COVERAGE_STATUS']} |")
    L += ["", "A subtotal is not a project total. Floor-by-floor tables: TRADES_WET_OPENINGS_FLOORS_COVERAGE.json FLOOR_BY_FLOOR.",
          "", "## A22 FINDINGS (incremental, conditional IF_BENCHMARK_IS_P7757)", ""]
    for i in gate["A22_INCREMENTAL_V5"]["ITEMS"]:
        L.append(f"- {i['ITEM_ID']}: engineering {i['ENGINEERING']} vs contractor {i['CONTRACTOR']} -> {i['CLASS']} ({', '.join(i['DRIVERS'])}). {i.get('NOTE') or ''}")
    L += ["", "## UNRESOLVED TECHNICAL ITEMS (not owner)", ""]
    for t in gate["TECHNICAL_FOLLOW_UPS_NOT_OWNER"]:
        L.append(f"- {t['ID']}: {t['WHAT']} (check: {t['SOURCE_TO_CHECK']})")
    L += ["", "## OWNER DECISIONS REQUIRED", "", "Withdrawn since PA01: " + "; ".join(gate["WITHDRAWN_FROM_QUEUE"]) + ".", ""]
    for n, d in enumerate(gate["OWNER_DECISION_QUEUE_V2"], 1):
        L += [f"**{n}. {d['DECISION_ID']}** ({d['PRIORITY']})", f"- location: {d['LOCATION']}", f"- card: {d['VISUAL_CARD']}",
              f"- known: {'; '.join(d['AVAILABLE_EVIDENCE'])}", f"- unknown: {d['QUESTION']}", f"- why sources cannot decide: {d['WHY_SOURCE_HIERARCHY_FAILED']}",
              f"- A: {d['OPTION_A']}", f"- B: {d['OPTION_B']}" + (f"; C: {d['OPTION_C_IF_REQUIRED']}" if d.get("OPTION_C_IF_REQUIRED") else ""),
              f"- impact: {d['QUANTITY_IMPACT_IF_KNOWN']}; blocks: {d['BLOCKS_WHAT']}", f"- recommendation: {d.get('TECHNICAL_RECOMMENDATION') or '-'}", ""]
    L += ["## NEXT PHASE AFTER OWNER RESPONSE", "",
          "First-floor room faces from the DWG FF copy (E1.4-style chains), NE / NW facade openings from the authored NW elevation blob and pages 6-7, the annex parapet run, "
          "the stair spine element and flight soffits from A-A, wet-room treatment heights once a finishes schedule exists; A22 incremental on each new face set; contractor basis parallel throughout."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    p = OUT / "OWNER_REPORT_V6.md"
    p.write_text(build(), encoding="utf-8")
    print(json.dumps({"OWNER_REPORT_V6_SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}))
