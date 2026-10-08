"""PRE-S8 - structural completeness audit, excavation to roof (2026-10-08). No kg is calculated and nothing frozen moves.

    python3 -I research/pre_s8_structural_completeness/build_pre_s8.py

Three passes, all over frozen Urban registers and the issued drawings:

B. Population census. Every structural family the brief names is searched for, never assumed: ST7757.dxf text (English
   and legacy-Arabic decoded) by sheet, the S1 census registers, the PRE-S7 panel census, the S1 project-rule register
   (pp.1-16) and the architectural P7757.dxf where a structural object is drawn only there. Every occurrence found
   gets one census row with the 14 brief fields.
C. Coverage against the existing Urban work:
   - stage ownership S3.1 / S4.1 (+D1.2) / S5.1 (+AD1, D1.1) / S6.1 (+D1.1) / S7 (+S7A);
   - concrete as recorded by the V3b BOQ lines and the coverage-recovery dashboard;
   - the rebar components and their states.
   Interfaces are audited for bars or concrete owned twice or by nobody.
D. Source exhaustion per S8 candidate. Each information channel is checked, and dimensioned evidence is kept apart
   from schematic / not-to-scale evidence. The output is the S8 readiness decision.

Blind: the builder reads no external reference quantity and no comparison register. Existing Urban
quantities are copied with their own state labels and never recombined into a new total; where two Urban registers
measure the same concrete, both are listed and the overlap is flagged, not summed.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "research" / "external_engine_lab"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import delta_release as DR  # noqa: E402
from engine.source import legacy_text as LT  # noqa: E402

ROUND = "PRE_S8"
QA_DATE = "2026-10-08"
POLICY = "PRE_S8_STRUCTURAL_COMPLETENESS_V1"
BASELINE_HEAD = "aeb8798"
R = ROOT / "research"
S1 = R / "alsenan_structural_census_s1"
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
ARCH_DXF = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
MANIFESTS = {"S4": R / "alsenan_footing_rebar_s4/S4_FREEZE_MANIFEST.json",
             "S4.1": R / "alsenan_footing_rebar_s4_1/S4_1_FREEZE_MANIFEST.json",
             "S5": R / "alsenan_ground_system_rebar_s5/S5_FREEZE_MANIFEST.json",
             "S5.1": R / "alsenan_ground_system_rebar_s5_1/S5_1_FREEZE_MANIFEST.json",
             "S6": R / "alsenan_superstructure_beam_rebar_s6/S6_FREEZE_MANIFEST.json",
             "S6.1": R / "alsenan_superstructure_beam_rebar_s6_1/S6_1_FREEZE_MANIFEST.json",
             "AD1": R / "ad1_authority_decisions/AD1_FREEZE_MANIFEST.json",
             "D1.1": R / "d1_1_stirrup_authority_audit/D1_1_FREEZE_MANIFEST.json",
             "D1.2": R / "d1_2_footing_cover_audit/D1_2_FREEZE_MANIFEST.json",
             "PRE-S7": R / "alsenan_slab_rebar_pre_s7/PRE_S7_FREEZE_MANIFEST.json",
             "PRE-S7.1": R / "alsenan_slab_rebar_pre_s7_1/PRE_S7_1_FREEZE_MANIFEST.json",
             "S7": R / "alsenan_slab_rebar_s7/12_S7_FREEZE_MANIFEST.json",
             "S7A": R / "alsenan_slab_rebar_s7a_qa/11_S7A_FREEZE_MANIFEST.json"}
S1_REGS = ["FOOTING_OCCURRENCE_REGISTER", "FOOTING_DEFINITION_REGISTER", "COLUMN_OCCURRENCE_REGISTER",
           "BEAM_OCCURRENCE_REGISTER", "SLAB_PANEL_REGISTER", "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER",
           "POOL_STRUCTURAL_REGISTER", "STRUCTURAL_PROJECT_RULE_REGISTER", "STRUCTURAL_LEVEL_REGISTER"]
P = {"s31_release": R / "alsenan_column_rebar_s3_1/COLUMN_RELEASE_REGISTER.json",
     "s31_index": R / "alsenan_column_rebar_s3_1/INDEX.json",
     "s31_summary": R / "alsenan_column_rebar_s3_1/COLUMN_REBAR_S3_1_SUMMARY.json",
     "s4_occ": R / "alsenan_footing_rebar_s4/FOOTING_REBAR_OCCURRENCES.csv",
     "s4_comp": R / "alsenan_footing_rebar_s4/FOOTING_REBAR_COMPONENTS.csv",
     "s5_occ": R / "alsenan_ground_system_rebar_s5/GROUND_SYSTEM_REBAR_OCCURRENCES.csv",
     "s6_occ": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCES.csv",
     "s6_cons": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OBJECT_CONSERVATION.csv",
     "pre7_census": R / "alsenan_slab_rebar_pre_s7/01_SLAB_PANEL_CENSUS.csv",
     "pre7_openings": R / "alsenan_slab_rebar_pre_s7/08_OPENING_REGISTER.csv",
     "pre7_conflicts": R / "alsenan_slab_rebar_pre_s7/11_SOURCE_CONFLICTS.csv",
     "p71_transfers": R / "alsenan_slab_rebar_pre_s7_1/02_OWNERSHIP_TRANSFERS.csv",
     "p71_conflicts": R / "alsenan_slab_rebar_pre_s7_1/09_REMAINING_CONFLICTS.csv",
     "s7_panels": R / "alsenan_slab_rebar_s7/05_S7_PANEL_SUMMARY.csv",
     "s7_blocked": R / "alsenan_slab_rebar_s7/02_S7_BLOCKED_ITEMS.csv",
     "s7_supports": R / "alsenan_slab_rebar_s7/06_S7_SUPPORT_SUMMARY.csv",
     "s7_summary": R / "alsenan_slab_rebar_s7/09_S7_PROJECT_SUMMARY.json",
     "s7a_summary": R / "alsenan_slab_rebar_s7a_qa/10_S7A_SUMMARY.json",
     "s7a_audit": R / "alsenan_slab_rebar_s7a_qa/08_END_CONDITION_AUDIT.csv",
     "d12_summary": R / "d1_2_footing_cover_audit/05_CORRECTED_RELEASE_SUMMARY.json",
     "srd_conflicts": R / "source_recovery_delta/10_PENDING_ENGINEER_CONFLICTS.csv",
     "v3b_boq": ROOT / "tests/alsenan/registers_v3b/BOQ_LINES_V3B.json",
     "cr_dashboard": R / "coverage_recovery_round/QUANTITY_COVERAGE_DASHBOARD.json"}
CODE = ["research/pre_s8_structural_completeness/build_pre_s8.py", "research/external_engine_lab/alsenan_structural_s1.py",
        "engine/source/legacy_text.py", "engine/source/delta_release.py"]
OUTPUTS = ["00_README.md", "01_FAMILY_POPULATION_SEARCH.csv", "02_STRUCTURAL_ELEMENT_CENSUS.csv",
           "03_CONCRETE_COVERAGE_MATRIX.csv", "04_REBAR_COVERAGE_MATRIX.csv", "05_STAGE_OWNERSHIP_REGISTER.csv",
           "06_S8_CANDIDATE_REGISTER.csv", "07_INTERFACE_DOUBLE_COUNT_AUDIT.csv", "08_SOURCE_CONFLICT_REGISTER.csv",
           "09_MISSING_REINFORCEMENT_COMPONENTS.csv", "10_S8_SOURCE_EXHAUSTION.csv", "11_S8_READINESS_DECISION.json",
           "12_PRE_S8_SUMMARY.json"]
MANIFEST_NAME = "13_PRE_S8_FREEZE_MANIFEST.json"
CENSUS_FIELDS = ["ELEMENT_ID", "ROW_KIND", "PARENT_ELEMENT", "ELEMENT_FAMILY", "FLOOR", "SOURCE_PAGE", "DXF_HANDLES", "PHYSICAL_GEOMETRY",
                 "CONCRETE_QUANTITY_STATE", "REBAR_COMPONENTS", "EXISTING_STAGE_OWNER", "NEW_S8_OWNER",
                 "S8_SCOPE", "SOURCE_AUTHORITY", "MISSING_INFORMATION", "CONFLICT", "QA_STATE", "SOURCE_REGISTER"]
ROW_KINDS = ("ELEMENT", "POPULATION_RECORD", "CONFLICT_CANDIDATE", "FACE_OF_ELEMENT", "COMPONENT_EVIDENCE",
             "TYPICAL_DETAIL_ONLY")
COUNTED_KINDS = ("ELEMENT", "POPULATION_RECORD", "CONFLICT_CANDIDATE")    # one physical element (or population) each
NO_S8 = "NONE (stays with the existing stage)"


class Stop(Exception):
    pass


def check(cond, what):
    if not cond:
        raise Stop(f"PRE-S8 STOP: {what}")


# ------------------------------------------------------------------ io helpers
def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _full(v):
    if v is None:
        return None
    s = f"{float(v):.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return _full(v)
    if isinstance(v, (list, tuple, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(name, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in fields})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def _json(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode())
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()[:16]


def _rel(p):
    return str(Path(p).relative_to(ROOT))


# ------------------------------------------------------------------ inputs
def verify_inputs():
    frozen = {k: DR.verify_frozen(m, ROOT) for k, m in MANIFESTS.items()}
    idx = _j(S1 / "INDEX.json")["registers"]
    for reg in S1_REGS:
        check(idx[reg]["sha256"] == _sha(S1 / f"{reg}.json"), f"S1 {reg} unchanged")
    s31 = _j(P["s31_index"])
    check(s31["outputs"]["COLUMN_RELEASE_REGISTER.json"] == _sha(P["s31_release"]), "S3.1 release register unchanged")
    check(s31["frozen_before_comparison"] is True, "S3.1 frozen before any comparison")
    out = {k: _j(m)["outputs"] for k, m in MANIFESTS.items()}
    for key, stage, name in (("s4_occ", "S4", "FOOTING_REBAR_OCCURRENCES.csv"),
                             ("s4_comp", "S4", "FOOTING_REBAR_COMPONENTS.csv"),
                             ("s5_occ", "S5", "GROUND_SYSTEM_REBAR_OCCURRENCES.csv"),
                             ("s6_occ", "S6", "SUPERSTRUCTURE_BEAM_OCCURRENCES.csv"),
                             ("s6_cons", "S6", "SUPERSTRUCTURE_BEAM_OBJECT_CONSERVATION.csv"),
                             ("pre7_census", "PRE-S7", "01_SLAB_PANEL_CENSUS.csv"),
                             ("pre7_openings", "PRE-S7", "08_OPENING_REGISTER.csv"),
                             ("pre7_conflicts", "PRE-S7", "11_SOURCE_CONFLICTS.csv"),
                             ("p71_transfers", "PRE-S7.1", "02_OWNERSHIP_TRANSFERS.csv"),
                             ("p71_conflicts", "PRE-S7.1", "09_REMAINING_CONFLICTS.csv"),
                             ("s7_panels", "S7", "05_S7_PANEL_SUMMARY.csv"),
                             ("s7_blocked", "S7", "02_S7_BLOCKED_ITEMS.csv"),
                             ("s7_supports", "S7", "06_S7_SUPPORT_SUMMARY.csv"),
                             ("s7_summary", "S7", "09_S7_PROJECT_SUMMARY.json"),
                             ("s7a_summary", "S7A", "10_S7A_SUMMARY.json"),
                             ("s7a_audit", "S7A", "08_END_CONDITION_AUDIT.csv"),
                             ("d12_summary", "D1.2", "05_CORRECTED_RELEASE_SUMMARY.json")):
        check(out[stage].get(name) == _sha(P[key]), f"{stage} {name} is the frozen output")
    check(_sha(DXF) == DXF_SHA and _sha(ARCH_DXF) == ARCH_SHA, "issued ST7757 / P7757 drawings unchanged")
    return frozen


# ------------------------------------------------------------------ B. population search in the drawing
FAMILY_SEARCH = [
    # family, English pattern, Arabic terms, S1 / register evidence key, PDF rule ids
    ("LEAN_BLINDING_CONCRETE", r"PLAIN\s+CONC|LEAN|BLINDING", ("خرسانة عادية", "نظافة"), "BLINDING",
     ["P8-N05", "P8-N06", "P8-N16", "P7-POOL"]),
    ("ISOLATED_FOOTING", r"^F\d{0,2}$|C\d{0,2}/F\d{0,2}|FN$", (), "FOOTING", ["P9-SOIL", "P13-FOOTING-TYP"]),
    ("COMBINED_FOOTING", r"COMBINED", (), "FOOTING_MULTI_COLUMN", ["P13-FOOTING-TYP"]),
    ("STRIP_FOOTING", r"STRIP\s+F|WALL\s+FOOT", (), None, []),
    ("RAFT_OR_PILE", r"\bRAFT\b|\bPILE\b|MAT\s+FOUND", ("لبشة", "خوازيق"), None, []),
    ("NECK_PEDESTAL", r"\bNECK\b|PEDESTAL", ("رقبة", "رقاب"), "COLUMN_FOUNDATION_STOREY", ["P13-FOOTING-DEEP"]),
    ("STARTER_DOWEL", r"STARTER|DOWEL", ("اشاير", "أشاير"), "S3_1_STARTER", ["P8-N09", "P13-FOOTING-TYP"]),
    ("STRAP_BEAM", r"^S\.?B\d$", (), "STRAP", []),
    ("GROUND_BEAM", r"GROUND\s+BEAM|^G\.?B\d*$", ("الشيناجات", "الشناجات"), "GROUND_BEAM",
     ["P13-GB-GT5", "P13-GB-LT5", "P13-GB-LT2_5", "P13-GB-EXT", "P1-NOTE-B"]),
    ("GROUND_SLAB", r"GROUND\s+SLAB|E\.W\.|S\.O\.G", ("بلاطة ارضية",), "GROUND_SLAB", ["P3-GROUND-SLAB"]),
    ("COLUMN", r"^C\d{0,2}$|^CN$", ("الاعمدة",), "COLUMN", ["P9-COL-TIES", "P9-COL-TMIN"]),
    ("SPECIAL_COLUMN", r"^T\.C$|^P\.C\b|^D\.C$", (), "SPECIAL_COLUMN", ["P15-TWISTED", "P15-PLANTED", "P3-LEGEND"]),
    ("STRUCTURAL_WALL", r"R\.?C\.?\s*WALL|STRUCTURAL\s+WALL|^B\.W$", ("حائط خرساني", "جدار خرساني"), "BEARING_WALL",
     ["P8-N20", "P3-LEGEND"]),
    ("RETAINING_WALL", r"RETAIN", ("ساند",), None, []),
    ("SHEAR_OR_CORE_WALL", r"SHEAR\s+WALL|CORE\s+WALL", (), None, []),
    ("BEAM", r"^B\d{1,2}$|^CB\d{1,2}$|^CA$", (), "BEAM", ["P11-12-CB-TYPICAL", "P10-SBT-REMARKS"]),
    ("ELEVATED_SLAB", r"^T\s?\d{2}$|SLAB", ("سقف",), "SLAB_PANEL", ["P8-N18", "P1-NOTE-A", "P4-6-NOTE-2"]),
    ("SUNKEN_SLAB_OR_STEP", r"SUNKEN|STEP", ("هابط",), "SUNKEN_SLAB", ["P3-LEGEND"]),
    ("CANTILEVER_OR_BALCONY", r"CANTILEVER|BALCON", ("كابولي", "بلكون", "البروزات"), "CANTILEVER", ["P3-LEGEND"]),
    ("STAIR_AND_LANDING", r"STAIR|LANDING", ("درج", "سلم"), "STAIR", ["P16-STAIR"]),
    ("LIFT_PIT_AND_WALLS", r"\bLIFT\b|ELEVATOR|^FF$", ("مصعد", "مصعددد"), "LIFT", ["P14-LIFT", "P8-N19"]),
    ("WATER_TANK", r"WATER\s+TANK|\bTANK\b", ("خزان",), "WATER_TANK", []),
    ("SWIMMING_POOL", r"SWIMMING|POOL", ("حمام سباحة", "مسبح"), "POOL", ["P7-POOL"]),
    ("DOME_OR_SPECIAL_ROOF", r"\bDOME\b", ("قبة",), "DOME", ["P7-DOME"]),
    ("RC_PARAPET", r"PARAPET", ("الدروة",), "PARAPET", ["P4-6-NOTE-1", "P14-PARAPETS"]),
    ("UPSTAND_OR_KERB", r"UPSTAND|\bKERB\b|\bCURB\b", (), None, []),
    ("EQUIPMENT_BASE_OR_PLINTH", r"EQUIP|PLINTH|MACHINE\s+BASE", ("قاعدة معدات",), None, []),
    ("OPENING_TRIM", r"\bVOID\b|OPENING|OPEN\s+TO\s+BELOW", ("منور", "فتحة"), "OPENING", ["P8-N04", "P16-BEAM-OPENING"]),
    ("LINTEL", r"LINTEL", ("عتب",), "LINTEL", ["P13-LINTEL"]),
    ("BOUNDARY_WALL", r"BOUNDARY|FENCE", ("سور",), "BOUNDARY_WALL", ["P14-BOUNDARY"]),
    ("RIBBED_OR_HORDI_SLAB", r"\bRIBS?\b|HORDI", ("هوردي",), "RIBBED", ["P16-RIBS"]),
    ("FOAM_CONCRETE", r"FOAM", ("فوم",), None, ["P3-LEGEND"]),
    ("STRUCTURAL_STEEL", r"\bHEA\b|\bHEB\b|\bIPE\b|\bUPN\b|STEEL\s+(BEAM|COL|SECTION)", (), None, []),
]
WORD_FALSE_POSITIVE = {"البحر"}          # 'the sea' / 'the span': not a structural family term


def dxf_texts():
    """Every TEXT / MTEXT / ATTRIB of ST7757.dxf with its sheet and its legacy-Arabic decoding."""
    import alsenan_structural_s1 as S
    src = S.Source()
    fam = {s.dxf.name: LT.font_family(s.dxf.font) for s in src.doc.styles}
    out = []

    def add(e, via):
        if e.dxftype() not in ("TEXT", "MTEXT", "ATTRIB"):
            return
        raw = e.dxf.text if e.dxftype() != "MTEXT" else e.text
        p = e.dxf.insert
        f = fam.get(e.dxf.get("style"))
        dec = LT.decode(raw, f)["text"] if f else raw
        sheet = src.sheet_of(p.x, p.y)
        out.append({"handle": e.dxf.handle or f"{via}>v", "via": via, "layer": e.dxf.layer,
                    "sheet": sheet or ("SCHEDULES_AND_NOTES" if p.y < 29036 else "OUTSIDE_FRAMES"),
                    "x": round(p.x), "y": round(p.y), "raw": (raw or "").strip(), "text": (dec or "").strip(),
                    "arabic": bool(f)})
    for e in src.msp:
        add(e, None)
        if e.dxftype() == "INSERT":
            for a in e.attribs:
                add(a, e.dxf.handle)
            try:
                for v in e.virtual_entities():
                    add(v, f"{e.dxf.handle}:{e.dxf.name}")
            except Exception:  # noqa: BLE001 - an unexplodable insert simply carries no text
                pass
    circles = []
    for e in src.msp.query("CIRCLE ARC"):
        if abs(2 * e.dxf.radius - 4422.2) <= 30:
            circles.append({"handle": e.dxf.handle, "type": e.dxftype(), "layer": e.dxf.layer,
                            "sheet": src.sheet_of(e.dxf.center.x, e.dxf.center.y),
                            "centre": [round(e.dxf.center.x), round(e.dxf.center.y)],
                            "diameter_mm": round(2 * e.dxf.radius, 1)})
    return out, circles, src


def arch_dome_circles():
    import ezdxf
    doc = ezdxf.readfile(str(ARCH_DXF))
    return [{"handle": e.dxf.handle, "layer": e.dxf.layer, "diameter_mm": round(2 * e.dxf.radius, 1),
             "centre": [round(e.dxf.center.x), round(e.dxf.center.y)]}
            for e in doc.modelspace().query("CIRCLE") if 2150 <= e.dxf.radius <= 2260]


def _ar_match(text, term):
    """A decoded-Arabic term matches as a whole word (with or without the article), never inside another word:
    'سور' (fence) is not a hit inside 'الجسور' (the beams)."""
    if " " in term:
        return term in text
    toks = re.findall(r"[\u0600-\u06FF]+", text)
    return any(t == term or t == "ال" + term or (term.startswith("ال") and t == term) for t in toks)


def search_hits(texts, pattern, arabic):
    rx = re.compile(pattern, re.I)
    hits = []
    for t in texts:
        s = t["text"]
        if t["arabic"]:
            if any(_ar_match(s, a) for a in arabic) and not any(w == s.strip() for w in WORD_FALSE_POSITIVE):
                hits.append(t)
        elif rx.search(s) or rx.search(t["raw"]):
            hits.append(t)
    return hits


# ------------------------------------------------------------------ C. existing Urban quantities
def v3b_concrete(boq):
    out = {}
    for ln in boq["lines"]:
        if ln["trade"] != "CONCRETE":
            continue
        t, c = ln["release"]["technical"], ln["release"]["commercial"]
        out[ln["code"]] = {"line_id": ln["line_id"], "level": ln["level"], "desc": ln["desc_en"],
                           "technical_class": t["class"], "technical_m3": t["qty"], "in_technical_total": t["in_total"],
                           "commercial_class": c["class"], "commercial_m3": c["qty"],
                           "commercial_provisional": c.get("provisional"), "formula": ln.get("formula"),
                           "details": ln.get("details") or []}
    return out


def _conc(v3, *codes):
    """A census concrete state from the V3b lines (technical layer first; a provisional commercial value is shown with
    its own label and never promoted)."""
    parts = []
    for c in codes:
        x = v3.get(c)
        if not x:
            continue
        s = f"V3b {x['line_id']} {c}: technical {x['technical_class']}"
        if x["technical_m3"] is not None:
            s += f" {x['technical_m3']:g} m3"
        if x["technical_m3"] is None and x["commercial_m3"] is not None:
            s += f" (commercial {x['commercial_class']} {x['commercial_m3']:g} m3, not technical)"
        parts.append(s)
    return "; ".join(parts) if parts else "NOT_MEASURED (no Urban concrete line)"


# ------------------------------------------------------------------ census builders per source
def footing_rows(S1d, s4occ, s4comp, v3):
    defs = {r["definition_id"]: r for r in S1d["FOOTING_DEFINITION_REGISTER"]}
    by_outline = {r["outline"]: r for r in s4occ}
    comps = defaultdict(list)
    for c in s4comp:
        comps[c["occurrence_id"]].append(c)
    det = Counter(d["ref"] for d in v3["C-FTG"]["details"])
    s1types = Counter(r["type"] for r in S1d["FOOTING_OCCURRENCE_REGISTER"] if r["type"])
    check(all(det[t] == n for t, n in s1types.items()), "V3b footing details match the S1 footing types")
    rows = []
    for f in S1d["FOOTING_OCCURRENCE_REGISTER"]:
        o = by_outline.get(f["outline"]["handle"])
        check(o is not None, f"S4 occurrence for {f['footing_id']}")
        cs = comps[o["occurrence_id"]]
        d = defs.get(f"FDEF-{f['type']}") if f["type"] else None
        ncol = len(f.get("supported_columns") or [])
        fam = "LIFT_FOOTING (lift base FF)" if f["type"] == "FF" else (
            "COMBINED_FOOTING" if ncol > 1 else "ISOLATED_FOOTING")
        geo = (f"L {d['L_cm']:g} x W {d['W_cm']:g} x D {d['source_row']['raw_attributes']['DEPHT']} cm (schedule)"
               if d else "outline drawn; two schedule definitions (F / F10)")
        conflict = "F / F10: one drawn outline, two schedule definitions" if not f["type"] else ""
        cstate = (_conc(v3, "C-FTG") if f["type"] else _conc(v3, "C-FTG-FF10"))
        comp = sorted({f"{c['component']}:{c['state']}" for c in cs})
        rows.append({
            "ELEMENT_ID": f["footing_id"], "ELEMENT_FAMILY": fam, "FLOOR": "FOUNDATION",
            "SOURCE_PAGE": "2 (plan); 9 (schedule); 13 (typical detail)",
            "DXF_HANDLES": [f["outline"]["handle"], (f.get("tag") or {}).get("handle")],
            "PHYSICAL_GEOMETRY": geo + f"; supports {ncol} column(s)",
            "CONCRETE_QUANTITY_STATE": cstate, "REBAR_COMPONENTS": comp,
            "EXISTING_STAGE_OWNER": f"S4.1 ({o['occurrence_id']} {o['release_state']}; D1.2 cover authority)",
            "NEW_S8_OWNER": NO_S8,
            "SOURCE_AUTHORITY": "PROJECT_SOURCE (plan outline + schedule row)",
            "MISSING_INFORMATION": ("BOXED bar meaning; founding level" if any(c["component"] == "BOXED" and
                                                                              c["state"] == "BLOCKED_UNQUANTIFIED"
                                                                              for c in cs) else "founding level")
            + ("; the lift walls on FF are the S8 LIFT element SPC-LIFT_PIT" if f["type"] == "FF" else ""),
            "CONFLICT": conflict, "QA_STATE": "COUNTED_OWNED" if f["type"] else "COUNTED_SOURCE_CONFLICT",
            "SOURCE_REGISTER": "S1 FOOTING_OCCURRENCE_REGISTER + S4 FOOTING_REBAR_OCCURRENCES"})
    return rows


def column_rows(S1d, s31, v3, special):
    by_occ = defaultdict(list)
    for r in s31["rows"]:
        by_occ[r["occurrence_id"]].append(r)
    spec_chain = defaultdict(list)
    for s in special:
        if s.get("bound_chain"):
            spec_chain[s["bound_chain"]].append(s["kind"])
    floor_line = {"GF": ("C-COL-GF", "C-COL-GF-RES", "C-JNT-GF"), "1F": ("C-COL-1F", "C-COL-1F-RES", "C-JNT-1F"),
                  "2F": ("C-COL-2F", "C-COL-2F-RES", "C-JNT-2F"), "FOUNDATION": ("C-NECK",)}
    rows = []
    for c in S1d["COLUMN_OCCURRENCE_REGISTER"]:
        parts = by_occ.get(c["column_id"], [])
        check(parts, f"S3.1 owns {c['column_id']}")
        fl = c["floor"]
        fam = "NECK_PEDESTAL (foundation storey of the column chain)" if fl == "FOUNDATION" else "COLUMN"
        if spec_chain.get(c["chain_id"]) and fl == "GF":
            fam = f"COLUMN ({'/'.join(sorted(set(spec_chain[c['chain_id']])))} bound)"
        comp = sorted({f"{r['component']}:{r['release_state']}" for r in parts})
        rows.append({
            "ELEMENT_ID": c["column_id"], "ELEMENT_FAMILY": fam, "FLOOR": fl,
            "SOURCE_PAGE": "1-6 (plans); 9 (schedule)", "DXF_HANDLES": (c.get("plan_source") or {}).get("handles"),
            "PHYSICAL_GEOMETRY": f"{c.get('column_type')} section {c.get('drawn_section_cm')} cm (drawn), "
                                 f"schedule {c.get('schedule_section_cm')}",
            "CONCRETE_QUANTITY_STATE": _conc(v3, *floor_line.get(fl, ())) + (
                "; CR COLUMNS_AND_JOINTS: foundation interval is a lower bound (founding level not printed)"
                if fl == "FOUNDATION" else ""),
            "REBAR_COMPONENTS": comp, "EXISTING_STAGE_OWNER": "S3.1 (columns, all storeys incl. the foundation "
                                                              "storey / neck)",
            "NEW_S8_OWNER": NO_S8,
            "SOURCE_AUTHORITY": "PROJECT_SOURCE (plan outline + type tag + schedule)",
            "MISSING_INFORMATION": "founding level / neck height" if fl == "FOUNDATION" else (
                "special extras are the SPC component rows (S8)" if "bound" in fam else ""),
            "CONFLICT": "" if c.get("drawn_vs_schedule") in (None, "MATCH") else f"drawn vs schedule: "
                                                                                   f"{c.get('drawn_vs_schedule')}",
            "QA_STATE": "COUNTED_OWNED", "SOURCE_REGISTER": "S1 COLUMN_OCCURRENCE_REGISTER + S3.1 COLUMN_RELEASE"})
    return rows


def ground_rows(s5occ, v3):
    rows = []
    for g in s5occ:
        strap = g["family"] == "STRAP_BEAM"
        det = json.loads(g["detail_ids"] or "[]")
        has_ext = any("EXTERIOR" in d for d in det)
        has_int = any(d.startswith("P13-GB-LT") or d.startswith("P13-GB-GT") for d in det)
        ext = has_ext and not has_int
        fam = "STRAP_BEAM" if strap else (
            "GROUND_BEAM (exterior, depth FOLLOW ARCH.)" if ext else
            "GROUND_BEAM (exterior / interior detail conflict)" if has_ext else
            "GROUND_BEAM (interior)")
        rows.append({
            "ELEMENT_ID": g["occurrence_id"], "ELEMENT_FAMILY": fam, "FLOOR": "FOUNDATION / GROUND",
            "SOURCE_PAGE": "2 (straps) / 3 (ground beams); 13 (sections)",
            "DXF_HANDLES": json.loads(g["geometry_handles"]) if g["geometry_handles"].startswith("[") else
            g["geometry_handles"],
            "PHYSICAL_GEOMETRY": f"{g['mark'] or ''} clear {g['member_clear_concrete_length_m']} m x "
                                 f"{g['width_mm']} x {g['depth_mm'] or '?'} mm ({g['depth_state']})",
            "CONCRETE_QUANTITY_STATE": _conc(v3, "C-STR") if strap else _conc(
                v3, *(("C-GB-EXT",) if ext else ("C-GB-INT", "C-GB-EXT") if has_ext else ("C-GB-INT",))),
            "REBAR_COMPONENTS": sorted(f"{k}:{v}" for k, v in json.loads(g["components_by_state"]).items()),
            "EXISTING_STAGE_OWNER": f"S5.1 ({g['occurrence_state']}; AD1 + D1.1 corrections)",
            "NEW_S8_OWNER": NO_S8, "SOURCE_AUTHORITY": "PROJECT_SOURCE (plan linework + p.13 section by length)",
            "MISSING_INFORMATION": g["why_not_resolved"] or "",
            "CONFLICT": f"detail candidates {det}" if (has_ext and has_int) or g["depth_state"] in (
                "SOURCE_CONFLICT", "CANDIDATE_CONFLICT") else "",
            "QA_STATE": "COUNTED_OWNED", "SOURCE_REGISTER": "S5 GROUND_SYSTEM_REBAR_OCCURRENCES"})
    return rows


DOME_RING_ARCS = {f"ARC:FFRS:BA00{i}" for i in range(3, 9)}


def beam_rows(s6occ, v3):
    line = {"GF_ROOF": ("C-BEAM-GF", "C-BEAM-GF-RES"), "1F_ROOF": ("C-BEAM-1F", "C-BEAM-1F-RES"),
            "2F_ROOF": ("C-BEAM-2F",)}
    rows = []
    for b in s6occ:
        ring = b["occurrence_id"] in DOME_RING_ARCS
        fam = "DOME_RING_BEAM (S1 DOME_RING arc, untagged in S6)" if ring else (
            "CANTILEVER_BEAM (CA)" if b["mark"] == "CA" else f"BEAM ({b['subfamily']})")
        rows.append({
            "ELEMENT_ID": b["occurrence_id"], "ELEMENT_FAMILY": fam, "FLOOR": b["floor"],
            "SOURCE_PAGE": "4-6 (plans); 10-12 (schedules)",
            "DXF_HANDLES": json.loads(b["geometry_handles"]) if b["geometry_handles"].startswith("[") else
            b["geometry_handles"],
            "PHYSICAL_GEOMETRY": f"{b['mark'] or 'untagged'} drawn width {b['drawn_width_mm']} mm, schedule width "
                                 f"{b['schedule_width_mm'] or '?'}",
            "CONCRETE_QUANTITY_STATE": (_conc(v3, "C-DOME-RING-12EB", "C-DOME-RING-2F33") if ring else
                                        _conc(v3, *line.get(b["floor"], ())[:1]) if b["occurrence_state"] ==
                                        "LOWER_BOUND" else _conc(v3, *line.get(b["floor"], ())[-1:])),
            "REBAR_COMPONENTS": sorted(f"{k}:{v}" for k, v in json.loads(b["components_by_state"]).items()),
            "EXISTING_STAGE_OWNER": f"S6.1 ({b['occurrence_state']}; D1.1 corrections)",
            "NEW_S8_OWNER": "S8 DOME (ring beam per DETAIL OF DOME) - ownership transfer from S6 required"
            if ring else NO_S8,
            "SOURCE_AUTHORITY": "PROJECT_SOURCE (plan band + tag + schedule)" if b["mark"] else
            "PROJECT_GEOMETRY (band without tag)",
            "MISSING_INFORMATION": b["occurrence_blocking_reason"] or "",
            "CONFLICT": "S6 untagged beam vs DETAIL OF DOME ring beam (same object, two potential owners)" if ring
            else "", "QA_STATE": "COUNTED_OWNED_TRANSFER_PENDING" if ring else "COUNTED_OWNED",
            "SOURCE_REGISTER": "S6 SUPERSTRUCTURE_BEAM_OCCURRENCES"})
    return rows


PANEL_FAMILY = {"NORMAL_SLAB": "ELEVATED_SLAB", "SUNKEN_SLAB": "SUNKEN_SLAB",
                "DOME_ZONE": "DOME (slab face inside the dome circle)", "STAIR_FLIGHT_ZONE": "STAIR_AND_LANDING",
                "DENSE_HATCH_CANTILEVER_OR_BEARING_WALL": "CANTILEVER_OR_BEARING_WALL_BAND",
                "WATER_TANK_PLACE_SLAB": "WATER_TANK_SUPPORT_SLAB", "STAIR_IN_VOID_ZONE": "STAIR_IN_LIGHT_WELL",
                "OPEN_TO_BELOW": "OPENING (void)", "OUTSIDE_BUILDING_OR_COURT": None}


def slab_rows(census, s7p, transfers, v3, parents):
    s7 = {r["PANEL_ID"]: r for r in s7p}
    tr = defaultdict(list)
    for t in transfers:
        tr[t["object_id"]].append(t["region"])
    line = {"GF_ROOF_SLAB": "C-SLAB-GF", "1F_ROOF_SLAB": "C-SLAB-1F", "2F_ROOF_SLAB": "C-SLAB-2F"}
    rows, skipped = [], []
    for c in census:
        fam = PANEL_FAMILY.get(c["PANEL_CLASS"], f"UNKNOWN ({c['PANEL_CLASS']})")
        if fam is None:
            skipped.append(c["SLAB_PANEL_ID"])
            continue
        p = s7.get(c["SLAB_PANEL_ID"], {})
        owner = ("S7 (bottom mesh + note-2 top over supports; PROJECT_BASIS_QTO)" if c["SCOPE"] == "IN_SCOPE_S7"
                 else f"none - S7 {c['SCOPE']}")
        s8 = NO_S8
        if c["PANEL_CLASS"] == "SUNKEN_SLAB":
            s8 = "S8 sunken step / edge extras / level-change detail (base mesh stays with S7)"
        elif c["SCOPE"] != "IN_SCOPE_S7" and c["PANEL_CLASS"] != "OPEN_TO_BELOW":
            s8 = f"S8 {fam}"
        elif c["PANEL_CLASS"] == "OPEN_TO_BELOW":
            s8 = "S8 OPENING_TRIM (trim / diagonal bars: NONE_DRAWN)"
        par = parents.get(c["SLAB_PANEL_ID"], "")
        rows.append({
            "ELEMENT_ID": c["SLAB_PANEL_ID"], "ROW_KIND": "FACE_OF_ELEMENT" if par else "ELEMENT",
            "PARENT_ELEMENT": par, "ELEMENT_FAMILY": fam, "FLOOR": c["FLOOR"],
            "SOURCE_PAGE": {"GFRS": "4", "FFRS": "5", "SFRS": "6"}.get(c["SOURCE_SHEET"], c["SOURCE_SHEET"]),
            "DXF_HANDLES": json.loads(c["BOUNDARY_HANDLES"])[:12],
            "PHYSICAL_GEOMETRY": f"{c['GEOMETRIC_AREA_M2']} m2, t {c['THICKNESS_MM'] or '?'} mm "
                                 f"({c['THICKNESS_AUTHORITY']})",
            "CONCRETE_QUANTITY_STATE": (_conc(v3, line[c["FLOOR"]]) + "; CR SLABS OFFICIAL")
            if c["PANEL_CLASS"] in ("NORMAL_SLAB", "SUNKEN_SLAB") else (
                "DEDUCTION (void)" if c["PANEL_CLASS"] == "OPEN_TO_BELOW" else
                (_conc(v3, "C-DOME-SHELL-12EB", "C-DOME-SHELL-2F33") if c["PANEL_CLASS"] == "DOME_ZONE" else
                 _conc(v3, "C-STAIR") if "STAIR" in c["PANEL_CLASS"] else
                 "NOT_ITEMISED (inside the V3b slab plate or not measured; not established)")),
            "REBAR_COMPONENTS": {"released_items": p.get("RELEASED_ITEMS_OWNED"), "panel_owned_kg_S7":
                                 p.get("PANEL_OWNED_KG"), "blocked_categories": p.get("BLOCKED_CATEGORIES")},
            "EXISTING_STAGE_OWNER": owner, "NEW_S8_OWNER": s8,
            "SOURCE_AUTHORITY": "PROJECT_GEOMETRY (slab face) + plan bar tokens",
            "MISSING_INFORMATION": c["SCOPE_REASON"] if c["SCOPE"] != "IN_SCOPE_S7" else "",
            "CONFLICT": c["CONFLICT"] or "", "QA_STATE": "COUNTED_OWNED" if c["SCOPE"] == "IN_SCOPE_S7" else
            "COUNTED_S8_CANDIDATE" if s8 != NO_S8 else "COUNTED_NOT_STRUCTURAL",
            "SOURCE_REGISTER": "PRE-S7 01_SLAB_PANEL_CENSUS + S7 05_S7_PANEL_SUMMARY"
            + (f" + PRE-S7.1 transfers {sorted(set(tr[c['SLAB_PANEL_ID']]))}" if tr.get(c["SLAB_PANEL_ID"]) else "")})
    return rows, skipped


def ground_slab_rows(S1d, v3, parents):
    rows = []
    for p in S1d["SLAB_PANEL_REGISTER"]:
        if p["sheet"] != "GBP" or p["class"] == "OUTSIDE_BUILDING_OR_COURT":
            continue
        stair = p["class"] == "STAIR_FLIGHT_ZONE"
        t = p.get("effective_thickness_mm")
        par = parents.get(p["panel_id"], "SPC-GROUND_SLAB" if not stair else "")
        rows.append({
            "ELEMENT_ID": p["panel_id"], "ROW_KIND": "FACE_OF_ELEMENT" if par else "ELEMENT", "PARENT_ELEMENT": par,
            "ELEMENT_FAMILY": "STAIR_AND_LANDING (ground flight)" if stair else
            "GROUND_SLAB (cell)", "FLOOR": "GROUND", "SOURCE_PAGE": "3",
            "DXF_HANDLES": p["boundary_handles"][:12],
            "PHYSICAL_GEOMETRY": f"{p['area_m2']} m2, t {t or '?'} mm ({p.get('thickness_authority')})",
            "CONCRETE_QUANTITY_STATE": _conc(v3, "C-STAIR") if stair else (
                _conc(v3, "C-GSLAB-ZONE-1", "C-GSLAB-ZONE-2") + "; CR GROUND_SLAB coverage 53.1 % (T=10 printed in "
                                                               "two zones only)"),
            "REBAR_COMPONENTS": ["MESH 5Ø10/m E.W. (P3-GROUND-SLAB, two printed zones):NOT_IN_S3_S7",
                                 "V3b R-GROUND_SLAB-GF DERIVED (pre-S stage, not a S3-S7 release)"]
            if not stair else ["P16 stair bars:NOT_QUANTIFIED"],
            "EXISTING_STAGE_OWNER": "none (no S3-S7 stage)", "NEW_S8_OWNER": "S8 GROUND_SLAB" if not stair else
            "S8 STAIR",
            "SOURCE_AUTHORITY": "PROJECT_GEOMETRY (cell) + PROJECT_SOURCE note (two zones)",
            "MISSING_INFORMATION": "" if t else "thickness / mesh not printed for this cell",
            "CONFLICT": "", "QA_STATE": "COUNTED_S8_CANDIDATE", "SOURCE_REGISTER": "S1 SLAB_PANEL_REGISTER (GBP)"})
    return rows


SPECIAL_MAP = {  # kind -> (family, page, s8 owner, v3b codes, missing)
    "TURN_COLUMN": ("SPECIAL_COLUMN (twisted)", "4; 15", "S8 SPECIAL_COLUMN extras (4Ø16 + spiral 6Ø8/m x 2 m)",
                    (), "extra-bar lengths at the floor (1 m above / below printed; anchorage not)"),
    "DEAD_COLUMN": ("SPECIAL_COLUMN (dead)", "4", "S8 SPECIAL_COLUMN (termination detail)", (),
                    "termination detail of a dead column not drawn"),
    "PLANTED_COLUMN": ("SPECIAL_COLUMN (planted)", "4-5; 15", "S8 SPECIAL_COLUMN (column + 4Ø16 support bars)", (),
                       "planted column height / schedule row; the carrying beam extra is partly in S6.1"),
    "STAIR_FLIGHT": ("STAIR_AND_LANDING", "3-5; 16", "S8 STAIR", ("C-STAIR",),
                     "waist thickness, riser height, landing levels per flight"),
    "STAIR_BEAM": ("STAIR_BEAM", "4-5; 10", NO_S8, (), ""),
    "LIFT_PIT": ("LIFT_PIT_AND_WALLS", "2; 9 (FF); 14", "S8 LIFT", (),
                 "pit depth ('As Per Lift Manufactures recommendations'), wall plan outline, wall height"),
    "LIFT_TIE_BEAM": ("LIFT_TIE_BEAM (conditional)", "8 note 19", "S8 LIFT (only if the storey height > 4.30 m)", (),
                      "storey heights at the lift; tie-beam section"),
    "LINTEL_POPULATION": ("LINTEL", "13 schedule; architectural openings", "S8 LINTEL",
                          ("C-LINT-GF", "C-LINT-1F", "C-LINT-2F"), "opening register binding (architectural)"),
    "BOUNDARY_WALL": ("BOUNDARY_WALL (RC columns 20x30, GB 20x40, pads 130x80x30)", "14", "S8 BOUNDARY_WALL",
                      ("C-BWALL",), "column / pad spacing on a plan; B.W schedule row not bound to a run"),
    "PARAPET": ("RC_PARAPET", "4-6 note 1; 14", "S8 PARAPET", (),
                "parapet run and height (architectural); RC vs masonry not stated per run"),
    "WATER_TANK_SLAB": ("WATER_TANK_SUPPORT_SLAB", "6", "S8 WATER_TANK", (), "tank walls absent; slab region only"),
    "DOME": ("DOME_OR_SPECIAL_ROOF", "5; 7", "S8 DOME", ("C-DOME-SHELL-12EB", "C-DOME-SHELL-2F33",
                                                       "C-DOME-RING-12EB", "C-DOME-RING-2F33"),
             "ring-beam depth 'AS PER ARCH'; shell bar anchorage into the ring"),
    "SWIMMING_POOL": ("SWIMMING_POOL (base + walls)", "3; 7", "S8 POOL", ("C-POOL", "C-POOL-BLD"),
                      "pool bar lengths from an N.I.S. detail (two depths)"),
    "GROUND_SLAB": ("GROUND_SLAB (population record)", "3", "S8 GROUND_SLAB", ("C-GSLAB-ZONE-1", "C-GSLAB-ZONE-2"),
                    "thickness / mesh outside the two printed zones"),
    "SLAB_CORNER_BARS": ("SLAB_CORNER_BARS", "4-6 legend", "S7.1 / S8 (corner groups blocked in S7)", (),
                         "corner bar length and count per corner"),
    "BEAM_OPENING": ("BEAM_OPENING_DETAIL (typical only)", "16", "none (no occurrence marked)", (),
                     "no opening in a beam is marked on any plan"),
    "CASEMENT_DETAIL": ("BEAM_IN_CASEMENT (typical only)", "15", "none (no occurrence marked)", (),
                        "no occurrence marked"),
    "RIBBED_SLAB": ("RIBBED_OR_HORDI_SLAB (typical only)", "16", "none (no occurrence marked)", (),
                    "no rib / hordi slab on any plan"),
    "SECTION_DETAIL_CALLOUT": (None, "", "", (), "")}


KIND_ROW = {"BEAM_OPENING": "TYPICAL_DETAIL_ONLY", "CASEMENT_DETAIL": "TYPICAL_DETAIL_ONLY",
            "RIBBED_SLAB": "TYPICAL_DETAIL_ONLY", "LINTEL_POPULATION": "POPULATION_RECORD",
            "BOUNDARY_WALL": "POPULATION_RECORD", "PARAPET": "POPULATION_RECORD", "SLAB_CORNER_BARS": "COMPONENT_EVIDENCE",
            "STAIR_BEAM": "COMPONENT_EVIDENCE", "GROUND_SLAB": "ELEMENT"}


def special_rows(S1d, v3, s6occ):
    col_by_chain = defaultdict(list)
    for c in S1d["COLUMN_OCCURRENCE_REGISTER"]:
        col_by_chain[c["chain_id"]].append(c)
    s6_by_tag = {}
    for b in s6occ:
        for h in json.loads(b["tag_handles"] or "[]"):
            s6_by_tag[h] = b["occurrence_id"]
    parapet = next(r for r in S1d["STRUCTURAL_PROJECT_RULE_REGISTER"] if r["rule_id"] == "P14-PARAPETS")
    rows = []
    for s in S1d["SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER"]:
        fam, page, s8, codes, missing = SPECIAL_MAP[s["kind"]]
        if fam is None:
            continue
        kind, parent = KIND_ROW.get(s["kind"], "ELEMENT"), ""
        if s["kind"] == "STAIR_BEAM":
            parent = s6_by_tag.get(s.get("tag_handle"), "")
            check(parent, f"stair beam {s['special_id']} has its S6 occurrence")
        elif s["kind"] in ("TURN_COLUMN", "DEAD_COLUMN", "PLANTED_COLUMN"):
            chain = col_by_chain.get(s.get("bound_chain"), [])
            gf = [c for c in chain if c["floor"] == "GF"] or chain
            if gf:
                kind, parent = "COMPONENT_EVIDENCE", gf[0]["column_id"]
        elif s["kind"] == "SLAB_CORNER_BARS":
            parent = "S7 slab population (CORNER_GROUP)"
        owner = {"STAIR_BEAM": "S6.1 (stair-qualified beam tag)", "SLAB_CORNER_BARS": "S7 (CORNER_GROUP blocked)",
                 "PLANTED_COLUMN": "S6.1 carrying-beam extra (planted_column_extra delta) / column not in S3.1"
                 }.get(s["kind"], "none (no S3-S7 stage)")
        rcomp = [f"rule {s.get('rule')}: {s.get('rule_status') or 'see rule register'}"]
        if s["kind"] == "PARAPET":
            rcomp = [f"P14 parapet sections ({parapet['raw_text'][:110]}):NOT_QUANTIFIED"]
        rows.append({
            "ELEMENT_ID": s["special_id"], "ROW_KIND": kind, "PARENT_ELEMENT": parent, "ELEMENT_FAMILY": fam,
            "FLOOR": s.get("floor") or "ALL",
            "SOURCE_PAGE": page, "DXF_HANDLES": [s.get("source_id")] if s.get("source_id") else [],
            "PHYSICAL_GEOMETRY": s.get("label") or s.get("note") or "",
            "CONCRETE_QUANTITY_STATE": _conc(v3, *codes) if codes else "NOT_MEASURED (no Urban concrete line)",
            "REBAR_COMPONENTS": rcomp,
            "EXISTING_STAGE_OWNER": owner, "NEW_S8_OWNER": s8,
            "SOURCE_AUTHORITY": f"S1 {s['terminal_state']}", "MISSING_INFORMATION": missing,
            "CONFLICT": "", "QA_STATE": "TYPICAL_DETAIL_ONLY" if s["terminal_state"] == "NOT_IN_SCOPE" else
            ("COUNTED_S8_CANDIDATE" if s8.startswith("S8") else "COUNTED_OWNED"),
            "SOURCE_REGISTER": "S1 SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER"})
    return rows


def search_rows(texts, struct_circles, arch_circles, v3, S1d, footings):
    """Occurrences the population search found that no earlier register owns as an element."""
    rows = []
    blind = [t for t in texts if re.search(r"PLAIN\s+CONC", t["text"], re.I)]
    rows.append({
        "ELEMENT_ID": "PS8-BLINDING-UNDER-FOOTINGS", "ROW_KIND": "POPULATION_RECORD", "PARENT_ELEMENT": "",
        "ELEMENT_FAMILY": "LEAN_BLINDING_CONCRETE", "FLOOR": "FOUNDATION",
        "SOURCE_PAGE": "8 notes 5, 6, 16; 7 (pool: '10cm PLAIN CONCRETE')",
        "DXF_HANDLES": [t["handle"] for t in blind],
        "PHYSICAL_GEOMETRY": "10 cm plain concrete printed on the pool detail only; under footings / ground beams "
                             "the extent is not printed",
        "CONCRETE_QUANTITY_STATE": _conc(v3, "C-BLD-F", "C-BLD-GB", "C-BLD-FULL", "C-POOL-BLD"),
        "REBAR_COMPONENTS": ["NONE (plain concrete)"], "EXISTING_STAGE_OWNER": "none (concrete only; no rebar stage)",
        "NEW_S8_OWNER": "concrete register only (no S8 rebar)", "SOURCE_AUTHORITY": "PROJECT_SOURCE notes (mix, "
                                                                                  "strength); extent OWNER fact",
        "MISSING_INFORMATION": "blinding extent and thickness under footings / ground beams not printed",
        "CONFLICT": "V3b blinding per footing (REVIEW) and full-footprint blinding (OWNER_PROJECT_FACT) measure the "
                    "same layer two ways: never sum them",
        "QA_STATE": "PREVIOUSLY_UNREGISTERED_IN_S_STAGES (concrete only; V3b lines exist)",
        "SOURCE_REGISTER": "population search (DXF) + V3b BOQ lines"})
    ff = [f for f in footings if f["ELEMENT_FAMILY"].startswith("LIFT_FOOTING")]
    lift_txt = [t for t in texts if "مصعد" in t["text"] or "مصعددد" in t["text"]]
    rows.append({
        "ELEMENT_ID": "PS8-LIFT-WALLS", "ROW_KIND": "COMPONENT_EVIDENCE", "PARENT_ELEMENT": "SPC-LIFT_PIT",
        "ELEMENT_FAMILY": "LIFT_PIT_AND_WALLS (walls 20 cm)", "FLOOR": "FOUNDATION",
        "SOURCE_PAGE": "9 (FF row remark 'lift base'); 14 (DETAIL OF LIFT WITH ISOLATED FOOTING)",
        "DXF_HANDLES": [t["handle"] for t in lift_txt] + [h for f in ff for h in f["DXF_HANDLES"] if h],
        "PHYSICAL_GEOMETRY": "walls 20 cm on the FF footing (460 x 450 x 55); plan outline of the shaft not drawn; "
                             "pit depth per the lift manufacturer",
        "CONCRETE_QUANTITY_STATE": "NOT_MEASURED (no Urban concrete line)",
        "REBAR_COMPONENTS": ["P14 walls 6Ø12/m + 6Ø16/m, 2Ø16, 2Ø12:NOT_QUANTIFIED"],
        "EXISTING_STAGE_OWNER": "none", "NEW_S8_OWNER": "S8 LIFT",
        "SOURCE_AUTHORITY": "PROJECT_SOURCE typical detail (p.14) + schedule remark (decoded Arabic)",
        "MISSING_INFORMATION": "shaft plan outline, pit depth, wall height", "CONFLICT": "",
        "QA_STATE": "NEW_EVIDENCE_LOCATION_BOUND (the S1 LIFT_PIT had no plan location: FF footing + schedule "
                    "remark bind it)", "SOURCE_REGISTER": "population search (DXF 1C64 + p.14)"})
    s_ffrs = [c for c in struct_circles if c["sheet"] == "FFRS"]
    a_tower = [c for c in arch_circles if abs(c["diameter_mm"] - 4410) < 5]
    rows.append({
        "ELEMENT_ID": "PS8-DOME-TOWER-ARCH-ONLY", "ROW_KIND": "CONFLICT_CANDIDATE", "PARENT_ELEMENT": "",
        "ELEMENT_FAMILY": "DOME_OR_SPECIAL_ROOF (tower roof, +13.90)",
        "FLOOR": "2F_ROOF", "SOURCE_PAGE": "architectural P7757 (plan circle); structural p.6 shows a flat panel",
        "DXF_HANDLES": [f"P7757:{c['handle']}" for c in a_tower],
        "PHYSICAL_GEOMETRY": f"architectural plan circle {a_tower[0]['diameter_mm'] if a_tower else '?'} mm; the "
                             "structural 2F roof has SP-2F_ROOF_SLAB-04 (flat, 160 mm) at that place",
        "CONCRETE_QUANTITY_STATE": _conc(v3, "C-DOME-SHELL-1300", "C-DOME-RING-1300"),
        "REBAR_COMPONENTS": ["DETAIL OF DOME (if it applies):NOT_ESTABLISHED"],
        "EXISTING_STAGE_OWNER": "S7 releases the flat panel SP-2F_ROOF_SLAB-04 at that place",
        "NEW_S8_OWNER": "S8 DOME only if the structural engineer confirms an RC dome there",
        "SOURCE_AUTHORITY": "ARCHITECTURAL drawing only (no structural occurrence)",
        "MISSING_INFORMATION": "whether the tower dome is structural RC, and what it sits on",
        "CONFLICT": f"architecture shows {len(arch_circles)} dome circles, the structural slab sheets "
                    f"{len(s_ffrs)} (FFRS); the third (tower) is not on any structural plan",
        "QA_STATE": "SOURCE_CONFLICT_PREVIOUSLY_UNREGISTERED", "SOURCE_REGISTER": "population search (P7757 + ST7757)"})
    return rows


# ------------------------------------------------------------------ C. coverage matrices
FAMILY_GROUP = [("LEAN_BLINDING", "LEAN_BLINDING_CONCRETE"), ("FOOTING", "FOOTING"), ("NECK", "NECK_PEDESTAL"),
                ("STRAP", "STRAP_BEAM"), ("GROUND_BEAM", "GROUND_BEAM"), ("GROUND_SLAB", "GROUND_SLAB"),
                ("COLUMN", "COLUMN"), ("SPECIAL_COLUMN", "SPECIAL_COLUMN"), ("BEAM", "BEAM"),
                ("DOME_RING", "DOME_RING_BEAM"), ("STAIR_BEAM", "STAIR_BEAM"), ("CANTILEVER", "CANTILEVER"),
                ("ELEVATED_SLAB", "ELEVATED_SLAB"), ("SUNKEN", "SUNKEN_SLAB"), ("STAIR", "STAIR"),
                ("LIFT", "LIFT"), ("TANK", "WATER_TANK"), ("POOL", "SWIMMING_POOL"), ("DOME", "DOME"),
                ("PARAPET", "PARAPET"), ("LINTEL", "LINTEL"), ("BOUNDARY", "BOUNDARY_WALL"),
                ("OPENING", "OPENING"), ("CORNER", "SLAB_CORNER_BARS"), ("TYPICAL_ONLY", "(typical only)")]


def family_group(fam):
    f = fam.upper()
    for key, label in (("TYPICAL ONLY", "TYPICAL_ONLY"), ("BLINDING", "LEAN_BLINDING_CONCRETE"),
                       ("LIFT", "LIFT"), ("FOOTING", "FOOTING"), ("NECK", "NECK_PEDESTAL"), ("STRAP", "STRAP_BEAM"),
                       ("GROUND_BEAM", "GROUND_BEAM"), ("GROUND_SLAB", "GROUND_SLAB"), ("DOME_RING", "DOME_RING_BEAM"),
                       ("DOME", "DOME"), ("SPECIAL_COLUMN", "SPECIAL_COLUMN"), ("STAIR_BEAM", "STAIR_BEAM"),
                       ("STAIR", "STAIR_AND_LANDING"), ("CANTILEVER", "CANTILEVER_OR_BEARING_WALL"),
                       ("SUNKEN", "SUNKEN_SLAB"), ("WATER_TANK", "WATER_TANK"), ("POOL", "SWIMMING_POOL"),
                       ("PARAPET", "RC_PARAPET"), ("LINTEL", "LINTEL"), ("BOUNDARY", "BOUNDARY_WALL"),
                       ("OPENING", "OPENING_TRIM"), ("CORNER", "SLAB_CORNER_BARS"), ("CASEMENT", "TYPICAL_ONLY"),
                       ("RIBBED", "TYPICAL_ONLY"), ("COLUMN", "COLUMN"), ("BEAM", "BEAM"),
                       ("ELEVATED_SLAB", "ELEVATED_SLAB")):
        if key in f:
            return label
    return "OTHER"


def concrete_matrix(census, v3, cr):
    cr_by = {r["trade"]: r for r in cr["rows"]}
    agg = defaultdict(lambda: {"n": 0, "states": Counter(), "lines": set()})
    for r in census:
        if r["ROW_KIND"] in ("COMPONENT_EVIDENCE", "TYPICAL_DETAIL_ONLY"):
            continue
        g = family_group(r["ELEMENT_FAMILY"])
        a = agg[(g, r["FLOOR"])]
        a["n"] += 1
        st = r["CONCRETE_QUANTITY_STATE"]
        cls = set(re.findall(r"technical (\w+)", st))
        good, part = cls & {"DERIVED", "OWNER_PROJECT_FACT"}, cls & {"PARTIAL"}
        bad = cls - {"DERIVED", "OWNER_PROJECT_FACT", "PARTIAL"}
        key = ("NOT_MEASURED" if st.startswith("NOT_MEASURED") else "DEDUCTION" if st.startswith("DEDUCTION") else
               "NOT_ITEMISED" if st.startswith("NOT_ITEMISED") else
               "MEASURED" if good and not part and not bad else
               "MEASURED_PARTIAL_LINE" if part and not bad else
               "MIXED_LINES (measured + blocked)" if (good or part) and bad else "BLOCKED")
        a["states"][key] += 1
        a["lines"].update(re.findall(r"V3b (B\d{4}) (\S+?):", st))
    cr_map = {"GROUND_BEAM": "GROUND_BEAMS", "GROUND_SLAB": "GROUND_SLAB", "COLUMN": "COLUMNS_AND_JOINTS",
              "NECK_PEDESTAL": "COLUMNS_AND_JOINTS", "BEAM": "BEAMS", "ELEVATED_SLAB": "SLABS",
              "SUNKEN_SLAB": "SLABS"}
    rows = []
    for (g, fl), a in sorted(agg.items()):
        lines = sorted(a["lines"])
        tech = [v3[c] for _, c in lines if c in v3]
        crr = cr_by.get(cr_map.get(g, ""))
        rows.append({"FAMILY": g, "FLOOR": fl, "ELEMENTS": a["n"], "ELEMENT_STATES": dict(a["states"]),
                     "URBAN_LINES": [f"{lid} {c}" for lid, c in lines],
                     "V3B_LINE_TECHNICAL_M3_SHARED": sum(x["technical_m3"] or 0.0 for x in tech) if tech else None,
                     "V3B_TECHNICAL_CLASSES": sorted({x["technical_class"] for x in tech}),
                     "V3B_LINE_COMMERCIAL_PROVISIONAL_M3_SHARED": sum(x["commercial_m3"] or 0.0 for x in tech
                                                          if x["technical_m3"] is None) if tech else None,
                     "CR_TRADE": crr["trade"] if crr else None,
                     "CR_VERIFIED_LOWER_BEST_M3": [crr["verified"], crr["lower_bound"], crr["best_provisional"]]
                     if crr else None,
                     "COVERAGE_STATE": "DEDUCTION_ONLY" if set(a["states"]) <= {"DEDUCTION"} else
                     "MEASURED" if set(a["states"]) <= {"MEASURED"} else
                     "MEASURED_PARTIAL" if set(a["states"]) <= {"MEASURED", "MEASURED_PARTIAL_LINE", "DEDUCTION"} else
                     "NOT_MEASURED" if set(a["states"]) <= {"NOT_MEASURED", "NOT_ITEMISED"} else
                     "BLOCKED" if set(a["states"]) <= {"BLOCKED"} else "PARTIAL_OR_BLOCKED",
                     "NOTE": "V3b line quantities are per family / floor (several rows can share one line); they are "
                             "copied, never re-summed across overlapping lines"})
    return rows


def rebar_matrix(census, s31, s7sum, d12, s7a):
    by_comp = defaultdict(lambda: {"elements": 0, "states": Counter(), "owner": set()})
    for r in census:
        g = family_group(r["ELEMENT_FAMILY"])
        comps = r["REBAR_COMPONENTS"]
        if isinstance(comps, dict):
            comps = [f"S7_RELEASED_ITEMS:{comps.get('released_items') or 0}",
                     f"S7_BLOCKED:{comps.get('blocked_categories') or ''}"]
        for c in comps or []:
            name, _, state = str(c).rpartition(":")
            k = (g, name or c)
            by_comp[k]["elements"] += 1
            by_comp[k]["states"][state or "?"] += 1
            by_comp[k]["owner"].add(r["EXISTING_STAGE_OWNER"].split(" ")[0])
    rows = []
    for (g, comp), a in sorted(by_comp.items()):
        st = set(a["states"])
        released = st & {"VERIFIED", "LOWER_BOUND", "PROVISIONAL", "BLOCKED_MODELLED"}
        blocked = st & {"BLOCKED_UNQUANTIFIED", "BLOCKED", "NOT_QUANTIFIED", "NOT_ESTABLISHED", "NOT_IN_S3_S7"}
        rows.append({"FAMILY": g, "COMPONENT": comp, "ELEMENTS": a["elements"], "STATES": dict(a["states"]),
                     "OWNERS": sorted(a["owner"]),
                     "COVERAGE": "RELEASED" if released and not blocked else "PARTIAL" if released and blocked else
                     "UNQUANTIFIED" if blocked else "NOT_APPLICABLE_OR_NOT_REQUIRED" if st <= {
                         "NOT_APPLICABLE", "NOT_REQUIRED"} else "OWNED_ELSEWHERE_OR_OTHER"})
    t31 = s31["totals_kg"]
    stage = [{"STAGE": "S3.1", "SCOPE": "columns, all storeys incl. foundation storey (necks)",
              "KG": t31["total"], "KG_BY_STATE": {k: t31[k] for k in ("verified", "lower_bound", "provisional",
                                                                         "blocked")},
              "NOTE": "verified / lower bound / provisional / blocked-modelled are separate states"},
             {"STAGE": "S4.1 (+D1.2)", "SCOPE": "footings", "KG": d12["combined"]["parts"]["S4.1"]["project_basis_kg"],
              "KG_BY_STATE": {"PROJECT_BASIS": d12["combined"]["parts"]["S4.1"]["project_basis_kg"]},
              "NOTE": "D1.2: minimum cover makes the straight run a project-basis value, not a lower bound"},
             {"STAGE": "S5.1 (+AD1, D1.1)", "SCOPE": "ground beams + strap beams",
              "KG": d12["combined"]["parts"]["S5.1"]["project_basis_kg"], "KG_BY_STATE": {
                  "PROJECT_BASIS": d12["combined"]["parts"]["S5.1"]["project_basis_kg"]}, "NOTE": ""},
             {"STAGE": "S6.1 (+D1.1)", "SCOPE": "superstructure beams (simple + continuous)",
              "KG": d12["combined"]["parts"]["S6.1"]["project_basis_kg"], "KG_BY_STATE": {
                  "PROJECT_BASIS": d12["combined"]["parts"]["S6.1"]["project_basis_kg"]}, "NOTE": ""},
             {"STAGE": "S7 (+S7A errata)", "SCOPE": "elevated slabs, 476 candidates",
              "KG": s7sum["totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"],
              "KG_BY_STATE": {"PROJECT_BASIS_QTO": s7sum["totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"]},
              "NOTE": "S7A: not a proven bound; top-extent readings move the top steel "
                      f"{s7a['scenario_range_top_extension_kg'][0]:g} - {s7a['scenario_range_top_extension_kg'][1]:g} "
                      "kg (sensitivity only)"}]
    return rows, stage


# ------------------------------------------------------------------ interfaces, conflicts, missing components
def interfaces(census, s7a_audit, s7sup):
    fam_tags = defaultdict(int)
    for r in census:
        fam_tags[family_group(r["ELEMENT_FAMILY"])] += 1
    cant = [x for x in s7sup if x["BEARING_WALL_CANDIDATE_BAND"] == "True"]
    cant_kg = sum(float(x["TOP_EXTENSION_KG"] or 0) + float(x["TOP_CROSSING_KG"] or 0) for x in cant)
    stair = [a for a in s7a_audit if "STAIR" in a["UNRESOLVED_REASON"]]
    stair_kg = sum(float(a["S7_TOP_EXTENSION_KG_AT_END"]) for a in stair)
    dome = [a for a in s7a_audit if "DOME" in a["UNRESOLVED_REASON"]]
    dome_kg = sum(float(a["S7_TOP_EXTENSION_KG_AT_END"]) for a in dome)
    tank = [a for a in s7a_audit if "WATER_TANK" in a["UNRESOLVED_REASON"]]
    tank_kg = sum(float(a["S7_TOP_EXTENSION_KG_AT_END"]) for a in tank)
    return [
        {"INTERFACE": "FOOTING -> STARTER -> COLUMN", "SIDE_A": "S4.1 footing (STARTER_DOWEL_REFERENCE: "
         "NOT_APPLICABLE in all 26)", "SIDE_B": "S3.1 column STARTER component (foundation storey)",
         "CONCRETE": "footing L x W x D vs neck from the footing top: no overlap by construction",
         "BARS_OWNED": "ONCE (S3.1)", "RISK": "BOXED bars (21 footings, BLOCKED_SEMANTICS) may be the starter box: "
         "if S4 later releases BOXED as starters, S3.1 STARTER would double count", "STATE": "OWNED_ONCE_WATCH_BOXED"},
        {"INTERFACE": "GROUND BEAM -> COLUMN", "SIDE_A": "S5.1 ground beam (DEVELOPMENT_SUPPORT_1/2 BLOCKED)",
         "SIDE_B": "S3.1 foundation-storey column (passes the ground-beam depth)",
         "CONCRETE": "S5 measures the clear concrete length face to face; the column keeps the joint: no overlap",
         "BARS_OWNED": "beam bars ONCE (S5.1, development blocked); column bars ONCE (S3.1)", "RISK": "",
         "STATE": "OWNED_ONCE"},
        {"INTERFACE": "COLUMN -> BEAM", "SIDE_A": "S3.1 column (LAP / ANCHORAGE through the joint)",
         "SIDE_B": "S6.1 beam (DEVELOPMENT_1/2 BLOCKED into the column)",
         "CONCRETE": "V3b keeps the joint zones as their own lines (C-JNT-*) beside columns and beams; CR "
                     "COLUMNS_AND_JOINTS includes them - never add C-JNT to a column total that already holds them",
         "BARS_OWNED": "ONCE each side", "RISK": "joint concrete in two Urban registers (V3b separate, CR combined)",
         "STATE": "OWNED_ONCE_CONCRETE_REGISTER_OVERLAP"},
        {"INTERFACE": "BEAM -> SLAB", "SIDE_A": "S6.1 beam bars", "SIDE_B": "S7 top-over-support bars (owned by the "
         "support record, counted once; NO_SUPPORT_TOP_BAR_DOUBLE_COUNT gate)",
         "CONCRETE": "V3b beams = clear length x B x (D - t); slab = net plate x t: no overlap",
         "BARS_OWNED": "ONCE (beam bars S6.1; slab top bars S7)", "RISK": "", "STATE": "OWNED_ONCE"},
        {"INTERFACE": "SLAB -> STAIR", "SIDE_A": "S7 slab strips ending at a stair zone",
         "SIDE_B": "S8 stair (flights excluded from S7)",
         "CONCRETE": "stair zones excluded from S7; stair concrete V3b BLOCKED",
         "BARS_OWNED": f"S7 top extensions at stair-adjacent unresolved ends: {stair_kg:.1f} kg ({len(stair)} "
                       "strip ends)", "RISK": "the stair landing / flight top bars over the shared beam must not "
                                           "repeat S7's extension", "STATE": "S8_MUST_EXCLUDE_S7_PORTION"},
        {"INTERFACE": "SLAB -> CANTILEVER", "SIDE_A": "S7 back-span top extensions at the dense-hatch bands",
         "SIDE_B": "S8 cantilever / bearing-wall band (classification blocked)",
         "CONCRETE": "hatch bands not itemised (inside or outside the V3b plate is not established)",
         "BARS_OWNED": f"S7 released {cant_kg:.1f} kg of top steel at the {len(cant)} bearing-wall-candidate "
                       "supports (blocked there, Q-HATCH)",
         "RISK": "no overlap today; the top steel over these supports is owned by NOBODY until the band is "
                 "classified (cantilever or bearing wall)", "STATE": "NOT_OWNED"},
        {"INTERFACE": "WALL -> FOUNDATION", "SIDE_A": "no structural / retaining / shear wall on any plan",
         "SIDE_B": "boundary-wall pads (p.14) / lift walls on FF", "CONCRETE": "none measured",
         "BARS_OWNED": "NOBODY (walls not quantified)", "RISK": "lift-wall and boundary-wall starters are owned by "
         "no stage", "STATE": "NOT_OWNED"},
        {"INTERFACE": "LIFT WALL -> PIT BASE", "SIDE_A": "S4.1 FF footing mesh (lift base, two layers)",
         "SIDE_B": "S8 lift walls 20 cm (p.14)", "CONCRETE": "FF in the V3b footing line; walls not measured",
         "BARS_OWNED": "base mesh ONCE (S4.1); wall bars NOBODY", "RISK": "S8 must not re-count the FF mesh as a "
         "pit slab", "STATE": "PARTIAL_OWNERSHIP"},
        {"INTERFACE": "POOL WALL -> POOL BASE", "SIDE_A": "pool base (N.I.S. detail p.7)", "SIDE_B": "pool walls",
         "CONCRETE": "V3b C-POOL walls + base (DERIVED) + blinding", "BARS_OWNED": "NOBODY in S3-S7 (V3b pre-S "
         "estimate only)", "RISK": "L-bars at the corners are drawn once per corner detail: count once",
         "STATE": "NOT_OWNED"},
        {"INTERFACE": "TANK WALL -> TANK BASE", "SIDE_A": "water-tank support slab (2 panels, T18, T&B)",
         "SIDE_B": "tank walls: ABSENT (the plan reads 'WATER TANK PLACE')",
         "CONCRETE": "slab region only", "BARS_OWNED": f"S7 transferred the region to S8 (S7 top extensions at its "
                                                        f"edges: {tank_kg:.1f} kg)",
         "RISK": "", "STATE": "WALLS_ABSENT"},
        {"INTERFACE": "DOME -> SLAB / RING BEAM", "SIDE_A": "S6 untagged arcs ARC:FFRS:BA003-008 (BLOCKED_TYPE, 0 kg)",
         "SIDE_B": "S8 dome ring beam per DETAIL OF DOME", "CONCRETE": "V3b dome ring lines BLOCKED (depth AS PER ARCH)",
         "BARS_OWNED": f"none yet (S7 top extensions at dome-zone ends: {dome_kg:.1f} kg)",
         "RISK": "two owners for one ring beam: transfer the arcs S6 -> S8 before S8 counts them",
         "STATE": "TRANSFER_REQUIRED"},
        {"INTERFACE": "BLINDING (three Urban measures)", "SIDE_A": "V3b C-BLD-F / C-BLD-GB (REVIEW)",
         "SIDE_B": "V3b C-BLD-FULL (OWNER_PROJECT_FACT)", "CONCRETE": "the same layer measured two ways",
         "BARS_OWNED": "n/a", "RISK": "never sum", "STATE": "CONCRETE_REGISTER_OVERLAP"}]


def conflict_rows(S1d, pre7c, p71c, srd):
    rows = []
    for r in S1d["STRUCTURAL_PROJECT_RULE_REGISTER"]:
        if r["status"] == "SOURCE_CONFLICT":
            rows.append({"CONFLICT_ID": f"RULE-{r['rule_id']}", "SOURCE": "S1 rule register", "WHERE": f"p.{r['page']}",
                         "DESCRIPTION": r["raw_text"][:240], "STATE": "PRESERVED", "AFFECTS": r.get("topic")})
    for r in pre7c:
        rows.append({"CONFLICT_ID": r["CONFLICT_ID"], "SOURCE": "PRE-S7 11_SOURCE_CONFLICTS", "WHERE": r["WHERE"],
                     "DESCRIPTION": f"{r['KIND']}: {r['EVIDENCE'][:200]}", "STATE": r["STATE"],
                     "AFFECTS": "slabs"})
    for r in p71c:
        if r["TRUE_SOURCE_CONFLICT"] == "True":
            rows.append({"CONFLICT_ID": f"PRE-S7.1 {r['PRE_S7_CONFLICT_ID']}", "SOURCE": "PRE-S7.1 09",
                         "WHERE": r["WHERE"], "DESCRIPTION": f"{r['KIND']}: {r['NOTE'][:200]}",
                         "STATE": r["AD2_STATE"], "AFFECTS": "slabs"})
    for r in srd:
        rows.append({"CONFLICT_ID": r["CONFLICT_ID"], "SOURCE": "SRD 10_PENDING_ENGINEER_CONFLICTS",
                     "WHERE": f"{r['STAGE']} {r['ITEM_ID']}",
                     "DESCRIPTION": f"{r['SOURCE_A']}={r['SOURCE_A_VALUE']} vs {r['SOURCE_B']}={r['SOURCE_B_VALUE']}"[
                         :240], "STATE": r["TERMINAL_STATE"], "AFFECTS": r["AFFECTED"][:80]})
    rows += [
        {"CONFLICT_ID": "PS8-C01", "SOURCE": "this round (population search)", "WHERE": "2F roof / tower",
         "DESCRIPTION": "architectural P7757 shows three dome circles (2 x 4422 terrace, 1 x 4410 tower); the "
                        "structural sheets show two (FFRS); the tower dome sits over the flat structural panel "
                        "SP-2F_ROOF_SLAB-04", "STATE": "PRESERVED_UNRESOLVED", "AFFECTS": "dome / S7 2F roof"},
        {"CONFLICT_ID": "PS8-C02", "SOURCE": "this round (ownership)", "WHERE": "FFRS arcs BA003-BA008",
         "DESCRIPTION": "S1 calls them DOME_RING; S6 carries them as untagged beams (BLOCKED_TYPE, 0 kg); the DETAIL OF "
                        "DOME specifies the ring beam", "STATE": "TRANSFER_REQUIRED", "AFFECTS": "S6 / S8 dome"},
        {"CONFLICT_ID": "PS8-C03", "SOURCE": "S7A (Phase A)", "WHERE": "every beam support",
         "DESCRIPTION": "note 2 'one third of the span' vs p.15 0.25 L1 / 0.30 max(L1, L2): same family supported, not "
                        "proven; total vs per side not established", "STATE": "PRESERVED (S7A)", "AFFECTS": "S7 top"},
        {"CONFLICT_ID": "PS8-C04", "SOURCE": "this round (concrete registers)", "WHERE": "blinding",
         "DESCRIPTION": "V3b blinding per footing / ground beam (REVIEW) vs full-footprint blinding (OWNER_PROJECT_"
                        "FACT): one layer, two measures", "STATE": "PRESERVED (never summed)", "AFFECTS": "concrete"}]
    return rows


def missing_components(census, s7blocked):
    agg = defaultdict(lambda: {"n": 0, "owners": set(), "examples": []})
    for r in census:
        comps = r["REBAR_COMPONENTS"]
        if isinstance(comps, dict):
            continue
        for c in comps or []:
            name, _, st = str(c).rpartition(":")
            if st in ("BLOCKED_UNQUANTIFIED", "BLOCKED", "NOT_QUANTIFIED", "NOT_ESTABLISHED", "NOT_IN_S3_S7"):
                k = (family_group(r["ELEMENT_FAMILY"]), name)
                agg[k]["n"] += 1
                agg[k]["owners"].add(r["EXISTING_STAGE_OWNER"].split(" (")[0])
                if len(agg[k]["examples"]) < 3:
                    agg[k]["examples"].append(r["ELEMENT_ID"])
    for b in s7blocked:
        k = ("ELEVATED_SLAB", b["ITEM"])
        agg[k]["n"] += 1
        agg[k]["owners"].add("S7 (blocked)")
        if len(agg[k]["examples"]) < 3:
            agg[k]["examples"].append(b["S7_BLOCKED_ID"])
    rows = []
    for (g, comp), a in sorted(agg.items()):
        rows.append({"FAMILY": g, "COMPONENT": comp, "OCCURRENCES": a["n"], "OWNER_STATE": sorted(a["owners"]),
                     "EXAMPLES": a["examples"], "QUANTITY": "NONE (unquantified)",
                     "WHY": "source does not establish a length / count / shape for this component"})
    return rows


# ------------------------------------------------------------------ D. source exhaustion per S8 candidate
CHANNELS = ("PLAN", "SECTION", "SCHEDULE", "TYPICAL_DETAIL", "NOTES_AR", "NOTES_EN", "DXF_BLOCKS_ATTRIBS",
            "LEADERS_GRAPHIC_BARS", "REVISIONS", "ARCHITECTURE")
EXHAUSTION = [  # candidate, channel findings, dimensioned, schematic, missing, decision
    ("STAIR_AND_LANDING",
     {"PLAN": "5 flights (GF-03, GF-21, GF-28, 1F-01, GBP-12) as slab faces with treads", "SECTION": "p.16 TYPICAL "
      "STEEL LAYOUT-STAIR SECTION; FFRS SECTION B-B", "SCHEDULE": "stair-qualified beam tags (3)",
      "TYPICAL_DETAIL": "P16-STAIR bars 6Ø14/m, 8Ø16/m, 6Ø12/m, Ø12/20, Ø8/15 ...; landing S.S.L +2.00 / +4.00",
      "NOTES_AR": "none specific", "NOTES_EN": "'(With Stair)' tags", "DXF_BLOCKS_ATTRIBS": "tread linework",
      "LEADERS_GRAPHIC_BARS": "GF-21 light-well 8Ø16/m drawn along both flights", "REVISIONS": "no other structural "
      "revision admitted", "ARCHITECTURE": "risers / goings from the architectural stair (6E rounds)"},
     "plan geometry of flights; landing levels +2.00 / +4.00 (p.16)", "p.16 section (N.I.S.)",
     "waist thickness, riser height, bar lengths per flight; which p.16 bar is which", "BLOCKED_NEEDS_AUTHORITY"),
    ("LIFT_PIT_AND_WALLS",
     {"PLAN": "FF footing (4 columns) on the foundation plan; shaft outline not drawn", "SECTION": "p.14 DETAIL OF "
      "LIFT WITH ISOLATED FOOTING", "SCHEDULE": "FF row 460 x 450 x 55, remark 'قاعدة مصعد' (lift base)",
      "TYPICAL_DETAIL": "walls 20 cm, 6Ø12/m + 6Ø16/m, 2Ø16, 2Ø12", "NOTES_AR": "p.8 note 19: lift tie beams at "
      "3.00 m if the storey height > 4.30 m", "NOTES_EN": "pit depth 'As Per Lift Manufactures recommendations'",
      "DXF_BLOCKS_ATTRIBS": "FTB block attributes of FF", "LEADERS_GRAPHIC_BARS": "none on plan",
      "REVISIONS": "none", "ARCHITECTURE": "lift shaft on the architectural plans (outline)"},
     "FF footing dimensions; wall thickness 20 cm", "p.14 detail", "pit depth, wall height, shaft outline",
     "BLOCKED_NEEDS_AUTHORITY"),
    ("SWIMMING_POOL",
     {"PLAN": "pool outline on GBP ('swimming pool' / 'حمام سباحة')", "SECTION": "p.7 DETAIL OF SWIMMING POOL (N.I.S)",
      "SCHEDULE": "none", "TYPICAL_DETAIL": "26 pool bar labels (7Ø14/m, 6Ø12/m, Ø12/20cm, 3Ø16, 4Ø16 ...)",
      "NOTES_AR": "none", "NOTES_EN": "10cm PLAIN CONCRETE, screed, insulation", "DXF_BLOCKS_ATTRIBS": "SWIM block",
      "LEADERS_GRAPHIC_BARS": "bar lines in the detail", "REVISIONS": "none", "ARCHITECTURE": "pool on the site plan"},
     "plan outline; wall 20 / base 40 thickness", "N.I.S. section (bar shapes, two depths)",
     "bar lengths from the N.I.S. section; deep / shallow extents on plan", "READY_PARTIAL"),
    ("DOME_OR_SPECIAL_ROOF",
     {"PLAN": "2 dome circles 4422 mm on FFRS (S-BOUN outlines repeated on SFRS)", "SECTION": "p.7 DETAIL OF DOME "
      "(N.I.S)", "SCHEDULE": "none", "TYPICAL_DETAIL": "Ø12/15cm two layers, shell 10 cm, ring beam 3Ø16 top / "
      "8Ø8/m / 2Ø14/20cm / 3Ø18 bottom", "NOTES_AR": "none", "NOTES_EN": "'SEE DETAIL' inside the circles",
      "DXF_BLOCKS_ATTRIBS": "none", "LEADERS_GRAPHIC_BARS": "detail bars", "REVISIONS": "none",
      "ARCHITECTURE": "three circles (third = tower roof +13.90, structural conflict PS8-C01)"},
     "plan circle 4422; shell 10 cm; span 442 / rise 190 printed", "N.I.S. detail",
     "ring-beam depth 'AS PER ARCH'; tower dome status", "READY_PARTIAL"),
    ("GROUND_SLAB",
     {"PLAN": "21 ground-slab cells on GBP", "SECTION": "none", "SCHEDULE": "none", "TYPICAL_DETAIL": "none",
      "NOTES_AR": "none", "NOTES_EN": "'5Ø10/m E.W. T=10cm' printed twice (two zones)", "DXF_BLOCKS_ATTRIBS":
      "hatched circle symbol", "LEADERS_GRAPHIC_BARS": "none", "REVISIONS": "none", "ARCHITECTURE": "floor levels"},
     "two zones with T = 10 cm and 5Ø10/m E.W.", "", "thickness / mesh for the cells outside the two zones",
     "READY_PARTIAL"),
    ("WATER_TANK",
     {"PLAN": "'WATER TANK PLACE' cloud over 2 SFRS panels with T 18 and (T&B) callouts", "SECTION": "none",
      "SCHEDULE": "none", "TYPICAL_DETAIL": "none", "NOTES_AR": "none", "NOTES_EN": "WATER TANK PLACE",
      "DXF_BLOCKS_ATTRIBS": "none", "LEADERS_GRAPHIC_BARS": "(T&B) bar callouts", "REVISIONS": "none",
      "ARCHITECTURE": "roof plan"},
     "T 18 thickness; T&B callouts", "", "whether the region is a slab (mesh T&B) or supports a separate tank; no tank "
     "walls", "READY_PARTIAL"),
    ("RC_PARAPET",
     {"PLAN": "plan note 1 on each roof sheet (check architectural parapet)", "SECTION": "p.14 parapet sections",
      "SCHEDULE": "none", "TYPICAL_DETAIL": "5Ø12/m, 5Ø10/m, 6Ø10/m, 6Ø12/m; 30 x 130; 15/15 x 105",
      "NOTES_AR": "'على المقاول مطابقة تفاصيل الدروة' (match parapet details with architecture)",
      "NOTES_EN": "CHECK ARCHITECTURAL DETAIL OF PARAPET, BEFORE CASTING", "DXF_BLOCKS_ATTRIBS": "none",
      "LEADERS_GRAPHIC_BARS": "none", "REVISIONS": "none", "ARCHITECTURE": "parapet runs / heights (PA01-PA02)"},
     "section dimensions on p.14", "", "which run takes which section; RC vs block per run", "BLOCKED_NEEDS_AUTHORITY"),
    ("LINTEL",
     {"PLAN": "no lintel on the structural plans", "SECTION": "none", "SCHEDULE": "p.13 LINTEL SCHEDULE by opening "
      "width", "TYPICAL_DETAIL": "none", "NOTES_AR": "p.8 note 4 (openings)", "NOTES_EN": "none",
      "DXF_BLOCKS_ATTRIBS": "none", "LEADERS_GRAPHIC_BARS": "none", "REVISIONS": "none",
      "ARCHITECTURE": "opening register (widths) from the architectural rounds"},
     "schedule rows by width", "", "binding of each architectural opening to a wall thickness and a schedule row",
     "READY_PARTIAL"),
    ("BOUNDARY_WALL",
     {"PLAN": "S-BOUN run on GBP; B.W schedule row unbound", "SECTION": "p.14 TYPICAL BOUNDARY WALL",
      "SCHEDULE": "B.W row (simple-beam schedule)", "TYPICAL_DETAIL": "R.C columns 20x30 4Ø14; GB 20x40; pads "
      "130x80x30", "NOTES_AR": "p.1 note B (external ground beams on the neighbour side)", "NOTES_EN": "none",
      "DXF_BLOCKS_ATTRIBS": "none", "LEADERS_GRAPHIC_BARS": "none", "REVISIONS": "none",
      "ARCHITECTURE": "fence sheet (front fence run)"},
     "typical section sizes", "", "column / pad spacing; which runs are RC", "BLOCKED_NEEDS_AUTHORITY"),
    ("SPECIAL_COLUMN",
     {"PLAN": "T.C x2, D.C x1, P.C x3 labels", "SECTION": "none", "SCHEDULE": "P.C 20x50 / 20x70 in the label",
      "TYPICAL_DETAIL": "p.15 twisted column (4Ø16 extra, spiral 6Ø8/m, 1 m above / below); planted column detail",
      "NOTES_AR": "none", "NOTES_EN": "none", "DXF_BLOCKS_ATTRIBS": "none", "LEADERS_GRAPHIC_BARS": "none",
      "REVISIONS": "none", "ARCHITECTURE": "none"},
     "1 m above / below; P.C sections", "p.15 detail", "planted column heights / bars; dead-column termination",
     "READY_PARTIAL"),
    ("CANTILEVER_OR_BEARING_WALL_BAND",
     {"PLAN": "8 dense-hatch bands (legend: cantilever portion = bearing wall hatch)", "SECTION": "none",
      "SCHEDULE": "B.W row", "TYPICAL_DETAIL": "none", "NOTES_AR": "none", "NOTES_EN": "legend", "DXF_BLOCKS_ATTRIBS":
      "hatch", "LEADERS_GRAPHIC_BARS": "none", "REVISIONS": "none", "ARCHITECTURE": "balconies / projections"},
     "band geometry", "", "cantilever vs bearing wall (the legend hatch is the same)", "BLOCKED_NEEDS_AUTHORITY"),
    ("SUNKEN_EXTRAS_AND_STEPS",
     {"PLAN": "6 sunken panels (base mesh in S7)", "SECTION": "none", "SCHEDULE": "none", "TYPICAL_DETAIL": "none",
      "NOTES_AR": "none", "NOTES_EN": "legend 'Sunken slab'", "DXF_BLOCKS_ATTRIBS": "hatch",
      "LEADERS_GRAPHIC_BARS": "none", "REVISIONS": "none", "ARCHITECTURE": "wet-room levels"},
     "", "", "step depth and step / edge bars (no detail)", "BLOCKED_NEEDS_AUTHORITY"),
    ("OPENING_TRIM",
     {"PLAN": "3 voids (GF-09, GF-13, 1F-06)", "SECTION": "none", "SCHEDULE": "none", "TYPICAL_DETAIL": "p.16 beam "
      "opening (no occurrence)", "NOTES_AR": "p.8 note 4 (all openings must appear on the structural plans)",
      "NOTES_EN": "VOID / منور", "DXF_BLOCKS_ATTRIBS": "void blocks", "LEADERS_GRAPHIC_BARS": "no trim / diagonal "
      "bars drawn", "REVISIONS": "none", "ARCHITECTURE": "openings"},
     "void outlines", "", "trim and diagonal bars (NONE_DRAWN)", "BLOCKED_NEEDS_AUTHORITY"),
    ("DOME_RING_BEAM",
     {"PLAN": "6 untagged arcs on FFRS", "SECTION": "p.7 dome detail", "SCHEDULE": "none", "TYPICAL_DETAIL":
      "ring beam 3Ø16 / 8Ø8/m / 2Ø14/20cm / 3Ø18", "NOTES_AR": "none", "NOTES_EN": "depth AS PER ARCH",
      "DXF_BLOCKS_ATTRIBS": "none", "LEADERS_GRAPHIC_BARS": "detail", "REVISIONS": "none",
      "ARCHITECTURE": "dome elevation"},
     "arc geometry; B 20", "N.I.S. depth (drawn 0.75)", "ring depth", "READY_PARTIAL")]


def exhaustion_rows(texts, census):
    s8 = Counter(family_group(r["ELEMENT_FAMILY"]) for r in census if str(r["NEW_S8_OWNER"]).startswith("S8"))
    rows = []
    for cand, ch, dim, nts, missing, decision in EXHAUSTION:
        check(set(ch) == set(CHANNELS), f"every channel checked for {cand}")
        rows.append({"S8_CANDIDATE": cand, **{f"CH_{k}": ch[k] for k in CHANNELS},
                     "DIMENSIONED_EVIDENCE": dim, "SCHEMATIC_NTS_EVIDENCE": nts, "MISSING": missing,
                     "READINESS": decision, "CENSUS_ELEMENTS": s8.get(_cand_group(cand), 0),
                     "RULE": "no bar is made from generic practice; no steel-per-volume ratio becomes a BOQ quantity"})
    return rows


def _cand_group(cand):
    return {"STAIR_AND_LANDING": "STAIR_AND_LANDING", "LIFT_PIT_AND_WALLS": "LIFT", "SWIMMING_POOL": "SWIMMING_POOL",
            "DOME_OR_SPECIAL_ROOF": "DOME", "GROUND_SLAB": "GROUND_SLAB", "WATER_TANK": "WATER_TANK",
            "RC_PARAPET": "RC_PARAPET", "LINTEL": "LINTEL", "BOUNDARY_WALL": "BOUNDARY_WALL",
            "SPECIAL_COLUMN": "SPECIAL_COLUMN", "CANTILEVER_OR_BEARING_WALL_BAND": "CANTILEVER_OR_BEARING_WALL",
            "SUNKEN_EXTRAS_AND_STEPS": "SUNKEN_SLAB", "OPENING_TRIM": "OPENING_TRIM",
            "DOME_RING_BEAM": "DOME_RING_BEAM"}.get(cand, cand)


# ------------------------------------------------------------------ build
def family_search(texts, census, S1d):
    counted = [r for r in census if r["ROW_KIND"] in COUNTED_KINDS]
    fam_count = Counter(family_group(r["ELEMENT_FAMILY"]) for r in counted)
    rules = {r["rule_id"] for r in S1d["STRUCTURAL_PROJECT_RULE_REGISTER"]}
    group_of = {"LEAN_BLINDING_CONCRETE": "LEAN_BLINDING_CONCRETE", "ISOLATED_FOOTING": "FOOTING",
                "COMBINED_FOOTING": "FOOTING", "NECK_PEDESTAL": "NECK_PEDESTAL", "STRAP_BEAM": "STRAP_BEAM",
                "GROUND_BEAM": "GROUND_BEAM", "GROUND_SLAB": "GROUND_SLAB", "COLUMN": "COLUMN",
                "SPECIAL_COLUMN": "SPECIAL_COLUMN", "BEAM": "BEAM", "ELEVATED_SLAB": "ELEVATED_SLAB",
                "SUNKEN_SLAB_OR_STEP": "SUNKEN_SLAB", "CANTILEVER_OR_BALCONY": "CANTILEVER_OR_BEARING_WALL",
                "STAIR_AND_LANDING": "STAIR_AND_LANDING", "LIFT_PIT_AND_WALLS": "LIFT", "WATER_TANK": "WATER_TANK",
                "SWIMMING_POOL": "SWIMMING_POOL", "DOME_OR_SPECIAL_ROOF": "DOME", "RC_PARAPET": "RC_PARAPET",
                "OPENING_TRIM": "OPENING_TRIM", "LINTEL": "LINTEL", "BOUNDARY_WALL": "BOUNDARY_WALL",
                "STRUCTURAL_WALL": "CANTILEVER_OR_BEARING_WALL", "RIBBED_OR_HORDI_SLAB": "TYPICAL_ONLY"}
    combined = sum(1 for r in counted if r["ELEMENT_FAMILY"] == "COMBINED_FOOTING")
    starters = sum(1 for r in census if r["ELEMENT_FAMILY"].startswith("NECK") and any(
        str(c).startswith("STARTER:") and not str(c).endswith("NOT_REQUIRED") for c in r["REBAR_COMPONENTS"]))
    typical = Counter(r["ELEMENT_FAMILY"].split(" (")[0] for r in census if r["ROW_KIND"] == "TYPICAL_DETAIL_ONLY")
    rows = []
    for fam, pat, ar, key, rids in FAMILY_SEARCH:
        check(all(r in rules for r in rids), f"rule ids of {fam} exist")
        hits = search_hits(texts, pat, ar)
        by_sheet = Counter(h["sheet"] for h in hits)
        n = fam_count.get(group_of.get(fam, ""), 0)
        if fam == "COMBINED_FOOTING":
            n = combined
        if fam == "ISOLATED_FOOTING":
            n = sum(1 for r in counted if r["ELEMENT_FAMILY"] in ("ISOLATED_FOOTING",))
        if fam == "RIBBED_OR_HORDI_SLAB":
            n = 0
        if n:
            state = "PRESENT"
        elif rids:
            state = "TYPICAL_DETAIL_ONLY_NO_OCCURRENCE" if fam in ("RIBBED_OR_HORDI_SLAB",) else \
                "RULE_ONLY_NO_OCCURRENCE"
        else:
            state = "ABSENT_IN_ISSUED_DOCUMENTS"
        if fam == "SPECIAL_COLUMN":
            n = sum(1 for r in census if r["ELEMENT_FAMILY"].startswith("SPECIAL_COLUMN"))
            state = f"PRESENT_AS_COMPONENT ({n} labels on S3.1-owned column occurrences)"
        if fam == "STARTER_DOWEL":
            state = (f"COMPONENT_FAMILY (S3.1 STARTER on {starters} foundation-storey columns; footing BOXED bars "
                     "semantics blocked)")
        if fam == "RIBBED_OR_HORDI_SLAB":
            state = f"TYPICAL_DETAIL_ONLY_NO_OCCURRENCE ({typical.get('RIBBED_OR_HORDI_SLAB', 0)} typical record)"
        if fam == "STRUCTURAL_WALL":
            state = "CANDIDATE_ONLY (B.W schedule row + legend hatch; no wall tagged on a plan)"
        if fam == "FOAM_CONCRETE":
            state = "LEGEND_ONLY (non-structural fill; no occurrence)"
        rows.append({"FAMILY": fam, "SEARCH_EN": pat, "SEARCH_AR": list(ar), "DXF_TEXT_HITS": len(hits),
                     "HITS_BY_SHEET": dict(sorted(by_sheet.items())),
                     "SAMPLE_HANDLES": [h["handle"] for h in hits[:6]],
                     "SAMPLE_TEXTS": sorted({h["text"][:40] for h in hits})[:6], "PDF_RULES": rids,
                     "CENSUS_OCCURRENCES": n, "STATE": state})
    return rows


def build():
    frozen = verify_inputs()
    S1d = {reg: _j(S1 / f"{reg}.json")["rows"] for reg in S1_REGS}
    texts, circles, _src = dxf_texts()
    arch = arch_dome_circles()
    check(len(arch) == 3 and len([c for c in circles if c["sheet"] == "FFRS"]) >= 2, "dome circles found")
    v3 = v3b_concrete(_j(P["v3b_boq"]))
    s31 = _j(P["s31_release"])
    fr = footing_rows(S1d, _rows(P["s4_occ"]), _rows(P["s4_comp"]), v3)
    cr_ = column_rows(S1d, s31, v3, S1d["SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER"])
    gr = ground_rows(_rows(P["s5_occ"]), v3)
    br = beam_rows(_rows(P["s6_occ"]), v3)
    parents = {}
    for x in S1d["SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER"]:
        if x["kind"] == "DOME":
            parents.update({f: x["special_id"] for f in x["dome_zone_faces"]})
        elif x["kind"] == "STAIR_FLIGHT":
            parents[x["special_id"].replace("SPC-STAIR-", "")] = x["special_id"]
        elif x["kind"] == "WATER_TANK_SLAB":
            parents.update({c["SLAB_PANEL_ID"]: x["special_id"] for c in _rows(P["pre7_census"])
                            if c["PANEL_CLASS"] == "WATER_TANK_PLACE_SLAB"})
    s6occ = _rows(P["s6_occ"])
    sr, skipped = slab_rows(_rows(P["pre7_census"]), _rows(P["s7_panels"]), _rows(P["p71_transfers"]), v3, parents)
    gs = ground_slab_rows(S1d, v3, parents)
    sp = special_rows(S1d, v3, s6occ)
    ps = search_rows(texts, circles, arch, v3, S1d, fr)
    census = fr + cr_ + gr + br + sr + gs + sp + ps
    owner_of = {r["ELEMENT_ID"]: r["EXISTING_STAGE_OWNER"] for r in census}
    for r in census:
        r.setdefault("ROW_KIND", "ELEMENT")
        r.setdefault("PARENT_ELEMENT", "")
        own_s = r["EXISTING_STAGE_OWNER"].startswith("S") or (
            r["ROW_KIND"] == "COMPONENT_EVIDENCE" and owner_of.get(r["PARENT_ELEMENT"], "").startswith("S"))
        r["S8_SCOPE"] = ("" if not str(r["NEW_S8_OWNER"]).startswith("S8") else
                         "COMPONENT_OF_OWNED_ELEMENT" if own_s else "WHOLE_ELEMENT")
        check(r["ROW_KIND"] in ROW_KINDS, f"row kind of {r['ELEMENT_ID']}")
    ids = [r["ELEMENT_ID"] for r in census]
    check(len(ids) == len(set(ids)), "one census row per element")
    known = set(ids)
    for r in census:
        par = r["PARENT_ELEMENT"]
        check(not par or par in known or par.startswith("S7 slab population"), f"parent {par} of {r['ELEMENT_ID']}")
    check(len(fr) == 26 and len(cr_) == 95 and len(gr) == 62 and len(br) == 140, "S1 / stage populations conserved")
    fam = family_search(texts, census, S1d)
    cmat = concrete_matrix(census, v3, _j(P["cr_dashboard"]))
    s7sum, s7a = _j(P["s7_summary"]), _j(P["s7a_summary"])
    rmat, stage = rebar_matrix(census, s31, s7sum, _j(P["d12_summary"]), s7a)
    check(abs(s7sum["totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"] - s7a["s7_frozen_total_kg"]) < 1e-9,
          "S7 total unchanged")
    inter = interfaces(census, _rows(P["s7a_audit"]), _rows(P["s7_supports"]))
    conf = conflict_rows(S1d, _rows(P["pre7_conflicts"]), _rows(P["p71_conflicts"]), _rows(P["srd_conflicts"]))
    miss = missing_components(census, _rows(P["s7_blocked"]))
    exh = exhaustion_rows(texts, census)
    s8 = [r for r in census if str(r["NEW_S8_OWNER"]).startswith("S8")]
    own = ownership(census)
    cand = s8_candidates(s8, exh)
    return {"frozen": frozen, "census": census, "fam": fam, "cmat": cmat, "rmat": rmat, "stage": stage,
            "inter": inter, "conf": conf, "miss": miss, "exh": exh, "own": own, "cand": cand, "skipped": skipped,
            "arch": arch, "circles": circles, "s7sum": s7sum, "s7a": s7a, "texts_n": len(texts)}


def ownership(census):
    agg = defaultdict(lambda: Counter())
    for r in census:
        if r["ROW_KIND"] not in COUNTED_KINDS + ("FACE_OF_ELEMENT",):
            continue
        agg[family_group(r["ELEMENT_FAMILY"])][r["EXISTING_STAGE_OWNER"].split(" (")[0]] += 1
    return [{"FAMILY": g, "OWNERS": dict(c), "ELEMENTS": sum(c.values()),
             "OWNED_BY_S3_S7": sum(v for k, v in c.items() if k.startswith("S")),
             "NO_STAGE": sum(v for k, v in c.items() if not k.startswith("S"))} for g, c in sorted(agg.items())]


def s8_candidates(s8, exh):
    dec = {_cand_group(r["S8_CANDIDATE"]): r["READINESS"] for r in exh}
    agg = defaultdict(list)
    for r in s8:
        agg[family_group(r["ELEMENT_FAMILY"])].append(r)
    rows = []
    for g, rs in sorted(agg.items()):
        rows.append({"S8_FAMILY": g, "ROWS": len(rs),
                     "WHOLE_ELEMENTS": sum(1 for r in rs if r["S8_SCOPE"] == "WHOLE_ELEMENT" and
                                           r["ROW_KIND"] in COUNTED_KINDS),
                     "FACES": sum(1 for r in rs if r["ROW_KIND"] == "FACE_OF_ELEMENT"),
                     "COMPONENTS_OF_OWNED_ELEMENTS": sum(1 for r in rs if r["S8_SCOPE"] == "COMPONENT_OF_OWNED_ELEMENT"),
                     "ELEMENT_IDS": [r["ELEMENT_ID"] for r in rs][:40],
                     "NEW_S8_OWNER": sorted({r["NEW_S8_OWNER"] for r in rs}),
                     "CONCRETE_STATES": sorted({r["CONCRETE_QUANTITY_STATE"][:90] for r in rs})[:4],
                     "MISSING": sorted({r["MISSING_INFORMATION"] for r in rs if r["MISSING_INFORMATION"]})[:4],
                     "READINESS": dec.get(g, "NOT_ASSESSED_COMPONENT_OF_OWNED_ELEMENT")})
    return rows


def summarise(B):
    c = B["census"]
    fam_state = Counter(r["STATE"].split(" (")[0] for r in B["fam"])
    counted = [r for r in c if r["ROW_KIND"] in COUNTED_KINDS]
    s8 = [r for r in counted if r["S8_SCOPE"] == "WHOLE_ELEMENT"]
    return {"round": ROUND, "date": QA_DATE, "policy": POLICY, "baseline": BASELINE_HEAD,
            "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
            "frozen_baselines": {k: v["manifest_sha256"] for k, v in B["frozen"].items()},
            "census_rows": len(c), "rows_by_kind": dict(sorted(Counter(r["ROW_KIND"] for r in c).items())),
            "elements_total": len(counted),
            "elements_by_family": dict(sorted(Counter(family_group(r["ELEMENT_FAMILY"]) for r in counted).items())),
            "s8_component_transfers": sorted({f"{r['ELEMENT_ID']}: {r['NEW_S8_OWNER']}" for r in c
                                              if r["S8_SCOPE"] == "COMPONENT_OF_OWNED_ELEMENT"})[:20],
            "s8_component_transfer_count": sum(1 for r in c if r["S8_SCOPE"] == "COMPONENT_OF_OWNED_ELEMENT"),
            "families_searched": len(B["fam"]), "family_states": dict(sorted(fam_state.items())),
            "concrete_states": dict(sorted(Counter(r["COVERAGE_STATE"] for r in B["cmat"]).items())),
            "rebar_coverage": dict(sorted(Counter(r["COVERAGE"] for r in B["rmat"]).items())),
            "s8_elements": len(s8), "s8_by_family": dict(sorted(Counter(family_group(r["ELEMENT_FAMILY"])
                                                                         for r in s8).items())),
            "previously_omitted": [r["ELEMENT_ID"] for r in c if "PREVIOUSLY" in r["QA_STATE"] or
                                   r["ROW_KIND"] == "CONFLICT_CANDIDATE" or r["QA_STATE"].startswith("NEW_EVIDENCE")],
            "interfaces": {r["INTERFACE"]: r["STATE"] for r in B["inter"]},
            "conflicts": len(B["conf"]), "missing_component_kinds": len(B["miss"]),
            "readiness": {r["S8_CANDIDATE"]: r["READINESS"] for r in B["exh"]},
            "stage_kg": {r["STAGE"]: r["KG"] for r in B["stage"]},
            "s7_total_kg_unchanged": B["s7sum"]["totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"],
            "kg_calculated_here": 0, "references_read": [], "s8_started": False,
            "not_structural_faces_skipped": B["skipped"], "dxf_texts_searched": B["texts_n"]}


def readiness_doc(B):
    order = [("1", "GROUND_SLAB", "two printed zones are dimensioned (T 10, 5Ø10/m E.W.); the rest needs a thickness "
                                  "authority"),
             ("2", "SWIMMING_POOL", "plan outline + N.I.S. section; bar lengths from the section labels only"),
             ("3", "DOME_OR_SPECIAL_ROOF + DOME_RING_BEAM", "after the S6 -> S8 arc transfer; ring depth stays "
                                                         "blocked"),
             ("4", "LINTEL", "schedule by width once the architectural openings are bound"),
             ("5", "WATER_TANK", "slab region T18 T&B (no walls)"),
             ("6", "SPECIAL_COLUMN extras", "twisted / planted printed extras"),
             ("7", "STAIR_AND_LANDING", "needs waist / riser / bar mapping authority"),
             ("8", "LIFT_PIT_AND_WALLS", "needs pit depth / shaft outline"),
             ("9", "RC_PARAPET, BOUNDARY_WALL, CANTILEVER bands, OPENING_TRIM, SUNKEN extras",
              "need run / identity / detail authority")]
    return {"decision": "PRE-S8 COMPLETE - S8 NOT STARTED. S8 may open only for the READY / READY_PARTIAL families, "
                        "each as its own frozen round; the BLOCKED families need the listed authority first.",
            "candidates": {r["S8_CANDIDATE"]: {"readiness": r["READINESS"], "missing": r["MISSING"],
                                               "dimensioned": r["DIMENSIONED_EVIDENCE"],
                                               "schematic_nts": r["SCHEMATIC_NTS_EVIDENCE"]} for r in B["exh"]},
            "recommended_s8_order": [{"step": s, "family": f, "why": w} for s, f, w in order],
            "pre_conditions": ["transfer ARC:FFRS:BA003-BA008 from S6 to S8 DOME before any ring-beam quantity",
                               "S8 stair / cantilever / tank / dome quantities exclude S7's released top extensions at "
                               "their shared supports (07_INTERFACE_DOUBLE_COUNT_AUDIT.csv)",
                               "blinding concrete: one register only (never V3b per-element + full footprint)",
                               "PS8-C01 tower dome: structural confirmation before any quantity"],
            "rule": "no S8 kg in this round; S7 total unchanged; no steel-per-volume ratio converted to a BOQ quantity"}


def readme(B, s):
    L = ["# PRE-S8: structural completeness audit, excavation to roof (2026-10-08)", "",
         "This is an analysis round. No kg is calculated, no frozen stage moves, and S8 is not started. S7 stays at "
         f"**{s['s7_total_kg_unchanged']:,.3f} kg**.", "",
         "## What was searched", "",
         f"- {s['dxf_texts_searched']} ST7757.dxf texts, legacy Arabic decoded and assigned to sheets.",
         f"- {s['families_searched']} structural families, searched as a population (01_FAMILY_POPULATION_SEARCH.csv).",
         "- The S1 census registers, the PRE-S7 panel census and the S1 rule register (pp.1-16).",
         "- The architectural P7757.dxf, where an object appears only there.", "",
         "## Census (02)", "",
         f"There are {s['elements_total']} physical elements or population records, in {s['census_rows']} census rows. "
         f"The other rows are faces of an element, component evidence or typical-only details: {s['rows_by_kind']}.",
         "", "Elements by family:", ""]
    for k, v in s["elements_by_family"].items():
        L.append(f"- {k}: {v}")
    L += ["", f"{s['s8_elements']} whole elements have no S3-S7 owner and go to S8. Another "
          f"{s['s8_component_transfer_count']} rows are components of owned elements that S8 would take (special-column "
          "extras, sunken extras, the dome ring arcs).", "",
          "Previously omitted, unregistered or newly bound occurrences:", "",
          "- PS8-BLINDING-UNDER-FOOTINGS: plain-concrete blinding. No S-stage register holds it; V3b measured it in "
          "two overlapping ways.",
          "- PS8-LIFT-WALLS: the S1 LIFT_PIT had no plan location. The FF lift footing (4 columns) and the decoded "
          "schedule remark 'قاعدة مصعد' (lift base) now bind it.",
          "- PS8-DOME-TOWER-ARCH-ONLY: an architectural tower dome over the flat structural panel SP-2F_ROOF_SLAB-04 "
          "(conflict PS8-C01).",
          "- ARC:FFRS:BA003-BA008: dome ring beams that S6 holds as untagged beams (PS8-C02).", "",
          "## Coverage (03, 04, 05)", "",
          "- Concrete comes from the V3b BOQ lines and the coverage-recovery dashboard. Lines are copied with their own "
          "labels and never re-summed.",
          "- Rebar comes from the S3.1, S4.1, S5.1, S6.1 and S7 component states.",
          "- Stage totals (copied, not combined):"]
    for k, v in s["stage_kg"].items():
        L.append(f"  - {k}: {v:,.3f} kg")
    L += ["", "## Interfaces (07)", ""]
    for k, v in s["interfaces"].items():
        L.append(f"- {k}: {v}")
    L += ["", "## S8 readiness (10, 11)", ""]
    for k, v in s["readiness"].items():
        L.append(f"- {k}: {v}")
    L += ["", "## Reproduce", "", "```", "python3 -I research/pre_s8_structural_completeness/build_pre_s8.py", "```", "",
          "The build is byte-identical on rebuild. It is blind: no external reference or comparison register is read.", ""]
    return "\n".join(L)


def write(B):
    _csv("01_FAMILY_POPULATION_SEARCH.csv", B["fam"], list(B["fam"][0]))
    _csv("02_STRUCTURAL_ELEMENT_CENSUS.csv", B["census"], CENSUS_FIELDS)
    _csv("03_CONCRETE_COVERAGE_MATRIX.csv", B["cmat"], list(B["cmat"][0]))
    _csv("04_REBAR_COVERAGE_MATRIX.csv", B["rmat"], list(B["rmat"][0]))
    _csv("05_STAGE_OWNERSHIP_REGISTER.csv", B["own"] + [{"FAMILY": f"STAGE {x['STAGE']}", "OWNERS": x["SCOPE"],
                                                          "ELEMENTS": None, "OWNED_BY_S3_S7": x["KG"],
                                                          "NO_STAGE": x["NOTE"]} for x in B["stage"]],
         ["FAMILY", "OWNERS", "ELEMENTS", "OWNED_BY_S3_S7", "NO_STAGE"])
    _csv("06_S8_CANDIDATE_REGISTER.csv", B["cand"], list(B["cand"][0]))
    _csv("07_INTERFACE_DOUBLE_COUNT_AUDIT.csv", B["inter"], list(B["inter"][0]))
    _csv("08_SOURCE_CONFLICT_REGISTER.csv", B["conf"], ["CONFLICT_ID", "SOURCE", "WHERE", "DESCRIPTION", "STATE",
                                                         "AFFECTS"])
    _csv("09_MISSING_REINFORCEMENT_COMPONENTS.csv", B["miss"], list(B["miss"][0]))
    _csv("10_S8_SOURCE_EXHAUSTION.csv", B["exh"], list(B["exh"][0]))
    _json("11_S8_READINESS_DECISION.json", readiness_doc(B))
    s = summarise(B)
    _json("12_PRE_S8_SUMMARY.json", s)
    (HERE / "00_README.md").write_text(readme(B, s), encoding="utf-8")
    return s


def main():
    B = build()
    s = write(B)
    inputs = sorted({_rel(p) for p in P.values()} | {f"research/alsenan_structural_census_s1/{r}.json" for r in S1_REGS})
    man = {"round": ROUND, "date": QA_DATE, "state": "FROZEN_ANALYSIS_NO_KG", "references_read": [],
           "baseline": BASELINE_HEAD, "engine_commit_stamp": s["engine_commit"],
           "rule": "PRE-S8 changes no frozen stage and calculates no kg; S8 is not started",
           "code": {c: _sha(ROOT / c) for c in CODE}, "inputs": {i: _sha(ROOT / i) for i in inputs},
           "drawing_sha256": {"ST7757.dxf": DXF_SHA, "P7757.dxf": ARCH_SHA},
           "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "frozen_baselines": s["frozen_baselines"]}
    _json(MANIFEST_NAME, man)
    print(json.dumps({k: s[k] for k in ("elements_total", "elements_by_family", "family_states", "concrete_states",
                                        "rebar_coverage", "s8_elements", "s8_by_family", "previously_omitted",
                                        "interfaces", "readiness", "stage_kg")}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
