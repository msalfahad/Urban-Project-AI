"""M9 S5 - metamorphic checks of the architectural route through the CAD reader: a DXF saved in another DXF version
(an ezdxf round trip) and a zone line drawn as one polyline instead of separate lines measure the same quantities.
The R2000 round trip found a real defect: a pre-2007 DXF stores Arabic text as \\U+XXXX escapes, which the reader did
not decode (the Arabic room word was lost); tools.arch_intake.decode_text now decodes them exactly.
(Translation / mirror / quarter turns of the whole villa: tests/m9_s2_arch; zone-level rigid motions, entity order,
collinear subdivision and furniture: test_s5_zones.) DWG round trips need a converter that is not installed here:
untested, never claimed."""

from __future__ import annotations

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import arch_rooms as AR             # noqa: E402
from tools import arch_synth as AS                     # noqa: E402
from tools import urban_boq_m9 as M9                   # noqa: E402

METHOD = "ARCH_TAKEOFF_V1"


def _quantities(room):
    out = {}
    for ln in room["lines"]:
        if ln.get("measured_net") is not None:
            k = (ln["location"]["floor"], ln["location"]["room_id"], ln["item_code"], ln["physical_element"])
            out[k] = round(ln["measured_net"], 6)
    return out


@pytest.mark.parametrize("version", ["R2000", "R2018"])
def test_dxf_version_round_trip_keeps_every_quantity(tmp_path, version):
    a = tmp_path / "villa.dxf"
    AS.villa(a)
    b = tmp_path / f"villa_{version}.dxf"
    doc = ezdxf.readfile(str(a))
    doc.dxfversion = ezdxf.const.acad_release_to_dxf_version[version]    # R2000: \U+XXXX escapes for Arabic text
    doc.saveas(str(b))
    ra, _, _ = M9.arch_compute(str(a), method=METHOD)
    rb, _, _ = M9.arch_compute(str(b), method=METHOD)
    qa, qb = _quantities(ra), _quantities(rb)
    assert qa and qa == qb


def test_zone_line_as_one_polyline_or_separate_lines():
    ents, roles, _ = AS.s5_zones()
    S0 = AR.spaces(ents, roles, 0.001, region_id="T")
    ents2, _, _ = AS.s5_zones()
    for s in ents2["segments"]:                         # the garden strip's three lines become one polyline path
        if s["layer"] == "A-FLOR" and s["a"] in ((4000.0, 1500.0), (4000.0, 200.0), (9000.0, 200.0)):
            s["path"] = ["PLINE:1"]
    S1 = AR.spaces(ents2, roles, 0.001, region_id="T")
    z0 = sorted((z["class"], tuple(z["codes"]), z["area_m2"]) for r in S0["zones"] for z in r.get("zones") or ())
    z1 = sorted((z["class"], tuple(z["codes"]), z["area_m2"]) for r in S1["zones"] for z in r.get("zones") or ())
    assert z0 and z0 == z1


def test_dxf_unicode_escapes_are_decoded_and_the_raw_text_kept():
    from tools import arch_intake as AI
    val, state = AI.decode_text("\\U+0635\\U+0627\\U+0644\\U+0629", "txt.shx")
    assert state == "DXF_UNICODE_ESCAPE" and val == "".join(chr(c) for c in (0x635, 0x627, 0x644, 0x629))
    assert AI.decode_text("LIVING", "txt.shx") == ("LIVING", "UNICODE")
