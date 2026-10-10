"""S8.7A - stair riser, finishing and structural-geometry correction audit. A dated correction layer over the frozen
S8.7 package (S8.7 is read, never written). Source-controlled and blind: frozen before any earlier commercial figure is
read.

    python3 -I research/alsenan_stairs_s8_7a/build_s8_7a.py

Reads the registered drawings again, independently of the S8.7 builder:
- ST7757.dxf through the frozen S1 reader: the GBP / GFRS / FFRS sheets (tread, winder and riser lines; beam bands);
- P7757.dxf with ezdxf, each plan registered onto the structural frame by the frozen S8.6 translations;
- section A-A of the architectural PDF and p.16 of ST7757.pdf as visual records (renders stay out of git);
- the owner's seven images (four plan crops of the sanitary drawing set, three crops of p.16) as supporting visual
  evidence: they are not a registered input and no count is taken from them alone.
and the frozen S8.7 outputs (population, tread census, geometry, concrete, bars, ownership), S1 slab panels and S6
beam occurrences.

Owner information enters as OWNER_SCENARIO: the floor levels, the riser scenarios (GF -> 1F 28 / 29, 1F -> 2F 27 /
26), the 150 - 160 mm preference, a 30 mm marble finish (bedding not confirmed) and a 160 mm waist sensitivity. No
scenario is selected and no scenario quantity is released: the production release stays S8.7's until the owner
approves a change.
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
from engine.source import stair_riser_schedule as RS  # noqa: E402

ROUND = "S8_7A"
DATE = "2026-10-10"
BASELINE_HEAD = "15730e0"
POLICY = "S8_7A_STAIR_RISER_AUDIT_V1"
R = ROOT / "research"
BY_SHA = ROOT / "data/inputs/by_sha256"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
STRUCT_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
STRUCT_PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
ARCH_PDF_SHA = "1e7087d3e61bbb682c9107193c97550a2837e5198bde0ee311319bf7f4a08459"
S87 = R / "alsenan_stairs_s8_7"
S87_MANIFEST = S87 / "17_S8_7_FREEZE_MANIFEST.json"
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
             "S8.7": S87_MANIFEST,
             "S8.8": R / "alsenan_lift_s8_8/18_S8_8_FREEZE_MANIFEST.json"}
S83_ERRATA = R / "alsenan_dome_ring_s8_3/errata"
S1D = R / "alsenan_structural_census_s1"
INDEXES = {"S1": (S1D / "INDEX.json", "registers"), "S2": (R / "alsenan_structural_s2/INDEX.json", "outputs"),
           "S3": (R / "alsenan_column_rebar_s3/INDEX.json", "outputs"),
           "S3.1": (R / "alsenan_column_rebar_s3_1/INDEX.json", "outputs")}
READ = {"S87_POPULATION": S87 / "01_STAIR_POPULATION_CENSUS.csv",
        "S87_TREADS": S87 / "02_TREAD_RUN_CENSUS.csv",
        "S87_LEVELS": S87 / "05_LEVEL_REGISTER.csv",
        "S87_GEOMETRY": S87 / "06_PLAN_AND_INCLINED_GEOMETRY.csv",
        "S87_CONCRETE": S87 / "07_CONCRETE_QTO.csv",
        "S87_BINDING": S87 / "08_REBAR_ANNOTATION_BINDING.csv",
        "S87_REBAR": S87 / "09_REBAR_QTO.csv",
        "S87_OWNERSHIP": S87 / "10_OWNERSHIP_AUDIT.csv",
        "S87_S7": S87 / "11_S7_STAIR_ADJACENT_RECOMPUTE.csv",
        "S87_BLOCKED": S87 / "12_BLOCKED_AND_CONFLICTS.csv",
        "S87_SUMMARY": S87 / "16_S8_7_SUMMARY.json",
        "S1_SLABS": S1D / "SLAB_PANEL_REGISTER.json",
        "S1_RULES": S1D / "STRUCTURAL_PROJECT_RULE_REGISTER.json",
        "S6_OCC": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCES.csv",
        "S86_REGISTRATION": R / "alsenan_lintels_s8_6/03_ARCH_STRUCTURAL_REGISTRATION.csv"}
CODE = ["engine/source/stair_riser_schedule.py", "engine/source/stair_geometry.py", "engine/source/rebar_unit_mass.py",
        "engine/source/delta_release.py", "research/alsenan_stairs_s8_7a/build_s8_7a.py",
        "research/external_engine_lab/alsenan_structural_s1.py"]
OUTPUTS = ["00_README.md", "01_RISER_COUNT_COMPARISON.csv", "02_RISER_LINE_EVIDENCE.csv",
           "03_RISER_ELEVATION_SCHEDULE.csv", "04_FIRST_LAST_RISER_FINISH_ADJUSTMENT.csv",
           "05_WAIST_AND_LANDING_GEOMETRY.csv", "06_CONCRETE_QUANTITY_SCENARIOS.csv",
           "07_REINFORCEMENT_QUANTITY_SCENARIOS.csv", "08_BEAM_AND_S6_S7_OWNERSHIP_RECONCILIATION.csv",
           "09_SOURCE_CONFLICT_REGISTER.csv", "10_ENGINEER_RFI_LIST.csv", "11_S8_7_REPRODUCTION_AND_CORRECTIONS.csv",
           "12_RELEASE_SUMMARY.json", "13_PROVENANCE.jsonl", "14_CONSERVATION_CHECKS.csv"]
MANIFEST_NAME = "15_S8_7A_CORRECTION_MANIFEST.json"
UNIT_MASS = {"method": UM.D2_OVER_162, "authority": "project-wide method used by S3.1 / S6.1 / S7 / S8",
             "selected_by": "Urban (project basis)"}
SOURCE_VERIFIED, PROJECT_BASIS_QTO = "SOURCE_VERIFIED", "PROJECT_BASIS_QTO"
OWNER_SCENARIO, BLOCKED, CONFLICT = "OWNER_SCENARIO", "BLOCKED_UNQUANTIFIED", "SOURCE_CONFLICT"
RELEASED_LANES = (SOURCE_VERIFIED, PROJECT_BASIS_QTO)
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")

# ------------------------------------------------------------------ owner information (OWNER_SCENARIO, not source)
OWNER = {"GF_FFL_M": 1.00, "1F_FFL_M": 5.50, "2F_FFL_M": 9.70, "RISE_GF_1F_MM": 4500.0, "RISE_1F_2F_MM": 4200.0,
         "PREFERRED_RISER_MM": (150.0, 160.0), "MARBLE_MM": 30.0, "BEDDING": "included only if explicitly confirmed",
         "WAIST_SENSITIVITY_MM": 160.0, "LANDING": "approximately halfway; actual levels from drawings or approval",
         "SCENARIOS": {"A1": {"A": 28, "B": 29}, "A2": {"A": 27, "B": 26}}}
OWNER_IMAGES = [  # id, what the image shows, how it is used
    ("IMG-1", "sanitary drawing set p.3 of 3 (2F plan, +9.70): main stair arriving from 1F; west flight 12 / east "
              "flight 11 tread lines; the NW quarter drawn flat (rounded handrail, no winder lines); up-path arrows",
     "agrees with the architectural 2F DXF view (no radial lines on that view)"),
    ("IMG-2", "sanitary drawing set p.1 of 3 (GF plan, +1.00 / +0.30): main stair with three radial winder lines in "
              "the NW quarter, the break symbol on the west flight, the +0.30 lobby door at the north",
     "agrees with the architectural GF DXF view"),
    ("IMG-3", "sanitary drawing set p.2 of 3 (1F plan, +5.50): main stair 1F -> 2F with three radial winder lines, "
              "the break symbol on the west flight, the up-path ending at the south end of the east flight",
     "agrees with the architectural 1F DXF view"),
    ("IMG-4", "sanitary drawing set p.2 of 3 (1F plan): the round (light-well) stair around the VOID: curved flight, "
              "straight flight along the south edge, corner landing, short flight north with the up arrow, +5.50",
     "agrees with the architectural 1F DXF view"),
    ("IMG-5", "ST7757 p.16 crop: TYPICAL STEEL LAYOUT-STAIR SECTION (N.I.S.), TYPICAL DETAIL FOR OPENING IN BEAM, "
              "DETAIL OF RIBS SOLID PART, TORSION STEEL FOR RIBS", "typical only; the same page S8.7 read"),
    ("IMG-6", "ST7757 p.16 crop: TYPICAL DETAIL OF STAIR BEAM and the upper part of the typical stair section "
              "(+4.00 / +3.95 S.S.L at the head beam)", "typical only"),
    ("IMG-7", "ST7757 p.16 crop: TYPICAL DETAIL OF STAIR BEAM (cranked beam column to column: 2Ø12 top, 4Ø16 bottom, "
              "6Ø8/m stirrups, depth AS PER SCH.)", "typical only"),
]
SECTION_AA = "P7757 architectural sections PDF sheet 4, SECTION A-A (visual, re-read at 600 dpi in this round)"
SECTION_AA_FACTS = {
    "A1-F2": (12, "upper flight GF -> 1F cut: 12 risers, 11 treads (11 goings = the 3.30 m of the structural plan)"),
    "A2-F2": (12, "upper flight 1F -> 2F cut: 12 risers, 11 treads"),
    "A1-L1_LEVEL_M": (3.50, "'320' from the +0.30 lobby floor to the top of the half-landing"),
}

# ------------------------------------------------------------------ cited geometry (sheet-local mm)
X_BAY_W, X_WALL_W, X_WALL_E, X_BAY_E = 17087.904, 18287.904, 18387.904, 19587.904
Y_BAY_N, Y_WALL_END, Y_ZONE_S = 20611.856, 19411.856, 16311.856
TURN_CORNER = (18237.904, 19461.856)
WEST_TREAD, EAST_TREAD = (17087.904, 18237.904), (18437.904, 19587.904)
WELL_C, WELL_R_IN, WELL_R_OUT = (23673.334, 11742.299), 1530.511, 2780.511
STRAIGHT_X, STRAIGHT_Y = (23700.0, 26800.0), (9011.856, 10161.856)
CF2_X, CF2_Y = (26757.904, 27907.904), (10150.0, 11450.0)
ENTR_X = (14250.0, 15600.0)
GOING_MM = 300.0
WIDTH_MAIN_MM = 1200.0        # bay edge to the central wall face (P7757 '1200' / '100' / '1200')
HEAD_BEAMS = {"GFRS": "BL020", "FFRS": "BL009"}
PAIR_TOL = 60.0


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
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
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


def structural_lines():
    import alsenan_structural_s1 as S1
    src = S1.Source()
    E = src.entities()
    out = {}
    for sh in ("GBP", "GFRS", "FFRS"):
        out[sh] = [{"view": sh, "handle": e["handle"], "layer": e["layer"], "a": tuple(e["a"][:2]),
                    "b": tuple(e["b"][:2])} for e in E[sh] if e["type"] == "LINE" and e["layer"] == "2"]
    return src, E, out


def architectural_lines():
    import ezdxf
    T = {}
    for r in _rows(READ["S86_REGISTRATION"]):
        if r["RECORD"] == "FLOOR":
            T[r["FLOOR"]] = (float(r["TX_MM"]), float(r["TY_MM"]))
    check(set(T) == {"GF", "1F", "2F"}, "S8.6 registers the three plans")
    doc = ezdxf.readfile(str(BY_SHA / f"{ARCH_SHA}.dxf"))
    msp = doc.modelspace()
    frames = []
    for e in msp:
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "1" and e.closed:
            pts = [(p[0], p[1]) for p in e.get_points("xy")]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            if abs(max(xs) - min(xs) - 40314) < 1 and abs(max(ys) - min(ys) - 28030) < 1:
                frames.append((min(xs), min(ys), max(xs), max(ys)))
    win = (16900.0, 8800.0, 28500.0, 21100.0)
    out = {}
    for fl, (tx, ty) in T.items():
        cand = [b for b in frames if b[0] + tx <= win[0] and b[1] + ty <= win[1] and b[2] + tx >= win[2]
                and b[3] + ty >= win[3]]
        check(len(cand) == 1, f"{fl}: one plan frame registers onto its structural sheet")
        fr = cand[0]
        ls = []
        for e in msp:
            if e.dxftype() != "LINE" or e.dxf.layer not in ("2", "5"):
                continue
            a, b = (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)
            if fr[0] <= a[0] <= fr[2] and fr[1] <= a[1] <= fr[3]:
                ls.append({"view": f"ARCH-{fl}", "handle": e.dxf.handle, "layer": e.dxf.layer,
                           "a": (a[0] + tx, a[1] + ty), "b": (b[0] + tx, b[1] + ty)})
        out[f"ARCH-{fl}"] = ls
    return T, out


# ------------------------------------------------------------------ independent recount
def _horizontal(lines, x_span, y_lo, y_hi, layers=None, tol=5.0):
    out = []
    for l in lines:
        (ax, ay), (bx, by_) = l["a"], l["b"]
        if abs(ay - by_) > 0.5 or (layers and l["layer"] not in layers):
            continue
        if abs(min(ax, bx) - x_span[0]) <= tol and abs(max(ax, bx) - x_span[1]) <= tol and y_lo <= ay <= y_hi:
            out.append((ay, l))
    return out


def _vertical(lines, x_lo, x_hi, y_span, tol=5.0, layers=None):
    out = []
    for l in lines:
        (ax, ay), (bx, by_) = l["a"], l["b"]
        if abs(ax - bx) > 0.5 or (layers and l["layer"] not in layers):
            continue
        if x_lo <= ax <= x_hi and abs(min(ay, by_) - y_span[0]) <= tol and abs(max(ay, by_) - y_span[1]) <= tol:
            out.append((ax, l))
    return out


def _pair(found):
    lines = [(off, f"{l['handle']}/L{l['layer']}") for off, l in found]
    return RS.pair_lines(lines, PAIR_TOL)


def _pair_span(found):
    """the pairs with the lowest and highest line offset of each (riser face / nosing either side)."""
    off = {f"{l['handle']}/L{l['layer']}": o for o, l in found}
    return [(p, ids, min(off[i] for i in ids), max(off[i] for i in ids)) for p, ids in _pair(found)]


def _angle(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0


def turn_risers(lines):
    """winder risers in the NW quarter: radial lines grouped by angle, then the closing riser at the NW / NE
    boundary (a vertical line from the central wall end to the bay edge)."""
    rad = []
    for l in lines:
        a, b = l["a"], l["b"]
        if not all(X_BAY_W - 30 <= p[0] <= X_WALL_W + 10 and TURN_CORNER[1] - 10 <= p[1] <= Y_BAY_N + 50 for p in (a, b)):
            continue
        ang = _angle(a, b)
        if 5 < ang < 85 or 95 < ang < 175:
            if math.dist(a, b) > 1000:
                rad.append((ang, l))
    groups = []
    for ang, l in sorted(rad, key=lambda x: x[0]):
        if groups and ang - groups[-1][0][-1] <= 3.0:
            groups[-1][0].append(ang)
            groups[-1][1].append(f"{l['handle']}/L{l['layer']}")
        else:
            groups.append(([ang], [f"{l['handle']}/L{l['layer']}"]))
    closing = _pair(_vertical(lines, X_WALL_E - 60, X_WALL_E + 5, (TURN_CORNER[1], Y_BAY_N)))
    return [(round(sum(a) / len(a), 2), ids) for a, ids in groups], closing


def well_risers(lines):
    rad = []
    for l in lines:
        a, b = l["a"], l["b"]
        ra, rb = math.dist(a, WELL_C), math.dist(b, WELL_C)
        lo, hi = min(ra, rb), max(ra, rb)
        if 1400 < lo < 1750 and 2650 < hi < 2850:
            inner = a if ra < rb else b
            outer = b if ra < rb else a
            ang_c = math.degrees(math.atan2(inner[1] - WELL_C[1], inner[0] - WELL_C[0])) % 360
            ang_l = math.degrees(math.atan2(outer[1] - inner[1], outer[0] - inner[0])) % 360
            axis = abs(outer[0] - inner[0]) < 0.5 or abs(outer[1] - inner[1]) < 0.5   # the straight treads
            if not axis and abs(((ang_l - ang_c + 180) % 360) - 180) < 4.0:
                rad.append((ang_c, l))
    groups = []
    for ang, l in sorted(rad, key=lambda x: x[0]):
        if groups and ang - groups[-1][0][-1] <= 2.5:
            groups[-1][0].append(ang)
            groups[-1][1].append(f"{l['handle']}/L{l['layer']}")
        else:
            groups.append(([ang], [f"{l['handle']}/L{l['layer']}"]))
    straight = _pair(_vertical(lines, STRAIGHT_X[0], STRAIGHT_X[1], STRAIGHT_Y, tol=60.0))
    cf2 = _pair(_horizontal(lines, CF2_X, CF2_Y[0], CF2_Y[1], tol=60.0))
    return [(round(sum(a) / len(a), 3), ids) for a, ids in groups], straight, cf2


# view, column / part, layers, element, role
MAIN_SPECS = [
    ("GFRS", "WEST", None, "A1-F1", "PRIMARY_STRUCTURAL"), ("GFRS", "TURN", None, "A1-W1", "PRIMARY_STRUCTURAL"),
    ("GFRS", "EAST", None, "A1-F2", "PRIMARY_STRUCTURAL"),
    ("FFRS", "WEST", None, "A2-F1", "PRIMARY_STRUCTURAL"), ("FFRS", "TURN", None, "A2-W1", "PRIMARY_STRUCTURAL"),
    ("FFRS", "EAST", None, "A2-F2", "PRIMARY_STRUCTURAL"),
    ("GBP", "WEST", None, "A1-F1", "REPEATED_VIEW_PARTIAL"), ("GBP", "EAST", None, "B-F1", "PRIMARY_STRUCTURAL"),
    ("ARCH-GF", "WEST", None, "A1-F1", "PRIMARY_ARCH"), ("ARCH-GF", "TURN", None, "A1-W1", "PRIMARY_ARCH"),
    ("ARCH-GF", "EAST", ("2",), "A1-F2", "PRIMARY_ARCH (overhead, hidden lines)"),
    ("ARCH-GF", "EAST", ("5",), "B-F1", "PRIMARY_ARCH (visible)"),
    ("ARCH-1F", "WEST", None, "A2-F1", "PRIMARY_ARCH"), ("ARCH-1F", "TURN", None, "A2-W1", "PRIMARY_ARCH"),
    ("ARCH-1F", "EAST", None, "A2-F2", "PRIMARY_ARCH"),
    ("ARCH-2F", "WEST", None, "A2-F1", "REPEATED_VIEW"), ("ARCH-2F", "TURN", None, "A2-W1", "REPEATED_VIEW"),
    ("ARCH-2F", "EAST", None, "A2-F2", "REPEATED_VIEW"),
]
WELL_SPECS = [("GFRS", "PRIMARY_STRUCTURAL"), ("ARCH-1F", "PRIMARY_ARCH"), ("ARCH-GF", "SECOND_VIEW"),
              ("GBP", "REPEATED_VIEW_PARTIAL")]


def recount(views):
    evidence, counts = [], {}
    for view, part, layers, el, role in MAIN_SPECS:
        ls = views[view]
        if part in ("WEST", "EAST"):
            span = WEST_TREAD if part == "WEST" else EAST_TREAD
            rs = _pair_span(_horizontal(ls, span, 15800.0, 19500.0, layers))
            r = [(p, ids) for p, ids, _, _ in rs]
            pos = [p for p, _ in r]
            counts[(view, el, part)] = {"risers": len(r), "radial": 0, "closing": 0, "positions": pos,
                                        "pitches": RS.pitches(pos), "role": role,
                                        "line_span": [(lo, hi) for _, _, lo, hi in rs]}
            for i, (p, ids) in enumerate(r, 1):
                evidence.append({"VIEW": view, "ELEMENT_ID": el, "PART": part, "ROLE": role, "RISER_IN_PART": i,
                                 "POSITION_MM": _r(p, 3), "LINES": ids,
                                 "LINE_KIND": "PAIR (nosing + riser face)" if len(ids) > 1 else "SINGLE LINE"})
        else:
            rad, closing = turn_risers(ls)
            counts[(view, el, part)] = {"risers": len(rad) + len(closing), "radial": len(rad),
                                        "closing": len(closing), "positions": [a for a, _ in rad], "pitches": [],
                                        "role": role}
            for i, (a, ids) in enumerate(rad, 1):
                evidence.append({"VIEW": view, "ELEMENT_ID": el, "PART": "TURN_RADIAL", "ROLE": role,
                                 "RISER_IN_PART": i, "POSITION_MM": None, "ANGLE_DEG": a, "LINES": ids,
                                 "LINE_KIND": "PAIR (nosing + riser face)" if len(ids) > 1 else "SINGLE LINE"})
            for i, (p, ids) in enumerate(closing, 1):
                evidence.append({"VIEW": view, "ELEMENT_ID": el, "PART": "TURN_CLOSING", "ROLE": role,
                                 "RISER_IN_PART": i, "POSITION_MM": _r(p, 3), "LINES": ids,
                                 "LINE_KIND": "PAIR (nosing + riser face)" if len(ids) > 1 else "SINGLE LINE"})
    for view, role in WELL_SPECS:
        rad, straight, cf2 = well_risers(views[view])
        for part, items, el in (("CURVED", rad, "C-F1"), ("STRAIGHT", straight, "C-F1"), ("SHORT", cf2, "C-F2")):
            counts[(view, el, part)] = {"risers": len(items), "positions": [p for p, _ in items],
                                        "pitches": RS.pitches([p for p, _ in items]), "role": role}
            for i, (p, ids) in enumerate(items, 1):
                evidence.append({"VIEW": view, "ELEMENT_ID": el, "PART": part, "ROLE": role, "RISER_IN_PART": i,
                                 "POSITION_MM": None if part == "CURVED" else _r(p, 3),
                                 "ANGLE_DEG": p if part == "CURVED" else None, "LINES": ids,
                                 "LINE_KIND": "PAIR (nosing + riser face)" if len(ids) > 1 else "SINGLE LINE"})
    for view, role in (("GBP", "PRIMARY_STRUCTURAL"), ("ARCH-GF", "PRIMARY_ARCH")):
        d = _pair(_vertical(views[view], ENTR_X[0], ENTR_X[1], (12211.856, 15011.856), tol=10.0))
        counts[(view, "D-F1", "FLIGHT")] = {"risers": len(d), "positions": [p for p, _ in d],
                                            "pitches": RS.pitches([p for p, _ in d]), "role": role}
        for i, (p, ids) in enumerate(d, 1):
            evidence.append({"VIEW": view, "ELEMENT_ID": "D-F1", "PART": "FLIGHT", "ROLE": role, "RISER_IN_PART": i,
                             "POSITION_MM": _r(p, 3), "LINES": ids,
                             "LINE_KIND": "PAIR (nosing + riser face)" if len(ids) > 1 else "SINGLE LINE"})
    return counts, evidence


def _c(counts, view, el, part):
    return counts.get((view, el, part), {}).get("risers")


def comparison_rows(counts):
    """storey runs: risers per segment and view, totals, uniform riser, landing level and the owner scenarios."""
    rows = []
    runs = {
        "A1": {"name": "main (service) stair GF -> 1F", "rise": OWNER["RISE_GF_1F_MM"], "bottom": OWNER["GF_FFL_M"],
               "views": [("STRUCTURAL GF roof sheet (GFRS)", "GFRS", "A1"), ("ARCHITECTURAL GF plan", "ARCH-GF", "A1")]},
        "A2": {"name": "main (service) stair 1F -> 2F", "rise": OWNER["RISE_1F_2F_MM"], "bottom": OWNER["1F_FFL_M"],
               "views": [("STRUCTURAL 1F roof sheet (FFRS)", "FFRS", "A2"), ("ARCHITECTURAL 1F plan", "ARCH-1F", "A2"),
                         ("ARCHITECTURAL 2F plan (repeated view)", "ARCH-2F", "A2")]},
    }
    for run, spec in runs.items():
        for label, view, a in spec["views"]:
            f1 = _c(counts, view, f"{a}-F1", "WEST")
            t = counts[(view, f"{a}-W1", "TURN")]
            f2 = _c(counts, view, f"{a}-F2", "EAST")
            n = f1 + t["risers"] + f2
            h = RS.uniform_riser(spec["rise"], n)
            land = spec["bottom"] + (f1 + t["risers"]) * h / 1000.0
            rows.append({"STOREY_RUN": run, "STAIR": spec["name"], "SOURCE": label, "VIEW": view,
                         "FLIGHT_1_RISERS": f1, "TURN_RADIAL": t["radial"], "TURN_CLOSING": t["closing"],
                         "TURN_RISERS": t["risers"], "FLIGHT_2_RISERS": f2, "TOTAL_RISERS": n,
                         "UNIFORM_RISER_MM": _r(h, 6), "BLONDEL_2R_PLUS_G_MM": _r(SG.blondel(h, GOING_MM), 6),
                         "IN_OWNER_RANGE_150_160": OWNER["PREFERRED_RISER_MM"][0] <= h <= OWNER["PREFERRED_RISER_MM"][1],
                         "HALF_LANDING_FFL_M_IF_UNIFORM": _r(land, 6), "KIND": "DRAWN_COUNT"})
        sec = SECTION_AA_FACTS[f"{run}-F2"][0]
        rows.append({"STOREY_RUN": run, "STAIR": spec["name"], "SOURCE": SECTION_AA, "VIEW": "SECTION A-A",
                     "FLIGHT_2_RISERS": sec, "KIND": "DRAWN_COUNT (upper flight only)",
                     "NOTE": SECTION_AA_FACTS[f"{run}-F2"][1]})
        for sc, n in OWNER["SCENARIOS"][run].items():
            h = RS.uniform_riser(spec["rise"], n)
            rows.append({"STOREY_RUN": run, "STAIR": spec["name"], "SOURCE": f"OWNER SCENARIO {sc}", "VIEW": "-",
                         "TOTAL_RISERS": n, "UNIFORM_RISER_MM": _r(h, 6),
                         "BLONDEL_2R_PLUS_G_MM": _r(SG.blondel(h, GOING_MM), 6),
                         "IN_OWNER_RANGE_150_160": OWNER["PREFERRED_RISER_MM"][0] <= h <= OWNER["PREFERRED_RISER_MM"][1],
                         "KIND": OWNER_SCENARIO})
        rows.append({"STOREY_RUN": run, "STAIR": spec["name"], "SOURCE": "counts in the owner range (150 - 160 mm)",
                     "VIEW": "-", "TOTAL_RISERS": RS.counts_in_range(spec["rise"], *OWNER["PREFERRED_RISER_MM"]),
                     "KIND": "ARITHMETIC"})
    for view in ("GFRS", "ARCH-1F", "ARCH-GF"):
        cu, st, sh = (_c(counts, view, "C-F1", "CURVED"), _c(counts, view, "C-F1", "STRAIGHT"),
                      _c(counts, view, "C-F2", "SHORT"))
        n = cu + st + sh
        h = RS.uniform_riser(OWNER["RISE_GF_1F_MM"], n)
        rows.append({"STOREY_RUN": "C", "STAIR": "round (light-well) stair GF -> 1F", "SOURCE": view, "VIEW": view,
                     "FLIGHT_1_RISERS": cu + st, "FLIGHT_1_PARTS": f"curved {cu} + straight {st}",
                     "FLIGHT_2_RISERS": sh, "TOTAL_RISERS": n, "UNIFORM_RISER_MM": _r(h, 6),
                     "BLONDEL_2R_PLUS_G_MM": _r(SG.blondel(h, GOING_MM), 6),
                     "IN_OWNER_RANGE_150_160": OWNER["PREFERRED_RISER_MM"][0] <= h <= OWNER["PREFERRED_RISER_MM"][1],
                     "HALF_LANDING_FFL_M_IF_UNIFORM": _r(OWNER["GF_FFL_M"] + (cu + st) * h / 1000.0, 6),
                     "KIND": "DRAWN_COUNT" if counts[(view, "C-F1", "CURVED")]["role"] != "SECOND_VIEW"
                     else "DRAWN_COUNT (second view)"})
    for view in ("GBP", "ARCH-GF"):
        rows.append({"STOREY_RUN": "B", "STAIR": "lobby steps +1.00 -> +0.30", "SOURCE": view, "VIEW": view,
                     "TOTAL_RISERS": _c(counts, view, "B-F1", "EAST"),
                     "UNIFORM_RISER_MM": _r(700.0 / _c(counts, view, "B-F1", "EAST"), 6), "KIND": "DRAWN_COUNT"})
        rows.append({"STOREY_RUN": "D", "STAIR": "entrance steps +0.15 -> +1.00", "SOURCE": view, "VIEW": view,
                     "TOTAL_RISERS": _c(counts, view, "D-F1", "FLIGHT"),
                     "UNIFORM_RISER_MM": _r(850.0 / _c(counts, view, "D-F1", "FLIGHT"), 6), "KIND": "DRAWN_COUNT"})
    return rows


# ------------------------------------------------------------------ scenarios
def scenarios(counts):
    """riser arrangements: the drawn ones (one per complete view) and the owner's (placed only where a drawing places
    them)."""
    g, a1, a2 = counts, "GFRS", "ARCH-1F"
    sc = {
        "A1-OWNER_A-28": {"run": "A1", "bottom": 1.00, "top": 5.50, "lane": OWNER_SCENARIO,
                          "basis": "owner scenario A; the structural GF roof sheet draws this arrangement",
                          "segments": [("A1-F1", RS.FLIGHT, _c(g, a1, "A1-F1", "WEST")),
                                       ("A1-W1", RS.WINDERS, g[(a1, "A1-W1", "TURN")]["risers"]),
                                       ("A1-L1", RS.LANDING, 0), ("A1-F2", RS.FLIGHT, _c(g, a1, "A1-F2", "EAST"))]},
        "A1-OWNER_B-29": {"run": "A1", "bottom": 1.00, "top": 5.50, "lane": OWNER_SCENARIO,
                          "basis": "owner scenario B; no drawing places a 29th riser (allocation not drawn)",
                          "segments": [("A1 (allocation not drawn)", RS.FLIGHT, 29)]},
        "A1-ARCH_GF-25": {"run": "A1", "bottom": 1.00, "top": 5.50, "lane": CONFLICT,
                          "basis": "architectural GF plan (10 / 4 / 11)",
                          "segments": [("A1-F1", RS.FLIGHT, _c(g, "ARCH-GF", "A1-F1", "WEST")),
                                       ("A1-W1", RS.WINDERS, g[("ARCH-GF", "A1-W1", "TURN")]["risers"]),
                                       ("A1-L1", RS.LANDING, 0),
                                       ("A1-F2", RS.FLIGHT, _c(g, "ARCH-GF", "A1-F2", "EAST"))]},
        "A2-OWNER_A-27": {"run": "A2", "bottom": 5.50, "top": 9.70, "lane": OWNER_SCENARIO,
                          "basis": "owner scenario A; the architectural 1F plan draws this arrangement",
                          "segments": [("A2-F1", RS.FLIGHT, _c(g, a2, "A2-F1", "WEST")),
                                       ("A2-W1", RS.WINDERS, g[(a2, "A2-W1", "TURN")]["risers"]),
                                       ("A2-L1", RS.LANDING, 0), ("A2-F2", RS.FLIGHT, _c(g, a2, "A2-F2", "EAST"))]},
        "A2-OWNER_B-26": {"run": "A2", "bottom": 5.50, "top": 9.70, "lane": OWNER_SCENARIO,
                          "basis": "owner scenario B; no drawing places 26 risers (allocation not drawn)",
                          "segments": [("A2 (allocation not drawn)", RS.FLIGHT, 26)]},
        "A2-FFRS-24": {"run": "A2", "bottom": 5.50, "top": 9.70, "lane": CONFLICT,
                       "basis": "structural 1F roof sheet and architectural 2F plan: NW quarter flat, closing riser only",
                       "segments": [("A2-F1", RS.FLIGHT, _c(g, "FFRS", "A2-F1", "WEST")),
                                    ("A2-W1 (flat quarter)", RS.LANDING, 0),
                                    ("A2-W1 closing riser", RS.WINDERS, g[("FFRS", "A2-W1", "TURN")]["risers"]),
                                    ("A2-L1", RS.LANDING, 0), ("A2-F2", RS.FLIGHT, _c(g, "FFRS", "A2-F2", "EAST"))]},
        "C-DRAWN-28": {"run": "C", "bottom": 1.00, "top": 5.50, "lane": SOURCE_VERIFIED,
                       "basis": "structural GF roof sheet = architectural 1F plan (12 curved + 11 straight / landing / 5)",
                       "segments": [("C-F1", RS.FLIGHT, _c(g, a1, "C-F1", "CURVED") + _c(g, a1, "C-F1", "STRAIGHT")),
                                    ("C-L1", RS.LANDING, 0), ("C-F2", RS.FLIGHT, _c(g, a1, "C-F2", "SHORT"))]},
    }
    check(sum(n for _, _, n in sc["A1-OWNER_A-28"]["segments"]) == 28, "owner A (GF -> 1F) = the GFRS arrangement")
    check(sum(n for _, _, n in sc["A2-OWNER_A-27"]["segments"]) == 27, "owner A (1F -> 2F) = the arch 1F arrangement")
    check(sum(n for _, _, n in sc["C-DRAWN-28"]["segments"]) == 28, "light-well stair: 28 drawn risers")
    return sc


def schedule_rows(sc):
    rows = []
    for sid, s in sc.items():
        r = RS.schedule(s["bottom"], s["top"], s["segments"])
        land = {x["after_riser"]: x for x in r["landings"]}
        for x in r["rows"]:
            rows.append({"SCENARIO": sid, "LANE": s["lane"], "RISER": x["riser"], "SEGMENT": x["segment"],
                         "KIND": x["kind"], "RISES_ONTO": x["onto"], "FINISHED_RISER_MM": _r(x["finished_riser_mm"], 6),
                         "FINISHED_LEVEL_AFTER_M": _r(x["finished_mm"] / 1000.0, 6),
                         "LANDING_AFTER": land[x["riser"]]["segment"] if x["riser"] in land else ""})
    return rows


FINISH_GRID = (30.0, 50.0, 80.0, 100.0)   # floor build-up f = FFL - SSL (mm): NOT ESTABLISHED; a reading grid only


def finish_rows(sc):
    rows = [{"SCENARIO": "GENERAL", "FORMULA": "finished riser h = (FFL_top - FFL_bottom) / n (uniform); concrete "
             "tread k = FFL_bottom + k h - s; first concrete riser = h + f_b - s; last = h - f_t + s; every other = h "
             "(landings with the tread finish); sum of concrete risers = n h - f_t + f_b",
             "STATE": "EQUATION", "NOTE": "f_b, f_t: FFL - structural slab level at the bottom / top floor; s: stair "
             "finish on a tread (marble + bedding)"}]
    s = OWNER["MARBLE_MM"]
    for sid, x in sc.items():
        if "allocation not drawn" in x["segments"][0][0]:
            continue
        h = (x["top"] - x["bottom"]) * 1000.0 / sum(n for _, _, n in x["segments"])
        for f in FINISH_GRID:
            r = RS.schedule(x["bottom"], x["top"], x["segments"], {"floor_bottom": f, "floor_top": f, "tread": s})
            c = [y["concrete_riser_mm"] for y in r["rows"]]
            first, last = RS.first_last(h, f, f, s)
            check(abs(c[0] - first) < 1e-9 and abs(c[-1] - last) < 1e-9, "closed form = schedule")
            rows.append({"SCENARIO": sid, "FLOOR_BUILD_UP_MM": f, "STAIR_FINISH_MM": s, "FINISHED_RISER_MM": _r(h, 6),
                         "FIRST_CONCRETE_RISER_MM": _r(first, 6), "LAST_CONCRETE_RISER_MM": _r(last, 6),
                         "OTHER_CONCRETE_RISERS_MM": _r(h, 6),
                         "SUM_CONCRETE_RISERS_MM": _r(math.fsum(c), 6),
                         "STATE": OWNER_SCENARIO + (" (p.16 typical +4.00 / +3.95 S.S.L reads 50; N.I.S.)" if f == 50
                                                    else ""),
                         "NOTE": "the floor build-up is not printed; s = 30 mm marble, bedding not confirmed"})
        fb, ft = RS.offsets_for(h, 200.0, 100.0, s)
        rows.append({"SCENARIO": sid, "FIRST_CONCRETE_RISER_MM": 200.0, "LAST_CONCRETE_RISER_MM": 100.0,
                     "STAIR_FINISH_MM": s, "FINISHED_RISER_MM": _r(h, 6),
                     "REQUIRED_FLOOR_BUILD_UP_BOTTOM_MM": _r(fb, 6), "REQUIRED_FLOOR_BUILD_UP_TOP_MM": _r(ft, 6),
                     "STATE": "NOT_SUPPORTED",
                     "NOTE": "a 200 / 100 first / last pair would need different floor build-ups top and bottom; no "
                             "drawing gives them, so the pair is not imposed"})
    return rows


# ------------------------------------------------------------------ geometry and quantities
def s87_geometry():
    return {r["ELEMENT_ID"]: r for r in _rows(READ["S87_GEOMETRY"])}


def flight_geometry(n, h, width, waist):
    f = SG.straight_flight(n, h, GOING_MM, width, waist)
    return {"run_mm": f["run"], "pitch_deg": f["pitch_deg"], "plan_m2": f["PLAN_PROJECTED_AREA"] / 1e6,
            "inclined_len_mm": f["inclined_waist_length"], "inclined_m2": f["INCLINED_WAIST_SURFACE_AREA"] / 1e6,
            "volume_m3": f["STAIR_CONCRETE_VOLUME"] / 1e9,
            "waist_m3": f["run"] / math.cos(math.radians(f["pitch_deg"])) * waist * width / 1e9,
            "steps_m3": (n - 1) * GOING_MM * h / 2.0 * width / 1e9}


WINDER_GOING_MM = math.pi / 2 * WIDTH_MAIN_MM / 2 / 4     # walking line at mid-width through the four winder treads


def quantity_rows(sc, geo):
    """concrete per element and scenario (waist 160 sensitivity); the bars of the one explicit family (8Ø16/m)."""
    t = OWNER["WAIST_SENSITIVITY_MM"]
    conc, bars, wl = [], [], []
    kg16 = kg_per_m(16)
    for sid, s in sc.items():
        n_total = sum(n for _, _, n in s["segments"])
        h = (s["top"] - s["bottom"]) * 1000.0 / n_total
        if "allocation not drawn" in s["segments"][0][0]:
            conc.append({"SCENARIO": sid, "ELEMENT_ID": s["segments"][0][0], "LANE": BLOCKED, "RISERS": n_total,
                         "RISER_MM": _r(h, 6), "CONCRETE_M3": None,
                         "REASON": "no drawing places the extra / missing riser: no per-flight geometry"})
            bars.append({"SCENARIO": sid, "ELEMENT_ID": s["segments"][0][0], "ROLE": "MAIN_BOTTOM",
                         "BAR_DIAMETER_MM": 16, "LANE": BLOCKED, "KG": None, "REASON": "no per-flight geometry"})
            continue
        lane = OWNER_SCENARIO if s["lane"] != CONFLICT else CONFLICT
        for seg, kind, n in s["segments"]:
            el = seg.split(" ")[0]
            if kind == RS.FLIGHT and el != "C-F1":
                width = WIDTH_MAIN_MM if el.startswith("A") else 1200.0
                fg = flight_geometry(n, h, width, t)
                conc.append({"SCENARIO": sid, "ELEMENT_ID": el, "KIND": "FLIGHT", "LANE": lane, "RISERS": n,
                             "RISER_MM": _r(h, 6), "GOING_MM": GOING_MM, "WIDTH_MM": width,
                             "RUN_MM": _r(fg["run_mm"], 6), "PITCH_DEG": _r(fg["pitch_deg"], 6),
                             "INCLINED_LENGTH_MM": _r(fg["inclined_len_mm"], 6),
                             "PLAN_PROJECTED_M2": _r(fg["plan_m2"]), "INCLINED_SOFFIT_M2": _r(fg["inclined_m2"]),
                             "WAIST_MM": t, "WAIST_M3": _r(fg["waist_m3"]), "STEPS_M3": _r(fg["steps_m3"]),
                             "CONCRETE_M3": _r(fg["volume_m3"]),
                             "METHOD": "stair_geometry.straight_flight, plumb cuts at the first and last riser line"})
                wl.append((sid, el, fg))
                bars.append({"SCENARIO": sid, "ELEMENT_ID": el, "ROLE": "MAIN_BOTTOM (8Ø16/m plan callout)",
                             "BAR_DIAMETER_MM": 16, "LANE": lane,
                             "EQUIVALENT_LENGTH_M": _r(RS.bar_length_rate(8, width, fg["inclined_len_mm"])),
                             "KG": _r(RS.bar_length_rate(8, width, fg["inclined_len_mm"]) * kg16),
                             "FORMULA": f"8 /m x {_full(width / 1000)} m x inclined {_full(fg['inclined_len_mm'] / 1000)} "
                                        f"m x {_full(kg16)} kg/m; anchorage and laps excluded (blocked)"})
            elif kind == RS.FLIGHT and el == "C-F1":
                a = float(geo["C-F1"]["PLAN_PROJECTED_AREA_M2"])
                v = RS.winder_plane_volume(a, h, GOING_MM, t)
                conc.append({"SCENARIO": sid, "ELEMENT_ID": el, "KIND": "CURVED + STRAIGHT FLIGHT", "LANE": lane,
                             "RISERS": n, "RISER_MM": _r(h, 6), "PLAN_PROJECTED_M2": _r(a), "WAIST_MM": t,
                             "CONCRETE_M3": _r(v), "METHOD": "plane-equivalent A x (t / cos(pitch) + h / 2) over the "
                                                             "S8.7 plan outline (approximation for the curved part)"})
                bars.append({"SCENARIO": sid, "ELEMENT_ID": el, "ROLE": "MAIN_BOTTOM (8Ø16/m plan callouts)",
                             "BAR_DIAMETER_MM": 16, "LANE": BLOCKED, "KG": None,
                             "REASON": "bar run along the curve not established (S8.7)"})
            elif kind == RS.WINDERS and n >= 3:
                a = float(geo[el]["PLAN_PROJECTED_AREA_M2"])
                v = RS.winder_plane_volume(a, h, WINDER_GOING_MM, t)
                conc.append({"SCENARIO": sid, "ELEMENT_ID": el, "KIND": "WINDER TURN", "LANE": lane, "RISERS": n,
                             "RISER_MM": _r(h, 6), "GOING_MM": _r(WINDER_GOING_MM, 6), "PLAN_PROJECTED_M2": _r(a),
                             "WAIST_MM": t, "CONCRETE_M3": _r(v),
                             "METHOD": "plane-equivalent A x (t / cos(pitch) + h / 2), walking line at mid-width "
                                       "(approximation: the winder soffit is not drawn)"})
                bars.append({"SCENARIO": sid, "ELEMENT_ID": el, "ROLE": "MAIN_BOTTOM (8Ø16/m plan callouts)",
                             "BAR_DIAMETER_MM": 16, "LANE": BLOCKED, "KG": None,
                             "REASON": "winder soffit form and bar paths not established"})
            elif kind == RS.LANDING or (kind == RS.WINDERS and n < 3):
                key = el if el in geo else None
                if key is None or "closing" in seg:
                    continue
                a = float(geo[key]["PLAN_PROJECTED_AREA_M2"])
                conc.append({"SCENARIO": sid, "ELEMENT_ID": seg, "KIND": "LANDING / FLAT QUARTER", "LANE": lane,
                             "PLAN_PROJECTED_M2": _r(a), "WAIST_MM": t, "CONCRETE_M3": _r(a * t / 1000.0),
                             "METHOD": "flat plate: outline x 160"})
        if s["run"] == "A2":
            a = float(geo["A2-T1"]["PLAN_PROJECTED_AREA_M2"])
            conc.append({"SCENARIO": sid, "ELEMENT_ID": "A2-T1", "KIND": "TOP ARRIVAL STRIP", "LANE": lane,
                         "PLAN_PROJECTED_M2": _r(a), "WAIST_MM": t, "CONCRETE_M3": _r(a * t / 1000.0),
                         "METHOD": "flat plate (released by S8.7)"})
        if s["run"] == "C":
            a = float(geo["C-T1"]["PLAN_PROJECTED_AREA_M2"])
            conc.append({"SCENARIO": sid, "ELEMENT_ID": "C-T1", "KIND": "TOP ARRIVAL", "LANE": lane,
                         "PLAN_PROJECTED_M2": _r(a), "WAIST_MM": t, "CONCRETE_M3": _r(a * t / 1000.0),
                         "METHOD": "flat plate (released by S8.7)"})
    released = {"A1-L1", "A2-T1", "C-T1"}
    for r in conc:
        r["ALREADY_RELEASED_BY_S8_7"] = r["ELEMENT_ID"] in released
    totals, unrel = defaultdict(float), defaultdict(float)
    for r in conc:
        if r.get("CONCRETE_M3") is not None:
            totals[r["SCENARIO"]] += r["CONCRETE_M3"]
            if not r["ALREADY_RELEASED_BY_S8_7"]:
                unrel[r["SCENARIO"]] += r["CONCRETE_M3"]
    for sid in sc:
        if sid in totals:
            lane = CONFLICT if sc[sid]["lane"] == CONFLICT else OWNER_SCENARIO
            conc.append({"SCENARIO": sid, "ELEMENT_ID": "TOTAL (whole stair, incl. the S8.7 plates)", "LANE": lane,
                         "CONCRETE_M3": _r(totals[sid]), "METHOD": "sum of the rows above"})
            conc.append({"SCENARIO": sid, "ELEMENT_ID": "TOTAL NOT RELEASED (scenario only)", "LANE": lane,
                         "CONCRETE_M3": _r(unrel[sid]), "METHOD": "sum of the rows not released by S8.7; never "
                                                                  "released by S8.7A"})
    return conc, bars, wl


def family_rows(binding):
    explicit = sorted({r["SOURCE_HANDLE"] for r in binding if "8%%C16/m" in (r.get("CALLOUT") or "")
                       or r.get("CALLOUT", "").startswith("8")})
    fams = [
        ("8Ø16/m", "MAIN_BOTTOM along the flights and both ways in the landings", 16,
         "EXPLICIT: nine plan callouts on the GF / 1F roof sheets with bar lines across the flights, the winder "
         "quarters and the landings (GFRS 490 / 491 / 48F / 5BC / 537 / 53D, FFRS 748 / 749 / 747); also on p.16",
         "released by S8.7 over the three plates only (59.020862261 kg); flights and winders blocked with their "
         "geometry"),
        ("6Ø14/m", "TOP bars over each flight / landing junction, bent to the pitch", 14,
         "TYPICAL ONLY (p.16 N.I.S.); no plan callout", BLOCKED),
        ("6Ø12/m", "LANDING TOP layer", 12, "TYPICAL ONLY (p.16)", BLOCKED),
        ("Ø12/20cm", "DISTRIBUTION transverse on the main bars along the waist", 12, "TYPICAL ONLY (p.16)", BLOCKED),
        ("Ø8/15cm", "STEP BAR inside each step", 8, "TYPICAL ONLY (p.16)", BLOCKED),
        ("1Ø12", "NOSING CORNER BAR in each step", 12, "TYPICAL ONLY (p.16)", BLOCKED),
        ("6Ø16/m", "STARTER from the ground beam into the first flight", 16,
         "TYPICAL ONLY (p.16); the project's flight foot support is not drawn", BLOCKED),
        ("2Ø12 / 4Ø16 (20 x 40)", "LANDING EDGE BEAM", 12,
         "TYPICAL ONLY (p.16); the project's landings end on S6 beams (BL033 / BL023 / BL028 / BL017)", BLOCKED),
        ("3Ø14 / 4Ø16 / 2Ø14/30 / Ø8/15", "GROUND BEAM G.B under the first flight (30 wide on 50 x 10 blinding)", 16,
         "TYPICAL ONLY (p.16)", BLOCKED),
        ("2Ø12 / 4Ø16 / 6Ø8/m, depth AS PER SCH.", "TYPICAL DETAIL OF STAIR BEAM (cranked, column to column)", 16,
         "TYPICAL ONLY (p.16, owner images 6 / 7); the stair-edge beams are S6 occurrences ('With Stair' B3-BL033, "
         "B3-BL023, CB3-BL022), blocked in S6 (UNDEFINED_CANDIDATE_DETAIL)", "OWNED_BY_S6 (blocked there)"),
        ("anchorage / development / laps / bends", "every family", None,
         "NOT DIMENSIONED on any drawing", BLOCKED),
    ]
    return [{"FAMILY": a, "ROLE": b, "BAR_DIAMETER_MM": c, "ASSIGNMENT": d, "STATE": e,
             "S8_7_BINDING_HANDLES": explicit if a == "8Ø16/m" else []} for a, b, c, d, e in fams]


# ------------------------------------------------------------------ beams, S6, S7
def beam_bands(src):
    import alsenan_structural_s1 as S1
    out = {}
    for sh in ("GFRS", "FFRS"):
        segs, _, _ = S1.beam_linework(src, sh)
        for ln in S1.beam_lines(S1.straight_bands(segs)):
            d = tuple(float(v) for v in ln["dir"])
            n = tuple(float(v) for v in ln["normal"])
            o, w, t0, t1 = float(ln["offset"]), float(ln["width_mm"]), float(ln["t0"]), float(ln["t1"])
            pts = [(d[0] * t + n[0] * (o + s * w / 2), d[1] * t + n[1] * (o + s * w / 2))
                   for t, s in ((t0, -1), (t1, -1), (t1, 1), (t0, 1))]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            out[(sh, ln["line_id"])] = (min(xs), min(ys), max(xs), max(ys))
    return out


def beam_rows(geo, bands, counts):
    occ = _rows(READ["S6_OCC"])
    by_line = defaultdict(list)
    for o in occ:
        for g in json.loads(o["geometry_objects"] or "[]"):
            m = re.fullmatch(r"SPAN:(\w+):(BL\d+):(\d+)-(\d+)", g)
            if m:
                by_line[(m.group(1), m.group(2))].append((int(m.group(3)), int(m.group(4)), o))
    rows = []
    for el, r in sorted(geo.items()):
        for t in json.loads(r["BEAM_BANDS_TOUCHING"] or "[]"):
            key = (r["SHEET"], t["beam_line"])
            bb = json.loads(r["PLAN_POLYGON_BBOX_MM"])
            band = bands.get(key)
            spans = []
            for lo, hi, o in by_line.get(key, []):
                if band is None:
                    continue
                along_y = (band[3] - band[1]) > (band[2] - band[0])
                e0, e1 = (bb[1], bb[3]) if along_y else (bb[0], bb[2])
                if lo < e1 + 150 and hi > e0 - 150:
                    spans.append(f"{o['occurrence_id']} ({o['mark'] or '-'}, {o['occurrence_state']}, "
                                 f"{o['known_kg'] or 0} kg)")
            rows.append({"ELEMENT_ID": el, "SHEET": r["SHEET"], "BEAM_LINE": t["beam_line"],
                         "BAND_BBOX_MM": [_r(v, 3) for v in band] if band else None,
                         "PLAN_OVERLAP_M2": t["overlap_m2"], "S6_OCCURRENCES": spans,
                         "ROLE": _beam_role(el, t["beam_line"], r["SHEET"]),
                         "OWNER": "S6 / S6.1 (beam family)", "S8_7A": "read; nothing added or moved"})
    # head beams against the last riser of each upper flight
    for sh, line, el, view_counts in (("GFRS", "BL020", "A1-F2", ("GFRS", "ARCH-GF")),
                                      ("FFRS", "BL009", "A2-F2", ("FFRS", "ARCH-1F"))):
        b = bands[(sh, line)]
        for v in view_counts:
            last = min(lo for lo, _ in counts[(v, el, "EAST")]["line_span"])      # the riser-face line
            inside = b[1] - 1 < last < b[3] + 1
            rows.append({"ELEMENT_ID": el, "SHEET": sh, "BEAM_LINE": line, "BAND_BBOX_MM": [_r(x, 3) for x in b],
                         "ROLE": f"HEAD BEAM: last riser of {el} on {v} at y {_full(last, 3)}",
                         "LAST_RISER_INSIDE_BEAM_BAND": inside,
                         "S8_7A": ("the last riser lies inside the head beam's plan width: the top tread would sit below "
                                   "the floor level over the beam (physically inconsistent unless the beam is lowered)"
                                   if inside else f"the last riser stops {_full(last - b[3], 3)} mm short of the head "
                                                  "beam face; the floor (over the beam) is the arrival")})
    s7 = _rows(READ["S87_S7"])
    rows.append({"ELEMENT_ID": "S7 stair-adjacent supports", "SHEET": "GFRS / FFRS", "BEAM_LINE": "-",
                 "S6_OCCURRENCES": [], "ROLE": "S7 top extensions at stair-zone supports",
                 "OWNER": "S7 (released, frozen)",
                 "S8_7A": f"{len(s7)} strip ends, {_full(math.fsum(float(r['KG_FROM_BAR_RUNS']) for r in s7))} kg "
                          "(S8.7 recompute, unchanged); no stair bar released at these supports"})
    return rows


def _beam_role(el, line, sheet):
    roles = {("GFRS", "BL033"): "north edge of the GF -> 1F bay (S6 'With Stair' B3)",
             ("FFRS", "BL023"): "north edge of the 1F -> 2F bay (S6 'With Stair' B3)",
             ("GFRS", "BL020"): "head beam B20 at the 1F floor edge (south of the bay)",
             ("FFRS", "BL009"): "head beam B23 at the 2F floor edge (south of the bay)",
             ("GFRS", "BL022"): "south edge of the light-well straight flight (S6 'With Stair' CB3)",
             ("GFRS", "BL015"): "beam CA across the light-well straight flight (level not stated, Q-ST-10)",
             ("GFRS", "BL028"): "east edge of the bay (B7 / B2)", ("FFRS", "BL017"): "east edge of the bay (B7 / B2)",
             ("GFRS", "BL016"): "west edge of the bay", ("FFRS", "BL019"): "west edge of the bay",
             ("GFRS", "BL001"): "east edge of the light-well short flight", ("GFRS", "BL039"): "north edge B29"}
    return roles.get((sheet, line), "edge member")


# ------------------------------------------------------------------ registers
QUESTIONS = {
    "Q-ST7A-01": ("architect", "GF -> 1F main stair: confirm the riser count and the foot of the lower flight. The "
                  "structural GF roof sheet draws 12 + 4 + 12 = 28 risers (first riser at y 16162); the architectural "
                  "GF plan and the ground-beam plan start the lower flight two risers later (y 16762) and the "
                  "architectural plan ends the upper flight one riser earlier: 10 + 4 + 11 = 25 (180 mm)."),
    "Q-ST7A-02": ("engineer / architect", "GF -> 1F upper flight: the structural sheet's 12th riser (y 16112) lies "
                  "inside the 400 mm head beam B20 (y 15912 - 16312). Is the beam lowered under the top tread, or does "
                  "the flight end at y 16412 as on the architectural plans (11 risers, 100 mm short of the beam)?"),
    "Q-ST7A-03": ("architect", "Half-landing GF -> 1F: section A-A gives +3.50 ('320' above the +0.30 lobby). With 28 "
                  "uniform risers the landing is at +3.571; with the architectural 25 at +3.520. Which governs, and is "
                  "'320' to the finished or the structural landing?"),
    "Q-ST7A-04": ("architect / engineer", "1F -> 2F main stair: the architectural 1F plan draws a four-riser winder "
                  "turn (27 risers, 155.6 mm); the structural 1F roof sheet and the 2F plan draw the NW quarter flat "
                  "(24 risers, 175 mm); section A-A draws 12 risers in the upper flight where every plan draws 11. "
                  "Confirm the turn and the riser count."),
    "Q-ST7A-05": ("owner / architect", "Owner scenario B (29 / 26 risers) is not drawn anywhere: where would the extra "
                  "(or missing) riser go, and would the going or the landing change?"),
    "Q-ST7A-06": ("architect", "Floor build-up (screed + tile / marble) at GF, 1F and 2F, and the stair finish with "
                  "bedding: needed for the first and last concrete risers (h + f_b - s and h - f_t + s)."),
    "Q-ST7A-07": ("engineer", "Waist thickness: p.16 shows 'THICK' with no value; the 'T 16' plan tags sit in the winder "
                  "quarter and on the light-well flight. Is 160 mm the waist (normal to the soffit) or only the slab "
                  "thickness of the zone?"),
    "Q-ST7A-08": ("engineer", "Winder soffit form (warped soffit or a flat slab under the winders) and the bar paths "
                  "through the turn."),
    "Q-ST7A-09": ("engineer", "Which p.16 typical bars apply to these stairs (6Ø14/m junction top bars, 6Ø12/m landing "
                  "top, Ø12/20 distribution, Ø8/15 step bars, 1Ø12 nosing bar), and the anchorage / laps of the 8Ø16/m "
                  "main bars into the beams."),
    "Q-ST7A-10": ("engineer", "Support at the foot of each lower flight (ground beam per p.16, ground slab or a beam), "
                  "and the stair beams at the bay edges (S6 'With Stair' beams are blocked for their detail)."),
    "Q-ST7A-11": ("architect", "Light-well (round) stair: the corner landing level is not printed; with 28 uniform "
                  "risers it is at +4.696. Confirm, and the level of beam CA under the straight part."),
}


def conflict_rows(counts, comp):
    a1 = {r["VIEW"]: r for r in comp if r["STOREY_RUN"] == "A1" and r["KIND"] == "DRAWN_COUNT"}
    a2 = {r["VIEW"]: r for r in comp if r["STOREY_RUN"] == "A2" and r["KIND"] == "DRAWN_COUNT"}
    rows = [
        ("SC-01", "A1-F1 foot", CONFLICT, f"GFRS {a1['GFRS']['FLIGHT_1_RISERS']} risers from y 16162 vs ARCH-GF "
         f"{a1['ARCH-GF']['FLIGHT_1_RISERS']} from y 16762 (GBP agrees with ARCH-GF on the foot)", "Q-ST7A-01"),
        ("SC-02", "A1-F2 head", CONFLICT, f"GFRS {a1['GFRS']['FLIGHT_2_RISERS']} (last at y 16112, inside head beam B20) "
         f"and SECTION A-A 12 vs ARCH-GF {a1['ARCH-GF']['FLIGHT_2_RISERS']} (last at y 16412)", "Q-ST7A-02"),
        ("SC-03", "A1 total", CONFLICT, f"GFRS {a1['GFRS']['TOTAL_RISERS']} (owner A) vs ARCH-GF "
         f"{a1['ARCH-GF']['TOTAL_RISERS']}; owner B 29 not drawn", "Q-ST7A-01, Q-ST7A-05"),
        ("SC-04", "A1-L1 level", CONFLICT, "section A-A +3.50 vs +3.571 (28 uniform) / +3.520 (25 uniform)",
         "Q-ST7A-03"),
        ("SC-05", "A2-W1 winders", CONFLICT, f"ARCH-1F {counts[('ARCH-1F', 'A2-W1', 'TURN')]['radial']} radial + "
         f"closing vs FFRS / ARCH-2F closing riser only", "Q-ST7A-04"),
        ("SC-06", "A2-F2 count", CONFLICT, f"every plan {a2['ARCH-1F']['FLIGHT_2_RISERS']} vs SECTION A-A 12 (a 12th "
         "riser would fall inside head beam B23)", "Q-ST7A-04"),
        ("SC-07", "A2 total", CONFLICT, f"ARCH-1F {a2['ARCH-1F']['TOTAL_RISERS']} (owner A) vs FFRS / ARCH-2F "
         f"{a2['FFRS']['TOTAL_RISERS']}; owner B 26 not drawn", "Q-ST7A-04, Q-ST7A-05"),
        ("SC-08", "irregular goings (ARCH-GF A1-F1 top)", "DRAWING_FACT", "pitches "
         + ", ".join(_full(p, 1) for p in counts[("ARCH-GF", "A1-F1", "WEST")]["pitches"][-3:])
         + " mm above the cut plane (pairs incomplete)", "Q-ST7A-01"),
        ("SC-09", "waist thickness", BLOCKED, "p.16 'THICK' without a value; 'T 16' zone tags only", "Q-ST7A-07"),
        ("SC-10", "light-well corner landing level", BLOCKED, "not printed (+4.696 if 28 uniform risers)", "Q-ST7A-11"),
        ("SC-11", "floor and stair finishes", BLOCKED, "build-ups not printed; 30 mm marble owner scenario", "Q-ST7A-06"),
        ("SC-12", "counting method", "NOT_A_CONFLICT", "nosing and riser-face lines are pairs (50 mm apart): counted "
         "once; the landing-edge lines (flight 1 last riser, the closing riser, flight 2 first riser) are real risers "
         "and are each counted once; repeated views (GBP, ARCH-2F, ARCH-GF light well) are not extra stairs", "-"),
    ]
    return [{"ID": a, "ITEM": b, "STATE": c, "EVIDENCE": d, "QUESTIONS": e} for a, b, c, d, e in rows]


def reproduction_rows(views):
    """S8.7's released quantities rebuilt from the drawings without the S8.7 builder."""
    from shapely.geometry import Polygon, box
    s87c = {r["ELEMENT_ID"]: r for r in _rows(READ["S87_CONCRETE"])}
    s87b = [r for r in _rows(READ["S87_REBAR"]) if r["QUANTITY_STATE"] in ("PROJECT_BASIS_QTO", "SOURCE_DERIVED_PHYSICAL")]
    by = {(l["view"], l["handle"]): l for v in views.values() for l in v}
    slabs = {x["panel_id"]: Polygon(x["polygon_mm"]) for x in _j(READ["S1_SLABS"])["rows"]}
    import alsenan_structural_s1 as S1
    E = S1.Source().entities()
    eb = {e["handle"]: e for e in E["GFRS"]}
    north, wall, edge = eb["279"], eb["25A"], eb["25B"]          # bay north edge, central wall east face, landing edge
    check(abs(north["a"][1] - Y_BAY_N) < 0.01 and abs(wall["a"][0] - X_WALL_E) < 0.01 and
          abs(edge["a"][1] - Y_WALL_END) < 0.01, "A1-L1 edges")
    l1 = box(wall["a"][0], edge["a"][1], max(edge["a"][0], edge["b"][0]), north["a"][1])
    ffrs_last = min(p for p in [l["a"][1] for l in views["FFRS"] if abs(l["a"][1] - l["b"][1]) < 0.5
                                and abs(min(l["a"][0], l["b"][0]) - EAST_TREAD[0]) < 5 and 16000 < l["a"][1] < 19500])
    t1 = slabs["SP-1F_ROOF_SLAB-01"].intersection(box(X_WALL_E, Y_ZONE_S - 1.0, X_BAY_E, ffrs_last))
    rows = []
    t = 160.0
    plates = {"A1-L1": l1.area / 1e6, "A2-T1": t1.area / 1e6}
    from shapely.geometry import Polygon as P
    a, b = eb["2CF"], eb["289"]
    c, d = eb["2CE"], eb["315"]
    poly = P([(a["a"][0], d["a"][1]), (b["a"][0], d["a"][1]), (c["b"][0], c["b"][1]), (a["a"][0], c["a"][1])])
    plates["C-T1"] = poly.area / 1e6
    for el, area in plates.items():
        r87 = s87c[el]
        rows.append({"ITEM": f"{el} concrete", "S8_7_VALUE": float(r87["CONCRETE_M3"]),
                     "S8_7A_VALUE": _r(area * t / 1000.0), "S8_7_LANE": r87["LANE"],
                     "AGREES": abs(area * t / 1000.0 - float(r87["CONCRETE_M3"])) < 1e-9,
                     "METHOD": "outline rebuilt from the drawn lines x 160 (zone tag)"})
    for r in s87b:
        el = r["FLIGHT_OR_LANDING_ID"]
        L = 8 * plates[el]
        rows.append({"ITEM": f"{el} {r['PHYSICAL_BAR_ROLE']} Ø{r['BAR_DIAMETER_MM']}", "S8_7_VALUE": float(r["KG"]),
                     "S8_7A_VALUE": _r(L * kg_per_m(16)), "S8_7_LANE": r["QUANTITY_STATE"],
                     "AGREES": abs(L * kg_per_m(16) - float(r["KG"])) < 1e-9, "METHOD": "8 /m x plate area x 1.580246914"})
    tot_c = math.fsum(r["S8_7A_VALUE"] for r in rows if r["ITEM"].endswith("concrete"))
    tot_k = math.fsum(r["S8_7A_VALUE"] for r in rows if not r["ITEM"].endswith("concrete"))
    s = _j(READ["S87_SUMMARY"])["released"]
    rows.append({"ITEM": "released concrete total", "S8_7_VALUE": s["concrete_m3"], "S8_7A_VALUE": _r(tot_c),
                 "AGREES": abs(tot_c - s["concrete_m3"]) < 1e-9, "METHOD": "sum"})
    rows.append({"ITEM": "released Ø16 total", "S8_7_VALUE": s["kg"], "S8_7A_VALUE": _r(tot_k),
                 "AGREES": abs(tot_k - s["kg"]) < 1e-9, "METHOD": "sum"})
    corrections = [
        ("CR-01", "A1-L1 level", "S8.7 state DERIVED_FROM_PRINTED (+3.50)", "SOURCE_CONFLICT (+3.50 section vs +3.571 / "
         "+3.520 under uniform risers)", "none: the plate volume does not depend on its level"),
        ("CR-02", "A1-F2 outline", "S8.7 polygon to y 16112 (12 risers), 0.24 m2 over head beam B20", "any future "
         "release must stop at the beam face (y 16312) or at the last architectural riser (y 16412)",
         "none now (A1-F2 is not released); a latent double count with S6 B20 is recorded"),
        ("CR-03", "A2-T1 arrival strip", "released 0.0192 m3 / 1.517037037 kg on the plans' 11-riser A2-F2",
         "kept: a 12th riser (section A-A) would fall inside head beam B23, so the plans' arrangement is the "
         "physically consistent one", "none"),
        ("CR-04", "'T 16' tags", "S8.7: zone tag used for the landings", "the tags sit in the winder quarter (main) and "
         "on the straight flight (light well): a zone thickness, not landing-specific; the waist stays a sensitivity",
         "none"),
        ("CR-05", "C-F1 outline", "0.345 m2 over beam CA (BL015)", "latent double count with S6 CA if the flight is "
         "ever released; CA's level against the flight is still a question", "none now"),
        ("CR-06", "double counting of the releases", "three plates + 59.020862261 kg", "no overlap with S6 beams, S7 "
         "panels or S7 top extensions (rebuilt)", "none"),
    ]
    rows += [{"CORRECTION_ID": cid, "ITEM": item, "S8_7_VALUE": was, "S8_7A_VALUE": now, "AGREES": None,
              "METHOD": "correction layer (S8.7 unchanged)", "QUANTITY_CHANGE": change}
             for cid, item, was, now, change in corrections]
    return rows, plates


def waist_rows(sc, geo, E_tags):
    rows = [{"ITEM": "p.16 waist", "VALUE": None, "STATE": BLOCKED,
             "EVIDENCE": "'THICK' leader on the waist with no value (TYPICAL STEEL LAYOUT-STAIR SECTION, N.I.S.)"}]
    for sh, h, el, p in E_tags:
        rows.append({"ITEM": f"'T 16' tag {sh} {h}", "VALUE": 160.0, "STATE": "ZONE_TAG (S1 LOCAL_PANEL_NOTE)",
                     "EVIDENCE": f"insertion at ({_full(p[0], 1)}, {_full(p[1], 1)}): inside {el}; a slab-thickness "
                                 "tag for the stair zone, not a landing-only tag"})
    rows.append({"ITEM": "waist 160", "VALUE": 160.0, "STATE": OWNER_SCENARIO,
                 "EVIDENCE": "owner sensitivity; supported only by the zone tags; never released"})
    for sid, s in sc.items():
        if "allocation not drawn" in s["segments"][0][0]:
            continue
        r = RS.schedule(s["bottom"], s["top"], s["segments"])
        for L in r["landings"]:
            sec = SECTION_AA_FACTS["A1-L1_LEVEL_M"][0] if L["segment"] == "A1-L1" else None
            rows.append({"ITEM": f"{sid} {L['segment']} finished level", "VALUE": _r(L["finished_mm"] / 1000.0, 6),
                         "STATE": s["lane"], "EVIDENCE": f"after riser {L['after_riser']} of {r['n']} at "
                                                         f"{_full(r['riser_mm'], 6)} mm"
                         + (f"; section A-A {sec} (difference {_full((L['finished_mm'] / 1000.0 - sec) * 1000, 3)} mm)"
                            if sec else "")})
    for el in ("A1-L1", "A2-L1", "A2-T1", "C-L1", "C-T1", "A1-W1", "A2-W1"):
        rows.append({"ITEM": f"{el} plan area", "VALUE": float(geo[el]["PLAN_PROJECTED_AREA_M2"]),
                     "STATE": SOURCE_VERIFIED, "EVIDENCE": f"S8.7 outline on {geo[el]['SHEET']}"})
    return rows


def conservation(L):
    out = []

    def A(cid, text, ok, detail=""):
        out.append({"CHECK_ID": cid, "CHECK": text, "RESULT": "PASS" if ok else "FAIL", "DETAIL": detail})
    c, s87 = L["counts"], L["s87_treads"]
    A("C01", "the independent recount reproduces every S8.7 primary straight count",
      all(L["s87_match"].values()), json.dumps({k: v for k, v in L["s87_match"].items()}))
    arch = [r for r in L["evidence"] if r["VIEW"].startswith("ARCH") and r["PART"] in ("WEST", "EAST", "STRAIGHT",
                                                                                      "SHORT", "FLIGHT")]
    singles = Counter(f"{r['VIEW']}:{r['ELEMENT_ID']}" for r in arch if not r["LINE_KIND"].startswith("PAIR"))
    A("C02", "architectural flights: the 1F plan draws every riser as a nosing / riser-face pair; single lines occur "
      "only where one line per riser is drawn (overhead or above the cut on the GF plan, the first riser of the "
      "repeated 2F view); no riser holds more than three lines",
      all(len(r["LINES"]) <= 3 for r in arch) and not [k for k in singles if k.startswith("ARCH-1F")] and
      set(singles) <= {"ARCH-2F:A2-F1", "ARCH-GF:A1-F1", "ARCH-GF:A1-F2", "ARCH-GF:B-F1", "ARCH-GF:C-F1",
                       "ARCH-GF:C-F2", "ARCH-GF:D-F1"}, json.dumps(dict(sorted(singles.items()))))
    A("C03", "owner scenario A = a complete drawn arrangement (GF -> 1F: GFRS 28; 1F -> 2F: ARCH-1F 27)",
      sum(n for _, _, n in L["sc"]["A1-OWNER_A-28"]["segments"]) == 28 and
      sum(n for _, _, n in L["sc"]["A2-OWNER_A-27"]["segments"]) == 27, "")
    A("C04", "every riser schedule closes on the top floor level", all(
        abs(r["FINISHED_LEVEL_AFTER_M"] - L["sc"][r["SCENARIO"]]["top"]) < 1e-9
        for r in L["sched"] if r["RISES_ONTO"] == "TOP_FLOOR"), "")
    A("C05", "first / last concrete risers: closed form = schedule; concrete risers sum to SSL_top - SSL_bottom",
      all(abs(r["SUM_CONCRETE_RISERS_MM"] - L["rise_of"][r["SCENARIO"]] - r["FLOOR_BUILD_UP_MM"] + r["FLOOR_BUILD_UP_MM"])
          < 1e-6 for r in L["fin"] if r.get("SUM_CONCRETE_RISERS_MM") is not None), "")
    A("C06", "S8.7 released concrete and bars reproduced exactly from the drawings",
      all(r["AGREES"] for r in L["repro"] if r["AGREES"] is not None), "")
    A("C07", "nothing new released: scenario quantities are OWNER_SCENARIO / SOURCE_CONFLICT / BLOCKED only",
      not [r for r in L["conc"] if r["LANE"] in RELEASED_LANES] and not [r for r in L["bars"] if r["LANE"] in
                                                                       RELEASED_LANES], "")
    A("C08", "all 26 earlier freezes (incl. S8.7 and S8.8), the S8.3 errata and the register indexes verify",
      len(L["frozen"]) == 26, f"{len(L['frozen'])} manifests")
    A("C09", "the light-well stair counts 28 on both primary views", L["c_counts"] == [28, 28], json.dumps(L["c_counts"]))
    A("C10", "each owner image is recorded as supporting evidence only", len(OWNER_IMAGES) == 7, "")
    return out


# ------------------------------------------------------------------ build
def run():
    frozen, errata, index = verify_inputs()
    src, E, struct = structural_lines()
    T, arch = architectural_lines()
    views = {**struct, **arch}
    counts, evidence = recount(views)
    s87_treads = _rows(READ["S87_TREADS"])
    s87 = {(r["VIEW"], r["ASSIGNED_ELEMENT"]): r for r in s87_treads}
    s87_match = {}
    for (view, el, part), cnt in counts.items():
        if part in ("WEST", "EAST") and view in ("GFRS", "FFRS") and el.startswith("A"):
            want = [r for r in s87_treads if r["VIEW"] == view and r["ASSIGNED_ELEMENT"] == el
                    and r["KIND"] == "PARALLEL"]
            s87_match[f"{view}:{el}"] = len(want) == 1 and int(want[0]["LINES"]) == cnt["risers"]
    comp = comparison_rows(counts)
    sc = scenarios(counts)
    sched = schedule_rows(sc)
    fin = finish_rows(sc)
    geo = s87_geometry()
    conc, bars, _ = quantity_rows(sc, geo)
    binding = _rows(READ["S87_BINDING"])
    fams = family_rows(binding)
    bands = beam_bands(src)
    beams = beam_rows(geo, bands, counts)
    conflicts = conflict_rows(counts, comp)
    repro, plates = reproduction_rows(views)
    by = {(sh, e["handle"]): e for sh in E for e in E[sh]}
    tags = []
    for sh, h in (("GFRS", "580"), ("FFRS", "74A"), ("GFRS", "5B6")):
        p = next(x["p"] for x in _j(READ["S1_SLABS"])["rows"] for x in x["local_thickness_notes"]
                 if x["handle"].startswith(h + ":"))
        from shapely.geometry import Point, box
        inside = [k for k, r in geo.items() if r["SHEET"] == sh and
                  box(*json.loads(r["PLAN_POLYGON_BBOX_MM"])).buffer(1).contains(Point(p[0], p[1]))]
        tags.append((sh, h, ", ".join(inside), p))
    waist = waist_rows(sc, geo, tags)
    rise_of = {k: (v["top"] - v["bottom"]) * 1000.0 for k, v in sc.items()}
    c_counts = [next(r["TOTAL_RISERS"] for r in comp if r["STOREY_RUN"] == "C" and r["VIEW"] == v)
                for v in ("GFRS", "ARCH-1F")]
    L = {"frozen": frozen, "errata": errata, "index": index, "counts": counts, "evidence": evidence, "comp": comp,
         "sc": sc, "sched": sched, "fin": fin, "conc": conc, "bars": bars, "fams": fams, "beams": beams,
         "conflicts": conflicts, "repro": repro, "plates": plates, "waist": waist, "s87_treads": s87_treads,
         "s87_match": s87_match, "rise_of": rise_of, "c_counts": c_counts, "T": T}
    L["cons"] = conservation(L)
    check(all(x["RESULT"] == "PASS" for x in L["cons"]), "conservation: " + json.dumps(
        [x for x in L["cons"] if x["RESULT"] != "PASS"]))
    return L


def provenance(L):
    lines = []
    for r in L["comp"]:
        lines.append({"record": f"COUNT:{r['STOREY_RUN']}:{r['SOURCE']}", "total": r.get("TOTAL_RISERS"),
                      "kind": r["KIND"]})
    for r in L["conc"]:
        lines.append({"record": f"CONCRETE:{r['SCENARIO']}:{r['ELEMENT_ID']}", "lane": r["LANE"],
                      "m3": r.get("CONCRETE_M3"), "method": r.get("METHOD") or r.get("REASON")})
    for i in OWNER_IMAGES:
        lines.append({"record": f"OWNER_IMAGE:{i[0]}", "shows": i[1], "use": i[2],
                      "state": "SUPPORTING_VISUAL_EVIDENCE (not a registered input; not committed)"})
    lines.append({"record": "OWNER_INFORMATION", **{k: v for k, v in OWNER.items() if k != "SCENARIOS"},
                  "scenarios": OWNER["SCENARIOS"], "state": OWNER_SCENARIO})
    (HERE / OUTPUTS[13]).write_text("".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in lines),
                                    encoding="utf-8")


def write(L):
    _csv(OUTPUTS[1], L["comp"], ["STOREY_RUN", "STAIR", "SOURCE", "VIEW", "KIND", "FLIGHT_1_RISERS", "FLIGHT_1_PARTS",
                                 "TURN_RADIAL", "TURN_CLOSING", "TURN_RISERS", "FLIGHT_2_RISERS", "TOTAL_RISERS",
                                 "UNIFORM_RISER_MM", "BLONDEL_2R_PLUS_G_MM", "IN_OWNER_RANGE_150_160",
                                 "HALF_LANDING_FFL_M_IF_UNIFORM", "NOTE"])
    _csv(OUTPUTS[2], L["evidence"], ["VIEW", "ELEMENT_ID", "PART", "ROLE", "RISER_IN_PART", "POSITION_MM",
                                     "ANGLE_DEG", "LINES", "LINE_KIND"])
    _csv(OUTPUTS[3], L["sched"])
    _csv(OUTPUTS[4], L["fin"], ["SCENARIO", "FLOOR_BUILD_UP_MM", "STAIR_FINISH_MM", "FINISHED_RISER_MM",
                                "FIRST_CONCRETE_RISER_MM", "LAST_CONCRETE_RISER_MM", "OTHER_CONCRETE_RISERS_MM",
                                "SUM_CONCRETE_RISERS_MM", "REQUIRED_FLOOR_BUILD_UP_BOTTOM_MM",
                                "REQUIRED_FLOOR_BUILD_UP_TOP_MM", "STATE", "FORMULA", "NOTE"])
    _csv(OUTPUTS[5], L["waist"])
    _csv(OUTPUTS[6], L["conc"], ["SCENARIO", "ELEMENT_ID", "KIND", "LANE", "RISERS", "RISER_MM", "GOING_MM",
                                 "WIDTH_MM", "RUN_MM", "PITCH_DEG", "INCLINED_LENGTH_MM", "PLAN_PROJECTED_M2",
                                 "INCLINED_SOFFIT_M2", "WAIST_MM", "WAIST_M3", "STEPS_M3", "CONCRETE_M3",
                                 "ALREADY_RELEASED_BY_S8_7", "METHOD", "REASON"])
    _csv(OUTPUTS[7], [dict(r, RECORD="FAMILY") for r in L["fams"]] + [dict(r, RECORD="SCENARIO_KG") for r in L["bars"]],
         ["RECORD", "FAMILY", "ROLE", "BAR_DIAMETER_MM", "ASSIGNMENT", "STATE", "S8_7_BINDING_HANDLES", "SCENARIO",
          "ELEMENT_ID", "LANE", "EQUIVALENT_LENGTH_M", "KG", "FORMULA", "REASON"])
    _csv(OUTPUTS[8], L["beams"], ["ELEMENT_ID", "SHEET", "BEAM_LINE", "BAND_BBOX_MM", "PLAN_OVERLAP_M2",
                                  "S6_OCCURRENCES", "ROLE", "LAST_RISER_INSIDE_BEAM_BAND", "OWNER", "S8_7A"])
    _csv(OUTPUTS[9], L["conflicts"])
    _csv(OUTPUTS[10], [{"QUESTION_ID": k, "TO": v[0], "QUESTION": v[1]} for k, v in QUESTIONS.items()])
    _csv(OUTPUTS[11], L["repro"], ["ITEM", "S8_7_VALUE", "S8_7A_VALUE", "S8_7_LANE", "AGREES", "METHOD",
                                   "CORRECTION_ID", "QUANTITY_CHANGE"])
    provenance(L)
    _csv(OUTPUTS[14], L["cons"])
    s87s = _j(READ["S87_SUMMARY"])
    tot = {r["SCENARIO"]: r["CONCRETE_M3"] for r in L["conc"] if r["ELEMENT_ID"].startswith("TOTAL NOT RELEASED")}
    whole = {r["SCENARIO"]: r["CONCRETE_M3"] for r in L["conc"] if r["ELEMENT_ID"].startswith("TOTAL (whole")}
    kg = defaultdict(float)
    for r in L["bars"]:
        if r.get("KG"):
            kg[r["SCENARIO"]] += r["KG"]
    summary = {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}", "corrects": "research/alsenan_stairs_s8_7 (frozen; "
                                                                            "unchanged)",
        "counts": {f"{r['STOREY_RUN']}:{r['SOURCE']}": r.get("TOTAL_RISERS") for r in L["comp"]
                   if r.get("TOTAL_RISERS") is not None},
        "proposed_for_confirmation": {
            "A1": {"risers": 28, "riser_mm": _r(4500 / 28, 6), "basis": "owner scenario A = the structural GF roof "
                   "sheet's complete arrangement (12 / 4 / 12); the architectural GF plan draws 25", "state": CONFLICT},
            "A2": {"risers": 27, "riser_mm": _r(4200 / 27, 6), "basis": "owner scenario A = the architectural 1F plan's "
                   "complete arrangement (12 / 4 / 11); the structural 1F roof sheet and the 2F plan draw 24",
                   "state": CONFLICT},
            "C": {"risers": 28, "riser_mm": _r(4500 / 28, 6), "basis": "both primary views", "state": SOURCE_VERIFIED},
            "B": {"risers": 4, "riser_mm": 175.0, "state": SOURCE_VERIFIED},
            "D": {"risers": 5, "riser_mm": 170.0, "state": SOURCE_VERIFIED}},
        "owner_scenario_b": "not drawn anywhere (29 / 26): no per-flight geometry",
        "released": {"production": "unchanged (S8.7)", "concrete_m3": s87s["released"]["concrete_m3"],
                     "kg": s87s["released"]["kg"], "new_release_by_s8_7a": {"concrete_m3": 0.0, "kg": 0.0},
                     "awaiting": "owner approval before any production BOQ change"},
        "scenario_totals_never_released": {"concrete_m3": {k: _r(v) for k, v in sorted(tot.items())},
                                           "whole_stair_incl_s8_7_plates_m3": {k: _r(v) for k, v in
                                                                                sorted(whole.items())},
                                           "main_bar_kg_flights": {k: _r(v) for k, v in sorted(kg.items())}},
        "can_be_released_now": ["the three S8.7 plates and their 8Ø16/m bars (already released, reproduced)"],
        "cannot_be_released": ["every flight and winder turn (riser counts in conflict, waist not established)",
                               "every scenario quantity (OWNER_SCENARIO)", "typical-only p.16 bar families",
                               "anchorage, laps and bends", "the unlevelled landings (A2-L1, C-L1)"],
        "questions": sorted(QUESTIONS), "conservation": {x["CHECK_ID"]: x["RESULT"] for x in L["cons"]},
        "frozen_baselines": {k: v["manifest_sha256"] for k, v in L["frozen"].items()},
        "register_indexes": L["index"], "s8_3_errata_sha256": L["errata"], "unit_mass": UM.describe(UNIT_MASS),
        "owner_images": [i[0] for i in OWNER_IMAGES], "references_read": []}
    _json(OUTPUTS[12], summary)
    (HERE / OUTPUTS[0]).write_text(readme(summary, L), encoding="utf-8")
    manifest = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "DATED_CORRECTION_LAYER",
                "corrects": summary["corrects"], "s8_7_manifest_sha256": _sha(S87_MANIFEST),
                "engine_commit_stamp": summary["engine_commit"], "references_read": [],
                "code": {c_: _sha(ROOT / c_) for c_ in CODE},
                "inputs": {str(p_.relative_to(ROOT)): _sha(p_) for p_ in READ.values()},
                "drawing_sha256": {"P7757.dxf": ARCH_SHA, "ST7757.dxf": STRUCT_SHA, "ST7757.pdf": STRUCT_PDF_SHA,
                                   "P7757 sections PDF": ARCH_PDF_SHA},
                "frozen_baselines": summary["frozen_baselines"], "register_indexes": L["index"],
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "released": summary["released"],
                "rule": "S8.7 stays as history; this layer recounts, records owner scenarios and corrections with a "
                        "reason each, releases nothing new and is frozen before any earlier commercial figure is read"}
    _json(MANIFEST_NAME, manifest)
    for k, m_ in MANIFESTS.items():
        DR.verify_frozen(m_, ROOT)
    for o in OUTPUTS + [MANIFEST_NAME]:
        check(not HYGIENE.search((HERE / o).read_text(encoding="utf-8")), f"hygiene: {o}")
    return summary


def readme(s, L):
    comp = L["comp"]

    def row(run, view):
        r = next(x for x in comp if x["STOREY_RUN"] == run and x["VIEW"] == view and x["KIND"].startswith("DRAWN"))
        return r
    a1s, a1a = row("A1", "GFRS"), row("A1", "ARCH-GF")
    a2s, a2a, a2r = row("A2", "FFRS"), row("A2", "ARCH-1F"), row("A2", "ARCH-2F")
    tot = s["scenario_totals_never_released"]["concrete_m3"]

    def fl(r):
        return f"{r['FLIGHT_1_RISERS']} + {r['TURN_RISERS']} + {r['FLIGHT_2_RISERS']} = **{r['TOTAL_RISERS']}**"
    return f"""# S8.7A stair riser, finishing and structural-geometry correction audit

Round {ROUND}, baseline `{BASELINE_HEAD}`, engine `{s['engine_commit']}`. A dated correction layer over the frozen S8.7
package (`{MANIFEST_NAME}`, `references_read: []`). S8.7 is unchanged and its release stands. Nothing new is
released; the owner decides before any production BOQ change.

## Conclusions

1. **The disagreement is not a counting error.** The recount, done again from the DXFs without the S8.7 builder,
   reproduces S8.7's counts. The method:
   - each architectural nosing line and the hidden riser face behind it are one riser;
   - the three landing-edge lines are real risers: flight 1's last riser, the closing riser of the turn, and flight
     2's first riser;
   - the ground-beam plan and the 2F plan are repeated views.

   The drawings themselves disagree:

   | GF -> 1F (4.50 m) | flight 1 + turn + flight 2 | riser |
   |---|---|---|
   | structural GF roof sheet | {fl(a1s)} | {_full(a1s['UNIFORM_RISER_MM'], 3)} mm |
   | architectural GF plan | {fl(a1a)} | {_full(a1a['UNIFORM_RISER_MM'], 3)} mm |
   | section A-A (upper flight) | 12 | - |

   | 1F -> 2F (4.20 m) | flight 1 + turn + flight 2 | riser |
   |---|---|---|
   | architectural 1F plan | {fl(a2a)} | {_full(a2a['UNIFORM_RISER_MM'], 3)} mm |
   | structural 1F roof sheet | {fl(a2s)} | {_full(a2s['UNIFORM_RISER_MM'], 3)} mm |
   | architectural 2F plan (repeated view) | {fl(a2r)} | {_full(a2r['UNIFORM_RISER_MM'], 3)} mm |
   | section A-A (upper flight) | 12 | - |

   The turn is three radial winder risers plus the closing riser into the landing. The structural 1F roof sheet and
   the 2F plan omit the radial winder lines.
2. **Owner scenario A is a complete drawn arrangement for each storey.** GF -> 1F 28 is the structural GF roof sheet
   (160.714 mm); 1F -> 2F 27 is the architectural 1F plan (155.556 mm). They are proposed for confirmation, not
   selected. Owner scenario B (29 / 26) is not drawn anywhere.

   Against the owner's 150 - 160 mm preference:
   - 28 risers give 160.714 mm, 0.714 mm over the range; 29 (155.172) and 30 fit.
   - For 1F -> 2F, 27 (155.556) and 28 (150.0) fit; 26 gives 161.538 mm.
3. **Physical checks.**
   - The structural sheet's 12th upper-flight riser (y 16112) lies inside the 400 mm head beam B20. The architectural
     plans end both upper flights at y 16412, 100 mm short of the head beam, and section A-A's 12th riser in the
     1F -> 2F upper flight would also fall inside its head beam.
   - With 28 uniform risers the GF -> 1F half-landing is at +3.571. Section A-A gives +3.50.
4. **The round (light-well) stair is consistent.** It has 28 risers on both primary views (12 curved + 11 straight,
   the corner landing, then 5): 160.714 mm, with the corner landing at +4.696 if the risers are uniform.
5. **First and last risers.** Uniform finished risers give a first concrete riser of h + f_b - s, a last of
   h - f_t + s, and every other riser h. The floor build-up is not printed, so `04` evaluates a grid. A worked example
   for GF -> 1F with 28 risers and 30 mm marble:
   - with 50 mm floor build-up, the first concrete riser is 180.714 mm and the last 140.714 mm;
   - with 30 mm (equal to the marble), every concrete riser is 160.714 mm.

   A 200 / 100 pair would need 69.3 mm of floor build-up at the bottom and 90.7 mm at the top. No drawing gives
   those, so the pair is not imposed.
6. **Waist.** It is not established (p.16 'THICK' carries no value). The 'T 16' tags are zone tags lying in the
   winder quarter and on the light-well flight. 160 mm stays a sensitivity.
7. **Bars.** Only 8Ø16/m is explicitly assigned on the project plans. Every other p.16 family is typical only and
   blocked, as are anchorage and laps.
8. **S8.7 release.** {_full(s['released']['concrete_m3'])} m3 and {_full(s['released']['kg'])} kg are reproduced
   exactly from the drawings. No double count was found. Two latent overlaps are recorded for any future flight
   release: A1-F2 over beam B20, and C-F1 over beam CA.

## Scenario concrete not yet released (waist 160 sensitivity; S8.7 plates excluded; never released here)

{chr(10).join(f'- {k}: {_full(v, 6)} m3' for k, v in tot.items())}

## Files

`01` comparison, `02` line evidence, `03` riser schedule, `04` first / last risers, `05` waist and landings, `06`
concrete, `07` bars, `08` beams and S6 / S7, `09` conflicts, `10` questions, `11` reproduction and corrections, `12`
release summary.
"""


def main():
    L = run()
    s = write(L)
    print(json.dumps({"counts": s["counts"], "released": s["released"],
                      "scenario_totals": s["scenario_totals_never_released"]}, indent=1))


if __name__ == "__main__":
    main()
