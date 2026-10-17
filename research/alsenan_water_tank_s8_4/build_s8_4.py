"""S8.4 - water-tank roof region: concrete and reinforcement QTO, source-controlled and blind (frozen before any
comparison).

    python3 -I research/alsenan_water_tank_s8_4/build_s8_4.py

Reads the registered structural DXF (ST7757: p.6 SECOND FLOOR ROOF SLAB, p.1 column and axis plan, the 't' thickness
tags of p.4 / p.5), the registered architectural DXF (P7757: every text, for any tank) and frozen Urban stages (S1
registers, PRE-S7, PRE-S7.1, S6, S7, S7A, S8.3). Pages that exist only as plots (the p.6 legend, the p.8-15 notes,
schedules and typical details, the architectural sections and elevations) enter as visual records read in session;
their renders are client drawing and stay out of git.

It establishes which physical objects the 'WATER TANK PLACE' annotation covers, measures only what the source states
(the slab thickness, the plan faces and the four (T&B) rate callouts), keeps every portion an interpretation would
change apart with its kg as sensitivity, and proves the interface with S7 without moving any frozen quantity. No
earlier Urban quantity, contractor figure or third-party figure is read.
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
from engine.source import legacy_text as LT  # noqa: E402
from engine.source import rebar_unit_mass as UM  # noqa: E402
from engine.source import slab_layered_mesh as M  # noqa: E402

ROUND = "S8_4"
DATE = "2026-10-09"
BASELINE_HEAD = "cce41a2"
POLICY = "S8_4_WATER_TANK_ROOF_REGION_V1"
R = ROOT / "research"
BY_SHA = ROOT / "data/inputs/by_sha256"
STRUCT_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
STRUCT_PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
SET_KEY = "P7757_ARCH_PDF_SET_01-12"
SET_PARTS = {"ARCH_PART_1_PAGES_01-06": "cd3b8669d55998cb638bd8e2b572da4992ed64babcecacd73753d6a2f0c68b97",
             "ARCH_PART_2_PAGES_07-12": "1e7087d3e61bbb682c9107193c97550a2837e5198bde0ee311319bf7f4a08459"}
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
             "S8.3A": R / "alsenan_dome_mesh_s8_3a/09_S8_3A_FREEZE_MANIFEST.json"}
S83_ERRATA = R / "alsenan_dome_ring_s8_3/errata"
S1D = R / "alsenan_structural_census_s1"
READ = {"S1_PANELS": S1D / "SLAB_PANEL_REGISTER.json",
        "S1_SPECIAL": S1D / "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER.json",
        "S1_SLAB_REBAR": S1D / "SLAB_REBAR_SOURCE_REGISTER.json",
        "S1_RULES": S1D / "STRUCTURAL_PROJECT_RULE_REGISTER.json",
        "PRE7_COMPONENTS": R / "alsenan_slab_rebar_pre_s7/04_COMPONENT_READINESS.csv",
        "PRE7_THICKNESS": R / "alsenan_slab_rebar_pre_s7/02_THICKNESS_REGISTER.csv",
        "PRE7_CONFLICTS": R / "alsenan_slab_rebar_pre_s7/11_SOURCE_CONFLICTS.csv",
        "PRE7_QUESTIONS": R / "alsenan_slab_rebar_pre_s7/15_ENGINEER_QUESTIONS.csv",
        "PRE71_TRANSFERS": R / "alsenan_slab_rebar_pre_s7_1/02_OWNERSHIP_TRANSFERS.csv",
        "PRE71_AD2": R / "alsenan_slab_rebar_pre_s7_1/01_AD2_DECISIONS.json",
        "S6_OCC": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCES.csv",
        "S7_ITEMS": R / "alsenan_slab_rebar_s7/01_S7_RELEASE_ITEMS.csv",
        "S7_BLOCKED": R / "alsenan_slab_rebar_s7/02_S7_BLOCKED_ITEMS.csv",
        "S7_RUNS": R / "alsenan_slab_rebar_s7/04_S7_BAR_RUNS.csv",
        "S7_PANELS": R / "alsenan_slab_rebar_s7/05_S7_PANEL_SUMMARY.csv",
        "S7_SUPPORTS": R / "alsenan_slab_rebar_s7/06_S7_SUPPORT_SUMMARY.csv",
        "S7_SUMMARY": R / "alsenan_slab_rebar_s7/09_S7_PROJECT_SUMMARY.json",
        "S7A_ENDS": R / "alsenan_slab_rebar_s7a_qa/08_END_CONDITION_AUDIT.csv",
        "S83_SUMMARY": R / "alsenan_dome_ring_s8_3/15_S8_3_SUMMARY.json",
        "S83A_VERIFY": R / "alsenan_dome_mesh_s8_3a/07_FROZEN_VERIFICATION.json",
        "SOURCE_MANIFEST": ROOT / "tests/alsenan/registers/SOURCE_MANIFEST.json"}
CODE = ["engine/source/slab_layered_mesh.py", "engine/source/slab_rebar_qto.py", "engine/source/delta_release.py",
        "engine/source/legacy_text.py", "engine/source/rebar_unit_mass.py",
        "research/alsenan_water_tank_s8_4/build_s8_4.py", "research/external_engine_lab/alsenan_structural_s1.py"]
OUTPUTS = ["00_README.md", "01_SOURCE_REGISTER.csv", "02_POPULATION_AND_OWNERSHIP.csv",
           "03_THICKNESS_AND_CALLOUT_REGISTER.csv", "04_CONCRETE_QTO.csv", "05_REINFORCEMENT_QTO.csv",
           "06_REINFORCEMENT_BANDS.csv", "07_S7_OWNERSHIP_RECONCILIATION.csv", "08_BLOCKED_COMPONENTS.csv",
           "09_SOURCE_CONFLICTS_AND_QUESTIONS.csv", "10_INTERFACE_AUDIT.csv", "11_SENSITIVITY_CASES.csv",
           "12_CONSERVATION_CHECKS.csv", "13_PROVENANCE.jsonl", "14_S8_4_SUMMARY.json"]
MANIFEST_NAME = "15_S8_4_FREEZE_MANIFEST.json"
UNIT_MASS = {"method": UM.D2_OVER_162, "authority": "project-wide method used by S7 / S8.1 / S8.2 / S8.3",
             "selected_by": "Urban (project basis)"}
SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO = "SOURCE_DERIVED_PHYSICAL", "PROJECT_BASIS_QTO"
BLOCKED, CONFLICT, SENS = "BLOCKED_UNQUANTIFIED", "SOURCE_CONFLICT", "SENSITIVITY_ONLY"
NOT_IN_SOURCE, NOT_ADDED = "NOT_IN_SOURCE", "NOT_ADDED"
RELEASED_LANES = (SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO)
S7_RESTRICTED_KG = 3802.015

# ------------------------------------------------------------------ the brief's starting population
START_POPULATION = ("SP-2F_ROOF_SLAB-01", "SP-2F_ROOF_SLAB-02", "SPC-WATER_TANK-SFRS")
PANELS = ("SP-2F_ROOF_SLAB-01", "SP-2F_ROOF_SLAB-02")
PARENT = "SPC-WATER_TANK-SFRS"
SHORT = {"SP-2F_ROOF_SLAB-01": "01", "SP-2F_ROOF_SLAB-02": "02"}
REGION = "WATER_TANK_SUPPORT_REGION"
# ------------------------------------------------------------------ structural source (ST7757)
SHEET, AXIS_SHEET = "SFRS", "CAP"
NOTE_H, LEADER_H, CLOUD_H = "1A85", ("1A83", "1A84"), "1A81"
NOTE2_H, NOTE2_RATE_H = ("EA", "EC"), "EB"
BEAM_LAYERS, COLUMN_LAYER, BAR_LAYER, TEXT_LAYER = ("1",), "S-COL.BON", "S-REIN-SLAB", "S-TEXT-SLAB"
TAG_RADIUS = (380.0, 420.0)                 # the 't' thickness block draws its circle at r 400
AXIS_DIMS = {"1176": ("X", 2700.0), "1182": ("X", 2000.0), "1150": ("Y_FROM_TOP", 4800.0),
             "12AC": ("Y_FROM_TOP", 1600.0)}
BEAM_WIDTH_MM = 200.0
STOP_RULE = {"rule": "P15-SLAB-ON-BEAMS", "ratio": 0.125, "fraction": 0.5,
             "classes": ("CONTINUOUS", "CONTINUITY_UNRESOLVED")}
NOTE2 = {"rule": "SFRS plan note 2", "rate_per_m": 5, "dia_mm": 10, "ratio": 1.0 / 3.0}
TANK_WORDS = re.compile(r"TANK|W\.T\b|RESERVOIR|خزان|خزن", re.I)
# ------------------------------------------------------------------ visual records (read in session; renders not kept)
VISUAL = [
    {"ID": "VR-S8.4-01", "FILE": "ST7757.pdf", "PAGE": 6, "DPI": 150, "BOX_PX": [915, 411, 1551, 900],
     "READ": "one scalloped cloud encloses both panels and the B3 beam between them; the 'WATER TANK PLACE' leader "
             "ends on its top edge; each panel holds a circled 'T / 18' tag and two bar callouts, each with its own "
             "'(T&B)'; a double line under the horizontal callout and a single line beside the vertical one"},
    {"ID": "VR-S8.4-02", "FILE": "ST7757.pdf", "PAGE": 6, "DPI": 150, "BOX_PX": [2133, 349, 2420, 1256],
     "READ": "legend and note 'THE BUILDER TO WORK WITH STATED DIMENSIONS NOT TO SCALE DRAWING' (plotted title block "
             "only; not in the DXF); no legend symbol for a tank, a tank base or a thickness tag"},
    {"ID": "VR-S8.4-03", "FILE": "ST7757.pdf", "PAGE": "8-15", "DPI": 45, "BOX_PX": None,
     "READ": "recommendations (p.8), schedules (p.9-12) and typical details (p.13-15: footings, ground beams, lintels, "
             "lift, parapet, boundary wall, columns, temperature table, slab on beams): no water-tank detail, section "
             "or schedule row"},
    {"ID": "VR-S8.4-04", "FILE": f"{SET_KEY} ARCH_PART_2_PAGES_07-12", "PAGE": 4, "DPI": 110,
     "BOX_PX": [793, 305, 1158, 386],
     "READ": "SECTION A-A (sheet 10) cuts the tower: the +13.90 roof with a 50 cm parapet; one unhatched, unlabelled "
             "element in view between the parapets, no taller than the parapet; no tank, plinth or tank wall is cut "
             "or labelled"},
    {"ID": "VR-S8.4-05", "FILE": f"{SET_KEY} ARCH_PART_2_PAGES_07-12", "PAGE": 5, "DPI": 110, "BOX_PX": None,
     "READ": "SECTION B-B (sheet 11): the tower in view with its parapet and the tower dome above; no tank"},
    {"ID": "VR-S8.4-06", "FILE": f"{SET_KEY} parts 1-2", "PAGE": "06 / 07-09", "DPI": 90, "BOX_PX": None,
     "READ": "the four elevations (sheets 06-09) show the tower top with its parapet and the tower dome; no tank"},
    {"ID": "VR-S8.4-07", "FILE": f"{SET_KEY} parts 1-2", "PAGE": "01-12", "DPI": 40, "BOX_PX": None,
     "READ": "the set has area plans, three floor plans, four elevations, two sections and the fence; no roof plan "
             "of the tower top (+13.90) exists, so no plan places or sizes a tank"}]


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


def _r(v, nd=9):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


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


# ------------------------------------------------------------------ inputs
def verify_inputs():
    need = {"ST7757.dxf": BY_SHA / f"{STRUCT_SHA}.dxf", "P7757.dxf": BY_SHA / f"{ARCH_SHA}.dxf"}
    absent = [k for k, p in need.items() if not p.exists()]
    check(not absent, f"private inputs not in data/inputs/by_sha256 (never committed): {absent}")
    check(_sha(need["ST7757.dxf"]) == STRUCT_SHA and _sha(need["P7757.dxf"]) == ARCH_SHA, "drawings unchanged")
    frozen = {k: DR.verify_frozen(m, ROOT) for k, m in MANIFESTS.items()}
    errata = _j(READ["S83A_VERIFY"])["s8_3_errata_sha256"]
    for name, h in errata.items():
        check(_sha(S83_ERRATA / name) == h, f"S8.3 errata {name} unchanged")
    return frozen, errata


# ------------------------------------------------------------------ geometry helpers
def _pip(pt, poly):
    x, y = pt
    inside = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def _centroid(poly):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        c = x0 * y1 - x1 * y0
        a += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    return (cx / (3 * a), cy / (3 * a))


def _seg_on(seg, a, b, tol=0.5):
    """seg lies on the segment a-b (collinear within tol, contained in its extent)."""
    (p, q) = seg
    L = math.dist(a, b)
    if L <= tol:
        return False
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    for pt in (p, q):
        dx, dy = pt[0] - a[0], pt[1] - a[1]
        if abs(dx * uy - dy * ux) > tol:
            return False
        s = dx * ux + dy * uy
        if not -tol <= s <= L + tol:
            return False
    return True


def _poly_segments(e):
    return [(s[0], s[1]) for s in e.get("segs", []) if s[0] != "ARC"]


def _dist_to_poly(pt, poly):
    best = math.inf
    for a, b in zip(poly, poly[1:] + poly[:1]):
        L2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((pt[0] - a[0]) * (b[0] - a[0]) + (pt[1] - a[1]) * (b[1] - a[1])) / L2))
        best = min(best, math.dist(pt, (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))))
    return best


# ------------------------------------------------------------------ drawings
def structural(src):
    E = src.entities()
    sh = E[SHEET]
    by = defaultdict(list)
    for e in sh:
        by[e["handle"]].append(e)
    one = lambda h: by[h][0] if len(by[h]) == 1 else None       # noqa: E731
    texts = [e for e in sh if e["type"] in ("TEXT", "MTEXT")]
    # every tank word on any sheet of the structural drawing (decoded text never matters here: all are Latin)
    tank_hits = [(k, e["handle"], e["text"]) for k, ents in E.items() for e in ents
                 if e["type"] in ("TEXT", "MTEXT") and TANK_WORDS.search(e["text"] or "")]
    note = one(NOTE_H)
    leader = [one(h) for h in LEADER_H]
    cloud = one(CLOUD_H)
    check(note and note["text"].strip().upper() == "WATER TANK PLACE", "the note 1A85 reads WATER TANK PLACE")
    check(all(leader) and cloud and cloud["closed"] and cloud["has_bulge"], "leader and cloud present")
    # thickness tags: circles (closed REIN polylines of constant radius) with their texts
    tags = []
    for e in sh:
        if e["type"] != "LWPOLYLINE" or e["layer"] != "REIN" or not e["closed"] or len(e["pts"]) < 24:
            continue
        c = _centroid(e["pts"])
        rr = [math.dist(c, p) for p in e["pts"]]
        if max(rr) - min(rr) > 2.0 or not TAG_RADIUS[0] <= sum(rr) / len(rr) <= TAG_RADIUS[1]:
            continue
        inside = [t for t in texts if math.dist(t["p"], c) <= sum(rr) / len(rr)]
        val = M.thickness_tag([(t["text"], t["p"]) for t in inside], c, sum(rr) / len(rr))
        tags.append({"circle": e["handle"], "centre": c, "radius": sum(rr) / len(rr),
                     "texts": sorted((t["handle"], t["text"]) for t in inside), "value": val,
                     "anchor": next((t for t in inside if (t["text"] or "").strip().isdigit()), None),
                     "letter": next((t for t in inside if (t["text"] or "").strip() == "T"), None)})
    # the project's 't' thickness block elsewhere (same circle radius and text offsets)
    blocks = []
    for k, ents in E.items():
        for e in ents:
            if e["type"] == "INSERT" and e.get("name") == "t":
                kids = [x for x in ents if x.get("via") == f"{e['handle']}:t"]
                circ = [x for x in kids if x["type"] == "LWPOLYLINE"]
                tx = [x for x in kids if x["type"] in ("TEXT", "MTEXT")]
                if len(circ) == 1:
                    c = _centroid(circ[0]["pts"])
                    letter = next((t for t in tx if t["text"].strip() == "T"), None)
                    num = next((t for t in tx if t["text"].strip().isdigit()), None)
                    blocks.append({"sheet": k, "insert": e["handle"], "centre": c,
                                   "radius": sum(math.dist(c, p) for p in circ[0]["pts"]) / len(circ[0]["pts"]),
                                   "value": num["text"].strip() if num else None,
                                   "offset_T": (letter["p"][0] - c[0], letter["p"][1] - c[1]) if letter else None,
                                   "offset_N": (num["p"][0] - c[0], num["p"][1] - c[1]) if num else None})
    calls = [t for t in texts if t["layer"] == TEXT_LAYER and M.parse_rate_callout(t["text"])]
    quals = [t for t in texts if t["layer"] == TEXT_LAYER and M.parse_layer_qualifier(t["text"])]
    bar_lines = [(e["handle"], tuple(e["a"]), tuple(e["b"])) for e in sh if e["type"] == "LINE" and e["layer"] == BAR_LAYER]
    faces = [(e["handle"], tuple(e["a"]), tuple(e["b"])) for e in sh if e["type"] == "LINE" and e["layer"] in BEAM_LAYERS]
    cols = {e["handle"]: e["pts"] for e in sh if e["type"] == "LWPOLYLINE" and e["layer"] == COLUMN_LAYER}
    beam_tags = [t for t in texts if t["layer"] == "S-TEXT" and re.fullmatch(r"B\d+", t["text"].strip())]
    note2 = [one(h) for h in NOTE2_H]
    note2_rate = one(NOTE2_RATE_H)
    # axis chains on the column and axis plan
    dims = {e["handle"]: e for e in E[AXIS_SHEET] if e["type"] == "DIMENSION"}
    axis_cols = {e["handle"]: e["pts"] for e in E[AXIS_SHEET] if e["type"] == "LWPOLYLINE" and e["layer"] == COLUMN_LAYER}
    return {"note": note, "leader": leader, "cloud": cloud, "tags": tags, "t_blocks": blocks, "calls": calls,
            "quals": quals, "bar_lines": bar_lines, "faces": faces, "cols": cols, "beam_tags": beam_tags,
            "note2": note2, "note2_rate": note2_rate, "dims": dims, "axis_cols": axis_cols, "tank_hits": tank_hits,
            "sheet_info": src.sheets[SHEET]}


def architecture():
    """Every text of the architectural DXF (model space and block definitions), legacy Arabic decoded."""
    import ezdxf
    doc = ezdxf.readfile(str(BY_SHA / f"{ARCH_SHA}.dxf"))
    fam = {st.dxf.name.upper(): LT.font_family(st.dxf.get("font", "") or "") for st in doc.styles}
    n, hits, decoded = 0, [], 0
    containers = [("MODEL", doc.modelspace())] + [(b.name, b) for b in doc.blocks
                                                  if not b.name.upper().startswith(("*MODEL", "*PAPER"))]
    for cname, cont in containers:
        for e in cont:
            t = e.dxftype()
            if t not in ("TEXT", "MTEXT", "ATTDEF"):
                continue
            raw = e.text if t == "MTEXT" else e.dxf.text
            f = fam.get((e.dxf.get("style", "") or "").upper())
            dec = LT.decode(raw, f)["text"] if f else ""
            decoded += bool(f)
            n += 1
            if TANK_WORDS.search(raw or "") or TANK_WORDS.search(dec or ""):
                hits.append((cname, e.dxf.handle, raw, dec))
    return {"texts": n, "decoded_legacy": decoded, "tank_hits": hits}


# ------------------------------------------------------------------ model
def panel_model(s1p, st, s7sup):
    """Polygons, edges (with what lies beyond) and the edge classes of the two panels."""
    out = {}
    sup_rows = [r for r in s7sup if r["FLOOR"] == "2F_ROOF_SLAB"]
    for pid in PANELS:
        p = s1p[pid]
        pts = [tuple(v) for v in p["polygon_mm"]]
        s1e = {e["edge_index"]: e for e in p["edges"]}
        edges = []
        for i, (a, b) in enumerate(zip(pts, pts[1:] + pts[:1])):
            drawn = [h for h, u, v in st["faces"] if _seg_on((a, b), u, v)]
            col = [h for h, ps in st["cols"].items() if any(_seg_on((a, b), u, v) for u, v in zip(ps, ps[1:] + ps[:1]))]
            e = s1e.get(i)
            sup_id, ad2 = None, None
            if e is None:
                check(col, f"{pid} edge {i}: not in S1, so it must lie on a drawn column outline")
                support, ref, cont, nb = "COLUMN", f"{SHEET}:{col[0]}", "COLUMN_FACE", None
            else:
                support, ref, cont, nb = e["support"], e["support_ref"], e["continuity"], e["neighbour_panel"]
            if support == "BEAM":
                cand = [r for r in sup_rows if r["SUPPORT_REF"] == ref and pid in json.loads(r["SIDES"])
                        and (nb in json.loads(r["SIDES"]) if nb else None in json.loads(r["SIDES"]))]
                check(len(cand) == 1, f"{pid} edge {i}: one S7 support record ({len(cand)})")
                sup_id, ad2 = cand[0]["SUPPORT_ID"], cand[0]["AD2_CONTINUITY"]
            if support == "COLUMN":
                cls = "COLUMN"
            elif cont in ("ADJACENT_OUTSIDE_BUILDING_OR_COURT", "DISCONTINUOUS"):
                cls = "NON_CONTINUOUS"
            elif ad2 == "CONTINUITY_UNRESOLVED":
                cls = "CONTINUITY_UNRESOLVED"
            elif ad2 in ("", None, "CONTINUOUS") and cont == "CONTINUOUS":
                cls = "CONTINUOUS"
            else:
                cls = "NON_CONTINUOUS"
            check(drawn or col, f"{pid} edge {i} lies on drawn beam-face or column linework")
            edges.append({"index": i, "a": a, "b": b, "length_mm": math.dist(a, b), "support": support,
                          "support_ref": ref, "s1_continuity": cont, "neighbour": nb, "s7_support": sup_id,
                          "s7_ad2_continuity": ad2, "class": cls, "drawn_lines": drawn, "column": col,
                          "in_s1": e is not None})
        out[pid] = {"points": pts, "area_mm2": M.polygon_area(pts), "edges": edges,
                    "classes": {e["index"]: e["class"] for e in edges}, "s1": p}
    return out


def bind_callouts(st, model, s1rebar):
    """Each rate callout -> its panel, its (T&B) qualifier, its bar graphic and its direction."""
    out = []
    for c in st["calls"]:
        pid = [p for p in PANELS if _pip(c["p"], model[p]["points"])]
        if not pid:
            continue
        check(len(pid) == 1, f"callout {c['handle']} in one panel")
        pid = pid[0]
        d = M.baseline_direction(c["rotation"])
        q = [x for x in st["quals"] if _pip(x["p"], model[pid]["points"]) and M.baseline_direction(x["rotation"]) == d]
        g = M.bind_to_bar_graphic(c["p"], c["rotation"], st["bar_lines"])
        s1 = [r for r in s1rebar if r["text_handle"] == c["handle"]]
        check(len(s1) == 1, f"S1 records callout {c['handle']} once")
        out.append({"handle": c["handle"], "panel": pid, "raw": c["text"], "p": c["p"], "rotation": c["rotation"],
                    "parsed": M.parse_rate_callout(c["text"]), "direction": d,
                    "qualifiers": [x["handle"] for x in q], "layers": [M.parse_layer_qualifier(x["text"]) for x in q],
                    "graphic": g, "s1": s1[0]})
    return sorted(out, key=lambda c: (c["panel"], c["direction"]))


def build():
    import alsenan_structural_s1 as S1
    frozen, errata = verify_inputs()
    src = S1.Source()
    check(src.sha256 == STRUCT_SHA, "S1 reads the registered structural DXF")
    st = structural(src)
    arch = architecture()
    s1p = {r["panel_id"]: r for r in _j(READ["S1_PANELS"])["rows"]}
    special = {r["special_id"]: r for r in _j(READ["S1_SPECIAL"])["rows"]}
    s1rebar = _j(READ["S1_SLAB_REBAR"])["rows"]
    rules = {r["rule_id"]: r for r in _j(READ["S1_RULES"])["rows"]}
    comps = {r["COMPONENT_ID"]: r for r in _rows(READ["PRE7_COMPONENTS"])}
    thick = {r["SLAB_PANEL_ID"]: r for r in _rows(READ["PRE7_THICKNESS"])}
    pre7c = {r["CONFLICT_ID"]: r for r in _rows(READ["PRE7_CONFLICTS"])}
    pre7q = {r["QUESTION_ID"]: r for r in _rows(READ["PRE7_QUESTIONS"])}
    transfers = [r for r in _rows(READ["PRE71_TRANSFERS"]) if r["region"] == REGION]
    ad2 = {d["id"]: d for d in _j(READ["PRE71_AD2"])["decisions"]}
    s6 = _rows(READ["S6_OCC"])
    s7_items = {r["S7_ITEM_ID"]: r for r in _rows(READ["S7_ITEMS"])}
    s7_blocked = [r for r in _rows(READ["S7_BLOCKED"]) if r["S8_REGION"] == REGION]
    s7_runs = _rows(READ["S7_RUNS"])
    s7_panels = {r["PANEL_ID"]: r for r in _rows(READ["S7_PANELS"])}
    s7_sup = _rows(READ["S7_SUPPORTS"])
    s7_sum = _j(READ["S7_SUMMARY"])
    s7a = [r for r in _rows(READ["S7A_ENDS"]) if "WATER_TANK" in r["UNRESOLVED_REASON"]]
    s83 = _j(READ["S83_SUMMARY"])
    um = {d: UM.kg_per_m(d, UNIT_MASS) for d in (10, 12, 14)}

    # ------------------------------------------------------------ population
    check(all(p in s1p for p in PANELS) and PARENT in special, "the starting population exists in S1")
    sp = special[PARENT]
    check(sp["kind"] == "WATER_TANK_SLAB" and sorted(sp["panels"]) == list(PANELS) and sp["raw"] == "WATER TANK PLACE"
          and sp["source_id"] == f"NOTE:{SHEET}:{NOTE_H}", "S1's special occurrence is the note over the two panels")
    model = panel_model(s1p, st, s7_sup)
    cloud_poly = [tuple(p) for p in st["cloud"]["pts"]]
    in_cloud = sorted(pid for pid, p in s1p.items() if p.get("sheet") == SHEET and p.get("polygon_mm")
                      and _pip(_centroid([tuple(v) for v in p["polygon_mm"]]), cloud_poly))
    check(in_cloud == list(PANELS), f"the cloud encloses exactly the two panels: {in_cloud}")
    leader_end = min([tuple(x["a"]) for x in st["leader"]] + [tuple(x["b"]) for x in st["leader"]],
                     key=lambda q: _dist_to_poly(q, cloud_poly))
    leader_gap = _dist_to_poly(leader_end, cloud_poly)
    check(leader_gap < 200.0, "the WATER TANK PLACE leader ends on the cloud")
    note_on_leader = min(abs(st["note"]["p"][1] - x["a"][1]) for x in st["leader"] if abs(x["a"][1] - x["b"][1]) < 1)
    check(note_on_leader < 300.0, "the note sits on the leader's horizontal arm")
    between = [h for h, a, b in st["faces"] if abs(a[0] - b[0]) < 1 and 19500 < a[0] < 19900]
    pop = []
    for pid in PANELS:
        m_ = model[pid]
        pop.append({"ROW_ID": f"P-{SHORT[pid]}", "OBJECT": pid, "ROW_KIND": "PHYSICAL_SLAB_PANEL",
                    "PHYSICAL_CLASS": "ROOF_SLAB_DESIGNATED_FOR_A_TANK", "PARENT": PARENT, "COUNTED_ONCE": True,
                    "SOURCE": f"ST7757 p.6 ({SHEET})", "HANDLES": m_["s1"]["boundary_handles"],
                    "AREA_M2": _r(m_["area_mm2"] / 1e6), "THICKNESS_MM": 180, "OWNER": "S8.4",
                    "PRE_S8_ID": pid, "S1_ID": m_["s1"]["source_id"],
                    "EVIDENCE": f"slab face between beam faces; inside cloud {CLOUD_H}; its own T 18 tag and two (T&B) "
                                f"callouts; S7 scope {s7_panels[pid]['S7_SCOPE']}"})
    pop.append({"ROW_ID": "P-ZONE", "OBJECT": PARENT, "ROW_KIND": "USE_ZONE_PARENT",
                "PHYSICAL_CLASS": "WATER TANK PLACE (a designated use over two panels; not a member)", "PARENT": "",
                "COUNTED_ONCE": True, "SOURCE": f"ST7757 p.6 ({SHEET})",
                "HANDLES": [NOTE_H, *LEADER_H, CLOUD_H], "AREA_M2": None, "THICKNESS_MM": None, "OWNER": "S8.4",
                "PRE_S8_ID": PARENT, "S1_ID": sp["source_id"],
                "EVIDENCE": f"one cloud ({len(cloud_poly)} vertices) encloses both panels and the beam between them "
                            f"(line(s) {between}); the leader ends {leader_gap:.0f} mm from the cloud; carries no "
                            "quantity of its own"})
    absent = {"TANK_BASE": "a separate reinforced-concrete tank base or plinth",
              "TANK_WALLS": "reinforced-concrete tank walls, cover slab or other structural tank member",
              "TANK_LOCAL_REINFORCEMENT": "local bars for tank loads: trimmers, extra bars, dowels or starters",
              "TANK_OPENINGS": "an opening, sleeve or penetration in the two panels"}
    for k, v in absent.items():
        pop.append({"ROW_ID": f"P-{k}", "OBJECT": k, "ROW_KIND": "NOT_IN_SOURCE", "PHYSICAL_CLASS": v, "PARENT": PARENT,
                    "COUNTED_ONCE": False, "SOURCE": "ST7757 DXF (all sheets) + p.6-15 plots; P7757 DXF + 12-sheet set",
                    "HANDLES": [], "AREA_M2": None, "THICKNESS_MM": None, "OWNER": "nobody (not drawn)",
                    "PRE_S8_ID": "", "S1_ID": "",
                    "EVIDENCE": f"structural tank words: {len(st['tank_hits'])} (the note only); architectural tank "
                                f"words: {len(arch['tank_hits'])} of {arch['texts']} texts; no section, detail, "
                                "schedule row or outline; VR-S8.4-03..07"})

    # ------------------------------------------------------------ thickness tags
    tags_in = {pid: [t for t in st["tags"] if _pip(t["centre"], model[pid]["points"])] for pid in PANELS}
    check(all(len(v) == 1 and v[0]["value"] and v[0]["value"]["thickness_mm"] == 180 for v in tags_in.values()),
          "one T 18 tag inside each panel")
    check(len(st["tags"]) == 2, "no other thickness tag on the sheet")
    ref = [b for b in st["t_blocks"] if b["value"] == "16"]
    check(len(ref) >= 3, "the 't' block reads 16 elsewhere (the project default)")
    off_err = max(math.dist(t["letter"]["p"], (t["centre"][0] + ref[0]["offset_T"][0], t["centre"][1] + ref[0]["offset_T"][1]))
                  for v in tags_in.values() for t in v)
    rad_err = max(abs(t["radius"] - ref[0]["radius"]) for v in tags_in.values() for t in v)
    check(off_err < 2.0 and rad_err < 2.0, "the T 18 tags are the 't' block's circle and offsets")
    thick_rows = []
    for pid in PANELS:
        t = tags_in[pid][0]
        thick_rows.append({"ROW_ID": f"T-{SHORT[pid]}", "KIND": "THICKNESS_TAG", "PANEL": pid,
                           "HANDLES": [t["circle"], t["letter"]["handle"], t["anchor"]["handle"]],
                           "RAW": "T / 18 (circled)", "READING": "slab thickness 180 mm",
                           "DIA_MM": None, "RATE_PER_M": None, "DIRECTION": None, "LAYERS": None,
                           "GRAPHIC": None, "S1_GRAPHIC": None, "AUTHORITY": "PROJECT_SOURCE",
                           "EVIDENCE": f"circle r {t['radius']:.1f} with 'T' over '18'; the project's 't' block "
                                       f"({len(ref)} inserts, e.g. {ref[0]['sheet']} {ref[0]['insert']}) draws the same "
                                       f"circle and offsets with '16' = the 160 mm default (P8-N18, P1-NOTE-A 'unless "
                                       f"stated otherwise'); geometry match {off_err:.2f} mm; never a bar diameter: no "
                                       f"bar symbol, no '/m'; PRE-S7 {thick[pid]['AUTHORITY']} "
                                       f"{thick[pid]['EFFECTIVE_THICKNESS_MM']} mm",
                           "SCOPE": f"the panel face that holds the tag ({_r(model[pid]['area_mm2'] / 1e6)} m2), "
                                    "beam faces to beam faces"})

    # ------------------------------------------------------------ callouts
    calls = bind_callouts(st, model, s1rebar)
    check(len(calls) == 4, f"four rate callouts in the two panels ({len(calls)})")
    for c in calls:
        check(c["parsed"]["basis"] == M.PER_M and len(c["qualifiers"]) == 1 and c["layers"][0] == (M.BOTTOM, M.TOP),
              f"{c['handle']}: a rate per metre with one (T&B)")
        check(c["graphic"] and c["graphic"]["direction"] == c["direction"], f"{c['handle']}: bound to a parallel bar")
        check(c["s1"]["direction"] == c["direction"] and c["s1"]["dia_mm"] == c["parsed"]["dia_mm"]
              and c["s1"]["count"] == c["parsed"]["count"] and c["s1"]["TandB"], f"{c['handle']}: agrees with S1")
        check(c["s1"]["tb_text_handle"] == c["qualifiers"][0], f"{c['handle']}: S1 and S8.4 bind the same (T&B)")
    dirs = Counter((c["panel"], c["direction"]) for c in calls)
    check(all(dirs[(p, d)] == 1 for p in PANELS for d in M.DIRECTIONS), "one callout per panel and direction")
    for c in calls:
        g = c["graphic"]["handles"]
        c["s1_graphic_ok"] = c["s1"]["bar_graphic_handle"] in g
        thick_rows.append({"ROW_ID": f"C-{c['handle']}", "KIND": "RATE_CALLOUT", "PANEL": c["panel"],
                           "HANDLES": [c["handle"], c["qualifiers"][0], *g], "RAW": f"{c['raw']} (T&B)",
                           "READING": f"{c['parsed']['count']} bars of Ø{c['parsed']['dia_mm']} per metre, direction "
                                      f"{c['direction']}, top and bottom",
                           "DIA_MM": c["parsed"]["dia_mm"], "RATE_PER_M": c["parsed"]["count"],
                           "DIRECTION": c["direction"], "LAYERS": list(c["layers"][0]), "GRAPHIC": g,
                           "S1_GRAPHIC": c["s1"]["bar_graphic_handle"], "AUTHORITY": "PROJECT_SOURCE",
                           "EVIDENCE": f"text rotation {c['rotation']:g} deg along the drawn bar "
                                       f"{'double line' if len(g) == 2 else 'line'} {g} ({c['graphic']['offset']:.0f} mm "
                                       f"away); its own '(T&B)' {c['qualifiers'][0]} gives the faces, the callout's "
                                       f"own bar gives the direction; S1 graphic {c['s1']['bar_graphic_handle']} "
                                       f"{'agrees' if c['s1_graphic_ok'] else 'is another bar (CF-S8.4-01)'}",
                           "SCOPE": f"the panel {c['panel']} face, beam faces to beam faces"})

    # ------------------------------------------------------------ axis chains (plan authority)
    dims = st["dims"]
    check(all(h in dims and abs(dims[h]["measurement"] - v) < 0.5 for h, (_, v) in AXIS_DIMS.items()),
          "the axis chains read 2700 / 2000 / 4800 / 1600")
    def extent(pid, k):
        v = [p[k] for p in model[pid]["points"]]
        return max(v) - min(v)
    p1x, p1y = extent(PANELS[0], 0), extent(PANELS[0], 1)
    p2x, p2y = extent(PANELS[1], 0), extent(PANELS[1], 1)
    spans = {"01_X": (p1x, AXIS_DIMS["1176"][1] - BEAM_WIDTH_MM), "02_X": (p2x, AXIS_DIMS["1182"][1] - BEAM_WIDTH_MM),
             "02_Y": (p2y, AXIS_DIMS["1150"][1] - AXIS_DIMS["12AC"][1] - BEAM_WIDTH_MM), "01_Y": (p1y, None)}
    check(all(abs(a - b) < 0.5 for a, b in spans.values() if b is not None), f"drawn spans agree with the chains {spans}")
    bl011_c = min(p[1] for p in model[PANELS[1]]["points"]) - BEAM_WIDTH_MM / 2      # on its axis (02's y span agrees)
    bl008_c = min(p[1] for p in model[PANELS[0]]["points"]) - BEAM_WIDTH_MM / 2
    bl008_offset = bl011_c - bl008_c
    s6_round = {r["occurrence_id"]: r for r in s6 if r["sheet"] == SHEET}
    beams_here = sorted({e["support_ref"] for m_ in model.values() for e in m_["edges"] if e["support"] == "BEAM"})
    beam_occ = {b: sorted(o for o, r in s6_round.items() if f"-{b}-" in o or o.startswith(f"SPAN:{SHEET}:{b}:"))
                for b in beams_here}
    widths = {o: (s6_round[o]["drawn_width_mm"], s6_round[o]["schedule_width_mm"], s6_round[o]["width_match_state"])
              for b in beams_here for o in beam_occ[b] if s6_round[o]["drawn_width_mm"]}
    check(widths and all(w == ("200", "200", "MATCH") for w in widths.values()), "the framing beams are 200 wide")

    # ------------------------------------------------------------ concrete
    conc = []
    for pid in PANELS:
        a = model[pid]["area_mm2"] / 1e6
        ex_beams = sorted({e["support_ref"] for e in model[pid]["edges"] if e["support"] == "BEAM"})
        ex_cols = sorted({c for e in model[pid]["edges"] for c in e["column"]} |
                         {e["support_ref"].split(":")[-1] for e in model[pid]["edges"] if e["support"] == "COLUMN"})
        conc.append({"ITEM_ID": f"S8.4-C-{SHORT[pid]}", "PANEL_ID": pid, "PARENT": PARENT, "NET_AREA_M2": _r(a),
                     "THICKNESS_MM": 180, "VOLUME_M3": _r(a * 0.18), "FORMULA": f"{_full(a)} m2 x 0.180 m",
                     "LANE": PROJECT_BASIS_QTO, "RELEASED": True,
                     "THICKNESS_AUTHORITY": f"PROJECT_SOURCE (circled T 18 tag {tags_in[pid][0]['letter']['handle']} in "
                                            "this panel; the 't' thickness-tag convention)",
                     "PLAN_AUTHORITY": "PROJECT_GEOMETRY (beam and column faces as drawn; the x spans agree with the "
                                       "printed axis chain less the scheduled 200 mm beam width"
                                       + ("; the y span depends on beam BL008's drawn offset from its axis)"
                                          if pid == PANELS[0] else "; so does the y span between the two axes)"),
                     "EXCLUDED": f"beam bands {ex_beams} (200 mm, full depth, with the beams) and columns {ex_cols}; "
                                 "no opening drawn",
                     "MEASUREMENT_ORIGIN": "face to face of the supporting beams and columns",
                     "WHY_NOT_PHYSICAL": "the sheet asks for stated dimensions, not scale; the panel faces are drawn, "
                                         "not dimensioned (VR-S8.4-02)"})
    for k in ("TANK_BASE", "TANK_WALLS"):
        conc.append({"ITEM_ID": f"S8.4-C-{k}", "PANEL_ID": "", "PARENT": PARENT, "NET_AREA_M2": None,
                     "THICKNESS_MM": None, "VOLUME_M3": None, "FORMULA": "", "LANE": NOT_IN_SOURCE, "RELEASED": False,
                     "THICKNESS_AUTHORITY": "", "PLAN_AUTHORITY": "", "EXCLUDED": "",
                     "MEASUREMENT_ORIGIN": "", "WHY_NOT_PHYSICAL": f"{absent[k]} is not drawn anywhere; not invented"})

    # ------------------------------------------------------------ reinforcement
    bars, bands_out, stop_rows = [], [], []
    comp_of = {(c["OWNER"], c["BAR_ROLE"]): cid for cid, c in comps.items()
               if c["OWNER"] in PANELS and c["BAR_ROLE"] in ("BOTTOM_X", "TOP_X", "BOTTOM_Y", "TOP_Y")}
    s7b_of = {r["COMPONENT_ID"]: r["S7_BLOCKED_ID"] for r in s7_blocked if r["ITEM"] == "TRANSFERRED_FAMILY"}
    for c in calls:
        pid, d = c["panel"], c["direction"]
        pts, cls = model[pid]["points"], model[pid]["classes"]
        n, dia = c["parsed"]["count"], c["parsed"]["dia_mm"]
        for layer in (M.BOTTOM, M.TOP):
            q = M.layer_quantity(pts, d, n, dia, cls, stop=STOP_RULE if layer == M.BOTTOM else None)
            fid = f"S8.4-R-{SHORT[pid]}-{d}-{layer[0]}"
            cid = comp_of[(pid, f"{layer}_{d}")]
            stop_kg = q["stop_zone_kg"]
            ends = sorted({(z["edge"], z["class"]) for z in q["stop_zones"]})
            bars.append({"ITEM_ID": fid, "PANEL_ID": pid, "PARENT": PARENT, "CALLOUT": c["handle"],
                         "QUALIFIER": c["qualifiers"][0], "GRAPHIC": c["graphic"]["handles"],
                         "RAW": f"{c['raw']} (T&B)", "DIA_MM": dia, "RATE_PER_M": n, "SPACING_MM": _r(1000.0 / n, 3),
                         "DIRECTION": d, "BARS_RUN_ALONG": d.lower(), "DISTRIBUTED_ACROSS": "y" if d == M.X else "x",
                         "LAYER": layer, "LAYER_AUTHORITY": f"PROJECT_SOURCE ('(T&B)' {c['qualifiers'][0]}: top and "
                                                            "bottom; the direction comes from the callout's own bar)",
                         "BAND_COUNT": len(q["bands"]), "DISTRIBUTION_WIDTH_M": _r(q["distribution_width_m"]),
                         "EQUIVALENT_COUNT_UNROUNDED": _r(q["equivalent_count"]), "MEAN_RUN_M": _r(q["mean_run_m"]),
                         "STRIP_INTEGRAL_M2": _r(q["area_m2"]), "PANEL_AREA_M2": _r(model[pid]["area_mm2"] / 1e6),
                         "FULL_LENGTH_M": _r(q["full_m"]), "STOP_ZONE_LENGTH_M": _r(q["stop_zone_m"]),
                         "RELEASED_LENGTH_M": _r(q["released_m"]), "UNIT_MASS_KG_M": _r(um[dia]),
                         "RELEASED_KG": _r(q["released_m"] * um[dia]), "STOP_ZONE_KG": _r(q["stop_zone_m"] * um[dia]),
                         "LANE": PROJECT_BASIS_QTO, "RELEASED": True, "COUNT_BASIS": "RATE_DENSITY",
                         "PHYSICAL_BBS_COUNT": "UNRESOLVED",
                         "RUN_BASIS": "face to face of the supporting beams / columns (PROJECT_GEOMETRY)",
                         "STOP_ZONE_STATE": (f"BLOCKED_UNQUANTIFIED ({STOP_RULE['rule']}: 50 % of bottom bars stop "
                                             f"0.125 L short of a continuous support; ends {ends}; whether the typical "
                                             "detail governs a (T&B) tank slab, and the continuity, are open: "
                                             "Q-S8.4-02, Q-S8.4-06)") if q["stop_zones"] else
                                            ("NONE (no continuous end)" if layer == M.BOTTOM else
                                             "NOT_APPLICABLE (the typical detail curtails bottom bars only)"),
                         "ANCHORAGE": "BLOCKED (portion beyond each face: no hook, leg or development detail)",
                         "LAP": "NONE_DRAWN (runs 2.45-3.3 m face to face; continuity over the beams blocked)",
                         "FABRICATION": "BBS count UNRESOLVED (equivalent count unrounded, never +1)",
                         "PRE_S7_COMPONENT": cid, "S7_BLOCKED_ID": s7b_of[cid],
                         "FORMULA": f"{n} /m x {_full(q['area_m2'])} m2 = {_full(q['full_m'])} m"
                                    + (f" - stop zones {_full(q['stop_zone_m'])} m" if q["stop_zones"] else "")
                                    + f"; x {dia}^2/162"})
            for b in q["bands"]:
                ed = {e["index"]: e for e in model[pid]["edges"]}
                bands_out.append({"ROW_ID": f"{fid}-B{b['band']}", "ITEM_ID": fid, "PANEL_ID": pid, "DIRECTION": d,
                                  "LAYER": layer, "T0_MM": _r(b["t0"], 3), "T1_MM": _r(b["t1"], 3),
                                  "WIDTH_MM": _r(b["width_mm"], 3), "RUN_MM": _r(b["integral_mm2"] / b["width_mm"], 3),
                                  "INTEGRAL_M2": _r(b["integral_mm2"] / 1e6),
                                  "START_EDGE": b["start_edge"], "START_SUPPORT": ed[b["start_edge"]]["support_ref"],
                                  "START_CLASS": b["start_class"], "END_EDGE": b["end_edge"],
                                  "END_SUPPORT": ed[b["end_edge"]]["support_ref"], "END_CLASS": b["end_class"],
                                  "FULL_LENGTH_M": _r(n * b["integral_mm2"] / 1e6), "STOP_ZONE_M": _r(b["stop_m"]),
                                  "RELEASED_LENGTH_M": _r(n * b["integral_mm2"] / 1e6 - b["stop_m"])})
            for z in q["stop_zones"]:
                e = model[pid]["edges"][z["edge"]]
                stop_rows.append({"family": fid, "panel": pid, "direction": d, "edge": z["edge"],
                                  "support": e["s7_support"] or e["support_ref"], "beam": e["support_ref"],
                                  "class": z["class"], "length_m": z["length_m"], "kg": z["length_m"] * um[dia]})
    released_kg = math.fsum(b["RELEASED_KG"] for b in bars)
    full_kg = math.fsum(b["FULL_LENGTH_M"] * b["UNIT_MASS_KG_M"] for b in bars)
    stop_kg = math.fsum(z["kg"] for z in stop_rows)
    check(abs(released_kg + stop_kg - full_kg) < 1e-6, "released + stop zones = full mesh")
    check(not any(b["DIA_MM"] == 18 for b in bars), "no T 18 read as a bar")

    # ------------------------------------------------------------ note 2 on the tank side (sensitivity per S7 item)
    edge_of_sup = defaultdict(list)
    for pid in PANELS:
        for e in model[pid]["edges"]:
            if e["s7_support"]:
                edge_of_sup[(e["s7_support"], pid)].append(e["index"])
    note2_rows = {}
    counted_edges = set()
    for r in sorted((x for x in s7_blocked if x["ITEM"] == "TOP_EXTENSION"), key=lambda x: x["S7_BLOCKED_ID"]):
        pid, sup, d = r["SIDE_PANEL"], r["SUPPORT_ID"], r["DIRECTION"]
        edges = edge_of_sup.get((sup, pid), [])
        geom_note = ""
        if not edges:              # S7A G-01: SUP-014's face found beyond is panel 01's edge on the same beam line
            same = [e["index"] for e in model[pid]["edges"] if e["support"] == "BEAM" and e["s1_continuity"] ==
                    "DISCONTINUOUS"]
            edges, geom_note = same, "same physical edge as the S7 support of that panel edge (S7A G-01)"
        new = [i for i in edges if (pid, i) not in counted_edges]
        L = M.edge_zone_length(model[pid]["points"], d, new, NOTE2["ratio"], NOTE2["rate_per_m"]) if new else 0.0
        counted_edges |= {(pid, i) for i in edges}
        note2_rows[r["S7_BLOCKED_ID"]] = {"edges": edges, "length_m": L, "kg": L * um[10], "note": geom_note,
                                          "counted_elsewhere": bool(edges) and not new}
    note2_kg = math.fsum(v["kg"] for v in note2_rows.values())

    # ------------------------------------------------------------ S7 interface
    s7_total = s7_sum["totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"]
    check(s7_total is not None and abs(float(s7_total) - S7_RESTRICTED_KG) < 5e-4, f"S7 total {s7_total}")
    recon = []
    adj_kg = []
    for e in sorted(s7a, key=lambda x: x["STRIP_ID"]):
        runs = [r for r in s7_runs if r["STRIP_ID"] == e["STRIP_ID"] and s7_items[r["S7_ITEM_ID"]]["SUPPORT_ID"] ==
                e["SUPPORT_ID"] and s7_items[r["S7_ITEM_ID"]]["BAR_ROLE"].startswith("TOP")]
        kg = math.fsum(float(r["KG"]) for r in runs)
        check(abs(kg - float(e["S7_TOP_EXTENSION_KG_AT_END"])) < 1e-6, f"{e['STRIP_ID']}: S7A = S7 bar runs")
        check(all(r["PANEL_ID"] not in PANELS for r in runs), f"{e['STRIP_ID']}: the S7 steel lies outside the tank")
        adj_kg.append(kg)
        it = s7_items[runs[0]["S7_ITEM_ID"]]
        recon.append({"ROW_ID": f"S7I-{len(recon) + 1:02d}", "ROW_KIND": "S7_RELEASED_ADJACENT_STRIP_END",
                      "S7_ID": it["S7_ITEM_ID"], "S7_STRIP_OR_COMPONENT": e["STRIP_ID"], "SUPPORT_ID": e["SUPPORT_ID"],
                      "BAR_ROLE": it["BAR_ROLE"], "DIA_MM": it["DIAMETER_MM"], "WHERE": runs[0]["PANEL_ID"],
                      "S7_KG": _r(kg), "S7_STATE": "RELEASED (PROJECT_BASIS_QTO)",
                      "S8_4_TERMINAL": "STAYS_WITH_S7 (not re-added; S8.4 releases nothing on a support)",
                      "S8_4_ROW": "", "OVERLAP": "NONE (the S7 run lies in the non-tank panel; S8.4 runs lie inside "
                                                 "the tank panels, face to face)",
                      "NOTE": f"S7A end {e['END']} of {e['STRIP_ID']}; beyond panel {e['BEYOND_PANEL']}"})
    tank_adj_kg = math.fsum(adj_kg)
    fam_of_comp = {b["PRE_S7_COMPONENT"]: b["ITEM_ID"] for b in bars}
    blocked = []

    def B(bid, obj, comp, where, state, why, question="", sens_kg=None, s7=None, kind="REINFORCEMENT"):
        blocked.append({"BLOCKED_ID": bid, "KIND": kind, "OBJECT": obj, "COMPONENT": comp, "WHERE": where,
                        "STATE": state, "KG": None, "SENSITIVITY_KG": _r(sens_kg) if sens_kg is not None else None,
                        "WHY": why, "QUESTION": question, "S7_ORIGIN": s7 or ""})
    stop_by_edge = defaultdict(list)
    for z in stop_rows:
        stop_by_edge[(z["family"], z["edge"])].append(z)
    for (fam, edge), zs in sorted(stop_by_edge.items()):
        z = zs[0]
        B(f"BL-STOP-{fam[7:]}-E{edge}", z["panel"], f"BOTTOM_STOP_ZONE {z['direction']}",
          f"{z['beam']} ({z['support']}), edge {edge}, {len(zs)} band(s)", BLOCKED,
          f"{STOP_RULE['rule']}: 50 % of bottom bars stop 0.125 L short of a continuous support; edge class "
          f"{z['class']}; applicability to the (T&B) tank slab not stated", "Q-S8.4-02; Q-S8.4-06",
          math.fsum(x["kg"] for x in zs))
    for b in bars:
        B(f"BL-ANCH-{b['ITEM_ID'][7:]}", b["PANEL_ID"], f"END_ANCHORAGE {b['DIRECTION']} {b['LAYER']}",
          "beyond every face of the panel", BLOCKED, "no hook, leg, development length or bend detail for the "
          "(T&B) bars into the edge beams; P8-N09 states starter bars only", "Q-S8.4-04")
    for pid in PANELS:
        B(f"BL-CONT-{SHORT[pid]}", pid, "TOP_AND_BOTTOM_CONTINUITY_OVER_SUPPORTS", "over BL003 and the shared beams",
          BLOCKED, "the two panels carry different families each way (7Ø14 / 6Ø14 against 6Ø12); no continuity, lap "
          "or crossing is drawn over the beams", "Q-S8.4-04")
        B(f"BL-BBS-{SHORT[pid]}", pid, "FABRICATION_COUNT", pid, BLOCKED,
          "equivalent counts are unrounded; whole bars, laps and bar marks are not detailed", "Q-S8.4-04")
    for r in sorted(s7_blocked, key=lambda x: x["S7_BLOCKED_ID"]):
        if r["ITEM"] == "TOP_EXTENSION":
            v = note2_rows[r["S7_BLOCKED_ID"]]
            B(f"BL-NOTE2-{r['S7_BLOCKED_ID']}", r["SIDE_PANEL"], f"NOTE2_TOP_OVER_BEAM {r['DIRECTION']}",
              f"{r['SUPPORT_ID']} tank side, edges {v['edges']}", BLOCKED,
              "plan note 2 (5Ø10/m over beams, 1/3 span both ways) on the tank side: whether it adds to the panel's "
              "own (T&B) top layer is not stated; AD2-D11 makes a local /Top callout override note 2 and never adds "
              "without a second family, but a (T&B) panel callout is not support-bound" +
              (f"; {v['note']}" if v["note"] else "") +
              ("; its length is carried by the other S7 item on the same edge" if v["counted_elsewhere"] else ""),
              "Q-S8.4-03", None if v["counted_elsewhere"] else v["kg"], r["S7_BLOCKED_ID"])
        elif r["ITEM"] == "TEMPERATURE":
            B(f"BL-TEMP-{r['S7_BLOCKED_ID']}", r["OWNER"], f"TEMPERATURE_{r['DIRECTION']}", r["OWNER"], NOT_ADDED,
              "no temperature steel is added: P15-TEMP-TABLE has no 180 mm row (175 / 200 only, no interpolation); "
              "under the typical detail temperature bars sit on the top face outside the top bars, and here the "
              "(T&B) top layer covers the whole face each way; the source states no extra steel", "Q-S8.4-05",
              None, r["S7_BLOCKED_ID"])
    B("BL-NOTE2-CROSSINGS", PARENT, "NOTE2_TOP_ACROSS_THE_BEAMS", "between the faces of the tank-region beams",
      BLOCKED, "top bars across the beam width are the support's; in the tank region note 2's applicability is the "
      "open question Q-S8.4-03", "Q-S8.4-03")
    B("BL-COVER", PARENT, "COVER_AND_EXPOSURE", "both panels", BLOCKED,
      "P8-N22 gives >= 25 mm for slabs; no exposure class or cover for a tank-bearing roof slab is stated; the plan "
      "quantity does not depend on it, the bar positions do", "Q-S8.4-05", kind="DETAILING")
    for k in ("TANK_BASE", "TANK_WALLS", "TANK_LOCAL_REINFORCEMENT", "TANK_OPENINGS"):
        B(f"BL-{k}", k, k, PARENT, NOT_IN_SOURCE, f"{absent[k]}: not drawn, noted or scheduled in either discipline; "
          "a tank's water load is not authority to invent it", "Q-S8.4-01; Q-S8.4-07", kind="STRUCTURE")

    # reconciliation: 22 S7 blocked items and 33 PRE-S7.1 transfers, each to one S8.4 terminal
    bl_ids = {b["BLOCKED_ID"] for b in blocked}
    for r in sorted(s7_blocked, key=lambda x: x["S7_BLOCKED_ID"]):
        if r["ITEM"] == "TRANSFERRED_FAMILY":
            term, row = "RELEASED_S8_4", fam_of_comp[r["COMPONENT_ID"]]
        elif r["ITEM"] == "TOP_EXTENSION":
            term, row = "BLOCKED_S8_4 (sensitivity only)", f"BL-NOTE2-{r['S7_BLOCKED_ID']}"
        else:
            term, row = "NOT_ADDED_S8_4", f"BL-TEMP-{r['S7_BLOCKED_ID']}"
        recon.append({"ROW_ID": f"EX-{r['S7_BLOCKED_ID']}", "ROW_KIND": "S7_EXCLUDED_ITEM", "S7_ID": r["S7_BLOCKED_ID"],
                      "S7_STRIP_OR_COMPONENT": r["COMPONENT_ID"], "SUPPORT_ID": r["SUPPORT_ID"], "BAR_ROLE": r["ITEM"],
                      "DIA_MM": r["DIA_MM"], "WHERE": r["SIDE_PANEL"] or r["OWNER"], "S7_KG": None,
                      "S7_STATE": r["S7_LANE"], "S8_4_TERMINAL": term, "S8_4_ROW": row, "OVERLAP": "NONE",
                      "NOTE": f"S7 category {r['CATEGORY']}"})
    for t in sorted(transfers, key=lambda x: x["TRANSFER_ID"]):
        oid, kind = t["object_id"], t["kind"]
        if kind == "PANEL":
            term, row = "RELEASED_S8_4", [f"S8.4-C-{SHORT[oid]}"] + [b["ITEM_ID"] for b in bars if b["PANEL_ID"] == oid]
        elif kind == "TOKEN":
            h = oid.split()[1]
            fam = [b["ITEM_ID"] for b in bars if h in (b["CALLOUT"], b["QUALIFIER"])]
            term, row = "RELEASED_S8_4", fam
        elif kind == "THICKNESS_MARK":
            h = re.search(r"\(([0-9A-F]+)\)", oid).group(1)
            term, row = "RELEASED_S8_4", [c["ITEM_ID"] for c in conc if c["PANEL_ID"] and
                                          tags_in[c["PANEL_ID"]][0]["letter"]["handle"] == h]
        elif kind.startswith("COMPONENT") and oid in fam_of_comp:
            term, row = "RELEASED_S8_4", [fam_of_comp[oid]]
        elif kind.startswith("COMPONENT TEMPERATURE"):
            s7b = [r["S7_BLOCKED_ID"] for r in s7_blocked if r["COMPONENT_ID"] == oid]
            term, row = "NOT_ADDED_S8_4", [f"BL-TEMP-{x}" for x in s7b]
        else:                                   # support top components and tank-side top-extension items
            s7b = [r["S7_BLOCKED_ID"] for r in s7_blocked if r["ITEM"] == "TOP_EXTENSION" and
                   (r["COMPONENT_ID"] == oid or (kind == "ITEM TOP_EXTENSION" and
                                                 r["SUPPORT_ID"] in t["reason"] and r["SIDE_PANEL"] in t["reason"]))]
            term, row = "BLOCKED_S8_4 (sensitivity only)", [f"BL-NOTE2-{x}" for x in s7b]
        check(row and all(x in bl_ids or x in {b["ITEM_ID"] for b in bars} or x in {c["ITEM_ID"] for c in conc}
                          for x in row), f"{t['TRANSFER_ID']} ({oid}) lands on S8.4 rows: {row}")
        recon.append({"ROW_ID": t["TRANSFER_ID"], "ROW_KIND": "PRE_S7_1_TRANSFER", "S7_ID": "",
                      "S7_STRIP_OR_COMPONENT": oid, "SUPPORT_ID": "", "BAR_ROLE": kind, "DIA_MM": "", "WHERE": t["reason"],
                      "S7_KG": None, "S7_STATE": t["state"], "S8_4_TERMINAL": term, "S8_4_ROW": row, "OVERLAP": "NONE",
                      "NOTE": f"from {t['from_stage']} ({t['region']})"})

    for name, ids in (("blocked", [b["BLOCKED_ID"] for b in blocked]), ("reconciliation", [r["ROW_ID"] for r in recon]),
                      ("families", [b["ITEM_ID"] for b in bars])):
        check(len(ids) == len(set(ids)), f"{name} ids are unique: {[k for k, v in Counter(ids).items() if v > 1]}")

    # ------------------------------------------------------------ conflicts and questions
    g_bad = [c for c in calls if not c["s1_graphic_ok"]]
    cq = [
        {"ID": "CF-S8.4-01", "KIND": "SOURCE_CONFLICT", "STATE": "RECORDED (S1 not edited; no quantity effect)",
         "TEXT": "S1 binds " + "; ".join(f"{c['handle']} to bar graphic {c['s1']['bar_graphic_handle']}" for c in g_bad) +
                 ", which are other callouts' bars; S8.4 binds " +
                 "; ".join(f"{c['handle']} to {c['graphic']['handles']}" for c in g_bad) +
                 ". S1's directions, diameters, rates and (T&B) bindings agree with S8.4.", "AFFECTS": "provenance only"},
        {"ID": "CF-S8.4-02", "KIND": "SOURCE_CONFLICT", "STATE": "OPEN (no quantity depends on it)",
         "TEXT": "the cloud is a scalloped marker over both panels and the beam between them; it does not follow the "
                 "panel faces and is not dimensioned: no tank footprint, position or support points are given",
         "AFFECTS": "tank loads and any local reinforcement (blocked)"},
        {"ID": "CF-S8.4-03", "KIND": "SOURCE_CONFLICT", "STATE": "OPEN (no quantity depends on it)",
         "TEXT": "architecture names no tank and has no roof plan of the +13.90 tower roof; section A-A shows one "
                 "unlabelled element in view at parapet height (VR-S8.4-04), section B-B and the elevations none",
         "AFFECTS": "whether a tank structure exists above the slab"},
        {"ID": "CF-S8.4-04", "KIND": "SOURCE_CONFLICT", "STATE": pre7c["C-05"]["STATE"],
         "TEXT": f"PRE-S7 C-05 carried: {pre7c['C-05']['EVIDENCE']}", "AFFECTS": "thickness (resolved: 180 in the two "
                 "panels only)"},
        {"ID": "CF-S8.4-05", "KIND": "SOURCE_CONFLICT", "STATE": "RESOLVED_FOR_OWNERSHIP (AD2-D08); engineer "
                                                                  "confirmation open (Q-S8.4-01)",
         "TEXT": f"PRE-S7 C-07 / {pre7q['Q-TANK']['QUESTION_ID']} (normal roof slab or water-tank structure): the source "
                 "draws two slab panels on beams, thicker and doubly reinforced, under a 'WATER TANK PLACE' cloud, and "
                 "no tank member; S8.4 owns and measures them as the roof slab designated for the tank",
         "AFFECTS": "classification"},
        {"ID": "CF-S8.4-06", "KIND": "SOURCE_CONFLICT", "STATE": "OPEN (PROJECT_BASIS lane)",
         "TEXT": "the legend asks for stated dimensions, not scale; the x spans and panel 02's y span follow from the "
                 "printed axis chains less the scheduled 200 mm beams, but panel 01's "
                 f"{_full(spans['01_Y'][0] / 1000, 3)} m y span depends on beam BL008, drawn {bl008_offset:.0f} mm "
                 "off the axis that carries BL011, which no dimension states",
         "AFFECTS": "panel 01 area, concrete and mesh (drawn geometry)"},
        {"ID": "CF-S8.4-07", "KIND": "SOURCE_CONFLICT", "STATE": "OPEN (stop zones blocked)",
         "TEXT": "S1 reads the panel edges on BL008, BL011 and BL002 as CONTINUOUS; AD2 (S7) leaves those supports "
                 "CONTINUITY_UNRESOLVED because the tank panels were special; S7A G-01 finds 100 mm of panel 03 "
                 "beyond panel 01's 0.30 m edge across column 421",
         "AFFECTS": "bottom stop zones (blocked) and note-2 sensitivity"},
        {"ID": "Q-S8.4-01", "KIND": "QUESTION", "STATE": "OPEN", "AFFECTS": "population",
         "TEXT": "Engineer: are the two T 18 panels the slab that carries the tank directly, or is there a tank base, "
                 "plinth or RC tank (walls, cover slab)? If so, issue its drawings."},
        {"ID": "Q-S8.4-02", "KIND": "QUESTION", "STATE": "OPEN", "AFFECTS": f"{_full(stop_kg, 6)} kg blocked",
         "TEXT": "Engineer: does the typical slab-on-beams curtailment (50 % of bottom bars stop 0.125 L short of a "
                 "continuous support) apply to the (T&B) mesh of the tank panels, or do all bars run through?"},
        {"ID": "Q-S8.4-03", "KIND": "QUESTION", "STATE": "OPEN", "AFFECTS": f"{_full(note2_kg, 6)} kg sensitivity",
         "TEXT": "Engineer: does plan note 2 (5Ø10/m over beams, 1/3 span) also apply on the tank side, in addition "
                 "to the (T&B) top layer?"},
        {"ID": "Q-S8.4-04", "KIND": "QUESTION", "STATE": "OPEN", "AFFECTS": "anchorage, continuity, laps, BBS",
         "TEXT": "Engineer: anchorage of the top and bottom bars into the edge beams, continuity or laps over BL003 "
                 "(7Ø14 / 6Ø14 against 6Ø12), and the bar marks for a BBS."},
        {"ID": "Q-S8.4-05", "KIND": "QUESTION", "STATE": "OPEN", "AFFECTS": "temperature steel, cover",
         "TEXT": "Engineer: confirm no temperature steel in a (T&B) panel (the table has no 180 mm row) and give the "
                 "cover / exposure for a tank-bearing roof slab (P8-N22 states >= 25 mm)."},
        {"ID": "Q-S8.4-06", "KIND": "QUESTION", "STATE": "OPEN", "AFFECTS": "stop zones",
         "TEXT": "Engineer: continuity of the tank panels with panels 06, 03 and 04 over BL008, BL011 and BL002 "
                 "(same 180 / 160 mm level?), and at column 421 (S7A G-01)."},
        {"ID": "Q-S8.4-07", "KIND": "QUESTION", "STATE": "OPEN", "AFFECTS": "local reinforcement",
         "TEXT": "Engineer / architect: tank type, capacity, footprint, support points and any upstand, curb or "
                 "dowels; architecture shows no tank and no tower-roof plan."},
        {"ID": "Q-S8.4-08", "KIND": "QUESTION", "STATE": "OPEN", "AFFECTS": "panel 01 y span",
         "TEXT": f"Engineer: dimension beam BL008's position (drawn {bl008_offset:.0f} mm off the axis of BL011)."}]

    # ------------------------------------------------------------ interfaces
    inter = []

    def I(iid, a, b, conc_, bars_, state):
        inter.append({"INTERFACE_ID": iid, "SIDE_A": a, "SIDE_B": b, "CONCRETE": conc_, "BARS": bars_, "STATE": state})
    for bm in beams_here:
        I(f"IF-BEAM-{bm}", "S8.4 tank panels (face to face)", f"beam line {bm}: S6 occurrences {beam_occ[bm]}",
          "slab measured to the beam faces; the 200 mm beam band keeps its full depth with the beams (no stage has "
          "released beam concrete; a later beam measure must take the full depth or add the slab zone over the beam)",
          "beam bars stay S6 (frozen); S8.4 releases no beam bar and no bar beyond a face", "OWNED_ONCE")
    cols_here = sorted({c for m_ in model.values() for e in m_["edges"] for c in e["column"]} |
                       {e["support_ref"].split(":")[-1] for m_ in model.values() for e in m_["edges"]
                        if e["support"] == "COLUMN"})
    I("IF-COLUMNS", "S8.4 tank panels", f"columns {cols_here} (S3.1)", "slab measured to the column faces (panel 01's "
      "50 x 300 notch is column 424)", "column bars stay S3.1", "OWNED_ONCE")
    I("IF-S7-SUPPORT-TOP", "S8.4 tank panels", "S7 note-2 top extensions at SUP-008 / 014 / 059 / 073",
      "none", f"{_full(tank_adj_kg, 9)} kg released by S7 on the non-tank sides (10 strip ends): stays S7, never "
      "re-added; the tank-side note-2 steel is blocked in S8.4 (sensitivity only)", "OWNED_ONCE")
    I("IF-S7-PANELS", "S8.4 tank panels", "S7 panels 03, 04, 06 (bottom mesh, note-2 tops)", "none (no S7 concrete)",
      "S7 strips end at their own faces; S8.4 strips lie inside the tank panels; disjoint", "OWNED_ONCE")
    I("IF-S8.3", "S8.4 tank panels", "S8.3 domes (1F roof) and the architectural-only tower dome over panel 04",
      "S8.3 released concrete is the two terrace shells on the 1F roof; the tower dome is not quantified",
      "S8.3 mesh is on the terrace shells; nothing on the 2F roof", "NO_OVERLAP")
    I("IF-TANK", "tank slab (S8.4)", "tank base / walls / equipment", "not in the source", "not in the source",
      "NOT_IN_SOURCE")

    # ------------------------------------------------------------ sensitivity
    by_dia = defaultdict(float)
    for b in bars:
        by_dia[b["DIA_MM"]] += b["RELEASED_KG"]
    bl003_only = math.fsum(z["kg"] for z in stop_rows if z["class"] != "CONTINUOUS")
    whole = []
    for b in bars:
        n_whole = math.ceil(b["EQUIVALENT_COUNT_UNROUNDED"] - 1e-9)
        whole.append(n_whole * b["MEAN_RUN_M"] * b["UNIT_MASS_KG_M"])
    sens = [
        {"CASE_ID": "SA-01", "LANE": SENS, "CASE": "bottom bars run face to face with no stop zone (the typical "
                                                   "curtailment does not govern the (T&B) slab)",
         "KG": _r(released_kg + stop_kg), "DELTA_KG": _r(stop_kg), "BASIS": "released + every bottom stop zone"},
        {"CASE_ID": "SA-02", "LANE": SENS, "CASE": "stop zones only at the resolved continuous support (BL003 "
                                                   "between the two panels); unresolved ends run through",
         "KG": _r(released_kg + bl003_only), "DELTA_KG": _r(bl003_only), "BASIS": "released + unresolved-end stop zones"},
        {"CASE_ID": "SA-03", "LANE": SENS, "CASE": "plan note 2 also applies on the tank side (5Ø10/m, 1/3 local "
                                                   "span from each beam face), additive to the (T&B) top layer",
         "KG": _r(released_kg + note2_kg), "DELTA_KG": _r(note2_kg), "BASIS": "released + note-2 tank-side lengths"},
        {"CASE_ID": "SA-04", "LANE": SENS, "CASE": "whole bars: each family's equivalent count rounded up, at its mean "
                                                   "run, full length (a fabrication view, not a BBS)",
         "KG": _r(math.fsum(whole)), "DELTA_KG": _r(math.fsum(whole) - released_kg), "BASIS": "ceil(count) x mean run"}]

    # ------------------------------------------------------------ conservation
    cons = []

    def A(cid, text, ok, detail=""):
        cons.append({"CHECK_ID": cid, "CHECK": text, "RESULT": "PASS" if ok else "FAIL", "DETAIL": detail})
    A("K-01", "every frozen stage (S4-S8.3A, PRE-S7-PRE-S8) and the S8.3 errata verify before and after",
      len(frozen) == len(MANIFESTS) and len(errata) == 3, f"{len(frozen)} manifests, {len(errata)} errata files")
    A("K-02", "S7 stays 3,802.015 kg", abs(float(s7_total) - S7_RESTRICTED_KG) < 5e-4, f"{s7_total}")
    A("K-03", "the ~20.1 kg of S7 top steel at the tank edges is traced by unique id and stays S7",
      len(adj_kg) == 10 and abs(tank_adj_kg - 20.087448558) < 1e-6,
      f"{_full(tank_adj_kg)} kg over {len(adj_kg)} strip ends, items "
      f"{sorted({r['S7_ID'] for r in recon if r['ROW_KIND'] == 'S7_RELEASED_ADJACENT_STRIP_END'})}")
    A("K-04", "S8.4 releases nothing on a support and nothing beyond a panel face",
      all(b["RUN_BASIS"].startswith("face to face") for b in bars) and not any("SUP-" in b["ITEM_ID"] for b in bars),
      "all eight families run face to face inside the panels")
    A("K-05", "every one of the 22 S7 items excluded to the tank region has exactly one S8.4 terminal",
      len(s7_blocked) == 22 and Counter(r["S7_ID"] for r in recon if r["ROW_KIND"] == "S7_EXCLUDED_ITEM") ==
      Counter(r["S7_BLOCKED_ID"] for r in s7_blocked), f"{len(s7_blocked)} items")
    A("K-06", "every one of the 33 PRE-S7.1 transfers to the region has an S8.4 terminal", len(transfers) == 33 and
      all(r["S8_4_ROW"] for r in recon if r["ROW_KIND"] == "PRE_S7_1_TRANSFER"), f"{len(transfers)} transfers")
    A("K-07", "the 12 PRE-S7 panel components (8 mesh + 4 temperature) all terminate",
      sorted(fam_of_comp) == sorted(c for c in comps if comps[c]["OWNER"] in PANELS and comps[c]["BAR_ROLE"] in
                                    ("BOTTOM_X", "TOP_X", "BOTTOM_Y", "TOP_Y")) and
      sum(1 for b in blocked if b["BLOCKED_ID"].startswith("BL-TEMP-")) == 4, f"{sorted(fam_of_comp)}")
    A("K-08", "two panels, one parent; the parent carries no quantity; each panel is counted once",
      [p["OBJECT"] for p in pop if p["ROW_KIND"] == "PHYSICAL_SLAB_PANEL"] == list(PANELS) and
      sorted(START_POPULATION) == sorted(p["OBJECT"] for p in pop if p["ROW_KIND"] in ("PHYSICAL_SLAB_PANEL",
                                                                                         "USE_ZONE_PARENT")),
      f"cloud encloses {in_cloud}")
    A("K-09", "each layer's strips cover its panel exactly and released + stop zones = full",
      all(abs(b["STRIP_INTEGRAL_M2"] - b["PANEL_AREA_M2"]) < 1e-9 and
          abs(b["RELEASED_LENGTH_M"] + b["STOP_ZONE_LENGTH_M"] - b["FULL_LENGTH_M"]) < 1e-9 for b in bars),
      f"{len(bars)} families")
    A("K-10", "(T&B) gives two faces per callout; directions come from the callouts' own bars, never from (T&B)",
      Counter((b["PANEL_ID"], b["DIRECTION"]) for b in bars) == Counter({(p, d): 2 for p in PANELS
                                                                          for d in M.DIRECTIONS}),
      "4 callouts x 2 faces = 8 families")
    A("K-11", "T 18 is a thickness: no Ø18 family, both tags inside their panels and nowhere else on the sheet",
      not any(b["DIA_MM"] == 18 for b in bars) and len(st["tags"]) == 2, f"tags {[t['circle'] for t in st['tags']]}")
    A("K-12", "every panel edge lies on drawn beam-face or column linework; the panels do not overlap",
      all(e["drawn_lines"] or e["column"] for m_ in model.values() for e in m_["edges"]) and
      not _pip(_centroid(model[PANELS[0]]["points"]), model[PANELS[1]]["points"]), "")
    A("K-13", "the S7 adjacent steel lies in S7 panels only", all(r["WHERE"] not in PANELS for r in recon
                                                                  if r["ROW_KIND"] == "S7_RELEASED_ADJACENT_STRIP_END"),
      "03 / 04 / 06")
    A("K-14", "no other S8 stage released a quantity in the two panels",
      all("SFRS" not in json.dumps(x) for x in s83["released"].values()) and
      all(s7_panels[p]["RELEASED_ITEMS_OWNED"] == "0" for p in PANELS), "S8.3 releases on the 1F roof only")
    A("K-15", "the framing beams keep their S6 occurrences (S6 frozen; S8.4 adds no beam quantity)",
      all(beam_occ[b] for b in beams_here), f"{beam_occ}")
    A("K-16", "no tank member, base or wall is invented",
      all(c["VOLUME_M3"] is None for c in conc if not c["RELEASED"]) and len(st["tank_hits"]) == 1 and
      not arch["tank_hits"], f"structural tank texts {st['tank_hits']}; architectural {arch['tank_hits']}")
    A("K-17", "no client drawing, render or crop in the package",
      not [p for p in HERE.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf", ".dxf", ".dwg")], "")
    check(all(c["RESULT"] == "PASS" for c in cons), "; ".join(f"{c['CHECK_ID']} {c['DETAIL']}" for c in cons
                                                             if c["RESULT"] != "PASS"))

    # ------------------------------------------------------------ source register
    srcreg = source_register(st, arch, calls, tags_in, model, ref, rules)
    for did in ("AD2-D08", "AD2-D11"):
        d_ = ad2[did]
        srcreg.append({"SOURCE_ID": did, "KIND": "FROZEN_DECISION", "FILE": str(READ["PRE71_AD2"].relative_to(ROOT)),
                       "PAGE": "", "HANDLES": [], "LAYER": "", "RAW": d_["decision"], "ROLE": d_["name"],
                       "EVIDENCE": "ownership of the region (D08); a local top callout never adds to note 2 without a "
                                   "second family (D11), applied here only as a sensitivity bound" if did == "AD2-D11"
                                   else "ownership of the region: S7 -> S8 special structure, nothing lost"})

    # ------------------------------------------------------------ write
    for o in OUTPUTS + [MANIFEST_NAME]:
        if (HERE / o).exists():
            (HERE / o).unlink()
    _csv(OUTPUTS[1], srcreg)
    _csv(OUTPUTS[2], pop)
    _csv(OUTPUTS[3], thick_rows)
    _csv(OUTPUTS[4], conc)
    _csv(OUTPUTS[5], bars)
    _csv(OUTPUTS[6], bands_out)
    _csv(OUTPUTS[7], recon)
    _csv(OUTPUTS[8], blocked)
    _csv(OUTPUTS[9], cq, ["ID", "KIND", "STATE", "TEXT", "AFFECTS"])
    _csv(OUTPUTS[10], inter)
    _csv(OUTPUTS[11], sens)
    _csv(OUTPUTS[12], cons)
    prov = [{"record": r["SOURCE_ID"], "output": OUTPUTS[1], "handles": r["HANDLES"], "file": r["FILE"],
             "page": r["PAGE"]} for r in srcreg]
    prov += [{"record": r["ROW_ID"], "output": OUTPUTS[2], "handles": r["HANDLES"], "drawing_sha256": STRUCT_SHA}
             for r in pop if r["HANDLES"]]
    prov += [{"record": r["ITEM_ID"], "output": OUTPUTS[4], "panel": r["PANEL_ID"], "drawing_sha256": STRUCT_SHA}
             for r in conc if r["RELEASED"]]
    prov += [{"record": r["ITEM_ID"], "output": OUTPUTS[5], "callout": r["CALLOUT"], "qualifier": r["QUALIFIER"],
              "graphic": r["GRAPHIC"], "pre_s7_component": r["PRE_S7_COMPONENT"], "drawing_sha256": STRUCT_SHA}
             for r in bars]
    prov += [{"record": v["ID"], "output": OUTPUTS[1], "file": v["FILE"], "page": v["PAGE"], "dpi": v["DPI"],
              "box_px": v["BOX_PX"], "kept_in_git": False} for v in VISUAL]
    (HERE / OUTPUTS[13]).write_text("".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in prov),
                                    encoding="utf-8")
    released_m3 = math.fsum(c["VOLUME_M3"] for c in conc if c["RELEASED"])
    summary = {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "starting_population": list(START_POPULATION),
        "confirmed_physical_elements": {"slab_panels": list(PANELS), "use_zone_parent": PARENT,
                                        "class": "ROOF_SLAB_DESIGNATED_FOR_A_TANK",
                                        "tank_base": NOT_IN_SOURCE, "tank_walls": NOT_IN_SOURCE},
        "panel_area_m2": {pid: _r(model[pid]["area_mm2"] / 1e6) for pid in PANELS},
        "thickness_mm": {pid: 180 for pid in PANELS},
        "released": {"concrete_m3": _r(released_m3), "reinforcement_kg": _r(released_kg),
                     "concrete_items": [c["ITEM_ID"] for c in conc if c["RELEASED"]],
                     "reinforcement_items": [b["ITEM_ID"] for b in bars], "lane": PROJECT_BASIS_QTO},
        "by_panel": {pid: {"concrete_m3": _r(math.fsum(c["VOLUME_M3"] for c in conc if c["PANEL_ID"] == pid)),
                           "reinforcement_kg": _r(math.fsum(b["RELEASED_KG"] for b in bars if b["PANEL_ID"] == pid))}
                     for pid in PANELS},
        "by_diameter_kg": {str(k): _r(v) for k, v in sorted(by_dia.items())},
        "by_family_kg": {b["ITEM_ID"]: _r(b["RELEASED_KG"]) for b in bars},
        "by_direction_layer_kg": {f"{d}_{l}": _r(math.fsum(b["RELEASED_KG"] for b in bars if b["DIRECTION"] == d and
                                                           b["LAYER"] == l))
                                  for d in M.DIRECTIONS for l in (M.BOTTOM, M.TOP)},
        "blocked_stop_zone_kg": _r(stop_kg), "full_mesh_kg": _r(full_kg),
        "note2_tank_side_sensitivity_kg": _r(note2_kg),
        "s7": {"restricted_kg": float(s7_total), "tank_adjacent_released_kg": _r(tank_adj_kg),
               "tank_adjacent_items": sorted({r["S7_ID"] for r in recon if r["ROW_KIND"] ==
                                              "S7_RELEASED_ADJACENT_STRIP_END"}),
               "excluded_items_terminated": len(s7_blocked), "transfers_terminated": len(transfers),
               "state": "UNCHANGED; adjacent steel stays S7"},
        "lanes": {"concrete": dict(sorted(Counter(c["LANE"] for c in conc).items())),
                  "reinforcement": dict(sorted(Counter(b["LANE"] for b in bars).items())),
                  "blocked": dict(sorted(Counter(b["STATE"] for b in blocked).items()))},
        "conflicts": [r["ID"] for r in cq if r["KIND"] == "SOURCE_CONFLICT"],
        "questions": [r["ID"] for r in cq if r["KIND"] == "QUESTION"],
        "sensitivity": {r["CASE_ID"]: r["KG"] for r in sens},
        "conservation": {c["CHECK_ID"]: c["RESULT"] for c in cons},
        "frozen_baselines": {k: v["manifest_sha256"] for k, v in frozen.items()},
        "s8_3_errata_sha256": errata,
        "unit_mass": UM.describe(UNIT_MASS), "references_read": []}
    _json(OUTPUTS[14], summary)
    (HERE / OUTPUTS[0]).write_text(readme(summary, conc, bars, blocked, cq, sens), encoding="utf-8")
    manifest = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "FROZEN_BEFORE_COMPARISON",
                "engine_commit_stamp": summary["engine_commit"], "references_read": [],
                "code": {c: _sha(ROOT / c) for c in CODE},
                "inputs": {str(p.relative_to(ROOT)): _sha(p) for p in READ.values()},
                "drawing_sha256": {"ST7757.dxf": STRUCT_SHA, "P7757.dxf": ARCH_SHA, "ST7757.pdf": STRUCT_PDF_SHA,
                                   **SET_PARTS},
                "frozen_baselines": summary["frozen_baselines"], "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
                "released": summary["released"],
                "rule": "frozen before any earlier Urban, contractor or third-party figure is read; the comparison "
                        "after it explains differences and never changes a frozen quantity"}
    _json(MANIFEST_NAME, manifest)
    # every frozen stage still verifies after the write
    for k, m in MANIFESTS.items():
        DR.verify_frozen(m, ROOT)
    return summary


def source_register(st, arch, calls, tags_in, model, ref, rules):
    man = {o["sha256"]: o for o in _j(READ["SOURCE_MANIFEST"])["files"] if isinstance(o, dict) and o.get("sha256")}
    rows = []

    def add(sid, kind, file, page, handles, layer, raw, role, evidence):
        rows.append({"SOURCE_ID": sid, "KIND": kind, "FILE": file, "PAGE": page, "HANDLES": handles, "LAYER": layer,
                     "RAW": raw, "ROLE": role, "EVIDENCE": evidence})
    add("SRC-01", "FILE", "ST7757.dxf", "1-7", [], "", STRUCT_SHA, "STRUCTURAL_AUTHORITY",
        f"registered {STRUCT_SHA in man}; p.6 plan read entity by entity; p.1 axis chains; t blocks on p.4 / p.5")
    add("SRC-02", "FILE", "ST7757.pdf", "1-15", [], "", STRUCT_PDF_SHA, "PLOT_OF_SRC-01 + PAGES_8-15",
        f"registered {STRUCT_PDF_SHA in man}; visual records only (the p.6 legend and p.8-15 exist only as plots)")
    add("SRC-03", "FILE", "P7757.dxf", "all", [], "", ARCH_SHA, "ARCHITECTURAL_EVIDENCE",
        f"registered {ARCH_SHA in man}; {arch['texts']} texts read ({arch['decoded_legacy']} legacy Arabic decoded); "
        f"tank words found: {len(arch['tank_hits'])}")
    for i, (k, s) in enumerate(SET_PARTS.items(), 4):
        add(f"SRC-0{i}", "FILE", f"{SET_KEY} {k}", "1-6", [], "", s, "ARCHITECTURAL_EVIDENCE (visual records)",
            "sections, elevations and the plan list; additional evidence of the registered set")
    sh = f"ST7757 p.{st['sheet_info']['pdf_page']} {SHEET}"
    n = st["note"]
    add("A-01", "ANNOTATION", sh, 6, [n["handle"]], n["layer"], n["text"], "USE_ZONE_NOTE",
        "the only tank word in the structural drawing")
    add("A-02", "ANNOTATION", sh, 6, list(LEADER_H), st["leader"][0]["layer"], "leader", "NOTE_TO_ZONE",
        "two lines from the note's baseline to the cloud's top edge")
    add("A-03", "ANNOTATION", sh, 6, [CLOUD_H], st["cloud"]["layer"], f"cloud, {len(st['cloud']['pts'])} bulged vertices",
        "USE_ZONE_EXTENT (graphic)", "encloses both panels and the B3 band between them; not dimensioned")
    for pid in PANELS:
        t = tags_in[pid][0]
        add(f"A-T-{SHORT[pid]}", "ANNOTATION", sh, 6, [t["circle"], t["letter"]["handle"], t["anchor"]["handle"]],
            "REIN / S-TEXT-SLAB", "T / 18", "SLAB_THICKNESS",
            f"inside {pid}; the 't' block convention ({len(ref)} inserts read '16' = 160 mm default)")
    for c in calls:
        add(f"A-C-{c['handle']}", "ANNOTATION", sh, 6, [c["handle"], c["qualifiers"][0], *c["graphic"]["handles"]],
            "S-TEXT-SLAB / S-REIN-SLAB", f"{c['raw']} (T&B)", "BAR_CALLOUT",
            f"{c['panel']} direction {c['direction']}")
    add("A-N2", "ANNOTATION", sh, 6, [*NOTE2_H, NOTE2_RATE_H], "S-TITLE TEXT",
        f"note 2 ({st['note2_rate']['text']}): top steel over beams, one third of the span, both directions",
        "GENERAL_TOP_RULE", "decoded from the legacy Arabic font; quantified by S7 on S7 panels; blocked here")
    beams = sorted({(t["handle"], t["text"].strip()) for t in st["beam_tags"]
                    if any(_dist_to_poly(t["p"], model[p]["points"]) < 700 for p in PANELS)})
    add("A-BEAMS", "ANNOTATION", sh, 6, [h for h, _ in beams], "S-TEXT", ", ".join(f"{h} {t}" for h, t in beams),
        "FRAMING", "beam tags around the two panels (S6 occurrences)")
    add("A-AXES", "DIMENSION", f"ST7757 p.1 {AXIS_SHEET}", 1, list(AXIS_DIMS), "S-DIM",
        ", ".join(f"{h} {st['dims'][h]['measurement']:g}" for h in AXIS_DIMS), "PLAN_AUTHORITY",
        "axis spacing 2700 / 2000 along x; 4800 and 1600 from the top give 3200 along y")
    for rid in ("P8-N18", "P1-NOTE-A", "P8-N22", "P8-N09", "P15-SLAB-ON-BEAMS", "P15-TEMP-TABLE", "P15-TEMP-NOTES"):
        r = rules[rid]
        add(f"RULE-{rid}", "PROJECT_RULE", f"ST7757 p.{r['page']}", r["page"], r.get("dxf_handles") or [], "",
            r["english_interpretation"], r["topic"], f"S1 {r['status']}")
    for v in VISUAL:
        add(v["ID"], "VISUAL_RECORD", v["FILE"], v["PAGE"], [], "", f"{v['DPI']} dpi box {v['BOX_PX']}",
            "VISUAL_EVIDENCE (render not kept)", v["READ"])
    for k, p in READ.items():
        add(f"REG-{k}", "FROZEN_REGISTER", str(p.relative_to(ROOT)), "", [], "", _sha(p), "URBAN_REGISTER_READ",
            "read, never written")
    return rows


def readme(s, conc, bars, blocked, cq, sens):
    r = s["released"]
    L = [f"# S8.4: water-tank roof region, concrete and reinforcement QTO", "",
         f"Baseline `{s['baseline']}`. Frozen before any comparison: `{MANIFEST_NAME}`, `references_read: []`.", "",
         "## Population", "",
         "- **Two physical slab panels**, SP-2F_ROOF_SLAB-01 and -02, on the second-floor (tower) roof, are the roof "
         "slab designated for the tank.",
         "  - One 'WATER TANK PLACE' note, leader and cloud (SPC-WATER_TANK-SFRS) mark both; the parent carries no "
         "quantity.",
         "  - Beam B3 (BL003) separates the panels; each has its own T 18 tag and its own two (T&B) callouts.",
         "- **No tank base, no tank walls, no tank member** in either discipline: not drawn, noted or scheduled.", "",
         "## Released (PROJECT_BASIS_QTO)", "",
         f"- Concrete: **{_full(r['concrete_m3'], 6)} m3** (net face area x 0.180 m).", ""]
    L += [f"| item | panel | area m2 | t mm | m3 |", "|---|---|---|---|---|"]
    L += [f"| {c['ITEM_ID']} | {c['PANEL_ID']} | {_full(c['NET_AREA_M2'], 6)} | 180 | {_full(c['VOLUME_M3'], 6)} |"
          for c in conc if c["RELEASED"]]
    L += ["", f"- Reinforcement: **{_full(r['reinforcement_kg'], 6)} kg**, eight families (two panels x two "
          "directions x top and bottom), rate density face to face, D^2/162, unrounded.", ""]
    L += ["| family | callout | Ø | /m | dir | layer | length m | kg | blocked stop zone kg |",
          "|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {b['ITEM_ID']} | {b['CALLOUT']} | {b['DIA_MM']} | {b['RATE_PER_M']} | {b['DIRECTION']} | {b['LAYER']} | "
          f"{_full(b['RELEASED_LENGTH_M'], 6)} | {_full(b['RELEASED_KG'], 6)} | {_full(b['STOP_ZONE_KG'], 6)} |"
          for b in bars]
    L += ["", f"By diameter: " + ", ".join(f"Ø{k} {_full(v, 6)} kg" for k, v in s["by_diameter_kg"].items()) + ".", "",
          "## How it is measured", "",
          "- **T 18 is the slab thickness**, 180 mm: a circled 'T' over '18', the project's 't' thickness block (which "
          "reads 16 = the 160 mm default elsewhere). It is never read as a Ø18 bar.",
          "- **(T&B) gives the faces, not the directions.** Each direction has its own callout, bound to its own drawn "
          "bar; each carries its own (T&B). Nothing is inferred for a second direction.",
          "- Bars run face to face of the supporting beams and columns. The bottom layer's stop zones at continuous or "
          "continuity-unresolved supports (the typical 50 % at 0.125 L) are blocked, not released, because neither "
          "their applicability to a (T&B) slab nor the continuity is established. The released quantity is common to "
          "every reading.",
          "- No temperature steel and no note-2 top steel are added on the tank side; both are recorded with their "
          "reasons and the note-2 kg as sensitivity.", "",
          "## S7 interface", "",
          f"- S7 stays **{s['s7']['restricted_kg']:,.3f} kg**.",
          f"- The {_full(s['s7']['tank_adjacent_released_kg'], 6)} kg of S7 top steel at the tank edges (items "
          f"{', '.join(s['s7']['tank_adjacent_items'])}) lies in panels 03, 04 and 06 and stays S7; S8.4 releases "
          "nothing on a support or beyond a face.",
          f"- All {s['s7']['excluded_items_terminated']} S7 items excluded to the region and all "
          f"{s['s7']['transfers_terminated']} PRE-S7.1 transfers land on exactly one S8.4 row (07).", "",
          "## Not released (08)", ""]
    cnt = Counter(b["STATE"] for b in blocked)
    L += [f"- {k}: {v}" for k, v in sorted(cnt.items())]
    L += ["", "## Sensitivity (not released)", ""]
    L += [f"- {x['CASE_ID']}: {x['CASE']} -> {_full(x['KG'], 6)} kg ({_full(x['DELTA_KG'], 6)})" for x in sens]
    L += ["", "## Conflicts and questions", ""]
    L += [f"- **{x['ID']}** ({x['STATE']}): {x['TEXT']}" for x in cq]
    L += ["", "## Outputs", ""] + [f"- `{o}`" for o in OUTPUTS] + [f"- `{MANIFEST_NAME}`", "",
          "Rebuild: `python3 -I research/alsenan_water_tank_s8_4/build_s8_4.py` (byte-identical). Renders and crops of "
          "the drawings stay outside git."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    try:
        s = build()
    except Stop as e:
        print(f"STOP: {e}")
        sys.exit(1)
    print(json.dumps({k: s[k] for k in ("released", "by_diameter_kg", "by_direction_layer_kg", "blocked_stop_zone_kg",
                                        "note2_tank_side_sensitivity_kg", "s7", "conservation")}, indent=1))
