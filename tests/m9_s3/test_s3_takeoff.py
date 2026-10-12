"""M9 S3 - geometry and takeoff acceleration, on SYNTHETIC drawings only (tools/arch_synth.py). Every expected value is
written by hand from the fixture coordinates (tread polygons, wedge areas, ellipse perimeters, keyboard letters) or is
a metamorphic identity (a variant of the same plan gives the same takeoff); none is taken from the engine. The
production path is exercised: urban_boq_m9.arch_compute and the `arch` CLI."""

from __future__ import annotations

import json
import math
import os
import stat
import sys
from collections import Counter
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import arch_rooms as AR             # noqa: E402
from engine.source import arch_walls as AW             # noqa: E402
from engine.source import coverage_census as CS        # noqa: E402
from tools import arch_intake as AI                    # noqa: E402
from tools import arch_synth as AS                     # noqa: E402
from tools import dwg_adapter as DA                    # noqa: E402
from tools import urban_boq_m9 as M9                   # noqa: E402
from tools import urban_intake as UI                   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
METHOD = "ARCH_TAKEOFF_V1"
TOL = 1e-6


@pytest.fixture(scope="module")
def stairs(tmp_path_factory):
    p = tmp_path_factory.mktemp("stairs") / "stairs.dxf"
    AS.stairs(p)
    room, arch, _E = M9.arch_compute(str(p), method=METHOD)
    return room, arch


def _flights(arch, floor, code):
    r = next(r for r in arch["rooms"] if r["floor"] == floor and code in r["codes"])
    return r, (r.get("symbols_inside") or {}).get("stair_flights") or []


def _lines(room, floor, item, name=None):
    return [ln for ln in room["lines"] if ln["location"]["floor"] == floor and ln["item_code"] == item and
            (name is None or ln["location"]["room_name_en"] == name)]


# ---- text sources: the Arabic (101) keyboard of an SHX big font
def test_keyboard_layout_is_one_to_one_and_decodes_by_hand():
    assert len(AI.KEYBOARD_AR101) == 34 and AI.KEYBOARD_AR101["b"] == "لا"
    # hand: m = teh marbuta, comma = waw, n = alef maksura, period = zain (the keys after the lam-alef key)
    assert [AI.KEYBOARD_AR101[k] for k in "nm,./`"] == ["ى", "ة", "و", "ز", "ظ", "ذ"]
    assert AI.decode_text("yvtm k,l", "xarb.shx") == ("غرفة نوم", "SHX_KEYBOARD")
    assert AI.decode_text("plhl", "XARB.SHX") == ("حمام", "SHX_KEYBOARD")
    assert AI.decode_text("plhl", "x-arab1b.shx")[1] == "SHX_UNMAPPED"        # never guessed
    assert AI.decode_text("BATH", "romans.shx") == ("BATH", "UNICODE")


# ---- metamorphic: the same plan through other entity encodings gives the same takeoff
def _takeoff(path, variant):
    AS.villa(path, variant=variant)
    room, arch, _E = M9.arch_compute(str(path), method=METHOD)
    rooms = sorted((r["floor"], "/".join(r["codes"]), r["class"], round(r["area_m2"], 6), len(r["doors"]),
                    len(r["windows"]), len(r["passages"])) for r in arch["rooms"])
    ops = sorted((o["floor"], o["kind"], round(o["width_m"], 4)) for o in arch["openings"])
    lines = sorted((ln["location"]["floor"], ln["item_code"], ln["evidence_state"], ln["measured_net"])
                   for ln in room["lines"])
    return rooms, ops, lines


@pytest.mark.parametrize("variant", ["NESTED_MIRRORED_DOORS", "ATTRIB_LABELS", "SHX_ARABIC"])
def test_entity_encodings_do_not_change_the_takeoff(tmp_path, variant):
    base = _takeoff(tmp_path / "base.dxf", None)
    got = _takeoff(tmp_path / f"{variant}.dxf", variant)
    assert got == base
    # and the base is the hand truth of S2: four GF rooms by their words, four doors, four windows
    rooms = {(f, c) for f, c, *_ in base[0]}
    assert {("GF", "LIVING"), ("GF", "BEDROOM"), ("GF", "BATHROOM"), ("GF", "KITCHEN")} <= rooms
    assert Counter((f, k) for f, k, _ in base[1])[("GF", "DOOR")] == 4


def test_the_shx_variant_really_holds_keyboard_text(tmp_path):
    p = tmp_path / "shx.dxf"
    AS.villa(p, variant="SHX_ARABIC")
    rep = AI.read_arch(p, unit_m=0.001)["report"]
    assert rep["texts"].get("SHX_KEYBOARD") == 1                               # the GF bedroom word
    doc = ezdxf.readfile(str(p))
    assert any(t.dxf.text == "yvtm k,l" for t in doc.modelspace().query("TEXT"))


# ---- entity normalisation against analytic values
@pytest.fixture(scope="module")
def ents(tmp_path_factory):
    p = tmp_path_factory.mktemp("ents") / "entities.dxf"
    t = AS.entities(p)
    E = UI.read(str(p))
    return p, t["truth"], E, AI.read_arch(p, unit_m=E["unit_m"])


def test_minsert_places_every_cell_and_attrib_mtext_are_texts(ents):
    _p, truth, E, A = ents
    cols = [s for s in E["segments"] if s["kind"] == "LWPOLYLINE" and s["path"] and s["path"][0].startswith("D")]
    assert len(cols) == 4 * truth["minsert_columns"]
    assert {(t["value"], t["kind"]) for t in A["texts"]} == {(truth["attrib"], "ATTRIB"), (truth["mtext"], "MTEXT")}


def test_ellipses_reach_the_architectural_route_as_chords(ents):
    _p, truth, E, _A = ents
    assert E["intake_findings"].get("NON_UNIFORM_SCALE_CURVE") == 1           # the stretched arc, never silent
    ch = AI.ellipse_chords(E["ellipses"], E["unit_m"])
    by = Counter()
    for s in ch:
        by[s["id"].split("~")[0]] += math.dist(s["a"], s["b"])
    full, quarter = sorted(by.values(), reverse=True)
    assert full == pytest.approx(truth["ellipse_full_mm"], rel=5e-4)          # Ramanujan perimeter of 2000 x 1000
    assert quarter == pytest.approx(truth["ellipse_full_mm"] / 4, rel=5e-4)   # a quarter of the same ellipse
    for s in ch:                                                              # every chord within 1 mm sagitta
        assert math.dist(s["a"], s["b"]) <= 2 * math.sqrt(2 * 2000 * 1.0) + 1e-6


def test_mline_spline_polyline_are_read_with_their_lengths(ents):
    p, truth, _E, A = ents
    by = Counter()
    for s in A["extra_segments"]:
        by[s["layer"]] += math.dist(s["a"], s["b"])
    assert by["P"] == pytest.approx(truth["polyline_perimeter_mm"], abs=1e-6)
    assert by["M"] == pytest.approx(2 * (4000 + 3000), abs=5.0)              # two element lines, mitred corner
    doc = ezdxf.readfile(str(p))
    ref = list(doc.modelspace().query("SPLINE")[0].construction_tool().flattening(0.01))
    exact = sum(math.dist(a, b) for a, b in zip(ref, ref[1:]))
    assert by["S"] == pytest.approx(exact, rel=1e-3)                          # 1 mm chords vs a 0.01 mm reference


# ---- stairs: straight, curved, a dog-leg on one layer; footprints out of the porcelain; two plans
def test_flights_and_their_tread_polygons(stairs):
    T = AS.ST_TRUTH
    _r, liv = _flights(stairs[1], "GF", "LIVING")
    _r, st = _flights(stairs[1], "GF", "STAIR")
    assert [(f["kind"], f["tread_lines"]) for f in liv] == [("STRAIGHT", T["living_flight"]["lines"])]
    assert sorted((f["kind"], f["tread_lines"]) for f in st) == [("RADIAL", 9), ("STRAIGHT", 7), ("STRAIGHT", 7)]
    fan = next(f for f in st if f["kind"] == "RADIAL")
    assert sum(fan["tread_areas_m2"]) == pytest.approx(T["fan"]["tread_m2"], abs=1e-5)
    assert sum(fan["step_widths_m"]) == pytest.approx(T["fan"]["step_lm"], abs=1e-5)
    assert fan["sweep_deg"] == pytest.approx(T["fan"]["sweep_deg"], abs=1e-3)
    assert fan["r_in_m"] == pytest.approx(0.5, abs=1e-4) and fan["r_out_m"] == pytest.approx(1.7, abs=1e-4)
    for f in st:
        if f["kind"] == "STRAIGHT":
            assert sum(f["tread_areas_m2"]) == pytest.approx(T["leg"]["tread_m2"], abs=1e-6)
            assert f["going_m"] == pytest.approx(0.30, abs=1e-6)


def test_the_two_legs_on_one_layer_are_two_flights():
    legs = [{"id": f"L{i}", "layer": "A-STAIR", "a": a, "b": b} for i, (a, b) in enumerate(AS.LEG_A + AS.LEG_B)]
    got = AR.tread_flights(legs, 0.001)
    assert sorted(f["tread_lines"] for f in got) == [7, 7]                    # interleaved 50 mm: still two runs


def test_radial_recogniser_is_rotation_invariant_and_refuses_non_fans():
    def fan(theta0, cx=5000.0, cy=-3000.0):
        return [{"id": f"F{k}", "layer": "S", "a": (cx + 500 * math.cos(math.radians(theta0 + 15 * k)),
                                                    cy + 500 * math.sin(math.radians(theta0 + 15 * k))),
                 "b": (cx + 1700 * math.cos(math.radians(theta0 + 15 * k)),
                       cy + 1700 * math.sin(math.radians(theta0 + 15 * k)))} for k in range(9)]
    for t in (0, 33, 200, 351):
        got = AR.radial_flights(fan(t), 0.001)
        assert len(got) == 1 and sum(got[0]["tread_areas_m2"]) == pytest.approx(AS.ST_TRUTH["fan"]["tread_m2"], abs=1e-5)
    tangent = [{"id": f"T{k}", "layer": "S", "a": (500 * math.cos(a) - 800 * math.sin(a), 500 * math.sin(a) +
                                                   800 * math.cos(a)),
                "b": (500 * math.cos(a) + 800 * math.sin(a), 500 * math.sin(a) - 800 * math.cos(a))}
               for k in range(9) for a in [math.radians(20 * k)]]                 # tangent to a circle: no centre
    assert AR.radial_flights(tangent, 0.001) == []
    parallel = [{"id": f"P{k}", "layer": "S", "a": (0, 300 * k), "b": (1200, 300 * k)} for k in range(9)]
    assert AR.radial_flights(parallel, 0.001) == []


def test_stair_lines_and_the_porcelain_deduction(stairs):
    room, _arch = stairs
    T = AS.ST_TRUTH
    por = _lines(room, "GF", "FIN.FLOOR.PORCELAIN", "Living / saloon")[0]
    assert por["measured_net"] == pytest.approx(T["living_floor_m2"], abs=TOL)   # UP-STAIR-005
    assert any(d["what"].startswith("stair treads") for d in por["deductions"])
    ceil = _lines(room, "GF", "FIN.CEILING", "Living / saloon")[0]
    assert ceil["measured_net"] == pytest.approx(T["living_gross_m2"] - 3 * AS.COL_A, abs=TOL)  # a ceiling keeps it
    gf_tread = sum(ln["measured_net"] for ln in _lines(room, "GF", "FIN.MARBLE.TREAD"))
    assert gf_tread == pytest.approx(T["living_flight"]["tread_m2"] + T["fan"]["tread_m2"] + 2 * T["leg"]["tread_m2"],
                                     abs=1e-5)
    gf_steps = sum(ln["measured_net"] for ln in _lines(room, "GF", "FIN.STAIR.STEP_LM"))
    assert gf_steps == pytest.approx(T["living_flight"]["step_lm"] + T["fan"]["step_lm"] + 2 * T["leg"]["step_lm"],
                                     abs=1e-5)
    assert {ln["evidence_state"] for ln in _lines(room, "GF", "FIN.MARBLE.RISER")} == {"BLOCKED_RFI"}  # no riser
    land = _lines(room, "GF", "FIN.MARBLE.LANDING")[0]
    assert land["evidence_state"] == "BOUNDED_EXPOSURE"
    assert land["bounded_range"]["high"] == pytest.approx(
        T["stair_room_m2"] - T["fan"]["tread_m2"] - 2 * T["leg"]["tread_m2"], abs=1e-5)


def test_two_plans_count_a_void_seen_stair_once_and_a_stacked_flight_twice(stairs):
    room, arch = stairs
    T = AS.ST_TRUTH
    c = arch["run"]["cross_plan_stairs"][0]
    assert c["state"] == "ALIGNED" and (c["offset"]["dx"], c["offset"]["dy"]) == (40000.0, 0.0)
    assert c["offset"]["votes"] == 3
    assert sorted(r["reading"] for r in c["repeats"]) == ["SEEN_THROUGH_VOID", "STACKED", "STACKED"]
    up = _lines(room, "1F", "FIN.MARBLE.TREAD")
    seen = [ln for ln in up if ln["evidence_state"] == "BOUNDED_EXPOSURE"]
    assert len(seen) == 1 and seen[0]["bounded_range"]["high"] == pytest.approx(T["fan"]["tread_m2"], abs=1e-5)
    assert seen[0]["bounded_range"]["low"] == 0.0
    counted = [ln for ln in up if ln["evidence_state"] == "PROVISIONAL"]
    assert sum(ln["measured_net"] for ln in counted) == pytest.approx(2 * T["leg"]["tread_m2"], abs=1e-6)
    assert all("STAIR_STACKED_FLIGHT_ASSUMED" in ln["notes"] for ln in counted)
    reasons = [u["reason"] for u in room["unresolved"] if u["floor"] == "1F"]
    assert sum(r.startswith("STAIR_STACKED_FLIGHT_ASSUMED") for r in reasons) == 2
    assert sum(r.startswith("STAIR_DRAWN_ON_TWO_PLANS") for r in reasons) == 1


def test_floor_offset_from_the_column_grid():
    cols = [(0, 0, 400, 400), (5000, 0, 5400, 400), (0, 7000, 400, 7400), (9000, 3000, 9400, 3400)]
    moved = [(x0 + 12345, y0 - 678, x1 + 12345, y1 - 678) for x0, y0, x1, y1 in cols[:3]]   # one column fewer above
    off = AR.floor_offset(cols, moved, 0.001)
    assert (off["dx"], off["dy"], off["votes"]) == (12345, -678, 3)
    assert AR.floor_offset(cols, [(1, 2, 3, 4)], 0.001) is None                 # one column votes for nothing


# ---- walls and the room graph (the S2 villa, hand truth)
@pytest.fixture(scope="module")
def villa(tmp_path_factory):
    p = tmp_path_factory.mktemp("villa3") / "villa.dxf"
    AS.villa(p)
    room, arch, _E = M9.arch_compute(str(p), method=METHOD)
    return room, arch


def test_wall_plan_area_is_conserved_and_has_one_thickness(villa):
    room, arch = villa
    gf = next(w for w in arch["walls"] if w["floor"] == "GF")
    # hand: plate 12.4 x 9.4 - the four rooms' gross faces - the doorway pieces (opening widths x 0.20)
    rooms = 66.0 + 2.8 * 4.8 + 2.8 * 2.4 + 2.8 * 6.4
    doorways = (0.9 + 0.8 + 0.9 + 1.0 + 1.5 + 1.5 + 1.5 + 0.6) * 0.2
    assert gf["conservation"]["wall_faces_m2"] == pytest.approx(12.4 * 9.4 - rooms - doorways, abs=1e-6)
    assert gf["conservation"]["junction_m2"] >= -1e-9
    # the three 0.4 x 0.4 columns and the strips between the two glazing lines of the four windows are thin faces,
    # never wall mass: 3 x 0.16 m2 and (1.5 + 1.5 + 1.5 + 0.6) x 0.2 / 3
    assert gf["conservation"]["thin_faces_not_wall_m2"] == {"COLUMN": pytest.approx(0.48, abs=1e-6),
                                                            "WINDOW": pytest.approx(5.1 * 0.2 / 3, abs=1e-6)}
    assert gf["conservation"]["band_strips_m2"] + gf["conservation"]["junction_m2"] == \
        pytest.approx(gf["conservation"]["wall_faces_m2"], abs=1e-6)
    assert {f["family"] for f in gf["by_thickness"]} == {"0.20"}
    run = _lines(room, "GF", "ARCH.WALL_RUN")
    assert len(run) == 1 and run[0]["measured_net"] == pytest.approx(gf["by_thickness"][0]["net_lm"], abs=1e-9)
    assert {ln["evidence_state"] for ln in _lines(room, "GF", "MAS.BLOCK")} == {"BLOCKED_RFI"}   # material + height


def test_room_graph_doors_windows_and_shared_walls(villa):
    _room, arch = villa
    gf = next(w for w in arch["walls"] if w["floor"] == "GF")
    name = {r["face_id"]: r["codes"][0] for r in arch["rooms"] if r["floor"] == "GF"}
    name["EXTERIOR"] = "EXTERIOR"
    edges = {tuple(sorted((name[e["a"]], name[e["b"]]))): e for e in gf["graph"]}
    ops = {k: sorted((o["kind"], o["width_m"]) for o in e["openings"]) for k, e in edges.items()}
    assert ops[("BEDROOM", "LIVING")] == [("DOOR", 0.9)]
    assert ops[("BATHROOM", "LIVING")] == [("DOOR", 0.8)]
    assert ops[("KITCHEN", "LIVING")] == [("DOOR", 0.9)]
    assert ops[("EXTERIOR", "LIVING")] == [("DOOR", 1.0), ("WINDOW", 1.5)]
    assert ops[("BATHROOM", "EXTERIOR")] == [("WINDOW", 0.6)]
    assert edges[("BATHROOM", "KITCHEN")]["shared_wall_lm"] == {"0.20": pytest.approx(2.8, abs=1e-6)}
    assert ops[("BATHROOM", "KITCHEN")] == []


# ---- flags: every unresolved record has its terminal classification
def test_every_unresolved_record_is_flagged(stairs, villa):
    for room, _arch in (stairs, villa):
        assert room["unresolved"]
        for u in room["unresolved"]:
            assert u["cause"] in ("SOFTWARE", "SOURCE", "REVIEW"), u
            assert u["module_function"] and u["next_action"] and u["reason"] and u["item"]
            assert u["location"]["floor"] and u["source_ref"]["drawing"]


def test_census_states_of_the_new_families(stairs):
    room, _arch = stairs
    rows = {r["code"]: r for r in CS.census(room["lines"], arch_run=True)}
    assert rows["B7-02"]["run_state"] == "QUANTIFIED" and rows["B7-06"]["run_state"] == "QUANTIFIED"
    assert rows["B7-03"]["run_state"] == "BLOCKED"                           # the riser height is not in a plan
    assert rows["B7-04"]["run_state"] == "BOUNDED_ONLY"                      # an upper bound of the landings
    assert rows["B9-01"]["run_state"] == "BLOCKED"                           # material and block height


# ---- DWG: an external converter, never a silent empty drawing
def _stub_converter(bin_dir, dxf):
    exe = bin_dir / "dwg2dxf"
    exe.write_text("#!" + sys.executable + " -I\n"
                   "import shutil, sys\n"
                   "a = sys.argv[1:]\n"
                   f"shutil.copyfile({str(dxf)!r}, a[a.index('-o') + 1])\n"
                   "print('stub dwg2dxf: Warning: synthetic conversion')\n", encoding="utf-8")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    return exe


def test_dwg_without_a_converter_is_blocked_with_the_remedy(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path / "empty"))
    dwg = tmp_path / "plan.dwg"
    dwg.write_bytes(b"AC1032" + b"\0" * 64)
    rec = DA.convert(dwg, tmp_path / "conv")
    assert rec["state"] == "BLOCKED" and "dwg2dxf" in rec["remedy"] and rec["dwg_version"]["release"] == "R2018"
    with pytest.raises(SystemExit) as ex:
        M9.main(["arch", "--drawings", str(dwg), "--out", str(tmp_path / "out"), "--method", METHOD])
    assert "DWG_CONVERSION_BLOCKED" in str(ex.value)
    rec2 = json.loads((tmp_path / "out" / "DWG_CONVERSION.json").read_text(encoding="utf-8"))
    assert rec2["conversions"][0]["state"] == "BLOCKED"


def test_dwg_through_a_converter_reaches_the_same_takeoff(tmp_path, monkeypatch):
    dxf = tmp_path / "villa.dxf"
    AS.villa(dxf)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _stub_converter(bin_dir, dxf)
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ.get("PATH", ""))
    dwg = tmp_path / "villa.dwg"
    dwg.write_bytes(b"AC1032" + b"\0" * 64)
    assert M9.main(["arch", "--drawings", str(dwg), "--out", str(tmp_path / "out"), "--method", METHOD,
                    "--no-m9-xlsx", "--no-svg"]) == 0
    rec = json.loads((tmp_path / "out" / "DWG_CONVERSION.json").read_text(encoding="utf-8"))["conversions"][0]
    assert rec["state"] == "CONVERTED" and rec["converter"] == "LIBREDWG_DWG2DXF"
    assert rec["pin_status"] == "UNREGISTERED_BUILD"                         # a stub is never a registered build
    assert rec["converter_warnings"] == 1 and rec["losses"] == []
    assert M9.main(["arch", "--drawings", str(dxf), "--out", str(tmp_path / "ref"), "--method", METHOD,
                    "--no-m9-xlsx", "--no-svg"]) == 0
    a = json.loads((tmp_path / "out" / "ARCH_ROOMS.json").read_text(encoding="utf-8"))["rooms"]
    b = json.loads((tmp_path / "ref" / "ARCH_ROOMS.json").read_text(encoding="utf-8"))["rooms"]
    assert [(r["room_id"], r["area_m2"]) for r in a] == [(r["room_id"], r["area_m2"]) for r in b]


# ---- the structural drawing joins the same workbook, route G unchanged
def test_structural_lines_join_the_architectural_run(tmp_path):
    from tools import synthetic_villa_m8 as SM8
    from tools import urban_boq_m2 as M2
    st = SM8.generate(tmp_path, 21)
    prof = tmp_path / "villa_m8_21.profile.json"
    plan = tmp_path / "villa.dxf"
    AS.villa(plan)
    V6 = str(ROOT / "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json")
    assert M9.main(["arch", "--drawings", str(plan), "--structural", str(st), "--profile", str(prof),
                    "--conventions", V6, "--as-of", "2026-01-01", "--out", str(tmp_path / "out"), "--method", METHOD,
                    "--no-svg"]) == 0
    lines = json.loads((tmp_path / "out" / "BOQ_LINES.json").read_text(encoding="utf-8"))
    s_lines = [ln for ln in lines if ln["item_code"].startswith("STR.")]
    R = M2.compute([str(st)], profile=str(prof), route="G", conventions=V6, completeness=True)
    assert sorted(ln["line_id"] for ln in s_lines) == sorted(ln["line_id"] for ln in M9.structural_lines(R))
    assert any(ln["item_code"] == "STR.REBAR" for ln in s_lines)              # reinforcement: its own lines
    assert any(ln["item_code"].startswith("FIN.") for ln in lines)
    assert M2.main(["run", "--drawings", str(st), "--profile", str(prof), "--route", "G", "--conventions", V6,
                    "--no-pdf", "--as-of", "2026-01-01", "--out", str(tmp_path / "m2")]) == 0
    a, b = tmp_path / "out" / "structural", tmp_path / "m2"
    fa = sorted(p.relative_to(a).as_posix() for p in a.rglob("*") if p.is_file())
    assert fa == sorted(p.relative_to(b).as_posix() for p in b.rglob("*") if p.is_file())
    assert [f for f in fa if f != "run_log.json" and (a / f).read_bytes() != (b / f).read_bytes()] == []
    import openpyxl
    wb = openpyxl.load_workbook(tmp_path / "out" / "URBAN_ROOM_BOQ.xlsx", read_only=True)
    assert {"STRUCTURAL", "MASONRY", "MARBLE", "UNRESOLVED"} <= set(wb.sheetnames)


# ---- hygiene: the S3 files carry no client identity and only controlled Arabic
S3_FILES = ["engine/source/arch_walls.py", "engine/source/arch_rooms.py", "engine/source/arch_measure.py",
            "engine/source/plane_poly.py", "tools/arch_intake.py", "tools/dwg_adapter.py", "tools/arch_overlay.py",
            "tools/arch_synth.py", "tests/m9_s3/test_s3_takeoff.py"]


def test_s3_files_carry_no_client_identity():
    import re
    hyg = re.compile("YEARS" + r" 2013|7757-[A-Z]|(?i:als[ey]?n[ya]?an)")
    for f in S3_FILES:
        assert not hyg.search((ROOT / f).read_text(encoding="utf-8")), f


def test_a_column_in_the_wall_line_is_not_wall():
    band = {"u": (1.0, 0.0), "n": (0.0, 1.0)}
    cuts = AW._columns_on(band, [(1000, -100, 1400, 300), (5000, 600, 5400, 1000)], 0.0, 200.0)
    assert cuts == [(1000, 1400)]                                             # the second column stands off the wall
    assert AW._minus([(0, 4000)], cuts) == [(0, 1000), (1400, 4000)]          # 4.0 m of wall, 0.4 m of it column


def test_convex_clip_agrees_with_shapely_geos_on_random_polygons():
    """Shapely (GEOS) as a TEST-ONLY oracle (S3 adoption matrix: USE AS TEST DEPENDENCY); the engine stays stdlib."""
    shapely = pytest.importorskip("shapely.geometry")
    import random
    from engine.source import plane_poly as PP
    rnd = random.Random(20261012)
    for _ in range(300):
        n = rnd.randint(3, 12)                                   # a star-shaped (possibly concave) simple subject
        cx, cy = rnd.uniform(-5, 5), rnd.uniform(-5, 5)
        angs = sorted(rnd.uniform(0, 2 * math.pi) for _ in range(n))
        subj = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a, r in ((a, rnd.uniform(0.5, 4)) for a in angs)]
        m = rnd.randint(3, 8)                                    # a convex window, either orientation
        wa = sorted(rnd.uniform(0, 2 * math.pi) for _ in range(m))
        wx, wy, wr = rnd.uniform(-3, 3), rnd.uniform(-3, 3), rnd.uniform(1, 5)
        win = [(wx + wr * math.cos(a), wy + wr * math.sin(a)) for a in wa]
        if rnd.random() < 0.5:
            win = win[::-1]
        S, W = shapely.Polygon(subj), shapely.Polygon(win)
        if not S.is_valid or not W.is_valid:
            continue
        assert abs(PP.area(PP.clip_convex(subj, win))) == pytest.approx(S.intersection(W).area, abs=1e-9)
