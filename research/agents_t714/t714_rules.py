"""T-714 rules (project-agnostic; scope: every villa). Research only, unwired. Built on R-T638-1 (formwork hold classes,
same contact method as the released lines), R-CONC-OWN-1 (a face against another member is not formed), R-T696-1
(bound_rounding_v1, directed rounding) and UP-QTY-STATUS-001 (every line reported once: released, bounded, held);
none of them edited.

R-T714-1 1.0.0  A HELD FORMWORK LINE TAKES THE BOUND ITS CONCRETE MEMBER CARRIES, FACE BY FACE, NEVER WIDER OR TIGHTER.
    Physical element: the formwork of a member is the sum of its cast faces not cast against earth, blinding, masonry or
    an earlier pour. A member whose concrete is HELD on a bound is held because ONE dimension has two printed / drawn
    readings (a width, a section, a depth, a height) or only a guaranteed floor. Each face is classed by how its contact
    area depends on THAT dimension:
      INDEPENDENT   the face does not contain the held dimension (a beam side under a width conflict, a beam soffit
                    under a depth hold, a slab-edge band along a beam): its measured figure stands, low = high.
      TWO_READINGS  the face ledger already carries the face at both readings (a column shaft at the drawn and the
                    printed perimeter): low .. high as recorded. Under a member that has only a floor (AT_LEAST), the
                    high is dropped (the member's upper end is open, so is the face's).
      SCALED        the face is proportional to the held dimension and recorded at one reading only (a beam soffit
                    b x L under a width conflict): the other end = figure x (other reading / recorded reading); the
                    ratio must equal the ratio of the member's own concrete bound (consistency, else refused).
      CAP_ONLY      a contact 0 .. x decided by something else than the member (a held neighbour, an unprinted
                    framing depth with a printed minimum): low 0, high x (x = the full face, a geometric cap).
      FLOOR_ONLY    a face record that bundles a part free of the held dimension (a ring soffit = its plan band) with
                    parts that follow it (inner / outer faces over the unprinted depth): low = the free part at the
                    LEAST drawn plan reading, high open.
      DEPENDENT     the face contains the held dimension but the ledger carries it at one unstated reading: low 0,
                    high open (no figure is chosen for it).
      BLOCK         an open drawn item outside the member decides whether the face is formed at all (OQ-10 formed vs
                    earth-cast below natural ground, a casting method, an unprinted thickness / section / mark / count,
                    a face with no recorded figure): the line stays HELD BLANK with that cause named.
    Line: any BLOCK -> BLANK_NAMED; member BLANK -> BLANK_NAMED with the member's cause; else low = sum of lows,
    high = sum of highs when every high is known. low > 0 and high known -> BOUNDED (only under a RELEASED or a BOUNDED
    member); low > 0, high open -> AT_LEAST; low = 0 -> BLANK_NAMED with the cap beside (a zero floor is never a line,
    never 0, never an AT_MOST printed as a quantity). Rounding R-T696-1 (floor low, ceiling high, 6 dp).
    Refused: a negative / mm-sized / missing figure on a face that is not BLOCK, a SCALED face whose ratio disagrees with
    the member's concrete ratio, a high that follows the open reading of an AT_LEAST member (dropped, never kept).

R-T714-2 1.0.0  A RELEASE ROW MADE ON AN OLDER CANDIDATE IS WIRED ONLY BY ITS CURRENT LINE ID, STALE 0.
    A fix row is restated on the candidate of record by line id; it is wired only when that line still exists with the
    same element id, the same class (HELD), no figure and no bound (the state the row was made for). Any difference makes
    the row STALE and it is not wired.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t696"))
import bound_rounding_v1 as BR  # noqa: E402

D = BR.D
RULES = {"R-T714-1": "1.0.0", "R-T714-2": "1.0.0"}
DEPS = ("INDEPENDENT", "TWO_READINGS", "SCALED", "CAP_ONLY", "FLOOR_ONLY", "DEPENDENT", "BLOCK")
MEMBER_CLASSES = ("RELEASED", "BOUNDED", "AT_LEAST", "BLANK")
LINE_CLASSES = ("BOUNDED", "AT_LEAST", "BLANK_NAMED")
MAX_FACE_M2 = D("1000")      # a single cast face above 1000 m2 is a unit error (mm2 / cm2 read as m2)


class Refused(ValueError):
    pass


def _fig(v, what, *, allow_zero=True):
    if v is None:
        raise Refused(f"{what}: missing figure (HELD by name, never a default)")
    d = D(v)
    if d < 0 or (d == 0 and not allow_zero):
        raise Refused(f"{what}: {d} not a contact area (negative)")
    if d >= MAX_FACE_M2:
        raise Refused(f"{what}: {d} m2 is not a face area (unit error)")
    return d


def member(cls, low=None, high=None, cause=""):
    """the concrete member state the formwork follows."""
    if cls not in MEMBER_CLASSES:
        raise Refused(f"member class {cls!r} not in {MEMBER_CLASSES}")
    if cls == "BOUNDED":
        lo, hi = _fig(low, "member low"), _fig(high, "member high")
        if lo <= 0 or hi < lo:
            raise Refused(f"member bound {lo} .. {hi} is not a positive bound")
        return {"cls": cls, "low": lo, "high": hi, "cause": cause}
    if cls == "AT_LEAST":
        lo = _fig(low, "member floor")
        if lo <= 0:
            raise Refused("an AT_LEAST member needs a positive floor (never 0)")
        if high is not None:
            raise Refused("an AT_LEAST member has no high")
        return {"cls": cls, "low": lo, "high": None, "cause": cause}
    return {"cls": cls, "low": None, "high": None, "cause": cause}


def face(face_id, dep, *, value=None, lo=None, hi=None, ratio=None, cause=""):
    """one cast face -> (low, high) contribution; BLOCK returns the cause."""
    if dep not in DEPS:
        raise Refused(f"{face_id}: dependence {dep!r} not in {DEPS}")
    out = {"face_id": face_id, "dep": dep, "cause": cause}
    if dep == "BLOCK":
        out.update(low=None, high=None)
        return out
    if dep == "INDEPENDENT":
        v = _fig(value, f"{face_id} figure")
        out.update(low=v, high=v)
    elif dep == "TWO_READINGS":
        a, b = _fig(lo, f"{face_id} low reading"), _fig(hi, f"{face_id} high reading")
        if b < a:
            raise Refused(f"{face_id}: high reading {b} below low reading {a}")
        out.update(low=a, high=b)
    elif dep == "SCALED":
        v = _fig(value, f"{face_id} figure")
        r = D(ratio) if ratio is not None else None
        if r is None or r <= 0:
            raise Refused(f"{face_id}: SCALED needs the positive ratio other reading / recorded reading")
        w = BR.mul(v, r)
        out.update(low=min(v, w), high=max(v, w), ratio=r)
    elif dep == "CAP_ONLY":
        out.update(low=D(0), high=_fig(hi, f"{face_id} cap"))
    elif dep == "FLOOR_ONLY":
        v = _fig(value, f"{face_id} depth-free part", allow_zero=False)
        out.update(low=v, high=None)
    elif dep == "DEPENDENT":
        out.update(low=D(0), high=None)
    return out


def check_ratio(face_ratio, member_low, member_high, *, tol="0.0005"):
    """a SCALED face's ratio must be the member's own concrete ratio (hi / lo or lo / hi)."""
    r, lo, hi = D(face_ratio), D(member_low), D(member_high)
    want = hi / lo if r >= 1 else lo / hi
    if abs(r - want) > D(tol) * want:
        raise Refused(f"SCALED ratio {r} disagrees with the member's concrete ratio {want:.6f}")
    return True


def combine(line_id, mem, faces):
    """R-T714-1: the line's class and bound from its member and faces."""
    if not faces:
        return {"line_id": line_id, "cls": "BLANK_NAMED", "low": None, "high": None,
                "why": "no cast face recorded on the line" + (f"; member: {mem['cause']}" if mem.get("cause") else ""),
                "cap_beside": None}
    if mem["cls"] == "BLANK":
        return {"line_id": line_id, "cls": "BLANK_NAMED", "low": None, "high": None,
                "why": "concrete member HELD BLANK: " + (mem["cause"] or "member cause not stated"), "cap_beside": None}
    blocks = [f for f in faces if f["dep"] == "BLOCK"]
    if blocks:
        return {"line_id": line_id, "cls": "BLANK_NAMED", "low": None, "high": None,
                "why": "; ".join(sorted({f["cause"] for f in blocks})), "cap_beside": None}
    if mem["cls"] == "AT_LEAST":
        for f in faces:
            if f["dep"] in ("TWO_READINGS", "SCALED"):
                f["high"] = None          # the member's upper end is open: so is a face that follows its reading
    low = BR.add(*[f["low"] for f in faces])
    highs = [f["high"] for f in faces]
    high = BR.add(*highs) if all(h is not None for h in highs) else None
    if low <= 0:
        cap = BR.round_high(high) if high is not None else None
        return {"line_id": line_id, "cls": "BLANK_NAMED", "low": None, "high": None,
                "why": "no positive floor: every face is 0 .. x or follows an unstated reading",
                "cap_beside": cap}
    if high is not None:
        # under an AT_LEAST member a high survives only when no face follows the member's open reading (all INDEPENDENT
        # / CAP_ONLY): the TWO_READINGS / SCALED highs were dropped above.
        lo_r, hi_r = BR.bound(low, high)
        return {"line_id": line_id, "cls": "BOUNDED", "low": lo_r, "high": hi_r, "why": "", "cap_beside": None}
    if mem["cls"] not in ("RELEASED", "BOUNDED", "AT_LEAST"):
        raise Refused(f"{line_id}: AT_LEAST under a member with no floor")
    return {"line_id": line_id, "cls": "AT_LEAST", "low": BR.round_low(low), "high": None, "why": "",
            "cap_beside": None}


def restate_fix(fix_id, line_id, element_id, index_line):
    """R-T714-2: a fix row is wired only on its unchanged HELD blank line."""
    if index_line is None:
        return {"fix": fix_id, "line_id": line_id, "state": "STALE", "why": "line not in the candidate"}
    checks = {"element_id": index_line.get("element_id") == element_id, "class": index_line.get("class") == "HELD",
              "no figure": index_line.get("measured_net") is None,
              "no bound": index_line.get("held_low") is None and index_line.get("held_high") is None}
    bad = [k for k, ok in checks.items() if not ok]
    return {"fix": fix_id, "line_id": line_id, "state": "STALE" if bad else "CURRENT",
            "why": ("differs: " + ", ".join(bad)) if bad else ""}
