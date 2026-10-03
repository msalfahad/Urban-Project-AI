"""Sixteen synthetic drawings for round 3's boundary authority and identity.

Round 2's cases proved nothing wrong could be RELEASED. These prove
something right can be MEASURED — and keep round 2's safety at the same
time, because a round that unlocked rooms by loosening a gate would have
undone the previous one.

The required results, checked on every case:

    a site boundary never closes an internal room
    external building walls MAY form room sides
    door openings do not leak rooms together
    open-plan zones are not invented as separate physical rooms
    bilingual equivalent labels do not create a false identity conflict
    unknown identity does not invalidate otherwise valid geometry
    no super-region releases as a room

No fixture states an expected area, because the classifiers under test are
forbidden to read one. Where a case does state a measured area it is the
arithmetic of the rectangle drawn, not a room-size prior.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from engine.cad_fixtures import Builder

WALL_T = 200.0


@dataclass(frozen=True)
class Case:
    name: str
    what_it_tests: str
    decode: dict
    expect: dict


def _ring(b, x0, y0, x1, y1, layer, t=WALL_T):
    """A closed rectangular wall drawn as inner and outer faces."""
    b.line(x0, y0, x1, y0, layer)
    b.line(x0, y1, x1, y1, layer)
    b.line(x0, y0, x0, y1, layer)
    b.line(x1, y0, x1, y1, layer)
    b.line(x0 - t, y0 - t, x1 + t, y0 - t, layer)
    b.line(x0 - t, y1 + t, x1 + t, y1 + t, layer)
    b.line(x0 - t, y0 - t, x0 - t, y1 + t, layer)
    b.line(x1 + t, y0 - t, x1 + t, y1 + t, layer)


def _partition_v(b, x, y0, y1, layer, t=WALL_T, *, gap=None):
    """A vertical partition, optionally interrupted by a doorway."""
    if gap:
        mid = (y0 + y1) / 2
        for xx in (x, x + t):
            b.line(xx, y0, xx, mid - gap / 2, layer)
            b.line(xx, mid + gap / 2, xx, y1, layer)
    else:
        b.line(x, y0, x, y1, layer)
        b.line(x + t, y0, x + t, y1, layer)


def _partition_h(b, y, x0, x1, layer, t=WALL_T, *, gap=None):
    if gap:
        mid = (x0 + x1) / 2
        for yy in (y, y + t):
            b.line(x0, yy, mid - gap / 2, yy, layer)
            b.line(mid + gap / 2, yy, x1, yy, layer)
    else:
        b.line(x0, y, x1, y, layer)
        b.line(x0, y + t, x1, y + t, layer)


def _stamp(b, block, texts, x, y, layer="TXT"):
    """A room stamp carrying one or more labels — a bilingual pair is two."""
    handles = [b.text(t, 0, i * -300.0, 250.0, layer)
               for i, t in enumerate(texts)]
    b.block(block, handles)
    b.insert(block, x, y)


# ------------------------------------------------------------------ cases

def _a_four_rooms_in_a_big_site():
    b = Builder()
    _ring(b, 0, 0, 60000, 40000, "OUTER")                 # the site
    _ring(b, 20000, 14000, 40000, 26000, "FABRIC")        # the building
    _partition_v(b, 29900, 14000, 26000, "FABRIC")
    _partition_h(b, 19900, 20000, 40000, "FABRIC")
    for n, (x, y) in enumerate(
            ((25000, 17000), (35000, 17000),
             (25000, 23000), (35000, 23000)), 1):
        _stamp(b, f"R{n}", [f"BEDROOM"], x, y)
    return Case(
        "A_FOUR_ROOMS_IN_A_MUCH_LARGER_SITE",
        "the site is vastly larger than the building. No room may be closed "
        "by the site line, and the four rooms must still measure",
        b.build(), {"site_must_not_close_a_room": True,
                    "min_released": 1})


def _b_corner_room_two_external_walls():
    b = Builder()
    _ring(b, 0, 0, 20000, 12000, "FABRIC")
    _partition_v(b, 9900, 0, 12000, "FABRIC")
    _partition_h(b, 5900, 0, 9900, "FABRIC")
    _stamp(b, "R1", ["KITCHEN"], 4500, 3000)     # corner: 2 external, 2 internal
    _stamp(b, "R2", ["STORE"], 4500, 9000)
    _stamp(b, "R3", ["OFFICE"], 15000, 6000)
    return Case(
        "B_CORNER_ROOM_TWO_EXTERNAL_TWO_INTERNAL",
        "an external building wall MUST be able to form a room side. "
        "Overcorrecting round 1 by rejecting envelope walls would make "
        "every corner room unmeasurable",
        b.build(), {"min_released": 1, "external_wall_may_close": True})


def _c_room_one_external_three_internal():
    b = Builder()
    _ring(b, 0, 0, 24000, 12000, "FABRIC")
    _partition_v(b, 7900, 0, 12000, "FABRIC")
    _partition_v(b, 15900, 0, 12000, "FABRIC")
    _partition_h(b, 5900, 7900, 15900, "FABRIC")
    _stamp(b, "R1", ["STORE"], 11900, 3000)
    _stamp(b, "R2", ["OFFICE"], 4000, 6000)
    _stamp(b, "R3", ["KITCHEN"], 20000, 6000)
    return Case(
        "C_ROOM_ONE_EXTERNAL_THREE_INTERNAL",
        "a room bounded mostly by partitions still measures",
        b.build(), {"min_released": 1})


def _d_two_rooms_with_a_doorway():
    b = Builder()
    _ring(b, 0, 0, 16000, 9000, "FABRIC")
    _partition_v(b, 7900, 0, 9000, "FABRIC", gap=900.0)
    _stamp(b, "R1", ["KITCHEN"], 4000, 4500)
    _stamp(b, "R2", ["DINING"], 12000, 4500)
    return Case(
        "D_TWO_ROOMS_SEPARATED_BY_A_DOORWAY",
        "a doorway must not leak one room into the other. Without a "
        "validated portal closing it topologically, neither room closes — "
        "which is the honest answer, not a merged super-room",
        b.build(), {"no_merged_super_room": True})


def _e_three_rooms_off_a_corridor():
    b = Builder()
    _ring(b, 0, 0, 30000, 14000, "FABRIC")
    _partition_h(b, 8900, 0, 30000, "FABRIC")
    _partition_v(b, 9900, 0, 8900, "FABRIC")
    _partition_v(b, 19900, 0, 8900, "FABRIC")
    _stamp(b, "R1", ["OFFICE"], 5000, 4500)
    _stamp(b, "R2", ["STORE"], 15000, 4500)
    _stamp(b, "R3", ["KITCHEN"], 25000, 4500)
    _stamp(b, "R4", ["CORRIDOR"], 15000, 11500)
    return Case(
        "E_THREE_ROOMS_CONNECTED_THROUGH_A_CORRIDOR",
        "three rooms and the corridor serving them are four spaces, not one",
        b.build(), {"min_released": 2, "no_merged_super_room": True})


def _f_open_plan_zones():
    b = Builder()
    _ring(b, 0, 0, 16000, 9000, "FABRIC")
    _stamp(b, "Z1", ["COOKING AREA"], 4000, 4500)
    _stamp(b, "Z2", ["DINING AREA"], 12000, 4500)
    return Case(
        "F_OPEN_PLAN_ZONES_WITH_NO_SEPARATOR",
        "two zone labels in one undivided space. Zones are not separate "
        "physical rooms and must not be invented as such",
        b.build(), {"zones_not_rooms": True})


def _g_label_inside_building_huge_site():
    b = Builder()
    _ring(b, 0, 0, 80000, 50000, "OUTER")
    _ring(b, 30000, 20000, 46000, 32000, "FABRIC")
    _partition_v(b, 37900, 20000, 32000, "FABRIC")
    _stamp(b, "R1", ["BEDROOM"], 34000, 26000)
    _stamp(b, "R2", ["BATHROOM"], 42000, 26000)
    return Case(
        "G_ROOM_LABEL_INSIDE_BUILDING_SITE_MUCH_LARGER",
        "round 1's failure at scale: the site dwarfs the building. Depth, "
        "not size, must be what keeps the flood in",
        b.build(), {"site_must_not_close_a_room": True, "min_released": 1})


def _h_courtyard_surrounded_by_rooms():
    b = Builder()
    _ring(b, 0, 0, 24000, 20000, "FABRIC")
    _ring(b, 9000, 8000, 15000, 12000, "FABRIC")          # the courtyard
    _partition_v(b, 8800, 0, 20000, "FABRIC")
    _partition_v(b, 15000, 0, 20000, "FABRIC")
    _stamp(b, "R1", ["OFFICE"], 4000, 10000)
    _stamp(b, "R2", ["STORE"], 20000, 10000)
    _stamp(b, "C1", ["COURTYARD"], 12000, 10000)
    return Case(
        "H_COURTYARD_SURROUNDED_BY_ROOMS",
        "a courtyard is an external space enclosed by fabric. The rooms "
        "beside it measure; the courtyard is not a room",
        b.build(), {"courtyard_is_external": True})


def _i_shaft_inside_room_network():
    b = Builder()
    _ring(b, 0, 0, 20000, 12000, "FABRIC")
    _partition_v(b, 9900, 0, 12000, "FABRIC")
    _ring(b, 13000, 5000, 15000, 7000, "FABRIC")          # the shaft
    _stamp(b, "R1", ["OFFICE"], 4500, 6000)
    return Case(
        "I_SHAFT_INSIDE_A_ROOM_NETWORK",
        "an unlabelled enclosure inside the fabric is a void, never a room, "
        "and the labelled room beside it still measures",
        b.build(), {"min_released": 1})


def _j_terrace_next_to_a_room():
    b = Builder()
    _ring(b, 0, 0, 14000, 10000, "FABRIC")
    _stamp(b, "R1", ["OFFICE"], 7000, 5000)
    _stamp(b, "T1", ["TERRACE"], 20000, 5000)         # outside the fabric
    return Case(
        "J_EXTERNAL_TERRACE_ADJACENT_TO_A_ROOM",
        "a terrace is an external space outside the enclosed fabric. It is "
        "a space and it is not a room",
        b.build(), {"terrace_is_external": True, "min_released": 1})


def _k_bilingual_same_room():
    b = Builder()
    _ring(b, 0, 0, 6000, 5000, "FABRIC")
    _stamp(b, "R1", ["KITCHEN", "مطبخ"], 3000, 2500)
    return Case(
        "K_BILINGUAL_LABELS_FOR_ONE_ROOM",
        "English and Arabic naming one concept is ONE identity stated "
        "twice. It must strengthen the identity, never create a conflict",
        b.build(), {"identity_relationship": "SAME_CONCEPT",
                    "identity_established": True,
                    "independent_statements": 2, "min_released": 1})


def _l_two_conflicting_labels():
    b = Builder()
    _ring(b, 0, 0, 6000, 5000, "FABRIC")
    _stamp(b, "R1", ["KITCHEN", "BEDROOM"], 3000, 2500)
    return Case(
        "L_TWO_GENUINELY_CONFLICTING_LABELS",
        "two different ROOM concepts in one place is a real contradiction. "
        "It is reported and releases nothing",
        b.build(), {"identity_relationship": "CONFLICT",
                    "identity_established": False, "releases_nothing": True})


def _m_unknown_label_in_a_valid_room():
    b = Builder()
    _ring(b, 0, 0, 6000, 5000, "FABRIC")
    _stamp(b, "R1", ["QQZZX"], 3000, 2500)
    return Case(
        "M_UNKNOWN_LABEL_INSIDE_A_VALID_ROOM",
        "§10: a valid physical room exists even when its name is UNKNOWN. "
        "Inability to read a label must not destroy correct geometry",
        b.build(), {"identity_established": False,
                    "geometry_must_be_valid": True, "min_released": 1})


def _n_valid_unlabelled_room():
    b = Builder()
    _ring(b, 0, 0, 20000, 12000, "FABRIC")
    _partition_v(b, 9900, 0, 12000, "FABRIC")
    _stamp(b, "R1", ["OFFICE"], 4500, 6000)
    return Case(
        "N_VALID_UNLABELLED_ROOM",
        "the space on the other side of the partition has no label. It is "
        "not measured because nothing seeds it, and that is not a failure",
        b.build(), {"min_released": 1})


def _o_envelope_with_several_rooms():
    b = Builder()
    _ring(b, 0, 0, 30000, 18000, "FABRIC")
    _partition_v(b, 9900, 0, 18000, "FABRIC")
    _partition_v(b, 19900, 0, 18000, "FABRIC")
    _partition_h(b, 8900, 19900, 30000, "FABRIC")
    _stamp(b, "R1", ["OFFICE"], 4500, 9000)
    _stamp(b, "R2", ["STORE"], 15000, 9000)
    _stamp(b, "R3", ["KITCHEN"], 25000, 4500)
    _stamp(b, "R4", ["BATHROOM"], 25000, 13500)
    return Case(
        "O_BUILDING_ENVELOPE_CONTAINING_SEVERAL_ROOMS",
        "the envelope holds four rooms. The rooms release; the envelope "
        "itself never does",
        b.build(), {"min_released": 2, "no_merged_super_room": True})


def _p_title_block_outside_the_building():
    b = Builder()
    _ring(b, 0, 0, 14000, 10000, "FABRIC")
    _stamp(b, "R1", ["OFFICE"], 7000, 5000)
    # A drawing frame well away from the building, with a sheet title.
    _ring(b, 30000, 0, 60000, 20000, "FRAME")
    b.text("GROUND FLOOR PLAN 1:100", 45000, 2000, 600.0, "FRAME")
    return Case(
        "P_TITLE_BLOCK_OUTSIDE_THE_BUILDING",
        "a sheet frame is not a room and its title is not a room name",
        b.build(), {"frame_releases_nothing": True, "min_released": 1})


def cases() -> list:
    return [_a_four_rooms_in_a_big_site(), _b_corner_room_two_external_walls(),
            _c_room_one_external_three_internal(), _d_two_rooms_with_a_doorway(),
            _e_three_rooms_off_a_corridor(), _f_open_plan_zones(),
            _g_label_inside_building_huge_site(),
            _h_courtyard_surrounded_by_rooms(), _i_shaft_inside_room_network(),
            _j_terrace_next_to_a_room(), _k_bilingual_same_room(),
            _l_two_conflicting_labels(), _m_unknown_label_in_a_valid_room(),
            _n_valid_unlabelled_room(), _o_envelope_with_several_rooms(),
            _p_title_block_outside_the_building()]


def freeze_hash() -> str:
    rows = sorted(f"{c.name}|{sorted(c.expect.items(), key=str)}"
                  for c in cases())
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()[:24]
