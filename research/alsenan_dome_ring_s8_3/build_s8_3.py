"""S8.3 - dome and ring-beam structural QTO, source-controlled and blind (frozen before any comparison).

    python3 -I research/alsenan_dome_ring_s8_3/build_s8_3.py

Reads the registered structural DXF (ST7757: p.5 first-floor roof slab, p.6 second-floor roof slab, p.7 DETAIL OF
DOME), the registered architectural DXF (P7757: second-floor plan, SOUTH EAST and NORTH WEST ELEVATIONS) and frozen
Urban stages (S1 registers, S6 / S6.1 beam records, S7 / S7A slab records). The architectural 12-sheet PDF set enters
only as visual records read in session (sheet, part, page, pixel box); its crops are client drawing and stay out of git.

It establishes each physical dome, its profile, its ring beam and their interfaces; transfers the dome ring arcs from
S6 to S8.3 without moving any frozen quantity; and measures only what geometry, scope and ownership establish. No
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

from engine.source import curved_member_geometry as G  # noqa: E402
from engine.source import delta_release as DR  # noqa: E402
from engine.source import graphic_evidence as GE  # noqa: E402
from engine.source import rebar_unit_mass as UM  # noqa: E402

ROUND = "S8_3"
DATE = "2026-10-09"
BASELINE_HEAD = "104c9d6"
POLICY = "S8_3_DOME_RING_SOURCE_CONTROLLED_V1"
R = ROOT / "research"
BY_SHA = ROOT / "data/inputs/by_sha256"
STRUCT_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
STRUCT_PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
SET_KEY = "P7757_ARCH_PDF_SET_01-12"
SET_PARTS = {"ARCH_PART_1_PAGES_01-06": "cd3b8669d55998cb638bd8e2b572da4992ed64babcecacd73753d6a2f0c68b97",
             "ARCH_PART_2_PAGES_07-12": "1e7087d3e61bbb682c9107193c97550a2837e5198bde0ee311319bf7f4a08459"}
RECONSTRUCTED = {"80b6a80428990db4dfa86aa343ed2c7cb429709459d564f0dac92362480a9b00": "ARCH_PART_1_PAGES_01-06",
                 "281a0c3f8c1cdd8f2a78528513b66d14ba4793e981e2d8059423faf6e6162f99": "ARCH_PART_2_PAGES_07-12"}
RECON_STATE = "BYTE_IDENTICAL_RECONSTRUCTION_FROM_VERIFIED_UPLOAD"
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
             "S8.2A": R / "alsenan_swimming_pool_s8_2a/12_S8_2A_FREEZE_MANIFEST.json"}
S1D = R / "alsenan_structural_census_s1"
READ = {"S1_SPECIAL": S1D / "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER.json",
        "S1_RULES": S1D / "STRUCTURAL_PROJECT_RULE_REGISTER.json",
        "S1_BEAM_DEFS": S1D / "BEAM_DEFINITION_REGISTER.json",
        "S1_LEVELS": S1D / "STRUCTURAL_LEVEL_REGISTER.json",
        "S1_PANELS": S1D / "SLAB_PANEL_REGISTER.json",
        "S6_OCC": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCES.csv",
        "S6_1_DELTA": R / "alsenan_superstructure_beam_rebar_s6_1/S6_1_DELTA_COMPONENTS.csv",
        "S7_ITEMS": R / "alsenan_slab_rebar_s7/01_S7_RELEASE_ITEMS.csv",
        "S7A_ENDS": R / "alsenan_slab_rebar_s7a_qa/08_END_CONDITION_AUDIT.csv",
        "SOURCE_MANIFEST": ROOT / "tests/alsenan/registers/SOURCE_MANIFEST.json"}
CODE = ["engine/source/curved_member_geometry.py", "engine/source/delta_release.py", "engine/source/graphic_evidence.py",
        "engine/source/rebar_unit_mass.py", "research/alsenan_dome_ring_s8_3/build_s8_3.py",
        "research/external_engine_lab/alsenan_structural_s1.py"]
OUTPUTS = ["00_README.md", "01_SOURCE_REGISTER.csv", "02_DOME_POPULATION.csv", "03_DOME_PROFILE_AND_LEVELS.csv",
           "04_RING_GEOMETRY.csv", "05_S6_TO_S8_3_OWNERSHIP_DELTA.csv", "06_CONCRETE_REGISTER.csv",
           "07_REBAR_NOTATION_REGISTER.csv", "08_REBAR_QTO_REGISTER.csv", "09_BLOCKED_COMPONENTS.csv",
           "10_SOURCE_CONFLICTS_AND_QUESTIONS.csv", "11_INTERFACE_AUDIT.csv", "12_SENSITIVITY_CASES.csv",
           "13_CONSERVATION_CHECKS.csv", "14_PROVENANCE.jsonl", "15_S8_3_SUMMARY.json"]
MANIFEST_NAME = "16_S8_3_FREEZE_MANIFEST.json"
UNIT_MASS = {"method": UM.D2_OVER_162, "authority": "project-wide method used by S7 / S8.1 / S8.2",
             "selected_by": "Urban (project basis)"}
SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO = "SOURCE_DERIVED_PHYSICAL", "PROJECT_BASIS_QTO"
BLOCKED, CONFLICT, SENS = "BLOCKED_UNQUANTIFIED", "SOURCE_CONFLICT", "SENSITIVITY_ONLY"
RELEASED_LANES = (SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO)

# ------------------------------------------------------------------ structural source (ST7757)
SHEET_PLAN, SHEET_UPPER, SHEET_DET = "FFRS", "SFRS", "DET"
RING_LAYER = "1"
RING_RADII = (2000.0, 2600.0)
FRAMING_REACH = 2900.0                      # straight bands whose centreline passes this close to a dome centre
SHELL_ARCS = ("182B", "182E")               # DETAIL OF DOME: extrados, intrados
SPAN_DIM, RISE_DIM, THICK_DIM, RING_DEPTH_DIM = "1A38", "1A6D", "19B1", "182F"
RING_SECTIONS = ("1A0A", "1A07")            # left and right cuts of the one ring
SHELL_BAR_LINE, RING_LINK = "1A09", "1A0B"
HOOP_DOT_BLOCK = "*U295"
SHELL_LABELS = {"1A0E": "1A0C", "1A15": "1A13"}          # label -> leader line whose free end is the tip
RING_LABELS = {"1A47": ("RING_TOP", "1A68"), "1A4B": ("RING_BOTTOM", "1A6C"), "1A37": ("RING_SIDE", "1A66"),
               "1A29": ("RING_LINKS", "1A58")}           # left-section label -> (family, right-section repeat)
# ------------------------------------------------------------------ architectural source (P7757)
ARCH_DOME_RADII = (2150.0, 2260.0)
ELEVATIONS = {
    "SE": {"title": "SOUTH EAST ELEVATION", "set_sheet": "06", "datum_dim": "2493",
           "tower": (-283300, -790900, -278400, -788500), "terrace": (-278000, -793600, -273500, -792300),
           "dims": {"2C86": "TOWER_CHORD", "2AF3": "TOWER_RISE", "2B71": "TERRACE_RISE_FROM_LOWER_LINE"}},
    "NW": {"title": "NORTH WEST ELEVATION", "set_sheet": "08", "datum_dim": "2A26",
           "tower": (-367300, -790900, -362700, -788600), "terrace": (-373500, -794460, -368000, -792700),
           "dims": {"2EDE": "TOWER_RISE", "2CF9": "TERRACE_RISE_FROM_RAILING", "2A34": "PARAPET_ABOVE_ROOF"}}}
PROFILE_RESIDUAL_MM = 6.0
# ------------------------------------------------------------------ visual records (12-sheet set, read in session)
PX_PER_M_SHEET11 = 156.9                    # '420' (+9.70 -> +13.90) spans 659 px on sheet 11
VISUAL = [
    {"ID": "VR-S8.3-01", "SET_SHEET": "11", "PART": "ARCH_PART_2_PAGES_07-12", "PAGE": 5, "TITLE": "SECTION B-B 1:100",
     "BOX_UPRIGHT_PX": [2150, 1350, 3150, 2050], "READ": "terrace dome (left) on a vertical drum over the +9.70 roof; "
     "dome drawn as seen (meridian lines), not cut: no shell thickness shown",
     "PX": {"apex_y": 1449, "springing_y": 1750, "roof_top_y": 1945, "outer_x": [2265, 2962]}},
    {"ID": "VR-S8.3-02", "SET_SHEET": "11", "PART": "ARCH_PART_2_PAGES_07-12", "PAGE": 5, "TITLE": "SECTION B-B 1:100",
     "BOX_UPRIGHT_PX": [4400, 1250, 5900, 2050], "READ": "terrace dome (right) on a vertical drum; printed '130' from "
     "the +9.70 roof to the springing line; '420' (+9.70 -> +13.90) spans 659 px",
     "PX": {"apex_y": 1451, "springing_y": 1748, "roof_top_y": 1948, "outer_x": [4540, 5232]}},
    {"ID": "VR-S8.3-03", "SET_SHEET": "11", "PART": "ARCH_PART_2_PAGES_07-12", "PAGE": 5, "TITLE": "SECTION B-B 1:100",
     "BOX_UPRIGHT_PX": [3208, 869, 3912, 1201], "READ": "tower dome drawn on top of the tower block", "PX": {}},
    {"ID": "VR-S8.3-04", "SET_SHEET": "10", "PART": "ARCH_PART_2_PAGES_07-12", "PAGE": 4, "TITLE": "SECTION A-A 1:100",
     "BOX_UPRIGHT_PX": [2981, 1200, 4078, 1366], "READ": "the section cuts the tower block: +13.90 roof with a 50 cm "
     "parapet and NO dome above it", "PX": {}},
    {"ID": "VR-S8.3-05", "SET_SHEET": "10", "PART": "ARCH_PART_2_PAGES_07-12", "PAGE": 4, "TITLE": "SECTION A-A 1:100",
     "BOX_UPRIGHT_PX": [2422, 1449, 3001, 1966], "READ": "a terrace dome in view beyond the cut, on the +9.70 roof",
     "PX": {}},
    {"ID": "VR-S8.3-06", "SET_SHEET": "01-12", "PART": "ALL", "PAGE": None, "TITLE": "title blocks",
     "BOX_UPRIGHT_PX": None, "READ": "owner, plot, parcel and area fields only; no consultant, revision or issue date "
     "(owner name not reproduced)", "PX": {}}]


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


def _r(v, nd=6):
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
    need = {"ST7757.dxf": BY_SHA / f"{STRUCT_SHA}.dxf", "P7757.dxf": BY_SHA / f"{ARCH_SHA}.dxf",
            **{k: BY_SHA / f"{s}.pdf" for k, s in SET_PARTS.items()}}
    absent = [k for k, p in need.items() if not p.exists()]
    check(not absent, f"private inputs not in data/inputs/by_sha256 (never committed): {absent}")
    check(_sha(need["ST7757.dxf"]) == STRUCT_SHA and _sha(need["P7757.dxf"]) == ARCH_SHA, "drawings unchanged")
    for k, s in SET_PARTS.items():
        check(_sha(need[k]) == s, f"{k} unchanged")
    return {k: DR.verify_frozen(m, ROOT) for k, m in MANIFESTS.items()}


def source_register(frozen):
    man = {o["sha256"]: o for o in _j(READ["SOURCE_MANIFEST"])["files"] if isinstance(o, dict) and o.get("sha256")}
    rows = []

    def add(sid, name, sha, role, disc, use, state, note=""):
        rows.append({"SOURCE_ID": sid, "FILE": name, "SHA256": sha, "REGISTERED": sha in man, "DISCIPLINE": disc,
                     "ROLE_IN_S8_3": role, "USED_FOR": use, "ACQUISITION": state, "NOTE": note})
    add("SRC-01", "ST7757.dxf", STRUCT_SHA, "STRUCTURAL_AUTHORITY", "STRUCTURAL",
        "p.5 ring bands, opening, framing, columns, SEE DETAIL; p.6 outline repeats; p.7 DETAIL OF DOME",
        "REGISTERED_ORIGINAL")
    add("SRC-02", "ST7757.pdf", STRUCT_PDF_SHA, "PLOT_OF_SRC-01", "STRUCTURAL", "not read: the DXF is its source",
        "REGISTERED_ORIGINAL")
    add("SRC-03", "P7757.dxf", ARCH_SHA, "ARCHITECTURAL_EVIDENCE", "ARCHITECTURAL",
        "second-floor plan dome circles; SE and NW elevation profiles, dimensions and levels", "REGISTERED_ORIGINAL")
    for i, (k, s) in enumerate(SET_PARTS.items(), 4):
        add(f"SRC-0{i}", f"{SET_KEY} {k}", s, "ARCHITECTURAL_EVIDENCE (parent evidence of the set)", "ARCHITECTURAL",
            "visual records: sections A-A and B-B" if "07-12" in k else "not needed (plans read from the DXF)",
            "UPLOADED_SET_PART", "additional evidence; not a replacement for the earlier registered PDFs")
    for i, (s, part) in enumerate(sorted(RECONSTRUCTED.items(), key=lambda kv: kv[1]), 6):
        add(f"SRC-0{i}", man.get(s, {}).get("file", "?"), s, "NOT USED", "ARCHITECTURAL",
            "not read: its parent set part is the evidence", RECON_STATE,
            f"rebuilt byte for byte from {part}; never a separately obtained original")
    for i, (k, m) in enumerate(sorted(frozen.items()), 8):
        add(f"SRC-F{i - 7:02d}", m["manifest"], m["manifest_sha256"], "FROZEN_URBAN_STAGE", "URBAN", "verified, not "
            "written" + (" and read" if k in ("S6", "S6.1", "S7", "S7A") else ""), "FROZEN")
    for i, (k, p) in enumerate(READ.items(), 1):
        add(f"SRC-R{i:02d}", str(p.relative_to(ROOT)), _sha(p), "URBAN_REGISTER_READ", "URBAN", k, "TRACKED")
    return rows


# ------------------------------------------------------------------ structural plan (p.5): domes, bands, framing
def _world(raw, frame):
    """A model-space ARC / CIRCLE -> a CCW arc in sheet-local coordinates (OCS -> world first)."""
    t = raw.dxftype()
    a0, a1 = (raw.dxf.start_angle, raw.dxf.end_angle) if t == "ARC" else (0.0, 360.0)
    a = G.world_arc((raw.dxf.center.x, raw.dxf.center.y), raw.dxf.radius, a0, a1,
                    tuple(raw.dxf.get("extrusion", (0.0, 0.0, 1.0))), full=(t == "CIRCLE"))
    a["c"] = (a["c"][0] - frame[0], a["c"][1] - frame[1])
    a["handle"] = raw.dxf.handle
    return a


def structural_plan(src, S1):
    frame = src.sheets[SHEET_PLAN]["frame"]
    curves = []
    for e in src.entities()[SHEET_PLAN]:
        if e["type"] in ("ARC", "CIRCLE") and e["layer"] == RING_LAYER and e["via"] is None \
                and RING_RADII[0] <= e["r"] <= RING_RADII[1]:
            w = _world(src.doc.entitydb[e["handle"]], frame)
            check(math.dist(w["c"], e["c"]) < 1e-2, f"{e['handle']}: S1 local centre equals the world centre")
            curves.append(w)
    groups = defaultdict(list)
    for w in curves:
        groups[(round(w["c"][0]), round(w["c"][1]))].append(w)
    check(len(groups) == 2, f"two dome centres on {SHEET_PLAN} (found {len(groups)})")
    texts = src.entities()[SHEET_PLAN]
    segs, arcs, _ = S1.beam_linework(src, SHEET_PLAN)
    s1_arc = S1.arc_bands(arcs)
    straight = S1.straight_bands(segs)
    domes = {}
    for tag, key in zip(("DOME-A", "DOME-B"), sorted(groups)):
        g = groups[key]
        c = g[0]["c"]
        check(all(math.dist(x["c"], c) < 1.0 for x in g), "concentric ring edges")
        r_in, r_out = min(x["r"] for x in g), max(x["r"] for x in g)
        inner = [x for x in g if abs(x["r"] - r_in) < 1e-6]
        outer = [x for x in g if abs(x["r"] - r_out) < 1e-6]
        bands = G.band_segments(inner, outer)
        rel = lambda p: (p[0] - c[0], p[1] - c[1])                                       # noqa: E731
        see = [t for t in texts if t["type"] in ("TEXT", "MTEXT") and t["text"].upper() == "SEE DETAIL"
               and math.dist(t["p"], c) < r_out]
        opening = [t for t in texts if t["type"] == "LINE" and t["layer"] == "S-OPENING"
                   and math.dist(t["a"], c) < 1.0]
        cols = [p for p in texts if p["type"] == "LWPOLYLINE" and p["layer"] == "S-COL.BON" and p["closed"]
                and any(math.dist(q, c) < r_out + 50 for q in p["pts"])]
        # framing: straight bands parallel to an axis whose centreline passes within reach of the centre
        frame_b = []
        for b in straight:
            a0, a1 = rel(b["centre_a"]), rel(b["centre_b"])
            L2 = (a1[0] - a0[0]) ** 2 + (a1[1] - a0[1]) ** 2
            t = max(0.0, min(1.0, -(a0[0] * (a1[0] - a0[0]) + a0[1] * (a1[1] - a0[1])) / L2)) if L2 else 0.0
            d = math.hypot(a0[0] + t * (a1[0] - a0[0]), a0[1] + t * (a1[1] - a0[1]))
            if d < FRAMING_REACH:
                vertical = abs(b["dir"][0]) < 1e-6
                off = a0[0] if vertical else a0[1]
                frame_b.append({"band_id": b["band_id"], "width": b["width_mm"], "vertical": vertical,
                                "offset": off, "span": sorted([a0[1], a1[1]] if vertical else [a0[0], a1[0]]),
                                "edges": b["edges"], "near_face": abs(off) - b["width_mm"] / 2.0})
        faces = {}
        for side, vert, sign in (("+x", True, 1), ("-x", True, -1), ("+y", False, 1), ("-y", False, -1)):
            # a framing member runs across the dome: its extent along its own direction straddles the centre
            cand = [f for f in frame_b if f["vertical"] == vert and f["offset"] * sign > 0
                    and f["span"][0] < 0.0 < f["span"][1]]
            check(cand, f"{tag}: a framing member on side {side}")
            best = min(cand, key=lambda f: f["near_face"])
            faces[side] = {"face": sign * best["near_face"], "band_id": best["band_id"], "width": best["width"]}
        bay = G.axis_rect(faces["-x"]["face"], faces["-y"]["face"], faces["+x"]["face"], faces["+y"]["face"])
        s1 = [b for b in s1_arc if math.dist(b["centre"], c) < 1.0]
        domes[tag] = {"centre": c, "r_in": r_in, "r_out": r_out, "inner": inner, "outer": outer, "bands": bands,
                      "see_detail": sorted(t["handle"] for t in see),
                      "opening_lines": sorted(t["handle"] for t in opening),
                      "opening_line_lengths": sorted({round(math.dist(t["a"], t["b"]), 1) for t in opening}),
                      "columns": [{"handle": p["handle"], "box": [min(q[0] for q in p["pts"]) - c[0],
                                                                   min(q[1] for q in p["pts"]) - c[1],
                                                                   max(q[0] for q in p["pts"]) - c[0],
                                                                   max(q[1] for q in p["pts"]) - c[1]]} for p in cols],
                      "framing": frame_b, "faces": faces, "bay": bay, "s1_bands": s1}
    # the ring band ids S1 / S6 use for each of our segments (same centre, same start angle)
    for tag, d in domes.items():
        for b in d["bands"]:
            hit = [s for s in d["s1_bands"] if abs(G.norm_deg(s["start_deg"] - b["start"])) < 0.01
                   or abs(G.norm_deg(s["start_deg"] - b["start"]) - 360) < 0.01]
            check(len(hit) == 1, f"{tag}: one S1 band at start {b['start']:.3f}")
            b["band_id"], b["s1_length_mm"], b["s1_sweep_deg"] = hit[0]["band_id"], hit[0]["length_mm"], hit[0]["sweep_deg"]
    # repeats of the dome outlines on the upper roof sheet
    up = src.sheets[SHEET_UPPER]["frame"]
    repeats = []
    for e in src.entities()[SHEET_UPPER]:
        if e["type"] == "CIRCLE" and e["via"] is None and RING_RADII[0] <= e["r"] <= RING_RADII[1]:
            w = _world(src.doc.entitydb[e["handle"]], up)
            hit = [t for t, d in domes.items() if math.dist(d["centre"], w["c"]) < 1.0 and abs(d["r_in"] - w["r"]) < 1e-6]
            repeats.append({"handle": e["handle"], "layer": e["layer"], "c": w["c"], "r": w["r"], "dome": hit[0] if hit else None})
    return domes, repeats, frame


# ------------------------------------------------------------------ p.7 DETAIL OF DOME
def _dim(doc, h, frame=(0.0, 0.0)):
    d = doc.entitydb[h]
    blk = doc.blocks.get(d.dxf.geometry) if d.dxf.get("geometry") else None
    txt = [q.dxf.text if q.dxftype() == "TEXT" else q.text for q in blk if q.dxftype() in ("TEXT", "MTEXT")] if blk else []
    txt = [re.sub(r"\\[A-Za-z][^;]*;|[{}]", "", t).strip() for t in txt]
    loc = lambda v: (round(v.x - frame[0], 3), round(v.y - frame[1], 3))                    # noqa: E731
    return {"handle": h, "text": txt[0] if txt else (d.dxf.get("text") or ""), "measurement": round(d.get_measurement(), 3),
            "dp": loc(d.dxf.defpoint), "dp2": loc(d.dxf.defpoint2), "dp3": loc(d.dxf.defpoint3)}


def detail(src):
    doc = src.doc
    f = src.sheets[SHEET_DET]["frame"]
    E = {e["handle"]: e for e in src.entities()[SHEET_DET]}
    ext, intr = (_world(doc.entitydb[h], f) for h in SHELL_ARCS)
    check(math.dist(ext["c"], intr["c"]) < 1e-6 and ext["r"] > intr["r"], "the shell arcs are concentric")
    span, rise, thick, depth = (_dim(doc, h, f) for h in (SPAN_DIM, RISE_DIM, THICK_DIM, RING_DEPTH_DIM))
    check((span["text"], rise["text"], thick["text"], depth["text"]) == ("442", "190", "10", "AS PER ARCH"),
          "detail dimension texts")
    secs = []
    for h in RING_SECTIONS:
        pts = E[h]["pts"]
        secs.append({"handle": h, "x0": min(p[0] for p in pts), "x1": max(p[0] for p in pts),
                     "y0": min(p[1] for p in pts), "y1": max(p[1] for p in pts)})
    axis_x = (secs[0]["x0"] + secs[1]["x1"]) / 2.0
    units_per_mm = span["measurement"] / (float(span["text"]) * 10.0)        # NTS detail: a proportion check only
    # the shell profile: sample both arcs; the extrados must be circular and centred on the axis between the rings
    sample = lambda a: [(a["c"][0] + a["r"] * math.cos(math.radians(a["start"] + a["sweep"] * k / 40)),  # noqa: E731
                        a["c"][1] + a["r"] * math.sin(math.radians(a["start"] + a["sweep"] * k / 40))) for k in range(41)]
    prof = G.profile_check(sample(ext), 1e-6, axis_x=axis_x, axis_tol=5.0)
    springing_y = secs[0]["y1"]
    # the drawn shell meets the ring tops: extrados at the outer faces, intrados inside them
    ex_end = G.arc_end_points(ext)
    meets = all(abs(p[1] - springing_y) < 1.0 for p in ex_end) and \
        abs(min(p[0] for p in ex_end) - secs[0]["x0"]) < 1.0 and abs(max(p[0] for p in ex_end) - secs[1]["x1"]) < 1.0
    # labels: the shell labels' leader tips against the drawn bar line and the hoop dots
    bar = E[SHELL_BAR_LINE]
    bar_r = [a[2] for a in bar["segs"] if a[0] == "ARC"]
    dots = [e for e in src.entities()[SHEET_DET] if e["type"] == "INSERT" and e.get("name") == HOOP_DOT_BLOCK]
    dot_r = sorted({round(math.dist(((d["bbox"][0] + d["bbox"][2]) / 2, (d["bbox"][1] + d["bbox"][3]) / 2), ext["c"]))
                    for d in dots})
    dot_w = sorted({round(d["bbox"][2] - d["bbox"][0], 1) for d in dots})
    shell_labels = []
    for h, lead in SHELL_LABELS.items():
        ln = E[lead]
        tip = min((ln["a"], ln["b"]), key=lambda p: abs(math.dist(p, ext["c"]) - intr["r"] - (ext["r"] - intr["r"]) / 2))
        rt = math.dist(tip, ext["c"])
        to_line = abs(rt - bar_r[0]) if bar_r else None
        to_dots = abs(rt - (dot_r[0] + dot_w[0] / 2.0)) if dot_r else None
        shell_labels.append({"handle": h, "text": E[h]["text"], "leader": lead, "tip_radius": round(rt, 1),
                             "points_at": "MERIDIONAL_BAR_LINE" if to_line < to_dots else "HOOP_BAR_DOTS"})
    check(sorted(x["points_at"] for x in shell_labels) == ["HOOP_BAR_DOTS", "MERIDIONAL_BAR_LINE"],
          "one shell label points at the drawn meridional bar, the other at the hoop dots")
    # ring section bars as drawn (graphic only): dots inside each cut
    ring_dots = []
    for s in secs:
        inside = [e for e in src.entities()[SHEET_DET] if e["type"] == "CIRCLE" and e["layer"] == "S-HAT.BAT"
                  and s["x0"] < e["c"][0] < s["x1"] and s["y0"] < e["c"][1] < s["y1"]]
        ring_dots.append({"section": s["handle"], "dots": len(inside),
                          "radii": sorted({round(e["r"], 1) for e in inside})})
    ring_labels = []
    for h, (fam, rep) in RING_LABELS.items():
        ring_labels.append({"family": fam, "handles": [h, rep], "texts": [E[h]["text"], E[rep]["text"]]})
    check(all(len(set(x["texts"])) == 1 for x in ring_labels), "left and right ring cuts carry the same labels")
    return {"ext": ext, "intr": intr, "span": span, "rise": rise, "thick": thick, "depth": depth, "sections": secs,
            "axis_x": axis_x, "units_per_mm": units_per_mm, "profile": prof, "springing_y": springing_y,
            "shell_meets_ring_outer_faces": meets, "bar_line_r": bar_r, "hoop_dots": len(dots), "hoop_dot_r": dot_r,
            "shell_labels": shell_labels, "ring_dots": ring_dots, "ring_labels": ring_labels}


# ------------------------------------------------------------------ architecture (P7757 DXF)
def _lines_in(msp, win, layer="5"):
    x0, y0, x1, y1 = win
    out = []
    for e in msp.query(f'LINE[layer=="{layer}"]'):
        a, b = e.dxf.start, e.dxf.end
        if all(x0 <= p.x <= x1 and y0 <= p.y <= y1 for p in (a, b)) and abs(a.x - b.x) > 1 and abs(a.y - b.y) > 1:
            out.append((e.dxf.handle, (a.x, a.y), (b.x, b.y)))
    return out


def _chain(segs):
    key = lambda p: (round(p[0], 1), round(p[1], 1))                                           # noqa: E731
    adj = defaultdict(list)
    for h, a, b in segs:
        adj[key(a)].append((key(b), h))
        adj[key(b)].append((key(a), h))
    ends = sorted(k for k, v in adj.items() if len(v) == 1)
    check(len(ends) == 2, "one open profile chain")
    path, seen, cur = [ends[0]], set(), ends[0]
    while True:
        nxt = [(p, h) for p, h in adj[cur] if h not in seen]
        if not nxt:
            break
        p, h = nxt[0]
        seen.add(h)
        path.append(p)
        cur = p
    check(len(seen) == len(segs), "every profile segment is in the chain")
    return path


def architecture(struct_domes, struct_frame, src):
    import ezdxf
    doc = ezdxf.readfile(BY_SHA / f"{ARCH_SHA}.dxf")
    msp = doc.modelspace()
    circles = sorted(({"handle": e.dxf.handle, "layer": e.dxf.layer, "c": G.world_arc(
        (e.dxf.center.x, e.dxf.center.y), e.dxf.radius, extrusion=tuple(e.dxf.extrusion), full=True)["c"],
        "r": e.dxf.radius} for e in msp.query("CIRCLE") if ARCH_DOME_RADII[0] <= e.dxf.radius <= ARCH_DOME_RADII[1]),
        key=lambda c: c["c"][0])
    check(len(circles) == 3, "three dome circles on the architectural plan")
    terr = [c for c in circles if abs(c["r"] - struct_domes["DOME-A"]["r_in"]) < 1e-6]
    tower = [c for c in circles if c not in terr]
    check(len(terr) == 2 and len(tower) == 1, "two terrace circles of the structural radius and one other")
    # architecture -> structural translation from the two terrace circles (one, exact, for both)
    a_w = [(d["centre"][0] + struct_frame[0], d["centre"][1] + struct_frame[1]) for d in
           (struct_domes["DOME-A"], struct_domes["DOME-B"])]
    t = (a_w[0][0] - terr[0]["c"][0], a_w[0][1] - terr[0]["c"][1])
    t_err = math.dist((terr[1]["c"][0] + t[0], terr[1]["c"][1] + t[1]), a_w[1])
    tw_local = (tower[0]["c"][0] + t[0] - struct_frame[0], tower[0]["c"][1] + t[1] - struct_frame[1])
    elev = {}
    for k, cfg in ELEVATIONS.items():
        datum = _dim(doc, cfg["datum_dim"])
        check(datum["text"] == "1440", f"{k}: the 1440 overall height dimension is the datum chain")
        y0 = datum["dp2"][1]
        lvl = lambda y: (y - y0) / 1000.0                                                    # noqa: E731
        out = {"datum_y": y0}
        for part in ("tower", "terrace"):
            path = _chain(_lines_in(msp, cfg[part]))
            c, Rf, res = G.circle_fit(path)
            apex = max(path, key=lambda p: p[1])
            out[part] = {"vertices": len(path), "centre_level": lvl(c[1]), "R_mm": Rf, "max_residual_mm": res,
                         "apex_level": lvl(apex[1]), "lowest_vertex_level": lvl(min(p[1] for p in path)),
                         "end_chord_mm": math.dist(path[0], path[-1]),
                         "state": "CIRCULAR" if res <= PROFILE_RESIDUAL_MM else "NOT_CIRCULAR"}
        out["dims"] = {}
        for h, role in cfg["dims"].items():
            d = _dim(doc, h)
            out["dims"][role] = {"handle": h, "text": d["text"], "measurement": d["measurement"],
                                 "from_level": lvl(d["dp2"][1]), "to_level": lvl(d["dp3"][1])}
        elev[k] = out
    # the tower centre on the upper structural sheet: which slab panel holds it
    panels = [p for p in _j(READ["S1_PANELS"])["rows"] if p["sheet"] == SHEET_UPPER and p.get("polygon_mm")]

    def inside(pt, poly):
        x, y = pt
        cnt = False
        for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                cnt = not cnt
        return cnt
    under = [p for p in panels if p["class"] == "SLAB_PANEL" and inside(tw_local, [tuple(q) for q in p["polygon_mm"]])]
    return {"circles": circles, "terrace": terr, "tower": tower[0], "translation": t, "translation_error_mm": t_err,
            "tower_local": tw_local, "tower_panel": [p["panel_id"] for p in under],
            "tower_panel_thickness": [p.get("effective_thickness_mm") for p in under], "elevations": elev}


# ------------------------------------------------------------------ registers
def visual_metrics():
    out = {}
    for v in VISUAL:
        p = v["PX"]
        if p.get("apex_y"):
            s = PX_PER_M_SHEET11
            out[v["ID"]] = {"rise_m": (p["springing_y"] - p["apex_y"]) / s, "drum_m": (p["roof_top_y"] - p["springing_y"]) / s,
                            "outer_width_m": (p["outer_x"][1] - p["outer_x"][0]) / s,
                            "apex_level": 9.70 + (p["roof_top_y"] - p["apex_y"]) / s,
                            "springing_level": 9.70 + (p["roof_top_y"] - p["springing_y"]) / s}
    return out


def shell_model(det):
    chord = float(det["span"]["text"]) * 10.0 / 1000.0              # printed cm -> m
    rise = float(det["rise"]["text"]) * 10.0 / 1000.0
    t = float(det["thick"]["text"]) * 10.0 / 1000.0
    Ro = G.cap_radius(chord, rise)
    return {"chord_m": chord, "rise_m": rise, "t_m": t, **G.shell_between_caps(Ro, rise, t)}


def _numeric_shell(r_out, h_out, t, n=20000):
    d = r_out - h_out
    r_in = r_out - t
    dz = h_out / n
    tot = 0.0
    for i in range(n):
        z = d + (i + 0.5) * dz
        tot += math.pi * (max(0.0, r_out * r_out - z * z) - max(0.0, r_in * r_in - z * z)) * dz
    return tot


def ring_partition(d, r1, r2):
    ann = math.pi * (r2 * r2 - r1 * r1)
    in_bay = G.annulus_rect_area((0.0, 0.0), r1, r2, d["bay"])
    return {"r1": r1, "r2": r2, "r_centreline": (r1 + r2) / 2.0, "annulus_mm2": ann, "in_bay_mm2": in_bay,
            "outside_bay_mm2": ann - in_bay}


def build():
    import alsenan_structural_s1 as S1
    frozen = verify_inputs()
    src = S1.Source()
    check(src.sha256 == STRUCT_SHA, "S1 reads the registered structural DXF")
    domes, repeats, frame = structural_plan(src, S1)
    det = detail(src)
    arch = architecture(domes, frame, src)
    vis = visual_metrics()
    shell = shell_model(det)
    um12 = UM.kg_per_m(12, UNIT_MASS)
    s6 = {r["occurrence_id"]: r for r in _rows(READ["S6_OCC"])}
    s61 = _rows(READ["S6_1_DELTA"])
    beam_defs = {r["beam_type"]: r for r in _j(READ["S1_BEAM_DEFS"])["rows"]}
    special = _j(READ["S1_SPECIAL"])
    s1_dome_rows = {r["special_id"]: r for r in special["rows"] if r.get("kind") == "DOME"}
    levels = {r["level"]: r for r in _j(READ["S1_LEVELS"])["rows"]}
    roof_level = levels["2F / 1F ROOF"]["value_m"]
    s7_items = _rows(READ["S7_ITEMS"])
    s7a = [r for r in _rows(READ["S7A_ENDS"]) if "DOME" in r["UNRESOLVED_REASON"]]
    # S1 dome ids -> our domes, through the dome-zone faces' handles (the inner ring edge is one of them)
    s1_of = {}
    for sid, r in s1_dome_rows.items():
        hs = set()
        for p in _j(READ["S1_PANELS"])["rows"]:
            if p["panel_id"] in r["dome_zone_faces"]:
                hs |= {h.split("|")[-1] for h in p.get("boundary_handles", [])}
        hit = [t for t, d in domes.items() if hs & {a["handle"] for a in d["inner"]}]
        check(len(hit) == 1, f"{sid} binds to one dome")
        s1_of[hit[0]] = {"special_id": sid, "faces": r["dome_zone_faces"], "see_detail": r["see_detail_labels"]}
    for t, d in domes.items():
        check(sorted(d["see_detail"]) == sorted(s1_of[t]["see_detail"]), f"{t}: S1 and S8.3 see the same SEE DETAIL labels")

    # ------------------------------------------------------------ 02 population
    pop = []
    names = {"DOME-A": "terrace dome A (1F roof; left of the pair on the p.5 sheet)",
             "DOME-B": "terrace dome B (1F roof; right of the pair on the p.5 sheet)"}
    arch_of = {"DOME-A": arch["terrace"][0], "DOME-B": arch["terrace"][1]}
    for t, d in domes.items():
        pop.append({"ROW_ID": f"P-{t}", "ROW_KIND": "PHYSICAL_DOME", "PHYSICAL_ID": t, "DESCRIPTION": names[t],
                    "SOURCE": "ST7757 p.5 + p.7; P7757 plan", "HANDLES": [a["handle"] for a in d["inner"] + d["outer"]],
                    "STRUCTURAL": True, "COUNTED_AS_PHYSICAL": True,
                    "EVIDENCE": f"ring band r {d['r_in']:.1f}-{d['r_out']:.1f} about {tuple(round(v, 1) for v in d['centre'])}; "
                                f"{len(d['see_detail'])} SEE DETAIL labels; {len(d['opening_lines'])} radial S-OPENING lines; "
                                f"S1 {s1_of[t]['special_id']}"})
    pop.append({"ROW_ID": "P-DOME-TOWER", "ROW_KIND": "PHYSICAL_DOME_ARCH_ONLY", "PHYSICAL_ID": "DOME-TOWER",
                "DESCRIPTION": "tower dome over the second-floor roof (architectural only)", "SOURCE": "P7757 plan + elevations",
                "HANDLES": [arch["tower"]["handle"]], "STRUCTURAL": False, "COUNTED_AS_PHYSICAL": True,
                "EVIDENCE": f"architectural circle r {arch['tower']['r']:.1f}; on structural p.6 the place is the flat panel "
                            f"{arch['tower_panel']} ({arch['tower_panel_thickness']} mm); no structural dome occurrence"})
    for x in repeats:
        pop.append({"ROW_ID": f"O-SFRS-{x['handle']}", "ROW_KIND": "REPEATED_OUTLINE", "PHYSICAL_ID": x["dome"],
                    "DESCRIPTION": f"outline on {SHEET_UPPER} (layer {x['layer']}) at the same place and radius",
                    "SOURCE": "ST7757 p.6", "HANDLES": [x["handle"]], "STRUCTURAL": True, "COUNTED_AS_PHYSICAL": False,
                    "EVIDENCE": "the upper roof sheet shows the lower terrace domes below; same centre to 1 mm"})
    for t, c in arch_of.items():
        pop.append({"ROW_ID": f"O-ARCH-{c['handle']}", "ROW_KIND": "ARCH_PLAN_OUTLINE", "PHYSICAL_ID": t,
                    "DESCRIPTION": "architectural second-floor plan circle 'R221' on the +9.70 roof",
                    "SOURCE": "P7757 plan (set sheet 05)", "HANDLES": [c["handle"]], "STRUCTURAL": False,
                    "COUNTED_AS_PHYSICAL": False,
                    "EVIDENCE": f"same radius {c['r']:.1f}; one translation maps both circles onto the structural centres "
                                f"(residual {arch['translation_error_mm']:.3f} mm)"})
    for k, e in arch["elevations"].items():
        seen = "DOME-A" if k == "SE" else "DOME-B"
        pop.append({"ROW_ID": f"O-{k}-TERRACE", "ROW_KIND": "ARCH_ELEVATION_VIEW", "PHYSICAL_ID": seen,
                    "DESCRIPTION": f"{ELEVATIONS[k]['title']}: the nearer terrace dome (view along plan x)",
                    "SOURCE": f"P7757 DXF (set sheet {ELEVATIONS[k]['set_sheet']})", "HANDLES": [],
                    "STRUCTURAL": False, "COUNTED_AS_PHYSICAL": False,
                    "EVIDENCE": "INFERRED_FROM_VIEW_DIRECTION: the elevations look along plan x and the two domes lie on "
                                "one plan line, so each shows only the dome on its own side; the architectural plan marks "
                                "the +x end 'SEA VIEW' (the north-west), so SE shows DOME-A and NW shows DOME-B"})
        pop.append({"ROW_ID": f"O-{k}-TOWER", "ROW_KIND": "ARCH_ELEVATION_VIEW", "PHYSICAL_ID": "DOME-TOWER",
                    "DESCRIPTION": f"{ELEVATIONS[k]['title']}: tower dome", "SOURCE": f"P7757 DXF (set sheet "
                    f"{ELEVATIONS[k]['set_sheet']})", "HANDLES": [], "STRUCTURAL": False, "COUNTED_AS_PHYSICAL": False,
                    "EVIDENCE": "drawn above the +13.90 tower roof"})
    for v in VISUAL[:5]:
        pop.append({"ROW_ID": f"O-{v['ID']}", "ROW_KIND": "VISUAL_RECORD", "PHYSICAL_ID": "DOME-TOWER" if "tower" in
                    v["READ"] else "TERRACE (one of A / B)", "DESCRIPTION": v["READ"],
                    "SOURCE": f"{SET_KEY} sheet {v['SET_SHEET']} ({v['PART']} p.{v['PAGE']})", "HANDLES": [],
                    "STRUCTURAL": False, "COUNTED_AS_PHYSICAL": False, "EVIDENCE": f"box {v['BOX_UPRIGHT_PX']}"})
    pop.append({"ROW_ID": "O-DET", "ROW_KIND": "TYPICAL_DETAIL", "PHYSICAL_ID": "DOME-A, DOME-B",
                "DESCRIPTION": "DETAIL OF DOME (N.I.S): one typical section, cut twice through the one ring",
                "SOURCE": "ST7757 p.7", "HANDLES": list(SHELL_ARCS) + list(RING_SECTIONS), "STRUCTURAL": True,
                "COUNTED_AS_PHYSICAL": False, "EVIDENCE": "bound to each dome by its four SEE DETAIL labels"})

    # ------------------------------------------------------------ 03 profile and levels
    se, nw = arch["elevations"]["SE"], arch["elevations"]["NW"]
    prof = []

    def P(i, item, value, unit, state, source, note=""):
        prof.append({"ITEM_ID": i, "ITEM": item, "VALUE": value, "UNIT": unit, "STATE": state, "SOURCE": source,
                     "NOTE": note})
    P("PR-01", "terrace dome outer chord at the springing plane", shell["chord_m"], "m", "STATED_DIMENSION",
      f"p.7 dim {SPAN_DIM} '442' between the ring outer faces at the springing level",
      f"plan ring inner circle {2 * domes['DOME-A']['r_in'] / 1000:.4f} m; section B-B outer widths "
      f"{vis['VR-S8.3-01']['outer_width_m']:.2f} / {vis['VR-S8.3-02']['outer_width_m']:.2f} m")
    P("PR-02", "terrace dome rise, springing to the outer apex", shell["rise_m"], "m", "STATED_DIMENSION",
      f"p.7 dim {RISE_DIM} '190'", f"section B-B {vis['VR-S8.3-01']['rise_m']:.2f} / {vis['VR-S8.3-02']['rise_m']:.2f} m; "
      f"SE elevation '193' from +{se['dims']['TERRACE_RISE_FROM_LOWER_LINE']['from_level']:.2f}")
    P("PR-03", "terrace dome shell thickness", shell["t_m"], "m", "STATED_DIMENSION",
      f"p.7 dim {THICK_DIM} '10' between the two shell surfaces", "drawn as concentric arcs: constant from the "
      "springing to the crown; no thickening, rib or opening drawn")
    P("PR-04", "profile of the drawn shell", det["profile"]["state"], "", "ESTABLISHED" if det["profile"]["state"] ==
      "SPHERICAL_ABOUT_AXIS" else "NOT_ESTABLISHED", f"p.7 arcs {SHELL_ARCS} concentric, centred on the axis between "
      "the two ring cuts", "structural plan: circular outline with 20 radial meridian lines (a surface of revolution)")
    P("PR-05", "architectural terrace profile (SE elevation)", se["terrace"]["state"], "",
      "CORROBORATES_FORM", "P7757 SE elevation polyline", f"circle fit R {se['terrace']['R_mm']:.1f} mm, residual "
      f"{se['terrace']['max_residual_mm']:.1f} mm; apex +{se['terrace']['apex_level']:.3f}")
    P("PR-06", "architectural terrace profile (NW elevation)", nw["terrace"]["state"], "",
      "CORROBORATES_FORM", "P7757 NW elevation polyline", f"circle fit R {nw['terrace']['R_mm']:.1f} mm, residual "
      f"{nw['terrace']['max_residual_mm']:.1f} mm; apex +{nw['terrace']['apex_level']:.3f} (0.44 m below the others)")
    P("PR-07", "outer sphere radius from the stated chord and rise", shell["r_out"], "m", "DERIVED_FROM_STATED",
      "R = (c^2/4 + h^2) / 2h", f"the drawn extrados proportion: {det['ext']['r'] / det['units_per_mm'] / 1000:.4f} m")
    P("PR-08", "centre of the sphere below the springing plane", shell["centre_below_springing"], "m",
      "DERIVED_FROM_STATED", "R - h", "the cap is less than a hemisphere")
    P("PR-09", "horizontal shell width at the springing plane", shell["springing_width"], "m", "DERIVED_FROM_STATED",
      "outer minus inner springing radius", "the shell sits on the outer part of the ring top (as drawn)")
    P("PR-10", "terrace roof level (ring and drum stand on it)", roof_level, "m", "STATED_LEVEL",
      "ST7757 p.6 '+9.70' (S1 level register); P7757 plan '+9.70'", "")
    P("PR-11", "terrace dome springing level", 9.70 + 1.30, "m", "STATED_ON_ONE_SECTION",
      "sheet 11 SECTION B-B '130' above the +9.70 roof", f"SE elevation lower line +{se['dims']['TERRACE_RISE_FROM_LOWER_LINE']['from_level']:.2f}; "
      f"section B-B measured +{vis['VR-S8.3-01']['springing_level']:.2f} / +{vis['VR-S8.3-02']['springing_level']:.2f}")
    P("PR-12", "terrace dome apex level", 9.70 + 1.30 + shell["rise_m"], "m", "DERIVED_FROM_STATED",
      "springing + rise", f"section B-B +{vis['VR-S8.3-01']['apex_level']:.2f} / +{vis['VR-S8.3-02']['apex_level']:.2f}; "
      f"SE +{se['terrace']['apex_level']:.3f}; NW +{nw['terrace']['apex_level']:.3f} (conflict CF-S8.3-05)")
    P("PR-13", "ring beam depth", None, "m", "NOT_ESTABLISHED", f"p.7 dim {RING_DEPTH_DIM} 'AS PER ARCH' (bottom to top "
      "of the ring)", "architecture shows a drum to the springing but never the ring bottom (CF-S8.3-03)")
    P("PR-14", "tower dome chord at its springing", float(se["dims"]["TOWER_CHORD"]["text"]) / 100.0, "m",
      "ARCHITECTURAL_ONLY", "P7757 SE elevation '441'", f"springing +{se['dims']['TOWER_CHORD']['from_level']:.2f}; "
      f"drawn {se['dims']['TOWER_CHORD']['measurement']:.1f} mm")
    P("PR-15", "tower dome rise", float(se["dims"]["TOWER_RISE"]["text"]) / 100.0, "m", "ARCHITECTURAL_ONLY",
      "P7757 SE / NW elevations '215'", f"drawn {se['dims']['TOWER_RISE']['measurement']:.1f} mm; circle fit R "
      f"{se['tower']['R_mm']:.1f} mm (residual {se['tower']['max_residual_mm']:.1f})")
    P("PR-16", "tower dome shell thickness", None, "m", "NOT_ESTABLISHED", "no structural or architectural thickness", "")
    P("PR-17", "openings in any dome shell", "NONE_DRAWN", "", "ESTABLISHED", "p.7 detail, p.5 plan, elevations, sections",
      "no oculus, lantern or penetration drawn in any source")

    # ------------------------------------------------------------ 04 ring geometry
    ring_rows = []
    for t, d in domes.items():
        for b in d["bands"]:
            occ = [o for o in s6.values() if json.loads(o["geometry_objects"] or "[]") == [f"ARC:{SHEET_PLAN}:{b['band_id']}"]]
            check(len(occ) == 1, f"{b['band_id']}: one S6 occurrence")
            ring_rows.append({"ROW_ID": f"{t}-{b['band_id']}", "DOME": t, "KIND": "DRAWN_BAND_SEGMENT",
                              "S6_OCCURRENCE": occ[0]["occurrence_id"], "S6_TAG": occ[0]["mark"] or "",
                              "START_DEG": b["start"], "SWEEP_DEG": b["sweep"],
                              "CROSSES_ZERO": b["start"] + b["sweep"] > 360.0,
                              "R1_MM": b["r1"], "R2_MM": b["r2"], "CENTRELINE_ARC_M": b["centreline_length"] / 1000,
                              "CENTRELINE_CHORD_M": b["chord_centreline"] / 1000, "PLAN_AREA_M2": b["area"] / 1e6,
                              "S1_LENGTH_M": b["s1_length_mm"] / 1000, "NOTE": "both edges drawn between framing members"})
        cov_out = G.coverage_deg([(a["start"], a["sweep"]) for a in d["outer"]])
        cov_in = G.coverage_deg([(a["start"], a["sweep"]) for a in d["inner"]])
        ring_rows.append({"ROW_ID": f"{t}-COVERAGE", "DOME": t, "KIND": "EDGE_COVERAGE",
                          "START_DEG": None, "SWEEP_DEG": cov_out, "R1_MM": d["r_in"], "R2_MM": d["r_out"],
                          "NOTE": f"outer edge drawn over {cov_out:.3f} deg, inner edge over {cov_in:.3f} deg "
                                  f"({'closed' if cov_in >= 360 - 1e-7 else 'broken at the side framing'}); the "
                                  "physical ring is one closed annulus, interrupted in the drawing by the framing members"})
        for side, f in d["faces"].items():
            ring_rows.append({"ROW_ID": f"{t}-FACE{side}", "DOME": t, "KIND": "BAY_FACE", "S6_OCCURRENCE": f["band_id"],
                              "R1_MM": f["face"], "NOTE": f"inner face of straight band {f['band_id']} (w {f['width']:.0f})"})
        for reading, (r1, r2) in (("PLAN", (d["r_in"], d["r_out"])), ("DETAIL", (d["r_in"] - 200.0, d["r_in"]))):
            p = ring_partition(d, r1, r2)
            d[f"part_{reading}"] = p
            ring_rows.append({"ROW_ID": f"{t}-RING-{reading}", "DOME": t, "KIND": f"RING_PARTITION_{reading}_READING",
                              "R1_MM": r1, "R2_MM": r2, "CENTRELINE_ARC_M": 2 * math.pi * p["r_centreline"] / 1000,
                              "PLAN_AREA_M2": p["in_bay_mm2"] / 1e6,
                              "NOTE": f"annulus {p['annulus_mm2'] / 1e6:.6f} m2 = inside the bay (ring) "
                                      f"{p['in_bay_mm2'] / 1e6:.6f} + inside the framing members "
                                      f"{p['outside_bay_mm2'] / 1e6:.6f}"})
        op = G.disk_rect_area((0.0, 0.0), d["r_in"], d["bay"])
        d["opening_m2"] = op / 1e6
        s1_faces = sum(p["area_m2"] for p in _j(READ["S1_PANELS"])["rows"] if p["panel_id"] in s1_of[t]["faces"])
        ring_rows.append({"ROW_ID": f"{t}-OPENING", "DOME": t, "KIND": "SLAB_OPENING_UNDER_DOME", "R2_MM": d["r_in"],
                          "PLAN_AREA_M2": op / 1e6, "NOTE": f"disk r {d['r_in']:.1f} inside the bay (exact); full disk "
                          f"{math.pi * d['r_in'] ** 2 / 1e6:.6f}; S1 dome-zone faces {s1_of[t]['faces']} sum "
                          f"{s1_faces:.3f} m2 (polygonal)"})
        for col in d["columns"]:
            bx = col["box"]
            ring_rows.append({"ROW_ID": f"{t}-COL-{col['handle']}", "DOME": t, "KIND": "COLUMN_AT_RING",
                              "PLAN_AREA_M2": G.annulus_rect_area((0, 0), d["r_in"], d["r_out"], G.axis_rect(*bx)) / 1e6,
                              "NOTE": f"column outline {[round(v) for v in bx]} (relative); plan-ring overlap shown; "
                                      "columns stay with the column stage"})

    # ------------------------------------------------------------ 05 S6 -> S8.3 ownership delta
    s6_label = DR.baseline_label(frozen["S6.1"])
    delta = []
    for t, d in domes.items():
        for b in d["bands"]:
            oid = next(r["S6_OCCURRENCE"] for r in ring_rows if r["ROW_ID"] == f"{t}-{b['band_id']}")
            o = s6[oid]
            known = sum(float(r["NEW_KNOWN_QUANTITY"] or 0) for r in s61 if r["OCCURRENCE_ID"] == oid)
            tag = o["mark"] or ""
            rec = DR.record(
                delta_id=f"S8.3-T{len(delta) + 1:02d}", change_kind=DR.OWNERSHIP_TRANSFER, frozen_baseline=s6_label,
                baseline_component_id=oid, old_state=o["occurrence_state"], old_known_quantity=known,
                new_project_source=f"ST7757 p.5 ring band of {t} + p.7 DETAIL OF DOME (SEE DETAIL x{len(d['see_detail'])})",
                source_page="5; 7", source_handles=[a["handle"] for a in d["inner"] + d["outer"]],
                graphic_evidence_class=GE.NO_GRAPHIC_EVIDENCE, new_component_model="DOME_RING_SEGMENT",
                delta_known_quantity=0.0, new_blocked_components=["RING_CONCRETE", "RING_BARS"],
                new_release_state=DR.TRANSFERRED_OUT,
                why=("segment of the closed ring of " + t + "; S6 holds it as an untagged beam" if not tag else
                     f"segment of the closed ring of {t}; S6 bound a nearby '{tag}' tag to it, which conflicts with the "
                     "DETAIL OF DOME (CF-S8.3-04)"),
                DOME=t, BAND_ID=b["band_id"], S6_TAG=tag, NEW_OWNER="S8.3 DOME RING (" + t + ")",
                SEGMENT_START_DEG=_r(b["start"], 6), SEGMENT_SWEEP_DEG=_r(b["sweep"], 6))
            delta.append(rec)

    # ------------------------------------------------------------ 06 concrete
    conc = []

    def C(i, dome, comp, lane, m3, basis, missing="", note=""):
        conc.append({"ITEM_ID": i, "DOME": dome, "COMPONENT": comp, "LANE": lane, "M3": m3,
                     "RELEASED": lane in RELEASED_LANES and m3 is not None, "BASIS": basis, "STILL_MISSING": missing,
                     "NOTE": note})
    for t in domes:
        C(f"CQ-{t}-SHELL", t, "SHELL", PROJECT_BASIS_QTO, shell["volume"],
          "solid between concentric spheres above the springing plane: outer chord 4.42 m, rise 1.90 m to the outer "
          "apex, thickness 0.10 m normal to the surface (p.7 printed dimensions; spherical form from the drawn arcs)",
          note="the shell owns everything above the springing plane; nothing below it")
        C(f"CQ-{t}-RING", t, "RING_BEAM", CONFLICT, None, "", "ring depth 'AS PER ARCH' (not established); ring plan "
          "position: plan band r 2211-2411 vs detail band under the shell edge (CF-S8.3-02, -03)",
          "plan areas for both readings are in 04; m3 only as sensitivity (12)")
        C(f"CQ-{t}-DRUM", t, "DRUM_BETWEEN_ROOF_AND_SPRINGING", BLOCKED, None, "", "architecture draws a 1.30 m drum; "
          "whether it is the RC ring itself or a wall under it is not stated", "")
        C(f"CQ-{t}-OPENING", t, "SLAB_OPENING_UNDER_DOME", "NOT_APPLICABLE", None,
          f"no slab: the 1F roof is open inside the dome circle ({domes[t]['opening_m2']:.6f} m2 inside the bay)",
          note="S7 releases no item on the dome-zone faces")
    C("CQ-DOME-TOWER-SHELL", "DOME-TOWER", "SHELL", CONFLICT, None, "", "architectural only: no structural dome, "
      "thickness, ring or support (CF-S8.3-01)", "")

    # ------------------------------------------------------------ 07 notation register
    notes = []
    for x in det["shell_labels"]:
        notes.append({"NOTATION_ID": f"N-{x['handle']}", "HANDLES": [x["handle"], x["leader"]], "RAW": x["text"],
                      "DIAMETER_MM": 12, "COUNT": None, "SPACING_MM": 150, "RATE_PER_M": None,
                      "ROLE": "SHELL_MERIDIONAL" if x["points_at"] == "MERIDIONAL_BAR_LINE" else "SHELL_HOOP",
                      "DIRECTION": "RADIAL (meridian)" if x["points_at"] == "MERIDIONAL_BAR_LINE" else "CIRCUMFERENTIAL",
                      "LAYERS_DRAWN": 1, "BOUND_BY": f"leader tip at r {x['tip_radius']} on the {x['points_at'].lower()}",
                      "FAMILY": "SHELL_MERIDIONAL" if x["points_at"] == "MERIDIONAL_BAR_LINE" else "SHELL_HOOP",
                      "NOTE": "one mesh drawn near the intrados; S1 read 'two layers' from the two labels (CF-S8.3-07)"})
    for x in det["ring_labels"]:
        raw = x["texts"][0]
        m = re.match(r"(\d+)%%c(\d+)(?:/(\d+)cm|/m)?", raw, re.I)
        cnt, dia = int(m.group(1)), int(m.group(2))
        per_m = raw.lower().endswith("/m")
        spacing = int(m.group(3)) * 10 if m.group(3) else None
        notes.append({"NOTATION_ID": f"N-{x['handles'][0]}", "HANDLES": x["handles"], "RAW": raw, "DIAMETER_MM": dia,
                      "COUNT": None if per_m else cnt, "SPACING_MM": spacing, "RATE_PER_M": cnt if per_m else None,
                      "ROLE": x["family"], "DIRECTION": "LONGITUDINAL (along the ring)" if x["family"] != "RING_LINKS"
                      else "TRANSVERSE (closed link round the section)", "LAYERS_DRAWN": None,
                      "BOUND_BY": "labels on both cuts of the one ring section (left and right): one family",
                      "FAMILY": x["family"], "NOTE": {"RING_SIDE": "two per face drawn at 20 cm in a depth that is "
                      "'AS PER ARCH': the number of rows depends on the depth", "RING_LINKS": "8 per metre of ring",
                      }.get(x["family"], "explicit count per section")})
    notes.append({"NOTATION_ID": f"N-{SHELL_BAR_LINE}", "HANDLES": [SHELL_BAR_LINE], "RAW": "(drawn bar, no text)",
                  "DIAMETER_MM": 12, "ROLE": "SHELL_BAR_INTO_RING", "DIRECTION": "meridian continuing down each ring "
                  "cut to its bottom, then a short hook inward", "LAYERS_DRAWN": 1, "FAMILY": "SHELL_ANCHORAGE",
                  "BOUND_BY": "the meridional bar line itself", "NOTE": "anchorage length is graphic only (N.I.S, depth "
                  "'AS PER ARCH')"})
    notes.append({"NOTATION_ID": f"N-{RING_LINK}", "HANDLES": [RING_LINK], "RAW": "(drawn link, no text)",
                  "DIAMETER_MM": 8, "ROLE": "RING_LINK_SHAPE", "DIRECTION": "closed rectangle inside the ring cut",
                  "FAMILY": "RING_LINKS", "BOUND_BY": "drawn inside the left ring cut",
                  "NOTE": "its size follows the ring depth"})
    notes.append({"NOTATION_ID": "N-RING-DOTS", "HANDLES": [x["section"] for x in det["ring_dots"]],
                  "RAW": f"bar dots in the two cuts: {[x['dots'] for x in det['ring_dots']]}", "ROLE": "GRAPHIC_ONLY",
                  "FAMILY": "RING_TOP / RING_BOTTOM / RING_SIDE", "BOUND_BY": "drawing", "NOTE": "the left cut draws all "
                  "3 + 3 + 2 x 2; the right cut draws a part of them: graphic completeness, not another family"})
    notes.append({"NOTATION_ID": "N-HOOP-DOTS", "HANDLES": [HOOP_DOT_BLOCK], "RAW": f"{det['hoop_dots']} dots on r "
                  f"{det['hoop_dot_r']} (detail units)", "ROLE": "GRAPHIC_ONLY", "FAMILY": "SHELL_HOOP",
                  "BOUND_BY": "drawing", "NOTE": "drawn about every 100 mm: graphic, never a count"})

    # ------------------------------------------------------------ 08 rebar QTO
    bars = []

    def B(i, dome, fam, lane, dia, length_m=None, basis="", missing="", note=""):
        kg = None if length_m is None else length_m * UM.kg_per_m(dia, UNIT_MASS)
        bars.append({"ITEM_ID": i, "DOME": dome, "FAMILY": fam, "LANE": lane, "DIAMETER_MM": dia,
                     "EQUIVALENT_LENGTH_M": length_m, "UNIT_MASS_KG_M": UM.kg_per_m(dia, UNIT_MASS) if dia else None,
                     "KG": kg, "RELEASED": lane in RELEASED_LANES and kg is not None, "BASIS": basis,
                     "STILL_MISSING": missing, "NOTE": note})
    body = G.length_at_spacing(shell["area_mid"], 0.150)
    for t in domes:
        for fam in ("SHELL_MERIDIONAL", "SHELL_HOOP"):
            B(f"RQ-{t}-{fam}", t, fam, PROJECT_BASIS_QTO, 12, body,
              "rate density over the shell mid-surface: area / 0.150 m (continuous, unrounded); one mesh as drawn",
              "fabrication count, crown curtailment, laps", "no lap, hook, anchorage or second mesh included")
        B(f"RQ-{t}-SHELL_ANCHORAGE", t, "SHELL_ANCHORAGE", BLOCKED, 12, missing="leg length into the ring follows the "
          "'AS PER ARCH' depth; the detail is N.I.S")
        for fam, dia in (("RING_TOP", 16), ("RING_BOTTOM", 18)):
            extra = "; dome A ring segments also tagged B4 (2T12 / 4T16 schedule) (CF-S8.3-04)" if t == "DOME-A" else ""
            B(f"RQ-{t}-{fam}", t, fam, CONFLICT, dia, missing="ring centreline radius: plan 2311.1 vs detail 2111.1 "
              f"(CF-S8.3-02); laps and continuity through the framing junctions{extra}",
              note="count stated (3); length only as sensitivity")
        B(f"RQ-{t}-RING_SIDE", t, "RING_SIDE", BLOCKED, 14, missing="rows at 20 cm over a depth 'AS PER ARCH'")
        B(f"RQ-{t}-RING_LINKS", t, "RING_LINKS", BLOCKED, 8, missing="link size follows the ring depth; 8 / m along "
          "the ring is stated")
        B(f"RQ-{t}-RING_LAPS", t, "RING_LAPS_AND_JUNCTIONS", BLOCKED, None, missing="no lap or junction detail with the "
          "framing beams and columns")
    B("RQ-DOME-TOWER", "DOME-TOWER", "ALL", CONFLICT, None, missing="no structural dome (CF-S8.3-01)")

    # ------------------------------------------------------------ 09 blocked components
    blocked = [{"BLOCK_ID": f"BL-{i:02d}", "DOME": r["DOME"], "COMPONENT": r.get("COMPONENT") or r.get("FAMILY"),
                "LANE": r["LANE"], "WHY": r["STILL_MISSING"] or r["NOTE"], "QUANTITY": None}
               for i, r in enumerate([x for x in conc + bars if x["LANE"] in (BLOCKED, CONFLICT)], 1)]

    # ------------------------------------------------------------ 10 conflicts and questions
    a_side = domes["DOME-A"]["faces"]
    b_side = domes["DOME-B"]["faces"]
    cq = [
        {"ID": "CF-S8.3-01", "KIND": "SOURCE_CONFLICT", "STATUS": "OPEN (carries PS8-C01)", "SUBJECT": "tower dome",
         "NOTE": f"architecture draws a third dome (r {arch['tower']['r']:.0f}, chord 4.41 m, rise 2.15 m, springing "
                 f"+{se['dims']['TOWER_CHORD']['from_level']:.2f}) on the plan, both elevations and section B-B, but "
                 f"section A-A, which cuts the tower, draws none; structurally the place is the flat panel "
                 f"{arch['tower_panel']} that S7 releases. Not counted, not quantified."},
        {"ID": "CF-S8.3-02", "KIND": "SOURCE_CONFLICT", "STATUS": "OPEN", "SUBJECT": "ring beam plan position",
         "NOTE": "the to-scale plan draws the 200 band outside the dome circle (r 2211.1-2411.1); the N.I.S detail puts "
                 "the '442' span between the ring OUTER faces, the shell extrados meeting them, so the ring lies under "
                 "the shell edge (r 2011.1-2211.1); section B-B draws the drum outer face on the dome outer face."},
        {"ID": "CF-S8.3-03", "KIND": "SOURCE_CONFLICT", "STATUS": "OPEN", "SUBJECT": "ring beam depth",
         "NOTE": "p.7 dimensions the ring depth 'AS PER ARCH'; architecture draws a drum 1.30 m above the +9.70 roof but "
                 "not the ring bottom; the B4 schedule row (dome A tags) says 50 cm; the drawn N.I.S depth is never used."},
        {"ID": "CF-S8.3-04", "KIND": "SOURCE_CONFLICT", "STATUS": "OPEN", "SUBJECT": "dome A ring type",
         "NOTE": f"two of dome A's four ring segments carry 'B4' tags (S6 bound them): B4 = "
                 f"{beam_defs['B4']['B_cm']:.0f} x {beam_defs['B4']['H_cm']:.0f} cm, top 2T12, bottom 4T16, 6T8/m; the "
                 "DETAIL OF DOME (SEE DETAIL x4) gives 3T16 / 3T18 / 2T14@20 / 8T8/m. Dome B carries no tag."},
        {"ID": "CF-S8.3-05", "KIND": "SOURCE_CONFLICT", "STATUS": "OPEN", "SUBJECT": "terrace dome level (NW elevation)",
         "NOTE": f"NW elevation apex +{nw['terrace']['apex_level']:.3f}; SE elevation +{se['terrace']['apex_level']:.3f}; "
                 f"section B-B +{vis['VR-S8.3-01']['apex_level']:.2f} / +{vis['VR-S8.3-02']['apex_level']:.2f}. No "
                 "quantity depends on it."},
        {"ID": "CF-S8.3-06", "KIND": "SOURCE_CONFLICT", "STATUS": "RECORDED", "SUBJECT": "architectural elevation radius",
         "NOTE": f"the elevation profiles fit R {se['terrace']['R_mm']:.0f} / {nw['terrace']['R_mm']:.0f} mm; a 4.42 m "
                 "chord needs R >= 2.21 m; the structural cap is R 2.235 m. Form agrees, size differs slightly."},
        {"ID": "CF-S8.3-07", "KIND": "INTERPRETATION", "STATUS": "RESOLVED_BY_DRAWING", "SUBJECT": "shell mesh layers",
         "NOTE": "S1 read 'two layers' from the two 'Ø12MM/15cm' labels; their leaders point one at the drawn meridional "
                 "bar and one at the hoop dots: one mesh, two directions. A second mesh is a sensitivity case only."},
        {"ID": "CF-S8.3-08", "KIND": "SOURCE_CONFLICT", "STATUS": "OPEN", "SUBJECT": "dome circle against its bay",
         "NOTE": f"dome A's circle (r {domes['DOME-A']['r_in']:.1f}) crosses its side framing faces at x "
                 f"{a_side['-x']['face']:.0f} / {a_side['+x']['face']:.0f}; dome B's at {b_side['+x']['face']:.0f}: "
                 "the shell edge / ring would bear partly on the side beams."},
        {"ID": "CF-S8.3-09", "KIND": "SOURCE_CONFLICT", "STATUS": "RECORDED", "SUBJECT": "springing level",
         "NOTE": f"section B-B '130' gives +11.00; the SE elevation's lower dimension line is "
                 f"+{se['dims']['TERRACE_RISE_FROM_LOWER_LINE']['from_level']:.2f}. No quantity depends on it."},
        {"ID": "PS8-C02", "KIND": "OWNERSHIP", "STATUS": "RESOLVED_BY_TRANSFER", "SUBJECT": "S6 dome ring arcs",
         "NOTE": f"all eight ring segments (BA001-BA008, six untagged + two tagged B4) transfer to S8.3 with 0 kg (05)"},
        {"ID": "Q-S8.3-01", "KIND": "QUESTION", "STATUS": "OPEN", "SUBJECT": "Engineer",
         "NOTE": "Engineer: give the ring beam depth and its plan position relative to the dome edge (outside the 4.42 m "
                 "circle as on p.5, or under the shell edge as on p.7), and whether the 1.30 m drum is RC."},
        {"ID": "Q-S8.3-02", "KIND": "QUESTION", "STATUS": "OPEN", "SUBJECT": "Engineer",
         "NOTE": "Engineer: do the 'B4' tags on dome A's ring apply, or does the DETAIL OF DOME govern both rings?"},
        {"ID": "Q-S8.3-03", "KIND": "QUESTION", "STATUS": "OPEN", "SUBJECT": "Architect / engineer",
         "NOTE": "Architect / engineer: is the tower dome built (section A-A omits it), and in what material, thickness "
                 "and support? Does the +13.90 slab under it change?"},
        {"ID": "Q-S8.3-04", "KIND": "QUESTION", "STATUS": "OPEN", "SUBJECT": "Engineer",
         "NOTE": "Engineer: anchorage of the shell bars into the ring, laps of the ring bars, and the junction detail "
                 "with the framing beams and columns."}]

    # ------------------------------------------------------------ 11 interfaces
    s7_by_dome = defaultdict(float)
    face_dome = {f: t for t, v in s1_of.items() for f in v["faces"]}
    for r in s7a:
        s7_by_dome[face_dome[r["BEYOND_PANEL"]]] += float(r["S7_TOP_EXTENSION_KG_AT_END"])
    s7_total = sum(float(r["S7_TOP_EXTENSION_KG_AT_END"]) for r in s7a)
    s7_zone_items = [r for r in s7_items if r["PANEL_ID"] in face_dome]
    tower_items = [r for r in s7_items if r["PANEL_ID"] in arch["tower_panel"]]
    inter = [
        {"INTERFACE": "SHELL -> RING", "SIDE_A": "S8.3 shell (above the springing plane)",
         "SIDE_B": "S8.3 ring (below it)", "CONCRETE": "split at the springing plane: disjoint", "BARS": "shell bars "
         "anchor into the ring (blocked)", "STATE": "OWNED_ONCE"},
        {"INTERFACE": "RING -> FRAMING BEAMS", "SIDE_A": "S8.3 ring: annulus inside the bay",
         "SIDE_B": "straight framing bands (S6 occurrences)", "CONCRETE": "plan partition at the bay faces: each point "
         "of the annulus is inside the bay (ring) or inside a framing band (beam); 04 reconciles both readings exactly",
         "BARS": "different families; no bar counted on both sides", "STATE": "OWNED_ONCE (no frozen beam concrete stage)"},
        {"INTERFACE": "RING SEGMENTS -> S6 ARCS", "SIDE_A": "8 drawn ring segments", "SIDE_B": "S6 BA001-BA008",
         "CONCRETE": "-", "BARS": "0 kg in S6 / S6.1 on all eight", "STATE": "TRANSFERRED (05)"},
        {"INTERFACE": "DOME OPENING -> S7 SLAB", "SIDE_A": "dome-zone faces " + ", ".join(sorted(face_dome)),
         "SIDE_B": "S7", "CONCRETE": "no slab inside the dome circle", "BARS": f"S7 release items on those faces: "
         f"{len(s7_zone_items)}", "STATE": "NOT_DOUBLE_COUNTED"},
        {"INTERFACE": "S7 TOP-SUPPORT BARS AT THE DOME BAYS", "SIDE_A": "S7 slab top-support extensions at the beams "
         "framing each dome bay", "SIDE_B": "S8.3", "CONCRETE": "-",
         "BARS": f"{s7_total:.6f} kg in S7 ({', '.join(f'{k} {v:.6f}' for k, v in sorted(s7_by_dome.items()))}); role "
                 "SLAB_TOP_SUPPORT of the adjacent panels; continuity END_UNRESOLVED in S7A",
         "STATE": "STAYS_WITH_S7: neither added to nor subtracted from S8.3"},
        {"INTERFACE": "TOWER DOME -> S7 SLAB", "SIDE_A": "architectural tower dome", "SIDE_B": f"S7 {arch['tower_panel']}",
         "CONCRETE": "flat slab unchanged", "BARS": f"S7 release items there: {len(tower_items)}",
         "STATE": "UNCHANGED (CF-S8.3-01)"},
        {"INTERFACE": "RING -> COLUMNS", "SIDE_A": "S8.3 ring", "SIDE_B": "columns at the ring (04)", "CONCRETE":
         "column outlines stay with the column stage", "BARS": "-", "STATE": "OWNED_ONCE"}]

    # ------------------------------------------------------------ 12 sensitivity
    sens = []

    def S(i, what, value, unit, basis):
        sens.append({"CASE_ID": i, "CASE": what, "VALUE": value, "UNIT": unit, "BASIS": basis, "LANE": SENS,
                     "IN_OFFICIAL_TOTAL": False})
    for t, d in domes.items():
        for reading in ("PLAN", "DETAIL"):
            p = d[f"part_{reading}"]
            for depth in (0.50, 1.30):
                S(f"SA-{t}-RING-{reading}-{int(depth * 100)}", f"{t} ring concrete, {reading.lower()} position, depth "
                  f"{depth:.2f} m", p["in_bay_mm2"] / 1e6 * depth, "m3", f"plan area inside the bay x depth "
                  f"({'B4 row' if depth == 0.5 else 'architectural drum'})")
            tot = G.concentric_circle_total(p["r_centreline"] / 1000.0, [0.0, 0.0, 0.0])["total"]
            S(f"SA-{t}-RINGBARS-{reading}", f"{t} ring top 3T16 + bottom 3T18 as closed circles ({reading.lower()} "
              "position)", tot * (UM.kg_per_m(16, UNIT_MASS) + UM.kg_per_m(18, UNIT_MASS)), "kg",
              "3 x 2 pi r_c each (symmetric bars: cover cancels); no laps")
    for h in (1.85, 1.93):
        alt = G.shell_between_caps(G.cap_radius(shell["chord_m"], h), h, shell["t_m"])
        S(f"SA-SHELL-RISE-{int(h * 100)}", f"one shell with rise {h:.2f} m", alt["volume"], "m3", "section B-B / SE readings")
    alt = G.shell_between_caps(G.cap_radius(2 * domes["DOME-A"]["r_out"] / 1000, shell["rise_m"]), shell["rise_m"], shell["t_m"])
    S("SA-SHELL-CHORD-4822", "one shell if the chord were the plan ring's outer diameter", alt["volume"], "m3", "CF-S8.3-02")
    for surf in ("area_in", "area_out"):
        S(f"SA-MESH-{surf.upper()}", f"one shell mesh, both directions, on the {surf[5:]}rados surface",
          2 * G.length_at_spacing(shell[surf], 0.150) * um12, "kg", "instead of the mid-surface")
    S("SA-MESH-TWO", "one shell with two meshes (S1's 'two layers'): kg for that one shell", 4 * body * um12, "kg",
      "CF-S8.3-07; the released single mesh is half of it")
    tw_c, tw_h = float(se["dims"]["TOWER_CHORD"]["text"]) / 100.0, float(se["dims"]["TOWER_RISE"]["text"]) / 100.0
    tw = G.shell_between_caps(G.cap_radius(tw_c, tw_h), tw_h, 0.10)
    S("SA-TOWER-SHELL", "tower dome if it were an RC shell like the terrace domes (t 0.10 assumed)", tw["volume"], "m3",
      "printed architectural chord 4.41 and rise 2.15; the terrace thickness assumed")

    # ------------------------------------------------------------ 13 conservation
    cons = []

    def A(i, what, ok, detail_):
        cons.append({"CHECK_ID": i, "CHECK": what, "RESULT": "PASS" if ok else "FAIL", "DETAIL": detail_})
    A("A-01", "every frozen stage verifies and none is written", len(frozen) == len(MANIFESTS),
      f"{len(frozen)} manifests")
    phys = [r for r in pop if r["COUNTED_AS_PHYSICAL"]]
    A("A-02", "two structural domes and one architectural-only dome; every repeat maps to one of them and is not "
      "counted", len(phys) == 3 and sum(r["STRUCTURAL"] for r in phys) == 2 and all(
          r["PHYSICAL_ID"] for r in pop if r["ROW_KIND"] == "REPEATED_OUTLINE") and len(repeats) == 2,
      f"{Counter(r['ROW_KIND'] for r in pop)}")
    segs = [r for r in ring_rows if r["KIND"] == "DRAWN_BAND_SEGMENT"]
    ids = sorted(b["band_id"] for d in domes.values() for b in d["bands"])
    A("A-03", "eight drawn ring segments = the eight S6 arcs BA001-BA008, one each; S1's lengths agree with the exact ones",
      ids == [f"BA00{i}" for i in range(1, 9)] and len({r["S6_OCCURRENCE"] for r in segs}) == 8
      and all(abs(r["CENTRELINE_ARC_M"] - r["S1_LENGTH_M"]) < 2e-4 for r in segs),
      json.dumps({r["ROW_ID"]: [_r(r["CENTRELINE_ARC_M"], 4), r["S1_LENGTH_M"]] for r in segs}))

    def ends_on_faces(d):
        """every end of a drawn segment is where the outer or inner edge meets a framing face"""
        faces = [("x", f["face"]) if k.endswith("x") else ("y", f["face"]) for k, f in d["faces"].items()]
        out = []
        for b in d["bands"]:
            for ang in (b["start"], b["start"] + b["sweep"]):
                pts = [(r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang))) for r in (d["r_in"], d["r_out"])]
                out.append(min(abs((p[0] if ax == "x" else p[1]) - v) for p in pts for ax, v in faces))
        return out
    gaps = {t: ends_on_faces(d) for t, d in domes.items()}
    A("A-04", "per dome the segments do not overlap, every segment end lies on a framing face (each gap is a junction), "
      "and a repeated outline is covered once",
      all(abs(sum(b["sweep"] for b in d["bands"]) - G.coverage_deg([(b["start"], b["sweep"]) for b in d["bands"]])) < 1e-9
          for d in domes.values()) and all(max(g) < 1.0 for g in gaps.values())
      and all(abs(G.coverage_deg([(a["start"], a["sweep"]) for a in d["outer"] * 2]) -
                  G.coverage_deg([(a["start"], a["sweep"]) for a in d["outer"]])) < 1e-9 for d in domes.values()),
      json.dumps({t: _r(max(g), 6) for t, g in gaps.items()}))
    A("A-05", "each ring annulus is partitioned once: inside the bay (ring) + inside the framing (beam) = annulus",
      all(abs(d[f"part_{k}"]["in_bay_mm2"] + d[f"part_{k}"]["outside_bay_mm2"] - d[f"part_{k}"]["annulus_mm2"]) < 1e-6
          and d[f"part_{k}"]["outside_bay_mm2"] >= -1e-6 for d in domes.values() for k in ("PLAN", "DETAIL")), "")
    dc = DR.conservation(0.0, delta, 0.0)
    A("A-06", "the S6 -> S8.3 transfer moves no quantity", dc["all_pass"] and len(delta) == 8
      and all(r["NEW_RELEASE_STATE"] == DR.TRANSFERRED_OUT for r in delta), json.dumps(dc["checks"]))
    A("A-07", "S7's dome-adjacent top-support steel reconciles by role and stays in S7; no S7 item on a dome-zone face",
      abs(s7_total - sum(s7_by_dome.values())) < 1e-9 and not s7_zone_items and len(s7a) > 0,
      f"{s7_total:.6f} kg over {len(s7a)} strip ends")
    num = _numeric_shell(shell["r_out"], shell["h_out"], shell["t_m"])
    A("A-08", "the closed-form shell volume equals a numerical solid of revolution",
      abs(num - shell["volume"]) / shell["volume"] < 1e-6, f"{shell['volume']:.9f} vs {num:.9f}")
    A("A-09", "the shell profile is established: circular, centred on the axis, concentric surfaces; the architecture "
      "draws circular profiles too", det["profile"]["state"] == "SPHERICAL_ABOUT_AXIS" and det["shell_meets_ring_outer_faces"]
      and se["terrace"]["state"] == nw["terrace"]["state"] == "CIRCULAR", json.dumps(det["profile"], default=str))
    A("A-10", "only released lanes carry a quantity; every blocked or conflicting row carries none",
      all((r["LANE"] in RELEASED_LANES) == (r.get("M3", r.get("KG")) is not None) or r["LANE"] == "NOT_APPLICABLE"
          for r in conc + bars), "")
    fams = Counter(n["FAMILY"] for n in notes if n["ROLE"] not in ("GRAPHIC_ONLY",))
    A("A-11", "every bar notation on the detail is parsed and bound to exactly one family; repeats on the second cut "
      "collapse into the first", len(det["shell_labels"]) == 2 and len(det["ring_labels"]) == 4
      and all(len(x["handles"]) == 2 for x in det["ring_labels"]), json.dumps(fams))
    A("A-12", "sensitivity never enters a total", all(r["LANE"] == SENS and r["IN_OFFICIAL_TOTAL"] is False for r in sens),
      f"{len(sens)} cases")
    pkg = [p.name for p in HERE.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".pdf", ".dxf", ".dwg")]
    A("A-13", "no client drawing, scan or crop in the package", not pkg, f"{pkg}")
    A("A-14", "the tower dome is neither counted as structural nor quantified, and S7's slab there is unchanged",
      all(r["M3"] is None for r in conc if r["DOME"] == "DOME-TOWER") and len(tower_items) > 0
      and arch["tower_panel"] and arch["translation_error_mm"] < 1.0, f"{arch['tower_panel']}")
    check(all(c["RESULT"] == "PASS" for c in cons), "; ".join(f"{c['CHECK_ID']} {c['DETAIL']}" for c in cons
                                                             if c["RESULT"] != "PASS"))

    # ------------------------------------------------------------ write
    for o in OUTPUTS + [MANIFEST_NAME]:
        if (HERE / o).exists():
            (HERE / o).unlink()
    srcreg = source_register(frozen)
    _csv(OUTPUTS[1], srcreg)
    _csv(OUTPUTS[2], pop)
    _csv(OUTPUTS[3], prof)
    ring_fields = ["ROW_ID", "DOME", "KIND", "S6_OCCURRENCE", "S6_TAG", "START_DEG", "SWEEP_DEG", "CROSSES_ZERO",
                   "R1_MM", "R2_MM", "CENTRELINE_ARC_M", "CENTRELINE_CHORD_M", "PLAN_AREA_M2", "S1_LENGTH_M", "NOTE"]
    _csv(OUTPUTS[4], [{k: (_r(v, 9) if isinstance(v, float) else v) for k, v in r.items()} for r in ring_rows], ring_fields)
    _csv(OUTPUTS[5], delta)
    _csv(OUTPUTS[6], [{k: (_r(v, 9) if isinstance(v, float) else v) for k, v in r.items()} for r in conc])
    note_fields = ["NOTATION_ID", "HANDLES", "RAW", "DIAMETER_MM", "COUNT", "SPACING_MM", "RATE_PER_M", "ROLE",
                   "DIRECTION", "LAYERS_DRAWN", "FAMILY", "BOUND_BY", "NOTE"]
    _csv(OUTPUTS[7], notes, note_fields)
    _csv(OUTPUTS[8], [{k: (_r(v, 9) if isinstance(v, float) else v) for k, v in r.items()} for r in bars])
    _csv(OUTPUTS[9], blocked)
    _csv(OUTPUTS[10], cq)
    _csv(OUTPUTS[11], inter)
    _csv(OUTPUTS[12], [{k: (_r(v, 9) if isinstance(v, float) else v) for k, v in r.items()} for r in sens])
    _csv(OUTPUTS[13], cons)
    prov = [{"record": r["ROW_ID"], "output": OUTPUTS[2], "handles": r["HANDLES"], "source": r["SOURCE"]} for r in pop]
    prov += [{"record": r["ROW_ID"], "output": OUTPUTS[4], "drawing_sha256": STRUCT_SHA, "sheet": SHEET_PLAN} for r in ring_rows]
    prov += [{"record": r["DELTA_ID"], "output": OUTPUTS[5], "baseline": r["FROZEN_BASELINE"],
              "component": r["BASELINE_COMPONENT_ID"]} for r in delta]
    prov += [{"record": n["NOTATION_ID"], "output": OUTPUTS[7], "handles": n["HANDLES"], "drawing_sha256": STRUCT_SHA,
              "sheet": SHEET_DET} for n in notes]
    prov += [{"record": v["ID"], "output": OUTPUTS[2], "set": SET_KEY, "set_sheet": v["SET_SHEET"], "part": v["PART"],
              "page": v["PAGE"], "box_upright_px": v["BOX_UPRIGHT_PX"],
              "drawing_sha256": SET_PARTS.get(v["PART"], sorted(SET_PARTS.values()))} for v in VISUAL]
    (HERE / OUTPUTS[14]).write_text("".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in prov),
                                    encoding="utf-8")
    released_m3 = sum(r["M3"] for r in conc if r["RELEASED"])
    released_kg = sum(r["KG"] for r in bars if r["RELEASED"])
    summary = {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "physical_domes": {"structural": sorted(domes), "architectural_only": ["DOME-TOWER"]},
        "physical_ring_beams": {t: {"closed": True, "drawn_segments": [b["band_id"] for b in d["bands"]],
                                    "plan_reading_r_mm": [_r(d["r_in"], 3), _r(d["r_out"], 3)],
                                    "detail_reading_r_mm": [_r(d["r_in"] - 200, 3), _r(d["r_in"], 3)]}
                                for t, d in domes.items()},
        "shell": {k: _r(shell[k], 9) for k in ("chord_m", "rise_m", "t_m", "r_out", "r_in", "volume", "area_mid",
                                                "centre_below_springing", "springing_width")},
        "released": {"concrete_m3": _r(released_m3, 9), "reinforcement_kg": _r(released_kg, 9),
                     "concrete_items": [r["ITEM_ID"] for r in conc if r["RELEASED"]],
                     "reinforcement_items": [r["ITEM_ID"] for r in bars if r["RELEASED"]],
                     "lane": PROJECT_BASIS_QTO},
        "by_dome": {t: {"concrete_m3": _r(sum(r["M3"] for r in conc if r["RELEASED"] and r["DOME"] == t), 9),
                        "reinforcement_kg": _r(sum(r["KG"] for r in bars if r["RELEASED"] and r["DOME"] == t), 9)}
                    for t in domes},
        "lanes": {"concrete": dict(sorted(Counter(r["LANE"] for r in conc).items())),
                  "reinforcement": dict(sorted(Counter(r["LANE"] for r in bars).items()))},
        "ownership_transfers": [r["BASELINE_COMPONENT_ID"] for r in delta],
        "s7_dome_adjacent_kg": {"total": _r(s7_total, 6), **{k: _r(v, 6) for k, v in sorted(s7_by_dome.items())},
                                "state": "STAYS_WITH_S7"},
        "conflicts": [r["ID"] for r in cq if r["KIND"] == "SOURCE_CONFLICT"],
        "questions": [r["ID"] for r in cq if r["KIND"] == "QUESTION"],
        "conservation": {c["CHECK_ID"]: c["RESULT"] for c in cons},
        "frozen_baselines": {k: v["manifest_sha256"] for k, v in frozen.items()},
        "unit_mass": UM.describe(UNIT_MASS), "references_read": []}
    _json(OUTPUTS[15], summary)
    (HERE / OUTPUTS[0]).write_text(readme(summary, prof, cq, conc, bars), encoding="utf-8")
    manifest = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "FROZEN_BEFORE_COMPARISON",
                "engine_commit_stamp": summary["engine_commit"], "references_read": [],
                "code": {c: _sha(ROOT / c) for c in CODE},
                "inputs": {str(p.relative_to(ROOT)): _sha(p) for p in READ.values()},
                "drawing_sha256": {"ST7757.dxf": STRUCT_SHA, "P7757.dxf": ARCH_SHA, **SET_PARTS},
                "frozen_baselines": summary["frozen_baselines"], "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
                "released": summary["released"],
                "rule": "frozen before any earlier Urban, contractor or third-party figure is read; the comparison "
                        "after it explains differences and never changes a frozen quantity"}
    _json(MANIFEST_NAME, manifest)
    return summary


def readme(s, prof, cq, conc, bars):
    r = s["released"]
    sh = s["shell"]
    L = ["# S8.3: dome and ring-beam structural QTO", "",
         f"Baseline `{s['baseline']}`. Frozen before any comparison: `{MANIFEST_NAME}`, `references_read: []`.", "",
         "## Population", "",
         "- **Two physical domes** are structural: DOME-A and DOME-B on the first-floor roof (terrace, +9.70).",
         "  - Each has one closed ring beam, drawn as four segments between the framing beams.",
         "  - The upper roof sheet and the architectural plan repeat their outlines; repeats are not counted again.",
         "- **The tower dome** is architectural only (conflict CF-S8.3-01). It is not quantified.", "",
         "## Released (PROJECT_BASIS_QTO)", "",
         f"- Concrete: **{r['concrete_m3']:.6f} m3**, the two shells. Each shell is {sh['volume']:.6f} m3: the solid "
         f"between concentric spheres above the springing plane (chord {sh['chord_m']:.2f} m, rise {sh['rise_m']:.2f} m, "
         f"thickness {sh['t_m']:.2f} m; outer radius {sh['r_out']:.6f} m).",
         f"- Reinforcement: **{r['reinforcement_kg']:.6f} kg**, the shell mesh Ø12 at 150 mm, meridional and hoop, at a "
         f"rate density over the mid-surface ({sh['area_mid']:.6f} m2 per shell).",
         "  - Unrounded, with no laps, hooks, anchorage or second mesh.",
         "  - The fabrication count stays unresolved.", "",
         "## Not released", ""]
    for x in conc + bars:
        if x["LANE"] not in RELEASED_LANES and x["LANE"] != "NOT_APPLICABLE":
            L.append(f"- {x['DOME']} {x.get('COMPONENT') or x.get('FAMILY')}: {x['LANE']}. {x['STILL_MISSING']}")
    L += ["", "## Conflicts and questions", ""] + [f"- **{c['ID']}** ({c['STATUS']}): {c['NOTE']}" for c in cq]
    L += ["", "## Profile and levels", "", "| item | value | state |", "|---|---|---|"]
    L += [f"| {p['ITEM']} | {_cell(p['VALUE'] if not isinstance(p['VALUE'], float) else round(p['VALUE'], 4))} "
          f"{p['UNIT']} | {p['STATE']} |" for p in prof]
    L += ["", "## Exposure before the freeze", "",
          "During source discovery, the frozen PRE-S8 census rows for the domes were printed in the session.",
          "- One of their columns carries earlier commercial dome figures from an old Urban register.",
          "- The builder does not read that file.",
          "- No reading, convention or quantity here was chosen with reference to those figures.",
          "- One sensitivity case (the tower dome with the terrace thickness, SA-TOWER-SHELL) lands close to one of "
          "them. It stays sensitivity only, and its 0.10 m comes from the terrace detail.",
          "- The post-freeze comparison reports them.", "",
          "## Outputs", ""] + [f"- `{o}`" for o in OUTPUTS] + [f"- `{MANIFEST_NAME}`"]
    return "\n".join(L) + "\n"


def main():
    try:
        s = build()
    except Stop as e:
        raise SystemExit(f"STOP: {e}")
    print(json.dumps({k: s[k] for k in ("physical_domes", "released", "by_dome", "lanes", "conservation")},
                     indent=1, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
