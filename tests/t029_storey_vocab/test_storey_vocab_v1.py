"""T-029: STOREY_VOCAB_V1 - storey titles in English and Arabic, ordered by level; an unrecognised plan title holds
its sheet (engine.source.storey_vocab, arch_plan.plan_regions(storey_vocab=...), discovery.region_findings).

Hand truth, written from the meaning of each title, not from engine output. Synthetic drawing (not a client drawing):
four sheet frames 30 x 20 m, each holding the same two-room plan (200 mm walls) and one title; room areas are the
inside rectangles, computed by hand below.
"""

from __future__ import annotations

import pytest

from engine.source import arch_plan as AP
from engine.source import arch_rooms as AR
from engine.source import discovery as DS
from engine.source import storey_vocab as SV
from tools import arch_synth as AS

# title -> expected storey id, or "HELD" (plan-like, no storey), "NOT_A_PLAN", "NOT_A_TITLE"
HAND = {
    # English only
    "GROUND FLOOR PLAN": "GF",                    # V1 already
    "1ST FL. PLAN": "1F",                         # V1: nothing (FL. abbreviation)
    "First Floor Plan": "1F",
    "2ND FLOOR PLAN": "2F",
    "FOURTH FLOOR PLAN": "4F",                    # V1: nothing (no 4F)
    "4TH FLOOR PLAN": "4F",
    "10TH FLOOR PLAN": "10F",
    "MEZZANINE FLOOR PLAN": "MEZZANINE",          # V1 already
    "MEZANINE PLAN": "MEZZANINE",                 # common misspelling
    "BASEMENT PLAN": "BASEMENT",
    "ROOF ANNEX PLAN": "ROOF",                    # the roof annex is the ROOF storey, as V1's 'الملحق'
    "ROOF PLAN": "ROOF",
    "PENTHOUSE PLAN": "HELD",                     # penthouse vs roof annex: not decided here -> held
    "LEVEL 00": "HELD",                           # level numbering convention not decided -> held
    "GROUND FL. PLAN": "GF",                      # V1: nothing (FL. abbreviation)
    "11TH FLOOR PLAN": "HELD",                    # beyond the table -> held, never read as 1F
    "SECTION A-A": "NOT_A_PLAN",
    "SOUTH ELEVATION": "NOT_A_PLAN",
    "SITE PLAN": "NOT_A_PLAN",
    "KEY PLAN": "NOT_A_PLAN",
    "LEVEL +3.20": "NOT_A_TITLE",                 # a level mark, not a title
    "KITCHEN": "NOT_A_TITLE",
    # Arabic only
    "الدور الأرضي": "GF",
    "الطابق الأرضي": "GF",                        # V1: nothing (الطابق)
    "الدور الاول": "1F",                          # alef without hamza: V1 nothing
    "مسقط الدور الأول": "1F",
    "الدور الرابع": "4F",
    "مسقط الطابق الخامس": "5F",
    "الميزانين": "MEZZANINE",
    "السرداب": "BASEMENT",
    "البدروم": "BASEMENT",
    "الملحق": "ROOF",
    "الدور الحادي عشر": "HELD",                  # eleventh: never 1F
    "مسقط الدور 4": "HELD",                       # numeral storey: not in the table -> held
    "قطاع أ-أ": "NOT_A_PLAN",
    "الواجهة الأمامية": "NOT_A_PLAN",
    # bilingual
    "FIRST FLOOR PLAN مسقط الدور الأول": "1F",
    "4TH FLOOR PLAN مسقط الدور الرابع": "4F",
}


@pytest.mark.parametrize("title", sorted(HAND))
def test_hand_titles(title):
    want = HAND[title]
    c = SV.classify(title)
    if want in ("HELD", "NOT_A_PLAN", "NOT_A_TITLE"):
        assert c["storey"] is None and c["order"] is None, (title, c)
        assert c["status"] == {"HELD": "HELD_UNRECOGNISED", "NOT_A_PLAN": "NOT_A_PLAN",
                               "NOT_A_TITLE": "NOT_A_TITLE"}[want], (title, c)
        assert SV.plan_like(title) is (want == "HELD")
    else:
        assert (c["storey"], c["status"]) == (want, "RECOGNISED"), (title, c)
        assert c["order"] == SV.ORDER[want]


def test_v1_titles_keep_their_storey():
    """every title ARCH_PLAN_V1 recognises gives the same storey id with the vocabulary (frozen runs unchanged)."""
    samples = ["BASEMENT FLOOR PLAN", "مسقط السرداب", "القبو", "GROUND FLOOR PLAN", "G.F. PLAN", "GF PLAN",
               "مسقط الدور الأرضي", "MEZZANINE PLAN", "الميزانين", "FIRST FLOOR PLAN", "1ST FLOOR PLAN",
               "1 ST. FLOOR PLAN", "مسقط الدور الأول", "SECOND FLOOR PLAN", "الدور الثاني", "THIRD FLOOR PLAN",
               "3RD FLOOR PLAN", "الدور الثالث", "ROOF PLAN", "TOP ROOF PLAN", "ROOF FLOOR PLAN", "مسقط السطح",
               "الملحق", "الدور الثاني عشر"]
    for t in samples:
        v1, _o = AP.floor_of_title(t)
        assert v1 is not None, t
        assert SV.storey_of_title(t)[:1] == (v1,), t
        assert SV.storey_of_title(t)[2] == SV.FALLBACK_ID


def test_v1_quirks_are_kept_not_fixed_here():
    """step 1 keeps every V1 reading, including two that a later slice must revisit (reported in the handoff):
    a second basement reads as BASEMENT, a lower ground floor as GF."""
    assert SV.storey_of_title("2ND BASEMENT PLAN")[:2] == ("BASEMENT", 0)
    assert SV.storey_of_title("LOWER GROUND FLOOR PLAN")[:2] == ("GF", 10)


def test_v1_reader_is_unchanged():
    """ARCH_PLAN_V1 still misses what it missed (the defect stays in the old method, fixed only on request)."""
    for t in ("1ST FL. PLAN", "4TH FLOOR PLAN", "الدور الرابع", "الدور الاول", "الطابق الأرضي"):
        assert AP.floor_of_title(t) == (None, None), t
    assert [fl for fl, _o, _p in AP.FLOOR_TITLES] == ["BASEMENT", "GF", "MEZZANINE", "1F", "2F", "3F", "ROOF"]


def test_storey_order_follows_the_building():
    seq = ["BASEMENT", "GF", "MEZZANINE"] + [f"{n}F" for n in range(1, 11)] + ["ROOF"]
    assert [SV.ORDER[s] for s in seq] == sorted(SV.ORDER[s] for s in seq)
    assert len(set(SV.ORDER.values())) == len(SV.ORDER)
    # the V1 storeys keep their relative order
    v1 = [fl for fl, _o, _p in sorted(AP.FLOOR_TITLES, key=lambda r: r[1])]
    assert [SV.ORDER[f] for f in v1] == sorted(SV.ORDER[f] for f in v1)


def test_missing_data_never_names_a_storey():
    for t in ("", None, "   ", "PLAN " + "x" * 70):
        c = SV.classify(t)
        assert c["storey"] is None and c["status"] == "NOT_A_TITLE", (t, c)


def test_policy_record():
    r = SV.policy_record()
    assert r["id"] == "STOREY_VOCAB_V1" and r["fallback"] == "ARCH_PLAN_V1"
    assert r["held_reason"] == "UNRECOGNISED_FLOOR_TITLE"
    assert [s["storey"] for s in r["storeys"]][:3] == ["BASEMENT", "GF", "MEZZANINE"]


# ---- integration: plan regions on a synthetic drawing with four titled frames ---------------------------------
FRAME_W, FRAME_H, GAP = 30000.0, 20000.0, 5000.0
# two rooms, inside rectangles (mm, plan origin = frame origin + (5000, 5000)): hand areas
ROOMS = {"A": ((200, 200), 4000, 3000, "BEDROOM"),       # 4.0 x 3.0 = 12.0 m2
         "B": ((4400, 200), 2500, 3000, "حمام")}          # 2.5 x 3.0 = 7.5 m2
OUTER = [(0, 0), (7100, 0), (7100, 3400), (0, 3400)]
AREAS = {"BEDROOM": 12.0, "حمام": 7.5}
# frame k: (title, expected V1 outcome, expected V2 outcome)
SHEETS = [("GROUND FLOOR PLAN", "GF", "GF"),
          ("1ST FL. PLAN", "OTHER", "1F"),
          ("مسقط الدور الرابع", "OTHER", "4F"),
          ("PENTHOUSE PLAN", "OTHER", "HELD"),
          ("SECTION A-A", "OTHER", "OTHER")]


def _xf(p, mirror, quarter, scale):
    x, y = p
    if mirror:
        x = -x
    for _ in range(quarter):
        x, y = -y, x
    return (x * scale, y * scale)


def _drawing(mirror=False, quarter=0, unit="mm"):
    scale = 1.0 if unit == "mm" else 0.001
    segs, texts = [], []
    for k, (title, _v1, _v2) in enumerate(SHEETS):
        ox = k * (FRAME_W + GAP)
        fr = [(ox, 0), (ox + FRAME_W, 0), (ox + FRAME_W, FRAME_H), (ox, FRAME_H)]
        for i in range(4):
            segs.append({"id": f"F{k}:{i}", "layer": "FRAME", "a": _xf(fr[i], mirror, quarter, scale),
                         "b": _xf(fr[(i + 1) % 4], mirror, quarter, scale)})
        texts.append({"id": f"TT{k}", "value": title, "height": 500.0 * scale, "layer": "TITLE",
                      **dict(zip("xy", _xf((ox + 2000, 1500), mirror, quarter, scale)))})
        if title.startswith("SECTION"):
            continue
        o = (ox + 5000, 5000)
        rooms = {r: [(o[0] + x, o[1] + y) for x, y in ((x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h))]
                 for r, ((x0, y0), w, h, _l) in ROOMS.items()}
        ents = AS._s4_ents(rooms, [(o[0] + x, o[1] + y) for x, y in OUTER], [],
                           texts=[(lab, (o[0] + x0 + w / 2, o[1] + y0 + h / 2))
                                  for _r, ((x0, y0), w, h, lab) in ROOMS.items()])
        for s in ents["segments"]:
            segs.append(dict(s, id=f"P{k}:{s['id']}", a=_xf(s["a"], mirror, quarter, scale),
                             b=_xf(s["b"], mirror, quarter, scale)))
        for t in ents["texts"]:
            x, y = _xf((t["x"], t["y"]), mirror, quarter, scale)
            texts.append(dict(t, id=f"P{k}:{t['id']}", x=x, y=y, height=200.0 * scale))
    return {"segments": segs, "arcs": [], "circles": [], "texts": texts, "inserts": [], "hatches": [],
            "unit_m": 0.001 if unit == "mm" else 1.0}


def _sheet_of(P, intake):
    """title -> outcome: the storey of its region, HELD, or OTHER."""
    out = {}
    for t in intake["texts"]:
        if t["id"].startswith("TT"):
            hit = [r["floor"] for r in P["regions"] if AP._in_box((t["x"], t["y"]), r["box"], 0)]
            held = [h for h in P.get("held_frames", []) if AP._in_box((t["x"], t["y"]), h["box"], 0)]
            out[t["value"]] = hit[0] if hit else ("HELD" if held else "OTHER")
    return out


VARIANTS = [(False, 0, "mm"), (True, 0, "mm"), (False, 1, "mm"), (True, 3, "m"), (False, 2, "m")]


@pytest.mark.parametrize("mirror,quarter,unit", VARIANTS)
def test_regions_with_storey_vocab(mirror, quarter, unit):
    E = _drawing(mirror, quarter, unit)
    P = AP.plan_regions(E, storey_vocab=SV.VOCAB_ID)
    assert P["storey_vocab"] == SV.VOCAB_ID
    assert _sheet_of(P, E) == {t: v2 for t, _v1, v2 in SHEETS}
    assert [r["floor"] for r in P["regions"]] == ["GF", "1F", "4F"]          # ordered by level
    (h,) = P["held_frames"]
    assert h["reason"] == "UNRECOGNISED_FLOOR_TITLE" and h["titles"] == ["PENTHOUSE PLAN"]
    assert len(P["other_frames"]) == 1                                       # the section only


@pytest.mark.parametrize("mirror,quarter,unit", VARIANTS)
def test_default_is_arch_plan_v1_unchanged(mirror, quarter, unit):
    E = _drawing(mirror, quarter, unit)
    P = AP.plan_regions(E)
    assert "held_frames" not in P and "storey_vocab" not in P
    assert _sheet_of(P, E) == {t: v1 for t, v1, _v2 in SHEETS}
    assert [r["order"] for r in P["regions"]] == [1]                         # V1 order numbers untouched


@pytest.mark.parametrize("mirror,quarter,unit", VARIANTS)
def test_rooms_on_a_new_storey_sheet_are_measured(mirror, quarter, unit):
    """the 1ST FL. and 4TH floor sheets (lost by V1) give their rooms with the hand areas."""
    E = _drawing(mirror, quarter, unit)
    P = AP.plan_regions(E, storey_vocab=SV.VOCAB_ID)
    for reg in P["regions"]:
        ents = AP.region_entities(E, reg["box"])
        S = AR.spaces(ents, AS.S4_ROLES, E["unit_m"], region_id=reg["region_id"])
        got = {}
        for f in S["spaces"]:
            inside = [t["value"] for t in ents["texts"] if t["value"] in AREAS
                      and AR.MD.point_in_poly(t["x"], t["y"], f["polygon"])]
            if inside:
                got[inside[0]] = f["area_m2"]
        assert set(got) == set(AREAS), (reg["floor"], got)                  # no room lost
        for lab, a in AREAS.items():
            assert got[lab] == pytest.approx(a, abs=1e-6), (reg["floor"], lab)


def test_held_sheet_reaches_the_discovery_report():
    E = _drawing()
    P = AP.plan_regions(E, storey_vocab=SV.VOCAB_ID)
    sheets, floors = DS.region_findings(P["regions"], other_frames=P["other_frames"],
                                        held_frames=P["held_frames"], titles_found=3, titles_in_frames=3)
    held = [f for f in sheets if f["code"] == "UNRECOGNISED_FLOOR_TITLE"]
    assert len(held) == 1 and held[0]["level"] == DS.REVIEW
    assert held[0]["evidence"]["titles"] == ["PENTHOUSE PLAN"]
    assert not [f for f in sheets + floors if f["level"] == DS.FATAL]
    # without held frames the findings are as before
    s0, f0 = DS.region_findings(P["regions"], other_frames=P["other_frames"], titles_found=3, titles_in_frames=3)
    assert s0 == [f for f in sheets if f["code"] != "UNRECOGNISED_FLOOR_TITLE"] and f0 == floors


def test_only_held_sheets_still_stop_the_run():
    """a drawing whose only plan title names no storey: held, and no region -> the run stops (never measured as 0)."""
    E = _drawing()
    keep = {"TT3"}
    E["texts"] = [t for t in E["texts"] if not t["id"].startswith("TT") or t["id"] in keep]
    P = AP.plan_regions(E, storey_vocab=SV.VOCAB_ID)
    assert P["regions"] == [] and len(P["held_frames"]) == 1
    sheets, floors = DS.region_findings(P["regions"], other_frames=P["other_frames"], held_frames=P["held_frames"])
    assert any(f["code"] == "NO_PLAN_REGION" and f["level"] == DS.FATAL for f in floors)


def test_unknown_storey_vocab_is_refused():
    with pytest.raises(AP.PlanError):
        AP.plan_regions(_drawing(), storey_vocab="STOREY_VOCAB_V9")
