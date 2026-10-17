"""S8.1 - ground slab concrete and mesh, restricted to the two source-zoned cells (2026-10-08).

    python3 -I research/alsenan_ground_slab_s8_1/build_s8_1.py

Scope. The ground-beam plan (ST7757 p.3, sheet GBP) carries the ground-slab callout twice: a TT1 symbol, a hatched
circle with 'T=10cm' and '5Ø10/m E.W.'. Each circle sits inside one cell bounded by ground-beam faces. Those two cells
are the two documented zones. The other 19 cells of the PRE-S8 ground-slab parent have no thickness and no mesh in the
source; they are listed and blocked, never filled from a ladder, a default or another slab family.

Rules are read before anything is measured (02_SOURCE_RULE_REGISTER.csv). Only P3-GROUND-SLAB sizes a quantity. P8-N22
(cover) is recorded as a conflict with a 100 mm slab, the suspended-slab rules (P8-N18, P1-NOTE-A, P4-6-NOTE-2,
P15-*) are excluded, and the material notes are descriptors.

Quantities (engine/source/ground_slab_qto.py over engine/source/slab_rebar_qto.py):
  concrete  = net zone area x 0.100 m (the zone polygon between ground-beam faces; the drawn arc is integrated as an
              arc, not as its chords)
  mesh      = two independent bar families, X (bars along x) and Y (bars along y): L = 5 /m x strip integral,
              kg = L x D^2 / 162. No +1, no rounding of the equivalent count, no second mat, no lap, hook, edge bar
              or development length.

Blind: the builder reads only the issued drawing, frozen S1 / PRE-S8 / S7 registers and the freeze manifests. It reads
no earlier quantity of the ground slab and no external estimate; the comparison runs after the freeze, in post_freeze/.
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
from engine.source import ground_slab_qto as G  # noqa: E402
from engine.source import slab_rebar_qto as SR  # noqa: E402

ROUND = "S8_1"
DATE = "2026-10-08"
POLICY = "S8_1_GROUND_SLAB_RESTRICTED_V1"
BASELINE_HEAD = "73f62c3"
R = ROOT / "research"
S1 = R / "alsenan_structural_census_s1"
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
SHEET = "GBP"
FLOOR = "GROUND_SLAB_SOG"
PARENT = "SPC-GROUND_SLAB"
MARKER_BLOCK = "TT1"
LEVEL_BLOCK = "LE"
RESTRICTED_TOTAL = "RESTRICTED_S8_1_PROJECT_BASIS"
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
             "PRE-S8": R / "pre_s8_structural_completeness/13_PRE_S8_FREEZE_MANIFEST.json"}
S1_REGS = ["SLAB_PANEL_REGISTER", "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER", "STRUCTURAL_PROJECT_RULE_REGISTER",
           "STRUCTURAL_LEVEL_REGISTER", "FOOTING_OCCURRENCE_REGISTER", "FOOTING_DEFINITION_REGISTER",
           "BEAM_OCCURRENCE_REGISTER", "COLUMN_OCCURRENCE_REGISTER"]
P = {"pre_s8_census": R / "pre_s8_structural_completeness/02_STRUCTURAL_ELEMENT_CENSUS.csv",
     "s7_panels": R / "alsenan_slab_rebar_s7/05_S7_PANEL_SUMMARY.csv",
     "s7_blocked": R / "alsenan_slab_rebar_s7/02_S7_BLOCKED_ITEMS.csv",
     "s7_summary": R / "alsenan_slab_rebar_s7/09_S7_PROJECT_SUMMARY.json",
     "s31_release": R / "alsenan_column_rebar_s3_1/COLUMN_RELEASE_REGISTER.json",
     "s31_index": R / "alsenan_column_rebar_s3_1/INDEX.json",
     "s4_occ": R / "alsenan_footing_rebar_s4/FOOTING_REBAR_OCCURRENCES.csv"}
FROZEN_OUTPUT_OF = {"pre_s8_census": ("PRE-S8", "02_STRUCTURAL_ELEMENT_CENSUS.csv"),
                    "s7_panels": ("S7", "05_S7_PANEL_SUMMARY.csv"),
                    "s7_blocked": ("S7", "02_S7_BLOCKED_ITEMS.csv"),
                    "s7_summary": ("S7", "09_S7_PROJECT_SUMMARY.json"),
                    "s4_occ": ("S4", "FOOTING_REBAR_OCCURRENCES.csv")}
# PRE-S8 census columns this round may use: identity and ownership only. The quantity-state columns of the census
# describe earlier registers and are dropped on load.
CENSUS_COLUMNS = ("ELEMENT_ID", "ROW_KIND", "PARENT_ELEMENT", "ELEMENT_FAMILY", "NEW_S8_OWNER", "S8_SCOPE", "QA_STATE",
                  "EXISTING_STAGE_OWNER")
CODE = ["research/alsenan_ground_slab_s8_1/build_s8_1.py", "engine/source/ground_slab_qto.py",
        "engine/source/slab_rebar_qto.py", "engine/source/rebar_unit_mass.py",
        "research/external_engine_lab/alsenan_structural_s1.py", "engine/source/delta_release.py"]
OUTPUTS = ["00_README.md", "01_GROUND_SLAB_POPULATION_AND_ZONE_REGISTER.csv", "02_SOURCE_RULE_REGISTER.csv",
           "03_CONCRETE_QTO.csv", "04_REINFORCEMENT_XY_QTO.csv", "05_REINFORCEMENT_STRIPS.csv",
           "06_BLOCKED_UNRESOLVED_COMPONENTS.csv", "07_OVERLAP_AND_OWNERSHIP_AUDIT.csv",
           "08_FLOOR_ZONE_SUMMARY.csv", "09_PROVENANCE.jsonl", "10_S8_1_SUMMARY.json",
           "12_PRE_S8_POPULATION_RECONCILIATION.csv"]
MANIFEST_NAME = "11_S8_1_FREEZE_MANIFEST.json"
# linework that may cross a zone interior: grid axes (no material) and the footing outlines drawn under the slab
ALLOWED_CROSSING_LAYERS = {"S-AXIS": "grid axis (no material)",
                           "S-FOOTINGS": "footing outline drawn below the slab (vertical separation, 07)",
                           "S-TEXT": "annotation (no material)", "S-DIM": "annotation (no material)",
                           "TEXT": "annotation (no material)", "LEVEL": "level mark (no material)"}
TEXT_EXHAUSTION = re.compile(r"E\.W|T\s*=\s*\d|GROUND\s*SLAB|S\.O\.G|SLAB\s+ON\s+GRADE|POLY|BLIND|PLAIN\s+CONC|"
                             r"D\.P\.M|COMPACT|SUB.?BASE|HARDCORE", re.I)
ARABIC_GROUND_SLAB = ("بلاطة ارضية", "البلاطة الارضية")


class Stop(Exception):
    pass


def check(cond, what):
    if not cond:
        raise Stop(f"S8.1 STOP: {what}")


# ------------------------------------------------------------------ io helpers
def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _full(v, nd=12):
    if v is None:
        return None
    s = f"{float(v):.{nd}f}".rstrip("0").rstrip(".")
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
    for key, (stage, name) in FROZEN_OUTPUT_OF.items():
        check(out[stage].get(name) == _sha(P[key]), f"{stage} {name} is the frozen output")
    check(_sha(DXF) == DXF_SHA, "issued ST7757 drawing unchanged")
    return frozen


def load_census():
    """PRE-S8 census rows, identity and ownership columns only."""
    return [{k: r[k] for k in CENSUS_COLUMNS} for r in _rows(P["pre_s8_census"])]


# ------------------------------------------------------------------ drawing
def read_drawing(panels):
    """Zone markers, arcs, level marks, linework crossing each cell and the text exhaustion of ST7757.dxf."""
    import alsenan_structural_s1 as S1M
    from ezdxf import bbox as BB
    from ezdxf import disassemble
    from shapely.geometry import LineString, Polygon, box
    src = S1M.Source(DXF)
    doc, msp = src.doc, src.msp
    fx, fy = src.sheets[SHEET]["frame"][:2]

    def loc(x, y):
        return (round(x - fx, 3), round(y - fy, 3))

    def on_sheet(x, y):
        return src.sheet_of(x, y) == SHEET

    markers = []
    for e in msp.query(f'INSERT[name=="{MARKER_BLOCK}"]'):
        p = e.dxf.insert
        if not on_sheet(p.x, p.y):
            continue
        texts, circle, leader = [], None, None
        for v in e.virtual_entities():
            t = v.dxftype()
            if t == "TEXT":
                texts.append(v.dxf.text)
            elif t == "CIRCLE":
                circle = (loc(v.dxf.center.x, v.dxf.center.y), round(v.dxf.radius, 3))
            elif t == "LWPOLYLINE":
                leader = [loc(x, y) for x, y, *_ in v.get_points()]
        markers.append({"handle": e.dxf.handle, "layer": e.dxf.layer, "insert": loc(p.x, p.y), "texts": texts,
                        "circle": circle, "leader": leader})
    for m in markers:
        th = [re.search(r"T\s*=\s*(\d+(?:\.\d+)?)\s*cm", t) for t in m["texts"]]
        me = [re.search(r"(\d+)\s*%%c\s*(\d+)\s*/\s*m\s*(E\.W\.)?", t) for t in m["texts"]]
        th = [x for x in th if x]
        me = [x for x in me if x]
        check(len(th) == 1 and len(me) == 1 and m["circle"], f"marker {m['handle']} reads one thickness and one mesh")
        m["thickness_mm"] = float(th[0].group(1)) * 10.0
        m["rate_per_m"] = int(me[0].group(1))
        m["dia_mm"] = int(me[0].group(2))
        m["each_way"] = bool(me[0].group(3))
        m["raw_thickness"] = th[0].group(0)
        m["raw_mesh"] = me[0].group(0).replace("%%c", "Ø")

    arcs = {}
    for pid, pn in panels.items():
        out = []
        for bh in pn["boundary_handles"]:
            e = doc.entitydb.get(bh.split("|")[1])
            if e is not None and e.dxftype() == "ARC":
                c = loc(e.dxf.center.x, e.dxf.center.y)
                out.append({"handle": e.dxf.handle, "layer": e.dxf.layer, "centre": c, "radius": e.dxf.radius,
                            "start_deg": e.dxf.start_angle, "end_deg": e.dxf.end_angle})
        arcs[pid] = out

    polys = {pid: Polygon(pn["polygon_mm"]) for pid, pn in panels.items()}
    inner = {pid: g.buffer(-1.0) for pid, g in polys.items()}
    levels = defaultdict(list)
    for e in msp.query("TEXT MTEXT"):
        p = e.dxf.insert
        if not on_sheet(p.x, p.y) or e.dxf.layer != "LEVEL":
            continue
        from shapely.geometry import Point
        lp = Point(*loc(p.x, p.y))
        for pid, g in polys.items():
            if g.contains(lp):
                levels[pid].append({"handle": e.dxf.handle, "text": (e.dxf.text if e.dxftype() == "TEXT" else e.text)})

    crossings = defaultdict(list)
    pool = []
    for e in msp:
        t = e.dxftype()
        if t in ("TEXT", "MTEXT", "DIMENSION", "ATTRIB", "POINT"):
            continue
        try:
            bb = BB.extents([e])
        except Exception:  # noqa: BLE001 - an entity without extents cannot cross a cell
            continue
        if not bb.has_data or not on_sheet((bb.extmin.x + bb.extmax.x) / 2, (bb.extmin.y + bb.extmax.y) / 2):
            continue
        if t == "INSERT" and e.dxf.name == "SWIM":
            pool.append({"handle": e.dxf.handle, "bbox_local": [*loc(bb.extmin.x, bb.extmin.y),
                                                                *loc(bb.extmax.x, bb.extmax.y)]})
        if t == "INSERT" and e.dxf.name in (MARKER_BLOCK, LEVEL_BLOCK):
            continue                   # the zone markers and the printed level marks themselves
        geoms = []
        if t == "HATCH":
            for path in e.paths:
                vs = getattr(path, "vertices", None)
                if vs and len(vs) > 2:
                    geoms.append(("HATCH_AREA", Polygon([loc(v[0], v[1]) for v in vs]).buffer(0)))
        else:
            srcs = list(e.virtual_entities()) if t == "INSERT" else [e]
            for s in srcs:
                try:
                    prims = list(disassemble.to_primitives([s]))
                except Exception:  # noqa: BLE001
                    continue
                for pr in prims:
                    try:
                        pts = [loc(v.x, v.y) for v in pr.vertices()]
                    except Exception:  # noqa: BLE001
                        continue
                    if len(pts) >= 2:
                        geoms.append((s.dxf.layer, LineString(pts)))
        for pid, g in inner.items():
            for lay, geo in geoms:
                hit = geo.intersection(g).area > 1.0 if lay == "HATCH_AREA" else geo.intersects(g)
                if hit:
                    crossings[pid].append({"handle": e.dxf.handle, "type": t,
                                           "layer": e.dxf.layer if lay == "HATCH_AREA" else lay,
                                           "block": e.dxf.name if t == "INSERT" else ""})
                    break

    texts = []
    styles = {}
    try:
        from engine.source import legacy_text as LT
        styles = {s.dxf.name: LT.font_family(s.dxf.font) for s in doc.styles}
    except Exception:  # noqa: BLE001
        LT = None

    def add(e, via):
        if e.dxftype() not in ("TEXT", "MTEXT", "ATTRIB"):
            return
        raw = (e.dxf.text if e.dxftype() != "MTEXT" else e.text) or ""
        fam = styles.get(e.dxf.get("style"))
        dec = LT.decode(raw, fam)["text"] if (LT and fam) else raw
        p = e.dxf.insert
        if TEXT_EXHAUSTION.search(raw) or any(w in (dec or "") for w in ARABIC_GROUND_SLAB):
            texts.append({"handle": e.dxf.handle or f"{via}>v", "via": via, "sheet": src.sheet_of(p.x, p.y),
                          "layer": e.dxf.layer, "text": (dec or raw).strip().replace("%%c", "Ø")})
    for e in msp:
        add(e, None)
        if e.dxftype() == "INSERT":
            for a in e.attribs:
                add(a, e.dxf.handle)
            try:
                for v in e.virtual_entities():
                    add(v, f"{e.dxf.handle}:{e.dxf.name}")
            except Exception:  # noqa: BLE001
                pass
    return {"markers": markers, "arcs": arcs, "levels": dict(levels), "crossings": dict(crossings), "pool": pool,
            "texts": texts, "frame_origin": [fx, fy], "polys": polys}


def point_in(poly_pts, pt):
    from shapely.geometry import Point, Polygon
    return Polygon(poly_pts).contains(Point(*pt))


# ------------------------------------------------------------------ zones
def regions(panels, arcs):
    out = {}
    for pid, pn in panels.items():
        ring, rep = G.ring_from_polygon(pn["polygon_mm"], [(a["centre"], a["radius"], a["start_deg"], a["end_deg"])
                                                          for a in arcs.get(pid, [])])
        holes = [G.ring_from_polygon(h)[0] for h in (pn.get("holes_mm") or [])]
        reg = [ring] + holes
        out[pid] = {"region": reg, "area_mm2": G.area(reg), "arc_chords_replaced": rep}
    return out


def bind_zones(panels, markers):
    zones = {}
    for m in markers:
        hits = [pid for pid, pn in panels.items() if point_in(pn["polygon_mm"], m["circle"][0])]
        check(len(hits) == 1, f"marker {m['handle']} circle lies in exactly one cell: {hits}")
        pid = hits[0]
        check(panels[pid]["class"] == "SLAB_PANEL", f"marker {m['handle']} lies in a slab cell")
        check(pid not in {z["panel_id"] for z in zones.values()}, f"one marker per cell ({pid})")
        zones[f"GS-ZONE-{m['handle']}"] = {"zone_id": f"GS-ZONE-{m['handle']}", "panel_id": pid, "marker": m}
    return zones


# ------------------------------------------------------------------ quantities
def quantities(zones, reg):
    conc, bars, strips, prov = [], [], [], []
    for zid, z in sorted(zones.items()):
        m, pid = z["marker"], z["panel_id"]
        a_mm2 = reg[pid]["area_mm2"]
        a_m2 = a_mm2 / 1e6
        v = G.slab_concrete(a_m2, m["thickness_mm"])
        cid = f"S8.1-C-{zid}"
        conc.append({"ITEM_ID": cid, "ZONE_ID": zid, "PANEL_ID": pid, "FLOOR": FLOOR, "PARENT_ELEMENT": PARENT,
                     "NET_AREA_M2": a_m2, "THICKNESS_MM": m["thickness_mm"], "VOLUME_M3": v,
                     "FORMULA": f"{_full(a_m2)} m2 x {m['thickness_mm'] / 1000:g} m",
                     "LANE": SR.check_label(SR.PROJECT_BASIS_QTO),
                     "THICKNESS_AUTHORITY": f"PROJECT_SOURCE (printed '{m['raw_thickness']}' in marker {m['handle']})",
                     "PLAN_AUTHORITY": "PROJECT_GEOMETRY (ground-beam inner faces as drawn; the arc as an arc; axis "
                                       "spacing agrees with the printed dimension chains, the face offsets are drawn "
                                       "only)",
                     "ZONE_BINDING": "MARKER_IN_CELL (the marker circle lies in this cell and in no other; the "
                                     "extent of application is not drawn)",
                     "EXCLUDED_VOLUMES": "ground-beam bands, columns / necks and footings (07); no opening or pit "
                                         "is drawn (P8-N04)",
                     "MEASUREMENT_ORIGIN": "S8.1 source-traced measurement (no earlier register line is used)",
                     "WHY_NOT_PHYSICAL": "the cell extent of each T=10 marker is a project-basis binding until the "
                                         "engineer confirms it"})
        prov.append({"item": cid, "kind": "CONCRETE", "formula": "area x thickness", "area_mm2": a_mm2,
                     "thickness_mm": m["thickness_mm"], "panel": pid, "s1_source_id": z.get("s1_source_id"),
                     "marker": m["handle"], "rules": ["P3-GROUND-SLAB"], "drawing_sha256": DXF_SHA})
        for d in G.DIRECTIONS:
            q = G.mesh_direction(reg[pid]["region"], d, rate_per_m=m["rate_per_m"], dia_mm=m["dia_mm"])
            check(q["coverage"]["reconciled"], f"{zid} {d} strips cover the zone area exactly")
            bid = f"S8.1-R-{zid}-{d}"
            bars.append({"ITEM_ID": bid, "ZONE_ID": zid, "PANEL_ID": pid, "FLOOR": FLOOR, "PARENT_ELEMENT": PARENT,
                         "DIRECTION": d, "BARS_RUN_ALONG": "x" if d == G.X else "y",
                         "DISTRIBUTED_ACROSS": "y" if d == G.X else "x", "RATE_PER_M": m["rate_per_m"],
                         "DIA_MM": m["dia_mm"], "BAR_FAMILIES_IN_DIRECTION": 1,
                         "STRIP_COUNT": len(q["strips"]), "DISTRIBUTION_WIDTH_M": q["distribution_width_m"],
                         "EQUIVALENT_COUNT_UNROUNDED": q["equivalent_count"], "MEAN_RUN_M": q["mean_run_m"],
                         "STRIP_INTEGRAL_M2": q["integral_m2"], "ZONE_AREA_M2": a_m2,
                         "COVERAGE_RECONCILED": q["coverage"]["reconciled"],
                         "EQUIVALENT_LENGTH_M": q["length_m"], "UNIT_MASS_KG_M": q["unit_mass_kg_m"],
                         "KG": q["kg"], "LANE": SR.check_label(SR.PROJECT_BASIS_QTO),
                         "COUNT_BASIS": SR.COUNT_RATE_DENSITY, "PHYSICAL_BBS_COUNT": q["physical_bbs_count"],
                         "RUN_BASIS": "face to face of the ground-beam inner faces (PROJECT_GEOMETRY)",
                         "END_TREATMENT": "BLOCKED (06: anchorage / cover at the beam faces not drawn)",
                         "LAYER_BASIS": f"'{m['raw_mesh']}' = one bar family in each plan direction; no second mat",
                         "FORMULA": f"{m['rate_per_m']} /m x {_full(q['integral_m2'])} m2 = "
                                    f"{_full(q['length_m'])} m x {m['dia_mm']}^2/162"})
            for i, s in enumerate(q["strips"], 1):
                strips.append({"ZONE_ID": zid, "DIRECTION": d, "BAND": i, "T0_MM": s["t0"], "T1_MM": s["t1"],
                               "WIDTH_MM": s["width_mm"], "MEAN_RUN_MM": s["run_mm"],
                               "INTEGRAL_MM2": s["integral_mm2"], "INTERVALS": s["intervals"],
                               "BRANCHES": s["branches"],
                               "EQUIVALENT_BARS_IN_BAND": m["rate_per_m"] * s["width_mm"] / 1000.0,
                               "EQUIVALENT_LENGTH_M": m["rate_per_m"] * s["integral_mm2"] / 1e6,
                               "KG": m["rate_per_m"] * s["integral_mm2"] / 1e6 * q["unit_mass_kg_m"]})
            prov.append({"item": bid, "kind": "MESH", "direction": d, "formula": "rate x strip integral x D^2/162",
                         "rate_per_m": m["rate_per_m"], "dia_mm": m["dia_mm"], "integral_mm2": q["integral_m2"] * 1e6,
                         "strips": len(q["strips"]), "panel": pid, "marker": m["handle"], "rules": ["P3-GROUND-SLAB"],
                         "unit_mass_method": q["unit_mass_method"], "drawing_sha256": DXF_SHA})
    return conc, bars, strips, prov


# ------------------------------------------------------------------ registers
def population(panels, reg, zones, census, drawing, rules):
    zone_of = {z["panel_id"]: z for z in zones.values()}
    faces = sorted(r["ELEMENT_ID"] for r in census if r["PARENT_ELEMENT"] == PARENT)
    parent = [r for r in census if r["ELEMENT_ID"] == PARENT]
    check(len(parent) == 1, "one PRE-S8 ground-slab parent")
    check(set(faces) == {pid for pid, pn in panels.items() if pn["class"] == "SLAB_PANEL"},
          "the PRE-S8 faces are the S1 GBP slab cells")
    rows = [{"ROW_ID": PARENT, "ROW_KIND": "PARENT", "PARENT_ELEMENT": "", "PANEL_ID": "", "ZONE_ID": "",
             "PRE_S8_ROW_KIND": parent[0]["ROW_KIND"], "PRE_S8_OWNER": parent[0]["NEW_S8_OWNER"],
             "AREA_M2_EXACT": None, "TERMINAL_STATE": "PARENT_AGGREGATE_ONLY",
             "CONCRETE_STATE": "SUM OF ITS MEASURED FACES (no quantity of its own)",
             "REBAR_STATE": "SUM OF ITS MEASURED FACES (no quantity of its own)",
             "NOTE": f"{len(faces)} faces; {len(zone_of)} measured in zones, {len(faces) - len(zone_of)} blocked"}]
    p3 = rules["P3-GROUND-SLAB"]
    for pid in sorted(panels):
        pn = panels[pid]
        z = zone_of.get(pid)
        in_pop = pid in faces
        edges = [{"edge": e["edge_index"], "length_m": e["length_m"], "support": e["support"],
                  "ref": e["support_ref"], "continuity": e["continuity"], "neighbour": e["neighbour_panel"]}
                 for e in pn["edges"]]
        lv = drawing["levels"].get(pid, [])
        cr = drawing["crossings"].get(pid, [])
        if in_pop:
            kind, term = "FACE", "MEASURED_ONCE_IN_ZONE" if z else "BLOCKED_NO_SOURCE_THICKNESS_OR_MESH"
        else:
            cen = [r for r in census if r["ELEMENT_ID"] == pid]
            kind = "SHEET_RECORD_OUTSIDE_POPULATION"
            term = (f"OTHER_OWNER ({cen[0]['NEW_S8_OWNER']}, parent {cen[0]['PARENT_ELEMENT']})" if cen else
                    "NOT_A_GROUND_SLAB_CELL (outside the building / court; not in the PRE-S8 census)")
        rows.append({
            "ROW_ID": pid, "ROW_KIND": kind, "PARENT_ELEMENT": PARENT if in_pop else "", "PANEL_ID": pid,
            "S1_SOURCE_ID": pn["source_id"], "S1_CLASS": pn["class"], "ZONE_ID": z["zone_id"] if z else "",
            "ZONE_MARKER": ({"handle": z["marker"]["handle"], "circle_centre_mm": z["marker"]["circle"][0],
                             "texts": [z["marker"]["raw_thickness"], z["marker"]["raw_mesh"]]} if z else ""),
            "BOUNDARY_HANDLES": pn["boundary_handles"],
            "POLYGON_MM": [[round(x, 3), round(y, 3)] for x, y in pn["polygon_mm"]],
            "HOLES_MM": pn.get("holes_mm") or [], "ARCS": drawing["arcs"].get(pid, []),
            "ARC_CHORDS_REPLACED": reg[pid]["arc_chords_replaced"],
            "AREA_M2_EXACT": reg[pid]["area_mm2"] / 1e6, "AREA_M2_S1": pn["area_m2"],
            "EDGES": edges, "PRINTED_LEVEL_MARKS": [x["text"] for x in lv],
            "SOURCE_THICKNESS_MM": z["marker"]["thickness_mm"] if z else None,
            "THICKNESS_AUTHORITY": "PROJECT_SOURCE (marker in the cell)" if z else (
                "NOT_ESTABLISHED (no marker in the cell; S1's candidate 100 mm from "
                f"{p3['rule_id']} ({p3['status']}, extent not drawn) is not adopted)" if pn["class"] == "SLAB_PANEL"
                else "NOT_APPLICABLE"),
            "SOURCE_REBAR_CALLOUT": z["marker"]["raw_mesh"] if z else "",
            "REBAR_AUTHORITY": "PROJECT_SOURCE (marker in the cell)" if z else (
                "NOT_ESTABLISHED" if pn["class"] == "SLAB_PANEL" else "NOT_APPLICABLE"),
            "OPENINGS_AND_PITS": ("none drawn (holes [], no void text / cross lines; P8-N04: every opening must "
                                  "appear on the structural drawings)") if not (pn.get("holes_mm") or
                                                                              pn["void_evidence"]["void_texts"]) else
            pn["void_evidence"],
            "LINEWORK_CROSSING_INTERIOR": sorted({f"{c['layer']}" for c in cr}),
            "CONCRETE_STATE": SR.PROJECT_BASIS_QTO if z else (SR.BLOCKED_UNQUANTIFIED if in_pop else "NOT_IN_S8_1"),
            "REBAR_STATE": SR.PROJECT_BASIS_QTO if z else (SR.BLOCKED_UNQUANTIFIED if in_pop else "NOT_IN_S8_1"),
            "TERMINAL_STATE": term, "PRE_S8_ROW_KIND": next((r["ROW_KIND"] for r in census if r["ELEMENT_ID"] == pid),
                                                            "NOT_IN_CENSUS"),
            "PRE_S8_OWNER": next((r["NEW_S8_OWNER"] for r in census if r["ELEMENT_ID"] == pid), ""),
            "NOTE": pn.get("status") or ""})
    return rows


RULE_ROLE = {
    "P3-GROUND-SLAB": ("APPLIED_IN_THE_TWO_MARKED_CELLS",
                       "sizes thickness (T=10cm) and mesh (5Ø10/m E.W.) of the cell each marker sits in; not "
                       "extended to unmarked cells"),
    "P8-N22": ("SOURCE_CONFLICT_RECORDED",
               "cover >= 7 cm in contact with soil and >= 2.5 cm for slabs cannot both hold in a 100 mm slab with a "
               "mesh of two Ø10 layers (70 + 10 + 10 + 25 = 115 mm); bar position is a conflict, the face-to-face "
               "run does not use a cover"),
    "P8-N03": ("CHECK_APPLIED", "printed axis dimension chains agree with the CAD axis spacing; the beam-face offsets "
                                "from the axes are drawn, not printed, so the plan authority stays PROJECT_GEOMETRY"),
    "P8-N04": ("CHECK_APPLIED", "no opening, pit or void is drawn in either zone, and openings must appear on the "
                                "structural drawings: no deduction"),
    "P8-N05": ("DESCRIPTOR_ONLY", "ready-mix concrete (specification, no quantity effect)"),
    "P8-N06": ("DESCRIPTOR_ONLY", "f'c >= 300 kg/cm2 for reinforced concrete (BOQ description)"),
    "P8-N07": ("DESCRIPTOR_ONLY", "cube testing (specification)"),
    "P8-N08": ("DESCRIPTOR_ONLY", "steel yield >= 4200 kg/cm2 (BOQ description)"),
    "P8-N13": ("DESCRIPTOR_ONLY", "sulphate-resisting cement for concrete in contact with soil (BOQ description)"),
    "P8-N16": ("NOT_APPLIED", "plain-concrete mix; no plain concrete / blinding is drawn under the zones (06)"),
    "P8-N18": ("EXCLUDED_SUSPENDED_SLAB_RULE", "16 cm applies to suspended slabs and is never applied to ground slabs"),
    "P1-NOTE-A": ("EXCLUDED_SUSPENDED_SLAB_RULE", "16 cm roof / slab default; suspended slabs only"),
    "P4-6-NOTE-2": ("EXCLUDED_SUSPENDED_SLAB_RULE", "top bars over beams (1/3 span) belong to the elevated slabs (S7)"),
    "P15-TEMP-TABLE": ("EXCLUDED_SUSPENDED_SLAB_RULE", "temperature steel by suspended-slab thickness"),
    "P15-TEMP-NOTES": ("EXCLUDED_SUSPENDED_SLAB_RULE", "temperature-bar laps and extents of suspended slabs"),
    "P15-SLAB-ON-BEAMS": ("EXCLUDED_SUSPENDED_SLAB_RULE", "50/50 split and 0.125 L curtailment of suspended slabs"),
    "P13-GB-EXT": ("INTERFACE_RULE", "ground beams run to the ground-floor slab level: the slab is measured to the "
                                     "beam faces and the concrete over the beam width belongs to the beam"),
    "P13-GB-GT5": ("INTERFACE_RULE", "ground beams bound the zones; their concrete and steel are owned elsewhere"),
    "P13-GB-LT5": ("INTERFACE_RULE", "ground beams bound the zones; their concrete and steel are owned elsewhere"),
    "P13-GB-LT2_5": ("INTERFACE_RULE", "ground beams bound the zones; their concrete and steel are owned elsewhere"),
    "P9-SOIL": ("CHECK_APPLIED", "founding level <= -1.50 (excavation >= 1.5 m): footing tops lie below the zones (07)"),
    "P14-LIFT": ("CHECK_APPLIED", "the lift pit sits on the FF footing, outside both zones (07)"),
    "P7-POOL": ("CHECK_APPLIED", "the pool lies outside both zones (07)"),
    "P3-LEGEND": ("CHECK_APPLIED", "no legend hatch (sunken / foam / bearing wall / open to below) inside the zones"),
    "P8-N01": ("GENERAL", "drawings are for guidance until reviewed (no quantity effect)"),
    "P8-N02": ("GENERAL", "discrepancies go to the supervising engineer (the conflicts in 06 are for that review)"),
    "P8-N24": ("GENERAL", "services coordination"),
}


def rule_register(rules, drawing, zones):
    out = []
    for rid, r in sorted(rules.items()):
        role, why = RULE_ROLE.get(rid, ("NOT_THIS_ELEMENT", f"scope {','.join(r['element_scope'])} is not the "
                                                           "ground slab"))
        out.append({"ITEM": rid, "KIND": "PROJECT_RULE", "PAGE": r["page"], "S1_STATUS": r["status"],
                    "SCOPE": r["element_scope"], "TEXT": r["english_interpretation"], "S8_1_ROLE": role,
                    "REASON": why})
    for z in sorted(zones.values(), key=lambda z: z["zone_id"]):
        m = z["marker"]
        out.append({"ITEM": f"MARKER {m['handle']}", "KIND": "SOURCE_MARKER (TT1 block)", "PAGE": 3,
                    "S1_STATUS": "PRINTED", "SCOPE": [z["panel_id"]], "TEXT": f"{m['raw_thickness']} / {m['raw_mesh']}",
                    "S8_1_ROLE": "ZONE_DEFINITION",
                    "REASON": f"circle centre {m['circle'][0]} (r {m['circle'][1]}) lies in {z['panel_id']} only"})
    hits = Counter((t["sheet"], t["text"]) for t in drawing["texts"])
    out.append({"ITEM": "TEXT_EXHAUSTION", "KIND": "SOURCE_SEARCH", "PAGE": "all sheets", "S1_STATUS": "SEARCHED",
                "SCOPE": ["ST7757.dxf TEXT / MTEXT / ATTRIB / block texts"],
                "TEXT": {f"{s}: {t}": n for (s, t), n in sorted(hits.items(), key=str)},
                "S8_1_ROLE": "SOURCE_EXHAUSTION",
                "REASON": "the only ground-slab texts are the two TT1 markers on GBP; the details-sheet plain-concrete "
                          "text belongs to the pool; no Arabic ground-slab note"})
    return out


def blocked_records(panels, zones, rules, reg, drawing):
    zone_cells = {z["panel_id"] for z in zones.values()}
    out = []
    for pid in sorted(panels):
        pn = panels[pid]
        if pn["class"] != "SLAB_PANEL" or pid in zone_cells:
            continue
        inside = sorted({c["layer"] for c in drawing["crossings"].get(pid, [])} - set(ALLOWED_CROSSING_LAYERS))
        geo = (f"; structural linework ({', '.join(inside)}) lies inside the S1 cell outline, so the cell geometry "
               "needs review before any measurement") if inside else ""
        for comp, why in (("CONCRETE_THICKNESS", "no T= marker in the cell; the extent of P3-GROUND-SLAB is not "
                                                 "drawn and no other note sizes it" + geo),
                          ("MESH", "no mesh callout in the cell" + geo)):
            out.append({"BLOCKED_ID": f"S8.1-B-{pid}-{comp}", "SUBJECT": pid, "PARENT_ELEMENT": PARENT,
                        "COMPONENT": comp, "LANE": SR.BLOCKED_UNQUANTIFIED, "KG": None, "M3": None,
                        "AREA_M2": reg[pid]["area_mm2"] / 1e6, "WHY": why,
                        "SOURCE_CHECKED": "GBP cell, TT1 markers, all DXF texts, P3 / P8 rules",
                        "NEXT_AUTHORITY": "engineer: does the ground-slab note apply to this cell, and with what "
                                          "thickness and mesh"})
    for zid, z in sorted(zones.items()):
        pid = z["panel_id"]
        refs = sorted({e["support_ref"] for e in panels[pid]["edges"] if e["support_ref"]})
        curved = bool(reg[pid]["arc_chords_replaced"])
        items = [
            ("END_ANCHORAGE_X", SR.BLOCKED_UNQUANTIFIED,
             f"bar ends at the ground-beam faces ({', '.join(refs)}): stop at cover, hook or run into the beam is not "
             "drawn; the run is measured face to face"),
            ("END_ANCHORAGE_Y", SR.BLOCKED_UNQUANTIFIED, "as X, for the bars along y"),
            ("FABRICATION_COUNT_X", SR.BLOCKED_UNQUANTIFIED,
             "integer bar count, set-out and edge bars not drawn; the equivalent count is a density, never rounded"),
            ("FABRICATION_COUNT_Y", SR.BLOCKED_UNQUANTIFIED, "as X, for the bars along y"),
            ("SUPPORT_INTERFACE", SR.BLOCKED_UNQUANTIFIED,
             "slab-to-ground-beam joint: dowels / starters into the beam and continuity of the mesh across the beams "
             "into the neighbouring cells are not drawn"),
            ("SUPPLEMENTARY_BARS", SR.BLOCKED_UNQUANTIFIED,
             "edge, corner or trimmer bars are not drawn" + ("; the curved edge has no trimming detail" if curved
                                                             else "")),
            ("LAP_SPLICES", SR.BLOCKED_UNQUANTIFIED, "no lap is drawn; none is invented"),
            ("LAYER_POSITION_AND_COVER", SR.SOURCE_CONFLICT,
             "P8-N22 (>= 7 cm against soil, >= 2.5 cm for slabs) does not fit a 100 mm slab with two Ø10 layers; "
             "bar level unresolved (no kg change under the face-to-face run)"),
            ("SUB_BASE_MEMBRANE_BLINDING", SR.BLOCKED_UNQUANTIFIED,
             "fill, membrane or blinding under the slab is not drawn (outside the reinforced-concrete scope)"),
        ]
        for comp, lane, why in items:
            out.append({"BLOCKED_ID": f"S8.1-B-{zid}-{comp}", "SUBJECT": zid, "PARENT_ELEMENT": PARENT,
                        "COMPONENT": comp, "LANE": SR.check_label(lane), "KG": None, "M3": None, "AREA_M2": None,
                        "WHY": why, "SOURCE_CHECKED": "GBP sheet, TT1 marker, P3 / P8 / P13 rules",
                        "NEXT_AUTHORITY": "engineer / ground-slab detail"})
    return out


def overlap_audit(panels, zones, reg, drawing, s1d, census, s7rows, s7blocked):
    from shapely.geometry import Polygon, box
    zp = {z["zone_id"]: Polygon(panels[z["panel_id"]]["polygon_mm"]) for z in zones.values()}
    lv = {r["kind"]: r for r in s1d["STRUCTURAL_LEVEL_REGISTER"]}
    found = lv["FOUNDATION_LEVEL"]["bound_m"]["max"]
    gf_ffl = next(r["value_m"] for r in s1d["STRUCTURAL_LEVEL_REGISTER"] if r["kind"] == "FFL" and r["level"] == "GF")
    defs = {d["definition_id"]: d for d in s1d["FOOTING_DEFINITION_REGISTER"]}
    out = []

    def add(cid, subject, check_, result, evidence, effect="none"):
        out.append({"CHECK_ID": cid, "SUBJECT": subject, "CHECK": check_, "RESULT": result, "EVIDENCE": evidence,
                    "QUANTITY_EFFECT": effect})
    for zid, z in sorted(zones.items()):
        pid = z["panel_id"]
        sup = Counter(e["support"] for e in panels[pid]["edges"])
        add(f"OV-{zid}-GB-BOUND", zid, "the zone is bounded by ground-beam faces",
            "PASS" if set(sup) == {"BEAM"} else "REVIEW", dict(sup),
            "slab measured to the beam faces; beam concrete and steel stay with the ground beams")
        bad = [c for c in drawing["crossings"].get(pid, []) if c["layer"] not in ALLOWED_CROSSING_LAYERS]
        check(not bad, f"{zid}: no structural linework crosses the zone interior: {bad}")
        add(f"OV-{zid}-LINEWORK", zid, "no ground-beam face, column / neck outline, hatch or other RC linework "
                                       "crosses the zone interior", "PASS",
            {lay: ALLOWED_CROSSING_LAYERS[lay] for lay in sorted({c["layer"] for c in drawing["crossings"].get(pid, [])})})
        lvl = [x["text"] for x in drawing["levels"].get(pid, [])]
        check(len(lvl) <= 1, f"{zid}: at most one printed level in the zone")
        top_mark = float(lvl[0]) if lvl else gf_ffl          # no mark in the cell: the GF floor level
        for f in s1d["FOOTING_OCCURRENCE_REGISTER"]:
            b = box(*f["outline"]["bbox"])
            a = zp[zid].intersection(b).area
            if a <= 0:
                continue
            ds = [float(defs[f"FDEF-{t}"]["source_row"]["raw_attributes"]["DEPHT"]) / 100.0
                  for t in ([f["type"]] if f["type"] else (f.get("candidate_types") or ["F", "F10"]))
                  if f"FDEF-{t}" in defs]
            dmax = max(ds)
            ftop = found + dmax
            margin = top_mark - 0.10 - ftop
            check(margin > 0, f"{zid} {f['footing_id']}: footing top below the slab")
            add(f"OV-{zid}-{f['footing_id']}", zid, "footing below the zone (plan overlap, vertical separation)",
                "PASS (no volume overlap)",
                {"plan_overlap_m2": round(a / 1e6, 6), "footing_type": f["type"], "depth_m": dmax,
                 "founding_level_bound_m": found, "footing_top_at_most_m": round(ftop, 3),
                 "zone_level_m": top_mark,
                 "zone_level_source": f"printed mark {lvl[0]} in the cell" if lvl else "GF FFL (level register)", "slab_underside_at_least_m": f"{top_mark} - build-up - 0.10",
                 "build_up_needed_for_contact_m": round(margin, 3)},
                "none: the slab and the footing are separate volumes, each owned once")
    ff = [f for f in s1d["FOOTING_OCCURRENCE_REGISTER"] if f["type"] == "FF"]
    for f in ff:
        b = box(*f["outline"]["bbox"])
        hit = {zid: round(zp[zid].intersection(b).area / 1e6, 6) for zid in zp}
        check(not any(hit.values()), "the lift footing lies outside the zones")
        add("OV-LIFT-FF", f["footing_id"], "lift footing / pit outside both zones", "PASS", hit)
    for p in drawing["pool"]:
        b = box(*p["bbox_local"])
        hit = {zid: round(zp[zid].intersection(b).area / 1e6, 6) for zid in zp}
        check(not any(hit.values()), "the pool lies outside the zones")
        add("OV-POOL", p["handle"], "swimming pool outside both zones", "PASS", hit)
    st = [pid for pid, pn in panels.items() if pn["class"] == "STAIR_FLIGHT_ZONE"]
    for pid in st:
        sp = Polygon(panels[pid]["polygon_mm"])
        hit = {zid: round(zp[zid].intersection(sp).area / 1e6, 6) for zid in zp}
        check(not any(hit.values()), "the ground stair flight lies outside the zones")
        add("OV-STAIR", pid, "ground stair flight is a separate S8 STAIR element", "PASS", hit)
    leak = [r["PANEL_ID"] for r in s7rows if r["PANEL_ID"].startswith("SP-GBP")]
    leak += [r[k] for r in s7blocked for k in r if isinstance(r[k], str) and "SP-GBP" in r[k]]
    check(not leak, f"no S7 item names a ground-slab cell: {leak[:3]}")
    add("OV-S7", "S7", "no elevated-slab (S7) item is on the ground-beam plan", "PASS",
        {"s7_panels": len(s7rows), "s7_blocked_items": len(s7blocked), "ground_cells_named": 0})
    face_ids = [r["ELEMENT_ID"] for r in census if r["PARENT_ELEMENT"] == PARENT]
    add("OV-PARENT", PARENT, "parent and faces are not both measured", "PASS",
        {"faces": len(face_ids), "parent_quantity": "aggregate of the faces only"})
    add("OV-LEGACY", "earlier ground-slab registers", "no earlier register line is read or added before the freeze",
        "PASS", "the builder reads the drawing, S1, PRE-S8 identity columns, S7 identity and freeze manifests only",
        "the comparison runs after the freeze (post_freeze/)")
    return out


def pre_s8_reconciliation(census):
    s31 = _j(P["s31_release"])
    s31_occ = sorted({r["occurrence_id"] for r in s31["rows"]})
    col = sorted(r["ELEMENT_ID"] for r in census if r["ELEMENT_FAMILY"].split(" ")[0] in ("COLUMN", "NECK_PEDESTAL")
                 and r["ROW_KIND"] == "ELEMENT")
    s1c = sorted(c["column_id"] for c in _j(S1 / "COLUMN_OCCURRENCE_REGISTER.json")["rows"])
    s4 = sorted(r["occurrence_id"] for r in _rows(P["s4_occ"]))
    ftg = [r for r in census if r["ELEMENT_FAMILY"].split(" ")[0] in ("ISOLATED_FOOTING", "COMBINED_FOOTING",
                                                                      "LIFT_FOOTING")]
    ftg_occ = sorted(r["EXISTING_STAGE_OWNER"].split("(", 1)[-1].split(";")[0] for r in ftg)
    s1f = sorted(f["footing_id"] for f in _j(S1 / "FOOTING_OCCURRENCE_REGISTER.json")["rows"])
    fam = Counter(r["ELEMENT_FAMILY"].split(" ")[0] for r in ftg)
    famc = Counter(r["ELEMENT_FAMILY"].split(" ")[0] for r in census if r["ELEMENT_ID"] in set(col))
    return [
        {"POPULATION": "COLUMN OCCURRENCES (all storeys incl. the foundation storey)",
         "PRE_S8_ROWS": len(col), "PRE_S8_BREAKDOWN": dict(famc), "STAGE": "S3.1", "STAGE_IDS": len(s31_occ),
         "S1_IDS": len(s1c), "ID_SETS_EQUAL": set(col) == set(s31_occ) == set(s1c),
         "UNMATCHED": sorted(set(col) ^ set(s31_occ))[:5]},
        {"POPULATION": "FOOTING OCCURRENCES", "PRE_S8_ROWS": len(ftg), "PRE_S8_BREAKDOWN": dict(fam),
         "STAGE": "S4 / S4.1", "STAGE_IDS": len(s4), "S1_IDS": len(s1f),
         "ID_SETS_EQUAL": set(ftg_occ) == set(s4) and len(ftg) == len(s1f) == len(set(r["ELEMENT_ID"] for r in ftg)),
         "UNMATCHED": sorted(set(ftg_occ) ^ set(s4))[:5]},
    ]


def summaries(conc, bars, blocked, panels, reg, zones):
    rows = []
    zone_cells = {z["panel_id"] for z in zones.values()}
    for zid in sorted(zones):
        c = [x for x in conc if x["ZONE_ID"] == zid][0]
        b = {x["DIRECTION"]: x for x in bars if x["ZONE_ID"] == zid}
        rows.append({"LEVEL": "ZONE", "ID": zid, "PANEL_ID": zones[zid]["panel_id"], "AREA_M2": c["NET_AREA_M2"],
                     "CONCRETE_M3": c["VOLUME_M3"], "X_LENGTH_M": b["X"]["EQUIVALENT_LENGTH_M"], "X_KG": b["X"]["KG"],
                     "Y_LENGTH_M": b["Y"]["EQUIVALENT_LENGTH_M"], "Y_KG": b["Y"]["KG"],
                     "TOTAL_KG": b["X"]["KG"] + b["Y"]["KG"], "LANE": SR.PROJECT_BASIS_QTO})
    blocked_cells = sorted(pid for pid, pn in panels.items() if pn["class"] == "SLAB_PANEL" and pid not in zone_cells)
    tot = {k: math.fsum(r[k] for r in rows) for k in ("AREA_M2", "CONCRETE_M3", "X_LENGTH_M", "X_KG", "Y_LENGTH_M",
                                                      "Y_KG", "TOTAL_KG")}
    barea = math.fsum(reg[p]["area_mm2"] for p in blocked_cells) / 1e6
    for level, rid in (("FLOOR", FLOOR), ("PARENT", PARENT), ("PROJECT", RESTRICTED_TOTAL)):
        rows.append({"LEVEL": level, "ID": SR.check_label(rid), "PANEL_ID": "", **tot,
                     "BLOCKED_CELLS": len(blocked_cells), "BLOCKED_AREA_M2": barea,
                     "LANE": SR.PROJECT_BASIS_QTO})
    return rows, blocked_cells, barea


def readme(s):
    z = s["zones"]
    L = [f"# S8.1 - ground slab, two source-zoned cells ({DATE})", "",
         "Restricted, project-basis quantity of the ground slab. The other S8 families are not started and no frozen "
         f"stage moves. S7 stays at **{s['s7_total_kg']:,.3f} kg**.", "",
         "## Zones", ""]
    for zid, v in sorted(z.items()):
        L.append(f"- {zid}: cell {v['panel_id']}, {v['area_m2']:.6f} m2, marker '{v['callout']}'"
                 + (f", printed level {', '.join(v['levels'])}" if v["levels"] else ""))
    L += ["", f"{s['blocked_cells']} other cells ({s['blocked_area_m2']:.6f} m2) carry no thickness and no mesh in "
              "the source. They are blocked, not filled. The ground stair flight and the court cell are other owners.",
          "", "## Quantities (project basis)", "",
          f"- Concrete: {s['concrete_m3']:.6f} m3 (net zone area x 0.100 m).",
          f"- Mesh X (bars along x): {s['x_length_m']:.6f} m, {s['x_kg']:.6f} kg.",
          f"- Mesh Y (bars along y): {s['y_length_m']:.6f} m, {s['y_kg']:.6f} kg.",
          f"- Total: {s['total_kg']:.6f} kg ({RESTRICTED_TOTAL}).", "",
          "Rate density 5 /m x strip integral, D^2/162. The equivalent count is never rounded and never +1. One bar "
          "family each way; no second mat, lap, hook, edge bar or development length. X and Y are integrated over "
          "their own strips (05); each covers the whole zone, so the two directions carry the same length.", "",
          "Concrete and mesh are PROJECT_BASIS_QTO: the thickness and mesh are printed, the plan is the drawn "
          "ground-beam faces, but the extent of each T=10 marker (its own cell) is a binding the engineer has to "
          "confirm before the concrete can be called source-derived physical.", "",
          "## Not quantified", "",
          f"{s['blocked_records']} blocked records (06): {s['blocked_cells']} cells x thickness and mesh, plus per zone "
          "the end anchorage, fabrication count, slab-beam interface, supplementary bars, laps and the sub-base. Bar "
          "position against P8-N22 cover is a SOURCE_CONFLICT.", "",
          "## Checks", "",
          "- Every one of the 21 PRE-S8 faces terminates once; the parent carries no quantity of its own.",
          "- X and Y strips each cover the zone area exactly; zone, direction, diameter and parent totals reconcile.",
          "- No ground-beam face, column / neck outline or other concrete linework crosses a zone; footings are below "
          "the slab, the lift and pool are elsewhere, and no S7 item is on the ground-beam plan.",
          "- The comparison with earlier figures runs only after the freeze (post_freeze/).", ""]
    return "\n".join(L)


def build():
    frozen = verify_inputs()
    s1d = {reg: _j(S1 / f"{reg}.json")["rows"] for reg in S1_REGS}
    panels = {p["panel_id"]: p for p in s1d["SLAB_PANEL_REGISTER"] if p["sheet"] == SHEET}
    rules = {r["rule_id"]: r for r in s1d["STRUCTURAL_PROJECT_RULE_REGISTER"]}
    census = load_census()
    drawing = read_drawing(panels)
    check(len(drawing["markers"]) == 2, "two ground-slab markers on the ground-beam plan")
    reg = regions(panels, drawing["arcs"])
    zones = bind_zones(panels, drawing["markers"])
    for z in zones.values():
        z["s1_source_id"] = panels[z["panel_id"]]["source_id"]
    conc, bars, strips, prov = quantities(zones, reg)
    pop = population(panels, reg, zones, census, drawing, rules)
    rr = rule_register(rules, drawing, zones)
    blocked = blocked_records(panels, zones, rules, reg, drawing)
    s7rows, s7blocked = _rows(P["s7_panels"]), _rows(P["s7_blocked"])
    audit = overlap_audit(panels, zones, reg, drawing, s1d, census, s7rows, s7blocked)
    recon_pre = pre_s8_reconciliation(census)
    summ, blocked_cells, barea = summaries(conc, bars, blocked, panels, reg, zones)

    # conservation
    faces = [r for r in pop if r["ROW_KIND"] == "FACE"]
    check(len(faces) == 21 and Counter(r["ROW_ID"] for r in faces).most_common(1)[0][1] == 1, "21 faces, once each")
    check(Counter(r["TERMINAL_STATE"] for r in faces) == Counter({"MEASURED_ONCE_IN_ZONE": len(zones),
                                                                 "BLOCKED_NO_SOURCE_THICKNESS_OR_MESH":
                                                                     21 - len(zones)}), "face terminals")
    check(len(conc) == len(zones) and len(bars) == 2 * len(zones), "each zone measured once, X and Y once each")
    check(all(b["KG"] is None and b["M3"] is None for b in blocked), "no blocked record carries a quantity")
    mass_rows = [{"kg": b["KG"], "ZONE": b["ZONE_ID"], "DIRECTION": b["DIRECTION"], "DIA": b["DIA_MM"],
                  "PARENT": b["PARENT_ELEMENT"], "LANE": b["LANE"]} for b in bars]
    rec = SR.reconcile(mass_rows, ["ZONE", "DIRECTION", "DIA", "PARENT", "LANE"])
    check(rec["ok"], "mass reconciles by zone, direction, diameter, parent and lane")
    strip_kg = math.fsum(s["KG"] for s in strips)
    check(abs(strip_kg - rec["total"]) <= 1e-9 * max(rec["total"], 1.0), "strips reconcile to the directional kg")
    vol = SR.reconcile([{"kg": c["VOLUME_M3"], "ZONE": c["ZONE_ID"], "PARENT": c["PARENT_ELEMENT"]} for c in conc],
                       ["ZONE", "PARENT"])
    check(vol["ok"], "concrete reconciles by zone and parent")
    for z in zones.values():
        xs = [b for b in bars if b["ZONE_ID"] == z["zone_id"]]
        check(all(abs(b["STRIP_INTEGRAL_M2"] - b["ZONE_AREA_M2"]) <= 1e-9 * b["ZONE_AREA_M2"] for b in xs),
              "each direction's strip integral equals the zone area")
        sx = [s for s in strips if s["ZONE_ID"] == z["zone_id"] and s["DIRECTION"] == G.X]
        sy = [s for s in strips if s["ZONE_ID"] == z["zone_id"] and s["DIRECTION"] == G.Y]
        check(sx and sy, "X and Y have their own strips")
    s7sum = _j(P["s7_summary"])["totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"]
    check(all(r["ID_SETS_EQUAL"] for r in recon_pre), "PRE-S8 column and footing populations reconcile by id")

    x_kg = math.fsum(b["KG"] for b in bars if b["DIRECTION"] == G.X)
    y_kg = math.fsum(b["KG"] for b in bars if b["DIRECTION"] == G.Y)
    summary = {
        "round": ROUND, "date": DATE, "policy": POLICY, "baseline": BASELINE_HEAD,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}", "references_read": [], "s8_families_started": [
            "GROUND_SLAB (two source-zoned cells only)"], "state": RESTRICTED_TOTAL,
        "zones": {zid: {"panel_id": z["panel_id"], "area_m2": reg[z["panel_id"]]["area_mm2"] / 1e6,
                        "callout": f"{z['marker']['raw_thickness']} / {z['marker']['raw_mesh']}",
                        "marker": z["marker"]["handle"],
                        "levels": [x["text"] for x in drawing["levels"].get(z["panel_id"], [])],
                        "arc_chords_replaced": reg[z["panel_id"]]["arc_chords_replaced"]}
                  for zid, z in sorted(zones.items())},
        "included_area_m2": math.fsum(c["NET_AREA_M2"] for c in conc), "blocked_cells": len(blocked_cells),
        "blocked_area_m2": barea, "concrete_m3": vol["total"],
        "concrete_by_zone_m3": {c["ZONE_ID"]: c["VOLUME_M3"] for c in conc},
        "x_length_m": math.fsum(b["EQUIVALENT_LENGTH_M"] for b in bars if b["DIRECTION"] == G.X), "x_kg": x_kg,
        "y_length_m": math.fsum(b["EQUIVALENT_LENGTH_M"] for b in bars if b["DIRECTION"] == G.Y), "y_kg": y_kg,
        "total_kg": rec["total"], "lanes": dict(Counter(b["LANE"] for b in bars)),
        "blocked_records": len(blocked), "blocked_by_lane": dict(Counter(b["LANE"] for b in blocked)),
        "reconciliation": {"mass": {k: v["ok"] for k, v in rec["levels"].items()},
                           "concrete": {k: v["ok"] for k, v in vol["levels"].items()},
                           "strips_kg_equal": True, "pre_s8_population": {r["POPULATION"]: r["ID_SETS_EQUAL"]
                                                                          for r in recon_pre}},
        "faces": {"total": len(faces), "measured": len(zones), "blocked": len(faces) - len(zones)},
        "s7_total_kg": s7sum, "s7_unchanged": True,
        "frozen_baselines": {k: v["manifest_sha256"] for k, v in frozen.items()},
    }
    return {"pop": pop, "rr": rr, "conc": conc, "bars": bars, "strips": strips, "blocked": blocked, "audit": audit,
            "summ": summ, "prov": prov, "summary": summary, "recon_pre": recon_pre, "frozen": frozen}


POP_FIELDS = ["ROW_ID", "ROW_KIND", "PARENT_ELEMENT", "PANEL_ID", "S1_SOURCE_ID", "S1_CLASS", "ZONE_ID", "ZONE_MARKER",
              "BOUNDARY_HANDLES", "POLYGON_MM", "HOLES_MM", "ARCS", "ARC_CHORDS_REPLACED", "AREA_M2_EXACT",
              "AREA_M2_S1", "EDGES", "PRINTED_LEVEL_MARKS", "SOURCE_THICKNESS_MM", "THICKNESS_AUTHORITY",
              "SOURCE_REBAR_CALLOUT", "REBAR_AUTHORITY", "OPENINGS_AND_PITS", "LINEWORK_CROSSING_INTERIOR",
              "CONCRETE_STATE", "REBAR_STATE", "TERMINAL_STATE", "PRE_S8_ROW_KIND", "PRE_S8_OWNER", "NOTE"]


def write(B):
    _csv("01_GROUND_SLAB_POPULATION_AND_ZONE_REGISTER.csv", B["pop"], POP_FIELDS)
    _csv("02_SOURCE_RULE_REGISTER.csv", B["rr"], list(B["rr"][0]))
    _csv("03_CONCRETE_QTO.csv", B["conc"], list(B["conc"][0]))
    _csv("04_REINFORCEMENT_XY_QTO.csv", B["bars"], list(B["bars"][0]))
    _csv("05_REINFORCEMENT_STRIPS.csv", B["strips"], list(B["strips"][0]))
    _csv("06_BLOCKED_UNRESOLVED_COMPONENTS.csv", B["blocked"], list(B["blocked"][0]))
    _csv("07_OVERLAP_AND_OWNERSHIP_AUDIT.csv", B["audit"], list(B["audit"][0]))
    _csv("08_FLOOR_ZONE_SUMMARY.csv", B["summ"], ["LEVEL", "ID", "PANEL_ID", "AREA_M2", "CONCRETE_M3", "X_LENGTH_M",
                                                  "X_KG", "Y_LENGTH_M", "Y_KG", "TOTAL_KG", "BLOCKED_CELLS",
                                                  "BLOCKED_AREA_M2", "LANE"])
    (HERE / "09_PROVENANCE.jsonl").write_text("".join(json.dumps(p, sort_keys=True, ensure_ascii=False) + "\n"
                                                      for p in B["prov"]), encoding="utf-8")
    _json("10_S8_1_SUMMARY.json", B["summary"])
    _csv("12_PRE_S8_POPULATION_RECONCILIATION.csv", B["recon_pre"], list(B["recon_pre"][0]))
    (HERE / "00_README.md").write_text(readme(B["summary"]), encoding="utf-8")


def main():
    B = build()
    write(B)
    inputs = sorted({_rel(p) for p in P.values()} | {f"research/alsenan_structural_census_s1/{r}.json"
                                                     for r in S1_REGS})
    man = {"round": ROUND, "date": DATE, "state": "FROZEN_BEFORE_COMPARISON", "references_read": [],
           "baseline": BASELINE_HEAD, "engine_commit_stamp": B["summary"]["engine_commit"],
           "rule": "S8.1 quantifies the two source-zoned ground-slab cells only; every other cell is blocked; the "
                   "comparison with earlier figures runs after this manifest is committed",
           "code": {c: _sha(ROOT / c) for c in CODE}, "inputs": {i: _sha(ROOT / i) for i in inputs},
           "drawing_sha256": {"ST7757.dxf": DXF_SHA},
           "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "frozen_baselines": B["summary"]["frozen_baselines"]}
    _json(MANIFEST_NAME, man)
    s = B["summary"]
    print(json.dumps({k: s[k] for k in ("zones", "included_area_m2", "blocked_cells", "blocked_area_m2", "concrete_m3",
                                        "x_length_m", "x_kg", "y_length_m", "y_kg", "total_kg", "blocked_records",
                                        "blocked_by_lane", "reconciliation", "s7_total_kg")}, indent=1,
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
