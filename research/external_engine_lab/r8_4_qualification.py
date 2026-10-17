"""R8.4 §11-§17 — decoder qualification register, target feature profiles, independent reconciliation.

Research lab only (SHADOW). Computes, for each real source, the FEATURE PROFILE a decoder would
have to be qualified for (engine/source/qualification.py), and records the qualification register.
No qualification is granted here: the only thing that can grant one is an executed K1-vs-K2
reconciliation against an INDEPENDENT export (§14-§17), and none was supplied.

    python3 research/external_engine_lab/r8_4_qualification.py <out_dir>
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import cad_profile as P, decoder_pins as PINS, qualification as Q   # noqa: E402
from engine.source.cad import libredwg_map as L                                          # noqa: E402

UPLOADS = Path("/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240")
SCRATCH = Path("/tmp/claude-0/-home-user-Urban-Project-AI/93607c01-16a4-590f-af7c-1c2701c3b240/scratchpad")
SOURCES = {
    "ALRASHED": {"sha256": "299c61b1df7660384e027d44c0a29d8b64c92995843c0517cea05d485974660c",
                 "decodes": ["data/runs/cad_convert/ALRASHED_ARCHITECTURAL.json",
                             "data/runs/pinned_redecode/ALRASHED_PINNED_REDECODE.json"]},
    "P7757": {"sha256": "7f61f3ac",   # prefix; full hash read from the pinned-redecode record
              "decodes": ["data/runs/cad_convert/P7757_ARCHITECTURAL.json",
                          "data/runs/pinned_redecode/P7757_PINNED_REDECODE.json"]},
    "QORTUBA": {"sha256": "2ec3a9c8",
                "decodes": ["data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json",
                            "data/runs/pinned_redecode/QORTUBA_PINNED_REDECODE.json"]},
}
# the historical decodes are the ones the active path consumed; their pin status is REPRODUCED_BY_REGISTERED_BUILD
BUILD = PINS.PINS["LIBREDWG_DWGREAD"][0]["sha256"]
DXF_PATTERNS = ("*.dxf", "*.DXF", "*.dxf.zip", "*autocad*", "*AUTOCAD*", "*oda*.dxf", "*ODA*")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(p):
    raw = Path(p).read_bytes()
    try:
        return json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return json.loads(raw.decode("utf-8", errors="replace"))


def full_source_sha(name):
    rec = json.loads((ROOT / "data/runs/pinned_redecode/PINNED_REDECODE_RESULTS.json").read_text())
    for c in rec["projects"].get(name, {}).get("dwg_candidates", []):
        if c.get("present") and c["sha256"].startswith(SOURCES[name]["sha256"]):
            return c["sha256"]
    return SOURCES[name]["sha256"]


def dxf_search():
    """Every DXF-like file reachable in the repo, the upload store and the scratchpad, with a
    verdict. A file qualifies as the independent P7757 export only if it is a DXF (text header
    or AutoCAD binary DXF sentinel) whose provenance says it was written by a non-LibreDWG
    writer from the P7757 DWG. None does."""
    rows = []
    for base in (ROOT / "data", UPLOADS, SCRATCH):
        if not base.exists():
            continue
        for pat in DXF_PATTERNS:
            for p in base.rglob(pat):
                if not p.is_file():
                    continue
                head = p.read_bytes()[:256]
                is_zip = head[:2] == b"PK"
                lines = [x.strip() for x in head.splitlines()]
                is_dxf = bool(lines) and (lines[0] in (b"0", b"999") or head.startswith(b"AutoCAD Binary DXF"))
                writer = lines[1].decode("latin-1") if is_dxf and lines[0] == b"999" and len(lines) > 1 else None
                if is_dxf and writer and "libredwg" in writer.lower():
                    verdict = (f"NOT_INDEPENDENT: written by {writer} — the same parser lineage as D1; a LibreDWG -> DXF -> "
                               "ezdxf chain is CORRELATED, not an INDEPENDENT_PARSER (R8.3 review)")
                elif is_dxf:
                    verdict = "NOT_ACCEPTED: DXF without recorded provenance tying it to the P7757 DWG and a non-LibreDWG writer"
                elif is_zip:
                    verdict = "NOT_ACCEPTED: archive; contents not a supplied independent export"
                else:
                    verdict = "NOT_A_DXF: " + head[:60].decode("latin-1", errors="replace").replace("\n", " ")
                rows.append({"path": str(p), "bytes": p.stat().st_size, "sha256": sha(p), "zip": is_zip,
                             "dxf_header": is_dxf, "writer_comment": writer, "verdict": verdict})
    seen, out = set(), []
    for r in rows:
        if r["path"] not in seen:
            seen.add(r["path"])
            out.append(r)
    return out


def main(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    profiles, register = {}, []
    for name, s in SOURCES.items():
        path = next((ROOT / d for d in s["decodes"] if (ROOT / d).exists()), None)
        src = full_source_sha(name)
        decode = load(path)
        doc = L.to_document(decode, source_sha256=src)
        prof = Q.source_feature_profile(doc, decode)
        cover = Q.qualification_for(BUILD, prof, P.DEFAULT_PARSER_POLICY.qualifications)
        empty = Q.QualificationEnvelope().covers(prof)
        profiles[name] = {"source_sha256": src, "decode": str(path.relative_to(ROOT)), "decode_sha256": sha(path),
                          "decoder_binary_sha256": BUILD, "feature_profile": prof.as_dict(),
                          "coverage_under_current_register": cover,
                          "features_an_envelope_must_cover": list(empty)}
        status = Q.BLOCKED_EXTERNAL_INPUT if name == "P7757" else Q.NOT_EXECUTED
        q = Q.DecoderQualification(
            f"DQ-R8_4-{name}", "LIBREDWG_DWGREAD_JSON (D1) -> K1", BUILD, status, Q.QualificationEnvelope(),
            reference_source_sha256=(src,), independent_route="INDEPENDENT_DXF (AutoCAD / ODA writer) -> EZDXF (D2) -> K2",
            excluded_capabilities=tuple(empty),
            evidence="research/external_engine_lab/r8_4_qualification.py",
            notes=("independent P7757 DXF not supplied (§17): INDEPENDENT_REAL_RECONCILIATION = BLOCKED_EXTERNAL_INPUT; "
                   "build NOT qualified" if name == "P7757" else
                   "no independent export requested for this source in R8.4; not executed"))
        register.append(q.as_dict())
    search = dxf_search()
    recon = {"SCHEMA": "URBAN_R8_4_INDEPENDENT_RECONCILIATION_V1",
             "INDEPENDENT_REAL_RECONCILIATION": "BLOCKED_EXTERNAL_INPUT",
             "target_source": {"project": "P7757", "sha256": full_source_sha("P7757")},
             "required_input": ("a DXF written from the P7757 DWG by AutoCAD or the ODA File Converter (not LibreDWG), "
                                "supplied as-is: hashed on receipt, never rewritten or repaired, provenance recorded "
                                "(writer, version, export options, who exported it)"),
             "planned_procedure": ["hash the DXF; record provenance", "D1 (LibreDWG JSON) -> K1 and D2 (ezdxf on the DXF) -> K2",
                                   "reconcile per handle and per instance path (engine/source/reconcile.py, REAL tolerance)",
                                   "report every non-PASS row with handle, instance path, field class",
                                   "qualify ONLY the envelope the PASS rows exercised"],
             "search": search, "rows": [], "qualified_envelope": None}
    envelope = {"SCHEMA": "URBAN_R8_4_DECODER_QUALIFICATION_ENVELOPE_V1",
                "rule": "target features ⊆ qualified envelope (engine/source/qualification.QualificationEnvelope.covers)",
                "qualified_envelopes": [], "target_feature_profiles": profiles,
                "handle_risk_basis": "representation (byte size vs value, collisions, absolute-reference resolution, max size); "
                                     "no object-count threshold"}
    reg = {"SCHEMA": "URBAN_R8_4_DECODER_QUALIFICATION_REGISTER_V1", "parser_policy": P.DEFAULT_PARSER_POLICY.policy_id,
           "cad_profile": P.DEFAULT_CAD_PROFILE.profile_id,
           "compatibility": {"URBAN_PARSER_INDEPENDENCE_V1.qualified_builds": sorted(P.PARSER_POLICY_V1.qualified_builds),
                             "note": "kept for V1 reproducibility only; V2 ignores it"},
           "qualifications": register}
    for fn, obj in (("DECODER_QUALIFICATION_REGISTER.json", reg), ("DECODER_QUALIFICATION_ENVELOPE.json", envelope),
                    ("INDEPENDENT_RECONCILIATION_RESULTS.json", recon)):
        (out_dir / fn).write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    print(json.dumps({k: {"handle": v["feature_profile"]["handle"], "uncovered": v["features_an_envelope_must_cover"][:12]}
                      for k, v in profiles.items()}, indent=1))
    print("dxf candidates:", len(search))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "research/external_engine_lab/outputs/r8_4")
