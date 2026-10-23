"""T-108 MASONRY_AREA_V1: hand fixtures, NOT the development villa.

Villa "T108-B" (metres), ground storey slab top to slab top 3.60 m (printed, DRAWING-CONFIRMED), slab 0.15 m.
  WA  white 0.20 external (type ASSUMED — OWNER-APPROVED, outer = white), physical run 8.00 m:
      beam B1 20 x 60 over 5.00 m -> 3.60 - 0.60 = 3.00 m; slab only over 3.00 m -> 3.60 - 0.15 = 3.45 m.
      gross = 5.00 x 3.00 + 3.00 x 3.45 = 25.35 m2.
      window N1 1.50 x 1.20 printed, sill 0.90 (head 2.10 < 3.00) = 1.80 m2; door D1 1.00 x 2.20 (owner door height,
      ASSUMED — OWNER-APPROVED) = 2.20 m2 -> net 21.35 m2, m3 21.35 x 0.20 = 4.270.
      white units: 62.5 x 25 face 6.4 / m2 -> 136.64; 60 x 20 face 8.333 / m2 -> 177.917 (installed, no waste).
      atab (no printed lintel schedule, bearing 0.20 m given by a specification note): N1 1.50 + 0.40 = 1.90 -> 2.50 m
      piece; D1 1.00 + 0.40 = 1.40 -> 2.50 m piece.
  WB  black 0.15 internal, 4.00 m under the slab only -> 3.45 m: gross 13.80 m2; door D2 0.80 x 2.20 = 1.76 m2 ->
      net 12.04 m2, m3 1.806; black units HELD (no face size); atab NOT APPLICABLE (black).
  WC  black 0.20, 3.00 m: a beam with no printed depth over 1.00 m (HELD), beam 20 x 60 over 2.00 m (3.00 m):
      known gross 2.00 x 3.00 = 6.00 m2, held length 1.00 m, status HELD, net None (never 0).
Adverse: lengths in millimetres; a member as deep as the storey; nothing drawn above (dome opening); a HELD storey
(annex datum) -> candidate only; mirror / rotation (pieces reversed) changes nothing; a printed lintel schedule makes
atab NOT APPLICABLE (never both); an atab longer than 4.00 m HELD; white 0.10 m has no 60 x 20 face; a glazed line
whose pieces cover the architectural run but whose physical run is only the solid piers; totals never sum HELD."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import masonry_area_v1 as M                 # noqa: E402

DC, AOA, HELD = M.DC, M.AOA, M.HELD
GF = {"floor_to_floor_m": 3.60, "status": DC}
B1 = {"kind": "BEAM", "mark": "B1", "depth_m": 0.60, "status": DC}
SLAB = {"kind": "SLAB", "mark": "S", "depth_m": 0.15, "status": DC}
BEAR = {"m": 0.20, "status": DC, "source": "specification note (fixture)"}


def wa(pieces=None):
    return {"id": "WA", "floor": "GF", "group": "EXTERNAL", "t_m": 0.20, "block_type": "WHITE", "type_status": AOA,
            "physical_length_m": 8.00, "length_status": DC,
            "pieces": pieces or [{"length_m": 5.00, "member": B1}, {"length_m": 3.00, "member": SLAB}]}


N1 = {"id": "N1", "kind": "WINDOW", "width_m": 1.50, "width_status": DC, "height_m": 1.20, "height_status": DC,
      "sill_m": 0.90, "in_gross": True, "frame": True, "faces": ("INTERNAL_PLASTER_PAINT", "EXTERNAL_PLASTER_PAINT")}
D1 = {"id": "D1", "kind": "DOOR", "width_m": 1.00, "width_status": DC, "height_m": 2.20, "height_status": AOA,
      "in_gross": True, "frame": True, "faces": ("INTERNAL_PLASTER_PAINT", "EXTERNAL_PLASTER_PAINT")}


def test_heights_follow_the_member_above_q60a():
    assert M.piece_height(GF, B1)[0] == pytest.approx(3.00)
    assert M.piece_height(GF, SLAB)[0] == pytest.approx(3.45)


def test_white_wall_gross_net_m3_units_atab():
    x = M.wall_ledger(wa(), GF, [N1, D1], printed_lintel_schedule=False, bearing=BEAR)
    assert x["gross_m2"] == pytest.approx(25.35)
    assert x["gross_status"] == DC
    assert x["deducted_m2"] == pytest.approx(4.00)
    assert x["net_m2"] == pytest.approx(21.35)
    assert x["net_status"] == AOA                       # the door height is the owner fallback
    assert x["net_m3"] == pytest.approx(4.27)
    assert x["units"]["62.5x25"]["units"] == pytest.approx(136.64)
    assert x["units"]["60x20"]["units"] == pytest.approx(177.917, abs=1e-3)
    assert x["units"]["62.5x25"]["status"] == AOA
    at = {a["opening"]: a for a in x["atab"]}
    assert at["N1"]["need_m"] == pytest.approx(1.90) and at["N1"]["piece_m"] == 2.50
    assert at["D1"]["need_m"] == pytest.approx(1.40) and at["D1"]["piece_m"] == 2.50
    assert x["adhesive"]["status"] == HELD


def test_black_wall_units_held_and_no_atab():
    wb = {"id": "WB", "floor": "GF", "group": "INTERNAL", "t_m": 0.15, "block_type": "BLACK", "type_status": AOA,
          "physical_length_m": 4.00, "length_status": DC, "pieces": [{"length_m": 4.00, "member": SLAB}]}
    d2 = dict(D1, id="D2", width_m=0.80, faces=("INTERNAL_PLASTER_PAINT", "INTERNAL_PLASTER_PAINT"))
    x = M.wall_ledger(wb, GF, [d2], bearing=BEAR)
    assert x["gross_m2"] == pytest.approx(13.80)
    assert x["net_m2"] == pytest.approx(12.04)
    assert x["net_m3"] == pytest.approx(1.806)
    assert x["units"]["black"]["units"] is None and x["units"]["black"]["status"] == HELD
    assert x["atab"][0]["status"] == "NOT_APPLICABLE"


def test_beam_without_printed_depth_holds_the_wall_never_zero():
    held_beam = {"kind": "BEAM", "mark": "(none)", "depth_m": None, "status": HELD}
    wc = {"id": "WC", "floor": "GF", "group": "INTERNAL", "t_m": 0.20, "block_type": "BLACK", "type_status": AOA,
          "physical_length_m": 3.00, "length_status": DC,
          "pieces": [{"length_m": 1.00, "member": held_beam}, {"length_m": 2.00, "member": B1}]}
    big = dict(D1, id="D9", width_m=3.00)                 # 6.60 m2 > the known 6.00: may lie in the held part
    x = M.wall_ledger(wc, GF, [big])
    assert x["net_candidate_m2"] is None                  # no candidate net with a held length (no false refusal)
    assert x["gross_m2"] == pytest.approx(6.00)          # the known part only
    assert x["gross"]["held_length_m"] == pytest.approx(1.00)
    assert x["gross_status"] == HELD and x["net_status"] == HELD
    assert x["net_m2"] is None and x["net_m3"] is None


def test_nothing_drawn_above_is_held():
    dome = {"kind": "NONE", "status": HELD}
    w = wa([{"length_m": 8.00, "member": dome}])
    x = M.wall_ledger(w, GF)
    assert x["net_m2"] is None and x["gross_status"] == HELD
    assert x["gross"]["held_length_m"] == pytest.approx(8.00)


def test_held_storey_gives_a_candidate_not_a_quantity():
    annex = {"floor_to_floor_m": 3.60, "status": HELD}
    x = M.wall_ledger(wa(), annex, [N1])
    assert x["net_candidate_m2"] == pytest.approx(25.35 - 1.80)
    assert x["net_m2"] is None and x["net_status"] == HELD


def test_mirror_and_rotation_change_nothing():
    a = M.wall_ledger(wa(), GF, [N1, D1])
    b = M.wall_ledger(wa([{"length_m": 3.00, "member": SLAB}, {"length_m": 5.00, "member": B1}]), GF, [D1, N1])
    assert a["gross_m2"] == pytest.approx(b["gross_m2"]) and a["net_m2"] == pytest.approx(b["net_m2"])


def test_pieces_scaled_to_the_run():
    # samples stop 0.10 m short of each node (8.00 - 0.20 sampled): the weighted height is applied to the run
    w = wa([{"length_m": 4.90, "member": B1}, {"length_m": 2.90, "member": SLAB}])
    x = M.wall_ledger(w, GF)
    hw = (4.90 * 3.00 + 2.90 * 3.45) / 7.80
    assert x["gross_m2"] == pytest.approx(8.00 * hw)


def test_glazed_line_physical_run_only():
    # architectural run 7.00 m, glazing span 6.30 m out (Q-69 B): physical blockwork 0.70 m under a 0.60 beam
    w = dict(wa([{"length_m": 7.00, "member": B1}]), physical_length_m=0.70, arch_length_m=7.00)
    x = M.wall_ledger(w, GF)
    assert x["gross_m2"] == pytest.approx(0.70 * 3.00)


def test_printed_lintel_schedule_wins_over_atab():
    x = M.wall_ledger(wa(), GF, [N1], printed_lintel_schedule=True, bearing=BEAR)
    assert x["atab"][0]["status"] == "NOT_APPLICABLE"
    assert "schedule" in x["atab"][0]["why"]


def test_atab_without_bearing_or_too_long_is_held():
    x = M.wall_ledger(wa(), GF, [N1])
    assert x["atab"][0]["status"] == HELD                 # no bearing source: never a default
    wide = dict(N1, id="N3", width_m=3.80)
    y = M.wall_ledger(wa(), GF, [wide], bearing=BEAR)
    assert y["atab"][0]["status"] == HELD and y["atab"][0]["need_m"] == pytest.approx(4.20)


def test_thin_white_wall_has_no_60x20_face():
    w = dict(wa(), t_m=0.10)
    x = M.wall_ledger(w, GF)
    assert x["units"]["60x20"]["status"] == "NOT_AVAILABLE"
    assert x["units"]["62.5x25"]["units"] == pytest.approx(25.35 * 6.4)


def test_millimetres_and_impossible_depth_refused():
    with pytest.raises(ValueError):
        M.wall_ledger(wa([{"length_m": 8000, "member": B1}]), GF)
    with pytest.raises(ValueError):
        M.piece_height(GF, {"kind": "BEAM", "depth_m": 3.60, "status": DC})
    with pytest.raises(ValueError):
        M.piece_height({"floor_to_floor_m": 3600, "status": DC}, B1)
    with pytest.raises(ValueError):
        M.wall_ledger(dict(wa(), type_status="PROVISIONAL"), GF)
    with pytest.raises(ValueError):
        M.wall_ledger(dict(wa(), block_type="RED"), GF)


def test_totals_never_sum_held():
    a = M.wall_ledger(wa(), GF, [N1, D1])
    held_beam = {"kind": "BEAM", "depth_m": None, "status": HELD}
    c = M.wall_ledger(dict(wa([{"length_m": 8.00, "member": held_beam}]), id="WX"), GF)
    t = M.totals([a, c])[("GF", "WHITE", 0.20)]
    assert t["net_by_status"][AOA]["m2"] == pytest.approx(21.35)
    assert t["walls_net_held"] == 1
    assert sum(s["m2"] for s in t["net_by_status"].values()) == pytest.approx(21.35)


def test_unwired():
    assert M.policy_record()["wired"] is False
