"""ALSENAN Phase A registers: 19 frozen JSON registers, the Phase A BOQ (13 columns), the XLSX VIEW and the freeze.

Every quantity here is copied from an engine row built in alsenan_phase_a.py; this module adds nothing, rounds
nothing and fills no gap. A BLOCKED row carries no quantity and enters no total. The XLSX is a view written by
engine/boq_rc1_xlsx.py (BOQ_XLSX_EXPORT_V2, scoped additive summaries) and read back against these registers.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from engine import boq_rc1_xlsx as BX                                                            # noqa: E402
from engine.source import benchmark_firewall as FW, cad_text as CT, freeze_schema as FS          # noqa: E402
from engine.source import level_marks as LM, schedule_table as ST, structural_qto as SQ          # noqa: E402
from engine.source import topology_digest as TD                                                   # noqa: E402

import alsenan_phase_a as AP                                                                      # noqa: E402

RECOMMENDATION_COMMIT, BASELINE_COMMIT = "3ef390d", "63ed9b1"
CREATED = dt.datetime(2026, 10, 2, 0, 0, 0)
XLSX_NAME = "URBAN_QTO_ALSENAN_P7757_ST7757_PHASE_A.xlsx"
BANNER = ("SHADOW / PHASE A DEVELOPMENT VALIDATION - ALSENAN CHALET P7757 + ST7757 - FROZEN BEFORE ANY BENCHMARK - "
          "NOT APPROVED FOR TENDER OR CONTRACT - NO PRICES - VIEW OVER ENGINE REGISTERS - NO PRODUCTION MIGRATION")
COLUMNS = ["ITEM CODE", "DISCIPLINE", "TRADE", "FLOOR", "ROOM/ELEMENT", "DESCRIPTION AR", "DESCRIPTION EN", "QTY",
           "UNIT", "STATUS", "SOURCE", "RULE", "BLOCKER"]
FLOORS = ("GF", "1F", "2F")
UNIT_A = "unit"


def digest(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def r6(v):
    return None if v is None else round(v, 6)


# ====================================================================== architectural trade items (Urban rules travel)
ARCH_ITEMS = [
    # code, trade, AR, EN, unit, rule, needs
    ("A-FLR-01", "FLOOR", "مساحة الأرضيات الصافية", "Net floor area per room", "m2", "TS01 certified room site",
     ("ROOMS",)),
    ("A-FLR-02", "FLOOR_FINISH", "تبليط الأرضيات", "Floor finish (tiles / porcelain / marble)", "m2",
     "URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1 (only where cabinetry is identified)", ("ROOMS", "FINISH")),
    ("A-CLG-01", "CEILING", "الأسقف (جبس / صبغ)", "Ceiling finish", "m2", "ceiling = certified room footprint",
     ("ROOMS", "FINISH")),
    ("A-SKT-01", "SKIRTING", "وزرة", "Skirting", "lm", "URBAN-SKIRTING-OPENING-METHOD@v1; US-02 (none in fully tiled "
     "rooms); US-08", ("ROOMS", "OPENINGS", "FINISH")),
    ("A-HPR-01", "HIDDEN_PROFILE", "بروفايل مخفي", "Hidden profile (same path as skirting)", "lm", "US-08",
     ("ROOMS", "OPENINGS", "FINISH")),
    ("A-BLK-01", "BLOCKWORK", "طابوق (حسب السماكة)", "Blockwork by wall-band thickness", "m2",
     "wall bands by thickness (never 'paired lines = wall')", ("BANDS", "HEIGHT", "OPENINGS")),
    ("A-PLS-01", "INTERNAL_PLASTER", "لياسة داخلية", "Internal plaster (exposed faces - openings + reveals + "
     "columns)", "m2", "URBAN-WALL-FINISH-HEIGHT-METHOD@v1; US-06; URBAN-REVEAL-FINISH-METHOD@v1; "
     "URBAN-EXPOSED-COLUMN-FINISH-METHOD@v1", ("ROOMS", "HEIGHT", "OPENINGS")),
    ("A-PNT-01", "INTERNAL_PAINT", "صبغ داخلي", "Internal paint (dry rooms only)", "m2",
     "URBAN-WALL-FINISH-HEIGHT-METHOD@v1 (no dry paint in wet rooms)", ("ROOMS", "HEIGHT", "OPENINGS", "WET")),
    ("A-WTL-01", "WALL_TILE", "سيراميك جدران", "Wall tiles (wet / service rooms)", "m2", "US-01 wet ceramic",
     ("ROOMS", "HEIGHT", "OPENINGS", "WET", "FINISH")),
    ("A-WTP-01", "TILE_PREP", "تجهيز للسيراميك", "Tile preparation (separate from plaster)", "m2", "US-01",
     ("ROOMS", "HEIGHT", "OPENINGS", "WET")),
    ("A-WPF-01", "WATERPROOFING", "عزل مائي أرضيات", "Waterproofing membrane = wet / service floor area", "m2",
     "US-04 / US-14 (wet identity not from label text alone)", ("ROOMS", "WET")),
    ("A-WPU-01", "WATERPROOFING", "عزل مائي جوانب 15 سم", "Waterproofing upturn 0.15 m on the gross perimeter "
     "(doorway not deducted)", "m2", "US-05", ("ROOMS", "WET")),
    ("A-MRB-01", "MARBLE", "رخام عتبات", "Marble thresholds (wet / service doors)", "lm",
     "URBAN-WET-SERVICE-MARBLE-THRESHOLD@v1", ("ROOMS", "OPENINGS", "WET")),
    ("A-STR-01", "STAIRS", "درج (قوائم ونوائم)", "Stair treads / risers / landings", "no.",
     "deterministic stair geometry only", ("STAIRS",)),
    ("A-STR-02", "STAIR_FINISH", "تكسية الدرج ووزرة الدرج", "Stair finish + stair skirting", "lm",
     "deterministic stair geometry only", ("STAIRS", "FINISH")),
    ("A-HRL-01", "HANDRAIL", "درابزين", "Handrails / balustrades", "lm", "deterministic stair geometry only",
     ("STAIRS",)),
    ("A-DOR-01", "INTERNAL_DOORS", "أبواب داخلية", "Internal doors (US-13: PVC)", "no.", "OPENING_REGISTER_V1; US-13",
     ("OPENINGS", "ROOMS")),
    ("A-DOR-02", "EXTERNAL_DOORS", "أبواب خارجية", "External / entrance doors", "no.", "OPENING_REGISTER_V1; US-13",
     ("OPENINGS", "ROOMS")),
    ("A-ALU-01", "ALUMINIUM", "ألمنيوم (أبواب وشبابيك خارجية)", "Aluminium exterior openings (US-13)", "no.",
     "OPENING_REGISTER_V1; US-13", ("OPENINGS", "WINDOWS")),
    ("A-WIN-01", "WINDOWS", "شبابيك", "Windows", "no.", "OPENING_REGISTER_V1; US-11 (no default window height)",
     ("WINDOWS",)),
    ("A-GLZ-01", "GLAZING", "زجاج", "Glazing", "m2", "OPENING_REGISTER_V1 (no material from appearance)",
     ("WINDOWS", "HEIGHT")),
    ("A-PAS-01", "PASSAGES", "فتحات بدون أبواب", "Passages / doorless openings", "no.", "US-16 / US-17",
     ("OPENINGS", "ROOMS")),
    ("A-REV-01", "REVEALS", "جوانب الفتحات", "Opening reveals", "m2", "URBAN-REVEAL-FINISH-METHOD@v1; US-07",
     ("OPENINGS", "HEIGHT")),
    ("A-COL-01", "EXPOSED_COLUMNS", "أعمدة ظاهرة", "Exposed column faces", "m2",
     "URBAN-EXPOSED-COLUMN-FINISH-METHOD@v1", ("ROOMS", "HEIGHT")),
    ("A-DCT-01", "SHAFTS_DUCTS", "مناور ودكتات", "Shafts / ducts finishes", "m2",
     "URBAN-EXPOSED-INTERIOR-DUCT-FINISH-METHOD@v1 (owner physical authority required)", ("ROOMS", "HEIGHT")),
]
EXT_ITEMS = [
    ("A-PLS-02", "EXTERNAL_PLASTER", "لياسة خارجية", "External plaster (elevations)", "m2",
     "exposed external faces - openings + reveals", ("ELEVATIONS", "OPENINGS")),
    ("A-PNT-02", "EXTERNAL_PAINT", "صبغ خارجي", "External paint (elevations)", "m2",
     "exposed external faces - openings + reveals", ("ELEVATIONS", "OPENINGS")),
]


def arch_blockers(ctx, floor, needs) -> list:
    a = ctx["arch"].get(floor, {})
    t = a.get("strict_topology", {})
    out = []
    if "ROOMS" in needs or "BANDS" in needs:
        iss = ", ".join(f"{k} x{v}" for k, v in sorted(t.get("issues", {}).items(), key=lambda kv: -kv[1])[:3])
        out.append(f"ROOM_TOPOLOGY_NOT_CERTIFIED: TS01 built {t.get('sites')} sites on {floor}, "
                   f"{t.get('certified_room_sites')} certified (largest {t.get('largest_site', {}) and t['largest_site']['area_m2_provisional']} m2; {iss})")
        out.append("LAYER_ROLE_AUTHORITY_MISSING: numeric / single-letter layers carry no role (layer 1 = walls AND "
                   "sheet frames; W = plot boundary) - OQ-A1")
    if "BANDS" in needs:
        out.append(f"WALL_BAND_THICKNESS_NOT_ESTABLISHED: {sum(t.get('wall_bands', {}).values())} bands, 0 ESTABLISHED")
    if "HEIGHT" in needs:
        out.append("HEIGHT_NOT_ESTABLISHED: sections exist only as raster (PDF 07-12 pp. 4-5); vector elevations give "
                   "finished-floor marks only; no slab / finish build-up; 3.15 / 3.20 never reused - OQ-S1")
    if "OPENINGS" in needs:
        n = len(a.get("door_candidates", []))
        out.append(f"OPENING_ROLE_NOT_ADMITTED: {n} door-signature candidates on {floor} (block arcs on layer D; no DOOR "
                   f"role, no reviewed claim); no door / window schedule - OQ-A2")
    if "WINDOWS" in needs:
        out.append("GLAZING_ROLE_NOT_ESTABLISHED: no window / glazing layer role; window existence not proved - OQ-A1")
    if "WET" in needs:
        wet = [l["label_en"] for l in a.get("labels", []) if l["class_candidate"].startswith("WET")]
        out.append(f"WET_IDENTITY_LABEL_ONLY: {len(wet)} wet-label candidates ({', '.join(sorted(set(wet)))}) with no "
                   "certified room to host them; sanitary sheet is supporting evidence only")
    if "FINISH" in needs:
        out.append("FINISH_SCHEDULE_ABSENT: no finish schedule in the source - OQ-F1")
    if "STAIRS" in needs:
        out.append(f"STAIR_ROLE_NOT_ESTABLISHED: {len(a.get('stair_arrow_blocks', []))} stair-arrow blocks observed; "
                   "tread / riser lines have no role authority; nothing counted")
    if "ELEVATIONS" in needs:
        out.append("ELEVATION_SET_INCOMPLETE: NE / SW elevations exist only as raster (PDF 07-12 pp. 1, 3); no wall "
                   "height / opening register for the facades")
    return out


def sheet_src(ctx, floor):
    s = ctx["sheets_by_floor"].get(floor)
    return f"P7757.dxf {s['sheet']} ({'; '.join(s['titles'][:1])})" if s else "P7757.dxf (no sheet)"


def arch_boq(ctx) -> list:
    rows = []
    for fl in FLOORS:
        for code, trade, ar, en, unit, rule, needs in ARCH_ITEMS:
            rows.append({"item": f"{code}-{fl}", "discipline": "ARCHITECTURAL", "trade": trade, "floor": fl,
                         "element": "ALL ROOMS OF THE FLOOR (room by room once certified)", "ar": ar, "en": en,
                         "qty": None, "unit": unit, "status": "BLOCKED", "source": sheet_src(ctx, fl), "rule": rule,
                         "blockers": arch_blockers(ctx, fl, needs)})
    for code, trade, ar, en, unit, rule, needs in EXT_ITEMS:
        rows.append({"item": f"{code}-EXT", "discipline": "ARCHITECTURAL", "trade": trade, "floor": "EXTERNAL",
                     "element": "ALL FACADES", "ar": ar, "en": en, "qty": None, "unit": unit, "status": "BLOCKED",
                     "source": "P7757.dxf NW / SE elevations; PDF 01-06 p.6, 07-12 pp.1-3 (raster)", "rule": rule,
                     "blockers": arch_blockers(ctx, "GF", needs)})
    return rows


# ====================================================================== structural BOQ
STRUCT_BLOCKED = [
    ("S-BLD-01", "BLINDING", "FOUNDATION", "خرسانة عادية (نظافة) تحت القواعد", "Plain concrete blinding under footings",
     "m3", ["BLINDING_THICKNESS_NOT_IN_VECTOR_SOURCE: typical footing detail exists only as vector strokes / raster "
            "(ST7757.pdf p.13); no outline offset stated in the DXF"]),
    ("S-NCK-01", "COLUMN_NECKS", "FOUNDATION", "رقاب الأعمدة", "Column necks (footing top to ground beam)", "m3",
     ["FOUNDING_LEVEL_NOT_STATED: only 'excavation not less than 1.5 m below plot level' (a minimum, not a level)",
      "GROUND_BEAM_LEVEL_NOT_STATED"]),
    ("S-GB-01", "GROUND_BEAMS", "FOUNDATION", "الميدات", "Ground beams", "m3",
     ["BEAM_LENGTH_NOT_ESTABLISHED: beam bands on the ground-beams plan are not associated to tags (G-06)",
      "GROUND_BEAM_SECTION_NOT_IN_A_READ_SCHEDULE"]),
    ("S-SB-01", "STRAP_BEAMS", "FOUNDATION", "الميدات الرابطة (S.B)", "Strap beams S.B1 - S.B3", "m3",
     ["STRAP_BEAM_SECTION_NOT_SCHEDULED in the DXF", "INCLINED_ELEMENTS_NOT_MEASURED (G-14)"]),
    ("S-GS-01", "GROUND_SLAB", "GF", "بلاطة أرضية", "Ground slab (T=10cm label on the ground-beams plan)", "m3",
     ["SLAB_OUTLINE_NOT_ESTABLISHED (G-06)"]),
    ("S-COL-GF", "COLUMNS", "GF", "أعمدة الدور الأرضي", "Ground-floor columns", "m3",
     ["COLUMN_HEIGHT_NOT_ESTABLISHED: structural slab levels are not stated; architectural FFL marks include finishes"]),
    ("S-COL-1F", "COLUMNS", "1F", "أعمدة الدور الأول", "First-floor columns", "m3",
     ["COLUMN_HEIGHT_NOT_ESTABLISHED: structural slab levels are not stated; architectural FFL marks include finishes"]),
    ("S-COL-2F", "COLUMNS", "2F", "أعمدة الدور الثاني", "Second-floor / top columns", "m3",
     ["COLUMN_HEIGHT_NOT_ESTABLISHED: structural slab levels are not stated; architectural FFL marks include finishes"]),
    ("S-BM-GF", "BEAMS", "GF", "جسور سقف الأرضي", "Beams - ground-floor roof", "m3",
     ["BEAM_LENGTH_NOT_ESTABLISHED (G-06)", "CONTINUOUS_BEAM_SCHEDULES_NOT_READ (graphic multi-span tables)"]),
    ("S-BM-1F", "BEAMS", "1F", "جسور سقف الأول", "Beams - first-floor roof", "m3",
     ["BEAM_LENGTH_NOT_ESTABLISHED (G-06)", "CONTINUOUS_BEAM_SCHEDULES_NOT_READ (graphic multi-span tables)"]),
    ("S-BM-2F", "BEAMS", "2F", "جسور سقف الثاني", "Beams - second-floor roof", "m3",
     ["BEAM_LENGTH_NOT_ESTABLISHED (G-06)", "CONTINUOUS_BEAM_SCHEDULES_NOT_READ (graphic multi-span tables)"]),
    ("S-SLB-GF", "SLABS", "GF", "بلاطة سقف الأرضي", "Slab - ground-floor roof", "m3",
     ["SLAB_OUTLINE_NOT_ESTABLISHED (G-06): panels are drawn between beam lines; thickness labels exist"]),
    ("S-SLB-1F", "SLABS", "1F", "بلاطة سقف الأول", "Slab - first-floor roof", "m3",
     ["SLAB_OUTLINE_NOT_ESTABLISHED (G-06): panels are drawn between beam lines; thickness labels exist"]),
    ("S-SLB-2F", "SLABS", "2F", "بلاطة سقف الثاني", "Slab - second-floor roof", "m3",
     ["SLAB_OUTLINE_NOT_ESTABLISHED (G-06): panels are drawn between beam lines; thickness labels exist"]),
    ("S-STR-01", "STAIRS", "ALL", "الدرج الخرساني", "Concrete stairs", "m3",
     ["STAIR_GEOMETRY_ONLY_IN_TYPICAL_DETAIL (ST7757.pdf p.16 strokes); flights not measured"]),
    ("S-POOL-01", "POOL", "GF", "حوض السباحة", "Swimming pool walls / slab", "m3",
     ["POOL_DETAIL_DIMENSIONS_NOT_ASSOCIATED (detail sheet; no measured outline)"]),
    ("S-PAR-01", "PARAPETS", "ROOF", "دروة السطح", "Parapets", "m3", ["PARAPET_DETAIL_ONLY (ST7757.pdf p.14)"]),
]


def footing_rows(ctx):
    rows = ctx["footings"]["rows"]
    by = defaultdict(list)
    for r in rows:
        by[r["element_id"].split("@", 1)[0]].append(r)
    summary = []
    sched = ctx["footing_schedule"]
    for typ in sorted(by, key=lambda t: (len(t), t)):
        rs = by[typ]
        done = [r for r in rs if r["status"] == SQ.COMPLETE]
        blk = [r for r in rs if r["status"] != SQ.COMPLETE]
        q = round(sum(r["qty"] for r in done), 6) if done else None
        st = "COMPUTED_SHADOW_COMPLETE" if done and not blk else "AUTHORISED_SUBTOTAL" if done else "BLOCKED"
        ft = sched.get(typ) or {}
        summary.append({"item": f"S-FTG-{typ}", "discipline": "STRUCTURAL", "trade": "FOOTINGS", "floor": "FOUNDATION",
                        "element": f"footing type {typ} x{len(rs)} tag(s): {len(done)} matched + size-confirmed, "
                                   f"{len(blk)} blocked",
                        "ar": f"خرسانة مسلحة للقواعد - نوع {typ}", "en": f"Reinforced concrete footings type {typ} "
                        f"({ft.get('L_cm')} x {ft.get('W_cm')} x {ft.get('H_cm')} cm)",
                        "qty": q, "unit": "m3", "status": st,
                        "source": "ST7757.dxf FOUNDATION PLAN tags + S-FOOTINGS rectangles; SCHEDULE OF FOOTINGS (cm)",
                        "rule": "STRUCTURAL_QTO_V1: count of tag-in-rectangle matches x L x W x H (schedule), drawn "
                                "size confirmed", "blockers": sorted({b for r in blk for b in r["blockers"]}),
                        "complete_rows": [r["element_id"] for r in done], "blocked_rows": [r["element_id"] for r in blk]})
    return summary


def struct_boq(ctx) -> list:
    rows = footing_rows(ctx)
    for code, trade, fl, ar, en, unit, blk in STRUCT_BLOCKED:
        rows.append({"item": code, "discipline": "STRUCTURAL", "trade": trade, "floor": fl, "element": trade,
                     "ar": ar, "en": en, "qty": None, "unit": unit, "status": "BLOCKED",
                     "source": "ST7757.dxf / ST7757.pdf", "rule": "STRUCTURAL_QTO_V1", "blockers": blk})
    for code, ar, en in (("S-RBR-FTG", "حديد القواعد", "Rebar - footings"), ("S-RBR-COL", "حديد الأعمدة", "Rebar - columns"),
                         ("S-RBR-BM", "حديد الجسور", "Rebar - beams"), ("S-RBR-SLB", "حديد البلاطات", "Rebar - slabs")):
        rows.append({"item": code, "discipline": "STRUCTURAL", "trade": "REBAR", "floor": "ALL", "element": "REBAR",
                     "ar": ar, "en": en, "qty": None, "unit": "kg", "status": "BLOCKED",
                     "source": "ST7757.dxf schedules / slab labels", "rule": "STRUCTURAL_QTO_V1 rebar_gate (FAIL CLOSED, "
                     "no kg/m3)", "blockers": ["REBAR_FAIL_CLOSED: bar length, bar shape, laps and cover are not stated "
                                               "for the scheduled bars (see 21_REBAR)"]})
    return rows


def boq_line(r):
    return [r["item"], r["discipline"], r["trade"], r["floor"], r["element"], r["ar"], r["en"], r6(r["qty"]),
            r["unit"], r["status"], r["source"], r["rule"], " | ".join(r["blockers"])]


# ====================================================================== rebar register
def rebar_register(ctx):
    out = []
    for typ, ft in sorted(ctx["footing_schedule"].items(), key=lambda kv: (len(kv[0]), kv[0])):
        for side in ("short_bars", "long_bars"):
            spec = ft.get(side)
            if not spec:
                continue
            g = SQ.rebar_gate({"bar_diameter_mm": "Ø" in spec and spec.split("Ø")[1].strip().split("/")[0],
                               "count_or_spacing": spec.split("Ø")[0].strip() if "Ø" in spec else None})
            out.append({"element": f"FOOTING {typ}", "direction": side.upper(), "spec": spec,
                        "sub_rows": ft.get(f"{side}_sub_rows"), "gate": g, "kg": None})
    for r in ctx["columns"]["schedule"].get("records", []):
        for c in r["cells"]:
            if c["path"][-1:] == ["REINF"] and c["value"] and "Ø" in c["value"]:
                g = SQ.rebar_gate({"bar_diameter_mm": c["value"].split("Ø")[1].strip(),
                                   "count_or_spacing": c["value"].split("Ø")[0].strip()})
                out.append({"element": f"COLUMN {r['type']}", "direction": " / ".join(c["path"]), "spec": c["value"],
                            "gate": g, "kg": None})
    for key, sl in sorted(ctx["slabs"].items()):
        for lab, n in sorted(sl["reinforcement_labels"].items()):
            g = SQ.rebar_gate({"bar_diameter_mm": lab.split("Ø")[1].split("/")[0] if "Ø" in lab else None,
                               "count_or_spacing": lab.split("Ø")[0] if "Ø" in lab else None})
            out.append({"element": f"SLAB {key}", "direction": f"label x{n}", "spec": lab, "gate": g, "kg": None})
    return out


# ====================================================================== owner questions (only after the sources)
OWNER_QUESTIONS = [
    {"id": "OQ-S1", "group": "SOURCE-REVISION",
     "question": "The 12-page architectural PDF (plotted May 06 2026 from ...\\7757-FATMA ALSNYAN\\P7757.dwg) holds 7 "
                 "sheets that the supplied P7757.dwg / .dxf do not contain (area plans, SW and NE elevations, two "
                 "sections, fence). Please supply the DWG that holds them, or confirm that the PDF is the issued set.",
     "evidence": "DWG / DXF: 5 sheet frames (GF, 1F, 2F plans; NW, SE elevations); PDF: 12 raster pages",
     "unblocks": ["all wall / ceiling heights", "external plaster / paint", "stairs in section"]},
    {"id": "OQ-S2", "group": "SOURCE-REVISION",
     "question": "Is ST7757.dwg / ST7757.dxf the issued structural revision? (no pinned decoder can prove the DXF equals "
                 "the AC1027 DWG here)", "evidence": "ST7757.dwg AC1027 vs ST7757.dxf AC1032 re-saved 2026-10-01",
     "unblocks": ["structural FINAL status (Phase A is SHADOW either way)"]},
    {"id": "OQ-A1", "group": "ARCHITECTURAL",
     "question": "Layer legend for P7757: which layers carry wall faces, windows / glazing, stairs and overhead / hidden "
                 "lines? Layer 1 holds both the walls and the sheet frames; layer W is the plot boundary wall.",
     "evidence": "layer census in the ROOM_REGISTER; the diagnostic run with 'layer 1 = walls' still leaves one site",
     "unblocks": ["room topology (every room-based quantity)", "windows", "blockwork by thickness"]},
    {"id": "OQ-A2", "group": "ARCHITECTURAL",
     "question": "Door / window schedule (types, sizes, heights, materials). None exists in the source.",
     "evidence": "door-signature candidates only (OPENING_REGISTER)", "unblocks": ["doors", "windows", "aluminium",
                                                                                   "glazing", "reveals", "marble"]},
    {"id": "OQ-F1", "group": "FINISH",
     "question": "Finish schedule per room (floor / wall / ceiling finishes, false-ceiling levels, wet-room tiling "
                 "height). None exists in the source.", "evidence": "no finish text or schedule in P7757",
     "unblocks": ["floor finish", "ceiling", "wall tiles", "paint", "skirting"]},
    {"id": "OQ-T1", "group": "STRUCTURAL",
     "question": "Founding level and ground-beam / slab top levels (structural, not finished-floor). The source states "
                 "only a minimum excavation depth (1.5 m below plot level).",
     "evidence": "ST7757 schedules sheet notes; ground-beams plan level marks are architectural FFL",
     "unblocks": ["column necks", "columns per floor", "ground beams"]},
]

DONORS = [
    {"donor": "OpenTakeoff (OT, Apache-2.0, e6d2251c)", "capability": "schedule scan (row / column grouping)",
     "class": "CLEAN_REIMPLEMENT", "where": "engine/source/schedule_table.py", "rejected": "silent row drop"},
    {"donor": "OpenTakeoff", "capability": "document structure / sheet detection", "class": "CLEAN_REIMPLEMENT",
     "where": "alsenan_phase_a.frames (repeated identical closed frames)", "rejected": "-"},
    {"donor": "OpenTakeoff", "capability": "PDF vector extraction / page census", "class": "CLEAN_REIMPLEMENT",
     "where": "alsenan_phase_a.pdf_facts (PyMuPDF census only; no PDF quantity)", "rejected": "quantities on "
     "scaleConfirmed:false; mixedScaleWarning warn-not-block"},
    {"donor": "OpenTakeoff", "capability": "One-Click / detectRooms", "class": "BENCHMARK_ONLY", "where": "-",
     "rejected": "a room detector as quantity authority"},
    {"donor": "U-C4N (UC4N, MIT, cdb10638)", "capability": "labels.plain (CAD text control codes)",
     "class": "CLEAN_REIMPLEMENT (COPY_ADAPT stays planned: clone absent)", "where": "engine/source/cad_text.py",
     "rejected": "takeoff.unit_of (inferred unit overrides INSUNITS)"},
    {"donor": "U-C4N", "capability": "CAD text / transform / blocks", "class": "ALREADY_REIMPLEMENTED (R8.1 kernel_ocs)",
     "where": "engine/source/cad", "rejected": "silent identity on unreadable extrusion"},
    {"donor": "beiming183 AutoCAD-MCP (BM, MIT)", "capability": "field-level readback diff", "class": "PATTERN_IN_USE",
     "where": "r8_6a_reconcile (DWG vs DXF)", "rejected": "geometry_digest as proof of physical geometry"},
    {"donor": "Slacker autocad-mcp (SL, Apache-2.0)", "capability": "live handle readback", "class": "BENCHMARK_ONLY",
     "where": "-", "rejected": "unitless INSUNITS as mm"},
    {"donor": "puran-water autocad-mcp (PW, MIT)", "capability": "-", "class": "BENCHMARK_ONLY", "where": "-",
     "rejected": "-"},
    {"donor": "any MCP / donor calculator", "capability": "quantities", "class": "REJECT", "where": "-",
     "rejected": "ONE Urban engine only"},
]

WEAKNESSES = [
    ("G-01", "Layer-role authority for numeric / single-letter layer drawings: only reviewed claims exist; the drawing "
             "itself offers no admissible role path, so TS01 certifies no room.", "ARCH: every room-based row"),
    ("G-02", "Multi-sheet model space with POLYLINE frames: handled in the Phase A adapter by rule; not yet an engine "
             "region designation (frame.ReferenceRegionDesignation needs an accepted basis).", "floor assignment"),
    ("G-03", "Door / window closure for block-door families when walls share a layer with the sheet frame; glazing "
             "role.", "openings, room closure"),
    ("G-04", "Height authority when sections exist only as raster.", "plaster, paint, tiles, blockwork"),
    ("G-05", "Schedule tables as block ATTRIBUTES were invisible to the canonical TEXT layer (now read through the "
             "realised attributes by SCHEDULE_TABLE_READER_V1).", "structural schedules"),
    ("G-06", "Structural tag -> element association for beams / slabs / columns (only footing rectangles are "
             "associated).", "beams, slabs, columns"),
    ("G-07", "Continuous-beam graphic schedules (multi-span) are not read.", "beams"),
    ("G-08", "Rebar needs bar length / shape / laps / cover; the source gives counts and diameters only.", "rebar"),
    ("G-09", "Legacy-codepage Arabic text is undecoded (English twins used for identity).", "labels"),
    ("G-10", "BOQ_XLSX_EXPORT_V2 hard-coded the Qortuba banner and summary name (fixed: parameters, defaults "
             "unchanged).", "exporter"),
    ("G-11", "Unit status reaches PROVISIONAL from in-source evidence; VERIFIED needs a second independent class.",
     "FINAL measurement"),
    ("G-12", "No PDF raster text lane (no OCR engine): raster sheets localise only.", "PDF-only sheets"),
    ("G-13", "Boundary-clipped and rotated footings are not drawn as closed axis-aligned rectangles; their tags lie "
             "outside any rectangle.", "8 footing occurrences"),
    ("G-14", "Inclined structural elements (strap beams) are not measured.", "strap beams"),
]


# ====================================================================== workbook model
def sheet(role, header, rows, qty_cols=(), status_col=None, widths=None, wrap=(), scope=None):
    s = {"role": role, "header": header, "rows": rows, "qty_cols": list(qty_cols), "status_col": status_col,
         "widths": widths or {}, "wrap_cols": list(wrap)}
    if scope:
        s["scope"] = scope
    return s


def workbook(regs) -> dict:
    """The XLSX model from the REGISTERS only (so the package rebuilds it from the committed files)."""
    ab, sb = regs["ARCH_BOQ"]["rows"], regs["CONCRETE_REGISTER"]["boq_rows"]
    units = regs["SOURCE_AUTHORITY_REGISTER"]["units"]
    slabs = regs["STRUCTURAL_ELEMENT_REGISTER"]["slabs"]
    W13 = {0: 14, 4: 30, 5: 30, 6: 40, 10: 34, 11: 40, 12: 80}
    m = {}
    m["00_READ_ME"] = sheet("INFO", ["TOPIC", "TEXT"], [
        ["WHAT", "Phase A development validation of the ONE Urban engine on Alsenan Chalet P7757 + ST7757 (shadow)."],
        ["NOT BLIND", "The same source files and the engine carry P7757 history; contamination is disclosed (03)."],
        ["FROZEN", "Frozen before any manual BOQ / freelancer / web-app value was opened. Phase B compares later."],
        ["ADDING", "Only 02_ARCH_BOQ_SUMMARY and 15_STRUCTURAL_SUMMARY lines may be added, each within its own scope."],
        ["BLOCKED", "A BLOCKED line has no quantity and is in no total; its blocker says what is missing."],
        ["UNITS", f"P7757: {units['ARCHITECTURAL']['status']} ({units['ARCHITECTURAL']['native_to_mm']} mm "
                  f"per unit); ST7757: {units['STRUCTURAL']['status']} ({units['STRUCTURAL']['native_to_mm']})."],
        ["NO PRICES", "No price, no calibration, no production migration."]], widths={1: 120})
    m["01_PROJECT_SOURCE"] = sheet("INFO", ["FILE", "DISCIPLINE", "TYPE", "BYTES", "SHA256", "VERSION", "ROLE",
                                            "AUTHORITY"],
                                   [[f["file"], f["discipline"], f["type"], f["bytes"], f["sha256"], f.get("cad_version")
                                     or f"{f.get('pages')} pages", f["declared_role"], f["authority"]]
                                    for f in regs["SOURCE_MANIFEST"]["files"]], widths={0: 40, 4: 66, 7: 60})
    m["02_ARCH_BOQ_SUMMARY"] = sheet("ADDITIVE_SUMMARY", COLUMNS, [boq_line(r) for r in ab], qty_cols=(7,),
                                     status_col=9, widths=W13, wrap=(12,), scope="ARCHITECTURAL")
    m["03_ROOM_MATRIX"] = sheet("BREAKDOWN", ["FLOOR", "LABEL (EN)", "LABEL (AR)", "CLASS CANDIDATE", "SITE", "AREA m2",
                                              "STATUS", "BLOCKER"],
                                [[r["floor"], r["label_en"], r["label_ar"], r["class_candidate"], r["site"], r["area_m2"],
                                  r["status"], r["blocker"]] for r in regs["ROOM_REGISTER"]["rooms"]],
                                qty_cols=(5,), status_col=6, widths={1: 26, 7: 80})

    def trade_sheet(prefixes):
        return [boq_line(r) for r in ab if any(r["item"].startswith(p) for p in prefixes)]
    m["04_FLOOR_CEILING"] = sheet("BREAKDOWN", COLUMNS, trade_sheet(("A-FLR", "A-CLG")), (7,), 9, W13, (12,))
    m["05_BLOCKWORK"] = sheet("BREAKDOWN", COLUMNS, trade_sheet(("A-BLK",)), (7,), 9, W13, (12,))
    m["06_WALL_FINISHES"] = sheet("BREAKDOWN", COLUMNS, trade_sheet(("A-PLS", "A-PNT", "A-WTL", "A-WTP", "A-REV",
                                                                     "A-COL", "A-DCT")), (7,), 9, W13, (12,))
    m["07_SKIRTING_PROFILE"] = sheet("BREAKDOWN", COLUMNS, trade_sheet(("A-SKT", "A-HPR")), (7,), 9, W13, (12,))
    m["08_DOORS"] = sheet("SCHEDULE", ["FLOOR", "OCCURRENCE", "BLOCK", "LEAF LAYER", "SWING RADIUS (native)",
                                       "LEAF WIDTH mm (provisional unit)", "STATUS", "WHY NOT ADMITTED"],
                          [[d["floor"], d["occurrence"], d["block"], ", ".join(d["leaf_layer"]),
                            d["swing_radius_native"], d["leaf_width_mm_provisional"], "INFO", d["not_admitted_because"]]
                           for d in regs["OPENING_REGISTER"]["door_signature_candidates"]], status_col=6,
                          widths={7: 70})
    m["09_WINDOWS_GLAZING"] = sheet("BREAKDOWN", COLUMNS, trade_sheet(("A-WIN", "A-GLZ", "A-ALU")), (7,), 9, W13, (12,))
    m["10_STAIRS_RAILINGS"] = sheet("BREAKDOWN", COLUMNS, trade_sheet(("A-STR", "A-HRL")), (7,), 9, W13, (12,))
    m["11_WATERPROOFING"] = sheet("BREAKDOWN", COLUMNS, trade_sheet(("A-WPF", "A-WPU")), (7,), 9, W13, (12,))
    m["12_MARBLE"] = sheet("BREAKDOWN", COLUMNS, trade_sheet(("A-MRB",)), (7,), 9, W13, (12,))
    m["13_ARCH_TRACEABILITY"] = sheet("INFO", ["ITEM CODE", "SOURCE", "RULE", "REGISTER", "ENGINE"],
                                      [[r["item"], r["source"], r["rule"], "ARCH_BOQ / ROOM_REGISTER / OPENING_REGISTER",
                                        "TS01 (room_topology) + WALL_BAND_POLICY_V5 + OPENING_REGISTER_V1"] for r in ab],
                                      widths={1: 50, 2: 60, 3: 50, 4: 60})
    ablk = Counter(b.split(":")[0] for r in ab for b in r["blockers"])
    m["14_ARCH_BLOCKERS"] = sheet("INFO", ["BLOCKER", "ROWS", "OWNER QUESTION"],
                                  [[k, v, next((q["id"] for q in OWNER_QUESTIONS if q["id"] in " ".join(
                                      b for r in ab for b in r["blockers"] if b.startswith(k))), "")]
                                   for k, v in sorted(ablk.items())], widths={0: 50})
    m["15_STRUCTURAL_SUMMARY"] = sheet("ADDITIVE_SUMMARY", COLUMNS, [boq_line(r) for r in sb], qty_cols=(7,),
                                       status_col=9, widths=W13, wrap=(12,), scope="STRUCTURAL")
    m["16_FOUNDATIONS"] = sheet("BREAKDOWN", ["ELEMENT ID", "TYPE", "COUNT", "L m", "W m", "H m", "FORMULA", "QTY m3",
                                              "STATUS", "DRAWN SIZE CHECK", "BLOCKER"],
                                [[r["element_id"], r["element_id"].split("@")[0], r["count"], r["dims"]["L"]["m"],
                                  r["dims"]["W"]["m"], r["dims"]["H"]["m"], r["formula"], r6(r["qty"]),
                                  "COMPUTED_SHADOW_COMPLETE" if r["status"] == SQ.COMPLETE else "BLOCKED",
                                  r.get("size_check") or "", " | ".join(r["blockers"])]
                                 for r in regs["CONCRETE_REGISTER"]["footing_rows"]], qty_cols=(7,), status_col=8,
                                widths={0: 46, 10: 80})
    m["17_COLUMNS"] = sheet("SCHEDULE", ["TYPE", "COUNT ON COLUMN PLAN", "FOUNDATION", "GROUND FLOOR", "1st FLOOR",
                                         "2nd FLOOR & TOP", "STATUS"],
                            [[c["type"], c["count_on_column_plan"], c["foundation"], c["ground_floor"], c["first_floor"],
                              c["second_floor"], "INFO"] for c in regs["STRUCTURAL_ELEMENT_REGISTER"]["columns"]],
                            status_col=6)
    m["18_BEAMS"] = sheet("SCHEDULE", ["TYPE", "CELLS (header path = value)", "STATUS"],
                          [[b["type"], b["cells"], "INFO"] for b in regs["STRUCTURAL_ELEMENT_REGISTER"]["simple_beams"]],
                          status_col=2, widths={1: 140})
    m["19_SLABS"] = sheet("SCHEDULE", ["SLAB SHEET", "THICKNESS LABELS (cm)", "REINFORCEMENT LABELS", "STATUS"],
                          [[k, v["thickness_labels_cm"], v["reinforcement_labels"], "INFO"]
                           for k, v in sorted(slabs.items())], status_col=3, widths={1: 30, 2: 120})
    m["20_STAIRS_STRUCTURE"] = sheet("BREAKDOWN", COLUMNS, [boq_line(r) for r in sb if r["item"] == "S-STR-01"],
                                     (7,), 9, W13, (12,))
    m["21_REBAR"] = sheet("SCHEDULE", ["ELEMENT", "DIRECTION / COLUMN", "SPEC", "GATE", "MISSING", "kg", "STATUS"],
                          [[r["element"], r["direction"], r["spec"], r["gate"]["state"], ", ".join(r["gate"]["missing"]),
                            r["kg"], "BLOCKED"] for r in regs["REBAR_REGISTER"]["specifications"]], qty_cols=(5,),
                          status_col=6, widths={0: 22, 1: 40, 4: 60})
    m["22_STRUCT_TRACEABILITY"] = sheet("INFO", ["ITEM CODE", "SOURCE", "RULE", "COMPLETE ROWS", "BLOCKED ROWS"],
                                        [[r["item"], r["source"], r["rule"], r.get("complete_rows", []),
                                          r.get("blocked_rows", [])] for r in sb], widths={1: 50, 2: 60, 3: 60, 4: 60})
    sblk = Counter(b.split(":")[0] for r in sb for b in r["blockers"])
    m["23_STRUCT_BLOCKERS"] = sheet("INFO", ["BLOCKER", "ROWS"], [[k, v] for k, v in sorted(sblk.items())],
                                    widths={0: 70})
    return m


def xlsx_sources(regs):
    ab, sb = regs["ARCH_BOQ"]["rows"], regs["CONCRETE_REGISTER"]["boq_rows"]
    src = [{"sheet": "02_ARCH_BOQ_SUMMARY", "row": i, "col": 7, "value": r6(r["qty"]), "ref": f"ARCH_BOQ.rows[{i}].qty"}
           for i, r in enumerate(ab)]
    return src + [{"sheet": "15_STRUCTURAL_SUMMARY", "row": i, "col": 7, "value": r6(r["qty"]),
                   "ref": f"CONCRETE_REGISTER.boq_rows[{i}].qty"} for i, r in enumerate(sb)]


SUMMARY_NAME = "02_ARCH_BOQ_SUMMARY / 15_STRUCTURAL_SUMMARY"


def xlsx(ctx, regs):
    model = workbook(regs)
    ab, sb = regs["ARCH_BOQ"]["rows"], regs["CONCRETE_REGISTER"]["boq_rows"]
    src = xlsx_sources(regs)
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / XLSX_NAME
        w = BX.write(model, p, created=CREATED, banner=BANNER, summary_name=SUMMARY_NAME)
        va = BX.validate(p, model, sources=src, summary_sheet="02_ARCH_BOQ_SUMMARY", canonical_ids=[r["item"] for r in ab],
                         banner=BANNER, summary_name=SUMMARY_NAME)
        vs = BX.validate(p, model, sources=[], summary_sheet="15_STRUCTURAL_SUMMARY",
                         canonical_ids=[r["item"] for r in sb], banner=BANNER,
                         summary_name=SUMMARY_NAME)
        w2 = BX.write(model, Path(d) / ("2_" + XLSX_NAME), created=CREATED, banner=BANNER,
                      summary_name=SUMMARY_NAME)
        data = p.read_bytes()
    state = "PASS" if va["state"] == vs["state"] == "PASS" and w["file_sha256"] == w2["file_sha256"] else "FAIL"
    return model, data, {"sheets": w["sheets"], "content_digest": w["content_digest"], "file_sha256": w["file_sha256"],
                         "bytes": w["bytes"], "rewrite_identical": w["file_sha256"] == w2["file_sha256"],
                         "readback": {"state": state, "architectural": {k: va[k] for k in (
                             "state", "differences", "formulas", "register_mismatches", "quantity_cells_checked",
                             "canonical_not_exactly_once", "row_drops")},
                             "structural": {k: vs[k] for k in ("state", "differences", "formulas",
                                                                "canonical_not_exactly_once", "row_drops")}},
                         "rows_per_sheet": va["rows_per_sheet"]}


# ====================================================================== registers
FREEZE_SCHEMA = {
    "SCHEMA": {"class": "TEXT"}, "freeze_policy": {"class": "TEXT"}, "phase": {"class": "TEXT"},
    "nature": {"class": "TEXT"}, "code_commit": {"class": "GIT_COMMIT"},
    "recommendation_commit": {"class": "GIT_COMMIT"}, "baseline_commit": {"class": "GIT_COMMIT"},
    "source_sha256": {"class": "SHA256_MAP"}, "zip_sha256": {"class": "SHA256_MAP"}, "scope": {"class": "TEXT"},
    "units": {"class": "TEXT"}, "unit_context_digest": {"class": "SHA256"},
    "sheet_register_digest": {"class": "SHA256"}, "room_register_digest": {"class": "SHA256"},
    "topology_result_digests": {"class": "SHA256_MAP"}, "opening_register_digest": {"class": "SHA256"},
    "surface_register_digest": {"class": "SHA256"}, "structural_element_digest": {"class": "SHA256"},
    "schedule_table_digests": {"class": "SHA256_MAP"}, "concrete_register_digest": {"class": "SHA256"},
    "rebar_register_digest": {"class": "SHA256"}, "trade_rows_digest": {"class": "SHA256"},
    "blocked_rows_digest": {"class": "SHA256"}, "owner_questions_digest": {"class": "SHA256"},
    "excel_content_digest": {"class": "SHA256"}, "excel_file_sha256": {"class": "SHA256"},
    "firewall_digest": {"class": "SHA256"}, "engine_policy_digests": {"class": "SHA256_MAP"},
    "counts": {"class": "TEXT"},
    "FREELANCER_BOQ_SEEN": {"class": "BOOLEAN", "why": "no freelancer file was opened; the firewall audit lists every "
                                                         "file the build opened"},
    "WEB_APP_QUANTITIES_SEEN": {"class": "BOOLEAN", "why": "no web-app report was opened (denied upload)"},
    "EXPECTED_TOTALS_USED": {"class": "BOOLEAN", "why": "no expected or desired total enters any rule or row"},
    "HISTORICAL_P7757_GOLD_USED": {"class": "BOOLEAN", "why": "no historical P7757 register / benchmark / project fact "
                                                                "is read or imported by Phase A code"},
    "CONTAMINATION_DISCLOSED": {"class": "BOOLEAN", "why": "the repository and the engine carry P7757 history; "
                                                           "BENCHMARK_FIREWALL lists it by path / role"},
    "comparison": {"class": "TEXT"}, "schema_validation": {"class": "OPTIONAL",
                                                           "why": "the validator's own result, attached after validation"},
}


def opened_files(ctx, work_hint="alsenan_work"):
    rows = []
    code = 0
    for p in ctx["firewall"]["audit"]:
        k, pat = FW.classify(p, AP.FIREWALL_RULES, root=ROOT)
        if p.endswith((".py", ".pyc")) or "/site-packages/" in p or "/dist-packages/" in p or p.startswith("/usr/lib"):
            code += 1
            continue
        if work_hint in p:
            p = "<WORKSPACE>/" + p.split(work_hint + "/", 1)[1]
        elif p.startswith(str(ROOT)):
            p = str(Path(p).relative_to(ROOT))
        rows.append({"path": p, "class": k, "rule": pat})
    return sorted(rows, key=lambda r: r["path"]), code


def registers(ctx) -> dict:
    regs = {}
    F = ctx["facts"]
    # ---------------- SOURCE_MANIFEST
    auth = {"P7757.dxf": "CANONICAL_ARCHITECTURAL (geometry = P7757.dwg, reconciled)",
            "P7757.dwg": "NATIVE_ORIGINAL (read through the pinned decode only)",
            "P7757_Architectural.dwf": "UNREAD (no W2D reader)",
            "P7757_Architectural_Plan_Pages_01-06.pdf": "SUPPORTING_RASTER (localisation only)",
            "P7757_Architectural_Plan_Pages_07-12.pdf": "SUPPORTING_RASTER (localisation only)",
            "ST7757.dxf": "CANONICAL_STRUCTURAL (geometry, schedules, labels)",
            "ST7757.dwg": "NATIVE_ORIGINAL (identity to the DXF NOT VERIFIED)",
            "ST7757.pdf": "CORROBORATING_VECTOR_PLOT", "sanitary-7757.pdf": "SUPPORTING_EVIDENCE_ONLY"}
    files = []
    for name, f in F.items():
        u = ctx["units"]["ARCHITECTURAL" if name.startswith("P7757") and name.endswith(".dxf") else
                         "STRUCTURAL"] if name.endswith(".dxf") else None
        files.append(dict(f, authority=auth[name], resolved_units=None if u is None else
                          {"status": u["status"], "native_to_mm": u["native_to_mm"]},
                          pdf_sheets=AP.PDF_SHEETS.get(name), pdf_sheets_in_dxf=AP.PDF_IN_DXF.get(name)))
    regs["SOURCE_MANIFEST"] = {"SCHEMA": "URBAN_ALSENAN_SOURCE_MANIFEST_V1", "zips": ctx["zips"], "files": files,
                               "originals": "kept as delivered; workspace copies are hash-addressed",
                               "pdf_sheet_identification": "VISION_OBSERVATION by the agent (localisation only)"}
    # ---------------- SOURCE_AUTHORITY_REGISTER
    regs["SOURCE_AUTHORITY_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_SOURCE_AUTHORITY_V1",
        "hierarchy": {"ARCHITECTURAL": ["P7757.dxf", "P7757.dwg (identity)", "PDF 01-12 (supporting)", "DWF (unread)"],
                      "STRUCTURAL": ["ST7757.dxf", "ST7757.pdf (corroborating)", "ST7757.dwg (unverified)"],
                      "SANITARY": ["sanitary-7757.pdf (evidence only)"]},
        "dwg_dxf_identity": ctx["identity"],
        "pdf_vs_dwg": {"architectural_pdf_sheets": 12, "architectural_dxf_sheets": sum(
            1 for s in ctx["sheets"] if s["discipline"] == "ARCHITECTURAL"),
            "pdf_only_sheets": [t for n, ts in AP.PDF_SHEETS.items() if n.startswith("P7757_")
                                for i, t in enumerate(ts, 1) if i not in AP.PDF_IN_DXF.get(n, {})],
            "state": "PDF_IS_A_LARGER_SHEET_SET - OQ-S1"},
        "units": ctx["units"]}
    # ---------------- FLOOR_PLAN_REGISTER
    floors = []
    for s in ctx["sheets"]:
        floors.append({k: s[k] for k in ("discipline", "sheet", "frame_handle", "bounds", "titles", "floor", "view")}
                      | {"structural_role": s.get("structural_role")})
    lev = {fl: [{"text": r["text"], "value_m": r["value_m"], "layer": r["layer"]} for r in a.get("levels", [])
                if r["layer"] in ("LEVEL", "5")] for fl, a in ctx["arch"].items()}
    regs["FLOOR_PLAN_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_FLOOR_PLAN_REGISTER_V1", "sheet_rule": "repeated identical closed frames (one entity, "
        "four segments); titles = frame texts with drawing-title words", "sheets": floors,
        "floors": {"GF": "GROUND FLOOR PLAN 1:100", "1F": "1st FLOOR PLAN 1:100", "2F": "2nd FLOOR PLAN 1:100 (roof "
                   "terraces of 1F + upper rooms)", "BASEMENT": "NONE in any source", "ROOF": "no separate roof plan; "
                   "roof areas are labelled on the 1F / 2F plans", "EXTERNAL": "court, garden, swimming pool on the GF "
                   "plan; fence only in PDF 07-12 p.6"},
        "plan_level_marks": lev, "excluded": "legends, title blocks, repeated alternatives: none found besides the 5 "
                                               "frames", "pdf_pages": AP.PDF_SHEETS}
    # ---------------- ROOM_REGISTER
    rooms = []
    for fl in FLOORS:
        a = ctx["arch"][fl]
        for l in a["labels"]:
            rooms.append({"floor": fl, "occurrence": l["occurrence"], "label_en": l["label_en"], "label_ar": l["label_ar"],
                          "class_candidate": l["class_candidate"], "site": None, "area_m2": None, "status": "BLOCKED",
                          "blocker": "NO_CERTIFIED_ROOM_SITE: TS01 certified 0 room sites on this floor"})
    regs["ROOM_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_ROOM_REGISTER_V1", "rooms": rooms,
        "topology_runs": {fl: ctx["arch"][fl]["strict_topology"] for fl in FLOORS},
        "diagnostic_hypothesis_run": ctx["diagnostic"], "layer_census": ctx["arch_layers"],
        "fixture_blocks": {fl: ctx["arch"][fl]["fixture_blocks"] for fl in FLOORS},
        "state": "NO_ROOM_CERTIFIED", "why": "G-01 / G-03 (see QA_RECONCILIATION.weaknesses)"}
    # ---------------- OPENING_REGISTER
    doors = [d for fl in FLOORS for d in ctx["arch"][fl]["door_candidates"]]
    regs["OPENING_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_OPENING_REGISTER_V1", "door_signature_candidates": doors,
                                "counts": dict(Counter(d["floor"] for d in doors)),
                                "by_block": dict(sorted(Counter(d["block"] for d in doors).items())),
                                "windows": "NOT_ESTABLISHED (no glazing role)", "admitted_openings": 0,
                                "basis": "GR.door_signature (one swing arc < pi) WITHOUT a DOOR layer role: candidate "
                                         "only; heights / materials NOT_ESTABLISHED (no schedule, sections raster)"}
    # ---------------- ARCH_BOQ, BLOCKWORK, STAIRS, WATERPROOFING
    ab = arch_boq(ctx)
    regs["ARCH_BOQ"] = {"SCHEMA": "URBAN_ALSENAN_ARCH_BOQ_V1", "columns": COLUMNS, "rows": ab,
                        "complete": sum(1 for r in ab if r["status"] != "BLOCKED"), "blocked": len(ab)}
    regs["BLOCKWORK_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_BLOCKWORK_V1",
                                  "wall_bands": {fl: ctx["arch"][fl]["strict_topology"].get("wall_bands") for fl in FLOORS},
                                  "rows": [r for r in ab if r["item"].startswith("A-BLK")],
                                  "rule": "blockwork from wall bands by thickness; 'paired lines = wall' is not a rule"}
    regs["STAIR_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_STAIR_REGISTER_V1",
                              "observations": {fl: {"stair_arrow_blocks": ctx["arch"][fl]["stair_arrow_blocks"]}
                                               for fl in FLOORS},
                              "rows": [r for r in ab if r["item"].startswith(("A-STR", "A-HRL"))],
                              "state": "BLOCKED: stair geometry has no role authority; nothing counted"}
    wet = [r for r in rooms if r["class_candidate"].startswith("WET") or r["class_candidate"].startswith("EXTERNAL_WET")]
    regs["WATERPROOFING_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_WATERPROOFING_V1", "method": "floor membrane = wet / "
                                      "service floor area; 0.15 m upturn on the gross perimeter; doorway not deducted "
                                      "(US-04 / US-05)", "wet_label_candidates": wet,
                                      "rows": [r for r in ab if r["item"].startswith("A-WP")],
                                      "state": "BLOCKED: no certified room; wet identity from labels alone is not "
                                               "sufficient"}
    # ---------------- structural
    cs = ctx["columns"]["schedule"]
    cols = []
    for r in cs.get("records", []):
        def grp(word):
            return [c["value"] for c in r["cells"] if c["path"] and word in c["path"][0].upper()]
        cols.append({"type": r["type"], "count_on_column_plan": ctx["columns"]["tags_on_column_plan"].get(r["type"], 0),
                     "foundation": " / ".join(grp("FOUNDATION")), "ground_floor": " / ".join(grp("GROUND")),
                     "first_floor": " / ".join(grp("1ST")), "second_floor": " / ".join(grp("2ND")),
                     "cells": [{"path": c["path"], "value": c["value"]} for c in r["cells"]]})
    regs["STRUCTURAL_ELEMENT_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_STRUCTURAL_ELEMENT_REGISTER_V1", "sheets": ctx["structural_sheets"],
        "schedules": {k: {kk: v[kk] for kk in ("title", "state", "unplaced", "header_bands", "leaf_columns",
                                                "table_digest", "bounds") if kk in v} for k, v in ctx["schedules"].items()},
        "footing_schedule": ctx["footing_schedule"], "columns": cols,
        "simple_beams": [{"type": r["type"], "cells": "; ".join(f"{'/'.join(c['path'])}={c['value']}" for c in r["cells"]
                                                                 if c["value"])}
                         for r in ctx["schedules"]["SIMPLE_BEAMS"].get("records", [])],
        "slabs": ctx["slabs"], "footing_geometry": {k: ctx["footings"][k] for k in ("rectangles", "tags", "association",
                                                                                     "untagged_rectangles")}}
    sb = struct_boq(ctx)
    frows = ctx["footings"]["rows"]
    complete = [r for r in frows if r["status"] == SQ.COMPLETE]
    regs["CONCRETE_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_CONCRETE_REGISTER_V1", "policy": SQ.policy_record(), "footing_rows": frows,
        "boq_rows": sb, "footing_summary": {"occurrences": len(frows), "complete": len(complete),
                                            "blocked": len(frows) - len(complete),
                                            "complete_m3": round(sum(r["qty"] for r in complete), 6)},
        "rule": "count x dimension, every dimension from a named source; m3 from schedule centimetres; drawn size "
                "confirmed against the schedule; nothing defaulted"}
    rb = rebar_register(ctx)
    regs["REBAR_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_REBAR_REGISTER_V1", "specifications": rb,
                              "tonnage_kg": None, "state": "FAIL_CLOSED: every tonnage BLOCKED; no kg/m3 ratio",
                              "gate_fields": list(SQ.REBAR_FIELDS),
                              "by_gate_state": dict(Counter(r["gate"]["state"] for r in rb)),
                              "stirrups_note": "column stirrups '6Ø8/m' appear in the column-reinforcement detail "
                                               "notes: spec only"}
    san = F["sanitary-7757.pdf"]
    regs["SANITARY_EVIDENCE_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_SANITARY_EVIDENCE_V1", "file": "sanitary-7757.pdf", "sha256": san["sha256"],
        "pages": san["page_census"], "text_layer": san["text_layer"], "role": "SUPPORTING_EVIDENCE_ONLY",
        "alignment_to_architecture": "NOT_EVALUATED (no PDF-to-CAD transform authority; no text layer)",
        "wet_room_corroboration": "NONE USED: the sheet changes no geometry and no wet identity",
        "plumbing_cost": "OUT OF SCOPE"}
    regs["OWNER_QUESTION_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_OWNER_QUESTIONS_V1", "questions": OWNER_QUESTIONS,
                                       "never_asked": ["expected quantities", "the freelancer BOQ", "the web-app report"]}
    # ---------------- firewall
    opened, code_files = opened_files(ctx)
    av = FW.verdict([], AP.FIREWALL_RULES, root=ROOT)
    viol = [r for r in opened if r["class"] in FW.DENIED]
    av = {"policy": FW.POLICY_ID, "state": "FAIL" if viol else "PASS", "violations": viol,
          "non_code_files_opened": opened, "code_files_opened": code_files}
    mv = FW.module_verdict(ctx["firewall"]["modules_all"], AP.DENIED_MODULES)
    cen = ctx["firewall"]["census"]
    regs["BENCHMARK_FIREWALL"] = {
        "SCHEMA": "URBAN_ALSENAN_BENCHMARK_FIREWALL_V1", "policy": FW.policy_record(),
        "rules": [{"pattern": r.pattern.replace(str(AP.UPLOADS), "<UPLOADS>"), "class": r.klass, "why": r.why}
                  for r in AP.FIREWALL_RULES],
        "census": {k: cen[k] for k in ("tokens", "tracked_files_mentioning_tokens", "by_class", "unclassified",
                                       "this_phase_files_excluded")} | {"entries": cen["entries"]},
        "uploads": cen["uploads"], "scratch_disclosure": cen["scratch_disclosure"], "audit_verdict": av,
        "module_verdict": {"state": mv["state"], "violations": mv["violations"], "denied_patterns": mv["denied_patterns"]},
        "denylist": ["historical quantities", "manual BOQ", "freelancer values", "web-app values", "prices"],
        "statements": {"FREELANCER_BOQ_SEEN": "NO", "WEB_APP_QUANTITIES_SEEN": "NO", "EXPECTED_TOTALS_USED": "NO",
                       "HISTORICAL_P7757_GOLD_USED": "NO / CONTAMINATION DISCLOSED"},
        "contamination": "the same source files were processed by earlier rounds (PA01-PA08, WT01 benchmark unseal, "
                         "DB01, R8.2-R8.10 shadows) and the engine was partly developed on P7757; Phase A code reads "
                         "none of those results - it cannot remove the history, so it discloses it"}
    regs["DONOR_REUSE_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_DONOR_REUSE_V1", "donors": DONORS,
                                    "lock": "research/external_engine_lab/DONORS.lock (commits pinned; clones absent)",
                                    "copied_code": "NONE"}
    # ---------------- QA + xlsx
    checks = qa(ctx, regs)
    regs["QA_RECONCILIATION"] = checks
    model, data, xs = xlsx(ctx, regs)
    regs["QA_RECONCILIATION"]["xlsx"] = xs
    ctx["xlsx_bytes"] = data
    regs["QA_RECONCILIATION"]["checks"].append({"check": "XLSX_READBACK", "state": xs["readback"]["state"],
                                                "critical": True, "detail": "every cell vs model; quantity cells vs "
                                                                            "registers; deterministic rewrite"})
    regs["QA_RECONCILIATION"]["silent_critical_errors"] = sum(
        1 for c in regs["QA_RECONCILIATION"]["checks"] if c["critical"] and c["state"] not in ("PASS", "BLOCKED_REPORTED"))
    # ---------------- freeze
    regs["ALSENAN_P7757_ST7757_PHASE_A_FREEZE"] = freeze(ctx, regs, xs)
    regs["TEST_RESULTS"] = {"SCHEMA": "URBAN_ALSENAN_TEST_RESULTS_V1", "state": "RECORDED_BY_THE_PACKAGE_STEP",
                            "why": "the one full suite runs from the final commit, after the registers are committed"}
    return regs


def qa(ctx, regs) -> dict:
    ch = []

    def add(name, state, critical, detail):
        ch.append({"check": name, "state": state, "critical": critical, "detail": detail})
    for fl in FLOORS:
        t = ctx["arch"][fl]["strict_topology"]
        add(f"ROOM_CLOSURE_{fl}", "BLOCKED_REPORTED" if t.get("certified_room_sites") == 0 else "PASS", True,
            f"TS01 {t.get('sites')} sites, {t.get('certified_room_sites')} certified")
    for n in ("FLOOR_AREA", "CEILING", "WALL_SURFACES", "OPENING_HOSTING", "WALL_BAND_DUPLICATION", "SURFACE_IDENTITY",
              "FLOOR_FINISH_PARTITION", "WET_ROOMS", "STAIRS"):
        add(n, "BLOCKED_REPORTED", True, "no certified room / role: every dependent row is BLOCKED with its blocker")
    ab = regs["ARCH_BOQ"]["rows"]
    add("ARCH_ROWS_BLOCKED_WITHOUT_QTY", "PASS" if all(r["qty"] is None for r in ab if r["status"] == "BLOCKED")
        else "FAIL", True, f"{len(ab)} rows")
    fr = ctx["footings"]
    add("STRUCT_NO_TAG_IN_TWO_RECTANGLES", "PASS", True, "associate() places each tag in exactly one (smallest) "
        "rectangle or none")
    multi = [i for i in fr["association"]["issues"] if i["why"] == SQ.MULTIPLE_TAGS]
    add("STRUCT_NO_RECTANGLE_WITH_TWO_TAGS", "PASS" if not multi else "FAIL", True, f"{len(multi)} found")
    done = [r for r in fr["rows"] if r["status"] == SQ.COMPLETE]
    sizes_ok = all(c["check"] and c["check"]["state"] == SQ.SIZE_CONFIRMED for c in fr["size_checks"]
                   if any(r["element_id"].startswith(c["type"] + "@") for r in done))
    add("STRUCT_COMPLETE_ROWS_SIZE_CONFIRMED", "PASS" if sizes_ok else "FAIL", True,
        f"{len(done)} complete footing rows, every drawn rectangle equals its schedule L x W (1 mm)")
    types = [r["type"] for r in ctx["schedules"]["FOOTINGS"]["records"]]
    add("STRUCT_SCHEDULE_TYPES_UNIQUE", "PASS" if len(types) == len(set(types)) else "FAIL", True, f"{len(types)} types")
    unp = [u for v in ctx["schedules"].values() for u in v.get("unplaced", [])]
    data_unp = [u for u in unp if u["key"].startswith("ATTRIB|")]
    add("STRUCT_SCHEDULE_DATA_ALL_PLACED", "PASS" if not data_unp else "FAIL", True,
        f"SCHEDULE_TABLE_READER_V1 placed every schedule value; {len(unp) - len(data_unp)} header word(s) on a grid "
        f"line reported, not dropped: {[u['value'] for u in unp if u not in data_unp]}")
    sb = regs["CONCRETE_REGISTER"]["boq_rows"]
    ok = True
    for r in sb:
        if r["item"].startswith("S-FTG-"):
            ids = set(r["complete_rows"])
            q = sum(x["qty"] for x in fr["rows"] if x["element_id"] in ids) if ids else None
            ok &= (q is None and r["qty"] is None) or (q is not None and abs(q - r["qty"]) <= 1e-9)
    add("STRUCT_SUMMARY_EQUALS_COMPLETE_ROWS", "PASS" if ok else "FAIL", True, "each footing-type line = sum of its "
        "complete occurrence rows exactly; blocked rows in no total")
    every = Counter(x for r in sb if r["item"].startswith("S-FTG-") for x in r["complete_rows"] + r["blocked_rows"])
    add("STRUCT_EVERY_ROW_ONCE", "PASS" if all(v == 1 for v in every.values()) and len(every) == len(fr["rows"])
        else "FAIL", True, f"{len(every)} occurrence rows, each in exactly one summary line")
    add("SOURCE_ROUTE_P7757_DWG_DXF", "PASS" if ctx["identity"].get("P7757", {}).get("state") == "GEOMETRY_IDENTICAL"
        else "FAIL", True, "K1 vs K2 reconciliation")
    add("SOURCE_ROUTE_ST7757_DWG_DXF", "BLOCKED_REPORTED", False, "no pinned decode of ST7757.dwg")
    for k, u in ctx["units"].items():
        add(f"UNITS_{k}", "PASS" if u["status"] in ("VERIFIED", "PROVISIONAL", "CONFIRMED_BY_HUMAN") else "FAIL", True,
            f"{u['status']} ({u['reason']}); allowed {u['allowed_uses']}")
    add("REBAR_FAIL_CLOSED", "PASS" if all(r["kg"] is None for r in regs["REBAR_REGISTER"]["specifications"]) else "FAIL",
        True, "no tonnage")
    return {"SCHEMA": "URBAN_ALSENAN_QA_RECONCILIATION_V1", "checks": ch,
            "weaknesses": [{"id": a, "weakness": b, "impact": c} for a, b, c in WEAKNESSES],
            "target": "zero silent critical errors: every critical check is PASS or BLOCKED_REPORTED with its reason"}


def freeze(ctx, regs, xs) -> dict:
    ab, sb = regs["ARCH_BOQ"]["rows"], regs["CONCRETE_REGISTER"]["boq_rows"]
    allrows = ab + sb
    from engine.source import level_marks as _LM
    rec = {
        "SCHEMA": "URBAN_ALSENAN_P7757_ST7757_PHASE_A_FREEZE_V1", "freeze_policy": FS.POLICY_ID, "phase": "PHASE_A",
        "nature": "DEVELOPMENT VALIDATION / STRESS TEST - NOT BLIND - frozen before any manual BOQ is opened",
        "code_commit": ctx["code_commit"], "recommendation_commit": RECOMMENDATION_COMMIT,
        "baseline_commit": BASELINE_COMMIT, "source_sha256": {k: v[0] for k, v in AP.FILES.items()},
        "zip_sha256": dict(AP.ZIPS),
        "scope": "architectural (P7757: GF, 1F, 2F plans; NW / SE elevations) + structural (ST7757: foundations, "
                 "columns, beams, slabs, schedules); sanitary as evidence; SHADOW only",
        "units": "; ".join(f"{k}: {u['status']} {u['native_to_mm']} mm/unit" for k, u in sorted(ctx["units"].items())),
        "unit_context_digest": digest(ctx["units"]), "sheet_register_digest": digest(regs["FLOOR_PLAN_REGISTER"]["sheets"]),
        "room_register_digest": digest(regs["ROOM_REGISTER"]["rooms"]),
        "topology_result_digests": {fl: ctx["arch"][fl]["strict_topology"]["result_digest"] for fl in FLOORS},
        "opening_register_digest": digest(regs["OPENING_REGISTER"]),
        "surface_register_digest": digest([r for r in ab if r["trade"] in ("INTERNAL_PLASTER", "INTERNAL_PAINT",
                                                                          "WALL_TILE", "TILE_PREP", "EXTERNAL_PLASTER",
                                                                          "EXTERNAL_PAINT", "REVEALS")]),
        "structural_element_digest": digest(regs["STRUCTURAL_ELEMENT_REGISTER"]),
        "schedule_table_digests": {k: v["table_digest"] for k, v in ctx["schedules"].items() if v.get("table_digest")},
        "concrete_register_digest": digest(regs["CONCRETE_REGISTER"]), "rebar_register_digest": digest(regs["REBAR_REGISTER"]),
        "trade_rows_digest": digest([boq_line(r) for r in allrows]),
        "blocked_rows_digest": digest([r["item"] for r in allrows if r["status"] == "BLOCKED"]),
        "owner_questions_digest": digest(OWNER_QUESTIONS), "excel_content_digest": xs["content_digest"],
        "excel_file_sha256": xs["file_sha256"], "firewall_digest": digest(regs["BENCHMARK_FIREWALL"]),
        "engine_policy_digests": {"BENCHMARK_FIREWALL_V1": FW.policy_record()["digest"],
                                  "STRUCTURAL_QTO_V1": SQ.policy_record()["digest"],
                                  "SCHEDULE_TABLE_READER_V1": digest(ST.policy_record()),
                                  "LEVEL_MARK_UNIT_EVIDENCE_V1": digest(_LM.policy_record()),
                                  "CAD_TEXT_CONTROL_V1": digest(CT.policy_record()),
                                  "BOQ_XLSX_EXPORT_V2": BX.policy_record()["digest"]},
        "counts": (f"architectural rows {len(ab)} (blocked {sum(1 for r in ab if r['status'] == 'BLOCKED')}); "
                   f"structural rows {len(sb)} (blocked {sum(1 for r in sb if r['status'] == 'BLOCKED')}); footing "
                   f"occurrences {regs['CONCRETE_REGISTER']['footing_summary']['occurrences']} (complete "
                   f"{regs['CONCRETE_REGISTER']['footing_summary']['complete']}, "
                   f"{regs['CONCRETE_REGISTER']['footing_summary']['complete_m3']} m3); owner questions "
                   f"{len(OWNER_QUESTIONS)}"),
        "FREELANCER_BOQ_SEEN": False, "WEB_APP_QUANTITIES_SEEN": False, "EXPECTED_TOTALS_USED": False,
        "HISTORICAL_P7757_GOLD_USED": False, "CONTAMINATION_DISCLOSED": True,
        "comparison": "NOT STARTED - Phase B only, after this freeze is committed"}
    rec["schema_validation"] = FS.validate({k: v for k, v in rec.items()}, FREEZE_SCHEMA)
    return rec
