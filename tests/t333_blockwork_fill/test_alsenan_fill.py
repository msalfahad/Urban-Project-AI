"""T-333 Alsenan (development villa) blockwork FILL table on ARCH_TAKEOFF_V3.0.21 from committed inputs only (the
merged T-291 ledger and register v4, the extracted V3.0.21 masonry lines, the merged T-311 component ledgers). Rebuilds
without writing and pins the results (not an accuracy claim)."""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t333"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t291"))
import t333_alsenan as A   # noqa: E402
import wall_line_ledger as R  # noqa: E402

X = A.build()
FILES = A.outputs(X)
S = json.loads(FILES["summary.json"])


def _rows(name):
    return list(csv.DictReader(io.StringIO(FILES[name])))


def test_committed_outputs_reproduce_byte_for_byte():
    for name, text in FILES.items():
        assert (HERE / name).read_text(encoding="utf-8") == text, name


def test_candidate_is_v3021_and_every_masonry_line_is_rebound_once():
    c = X["candidate"]
    assert c["candidate"] == "ARCH_TAKEOFF_V3.0.21"
    assert c["candidate_lines_json_sha256"].startswith("be22a4e4")         # T-315 r2 Gate B V3.0.21 json
    assert c["candidate_lines_csv_sha256"].startswith("3548e39c")          # and its csv
    assert c["lines_total"] == 3706
    assert len(X["new_lines"]) == 28 and X["unbound"] == []
    assert len({v["line_id"] for v in X["mapping"].values()}) == 28
    assert all(k == v["line_id"] for k, v in X["mapping"].items())        # ids stable V3.0.15 -> V3.0.21


def test_every_area_and_volume_line_is_blank_before_so_the_fill_replaces_blanks():
    av = [l for l in X["new_lines"] if l["item_code"] in ("MAS.BLOCK", "ARCH.WALL_PANEL", "ARCH.WALL_VOLUME")]
    assert len(av) == 21
    assert all(l["measured_net"] is None and l["evidence_state"] == "BLOCKED_RFI" for l in av)
    assert S["filled_lines_actions"] == {"REPLACE_BLANK": 21}


def test_every_wall_once_per_item_and_closure_zero():
    for it in ("MAS.BLOCK", "ARCH.WALL_PANEL", "ARCH.WALL_VOLUME"):
        rows = [r for r in X["rows"] if r["item_code"] == it]
        assert sorted(r["wall_id"] for r in rows) == sorted(X["walls"]) and len(rows) == 76
        assert all(abs(v) <= R.TOL for v in X["closures"][it].values())


def test_mas_block_after_totals_carry_register_v4_and_the_checker_values():
    m = S["MAS.BLOCK_m2_after"]
    assert m["verified"] == pytest.approx(297.847, abs=1e-4)
    assert m["drawing_confirmed"] == pytest.approx(48.4657, abs=1e-4)
    assert m["owner_approved"] == pytest.approx(76.2187, abs=1e-4)
    assert m["determinate"] == pytest.approx(422.5314, abs=1e-4)
    assert m["established_parts"] == pytest.approx(156.5697, abs=1e-4)
    assert m["drop_upper_at_d0"] == pytest.approx(46.8019, abs=1e-4)
    assert m["drop_coefficient_m2_per_m_of_d"] == pytest.approx(7.9131, abs=1e-4)
    ck = {c["wall_id"]: c for c in X["checker"]}
    assert set(ck) == {"1F-W20", "1F-W22", "GF-W16"}
    assert all(abs(c["difference_m2"]) <= 0.0005 for c in ck.values())
    assert ck["GF-W16"]["fill_status"] == "HELD ON DROP"


def test_volume_rows_are_area_times_thickness():
    area = {r["wall_id"]: r for r in X["rows"] if r["item_code"] == "MAS.BLOCK"}
    for r in X["rows"]:
        if r["item_code"] != "ARCH.WALL_VOLUME" or r["carried"] is None:
            continue
        assert r["carried"] == pytest.approx(area[r["wall_id"]]["carried"] * float(r["family"]), abs=1e-6)


def test_held_walls_blank_with_their_item_never_zero():
    fill = _rows("FILL_T333.csv")
    held = [r for r in fill if r["status"] == "HELD"]
    assert held and all(r["carried"] == "" and r["held_item"] for r in held)
    drop = [r for r in fill if r["status"] == "HELD ON DROP"]
    assert drop and all(r["carried"] == "" and float(r["upper_at_d0"]) > 0 and float(r["drop_coefficient"]) > 0
                        for r in drop)


def test_parapet_block_alternative_in_no_line_and_plinth_course_contained_once():
    assert S["parapet_runs"] == 24
    assert S["parapet_block_alternative_m2"] == pytest.approx([0.0, 60.596], abs=6e-4)
    assert S["plinth_course_contained_m2"] == pytest.approx(5.059, abs=6e-4)
    comps = _rows("COMPONENTS_T333.csv")
    assert all(c["line_id"] == "" for c in comps if c["kind"].startswith("ALTERNATIVE"))
    gf20 = next(l["line_id"] for l in X["new_lines"] if l["item_code"] == "MAS.BLOCK" and l["floor"] == "GF"
                and l["family"] == "0.2")
    assert {c["line_id"] for c in comps if c["kind"] == "CONTAINED" and c["low"]} == {gf20}


def test_no_coordinates_or_names_in_the_outputs():
    for name, text in FILES.items():
        assert "-186," not in text and "-798," not in text, name


def test_v3021_masonry_lines_equal_v3015_except_the_revision_identity():
    a = {l["line_id"]: l for l in json.loads((ROOT / "research/agents_t291/CANDIDATE_V3015_MASONRY_LINES.json")
                                            .read_text(encoding="utf-8"))["masonry_lines"]}
    b = {l["line_id"]: l for l in X["candidate"]["masonry_lines"]}
    assert set(a) == set(b)
    for k in a:
        for f in ("item_code", "floor", "element_id", "unit", "evidence_state", "measured_net", "bounded_range",
                  "formula", "walls_in_line", "rfi_question", "project_id"):
            assert a[k].get(f) == b[k].get(f), (k, f)
    assert {l["revision_set_sha256"][:8] for l in b.values()} == {"5e369075"}
    fill = _rows("FILL_T333.csv")
    assert {r["revision_set_sha256"][:8] for r in fill} == {"5e369075"}
