"""T-201: the W2D (DWF 2D vector stream) reader on a hand-built synthetic stream: relative 16 / 32-bit coordinates,
the Units transform back to drawing units, texts, and refusal of unknown opcodes and truncated streams (never a
silent skip)."""
from __future__ import annotations

import io
import struct
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t201"))

import w2d_reader as W                                                 # noqa: E402

HDR = b"(W2D V06.00)(Units '' ((2 0 0 0)(0 2 0 0)(0 0 1 0)(100 200 0 1)))V(Comment 'a \\' quoted (paren')"


def _stream():
    s = bytearray(HDR)
    s += b"O" + struct.pack("<ii", 100, 200)                           # current point = drawing (0, 0)
    # a 1000 x 600 drawing-unit rectangle = 2000 x 1200 logical, 16-bit relative polyline of 5 points
    s += b"\x10\x05" + struct.pack("<10h", 0, 0, 2000, 0, 0, 1200, -2000, 0, 0, -1200)
    s += b"\x0c" + struct.pack("<4h", 0, 0, 2000, 1200)                # 16-bit line: diagonal
    s += b"l" + struct.pack("<4i", -2000, -1200, 40000, 0)             # 32-bit line
    s += b"\x92" + struct.pack("<iiIHH", 10, 10, 50, 0, 16384)         # circular arc
    s += b"e" + struct.pack("<iiIIHHH", 0, 0, 30, 20, 0, 65535, 0)     # ellipse
    s += b"\x06" + struct.pack("<H", 0x0021) + b"'Arial'" + struct.pack("<i", 212)   # font: name + height
    s += b"v" + b"x" + struct.pack("<ii", 4, 4) + b"'W 1'" + b"V"     # hidden searchable text
    s += b"\x18" + struct.pack("<ii", 2, 2) + b"'+1.00'" + b"\x01\x01" + struct.pack("<8i", 0, -37, 836, 0, 0, 213,
                                                                                       -836, 0) + b"\x01"
    s += b"{" + struct.pack("<i", 6) + struct.pack("<H", 12) + b"abc}"  # extended binary skipped by its size
    s += b"(EndOfDWF)"
    return bytes(s)


def test_units_and_geometry_back_to_drawing_units():
    p = W.parse_w2d(_stream())
    tr = p["units"]
    assert tr == (2.0, 2.0, 100.0, 200.0)
    rect = [W.to_model(q, tr) for q in p["polylines"][0]]
    assert rect == [(0.0, 0.0), (1000.0, 0.0), (1000.0, 600.0), (0.0, 600.0), (0.0, 0.0)]
    diag = [W.to_model(q, tr) for q in p["polylines"][1]]
    assert diag == [(0.0, 0.0), (1000.0, 600.0)]                        # relative to the running current point
    long = [W.to_model(q, tr) for q in p["polylines"][2]]
    assert long == [(0.0, 0.0), (20000.0, 0.0)]
    assert [a[0] for a in p["arcs"]] == ["ARC", "ELLIPSE"]
    texts = [(t[2], t[3]) for t in p["texts"]]
    assert texts == [("W 1", False), ("+1.00", True)]


def test_unknown_opcode_and_truncation_refused():
    with pytest.raises(W.W2DError, match="unknown opcode 0x99"):
        W.parse_w2d(HDR + b"\x99")
    with pytest.raises(W.W2DError, match="truncated"):
        W.parse_w2d(HDR + b"\x10\x05" + struct.pack("<3h", 0, 0, 1))


def test_dwf_package_reader(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("manifest.xml", "<x/>")
        z.writestr("sheet\\a.w2d", _stream())
    p = tmp_path / "t.dwf"
    p.write_bytes(b"(DWF V06.00)" + buf.getvalue())
    res = W.read_dwf_graphics(p)
    assert len(res) == 1 and len(res[0][1]["polylines"]) == 3
    bad = tmp_path / "bad.dwf"
    bad.write_bytes(b"PK..")
    with pytest.raises(W.W2DError):
        W.read_dwf_graphics(bad)
