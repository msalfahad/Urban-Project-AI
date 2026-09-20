"""PA08 source acceptance: what a candidate source package is, before the production engine reads it.

Records PROJECT_ALIAS, SOURCE_FILES, SOURCE_HASHES, DWG/DXF version, PDF page count, vector-or-raster, text
availability, unit status, KNOWN_PRIOR_EXPOSURE, and answers HAS_THIS_PROJECT_BEEN_USED_TO_DEVELOP_THE_ENGINE.
A YES rejects the package as independent validation (it may still serve as a regression project).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from research.qs_wall_treatment_01.pa08 import config as C8

MINIMUM = {"REQUIRED": ["ARCHITECTURAL_DWG_OR_DXF (or a LibreDWG JSON decode)", "ORIGINAL_ARCHITECTURAL_PDF"], "STRONGLY_PREFERRED": ["STRUCTURAL_DWG_OR_PDF"],
           "OPTIONAL": ["SANITARY", "ELECTRICAL"], "NOT_REQUIRED": ["Excel BOQ", "contractor invoice", "previous takeoff", "final quantities"]}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _dwg_version(p):
    with open(p, "rb") as f:
        head = f.read(6)
    return head.decode("ascii", "replace") if head.startswith(b"AC10") else "UNKNOWN"


def _dxf_version(p):
    try:
        with open(p, "r", errors="replace") as f:
            txt = f.read(20000)
        m = re.search(r"\$ACADVER\s*\n\s*1\s*\n\s*(AC\d+)", txt)
        return m.group(1) if m else "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def _pdf_facts(p):
    facts = {"PAGE_COUNT": None, "VECTOR_OR_RASTER": "UNKNOWN", "TEXT_AVAILABILITY": "UNKNOWN"}
    try:
        import pypdf
        r = pypdf.PdfReader(str(p))
        facts["PAGE_COUNT"] = len(r.pages)
        texts, images, vectors = 0, 0, 0
        for pg in r.pages[:12]:
            t = pg.extract_text() or ""
            texts += len(t.strip())
            try:
                images += len(pg.images)
            except Exception:
                pass
            try:
                c = pg.get_contents()
                data = c.get_data() if c is not None else b""
                vectors += data.count(b" l\n") + data.count(b" c\n") + data.count(b" re\n")
            except Exception:
                pass
        facts["VECTOR_OR_RASTER"] = "VECTOR" if vectors > 200 else ("RASTER" if images and vectors <= 200 else "UNKNOWN")
        facts["TEXT_AVAILABILITY"] = "TEXT_LAYER" if texts > 200 else ("NONE_OR_OUTLINED" if texts == 0 else "SPARSE")
    except Exception as e:
        facts["ERROR"] = repr(e)
    return facts


def _decode_facts(p):
    """A LibreDWG JSON decode: INSUNITS / DIMLFAC and entity counts, without interpreting geometry."""
    try:
        d = json.loads(Path(p).read_text("utf-8"))
        objs = d.get("OBJECTS", [])
        hdr = d.get("HEADER", {})
        ins = hdr.get("INSUNITS"); dimlfac = hdr.get("DIMLFAC")
        layers = sorted({str(o.get("name", "")) for o in objs if o.get("object") == "LAYER"})
        ltypes = sorted({str(o.get("name", "")) for o in objs if o.get("object") == "LTYPE"})
        beam_conv = [n for n in layers if any(t in n.upper() for t in ("BEAM", "BM", "CEIL", "SLAB"))] + [n for n in ltypes if any(t in n.upper() for t in ("HIDDEN", "DASH"))]
        return {"ENTITIES": len(objs), "INSUNITS": ins, "DIMLFAC": dimlfac, "TEXT_ENTITIES": sum(1 for o in objs if o.get("entity") in ("TEXT", "MTEXT")),
                "UNIT_STATUS": "DECLARED_MM" if ins == 4 else ("DECLARED_OTHER" if ins else "UNDECLARED"), "VECTOR_OR_RASTER": "VECTOR",
                "LAYERS": layers[:200], "LINETYPES": ltypes[:50],
                # gate Q11: a beam drawn with continuous lines on the wall layer is indistinguishable from a partition; the source must carry a convention
                "BEAM_CONVENTION": {"STATUS": "LAYER_OR_LINETYPE_PRESENT" if beam_conv else "ABSENT_BEAMS_ON_PLAN_UNRESOLVABLE", "WITNESSES": beam_conv[:20]}}
    except Exception as e:
        return {"ERROR": repr(e), "UNIT_STATUS": "UNKNOWN"}


def classify(p):
    s = str(p).lower()
    if s.endswith(".dwg"):
        return "ARCHITECTURAL_DWG_OR_DXF_CANDIDATE"
    if s.endswith(".dxf"):
        return "ARCHITECTURAL_DWG_OR_DXF_CANDIDATE"
    if s.endswith(".json"):
        try:
            head = Path(p).read_text("utf-8")[:4000] if Path(p).exists() else ""
        except Exception:
            head = ""
        return "PRIMITIVE_JSON_SYNTHETIC" if '"primitives"' in head and '"OBJECTS"' not in head else "CAD_DECODE_JSON"
    if s.endswith(".pdf"):
        return "PDF"
    if s.endswith((".xlsx", ".xls", ".csv")):
        return "FORBIDDEN_SPREADSHEET"
    return "OTHER"


def accept(project_alias, files, families=None, declared_exposure=None):
    """Acceptance record for a candidate package.  `families` maps path -> ARCHITECTURAL / STRUCTURAL / SANITARY / ELECTRICAL."""
    families = families or {}
    dev_hashes = {}
    for pid, meta in C8.DEVELOPMENT_PROJECTS.items():
        for path in meta["PATHS"]:
            if Path(path).exists():
                dev_hashes[sha256(path)] = pid
    rows, exposure = [], []
    for f in files:
        p = Path(f)
        row = {"PATH": str(p), "EXISTS": p.exists(), "KIND": classify(p), "FAMILY": families.get(str(p), "UNDECLARED"), "BYTES": p.stat().st_size if p.exists() else None, "SHA256": sha256(p) if p.exists() else None}
        if row["KIND"] == "FORBIDDEN_SPREADSHEET":
            row["REFUSED"] = "spreadsheets are never part of a validation source package"
        elif p.exists():
            if p.suffix.lower() == ".dwg":
                row["DWG_VERSION"] = _dwg_version(p); row["VECTOR_OR_RASTER"] = "VECTOR"; row["DECODER_AVAILABLE"] = False; row["NOTE"] = "no DWG decoder in this environment: supply a DXF or a LibreDWG JSON decode of the same file"
            elif p.suffix.lower() == ".dxf":
                row["DXF_VERSION"] = _dxf_version(p); row["VECTOR_OR_RASTER"] = "VECTOR"; row["DECODER_AVAILABLE"] = True
            elif p.suffix.lower() == ".pdf":
                row.update(_pdf_facts(p))
            elif row["KIND"] == "PRIMITIVE_JSON_SYNTHETIC":
                row["NOTE"] = "a primitive JSON is a synthetic / test-mode document, never an accepted validation source"; row["UNIT_STATUS"] = "SYNTHETIC"; row["VECTOR_OR_RASTER"] = "VECTOR"; row["DECODER_AVAILABLE"] = True
            elif p.suffix.lower() == ".json":
                row.update(_decode_facts(p))
            if row["SHA256"] in dev_hashes:
                exposure.append({"PATH": str(p), "MATCHES_DEVELOPMENT_PROJECT": dev_hashes[row["SHA256"]], "BY": "sha256"})
        rows.append(row)
    alias_hit = [a for a in C8.DEVELOPMENT_ALIASES if a.lower() in str(project_alias).lower() or any(a.lower() in Path(f).name.lower() for f in files)]
    if alias_hit:
        exposure.append({"ALIAS_HIT": alias_hit, "BY": "alias / file name"})
    dir_hit = [a for a in C8.DEVELOPMENT_ALIASES if any(a.lower() in str(Path(f).parent).lower() for f in files)]
    if declared_exposure:
        exposure.append({"DECLARED": declared_exposure, "BY": "owner declaration"})
    has_arch = any(r["KIND"] in ("ARCHITECTURAL_DWG_OR_DXF_CANDIDATE", "CAD_DECODE_JSON") and r["EXISTS"] and r.get("FAMILY") in ("ARCHITECTURAL", "UNDECLARED") for r in rows)
    has_pdf = any(r["KIND"] == "PDF" and r["EXISTS"] for r in rows)
    decodable = any((r["KIND"] == "CAD_DECODE_JSON" or r.get("DECODER_AVAILABLE")) and r["EXISTS"] for r in rows)
    synthetic = any(r["KIND"] == "PRIMITIVE_JSON_SYNTHETIC" for r in rows)
    used = bool(exposure)
    units = [r.get("UNIT_STATUS") for r in rows if r.get("UNIT_STATUS")]
    rec = {"ARTIFACT": "PA08_SOURCE_ACCEPTANCE", "PROJECT_ALIAS": project_alias, "SOURCE_FILES": [r["PATH"] for r in rows], "SOURCE_HASHES": {r["PATH"]: r["SHA256"] for r in rows}, "FILES": rows,
           "MINIMUM_PACKAGE": MINIMUM, "MINIMUM_PACKAGE_MET": has_arch and has_pdf, "DECODABLE_ARCHITECTURAL_SOURCE": decodable,
           "PDF_PAGE_COUNT": {r["PATH"]: r.get("PAGE_COUNT") for r in rows if r["KIND"] == "PDF"}, "VECTOR_OR_RASTER": {r["PATH"]: r.get("VECTOR_OR_RASTER") for r in rows},
           "TEXT_AVAILABILITY": {r["PATH"]: r.get("TEXT_AVAILABILITY") for r in rows if r["KIND"] == "PDF"}, "UNIT_STATUS": units[0] if units else "UNKNOWN_UNTIL_DECODED",
           "KNOWN_PRIOR_EXPOSURE": exposure, "DIRECTORY_CARRIES_DEVELOPMENT_ALIAS": dir_hit, "HAS_THIS_PROJECT_BEEN_USED_TO_DEVELOP_THE_ENGINE": "YES" if used else "NO",
           "SYNTHETIC_SOURCE": synthetic,
           "INDEPENDENT_VALIDATION_STATUS": "REJECTED_NOT_INDEPENDENT" if used else ("REJECTED_SYNTHETIC_DRY_RUN_ONLY" if synthetic else ("ACCEPTED" if (has_arch and has_pdf and decodable) else "INCOMPLETE_PACKAGE")),
           "REGRESSION_USE_ALLOWED": True}
    return rec
