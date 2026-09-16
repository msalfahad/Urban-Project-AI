"""Twelve synthetic drawings for the enclosure-role and seed classifiers.

Round 1 released a plot as a washroom. These cases exist so that a change
which re-opens that door fails here, on geometry built by hand, instead of
on a client's drawing.

The SAFETY RESULT is the point, and it is asserted on every case:

    NO site boundary, NO building envelope, NO title block and NO
    super-region may be released as a physical room.

A case may legitimately release nothing. Zero is a safe answer; a wrong
room is not.

None of these fixtures contains a string from any real project, and none
carries an expected room size — the classifiers under test are forbidden to
read an area, so a fixture that stated one would be testing nothing.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from engine.cad_fixtures import Builder

# Roles a fixture may demand, by name, so the expectation is readable.
from engine.enclosure_role import (BUILDING_ENVELOPE, PHYSICAL_ROOM,
                                   SITE_OR_PLOT, SUPER_REGION, UNRESOLVED,
                                   VOID_OR_SHAFT)
from engine.semantic_seed import (AMBIGUOUS, NON_SPACE_ANNOTATION, ROOM_LIKE)


@dataclass(frozen=True)
class Case:
    name: str
    what_it_tests: str
    decode: dict
    expect: dict


def _rect(b, x0, y0, x1, y1, layer, t=200.0):
    """A rectangle drawn as paired wall faces, outer offset by `t`."""
    b.line(x0, y0, x1, y0, layer)
    b.line(x0, y1, x1, y1, layer)
    b.line(x0, y0, x0, y1, layer)
    b.line(x1, y0, x1, y1, layer)
    b.line(x0 - t, y0 - t, x1 + t, y0 - t, layer)
    b.line(x0 - t, y1 + t, x1 + t, y1 + t, layer)
    b.line(x0 - t, y0 - t, x0 - t, y1 + t, layer)
    b.line(x1 + t, y0 - t, x1 + t, y1 + t, layer)


def _stamp(b, name, text, x, y, layer="TXT"):
    """A room-name block placed at a point — the shape of a real stamp."""
    t = b.text(text, 0, 0, 250.0, layer)
    b.block(name, [t])
    b.insert(name, x, y)


def _a_plot_with_building_and_rooms():
    b = Builder()
    _rect(b, 0, 0, 30000, 15000, "OUTER")              # plot
    _rect(b, 4000, 3000, 20000, 12000, "FABRIC")       # building
    b.line(12000, 3000, 12000, 12000, "FABRIC")        # partition
    b.line(12200, 3000, 12200, 12000, "FABRIC")
    _stamp(b, "S1", "ALPHA", 8000, 7000)
    _stamp(b, "S2", "BETA", 16000, 7000)
    return Case("A_PLOT_BUILDING_ROOMS",
                "a plot holds a building which holds two rooms. Neither the "
                "plot nor the building may release as a room",
                b.build(), {"no_room_release_for_roles":
                            [SITE_OR_PLOT, BUILDING_ENVELOPE, SUPER_REGION]})


def _b_envelope_four_rooms():
    b = Builder()
    _rect(b, 0, 0, 20000, 10000, "FABRIC")
    b.line(10000, 0, 10000, 10000, "FABRIC")
    b.line(10200, 0, 10200, 10000, "FABRIC")
    b.line(0, 5000, 20000, 5000, "FABRIC")
    b.line(0, 5200, 20000, 5200, "FABRIC")
    for n, (x, y) in enumerate(
            ((5000, 2500), (15000, 2500), (5000, 7500), (15000, 7500)), 1):
        _stamp(b, f"R{n}", f"ROOM{n}", x, y)
    return Case("B_ENVELOPE_FOUR_ROOMS",
                "an envelope containing four labelled rooms separated by "
                "partitions is never one room",
                b.build(), {"no_room_release_for_roles":
                            [BUILDING_ENVELOPE, SUPER_REGION, SITE_OR_PLOT]})


def _c_label_inside_site_only():
    """The round-1 failure in miniature.

    A stray room label lands on the plot, outside the building. The site is
    only distinguishable from a room because the drawing shows what a site
    contains — a building, with its own labelled rooms. A lone rectangle
    with one name in it is genuinely indistinguishable from a room, and a
    fixture that asserted otherwise would be asserting a size test.
    """
    b = Builder()
    _rect(b, 0, 0, 30000, 15000, "OUTER")
    _rect(b, 4000, 3000, 20000, 12000, "FABRIC")
    b.line(12000, 3000, 12000, 12000, "FABRIC")
    b.line(12200, 3000, 12200, 12000, "FABRIC")
    _stamp(b, "S1", "ALPHA", 8000, 7000)
    _stamp(b, "S2", "BETA", 16000, 7000)
    _stamp(b, "S3", "GAMMA", 25000, 13500)      # the stray one, on the plot
    return Case("C_ROOM_LABEL_INSIDE_SITE_POLYGON",
                "a room label strays onto the SITE, outside the building. "
                "The site must not become that room — round 1's exact "
                "failure, and the assertion is on RELEASE, not on the role",
                b.build(), {"site_must_not_release": True,
                            "labels_that_must_not_release": ["GAMMA"],
                            "released_labels": ["ALPHA", "BETA"]})


def _d_two_labels_one_envelope():
    b = Builder()
    _rect(b, 0, 0, 16000, 9000, "FABRIC")
    b.line(8000, 0, 8000, 9000, "FABRIC")
    b.line(8200, 0, 8200, 9000, "FABRIC")
    _stamp(b, "S1", "DELTA", 4000, 4500)
    _stamp(b, "S2", "EPSILON", 12000, 4500)
    return Case("D_TWO_LABELS_ONE_ENVELOPE",
                "two labels with drawn material between them: the outer "
                "enclosure is a super-region, not a room",
                b.build(), {"no_room_release_for_roles":
                            [SUPER_REGION, BUILDING_ENVELOPE, SITE_OR_PLOT]})


def _e_open_plan_two_zones():
    """One space, two labels, NO material between them."""
    b = Builder()
    _rect(b, 0, 0, 16000, 9000, "FABRIC")
    _stamp(b, "S1", "ZETA", 4000, 4500)
    _stamp(b, "S2", "ETA", 12000, 4500)
    return Case("E_OPEN_PLAN_TWO_ZONES",
                "one physical space carrying two functional-zone labels and "
                "NO partition between them. It is not a super-region — the "
                "separating-material test is what tells them apart",
                b.build(), {"separating_partitions": 0,
                            "not_role": SUPER_REGION})


def _f_closed_courtyard():
    b = Builder()
    _rect(b, 0, 0, 20000, 14000, "FABRIC")
    _rect(b, 7000, 5000, 13000, 9000, "FABRIC")
    _stamp(b, "S1", "THETA", 3000, 3000)
    return Case("F_CLOSED_COURTYARD",
                "an enclosure inside an enclosure: the outer one contains "
                "another and cannot be a leaf space",
                b.build(), {"outer_contains_nested": True})


def _g_shaft_in_building():
    b = Builder()
    _rect(b, 0, 0, 18000, 10000, "FABRIC")
    _rect(b, 8000, 4000, 9500, 6000, "FABRIC")
    _stamp(b, "S1", "IOTA", 3000, 5000)
    return Case("G_SHAFT_INSIDE_BUILDING",
                "a small unlabelled enclosure is a void or shaft, never a "
                "room, because it carries no room-like observation",
                b.build(), {"expect_role_present": VOID_OR_SHAFT})


def _h_annotation_text_inside_room():
    b = Builder()
    _rect(b, 0, 0, 6000, 4000, "FABRIC")
    _stamp(b, "S1", "KAPPA", 3000, 2000)
    _stamp(b, "LV", "+0.15", 4500, 3000)          # a level mark
    return Case("H_ANNOTATION_TEXT_INSIDE_ROOM",
                "a level mark inside a room is a measurement, not a second "
                "room. The numeric test removes it without knowing what a "
                "level mark is called",
                b.build(), {"non_space_texts": ["+0.15"],
                            "room_like_texts": ["KAPPA"]})


def _i_title_block_rectangle():
    b = Builder()
    _rect(b, 0, 0, 40000, 28000, "FRAME")
    b.text("SOMETHING PLAN 1:100", 20000, 1500, 500.0, "FRAME")
    _stamp(b, "S1", "LAMBDA", 10000, 10000)
    return Case("I_TITLE_BLOCK_RECTANGLE",
                "a frame round a drawing carrying a scale ratio. The title "
                "is not a room name and the frame is not a room",
                b.build(), {"non_space_texts": ["SOMETHING PLAN 1:100"],
                            "frame_must_not_release": True})


def _j_room_through_a_door():
    b = Builder()
    # Two rooms sharing a partition interrupted by a 900 mm opening.
    _rect(b, 0, 0, 14000, 8000, "FABRIC")
    b.line(7000, 0, 7000, 3550, "FABRIC")
    b.line(7000, 4450, 7000, 8000, "FABRIC")
    b.line(7200, 0, 7200, 3550, "FABRIC")
    b.line(7200, 4450, 7200, 8000, "FABRIC")
    _stamp(b, "S1", "MU", 3500, 4000)
    _stamp(b, "S2", "NU", 10500, 4000)
    return Case("J_ROOMS_CONNECTED_THROUGH_A_DOOR",
                "two rooms joined by an opening. The partition still counts "
                "as separating material, so the outer enclosure is not one "
                "room — a doorway does not merge two spaces",
                b.build(), {"no_room_release_for_roles":
                            [SUPER_REGION, BUILDING_ENVELOPE, SITE_OR_PLOT]})


def _k_room_with_no_label():
    b = Builder()
    _rect(b, 0, 0, 5000, 4000, "FABRIC")
    return Case("K_ROOM_WITH_NO_LABEL",
                "a closed space with nothing named inside it. It is a void "
                "or shaft — not a room, and equally not a failure",
                b.build(), {"expect_role_present": VOID_OR_SHAFT,
                            "room_like_texts": []})


def _l_label_with_no_enclosure():
    b = Builder()
    b.line(0, 0, 9000, 0, "FABRIC")          # a single wall, nothing closed
    b.line(0, 200, 9000, 200, "FABRIC")
    _stamp(b, "S1", "XI", 4500, 3000)
    return Case("L_LABEL_WITH_NO_VALID_ENCLOSURE",
                "a room-like label with no enclosure around it releases "
                "nothing. A name is evidence for identity and never for a "
                "boundary",
                b.build(), {"releases_nothing": True,
                            "room_like_texts": ["XI"]})


def cases() -> list:
    return [_a_plot_with_building_and_rooms(), _b_envelope_four_rooms(),
            _c_label_inside_site_only(), _d_two_labels_one_envelope(),
            _e_open_plan_two_zones(), _f_closed_courtyard(),
            _g_shaft_in_building(), _h_annotation_text_inside_room(),
            _i_title_block_rectangle(), _j_room_through_a_door(),
            _k_room_with_no_label(), _l_label_with_no_enclosure()]


def freeze_hash() -> str:
    rows = sorted(f"{c.name}|{sorted(c.expect.items(), key=str)}"
                  for c in cases())
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()[:24]
