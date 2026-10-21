"""R8.5 §2-§6, §22-§25 — capability-signature register and decoder qualification V2 records.

Research lab only. Target signatures of each real source (engine/source/qualification.capability_signatures)
and the V2 qualification records. No record is QUALIFIED: that needs an executed K1-vs-K2 comparison on an
INDEPENDENT (AutoCAD / ODA-written) export, and none has been supplied. The DXF search is re-run.

    python3 research/external_engine_lab/r8_5_qualification.py <out_dir>
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from engine.source import cad_profile as P, decoder_pins as PINS, qualification as Q      # noqa: E402
from engine.source.cad import libredwg_map as L                                             # noqa: E402

from r8_4_qualification import SOURCES, dxf_search, full_source_sha, load                  # noqa: E402

BUILD = PINS.PINS["LIBREDWG_DWGREAD"][0]["sha256"]


def dims(sig):
    return dict(p.split("=", 1) for p in sig.split("|"))


def main(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    sig_reg, records = {"SCHEMA": "URBAN_R8_5_CAPABILITY_SIGNATURE_REGISTER_V1",
                        "dimensions": ["KIND", "CHAIN", "NET", "DEPTH", "EXT", "CTX", "VIS", "HANDLE", "REF"],
                        "equivalence_rules": [r.equivalence_rule_id for r in Q.EQUIVALENCE_RULES], "projects": {}}, []
    for name, s in SOURCES.items():
        path = next(ROOT / d for d in s["decodes"] if (ROOT / d).exists())
        src = full_source_sha(name)
        doc = L.to_document(load(path), source_sha256=src)
        sigs = Q.capability_signatures(doc)
        cov = Q.coverage_v2(sigs, (), BUILD)
        by = Counter()
        for sig, keys in sigs.items():
            d = dims(sig)
            by[("REF:" + d["REF"]) if "REF" in d else d["KIND"]] += len(keys)
        handle = Counter(dims(sg).get("HANDLE", dims(sg).get("TARGET")) for sg in sigs)
        sig_reg["projects"][name] = {
            "source_sha256": src, "signature_count": len(sigs), "occurrences": sum(len(v) for v in sigs.values()),
            "occurrences_by_kind_or_reference": dict(by), "signatures_by_handle_class": dict(handle),
            "max_depth": max((int(dims(sg).get("DEPTH", 0)) for sg in sigs), default=0),
            "net_reflected_signatures": sum(1 for sg in sigs if "NET=NET_REFLECTED" in sg),
            "signatures": [{"signature": sg, "occurrences": len(v), "example": [v[0][0], list(v[0][1])]}
                           for sg, v in sorted(sigs.items())],
            "coverage": {"covered": cov["covered"], "not_exercised": sum(1 for u in cov["uncovered"] if u[1] == Q.NOT_EXERCISED),
                         "reason": cov["reason"]}}
        status = Q.BLOCKED_EXTERNAL_INPUT if name == "P7757" else Q.NOT_EXECUTED
        records.append(Q.DecoderQualificationV2(
            f"DQ2-R8_5-{name}", "LIBREDWG_DWGREAD_JSON (D1) -> K1", BUILD, status, (), (src,),
            "INDEPENDENT_DXF (AutoCAD / ODA writer) -> EZDXF (D2) -> K2",
            notes=("independent P7757 DXF not supplied: no signature exercised" if name == "P7757" else
                   "no independent export requested for this source")).as_dict())
        print(name, len(sigs), sum(len(v) for v in sigs.values()), dict(handle))
    search = dxf_search()
    q2 = {"SCHEMA": Q.QUALIFICATION_SCHEMA_V2, "parser_policy": P.DEFAULT_PARSER_POLICY.policy_id,
          "cad_profile": P.DEFAULT_CAD_PROFILE.profile_id, "states": [Q.EXERCISED_AND_PASS, Q.EXERCISED_NONPASS, Q.NOT_EXERCISED],
          "rule": ("a signature enters a qualification only as EXERCISED_AND_PASS: every occurrence compared and PASS; "
                   "WARN / BLOCK / limitation / unmatched / ambiguous / not compared = EXERCISED_NONPASS; no percentage"),
          "v1_records_kept": "URBAN_DECODER_QUALIFICATION_V1 (R8.4 flat envelope) reproducible, not used by parser V3",
          "qualified_signatures": [], "records": records}
    rec = {"SCHEMA": "URBAN_R8_5_INDEPENDENT_RECONCILIATION_V1",
           "INDEPENDENT_REAL_RECONCILIATION": "BLOCKED_EXTERNAL_INPUT",
           "expected_input": "P7757_AUTOCAD_2018_INDEPENDENT.dxf or an ODA-written equivalent",
           "found": [x for x in search if x["dxf_header"] and x["writer_comment"] and "libredwg" not in x["writer_comment"].lower()],
           "search": search, "qualified_signatures": [],
           "handle_domains_to_prove": ["3-byte handle identity", "absolute references", "INSERT lineage",
                                       "BLOCK_RECORD lineage"]}
    for fn, obj in (("CAPABILITY_SIGNATURE_REGISTER.json", sig_reg), ("DECODER_QUALIFICATION_V2.json", q2),
                    ("INDEPENDENT_RECONCILIATION_RESULTS.json", rec)):
        (out_dir / fn).write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str))
    print("independent found:", len(rec["found"]), "searched:", len(search))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "research/external_engine_lab/outputs/r8_5")
