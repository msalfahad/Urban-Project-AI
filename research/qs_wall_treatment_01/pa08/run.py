"""PA08 real entry point: independent blind validation of ONE villa never used to develop the engine.

    python -m research.qs_wall_treatment_01.pa08.run --alias ALIAS --arch decode.json|plan.dxf --pdf plan.pdf [--struct file ...] --truth TRUTH_PACK.json [--registry registry.json]

It refuses to run without an ACCEPTED source package and a valid, sealed truth pack; it never reads P7757, 23010,
benchmarks or workbooks; it freezes the blind output before the truth is opened.  The result is a geometry / topology
truth comparison; a quantity is never validated here.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research.qs_wall_treatment_01.pa08 import blind_run as BR, compare as CMP, config as C8, gate_v4 as G4, protocol as P8, source_acceptance as SA, truth_pack as TP


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--alias", required=True); ap.add_argument("--arch", required=True); ap.add_argument("--pdf", required=True); ap.add_argument("--struct", nargs="*", default=[])
    ap.add_argument("--truth", required=True); ap.add_argument("--registry", default=None); ap.add_argument("--declared-exposure", default=None)
    a = ap.parse_args(argv)
    C8.OUT8.mkdir(parents=True, exist_ok=True)
    P8.write_all()
    files = [a.arch, a.pdf] + list(a.struct)
    fam = {a.arch: "ARCHITECTURAL", a.pdf: "ARCHITECTURAL", **{s: "STRUCTURAL" for s in a.struct}}
    acc = SA.accept(a.alias, files, fam, a.declared_exposure)
    (C8.OUT8 / "PA08_SOURCE_ACCEPTANCE.json").write_text(json.dumps(acc, indent=1), "utf-8")
    if acc["INDEPENDENT_VALIDATION_STATUS"] != "ACCEPTED":
        print(json.dumps({"STATUS": "REFUSED", "WHY": acc["INDEPENDENT_VALIDATION_STATUS"], "EXPOSURE": acc["KNOWN_PRIOR_EXPOSURE"]}, indent=1))
        return 2
    seal = TP.seal(a.truth)
    registry = json.loads(Path(a.registry).read_text("utf-8")) if a.registry else {"_REGISTRY_ID": "PA08_NO_OWNER_REGISTRY", "NORMAL_INTERNAL_PLASTER_HEIGHT": {"VALUE": None, "SOURCE_TYPE": "UNKNOWN"}}
    cfg = BR.config_for(acc, registry)
    blind = BR.launch(cfg, [f["PATH"] for f in acc["FILES"] if f["EXISTS"] and f["KIND"] != "FORBIDDEN_SPREADSHEET"])
    (C8.OUT8 / "PA08_BLIND_RESULT.json").write_text(json.dumps(blind, indent=1), "utf-8")
    if blind["STATUS"] != "COMPLETED":
        print(json.dumps({"STATUS": blind["STATUS"], "VIOLATIONS": blind["VIOLATIONS"], "STDERR_TAIL": blind["STDERR_TAIL"]}, indent=1))
        return 3
    truth = json.loads((C8.SEALED_DIR / "TRUTH_PACK.json").read_text("utf-8"))
    result = CMP.compare(C8.BLIND_DIR, truth, blind["FREEZE"])
    (C8.OUT8 / "PA08_INDEPENDENT_VALIDATION_RESULT.json").write_text(json.dumps(result, indent=1), "utf-8")
    regs = {n: json.loads((C8.BLIND_DIR / f"{n}.json").read_text("utf-8")) for n in ("PA07_QUANTITY_SAFETY_REGISTER", "PA07_PHYSICAL_SPACE_REGISTER", "PA06_SOURCE_UNIT_REGISTER") if (C8.BLIND_DIR / f"{n}.json").exists()}
    review_p = C8.OUT / "pa07r1" / "PA07R1_COLD_REVIEW.json"
    review = json.loads(review_p.read_text("utf-8")) if review_p.exists() else None
    gate = G4.evaluate(review=review, validation=result, acceptance=acc, blind=blind, truth_seal=seal, leakage=None, blind_registers=regs, dry_run=False)
    (C8.OUT8 / "PA08_PROJECT_3_GATE_V4.json").write_text(json.dumps(gate, indent=1), "utf-8")
    print(json.dumps({"STATUS": "EXECUTED", "SILENT_WRONG_QUANTITY_COUNT": result["METRICS"]["SILENT_WRONG_QUANTITY_COUNT"], "CLASS_COUNTS": result["CLASS_COUNTS"], "READINESS": gate["READINESS"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
