"""Split a submission set into DRAWINGS the engine may read and a SEALED part.

A municipality submission set is not homogeneous. Most of its sheets are
drawings — plans, elevations, sections — and the engine is meant to read
those. But a submission set also carries the architect's own AREA TAKE-OFF:
a table of floor areas with totals and percentages, drawn on the sheet.

That table is a KNOWN TOTAL. It is the same kind of object as a previous
BOQ, a contractor quantity or a manual qiyal, and the standing rule is that
none of those may reach the engine. Worse, on a second project it is the
ONLY independent check the project has of whether the engine measures a
real building — and a check that has been read is a check that is spent.

So the set is split before anything reads it:

    DRAWINGS   the pages the automatic pipeline is pointed at;
    SEALED     the take-off pages, written under a name that
               `engine.reference_mapping.refuse_if_sealed` refuses.

This tool performs the split and nothing else. It does not read a value off
either part, and it does not decide which pages are which — the page numbers
are supplied by the operator, from a visual index of the set.

    python3 -m tools.split_submission_set <pdf> <out_dir> \
        --sealed 0,1 --sealed-name P7757_area_takeoff_benchmark.pdf
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from engine.reference_mapping import SEALED


class SplitError(RuntimeError):
    """The split was asked to do something that would spend the benchmark."""


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def split(pdf: str, out_dir: str, *, sealed_pages, sealed_name: str,
          drawings_name: str) -> dict:
    """Write the two parts and return a record of what went where."""
    import pymupdf

    if sealed_name not in SEALED:
        raise SplitError(
            f"{sealed_name} is not in engine.reference_mapping.SEALED. A "
            "sealed part must be refused BY NAME, or the seal is a comment "
            "rather than a guard. Add the name there first")

    src_path = Path(pdf)
    src = pymupdf.open(src_path)
    total = src.page_count
    sealed_set = sorted({int(p) for p in sealed_pages})
    for p in sealed_set:
        if not 0 <= p < total:
            raise SplitError(f"page {p} is not in a {total}-page document")
    keep = [p for p in range(total) if p not in set(sealed_set)]
    if not keep:
        raise SplitError("every page was sealed. Nothing would be read")

    out = Path(out_dir)
    (out / "inputs").mkdir(parents=True, exist_ok=True)
    (out / "sealed").mkdir(parents=True, exist_ok=True)

    sealed_doc = pymupdf.open()
    for p in sealed_set:
        sealed_doc.insert_pdf(src, from_page=p, to_page=p)
    sealed_out = out / "sealed" / sealed_name
    sealed_doc.save(sealed_out)
    sealed_doc.close()

    draw_doc = pymupdf.open()
    for p in keep:
        draw_doc.insert_pdf(src, from_page=p, to_page=p)
    draw_out = out / "inputs" / drawings_name
    draw_doc.save(draw_out)
    draw_doc.close()
    src.close()

    rec = {
        "source_file": src_path.name,
        "source_sha256_16": _hash(src_path),
        "source_pages": total,
        "drawings_file": str(draw_out),
        "drawings_sha256_16": _hash(draw_out),
        "drawings_source_pages": keep,
        "sealed_file": str(sealed_out),
        "sealed_source_pages": sealed_set,
        "sealed_sha256_16": _hash(sealed_out),
        "why_sealed": (
            "these pages carry the architect's own area take-off — floor "
            "areas with totals and percentages. That is a KNOWN TOTAL, the "
            "same kind of object as a previous BOQ or a manual qiyal, and "
            "it is the only independent check this project has of whether "
            "the engine measured a real building. Reading it before the "
            "automatic result is frozen would spend it"),
        "no_value_was_read": True,
    }
    (out / "split_record.json").write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("out_dir")
    ap.add_argument("--sealed", required=True,
                    help="comma-separated 0-based page numbers to seal")
    ap.add_argument("--sealed-name", required=True)
    ap.add_argument("--drawings-name", required=True)
    a = ap.parse_args(argv)
    try:
        rec = split(a.pdf, a.out_dir,
                    sealed_pages=a.sealed.split(","),
                    sealed_name=a.sealed_name,
                    drawings_name=a.drawings_name)
    except Exception as exc:  # noqa: BLE001 - reported, not hidden
        print(f"REFUSED: {exc}")
        return 1
    print(json.dumps(rec, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
