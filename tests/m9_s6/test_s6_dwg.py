"""M9 S6 Phase 1 - DWG admission with a FAKE converter (a script named dwg2dxf on PATH; never a real converter):
strict conversion (ARCH_TAKEOFF_V2 and --strict-admission) names the output after the DWG's hash, removes a stale
output before converting, and blocks an unreadable or entity-less result; the V1 conversion (strict=False) keeps
its M9 S3 behaviour."""

from __future__ import annotations

import os
import sys

import pytest

ezdxf = pytest.importorskip("ezdxf")

from tools import dwg_adapter as DA                     # noqa: E402

FAKE = """#!{py}
import shutil, sys
args = sys.argv[1:]
out, src = args[args.index("-o") + 1], args[-1]
lines = open(src, encoding="ascii", errors="replace").read().splitlines()
mode = lines[1].strip() if len(lines) > 1 else "SILENT"
if mode == "COPY":
    shutil.copyfile(lines[2].strip(), out)
elif mode == "GARBAGE":
    open(out, "wb").write(b"\\x00\\x01 not a dxf")
sys.exit(0)
"""


@pytest.fixture
def fake(tmp_path, monkeypatch):
    d = tmp_path / "fakebin"
    d.mkdir()
    exe = d / "dwg2dxf"
    exe.write_text(FAKE.format(py=sys.executable), encoding="ascii")
    exe.chmod(0o755)
    monkeypatch.setenv("PATH", str(d) + os.pathsep + os.environ.get("PATH", ""))
    assert DA.converters() and DA.converters()[0]["converter"] == "LIBREDWG_DWG2DXF"

    def dwg(path, mode, dxf=""):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"AC1032\n{mode}\n{dxf}\n", encoding="ascii")
        return path
    return dwg


def _empty(tmp_path):
    p = tmp_path / "empty.dxf"
    d = ezdxf.new("R2018")
    d.saveas(str(p))
    return p


def test_empty_conversion_is_blocked_in_strict_mode(fake, tmp_path):
    dwg = fake(tmp_path / "a" / "plan.dwg", "COPY", _empty(tmp_path))
    rec = DA.convert(dwg, tmp_path / "conv", strict=True)
    assert rec["state"] == "BLOCKED" and rec["remedy"].startswith("EMPTY_CONVERSION")
    assert DA.convert(dwg, tmp_path / "conv_v1")["state"] == "CONVERTED"          # V1: unchanged behaviour


def test_garbage_conversion_is_blocked_in_strict_mode(fake, tmp_path):
    rec = DA.convert(fake(tmp_path / "plan.dwg", "GARBAGE"), tmp_path / "conv", strict=True)
    assert rec["state"] == "BLOCKED" and rec["remedy"].startswith("CONVERTED_FILE_UNREADABLE")


def test_a_silent_converter_never_leaves_a_stale_revision_to_be_read(fake, tmp_path, build):
    villa = build("base")
    conv = tmp_path / "conv"
    first = DA.convert(fake(tmp_path / "rev1" / "plan.dwg", "COPY", villa), conv, strict=True)
    assert first["state"] == "CONVERTED"
    # the same DWG path re-issued with a converter that writes nothing: the earlier output is removed first
    again = fake(tmp_path / "rev1" / "plan.dwg", "SILENT")
    stale = conv / f"plan.{DA._sha(again)[:12]}.dxf"
    stale.write_bytes((conv / os.path.basename(first["dxf"])).read_bytes())          # an earlier file of that name
    rec = DA.convert(again, conv, strict=True)
    assert rec["state"] == "BLOCKED" and not stale.exists()


def test_same_file_name_different_content_never_share_an_output(fake, tmp_path, build):
    a = fake(tmp_path / "arch" / "villa.dwg", "COPY", build("base"))
    b = fake(tmp_path / "struct" / "villa.dwg", "COPY", build("empty"))
    ra = DA.convert(a, tmp_path / "conv", strict=True)
    rb = DA.convert(b, tmp_path / "conv", strict=True)
    assert ra["dxf"] != rb["dxf"]
    assert ra["state"] == "CONVERTED" and rb["state"] == "BLOCKED"                  # and each is judged on its own
    assert DA.convert(a, tmp_path / "v1")["dxf"].endswith("villa.dxf")              # V1 naming unchanged


@pytest.mark.parametrize("method,extra", [("ARCH_TAKEOFF_V2", []), ("ARCH_TAKEOFF_V1", ["--strict-admission"])])
def test_cli_blocks_a_failed_conversion_with_exit_2_and_keeps_the_record(fake, tmp_path, cli, h, method, extra):
    out = tmp_path / "out"
    dwg = fake(tmp_path / "plan.dwg", "COPY", _empty(tmp_path))
    rc, _, _ = cli("--drawings", dwg, "--out", out, "--method", method, "--no-svg", "--no-m9-xlsx", *extra)
    assert rc == 2
    B = h.read(out, "ADMISSION_BLOCKED.json")
    assert [f["code"] for f in B["stopping_findings"]] == ["DWG_CONVERSION_BLOCKED"]
    assert h.read(out, "DWG_CONVERSION.json")["conversions"][0]["state"] == "BLOCKED"
    assert not (out / "BOQ_LINES.json").exists()
