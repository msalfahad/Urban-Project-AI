"""ALSENAN CHALET / P7757 + ST7757 - FULL-VILLA DEVELOPMENT VALIDATION, PHASE A (SHADOW; frozen before any benchmark).

    python3 research/external_engine_lab/alsenan_phase_a.py <work_dir> <register_dir> [code_commit]

PROJECT ADAPTER: this module supplies FACTS ONLY - the delivered files (by sha256), and what is found in them by
explicit rules (sheet frames, titles, tags, schedule grids, level marks). Every measurement is made by the ONE Urban
engine (engine/source): TS01 topology, frame.assess, schedule_table, structural_qto, level_marks. There is no P7757
or ST7757 calculator here, no donor / MCP calculator, no Qortuba fact (3.15 / 3.20, openings, ducts, sills ...).

Firewall: the firewall census (path / role only) runs first and OUTSIDE the measurement build; the build itself runs
inside benchmark_firewall.OpenAudit and fails closed when it opens a denied file or loads a denied module. No P7757
historical register, project rule, supervised floor assignment, owner fact, manual BOQ, web-app report or price is
read. The uploads folder is read only for the three zips named by sha256 below.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import pickle
import shutil
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import ezdxf                                                                                     # noqa: E402
import pymupdf                                                                                   # noqa: E402

from engine.source import benchmark_firewall as FW, cad_text as CT, canonical_build as CB       # noqa: E402
from engine.source import canonical_input as CI, frame as FR, geometry_role as GR               # noqa: E402
from engine.source import level_marks as LM, role_authority as RA, room_topology as RT          # noqa: E402
from engine.source import schedule_table as ST, structural_qto as SQ, text_role as TX           # noqa: E402
from engine.source import topology_closures as TC, topology_digest as TD                         # noqa: E402
from engine.source.cad import kernel_ezdxf as K2R                                               # noqa: E402
import r8_6a_reconcile as RECON                                                                  # noqa: E402

PHASE = "ALSENAN_P7757_ST7757_PHASE_A"
UPLOADS = Path("/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240")
STORE = ROOT / "data/inputs/by_sha256"
ZIPS = {"58e923eb-Plans_Part1_CAD_Structural.zip": "f5d183340b2601bf1508127daa2e3ae6beab82b42a8f7527b269ccfe24284b00",
        "4eb9afb0-Plans_Part2_Architectural_PDF_01-06.zip": "d98a26f6b7bfaafee87c1d20f4142f6c6184c8449b4009bba1ce8ed50dd9a71c",
        "6e3da136-Plans_Part3_Architectural_PDF_07-12.zip": "4658c268ac5a8b40ec6f7cb8c7a911d4b45bf19c023a8ce3a54165fb7ea131bb"}
# the delivered files: name as delivered -> (sha256, discipline, declared role). Identity is the hash, never the name.
FILES = {
    "P7757.dwg": ("7f61f3acdd62d62dc745f8b522f8136cb41c575df36ec6d9f27c2fe48fea41e3", "ARCHITECTURAL", "CAD_NATIVE"),
    "P7757.dxf": ("ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4", "ARCHITECTURAL", "CAD_EXCHANGE"),
    "P7757_Architectural.dwf": ("7d440a57aa8930566a4028ff5e91ee819df1007fad3bd986d4db743f100d735f", "ARCHITECTURAL",
                                "DWF_PUBLISH"),
    "P7757_Architectural_Plan_Pages_01-06.pdf": ("80b6a80428990db4dfa86aa343ed2c7cb429709459d564f0dac92362480a9b00",
                                                 "ARCHITECTURAL", "PDF_PLOT"),
    "P7757_Architectural_Plan_Pages_07-12.pdf": ("281a0c3f8c1cdd8f2a78528513b66d14ba4793e981e2d8059423faf6e6162f99",
                                                 "ARCHITECTURAL", "PDF_PLOT"),
    "ST7757.dwg": ("3f7a556c69786834c16c355504437b5abcd1f5aa3a9625b33a2c5b14213f0227", "STRUCTURAL", "CAD_NATIVE"),
    "ST7757.dxf": ("9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079", "STRUCTURAL", "CAD_EXCHANGE"),
    "ST7757.pdf": ("74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3", "STRUCTURAL", "PDF_PLOT"),
    "sanitary-7757.pdf": ("116736870983e63a9bf80e778fe2fc098e333148cce5337190a1ac3398d82596", "SANITARY_SUPPORTING",
                          "PDF_PLOT"),
}
REV_ARCH, REV_STR = "ALSENAN_P7757_DXF", "ALSENAN_ST7757_DXF"
DWG_DECODE = ROOT / "data/runs/cad_convert/P7757_ARCHITECTURAL.json"     # pinned LibreDWG decode of P7757.dwg (SOURCE)
EPS = 1.0                                                                # native coincidence for drawn tables / tags

# ------------------------------------------------------------------ firewall rules (PATH / ROLE only)
TOKENS = ("p7757", "st7757", "7757", "alsenan", "al senan", "al_senan", "chalet")
FIREWALL_RULES = (
    FW.Rule("data/inputs/by_sha256/*", FW.SOURCE, "hash-addressed delivered sources"),
    FW.Rule("data/runs/cad_convert/*", FW.SOURCE_DERIVED, "pinned decoder output of a delivered DWG"),
    FW.Rule(str(UPLOADS / "58e923eb-*.zip"), FW.SOURCE, "delivered zip 1 (this brief)"),
    FW.Rule(str(UPLOADS / "4eb9afb0-*.zip"), FW.SOURCE, "delivered zip 2 (this brief)"),
    FW.Rule(str(UPLOADS / "6e3da136-*.zip"), FW.SOURCE, "delivered zip 3 (this brief)"),
    FW.Rule(str(UPLOADS / "*"), FW.UNRELATED_UPLOAD, "any other upload (spreadsheets, cost reports, earlier files)"),
    FW.Rule("*/alsenan_work/*/src/*", FW.SOURCE, "isolated workspace copies of the delivered files"),
    FW.Rule("*/alsenan_work/*", FW.SOURCE_DERIVED, "isolated workspace caches built from the delivered files"),
    FW.Rule("tests/data/p7757*", FW.BENCHMARK_GOLD, "historical P7757 expectations"),
    FW.Rule("*benchmark*", FW.BENCHMARK_GOLD, "benchmark material"),
    FW.Rule("*unseal*", FW.BENCHMARK_GOLD, "benchmark unseal material"),
    FW.Rule("*.xls", FW.MANUAL_BOQ, "spreadsheet"),
    FW.Rule("*.xlsx", FW.MANUAL_BOQ, "spreadsheet (outputs of this phase are written, never read)"),
    FW.Rule("tools/parse_cost_export.py", FW.COST_DATA, "cost-export tooling"),
    FW.Rule("tests/alsenan/registers/*", FW.SOURCE_DERIVED, "this phase's own registers"),
    FW.Rule("tests/*/registers/*", FW.HISTORICAL_PROJECT_RESULT, "historical round registers"),
    FW.Rule("tests/*FIXTURE_MANIFEST.json", FW.HISTORICAL_PROJECT_RESULT, "historical fixture manifests"),
    FW.Rule("research/qs_wall_treatment_01/*", FW.HISTORICAL_PROJECT_RESULT, "WT01 / DB01 / PA rounds"),
    FW.Rule("data/registry/*", FW.PROJECT_FACT, "owner / project facts of earlier rounds"),
    FW.Rule("data/trade_rules/*", FW.PROJECT_FACT, "rule library with historical project provenance"),
    FW.Rule("docs/*", FW.HISTORICAL_PROJECT_RESULT, "round documents"),
    FW.Rule("research/external_engine_lab/alsenan_*", FW.CODE, "this phase's lab code"),
    FW.Rule("research/*.json", FW.HISTORICAL_PROJECT_RESULT, "research outputs"),
    FW.Rule("engine/*", FW.CODE, "engine code"),
    FW.Rule("research/*", FW.CODE, "lab code"),
    FW.Rule("tools/*", FW.CODE, "tools"),
    FW.Rule("tests/*", FW.GENERIC_TEST, "tests"),
    FW.Rule("agents/*", FW.CODE, "agents"),
    FW.Rule("integrations/*", FW.CODE, "integrations"),
    FW.Rule("social/*", FW.CODE, "social"),
    FW.Rule("*.py", FW.CODE, "python"),
    FW.Rule("*.pyc", FW.CODE, "python bytecode"),
)
DENIED_MODULES = ("r8_9_p7757", "r8_10_p7757", "*p7757*", "*qs_wall_treatment*", "rc1_qortuba", "r8_1?_qortuba",
                  "r8_20*", "r8_19*", "parapet_assembly*", "engine.round*", "engine.supervised_benchmark",
                  "engine.freeze_manifest", "tools.parse_cost_export")


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def digest(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def firewall_census() -> dict:
    """Every tracked file whose PATH or CONTENT mentions a project token (git grep -l prints names only), classified
    by path. Runs before the audited build."""
    ls = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    by_path = {p for p in ls if any(t in p.lower() for t in TOKENS)}
    pat = "|".join(t.replace(" ", "[ _]") for t in TOKENS)
    gg = subprocess.run(["git", "grep", "-l", "-i", "-E", pat], cwd=ROOT, capture_output=True, text=True).stdout.split("\n")
    by_content = {p for p in gg if p}
    own = {p for p in by_path | by_content if "alsenan" in p.lower() and (p.startswith("research/external_engine_lab/")
                                                                          or p.startswith("tests/alsenan/"))}
    cen = FW.census(sorted((by_path | by_content) - own), FIREWALL_RULES, root=ROOT)
    up = sorted(p.name for p in UPLOADS.iterdir()) if UPLOADS.exists() else []
    upc = FW.census([str(UPLOADS / n) for n in up], FIREWALL_RULES)
    return {"tokens": list(TOKENS), "tracked_files_mentioning_tokens": cen["files"], "by_class": cen["by_class"],
            "unclassified": cen["unclassified"], "entries": cen["entries"],
            "this_phase_files_excluded": sorted(own),
            "uploads": {"files": len(up), "by_class": upc["by_class"],
                        "names_of_denied_uploads": [Path(e["path"]).name for e in upc["entries"]
                                                    if e["class"] in FW.DENIED]}}


# ------------------------------------------------------------------ intake
def intake(work: Path) -> dict:
    """Extract the three zips (verified by sha256) into an isolated workspace; never rename the originals; copy each
    file to the hash-addressed store. Returns {name: path}."""
    src = work / "src"
    src.mkdir(parents=True, exist_ok=True)
    zips = {}
    for z, want in ZIPS.items():
        zp = UPLOADS / z
        if zp.exists():
            got = sha(zp)
            if got != want:
                raise ValueError(f"zip {z}: sha256 {got} is not the delivered {want}")
            with zipfile.ZipFile(zp) as zf:
                zips[z] = {"sha256": got, "bytes": zp.stat().st_size,
                           "members": [{"name": i.filename, "bytes": i.file_size, "date_time": list(i.date_time)}
                                       for i in zf.infolist()]}
                for i in zf.infolist():
                    if not (src / i.filename).exists():
                        zf.extract(i, src)
        else:
            zips[z] = {"sha256": want, "bytes": None, "members": None, "note": "zip not present in this container; "
                                                                                 "files verified by sha256 instead"}
    paths = {}
    for name, (want, _, _) in FILES.items():
        p = src / name
        if not p.exists():
            cand = STORE / f"{want}{Path(name).suffix.lower()}"
            if cand.exists():
                shutil.copyfile(cand, p)
        if not p.exists():
            raise FileNotFoundError(f"{name} (sha256 {want}) is not available")
        got = sha(p)
        if got != want:
            raise ValueError(f"{name}: sha256 {got} is not the delivered {want}")
        STORE.mkdir(parents=True, exist_ok=True)
        dst = STORE / f"{want}{Path(name).suffix.lower()}"
        if not dst.exists():
            shutil.copyfile(p, dst)
        if sha(dst) != want:                         # verified on every run (also keeps the opened-file log stable)
            raise ValueError(f"store copy of {name} does not hash to {want}")
        paths[name] = p
    return {"paths": paths, "zips": zips}


def _bytes(p) -> bytes:
    with open(p, "rb") as f:                         # read through Python so the firewall audit sees the open
        return f.read()


def jd(v):
    """Julian date -> ISO timestamp (UTC, seconds)."""
    if not isinstance(v, (int, float)):
        return None
    import datetime as dt
    return (dt.datetime(1858, 11, 17) + dt.timedelta(days=float(v) - 2400000.5)).replace(microsecond=0).isoformat()


def raw_header(path, names=("$TDCREATE", "$TDUPDATE", "$TDINDWG", "$LASTSAVEDBY")) -> dict:
    """Header values exactly as stored in the DXF bytes (ezdxf rewrites $TDCREATE with the load time on reading)."""
    out = {}
    lines = _bytes(path).decode("cp1252", errors="replace").splitlines()
    end = next((i for i in range(len(lines) - 1) if lines[i].strip() == "0" and lines[i + 1].strip() == "ENDSEC"), 0)
    for i in range(0, end - 3):
        if lines[i].strip() == "9" and lines[i + 1].strip() in names:
            out[lines[i + 1].strip()] = lines[i + 3].strip()
    return out


def dxf_facts(path) -> dict:
    d = ezdxf.readfile(str(path))
    h = d.header
    raw = raw_header(path)
    msp = d.modelspace()
    c = Counter(e.dxftype() for e in msp)
    ext = (h.get("$EXTMIN"), h.get("$EXTMAX"))
    return {"cad_version": d.dxfversion, "release": d.acad_release, "maintenance": h.get("$ACADMAINTVER"),
            "insunits_declared": h.get("$INSUNITS"), "insunits_name": FR.INSUNITS.get(h.get("$INSUNITS"), ("?",))[0],
            "measurement": h.get("$MEASUREMENT"), "dimlfac": h.get("$DIMLFAC"), "dimscale": h.get("$DIMSCALE"),
            "ltscale": h.get("$LTSCALE"), "last_saved_by": raw.get("$LASTSAVEDBY"), "tdcreate": jd(float(raw["$TDCREATE"])) if "$TDCREATE" in raw else None,
            "tdupdate": jd(float(raw["$TDUPDATE"])) if "$TDUPDATE" in raw else None,
            "header_dates_basis": "raw DXF HEADER values (ezdxf restamps $TDCREATE on load)", "fingerprint_guid": h.get("$FINGERPRINTGUID"),
            "version_guid": h.get("$VERSIONGUID"), "codepage": h.get("$DWGCODEPAGE"),
            "extents": [[round(v, 3) for v in list(e)[:2]] for e in ext if e is not None],
            "layouts": [{"name": lay.name, "entities": len(lay)} for lay in d.layouts],
            "modelspace_entities": sum(c.values()), "entity_counts": dict(sorted(c.items())), "blocks": len(d.blocks),
            "layers": sorted(lay.dxf.name for lay in d.layers)}


def dwg_facts(path) -> dict:
    b = _bytes(path)
    v = b[:6].decode("ascii", "replace")
    names = {"AC1018": "R2004", "AC1021": "R2007", "AC1024": "R2010", "AC1027": "R2013", "AC1032": "R2018"}
    return {"cad_version": v, "release": names.get(v, "?"), "bytes": len(b),
            "content": "native DWG: readable only through a pinned decoder decode"}


def dwf_facts(path) -> dict:
    b = _bytes(path)
    return {"header": b[:12].decode("ascii", "replace"), "bytes": len(b), "reader": "NONE (W2D streams unread)"}


def pdf_facts(path) -> dict:
    doc = pymupdf.open(stream=_bytes(path), filetype="pdf")
    pages = []
    for p in doc:
        imgs = p.get_images()
        txt = p.get_text().strip()
        pages.append({"page": p.number + 1, "size_pt": [round(p.rect.width, 1), round(p.rect.height, 1)],
                      "size_mm": [round(p.rect.width / 72 * 25.4, 1), round(p.rect.height / 72 * 25.4, 1)],
                      "images": len(imgs), "image_px": [[im[2], im[3]] for im in imgs[:2]],
                      "vector_paths": len(p.get_drawings()), "text_chars": len(txt),
                      "text": " | ".join(x.strip() for x in txt.splitlines() if x.strip())[:200],
                      "lane": ("RASTER" if imgs and not p.get_drawings() else "VECTOR" if not imgs else "MIXED")})
    m = {k: v for k, v in (doc.metadata or {}).items() if v}
    return {"pages": len(pages), "metadata": m, "page_census": pages,
            "lanes": dict(Counter(p["lane"] for p in pages)), "text_layer": any(p["text_chars"] for p in pages)}


# visual identification of the raster / vector-stroke sheets: LOCALISATION ONLY (agent observation, never a quantity)
PDF_SHEETS = {
    "P7757_Architectural_Plan_Pages_01-06.pdf": [
        "AREA PLANS - GROUND FLOOR + 1st FLOOR (municipal area calculation)", "AREA PLAN - 2nd FLOOR + TOTAL FLOORS AREA",
        "GROUND FLOOR PLAN 1:100", "1st FLOOR PLAN 1:100", "2nd FLOOR PLAN 1:100", "SOUTH EAST ELEVATION 1:100"],
    "P7757_Architectural_Plan_Pages_07-12.pdf": [
        "SOUTH WEST ELEVATION 1:100", "NORTH WEST ELEVATION 1:100", "NORTH EAST ELEVATION 1:100", "SECTION 1:100",
        "SECTION 1:100", "FENCE ELEVATION + FENCE SECTION"],
    "ST7757.pdf": ["COLUMN & AXIS PLAN", "FOUNDATION PLAN", "GROUND BEAMS PLAN", "GROUND FLOOR ROOF SLAB",
                   "FIRST FLOOR ROOF SLAB", "SECOND FLOOR ROOF SLAB", "DETAIL OF SWIMMING POOL + DETAIL OF DOME",
                   "RECOMMENDATIONS (raster image)", "SCHEDULES (columns, footings)", "SCHEDULE OF SIMPLE BEAMS",
                   "SCHEDULE OF CONTINUOUS BEAMS (2 SPAN) x2", "SCHEDULE OF CONTINUOUS BEAMS (THREE SPAN)",
                   "TYPICAL DETAILS (footing, lintel, ground beams)", "TYPICAL DETAILS (parapet, lift pit, boundary wall)",
                   "TYPICAL DETAILS (twisted columns, slab on beams, planted column)", "TYPICAL DETAILS (stairs)"],
    "sanitary-7757.pdf": ["SANITARY SHEET 1", "SANITARY SHEET 2", "SANITARY SHEET 3"],
}
# PDF sheets that have a DXF counterpart (by the same visual identification; architectural DXF holds 5 sheets)
PDF_IN_DXF = {"P7757_Architectural_Plan_Pages_01-06.pdf": {3: "GF", 4: "1F", 5: "2F", 6: "SE_ELEVATION"},
              "P7757_Architectural_Plan_Pages_07-12.pdf": {2: "NW_ELEVATION"}}


# ------------------------------------------------------------------ canonical inputs
def k2(path, revision_id, cache: Path):
    """K2 canonical records + realised geometry (attributes) of one DXF, cached by the DXF sha256."""
    if cache.exists():
        blob = pickle.loads(_bytes(cache))
        if blob.get("dxf_sha256") == sha(path):
            return blob
    doc, findings = K2R.load(str(path))
    if doc is None:
        raise ValueError(f"K2 could not load {path}")
    rg = K2R.realise(doc)
    k = CB.K2(revision_id, doc, rg)
    blob = {"parts": k.parts(), "texts": k.texts(), "dims": k.dimensions(),
            "attributes": [(a.tag, a.value, tuple(a.insertion), a.owner_insert_handle) for a in rg.attributes],
            "unrealised": [{"code": f.code, "obs_id": f.obs_id, "layer": None,
                            "path": [p.split(":", 1)[1].split("[")[0] for p in f.instance_path]} for f in rg.findings],
            "findings": [(f.code, f.obs_id, tuple(f.instance_path), f.detail) for f in rg.findings],
            "inserts": {e.dxf.handle: {"name": e.dxf.name, "layer": e.dxf.layer, "x": e.dxf.insert.x, "y": e.dxf.insert.y}
                        for e in doc.modelspace().query("INSERT")},
            "header": {h: doc.header.get(h) for h in ("$INSUNITS", "$DIMLFAC")}, "dxf_sha256": sha(path)}
    cache.write_bytes(pickle.dumps(blob))
    return blob


def revision(rid, anchor):
    return CI.SourceRevision(rid, CI.DERIVED_PENDING_SOURCE, anchor, None, "PHASE_A_DEVELOPMENT_VALIDATION")


def in_box(x, y, b):
    return b[0] <= x <= b[2] and b[1] <= y <= b[3]


def frames(blob) -> list:
    """SHEET FRAMES by rule: closed axis-aligned rectangles drawn as ONE source entity (one handle, four segments, no
    insert path), of one size repeated at least twice, not overlapping each other."""
    by = defaultdict(list)
    for p in blob["parts"]:
        if p.kind == "SEGMENT" and not p.identity.instance_handles:
            by[p.identity.source_handle].append(p)
    cand = []
    for h, ps in by.items():
        if len(ps) != 4:
            continue
        r = SQ.rectangles([(p.identity.key,) + tuple(p.geometry) for p in ps], eps=EPS)
        if len(r) == 1:
            cand.append({"handle": h, "layer": ps[0].layer, "bounds": r[0]["bounds"],
                         "size": (round(r[0]["width"]), round(r[0]["height"]))})
    groups = []                     # one size within 0.05 % (plot-frame drafting noise), never by position
    for c in sorted(cand, key=lambda c: (-c["size"][0] * c["size"][1], c["handle"])):
        g = next((g for g in groups if all(abs(a - b) <= max(2 * EPS, 5e-4 * b) for a, b in zip(c["size"], g[0]["size"]))),
                 None)
        (g.append(c) if g is not None else groups.append([c]))
    rep = [g for g in groups if len(g) >= 2]
    if not rep:
        return []
    fr = max(rep, key=lambda g: g[0]["size"][0] * g[0]["size"][1])
    return sorted(fr, key=lambda c: (c["bounds"][1], c["bounds"][0]))


TITLE_WORDS = ("FLOOR PLAN", "ELEVATION", "SECTION", "PLAN", "SLAB", "SCHEDULE", "DETAIL")


def sheet_titles(blob, b) -> list:
    out = []
    for t in blob["texts"]:
        if t.x is None or not in_box(t.x, t.y, b) or not t.value:
            continue
        v = CT.plain(t.value)[0].strip()
        if any(w in v.upper() for w in TITLE_WORDS) and not CT.legacy_codepage_suspect(v):
            out.append({"text": v, "key": t.identity.key, "height": t.height})
    return sorted(out, key=lambda z: (-(z["height"] or 0), z["text"]))


def floor_of(titles) -> tuple:
    """(floor id, view kind) from the sheet's own title words; None when the title does not say."""
    u = " ".join(t["text"].upper() for t in titles)
    if "ELEVATION" in u:
        for d in ("NORTH WEST", "SOUTH EAST", "NORTH EAST", "SOUTH WEST"):
            if d in u:
                return d.replace(" ", "_") + "_ELEVATION", "ELEVATION"
        return "ELEVATION", "ELEVATION"
    if "GROUND FLOOR" in u and "ROOF" not in u:
        return "GF", "PLAN"
    if ("1ST" in u or "FIRST" in u) and "ROOF" not in u:
        return "1F", "PLAN"
    if ("2ND" in u or "SECOND" in u) and "ROOF" not in u:
        return "2F", "PLAN"
    return None, None


def assemble(blob, rev, b, region_id, unit_mm, unit_id):
    bb = (b[0] - EPS, b[1] - EPS, b[2] + EPS, b[3] + EPS)
    return CB.assemble(rev, region_id, bb, "MF:" + region_id, unit_mm, unit_id, blob["parts"], blob["texts"],
                       blob["dims"], notes={"insunits": blob["header"]["$INSUNITS"],
                                            "dimlfac": float(blob["header"]["$DIMLFAC"] or 1.0), "route": "K2",
                                            "findings": blob["findings"], "clip_bounds": list(bb)})


# ------------------------------------------------------------------ units
def unit_context(name, sha256, insunits, evidence, view_records):
    decl, finding = FR.declaration_evidence(insunits, "MODEL_SPACE", sha256, parser="EZDXF")
    ev = list(decl) + list(evidence)
    a = FR.assess(FR.NATIVE_UNIT, ev, sha256, scope="MODEL_SPACE")
    return {"source": name, "sha256": sha256, "status": a.status, "native_to_mm": a.value, "reason": a.reason,
            "classes": [list(c) for c in a.classes], "admitted": list(a.admitted),
            "excluded": [list(x) for x in a.excluded], "allowed_uses": list(FR.allowed_uses(a.status)),
            "evidence": [e.as_dict() for e in ev], "views": view_records}


# ------------------------------------------------------------------ architectural
ROOM_CLASSES = {"BATH": "WET_CANDIDATE", "W.C": "WET_CANDIDATE", "WASH": "WET_CANDIDATE", "KITCHEN": "WET_CANDIDATE",
                "LAUNDRY": "WET_CANDIDATE", "PANTRY": "SERVICE_CANDIDATE", "SWIMMING POOL": "EXTERNAL_WET_CANDIDATE",
                "COURT": "EXTERNAL_CANDIDATE", "GARDEN": "EXTERNAL_CANDIDATE", "ROOF": "ROOF_CANDIDATE",
                "VOID": "VOID_CANDIDATE"}


EXTRA_SPACE_WORDS = ("COURT", "GARDEN", "POOL", "SWIMMING", "DEWANEYA", "DIWANIA", "AREA", "R.")


def _english_space_name(v):
    """A value is an English space name when one of its tokens is generic room vocabulary (TX.ROOM_WORDS) or an
    external-space word; everything else in a label occurrence (legacy-codepage Arabic) stays UNDECODED."""
    toks = {t.strip(".,").replace(".", "") for t in v.upper().split()}
    return bool(toks & (set(TX.ROOM_WORDS) | {w.replace(".", "") for w in EXTRA_SPACE_WORDS}))


def label_register(inp, floor, troles):
    occ = defaultdict(list)
    for t in inp.texts:
        if t.visibility != CI.VISIBLE or t.x is None:
            continue
        o = (t.identity.instance_handles or ("E" + t.identity.source_handle,))[0]
        occ[o].append(t)
    rows = []
    for o, ts in sorted(occ.items()):
        vals = [CT.plain(t.value)[0].strip() for t in ts if t.value]
        en = [v for v in vals if v and _english_space_name(v)]
        roles = sorted({troles[t.identity.key].role for t in ts if t.identity.key in troles})
        if not en or not any(r.startswith("ROOM_LABEL") for r in roles):
            continue
        name = " / ".join(en)
        other = [v for v in vals if v not in en]
        cls = next((c for w, c in ROOM_CLASSES.items() if w in name.upper()), "DRY_OR_UNCLASSIFIED")
        rows.append({"floor": floor, "occurrence": o, "label_en": name,
                     "label_ar": "UNDECODED_LEGACY_CODEPAGE" if other else None, "text_roles": roles,
                     "x": round(ts[0].x, 3), "y": round(ts[0].y, 3), "class_candidate": cls,
                     "class_basis": "LABEL_TEXT_ONLY (never sufficient alone for wet identity)"})
    return rows


def door_candidates(inp, blob, floor, unit):
    occ = defaultdict(list)
    for p in inp.parts:
        if p.identity.instance_handles and p.visibility == CI.VISIBLE:
            occ[p.identity.instance_handles[0]].append(p)
    out = []
    for o, ps in sorted(occ.items()):
        sig = GR.door_signature(ps)
        if sig is None:
            continue
        ins = blob["inserts"].get(format(int(o), "X")) or {}
        out.append({"floor": floor, "occurrence": o, "block": ps[0].lineage[0].block_name if ps[0].lineage else None,
                    "leaf_layer": sorted({CI.effective_layer(p)[0] for p in ps}),
                    "swing_radius_native": round(sig["radius"], 3),
                    "leaf_width_mm_provisional": None if unit is None else round(sig["radius"] * unit, 1),
                    "hinge": [round(v, 3) for v in sig["hinge"]], "insert_layer": ins.get("layer"),
                    "status": "DOOR_SIGNATURE_CANDIDATE",
                    "not_admitted_because": "no DOOR layer role / reviewed claim (GR-02 needs signature AND role)"})
    return out


def topology(inp, rev, region, unrealised, claims=()):
    r = RT.run(inp, frame_insert=None, expected_revision_id=rev.revision_id, selected_region_id=region,
               unrealised=unrealised, closure_policy=TC.POLICY_ID, claims=claims)
    out = {"state": r["state"], "validation_state": r["validation"]["state"]}
    if r.get("sites") is None:
        return out, r
    u2 = (inp.unit_native_to_mm ** 2) / 1e6
    sites = r["sites"]
    certified = [s for s in sites if s["status"] != "REVIEW_REQUIRED"]
    big = max(sites, key=lambda s: s["area_m2"]) if sites else None
    out.update({"sites": len(sites), "by_status": dict(Counter(s["status"] for s in sites)),
                "certified_room_sites": len(certified),
                "issues": dict(sorted(Counter(i for s in sites for i in s["issues"]).items())),
                "largest_site": None if big is None else {"area_m2_provisional": round(big["area_m2"], 3),
                                                          "labels": len(big["labels"]), "issues": big["issues"]},
                "labelled_sites": sum(1 for s in sites if s["labels"]),
                "wall_bands": dict(Counter(b["state"] for b in (r.get("wall_bands") or {}).get("bands", []))),
                "closures": len((r.get("topology_closures") or {}).get("closures", [])),
                "passages": len(r.get("passages") or []),
                "roles": dict(sorted(Counter(v.role for v in r["roles"]["roles"].values()).items()))
                if isinstance(r.get("roles"), dict) and "roles" in r["roles"] else None,
                "result_digest": TD.digest(r)["sha256"], "unit_basis": u2})
    return out, r


def level_records(blob, b):
    recs = []
    for t in blob["texts"]:
        if t.x is None or not in_box(t.x, t.y, b):
            continue
        v = LM.parse_level(t.value)
        if v is not None:
            recs.append({"key": t.identity.key, "text": t.value, "value_m": v, "x": round(t.x, 3), "y": t.y,
                         "layer": t.layer, "height": t.height, "in_insert": bool(t.identity.instance_handles)})
    return sorted(recs, key=lambda r: (r["layer"], -r["y"], r["x"]))


# ------------------------------------------------------------------ structural
def grid(blob, b, layer):
    H, V = [], []
    for p in blob["parts"]:
        if p.kind != "SEGMENT" or CI.effective_layer(p)[0] != layer:
            continue
        g = p.geometry
        if not (b[0] <= min(g[0], g[2]) and max(g[0], g[2]) <= b[2] and b[1] <= min(g[1], g[3]) and
                max(g[1], g[3]) <= b[3]):
            continue
        if abs(g[1] - g[3]) <= 1e-6:
            H.append((g[1], g[0], g[2], p.identity.key))
        elif abs(g[0] - g[2]) <= 1e-6:
            V.append((g[0], g[1], g[3], p.identity.key))
    return H, V


def table_items(blob, b):
    it = [ST.Item(t.identity.key, t.value, t.x, t.y, "TEXT") for t in blob["texts"]
          if t.x is not None and t.value and in_box(t.x, t.y, b)]
    it += [ST.Item(f"ATTRIB|{o}|{tag}", v, x, y, "ATTRIB", tag, o) for tag, v, (x, y), o in blob["attributes"]
           if v not in (None, "") and in_box(x, y, b)]
    return it


def schedule_bounds(blob, title, layer="S-LINE.SCH"):
    """The table under a schedule title: the connected grid (segments of the grid layer that touch or cross each
    other) whose extent contains the title; the smallest such grid."""
    t = next(t for t in blob["texts"] if t.value and t.value.strip().upper() == title.upper())
    segs = [p for p in blob["parts"] if p.kind == "SEGMENT" and CI.effective_layer(p)[0] == layer]
    boxes = [(min(g[0], g[2]) - EPS, min(g[1], g[3]) - EPS, max(g[0], g[2]) + EPS, max(g[1], g[3]) + EPS)
             for g in (p.geometry for p in segs)]
    parent = list(range(len(segs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    order = sorted(range(len(boxes)), key=lambda i: boxes[i][0])
    for a_i, i in enumerate(order):                      # sweep on x: touching / crossing extents join one grid
        for j in order[a_i + 1:]:
            if boxes[j][0] > boxes[i][2]:
                break
            if boxes[j][1] <= boxes[i][3] and boxes[i][1] <= boxes[j][3]:
                parent[find(i)] = find(j)
    comp = defaultdict(list)
    for i in range(len(segs)):
        comp[find(i)].append(i)
    cands = []
    for ids in comp.values():
        b = (min(boxes[i][0] for i in ids) + EPS, min(boxes[i][1] for i in ids) + EPS,
             max(boxes[i][2] for i in ids) - EPS, max(boxes[i][3] for i in ids) - EPS)
        if in_box(t.x, t.y, b):
            cands.append(b)
    if not cands:
        return None, t.identity.key
    return min(cands, key=lambda b: (b[2] - b[0]) * (b[3] - b[1])), t.identity.key


def read_schedule(blob, title, header_rows, key_header):
    b, tkey = schedule_bounds(blob, title)
    if b is None:
        return {"title": title, "state": "TABLE_FRAME_NOT_FOUND", "title_key": tkey, "records": []}
    H, V = grid(blob, b, "S-LINE.SCH")
    tab = ST.read(table_items(blob, b), H, V, eps=EPS)
    # header bands: from the first band holding header words to the band above the first key value
    bands = tab["bands"]
    first_hdr = next(k for k, bd in enumerate(bands) if any(
        any(v["value"].strip().upper() in header_rows for v in c["values"]) for c in bd["cells"]))
    hdr = [first_hdr]
    while hdr[-1] + 1 < len(bands) and not any(v["kind"] == "ATTRIB" for c in bands[hdr[-1] + 1]["cells"]
                                                for v in c["values"]):
        hdr.append(hdr[-1] + 1)
    leaves = ST.header_paths(tab, hdr)
    recs, seen = [], set()
    for k in range(hdr[-1] + 1, len(bands)):
        rec = ST.record(tab, k, leaves)
        key = next((r for r in rec if any(key_header in p.upper() for p in r["path"])), None)
        if key is None or not key["values"]:
            continue
        sig = (tuple(key["keys"]), k if not key["merged_bands"] > 1 else None)
        kv = " ".join(key["values"])
        if (kv, sig[0]) in seen:
            for r_ in recs:
                if r_["type"] == kv:
                    r_["bands"].append(k)
                    for x, y in zip(r_["cells"], rec):
                        if y["values"] and y["merged_bands"] == 1:
                            x.setdefault("sub_rows", []).append(" ".join(CT.plain(v)[0] for v in y["values"]))
            continue
        seen.add((kv, sig[0]))
        recs.append({"type": kv, "bands": [k], "cells": [{"path": r["path"], "value": " ".join(
            CT.plain(v)[0] for v in r["values"]), "keys": r["keys"], "tags": [t for t in r["tags"] if t],
            "merged_bands": r["merged_bands"]} for r in rec]})
    return {"title": title, "title_key": tkey, "bounds": [round(v, 3) for v in b], "state": tab["state"],
            "unplaced": tab["unplaced"], "header_bands": hdr, "leaf_columns": [lf["path"] for lf in leaves],
            "records": recs, "table_digest": ST.digest(tab)}


def cell(rec, *words):
    for c in rec["cells"]:
        u = [p.upper() for p in c["path"]]
        if all(any(w in p for p in u) for w in words):
            return c
    return None


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def footing_schedule(sched) -> dict:
    out = {}
    for r in sched["records"]:
        # the header leaf labels are exactly 'L', 'W', 'H' under FOOTING SIZE (cm); the attribute tag never decides
        L = next((c for c in r["cells"] if c["path"][-1:] == ["L"]), None)
        Wd = next((c for c in r["cells"] if c["path"][-1:] == ["W"]), None)
        Hh = next((c for c in r["cells"] if c["path"][-1:] == ["H"]), None)
        sb = next((c for c in r["cells"] if c["path"][-1:] == ["SHORT BARS"]), None)
        lb = next((c for c in r["cells"] if c["path"][-1:] == ["LONG BARS"]), None)
        out[r["type"]] = {"L_cm": num(L and L["value"]), "W_cm": num(Wd and Wd["value"]),
                          "H_cm": num(Hh and Hh["value"]), "short_bars": sb and sb["value"],
                          "short_bars_sub_rows": sb and sb.get("sub_rows"), "long_bars": lb and lb["value"],
                          "long_bars_sub_rows": lb and lb.get("sub_rows"),
                          "keys": sorted({k for c in (L, Wd, Hh) if c for k in c["keys"]}),
                          "unit_note": "(cm) - header text of the FOOTING SIZE columns",
                          "attribute_tags_seen": sorted({t for c in (L, Wd, Hh) if c for t in c["tags"]})}
    return out


def ctype_names(sched):
    return [r["type"] for r in sched.get("records", [])]


def footing_tag_types(value):
    """'C2/F2' -> 'F2'; 'C/F' -> 'F'; 'F12' -> 'F12'; 'CN/FN' -> 'FN'. A tag without a footing part -> None."""
    for part in value.replace(" ", "").split("/"):
        if part.startswith("F"):
            return part
    return None


def build(work, commit=None) -> dict:
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    fw_census = firewall_census()
    loaded_before = set(sys.modules)
    with FW.OpenAudit() as audit:
        ctx = _build(work)
    ctx["code_commit"] = commit
    ctx["firewall"] = {"census": fw_census, "audit": audit.opened, "modules_loaded_during_build":
                       sorted(set(sys.modules) - loaded_before), "modules_all": sorted(sys.modules)}
    return ctx


def _build(work: Path) -> dict:
    got = intake(work)
    P = got["paths"]
    ctx = {"zips": got["zips"], "paths": {k: str(v.relative_to(work)) for k, v in P.items()}}
    # ---------------- manifest facts
    facts = {}
    for name, (h, disc, role) in FILES.items():
        p = P[name]
        ext = Path(name).suffix.lower()
        f = {"file": name, "discipline": disc, "declared_role": role, "sha256": h, "bytes": p.stat().st_size,
             "type": ext[1:].upper()}
        f.update(dxf_facts(p) if ext == ".dxf" else dwg_facts(p) if ext == ".dwg" else dwf_facts(p) if ext == ".dwf"
                 else pdf_facts(p))
        facts[name] = f
    if DWG_DECODE.exists():
        dec = json.loads(_bytes(DWG_DECODE).decode("utf-8", errors="replace"))
        hd = dec.get("HEADER", {})
        facts["P7757.dwg"].update({"decoded_by": "pinned LibreDWG decode (data/runs/cad_convert)",
                                   "insunits_declared": hd.get("INSUNITS"), "dimlfac": hd.get("DIMLFAC"),
                                   "last_saved_by": hd.get("LASTSAVEDBY"), "decode_entities": len(dec.get("OBJECTS", []))})
    ctx["facts"] = facts
    # ---------------- canonical inputs
    A = k2(P["P7757.dxf"], REV_ARCH, work / f"k2_{FILES['P7757.dxf'][0][:16]}.pkl")
    S = k2(P["ST7757.dxf"], REV_STR, work / f"k2_{FILES['ST7757.dxf'][0][:16]}.pkl")
    ra, rs = revision(REV_ARCH, FILES["P7757.dxf"][0]), revision(REV_STR, FILES["ST7757.dxf"][0])
    # ---------------- DWG vs DXF
    ident = {}
    if DWG_DECODE.exists():
        cache = work / f"rg_{FILES['P7757.dxf'][0][:16]}.pkl"
        if not cache.exists():
            doc, _ = K2R.load(str(P["P7757.dxf"]))
            cache.write_bytes(pickle.dumps({"rg": K2R.realise(doc), "insert_blocks": K2R.insert_blocks(doc)}))
        rec = RECON.run(str(cache), "P7757")
        ident["P7757"] = {"method": "r8_6a_reconcile: K1 (pinned decode of the DWG) vs K2 (ezdxf on the DXF), REAL "
                                    "tolerance, correlated by source handle", "summary": rec["summary"],
                          "state": "GEOMETRY_IDENTICAL" if rec["summary"]["verdict"] == "PASS" else "DIFFERENT",
                          "provenance": "the DXF is an owner re-save (AC1032, LASTSAVEDBY " +
                                        str(facts["P7757.dxf"]["last_saved_by"]) + ") - writer not independent"}
    ident["ST7757"] = {"method": "header only (no pinned decode of ST7757.dwg)", "state": "NOT_VERIFIED",
                       "dwg_version": facts["ST7757.dwg"]["cad_version"], "dxf_version": facts["ST7757.dxf"]["cad_version"]}
    ctx["identity"] = ident
    # ---------------- sheets
    fa, fs = frames(A), frames(S)
    sheets = []
    for disc, blob, fr in (("ARCHITECTURAL", A, fa), ("STRUCTURAL", S, fs)):
        for i, f in enumerate(fr):
            titles = sheet_titles(blob, f["bounds"])
            fl, kind = floor_of(titles) if disc == "ARCHITECTURAL" else (None, None)
            sheets.append({"discipline": disc, "sheet": f"{disc[:4]}-S{i + 1:02d}", "frame_handle": f["handle"],
                           "frame_layer": f["layer"], "bounds": [round(v, 3) for v in f["bounds"]],
                           "size_native": list(f["size"]), "titles": [t["text"] for t in titles],
                           "floor": fl, "view": kind})
    ctx["sheets"] = sheets
    # ---------------- units
    views = []
    lev_ev = []
    for s in sheets:
        if s["discipline"] == "ARCHITECTURAL" and s["view"] == "ELEVATION":
            recs = [r for r in level_records(A, s["bounds"]) if not r["in_insert"]]
            fam = Counter((r["layer"], r["height"]) for r in recs).most_common(1)
            marks = [{"key": r["key"], "text": r["text"], "y": r["y"], "layer": r["layer"], "height": r["height"]}
                     for r in recs if fam and (r["layer"], r["height"]) == fam[0][0]]
            ve = LM.view_evidence(marks, view_id=s["sheet"] + ":" + str(s["floor"]), source_sha256=ra.anchor_sha256)
            lev_ev += ve["evidence"]
            views.append({k: v for k, v in ve.items() if k != "evidence"})
    ua = unit_context("P7757.dxf", ra.anchor_sha256, facts["P7757.dxf"]["insunits_declared"], lev_ev, views)
    ctx["sheets_by_floor"] = {s["floor"]: s for s in sheets if s["floor"]}
    # ---------------- structural sheets by title
    ssheet = {}
    for s in sheets:
        if s["discipline"] != "STRUCTURAL":
            continue
        u = " ".join(s["titles"]).upper()
        for key, words in (("COLUMN_AXIS", ("COLUMN & AXIS",)), ("FOUNDATION", ("FOUNDATION PLAN",)),
                           ("GROUND_BEAMS", ("GROUND BEAMS",)), ("GF_ROOF_SLAB", ("GROUND FLOOR ROOF SLAB",)),
                           ("1F_ROOF_SLAB", ("FIRST FLOOR ROOF SLAB",)), ("2F_ROOF_SLAB", ("SECOND FLOOR ROOF SLAB",)),
                           ("SCHEDULES", ("SCHEDULE  OF COLUMNS", "SCHEDULE  OF  FOOTINGS")),
                           ("SIMPLE_BEAMS", ("SCHEDULE OF SIMPLE BEAMS",)), ("POOL_DOME", ("SWIMMING POOL",))):
            if any(w in u for w in words):
                s["structural_role"] = key
                ssheet.setdefault(key, s)
    ctx["structural_sheets"] = ssheet
    # ---------------- schedules
    fsch = read_schedule(S, "Schedule  of  Footings", ("TYPE",), "TYPE")
    csch = read_schedule(S, "Schedule  of Columns", ("TYPE",), "TYPE")
    bsch = read_schedule(S, "Schedule of Simple Beams", ("TYPE", "BEAM", "NO.", "SIZE"), "")
    ctx["schedules"] = {"FOOTINGS": fsch, "COLUMNS": csch, "SIMPLE_BEAMS": bsch}
    ftab = footing_schedule(fsch)
    ctx["footing_schedule"] = ftab
    # ---------------- footings: rectangles, tags, size check, unit evidence for ST
    fb = ssheet["FOUNDATION"]["bounds"]
    segs = [(p.identity.key,) + tuple(p.geometry) for p in S["parts"] if p.kind == "SEGMENT"
            and CI.effective_layer(p)[0] == "S-FOOTINGS" and in_box(p.geometry[0], p.geometry[1], fb)
            and in_box(p.geometry[2], p.geometry[3], fb)]
    rects = SQ.rectangles(segs, eps=EPS)
    tags = [{"key": t.identity.key, "value": t.value.strip(), "x": t.x, "y": t.y} for t in S["texts"]
            if t.x is not None and t.value and in_box(t.x, t.y, fb) and footing_tag_types(t.value.strip())
            and t.value.strip().upper() not in ("FOUNDATION PLAN.",) and len(t.value.strip()) <= 8]
    assoc = SQ.associate(rects, tags)
    ratios = []
    for r in assoc["rectangles"]:
        if len(r["tags"]) == 1:
            ft = ftab.get(footing_tag_types(r["tags"][0]["value"]))
            if ft and ft["L_cm"] and ft["W_cm"]:
                d = sorted([r["width"], r["height"]])
                s_ = sorted([ft["L_cm"] * 10.0, ft["W_cm"] * 10.0])
                ratios.append((s_[0] / d[0], s_[1] / d[1], r["tags"][0]["value"]))
    st_ev = []
    vals = sorted({round(x, 9) for a, b, _ in ratios for x in (a, b)})
    if ratios:
        lineage = (FR.family_lineage(FR.EXPLICIT_UNIT_NOTE, rs.anchor_sha256), "AUTHORED:FOOTING_SCHEDULE_CM_NOTE")
        agree = all(abs(v - vals[0]) / vals[0] <= FR.AGREEMENT_REL for v in vals)
        for k, v in enumerate([vals[0]] if agree else vals):
            st_ev.append(FR.UnitEvidence(f"FOOTING_SCHEDULE_CM:{k}", FR.NATIVE_UNIT, FR.EXPLICIT_UNIT_NOTE, "MODEL_SPACE",
                                         lineage, derived_value=v, observed_value=len(ratios), source_ref="FOOTING_SCHEDULE",
                                         source_sha256=rs.anchor_sha256, unit="cm"))
    us = unit_context("ST7757.dxf", rs.anchor_sha256, facts["ST7757.dxf"]["insunits_declared"], st_ev,
                      [{"view": "FOUNDATION_PLAN vs SCHEDULE OF FOOTINGS (cm)", "pairs": len(ratios),
                        "distinct_ratios": vals[:6]}])
    ctx["units"] = {"ARCHITECTURAL": ua, "STRUCTURAL": us}
    umm_a, umm_s = ua["native_to_mm"], us["native_to_mm"]
    frows, fcheck = [], []
    for r in assoc["rectangles"]:
        if len(r["tags"]) != 1:
            continue
        tag = r["tags"][0]
        typ = footing_tag_types(tag["value"])
        ft = ftab.get(typ)
        chk = None if ft is None or umm_s is None else SQ.size_check(r, ft["L_cm"] * 10, ft["W_cm"] * 10, umm_s, tol_mm=1.0)
        fcheck.append({"tag": tag["value"], "type": typ, "rectangle": [round(v, 3) for v in r["bounds"]],
                       "check": chk})
        blockers = [] if ft is not None else ["FOOTING_TYPE_NOT_IN_SCHEDULE"]
        if chk is not None and chk["state"] != SQ.SIZE_CONFIRMED:
            blockers.append("DRAWN_SIZE_CONTRADICTS_SCHEDULE")
        if chk is None and ft is not None:
            blockers.append("UNIT_NOT_ESTABLISHED_FOR_SIZE_CHECK")
        frows.append(SQ.concrete_row(
            item="STR-FTG", element_class="FOOTING", floor="FOUNDATION", element_id=f"{typ}@{tag['key'].split('|', 1)[1]}",
            count=1, dims={"L": {"m": ft and ft["L_cm"] / 100.0, "source": ft and "SCHEDULE OF FOOTINGS (cm) " + typ},
                           "W": {"m": ft and ft["W_cm"] / 100.0, "source": ft and "SCHEDULE OF FOOTINGS (cm) " + typ},
                           "H": {"m": ft and ft["H_cm"] / 100.0, "source": ft and "SCHEDULE OF FOOTINGS (cm) " + typ}},
            formula="1 x L x W x H", sources=[tag["key"]] + r["edge_keys"] + (ft["keys"] if ft else []),
            extra_blockers=blockers))
        frows[-1]["size_check"] = None if chk is None else (f"{chk['state']}: drawn {chk['drawn_mm']} mm vs schedule "
                                                            f"{chk['schedule_mm']} mm (tol {chk['tol_mm']} mm)")
    for o in assoc["orphans"]:
        typ = footing_tag_types(o["value"])
        ft = ftab.get(typ)
        frows.append(SQ.concrete_row(
            item="STR-FTG", element_class="FOOTING", floor="FOUNDATION", element_id=f"{typ}@{o['key'].split('|', 1)[1]}",
            count=None, dims={"L": {"m": ft and ft["L_cm"] / 100.0, "source": ft and "SCHEDULE OF FOOTINGS (cm) " + typ},
                              "W": {"m": ft and ft["W_cm"] / 100.0, "source": ft and "SCHEDULE OF FOOTINGS (cm) " + typ},
                              "H": {"m": ft and ft["H_cm"] / 100.0, "source": ft and "SCHEDULE OF FOOTINGS (cm) " + typ}},
            formula="1 x L x W x H", sources=[o["key"]],
            extra_blockers=["TAG_OUTSIDE_EVERY_DRAWN_FOOTING_RECTANGLE (boundary-clipped / rotated / tag drawn beside: "
                            "never matched by distance)"]))
    untagged = [i for i in assoc["issues"] if i["why"] == SQ.NO_TAG]
    ctx["footings"] = {"rectangles": len(rects), "tags": len(tags), "association": {
        "matched": sum(1 for r in assoc["rectangles"] if len(r["tags"]) == 1), "orphan_tags": [o["value"] for o in assoc["orphans"]],
        "issues": assoc["issues"]}, "size_checks": fcheck, "rows": frows, "untagged_rectangles": untagged}
    # ---------------- columns (counts by tag on the column plan; heights not established)
    cb = ssheet["COLUMN_AXIS"]["bounds"]
    ctags = Counter(t.value.strip() for t in S["texts"] if t.x is not None and t.value and in_box(t.x, t.y, cb)
                    and t.layer == "S-TEXT" and t.value.strip() in set(ctype_names(csch)))
    ctx["columns"] = {"tags_on_column_plan": dict(sorted(ctags.items())), "schedule": csch}
    # ---------------- slab thickness labels
    slabs = {}
    for key in ("GF_ROOF_SLAB", "1F_ROOF_SLAB", "2F_ROOF_SLAB"):
        sb = ssheet.get(key)
        if not sb:
            continue
        ts = [t for t in S["texts"] if t.x is not None and t.value and in_box(t.x, t.y, sb["bounds"])
              and t.layer == "S-TEXT-SLAB"]
        thick = Counter(t.value.strip() for t in ts if t.value.strip().isdigit())
        bars = Counter(CT.plain(t.value)[0].strip() for t in ts if "%%" in t.value.lower())
        slabs[key] = {"thickness_labels_cm": dict(sorted(thick.items())), "reinforcement_labels": dict(sorted(bars.items()))}
    ctx["slabs"] = slabs
    # ---------------- architectural floors
    arch = {}
    for fl in ("GF", "1F", "2F"):
        s = ctx["sheets_by_floor"].get(fl)
        if not s:
            arch[fl] = {"state": "PLAN_SHEET_NOT_FOUND"}
            continue
        inp = assemble(A, ra, s["bounds"], f"{s['sheet']}:{fl}", umm_a or 1.0,
                       "ALSENAN-PHASE-A-UNIT:" + (ua["status"] or "NONE"))
        troles = TX.classify(inp)
        labels = label_register(inp, fl, troles)
        doors = door_candidates(inp, A, fl, umm_a)
        strict, _ = topology(inp, ra, inp.region_id, A["unrealised"])
        arch[fl] = {"sheet": s["sheet"], "region": inp.region_id, "parts": len(inp.parts), "texts": len(inp.texts),
                    "labels": labels, "door_candidates": doors, "strict_topology": strict,
                    "levels": level_records(A, s["bounds"]),
                    "fixture_blocks": dict(Counter(p.lineage[0].block_name for p in inp.parts if p.lineage and
                                                   CI.effective_layer(p)[0] == "TOI" and p.identity.instance_handles)),
                    "stair_arrow_blocks": sorted({p.identity.instance_handles[0] for p in inp.parts if p.lineage and
                                                  p.lineage[0].block_name == "AR1" and p.identity.instance_handles})}
    # diagnostic hypothesis (GF only): the obvious layer guess, run to SHOW the weakness; produces no quantity
    s = ctx["sheets_by_floor"]["GF"]
    inp = assemble(A, ra, s["bounds"], f"{s['sheet']}:GF", umm_a or 1.0, "ALSENAN-PHASE-A-UNIT:DIAGNOSTIC")
    hyp = (("1", GR.TOPOLOGY_BOUNDARY), ("S-COL.BON", GR.STRUCTURAL_OBSTACLE), ("D", GR.OPENING_SYMBOL),
           ("TOI", GR.SANITARY_FIXTURE))
    claims = [RA.SourceLayerRoleClaim(f"PHASE-A-DIAGNOSTIC-HYPOTHESIS-{l}", ra.revision_id, ra.anchor_sha256, l,
                                      "EFFECTIVE", role, ("DIAGNOSTIC HYPOTHESIS - NOT A CLAIM",), "NONE", RA.REVIEWED)
              for l, role in hyp]
    diag, _ = topology(inp, ra, inp.region_id, A["unrealised"], claims=claims)
    ctx["diagnostic"] = {"floor": "GF", "hypothesis": [list(h) for h in hyp], "result": diag,
                         "status": "DIAGNOSTIC_ONLY - no quantity, no BOQ value",
                         "why_shown": "the layer roles are NOT established; this run shows that even the obvious "
                                      "hypothesis (layer 1 = wall faces) does not close the rooms"}
    ctx["arch"] = arch
    # layer census per architectural plan (evidence for the owner layer question)
    lay = Counter(CI.effective_layer(p)[0] for p in A["parts"])
    ctx["arch_layers"] = dict(sorted(lay.items()))
    return ctx


def main(work, regdir, commit=None):
    import alsenan_registers as REGS
    ctx = build(work, commit)
    regs = REGS.registers(ctx)
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({"firewall": regs["BENCHMARK_FIREWALL"]["audit_verdict"]["state"],
                      "freeze_schema": regs["ALSENAN_P7757_ST7757_PHASE_A_FREEZE"]["schema_validation"]["state"],
                      "units": {k: v["status"] for k, v in ctx["units"].items()},
                      "footings": regs["CONCRETE_REGISTER"]["footing_summary"],
                      "xlsx": regs["QA_RECONCILIATION"]["xlsx"]["readback"]["state"]}, indent=1))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:4])
