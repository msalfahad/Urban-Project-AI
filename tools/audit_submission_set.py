"""Per-page representation census of a multi-sheet source. No measurement.

`tools/freeze_new_source.py` audits ONE page, because project 23010 is one
sheet. A municipality submission set is ten or twelve, and "does this
document have vector content" is not a question with one answer per
document — a set can carry vector plans and scanned elevations, or the
reverse.

So every page is counted separately, and the census answers one question
per page:

    CAN THE CURRENT ENGINE READ THIS PAGE AT ALL?

which is decided by what the page is made of, not by what is drawn on it:

    VECTOR_LINEWORK   stroked/filled paths the vector reader can see;
    RASTER_IMAGE_ONLY a scan — the page is a photograph of a drawing, and
                      every vector stage downstream has nothing to read;
    EMPTY             neither.

Nothing here measures a room, extracts a dimension, or reads a value off a
table. It counts primitives.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from engine.reference_mapping import refuse_if_sealed

# What a page is made of, and what that means for the vector pipeline.
VECTOR_LINEWORK = "VECTOR_LINEWORK"
RASTER_IMAGE_ONLY = "RASTER_IMAGE_ONLY"
EMPTY = "NO_CONTENT"

READABLE = {
    VECTOR_LINEWORK: "the vector reader sees paths on this page",
    RASTER_IMAGE_ONLY: (
        "the vector reader sees NOTHING on this page. It is a photograph of "
        "a drawing. Every stage that consumes strokes — wall faces, bands, "
        "the material graph, the wall solid, the enclosure's supported "
        "lines — has an empty input, and an empty input is not a drawing "
        "with no walls"),
    EMPTY: "the page carries neither paths nor images",
}


def census(pdf: str) -> dict:
    """Count what each page is made of."""
    import pymupdf

    refuse_if_sealed(pdf)
    path = Path(pdf)
    doc = pymupdf.open(path)
    pages = []
    for i, pg in enumerate(doc):
        draws = pg.get_drawings()
        imgs = pg.get_images(full=True)
        text = pg.get_text("text")
        img_rows = []
        for entry in imgs:
            info = doc.extract_image(entry[0])
            img_rows.append({
                "xref": entry[0], "width_px": info["width"],
                "height_px": info["height"], "bpc": info["bpc"],
                "encoding": info["ext"],
                "effective_dpi_across_sheet": (
                    round(info["width"] / (pg.rect.width / 72.0), 1)
                    if pg.rect.width else None),
            })
        if draws:
            kind = VECTOR_LINEWORK
        elif imgs:
            kind = RASTER_IMAGE_ONLY
        else:
            kind = EMPTY
        pages.append({
            "page": i,
            "page_size_pt": [round(pg.rect.width, 1), round(pg.rect.height, 1)],
            "page_rotation": pg.rotation,
            "representation": kind,
            "what_that_means": READABLE[kind],
            "vector_paths": len(draws),
            "text_characters": len(text),
            "text_objects_present": bool(text.strip()),
            "images": img_rows,
        })

    kinds = {}
    for row in pages:
        kinds[row["representation"]] = kinds.get(row["representation"], 0) + 1
    return {
        "source_file": path.name,
        "source_sha256_16": hashlib.sha256(
            path.read_bytes()).hexdigest()[:16],
        "page_count": doc.page_count,
        "producer": doc.metadata.get("producer", ""),
        "creator": doc.metadata.get("creator", ""),
        "pages_by_representation": kinds,
        "document_carries_any_vector_linework": (
            kinds.get(VECTOR_LINEWORK, 0) > 0),
        "document_carries_any_text_object": any(
            r["text_objects_present"] for r in pages),
        "pages": pages,
        "contains_no_measurement": True,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    try:
        rec = census(a.pdf)
    except Exception as exc:  # noqa: BLE001 - reported, not hidden
        print(f"REFUSED: {exc}")
        return 1
    text = json.dumps(rec, indent=2)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {a.json}")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
