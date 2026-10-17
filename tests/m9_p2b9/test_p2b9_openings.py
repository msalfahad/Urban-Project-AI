"""Phase 2B-9 acceptance: the opening schedule and its effect on the finishes (ARCH_TAKEOFF_V2.8, UP-OPEN-SCHED-001,
UP-REVEAL-001), on worked example 1 (a 4.00 x 3.00 m bedroom, door D1 1.00 x 2.20, window W1 1.50 x 1.20 sill 1.00,
its glazing 0.10 m from the room face; the floor-to-ceiling variant W2 1.50 x 3.00 sill 0).

    wall face   42.00 gross - door 2.20 - window 1.80 = 38.00 m2; each opening deducted by its own rectangle inside
                the trade's band, w x (min(head, H) - max(sill, 0)); the reveals are never inside the 38.00
    reveals     the measured depth (strip area / width), jambs 2 x d x the window's band height, head d x w only where
                wall remains above, plaster PROVISIONAL; the sill surface its own geometry (finish by the detail)
    skirting    a sill window is skirted under its sill, floor-level glazing is not, an unknown sill is a range
    no height   the window's width is released, its area held; a schedule row whose width is not the window's gives
                neither its height nor its sill

Truth: p2b9_truth (hand arithmetic)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

pytest.importorskip("ezdxf")

import p2b9_fixtures as F                                     # noqa: E402
import p2b9_run as R                                          # noqa: E402
import p2b9_truth as T                                        # noqa: E402

A = 1e-6
VARIANTS = {
    "sill": dict(window="SILL"),
    "floor": dict(window="FLOOR"),
    "no_schedule": dict(evidence={"TAGS", "SECTION"}),
    "wrong_row": dict(rows={"W1": (1200, 1200, 1000)}),
    "clip": dict(evidence={"TAGS", "SCHEDULE", "SECTION2"}, rows={"W1": (1500, 1900, 1000)}),
}


@pytest.fixture(scope="module")
def ex1(tmp_path_factory):
    work = tmp_path_factory.mktemp("p2b9_openings")
    cache = {}

    def get(key, method=R.V28, facts=False):
        k = (key, method, facts)
        if k not in cache:
            dxf = F.example1(work / f"{key}.dxf", **VARIANTS[key])
            cache[k] = R.run(dxf, work / f"o_{key}_{method}_{facts}", facts=facts, method=method)
        return cache[k]
    return get


def test_example1_wall_face_and_openings(ex1):
    out = ex1("sill")
    for code, el in (("FIN.PLASTER", "plaster"), ("FIN.PAINT", "paint")):
        ln = R.the(out, code, el)
        assert ln["evidence_state"] == "SOURCE_DERIVED"
        assert ln["gross"] == pytest.approx(T.E1_GROSS, abs=A)
        assert ln["measured_net"] == pytest.approx(T.E1_NET, abs=A)
        assert sorted(round(d["m2"], 6) for d in ln["deductions"]) == [round(T.E1_WIN_A, 6), round(T.E1_DOOR_A, 6)]
    d, w = R.opening(out, "DOOR"), R.opening(out, "WINDOW")
    assert (d["plan_width_m"], d["height"]["value_m"], d["area_m2"], d["area_state"]) == (1.0, 2.2, T.E1_DOOR_A,
                                                                                          "MEASURED")
    assert (w["class"], w["plan_width_m"], w["height"]["value_m"], w["sill"]["value_m"], w["head_m"]) == \
        ("WINDOW", T.E1_WIN_W, T.E1_WIN_H, T.E1_SILL, 2.2)
    assert w["area_m2"] == pytest.approx(T.E1_WIN_A, abs=A)
    win = R.the(out, "ARCH.WINDOW")
    assert (win["measured_net"], win["calculation"]["inputs"]["area_m2"], win["calculation"]["inputs"]["mark"]) == \
        (1, pytest.approx(T.E1_WIN_A, abs=A), "W1")
    # the door's BOQ height is the schedule's, not the owner reference
    door = [ln for ln in R.lines(out) if ln["item_code"].startswith("DOOR.")]
    assert len(door) == 1 and "SCHEDULE" in door[0]["notes"]
    # the door jambs are their own provisional line (2 x 0.20 x 2.20 + 0.20 x 1.00), never inside the 38.00
    jam = R.the(out, "FIN.PLASTER", "door jambs")
    assert (jam["measured_net"], jam["evidence_state"]) == (pytest.approx(T.E1_DOOR_JAMB_PLASTER, abs=A),
                                                            "PROVISIONAL")
    assert R.net(out, "FIN.SKIRTING", "skirting") == pytest.approx(T.E1_SKIRTING, abs=A)


def test_v271_deducted_the_window_at_full_height(ex1):
    """as found: V2.7.1 with the S2 facts (door 2.10, window 1.50) deducts each window at its full height inside the
    band (WINDOW_POSITION_ASSUMED) and blocks the reveal - no schedule, no sill."""
    out = ex1("sill", method=R.V271, facts=True)
    ln = R.the(out, "FIN.PLASTER", "plaster")
    assert ln["measured_net"] == pytest.approx(42.00 - 1.00 * 2.10 - 1.50 * 1.50, abs=A)       # 37.65
    assert "WINDOW_POSITION_ASSUMED" in ln["notes"]
    assert R.the(out, "ARCH.WINDOW_REVEAL")["evidence_state"] == "BLOCKED_RFI"


def test_a_window_is_deducted_inside_each_band_only(ex1):
    """head 2.90 above the finished ceiling 2.80, under the soffit 3.00: paint deducts 1.80 m of the window's height,
    plaster 1.90 m."""
    out = ex1("clip")
    assert R.net(out, "FIN.PLASTER", "plaster") == pytest.approx(T.E1_CLIP_PLASTER, abs=A)
    assert R.net(out, "FIN.PAINT", "paint") == pytest.approx(T.E1_CLIP_PAINT, abs=A)
    assert R.opening(out, "WINDOW")["head_m"] == pytest.approx(T.E1_CLIP_HEAD, abs=A)
    assert R.net(out, "FIN.PLASTER", "window reveals") == pytest.approx(T.E1_CLIP_REVEALS, abs=A)


def test_floor_glazing_is_not_skirted(ex1):
    out = ex1("floor")
    w = R.opening(out, "WINDOW")
    assert (w["class"], w["sill"]["value_m"], w["head_m"]) == ("FLOOR_GLAZING", 0.0, 3.0)
    sk = R.the(out, "FIN.SKIRTING", "skirting")
    assert sk["measured_net"] == pytest.approx(T.E1F_SKIRTING, abs=A)
    assert "floor-level glazing not skirted (1.50 m)" in sk["notes"]
    assert not R.all_of(out, "FIN.SKIRTING", "skirting, boundary role unresolved")
    assert R.net(out, "FIN.PLASTER", "plaster") == pytest.approx(T.E1F_NET, abs=A)


def test_an_unknown_sill_makes_skirting_a_range(ex1):
    out = ex1("no_schedule")
    assert R.opening(out, "WINDOW")["class"] == "WINDOW_SILL_NOT_ESTABLISHED"
    assert R.net(out, "FIN.SKIRTING", "skirting") == pytest.approx(T.E1_UNKNOWN_SILL_SKIRTING, abs=A)
    rng = R.the(out, "FIN.SKIRTING", "skirting, boundary role unresolved")
    assert rng["measured_net"] is None
    lo, hi = T.E1_UNKNOWN_SILL_SKIRTING_RANGE
    assert (rng["bounded_range"]["low"], rng["bounded_range"]["high"]) == (lo, pytest.approx(hi, abs=A))
    assert set(rng["calculation"]["inputs"]["unresolved_by_roles"]) == {"WINDOW_SILL_NOT_ESTABLISHED"}
    # the wall face is a range too: the window's deduction is anywhere between none and its full band
    for code, el in (("FIN.PLASTER", "plaster"), ("FIN.PAINT", "paint")):
        ln = R.the(out, code, el)
        assert ln["measured_net"] is None
        assert (ln["bounded_range"]["low"], ln["bounded_range"]["high"]) == (
            pytest.approx(T.E1_UNKNOWN_WIN_LOW, abs=A), pytest.approx(T.E1_UNKNOWN_WIN_HIGH, abs=A))


def test_a_window_without_a_height_holds_its_area(ex1):
    out = ex1("no_schedule")
    w = R.opening(out, "WINDOW")
    assert (w["height"]["value_m"], w["area_m2"], w["area_state"]) == (None, None, "HELD: height not established")
    ln = R.the(out, "ARCH.WINDOW")
    assert ln["measured_net"] == 1 and ln["calculation"]["inputs"]["width_m"] == pytest.approx(T.E1_WIN_W, abs=A)
    assert ln["calculation"]["inputs"]["area_m2"] is None and "width released, area held" in ln["notes"]
    assert R.the(out, "ARCH.WINDOW_REVEAL")["evidence_state"] == "BLOCKED_RFI"
    # the mark's row has another width: neither its height nor its sill is the window's
    out = ex1("wrong_row")
    w = R.opening(out, "WINDOW")
    assert {f["code"] for f in w["findings"]} == {"SCHEDULE_WIDTH_DIFFERS"}
    assert (w["height"]["state"], w["sill"]["state"], w["area_m2"]) == ("CONFLICT", "CONFLICT", None)
    assert R.the(out, "FIN.PLASTER", "plaster")["measured_net"] is None


def test_example1_reveals_and_sill_surface(ex1):
    out = ex1("sill")
    rv = R.the(out, "FIN.PLASTER", "window reveals")
    assert (rv["measured_net"], rv["evidence_state"]) == (pytest.approx(T.E1_REVEAL_PLASTER, abs=A), "PROVISIONAL")
    rec = [r for r in R.reveals(out) if r["state"] == "MEASURED"]
    assert len(rec) == 1
    assert (rec[0]["depth_m"], rec[0]["jambs_m2"], rec[0]["head_m2"]) == (
        pytest.approx(T.E1_REVEAL_D, abs=A), pytest.approx(T.E1_REVEAL_JAMBS, abs=A),
        pytest.approx(T.E1_REVEAL_HEAD, abs=A))
    sill = R.the(out, "ARCH.WINDOW_REVEAL", "window sill surface")
    assert sill["measured_net"] == pytest.approx(T.E1_SILL_SURFACE, abs=A)
    # the strip outside the glazing is external: its own line, never the room's reveal
    ext = R.the(out, "ARCH.WINDOW_REVEAL", "window external strip")
    assert (ext.get("location") or {}).get("room_id") != (sill.get("location") or {}).get("room_id")
    assert [r["state"] for r in R.reveals(out) if r["state"] != "MEASURED"] == ["EXTERNAL_NOT_IN_INTERNAL_SCOPE"]
    # the main wall face is the hand value exactly: no reveal inside it
    assert R.net(out, "FIN.PLASTER", "plaster") == pytest.approx(T.E1_NET, abs=A)


def test_floor_glazing_reveals_and_floor_strip(ex1):
    out = ex1("floor")
    rv = R.the(out, "FIN.PLASTER", "window reveals")
    assert rv["measured_net"] == pytest.approx(T.E1F_REVEAL_PLASTER, abs=A)       # jambs only: no wall above
    rec = [r for r in R.reveals(out) if r["state"] == "MEASURED"][0]
    assert rec["head_m2"] == 0.0
    fl = R.the(out, "FIN.FLOOR.PORCELAIN", "window floor strip")
    assert (fl["measured_net"], fl["evidence_state"]) == (pytest.approx(T.E1F_FLOOR_STRIP, abs=A), "PROVISIONAL")
    assert not R.all_of(out, "ARCH.WINDOW_REVEAL", "window sill surface")
