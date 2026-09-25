"""Freeze and source-audit a NEW project's drawing. No measurement.

    A SOURCE AUDIT MAY RUN ON PROJECT 2 NOW. A MEASUREMENT MAY NOT.

The reason for running this before anything else is that the second project
is the only thing that can tell us whether the engine reads DRAWINGS or
reads THIS drawing. Every tolerance, every pen weight, every assumption
about how a wall is represented was chosen against one sheet, and a second
sheet is where those choices either survive or are exposed.

What this tool does, and nothing more:

    HASH the file and record it, so the audit is attached to an exact
    revision and a later re-run can prove the source did not move;
    COUNT what the sheet is made of — paths, segments, curves, stroke
    weights, how walls appear to be drawn;
    STATE whether the current engine can read that representation at all.

What it refuses to do:

    measure a room, produce an area, produce a length, produce a quantity;
    open any benchmark, any qiyal, any previous BOQ or contractor quantity;
    tune anything on project 23010 using what it finds here.

That last refusal is the important one. Project 2's value is destroyed the
moment its answers are used to adjust the project it is meant to test.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from engine.reference_mapping import refuse_if_sealed
from engine.source_audit import audit_drawing

OUT = Path("data/runs/source_audits")

# What this tool will not touch, whatever it is pointed at.
REFUSED_INPUTS = ("site_benchmark", "qiyal", "boq", "contractor",
                  "quotation", "cost", "rate", "price")


class IntakeError(RuntimeError):
    """A new source was asked to do something a new source may not do."""


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def freeze(pdf: str, *, project_id: str, drawing_id: str,
           revision: str) -> dict:
    """Hash, audit, and record. Returns the audit; writes it beside the run.

    The hash comes FIRST and is part of the record, because an audit of a
    file that has since changed is not an audit of anything.
    """
    path = Path(pdf)
    refuse_if_sealed(str(path))
    low = path.name.lower()
    for bad in REFUSED_INPUTS:
        if bad in low:
            raise IntakeError(
                f"{path.name} looks like a {bad} document. This tool reads "
                "DRAWINGS. A benchmark, a qiyal sheet, a previous BOQ or any "
                "contractor quantity must never reach the engine, and "
                "certainly not through an intake path")
    if not path.exists():
        raise IntakeError(
            f"{path} does not exist. The second project cannot be frozen "
            "until the drawing is supplied — and until it is, nothing here "
            "says anything about whether the engine generalises")

    from engine.vector_source import read

    src_hash = _hash(path)
    drawing = read(path)
    audit = audit_drawing(drawing, drawing_id=drawing_id, revision=revision,
                          source_hash=src_hash)
    rec = {
        "project_id": project_id,
        "drawing_id": drawing_id,
        "drawing_revision": revision,
        "source_file": path.name,
        "source_sha256_16": src_hash,
        "frozen": True,
        "audit": audit.record(),
        "what_this_is": (
            "a representation audit of a frozen source. It counts what the "
            "sheet is made of and states whether the current engine can "
            "read that representation. It contains no measurement of any "
            "room and no quantity of any kind"),
        "what_may_not_be_done_with_it": (
            "project 23010's tolerances, pen weights and representation "
            "assumptions must NOT be adjusted using what this audit finds. "
            "The second project is the only test of whether those choices "
            "generalise, and tuning against it destroys the test"),
        "measurement_status": "NOT_ATTEMPTED_AND_NOT_PERMITTED_HERE",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{project_id}_{drawing_id}_{revision}.json"
    out.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    rec["written_to"] = str(out)
    return rec


def main(argv=None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if len(args) != 4:
        print(__doc__)
        print("usage: freeze_new_source.py <pdf> <project_id> <drawing_id> "
              "<revision>")
        return 2
    try:
        rec = freeze(args[0], project_id=args[1], drawing_id=args[2],
                     revision=args[3])
    except (IntakeError, Exception) as exc:  # noqa: BLE001 - reported, not hidden
        print(f"REFUSED: {exc}")
        return 1
    print(json.dumps({k: v for k, v in rec.items() if k != "audit"},
                     indent=2))
    print(json.dumps(rec["audit"], indent=2)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
