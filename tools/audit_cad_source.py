"""Representation audit of an authored CAD source. No measurement.

The PDF sources for project 7757 are scans, so the engine had nothing to
read. A DWG is the other end of the range: not a picture of a drawing and
not a plot of one, but the authored model — units, layers, blocks, and
entities that know what they are.

That does not make it readable here, and the audit's job is to establish
which obstacle actually applies rather than to guess:

    THE CONTAINER    DWG is proprietary binary. Reading it needs a decoder,
                     and what a decoder cannot decode is INVISIBLE rather
                     than wrong;
    THE OBJECT MODEL a drawing authored in AutoCAD Architecture MAY store
                     walls, doors and windows as AEC custom objects, which a
                     reader without the object enabler sees only as proxies.
                     Whether it does is a QUESTION, answered by the class
                     table's instance counts — not by the presence of AEC
                     class names, which ACA registers in every drawing it
                     touches whether they are used or not.

On project 7757 that question came back negative: 244 AEC classes declared,
every one of them with ZERO instances and none an entity class. The walls
are plain lines. The distinction mattered enough to be worth measuring
instead of assuming.

The census itself lives in `engine.cad_source`, which documents the two
traps in the decode — a decoder artefact counted as geometry, and an
unnamed entity read as an unknown one.

What is deliberately not done here: no room measured, no area computed, no
scale asserted. Section B of the gate asks for scale ESTABLISHMENT, and
what this reports is the source's own declaration — $INSUNITS,
$MEASUREMENT, the limits and the extents — which is the evidence a scale
would be established from, not the scale.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from engine import cad_source as cad
from engine.reference_mapping import refuse_if_sealed

# How the decode went.
READ_OK = "CONVERTED_AND_READ"
NO_CONVERTER = "NO_DWG_CONVERTER_AVAILABLE"
CONVERT_FAILED = "CONVERTER_COULD_NOT_READ_THIS_FILE"

# Re-exported so callers and tests read one definition, not a second copy
# that can drift from it.
INSUNITS = cad.INSUNITS
MEASUREMENT = cad.MEASUREMENT


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


# Where the decoder may be named, in order. A build artefact under /tmp is
# deliberately NOT in this list: this container is ephemeral, and a default
# that silently works today and vanishes tomorrow makes a run
# irreproducible without saying so.
DECODER_ENV = "URBAN_DWG_DECODER"


def _find_converter(explicit: str = "") -> str:
    """The DWG decoder: named explicitly, in the environment, or on PATH."""
    import os
    import shutil

    for cand in (explicit, os.environ.get(DECODER_ENV, ""), "dwgread"):
        if cand and (shutil.which(cand) or Path(cand).is_file()):
            return cand
    return ""


def audit(dwg: str, *, work_dir: str, converter: str = "") -> dict:
    """Hash, decode, census. Nothing measured."""
    refuse_if_sealed(dwg)
    p = Path(dwg)
    rec = {
        "source_file": p.name,
        "source_sha256_16": _hash(p),
        "bytes": p.stat().st_size,
        "dwg_format_marker": p.read_bytes()[:6].decode("latin-1", "replace"),
        "contains_no_measurement": True,
    }
    conv = _find_converter(converter)
    if not conv:
        rec["conversion"] = {
            "status": NO_CONVERTER, "converter": "",
            "why": ("no DWG decoder on this machine. DWG is a proprietary "
                    "binary format; without a decoder NOTHING is known "
                    "about this drawing")}
        rec["representation"] = "NOT_ESTABLISHED"
        rec["why"] = (
            "the file could not be opened, so nothing below is known. This "
            "is NOT a finding that the drawing is empty")
        return rec

    out_json = str(Path(work_dir) / (p.stem + ".json"))
    try:
        rec["conversion"] = {"status": READ_OK, "converter": conv,
                             **cad.decode(dwg, converter=conv,
                                          out_json=out_json)}
    except (cad.CadReadError, subprocess.SubprocessError) as exc:
        rec["conversion"] = {"status": CONVERT_FAILED, "converter": conv,
                             "why": str(exc)}
        rec["representation"] = "NOT_ESTABLISHED"
        rec["why"] = (
            "the decoder failed, so nothing below is known. This is NOT a "
            "finding that the drawing is empty")
        return rec

    decoded = json.loads(Path(out_json).read_text(errors="replace"))
    cen = cad.census(decoded, source_file=p.name,
                     source_sha256_16=rec["source_sha256_16"], decoder=conv)
    rec["census"] = cen.record()
    rec["representation"] = "AUTHORED_CAD_VECTOR_GEOMETRY"
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dwg")
    ap.add_argument("--work-dir", default="data/runs/cad_convert")
    ap.add_argument("--converter", default="")
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    try:
        rec = audit(a.dwg, work_dir=a.work_dir, converter=a.converter)
    except Exception as exc:  # noqa: BLE001 - reported, not hidden
        print(f"REFUSED: {exc}")
        return 1
    text = json.dumps(rec, indent=2, ensure_ascii=False, default=str)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {a.json}")
    print(text[:7000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
