"""ALSENAN CONTROL-PLANE AUDIT R1 - diagnostic registers (diagnosis only; no production quantity is changed).

Inputs (all in the repository; the build is offline and deterministic):
    tests/alsenan/registers_*                       frozen V3 / V3b / A3 / B1 / B2A1 registers
    evidence/LIVE_EXTRACT.json                      extract_live.py (TS01 semantic state, wet labels, wall ledger,
                                                    column states, beam occurrences, footing / strap rows)
    evidence/ST7757_SCHEDULE_EXTRACT.json           extract_schedules.py (every ST7757 schedule block + loose texts)
    the Python sources themselves                   import graph (legacy CAD reachability) and code anchors

Outputs: registers/<NAME>.json for the ten registers named in REGISTERS, plus registers/INDEX.json (sha256 of each).

    python3 research/alsenan_control_plane_01/build_registers.py

Every register carries SCHEMA, rule and rows. Quantities quoted here are copied from frozen registers; the only
numbers computed here are DIAGNOSTIC magnitudes (labelled DIAGNOSTIC_MAGNITUDE_NOT_A_QUANTITY) used to size a defect -
they are never a release value, a target or a correction.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LAB = ROOT / "research" / "external_engine_lab"
REG = ROOT / "tests" / "alsenan"
OUT = HERE / "registers"
EVID = HERE / "evidence"

REGISTERS = ("STRUCTURAL_SOURCE_COVERAGE_REGISTER", "STRUCTURAL_POPULATION_COVERAGE_REGISTER", "SILENT_DROP_REGISTER",
             "ROOM_SEMANTIC_TRADE_RELEASE_REGISTER", "WALL_LENGTH_CONSERVATION_REGISTER",
             "OPENING_COMPLETENESS_REGISTER", "LEGACY_CAD_REACHABILITY_REGISTER", "DONOR_DELTA_REGISTER",
             "BENCHMARK_CONFIDENCE_REGISTER", "ACCURACY_SCORECARD_DRAFT")
NOT_A_QTY = "DIAGNOSTIC_MAGNITUDE_NOT_A_QUANTITY"
WET_ROOM_EN = re.compile(r"^(BATH|W\.?C|WASH|TOILET|SHOWER)$", re.I)   # English wet-room labels (one per room)
COVER_SOIL_M = 0.07                         # alsenan_v3_structure.COVER["soil"]
ST_SOURCE = "ST7757.dxf (sha256 9f9d1179...) / ST7757.pdf (sha256 74da1523...)"


def _j(p):
    return json.loads(Path(p).read_text())


def _r(v, n=3):
    return None if v is None else round(v, n)


def kgm(d):
    return d * d / 162.0


def load():
    return {
        "live": _j(EVID / "LIVE_EXTRACT.json"),
        "sched": _j(EVID / "ST7757_SCHEDULE_EXTRACT.json"),
        "rooms": _j(REG / "registers_v3/ROOM_REGISTER_V3.json"),
        "finish": _j(REG / "registers_v3/FINISH_REGISTER.json"),
        "rebar": _j(REG / "registers_v3/REBAR_REGISTER.json"),
        "lines": _j(REG / "registers_v3b/BOQ_LINES_V3B.json"),
        "openings_v3b": _j(REG / "registers_v3b/OPENING_REGISTER_V3B.json"),
        "pop": _j(REG / "registers_v3b/REBAR_POPULATION_REGISTER.json"),
        "struct_v3b": _j(REG / "registers_v3b/STRUCTURE_V3B_REGISTER.json"),
        "evidence_a3": _j(REG / "registers_a3/REBAR_EVIDENCE_REGISTER.json"),
        "bench_eval": _j(REG / "registers_v3b_eval/BENCHMARK_EVALUATION_V3B.json"),
        "bench_norm": _j(REG / "registers_b1/BENCHMARK_NORMALISED.json"),
        "bench_qa": _j(REG / "registers_b1/MANUAL_BOQ_QA.json"),
    }


# ============================================================================ E. structural source coverage
def _att(rows, key):
    return {r["attributes"][key]: r for r in rows}


def source_coverage(D) -> dict:
    s = D["sched"]["blocks"]
    defs = {(d["element"], d["type"]): d for d in D["evidence_a3"]["definitions"]}
    remarks = {r["beam"]: r for r in D["sched"]["beam_remarks"]}
    rows = []

    def add(obj, state, **kw):
        rows.append({"object": obj, "state": state, "source_file": kw.pop("file", "ST7757.dxf"), **kw})

    for r in s["FT"]:
        a = r["attributes"]
        boxed = a.get("BOXED", "")
        add(f"FOOTING {a['FO-TY']}", "CONSUMED_PARTIAL" if boxed else "CONSUMED_COMPLETE", page=9,
            title="SCHEDULE OF FOOTINGS", bbox_anchor=r["insert"], dxf_handle=r["handle"], block="FT",
            row_ids=[a["FO-TY"]], parser="alsenan_phase_a.footing_schedule (PDF text)",
            consumer="alsenan_phase_a3._rebar -> alsenan_v3_structure.footing_rebar",
            fields_read=["W", "H", "DEPHT", "SH-B", "SH-D", "LO-B", "LO-D"],
            fields_unread=(["BOXED"] if boxed else []), value_unread=({"BOXED": boxed} if boxed else {}),
            reason=("BOXED column (boxed / starter bar count, e.g. '3+4') never parsed; no BLOCKED row is written "
                    "either - SILENT" if boxed else "all bar fields consumed"),
            provenance="DXF ATTRIB values", affected_population=f"footings of type {a['FO-TY']}",
            defect=("SD-08" if boxed else None))
    for r in s["FTB"]:
        a = r["attributes"]
        t = a["FO-TY"]
        d = defs.get(("FOOTING", t), {})
        if t == "FF":
            st, why, dft = ("CONSUMED_PARTIAL", "the merged two-layer cell '6 9 Ø Ø 14/m 14/m' is read as one string; "
                            "bars={} and definition BLOCKED, so no rebar row and no BLOCKED population row is emitted "
                            "for the one FF (lift footing) occurrence", "D3")
        else:
            st, why, dft = ("CONSUMED_PARTIAL", "TOP layer read as the bottom mesh with per_m ignored (count used as an "
                            "absolute bar count); the BOT layer is routed to 'boxed' and emitted as BLOCKED 'boxed bar "
                            "shape not dimensioned'", "D2")
        add(f"FOOTING {t}", st, page=9, title="SCHEDULE OF FOOTINGS (two-layer rows)", bbox_anchor=r["insert"],
            dxf_handle=r["handle"], block="FTB", row_ids=[t], parser="alsenan_phase_a.footing_schedule (PDF text)",
            consumer="alsenan_phase_a3._rebar -> alsenan_v3_structure.footing_rebar",
            fields_read=["W", "H", "DEPHT", "SH-T-B", "SH-T-D", "LO-T-B", "LO-T-D"] if t != "FF" else ["W", "H", "DEPHT"],
            fields_misread=(["SH-T-D per_m", "LO-T-D per_m", "SH-B-* / LO-B-* (BOT layer -> 'boxed')"] if t != "FF"
                            else ["SH-T-*", "LO-T-*", "SH-B-*", "LO-B-*"]),
            fields_unread=["BOXED-T", "BOXED-B"], schedule_values={k: a[k] for k in a if k != "FO-TY"},
            a3_definition={"bars": d.get("bars"), "boxed": d.get("boxed"), "definition": d.get("definition")},
            reason=why, provenance="DXF ATTRIB values; PDF p.9 shows TOP / BOT layer labels",
            affected_population=f"footings of type {t}", defect=dft)
    rows.append({"object": "FOOTING REMARKS column", "state": "UNREAD", "source_file": "ST7757.pdf", "page": 9,
                 "title": "SCHEDULE OF FOOTINGS - REMARKS", "row_ids": ["FF"],
                 "value_unread": {"FF": "rHu}]M lwu}}] (legacy Arabic font; = 'lift footing')"},
                 "parser": None, "consumer": None, "fields_unread": ["REMARKS"],
                 "reason": "REMARKS never parsed; FF is the lift footing (p.14 lift detail)", "provenance": "PDF text",
                 "affected_population": "FF (1 occurrence)", "defect": "D3"})
    sbt = defaultdict(list)
    for r in s["SBT"]:
        sbt[r["attributes"]["BEAM"]].append(r)
    for t, rs in sbt.items():
        a = rs[0]["attributes"]
        el = "STRAP" if t.startswith("SB") else "BEAM"
        d = defs.get((el, t))
        if len(rs) > 1:
            st, why, dft = "SOURCE_CONFLICT", (
                f"{len(rs)} schedule rows carry the name {t} with different sections / bars "
                f"({'; '.join(x['attributes']['W'] + 'x' + x['attributes']['H'] for x in rs)}); the A3 parser keeps "
                f"one (W={d['fields'] if d else None}) without recording the conflict"), "SD-12"
        elif el == "STRAP":
            st, why, dft = "CONSUMED_PARTIAL", ("definition parsed (element=STRAP) but alsenan_v3_structure.beam_rebar "
                                                "filters element=='BEAM' - no rebar row, no BLOCKED row"), "D4"
        elif t in remarks:
            st, why, dft = "CONSUMED_PARTIAL", (f"REMARKS side bars '{remarks[t]['text']}' captured as a string by "
                                                f"_simple_beam_library but never consumed; side bars are emitted as a "
                                                f"BLOCKED / provisional 2..4 range instead"), "SD-11"
        else:
            st, why, dft = "CONSUMED_COMPLETE", "BOT / TOP / stirrups consumed", None
        add(f"{el} {t}", st, page=10, title="SCHEDULE OF SIMPLE BEAMS", bbox_anchor=rs[0]["insert"],
            dxf_handle=[x["handle"] for x in rs], block="SBT", row_ids=[t],
            parser="alsenan_phase_a3._simple_beam_library (CAD table)",
            consumer="alsenan_v3_structure.beam_rebar" + (" (filtered out)" if el == "STRAP" else ""),
            fields_read=["W", "H", "BOT-B", "BOT-D", "TOP-B", "TOP-D", "STI-B", "D"],
            fields_unread=(["REMARKS"] if t in remarks else []),
            value_unread=({"REMARKS": remarks[t]["text"]} if t in remarks else {}),
            schedule_values=[x["attributes"] for x in rs], reason=why, provenance="DXF ATTRIB + S-TEXT.SCH TEXT",
            affected_population=f"{el.lower()} occurrences of type {t}", defect=dft)
    for blk in ("C-BEAM2", "C-BEAM3"):
        for r in s[blk]:
            a = r["attributes"]
            bars = {k: v for k, v in a.items() if re.match(r"(BOT|MID|STR)", k) and v}
            add(f"CONTINUOUS BEAM {a['BEAM-NAME']}", "CONSUMED_PARTIAL", page=11 if blk == "C-BEAM2" else 12,
                title=f"CONTINUES BEAMS ({blk[-1]} SPAN)", bbox_anchor=r["insert"], dxf_handle=r["handle"], block=blk,
                row_ids=[a["BEAM-NAME"]], parser="alsenan_phase_a3.CB_TRANSCRIPTION (hand-read from the PDF; "
                                                 "'text drawn as vector glyphs')",
                consumer="alsenan_phase_a3._beams (concrete BLOCKED) ; rebar: none",
                fields_read=["W", "H", "L1-M", "L2-M"] + (["L3-M"] if blk == "C-BEAM3" else []),
                fields_unread=sorted(bars), fields_not_relevant=[k for k in a if k.startswith("T/M")],
                schedule_values=a,
                reason="every reinforcement attribute is present as a DXF ATTRIB but was never read; T/M-n are "
                       "design loads (t/m), not bars", provenance="DXF ATTRIB values",
                affected_population=f"CB occurrences of type {a['BEAM-NAME']}", defect="D1")
    for r in s["CGT"]:
        a = r["attributes"]
        add(f"COLUMN {a['COL-T']}", "CONSUMED_COMPLETE", page=9, title="SCHEDULE OF COLUMNS",
            bbox_anchor=r["insert"], dxf_handle=r["handle"], block="CGT", row_ids=[a["COL-T"]],
            parser="alsenan_phase_a3 column library", consumer="alsenan_v3_structure.column_rebar",
            fields_read=[k for k in a if k not in ("COL-T", "LOAD")], fields_not_relevant=["LOAD"],
            reason="sections and bars per storey band consumed (matches p.9)", provenance="DXF ATTRIB values",
            affected_population=f"column occurrences of type {a['COL-T']}", defect=None)
    loose = Counter((t["layer"], t["text"]) for t in D["sched"]["loose_texts"])
    for layer, text, st, why, page, dft in (
            ("S-TEXT-SLAB", "P.C 20x70", "UNREAD", "planted column (on slab) - no consumer; no concrete, no rebar, "
             "no BLOCKED row", 4, "SD-13"),
            ("S-TEXT-SLAB", "P.C 20x50", "UNREAD", "planted column x2 - no consumer", 4, "SD-13"),
            ("S-TEXT-SLAB", "10%%C16", "UNREAD", "planted-column bars (P.C 20x70)", 4, "SD-13"),
            ("S-TEXT-SLAB", "8%%C16", "UNREAD", "planted-column bars (P.C 20x50)", 4, "SD-13"),
            ("S-TEXT-SLAB", "(T&B)", "UNREAD", "top-and-bottom qualifier on 2F slab bars - the slab binder reads the "
             "bar text, not the qualifier (layer count unproved)", 6, "SD-14"),
            ("S-TEXT-SLAB", "11%%C18", "UNREAD", "section B-B bars (p.5) - not bound to any member", 5, "SD-15"),
            ("S-TEXT-SLAB", "3%%C18", "UNREAD", "section B-B bars (p.5)", 5, "SD-15"),
            ("S-TEXT.SCH", "2%%C12/30cm", "CONSUMED_PARTIAL", "simple-beam REMARKS side bars (see BEAM rows)", 10,
             "SD-11"),
            ("S-TEXT.SCH", "2%%C16/20cm", "CONSUMED_PARTIAL", "simple-beam REMARKS side bars", 10, "SD-11"),
            ("S-TEXT.SCH", "2%%C14/20cm", "CONSUMED_PARTIAL", "simple-beam REMARKS side bars", 10, "SD-11"),
            ("S-TEXT.SCH", "2%%C12", "UNREAD", "continuous-beam side bars (CB schedules, split text '2Ø12' + "
             "'30cm')", 11, "D1"),
            ("S-TEXT.D", "*  ST. OF COLUMN- 6%%C8/m", "CONSUMED_COMPLETE", "column ties 6Ø8/m", 9, None)):
        add(f"TEXT '{text}'", st, layer=layer, occurrences=loose.get((layer, text), 0), page=page,
            title="loose drawing text", parser=None if st == "UNREAD" else "see reason",
            consumer=None if st == "UNREAD" else "see reason", reason=why, provenance="DXF TEXT",
            affected_population=why, defect=dft)
    for obj, page, st, why, dft in (
            ("p.3 slab on grade 5Ø10/m E.W., T = 10 cm", 3, "CONSUMED_COMPLETE",
             "ground slab mesh (alsenan_v3_structure ground)", None),
            ("p.7 pool + dome details", 7, "CONSUMED_PARTIAL", "V3b pool / dome populations (DERIVED + provisional)",
             None),
            ("p.8 RECOMMENDATIONS notes 1-24 (raster image)", 8, "CONSUMED_PARTIAL",
             "note 21 (side bars by width) read by hand; the rest unread - raster", "SD-16"),
            ("p.13 lintel detail + schedule", 13, "CONSUMED_COMPLETE", "lintel bars by width", None),
            ("p.13 ground beam sections", 13, "CONSUMED_PARTIAL", "ground-beam bars consumed; hooks BLOCKED_DETAILING",
             None),
            ("p.14 lift with isolated footing", 14, "UNREAD", "lift pit / FF footing detail - no consumer", "D3"),
            ("p.14 boundary wall, parapets", 14, "CONSUMED_PARTIAL", "V3b BOUNDARY_WALL provisional", None),
            ("p.15 temperature reinforcement schedule", 15, "UNREAD", "no consumer; slab top steel population unknown",
             "SD-16"),
            ("p.15 twisted column / beam in casement / slab on beams", 15, "NOT_RELEVANT",
             "typical details; no tagged occurrence found on the plans (unproved - see owner question Q-S5)", None),
            ("p.15 planted column detail", 15, "UNREAD", "planted columns P.C on p.4 have no consumer", "SD-13"),
            ("p.16 stair beam + stair steel layout (8Ø16/m, 6Ø14/m, Ø12/20 ...)", 16, "UNREAD",
             "V3b STAIRS rebar BLOCKED 'no callout bound' although the typical layout is printed", "SD-17"),
            ("p.16 opening in beam, ribs / torsion", 16, "NOT_RELEVANT", "typical details", None)):
        rows.append({"object": obj, "state": st, "source_file": "ST7757.pdf", "page": page, "title": obj,
                     "parser": None if st in ("UNREAD", "NOT_RELEVANT") else "manual / V3b lane",
                     "consumer": None if st in ("UNREAD", "NOT_RELEVANT") else "see reason", "reason": why,
                     "provenance": "PDF page (vector or raster)", "affected_population": why, "defect": dft})
    c = Counter(r["state"] for r in rows)
    return {"SCHEMA": "URBAN_ALSENAN_STRUCTURAL_SOURCE_COVERAGE_V1", "source": ST_SOURCE,
            "states": ["CONSUMED_COMPLETE", "CONSUMED_PARTIAL", "UNREAD", "NOT_RELEVANT", "SOURCE_CONFLICT"],
            "counts": dict(sorted(c.items())), "rows": rows,
            "rule": "every schedule block, every reinforcement text and every structural PDF page has exactly one "
                    "state; UNREAD / CONSUMED_PARTIAL / SOURCE_CONFLICT name the defect that leaves it so"}


# ============================================================================ F. structural population coverage
def population_coverage(D) -> dict:
    L = D["live"]
    defs = {(d["element"], d["type"]): d for d in D["evidence_a3"]["definitions"]}
    ft = {r["attributes"]["FO-TY"]: r["attributes"] for r in D["sched"]["blocks"]["FT"]}
    ftb = {r["attributes"]["FO-TY"]: r["attributes"] for r in D["sched"]["blocks"]["FTB"]}
    cb = {r["attributes"]["BEAM-NAME"]: r["attributes"] for b in ("C-BEAM2", "C-BEAM3") for r in D["sched"]["blocks"][b]}
    remarks = {r["beam"]: r["text"] for r in D["sched"]["beam_remarks"]}
    fr = defaultdict(lambda: {"kg": 0.0, "bars": 0, "blocked": 0})
    for b in D["rebar"]["footings"]:
        t, n = b["ref"].split()[0], b["ref"].split()[1]
        k = fr[(t, n)]
        if b.get("status") == "BLOCKED":
            k["blocked"] += 1
        else:
            k["kg"] += b.get("net_design_weight_kg") or 0.0
            k["bars"] += b.get("count") or 0
    rows = []
    for i, f in enumerate(L["footings"]):
        t, ref = f["type"], f"#{i + 1}"
        em = fr.get((t, ref), {"kg": 0.0, "bars": 0, "blocked": 0})
        row = {"population": "FOOTING", "occurrence": f"{t} {ref}", "mark": f["mark"], "type": t,
               "concrete_state": f["status"], "rebar_emitted_kg": _r(em["kg"]), "rebar_emitted_bars": em["bars"],
               "blocked_records": em["blocked"]}
        if not str(f["status"]).startswith("COMPUTED"):
            row.update(state="REBAR_BLOCKED", why="footing concrete BLOCKED (F / F10 source conflict); V3a emits "
                       "nothing (structure.py:278, silent) - V3b FOOTING_F_F10 adds a labelled range", defect="SD-01")
        elif t == "FF":
            row.update(state="REBAR_BLOCKED", why="definition bars={} (merged two-layer cell); NO rebar row and NO "
                       "BLOCKED row - silent", defect="D3", silent=True)
        elif t in ftb:
            a = ftb[t]
            L_, W_ = f["L_m"], f["W_m"]
            mag = 0.0
            for lay in ("T", "B"):
                for side, span, across in (("SH", W_, L_), ("LO", L_, W_)):
                    pm, dia = float(a[f"{side}-{lay}-B"]), int(a[f"{side}-{lay}-D"].split("/")[0])
                    n = math.ceil(pm * (across - 2 * COVER_SOIL_M)) + 1
                    mag += n * (span - 2 * COVER_SOIL_M) * kgm(dia)
            row.update(state="REBAR_PARTIAL", why="TOP layer emitted with the per-metre count used as an absolute "
                       "count; BOT layer BLOCKED as 'boxed bars'", defect="D2",
                       schedule_layers={"TOP": f"{a['SH-T-B']}Ø{a['SH-T-D']} / {a['LO-T-B']}Ø{a['LO-T-D']}",
                                        "BOT": f"{a['SH-B-B']}Ø{a['SH-B-D']} / {a['LO-B-B']}Ø{a['LO-B-D']}"},
                       straight_mesh_magnitude_kg={"value": _r(mag, 1), "label": NOT_A_QTY,
                                                   "basis": "per_m x (side - 2 x 0.07) + 1 bars per direction per "
                                                            "layer, straight length side - 2 x 0.07, D^2/162; no "
                                                            "hooks, no laps"})
        elif ft.get(t, {}).get("BOXED"):
            row.update(state="REBAR_PARTIAL", why=f"mesh emitted; BOXED '{ft[t]['BOXED']}' unread and not flagged",
                       defect="SD-08", silent=True)
        else:
            row.update(state="REBAR_COMPLETE", why="mesh emitted (hooks / laps not detailed for straight bars)",
                       defect=None)
        rows.append(row)
    for c in L["columns"]:
        st, kg = c["state"], c["rebar_net_kg"] or 0.0
        row = {"population": "COLUMN", "occurrence": f"{c['floor']} {c['type']} {c['tag']}", "type": c["type"],
               "concrete_state": st, "concrete_m3": c["concrete_m3"], "rebar_emitted_kg": kg}
        if st == "NOT_IN_STOREY":
            row.update(state="NOT_REQUIRED", why="column type stops below this storey", defect=None)
        elif c["concrete_m3"] is None and kg > 0:
            row.update(state="REBAR_WITHOUT_CONCRETE", why="column_rebar skips only when the definition or B_cm is "
                       "missing; occurrence state is ignored, so rebar is priced for an occurrence whose concrete "
                       "is blocked / not drawn", defect="D5")
        elif kg > 0:
            row.update(state="REBAR_COMPLETE", why="verticals + ties emitted (tie hooks BLOCKED)", defect=None)
        else:
            row.update(state="REBAR_BLOCKED", why="no definition / no section", defect=None)
        rows.append(row)
    br = defaultdict(float)
    for b in D["rebar"]["beams"]:
        p = b["ref"].split()
        br[(p[0], p[1], p[2])] += b.get("straight_weight_kg") or 0.0
    residue = {(b["floor"], b["type"], b["id"].split("|")[1]): b for b in D["struct_v3b"]["residue"]["beams"]}
    for o in L["beam_occurrences"]:
        t, key = o["type"], (o["floor"], o["type"], o["tag"])
        kg = br.get(key, 0.0)
        res = residue.get(key)
        row = {"population": "BEAM" if not t.startswith("CB") else "CONTINUOUS_BEAM",
               "occurrence": f"{o['floor']} {t} {o['tag']}", "type": t, "occurrence_state": o["state"],
               "B_cm": o["B_cm"], "D_cm": o["D_cm"], "rebar_emitted_straight_kg": _r(kg),
               "v3b_residue_commercial": (res or {}).get("commercial", {}) and res["commercial"]["class"]}
        if t.startswith("CB"):
            a = cb.get(t, {})
            row.update(state="REBAR_BLOCKED", silent=o["state"] == "MEASURED", defect="D1",
                       why=("MEASURED continuous beam: no BEAM definition exists for CB types (the schedule "
                            "attributes were never read) - beam_rebar skips it at structure.py:326 without a record"
                            if o["state"] == "MEASURED" else
                            f"{o['state']}: V3a skips; V3b residue {'concrete only' if res else 'none'} - rebar only "
                            f"via BEAM_RESIDUE budget when a per-type kg/m exists (none for CB)"),
                       schedule_bars={k: v for k, v in a.items() if re.match(r"(BOT|MID|STR)", k) and v})
        elif o["state"] != "MEASURED":
            row.update(state="REBAR_PARTIAL" if res and res.get("commercial") else "REBAR_BLOCKED",
                       why=f"{o['state']}: V3a skips (structure.py:326); V3b residue budget by type kg/m",
                       defect="SD-03")
        elif (o["D_cm"] or 0) > 60:
            row.update(state="REBAR_PARTIAL", why=f"main bars + stirrups emitted; side bars BLOCKED in V3a and a "
                       f"provisional 2..4 range in V3b although the schedule prints '{remarks.get(t)}'",
                       defect="SD-11")
        else:
            row.update(state="REBAR_COMPLETE", why="main bars + stirrups emitted (anchorage BLOCKED_DETAILING)",
                       defect=None)
        rows.append(row)
    for s_ in L["straps"]:
        d = defs.get(("STRAP", s_["type"]))
        rows.append({"population": "STRAP_BEAM", "occurrence": f"FOUNDATION {s_['type']} {s_['mark']}",
                     "type": s_["type"], "concrete_state": s_["status"], "rebar_emitted_kg": 0.0,
                     "state": "REBAR_BLOCKED", "silent": True, "defect": "D4",
                     "why": "definition exists (element=STRAP) but beam_rebar filters element=='BEAM'; no record",
                     "schedule_bars": d and d["fields"]})
    pops = {r["population"]: r for r in D["pop"]["rows"]}
    for p in ("SLAB", "GROUND", "GROUND_SLAB", "LINTELS", "DOME", "POOL", "BOUNDARY_WALL", "GROUND_BEAM_EXT",
              "COLUMN_STARTERS", "STAIRS"):
        r = pops.get(p)
        if r:
            rows.append({"population": p, "occurrence": "(population row - V3b)", "state":
                         "REBAR_BLOCKED" if r["blocked"] and not r["net_kg"] else
                         ("REBAR_PARTIAL" if set(r["classes"]) - {"DERIVED"} else "REBAR_COMPLETE"),
                         "v3b_classes": r["classes"], "net_kg": r["net_kg"], "technical_kg": r["technical_kg"],
                         "defect": "SD-17" if p == "STAIRS" else None,
                         "why": "population-level row from REBAR_POPULATION_REGISTER (V3b)"})
    g = D["live"]["ground"]
    z1 = next(z for z in g["v3a_zones"] if z["id"] == "ZONE-1")
    ground = {"defect": "D6", "code": "research/external_engine_lab/alsenan_v3_structure.py:108 "
                                      "outer = min(hit, key=lambda p: p.area)",
              "v3a_zone_1": {"outer_m2": _r(z1["outer_area_m2"]), "slab_m2": _r(z1["slab_area_m2"]),
                             "mesh_text": z1["mesh_text"]},
              "v3b_zones": g["zones"], "footprints": g["footprints"],
              "footprint_total_m2": _r(sum(f["area_m2"] for f in g["footprints"])),
              "finding": "ZONE-1's label lies inside several closed cells and binds to the smallest (outer "
                         f"{_r(z1['outer_area_m2'])} m2) inside footprint FP-1 ({g['footprints'][0]['area_m2']} m2); "
                         "the rest of FP-1 carries no ground-slab zone and no BLOCKED row. Whether that remainder is slab-on-grade "
                         "is UNRESOLVED (engineer question Q-S4); the defect is the min-area binding rule, not a "
                         "missing quantity"}
    by = defaultdict(Counter)
    for r in rows:
        by[r["population"]][r["state"]] += 1
    d5 = [r for r in rows if r.get("defect") == "D5"]
    return {"SCHEMA": "URBAN_ALSENAN_STRUCTURAL_POPULATION_COVERAGE_V1",
            "states": ["REBAR_COMPLETE", "REBAR_PARTIAL", "REBAR_BLOCKED", "NOT_REQUIRED", "REBAR_WITHOUT_CONCRETE"],
            "counts": {k: dict(sorted(v.items())) for k, v in sorted(by.items())},
            "silent_occurrences": sum(1 for r in rows if r.get("silent")),
            "d5_rebar_without_concrete": {"occurrences": len(d5), "kg": _r(sum(r["rebar_emitted_kg"] for r in d5), 1),
                                          "by_state": {k: _r(sum(r["rebar_emitted_kg"] for r in d5
                                                                 if r["concrete_state"] == k), 1)
                                                       for k in sorted({r["concrete_state"] for r in d5})}},
            "ground_zone_binding": ground, "rows": rows,
            "rule": "every concrete occurrence has one rebar state; REBAR_WITHOUT_CONCRETE and silent=True are "
                    "control-plane defects, not quantities"}


# ============================================================================ H. silent drops
SILENT = [
    # id, file, line, anchor, condition, population, current, correct, severity, test
    ("SD-01", "alsenan_v3_structure.py", 277, 'if not str(f.get("status", "")).startswith("COMPUTED") or f["type"] not in defs:',
     "footing not COMPUTED or type has no definition", "F, F10 (BLOCKED); any unparsed type",
     "skipped - no rebar row, no BLOCKED row", "emit REBAR_BLOCKED row naming the concrete blocker", "MEDIUM",
     "test_sd01_footing_skip_is_silent"),
    ("SD-02", "alsenan_v3_structure.py", 300, 'if d is None or r.get("B_cm") is None:',
     "column type without definition / section", "column occurrences", "skipped silently; occurrence STATE is "
     "never consulted (D5: rebar for NOT_DRAWN / BLOCKED occurrences)",
     "rebar state must follow the occurrence state; BLOCKED concrete => REBAR_BLOCKED", "HIGH",
     "test_d5_column_rebar_ignores_occurrence_state"),
    ("SD-03", "alsenan_v3_structure.py", 325, 'if d is None or o["state"] != "MEASURED":',
     "beam type without BEAM definition, or occurrence not MEASURED", "all CB (13 types), all non-MEASURED beams",
     "skipped - no row", "REBAR_BLOCKED row with reason; CB definitions from the DXF attributes", "HIGH",
     "test_d1_cb_measured_occurrence_emits_nothing"),
    ("SD-04", "alsenan_v3_structure.py", 329, "if not Ls or not Lc:", "beam lengths missing", "MEASURED beams "
     "with a missing support / clear length", "skipped - no row", "REBAR_BLOCKED row", "MEDIUM",
     "test_sd04_beam_without_length_is_silent"),
    ("SD-05", "alsenan_v3_structure.py", 379, 'if o.get("width_m") is None:', "opening without width",
     "openings", "no lintel, no row", "LINTEL_BLOCKED row", "LOW", "test_sd_code_anchors_hold"),
    ("SD-06", "alsenan_v3_structure.py", 401, 'if l.get("status") != "COMPUTED":', "lintel not COMPUTED",
     "lintels", "no rebar, no row", "REBAR_BLOCKED row", "LOW", "test_sd_code_anchors_hold"),
    ("SD-07", "alsenan_v3_structure.py", 431, 'if b["state"] != "WALL_BAND_ESTABLISHED":',
     "wall band AMBIGUOUS", "46.63 m of ambiguous wall-band centreline", "dropped from blockwork with no row",
     "BLOCKWORK_BLOCKED (or PARTIAL lower bound) row carrying the length", "HIGH",
     "test_i_ambiguous_band_length_not_in_blockwork"),
    ("SD-08", "alsenan_phase_a.py", None, "BOXED", "footing BOXED column", "F, F2-F7, F9-F11, F15",
     "never parsed, never flagged", "parse; REBAR_BLOCKED (shape) row per occurrence until dimensioned", "MEDIUM",
     "test_sd08_boxed_column_unread"),
    ("SD-09", "alsenan_v3_layers.py", 391, 'if r["class"] not in ("ROOM", "OPEN_PLAN_ZONE", "UNNAMED_ROOM") or r["room_class"] in ("SHAFT", "ROOF", "EXTERNAL"):',
     "room class SHAFT / ROOF / EXTERNAL or strip", "shafts, opening strips", "no finish row", "explicit "
     "NOT_IN_SCOPE row (scope decision recorded)", "LOW", "test_sd_code_anchors_hold"),
    ("SD-10", "alsenan_v3_registers.py", 293, 'if r["room_class"] not in ("WET", "SERVICE"):',
     "room classed DRY / UNKNOWN", "wet labels inside DRY zones (GF-Z04 Wash, GF-Z06 Wash)",
     "no wall tile / WP row - the wet label is lost", "zone with a wet label and unresolved semantics => "
     "TILE_WP_BLOCKED row", "HIGH", "test_j_wet_label_in_dry_zone_gets_no_tile"),
    ("SD-11", "alsenan_v3_structure.py", 344, 'if o["D_cm"] and o["D_cm"] > 60:', "beam deeper than 60 cm",
     "B7-B29 occurrences", "side bars BLOCKED ('width-to-count mapping not printed') though REMARKS prints them",
     "consume REMARKS (2Ø12/30cm etc.)", "MEDIUM", "test_sd11_side_bar_remarks_unused"),
    ("SD-12", "alsenan_phase_a3.py", None, "_simple_beam_library", "duplicate schedule name", "SB2 (two rows "
     "80x50 and 100x50)", "one row kept, conflict not recorded", "SOURCE_CONFLICT row; drawn width selects",
     "MEDIUM", "test_sd12_sb2_duplicate_rows"),
    ("SD-13", None, None, None, "planted column texts", "P.C 20x70, 2 x P.C 20x50", "no consumer",
     "UNREAD row in coverage; owner question", "MEDIUM", "test_e_every_schedule_block_has_a_state"),
    ("SD-14", None, None, None, "(T&B) qualifier", "2F slab bars x4", "qualifier ignored", "layer count read",
     "LOW", "test_e_every_schedule_block_has_a_state"),
    ("SD-15", None, None, None, "section B-B bars", "p.5 11Ø18 / 3Ø18", "unbound", "bind to member or BLOCKED",
     "LOW", "test_e_every_schedule_block_has_a_state"),
    ("SD-16", None, None, None, "p.8 notes (raster), p.15 temperature steel", "slab top steel / general notes",
     "unread", "OCR or owner transcription; BLOCKED rows", "MEDIUM", "test_e_every_schedule_block_has_a_state"),
    ("SD-17", "alsenan_v3b_struct.py", None, "no callout bound", "stair rebar", "stairs",
     "BLOCKED although p.16 prints a typical stair steel layout", "bind the typical layout as SOURCE_RULE "
     "(provisional until owner confirms)", "MEDIUM", "test_sd_code_anchors_hold"),
    ("SD-18", "alsenan_v3b_rebar.py", 166, 'if not c or not b.get("length_m"):', "residue beam without "
     "commercial / length", "V3b residue beams", "skipped", "REBAR_BLOCKED row", "LOW", "test_sd_code_anchors_hold"),
    ("SD-19", "alsenan_v3b_rebar.py", 169, "if k is None:", "residue beam type without measured kg/m "
     "(every CB)", "CB residue occurrences", "skipped - CB never gets rebar even as budget", "REBAR_BLOCKED row",
     "MEDIUM", "test_sd_code_anchors_hold"),
    ("SD-20", "alsenan_v3b_struct.py", 329, 'if r.get("volume_m3") is not None or r["state"] in ("NOT_IN_STOREY", "NOT_DRAWN_ON_STOREY_SHEET"):',
     "column NOT_DRAWN_ON_STOREY_SHEET", "17 occurrences", "no concrete (but rebar is emitted: D5)",
     "consistent state across concrete and rebar", "HIGH", "test_d5_column_rebar_ignores_occurrence_state"),
    ("SD-21", "alsenan_v3b_finish.py", 287, "if not H:", "floor without wall height", "lintel/reveal rows",
     "skipped", "BLOCKED row", "LOW", "test_sd_code_anchors_hold"),
    ("SD-22", "alsenan_v3_structure.py", 108, "outer = min(hit, key=lambda p: p.area)",
     "ground zone label inside several cells", "ground zones", "binds to the SMALLEST containing cell (D6)",
     "bind to the cell whose boundary is the zone outline; ambiguity => BLOCKED", "HIGH",
     "test_d6_ground_zone_binds_smallest_cell"),
    ("SD-23", None, None, None, "wet label outside every room site", "1F W.C / مرحاض, 1F BATH / حمام",
     "label silently unused (NO_SITE)", "WET_LABEL_UNPLACED row + owner question", "HIGH",
     "test_j_unplaced_wet_labels"),
]


def silent_drops(D) -> dict:
    rows = []
    for sid, f, line, anchor, cond, pop, cur, corr, sev, test in SILENT:
        loc = None
        if f and line:
            loc = f"research/external_engine_lab/{f}:{line}"
        elif f:
            loc = f"research/external_engine_lab/{f}"
        rows.append({"id": sid, "code_location": loc, "anchor": anchor, "condition": cond,
                     "input_population": pop, "current_behaviour": cur, "correct_future_behaviour": corr,
                     "severity": sev, "test_required": test})
    return {"SCHEMA": "URBAN_ALSENAN_SILENT_DROP_V1", "rows": rows,
            "rule": "a silent drop is a code path that removes an input object from every output without writing a "
                    "BLOCKED / NOT_IN_SCOPE row; anchors are verified against the source by the tests",
            "continue_sites_scanned": "136 `continue` statements in the active Alsenan modules were read; the rows "
                                      "above are the ones that drop a quantity-bearing object"}


# ============================================================================ B/C/J. room semantic / trade / release
def room_release(D) -> dict:
    sem = {s["room"]: s for s in D["live"]["semantic"]}
    fin = {r["room"]: r for r in D["finish"]["rows"]}
    lines = defaultdict(list)
    for ln in D["lines"]["lines"]:
        if ln.get("trace"):
            lines[ln["trace"]].append(ln)
    wet = defaultdict(list)
    for w in D["live"]["wet_labels"]:
        wet[w["room"]].append(w["text"])
    rows = []
    for r in D["rooms"]["rows"]:
        s, f = sem.get(r["id"], {}), fin.get(r["id"], {})
        ls = {ln["code"].rsplit("-" + r["id"], 1)[0]: ln for ln in lines[r["id"]]}

        def rel(code):
            ln = ls.get(code)
            if not ln:
                return None
            t, c = ln["release"]["technical"], ln["release"]["commercial"]
            return {"line_id": ln.get("line_id"), "qty": ln["qty"], "v3a_status": ln["status"],
                    "technical_class": t["class"], "in_total": t["in_total"], "commercial_class": c["class"],
                    "procurement_eligible": c.get("procurement_eligible"), "confidence": c.get("confidence")}

        labels = [n.strip() for n in r["name_en"].split(" / ") if n.strip()]
        wet_in = sorted(set(wet.get(r["id"], [])))
        wet_rooms_in = sorted(t for t in wet_in if WET_ROOM_EN.match(t))
        flags = []
        if any(k in str(s.get("ts01_semantic_state")) for k in ("UNRESOLVED", "BOUNDARY_MISSING")):
            flags.append("TS01_UNRESOLVED_BUT_RELEASED")
        if r["status"] != "COMPUTED" and (rel("F-FL") or {}).get("in_total"):
            flags.append("REVIEW_ROOM_FLOOR_IN_TOTAL")
        if r["room_class"] == "DRY" and wet_rooms_in:
            flags.append("WET_LABEL_IN_DRY_ZONE")
        if len(labels) >= 2 and r["room_class"] == "DRY":
            flags.append("MULTI_NAME_DRY_WINS")
        rows.append({
            "room": r["id"], "floor": r["floor"], "physical_space": r["site"], "physical_class": r["class"],
            "physical_status": r["physical_status"], "area_m2": _r(r["area_m2"]),
            "semantic_zone_state_ts01": s.get("ts01_semantic_state"),
            "semantic_zones": [z["label_values"] for z in s.get("zones", [])],
            "name_en": r["name_en"], "name_ar": r["name_ar"], "alsenan_room_class": r["room_class"],
            "wet_labels_inside": wet_in, "wet_room_labels_inside_en": wet_rooms_in, "room_status_v3": r["status"],
            "trade_region": {"floor_m2": f.get("floor_area_m2"), "floor_material": f.get("floor_material"),
                             "skirting_m": f.get("skirting_m"), "ceiling_m2": f.get("ceiling_area_m2"),
                             "wall_tile_gross_m2": f.get("wall_tile_gross_m2"), "wall_state": f.get("wall_state")},
            "release": {"floor": rel("F-FL"), "skirting": rel("F-SK"), "ceiling": rel("CE"),
                        "plaster_seq_P-SP": rel("P-SP"), "paint_P-PA": rel("P-PA"), "wall_tile_T-WT": rel("T-WT"),
                        "wp_floor": rel("T-WP-FLOOR")},
            "flags": flags})
    tot = defaultdict(float)
    for x in rows:
        a = x["trade_region"]["floor_m2"] or 0.0
        tot["floor_total"] += a
        tot["floor_" + ("clean_COMPUTED" if x["room_status_v3"] == "COMPUTED" else "COMPUTED_REVIEW")] += a
        if x["room_status_v3"] != "COMPUTED":
            tot["review_" + x["alsenan_room_class"]] += a
    unplaced = [w for w in D["live"]["wet_labels"] if w["located"] != "IN_ROOM_ROW"]
    lost = [{"floor": x["floor"], "label": t, "where": x["room"], "why": "WET_LABEL_IN_DRY_ZONE"}
            for x in rows if "WET_LABEL_IN_DRY_ZONE" in x["flags"] for t in x["wet_room_labels_inside_en"]]
    lost += [{"floor": w["floor"], "label": w["text"], "where": "NO_SITE", "xy": w["xy"], "why": "WET_LABEL_UNPLACED"}
             for w in unplaced if WET_ROOM_EN.match(w["text"])]
    return {"SCHEMA": "URBAN_ALSENAN_ROOM_SEMANTIC_TRADE_RELEASE_V1", "rows": rows,
            "floor_decomposition_m2": {k: _r(v) for k, v in sorted(tot.items())},
            "wet_labels_not_in_a_room_row": unplaced, "wet_rooms_lost": lost,
            "rule": "physical space (site) != semantic zone (TS01) != trade region (finish row) != release line; "
                    "each column is read from its own register - a mismatch is a flag, never a correction"}


# ============================================================================ I. wall length conservation
def wall_conservation(D) -> dict:
    rows, tot = [], defaultdict(float)
    for fl, w in D["live"]["wall_ledger"].items():
        est = {int(k): v for k, v in w["established_centreline_m_by_width_mm"].items()}
        amb = {int(k): v for k, v in w["ambiguous_centreline_m_by_width_mm"].items()}
        bw = w["blockwork_rows_m"]
        est_x920 = sum(v for k, v in est.items() if k != 920)
        bw_in = sum(v for k, v in bw.items() if not k.endswith("EXCLUDED"))
        topo = (w["admitted_not_in_any_band_m_by_role"] or {}).get("TOPOLOGY_BOUNDARY", 0.0)
        rows.append({"floor": fl, "established_m_by_width_mm": est, "ambiguous_m_by_width_mm": amb,
                     "established_m": _r(sum(est.values())), "established_excl_920_m": _r(est_x920),
                     "ambiguous_m": _r(sum(amb.values())), "blockwork_rows_m": bw,
                     "blockwork_counted_m": _r(bw_in),
                     "topology_boundary_not_in_any_band_m": _r(topo),
                     "admitted_not_in_any_band_m_by_role": w["admitted_not_in_any_band_m_by_role"],
                     "conservation": {"established_excl_920 - blockwork_counted": _r(est_x920 - bw_in),
                                      "ambiguous_with_no_row": _r(sum(amb.values()))},
                     "band_counts": w["band_counts"]})
        tot["established_m"] += sum(est.values())
        tot["established_excl_920_m"] += est_x920
        tot["ambiguous_m"] += sum(amb.values())
        tot["topology_boundary_not_in_any_band_m"] += topo
        tot["blockwork_counted_m"] += bw_in
    return {"SCHEMA": "URBAN_ALSENAN_WALL_LENGTH_CONSERVATION_V1", "rows": rows,
            "totals": {k: _r(v, 2) for k, v in sorted(tot.items())},
            "rule": "admitted boundary length = established bands + ambiguous bands + unpaired boundary; every metre "
                    "must end in a blockwork row, a BLOCKED row or a NOT_WALL classification. Today ambiguous bands "
                    "and unpaired TOPOLOGY_BOUNDARY length end nowhere (SD-07)"}


# ============================================================================ K. openings
def openings(D) -> dict:
    v3 = {o["id"]: o for o in D["live"]["openings"]}
    h = {o["id"]: o for o in D["openings_v3b"]["heights"]}
    a = {o["id"]: o for o in D["openings_v3b"]["areas"]}
    rows = []
    for oid in sorted(v3):
        o, hh, aa = v3[oid], h.get(oid, {}), a.get(oid, {})
        flags = []
        if o["status"] == "COMPUTED" and str(o.get("height_state", "")).startswith("BLOCKED"):
            flags.append("V3A_STATUS_COMPUTED_WITH_BLOCKED_HEIGHT")
        if o["kind"] == "WINDOW" and ((aa.get("sill_m") or 1.0) < 0.15 or (hh.get("height_m") or 0) >= 2.0):
            flags.append("GLAZED_DOOR_CANDIDATE")
        if aa.get("commercial") == "BUDGET_ESTIMATE":
            flags.append("BUDGET_AREA")
        rows.append({"id": oid, "floor": o["floor"], "kind": o["kind"], "width_m": o["width_m"],
                     "wall_t_m": o["wall_t_m"], "v3a_height_state": o.get("height_state"), "v3a_status": o["status"],
                     "v3b_height_m": hh.get("height_m"), "v3b_state": hh.get("state"), "v3b_grade": hh.get("grade"),
                     "v3b_technical": hh.get("technical"), "v3b_commercial": hh.get("commercial"),
                     "sill_m": aa.get("sill_m"), "area_m2": aa.get("area_m2"), "low_m2": aa.get("low_m2"),
                     "high_m2": aa.get("high_m2"),
                     "completeness": ("COMPLETE" if hh.get("technical") in ("RASTER_DERIVED", "MEASURED", "DERIVED")
                                      else "HEIGHT_PROVISIONAL" if hh.get("technical") == "PARTIAL"
                                      else "HEIGHT_BLOCKED"), "flags": flags})
    c = Counter((r["kind"], r["completeness"]) for r in rows)
    return {"SCHEMA": "URBAN_ALSENAN_OPENING_COMPLETENESS_V1", "rows": rows,
            "counts": {f"{k[0]}|{k[1]}": v for k, v in sorted(c.items())},
            "glazed_door_candidates": [r["id"] for r in rows if "GLAZED_DOOR_CANDIDATE" in r["flags"]],
            "rule": "an opening is complete only with width, height and sill from source or raster; V3a status "
                    "COMPUTED with a BLOCKED height is a status defect"}


# ============================================================================ O. legacy CAD reachability
SEARCH = [ROOT, LAB, ROOT / "tools"]
ROOTS = {"RC1 Qortuba (rc1_qortuba)": LAB / "rc1_qortuba.py",
         "Alsenan V3b (alsenan_v3b)": LAB / "alsenan_v3b.py",
         "engine.document_reader": ROOT / "engine/document_reader.py",
         "engine.pm_sync": ROOT / "engine/pm_sync.py", "engine.ingest.harness": ROOT / "engine/ingest/harness.py",
         "tools/run_cad_pipeline.py": ROOT / "tools/run_cad_pipeline.py",
         "tools/run_pipeline.py": ROOT / "tools/run_pipeline.py",
         "engine.freeze_manifest": ROOT / "engine/freeze_manifest.py"}
TARGET = ROOT / "engine/cad_adapter.py"


def _resolve(name, here):
    parts = name.split(".")
    for base in [here.parent] + SEARCH:
        for cand in (base.joinpath(*parts).with_suffix(".py"), base.joinpath(*parts, "__init__.py")):
            if cand.exists():
                return cand
    return None


def _imports(path):
    try:
        tree = ast.parse(path.read_text())
    except (SyntaxError, UnicodeDecodeError):
        return []
    top = set(id(n) for n in tree.body)
    out = []
    for node in ast.walk(tree):
        lazy = id(node) not in top and not isinstance(getattr(node, "_parent", None), ast.Module)
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
        else:
            continue
        for n in names:
            p = _resolve(n, path)
            if p:
                out.append((p, id(node) not in top))
    return out


def _reach(root, allow_lazy):
    seen, stack, parent = {root}, [root], {}
    while stack:
        p = stack.pop()
        for q, lazy in _imports(p):
            if (lazy and not allow_lazy) or q in seen:
                continue
            seen.add(q)
            parent[q] = p
            stack.append(q)
    if TARGET not in seen:
        return None
    chain, q = [TARGET], TARGET
    while q in parent:
        q = parent[q]
        chain.append(q)
    return [str(x.relative_to(ROOT)) for x in reversed(chain)]


def legacy_cad(D) -> dict:
    refs = sorted(str(p.relative_to(ROOT)) for p in list((ROOT / "engine").rglob("*.py")) +
                  list((ROOT / "tools").rglob("*.py")) + list((ROOT / "research").rglob("*.py")) +
                  list((ROOT / "tests").rglob("*.py"))
                  if "cad_adapter" in p.read_text(errors="ignore") and "alsenan_control_plane" not in str(p))
    rows = []
    for name, p in ROOTS.items():
        if not p.exists():
            rows.append({"entry_point": name, "path": str(p.relative_to(ROOT)), "exists": False})
            continue
        top = _reach(p, False)
        lazy = top or _reach(p, True)
        guard = "refuse_if_sealed" in p.read_text() if p.suffix == ".py" else False
        rows.append({"entry_point": name, "path": str(p.relative_to(ROOT)), "exists": True,
                     "reaches_cad_adapter_module_level": top is not None, "chain_module_level": top,
                     "reaches_cad_adapter_incl_lazy": lazy is not None, "chain_incl_lazy": lazy,
                     "deprecation_guard": False, "seal_guard_only": guard,
                     "state": ("REACHABLE" if top else "REACHABLE_LAZY" if lazy else "NOT_REACHABLE")})
    return {"SCHEMA": "URBAN_ALSENAN_LEGACY_CAD_REACHABILITY_V1", "target": "engine/cad_adapter.py",
            "files_referencing_cad_adapter": refs, "files_referencing_count": len(refs), "rows": rows,
            "rule": "static AST import graph (module-level and lazy function-level imports, bare lab names "
                    "resolved against research/external_engine_lab and tools); the legacy adapter must be "
                    "unreachable from release paths or reachable only behind an explicit deprecation guard"}


# ============================================================================ M. donors
DONORS = [
    {"donor": "kentucky-ai/opentakeoff", "licence": "Apache-2.0", "lock": "e6d2251", "upstream_head": "c7e02eb",
     "commits_ahead": 42, "use": "PATTERNS ONLY (TypeScript)", "new_ideas": [
         "63a86e5 measured that OCR confidence does not separate misreads (247 correct / 23 misread; below 0.9: 21 "
         "correct + 10 misreads) -> never gate a schedule value on OCR confidence alone",
         "24d1d95 wordClean ruling cleanup + repairKey with a read_as flag -> keep the raw read beside the repair",
         "256ef63 public regression fixtures for high-confidence OCR code errors -> adversarial schedule fixtures",
         "c3ec135 duplicate re-import prevention -> idempotent schedule ingest (SB2 duplicate rows)",
         "1f2919e sheetgraph finish-table headings; sheetgraph.ts classifySheetRole / extractTables / roomTags / "
         "detailCallouts / resolveTag; MCP find_schedule / resolve_tag -> a schedule-to-tag resolver with an "
         "explicit unresolved state", "RFI model with tombstones -> owner questions that cannot silently vanish",
         "scalewarn.ts / gate.ts -> scale warnings as a gate, not a log line"],
     "existing_urban_use": "schedule-reading ideas behind A3 (V3c audit)",
     "implemented_wrongly": "A3 reads schedules from PDF text and hand transcription when the DXF carries the same "
                            "table as ATTRIBs; no find_schedule-style coverage check exists"},
    {"donor": "jeremylongshore/cad-ai-agent", "licence": "Apache-2.0", "lock": "3215dc0", "use": "PATTERNS ONLY",
     "new_ideas": [
         "tests/property/test_fuzz_matching.py: seeded-RNG fuzz (Random(42), bounded iterations) - property tests "
         "without a runtime dependency (hypothesis is declared there but not needed for the pattern)",
         "models/health_schema.py: deterministic HealthReport (issues with evidence refs, checks_run list, score) -> "
         "every register lists checks_run so a missing check is visible",
         "core/cross_drawing_checker.py: pure, order-stable cross-sheet consistency passes (labels, layers, blocks, "
         "counts, alignment) -> architectural vs structural sheet cross-check (column tags, lift, stair)",
         "models/comparison_schema.py: typed revision comparison"],
     "existing_urban_use": "none", "implemented_wrongly": None},
    {"donor": "userfypp/plan-measure", "licence": "MIT", "lock": "ec5c475", "use": "PATTERNS ONLY (TypeScript)",
     "new_ideas": [
         "types/domain.ts: PageCalibration = UniformPageCalibration | XyPageCalibration with separate xReference / "
         "yReference two-point references -> per-axis scale for raster sheets (L)",
         "measurements carry calibrationId -> every raster-derived quantity names the calibration it used",
         "persistenceCodec.ts versioned decode with validation -> register schema migration (D)"],
     "existing_urban_use": "V3b raster lane uses one uniform scale per sheet", "implemented_wrongly":
         "V3b.1 sheet calibration is uniform; a per-axis residual is not measured or recorded"},
    {"donor": "ContractorKeith/conmcp", "licence": "MIT", "lock": "0a08f63", "use": "PATTERNS ONLY",
     "new_ideas": ["domain/sheets.py: unknown pages fall back to 'unclassified' rather than guessing",
                   "domain/quantities.py: one explicit UOM vocabulary as the single source of truth",
                   "audit.py: audit_event per tool call", "TakeoffItem.source sheet reference on every item"],
     "existing_urban_use": "unit guard exists (V3 UNIT_REGISTER)", "implemented_wrongly": None},
    {"donor": "braedonsaunders/bidwright", "licence": "AGPL-3.0-only", "lock": "4f20096",
     "use": "IDEAS ONLY - no code, no copied structure",
     "new_ideas": ["evidence gate: a worksheet item is rejected unless it carries a structured source reference; "
                   "prose ('best judgment', 'see notes') must keep failing - and the gate itself has a contract test",
                   "drawing-evidence atlas: documents not classified as drawing evidence are listed as excluded, "
                   "with an explicit 'add with rationale' path"],
     "existing_urban_use": "none", "implemented_wrongly": None},
    {"donor": "U-C4N (prior lock)", "licence": "see DONORS.lock", "use": "SHADOW EXPERIMENT DESIGN ONLY",
     "new_ideas": ["run as a shadow reader of the same DXF and compare per-entity counts / attribute values against "
                   "K2 (no production path)"], "existing_urban_use": "R8 donor audit",
     "implemented_wrongly": None},
]


def donors(D) -> dict:
    return {"SCHEMA": "URBAN_ALSENAN_DONOR_DELTA_V1", "rows": DONORS,
            "rule": "no donor code enters production; AGPL donors are ideas only; every idea maps to a control gate "
                    "or a test in the review, never to a quantity"}


# ============================================================================ Q. benchmark confidence
def benchmark(D) -> dict:
    norm = {(r["trade"], r["subtrade"]): r for r in D["bench_norm"]["records"] if r["row_kind"] == "COVER_TOTAL"}
    typed = {(i["file"], i["label"]): i["value"] for f in D["bench_qa"]["findings"]
             if f["check"] == "TYPED_CONSTANTS_ON_COVERS" for i in f["items"]}
    rows = []
    for e in D["bench_eval"]["rows"]:
        trade, sub = e["benchmark"].split(" / ")
        n = norm.get((trade, sub), {})
        is_typed = any(abs(v - e["benchmark_qty"]) < 0.005 for (fl, lab), v in typed.items()
                       if lab == n.get("label_ar")) or (trade == "REBAR")
        backed = bool(n.get("source_formula")) or str(n.get("formula", "")).startswith("=SUM")
        notes = []
        if trade == "REBAR":
            cls = "WEAK_HUMAN_REFERENCE"
            notes.append("44.19 t = sum of seven typed constants on the RC cover (5.8+9.75+7.95+9.89+5.4+3.9+1.5); "
                         "no bar schedule behind it; RC كمرات!I82 also skips I59 (0.128 m3)")
        elif sub == "WET_ROOM:FLOOR":
            cls = "WEAK_HUMAN_REFERENCE"
            notes.append("cover value 72.01 is a typed constant; it equals the formula-backed wet-floor tile subtotal "
                         "(سيراميك!H65 =SUM(H42:H63)) and is reused for wet ceilings and decor paint - the WP area "
                         "equals the tile area with no separate measurement")
        elif is_typed or not backed and trade in ("RAILING",) or sub == "ROOF:FLOOR":
            cls = "WEAK_HUMAN_REFERENCE"
            notes.append("typed constant on the cover, not traceable to a detail row")
        elif trade in ("PAINT", "PLASTER"):
            cls = "STRONG_HUMAN_REFERENCE"
            notes.append(f"gross {n.get('gross')} - deduction {n.get('deduction')}; unit cell blank in B1 (unit "
                         "inferred from trade)")
        elif trade == "OTHER_CONCRETE":
            cls = "STRONG_HUMAN_REFERENCE"
            notes.append("=SUM of detail rows; one SUM_SKIPS_LEADING_ROWS finding (I59 = 0.128 m3) -> "
                         "HUMAN_FORMULA_ERROR of +0.128 m3 inside it")
        else:
            cls = "STRONG_HUMAN_REFERENCE"
            notes.append(f"formula-backed ({n.get('source_formula') or n.get('formula')})")
        rows.append({"benchmark": e["benchmark"], "qty": e["benchmark_qty"], "unit": e["unit"],
                     "unit_source": e["benchmark_unit_source"], "cover_formula": n.get("formula"),
                     "source_formula": n.get("source_formula"), "class": cls,
                     "urban_v3b_technical": e["v3b_technical"], "urban_v3b_commercial": e["v3b_commercial"],
                     "diff_technical_pct": e["diff_technical_pct"], "diff_commercial_pct": e["diff_commercial_pct"],
                     "notes": notes, "use": "FINDING_ONLY - never a target"})
    rows.append({"benchmark": "FIN رخام+حوش!H44", "class": "HUMAN_FORMULA_ERROR",
                 "notes": ["=SUM(H13:H41) contains H13 (151.8) which is also reported on the cover (B22 and B24) - "
                           "double count or omitted item"], "use": "FINDING_ONLY"})
    rows.append({"benchmark": "RC كمرات!I82", "class": "HUMAN_FORMULA_ERROR",
                 "notes": ["=SUM(I60:I78) skips I59 (0.128); the same block's I79 includes it"], "use": "FINDING_ONLY"})
    return {"SCHEMA": "URBAN_ALSENAN_BENCHMARK_CONFIDENCE_V1",
            "classes": ["VERIFIED_SOURCE_TRUTH", "STRONG_HUMAN_REFERENCE", "WEAK_HUMAN_REFERENCE",
                        "HUMAN_FORMULA_ERROR", "UNRESOLVED"],
            "rows": rows, "counts": dict(Counter(r["class"] for r in rows)),
            "rule": "no freelancer value is VERIFIED_SOURCE_TRUTH - only a value re-derived from the drawings can be; "
                    "a human reference ranks a disagreement for review and never moves a quantity"}


# ============================================================================ P. scorecard
def scorecard(D, regs) -> dict:
    rr = regs["ROOM_SEMANTIC_TRADE_RELEASE_REGISTER"]
    pc = regs["STRUCTURAL_POPULATION_COVERAGE_REGISTER"]
    sc = regs["STRUCTURAL_SOURCE_COVERAGE_REGISTER"]
    wc = regs["WALL_LENGTH_CONSERVATION_REGISTER"]["totals"]
    oc = regs["OPENING_COMPLETENESS_REGISTER"]
    fd = rr["floor_decomposition_m2"]
    nsrc = len(sc["rows"])
    complete = sum(1 for r in sc["rows"] if r["state"] in ("CONSUMED_COMPLETE", "NOT_RELEVANT"))
    occ = [r for r in pc["rows"] if r["population"] in ("FOOTING", "COLUMN", "BEAM", "CONTINUOUS_BEAM", "STRAP_BEAM")]
    req = [r for r in occ if r["state"] != "NOT_REQUIRED"]
    metrics = [
        ("M01", "floor area released while its room is COMPUTED_REVIEW", "m2",
         fd.get("floor_COMPUTED_REVIEW"), 0.0, "rooms not proved closed must not carry a COMPUTED floor"),
        ("M02", "rooms with TS01 semantic state unresolved but released", "nr",
         sum(1 for r in rr["rows"] if "TS01_UNRESOLVED_BUT_RELEASED" in r["flags"]), 0, "BLOCKED_SEMANTIC_ZONE"),
        ("M03", "wet labels lost (in DRY zone or no site)", "nr",
         len(rr["wet_rooms_lost"]), 0, "English label per wet room (Arabic twin not double-counted)"),
        ("M04", "structural source objects fully consumed", "%", _r(100.0 * complete / nsrc, 1), 100.0, None),
        ("M05", "concrete occurrences with complete rebar", "%",
         _r(100.0 * sum(1 for r in req if r["state"] == "REBAR_COMPLETE") / len(req), 1), 100.0, None),
        ("M06", "occurrences dropped silently (no row)", "nr", pc["silent_occurrences"], 0, None),
        ("M07", "rebar kg on occurrences with no concrete", "kg", pc["d5_rebar_without_concrete"]["kg"], 0.0, None),
        ("M08", "ambiguous wall-band length with no row", "m", wc["ambiguous_m"], 0.0, None),
        ("M09", "unpaired topology-boundary length with no row", "m", wc["topology_boundary_not_in_any_band_m"],
         0.0, "classified as wall / not-wall / blocked"),
        ("M10", "openings with a source or raster height", "%",
         _r(100.0 * sum(1 for r in oc["rows"] if r["completeness"] == "COMPLETE") / len(oc["rows"]), 1), 100.0,
         None),
        ("M11", "openings COMPUTED in V3a with a BLOCKED height", "nr",
         sum(1 for r in oc["rows"] if "V3A_STATUS_COMPUTED_WITH_BLOCKED_HEIGHT" in r["flags"]), 0, None),
        ("M12", "silent-drop code paths", "nr", len(regs["SILENT_DROP_REGISTER"]["rows"]), 0, None),
    ]
    return {"SCHEMA": "URBAN_ALSENAN_ACCURACY_SCORECARD_DRAFT_V1",
            "rows": [{"id": i, "metric": m, "unit": u, "current": c, "acceptance": a, "note": n}
                     for i, m, u, c, a, n in metrics],
            "rule": "DRAFT - the scorecard measures control-plane completeness (what is released on what evidence), "
                    "not closeness to the freelancer workbook; no row is ever computed from a benchmark value"}


def build():
    D = load()
    regs = {}
    regs["STRUCTURAL_SOURCE_COVERAGE_REGISTER"] = source_coverage(D)
    regs["STRUCTURAL_POPULATION_COVERAGE_REGISTER"] = population_coverage(D)
    regs["SILENT_DROP_REGISTER"] = silent_drops(D)
    regs["ROOM_SEMANTIC_TRADE_RELEASE_REGISTER"] = room_release(D)
    regs["WALL_LENGTH_CONSERVATION_REGISTER"] = wall_conservation(D)
    regs["OPENING_COMPLETENESS_REGISTER"] = openings(D)
    regs["LEGACY_CAD_REACHABILITY_REGISTER"] = legacy_cad(D)
    regs["DONOR_DELTA_REGISTER"] = donors(D)
    regs["BENCHMARK_CONFIDENCE_REGISTER"] = benchmark(D)
    regs["ACCURACY_SCORECARD_DRAFT"] = scorecard(D, regs)
    return regs


def write(regs):
    OUT.mkdir(exist_ok=True)
    idx = {}
    for name in REGISTERS:
        txt = json.dumps(regs[name], indent=1, ensure_ascii=False, sort_keys=False) + "\n"
        (OUT / f"{name}.json").write_text(txt)
        idx[name] = hashlib.sha256(txt.encode()).hexdigest()
    idx_doc = {"SCHEMA": "URBAN_ALSENAN_CONTROL_PLANE_INDEX_V1", "registers": idx,
               "evidence": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(EVID.glob("*.json"))}}
    (OUT / "INDEX.json").write_text(json.dumps(idx_doc, indent=1) + "\n")
    return idx_doc


if __name__ == "__main__":
    doc = write(build())
    for k, v in doc["registers"].items():
        print(f"{k:45s} {v[:12]}")
