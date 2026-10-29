"""T-342 R-T342-BIND-1 on a hand-made villa (not Alsenan): a pool label written as a compound phrase whose first word
is a bathroom word, a court with two labels, a roof label repeated in one face, a label outside every face, a void,
and the adverse cases (binding by name only, a court bound to a floor-tile line, a held space carried as 0)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t342"))
import t342_label_binding as B  # noqa: E402

VOCAB = {"bath": "BATHROOM", "bath swim": "POOL", "court": "GARDEN", "roof": "ROOF", "void": "VOID"}


def word(text):  # compound phrase before the bare word (as ROOM_VOCAB_V2)
    t = text.lower()
    for k in sorted(VOCAB, key=len, reverse=True):
        if k in t:
            return VOCAB[k]
    return None


LABELS = [
    {"text_id": "X1", "text": "bath swim", "code": "BATHROOM", "floor": "GF", "status": "SILENT_OMISSION"},
    {"text_id": "X2", "text": "court", "code": "GARDEN", "floor": "GF", "status": "SILENT_OMISSION"},
    {"text_id": "X3", "text": "court", "code": "GARDEN", "floor": "GF", "status": "SILENT_OMISSION"},
    {"text_id": "X4", "text": "roof", "code": "ROOF", "floor": "1F", "status": "SILENT_OMISSION"},
    {"text_id": "X5", "text": "roof", "code": "ROOF", "floor": "1F", "status": "SILENT_OMISSION"},
    {"text_id": "X6", "text": "bath", "code": "BATHROOM", "floor": "GF", "status": "SILENT_OMISSION"},
    {"text_id": "X7", "text": "void", "code": "VOID", "floor": "1F", "status": "SILENT_OMISSION"},
]
# hand geometry: pool 4.00 x 2.50 = 10.000 m2 water; court 12.00 x 6.00 = 72.000 less the pool shell 4.40 x 2.90 = 12.760
# -> 59.240 m2; roof 8.00 x 5.00 = 40.000 m2; void 2.00 x 1.50 = 3.000 m2
FACES = [
    {"face_id": "F-POOL", "floor": "GF", "code": "POOL", "labels": ["X1"], "source": ["P1", "P2"], "area_m2": 10.0},
    {"face_id": "F-COURT", "floor": "GF", "code": "GARDEN", "labels": ["X2", "X3"], "source": ["C1"], "area_m2": 59.24},
    {"face_id": "F-ROOF", "floor": "1F", "code": "ROOF", "labels": ["X4", "X5"], "source": ["R1"], "area_m2": 40.0},
    {"face_id": "F-VOID", "floor": "1F", "code": "VOID", "labels": ["X7"], "source": ["V1"], "area_m2": 3.0},
]
LINES = [
    {"line_id": "L-POOL-CONC", "item_code": "CONC.POOL", "quantity": 4.2, "source": ["P1"], "cites": []},
    {"line_id": "L-ROOF-WP", "item_code": "FIN.WP.ROOF", "quantity": 40.0, "source": ["R1"], "cites": ["X4"]},
    {"line_id": "L-TILE-GF", "item_code": "FIN.FLOOR.TILE", "quantity": 30.0, "source": ["T9"], "cites": []},
]


def scopes(court_lines=("FLOOR.OUTDOOR",), court_status="MISSING", court_q=59.24):
    return {
        "F-POOL": [{"scope": "pool shell concrete", "item_codes": ["CONC.POOL"], "status": "BOUND"}],
        "F-COURT": [{"scope": "outdoor floor finish", "item_codes": list(court_lines), "status": court_status,
                     "quantity": court_q, "unit": "m2", "evidence_status": "DRAWING-CONFIRMED"}],
        "F-ROOF": [{"scope": "roof membrane", "item_codes": ["FIN.WP.ROOF"], "status": "BOUND"}],
        "F-VOID": [{"scope": "floor / ceiling", "item_codes": [], "status": "NOT_APPLICABLE",
                    "evidence": "opening open to below, slab edge lines V1"}],
    }


def test_normal_case():
    r = B.bind(LABELS, FACES, LINES, scopes(), word=word)
    by = {x["text_id"]: x for x in r["rows"]}
    assert by["X1"]["code"] == "POOL" and by["X1"]["retype"].startswith("RETYPED BATHROOM -> POOL")
    assert by["X1"]["binding"] == "BOUND" and by["X1"]["lines"] == ["L-POOL-CONC"]
    assert by["X2"]["binding"] == "MISSING" and by["X3"]["binding"] == "DUPLICATE_OF" and by["X3"]["duplicate_of"] == "X2"
    assert by["X4"]["binding"] == "BOUND" and by["X5"]["duplicate_of"] == "X4" and by["X5"]["lines"] == ["L-ROOF-WP"]
    assert by["X6"]["binding"] == "MISSING_NO_FACE"          # a bathroom label outside every face: HELD, never 0
    assert by["X7"]["binding"] == "NOT_APPLICABLE"
    court = [s for s in r["scopes"] if s["face_id"] == "F-COURT"][0]
    assert court["status"] == "MISSING" and court["quantity"] == pytest.approx(12.0 * 6.0 - 4.4 * 2.9)
    assert r["summary"]["by_binding"] == {"BOUND": 2, "MISSING": 1, "DUPLICATE_OF": 2, "MISSING_NO_FACE": 1,
                                          "NOT_APPLICABLE": 1}


def test_without_compound_vocabulary_the_pool_label_reads_as_a_bathroom_and_is_refused():
    with pytest.raises(ValueError, match="differs from its face"):
        B.bind(LABELS, FACES, LINES, scopes(), word=None)


def test_mirror_and_order_do_not_change_the_binding():
    r1 = B.bind(LABELS, FACES, LINES, scopes(), word=word)
    r2 = B.bind(list(reversed(LABELS)), list(reversed(FACES)), list(reversed(LINES)), scopes(), word=word)
    s1 = {x["text_id"]: (x["binding"] if x["binding"] != "DUPLICATE_OF" else "COUNTED_ONCE") for x in r1["rows"]}
    s2 = {x["text_id"]: (x["binding"] if x["binding"] != "DUPLICATE_OF" else "COUNTED_ONCE") for x in r2["rows"]}
    # the first label met in a face carries the binding, the other one is its duplicate: the face is bound once
    assert {k: v for k, v in s1.items() if k not in ("X2", "X3", "X4", "X5")} == \
        {k: v for k, v in s2.items() if k not in ("X2", "X3", "X4", "X5")}
    assert sorted([s1["X2"], s1["X3"]]) == sorted([s2["X2"], s2["X3"]])


def test_adverse_binding_by_name_only_is_refused():
    lines = LINES + [{"line_id": "L-NAMED", "item_code": "FIN.WP.ROOF", "quantity": 9.0, "source": ["Z7"],
                      "cites": ["X5"]}]
    r = B.bind(LABELS, FACES, lines, scopes(), word=word)
    roof = [s for s in r["scopes"] if s["face_id"] == "F-ROOF"][0]
    assert roof["lines"] == ["L-ROOF-WP"] and ("L-NAMED", "REFUSED_NAME_ONLY") in roof["refused"]


def test_adverse_court_bound_to_an_interior_floor_tile_line_is_refused():
    lines = LINES + [{"line_id": "L-TILE-COURT", "item_code": "FIN.FLOOR.TILE", "quantity": 59.24, "source": ["C1"],
                      "cites": ["X2"]}]
    r = B.bind(LABELS, FACES, lines, scopes(), word=word)
    court = [s for s in r["scopes"] if s["face_id"] == "F-COURT"][0]
    assert court["lines"] == [] and court["status"] == "MISSING"
    assert ("L-TILE-COURT", "REFUSED_WRONG_TRADE") in court["refused"]


def test_adverse_held_space_never_zero():
    with pytest.raises(ValueError, match="never carries 0"):
        B.bind(LABELS, FACES, LINES, scopes(court_q=0.0), word=word)
    lines = LINES + [{"line_id": "L-ZERO", "item_code": "FLOOR.OUTDOOR", "quantity": 0.0, "source": ["C1"], "cites": []}]
    r = B.bind(LABELS, FACES, lines, scopes(), word=word)
    court = [s for s in r["scopes"] if s["face_id"] == "F-COURT"][0]
    assert court["lines"] == [] and ("L-ZERO", "REFUSED_ZERO_FOR_HELD") in court["refused"]


def test_bound_scope_with_no_line_is_downgraded_to_missing():
    r = B.bind(LABELS, FACES, [l for l in LINES if l["line_id"] != "L-POOL-CONC"], scopes(), word=word)
    pool = [s for s in r["scopes"] if s["face_id"] == "F-POOL"][0]
    assert pool["status"] == "MISSING" and pool["quantity"] is None
    assert [x for x in r["rows"] if x["text_id"] == "X1"][0]["binding"] == "MISSING"


def test_not_applicable_needs_evidence():
    sc = scopes()
    sc["F-VOID"][0]["evidence"] = None
    with pytest.raises(ValueError, match="needs drawing evidence"):
        B.bind(LABELS, FACES, LINES, sc, word=word)


# ---- a pool measured on another drawing (structural shell POOL-9): D shape, half circle r 1.40 + rectangle 2.80 x 1.20
D_AREA = math.pi * 1.40 ** 2 / 2 + 2.80 * 1.20            # 3.0788 + 3.360 = 6.4388 m2
D_PERIM = math.pi * 1.40 + 2.80 + 2 * 1.20                 # 4.3982 + 5.200 = 9.5982 lm
CIRCLE_AREA = math.pi * 1.40 ** 2                          # 6.1575 m2: the circle reading of the same printed radius


def _pool_case(corr):
    faces = [{"face_id": "F-P", "floor": "GF", "code": "POOL", "labels": ["Y1"], "source": ["A1"], "corresponds": corr}]
    labels = [{"text_id": "Y1", "text": "bath swim", "code": "BATHROOM", "floor": "GF"}]
    lines = [{"line_id": "L-SHELL", "item_code": "CONC.POOL", "quantity": 3.1, "source": ["POOL-9"], "cites": []}]
    sc = {"F-P": [{"scope": "pool shell concrete", "item_codes": ["CONC.POOL"], "status": "BOUND"}]}
    return B.bind(labels, faces, lines, sc, word=word)


def test_cross_drawing_pool_bound_on_area_and_perimeter():
    r = _pool_case([{"element": "POOL-9", "face_m2": round(D_AREA, 3), "element_m2": D_AREA,
                     "face_lm": round(D_PERIM, 3), "element_lm": D_PERIM}])
    assert r["rows"][0]["binding"] == "BOUND" and r["rows"][0]["lines"] == ["L-SHELL"]


def test_adverse_cross_drawing_by_name_only_or_circle_reading_is_refused():
    r = _pool_case([{"element": "POOL-9"}])
    assert r["rows"][0]["binding"] == "MISSING" and r["rows"][0]["elements_refused"] == [("POOL-9", "CORR_NAME_ONLY")]
    r = _pool_case([{"element": "POOL-9", "face_m2": round(D_AREA, 3), "element_m2": CIRCLE_AREA}])
    assert r["rows"][0]["binding"] == "MISSING" and r["rows"][0]["elements_refused"][0][1].startswith("CORR_AREA")
    # same area, wrong outline (perimeter of the circle 8.796 vs the D 9.598): refused too
    r = _pool_case([{"element": "POOL-9", "face_m2": D_AREA, "element_m2": D_AREA, "face_lm": 2 * math.pi * 1.40,
                     "element_lm": D_PERIM}])
    assert r["rows"][0]["elements_refused"][0][1].startswith("CORR_PERIMETER")


def test_units_millimetre_figures_are_not_metres():
    # a correspondence written in mm2 against an m2 element never agrees: refused, never silently scaled
    r = _pool_case([{"element": "POOL-9", "face_m2": D_AREA * 1e6, "element_m2": D_AREA}])
    assert r["rows"][0]["binding"] == "MISSING"
