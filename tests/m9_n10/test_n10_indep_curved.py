"""Phase N10 - the independent side of the curved openings: tools/indep_reader.py reads the jambed curved gaps of the
raw drawing (no engine module) and, with curved_closures, closes them on both faces; tools/arch_change_verify.py then
checks the V2.8 -> V2.9 changes of a curved window against that reading (hand truth: n10_truth.py)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "m9_p2b9"))
sys.path.insert(0, str(ROOT / "tools"))

import arch_change_verify as V                                # noqa: E402
import indep_reader as IR                                     # noqa: E402
import n10_fixtures as F                                      # noqa: E402
import n10_run as R                                           # noqa: E402
import n10_truth as T                                         # noqa: E402
import p2b9_fixtures as F9                                    # noqa: E402

ROLES = {"A-WALL": "WALL", "A-GLAZ": "WINDOW", "A-DOOR": "DOOR", "A-COL": "COLUMN"}
FLAT = 1e-4       # the reader flattens curves in 5 mm steps: a few square micrometres per arc


@pytest.mark.parametrize("opening", ["WINDOW", "SPLAYED", "PASSAGE"])
def test_reader_curved_gap_census(tmp_path, opening):
    D = IR.Drawing(F.curved_room(tmp_path / "c.dxf", opening=opening), roles=ROLES)
    g = D.curved_gaps()
    assert len(g) == 1
    inner = T.GAP_INNER if opening == "PASSAGE" else T.WIN_INNER
    assert g[0]["inner_lm"] == pytest.approx(inner, abs=1e-6)
    assert g[0]["glazing_share"] == (0.0 if opening == "PASSAGE" else pytest.approx(1.0, abs=1e-6))


def test_reader_refuses_a_gap_without_jambs(tmp_path):
    D = IR.Drawing(F.curved_room(tmp_path / "c.dxf", opening="NO_JAMB"), roles=ROLES)
    assert D.curved_gaps() == []


def test_reader_closes_the_curved_window_on_the_room_face(tmp_path):
    dxf = F.curved_room(tmp_path / "c.dxf", opening="WINDOW")
    assert IR.Drawing(dxf, roles=ROLES).face_at((1.3, 1.5)) is None          # the room leaks without the closure
    D = IR.Drawing(dxf, roles=ROLES, curved_closures=True)
    f = D.face_at((1.3, 1.5))
    assert f["area_m2"] == pytest.approx(T.FLOOR, abs=FLAT)
    assert f["perimeter_m"] == pytest.approx(T.PERIM, abs=FLAT)
    ops, free = D.openings_on(f)
    assert sorted((o["kind"], round(o["width_m"], 6)) for o in ops) == [("DOOR", 1.0), ("WINDOW", round(T.WIN_INNER, 6))]
    assert free == pytest.approx(0.0, abs=1e-4)


def test_v28_to_v29_curved_window_changes_are_independently_verified(tmp_path):
    """example 4S with its roles declared: V2.8 closes the room at the glazing (7.507006 m2), V2.9 at the room face
    (7.068583 m2). Every changed total is explained by the CURVED_OPENING record and the floor change is VERIFIED by
    the reader's own face (closed by its own curved closures)."""
    dxf = F9.example4_curved_stub(tmp_path / "e4s.dxf")
    roles = F.ROLES
    before = R.run(dxf, tmp_path / "v28", roles=roles, method=R.V28)
    after = R.run(dxf, tmp_path / "v29", roles=roles, method=R.V29)
    rep = V.Verifier(before, after, dxf, {}, dict(x.split("=", 1) for x in roles)).report()
    assert rep["summary"]["UNEXPLAINED"] == 0 and rep["summary"]["CONTRADICTED"] == 0
    floor = [r for r in rep["differences"] if r["item_code"] == "FIN.FLOOR.PORCELAIN" and r["after"] > 1]
    assert len(floor) == 1
    assert (floor[0]["before"], floor[0]["after"]) == (pytest.approx(T.FLOOR_IF_CLOSED_AT_GLAZING, abs=1e-5),
                                                        pytest.approx(T.FLOOR, abs=1e-5))
    assert floor[0]["status"] == "VERIFIED" and floor[0]["verification"]["method"] == "INDEPENDENT_FACE"
    assert floor[0]["verification"]["independent"] == pytest.approx(T.FLOOR, abs=FLAT)
    assert "CURVED_OPENING" in floor[0]["kinds"]
    json.dumps(rep)                                            # the report is plain data
