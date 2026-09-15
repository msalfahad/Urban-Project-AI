"""Representation audit of an authored CAD source. No measurement.

The PDF sources for project 7757 are scans, so the engine had nothing to
read. A DWG is the other end of the range: it is not a picture of a drawing
and not a plot of one — it is the authored model, with units, layers,
blocks, and entities that know what they are.

That does not make it readable. Two things stand between a DWG and this
engine, and this tool's job is to establish which of them apply:

    THE CONTAINER      DWG is a proprietary binary format. Reading it here
                       needs a converter, and what the converter cannot
                       decode is invisible rather than wrong;
    THE OBJECT MODEL    a drawing authored in AutoCAD Architecture stores
                       walls, doors and windows as AEC CUSTOM OBJECTS. A
                       reader without the object enabler sees a PROXY: the
                       cached plot graphics if the file carries them, and
                       nothing at all if it does not.

So the audit counts what a generic reader can actually see, and reports the
proxy population SEPARATELY and by name. A drawing whose walls are all
proxies is not a drawing with no walls — that is invariant 43 in a new
costume, and the distinction is the whole point of the count.

What is deliberately not done here: no room is measured, no area computed,
no scale asserted. Section B of the gate asks for scale ESTABLISHMENT, and
what this reports is the source's own declaration ($INSUNITS,
$MEASUREMENT, extents) — the evidence a scale would be established from,
not the scale.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from engine.reference_mapping import refuse_if_sealed

# What the container turned out to be.
READ_OK = "CONVERTED_AND_READ"
NO_CONVERTER = "NO_DWG_CONVERTER_AVAILABLE"
CONVERT_FAILED = "CONVERTER_COULD_NOT_READ_THIS_FILE"

# AutoCAD's own name for "an object I do not have the code for".
PROXY_TYPES = ("ACAD_PROXY_ENTITY", "ACAD_PROXY_OBJECT", "PROXY")

# $INSUNITS, as AutoCAD defines it. 0 is the dangerous one: it means the
# drawing declares no unit at all, which is NOT a declaration of millimetres.
INSUNITS = {
    0: "UNITLESS — the drawing declares NO unit. This is not a declaration "
       "of millimetres and must not be read as one",
    1: "inches", 2: "feet", 3: "miles", 4: "millimetres", 5: "centimetres",
    6: "metres", 7: "kilometres", 8: "microinches", 9: "mils", 10: "yards",
    11: "angstroms", 12: "nanometres", 13: "microns", 14: "decimetres",
    15: "decametres", 16: "hectometres", 17: "gigametres", 18: "astronomical",
    19: "light years", 20: "parsecs",
}
MEASUREMENT = {0: "imperial (ANSI) linetype/hatch tables",
               1: "metric (ISO) linetype/hatch tables"}

# Header variables worth quoting. Everything here is a DECLARATION by the
# author, which is evidence and not a measurement.
WANTED_VARS = ("$INSUNITS", "$MEASUREMENT", "$LUNITS", "$LUPREC", "$AUNITS",
               "$EXTMIN", "$EXTMAX", "$LIMMIN", "$LIMMAX", "$DIMSCALE",
               "$LTSCALE", "$TILEMODE", "$ACADVER", "$HANDSEED",
               "$PDSIZE", "$CELTSCALE", "$DIMLUNIT", "$DIMALT")


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _find_converter(explicit: str = "") -> str:
    import shutil

    for cand in ([explicit] if explicit else []) + [
            "dwg2dxf", "dwgread",
            "/tmp/ldwg/programs/dwg2dxf", "/tmp/ldwg/programs/dwgread"]:
        if cand and (shutil.which(cand) or Path(cand).is_file()):
            return cand
    return ""


def to_dxf(dwg: str, out: str, *, converter: str = "") -> dict:
    """Convert DWG to DXF with whatever converter this machine has."""
    conv = _find_converter(converter)
    if not conv:
        return {"status": NO_CONVERTER, "converter": "",
                "why": ("no DWG converter on this machine. DWG is a "
                        "proprietary binary format; the engine reads DXF and "
                        "vector PDF")}
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    cmd = ([conv, "-o", out, dwg] if "dwg2dxf" in conv
           else [conv, "-O", "DXF", "-o", out, dwg])
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        return {"status": CONVERT_FAILED, "converter": conv,
                "why": "conversion timed out"}
    ok = Path(out).exists() and Path(out).stat().st_size > 0
    return {
        "status": READ_OK if ok else CONVERT_FAILED,
        "converter": conv,
        "command": " ".join(cmd),
        "exit_code": res.returncode,
        "stderr_tail": (res.stderr or "")[-1500:],
        "dxf_bytes": Path(out).stat().st_size if ok else 0,
        "dxf_sha256_16": _hash(Path(out)) if ok else "",
    }


def _entity_rows(layout, space: str) -> list:
    rows = []
    for e in layout:
        t = e.dxftype()
        rows.append({
            "space": space, "type": t,
            "layer": str(getattr(e.dxf, "layer", "")),
            "is_proxy": t in PROXY_TYPES,
        })
    return rows


def audit(dwg: str, *, work_dir: str, converter: str = "") -> dict:
    """Hash, convert, read, count. Nothing measured."""
    refuse_if_sealed(dwg)
    p = Path(dwg)
    rec = {
        "source_file": p.name,
        "source_sha256_16": _hash(p),
        "bytes": p.stat().st_size,
        "dwg_format_marker": p.read_bytes()[:6].decode("latin-1", "replace"),
        "contains_no_measurement": True,
    }
    dxf = str(Path(work_dir) / (p.stem + ".dxf"))
    rec["conversion"] = to_dxf(dwg, dxf, converter=converter)
    if rec["conversion"]["status"] != READ_OK:
        rec["representation"] = "NOT_ESTABLISHED"
        rec["why"] = (
            "the file could not be opened, so nothing below is known. This "
            "is NOT a finding that the drawing is empty")
        return rec

    import ezdxf

    doc = ezdxf.readfile(dxf)
    hdr = {}
    for v in WANTED_VARS:
        try:
            hdr[v] = doc.header[v]
        except Exception:  # noqa: BLE001 - absence is the answer
            hdr[v] = None
    rec["header_variables_as_declared"] = {
        k: (list(v) if isinstance(v, tuple) else v) for k, v in hdr.items()}
    ins = hdr.get("$INSUNITS")
    rec["declared_units"] = {
        "insunits_code": ins,
        "insunits_means": INSUNITS.get(ins, "unrecognised code"),
        "measurement_code": hdr.get("$MEASUREMENT"),
        "measurement_means": MEASUREMENT.get(hdr.get("$MEASUREMENT"),
                                             "unrecognised code"),
        "this_is": ("the author's DECLARATION of the drawing unit. It is "
                    "strong evidence and it is not a measurement"),
    }

    rows = _entity_rows(doc.modelspace(), "MODEL")
    layouts = []
    for name in doc.layout_names():
        if name == "Model":
            continue
        layouts.append(name)
        rows.extend(_entity_rows(doc.layout(name), f"PAPER:{name}"))
    rec["layouts"] = {"model_space_entities": sum(
        1 for r in rows if r["space"] == "MODEL"),
        "paper_space_layouts": layouts,
        "paper_space_entities": sum(
            1 for r in rows if r["space"].startswith("PAPER"))}

    by_type = Counter(r["type"] for r in rows)
    rec["entities_by_type"] = dict(by_type.most_common())
    rec["entity_total"] = len(rows)

    proxies = [r for r in rows if r["is_proxy"]]
    rec["proxy_population"] = {
        "count": len(proxies),
        "by_type": dict(Counter(r["type"] for r in proxies)),
        "share_of_all_entities_pct": (
            round(100.0 * len(proxies) / len(rows), 2) if rows else None),
        "what_a_proxy_is": (
            "an object whose defining code is not present. Its geometry is "
            "available only as cached plot graphics, if the file carries "
            "them. A wall stored as a proxy is NOT a wall this engine can "
            "measure, and it is NOT an absent wall either"),
    }

    rec["layers"] = {
        "count": len(doc.layers),
        "names": sorted(lay.dxf.name for lay in doc.layers),
        "entities_per_layer": dict(
            Counter(r["layer"] for r in rows).most_common(40)),
    }
    rec["blocks"] = {
        "count": sum(1 for b in doc.blocks
                     if not b.name.startswith(("*", "$"))),
        "names_sample": sorted(
            b.name for b in doc.blocks
            if not b.name.startswith(("*", "$")))[:60],
        "insert_count": by_type.get("INSERT", 0),
    }
    rec["annotation"] = {
        "TEXT": by_type.get("TEXT", 0), "MTEXT": by_type.get("MTEXT", 0),
        "ATTDEF": by_type.get("ATTDEF", 0),
        "LEADER": by_type.get("LEADER", 0) + by_type.get("MULTILEADER", 0),
    }
    rec["dimensions"] = {
        "DIMENSION": by_type.get("DIMENSION", 0),
        "styles": sorted(s.dxf.name for s in doc.dimstyles),
    }
    rec["line_representations"] = {
        k: by_type.get(k, 0) for k in
        ("LINE", "LWPOLYLINE", "POLYLINE", "ARC", "CIRCLE", "ELLIPSE",
         "SPLINE", "HATCH", "SOLID", "3DFACE", "REGION")}
    rec["what_is_not_established_here"] = (
        "any scale in building millimetres, any room, any area, any length. "
        "The declarations above are the EVIDENCE a scale would be "
        "established from")
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
    print(text[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
