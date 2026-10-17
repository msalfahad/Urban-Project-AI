"""S8.7 - staircases and landings: physical population, geometry, concrete and reinforcement. Source-controlled and
blind (frozen before any comparison).

    python3 -I research/alsenan_stairs_s8_7/build_s8_7.py

Reads the registered architectural DXF (P7757: GF / 1F / 2F plans, registered onto the structural sheets by the
frozen S8.6 translations), the registered structural DXF (ST7757: the GBP / GFRS / FFRS / SFRS sheets through the
frozen S1 reader) and frozen Urban stages:
- S1 registers (slab panels, special occurrences, project rules, levels);
- S6 beam occurrences (the three 'With Stair' beams);
- S7 bar runs and release items, the S7A end-condition audit (the stair-adjacent top steel, recomputed run by run);
- S8.1 / S8.1A ground-slab population and the recovered stair bay;
- S8.6 slab-opening census rows;
- PRE-S8, through column whitelists only (its concrete-state columns are never bound to a name).
p.16 of ST7757.pdf and section A-A of the architectural PDF have no vector text: they enter as visual records read in
session from renders; the renders are client drawing and stay out of git.

Every set of drawn treads on every plan is found, assigned to one physical stair element or recorded as a repeated
view of one, and given levels, geometry and one quantity lane. A stair quantity is released only where its outline,
its levels and its thickness all have authority. No earlier Urban total, contractor figure or third-party figure is
read before the freeze.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
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
from engine.source import rebar_unit_mass as UM  # noqa: E402
from engine.source import stair_geometry as SG  # noqa: E402

ROUND = "S8_7"
DATE = "2026-10-10"
BASELINE_HEAD = "3bdc894"
POLICY = "S8_7_STAIRS_V1"
R = ROOT / "research"
BY_SHA = ROOT / "data/inputs/by_sha256"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
STRUCT_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
STRUCT_PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
ARCH_PDF_SHA = "1e7087d3e61bbb682c9107193c97550a2837e5198bde0ee311319bf7f4a08459"
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
             "S7A": R / "alsenan_slab_rebar_s7a_qa/11_S7A_FREEZE_MANIFEST.json",
             "PRE-S8": R / "pre_s8_structural_completeness/13_PRE_S8_FREEZE_MANIFEST.json",
             "S8.1": R / "alsenan_ground_slab_s8_1/11_S8_1_FREEZE_MANIFEST.json",
             "S8.1A": R / "alsenan_ground_slab_s8_1a/14_S8_1A_FREEZE_MANIFEST.json",
             "S8.2": R / "alsenan_swimming_pool_s8_2/18_S8_2_FREEZE_MANIFEST.json",
             "S8.2A": R / "alsenan_swimming_pool_s8_2a/12_S8_2A_FREEZE_MANIFEST.json",
             "S8.3": R / "alsenan_dome_ring_s8_3/16_S8_3_FREEZE_MANIFEST.json",
             "S8.3A": R / "alsenan_dome_mesh_s8_3a/09_S8_3A_FREEZE_MANIFEST.json",
             "S8.4": R / "alsenan_water_tank_s8_4/15_S8_4_FREEZE_MANIFEST.json",
             "S8.5": R / "alsenan_special_columns_s8_5/17_S8_5_FREEZE_MANIFEST.json",
             "S8.6": R / "alsenan_lintels_s8_6/15_S8_6_FREEZE_MANIFEST.json",
             "S8.6A": R / "alsenan_lintels_s8_6a/12_S8_6A_CORRECTION_MANIFEST.json"}
S83_ERRATA = R / "alsenan_dome_ring_s8_3/errata"
S1D = R / "alsenan_structural_census_s1"
S2D = R / "alsenan_structural_s2"
S31D = R / "alsenan_column_rebar_s3_1"
INDEXES = {"S1": (S1D / "INDEX.json", "registers"), "S2": (S2D / "INDEX.json", "outputs"),
           "S3": (R / "alsenan_column_rebar_s3/INDEX.json", "outputs"), "S3.1": (S31D / "INDEX.json", "outputs")}
PRE = R / "pre_s8_structural_completeness"
READ = {"S1_SLABS": S1D / "SLAB_PANEL_REGISTER.json",
        "S1_SPECIAL": S1D / "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER.json",
        "S1_RULES": S1D / "STRUCTURAL_PROJECT_RULE_REGISTER.json",
        "S1_LEVELS": S1D / "STRUCTURAL_LEVEL_REGISTER.json",
        "S6_OCC": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCES.csv",
        "S7_RUNS": R / "alsenan_slab_rebar_s7/04_S7_BAR_RUNS.csv",
        "S7_ITEMS": R / "alsenan_slab_rebar_s7/01_S7_RELEASE_ITEMS.csv",
        "S7A_AUDIT": R / "alsenan_slab_rebar_s7a_qa/08_END_CONDITION_AUDIT.csv",
        "S81_POP": R / "alsenan_ground_slab_s8_1/01_GROUND_SLAB_POPULATION_AND_ZONE_REGISTER.csv",
        "S81A_REGION": R / "alsenan_ground_slab_s8_1a/01_RECOVERED_LIFT_PIT_REGION.csv",
        "S81A_DELTA": R / "alsenan_ground_slab_s8_1a/02_POPULATION_OWNERSHIP_DELTA.csv",
        "S81A_QUESTIONS": R / "alsenan_ground_slab_s8_1a/08_CONFLICT_AND_QUESTION_REGISTER.csv",
        "S86_CENSUS": R / "alsenan_lintels_s8_6/01_OPENING_CENSUS.csv",
        "S86_REGISTRATION": R / "alsenan_lintels_s8_6/03_ARCH_STRUCTURAL_REGISTRATION.csv",
        "PRE_S8_CENSUS": PRE / "02_STRUCTURAL_ELEMENT_CENSUS.csv",
        "PRE_S8_INTERFACES": PRE / "07_INTERFACE_DOUBLE_COUNT_AUDIT.csv",
        "PRE_S8_EXHAUSTION": PRE / "10_S8_SOURCE_EXHAUSTION.csv",
        "PRE_S8_READINESS": PRE / "11_S8_READINESS_DECISION.json"}
# PRE-S8 is read for population, ownership and missing-authority claims only. Its concrete-state columns and its
# coverage matrices carry earlier figures: they are never bound to a name before the freeze.
PRE_S8_COLUMNS = {"PRE_S8_CENSUS": ("ELEMENT_ID", "ROW_KIND", "PARENT_ELEMENT", "ELEMENT_FAMILY", "FLOOR",
                                    "SOURCE_PAGE", "EXISTING_STAGE_OWNER", "NEW_S8_OWNER", "S8_SCOPE",
                                    "MISSING_INFORMATION", "CONFLICT"),
                  "PRE_S8_INTERFACES": ("INTERFACE", "SIDE_A", "SIDE_B", "RISK", "STATE"),
                  "PRE_S8_EXHAUSTION": ("S8_CANDIDATE", "CH_PLAN", "CH_SECTION", "CH_TYPICAL_DETAIL", "MISSING",
                                        "READINESS")}
PRE_S8_READINESS_KEYS = ("missing", "readiness", "schematic_nts", "dimensioned")
PRE_S8_FIREWALLED = ("CONCRETE_QUANTITY_STATE", "CONCRETE_STATES", "CONCRETE", "BARS_OWNED", "URBAN_LINES",
                     "V3B_", "CR_")
INADVERTENT_EXPOSURE = {
    "when": "S8.7 source survey, before any S8.7 quantity existed",
    "what": "one exploratory read of PRE-S8 06_S8_CANDIDATE_REGISTER.csv printed its CONCRETE_STATES cell for the "
            "stair family, which carries an earlier commercial provisional stair concrete figure",
    "use": "none: no S8.7 dimension, lane or quantity reads it; every later PRE-S8 read goes through the column "
           "whitelists above; the figure is used only by the post-freeze comparison"}
CODE = ["engine/source/stair_geometry.py", "engine/source/rebar_unit_mass.py", "engine/source/delta_release.py",
        "research/alsenan_stairs_s8_7/build_s8_7.py", "research/external_engine_lab/alsenan_structural_s1.py"]
OUTPUTS = ["00_README.md", "01_STAIR_POPULATION_CENSUS.csv", "02_TREAD_RUN_CENSUS.csv",
           "03_ASSEMBLY_FLIGHT_LANDING_CROSSWALK.csv", "04_GROUND_LEVEL_REGION_RECONCILIATION.csv",
           "05_LEVEL_REGISTER.csv", "06_PLAN_AND_INCLINED_GEOMETRY.csv", "07_CONCRETE_QTO.csv",
           "08_REBAR_ANNOTATION_BINDING.csv", "09_REBAR_QTO.csv", "10_OWNERSHIP_AUDIT.csv",
           "11_S7_STAIR_ADJACENT_RECOMPUTE.csv", "12_BLOCKED_AND_CONFLICTS.csv", "13_PRE_S8_CONDITION_RESOLUTION.csv",
           "14_PROVENANCE.jsonl", "15_CONSERVATION_CHECKS.csv", "16_S8_7_SUMMARY.json"]
MANIFEST_NAME = "17_S8_7_FREEZE_MANIFEST.json"
UNIT_MASS = {"method": UM.D2_OVER_162, "authority": "project-wide method used by S3.1 / S6.1 / S7 / S8",
             "selected_by": "Urban (project basis)"}
SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO = "SOURCE_DERIVED_PHYSICAL", "PROJECT_BASIS_QTO"
BLOCKED, CONFLICT, SENS = "BLOCKED_UNQUANTIFIED", "SOURCE_CONFLICT", "SENSITIVITY_ONLY"
RELEASED_LANES = (SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO)
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")


class Stop(RuntimeError):
    pass


def check(cond, msg):
    if not cond:
        raise Stop(msg)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _full(v, nd=9):
    s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
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


def _r(v, nd=9):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


def _csv(name, rows, fields=None):
    fields = fields or list(rows[0])
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


def kg_per_m(d):
    return UM.kg_per_m(d, UNIT_MASS)


# ------------------------------------------------------------------ inputs
def verify_inputs():
    for sha, name, ext in ((ARCH_SHA, "P7757.dxf", "dxf"), (STRUCT_SHA, "ST7757.dxf", "dxf"),
                           (STRUCT_PDF_SHA, "ST7757.pdf", "pdf"), (ARCH_PDF_SHA, "P7757 sections PDF", "pdf")):
        f = BY_SHA / f"{sha}.{ext}"
        check(f.exists(), f"private input {name} not in data/inputs/by_sha256 (never committed)")
        check(_sha(f) == sha, f"{name} unchanged")
    frozen = {k: DR.verify_frozen(m, ROOT) for k, m in MANIFESTS.items()}
    errata = _j(R / "alsenan_dome_mesh_s8_3a/07_FROZEN_VERIFICATION.json")["s8_3_errata_sha256"]
    for name, h in errata.items():
        check(_sha(S83_ERRATA / name) == h, f"S8.3 errata {name} unchanged")
    index = {}
    for k, (p, key) in INDEXES.items():
        n = 0
        for name, v in _j(p)[key].items():
            h = v["sha256"] if isinstance(v, dict) else v
            f = p.parent / (v["file"] if isinstance(v, dict) else name)
            check(_sha(f) == h, f"{k} register {name} unchanged")
            n += 1
        index[k] = {"index_sha256": _sha(p), "registers_verified": n}
    return frozen, errata, index


def pre_s8(key, pattern=r"STAIR"):
    """PRE-S8 rows of the stair family, whitelisted columns only."""
    cols = PRE_S8_COLUMNS[key]
    check(not [c for c in cols for f in PRE_S8_FIREWALLED if c.startswith(f)],
          "PRE-S8 whitelist excludes the firewalled columns")
    with open(READ[key], encoding="utf-8", newline="") as fh:
        rd = csv.reader(fh)
        head = next(rd)
        idx = {c: head.index(c) for c in cols}
        out = []
        for row in rd:
            rec = {c: row[i] for c, i in idx.items()}
            if re.search(pattern, " ".join(rec.values()), re.I):
                out.append(rec)
    return out


def pre_s8_readiness():
    d = _j(READ["PRE_S8_READINESS"])["candidates"]["STAIR_AND_LANDING"]
    return {k: d.get(k) for k in PRE_S8_READINESS_KEYS}


# ------------------------------------------------------------------ visual records (no vector text in the PDFs)
P16 = "ST7757.pdf p.16 'TYPICAL STEEL LAYOUT-STAIR SECTION.' (N.I.S.) and 'TYPICAL DETAIL OF STAIR BEAM' (visual)"
P16_CALLOUTS = [
    # callout, where it sits on the typical section, physical role, layer / shape
    ("8Ø16/m", "along the waist of both flights at the soffit, continuing into the landing bottom", "MAIN_BOTTOM",
     "bottom, longitudinal; bent at the landing junction"),
    ("6Ø14/m", "top bars over each flight-landing junction and at the top beam, bent to the pitch", "TOP_JUNCTION_BENT",
     "top, cranked over the kink"),
    ("6Ø12/m", "landing top layer, straight over the landing", "LANDING_TOP", "top, landing"),
    ("Ø12/20cm", "transverse bars on the main bars along the waist (both flights)", "DISTRIBUTION_TRANSVERSE",
     "bottom, transverse"),
    ("Ø8/15", "bent bar inside each step (tread / riser shape)", "STEP_BAR", "in each step"),
    ("1Ø12", "one bar along each step at the nosing corner", "NOSING_CORNER_BAR", "in each step, longitudinal"),
    ("6Ø16/m", "top bars of the first flight entering the ground beam G.B", "STARTER_FROM_GROUND_BEAM",
     "top, anchored in the G.B"),
    ("2Ø12 / 4Ø16", "landing edge beam 20 x 40 cm: top / bottom", "LANDING_EDGE_BEAM", "beam"),
    ("3Ø14 / 4Ø16 / 2Ø14/30cm / Ø8/15cm", "ground beam G.B 30 cm wide on 50 x 10 cm blinding: top / bottom / side / "
     "stirrups; T.O.B +0.00, S.S.L -0.05", "GROUND_BEAM_AT_FIRST_FLIGHT", "beam"),
    ("2Ø12 / 4Ø16 / 6Ø8/m", "TYPICAL DETAIL OF STAIR BEAM (depth AS PER SCH.) framing into a column: top / bottom / "
     "stirrups", "STAIR_BEAM", "beam"),
]
P16_GEOMETRY = {"goings": "'30' (cm) dimensioned on two treads", "waist": "'THICK' leader on the waist with no value",
                "landing": "'LANDING (S.S.L +2.00)'; landing edge beam 20 x 40",
                "levels": "+0.00 T.O.B / -0.05 S.S.L / +2.00 landing / +4.00 and +3.95 S.S.L at the top beam",
                "scale": "N.I.S. (typical: its levels are not this villa's levels)"}
SECTION_AA = "P7757 architectural sections PDF sheet 4, SECTION A-A (visual, scaled drawing)"
SECTION_AA_FACTS = [
    ("LEVELS", "+0.00 / +0.15 / +0.30 / +1.00 / +5.50 / +9.70 / +13.90 printed"),
    ("HALF_LANDING_GF_1F", "dimension '320' from the +0.30 lobby floor to the top of the half-landing slab: +3.50"),
    ("HALF_LANDING_1F_2F", "no level and no dimension; drawn about 2.00 m below +9.70 (scaled only)"),
    ("CUT_FLIGHT_GF_1F", "upper flight (half-landing up to +5.50) cut: 12 risers, 11 treads drawn"),
    ("CUT_FLIGHT_1F_2F", "upper flight (half-landing up to +9.70) cut: 12 risers, 11 treads drawn"),
    ("LOWER_FLIGHTS", "seen in elevation behind balustrades: risers not countable"),
    ("LOBBY_STEPS", "steps cut from the +1.00 floor down to the +0.30 lobby, on grade"),
    ("STEPS_MONOLITHIC", "cut flights hatched as one solid with the waist and the landing"),
    ("HALF_LANDING_SUPPORT", "each half-landing ends on a downstand at the north wall"),
]
SECTION_LEVELS = {"HALF_LANDING_GF_1F_M": 3.5, "LOBBY_M": 0.3, "DIM_320_M": 3.2}

# ------------------------------------------------------------------ cited drawing geometry (checked against the DXF)
X_BAY_W, X_WALL_W, X_WALL_E, X_BAY_E = 17087.904, 18287.904, 18387.904, 19587.904
Y_BAY_N, Y_WALL_END, Y_ZONE_S = 20611.856, 19411.856, 16311.856
X_GBP_W, Y_GBP_S, Y_GBP_N = 17187.904, 15711.856, 20511.856
WELL_C, WELL_R_IN, WELL_R_OUT = (23673.334, 11742.299), 1530.511, 2780.511
Y_WELL_S, Y_WELL_VOID_S, X_WELL_E, Y_WELL_N = 9011.856, 10211.856, 27907.904, 12961.856
CITED = [  # sheet, handle, kind, coordinates that the constants above are read from
    ("GFRS", "279", "LINE", ((19587.904, 20611.856), (17087.904, 20611.856)), "main bay north edge"),
    ("GFRS", "284", "LINE", ((17087.904, 20311.856), (17087.904, 16311.856)), "main bay west edge"),
    ("GFRS", "256", "LINE", ((18287.904, 16311.856), (18287.904, 19411.856)), "central wall west face"),
    ("GFRS", "25A", "LINE", ((18387.904, 16311.856), (18387.904, 19411.856)), "central wall east face"),
    ("GFRS", "25F", "LINE", ((18387.904, 19411.856), (18287.904, 19411.856)), "central wall north end"),
    ("GFRS", "2F3", "LINE", ((18387.904, 19461.856), (18387.904, 20611.856)), "last winder riser (GF->1F)"),
    ("FFRS", "62D", "LINE", ((18287.904, 16311.856), (18287.904, 19411.856)), "central wall west face (1F)"),
    ("FFRS", "62E", "LINE", ((18387.904, 16311.856), (18387.904, 19411.856)), "central wall east face (1F)"),
    ("FFRS", "5E2", "LINE", ((18387.904, 19461.856), (18387.904, 20611.856)), "NE landing west edge (1F)"),
    ("FFRS", "5C0", "LINE", ((31557.904, 20611.856), (17087.904, 20611.856)), "main bay north edge (1F)"),
    ("GBP", "7CC", "LINE", ((19587.904, 15711.856), (17187.904, 15711.856)), "stair bay south edge (ground)"),
    ("GBP", "143", "LINE", ((18287.904, 16711.856), (18287.904, 18732.067)), "central wall west face (ground)"),
    ("GBP", "1C3", "LINE", ((18387.904, 16711.856), (18387.904, 19461.856)), "central wall east face (ground)"),
    ("GFRS", "2DD", "ARC", ((23673.334, 11742.299), 2780.511), "light-well flight outer boundary"),
    ("GFRS", "2DE", "ARC", ((23673.334, 11742.299), 1530.511), "light-well flight inner boundary (void edge)"),
    ("GFRS", "2D0", "LINE", ((26707.904, 10211.856), (23658.825, 10211.856)), "light-well void south edge"),
    ("GFRS", "289", "LINE", ((27907.904, 9011.856), (27907.904, 11411.856)), "light-well stair east edge"),
    ("GFRS", "2CE", "LINE", ((20887.904, 12961.856), (27660.991, 12961.856)), "light-well north edge"),
    ("GFRS", "2CF", "LINE", ((26707.904, 12961.856), (26707.904, 10211.856)), "light-well void east edge"),
    ("GFRS", "2CC", "LINE", ((27282.904, 9011.856), (27282.904, 12961.856)), "bar line 8Ø16/m north flight"),
    ("GFRS", "535", "LINE", ((23690.552, 9636.856), (27735.217, 9636.856)), "bar line 8Ø16/m straight flight"),
    ("GFRS", "44A", "LINE", ((18962.904, 20611.856), (18962.904, 16311.856)), "bar line 8Ø16/m east flight"),
    ("GFRS", "451", "LINE", ((17332.45, 20086.856), (19293.869, 20086.856)), "bar line 8Ø16/m north strip"),
]


# ------------------------------------------------------------------ drawings
def structural():
    import alsenan_structural_s1 as S1
    E = S1.Source().entities()
    by = {(sh, e["handle"]): e for sh in E for e in E[sh]}
    for sh, h, kind, geo, what in CITED:
        e = by.get((sh, h))
        check(e is not None and e["type"] == kind, f"cited {sh} {h} ({what}) exists")
        if kind == "LINE":
            check(math.dist(e["a"][:2], geo[0]) < 0.01 and math.dist(e["b"][:2], geo[1]) < 0.01,
                  f"cited {sh} {h} ({what}) coordinates")
        else:
            check(math.dist(e["c"][:2], geo[0]) < 0.01 and abs(e["r"] - geo[1]) < 0.01, f"cited {sh} {h} ({what})")
    return E, by


def registration():
    T = {}
    for r in _rows(READ["S86_REGISTRATION"]):
        if r["RECORD"] == "FLOOR":
            T[r["FLOOR"]] = (r["SHEET"], float(r["TX_MM"]), float(r["TY_MM"]), int(r["VOTES"]))
    check(set(T) == {"GF", "1F", "2F"}, "S8.6 registers the three plans")
    return T


def architectural(T):
    import ezdxf
    doc = ezdxf.readfile(str(BY_SHA / f"{ARCH_SHA}.dxf"))
    msp = doc.modelspace()
    frames = {}
    for e in msp:
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "1" and e.closed:
            pts = [(p[0], p[1]) for p in e.get_points("xy")]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            if abs(max(xs) - min(xs) - 40314) < 1 and abs(max(ys) - min(ys) - 28030) < 1:
                frames[e.dxf.handle] = (min(xs), min(ys), max(xs), max(ys))
    out = {fl: {"lines": [], "levels": [], "dims": []} for fl in T}
    hidden = {L.dxf.name for L in doc.layers if (L.dxf.linetype or "").upper() == "HIDDEN"}
    for fl, (sheet, tx, ty, _) in T.items():
        # the plan frame that the registration translation maps onto the structural sheet frame
        m = WIN["MAIN"]
        cand = [b for b in frames.values() if b[0] + tx <= m[0] and b[1] + ty <= m[1] and b[2] + tx >= m[2]
                and b[3] + ty >= m[3]]
        check(len(cand) == 1, f"{fl}: one plan frame registers onto {sheet}")
        out[fl]["frame"] = cand[0]
    for e in msp:
        t = e.dxftype()
        if t not in ("LINE", "TEXT", "MTEXT", "DIMENSION"):
            continue
        p = (e.dxf.start.x, e.dxf.start.y) if t == "LINE" else \
            ((e.dxf.defpoint2.x, e.dxf.defpoint2.y) if t == "DIMENSION" else (e.dxf.insert.x, e.dxf.insert.y))
        for fl, (sheet, tx, ty, _) in T.items():
            x0, y0, x1, y1 = out[fl]["frame"]
            if not (x0 <= p[0] <= x1 and y0 <= p[1] <= y1):
                continue
            if t == "LINE":
                a = (e.dxf.start.x + tx, e.dxf.start.y + ty)
                b = (e.dxf.end.x + tx, e.dxf.end.y + ty)
                out[fl]["lines"].append({"handle": e.dxf.handle, "layer": e.dxf.layer, "a": a, "b": b,
                                         "hidden": e.dxf.layer in hidden})
            elif t == "DIMENSION":
                q = (e.dxf.defpoint3.x + tx, e.dxf.defpoint3.y + ty)
                out[fl]["dims"].append({"handle": e.dxf.handle, "a": (p[0] + tx, p[1] + ty), "b": q,
                                        "m": float(e.get_measurement())})
            else:
                s = e.dxf.text if t == "TEXT" else e.text
                if re.fullmatch(r"\s*(%%[pP]|[+\-±])\s*\d+\.\d\d\s*", s or ""):
                    out[fl]["levels"].append({"handle": e.dxf.handle, "text": s.strip(), "layer": e.dxf.layer,
                                              "p": (p[0] + tx, p[1] + ty)})
            break
    return out


def _inside(p, box):
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]


def _axis(a, b):
    if abs(a[1] - b[1]) < 0.5:
        return "H"
    if abs(a[0] - b[0]) < 0.5:
        return "V"
    return "R"


def struct_lines(E, sheet, box, lo=600.0, hi=6000.0):
    out = []
    for e in E[sheet]:
        if e["type"] != "LINE":
            continue
        a, b = tuple(e["a"][:2]), tuple(e["b"][:2])
        if _inside(a, box) and _inside(b, box) and lo <= math.dist(a, b) <= hi:
            out.append({"handle": e["handle"], "layer": e["layer"], "a": a, "b": b, "hidden": False})
    return out


def arch_lines(A, fl, box, lo=600.0, hi=6000.0):
    return [x for x in A[fl]["lines"] if _inside(x["a"], box) and _inside(x["b"], box)
            and lo <= math.dist(x["a"], x["b"]) <= hi]


def cluster(vals, tol=60.0):
    out = []
    for v in sorted(vals):
        if out and v - out[-1][-1] <= tol:
            out[-1].append(v)
        else:
            out.append([v])
    return [sum(c) / len(c) for c in out]


# ------------------------------------------------------------------ windows (sheet-local mm)
WIN = {"MAIN": (16900.0, 15400.0, 19800.0, 21100.0), "WELL": (20500.0, 8800.0, 28500.0, 13300.0),
       "ENTRANCE": (13600.0, 12000.0, 16000.0, 15500.0)}
SHEETS = ("GBP", "GFRS", "FFRS", "SFRS")
FLOOR_SHEET = {"GF": "GFRS", "1F": "FFRS", "2F": "SFRS"}


def tread_census(E, A):
    """every regular set of drawn treads in the three windows, on every sheet and plan, any layer."""
    runs = []
    for src, views in (("ST7757", SHEETS), ("P7757", ("GF", "1F", "2F"))):
        for v in views:
            for wn, box in WIN.items():
                L = struct_lines(E, v, box) if src == "ST7757" else arch_lines(A, v, box)
                bylayer = defaultdict(list)
                for x in L:
                    if _axis(x["a"], x["b"]) != "R":
                        bylayer[x["layer"]].append(x)
                for layer, xs in sorted(bylayer.items()):
                    segs = [(x["handle"], x["a"], x["b"]) for x in xs]
                    for r in SG.detect_tread_runs(segs, pitch=(230.0, 360.0), len_tol=60.0, min_lines=3):
                        runs.append({"source": src, "view": v, "window": wn, "layer": layer,
                                     "hidden": any(x["hidden"] for x in xs if x["handle"] in r["ids"]), **r})
                radial = [x for x in L if _axis(x["a"], x["b"]) == "R" and 1000 <= math.dist(x["a"], x["b"]) <= 1700]
                if len(radial) >= 2:
                    runs.append({"source": src, "view": v, "window": wn, "layer": "+".join(sorted({x["layer"] for x in radial})),
                                 "hidden": all(x["hidden"] for x in radial), "ids": [x["handle"] for x in radial],
                                 "angle": None, "count": len(radial), "pitches": [], "length": None,
                                 "offsets": [], "along": None, "radial": True,
                                 "segments": [(x["handle"], x["a"], x["b"]) for x in radial]})
    return runs


# ------------------------------------------------------------------ population: every run to one element
STAIRS = {
    "ST-A": {"name": "main stair (dog-leg, two flights, winder turn and half-landing per storey)", "kind": "STAIRCASE",
             "floors": "GF -> 1F -> 2F", "zones": ["SP-GF_ROOF_SLAB-03", "SP-1F_ROOF_SLAB-01"]},
    "ST-B": {"name": "lobby steps from the GF floor down to the +0.30 side lobby", "kind": "STEP_FLIGHT",
             "floors": "GF", "zones": []},
    "ST-C": {"name": "light-well stair (curved flight into a straight flight, corner landing, short flight)",
             "kind": "STAIRCASE", "floors": "GF -> 1F", "zones": ["SP-GF_ROOF_SLAB-21", "SP-GF_ROOF_SLAB-28"]},
    "ST-D": {"name": "external entrance steps from the garden to the entrance porch", "kind": "STEP_FLIGHT",
             "floors": "GF (outside)", "zones": []},
}
ELEMENTS = [  # id, stair, storey run, kind, primary structural view, primary architectural view
    ("A1-F1", "ST-A", "A1 GF->1F", "FLIGHT", "GFRS", "GF"),
    ("A1-W1", "ST-A", "A1 GF->1F", "WINDER_TURN", "GFRS", "GF"),
    ("A1-L1", "ST-A", "A1 GF->1F", "HALF_LANDING", "GFRS", "GF"),
    ("A1-F2", "ST-A", "A1 GF->1F", "FLIGHT", "GFRS", "GF"),
    ("A2-F1", "ST-A", "A2 1F->2F", "FLIGHT", "FFRS", "1F"),
    ("A2-W1", "ST-A", "A2 1F->2F", "WINDER_TURN", "FFRS", "1F"),
    ("A2-L1", "ST-A", "A2 1F->2F", "HALF_LANDING", "FFRS", "1F"),
    ("A2-F2", "ST-A", "A2 1F->2F", "FLIGHT", "FFRS", "1F"),
    ("A2-T1", "ST-A", "A2 1F->2F", "TOP_ARRIVAL", "FFRS", "1F"),
    ("B-F1", "ST-B", "B GF", "STEP_FLIGHT", "GBP", "GF"),
    ("C-F1", "ST-C", "C GF->1F", "FLIGHT (curved part + straight part, no landing between)", "GFRS", "1F"),
    ("C-L1", "ST-C", "C GF->1F", "CORNER_LANDING", "GFRS", "1F"),
    ("C-F2", "ST-C", "C GF->1F", "FLIGHT", "GFRS", "1F"),
    ("C-T1", "ST-C", "C GF->1F", "TOP_ARRIVAL", "GFRS", "1F"),
    ("D-F1", "ST-D", "D GF outside", "STEP_FLIGHT", "GBP", "GF"),
]
KIND = {e[0]: e[3] for e in ELEMENTS}


def assign(run):
    """(element, view role) for one detected run. Roles: PRIMARY (the view the element is measured on), SECOND_VIEW
    (another drawing of the same element) and REPEATED_VIEW (the same element shown on a sheet of another level)."""
    src, v, w = run["source"], run["view"], run["window"]
    if run.get("radial"):
        if w == "WELL":
            return ("C-F1", {"GFRS": "PRIMARY", "GBP": "REPEATED_VIEW", "1F": "PRIMARY_ARCH",
                             "GF": "SECOND_VIEW"}[v])
        if w == "MAIN":
            if run["quadrant"] != "NW":
                return ("NONE", f"UNEXPLAINED_DIAGONAL_{run['quadrant']}")
            if src == "ST7757":
                return ("A1-W1" if v == "GFRS" else "A2-W1", "PRIMARY")
            return ({"GF": "A1-W1", "1F": "A2-W1"}[v], "PRIMARY_ARCH")
    lo, hi = run["along"]
    if w == "MAIN":
        west = hi <= X_WALL_W + 1
        if src == "ST7757":
            if v == "GBP":
                return ("A1-F1", "REPEATED_VIEW") if west else ("B-F1", "PRIMARY")
            el = {("GFRS", True): "A1-F1", ("GFRS", False): "A1-F2", ("FFRS", True): "A2-F1",
                  ("FFRS", False): "A2-F2"}[(v, west)]
            return (el, "PRIMARY")
        if v == "GF":
            if not west and not run["hidden"]:
                return ("B-F1", "PRIMARY_ARCH")
            return ("A1-F1" if west else "A1-F2", "PRIMARY_ARCH")
        if v == "1F":
            return ("A2-F1" if west else "A2-F2", "PRIMARY_ARCH")
        return ("A2-F1" if west else "A2-F2", "REPEATED_VIEW")
    if w == "WELL":
        role = {"GFRS": "PRIMARY", "1F": "PRIMARY_ARCH", "GF": "SECOND_VIEW"}.get(v, "REPEATED_VIEW")
        return ("C-F1" if run["angle"] == 90.0 else "C-F2", role)
    if w == "ENTRANCE":
        return ("D-F1", "PRIMARY" if src == "ST7757" else "PRIMARY_ARCH")
    return ("NONE", "UNASSIGNED")


def _dir_cluster(angles, tol=2.0):
    """line directions (degrees mod 180) of radial treads; parallel paired lines merge."""
    a = sorted(x % 180.0 for x in angles)
    out = []
    for v in a:
        if out and v - out[-1][-1] <= tol:
            out[-1].append(v)
        else:
            out.append([v])
    if len(out) > 1 and out[0][0] + 180.0 - out[-1][-1] <= tol:
        out[0] = out[-1] + out[0]
        out.pop()
    return [sum(c) / len(c) for c in out]


def tread_positions(runs, el, role):
    """riser lines of one element in one view: every drawn line once, paired lines (nosing + riser, 50 mm apart, or
    parallel radial pairs) once. Returns (straight offsets, radial directions)."""
    offs, dirs = [], []
    for r in runs:
        if r["assigned"] != (el, role):
            continue
        if r.get("radial"):
            dirs += [math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) for _, a, b in r["segments"]]
        else:
            offs += [abs(o) for o in r["offsets"]]
    return (cluster(offs, 60.0) if offs else []), (_dir_cluster(dirs) if dirs else [])


def population(E, A):
    runs = tread_census(E, A)
    out = []
    for r in runs:
        if r.get("radial") and r["window"] == "MAIN":
            quads = defaultdict(list)
            for sgm in r["segments"]:
                (x0, y0), (x1, y1) = sgm[1], sgm[2]
                q = ("N" if min(y0, y1) > Y_WALL_END - 50 else "S") + ("W" if max(x0, x1) < X_WALL_E + 50 else "E")
                quads[q].append(sgm)
            for q, sg in sorted(quads.items()):
                out.append({**r, "segments": sg, "ids": [x[0] for x in sg], "count": len(sg), "quadrant": q})
        elif r.get("radial") and r["window"] == "WELL" and "S-OPENING" in r["layer"]:
            keep = [s for s in r["segments"] if by_layer(E, r["view"], s[0]) == "2"]
            gone = [s[0] for s in r["segments"] if by_layer(E, r["view"], s[0]) != "2"]
            out.append({**r, "segments": keep, "ids": [s[0] for s in keep], "count": len(keep), "layer": "2",
                        "excluded_ids": gone})
        else:
            out.append(r)
    for r in out:
        r["assigned"] = assign(r)
    check(not [r for r in out if r["assigned"][1] == "UNASSIGNED"], "every tread run is assigned")
    return out


_LAYER = {}


def by_layer(E, sheet, handle):
    if not _LAYER:
        for sh in E:
            for e in E[sh]:
                _LAYER[(sh, e["handle"])] = e["layer"]
    return _LAYER.get((sheet, handle))


# ------------------------------------------------------------------ element geometry
WAIST_TAG_MM = 160.0          # the 'T' / '16' thickness tag inside each stair zone (S1 thickness_note 160)
GOING_MM = 300.0              # the drawn pitch of every tread set (both drawings); p.16 dimensions '30' typical
CLOSING_RISER = {"GFRS": ["2F3"], "FFRS": ["5E2"], "GF": ["2C6", "49C", "49D"], "1F": ["BE4", "BE5"]}


def _rect(x0, y0, x1, y1):
    from shapely.geometry import box
    return box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def _arc_pts(c, r, a0, a1, step_deg=0.05):
    n = max(2, int(abs(a1 - a0) / math.radians(step_deg)) + 1)
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * k / (n - 1)), c[1] + r * math.sin(a0 + (a1 - a0) * k / (n - 1)))
            for k in range(n)]


def light_well_band(by, first_line):
    """the curved + straight band of the light-well flight: outer arc 2DD, south edge, last straight riser line,
    void edge 2D0, inner arc 2DE; cut at the first riser line (the side holding the flight)."""
    from shapely.geometry import Polygon, LineString
    from shapely.ops import split
    o, i = by[("GFRS", "2DD")], by[("GFRS", "2DE")]
    pts = _arc_pts(WELL_C, WELL_R_OUT, o["a0"], o["a1"])
    pts += [(X_LAST_STRAIGHT, Y_WELL_S), (X_LAST_STRAIGHT, Y_WELL_VOID_S), (by[("GFRS", "2D0")]["b"][0], Y_WELL_VOID_S)]
    pts += list(reversed(_arc_pts(WELL_C, WELL_R_IN, i["a0"], i["a1"])))
    band = Polygon(pts).buffer(0)
    (ax, ay), (bx, by_) = first_line
    dx, dy = bx - ax, by_ - ay
    cut = LineString([(ax - 3 * dx, ay - 3 * dy), (bx + 3 * dx, by_ + 3 * dy)])
    parts = sorted(split(band, cut).geoms, key=lambda g: -g.area)
    return parts[0], band


X_LAST_STRAIGHT = 26757.904


def columns(E, sheet, box):
    out = []
    for e in E[sheet]:
        if e["type"] == "LWPOLYLINE" and e["layer"] == "S-COL.BON" and e.get("closed"):
            xs, ys = [q[0] for q in e["pts"]], [q[1] for q in e["pts"]]
            if min(xs) < box[2] and max(xs) > box[0] and min(ys) < box[3] and max(ys) > box[1]:
                out.append((e["handle"], _rect(min(xs), min(ys), max(xs), max(ys))))
    return out


def element_geometry(E, by, runs, zones):
    """plan outline of every element on its structural sheet: drawn riser lines, wall faces and bay edges; column
    outlines are taken out (a flight never passes through a column)."""
    from shapely.geometry import Polygon
    pos = {}
    for el, *_ in ELEMENTS:
        for role in ("PRIMARY", "PRIMARY_ARCH", "SECOND_VIEW", "REPEATED_VIEW"):
            pos[(el, role)] = tread_positions(runs, el, role)
    st = {el: pos[(el, "PRIMARY")][0] for el, *_ in ELEMENTS}
    check(abs(max(st["C-F1"]) - X_LAST_STRAIGHT) < 0.01, "last straight riser of the light-well flight")
    g = {}
    for a, sheet in (("A1", "GFRS"), ("A2", "FFRS")):
        f1, f2 = st[f"{a}-F1"], st[f"{a}-F2"]
        g[f"{a}-F1"] = _rect(X_BAY_W, min(f1), X_WALL_W, max(f1))
        g[f"{a}-W1"] = Polygon([(X_BAY_W, max(f1)), (X_WALL_W, max(f1)), (X_WALL_W, Y_WALL_END), (X_WALL_E, Y_WALL_END),
                                (X_WALL_E, Y_BAY_N), (X_BAY_W, Y_BAY_N)])
        g[f"{a}-L1"] = _rect(X_WALL_E, max(f2), X_BAY_E, Y_BAY_N)
        g[f"{a}-F2"] = _rect(X_WALL_E, min(f2), X_BAY_E, max(f2))
    top = zones["SP-1F_ROOF_SLAB-01"].intersection(_rect(X_WALL_E, Y_ZONE_S - 1.0, X_BAY_E, min(st["A2-F2"])))
    check(top.area > 1.0, "the 1F -> 2F arrival strip between the beam face and the last riser")
    g["A2-T1"] = top
    b = st["B-F1"]
    g["B-F1"] = _rect(X_WALL_E, min(b), X_BAY_E, max(b))
    first = by[("GFRS", "2EA")]
    g["C-F1"], band = light_well_band(by, (first["a"][:2], first["b"][:2]))
    c2 = st["C-F2"]
    g["C-L1"] = _rect(X_LAST_STRAIGHT, Y_WELL_S, X_WELL_E, min(c2))
    g["C-F2"] = _rect(X_VOID_E, min(c2), X_WELL_E, max(c2))
    g["C-T1"] = zones["SP-GF_ROOF_SLAB-28"].intersection(_rect(X_VOID_E, max(c2), X_WELL_E + 1.0, Y_WELL_N))
    d = st["D-F1"]
    lines = [by[("GBP", h)] for h in ("179", "18A")]
    g["D-F1"] = _rect(min(d), lines[0]["b"][1], max(d), lines[0]["a"][1])
    cut = {}
    for el, stair, run_, kind, sheet, floor in ELEMENTS:
        for h, c in columns(E, sheet, g[el].bounds):
            if g[el].intersection(c).area > 1.0:
                cut.setdefault(el, []).append((h, g[el].intersection(c).area / 1e6))
                g[el] = g[el].difference(c)
    return g, pos, band, cut


X_VOID_E = 26707.904


def counts(by, A, pos):
    """riser lines per element and view; the closing riser of each winder turn is a single vertical line."""
    out = {}
    for el, stair, run_, kind, sheet, floor in ELEMENTS:
        sp, sr = pos[(el, "PRIMARY")]
        ap, ar = pos[(el, "PRIMARY_ARCH")]
        n_s, n_a = len(sp) + len(sr), len(ap) + len(ar)
        if kind == "WINDER_TURN":
            hs = [h for h in CLOSING_RISER[sheet] if (sheet, h) in by]
            ha = [x["handle"] for x in A[floor]["lines"] if x["handle"] in CLOSING_RISER[floor]]
            n_s += 1 if hs else 0
            n_a += 1 if ha else 0
        out[el] = {"struct": n_s if (sp or sr or kind == "WINDER_TURN") else None,
                   "arch": n_a if (ap or ar or kind == "WINDER_TURN") else None,
                   "struct_radial": len(sr), "arch_radial": len(ar),
                   "second": (lambda p: len(p[0]) + len(p[1]) if (p[0] or p[1]) else None)(pos[(el, "SECOND_VIEW")]),
                   "repeated": (lambda p: len(p[0]) + len(p[1]) if (p[0] or p[1]) else None)(pos[(el, "REPEATED_VIEW")])}
    out["A1-F2"]["section"] = 12
    out["A2-F2"]["section"] = 12
    return out



# ------------------------------------------------------------------ levels
LEVEL_OF = {  # element: (from, to); each entry (value_m or None, state, basis)
    "A1-F1": ((1.0, "PRINTED", "'+1.00' in the bay (GBP 1C2 / P7757 GF 413) = S1 GF FFL"),
              (None, "NOT_PRINTED", "the winder turn follows; the level where the straight part ends is not given")),
    "A1-W1": ((None, "NOT_PRINTED", "inside the turn"),
              (3.5, "DERIVED_FROM_PRINTED", "SECTION A-A '320' from the printed +0.30 lobby to the half-landing top")),
    "A1-L1": ((3.5, "DERIVED_FROM_PRINTED", "SECTION A-A: +0.30 + 3.20 (printed dimension) = +3.50"),
              (3.5, "DERIVED_FROM_PRINTED", "flat")),
    "A1-F2": ((3.5, "DERIVED_FROM_PRINTED", "the half-landing"),
              (5.5, "PRINTED", "'+5.50' south of the bay (P7757 1F D18) = S1 1F FFL")),
    "A2-F1": ((5.5, "PRINTED", "'+5.50' (P7757 1F D18) = S1 1F FFL"),
              (None, "NOT_PRINTED", "the winder turn follows")),
    "A2-W1": ((None, "NOT_PRINTED", "inside the turn"),
              (None, "NOT_PRINTED", "the 1F -> 2F half-landing carries no level and no dimension")),
    "A2-L1": ((None, "NOT_PRINTED", "SECTION A-A draws it about 2.00 m below +9.70 (scaled, sensitivity only)"),
              (None, "NOT_PRINTED", "flat")),
    "A2-F2": ((None, "NOT_PRINTED", "the half-landing"),
              (9.7, "PRINTED", "'+9.70' south of the bay (P7757 2F 134E) = S1 2F FFL")),
    "A2-T1": ((9.7, "PRINTED", "'+9.70' (P7757 2F 134E)"), (9.7, "PRINTED", "flat")),
    "B-F1": ((1.0, "PRINTED", "'+1.00' in the bay (GBP 1C2)"), (0.3, "PRINTED", "'+0.30' lobby (GBP 1C9)")),
    "C-F1": ((1.0, "PRINTED", "GF FFL +1.00 (S1; '+1.00' 40F / GBP 1BE in the hall)"),
             (None, "NOT_PRINTED", "the corner landing carries no level")),
    "C-L1": ((None, "NOT_PRINTED", "no level, no section through the light-well stair"),
             (None, "NOT_PRINTED", "flat")),
    "C-F2": ((None, "NOT_PRINTED", "the corner landing"),
             (5.5, "PRINTED", "'+5.50' at the arrival (P7757 1F D16)")),
    "C-T1": ((5.5, "PRINTED", "'+5.50' (P7757 1F D16)"), (5.5, "PRINTED", "flat")),
    "D-F1": ((0.15, "PRINTED", "'+0.15' at the foot (GBP 1B8 / P7757 GF 409)"),
             (1.0, "PRINTED_NEAREST", "'+1.00' (GBP 1C0 / P7757 GF 411) is the nearest mark on the porch side; "
                                      "its binding to the top of the steps is project basis")),
}


def level_register(A, E, S1L):
    rows = []
    for fl in ("GF", "1F", "2F"):
        for x in sorted(A[fl]["levels"], key=lambda q: q["handle"]):
            near = [w for w, b in WIN.items() if _inside(x["p"], (b[0] - 3000, b[1] - 3000, b[2] + 3000, b[3] + 3000))]
            rows.append({"LEVEL_ID": f"ARCH-{fl}-{x['handle']}", "SOURCE": f"P7757 {fl} plan (registered)",
                         "TEXT": x["text"], "VALUE_M": _level(x["text"]), "POSITION_MM": [round(v, 3) for v in x["p"]],
                         "NEAR_STAIR_WINDOW": near, "STATE": "PRINTED", "USE": ""})
    for m in _j(READ["S1_LEVELS"])["printed_marks"]:
        rows.append({"LEVEL_ID": f"STRUCT-{m['sheet']}-{m['handle'].split(':')[0]}", "SOURCE": f"ST7757 {m['sheet']} (S1)",
                     "TEXT": m["raw"], "VALUE_M": _level(m["raw"]), "POSITION_MM": m["position_mm"],
                     "NEAR_STAIR_WINDOW": [w for w, b in WIN.items()
                                           if _inside(m["position_mm"], (b[0] - 3000, b[1] - 3000, b[2] + 3000,
                                                                          b[3] + 3000))],
                     "STATE": "PRINTED", "USE": ""})
    for r in _j(READ["S1_LEVELS"])["rows"]:
        if r["kind"] in ("FFL", "FFL / ROOF", "ROOF_LEVEL"):
            rows.append({"LEVEL_ID": f"S1-{r['level'].replace(' ', '_').replace('/', '')}", "SOURCE": "S1 level register",
                         "TEXT": r["level"], "VALUE_M": r["value_m"], "POSITION_MM": None, "NEAR_STAIR_WINDOW": [],
                         "STATE": r["status"], "USE": r["source"]})
    for k, v in SECTION_AA_FACTS:
        rows.append({"LEVEL_ID": f"SECTION-AA-{k}", "SOURCE": SECTION_AA, "TEXT": v,
                     "VALUE_M": SECTION_LEVELS["HALF_LANDING_GF_1F_M"] if k == "HALF_LANDING_GF_1F" else None,
                     "POSITION_MM": None, "NEAR_STAIR_WINDOW": ["MAIN"],
                     "STATE": "DERIVED_FROM_PRINTED" if k == "HALF_LANDING_GF_1F" else
                     ("NOT_PRINTED" if k == "HALF_LANDING_1F_2F" else "VISUAL_RECORD"), "USE": ""})
    rows.append({"LEVEL_ID": "P16-TYPICAL-LEVELS", "SOURCE": P16, "TEXT": P16_GEOMETRY["levels"], "VALUE_M": None,
                 "POSITION_MM": None, "NEAR_STAIR_WINDOW": [], "STATE": "TYPICAL_NOT_PROJECT",
                 "USE": "never used: the typical section is N.I.S. and its levels are not this villa's"})
    for el, (a, b) in LEVEL_OF.items():
        rows.append({"LEVEL_ID": f"ELEMENT-{el}", "SOURCE": "S8.7 binding", "TEXT": f"from {a[0]} to {b[0]}",
                     "VALUE_M": None, "POSITION_MM": None, "NEAR_STAIR_WINDOW": [],
                     "STATE": f"{a[1]} / {b[1]}", "USE": f"{a[2]} | {b[2]}"})
    return rows


def _level(t):
    t = t.replace("%%p", "+").replace("%%P", "+").replace("±", "+").strip()
    try:
        return float(t)
    except ValueError:
        return None


# ------------------------------------------------------------------ geometry register
def riser_state(el, c):
    s, a, sec = c["struct"], c["arch"], c.get("section")
    vals = {v for v in (s, a, sec) if v is not None}
    if not vals:
        return None, "NOT_APPLICABLE"
    if len(vals) == 1:
        return vals.pop(), "AGREED"
    return None, "SOURCE_CONFLICT"


def geometry_rows(g, c):
    rows, data = [], {}
    for el, stair, run_, kind, sheet, floor in ELEMENTS:
        poly = g[el]
        n, nst = riser_state(el, c[el])
        (z0, s0, _), (z1, s1, _) = LEVEL_OF[el]
        flight = kind.startswith("FLIGHT") or kind == "STEP_FLIGHT"
        width = {"C-F1": None, "D-F1": 2800.0, "C-L1": 1150.0, "C-T1": None, "A2-T1": 1200.0}.get(el, 1200.0)
        width_state = {"C-F1": "DRAWN_BAND (1250 curved / 1200 straight; tread lines 1150)",
                       "D-F1": "DRAWN (tread lines 2800 on both drawings)",
                       "C-L1": "DRAWN (last straight riser 2C4 to the east edge 289)",
                       "C-F2": "DRAWN_BAND (void edge 2CF to east edge 289; tread lines 1150)",
                       "C-T1": "S1 zone outline (oblique north-east edge)"}.get(
            el, "PRINTED (P7757 '1200' / '100' / '1200' across the bay = structural wall to bay edge)")
        rise = (z1 - z0) if (z0 is not None and z1 is not None) else None
        if el in ("A1-F1", "A1-W1"):
            rise_state = "PRINTED_FOR_F1_PLUS_W1 (+1.00 -> +3.50 = 2.50 m over the straight part and the turn)"
        elif rise is not None and flight:
            rise_state = "FROM_PRINTED_LEVELS"
        elif flight or kind == "WINDER_TURN":
            rise_state = "NOT_ESTABLISHED (a level at one end is not printed)"
        else:
            rise_state = "NOT_APPLICABLE (flat)"
        riser = None
        if flight and n is not None and rise is not None and el not in ("A1-F1",):
            riser = abs(rise) * 1000.0 / n
        goings = (n - 1) if (flight and n is not None and el != "C-F1") else None
        run = goings * GOING_MM if goings is not None else None
        row = {"ELEMENT_ID": el, "STAIR_ID": stair, "STOREY_RUN": run_, "KIND": kind, "SHEET": sheet,
               "PLAN_POLYGON_BBOX_MM": [round(v, 3) for v in poly.bounds],
               "PLAN_PROJECTED_AREA_M2": _r(poly.area / 1e6),
               "PLAN_AREA_STATE": SOURCE_DERIVED_PHYSICAL if el not in ("A1-F1", "A1-F2", "A2-W1") else CONFLICT,
               "WIDTH_MM": width, "WIDTH_STATE": width_state,
               "RISERS_STRUCTURAL_PLAN": c[el]["struct"], "RISERS_ARCH_PLAN": c[el]["arch"],
               "RISERS_ARCH_OTHER_VIEW": c[el]["second"], "RISERS_REPEATED_VIEW": c[el]["repeated"],
               "RISERS_SECTION_A_A": c[el].get("section"), "RISER_COUNT": n, "RISER_COUNT_STATE": nst,
               "LEVEL_FROM_M": z0, "LEVEL_FROM_STATE": s0, "LEVEL_TO_M": z1, "LEVEL_TO_STATE": s1,
               "TOTAL_RISE_M": _r(abs(rise)) if (rise is not None and flight) else None, "RISE_STATE": rise_state,
               "RISER_HEIGHT_MM": _r(riser), "RISER_HEIGHT_STATE": (
                   "FROM_PRINTED_LEVELS_AND_AGREED_COUNT" if riser is not None and el != "D-F1" else
                   ("PROJECT_BASIS (top level binding)" if riser is not None else "NOT_ESTABLISHED")),
               "GOINGS": goings, "GOING_MM": GOING_MM if flight else None,
               "GOING_STATE": "DRAWN_PITCH (both drawings; p.16 '30' typical)" if flight else "NOT_APPLICABLE",
               "HORIZONTAL_RUN_MM": run, "RUN_STATE": ("PRINTED (P7757 1F / 2F '3300')" if el == "A2-F1" else
                                                       ("DRAWN" if run is not None else "NOT_ESTABLISHED")),
               "WAIST_THICKNESS_MM": WAIST_TAG_MM if (flight and not el.startswith(("B", "D"))) else None,
               "WAIST_STATE": ("PROJECT_BASIS (zone tag 'T' / '16'; p.16 waist 'THICK' has no value)"
                               if (flight and not el.startswith(("B", "D"))) else
                               ("NOT_IN_SOURCE (steps on grade: no section, no thickness)"
                                if el.startswith(("B", "D")) else "NOT_APPLICABLE")),
               "LANDING_THICKNESS_MM": WAIST_TAG_MM if kind in ("HALF_LANDING", "CORNER_LANDING", "TOP_ARRIVAL")
               else None}
        tread = goings * GOING_MM * width / 1e6 if (goings is not None and width) else None
        rows.append(row)
        data[el] = {"n": n, "riser": riser, "goings": goings, "run": run, "width": width, "rise": rise,
                    "tread_area": tread}
        row["FINISHING_TREAD_AREA_M2"] = _r(tread)
        row["FINISHING_RISER_AREA_M2"] = _r(n * riser * width / 1e6) if (riser is not None and width) else None
        row["HANDRAIL_PATH_LENGTH_M"] = _r(math.hypot(run, (n - 1) * riser) / 1000.0) if (
            riser is not None and run is not None) else None
        row["INCLINED_WAIST_SURFACE_AREA_M2"] = None
        row["INCLINED_STATE"] = "NOT_ESTABLISHED (see 07 sensitivity)" if flight else "NOT_APPLICABLE"
    return rows, data


# ------------------------------------------------------------------ concrete
def _flight_volume(n, riser, width, waist, bottom=None, top=None):
    f = SG.straight_flight(n, riser, GOING_MM, width, waist, bottom=bottom, top=top)
    plates = (bottom[0] * bottom[1] if bottom else 0.0) + (top[0] * top[1] if top else 0.0)
    return f, (f["profile_area"] - plates) * width / 1e9


def concrete_rows(g, geo):
    t = WAIST_TAG_MM
    rows, sens = [], {}
    L1 = 1200.0   # each half-landing is 1200 deep (P7757 1F / 2F '1200' printed; structural 19412 -> 20612)
    readings = {
        "A1-F1": [("STRUCTURAL_PLAN (12 straight + 4 winder risers in 2.50 m)", 12, 2500.0 / 16, None, None),
                  ("ARCH_PLAN (10 straight + 4 winder risers in 2.50 m)", 10, 2500.0 / 14, None, None)],
        "A1-F2": [("STRUCTURAL_PLAN_AND_SECTION (12 risers in 2.00 m)", 12, 2000.0 / 12, (L1, t), None),
                  ("ARCH_PLAN (11 risers in 2.00 m)", 11, 2000.0 / 11, (L1, t), None)],
        "A2-F1": [("UNIFORM_RISER (12 + 4 + 11 = 27 risers in 4.20 m; half-landing level not printed)", 12,
                   4200.0 / 27, None, None)],
        "A2-F2": [("UNIFORM_RISER (27 risers in 4.20 m)", 11, 4200.0 / 27, (L1, t), None)],
        "C-F2": [("UNIFORM_RISER (28 risers in 4.50 m; corner landing level not printed)", 5, 4500.0 / 28,
                  (1200.0, t), (1550.0, t))],
    }
    decide = {
        "A1-F1": (CONFLICT, "riser count and run differ between the structural plan (12 risers from 16162) and the "
                            "architectural plan (10 from 16712); waist from the zone tag only"),
        "A1-W1": (BLOCKED, "winder soffit form (flat slab under the winders or warped soffit) and the level of each "
                           "winder are not stated"),
        "A1-L1": (PROJECT_BASIS_QTO, "outline drawn on both plans (structural 2F3 / 25A / 279 and the last riser "
                                     "of A1-F2); top at +3.50 from the printed '320' on SECTION A-A; thickness 160 "
                                     "from the zone tag 'T' / '16' (580) bound to the landing plate (project basis)"),
        "A1-F2": (CONFLICT, "riser count and run differ: structural plan and SECTION A-A 12 risers / 3.30 m, "
                            "architectural plan 11 / 3.00 m"),
        "A2-F1": (BLOCKED, "the 1F -> 2F half-landing level is not printed, so the rise of the flight is unknown"),
        "A2-W1": (CONFLICT, "the structural 1F roof sheet draws no winder lines (one riser line 5E2) where the "
                            "architectural 1F plan draws four winder risers; levels not printed"),
        "A2-L1": (BLOCKED, "the 1F -> 2F half-landing level is not printed (scaled only): the volume is blocked "
                           "although it does not depend on the level"),
        "A2-F2": (BLOCKED, "half-landing level not printed; SECTION A-A draws 12 risers where both plans draw 11"),
        "B-F1": (BLOCKED, "steps on grade: no structural section, thickness or bars for them (concrete, masonry or "
                          "fill not stated)"),
        "C-F1": (BLOCKED, "the corner landing level is not printed; curved flight; beam CA (S1 BM-GF_ROOF-CA-BL015-69E, "
                          "outline 54E) crosses the straight part on the GF roof sheet at a level not stated"),
        "C-L1": (BLOCKED, "the corner landing level is not printed: the volume is blocked although it does not "
                          "depend on the level"),
        "C-F2": (BLOCKED, "the corner landing level is not printed, so the rise of the short flight is unknown"),
        "A2-T1": (PROJECT_BASIS_QTO, "arrival strip at +9.70 between the south beam face (FFRS BL009) and the last "
                                     "riser of A2-F2, inside the S1 zone SP-1F_ROOF_SLAB-01; level printed; "
                                     "thickness 160 from the zone tag 74A (project basis)"),
        "C-T1": (PROJECT_BASIS_QTO, "outline from the S1 zone SP-GF_ROOF_SLAB-28 north of the last riser line "
                                    "(S315), the void edge 2CF and the north edge 2CE; level +5.50 printed at the "
                                    "arrival (P7757 1F D16); thickness 160 from the zone tag 5B6 (project basis)"),
        "D-F1": (BLOCKED, "external steps on grade: no structural section, thickness or bars"),
    }
    for el, stair, run_, kind, sheet, floor in ELEMENTS:
        lane, why = decide[el]
        m3 = g[el].area / 1e6 * t / 1000.0 if lane in RELEASED_LANES else None
        sv = []
        for label, n, r, bot, top in readings.get(el, []):
            f, v = _flight_volume(n, r, 1200.0, t, bottom=bot, top=top)
            sv.append({"reading": label, "risers": n, "riser_mm": _r(r), "run_mm": f["run"],
                       "m3_flight_only": _r(v), "inclined_waist_length_mm": _r(f["inclined_waist_length"]),
                       "INCLINED_WAIST_SURFACE_AREA_m2": _r(f["INCLINED_WAIST_SURFACE_AREA"] / 1e6),
                       "HANDRAIL_PATH_LENGTH_m": _r(f["HANDRAIL_PATH_LENGTH"] / 1000.0)})
        if el in ("A2-L1", "C-L1"):
            sv.append({"reading": "PLATE (level-independent outline x zone tag 160)",
                       "m3_flight_only": _r(g[el].area / 1e6 * t / 1000.0)})
        sens[el] = sv
        rows.append({"ELEMENT_ID": el, "STAIR_ID": stair, "STOREY_RUN": run_, "KIND": kind,
                     "COMPONENT": {"FLIGHT": "WAIST_AND_MONOLITHIC_STEPS", "WINDER_TURN": "WINDER_TURN",
                                   "HALF_LANDING": "LANDING_PLATE", "CORNER_LANDING": "LANDING_PLATE",
                                   "TOP_ARRIVAL": "LANDING_PLATE", "STEP_FLIGHT": "STEPS_ON_GRADE"}.get(
                         kind, "WAIST_AND_MONOLITHIC_STEPS"),
                     "PLAN_AREA_M2": _r(g[el].area / 1e6), "THICKNESS_MM": t if lane in RELEASED_LANES else None,
                     "LANE": lane, "CONCRETE_M3": _r(m3), "REASON": why,
                     "FORMULA": (f"{_full(g[el].area / 1e6)} m2 x {_full(t / 1000.0)} m = {_full(m3)} m3"
                                 if m3 is not None else ""),
                     "OVERLAP_DEDUCTED": "none: the plate ends at the riser line, the beam faces and the column faces "
                                         "(S6 beams and columns keep their own concrete)" if m3 is not None else "",
                     "SENSITIVITY_ONLY": sv})
    return rows, sens


# ------------------------------------------------------------------ reinforcement
PLAN_CALLOUTS = [  # sheet, text handle, bar-line handles, bar direction, element(s) the bar lines cross
    ("GFRS", "490", ("44F", "450"), "N-S", ("A1-F1", "A1-W1")),
    ("GFRS", "491", ("44A", "44E"), "N-S", ("A1-F2", "A1-L1")),
    ("GFRS", "48F", ("451", "452"), "E-W", ("A1-W1", "A1-L1")),
    ("FFRS", "748", ("743", "744"), "N-S", ("A2-F1", "A2-W1")),
    ("FFRS", "749", ("741", "742"), "N-S", ("A2-F2", "A2-L1")),
    ("FFRS", "747", ("745", "746"), "E-W", ("A2-W1", "A2-L1")),
    ("GFRS", "5BC", ("2DB", "2DC"), "ALONG_CURVE", ("C-F1",)),
    ("GFRS", "537", ("535", "536"), "E-W", ("C-F1", "C-L1")),
    ("GFRS", "53D", ("2CC", "2CD"), "N-S", ("C-L1", "C-F2", "C-T1")),
]
TAGS = [("GFRS", "580", ("A1",)), ("FFRS", "74A", ("A2",)), ("GFRS", "5B6", ("C",))]


def rebar_binding(E, by):
    rows = []
    texts = {(sh, e["handle"].split(":")[0]): e for sh in E for e in E[sh] if e["type"] in ("TEXT", "MTEXT")}
    for k, (txt, where, role, layer) in enumerate(P16_CALLOUTS, 1):
        plan = "8Ø16/m on every flight and landing strip of ST-A and ST-C (plan callouts)" if txt == "8Ø16/m" else ""
        rows.append({"BINDING_ID": f"P16-{k:02d}", "SOURCE": P16, "HANDLE": "", "TEXT": txt, "POSITION_MM": None,
                     "BAR_LINES": [], "WHERE_DRAWN": where, "PHYSICAL_BAR_ROLE": role, "LAYER_OR_SHAPE": layer,
                     "BOUND_TO": plan or "no plan callout, no note and no reference on any plan binds it to a "
                                        "project stair",
                     "APPLICABILITY": "PLAN_CALLOUT_CONFIRMS_DIAMETER_AND_RATE" if plan else "TYPICAL_ONLY",
                     "STATE": "ROLE_READ (diameter and rate from the plan; role from p.16)" if plan else
                     "BLOCKED_UNQUANTIFIED (typical detail only: no generic bar is made)"})
    for sh, h, bl, direction, els in PLAN_CALLOUTS:
        t = texts[(sh, h)]
        lines = [by[(sh, x)] for x in bl]
        check(all(x["layer"] in ("ST", "5") for x in lines), f"{sh} {h}: bar lines on the bar layers")
        rows.append({"BINDING_ID": f"{sh}-{h}", "SOURCE": f"ST7757 {sh} plan", "HANDLE": h, "TEXT": t["text"],
                     "POSITION_MM": [round(v, 3) for v in t["p"][:2]], "BAR_LINES": list(bl),
                     "WHERE_DRAWN": f"bar line pair {'/'.join(bl)} ({direction})", "PHYSICAL_BAR_ROLE":
                     "MAIN_BOTTOM along the flight (p.16), continuing as the landing bottom bar"
                     if direction in ("N-S", "ALONG_CURVE") and not h in ("48F", "747") else
                     ("LANDING_BOTTOM_TRANSVERSE across the north strip" if h in ("48F", "747") else
                      "MAIN_BOTTOM along the straight flight, continuing across the corner landing"),
                     "LAYER_OR_SHAPE": "bottom (unqualified plan callout; p.16 draws 8Ø16/m at the soffit)",
                     "BOUND_TO": list(els), "APPLICABILITY": "PLAN_CALLOUT", "STATE": "BOUND"})
    for sh, h, st in TAGS:
        t = [e for (s_, hh), e in texts.items() if s_ == sh and hh == h]
        rows.append({"BINDING_ID": f"{sh}-{h}-TAG", "SOURCE": f"ST7757 {sh} plan", "HANDLE": h,
                     "TEXT": " / ".join(sorted(x["text"] for x in t)), "POSITION_MM": [round(v, 3) for v in t[0]["p"][:2]],
                     "BAR_LINES": [], "WHERE_DRAWN": "thickness tag inside the stair zone at a flight / landing "
                                                     "junction", "PHYSICAL_BAR_ROLE": "NOT_A_BAR (thickness 16 cm)",
                     "LAYER_OR_SHAPE": "", "BOUND_TO": list(st), "APPLICABILITY": "ZONE_THICKNESS",
                     "STATE": "landing plates: project basis; waist: project basis (sensitivity only)"})
    return rows


def _rate_len(rate, area_m2):
    """equivalent length (m) of an n/m rate spread over a plate: rate x area (unrounded; AD2-D02 rate density)."""
    return rate * area_m2


def rebar_rows(g, conc):
    rows = []
    lane = {r["ELEMENT_ID"]: r["LANE"] for r in conc}
    um16 = kg_per_m(16)

    def add(el, src, role, d, rate, scope, length_basis, eq, state, why, owner="S8.7", formula=""):
        rows.append({"STAIR_ID": el.split("-")[0].replace("A1", "ST-A").replace("A2", "ST-A").replace(
                         "B", "ST-B").replace("C", "ST-C").replace("D", "ST-D"),
                     "FLIGHT_OR_LANDING_ID": el, "SOURCE_HANDLE": src, "PHYSICAL_BAR_ROLE": role, "BAR_DIAMETER_MM": d,
                     "SPACING_OR_COUNT": rate, "DISTRIBUTION_SCOPE": scope, "SUPPORTED_LENGTH": length_basis,
                     "OWNER": owner, "QUANTITY_STATE": state,
                     "EQUIVALENT_LENGTH_M": _r(eq), "KG": _r(eq * kg_per_m(d)) if (eq is not None and d) else None,
                     "REASON": why, "FORMULA": formula})

    for el, src, scope in (("A1-L1", "GFRS 491 (44A/44E) N-S", "landing plate 1.20 x 1.20 m"),
                           ("A1-L1", "GFRS 48F (451/452) E-W", "landing plate 1.20 x 1.20 m"),
                           ("A2-T1", "FFRS 749 (741/742) N-S", "arrival strip 1.20 x 0.10 m"),
                           ("C-T1", "GFRS 53D (2CC/2CD) N-S", "top arrival plate (S1 zone north of S315)")):
        a = g[el].area / 1e6
        eq = _rate_len(8.0, a)
        rel = lane[el] in RELEASED_LANES
        add(el, src, "LANDING_BOTTOM_LONGITUDINAL" if "N-S" in src else "LANDING_BOTTOM_TRANSVERSE", 16, "8/m",
            scope, "plate face to face (riser line, beam / column / void faces); anchorage separate",
            eq if rel else None, PROJECT_BASIS_QTO if rel else BLOCKED,
            "plan callout and bar lines cross the released plate; rate density over the plate (S7 AD2-D02 "
            "reading); layer bottom (unqualified callout; p.16)" if rel else "plate blocked",
            formula=f"8 /m x {_full(a)} m2 = {_full(eq)} m; x 16^2/162 = {_full(um16)} kg/m -> "
                    f"{_full(eq * um16)} kg" if rel else "")
    for el in ("A1-L1", "A2-T1", "C-T1"):
        if el != "A1-L1":
            add(el, "-", "LANDING_BOTTOM_TRANSVERSE", None, "", "plate", "", None, "NOT_IN_SOURCE",
                "no callout or bar line crosses this plate in the other direction")
        add(el, "p.16 6Ø12/m", "LANDING_TOP", 12, "6/m", "landing", "", None, BLOCKED,
            "typical detail only: no plan callout, note or reference")
        add(el, "p.16 6Ø14/m", "TOP_JUNCTION_BENT", 14, "6/m", "landing / flight junction", "", None, BLOCKED,
            "typical detail only: no plan callout, note or reference")
        add(el, "-", "ANCHORAGE_AND_CONTINUATION", 16, "", "bar ends at the beam / column / flight",
            "", None, BLOCKED, "anchorage into the supports and continuation into the flight are not stated "
                               "(no length is made from generic practice)")
    for el in ("A2-L1", "C-L1"):
        a = g[el].area / 1e6
        dirs = 2
        add(el, "FFRS 749 + 747" if el == "A2-L1" else "GFRS 537 + 53D", "LANDING_BOTTOM (two directions)", 16,
            "8/m", "landing plate", "plate face to face", None, BLOCKED,
            f"level not printed (landing blocked); sensitivity {_full(dirs * _rate_len(8.0, a) * um16)} kg "
            f"(rate density, both directions)")
    for el in ("A1-F1", "A1-F2", "A2-F1", "A2-F2", "C-F1", "C-F2"):
        add(el, {"A1-F1": "GFRS 490", "A1-F2": "GFRS 491", "A2-F1": "FFRS 748", "A2-F2": "FFRS 749",
                 "C-F1": "GFRS 5BC + 537", "C-F2": "GFRS 53D"}[el], "MAIN_BOTTOM", 16, "8/m",
            "flight width", "inclined waist (not established)", None, CONFLICT if lane[el] == CONFLICT else BLOCKED,
            "the flight geometry is " + ("in conflict" if lane[el] == CONFLICT else "blocked") + " (07)")
        for role, d, rate in (("DISTRIBUTION_TRANSVERSE", 12, "1 / 0.20 m"), ("STEP_BAR", 8, "1 / 0.15 m"),
                              ("NOSING_CORNER_BAR", 12, "1 per step"), ("TOP_JUNCTION_BENT", 14, "6/m")):
            add(el, f"p.16 {'Ø12/20cm' if role.startswith('DIS') else 'Ø8/15' if role == 'STEP_BAR' else '1Ø12' if role.startswith('NOS') else '6Ø14/m'}",
                role, d, rate, "flight", "", None, BLOCKED, "typical detail only: no plan callout, note or reference")
    for el in ("A1-F1", "C-F1"):
        add(el, "p.16 6Ø16/m", "STARTER_FROM_GROUND_BEAM", 16, "6/m", "first flight", "", None, BLOCKED,
            "typical detail only; no ground beam is drawn at the foot of the flight")
    for el in ("A1-W1", "A2-W1"):
        add(el, "GFRS 490 / 48F" if el == "A1-W1" else "FFRS 748 / 747", "WINDER_TURN_BARS", 16, "8/m",
            "winder quadrant", "", None, BLOCKED, "winder soffit form not stated")
    for el in ("B-F1", "D-F1"):
        add(el, "-", "NONE_SHOWN", None, "", "", "", None, "NOT_IN_SOURCE", "no reinforcement drawn or noted")
    return rows


# ------------------------------------------------------------------ structure around the stairs
def beam_bands(sheets=("GFRS", "FFRS", "GBP")):
    import alsenan_structural_s1 as S1
    from shapely.geometry import Polygon
    src = S1.Source()
    out = {}
    for sh in sheets:
        segs, _, _ = S1.beam_linework(src, sh)
        for ln in S1.beam_lines(S1.straight_bands(segs)):
            d, n = tuple(float(v) for v in ln["dir"]), tuple(float(v) for v in ln["normal"])
            o, w, t0, t1 = float(ln["offset"]), float(ln["width_mm"]), float(ln["t0"]), float(ln["t1"])
            pts = [(d[0] * t + n[0] * (o + s * w / 2), d[1] * t + n[1] * (o + s * w / 2))
                   for t, s in ((t0, -1), (t1, -1), (t1, 1), (t0, 1))]
            out[(sh, ln["line_id"])] = Polygon(pts)
    return out


OVERLAP_TOL_M2 = 1e-4     # 100 mm2: drawing round-off between the bands (x.9) and the outlines (x.904)


def supports_of(g, bands, sheet_of):
    out = {}
    for el, poly in g.items():
        sh = sheet_of[el]
        near = []
        for (s, lid), b in bands.items():
            if s != sh:
                continue
            gap = poly.distance(b)
            ov = poly.intersection(b).area / 1e6
            if gap < 1.0:
                near.append({"beam_line": lid, "overlap_m2": _r(ov, 6) if ov > OVERLAP_TOL_M2 else 0.0,
                             "touch": True})
        out[el] = sorted(near, key=lambda x: x["beam_line"])
    return out


# ------------------------------------------------------------------ S7 stair-adjacent top steel
ZONE_TO_STAIR = {"SP-GF_ROOF_SLAB-03": "ST-A (A1 GF->1F)", "SP-1F_ROOF_SLAB-01": "ST-A (A2 1F->2F)",
                 "SP-GF_ROOF_SLAB-21": "ST-C (light-well void + curved flight)",
                 "SP-GF_ROOF_SLAB-28": "ST-C (straight end, corner landing, short flight, top arrival)"}


def s7_recompute():
    items = {r["S7_ITEM_ID"]: r for r in _rows(READ["S7_ITEMS"])}
    runs = _rows(READ["S7_RUNS"])
    aud = [a for a in _rows(READ["S7A_AUDIT"]) if "STAIR" in a["UNRESOLVED_REASON"]]
    ends = {(a["STRIP_ID"], a["END"]): a for a in aud}
    per = defaultdict(list)
    for r in runs:
        if r["BAR_ROLE"] == "TOP_OVER_SUPPORT_EXTENSION":
            k = (r["STRIP_ID"], "END" if r["END_USED"] == "END" else "START")
            if k in ends:
                per[k].append(r)
    rows = []
    for k in sorted(ends):
        a, rr = ends[k], per[k]
        m = re.search(r"into (SP-[A-Z0-9_]+-\d+)", rr[0]["SUPPORT_RELATION"]) if rr else None
        into = m.group(1) if m else ""
        dia = sorted({items[x["S7_ITEM_ID"]]["DIAMETER_MM"] for x in rr})
        kg = math.fsum(float(x["KG"]) for x in rr)
        rows.append({"STRIP_ID": k[0], "END": k[1], "FLOOR": a["FLOOR"], "S7_PANEL": a["PANEL"],
                     "SUPPORT_ID": a["SUPPORT_ID"], "SUPPORT_KIND": a["SUPPORT_KIND"],
                     "STAIR_ZONE_BEYOND": a["BEYOND_PANEL"], "STAIR_ELEMENT": ZONE_TO_STAIR[a["BEYOND_PANEL"]],
                     "S7A_REASON": a["UNRESOLVED_REASON"], "S7_BAR_RUN_ROWS": [x["BAR_RUN_ROW_ID"] for x in rr],
                     "S7_ITEMS": sorted({x["S7_ITEM_ID"] for x in rr}), "DIAMETER_MM": dia,
                     "EXTENSION_LENGTH_MM": sorted({x["EXTENSION_LENGTH_MM"] for x in rr}),
                     "EXTENSION_INTO_PANEL": into, "KG_FROM_BAR_RUNS": _r(kg),
                     "KG_S7A_AUDIT": _r(float(a["S7_TOP_EXTENSION_KG_AT_END"])),
                     "OWNER": "S7 (released, frozen)",
                     "S8_7_TOP_STEEL_AT_THIS_SUPPORT": 0.0,
                     "STATE": "OWNED_ONCE_BY_S7" if (into == a["PANEL"] and into not in ZONE_TO_STAIR) else "CHECK"})
    return rows


# ------------------------------------------------------------------ ground-level regions
def _family(cls):
    if cls in ("GF_FLOOR_+1.00", "LOBBY_FLOOR_+0.30"):
        return "ground-slab family (not stair; S8.1 / S8.1A keep it excluded; no thickness or mesh is printed)"
    if cls == "CENTRAL_WALL_FOOTPRINT":
        return "wall family (not quantified by any stage)"
    if cls == "SOURCE_CONFLICT_A1-F1_START":
        return "S8.7 stair (ST-A) or ground-slab family: source conflict"
    return "S8.7 stair (" + ("ST-B" if cls == "B-F1" else "ST-A, measured on GFRS") + ")"


def ground_rows(g, zones):
    from shapely.geometry import Polygon
    rg02 = next(r for r in _rows(READ["S81A_REGION"]) if r["PART_ID"] == "S8.1A-RG-02")
    RG = Polygon(json.loads(rg02["POLYGON_MM"]))
    check(abs(float(rg02["AREA_M2"]) - 11.52) < 1e-9 and abs(RG.area / 1e6 - 11.52) < 1e-6, "S8.1A-RG-02 is 11.52 m2")
    ys, yf1, ya, yb0, yb1, yn = Y_GBP_S, 16161.856, 16711.856, 18511.856, 19411.856, Y_GBP_N
    yw1 = 19461.856
    parts = [
        ("RG02-P01", (X_GBP_W, ys, X_BAY_E, yf1), "GF_FLOOR_+1.00", "ground-slab family (south strip at +1.00)"),
        ("RG02-P02", (X_GBP_W, yf1, X_WALL_W, ya), "SOURCE_CONFLICT_A1-F1_START",
         "structural GFRS: the first two risers of A1-F1; architectural GF: +1.00 floor"),
        ("RG02-P03", (X_GBP_W, ya, X_WALL_W, yw1), "UNDER_A1-F1",
         "ground under the lower flight (GBP draws its first 7 risers: repeated view of A1-F1)"),
        ("RG02-P04", (X_GBP_W, yw1, X_WALL_W, yn), "LOBBY_FLOOR_+0.30", "ground-slab family (+0.30 lobby under the turn)"),
        ("RG02-P05", (X_WALL_W, yf1, X_WALL_E, ya), "GF_FLOOR_+1.00", "ground-slab family (south of the central wall)"),
        ("RG02-P06", (X_WALL_W, ya, X_WALL_E, yw1), "CENTRAL_WALL_FOOTPRINT",
         "the 100 mm wall between the flights (GBP 143 / 1C3 / 144): wall family, not stair, not slab"),
        ("RG02-P07", (X_WALL_W, yw1, X_WALL_E, yn), "LOBBY_FLOOR_+0.30", "ground-slab family"),
        ("RG02-P08", (X_WALL_E, yf1, X_BAY_E, yb0), "GF_FLOOR_+1.00",
         "ground-slab family (corridor at +1.00 under A1-F2 leading to the lobby steps)"),
        ("RG02-P09", (X_WALL_E, yb0, X_BAY_E, yb1), "B-F1", "the lobby steps ST-B (+1.00 -> +0.30): stair family"),
        ("RG02-P10", (X_WALL_E, yb1, X_BAY_E, yn), "LOBBY_FLOOR_+0.30", "ground-slab family (+0.30 lobby under A1-L1)"),
    ]
    rows, tot = [], 0.0
    s81 = [r for r in _rows(READ["S81_POP"]) if r["POLYGON_MM"] and r["ROW_KIND"] == "FACE"]
    for pid, b, cls, note in parts:
        P = _rect(*b).intersection(RG)
        tot += P.area
        ov = sum(Polygon(json.loads(r["POLYGON_MM"])).intersection(P).area for r in s81) / 1e6
        rows.append({"REGION": "S8.1A-RG-02 (GBP, 11.52 m2)", "PART_ID": pid, "BBOX_MM": [round(v, 3) for v in b],
                     "AREA_M2": _r(P.area / 1e6), "CLASS": cls, "NOTE": note,
                     "S8_7_ELEMENT": {"B-F1": "B-F1", "UNDER_A1-F1": "A1-F1 (repeated view)",
                                      "SOURCE_CONFLICT_A1-F1_START": "A1-F1 (conflict)"}.get(cls, ""),
                     "OVERLAP_WITH_S8_1_FACES_M2": _r(ov), "OWNER_FAMILY": _family(cls),
                     "QUANTIFIED_IN_ANY_STAGE": False})
    check(abs(tot / 1e6 - 11.52) < 1e-6, f"RG-02 partition closes ({tot / 1e6})")
    G12 = zones["SP-GBP-12"]
    s81_12 = next(r for r in _rows(READ["S81_POP"]) if r["ROW_ID"] == "SP-GBP-12")
    check(abs(float(s81_12["AREA_M2_EXACT"]) - 8.37232788) < 1e-9, "S8.1 SP-GBP-12 is 8.37232788 m2")
    G12 = Polygon(json.loads(s81_12["POLYGON_MM"]))
    fl = g["C-F1"].intersection(G12)
    rows.append({"REGION": "SP-GBP-12 (GBP, S8.1 excluded 8.37232788 m2)", "PART_ID": "GBP12-P01",
                 "BBOX_MM": [round(v, 3) for v in fl.bounds], "AREA_M2": _r(fl.area / 1e6),
                 "CLASS": "UNDER_C-F1", "NOTE": "footprint of the light-well flight (GBP draws its first 9 risers and "
                                                "the curtail arcs: repeated view of C-F1, same coordinates as GFRS)",
                 "S8_7_ELEMENT": "C-F1 (repeated view)",
                 "OVERLAP_WITH_S8_1_FACES_M2": _r(sum(Polygon(json.loads(r["POLYGON_MM"])).intersection(fl).area
                                                  for r in s81) / 1e6),
                 "OWNER_FAMILY": "S8.7 stair (ST-C, measured on GFRS)", "QUANTIFIED_IN_ANY_STAGE": False})
    rest = G12.difference(g["C-F1"])
    rows.append({"REGION": "SP-GBP-12 (GBP, S8.1 excluded 8.37232788 m2)", "PART_ID": "GBP12-P02",
                 "BBOX_MM": [round(v, 3) for v in rest.bounds], "AREA_M2": _r(rest.area / 1e6),
                 "CLASS": "GF_FLOOR_+1.00", "NOTE": "hall floor under the light well (ground-slab family)",
                 "S8_7_ELEMENT": "", "OVERLAP_WITH_S8_1_FACES_M2": _r(sum(
                     Polygon(json.loads(r["POLYGON_MM"])).intersection(rest).area for r in s81) / 1e6),
                 "OWNER_FAMILY": _family("GF_FLOOR_+1.00"), "QUANTIFIED_IN_ANY_STAGE": False})
    check(abs((fl.area + rest.area) / 1e6 - 8.37232788) < 1e-6, "SP-GBP-12 partition closes")
    return rows, RG, G12


# ------------------------------------------------------------------ registers
def census_rows(geo, conc, c, g):
    lane = {r["ELEMENT_ID"]: r["LANE"] for r in conc}
    rows = []
    for sid, st in STAIRS.items():
        els = [e for e in ELEMENTS if e[1] == sid]
        rows.append({"ELEMENT_ID": sid, "ROW_KIND": st["kind"], "PARENT": "", "STAIR_ID": sid, "NAME": st["name"],
                     "FLOORS": st["floors"], "S1_PRE_S8_ZONES": st["zones"],
                     "IN_S1_PRE_S8": {"ST-A": "YES (2 of the 5 zones: one per storey run)",
                                      "ST-B": "NO (inside the S8.1A recovered bay RG-02; not a PRE-S8 stair)",
                                      "ST-C": "YES (3 of the 5 zones: GF-21, GF-28 and the repeated GBP-12)",
                                      "ST-D": "NO (omitted: inside SP-GBP-01 outside the building)"}[sid],
                     "ELEMENTS": [e[0] for e in els], "STATE": "PHYSICAL_STAIR_ELEMENT"})
    runs_ = defaultdict(list)
    for e in ELEMENTS:
        runs_[(e[1], e[2])].append(e[0])
    for (sid, rn), els in sorted(runs_.items()):
        if sid == "ST-A":
            rows.append({"ELEMENT_ID": rn.split()[0], "ROW_KIND": "STOREY_RUN", "PARENT": sid, "STAIR_ID": sid,
                         "NAME": rn, "FLOORS": rn.split(" ", 1)[1], "S1_PRE_S8_ZONES":
                         ["SP-GF_ROOF_SLAB-03"] if rn.startswith("A1") else ["SP-1F_ROOF_SLAB-01"],
                         "IN_S1_PRE_S8": "YES", "ELEMENTS": els, "STATE": "STOREY_RUN"})
    for el, stair, rn, kind, sheet, floor in ELEMENTS:
        rows.append({"ELEMENT_ID": el, "ROW_KIND": kind, "PARENT": rn.split()[0] if stair == "ST-A" else stair,
                     "STAIR_ID": stair, "NAME": rn, "FLOORS": rn.split(" ", 1)[1], "S1_PRE_S8_ZONES": [],
                     "IN_S1_PRE_S8": "", "ELEMENTS": [], "STATE": f"{lane[el]} (plan {_full(g[el].area / 1e6)} m2 "
                                                                  f"on {sheet})"})
    return rows


def tread_rows(runs):
    rows = []
    for k, r in enumerate(runs, 1):
        el, role = r["assigned"]
        rows.append({"RUN_ID": f"TR-{k:03d}", "SOURCE": r["source"], "VIEW": r["view"], "WINDOW": r["window"],
                     "LAYER": r["layer"], "LINETYPE": "HIDDEN" if r["hidden"] else "CONTINUOUS",
                     "KIND": "RADIAL" if r.get("radial") else "PARALLEL", "LINES": r["count"],
                     "ANGLE_DEG": r["angle"], "LINE_LENGTH_MM": _r(r["length"], 3) if r["length"] else None,
                     "PITCHES_MM": [round(v, 1) for v in r["pitches"]],
                     "OFFSETS_MM": [round(abs(v), 3) for v in r["offsets"]],
                     "ALONG_MM": [round(v, 3) for v in r["along"]] if r["along"] else None,
                     "HANDLES": r["ids"], "EXCLUDED_HANDLES": r.get("excluded_ids", []),
                     "ASSIGNED_ELEMENT": el, "VIEW_ROLE": role})
    return rows


def opening_map():
    m = {"SO-GFRS-03": ("ST-A A1", "the stair opening of the GF roof slab over the GF -> 1F run"),
         "SO-FFRS-01": ("ST-A A2", "the stair opening of the 1F roof slab over the 1F -> 2F run"),
         "SO-GFRS-21": ("ST-C + LIGHT_WELL_VOID", "the light well open to below and the curved flight band"),
         "SO-GFRS-28": ("ST-C", "straight end, corner landing, short flight and top arrival"),
         "SO-GBP-12": ("ST-C (repeated view) + GF hall floor", "ground view of the light-well flight start"),
         "SO-GFRS-13": ("NOT_STAIR (lift shaft void)", "beside the main stair bay, x 19788 - 21588"),
         "SO-FFRS-06": ("NOT_STAIR (lift shaft void)", "same shaft one storey up"),
         "SO-GFRS-09": ("NOT_STAIR (void at x 31209 - 32908)", "no tread drawn in or near it")}
    rows = []
    for r in _rows(READ["S86_CENSUS"]):
        if r["OPENING_ID"].startswith("SO-"):
            a, why = m[r["OPENING_ID"]]
            rows.append((r["OPENING_ID"], r["TYPE_BASIS"], a, why))
    check(len(rows) == 8, "the eight S8.6 slab openings")
    return rows


def crosswalk_rows(g, zones, sheet_of, band, G12, RG):
    rows = []
    for z, sh in (("SP-GF_ROOF_SLAB-03", "GFRS"), ("SP-1F_ROOF_SLAB-01", "FFRS"), ("SP-GF_ROOF_SLAB-21", "GFRS"),
                  ("SP-GF_ROOF_SLAB-28", "GFRS")):
        Z = zones[z]
        hit = {el: g[el].intersection(Z).area / 1e6 for el in g if sheet_of[el] == sh and g[el].intersection(Z).area > 1.0}
        void = Z.difference(_union([g[e] for e in hit])).area / 1e6
        for el, a in sorted(hit.items()):
            rows.append({"SOURCE_RECORD": z, "SOURCE": "S1 SLAB_PANEL_REGISTER / PRE-S8 STAIR_AND_LANDING face",
                         "S1_AREA_M2": _r(Z.area / 1e6), "ELEMENT": el, "RELATION": "PART_OF_ZONE",
                         "AREA_M2": _r(a), "NOTE": ""})
        if void > 1e-6:
            rows.append({"SOURCE_RECORD": z, "SOURCE": "S1 SLAB_PANEL_REGISTER", "S1_AREA_M2": _r(Z.area / 1e6),
                         "ELEMENT": "LIGHT_WELL_VOID" if z.endswith("-21") else "RESIDUAL",
                         "RELATION": "VOID_OPEN_TO_BELOW" if z.endswith("-21") else "RESIDUAL",
                         "AREA_M2": _r(void), "NOTE": "X lines 2D1 / 2D2 / 54B / 54C and 'VOID' (2D3): no slab, no "
                                                      "stair; nothing is measured" if z.endswith("-21") else ""})
    rows.append({"SOURCE_RECORD": "SP-GBP-12", "SOURCE": "S1 / S8.1 (excluded 8.37232788 m2)",
                 "S1_AREA_M2": _r(G12.area / 1e6), "ELEMENT": "C-F1", "RELATION": "REPEATED_VIEW (ground plan of the "
                 "same flight: 9 of its 12 radial risers at identical coordinates)",
                 "AREA_M2": _r(G12.intersection(g["C-F1"]).area / 1e6), "NOTE": "remainder is GF hall floor (04)"})
    rows.append({"SOURCE_RECORD": "S8.1A-RG-02", "SOURCE": "S8.1A recovered stair bay (11.52 m2)",
                 "S1_AREA_M2": _r(RG.area / 1e6), "ELEMENT": "B-F1 + A1-F1 (repeated view) + floors",
                 "RELATION": "GROUND_VIEW_OF_THE_MAIN_STAIR_BAY", "AREA_M2": _r(RG.area / 1e6),
                 "NOTE": "not a second staircase: partition in 04"})
    rows.append({"SOURCE_RECORD": "SP-GBP-01", "SOURCE": "S1 / S8.1 (outside the building, excluded)",
                 "S1_AREA_M2": None, "ELEMENT": "D-F1", "RELATION": "CONTAINS (omitted stair)",
                 "AREA_M2": _r(g["D-F1"].intersection(zones["SP-GBP-01"]).area / 1e6),
                 "NOTE": "S1 counted 9 tread lines in SP-GBP-01 without a stair record"})
    for oid, basis, a, why in opening_map():
        rows.append({"SOURCE_RECORD": oid, "SOURCE": "S8.6 slab-opening census", "S1_AREA_M2": None,
                     "ELEMENT": a, "RELATION": "OPENING", "AREA_M2": None, "NOTE": f"{basis}; {why}"})
    for occ in ("BM-GF_ROOF-B3-BL033-6B7", "BM-1F_ROOF-B3-BL023-6B9", "CBO-GFRS-CB3-BL022", "BM-GF_ROOF-CA-BL015-69E"):
        rows.append({"SOURCE_RECORD": occ, "SOURCE": "S6 occurrence ('With Stair' tag)" if "CA" not in occ else
                     "S6 occurrence (beam CA)", "S1_AREA_M2": None,
                     "ELEMENT": {"BM-GF_ROOF-B3-BL033-6B7": "A1-L1 / A1-W1 north support",
                                 "BM-1F_ROOF-B3-BL023-6B9": "A2-L1 / A2-W1 north support",
                                 "CBO-GFRS-CB3-BL022": "C-F1 / C-L1 south support (span 24308 - 27658)",
                                 "BM-GF_ROOF-CA-BL015-69E": "crosses C-F1 (plan overlap 0.345 m2; level not stated)"}[occ],
                     "RELATION": "SUPPORT (S6 owns; not re-added)", "AREA_M2": None, "NOTE": ""})
    for z in STAIRS["ST-A"]["zones"] + STAIRS["ST-C"]["zones"] + ["SP-GBP-12"]:
        rows.append({"SOURCE_RECORD": f"SPC-STAIR-{z}", "SOURCE": "S1 SPECIAL_STRUCTURAL_OCCURRENCE / PRE-S8 ELEMENT",
                     "S1_AREA_M2": None, "ELEMENT": "ST-A" if z in STAIRS["ST-A"]["zones"] else "ST-C",
                     "RELATION": "ONE OF " + ("2" if z in STAIRS["ST-A"]["zones"] else "3") + " RECORDS OF ONE STAIR",
                     "AREA_M2": None, "NOTE": "five PRE-S8 stair zones = two staircases"})
    return rows


def _union(polys):
    from shapely.ops import unary_union
    return unary_union(polys)


QUESTIONS = {
    "Q-ST-01": "Main stair GF -> 1F: the structural GF roof plan draws 12 + 12 risers (first riser at y 16162 / "
               "16112), the architectural GF plan 10 + 11 (from 16712 / 16412). SECTION A-A draws 12 in the upper "
               "flight. Which riser count and which start line govern?",
    "Q-ST-02": "State the waist thickness of the flights (p.16 'THICK' has no value). Is the zone tag 'T' / '16' "
               "the waist, the landing, or both?",
    "Q-ST-03": "State the 1F -> 2F half-landing level (SECTION A-A draws it about 2.00 m below +9.70, unprinted) "
               "and the light-well corner landing level.",
    "Q-ST-04": "The structural 1F roof sheet draws no winder lines in the 1F -> 2F turn (only 5E2) while the "
               "architectural 1F plan draws four winder risers: confirm the turn.",
    "Q-ST-05": "SECTION A-A draws 12 risers in the 1F -> 2F upper flight where both plans draw 11.",
    "Q-ST-06": "Winder turns: is the soffit under the winders a flat slab at the landing level or warped?",
    "Q-ST-07": "Lobby steps (+1.00 -> +0.30) and entrance steps (+0.15 -> +1.00): concrete on grade, masonry or fill? "
               "No section, thickness or bar is drawn.",
    "Q-ST-08": "Which p.16 bars apply to these stairs (6Ø14/m, 6Ø12/m, Ø12/20cm, Ø8/15, 1Ø12, 6Ø16/m)? Only 8Ø16/m "
               "is called out on the plans.",
    "Q-ST-09": "'B3 (With Stair)' beams (GFRS 6B6, FFRS 6B8; CB3 middle span on GFRS, PEC-13): are they the "
               "half-landing / corner-landing beams at the landing level (SECTION A-A draws a downstand there)? "
               "S6 owns them and keeps them blocked.",
    "Q-ST-10": "Beam CA (S1 BM-GF_ROOF-CA-BL015-69E, outline 54E, 300 wide) crosses the light-well straight "
               "flight on the GF roof sheet: does it support the flight, or is it a roof beam over it (about 1.3 m "
               "headroom there)?",
    "Q-ST-11": "The single diagonals SW of the GF stair start (2F1D / 2F1E) and across the 2F NE landing quadrant "
               "(2F1F / 2F20; FFRS 648) carry no stated meaning.",
    "Q-ST-12": "Entrance steps: is the top of the steps the +1.00 porch (nearest printed mark 1C0)?",
}


def blocked_rows(conc, reb, c):
    rows = []
    for r in conc:
        if r["LANE"] not in RELEASED_LANES:
            rows.append({"ITEM": f"{r['ELEMENT_ID']} concrete", "STATE": r["LANE"], "REASON": r["REASON"],
                         "SENSITIVITY_ONLY": r["SENSITIVITY_ONLY"], "QUESTION": _q(r["ELEMENT_ID"])})
    for r in reb:
        if r["QUANTITY_STATE"] not in RELEASED_LANES:
            rows.append({"ITEM": f"{r['FLIGHT_OR_LANDING_ID']} {r['PHYSICAL_BAR_ROLE']} ({r['SOURCE_HANDLE']})",
                         "STATE": r["QUANTITY_STATE"], "REASON": r["REASON"], "SENSITIVITY_ONLY": None,
                         "QUESTION": "Q-ST-08" if "typical" in r["REASON"] else _q(r["FLIGHT_OR_LANDING_ID"])})
    for k, v in sorted(QUESTIONS.items()):
        rows.append({"ITEM": k, "STATE": "QUESTION_FOR_THE_ENGINEER", "REASON": v, "SENSITIVITY_ONLY": None,
                     "QUESTION": k})
    return rows


def _q(el):
    return {"A1-F1": "Q-ST-01", "A1-F2": "Q-ST-01", "A1-W1": "Q-ST-06", "A2-F1": "Q-ST-03", "A2-F2": "Q-ST-05",
            "A2-W1": "Q-ST-04", "A2-L1": "Q-ST-03", "B-F1": "Q-ST-07", "C-F1": "Q-ST-03", "C-L1": "Q-ST-03",
            "C-F2": "Q-ST-03", "D-F1": "Q-ST-07"}.get(el, "")


def pre_s8_rows(pre_census, pre_ex, ready):
    rows = []
    conds = [
        ("waist thickness", "PARTIAL", "zone tags 'T' / '16' (580, 74A, 5B6) are the only thicknesses; p.16 waist "
         "'THICK' has no value. Bound to the landing plates and the top arrival (project basis); the waist reading "
         "160 enters sensitivity only", "A1-L1, C-T1 released; flights not"),
        ("riser height", "PARTIAL", "printed levels with an agreed riser count give the lobby steps 175 mm (4 risers "
         "in 0.70 m) and the entrance steps 170 mm (project basis top level); the GF -> 1F flights conflict "
         "(Q-ST-01); the 1F -> 2F and light-well flights lack an intermediate level (Q-ST-03)", "no flight released"),
        ("landing levels per flight", "PARTIAL", "GF -> 1F half-landing +3.50 from SECTION A-A ('320' from the "
         "printed +0.30); light-well top arrival +5.50 printed; 1F -> 2F half-landing and light-well corner landing "
         "not printed", "A1-L1 and C-T1 levels resolved"),
        ("bar lengths per flight; which p.16 bar is which", "PARTIAL", "every p.16 callout is read and given its "
         "role (08); the plans call out 8Ø16/m only, on every flight and landing strip, with bar lines; lengths per "
         "flight wait for the flight geometry", "landing plates measured by rate density (project basis)"),
        ("open-to-below evidence and slab / special-structure evidence in the same geometry", "RESOLVED",
         "SP-GF_ROOF_SLAB-21 = light-well void (X lines + 'VOID') + the curved flight band; 5BC sits on the flight "
         "with curved bar lines 2DB / 2DC, not over the void", "C-01 / PRE-S7.1 C-01 answered"),
        ("special-structure evidence: goes to the special-structures round", "RESOLVED",
         "this round: every stair zone is mapped to a physical element (03)", ""),
        ("thickness / mesh not printed for this cell", "RESOLVED_AS_POPULATION", "SP-GBP-12 is not a stair element: "
         "the ground view of the light-well flight start plus GF hall floor (04)", "no thickness exists for either"),
        ("5 flights (GF-03, GF-21, GF-28, 1F-01, GBP-12) as slab faces with treads", "CORRECTED",
         "five zones = two staircases (ST-A in two storey runs, ST-C) + one repeated ground view; two step flights "
         "(ST-B in the recovered bay, ST-D omitted) were not in the census", ""),
    ]
    seen = " | ".join(sorted({r["MISSING_INFORMATION"] for r in pre_census if r["MISSING_INFORMATION"]}))
    for cond, state, how, eff in conds:
        rows.append({"PRE_S8_CONDITION": cond, "WHERE_IN_PRE_S8": "02 census MISSING_INFORMATION" if cond in seen
                     else "10 exhaustion / 11 readiness", "NEW_EVIDENCE": how, "STATE": state, "EFFECT": eff})
    rows.append({"PRE_S8_CONDITION": f"readiness {ready['readiness']}", "WHERE_IN_PRE_S8": "11 readiness",
                 "NEW_EVIDENCE": "the gate is kept: a quantity is released only where outline, level and thickness "
                                 "have authority", "STATE": "KEPT_FOR_FLIGHTS",
                 "EFFECT": "two plates released, every flight blocked or in conflict"})
    return rows


def ownership_rows(s7rows, supp, sheet_of, g):
    kg7 = math.fsum(r["KG_FROM_BAR_RUNS"] for r in s7rows)
    rows = [
        {"INTERFACE": "S7 slab zones -> S8.7", "FROZEN_OWNER": "S7 (EXCLUDED_SPECIAL_STRUCTURE / CLASSIFICATION_BLOCKED)",
         "WHAT": "SP-GF_ROOF_SLAB-03, -21, -28, SP-1F_ROOF_SLAB-01", "S8_7": "every zone mapped to its elements (03)",
         "QUANTITY_MOVED": 0.0, "STATE": "TRANSFERRED_TO_S8_7 (no S7 figure changes)"},
        {"INTERFACE": "S7 top extensions at stair-adjacent supports", "FROZEN_OWNER": "S7 (released)",
         "WHAT": f"{len(s7rows)} strip ends, {_full(kg7)} kg (recomputed from 04_S7_BAR_RUNS: "
                 f"{sum(len(r['S7_BAR_RUN_ROWS']) for r in s7rows)} runs, diameters "
                 f"{sorted({d for r in s7rows for d in r['DIAMETER_MM']})})",
         "S8_7": "every extension lies in its S7 panel; S8.7 releases no top bar at any of these supports",
         "QUANTITY_MOVED": 0.0, "STATE": "OWNED_ONCE_BY_S7"},
    ]
    for occ, what in (("BM-GF_ROOF-B3-BL033-6B7", "north edge of the GF -> 1F bay (A1-W1 / A1-L1)"),
                      ("BM-1F_ROOF-B3-BL023-6B9", "north edge of the 1F -> 2F bay (A2-W1 / A2-L1)"),
                      ("CBO-GFRS-CB3-BL022", "south edge of the light-well straight flight and corner landing"),
                      ("BM-GF_ROOF-CA-BL015-69E", "beam CA across the light-well straight flight (Q-ST-10)")):
        rows.append({"INTERFACE": "S6 'With Stair' beam" if "CA" not in occ else "S6 beam CA",
                     "FROZEN_OWNER": "S6 / S6.1", "WHAT": f"{occ}: {what}",
                     "S8_7": "p.16 'TYPICAL DETAIL OF STAIR BEAM' read (2Ø12 top, 4Ø16 bottom, 6Ø8/m, depth AS PER "
                             "SCH.): evidence for the beam family; nothing is added here (Q-ST-09)",
                     "QUANTITY_MOVED": 0.0, "STATE": "OWNED_BY_S6_NOT_READDED"})
    for el in ("A1-L1", "A2-T1", "C-T1"):
        rows.append({"INTERFACE": f"{el} supports", "FROZEN_OWNER": "S6 beams / S1 columns",
                     "WHAT": json.dumps(supp[el]), "S8_7": "the plate stops at every beam and column face",
                     "QUANTITY_MOVED": 0.0,
                     "STATE": "NO_OVERLAP" if all((x["overlap_m2"] or 0) <= 1e-6 for x in supp[el]) else "OVERLAP"})
    rows += [
        {"INTERFACE": "S8.1 ground slab", "FROZEN_OWNER": "S8.1 (excluded)", "WHAT": "SP-GBP-12 8.37232788 m2; "
         "SP-GBP-01 outside the building", "S8_7": "GBP-12 = repeated view of C-F1 + hall floor; SP-GBP-01 holds "
         "ST-D (04, 03)", "QUANTITY_MOVED": 0.0, "STATE": "RECONCILED"},
        {"INTERFACE": "S8.1A recovered stair bay", "FROZEN_OWNER": "S8.1A (excluded, stair family)",
         "WHAT": "S8.1A-RG-02 11.52 m2; Q-S8.1A-03", "S8_7": "ground view of the main stair bay: ST-B + A1-F1 "
         "(repeated) + +1.00 / +0.30 floors + the central wall (04); not a second staircase",
         "QUANTITY_MOVED": 0.0, "STATE": "RECONCILED"},
        {"INTERFACE": "S8.6 slab openings", "FROZEN_OWNER": "S8.6 (no lintel)", "WHAT": "8 slab openings",
         "S8_7": "5 connected to stairs, 3 voids not stairs (03)", "QUANTITY_MOVED": 0.0, "STATE": "RECONCILED"},
        {"INTERFACE": "S8.6 / S8.6A lintels", "FROZEN_OWNER": "S8.6A", "WHAT": "no lintel is reopened",
         "S8_7": "untouched", "QUANTITY_MOVED": 0.0, "STATE": "UNCHANGED"},
        {"INTERFACE": "2F roof over the main stair", "FROZEN_OWNER": "S7 (SP-2F_ROOF_SLAB-01 / -06)",
         "WHAT": "no stair rises above +9.70 (SFRS has no tread line)", "S8_7": "nothing", "QUANTITY_MOVED": 0.0,
         "STATE": "NOT_STAIR"},
    ]
    return rows


def conservation(L):
    out = []

    def A(cid, text, ok, detail=""):
        out.append({"CHECK_ID": cid, "CHECK": text, "RESULT": "PASS" if ok else "FAIL", "DETAIL": detail})
    runs, conc, reb = L["runs"], L["conc"], L["reb"]
    A("C01", "every detected tread run is assigned to one element (or recorded as an unexplained diagonal)",
      all(r["assigned"][0] != "NONE" or r["assigned"][1].startswith("UNEXPLAINED") for r in runs),
      f"{len(runs)} runs")
    A("C02", "every element has exactly one concrete row and one lane",
      sorted(r["ELEMENT_ID"] for r in conc) == sorted(e[0] for e in ELEMENTS), f"{len(conc)} elements")
    m3 = math.fsum(r["CONCRETE_M3"] for r in conc if r["CONCRETE_M3"] is not None)
    A("C03", "released m3 = sum of the released rows", abs(m3 - L["released_m3"]) < 1e-12, _full(m3))
    kg = math.fsum(r["KG"] for r in reb if r["QUANTITY_STATE"] in RELEASED_LANES)
    A("C04", "released kg = sum of the released bar rows; Ø16 only", abs(kg - L["released_kg"]) < 1e-12 and
      {r["BAR_DIAMETER_MM"] for r in reb if r["QUANTITY_STATE"] in RELEASED_LANES} == {16}, _full(kg))
    s7 = L["s7"]
    A("C05", "S7 stair-adjacent top steel recomputed run by run equals the S7A audit; 75 ends; all in S7 panels",
      len(s7) == 75 and abs(math.fsum(r["KG_FROM_BAR_RUNS"] for r in s7) - math.fsum(r["KG_S7A_AUDIT"] for r in s7))
      < 1e-9 and all(r["STATE"] == "OWNED_ONCE_BY_S7" for r in s7) and all(
          abs(r["KG_FROM_BAR_RUNS"] - r["KG_S7A_AUDIT"]) < 1e-9 for r in s7),
      _full(math.fsum(r["KG_FROM_BAR_RUNS"] for r in s7)))
    zc = L["zone_cover"]
    A("C06", "S1 stair zones on their own sheet: GF-03, 1F-01 and GF-28 are tiled exactly by their elements; GF-21 "
      "= flight band + void", all(abs(a - b) < 1e-6 for a, b in zc.values()), json.dumps({k: [_r(a), _r(b)] for k, (a, b)
                                                                                            in zc.items()}))
    A("C07", "RG-02 partition closes to 11.52 m2 and SP-GBP-12 to 8.37232788 m2; no part is ground slab and stair",
      L["ground_ok"], "")
    rel = [e for e in L["g"] if any(r["ELEMENT_ID"] == e and r["LANE"] in RELEASED_LANES for r in conc)]
    ov = [(a, b) for a in rel for b in L["g"] if a != b and L["sheet_of"][a] == L["sheet_of"][b]
          and L["g"][a].intersection(L["g"][b]).area > 1.0]
    A("C08", "no released plate overlaps another element on its sheet", not ov, json.dumps(ov))
    bo = {el: [x for x in L["supp"][el] if (x["overlap_m2"] or 0) > 1e-6] for el in rel}
    A("C09", "no released plate overlaps an S6 beam band or a column", not any(bo.values()), json.dumps(bo))
    A("C10", "the released plates lie inside S7-excluded stair zones (no S7 panel overlaps them)",
      L["inside_excluded"], "")
    A("C11", "PRE-S8 read through whitelists only; no firewalled column bound; references_read empty",
      L["whitelist_ok"], json.dumps(PRE_S8_COLUMNS))
    A("C12", "all 24 earlier freezes, the S8.3 errata and the S1 / S2 / S3 / S3.1 register indexes verify",
      len(L["frozen"]) == 24, f"{len(L['frozen'])} manifests")
    A("C13", "every p.16 callout has a role; typical-only callouts release nothing",
      all(r["PHYSICAL_BAR_ROLE"] for r in L["binding"]) and not [r for r in reb if r["QUANTITY_STATE"] in RELEASED_LANES
                                                                  and "p.16" in r["SOURCE_HANDLE"]], "")
    A("C14", "bends, hooks, anchorages and laps are separate rows and none is released",
      not [r for r in reb if r["PHYSICAL_BAR_ROLE"] == "ANCHORAGE_AND_CONTINUATION" and
           r["QUANTITY_STATE"] in RELEASED_LANES], "")
    A("C15", "the inadvertent PRE-S8 exposure is recorded and nothing reads it", True, INADVERTENT_EXPOSURE["use"])
    return out


# ------------------------------------------------------------------ build
def run():
    from shapely.geometry import Polygon
    frozen, errata, index = verify_inputs()
    E, by = structural()
    T = registration()
    A = architectural(T)
    pre_census = pre_s8("PRE_S8_CENSUS")
    pre_if = pre_s8("PRE_S8_INTERFACES")
    pre_ex = pre_s8("PRE_S8_EXHAUSTION")
    ready = pre_s8_readiness()
    check(len([r for r in pre_census if r["ROW_KIND"] == "ELEMENT" and r["ELEMENT_ID"].startswith("SPC-STAIR-SP")]) == 5,
          "PRE-S8 carries five stair zones")
    zones = {x["panel_id"]: Polygon(x["polygon_mm"]) for x in _j(READ["S1_SLABS"])["rows"]}
    runs = population(E, A)
    g, pos, band, cut = element_geometry(E, by, runs, zones)
    c = counts(by, A, pos)
    sheet_of = {e[0]: e[4] for e in ELEMENTS}
    geo_rows, geo = geometry_rows(g, c)
    for r in geo_rows:
        r["COLUMN_OUTLINES_REMOVED"] = cut.get(r["ELEMENT_ID"], [])
    conc, sens = concrete_rows(g, geo)
    for r in geo_rows:
        sv = [x for x in sens.get(r["ELEMENT_ID"], []) if "INCLINED_WAIST_SURFACE_AREA_m2" in x]
        if sv:
            r["INCLINED_STATE"] = "SENSITIVITY_ONLY: " + "; ".join(
                f"{x['reading']}: waist {_full(x['inclined_waist_length_mm'])} mm, soffit "
                f"{_full(x['INCLINED_WAIST_SURFACE_AREA_m2'])} m2, handrail {_full(x['HANDRAIL_PATH_LENGTH_m'])} m"
                for x in sv)
    binding = rebar_binding(E, by)
    reb = rebar_rows(g, conc)
    bands = beam_bands()
    supp = supports_of(g, bands, sheet_of)
    for r in geo_rows:
        r["BEAM_BANDS_TOUCHING"] = supp[r["ELEMENT_ID"]]
    s7 = s7_recompute()
    ground, RG, G12 = ground_rows(g, zones)
    cross = crosswalk_rows(g, zones, sheet_of, band, G12, RG)
    zc = {}
    for z, sh in (("SP-GF_ROOF_SLAB-03", "GFRS"), ("SP-1F_ROOF_SLAB-01", "FFRS"), ("SP-GF_ROOF_SLAB-28", "GFRS"),
                  ("SP-GF_ROOF_SLAB-21", "GFRS")):
        tiles = sum(g[e].intersection(zones[z]).area for e in g if sheet_of[e] == sh) / 1e6
        void = [x["AREA_M2"] for x in cross if x["SOURCE_RECORD"] == z and x["RELATION"] == "VOID_OPEN_TO_BELOW"]
        zc[z] = (zones[z].area / 1e6, tiles + (void[0] if void else 0.0))
    released_m3 = math.fsum(r["CONCRETE_M3"] for r in conc if r["CONCRETE_M3"] is not None)
    released_kg = math.fsum(r["KG"] for r in reb if r["QUANTITY_STATE"] in RELEASED_LANES)
    home = {"A1-L1": "SP-GF_ROOF_SLAB-03", "A2-T1": "SP-1F_ROOF_SLAB-01", "C-T1": "SP-GF_ROOF_SLAB-28"}
    inside = all(g[e].difference(zones[home[e]]).area < 1.0 for e in home)
    s7_panels = [x for x in _j(READ["S1_SLABS"])["rows"] if x["class"] == "SLAB_PANEL"]
    inside = inside and not [x["panel_id"] for x in s7_panels for e in home
                             if x["sheet"] == sheet_of[e] and Polygon(x["polygon_mm"]).intersection(g[e]).area > 1.0]
    L = {"runs": runs, "conc": conc, "reb": reb, "s7": s7, "g": g, "sheet_of": sheet_of, "supp": supp,
         "zone_cover": zc, "ground_ok": True, "released_m3": released_m3, "released_kg": released_kg,
         "inside_excluded": inside, "whitelist_ok": True, "frozen": frozen, "binding": binding}
    cons = conservation(L)
    check(all(x["RESULT"] == "PASS" for x in cons), "conservation: " + json.dumps([x for x in cons
                                                                                   if x["RESULT"] != "PASS"]))
    own = ownership_rows(s7, supp, sheet_of, g)
    levels = level_register(A, E, None)
    census = census_rows(geo, conc, c, g)
    blocked = blocked_rows(conc, reb, c)
    pres = pre_s8_rows(pre_census, pre_ex, ready)
    return {"frozen": frozen, "errata": errata, "index": index, "runs": runs, "g": g, "c": c, "geo_rows": geo_rows,
            "conc": conc, "binding": binding, "reb": reb, "supp": supp, "s7": s7, "ground": ground, "cross": cross,
            "cons": cons, "own": own, "levels": levels, "census": census, "blocked": blocked, "pres": pres,
            "pre_if": pre_if, "ready": ready, "released_m3": released_m3, "released_kg": released_kg, "A": A, "T": T}


def provenance(L):
    lines = []
    for r in L["conc"]:
        lines.append({"record": f"CONCRETE:{r['ELEMENT_ID']}", "lane": r["LANE"], "m3": r["CONCRETE_M3"],
                      "sources": ["ST7757 " + next(e[4] for e in ELEMENTS if e[0] == r["ELEMENT_ID"]),
                                  "P7757 " + next(e[5] for e in ELEMENTS if e[0] == r["ELEMENT_ID"]), SECTION_AA,
                                  "S1 SLAB_PANEL_REGISTER"], "reason": r["REASON"]})
    for r in L["reb"]:
        if r["QUANTITY_STATE"] in RELEASED_LANES:
            lines.append({"record": f"REBAR:{r['FLIGHT_OR_LANDING_ID']}:{r['PHYSICAL_BAR_ROLE']}",
                          "lane": r["QUANTITY_STATE"], "kg": r["KG"], "sources": [r["SOURCE_HANDLE"], P16],
                          "formula": r["FORMULA"]})
    lines.append({"record": "S7_STAIR_ADJACENT", "sources": [str(READ["S7_RUNS"].relative_to(ROOT)),
                                                             str(READ["S7A_AUDIT"].relative_to(ROOT))],
                  "kg": _r(math.fsum(r["KG_FROM_BAR_RUNS"] for r in L["s7"])), "ends": len(L["s7"])})
    lines.append({"record": "INADVERTENT_EXPOSURE", **INADVERTENT_EXPOSURE})
    (HERE / OUTPUTS[14]).write_text("".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in lines),
                                    encoding="utf-8")


def write(L):
    _csv(OUTPUTS[1], L["census"])
    _csv(OUTPUTS[2], tread_rows(L["runs"]))
    _csv(OUTPUTS[3], L["cross"])
    _csv(OUTPUTS[4], L["ground"])
    _csv(OUTPUTS[5], L["levels"])
    _csv(OUTPUTS[6], L["geo_rows"])
    _csv(OUTPUTS[7], L["conc"])
    _csv(OUTPUTS[8], L["binding"])
    _csv(OUTPUTS[9], L["reb"])
    _csv(OUTPUTS[10], L["own"])
    _csv(OUTPUTS[11], L["s7"])
    _csv(OUTPUTS[12], L["blocked"])
    _csv(OUTPUTS[13], L["pres"])
    provenance(L)
    _csv(OUTPUTS[15], L["cons"])
    rel_c = [r for r in L["conc"] if r["LANE"] in RELEASED_LANES]
    rel_b = [r for r in L["reb"] if r["QUANTITY_STATE"] in RELEASED_LANES]
    lanes = Counter(r["LANE"] for r in L["conc"])
    summary = {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "physical_population": {
            "staircases": ["ST-A main stair (GF -> 1F -> 2F, two storey runs)", "ST-C light-well stair (GF -> 1F)"],
            "step_flights": ["ST-B lobby steps (+1.00 -> +0.30)", "ST-D entrance steps (+0.15 -> +1.00, omitted from "
                                                                  "S1 / PRE-S8)"],
            "elements": [e[0] for e in ELEMENTS], "pre_s8_zones": 5, "staircases_count": 2, "step_flights_count": 2},
        "released": {"concrete_m3": _r(L["released_m3"]), "kg": _r(L["released_kg"]),
                     "kg_by_diameter": {"16": _r(L["released_kg"])},
                     "kg_by_role": {k: _r(math.fsum(r["KG"] for r in rel_b if r["PHYSICAL_BAR_ROLE"] == k))
                                    for k in sorted({r["PHYSICAL_BAR_ROLE"] for r in rel_b})},
                     "elements": [r["ELEMENT_ID"] for r in rel_c], "lane": sorted({r["LANE"] for r in rel_c})},
        "concrete_lanes": dict(sorted(lanes.items())),
        "s7_stair_adjacent": {"ends": len(L["s7"]), "runs": sum(len(r["S7_BAR_RUN_ROWS"]) for r in L["s7"]),
                              "kg": _r(math.fsum(r["KG_FROM_BAR_RUNS"] for r in L["s7"])),
                              "diameters": sorted({d for r in L["s7"] for d in r["DIAMETER_MM"]})},
        "questions": sorted(QUESTIONS), "conservation": {x["CHECK_ID"]: x["RESULT"] for x in L["cons"]},
        "frozen_baselines": {k: v["manifest_sha256"] for k, v in L["frozen"].items()},
        "register_indexes": L["index"], "s8_3_errata_sha256": L["errata"], "unit_mass": UM.describe(UNIT_MASS),
        "inadvertent_exposure": INADVERTENT_EXPOSURE, "references_read": []}
    _json(OUTPUTS[16], summary)
    (HERE / OUTPUTS[0]).write_text(readme(summary, L), encoding="utf-8")
    manifest = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "FROZEN_BEFORE_COMPARISON",
                "engine_commit_stamp": summary["engine_commit"], "references_read": [],
                "inadvertent_exposure": INADVERTENT_EXPOSURE,
                "code": {c_: _sha(ROOT / c_) for c_ in CODE},
                "inputs": {str(p_.relative_to(ROOT)): _sha(p_) for p_ in READ.values()},
                "drawing_sha256": {"P7757.dxf": ARCH_SHA, "ST7757.dxf": STRUCT_SHA, "ST7757.pdf": STRUCT_PDF_SHA,
                                   "P7757 sections PDF": ARCH_PDF_SHA},
                "pre_s8_columns_read": PRE_S8_COLUMNS, "pre_s8_readiness_keys_read": list(PRE_S8_READINESS_KEYS),
                "frozen_baselines": summary["frozen_baselines"], "register_indexes": L["index"],
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "released": summary["released"],
                "rule": "frozen before any earlier Urban, contractor or third-party stair figure is used; the "
                        "comparison after it explains differences and never changes a frozen quantity"}
    _json(MANIFEST_NAME, manifest)
    for k, m_ in MANIFESTS.items():
        DR.verify_frozen(m_, ROOT)
    for o in OUTPUTS:
        check(not HYGIENE.search((HERE / o).read_text(encoding="utf-8")), f"hygiene: {o}")
    return summary


def readme(s, L):
    rel = s["released"]
    rows = "\n".join(f"| {r['ELEMENT_ID']} | {r['KIND']} | {_full(r['PLAN_AREA_M2'])} | {r['LANE']} | "
                     f"{_full(r['CONCRETE_M3']) if r['CONCRETE_M3'] is not None else '-'} |" for r in L["conc"])
    return f"""# S8.7 staircases and landings

Round {ROUND}, baseline `{BASELINE_HEAD}`, engine `{s['engine_commit']}`. Frozen before any comparison
(`{MANIFEST_NAME}`, `references_read: []`).

## Physical population

- **ST-A main stair**: one dog-leg stair in two storey runs.
  - A1 runs GF -> 1F on the GF roof sheet: lower flight, winder turn, half-landing at +3.50, upper flight.
  - A2 runs 1F -> 2F on the 1F roof sheet, with the same parts. Its half-landing level is not printed.
- **ST-B lobby steps**: 4 risers from the GF floor (+1.00) down to the +0.30 side lobby, inside the S8.1A bay.
- **ST-C light-well stair**: GF -> 1F. A curved flight runs into a straight flight, then a corner landing, a
  5-riser flight and the top arrival at +5.50.
- **ST-D entrance steps**: 5 risers from +0.15 to the +1.00 porch. They were omitted from S1 / PRE-S8 and lie in
  SP-GBP-01, outside the building.

The five PRE-S8 zones are two staircases plus one repeated ground view. GF-03 and 1F-01 are ST-A. GF-21 and GF-28
are ST-C. GBP-12 is ST-C seen on the ground plan.

## Concrete

| Element | Kind | Plan m2 | Lane | m3 |
|---|---|---|---|---|
{rows}

Released: **{_full(rel['concrete_m3'])} m3**, on the project basis. It is three flat plates whose outline, level and
thickness all have authority:

- the GF -> 1F half-landing A1-L1, at +3.50;
- the 1F -> 2F arrival strip A2-T1, at +9.70;
- the light-well top arrival C-T1, at +5.50.

Reinforcement released: **{_full(rel['kg'])} kg**, all Ø16. These are the 8Ø16/m bottom bars that the plan callouts
and bar lines carry across those plates, measured by rate density. Every flight, winder turn, unlevelled landing and
step flight is blocked or in source conflict; its sensitivity is in `07_CONCRETE_QTO.csv` and is never released.

The main open points for the engineer (`12_BLOCKED_AND_CONFLICTS.csv`, Q-ST-01 to Q-ST-12):

- **Q-ST-01**: the GF -> 1F riser count (structural 12 + 12, architectural 10 + 11).
- **Q-ST-02**: the waist thickness.
- **Q-ST-03**: the 1F -> 2F half-landing level and the light-well corner landing level.
- **Q-ST-08**: which typical p.16 bars apply to these stairs.

## S7 stair-adjacent top steel

{s['s7_stair_adjacent']['ends']} strip ends, {s['s7_stair_adjacent']['runs']} bar runs, {_full(s['s7_stair_adjacent']['kg'])} kg (Ø{', Ø'.join(s['s7_stair_adjacent']['diameters'])}),
recomputed run by run from the frozen S7 bar records. All of it stays S7's; S8.7 releases no top bar at those
supports.

## Firewall

PRE-S8 is read through column whitelists only. One exploratory read during the source survey printed the
`CONCRETE_STATES` cell of the PRE-S8 candidate register (an earlier commercial stair figure). It is recorded in the
manifest and nothing reads it.
"""


def main():
    L = run()
    s = write(L)
    print(json.dumps({"released": s["released"], "lanes": s["concrete_lanes"], "s7": s["s7_stair_adjacent"]},
                     indent=1))


if __name__ == "__main__":
    main()
