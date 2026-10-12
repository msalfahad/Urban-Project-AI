"""DWG ADAPTER (M9 S3) - a DWG becomes the DXF the pipeline reads, through an external converter run as a separate
program: never linked into Urban, never an MCP server, never a network service.

    converters()                    the converters found on this machine, each with its identity and pin status
    convert(dwg, out_dir)           -> the conversion record (below); the DXF lands in out_dir
    loss_report(dxf_path)           the converted drawing's entity census, with what the pipeline cannot read in it

Converters, in order of preference:
    LIBREDWG_DWG2DXF   `dwg2dxf` of GNU LibreDWG (GPL-3.0; run as a separate program, so Urban is not a derivative)
    ODA                the ODA File Converter (freeware, proprietary licence) through ezdxf.addons.odafc
A converter's executable is hashed and checked against engine.source.decoder_pins: REGISTERED, or UNREGISTERED_BUILD
(the run is recorded as such and may not support FINAL provenance).

The conversion record: {state CONVERTED | BLOCKED, converter, converter_path, converter_sha256, pin_status, dwg,
dwg_sha256, dwg_version (from the file header), dxf, dxf_sha256, stdout_tail, stderr_tail, losses, remedy}. Losses are
counted, never silently dropped: proxy entities (graphics only), custom-class objects, entity kinds the K2 kernel leaves
UNHANDLED, and the converter's own warnings. No converter -> state BLOCKED with the remedy; the route stops on it and
never reads an empty drawing.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import decoder_pins as PINS            # noqa: E402

POLICY_ID = "DWG_ADAPTER_V1"
# the AutoCAD release that wrote a DWG, from the six-byte version string at the start of the file
DWG_VERSIONS = {"AC1009": "R11/R12", "AC1012": "R13", "AC1014": "R14", "AC1015": "R2000", "AC1018": "R2004",
                "AC1021": "R2007", "AC1024": "R2010", "AC1027": "R2013", "AC1032": "R2018"}
REMEDY = ("no DWG converter on this machine: install GNU LibreDWG (`dwg2dxf`, GPL-3.0, free software) or the ODA File "
          "Converter (free download, proprietary licence), or export the drawing to DXF from the CAD program; then "
          "run again (the DXF is read directly)")
# what the K2 kernel / the architectural reader do not turn into geometry
NOT_GEOMETRY = {"ACAD_PROXY_ENTITY": "proxy entity (graphics only)", "OLE2FRAME": "embedded OLE object",
                "RTEXT": "reactive text (no text value in DXF)", "WIPEOUT": "masking frame",
                "ACAD_TABLE": "table object", "MESH": "3D mesh", "3DSOLID": "ACIS solid", "REGION": "ACIS region",
                "BODY": "ACIS body", "SURFACE": "ACIS surface"}


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dwg_version(path):
    head = Path(path).read_bytes()[:6].decode("ascii", "replace")
    return {"code": head, "release": DWG_VERSIONS.get(head, "UNKNOWN")}


def converters():
    out = []
    exe = shutil.which("dwg2dxf")
    if exe:
        sha = _sha(exe)
        out.append({"converter": "LIBREDWG_DWG2DXF", "path": exe, "sha256": sha,
                    "pin_status": PINS.status("LIBREDWG_DWG2DXF", sha)})
    try:
        from ezdxf.addons import odafc
        if odafc.is_installed():
            exe = shutil.which("ODAFileConverter") or "ODAFileConverter"
            sha = _sha(exe) if Path(exe).exists() else None
            out.append({"converter": "ODA", "path": exe, "sha256": sha, "pin_status": PINS.status("ODA", sha)})
    except Exception:                                              # noqa: BLE001 - ezdxf without the add-on
        pass
    return out


def loss_report(dxf_path):
    import ezdxf
    doc = ezdxf.readfile(str(dxf_path))
    types = Counter()
    for layout in [doc.modelspace()] + [b for b in doc.blocks if not b.name.startswith("*")]:
        for e in layout:
            types[e.dxftype()] += 1
    losses = [{"type": t, "count": n, "why": NOT_GEOMETRY[t]} for t, n in sorted(types.items()) if t in NOT_GEOMETRY]
    return {"entity_types": dict(sorted(types.items())), "losses": losses,
            "dxf_version": doc.dxfversion, "insunits": doc.header.get("$INSUNITS")}


def convert(dwg, out_dir, *, prefer=None):
    dwg = Path(dwg)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = {"policy": POLICY_ID, "dwg": dwg.name, "dwg_sha256": _sha(dwg), "dwg_version": dwg_version(dwg)}
    found = converters()
    if prefer:
        found = [c for c in found if c["converter"] == prefer] or found
    if not found:
        return dict(rec, state="BLOCKED", converter=None, remedy=REMEDY, losses=[])
    c = found[0]
    dxf = out_dir / (dwg.stem + ".dxf")
    if c["converter"] == "LIBREDWG_DWG2DXF":
        p = subprocess.run([c["path"], "-y", "-o", str(dxf), str(dwg)], capture_output=True, text=True, timeout=600)
        out, err, code = p.stdout, p.stderr, p.returncode
    else:
        from ezdxf.addons import odafc
        try:
            odafc.convert(str(dwg), str(dxf), version="R2018", replace=True)
            out, err, code = "", "", 0
        except Exception as ex:                                    # noqa: BLE001 - the converter's own failure
            out, err, code = "", str(ex), 1
    rec.update(converter=c["converter"], converter_path=c["path"], converter_sha256=c["sha256"],
               pin_status=c["pin_status"], returncode=code, stdout_tail=out.splitlines()[-20:],
               stderr_tail=err.splitlines()[-20:],
               converter_warnings=sum(1 for ln in (out + "\n" + err).splitlines() if "warn" in ln.lower()))
    if code != 0 or not dxf.exists() or dxf.stat().st_size == 0:
        return dict(rec, state="BLOCKED", remedy=f"the converter failed (exit {code}): see stderr_tail; " + REMEDY,
                    losses=[])
    lr = loss_report(dxf)
    return dict(rec, state="CONVERTED", dxf=str(dxf), dxf_sha256=_sha(dxf), converted_dxf_version=lr["dxf_version"],
                entity_types=lr["entity_types"], losses=lr["losses"], remedy=None)


def policy_record():
    return {"policy_id": POLICY_ID, "converters": ["LIBREDWG_DWG2DXF", "ODA"], "remedy": REMEDY,
            "never": ["a converter linked into Urban or run as a service", "an empty drawing read after a failed "
                      "conversion", "a lost entity kind left uncounted"]}
