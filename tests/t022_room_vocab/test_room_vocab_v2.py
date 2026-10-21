"""T-022: ROOM_VOCAB_V2 - compound room names before bare words (engine.source.room_vocab).

Hand truth, written from the meaning of each label (Kuwait villa vocabulary), not from engine output. Wet = the
owner wet codes of UP-WET-001 (BATHROOM, KITCHEN, PANTRY, IRONING, LAUNDRY). Synthetic plan (not a client drawing):
five closed rooms; areas are the inside rectangles, computed by hand below.
"""

from __future__ import annotations

import math

import pytest

from engine.source import arch_rooms as AR
from engine.source import knowledge as K
from engine.source import owner_finish_scope as OFS
from engine.source import room_vocab as RV
from tools import arch_synth as AS

# label -> (expected code, expected wet flag); None code = held (no type guessed)
HAND = {
    # Arabic only
    "حمام سباحة": ("POOL", False),               # swimming pool: V1 read it as BATHROOM (wet) - the defect
    "حمام السباحة": ("POOL", False),
    "بركة سباحة": ("POOL", False),               # V1: no room word at all
    "حوض سباحة": ("POOL", False),
    "مسبح": ("POOL", False),
    "حمام": ("BATHROOM", True),
    "حمام ماستر": ("BATHROOM", True),            # master bathroom: V1 read it as MASTER_BEDROOM (dry) - wet room lost
    "حمام ضيوف": ("BATHROOM", True),
    "حمام المسبح": ("BATHROOM", True),           # the pool's bathroom is a bathroom
    "دورة مياه": ("BATHROOM", True),
    "مطبخ تحضيري": ("PANTRY", True),             # preparation kitchen: V1 read it as KITCHEN
    "مطبخ": ("KITCHEN", True),
    "غرفة غسيل": ("LAUNDRY", True),
    "غسيل سيارات": (None, None),                 # car wash: V1 read it as LAUNDRY (wet); held, never guessed
    "غرفة مضخات": ("PLANT", False),
    "غرفة نوم ماستر": ("MASTER_BEDROOM", False),
    "ماستر": ("MASTER_BEDROOM", False),
    # English only
    "swimming pool": ("POOL", False),
    "SWIMMING BATH": ("POOL", False),            # V1: BATHROOM
    "pool pump room": ("PLANT", False),
    "POOL PLANT ROOM": ("PLANT", False),         # V1: POOL
    "POOL SHOWER": ("BATHROOM", True),
    "MASTER BATH": ("BATHROOM", True),
    "Guest W.C.": ("BATHROOM", True),
    "PREP KITCHEN": ("PANTRY", True),            # V1: KITCHEN
    "CAR WASH": (None, None),
    "BEDROOM": ("BEDROOM", False),
    # mixed Arabic + English
    "حمام سباحة SWIMMING POOL": ("POOL", False),
    "BATH حمام": ("BATHROOM", True),
    "مطبخ تحضيري PANTRY": ("PANTRY", True),
}


@pytest.mark.parametrize("label", sorted(HAND))
def test_hand_labels(label):
    code, wet = HAND[label]
    c = RV.classify(label)
    assert c["code"] == code, (label, c)
    assert c["wet"] is wet, (label, c)
    assert RV.room_word(label)[0] == code
    assert c["status"] == ("TYPED" if code else "HELD_COMPOUND")


def test_swimming_pool_is_dry_for_wet_room_scope():
    """'حمام سباحة' -> POOL: an exterior space, so no wet-room finish (porcelain / waterproofing) is applied."""
    c = RV.classify("حمام سباحة")
    assert (c["code"], c["kind"], c["wet"]) == ("POOL", AR.EXTERIOR, False)
    assert "POOL" not in K.wet_codes()


def test_missing_data_never_types_a_room():
    """nothing matched / empty / not a tag -> no code (held as an unlabelled space), never a dry default."""
    for t, status in (("", "NO_ROOM_WORD"), (None, "NO_ROOM_WORD"), ("XYZ 12", "NO_ROOM_WORD"),
                      ("2.40", "NO_ROOM_WORD"), ("حمام سباحة " + "x" * 40, "NOT_A_TAG")):
        c = RV.classify(t)
        assert (c["code"], c["wet"], c["status"]) == (None, None, status)
        assert RV.room_word(t) == (None, None)


def test_longest_compound_wins_and_ties_keep_table_order():
    # 'SWIMMING POOL' (POOL, 13 chars) and 'SWIMMING POOL PUMP' (PLANT, 18) both match: the longer phrase wins
    assert RV.room_word("SWIMMING POOL PUMP ROOM")[0] == "PLANT"
    assert RV.room_word("مضخات حمام السباحة")[0] == "PLANT"            # 'حمام السباحة' (POOL) is the shorter phrase
    assert RV.room_word("POOL PUMP")[0] == "PLANT"
    # equal length, two entries: table order decides (both patterns here name the same room, so it is stable)
    u = RV.DM.normalize("حمام المسبح").upper()
    assert RV._compound(u)[0][0] == "BATHROOM"


def test_v1_lexicon_is_unchanged():
    """ROOM_VOCAB_V1 (arch_rooms.room_word) still reads as before: frozen methods depend on it."""
    assert AR.room_word("حمام سباحة")[0] == "BATHROOM"
    assert AR.room_word("حمام ماستر")[0] == "MASTER_BEDROOM"
    assert AR.room_word("مطبخ تحضيري")[0] == "KITCHEN"
    assert AR.room_word("غسيل سيارات")[0] == "LAUNDRY"


def test_v2_differs_from_v1_only_where_a_compound_matches():
    """no type change for a label without a compound phrase: every lexicon word and the rooms-test labels."""
    plain = [w for _c, en, ar, _k, _p in AR.LEXICON for w in (en, ar)] + \
        ["LIVING", "SALOON", "W.C.", "TOILET", "SHOWER", "POWDER", "KITCHEN", "PANTRY", "MAID", "DRIVER", "STORE",
         "LOBBY", "STAIR", "LIFT", "VOID", "GARAGE", "BALCONY", "ROOF", "GARDEN", "POOL", "MASTER BEDROOM",
         "غرفة نوم", "صالة", "ديوانية", "مجلس", "ممر", "درج", "مصعد", "منور", "كراج", "سطح", "حديقة", "حوش"]
    for w in plain:
        if RV._compound(RV.DM.normalize(w).upper())[0] is None:
            assert RV.room_word(w) == AR.room_word(w), w


# ---- integration: the faces of a plan typed with ROOM_VOCAB_V2 (arch_rooms.spaces(vocab=...))
# five closed rooms, 200 mm walls, no openings; label at each room's centre. Inside areas by hand:
ROOMS = {"POOL": ((200, 200), 6000, 4000, "حمام سباحة"),          # 6.0 x 4.0 = 24.0 m2
         "MBATH": ((6400, 200), 2500, 2000, "حمام ماستر"),        # 2.5 x 2.0 = 5.0 m2
         "WASH": ((6400, 2400), 2500, 1800, "غسيل سيارات"),       # 2.5 x 1.8 = 4.5 m2
         "PREP": ((200, 4400), 3000, 2500, "مطبخ تحضيري"),        # 3.0 x 2.5 = 7.5 m2
         "PUMP": ((3400, 4400), 2000, 2000, "pool pump room")}     # 2.0 x 2.0 = 4.0 m2
OUTER = [(0, 0), (9100, 0), (9100, 7100), (0, 7100)]
V2_TRUTH = {"POOL": ("POOL", 24.0, "NONE"), "MBATH": ("BATHROOM", 5.0, "WET"), "WASH": (None, 4.5, "NONE"),
            "PREP": ("PANTRY", 7.5, "WET"), "PUMP": ("PLANT", 4.0, "DRY")}
V1_TRUTH = {"POOL": "BATHROOM", "MBATH": "MASTER_BEDROOM", "WASH": "LAUNDRY", "PREP": "KITCHEN", "PUMP": "PLANT"}


def _xf(p, mirror, quarter, scale):
    x, y = p
    if mirror:
        x = -x
    for _ in range(quarter):
        x, y = -y, x
    return (x * scale, y * scale)


def _plan(mirror=False, quarter=0, unit="mm"):
    scale = 1.0 if unit == "mm" else 0.001
    rooms, texts = {}, []
    for k, ((x, y), w, h, label) in ROOMS.items():
        rooms[k] = [_xf(q, mirror, quarter, scale) for q in ((x, y), (x + w, y), (x + w, y + h), (x, y + h))]
        texts.append((label, _xf((x + w / 2, y + h / 2), mirror, quarter, scale)))
    outer = [_xf(q, mirror, quarter, scale) for q in OUTER]
    ents = AS._s4_ents(rooms, outer, [], texts=texts)
    return ents, AS.S4_ROLES, (0.001 if unit == "mm" else 1.0), {lab: k for k, (_o, _w, _h, lab) in ROOMS.items()}


def _by_room(S, label_room, ents):
    out = {}
    for f in S["spaces"]:
        inside = [t["value"] for t in ents["texts"] if AR.MD.point_in_poly(t["x"], t["y"], f["polygon"])]
        assert len(inside) <= 1, inside
        if not inside:                       # the leftover floor between the rooms: no label, no type
            assert f["codes"] == [] and f["class"] == "UNLABELLED"
            continue
        out[label_room[inside[0]]] = f
    return out


@pytest.mark.parametrize("mirror,quarter,unit", [(False, 0, "mm"), (True, 0, "mm"), (False, 1, "mm"),
                                                 (True, 3, "m"), (False, 2, "m")])
def test_spaces_with_vocab_v2(mirror, quarter, unit):
    ents, roles, u, label_room = _plan(mirror, quarter, unit)
    S = AR.spaces(ents, roles, u, region_id="T", vocab=RV.VOCAB_ID)
    assert S["vocab"] == RV.VOCAB_ID
    rooms = _by_room(S, label_room, ents)
    assert set(rooms) == set(ROOMS)                                  # no room lost
    for k, (code, area, scope) in V2_TRUTH.items():
        f = rooms[k]
        assert f["codes"] == ([code] if code else []), (k, f["codes"])
        assert f["area_m2"] == pytest.approx(area, abs=1e-6), k
        if code is None:                                             # held: an unlabelled space with its question
            assert f["class"] == "UNLABELLED" and "UNLABELLED_SPACE" in f["issue"]
            continue
        room = {"class": f["class"], "codes": f["codes"], "kind": AR.LEX[code][2]}
        assert OFS.finish_scope(room)["scope"] == scope, k
    assert not math.isnan(sum(f["area_m2"] for f in S["spaces"]))


def test_spaces_default_is_vocab_v1_unchanged():
    ents, roles, u, label_room = _plan()
    S = AR.spaces(ents, roles, u, region_id="T")
    assert "vocab" not in S
    rooms = _by_room(S, label_room, ents)
    assert {k: (f["codes"] or [None])[0] for k, f in rooms.items()} == V1_TRUTH


def test_unknown_vocab_is_refused():
    ents, roles, u, _ = _plan()
    with pytest.raises(ValueError):
        AR.spaces(ents, roles, u, region_id="T", vocab="ROOM_VOCAB_V9")


def test_policy_record():
    r = RV.policy_record()
    assert r["id"] == "ROOM_VOCAB_V2" and r["fallback"] == "ROOM_VOCAB_V1"
    assert {c["code"] for c in r["compounds"]} == {"POOL", "PLANT", "BATHROOM", "PANTRY", None}
