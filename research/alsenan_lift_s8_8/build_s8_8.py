"""S8.8 - lift pit, shaft walls, foundation and intermediate tie beam: population, ownership, geometry, concrete and
reinforcement. Source-controlled and blind (frozen before any comparison).

    python3 -I research/alsenan_lift_s8_8/build_s8_8.py

Reads the registered structural DXF (ST7757: the FP / GBP / GFRS / FFRS / SFRS sheets through the frozen S1 reader),
the registered architectural DXF (P7757: GF / 1F / 2F plans, registered onto the structural sheets by the frozen S8.6
translations) and frozen Urban stages:
- S1 registers (special occurrences, project rules, levels, footings, footing definitions, columns, slab panels);
- S2 component release (the FF footing, the GF lift tie beam, the roof panel over the shaft);
- S3 column flags and the S3.1 starter register (the four lift columns);
- S4 / S4.1 FF footing reinforcement and the S4.1 ownership transfer of the p.14 '2 Ø16' bars;
- S5 ground beams that frame into the FF footing; S6 beams around the shaft; S7 panel summary;
- S8.1A recovered pit region; S8.6 landing openings and their lintel binding; S8.7 stair element outlines;
- PRE-S8, through column whitelists only (its concrete-state columns and coverage matrices are never bound to a name).
p.14 of ST7757.pdf ('DETAIL OF LIFT WITH ISOLATED FOOTING') has no usable vector text: it enters as a visual record
read in session from renders; the renders are client drawing and stay out of git. p.8 note 19 enters through the S1
rule register (its English interpretation).

Every representation of the shaft on every plan is grouped into one physical shaft. Each component gets one
ownership state. A quantity is released only where its outline, its levels and its thickness all have authority; the
pit depth is the lift manufacturer's and is not printed, so no pit-wall concrete and no wall bar is released. No
earlier Urban total, contractor figure or third-party figure is read before the freeze.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "research" / "external_engine_lab"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import delta_release as DR  # noqa: E402
from engine.source import rebar_unit_mass as UM  # noqa: E402
from engine.source import shaft_geometry as SG  # noqa: E402

ROUND = "S8_8"
DATE = "2026-10-10"
BASELINE_HEAD = "dc2d778"
POLICY = "S8_8_LIFT_V1"
R = ROOT / "research"
BY_SHA = ROOT / "data/inputs/by_sha256"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
STRUCT_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
STRUCT_PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
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
             "S8.6A": R / "alsenan_lintels_s8_6a/12_S8_6A_CORRECTION_MANIFEST.json",
             "S8.7": R / "alsenan_stairs_s8_7/17_S8_7_FREEZE_MANIFEST.json"}
S83_ERRATA = R / "alsenan_dome_ring_s8_3/errata"
S1D = R / "alsenan_structural_census_s1"
S2D = R / "alsenan_structural_s2"
S3D = R / "alsenan_column_rebar_s3"
S31D = R / "alsenan_column_rebar_s3_1"
INDEXES = {"S1": (S1D / "INDEX.json", "registers"), "S2": (S2D / "INDEX.json", "outputs"),
           "S3": (S3D / "INDEX.json", "outputs"), "S3.1": (S31D / "INDEX.json", "outputs")}
PRE = R / "pre_s8_structural_completeness"
READ = {"S1_SPECIAL": S1D / "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER.json",
        "S1_RULES": S1D / "STRUCTURAL_PROJECT_RULE_REGISTER.json",
        "S1_LEVELS": S1D / "STRUCTURAL_LEVEL_REGISTER.json",
        "S1_FOOTINGS": S1D / "FOOTING_OCCURRENCE_REGISTER.json",
        "S1_FOOTING_DEFS": S1D / "FOOTING_DEFINITION_REGISTER.json",
        "S1_COLUMNS": S1D / "COLUMN_OCCURRENCE_REGISTER.json",
        "S1_SLABS": S1D / "SLAB_PANEL_REGISTER.json",
        "S2_RELEASE": S2D / "ALSENAN_COMPONENT_RELEASE.json",
        "S3_FLAGS": S3D / "COLUMN_ENGINEERING_FLAGS.json",
        "S31_STARTERS": S31D / "COLUMN_LAP_STARTER_REGISTER.json",
        "S4_OCC": R / "alsenan_footing_rebar_s4/FOOTING_REBAR_OCCURRENCES.csv",
        "S4_COMP": R / "alsenan_footing_rebar_s4/FOOTING_REBAR_COMPONENTS.csv",
        "S41_TRANSFERS": R / "alsenan_footing_rebar_s4_1/S4_1_OWNERSHIP_TRANSFERS.csv",
        "S41_UNRESOLVED": R / "alsenan_footing_rebar_s4_1/S4_1_UNRESOLVED.csv",
        "S5_OCC": R / "alsenan_ground_system_rebar_s5/GROUND_SYSTEM_REBAR_OCCURRENCES.csv",
        "S6_OCC": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCES.csv",
        "S7_PANELS": R / "alsenan_slab_rebar_s7/05_S7_PANEL_SUMMARY.csv",
        "S81A_REGION": R / "alsenan_ground_slab_s8_1a/01_RECOVERED_LIFT_PIT_REGION.csv",
        "S81A_QUESTIONS": R / "alsenan_ground_slab_s8_1a/08_CONFLICT_AND_QUESTION_REGISTER.csv",
        "S86_CENSUS": R / "alsenan_lintels_s8_6/01_OPENING_CENSUS.csv",
        "S86_BINDING": R / "alsenan_lintels_s8_6/04_OPENING_LINTEL_BINDING_MATRIX.csv",
        "S86_REGISTRATION": R / "alsenan_lintels_s8_6/03_ARCH_STRUCTURAL_REGISTRATION.csv",
        "S87_GEOMETRY": R / "alsenan_stairs_s8_7/06_PLAN_AND_INCLINED_GEOMETRY.csv",
        "PRE_S8_CENSUS": PRE / "02_STRUCTURAL_ELEMENT_CENSUS.csv",
        "PRE_S8_INTERFACES": PRE / "07_INTERFACE_DOUBLE_COUNT_AUDIT.csv",
        "PRE_S8_EXHAUSTION": PRE / "10_S8_SOURCE_EXHAUSTION.csv",
        "PRE_S8_READINESS": PRE / "11_S8_READINESS_DECISION.json"}
# PRE-S8 is read for population, ownership and missing-authority claims only. Its concrete-state columns and its
# coverage matrices carry earlier figures: they are never bound to a name before the freeze.
PRE_S8_COLUMNS = {"PRE_S8_CENSUS": ("ELEMENT_ID", "ROW_KIND", "PARENT_ELEMENT", "ELEMENT_FAMILY", "FLOOR",
                                    "SOURCE_PAGE", "DXF_HANDLES", "PHYSICAL_GEOMETRY", "EXISTING_STAGE_OWNER",
                                    "NEW_S8_OWNER", "S8_SCOPE", "SOURCE_AUTHORITY", "MISSING_INFORMATION", "CONFLICT",
                                    "QA_STATE"),
                  "PRE_S8_INTERFACES": ("INTERFACE", "SIDE_A", "SIDE_B", "RISK", "STATE"),
                  "PRE_S8_EXHAUSTION": ("S8_CANDIDATE", "CH_PLAN", "CH_SECTION", "CH_TYPICAL_DETAIL", "CH_NOTES_EN",
                                        "CH_ARCHITECTURE", "DIMENSIONED_EVIDENCE", "SCHEMATIC_NTS_EVIDENCE",
                                        "MISSING", "READINESS", "RULE")}
PRE_S8_READINESS_KEYS = ("missing", "readiness", "schematic_nts", "dimensioned")
PRE_S8_FIREWALLED = ("CONCRETE_QUANTITY_STATE", "CONCRETE_STATES", "CONCRETE", "BARS_OWNED", "URBAN_LINES",
                     "V3B_", "CR_")
PRE_S8_LIFT = r"LIFT|(?<![A-Z])PIT(?![A-Z])|_PIT|FTG-FF-18688"
CODE = ["engine/source/shaft_geometry.py", "engine/source/rebar_unit_mass.py", "engine/source/delta_release.py",
        "research/alsenan_lift_s8_8/build_s8_8.py", "research/external_engine_lab/alsenan_structural_s1.py"]
OUTPUTS = ["00_README.md", "01_SOURCE_CENSUS.csv", "02_LIFT_POPULATION.csv", "03_REPRESENTATION_CROSSWALK.csv",
           "04_FOUNDATION_OWNERSHIP_AUDIT.csv", "05_PIT_FOOTPRINT_AND_DEPTH_EVIDENCE.csv",
           "06_WALL_GEOMETRY_AND_CONCRETE_QTO.csv", "07_REBAR_CALLOUT_REGISTER.csv", "08_REBAR_QTO.csv",
           "09_TIE_BEAM_TRIGGER_AND_OWNERSHIP.csv", "10_LIFT_OPENING_RECONCILIATION.csv",
           "11_OVERLAP_AND_DOUBLE_COUNT_CHECKS.csv", "12_OWNERSHIP_AUDIT.csv", "13_BLOCKED_AND_CONFLICTS.csv",
           "14_RFI_QUESTIONS.csv", "15_PROVENANCE.jsonl", "16_CONSERVATION_CHECKS.csv", "17_S8_8_SUMMARY.json"]
MANIFEST_NAME = "18_S8_8_FREEZE_MANIFEST.json"
UNIT_MASS = {"method": UM.D2_OVER_162, "authority": "project-wide method used by S3.1 / S6.1 / S7 / S8",
             "selected_by": "Urban (project basis)"}
SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO = "SOURCE_DERIVED_PHYSICAL", "PROJECT_BASIS_QTO"
BLOCKED, CONFLICT, SENS = "BLOCKED_UNQUANTIFIED", "SOURCE_CONFLICT", "SENSITIVITY_ONLY"
NOT_IN_SOURCE, NOT_S8_8 = "NOT_IN_SOURCE", "NOT_RELEASED_BY_S8_8 (owned by another family)"
RELEASED_LANES = (SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO)
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
ARABIC = re.compile(r"[؀-ۿ]+(?:[\s.,'\"()-]*[؀-ۿ]+)*")
OVERLAP_TOL_M2 = 1e-4


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


def _clean(s):
    """source text without its Arabic runs (the drawings' Arabic is never reproduced)."""
    return ARABIC.sub("<Arabic text>", s or "")


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


def _m2(mm2):
    return _r(mm2 / 1e6)


# ------------------------------------------------------------------ inputs
def verify_inputs():
    for sha, name, ext in ((ARCH_SHA, "P7757.dxf", "dxf"), (STRUCT_SHA, "ST7757.dxf", "dxf"),
                           (STRUCT_PDF_SHA, "ST7757.pdf", "pdf")):
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


def pre_s8(key, pattern=PRE_S8_LIFT):
    """PRE-S8 rows of the lift family, whitelisted columns only."""
    cols = PRE_S8_COLUMNS[key]
    check(not [c for c in cols for f in PRE_S8_FIREWALLED if c.startswith(f)],
          "PRE-S8 whitelist excludes the firewalled columns")
    with open(READ[key], encoding="utf-8", newline="") as fh:
        rd = csv.reader(fh)
        head = next(rd)
        idx = {c: head.index(c) for c in cols}
        out = []
        for row in rd:
            rec = {c: _clean(row[i]) for c, i in idx.items()}
            if re.search(pattern, " ".join(rec.values()), re.I):
                out.append(rec)
    return out


def pre_s8_readiness():
    c = _j(READ["PRE_S8_READINESS"])["candidates"]
    return {k: {kk: _clean(str(v.get(kk))) for kk in PRE_S8_READINESS_KEYS} for k, v in c.items() if "LIFT" in k}


# ------------------------------------------------------------------ cited drawing geometry (checked against the DXF)
SHAFT_IN = (19787.904, 15611.856, 21587.904, 17411.856)     # S-BW inside face, FP 10EA = GBP 7BE
SHAFT_OUT = (19587.904, 15411.856, 21787.904, 17611.856)    # S-BW outside face, FP 10EB = GBP 7C2
COLUMNS = {  # corner, S1 chain, type at the foundation storey, plan rectangle drawn on FP / GBP / GFRS / FFRS
    "SW": ("COLPOS-X09-Y07-19688-15662", "C2", (19587.904, 15411.856, 19787.904, 15911.856)),
    "NW": ("COLPOS-X09-Y09-19688-17362", "C1", (19587.904, 17111.856, 19787.904, 17611.856)),
    "SE": ("COLPOS-X10-Y07-21713-15912", "C9", (21587.904, 15411.856, 21837.904, 16411.856)),
    "NE": ("COLPOS-X10-Y09-21688-17362", "C2", (21587.904, 17111.856, 21787.904, 17611.856))}
SE_2F = (21587.904, 15411.856, 21787.904, 16111.856)        # the SE column at 2F (S1 COL-C9-X10-Y07-2F, 20 x 70)
FOOTING = (18687.697, 14111.998, 23287.697, 18611.998)      # FF outline FP 1B2B
FOOTING_ID, FOOTING_OCC = "FTG-FF-18688-14112", "FOCC-1B2B"
DOOR_X = (20187.904, 21187.904)                             # architectural jambs, every floor
COLUMN_HANDLES = {"FP": ("1096", "1099", "1090", "1093"), "GBP": ("1F2", "1F5", "1EC", "1EF"),
                  "GFRS": ("33E", "341", "338", "33B"), "FFRS": ("67F", "682", "679", "67C"),
                  "SFRS": ("41E", "421", "418", "41B")}
CITED_POLY = [  # sheet, handle, layer, rectangle, what
    ("FP", "10EA", "S-BW", SHAFT_IN, "shaft inside face (foundation plan)"),
    ("FP", "10EB", "S-BW", SHAFT_OUT, "shaft outside face (foundation plan)"),
    ("GBP", "7BE", "S-BW", SHAFT_IN, "shaft inside face (ground-beam plan)"),
    ("GBP", "7C2", "S-BW", SHAFT_OUT, "shaft outside face (ground-beam plan)"),
    ("FP", "1B2B", "S-FOOTINGS", FOOTING, "FF footing outline"),
] + [(sh, h, "S-COL.BON", SE_2F if (sh, k) == ("SFRS", "SE") else COLUMNS[k][2], f"{k} lift column ({sh})")
     for sh, hs in COLUMN_HANDLES.items() for k, h in zip(("SW", "NW", "SE", "NE"), hs)]
CITED_LINE = [  # sheet, handle, layer, end points, what
    ("GFRS", "54F", "S-OPENING", ((19787.904, 15611.856), (21587.904, 17411.856)), "shaft void cross (GF roof)"),
    ("GFRS", "550", "S-OPENING", ((19787.904, 17411.856), (21587.904, 15611.856)), "shaft void cross (GF roof)"),
    ("FFRS", "73F", "S-OPENING", ((19787.904, 17411.856), (21587.904, 15611.856)), "shaft void cross (1F roof)"),
    ("FFRS", "740", "S-OPENING", ((21587.904, 17411.856), (19787.904, 15611.856)), "shaft void cross (1F roof)"),
]
CITED_TEXT = [  # sheet, handle, text, what
    ("FP", "1676", "FF", "footing tag inside the shaft"), ("FP", "109A", "C9", "SE column tag"),
    ("FP", "109B", "C2", "SW column tag"), ("FP", "109C", "C2", "NE column tag"), ("FP", "109D", "C1", "NW column tag"),
    ("GFRS", "45E", "B1", "beam tag, N side (GF roof)"), ("GFRS", "45F", "B14", "beam tag, S side (GF roof)"),
    ("GFRS", "4B6", "B7", "beam tag, W side (GF roof)"), ("GFRS", "4B7", "B1", "beam tag, E side (GF roof)"),
    ("FFRS", "6CB", "B1", "beam tag, N side (1F roof)"), ("FFRS", "6CC", "B7", "beam tag, S side (1F roof)"),
    ("FFRS", "6CD", "B7", "beam tag, W side (1F roof)"), ("FFRS", "6CE", "B1", "beam tag, E side (1F roof)"),
    ("SFRS", "78A", "B2", "beam tag, S side (2F roof)"), ("SFRS", "78B", "B1", "beam tag, E side (2F roof)"),
    ("SFRS", "78C", "B1", "beam tag, W side (2F roof)"), ("SFRS", "78D", "B1", "beam tag, N side (2F roof)"),
    ("SFRS", "791", "5%%c10/m", "roof slab bars over the shaft (2F roof)"),
    ("SFRS", "793", "5%%c10/m", "roof slab bars over the shaft (2F roof)"),
]
POOL_SBW = [("GBP", "7C5"), ("GBP", "7C6")]                 # the only other S-BW outlines: the S8.2 pool
ARCH_CITED = {  # floor: (handle, kind, geometry, what); geometry registered onto the structural sheet frame
    "GF": [("216", "LINE", ((19787.904, 17411.856), (19787.904, 15611.856)), "inside face W"),
           ("212", "LINE", ((21587.904, 17411.856), (21587.904, 15611.856)), "inside face E"),
           ("219", "LINE", ((21587.904, 17411.856), (19787.904, 17411.856)), "inside face N"),
           ("21E", "LINE", ((20187.904, 15611.856), (19787.904, 15611.856)), "inside face S, W of the door"),
           ("21D", "LINE", ((21587.904, 15611.856), (21187.904, 15611.856)), "inside face S, E of the door"),
           ("21C", "LINE", ((19587.904, 17611.856), (19587.904, 15611.856)), "outside face W"),
           ("BB", "LINE", ((20187.904, 15411.856), (19587.904, 15411.856)), "outside face S, W of the door"),
           ("20D", "LINE", ((21787.904, 15411.856), (21187.904, 15411.856)), "outside face S, E of the door"),
           ("226", "LINE", ((20187.904, 15411.856), (20187.904, 15611.856)), "door jamb W"),
           ("227", "LINE", ((21187.904, 15411.856), (21187.904, 15611.856)), "door jamb E"),
           ("666", "DIMENSION", 1800.0, "inside width E-W"), ("67D", "DIMENSION", 1800.0, "inside depth N-S"),
           ("672", "DIMENSION", 200.0, "wall N")],
    "1F": [("B13", "LINE", ((19787.904, 17411.856), (19787.904, 15611.856)), "inside face W"),
           ("B11", "LINE", ((21587.904, 17411.856), (21587.904, 15611.856)), "inside face E"),
           ("B15", "LINE", ((21587.904, 17411.856), (19787.904, 17411.856)), "inside face N"),
           ("B1A", "LINE", ((20187.904, 15611.856), (19787.904, 15611.856)), "inside face S, W of the door"),
           ("B19", "LINE", ((21587.904, 15611.856), (21187.904, 15611.856)), "inside face S, E of the door"),
           ("B06", "LINE", ((21787.904, 17611.856), (21787.904, 15611.856)), "outside face E"),
           ("B14", "LINE", ((21787.904, 17611.856), (19787.904, 17611.856)), "outside face N"),
           ("B96", "LINE", ((20187.904, 15411.856), (20187.904, 15611.856)), "door jamb W"),
           ("B97", "LINE", ((21187.904, 15411.856), (21187.904, 15611.856)), "door jamb E"),
           ("D31", "DIMENSION", 1800.0, "inside depth N-S"), ("D3D", "DIMENSION", 1800.0, "inside width E-W"),
           ("D62", "DIMENSION", 200.0, "wall N"), ("E94", "DIMENSION", 200.0, "wall E")],
    "2F": [("1297", "LINE", ((19787.904, 17411.856), (19787.904, 15611.856)), "inside face W"),
           ("1293", "LINE", ((21587.904, 17411.856), (21587.904, 15611.856)), "inside face E"),
           ("1299", "LINE", ((21587.904, 17411.856), (19787.904, 17411.856)), "inside face N"),
           ("129C", "LINE", ((20187.904, 15611.856), (19787.904, 15611.856)), "inside face S, W of the door"),
           ("129B", "LINE", ((21587.904, 15611.856), (21187.904, 15611.856)), "inside face S, E of the door"),
           ("128A", "LINE", ((20187.904, 15411.856), (19587.904, 15411.856)), "outside face S, W of the door"),
           ("1289", "LINE", ((21587.904, 15411.856), (21187.904, 15411.856)), "outside face S, E of the door"),
           ("12AE", "LINE", ((20187.904, 15411.856), (20187.904, 15611.856)), "door jamb W"),
           ("12AF", "LINE", ((21187.904, 15411.856), (21187.904, 15611.856)), "door jamb E"),
           ("139A", "DIMENSION", 1800.0, "inside depth N-S"), ("13A6", "DIMENSION", 1800.0, "inside width E-W"),
           ("13CB", "DIMENSION", 200.0, "wall N"), ("142F", "DIMENSION", 200.0, "wall E"),
           ("1538", "DIMENSION", 200.0, "wall S")]}

# ------------------------------------------------------------------ visual record (no usable vector text on p.14)
P14 = "ST7757.pdf p.14 'DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT)' (typical section, visual)"
P14_SECTION = ("the section cuts two opposite walls: the right-hand wall carries the 'Lift door' above F.F.L, so it "
               "is the door wall (S in plan, the only wall with a landing door); the left-hand wall is the wall "
               "opposite it (N). The W and E walls are not cut and no other view shows their bars")
P14_CALLOUTS = [
    # id, callout as printed, where it is drawn, bar direction, role, walls drawn, face, spacing / count, extent,
    # anchorage / bends / laps as drawn, owner, state
    ("P14-G01", "20", "dimension across each cut wall", "-", "WALL_THICKNESS", "S, N", "-", "200 mm", "-", "-",
     "S8.8", "ESTABLISHED (agrees with the S-BW outlines and the architectural 200 dimensions)"),
    ("P14-G02", "AS ARCH.", "clear width between the cut walls", "-", "PIT_INSIDE_WIDTH", "-", "-",
     "1800 mm (architectural plans)", "-", "-", "S8.8", "ESTABLISHED"),
    ("P14-G03", "AS PER SCHEDULE", "footing projection beyond each wall; footing depth", "-", "FOOTING_EXTENT",
     "-", "-", "FF row: 460 x 450 x 55 cm", "-", "-", "S1 / S4 (footing family)", "ESTABLISHED"),
    ("P14-G04", "As Per Lift Manufactures recommendations", "vertical dimension from the footing top inside the "
     "pit to the top of the cut walls", "-", "PIT_DEPTH", "-", "-", "not printed", "-", "-", "S8.8",
     "BLOCKED (the lift manufacturer's)"),
    ("P14-G05", "AS PER PLAN", "the wall above the slab on grade (no hatch, no bars)", "-",
     "SHAFT_ENCLOSURE_ABOVE_PIT", "N (drawn above the slab)", "-", "-", "-", "-",
     "architectural plans (blockwork 200, S8.6 wall owner)", "NOT_STRUCTURAL_RC in the source"),
    ("P14-G06", "Lift door", "opening above F.F.L in the right-hand wall", "-", "LANDING_DOOR", "S", "-", "-", "-",
     "-", "S8.6 (OP-GF-023)", "OPENING_IN_BLOCKWORK"),
    ("P14-G07", "F.F.L / Slab on grade.", "the cut walls stop at the top of the slab on grade", "-",
     "PIT_WALL_TOP", "S, N", "-", "GF FFL +1.00 less the floor finish (not printed)", "-", "-",
     "S8.1 / S8.1A (ground slab)", "BLOCKED (finish thickness not printed)"),
    ("P14-R01", "6Ø12/m", "dots on both faces of both cut walls; the right-hand leader passes through both faces",
     "HORIZONTAL (along the wall)", "WALL_HORIZONTAL", "S, N", "BOTH (drawn)", "6 per metre of wall height",
     "around the wall face; at the corner columns not shown", "laps, corner bars and the column joint not shown",
     "S8.8", "BLOCKED (distribution = wall height, not established; applicability to W / E not shown)"),
    ("P14-R02", "6Ø16/m", "lines on both faces of both cut walls, closed as a U over the wall top and running down "
     "through the footing to its bottom layer; the leader crosses both faces", "VERTICAL", "WALL_VERTICAL",
     "S, N", "BOTH (drawn)", "6 per metre of wall face", "footing bottom layer to the wall top, U over the top",
     "no bend drawn at the foot; U closed over the top; laps not shown", "S8.8",
     "BLOCKED (bar length needs the wall height and the footing top; applicability to W / E not shown)"),
    ("P14-R03", "2 Ø16", "two dots in the footing top layer, inside the wall width (upper leader, left wall); "
     "repeated without a label under the right wall", "LONGITUDINAL (along the wall, in the footing)",
     "WALL_BASE_TOP", "S, N", "inside the wall cage", "2 per cut wall", "along the wall: not shown",
     "ends at the corners / columns not shown", "S8.8 (S4.1-T01 transfer from the FF footing)",
     "BLOCKED (length and the W / E walls not established)"),
    ("P14-R04", "2 Ø16", "two dots in the footing bottom layer, inside the wall width (lower leader, left wall); "
     "repeated without a label under the right wall", "LONGITUDINAL (along the wall, in the footing)",
     "WALL_BASE_BOTTOM", "S, N", "inside the wall cage", "2 per cut wall", "along the wall: not shown",
     "ends at the corners / columns not shown", "S8.8 (S4.1-T01 transfer from the FF footing)",
     "BLOCKED (length and the W / E walls not established)"),
    ("P14-R05", "2Ø12", "two dots inside the U at the top of the right-hand (door) wall; repeated without a label "
     "at the top of the left wall", "LONGITUDINAL (along the wall top)", "WALL_TOP", "S, N", "inside the U",
     "2 per cut wall", "along the wall top: not shown", "ends not shown", "S8.8",
     "BLOCKED (length and the W / E walls not established)"),
    ("P14-R06", "AS PER SCH.", "three leaders to the footing top and bottom dots", "BOTH WAYS", "FOOTING_MATS",
     "-", "top and bottom", "FF row: 6Ø14/m top, 9Ø14/m bottom, both ways", "footing", "-",
     "S4 / S4.1 (FOCC-1B2B)", "ALREADY_OWNED_AND_MEASURED (S4 lower bound)"),
    ("P14-R07", "(perimeter loop, no label)", "a closed loop round the footing section", "-", "FOOTING_LOOP", "-",
     "-", "-", "-", "S4.1: the loop cannot pair the 6/m top with the 9/m bottom bars (QA only)",
     "S4.1 (FOCC-1B2B end treatments)", "BLOCKED in S4.1 (not re-counted here)"),
    ("P14-N01", "Water proofing membrane / Protection Board / Well graded clean compacted fill / 5cm Screed / 10cm "
     "Plain con.", "outside the walls and under the footing", "-", "NON_STRUCTURAL_LAYERS", "-", "-", "-", "-", "-",
     "waterproofing / earthworks / footing blinding (not S8.8)", "NOT_S8_8"),
    ("P14-X01", "5Ø12/m", "below the title line of the lift detail", "-", "OTHER_DETAIL", "-", "-", "-", "-", "-",
     "the parapet detail below on the same sheet", "NOT_LIFT"),
]
P8_N19_RULE, P14_RULE, P9_SOIL_RULE, P8_SLAB_RULE = "P8-N19", "P14-LIFT", "P9-SOIL", "P8-N18"


# ------------------------------------------------------------------ drawings
def structural():
    import alsenan_structural_s1 as S1
    src = S1.Source()
    E = src.entities()
    by = {(sh, e["handle"]): e for sh in E for e in E[sh]}
    for sh, h, layer, rect, what in CITED_POLY:
        e = by.get((sh, h))
        check(e is not None and e["type"] == "LWPOLYLINE" and e["layer"] == layer and e.get("closed"),
              f"cited {sh} {h} ({what}) exists")
        xs, ys = [p[0] for p in e["pts"]], [p[1] for p in e["pts"]]
        check(max(abs(a - b) for a, b in zip((min(xs), min(ys), max(xs), max(ys)), rect)) < 0.01,
              f"cited {sh} {h} ({what}) rectangle")
        check(len(e["pts"]) == 4, f"cited {sh} {h} is a rectangle")
    for sh, h, layer, (a, b), what in CITED_LINE:
        e = by.get((sh, h))
        check(e is not None and e["type"] == "LINE" and e["layer"] == layer, f"cited {sh} {h} ({what}) exists")
        check(math.dist(e["a"][:2], a) < 0.01 and math.dist(e["b"][:2], b) < 0.01, f"cited {sh} {h} ({what})")
    near = (SHAFT_OUT[0] - 400, SHAFT_OUT[1] - 400, SHAFT_OUT[2] + 400, SHAFT_OUT[3] + 400)
    for sh, h, text, what in CITED_TEXT:
        e = by.get((sh, h))
        check(e is not None and e["type"] == "TEXT" and e["text"] == text, f"cited {sh} {h} '{text}' ({what})")
        check(near[0] <= e["p"][0] <= near[2] and near[1] <= e["p"][1] <= near[3], f"cited {sh} {h} at the shaft")
    sbw = sorted((sh, e["handle"]) for sh in E for e in E[sh] if e.get("layer") == "S-BW")
    check(sbw == sorted([("FP", "10EA"), ("FP", "10EB"), ("GBP", "7BE"), ("GBP", "7C2")] + POOL_SBW),
          "S-BW outlines: the shaft (FP, GBP) and the pool only")
    return src, E, by


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
    out = {}
    for fl, cited in ARCH_CITED.items():
        _, tx, ty, _ = T[fl]
        rows = []
        for h, kind, geo, what in cited:
            e = doc.entitydb.get(h)
            check(e is not None and e.dxftype() == kind, f"architectural {fl} {h} ({what}) exists")
            if kind == "LINE":
                a = (e.dxf.start.x + tx, e.dxf.start.y + ty)
                b = (e.dxf.end.x + tx, e.dxf.end.y + ty)
                check(math.dist(a, geo[0]) < 0.01 and math.dist(b, geo[1]) < 0.01,
                      f"architectural {fl} {h} ({what}) registers onto the S-BW outline")
                rows.append({"floor": fl, "handle": h, "kind": kind, "layer": e.dxf.layer, "what": what,
                             "a": [_r(a[0], 3), _r(a[1], 3)], "b": [_r(b[0], 3), _r(b[1], 3)]})
            else:
                m = float(e.get_measurement())
                check(abs(m - geo) < 1e-6, f"architectural {fl} {h} ({what}) reads {geo}")
                p = (e.dxf.defpoint2.x + tx, e.dxf.defpoint2.y + ty)
                q = (e.dxf.defpoint3.x + tx, e.dxf.defpoint3.y + ty)
                rows.append({"floor": fl, "handle": h, "kind": kind, "layer": e.dxf.layer, "what": what,
                             "measurement_mm": m, "a": [_r(p[0], 3), _r(p[1], 3)], "b": [_r(q[0], 3), _r(q[1], 3)]})
        out[fl] = rows
    return out


def schedule_row():
    """the FF row of the footing schedule (FTB insert 2B1E), read directly from the structural DXF."""
    import ezdxf
    doc = ezdxf.readfile(str(BY_SHA / f"{STRUCT_SHA}.dxf"))
    e = doc.entitydb.get("2B1E")
    check(e is not None and e.dxftype() == "INSERT" and e.dxf.name == "FTB", "FF schedule row 2B1E exists")
    att = {a.dxf.tag: a.dxf.text for a in e.attribs}
    check(att.get("FO-TY") == "FF", "schedule row 2B1E is FF")
    return {k: att[k] for k in ("FO-TY", "W", "H", "DEPHT", "SH-T-B", "SH-T-D", "LO-T-B", "LO-T-D", "SH-B-B",
                                "SH-B-D", "LO-B-B", "LO-B-D")}


def beam_bands(src, sheets=("GBP", "GFRS", "FFRS", "SFRS")):
    import alsenan_structural_s1 as S1
    from shapely.geometry import Polygon
    out = {}
    for sh in sheets:
        segs, _, _ = S1.beam_linework(src, sh)
        for ln in S1.beam_lines(S1.straight_bands(segs)):
            d = tuple(float(v) for v in ln["dir"])
            n = tuple(float(v) for v in ln["normal"])
            o, w, t0, t1 = float(ln["offset"]), float(ln["width_mm"]), float(ln["t0"]), float(ln["t1"])
            out[(sh, ln["line_id"])] = Polygon([(d[0] * t + n[0] * (o + s * w / 2), d[1] * t + n[1] * (o + s * w / 2))
                                                for t, s in ((t0, -1), (t1, -1), (t1, 1), (t0, 1))])
    return out


# ------------------------------------------------------------------ population
def representations(E, by, A):
    """every view of the shaft and of each lift column, grouped: repeated views are one physical object."""
    from shapely.geometry import Polygon
    slabs = {x["panel_id"]: x for x in _j(READ["S1_SLABS"])["rows"]}
    items = [("FP:10EA", "FP", SHAFT_IN), ("GBP:7BE", "GBP", SHAFT_IN)]
    for pid, sh in (("SP-GF_ROOF_SLAB-13", "GFRS"), ("SP-1F_ROOF_SLAB-06", "FFRS"), ("SP-2F_ROOF_SLAB-03", "SFRS")):
        b = Polygon(slabs[pid]["polygon_mm"]).bounds
        items.append((f"{sh}:{pid}", sh, b))
    for fl, rows in A.items():
        pts = [p for r in rows if r["kind"] == "LINE" and r["what"].startswith("inside face") for p in (r["a"], r["b"])]
        items.append((f"ARCH-{fl}:inside faces", f"ARCH-{fl}", (min(p[0] for p in pts), min(p[1] for p in pts),
                                                                max(p[0] for p in pts), max(p[1] for p in pts))))
    pool = []
    for sh, h in POOL_SBW:
        xs = [p[0] for p in by[(sh, h)]["pts"]]
        ys = [p[1] for p in by[(sh, h)]["pts"]]
        pool.append((f"{sh}:{h}", f"{sh}-POOL-{h}", (min(xs), min(ys), max(xs), max(ys))))
    shaft_groups = SG.group_representations(items + pool[:1], tol=1.0)
    rows = []
    for g in shaft_groups:
        is_shaft = any(v == "FP" for v in g["views"])
        rows.append({"OBJECT": "LIFT-01 shaft void (inside face)" if is_shaft else "S8.2 SPC-POOL (S-BW, GBP only)",
                     "VIEWS": g["views"], "RECORDS": g["ids"], "RECT_MM": [_r(v, 3) for v in g["rect"]],
                     "PHYSICAL_OBJECTS": 1, "STATE": "ONE_PHYSICAL_SHAFT" if is_shaft else
                     "NOT_A_LIFT (no FF footing, no void on any upper floor; owned by S8.2)"})
    for k, (chain, typ, rect) in COLUMNS.items():
        its = []
        for sh, hs in COLUMN_HANDLES.items():
            h = hs[("SW", "NW", "SE", "NE").index(k)]
            xs = [p[0] for p in by[(sh, h)]["pts"]]
            ys = [p[1] for p in by[(sh, h)]["pts"]]
            its.append((f"{sh}:{h}", sh, (min(xs), min(ys), max(xs), max(ys))))
        gs = SG.group_representations(its, tol=0.5)
        for g in gs:
            rows.append({"OBJECT": f"LIFT-01-COL-{k} ({chain})", "VIEWS": g["views"], "RECORDS": g["ids"],
                         "RECT_MM": [_r(v, 3) for v in g["rect"]], "PHYSICAL_OBJECTS": 1,
                         "STATE": "ONE_COLUMN_CHAIN" if len(gs) == 1 else
                         ("SECTION_CHANGES_AT_2F (S1 COL-C9-X10-Y07-2F 20 x 70)" if g["views"] == ["SFRS"]
                          else "ONE_COLUMN_CHAIN (FP to FFRS)")})
    n_shafts = sum(1 for g in shaft_groups if any(v == "FP" for v in g["views"]))
    return rows, shaft_groups, n_shafts


POPULATION = [
    # id, kind, parent, physical description, existing record(s), S8.8 decision
    ("LIFT-01", "LIFT_SHAFT", "", "one lift shaft, 1800 x 1800 inside, 200 walls, three stops (GF +1.00, 1F +5.50, "
     "2F +9.70) under the 2F roof (+13.90)", "S1 SPC-LIFT_PIT; PRE-S8 SPC-LIFT_PIT / PS8-LIFT-WALLS",
     "ONE_PHYSICAL_SHAFT"),
    ("LIFT-01-FTG", "FOOTING", "LIFT-01", "FF footing 4600 x 4500 x 550 under the four lift columns and the pit",
     f"S1 {FOOTING_ID}; S4 / S4.1 {FOOTING_OCC}", "EXISTING_ELEMENT (footing family)"),
    ("LIFT-01-PIT-BASE", "PIT_FLOOR", "LIFT-01", "the pit floor is the FF footing top; p.14 draws no separate pit "
     "slab", f"{FOOTING_ID}", "NOT_A_SEPARATE_ELEMENT"),
    ("LIFT-01-PIT-WALL-S", "PIT_WALL", "LIFT-01", "RC pit wall S between the SW and SE columns (door wall)",
     "S8.1A RG-12; PRE-S8 PS8-LIFT-WALLS", "NEW_S8_8_ELEMENT"),
    ("LIFT-01-PIT-WALL-N", "PIT_WALL", "LIFT-01", "RC pit wall N between the NW and NE columns",
     "S8.1A RG-13; PRE-S8 PS8-LIFT-WALLS", "NEW_S8_8_ELEMENT"),
    ("LIFT-01-PIT-WALL-W", "PIT_WALL", "LIFT-01", "RC pit wall W between the SW and NW columns",
     "S8.1A RG-14; PRE-S8 PS8-LIFT-WALLS", "NEW_S8_8_ELEMENT"),
    ("LIFT-01-PIT-WALL-E", "PIT_WALL", "LIFT-01", "RC pit wall E between the SE and NE columns",
     "S8.1A RG-15; PRE-S8 PS8-LIFT-WALLS", "NEW_S8_8_ELEMENT"),
    ("LIFT-01-ENCL-GF", "SHAFT_ENCLOSURE", "LIFT-01", "shaft walls GF +1.00 -> +5.50: 200 walls drawn on the "
     "architectural plan only ('AS PER PLAN' on p.14)", "S8.6 wall owner ARCHITECTURAL_BLOCKWORK",
     "NOT_STRUCTURAL_RC"),
    ("LIFT-01-ENCL-1F", "SHAFT_ENCLOSURE", "LIFT-01", "shaft walls 1F +5.50 -> +9.70 (architectural plan only)",
     "S8.6 wall owner ARCHITECTURAL_BLOCKWORK", "NOT_STRUCTURAL_RC"),
    ("LIFT-01-ENCL-2F", "SHAFT_ENCLOSURE", "LIFT-01", "shaft walls 2F +9.70 -> +13.90 (architectural plan only)",
     "S8.6 wall owner ARCHITECTURAL_BLOCKWORK", "NOT_STRUCTURAL_RC"),
    ("LIFT-01-DOOR-GF", "LANDING_DOOR", "LIFT-01", "landing door 1000 wide in the S wall at GF", "S8.6 OP-GF-023",
     "EXISTING_OPENING"),
    ("LIFT-01-DOOR-1F", "LANDING_DOOR", "LIFT-01", "landing door 1000 wide in the S wall at 1F", "S8.6 OP-1F-012",
     "EXISTING_OPENING"),
    ("LIFT-01-DOOR-2F", "LANDING_DOOR", "LIFT-01", "landing door 1000 wide in the S wall at 2F", "S8.6 OP-2F-005",
     "EXISTING_OPENING"),
    ("LIFT-01-TIE-GF", "LIFT_TIE_BEAM", "LIFT-01", "P8-N19 tie beams round the lift columns at 3.00 m in the GF "
     "storey (4.50 m floor to floor)", "S1 SPC-LIFT_TIE_BEAM-GF; S2 BM-GF-LIFT_TIE", "CONDITIONAL (not drawn)"),
    ("LIFT-01-COL-SW", "COLUMN", "LIFT-01", "C2 at the SW corner (FOUNDATION -> 2F)", COLUMNS["SW"][0],
     "EXISTING_ELEMENT (column family)"),
    ("LIFT-01-COL-NW", "COLUMN", "LIFT-01", "C1 at the NW corner (FOUNDATION -> 2F)", COLUMNS["NW"][0],
     "EXISTING_ELEMENT (column family)"),
    ("LIFT-01-COL-SE", "COLUMN", "LIFT-01", "C9 at the SE corner (FOUNDATION -> 1F; 20 x 70 at 2F)", COLUMNS["SE"][0],
     "EXISTING_ELEMENT (column family)"),
    ("LIFT-01-COL-NE", "COLUMN", "LIFT-01", "C2 at the NE corner (FOUNDATION -> 2F)", COLUMNS["NE"][0],
     "EXISTING_ELEMENT (column family)"),
    ("LIFT-01-BEAMS-GF_ROOF", "SHAFT_BEAMS", "LIFT-01", "four beams on the shaft walls at +5.50", "S6 (4 occurrences)",
     "EXISTING_ELEMENT (beam family)"),
    ("LIFT-01-BEAMS-1F_ROOF", "SHAFT_BEAMS", "LIFT-01", "four beams on the shaft walls at +9.70", "S6 (4 occurrences)",
     "EXISTING_ELEMENT (beam family)"),
    ("LIFT-01-BEAMS-2F_ROOF", "SHAFT_BEAMS", "LIFT-01", "four beams on the shaft walls at +13.90",
     "S6 (4 occurrences)", "EXISTING_ELEMENT (beam family)"),
    ("LIFT-01-GROUND-BEAMS", "GROUND_BEAMS", "LIFT-01", "two ground beams that frame into the FF footing",
     "S5 GSO-15D-7C8-1, GSO-17C-7E3-1", "EXISTING_ELEMENT (ground-beam family)"),
    ("LIFT-01-VOID-GF_ROOF", "SLAB_VOID", "LIFT-01", "the shaft void through the GF roof slab (+5.50)",
     "S1 SP-GF_ROOF_SLAB-13 OPEN_TO_BELOW", "EXISTING_RECORD"),
    ("LIFT-01-VOID-1F_ROOF", "SLAB_VOID", "LIFT-01", "the shaft void through the 1F roof slab (+9.70)",
     "S1 SP-1F_ROOF_SLAB-06 OPEN_TO_BELOW", "EXISTING_RECORD"),
    ("LIFT-01-GROUND-SLAB-OPENING", "SLAB_VOID", "LIFT-01", "the pit opening in the slab on grade",
     "S8.1A RG-04 (GBP 7BE)", "EXISTING_RECORD"),
    ("LIFT-01-ROOF", "SHAFT_ROOF", "LIFT-01", "the 2F roof slab panel over the shaft (+13.90, 160 mm)",
     "S1 SP-2F_ROOF_SLAB-03; S7", "EXISTING_ELEMENT (slab family)"),
    ("LIFT-01-OVERRUN", "OVERRUN", "LIFT-01", "lift overrun / machine room / roof upstand: none labelled or levelled "
     "on any plan, section or elevation", "-", "NOT_IN_SOURCE"),
]


# ------------------------------------------------------------------ geometry
def shaft_geometry():
    s = SG.shaft([SHAFT_IN], 200.0)
    t = {SHAFT_IN[0] - SHAFT_OUT[0], SHAFT_IN[1] - SHAFT_OUT[1], SHAFT_OUT[2] - SHAFT_IN[2],
         SHAFT_OUT[3] - SHAFT_IN[3]}
    check(all(abs(v - 200.0) < 1e-6 for v in t), "the S-BW faces are 200 apart on every side")
    check(all(abs(a - b) < 1e-9 for a, b in zip(s["outer"][0], SHAFT_OUT)), "inside face + 200 = outside face")
    w = SG.wall_pieces(SHAFT_IN, 200.0, [(k, v[2]) for k, v in COLUMNS.items()])
    door = SG.split_opening(w["pieces"], "S", *DOOR_X)
    return s, w, door


def s81a_region():
    out = {}
    for r in _rows(READ["S81A_REGION"]):
        pts = json.loads(r["POLYGON_MM"])
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        out[r["PART_ID"]] = {"kind": r["KIND"], "lane": r["LANE"], "area_m2": float(r["AREA_M2"]),
                             "bbox": (min(xs), min(ys), max(xs), max(ys)), "owner": r["OWNER"], "state": r["STATE"],
                             "polygon": pts}
    return out


LEVEL_KEYS = {"FOUNDATION": "FOUNDATION", "GF": "GF", "1F": "1F", "2F / 1F ROOF": "2F", "ROOF (2F roof)": "ROOF",
              "GROUND_BEAMS / NATURAL GROUND": "NATURAL_GROUND"}


def levels():
    out = {}
    for r in _j(READ["S1_LEVELS"])["rows"]:
        k = LEVEL_KEYS.get(r["level"])
        if k:
            out[k] = {"value_m": r.get("value_m"), "bound_m": r.get("bound_m"), "status": r["status"],
                      "source": _clean(r["source"])}
    check({"FOUNDATION", "GF", "1F", "2F", "ROOF"} <= set(out), "S1 level register carries the lift levels")
    check([out[k]["value_m"] for k in ("GF", "1F", "2F", "ROOF")] == [1.0, 5.5, 9.7, 13.9], "lift levels")
    check(out["FOUNDATION"]["status"] == "BLOCKED" and out["FOUNDATION"]["bound_m"] == {"max": -1.5},
          "founding level is a bound only")
    return out


def rules():
    rr = {r["rule_id"]: r for r in _j(READ["S1_RULES"])["rows"]}
    for k in (P8_N19_RULE, P14_RULE, P9_SOIL_RULE, P8_SLAB_RULE):
        check(k in rr, f"S1 rule {k}")
    check(rr[P8_N19_RULE]["values"] == {"beam_height_m": 3.0, "trigger_storey_height_m": 4.3}, "P8-N19 values")
    check(rr[P8_SLAB_RULE]["values"] == {"t_mm": 160}, "P8-N18 slab thickness")
    check(rr[P9_SOIL_RULE]["values"]["min_depth_m"] == 1.5, "P9 minimum excavation")
    return {k: {"page": rr[k]["page"], "status": rr[k]["status"], "priority": rr[k]["priority"],
                "english": _clean(rr[k]["english_interpretation"]), "normalized": _clean(rr[k]["normalized_rule"]),
                "values": rr[k].get("values")} for k in (P8_N19_RULE, P14_RULE, P9_SOIL_RULE, P8_SLAB_RULE)}


def depth_rows(LV, sched, s):
    f_depth = float(sched["DEPHT"]) / 100.0
    found = LV["FOUNDATION"]
    rows = [
        ("LV-01", "LOWEST_FOUNDATION_LEVEL", None, BLOCKED, "founding level <= -1.50 (minimum excavation 1.5 m "
         "below the plot level, p.9 note 1); no founding level is printed for FF", found["source"]),
        ("LV-02", "FF_FOOTING_TOP (= PIT FLOOR)", None, BLOCKED, f"founding level + {_full(f_depth)} m (schedule "
         "depth 55 cm); the founding level is not printed", "FF schedule 2B1E DEPHT 55; p.14"),
        ("LV-03", "PIT_BOTTOM", None, BLOCKED, "the pit floor is the FF top (p.14 draws no pit slab)", P14),
        ("LV-04", "PIT_WALL_TOP", None, BLOCKED, "top of the slab on grade = GF FFL +1.00 less the floor finish "
         "(not printed)", P14 + "; S1 GF FFL"),
        ("LV-05", "PIT_DEPTH", None, BLOCKED, "'As Per Lift Manufactures recommendations' (footing top to wall "
         "top)", P14),
        ("LV-06", "GF_FFL (lowest stop)", LV["GF"]["value_m"], LV["GF"]["status"], "printed", LV["GF"]["source"]),
        ("LV-07", "1F_FFL (stop)", LV["1F"]["value_m"], LV["1F"]["status"], "printed", LV["1F"]["source"]),
        ("LV-08", "2F_FFL (top stop)", LV["2F"]["value_m"], LV["2F"]["status"], "printed", LV["2F"]["source"]),
        ("LV-09", "ROOF over the shaft", LV["ROOF"]["value_m"], LV["ROOF"]["status"], "printed; the roof slab panel "
         "SP-2F_ROOF_SLAB-03 (160) covers the shaft", LV["ROOF"]["source"]),
        ("LV-10", "TRAVEL (lowest to top stop)", _r(LV["2F"]["value_m"] - LV["GF"]["value_m"]), "DERIVED",
         "2F FFL - GF FFL", "LV-06, LV-08"),
        ("LV-11", "TOP_STOREY (top stop to roof level)", _r(LV["ROOF"]["value_m"] - LV["2F"]["value_m"]),
         "DERIVED", "the headroom the manufacturer needs is not stated; no overrun is labelled", "LV-08, LV-09"),
        ("LV-12", "OVERRUN / MACHINE ROOM", None, NOT_IN_SOURCE, "none labelled or levelled", "all plans / sections"),
    ]
    out = [{"RECORD": "LEVEL", "ID": i, "WHAT": w, "VALUE": v, "STATE": st, "BASIS": b, "SOURCE": src}
           for i, w, v, st, b, src in rows]
    geo = [
        ("GE-01", "INSIDE_CLEAR_OUTLINE (pit internal area)", _m2(s["INSIDE_CLEAR_AREA"]), "m2", "ESTABLISHED",
         "S-BW FP 10EA = GBP 7BE; architectural 1800 x 1800 on GF / 1F / 2F", [_r(v, 3) for v in SHAFT_IN]),
        ("GE-02", "GROSS_OUTER_OUTLINE", _m2(s["GROSS_OUTER_AREA"]), "m2", "ESTABLISHED", "S-BW FP 10EB = GBP 7C2",
         [_r(v, 3) for v in SHAFT_OUT]),
        ("GE-03", "WALL_RING (outer - inner, corners once)", _m2(s["WALL_RING_AREA"]), "m2", "ESTABLISHED",
         "GE-02 - GE-01", ""),
        ("GE-04", "INSIDE_PERIMETER", _r(s["INSIDE_PERIMETER"] / 1000), "m", "ESTABLISHED", "4 x 1.80", ""),
        ("GE-05", "OUTER_PERIMETER", _r(s["OUTER_PERIMETER"] / 1000), "m", "ESTABLISHED", "4 x 2.20", ""),
        ("GE-06", "CENTRELINE_PERIMETER", _r(s["CENTRELINE_PERIMETER"] / 1000), "m", "ESTABLISHED",
         "4 x 2.00; x 0.20 = the ring", ""),
        ("GE-07", "WALL_THICKNESS", 200.0, "mm", "ESTABLISHED", "S-BW offsets; architectural 200 (GF 672, 1F D62 / "
         "E94, 2F 13CB / 142F / 1538); p.14 '20'", ""),
        ("GE-08", "FF_FOOTING_FOOTPRINT", _m2(SG.region_area([FOOTING])), "m2", "ESTABLISHED",
         "FP 1B2B 4600 x 4500 = schedule 460 x 450", [_r(v, 3) for v in FOOTING]),
        ("GE-09", "GROUND_SLAB_VOID (S8.1A RG-04)", None, "m2", "ESTABLISHED", "see 11 (equal to GE-01)", ""),
        ("GE-10", "PIT_VOID_VOLUME", None, "m3", "BLOCKED", "GE-01 x pit depth (LV-05 blocked)", ""),
    ]
    out += [{"RECORD": "PLAN", "ID": i, "WHAT": w, "VALUE": v, "UNIT": u, "STATE": st, "BASIS": b, "SOURCE": src}
            for i, w, v, u, st, b, src in geo]
    return out


def wall_rows(w, LV, sched):
    """pit-wall concrete: footprint per piece; heights blocked; one sensitivity reading, never released."""
    f_depth = float(sched["DEPHT"]) / 100.0
    sens_bottom = LV["FOUNDATION"]["bound_m"]["max"] + f_depth          # FF top at the minimum founding level
    sens_top = LV["GF"]["value_m"]                                       # wall top taken at FFL (no finish)
    rows = []
    for p in w["pieces"]:
        fp = p["footprint"]
        rows.append({
            "ELEMENT_ID": f"LIFT-01-PIT-WALL-{p['side']}", "SIDE": p["side"], "RECT_MM": [_r(v, 3) for v in p["rect"]],
            "LENGTH_MM": _r(p["length"], 6), "THICKNESS_MM": 200.0, "INNER_FACE_MM": _r(p["inner_face"], 6),
            "OUTER_FACE_MM": _r(p["outer_face"], 6), "FOOTPRINT_M2": _m2(fp), "BOTTOM_LEVEL": "BLOCKED (FF top)",
            "TOP_LEVEL": "BLOCKED (slab-on-grade top)", "HEIGHT_M": None,
            "CONCRETE_M3": SG.wall_volume(fp, None, None), "LANE": BLOCKED,
            "M3_PER_M_HEIGHT_CONDITIONAL": _m2(fp),
            "SENSITIVITY": f"{SENS}: wall from the FF top at the -1.50 minimum founding ({sens_bottom:+.2f}) to "
                           f"{sens_top:+.2f} -> {_full(SG.wall_volume(fp, sens_bottom, sens_top))} m3 (not a "
                           f"quantity: the depth is the manufacturer's)",
            "REASON": "plan outline, thickness and the column cut-outs are established; the pit depth (footing top "
                      "to wall top) is not printed (P14-LIFT 'As Per Lift Manufactures recommendations')"})
    other = [
        ("LIFT-01-PIT-BASE", "-", None, NOT_S8_8 + ": the FF footing top is the pit floor (OWNED_BUT_UNMEASURED by "
         "the footing family)", "p.14 draws no pit slab; a second base would double-count the footing"),
        ("LIFT-01-FTG", "-", None, NOT_S8_8 + " (footing family)", "FF 4.60 x 4.50 x 0.55 (see 04)"),
        ("LIFT-01-ENCL-GF", "-", None, "NOT_STRUCTURAL_RC", "'AS PER PLAN' above the slab on grade; 200 walls on the "
         "architectural plan only (no S-BW above the ground-beam plan)"),
        ("LIFT-01-ENCL-1F", "-", None, "NOT_STRUCTURAL_RC", "as GF"),
        ("LIFT-01-ENCL-2F", "-", None, "NOT_STRUCTURAL_RC", "as GF"),
        ("LIFT-01-TIE-GF", "-", None, BLOCKED, "section, reinforcement and the storey-height measure not stated "
         "(see 09)"),
        ("LIFT-01-OVERRUN", "-", None, NOT_IN_SOURCE, "none labelled or levelled"),
    ]
    for eid, side, m3, lane, why in other:
        rows.append({"ELEMENT_ID": eid, "SIDE": side, "CONCRETE_M3": m3, "LANE": lane, "REASON": why})
    total_sens = SG.wall_volume(w["net_footprint"], sens_bottom, sens_top)
    rows.append({"ELEMENT_ID": "LIFT-01-PIT-WALLS (all)", "SIDE": "S+N+W+E", "FOOTPRINT_M2": _m2(w["net_footprint"]),
                 "CONCRETE_M3": None, "LANE": BLOCKED, "M3_PER_M_HEIGHT_CONDITIONAL": _m2(w["net_footprint"]),
                 "SENSITIVITY": f"{SENS}: {_full(total_sens)} m3 on the reading above (never released)",
                 "REASON": "sum of the four pieces; columns cut out once"})
    return rows, total_sens


# ------------------------------------------------------------------ reinforcement
def rebar_rows(w):
    rows = []
    kg12, kg16 = kg_per_m(12), kg_per_m(16)
    drawn = {"S": "DRAWN (cut wall, door)", "N": "DRAWN (cut wall, opposite the door)", "W": "NOT_SHOWN",
             "E": "NOT_SHOWN"}
    for p in w["pieces"]:
        side, L = p["side"], p["length"]
        for face, fl in (("INNER", p["inner_face"]), ("OUTER", p["outer_face"])):
            n = SG.rate_count(6, fl)
            rows.append({"ELEMENT_ID": f"LIFT-01-PIT-WALL-{side}", "CALLOUT": "P14-R02 6Ø16/m", "ROLE": "WALL_VERTICAL",
                         "BAR_DIAMETER_MM": 16, "FACE": face, "APPLICABILITY": drawn[side],
                         "DISTRIBUTION_LENGTH_MM": _r(fl, 6), "DISTRIBUTION_STATE": "ESTABLISHED (face between the "
                         "columns)", "COUNT_ALONG_FACE": n, "BAR_LENGTH_STATE": "BLOCKED (footing bottom layer to "
                         "the wall top: needs the founding level and the pit depth)", "KG": 0.0,
                         "KG_PER_M_BAR_LENGTH_CONDITIONAL": _r(n * kg16), "QUANTITY_STATE": BLOCKED,
                         "FORMULA": f"count = ceil(6 x {_full(fl / 1000)}) = {n}; kg = count x bar length x "
                                    f"{_full(kg16)}"})
            rows.append({"ELEMENT_ID": f"LIFT-01-PIT-WALL-{side}", "CALLOUT": "P14-R01 6Ø12/m",
                         "ROLE": "WALL_HORIZONTAL", "BAR_DIAMETER_MM": 12, "FACE": face, "APPLICABILITY": drawn[side],
                         "DISTRIBUTION_LENGTH_MM": None, "DISTRIBUTION_STATE": "BLOCKED (wall height)",
                         "COUNT_ALONG_FACE": None, "BAR_LENGTH_STATE": f"straight run {_full(fl)} mm between the "
                         "columns; the joint at the corner columns (through, stop, wrap, lap) is not shown",
                         "KG": 0.0, "KG_PER_M_WALL_HEIGHT_CONDITIONAL": _r(6 * fl / 1000 * kg12),
                         "QUANTITY_STATE": BLOCKED,
                         "FORMULA": f"kg = ceil(6 x height) x {_full(fl / 1000)} x {_full(kg12)} (+ joints)"})
        for cid, role, d in (("P14-R03 2 Ø16", "WALL_BASE_TOP", 16), ("P14-R04 2 Ø16", "WALL_BASE_BOTTOM", 16),
                             ("P14-R05 2Ø12", "WALL_TOP", 12)):
            rows.append({"ELEMENT_ID": f"LIFT-01-PIT-WALL-{side}", "CALLOUT": cid, "ROLE": role, "BAR_DIAMETER_MM": d,
                         "FACE": "IN THE WALL CAGE", "APPLICABILITY": drawn[side], "DISTRIBUTION_LENGTH_MM": None,
                         "DISTRIBUTION_STATE": "-", "COUNT_ALONG_FACE": 2, "BAR_LENGTH_STATE": f"along the wall: not "
                         f"shown (net piece {_full(L)} mm; outside face of the wall line 2200 mm; ends at the "
                         "columns not shown)", "KG": 0.0, "KG_PER_M_BAR_LENGTH_CONDITIONAL": _r(2 * kg_per_m(d)),
                         "QUANTITY_STATE": BLOCKED, "FORMULA": f"kg = 2 x length x {_full(kg_per_m(d))}"})
    rows.append({"ELEMENT_ID": "LIFT-01 (all walls)", "CALLOUT": "anchorage / bends / laps", "ROLE":
                 "ANCHORAGE_AND_CONTINUATION", "BAR_DIAMETER_MM": None, "FACE": "-", "APPLICABILITY": "-",
                 "KG": 0.0, "QUANTITY_STATE": BLOCKED, "FORMULA": "-",
                 "BAR_LENGTH_STATE": "vertical bars: foot not bent on p.14, U over the top; horizontal bars: corner "
                                     "and column joints not shown; laps not dimensioned"})
    rows.append({"ELEMENT_ID": "LIFT-01-TIE-GF", "CALLOUT": "P8-N19", "ROLE": "TIE_BEAM_BARS", "KG": 0.0,
                 "QUANTITY_STATE": BLOCKED, "BAR_LENGTH_STATE": "no section and no bars stated", "FORMULA": "-"})
    return rows


def callout_rows():
    keys = ("CALLOUT_ID", "AS_PRINTED", "WHERE_DRAWN", "BAR_DIRECTION", "ROLE", "WALLS_DRAWN", "FACE",
            "SPACING_OR_COUNT", "EXTENT", "ANCHORAGE_BENDS_LAPS", "OWNER", "STATE")
    out = [dict(zip(keys, c)) for c in P14_CALLOUTS]
    for r in out:
        r["SOURCE"] = P14
        r["SECTION"] = P14_SECTION
    return out


# ------------------------------------------------------------------ tie beam
BEAM_DEPTH_OVER_DOOR = {}   # filled from the S8.6 binding (frozen): the beam over each landing opening


def tie_rows(LV, w, RU, s86_binding):
    lv = [LV["GF"]["value_m"], LV["1F"]["value_m"], LV["2F"]["value_m"], LV["ROOF"]["value_m"]]
    thr, off = RU[P8_N19_RULE]["values"]["trigger_storey_height_m"], RU[P8_N19_RULE]["values"]["beam_height_m"]
    slab = RU[P8_SLAB_RULE]["values"]["t_mm"] / 1000.0
    ff = SG.tie_beam_trigger(lv, thr, off, SG.FLOOR_TO_FLOOR)
    cs = SG.tie_beam_trigger(lv, thr, off, SG.CLEAR_TO_SLAB_SOFFIT, slab=slab, finish=None)
    depth = {b["FLOOR"]: float(b["BEAM_DEPTH_MM"]) / 1000.0 for b in s86_binding}
    names = {1.0: "GF", 5.5: "1F", 9.7: "2F"}
    rows = []
    for a, b in zip(ff, cs):
        fl = names[a["lower"]]
        d = depth[fl]
        beam_clear_upper = a["height"] - d                      # any finish only lowers it
        beam_state = SG.TRIGGERED if beam_clear_upper > thr + 1e-9 else SG.NOT_TRIGGERED
        finish_switch = a["height"] - slab - thr                # finish below which the slab-soffit measure triggers
        if a["state"] == SG.NOT_TRIGGERED:
            req = "NOT_REQUIRED (no measure gives a storey higher than 4.30 m: every other measure is smaller)"
        else:
            req = "NOT_ESTABLISHED (triggered only under floor-to-floor; the note does not define its storey height)"
        rows.append({"STOREY": fl, "LOWER_FFL_M": a["lower"], "UPPER_FFL_M": a["upper"],
                     "FLOOR_TO_FLOOR_M": _r(a["height"]), "TRIGGER_FLOOR_TO_FLOOR": a["state"],
                     "TRIGGER_CLEAR_TO_SLAB_SOFFIT": b["state"] if a["state"] == SG.TRIGGERED else SG.NOT_TRIGGERED,
                     "CLEAR_TO_SLAB_SOFFIT_NOTE": f"{_full(a['height'])} - {_full(slab)} (P8-N18 slab) - finish; > 4.30 "
                                                  f"only if the finish is under {_full(finish_switch * 1000)} mm"
                     if a["state"] == SG.TRIGGERED else "smaller than floor to floor",
                     "TRIGGER_CLEAR_TO_BEAM_SOFFIT": beam_state,
                     "CLEAR_TO_BEAM_SOFFIT_NOTE": f"at most {_full(beam_clear_upper)} m under the {_full(d * 1000)} mm "
                                                  "beam over the landing door (S8.6 binding)",
                     "REQUIREMENT": req,
                     "ELEVATION_IF_REQUIRED_M": a["elevation"],
                     "ELEVATION_DATUM": "storey FFL + 3.00 (the note's 'at 3.00 m height'; datum not stated)"
                     if a["state"] == SG.TRIGGERED else "-",
                     "EXISTING_BEAM_AT_ELEVATION": "none (S6 beams round the shaft are at +5.50 / +9.70 / +13.90)"
                     if a["state"] == SG.TRIGGERED else "-",
                     "PLAN_PATH": "the four column-to-column spans S / N / W / E: "
                                  + " / ".join(f"{p['side']} {_full(p['length'] / 1000)} m" for p in w["pieces"])
                                  + f" = {_full(sum(p['length'] for p in w['pieces']) / 1000)} m"
                     if a["state"] == SG.TRIGGERED else "-",
                     "SECTION": "NOT_STATED" if a["state"] == SG.TRIGGERED else "-",
                     "REINFORCEMENT": "NOT_STATED" if a["state"] == SG.TRIGGERED else "-",
                     "S1_S2_RECORD": "S1 SPC-LIFT_TIE_BEAM-GF (COUNTED_BLOCKED); S2 BM-GF-LIFT_TIE (BLOCKED)"
                     if fl == "GF" else "none",
                     "OWNER": "S8.8" if a["state"] == SG.TRIGGERED else "-",
                     "QUANTITY_STATE": BLOCKED if a["state"] == SG.TRIGGERED else "NOT_A_COMPONENT",
                     "CONCRETE_M3": None, "KG": 0.0})
    rows.append({"STOREY": "FOUNDATION (footing to GF)", "REQUIREMENT": "NOT_ESTABLISHED (no printed founding level; "
                 "the pit walls are RC in this storey)", "QUANTITY_STATE": "NOT_A_COMPONENT", "KG": 0.0})
    return rows, ff


# ------------------------------------------------------------------ existing owners
def s6_shaft_beams(src):
    from shapely.geometry import box
    ring = box(*SHAFT_OUT).difference(box(*SHAFT_IN))
    bands = beam_bands(src, ("GFRS", "FFRS", "SFRS"))
    lines = {k: v for k, v in bands.items() if v.intersection(ring).area > 0.1e6}
    out = []
    for o in _rows(READ["S6_OCC"]):
        for g in json.loads(o["geometry_objects"] or "[]"):
            m = re.fullmatch(r"SPAN:(\w+):(BL\d+):(\d+)-(\d+)", g)
            if not m or (m.group(1), m.group(2)) not in lines:
                continue
            P = lines[(m.group(1), m.group(2))]
            x0, y0, x1, y1 = P.bounds
            lo, hi = float(m.group(3)), float(m.group(4))
            along_y = (y1 - y0) > (x1 - x0)
            ext = (SHAFT_OUT[1], SHAFT_OUT[3]) if along_y else (SHAFT_OUT[0], SHAFT_OUT[2])
            if lo >= ext[0] - 150 and hi <= ext[1] + 150 and o["occurrence_id"].startswith("BM-"):
                out.append({"occurrence_id": o["occurrence_id"], "mark": o["mark"], "sheet": m.group(1),
                            "line": m.group(2), "span": g, "state": o["occurrence_state"],
                            "known_kg": float(o["known_kg"] or 0.0)})
    return sorted(out, key=lambda r: (r["sheet"], r["occurrence_id"])), lines


def owners(src, s, w):
    from shapely.geometry import Polygon, box
    S4o = [r for r in _rows(READ["S4_OCC"]) if r["occurrence_id"] == FOOTING_OCC]
    check(len(S4o) == 1, "S4 FOCC-1B2B")
    S4c = [r for r in _rows(READ["S4_COMP"]) if r["occurrence_id"] == FOOTING_OCC]
    T01 = [r for r in _rows(READ["S41_TRANSFERS"]) if r["OCCURRENCE_ID"] == FOOTING_OCC]
    check(len(T01) == 1 and T01[0]["TRANSFER_ID"] == "S4.1-T01" and T01[0]["TARGET_STAGE"] == "S8",
          "S4.1-T01 hands the p.14 '2 Ø16' to S8")
    U41 = [r for r in _rows(READ["S41_UNRESOLVED"]) if FOOTING_OCC in r["BASELINE_COMPONENT_ID"]]
    st = [r for r in _j(READ["S31_STARTERS"])["rows"] if (r.get("footing") or {}).get("ref") == FOOTING_ID
          and r.get("component") == "STARTER"]
    check(len(st) == 4 and {r["chain_id"] for r in st} == {v[0] for v in COLUMNS.values()},
          "S3.1 starters of the four lift columns into FF")
    gb = [r for r in _rows(READ["S5_OCC"]) if FOOTING_OCC in (r["start_node"] + r["end_node"])]
    check(len(gb) == 2, "two S5 ground beams frame into FF")
    s6, lines = s6_shaft_beams(src)
    check(len(s6) == 12 and Counter(r["sheet"] for r in s6) == {"GFRS": 4, "FFRS": 4, "SFRS": 4},
          "S6: four beams on the shaft walls per roof level")
    s7 = [r for r in _rows(READ["S7_PANELS"]) if r["PANEL_ID"] == "SP-2F_ROOF_SLAB-03"]
    check(len(s7) == 1, "S7 panel over the shaft")
    s2 = [c for c in _j(READ["S2_RELEASE"])["components"]
          if c["element_id"] in (FOOTING_ID, "BM-GF-LIFT_TIE", "SP-2F_ROOF_SLAB-03")]
    flags = [f for f in _j(READ["S3_FLAGS"])["flags"] if f.get("flag_id") == "STR-COL-013"]
    check(len(flags) == 1 and "COL-C2-X09-Y07-FOUNDATION" in flags[0]["element_ids"], "S3 flag STR-COL-013")
    cols = {r["column_id"]: r for r in _j(READ["S1_COLUMNS"])["rows"] if r["chain_id"] in
            {v[0] for v in COLUMNS.values()}}
    ftg = [r for r in _j(READ["S1_FOOTINGS"])["rows"] if r["footing_id"] == FOOTING_ID]
    fdef = [r for r in _j(READ["S1_FOOTING_DEFS"])["rows"] if r["footing_type"] == "FF"]
    check(len(ftg) == 1 and len(fdef) == 1, "S1 FF occurrence and definition")
    spec = [r for r in _j(READ["S1_SPECIAL"])["rows"] if r["special_id"] in ("SPC-LIFT_PIT", "SPC-LIFT_TIE_BEAM-GF")]
    check(len(spec) == 2, "S1 lift special occurrences")
    slabs = [x for x in _j(READ["S1_SLABS"])["rows"]
             if Polygon(x["polygon_mm"]).intersection(box(*SHAFT_OUT)).area > 1e4]
    s86 = [r for r in _rows(READ["S86_CENSUS"]) if r["TYPE"] == "6_SERVICE_SHAFT_OPENING"]
    s86b = [r for r in _rows(READ["S86_BINDING"]) if r["TYPE"] == "6_SERVICE_SHAFT_OPENING"]
    check(len(s86) == 3 and len(s86b) == 3, "S8.6: three lift landing openings")
    s87 = _rows(READ["S87_GEOMETRY"])
    q81a = [r for r in _rows(READ["S81A_QUESTIONS"]) if r["KIND"] == "LIFT_PIT"]
    return {"S4o": S4o[0], "S4c": S4c, "T01": T01[0], "U41": U41, "starters": st, "gb": gb, "s6": s6,
            "s6_lines": lines, "s7": s7[0], "s2": s2, "flag": flags[0], "cols": cols, "ftg": ftg[0], "fdef": fdef[0],
            "spec": spec, "slabs": slabs, "s86": s86, "s86b": s86b, "s87": s87, "q81a": q81a}


def foundation_rows(O, sched, w):
    f = O["ftg"]
    d = O["fdef"]
    vol = SG.region_area([FOOTING]) / 1e6 * float(sched["DEPHT"]) / 100.0
    on = SG.plan_overlap(w["pieces"], [FOOTING])
    rows = [
        {"ITEM": "FF identity", "VALUE": "FF (lift base)", "EVIDENCE": "FP tag 1676 'FF' inside the shaft; schedule "
         "row 2B1E FO-TY 'FF'; remark 1C64 (legacy-encoded Arabic, decoded by PRE-S8 as 'lift base'; not reproduced)",
         "STATE": "ESTABLISHED"},
        {"ITEM": "schedule size (2B1E W / H / DEPHT)", "VALUE": f"{sched['W']} x {sched['H']} x {sched['DEPHT']} cm",
         "EVIDENCE": "ST7757.dxf FTB insert 2B1E (p.9)", "STATE": "PRINTED"},
        {"ITEM": "drawn outline (FP 1B2B)", "VALUE": f"{_full(FOOTING[2] - FOOTING[0])} x "
         f"{_full(FOOTING[3] - FOOTING[1])} mm", "EVIDENCE": "S-FOOTINGS LWPOLYLINE 1B2B",
         "STATE": "MATCH" if f["sizes"]["match"] else "MISMATCH"},
        {"ITEM": "S1 definition", "VALUE": f"{d['L_cm']} x {d['W_cm']} x {d['D_cm']} cm; "
         + "; ".join(f"{c['component']} {c['count']}Ø{c['dia_mm']}/m" for c in d["components"]),
         "EVIDENCE": "S1 FDEF-FF", "STATE": d["definition_id"]},
        {"ITEM": "PRE-S8 figure 460 x 450 x 55", "VALUE": "verified", "EVIDENCE": "schedule = drawn = S1",
         "STATE": "VERIFIED"},
        {"ITEM": "footing concrete", "VALUE": f"{_full(vol)} m3 (4.60 x 4.50 x 0.55)", "EVIDENCE": "outline + schedule "
         "depth (both have authority)", "STATE": "OWNED_BUT_UNMEASURED (footing family: S1 / S2 count it, no frozen "
         "stage holds its m3); not released by S8.8"},
        {"ITEM": "footing bars (four mats)", "VALUE": f"{O['S4o']['known_kg']} kg Ø14 ({O['S4o']['release_state']})",
         "EVIDENCE": "S4 FOCC-1B2B; " + "; ".join(f"{c['component']} {c['state']} {c['kg']}" for c in O["S4c"]
                                                   if c["kg"]),
         "STATE": "ALREADY_OWNED_AND_MEASURED (S4 lower bound; S4.1 end treatments blocked)"},
        {"ITEM": "p.14 '2 Ø16' at the wall base", "VALUE": "0 kg", "EVIDENCE": f"{O['T01']['TRANSFER_ID']}: "
         f"{O['T01']['FACTS_FOUND']}; still missing: {O['T01']['STILL_MISSING']}",
         "STATE": "TRANSFERRED_TO_S8_8 -> BLOCKED_UNQUANTIFIED (see 08)"},
        {"ITEM": "column starters into FF", "VALUE": f"{_full(math.fsum(r['kg'] for r in O['starters']))} kg Ø16 "
         f"({len(O['starters'])} columns)", "EVIDENCE": "S3.1 " + "; ".join(f"{r['occurrence_id']} {r['count']}Ø"
                                                                            f"{r['dia_mm']} {r['kg']}"
                                                                            for r in O["starters"]),
         "STATE": "ALREADY_OWNED_AND_MEASURED (S3.1, " + ", ".join(sorted({r["basis_state"] for r in O["starters"]}))
                  + ")"},
        {"ITEM": "ground beams framing into FF", "VALUE": ", ".join(r["occurrence_id"] for r in O["gb"]),
         "EVIDENCE": "; ".join(f"{r['occurrence_id']} {r['occurrence_state']} {r['known_kg']} kg" for r in O["gb"]),
         "STATE": "ALREADY_OWNED_AND_MEASURED (S5 lower bound)"},
        {"ITEM": "pit floor", "VALUE": "the FF top", "EVIDENCE": P14 + ": the walls stand on the footing; no pit slab",
         "STATE": "NOT_A_SEPARATE_ELEMENT"},
        {"ITEM": "pit walls on the footing", "VALUE": f"{_full(on['on'] / 1e6)} m2 on, {_full(on['off'] / 1e6)} m2 off",
         "EVIDENCE": "plan overlap of the net wall pieces with 1B2B", "STATE": "ALL_ON_FOOTING (walls start at its top: "
                                                                              "no shared volume)"},
        {"ITEM": "shaft position on the footing", "VALUE": f"margins W {_full(SHAFT_OUT[0] - FOOTING[0])}, E "
         f"{_full(FOOTING[2] - SHAFT_OUT[2])}, S {_full(SHAFT_OUT[1] - FOOTING[1])}, N "
         f"{_full(FOOTING[3] - SHAFT_OUT[3])} mm", "EVIDENCE": "10EB inside 1B2B", "STATE": "ESTABLISHED"},
        {"ITEM": "founding level", "VALUE": "not printed (<= -1.50 minimum)", "EVIDENCE": "p.9 note 1 (S1 P9-SOIL); "
         "S1 level register", "STATE": BLOCKED},
        {"ITEM": "lower ground beam (P13-FOOTING-DEEP)", "VALUE": "-", "EVIDENCE": "S2 FTG-FF LOWER_GROUND_BEAM "
         + "; ".join(c["release_state"] for c in O["s2"] if c["element_id"] == FOOTING_ID
                     and c["component"] == "LOWER_GROUND_BEAM"), "STATE": "BLOCKED (footing family; not S8.8)"},
    ]
    return rows, vol


def ownership_rows(O, w, vol):
    def st(**k):
        return SG.ownership_state(**k)
    s6kg = {sh: math.fsum(r["known_kg"] for r in O["s6"] if r["sheet"] == sh) for sh in ("GFRS", "FFRS", "SFRS")}
    rows = [
        ("LIFT-01-FTG", "concrete", "footing family (S1 / S2)", st(owner="S1/S2", measured=False),
         f"{_full(vol)} m3 computable, unmeasured"),
        ("LIFT-01-FTG", "bars (four mats)", "S4 / S4.1", st(owner="S4", measured=True),
         f"{O['S4o']['known_kg']} kg Ø14 lower bound"),
        ("LIFT-01-FTG", "'2 Ø16' wall-base bars", "S8.8 (S4.1-T01)", st(blocked="length / walls"), "0 kg"),
        ("LIFT-01-PIT-BASE", "concrete", "footing family (the FF top is the pit floor)",
         st(owner="S1/S2", measured=False), "no separate element"),
        ("LIFT-01-PIT-WALL-S/N/W/E", "concrete", "S8.8", st(blocked="pit depth"),
         f"{_full(w['net_footprint'] / 1e6)} m2 footprint; height blocked"),
        ("LIFT-01-PIT-WALL-S/N/W/E", "6Ø16/m vertical", "S8.8", st(blocked="bar length"), "0 kg"),
        ("LIFT-01-PIT-WALL-S/N/W/E", "6Ø12/m horizontal", "S8.8", st(blocked="wall height"), "0 kg"),
        ("LIFT-01-PIT-WALL-S/N/W/E", "2Ø12 wall top", "S8.8", st(blocked="length"), "0 kg"),
        ("LIFT-01-PIT-WALL ring vs columns", "plan", "S8.8 / column family",
         st(conflict="foundation-storey column width"), "drawn 200 (flush) vs schedule 300 (S3 STR-COL-013)"),
        ("LIFT-01-GROUND-SLAB-OPENING", "area", "S8.1A (RG-04 excluded from the ground slab)",
         st(owner="S8.1A", measured=True), "3.24 m2 excluded"),
        ("LIFT-01-ENCL-GF/1F/2F", "walls", "architectural blockwork (S8.6 wall owner)",
         st(owner="architectural", measured=False), "not structural"),
        ("LIFT-01-DOOR-GF/1F/2F", "openings + lintels", "S8.6", st(owner="S8.6", measured=False),
         "lintels BLOCKED_SUPPORT_IDENTITY in S8.6"),
        ("LIFT-01-TIE-GF", "concrete + bars", "S8.8 (S1 SPC-LIFT_TIE_BEAM-GF, S2 BM-GF-LIFT_TIE)",
         st(blocked="section / measure"), "not drawn; section not stated"),
        ("LIFT-01-COL-SW/NW/SE/NE", "bars", "S3 / S3.1", st(owner="S3", measured=True), "column family"),
        ("LIFT-01-COL-SW/NW/SE/NE", "concrete", "column family", st(owner="S3", measured=False), "column family"),
        ("LIFT-01-COL-SW/NW/SE/NE", "starters into FF", "S3.1", st(owner="S3.1", measured=True),
         f"{_full(math.fsum(r['kg'] for r in O['starters']))} kg"),
        ("LIFT-01-BEAMS-GF_ROOF", "bars", "S6", st(owner="S6", measured=True), f"{_full(s6kg['GFRS'])} kg lower bound"),
        ("LIFT-01-BEAMS-1F_ROOF", "bars", "S6", st(owner="S6", measured=True), f"{_full(s6kg['FFRS'])} kg lower bound"),
        ("LIFT-01-BEAMS-2F_ROOF", "bars", "S6", st(owner="S6", measured=True), f"{_full(s6kg['SFRS'])} kg lower bound"),
        ("LIFT-01-BEAMS-*", "concrete", "beam family", st(owner="S2", measured=False), "no frozen m3"),
        ("LIFT-01-GROUND-BEAMS", "bars", "S5", st(owner="S5", measured=True),
         f"{_full(math.fsum(float(r['known_kg']) for r in O['gb']))} kg lower bound"),
        ("LIFT-01-VOID-GF_ROOF / 1F_ROOF", "void", "S1 (OPEN_TO_BELOW, no slab concrete; S7 places no bars)",
         st(owner="S1", measured=True), "3.24 m2 each"),
        ("LIFT-01-ROOF", "bars", "S7", st(owner="S7", measured=True), f"{O['s7']['PANEL_OWNED_KG']} kg panel-owned"),
        ("LIFT-01-ROOF", "concrete", "slab family (S1 160 mm, S2 3.24 m2 plan)", st(owner="S2", measured=False),
         "no frozen m3"),
        ("LIFT-01-OVERRUN", "-", "-", st(blocked="not in source"), "none documented"),
    ]
    return [{"COMPONENT": a, "PART": b, "OWNER": c, "STATE": d, "QUANTITY_RECORD": e} for a, b, c, d, e in rows]


# ------------------------------------------------------------------ openings and overlaps
def opening_rows(O, door, A):
    out = []
    by_fl = {r["FLOOR"]: r for r in O["s86"]}
    bind = {r["FLOOR"]: r for r in O["s86b"]}
    for fl, oid in (("GF", "OP-GF-023"), ("1F", "OP-1F-012"), ("2F", "OP-2F-005")):
        c = by_fl[fl]
        check(c["OPENING_ID"] == oid, f"S8.6 {oid}")
        jambs = [r for r in A[fl] if r["what"].startswith("door jamb")]
        x = sorted(r["a"][0] for r in jambs)
        out.append({"ELEMENT_ID": f"LIFT-01-DOOR-{fl}", "S8_6_OPENING": oid, "FLOOR": fl, "FFL_M": c["FFL_M"],
                    "WALL_SIDE": "S", "JAMB_HANDLES": [r["handle"] for r in jambs], "JAMB_X_MM": x,
                    "WIDTH_ARCH_MM": _r(x[1] - x[0], 6), "WIDTH_S8_6_MM": c["WIDTH_MM"],
                    "WIDTH_IN_WALL_LINE_MM": _r(door["width_in_wall"], 6),
                    "DISTANCE_TO_INNER_CORNERS_MM": [_r(x[0] - SHAFT_IN[0], 6), _r(SHAFT_IN[2] - x[1], 6)],
                    "WALL_OWNER": c["WALL_OWNER"], "RC_WALL_DEDUCTION_M3": 0.0,
                    "WHY_NO_RC_DEDUCTION": "the door is in the shaft enclosure above the slab on grade (blockwork, "
                                           "'AS PER PLAN'); the RC pit wall below has no door (p.14)",
                    "LINTEL": f"S8.6 {bind[fl]['SCHEDULE_ROW']} {bind[fl]['SECTION']}: {bind[fl]['DECISION']} "
                              f"({bind[fl]['LANE']})", "BEAM_OVER_DOOR_DEPTH_MM": bind[fl]["BEAM_DEPTH_MM"],
                    "HEIGHT": c["HEIGHT_STATE"], "STATE": "RECONCILED (S8.6 opening = architectural jambs)"})
    out.append({"ELEMENT_ID": "LIFT-01-PIT-WALL-S", "S8_6_OPENING": "-", "FLOOR": "pit", "WALL_SIDE": "S",
                "WIDTH_IN_WALL_LINE_MM": 0.0, "RC_WALL_DEDUCTION_M3": 0.0,
                "WHY_NO_RC_DEDUCTION": "p.14: the door wall is solid to the slab-on-grade top; its top bars 2Ø12 sit "
                                       "under the GF door", "STATE": "NO_OPENING"})
    return out


def overlap_rows(O, w, src):
    from shapely.geometry import box
    from shapely.ops import unary_union
    pieces = unary_union([box(*p["rect"]) for p in w["pieces"]])
    rows = []

    def A(cid, what, a_m2, ok, detail=""):
        rows.append({"CHECK_ID": cid, "CHECK": what, "OVERLAP_M2": _r(a_m2), "RESULT": "PASS" if ok else "FAIL",
                     "DETAIL": detail})
    cols = unary_union([box(*v[2]) for v in COLUMNS.values()])
    A("OV-01", "net pit-wall pieces vs the four lift columns", pieces.intersection(cols).area / 1e6,
      pieces.intersection(cols).area < 1.0, f"columns take {_full(sum(w['member_overlap'].values()) / 1e6)} m2 "
                                            "of the ring once")
    gb = beam_bands(src, ("GBP",))
    hits = {k[1]: P.intersection(pieces).area / 1e6 for k, P in gb.items() if P.intersection(pieces).area > 0}
    A("OV-02", "net pit-wall pieces vs S5 ground-beam bands (GBP)", sum(hits.values()),
      sum(hits.values()) < OVERLAP_TOL_M2, json.dumps({k: _r(v) for k, v in hits.items()}))
    ring_hits = {k[1]: _r(P.intersection(box(*SHAFT_OUT).difference(box(*SHAFT_IN))).area / 1e6)
                 for k, P in gb.items() if P.intersection(box(*SHAFT_OUT)).area > 0}
    A("OV-03", "ground-beam bands that reach the ring do so inside a column", 0.0,
      all(gb[("GBP", k)].intersection(box(*SHAFT_OUT).difference(box(*SHAFT_IN))).difference(cols).area < 100.0
          for k in ring_hits), json.dumps(ring_hits))
    A("OV-04", "pit walls vs the FF footing: plan inside, volume shared none (walls start at the footing top)", 0.0,
      SG.plan_overlap(w["pieces"], [FOOTING])["off"] == 0.0, "")
    s87 = []
    for r in O["s87"]:
        b = json.loads(r["PLAN_POLYGON_BBOX_MM"])
        a = box(*b).intersection(box(*SHAFT_OUT)).area / 1e6
        if a > 0:
            s87.append((r["ELEMENT_ID"], _r(a)))
    A("OV-05", "S8.7 stair elements vs the shaft outline (shared core)", sum(a for _, a in s87), not s87,
      "ST-A bay east edge x 19587.904 = the shaft outside face W: touch only")
    region = s81a_region()
    ring_parts = ["S8.1A-RG-12", "S8.1A-RG-13", "S8.1A-RG-14", "S8.1A-RG-15"]
    same = all(any(max(abs(a - b) for a, b in zip(region[k]["bbox"], p["rect"])) < 0.01 for p in w["pieces"])
               for k in ring_parts)
    A("OV-06", "S8.1A pit-wall cells RG-12..15 = the four net pieces (ground slab excludes them once)", 0.0, same,
      json.dumps({k: region[k]["area_m2"] for k in ring_parts}))
    A("OV-07", "S8.1A RG-04 = the pit internal area (the ground-slab opening is the shaft void, not the footing)",
      0.0, max(abs(a - b) for a, b in zip(region["S8.1A-RG-04"]["bbox"], SHAFT_IN)) < 0.01 and
      abs(region["S8.1A-RG-04"]["area_m2"] - 3.24) < 1e-6, f"RG-04 {region['S8.1A-RG-04']['area_m2']} m2")
    slabs_in = [(x["sheet"], x["panel_id"], x["class"]) for x in O["slabs"]
                if x["class"] == "SLAB_PANEL" and x["sheet"] in ("GFRS", "FFRS")]
    A("OV-08", "no S1 / S7 slab panel spans the shaft at +5.50 or +9.70", 0.0, not slabs_in, json.dumps(slabs_in))
    A("OV-09", "S6 beams on the shaft walls sit at +5.50 / +9.70 / +13.90; nothing in the pit and nothing at +4.00",
      0.0, {r["sheet"] for r in O["s6"]} == {"GFRS", "FFRS", "SFRS"}, f"{len(O['s6'])} occurrences")
    A("OV-10", "p.14 footing mats stay with S4; S8.8 adds no base mesh (PRE-S8 'LIFT WALL -> PIT BASE')", 0.0, True,
      "no pit slab, no second footing")
    A("OV-11", "S3.1 starters (Ø16 column bars) and the 6Ø16/m wall verticals are different bars", 0.0, True,
      "starters are inside the columns; the wall pieces exclude the columns")
    return rows, s87


# ------------------------------------------------------------------ registers
QUESTIONS = {
    "Q-LIFT-01": ("lift manufacturer / engineer", "Pit depth (footing top to the slab-on-grade top) and the lift "
                  "model: p.14 gives 'As Per Lift Manufactures recommendations'.", "all pit-wall concrete and bars"),
    "Q-LIFT-02": ("engineer", "Founding level of FF (and so its top = the pit floor). p.9 note 1 only gives a 1.5 m "
                  "minimum excavation; with the 55 cm footing the pit floor would be at or below -0.95, at least "
                  "1.95 m under the GF floor. Does that match the manufacturer's pit, or is a raised pit floor "
                  "intended?", "pit floor, wall height"),
    "Q-LIFT-03": ("engineer", "Top of the pit walls: the slab-on-grade top (FFL +1.00 less the floor finish). What is "
                  "the finish thickness?", "wall top, wall height"),
    "Q-LIFT-04": ("engineer", "Are 6Ø12/m and 6Ø16/m per face (both faces drawn) and do they apply to the W and E "
                  "walls that the p.14 section does not cut?", "wall bars"),
    "Q-LIFT-05": ("engineer", "Vertical 6Ø16/m: anchorage at the foot (p.14 shows no bend at the footing bottom "
                  "layer), the U over the wall top, and laps.", "vertical bar length"),
    "Q-LIFT-06": ("engineer", "Horizontal 6Ø12/m at the corner columns: through the column, stopped at its face, "
                  "or lapped round the corner?", "horizontal bar length"),
    "Q-LIFT-07": ("engineer", "'2 Ø16' top and bottom in the footing under each wall, and '2Ø12' at the wall top: "
                  "length along the wall, end anchorage, and whether all four walls carry them (S4.1-T01, S4-Q1).",
                  "wall-base / wall-top bars"),
    "Q-LIFT-08": ("engineer", "Foundation-storey lift columns: the plans draw 200 x 500 (C2 / C1) and 250 x 1000 "
                  "(C9) flush with the 200 pit walls; the column schedule gives 300 wide (S3 used the schedule, "
                  "STR-COL-013). Which is right, and does the wider column project into the pit?",
                  "pit-wall footprint, pit clear size"),
    "Q-LIFT-09": ("engineer", "P8-N19: which storey height is meant (floor to floor, clear to slab soffit, clear to "
                  "beam soffit)? GF is 4.50 m floor to floor but at most 3.75 m clear under the 750 mm beams.",
                  "whether the GF tie beam exists"),
    "Q-LIFT-10": ("engineer", "If the GF tie beams are required: section, reinforcement, the 3.00 m datum (FFL or "
                  "structural floor), and whether they run on all four sides or only between the columns; how they "
                  "meet the landing-door lintel L1 on the S side.", "tie-beam concrete and bars"),
    "Q-LIFT-11": ("architect / engineer", "The shaft enclosure above GF is 200 walls on the architectural plans only "
                  "('AS PER PLAN'): confirm blockwork (not RC) on all three storeys.", "shaft walls above the pit"),
    "Q-LIFT-12": ("lift manufacturer / architect", "Top-floor headroom (2F +9.70 to the roof +13.90) and any "
                  "overrun, machine room or roof upstand: none is labelled.", "lift roof / overrun"),
    "Q-LIFT-13": ("engineer", "Pit drainage, sump or waterproofing details (p.14 shows a membrane and protection "
                  "board only).", "non-structural; recorded"),
}


PRE_S8_INTERFACE_RESOLUTION = {
    "LIFT WALL -> PIT BASE": "no pit slab: the FF mats stay S4's and S8.8 adds no base mesh (OV-10)",
    "WALL -> FOUNDATION": "the lift-wall starters are the 6Ø16/m verticals run into the footing: owned by S8.8, "
                          "BLOCKED (bar length)",
}


def blocked_rows(O, pres_census, pre_if=(), pre_ex=()):
    rows = [
        ("B-01", "PIT_DEPTH", BLOCKED, "As Per Lift Manufactures recommendations", "Q-LIFT-01"),
        ("B-02", "PIT_FLOOR / FF TOP LEVEL", BLOCKED, "founding level not printed (<= -1.50)", "Q-LIFT-02"),
        ("B-03", "PIT_WALL_TOP", BLOCKED, "floor finish not printed", "Q-LIFT-03"),
        ("B-04", "PIT_WALL_CONCRETE (S, N, W, E)", BLOCKED, "height = B-01", "Q-LIFT-01"),
        ("B-05", "6Ø16/m VERTICAL", BLOCKED, "bar length; per face; W / E applicability", "Q-LIFT-04, Q-LIFT-05"),
        ("B-06", "6Ø12/m HORIZONTAL", BLOCKED, "distribution = wall height; corner joints; W / E", "Q-LIFT-04, "
                                                                                              "Q-LIFT-06"),
        ("B-07", "2 Ø16 WALL BASE (top, bottom)", BLOCKED, "length along the wall; W / E", "Q-LIFT-07"),
        ("B-08", "2Ø12 WALL TOP", BLOCKED, "length along the wall; W / E", "Q-LIFT-07"),
        ("B-09", "ANCHORAGE / BENDS / LAPS", BLOCKED, "not drawn or dimensioned", "Q-LIFT-05, Q-LIFT-06"),
        ("B-10", "GF LIFT TIE BEAM", BLOCKED, "trigger depends on the undefined height measure; section and bars not "
                                             "stated; not drawn", "Q-LIFT-09, Q-LIFT-10"),
        ("B-11", "LIFT OVERRUN / HEADROOM", NOT_IN_SOURCE, "none labelled or levelled", "Q-LIFT-12"),
        ("B-12", "LANDING-DOOR LINTELS", "BLOCKED in S8.6", "S8.6 BLOCKED_SUPPORT_IDENTITY (owner S8.6)", "Q-LIFT-10"),
        ("C-01", "FOUNDATION-STOREY COLUMN WIDTH AT THE PIT", CONFLICT, "drawn 200 (C2 / C1) / 250 (C9) flush with "
         "the 200 walls vs schedule 300 (S3 used it, flag STR-COL-013): the pit-wall cut-outs and the pit clear size "
         "follow the drawn plans until resolved", "Q-LIFT-08"),
        ("C-02", "P8-N19 STOREY HEIGHT", "UNDEFINED_TERM", "GF triggered floor to floor (4.50 > 4.30), not clear to "
         "beam soffit (<= 3.75); clear to slab soffit only if the finish is under 40 mm", "Q-LIFT-09"),
        ("C-03", "PIT DEPTH VS FOUNDING", "QUESTION", "the pit floor is the FF top (p.14) and FF is at least 1.5 m "
         "below the plot level (p.9): the implied pit is at least about 1.95 m deep, whatever the manufacturer needs",
         "Q-LIFT-02"),
        ("C-04", "PRE-S8 'shaft outline not drawn'", "CORRECTED", "the outline is drawn: S-BW FP 10EA / 10EB and GBP "
         "7BE / 7C2, dimensioned 1800 / 200 on all three architectural plans", "-"),
        ("C-05", "S1 / PRE-S8 'lift pit on the FF raft'", "TERMINOLOGY", "FF is an isolated four-column footing (p.14 "
         "'WITH ISOLATED FOOTING'), not a raft; no quantity depends on the word", "-"),
    ]
    out = [{"ID": a, "ITEM": b, "STATE": c, "WHY": d, "QUESTIONS": e} for a, b, c, d, e in rows]
    resolution = {
        "SPC-LIFT_PIT": "outline ESTABLISHED (S-BW + architectural dimensions); pit depth and wall height stay BLOCKED",
        "SPC-LIFT_TIE_BEAM-GF": "storey heights ESTABLISHED floor to floor (4.50 / 4.20 / 4.20); the note's measure "
                                "is undefined; the section stays BLOCKED",
        "PS8-LIFT-WALLS": "shaft plan outline ESTABLISHED; pit depth and wall height stay BLOCKED",
        FOOTING_ID: "dimensions VERIFIED (schedule = drawn = S1); founding level stays BLOCKED",
    }
    for r in pres_census:
        if r["ELEMENT_ID"] in resolution:
            out.append({"ID": f"PRE-S8:{r['ELEMENT_ID']}", "ITEM": r["ELEMENT_FAMILY"], "STATE": r["QA_STATE"],
                        "WHY": f"PRE-S8 missing: {r['MISSING_INFORMATION'] or '-'} -> S8.8: {resolution[r['ELEMENT_ID']]}",
                        "QUESTIONS": "-"})
    for r in pre_if:
        if r["INTERFACE"] in PRE_S8_INTERFACE_RESOLUTION:
            out.append({"ID": f"PRE-S8-IF:{r['INTERFACE']}", "ITEM": f"{r['SIDE_A']} / {r['SIDE_B']}",
                        "STATE": r["STATE"], "WHY": f"PRE-S8 risk: {r['RISK']} -> S8.8: "
                                                  f"{PRE_S8_INTERFACE_RESOLUTION[r['INTERFACE']]}", "QUESTIONS": "-"})
    for r in pre_ex:
        out.append({"ID": f"PRE-S8-READINESS:{r['S8_CANDIDATE']}", "ITEM": r["S8_CANDIDATE"], "STATE": r["READINESS"],
                    "WHY": f"PRE-S8 missing: {r['MISSING']} -> S8.8: plan outline established; pit depth, wall "
                           "height and bar extents stay BLOCKED_NEEDS_AUTHORITY", "QUESTIONS": "Q-LIFT-01..07"})
    return out


def rfi_rows():
    return [{"QUESTION_ID": k, "TO": v[0], "QUESTION": v[1], "BLOCKS": v[2]} for k, v in QUESTIONS.items()]


def census_rows(E, by, A, O, RU, sched):
    rows = []
    for sh, h, layer, rect, what in CITED_POLY:
        rows.append({"SOURCE": f"ST7757.dxf {sh}", "HANDLE": h, "KIND": "LWPOLYLINE", "LAYER": layer,
                     "CONTENT": [_r(v, 3) for v in rect], "USED_FOR": what, "STATE": "VERIFIED_IN_DXF"})
    for sh, h, layer, ab, what in CITED_LINE:
        rows.append({"SOURCE": f"ST7757.dxf {sh}", "HANDLE": h, "KIND": "LINE", "LAYER": layer,
                     "CONTENT": [list(p) for p in ab], "USED_FOR": what, "STATE": "VERIFIED_IN_DXF"})
    for sh, h, text, what in CITED_TEXT:
        rows.append({"SOURCE": f"ST7757.dxf {sh}", "HANDLE": h, "KIND": "TEXT", "LAYER": by[(sh, h)]["layer"],
                     "CONTENT": text, "USED_FOR": what, "STATE": "VERIFIED_IN_DXF"})
    for sh, h in POOL_SBW:
        rows.append({"SOURCE": f"ST7757.dxf {sh}", "HANDLE": h, "KIND": "LWPOLYLINE", "LAYER": "S-BW",
                     "CONTENT": "pool shell outline", "USED_FOR": "the only other S-BW outline: S8.2 SPC-POOL (not a "
                                                                 "lift)", "STATE": "VERIFIED_IN_DXF"})
    rows.append({"SOURCE": "ST7757.dxf schedule (p.9)", "HANDLE": "2B1E", "KIND": "INSERT FTB", "LAYER": "S-TEXT.SCH",
                 "CONTENT": sched, "USED_FOR": "FF footing schedule row", "STATE": "VERIFIED_IN_DXF"})
    rows.append({"SOURCE": "ST7757.dxf schedule (p.9)", "HANDLE": "1C64", "KIND": "TEXT", "LAYER": "S-TEXT.SCH",
                 "CONTENT": "legacy-encoded remark (not reproduced)", "USED_FOR": "FF remark 'lift base' (PRE-S8 "
                                                                              "decoding)", "STATE": "RECORDED"})
    for fl, rr in A.items():
        for r in rr:
            rows.append({"SOURCE": f"P7757.dxf {fl} plan (registered by S8.6)", "HANDLE": r["handle"],
                         "KIND": r["kind"], "LAYER": r["layer"],
                         "CONTENT": r.get("measurement_mm", [r["a"], r["b"]]), "USED_FOR": r["what"],
                         "STATE": "VERIFIED_IN_DXF"})
    rows.append({"SOURCE": P14, "HANDLE": "visual", "KIND": "PDF_RASTER", "CONTENT": "see 07", "USED_FOR":
                 "pit section, wall bars, pit depth note", "STATE": "VISUAL_RECORD (renders not committed)"})
    for k, v in RU.items():
        rows.append({"SOURCE": f"S1 rule register {k} (p.{v['page']})", "HANDLE": "-", "KIND": v["status"],
                     "CONTENT": v["english"], "USED_FOR": v["normalized"], "STATE": v["priority"]})
    for r in O["spec"]:
        rows.append({"SOURCE": "S1 special occurrence register", "HANDLE": r["special_id"], "KIND": r["kind"],
                     "CONTENT": f"{r['status']} / {r['terminal_state']}", "USED_FOR": "lift family record",
                     "STATE": "READ"})
    for c in O["s2"]:
        rows.append({"SOURCE": "S2 component release", "HANDLE": c["element_id"], "KIND": c["component"],
                     "CONTENT": f"{c['release_state']} ({c['unit']})", "USED_FOR": "existing component record",
                     "STATE": "READ"})
    rows.append({"SOURCE": "S3 column flags", "HANDLE": O["flag"]["flag_id"], "KIND": O["flag"]["detector"],
                 "CONTENT": _clean(O["flag"]["current_interpretation"]), "USED_FOR": "foundation-storey column width",
                 "STATE": "READ"})
    for r in O["q81a"]:
        rows.append({"SOURCE": "S8.1A question register", "HANDLE": r["ID"], "KIND": r["KIND"],
                     "CONTENT": _clean(r["QUESTION"]), "USED_FOR": "pit depth (handed to the lift family)",
                     "STATE": r["STATUS"]})
    return rows


def population_rows(n_shafts):
    keys = ("ELEMENT_ID", "KIND", "PARENT", "DESCRIPTION", "EXISTING_RECORDS", "DECISION")
    out = [dict(zip(keys, p)) for p in POPULATION]
    for r in out:
        r["SHAFT_COUNT"] = n_shafts if r["ELEMENT_ID"] == "LIFT-01" else ""
    return out


def conservation(L):
    out = []

    def A(cid, text, ok, detail=""):
        out.append({"CHECK_ID": cid, "CHECK": text, "RESULT": "PASS" if ok else "FAIL", "DETAIL": detail})
    s, w = L["s"], L["w"]
    A("C01", "one physical shaft: every inside-face view groups into one; the other S-BW outline is the S8.2 pool",
      L["n_shafts"] == 1, json.dumps([g["views"] for g in L["shaft_groups"]]))
    A("C02", "inside 1800 x 1800, walls 200 on every side; architectural 1800 / 200 on GF / 1F / 2F",
      abs(s["INSIDE_CLEAR_AREA"] - 3.24e6) < 1e-3 and abs(s["WALL_RING_AREA"] - 1.6e6) < 1e-3, "")
    A("C03", "net wall pieces + column overlaps = the ring exactly; net = S8.1A RG-12..15",
      abs(w["net_footprint"] + sum(w["member_overlap"].values()) - w["ring_area"]) < 1e-6 and
      abs(w["net_footprint"] - 1.1e6) < 1e-3, f"net {_full(w['net_footprint'] / 1e6)} m2, columns "
                                              f"{_full(sum(w['member_overlap'].values()) / 1e6)} m2")
    A("C04", "the 3.24 m2 ground-slab opening = the pit internal area = the GF / 1F roof voids = the roof panel",
      all(x["RESULT"] == "PASS" for x in L["over"] if x["CHECK_ID"] == "OV-07") and L["n_shafts"] == 1, "")
    A("C05", "the whole shaft stands on the FF footing; walls start at its top (no shared volume)",
      SG.plan_overlap(w["pieces"], [FOOTING])["off"] == 0.0, "")
    A("C06", "FF drawn 4600 x 4500 = schedule 460 x 450 (depth 55)",
      abs(FOOTING[2] - FOOTING[0] - 4600) < 0.01 and abs(FOOTING[3] - FOOTING[1] - 4500) < 0.01 and
      (L["sched"]["W"], L["sched"]["H"], L["sched"]["DEPHT"]) == ("460", "450", "55"), "")
    A("C07", "every overlap check passes", all(x["RESULT"] == "PASS" for x in L["over"]),
      json.dumps([x["CHECK_ID"] for x in L["over"] if x["RESULT"] != "PASS"]))
    A("C08", "no concrete and no kg released; every pit-wall quantity is blocked",
      L["released_m3"] == 0.0 and L["released_kg"] == 0.0 and
      all(r["LANE"] not in RELEASED_LANES for r in L["walls"]) and
      all(r["QUANTITY_STATE"] not in RELEASED_LANES for r in L["reb"]), "")
    A("C09", "the three S8.6 landing openings sit in the S wall at the architectural jambs, 1000 wide, none in the RC "
      "pit wall", all(r["STATE"].startswith("RECONCILED") and r["WIDTH_ARCH_MM"] == 1000.0
                      for r in L["open"] if r["S8_6_OPENING"] != "-"), "")
    A("C10", "P8-N19: GF triggered only floor to floor; 1F and 2F never triggered",
      [r["TRIGGER_FLOOR_TO_FLOOR"] for r in L["tie"][:3]] == [SG.TRIGGERED, SG.NOT_TRIGGERED, SG.NOT_TRIGGERED] and
      L["tie"][0]["TRIGGER_CLEAR_TO_BEAM_SOFFIT"] == SG.NOT_TRIGGERED, "")
    A("C11", "12 S6 beam occurrences on the shaft walls, four per roof level", len(L["O"]["s6"]) == 12, "")
    A("C12", "every component in the ownership audit has exactly one of the six states",
      all(r["STATE"] in (SG.ALREADY_OWNED_AND_MEASURED, SG.OWNED_BUT_UNMEASURED, SG.NEW_SOURCE_DERIVED,
                         SG.NEW_PROJECT_BASIS_QTO, SG.BLOCKED_UNQUANTIFIED, SG.SOURCE_CONFLICT) for r in L["own"]), "")
    A("C13", "PRE-S8 read through whitelists only; no firewalled column bound; references_read empty", True,
      json.dumps(PRE_S8_COLUMNS))
    A("C14", "all 25 earlier freezes, the S8.3 errata and the S1 / S2 / S3 / S3.1 register indexes verify",
      len(L["frozen"]) == 25, f"{len(L['frozen'])} manifests")
    A("C15", "the S4 FF bars and the S3.1 starters are read, not re-counted; the S4.1-T01 bars land here blocked",
      L["O"]["T01"]["KG_IN_S4_1"] == "0.0" and all(r["KG"] == 0.0 for r in L["reb"]), "")
    return out


# ------------------------------------------------------------------ build
def run():
    frozen, errata, index = verify_inputs()
    src, E, by = structural()
    T = registration()
    A = architectural(T)
    sched = schedule_row()
    LV = levels()
    RU = rules()
    pre_census = pre_s8("PRE_S8_CENSUS")
    pre_if = pre_s8("PRE_S8_INTERFACES")
    pre_ex = pre_s8("PRE_S8_EXHAUSTION")
    ready = pre_s8_readiness()
    check({r["ELEMENT_ID"] for r in pre_census if r["ROW_KIND"] == "ELEMENT"} >=
          {"SPC-LIFT_PIT", "SPC-LIFT_TIE_BEAM-GF", FOOTING_ID}, "PRE-S8 lift rows")
    reps, shaft_groups, n_shafts = representations(E, by, A)
    s, w, door = shaft_geometry()
    O = owners(src, s, w)
    found, vol = foundation_rows(O, sched, w)
    depth = depth_rows(LV, sched, s)
    walls, sens = wall_rows(w, LV, sched)
    callouts = callout_rows()
    reb = rebar_rows(w)
    tie, ff = tie_rows(LV, w, RU, O["s86b"])
    opens = opening_rows(O, door, A)
    over, s87 = overlap_rows(O, w, src)
    own = ownership_rows(O, w, vol)
    blocked = blocked_rows(O, pre_census, pre_if, pre_ex)
    released_m3 = math.fsum(r["CONCRETE_M3"] for r in walls if r["LANE"] in RELEASED_LANES)
    released_kg = math.fsum(r["KG"] for r in reb if r["QUANTITY_STATE"] in RELEASED_LANES)
    L = {"frozen": frozen, "errata": errata, "index": index, "s": s, "w": w, "door": door, "O": O, "found": found,
         "vol": vol, "depth": depth, "walls": walls, "sens": sens, "callouts": callouts, "reb": reb, "tie": tie,
         "open": opens, "over": over, "own": own, "blocked": blocked, "reps": reps, "shaft_groups": shaft_groups,
         "n_shafts": n_shafts, "sched": sched, "LV": LV, "RU": RU, "A": A, "pre_census": pre_census,
         "pre_if": pre_if, "pre_ex": pre_ex, "ready": ready, "released_m3": released_m3, "released_kg": released_kg,
         "census": census_rows(E, by, A, O, RU, sched), "s87": s87}
    L["cons"] = conservation(L)
    check(all(x["RESULT"] == "PASS" for x in L["cons"]), "conservation: " + json.dumps(
        [x for x in L["cons"] if x["RESULT"] != "PASS"]))
    return L


def provenance(L):
    lines = []
    for r in L["walls"]:
        lines.append({"record": f"CONCRETE:{r['ELEMENT_ID']}", "lane": r["LANE"], "m3": r["CONCRETE_M3"],
                      "sources": ["ST7757 FP 10EA / 10EB, GBP 7BE / 7C2", "P7757 GF / 1F / 2F (registered)", P14,
                                  "S8.1A 01_RECOVERED_LIFT_PIT_REGION"], "reason": r["REASON"]})
    for r in L["reb"]:
        lines.append({"record": f"REBAR:{r['ELEMENT_ID']}:{r['ROLE']}:{r.get('FACE', '')}",
                      "state": r["QUANTITY_STATE"], "kg": r["KG"], "sources": [P14], "formula": r["FORMULA"]})
    for r in L["tie"]:
        lines.append({"record": f"TIE_BEAM:{r['STOREY']}", "requirement": r["REQUIREMENT"],
                      "sources": ["S1 rule P8-N19", "S1 level register", "S8.6 04_OPENING_LINTEL_BINDING_MATRIX"]})
    lines.append({"record": "FOOTING:FF", "m3_computed_not_released": _r(L["vol"]),
                  "sources": ["ST7757 FP 1B2B", "ST7757 2B1E", str(READ["S4_OCC"].relative_to(ROOT))]})
    (HERE / OUTPUTS[15]).write_text("".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in lines),
                                    encoding="utf-8")


def write(L):
    _csv(OUTPUTS[1], L["census"], ["SOURCE", "HANDLE", "KIND", "LAYER", "CONTENT", "USED_FOR", "STATE"])
    _csv(OUTPUTS[2], population_rows(L["n_shafts"]))
    _csv(OUTPUTS[3], L["reps"])
    _csv(OUTPUTS[4], L["found"])
    _csv(OUTPUTS[5], L["depth"], ["RECORD", "ID", "WHAT", "VALUE", "UNIT", "STATE", "BASIS", "SOURCE"])
    _csv(OUTPUTS[6], L["walls"], ["ELEMENT_ID", "SIDE", "RECT_MM", "LENGTH_MM", "THICKNESS_MM", "INNER_FACE_MM",
                                  "OUTER_FACE_MM", "FOOTPRINT_M2", "BOTTOM_LEVEL", "TOP_LEVEL", "HEIGHT_M",
                                  "CONCRETE_M3", "LANE", "M3_PER_M_HEIGHT_CONDITIONAL", "SENSITIVITY", "REASON"])
    _csv(OUTPUTS[7], L["callouts"])
    _csv(OUTPUTS[8], L["reb"], ["ELEMENT_ID", "CALLOUT", "ROLE", "BAR_DIAMETER_MM", "FACE", "APPLICABILITY",
                                "DISTRIBUTION_LENGTH_MM", "DISTRIBUTION_STATE", "COUNT_ALONG_FACE", "BAR_LENGTH_STATE",
                                "KG", "KG_PER_M_BAR_LENGTH_CONDITIONAL", "KG_PER_M_WALL_HEIGHT_CONDITIONAL",
                                "QUANTITY_STATE", "FORMULA"])
    _csv(OUTPUTS[9], L["tie"], ["STOREY", "LOWER_FFL_M", "UPPER_FFL_M", "FLOOR_TO_FLOOR_M", "TRIGGER_FLOOR_TO_FLOOR",
                                "TRIGGER_CLEAR_TO_SLAB_SOFFIT", "CLEAR_TO_SLAB_SOFFIT_NOTE",
                                "TRIGGER_CLEAR_TO_BEAM_SOFFIT", "CLEAR_TO_BEAM_SOFFIT_NOTE", "REQUIREMENT",
                                "ELEVATION_IF_REQUIRED_M", "ELEVATION_DATUM", "EXISTING_BEAM_AT_ELEVATION",
                                "PLAN_PATH", "SECTION", "REINFORCEMENT", "S1_S2_RECORD", "OWNER", "QUANTITY_STATE",
                                "CONCRETE_M3", "KG"])
    _csv(OUTPUTS[10], L["open"], ["ELEMENT_ID", "S8_6_OPENING", "FLOOR", "FFL_M", "WALL_SIDE", "JAMB_HANDLES",
                                  "JAMB_X_MM", "WIDTH_ARCH_MM", "WIDTH_S8_6_MM", "WIDTH_IN_WALL_LINE_MM",
                                  "DISTANCE_TO_INNER_CORNERS_MM", "WALL_OWNER", "RC_WALL_DEDUCTION_M3",
                                  "WHY_NO_RC_DEDUCTION", "LINTEL", "BEAM_OVER_DOOR_DEPTH_MM", "HEIGHT", "STATE"])
    _csv(OUTPUTS[11], L["over"])
    _csv(OUTPUTS[12], L["own"])
    _csv(OUTPUTS[13], L["blocked"])
    _csv(OUTPUTS[14], rfi_rows())
    provenance(L)
    _csv(OUTPUTS[16], L["cons"])
    O, w = L["O"], L["w"]
    summary = {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "physical_population": {"lift_shafts": L["n_shafts"], "shaft": "LIFT-01",
                                "elements": [p[0] for p in POPULATION]},
        "dimensions_established": {
            "inside_mm": [1800, 1800], "wall_mm": 200, "outside_mm": [2200, 2200],
            "inside_area_m2": _m2(L["s"]["INSIDE_CLEAR_AREA"]), "ring_area_m2": _m2(L["s"]["WALL_RING_AREA"]),
            "net_wall_footprint_m2": _m2(w["net_footprint"]),
            "column_overlap_m2": _m2(sum(w["member_overlap"].values())),
            "wall_pieces_mm": {p["side"]: _r(p["length"], 6) for p in w["pieces"]},
            "perimeters_m": {"inside": _r(L["s"]["INSIDE_PERIMETER"] / 1000),
                             "outside": _r(L["s"]["OUTER_PERIMETER"] / 1000),
                             "centreline": _r(L["s"]["CENTRELINE_PERIMETER"] / 1000)},
            "stops_m": [1.0, 5.5, 9.7], "roof_m": 13.9, "door_mm": 1000},
        "blocked_levels": ["founding level", "FF top / pit floor", "pit-wall top", "pit depth", "overrun"],
        "opening_3_24_equals_pit_internal_area": True,
        "footing": {"id": FOOTING_ID, "schedule_cm": [460, 450, 55], "concrete_m3_computed_not_released": _r(L["vol"]),
                    "concrete_state": SG.OWNED_BUT_UNMEASURED, "bars_kg_S4_lower_bound": float(O["S4o"]["known_kg"]),
                    "bars_state": SG.ALREADY_OWNED_AND_MEASURED,
                    "starters_kg_S3_1": _r(math.fsum(r["kg"] for r in O["starters"]))},
        "released": {"concrete_m3": _r(L["released_m3"]), "kg": _r(L["released_kg"]), "kg_by_diameter": {},
                     "kg_by_role": {}, "pit_base_m3": 0.0, "pit_wall_m3": 0.0},
        "sensitivity_only": {"pit_walls_m3_if_ff_at_minimum_founding_and_top_at_ffl": _r(L["sens"])},
        "tie_beam": {r["STOREY"]: r["REQUIREMENT"] for r in L["tie"]},
        "s6_shaft_beams": [r["occurrence_id"] for r in O["s6"]],
        "questions": sorted(QUESTIONS), "conservation": {x["CHECK_ID"]: x["RESULT"] for x in L["cons"]},
        "frozen_baselines": {k: v["manifest_sha256"] for k, v in L["frozen"].items()},
        "register_indexes": L["index"], "s8_3_errata_sha256": L["errata"], "unit_mass": UM.describe(UNIT_MASS),
        "pre_s8_readiness": L["ready"], "references_read": []}
    _json(OUTPUTS[17], summary)
    (HERE / OUTPUTS[0]).write_text(readme(summary, L), encoding="utf-8")
    manifest = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "FROZEN_BEFORE_COMPARISON",
                "engine_commit_stamp": summary["engine_commit"], "references_read": [],
                "code": {c_: _sha(ROOT / c_) for c_ in CODE},
                "inputs": {str(p_.relative_to(ROOT)): _sha(p_) for p_ in READ.values()},
                "drawing_sha256": {"P7757.dxf": ARCH_SHA, "ST7757.dxf": STRUCT_SHA, "ST7757.pdf": STRUCT_PDF_SHA},
                "pre_s8_columns_read": PRE_S8_COLUMNS, "pre_s8_readiness_keys_read": list(PRE_S8_READINESS_KEYS),
                "frozen_baselines": summary["frozen_baselines"], "register_indexes": L["index"],
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "released": summary["released"],
                "rule": "frozen before any earlier Urban, contractor or third-party lift figure is used; the "
                        "comparison after it explains differences and never changes a frozen quantity"}
    _json(MANIFEST_NAME, manifest)
    for k, m_ in MANIFESTS.items():
        DR.verify_frozen(m_, ROOT)
    for o in OUTPUTS + [MANIFEST_NAME]:
        check(not HYGIENE.search((HERE / o).read_text(encoding="utf-8")), f"hygiene: {o}")
    return summary


def readme(s, L):
    d = s["dimensions_established"]
    pieces = ", ".join(f"{k} {_full(v / 1000)} m" for k, v in d["wall_pieces_mm"].items())
    tie = "\n".join(f"| {r['STOREY']} | {_full(r['FLOOR_TO_FLOOR_M']) if r.get('FLOOR_TO_FLOOR_M') else '-'} | "
                    f"{r.get('TRIGGER_FLOOR_TO_FLOOR', '-')} | {r.get('TRIGGER_CLEAR_TO_BEAM_SOFFIT', '-')} | "
                    f"{r['REQUIREMENT']} |" for r in L["tie"])
    return f"""# S8.8 lift pit, shaft walls, foundation and intermediate tie beam

Round {ROUND}, baseline `{BASELINE_HEAD}`, engine `{s['engine_commit']}`. Frozen before any comparison
(`{MANIFEST_NAME}`, `references_read: []`).

## Physical population

There is **one lift shaft**, LIFT-01. Every view of it groups into one physical shaft (`03`):

- the S-BW outlines on the foundation plan (10EA / 10EB) and the ground-beam plan (7BE / 7C2);
- the open-to-below panels on the GF and 1F roof sheets, and the roof panel on the 2F roof sheet;
- the inside faces on the three architectural plans.

The only other S-BW outline (GBP 7C5 / 7C6) is the S8.2 pool.

The shaft is 1800 x 1800 inside, with 200 walls and four corner columns:

- C2 at the SW corner;
- C1 at the NW corner;
- C9 at the SE corner;
- C2 at the NE corner.

It sits on the FF footing (460 x 450 x 55). It serves three stops (GF +1.00, 1F +5.50, 2F +9.70), each with a 1000 mm
door in the S wall, under the 2F roof at +13.90. No overrun is labelled.

## What is established and what is not

- **Plan geometry: established.**
  - The 3.24 m2 S8.1A opening equals the pit's inside area exactly.
  - The ring is {_full(d['ring_area_m2'])} m2. The columns take {_full(d['column_overlap_m2'])} m2 of it, once.
  - The net wall pieces ({pieces}) give {_full(d['net_wall_footprint_m2'])} m2.
  - Perimeters (m): inside {_full(d['perimeters_m']['inside'])}, outside {_full(d['perimeters_m']['outside'])}, \
centreline {_full(d['perimeters_m']['centreline'])}.
- **Pit floor.** It is the FF footing top: p.14 draws no pit slab, so no second base is added.
- **Levels: not established.**
  - The pit depth is 'As Per Lift Manufactures recommendations'.
  - The founding level is not printed. p.9 note 1 gives only a 1.5 m minimum excavation.
  - The wall top is the slab-on-grade top, which is FFL less a finish that is not printed.
- **Above the pit.** The enclosure is 'AS PER PLAN': 200 walls on the architectural plans only (blockwork, the
  S8.6 wall owner).

## Released

**{_full(s['released']['concrete_m3'])} m3 and {_full(s['released']['kg'])} kg.**

- **Pit-wall concrete.** Blocked on the depth.
  - Coefficient: {_full(d['net_wall_footprint_m2'])} m3 per metre of wall height.
  - Sensitivity: {_full(s['sensitivity_only']['pit_walls_m3_if_ff_at_minimum_founding_and_top_at_ffl'])} m3, with FF \
at the -1.50 minimum founding and the wall top at +1.00. It is never released.
- **Wall bars.** p.14 draws 6Ø16/m vertical U-bars and 6Ø12/m horizontal bars on both faces of the two walls it
  cuts, the door wall (S) and the wall opposite (N). It also draws 2 Ø16 top and bottom in the footing under each
  wall, and 2Ø12 at the wall top. All are blocked: no bar length without the depth, no extents along the walls, and
  the W and E walls are not shown.
- **FF footing.**
  - The four mats are S4's: {s['footing']['bars_kg_S4_lower_bound']} kg Ø14, a lower bound.
  - The concrete ({_full(s['footing']['concrete_m3_computed_not_released'])} m3) is computable. The footing \
family owns it and no frozen stage has measured it.
  - The S3.1 starters ({_full(s['footing']['starters_kg_S3_1'])} kg) stay S3.1's.

## Tie beam (P8-N19)

| Storey | Floor to floor m | Floor-to-floor trigger | Clear to beam soffit | Requirement |
|---|---|---|---|---|
{tie}

## Open points

- **Conflict:** the foundation-storey column width (drawn 200 vs scheduled 300) at the pit walls (Q-LIFT-08).
- **Questions:** Q-LIFT-01 to Q-LIFT-13 in `14_RFI_QUESTIONS.csv`.

## Firewall

PRE-S8 is read through column whitelists only. No earlier lift figure is read before the freeze.
"""


def main():
    L = run()
    s = write(L)
    print(json.dumps({"released": s["released"], "shafts": s["physical_population"]["lift_shafts"],
                      "tie": s["tie_beam"], "sens": s["sensitivity_only"]}, indent=1))


if __name__ == "__main__":
    main()
