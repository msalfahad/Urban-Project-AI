"""COLUMN_EVIDENCE_V1 (T-256, unwired, stdlib only): per-member evidence for a column section CONFLICT and for an upper
column line no plan draws.

Rule proposal R-COLUMN-EVIDENCE-1 (any villa; provenance: owner X6 = Q-61 (1), ERS s.2.2 / s.3, R-SECTION-CONFLICT-1
(T-217), COLUMN_LINE_V1 (T-248), T-220 NOT_DRAWN, T-256). It extends R-SECTION-CONFLICT-1 with two questions.

1. INDEPENDENCE. A source counts once per DOCUMENT. A plot of a drawing (the PDF of the DXF) and a copy of a drawing's
   layer inside another set (an architectural plan carrying the structural column layer with identical outlines) are
   the SAME document as their original: they confirm what was issued, they never add a reading. A typical detail
   (not drawn for this member) and a type table (a schedule band printed for every type, whether or not a member of
   that type exists on that storey) are not member-specific: they are recorded and never counted as a third source.

2. THIRD SOURCE. A section CONFLICT (two readings) is SETTLED only by an independent, member-specific PRINTED source
   (a size text or a face-to-face dimension at the member, in a document other than the two in conflict):
     - it agrees with the printed reading and the other reading is DRAWN only  -> SETTLED (DRAWING-CONFIRMED with
       that source; the drawn outline is a drafting slip, evidence only);
     - it agrees with the drawn reading -> still CONFLICT, now PRINTED_VS_PRINTED (a stronger designer item; X6:
       never resolved by preferring one printed document);
     - it agrees with neither -> CONFLICT with three candidates.
   Without such a source the record stays CONFLICT with both readings, the range, and the designer question.
   Never the larger end, never the schedule by default, never the freelancer's section.

3. EXISTENCE of an upper member that its storey plan does not draw. NOT_PRESENT only when every sheet that could draw it
   was searched and found nothing (the storey's structural plan, its plot, the architectural plan of the storey, the
   plan below for a start / stop symbol), no member-specific printed source names it, and the only thing that suggests
   it is a type-table band; the line is then REMOVED (no line), never a line of 0. Any sheet not searched, or any
   member-specific print -> UNKNOWN (no value, never 0). FOUND on any sheet -> EXISTS (its section is then classified).

4. CROSS-TRADE. Under C1 (R-CONC-OWN-1) slabs stop at the DRAWN column faces. A section reading other than the drawn
   one moves (A_reading - A_drawn) x t_plate between the column line and the slab line inside the slab plate: positive
   = DOUBLE (both lines bill it in that reading), negative = GAP (neither bills it). The column line's range is
   unchanged by this; the pair is reported so the slab line moves with the column when the conflict is answered.
"""
from __future__ import annotations

from dataclasses import dataclass, field

METHOD = "COLUMN_EVIDENCE_V1"
RULE = "R-COLUMN-EVIDENCE-1 (proposed)"
PRINTED = ("SCHEDULE", "TEXT", "DIM")
KINDS = PRINTED + ("DRAWN",)
_UNIT = {"m": 1.0, "cm": 0.01, "mm": 0.001}


class ConflictUnresolved(ValueError):
    """A single value was asked of a record that is not settled (CONFLICT, UNKNOWN, HELD)."""


class PreferenceRefused(ValueError):
    """A conflict was to be resolved by source preference (schedule wins, larger wins, closest to another side)."""


@dataclass(frozen=True)
class Source:
    kind: str                 # SCHEDULE / TEXT / DIM / DRAWN
    W: float
    D: float
    units: str
    document: str             # e.g. 'ST dxf: FFRS slab plan', 'ST dxf: column schedule', 'ARCH dxf: 1F plan'
    copy_of: str | None = None     # the document this one reproduces (a plot, an xref copy): never an extra reading
    member_specific: bool = True   # False: a typical detail or a type-table band
    ref: str = ""

    def section_m(self):
        if self.kind not in KINDS:
            raise ValueError(f"unknown source kind {self.kind!r}")
        if self.units not in _UNIT:
            raise ValueError(f"unknown units {self.units!r}")
        if self.W is None or self.D is None or self.W <= 0 or self.D <= 0:
            raise ValueError(f"section sides must be positive ({self.ref})")
        f = _UNIT[self.units]
        return tuple(sorted((round(self.W * f, 6), round(self.D * f, 6))))

    @property
    def root(self):
        return self.copy_of or self.document


@dataclass
class Evidence:
    member: str
    status: str                       # AGREE / SETTLED / CONFLICT / HELD
    basis: str
    readings: list = field(default_factory=list)   # [{"section_m", "area_m2", "documents", "kinds"}]
    governing: tuple | None = None
    copies: list = field(default_factory=list)     # sources that only reproduce a counted document
    not_counted: list = field(default_factory=list)  # typical details, type-table bands used only as context
    third: list = field(default_factory=list)      # independent member-specific printed sources found
    codes: list = field(default_factory=list)      # drawn-only sections recorded as drafting slips

    @property
    def range_m2(self):
        if self.status in ("AGREE", "SETTLED") and self.governing:
            g = _area(self.governing)          # a settled record has one reading; the drawn slip is evidence only
            return (g, g)
        a = [r["area_m2"] for r in self.readings]
        return (min(a), max(a)) if a else (None, None)

    def m3(self, height_m):
        if height_m is None:
            return (None, None)
        if height_m <= 0:
            raise ValueError("height must be positive")
        lo, hi = self.range_m2
        return (None, None) if lo is None else (round(lo * height_m, 6), round(hi * height_m, 6))

    def value_m3(self, height_m):
        """The single released value: only for AGREE or SETTLED."""
        if self.status not in ("AGREE", "SETTLED"):
            raise ConflictUnresolved(f"{self.member}: {self.status} has no single value")
        lo, hi = self.m3(height_m)
        if lo is None:
            raise ConflictUnresolved(f"{self.member}: height not given")
        return lo

    def pick(self, by: str):
        raise PreferenceRefused(f"{self.member}: resolving a {self.status} by '{by}' is refused (X6, ERS s.3)")


def _area(s):
    return round(s[0] * s[1], 6)


def classify(member: str, sources: list) -> Evidence:
    counted, copies, context = [], [], []
    roots = set()
    for s in sources:
        s.section_m()                                  # validates units / sides
        if not s.member_specific:
            context.append(s)
        elif s.copy_of:
            copies.append(s)
        else:
            counted.append(s)
            roots.add(s.document)
    for c in copies:
        if c.copy_of not in roots:
            raise ValueError(f"{member}: {c.document} is a copy of {c.copy_of}, which is not among the sources")
    printed = [s for s in counted if s.kind in PRINTED]
    if not printed:
        return Evidence(member, "HELD", "SECTION_NOT_PRINTED", copies=copies, not_counted=context)
    by_sec = {}
    for s in counted:
        by_sec.setdefault(s.section_m(), []).append(s)
    readings = [{"section_m": k, "area_m2": _area(k), "documents": sorted({x.document for x in v}),
                 "kinds": sorted({x.kind for x in v})} for k, v in sorted(by_sec.items())]
    ev = Evidence(member, "", "", readings=readings, copies=copies, not_counted=context)
    if len(by_sec) == 1:
        ev.status, ev.basis, ev.governing = "AGREE", "ALL_SOURCES_AGREE", readings[0]["section_m"]
        return ev
    # the conflict pair: the schedule and the drawn outline of the storey plan (their documents)
    base_docs = {s.document for s in counted if s.kind in ("SCHEDULE", "DRAWN")}
    third = [s for s in counted if s.kind in ("TEXT", "DIM") and s.document not in base_docs]
    ev.third = third
    printed_secs = {s.section_m() for s in printed}
    drawn_only = {k for k, v in by_sec.items() if all(x.kind == "DRAWN" for x in v)}
    drawn_docs = {s.document for s in counted if s.kind == "DRAWN"}
    own_print = [s for s in counted if s.kind in ("TEXT", "DIM") and s.document in drawn_docs]
    if len(printed_secs) == 1 and (third or own_print):
        ev.status, ev.governing = "SETTLED", next(iter(printed_secs))
        ev.basis = "THIRD_PRINTED_SOURCE_AGREES_WITH_PRINT" if third else "DRAWING_PRINTS_IT (DRAFTING_NOTE)"
        ev.codes = sorted(drawn_only)
        return ev
    ev.status = "CONFLICT"
    if len(printed_secs) > 1:
        ev.basis = "PRINTED_VS_PRINTED"
    else:
        ev.basis = "PRINTED_VS_DRAWN"
    return ev


def plate_transfer(drawn_m2: float, reading_m2: float, t_plate_m: float):
    """Concrete that moves between the column line and the slab line inside the slab plate for one reading (C1)."""
    if t_plate_m is None or t_plate_m <= 0:
        raise ValueError("slab plate thickness must be printed and positive")
    d = round((reading_m2 - drawn_m2) * t_plate_m, 6)
    return {"m3": d, "kind": "DOUBLE" if d > 0 else ("GAP" if d < 0 else "NONE")}


REQUIRED_SEARCH = ("storey structural plan", "plot of the storey plan", "architectural plan of the storey",
                   "structural plan below (start / stop symbol)")


def existence(line: str, searched: dict, member_specific_print: bool, type_band_only: bool):
    """searched: {required search key: 'FOUND' / 'ABSENT' / 'NOT_SEARCHED'} (keys of REQUIRED_SEARCH)."""
    for k in searched:
        if k not in REQUIRED_SEARCH:
            raise ValueError(f"unknown search {k!r}")
    missing = [k for k in REQUIRED_SEARCH if searched.get(k, "NOT_SEARCHED") == "NOT_SEARCHED"]
    if any(searched.get(k) == "FOUND" for k in REQUIRED_SEARCH):
        return {"line": line, "status": "EXISTS", "action": "CLASSIFY_SECTION", "m3": None}
    if missing or member_specific_print or not type_band_only:
        why = (["NOT_SEARCHED: " + ", ".join(missing)] if missing else []) + \
              (["a member-specific print names it"] if member_specific_print else []) + \
              (["a source other than a type-table band suggests it"] if not type_band_only else [])
        return {"line": line, "status": "UNKNOWN", "action": "HOLD", "m3": None, "why": why}
    return {"line": line, "status": "NOT_PRESENT", "action": "REMOVE_LINE", "m3": None,
            "why": ["absent on every sheet that could draw it; only a type-table band suggests it"]}
