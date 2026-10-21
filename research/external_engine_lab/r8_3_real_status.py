"""R8.3 §28-§30, §33, §42 — unit / region / frame / CAD_PROFILE status of the three real sources.

Research lab only (SHADOW). Every status here is CALCULATED by engine/source/frame.py and
cad_profile.py from evidence emitted by engine/source/cad/unit_evidence.py; nothing is set by
hand and no quantity, room or total is read. No project's evidence is transferred to another.

    python3 research/external_engine_lab/r8_3_real_status.py > out.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import cad_profile as P, decoder_pins as PINS, frame as FR          # noqa: E402
from engine.source.conservation import conservation                                     # noqa: E402
from engine.source.cad import kernel as K1, libredwg_map as L, unit_evidence as UE      # noqa: E402

UPLOADS = Path("/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240")
PROJECTS = {
    "ALRASHED": {"decode": "data/runs/cad_convert/ALRASHED_ARCHITECTURAL.json", "dwg": UPLOADS / "a0f821ff-16-11-2025.dwg"},
    "P7757": {"decode": "data/runs/cad_convert/P7757_ARCHITECTURAL.json",
              "dwg": ROOT / "data/golden/7757/source_c/P7757_ARCHITECTURAL.dwg"},
    "QORTUBA": {"decode": "data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json", "dwg": UPLOADS / "b634a91b-qurtoba1.dwg"},
}
INDEPENDENT_DXF_GLOBS = ("*INDEPENDENT*.dxf", "*AUTOCAD*.dxf", "*ODA*.dxf")
AREA = P.MeasurementMethod("SCALE_DEPENDENT_AREA_OR_LENGTH", scale_dependent=True)
COUNT = P.MeasurementMethod("COUNT_BY_ESTABLISHED_IDENTITY", scale_dependent=False, requires_identity=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(path):
    raw = (ROOT / path).read_bytes()
    try:
        return json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return json.loads(raw.decode("utf-8", errors="replace"))


def independent_dxf():
    found = []
    for base in (ROOT, UPLOADS):
        for g in INDEPENDENT_DXF_GLOBS:
            found += [str(p) for p in base.rglob(g) if p.is_file()] if base.exists() else []
    return sorted(set(found))


def column_closure(decode, document, realised):
    """Question A (§33): is the column polygon physically closed? Source flag vs K1 realisation."""
    layers = {tuple(o["handle"][1:]) if False else o["handle"][-1]: o.get("name")
              for o in decode["OBJECTS"] if o.get("object") == "LAYER"}
    cols = [o for o in decode["OBJECTS"] if o.get("type") == 77 and layers.get((o.get("layer") or [None])[-1]) == "col.str"]
    closed = [o for o in cols if int(o.get("flag", 0) or 0) & 512]
    spans = Counter(str(s.lineage.source_handle) for s in realised.segments)
    arcs = Counter(str(a.lineage.source_handle) for a in realised.arcs)
    ok = 0
    detail = []
    for o in closed:
        hid = L.handle_id(o.get("handle"))
        n = len(o.get("points") or [])
        got = spans.get(hid, 0) + arcs.get(hid, 0)
        inst = max(1, got // max(n, 1)) if got else 0
        ok += got >= n and got % n == 0 if n else 0
        if len(detail) < 12:
            detail.append({"handle": hid, "vertices": n, "flag": o.get("flag"), "k1_spans_realised": got})
    return {"layer": "col.str", "lwpolylines": len(cols), "source_closed_flag_512": len(closed),
            "flag_bit_1_set_on_closed": sum(1 for o in closed if int(o.get("flag", 0)) & 1),
            "k1_realises_closing_span": ok, "sample": detail,
            "answer": "PHYSICALLY_CLOSED_PER_SOURCE" if closed and ok == len(closed) else "SEE_DETAIL"}


def run(proj, s):
    d = load(s["decode"])
    dsha = sha(ROOT / s["decode"])
    src = sha(s["dwg"]) if Path(s["dwg"]).exists() else None
    doc = L.to_document(d, source_sha256=src)
    rg = K1.realise(doc)
    cons = conservation(doc, rg, raw_entity_rows=doc.notes.get("raw_entity_rows"))
    balanced = all(cons[k]["BALANCED"] for k in ("source_level", "observation_level", "visit_level"))
    ex = UE.extract(d, src)
    uc = FR.unit_context(src, "MODEL_SPACE", FR.MODEL_SPACE, ex["evidence"], insunits=d.get("HEADER", {}).get("INSUNITS"))
    rt = FR.region_transform(uc, "MODEL_SPACE_WHOLE", FR.MODEL_SPACE_PLAN, reference=False)
    rt_findings = tuple(ex["findings"])
    fr = FR.measurement_frame(uc, rt)
    pin = PINS.decode_status(dsha)
    ctx = P.SourceValidationContext(balanced, pin, PINS.PINS["LIBREDWG_DWGREAD"][0]["sha256"],
                                    tuple(f for f in doc.findings if f.obs_id is None), reconciliation=None)
    profiles = {}
    for kind, method in (("LINE", AREA), ("LWPOLYLINE", AREA), ("ELLIPSE", AREA), ("INSERT", COUNT)):
        r = P.evaluate(kind, "REPRESENTATIVE", (), method, ctx, fr, uc, rt, region_findings=rt_findings)
        profiles[f"{kind}/{method.method_id}"] = r.as_dict()
    trunc = next((f for f in doc.findings if f.code == "HANDLE_VALUE_TRUNCATED"), None)
    out = {
        "project": proj, "source_file": str(s["dwg"]), "source_sha256": src,
        "original_dwg_available": Path(s["dwg"]).exists(),
        "historical_decode": s["decode"], "historical_decode_sha256": dsha,
        "historical_decoder_pin_status": pin,
        "handle_representation": ("PINNED_LIBREDWG_DWGREAD_JSON_HANDLE_REPRESENTATION_DEFECT present: " + trunc.detail)
        if trunc else "no 3-byte handles",
        "k1": {"segments": len(rg.segments), "arcs": len(rg.arcs), "circles": len(rg.circles),
               "elliptical_arcs": len(rg.elliptical_arcs), "unplaced": len(rg.unplaced)},
        "conservation_balanced": balanced, "conservation": cons,
        "unit_evidence_rows": ex["rows"], "scale_notes": ex["scale_notes"],
        "unit_context": uc.as_dict(), "region": rt.as_dict(),
        "region_findings": [f.as_dict() for f in rt_findings], "frame": fr.as_dict(),
        "cad_profile": profiles,
    }
    if proj == "ALRASHED":
        out["column_question_A"] = column_closure(d, doc, rg)
    return out


def main():
    ind = independent_dxf()
    res = {"SCHEMA": "URBAN_R8_3_REAL_STATUS_V1", "independent_dxf_found": ind,
           "INDEPENDENT_REAL_RECONCILIATION": "EXECUTED" if ind else "BLOCKED_EXTERNAL_INPUT",
           "projects": {p: run(p, s) for p, s in PROJECTS.items()}}
    return res


if __name__ == "__main__":
    print(json.dumps(main(), indent=1, default=str))
