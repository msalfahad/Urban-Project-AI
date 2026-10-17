"""R8.6A real DXFs, read only through the hash-addressed store (data/inputs/by_sha256/<sha256>.dxf). A missing
input skips with its reason; bytes that do not hash to the declared name fail. The files are scanned read-only
and must still show what the committed intake register records."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((Path(__file__).parent / "FIXTURE_MANIFEST.json").read_text())
INTAKE = json.loads((Path(__file__).parent / "registers/DXF_INTAKE_REGISTER.json").read_text())["files"]


def _input(key):
    want = MANIFEST["inputs"][key]
    p = ROOT / MANIFEST["store"] / f"{want['sha256']}.dxf"
    if not p.exists():
        pytest.skip(f"hash-addressed input not present in this checkout: {p.relative_to(ROOT)}")
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    assert h.hexdigest() == want["sha256"] and p.stat().st_size == want["bytes"], f"INPUT DRIFT: {p.name}"
    return p


@pytest.fixture(scope="module")
def scan():
    sys.path.insert(0, str(ROOT / "research/external_engine_lab"))
    import r8_6a_intake as I
    return I.scan


@pytest.mark.parametrize("key,name", [("P7757_DXF", "P7757"), ("ST7757_DXF", "ST7757"), ("QORTUBA_DXF", "QORTUBA")])
def test_the_file_still_says_what_the_register_records(scan, key, name):
    s = scan(_input(key))
    rec = INTAKE[name]
    assert s["header"] == rec["header"]
    assert s["acadmaintver_group_code"] == rec["acadmaintver_group_code"] == 90
    assert s["sections"] == rec["sections"] and "ACDSDATA" in s["sections"]
    assert s["census"] == rec["census"] and s["handles"] == rec["handles"]
    assert s["handles"]["collisions"] == 0


def test_p7757_keeps_0x929_as_arc_dimension():
    p = _input("P7757_DXF")
    seen, code = None, None
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        it = iter(f)
        for c in it:
            v = next(it).rstrip("\r\n")
            c = c.strip()
            if c == "0":
                code = v
            elif c == "5" and v.upper() == "929":
                seen = code
                break
    assert seen == "ARC_DIMENSION"
