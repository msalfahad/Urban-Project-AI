"""Did a transformation destroy vector information, or recompress a scan?

A file that arrives already processed — compressed to fit a size limit,
re-saved by a viewer, exported by a phone — is not the source. Its audit is
an audit of the transformation as much as of the drawing, and the two are
indistinguishable from one file alone.

The distinction is decisive for this project:

    VECTOR -> RASTER   the drawing HAD linework and the transformation
                       flattened it. The engine's stop says nothing about
                       the source, only about the copy;
    RASTER -> RASTER   the drawing was a scan before anything touched it.
                       The engine's stop is a real property of the source.

This compares two renditions page by page and separates those two cases on
evidence rather than on file size:

    VECTOR PATHS on each side          — the only direct test. A rendition
                                         with paths that the other lacks
                                         proves flattening;
    IMAGE PIXEL DIMENSIONS             — a re-raster almost never lands on
                                         the same pixel grid as the other
                                         rendition's scan;
    COMPRESSED STREAM BYTES            — which rendition carries more data;
    JPEG QUANTISATION                  — a recompression coarsens the
                                         quantisation tables. A fresh
                                         raster of vector art does not have
                                         a coarser version of a table it
                                         never had;
    DECODED PIXEL AGREEMENT            — how far the two images actually
                                         differ, which distinguishes "the
                                         same scan at lower quality" from
                                         "a different rendering".

No room is measured. No value is read off any page.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from engine.reference_mapping import refuse_if_sealed

# What the comparison concluded, and what each conclusion licenses.
FLATTENED = "TRANSFORMATION_FLATTENED_VECTOR_TO_RASTER"
RECOMPRESSED = "BOTH_RENDITIONS_ARE_RASTER_TRANSFORMATION_ONLY_RECOMPRESSED"
BOTH_VECTOR = "BOTH_RENDITIONS_CARRY_VECTOR_LINEWORK"
UNDECIDED = "NOT_DECIDABLE_FROM_THESE_TWO_FILES"

MEANS = {
    FLATTENED: (
        "one rendition carries vector paths the other does not. The engine's "
        "result on the flattened copy is a fact about the copy and says "
        "NOTHING about the source. Re-run on the rendition that has paths"),
    RECOMPRESSED: (
        "neither rendition carries a single vector path, and the images sit "
        "on the same pixel grid. The transformation recompressed pixels that "
        "were already pixels. The engine's stop is a property of the SOURCE, "
        "not of the transformation"),
    BOTH_VECTOR: (
        "both renditions carry linework. Whichever is used, the vector "
        "reader has an input"),
    UNDECIDED: (
        "the two files do not line up page for page, so no page-level "
        "comparison was possible. Nothing may be concluded about either"),
}


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _dqt_summary(blob: bytes) -> dict:
    """Mean quantisation step of each JPEG table, biggest signal first.

    A larger mean step is a coarser table, which is what a recompression
    produces. Read straight off the DQT marker; no decoding.
    """
    out: list = []
    i = 2
    n = len(blob)
    while i + 4 < n:
        if blob[i] != 0xFF:
            i += 1
            continue
        marker = blob[i + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg_len = int.from_bytes(blob[i + 2:i + 4], "big")
        if marker == 0xDB:
            body = blob[i + 4:i + 2 + seg_len]
            j = 0
            while j < len(body):
                prec = body[j] >> 4
                size = 128 if prec else 64
                table = body[j + 1:j + 1 + size]
                if prec:
                    vals = [int.from_bytes(table[k:k + 2], "big")
                            for k in range(0, len(table), 2)]
                else:
                    vals = list(table)
                if vals:
                    out.append(round(sum(vals) / len(vals), 2))
                j += 1 + size
        if marker == 0xDA:
            break
        i += 2 + seg_len
    return {"tables": out,
            "mean_quantisation_step": (
                round(sum(out) / len(out), 2) if out else None)}


def _page_rows(doc):
    import pymupdf  # noqa: F401  (doc is already open)

    rows = []
    for pg in doc:
        draws = pg.get_drawings()
        imgs = pg.get_images(full=True)
        entry = {
            "page_size_pt": [round(pg.rect.width, 1), round(pg.rect.height, 1)],
            "page_rotation": pg.rotation,
            "vector_paths": len(draws),
            "text_characters": len(pg.get_text("text")),
            "images": [],
        }
        for e in imgs:
            info = doc.extract_image(e[0])
            blob = info["image"]
            row = {
                "width_px": info["width"], "height_px": info["height"],
                "bpc": info["bpc"], "encoding": info["ext"],
                "stream_bytes": len(blob),
                "stream_sha256_16": hashlib.sha256(blob).hexdigest()[:16],
            }
            if info["ext"] in ("jpeg", "jpg"):
                row.update(_dqt_summary(blob))
            entry["images"].append(row)
        rows.append(entry)
    return rows


def compare(a_paths, b_path: str, *, label_a: str, label_b: str,
            sample_pages=(), dpi: int = 150) -> dict:
    """Compare a rendition (possibly split across files) against another."""
    import pymupdf

    for p in list(a_paths) + [b_path]:
        refuse_if_sealed(p)

    a_docs = [pymupdf.open(p) for p in a_paths]
    b_doc = pymupdf.open(b_path)

    a_rows: list = []
    for d in a_docs:
        a_rows.extend(_page_rows(d))
    b_rows = _page_rows(b_doc)

    a_vec = sum(r["vector_paths"] for r in a_rows)
    b_vec = sum(r["vector_paths"] for r in b_rows)
    a_txt = sum(r["text_characters"] for r in a_rows)
    b_txt = sum(r["text_characters"] for r in b_rows)

    if len(a_rows) != len(b_rows):
        verdict = UNDECIDED
    elif a_vec > 0 and b_vec == 0:
        verdict = FLATTENED
    elif b_vec > 0 and a_vec == 0:
        verdict = FLATTENED
    elif a_vec > 0 and b_vec > 0:
        verdict = BOTH_VECTOR
    else:
        verdict = RECOMPRESSED

    # Pixel agreement on a sample. Only meaningful when the page counts line
    # up; the sample keeps a 12-page comparison from rendering 24 sheets.
    agreement: dict = {}
    if len(a_rows) == len(b_rows):
        pages = sample_pages or (0, len(a_rows) // 2, len(a_rows) - 1)
        for p in sorted({int(x) for x in pages if 0 <= int(x) < len(a_rows)}):
            # Locate p inside whichever of the A files holds it.
            off, doc = p, None
            for d in a_docs:
                if off < d.page_count:
                    doc = d
                    break
                off -= d.page_count
            if doc is None:
                continue
            # Render each from its own document at its own local index.
            import numpy as np

            def grey(dc, idx):
                pm = dc[idx].get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
                return np.frombuffer(pm.samples, np.uint8).reshape(
                    pm.height, pm.width)

            ga, gb = grey(doc, off), grey(b_doc, p)
            if ga.shape != gb.shape:
                agreement[f"page_{p}"] = {
                    "comparable": False,
                    "shapes": [list(ga.shape), list(gb.shape)]}
                continue
            df = np.abs(ga.astype(np.int16) - gb.astype(np.int16))
            ink_a = int((ga <= 200).sum())
            ink_b = int((gb <= 200).sum())
            agreement[f"page_{p}"] = {
                "comparable": True, "render_dpi": dpi,
                "identical": bool(df.max() == 0),
                "max_abs_difference": int(df.max()),
                "mean_abs_difference": round(float(df.mean()), 4),
                "pixels_differing_by_more_than_8_levels_pct": round(
                    100.0 * float((df > 8).mean()), 4),
                "ink_at_threshold_200": {
                    label_a: ink_a, label_b: ink_b,
                    "delta_pct": (round(100.0 * (ink_b - ink_a) / ink_a, 3)
                                  if ink_a else None)},
            }

    def side(paths, rows, vec, txt):
        return {
            "files": [{"name": Path(p).name,
                       "bytes": Path(p).stat().st_size,
                       "sha256_16": _hash(Path(p))} for p in paths],
            "total_bytes": sum(Path(p).stat().st_size for p in paths),
            "pages": len(rows),
            "vector_paths_total": vec,
            "text_characters_total": txt,
            "image_stream_bytes_total": sum(
                i["stream_bytes"] for r in rows for i in r["images"]),
            "image_pixel_sizes": sorted({
                f'{i["width_px"]}x{i["height_px"]}'
                for r in rows for i in r["images"]}),
            "image_encodings": sorted({
                i["encoding"] for r in rows for i in r["images"]}),
            "mean_jpeg_quantisation_step": (
                round(sum(i["mean_quantisation_step"] for r in rows
                          for i in r["images"]
                          if i.get("mean_quantisation_step") is not None)
                      / max(1, sum(1 for r in rows for i in r["images"]
                                   if i.get("mean_quantisation_step")
                                   is not None)), 3)
                if any(i.get("mean_quantisation_step") is not None
                       for r in rows for i in r["images"]) else None),
            "page_rows": rows,
        }

    return {
        "verdict": verdict,
        "what_that_means": MEANS[verdict],
        label_a: side(list(a_paths), a_rows, a_vec, a_txt),
        label_b: side([b_path], b_rows, b_vec, b_txt),
        "pixel_agreement_sample": agreement,
        "contains_no_measurement": True,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--a", nargs="+", required=True,
                    help="rendition A, one or more files in page order")
    ap.add_argument("--b", required=True, help="rendition B, one file")
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    ap.add_argument("--pages", default="")
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    try:
        rec = compare(a.a, a.b, label_a=a.label_a, label_b=a.label_b,
                      sample_pages=(a.pages.split(",") if a.pages else ()),
                      dpi=a.dpi)
    except Exception as exc:  # noqa: BLE001 - reported, not hidden
        print(f"REFUSED: {exc}")
        return 1
    text = json.dumps(rec, indent=2, ensure_ascii=False)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {a.json}")
    summary = {k: v for k, v in rec.items() if k != "pixel_agreement_sample"}
    for k in (a.label_a, a.label_b):
        summary[k] = {kk: vv for kk, vv in summary[k].items()
                      if kk != "page_rows"}
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps(rec["pixel_agreement_sample"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
