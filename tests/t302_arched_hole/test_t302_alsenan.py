"""T-302 on the development villa: the committed W17 ledger rebuilds byte for byte from the relative drawing constants
(own read of P7757.dxf, checked by `t302_alsenan.py --extract`) and T-292's merged face ledger; no drawing needed."""
import csv
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "research" / "agents_t302"
sys.path.insert(0, str(HERE))
import t302_alsenan as A      # noqa: E402
import t302_arched_hole as R  # noqa: E402


@pytest.fixture(scope="module")
def files():
    return A.outputs()


def test_rebuild_byte_identical(files):
    for n, t in files.items():
        assert (HERE / n).read_text(encoding="utf-8") == t, n


def test_plan_and_elevation_register_on_the_drawn_jambs():
    prof, elev, ok, res = A.model()
    assert ok and max(abs(r) for r in res) < 1e-3
    # the printed chain 2D53 is the jamb-to-jamb projection of the exterior face
    assert A.PRINTED_CHAIN["2D53"] == pytest.approx(A.JAMBS_U[1] - A.JAMBS_U[0], abs=1e-3)
    # the jamb lines end ON the drawn head
    for u, top in zip(A.JAMBS_U, A.JAMB_TOPS):
        assert prof(u) == pytest.approx(top, abs=1e-3)


def test_the_1350_springing_is_outside_the_hole():
    prof, _, _, _ = A.model()
    # T-292's lower bound read 1.350 at the jambs; at the drawn jambs the head is 2.168 / 2.219
    assert min(prof(u) for u in A.JAMBS_U) > 2160 > 1350
    # the arch ends are the curved bay's exterior ends (BCD / BD0 on r 1935), not the window jambs
    import math
    assert A.R_EXT * math.sin(math.radians(A.BAY_ENDS_EXT[0])) == pytest.approx(A.HEAD[-1][0], abs=0.05)


def test_face_values_and_statuses(files):
    rows = {r["face"].split()[0]: r for r in csv.DictReader(files["W17_HOLE_LEDGER_T302.csv"].splitlines())}
    ext, cl, room = rows["EXTERIOR"], rows["CENTRELINE"], rows["ROOM"]
    assert (ext["hole_m2"], ext["status"], ext["projected_m2"]) == ("8.1434", R.STATUS_CONFIRMED, "7.4223")
    assert (cl["hole_m2"], cl["status"]) == ("8.4598 .. 8.5699", R.STATUS_BOUNDED)
    assert (room["hole_m2"], room["status"]) == ("8.7414 .. 8.9965", R.STATUS_BOUNDED)
    assert room["developed_jamb_to_jamb_m"] == "3.2895" and ext["developed_jamb_to_jamb_m"] == "2.9767"
    for r in (ext, cl, room):
        hi = float(r["hole_m2"].split(" .. ")[-1])
        assert hi < float(r["rectangle_cap_m2"])


def test_room_hole_is_not_the_window_measure_and_lies_in_the_checker_bounds(files):
    s = json.loads(files["summary.json"])
    lo, hi = s["room_hole_m2"]
    assert s["window_line_q76a_m2"] == 9.87 and hi < 9.87
    assert 8.1239 <= lo <= hi <= 9.858          # Checker F-T292-02: projection on the outer face .. w x crown
    with pytest.raises(R.Refused):
        R.check_deduction(9.87, "WINDOW_LINE", 3.2895, 3.0)
    with pytest.raises(R.Refused):
        R.check_deduction(s["exterior_projected_m2"], "PROJECTED", 2.9767, 3.0)
    assert s["quantity_changed_in_candidate"] is False


def test_1f11_line_recomputed_with_only_the_w17_hole_replaced(files):
    rows = list(csv.DictReader(files["LINE_1F11_T302.csv"].splitlines()))
    assert sorted(r["item_code"] for r in rows) == ["FIN.PAINT", "FIN.PLASTER"]
    for r in rows:
        assert (r["verified_faces"], r["verified_m2"], r["w17_piece_gross_m2"]) == ("8", "59.4510", "11.0081")
        assert r["t292_reproduced_residual_m2"] == "0.0000"
        assert r["t292_line_m2"] == "60.6011 .. 66.0230"
        assert r["t302_piece_m2"] == "2.0116 .. 2.2667"
        assert r["t302_line_m2"] == "61.4626 .. 61.7177"
        lo, hi = map(float, r["t302_line_m2"].split(" .. "))
        assert 60.6011 <= lo <= hi <= 62.3352     # inside T-292 and the Checker's per-code bounds
        assert lo - 59.4511 > 2.0                 # the released 59.4511 is low by 2.0115 .. 2.2666 m2
        assert r["status"] == R.STATUS_BOUNDED
