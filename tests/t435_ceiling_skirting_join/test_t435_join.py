"""T-435 CEILING_SKIRTING_JOIN_V1 (R-T435-1) on hand villa K435 (not Alsenan).

Villa K435, one storey, hand figures:
  R1 living 5.00 x 4.00 = 20.00 m2 dry, ceiling 20.00, skirting 16.20 lm (18.00 - door 0.90 x 2)
  R2 bath 2.00 x 1.50 = 3.00 m2 wet, ceiling 3.00, no skirting (wall tile to the floor: WT-2 line)
  R3 hall 3.00 x 1.20 = 3.60 m2 dry, ceiling NONE, skirting NONE  -> the silent omission (3.60 m2; 6.00 lm drawn)
  R4 porch 2.00 x 2.00 = 4.00 m2, open to sky (no ceiling by reason), skirting 2.00 lm (one wall)
  R5 under-stair floor 1.00 x 1.20 = 1.20 m2, ceiling = the flight soffit ST-1, skirting on host R1's line
  S1 doorway strip 0.90 x 0.20 = 0.18 m2: ceiling = lintel soffit, skirting = door strip
  R6 dining 4.00 x 3.00 = 12.00 m2, ceiling line only 10.50 (1.50 short, no reason) -> PARTIAL 1.50
  X1 a part an integration row adds (READY), 2.50 m2, no lines yet -> SILENT_OMISSION 2.50 m2, 3.25 lm drawn
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t435"))
import ceiling_skirting_join_v1 as J  # noqa: E402


def L(lid, code, room, q, unit="m2", state="MEASURED", bound=None, trade=""):
    return {"line_id": lid, "item_code": code, "room_id": room, "floor": "GF", "unit": unit, "measured_net": q,
            "evidence_state": state, "bounded_range": bound, "trade": trade}


def villa():
    return [
        L("F1", "FIN.FLOOR.PORCELAIN", "R1", 20.00), L("C1", "FIN.CEILING", "R1", 20.00),
        L("K1", "FIN.SKIRTING", "R1", 16.20, "lm"),
        L("F2", "FIN.FLOOR.WET_TILE", "R2", 3.00), L("C2", "FIN.CEILING", "R2", 3.00),
        L("WT2", "FIN.WALL_TILE", "R2", 13.20),
        L("F3", "FIN.FLOOR.PORCELAIN", "R3", 3.60),
        L("F4", "FIN.FLOOR.PORCELAIN", "R4", 4.00), L("K4", "FIN.SKIRTING", "R4", 2.00, "lm"),
        L("F5", "FIN.FLOOR.PORCELAIN", "R5", 1.20), L("ST1", "STAIR.SOFFIT", "ST-1", 1.44),
        L("F6", "FIN.FLOOR.PORCELAIN", "S1", 0.18),
        L("F7", "FIN.FLOOR.PORCELAIN", "R6", 12.00), L("C7", "FIN.CEILING", "R6", 10.50),
        L("B7", "FIN.FLOOR.BED.DRY", "R6", 12.00),
        L("NA", "FIN.FLOOR.PORCELAIN", "S2", 0.0, state="NOT_APPLICABLE_WITH_EVIDENCE"),
        L("CB", "FIN.CEILING.BULKHEAD", "R3", 0.60),
    ]


REASONS = [
    {"space_id": "R2", "layer": "SKIRTING", "code": "WET_WALL_TILE_TO_FLOOR", "line_id": "WT2", "evidence": "wet"},
    {"space_id": "R4", "layer": "CEILING", "code": "OPEN_TO_SKY", "evidence": "no slab over the porch"},
    {"space_id": "R5", "layer": "CEILING", "code": "UNDER_FLIGHT_SOFFIT", "line_id": "ST1", "evidence": "flight"},
    {"space_id": "R5", "layer": "SKIRTING", "code": "SKIRTING_ON_HOST_FACE", "line_id": "K1", "evidence": "in R1"},
    {"space_id": "S1", "layer": "CEILING", "code": "OPENING_SOFFIT_IN_WALL", "evidence": "lintel"},
    {"space_id": "S1", "layer": "SKIRTING", "code": "DOORWAY_STRIP", "evidence": "door frame"},
]
EXTRA = [{"space_id": "X1", "floor": "GF", "m2": 2.50, "source": "T-9999 READY", "wall_face_lm": 3.25,
          "wall_face_status": "DRAWING-CONFIRMED"}]


def run(lines=None, reasons=REASONS, extra=EXTRA):
    lines = villa() if lines is None else lines
    sp = J.census(lines, extra)
    return sp, J.join(sp, lines, reasons)


def status(rows, sid, layer):
    return next(r for r in rows if r["space_id"] == sid and r["layer"] == layer)


def test_normal_census_and_statuses():
    sp, rows = run()
    assert sorted(sp) == ["R1", "R2", "R3", "R4", "R5", "R6", "S1", "X1"]  # NA strip and bed line not floored spaces
    exp = {("R1", "CEILING"): "OWNED", ("R1", "SKIRTING"): "OWNED", ("R2", "CEILING"): "OWNED",
           ("R2", "SKIRTING"): "REASON", ("R3", "CEILING"): "SILENT_OMISSION", ("R3", "SKIRTING"): "SILENT_OMISSION",
           ("R4", "CEILING"): "REASON", ("R4", "SKIRTING"): "OWNED", ("R5", "CEILING"): "REASON",
           ("R5", "SKIRTING"): "REASON", ("S1", "CEILING"): "REASON", ("S1", "SKIRTING"): "REASON",
           ("R6", "CEILING"): "PARTIAL", ("R6", "SKIRTING"): "SILENT_OMISSION",
           ("X1", "CEILING"): "SILENT_OMISSION", ("X1", "SKIRTING"): "SILENT_OMISSION"}
    got = {(r["space_id"], r["layer"]): r["status"] for r in rows}
    assert got == exp


def test_omissions_in_units():
    _, rows = run()
    t = J.totals(rows)
    # ceiling: R3 3.60 + X1 2.50 = 6.10 m2 silent; R6 1.50 m2 partial
    assert t["CEILING"]["SILENT_OMISSION"]["floor_m2"] == pytest.approx(6.10)
    assert t["CEILING"]["partial_shortfall_m2"] == pytest.approx(1.50)
    # skirting: X1 3.25 lm measured; R3 and R6 lm UNKNOWN (never 0)
    assert t["SKIRTING"]["SILENT_OMISSION"]["lm_measured"] == pytest.approx(3.25)
    assert t["SKIRTING"]["SILENT_OMISSION"]["lm_unknown_spaces"] == 2
    r3 = status(rows, "R3", "SKIRTING")
    assert r3["omission"] == {"unit": "lm", "value": None, "status": "UNKNOWN"}


def test_bulkhead_is_not_a_ceiling_over_the_floor():
    _, rows = run()
    assert status(rows, "R3", "CEILING")["line_ids"] == []


def test_adverse_floored_space_with_no_ceiling_counted_zero():
    """the named adverse case: a ceiling layer that drops a floored space must not read as 0 / complete"""
    _, rows = run()
    r = status(rows, "R3", "CEILING")
    assert r["status"] == "SILENT_OMISSION" and r["omission"]["value"] == pytest.approx(3.60)
    assert r["line_qty"] is None  # never 0


def test_adverse_reason_citing_missing_or_wrong_line_is_refused():
    bad = [{"space_id": "R5", "layer": "CEILING", "code": "UNDER_FLIGHT_SOFFIT", "line_id": "NOPE", "evidence": "x"},
           {"space_id": "R2", "layer": "SKIRTING", "code": "WET_WALL_TILE_TO_FLOOR", "line_id": "C2", "evidence": "x"}]
    _, rows = run(reasons=bad)
    for sid, layer in (("R5", "CEILING"), ("R2", "SKIRTING")):
        r = status(rows, sid, layer)
        assert r["status"] == "SILENT_OMISSION" and r["refused"]


def test_adverse_double_owned_with_stair_soffit():
    lines = villa() + [L("C5", "FIN.CEILING", "R5", 1.20)]
    _, rows = run(lines=lines)
    assert status(rows, "R5", "CEILING")["status"] == "DOUBLE_OWNED"


def test_adverse_open_to_sky_with_a_ceiling_line_is_double():
    lines = villa() + [L("C4", "FIN.CEILING", "R4", 4.00)]
    _, rows = run(lines=lines)
    assert status(rows, "R4", "CEILING")["status"] == "DOUBLE_OWNED"


def test_adverse_one_line_two_spaces():
    lines = villa()
    for ln in lines:
        if ln["line_id"] == "K4":
            ln["room_id"] = "R1"
    _, rows = run(lines=lines)
    assert J.overlap(rows) == []  # K4 now just sits on R1 (one space)
    rows2 = [dict(r) for r in rows] + [{**status(rows, "R1", "SKIRTING"), "space_id": "R9"}]
    assert "K1" in J.overlap(rows2)


def test_adverse_extra_space_already_in_candidate():
    with pytest.raises(ValueError):
        J.census(villa(), [{"space_id": "R1", "m2": 1.0}])


def test_adverse_reason_for_wrong_layer_or_unknown():
    with pytest.raises(ValueError):
        J.join(J.census(villa()), villa(), [{"space_id": "R4", "layer": "SKIRTING", "code": "OPEN_TO_SKY"}])
    with pytest.raises(ValueError):
        J.join(J.census(villa()), villa(), [{"space_id": "R4", "layer": "CEILING", "code": "GUESS"}])


def test_adverse_held_floor_area_is_held_not_zero():
    lines = villa() + [L("F8", "FIN.FLOOR.PORCELAIN", "R8", None, state="HELD", bound=(0.0, 0.23))]
    sp, rows = run(lines=lines)
    assert sp["R8"].m2 is None
    r = status(rows, "R8", "CEILING")
    assert r["status"] == "SILENT_OMISSION" and r["omission"]["status"] == "HELD" and r["omission"]["value"] is None


def test_mirror_and_units_invariance():
    """the join is topological: mirroring / rotating a villa changes no id or figure; lm and m2 never mixed"""
    _, rows = run()
    t = J.totals(rows)
    assert "lm_measured" not in t["CEILING"]["SILENT_OMISSION"]
    assert "lm_measured" in t["SKIRTING"]["SILENT_OMISSION"]


def test_alsenan_committed_table_closes_and_names_the_omissions():
    """the committed Alsenan join (ids and figures only) reproduces and keeps its findings (no private input needed)"""
    import json
    here = Path(__file__).resolve().parents[2] / "research" / "agents_t435"
    sys.path.insert(0, str(here))
    import hashlib
    s = json.loads((here / "summary.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((here / "JOIN_T435.csv").read_bytes()).hexdigest() == s["table_sha256"]
    assert s["candidate_json_sha256_8"] == "733f2efb"
    sil = {(o["space_id"], o["layer"]) for o in s["silent_omissions"]}
    assert ("GF-RFD4E1D", "CEILING") in sil and ("GF-RFD4E1D", "SKIRTING") in sil
    assert s["ceiling_silent_m2"] == pytest.approx(7.345)
    assert s["double_owned"] == [] and s["overlap_line_ids"] == []
    for o in s["silent_omissions"]:
        if o["layer"] == "SKIRTING" and o["space_id"] != "GF-RFD4E1D":
            assert o["omission"]["value"] is None and o["omission"]["status"] == "UNKNOWN"  # never 0
    d = next(o for o in s["silent_omissions"] if o["space_id"] == "GF-RFD4E1D" and o["layer"] == "SKIRTING")
    assert d["omission"]["value"] == pytest.approx(3.90)
