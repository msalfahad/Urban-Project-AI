"""T-352 stair formwork rules (STAIR_FORMWORK_T352_V1): the formed faces of a staircase that the general formwork
ledger (T-163 r3 / T-332) does not already carry, one row per flight side, landing edge and junction, bound to the
stair concrete line it belongs to, each face once.

Pure rules, stdlib only (no engine import, no drawing access). Research piece, not wired; nothing is released.

Physical model (ERS s.2.1). A straight flight measured by the owner method (Q-19 steps, Q-47 A waist between the
first and the last riser line, Q-62 A cond wedges) has, in side elevation, one profile: the step triangles above the
pitch line through the inner step corners plus the waist band of perpendicular thickness t below it. Along the stair
width the flight is a prism, so the area of ONE side face equals the stair-owned concrete volume / width. In station
s (horizontal, from the first riser line, going g, riser r) over the waist region [0, (n_lines - 1) g]:

    top(s)    = (floor(s / g) + 1) r          (tread of the step above, relative to the first floor / landing level)
    bottom(s) = (r / g) s - t sec,  sec = hypot(g, r) / g

so the profile area between two stations is the exact integral of top - bottom (piecewise constant minus linear).
The arrival triangle beyond the last riser line lies in the landing / plate it arrives into (Q-62 wedge) and is
never part of the side face of the flight.

Formed or not (the classification, never a default):
  VOID       the side faces open space drawn as an opening, a well, a light well or a free slab edge with nothing
             below at that level: a form is physically required (wet concrete needs a containing surface) -> the
             face is FORMED and gets a value.
  WALL       the side abuts a masonry wall: formed or cast against it depends on the construction sequence, which
             no drawing prints -> HELD with the bound 0 .. area, never a value, never 0.
  MEMBER     the side abuts a concrete member (beam band, stair beam, column): cast together or against it is not
             printed -> HELD 0 .. area.
  JUNCTION   the side abuts a held junction piece (well end, winder turn, corner of two lanes) whose concrete is
             itself HELD -> HELD 0 .. area.
  UNKNOWN    what lies beside the side is not established (support, waist or neighbour not printed) -> HELD,
             unbounded when the profile itself is not established.
A winder or curved part is measured only where it is drawn AND dimensioned AND its riser count agrees with the
section (owner S-9: never generated); otherwise HELD.
"""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass, field
from typing import Iterable

RULE = "STAIR_FORMWORK_T352_V1"
CONTACTS = ("VOID", "WALL", "MEMBER", "JUNCTION", "UNKNOWN")
STATUSES = ("CALCULATED", "HELD", "CONFLICT", "NOT_APPLICABLE")
EVIDENCE = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN")
KINDS = ("FLIGHT_SIDE", "LANDING_EDGE", "JUNCTION_STRIP", "WINDER", "CURVED", "RISER", "SOFFIT")
UNITS = {"m": 1.0, "cm": 0.01, "mm": 0.001}


class StairFormworkError(ValueError):
    """A face that breaks a rule of this module (refused, never silently corrected)."""


def to_m(value: float, unit: str) -> float:
    if unit not in UNITS:
        raise StairFormworkError(f"unknown unit {unit!r}")
    return float(value) * UNITS[unit]


def sec(r: float, g: float) -> float:
    if r <= 0 or g <= 0:
        raise StairFormworkError("riser and going must be positive (a missing riser is HELD, never computed)")
    return math.hypot(g, r) / g


def profile_strip(r: float, g: float, t: float, n_lines: int, s_a: float, s_b: float) -> float:
    """Side-elevation area (m2) of the owner-method flight profile between stations s_a <= s_b inside the waist
    region [0, (n_lines - 1) g]. Exact: top is constant on each going, bottom is linear."""
    if t is None or t <= 0:
        raise StairFormworkError("waist thickness not printed: the side profile is HELD, never computed with 0")
    if n_lines < 2:
        raise StairFormworkError("a flight needs at least two riser lines")
    s_end = (n_lines - 1) * g
    if not (-1e-9 <= s_a <= s_b <= s_end + 1e-9):
        raise StairFormworkError(f"strip {s_a} .. {s_b} outside the waist region 0 .. {s_end}")
    ts = t * sec(r, g)
    k = (r / g)
    area, s = 0.0, s_a
    while s < s_b - 1e-12:
        j = min(int(math.floor(s / g + 1e-9)), n_lines - 2)
        nxt = min(s_b, (j + 1) * g)
        top = (j + 1) * r
        # integral of top - (k s - ts) from s to nxt
        area += (top + ts) * (nxt - s) - k * (nxt * nxt - s * s) / 2.0
        s = nxt
    return area


def flight_profile(r: float, g: float, t: float, n_lines: int) -> float:
    """Whole waist-region profile (m2): (n - 1) step triangles + waist band t x sloped length."""
    return profile_strip(r, g, t, n_lines, 0.0, (n_lines - 1) * g)


@dataclass
class Face:
    face_id: str
    stair: str
    piece: str
    kind: str
    side: str
    contact: str
    status: str
    evidence: str
    line_id: str | None
    m2: float | None = None
    lo: float | None = None
    hi: float | None = None
    drawn: bool = True
    dimensioned: bool = True
    count_agrees: bool = True
    plane: str | None = None          # region claim, e.g. 'GF-soffit:GF-130' (one surface, one face)
    source: str = ""
    basis: str = ""
    supersedes: tuple = field(default_factory=tuple)

    def check(self) -> "Face":
        if self.kind not in KINDS:
            raise StairFormworkError(f"{self.face_id}: unknown kind {self.kind!r}")
        if self.contact not in CONTACTS:
            raise StairFormworkError(f"{self.face_id}: unknown contact {self.contact!r}")
        if self.status not in STATUSES:
            raise StairFormworkError(f"{self.face_id}: unknown status {self.status!r}")
        if self.evidence not in EVIDENCE:
            raise StairFormworkError(f"{self.face_id}: unknown evidence {self.evidence!r}")
        if self.status == "CALCULATED":
            if self.contact != "VOID":
                raise StairFormworkError(
                    f"{self.face_id}: a face against {self.contact} is not a measured form (construction sequence "
                    "or neighbour not printed): HELD 0 .. area, never CALCULATED")
            if self.m2 is None or self.m2 <= 0:
                raise StairFormworkError(f"{self.face_id}: CALCULATED needs a positive m2")
            if self.lo is not None or self.hi is not None:
                raise StairFormworkError(f"{self.face_id}: a CALCULATED face carries m2, not a range")
            if self.kind in ("WINDER", "CURVED") and not (self.drawn and self.dimensioned and self.count_agrees):
                raise StairFormworkError(
                    f"{self.face_id}: winder / curved face not drawn, not dimensioned or its riser count disagrees "
                    "with the section: generated geometry is refused (owner S-9), HELD")
            if not self.line_id:
                raise StairFormworkError(f"{self.face_id}: a valued face must bind to one concrete line")
        else:
            if self.m2 is not None:
                raise StairFormworkError(
                    f"{self.face_id}: a {self.status} face carries no m2 (held never becomes a number, never 0)")
            for v in (self.lo, self.hi):
                if v is not None and v < 0:
                    raise StairFormworkError(f"{self.face_id}: negative bound")
            if self.lo is not None and self.hi is not None and self.lo > self.hi + 1e-12:
                raise StairFormworkError(f"{self.face_id}: lo above hi")
            if self.status in ("HELD", "CONFLICT") and self.hi == 0:
                raise StairFormworkError(f"{self.face_id}: a held face with an upper bound of 0 is a hidden 0")
            if self.status == "CONFLICT" and (self.lo is None or self.hi is None):
                raise StairFormworkError(f"{self.face_id}: a CONFLICT carries both readings as a range")
        return self


def check_faces(faces: Iterable[Face], existing_ids: Iterable[str] = ()) -> list[Face]:
    """Every face once: unique ids, no id re-added from the existing (T-163 r3 / T-332) ledger, one claim per
    plane region (a stair soffit never also counted with a slab soffit), superseded ids exist and are not reused."""
    existing = set(existing_ids)
    out, seen, planes = [], set(), {}
    for f in faces:
        f.check()
        if f.face_id in seen:
            raise StairFormworkError(f"{f.face_id}: face listed twice")
        if f.face_id in existing:
            raise StairFormworkError(f"{f.face_id}: already in the general formwork ledger, never added again")
        seen.add(f.face_id)
        if f.plane:
            if f.plane in planes:
                raise StairFormworkError(
                    f"{f.face_id}: region {f.plane} already claimed by {planes[f.plane]} (one surface, one face)")
            planes[f.plane] = f.face_id
        for s in f.supersedes:
            if s not in existing:
                raise StairFormworkError(f"{f.face_id}: supersedes {s}, which is not in the existing ledger")
        out.append(f)
    return out


def claim_existing_planes(faces: Iterable[Face], existing_planes: dict) -> None:
    """Refuse a new face whose plane region is already carried by an existing face (e.g. a stair soffit region that
    the slab-soffit line already measures)."""
    for f in faces:
        if f.plane and f.plane in existing_planes:
            raise StairFormworkError(
                f"{f.face_id}: region {f.plane} is already measured by existing face {existing_planes[f.plane]}")


def _fmt(v: float | None) -> str:
    return "" if v is None else f"{v:.6f}"


def fill_rows(faces: Iterable[Face]) -> list[dict]:
    """Addendum FILL for T-199 (formwork family): per concrete line and status, the face ids, m2 for CALCULATED,
    lo / hi for HELD / CONFLICT only where EVERY face of the row carries that bound (else blank), never 0 for held.
    Faces with no line id go to the NO_LINE row."""
    groups: dict = {}
    for f in faces:
        groups.setdefault((f.line_id or "NO_LINE", f.status), []).append(f)
    rows = []
    for (line, status), fs in sorted(groups.items()):
        row = {"line_id": line, "status": status, "faces": len(fs), "face_ids": " ".join(x.face_id for x in fs)}
        if status == "CALCULATED":
            row.update(m2=sum(x.m2 for x in fs), lo=None, hi=None)
        else:
            lo = None if any(x.lo is None for x in fs) else sum(x.lo for x in fs)
            hi = None if any(x.hi is None for x in fs) else sum(x.hi for x in fs)
            row.update(m2=None, lo=lo, hi=hi)
        if status != "CALCULATED" and row["m2"] is not None:
            raise StairFormworkError("held FILL row with a value")
        rows.append(row)
    return rows


def write_fill_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["line_id", "family", "status", "faces", "m2", "lo", "hi", "face_ids"])
    for r in rows:
        if r["status"] != "CALCULATED" and r.get("m2") not in (None, ""):
            raise StairFormworkError(f"{r['line_id']}: a held row printed with m2")
        if r["status"] != "CALCULATED" and r.get("hi") == 0:
            # lo 0 is a real lower bound (a face that may be cast against its neighbour); hi 0 is a hidden 0
            raise StairFormworkError(f"{r['line_id']}: a held row printed with hi 0 (0 .. 0 is a hidden 0)")
        w.writerow([r["line_id"], "FW.STAIR", r["status"], r["faces"], _fmt(r["m2"]), _fmt(r["lo"]),
                    _fmt(r["hi"]), r["face_ids"]])
    return buf.getvalue()


def totals(faces: Iterable[Face]) -> dict:
    fs = list(faces)
    calc = [f for f in fs if f.status == "CALCULATED"]
    held = [f for f in fs if f.status in ("HELD", "CONFLICT")]
    return {
        "calculated_m2": sum(f.m2 for f in calc),
        "calculated_faces": len(calc),
        "held_faces": len(held),
        "held_bounded_hi_m2": sum(f.hi for f in held if f.hi is not None),
        "held_bounded_lo_m2": sum(f.lo for f in held if f.lo is not None),
        "held_unbounded_faces": sum(1 for f in held if f.hi is None),
    }
