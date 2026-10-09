"""S8.2 - Alsenan swimming pool: source-controlled concrete and reinforcement QTO (blind; frozen before comparison).

    python3 -I research/alsenan_swimming_pool_s8_2/build_s8_2.py

Sources: ST7757.dxf (GBP plan outline, DET p.7 'DETAIL OF SWIMMING POOL (N.I.S)'), ST7757.pdf p.7 (notes, legend),
the registered architectural GF plan (P7757), S1's 26 pool bar labels, the PRE-S8 census and the S8.1A pool build-up
finding. No earlier pool quantity, contractor estimate or donor figure is read.

What the source establishes and what it does not:
  * plan: the pool's structural and water outlines are drawn true size on GBP (S-BW, the legend's bearing wall) and
    agree with the stated architectural dimensions (350 x 350, wall 20). They are measured exactly (lines and arcs).
  * section: the p.7 section is NOT TO SCALE; its depths, wall heights and deep / slope / shallow lengths all read
    'AS PER ARCH', and the architectural set prints none of them. Only the stated '20' (both walls) and '40' (deep
    base) are dimensions. Drawn lengths stay in drawing units and never become millimetres.
So the pool population, its plan geometry, every bar label's binding, the bar topology and the wall/base interfaces
are recorded in full, and every volume and every bar mass is blocked until a depth, height or extent is stated.
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
for p in (ROOT, ROOT / "research" / "external_engine_lab", ROOT / "research" / "source_recovery_delta"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import delta_release as DR  # noqa: E402
from engine.source import ground_slab_qto as GS  # noqa: E402
from engine.source import pool_qto as PQ  # noqa: E402
from engine.source import slab_rebar_qto as SR  # noqa: E402

ROUND = "S8_2"
DATE = "2026-10-09"
BASELINE_HEAD = "763a00e"
POLICY = "S8_2_POOL_SOURCE_CONTROLLED_QTO_V1"
R = ROOT / "research"
S1 = R / "alsenan_structural_census_s1"
S81 = R / "alsenan_ground_slab_s8_1"
S81A = R / "alsenan_ground_slab_s8_1a"
PRE8 = R / "pre_s8_structural_completeness"
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
PDF = ROOT / "data/inputs/by_sha256/74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3.pdf"
PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
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
             "PRE-S8": PRE8 / "13_PRE_S8_FREEZE_MANIFEST.json",
             "S8.1": S81 / "11_S8_1_FREEZE_MANIFEST.json",
             "S8.1A": S81A / "14_S8_1A_FREEZE_MANIFEST.json"}
S1_REGS = ["POOL_STRUCTURAL_REGISTER", "STRUCTURAL_PROJECT_RULE_REGISTER", "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER"]
P = {"census": PRE8 / "02_STRUCTURAL_ELEMENT_CENSUS.csv",
     "interfaces": PRE8 / "07_INTERFACE_DOUBLE_COUNT_AUDIT.csv",
     "exhaustion": PRE8 / "10_S8_SOURCE_EXHAUSTION.csv",
     "s81_register": S81 / "01_GROUND_SLAB_POPULATION_AND_ZONE_REGISTER.csv",
     "s81a_cover": S81A / "05_COVER_APPLICABILITY_AUDIT.csv",
     "ps51_summary": R / "pre_s5_1_source_resolution/PRE_S5_1_SUMMARY.json",
     "ps51_index": R / "pre_s5_1_source_resolution/INDEX.json"}
FROZEN_OUTPUT_OF = {"census": ("PRE-S8", "02_STRUCTURAL_ELEMENT_CENSUS.csv"),
                    "interfaces": ("PRE-S8", "07_INTERFACE_DOUBLE_COUNT_AUDIT.csv"),
                    "exhaustion": ("PRE-S8", "10_S8_SOURCE_EXHAUSTION.csv"),
                    "s81_register": ("S8.1", "01_GROUND_SLAB_POPULATION_AND_ZONE_REGISTER.csv"),
                    "s81a_cover": ("S8.1A", "05_COVER_APPLICABILITY_AUDIT.csv")}
# census fields read: identity and ownership only (the census also quotes earlier estimates; those are never read)
CENSUS_COLUMNS = ("ELEMENT_ID", "ROW_KIND", "PARENT_ELEMENT", "ELEMENT_FAMILY", "FLOOR", "SOURCE_PAGE", "DXF_HANDLES",
                  "NEW_S8_OWNER", "S8_SCOPE")
CODE = ["engine/source/pool_qto.py", "engine/source/ground_slab_qto.py", "engine/source/slab_rebar_qto.py",
        "engine/source/rebar_unit_mass.py", "engine/source/delta_release.py",
        "research/alsenan_swimming_pool_s8_2/build_s8_2.py", "research/external_engine_lab/alsenan_structural_s1.py",
        "research/source_recovery_delta/vector_pdf.py", "engine/source/legacy_text.py"]
OUTPUTS = ["00_README.md", "01_POOL_SOURCE_AND_RULE_REGISTER.csv", "02_POOL_POPULATION_AND_OWNERSHIP.csv",
           "03_CONCRETE_GEOMETRY_AND_QTO.csv", "04_BASE_REINFORCEMENT_QTO.csv", "05_WALL_REINFORCEMENT_QTO.csv",
           "06_BAR_RUN_AND_BENT_BAR_REGISTER.csv", "07_BLOCKED_REINFORCEMENT_REGISTER.csv",
           "08_WALL_BASE_INTERFACE_AUDIT.csv", "09_PLAIN_CONCRETE_AND_BUILD_UP_REGISTER.csv",
           "10_FLOOR_POOL_SUMMARY.csv", "11_PROVENANCE.jsonl", "12_CONSERVATION_CHECKS.csv",
           "13_REBAR_EVIDENCE_BINDING.csv", "14_COVER_APPLICABILITY.csv", "15_SENSITIVITY_SCENARIOS.csv",
           "16_CONFLICT_AND_QUESTION_REGISTER.csv", "17_S8_2_SUMMARY.json"]
MANIFEST_NAME = "18_S8_2_FREEZE_MANIFEST.json"

PARENT = "SPC-POOL"
FLOOR = "GROUND"
BLINDING_RECORD = "PS8-BLINDING-UNDER-FOOTINGS"
DET, GBP = "DET", "GBP"
POOL_TITLE, NIS_TEXT = "1864", "186A"
POOL_BOX = (-600.0, 11800.0, 19000.0, 27500.0)            # DET local: the section, its sub-details, labels, dims
DOME_SHELL_ARCS = ("182B", "182E")                         # DETAIL OF DOME shell profile (excluded)
DOME_DIMS = ("19B1", "182F")                               # dome shell thickness '10' and dome 'AS PER ARCH'
# section outline (S-EXTL.D) by role
SEC = {"DEEP_WALL_OUTER": "187A", "DEEP_WALL_INNER": "18A3", "DEEP_BASE_TOP": "18B2", "DEEP_BASE_BOTTOM": "1871",
       "SLOPE_TOP": "189D", "SLOPE_BOTTOM": "18A5", "SHALLOW_TOP": "190B", "SHALLOW_BOTTOM": "184B",
       "SHALLOW_WALL_INNER": "1911", "SHALLOW_WALL_OUTER": "1927", "DEEP_WALL_TOP": "186D",
       "SHALLOW_WALL_TOP": "1843"}
BUILDUP_LINES = {"SCREED_OUTER": "1854", "MEMBRANE_OUTER": "184D", "PLAIN_BOTTOM_DEEP": "186F",
                 "PLAIN_BOTTOM_SHALLOW": "1859", "PLAIN_END_DEEP": "187F", "PLAIN_END_SHALLOW": "192A"}
HATCH_FAMILY = {"S-SECRH.D": "SCREED", "S-INSU.D": "INSULATION_MEMBRANE", "S-PLAH.D": "PLAIN_CONCRETE"}
BUILDUP_TEXT = {"1874": "SCREED", "1876": "INSULATION_MEMBRANE", "1877": "PLAIN_CONCRETE"}
BOQ_FAMILY = {"SCREED": "SCREED", "INSULATION_MEMBRANE": "WATERPROOFING_OR_INSULATION",
              "PLAIN_CONCRETE": "PLAIN_CONCRETE"}
# plan (GBP local)
PLAN_OUTER, PLAN_INNER = "7C6", "7C5"                     # S-BW: structural outline, water outline
BOUNDARY_WALLS = ("7FC", "7FE")                            # S-BOUN: the site boundary wall stops at the pool corners
CURVED_GB = ("157", "158")                                 # layer 1: the curved ground beam round the pool
SWIM_BLOCK = "147"
HOOK_MAX_UNITS = 150.0                                     # end legs this short (drawing units) are drawn hooks
LEADER_TOL = 20.0                                          # leader tip to bar / dot (drawing units)
NEAREST_MAX = 350.0                                        # sub-detail label to its bar shape (drawing units)
DOT_MAX = 60.0                                             # a closed S-REIN.D polyline this small is a bar dot
DOT_DEDUPE = 10.0
LAP_TOL = 40.0                                             # side-by-side bars closer than any layer gap (86 units)
REGIONS = ("DEEP_WALL", "DEEP_BASE", "SLOPE", "SHALLOW_BASE", "SHALLOW_WALL")
COMPONENT_OF_REGION = {"DEEP_WALL": "PL-WALL-SECTION-DEEP", "DEEP_BASE": "PL-BASE-DEEP", "SLOPE": "PL-BASE-SLOPE",
                       "SHALLOW_BASE": "PL-BASE-SHALLOW", "SHALLOW_WALL": "PL-WALL-SECTION-SHALLOW"}
OWNER_PRIORITY = ("DEEP_WALL", "SHALLOW_WALL", "DEEP_BASE", "SHALLOW_BASE", "SLOPE")
JUNCTIONS = {"J-DEEP-WALL-BASE": ("DEEP_WALL", "DEEP_BASE"), "J-SHALLOW-WALL-BASE": ("SHALLOW_WALL", "SHALLOW_BASE"),
             "J-DEEP-SLOPE": ("DEEP_BASE", "SLOPE"), "J-SLOPE-SHALLOW": ("SLOPE", "SHALLOW_BASE")}
VIEW_CONFLICTS = ("SECOND_VIEW_DIAMETER_CONFLICT", "SECOND_VIEW_TOPOLOGY_DIFFERS")
SUBDETAIL_JUNCTION = (("J-DEEP-WALL-BASE", 1500.0, 4600.0), ("J-DEEP-SLOPE", 4600.0, 9300.0),
                      ("J-SLOPE-SHALLOW", 9300.0, 14500.0), ("J-SHALLOW-WALL-BASE", 14500.0, 17600.0))


class Stop(Exception):
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


def _full(v, nd=12):
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


def _csv(name, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in fields})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def _json(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _r(v, nd=3):
    return round(float(v), nd)


def _pt(p):
    return [_r(p[0]), _r(p[1])]


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode())
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()[:16]


def _mid_point(e):
    if e["type"] == "LINE":
        return ((e["a"][0] + e["b"][0]) / 2, (e["a"][1] + e["b"][1]) / 2)
    if e["type"] == "ARC":
        t = 0.5 * (e["a0"] + (e["a1"] if e["a1"] > e["a0"] else e["a1"] + 2 * math.pi))
        return (e["c"][0] + e["r"] * math.cos(t), e["c"][1] + e["r"] * math.sin(t))
    if e["type"] == "LWPOLYLINE":
        a, b = e["pts"][0], e["pts"][1] if len(e["pts"]) > 1 else e["pts"][0]
        return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    return _key_point(e)


def _inbox(p, b):
    return b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]


def _key_point(e):
    if "a" in e:
        return e["a"]
    if "pts" in e and e["pts"]:
        return e["pts"][0]
    if "c" in e:
        return e["c"]
    if "p" in e:
        return e["p"]
    if "bbox" in e:
        return (e["bbox"][0], e["bbox"][1])
    return None


# ------------------------------------------------------------------ inputs
def verify_inputs():
    absent = [f"{f.name}" for f in (DXF, ARCH, PDF) if not f.exists()]
    check(not absent, f"issued drawings not in data/inputs/by_sha256 (client data, never committed): {absent}")
    frozen = {k: DR.verify_frozen(m, ROOT) for k, m in MANIFESTS.items()}
    idx = _j(S1 / "INDEX.json")["registers"]
    for reg in S1_REGS:
        check(idx[reg]["sha256"] == _sha(S1 / f"{reg}.json"), f"S1 {reg} unchanged")
    out = {k: _j(m)["outputs"] for k, m in MANIFESTS.items()}
    for key, (stage, name) in FROZEN_OUTPUT_OF.items():
        check(out[stage].get(name) == _sha(P[key]), f"{stage} {name} is the frozen output")
    check(_j(P["ps51_index"])["outputs"]["PRE_S5_1_SUMMARY.json"] == _sha(P["ps51_summary"]),
          "PS5.1 registration record unchanged")
    for f, sha in ((DXF, DXF_SHA), (ARCH, ARCH_SHA), (PDF, PDF_SHA)):
        check(_sha(f) == sha, f"issued drawing {f.name} unchanged")
    return frozen


def census_rows():
    rows = [{k: r[k] for k in CENSUS_COLUMNS} for r in _rows(P["census"])]
    pool = [r for r in rows if r["ELEMENT_ID"] == PARENT]
    check(len(pool) == 1 and pool[0]["NEW_S8_OWNER"] == "S8 POOL", "PRE-S8 holds one pool element owned by S8 POOL")
    blind = [r for r in rows if r["ELEMENT_ID"] == BLINDING_RECORD]
    check(len(blind) == 1 and "1877" in blind[0]["DXF_HANDLES"], "PRE-S8 blinding record cites the pool's 1877")
    return {"pool": pool[0], "blinding": blind[0]}


# ------------------------------------------------------------------ DET (p.7) evidence
def det_evidence(src):
    """Every entity of the pool detail on DET, the dome detail kept out."""
    E = src.entities()[DET]
    dome_arcs = [e for e in E if e["handle"] in DOME_SHELL_ARCS]
    check(len(dome_arcs) == 2, "the dome shell profile is found")
    c = dome_arcs[0]["c"]
    r_lo, r_hi = min(a["r"] for a in dome_arcs) - 300.0, max(a["r"] for a in dome_arcs) + 300.0

    def on_dome(e):                                        # any characteristic point inside the dome shell band
        pts = [_key_point(e)]
        if "bbox" in e:
            b = e["bbox"]
            pts += [(b[0], b[1]), (b[2], b[3]), (b[0], b[3]), (b[2], b[1])]
        return any(r_lo <= math.dist(p, c) <= r_hi for p in pts if p is not None)
    boxed = [e for e in E if _key_point(e) is not None and _inbox(_key_point(e), POOL_BOX)]
    dome_in_box = sorted(e["handle"] for e in boxed if on_dome(e))
    pool = [e for e in boxed if not on_dome(e)]
    by_h = {e["handle"]: e for e in E}
    s1pool = _j(S1 / "POOL_STRUCTURAL_REGISTER.json")
    s1_handles = [r["source_id"].split(":")[-1] for r in s1pool["rows"]]
    check(len(s1_handles) == 26 and all(h in {e["handle"] for e in pool} for h in s1_handles),
          "all 26 S1 pool labels lie in the pool detail")
    check(not set(s1_handles) & set(dome_in_box), "no pool label lies on the dome shell band")
    title = by_h[POOL_TITLE]
    check("SWIMMING POOL" in title["text"].upper() and by_h[NIS_TEXT]["text"] == "(N.I.S)", "pool title and N.I.S")
    sec = {}
    for role, h in SEC.items():
        e = by_h[h]
        check(e["layer"] == "S-EXTL.D" and e["type"] == "LINE", f"outline {role} is an S-EXTL.D line")
        sec[role] = (tuple(e["a"]), tuple(e["b"]))
    return {"all": E, "pool": pool, "by_h": by_h, "sec": sec, "s1": s1pool, "s1_handles": s1_handles,
            "dome_in_box": dome_in_box}


def section_regions(sec):
    """The section's five concrete regions (drawing units, NTS) from the outline lines. The base regions include the
    wall footprint below the base top: the base owns it."""
    xs = lambda role: sec[role][0][0]  # noqa: E731
    ys = lambda role: sec[role][0][1]  # noqa: E731
    y_top_d, y_bot_d = ys("DEEP_BASE_TOP"), ys("DEEP_BASE_BOTTOM")
    y_top_s, y_bot_s = ys("SHALLOW_TOP"), ys("SHALLOW_BOTTOM")
    y_wall = ys("DEEP_WALL_TOP")
    check(abs(ys("SHALLOW_WALL_TOP") - y_wall) < 1e-6, "both walls reach the same top line")
    x_wo, x_wi = xs("DEEP_WALL_OUTER"), xs("DEEP_WALL_INNER")
    x_si, x_so = xs("SHALLOW_WALL_INNER"), xs("SHALLOW_WALL_OUTER")
    st0, st1 = sorted(sec["SLOPE_TOP"])
    sb0, sb1 = sorted(sec["SLOPE_BOTTOM"])
    reg = {"DEEP_WALL": [[(x_wo, y_top_d), (x_wi, y_top_d), (x_wi, y_wall), (x_wo, y_wall)]],
           "DEEP_BASE": [[(x_wo, y_bot_d), sb0, st0, (x_wo, y_top_d)]],
           "SLOPE": [[sb0, sb1, st1, st0]],
           "SHALLOW_BASE": [[sb1, (x_so, y_bot_s), (x_so, y_top_s), st1]],
           "SHALLOW_WALL": [[(x_si, y_top_s), (x_so, y_top_s), (x_so, y_wall), (x_si, y_wall)]]}
    check(abs(sb0[1] - y_bot_d) < 1e-6 and abs(st0[1] - y_top_d) < 1e-6 and abs(sb1[1] - y_bot_s) < 1e-6
          and abs(st1[1] - y_top_s) < 1e-6, "the slope lines join the deep and shallow base lines")
    faces = {"DEEP_WALL": {"OUTER": ("V", x_wo), "INNER": ("V", x_wi), "TOP": ("H", y_wall)},
             "SHALLOW_WALL": {"OUTER": ("V", x_so), "INNER": ("V", x_si), "TOP": ("H", y_wall)},
             "DEEP_BASE": {"TOP": ("H", y_top_d), "BOTTOM": ("H", y_bot_d)},
             "SHALLOW_BASE": {"TOP": ("H", y_top_s), "BOTTOM": ("H", y_bot_s)},
             "SLOPE": {"TOP": ("L", st0, st1), "BOTTOM": ("L", sb0, sb1)}}
    drawn = {"deep_wall_width": x_wi - x_wo, "shallow_wall_width": x_so - x_si,
             "deep_base_depth": y_top_d - y_bot_d, "shallow_base_depth": y_top_s - y_bot_s,
             "wall_top": y_wall, "deep_base_top": y_top_d, "shallow_top": y_top_s, "deep_base_bottom": y_bot_d,
             "x_wall_outer_deep": x_wo, "x_wall_inner_deep": x_wi, "x_wall_inner_shallow": x_si,
             "x_wall_outer_shallow": x_so, "slope_top": [st0, st1], "slope_bottom": [sb0, sb1]}
    return {"regions": reg, "faces": faces, "drawn": drawn}


def region_of(p, regions):
    hits = [rid for rid in REGIONS if any(PQ._clip_convex(p, p, poly) for poly in regions[rid])]
    return hits[0] if len(hits) == 1 else (hits if hits else None)


def face_distance(p, face):
    if face[0] == "V":
        return abs(p[0] - face[1])
    if face[0] == "H":
        return abs(p[1] - face[1])
    return PQ._pt_seg(p, face[1], face[2])


def nearest_face(p, region, faces, *, exclude=()):
    fs = {k: v for k, v in faces[region].items() if k not in exclude}
    return min(fs, key=lambda k: (face_distance(p, fs[k]), k))


def det_dimensions(src, sec_drawn):
    """Every DIMENSION in the pool detail: displayed text (from its geometry block), drawn measurement, what it spans."""
    doc = src.doc
    fx, fy = src.sheets[DET]["frame"][:2]
    levels = {"WALL_TOP": sec_drawn["wall_top"], "DEEP_BASE_TOP": sec_drawn["deep_base_top"],
              "SHALLOW_FLOOR_TOP": sec_drawn["shallow_top"], "DEEP_BASE_BOTTOM": sec_drawn["deep_base_bottom"]}
    xs = {"DEEP_WALL_OUTER": sec_drawn["x_wall_outer_deep"], "DEEP_WALL_INNER": sec_drawn["x_wall_inner_deep"],
          "SLOPE_TOP_START": sec_drawn["slope_top"][0][0], "SLOPE_TOP_END": sec_drawn["slope_top"][1][0],
          "SHALLOW_WALL_INNER": sec_drawn["x_wall_inner_shallow"],
          "SHALLOW_WALL_OUTER": sec_drawn["x_wall_outer_shallow"]}
    out = []
    for d in doc.modelspace().query("DIMENSION"):
        p2 = (d.dxf.defpoint2.x - fx, d.dxf.defpoint2.y - fy)
        p3 = (d.dxf.defpoint3.x - fx, d.dxf.defpoint3.y - fy)
        mid = ((p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2)
        if not _inbox(mid, POOL_BOX) or d.dxf.handle in DOME_DIMS:
            continue
        blk = doc.blocks.get(d.dxf.geometry)
        shown = [x.plain_text() if x.dxftype() == "MTEXT" else x.dxf.text for x in blk
                 if x.dxftype() in ("MTEXT", "TEXT")]
        txt = re.sub(r"\s+", " ", " ".join(shown)).strip()
        vertical = abs(p2[0] - p3[0]) < 1.0
        if vertical:
            span = [k for y in (p2[1], p3[1]) for k, v in levels.items() if abs(v - y) < 1.0]
        else:
            span = [k for x in (p2[0], p3[0]) for k, v in xs.items() if abs(v - x) < 1.0]
        num = re.fullmatch(r"\d+(?:\.\d+)?", txt)
        out.append({"handle": d.dxf.handle, "text": txt, "measurement_units": _r(d.get_measurement()),
                    "orientation": "VERTICAL" if vertical else "HORIZONTAL", "spans": span,
                    "p2": _pt(p2), "p3": _pt(p3),
                    "authority": PQ.STATED if num else ("REFERENCE_AS_PER_ARCH" if "ARCH" in txt.upper() else
                                                        "UNREAD"),
                    "value_cm": float(txt) if num else None})
    out.sort(key=lambda d: d["handle"])
    return out


def pdf_page7():
    """Page 7 vector layers: the printed notes / legend glyph layer, the plot stamp and the page's layer census."""
    import vector_pdf as VP
    paths = VP.paths(PDF, 7)
    lay = Counter(p[0] for p in paths)
    return {"layers": dict(sorted(lay.items())), "paths": len(paths)}


# ------------------------------------------------------------------ plan geometry (GBP, true size)
def ring_from_segs(segs):
    """An exact ground_slab_qto ring from a polyline's S1 segments (lines and bulge arcs in polyline order)."""
    edges, prev = [], None
    for k, sg in enumerate(segs):
        if sg[0] != "ARC":
            a, b = sg
            edges.append(GS.line(a, b))
            prev = b
            continue
        _, c, r, a0, a1 = sg
        while a1 <= a0:
            a1 += 2 * math.pi
        p0 = (c[0] + r * math.cos(a0), c[1] + r * math.sin(a0))
        p1 = (c[0] + r * math.cos(a1), c[1] + r * math.sin(a1))
        nxt = segs[(k + 1) % len(segs)]
        start = prev if prev is not None else (nxt[0] if nxt[0] != "ARC" else None)
        if start is not None and math.dist(start, p1) < math.dist(start, p0):
            edges.append(GS.arc(c, r, a1, a0))
            prev = p0
        else:
            edges.append(GS.arc(c, r, a0, a1))
            prev = p1
    GS.check_ring(edges, tol=1e-3)
    return edges


def plan_geometry(src):
    E = {e["handle"]: e for e in src.entities()[GBP]}
    outer, inner = E[PLAN_OUTER], E[PLAN_INNER]
    check(outer["layer"] == inner["layer"] == "S-BW", "pool outlines are S-BW bearing-wall outlines")
    r_out, r_in = [ring_from_segs(e["segs"]) for e in (outer, inner)]
    A_out, A_in = PQ.region_area_m2([r_out]), PQ.region_area_m2([r_in])
    band = PQ.band_area_m2([r_out], [r_in])
    arcs_o = [e for e in r_out if e[0] == GS.ARC]
    arcs_i = [e for e in r_in if e[0] == GS.ARC]
    check(len(arcs_o) == len(arcs_i) == 1 and math.dist(arcs_o[0][1], arcs_i[0][1]) < 1e-6,
          "one concentric west arc on each outline")
    c = arcs_o[0][1]
    Ro, Ri = arcs_o[0][2], arcs_i[0][2]
    xo = [v for e in r_out if e[0] == GS.LINE for v in (e[1][0], e[2][0])]
    yo = [v for e in r_out if e[0] == GS.LINE for v in (e[1][1], e[2][1])]
    xi = [v for e in r_in if e[0] == GS.LINE for v in (e[1][0], e[2][0])]
    yi = [v for e in r_in if e[0] == GS.LINE for v in (e[1][1], e[2][1])]
    east_o, east_i = max(xo), max(xi)
    t_e, t_n, t_s = east_o - east_i, max(yo) - max(yi), min(yi) - min(yo)
    t_w = Ro - Ri
    check(all(abs(t - t_e) < 1e-6 for t in (t_n, t_s, t_w)), "one uniform wall band all round")
    check(abs(min(xo) - c[0]) < 1e-6 and abs(min(xi) - c[0]) < 1e-6, "the straight sides start at the arc centre")
    # wall runs: east wall full height (owns both corners), north / south between the arc tangent and the east wall,
    # the west half-annulus
    pi = math.pi
    runs = {"PL-WALL-RUN-E": [[GS.line((east_i, min(yo)), (east_o, min(yo))), GS.line((east_o, min(yo)), (east_o, max(yo))),
                               GS.line((east_o, max(yo)), (east_i, max(yo))), GS.line((east_i, max(yo)), (east_i, min(yo)))]],
            "PL-WALL-RUN-N": [[GS.line((c[0], max(yi)), (east_i, max(yi))), GS.line((east_i, max(yi)), (east_i, max(yo))),
                               GS.line((east_i, max(yo)), (c[0], max(yo))), GS.line((c[0], max(yo)), (c[0], max(yi)))]],
            "PL-WALL-RUN-S": [[GS.line((c[0], min(yo)), (east_i, min(yo))), GS.line((east_i, min(yo)), (east_i, min(yi))),
                               GS.line((east_i, min(yi)), (c[0], min(yi))), GS.line((c[0], min(yi)), (c[0], min(yo)))]],
            "PL-WALL-RUN-W": [[GS.arc(c, Ro, pi / 2, 3 * pi / 2), GS.line((c[0], c[1] - Ro), (c[0], c[1] - Ri)),
                               GS.arc(c, Ri, 3 * pi / 2, pi / 2), GS.line((c[0], c[1] + Ri), (c[0], c[1] + Ro))]]}
    run_area = {k: PQ.region_area_m2(v) for k, v in runs.items()}
    tile = PQ.tiling(list(run_area.values()), band, tol_m2=1e-9)
    check(tile["exact"], f"the four wall runs tile the band: {tile}")
    faces = {"PL-WALL-RUN-E": {"inner_m": (max(yi) - min(yi)) / 1000, "outer_m": (max(yo) - min(yo)) / 1000 + 2 * t_e / 1000},
             "PL-WALL-RUN-N": {"inner_m": (east_i - c[0]) / 1000, "outer_m": (east_i - c[0]) / 1000},
             "PL-WALL-RUN-S": {"inner_m": (east_i - c[0]) / 1000, "outer_m": (east_i - c[0]) / 1000},
             "PL-WALL-RUN-W": {"inner_m": pi * Ri / 1000, "outer_m": pi * Ro / 1000}}
    L_in, L_out = PQ.ring_length_m(r_in), PQ.ring_length_m(r_out)
    check(abs(math.fsum(f["inner_m"] for f in faces.values()) - L_in) < 1e-9
          and abs(math.fsum(f["outer_m"] for f in faces.values()) - L_out) < 1e-9, "run faces sum to the perimeters")
    # neighbours: the boundary wall touches the pool only at its corners; the curved ground beam stays clear
    from shapely.geometry import Point, Polygon, box
    pool_poly = box(c[0], min(yo), east_o, max(yo)).union(Point(c).buffer(Ro, 1024))
    touch = []
    for h in BOUNDARY_WALLS:
        w = E[h]
        poly = Polygon([sg[0] for sg in w["segs"]])
        on_line = sorted({_r(q[1]) for sg in w["segs"] for q in sg[:2]
                          if east_i - 1e-6 <= q[0] <= east_o + 1e-6 and min(yo) - 1e-6 <= q[1] <= max(yo) + 1e-6})
        touch.append({"handle": h, "layer": w["layer"], "overlap_m2": poly.intersection(pool_poly).area / 1e6,
                      "shared_points_y": on_line})
    check(all(t["overlap_m2"] < 1e-6 for t in touch), "the boundary wall does not overlap the pool walls")
    gb = [E[h] for h in CURVED_GB]
    gb_inner_r = min(g["r"] for g in gb)
    clear_mm = gb_inner_r - Ro - max(math.dist(g["c"], c) for g in gb)
    check(clear_mm > 0, "the curved ground beam stays clear of the pool")
    return {"rings": {"outer": r_out, "inner": r_in}, "A_out": A_out, "A_in": A_in, "band": band, "centre": c,
            "R_out": Ro, "R_in": Ri, "wall_t_mm": t_e, "east_outer_x": east_o, "east_inner_x": east_i,
            "y_out": (min(yo), max(yo)), "y_in": (min(yi), max(yi)), "runs": runs, "run_area": run_area,
            "run_faces": faces, "L_in": L_in, "L_out": L_out, "boundary_touch": touch,
            "curved_gb": [{"handle": g["handle"], "r": _r(g["r"]), "centre": _pt(g["c"])} for g in gb],
            "curved_gb_clear_mm": clear_mm, "tiling": tile,
            "swim_block": {k: E[SWIM_BLOCK][k] for k in ("handle", "name", "bbox", "scale", "rotation")}}


# ------------------------------------------------------------------ architectural corroboration (P7757, registered)
def arch_corroboration(pg, src):
    """Stated architectural dimensions round the pool (GBP local through the PS5.1 registration) and the
    architectural pool outline. Any level, depth or section of the pool would be read here: none is printed."""
    import ezdxf
    from ezdxf import disassemble
    from engine.source import legacy_text as LT
    reg = _j(P["ps51_summary"])["registration"]
    check(reg["state"] == "REGISTERED", "PS5.1 architectural registration holds")
    tx, ty = reg["translation_arch_to_gbp"]
    gbp_frame = src.sheets[GBP]["frame"][:2]
    to_gbp = lambda x, y: (x + tx - gbp_frame[0], y + ty - gbp_frame[1])  # noqa: E731
    win = (pg["centre"][0] - 2500.0, pg["y_out"][0] - 1500.0, pg["east_outer_x"] + 1500.0, pg["y_out"][1] + 1500.0)
    doc = ezdxf.readfile(ARCH)
    styles = {s.dxf.name: LT.font_family(s.dxf.font) for s in doc.styles}
    texts, ticks, lines5, arcs5, depth_words = [], [], [], [], []
    rx = re.compile(r"(pool|swim|depth|deep|shallow|section|سباح|عمق|قطاع|مقطع|حوض|^[-+]\s?\d+\.\d{2}$)", re.I)
    for e in disassemble.recursive_decompose(doc.modelspace()):
        t = e.dxftype()
        if t in ("TEXT", "MTEXT"):
            raw = e.dxf.text if t == "TEXT" else e.plain_text()
            fam = styles.get(e.dxf.get("style", "Standard"))
            dec = ((LT.decode(raw, fam)["text"] if fam else raw) or raw).strip()
            p = to_gbp(e.dxf.insert.x, e.dxf.insert.y)
            if rx.search(raw.strip()) or rx.search(dec):
                depth_words.append({"layer": e.dxf.layer, "text": dec, "p": _pt(p)})
            if _inbox(p, win):
                texts.append({"layer": e.dxf.layer, "text": dec, "p": _pt(p), "rotation": _r(e.dxf.get("rotation", 0))})
        elif t == "LINE":
            a = to_gbp(e.dxf.start.x, e.dxf.start.y)
            b = to_gbp(e.dxf.end.x, e.dxf.end.y)
            if not (_inbox(a, win) and _inbox(b, win)):
                continue
            if e.dxf.layer == "0" and abs(math.dist(a, b) - 226.3) < 1.0:            # 45-degree dimension ticks
                ticks.append(_pt(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)))
            if e.dxf.layer == "5":
                lines5.append([_pt(a), _pt(b)])
        elif t == "ARC" and e.dxf.layer == "5":
            c = to_gbp(e.dxf.center.x, e.dxf.center.y)
            if _inbox(c, win):
                arcs5.append({"c": _pt(c), "r": _r(e.dxf.radius), "a0": _r(e.dxf.start_angle), "a1": _r(e.dxf.end_angle)})
    num = [t for t in texts if t["layer"] == "4" and re.fullmatch(r"\d+", t["text"])]
    y0, y1 = pg["y_out"]
    ns = [t for t in num if t["text"] == "350" and abs(t["p"][1] - (y0 + y1) / 2) < 400]
    tick_y = sorted({tk[1] for tk in ticks if abs(tk[0] - ns[0]["p"][0]) < 200}) if ns else []
    ns_ok = bool(ns) and any(abs(v - y0) < 1.0 for v in tick_y) and any(abs(v - y1) < 1.0 for v in tick_y)
    arch_radii = sorted({a["r"] for a in arcs5 if math.dist(a["c"], _pt(pg["centre"])) < 1.0})
    pool_words = [w for w in depth_words if re.search(r"pool|swim|سباح", w["text"], re.I)]
    other_words = [w for w in depth_words if w not in pool_words]
    return {"numeric_texts": num, "ns_350": ns, "ns_ticks_y": tick_y, "ns_350_matches_outline": ns_ok,
            "arch_pool_radii": arch_radii, "arch_lines_layer5": len(lines5), "pool_labels": pool_words,
            "depth_or_section_texts": other_words}


# ------------------------------------------------------------------ bars, dots, labels
def det_bars(det, regions):
    """Drawn bar segments (S-REIN.D lines / arcs / polylines) of the main section and of the corner sub-details."""
    main, corner, dots, other = [], [], [], []
    for e in det["pool"]:
        if e["layer"] not in ("S-REIN.D", "REIN"):
            continue
        box = "MAIN" if region_of(_mid_point(e), regions["regions"]) is not None else "CORNER"
        if e["type"] == "LWPOLYLINE":
            xs, ys = [q[0] for q in e["pts"]], [q[1] for q in e["pts"]]
            if max(xs) - min(xs) < DOT_MAX and max(ys) - min(ys) < DOT_MAX:
                dots.append({"handle": e["handle"], "c": ((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2),
                             "r": (max(xs) - min(xs)) / 2, "box": box})
                continue
            segs = [("LINE", f"{e['handle']}#{k}", tuple(a), tuple(b)) for k, (a, b) in
                    enumerate(zip(e["pts"], e["pts"][1:] + (e["pts"][:1] if e["closed"] else [])))]
        elif e["type"] == "LINE":
            segs = [("LINE", e["handle"], tuple(e["a"]), tuple(e["b"]))]
        elif e["type"] == "ARC":
            segs = [("ARC", e["handle"], tuple(e["c"]), e["r"], e["a0"], e["a1"])]
        else:
            other.append(e["handle"])
            continue
        (main if box == "MAIN" else corner).extend(segs)
    check(not other, f"no other bar entity type in the pool detail: {other}")
    # collapse duplicate dots (identical or overlapping drawn circles)
    kept, dup = [], []
    for d in sorted(dots, key=lambda d: d["handle"]):
        twin = next((k for k in kept if math.dist(k["c"], d["c"]) <= DOT_DEDUPE), None)
        if twin:
            dup.append((d["handle"], twin["handle"]))
        else:
            kept.append(d)
    for d in kept:
        d["region"] = region_of(d["c"], regions["regions"])
    check(all(isinstance(d["region"], str) for d in kept), "every dot lies in exactly one section region")
    return {"main": main, "corner": corner, "dots": kept, "dot_duplicates": dup}


def dot_rows(dots, regions):
    """Dots grouped into drawn rows: wall faces (OUTER / INNER), the wall TOP, base and slope TOP / BOTTOM, and the
    dots under a wall at the base bottom (UNDER_WALL_BOTTOM) and base top (UNDER_WALL_TOP)."""
    dr = regions["drawn"]
    bands = {"DEEP_BASE": (dr["x_wall_outer_deep"], dr["x_wall_inner_deep"]),
             "SHALLOW_BASE": (dr["x_wall_inner_shallow"], dr["x_wall_outer_shallow"])}
    rows = defaultdict(list)
    for d in dots:
        reg, c = d["region"], d["c"]
        if reg in ("DEEP_WALL", "SHALLOW_WALL"):
            face = "TOP" if dr["wall_top"] - c[1] <= 200.0 else nearest_face(c, reg, regions["faces"],
                                                                                 exclude=("TOP",))
        else:
            face = nearest_face(c, reg, regions["faces"])
            b = bands.get(reg)
            if b and b[0] <= c[0] <= b[1]:
                face = "UNDER_WALL_" + face
        rows[(reg, face)].append(d)
    out = {}
    for (reg, face), ds in sorted(rows.items()):
        rid = f"DOTROW-{reg}-{face}"
        for d in ds:
            d["row"] = rid
        out[rid] = {"row_id": rid, "region": reg, "face": face, "dots": sorted(d["handle"] for d in ds),
                    "n_dots": len(ds)}
    return out


def det_labels(det):
    """Bar labels (diameter texts on S-TEXT.D) with their leader tips, and the label anchors of the sub-details."""
    pool = det["pool"]
    texts = [e for e in pool if e["type"] in ("TEXT", "MTEXT") and e["layer"] == "S-TEXT.D"
             and re.search(r"%%[cC]|Ø", e["text"])]
    segs = []
    for e in pool:
        if e["layer"] != "S-TEXT.D":
            continue
        if e["type"] == "LINE":
            segs.append((e["handle"], tuple(e["a"]), tuple(e["b"])))
        elif e["type"] == "LWPOLYLINE":
            segs.extend((e["handle"], tuple(a), tuple(b)) for a, b in zip(e["pts"], e["pts"][1:]))
    par = list(range(len(segs)))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]
            i = par[i]
        return i
    for i in range(len(segs)):
        for j in range(i + 1, len(segs)):
            a, b = segs[i], segs[j]
            if min(PQ._pt_seg(p, b[1], b[2]) for p in (a[1], a[2])) < 2.0 or \
                    min(PQ._pt_seg(p, a[1], a[2]) for p in (b[1], b[2])) < 2.0:
                par[find(i)] = find(j)
    comp = defaultdict(list)
    for i, s in enumerate(segs):
        comp[find(i)].append(s)
    out = []
    for t in sorted(texts, key=lambda t: t["handle"]):
        x, y = t["p"]
        rot = t.get("rotation", 0.0)
        under = None
        for k, ss in comp.items():
            for h, a, b in ss:
                if rot in (0.0, 360.0) and abs(a[1] - b[1]) < 2.0 and -10 < y - a[1] < 160 \
                        and min(a[0], b[0]) - 300 <= x <= max(a[0], b[0]) + 50:
                    under = k
                if rot == 90.0 and abs(a[0] - b[0]) < 2.0 and -10 < a[0] - x < 160 \
                        and min(a[1], b[1]) - 300 <= y <= max(a[1], b[1]) + 50:
                    under = k
        tips = [p for h, a, b in comp[under] for p in (a, b)] if under is not None else []
        box = "MAIN" if tips else "CORNER"
        out.append({"handle": t["handle"], "raw": t["text"], "p": tuple(t["p"]), "rotation": rot, "box": box,
                    "leader": sorted({h for h, a, b in comp[under]}) if under is not None else [], "tips": tips,
                    "notation": PQ.parse_notation(t["text"])})
    return out


def runs_of(segs, regions):
    out = PQ.chain_runs(segs, tol=0.5)
    runs = {}
    for i, r in enumerate(out["runs"], 1):
        sh = PQ.run_shape(r, hook_max_units=HOOK_MAX_UNITS)
        r["shape"] = sh["shape"]
        r["shape_detail"] = sh
        r["lengths_in"] = PQ.leg_lengths_in(r, regions)
        runs[i] = r
    return runs, out["duplicates"]


def bind_all(labels, runs, corner_runs, dots, rows):
    """Main-section labels bind through their leader tips; sub-detail labels (no leaders) bind the nearest drawn
    bar shape of their sub-detail. Every label ends BOUND, AMBIGUOUS or UNBOUND."""
    seg_run = {}
    targets = []
    for rid, r in runs.items():
        for s in r["_segs"]:
            seg_run[s[1]] = rid
            g = ("SEG", s[2], s[3]) if s[0] == "LINE" else ("ARC", s[2], s[3])
            targets.append((s[1], g))
    for d in dots:
        targets.append((d["handle"], ("DOT", d["c"], d["r"])))
    main = [l for l in labels if l["box"] == "MAIN"]
    sub = [l for l in labels if l["box"] == "CORNER"]
    b_main = PQ.bind_leaders([(l["handle"], l["tips"]) for l in main], targets, tol=LEADER_TOL)
    ctargets = []
    cseg_run = {}
    for rid, r in corner_runs.items():
        for s in r["_segs"]:
            cseg_run[s[1]] = rid
            ctargets.append((s[1], ("SEG", s[2], s[3]) if s[0] == "LINE" else ("ARC", s[2], s[3])))
    anchors = []
    for l in sub:
        x, y = l["p"]
        h = 200.0                                                   # text height
        anchors.append((l["handle"], (x, y) if l["rotation"] == 90.0 else (x + 3 * h, y)))
    # a sub-detail label binds to a whole bar shape: the pieces of one shape are not rivals
    b_sub = PQ.bind_nearest(anchors, [(f"CR{cseg_run[sid]}", g) for sid, g in ctargets], max_d=NEAREST_MAX)
    out = {}
    dot_row = {d["handle"]: d["row"] for d in dots}
    for l in labels:
        b = b_main.get(l["handle"]) or b_sub.get(l["handle"])
        dot_ids = sorted(t for t in b["targets"] if t in dot_row)
        seg_ids = sorted(t for t in b["targets"] if t in seg_run)
        # a tip on a dot binds the dot's bar family; a bar line passing the same tip is an incidental contact
        incidental = seg_ids if dot_ids else []
        bound_segs = [] if dot_ids else seg_ids
        out[l["handle"]] = {**b, "method": "LEADER" if l["box"] == "MAIN" else "PROXIMITY_SUB_DETAIL",
                            "runs": [f"R{r}" for r in sorted({seg_run[t] for t in bound_segs})],
                            "segments": bound_segs, "incidental_segments": incidental,
                            "dots": dot_ids, "dot_rows": sorted({dot_row[t] for t in dot_ids}),
                            "corner_shapes": [t for t in b["targets"] if t.startswith("CR")]}
    return out


# ------------------------------------------------------------------ bar runs, end marks, families
def split_marks(runs):
    """A run no longer than a hook that touches another run's middle is a drawn bar-end mark on that run."""
    marks, keep = [], {}
    for rid, r in runs.items():
        if r["drawn_length_units"] <= HOOK_MAX_UNITS and len(r["run_segments"]) == 1:
            host = None
            for oid, o in runs.items():
                if oid == rid or o["drawn_length_units"] <= HOOK_MAX_UNITS:
                    continue
                for s in o["_segs"]:
                    if s[0] == "LINE" and min(PQ._pt_seg(p, s[2], s[3]) for p in (r["start"], r["end"])) <= 1.0:
                        host = (oid, s[1])
            marks.append({"mark_id": f"M{len(marks) + 1}", "segments": r["run_segments"], "host": host,
                          "point": _pt(r["start"])})
        else:
            keep[rid] = r
    ren = {old: i for i, old in enumerate(sorted(keep), 1)}
    runs2 = {ren[k]: v for k, v in keep.items()}
    for m in marks:
        if m["host"]:
            m["host"] = (f"R{ren[m['host'][0]]}", m["host"][1])
    return runs2, marks


def run_groups(run, label_dia):
    """Diameter of every segment of one run from the labels on it: a segment between two labels of one diameter
    takes it; between two different diameters it is a CONFLICT_ZONE; beyond the last label it takes the nearest."""
    ids = run["run_segments"]
    lab = [(i, label_dia[s]) for i, s in enumerate(ids) if s in label_dia]
    out = {}
    for i, s in enumerate(ids):
        left = [d for j, d in lab if j <= i]
        right = [d for j, d in lab if j >= i]
        lv = left[-1] if left else None
        rv = right[0] if right else None
        if lv is None or rv is None:
            out[s] = lv if lv is not None else rv
        else:
            out[s] = lv if lv == rv else "CONFLICT_ZONE"
    return out


def families(labels, binding, runs, marks, rows, corner_runs, regions):
    """One bar family per physical bar set: a drawn run (or the part of it one diameter governs) or a dot row bound
    by a label. Labels on one family are one family (counted once); sub-detail labels are second views."""
    lab = {l["handle"]: l for l in labels}
    fams, label_state = [], {}
    seg_dia = {}
    for lid, b in binding.items():
        if b["segments"]:
            for s in b["segments"]:
                seg_dia[s] = lab[lid]["notation"]["dia_mm"]
    # ---- run families
    for rid in sorted(runs):
        r = runs[rid]
        rname = f"R{rid}"
        on = sorted(l for l, b in binding.items() if rname in b["runs"])
        if not on:
            continue
        groups = run_groups(r, {s: seg_dia[s] for s in r["run_segments"] if s in seg_dia})
        dias = sorted({v for v in groups.values() if v != "CONFLICT_ZONE"})
        diam = PQ.run_diameters(on, {l: lab[l]["notation"] for l in on})
        parts = [(f"BF-{rname}", dias[0], r["run_segments"])] if len(dias) == 1 else \
            [(f"BF-{rname}-D{int(d)}", d, [s for s in r["run_segments"] if groups[s] == d]) for d in dias]
        for fid, d, segs in parts:
            mine = sorted(l for l in on if set(binding[l]["segments"]) & set(segs))
            sub = {"_segs": [s for s in r["_segs"] if s[1] in segs]}
            lens = PQ.leg_lengths_in(sub, regions["regions"])
            owner_region = PQ.owner_of(lens, priority=OWNER_PRIORITY)
            nots = {lab[l]["raw"] for l in mine}
            fams.append({"FAMILY_ID": fid, "KIND": "DRAWN_RUN", "RUNS": [rname], "SEGMENTS": segs, "LABELS": mine,
                         "PRIMARY_LABEL": mine[0], "NOTATION": lab[mine[0]]["raw"],
                         "NOTATION_KIND": lab[mine[0]]["notation"]["kind"], "DIA_MM": d,
                         "PER_M": lab[mine[0]]["notation"]["per_m"], "COUNT": lab[mine[0]]["notation"]["count"],
                         "OWNER_REGION": owner_region, "COMPONENT_OWNER_ID": COMPONENT_OF_REGION[owner_region],
                         "LEG_UNITS": {k: v for k, v in lens.items() if v > 0},
                         "DIAMETER_STATE": diam["state"] if len(dias) == 1 else PQ.CONFLICT,
                         "NOTATIONS_ON_FAMILY": sorted(nots),
                         "END_MARKS": [m["mark_id"] for m in marks if m["host"] and m["host"][0] == rname]})
            for k, l in enumerate(mine):
                label_state[l] = (fid, "FAMILY_PRIMARY_LABEL" if k == 0 else "SAME_FAMILY_SECOND_LABEL (counted once)")
        zone = [s for s in r["run_segments"] if groups[s] == "CONFLICT_ZONE"]
        if zone:
            sub = {"_segs": [s for s in r["_segs"] if s[1] in zone]}
            lens = PQ.leg_lengths_in(sub, regions["regions"])
            owner_region = PQ.owner_of(lens, priority=OWNER_PRIORITY)
            fams.append({"FAMILY_ID": f"BF-{rname}-CONNECTOR", "KIND": "DRAWN_RUN_CONFLICT_ZONE", "RUNS": [rname],
                         "SEGMENTS": zone, "LABELS": [], "PRIMARY_LABEL": None, "NOTATION": None,
                         "NOTATION_KIND": None, "DIA_MM": None, "PER_M": None, "COUNT": None,
                         "OWNER_REGION": owner_region, "COMPONENT_OWNER_ID": COMPONENT_OF_REGION[owner_region],
                         "LEG_UNITS": {k: v for k, v in lens.items() if v > 0}, "DIAMETER_STATE": PQ.CONFLICT,
                         "NOTATIONS_ON_FAMILY": sorted({lab[l]["raw"] for l in on}), "END_MARKS": []})
    # ---- dot-row families
    row_claims = defaultdict(list)
    for lid, b in binding.items():
        for rw in b["dot_rows"]:
            row_claims[rw].append(lid)
    by_label_rows = defaultdict(list)
    for lid, b in binding.items():
        if b["dot_rows"]:
            by_label_rows[lid] = b["dot_rows"]
    for lid in sorted(by_label_rows):
        n = lab[lid]["notation"]
        rws = by_label_rows[lid]
        regs = Counter(rows[rw]["region"] for rw in rws)
        owner_region = sorted(regs, key=lambda k: (-regs[k], OWNER_PRIORITY.index(k)))[0]
        shared = sorted({o for rw in rws for o in row_claims[rw] if o != lid})
        diam_conflict = [o for o in shared if lab[o]["notation"]["dia_mm"] != n["dia_mm"]]
        fid = f"BF-{lid}"
        fams.append({"FAMILY_ID": fid, "KIND": "DOT_ROW", "RUNS": [], "SEGMENTS": [], "LABELS": [lid],
                     "PRIMARY_LABEL": lid, "NOTATION": lab[lid]["raw"], "NOTATION_KIND": n["kind"],
                     "DIA_MM": n["dia_mm"], "PER_M": n["per_m"], "COUNT": n["count"], "DOT_ROWS": rws,
                     "DOTS": binding[lid]["dots"], "OWNER_REGION": owner_region,
                     "COMPONENT_OWNER_ID": COMPONENT_OF_REGION[owner_region], "LEG_UNITS": {},
                     "DIAMETER_STATE": PQ.CONFLICT if diam_conflict else "CONSISTENT",
                     "SHARED_ROW_WITH": shared, "NOTATIONS_ON_FAMILY": [lab[lid]["raw"]], "END_MARKS": []})
        label_state[lid] = (fid, "FAMILY_PRIMARY_LABEL")
    for rw, info in sorted(rows.items()):
        if rw not in row_claims:
            fams.append({"FAMILY_ID": f"BF-UNLABELLED-{rw}", "KIND": "DOT_ROW_UNLABELLED", "RUNS": [], "SEGMENTS": [],
                         "LABELS": [], "PRIMARY_LABEL": None, "NOTATION": None, "NOTATION_KIND": None, "DIA_MM": None,
                         "PER_M": None, "COUNT": None, "DOT_ROWS": [rw], "DOTS": info["dots"],
                         "OWNER_REGION": info["region"], "COMPONENT_OWNER_ID": COMPONENT_OF_REGION[info["region"]],
                         "LEG_UNITS": {}, "DIAMETER_STATE": "UNLABELLED", "NOTATIONS_ON_FAMILY": [], "END_MARKS": []})
    # ---- faces each drawn family's core legs lie on (hooks excluded)
    seg_of = {s[1]: s for r in runs.values() for s in r["_segs"]}
    for f in fams:
        faces = set()
        for sid in f["SEGMENTS"]:
            sg = seg_of[sid]
            if sg[0] != "LINE" or math.dist(sg[2], sg[3]) <= HOOK_MAX_UNITS:
                continue
            mid = ((sg[2][0] + sg[3][0]) / 2, (sg[2][1] + sg[3][1]) / 2)
            reg = region_of(mid, regions["regions"])
            if isinstance(reg, str):
                faces.add(f"{reg}:{nearest_face(mid, reg, regions['faces'])}")
        f["FACES"] = sorted(faces)
    # ---- sub-detail labels: second views of the main-section families (06 / 13 / 16)
    corr = subdetail_correspondence(corner_runs, fams, runs, regions)
    fam_by_id = {f["FAMILY_ID"]: f for f in fams}
    views = []
    for lid, b in sorted(binding.items()):
        if b["method"] != "PROXIMITY_SUB_DETAIL":
            continue
        d = lab[lid]["notation"]["dia_mm"]
        shapes = b["corner_shapes"]
        readings = [{**_view_reading(corr[cr], d, fam_by_id), "faces": corr[cr]["faces"], "cover": corr[cr]["cover"]}
                    for cr in shapes]
        junction = corr[shapes[0]]["junction"] if shapes else None
        if b["state"] == "AMBIGUOUS":
            state, matched = "SUB_DETAIL_BINDING_AMBIGUOUS", []
        elif readings:
            state, matched = readings[0]["state"], readings[0]["matched"]
        else:
            state, matched = "SUB_DETAIL_UNBOUND", []
        views.append({"label": lid, "junction": junction, "shapes": shapes, "dia_mm": d, "state": state,
                      "matched": matched, "involved": sorted({x for r in readings for x in r["involved"]}),
                      "readings": [{"shape": cr, **r} for cr, r in zip(shapes, readings)]})
        label_state[lid] = (matched[0] if state == "SECOND_VIEW_OF_FAMILY" else None, state)
    return fams, label_state, views, corr


def _core_legs(run):
    """Straight legs longer than a drawn hook: orientation (V / H / S), length, midpoint."""
    out = []
    for s in run["_segs"]:
        if s[0] != "LINE" or math.dist(s[2], s[3]) <= HOOK_MAX_UNITS:
            continue
        dx, dy = s[3][0] - s[2][0], s[3][1] - s[2][1]
        o = "V" if abs(dx) < 1.0 else "H" if abs(dy) < 1.0 else "S"
        out.append({"o": o, "len": math.dist(s[2], s[3]), "mid": ((s[2][0] + s[3][0]) / 2, (s[2][1] + s[3][1]) / 2),
                    "seg": s[1]})
    return out


def _hook_sides(run):
    """Orientation of the core leg each drawn hook (an end leg no longer than a hook) is attached to."""
    segs = [s for s in run["_segs"] if s[0] == "LINE"]
    out = set()
    for end, nxt in ((segs[0], segs[1:2]), (segs[-1], segs[-2:-1])) if len(segs) > 1 else ():
        if math.dist(end[2], end[3]) <= HOOK_MAX_UNITS and nxt:
            dx, dy = nxt[0][3][0] - nxt[0][2][0], nxt[0][3][1] - nxt[0][2][1]
            out.add("V" if abs(dx) < 1.0 else "H" if abs(dy) < 1.0 else "S")
    return out


def _longest(legs, o):
    c = [l for l in legs if l["o"] == o]
    return max(c, key=lambda l: (l["len"], l["seg"])) if c else None


def subdetail_correspondence(corner_runs, fams, runs, regions):
    """Which main-section bar family each corner sub-detail shape shows. The sub-details are NTS sketches drawn in
    the main section's orientation, so only order is read, never a length:
      wall / base corner: the shape's longest vertical leg is the OUTER or INNER face (by side, from the main
        section's wall faces) and its longest horizontal leg the base BOTTOM or TOP (lower or higher of the two);
        the main families with a core leg on each of those faces answer it.
      base / slope junction: the shapes and the main runs crossing the junction are ranked by the height of their
        longest horizontal leg; with equal counts, rank k shows rank k. Drawn hooks are a corroboration only."""
    seg_of = {s[1]: s for r in runs.values() for s in r["_segs"]}
    run_fams = [f for f in fams if f["KIND"] == "DRAWN_RUN"]
    fam_faces = {f["FAMILY_ID"]: {tuple(x.split(":")) for x in f["FACES"]} for f in run_fams}
    groups = defaultdict(list)
    for cid, cr in corner_runs.items():
        groups[_shape_junction(cr)].append(f"CR{cid}")
    out = {}
    for j, names in sorted(groups.items()):
        upper, lower = JUNCTIONS[j]
        legs = {n: _core_legs(corner_runs[int(n[2:])]) for n in names}
        if "WALL" in upper:
            outer_x, inner_x = regions["faces"][upper]["OUTER"][1], regions["faces"][upper]["INNER"][1]
            outer_is_min = outer_x < inner_x
            v = {n: _longest(legs[n], "V") for n in names}
            h = {n: _longest(legs[n], "H") for n in names}
            vx = sorted(v[n]["mid"][0] for n in names if v[n])
            hy = sorted(h[n]["mid"][1] for n in names if h[n])
            for n in names:
                faces = []
                if v[n] and len(vx) == 2:
                    lo = v[n]["mid"][0] == vx[0]
                    faces.append((upper, "OUTER" if lo == outer_is_min else "INNER"))
                if h[n] and len(hy) == 2:
                    faces.append((lower, "BOTTOM" if h[n]["mid"][1] == hy[0] else "TOP"))
                cover = {f"{rg}:{fc}": sorted(fid for fid, fs in fam_faces.items() if (rg, fc) in fs)
                         for rg, fc in faces}
                whole = sorted(fid for fid, fs in fam_faces.items() if faces and set(faces) <= fs)
                out[n] = {"junction": j, "rule": "FACE_ORDER", "faces": [f"{rg}:{fc}" for rg, fc in faces],
                          "cover": cover, "whole": whole, "rank": None, "hook_check": None,
                          "determined": len(faces) == 2}
        else:
            base = lower if lower != "SLOPE" else upper
            crossing = [f for f in run_fams if f["LEG_UNITS"].get(upper, 0) > HOOK_MAX_UNITS
                        and f["LEG_UNITS"].get(lower, 0) > HOOK_MAX_UNITS]

            def main_h(f):
                hs = [l for sid in f["SEGMENTS"] for l in _core_legs({"_segs": [seg_of[sid]]})
                      if l["o"] == "H" and region_of(l["mid"], regions["regions"]) == base]
                return max(hs, key=lambda l: (l["len"], l["seg"]))["mid"][1] if hs else None
            mk = sorted(((main_h(f), f["FAMILY_ID"]) for f in crossing if main_h(f) is not None), reverse=True)
            sk = sorted(((_longest(legs[n], "H")["mid"][1], n) for n in names if _longest(legs[n], "H")),
                        reverse=True)
            ok = len(mk) == len(sk) == len(names)
            for k, (_, n) in enumerate(sk):
                fid = mk[k][1] if ok else None
                hc = None
                if fid:
                    vs = _hook_sides(corner_runs[int(n[2:])])
                    ms = _hook_sides({"_segs": [seg_of[sid] for sid in next(f for f in crossing
                                                                            if f["FAMILY_ID"] == fid)["SEGMENTS"]]})
                    hc = "AGREES" if vs == ms else "NOT_ALL_SHOWN_IN_VIEW" if vs < ms else "DIFFERS"
                out[n] = {"junction": j, "rule": "HORIZONTAL_LEG_RANK", "faces": [], "cover": {},
                          "whole": [fid] if fid else [], "rank": k + 1, "hook_check": hc, "determined": ok}
    return out


def _view_reading(c, dia, fam_by_id):
    """What a sub-detail label on one shape says about the main section."""
    if not c["determined"]:
        return {"state": "SECOND_VIEW_FAMILY_NOT_DETERMINED", "matched": [], "involved": []}
    if len(c["whole"]) == 1:
        fid = c["whole"][0]
        same = fam_by_id[fid]["DIA_MM"] == dia
        return {"state": "SECOND_VIEW_OF_FAMILY" if same else "SECOND_VIEW_DIAMETER_CONFLICT", "matched": [fid],
                "involved": [fid]}
    if len(c["whole"]) > 1:
        return {"state": "SECOND_VIEW_FAMILY_NOT_DETERMINED", "matched": [], "involved": c["whole"]}
    involved = sorted({x for v in c["cover"].values() for x in v})
    if not c["cover"] or not all(c["cover"].values()):
        return {"state": "SECOND_VIEW_FAMILY_NOT_DETERMINED", "matched": [], "involved": involved}
    every_face_same_dia = all(any(fam_by_id[x]["DIA_MM"] == dia for x in v) for v in c["cover"].values())
    return {"state": "SECOND_VIEW_TOPOLOGY_DIFFERS" if every_face_same_dia else "SECOND_VIEW_DIAMETER_CONFLICT",
            "matched": [], "involved": involved}


# ------------------------------------------------------------------ interfaces
def interface_audit(runs, corner_runs, regions, fams, views, marks):
    rows = []
    fam_of_run = defaultdict(list)
    for f in fams:
        for r in f["RUNS"]:
            fam_of_run[r].append(f)
    named = {f"R{k}": v for k, v in runs.items()}
    for j, (wall, base) in sorted(JUNCTIONS.items()):
        res = PQ.classify_interface(named, regions["regions"], wall, base, eps_units=1.0,
                                    parallel_tol_units=LAP_TOL, priority=OWNER_PRIORITY)
        jviews = [v for v in views if v["junction"] == j]
        level_change = "WALL" not in wall
        for x in res:
            if level_change and not (x["in_wall_units"] > 1.0 and x["in_base_units"] > 1.0):
                continue                                   # a base bar that does not cross the level change
            fs = fam_of_run[x["run_id"]]
            dias = sorted({f["DIA_MM"] for f in fs if f["DIA_MM"] is not None})
            conflict = any(f["DIAMETER_STATE"] == PQ.CONFLICT for f in fs)
            vconf = [v["label"] for v in jviews if v["state"] in VIEW_CONFLICTS
                     and set(v["involved"]) & {f["FAMILY_ID"] for f in fs}]
            mk = [m["mark_id"] for m in marks if m["host"] and m["host"][0] == x["run_id"]]
            cls = x["class"]
            if conflict or vconf:
                verdict = PQ.UNRESOLVED
                why = "; ".join(w for w in (
                    "one drawn run carries two diameters" if conflict else "",
                    f"sub-detail {', '.join(vconf)} draws this corner differently (another diameter or one continuous "
                    "bar)" if vconf else "") if w)
            elif mk:
                verdict = PQ.UNRESOLVED
                why = f"bar-end mark {', '.join(mk)} on the run: one bar or two lapped bars is not shown"
            else:
                verdict = cls
                why = {"SINGLE_BENT_BAR": "one drawn run bends from one region into the other: one physical bar, "
                                          "counted once by its owner",
                       "BASE_ONLY": "the run stays in the base at this junction",
                       "ANCHORED_STRAIGHT": "a straight run ends inside the other region",
                       "LAP_BETWEEN_DISTINCT_BARS": "two distinct runs side by side",
                       "SEPARATE_STARTER": "a bent run beside a wall bar",
                       "UNRESOLVED": "the run stops above the base: no anchorage is drawn"}[cls]
            rows.append({"INTERFACE_ID": f"{j}:{x['run_id']}", "JUNCTION": j, "WALL_OR_UPPER": wall, "BASE_OR_LOWER": base,
                         "BAR_RUN_ID": x["run_id"], "FAMILIES": [f["FAMILY_ID"] for f in fs], "DIAMETERS_MM": dias,
                         "ENGINE_CLASS": cls, "VERDICT": verdict, "IN_UPPER_UNITS": x["in_wall_units"],
                         "IN_LOWER_UNITS": x["in_base_units"], "PARTNER_RUN": x["partner"],
                         "COMPONENT_OWNER_ID": COMPONENT_OF_REGION[PQ.owner_of(
                             {k: v for k, v in runs[int(x['run_id'][1:])]['lengths_in'].items()},
                             priority=OWNER_PRIORITY)],
                         "SUB_DETAIL_VIEWS": [{"label": v["label"], "state": v["state"], "shapes": v["shapes"]}
                                              for v in jviews],
                         "WHY": why, "COUNTED": "ONCE (one BAR_RUN_ID, one COMPONENT_OWNER_ID)"})
    return rows


# ------------------------------------------------------------------ population
def population(pg, regions, dims, census, arch):
    dimd = {d["handle"]: d for d in dims}
    stated_40 = [d for d in dims if d["value_cm"] == 40.0]
    stated_20 = [d for d in dims if d["value_cm"] == 20.0]
    check(len(stated_40) == 1 and stated_40[0]["spans"] == ["DEEP_BASE_TOP", "DEEP_BASE_BOTTOM"],
          "the only base dimension is the deep base's 40")
    check(sorted(tuple(d["spans"]) for d in stated_20) == [("DEEP_WALL_OUTER", "DEEP_WALL_INNER"),
                                                           ("SHALLOW_WALL_INNER", "SHALLOW_WALL_OUTER")],
          "both walls are dimensioned 20")
    check(abs(pg["wall_t_mm"] - 200.0) < 1e-6, "the plan band is 200 mm, the stated 20 cm")
    asper = {tuple(d["spans"]): d["handle"] for d in dims if d["authority"] == "REFERENCE_AS_PER_ARCH"}
    rows = []

    def add(cid, kind, mat, typ, *, handles, shape, dims_, thickness, level, authority, readiness, missing, owner,
            exists="PRESENT", row_kind="COMPONENT", plan_area=None, page="3; 7", parent=PARENT):
        rows.append({"COMPONENT_ID": cid, "ROW_KIND": row_kind, "PARENT": parent, "COMPONENT_TYPE": typ,
                     "MATERIAL": mat, "SOURCE_PAGE": page, "DXF_HANDLES": handles, "SHAPE": shape,
                     "PHYSICAL_DIMENSIONS": dims_, "THICKNESS": thickness, "LEVEL": level, "PLAN_AREA_M2": plan_area,
                     "SOURCE_AUTHORITY": authority, "QTO_READINESS": readiness, "MISSING_INFORMATION": missing,
                     "COMPONENT_OWNER_ID": owner, "EXISTS": exists, "KIND": kind})
    add(PARENT, "PARENT", "", "SWIMMING_POOL", row_kind="PARENT", parent="", handles=[PLAN_OUTER, PLAN_INNER, POOL_TITLE],
        shape="D-shaped shell: rectangle + semicircular west end", dims_={"outer_m": [3.5, 3.5], "inner_m": [3.1, 3.1]},
        thickness=None, level={"court": "+0.15 (GBP / arch)", "pool": "NOT_PRINTED"},
        authority=f"PRE-S8 {census['pool']['ELEMENT_ID']} ({census['pool']['NEW_S8_OWNER']}) + GBP S-BW outlines; "
                  f"architectural 350 N-S {'matches' if arch['ns_350_matches_outline'] else 'does not match'} the outline",
        readiness="PARENT_AGGREGATE_ONLY",
        missing=["depths", "wall heights", "deep/shallow layout"], owner="S8 POOL")
    base_missing = ["deep / slope / shallow plan extents ('AS PER ARCH'; not printed in the architectural set)",
                    "which plan end is deep (no section mark on plan)"]
    add("PL-BASE", "GROUP", "RC", "BASE_SLAB", row_kind="GROUP", handles=[PLAN_OUTER, SEC["DEEP_BASE_BOTTOM"]],
        shape="structural footprint (outer S-BW outline)", plan_area=pg["A_out"],
        dims_={"footprint_m2": pg["A_out"]}, thickness={"deep": "40 cm (stated, 193F)", "slope": "NOT_STATED",
                                                       "shallow": "NOT_STATED"},
        level="NOT_PRINTED", authority="CAD_GEOMETRY (GBP) corroborated by the stated 350 x 350",
        readiness="BLOCKED", missing=base_missing, owner=PARENT)
    add("PL-BASE-DEEP", "BASE_ZONE", "RC", "DEEP_END_BASE", handles=[SEC["DEEP_BASE_TOP"], SEC["DEEP_BASE_BOTTOM"], "193F"],
        shape="flat slab", dims_={"thickness_cm": 40, "plan_length": f"AS PER ARCH ({asper.get(('DEEP_WALL_INNER', 'SLOPE_TOP_START'))})"},
        thickness={"value_mm": 400, "authority": PQ.STATED, "dimension": "193F"}, level="NOT_PRINTED",
        authority="p.7 stated 40 + NTS section", readiness="BLOCKED",
        missing=["plan extent of the deep zone"], owner="PL-BASE")
    add("PL-BASE-SLOPE", "BASE_ZONE", "RC", "SLOPING_BASE", handles=[SEC["SLOPE_TOP"], SEC["SLOPE_BOTTOM"]],
        shape="plane sloping slab", dims_={"plan_length": f"AS PER ARCH ({asper.get(('SLOPE_TOP_START', 'SLOPE_TOP_END'))})",
                                           "rise": "not printed"},
        thickness={"value_mm": None, "authority": PQ.NTS_GRAPHIC, "note": "drawn, not dimensioned"}, level="NOT_PRINTED",
        authority="NTS section only", readiness="BLOCKED",
        missing=["slope plan length", "rise", "thickness"], owner="PL-BASE")
    add("PL-BASE-SHALLOW", "BASE_ZONE", "RC", "SHALLOW_END_BASE", handles=[SEC["SHALLOW_TOP"], SEC["SHALLOW_BOTTOM"]],
        shape="flat slab", dims_={"plan_length": f"AS PER ARCH ({asper.get(('SLOPE_TOP_END', 'SHALLOW_WALL_INNER'))})"},
        thickness={"value_mm": None, "authority": PQ.NTS_GRAPHIC,
                   "note": "drawn equal to the deep 40 (1495.69 units) but not dimensioned"},
        level="NOT_PRINTED", authority="NTS section only", readiness="BLOCKED",
        missing=["plan extent", "thickness"], owner="PL-BASE")
    for rid in sorted(pg["runs"]):
        add(rid, "WALL_RUN", "RC", "PERIMETER_WALL", handles=[PLAN_OUTER, PLAN_INNER],
            shape="curved half-annulus" if rid.endswith("-W") else "straight",
            plan_area=pg["run_area"][rid], dims_={"band_m2": pg["run_area"][rid], **pg["run_faces"][rid]},
            thickness={"value_mm": 200, "authority": PQ.STATED, "dimensions": ["194D", "195B"],
                       "plan": "CAD_GEOMETRY 200 mm band"},
            level="NOT_PRINTED", authority="CAD_GEOMETRY (GBP) + stated 20", readiness="BLOCKED",
            missing=["wall height (varies from the deep to the shallow end: 'AS PER ARCH')",
                     "which run is the deep end / shallow end / side wall"], owner=PARENT)
    add("PL-WALL-SECTION-DEEP", "SECTION_VIEW", "RC", "DEEP_END_WALL (section view)", row_kind="SECTION_VIEW",
        handles=[SEC["DEEP_WALL_OUTER"], SEC["DEEP_WALL_INNER"], "194D", "1931"], shape="section of an end wall",
        dims_={"thickness_cm": 20, "height": f"AS PER ARCH ({asper.get(('WALL_TOP', 'DEEP_BASE_TOP'))})"},
        thickness={"value_mm": 200, "authority": PQ.STATED}, level="NOT_PRINTED", authority="p.7 NTS section",
        readiness="VIEW_ONLY (its plan run is not identified; quantities sit on the plan runs)",
        missing=["plan run it cuts"], owner="one of PL-WALL-RUN-E / PL-WALL-RUN-W (not determined)")
    add("PL-WALL-SECTION-SHALLOW", "SECTION_VIEW", "RC", "SHALLOW_END_WALL (section view)", row_kind="SECTION_VIEW",
        handles=[SEC["SHALLOW_WALL_INNER"], SEC["SHALLOW_WALL_OUTER"], "195B", "1993"], shape="section of an end wall",
        dims_={"thickness_cm": 20, "height": f"AS PER ARCH ({asper.get(('SHALLOW_FLOOR_TOP', 'WALL_TOP'))})"},
        thickness={"value_mm": 200, "authority": PQ.STATED}, level="NOT_PRINTED", authority="p.7 NTS section",
        readiness="VIEW_ONLY (its plan run is not identified; quantities sit on the plan runs)",
        missing=["plan run it cuts"], owner="one of PL-WALL-RUN-E / PL-WALL-RUN-W (not determined)")
    for jid, (u, l) in sorted(JUNCTIONS.items()):
        add(f"PL-INT-{jid}", "INTERFACE", "RC", "WALL_TO_BASE_INTERSECTION" if "WALL" in jid else "BASE_LEVEL_CHANGE",
            row_kind="INTERFACE", handles=[], shape="section junction", dims_={}, thickness=None, level="NOT_PRINTED",
            authority="p.7 NTS section + corner sub-detail", readiness="SEE 08 (no own quantity)",
            missing=[], owner=f"{COMPONENT_OF_REGION[u]} / {COMPONENT_OF_REGION[l]}")
    add("PL-CORNERS-PLAN", "PLAN_CORNERS", "RC", "WALL_RETURNS_AND_CORNERS", row_kind="INTERFACE",
        handles=[PLAN_OUTER], shape="two 90-degree corners (E wall to N and S walls); tangent joins at the curve",
        dims_={"corners": 2, "tangent_joins": 2}, thickness=None, level="NOT_PRINTED",
        authority="GBP CAD geometry", readiness="NO_CORNER_REINFORCEMENT_DRAWN_IN_PLAN",
        missing=["plan corner bars (none drawn)"], owner="PL-WALL-RUN-E (band split)")
    for cid, typ, why in (("PL-STEPS", "INTERNAL_STEPS_OR_BENCHES", "no step or bench in the section or the plan"),
                          ("PL-THICKENING", "STRUCTURAL_THICKENING_OR_HAUNCH", "no haunch or thickening drawn"),
                          ("PL-OPENINGS", "OPENINGS_AND_SERVICE_PENETRATIONS",
                           "none drawn; skimmers, drains and inlets are not shown (absence is not proven)"),
                          ("PL-PUMP-ROOM", "PUMP_ROOM", "not drawn on any structural or architectural sheet")):
        add(cid, "NOT_SHOWN", "", typ, row_kind="NOT_SHOWN", handles=[], shape="", dims_={}, thickness=None,
            level="", authority="source search (p.3, p.7, architectural GF)", readiness="NOT_QUANTIFIED",
            missing=[why], owner=PARENT, exists="NOT_SHOWN_IN_SOURCE")
    for h, fam in sorted(BUILDUP_TEXT.items()):
        add(f"PL-BUILDUP-{fam}", "BUILD_UP", BOQ_FAMILY[fam], fam, row_kind="BUILD_UP", handles=[h],
            shape="layer", dims_={}, thickness={"stated": "see 09"}, level="NOT_PRINTED", authority="p.7 text + hatch",
            readiness="BLOCKED", missing=["extent / area (see 09)"], owner=PARENT)
    return rows


# ------------------------------------------------------------------ roles
ROLE_TOKENS = ("TOP", "BOTTOM", "OUTER", "INNER", "VERTICAL", "HORIZONTAL", "CORNER")


def derived_role(lid, binding, runs_by_seg, rows, regions, views):
    b = binding[lid]
    if b["segments"]:
        out = []
        for sid in b["segments"]:
            s = runs_by_seg[sid]
            mid = ((s[2][0] + s[3][0]) / 2, (s[2][1] + s[3][1]) / 2) if s[0] == "LINE" else s[2]
            reg = region_of(mid, regions["regions"])
            if not isinstance(reg, str):
                out.append("UNLOCATED")
                continue
            dx, dy = (abs(s[3][0] - s[2][0]), abs(s[3][1] - s[2][1])) if s[0] == "LINE" else (0, 0)
            orient = "VERTICAL" if dx < 1 else "HORIZONTAL" if dy < 1 else "SLOPED"
            face = nearest_face(mid, reg, regions["faces"], exclude=("TOP",) if "WALL" in reg else ())
            kind = "WALL_VERTICAL" if "WALL" in reg else "LONGITUDINAL"
            out.append(f"{reg}:{kind}_{face}" + ("" if "WALL" in reg else f" ({orient})"))
        return "; ".join(sorted(set(out)))
    if b["dot_rows"]:
        parts = []
        for rw in b["dot_rows"]:
            reg, face = rows[rw]["region"], rows[rw]["face"]
            if face == "TOP" and "WALL" in reg:
                parts.append(f"{reg}:TOP_LONGITUDINAL_GROUP")
            elif face.startswith("UNDER_WALL_"):
                parts.append(f"{reg}:CORNER_LONGITUDINAL_{face[len('UNDER_WALL_'):]} (under the wall)")
            elif "WALL" in reg:
                parts.append(f"{reg}:HORIZONTAL_{face}")
            else:
                parts.append(f"{reg}:TRANSVERSE_{face}")
        return "; ".join(sorted(parts))
    v = next((v for v in views if v["label"] == lid), None)
    return f"SUB_DETAIL_BAR_SHAPE at {v['junction']} ({', '.join(v['shapes'])})" if v else "UNBOUND"


def role_agreement(s1_role, derived):
    s1 = {t for t in ROLE_TOKENS if t in s1_role.upper()}
    d = {t for t in ROLE_TOKENS if t in derived.upper()}
    if "WALL_VERTICAL" in derived:
        d.add("VERTICAL")
    if not s1:
        return "NO_FACE_CLAIM_IN_S1"
    return "AGREES" if s1 <= d else "DIFFERS"


# ------------------------------------------------------------------ quantities (every one blocked unless established)
BASE_REGIONS = ("DEEP_BASE", "SLOPE", "SHALLOW_BASE")


def family_quantity(f):
    """Engine call with the authorities the source actually gives. Nothing here invents a width or a run."""
    base = f["OWNER_REGION"] in BASE_REGIONS
    if f["KIND"] in ("DRAWN_RUN_CONFLICT_ZONE",) or f["DIAMETER_STATE"] == PQ.CONFLICT:
        return {"lane": PQ.CONFLICT, "kg": None, "length_m": None, "equivalent_count": None,
                "missing": ["source conflict on this bar family (16)"]}
    if f["NOTATION_KIND"] is None:
        return {"lane": PQ.BLOCKED, "kg": None, "length_m": None, "equivalent_count": None,
                "missing": ["no bar notation on this drawn bar set"]}
    n = PQ.parse_notation(f["NOTATION"])
    if n["kind"] == PQ.FINITE_GROUP:
        q = PQ.finite_qty(n, None, PQ.NOT_ESTABLISHED)
        q["missing"] = ["bar run: the plan length of the wall top / corner it follows (which plan run is not shown)"]
        return q
    width_auth = PQ.NOT_ESTABLISHED
    run_auth = PQ.NTS_GRAPHIC if f["KIND"] == "DRAWN_RUN" else PQ.NOT_ESTABLISHED
    q = PQ.rate_qty(n, None, width_auth, None, run_auth)
    if base:
        q["missing"] = ["distribution width: the zone's plan extent across the bars ('AS PER ARCH'; not printed)",
                        "bar run: the zone's length along the bars plus drawn cranks / hooks (NTS)"]
    elif f["KIND"] == "DOT_ROW":
        q["missing"] = ["distribution width: the wall height ('AS PER ARCH'; not printed)",
                        "bar run: the plan face length of the wall it runs along (which plan run is not shown)"]
    else:
        q["missing"] = ["distribution width: the plan face length of the wall (which plan run is not shown)",
                        "bar run: the wall height plus its legs into the base ('AS PER ARCH'; NTS)"]
    return q


def rebar_rows(fams, binding, labels, roles, interfaces):
    lab = {l["handle"]: l for l in labels}
    base_rows, wall_rows = [], []
    for f in fams:
        q = family_quantity(f)
        um = SR.unit_mass(f["DIA_MM"]) if f["DIA_MM"] else None
        jv = sorted({(i["JUNCTION"], i["VERDICT"]) for i in interfaces if f["FAMILY_ID"] in i["FAMILIES"]})
        row = {"FAMILY_ID": f["FAMILY_ID"], "KIND": f["KIND"], "NOTATION": f["NOTATION"],
               "NOTATION_KIND": f["NOTATION_KIND"], "DIA_MM": f["DIA_MM"], "PER_M": f["PER_M"], "COUNT": f["COUNT"],
               "UNIT_MASS_KG_M": um, "ROLE": "; ".join(roles[l] for l in f["LABELS"]) if f["LABELS"] else
               "; ".join(f.get("DOT_ROWS", [])) or "CONNECTOR",
               "COMPONENT_OWNER_ID": f["COMPONENT_OWNER_ID"], "BAR_RUN_IDS": f["RUNS"],
               "DOT_ROWS": f.get("DOT_ROWS", []), "LABELS": f["LABELS"], "DIAMETER_STATE": f["DIAMETER_STATE"],
               "DISTRIBUTION_WIDTH_M": None, "BAR_RUN_M": None, "EQUIVALENT_COUNT": q.get("equivalent_count"),
               "LENGTH_M": q.get("length_m"), "KG": q.get("kg"), "LANE": q["lane"], "MISSING": q["missing"],
               "INTERFACES": [f"{a}: {b}" for a, b in jv], "PHYSICAL_BBS": "UNRESOLVED",
               "END_MARKS": f["END_MARKS"]}
        (base_rows if f["OWNER_REGION"] in BASE_REGIONS else wall_rows).append(row)
    return base_rows, wall_rows


def concrete_rows(pg):
    rows = []
    g = lambda i, item, v, auth, note: rows.append(  # noqa: E731
        {"ROW_ID": i, "ROW_KIND": "GEOMETRY", "ITEM": item, "COMPONENT_ID": "", "VALUE": v, "UNIT": "m2",
         "AUTHORITY": auth, "M3": None, "LANE": "GEOMETRY_ESTABLISHED", "MISSING": [], "NOTE": note})
    g("CG-01", "water outline (inner S-BW 7C5)", pg["A_in"], PQ.CAD_GEOMETRY,
      "3.10 x 3.10 D-shape: rectangle 1.55 x 3.10 + semicircle R1.55 (exact arc)")
    g("CG-02", "structural outline (outer S-BW 7C6) = base footprint", pg["A_out"], PQ.CAD_GEOMETRY,
      "3.50 x 3.50 D-shape: rectangle 1.75 x 3.50 + semicircle R1.75; stated 350 N-S on the architectural plan")
    g("CG-03", "wall plan band (outline minus water)", pg["band"], PQ.CAD_GEOMETRY,
      "uniform 200 mm band (stated 20 cm in the section); tiled exactly by the four wall runs")
    for i, rid in enumerate(sorted(pg["run_area"]), 4):
        g(f"CG-{i:02d}", f"{rid} band", pg["run_area"][rid], PQ.CAD_GEOMETRY,
          f"inner face {pg['run_faces'][rid]['inner_m']:.6f} m, outer face {pg['run_faces'][rid]['outer_m']:.6f} m")
    rows.append({"ROW_ID": "CG-08", "ROW_KIND": "GEOMETRY", "ITEM": "water perimeter / outer perimeter", "COMPONENT_ID": "",
                 "VALUE": [pg["L_in"], pg["L_out"]], "UNIT": "m", "AUTHORITY": PQ.CAD_GEOMETRY, "M3": None,
                 "LANE": "GEOMETRY_ESTABLISHED", "MISSING": [], "NOTE": "exact lines and arcs"})
    sp = PQ.wall_base_split(pg["A_out"], pg["band"], 0.40, None, footprint_authority=PQ.CAD_GEOMETRY,
                            band_authority=PQ.CAD_GEOMETRY, base_t_authority=PQ.STATED,
                            wall_h_authority=PQ.NOT_ESTABLISHED)
    q = lambda i, cid, item, res, missing, note: rows.append(  # noqa: E731
        {"ROW_ID": i, "ROW_KIND": "QUANTITY", "ITEM": item, "COMPONENT_ID": cid, "VALUE": None, "UNIT": "m3",
         "AUTHORITY": "", "M3": res["m3"], "LANE": res["lane"], "MISSING": missing, "NOTE": note})
    deep = PQ.prism(None, PQ.NOT_ESTABLISHED, 0.40, PQ.STATED)
    q("CQ-01", "PL-BASE-DEEP", "deep-end base: plan extent x 0.40", deep,
      ["plan extent of the deep zone ('AS PER ARCH' 1985; not printed in the architectural set)"],
      "thickness stated (40, dimension 193F); the zone's plan area is not")
    slope = PQ.prism(None, PQ.NOT_ESTABLISHED, None, PQ.NTS_GRAPHIC)
    q("CQ-02", "PL-BASE-SLOPE", "sloping base", slope,
      ["plan extent and rise ('AS PER ARCH' 1977)", "thickness (drawn only)"], "a plane slab: V = A x t / cos(theta)")
    shallow = PQ.prism(None, PQ.NOT_ESTABLISHED, None, PQ.NTS_GRAPHIC)
    q("CQ-03", "PL-BASE-SHALLOW", "shallow-end base", shallow,
      ["plan extent ('AS PER ARCH' 1969)", "thickness (drawn equal to 40, not dimensioned)"], "")
    for i, rid in enumerate(sorted(pg["runs"]), 4):
        w = PQ.prism(pg["run_area"][rid], PQ.CAD_GEOMETRY, None, PQ.NOT_ESTABLISHED)
        q(f"CQ-{i:02d}", rid, f"{rid}: band x height above the base top", w,
          ["wall height above the base top ('AS PER ARCH' 1931 / 1993; varies from the deep to the shallow end)"],
          f"band {pg['run_area'][rid]:.6f} m2 established; the deep / shallow end is not identified on plan")
    rows.append({"ROW_ID": "CO-01", "ROW_KIND": "OWNERSHIP_RULE", "ITEM": "wall / base intersection",
                 "COMPONENT_ID": "PL-BASE", "VALUE": None, "UNIT": "", "AUTHORITY": "pool_qto.wall_base_split",
                 "M3": None, "LANE": "RULE", "MISSING": [],
                 "NOTE": f"{sp['base']['owns']}; {sp['wall']['owns']}; the band x base-thickness prism is owned once, "
                         f"by the {sp['intersection_owner']}"})
    rows.append({"ROW_ID": "CO-02", "ROW_KIND": "OWNERSHIP_RULE", "ITEM": "east wall on the boundary-wall line",
                 "COMPONENT_ID": "PL-WALL-RUN-E", "VALUE": None, "UNIT": "", "AUTHORITY": "GBP S-BW / S-BOUN",
                 "M3": None, "LANE": "RULE", "MISSING": [],
                 "NOTE": "the S-BOUN boundary wall stops at the pool corners (plan overlap 0 m2); the pool owns the "
                         "east wall between its corners; any wall above court level on that line is not pool"})
    rows.append({"ROW_ID": "CO-03", "ROW_KIND": "OWNERSHIP_RULE", "ITEM": "curved ground beam round the pool",
                 "COMPONENT_ID": "", "VALUE": pg["curved_gb_clear_mm"], "UNIT": "mm clear", "AUTHORITY": "GBP layer 1",
                 "M3": None, "LANE": "RULE", "MISSING": [],
                 "NOTE": "ground-beam arcs 157 / 158 (S5 / S6 owned) lie outside the pool outline: no shared concrete"})
    return rows


def blocked_register(fams, rebar):
    out = []
    q = {r["FAMILY_ID"]: r for r in rebar}
    for f in fams:
        comps = ["DISTRIBUTION_WIDTH", "BAR_RUN", "COUNT_CONVENTION", "LAPS", "ANCHORAGE", "COVER"]
        if f["KIND"] == "DRAWN_RUN":
            comps += ["BENDS_AND_HOOKS"]
        if f["DIAMETER_STATE"] == PQ.CONFLICT or f["KIND"] == "DRAWN_RUN_CONFLICT_ZONE":
            comps += ["TOPOLOGY_OR_DIAMETER_CONFLICT"]
        if f["END_MARKS"]:
            comps += ["BAR_END_MARK_AT_MIDSPAN"]
        if f["NOTATION_KIND"] is None and f["KIND"] != "DRAWN_RUN_CONFLICT_ZONE":
            comps += ["NOTATION"]
        why = {"DISTRIBUTION_WIDTH": "plan extent across the bars is not established",
               "BAR_RUN": "bar length is not established; the drawn length is NTS",
               "COUNT_CONVENTION": "physical bar count (end bars, rounding) is not stated",
               "LAPS": "no lap length or lap position is printed",
               "ANCHORAGE": "anchorage / development into the adjoining element is not printed",
               "COVER": "governing cover not established (14)",
               "BENDS_AND_HOOKS": "bends and hooks are drawn on an NTS detail: no radius, no leg length",
               "TOPOLOGY_OR_DIAMETER_CONFLICT": "the drawing shows two incompatible readings (16)",
               "BAR_END_MARK_AT_MIDSPAN": "a drawn hook mark at mid-span: one bar or two lapped bars is not shown",
               "NOTATION": "drawn bars with no notation"}
        for c in comps:
            out.append({"BLOCKED_ID": f"{f['FAMILY_ID']}:{c}", "FAMILY_ID": f["FAMILY_ID"], "COMPONENT": c,
                        "COMPONENT_OWNER_ID": f["COMPONENT_OWNER_ID"], "LANE": q[f["FAMILY_ID"]]["LANE"]
                        if c == "TOPOLOGY_OR_DIAMETER_CONFLICT" else PQ.BLOCKED, "KG": None, "LENGTH_M": None,
                        "WHY": why[c]})
    return out


# ------------------------------------------------------------------ build-up
def buildup_register(src, det, regions, pg):
    """Screed, insulation membrane and plain concrete: exact wording, hatch, stacked-label order, extent."""
    doc = src.doc
    fx, fy = src.sheets[DET]["frame"][:2]
    by_h = det["by_h"]
    hatches = {}
    for h in doc.modelspace().query("HATCH"):
        if h.dxf.layer in HATCH_FAMILY:
            pts = []
            for p in h.paths:
                if hasattr(p, "vertices"):
                    pts += [(v[0] - fx, v[1] - fy) for v in p.vertices]
                else:
                    pts += [(e.start[0] - fx, e.start[1] - fy) for e in p.edges if hasattr(e, "start")]
            hatches[HATCH_FAMILY[h.dxf.layer]] = {"handle": h.dxf.handle, "layer": h.dxf.layer,
                                                  "pattern": h.dxf.pattern_name, "paths": len(h.paths),
                                                  "x": (min(q[0] for q in pts), max(q[0] for q in pts)),
                                                  "y": (min(q[1] for q in pts), max(q[1] for q in pts))}
    check(set(hatches) == set(HATCH_FAMILY.values()), "one hatch per build-up layer")
    dr = regions["drawn"]
    lines = {k: by_h[h] for k, h in BUILDUP_LINES.items()}
    y_screed_out = min(p[1] for p in lines["SCREED_OUTER"]["pts"])
    y_membrane_out = min(p[1] for p in lines["MEMBRANE_OUTER"]["pts"])
    y_plain_bot = lines["PLAIN_BOTTOM_DEEP"]["a"][1]
    x_screed_out = min(p[0] for p in lines["SCREED_OUTER"]["pts"])
    x_membrane_out = min(p[0] for p in lines["MEMBRANE_OUTER"]["pts"])
    x_plain_end = lines["PLAIN_END_DEEP"]["a"][0]
    bands = {"SCREED": dr["deep_base_bottom"] - y_screed_out, "INSULATION_MEMBRANE": y_screed_out - y_membrane_out,
             "PLAIN_CONCRETE": y_membrane_out - y_plain_bot}
    order_down = sorted(hatches, key=lambda k: -hatches[k]["y"][0])        # nearest the concrete first
    texts = sorted(((h, by_h[h]) for h in BUILDUP_TEXT), key=lambda kv: -kv[1]["p"][1])
    check([BUILDUP_TEXT[h] for h, _ in texts] == ["SCREED", "INSULATION_MEMBRANE", "PLAIN_CONCRETE"],
          "stacked labels read screed / membrane / plain concrete from the top")
    rows = []
    for h, t in texts:
        fam = BUILDUP_TEXT[h]
        m = re.match(r"(\d+(?:\.\d+)?)\s*cm\b", t["text"])
        ht = hatches[fam]
        wraps_walls = ht["y"][1] >= dr["wall_top"] - 1.0
        rows.append({"LAYER_ID": f"PL-BUILDUP-{fam}", "SOURCE_WORDING": t["text"], "TEXT_HANDLE": h,
                     "BOQ_FAMILY": BOQ_FAMILY[fam], "STATED_THICKNESS_CM": float(m.group(1)) if m else None,
                     "THICKNESS_AUTHORITY": PQ.STATED if m else PQ.NOT_ESTABLISHED,
                     "HATCH": f"{ht['handle']} {ht['layer']} {ht['pattern']}",
                     "POSITION_FROM_CONCRETE": order_down.index(fam) + 1,
                     "DRAWN_THICKNESS_UNITS_NTS": _r(bands[fam]),
                     "EXTENT_DRAWN": ("under the whole base and up the outer face of both walls to the wall top"
                                      if wraps_walls else
                                      f"under the base only, projecting past the membrane by {_r(x_membrane_out - x_plain_end)} "
                                      "drawing units (not dimensioned)"),
                     "AREA_M2": None, "VOLUME_M3": None, "LANE": PQ.BLOCKED,
                     "MISSING": (["wall heights (wall faces)", "true area of the sloping underside"] if wraps_walls else
                                 ["projection beyond the walls", "true area of the sloping underside"]),
                     "MEANING_NOT_ESTABLISHED": ("product / specification of an 'insulation membrane' 5 cm thick is not "
                                                 "stated; the wording is kept as printed" if fam == "INSULATION_MEMBRANE"
                                                 else ""),
                     "BINDING": "stacked label order on leader 187B (ticks in each band) agrees with the hatch order "
                                "from the concrete outwards and with the hatch layer names",
                     "INTERFACE": (f"{BLINDING_RECORD} cites handle 1877: the pool's plain concrete is this pool record "
                                   "and must not be counted again under blinding" if fam == "PLAIN_CONCRETE" else ""),
                     "NOT_GROUND_SLAB": "S8.1A C-03: these texts are the pool's build-up, not the ground slab's"})
    return rows, {"bands_units": bands, "order_from_concrete": order_down,
                  "screed_outer_x": x_screed_out, "membrane_outer_x": x_membrane_out}


# ------------------------------------------------------------------ cover
def cover_rows(rules):
    n22 = next(r for r in rules if r["rule_id"] == "P8-N22")
    rows = [
        {"FACE": "BASE_UNDERSIDE", "CONTACT_DRAWN": "screed then insulation membrane then plain concrete",
         "CONTACT_CONDITION": "CAST_ON_MEMBRANE_OR_SEPARATION", "SOURCE_RULE": "P8-N22",
         "RULE_TEXT": n22["raw_text"], "RULE_VALUES": n22["values"],
         "APPLIES": "slab minimum 25 mm may apply (a base is a slab); the 70 mm soil value needs a slab cast "
                    "against soil, which is not drawn",
         "SOURCE_MINIMUM_MM": None, "NOMINAL_DESIGN_COVER_MM": None, "FABRICATION_COVER_MM": None,
         "STATE": "COVER_APPLICABILITY_UNRESOLVED"},
        {"FACE": "WALL_OUTER_FACE", "CONTACT_DRAWN": "screed and membrane up the wall; what lies beyond is not drawn",
         "CONTACT_CONDITION": "CONTACT_CONDITION_UNRESOLVED", "SOURCE_RULE": "P8-N22",
         "RULE_TEXT": n22["raw_text"], "RULE_VALUES": n22["values"],
         "APPLIES": "the member list is columns, slabs and beams; a pool wall is not named, and soil contact is "
                    "not drawn",
         "SOURCE_MINIMUM_MM": None, "NOMINAL_DESIGN_COVER_MM": None, "FABRICATION_COVER_MM": None,
         "STATE": "COVER_APPLICABILITY_UNRESOLVED"},
        {"FACE": "WALL_INNER_AND_BASE_TOP (water-facing)", "CONTACT_DRAWN": "pool water",
         "CONTACT_CONDITION": "WATER_FACING", "SOURCE_RULE": "none",
         "RULE_TEXT": "", "RULE_VALUES": {},
         "APPLIES": "no project rule names a water-facing surface",
         "SOURCE_MINIMUM_MM": None, "NOMINAL_DESIGN_COVER_MM": None, "FABRICATION_COVER_MM": None,
         "STATE": "UNKNOWN_EXPOSURE_CONDITION"},
        {"FACE": "ALL (drawn covers)", "CONTACT_DRAWN": "", "CONTACT_CONDITION": "", "SOURCE_RULE": "",
         "RULE_TEXT": "", "RULE_VALUES": {},
         "APPLIES": "bar offsets on the NTS section are drawing units only and are never converted to mm",
         "SOURCE_MINIMUM_MM": None, "NOMINAL_DESIGN_COVER_MM": None, "FABRICATION_COVER_MM": None,
         "STATE": "NTS_NOT_A_MEASUREMENT"},
        {"FACE": "CHECKER", "CONTACT_DRAWN": "", "CONTACT_CONDITION": "", "SOURCE_RULE": "",
         "RULE_TEXT": "", "RULE_VALUES": {},
         "APPLIES": "a code or design checker may challenge the detail (water-retaining exposure) but never replaces "
                    "the project's bar notation or quantity basis",
         "SOURCE_MINIMUM_MM": None, "NOMINAL_DESIGN_COVER_MM": None, "FABRICATION_COVER_MM": None,
         "STATE": "CHALLENGE_ONLY"}]
    return rows


# ------------------------------------------------------------------ sensitivity (never released)
def sensitivity_rows(pg, fams):
    rows = []
    add = lambda i, item, basis, value, unit, kind, note: rows.append(  # noqa: E731
        {"SCENARIO_ID": i, "ITEM": item, "BASIS": basis, "VALUE": value, "UNIT": unit, "KIND": kind,
         "LANE": PQ.SENSITIVITY_ONLY, "IN_OFFICIAL_TOTAL": False, "NOTE": note})
    add("SEN-01", "base concrete, reading A (40 cm on the deep base only, as dimensioned)", "0.40 m3 per m2 of the "
        "deep zone's plan area", 0.40, "m3/m2", "COEFFICIENT", "the deep zone's plan area is not printed")
    add("SEN-02", "base concrete, reading B (40 cm on the whole base, as drawn)", "footprint x 0.40 (flat projection)",
        pg["A_out"] * 0.40, "m3", "LOWER_BOUND",
        "a lower bound only: the sloping strip adds A x t (1/cos(theta) - 1), theta not printed")
    add("SEN-03", "wall concrete per metre of uniform wall height above the base top", "band area",
        pg["band"], "m3/m", "COEFFICIENT", "wall heights vary from the deep to the shallow end and are not printed")
    for i, rid in enumerate(sorted(pg["run_area"]), 4):
        add(f"SEN-{i:02d}", f"{rid} concrete per metre of its height", "run band area", pg["run_area"][rid],
            "m3/m", "COEFFICIENT", "")
    add("SEN-08", "plain concrete under the base (10 cm)", "footprint x 0.10", pg["A_out"] * 0.10, "m3",
        "LOWER_BOUND", "the drawn projection past the walls and the sloping strip add to it; neither is dimensioned")
    add("SEN-09", "screed (5 cm) and insulation membrane, base underside", "footprint (flat projection)",
        pg["A_out"], "m2", "LOWER_BOUND", "screed volume = 0.05 x area; the sloping strip adds")
    add("SEN-10", "screed and membrane up the outer wall faces, per metre of wall height", "outer perimeter",
        pg["L_out"], "m2/m", "COEFFICIENT", "")
    for f in fams:
        if f["NOTATION_KIND"] in (PQ.RATE, PQ.SPACING) and f["DIAMETER_STATE"] != PQ.CONFLICT:
            um = SR.unit_mass(f["DIA_MM"])
            add(f"SEN-{f['FAMILY_ID']}", f"{f['FAMILY_ID']} {f['NOTATION']}", "source notation density: bars per m x "
                "D^2/162 (one family, one direction)", f["PER_M"] * um, "kg/m2", "NOTATION_DENSITY",
                f"{f['PER_M']:g} m of bar per m2 of the zone it covers; laps, legs and hooks excluded")
        elif f["NOTATION_KIND"] == PQ.FINITE_GROUP:
            um = SR.unit_mass(f["DIA_MM"])
            add(f"SEN-{f['FAMILY_ID']}", f"{f['FAMILY_ID']} {f['NOTATION']}", "count x D^2/162",
                f["COUNT"] * um, "kg/m", "NOTATION_DENSITY", "per metre of the run the group follows")
    return rows


# ------------------------------------------------------------------ conflicts and questions
def conflicts_questions(fams, views, marks, rows, binding, regions, dims):
    out = []
    add = lambda i, kind, to, text, affects, status: out.append(  # noqa: E731
        {"ID": i, "KIND": kind, "TO": to, "TEXT": text, "AFFECTS": affects, "STATUS": status})
    conf_runs = sorted({r for f in fams if f["KIND"] == "DRAWN_RUN_CONFLICT_ZONE" for r in f["RUNS"]})
    for r in conf_runs:
        fs = [f for f in fams if r in f["RUNS"]]
        add(f"CF-S8.2-{r}", "DIAMETER_ON_ONE_DRAWN_BAR", "structural engineer",
            f"{r} is drawn as one continuous bar but carries {sorted({f['NOTATION'] for f in fs if f['NOTATION']})}: "
            "outer leg and base leg one diameter, inner leg another, joined over the wall top", [f["FAMILY_ID"] for f in fs],
            "OPEN")
    for v in views:
        rd = v["readings"][0] if v["readings"] else {}
        where = ", ".join(rd.get("faces") or []) or v["junction"]
        if v["state"] == "SECOND_VIEW_DIAMETER_CONFLICT":
            add(f"CF-S8.2-{v['label']}", "SUB_DETAIL_DIAMETER_DISAGREES", "structural engineer",
                f"sub-detail label {v['label']} ({v['dia_mm']:g} mm) draws one bar over {where}; the main section has "
                f"{rd.get('cover') or v['involved']} there, not all of {v['dia_mm']:g} mm", v["involved"], "OPEN")
        if v["state"] == "SECOND_VIEW_TOPOLOGY_DIFFERS":
            add(f"CF-S8.2-{v['label']}", "SUB_DETAIL_TOPOLOGY_DISAGREES", "structural engineer",
                f"sub-detail label {v['label']} draws one continuous bar over {where} (looped at the corner); the main "
                f"section draws separate bars {rd.get('cover')} there", v["involved"], "OPEN")
        if v["state"] == "SUB_DETAIL_BINDING_AMBIGUOUS":
            alt = "; ".join(f"{r['shape']} -> {r['matched'] or r['involved']} ({r['state']})" for r in v["readings"])
            add(f"CF-S8.2-{v['label']}", "AMBIGUOUS_LABEL", "drawing review",
                f"sub-detail label {v['label']} ({v['dia_mm']:g} mm) sits between two bar shapes: {alt}",
                v["shapes"], "OPEN")
    for m in marks:
        add(f"CF-S8.2-{m['mark_id']}", "BAR_END_MARK", "structural engineer",
            f"a hook mark at mid-span of {m['host'][0] if m['host'] else '?'} (segment {m['host'][1] if m['host'] else '?'}): "
            "one bar or two lapped bars is not shown", [m["host"][0]] if m["host"] else [], "OPEN")
    shared = [f for f in fams if f.get("SHARED_ROW_WITH")]
    for f in shared:
        add(f"CF-S8.2-ROW-{f['FAMILY_ID']}", "DOT_ROW_CLAIMED_TWICE", "structural engineer",
            f"{f['FAMILY_ID']} ({f['NOTATION']}) shares drawn dots with {f['SHARED_ROW_WITH']}: the zone boundary "
            "between the two transverse notations is not drawn", [f["FAMILY_ID"]] + f["SHARED_ROW_WITH"], "OPEN")
    on_face = defaultdict(list)
    for f in fams:
        if f["KIND"] == "DRAWN_RUN":
            for fc in f["FACES"]:
                if fc.split(":")[0] in BASE_REGIONS:
                    on_face[fc].append(f)
    for fc, fs in sorted(on_face.items()):
        if len(fs) < 2:
            continue
        nots = sorted({PQ.parse_notation(f["NOTATION"])["raw"] for f in fs})
        same = len({(f["DIA_MM"], f["PER_M"]) for f in fs}) == 1
        add(f"CF-S8.2-COUNT-{fc.replace(':', '-')}", "COUNT_CONVENTION", "structural engineer",
            f"{fc}: {len(fs)} drawn bars lie on this face ({', '.join(f['FAMILY_ID'] + ' ' + f['NOTATION'] for f in fs)}): "
            + ("one rate in total or the rate for each bar is not stated" if same else
               "which notation governs where they overlap, and whether the rates add, is not stated"),
            [f["FAMILY_ID"] for f in fs], "OPEN")
    add("CF-S8.2-TRANSVERSE-LAYERS", "RATE_SCOPE", "structural engineer",
        "each transverse label fans to both the top and the bottom row of its zone: one rate per layer or one rate "
        "shared by the two layers is not stated", [f["FAMILY_ID"] for f in fams if f["KIND"] == "DOT_ROW"
                                                    and len(f.get("DOT_ROWS", [])) > 1], "OPEN")
    units = {d["handle"]: d["measurement_units"] / d["value_cm"] for d in dims if d["value_cm"]}
    add("CF-S8.2-NTS-SCALE", "NOT_TO_SCALE", "record",
        f"drawing units per stated cm differ: {', '.join(f'{h} {v:.2f}' for h, v in sorted(units.items()))}; "
        "plain concrete and the thin layers are drawn at other ratios again", [], "CONFIRMED (no drawn length is used)")
    add("CF-S8.2-SHALLOW-THICKNESS", "THICKNESS_SCOPE", "structural engineer",
        "the slope and shallow base are drawn as thick as the deep base (1495.69 units) but only the deep base is "
        "dimensioned 40", ["PL-BASE-SLOPE", "PL-BASE-SHALLOW"], "OPEN")
    add("CF-S8.2-S1-ROLES", "S1_PROVISIONAL_ROLES", "record",
        "S1's pool roles came from a visual reading; this round binds every label from its leader or sub-detail "
        "shape (13 lists both)", [], "SUPERSEDED_BY_BINDING")
    add("CF-S8.2-BLINDING", "DOUBLE_COUNT_RISK", "record",
        f"{BLINDING_RECORD} cites the pool's '10cm PLAIN CONCRETE' (1877): counted only as the pool's build-up",
        [BLINDING_RECORD, "PL-BUILDUP-PLAIN_CONCRETE"], "GUARDED (no quantity on either side)")
    qs = [("Q-S8.2-01", "architect", "Pool depths: deep-end and shallow-end water depths, wall top level against the "
                                     "court (+0.15), and the plan lengths of the deep, sloping and shallow zones "
                                     "('AS PER ARCH'); the architectural set prints none of them."),
          ("Q-S8.2-02", "architect", "Which plan end is deep: the straight east end or the curved west end? No section "
                                     "mark ties the p.7 section to the plan."),
          ("Q-S8.2-03", "structural engineer", "Thickness of the sloping and shallow base (only the deep base is "
                                               "dimensioned 40)."),
          ("Q-S8.2-04", "structural engineer", "Deep-wall vertical bars: inner face 7Ø12/m (main section) or 7Ø14/m "
                                               "(corner sub-detail); one hairpin over the top or separate bars?"),
          ("Q-S8.2-05", "structural engineer", "Count convention where two drawn bars carry the same rate, and whether "
                                               "each transverse rate is per layer."),
          ("Q-S8.2-06", "structural engineer", "Side walls: the section cuts the two end walls; the reinforcement of "
                                               "the other walls (straight and curved) is not shown."),
          ("Q-S8.2-07", "structural engineer", "Laps, anchorage, hook and bend dimensions, and the cover for the "
                                               "water face and the membrane face."),
          ("Q-S8.2-08", "architect / engineer", "Plain-concrete projection past the walls; what '5cm INSULATION "
                                                "MEMBRANE' is as a product; screed on the outer wall faces."),
          ("Q-S8.2-09", "architect / MEP", "Openings and penetrations (skimmers, drains, inlets, lights) - none are "
                                           "drawn."),
          ("Q-S8.2-10", "architect / engineer", "The east pool wall lies on the site boundary-wall line: where the "
                                                "pool wall ends and the boundary wall starts above court level.")]
    for i, to, text in qs:
        add(i, "QUESTION", to, text, [], "OPEN (revisit only on new source evidence or a consultant clarification)")
    return out


# ------------------------------------------------------------------ source and rule register
def source_rule_register(dims, arch, pdf7, rules, census, pg, det):
    rows = []
    add = lambda i, kind, src, ref, text, auth, use: rows.append(  # noqa: E731
        {"ID": i, "KIND": kind, "SOURCE": src, "REFERENCE": ref, "CONTENT": text, "AUTHORITY": auth, "USE_IN_S8_2": use})
    add("SRC-01", "DRAWING", "ST7757.dxf", DXF_SHA, "structural CAD (GBP plan, DET p.7 details)", "ISSUED", "geometry")
    add("SRC-02", "DRAWING", "ST7757.pdf", PDF_SHA, f"page 7 vector layers {pdf7['layers']}", "ISSUED",
        "notes, legend, cross-check")
    add("SRC-03", "DRAWING", "P7757.dxf", ARCH_SHA, "architectural GF plan (registered by PS5.1)", "ISSUED",
        "stated plan dimensions; depth search")
    add("SRC-04", "PLAN", "GBP", f"{PLAN_OUTER}, {PLAN_INNER}, SWIM {pg['swim_block']['handle']}",
        "S-BW structural and water outlines (bearing wall per the p.7 legend); 'swimming pool' block", PQ.CAD_GEOMETRY,
        "footprint, band, wall runs")
    add("SRC-05", "DETAIL", "DET p.7", f"{POOL_TITLE}, {NIS_TEXT}", "DETAIL OF SWIMMING POOL. (N.I.S)", "NTS",
        "topology, stated 20 / 40, bar labels")
    add("SRC-06", "NOTE", "ST7757.pdf p.7 (S-LEG.TEXT, read on the page render)", "NOTES",
        "THE BUILDER TO WORK WITH STATED DIMENSIONS NOT TO SCALE DRAWING.", "PROJECT_NOTE",
        "only stated dimensions measure; drawn lengths never do")
    add("SRC-07", "LEGEND", "ST7757.pdf p.7 (S-LEG.TEXT)", "LEGEND", "Bearing wall (B.W)", "PROJECT_LEGEND",
        "S-BW outlines are bearing walls")
    add("SRC-08", "STAMP", "ST7757.pdf p.7 (S-NOTE)", "plot stamp", "file path, layout name DETAILS, plot date",
        "NO_ENGINEERING_CONTENT", "none")
    for d in dims:
        add(f"DIM-{d['handle']}", "DIMENSION", "DET p.7", d["handle"], f"'{d['text']}' {d['orientation']} {d['spans']} "
            f"({d['measurement_units']} drawing units)", d["authority"],
            "thickness" if d["value_cm"] else "none ('AS PER ARCH': the architectural set does not print it)")
    add("ARCH-350", "STATED_PLAN_DIMENSION", "P7757.dxf layer 4", "350 / 115 / 75 chain",
        f"N-S 350 between ticks {arch['ns_ticks_y']}", PQ.STATED if arch["ns_350_matches_outline"] else "MISMATCH",
        "corroborates the S-BW outline")
    add("ARCH-OUTLINE", "PLAN", "P7757.dxf layer 5", "arcs + lines", f"pool arcs R {arch['arch_pool_radii']}",
        "ARCHITECTURAL_GEOMETRY", "corroborates the water and structural outlines")
    add("ARCH-DEPTH", "SEARCH", "P7757.dxf all texts", "pool / depth / level / section words",
        f"pool labels {len(arch['pool_labels'])}; depth, level or section texts {len(arch['depth_or_section_texts'])}",
        "SEARCH_RESULT", "no depth exists to measure")
    for rid in ("P8-N22", "P8-N13", "P8-N16", "P7-POOL"):
        r = next(x for x in rules if x["rule_id"] == rid)
        add(rid, "PROJECT_RULE", f"ST7757.pdf p.{r['page']}", rid, r["raw_text"], r["status"],
            {"P8-N22": "cover (14)", "P8-N13": "material (no quantity)", "P8-N16": "plain-concrete mix (09)",
             "P7-POOL": "S1 candidate rule; superseded by the binding (13)"}[rid])
    add("S1-POOL", "CENSUS", "S1 POOL_STRUCTURAL_REGISTER", "26 rows", "pool bar labels with provisional roles",
        "PROVISIONAL", "the 26 records bound and terminated (13)")
    add("PRE-S8-POOL", "CENSUS", "PRE-S8 02", census["pool"]["ELEMENT_ID"], census["pool"]["ELEMENT_FAMILY"],
        census["pool"]["NEW_S8_OWNER"], "parent of the population")
    add("UNIT-MASS", "METHOD", "slab_rebar_qto", SR.UNIT_MASS_METHOD["method"], SR.UNIT_MASS_METHOD["authority"],
        "PROJECT_METHOD", "kg/m of every family")
    return rows


# ------------------------------------------------------------------ the 26 records
def evidence_binding(det, labels, binding, label_state, roles, rebar_by_family):
    s1 = {r["source_id"].split(":")[-1]: r for r in det["s1"]["rows"]}
    lab = {l["handle"]: l for l in labels}
    rows = []
    for h in sorted(s1):
        r, l, b = s1[h], lab[h], binding[h]
        fam, state = label_state[h]
        rows.append({"S1_SOURCE_ID": r["source_id"], "HANDLE": h, "RAW": r["raw"], "NOTATION_KIND": l["notation"]["kind"],
                     "DIA_MM": l["notation"]["dia_mm"], "PER_M": l["notation"]["per_m"],
                     "COUNT": l["notation"]["count"], "BINDING_METHOD": b["method"], "BINDING_STATE": b["state"],
                     "LEADER": l["leader"], "BOUND_RUNS": b["runs"], "BOUND_SEGMENTS": b["segments"],
                     "BOUND_DOT_ROWS": b["dot_rows"], "BOUND_SUB_DETAIL_SHAPES": b["corner_shapes"],
                     "INCIDENTAL_CONTACTS": b["incidental_segments"], "DERIVED_ROLE": roles[h],
                     "S1_PROVISIONAL": f"{r['component']} / {r['role']}",
                     "S1_ROLE_CHECK": role_agreement(r["role"], roles[h]), "FAMILY_ID": fam,
                     "TERMINAL_STATE": state,
                     "QUANTITY_LANE": "VIEW_ONLY" if b["method"] == "PROXIMITY_SUB_DETAIL" or fam not in rebar_by_family
                     else rebar_by_family[fam]["LANE"],
                     "KG": None})
    return rows


# ------------------------------------------------------------------ bar runs, end marks, sub-detail shapes, dot rows
def _shape_junction(cr):
    xs = [s[2][0] for s in cr["_segs"]] + [s[3][0] for s in cr["_segs"] if s[0] == "LINE"]
    xc = (min(xs) + max(xs)) / 2
    return next(j for j, x0, x1 in SUBDETAIL_JUNCTION if x0 <= xc < x1)


def bar_run_register(runs, dups, marks, corner_runs, cdups, rows, fams, views, binding, corr):
    fam_of = defaultdict(list)
    for f in fams:
        for r in f["RUNS"]:
            fam_of[r].append(f["FAMILY_ID"])
        for rw in f.get("DOT_ROWS", []):
            fam_of[rw].append(f["FAMILY_ID"])
    out = []

    def row(**kw):
        base = {"BAR_RUN_ID": None, "ROW_KIND": None, "VIEW": None, "SEGMENTS": [], "SHAPE": None, "LEGS": None,
                "CORE_LEGS": None, "BENDS": None, "DRAWN_HOOKS": None, "TURNS_DEG": [], "DRAWN_LENGTH_UNITS_NTS": None,
                "LEG_UNITS_BY_REGION": {}, "OWNER_REGION": None, "COMPONENT_OWNER_ID": None, "FAMILIES": [],
                "LABELS": [], "END_MARKS": [], "JUNCTION": None, "BENT_BAR": None, "CUT_LENGTH_MM": None,
                "BEND_HOOK_STATE": None, "STRAIGHT_PORTIONS": None, "NOTE": ""}
        base.update(kw)
        out.append(base)
    for rid in sorted(runs):
        r, name = runs[rid], f"R{rid}"
        sd = r["shape_detail"]
        owner = PQ.owner_of(r["lengths_in"], priority=OWNER_PRIORITY)
        row(BAR_RUN_ID=name, ROW_KIND="DRAWN_RUN", VIEW="MAIN_SECTION", SEGMENTS=r["run_segments"], SHAPE=r["shape"],
            LEGS=sd["legs"], CORE_LEGS=sd["core_legs"], BENDS=sd["bends"], DRAWN_HOOKS=sd["hooks"],
            TURNS_DEG=[_r(t, 1) for t in sd["turns_deg"]], DRAWN_LENGTH_UNITS_NTS=_r(r["drawn_length_units"]),
            LEG_UNITS_BY_REGION={k: _r(v) for k, v in r["lengths_in"].items() if v > 0}, OWNER_REGION=owner,
            COMPONENT_OWNER_ID=COMPONENT_OF_REGION[owner], FAMILIES=fam_of[name],
            LABELS=sorted(l for l, b in binding.items() if name in b["runs"]),
            END_MARKS=[m["mark_id"] for m in marks if m["host"] and m["host"][0] == name],
            BENT_BAR=r["shape"] != PQ.STRAIGHT,
            BEND_HOOK_STATE="DRAWN_ONLY (NTS: no bend radius, no hook or leg length)" if sd["bends"] or sd["hooks"]
            else "NONE_DRAWN",
            STRAIGHT_PORTIONS="NOT_MEASURABLE (no leg is dimensioned; drawn legs are NTS)",
            NOTE="owner = region holding the larger share of the drawn length (ownership only, never a quantity)")
    for m in marks:
        row(BAR_RUN_ID=m["mark_id"], ROW_KIND="BAR_END_MARK", VIEW="MAIN_SECTION", SEGMENTS=m["segments"],
            SHAPE="HOOK_MARK", FAMILIES=fam_of[m["host"][0]] if m["host"] else [],
            COMPONENT_OWNER_ID=None, BEND_HOOK_STATE="DRAWN_ONLY",
            NOTE=f"short hook mark touching the middle of {m['host'][0]} segment {m['host'][1]} at {m['point']}: "
                 "a bar end inside the run (one bar or two lapped bars is not shown)" if m["host"] else
                 "short hook mark with no host run")
    for cid in sorted(corner_runs):
        cr, name = corner_runs[cid], f"CR{cid}"
        sd = cr["shape_detail"]
        vs = [v for v in views if name in v["shapes"]]
        c = corr[name]
        row(BAR_RUN_ID=name, ROW_KIND="SUB_DETAIL_SHAPE", VIEW="CORNER_SUB_DETAIL", SEGMENTS=cr["run_segments"],
            SHAPE=cr["shape"], LEGS=sd["legs"], CORE_LEGS=sd["core_legs"], BENDS=sd["bends"], DRAWN_HOOKS=sd["hooks"],
            TURNS_DEG=[_r(t, 1) for t in sd["turns_deg"]], DRAWN_LENGTH_UNITS_NTS=_r(cr["drawn_length_units"]),
            JUNCTION=c["junction"], LABELS=sorted(v["label"] for v in vs),
            FAMILIES=c["whole"] or sorted({x for v in c["cover"].values() for x in v}),
            BENT_BAR=cr["shape"] != PQ.STRAIGHT,
            COMPONENT_OWNER_ID="VIEW_ONLY (a second view of main-section bars; never counted)",
            BEND_HOOK_STATE="DRAWN_ONLY (NTS)", STRAIGHT_PORTIONS="NOT_MEASURABLE",
            NOTE=(f"{c['rule']}: " + (f"faces {c['faces']} -> {c['cover']}" if c["rule"] == "FACE_ORDER" else
                                      f"rank {c['rank']} -> {c['whole']} (hooks {c['hook_check']})") + "; " +
                  ("; ".join(f"{v['label']}: {v['state']}" for v in vs) or "no label on this shape")))
    for rid, info in sorted(rows.items()):
        reg = info["region"]
        row(BAR_RUN_ID=rid, ROW_KIND="DOT_ROW", VIEW="MAIN_SECTION", SEGMENTS=info["dots"], SHAPE="BARS_IN_SECTION",
            OWNER_REGION=reg, COMPONENT_OWNER_ID=COMPONENT_OF_REGION[reg], FAMILIES=fam_of[rid],
            LABELS=sorted(l for l, b in binding.items() if rid in b["dot_rows"]),
            NOTE=f"{info['n_dots']} drawn dots ({info['face']}); bars run out of the section plane: their run is a plan "
                 "length, never a drawn one")
    for d, k in dups:
        row(BAR_RUN_ID=f"DUP-{d}", ROW_KIND="DUPLICATE_COLLAPSED", VIEW="MAIN_SECTION", SEGMENTS=[d, k],
            NOTE=f"{d} repeats the geometry of {k}: counted once")
    for d, k in cdups:
        row(BAR_RUN_ID=f"DUP-{d}", ROW_KIND="DUPLICATE_COLLAPSED", VIEW="CORNER_SUB_DETAIL", SEGMENTS=[d, k],
            NOTE=f"{d} repeats the geometry of {k}: counted once")
    return out


# ------------------------------------------------------------------ floor / pool summary
TRADES = (("RC_CONCRETE", "m3"), ("REINFORCEMENT", "kg"), ("PLAIN_CONCRETE", "m3"), ("SCREED", "m2"),
          ("WATERPROOFING_OR_INSULATION", "m2"))


def _released(items):
    return PQ.released_total([{"lane": lane, "q": q} for lane, q in items], "q")


def summary_rows(concrete, rebar, buildup):
    items = defaultdict(list)                          # (trade, component) -> [(lane, qty)]
    for r in concrete:
        if r["ROW_KIND"] == "QUANTITY":
            items[("RC_CONCRETE", r["COMPONENT_ID"])].append((r["LANE"], r["M3"]))
    for r in rebar:
        items[("REINFORCEMENT", r["COMPONENT_OWNER_ID"])].append((r["LANE"], r["KG"]))
    for r in buildup:
        q = r["VOLUME_M3"] if r["BOQ_FAMILY"] == "PLAIN_CONCRETE" else r["AREA_M2"]
        items[(r["BOQ_FAMILY"], r["LAYER_ID"])].append((r["LANE"], q))
    out = []

    def add(level, ident, trade, unit, its):
        n = Counter(l for l, _ in its)
        rel = _released(its)
        unresolved = len(its) - n[PQ.RELEASED]
        out.append({"LEVEL": level, "ID": ident, "FLOOR": FLOOR, "PARENT": PARENT if level != "FLOOR" else "",
                    "TRADE": trade, "UNIT": unit, "ROWS": len(its), "RELEASED_ROWS": n[PQ.RELEASED],
                    "BLOCKED_ROWS": n[PQ.BLOCKED], "CONFLICT_ROWS": n[PQ.CONFLICT], "RELEASED_QTY": rel,
                    "TOTAL_QTY": rel if unresolved == 0 and its else None,
                    "TOTAL_STATE": "COMPLETE" if unresolved == 0 and its else
                    f"UNKNOWN ({unresolved} of {len(its)} rows unresolved; released part only, not the total)"})
    for trade, unit in TRADES:
        comps = sorted(c for t, c in items if t == trade)
        for c in comps:
            add("COMPONENT", c, trade, unit, items[(trade, c)])
        allits = [x for c in comps for x in items[(trade, c)]]
        add("POOL_TRADE", PARENT, trade, unit, allits)
        add("FLOOR", f"{FLOOR} (pool scope only)", trade, unit, allits)
    return out


# ------------------------------------------------------------------ conservation checks
def conservation_checks(ctx):
    out = []

    def add(cid, what, ok, detail):
        out.append({"CHECK_ID": cid, "CHECK": what, "RESULT": "PASS" if ok else "FAIL", "DETAIL": detail})
    pop, pg, fams, ev = ctx["population"], ctx["pg"], ctx["fams"], ctx["evidence"]
    parents = [r for r in pop if r["ROW_KIND"] == "PARENT"]
    ids = {r["COMPONENT_ID"] for r in pop}
    orphans = [r["COMPONENT_ID"] for r in pop if r["ROW_KIND"] != "PARENT" and r["PARENT"] not in ids]
    add("C-01", "one parent; every component hangs from the pool parent", len(parents) == 1 and not orphans
        and len(ids) == len(pop), f"parents {len(parents)}; orphans {orphans}; ids unique {len(ids) == len(pop)}")
    no_owner = [r["COMPONENT_ID"] for r in pop if not r["COMPONENT_OWNER_ID"]]
    fam_owner = [f["FAMILY_ID"] for f in fams if f["COMPONENT_OWNER_ID"] not in ids]
    run_rows = [r for r in ctx["bar_runs"] if r["ROW_KIND"] == "DRAWN_RUN"]
    run_owner = [r["BAR_RUN_ID"] for r in run_rows if r["COMPONENT_OWNER_ID"] not in ids]
    add("C-02", "one owner per component, per bar family and per drawn bar run",
        not no_owner and not fam_owner and not run_owner,
        f"components without owner {no_owner}; families with no population owner {fam_owner}; runs {run_owner}")
    tile = pg["tiling"]
    water_plus_band = abs(pg["A_in"] + pg["band"] - pg["A_out"])
    add("C-03", "plan footprints: water + wall band = outline; wall runs tile the band; no overlap with neighbours",
        tile["exact"] and water_plus_band < 1e-9 and all(t["overlap_m2"] < 1e-6 for t in pg["boundary_touch"])
        and pg["curved_gb_clear_mm"] > 0,
        f"runs sum {tile['sum_m2']:.9f} vs band {tile['whole_m2']:.9f} (gap {tile['gap_m2']:.2e}); water + band - "
        f"outline {water_plus_band:.2e} m2; boundary-wall overlap {[t['overlap_m2'] for t in pg['boundary_touch']]}; "
        f"curved ground beam clear {pg['curved_gb_clear_mm']:.1f} mm")
    s1h = set(ctx["det"]["s1_handles"])
    terminated = [r for r in ev if r["TERMINAL_STATE"]]
    add("C-04", "all 26 S1 pool records bound and terminated", len(ev) == 26 and {r["HANDLE"] for r in ev} == s1h
        and len(terminated) == 26, f"{len(ev)} rows; states {dict(Counter(r['TERMINAL_STATE'] for r in ev))}")
    seg_count = Counter(s for f in fams if f["KIND"] in ("DRAWN_RUN", "DRAWN_RUN_CONFLICT_ZONE") for s in f["SEGMENTS"])
    run_segs = Counter(s for r in run_rows for s in r["SEGMENTS"])
    labelled_runs = {r for f in fams for r in f["RUNS"]}
    partition_ok = all(seg_count[s] == 1 for r in run_rows if r["BAR_RUN_ID"] in labelled_runs for s in r["SEGMENTS"])
    iface = Counter((i["JUNCTION"], i["BAR_RUN_ID"]) for i in ctx["interfaces"])
    add("C-05", "no double bar: each drawn segment in one run and one family; one interface row per run per junction",
        partition_ok and all(v == 1 for v in run_segs.values()) and all(v == 1 for v in iface.values()),
        f"segments in families {sum(seg_count.values())} (max multiplicity {max(seg_count.values())}); "
        f"interface rows {len(iface)}; sub-detail views counted 0 times")
    nts_cols = [(o, k) for o, rws in (("04", ctx["base_rebar"]), ("05", ctx["wall_rebar"]), ("06", ctx["bar_runs"]))
                for r in rws for k in ("CUT_LENGTH_MM", "BAR_RUN_M", "LENGTH_M", "DISTRIBUTION_WIDTH_M")
                if r.get(k) not in (None, "")]
    mm_from_dims = [d["handle"] for d in ctx["dims"] if d["value_cm"] is None and d.get("value_mm")]
    add("C-06", "no NTS drawn length becomes a measurement", not nts_cols and not mm_from_dims,
        "every drawn length stays in drawing units (_UNITS_NTS columns); cut length, bar run, width and length are "
        f"empty on every bar row; offenders {nts_cols}")
    carrying = [(o, r.get("ROW_ID") or r.get("FAMILY_ID") or r.get("LAYER_ID") or r.get("BLOCKED_ID"))
                for o, rws, keys in (("03", ctx["concrete"], ("M3",)), ("04", ctx["base_rebar"], ("KG", "LENGTH_M")),
                                     ("05", ctx["wall_rebar"], ("KG", "LENGTH_M")),
                                     ("07", ctx["blocked"], ("KG", "LENGTH_M")),
                                     ("09", ctx["buildup"], ("AREA_M2", "VOLUME_M3")))
                for r in rws for k in keys if r.get("LANE") != PQ.RELEASED and r.get(k) not in (None, "")]
    add("C-07", "no blocked or conflicting component carries an official m3, m2 or kg", not carrying,
        f"offenders {carrying}")
    s81 = _rows(P["s81_register"])
    s81_handles = {h for r in s81 for h in re.findall(r"[0-9A-F]{2,5}", r["BOUNDARY_HANDLES"])}
    pool_handles = {h for r in pop for h in r["DXF_HANDLES"]} | {s for f in fams for s in f["SEGMENTS"]}
    leak = sorted(pool_handles & s81_handles)
    s7_s81 = [ctx["frozen"][k]["files_checked"] for k in ("S7", "S8.1", "S8.1A")]
    add("C-08", "no S7 / S8.1 leak: pool handles are not ground-slab boundaries; frozen stages verify",
        not leak and all(n > 0 for n in s7_s81), f"shared handles {leak}; S7 / S8.1 / S8.1A files verified {s7_s81}")
    plain = [r for r in ctx["buildup"] if r["BOQ_FAMILY"] == "PLAIN_CONCRETE"]
    add("C-09", "no double plain concrete: one pool plain-concrete layer, no volume, the PRE-S8 blinding record guarded",
        len(plain) == 1 and plain[0]["VOLUME_M3"] is None and "1877" in ctx["census"]["blinding"]["DXF_HANDLES"]
        and BLINDING_RECORD in plain[0]["INTERFACE"], f"{len(plain)} plain-concrete layer; {BLINDING_RECORD} cites "
                                                      "1877 and holds no pool quantity here")
    ratio = [r["SCENARIO_ID"] for r in ctx["sensitivity"] if "kg/m3" in r["UNIT"] or r["IN_OFFICIAL_TOTAL"]]
    off = [r for r in ctx["sensitivity"] if r["LANE"] != PQ.SENSITIVITY_ONLY]
    add("C-10", "no rough ratio: no kg/m3; sensitivity rows never enter a total", not ratio and not off,
        f"{len(ctx['sensitivity'])} sensitivity rows, all SENSITIVITY_ONLY and IN_OFFICIAL_TOTAL False")
    bad = []
    for trade, _ in TRADES:
        rs = [r for r in ctx["summary"] if r["TRADE"] == trade]
        comp = math.fsum(r["RELEASED_QTY"] for r in rs if r["LEVEL"] == "COMPONENT")
        n_comp = sum(r["ROWS"] for r in rs if r["LEVEL"] == "COMPONENT")
        for lv in ("POOL_TRADE", "FLOOR"):
            t = next(r for r in rs if r["LEVEL"] == lv)
            if abs(t["RELEASED_QTY"] - comp) > 1e-9 or t["ROWS"] != n_comp:
                bad.append((trade, lv))
    add("C-11", "totals reconcile: component = pool trade = floor, for every trade", not bad, f"mismatches {bad}")
    zero = [r["ID"] + ":" + r["TRADE"] for r in ctx["summary"] if r["ROWS"] and r["RELEASED_ROWS"] < r["ROWS"]
            and r["TOTAL_QTY"] is not None]
    add("C-12", "unknown stays unknown: a total with an unresolved row is empty, never 0", not zero,
        f"offenders {zero}; released rows {sum(r['RELEASED_ROWS'] for r in ctx['summary'] if r['LEVEL'] == 'FLOOR')}")
    add("C-13", "all frozen stages verify (code, inputs, outputs)", len(ctx["frozen"]) == len(MANIFESTS),
        f"{len(ctx['frozen'])} manifests: {sum(v['files_checked'] for v in ctx['frozen'].values())} files")
    fg = [f for f in fams if f["NOTATION_KIND"] == PQ.FINITE_GROUP]
    in_rows = {f["FAMILY_ID"]: sum(ctx["dot_rows"][rw]["n_dots"] for rw in f["DOT_ROWS"]) for f in fg}
    fg_ok = all(f["PER_M"] is None and in_rows[f["FAMILY_ID"]] == f["COUNT"] for f in fg)
    add("C-14", "a finite group is never a rate; the drawn dots of its row match its count", bool(fg) and fg_ok,
        "; ".join(f"{f['FAMILY_ID']} {f['NOTATION']}: {in_rows[f['FAMILY_ID']]} dots in {f['DOT_ROWS']}" for f in fg))
    text = "\n".join((HERE / o).read_text(encoding="utf-8") for o in OUTPUTS[1:10] + OUTPUTS[12:16]
                     if (HERE / o).exists())
    forb = [w for w in SR.FORBIDDEN_LABELS if w in text]
    add("C-15", "no forbidden release label in any output", not forb, f"found {forb}")
    sub = {r["HANDLE"] for r in ev if r["BINDING_METHOD"] == "PROXIMITY_SUB_DETAIL"}
    views_counted = sorted({r["HANDLE"] for r in ev if r["HANDLE"] in sub and r["QUANTITY_LANE"] != "VIEW_ONLY"} |
                           {l for f in fams for l in f["LABELS"] if l in sub})
    add("C-16", "sub-detail labels are second views: never a family of their own", not views_counted,
        f"{sum(1 for r in ev if r['BINDING_METHOD'] == 'PROXIMITY_SUB_DETAIL')} sub-detail labels; offenders "
        f"{views_counted}")
    return out


# ------------------------------------------------------------------ provenance, summary, readme, build
def provenance(ctx):
    base = {"source": "ST7757.dxf", "drawing_sha256": DXF_SHA}
    out = []
    for r in ctx["population"]:
        out.append({**base, "record": r["COMPONENT_ID"], "output": OUTPUTS[2], "lane": r["QTO_READINESS"],
                    "handles": r["DXF_HANDLES"], "authority": r["SOURCE_AUTHORITY"],
                    "sheets": [GBP, DET] if r["ROW_KIND"] in ("PARENT", "GROUP", "COMPONENT") else [DET]})
    for r in ctx["concrete"]:
        out.append({**base, "record": r["ROW_ID"], "output": OUTPUTS[3], "lane": r["LANE"], "component": r["COMPONENT_ID"],
                    "authority": r["AUTHORITY"], "missing": r["MISSING"], "sheets": [GBP] if r["ROW_KIND"] == "GEOMETRY"
                    else [GBP, DET]})
    for name, rws in ((OUTPUTS[4], ctx["base_rebar"]), (OUTPUTS[5], ctx["wall_rebar"])):
        for r in rws:
            out.append({**base, "record": r["FAMILY_ID"], "output": name, "lane": r["LANE"], "sheets": [DET],
                        "labels": r["LABELS"], "runs": r["BAR_RUN_IDS"], "dot_rows": r["DOT_ROWS"],
                        "owner": r["COMPONENT_OWNER_ID"], "unit_mass": SR.UNIT_MASS_METHOD["method"]})
    for r in ctx["buildup"]:
        out.append({**base, "record": r["LAYER_ID"], "output": OUTPUTS[9], "lane": r["LANE"], "sheets": [DET],
                    "handles": [r["TEXT_HANDLE"]], "wording": r["SOURCE_WORDING"], "hatch": r["HATCH"]})
    for r in ctx["evidence"]:
        out.append({**base, "record": r["S1_SOURCE_ID"], "output": OUTPUTS[13], "lane": r["QUANTITY_LANE"],
                    "sheets": [DET], "handles": [r["HANDLE"]] + r["LEADER"], "binding": r["BINDING_METHOD"],
                    "state": r["TERMINAL_STATE"], "family": r["FAMILY_ID"]})
    out.append({"record": "ARCH-CORROBORATION", "output": OUTPUTS[1], "lane": "CORROBORATION", "source": "P7757.dxf",
                "drawing_sha256": ARCH_SHA, "registration": "PS5.1 translation_arch_to_gbp",
                "ns_350_matches_outline": ctx["arch"]["ns_350_matches_outline"],
                "arch_pool_radii": ctx["arch"]["arch_pool_radii"]})
    out.append({"record": "PDF-P7", "output": OUTPUTS[1], "lane": "NOTES_AND_LEGEND", "source": "ST7757.pdf",
                "drawing_sha256": PDF_SHA, "page": 7, "layers": ctx["pdf7"]["layers"]})
    return out


def write_jsonl(name, rows):
    (HERE / name).write_text("".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in rows),
                             encoding="utf-8")


def build():
    import alsenan_structural_s1 as S1M
    frozen = verify_inputs()
    census = census_rows()
    rules = _j(S1 / "STRUCTURAL_PROJECT_RULE_REGISTER.json")["rows"]
    src = S1M.Source(DXF)
    check(src.sha256 == DXF_SHA, "S1 reader opened the issued structural DXF")
    det = det_evidence(src)
    regions = section_regions(det["sec"])
    dims = det_dimensions(src, regions["drawn"])
    pdf7 = pdf_page7()
    pg = plan_geometry(src)
    arch = arch_corroboration(pg, src)
    check(arch["ns_350_matches_outline"], "the architectural 350 matches the structural outline")
    check(not arch["pool_labels"] or all(not re.search(r"\d", w["text"]) for w in arch["pool_labels"]),
          "no architectural pool label carries a depth")
    bars = det_bars(det, regions)
    rows = dot_rows(bars["dots"], regions)
    runs0, dups = runs_of(bars["main"], regions["regions"])
    runs, marks = split_marks(runs0)
    corner_runs, cdups = runs_of(bars["corner"], {})
    labels = det_labels(det)
    check({l["handle"] for l in labels} == set(det["s1_handles"]), "the pool's bar labels are exactly S1's 26")
    binding = bind_all(labels, runs, corner_runs, bars["dots"], rows)
    fams, label_state, views, corr = families(labels, binding, runs, marks, rows, corner_runs, regions)
    interfaces = interface_audit(runs, corner_runs, regions, fams, views, marks)
    runs_by_seg = {s[1]: s for r in runs.values() for s in r["_segs"]}
    roles = {l["handle"]: derived_role(l["handle"], binding, runs_by_seg, rows, regions, views) for l in labels}
    base_rb, wall_rb = rebar_rows(fams, binding, labels, roles, interfaces)
    rebar_by_family = {r["FAMILY_ID"]: r for r in base_rb + wall_rb}
    pop = population(pg, regions, dims, census, arch)
    concrete = concrete_rows(pg)
    blocked = blocked_register(fams, base_rb + wall_rb)
    buildup, bu_info = buildup_register(src, det, regions, pg)
    cover = cover_rows(rules)
    sens = sensitivity_rows(pg, fams)
    cq = conflicts_questions(fams, views, marks, rows, binding, regions, dims)
    srr = source_rule_register(dims, arch, pdf7, rules, census, pg, det)
    ev = evidence_binding(det, labels, binding, label_state, roles, rebar_by_family)
    bar_runs = bar_run_register(runs, dups, marks, corner_runs, cdups, rows, fams, views, binding, corr)
    summ = summary_rows(concrete, base_rb + wall_rb, buildup)

    for o in OUTPUTS + [MANIFEST_NAME]:                            # a rebuild never inherits a stale output
        if (HERE / o).exists():
            (HERE / o).unlink()
    for name, rws in ((OUTPUTS[1], srr), (OUTPUTS[2], pop), (OUTPUTS[3], concrete), (OUTPUTS[4], base_rb),
                      (OUTPUTS[5], wall_rb), (OUTPUTS[6], bar_runs), (OUTPUTS[7], blocked), (OUTPUTS[8], interfaces),
                      (OUTPUTS[9], buildup), (OUTPUTS[10], summ), (OUTPUTS[13], ev), (OUTPUTS[14], cover),
                      (OUTPUTS[15], sens), (OUTPUTS[16], cq)):
        check(rws, f"{name} has rows")
        _csv(name, rws, list(rws[0]))
    ctx = {"population": pop, "pg": pg, "fams": fams, "evidence": ev, "bar_runs": bar_runs, "interfaces": interfaces,
           "base_rebar": base_rb, "wall_rebar": wall_rb, "concrete": concrete, "blocked": blocked, "buildup": buildup,
           "dims": dims, "det": det, "frozen": frozen, "census": census, "sensitivity": sens, "summary": summ,
           "arch": arch, "pdf7": pdf7, "dot_rows": rows}
    cons = conservation_checks(ctx)
    _csv(OUTPUTS[12], cons, list(cons[0]))
    check(all(c["RESULT"] == "PASS" for c in cons), "conservation: " + "; ".join(
        f"{c['CHECK_ID']} {c['DETAIL']}" for c in cons if c["RESULT"] != "PASS"))
    write_jsonl(OUTPUTS[11], provenance(ctx))
    lanes = Counter(r["LANE"] for r in base_rb + wall_rb)
    summary = {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "plan_m2": {"structural_footprint": pg["A_out"], "water": pg["A_in"], "wall_band": pg["band"],
                    "wall_runs": dict(sorted(pg["run_area"].items()))},
        "perimeter_m": {"water": pg["L_in"], "outer": pg["L_out"]},
        "stated": {"wall_thickness_mm": 200, "deep_base_thickness_mm": 400,
                   "dimensions": {d["handle"]: d["text"] for d in dims}},
        "depths": {"deep_end": None, "shallow_end": None, "wall_heights": None, "zone_lengths": None,
                   "state": "NOT_ESTABLISHED ('AS PER ARCH'; the architectural set prints none)"},
        "concrete": {"released_m3": _released([(r["LANE"], r["M3"]) for r in concrete if r["ROW_KIND"] == "QUANTITY"]),
                     "blocked_rows": sum(1 for r in concrete if r["ROW_KIND"] == "QUANTITY" and r["LANE"] == PQ.BLOCKED),
                     "total_m3": None},
        "reinforcement": {"families": len(fams), "lanes": dict(sorted(lanes.items())),
                          "released_kg": _released([(r["LANE"], r["KG"]) for r in base_rb + wall_rb]),
                          "base_families": len(base_rb), "wall_families": len(wall_rb), "total_kg": None,
                          "diameters_mm": sorted({f["DIA_MM"] for f in fams if f["DIA_MM"]}),
                          "physical_bbs": "UNRESOLVED", "equivalent_length_m": None},
        "bar_runs": {"drawn_runs": len(runs), "end_marks": len(marks), "sub_detail_shapes": len(corner_runs),
                     "dot_rows": len(rows), "duplicates_collapsed": len(dups) + len(cdups),
                     "shapes": dict(sorted(Counter(r["shape"] for r in runs.values()).items()))},
        "interfaces": dict(sorted(Counter(i["VERDICT"] for i in interfaces).items())),
        "records_26": dict(sorted(Counter(r["TERMINAL_STATE"] for r in ev).items())),
        "build_up": {r["LAYER_ID"]: {"wording": r["SOURCE_WORDING"], "boq_family": r["BOQ_FAMILY"], "lane": r["LANE"]}
                     for r in buildup},
        "build_up_order_from_concrete": bu_info["order_from_concrete"],
        "cover": dict(sorted(Counter(r["STATE"] for r in cover).items())),
        "conflicts": sorted(r["ID"] for r in cq if r["KIND"] != "QUESTION"),
        "questions": sorted(r["ID"] for r in cq if r["KIND"] == "QUESTION"),
        "conservation": {c["CHECK_ID"]: c["RESULT"] for c in cons},
        "frozen_baselines": {k: v["manifest_sha256"] for k, v in frozen.items()},
        "references_read": []}
    _json(OUTPUTS[17], summary)
    (HERE / OUTPUTS[0]).write_text(readme(summary, pop, concrete, fams, interfaces, buildup, cq), encoding="utf-8")
    manifest = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "FROZEN_BEFORE_COMPARISON",
                "engine_commit_stamp": summary["engine_commit"], "references_read": [],
                "code": {c: _sha(ROOT / c) for c in CODE},
                "inputs": {str(Path(v).relative_to(ROOT)): _sha(v) for v in P.values()} |
                          {f"research/alsenan_structural_census_s1/{r}.json": _sha(S1 / f"{r}.json") for r in S1_REGS},
                "drawing_sha256": {"ST7757.dxf": DXF_SHA, "P7757.dxf": ARCH_SHA, "ST7757.pdf": PDF_SHA},
                "frozen_baselines": summary["frozen_baselines"],
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
                "released": {"concrete_m3": summary["concrete"]["released_m3"],
                             "reinforcement_kg": summary["reinforcement"]["released_kg"]},
                "rule": "S8.2 is built blind and frozen before any earlier pool quantity, contractor estimate or donor "
                        "figure is opened; only stated or CAD-established dimensions measure"}
    _json(MANIFEST_NAME, manifest)
    return summary


def readme(s, pop, concrete, fams, interfaces, buildup, cq):
    pm = s["plan_m2"]
    L = ["# S8.2: swimming pool, source-controlled concrete and reinforcement QTO", "",
         f"Baseline `{s['baseline']}`. Built blind and frozen before comparison (`{MANIFEST_NAME}`, "
         "`references_read: []`).", "",
         "## Result", "",
         f"- Released concrete: **{s['concrete']['released_m3']:g} m3**. All {s['concrete']['blocked_rows']} concrete "
         "rows are blocked.",
         f"- Released reinforcement: **{s['reinforcement']['released_kg']:g} kg**. The "
         f"{s['reinforcement']['families']} bar families are split by lane as {s['reinforcement']['lanes']}.",
         "- Pool totals: **unknown**. They are left empty, not 0.", "",
         "The p.7 detail is NOT TO SCALE. Its depths, wall heights and deep / slope / shallow lengths read "
         "'AS PER ARCH', and the architectural set prints none of them. Every volume and every bar mass therefore "
         "waits for a stated depth, height or extent.", "",
         "## Established geometry (GBP, exact lines and arcs)", "",
         "| item | m2 |", "|---|---|",
         f"| structural footprint (base) | {pm['structural_footprint']:.6f} |",
         f"| water outline | {pm['water']:.6f} |",
         f"| wall band (200 mm) | {pm['wall_band']:.6f} |"]
    L += [f"| {k} | {v:.6f} |" for k, v in pm["wall_runs"].items()]
    L += ["", f"Stated dimensions: walls 20 cm (both), deep base 40 cm. Perimeters: water {s['perimeter_m']['water']:.6f} m, "
              f"outer {s['perimeter_m']['outer']:.6f} m.", "",
          "## Reinforcement", "",
          f"- {s['bar_runs']['drawn_runs']} drawn bar runs in the main section, shaped {s['bar_runs']['shapes']}.",
          f"- {s['bar_runs']['end_marks']} bar-end mark, {s['bar_runs']['sub_detail_shapes']} sub-detail shapes and "
          f"{s['bar_runs']['dot_rows']} dot rows.",
          f"- Diameters: {s['reinforcement']['diameters_mm']} mm.",
          f"- All 26 S1 records terminate: {s['records_26']}.",
          f"- Wall/base interfaces: {s['interfaces']}.",
          "- No physical bar schedule exists. Bends, hooks, laps and anchorage are drawn only on the NTS detail.", "",
          "## Build-up (kept as printed, separate BOQ families)", ""]
    L += [f"- `{k}`: '{v['wording']}' -> {v['boq_family']} ({v['lane']})" for k, v in s["build_up"].items()]
    L += ["", f"## Conflicts ({len(s['conflicts'])}) and questions ({len(s['questions'])})", "",
          "See `16_CONFLICT_AND_QUESTION_REGISTER.csv`.", "",
          "## Outputs", ""] + [f"- `{o}`" for o in OUTPUTS] + [f"- `{MANIFEST_NAME}`"]
    return "\n".join(L) + "\n"


def main():
    try:
        s = build()
    except Stop as e:
        raise SystemExit(f"STOP: {e}")
    print(json.dumps({k: s[k] for k in ("plan_m2", "concrete", "reinforcement", "interfaces", "records_26",
                                        "conservation")}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
