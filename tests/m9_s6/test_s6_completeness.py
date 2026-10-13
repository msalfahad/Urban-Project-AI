"""M9 S6 Phase 1 - floor-category and finish-surface completeness (ARCH_TAKEOFF_V2): every physical region part and
every eligible surface of every space ends in a measured LINE, an explicit EXCLUSION with its reason, or an RFI;
UNACCOUNTED fails the run (exit 3, nothing published, the computed lines kept as diagnostics). Doorway strips are
reviewed one by one (a window reveal is never counted as floor or excluded without its sill). Physical regions,
functional spaces and finish zones are three separate views. Nothing is assumed: the added lines carry no quantity
and no material."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import arch_completeness as AC      # noqa: E402
from engine.source import arch_rooms as AR             # noqa: E402
from tools import urban_boq_m9 as M9                   # noqa: E402

V1, V2 = "ARCH_TAKEOFF_V1", "ARCH_TAKEOFF_V2"
FACTS = Path(__file__).resolve().parents[2] / "research" / "urban_m9_s2" / "SYNTHETIC_FACTS_S2.json"


@pytest.fixture
def v2(build):
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    return M9.arch_compute(str(build("base")), method=V2, facts=facts)


def test_every_region_part_and_surface_is_accounted(v2):
    _, arch, _ = v2
    assert [c["gate"] for c in arch["coverage"]] == ["PASS", "PASS"]
    for c in arch["coverage"]:
        assert c["unaccounted"] == []
        assert {r["state"] for r in c["physical_regions"]["faces"]} <= {"LINE", "RFI", "EXCLUDED"}
        assert c["physical_regions"]["covered_m2"] == pytest.approx(c["physical_regions"]["faces_m2"], abs=0.05)
        for sp in c["functional_spaces"]:
            assert set(sp["surfaces"]) == set(AC.SURFACES)
            assert {x["state"] for x in sp["surfaces"].values()} <= {"LINE", "RFI", "EXCLUDED"}
        for r in c["physical_regions"]["faces"]:
            if r["state"] == "EXCLUDED":
                assert r["reason"] == AC.EXCLUSIONS[r["category"]]              # every exclusion says why


def test_three_views_are_kept_apart(v2):
    _, arch, _ = v2
    c = arch["coverage"][0]
    assert set(c) >= {"physical_regions", "functional_spaces", "finish_zones"}
    assert all("category" in f and "face_id" in f for f in c["physical_regions"]["faces"])
    assert all("surfaces" in s and "room_id" in s for s in c["functional_spaces"])
    assert "finish_lines" in c["finish_zones"] and "zones" in c["finish_zones"]


def test_doorway_strips_are_reviewed_one_by_one(v2):
    room, arch, _ = v2
    for fa, c in zip(arch["floor_areas"], arch["coverage"]):
        strips = fa["strips"]
        assert strips and len({s["strip_id"] for s in strips}) == len(strips)
        assert sum(s["area_m2"] for s in strips) == pytest.approx(fa["categories_m2"]["DOORWAY_STRIPS"], abs=1e-6)
        assert sum(fa["doorway_strips_by_class_m2"].values()) == pytest.approx(fa["categories_m2"]["DOORWAY_STRIPS"])
        for s in strips:
            assert s["disposition"] == "BLOCKED_RFI" and s["question"]
            if s["class"] == "WINDOW_REVEAL":
                g = s["geometry"]
                assert g["bounded_by_glazing"] and g["within_opening_box"] and g["depth_within_wall"]
                assert s["floor_status"].startswith("NOT_ESTABLISHED")             # neither floor nor excluded
            if s["class"] == "THRESHOLD":
                assert s["floor_status"] == "FLOOR (finish not established)"
    strip_lines = [ln for ln in room["lines"] if ln["item_code"] in ("ARCH.THRESHOLD", "ARCH.WINDOW_REVEAL")]
    assert strip_lines and all(ln["measured_net"] is None and ln["evidence_state"] == "BLOCKED_RFI"
                               for ln in strip_lines)
    classes = {s["class"] for fa in arch["floor_areas"] for s in fa["strips"]}
    assert {"THRESHOLD", "WINDOW_REVEAL"} <= classes


def test_surfaces_v1_left_silent_get_an_rfi_and_nothing_is_assumed(build, v2):
    room2, arch2, _ = v2
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    room1, arch1, _ = M9.arch_compute(str(build("base")), method=V1, facts=facts)
    ids1 = {ln["line_id"] for ln in room1["lines"]}
    added = [ln for ln in room2["lines"] if ln["line_id"] not in ids1]
    assert added and all(ln["measured_net"] is None for ln in added)                # no quantity is invented
    assert all(ln["evidence_state"] in ("BLOCKED_RFI", "NOT_APPLICABLE_WITH_EVIDENCE") for ln in added)
    assert room1["materials"] == room2["materials"]                                  # no material is assumed
    stair = [r for r in arch2["rooms"] if r.get("kind") == AR.STAIR]
    assert stair
    for r in stair:
        got = {ln["item_code"] for ln in added if ln["location"]["room_id"] == r["room_id"]}
        assert {"FIN.PLASTER", "FIN.PAINT", "FIN.SKIRTING"} <= got
    wet = [r for r in arch2["rooms"] if r.get("kind") == AR.WET and r["class"] in ("ROOM", "MIXED")]
    for r in wet:                                       # tile 2.4 m, finish 3.0 m: the band above has no rule
        band = [ln for ln in added if ln["location"]["room_id"] == r["room_id"] and ln["item_code"] == "FIN.PAINT"]
        assert band and band[0]["calculation"]["inputs"]["band_h_m"] == pytest.approx(0.6)


def test_full_height_wet_tile_leaves_no_band(build, tmp_path):
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    facts["wall_heights"]["*"]["WALL_TILE"]["value_m"] = 3.0
    room, arch, _ = M9.arch_compute(str(build("base")), method=V2, facts=facts)
    wet = {r["room_id"] for r in arch["rooms"] if r.get("kind") == AR.WET and r["class"] in ("ROOM", "MIXED")}
    paint = [ln for ln in room["lines"] if ln["location"]["room_id"] in wet and ln["item_code"] == "FIN.PAINT"]
    assert paint and all(ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" for ln in paint)


def test_an_exterior_space_gets_its_scope_question_and_no_finish():
    M = {"rooms": [{"room_id": "GF-X", "kind": AR.EXTERIOR, "class": "ROOM", "codes": ["GARDEN"], "area_m2": 12.0}],
         "lines": []}
    lines, unres = AC.surface_rfis({"project_id": "t", "revision_set_sha256": "0", "documents": []}, M, "GF")
    assert lines == [] and [u["item"] for u in unres] == ["ARCH.EXTERIOR"]
    assert unres[0]["reason"].startswith("EXTERIOR_FINISH_SCOPE_NOT_ESTABLISHED")


def test_an_unaccounted_surface_fails_the_run_with_exit_3(build, cli, tmp_path, monkeypatch, h):
    real = AC.coverage

    def broken(*a, **k):
        c = real(*a, **k)
        c["unaccounted"].append({"view": "PHYSICAL", "face_id": "F-TEST", "category": "TEST", "why": "injected"})
        c["gate"] = "FAIL"
        return c
    monkeypatch.setattr(AC, "coverage", broken)
    out = tmp_path / "out"
    rc, _, _ = cli("--drawings", build("base"), "--out", out, "--method", V2, "--no-svg", "--no-m9-xlsx")
    assert rc == 3
    assert not (out / "BOQ_LINES.json").exists() and not (out / "FINISH_COVERAGE.json").exists()
    F = h.read(out, "COMPLETENESS_FAILED.json")
    assert F["boq_published"] is False and F["unaccounted"][0]["face_id"] == "F-TEST"
    assert (out / "diagnostics" / "BOQ_LINES_UNPUBLISHED.json").exists()
    assert (out / "diagnostics" / "FINISH_COVERAGE.json").exists()
    D = h.read(out, "DRAWING_DISCOVERY.json")
    assert "SURFACE_UNACCOUNTED" in {f["code"] for f in D["stages"]["9_finish_zones"]["findings"]}
