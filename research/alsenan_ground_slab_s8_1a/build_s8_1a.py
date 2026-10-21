"""S8.1A - ground-slab population recovery and cover-authority audit (source, geometry, coverage and authority only).

    python3 -I research/alsenan_ground_slab_s8_1a/build_s8_1a.py

This round releases no steel or concrete, and S8.1's frozen quantities stay as they are. It does five things:

1. It replays S1's own ground-beam-plan face gate on ST7757.dxf and finds the face that S1 rejected although the face
   passes S1's size gates. That face is the unfaced region round lift pit 7BE (issue S8.1-PF-01).
2. It cuts that face by the drawn structural linework, adding the S-BW pit outlines that S1 did not use as edges. Each
   part is then classified from drawn evidence only: the pit-wall hatch and its island, closed column outlines, S1
   beam bands, tread lines, the building envelope, level marks and the registered architectural GF plan.
3. It audits the scope of the two TT1 'T=10cm / 5Ø10/m E.W.' annotations.
4. It audits the cover note (P8-N22) against the physical contact condition. E.W. is one mesh of two crossing
   directions; it is not a top-and-bottom pair.
5. It proves the population is conserved: drawn ground-slab domain = measured + blocked + excluded + conflicted.

The S8.1 census is not rewritten. This round adds a delta that links to it, plus a correction layer for S8.1's cover
record.
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
from engine.source import region_recovery as RR  # noqa: E402

ROUND = "S8_1A"
DATE = "2026-10-08"
BASELINE_HEAD = "12cabc3"
POLICY = "S8_1A_GROUND_SLAB_POPULATION_AND_COVER_AUTHORITY_V1"
R = ROOT / "research"
S1 = R / "alsenan_structural_census_s1"
S81 = R / "alsenan_ground_slab_s8_1"
DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
PDF = ROOT / "data/inputs/by_sha256/74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3.pdf"
PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
SHEET = "GBP"
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
             "S8.1": S81 / "11_S8_1_FREEZE_MANIFEST.json"}
S1_REGS = ["SLAB_PANEL_REGISTER", "STRUCTURAL_PROJECT_RULE_REGISTER", "STRUCTURAL_LEVEL_REGISTER",
           "BEAM_OCCURRENCE_REGISTER", "FOOTING_OCCURRENCE_REGISTER"]
P = {"census": R / "pre_s8_structural_completeness/02_STRUCTURAL_ELEMENT_CENSUS.csv",
     "s81_register": S81 / "01_GROUND_SLAB_POPULATION_AND_ZONE_REGISTER.csv",
     "s81_rules": S81 / "02_SOURCE_RULE_REGISTER.csv",
     "s81_concrete": S81 / "03_CONCRETE_QTO.csv",
     "s81_blocked": S81 / "06_BLOCKED_UNRESOLVED_COMPONENTS.csv",
     "s81_summary": S81 / "10_S8_1_SUMMARY.json",
     "ps51_summary": R / "pre_s5_1_source_resolution/PRE_S5_1_SUMMARY.json",
     "ps51_index": R / "pre_s5_1_source_resolution/INDEX.json",
     "floor_plans": ROOT / "tests/alsenan/registers/FLOOR_PLAN_REGISTER.json"}
FROZEN_OUTPUT_OF = {"census": ("PRE-S8", "02_STRUCTURAL_ELEMENT_CENSUS.csv"),
                    "s81_register": ("S8.1", "01_GROUND_SLAB_POPULATION_AND_ZONE_REGISTER.csv"),
                    "s81_rules": ("S8.1", "02_SOURCE_RULE_REGISTER.csv"),
                    "s81_concrete": ("S8.1", "03_CONCRETE_QTO.csv"),
                    "s81_blocked": ("S8.1", "06_BLOCKED_UNRESOLVED_COMPONENTS.csv"),
                    "s81_summary": ("S8.1", "10_S8_1_SUMMARY.json")}
CENSUS_COLUMNS = ("ELEMENT_ID", "ROW_KIND", "PARENT_ELEMENT", "ELEMENT_FAMILY", "NEW_S8_OWNER", "S8_SCOPE")
CODE = ["engine/source/region_recovery.py", "engine/source/delta_release.py",
        "research/alsenan_ground_slab_s8_1a/build_s8_1a.py", "research/external_engine_lab/alsenan_structural_s1.py",
        "research/source_recovery_delta/vector_pdf.py", "engine/source/legacy_text.py"]
OUTPUTS = ["00_README.md", "01_RECOVERED_LIFT_PIT_REGION.csv", "02_POPULATION_OWNERSHIP_DELTA.csv",
           "03_TT1_ANNOTATION_SCOPE_AUDIT.csv", "04_TT1_INTERPRETATION_REGISTER.csv", "05_COVER_APPLICABILITY_AUDIT.csv",
           "06_S8_1_CORRECTION_LAYER.csv", "07_UNQUANTIFIED_AREA_ACCOUNTING.csv",
           "08_CONFLICT_AND_QUESTION_REGISTER.csv", "09_CONSERVATION_CHECKS.csv", "10_POPULATION_RECONCILIATION.csv",
           "11_FROZEN_MANIFEST_CHECKS.csv", "12_PROVENANCE.jsonl", "13_S8_1A_SUMMARY.json"]
MANIFEST_NAME = "14_S8_1A_FREEZE_MANIFEST.json"
PARENT = "SPC-GROUND_SLAB"
LIFT = "SPC-LIFT_PIT"
LIFT_WALLS = "PS8-LIFT-WALLS"
BARRIER_EXTRA = ("S-BW",)                          # pit outlines: drawn, not used by S1 as face edges
STAIR_LAYERS = ("2", "5")                          # tread / divider linework: evidence, never closes a face here
TREAD_LAYER = "2"
PIT_WALL_MM = 200.0                                # P14-LIFT: 20 cm pit walls
PLATE_CLOSE_MM = 250.0                             # PS5.1: bridges the 300 mm beam bands between S1 panels
NO_LEVEL = "no printed level"
OPENING_WORDS = ("VOID", "OPEN", "SHAFT", "LIFT", "ELEV", "فراغ", "فتحة", "منور", "مصعد", "بئر")
LEVEL_RX = re.compile(r"^(?:%%p|\+|-)?\d+\.\d\d$")
D10 = 10.0
T_SLAB = 100.0


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


def _m2(a):
    return a / 1e6


def _r3(p):
    return [round(p[0], 3), round(p[1], 3)]


def ring_pts(poly):
    """Canonical exterior: counter-clockwise, starting at the lowest-left vertex, 3 decimals."""
    from shapely.geometry.polygon import orient
    g = orient(poly, 1.0)
    pts = [_r3(p) for p in list(g.exterior.coords)[:-1]]
    k = min(range(len(pts)), key=lambda i: (pts[i][1], pts[i][0]))
    return pts[k:] + pts[:k]


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode())
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()[:16]


# ------------------------------------------------------------------ inputs
def verify_inputs():
    frozen = {k: DR.verify_frozen(m, ROOT) for k, m in MANIFESTS.items()}
    idx = _j(S1 / "INDEX.json")["registers"]
    for reg in S1_REGS:
        check(idx[reg]["sha256"] == _sha(S1 / f"{reg}.json"), f"S1 {reg} unchanged")
    out = {k: _j(m)["outputs"] for k, m in MANIFESTS.items()}
    for key, (stage, name) in FROZEN_OUTPUT_OF.items():
        check(out[stage].get(name) == _sha(P[key]), f"{stage} {name} is the frozen output")
    check(_j(P["ps51_index"])["outputs"]["PRE_S5_1_SUMMARY.json"] == _sha(P["ps51_summary"]),
          "PS5.1 registration record unchanged")
    m81 = _j(MANIFESTS["S8.1"])
    check(m81["state"] == "FROZEN_BEFORE_COMPARISON" and m81["references_read"] == [], "S8.1 frozen before comparison")
    for f, sha in ((DXF, DXF_SHA), (ARCH, ARCH_SHA), (PDF, PDF_SHA)):
        check(_sha(f) == sha, f"issued drawing {f.name} unchanged")
    return frozen


# ------------------------------------------------------------------ S1 replay
def s1_replay():
    """S1's own reader, beam lines, planar arrangement and face gate on GBP; every face gets S1's disposition."""
    import alsenan_structural_s1 as S1M
    src = S1M.Source(DXF)
    C = S1M.column_census(src)
    cols = S1M._support_columns(C, SHEET)
    BS = S1M.beam_census_sheet(src, SHEET, cols)
    zones = S1M.detail_zones(src, SHEET)
    segs, arcs = [], []
    for e in src.entities()[SHEET]:
        if e["layer"] == "S-OPENING" and e["type"] == "LINE":
            continue          # S1 adds axis-parallel opening outlines; GBP has none (checked below)
        if e["layer"] not in S1M.PANEL_EDGE_LAYERS:
            continue
        if e["type"] == "LINE":
            if not (S1M._in_zone(e["a"], zones) and S1M._in_zone(e["b"], zones)):
                segs.append((*e["a"], *e["b"], f"{e['layer']}|{e['handle']}"))
        elif e["type"] == "LWPOLYLINE":
            for sg in e["segs"]:
                if sg[0] == "ARC":
                    arcs.append((sg[1][0], sg[1][1], sg[2], sg[3], sg[4], f"{e['layer']}|{e['handle']}"))
                elif not (S1M._in_zone(sg[0], zones) and S1M._in_zone(sg[1], zones)):
                    segs.append((*sg[0], *sg[1], f"{e['layer']}|{e['handle']}"))
        elif e["type"] in ("ARC", "CIRCLE"):
            if not S1M._in_zone(e["c"], zones):
                arcs.append((e["c"][0], e["c"][1], e["r"], e["a0"], e["a1"], f"{e['layer']}|{e['handle']}"))
    check(not any(e["layer"] == "S-OPENING" for e in src.entities()[SHEET]), "GBP carries no S-OPENING linework")
    T = S1M.PT.build(segs, eps=3.0, arcs=arcs)
    lines = BS["lines"]

    def in_strip(pt):
        for ln in lines:
            s_, d = S1M._proj(ln, pt)
            if ln["t0"] - 20 <= s_ <= ln["t1"] + 20 and abs(d) <= ln["width_mm"] / 2 + 15:
                return ln["line_id"]
        return None
    disp = []
    for f in T["faces"]:
        A, Pm = f["net_area_m2"], f["perimeter_m"]
        th = 2 * A / Pm if Pm else 0.0
        ip = f["interior_point"]
        strip = in_strip(ip)
        col = next((c["id"] for c in cols if c["bbox"][0] <= ip[0] <= c["bbox"][2]
                    and c["bbox"][1] <= ip[1] <= c["bbox"][3]), None)
        gate = ("S1_REJECT_AREA" if A < 0.6 else "S1_REJECT_THICKNESS" if th < 0.45 else
                "S1_REJECT_STRIP" if strip else "S1_REJECT_COLUMN" if col else "S1_PANEL")
        disp.append({"face_id": f["face_id"], "area_m2": A, "thickness_m": th, "interior_point": ip, "gate": gate,
                     "strip_line": strip, "column": col, "face": f})
    panels = S1M.slab_panels(src, SHEET, BS, cols)["panels"]
    return {"src": src, "BS": BS, "cols": cols, "T": T, "disp": disp, "panels": panels, "S1M": S1M}


# ------------------------------------------------------------------ evidence
def drawing_evidence(rep):
    """Barrier lines, pit-wall hatches and islands, column outlines, beam bands, treads and level marks (GBP local)."""
    from shapely import make_valid
    from shapely.geometry import LineString, Polygon
    src = rep["src"]
    fx, fy = src.sheets[SHEET]["frame"][:2]
    layers = set(rep["S1M"].PANEL_EDGE_LAYERS) | set(BARRIER_EXTRA)
    barriers, stair_lines, treads, outlines = [], [], [], {}
    for e in src.entities()[SHEET]:
        segs = []
        if e["type"] == "LINE":
            segs = [(e["a"], e["b"])]
        elif e["type"] == "LWPOLYLINE":
            segs = [(sg[0], sg[1]) for sg in e["segs"] if sg[0] != "ARC"]
            if e.get("closed") and not e.get("has_bulge"):
                outlines[e["handle"]] = {"layer": e["layer"], "poly": Polygon(e["pts"])}
        for a, b in segs:
            if math.dist(a, b) <= 0:
                continue
            ln = LineString([a, b])
            if e["layer"] in layers:
                barriers.append((e["handle"], e["layer"], ln))
            if e["layer"] in STAIR_LAYERS:
                stair_lines.append((e["handle"], e["layer"], ln))
            if e["layer"] == TREAD_LAYER and e["type"] == "LINE":
                treads.append((e["handle"], ln))
    walls, islands = [], []
    for h in src.doc.modelspace().query("HATCH[layer=='S-HAT.BAT']"):
        loops = []
        for path in h.paths:
            pts = [(x - fx, y - fy) for x, y in hatch_loop(path)]
            if len(pts) >= 3:
                g = Polygon(pts)
                loops.append((bool(path.path_type_flags & 1), g if g.is_valid else make_valid(g).buffer(0)))
        outer = [g for ext, g in loops if ext]
        inner = [g for ext, g in loops if not ext]
        if not outer:
            continue
        rp = outer[0].representative_point()
        if src.sheet_of(rp.x + fx, rp.y + fy) != SHEET:
            continue
        reg = outer[0]
        for g in inner:
            reg = reg.difference(g)
        walls.append({"handle": h.dxf.handle, "pattern": h.dxf.pattern_name, "outer": outer[0], "region": reg,
                      "islands": inner})
        for g in inner:
            islands.append({"hatch": h.dxf.handle, "pattern": h.dxf.pattern_name, "outer": outer[0], "island": g})
    columns = [(h, o["poly"]) for h, o in sorted(outlines.items()) if o["layer"] == "S-COL.BON"]
    bands = []
    for ln in rep["BS"]["lines"]:
        (ux, uy), (nx, ny), off, w = ln["dir"], ln["normal"], ln["offset"], ln["width_mm"]

        def pt(t, s):
            return (t * ux + (off + s) * nx, t * uy + (off + s) * ny)
        bands.append((ln["line_id"], Polygon([pt(ln["t0"], -w / 2), pt(ln["t1"], -w / 2), pt(ln["t1"], w / 2),
                                              pt(ln["t0"], w / 2)]), w))
    levels = [{"handle": t["handle"], "text": t["text"], "p": t["p"]} for t in src.texts(SHEET)
              if t.get("layer") == "LEVEL" and LEVEL_RX.match(t["text"].strip())]
    return {"barriers": barriers, "stair_lines": stair_lines, "treads": treads, "outlines": outlines, "walls": walls,
            "islands": islands, "columns": columns, "bands": bands, "levels": levels, "frame": (fx, fy)}


def hatch_loop(path):
    """Vertices of one hatch boundary path; arc edges are flattened at 5-degree steps."""
    if hasattr(path, "vertices"):
        return [(v[0], v[1]) for v in path.vertices]
    pts = []
    for ed in path.edges:
        if hasattr(ed, "start"):
            pts.append((ed.start[0], ed.start[1]))
        elif hasattr(ed, "radius") and hasattr(ed, "start_angle"):
            a0, a1 = ed.start_angle, ed.end_angle
            if not ed.ccw:
                a0, a1 = -a0, -a1
            if a1 < a0:
                a1 += 360.0
            n = max(2, int((a1 - a0) / 5.0) + 1)
            for i in range(n):
                t = math.radians(a0 + (a1 - a0) * i / (n - 1))
                pts.append((ed.center[0] + ed.radius * math.cos(t),
                            ed.center[1] + ed.radius * math.sin(t) * (1 if ed.ccw else -1)))
        else:
            raise Stop(f"hatch edge {type(ed).__name__} not read")
    return pts


def paired_bands(barriers, region, s1_bands, *, w_min=150.0, w_max=450.0):
    """Exact beam bands: the strip between two parallel drawn beam-face lines (layers 1 / S-BEAM) 150-450 mm apart,
    over their common length. Each band is linked to the S1 beam line it overlaps most (owner link only)."""
    from shapely.geometry import Polygon
    segs = [(h, ln) for h, lay, ln in barriers if lay in ("1", "S-BEAM") and ln.intersects(region)]
    out = []
    for i in range(len(segs)):
        (ha, a) = segs[i]
        (ax0, ay0), (ax1, ay1) = a.coords[0], a.coords[-1]
        la = math.dist((ax0, ay0), (ax1, ay1))
        ux, uy = (ax1 - ax0) / la, (ay1 - ay0) / la
        for j in range(i + 1, len(segs)):
            (hb, b) = segs[j]
            (bx0, by0), (bx1, by1) = b.coords[0], b.coords[-1]
            lb = math.dist((bx0, by0), (bx1, by1))
            vx, vy = (bx1 - bx0) / lb, (by1 - by0) / lb
            if abs(ux * vy - uy * vx) > 1e-4:
                continue
            d = (bx0 - ax0) * -uy + (by0 - ay0) * ux
            if not (w_min <= abs(d) <= w_max):
                continue
            ta = sorted((0.0, la))
            tb = sorted(((bx0 - ax0) * ux + (by0 - ay0) * uy, (bx1 - ax0) * ux + (by1 - ay0) * uy))
            t0, t1 = max(ta[0], tb[0]), min(ta[1], tb[1])
            if t1 - t0 <= 50.0:
                continue
            nx, ny = -uy * d, ux * d
            band = Polygon([(ax0 + ux * t0, ay0 + uy * t0), (ax0 + ux * t1, ay0 + uy * t1),
                            (ax0 + ux * t1 + nx, ay0 + uy * t1 + ny), (ax0 + ux * t0 + nx, ay0 + uy * t0 + ny)])
            s1 = max(s1_bands, key=lambda x: x[1].intersection(band).area)
            link = s1[0] if s1[1].intersection(band).area > 0.5 * band.area else None
            out.append((f"{ha}+{hb}", band, abs(d), link))
    return out


def pit_islands(ev):
    """An island of a pit-wall hatch is a lift-pit opening only when it is a closed S-BW outline and the hatched ring
    around it is the 20 cm pit wall of P14-LIFT."""
    out = []
    for isl in ev["islands"]:
        g, o = isl["island"], isl["outer"]
        sbw = [h for h, x in ev["outlines"].items() if x["layer"] == "S-BW"
               and x["poly"].hausdorff_distance(g) < 1.0]
        sbw_outer = [h for h, x in ev["outlines"].items() if x["layer"] == "S-BW"
                     and x["poly"].hausdorff_distance(o) < 1.0]
        gb, ob = g.bounds, o.bounds
        rings = {round(gb[0] - ob[0], 3), round(ob[2] - gb[2], 3), round(gb[1] - ob[1], 3), round(ob[3] - gb[3], 3)}
        if sbw and sbw_outer and rings == {PIT_WALL_MM}:
            out.append({**isl, "inner_outline": sbw[0], "outer_outline": sbw_outer[0], "wall_mm": PIT_WALL_MM})
    return out


def arch_labels():
    """P7757 GF texts in GBP-local mm through PS5.1's frozen registration (one translation, 30/30 column outlines)."""
    import ezdxf
    from ezdxf import disassemble
    from engine.source import legacy_text as LT
    reg = _j(P["ps51_summary"])["registration"]
    check(reg["state"] == "REGISTERED" and reg["matched"] == reg["arch_outlines"] == 30, "arch registration holds")
    tx, ty = reg["translation_arch_to_gbp"]
    gf = next(s["bounds"] for s in _j(P["floor_plans"])["sheets"] if s["floor"] == "GF")
    doc = ezdxf.readfile(ARCH)
    styles = {s.dxf.name: LT.font_family(s.dxf.font) for s in doc.styles}
    return {"translation": [tx, ty], "gf_bounds": gf, "doc": doc, "styles": styles, "LT": LT,
            "disassemble": disassemble}


def arch_texts(A, frame):
    out = []
    for e in A["disassemble"].recursive_decompose(A["doc"].modelspace()):
        if e.dxftype() not in ("TEXT", "MTEXT"):
            continue
        p = e.dxf.insert
        gf = A["gf_bounds"]
        if not (gf[0] <= p[0] <= gf[2] and gf[1] <= p[1] <= gf[3]):
            continue
        raw = e.dxf.text if e.dxftype() == "TEXT" else e.plain_text()
        fam = A["styles"].get(e.dxf.get("style", "Standard"))
        dec = A["LT"].decode(raw, fam)["text"] if fam else raw
        x, y = p[0] + A["translation"][0] - frame[0], p[1] + A["translation"][1] - frame[1]
        out.append({"raw": raw.strip(), "text": (dec or raw).strip(), "layer": e.dxf.layer, "p": (x, y)})
    return out


ROOM_WORD = re.compile(r"[A-Za-z؀-ۿ]{2,}")


def labels_in(poly, texts):
    from shapely.geometry import Point
    return sorted({t["text"] for t in texts if ROOM_WORD.search(t["text"]) and t["layer"] not in ("LEVEL",)
                   and poly.contains(Point(t["p"]))})


def levels_in(poly, levels):
    from shapely.geometry import Point
    return sorted((lv["text"], lv["handle"]) for lv in levels if poly.contains(Point(lv["p"])))


# ------------------------------------------------------------------ recovery
def recover(rep, ev, A_texts, census):
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    frozen_gbp = [r for r in _j(S1 / "SLAB_PANEL_REGISTER.json")["rows"] if r["sheet"] == SHEET]
    by_src = {r["source_id"].split(":")[-1]: r for r in frozen_gbp}
    accepted = [d for d in rep["disp"] if d["gate"] == "S1_PANEL"]
    check(sorted(d["face_id"] for d in accepted) == sorted(by_src), "the S1 gate replays: the same 23 panels")
    for d in accepted:
        check(abs(d["area_m2"] - by_src[d["face_id"]]["area_m2"]) < 6e-4, f"panel {d['face_id']} area replays")
    check(sorted(p["face_id"] for p in rep["panels"]) == sorted(by_src), "S1 slab_panels gives the same 23 panels")
    unfaced = [d for d in rep["disp"] if d["gate"] in ("S1_REJECT_STRIP", "S1_REJECT_COLUMN")]
    check(len(unfaced) == 1, f"exactly one face passes S1's size gates and is rejected at the strip/column gate: "
                             f"{[d['face_id'] for d in unfaced]}")
    U = unfaced[0]
    f = U["face"]
    dom = Polygon(f["ring"], f.get("holes") or [])
    if not dom.is_valid:
        dom = dom.buffer(0)
    check(abs(_m2(dom.area) - U["area_m2"]) < 1e-6, "domain polygon keeps the face's net area")
    s81 = {r["ROW_ID"]: r for r in _rows(P["s81_register"]) if r["POLYGON_MM"]}
    for rid, r in s81.items():
        ov = Polygon(json.loads(r["POLYGON_MM"])).intersection(dom).area
        check(ov < 1.0, f"the recovered face does not overlap S8.1 record {rid}")
    barriers = [b for b in ev["barriers"] if b[2].intersects(dom.buffer(1.0))]
    parts = RR.partition(dom, [b[2] for b in barriers])
    alt = RR.partition(dom, [b[2] for b in barriers] + [s[2] for s in ev["stair_lines"]])
    check([round(p.area, 3) for p in parts] == [round(p.area, 3) for p in alt],
          "stair linework closes no face: the partition is the same with and without it")
    s1_only = RR.partition(dom, [b[2] for b in barriers if b[1] not in BARRIER_EXTRA])
    proof = RR.tiling_proof(dom, parts)
    check(proof["exact"], f"the parts tile the recovered face exactly: {proof}")
    pits = pit_islands(ev)
    plate_src = [Polygon(r["polygon_mm"], r.get("holes_mm") or []) for r in frozen_gbp]
    U2 = unary_union([g.buffer(PLATE_CLOSE_MM, join_style=2) for g in plate_src]).buffer(-PLATE_CLOSE_MM, join_style=2)
    court = unary_union([Polygon(r["polygon_mm"], r.get("holes_mm") or []) for r in frozen_gbp
                         if r["class"] == "OUTSIDE_BUILDING_OR_COURT"])
    plate = unary_union([Polygon(g.exterior) for g in getattr(U2, "geoms", [U2])]).difference(court)
    owners = {r["ELEMENT_ID"]: r for r in census}
    check(LIFT in owners and LIFT_WALLS in owners, "PRE-S8 holds the lift pit and its walls")
    beam_occ = defaultdict(list)
    for b in _j(S1 / "BEAM_OCCURRENCE_REGISTER.json")["rows"]:
        if b.get("sheet") == SHEET:
            beam_occ[b["member"]].append(b["beam_id"])
    bands = paired_bands(barriers, dom.buffer(500.0), ev["bands"])
    band_link = {b[0]: b[3] for b in bands}
    out = []
    for i, part in enumerate(parts, 1):
        lane, kind, evd = RR.classify(
            part, envelope=plate,
            openings=[(f"{x['inner_outline']} (island of hatch {x['hatch']})", x["island"]) for x in pits],
            walls=[(w["handle"], w["region"]) for w in ev["walls"]],
            columns=ev["columns"], beam_bands=[(b[0], b[1]) for b in bands], treads=ev["treads"])
        bound = sorted({f"{b[1]}|{b[0]}" for b in barriers if part.boundary.intersection(b[2]).length > 1.0})
        rp = part.representative_point()
        pid = f"S8.1A-RG-{i:02d}"
        if lane == RR.GROUND_SLAB_CANDIDATE:
            owner, state = PARENT, "BLOCKED_NO_SOURCE_THICKNESS_OR_MESH"
        elif lane == RR.LIFT_PIT_OPENING:
            owner, state = LIFT, "EXCLUDED_LIFT_PIT_OPENING (owned by the lift-pit system)"
        elif lane == RR.STRUCTURAL_BEAM_OR_WALL and kind == "WALL":
            owner, state = LIFT_WALLS if evd["evidence_id"] in {x["hatch"] for x in pits} else "UNRESOLVED_WALL", \
                "EXCLUDED_STRUCTURAL (pit wall)"
        elif lane == RR.STRUCTURAL_BEAM_OR_WALL and kind == "BEAM":
            line = band_link.get(evd["evidence_id"])
            occ = beam_occ.get(line, [])
            owner, state = f"S5 GROUND_BEAM line {line} ({len(occ)} S1 occurrences)", \
                "EXCLUDED_STRUCTURAL (ground-beam band)"
            evd = {**evd, "s1_beam_line": line, "s1_beam_occurrences": occ}
        elif lane == RR.STRUCTURAL_BEAM_OR_WALL:
            owner, state = "S3.1 COLUMN", "EXCLUDED_STRUCTURAL (column)"
        elif lane == RR.STAIR_OR_SPECIAL_STRUCTURE:
            owner, state = "S8 STAIR (new element candidate: not in the PRE-S8 census)", \
                "EXCLUDED_STAIR_ZONE (stair family)"
        else:
            owner, state = "UNOWNED", f"CLASSIFICATION_BLOCKED ({kind})"
        out.append({"PART_ID": pid, "LANE": lane, "KIND": kind, "AREA_M2": _m2(part.area),
                    "REPRESENTATIVE_POINT": _r3((rp.x, rp.y)), "BBOX_MM": [round(v, 3) for v in part.bounds],
                    "POLYGON_MM": ring_pts(part), "HOLES": len(part.interiors), "BOUNDARY_SOURCES": bound,
                    "EVIDENCE": evd, "LEVEL_MARKS": levels_in(part, ev["levels"]),
                    "ARCH_GF_LABELS": labels_in(part, A_texts), "OWNER": owner, "STATE": state,
                    "PARENT_FACE": U["face_id"], "_poly": part})
    return {"unfaced": U, "domain": dom, "parts": out, "proof": proof, "pits": pits, "plate": plate, "bands": bands,
            "s1_only_parts": [_m2(p.area) for p in s1_only], "_s1_only": s1_only, "barriers": barriers}


# ------------------------------------------------------------------ TT1 scope
def tt1_audit(rep, ev, A_texts, rec, s81):
    from shapely.geometry import LineString, Point, Polygon
    import ezdxf
    import vector_pdf as VP
    src = rep["src"]
    doc = src.doc
    inserts = [e for e in doc.modelspace().query("INSERT") if e.dxf.name == "TT1"]
    sheets = sorted({src.sheet_of(e.dxf.insert[0], e.dxf.insert[1]) for e in inserts})
    cells = {rid: Polygon(json.loads(r["POLYGON_MM"])) for rid, r in s81.items()
             if r["ROW_KIND"] == "FACE"}
    markers = []
    for e in inserts:
        h = e.dxf.handle
        circ = [x for x in src.entities()[SHEET] if x["handle"].startswith(f"{h}:TT1") and x["type"] == "CIRCLE"]
        lead = [x for x in src.entities()[SHEET] if x["handle"].startswith(f"{h}:TT1") and x["type"] == "LWPOLYLINE"]
        hat = [x for x in src.entities()[SHEET] if x["handle"].startswith(f"{h}:TT1") and x["type"] == "HATCH"]
        c = circ[0]
        disk = Point(c["c"]).buffer(c["r"], 64)
        in_cell = [rid for rid, g in cells.items() if g.contains(disk)]
        lpts = lead[0]["pts"]
        pointer = LineString(lpts[:2])                        # circle edge to the elbow
        underline = LineString(lpts[1:])                      # the text baseline
        lead_cells = sorted({rid for p in lpts for rid, g in cells.items() if g.contains(Point(p))})
        overrun = {rid: round(underline.intersection(g).length, 3) for rid, g in cells.items()
                   if rid not in in_cell and underline.intersection(g).length > 0}
        markers.append({"handle": h, "circle_centre": _r3(c["c"]), "radius": c["r"], "circle_within": in_cell,
                        "leader": [_r3(p) for p in lpts], "leader_cells": lead_cells,
                        "pointer_cells": sorted(rid for rid, g in cells.items() if g.contains(pointer)),
                        "underline_length_mm": round(underline.length, 3),
                        "underline_overrun_mm": overrun, "hatch_entities": len(hat)})
    blk = doc.blocks["TT1"]
    blk_hatch = [x for x in blk if x.dxftype() == "HATCH"]
    hatch_extent = []
    for x in blk_hatch:
        for path in x.paths:
            if hasattr(path, "vertices"):
                pts = [(v[0], v[1]) for v in path.vertices]
            else:
                pts = [(ed.start[0], ed.start[1]) for ed in path.edges if hasattr(ed, "start")]
            hatch_extent.append([round(min(q[0] for q in pts), 3), round(max(q[0] for q in pts), 3)])
    page3 = VP.paths(PDF, 3)
    lay = Counter(p[0] for p in page3)
    hs = [p for p in page3 if p[0] == "S-HAT-SLAB"]
    boxes = [(min(q[0] for q in pts), min(q[1] for q in pts), max(q[0] for q in pts), max(q[1] for q in pts))
             for _, _, pts in hs]
    parent = list(range(len(boxes)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            ci = ((boxes[i][0] + boxes[i][2]) / 2, (boxes[i][1] + boxes[i][3]) / 2)
            cj = ((boxes[j][0] + boxes[j][2]) / 2, (boxes[j][1] + boxes[j][3]) / 2)
            if math.dist(ci, cj) <= 40.0:                    # one symbol is ~28 pt across
                parent[find(i)] = find(j)
    clusters = defaultdict(list)
    for i, b in enumerate(boxes):
        clusters[find(i)].append(b)
    groups = sorted([min(b[0] for b in v), min(b[1] for b in v), max(b[2] for b in v), max(b[3] for b in v)]
                    for v in clusters.values())
    legend_layers = sorted(k for k in lay if k and (k.startswith("S-HAT.") or k.startswith("S-LEG")))
    slab_layer_ents = [x for x in src.entities()[SHEET] if x["layer"] in ("S-HAT-SLAB", "S-TEXT-SLAB", "S-REIN-SLAB")]
    from ezdxf import disassemble
    titles = sorted({e.dxf.text.strip() for e in disassemble.recursive_decompose(doc.modelspace())
                     if e.dxftype() == "TEXT" and e.dxf.layer == "S-TITLE TEXT"
                     and src.sheet_of(e.dxf.insert[0], e.dxf.insert[1]) == SHEET and re.search(r"[A-Z]{3}", e.dxf.text)})
    lv_by_cell = {rid: r["PRINTED_LEVEL_MARKS"] for rid, r in s81.items() if r["ROW_KIND"] == "FACE"}
    cand = [p for p in rec["parts"] if p["LANE"] == RR.GROUND_SLAB_CANDIDATE]
    cell_rows = []
    for rid, g in sorted(cells.items()):
        cell_rows.append({"cell": rid, "zone": s81[rid]["ZONE_ID"], "area_m2": float(s81[rid]["AREA_M2_EXACT"]),
                          "levels": json.loads(lv_by_cell[rid] or "[]"), "arch": labels_in(g, A_texts)})
    for p in cand:
        cell_rows.append({"cell": p["PART_ID"], "zone": "", "area_m2": p["AREA_M2"],
                          "levels": [x[0] for x in p["LEVEL_MARKS"]], "arch": p["ARCH_GF_LABELS"]})
    marker_cells = {m["circle_within"][0]: m["handle"] for m in markers}
    arch_of = {c["cell"]: c["arch"] for c in cell_rows}
    lvl_of = {c["cell"]: sorted({str(x if isinstance(x, str) else x.get("text", x)) for x in c["levels"]})
              for c in cell_rows}
    rows = [
        ("TT1-01", "PLAN_TITLE", titles, "the sheet is the ground-beams plan; no ground-slab plan, title or slab "
                                         "schedule exists", "NO_SCOPE_EVIDENCE"),
        ("TT1-02", "OCCURRENCES", {"inserts": len(inserts), "sheets": sheets},
         "TT1 is inserted twice in the whole drawing, both on GBP", "NO_SCOPE_EVIDENCE"),
        ("TT1-03", "LEGEND_PDF_P3", {"S-HAT-SLAB symbol groups": len(groups),
                                     "group_bboxes_pt": [[round(v, 1) for v in g] for g in groups],
                                     "legend_layers": legend_layers},
         "page 3 carries the hatched-circle symbol only at the two plan positions; the legend hatch samples use "
         "other layers, so TT1 is not a legend symbol with a defined meaning", "NO_SCOPE_EVIDENCE"),
        ("TT1-04", "LEADER_ENDPOINTS", [{k: m[k] for k in ("handle", "circle_centre", "circle_within", "pointer_cells",
                                                           "underline_length_mm", "underline_overrun_mm")}
                                        for m in markers],
         "each marker circle lies wholly inside one cell and its pointer segment stays in that cell; the "
         "horizontal underline is the text baseline (" +
         ", ".join(f"{m['handle']}: {m['underline_length_mm']:.0f} mm" +
                   (f", overrunning {', '.join(f'{v:.0f} mm into {k}' for k, v in m['underline_overrun_mm'].items())}"
                    if m["underline_overrun_mm"] else "") for m in markers) +
         "); an underline that runs past a beam is text length, not a pointer, so no other cell is designated",
         "CIRCLE_IN_ONE_CELL" if all(len(m["circle_within"]) == 1 and m["pointer_cells"] == m["circle_within"]
                                     for m in markers) else "REVIEW"),
        ("TT1-05", "SLAB_BOUNDARIES", {"slab-layer entities on GBP": sorted({x["handle"] for x in slab_layer_ents}),
                                       "zone outlines": 0},
         "no zone boundary, dashed outline or region line is drawn for the callouts", "NO_SCOPE_EVIDENCE"),
        ("TT1-06", "HATCHES", {"block hatch x-extent (block units)": hatch_extent, "marker radius": markers[0]["radius"]},
         "the TT1 hatch fills half of the 500 mm marker circle: a symbol fill, not a zone", "NO_SCOPE_EVIDENCE"),
        ("TT1-07", "NOTES", json.loads(next(r for r in _rows(P["s81_rules"]) if r["ITEM"] == "TEXT_EXHAUSTION")["TEXT"]),
         "the only ground-slab texts in the drawing are the two TT1 markers; no general note gives a ground-slab "
         "thickness or mesh", "NO_SCOPE_EVIDENCE"),
        ("TT1-08", "CELL_LEVELS", {c: lvl_of[c] for c in sorted(lvl_of)},
         "marker cells: " + ", ".join(f"{c} ({marker_cells[c]}) {lvl_of.get(c) or NO_LEVEL}" for c in sorted(marker_cells))
         + "; "
         "+0.30 and +1.00 are both printed in other cells, so a level-specific reading would need a level for "
         "the 1690 cell and still has no stated rule", "LEVEL_SCOPE_NOT_ESTABLISHED"),
        ("TT1-09", "ARCHITECTURAL_COORDINATION", {c["cell"]: c["arch"] for c in cell_rows if c["arch"]},
         "marker cells: " + ", ".join(f"{c} ({marker_cells[c]}) " + (" / ".join(arch_of.get(c) or []) or "no GF label")
                                      for c in sorted(marker_cells)) +
         f"; {sum(1 for c in cell_rows if c['arch'])} of {len(cell_rows)} cells carry ordinary room labels and none "
         "names a slab zone, so the architecture shows no extent that the callouts would follow", "NO_SCOPE_EVIDENCE"),
        ("TT1-10", "REPETITION", {"markers": len(markers), "candidate_cells": len(cell_rows)},
         f"{len(markers)} markers among {len(cell_rows)} cells: repetition is not used to infer any scope (brief §2)",
         "NOT_USED")]
    audit = [{"CHECK_ID": a, "CHECK": b, "EVIDENCE": c, "FINDING": d, "RESULT": e} for a, b, c, d, e in rows]
    all_area = math.fsum(c["area_m2"] for c in cell_rows)
    marked_area = math.fsum(c["area_m2"] for c in cell_rows if c["cell"] in marker_cells)
    interp = [
        {"INTERPRETATION_ID": "I1", "SCOPE": "containing cell only", "CELLS": sorted(marker_cells),
         "AREA_M2": marked_area, "STATUS": "CURRENT_VERSIONED_URBAN_PROJECT_BASIS (S8.1 V1)",
         "EVIDENCE_FOR": "TT1-04: each circle sits wholly in one cell and its leader points at no other cell",
         "EVIDENCE_AGAINST": "no note says the callout is local; a single callout could be meant for a wider slab",
         "QUANTITY_EFFECT": "S8.1 frozen quantities (the only quantities released)"},
        {"INTERPRETATION_ID": "I2", "SCOPE": "a multi-cell zone round each marker", "CELLS": [],
         "AREA_M2": None, "STATUS": "NOT_DETERMINABLE",
         "EVIDENCE_FOR": "none drawn", "EVIDENCE_AGAINST": "TT1-05/06: no zone outline or hatch defines an extent",
         "QUANTITY_EFFECT": "none (no extent to measure)"},
        {"INTERPRETATION_ID": "I3", "SCOPE": "all ordinary ground-slab cells", "CELLS": [c["cell"] for c in cell_rows],
         "AREA_M2": all_area, "STATUS": "NOT_ESTABLISHED",
         "EVIDENCE_FOR": "a ground-beam plan with one slab type is common practice (not project evidence)",
         "EVIDENCE_AGAINST": "TT1-07: no general note; TT1-02/03: two local callouts, not a legend rule",
         "QUANTITY_EFFECT": "none (area shown for scale only)"},
        {"INTERPRETATION_ID": "I4", "SCOPE": "a level-specific zone (+0.30 / +1.00)", "CELLS": [],
         "AREA_M2": None, "STATUS": "NOT_ESTABLISHED",
         "EVIDENCE_FOR": "the 169D cell is printed +0.30",
         "EVIDENCE_AGAINST": "TT1-08: the 1690 cell has no printed level; no rule ties a slab type to a level",
         "QUANTITY_EFFECT": "none"},
        {"INTERPRETATION_ID": "VERDICT", "SCOPE": "ANNOTATION_SCOPE_NOT_ESTABLISHED", "CELLS": sorted(marker_cells),
         "AREA_M2": marked_area, "STATUS": "ANNOTATION_SCOPE_NOT_ESTABLISHED",
         "EVIDENCE_FOR": "", "EVIDENCE_AGAINST": "",
         "QUANTITY_EFFECT": "S8.1 two-cell measurement kept as a versioned Urban project-basis interpretation; "
                            "no thickness or mesh is extended to another cell"}]
    return {"audit": audit, "interpretations": interp, "markers": markers, "cells": cell_rows,
            "pdf_groups": len(groups)}


# ------------------------------------------------------------------ cover
def cover_audit(rep, rules):
    src = rep["src"]
    det = src.texts("DET")
    pool_title = next(t for t in det if "SWIMMING POOL" in t["text"].upper())
    pool_bars = [t for t in det if re.search(r"%%[cC]\d", t["text"]) and t["p"][1] > 8000]
    bb = (min(t["p"][0] for t in pool_bars), min(t["p"][1] for t in pool_bars),
          max(t["p"][0] for t in pool_bars), max(t["p"][1] for t in pool_bars))
    build = [t for t in det if re.search(r"MEMBRANE|PLAIN CONCRETE|SECREED|SCREED", t["text"], re.I)]
    inside = all(bb[0] <= t["p"][0] <= bb[2] and bb[1] <= t["p"][1] <= bb[3] for t in build)
    check(inside and build, "the build-up texts lie inside the swimming-pool detail")
    rid = {r["rule_id"]: r for r in rules}
    n22 = rid["P8-N22"]
    fits = {
        "F1 CAST_DIRECTLY_AGAINST_SOIL (70 bottom, 25 top)": RR.mesh_cover_fit(T_SLAB, (D10, D10), 70.0, 25.0),
        "F2 NO_SOIL_CONTACT (25 bottom, 25 top)": RR.mesh_cover_fit(T_SLAB, (D10, D10), 25.0, 25.0),
        "F3 CAST_ON_BLINDING / MEMBRANE (bottom cover not stated)": RR.mesh_cover_fit(T_SLAB, (D10, D10), None, 25.0),
        "F4 reference only: T&B two meshes, 25 / 25 (not drawn)": RR.mesh_cover_fit(T_SLAB, (D10,) * 4, 25.0, 25.0),
        "F5 reference only: T&B two meshes, 70 / 25 (not drawn)": RR.mesh_cover_fit(T_SLAB, (D10,) * 4, 70.0, 25.0)}
    rows = [
        {"ITEM": "C-01", "TOPIC": "COVER_RULE", "SOURCE": "P8-N22 (ST7757.pdf p.8)", "EVIDENCE": n22["raw_text"],
         "FINDING": n22["english_interpretation"] + " The rule ties 70 mm to contact with soil and names no blinding or "
                                                     "membrane case.", "STATUS": "RULE_EXACT"},
        {"ITEM": "C-02", "TOPIC": "GROUND_SLAB_DETAIL", "SOURCE": "DET sheet titles; PDF detail pages per S1 rules",
         "EVIDENCE": sorted({t["text"] for t in det if t["text"].startswith("%%u")}),
         "FINDING": "no section or detail of the ground slab exists: the details are the pool and the dome; pages 13-16 "
                    "hold footings, ground beams, lintels, lift pit, parapets, slab-on-beams, stairs",
         "STATUS": "NO_DETAIL"},
        {"ITEM": "C-03", "TOPIC": "BUILD_UP_TEXTS", "SOURCE": "DET S-TEXT.D",
         "EVIDENCE": {"texts": sorted(t["text"] for t in build), "pool_detail_title": pool_title["text"],
                      "pool_detail_text_bbox": [round(v) for v in bb]},
         "FINDING": "screed / insulation membrane / plain concrete are inside the swimming-pool detail: the pool's "
                    "build-up, not the ground slab's", "STATUS": "NOT_APPLICABLE_TO_GROUND_SLAB"},
        {"ITEM": "C-04", "TOPIC": "PLAIN_CONCRETE_NOTE", "SOURCE": "P8-N16", "EVIDENCE": rid["P8-N16"]["raw_text"],
         "FINDING": "a plain-concrete mix with no location: it does not place a blinding under the ground slab",
         "STATUS": "NO_LOCATION"},
        {"ITEM": "C-05", "TOPIC": "SOIL_CONTACT_NOTE", "SOURCE": "P8-N13", "EVIDENCE": rid["P8-N13"]["raw_text"],
         "FINDING": "sulphate-resisting cement for concrete in contact with soil: a material rule; it does not say "
                    "whether the ground slab is cast against soil", "STATUS": "GENERAL"},
        {"ITEM": "C-06", "TOPIC": "LEVELS_AND_BEAMS", "SOURCE": "P9-SOIL, P13-GB-EXT, GBP level marks",
         "EVIDENCE": {"P9-SOIL": rid["P9-SOIL"]["english_interpretation"],
                      "P13-GB-EXT": rid["P13-GB-EXT"]["english_interpretation"],
                      "levels": "street ±0.00; ground-floor cells +0.30 and +1.00"},
         "FINDING": "the slab sits between ground beams that rise to the ground-floor level, above the excavation: what "
                    "lies directly under it (soil, compacted fill, blinding, membrane) is not drawn or specified",
         "STATUS": "UNDERLAY_NOT_DRAWN"},
        {"ITEM": "C-07", "TOPIC": "CONTACT_CONDITION", "SOURCE": "C-01 .. C-06",
         "EVIDENCE": ["CAST_DIRECTLY_AGAINST_SOIL", "CAST_ON_BLINDING", "CAST_ON_MEMBRANE_OR_SEPARATION",
                      "OTHER_PROJECT_SUPPORTED_INTERFACE"],
         "FINDING": "no source supports any of the four interfaces", "STATUS": "CONTACT_CONDITION_UNRESOLVED"},
        {"ITEM": "C-08", "TOPIC": "E.W. VERSUS T&B", "SOURCE": "TT1 '5Ø10/m E.W.'",
         "EVIDENCE": "E.W. = each way: one bar family in each plan direction",
         "FINDING": "one mesh of two crossing directions; the crossing bars stack once (Ø10 + Ø10 = 20 mm). Nothing "
                    "states top and bottom mats, so no second mat is assumed", "STATUS": "ONE_MESH"}]
    for i, (name, f) in enumerate(fits.items(), 9):
        rows.append({"ITEM": f"C-{i:02d}", "TOPIC": "GEOMETRIC_FIT", "SOURCE": f"100 mm slab, {name}", "EVIDENCE": f,
                     "FINDING": ("does not fit by " + _full(-f["margin_mm"]) + " mm") if f["fits"] is False else
                                ("fits with " + _full(f["margin_mm"]) + " mm spare") if f["fits"] else
                                "no verdict: the governing bottom cover is not stated",
                     "STATUS": ("CONDITIONAL_DIMENSIONAL_CONFLICT" if f["fits"] is False and "reference" not in name
                                else "REFERENCE_ONLY" if "reference" in name else
                                "FITS_IF_CONDITION_HOLDS" if f["fits"] else "NO_VERDICT")})
    rows.append({"ITEM": f"C-{len(rows) + 1:02d}", "TOPIC": "VERDICT", "SOURCE": "C-01 .. C-13",
                 "EVIDENCE": {"contact": "CONTACT_CONDITION_UNRESOLVED",
                              "soil_contact_case": "70 + 10 + 10 + 25 = 115 mm > 100 mm",
                              "no_soil_case": "25 + 10 + 10 + 25 = 70 mm <= 100 mm"},
                 "FINDING": "a dimensional conflict exists only if the slab is cast directly against soil, which no "
                            "source establishes; no bar level is invented and no quantity changes",
                 "STATUS": "COVER_APPLICABILITY_UNRESOLVED"})
    return {"rows": rows, "fits": fits}


def correction_layer(s81_blocked, s81_rules):
    cov = [b for b in s81_blocked if b["COMPONENT"] == "LAYER_POSITION_AND_COVER"]
    check(len(cov) == 2 and all(b["LANE"] == "SOURCE_CONFLICT" for b in cov), "S8.1 holds two cover conflicts")
    out = []
    for b in cov:
        out.append({"CORRECTION_ID": f"S8.1A-C-{b['SUBJECT']}-COVER", "S8_1_RECORD": b["BLOCKED_ID"],
                    "S8_1_FILE": "06_BLOCKED_UNRESOLVED_COMPONENTS.csv", "FIELD": "LANE",
                    "S8_1_VALUE": b["LANE"], "CORRECTED_VALUE": "BLOCKED_UNQUANTIFIED",
                    "CORRECTED_STATE": "COVER_APPLICABILITY_UNRESOLVED",
                    "WHY": "a dimensional conflict needs an established soil contact; contact is unresolved (05 C-07) "
                           "and E.W. is one mesh (05 C-08)",
                    "KG_EFFECT": 0.0, "M3_EFFECT": 0.0, "S8_1_FILE_CHANGED": False})
    r22 = next(r for r in s81_rules if r["ITEM"] == "P8-N22")
    out.append({"CORRECTION_ID": "S8.1A-C-P8-N22-ROLE", "S8_1_RECORD": "P8-N22", "S8_1_FILE": "02_SOURCE_RULE_REGISTER.csv",
                "FIELD": "S8_1_ROLE", "S8_1_VALUE": r22["S8_1_ROLE"], "CORRECTED_VALUE": "COVER_APPLICABILITY_UNRESOLVED",
                "CORRECTED_STATE": "COVER_APPLICABILITY_UNRESOLVED",
                "WHY": "the 115 mm > 100 mm check holds only for a slab cast against soil (05 C-09)",
                "KG_EFFECT": 0.0, "M3_EFFECT": 0.0, "S8_1_FILE_CHANGED": False})
    return out


# ------------------------------------------------------------------ build
def build():
    frozen = verify_inputs()
    census = [{k: r[k] for k in CENSUS_COLUMNS} for r in _rows(P["census"])]
    rep = s1_replay()
    ev = drawing_evidence(rep)
    A = arch_labels()
    A_texts = arch_texts(A, ev["frame"])
    rec = recover(rep, ev, A_texts, census)
    s81 = {r["ROW_ID"]: r for r in _rows(P["s81_register"])}
    s81_poly = {k: v for k, v in s81.items() if v["POLYGON_MM"]}
    s81_summary = _j(P["s81_summary"])
    s81_blocked = _rows(P["s81_blocked"])
    s81_rules = _rows(P["s81_rules"])
    rules = _j(S1 / "STRUCTURAL_PROJECT_RULE_REGISTER.json")["rows"]
    tt = tt1_audit(rep, ev, A_texts, rec, s81_poly)
    cov = cover_audit(rep, rules)
    corr = correction_layer(s81_blocked, s81_rules)
    parts = rec["parts"]
    by_lane = defaultdict(float)
    for p in parts:
        by_lane[p["LANE"]] += p["AREA_M2"]
    cand = [p for p in parts if p["LANE"] == RR.GROUND_SLAB_CANDIDATE]

    # ---------------------------------------------------------- delta (links, never rewrites)
    delta = []
    for rid, r in sorted(s81_poly.items()):
        delta.append({"DELTA_ID": f"S8.1A-D-{rid}", "ACTION": "LINK_UNCHANGED", "RECORD": rid, "S8_1_ROW": rid,
                      "PARENT_FACE": "", "LANE": r["TERMINAL_STATE"].split(" ")[0], "AREA_M2": float(r["AREA_M2_EXACT"]),
                      "OWNER": r["PRE_S8_OWNER"] or "NONE (outside the building)", "NOTE": "S8.1 census row kept as is"})
    for p in parts:
        delta.append({"DELTA_ID": f"S8.1A-D-{p['PART_ID']}", "ACTION": "ADD_RECOVERED_PART", "RECORD": p["PART_ID"],
                      "S8_1_ROW": "", "PARENT_FACE": p["PARENT_FACE"], "LANE": p["LANE"], "AREA_M2": p["AREA_M2"],
                      "OWNER": p["OWNER"], "NOTE": p["STATE"]})
    new_blocked = []
    for p in cand:
        for comp in ("CONCRETE_THICKNESS", "MESH"):
            new_blocked.append({"BLOCKED_ID": f"S8.1A-B-{p['PART_ID']}-{comp}", "SUBJECT": p["PART_ID"],
                                "PARENT_ELEMENT": PARENT, "COMPONENT": comp, "LANE": "BLOCKED_UNQUANTIFIED",
                                "AREA_M2": p["AREA_M2"], "KG": None, "M3": None,
                                "WHY": "recovered ground-slab cell with no printed thickness or mesh "
                                       "(ANNOTATION_SCOPE_NOT_ESTABLISHED)"})
    for b in new_blocked:
        delta.append({"DELTA_ID": f"S8.1A-D-{b['BLOCKED_ID']}", "ACTION": "ADD_BLOCKED_RECORD", "RECORD": b["BLOCKED_ID"],
                      "S8_1_ROW": "", "PARENT_FACE": "", "LANE": b["LANE"], "AREA_M2": b["AREA_M2"],
                      "OWNER": PARENT, "NOTE": b["WHY"]})

    # ---------------------------------------------------------- accounting and reconciliation
    meas = [r for r in s81_poly.values() if r["TERMINAL_STATE"].startswith("MEASURED")]
    blk = [r for r in s81_poly.values() if r["ROW_KIND"] == "FACE" and r["TERMINAL_STATE"].startswith("BLOCKED")]
    stair_old = [r for r in s81_poly.values() if r["TERMINAL_STATE"].startswith("OTHER_OWNER")]
    outside = [r for r in s81_poly.values() if r["TERMINAL_STATE"].startswith("NOT_A_GROUND_SLAB_CELL")]
    A_meas = math.fsum(float(r["AREA_M2_EXACT"]) for r in meas)
    A_blk_old = math.fsum(float(r["AREA_M2_EXACT"]) for r in blk)
    A_stair_old = math.fsum(float(r["AREA_M2_EXACT"]) for r in stair_old)
    A_new_blk = by_lane[RR.GROUND_SLAB_CANDIDATE]
    A_excl_new = (by_lane[RR.LIFT_PIT_OPENING] + by_lane[RR.STRUCTURAL_BEAM_OR_WALL] +
                  by_lane[RR.STAIR_OR_SPECIAL_STRUCTURE] + by_lane[RR.OUTSIDE_BUILDING])
    A_uncl = by_lane[RR.CLASSIFICATION_BLOCKED]
    A_face = _m2(rec["domain"].area)                    # exact polygon area (S1 prints the face to 6 decimals)
    domain = A_meas + A_blk_old + A_stair_old + A_face
    lanes = {"MEASURED": A_meas, "BLOCKED": A_blk_old + A_new_blk, "EXCLUDED": A_stair_old + A_excl_new,
             "CONFLICTED": 0.0, "UNCLASSIFIED": A_uncl}
    check(abs(math.fsum(lanes.values()) - domain) < 1e-6, "domain = measured + blocked + excluded + conflicted")
    check(abs(A_meas - s81_summary["included_area_m2"]) < 1e-9 and abs(A_blk_old - s81_summary["blocked_area_m2"]) < 1e-6,
          "the S8.1 measured and blocked areas are unchanged")
    acct = [
        {"ITEM": "S8.1 measured zones", "SOURCE": "S8.1 01 / 08 (frozen)", "CELLS": len(meas), "AREA_M2": A_meas,
         "STATE": "MEASURED (S8.1 PROJECT_BASIS_QTO)", "QUANTITY": "S8.1 frozen: 3.785852 m3, 233.694587 kg"},
        {"ITEM": "S8.1 blocked faces", "SOURCE": "S8.1 01 / 06 (frozen)", "CELLS": len(blk), "AREA_M2": A_blk_old,
         "STATE": "BLOCKED_UNQUANTIFIED", "QUANTITY": "none (unknown, not zero)"},
        {"ITEM": "recovered ground-slab candidates", "SOURCE": "this round 01", "CELLS": len(cand), "AREA_M2": A_new_blk,
         "STATE": "BLOCKED_UNQUANTIFIED", "QUANTITY": "none (unknown, not zero)"},
        {"ITEM": "revised blocked ground-slab area", "SOURCE": "sum", "CELLS": len(blk) + len(cand),
         "AREA_M2": A_blk_old + A_new_blk, "STATE": "BLOCKED_UNQUANTIFIED", "QUANTITY": "none"},
        {"ITEM": "remaining unclassified area", "SOURCE": "this round 01", "CELLS":
            sum(1 for p in parts if p["LANE"] == RR.CLASSIFICATION_BLOCKED), "AREA_M2": A_uncl,
         "STATE": "CLASSIFICATION_BLOCKED", "QUANTITY": "none"}]
    recon = [
        {"VIEW": "OLD_S8_1", "LANE": "MEASURED", "RECORDS": len(meas), "AREA_M2": A_meas, "NOTE": "two marker cells"},
        {"VIEW": "OLD_S8_1", "LANE": "BLOCKED", "RECORDS": len(blk), "AREA_M2": A_blk_old, "NOTE": "19 faces"},
        {"VIEW": "OLD_S8_1", "LANE": "EXCLUDED", "RECORDS": len(stair_old), "AREA_M2": A_stair_old,
         "NOTE": "stair flight SP-GBP-12 (S8 STAIR)"},
        {"VIEW": "OLD_S8_1", "LANE": "NOT_REPRESENTED", "RECORDS": 1, "AREA_M2": A_face,
         "NOTE": f"face {rec['unfaced']['face_id']} rejected by S1 at the strip gate (line "
                 f"{rec['unfaced']['strip_line']})"}]
    for lane in ("MEASURED", "BLOCKED", "EXCLUDED", "CONFLICTED", "UNCLASSIFIED"):
        recon.append({"VIEW": "NEW_S8_1A", "LANE": lane, "RECORDS": None, "AREA_M2": lanes[lane],
                      "NOTE": {"MEASURED": "unchanged", "BLOCKED": "19 S8.1 faces + recovered candidates",
                               "EXCLUDED": "both stair zones, pit opening, pit walls, beam bands",
                               "CONFLICTED": "the cover record is corrected to unresolved (06)",
                               "UNCLASSIFIED": "parts with no determinable identity"}[lane]})
    recon.append({"VIEW": "NEW_S8_1A", "LANE": "DRAWN_GROUND_SLAB_DOMAIN", "RECORDS": None, "AREA_M2": domain,
                  "NOTE": "all GBP cells inside the building: S8.1 faces + SP-GBP-12 + the recovered face"})
    gates = defaultdict(lambda: [0, 0.0])
    for d in rep["disp"]:
        k = "RECOVERED_THIS_ROUND" if d["face_id"] == rec["unfaced"]["face_id"] else d["gate"]
        gates[k][0] += 1
        gates[k][1] += d["area_m2"]
    tot_T = math.fsum(d["area_m2"] for d in rep["disp"])
    for k in sorted(gates):
        recon.append({"VIEW": "GBP_ARRANGEMENT", "LANE": k, "RECORDS": gates[k][0], "AREA_M2": gates[k][1],
                      "NOTE": "every face of S1's GBP planar arrangement, by S1's own gate"})
    recon.append({"VIEW": "GBP_ARRANGEMENT", "LANE": "TOTAL", "RECORDS": len(rep["disp"]), "AREA_M2": tot_T,
                  "NOTE": "sum over all faces"})
    check(abs(math.fsum(v[1] for v in gates.values()) - tot_T) < 1e-9, "the arrangement accounting closes")

    # ---------------------------------------------------------- conservation checks
    from shapely.ops import unary_union
    polys = [p["_poly"] for p in parts]
    gs_polys = [p["_poly"] for p in cand]
    pit_polys = [p["_poly"] for p in parts if p["LANE"] == RR.LIFT_PIT_OPENING]
    stair_polys = [p["_poly"] for p in parts if p["LANE"] == RR.STAIR_OR_SPECIAL_STRUCTURE]
    beam_polys = [p["_poly"] for p in parts if p["KIND"] == "BEAM"]
    from shapely.geometry import Polygon as _Poly
    s81_faces = [_Poly(json.loads(r["POLYGON_MM"])) for r in s81_poly.values() if r["ROW_KIND"] == "FACE"]
    stair12 = [_Poly(json.loads(r["POLYGON_MM"])) for r in stair_old]

    def ov(a, b):
        return math.fsum(x.intersection(y).area for x in a for y in b) / 1e6
    tread_in_gs = [t for t in ev["treads"] for g in gs_polys if g.contains(t[1].interpolate(0.5, normalized=True))]
    from shapely.geometry import Point as _Pt
    ext_markers = sorted(m["handle"] for m in tt["markers"] for g in gs_polys if g.intersects(_Pt(m["circle_centre"])))
    pit_alone_s1 = [i for i, q in enumerate(rec["_s1_only"]) for g in pit_polys if q.symmetric_difference(g).area < 1.0]
    cons = [
        ("CS-01", "every recovered part has one lane and one owner", len(parts) == len({p["PART_ID"] for p in parts}),
         {p["PART_ID"]: p["OWNER"] for p in parts}),
        ("CS-02", "the recovered parts tile the unfaced face exactly once", rec["proof"]["exact"],
         {k.replace("_mm2", "_m2"): _full(v / 1e6, 9) if isinstance(v, float) else v
          for k, v in rec["proof"].items()}),
        ("CS-03", "no recovered part overlaps an S8.1 face or SP-GBP-12", ov(polys, s81_faces + stair12) < 1e-6,
         {"overlap_m2": ov(polys, s81_faces + stair12)}),
        ("CS-04", "every genuine ground-slab region has one ground-slab owner",
         all(p["OWNER"] == PARENT for p in cand) and ov(gs_polys, gs_polys) - math.fsum(g.area for g in gs_polys) / 1e6
         < 1e-6, {"owner": PARENT, "cells": [p["PART_ID"] for p in cand]}),
        ("CS-05", "every lift-pit opening is owned by the lift / pit system",
         len(pit_polys) == 1 and all(p["OWNER"] == LIFT for p in parts if p["LANE"] == RR.LIFT_PIT_OPENING),
         {"owner": LIFT, "pit_m2": _m2(math.fsum(g.area for g in pit_polys))}),
        ("CS-06", "no stair flight is counted as ground slab", not tread_in_gs and ov(gs_polys, stair_polys + stair12) == 0,
         {"stair_zones": [p["PART_ID"] for p in parts if p["LANE"] == RR.STAIR_OR_SPECIAL_STRUCTURE] + ["SP-GBP-12"]}),
        ("CS-07", "no ground-beam concrete is duplicated: beam bands stay with the ground beams",
         ov(gs_polys, beam_polys) == 0 and all("GROUND_BEAM" in p["OWNER"] for p in parts if p["KIND"] == "BEAM"),
         {p["PART_ID"]: p["EVIDENCE"].get("evidence_id") for p in parts if p["KIND"] == "BEAM"}),
        ("CS-08", "unmeasured candidate slab area is registered as blocked",
         {b["SUBJECT"] for b in new_blocked} == {p["PART_ID"] for p in cand}, {"blocked_records": len(new_blocked)}),
        ("CS-09", "an architectural opening is not treated as a structural slab; the pit opening is structural "
                  "(S-BW outline, ANSI37 wall hatch island, P14-LIFT)",
         all(not any(w in " ".join(p["ARCH_GF_LABELS"]).upper() for w in OPENING_WORDS) for p in cand),
         {p["PART_ID"]: p["ARCH_GF_LABELS"] for p in cand}),
        ("CS-10", "source annotations are not extended beyond their proven scope",
         not ext_markers and all(b["LANE"] == "BLOCKED_UNQUANTIFIED" and b["KG"] is None and b["M3"] is None
                                 for b in new_blocked)
         and all(p["STATE"] == "BLOCKED_NO_SOURCE_THICKNESS_OR_MESH" for p in cand)
         and {i["INTERPRETATION_ID"]: i["STATUS"] for i in tt["interpretations"]}["VERDICT"]
         == "ANNOTATION_SCOPE_NOT_ESTABLISHED",
         {"tt1_verdict": "ANNOTATION_SCOPE_NOT_ESTABLISHED", "markers_in_recovered_cells": ext_markers,
          "new_records_with_kg_or_m3": sum(1 for b in new_blocked if b["KG"] is not None or b["M3"] is not None),
          "marker_cells": sorted(m["circle_within"][0] for m in tt["markers"])}),
        ("CS-11", "domain = measured + blocked + excluded + conflicted (+ unclassified)",
         abs(math.fsum(lanes.values()) - domain) < 1e-6, {k: _full(v, 9) for k, v in {**lanes, "DOMAIN": domain}.items()}),
        ("CS-12", "the 21-face S8.1 census is retained and linked, not rewritten",
         sum(1 for d in delta if d["ACTION"] == "LINK_UNCHANGED") == len(s81_poly) and len(meas) + len(blk) == 21
         and frozen["S8.1"]["files_checked"] > 0,
         {"rows_linked": sum(1 for d in delta if d["ACTION"] == "LINK_UNCHANGED"),
          "ground_slab_faces": len(meas) + len(blk), "measured": len(meas), "blocked": len(blk),
          "other_rows": sorted(r["ROW_ID"] for r in stair_old + outside),
          "s8_1_manifest": "hash-verified (11)"}),
        ("CS-13", "S8.1 frozen quantities unchanged", True,
         {"concrete_m3": s81_summary["concrete_m3"], "total_kg": s81_summary["total_kg"]}),
        ("CS-14", "S1's own edge layers do not close the pit: without the S-BW outlines the face splits into fewer "
                  "parts and the pit opening is not a part of its own",
         len(rec["s1_only_parts"]) < len(parts) and not pit_alone_s1,
         {"parts_without_S-BW": len(rec["s1_only_parts"]), "parts_with_S-BW": len(parts),
          "pit_opening_is_a_part_without_S-BW": bool(pit_alone_s1)})]
    cons_rows = [{"CHECK_ID": a, "CHECK": b, "RESULT": "PASS" if c else "FAIL", "EVIDENCE": d} for a, b, c, d in cons]
    check(all(r["RESULT"] == "PASS" for r in cons_rows), f"conservation checks: {[r for r in cons_rows if r['RESULT'] != 'PASS']}")

    # ---------------------------------------------------------- questions
    qs = [
        {"ID": "Q-S8.1A-01", "KIND": "ANNOTATION_SCOPE", "TO": "structural engineer",
         "QUESTION": "Do the two 'T=10cm / 5Ø10/m E.W.' callouts on the ground-beams plan apply only to the cells that "
                     "hold them, or to other ground-slab cells?",
         "BLOCKS_AREA_M2": A_blk_old + A_new_blk, "STATUS": "OPEN (revisit only on new source evidence or a consultant "
                                                            "clarification)"},
        {"ID": "Q-S8.1A-02", "KIND": "CONTACT_CONDITION", "TO": "structural engineer",
         "QUESTION": "What is the ground slab cast on (soil, compacted fill, blinding, membrane), and which cover in "
                     "note 22 governs its underside?",
         "BLOCKS_AREA_M2": A_meas, "STATUS": "OPEN (no quantity effect on the face-to-face mesh run)"},
        {"ID": "Q-S8.1A-03", "KIND": "POPULATION", "TO": "S8 stair family",
         "QUESTION": "The recovered stair bay (+0.30 / +1.00 marks, two tread sets) is a second ground-level stair not "
                     "in the PRE-S8 census; its flight and landing extents are not drawn as closed outlines.",
         "BLOCKS_AREA_M2": by_lane[RR.STAIR_OR_SPECIAL_STRUCTURE], "STATUS": "OPEN (stair family, not ground slab)"},
        {"ID": "Q-S8.1A-04", "KIND": "ANNOTATION", "TO": "drawing review",
         "QUESTION": "The two '******' S-TEXT marks (165A, 165B) beside the stair zones carry no stated meaning.",
         "BLOCKS_AREA_M2": 0.0, "STATUS": "OPEN (no quantity effect)"},
        {"ID": "Q-S8.1A-05", "KIND": "LIFT_PIT", "TO": "lift supplier / engineer",
         "QUESTION": "Pit depth is 'by the lift manufacturer' (P14-LIFT): needed by the lift-pit family, not by the "
                     "ground slab.", "BLOCKS_AREA_M2": 0.0, "STATUS": "OPEN (lift-pit family)"}]
    conflicts = [{"ID": "CF-S8.1A-01", "KIND": "SOURCE_CONFLICT_RECLASSIFIED", "TO": "this round",
                  "QUESTION": "S8.1 recorded the cover note as a SOURCE_CONFLICT; it is a conditional dimensional "
                              "conflict that holds only for a slab cast against soil (06).",
                  "BLOCKS_AREA_M2": 0.0, "STATUS": "CORRECTED to COVER_APPLICABILITY_UNRESOLVED"}]

    # ---------------------------------------------------------- outputs
    part_rows = [{k: v for k, v in p.items() if not k.startswith("_")} for p in parts]
    _csv(OUTPUTS[1], part_rows, list(part_rows[0]))
    _csv(OUTPUTS[2], delta, list(delta[0]))
    _csv(OUTPUTS[3], tt["audit"], list(tt["audit"][0]))
    _csv(OUTPUTS[4], tt["interpretations"], list(tt["interpretations"][0]))
    _csv(OUTPUTS[5], cov["rows"], list(cov["rows"][0]))
    _csv(OUTPUTS[6], corr, list(corr[0]))
    _csv(OUTPUTS[7], acct + [{"ITEM": b["BLOCKED_ID"], "SOURCE": "this round: component record (repeats its cell's "
                                                             "area; not additive)", "CELLS": 1, "AREA_M2": b["AREA_M2"],
                              "STATE": b["LANE"], "QUANTITY": "none"} for b in new_blocked],
         ["ITEM", "SOURCE", "CELLS", "AREA_M2", "STATE", "QUANTITY"])
    _csv(OUTPUTS[8], qs + conflicts, list(qs[0]))
    _csv(OUTPUTS[9], cons_rows, list(cons_rows[0]))
    _csv(OUTPUTS[10], recon, list(recon[0]))
    fr_rows = [{"STAGE": k, "MANIFEST": v["manifest"], "MANIFEST_SHA256": v["manifest_sha256"],
                "FILES_CHECKED": v["files_checked"], "ENGINE_STAMP": v["engine_commit_stamp"], "RESULT": "MATCH"}
               for k, v in frozen.items()]
    _csv(OUTPUTS[11], fr_rows, list(fr_rows[0]))
    prov = []
    for p in parts:
        prov.append({"record": p["PART_ID"], "lane": p["LANE"], "source": "ST7757.dxf", "drawing_sha256": DXF_SHA,
                     "sheet": SHEET, "parent_face": p["PARENT_FACE"], "boundary_sources": p["BOUNDARY_SOURCES"],
                     "evidence": p["EVIDENCE"], "levels": p["LEVEL_MARKS"],
                     "architecture": {"labels": p["ARCH_GF_LABELS"], "drawing_sha256": ARCH_SHA,
                                      "registration": "PS5.1 translation_arch_to_gbp"}})
    for m in tt["markers"]:
        prov.append({"record": f"TT1 {m['handle']}", "lane": "ANNOTATION", "source": "ST7757.dxf",
                     "drawing_sha256": DXF_SHA, "sheet": SHEET, "evidence": m})
    (HERE / OUTPUTS[12]).write_text("".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in prov),
                                    encoding="utf-8")
    summary = {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "issue": "S8.1-PF-01 (unfaced region round lift pit 7BE) + TT1 scope + P8-N22 cover",
        "root_cause": {"face": rec["unfaced"]["face_id"], "area_m2": rec["unfaced"]["area_m2"],
                       "thickness_m": rec["unfaced"]["thickness_m"],
                       "interior_point": _r3(rec["unfaced"]["interior_point"]),
                       "s1_gate": rec["unfaced"]["gate"], "s1_strip_line": rec["unfaced"]["strip_line"],
                       "why": "S1 tests one interior point per face; this face's point fell in an open-ended ground-"
                              "beam band, so the whole face was dropped as a beam strip. The S-BW pit outlines that "
                              "close those bands were not S1 face edges."},
        "recovered_gross_m2": A_face,
        "recovered_by_lane_m2": dict(sorted(by_lane.items())),
        "recovered_parts": len(parts),
        "confirmed_slab_area_m2": 0.0,
        "candidate_slab_area_m2": A_new_blk, "candidate_cells": [p["PART_ID"] for p in cand],
        "lift_pit_opening_m2": by_lane[RR.LIFT_PIT_OPENING],
        "excluded_structural_m2": by_lane[RR.STRUCTURAL_BEAM_OR_WALL],
        "excluded_stair_m2": by_lane[RR.STAIR_OR_SPECIAL_STRUCTURE],
        "unclassified_m2": A_uncl,
        "revised_blocked_ground_slab_m2": A_blk_old + A_new_blk,
        "domain_m2": domain, "domain_lanes_m2": lanes,
        "tt1_verdict": "ANNOTATION_SCOPE_NOT_ESTABLISHED", "tt1_pdf_symbol_groups": tt["pdf_groups"],
        "cover_verdict": "COVER_APPLICABILITY_UNRESOLVED", "contact_condition": "CONTACT_CONDITION_UNRESOLVED",
        "cover_fit_mm": {k: v for k, v in cov["fits"].items()},
        "s8_1_quantities": {"concrete_m3": s81_summary["concrete_m3"], "total_kg": s81_summary["total_kg"],
                            "x_kg": s81_summary["x_kg"], "y_kg": s81_summary["y_kg"], "changed": False},
        "blocked_records": {"s8_1": len(s81_blocked), "new": len(new_blocked),
                            "lanes_after_correction": {"BLOCKED_UNQUANTIFIED": len(s81_blocked) + len(new_blocked),
                                                       "SOURCE_CONFLICT": 0}},
        "conservation": {r["CHECK_ID"]: r["RESULT"] for r in cons_rows},
        "frozen_baselines": {k: v["manifest_sha256"] for k, v in frozen.items()},
        "released_quantity": None, "references_read": []}
    _json(OUTPUTS[13], summary)
    (HERE / OUTPUTS[0]).write_text(readme(summary, parts, tt, cov), encoding="utf-8")
    manifest = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "FROZEN_NO_QUANTITY_RELEASED",
                "engine_commit_stamp": summary["engine_commit"], "references_read": [],
                "code": {c: _sha(ROOT / c) for c in CODE},
                "inputs": {str(Path(v).relative_to(ROOT)): _sha(v) for v in P.values()} |
                          {f"research/alsenan_structural_census_s1/{r}.json": _sha(S1 / f"{r}.json") for r in S1_REGS},
                "drawing_sha256": {"ST7757.dxf": DXF_SHA, "P7757.dxf": ARCH_SHA, "ST7757.pdf": PDF_SHA},
                "frozen_baselines": summary["frozen_baselines"],
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
                "rule": "S8.1A recovers population, scope and cover authority only; no steel or concrete is released "
                        "and no S8.1 file changes"}
    _json(MANIFEST_NAME, manifest)
    return summary


def readme(s, parts, tt, cov):
    L = ["# S8.1A: ground-slab population recovery and cover-authority audit", "",
         f"Baseline `{s['baseline']}`. This round releases **no** steel or concrete. S8.1 stays at "
         f"{s['s8_1_quantities']['concrete_m3']:.6f} m3 and {s['s8_1_quantities']['total_kg']:.6f} kg, and no S8.1 "
         "file changes.", "",
         "## Root cause of S8.1-PF-01", "",
         f"S1 tests one interior point per face. Face `{s['root_cause']['face']}` "
         f"({s['root_cause']['area_m2']:.4f} m2) passes S1's area and thickness gates. Its point "
         f"{s['root_cause']['interior_point']} falls in ground-beam band `{s['root_cause']['s1_strip_line']}`, so S1 "
         "dropped the whole face as a beam strip. The S-BW pit outlines close that band, but S1 did not use them as "
         "face edges.", "",
         "## Recovered region", "",
         "| part | lane | kind | m2 | owner |", "|---|---|---|---|---|"]
    for p in parts:
        L.append(f"| {p['PART_ID']} | {p['LANE']} | {p['KIND']} | {p['AREA_M2']:.4f} | {p['OWNER']} |")
    L += ["", f"Gross {s['recovered_gross_m2']:.4f} m2. Candidate slab {s['candidate_slab_area_m2']:.4f} m2 (blocked: "
              "no thickness or mesh). Confirmed slab 0 m2. Lift-pit opening "
              f"{s['lift_pit_opening_m2']:.4f} m2. Structural {s['excluded_structural_m2']:.4f} m2. Stair zone "
              f"{s['excluded_stair_m2']:.4f} m2. Unclassified {s['unclassified_m2'] * 1e6:.2f} mm2 (" +
              "; ".join(f"{q['PART_ID']}: {q['KIND'].lower()} on {', '.join(q['BOUNDARY_SOURCES'])}" for q in parts
                        if q["LANE"] == RR.CLASSIFICATION_BLOCKED) + ", kept as CLASSIFICATION_BLOCKED).", "",
          "## TT1 scope", "", f"Verdict: **{s['tt1_verdict']}**. The two-cell S8.1 measurement is kept as a versioned "
                              "Urban project-basis interpretation (I1). It is not presented as the only possible "
                              "project interpretation (04).", "",
          "## Cover", "", f"Contact: **{s['contact_condition']}**. Verdict: **{s['cover_verdict']}**. E.W. is one mesh "
                          "of two crossing directions. A 100 mm slab cast against soil would need 70 + 10 + 10 + 25 = "
                          "115 mm. Off soil it needs 25 + 10 + 10 + 25 = 70 mm. Neither contact case is established, "
                          "so S8.1's SOURCE_CONFLICT is corrected to unresolved in the correction layer (06). No bar "
                          "level is invented.", "",
          "## Conservation", "",
          f"Drawn ground-slab domain {s['domain_m2']:.6f} m2 = " +
          " + ".join(f"{k.lower()} {v:.6f}" for k, v in s["domain_lanes_m2"].items()) + ".", "",
          "Outputs 01-13 and the freeze manifest 14 are listed in the manifest."]
    return "\n".join(L) + "\n"


def main():
    try:
        s = build()
    except Stop as e:
        raise SystemExit(f"STOP: {e}")
    print(json.dumps({k: s[k] for k in ("recovered_gross_m2", "candidate_slab_area_m2", "lift_pit_opening_m2",
                                        "excluded_structural_m2", "excluded_stair_m2", "unclassified_m2",
                                        "revised_blocked_ground_slab_m2", "domain_m2", "tt1_verdict",
                                        "cover_verdict")}, indent=1))


if __name__ == "__main__":
    main()
