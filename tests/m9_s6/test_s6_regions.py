"""M9 S6 Phase 1 - plan regions. ARCH_TAKEOFF_V2 separates several plans in one sheet frame along the empty bands
between their drawn geometry (a cut never runs through a plan; titles no band separates are blocked, not guessed) and
reads a frame drawn as four lines (a review flag). ARCH_TAKEOFF_V1 keeps the midpoint cut; behind --strict-admission a
midpoint cut that crosses drawn geometry stops the run."""

from __future__ import annotations

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import arch_plan as AP              # noqa: E402
from tools import arch_discovery as AD                 # noqa: E402
from tools import urban_boq_m9 as M9                   # noqa: E402

V1, V2 = "ARCH_TAKEOFF_V1", "ARCH_TAKEOFF_V2"


def _rooms_by_floor(arch):
    out = {}
    for r in arch["rooms"]:
        out.setdefault(r["floor"], []).append((r["class"], "+".join(r.get("codes") or []), round(r["area_m2"], 6)))
    return {k: sorted(v) for k, v in out.items()}


def test_two_plans_in_one_frame_are_measured_on_their_own_floors(build):
    ref = _rooms_by_floor(M9.arch_compute(str(build("base")), method=V2)[1])
    _, arch, _ = M9.arch_compute(str(build("two_plans_left")), method=V2)
    assert arch["run"]["s6"]["region_split"] == "EMPTY_BANDS"
    assert _rooms_by_floor(arch) == ref
    assert [r["floor"] for r in arch["regions"]] == ["GF", "1F"]


def test_v1_strict_stops_a_midpoint_cut_through_a_plan(build, cli, tmp_path, h):
    out = tmp_path / "out"
    rc, _, _ = cli("--drawings", build("two_plans_left"), "--out", out, "--method", V1, "--strict-admission",
                   "--no-svg", "--no-m9-xlsx")
    assert rc == 2
    assert "REGION_CUT_CROSSES_GEOMETRY" in {f["code"] for f in h.read(out, "ADMISSION_BLOCKED.json")["stopping_findings"]}
    ok = tmp_path / "ok"                                   # control: the titles centred under their plans
    assert cli("--drawings", build("two_plans_centred"), "--out", ok, "--method", V1, "--strict-admission",
               "--no-svg", "--no-m9-xlsx")[0] == 0


def test_frame_drawn_as_lines_is_read_with_a_review_flag(build, cli, tmp_path, h):
    ref = _rooms_by_floor(M9.arch_compute(str(build("base")), method=V2)[1])
    out = tmp_path / "out"
    assert cli("--drawings", build("frame_exploded"), "--out", out, "--method", V2, "--no-svg", "--no-m9-xlsx")[0] == 0
    D = h.read(out, "DRAWING_DISCOVERY.json")
    assert "FRAME_DRAWN_AS_LINES" in {f["code"] for f in h.findings(D, "REVIEW_REQUIRED")}
    rooms = {}
    for r in h.read(out, "ARCH_ROOMS.json")["rooms"]:
        rooms.setdefault(r["floor"], []).append((r["class"], "+".join(r.get("codes") or []), round(r["area_m2"], 6)))
    assert {k: sorted(v) for k, v in rooms.items()} == ref


def test_sheet_frame_sides_are_never_plan_geometry(build, h):
    ref = M9.arch_compute(str(build("base")), method=V2)
    got = M9.arch_compute(str(build("frame_on_wall_layer")), method=V2)
    assert h.fingerprint(*got[:2]) == h.fingerprint(*ref[:2])          # without the S6 rule the plate was the frame
    assert all(r["frame_side_segments_dropped"] == 4 for r in got[1]["regions"])


def _sq(x0, y0, s):
    p = [(x0, y0), (x0 + s, y0), (x0 + s, y0 + s), (x0, y0 + s)]
    return [{"a": p[i], "b": p[(i + 1) % 4]} for i in range(4)]


def test_xy_cut_never_cuts_drawn_geometry():
    titles = [{"x": 1.0, "y": -1.0, "floor": "GF"}, {"x": 12.0, "y": -1.0, "floor": "1F"}]
    wide = _sq(0, 0, 10) + _sq(11, 0, 10)                  # an empty band 1.0 wide between the plans
    pieces = AP.xy_cut((-1, -2, 22, 11), wide, titles, 0.5)
    assert pieces and [len(t) for _b, t in pieces] == [1, 1]
    assert pieces[0][0][2] == pytest.approx(10.5)            # the cut runs in the middle of the empty band
    narrow = _sq(0, 0, 10) + _sq(10.2, 0, 10)              # 0.2 wide: below the band minimum - not cut
    assert AP.xy_cut((-1, -2, 22, 11), narrow, titles, 0.5) is None
    joined = _sq(0, 0, 10) + _sq(5, 0, 10)                 # overlapping drawings: no band at all
    assert AP.xy_cut((-1, -2, 22, 11), joined, titles, 0.5) is None


def test_region_override_is_validated():
    r = AD.override_regions(["GF=0,0,10,10", "1F=20,0,30,10"])
    assert [x["floor"] for x in r["regions"]] == ["GF", "1F"] and r["overrides"] is True
    for bad in ("XF=0,0,1,1", "GF=0,0,1", "GF=5,0,1,1"):
        with pytest.raises(ValueError):
            AD.override_regions([bad])
