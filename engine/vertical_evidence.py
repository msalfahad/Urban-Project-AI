"""§14. A plan carries no height. So GO AND LOOK, and refuse if nothing.

A riser height is a vertical fact, and a floor plan is a horizontal
document. Round 6D asked the plan, found nothing and refused — which was
right, and incomplete: the architectural source set is more than the
plans. Sections, elevations and level marks are drawn too, and a riser
height that is written down somewhere in the set is not "not
established", it is not yet looked for.

This module looks. It reads what a representation of the design says
about heights, and it says which of three things is true:

    PLACED     the text sits somewhere the engine can attribute it —
               a level mark inside a drawing region, on a floor;
    UNPLACED   the text exists in a representation this project cannot
               place (a W2D stream with no reader for it), so it is a
               lead and never a measurement;
    NOTHING    the set does not carry it.

And then, whatever it found, the arithmetic is the same: a riser height
comes from a floor-to-floor rise divided by a riser COUNT, and both have
to be established. NO GENERIC BUILDING DEFAULT. Not 150, not 170, not
175, not "typical". A stair whose rise nobody has written down is a
stair whose riser quantity is NOT ESTABLISHED, however many buildings
have 170 mm risers.

What this module may NEVER take from a drawing, however plainly it is
printed there: an area, a total, a take-off, a quantity. Those are the
sealed answers this project is not allowed to read, and a text that
looks like one is refused by name rather than quietly skipped.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

MODEL = "VERTICAL_EVIDENCE_IS_SEARCHED_FOR_AND_NEVER_ASSUMED_V2"

# --- what a piece of vertical evidence is -------------------------------
LEVEL_MARK = "A_LEVEL_MARK"
RISER_NOTE = "A_RISER_NOTE"
SECTION_SHEET = "A_SECTION_SHEET"
ELEVATION_SHEET = "AN_ELEVATION_SHEET"
KINDS = (LEVEL_MARK, RISER_NOTE, SECTION_SHEET, ELEVATION_SHEET)

# --- how well the engine can use it -------------------------------------
PLACED = "PLACED_IN_A_DRAWING_REGION"
UNPLACED = "FOUND_BUT_NOT_PLACEABLE_BY_THIS_PROJECT"
REFUSED_TAKE_OFF = "REFUSED_IT_IS_A_TAKE_OFF_TOTAL"
STATES = (PLACED, UNPLACED, REFUSED_TAKE_OFF)

# §11 (6E-A). TWO DIFFERENT SENTENCES, and Round 6E let them blur:
#
#   "the source set carries no vertical evidence"   — about the DRAWINGS
#   "this engine cannot place the evidence it has"  — about the ENGINE
#
# For P7757 the second is true and the first is false. The set carries
# eight level marks, two sections and four elevations; what is missing is
# a reader that can put them against a floor and a stair.
EVIDENCE_PRESENT = "THE_SOURCE_SET_CARRIES_VERTICAL_EVIDENCE"
EVIDENCE_ABSENT = "THE_SOURCE_SET_CARRIES_NO_VERTICAL_EVIDENCE"
PLACED_AGAINST_A_FLOOR = "THE_EVIDENCE_IS_PLACED_AGAINST_A_FLOOR"
PLACEMENT_NOT_ESTABLISHED = "THE_EVIDENCE_IS_NOT_PLACED_AGAINST_A_FLOOR"

# And the one inference that is never made from a level list.
NEVER_BY_PLAUSIBILITY = (
    "a level is never assigned to a floor or to a stair because the "
    "difference between two numbers would give a believable riser. A "
    "plausible answer from unplaced evidence is a guess with arithmetic "
    "in front of it")

NOT_ESTABLISHED = "RISER_HEIGHT_NOT_ESTABLISHED"
ESTABLISHED = "RISER_HEIGHT_ESTABLISHED"
NO_VERTICAL_EVIDENCE = "THE_SOURCE_SET_CARRIES_NO_VERTICAL_EVIDENCE"
NO_READER = "NO_READER_PLACES_THE_VERTICAL_EVIDENCE_THIS_SET_CARRIES"
NO_RISER_COUNT = "THE_NUMBER_OF_RISERS_IS_NOT_ESTABLISHED"
NO_FLOOR_PAIR = "NO_TWO_LEVELS_ARE_ATTRIBUTED_TO_TWO_FLOORS"

# A take-off total printed on a drawing is still a take-off total.
TAKE_OFF = re.compile(r"(TOTAL|AREA\s*=|=\s*\d+(\.\d+)?\s*M|%%%)", re.I)

# A level mark: a signed metre figure, or AutoCAD's plus-minus datum.
_PM = "%%p"
LEVEL = re.compile(r"^\s*(?:%%[pP]|[+\-−])\s*(\d{1,3}(?:\.\d{1,3})?)\s*$")

# A riser note, in the forms a drawing writes one:
#   17R @ 170     17 RISERS      R = 170      17 x 170
RISERS_AT = re.compile(
    r"(\d{1,2})\s*(?:R|RISERS?)\b(?:\s*[@xX×]\s*(\d{2,3}(?:\.\d+)?))?",
    re.I)
RISE_ONLY = re.compile(r"\bR\s*(?:=|:)\s*(\d{2,3}(?:\.\d+)?)", re.I)
SECTION_WORD = re.compile(r"\bSECTION\b", re.I)
ELEVATION_WORD = re.compile(r"\bELEVATION\b", re.I)


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "KINDS": list(KINDS),
        "STATES": list(STATES),
        "why": {
            "no_generic_default": (
                "a riser height is a fact about one building. 170 mm is "
                "a fact about a habit, and a habit is not evidence"),
            "unplaced_is_not_measured": (
                "a level mark in a stream this project cannot read is a "
                "lead. It says the set carries the answer and it does "
                "not say what the answer is"),
            "a_total_is_still_sealed": (
                "an area printed on a drawing is the take-off this "
                "project may not read. It is refused by name here so "
                "that nobody reads it by accident"),
        },
    }


def model_hash() -> str:
    parts = ([MODEL] + list(KINDS) + list(STATES)
             + [NOT_ESTABLISHED, ESTABLISHED, NO_VERTICAL_EVIDENCE,
                NO_READER, NO_RISER_COUNT, NO_FLOOR_PAIR,
                EVIDENCE_PRESENT, EVIDENCE_ABSENT,
                PLACED_AGAINST_A_FLOOR, PLACEMENT_NOT_ESTABLISHED])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


@dataclass
class Finding:
    """One piece of vertical evidence, and how far it can be trusted."""

    finding_id: str = ""
    kind: str = ""
    text: str = ""
    value_mm: float | None = None
    risers: int | None = None
    source: str = ""              # which representation it came from
    representation: str = ""      # DESIGN_CAD / DESIGN_DWF / DESIGN_PDF
    region_id: str = ""
    floor_level: str = ""
    at_mm: tuple = ()
    status: str = UNPLACED
    why: str = ""

    def record(self) -> dict:
        return {
            "vertical_evidence_id": self.finding_id,
            "kind": self.kind,
            "text": self.text,
            "value_mm": (None if self.value_mm is None
                         else round(self.value_mm, 1)),
            "risers": self.risers,
            "source": self.source,
            "representation": self.representation,
            "drawing_region_id": self.region_id,
            "floor_level": self.floor_level,
            "at_mm": [round(v, 1) for v in self.at_mm],
            "status": self.status,
            "why": self.why,
        }


def level_mm(text: str):
    """The level a mark states, in millimetres, or None.

    `%%p0.00` is the datum itself and reads 0. A bare `4.30` is not a
    level: it is a dimension, a scale, a number on a drawing.
    """
    t = (text or "").strip()
    m = LEVEL.match(t)
    if not m:
        return None
    v = float(m.group(1)) * 1000.0
    if t.lstrip().startswith(("-", "−")):
        v = -v
    return v


def riser_note(text: str):
    """(count, rise_mm) from a note, either of which may be None."""
    t = (text or "").strip()
    m = RISERS_AT.search(t)
    if m:
        rise = float(m.group(2)) if m.group(2) else None
        return int(m.group(1)), rise
    m = RISE_ONLY.search(t)
    if m:
        return None, float(m.group(1))
    return None, None


def scan(texts, *, source: str, representation: str, placed: bool = True,
         region_of=None, floor_of=None, start: int = 1) -> list:
    """Every piece of vertical evidence in one representation.

    `texts` are objects with `.text` and, where the representation can be
    placed, `.x`/`.y` and a region. A representation with no reader —
    strings pulled out of a binary stream — passes placed=False, and
    every finding from it is a LEAD and never a measurement.
    """
    region_of = region_of or (lambda t: getattr(t, "region_id", ""))
    floor_of = floor_of or (lambda t: getattr(t, "floor_level", ""))
    out, n = [], start
    for t in texts:
        raw = (getattr(t, "text", None) if not isinstance(t, str) else t)
        raw = (raw or "").strip()
        if not raw:
            continue
        kind, value, risers, why = "", None, None, ""
        if TAKE_OFF.search(raw):
            # SEALED. An area total printed on a drawing is the answer
            # this project is not allowed to read, and it is named here
            # so that it is refused rather than skipped in silence.
            out.append(Finding(
                finding_id=f"VE-{n:04d}", kind="", text=raw[:80],
                source=source, representation=representation,
                status=REFUSED_TAKE_OFF,
                why="it states a quantity, and quantities are sealed"))
            n += 1
            continue
        v = level_mm(raw)
        if v is not None:
            kind, value = LEVEL_MARK, v
            why = "a level mark states a height above the datum"
        else:
            count, rise = riser_note(raw)
            if count is not None or rise is not None:
                kind, value, risers = RISER_NOTE, rise, count
                why = "a riser note states the stair's own rise"
            elif SECTION_WORD.search(raw):
                kind = SECTION_SHEET
                why = "a section is where a rise is drawn to scale"
            elif ELEVATION_WORD.search(raw):
                kind = ELEVATION_SHEET
                why = "an elevation carries the levels of the building"
        if not kind:
            continue
        out.append(Finding(
            finding_id=f"VE-{n:04d}", kind=kind, text=raw[:80],
            value_mm=value, risers=risers, source=source,
            representation=representation,
            region_id=(region_of(t) if placed else ""),
            floor_level=(floor_of(t) if placed else ""),
            at_mm=((float(getattr(t, "x", 0.0)), float(getattr(t, "y", 0.0)))
                   if placed and hasattr(t, "x") else ()),
            status=(PLACED if placed else UNPLACED),
            why=why))
        n += 1
    return out


def assess(findings, *, floors_needed=(), risers=None, attempts=()) -> dict:
    """Can a riser height be established from what was found? (§14)

    Only from a floor-to-floor rise BETWEEN TWO NAMED FLOORS and a riser
    COUNT that is itself established. Two levels nobody can attribute to
    a floor are not a rise; a rise with no count is not a height; and
    neither of them is ever a default.
    """
    found = list(findings)
    levels = [f for f in found
              if f.kind == LEVEL_MARK and f.status == PLACED
              and f.floor_level and f.value_mm is not None]
    by_floor: dict = {}
    for f in levels:
        by_floor.setdefault(f.floor_level, set()).add(round(f.value_mm, 1))
    notes = [f for f in found
             if f.kind == RISER_NOTE and f.status == PLACED
             and f.value_mm is not None]

    leads = [f for f in found if f.status == UNPLACED]
    sealed = [f for f in found if f.status == REFUSED_TAKE_OFF]

    carries = [f for f in found
               if f.kind in (LEVEL_MARK, RISER_NOTE, SECTION_SHEET,
                             ELEVATION_SHEET)
               and f.status in (PLACED, UNPLACED)]
    out = {
        "model": MODEL,
        # §11 the two sentences, told apart and both answered
        "vertical_evidence": (EVIDENCE_PRESENT if carries
                              else EVIDENCE_ABSENT),
        "vertical_evidence_found": len(carries),
        "placement": (PLACED_AGAINST_A_FLOOR if levels
                      else PLACEMENT_NOT_ESTABLISHED),
        "levels_found_m": sorted({round((f.value_mm or 0.0) / 1000.0, 3)
                                  for f in found
                                  if f.kind == LEVEL_MARK
                                  and f.value_mm is not None}),
        "sheets_found": sorted({f.text for f in found
                                if f.kind in (SECTION_SHEET,
                                              ELEVATION_SHEET)}),
        "placement_attempts": [dict(a) for a in (attempts or ())],
        "never_by_plausibility": NEVER_BY_PLAUSIBILITY,
        "findings": [f.record() for f in found],
        "level_marks_placed": sum(1 for f in found
                                  if f.kind == LEVEL_MARK
                                  and f.status == PLACED),
        "level_marks_attributed_to_a_floor": len(levels),
        "levels_by_floor": {k: sorted(v) for k, v in by_floor.items()},
        "riser_notes_placed": len(notes),
        "leads_in_representations_this_project_cannot_place": len(leads),
        "take_off_totals_refused": len(sealed),
    }

    if notes:
        # A NOTE IS THE DRAWING SAYING IT. Nothing beats that.
        rise = notes[0].value_mm
        out.update({
            "riser_height_status": ESTABLISHED,
            "riser_height_mm": rise,
            "riser_height_source": f"{notes[0].source}:{notes[0].text}",
            "why": "the drawing writes the rise down",
        })
        return out

    want = [f for f in floors_needed if f]
    pairs = [f for f in want if len(by_floor.get(f, ())) >= 1]
    if len(pairs) >= 2:
        lo = min(min(by_floor[pairs[0]]), min(by_floor[pairs[1]]))
        hi = max(max(by_floor[pairs[0]]), max(by_floor[pairs[1]]))
        rise = hi - lo
        if risers:
            out.update({
                "riser_height_status": ESTABLISHED,
                "floor_to_floor_mm": rise,
                "riser_height_mm": rise / float(risers),
                "riser_height_source": (
                    f"levels on {pairs[0]} and {pairs[1]}, over "
                    f"{risers} risers counted from the drawing"),
                "why": "a rise between two floors, over a counted number",
            })
            return out
        out.update({
            "riser_height_status": NOT_ESTABLISHED,
            "floor_to_floor_mm": rise,
            "what_would_settle_it": NO_RISER_COUNT,
            "why": ("the rise between these two floors is established "
                    "and the number of risers is not. A height is the "
                    "one divided by the other and neither is assumed"),
        })
        return out

    if leads:
        out.update({
            "riser_height_status": NOT_ESTABLISHED,
            "what_would_settle_it": NO_READER,
            "why": ("the architectural set DOES carry vertical evidence "
                    f"— {len(leads)} findings, level marks, section and "
                    "elevation sheets — in a representation this project "
                    "has no reader for. THIS IS NOT AN ABSENCE OF "
                    "EVIDENCE: it is an absence of placement. A reader "
                    "that places them, or the same sheets in a source "
                    "the engine already decodes, settles it, and "
                    + NEVER_BY_PLAUSIBILITY),
        })
        return out
    if not levels:
        out.update({
            "riser_height_status": NOT_ESTABLISHED,
            "what_would_settle_it": NO_VERTICAL_EVIDENCE,
            "why": "the set carries no level, no section and no note",
        })
        return out
    out.update({
        "riser_height_status": NOT_ESTABLISHED,
        "what_would_settle_it": NO_FLOOR_PAIR,
        "why": ("level marks were found and placed, and not two of them "
                "on two floors this stair connects"),
    })
    return out
