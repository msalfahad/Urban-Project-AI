"""Structural audit of a DWF package. Representation only, no geometry read.

A DWF is a ZIP with a twelve-byte version header in front of it. Inside sit
a manifest, per-sheet descriptors, and the drawing itself as one or more
**W2D** streams — Autodesk's binary 2D vector format.

What this establishes, and all it establishes:

    IS THERE VECTOR GEOMETRY IN HERE AT ALL   — a W2D stream is linework,
                                                not a picture of linework;
    WHAT DOES THE PUBLISHER SAY THE UNITS ARE — the ePlot descriptor states
                                                the paper size and unit, and
                                                each graphic resource carries
                                                a transform into that unit;
    WHAT WAS IT PUBLISHED FROM                — the source DWG, the
                                                application, the layout.

What it does NOT do, deliberately:

    decode a W2D stream, extract a single line, derive a scale, or measure
    anything. This project has no W2D reader. Saying "there is vector
    geometry here" is a fact about the container; saying what that geometry
    IS would require the reader, and the reader is not this tool.

The transform matters more than it looks. The engine's current pixel scale
is a printed dimension off PROJECT 1, hardcoded. A DWF states its own
paper unit and its own transform, which is the beginning of a scale
derived from the source rather than inherited from another building — but
it is paper millimetres, and the step from paper to building still needs
the plot scale. That step is not taken here.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

from engine.reference_mapping import refuse_if_sealed

W2D_MIME = "application/x-w2d"

HAS_VECTOR = "PACKAGE_CARRIES_W2D_VECTOR_STREAMS"
NO_VECTOR = "PACKAGE_CARRIES_NO_VECTOR_STREAM"
NOT_A_DWF = "NOT_A_DWF_PACKAGE"

MEANS = {
    HAS_VECTOR: (
        "the drawing is present as linework, not as a picture of linework. "
        "Reading it needs a W2D reader, which this project does not have"),
    NO_VECTOR: (
        "no W2D stream. Whatever this package carries, it is not vector "
        "geometry"),
    NOT_A_DWF: "the file does not open as a DWF package",
}


def _attrs(xml: str, tag: str) -> list:
    out = []
    for m in re.finditer(r"<" + re.escape(tag) + r"\b([^>]*)/?>", xml):
        out.append(dict(re.findall(r'(\w+)="([^"]*)"', m.group(1))))
    return out


def audit(path: str) -> dict:
    """Open the container, count what is in it, quote what it declares."""
    refuse_if_sealed(path)
    p = Path(path)
    raw = p.read_bytes()
    rec = {
        "source_file": p.name,
        "source_sha256_16": hashlib.sha256(raw).hexdigest()[:16],
        "bytes": len(raw),
        "header": raw[:12].decode("latin-1", "replace"),
        "contains_no_measurement": True,
    }
    body = raw[12:] if raw[:5] == b"(DWF " else raw
    try:
        z = zipfile.ZipFile(io.BytesIO(body))
    except Exception:
        rec["verdict"] = NOT_A_DWF
        rec["what_that_means"] = MEANS[NOT_A_DWF]
        return rec

    entries = []
    for name in z.namelist():
        info = z.getinfo(name)
        head = z.read(name)[:16]
        entries.append({
            "name": name,
            "stored_bytes": info.compress_size,
            "uncompressed_bytes": info.file_size,
            "leading_bytes": head.decode("latin-1", "replace"),
            "is_w2d_stream": head.startswith("(W2D".encode()),
        })
    rec["entries"] = entries
    w2d = [e for e in entries if e["is_w2d_stream"]]
    rec["w2d_stream_count"] = len(w2d)
    rec["w2d_uncompressed_bytes_total"] = sum(
        e["uncompressed_bytes"] for e in w2d)
    rec["verdict"] = HAS_VECTOR if w2d else NO_VECTOR
    rec["what_that_means"] = MEANS[rec["verdict"]]

    if "manifest.xml" in z.namelist():
        man = z.read("manifest.xml").decode("utf-8", "replace")
        rec["published_from"] = sorted({
            a.get("href", "") for a in _attrs(man, "dwf:Source")})
        rec["publisher_provider"] = sorted({
            a.get("provider", "") for a in _attrs(man, "dwf:Source")})
        rec["toolkit"] = next(
            (a.get("value", "") for a in _attrs(man, "dwf:Property")
             if a.get("name") == "DWFToolkitVersion"), "")
        rec["sheets"] = [
            {"name": a.get("name", ""), "title": a.get("title", ""),
             "type": a.get("type", "")}
            for a in _attrs(man, "dwf:Section")
            if a.get("type", "").endswith("ePlot")]

    desc = [n for n in z.namelist()
            if n.endswith("descriptor.xml") and "ePlot_" in n]
    pages = []
    for n in desc:
        xml = z.read(n).decode("utf-8", "replace")
        paper = (_attrs(xml, "ePlot:Paper") or [{}])[0]
        props = {a.get("name", ""): a.get("value", "")
                 for a in _attrs(xml, "ePlot:Property") if a.get("value")}
        pages.append({
            "page_name": (_attrs(xml, "ePlot:Page") or [{}])[0].get("name", ""),
            "paper_units": paper.get("units", ""),
            "paper_width": paper.get("width", ""),
            "paper_height": paper.get("height", ""),
            "paper_clip": paper.get("clip", ""),
            "authoring_application": props.get("Creator", ""),
            "source_dwg": props.get("File Name", ""),
            "layout": props.get("Layout Name", ""),
            "graphic_resources": [
                {"role": a.get("role", ""), "bytes": a.get("size", ""),
                 "transform": a.get("transform", "")}
                for a in _attrs(xml, "ePlot:GraphicResource")],
        })
    rec["pages"] = pages
    rec["what_is_still_missing_to_measure"] = (
        "a W2D reader, and the step from PAPER millimetres — which the "
        "descriptor states — to BUILDING millimetres, which it does not. "
        "The paper transform is not a building scale")
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dwf")
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    try:
        rec = audit(a.dwf)
    except Exception as exc:  # noqa: BLE001 - reported, not hidden
        print(f"REFUSED: {exc}")
        return 1
    text = json.dumps(rec, indent=2, ensure_ascii=False)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {a.json}")
    print(json.dumps({k: v for k, v in rec.items() if k != "entries"},
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
