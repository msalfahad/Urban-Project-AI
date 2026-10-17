"""R8.14 BLIND Qortuba run of the FROZEN WALL_BAND_POLICY_V5.

    python3 research/external_engine_lab/r8_14_blind.py <work> <out.json>

Inputs: the canonical inputs of both revisions, the R8.10 TS01 claims already accepted (7116-7119 walls, the two xref
occurrences) and the frozen engine. NOT given: any owner physical, finish or method fact (passage, floor footprint,
3.20 m, thresholds, soffit, skirting), any expected H2430 / H2431 status, row value or historical total. This module
imports no owner-fact, trade or row code. The record is written once and committed before any comparison.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_10_claims as CL                                                                     # noqa: E402
import r8_10_qortuba as Q10                                                                   # noqa: E402
import r8_8_topology as LAB                                                                   # noqa: E402
from engine.source import topology_closures as TC, wall_bands as WB                           # noqa: E402

FREEZE = ROOT / "tests/r8_14/registers/R8_14_V5_FREEZE.json"
WATCH = ("470", "471", "477", "2296", "2297", "2430", "2431", "1316", "718")
DEFECTS = ("574", "584", "2060", "2061", "552", "1672", "459", "551", "817", "549", "550", "545")   # the R8.12 findings


def handle(k):
    return Q10.handle(k)


def run(inp, name, facts, pc, xc):
    u = CL.attach_xref_facts(LAB.UNREALISED[name], facts)
    r = LAB.run(inp, u, part_claims=pc, xref_claims=xc, closure_policy=TC.POLICY_ID)
    r["_unit2"] = (inp.unit_native_to_mm ** 2) / 1e6
    return r


def touches(rec_sources, watch=WATCH):
    return bool({handle(s) for s in rec_sources} & set(watch))


def summary(r, inp):
    u = inp.unit_native_to_mm
    wb = r["wall_bands"]
    bands = []
    for b in wb["bands"]:
        bands.append({"band_id": b["band_id"], "state": b["state"], "faces": [handle(f) for f in b["faces"]],
                      "width_mm": round(b["width"] * u, 2),
                      "interval": [round(v, 4) for v in b["interval"]],
                      "intervals": [dict(iv, by=[handle(x) for x in iv["by"]]) for iv in b["evidence"]["intervals"]],
                      "ends": [{"end": e["end"], "kind": e["kind"], "faces": [handle(x) for x in e.get("faces", [])],
                                "caps": [{"source": handle(c["source"]), "role": c["role"], "grade": c["grade"],
                                          "gap_mm": [round(c["gap_to_face_a_end"] * u, 2),
                                                     round(c["gap_to_face_b_end"] * u, 2)]}
                                         for c in e.get("drawn_caps", [])]} for e in b["ends"]],
                      "spans": b["spans"]})
    spans = {s["span_id"]: s for s in wb["spans"]}
    closures = [{"closure_id": c["closure_id"], "band_id": c["band_id"], "release": c["release"],
                 "geometry": [round(v, 4) for v in c["geometry"]],
                 "evidence": [handle(x) for x in c["source_evidence_ids"]],
                 "material": c["physical_material"],
                 "safety": {"label_partition_unchanged": c["safety"].get("label_partition_unchanged"),
                            "area_balance_ok": c["safety"].get("area_balance_ok"), "passes": c["safety"].get("passes"),
                            "separated_pieces": [{"area_m2": round(p["area"] * r["_unit2"], 4),
                                                  "pure_band_interior": p["pure_band_interior"],
                                                  "boundary": [x if x.startswith(TC.PREFIX) else handle(x)
                                                               for x in p["boundary"]]}
                                                 for p in c["safety"].get("separated_pieces", [])]}}
                for c in r["topology_closures"]["closures"]]
    hall = next((s for s in r["sites"] if any("HALL" in v for v in LAB.stamps(s).values())), None)
    watched = [b for b in bands if touches(b["faces"])]
    return {
        "counts": {"chains": len(wb["chains"]), "assemblies": len(bands),
                   "established": sum(1 for b in bands if b["state"] == WB.ESTABLISHED),
                   "spans": len(wb["spans"]), "closures": len(closures),
                   "authorised": sum(1 for c in closures if c["release"] == TC.AUTHORISED_FOR_SHADOW),
                   "passages": len(r["passages"])},
        "watched_bands": [dict(b, span_records=[{"span_id": sid, "s": [round(v, 4) for v in spans[sid]["s"]],
                                                 "source_intervals": [dict(x, source=handle(x["source"]))
                                                                      for x in spans[sid]["source_intervals"]]}
                                                for sid in b["spans"]]) for b in watched],
        "watched_chains": [{"chain_id": c["chain_id"], "fragments": [handle(f["source"]) for f in c["fragments"]],
                            "nodes": [dict(n, between=[handle(x) for x in n.get("between", [])],
                                           by=handle(n["by"]) if n.get("by") else None) for n in c["nodes"]]}
                           for c in wb["chains"] if touches([f["source"] for f in c["fragments"]])],
        "closures": closures,
        "passages": [{"passage_id": p["passage_id"], "band_id": p["band_id"], "end_kind": p["end_kind"],
                      "target": handle(p["target"]) if "|H" in p["target"] else p["target"],
                      "width_mm": round(p["width_mm"], 2), "thickness_mm": round(p["thickness_mm"], 1),
                      "strip_in_site": p["strip_in_site"]} for p in r["passages"]],
        "hall": None if hall is None else {"site": hall["site_id"], "area_m2": round(hall["area_m2"], 4),
                                           "issues": hall["issues"]},
        "labelled_sites": sorted([[round(s["area_m2"], 4), sorted({v for vs in LAB.stamps(s).values() for v in vs})]
                                  for s in r["sites"] if s["labels"]], key=lambda z: -z[0]),
        "run_input_digest": r["run_manifest"]["RUN_INPUT_DIGEST"],
        "v4": {"chain_id_collisions": wb["chain_id_collisions"],
               "chains_line_disambiguated": sorted([handle(f["source"]) + "|" + f["source"].rsplit("|", 1)[1]
                                                    for f in c["fragments"]] for c in wb["chains"]
                                                   if c["identity_basis"] == WB.IDENTITY_LINE),
               "band_ids_unique": len({b["band_id"] for b in wb["bands"]}) == len(wb["bands"]),
               "chain_ids_unique": len({c["chain_id"] for c in wb["chains"]}) == len(wb["chains"]),
               "support_counts": {st: sum(1 for b in wb["bands"]
                                          if b["evidence"]["structural_support"]["state"] == st)
                                  for st in (WB.SELF_SUPPORTED, WB.INHERITED_SUPPORT)},
               "inherited": [{"band_id": b["band_id"], "faces": [handle(f) for f in b["faces"]],
                              "across": [handle(x) for x in b["evidence"]["structural_support"].get("across", [])]}
                             for b in wb["bands"] if b["evidence"]["structural_support"]["state"] == WB.INHERITED_SUPPORT],
               "unsupported_runs": len(wb["unsupported_runs"]),
               "boundary_cases": [dict(u, chain_a=[handle(f["source"]) for c in wb["chains"] if c["chain_id"] == u["chain_a"]
                                                  for f in c["fragments"]],
                                       chain_b=[handle(f["source"]) for c in wb["chains"] if c["chain_id"] == u["chain_b"]
                                                for f in c["fragments"]])
                                  for u in wb["unsupported_runs"] if u.get("reason") == WB.BOUNDARY_CASE],
               "geometric_candidates": [{"band_id": b["band_id"], "faces": [handle(f) for f in b["faces"]],
                                         "width_mm": round(b["width"] * u, 2),
                                         "authority": b["evidence"]["physical_authority"]}
                                        for b in wb["bands"] if b["state"] == WB.GEOMETRIC_CANDIDATE],
               "isolated_loops": [handle(x["entity"] + "|0") for x in wb["isolated_loops"]],
               "physical_authority_entities": [handle(x + "|0") for x in wb["physical_authority_entities"]],
               "unsupported_touching_r8_12_findings": [
                   dict(u, chain_a=[handle(f["source"]) for c in wb["chains"] if c["chain_id"] == u["chain_a"]
                                    for f in c["fragments"]],
                        chain_b=[handle(f["source"]) for c in wb["chains"] if c["chain_id"] == u["chain_b"]
                                 for f in c["fragments"]])
                   for u in wb["unsupported_runs"]
                   if {handle(f["source"]) for c in wb["chains"] if c["chain_id"] in (u["chain_a"], u["chain_b"])
                       for f in c["fragments"]} & set(DEFECTS)],
               "bands_touching_r8_12_findings": [b for b in bands if touches(b["faces"], DEFECTS)]}}


def main(work, out):
    freeze = json.loads(FREEZE.read_text())
    assert WB.POLICY_ID == freeze["wall_band_policy"]["id"] == "WALL_BAND_POLICY_V5", "policy id is not the frozen one"
    assert WB.policy_record()["digest"] == freeze["wall_band_policy"]["digest"], "policy digest is not the frozen one"
    for f, h in freeze["engine_file_sha256"].items():
        assert hashlib.sha256((ROOT / f).read_bytes()).hexdigest() == h, f"engine file changed after the freeze: {f}"
    inps, _, facts = Q10.inputs(work)
    pc, xc, _ = CL.load()
    rec = {"SCHEMA": "URBAN_R8_14_BLIND_QORTUBA_V5_RESULT_V1", "freeze": freeze["frozen_commit"],
           "wall_band_policy": freeze["wall_band_policy"], "blind": {
               "owner_fact_used": False, "floor_fact_used": False, "finish_fact_used": False,
               "expected_h2430_given": False, "expected_q14_given": False, "historical_totals_given": False,
               "inputs": ["canonical inputs (both revisions)", "R8.10 TS01 claims (7116-7119, xref occurrences)",
                          "the frozen engine"]},
           "NEW_K2": summary(run(inps["NEW_K2"], "NEW_K2", facts, pc, xc), inps["NEW_K2"]),
           "OLD_K1": summary(run(inps["OLD_K1"], "OLD_K1", facts, pc, xc), inps["OLD_K1"])}
    Path(out).write_text(json.dumps(rec, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: rec[k]["counts"] for k in ("NEW_K2", "OLD_K1")}))


if __name__ == "__main__":
    main(*sys.argv[1:3])
