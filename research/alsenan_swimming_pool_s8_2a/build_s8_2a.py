"""S8.2A - architectural elevation source recovery and pool depth authority (correction layer on frozen S8.2).

    python3 -I research/alsenan_swimming_pool_s8_2a/build_s8_2a.py

S8.2 is frozen and never written. This layer adds the architectural evidence S8.2 did not hold:
  * the re-supplied architectural PDFs (pages 01-06 and 07-12), registered as additional sources and compared with
    the earlier registered PDFs byte for byte;
  * the NORTH WEST ELEVATION, read as vector geometry from the registered architectural DXF (P7757.dxf), with the
    scanned sheet 08 as the same drawing;
  * the plan dimensions and labels round the pool in the same DXF.
It decides what the elevation's '115' and '70' measure, which pool levels that establishes, and what it changes for
every S8.2 concrete row and bar family. A quantity is released only where geometry, dimensional scope and ownership
are all established. No earlier pool quantity, contractor estimate or third-party figure is read.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
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
from engine.source import elevation_binding as EB  # noqa: E402
from engine.source import source_identity as SI  # noqa: E402

ROUND = "S8_2A"
DATE = "2026-10-09"
BASELINE_HEAD = "3286056"
POLICY = "S8_2A_ARCH_ELEVATION_DEPTH_AUTHORITY_V1"
R = ROOT / "research"
S82 = R / "alsenan_swimming_pool_s8_2"
BY_SHA = ROOT / "data/inputs/by_sha256"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
ARCH = BY_SHA / f"{ARCH_SHA}.dxf"
STRUCT_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
NEW_PDFS = {"ARCH_PART_1_PAGES_01-06": "cd3b8669d55998cb638bd8e2b572da4992ed64babcecacd73753d6a2f0c68b97",
            "ARCH_PART_2_PAGES_07-12": "1e7087d3e61bbb682c9107193c97550a2837e5198bde0ee311319bf7f4a08459"}
EARLIER_NAME = {"ARCH_PART_1_PAGES_01-06": "P7757_Architectural_Plan_Pages_01-06.pdf",
                "ARCH_PART_2_PAGES_07-12": "P7757_Architectural_Plan_Pages_07-12.pdf"}
SOURCE_MANIFEST = ROOT / "tests/alsenan/registers/SOURCE_MANIFEST.json"
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
             "S8.2": S82 / "18_S8_2_FREEZE_MANIFEST.json"}
S82_READ = ["17_S8_2_SUMMARY.json", "02_POOL_POPULATION_AND_OWNERSHIP.csv", "03_CONCRETE_GEOMETRY_AND_QTO.csv",
            "04_BASE_REINFORCEMENT_QTO.csv", "05_WALL_REINFORCEMENT_QTO.csv", "13_REBAR_EVIDENCE_BINDING.csv",
            "16_CONFLICT_AND_QUESTION_REGISTER.csv"]
CODE = ["engine/source/elevation_binding.py", "engine/source/source_identity.py", "engine/source/delta_release.py",
        "research/alsenan_swimming_pool_s8_2a/build_s8_2a.py", "research/alsenan_swimming_pool_s8_2/build_s8_2.py",
        "engine/source/pool_qto.py", "engine/source/ground_slab_qto.py", "engine/source/slab_rebar_qto.py",
        "engine/source/rebar_unit_mass.py", "research/external_engine_lab/alsenan_structural_s1.py",
        "engine/source/legacy_text.py"]
OUTPUTS = ["00_README.md", "01_ARCH_PDF_IDENTITY_COMPARISON.csv", "02_ELEVATION_TO_PLAN_BINDING_AUDIT.csv",
           "03_DIMENSION_SOURCE_REGISTER.csv", "04_POOL_DEPTH_AND_ZONE_INTERPRETATION.csv",
           "05_QUANTITY_READINESS_DELTA.csv", "06_BLOCKED_REGISTER_DELTA.csv",
           "07_CONFLICT_AND_QUESTION_REGISTER_DELTA.csv", "08_SENSITIVITY_CASES.csv", "09_CONSERVATION_CHECKS.csv",
           "10_PROVENANCE.jsonl", "11_S8_2A_SUMMARY.json"]
MANIFEST_NAME = "12_S8_2A_FREEZE_MANIFEST.json"

# ------------------------------------------------------------------ the NW elevation in P7757.dxf (arch model space)
ELEV_TITLE = "NORTH WEST ELEVATION"
ELEV_WINDOW = 16000.0                   # half width of the elevation's dimension window about its title (mm)
DATUM_DIM = "29EE"                      # '100': ±0.00 -> +1.00 (the house ground-floor level)
TOTAL_DIM = "2A26"                      # '1440' from ±0.00
DEPTH_DIM, STEP_DIM, GLAZING_DIM = "2E5E", "2E6C", "2E7A"     # '115', '70', '430'
PIT_WINDOW = (-367500.0, -361000.0, -806600.0, -804000.0)     # x0, x1, y0, y1 round the sunken element
PLAN_DIMS = {"LENGTH_350": "6A1", "WIDTH_350": "4C4", "PLAN_115": "4D0", "GAP_50": "696", "CURVED_WALL_20": "689"}
POOL_LABEL = "swimming pool"
OTHER_PIT_WORDS = re.compile(r"\b(lift|elevator|pit|tank|sump|manhole)\b", re.I)
# scanned sheets: what was read on the upright page image in this session (crops are client drawing, kept out of git)
VISUAL = [
    {"ID": "VR-01", "PDF": "ARCH_PART_2_PAGES_07-12", "PAGE": 2, "SHEET": "NORTH WEST ELEVATION 1:100",
     "BOX_UPRIGHT_PX": [3700, 3300, 4300, 3800], "READ": "sunken box below the hatched ground; vertical chain "
     "'115' (box top to inner floor) then '70' (box top to the base of the curved element) then '430'; '+0.15' "
     "level tip on the deck surface right of the box, the box walls rising above it",
     "SCALE_CHECK": "the '115' witnesses ~181 px apart = 1.574 px/cm, the nominal 1:100 of a 4672 px A3 scan"},
    {"ID": "VR-02", "PDF": "ARCH_PART_1_PAGES_01-06", "PAGE": 3, "SHEET": "GROUND FLOOR PLAN 1:100",
     "BOX_UPRIGHT_PX": [4700, 1050, 6000, 2400], "READ": "D-shaped 'swimming pool / حمام سباحة' 350 x 350 at the sea-view "
     "end beside the MASTER BED ROOM, inside a curved wall (gap 50, wall 20); '+0.15' level marks round it; a "
     "horizontal '115' from the pool face to a return wall (plan dimension, not a depth)",
     "SCALE_CHECK": ""},
    {"ID": "VR-03", "PDF": "ARCH_PART_1_PAGES_01-06", "PAGE": 3, "SHEET": "GROUND FLOOR PLAN 1:100",
     "BOX_UPRIGHT_PX": [900, 150, 1500, 700], "READ": "north arrow pointing to the page's lower right: street side = "
     "south-east (sheet 06 SOUTH EAST ELEVATION), sea-view side = north-west (sheet 08)", "SCALE_CHECK": ""},
    {"ID": "VR-04", "PDF": "ARCH_PART_2_PAGES_07-12", "PAGE": 1, "SHEET": "SOUTH WEST ELEVATION 1:100",
     "BOX_UPRIGHT_PX": None, "READ": "no sunken element drawn", "SCALE_CHECK": ""},
    {"ID": "VR-05", "PDF": "ARCH_PART_2_PAGES_07-12", "PAGE": 3, "SHEET": "NORTH EAST ELEVATION 1:100",
     "BOX_UPRIGHT_PX": None, "READ": "no sunken element drawn (the pool is on the far side)", "SCALE_CHECK": ""},
    {"ID": "VR-06", "PDF": "ARCH_PART_2_PAGES_07-12", "PAGE": 4, "SHEET": "SECTION A-A 1:100",
     "BOX_UPRIGHT_PX": None, "READ": "cuts the stair core; no pool", "SCALE_CHECK": ""},
    {"ID": "VR-07", "PDF": "ARCH_PART_2_PAGES_07-12", "PAGE": 5, "SHEET": "SECTION B-B 1:100",
     "BOX_UPRIGHT_PX": None, "READ": "cuts the middle of the plot, clear of the pool; no pool", "SCALE_CHECK": ""},
    {"ID": "VR-08", "PDF": "ARCH_PART_2_PAGES_07-12", "PAGE": 6, "SHEET": "FENCE PLAN / ELEVATION / SECTION",
     "BOX_UPRIGHT_PX": None, "READ": "no pool", "SCALE_CHECK": ""},
    {"ID": "VR-09", "PDF": "ALL", "PAGE": None, "SHEET": "title blocks",
     "BOX_UPRIGHT_PX": None, "READ": "owner, plot number, parcel and area fields only; no consultant name, no "
     "revision, no issue date on any sheet; the only date is the plot stamp on sheet 03 (May 06, 2026 11:21, "
     "P7757.dwg, A008-PC; its folder path carries a personal name, not reproduced)", "SCALE_CHECK": ""}]


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


# ------------------------------------------------------------------ inputs
def verify_inputs():
    absent = [p.name for p in [ARCH, BY_SHA / f"{STRUCT_SHA}.dxf"] + [BY_SHA / f"{s}.pdf" for s in NEW_PDFS.values()]
              if not p.exists()]
    check(not absent, f"private inputs not in data/inputs/by_sha256 (never committed): {absent}")
    frozen = {k: DR.verify_frozen(m, ROOT) for k, m in MANIFESTS.items()}
    m82 = _j(MANIFESTS["S8.2"])
    check(m82["state"] == "FROZEN_BEFORE_COMPARISON" and m82["references_read"] == [], "S8.2 frozen before comparison")
    for o in S82_READ:
        check(m82["outputs"][o] == _sha(S82 / o), f"S8.2 {o} is the frozen output")
    check(_sha(ARCH) == ARCH_SHA, "architectural DXF unchanged")
    for k, s in NEW_PDFS.items():
        check(_sha(BY_SHA / f"{s}.pdf") == s, f"{k} unchanged")
    return frozen


# ------------------------------------------------------------------ 01 PDF identity
def _page_images(b):
    from pypdf import PdfReader
    out = []
    for i, p in enumerate(PdfReader(io.BytesIO(b)).pages, 1):
        found = []

        def walk(o):
            o = o.get_object()
            if o.get("/Subtype") == "/Image":
                found.append((int(o["/Width"]), int(o["/Height"]), str(o.get("/Filter")), hashlib.sha256(o._data).hexdigest()))
            elif o.get("/Subtype") == "/Form":
                for v in o.get("/Resources", {}).get("/XObject", {}).values():
                    walk(v)
        for v in p["/Resources"].get("/XObject", {}).values():
            walk(v)
        out.append({"page": i, "size_pt": [float(x) for x in p.mediabox[2:]], "text_chars": len(p.extract_text() or ""),
                    "images": found})
    return out


def pdf_identity():
    man = {o["file"]: o for o in _j(SOURCE_MANIFEST)["files"]} if "files" in _j(SOURCE_MANIFEST) else {}
    if not man:
        def objs(o):
            if isinstance(o, dict):
                yield o
                for v in o.values():
                    yield from objs(v)
            elif isinstance(o, list):
                for v in o:
                    yield from objs(v)
        man = {o["file"]: o for o in objs(_j(SOURCE_MANIFEST)) if isinstance(o.get("file"), str) and "sha256" in o}
    rows, pages, ident = [], [], {}
    from pypdf import PdfReader
    for key, sha in NEW_PDFS.items():
        b = (BY_SHA / f"{sha}.pdf").read_bytes()
        earlier = man[EARLIER_NAME[key]]
        rel = SI.relation(b, earlier["sha256"])
        meta = {k: str(v) for k, v in (PdfReader(io.BytesIO(b)).metadata or {}).items()}
        imgs = _page_images(b)
        restored = BY_SHA / f"{earlier['sha256']}.pdf"
        restored_ok = restored.exists() and _sha(restored) == earlier["sha256"]
        same_census = (len(imgs) == earlier["pages"] and all(
            [list(im[:2]) for im in pg["images"]] == c["image_px"] and pg["text_chars"] == c["text_chars"] == 0
            for pg, c in zip(imgs, earlier["page_census"])))
        ident[key] = {"relation": rel["relation"], "earlier_sha256": earlier["sha256"]}
        rows.append({"SOURCE_KEY": key, "NEW_SHA256": sha, "NEW_BYTES": len(b), "EARLIER_FILE": EARLIER_NAME[key],
                     "EARLIER_SHA256": earlier["sha256"], "EARLIER_BYTES": earlier["bytes"],
                     "BYTE_DELTA": len(b) - earlier["bytes"], "RELATION": rel["relation"],
                     "REMOVED_INFO_BYTES": rel["removed_bytes"], "RECONSTRUCTED_SHA256": rel["reconstructed_sha256"],
                     "NEW_METADATA": meta, "PAGES": len(imgs), "PAGE_CENSUS_MATCHES_EARLIER": same_census,
                     "EARLIER_RESTORED_ON_DISK": restored_ok, "EARLIER_SHEETS": earlier.get("pdf_sheets"),
                     "LANE": "RASTER (one 4672 x 6624 JPEG per page; no text or vector layer)",
                     "REGISTERED_AS": "ADDITIONAL_SOURCE (not a replacement): same drawing content as the earlier file"})
        for pg in imgs:
            pages.append({"SOURCE_KEY": key, "PAGE": pg["page"], "SHEET": (earlier.get("pdf_sheets") or [None] * 6)[pg["page"] - 1],
                          "SIZE_PT": pg["size_pt"], "IMAGE_PX": [im[:2] for im in pg["images"]],
                          "IMAGE_FILTER": [im[2] for im in pg["images"]],
                          "IMAGE_SHA256": [im[3] for im in pg["images"]], "TEXT_CHARS": pg["text_chars"]})
    return rows, pages, ident


# ------------------------------------------------------------------ 02/03 the elevation and the plan (vector)
def _dim_rows(doc, keep):
    out = {}
    for d in doc.modelspace().query("DIMENSION"):
        p2, p3 = d.dxf.get("defpoint2"), d.dxf.get("defpoint3")
        if p2 is None or p3 is None or not keep(d, p2, p3):
            continue
        blk = doc.blocks.get(d.dxf.geometry) if d.dxf.get("geometry") else None
        shown = [(x.plain_text() if x.dxftype() == "MTEXT" else x.dxf.text) for x in blk
                 if x.dxftype() in ("MTEXT", "TEXT")] if blk else []
        out[d.dxf.handle] = {"handle": d.dxf.handle, "text": " ".join(s.strip() for s in shown),
                             "measurement_mm": round(d.get_measurement(), 3), "p2": (p2.x, p2.y), "p3": (p3.x, p3.y),
                             "layer": d.dxf.layer}
    return out


def elevation(doc):
    from ezdxf import disassemble
    ents = list(disassemble.recursive_decompose(doc.modelspace()))
    titles = [e for e in ents if e.dxftype() in ("TEXT", "MTEXT") and ELEV_TITLE in
              (e.dxf.text if e.dxftype() == "TEXT" else e.plain_text()).upper()]
    check(len(titles) == 1, "one NORTH WEST ELEVATION title in the architectural DXF")
    tx, ty = titles[0].dxf.insert.x, titles[0].dxf.insert.y
    dims = _dim_rows(doc, lambda d, p2, p3: abs((p2.x + p3.x) / 2 - tx) <= ELEV_WINDOW
                     and ty - 2000 <= (p2.y + p3.y) / 2 <= ty + 20000)
    for h in (DATUM_DIM, TOTAL_DIM, DEPTH_DIM, STEP_DIM, GLAZING_DIM):
        check(h in dims, f"elevation dimension {h} present")
    dd = dims[DATUM_DIM]
    check(dd["text"] == "100" and abs(dd["measurement_mm"] - 1000) < 1e-6, "datum dimension is '100' (1000 mm)")
    zero_y = min(dd["p2"][1], dd["p3"][1])                                  # its low witness: ±0.00
    check(abs(min(dims[TOTAL_DIM]["p2"][1], dims[TOTAL_DIM]["p3"][1]) - zero_y) < 1.0, "1440 chain starts at ±0.00")
    lv = lambda y: EB.level_at(y, zero_y, 0.0)                              # noqa: E731
    span = {h: {k: round(v, 6) for k, v in EB.dimension_span(dims[h]["p2"][1], dims[h]["p3"][1], zero_y, 0.0).items()}
            for h in (DATUM_DIM, DEPTH_DIM, STEP_DIM, GLAZING_DIM)}
    x0, x1, y0, y1 = PIT_WINDOW
    vert, horiz, texts = [], [], []
    for e in ents:
        t = e.dxftype()
        if t == "LINE":
            a, b = e.dxf.start, e.dxf.end
            if x0 <= min(a.x, b.x) and max(a.x, b.x) <= x1 and y0 <= min(a.y, b.y) and max(a.y, b.y) <= y1:
                if abs(a.x - b.x) < 1.0:
                    vert.append({"x": a.x, "layer": e.dxf.layer, "lo": lv(min(a.y, b.y)), "hi": lv(max(a.y, b.y))})
                elif abs(a.y - b.y) < 1.0:
                    horiz.append({"level": round(lv(a.y), 3), "layer": e.dxf.layer, "x0": min(a.x, b.x), "x1": max(a.x, b.x)})
        elif t in ("TEXT", "MTEXT"):
            p = e.dxf.insert
            if x0 - 3000 <= p.x <= x1 + 3000 and y0 <= p.y <= y1 + 500:
                texts.append({"text": (e.dxf.text if t == "TEXT" else e.plain_text()).strip(), "x": p.x,
                              "level": round(lv(p.y), 3), "layer": e.dxf.layer})
    r = lambda v: round(v, 3)                                               # noqa: E731
    walls = [v for v in vert if v["layer"] == "1"]
    outer = sorted(v["x"] for v in walls if r(v["lo"]) <= -1.0 and r(v["hi"]) >= -0.1)
    inner = sorted(v["x"] for v in walls if r(v["lo"]) == -0.9 and r(v["hi"]) == 0.3)
    check(len(outer) == 2 and len(inner) == 2, f"the sunken element has two outer and two inner faces: {outer} {inner}")
    axis = (inner[0] + inner[1]) / 2
    check(abs((outer[0] + outer[1]) / 2 - axis) < 1.0, "inner and outer faces share one axis")
    gens = sorted(v["x"] - axis for v in walls if r(v["lo"]) == -0.85 and r(v["hi"]) == 0.3
                  and inner[0] < v["x"] < inner[1])
    curved = sorted(v["x"] - axis for v in walls if r(v["lo"]) == 0.15 and r(v["hi"]) == 1.0)
    levels = sorted({(h["level"], h["layer"]) for h in horiz})
    return {"title_xy": (tx, ty), "dims": dims, "zero_y": zero_y, "span": span, "axis_x": axis,
            "outer_x": outer, "inner_x": inner, "outer_w": outer[1] - outer[0], "inner_w": inner[1] - inner[0],
            "wall_t": inner[0] - outer[0], "generators": gens, "curved": curved, "levels": levels, "texts": texts,
            "deck_text": [t for t in texts if t["text"] == "+0.15"]}


def plan(doc, s82_mod):
    """The pool in the architectural plan: its arcs (located through the PS5.1 registration from the structural
    outline), the plan dimensions round it and the labels inside it."""
    import alsenan_structural_s1 as S1M
    from ezdxf import disassemble
    src = S1M.Source(ROOT / "data/inputs/by_sha256" / f"{STRUCT_SHA}.dxf")
    pg = s82_mod.plan_geometry(src)
    reg = _j(R / "pre_s5_1_source_resolution/PRE_S5_1_SUMMARY.json")["registration"]
    check(reg["state"] == "REGISTERED", "PS5.1 registration holds")
    tx, ty = reg["translation_arch_to_gbp"]
    gx, gy = src.sheets["GBP"]["frame"][:2]
    c = (pg["centre"][0] + gx - tx, pg["centre"][1] + gy - ty)
    arcs, labels = [], []
    for e in disassemble.recursive_decompose(doc.modelspace()):
        t = e.dxftype()
        if t in ("ARC", "CIRCLE") and math.dist((e.dxf.center.x, e.dxf.center.y), c) < 50:
            arcs.append({"layer": e.dxf.layer, "r": round(e.dxf.radius, 3), "a0": round(e.dxf.get("start_angle", 0.0), 3),
                         "a1": round(e.dxf.get("end_angle", 360.0), 3),
                         "centre_offset_mm": round(math.dist((e.dxf.center.x, e.dxf.center.y), c), 3)})
        elif t in ("TEXT", "MTEXT"):
            p = e.dxf.insert
            d = math.dist((p.x, p.y), c)
            if d < 6000:
                labels.append({"text": (e.dxf.text if t == "TEXT" else e.plain_text()).strip(), "layer": e.dxf.layer,
                               "dist_mm": round(d, 1), "dx": round(p.x - c[0]), "dy": round(p.y - c[1])})
    dims = _dim_rows(doc, lambda d, p2, p3: abs((p2.x + p3.x) / 2 - c[0]) < 4500 and abs((p2.y + p3.y) / 2 - c[1]) < 6000)
    for k, h in PLAN_DIMS.items():
        check(h in dims, f"plan dimension {k} ({h}) present")
    return {"centre_arch": c, "centre_gbp": pg["centre"], "R_out": pg["R_out"], "R_in": pg["R_in"],
            "A_out": pg["A_out"], "arcs": sorted(arcs, key=lambda a: (a["layer"], a["r"], a["a0"])),
            "labels": sorted(labels, key=lambda x: x["dist_mm"]), "dims": dims}


def binding(el, pl):
    """Criteria for the sunken element on the NW elevation being the swimming pool."""
    R_in, R_out = pl["R_in"], pl["R_out"]
    lab = [x for x in pl["labels"] if x["text"].lower() == POOL_LABEL and x["dist_mm"] < R_in]
    others = [x for x in pl["labels"] if OTHER_PIT_WORDS.search(x["text"]) and x["dist_mm"] < R_out + 500]
    curved_arc = next(a for a in pl["arcs"] if a["layer"] == "5" and a["r"] not in (round(R_in, 3), round(R_out, 3)))
    hw = EB.arc_projected_half_width(curved_arc["r"], curved_arc["a0"], curved_arc["a1"], axis="y")
    iv_y = EB.arc_projected_interval(curved_arc["r"], curved_arc["a0"], curved_arc["a1"], axis="y")
    iv_x = EB.arc_projected_interval(curved_arc["r"], curved_arc["a0"], curved_arc["a1"], axis="x")
    cyl = EB.cylinder_from_generators(el["inner_w"] / 2, el["generators"], tol=1.0)
    curved_sym = EB.cylinder_from_generators(max(abs(v) for v in el["curved"]), el["curved"], tol=1.0)
    width = pl["dims"][PLAN_DIMS["WIDTH_350"]]["measurement_mm"]
    gap = pl["dims"][PLAN_DIMS["GAP_50"]]["measurement_mm"]
    plan_deck = [x for x in pl["labels"] if x["text"] == "+0.15" and x["layer"] == "LEVEL"]
    C = lambda kind, ok, ev: {"kind": kind, "ok": bool(ok), "detail": ev}          # noqa: E731
    crit = [
        C(EB.IDENTITY_LABEL, lab, f"plan text '{POOL_LABEL}' (layer 5) {lab[0]['dist_mm'] if lab else '-'} mm from the "
                                  f"pool arc centre, inside the R{R_in:.0f} water outline"),
        C(EB.DIMENSION_MATCH, abs(el["outer_w"] - width) < 1.0,
          f"elevation outer faces {el['outer_w']:.1f} mm apart = plan '350' ({PLAN_DIMS['WIDTH_350']}) {width:.1f} mm"),
        C(EB.DIMENSION_MATCH, abs(el["inner_w"] - 2 * R_in) < 1.0,
          f"elevation inner faces {el['inner_w']:.1f} mm apart = 2 x the R{R_in:.0f} water arc"),
        C(EB.DIMENSION_MATCH, abs(el["wall_t"] - (R_out - R_in)) < 1.0,
          f"elevation wall {el['wall_t']:.1f} mm = R{R_out:.0f} - R{R_in:.0f}"),
        C(EB.FEATURE_MATCH, cyl["consistent"] and abs(cyl["radius"] - R_in) < 1.0,
          f"{len(el['generators'])} generator lines inside the element are those of a cylinder of radius "
          f"{cyl['radius']:.1f} mm seen side-on (angles {[round(a, 1) for a in cyl['angles_deg']]}): the pool's "
          f"semicircular inner wall R{R_in:.0f}"),
        C(EB.FEATURE_MATCH, curved_sym["consistent"] and abs(max(abs(v) for v in el["curved"]) - hw) < 1.0,
          f"the curved element above is symmetric about the same axis with half-width "
          f"{max(abs(v) for v in el['curved']):.1f} mm = the plan arc R{curved_arc['r']:.0f} "
          f"({curved_arc['a0']}-{curved_arc['a1']} deg, inner face of the curved wall: pool R{R_out:.0f} + gap "
          f"{gap:.0f}) projected on the facade axis, {hw:.1f} mm"),
        C(EB.FEATURE_MATCH, abs(iv_y[0] + iv_y[1]) < 1.0 and abs(iv_x[0] + iv_x[1]) > 100.0
          and curved_sym["symmetric"] and cyl["symmetric"],
          f"view direction: both drawn features are symmetric about the element's axis. The curved-wall arc projects "
          f"symmetrically only onto plan y ({iv_y[0]:.0f}..{iv_y[1]:.0f} mm); onto x it spans {iv_x[0]:.0f}.."
          f"{iv_x[1]:.0f} mm. So the elevation looks along plan x, from the straight sea-side end"),
        C(EB.LEVEL_MATCH, el["deck_text"] and plan_deck,
          f"'+0.15' on the elevation deck line right of the element and {len(plan_deck)} '+0.15' LEVEL marks round "
          "the pool in plan"),
        C(EB.CONTRADICTION, others, "another sunken object (lift, pit, tank, sump) labelled at this place in plan: "
                                    f"{[o['text'] for o in others]}")]
    return crit, EB.binding_verdict(crit), {"curved_arc": curved_arc, "half_width": hw, "interval_y": iv_y,
                                            "interval_x": iv_x, "cylinder": cyl}


# ------------------------------------------------------------------ registers
def dimension_register(el, pl):
    sp = el["span"]
    E = lambda h: el["dims"][h]                                                # noqa: E731
    rows = []

    def add(i, src, handle, text, mm, levels, binds, authority, use, note=""):
        rows.append({"DIM_ID": i, "SOURCE": src, "HANDLE": handle, "PRINTED": text, "MEASUREMENT_MM": mm,
                     "WITNESS_LEVELS_M": levels, "BINDS_TO": binds, "AUTHORITY": authority, "USE": use, "NOTE": note})
    add("D-01", "P7757.dxf NW elevation", DATUM_DIM, E(DATUM_DIM)["text"], E(DATUM_DIM)["measurement_mm"],
        [sp[DATUM_DIM]["low_m"], sp[DATUM_DIM]["high_m"]], "DATUM: ±0.00 to the house ground floor +1.00",
        "STATED_DIMENSION", "level datum of every witness point below")
    add("D-02", "P7757.dxf NW elevation", DEPTH_DIM, E(DEPTH_DIM)["text"], E(DEPTH_DIM)["measurement_mm"],
        [sp[DEPTH_DIM]["low_m"], sp[DEPTH_DIM]["high_m"]], "SWIMMING POOL: inner depth, wall top to inner floor, at "
        "the drawn plane", "STATED_DIMENSION", "pool wall top +0.30 and inner floor -0.85 at that plane",
        "the scanned sheet 08 prints the same '115' (VR-01)")
    add("D-03", "P7757.dxf NW elevation", STEP_DIM, E(STEP_DIM)["text"], E(STEP_DIM)["measurement_mm"],
        [sp[STEP_DIM]["low_m"], sp[STEP_DIM]["high_m"]], "BUILDING: pool wall top +0.30 to the house ground floor "
        "+1.00 under the curved glazing", "STATED_DIMENSION", "none for the pool (not a pool depth, not a step below "
        "the deck)")
    add("D-04", "P7757.dxf NW elevation", GLAZING_DIM, E(GLAZING_DIM)["text"], E(GLAZING_DIM)["measurement_mm"],
        [sp[GLAZING_DIM]["low_m"], sp[GLAZING_DIM]["high_m"]], "BUILDING: curved glazing, ground floor +1.00 to +5.30",
        "STATED_DIMENSION", "none for the pool")
    add("D-05", "P7757.dxf NW elevation", "text", "+0.15", None, [0.15], "DECK level round the pool",
        "STATED_LEVEL", "deck surface; the pool walls rise 0.15 above it to +0.30")
    for k, h in PLAN_DIMS.items():
        d = pl["dims"][h]
        binds = {"LENGTH_350": "SWIMMING POOL: outer length (straight end to the arc apex)",
                 "WIDTH_350": "SWIMMING POOL: outer width along the sea-view facade",
                 "PLAN_115": "PLAN OFFSET: pool face to the return wall (horizontal; a homonym of the elevation's 115)",
                 "GAP_50": "gap between the pool and the curved wall",
                 "CURVED_WALL_20": "curved master-bedroom wall thickness"}[k]
        add(f"D-P-{k}", "P7757.dxf GF plan", h, d["text"], d["measurement_mm"], None, binds, "STATED_DIMENSION",
            "corroborates the binding" if k != "PLAN_115" else "none: a plan distance, never a depth")
    for v in VISUAL:
        add(v["ID"], f"scan {v['PDF']} p.{v['PAGE']}" if v["PAGE"] else "scans (all sheets)", "raster",
            v["SHEET"], None, None, v["READ"], "VISUAL_RECORD (same drawing as the DXF; crops kept out of git)",
            v["SCALE_CHECK"] or "identity / orientation", f"box {v['BOX_UPRIGHT_PX']}" if v["BOX_UPRIGHT_PX"] else "")
    return rows


def interpretation(el, s82):
    sp = el["span"]
    wall_top, floor = sp[DEPTH_DIM]["high_m"], sp[DEPTH_DIM]["low_m"]
    prof = EB.floor_profile([{"source": "P7757 NW elevation (architectural)", "levels": [round(floor, 3)]},
                             {"source": "ST7757 p.7 DETAIL OF SWIMMING POOL (structural)",
                              "levels": ["DEEP", "SLOPE", "SHALLOW"]}])
    I = lambda i, item, value, unit, state, auth, basis: {                      # noqa: E731
        "ITEM_ID": i, "ITEM": item, "VALUE": value, "UNIT": unit, "STATE": state, "AUTHORITY": auth, "BASIS": basis}
    return [
        I("Z-01", "pool wall top level", wall_top, "m", "ESTABLISHED", "STATED_DIMENSION",
          f"{STEP_DIM} '70' down from the +1.00 floor and {DEPTH_DIM} '115' upper witness; drawn top line at +0.30"),
        I("Z-02", "deck level round the pool", 0.15, "m", "ESTABLISHED", "STATED_LEVEL", "elevation and plan '+0.15'"),
        I("Z-03", "wall upstand above the deck", round(wall_top - 0.15, 6), "m", "DERIVED_FROM_STATED_LEVELS", "STATED_LEVEL",
          "+0.30 - +0.15; whether the RC wall or a coping forms it is not stated"),
        I("Z-04", "inner depth at the drawn plane", sp[DEPTH_DIM]["span_m"], "m", "STATED_AT_DRAWN_PLANE_ONLY",
          "STATED_DIMENSION", "the elevation cuts the pool at one plane parallel to the sea-view facade; which zone "
                              "that plane lies in is not stated"),
        I("Z-05", "inner floor level at the drawn plane", floor, "m", "DERIVED_AT_DRAWN_PLANE_ONLY", "STATED_DIMENSION",
          "+0.30 - 1.15; the inner faces stop at -0.90 and two floor lines sit at -0.85: finish or base top not shown"),
        I("Z-06", "deep-end depth", None, "m", "NOT_ESTABLISHED", "NOT_ESTABLISHED",
          "the architectural elevation draws one flat floor; the structural detail draws deep / slope / shallow"),
        I("Z-07", "shallow-end depth", None, "m", "NOT_ESTABLISHED", "NOT_ESTABLISHED", "as Z-06"),
        I("Z-08", "wall heights by wall run", None, "m", "NOT_ESTABLISHED", "NOT_ESTABLISHED",
          "wall top known (+0.30); the base top under each run is not"),
        I("Z-09", "floor slope", None, "", prof["state"], "SOURCE_CONFLICT",
          f"{prof['sources']}: one dimension cannot be applied to the whole pool"),
        I("Z-10", "deep / shallow zone boundaries in plan", None, "m", "NOT_ESTABLISHED", "NOT_ESTABLISHED",
          "no level-change line on plan or elevation"),
        I("Z-11", "direction of any deep / shallow profile", None, "", "INFERENCE_ONLY", "INFERENCE",
          "the elevation views the pool along plan x and shows one flat floor across its full 3.10 m: a profile "
          "across plan y would have shown; if the structural profile exists it runs along x (straight sea-side end "
          "to curved end) or the architect drew the floor flat. Not used for any quantity"),
        I("Z-12", "base thickness by zone", {"deep": 0.40, "slope": None, "shallow": None}, "m", "UNCHANGED_FROM_S8_2",
          "STATED_DIMENSION (deep only)", "the architectural elevation draws the base from the inner floor to -1.05 "
                                         "(not a structural dimension; conflicts with the stated 40 cm)"),
        I("Z-13", "structural concrete ownership", "base owns footprint x thickness incl. wall footprint; walls own "
          "band x height above base top", "", "UNCHANGED_FROM_S8_2", "S8.2 CO-01", ""),
        I("Z-14", "pool wall / base interfaces", s82["summary"]["interfaces"], "", "UNCHANGED_FROM_S8_2", "S8.2 08",
          "no new bar evidence"),
        I("Z-15", "floor profile across sources", prof["state"], "", prof["state"], "elevation_binding.floor_profile",
          f"uniform application of '115' allowed: {prof['uniform_dimension_allowed']}")]


def readiness(s82, interp):
    z = {r["ITEM_ID"]: r for r in interp}
    rows = []
    for r in _rows(S82 / "03_CONCRETE_GEOMETRY_AND_QTO.csv"):
        if r["ROW_KIND"] != "QUANTITY":
            continue
        wall = r["COMPONENT_ID"].startswith("PL-WALL-RUN")
        rows.append({"ROW_ID": r["ROW_ID"], "KIND": "CONCRETE", "COMPONENT_ID": r["COMPONENT_ID"],
                     "S8_2_LANE": r["LANE"], "S8_2A_LANE": r["LANE"], "M3": None, "KG": None,
                     "NEWLY_ESTABLISHED": (f"wall top +{z['Z-01']['VALUE']:.2f}; depth 1.15 at one drawn plane"
                                           if wall else "base top +0.30 - 1.15 = -0.85 at one drawn plane only"),
                     "STILL_MISSING": ("base top level under this run (the floor profile is a PROFILE_CONFLICT; zone of "
                                       "the drawn plane not stated); which run is deep / shallow"
                                       if wall else "plan extent of this zone; thickness (slope / shallow); zone of the "
                                                    "drawn plane"),
                     "RELEASED": False})
    for name in ("04_BASE_REINFORCEMENT_QTO.csv", "05_WALL_REINFORCEMENT_QTO.csv"):
        for r in _rows(S82 / name):
            wall = "WALL" in r["COMPONENT_OWNER_ID"]
            rows.append({"ROW_ID": r["FAMILY_ID"], "KIND": "REINFORCEMENT", "COMPONENT_ID": r["COMPONENT_OWNER_ID"],
                         "S8_2_LANE": r["LANE"], "S8_2A_LANE": r["LANE"], "M3": None, "KG": None,
                         "NEWLY_ESTABLISHED": ("wall top +0.30" if wall else "none for the base bars"),
                         "STILL_MISSING": ("wall height by run (distribution width or bar run); plan face length of the "
                                           "run the section cuts; laps, anchorage, bends" if wall else
                                           "zone plan extents; bar runs; laps, anchorage, bends")
                         + ("; the S8.2 source conflict on this family" if r["LANE"] == "SOURCE_CONFLICT" else ""),
                         "RELEASED": False})
    return rows


def blocked_delta(s82):
    out = []
    for r in _rows(S82 / "03_CONCRETE_GEOMETRY_AND_QTO.csv"):
        if r["ROW_KIND"] == "QUANTITY" and r["COMPONENT_ID"].startswith("PL-WALL-RUN"):
            out.append({"BLOCKED_ID": f"{r['ROW_ID']}:WALL_HEIGHT", "S8_2_REASON": json.loads(r["MISSING"])[0],
                        "S8_2A_REASON": "wall top +0.30 established (NW elevation); the base top under this run is not: "
                                        "the elevation states 1.15 at one plane and draws a flat floor, the structural "
                                        "detail draws deep / slope / shallow",
                        "STATE": "STILL_BLOCKED (narrowed)"})
    for i, (rid, why) in enumerate((("PL-BASE-DEEP", "plan extent of the deep zone"),
                                    ("PL-BASE-SLOPE", "plan extent, rise, thickness"),
                                    ("PL-BASE-SHALLOW", "plan extent, thickness")), 1):
        out.append({"BLOCKED_ID": f"CQ-0{i}:{rid}", "S8_2_REASON": why, "S8_2A_REASON": why + " (no new evidence)",
                    "STATE": "STILL_BLOCKED (unchanged)"})
    out.append({"BLOCKED_ID": "ALL_FAMILIES:BAR_RUN_AND_WIDTH", "S8_2_REASON": "distribution width / bar run not "
                "established", "S8_2A_REASON": "unchanged for the base; for the walls the top is known but the height "
                                               "by run is not", "STATE": "STILL_BLOCKED"})
    out.append({"BLOCKED_ID": "ALL_FAMILIES:LAPS_ANCHORAGE_BENDS", "S8_2_REASON": "drawn only on the NTS detail",
                "S8_2A_REASON": "unchanged: an architectural elevation carries no bar detail", "STATE": "STILL_BLOCKED"})
    return out


def conflicts_questions(s82_cq, verdict):
    out = []
    for r in s82_cq:
        if r["KIND"] == "QUESTION":
            continue
        out.append({"ID": r["ID"], "KIND": r["KIND"], "S8_2_STATUS": r["STATUS"],
                    "S8_2A_STATUS": r["STATUS"], "NOTE": "no new evidence on this conflict"})
    new = [("CF-S8.2A-01", "FLOOR_PROFILE_CONFLICT", "the architectural NW elevation draws one flat inner floor at "
            "-0.85 (1.15 below the +0.30 wall top); the structural p.7 detail draws a deep base, a slope and a shallow "
            "base", "OPEN"),
           ("CF-S8.2A-02", "BASE_THICKNESS_DRAWN", "the architectural elevation draws the base from the inner floor to "
            "-1.05 (about 0.15-0.20 m); the structural detail dimensions the deep base 40 cm. The structural dimension "
            "governs the structure; the architectural line is not a structural dimension", "RECORDED"),
           ("CF-S8.2A-03", "HOMONYM", "'115' appears twice: a vertical 1150 mm pool depth on the NW elevation (2E5E) "
            "and a horizontal 1150 mm plan offset beside the pool (4D0). Only the first is a depth", "GUARDED"),
           ("CF-S8.2A-04", "WALL_TOP_COMPOSITION", "the walls rise 0.15 above the +0.15 deck to +0.30; whether the RC "
            "wall reaches +0.30 or a coping forms the top is not stated", "OPEN")]
    for i, k, t, s in new:
        out.append({"ID": i, "KIND": k, "S8_2_STATUS": "", "S8_2A_STATUS": s, "NOTE": t})
    qs = [("Q-S8.2-01", "PARTLY_ANSWERED", "wall top +0.30 and one inner depth 1.15 (floor -0.85) at one drawn plane are "
           "now stated (NW elevation); the deep and shallow depths and the zone lengths are still not"),
          ("Q-S8.2-02", "NARROWED (inference only)", "if the floor changes level, the change runs along plan x (between "
           "the straight sea-side end and the curved end): the NW elevation looks along x and shows no change across y"),
          ("Q-S8.2A-01", "OPEN", "Architect / engineer: is the pool floor flat at -0.85 (NW elevation) or deep / slope / "
           "shallow (structural p.7)? If it changes, give both depths and where the change starts in plan"),
          ("Q-S8.2A-02", "OPEN", "Engineer: does the RC wall reach the +0.30 top, or is the top 0.15 a coping?"),
          ("Q-S8.2A-03", "OPEN", "Architect: the base drawn on the elevation (to -1.05) is thinner than the structural "
           "40 cm; confirm the structural thickness governs")]
    for i, s, t in qs:
        out.append({"ID": i, "KIND": "QUESTION", "S8_2_STATUS": "OPEN" if i.startswith("Q-S8.2-") else "",
                    "S8_2A_STATUS": s, "NOTE": t})
    out.append({"ID": "PF-01 (S8.2 post-freeze)", "KIND": "SOURCE_NOT_IN_S8_2", "S8_2_STATUS": "OPEN",
                "S8_2A_STATUS": f"SOURCE HELD AND {verdict['state']}; SCOPE OPEN",
                "NOTE": "the architectural elevation is now held; its 115 binds to the pool but only at one plane"})
    return out


def sensitivity(s82, interp):
    band = s82["summary"]["plan_m2"]["wall_band"]
    A = s82["summary"]["plan_m2"]["structural_footprint"]
    z = {r["ITEM_ID"]: r for r in interp}
    rows = []
    add = lambda i, item, basis, value, unit, note: rows.append(                   # noqa: E731
        {"CASE_ID": i, "ITEM": item, "BASIS": basis, "VALUE": value, "UNIT": unit, "LANE": "SENSITIVITY_ONLY",
         "IN_OFFICIAL_TOTAL": False, "NOTE": note})
    add("SA-01", "walls if the floor were flat at the drawn depth everywhere", "wall band x 1.15 (wall top to inner floor)",
        band * z["Z-04"]["VALUE"], "m3", "the structural detail draws a deep / slope / shallow floor (CF-S8.2A-01)")
    add("SA-02", "wall portion above the deck, if the RC wall reaches +0.30", "wall band x 0.15", band * z["Z-03"]["VALUE"],
        "m3", "the RC top is not stated (CF-S8.2A-04)")
    add("SA-03", "walls per 0.10 m of uniform height", "wall band x 0.10", band * 0.10, "m3/0.1 m", "")
    add("SA-04", "base at the stated 40 cm under the whole footprint", "footprint x 0.40", A * 0.40, "m3",
        "40 cm is dimensioned on the deep base only (S8.2 SEN-02)")
    return rows


def conservation(ctx):
    out = []
    add = lambda i, what, ok, detail: out.append({"CHECK_ID": i, "CHECK": what, "RESULT": "PASS" if ok else "FAIL",
                                                  "DETAIL": detail})                   # noqa: E731
    m82 = _j(MANIFESTS["S8.2"])
    out_ok = all(_sha(S82 / o) == h for o, h in m82["outputs"].items())
    add("A-01", "S8.2 is untouched: its manifest and every frozen output verify", out_ok and "S8.2" in ctx["frozen"],
        f"{len(m82['outputs'])} outputs; S8.2 files checked {ctx['frozen']['S8.2']['files_checked']}")
    add("A-02", "every earlier frozen stage verifies", len(ctx["frozen"]) == len(MANIFESTS),
        f"{len(ctx['frozen'])} manifests")
    rel = {r["SOURCE_KEY"]: r["RELATION"] for r in ctx["identity"]}
    add("A-03", "both architectural PDFs are the earlier sources apart from wrapper metadata",
        all(v == SI.WRAPPER_METADATA_ONLY for v in rel.values()) and all(r["PAGE_CENSUS_MATCHES_EARLIER"]
                                                                          for r in ctx["identity"]), str(rel))
    add("A-04", "the depth dimension binds to the pool on label, dimension and feature criteria",
        ctx["verdict"]["state"] == EB.BOUND and not ctx["verdict"]["failed"], json.dumps(ctx["verdict"]))
    sp = ctx["el"]["span"]
    add("A-05", "'115' spans +0.30 to -0.85; '70' spans +0.30 to +1.00 (building, not pool)",
        abs(sp[DEPTH_DIM]["high_m"] - 0.30) < 1e-6 and abs(sp[DEPTH_DIM]["low_m"] + 0.85) < 1e-6
        and abs(sp[STEP_DIM]["low_m"] - 0.30) < 1e-6 and abs(sp[STEP_DIM]["high_m"] - 1.00) < 1e-6,
        json.dumps({k: sp[k] for k in (DEPTH_DIM, STEP_DIM)}))
    z = {r["ITEM_ID"]: r for r in ctx["interp"]}
    add("A-06", "the depth is not applied uniformly while the floor profile conflicts",
        z["Z-15"]["VALUE"] == EB.PROFILE_CONFLICT and z["Z-06"]["VALUE"] is None and z["Z-07"]["VALUE"] is None,
        f"floor profile {z['Z-15']['VALUE']}")
    add("A-07", "nothing released: no m3 or kg on any readiness row",
        all(r["M3"] is None and r["KG"] is None and not r["RELEASED"] for r in ctx["ready"]),
        f"{len(ctx['ready'])} rows; S8.2 lanes unchanged "
        f"{dict(Counter(r['S8_2A_LANE'] for r in ctx['ready']))}")
    add("A-08", "every S8.2 concrete row and bar family is carried",
        sum(1 for r in ctx["ready"] if r["KIND"] == "CONCRETE") == 7
        and sum(1 for r in ctx["ready"] if r["KIND"] == "REINFORCEMENT") == 21, "7 concrete rows, 21 families")
    homonym = [r for r in ctx["dims"] if r["PRINTED"] == "115"]
    add("A-09", "the plan's horizontal 115 is never used as a depth", len(homonym) == 2 and any(
        r["HANDLE"] == PLAN_DIMS["PLAN_115"] and r["USE"].startswith("none") for r in homonym), "")
    add("A-10", "the 26 records and 5 source conflicts of S8.2 stay authoritative",
        len(_rows(S82 / "13_REBAR_EVIDENCE_BINDING.csv")) == 26
        and sum(1 for r in ctx["ready"] if r["S8_2A_LANE"] == "SOURCE_CONFLICT") == 5, "")
    add("A-11", "sensitivity never enters a total", all(r["LANE"] == "SENSITIVITY_ONLY" and r["IN_OFFICIAL_TOTAL"] is False
                                                        for r in ctx["sens"]), f"{len(ctx['sens'])} cases")
    pkg = [p.name for p in HERE.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf", ".dxf", ".dwg")]
    add("A-12", "no client drawing, scan or crop in the package", not pkg, f"{pkg}")
    return out


# ------------------------------------------------------------------ build
def _load_s82_builder():
    spec = importlib.util.spec_from_file_location("build_s8_2_frozen", S82 / "build_s8_2.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def build():
    import ezdxf
    frozen = verify_inputs()
    s82 = {"summary": _j(S82 / "17_S8_2_SUMMARY.json")}
    identity, pages, ident = pdf_identity()
    doc = ezdxf.readfile(ARCH)
    el = elevation(doc)
    pl = plan(doc, _load_s82_builder())
    check(abs(pl["A_out"] - s82["summary"]["plan_m2"]["structural_footprint"]) < 1e-9,
          "S8.2's frozen footprint is the plan outline")
    crit, verdict, feat = binding(el, pl)
    dims = dimension_register(el, pl)
    interp = interpretation(el, s82)
    ready = readiness(s82, interp)
    blocked = blocked_delta(s82)
    cq = conflicts_questions(_rows(S82 / "16_CONFLICT_AND_QUESTION_REGISTER.csv"), verdict)
    sens = sensitivity(s82, interp)
    for o in OUTPUTS + [MANIFEST_NAME]:
        if (HERE / o).exists():
            (HERE / o).unlink()
    bind_rows = [{"CRITERION": f"B-{i:02d}", "KIND": c["kind"], "SATISFIED": c["ok"], "EVIDENCE": c["detail"]}
                 for i, c in enumerate(crit, 1)]
    bind_rows.append({"CRITERION": "VERDICT", "KIND": "BINDING", "SATISFIED": verdict["state"] == EB.BOUND,
                      "EVIDENCE": f"{verdict['state']}: '115' ({DEPTH_DIM}) measures the swimming pool; '70' "
                                  f"({STEP_DIM}) measures the building (pool wall top to the house floor)"})
    _csv(OUTPUTS[1], identity + [{"SOURCE_KEY": p["SOURCE_KEY"], "NEW_SHA256": f"page {p['PAGE']}",
                                  "EARLIER_FILE": p["SHEET"], "RELATION": "PAGE_IMAGE",
                                  "NEW_METADATA": {"size_pt": p["SIZE_PT"], "image_px": p["IMAGE_PX"],
                                                   "filter": p["IMAGE_FILTER"], "text_chars": p["TEXT_CHARS"],
                                                   "image_sha256": p["IMAGE_SHA256"]}}
                                 for p in pages], list(identity[0]))
    _csv(OUTPUTS[2], bind_rows, list(bind_rows[0]))
    _csv(OUTPUTS[3], dims, list(dims[0]))
    _csv(OUTPUTS[4], interp, list(interp[0]))
    _csv(OUTPUTS[5], ready, list(ready[0]))
    _csv(OUTPUTS[6], blocked, list(blocked[0]))
    _csv(OUTPUTS[7], cq, list(cq[0]))
    _csv(OUTPUTS[8], sens, list(sens[0]))
    ctx = {"frozen": frozen, "identity": identity, "verdict": verdict, "el": el, "interp": interp, "ready": ready,
           "dims": dims, "sens": sens}
    cons = conservation(ctx)
    _csv(OUTPUTS[9], cons, list(cons[0]))
    check(all(c["RESULT"] == "PASS" for c in cons), "; ".join(f"{c['CHECK_ID']} {c['DETAIL']}" for c in cons
                                                             if c["RESULT"] != "PASS"))
    prov = [{"record": r["DIM_ID"], "output": OUTPUTS[3], "source": r["SOURCE"], "handle": r["HANDLE"],
             "drawing_sha256": ARCH_SHA if r["HANDLE"] != "raster" else
             NEW_PDFS["ARCH_PART_2_PAGES_07-12" if "07-12" in r["SOURCE"] else "ARCH_PART_1_PAGES_01-06"],
             "authority": r["AUTHORITY"]} for r in dims]
    prov += [{"record": c["CRITERION"], "output": OUTPUTS[2], "kind": c["KIND"], "satisfied": c["SATISFIED"],
              "drawing_sha256": ARCH_SHA} for c in bind_rows]
    prov += [{"record": r["SOURCE_KEY"], "output": OUTPUTS[1], "relation": r["RELATION"], "sha256": r["NEW_SHA256"],
              "earlier_sha256": r["EARLIER_SHA256"]} for r in identity]
    (HERE / OUTPUTS[10]).write_text("".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in prov),
                                    encoding="utf-8")
    sp = el["span"]
    summary = {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "pdf_identity": ident,
        "binding": {"115": {"handle": DEPTH_DIM, "state": verdict["state"], "object": "SWIMMING_POOL",
                            "measures": "inner depth, wall top to inner floor, at the drawn plane",
                            "levels_m": [sp[DEPTH_DIM]["high_m"], sp[DEPTH_DIM]["low_m"]]},
                    "70": {"handle": STEP_DIM, "object": "BUILDING", "measures": "pool wall top +0.30 to the house "
                           "ground floor +1.00", "levels_m": [sp[STEP_DIM]["low_m"], sp[STEP_DIM]["high_m"]]},
                    "+0.15": {"object": "DECK", "level_m": 0.15},
                    "criteria_satisfied": verdict["satisfied"]},
        "newly_established": {r["ITEM"]: r["VALUE"] for r in interp if r["STATE"] in
                              ("ESTABLISHED", "DERIVED_FROM_STATED_LEVELS", "STATED_AT_DRAWN_PLANE_ONLY",
                               "DERIVED_AT_DRAWN_PLANE_ONLY")},
        "not_established": [r["ITEM"] for r in interp if r["STATE"] == "NOT_ESTABLISHED"],
        "floor_profile": next(r["VALUE"] for r in interp if r["ITEM_ID"] == "Z-15"),
        "released": {"concrete_m3": 0.0, "reinforcement_kg": 0.0, "rows_released": 0},
        "s8_2_lanes_after": dict(sorted(Counter(r["S8_2A_LANE"] for r in ready).items())),
        "conflicts_new": [r["ID"] for r in cq if r["ID"].startswith("CF-S8.2A")],
        "questions_new": [r["ID"] for r in cq if r["ID"].startswith("Q-S8.2A")],
        "sensitivity": {r["CASE_ID"]: r["VALUE"] for r in sens},
        "conservation": {c["CHECK_ID"]: c["RESULT"] for c in cons},
        "frozen_baselines": {k: v["manifest_sha256"] for k, v in frozen.items()},
        "references_read": []}
    _json(OUTPUTS[11], summary)
    (HERE / OUTPUTS[0]).write_text(readme(summary, identity, crit, interp), encoding="utf-8")
    manifest = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "FROZEN_CORRECTION_LAYER",
                "corrects": "S8.2 (frozen, unchanged)", "engine_commit_stamp": summary["engine_commit"],
                "references_read": [], "code": {c: _sha(ROOT / c) for c in CODE},
                "inputs": {str(SOURCE_MANIFEST.relative_to(ROOT)): _sha(SOURCE_MANIFEST),
                           "research/pre_s5_1_source_resolution/PRE_S5_1_SUMMARY.json":
                               _sha(R / "pre_s5_1_source_resolution/PRE_S5_1_SUMMARY.json")}
                          | {f"research/alsenan_swimming_pool_s8_2/{o}": _sha(S82 / o) for o in S82_READ},
                "drawing_sha256": {"P7757.dxf": ARCH_SHA, "ST7757.dxf": STRUCT_SHA, **NEW_PDFS,
                                   **{f"EARLIER_{k}": v["earlier_sha256"] for k, v in ident.items()}},
                "frozen_baselines": summary["frozen_baselines"],
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
                "released": summary["released"],
                "rule": "S8.2A is a dated correction layer: S8.2 is never written; a quantity is released only where "
                        "geometry, dimensional scope and ownership are established"}
    _json(MANIFEST_NAME, manifest)
    return summary


def readme(s, identity, crit, interp):
    b = s["binding"]
    L = ["# S8.2A: architectural elevation source recovery and pool depth authority", "",
         f"Baseline `{s['baseline']}`. A dated correction layer on the frozen S8.2. No S8.2 file changes. "
         f"Manifest `{MANIFEST_NAME}`, `references_read: []`.", "",
         "## Answer", "",
         f"- **'115' belongs to the swimming pool** ({b['115']['state']}). It is the inner depth from the pool-wall "
         f"top (+{b['115']['levels_m'][0]:.2f}) to the inner floor ({b['115']['levels_m'][1]:.2f}), at the one plane "
         "the north-west elevation draws.",
         f"- **'70' does not.** It runs from the pool-wall top (+{b['70']['levels_m'][0]:.2f}) to the house ground "
         f"floor (+{b['70']['levels_m'][1]:.2f}).",
         "- **'+0.15'** is the deck round the pool. The walls rise 0.15 above it.",
         f"- **Released:** concrete {s['released']['concrete_m3']:g} m3, reinforcement "
         f"{s['released']['reinforcement_kg']:g} kg. The floor profile is a **{s['floor_profile']}**: the "
         "architectural elevation draws one flat floor, the structural detail a deep end, a slope and a shallow end. "
         "So no single depth applies to the whole pool.", "",
         "## Source identity", ""]
    for r in identity:
        L.append(f"- `{r['SOURCE_KEY']}` `{r['NEW_SHA256'][:12]}…` against the earlier `{r['EARLIER_SHA256'][:12]}…`: "
                 f"**{r['RELATION']}**. The new file is {r['BYTE_DELTA']} bytes longer, entirely from an added "
                 "/Title and /Subject. Removing them reproduces the earlier file's SHA-256 exactly.")
    L += ["", "## Binding criteria (vector DXF)", ""] + [f"- [{'x' if c['ok'] else ' '}] {c['kind']}: {c['detail']}"
                                                          for c in crit]
    L += ["", "## Pool levels and zones", "", "| item | value | state |", "|---|---|---|"]
    L += [f"| {r['ITEM']} | {_cell(r['VALUE'])} {r['UNIT']} | {r['STATE']} |" for r in interp]
    L += ["", "## Outputs", ""] + [f"- `{o}`" for o in OUTPUTS] + [f"- `{MANIFEST_NAME}`"]
    return "\n".join(L) + "\n"


def main():
    try:
        s = build()
    except Stop as e:
        raise SystemExit(f"STOP: {e}")
    print(json.dumps({k: s[k] for k in ("pdf_identity", "binding", "newly_established", "floor_profile", "released",
                                        "conservation")}, indent=1, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
