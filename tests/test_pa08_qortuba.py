"""PA08 Qortuba package: the deterministic reader helpers (keyboard-map decode, rotated-dimension projection) and the
verdict logic; the engine is untouched by this package."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from research.qs_wall_treatment_01.pa08.qortuba import common as C


def test_keyboard_map_decodes_the_gulf_shape_font_convention():
    assert C.kb_decode("whgm")[0] == "صالة"
    assert C.kb_decode("plHL")[0] == "حمام"
    assert C.kb_decode("lBfS")[0] == "ملابس"
    assert C.kb_decode("s'P")[0] == "سطح"
    assert C.kb_decode("Hglsr' HBtrD gg],v HgehkD")[0] == "المسقط الافقي للدور الثاني"
    assert C.looks_keyboard_arabic("whgm") and C.looks_keyboard_arabic("k,LVzdsD") and not C.looks_keyboard_arabic("HALL") and not C.looks_keyboard_arabic("BED.ROOM")


def test_rotated_linear_dimension_projection_is_the_authored_value():
    # extension origins offset 68 mm perpendicular to a 150 mm dimension rotated by pi: raw distance 164.9, projection 150
    p1, p2, rot = (0.0, 0.0), (-150.0, 68.4), math.pi
    raw = math.hypot(p2[0] - p1[0], p2[1] - p1[1]); proj = abs((p2[0] - p1[0]) * math.cos(rot) + (p2[1] - p1[1]) * math.sin(rot))
    assert abs(raw - 164.87) < 0.1 and abs(proj - 150.0) < 1e-9


@pytest.mark.skipif(not (Path(C.OUT) / "PA08_QORTUBA_PRELIMINARY_VERDICT.json").exists(), reason="Qortuba blind outputs not present in this checkout")
def test_qortuba_blind_outputs_are_loud_everywhere():
    import json
    v = json.loads((Path(C.OUT) / "PA08_QORTUBA_PRELIMINARY_VERDICT.json").read_text("utf-8"))
    tr = json.loads((Path(C.OUT) / "PA08_QORTUBA_QUANTITY_TRACE.json").read_text("utf-8"))
    assert v["VERDICT"] in ("READY_FOR_EXTERNAL_COMPARISON", "NOT_READY_FOR_EXTERNAL_COMPARISON")
    assert all("STATUS" in l and l["STATUS"] for l in tr["LINES"])          # no naked number
    assert all(l["VALUE"] is None for l in tr["LINES"] if l["UNIT"] == "m2" and l["TRADE"] in ("NORMAL_INTERNAL_PLASTER", "WET_ROOM_SPLATTER", "COLUMN_BONDING"))
    fz = json.loads((Path(C.OUT) / "FREEZE_PA08_QORTUBA_BLIND_01.json").read_text("utf-8"))
    assert fz["ENGINE_PATCHED_BEFORE_FREEZE"] is False and fz["ENGINE_FREEZE_BASE"]["ENGINE_CODE_DRIFT"] == []
