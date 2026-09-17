"""Record one pass of a blind visual run, and freeze what it decided.

    python -m tools.a18_record_pass --run-dir data/runs/7757/blind/A18-GF-001 \
        --sandbox <the isolated directory the pass could see> \
        --pass-id PASS_A --report <the pass's own report, verbatim> \
        --decided '{"selected_page": 1}' --out <record>.json

A pass reads images and writes a report. What it looked at is as much of
the record as what it concluded: the crops it cut are inputs that reached
it, so they are offered through the contract like everything else and
land in the run's manifest with the basis that decided each box.

The report is stored VERBATIM and hashed. Nothing here rewrites, grades
or summarises it — a first-run result is only worth having if it is the
result that actually came back.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from engine import blind_input_contract as bic
from engine import export_provenance as prov

PAGE = re.compile(r"-(\d{2})")


def register_crops(run: bic.BlindRun, sandbox, run_dir) -> list:
    """Every crop the pass cut, copied into the record and gated."""
    src = Path(sandbox) / "crops"
    if not src.is_dir():
        return []
    dst = Path(run_dir) / "crops"
    dst.mkdir(parents=True, exist_ok=True)
    out = []
    for crop in sorted(src.iterdir()):
        if not crop.is_file():
            continue
        shutil.copy2(crop, dst / crop.name)
        hit = PAGE.search(crop.stem)
        page = hit.group(1) if hit else ""
        out.append(run.offer(bic.Input(
            input_id=crop.stem.upper(), kind=bic.LOCAL_CROP,
            what_it_is=f"a crop the pass cut from page {page or '?'}",
            path=str(dst / crop.name),
            derived_from=f"IMG-{page}" if page else "UNRECORDED",
            crop_basis=bic.CROP_REQUESTED_BY_THE_AGENT,
            supplied_by="THE_PASS_ITSELF")))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--sandbox", required=True)
    ap.add_argument("--pass-id", required=True)
    ap.add_argument("--run-id", default="")
    ap.add_argument("--report", required=True)
    ap.add_argument("--decided", default="{}")
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)

    run_dir = Path(a.run_dir)
    run = bic.BlindRun(run_id=a.run_id or run_dir.name, pass_id="A18")
    crops = register_crops(run, a.sandbox, run_dir)

    report = Path(a.report)
    decided = json.loads(a.decided)
    record = {
        "MODEL": bic.MODEL,
        "run_id": run.run_id,
        "pass_id": a.pass_id,
        "phase": run.phase,
        "status": run.status,
        "decided": decided,
        "SELECTION_HASH": prov.canonical_sha256(decided),
        "frozen": bool(a.freeze),
        "report": {
            "file": report.name,
            "stored": "VERBATIM",
            **{k: v for k, v in prov.file_hashes(report).items()
               if k in (prov.RAW, "bytes")},
        },
        "crops_the_pass_cut": {
            "count": len(crops),
            "admitted": sum(1 for c in crops if c.admitted),
            "refused": [c.record() for c in crops if not c.admitted],
            "basis": bic.CROP_REQUESTED_BY_THE_AGENT,
            "rows": [c.record() for c in crops],
        },
        "why_the_crops_are_here": (
            "a crop is an input that reached the pass. What it looked at "
            "is as much of the record as what it concluded"),
    }
    record["PASS_RECORD_HASH"] = prov.canonical_sha256(record)

    out = Path(a.out or run_dir / f"{run.run_id}_{a.pass_id}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False,
                              default=str) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out), "pass_id": a.pass_id,
                      "decided": decided,
                      "SELECTION_HASH": record["SELECTION_HASH"][:16],
                      "frozen": record["frozen"],
                      "crops": record["crops_the_pass_cut"]["count"],
                      "crops_admitted":
                          record["crops_the_pass_cut"]["admitted"],
                      "PASS_RECORD_HASH":
                          record["PASS_RECORD_HASH"][:16]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
