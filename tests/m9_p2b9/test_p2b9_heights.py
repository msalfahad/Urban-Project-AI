"""Phase 2B-9 acceptance: wall-finish heights read from the drawing's own evidence (ARCH_TAKEOFF_V2.8,
engine.source.arch_v28, UP-HGT-001), never from a floor-to-floor interval and never invented.

Hierarchy (rank, then scope OPENING > ROOM > FLOOR > PROJECT): element annotation 1, schedule 2, section / elevation
3, derived 3.5, floor note 4, project note 4.5, project rule (the facts) 5, Urban default 6 (always ASSUMED). Plaster
runs to the structural soffit (U/S SLAB - F.F.L.), paint to the finished ceiling (F.C.L. - F.F.L.); two governing
values more than 5 mm apart are a CONFLICT (no value); a lower-ranked disagreeing value is kept as overridden.

Truth: p2b9_truth (hand arithmetic on the example-1 room: 14.00 m run, door 1.00 x 2.20, window 1.50 x 1.20 sill
1.00)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

pytest.importorskip("ezdxf")

import p2b9_fixtures as F                                     # noqa: E402
import p2b9_run as R                                          # noqa: E402
import p2b9_truth as T                                        # noqa: E402

from engine.source import arch_v28 as AV                     # noqa: E402

A = 1e-6
VARIANTS = {
    "full": dict(evidence=F.FULL),
    "full_facts": dict(evidence=F.FULL),
    "section2_only": dict(evidence={"TAGS", "SCHEDULE", "SECTION2"}),
    "conflict": dict(evidence={"TAGS", "SCHEDULE", "SECTION", "SECTION2"}),
    "room_note_270": dict(evidence={"TAGS", "SCHEDULE", "SECTION", "ROOM_NOTE"}, room_note="C.H. 2.70"),
    "floor_note": dict(evidence={"TAGS", "FLOOR_NOTE"}),
    "sill_tag": dict(evidence={"TAGS", "SCHEDULE", "SECTION", "SILL_TAG"}),
    "none": dict(evidence=frozenset()),
    "floor_to_floor": dict(evidence={"TAGS", "SCHEDULE", "SECTION_FF"}),
}


@pytest.fixture(scope="module")
def ex1(tmp_path_factory):
    work = tmp_path_factory.mktemp("p2b9_heights")
    cache = {}

    def get(key, method=R.V28):
        if (key, method) not in cache:
            dxf = F.example1(work / f"{key}.dxf", **VARIANTS[key])
            cache[(key, method)] = R.run(dxf, work / f"o_{key}_{method}", facts=key.endswith("_facts"),
                                         method=method)
        return cache[(key, method)]
    return get


def test_section_heights_govern_the_wall_finish(ex1):
    out = ex1("full")
    h = R.room_heights(out)
    assert (h["PLASTER"]["state"], h["PLASTER"]["governing"], h["PLASTER"]["value_m"]) == ("ESTABLISHED", "SECTION",
                                                                                            T.H)
    assert "U/S SLAB" in h["PLASTER"]["authority"]
    assert (h["PAINT"]["governing"], h["PAINT"]["value_m"]) == ("SECTION", T.H) and "F.C.L." in h["PAINT"]["authority"]
    for code in ("FIN.PLASTER", "FIN.PAINT"):
        ln = R.the(out, code, "plaster" if code == "FIN.PLASTER" else "paint")
        assert ln["measured_net"] == pytest.approx(T.E1_NET, abs=A)
        assert ln["calculation"]["inputs"]["height_authority"].startswith("SECTION")
    # the project facts (rank 5: 2.10 m doors, 1.50 m windows) do not override the schedule (rank 2)
    out_f = ex1("full_facts")
    assert R.net(out_f, "FIN.PLASTER", "plaster") == pytest.approx(T.E1_NET, abs=A)
    d = R.opening(out_f, "DOOR")
    assert (d["height"]["governing"], d["height"]["value_m"]) == ("SCHEDULE", T.DOOR_H)
    assert {(x["kind"], x["value_m"]) for x in d["height"]["overridden"]} == {("PROJECT_RULE", 2.1)}


def test_paint_runs_to_the_ceiling_and_plaster_to_the_soffit(ex1):
    """a section with F.C.L. +2.80 under U/S SLAB +3.00: two heights, never one taken for the other."""
    out = ex1("section2_only")
    h = R.room_heights(out)
    assert (h["PLASTER"]["value_m"], h["PAINT"]["value_m"]) == (3.0, 2.8)
    assert R.net(out, "FIN.PLASTER", "plaster") == pytest.approx(T.E1_NET, abs=A)
    assert R.net(out, "FIN.PAINT", "paint") == pytest.approx(T.E1_PAINT_AT_280, abs=A)


def test_the_evidence_hierarchy_order(ex1):
    # 1 (element, room scope) over 3 (section, floor scope): the room's ceiling note governs its paint height
    out = ex1("room_note_270")
    h = R.room_heights(out)
    assert (h["PAINT"]["governing"], h["PAINT"]["value_m"]) == ("ELEMENT_ANNOTATION", 2.7)
    assert h["PLASTER"]["governing"] == "SECTION"            # a ceiling note is not a soffit
    assert R.net(out, "FIN.PAINT", "paint") == pytest.approx(T.E1_PAINT_AT_270, abs=A)
    # 1 (an annotation on the window) over 2 (its schedule row): SILL 0.90 governs, the schedule's 1.00 overridden
    w = R.opening(ex1("sill_tag"), "WINDOW")
    assert (w["sill"]["governing"], w["sill"]["value_m"]) == ("ELEMENT_ANNOTATION", T.E1_SILL_TAG)
    assert w["sill"]["overridden"] == [{"kind": "SCHEDULE", "scope": "OPENING", "value_m": 1.0,
                                        "difference_m": pytest.approx(0.1, abs=A)}]
    assert w["head_m"] == pytest.approx(T.E1_SILL_TAG_HEAD, abs=A)
    assert R.net(ex1("sill_tag"), "FIN.PLASTER", "plaster") == pytest.approx(T.E1_NET, abs=A)
    # 4 (a floor note) when nothing better exists: the ceiling note gives paint, but no soffit -> plaster BLOCKED
    out = ex1("floor_note")
    h = R.room_heights(out)
    assert (h["PAINT"]["governing"], h["PAINT"]["value_m"]) == ("FLOOR_NOTE", 3.0)
    assert h["PLASTER"]["state"] == "BLOCKED" and h["PLASTER"]["value_m"] is None
    w = R.opening(out, "WINDOW")
    assert (w["sill"]["governing"], w["sill"]["value_m"]) == ("FLOOR_NOTE", 1.0)
    assert w["height"]["value_m"] is None and w["area_m2"] is None
    # 6 (the Urban default) only for a door without a schedule row, and labelled assumed
    d = R.opening(out, "DOOR")
    assert (d["height"]["governing"], d["area_state"]) == ("URBAN_DEFAULT", "ASSUMED_HEIGHT")


def test_a_same_rank_conflict_holds_the_value(ex1):
    out = ex1("conflict")
    h = R.room_heights(out)
    assert h["PAINT"]["state"] == "CONFLICT" and h["PAINT"]["value_m"] is None
    assert "2.800" in h["PAINT"]["why"][0] and "3.000" in h["PAINT"]["why"][0]
    assert (h["PLASTER"]["state"], h["PLASTER"]["value_m"]) == ("ESTABLISHED", 3.0)    # both sections agree
    paint = R.the(out, "FIN.PAINT", "paint")
    assert paint["measured_net"] is None and paint["evidence_state"] == "BLOCKED_RFI"
    assert R.net(out, "FIN.PLASTER", "plaster") == pytest.approx(T.E1_NET, abs=A)
    assert [(m["quantity"], m["state"]) for m in R.missing(out)] == [("PAINT", "CONFLICT")]


def test_the_missing_evidence_report(ex1):
    out = ex1("none")
    miss = {(m.get("room") or m.get("kind"), m["quantity"]): m for m in R.missing(out)}
    assert set(miss) == {("Bedroom", "PLASTER"), ("Bedroom", "PAINT"), ("DOOR", "HEIGHT"), ("WINDOW", "HEIGHT"),
                         ("WINDOW", "SILL")}
    assert miss[("DOOR", "HEIGHT")]["governing"] == "URBAN_DEFAULT" and miss[("DOOR", "HEIGHT")]["used"] == T.DOOR_H
    for k in (("Bedroom", "PLASTER"), ("Bedroom", "PAINT"), ("WINDOW", "HEIGHT"), ("WINDOW", "SILL")):
        assert miss[k]["used"] is None and miss[k]["needed"]
    # nothing invented: no wall finish released, the window's area held
    for code, el in (("FIN.PLASTER", "plaster"), ("FIN.PAINT", "paint")):
        assert R.the(out, code, el)["measured_net"] is None
    w = R.opening(out, "WINDOW")
    assert (w["area_m2"], w["class"]) == (None, "WINDOW_SILL_NOT_ESTABLISHED")
    # a dry room needs no wall-tile height: none is asked for
    assert not any(m["quantity"] == "WALL_TILE" for m in R.missing(ex1("full")))


def test_floor_to_floor_is_never_a_wall_height(ex1):
    """a section giving only the two finished floor levels (3.60 m floor to floor): reported, never a wall height."""
    out = ex1("floor_to_floor")
    he = R.height_evidence(out)
    bands = [b for v in he["evidence"]["views"] for b in v["bands"]]
    assert [(b["ffl_m"], b["next_ffl_m"], b["floor"]) for b in bands] == [(0.0, 3.6, "GF"), (3.6, None, "1F")]
    h = R.room_heights(out)
    assert h["PLASTER"]["state"] == h["PAINT"]["state"] == "BLOCKED"
    assert R.the(out, "FIN.PLASTER", "plaster")["measured_net"] is None
    assert {(m.get("room"), m["quantity"]) for m in R.missing(out)} >= {("Bedroom", "PLASTER"), ("Bedroom", "PAINT")}
    # and at the resolver: a floor-to-floor candidate never governs, even when it is the best-ranked one
    cs = [AV.cand("PAINT", 3.6, "SECTION", "FLOOR", "GF", {"text": "F.F.L. +3.60 (floor above)"}, None,
                  never_wall_height=True),
          AV.cand("PAINT", 3.0, "FLOOR_NOTE", "FLOOR", "GF", {"text": "CEILING HEIGHT 3.00 M"}, None)]
    r = AV.resolve("PAINT", cs)
    assert (r["state"], r["value_m"], r["governing"]) == ("ESTABLISHED", 3.0, "FLOOR_NOTE")
    r = AV.resolve("PAINT", cs[:1])
    assert r["state"] == "BLOCKED" and r["value_m"] is None


@pytest.mark.parametrize("raw,unit,q,want", [
    ("2200", None, "HEIGHT", (2.2, "UNIT_INFERRED_MM")),       # 2200 m / 22 m impossible: mm
    ("2.20", None, "HEIGHT", (2.2, "UNIT_INFERRED_M")),        # a decimal below 30 is metres
    ("220", None, "HEIGHT", (2.2, "UNIT_INFERRED_CM")),        # 220 m and 0.22 m outside 0.30 .. 6.00
    ("1000", None, "SILL", (1.0, "UNIT_INFERRED_MM")),
    ("100", None, "SILL", (None, "UNIT_AMBIGUOUS:CM/MM")),     # 1.00 m or 0.10 m: both plausible, not guessed
    ("2.2", "M", "HEIGHT", (2.2, "UNIT_STATED_M")),
    ("90", "CM", "SILL", (0.9, "UNIT_STATED_CM")),
    ("9000", None, "HEIGHT", (None, "OUT_OF_RANGE")),          # 9.00 m is not an opening height
])
def test_units_are_inferred_only_when_unique(raw, unit, q, want):
    assert AV.to_m(raw, unit, q) == want


def test_v271_is_unchanged_by_the_evidence(ex1):
    """the same drawing under ARCH_TAKEOFF_V2.7.1: no V2.8 output, and its as-found reading (no heights without the
    facts) - the evidence reader is opt-in."""
    out = ex1("full", method=R.V271)
    assert not (out / "HEIGHT_EVIDENCE.json").exists() and not (out / "OPENING_SCHEDULE.json").exists()
    assert R.the(out, "FIN.PLASTER", "plaster")["measured_net"] is None
