"""R8.2 §10 — attempt K2 on the real sources, and record exactly what happened.

Research lab only. For each project: is there a DWG? Can an independent DXF be
produced here? Does ezdxf load it? Nothing is repaired, patched or guessed: a
DXF that fails to load is reported with its hash and the loader's error.

K2_REAL_SOURCE_STATUS vocabulary:
    EXECUTED            K2 realised the real source
    NOT_EXECUTED        K2 could not run (reason recorded)
    SHARED_PARSER       the DXF came from the same parser lineage as D1 (LibreDWG)
    INDEPENDENT_PARSER  the DXF came from AutoCAD / ODA / another parser
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source.cad import kernel_ezdxf as K2          # noqa: E402

DWG2DXF = Path("/tmp/ldwg/programs/dwg2dxf")
SOURCES = {
    "P7757": {"dwg": "data/golden/7757/source_c/P7757_ARCHITECTURAL.dwg",
              "existing_dxf": "data/runs/cad_convert/P7757_ARCHITECTURAL.dxf"},
    "ALRASHED": {"dwg": None, "existing_dxf": None},
    "QORTUBA": {"dwg": None, "existing_dxf": None},
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest() if p and Path(p).exists() else None


def attempt(dxf_path, label, chain):
    doc, findings = K2.load(dxf_path)
    row = {"label": label, "dxf_sha256": sha(dxf_path), "dxf_bytes": Path(dxf_path).stat().st_size,
           "ends_with_EOF": Path(dxf_path).read_bytes().rstrip().endswith(b"EOF"), "conversion_chain": chain}
    if doc is None:
        row.update(loaded=False, error=findings[0].detail[:300])
        return row
    rg = K2.realise(doc)
    row.update(loaded=True, visits=rg.visits, dispositions=dict(rg.dispositions))
    return row


def main():
    out = {"tools": {"dwg2dxf": {"path": str(DWG2DXF), "present": DWG2DXF.exists(), "sha256": sha(DWG2DXF)}},
           "projects": {}}
    for proj, s in SOURCES.items():
        rec = {"dwg_present": bool(s["dwg"] and (ROOT / s["dwg"]).exists()), "dwg_sha256": sha(ROOT / s["dwg"]) if s["dwg"] else None,
               "attempts": []}
        if s["existing_dxf"] and (ROOT / s["existing_dxf"]).exists():
            rec["attempts"].append(attempt(ROOT / s["existing_dxf"], "existing data/runs DXF",
                                           ["DWG", "LibreDWG dwg2dxf 0.13.3 (producing flags unrecorded)"]))
        if rec["dwg_present"] and DWG2DXF.exists():
            with tempfile.TemporaryDirectory() as td:
                for flag in ("", "r2000", "r2004", "r2010"):
                    dst = Path(td) / f"out_{flag or 'default'}.dxf"
                    cmd = [str(DWG2DXF)] + (["--as", flag] if flag else []) + ["-y", "-o", str(dst), str(ROOT / s["dwg"])]
                    p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                    if dst.exists():
                        a = attempt(dst, f"dwg2dxf {flag or 'default'}", ["DWG", f"LibreDWG dwg2dxf 0.13.3 {flag or 'default'}"])
                        a["dwg2dxf_exit"] = p.returncode
                        a["dwg2dxf_error_lines"] = sum(1 for ln in p.stderr.splitlines() if ln.startswith("ERROR"))
                        rec["attempts"].append(a)
        loaded = [a for a in rec["attempts"] if a.get("loaded")]
        if loaded:
            rec["K2_REAL_SOURCE_STATUS"] = ["EXECUTED", "SHARED_PARSER"]
        else:
            rec["K2_REAL_SOURCE_STATUS"] = ["NOT_EXECUTED"]
            rec["reason"] = ("no DWG or DXF of this project exists in the environment (only a LibreDWG JSON decode)"
                             if not rec["dwg_present"] and not rec["attempts"] else
                             "every DXF available here (all LibreDWG-derived) is rejected by ezdxf 1.4.4; "
                             "an independent DXF (AutoCAD / ODA export) is required")
        rec["parser_independence"] = ("NOT_AVAILABLE: any DXF producible here comes from LibreDWG, the D1 parser"
                                      if rec["dwg_present"] else "NOT_AVAILABLE: no source")
        out["projects"][proj] = rec
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
