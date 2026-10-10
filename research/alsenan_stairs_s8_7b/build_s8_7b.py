"""S8.7B - staircase owner scenario and engineering reconciliation. A research scenario layer over the frozen S8.7
package and the S8.7A correction layer (both read, never written). Source-controlled and blind: frozen before any
earlier commercial figure is read. Release delta: 0 m3 concrete and 0 kg reinforcement.

    python3 -I research/alsenan_stairs_s8_7b/build_s8_7b.py

Reads the registered drawings again, with its own code (not the S8.7 / S8.7A builders):
- ST7757.dxf: every stair line, callout, column outline and the head-beam edges read with ezdxf from model space;
  only the sheet frames come from the frozen S1 reader (and its beam bands, for the edge members);
- P7757.dxf with ezdxf, each plan registered onto the structural frame by the frozen S8.6 translations, and the
  printed LEVEL texts of the three plans;
- section A-A (P7757 sections PDF sheet 4): rendered at 600 dpi by pdftoppm into a temporary folder (never kept) and
  measured: the level chain calibrates the scale; the slab, landing and tread lines give the landing levels and the
  riser counts of the four flights the section shows;
- ST7757.pdf p.16 (no vector text): the typical stair section and the typical stair beam, recorded as a visual record.
The frozen S8.7 / S8.7A outputs are read only to cross-check counts, released plates and ownership.

The owner's four decisions enter as a provisional research scenario: GF -> 1F 28 risers, 1F -> 2F 27 risers, the
structural waist UNKNOWN (engineer to confirm) and a 30 mm stair finish (bedding not included unless confirmed).
Nothing is approved, selected or released.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import subprocess
import sys
import tempfile
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
from engine.source import stair_scenario_checks as SC  # noqa: E402

ROUND = "S8_7B"
DATE = "2026-10-10"
BASELINE_HEAD = "303df68"
POLICY = "S8_7B_OWNER_SCENARIO_ENGINEERING_RECONCILIATION_V1"
R = ROOT / "research"
BY_SHA = ROOT / "data/inputs/by_sha256"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
STRUCT_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
STRUCT_PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
ARCH_PDF_SHA = "1e7087d3e61bbb682c9107193c97550a2837e5198bde0ee311319bf7f4a08459"
S87 = R / "alsenan_stairs_s8_7"
S87A = R / "alsenan_stairs_s8_7a"
S87_MANIFEST = S87 / "17_S8_7_FREEZE_MANIFEST.json"
S87A_MANIFEST = S87A / "15_S8_7A_CORRECTION_MANIFEST.json"
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
             "S8.7A": S87A_MANIFEST,
             "S8.8": R / "alsenan_lift_s8_8/18_S8_8_FREEZE_MANIFEST.json"}
S83_ERRATA = R / "alsenan_dome_ring_s8_3/errata"
S1D = R / "alsenan_structural_census_s1"
INDEXES = {"S1": (S1D / "INDEX.json", "registers"), "S2": (R / "alsenan_structural_s2/INDEX.json", "outputs"),
           "S3": (R / "alsenan_column_rebar_s3/INDEX.json", "outputs"),
           "S3.1": (R / "alsenan_column_rebar_s3_1/INDEX.json", "outputs")}
READ = {"S87_GEOMETRY": S87 / "06_PLAN_AND_INCLINED_GEOMETRY.csv",
        "S87_CONCRETE": S87 / "07_CONCRETE_QTO.csv",
        "S87_BINDING": S87 / "08_REBAR_ANNOTATION_BINDING.csv",
        "S87_REBAR": S87 / "09_REBAR_QTO.csv",
        "S87_OWNERSHIP": S87 / "10_OWNERSHIP_AUDIT.csv",
        "S87_S7": S87 / "11_S7_STAIR_ADJACENT_RECOMPUTE.csv",
        "S87_SUMMARY": S87 / "16_S8_7_SUMMARY.json",
        "S87A_COUNTS": S87A / "01_RISER_COUNT_COMPARISON.csv",
        "S87A_SUMMARY": S87A / "12_RELEASE_SUMMARY.json",
        "S6_OCC": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCES.csv",
        "S86_REGISTRATION": R / "alsenan_lintels_s8_6/03_ARCH_STRUCTURAL_REGISTRATION.csv"}
CODE = ["engine/source/stair_scenario_checks.py", "engine/source/stair_riser_schedule.py",
        "engine/source/stair_geometry.py", "engine/source/rebar_unit_mass.py", "engine/source/delta_release.py",
        "research/alsenan_stairs_s8_7b/build_s8_7b.py", "research/external_engine_lab/alsenan_structural_s1.py"]
OUTPUTS = ["00_README.md", "01_OWNER_SCENARIO_ASSUMPTION_REGISTER.csv", "02_RISER_CALCULATION_TABLE.csv",
           "03_RISER_SETTING_OUT_SCHEDULE.csv", "04_LANDING_ELEVATION_RECONCILIATION.csv",
           "05_STRUCTURAL_ARCHITECTURAL_CONFLICT_MATRIX.csv", "06_BEAM_INTERFERENCE_AUDIT.csv",
           "07_FIRST_LAST_RISER_FINISH_BUILDUP.csv", "08_WAIST_THICKNESS_CONCRETE_SENSITIVITY.csv",
           "09_REINFORCEMENT_OWNERSHIP_AUDIT.csv", "10_ENGINEER_RFI_REGISTER.csv",
           "11_CONSERVATION_NO_DOUBLE_COUNT_CHECKS.csv", "12_PLAN_RISER_LINE_EVIDENCE.csv",
           "13_SECTION_AND_DETAIL_EVIDENCE.csv", "14_RELEASE_SUMMARY.json", "15_PROVENANCE.jsonl"]
MANIFEST_NAME = "16_S8_7B_FREEZE_MANIFEST.json"
UNIT_MASS = {"method": UM.D2_OVER_162, "authority": "project-wide method used by S3.1 / S6.1 / S7 / S8",
             "selected_by": "Urban (project basis)"}
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")

# ------------------------------------------------------------------ status vocabulary
PROV_OWNER = "PROVISIONAL_OWNER_SCENARIO"
ENGINEER = "REQUIRES_ENGINEER_CONFIRMATION"
WITH_CONFLICT = "PROVISIONAL_SCENARIO_WITH_CONFLICT"
SENS = "RESEARCH_SENSITIVITY_NOT_RELEASED"
COND = "CONDITIONAL_ESTIMATE_NOT_RELEASED"
NULL = "NOT_COMPUTABLE"
BLOCKED = "BLOCKED_UNQUANTIFIED"
CONFLICT = "SOURCE_CONFLICT"
VERIFIED = "SOURCE_VERIFIED"
PRINTED = "PRINTED_ON_DRAWING"
SCALED = "SCALED_FROM_SECTION_1_100 (indicative)"
INFERRED = "INFERRED_NOT_PRINTED"
TYPICAL = "TYPICAL_ONLY (N.I.S.)"
EXPLICIT = "PROJECT_SPECIFIC_EXPLICIT"
UNVERIFIED = "UNVERIFIED_ENGINEERING_INTERPRETATION"
ILLUSTRATIVE = "ILLUSTRATIVE_NOT_PROJECT_FACT"
ALREADY = "ALREADY_RELEASED_BY_S8_7 (frozen; not counted again)"
RELEASED_LANES = ("SOURCE_VERIFIED_RELEASED", "PROJECT_BASIS_QTO")

# ------------------------------------------------------------------ owner decisions (provisional research scenario)
OWNER = {"A1_RISERS": 28, "A2_RISERS": 27, "WAIST_MM": None, "STAIR_FINISH_MM": 30.0, "BEDDING_MM": None,
         "PREFERRED_RISER_MM": (150.0, 160.0)}
FFL_MM = {"GF": 1000.0, "1F": 5500.0, "2F": 9700.0}
WAISTS_MM = (150.0, 160.0, 175.0, 200.0)
FLOOR_BUILD_UPS_MM = (30.0, 50.0, 80.0, 100.0)      # illustrative only: no build-up is printed
TREAD_BUILD_UPS = ((30.0, 0.0, "marble 30 + bedding 0 (only if the 30 mm is confirmed to include bedding)"),
                   (30.0, 20.0, "marble 30 + bedding 20 (illustrative)"),
                   (30.0, 30.0, "marble 30 + bedding 30 (illustrative)"))
GOING_MM = 300.0
WIDTH_MAIN_MM = 1200.0          # bay edge to the central wall face; the tread lines are 1150 long
TREAD_LINE_MM = 1150.0

# ------------------------------------------------------------------ cited geometry (structural sheet-local mm)
X_BAY_W, X_WALL_W, X_WALL_E, X_BAY_E = 17087.904, 18287.904, 18387.904, 19587.904
Y_TURN, Y_BAY_N, Y_WALL_END = 19461.856, 20611.856, 19411.856
WEST_X, EAST_X = (17087.904, 18237.904), (18437.904, 19587.904)
WELL_C = (23673.334, 11742.299)
STRAIGHT_X, STRAIGHT_Y = (23700.0, 26800.0), (9011.856, 10161.856)
CF2_X, CF2_Y = (26757.904, 27907.904), (10150.0, 11450.0)
ENTR_X, ENTR_Y = (14250.0, 15600.0), (12211.856, 15011.856)
HEAD_BEAM_EDGES = {"B20": ("GFRS", "458", "2C6"), "B23": ("FFRS", "5E4", "5E1")}   # raw DXF edge lines (layer 1)
PAIR_TOL = 60.0

# ------------------------------------------------------------------ section A-A (600 dpi pixel windows, cited)
SEC = {"page": 4, "dpi": 600, "dark": 140, "crop": (1500, 3700, 3900, 2900),
       "chain_bottom": (6450, 6560, 1500, 5400), "chain_top": (3700, 3880, 1500, 5400),
       "chain_bottom_levels_m": (0.00, 9.70, 13.90, 14.40), "chain_top_levels_m": (1.00, 5.50, 9.70),
       "landing": {"A1": (5800, 6050, 1800, 2800), "A2": (5800, 6050, 2900, 4100)},
       "cut": {"A1": (2550, 3120, 4950, 5800), "A2": (3560, 4110, 4950, 5800)},
       "seen": {"A1": (1990, 2620, 4950, 6350), "A2": (3060, 3620, 4950, 6350)}}
P16_FACTS = [  # visual record of ST7757.pdf p.16, read from 100 / 300 dpi renders this round (not kept)
    ("P16-01", "TYPICAL STEEL LAYOUT-STAIR SECTION (N.I.S.)", "waist", "'THICK' with a dimension leader across the "
     "waist of both flights; no value", TYPICAL),
    ("P16-02", "TYPICAL STEEL LAYOUT-STAIR SECTION (N.I.S.)", "goings", "'30' on the treads", TYPICAL),
    ("P16-03", "TYPICAL STEEL LAYOUT-STAIR SECTION (N.I.S.)", "generic levels", "landing S.S.L +2.00 on a 0.00 -> "
     "4.00 storey: a schematic half-landing, not a project level", TYPICAL),
    ("P16-04", "TYPICAL STEEL LAYOUT-STAIR SECTION (N.I.S.)", "head", "'+4.00' at the top of the last concrete step; "
     "'+3.95 S.S.L' on the slab beyond the head beam (50 mm; meaning not stated)", TYPICAL),
    ("P16-05", "TYPICAL STEEL LAYOUT-STAIR SECTION (N.I.S.)", "foot", "'+0.00 T.O.B' on the ground beam G.B and "
     "'-0.05 S.S.L' on the slab beside it (50 mm; meaning not stated)", TYPICAL),
    ("P16-06", "TYPICAL STEEL LAYOUT-STAIR SECTION (N.I.S.)", "bars", "8Ø16/m bottom along the waist and the landing; "
     "6Ø14/m top at the junctions and the head; 6Ø12/m landing top; Ø12/20cm distribution; Ø8/15 step bars; 1Ø12 "
     "nosing bar; 6Ø16/m starter into the G.B", TYPICAL),
    ("P16-07", "TYPICAL STEEL LAYOUT-STAIR SECTION (N.I.S.)", "landing edge beam", "20 x 40: 2Ø12 top, 4Ø16 bottom",
     TYPICAL),
    ("P16-08", "TYPICAL STEEL LAYOUT-STAIR SECTION (N.I.S.)", "ground beam G.B", "30 wide (depth not dimensioned) on "
     "a 50 x 10 blinding: 3Ø14 top, 4Ø16 bottom, 2Ø14/30cm sides, Ø8/15cm stirrups", TYPICAL),
    ("P16-09", "TYPICAL DETAIL OF STAIR BEAM", "cranked beam", "column to column, cranked to follow the stair: 2Ø12 "
     "top, 4Ø16 bottom, 6Ø8/m stirrups, depth 'AS PER SCH.' on both the inclined and the level part", TYPICAL),
]


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
    s = f"{v:.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
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


# ------------------------------------------------------------------ drawing reads (own code)
def structural_read():
    """model-space LINE / TEXT / ARC / closed LWPOLYLINE entities of GBP / GFRS / FFRS in sheet-local mm. The frozen
    S1 reader supplies only the sheet frames (and, separately, the beam bands)."""
    import alsenan_structural_s1 as S1
    src = S1.Source()
    frames = {k: src.sheets[k]["frame"] for k in ("GBP", "GFRS", "FFRS")}

    def sheet(x, y):
        for k, f in frames.items():
            if f[0] <= x <= f[2] and f[1] <= y <= f[3]:
                return k
        return None
    lines, texts, arcs, polys = (defaultdict(list) for _ in range(4))
    for e in src.msp:
        t = e.dxftype()
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            sh = sheet(a.x, a.y)
            if sh:
                f = frames[sh]
                lines[sh].append({"view": sh, "handle": e.dxf.handle, "layer": e.dxf.layer,
                                  "a": (a.x - f[0], a.y - f[1]), "b": (b.x - f[0], b.y - f[1])})
        elif t in ("TEXT", "MTEXT"):
            p = e.dxf.insert
            sh = sheet(p.x, p.y)
            if sh:
                f = frames[sh]
                txt = e.dxf.text if t == "TEXT" else e.text
                texts[sh].append({"handle": e.dxf.handle, "layer": e.dxf.layer, "text": (txt or "").strip(),
                                  "p": (p.x - f[0], p.y - f[1])})
        elif t == "ARC":
            c = e.dxf.center
            sh = sheet(c.x, c.y)
            if sh:
                f = frames[sh]
                arcs[sh].append({"handle": e.dxf.handle, "layer": e.dxf.layer, "c": (c.x - f[0], c.y - f[1]),
                                 "r": float(e.dxf.radius), "a0": float(e.dxf.start_angle),
                                 "a1": float(e.dxf.end_angle)})
        elif t == "INSERT":
            p = e.dxf.insert
            sh = sheet(p.x, p.y)
            if sh:
                f = frames[sh]
                try:
                    subs = list(e.virtual_entities())
                except Exception:
                    subs = []
                for v in subs:
                    if v.dxftype() in ("TEXT", "MTEXT"):
                        q = v.dxf.insert
                        txt = v.dxf.text if v.dxftype() == "TEXT" else v.text
                        texts[sh].append({"handle": e.dxf.handle, "layer": v.dxf.layer, "text": (txt or "").strip(),
                                          "p": (q.x - f[0], q.y - f[1]), "via_insert": True})
        elif t == "LWPOLYLINE" and e.closed and e.dxf.layer.upper().startswith("S-COL"):
            pts = [(p[0], p[1]) for p in e.get_points("xy")]
            sh = sheet(sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
            if sh:
                f = frames[sh]
                polys[sh].append({"handle": e.dxf.handle, "layer": e.dxf.layer,
                                  "pts": [(p[0] - f[0], p[1] - f[1]) for p in pts]})
    return src, frames, lines, texts, arcs, polys


def architectural_read():
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
    lines, levels = {}, []
    for fl, (tx, ty) in sorted(T.items()):
        cand = [b for b in frames if b[0] + tx <= win[0] and b[1] + ty <= win[1] and b[2] + tx >= win[2]
                and b[3] + ty >= win[3]]
        check(len(cand) == 1, f"{fl}: one plan frame registers onto its structural sheet")
        fr = cand[0]
        ls = []
        for e in msp:
            t = e.dxftype()
            if t == "LINE" and e.dxf.layer in ("2", "5"):
                a, b = (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)
                if fr[0] <= a[0] <= fr[2] and fr[1] <= a[1] <= fr[3]:
                    ls.append({"view": f"ARCH-{fl}", "handle": e.dxf.handle, "layer": e.dxf.layer,
                               "a": (a[0] + tx, a[1] + ty), "b": (b[0] + tx, b[1] + ty)})
            elif t == "TEXT" and e.dxf.layer == "LEVEL":
                p = e.dxf.insert
                if fr[0] <= p.x <= fr[2] and fr[1] <= p.y <= fr[3]:
                    levels.append({"plan": f"ARCH-{fl}", "handle": e.dxf.handle, "text": e.dxf.text.strip(),
                                   "p": (p.x + tx, p.y + ty)})
        lines[f"ARCH-{fl}"] = ls
    return T, lines, levels


# ------------------------------------------------------------------ plan recount (own code)
def _ang(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0


def _rid(l):
    return f"{l['handle']}/L{l['layer']}"


def _h_lines(ls, x_span, y_lo, y_hi, layers=None, tol=5.0):
    out = []
    for l in ls:
        (ax, ay), (bx, by_) = l["a"], l["b"]
        if abs(ay - by_) <= 0.5 and (not layers or l["layer"] in layers) and y_lo <= ay <= y_hi \
                and abs(min(ax, bx) - x_span[0]) <= tol and abs(max(ax, bx) - x_span[1]) <= tol:
            out.append((ay, l))
    return out


def _v_lines(ls, x_lo, x_hi, y_span, layers=None, tol=5.0):
    out = []
    for l in ls:
        (ax, ay), (bx, by_) = l["a"], l["b"]
        if abs(ax - bx) <= 0.5 and (not layers or l["layer"] in layers) and x_lo <= ax <= x_hi \
                and abs(min(ay, by_) - y_span[0]) <= tol and abs(max(ay, by_) - y_span[1]) <= tol:
            out.append((ax, l))
    return out


def _risers(found, walk):
    """pair the drawn lines into risers (nosing + riser face within 60 mm = one riser), in walking order. The riser
    face is the hidden layer-2 line of a pair (the nosing projects towards the walker), else the line itself."""
    by_id = {_rid(l): (o, l) for o, l in found}
    pairs = RS.pair_lines([(o, _rid(l)) for o, l in found], PAIR_TOL)
    out = []
    for pos, ids in pairs:
        offs = [by_id[i][0] for i in ids]
        face_c = [by_id[i][0] for i in ids if by_id[i][1]["layer"] == "2"] or offs
        face = (max(face_c) if walk > 0 else min(face_c)) if len(ids) > 1 else offs[0]
        out.append({"pos": pos, "ids": ids, "face": face, "kind": "PAIR (nosing + riser face)" if len(ids) > 1
                    else "SINGLE LINE"})
    return sorted(out, key=lambda r: walk * r["pos"])


def _turn(ls):
    rad = []
    for l in ls:
        a, b = l["a"], l["b"]
        if not all(X_BAY_W - 40 <= p[0] <= X_WALL_E + 10 and Y_TURN - 10 <= p[1] <= Y_BAY_N + 50 for p in (a, b)):
            continue
        g = _ang(a, b)
        if (5 < g < 85 or 95 < g < 175) and math.dist(a, b) > 1000:
            rad.append((g, l))
    groups = []
    for g, l in sorted(rad, key=lambda x: (x[0], x[1]["handle"])):
        if groups and g - groups[-1]["angles"][-1] <= 3.0:
            groups[-1]["angles"].append(g)
            groups[-1]["lines"].append(l)
        else:
            groups.append({"angles": [g], "lines": [l]})
    closing = _risers(_v_lines(ls, X_WALL_E - 60, X_WALL_E + 5, (Y_TURN, Y_BAY_N)), +1)
    rad_out = []
    for gr in sorted(groups, key=lambda gr: -sum(gr["angles"]) / len(gr["angles"])):    # walking order 180 -> 90
        ls_ = gr["lines"]
        a = (sum(l["a"][0] for l in ls_) / len(ls_), sum(l["a"][1] for l in ls_) / len(ls_))
        b = (sum(l["b"][0] for l in ls_) / len(ls_), sum(l["b"][1] for l in ls_) / len(ls_))
        rad_out.append({"angle": round(sum(gr["angles"]) / len(gr["angles"]), 3), "ids": [_rid(l) for l in ls_],
                        "mean_line": (a, b), "kind": "PAIR (nosing + riser face)" if len(ls_) > 1 else "SINGLE LINE"})
    return rad_out, closing


def _well(ls):
    rad = []
    for l in ls:
        a, b = l["a"], l["b"]
        ra, rb = math.dist(a, WELL_C), math.dist(b, WELL_C)
        if 1400 < min(ra, rb) < 1750 and 2650 < max(ra, rb) < 2850:
            inner, outer = (a, b) if ra < rb else (b, a)
            if abs(outer[0] - inner[0]) < 0.5 or abs(outer[1] - inner[1]) < 0.5:
                continue                                                  # the straight treads
            ang_c = math.degrees(math.atan2(inner[1] - WELL_C[1], inner[0] - WELL_C[0])) % 360
            ang_l = math.degrees(math.atan2(outer[1] - inner[1], outer[0] - inner[0])) % 360
            if abs(((ang_l - ang_c + 180) % 360) - 180) < 4.0:
                rad.append((ang_c, l, math.dist(inner, WELL_C), math.dist(outer, WELL_C)))
    groups = []
    for ang, l, ri, ro in sorted(rad, key=lambda x: (x[0], x[1]["handle"])):
        if groups and ang - groups[-1]["angles"][-1] <= 2.5:
            groups[-1]["angles"].append(ang)
            groups[-1]["lines"].append(l)
            groups[-1]["radii"].append((ri, ro))
        else:
            groups.append({"angles": [ang], "lines": [l], "radii": [(ri, ro)]})
    curved = [{"angle": round(sum(g["angles"]) / len(g["angles"]), 3), "ids": [_rid(l) for l in g["lines"]],
               "r_in": sum(r[0] for r in g["radii"]) / len(g["radii"]),
               "r_out": sum(r[1] for r in g["radii"]) / len(g["radii"]),
               "kind": "PAIR (nosing + riser face)" if len(g["lines"]) > 1 else "SINGLE LINE"} for g in groups]
    straight = _risers(_v_lines(ls, STRAIGHT_X[0], STRAIGHT_X[1], STRAIGHT_Y, tol=60.0), +1)
    short = _risers(_h_lines(ls, CF2_X, CF2_Y[0], CF2_Y[1], tol=60.0), +1)
    return curved, straight, short


# view: (stair part -> (layers, element, walk direction, role))
MAIN_VIEWS = {
    "GFRS": {"WEST": (None, "A1-F1", +1, "PRIMARY_STRUCTURAL"), "TURN": (None, "A1-W1", 0, "PRIMARY_STRUCTURAL"),
             "EAST": (None, "A1-F2", -1, "PRIMARY_STRUCTURAL")},
    "FFRS": {"WEST": (None, "A2-F1", +1, "PRIMARY_STRUCTURAL"), "TURN": (None, "A2-W1", 0, "PRIMARY_STRUCTURAL"),
             "EAST": (None, "A2-F2", -1, "PRIMARY_STRUCTURAL")},
    "GBP": {"WEST": (None, "A1-F1", +1, "REPEATED_VIEW_PARTIAL"), "EAST": (None, "B-F1", +1, "PRIMARY_STRUCTURAL")},
    "ARCH-GF": {"WEST": (None, "A1-F1", +1, "PRIMARY_ARCH"), "TURN": (None, "A1-W1", 0, "PRIMARY_ARCH"),
                "EAST": (("2",), "A1-F2", -1, "PRIMARY_ARCH (overhead, hidden lines)"),
                "EAST_VISIBLE": (("5",), "B-F1", +1, "PRIMARY_ARCH (visible)")},
    "ARCH-1F": {"WEST": (None, "A2-F1", +1, "PRIMARY_ARCH"), "TURN": (None, "A2-W1", 0, "PRIMARY_ARCH"),
                "EAST": (None, "A2-F2", -1, "PRIMARY_ARCH")},
    "ARCH-2F": {"WEST": (None, "A2-F1", +1, "REPEATED_VIEW"), "TURN": (None, "A2-W1", 0, "REPEATED_VIEW"),
                "EAST": (None, "A2-F2", -1, "REPEATED_VIEW")},
}
WELL_VIEWS = {"GFRS": "PRIMARY_STRUCTURAL", "ARCH-1F": "PRIMARY_ARCH", "ARCH-GF": "SECOND_VIEW",
              "GBP": "REPEATED_VIEW_PARTIAL"}
ENTR_VIEWS = {"GBP": "PRIMARY_STRUCTURAL", "ARCH-GF": "PRIMARY_ARCH"}


def recount(views):
    counts, ev = {}, []

    def add(view, stair, el, part, role, i, r, pos_key="pos"):
        ev.append({"VIEW": view, "STAIR": stair, "ELEMENT_ID": el, "PART": part, "ROLE": role, "RISER_IN_PART": i,
                   "POSITION_MM": _r(r.get(pos_key), 3) if part not in ("TURN_RADIAL", "CURVED") else None,
                   "RISER_FACE_MM": _r(r.get("face"), 3) if r.get("face") is not None else None,
                   "ANGLE_DEG": r.get("angle"), "LINES": r["ids"], "LINE_KIND": r["kind"],
                   "STATUS": "DRAWN_LINE_READ (a drawing fact; authority per view in 05)"})
    for view, parts in MAIN_VIEWS.items():
        ls = views[view]
        for part, (layers, el, walk, role) in parts.items():
            stair = "main (service) stair" if el.startswith("A") else "lobby steps (on grade)"
            if part in ("WEST", "EAST", "EAST_VISIBLE"):
                span = WEST_X if part == "WEST" else EAST_X
                rs = _risers(_h_lines(ls, span, 15800.0, 19500.0, layers), walk)
                counts[(view, el)] = {"risers": len(rs), "list": rs, "role": role}
                for i, r in enumerate(rs, 1):
                    add(view, stair, el, part, role, i, r)
            else:
                rad, closing = _turn(ls)
                counts[(view, el)] = {"risers": len(rad) + len(closing), "radial": len(rad), "closing": len(closing),
                                      "rad": rad, "closing_list": closing, "role": role}
                for i, r in enumerate(rad, 1):
                    add(view, stair, el, "TURN_RADIAL", role, i, r)
                for i, r in enumerate(closing, 1):
                    add(view, stair, el, "TURN_CLOSING", role, i, r)
    for view, role in WELL_VIEWS.items():
        curved, straight, short = _well(views[view])
        counts[(view, "C-F1:CURVED")] = {"risers": len(curved), "list": curved, "role": role}
        counts[(view, "C-F1:STRAIGHT")] = {"risers": len(straight), "list": straight, "role": role}
        counts[(view, "C-F2")] = {"risers": len(short), "list": short, "role": role}
        for part, items, el in (("CURVED", curved, "C-F1"), ("STRAIGHT", straight, "C-F1"), ("SHORT", short, "C-F2")):
            for i, r in enumerate(items, 1):
                add(view, "round (light-well) stair", el, part, role, i, r)
    for view, role in ENTR_VIEWS.items():
        d = _risers(_v_lines(views[view], ENTR_X[0], ENTR_X[1], ENTR_Y, tol=10.0), +1)
        counts[(view, "D-F1")] = {"risers": len(d), "list": d, "role": role}
        for i, r in enumerate(d, 1):
            add(view, "entrance steps (on grade)", "D-F1", "FLIGHT", role, i, r)
    return counts, ev


def _n(counts, view, el):
    return counts.get((view, el), {}).get("risers")


def drawn_arrangements(c):
    """every complete drawn arrangement per storey run: (risers before the landing, after it, winder radials)."""
    out = {}
    for view, run, f1, w, f2 in (("GFRS", "A1", "A1-F1", "A1-W1", "A1-F2"), ("ARCH-GF", "A1", "A1-F1", "A1-W1", "A1-F2"),
                                 ("FFRS", "A2", "A2-F1", "A2-W1", "A2-F2"), ("ARCH-1F", "A2", "A2-F1", "A2-W1", "A2-F2"),
                                 ("ARCH-2F", "A2", "A2-F1", "A2-W1", "A2-F2")):
        n1, tw, n2 = _n(c, view, f1), c[(view, w)], _n(c, view, f2)
        out[(run, view)] = {"flight_1": n1, "radial": tw["radial"], "closing": tw["closing"],
                            "before_landing": n1 + tw["radial"] + tw["closing"], "after_landing": n2,
                            "total": n1 + tw["radial"] + tw["closing"] + n2}
    for view in ("GFRS", "ARCH-1F", "ARCH-GF"):
        cu, st, sh = _n(c, view, "C-F1:CURVED"), _n(c, view, "C-F1:STRAIGHT"), _n(c, view, "C-F2")
        out[("C", view)] = {"flight_1": cu + st, "curved": cu, "straight": st, "radial": 0, "closing": 0,
                            "before_landing": cu + st, "after_landing": sh, "total": cu + st + sh}
    return out


# ------------------------------------------------------------------ section A-A (render + measure)
def _render(pdf, page, dpi, crop):
    """the page rendered at `dpi` inside the crop window (x, y, w, h in page pixels; pixel-identical to the same
    window of a full render), returned as a dark-pixel mask indexed in page pixels."""
    import numpy as np
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    x, y, w, h = crop
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", str(dpi), "-x", str(x), "-y", str(y),
                        "-W", str(w), "-H", str(h), "-png", str(pdf), str(Path(d) / "p")], check=True,
                       capture_output=True)
        f = sorted(Path(d).glob("p*.png"))
        check(len(f) == 1, "one rendered page")
        win = np.asarray(Image.open(f[0]).convert("L")) < SEC["dark"]
    check(win.shape == (h, w), "rendered window size")
    out = np.zeros((y + h, x + w), dtype=bool)
    out[y:, x:] = win
    return out


def _vgroups(dark, y0, y1, x0, x1, frac=0.9):
    import numpy as np
    cnt = dark[y0:y1, x0:x1].sum(axis=0)
    idx = np.where(cnt >= frac * (y1 - y0))[0]
    groups = []
    for i in idx.tolist():
        if groups and i - groups[-1][-1] <= 1:
            groups[-1].append(i)
        else:
            groups.append([i])
    return [{"x0": x0 + g[0], "x1": x0 + g[-1], "c": x0 + (g[0] + g[-1]) / 2.0, "w": g[-1] - g[0] + 1}
            for g in groups]


def _tread_runs(dark, x0, x1, y0, y1, lo, hi):
    """short constant-x runs (tread or slab surface lines in the rotated section), clustered by thickness."""
    import numpy as np
    segs = []
    for x in range(x0, x1):
        col = np.concatenate(([0], dark[y0:y1, x].astype(np.int8), [0]))
        d = np.diff(col)
        starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
        for a_, b_ in zip(starts.tolist(), ends.tolist()):
            if lo <= b_ - a_ <= hi:
                segs.append((x, y0 + a_, y0 + b_ - 1))
    cl = []
    for x, a, b in sorted(segs):
        for c in cl:
            if x - c["x1"] <= 2 and not (b < c["a"] - 5 or a > c["b"] + 5):
                c["x1"], c["a"], c["b"], c["n"] = x, min(c["a"], a), max(c["b"], b), c["n"] + 1
                break
        else:
            cl.append({"x0": x, "x1": x, "a": a, "b": b, "n": 1})
    return [dict(c, c=(c["x0"] + c["x1"]) / 2.0) for c in cl if c["n"] >= 3]


def _grid_count(lines, x_from, x_to, n_range, tol=5.0):
    """the riser count whose uniform grid between two level lines explains the drawn tread lines best:
    score = drawn lines on the grid - grid positions without a line."""
    best = None
    xs = sorted({round(c, 1) for c in lines})
    for n in n_range:
        p = (x_to - x_from) / n
        grid = [x_from + k * p for k in range(1, n)]
        on = sum(1 for x in xs if any(abs(x - g) <= tol for g in grid))
        missing = sum(1 for g in grid if not any(abs(x - g) <= tol for x in xs))
        score = on - missing
        if best is None or score > best["score"]:
            best = {"n": n, "pitch_px": p, "score": score, "on_grid": on, "missing": missing,
                    "grid_px": [round(g, 1) for g in grid]}
    return best


def section_a_a():
    import numpy as np
    dark = _render(BY_SHA / f"{ARCH_PDF_SHA}.pdf", SEC["page"], SEC["dpi"], SEC["crop"])
    rows = []
    # calibration: the bottom chain '100 / 870 / 420 / 50' extension lines
    thin = [g for g in _vgroups(dark, *SEC["chain_bottom"]) if g["w"] <= 7]
    check(len(thin) == len(SEC["chain_bottom_levels_m"]), f"bottom level chain: {len(thin)} extension lines")
    E = np.array(SEC["chain_bottom_levels_m"])
    X = np.array([g["c"] for g in thin])
    b, a = np.polyfit(E, X, 1)
    resid = X - (a + b * E)
    nominal = SEC["dpi"] / 0.0254 / 100.0
    check(float(np.abs(resid).max()) < 2.0 and abs(b / nominal - 1) < 0.005, "section A-A scale is 1:100")

    def elev(x):
        return (x - a) / b
    for g, e in zip(thin, SEC["chain_bottom_levels_m"]):
        rows.append({"RECORD": "SECTION_A_A_CALIBRATION", "ITEM": f"extension line {_full(e, 2)} (bottom chain)",
                     "PIXEL_X": g["c"], "VALUE": _r(elev(g["c"]), 4), "UNIT": "m", "STATUS": PRINTED,
                     "EVIDENCE": f"x = {_full(a, 3)} + {_full(b, 4)} px/m x level; residual "
                                 f"{_full(float(g['c'] - (a + b * e)), 2)} px"})
    top = [g for g in _vgroups(dark, *SEC["chain_top"]) if g["w"] <= 5]
    datum = {}
    for e in SEC["chain_top_levels_m"]:
        g = min(top, key=lambda g: abs(elev(g["c"]) - e))
        check(abs(elev(g["c"]) - e) < 0.015, f"top chain {e} at its printed level")
        datum[e] = g["c"]
        rows.append({"RECORD": "SECTION_A_A_CALIBRATION", "ITEM": f"extension line +{_full(e, 2)} (top chain)",
                     "PIXEL_X": g["c"], "VALUE": _r(elev(g["c"]), 4), "UNIT": "m", "STATUS": PRINTED,
                     "EVIDENCE": "check against the calibration (within 15 mm)"})
    # landing level lines: a thin line 8 - 16 px above a thick slab-top line
    land = {}
    for run, win in SEC["landing"].items():
        gs = _vgroups(dark, *win)
        thick = [g for g in gs if g["w"] >= 8]
        thin_ = [g for g in gs if g["w"] <= 6]
        lv = [(t, s) for t in thick for s in thin_ if 8 <= s["c"] - t["c"] <= 16]
        land[run] = [{"slab_top_px": t["c"], "level_px": s["c"], "level_m": elev(s["c"]),
                      "slab_line_m": elev(t["c"])} for t, s in lv]
    a1 = sorted(land["A1"], key=lambda x: x["level_m"])
    check(len(a1) == 2, "A1 window: the +0.30 lobby floor and the half-landing")
    a2 = land["A2"]
    check(len(a2) == 1, "A2 window: one half-landing")
    lobby, l1, l2 = a1[0], a1[1], a2[0]
    for nm, x, st, note in (("+0.30 lobby floor (level line)", lobby, PRINTED, "'+0.30' level symbol on this line"),
                            ("GF -> 1F half-landing (level line)", l1, PRINTED,
                             "dimension '320' from the +0.30 lobby floor to this line = +3.50"),
                            ("1F -> 2F half-landing (level line)", l2, SCALED, "no level or dimension printed")):
        rows.append({"RECORD": "SECTION_A_A_LEVEL", "ITEM": nm, "PIXEL_X": x["level_px"], "VALUE": _r(x["level_m"], 4),
                     "UNIT": "m", "STATUS": st,
                     "EVIDENCE": f"{note}; slab-top line {_full(x['slab_line_m'], 3)} m "
                                 f"({_full((x['level_m'] - x['slab_line_m']) * 1000, 0)} mm below the level line, "
                                 "line centres: the drawn finish, not a dimension)"})
    check(abs(lobby["level_m"] - 0.30) < 0.015 and abs(l1["level_m"] - 3.50) < 0.015, "+0.30 and +3.50 measured")
    check(abs((l1["level_m"] - lobby["level_m"]) - 3.20) < 0.015, "'320' is drawn to scale")
    # flights: cut (thick structural tread lines) and seen (thin finish lines)
    flights = {}
    spec = {"A1": (datum[1.00], l1, datum[5.50], 1.00, 5.50), "A2": (datum[5.50], l2, datum[9.70], 5.50, 9.70)}
    for run, (x_bot, L, x_top, e_bot, e_top) in spec.items():
        cut = _tread_runs(dark, *SEC["cut"][run], 50, 95)
        thick = [c["c"] for c in cut if (c["x1"] - c["x0"] + 1) >= 8]
        floor_thick = max(thick)
        up = _grid_count([c["c"] for c in cut if c["c"] < floor_thick - 3], L["slab_top_px"], floor_thick,
                         range(6, 25))
        seen = _tread_runs(dark, *SEC["seen"][run], 35, 130)
        thin_seen = [c["c"] for c in seen if (c["x1"] - c["x0"] + 1) <= 6 and x_bot + 5 < c["c"] < L["level_px"] - 5]
        lo = _grid_count(thin_seen, x_bot, L["level_px"], range(6, 25))
        offs = []
        for t in thick:
            near = [c["c"] - t for c in cut if (c["x1"] - c["x0"] + 1) <= 6 and 8 <= c["c"] - t <= 16]
            if near:
                offs.append(min(near))
        flights[run] = {"upper": up, "lower": lo, "landing_m": L["level_m"], "bottom_m": e_bot, "top_m": e_top,
                        "finish_offset_px": sorted(offs)}
        for part, g, frm, to, kind in (("upper flight (cut, structural tread lines)", up, L["level_m"], e_top, "cut"),
                                       ("lower flight + turn (seen; finish lines, some hidden by rails)", lo, e_bot,
                                        L["level_m"], "seen")):
            rows.append({"RECORD": "SECTION_A_A_FLIGHT", "ITEM": f"{run} {part}", "PIXEL_X": None,
                         "VALUE": g["n"], "UNIT": "risers", "STATUS": "DRAWN_COUNT (measured)",
                         "EVIDENCE": f"{g['n'] - 1 - g['missing']} of {g['n'] - 1} intermediate grid positions carry "
                                     f"a drawn line ({g['on_grid']} line groups on the grid); pitch "
                                     f"{_full(g['pitch_px'], 2)} px = "
                                     f"{_full(g['pitch_px'] / b * 1000, 1)} mm; from {_full(frm, 3)} to "
                                     f"{_full(to, 3)} m: {_full((to - frm) * 1000 / g['n'], 2)} mm per riser"})
    check((flights["A1"]["lower"]["n"], flights["A1"]["upper"]["n"]) == (15, 12), "section A-A GF -> 1F: 15 + 12")
    check((flights["A2"]["lower"]["n"], flights["A2"]["upper"]["n"]) == (13, 12), "section A-A 1F -> 2F: 13 + 12")
    fo = flights["A1"]["finish_offset_px"] + flights["A2"]["finish_offset_px"]
    med = sorted(fo)[len(fo) // 2]
    rows.append({"RECORD": "SECTION_A_A_FINISH", "ITEM": "finish line above the structural tread lines (cut flights)",
                 "PIXEL_X": None, "VALUE": _r(med / b * 1000, 1), "UNIT": "mm", "STATUS": ILLUSTRATIVE,
                 "EVIDENCE": f"median of {len(fo)} tread pairs, line centre to line centre; at 1:100 the lines are "
                             "20 - 45 mm wide, so this is an indication that a finish is drawn, not a thickness"})
    return {"rows": rows, "flights": flights, "lobby_m": lobby["level_m"], "a1_landing_m": l1["level_m"],
            "a2_landing_m": l2["level_m"], "scale_px_per_m": b, "finish_offset_mm": med / b * 1000}


# ------------------------------------------------------------------ plan geometry of each element (own outlines)
def element_outlines(counts):
    from shapely.geometry import box
    g = {}
    a1f1 = counts[("GFRS", "A1-F1")]["list"]
    a1f2 = counts[("GFRS", "A1-F2")]["list"]
    a2f1 = counts[("ARCH-1F", "A2-F1")]["list"]
    a2f2 = counts[("ARCH-1F", "A2-F2")]["list"]
    g["A1-F1"] = ("GFRS", box(X_BAY_W, a1f1[0]["face"], X_WALL_W, a1f1[-1]["face"]))
    g["A1-W1"] = ("GFRS", box(X_BAY_W, Y_TURN, X_WALL_E, Y_BAY_N))
    g["A1-L1"] = ("GFRS", box(X_WALL_E, Y_WALL_END, X_BAY_E, Y_BAY_N))
    g["A1-F2"] = ("GFRS", box(X_WALL_E, a1f2[-1]["face"], X_BAY_E, a1f2[0]["face"]))
    g["A2-F1"] = ("FFRS", box(X_BAY_W, a2f1[0]["face"], X_WALL_W, a2f1[-1]["face"]))
    g["A2-W1"] = ("FFRS", box(X_BAY_W, Y_TURN, X_WALL_E, Y_BAY_N))
    g["A2-L1"] = ("FFRS", box(X_WALL_E, Y_WALL_END, X_BAY_E, Y_BAY_N))
    g["A2-F2"] = ("FFRS", box(X_WALL_E, a2f2[-1]["face"], X_BAY_E, a2f2[0]["face"]))
    g["A2-T1"] = ("FFRS", box(X_WALL_E, 16311.856, X_BAY_E, a2f2[-1]["face"]))
    st = counts[("GFRS", "C-F1:STRAIGHT")]["list"]
    sh = counts[("GFRS", "C-F2")]["list"]
    g["C-F1:STRAIGHT"] = ("GFRS", box(st[0]["face"], STRAIGHT_Y[0], st[-1]["face"], STRAIGHT_Y[1]))
    g["C-L1"] = ("GFRS", box(st[-1]["face"], STRAIGHT_Y[0], CF2_X[1], sh[0]["face"]))
    g["C-F2"] = ("GFRS", box(CF2_X[0], sh[0]["face"], CF2_X[1], sh[-1]["face"]))
    b = counts[("GBP", "B-F1")]["list"]
    d = counts[("GBP", "D-F1")]["list"]
    g["B-F1"] = ("GBP", box(X_WALL_E, b[0]["face"], X_BAY_E, b[-1]["face"]))
    g["D-F1"] = ("GBP", box(d[0]["face"], ENTR_Y[0], d[-1]["face"], ENTR_Y[1]))
    return g


def curved_region(curved, x_first_straight, r_in, r_out):
    from shapely.geometry import Point, Polygon, box
    ann = Point(WELL_C).buffer(r_out, 512).difference(Point(WELL_C).buffer(r_in, 512))
    a0 = curved[0]["angle"]
    pts = [WELL_C] + [(WELL_C[0] + 6000 * math.cos(math.radians(a)), WELL_C[1] + 6000 * math.sin(math.radians(a)))
                      for a in [a0 + i * (300.0 - a0) / 400 for i in range(401)]]
    wedge = Polygon(pts)
    half = box(WELL_C[0] - 10000, WELL_C[1] - 10000, x_first_straight, WELL_C[1] + 10000)
    return ann.intersection(wedge).intersection(half)


def winder_treads(rad, region):
    """the turn split into treads by angular wedges about the fan centre of the radial risers (each wedge edge runs
    from the centre through a riser's outer end). Returns the treads in walking order, the centre and its miss."""
    from shapely.geometry import Polygon
    centre, miss = SG.fan_centre([(r["ids"][0], r["mean_line"][0], r["mean_line"][1]) for r in rad])
    angs = []
    for r in rad:
        a, b = r["mean_line"]
        outer = a if math.dist(a, centre) > math.dist(b, centre) else b
        angs.append(math.degrees(math.atan2(outer[1] - centre[1], outer[0] - centre[0])))
    angs = sorted(angs, reverse=True)
    back = (angs[0] + angs[-1]) / 2.0 + 180.0                     # the direction opposite the middle of the turn
    edges = [back] + angs + [back - 360.0]

    def wedge(lo, hi):
        pts = [centre] + [(centre[0] + 9000 * math.cos(math.radians(lo + (hi - lo) * i / 200)),
                           centre[1] + 9000 * math.sin(math.radians(lo + (hi - lo) * i / 200))) for i in range(201)]
        return Polygon(pts)
    pieces = [region.intersection(wedge(edges[k + 1], edges[k])) for k in range(len(edges) - 1)]
    return [p for p in pieces if p.area > 1.0], centre, miss


def walking_going(centre, n_treads, radius=WIDTH_MAIN_MM / 2.0):
    start = max(0.0, centre[1] - Y_TURN)
    end = max(0.0, X_WALL_E - centre[0])
    length = start + math.pi / 2.0 * radius + end
    return length / n_treads, length


# ------------------------------------------------------------------ beams
def beam_bands(src):
    import alsenan_structural_s1 as S1
    out = {}
    for sh in ("GBP", "GFRS", "FFRS"):
        segs, _, _ = S1.beam_linework(src, sh)
        for ln in S1.beam_lines(S1.straight_bands(segs)):
            d = tuple(float(v) for v in ln["dir"])
            n = tuple(float(v) for v in ln["normal"])
            o, w, t0, t1 = float(ln["offset"]), float(ln["width_mm"]), float(ln["t0"]), float(ln["t1"])
            pts = [(d[0] * t + n[0] * (o + s * w / 2), d[1] * t + n[1] * (o + s * w / 2))
                   for t, s in ((t0, -1), (t1, -1), (t1, 1), (t0, 1))]
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            out[(sh, ln["line_id"])] = {"pts": pts, "bbox": (min(xs), min(ys), max(xs), max(ys)),
                                        "dir": d, "width_mm": w}
    return out


def head_beam_edges(lines):
    out = {}
    for mark, (sh, h_lo, h_hi) in HEAD_BEAM_EDGES.items():
        by = {l["handle"]: l for l in lines[sh]}
        check(h_lo in by and h_hi in by, f"{mark} edge lines {h_lo} / {h_hi} on {sh}")
        lo, hi = by[h_lo], by[h_hi]
        check(abs(lo["a"][1] - lo["b"][1]) < 0.5 and abs(hi["a"][1] - hi["b"][1]) < 0.5, f"{mark} edges horizontal")
        out[mark] = {"sheet": sh, "y_south": lo["a"][1], "y_north": hi["a"][1], "handles": [h_lo, h_hi],
                     "x": (min(lo["a"][0], lo["b"][0]), max(lo["a"][0], lo["b"][0])),
                     "width_mm": hi["a"][1] - lo["a"][1]}
    return out


def s6_occurrences():
    """S6 occurrences per (sheet, beam line) with their spans along the line (t-coordinates)."""
    occ = _rows(READ["S6_OCC"])
    by_line = defaultdict(list)
    for o in occ:
        for g in json.loads(o["geometry_objects"] or "[]"):
            m = re.fullmatch(r"SPAN:(\w+):(BL\d+):(-?\d+)-(-?\d+)", g)
            if m:
                by_line[(m.group(1), m.group(2))].append((float(m.group(3)), float(m.group(4)), o))
    return by_line


def occ_list(occ, sh, line, rng=None):
    """the distinct S6 occurrences of a beam line whose span meets rng (t-range along the line), if given."""
    seen, out = set(), []
    for lo, hi, o in sorted(occ.get((sh, line), []), key=lambda x: (x[0], x[2]["occurrence_id"])):
        if rng is not None and not (min(lo, hi) < rng[1] and max(lo, hi) > rng[0]):
            continue
        if o["occurrence_id"] in seen:
            continue
        seen.add(o["occurrence_id"])
        out.append(o)
    return out


# ------------------------------------------------------------------ owner register
def owner_register(levels):
    def lv(plan, text):
        return [x["handle"] for x in levels if x["plan"] == plan and x["text"] == text]
    rows = [
        ("O-01", "Main stair GF -> 1F riser count", "28", PROV_OWNER,
         "owner decision (S8.7B brief); drawn only by the structural GF roof sheet (12 + 4 + 12)",
         "evaluated against the drawings in 04 / 05 / 06; not approved"),
        ("O-02", "Main stair 1F -> 2F riser count", "27", PROV_OWNER,
         "owner decision (S8.7B brief); drawn only by the architectural 1F plan (12 + 4 + 11)",
         "evaluated against the drawings in 04 / 05 / 06; not approved"),
        ("O-03", "Structural stair waist thickness", "UNKNOWN", ENGINEER,
         "p.16 'THICK' without a value; the plan '16' tags are zone tags",
         "150 / 160 / 175 / 200 mm evaluated as research sensitivity only (08)"),
        ("O-04", "Marble / stair finish", "30 mm", PROV_OWNER, "owner decision (S8.7B brief)",
         "kept separate from bedding / adhesive, which is not stated (07 shows bedding 0 / 20 / 30 illustratively)"),
        ("O-05", "Marble bedding / adhesive", "NOT STATED", ENGINEER, "no drawing or owner statement",
         "never assumed to be inside the 30 mm"),
        ("O-06", "Finished floor levels", "GF +1.00, 1F +5.50, 2F +9.70", VERIFIED,
         f"printed: GF plan {lv('ARCH-GF', '+1.00')}, 1F plan {lv('ARCH-1F', '+5.50')}, 2F plan "
         f"{lv('ARCH-2F', '+9.70')}; section A-A level chain; owner statement",
         "established datums"),
        ("O-07", "Floor-to-floor rises", "4500 / 4200 mm", VERIFIED, "derived from O-06", "established"),
        ("O-08", "Preferred riser range", "150 - 160 mm", "OWNER_PREFERENCE", "owner statement",
         "28 risers give 160.714 mm: 0.714 mm above the preferred maximum -> TOLERANCE_DECISION_REQUIRED"),
        ("O-09", "Round (light-well) stair", "28 risers as drawn", "DRAWN_ARRANGEMENT_EVALUATED",
         "the structural GF roof sheet and the architectural 1F plan both draw 12 curved + 11 straight / landing / 5",
         "the owner's main-stair decisions are NOT an approval of the round stair"),
        ("O-10", "Landing position", "approximately halfway (owner statement)", "OWNER_STATEMENT",
         "owner statement", "not used to set any level: levels come from the drawings (04)"),
        ("O-11", "Lower / upper floor build-ups (screed + tile)", "NOT STATED", ENGINEER, "no drawing",
         "30 / 50 / 80 / 100 mm evaluated illustratively (07)"),
        ("O-12", "Release delta of this layer", "0 m3 concrete, 0 kg reinforcement", "RULE",
         "S8.7B brief", "S8.7's frozen release (0.516582788 m3, 59.020862261 kg) is unchanged"),
    ]
    return [{"ID": a, "PARAMETER": b, "VALUE": c, "STATUS": d, "EVIDENCE": e, "USE_IN_S8_7B": f}
            for a, b, c, d, e, f in rows]


# ------------------------------------------------------------------ riser tables
def _blondel(h):
    return 2 * h + GOING_MM


def riser_rows(arr, sec):
    lo, hi = OWNER["PREFERRED_RISER_MM"]
    cases = [("A1", "main stair GF -> 1F", "GF", "1F", OWNER["A1_RISERS"], "OWNER_SCENARIO (provisional)", PROV_OWNER),
             ("A1", "main stair GF -> 1F", "GF", "1F", arr[("A1", "ARCH-GF")]["total"], "architectural GF plan",
              "DRAWN_ALTERNATIVE"),
             ("A1", "main stair GF -> 1F", "GF", "1F", sec["flights"]["A1"]["lower"]["n"] + sec["flights"]["A1"]["upper"]["n"],
              "section A-A (measured)", "DRAWN_ALTERNATIVE"),
             ("A2", "main stair 1F -> 2F", "1F", "2F", OWNER["A2_RISERS"], "OWNER_SCENARIO (provisional)", PROV_OWNER),
             ("A2", "main stair 1F -> 2F", "1F", "2F", arr[("A2", "FFRS")]["total"],
              "structural 1F roof sheet / 2F plan", "DRAWN_ALTERNATIVE"),
             ("A2", "main stair 1F -> 2F", "1F", "2F", sec["flights"]["A2"]["lower"]["n"] + sec["flights"]["A2"]["upper"]["n"],
              "section A-A (measured)", "DRAWN_ALTERNATIVE"),
             ("C", "round (light-well) stair GF -> 1F", "GF", "1F", arr[("C", "GFRS")]["total"],
              "drawn (GF roof sheet = architectural 1F plan)", "DRAWN_ARRANGEMENT_EVALUATED")]
    rows = []
    for run, stair, f0, f1, n, basis, status in cases:
        b, t = FFL_MM[f0], FFL_MM[f1]
        rise = t - b
        h = rise / n
        so = SC.setting_out(b, t, n)
        fl, ce = math.floor(h), math.ceil(h)
        flag = "WITHIN_PREFERENCE" if lo <= h <= hi else (
            "TOLERANCE_DECISION_REQUIRED" if h - hi < 1.0 and h > hi else "OUTSIDE_PREFERENCE")
        rows.append({"STAIR_RUN": run, "STAIR": stair, "BASIS": basis, "STATUS": status, "FROM_FFL_M": b / 1000,
                     "TO_FFL_M": t / 1000, "RISE_MM": rise, "RISERS": n,
                     "FINISHED_RISER_MM_FULL_PRECISION": _r(h, 10), "FINISHED_RISER_MM_DISPLAY": f"{h:.3f}",
                     "PREFERENCE_150_160": flag, "ABOVE_PREFERRED_MAX_MM": _r(max(0.0, h - hi), 6),
                     "BLONDEL_2R_PLUS_G_MM": _r(_blondel(h), 6),
                     "SETTING_OUT_ROUNDED_RISERS": {str(int(k)): v for k, v in sorted(so["rounded_riser_counts"].items())},
                     "SETTING_OUT_MAX_LEVEL_DEVIATION_MM": _r(so["max_abs_deviation_mm"], 6),
                     "REPEATED_ROUNDED_RISERS_MM": [fl, ce],
                     "TOP_LEVEL_DRIFT_IF_REPEATED_MM": [_r(SC.rounded_riser_drift(rise, n, fl), 6),
                                                        _r(SC.rounded_riser_drift(rise, n, ce), 6)],
                     "NOTE": "set out cumulative levels rounded to 1 mm (03), never one rounded riser repeated"})
    return rows


def owner_segments(arr):
    a1 = arr[("A1", "GFRS")]
    a2 = arr[("A2", "ARCH-1F")]
    c = arr[("C", "GFRS")]
    return {
        "A1-OWNER-28": {"run": "A1", "b": FFL_MM["GF"], "t": FFL_MM["1F"], "lane": WITH_CONFLICT,
                        "allocation": "structural GF roof sheet (12 / 3 radial + closing / landing / 12)",
                        "segments": [("A1-F1", RS.FLIGHT, a1["flight_1"]),
                                     ("A1-W1", RS.WINDERS, a1["radial"] + a1["closing"]),
                                     ("A1-L1", RS.LANDING, 0), ("A1-F2", RS.FLIGHT, a1["after_landing"])]},
        "A2-OWNER-27": {"run": "A2", "b": FFL_MM["1F"], "t": FFL_MM["2F"], "lane": WITH_CONFLICT,
                        "allocation": "architectural 1F plan (12 / 3 radial + closing / landing / 11)",
                        "segments": [("A2-F1", RS.FLIGHT, a2["flight_1"]),
                                     ("A2-W1", RS.WINDERS, a2["radial"] + a2["closing"]),
                                     ("A2-L1", RS.LANDING, 0), ("A2-F2", RS.FLIGHT, a2["after_landing"])]},
        "C-DRAWN-28": {"run": "C", "b": FFL_MM["GF"], "t": FFL_MM["1F"], "lane": "DRAWN_ARRANGEMENT_EVALUATED",
                       "allocation": "12 curved + 11 straight / corner landing / 5",
                       "segments": [("C-F1", RS.FLIGHT, c["flight_1"]), ("C-L1", RS.LANDING, 0),
                                    ("C-F2", RS.FLIGHT, c["after_landing"])]},
    }


def setting_out_rows(sc):
    rows = []
    for sid, s in sc.items():
        n = sum(x[2] for x in s["segments"])
        sched = RS.schedule(s["b"] / 1000, s["t"] / 1000, s["segments"])
        so = SC.setting_out(s["b"], s["t"], n)
        check(sched["n"] == n, "schedule length")
        for x, y in zip(sched["rows"], so["rows"]):
            check(abs(x["finished_mm"] - y["exact_mm"]) < 1e-6, "schedule = setting-out levels")
            rows.append({"SCENARIO": sid, "STATUS": s["lane"], "RISER": x["riser"], "SEGMENT": x["segment"],
                         "KIND": x["kind"], "RISES_ONTO": x["onto"],
                         "FINISHED_RISER_MM_EXACT": _r(x["finished_riser_mm"], 10),
                         "FINISHED_LEVEL_EXACT_M": _r(x["finished_mm"] / 1000.0, 10),
                         "SETTING_OUT_LEVEL_MM": y["rounded_mm"], "SETTING_OUT_RISER_MM": y["rounded_riser_mm"],
                         "SETTING_OUT_DEVIATION_MM": _r(y["deviation_mm"], 6),
                         "NOTE": "construction-friendly: cumulative level rounded to 1 mm; the exact level governs"})
    return rows


# ------------------------------------------------------------------ landing reconciliation
def landing_rows(arr, sec, sc_):
    rows = []
    printed = {"A1": (3500.0, PRINTED, "section A-A: '320' from the +0.30 lobby floor (+3.50); measured level line "
                      f"+{_full(sec['a1_landing_m'], 3)}"),
               "A2": (None, INFERRED, f"no level printed; section A-A level line scales to +{_full(sec['a2_landing_m'], 3)} "
                      "(1:100, indicative)"),
               "C": (None, INFERRED, "no level printed on any plan; no section cuts the round stair")}
    cases = [("A1", "OWNER-28 (structural GF roof sheet allocation)", arr[("A1", "GFRS")], "FFL_GF", "FFL_1F", PROV_OWNER),
             ("A1", "architectural GF plan", arr[("A1", "ARCH-GF")], "FFL_GF", "FFL_1F", "DRAWN_ALTERNATIVE"),
             ("A1", "section A-A (measured)", {"before_landing": sec["flights"]["A1"]["lower"]["n"],
                                               "after_landing": sec["flights"]["A1"]["upper"]["n"], "radial": None,
                                               "closing": None}, "FFL_GF", "FFL_1F", "DRAWN_ALTERNATIVE"),
             ("A2", "OWNER-27 (architectural 1F plan allocation)", arr[("A2", "ARCH-1F")], "FFL_1F", "FFL_2F", PROV_OWNER),
             ("A2", "structural 1F roof sheet / 2F plan", arr[("A2", "FFRS")], "FFL_1F", "FFL_2F", "DRAWN_ALTERNATIVE"),
             ("A2", "section A-A (measured)", {"before_landing": sec["flights"]["A2"]["lower"]["n"],
                                               "after_landing": sec["flights"]["A2"]["upper"]["n"], "radial": None,
                                               "closing": None}, "FFL_1F", "FFL_2F", "DRAWN_ALTERNATIVE"),
             ("C", "drawn 28 (corner landing)", arr[("C", "GFRS")], "FFL_GF", "FFL_1F", "DRAWN_ARRANGEMENT_EVALUATED")]
    for run, basis, a, f0, f1, status in cases:
        b, t = FFL_MM[f0[4:]], FFL_MM[f1[4:]]
        n = a["before_landing"] + a["after_landing"]
        h = (t - b) / n
        implied = b + a["before_landing"] * h
        p, pst, pev = printed[run]
        row = {"STAIR_RUN": run, "ARRANGEMENT": basis, "STATUS": status, "RISERS": n,
               "RISERS_BEFORE_LANDING": a["before_landing"], "RISERS_AFTER_LANDING": a["after_landing"],
               "WINDER_RADIAL_RISERS": a.get("radial"), "WINDER_CLOSING_RISERS": a.get("closing"),
               "START_FFL_M": b / 1000, "FINISH_FFL_M": t / 1000, "FINISHED_RISER_MM": _r(h, 10),
               "LANDING_IMPLIED_BY_UNIFORM_RISERS_M": _r(implied / 1000, 10), "LANDING_PRINTED_M": None if p is None else p / 1000,
               "PRINTED_LEVEL_STATUS": pst, "PRINTED_LEVEL_EVIDENCE": pev,
               "IMPLIED_MINUS_PRINTED_MM": None if p is None else _r(implied - p, 6)}
        scaled = {"A1": sec["a1_landing_m"], "A2": sec["a2_landing_m"]}.get(run)
        if scaled is not None:
            row["LANDING_SCALED_FROM_SECTION_M"] = _r(scaled, 4)
            row["IMPLIED_MINUS_SCALED_MM"] = _r(implied - scaled * 1000, 1)
        if p is not None:
            reach = SC.landing_reach(b, t, n, p)
            split = SC.split_risers(b, t, p, a["before_landing"], a["after_landing"])
            row.update({"PRINTED_LEVEL_REACHABLE_WITH_UNIFORM_RISERS": reach["reachable"],
                        "PRINTED_LEVEL_AT_RISER_INDEX": _r(reach["k_exact"], 6),
                        "NEAREST_BOUNDARIES_M": [_r(reach["level_below_mm"] / 1000, 6), _r(reach["level_above_mm"] / 1000, 6)],
                        "UNEQUAL_RISERS_TO_KEEP_PRINTED_LEVEL_MM": [_r(split["riser_below_mm"], 6),
                                                                    _r(split["riser_above_mm"], 6)],
                        "UNEQUAL_RISER_DIFFERENCE_MM": _r(split["difference_mm"], 6)})
            row["RESULT"] = ("CONSISTENT" if reach["reachable"] and abs(implied - p) < 0.5 else
                             "PRINTED LANDING NOT REACHABLE WITH UNIFORM RISERS" if not reach["reachable"] else
                             "REACHABLE ONLY WITH A DIFFERENT ALLOCATION")
        else:
            row["RESULT"] = "LANDING LEVEL NOT PRINTED: INFERRED FROM UNIFORM RISERS"
        rows.append(row)
    for run, f0, f1, p in (("A1", "GF", "1F", 3500.0),):
        got = SC.uniform_counts_for_landing(FFL_MM[f0], FFL_MM[f1], p, range(20, 41))
        rows.append({"STAIR_RUN": run, "ARRANGEMENT": "every uniform count 20 - 40 that reaches the printed +3.50",
                     "STATUS": "ARITHMETIC", "RISERS": [n for n, _, _ in got],
                     "RISERS_BEFORE_LANDING": [k for _, k, _ in got], "FINISHED_RISER_MM": [_r(h, 6) for _, _, h in got],
                     "LANDING_PRINTED_M": p / 1000, "PRINTED_LEVEL_STATUS": PRINTED,
                     "RESULT": "no uniform riser in the owner's 150 - 160 mm range reaches +3.50 (it needs n a multiple "
                               "of 9: 27 at 166.667 mm or 36 at 125 mm)"})
    return rows


# ------------------------------------------------------------------ conflicts
def conflict_rows(arr, counts, sec, edges):
    a1g, a1a = arr[("A1", "GFRS")], arr[("A1", "ARCH-GF")]
    a2s, a2a, a2r = arr[("A2", "FFRS")], arr[("A2", "ARCH-1F")], arr[("A2", "ARCH-2F")]
    s1, s2 = sec["flights"]["A1"], sec["flights"]["A2"]
    foot_g = counts[("GFRS", "A1-F1")]["list"][0]["face"]
    foot_a = counts[("ARCH-GF", "A1-F1")]["list"][0]["face"]
    foot_b = counts[("GBP", "A1-F1")]["list"][0]["face"]
    head_g = counts[("GFRS", "A1-F2")]["list"][-1]["face"]
    head_a = counts[("ARCH-GF", "A1-F2")]["list"][-1]["face"]
    rows = [
        ("CM-01", "A1 GF -> 1F total risers", {"GFRS": a1g["total"], "ARCH-GF": a1a["total"],
                                               "SECTION A-A": s1["lower"]["n"] + s1["upper"]["n"], "OWNER": 28},
         CONFLICT, "three drawings, three counts; the owner's 28 is the structural sheet's"),
        ("CM-02", "A1 risers before the half-landing", {"GFRS": a1g["before_landing"], "ARCH-GF": a1a["before_landing"],
                                                        "SECTION A-A": s1["lower"]["n"]}, CONFLICT,
         "16 / 14 / 15"),
        ("CM-03", "A1 upper flight risers", {"GFRS": a1g["after_landing"], "ARCH-GF": a1a["after_landing"],
                                             "SECTION A-A": s1["upper"]["n"]}, CONFLICT,
         "12 on the structural sheet and the section; 11 on the architectural plan"),
        ("CM-04", "A1 half-landing level", {"SECTION A-A printed": 3.50, "OWNER-28 implied": _r(1 + 16 * 4.5 / 28, 6),
                                            "ARCH-GF implied": _r(1 + a1a['before_landing'] * 4.5 / a1a['total'], 6),
                                            "SECTION A-A implied": _r(1 + 15 * 4.5 / 27, 6)}, CONFLICT,
         "only the section's own 27 reaches the printed +3.50 with uniform risers"),
        ("CM-05", "A1 foot of the lower flight (first riser face, y)", {"GFRS": _r(foot_g, 3), "ARCH-GF": _r(foot_a, 3),
                                                                        "GBP": _r(foot_b, 3)}, CONFLICT,
         f"{_full(foot_a - foot_g, 1)} mm apart: two goings"),
        ("CM-06", "A1 last riser face of the upper flight (y)", {"GFRS": _r(head_g, 3), "ARCH-GF": _r(head_a, 3),
                                                                 "B20 north face": _r(edges["B20"]["y_north"], 3)},
         CONFLICT, "the structural sheet's last riser lies inside B20"),
        ("CM-07", "A1 winder turn", {"GFRS": f"{a1g['radial']} radial + {a1g['closing']} closing",
                                     "ARCH-GF": f"{a1a['radial']} radial + {a1a['closing']} closing"}, VERIFIED,
         "both draw the same four-riser turn"),
        ("CM-08", "A2 1F -> 2F total risers", {"FFRS": a2s["total"], "ARCH-1F": a2a["total"], "ARCH-2F": a2r["total"],
                                               "SECTION A-A": s2["lower"]["n"] + s2["upper"]["n"], "OWNER": 27},
         CONFLICT, "the owner's 27 is the architectural 1F plan's"),
        ("CM-09", "A2 winder turn", {"FFRS": f"{a2s['radial']} radial + {a2s['closing']} closing",
                                     "ARCH-1F": f"{a2a['radial']} radial + {a2a['closing']} closing",
                                     "ARCH-2F": f"{a2r['radial']} radial + {a2r['closing']} closing"}, CONFLICT,
         "only the architectural 1F plan draws winders; the structural sheet draws the quarter flat"),
        ("CM-10", "A2 risers before the half-landing", {"FFRS": a2s["before_landing"], "ARCH-1F": a2a["before_landing"],
                                                        "SECTION A-A": s2["lower"]["n"]}, CONFLICT, "13 / 16 / 13"),
        ("CM-11", "A2 upper flight risers", {"FFRS": a2s["after_landing"], "ARCH-1F": a2a["after_landing"],
                                             "SECTION A-A": s2["upper"]["n"]}, CONFLICT,
         "11 on every plan; 12 on the section (which would end inside B23)"),
        ("CM-12", "A2 half-landing level", {"OWNER-27 implied": _r(5.5 + 16 * 4.2 / 27, 6),
                                            "FFRS implied": _r(5.5 + 13 * 4.2 / 24, 6),
                                            "SECTION A-A scaled": _r(sec["a2_landing_m"], 3), "printed": None},
         CONFLICT, f"no level printed; {_full((5.5 + 16 * 4.2 / 27 - sec['a2_landing_m']) * 1000, 0)} mm between the "
                   "owner's arrangement and the section"),
        ("CM-13", "C round stair total risers", {"GFRS": arr[("C", "GFRS")]["total"], "ARCH-1F": arr[("C", "ARCH-1F")]["total"],
                                                 "ARCH-GF (second view)": arr[("C", "ARCH-GF")]["total"]},
         VERIFIED, "the two primary views agree; the GF plan's second view draws one riser fewer in the short flight"),
        ("CM-14", "waist thickness", {"p.16": "THICK (no value)", "plans": "'16' zone tags"}, BLOCKED,
         "not established; engineer"),
        ("CM-15", "finish build-ups", {"stair": "30 mm owner (bedding not stated)", "floors": "not printed",
                                       "section A-A": f"finish line drawn ~{_full(sec['finish_offset_mm'], 0)} mm (indicative)",
                                       "p.16": "50 mm head / foot offsets (typical, meaning not stated)"}, BLOCKED,
         "first / last concrete risers stay a function of the build-ups (07)"),
    ]
    return [{"ID": a, "ITEM": b, "VALUES_BY_SOURCE": c, "STATUS": d, "NOTE": e} for a, b, c, d, e in rows]


# ------------------------------------------------------------------ beam interference
def _overlap_volume(n, h, width, t, s0, s1):
    if s1 <= s0:
        return 0.0
    return SC.flight_section_volume(n, h, GOING_MM, width, t, s0, s1) / 1e9


def beam_rows(counts, edges, bands, outlines, occ):
    rows = []
    b20, b23 = edges["B20"], edges["B23"]

    def occ_of(sh, line, rng=(X_BAY_W, X_BAY_E)):
        return [f"{o['occurrence_id']} ({o['mark'] or '-'}, {o['occurrence_state']}, {o['known_kg'] or 0} kg)"
                for o in occ_list(occ, sh, line, rng)]
    heads = [("A1-F2", "B20", b20, "GFRS", "OWNER-28 (structural GF roof sheet)", counts[("GFRS", "A1-F2")]["list"],
              28, 4500.0, PROV_OWNER),
             ("A1-F2", "B20", b20, "ARCH-GF", "architectural GF plan", counts[("ARCH-GF", "A1-F2")]["list"], None, None,
              "DRAWN_ALTERNATIVE"),
             ("A1-F2", "B20", b20, "SECTION A-A", "section A-A (12 risers, 11 goings of 300)", None, 27, 4500.0,
              "DRAWN_ALTERNATIVE"),
             ("A2-F2", "B23", b23, "ARCH-1F", "OWNER-27 (architectural 1F plan)", counts[("ARCH-1F", "A2-F2")]["list"],
              27, 4200.0, PROV_OWNER),
             ("A2-F2", "B23", b23, "FFRS", "structural 1F roof sheet", counts[("FFRS", "A2-F2")]["list"], None, None,
              "DRAWN_ALTERNATIVE"),
             ("A2-F2", "B23", b23, "SECTION A-A", "section A-A (12 risers, 11 goings of 300)", None, 25, 4200.0,
              "DRAWN_ALTERNATIVE")]
    line_of = {"B20": ("GFRS", "BL020"), "B23": ("FFRS", "BL009")}
    for el, mark, e, view, basis, lst, n_tot, rise, status in heads:
        first = counts[("GFRS" if el == "A1-F2" else "FFRS", el)]["list"][0]["face"]
        if lst is None:
            n_up = 12
            face = first - (n_up - 1) * GOING_MM
            evid = f"inferred: first riser y {_full(first, 3)} - 11 x 300"
        else:
            n_up = len(lst)
            face = lst[-1]["face"]
            evid = f"riser-face line {lst[-1]['ids']}"
        inside = e["y_south"] - 0.5 <= face <= e["y_north"] + 0.5
        clear = face - e["y_north"]
        over_len = max(0.0, e["y_north"] - face)
        row = {"INTERFACE": f"{el} head / {mark}", "SHEET": e["sheet"], "BEAM": f"{mark} ({line_of[mark][1]})",
               "BEAM_BAND_Y_MM": [_r(e["y_south"], 3), _r(e["y_north"], 3)], "BEAM_EDGE_HANDLES": e["handles"],
               "ARRANGEMENT": basis, "STATUS": status, "LAST_RISER_FACE_Y_MM": _r(face, 3),
               "CLEARANCE_TO_BEAM_FACE_MM": _r(clear, 3), "PLAN_OVERLAP_M2": _r(over_len * WIDTH_MAIN_MM / 1e6, 6),
               "RESULT": ("INTERFERENCE: the last riser and the top tread lie over the beam at the same floor level"
                          if inside else "CLEAR: the floor strip between the riser and the beam face is the arrival"),
               "S6_OCCURRENCES": occ_of(*line_of[mark]), "EVIDENCE": evid}
        if inside and n_tot:
            h = rise / n_tot
            run = (n_up - 1) * GOING_MM
            s0 = run - over_len
            row["OVERLAP_ZONE_M3_BY_WAIST"] = {f"{int(t)}": _r(_overlap_volume(n_up, h, WIDTH_MAIN_MM, t, s0, run), 9)
                                              for t in WAISTS_MM}
            row["RESOLUTION"] = ("not resolved here: neither the flight is shortened nor the beam moved; engineer to "
                                 "confirm a lowered / cranked beam or the architectural flight end")
        rows.append(row)
    # foot of the 1F -> 2F lower flight on B20 (same floor level: a support interface)
    f1 = counts[("ARCH-1F", "A2-F1")]["list"][0]["face"]
    over = max(0.0, b20["y_north"] - f1)
    rows.append({"INTERFACE": "A2-F1 foot / B20", "SHEET": "GFRS (the 1F floor)", "BEAM": "B20 (BL020)",
                 "BEAM_BAND_Y_MM": [_r(b20["y_south"], 3), _r(b20["y_north"], 3)], "BEAM_EDGE_HANDLES": b20["handles"],
                 "ARRANGEMENT": "OWNER-27 (architectural 1F plan)", "STATUS": PROV_OWNER,
                 "LAST_RISER_FACE_Y_MM": None, "FIRST_RISER_FACE_Y_MM": _r(f1, 3),
                 "PLAN_OVERLAP_M2": _r(over * WIDTH_MAIN_MM / 1e6, 6),
                 "OVERLAP_ZONE_M3_BY_WAIST": {f"{int(t)}": _r(_overlap_volume(12, 4200 / 27, WIDTH_MAIN_MM, t, 0.0, over), 9)
                                             for t in WAISTS_MM},
                 "RESULT": "SUPPORT INTERFACE: the foot bears on the beam; the zone is reported apart so the flight and "
                           "the beam are never counted over the same volume",
                 "S6_OCCURRENCES": occ_of("GFRS", "BL020"), "EVIDENCE": "first riser face of A2-F1"})
    # every element / band plan overlap or touch on the element's own sheet
    from shapely.geometry import box
    level_of = {"A1-F1": "GF -> landing (below the 1F floor beams)", "A1-W1": "turn below the 1F floor",
                "A1-L1": "half-landing below the 1F floor", "A1-F2": "landing -> 1F (head at the 1F floor)",
                "A2-F1": "1F -> landing (below the 2F floor beams)", "A2-W1": "turn below the 2F floor",
                "A2-L1": "half-landing below the 2F floor", "A2-F2": "landing -> 2F (head at the 2F floor)",
                "A2-T1": "2F floor arrival", "C-F1:STRAIGHT": "light-well flight below the 1F floor",
                "C-L1": "corner landing below the 1F floor", "C-F2": "landing -> 1F (head at the 1F floor)",
                "C-F1:CURVED": "light-well flight below the 1F floor", "B-F1": "ground steps", "D-F1": "ground steps"}
    roles = {("GFRS", "BL033"): "north edge, 'With Stair' B3 (S6 BLOCKED)",
             ("FFRS", "BL023"): "north edge, 'With Stair' B3 (S6 BLOCKED)",
             ("GFRS", "BL022"): "south edge of the straight flight / corner landing, 'With Stair' CB3 (S6 BLOCKED)",
             ("GFRS", "BL015"): "beam CA across the straight flight (S6 BLOCKED; level not stated)",
             ("GFRS", "BL001"): "east edge of the short flight", ("GFRS", "BL039"): "north edge (arrival)",
             ("GFRS", "BL020"): "B20 head beam at the 1F floor", ("FFRS", "BL009"): "B23 head beam at the 2F floor",
             ("GFRS", "BL016"): "west edge of the bay", ("FFRS", "BL019"): "west edge of the bay",
             ("GFRS", "BL028"): "east edge of the bay", ("FFRS", "BL017"): "east edge of the bay"}
    from shapely.geometry import Polygon
    for el, (sh, poly) in sorted(outlines.items()):
        for (bsh, line), bd in sorted(bands.items()):
            if bsh != sh:
                continue
            bb = bd["bbox"]
            band = Polygon(bd["pts"])
            if poly.distance(band) > 1.0:
                continue
            ov = poly.intersection(band).area / 1e6
            same = ("head" in level_of.get(el, "") and line in ("BL020", "BL009", "BL001", "BL039")) or \
                   el in ("A2-T1",)
            rows.append({"INTERFACE": f"{el} / {line}", "SHEET": sh, "BEAM": f"{line}",
                         "BEAM_BAND_Y_MM": [_r(bb[1], 3), _r(bb[3], 3)], "ARRANGEMENT": "plan outline (S8.7B)",
                         "STATUS": "PLAN_RELATION", "PLAN_OVERLAP_M2": _r(ov, 6),
                         "RESULT": ("TOUCH (shared edge)" if ov < 1e-6 else
                                    "PLAN OVERLAP AT THE SAME FLOOR LEVEL" if same else
                                    "PLAN OVERLAP: steps on grade over a ground beam (beam top level not stated; "
                                    "zone deducted from NET)" if sh == "GBP" else
                                    "PLAN OVERLAP: beam level not stated (zone deducted from NET; Q-ST7B-12)"
                                    if line in ("BL015", "BL041") else
                                    "PLAN OVERLAP ONLY: the element is at a different level from the beam"),
                         "S6_OCCURRENCES": occ_of(sh, line, (poly.bounds[0], poly.bounds[2]) if abs(bd["dir"][1]) < 0.5
                                                  else (poly.bounds[1], poly.bounds[3])),
                         "EVIDENCE": f"{level_of.get(el, '')}; {roles.get((sh, line), 'edge member')}"})
    rows.append({"INTERFACE": "'With Stair' edge beams (BL033 GFRS, BL023 FFRS, BL022 GFRS)", "SHEET": "GFRS / FFRS",
                 "BEAM": "B3 / B3 / CB3", "STATUS": UNVERIFIED,
                 "RESULT": "the landings and turns sit about 2 m below the floors these beams are drawn on; p.16's "
                           "'TYPICAL DETAIL OF STAIR BEAM' is a cranked beam that would explain the qualifier, but no "
                           "plan or section draws a cranked beam here: not assumed",
                 "S6_OCCURRENCES": occ_of("GFRS", "BL033") + occ_of("FFRS", "BL023") +
                                   occ_of("GFRS", "BL022", (20892.0, CF2_X[1])),
                 "EVIDENCE": "S6 occurrence states; p.16 visual record P16-09"})
    gb = [(line, bd["bbox"]) for (bsh, line), bd in bands.items() if bsh == "GBP" and bd["bbox"][0] < X_WALL_W
          and bd["bbox"][2] > X_BAY_W and 15000 < bd["bbox"][3] < 17200 and abs(bd["dir"][1]) < 0.01]
    foot = counts[("GFRS", "A1-F1")]["list"][0]["face"]
    rows.append({"INTERFACE": "A1-F1 foot / ground beams", "SHEET": "GBP", "BEAM": [g[0] for g in gb] or None,
                 "ARRANGEMENT": "OWNER-28 foot (structural GF roof sheet)", "STATUS": "SUPPORT_NOT_ESTABLISHED",
                 "FIRST_RISER_FACE_Y_MM": _r(foot, 3),
                 "RESULT": ("nearest ground-beam band north face at y "
                            + ", ".join(_full(g[1][3], 1) for g in gb) + f"; the foot is {_full(foot - max(g[1][3] for g in gb), 1)}"
                            " mm north of it" if gb else "no ground-beam band under the foot")
                 + "; p.16 draws a G.B at the foot (typical only)", "EVIDENCE": "S1 beam bands on GBP"})
    return rows


# ------------------------------------------------------------------ finishes and first / last risers
def finish_rows(sc):
    rows = [{"CASE": "GENERAL", "STATUS": "EQUATION",
             "NOTE": "datums: FFL (printed); SSL = FFL - floor build-up (screed + tile + adhesive); finished tread k = "
                     "FFL_b + k h; concrete tread = finished tread - tread build-up (marble + bedding); the last riser "
                     "arrives on SSL_t. First concrete riser = h + f_b - s; last = h - f_t + s; every other = h; the "
                     "concrete risers sum to (FFL_t - f_t) - (FFL_b - f_b). Finished risers stay uniform."}]
    for sid, s in sc.items():
        n = sum(x[2] for x in s["segments"])
        land_after = []
        k = 0
        for seg, kind, m in s["segments"]:
            if kind == RS.LANDING:
                land_after.append(k)
            k += m
        h = (s["t"] - s["b"]) / n
        for marble, bedding, label in TREAD_BUILD_UPS:
            tread = SC.build_up({"marble": marble, "bedding": bedding})
            for f in FLOOR_BUILD_UPS_MM:
                d = SC.datum_levels(s["b"], s["t"], n, land_after, f, f, tread)
                fl = RS.first_last(h, f, f, tread)
                check(abs(d["first_mm"] - fl[0]) < 1e-9 and abs(d["last_mm"] - fl[1]) < 1e-9 and
                      abs(d["closure_mm"]) < 1e-7, "datum model = closed form")
                rows.append({"CASE": "GRID", "SCENARIO": sid, "STATUS": ILLUSTRATIVE, "TREAD_BUILD_UP": label,
                             "MARBLE_MM": marble, "BEDDING_MM": bedding, "TREAD_BUILD_UP_MM": tread,
                             "FLOOR_BUILD_UP_BOTTOM_MM": f, "FLOOR_BUILD_UP_TOP_MM": f,
                             "FINISHED_RISER_MM": _r(h, 10), "FIRST_CONCRETE_RISER_MM": _r(d["first_mm"], 9),
                             "LAST_CONCRETE_RISER_MM": _r(d["last_mm"], 9), "OTHER_CONCRETE_RISERS_MM": _r(h, 10),
                             "SSL_BOTTOM_M": _r(d["ssl_bottom_mm"] / 1000, 6), "SSL_TOP_M": _r(d["ssl_top_mm"] / 1000, 6),
                             "CONCRETE_RISE_MM": _r(math.fsum(d["concrete_risers_mm"]), 9),
                             "CLOSURE_MM": _r(d["closure_mm"], 9)})
        for fb, ft in ((50.0, 80.0), (80.0, 50.0)):
            d = SC.datum_levels(s["b"], s["t"], n, land_after, fb, ft, OWNER["STAIR_FINISH_MM"])
            rows.append({"CASE": "UNEQUAL_FLOORS", "SCENARIO": sid, "STATUS": ILLUSTRATIVE,
                         "TREAD_BUILD_UP": "marble 30 (bedding not stated)", "MARBLE_MM": 30.0, "TREAD_BUILD_UP_MM": 30.0,
                         "FLOOR_BUILD_UP_BOTTOM_MM": fb, "FLOOR_BUILD_UP_TOP_MM": ft, "FINISHED_RISER_MM": _r(h, 10),
                         "FIRST_CONCRETE_RISER_MM": _r(d["first_mm"], 9), "LAST_CONCRETE_RISER_MM": _r(d["last_mm"], 9),
                         "OTHER_CONCRETE_RISERS_MM": _r(h, 10), "CONCRETE_RISE_MM": _r(math.fsum(d["concrete_risers_mm"]), 9),
                         "CLOSURE_MM": _r(d["closure_mm"], 9)})
        for marble, bedding, label in TREAD_BUILD_UPS:
            tread = marble + bedding
            fb, ft = RS.offsets_for(h, 200.0, 100.0, tread)
            rows.append({"CASE": "200_100_REQUIREMENT", "SCENARIO": sid, "STATUS": "NOT_SUPPORTED_BY_ANY_DRAWING",
                         "TREAD_BUILD_UP": label, "TREAD_BUILD_UP_MM": tread, "FINISHED_RISER_MM": _r(h, 10),
                         "FIRST_CONCRETE_RISER_MM": 200.0, "LAST_CONCRETE_RISER_MM": 100.0,
                         "FLOOR_BUILD_UP_BOTTOM_MM": _r(fb, 9), "FLOOR_BUILD_UP_TOP_MM": _r(ft, 9),
                         "NOTE": "the floor build-ups a 200 / 100 pair would need; nothing prints them, so it is not used"})
    s = sc["A1-OWNER-28"]
    d = SC.datum_levels(s["b"], s["t"], 28, [16], 80.0, 80.0, 50.0)
    for k in range(1, 29):
        rows.append({"CASE": "WORKED_EXAMPLE A1-OWNER-28 floors 80 / stair 30 + 20", "SCENARIO": "A1-OWNER-28",
                     "STATUS": ILLUSTRATIVE, "RISER": k, "FINISHED_LEVEL_M": _r(d["finished_mm"][k] / 1000, 10),
                     "CONCRETE_LEVEL_M": _r(d["concrete_mm"][k] / 1000, 10), "FINISHED_RISER_MM": _r(d["riser_mm"], 10),
                     "CONCRETE_RISER_MM": _r(d["concrete_risers_mm"][k - 1], 9),
                     "NOTE": "uniform finished risers with an unequal first and last concrete riser"})
    rows.append({"CASE": "REFERENCE", "STATUS": TYPICAL, "NOTE": "p.16 typical stair section: '+4.00' at the head step "
                 "and '+3.95 S.S.L' beyond; '+0.00 T.O.B' at the foot and '-0.05 S.S.L' beside it (50 mm each; "
                 "meaning not stated; generic levels): not a project build-up"})
    return rows


# ------------------------------------------------------------------ concrete sensitivity
def _cutouts(poly, cols, axis, s_origin, sign):
    """column outlines inside an element: (area m2, s-range along the walking axis, handle)."""
    from shapely.geometry import Polygon
    out = []
    for c in cols:
        cp = Polygon(c["pts"])
        if not cp.is_valid:
            cp = cp.buffer(0)
        x = poly.intersection(cp)
        if x.area > 1.0:
            b = x.bounds
            lo, hi = (b[1], b[3]) if axis == "y" else (b[0], b[2])
            s = sorted(((lo - s_origin) * sign, (hi - s_origin) * sign))
            out.append({"handle": c["handle"], "area_m2": x.area / 1e6, "s": s,
                        "frac_width": x.area / ((s[1] - s[0]) * 1.0)})
    return out


def concrete_rows(sc, counts, outlines, cols, edges, bands, released, ct1_area):
    rows = []
    a1h, a2h, ch = 4500.0 / 28, 4200.0 / 27, 4500.0 / 28

    def flight(stair, el, n, h, width, alt_width, sheet, axis, origin, sign, overlaps, status, lane, geom, evid):
        poly = outlines[el][1] if el in outlines else None
        cuts = _cutouts(poly, cols[sheet], axis, origin, sign) if poly is not None else []
        run_ = (n - 1) * GOING_MM
        for c in cuts:
            c["s"] = [max(0.0, c["s"][0]), min(run_, c["s"][1])]
        for t in WAISTS_MM:
            f = SG.straight_flight(n, h, GOING_MM, width, t)
            gross = SC.flight_section_volume(n, h, GOING_MM, width, t) / 1e9
            check(abs(gross - f["STAIR_CONCRETE_VOLUME"] / 1e9) < 1e-12, f"{el}: section integral = outline")
            run = (n - 1) * GOING_MM
            incl = run * math.hypot(GOING_MM, h) / GOING_MM
            ov = sum(_overlap_volume(n, h, width, t, o[0], o[1]) * (o[2] if len(o) > 2 else 1.0) for o in overlaps)
            cut = sum(_overlap_volume(n, h, width, t, *c["s"]) * c["frac_width"] / width for c in cuts)
            rows.append({"STAIR": stair, "ELEMENT_ID": el, "KIND": "FLIGHT", "STATUS": status, "LANE": lane,
                         "RISERS": n, "RISER_MM": _r(h, 10), "GOING_MM": GOING_MM, "WIDTH_MM": width,
                         "WIDTH_ALT_MM": alt_width, "RUN_MM": run, "PITCH_DEG": _r(math.degrees(math.atan2(h, GOING_MM)), 6),
                         "INCLINED_LENGTH_MM": _r(incl, 6), "PLAN_AREA_M2": _r(run * width / 1e6, 9),
                         "INCLINED_SOFFIT_M2": _r(incl * width / 1e6, 9), "WAIST_MM": t,
                         "WAIST_M3": _r(incl * t * width / 1e9, 9), "STEPS_M3": _r((n - 1) * GOING_MM * h / 2 * width / 1e9, 9),
                         "GROSS_M3": _r(gross, 9), "BEAM_OVERLAP_ZONE_M3": _r(ov, 9), "COLUMN_CUTOUT_M3": _r(cut, 9),
                         "NET_M3": _r(gross - ov - cut, 9),
                         "ALT_WIDTH_GROSS_M3": _r(gross * alt_width / width, 9) if alt_width else None,
                         "UPPER_BOUND_M3": None, "ALREADY_RELEASED_BY_S8_7": False,
                         "METHOD": "exact section integral between plumb cuts at the first and last riser lines "
                                   "(= stair_geometry.straight_flight); overlaps and column cut-outs reported apart",
                         "GEOMETRY_STATE": geom, "EVIDENCE": evid + (f"; columns {[c['handle'] for c in cuts]}" if cuts
                                                                     else "")})

    def plate(stair, el, sheet, status, lane, geom, evid):
        poly = outlines[el][1]
        cuts = [c for c in cols[sheet] if poly.intersection(_poly(c)).area > 1.0]
        area = poly.area / 1e6 - sum(poly.intersection(_poly(c)).area for c in cuts) / 1e6
        for t in WAISTS_MM:
            rel = el in released
            rows.append({"STAIR": stair, "ELEMENT_ID": el, "KIND": "LANDING / PLATE", "STATUS": status,
                         "LANE": ALREADY if rel else lane, "PLAN_AREA_M2": _r(area, 9), "WAIST_MM": t,
                         "GROSS_M3": _r(area * t / 1000, 9), "BEAM_OVERLAP_ZONE_M3": 0.0, "COLUMN_CUTOUT_M3": 0.0,
                         "NET_M3": 0.0 if rel else _r(area * t / 1000, 9), "ALREADY_RELEASED_BY_S8_7": rel,
                         "METHOD": "flat plate: plan outline less columns x thickness (taken equal to the waist case: an "
                                   "assumption, the landing thickness is not printed)",
                         "GEOMETRY_STATE": geom, "EVIDENCE": evid + (f"; S8.7 released {released[el]} m3 at 160 "
                                                                     "(frozen, unchanged)" if rel else "")
                         + (f"; columns {[c['handle'] for c in cuts]}" if cuts else "")})

    def winder(stair, el, h, treads, wgo, wlen, status, geom, evid):
        areas = [p.area for p in treads]
        for t in WAISTS_MM:
            b = SC.winder_bounds(areas, h, t, wgo)
            rows.append({"STAIR": stair, "ELEMENT_ID": el, "KIND": "WINDER TURN", "STATUS": status, "LANE": COND,
                         "RISERS": len(areas), "RISER_MM": _r(h, 10), "GOING_MM": _r(wgo, 6),
                         "PITCH_DEG": _r(b["pitch_deg"], 6), "PLAN_AREA_M2": _r(b["plan_area_mm2"] / 1e6, 9),
                         "WAIST_MM": t, "GROSS_M3": _r(b["plane_equivalent_mm3"] / 1e9, 9),
                         "UPPER_BOUND_M3": _r(b["flat_soffit_bound_mm3"] / 1e9, 9), "BEAM_OVERLAP_ZONE_M3": 0.0,
                         "COLUMN_CUTOUT_M3": 0.0, "NET_M3": _r(b["plane_equivalent_mm3"] / 1e9, 9),
                         "ALREADY_RELEASED_BY_S8_7": False,
                         "METHOD": "plane-equivalent A (t / cos + h / 2) on a walking line 600 from the fan centre "
                                   f"({_full(wlen, 1)} mm / {len(areas)} treads); upper bound: flat soffit under "
                                   "solid steps (exact tread polygons)",
                         "GEOMETRY_STATE": geom, "EVIDENCE": evid + f"; tread areas m2 {[_r(a / 1e6, 6) for a in areas]}"})
    A1, A2 = sc["A1-OWNER-28"], sc["A2-OWNER-27"]
    seg1 = {s[0]: s[2] for s in A1["segments"]}
    seg2 = {s[0]: s[2] for s in A2["segments"]}
    g = counts
    b20, b23 = edges["B20"], edges["B23"]
    # A1 (owner 28 on the GF roof sheet allocation)
    st1 = "main stair GF -> 1F (OWNER-28)"
    f1 = g[("GFRS", "A1-F1")]["list"]
    flight(st1, "A1-F1", seg1["A1-F1"], a1h, WIDTH_MAIN_MM, TREAD_LINE_MM, "GFRS", "y", f1[0]["face"], +1, [],
           WITH_CONFLICT, SENS, "DRAWN (structural sheet); foot conflicts with the architectural plan by two goings",
           "GFRS west column")
    winder(st1, "A1-W1", a1h, g["_treads_A1"], g["_walk_A1"][0], g["_walk_A1"][1], WITH_CONFLICT,
           "APPROXIMATION: the winder soffit is not drawn", "GFRS radial lines")
    plate(st1, "A1-L1", "GFRS", WITH_CONFLICT, SENS, "DRAWN; level +3.571 implied vs +3.50 printed", "GFRS NE quarter")
    f2 = g[("GFRS", "A1-F2")]["list"]
    s_over = f2[0]["face"] - b20["y_north"]
    run2 = (seg1["A1-F2"] - 1) * GOING_MM
    flight(st1, "A1-F2", seg1["A1-F2"], a1h, WIDTH_MAIN_MM, TREAD_LINE_MM, "GFRS", "y", f2[0]["face"], -1,
           [(s_over, run2)] if s_over < run2 else [], WITH_CONFLICT, SENS,
           "DRAWN (structural sheet); the last 200 mm over head beam B20", "GFRS east column")
    # A2 (owner 27 on the architectural 1F plan allocation)
    st2 = "main stair 1F -> 2F (OWNER-27)"
    a2f1 = g[("ARCH-1F", "A2-F1")]["list"]
    foot_over = max(0.0, b20["y_north"] - a2f1[0]["face"])
    flight(st2, "A2-F1", seg2["A2-F1"], a2h, WIDTH_MAIN_MM, TREAD_LINE_MM, "FFRS", "y", a2f1[0]["face"], +1,
           [(0.0, foot_over)] if foot_over > 0 else [], WITH_CONFLICT, SENS,
           "DRAWN (architectural 1F plan = structural 1F sheet for this flight); foot on B20 (support zone apart)",
           "ARCH-1F west column")
    winder(st2, "A2-W1", a2h, g["_treads_A2"], g["_walk_A2"][0], g["_walk_A2"][1], WITH_CONFLICT,
           "APPROXIMATION; the structural 1F sheet draws this quarter flat", "ARCH-1F radial lines (registered)")
    plate(st2, "A2-L1", "FFRS", WITH_CONFLICT, SENS, "DRAWN; level not printed (+7.989 implied)", "FFRS NE quarter")
    a2f2 = g[("ARCH-1F", "A2-F2")]["list"]
    flight(st2, "A2-F2", seg2["A2-F2"], a2h, WIDTH_MAIN_MM, TREAD_LINE_MM, "FFRS", "y", a2f2[0]["face"], -1, [],
           WITH_CONFLICT, SENS, "DRAWN; ends 100 mm clear of B23", "ARCH-1F east column")
    plate(st2, "A2-T1", "FFRS", WITH_CONFLICT, SENS, "DRAWN arrival strip", "between B23 and the last riser")
    # C (round stair as drawn)
    st3 = "round (light-well) stair GF -> 1F (drawn 28)"
    cur = g[("GFRS", "C-F1:CURVED")]["list"]
    stl = g[("GFRS", "C-F1:STRAIGHT")]["list"]
    r_in = sum(c["r_in"] for c in cur) / len(cur)
    r_out = sum(c["r_out"] for c in cur) / len(cur)
    reg = curved_region(cur, stl[0]["face"], r_in, r_out)
    reg_alt = curved_region(cur, stl[0]["face"], g["_well_arcs"][0], g["_well_arcs"][1])
    r_w = (r_in + r_out) / 2
    end_ang = 270.0 + math.degrees(math.asin((stl[0]["face"] - WELL_C[0]) / r_w))
    wlen = math.radians(end_ang - cur[0]["angle"]) * r_w
    wgo = wlen / len(cur)
    for t in WAISTS_MM:
        v = RS.winder_plane_volume(reg.area / 1e6, ch, wgo, t)
        rows.append({"STAIR": st3, "ELEMENT_ID": "C-F1 (curved part)", "KIND": "CURVED FLIGHT", "STATUS":
                     "DRAWN_ARRANGEMENT_EVALUATED", "LANE": COND, "RISERS": len(cur), "RISER_MM": _r(ch, 10),
                     "GOING_MM": _r(wgo, 6), "WIDTH_MM": _r(r_out - r_in, 3), "WIDTH_ALT_MM": _r(g["_well_arcs"][1] -
                                                                                          g["_well_arcs"][0], 3),
                     "PITCH_DEG": _r(math.degrees(math.atan2(ch, wgo)), 6), "PLAN_AREA_M2": _r(reg.area / 1e6, 9),
                     "WAIST_MM": t, "GROSS_M3": _r(v, 9), "BEAM_OVERLAP_ZONE_M3": 0.0, "COLUMN_CUTOUT_M3": 0.0,
                     "NET_M3": _r(v, 9), "ALT_WIDTH_GROSS_M3": _r(RS.winder_plane_volume(reg_alt.area / 1e6, ch, wgo, t), 9),
                     "ALREADY_RELEASED_BY_S8_7": False,
                     "METHOD": f"plane-equivalent over the annular plan between the radial tread ends (r {_full(r_in, 1)} - "
                               f"{_full(r_out, 1)}), walking line r {_full(r_w, 1)} ({_full(wlen, 1)} mm / {len(cur)} "
                               "treads); a helical soffit is approximated",
                     "GEOMETRY_STATE": "APPROXIMATION: the curved soffit and its support are not drawn; ALT = the "
                                       "S-OPENING annulus", "EVIDENCE": "GFRS radial lines and S-OPENING arcs"})
    ca = []
    for line in ("BL015", "BL041"):
        co = [b["bbox"] for (bsh, ln_), b in bands.items() if bsh == "GFRS" and ln_ == line]
        if co and co[0][1] < STRAIGHT_Y[1] and co[0][3] > STRAIGHT_Y[0]:
            bb = co[0]
            a_, b_ = sorted(((bb[0] - stl[0]["face"]), (bb[2] - stl[0]["face"])))
            frac = (min(bb[3], STRAIGHT_Y[1]) - max(bb[1], STRAIGHT_Y[0])) / (STRAIGHT_Y[1] - STRAIGHT_Y[0])
            ca.append((max(0.0, a_), min((len(stl) - 1) * GOING_MM, b_), frac))
    flight(st3, "C-F1:STRAIGHT", len(stl), ch, TREAD_LINE_MM, 1200.0, "GFRS", "x", stl[0]["face"], +1, ca,
           "DRAWN_ARRANGEMENT_EVALUATED", SENS, "DRAWN; width = tread lines (ALT 1200 to the void edge); beam CA "
                                                "crosses it (level not stated)", "GFRS straight treads")
    plate(st3, "C-L1", "GFRS", "DRAWN_ARRANGEMENT_EVALUATED", SENS, "DRAWN; level not printed (+4.696 implied)",
          "GFRS corner landing")
    sh_ = g[("GFRS", "C-F2")]["list"]
    flight(st3, "C-F2", len(sh_), ch, TREAD_LINE_MM, 1200.0, "GFRS", "y", sh_[0]["face"], +1, [],
           "DRAWN_ARRANGEMENT_EVALUATED", SENS, "DRAWN; width = tread lines (ALT 1200)", "GFRS short flight")
    for t in WAISTS_MM:
        rows.append({"STAIR": st3, "ELEMENT_ID": "C-T1", "KIND": "LANDING / PLATE", "STATUS": "DRAWN_ARRANGEMENT_EVALUATED",
                     "LANE": ALREADY, "PLAN_AREA_M2": _r(ct1_area, 9), "WAIST_MM": t, "GROSS_M3": _r(ct1_area * t / 1000, 9),
                     "BEAM_OVERLAP_ZONE_M3": 0.0, "COLUMN_CUTOUT_M3": 0.0, "NET_M3": 0.0, "ALREADY_RELEASED_BY_S8_7": True,
                     "METHOD": "S8.7 outline (frozen) x thickness; shown for completeness, never counted again",
                     "GEOMETRY_STATE": "DRAWN", "EVIDENCE": f"S8.7 released {released['C-T1']} m3 at 160 (frozen, unchanged)"})
    # steps on grade
    for el, n, h, w, evid in (("B-F1", len(g[("GBP", "B-F1")]["list"]), 700.0 / len(g[("GBP", "B-F1")]["list"]),
                               WIDTH_MAIN_MM, "GBP east column, +1.00 -> +0.30"),
                              ("D-F1", len(g[("GBP", "D-F1")]["list"]), 850.0 / len(g[("GBP", "D-F1")]["list"]),
                               ENTR_Y[1] - ENTR_Y[0], "GBP entrance, +0.15 -> +1.00")):
        from shapely.geometry import Polygon
        poly = outlines[el][1]
        lst = g[("GBP", el)]["list"]
        axis_x = el == "D-F1"
        o0 = lst[0]["face"]
        zones = []
        for (bsh, ln_), bd in sorted(bands.items()):
            if bsh != "GBP":
                continue
            x = poly.intersection(Polygon(bd["pts"]))
            if x.area > 1000.0:
                b_ = x.bounds
                lo_, hi_ = ((b_[0], b_[2]) if axis_x else (b_[1], b_[3]))
                s_ = sorted((abs(lo_ - o0), abs(hi_ - o0)))
                frac = x.area / ((hi_ - lo_) * w)
                zones.append((max(0.0, s_[0]), min((n - 1) * GOING_MM, s_[1]), frac, ln_))
        for t in WAISTS_MM:
            gross = SC.flight_section_volume(n, h, GOING_MM, w, t) / 1e9
            solid = SC.solid_steps_volume(n, h, GOING_MM, w) / 1e9
            ovz = sum(_overlap_volume(n, h, w, t, z[0], z[1]) * z[2] for z in zones if z[1] > z[0])
            rows.append({"STAIR": "steps on grade", "ELEMENT_ID": el, "KIND": "STEPS ON GRADE",
                         "STATUS": "DRAWN (riser count and levels printed)", "LANE": COND, "RISERS": n,
                         "RISER_MM": _r(h, 10), "GOING_MM": GOING_MM, "WIDTH_MM": w, "RUN_MM": (n - 1) * GOING_MM,
                         "PLAN_AREA_M2": _r((n - 1) * GOING_MM * w / 1e6, 9), "WAIST_MM": t, "GROSS_M3": _r(gross, 9),
                         "UPPER_BOUND_M3": _r(solid + (n - 1) * GOING_MM * w * t / 1e9, 9),
                         "BEAM_OVERLAP_ZONE_M3": _r(ovz, 9), "COLUMN_CUTOUT_M3": 0.0, "NET_M3": _r(gross - ovz, 9),
                         "ALREADY_RELEASED_BY_S8_7": False,
                         "METHOD": "two readings, construction not drawn: a waist slab on fill (exact integral) or "
                                   "solid steps on a slab of the case thickness (upper)",
                         "GEOMETRY_STATE": "CONDITIONAL: what lies under the steps is not drawn",
                         "EVIDENCE": evid + (f"; ground-beam zones {[z[3] for z in zones]}" if zones else "")})
    # totals (new quantities only: the S8.7 plates are excluded)
    tot = []
    for t in WAISTS_MM:
        for stair in (st1, st2, st3, "steps on grade"):
            rs = [r for r in rows if r["STAIR"] == stair and r["WAIST_MM"] == t]
            tot.append({"STAIR": stair, "ELEMENT_ID": "TOTAL NOT RELEASED (new; S8.7 plates excluded)",
                        "KIND": "TOTAL", "LANE": SENS if stair != "steps on grade" else COND, "WAIST_MM": t,
                        "GROSS_M3": _r(math.fsum(r["GROSS_M3"] for r in rs if not r["ALREADY_RELEASED_BY_S8_7"]), 9),
                        "NET_M3": _r(math.fsum(r["NET_M3"] for r in rs), 9),
                        "UPPER_BOUND_M3": _r(math.fsum(max(r["GROSS_M3"], r.get("UPPER_BOUND_M3") or 0.0,
                                                           r.get("ALT_WIDTH_GROSS_M3") or 0.0) for r in rs
                                                       if not r["ALREADY_RELEASED_BY_S8_7"]), 9),
                        "METHOD": "sum of the rows above; GROSS includes the beam overlap zones, NET excludes them and "
                                  "the column cut-outs; UPPER takes each row's largest reading (gross, alternative "
                                  "width, flat-soffit or solid-step bound)",
                        "ALREADY_RELEASED_BY_S8_7": False})
        rs = [x for x in tot if x["WAIST_MM"] == t]
        tot.append({"STAIR": "ALL", "ELEMENT_ID": "GRAND TOTAL NOT RELEASED", "KIND": "TOTAL", "LANE": SENS,
                    "WAIST_MM": t, "GROSS_M3": _r(math.fsum(x["GROSS_M3"] for x in rs), 9),
                    "NET_M3": _r(math.fsum(x["NET_M3"] for x in rs), 9),
                    "UPPER_BOUND_M3": _r(math.fsum(x["UPPER_BOUND_M3"] for x in rs), 9),
                    "METHOD": "never released; release delta 0 m3", "ALREADY_RELEASED_BY_S8_7": False})
    return rows + tot


def _poly(c):
    from shapely.geometry import Polygon
    p = Polygon(c["pts"])
    return p if p.is_valid else p.buffer(0)


# ------------------------------------------------------------------ reinforcement and ownership
def _seg_dist(p, a, b):
    ax, ay, bx, by_ = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by_ - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.dist(p, (ax + t * dx, ay + t * dy))


def rebar_rows(stexts, slines, sarcs, outlines, extra_polys, conc, s87_rebar, s7, occ):
    from shapely.geometry import Point
    rows = []
    polys = {el: p for el, (sh, p) in outlines.items()}
    polys.update(extra_polys)
    sheet_of = {el: sh for el, (sh, _) in outlines.items()}
    sheet_of.update({k: "GFRS" for k in extra_polys})
    callouts = []
    for sh in ("GFRS", "FFRS"):
        for t in stexts[sh]:
            txt = t["text"].replace("%%C", "Ø").replace("%%c", "Ø")
            if not re.fullmatch(r"8Ø16/m", txt):
                continue
            pt = Point(t["p"])
            els = sorted(el for el, pg in polys.items() if sheet_of[el] == sh and pg.buffer(400).contains(pt))
            if not els:
                continue
            near = [l for l in slines[sh] if l["layer"] in ("ST", "5") and _seg_dist(t["p"], l["a"], l["b"]) < 400]
            dirs = sorted({"N-S" if abs(l["a"][0] - l["b"][0]) < 0.5 else "E-W" if abs(l["a"][1] - l["b"][1]) < 0.5
                           else "INCLINED" for l in near})

            def on_arc(a):
                ang = math.degrees(math.atan2(t["p"][1] - a["c"][1], t["p"][0] - a["c"][0])) % 360
                return a["a0"] <= ang <= a["a1"] and abs(math.dist(t["p"], a["c"]) - a["r"]) < 400
            arcs = [a["handle"] for a in sarcs[sh] if a["layer"] == "5" and on_arc(a)]
            callouts.append(t["handle"])
            rows.append({"RECORD": "PLAN_CALLOUT", "SHEET": sh, "HANDLE": t["handle"], "FAMILY": "8Ø16/m",
                         "BAR_DIAMETER_MM": 16, "POSITION_MM": [_r(t["p"][0], 3), _r(t["p"][1], 3)],
                         "ELEMENTS": els, "DIRECTION": dirs + (["ALONG_CURVE"] if arcs else []),
                         "BAR_LINES": sorted(l["handle"] for l in near) + arcs, "PLACEMENT": "BOTTOM (p.16 role)",
                         "AUTHORITY": EXPLICIT, "EXISTING_OWNER": "S8.7 (released only over A1-L1 / A2-T1 / C-T1)",
                         "STATE": "EXPLICIT_RATE; no further release (geometry of the flights / turns not approved)"})
    for sh in ("GFRS", "FFRS"):
        for t in stexts[sh]:
            if t["text"].strip() != "16":
                continue
            pt = Point(t["p"])
            inside = sorted(el for el, pg in polys.items() if sheet_of[el] == sh and pg.contains(pt))
            near = sorted(f"{el} ({_full(pg.distance(pt), 0)} mm)" for el, pg in polys.items()
                          if sheet_of[el] == sh and not pg.contains(pt) and pg.distance(pt) <= 300)
            if inside or near:
                rows.append({"RECORD": "ZONE_TAG", "SHEET": sh, "HANDLE": t["handle"], "FAMILY": "'16' thickness tag",
                             "POSITION_MM": [_r(t["p"][0], 3), _r(t["p"][1], 3)], "ELEMENTS": inside,
                             "DIRECTION": [f"near {x}" for x in near],
                             "AUTHORITY": "ZONE_TAG (slab-thickness tag in the stair zone)",
                             "STATE": "not a waist dimension: it sits at a flight / turn junction or on a flight; the "
                                      "waist stays UNKNOWN"})
    fams = [("8Ø16/m", 16, "longitudinal along each flight; both ways across the turns and landings", "BOTTOM",
             EXPLICIT + " (nine plan callouts) + role from p.16", "S8.7 over the three released plates", "PARTLY_RELEASED"),
            ("6Ø14/m", 14, "longitudinal, cranked over each flight / landing junction and at the head", "TOP", TYPICAL,
             "none", BLOCKED),
            ("6Ø12/m", 12, "landing top, both ways", "TOP", TYPICAL, "none", BLOCKED),
            ("Ø12/20cm", 12, "transverse distribution over the main bars", "BOTTOM", TYPICAL, "none", BLOCKED),
            ("Ø8/15", 8, "bent step bar in each step", "STEP", TYPICAL, "none", BLOCKED),
            ("1Ø12", 12, "nosing corner bar along each step", "STEP", TYPICAL, "none", BLOCKED),
            ("6Ø16/m", 16, "starter from the ground beam into the first flight", "TOP at the foot", TYPICAL +
             "; no ground beam is drawn under either lower flight's foot", "none", BLOCKED),
            ("2Ø12 / 4Ø16 (20 x 40)", 16, "landing edge beam", "BEAM", TYPICAL + "; the project landings end on S6 "
             "edge beams", "S6 (edge beams)", BLOCKED),
            ("3Ø14 / 4Ø16 / 2Ø14/30 / Ø8/15", 16, "ground beam G.B at the foot", "BEAM", TYPICAL, "none", BLOCKED),
            ("2Ø12 / 4Ø16 / 6Ø8/m, depth AS PER SCH.", 16, "typical cranked stair beam, column to column", "BEAM",
             TYPICAL + "; no cranked beam is drawn on any plan or section", "S6 'With Stair' occurrences (BLOCKED there)",
             "OWNED_BY_S6 (not re-added)"),
            ("anchorage / development / laps / bends", None, "every family", "-", "NOT DIMENSIONED on any drawing", "none",
             BLOCKED)]
    for f, d, direction, place, auth, owner, state in fams:
        rows.append({"RECORD": "FAMILY", "FAMILY": f, "BAR_DIAMETER_MM": d, "DIRECTION": direction,
                     "PLACEMENT": place, "DEVELOPMENT_ANCHORAGE": "not dimensioned", "AUTHORITY": auth,
                     "EXISTING_OWNER": owner, "STATE": state})
    for r in s87_rebar:
        if r["QUANTITY_STATE"] in ("PROJECT_BASIS_QTO", "SOURCE_DERIVED_PHYSICAL"):
            rows.append({"RECORD": "S8_7_RELEASED (preserved)", "FAMILY": "8Ø16/m", "BAR_DIAMETER_MM": int(r["BAR_DIAMETER_MM"]),
                         "ELEMENTS": [r["FLIGHT_OR_LANDING_ID"]], "DIRECTION": r["PHYSICAL_BAR_ROLE"],
                         "PLACEMENT": "BOTTOM", "AUTHORITY": EXPLICIT, "EXISTING_OWNER": "S8.7 (frozen)",
                         "KG": float(r["KG"]), "STATE": "UNCHANGED; not counted again"})
    rows.append({"RECORD": "S7_OWNED (preserved)", "FAMILY": "S7 top extensions at stair-adjacent supports",
                 "BAR_DIAMETER_MM": sorted({int(float(x["BAR_DIAMETER_MM"])) for x in s7 if x.get("BAR_DIAMETER_MM")})
                 or None, "PLACEMENT": "TOP (slab)", "EXISTING_OWNER": "S7 (released, frozen)",
                 "KG": _r(math.fsum(float(x["KG_FROM_BAR_RUNS"]) for x in s7), 9), "ELEMENTS": [f"{len(s7)} strip ends"],
                 "STATE": "OWNED_ONCE_BY_S7; S8.7B adds no top bar at these supports"})
    for sh, line, what, rng in (("GFRS", "BL020", "B20 head beam", (X_BAY_W, X_BAY_E)),
                                ("FFRS", "BL009", "B23 head beam", (X_BAY_W, X_BAY_E)),
                                ("GFRS", "BL033", "'With Stair' north edge (GF -> 1F)", (X_BAY_W, X_BAY_E)),
                                ("FFRS", "BL023", "'With Stair' north edge (1F -> 2F)", (X_BAY_W, X_BAY_E)),
                                ("GFRS", "BL022", "'With Stair' light-well south edge", (20892.0, CF2_X[1])),
                                ("GFRS", "BL015", "beam CA", None)):
        for o in occ_list(occ, sh, line, rng):
            if not o["mark"]:
                continue
            rows.append({"RECORD": "S6_OWNED", "SHEET": sh, "HANDLE": o["occurrence_id"], "FAMILY": f"{what} ({o['mark']})",
                         "EXISTING_OWNER": "S6 / S6.1", "KG": float(o["known_kg"] or 0),
                         "STATE": f"{o['occurrence_state']} in S6; not re-added, not moved"})
    kg16 = kg_per_m(16)
    for r in conc:
        if r.get("KIND") == "FLIGHT" and r["WAIST_MM"] == 160.0 and r["STAIR"] != "steps on grade":
            L = RS.bar_length_rate(8, r["WIDTH_MM"], r["INCLINED_LENGTH_MM"])
            rows.append({"RECORD": "SENSITIVITY_KG", "FAMILY": "8Ø16/m", "BAR_DIAMETER_MM": 16,
                         "ELEMENTS": [r["ELEMENT_ID"]], "DIRECTION": "longitudinal along the flight", "PLACEMENT": "BOTTOM",
                         "AUTHORITY": EXPLICIT + " (rate); length from the provisional riser count",
                         "EQUIVALENT_LENGTH_M": _r(L, 9), "KG": _r(L * kg16, 9), "LANE": SENS,
                         "STATE": "not released; anchorage, laps and the transverse / top families excluded (blocked); "
                                  "independent of the waist"})
        if r.get("KIND") in ("WINDER TURN", "CURVED FLIGHT") and r["WAIST_MM"] == 160.0:
            rows.append({"RECORD": "SENSITIVITY_KG", "FAMILY": "8Ø16/m", "BAR_DIAMETER_MM": 16,
                         "ELEMENTS": [r["ELEMENT_ID"]], "LANE": BLOCKED, "KG": None,
                         "STATE": "bar paths through the turn / along the curve not established"})
    return rows, callouts


QUESTIONS = {
    "Q-ST7B-01": ("architect / owner", "GF -> 1F: the owner's 28 risers (160.714 mm) cannot reach the printed +3.50 "
                  "half-landing with equal risers (it falls between riser 15 at +3.411 and riser 16 at +3.571). Section "
                  "A-A draws 15 + 12 = 27 risers of 166.667 mm to that level. Which governs: the printed +3.50 (and "
                  "27 risers), or 28 risers with the landing at +3.571?"),
    "Q-ST7B-02": ("engineer / architect", "GF -> 1F head: with 12 upper risers (structural sheet, section A-A) the last "
                  "riser is 200 mm inside head beam B20 and the top tread sits over the beam at the 1F floor. Is B20 "
                  "lowered / cranked under the top tread, or does the flight end at the architectural position (100 mm "
                  "clear of B20, 11 upper risers)?"),
    "Q-ST7B-03": ("architect / engineer", "GF -> 1F foot: the structural sheet starts the lower flight two goings "
                  "earlier than the architectural and ground-beam plans. Which foot position, and what supports it (no "
                  "ground beam is drawn under it; p.16's G.B is typical only)?"),
    "Q-ST7B-04": ("owner / architect", "GF -> 1F riser height: 160.714 mm is 0.714 mm above the preferred 160 mm. "
                  "Accept as a tolerance, or change the count (29 = 155.172, 30 = 150.0) knowing that neither reaches "
                  "+3.50 with equal risers either?"),
    "Q-ST7B-05": ("architect / engineer", "1F -> 2F: the owner's 27 risers need the four-riser winder turn of the "
                  "architectural 1F plan; the structural 1F roof sheet and the 2F plan draw that quarter flat (24 "
                  "risers). Confirm the winders and their structural form."),
    "Q-ST7B-06": ("architect", "1F -> 2F half-landing level: not printed. 27 risers put it at +7.989; section A-A "
                  "scales to about +7.69 (13 + 12 = 25 risers of 168 mm). Confirm the level and the count."),
    "Q-ST7B-07": ("engineer / architect", "1F -> 2F head: with the owner's 11 upper risers the last riser stops 100 mm "
                  "clear of B23 (the S8.7 arrival strip A2-T1 fills the gap). Section A-A draws 12, which would put the "
                  "last riser inside B23. Confirm 11."),
    "Q-ST7B-08": ("engineer", "Structural waist thickness (normal to the soffit) of the flights, the winder turns and "
                  "the curved flight, and the landing thickness: p.16 says 'THICK' without a value and the plan '16' "
                  "tags are zone tags."),
    "Q-ST7B-09": ("architect", "Stair finish: is the 30 mm marble inclusive of its bedding / adhesive? State the "
                  "bedding, and the floor build-ups (screed + tile + adhesive) at GF, 1F, 2F and on the landings."),
    "Q-ST7B-10": ("engineer", "Which p.16 typical bars apply here (6Ø14/m junction and head top bars, 6Ø12/m landing "
                  "top, Ø12/20 distribution, Ø8/15 step bars, 1Ø12 nosing bars, 6Ø16/m starters), and the anchorage / "
                  "laps of the 8Ø16/m main bars into the beams."),
    "Q-ST7B-11": ("engineer", "Are the 'With Stair' beams (B3 on the GF and 1F roof sheets, CB3 in the light well) the "
                  "p.16 cranked stair beam? Their depth 'AS PER SCH.' and the level at which they carry the landings."),
    "Q-ST7B-12": ("architect / engineer", "Round (light-well) stair: confirm 28 risers, the foot level (+1.00 is not "
                  "printed inside the light well), the corner-landing level (+4.696 with equal risers; not printed), "
                  "the structural width (tread lines 1150; opening annulus 1250), the curved soffit and its supports, "
                  "and the level of beam CA across the straight part."),
    "Q-ST7B-13": ("engineer", "Winder soffit form for both turns (warped, inclined or a flat slab under solid steps): "
                  "the two readings differ by a factor of about two."),
    "Q-ST7B-14": ("architect / engineer", "Steps on grade (lobby +1.00 -> +0.30, entrance +0.15 -> +1.00): solid "
                  "concrete or a slab on fill, and the thickness."),
}


def conservation(L):
    out = []

    def A(cid, text, ok, detail=""):
        out.append({"CHECK_ID": cid, "CHECK": text, "RESULT": "PASS" if ok else "FAIL", "DETAIL": detail})
    A("C01", "all 27 earlier freezes (S4 ... S8.8, S8.7A), the S8.3 errata and the register indexes verify before "
      "and after the build", len(L["frozen"]) == 27, f"{len(L['frozen'])} manifests")
    s87 = _j(READ["S87_SUMMARY"])["released"]
    A("C02", "S8.7's frozen release is unchanged and this layer releases nothing (delta 0 m3, 0 kg)",
      abs(s87["concrete_m3"] - 0.516582788) < 1e-12 and abs(s87["kg"] - 59.020862261) < 1e-9 and
      L["release_delta"] == {"concrete_m3": 0.0, "kg": 0.0}, json.dumps(s87, sort_keys=True))
    A("C03", "the S8.7 plates (A1-L1, A2-T1, C-T1) are excluded from every new total",
      all(r["NET_M3"] == 0.0 for r in L["conc"] if r.get("ALREADY_RELEASED_BY_S8_7")) and
      {r["ELEMENT_ID"] for r in L["conc"] if r.get("ALREADY_RELEASED_BY_S8_7")} == {"A1-L1", "A2-T1", "C-T1"}, "")
    A("C04", "the independent plan recount equals S8.7A's frozen per-view totals", L["s87a_match"]["ok"],
      json.dumps(L["s87a_match"]["detail"], sort_keys=True))
    A("C05", "every riser schedule closes exactly on its top FFL and its finished risers are equal",
      all(abs(r["FINISHED_LEVEL_EXACT_M"] - L["sc"][r["SCENARIO"]]["t"] / 1000) < 1e-9
          for r in L["sched"] if r["RISES_ONTO"] == "TOP_FLOOR"), "")
    A("C06", "setting out: cumulative levels rounded to 1 mm stay within 0.5 mm and the rounded risers add up to "
      "the rise", all(abs(r["SETTING_OUT_DEVIATION_MM"]) <= 0.5 + 1e-9 for r in L["sched"]), "")
    A("C07", "finish datums: the separately written datum model equals the closed form and closes on SSL_t - SSL_b",
      all(abs(r["CLOSURE_MM"]) < 1e-6 for r in L["fin"] if r.get("CLOSURE_MM") is not None), "")
    A("C08", "every flight volume: exact section integral = stair_geometry outline (checked row by row)",
      len([r for r in L["conc"] if r.get("KIND") == "FLIGHT"]) > 0, "asserted in the build")
    A("C09", "no double count at beams and columns: GROSS = NET + beam overlap zone + column cut-out on every row",
      all(abs(r["GROSS_M3"] - r["NET_M3"] - r["BEAM_OVERLAP_ZONE_M3"] - r["COLUMN_CUTOUT_M3"]) < 5e-9
          for r in L["conc"] if r.get("KIND") not in ("TOTAL",) and not r.get("ALREADY_RELEASED_BY_S8_7")), "")
    A("C10", "section A-A calibration: four chain lines on 1:100 within 2 px; +1.00 / +5.50 / +9.70 within 15 mm",
      L["sec"]["scale_px_per_m"] > 0, f"{_full(L['sec']['scale_px_per_m'], 3)} px/m")
    A("C11", "section A-A riser counts: GF -> 1F 15 + 12 (166.667 mm), 1F -> 2F 13 + 12 (168 mm); +3.50 printed and "
      "measured", (L["sec"]["flights"]["A1"]["lower"]["n"], L["sec"]["flights"]["A1"]["upper"]["n"],
                   L["sec"]["flights"]["A2"]["lower"]["n"], L["sec"]["flights"]["A2"]["upper"]["n"]) == (15, 12, 13, 12),
      "")
    A("C12", "no scenario quantity sits in a released lane",
      not [r for r in L["conc"] if r.get("LANE") in RELEASED_LANES] and
      not [r for r in L["rebar"] if r.get("LANE") in RELEASED_LANES], "")
    A("C13", "the S7 top-extension record is preserved (75 strip ends, 71.895327413 kg)",
      len(L["s7"]) == 75 and abs(math.fsum(float(x["KG_FROM_BAR_RUNS"]) for x in L["s7"]) - 71.895327413) < 1e-6, "")
    A("C14", "the nine 8Ø16/m plan callouts read again equal S8.7's bindings",
      sorted(L["callouts"]) == sorted(L["s87_callouts"]), json.dumps(sorted(L["callouts"])))
    A("C15", "the owner's main-stair decisions are not applied to the round stair",
      all("OWNER" not in r["SCENARIO"] for r in L["sched"] if r["SCENARIO"].startswith("C-")), "")
    A("C16", "plan areas less columns against S8.7's outlines: every difference is the stated cause",
      all(abs(d["diff_m2"] - d["expected_m2"]) < 1e-6 for d in L["area_cmp"]), json.dumps(L["area_cmp"], sort_keys=True))
    return out


def level_rows(levels):
    from shapely.geometry import Point, box
    zones = {"main bay NE quarter (under the turn landing)": box(X_WALL_E, Y_WALL_END, X_BAY_E, Y_BAY_N),
             "main bay NW quarter (turn)": box(X_BAY_W, Y_TURN, X_WALL_E, Y_BAY_N),
             "main bay east column": box(X_WALL_E, 16311.856, X_BAY_E, Y_WALL_END),
             "main bay west column": box(X_BAY_W, 16311.856, X_WALL_W, Y_TURN),
             "light well": Point(WELL_C).buffer(2900).union(box(23600, 8900, 28000, 13000))}
    rows = []
    for x in sorted(levels, key=lambda x: (x["plan"], x["handle"])):
        pt = Point(x["p"])
        z = [k for k, b in zones.items() if b.contains(pt)]
        near = min(((k, b.distance(pt)) for k, b in zones.items()), key=lambda kv: kv[1])
        rows.append({"RECORD": "PLAN_LEVEL_TEXT", "ITEM": f"{x['plan']} '{x['text']}' ({x['handle']})", "PIXEL_X": None,
                     "VALUE": x["text"], "UNIT": "m", "STATUS": PRINTED,
                     "EVIDENCE": f"registered at ({_full(x['p'][0], 1)}, {_full(x['p'][1], 1)}); "
                                 + (f"inside the {z[0]}" if z else f"{_full(near[1], 0)} mm from the {near[0]}")})
    return rows


# ------------------------------------------------------------------ build
def run():
    from shapely.geometry import box
    frozen, errata, index = verify_inputs()
    src, frames, slines, stexts, sarcs, scols = structural_read()
    T, alines, levels = architectural_read()
    views = {"GBP": slines["GBP"], "GFRS": slines["GFRS"], "FFRS": slines["FFRS"], **alines}
    counts, ev = recount(views)
    arr = drawn_arrangements(counts)
    sec = section_a_a()
    outlines = element_outlines(counts)
    reg = box(X_BAY_W, Y_TURN, X_WALL_E, Y_BAY_N)
    for key, view, el in (("A1", "GFRS", "A1-W1"), ("A2", "ARCH-1F", "A2-W1")):
        tr, centre, miss = winder_treads(counts[(view, el)]["rad"], reg)
        check(len(tr) == counts[(view, el)]["radial"] + 1, f"{el}: treads = radial risers + 1")
        check(abs(sum(p.area for p in tr) - reg.area) < 1.0, f"{el}: treads tile the quarter")
        counts[f"_treads_{key}"] = tr
        counts[f"_walk_{key}"] = walking_going(centre, len(tr))
        counts[f"_fan_{key}"] = (centre, miss)
    op = sorted(a["r"] for a in sarcs["GFRS"] if a["layer"] == "S-OPENING" and math.dist(a["c"], WELL_C) < 1.0)
    check(len(op) == 2, "the light-well opening annulus (two S-OPENING arcs)")
    counts["_well_arcs"] = (op[0], op[1])
    edges = head_beam_edges(slines)
    bands = beam_bands(src)
    occ = s6_occurrences()
    s87c = _rows(READ["S87_CONCRETE"])
    released = {r["ELEMENT_ID"]: float(r["CONCRETE_M3"]) for r in s87c
                if r["CONCRETE_M3"] and r["LANE"] in ("PROJECT_BASIS_QTO", "SOURCE_VERIFIED")}
    check(set(released) == {"A1-L1", "A2-T1", "C-T1"}, "S8.7 released three plates")
    s87g = {r["ELEMENT_ID"]: r for r in _rows(READ["S87_GEOMETRY"])}
    sc = owner_segments(arr)
    check(sum(x[2] for x in sc["A1-OWNER-28"]["segments"]) == OWNER["A1_RISERS"], "owner 28 = the GFRS arrangement")
    check(sum(x[2] for x in sc["A2-OWNER-27"]["segments"]) == OWNER["A2_RISERS"], "owner 27 = the ARCH-1F arrangement")
    cur = counts[("GFRS", "C-F1:CURVED")]["list"]
    stl = counts[("GFRS", "C-F1:STRAIGHT")]["list"]
    r_in = sum(c["r_in"] for c in cur) / len(cur)
    r_out = sum(c["r_out"] for c in cur) / len(cur)
    creg = curved_region(cur, stl[0]["face"], r_in, r_out)
    conc = concrete_rows(sc, counts, outlines, scols, edges, bands, released,
                         float(s87g["C-T1"]["PLAN_PROJECTED_AREA_M2"]))
    s87a = _rows(READ["S87A_COUNTS"])
    detail, ok = {}, True
    for run_, view in (("A1", "GFRS"), ("A1", "ARCH-GF"), ("A2", "FFRS"), ("A2", "ARCH-1F"), ("A2", "ARCH-2F"),
                       ("C", "GFRS"), ("C", "ARCH-1F"), ("C", "ARCH-GF")):
        want = [r for r in s87a if r["STOREY_RUN"] == run_ and r["VIEW"] == view and r["KIND"].startswith("DRAWN_COUNT")]
        got = arr[(run_, view)]["total"]
        detail[f"{run_}:{view}"] = [got, int(want[0]["TOTAL_RISERS"]) if want else None]
        ok = ok and bool(want) and int(want[0]["TOTAL_RISERS"]) == got
    area_cmp = []
    expected = {"A1-W1": (-0.005, "S8.7 includes the 150 x 50 strip beside the wall end below the turn riser line "
                                  "(less its 50 x 50 wall corner)"),
                "A2-W1": (-0.005, "as A1-W1"),
                "C-F2": (-(1200.0 - TREAD_LINE_MM) * 1200.0 / 1e6, "S8.7 takes the flight from the void edge (1200 "
                                                                     "wide); S8.7B the tread lines (1150; 1200 kept as "
                                                                     "the alternative width)")}
    for el in ("A1-F1", "A1-W1", "A1-L1", "A1-F2", "A2-F1", "A2-W1", "A2-L1", "A2-F2", "A2-T1", "C-L1", "C-F2",
               "B-F1", "D-F1"):
        sh, poly = outlines[el]
        cols_in = [(c["handle"], poly.intersection(_poly(c)).area / 1e6) for c in scols[sh]
                   if poly.intersection(_poly(c)).area > 1.0]
        mine = poly.area / 1e6 - sum(a for _, a in cols_in)
        theirs = float(s87g[el]["PLAN_PROJECTED_AREA_M2"])
        exp, why = expected.get(el, (0.0, "same outline"))
        area_cmp.append({"element": el, "s8_7b_m2": _r(mine, 6), "s8_7_m2": theirs, "diff_m2": _r(mine - theirs, 6),
                         "expected_m2": _r(exp, 6), "columns_removed": [[h, _r(a, 6)] for h, a in cols_in],
                         "s8_7_columns_removed": json.loads(s87g[el]["COLUMN_OUTLINES_REMOVED"] or "[]"), "why": why})
    rebar, callouts = rebar_rows(stexts, slines, sarcs, outlines, {"C-F1:CURVED": creg}, conc,
                                 _rows(READ["S87_REBAR"]), _rows(READ["S87_S7"]), occ)
    s87_callouts = [r["HANDLE"] for r in _rows(READ["S87_BINDING"]) if r["SOURCE"].startswith("ST7757 ") and
                    r["TEXT"] == "8%%C16/m"]
    L = {"frozen": frozen, "errata": errata, "index": index, "counts": counts, "ev": ev, "arr": arr, "sec": sec,
         "outlines": outlines, "edges": edges, "bands": bands, "occ": occ, "sc": sc, "conc": conc, "rebar": rebar,
         "callouts": callouts, "s87_callouts": s87_callouts, "levels": levels, "released": released,
         "s7": _rows(READ["S87_S7"]), "s87a_match": {"ok": ok, "detail": detail}, "area_cmp": area_cmp,
         "release_delta": {"concrete_m3": 0.0, "kg": 0.0}, "T": T}
    L["owner"] = owner_register(levels)
    L["risers"] = riser_rows(arr, sec)
    L["sched"] = setting_out_rows(sc)
    L["landings"] = landing_rows(arr, sec, sc)
    L["conflicts"] = conflict_rows(arr, counts, sec, edges)
    L["beams"] = beam_rows(counts, edges, bands, outlines, occ)
    L["fin"] = finish_rows(sc)
    L["evidence13"] = sec["rows"] + level_rows(levels) + [
        {"RECORD": "P16_VISUAL_RECORD", "ITEM": f"{a} {b}: {c}", "VALUE": d, "STATUS": e,
         "EVIDENCE": "ST7757.pdf p.16 (no vector text), rendered 100 / 300 dpi this round; renders not kept"}
        for a, b, c, d, e in P16_FACTS]
    L["cons"] = conservation(L)
    check(all(x["RESULT"] == "PASS" for x in L["cons"]), "conservation: " + json.dumps(
        [x for x in L["cons"] if x["RESULT"] != "PASS"]))
    return L


def provenance(L):
    lines = [{"record": "OWNER_DECISIONS", "a1_risers": OWNER["A1_RISERS"], "a2_risers": OWNER["A2_RISERS"],
              "waist": "UNKNOWN", "stair_finish_mm": OWNER["STAIR_FINISH_MM"], "bedding": "NOT_STATED",
              "state": PROV_OWNER}]
    for k, v in sorted(L["arr"].items()):
        lines.append({"record": f"DRAWN_ARRANGEMENT:{k[0]}:{k[1]}", **v})
    for run_, f in sorted(L["sec"]["flights"].items()):
        lines.append({"record": f"SECTION_A_A:{run_}", "lower": f["lower"]["n"], "upper": f["upper"]["n"],
                      "landing_m": _r(f["landing_m"], 4), "on_grid": [f["lower"]["on_grid"], f["upper"]["on_grid"]],
                      "missing": [f["lower"]["missing"], f["upper"]["missing"]]})
    for r in L["conc"]:
        lines.append({"record": f"CONCRETE:{r['ELEMENT_ID']}:{r.get('WAIST_MM')}", "stair": r["STAIR"],
                      "lane": r.get("LANE"), "gross_m3": r.get("GROSS_M3"), "net_m3": r.get("NET_M3")})
    lines.append({"record": "RENDERS", "tool": "pdftoppm", "dpi": SEC["dpi"],
                  "state": "temporary folder, deleted after measuring; never committed"})
    (HERE / OUTPUTS[15]).write_text("".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in lines),
                                    encoding="utf-8")


def write(L):
    _csv(OUTPUTS[1], L["owner"])
    _csv(OUTPUTS[2], L["risers"])
    _csv(OUTPUTS[3], L["sched"])
    _csv(OUTPUTS[4], L["landings"])
    _csv(OUTPUTS[5], L["conflicts"])
    _csv(OUTPUTS[6], L["beams"])
    _csv(OUTPUTS[7], L["fin"])
    _csv(OUTPUTS[8], L["conc"])
    _csv(OUTPUTS[9], L["rebar"])
    _csv(OUTPUTS[10], [{"QUESTION_ID": k, "TO": v[0], "QUESTION": v[1], "STATUS": "OPEN"} for k, v in QUESTIONS.items()])
    _csv(OUTPUTS[11], L["cons"])
    _csv(OUTPUTS[12], L["ev"])
    _csv(OUTPUTS[13], L["evidence13"], ["RECORD", "ITEM", "PIXEL_X", "VALUE", "UNIT", "STATUS", "EVIDENCE"])
    provenance(L)
    s87s = _j(READ["S87_SUMMARY"])
    tot = {}
    for r in L["conc"]:
        if r["KIND"] == "TOTAL":
            tot.setdefault(r["STAIR"], {})[str(int(r["WAIST_MM"]))] = {"gross": r["GROSS_M3"], "net": r["NET_M3"],
                                                                       "upper": r["UPPER_BOUND_M3"]}
    kg = math.fsum(r["KG"] for r in L["rebar"] if r.get("RECORD") == "SENSITIVITY_KG" and r.get("KG"))
    land = {r["ARRANGEMENT"]: r for r in L["landings"] if r["STAIR_RUN"] == "A1"}
    beams = {(r["INTERFACE"], r.get("ARRANGEMENT")): r for r in L["beams"]}
    summary = {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "layer_over": ["research/alsenan_stairs_s8_7 (frozen; unchanged)",
                       "research/alsenan_stairs_s8_7a (frozen; unchanged)"],
        "owner_scenario": {"A1_risers": 28, "A2_risers": 27, "waist": "UNKNOWN (REQUIRES_ENGINEER_CONFIRMATION)",
                           "stair_finish_mm": 30.0, "bedding": "NOT_STATED", "state": PROV_OWNER},
        "answers": {
            "A1_28_landing": {"printed_m": 3.50, "implied_m": _r(1 + 16 * 4.5 / 28, 9), "difference_mm":
                              _r((1 + 16 * 4.5 / 28 - 3.5) * 1000, 6), "reachable_with_uniform_risers": False,
                              "uniform_counts_reaching_3_50": land["every uniform count 20 - 40 that reaches the printed "
                                                                   "+3.50"]["RISERS"],
                              "state": WITH_CONFLICT},
            "A1_28_B20": {"last_riser_y": beams[("A1-F2 head / B20", "OWNER-28 (structural GF roof sheet)")]
                          ["LAST_RISER_FACE_Y_MM"], "clearance_mm": beams[("A1-F2 head / B20",
                                                                           "OWNER-28 (structural GF roof sheet)")]
                          ["CLEARANCE_TO_BEAM_FACE_MM"], "state": WITH_CONFLICT},
            "A2_27_winders": {"drawn_by": "architectural 1F plan only", "structural_1F_roof_sheet": "flat quarter",
                              "state": WITH_CONFLICT},
            "A2_27_B23": {"clearance_mm": beams[("A2-F2 head / B23", "OWNER-27 (architectural 1F plan)")]
                          ["CLEARANCE_TO_BEAM_FACE_MM"], "state": "CLEAR"},
            "C_28": {"supported_by": ["GF roof sheet", "architectural 1F plan"], "second_view": "architectural GF plan "
                     "draws 27 (one fewer in the short flight)", "landing": "not printed (+4.696 implied)",
                     "state": "INDEPENDENTLY_DRAWN_ON_TWO_PRIMARY_VIEWS; not owner-approved"},
            "landing_levels": {"A1": "PRINTED +3.50 (section A-A '320' from +0.30; measured +"
                               f"{_full(L['sec']['a1_landing_m'], 3)})",
                               "A2": f"NOT PRINTED (+7.989 under 27; section A-A scales +{_full(L['sec']['a2_landing_m'], 3)})",
                               "C": "NOT PRINTED (+4.696 under 28)"},
            "finish_30mm": "changes no finished level or finished riser; it lowers every concrete tread by the full "
                           "tread build-up and makes the first / last concrete risers h + f_b - s / h - f_t + s; with the "
                           "floor build-up equal to the stair build-up every concrete riser equals h",
            "section_a_a": {"GF_1F": "15 + 12 = 27 risers of 166.667 mm, landing +3.50",
                            "1F_2F": "13 + 12 = 25 risers of 168 mm, landing about +7.69"}},
        "concrete_sensitivity_m3_by_waist": tot,
        "main_bar_sensitivity_kg_8d16": _r(kg, 9),
        "release_delta": L["release_delta"],
        "frozen_release_unchanged": {"concrete_m3": s87s["released"]["concrete_m3"], "kg": s87s["released"]["kg"]},
        "blocked_reinforcement": [r["FAMILY"] for r in L["rebar"] if r.get("RECORD") == "FAMILY" and
                                  r["STATE"] == BLOCKED],
        "questions": sorted(QUESTIONS), "conservation": {x["CHECK_ID"]: x["RESULT"] for x in L["cons"]},
        "frozen_baselines": {k: v["manifest_sha256"] for k, v in L["frozen"].items()},
        "register_indexes": L["index"], "s8_3_errata_sha256": L["errata"], "unit_mass": UM.describe(UNIT_MASS),
        "references_read": [],
        "rule": "a provisional owner scenario evaluated against the drawings; nothing approved, selected or released"}
    _json(OUTPUTS[14], summary)
    (HERE / OUTPUTS[0]).write_text(readme(summary, L), encoding="utf-8")
    manifest = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "FROZEN_BEFORE_COMPARISON",
                "layer_over": summary["layer_over"], "s8_7_manifest_sha256": _sha(S87_MANIFEST),
                "s8_7a_manifest_sha256": _sha(S87A_MANIFEST), "engine_commit_stamp": summary["engine_commit"],
                "references_read": [], "code": {c_: _sha(ROOT / c_) for c_ in CODE},
                "inputs": {str(p_.relative_to(ROOT)): _sha(p_) for p_ in READ.values()},
                "drawing_sha256": {"P7757.dxf": ARCH_SHA, "ST7757.dxf": STRUCT_SHA, "ST7757.pdf": STRUCT_PDF_SHA,
                                   "P7757 sections PDF": ARCH_PDF_SHA},
                "frozen_baselines": summary["frozen_baselines"], "register_indexes": L["index"],
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "release_delta": L["release_delta"],
                "rule": "frozen before any earlier Urban, contractor or third-party stair figure is read; the "
                        "comparison after it explains differences and never changes a frozen quantity"}
    _json(MANIFEST_NAME, manifest)
    for k, m_ in MANIFESTS.items():
        DR.verify_frozen(m_, ROOT)
    for o in OUTPUTS + [MANIFEST_NAME]:
        check(not HYGIENE.search((HERE / o).read_text(encoding="utf-8")), f"hygiene: {o}")
    return summary


def readme(s, L):
    a = s["answers"]
    sec = L["sec"]
    f1, f2 = sec["flights"]["A1"], sec["flights"]["A2"]
    tot = s["concrete_sensitivity_m3_by_waist"]
    stairs = [k for k in tot if k != "ALL"]

    def trow(k):
        return " | ".join(f"{_full(tot[k][w]['gross'], 3)} / {_full(tot[k][w]['net'], 3)}" for w in ("150", "160", "175",
                                                                                                    "200"))
    t = "\n".join(f"   | {k} | {trow(k)} |" for k in stairs + ["ALL"])
    b20 = next(r for r in L["beams"] if r["INTERFACE"] == "A1-F2 head / B20" and r["ARRANGEMENT"].startswith("OWNER"))
    b20z = b20["OVERLAP_ZONE_M3_BY_WAIST"]
    fin = {(r["SCENARIO"], r.get("TREAD_BUILD_UP_MM"), r.get("FLOOR_BUILD_UP_BOTTOM_MM")): r for r in L["fin"]
           if r["CASE"] == "GRID"}
    e50 = fin[("A1-OWNER-28", 30.0, 50.0)]
    e80 = fin[("A1-OWNER-28", 50.0, 80.0)]
    req = next(r for r in L["fin"] if r["CASE"] == "200_100_REQUIREMENT" and r["SCENARIO"] == "A1-OWNER-28"
               and r["TREAD_BUILD_UP_MM"] == 30.0)
    blocked = ", ".join(s["blocked_reinforcement"])
    return f"""# S8.7B staircase owner scenario and engineering reconciliation

Round {ROUND}, baseline `{BASELINE_HEAD}`, engine `{s['engine_commit']}`. A research scenario layer over the frozen S8.7
package and the S8.7A correction layer; both are unchanged and verified. **Release delta: 0 m3 concrete and 0 kg
reinforcement.** S8.7's frozen release ({s['frozen_release_unchanged']['concrete_m3']} m3,
{s['frozen_release_unchanged']['kg']} kg) is untouched. A zero delta means nothing more is released here, not that
the stairs contain no concrete or steel. Passing tests prove the arithmetic and the reading, not engineering approval.

## The owner's provisional scenario

| Parameter | Owner scenario | Status |
|---|---|---|
| Main stair, GF -> 1F | 28 risers | PROVISIONAL_OWNER_SCENARIO |
| Main stair, 1F -> 2F | 27 risers | PROVISIONAL_OWNER_SCENARIO |
| Structural stair waist | UNKNOWN | REQUIRES_ENGINEER_CONFIRMATION |
| Marble / stair finish | 30 mm (bedding not stated, never assumed inside it) | PROVISIONAL_OWNER_SCENARIO |

The round (light-well) stair is evaluated on its own drawn 28-riser arrangement; the owner's decisions are not read
as an approval of it.

## Findings

1. **GF -> 1F, 28 risers: PROVISIONAL_SCENARIO_WITH_CONFLICT.**
   - The finished riser is 4500 / 28 = 160.714285714 mm, 0.714 mm above the preferred 160 mm maximum. This is a
     tolerance decision for the owner, not an automatic approval.
   - **Landing.** The half-landing is printed at +3.50: section A-A dimensions it '320' above the +0.30 lobby
     floor, and its level line measures +{_full(sec['a1_landing_m'], 3)}.
     - With 28 equal risers that level falls between riser 15 (+3.411) and riser 16 (+3.571).
     - The only drawn 28-riser allocation (the structural GF roof sheet: 12 + 4 + 12) lands at
       +{_full(a['A1_28_landing']['implied_m'], 3)}, {_full(a['A1_28_landing']['difference_mm'], 1)} mm above the
       printed level.
     - Keeping +3.50 with that allocation would need unequal risers of 156.25 and 166.667 mm.
     - With equal risers only {' or '.join(str(n) for n in a['A1_28_landing']['uniform_counts_reaching_3_50'])}
       risers reach +3.50 (166.667 / 125 mm); none lies in the 150 - 160 mm band.
   - **B20.** On the structural sheet the 12th upper riser (y {_full(a['A1_28_B20']['last_riser_y'], 1)}) is
     {_full(-a['A1_28_B20']['clearance_mm'], 0)} mm inside head beam B20, so the top tread sits over the beam at
     the 1F floor. The overlap zone is {_full(b20z['150'], 3)} - {_full(b20z['200'], 3)} m3 (150 - 200 mm waist)
     and is reported apart. Nothing is resolved here: no flight is shortened and no beam is moved. The
     architectural plan's 11-riser upper flight stops 100 mm clear of B20.
   - **Foot.** The structural sheet starts the lower flight 600 mm (two goings) south of the architectural and
     ground-beam plans, and no ground beam is drawn under either foot.
   - **Section A-A (measured this round).** The section draws a third arrangement: {f1['lower']['n']} +
     {f1['upper']['n']} = {f1['lower']['n'] + f1['upper']['n']} equal risers of 166.667 mm, which reaches +3.50
     exactly.
2. **1F -> 2F, 27 risers: PROVISIONAL_SCENARIO_WITH_CONFLICT.**
   - The finished riser is 155.555555556 mm, inside the preference.
   - **Winders.** 27 needs the architectural 1F plan's four-riser winder turn (3 radial + closing). The structural
     1F roof sheet and the 2F plan draw that quarter flat (24 risers of 175 mm).
   - **B23.** The 11-riser upper flight stops {_full(a['A2_27_B23']['clearance_mm'], 0)} mm clear of head beam
     B23, with the S8.7 arrival strip A2-T1 between them. This is compatible.
   - **Landing.** No level is printed. 27 risers put it at +7.989; section A-A scales to
     +{_full(sec['a2_landing_m'], 3)} and draws {f2['lower']['n']} + {f2['upper']['n']} = 25 risers of 168 mm. Its
     12-riser upper flight would end inside B23.
   - **Foot.** The foot bears on B20 at the 1F floor. This is a support interface; its zone is reported apart.
3. **Round (light-well) stair, 28 risers: independently drawn, not owner-approved.**
   - The GF roof sheet and the architectural 1F plan agree: 12 curved + 11 straight, then a corner landing, then 5
     (160.714 mm). The architectural GF plan's second view draws one riser fewer.
   - No section cuts this stair. Its foot level is not printed inside the light well; its corner landing is not
     printed (+4.696 with equal risers); its 1F arrival '+5.50' is printed.
   - Beam CA crosses the straight part at an unstated level; its zone is deducted from NET.
4. **Landing levels.**
   - Established: GF -> 1F +3.50 (printed).
   - Inferred, not printed: 1F -> 2F (+7.989 under 27; section scale +7.69) and the round-stair corner landing
     (+4.696).
   - The +0.30 lobby under the GF -> 1F landing is printed on the GF plan and on the section.
5. **What the 30 mm finish changes.**
   - No finished level or finished riser moves. Every concrete tread lies the full tread build-up (marble + bedding)
     below its finished tread.
   - The first concrete riser is h + f_b - s and the last h - f_t + s (f = floor build-up, s = stair build-up);
     every other riser is h. Finished risers stay equal while the first and last concrete risers differ.
   - With s = 30 and f = 50 (illustrative) they are {_full(e50['FIRST_CONCRETE_RISER_MM'], 3)} /
     {_full(e50['LAST_CONCRETE_RISER_MM'], 3)} mm. With bedding 20 (s = 50) and f = 80 they are
     {_full(e80['FIRST_CONCRETE_RISER_MM'], 3)} / {_full(e80['LAST_CONCRETE_RISER_MM'], 3)} mm. With f = s every
     concrete riser equals h.
   - A 200 / 100 pair would need {_full(req['FLOOR_BUILD_UP_BOTTOM_MM'], 2)} / {_full(req['FLOOR_BUILD_UP_TOP_MM'], 2)}
     mm floor build-ups (s = 30). Nothing prints them, so the pair is not used.
   - Two drawn offsets exist but are indications only: section A-A draws a finish line about
     {_full(sec['finish_offset_mm'], 0)} mm above the structural treads, and p.16's typical detail shows 50 mm
     head and foot offsets.
6. **Concrete sensitivity by waist** (research only, never released; m3, GROSS / NET; NET excludes the beam overlap
   zones and column cut-outs; the S8.7 plates are excluded):

   | Stair | 150 | 160 | 175 | 200 |
   |---|---|---|---|---|
{t}

   Flights use an exact section integral between plumb cuts. Winders and the curved flight are plane-equivalent
   approximations; `08` gives a flat-soffit upper bound for the winders and solid-step readings for the steps on
   grade.
7. **Reinforcement.**
   - Only 8Ø16/m is project-specific: nine plan callouts, read again and equal to S8.7's bindings.
   - S8.7's {s['frozen_release_unchanged']['kg']} kg over the three plates and S7's 75 stair-side top extensions
     (71.895327413 kg) are preserved and not counted again.
   - Blocked: {blocked}.
   - The 8Ø16/m main-bar sensitivity along the straight flights ({_full(s['main_bar_sensitivity_kg_8d16'], 3)} kg)
     is never released.
   - The p.16 cranked stair beam is not assumed to exist anywhere. The 'With Stair' beams stay with S6.
8. **Engineer decisions needed** (`10`, Q-ST7B-01..14):
   - which of +3.50 / 28 risers governs on GF -> 1F;
   - B20 under the GF -> 1F top tread;
   - the GF -> 1F foot and its support;
   - the 0.714 mm tolerance;
   - the 1F -> 2F winders and landing level;
   - the waist and landing thickness;
   - marble bedding and floor build-ups;
   - the typical bars, anchorage and laps;
   - the 'With Stair' beams;
   - the round stair's levels, width, soffit and beam CA;
   - the winder soffit form;
   - the steps on grade.

## Files

- `01` owner scenario and assumption register
- `02` riser calculation table
- `03` riser-by-riser setting-out schedule (exact levels and 1 mm site levels)
- `04` landing and elevation reconciliation
- `05` structural / architectural conflict matrix
- `06` beam interference audit
- `07` first / last risers and finish build-ups
- `08` waist-thickness concrete sensitivity
- `09` reinforcement and ownership audit
- `10` engineer RFI register
- `11` conservation and no-double-count checks
- `12` plan riser line evidence
- `13` section A-A, plan level texts and the p.16 visual record
- `14` release summary
- `15` provenance
- `16` freeze manifest
"""


def main():
    L = run()
    s = write(L)
    print(json.dumps({"release_delta": s["release_delta"], "answers": s["answers"],
                      "conservation": s["conservation"]}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Stop as e:
        print(f"STOP: {e}", file=sys.stderr)
        sys.exit(2)
