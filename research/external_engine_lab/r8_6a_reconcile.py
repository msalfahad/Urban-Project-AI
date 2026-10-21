"""R8.6A — DIAGNOSTIC reconciliation of the supplied DXFs against D1 (shadow; nothing qualifies).

K1 = D1 (pinned LibreDWG decode of the exact DWG) -> kernel.realise.
K2 = the supplied DXF -> ezdxf -> kernel_ezdxf.realise (loaded read-only; the file is never rewritten).
reconcile.reconcile with the R8.2 REAL tolerance (declared before any real comparison, not tuned here),
correlation by handle + instance path only, block lineage by block-record handle. No nearest-neighbour.

Every per-signature result is passed through independent_export.scoped_signature_states (by r8_6a_intake.py): while the DXF's
decoder is not proven independent, every signature reads PROVENANCE_NOT_INDEPENDENT and the diagnostic
outcome is kept beside it.

    python3 research/external_engine_lab/r8_6a_reconcile.py <k2_pickle> <project> <out_json> [round1_proof]
"""

from __future__ import annotations

import json
import pickle
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import qualification as Q, reconcile as RC                                   # noqa: E402
from engine.source.cad import kernel, libredwg_map as L                                         # noqa: E402

DECODES = {"P7757": ROOT / "data/runs/cad_convert/P7757_ARCHITECTURAL.json",
           "QORTUBA": ROOT / "data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json"}
PASS_V = ("PASS",)


def k1(project):
    dec = json.loads(DECODES[project].read_text(encoding="utf-8", errors="replace"))
    doc = L.to_document(dec)
    return doc, kernel.realise(doc), L.insert_blocks(doc)


def magnitude(rg):
    m = 0.0
    for s in rg.segments:
        m = max(m, abs(s.a[0]), abs(s.a[1]), abs(s.b[0]), abs(s.b[1]))
    return m


def occ_key(row_key):
    h, path = row_key[0], row_key[1]
    return (f"D1:{h}", tuple(f"D1:{p}" for p in path))


def run(k2_pickle, project, scope_occurrences=None, region=None):
    doc, r1, ib1 = k1(project)
    blob = pickle.load(open(k2_pickle, "rb"))
    r2, ib2 = blob["rg"], blob["insert_blocks"]
    if region is not None:
        x0, y0, x1, y1 = region

        def inside(it):
            pts = it.get("pts") or [it.get("center")]
            return all(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in pts if p is not None)
        for rg in (r1, r2):
            rg.segments = [s for s in rg.segments if inside({"pts": [s.a, s.b]})]
            rg.arcs = [a for a in rg.arcs if inside({"center": a.center})]
            rg.circles = [c for c in rg.circles if inside({"center": c.center})]
            rg.elliptical_arcs = [e for e in rg.elliptical_arcs if inside({"center": e.center})]
    tol = RC.real_tolerance(magnitude(r1), 16)
    res = RC.reconcile(r1, r2, tol, insert_blocks_a=ib1, insert_blocks_b=ib2, name_a="D1/K1", name_b="DXF/K2")
    by_occ = defaultdict(list)
    for row in res["items"]:
        if row.get("field_class") == "BLOCK_LINEAGE":
            continue
        by_occ[occ_key(row["key"])].append(row["status"])
    verdict = {k: ("PASS" if all(s == "PASS" for s in v) else next(s for s in v if s != "PASS")) for k, v in by_occ.items()}
    lineage = {}
    for row in res["items"]:
        if row.get("field_class") == "BLOCK_LINEAGE":
            lineage[row.get("insert_a") or row.get("key", [None])[0]] = row.get("outcome")
    sigs = Q.capability_signatures(doc)
    scope = None if scope_occurrences is None else {(o, tuple(p)) for o, p in scope_occurrences}
    states, detail = {}, {}
    for sg, keys in sigs.items():
        keys = [(o, tuple(p)) for o, p in keys]
        if scope is not None:
            keys = [k for k in keys if k in scope]
            if not keys:
                continue
        if sg.startswith("REF="):
            vb = {k: ("PASS" if lineage.get(k[0][3:]) == RC.LINEAGE_PASS else lineage.get(k[0][3:], "NOT_COMPARED"))
                  for k in keys}
        else:
            vb = {k: verdict.get(k, "NOT_COMPARED") for k in keys}
        compared = sum(1 for k in keys if vb[k] != "NOT_COMPARED")
        st = (Q.NOT_EXERCISED if compared == 0 else
              Q.signature_states({sg: keys}, {k: v for k, v in vb.items()})[0][1])
        states[sg] = st
        detail[sg] = {"source_occurrences": len(keys), "compared": compared,
                      "pass": sum(1 for k in keys if vb[k] == "PASS"),
                      "nonpass_by_status": dict(Counter(v for v in vb.values() if v not in ("PASS",))),
                      "examples_nonpass": [[k[0], list(k[1]), vb[k]] for k in keys if vb[k] != "PASS"][:5]}
    summary = {k: res[k] for k in ("verdict", "field_class", "scope", "correlated_by", "correlation_bases",
                                   "lineage_bases", "lineage_outcomes", "tolerance", "counts", "non_pass_by_field")}
    return {"summary": summary, "signature_diagnostic_states": states, "signature_detail": detail,
            "items_nonpass_examples": [r for r in res["items"] if r["status"] != "PASS"][:40]}


def main(k2_pickle, project, out, proof=None, region=None):
    scope = None
    if proof:
        p = json.loads(Path(proof).read_text())
        scope = {(o, tuple(pth)) for r in p["rows"] for o, pth in r["source_occurrences"]}
    r = run(k2_pickle, project, scope, region)
    Path(out).write_text(json.dumps(r, indent=1, default=str))
    print(r["summary"]["verdict"], r["summary"]["counts"], r["summary"]["lineage_outcomes"])
    print(Counter(r["signature_diagnostic_states"].values()))
    return r


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], a[3], a[4] if len(a) > 4 else None)
