"""T-383 on the development villa (committed T-301 ledgers + the committed waterproofing-line extract; no private
input): restated per WP line, against the T-301 WP.FOUNDATION inventory and the T-471 register."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t236"))

import wp_join_devvilla as D  # noqa: E402


def test_two_wp_lines_close_on_their_inventory_and_carry_their_whole_records():
    doc, recs, els, ls = D.run()
    assert doc["refused"] is None and doc["inventory_counts"] == {"IN_LINE": 320, "MISSING": 0, "NOT_APPLICABLE": 96}
    assert doc["wp_groups"] == 20 and doc["wp_lines"] == len(ls)
    # LIFT-01 base screed: one face 4.600 x 4.500 = 20.700 m2, x 0.05 = 1.035 m3 (Checker T-353 (e) re-measure)
    passing = [tuple(g) for g in doc["groups_passing"]]
    assert passing == [("WATERPROOFING", "WP.FOUNDATION.LIFT_PIT_SCREED", "m2"),
                       ("WATERPROOFING", "WP.FOUNDATION.LIFT_PIT_SCREED", "m3")]
    m2 = recs[passing[0]]
    assert (m2["line_qty"], m2["inventory_qty_in_line"], m2["residual"]) == (20.7, 20.7, 0.0)
    assert [x["line_id"] for x in doc["wp_whole_lines"]] == ["L-e11f17bb076058bf172d", "L-e4789d76efedbc351bd4"]
    assert doc["wp_whole_records_not_counted"] == []


def test_every_other_wp_line_is_blocked_by_a_named_cause_never_by_silence():
    doc, recs, *_r = D.run()
    held = {g[1]: r["held"] for g, r in recs.items() if g[1].startswith("WP.FOUNDATION.") and not r["t383_passes"]}
    assert held == {"WP.FOUNDATION.BURIED_LIQUID": 178, "WP.FOUNDATION.FOOTING_MEMBRANE": 1,
                    "WP.FOUNDATION.FOOTING_SCREED": 1, "WP.FOUNDATION.FOOTING_SIDES": 25,
                    "WP.FOUNDATION.LIFT_PIT_BOARD": 1, "WP.FOUNDATION.LIFT_PIT_MEMBRANE": 1,
                    "WP.FOUNDATION.PROCUREMENT": 1}
    absent = sorted(g[1] for g, r in recs.items() if r["blockers"] and r["blockers"][0].startswith("NO WP INVENTORY"))
    assert absent == ["FIN.WP.DOORWAY", "FIN.WP.DOORWAY_TRANSITION", "FIN.WP.DOORWAY_TRANSITION_NR", "FIN.WP.FLOOR",
                      "FIN.WP.MEMBRANE_ROLLS", "FIN.WP.PENETRATION", "FIN.WP.ROOF", "FIN.WP.ROOF_UPTURN",
                      "FIN.WP.TERMINATION", "FIN.WP.WALL_UPTURN"]
    assert all(r["inventory_count"] is None for g, r in recs.items() if g[1] in absent)   # blank, never 0
    assert all(r["blockers"] for r in recs.values() if not r["t383_passes"])


def test_t471_component_states_unchanged_and_inventory_named():
    doc, *_r = D.run()
    rows = {r["component_id"]: r for r in doc["components"]}
    # the T-471 V3.0.42 matrix states (same line counts), with the WP inventory status beside them
    assert {k: (r["state"], r["gate"], r["lines"], r["wp_inventory"]) for k, r in rows.items()} == {
        "C-B8-01": ("APPLICABLE_HELD", "HELD", 35, "ABSENT"), "C-B8-02": ("APPLICABLE_HELD", "HELD", 41, "ABSENT"),
        "C-B8-03": ("APPLICABLE_HELD", "HELD", 25, "ABSENT"), "C-B8-05": ("APPLICABLE_HELD", "HELD", 22, "ABSENT"),
        "C-B8-06": ("APPLICABLE_HELD", "HELD", 8, "ABSENT"), "C-B8-08": ("APPLICABLE_HELD", "HELD", 19, "INCOMPLETE")}


def test_committed_report_is_the_reproduced_one(tmp_path):
    D.main(["--out", str(tmp_path)])
    assert (tmp_path / D.OUT).read_bytes() == (D.HERE / D.OUT).read_bytes()
