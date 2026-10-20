"""T-131: ARCH_TAKEOFF_V3.0, the one opt-in candidate (engine.source.arch_v30), on synthetic drawings only (no client
drawing). Hand calculations:

PASSAGE VILLA (mm, one ground-floor plan; walls 0.20): outer face 12.40 x 9.40 m -> walked outline 2 x (12.40 + 9.40)
= 43.60 m (UP-FACADE-001: openings included). A 1.20 m wide unlabelled strip x 6.20..7.40, y 0.20..5.00 opens to the
south through a doorless 1.20 m gap (PASSAGE) with nothing drawn across it; a STORE room closes it at y 5.20.
FACADE_PASSAGE_WALLS_V1: mouth 1.20 m out; the strip's building faces in: 4.80 (west) + 4.80 (east) + 1.20 (north)
+ 0.20 + 0.20 (the two jamb faces of the 0.20 m wall band at the mouth) = 11.20 m; delta = 11.20 - 1.20 = 10.00 m.
  no decision        -> the roof is not read: HELD range 43.60 .. 53.60 m (BOUNDED_EXPOSURE), the opening line stays;
  owner Q-67 A bound (condition evidenced) -> 53.60 m, the mouth is NOT_A_BUILDING_OPENING.
Mirrored, a quarter turn and metres: the same numbers.

STRAP (structural, one sheet): closed footing A x 0..2.00, y 0..2.00; footing B x 6.00..8.00, y 0..2.00 drawn as an
OPEN outline (its west side broken 0.70 .. 1.30 where the strap enters). Strap faces y 0.75 / 1.25 (drawn 0.50), x
1.00 .. 7.00; printed section 50 x 40. Centre line 6.00 m = 1.00 in A (left to the footing) + 4.00 clear + 1.00 in
the open outline of B. Clear 4.00 x 0.50 x 0.40 = 0.800 m3 (route line had 1.000); held [0, 1.00 x 0.50 x 0.40 =
0.200] m3 as its own line, never 0 in the measured line. Drawn 0.53 vs printed 0.50 -> the piece holds the strap
(Q-16): the route line stays. Rotated 30 deg, mirrored, metres: the same numbers.
"""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30                     # noqa: E402
from engine.source import boq_line as BL                      # noqa: E402
from tools import arch_synth as AS                            # noqa: E402
from tools import urban_boq_m9 as M9                          # noqa: E402

PID = "synthetic-passage-villa"
WALKED, DELTA = 43.60, 10.00


# ------------------------------------------------------------------------------------------------ drawings
def _passage_villa(path, *, mirror=False, quarter_turns=0, metres=False):
    import ezdxf
    rooms = {"LIVING": [(200, 200), (6000, 200), (6000, 9200), (200, 9200)],
             "STRIP": [(6200, 200), (7400, 200), (7400, 5000), (6200, 5000)],
             "STORE": [(6200, 5200), (7400, 5200), (7400, 9200), (6200, 9200)],
             "BEDROOM": [(7600, 200), (12200, 200), (12200, 9200), (7600, 9200)]}
    outer = [(0, 0), (12400, 0), (12400, 9400), (0, 9400)]
    labels = {"LIVING": (3000, 3000), "STORE": (6800, 7000), "BEDROOM": (9800, 6000)}
    words = {k: k for k in labels}
    openings = [("DOOR", "y", 0, 200, 2000, 3000, (3000, 200, 90, 1, 1)),
                ("PASSAGE", "y", 0, 200, 6200, 7400, None),
                ("DOOR", "x", 6000, 6200, 6000, 6900, (6200, 6000, 0, 1, 1)),
                ("WINDOW", "x", 12200, 12400, 3000, 4500, None)]
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    blk = doc.blocks.new("DOOR1000")
    blk.add_line((0, 0), (1000, 0), dxfattribs={"layer": "0"})
    blk.add_arc((0, 0), 1000, 0, 90, dxfattribs={"layer": "0"})
    msp = doc.modelspace()
    (x0, y0), (x1, y1), org, title = AS.FRAMES["GF"]
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": "A-FRAME"})
    msp.add_text(title, dxfattribs={"layer": "A-TITLE", "height": 500}).set_placement((x0 + 2000, y0 + 1500))
    AS._plan(msp, rooms=rooms, outer=outer, labels=labels, words=words, openings=openings, columns=(), level="+0.00",
             treads=(), origin=org, dx=0.0, dy=0.0, mirror=mirror, quarter_turns=quarter_turns)
    mm = path.with_suffix(".mm.dxf")
    doc.saveas(str(mm))
    if not metres:
        return mm
    from ezdxf.math import Matrix44
    d2 = ezdxf.readfile(str(mm))
    d2.header["$INSUNITS"] = 6
    for e in d2.modelspace():
        e.transform(Matrix44.scale(0.001, 0.001, 0.001))
    d2.saveas(str(path))
    return path


def _decisions(path, *, project=PID, evidence=True):
    d = {"question": "Q-67", "answer": "A", "conditional": True, "binds": "PASSAGE_SINGLE_OPEN_MOUTH_EXTERIOR",
         "floors": ["GF"], "condition": "open to outside air without enclosing doors or glazing"}
    if evidence:
        d["condition_evidence"] = {"task": "synthetic", "finding": "nothing drawn across the mouth"}
    path.write_text(json.dumps({"schema": A30.DECISIONS_SCHEMA, "project": project, "decisions": [d]}),
                    encoding="utf-8")
    return path


def _run(dxf, out, method, *extra):
    argv = ["arch", "--drawings", str(dxf), "--out", str(out), "--method", method, "--no-svg", "--no-m9-xlsx",
            "--project", PID] + list(extra)
    assert M9.main(argv) == 0
    return out


def _lines(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _by(lines, code, floor="GF"):
    return [ln for ln in lines if ln["item_code"] == code and ln["location"]["floor"] == floor]


VARIANTS = [{}, {"mirror": True}, {"quarter_turns": 1}, {"metres": True}]


# ------------------------------------------------------------------------------------------------ passage, end to end
@pytest.mark.parametrize("variant", VARIANTS)
def test_passage_held_as_a_range_without_a_decision_and_base_unchanged(tmp_path, variant):
    dxf = _passage_villa(tmp_path / "p.dxf", **variant)
    b = _run(dxf, tmp_path / "v213", "ARCH_TAKEOFF_V2.13")
    c = _run(dxf, tmp_path / "v30", "ARCH_TAKEOFF_V3.0")
    # the base outputs of the V3.0 run are the V2.13 run's, byte for byte
    for f in sorted(p.name for p in b.iterdir()):
        assert (c / f).read_bytes() == (b / f).read_bytes(), f
    base, cand = _lines(b / "BOQ_LINES.json"), _lines(c / "V3_0_BOQ_LINES.json")
    [run] = [ln for ln in _by(cand, "ARCH.FACADE_RUN") if ln["location"]["element_id"].endswith(":facade")]
    [brun] = [ln for ln in _by(base, "ARCH.FACADE_RUN") if ln["location"]["element_id"].endswith(":facade")]
    assert abs(brun["measured_net"] - WALKED) < 1e-6
    assert run["line_id"] == brun["line_id"] and run["evidence_state"] == "BOUNDED_EXPOSURE"
    assert run["measured_net"] is None
    assert abs(run["bounded_range"]["low"] - WALKED) < 1e-6 and abs(run["bounded_range"]["high"] - WALKED - DELTA) < 1e-6
    assert "PASSAGE_NOT_SETTLED" in run["rfi"]["question"]
    # every line the pieces do not name is the base line itself
    changed = {ln["line_id"] for ln in cand if ln != next(x for x in base if x["line_id"] == ln["line_id"])}
    assert {x["item_code"] for x in cand if x["line_id"] in changed} <= {"ARCH.FACADE_RUN", "ARCH.FACADE"}
    assert len(cand) == len(base)
    assert [x for x in _by(cand, "ARCH.PASSAGE")] == [x for x in _by(base, "ARCH.PASSAGE")]
    rec = json.loads((c / "V3_0_RUN.json").read_text(encoding="utf-8"))
    assert rec["released_default"] is False and rec["base_method"] == "ARCH_TAKEOFF_V2.13"
    assert rec["identity"]["unchanged"] == rec["identity"]["unchanged_identical"] == len(base) - len(changed)


@pytest.mark.parametrize("variant", [{}, {"mirror": True}, {"metres": True}])
def test_passage_released_by_the_bound_owner_decision(tmp_path, variant):
    dxf = _passage_villa(tmp_path / "p.dxf", **variant)
    c = _run(dxf, tmp_path / "v30", "ARCH_TAKEOFF_V3.0", "--v30-decisions", str(_decisions(tmp_path / "d.json")))
    cand = _lines(c / "V3_0_BOQ_LINES.json")
    base = _lines(c / "BOQ_LINES.json")
    [run] = [ln for ln in _by(cand, "ARCH.FACADE_RUN") if ln["location"]["element_id"].endswith(":facade")]
    [brun] = [ln for ln in _by(base, "ARCH.FACADE_RUN") if ln["line_id"] == run["line_id"]]
    assert run["evidence_state"] == brun["evidence_state"] and abs(run["measured_net"] - WALKED - DELTA) < 1e-6
    v = run["calculation"]["inputs"]["v3_0"]
    assert abs(v["geometric_perimeter_m"] - 53.6) < 1e-6 and v["billable_run_m"] == v["geometric_perimeter_m"]
    assert v["decision"]["question"] == "Q-67"
    mouth = [ln for ln in _by(cand, "ARCH.PASSAGE") if ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE"]
    assert len(mouth) == 1 and "NOT_A_BUILDING_OPENING" in mouth[0]["notes"]
    assert len(_by(base, "ARCH.PASSAGE")) == len(_by(cand, "ARCH.PASSAGE"))
    led = json.loads((c / "V3_0_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    [row] = [r for r in led["rows"] if r["item_code"] == "ARCH.FACADE_RUN"]
    assert abs(row["before_base_v2_13"]["value"] - WALKED) < 1e-6 and abs(row["change"]["delta"] - DELTA) < 1e-6
    assert row["verification"]["task"] == "T-109" and row["verification"]["merge_commit"] == "4fddf74"
    assert row["verification"]["condition_check"]["task"] == "T-123"
    assert row["rollback"].startswith("run the released ARCH_TAKEOFF_V2.9")
    assert any(h["what"].startswith("Q-64 B") for h in row["held"])
    assert {d["item_code"] for d in row["downstream"]} >= {"ARCH.PASSAGE"}


@pytest.mark.parametrize("kw,why", [({"project": "another-project"}, "OTHER_PROJECT"),
                                    ({"evidence": False}, "CONDITION_NOT_EVIDENCED")])
def test_a_decision_for_another_project_or_without_its_condition_check_binds_nothing(tmp_path, kw, why):
    dxf = _passage_villa(tmp_path / "p.dxf")
    c = _run(dxf, tmp_path / "v30", "ARCH_TAKEOFF_V3.0", "--v30-decisions",
             str(_decisions(tmp_path / "d.json", **kw)))
    [run] = [ln for ln in _by(_lines(c / "V3_0_BOQ_LINES.json"), "ARCH.FACADE_RUN")
             if ln["location"]["element_id"].endswith(":facade")]
    assert run["evidence_state"] == "BOUNDED_EXPOSURE"
    rec = json.loads((c / "V3_0_RUN.json").read_text(encoding="utf-8"))
    assert rec["decisions"]["used"] == [] and rec["decisions"]["refused"][0]["refused"].startswith(why)


def test_villa_without_passage_stair_or_strap_is_the_base_run(tmp_path):
    AS.villa(tmp_path / "villa.dxf")
    b = _run(tmp_path / "villa.dxf", tmp_path / "v213", "ARCH_TAKEOFF_V2.13")
    c = _run(tmp_path / "villa.dxf", tmp_path / "v30", "ARCH_TAKEOFF_V3.0")
    assert _lines(c / "V3_0_BOQ_LINES.json") == _lines(b / "BOQ_LINES.json")
    rec = json.loads((c / "V3_0_RUN.json").read_text(encoding="utf-8"))
    assert rec["identity"]["replaced"] == rec["identity"]["added"] == 0
    assert rec["piece_logs"][0]["state"] == "NO_STRUCTURAL_DRAWING"


def test_the_v2_13_family_and_the_method_list_are_untouched():
    assert M9.ARCH_METHODS[-1] == "ARCH_TAKEOFF_V2.13" and M9.V30 not in M9.ARCH_METHODS
    assert M9.CANDIDATE_METHODS == ("ARCH_TAKEOFF_V3.0",)
    with pytest.raises(SystemExit):
        M9.arch_compute("x.dxf", method=M9.V30)                     # only the CLI builds the candidate


def test_v30_options_need_the_candidate(tmp_path):
    dxf = _passage_villa(tmp_path / "p.dxf")
    with pytest.raises(SystemExit):
        M9.main(["arch", "--drawings", str(dxf), "--out", str(tmp_path / "o"), "--method", "ARCH_TAKEOFF_V2.13",
                 "--v30-decisions", str(_decisions(tmp_path / "d.json"))])


# ------------------------------------------------------------------------------------------------ straps
def _xf(p, deg, mirror, scale):
    x, y = p
    if mirror:
        x = -x
    a = math.radians(deg)
    return ((x * math.cos(a) - y * math.sin(a)) * scale, (x * math.sin(a) + y * math.cos(a)) * scale)


def _strap_dxf(path, *, deg=0.0, mirror=False, metres=False, drawn_w=0.50):
    import ezdxf
    s = 1.0 if metres else 1000.0
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6 if metres else 4
    msp = doc.modelspace()
    X = lambda p: _xf(p, deg, mirror, s)                             # noqa: E731
    msp.add_lwpolyline([X(p) for p in ((0, 0), (2, 0), (2, 2), (0, 2))], close=True, dxfattribs={"layer": "S-FTG"})
    # footing B, open: its west side is broken 0.70 .. 1.30 where the strap enters
    msp.add_lwpolyline([X(p) for p in ((6, 1.30), (6, 2), (8, 2), (8, 0), (6, 0), (6, 0.70))], close=False,
                       dxfattribs={"layer": "S-FTG"})
    y0, y1 = 1.0 - drawn_w / 2, 1.0 + drawn_w / 2
    f1 = msp.add_line(X((1, y0)), X((7, y0)), dxfattribs={"layer": "S-FTG"})
    f2 = msp.add_line(X((1, y1)), X((7, y1)), dxfattribs={"layer": "S-FTG"})
    doc.saveas(str(path))
    return path, [f"D1:{int(f1.dxf.handle, 16)}:0", f"D1:{int(f2.dxf.handle, 16)}:0"], (0.001 if not metres else 1.0)


def _route(handles, unit_m):
    band = {"band_id": "BAND0001", "family": "STRAP_BEAM", "mark": "SB1", "handles": handles, "state": "BOUND",
            "schedule_width_m": 0.50, "depth_m": 0.40, "schedule_source": "INSERT 1", "alternatives": []}
    return {"generic": {"D": {"unit_m": unit_m, "sheets": {"SH1": {"straps": {"layers": ["S-FTG"], "bands": [band]}}}}}}


def _strap_line(value=1.0):
    item = {"item_id": "P-C:GROUND_BEAMS:FOUNDATION:BAND0001", "trade": "CONCRETE", "family": "GROUND_BEAMS",
            "storey": "FOUNDATION", "category": "PROVISIONAL", "unit": "m3", "low": value, "base": value, "high": value,
            "source": "synthetic strap faces", "dimensions": {"width_m": 0.5, "clear_length_m": 5.0, "depth_m": 0.4},
            "formula": "net plan x H", "assumptions": [], "support": "SOURCE_COMPLETE_UNREVIEWED", "limitations": ""}
    return BL.from_route_g(item, project_id=PID, revision_set_sha256="0" * 64, conventions_set="SYNTH",
                           conventions_digest="0" * 64, documents=[{"file": "s.dxf", "sha256": "0"}])


@pytest.mark.parametrize("variant", [{}, {"deg": 30.0}, {"mirror": True}, {"metres": True},
                                     {"deg": -121.0, "mirror": True, "metres": True}])
def test_strap_clear_length_at_the_printed_section_and_the_open_outline_part_held(tmp_path, variant):
    dxf, handles, u = _strap_dxf(tmp_path / "s.dxf", **variant)
    base = [_strap_line()]
    ch, log = A30.strap_changes(_route(handles, u), dxf, base)
    assert log["state"] == "RUN" and [b["state"] for b in log["bands"]] == ["CHANGED"]
    rep = [c for c in ch if c["action"] == "REPLACE"]
    add = [c for c in ch if c["action"] == "ADD"]
    assert len(rep) == 1 and len(add) == 1
    a = rep[0]["after"]
    assert a["line_id"] == base[0]["line_id"] and abs(a["measured_net"] - 0.800) < 1e-6
    i = a["calculation"]["inputs"]
    assert abs(i["clear_length_m"] - 4.0) < 1e-6 and abs(i["in_footing_m"] - 1.0) < 1e-6
    assert abs(i["in_open_outline_m"] - 1.0) < 1e-6
    h = add[0]["after"]
    assert h["evidence_state"] == "BOUNDED_EXPOSURE" and h["measured_net"] is None
    assert h["bounded_range"]["low"] == 0.0 and abs(h["bounded_range"]["high"] - 0.200) < 1e-6
    lines, ident = A30.integrate(base, ch)
    assert ident["replaced"] == 1 and ident["added"] == 1 and len(lines) == 2
    BL.validate(lines[0])
    BL.validate(lines[1])


def test_strap_drawn_width_off_the_printed_width_keeps_the_route_line(tmp_path):
    dxf, handles, u = _strap_dxf(tmp_path / "s.dxf", drawn_w=0.53)
    ch, log = A30.strap_changes(_route(handles, u), dxf, [_strap_line()])
    assert ch == [] and log["bands"][0]["state"] == "KEPT_PIECE_HELD"
    assert log["bands"][0]["why"] == "STRAP_WIDTH_CONFLICT"


def test_strap_without_structural_drawing_or_line_changes_nothing(tmp_path):
    assert A30.strap_changes(None, None, [])[1]["state"] == "NO_STRUCTURAL_DRAWING"
    dxf, handles, u = _strap_dxf(tmp_path / "s.dxf")
    assert A30.strap_changes(_route(handles, u), dxf, [])[1]["state"] == "NO_STRAP_LINE"


# ------------------------------------------------------------------------------------------------ stair adapter
def _floor_line(room_id, net):
    return BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code="FIN.FLOOR.PORCELAIN", unit="m2",
                        evidence_state="SOURCE_DERIVED", approval_state="MACHINE_ONLY", measured_net=net,
                        element_id=f"{room_id}:floor", floor="1F", room_id=room_id, physical_element="floor",
                        formula="room face net", inputs={}, documents=[{"file": "x.dxf", "sha256": "0"}],
                        geometry_source="SYNTHETIC_FIXTURE", geometry_confidence="TOLERANCE_CERTIFIED",
                        rule_id="UP-FLOOR", rule_version="1", rule_set="synthetic", rule_set_digest="0" * 64,
                        material_state="BY_SPEC")


@pytest.mark.parametrize("rec,state,value,rng", [
    ({"scope": "STAIR_PASSES_THROUGH_SLAB", "status": "HELD_RANGE", "floor_net_low_m2": 38.0,
      "floor_net_high_m2": 38.5, "held": [{"category": "STAIR_FOOT_UNSETTLED", "m2": 0.5}]},
     "BOUNDED_EXPOSURE", None, (38.0, 38.5)),
    ({"scope": "STAIR_IN_FACE", "status": "RELEASED", "floor_net_low_m2": 41.25, "floor_net_high_m2": 41.25},
     "SOURCE_DERIVED", 41.25, None),
    ({"scope": "NO_STAIR_NO_VOID", "status": "RELEASED", "floor_net_low_m2": 44.0, "floor_net_high_m2": 44.0},
     None, None, None),
    ({"scope": "STAIR_PASSES_THROUGH_SLAB", "status": "HELD", "floor_net_low_m2": None, "floor_net_high_m2": None},
     None, None, None)])
def test_stair_residue_becomes_a_range_never_one_value(monkeypatch, rec, state, value, rng):
    from engine.source import stair_floor_residue as SFR
    monkeypatch.setattr(SFR, "face_residue", lambda *a, **k: dict(rec, policy="STAIR_FLOOR_RESIDUE_V1"))
    ln = _floor_line("1F-R1", 44.0)
    room_boq = {"lines": [ln], "materials": [{"method": "TILE_RECT_EXACT_V1", "line_id": ln["line_id"],
                                              "net_installed_m2": 44.0}]}
    arch = {"run": {"unit_m": 0.001}, "rooms": [{"room_id": "1F-R1", "floor": "1F"}], "openings": []}
    ch, log = A30.stair_changes(room_boq, arch, {"segments": [], "arcs": []})
    if state is None:
        assert ch == [] and log["rooms"][0]["state"].startswith("KEPT")
        return
    [c] = ch
    a = c["after"]
    assert a["line_id"] == ln["line_id"] and a["evidence_state"] == state
    if rng:
        assert a["measured_net"] is None and (a["bounded_range"]["low"], a["bounded_range"]["high"]) == rng
    else:
        assert a["measured_net"] == value
    assert c["downstream"][0]["v3_0"].startswith("STALE")
    BL.validate(a)


# ------------------------------------------------------------------------------------------------ integrate
def test_integrate_keeps_every_other_line_and_refuses_double_or_unknown_changes():
    a, b = _floor_line("1F-A", 10.0), _floor_line("1F-B", 20.0)
    a2 = copy.deepcopy(a)
    a2["measured_net"] = 9.0
    lines, ident = A30.integrate([a, b], [A30._change("STAIR_FLOOR_RESIDUE", "REPLACE", a, a2)])
    assert lines[0]["measured_net"] == 9.0 and lines[1] is b
    assert ident["unchanged"] == ident["unchanged_identical"] == 1
    with pytest.raises(ValueError):
        A30.integrate([a, b], [A30._change("STAIR_FLOOR_RESIDUE", "REPLACE", a, a2)] * 2)
    c = _floor_line("1F-C", 1.0)
    with pytest.raises(ValueError):
        A30.integrate([a, b], [A30._change("STAIR_FLOOR_RESIDUE", "REPLACE", c, c)])
    with pytest.raises(ValueError):
        A30.integrate([a, b], [A30._change("STRAPS", "ADD", None, b)])


def test_ledger_lists_released_before_and_lines_not_in_the_released_run():
    a = _floor_line("1F-A", 10.0)
    a2 = copy.deepcopy(a)
    a2["measured_net"] = 9.0
    led = A30.ledger([A30._change("STAIR_FLOOR_RESIDUE", "REPLACE", a, a2)], released_lines=[a])
    r = led["rows"][0]
    assert r["before_released_v2_9"]["value"] == 10.0 and r["change"] == {"delta": -1.0, "pct": -10.0}
    led = A30.ledger([A30._change("STAIR_FLOOR_RESIDUE", "REPLACE", a, a2)], released_lines=[])
    assert led["rows"][0]["before_released_v2_9"]["state"] == "NOT_IN_RELEASED"
    assert led["released_default"] is False
