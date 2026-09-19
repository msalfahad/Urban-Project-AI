"""§14. Search the architectural source set for what a plan cannot say.

    python -m tools.scan_vertical_evidence \
        --cad data/runs/cad_convert/P7757_ARCHITECTURAL.json \
        --dwf <package>.dwf --pdf <sheet>.pdf --out vertical_evidence.json

Three representations of ONE design, in the order of what the engine can
do with them:

    DESIGN_CAD   the decoded drawing. Its texts have coordinates, so a
                 level mark in it is PLACED: a region, and a floor;
    DESIGN_PDF   a published sheet. Where it carries real text, that
                 text has a page position — placed on the sheet, which
                 is not yet placed in the building;
    DESIGN_DWF   the published package. Its W2D streams are vector, and
                 this project has no W2D reader, so strings pulled out
                 of them are LEADS: the set says it carries the answer,
                 and this tool may not say what the answer is.

Nothing here measures anything and nothing here assumes a rise.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from engine import vertical_evidence as ve
from engine.reference_mapping import refuse_if_sealed

DESIGN_CAD = "DESIGN_CAD"
DESIGN_DWF = "DESIGN_DWF"
DESIGN_PDF = "DESIGN_PDF"

# A W2D stream writes its strings in single quotes. Pulling them out is
# not reading the format: it is reading the ASCII that happens to be in
# it, which is why everything from here is UNPLACED.
W2D_STRING = re.compile(rb"'([ -~]{1,60})'")

# §11 (6E-A). Each W2D text is preceded by the two bytes `vx` and two
# 32-bit integers. They are the position — and W2D writes positions as
# DELTAS from the running point, so the pair beside a level mark is not
# where it is on the sheet. Reading it as absolute would place a level
# a few millimetres from the origin and attribute it to whatever region
# sits there, which is worse than not placing it at all.
W2D_TEXT_OPCODE = re.compile(rb"vx(.{4})(.{4})'([ -~]{1,60})'", re.S)
DELTA_ENCODED = "THE_W2D_TEXT_POSITIONS_ARE_DELTA_ENCODED"


def w2d_text_positions(path, limit: int = 40) -> list:
    """What the stream says about WHERE its texts are, and how far that
    gets: an opcode, two integers, and no running point to add them to.
    """
    raw = Path(path).read_bytes()
    at = raw.find(b"PK\x03\x04")
    if at < 0:
        return []
    zf = zipfile.ZipFile(io.BytesIO(raw[at:]))
    out = []
    for name in zf.namelist():
        if not name.lower().endswith(".w2d"):
            continue
        data = zf.read(name)
        for m in W2D_TEXT_OPCODE.finditer(data):
            dx = int.from_bytes(m.group(1), "little", signed=True)
            dy = int.from_bytes(m.group(2), "little", signed=True)
            out.append({"text": m.group(3).decode("ascii", "replace"),
                        "delta_x": dx, "delta_y": dy,
                        "status": DELTA_ENCODED})
            if len(out) >= limit:
                return out
    return out


@dataclass
class _Text:
    text: str
    x: float = 0.0
    y: float = 0.0
    region_id: str = ""
    floor_level: str = ""


def from_cad(path: str, *, region_of=None, floor_of=None) -> list:
    """The decoded drawing's own texts, with their coordinates."""
    refuse_if_sealed(path)
    from engine import cad_adapter as adapter

    nd = adapter.normalize(json.loads(Path(path).read_text()),
                           source_file=Path(path).name, source_hash="SCAN")
    texts = []
    for t in nd.texts:
        x, y = float(getattr(t, "x", 0.0)), float(getattr(t, "y", 0.0))
        body = getattr(t, "value", None) or getattr(t, "text", "") or ""
        texts.append(_Text(body, x, y,
                           region_id=(region_of(x, y) if region_of else ""),
                           floor_level=(floor_of(x, y) if floor_of else "")))
    return ve.scan(texts, source=Path(path).name,
                   representation=DESIGN_CAD, placed=True)


def from_dwf(path: str, start: int = 1) -> list:
    """Strings inside the package's W2D streams. LEADS, never measures."""
    refuse_if_sealed(path)
    raw = Path(path).read_bytes()
    at = raw.find(b"PK\x03\x04")
    if at < 0:
        return []
    zf = zipfile.ZipFile(io.BytesIO(raw[at:]))
    seen, out = set(), []
    for name in zf.namelist():
        if not name.lower().endswith(".w2d"):
            continue
        for m in W2D_STRING.findall(zf.read(name)):
            s = m.decode("ascii", "replace").strip()
            if s and s not in seen:
                seen.add(s)
                out.append(s)
    return ve.scan(out, source=Path(path).name,
                   representation=DESIGN_DWF, placed=False, start=start)


def from_pdf(path: str, start: int = 1) -> list:
    """A published sheet's text, where the sheet carries any."""
    refuse_if_sealed(path)
    try:
        import pymupdf
    except ImportError:      # noqa: BLE001
        return []
    doc = pymupdf.open(path)
    texts = []
    for page in doc:
        for line in page.get_text().splitlines():
            if line.strip():
                texts.append(_Text(line.strip()))
    # A SHEET POSITION IS NOT A BUILDING POSITION. Text on a published
    # page is placed on the page, and this tool cannot put the page in
    # the building, so these are leads like the DWF's.
    return ve.scan(texts, source=Path(path).name,
                   representation=DESIGN_PDF, placed=False, start=start)


def placement_attempts(cad: str, dwf: str = "", pdfs=()) -> list:
    """§11. What was actually tried to PLACE the evidence, and what each
    attempt established. An absence of placement is reported as one, and
    never as an absence of evidence.
    """
    out = []
    if cad:
        out.append({
            "attempt": "THE_DECODED_DWG",
            "representation": DESIGN_CAD,
            "what_it_established": (
                "its texts carry coordinates, so a level mark in it is "
                "placed. The decode carries %%p0.00 and +0.15 only, and "
                "neither is attributable to a floor-to-floor pair"),
            "blocked_by": "",
        })
    for p in pdfs or ():
        if not Path(p).exists():
            continue
        pages, rasters, vectors, chars = 0, 0, 0, 0
        try:
            import pymupdf

            doc = pymupdf.open(p)
            for page in doc:
                pages += 1
                rasters += len(page.get_images())
                vectors += len(page.get_drawings())
                chars += len(page.get_text())
        except Exception as exc:      # noqa: BLE001
            out.append({"attempt": "THE_PUBLISHED_PDF",
                        "representation": DESIGN_PDF, "file": Path(p).name,
                        "what_it_established": "",
                        "blocked_by": f"{type(exc).__name__}"})
            continue
        out.append({
            "attempt": "THE_PUBLISHED_PDF",
            "representation": DESIGN_PDF,
            "file": Path(p).name,
            "what_it_established": (
                f"{pages} pages, {rasters} raster images, {vectors} "
                f"vector drawings, {chars} characters of text"),
            "blocked_by": ("" if (vectors or chars) else
                           "every page is a single scanned image: no "
                           "vector geometry and no text. Placing a level "
                           "from it would need OCR, which this project "
                           "does not use"),
        })
    if dwf and Path(dwf).exists():
        found = w2d_text_positions(dwf)
        out.append({
            "attempt": "THE_DWF_W2D_STREAM",
            "representation": DESIGN_DWF,
            "file": Path(dwf).name,
            "what_it_established": (
                f"{len(found)} texts carry a position opcode: two bytes "
                "'vx' and two 32-bit integers before the string"),
            "blocked_by": (
                "the integers are DELTAS from the stream's running "
                "point, not absolute coordinates. Accumulating them "
                "needs a W2D opcode reader, which this project does "
                "not have. Reading them as absolute would place a "
                "level a few millimetres from the origin and attribute "
                "it to whatever sits there"),
            "sample": found[:5],
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cad")
    ap.add_argument("--dwf", action="append", default=[])
    ap.add_argument("--pdf", action="append", default=[])
    ap.add_argument("--floors", default="",
                    help="the two floors a stair connects, comma separated")
    ap.add_argument("--risers", type=int, default=0)
    ap.add_argument("--out")
    a = ap.parse_args()

    found = []
    if a.cad:
        found += from_cad(a.cad)
    for p in a.dwf:
        found += from_dwf(p, start=len(found) + 1)
    for p in a.pdf:
        found += from_pdf(p, start=len(found) + 1)
    out = ve.assess(
        found,
        floors_needed=[f for f in a.floors.split(",") if f],
        risers=(a.risers or None),
        attempts=placement_attempts(a.cad, a.dwf[0] if a.dwf else "",
                                    a.pdf))
    out["sources"] = ([{"path": a.cad, "representation": DESIGN_CAD}]
                      if a.cad else [])
    out["sources"] += [{"path": p, "representation": DESIGN_DWF}
                       for p in a.dwf]
    out["sources"] += [{"path": p, "representation": DESIGN_PDF}
                       for p in a.pdf]
    text = json.dumps(out, indent=2, ensure_ascii=False, sort_keys=True)
    if a.out:
        Path(a.out).write_text(text + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "findings"},
                     indent=2, ensure_ascii=False)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
