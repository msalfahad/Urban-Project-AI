"""M5 sources: the inventory (sha256 per file) and the loaders of every quantity source the reconciliation reads.

Phase: RECONCILIATION (engine/benchmark_protection). The engine is frozen at the M4 commit before any external figure
is opened here. External figures (the freelancer lineage, the U-C4N and christiannp records) are read from their own
records at build time. None is a constant in this code, and none is passed to the engine.

Stage folders are found by their suffix (research/*_structural_s9a ...), so no project name is written in this file;
printed paths replace the project prefix with {P}.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[1]
sys.path.insert(0, str(ROOT))

INPUTS = ROOT / "data" / "inputs" / "by_sha256"
DXF_ST = INPUTS / "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
DXF_ARCH = INPUTS / "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
PDF_ST = INPUTS / "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3.pdf"
M4 = ROOT / "research" / "urban_engine_m4_correctness"
M4_PROFILE = M4 / "profile_st7757_m4.json"
M4_READINGS = M4 / "evidence" / "OCR_INDEPENDENT_READINGS.json"
M3_EVIDENCE = ROOT / "research" / "urban_engine_m3_recovery" / "evidence" / "DETAIL_EVIDENCE.json"
M4_FREEZE_COMMIT = "35c0587"
CHRIS = ROOT / "research" / "christiannp_blind_process"
R91 = ROOT / "research" / "R9_1_CHRIS_POST_FREEZE"
BRIEF = PKG / "evidence" / "M5_BRIEF_STATED_VALUES.json"


def stage(suffix):
    """The one research folder whose name ends with `_<suffix>`."""
    hits = sorted(p for p in (ROOT / "research").glob(f"*_{suffix}") if p.is_dir())
    if len(hits) != 1:
        raise FileNotFoundError(f"research/*_{suffix}: {len(hits)} matches")
    return hits[0]


def prefix():
    return stage("structural_s9a").name[: -len("_structural_s9a")]


def show(path):
    """A printable path: repository-relative, the project prefix written {P}."""
    p = Path(path)
    try:
        s = str(p.resolve().relative_to(ROOT))
    except ValueError:
        s = p.name
    return re.sub(re.escape(prefix()), "{P}", s, flags=re.IGNORECASE)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_json_str(s):
    return json.loads(s) if s else []


def num(x):
    try:
        if x in (None, ""):
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ inventory
def inventory():
    """Every file the reconciliation reads, hashed; recorded hashes checked where the source keeps one."""
    s31 = stage("multi_engine_comparison")
    idx = read_json(s31 / "INDEX.json")
    rows = []

    def add(sid, role, path, expected=None, expected_from=None, note=""):
        p = Path(path)
        if not p.exists():
            rows.append({"SOURCE_ID": sid, "ROLE": role, "PATH": show(p), "SHA256": "", "BYTES": "",
                         "STATE": "MISSING", "EXPECTED_SHA_RECORD": expected_from or "", "NOTE": note})
            return
        h = sha256(p)
        state = "PRESENT" if expected is None else ("HASH_MATCH" if h == expected else "HASH_MISMATCH")
        rows.append({"SOURCE_ID": sid, "ROLE": role, "PATH": show(p), "SHA256": h, "BYTES": p.stat().st_size,
                     "STATE": state, "EXPECTED_SHA_RECORD": expected_from or "", "NOTE": note})

    add("DRW-ST-DXF", "DRAWING (structural ST7757, CAD)", DXF_ST, DXF_ST.stem, "file name (content address)")
    add("DRW-ARCH-DXF", "DRAWING (architectural P7757, CAD)", DXF_ARCH, DXF_ARCH.stem, "file name (content address)")
    add("DRW-ST-PDF", "DRAWING (structural ST7757, plotted, 16 pages)", PDF_ST, PDF_ST.stem,
        "file name (content address)")
    for p in sorted(INPUTS.glob("*.pdf")):
        if p != PDF_ST:
            add("DRW-ARCH-PDF-" + p.stem[:8], "DRAWING (architectural P7757 plotted part)", p, p.stem,
                "file name (content address)")
    for name in ("FREELANCER_CATEGORY_LINEAGE.json", "MULTI_ENGINE_CONCRETE_COMPARISON.json",
                 "FREELANCER_STRUCTURAL_SCOPE_MAP.json", "SOURCE_ORACLE_COMPARISON_REGISTER.json"):
        add("S31-" + name.split(".")[0], "COMPARISON RECORD (S3.1, post-freeze)", s31 / name,
            idx["outputs"].get(name), "S3.1 INDEX.json outputs")
    add("FL-WORKBOOK-ORIGINAL", "FREELANCER BOQ (original workbook)",
        Path("uploads") / "<session>" / "<freelancer workbook upload>", None,
        "S3.1 INDEX.json key freelancer_workbook_sha256; upload path in the S3.1 builder constant FREELANCER_WB",
        "MISSING in this environment (not in the upload folder or the repository). The S3.1 lineage, which traced "
        "every leaf row from the workbook formulas and is pinned to the workbook hash, is used instead and cited as "
        "DERIVED. Not recreated from memory.")
    add("CHR-EVIDENCE", "MCP RECORD (christiannp, report-explicit values)", CHRIS / "process_log/EVIDENCE_INVENTORY.json")
    add("CHR-HANDOFF", "MCP RECORD (christiannp forensic handoff)", CHRIS / "CHRISTIANNP_BLIND_PROCESS_HANDOFF.md")
    add("CHR-REPORT", "MCP REPORT (christiannp sealed blind BOQ)", CHRIS / "process_log" / f"CHRISTIANNP_{prefix().upper()}_BLIND_FULL_BOQ.md", None, "",
        "MISSING (the handoff records it as never received). Item tables (footing occurrences, stair breakdown, "
        "raster class areas) are AWAITING_REPORT_FILE; only report-explicit totals are used.")
    add("UC4N-REPORT", "MCP REPORT (U-C4N blind AutoCAD MCP run, item level)",
        ROOT / "research/external_engine_lab/UC4N_BLIND_BOQ_REPORT.md", None, "",
        "MISSING: no U-C4N item-level file exists in the repository or the uploads; only the category values "
        "recorded from the owner brief (S3.1 section 16) in MULTI_ENGINE_CONCRETE_COMPARISON.json are held.")
    add("R91-QTY", "MCP CROSSWALK (R9.1 christiannp post-freeze)", R91 / "15_QUANTITY_RECONCILIATION_UPDATED.csv",
        read_json(R91 / "INDEX.json")["files"].get("15_QUANTITY_RECONCILIATION_UPDATED.csv"), "R9.1 INDEX.json")
    add("R91-GB", "MCP CROSSWALK (R9.1 ground beams)", R91 / "03_GB_OBJECT_CROSSWALK.csv",
        read_json(R91 / "INDEX.json")["files"].get("03_GB_OBJECT_CROSSWALK.csv"), "R9.1 INDEX.json")
    for name in ("SUMMARY.json", "PROVISIONAL_REGISTER.csv", "UNRESOLVED_REGISTER.csv", "SLAB_FACES.csv",
                 "UNRESOLVED_CONCRETE_EXCEPTIONS.csv"):
        add("M4-" + name.split(".")[0], "URBAN M4 register (frozen engine " + M4_FREEZE_COMMIT + ")",
            M4 / "st7757_route_g" / name)
    add("M4-PROFILE", "URBAN M4 project profile (printed values)", M4_PROFILE)
    add("M4-OCR-READINGS", "URBAN M4 second OCR reading", M4_READINGS)
    add("M3-EVIDENCE", "URBAN M3 detail evidence (frozen)", M3_EVIDENCE)
    m1 = stage("m1_usable_boq") / "boq"
    for name in ("PROVISIONAL_REGISTER.csv", "VERIFIED_REGISTER.csv", "UNRESOLVED_REGISTER.csv", "SUMMARY.json"):
        add("M1-" + name.split(".")[0], "URBAN M1 register (frozen stages S1 - S9A)", m1 / name)
    for suf, files in (("structural_s9", ("02_CONCRETE_BOQ_RECONCILIATION.csv", "16_S9_FREEZE_MANIFEST.json")),
                       ("structural_s9a", ("03_BAND_CORRECTION_REGISTER.csv", "05_BEAM_CONVENTION_COMPARISON.csv",
                                           "08_GROUND_BEAM_AUDIT.csv", "18_S9A_CORRECTION_MANIFEST.json")),
                       ("ground_slab_s8_1a", ("01_RECOVERED_LIFT_PIT_REGION.csv", "04_TT1_INTERPRETATION_REGISTER.csv")),
                       ("swimming_pool_s8_2", ("02_POOL_POPULATION_AND_OWNERSHIP.csv",)),
                       ("dome_ring_s8_3", ("06_CONCRETE_REGISTER.csv",)),
                       ("stairs_s8_7", ("06_PLAN_AND_INCLINED_GEOMETRY.csv",)),
                       ("stairs_s8_7c", ("11_RELEASE_SUMMARY.json",)),
                       ("lift_s8_8", ("03_REPRESENTATION_CROSSWALK.csv", "06_WALL_GEOMETRY_AND_CONCRETE_QTO.csv")),
                       ("structural_census_s1", (prefix().upper() + "_STRUCTURAL_CENSUS_S1.md",))):
        d = stage(suf)
        for f in files:
            sid = re.sub(re.escape(prefix()) + "_?", "", f.split(".")[0], flags=re.IGNORECASE)[:24]
            add(suf.upper() + "-" + sid, "URBAN S-stage record", d / f)
    add("M5-BRIEF", "OWNER BRIEF M5 (stated values, rate)", BRIEF)
    return rows


# ------------------------------------------------------------------ freelancer (derived lineage)
ROW_DESC = {   # English names of the leaf rows whose workbook label is not a mark (keyed by category and row)
    ("PLAIN_CONCRETE", 11): "plain concrete (one plate)",
    ("FOUNDATIONS_RELATED", 32): "perimeter tie beam",
    ("GROUND_BEAMS_AND_GROUND_SLAB", 11): "concrete ground floor (ground slab)",
    ("GROUND_BEAMS_AND_GROUND_SLAB", 13): "ground beams, longitudinal",
    ("GROUND_BEAMS_AND_GROUND_SLAB", 14): "ground beams, transverse",
    ("GROUND_BEAMS_AND_GROUND_SLAB", 15): "boundary-wall (fence) ground beam",
    ("WALLS_AND_COLUMNS", 11): "lift walls 20 cm (basement walls section)",
    ("SLABS", 11): "GF slab S.S 16 cm",
    ("SLABS", 16): "1F slab S.S 16 cm (deduction multiplied by 0)",
    ("SLABS", 23): "2F slab 16 cm",
    ("SLABS", 24): "2F slab 18 cm",
    ("STAIRS_AND_DOME", 20): "main stair: steps + waist slab",
    ("STAIRS_AND_DOME", 21): "main stair: landings",
    ("STAIRS_AND_DOME", 11): "entrance stair: slab + steps",
    ("STAIRS_AND_DOME", 12): "stair 2: slab + steps",
    ("STAIRS_AND_DOME", 13): "domes",
    ("SWIMMING_POOL", 11): "pool floor",
    ("SWIMMING_POOL", 12): "pool walls",
    ("SWIMMING_POOL", 13): "pump walls",
    ("SWIMMING_POOL", 14): "pool steps",
    ("SWIMMING_POOL", 15): "pump-room floor",
}
FL_FAMILY = {   # freelancer physical kind -> M5 canonical family
    "PLAIN_CONCRETE": "BLINDING", "FOOTING": "FOOTINGS", "STRAP_BEAM": "STRAPS",
    "PERIMETER_GROUND_BEAM": "GB_PERIMETER", "GROUND_BEAM": "GROUND_BEAMS", "BOUNDARY_GROUND_BEAM": "BOUNDARY_WALL",
    "GROUND_SLAB": "GROUND_SLAB", "COLUMN_NECK": "NECKS", "COLUMN_GF": "COLUMNS", "COLUMN_1F": "COLUMNS",
    "COLUMN_2F": "COLUMNS", "LIFT_WALL": "LIFT", "BEAM_GROSS_GF": "BEAMS", "BEAM_GROSS_1F": "BEAMS",
    "BEAM_GROSS_2F": "BEAMS", "SLAB_NET_GF": "SLABS", "SLAB_NET_1F": "SLABS", "SLAB_NET_2F": "SLABS",
    "STAIR": "STAIRS", "DOME": "DOMES", "POOL": "POOL", "POOL_PUMP_WALL": "POOL_PUMP_ROOM",
    "POOL_ROOM_FLOOR": "POOL_PUMP_ROOM",
}


def _floor(kind):
    for f in ("GF", "1F", "2F"):
        if kind.endswith("_" + f):
            return f
    return {"FOOTING": "FOUNDATION", "STRAP_BEAM": "FOUNDATION", "COLUMN_NECK": "FOUNDATION",
            "LIFT_WALL": "FOUNDATION", "PLAIN_CONCRETE": "FOUNDATION"}.get(kind, "GROUND")


def _mark(label):
    s = str(label or "").strip()
    if s and s.isascii() and len(s) <= 8 and " " not in s:
        m = s.replace(".", "").upper()
        if m.startswith(("BCB", "GCB")):
            m = m[1:]
        if m.startswith("STB"):
            m = "SB" + m[3:]
        return m
    return ""


def freelancer():
    """The freelancer BOQ as the S3.1 lineage traced it (DERIVED from the hash-pinned workbook)."""
    s31 = stage("multi_engine_comparison")
    idx = read_json(s31 / "INDEX.json")
    path = s31 / "FREELANCER_CATEGORY_LINEAGE.json"
    if sha256(path) != idx["outputs"]["FREELANCER_CATEGORY_LINEAGE.json"]:
        raise ValueError("freelancer lineage does not match its S3.1 INDEX hash")
    L = read_json(path)
    if L["workbook_sha256"] != idx["freelancer_workbook_sha256"]:
        raise ValueError("lineage is not pinned to the recorded workbook")
    cats, rows = {}, []
    sheets = {}
    for c in L["categories"]:
        cid = c["category_id"]
        cats[cid] = {"quantity": c["quantity"], "summary_value": c.get("summary_value"),
                     "by_kind": c.get("quantity_by_physical_kind") or {}, "notes": c.get("notes") or [],
                     "overlap": c.get("possible_overlap") or []}
        for s in c.get("subcomponents") or []:
            if s.get("row") is None:
                continue
            sh = sheets.setdefault(s.get("sheet"), f"WS{len(sheets) + 1:02d}")
            kind = s.get("physical_kind") or ""
            factors = [x for x in (s.get("B"), s.get("C"), s.get("D")) if isinstance(x, (int, float))]
            cnt = s.get("count") if isinstance(s.get("count"), (int, float)) else 1
            recomputed = cnt * math.prod(factors) if factors else 0.0
            rows.append({
                "FL_ID": f"FL-{sh}-R{s['row']:03d}", "CATEGORY": cid, "PHYSICAL_KIND": kind,
                "FAMILY": FL_FAMILY.get(kind, kind), "FLOOR": _floor(kind), "MARK": _mark(s.get("label")),
                "DESCRIPTION": ROW_DESC.get((cid, s["row"])) or _mark(s.get("label")) or kind,
                "COUNT": s.get("count") if isinstance(s.get("count"), (int, float)) else
                (1 if s.get("count") is None else "formula"),
                "B": s.get("B"), "C": s.get("C"), "D": s.get("D"), "VALUE_M3": float(s.get("value") or 0.0),
                "RECOMPUTED_M3": recomputed, "CELL": s.get("cell"), "WORKSHEET": sh, "ROW": s["row"]})
    total = cats.get("TOTAL_RC", {}).get("quantity")
    return {"categories": cats, "rows": rows, "total_rc": total, "lineage_notes": L.get("lineage_notes") or {},
            "worksheets": sheets, "lineage_sha256": sha256(path)}


# ------------------------------------------------------------------ MCP records
MCP_NAMES = {"UC4N": "U-C4N", "CHRISTIANNP": "christiannp"}


def mcp():
    """U-C4N and christiannp category values (S3.1 rows recorded from the owner brief) + christiannp explicit values."""
    s31 = stage("multi_engine_comparison")
    d = read_json(s31 / "MULTI_ENGINE_CONCRETE_COMPARISON.json")
    rows = []
    for r in d["rows"]:
        rows.append({"section": r["section"], "category": r["category"], "subcategory": r["subcategory"],
                     "basis": r["measurement_basis"], "FREELANCER": r.get("FREELANCER_QS"),
                     "UC4N": r.get("UC4N"), "CHRISTIANNP": r.get("CHRISTIANNP")})
    ev = read_json(CHRIS / "process_log/EVIDENCE_INVENTORY.json")["REPORT_EXPLICIT"]
    explicit = {k: v["value"] for k, v in ev["values"].items()}
    return {"rows": rows, "christiannp_explicit": explicit, "christiannp_assumptions": ev["assumptions"]}


def brief():
    return read_json(BRIEF)


# ------------------------------------------------------------------ Urban M4 (frozen engine) and M1 / S-stage registers
def m4_run(cache=None):
    """The M4 pipeline, exactly as the M4 package runs it (route G, V3 conventions, M4 profile)."""
    from tools import urban_boq_m2 as CLI
    return CLI.compute([str(DXF_ST)], profile=str(M4_PROFILE), route="G", cache_dir=cache,
                       evidence=str(M3_EVIDENCE), arch=[str(DXF_ARCH)], evidence_review=str(M4_READINGS))


def m1_items():
    d = stage("m1_usable_boq") / "boq"
    out = []
    for name, cat in (("VERIFIED_REGISTER.csv", "VERIFIED"), ("PROVISIONAL_REGISTER.csv", "PROVISIONAL"),
                      ("UNRESOLVED_REGISTER.csv", "UNRESOLVED")):
        for r in read_csv(d / name):
            if r["TRADE"] != "CONCRETE":
                continue
            r = dict(r)
            r["M1_CATEGORY"] = cat
            for k in ("LOW", "BASE", "HIGH", "EXPOSURE_LOW", "EXPOSURE_HIGH"):
                r[k] = num(r.get(k))
            out.append(r)
    return out


def m1_summary():
    return read_json(stage("m1_usable_boq") / "boq" / "SUMMARY.json")


def s9a_bands():
    return read_csv(stage("structural_s9a") / "03_BAND_CORRECTION_REGISTER.csv")


def s81a_regions():
    return read_csv(stage("ground_slab_s8_1a") / "01_RECOVERED_LIFT_PIT_REGION.csv")


def s87_elements():
    return read_csv(stage("stairs_s8_7") / "06_PLAN_AND_INCLINED_GEOMETRY.csv")


def s83_concrete():
    return read_csv(stage("dome_ring_s8_3") / "06_CONCRETE_REGISTER.csv")


def s82_population():
    return read_csv(stage("swimming_pool_s8_2") / "02_POOL_POPULATION_AND_OWNERSHIP.csv")


def s88_crosswalk():
    return read_csv(stage("lift_s8_8") / "03_REPRESENTATION_CROSSWALK.csv")


def s9a_gb_audit():
    return read_csv(stage("structural_s9a") / "08_GROUND_BEAM_AUDIT.csv")


def census_rules():
    """Printed-rule records of the S1 census that this reconciliation cites (id -> text)."""
    d = stage("structural_census_s1")
    md = next(d.glob("*_STRUCTURAL_CENSUS_S1.md"))
    out = {}
    for line in md.read_text(encoding="utf-8").splitlines():
        if line.startswith("| P") and line.count("|") >= 5:
            cells = [c.strip() for c in line.strip("|").split("|")]
            out[cells[0]] = {"page": cells[1], "class": cells[2], "text": cells[3]}
    return out


# ------------------------------------------------------------------ boundary wall drawn on the ground-beam plan
def boundary_runs(sheet_box):
    """Closed polylines of layer S-BOUN inside the ground-beam plan box: drawn boundary-wall strips.

    Read with ezdxf (a reader independent of the engine's intake). The centreline length of a strip is its area
    divided by its drawn thickness (the shortest edge)."""
    import ezdxf
    doc = ezdxf.readfile(str(DXF_ST))
    x0, y0, x1, y1 = sheet_box
    out = []
    for e in doc.modelspace():
        try:
            if e.dxf.layer.upper() != "S-BOUN" or e.dxftype() != "LWPOLYLINE" or not e.closed:
                continue
        except Exception:                                   # noqa: BLE001 - entities without a layer (RTEXT)
            continue
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        if not all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in pts):
            continue
        out.append(dict(strip_centreline(pts), handle=e.dxf.handle, points=pts))
    return sorted(out, key=lambda r: -r["centreline_m"])


def strip_centreline(pts):
    """A closed strip outline (constant drawn thickness): area, thickness (the shortest edge) and centreline length
    (area / thickness), in mm / mm2 / m."""
    area = abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                   for i in range(len(pts)))) / 2.0
    t = min(math.dist(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts)))
    return {"area_mm2": float(area), "thickness_mm": float(t), "centreline_m": float(area / t / 1000.0)}


def boundary_typical():
    """The printed boundary-wall typical (p.14) and the B.W schedule row, as recorded by PRE-S8 and the S1 census."""
    rows = read_csv(ROOT / "research" / "pre_s8_structural_completeness" / "10_S8_SOURCE_EXHAUSTION.csv")
    row = next(r for r in rows if r["S8_CANDIDATE"] == "BOUNDARY_WALL")
    t = row["CH_TYPICAL_DETAIL"]
    gb = re.search(r"GB (\d+)x(\d+)", t)
    pad = re.search(r"pads (\d+)x(\d+)x(\d+)", t)
    col = re.search(r"columns (\d+)x(\d+)", t)
    cen = census_rules().get("P14-BOUNDARY", {}).get("text", "")
    bw = re.search(r"B\.W (\d+)x(\d+)", cen)
    note_b = census_rules().get("P1-NOTE-B", {})
    cm = lambda m, k: float(m.group(k)) / 100.0 if m else None          # noqa: E731
    return {"gb_w": cm(gb, 1), "gb_h": cm(gb, 2), "pad": tuple(cm(pad, k) for k in (1, 2, 3)) if pad else None,
            "col": (cm(col, 1), cm(col, 2)) if col else None, "bw_w": cm(bw, 1), "bw_h": cm(bw, 2),
            "typical_text": t, "census_text": cen, "missing": row["MISSING"], "readiness": row["READINESS"],
            "note_b": note_b.get("text", ""), "note_b_class": note_b.get("class", "")}
