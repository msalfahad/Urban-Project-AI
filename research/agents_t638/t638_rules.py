"""R-T638-1 FORMWORK HOLD CENSUS (every villa; research provenance, proposed): every HELD-blank formwork line of a
candidate (B10-13 STR.FORMWORK) gets exactly one class, the named cause of every face it carries and, where the
evidence proves a figure, a fix row FR-T638-n; nothing is wired here.

Physical element (ERS s.2.1). A formwork piece is the temporary mould face of one cast concrete face that is NOT cast
against earth, blinding, masonry or an earlier pour; it bounds one member and sits beside the line that carries that
member's concrete. Contact m2 is physical; panels / reuse (procurement) and rate are not measured here.

Classes (T-638 row, owner directive 2026-11-08 12:40 item 3):
  A_FIX   the member's concrete is RELEASED and every face the fix row releases was measured by the SAME method that
          produced the released B10-13 lines (walk faces R4-2xx / R4-3xx, column shaft perimeter x (interval - D_ctrl),
          T-119 r2) with its own hold cause now settled by merged evidence. The row releases the proven figure; any
          face of the line still open goes to a HELD companion with its bound beside (never summed, never 0).
  B_HELD  the face is held by a HELD concrete element: the member's own concrete line (BLOCKED_RFI, BOUNDED_EXPOSURE,
          a ranged PROVISIONAL line, a missing-category line now HELD) or the adjacent member / edge whose geometry
          decides the contact (RING_MIX, STAIR, HELD_EDGE, UNMATCHED, held member). Never computed from a HELD volume.
  C_HELD  a drawn dimension or detail is genuinely missing: the contact condition below the natural ground (OQ-10:
          formed vs earth-cast; the working space is not printed, the same missing item as the B1 excavation working
          space UP-EXC-001 / OQ-13), the depth of an unlabelled framing member (D-26), the annex datum (Q-54 B), a
          section CONFLICT in the issued set, a casting method not specified, a mark / count / thickness not printed.
          The cause names the drawing and the item.

Ordering when a line carries several open faces: A_FIX if the row releases a proven figure; otherwise B_HELD if any
face is blocked by a HELD concrete element; otherwise C_HELD. Every face's own cause is listed either way.

Generic contact calculator (used by the fixture and as the method statement; the development-villa figures are the
merged ledger values of the same method, never recomputed from a HELD volume):
  beam between supports under a slab   soffit b x L_clear + sides 2 x L_clear x (D - t); a side against masonry /
                                       an earlier pour has no form (that side is dropped, never valued)
  column in a storey                   shaft perimeter x (H - D_ctrl), D_ctrl = the deepest framing member; joint
                                       strip perimeter x (D_ctrl - t) - sum over framing members b_i x (D_i - t);
                                       total = perimeter x (H - t) - sum b_i x (D_i - t)
"""
from __future__ import annotations

from decimal import Decimal

CLASSES = ("A_FIX", "B_HELD", "C_HELD")
CONTACT_FORMED = ("FORM",)
CONTACT_NO_FORM = ("EARTH", "BLINDING", "MASONRY", "EARLIER_POUR", "SCREED")
CONCRETE_RELEASED = ("RELEASED",)
Q6 = Decimal("0.000001")
MAX_MEMBER_DIM_M = Decimal("5")       # a member width / depth above 5 m is a unit error (mm read as m), refused


class RuleError(Exception):
    pass


def D(x):
    return None if x is None else Decimal(str(x))


def q(x):
    return D(x).quantize(Q6)


def S(x):
    if x is None:
        return None
    s = format(D(x).normalize(), "f")
    return "0" if s in ("-0", "0.0") else s


def _dim(name, v, upper=MAX_MEMBER_DIM_M):
    if v is None or str(v).strip() == "":
        raise RuleError(f"{name} missing: a missing dimension is HELD, never 0")
    d = D(v)
    if d <= 0:
        raise RuleError(f"{name} {v}: must be > 0")
    if upper is not None and d > upper:
        raise RuleError(f"{name} {v}: above {upper} m, read in mm? (units refused)")
    return d


def require_released(concrete_state, what):
    """R-T638-1 B: formwork is never computed from a HELD concrete volume."""
    if concrete_state not in CONCRETE_RELEASED:
        raise RuleError(f"{what}: concrete line {concrete_state}: formwork from a HELD volume refused (class B)")


def require_formed(contact, what):
    if contact in CONTACT_NO_FORM:
        raise RuleError(f"{what}: face cast against {contact}: no form, never valued")
    if contact not in CONTACT_FORMED:
        raise RuleError(f"{what}: contact {contact!r} unknown: HELD")


# ---- generic contact calculator (method statement + fixture) --------------------------------------------------------

def beam_forms(b, depth, t, l_clear, concrete_state="RELEASED", side_contacts=("FORM", "FORM"),
               soffit_contact="FORM"):
    """soffit b x L + each formed side L x (D - t). Returns {'soffit', 'sides', 'total'} in m2 (Decimal)."""
    require_released(concrete_state, "beam")
    b, depth, l_clear = _dim("beam width", b), _dim("beam depth", depth), _dim("clear span", l_clear, upper=None)
    t = _dim("slab thickness", t)
    if depth <= t:
        raise RuleError(f"beam depth {depth} <= slab {t}: no side below the slab (a band, not a beam)")
    out = {"soffit": Decimal(0), "sides": Decimal(0)}
    require_formed(soffit_contact, "beam soffit")
    out["soffit"] = b * l_clear
    for i, c in enumerate(side_contacts):
        if c in CONTACT_NO_FORM:
            continue                      # that side has no form: dropped, never a valued 0
        require_formed(c, f"beam side {i + 1}")
        out["sides"] += l_clear * (depth - t)
    out["total"] = out["soffit"] + out["sides"]
    return {k: q(v) for k, v in out.items()}


def column_forms(a, c, h, t, framing, concrete_state="RELEASED"):
    """shaft perimeter x (H - D_ctrl) + joint strip perimeter x (D_ctrl - t) - sum b_i x (D_i - t).
    framing: list of (b_i, D_i) of the members that frame into the column (empty: shaft to the slab soffit)."""
    require_released(concrete_state, "column")
    a, c, h, t = _dim("column side a", a), _dim("column side c", c), _dim("storey interval", h, upper=None), \
        _dim("slab thickness", t)
    per = 2 * (a + c)
    fr = [(_dim("framing width", b), _dim("framing depth", d)) for b, d in framing]
    for b, d in fr:
        if d < t:
            raise RuleError(f"framing member depth {d} < slab {t}")
        if b > max(a, c):
            raise RuleError(f"framing width {b} wider than the column face: join not a strip")
    d_ctrl = max([d for _, d in fr], default=t)
    if d_ctrl >= h:
        raise RuleError(f"controlling depth {d_ctrl} >= interval {h}")
    shaft = per * (h - d_ctrl)
    joint = per * (d_ctrl - t) - sum((b * (d - t) for b, d in fr), Decimal(0))
    if joint < 0:
        raise RuleError("joint strip negative: framing joins exceed the column perimeter")
    return {"shaft": q(shaft), "joint": q(joint), "total": q(shaft + joint), "d_ctrl": q(d_ctrl)}


# ---- census entry and fix-row guards --------------------------------------------------------------------------------

BLANK = {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None}


def check_entry(e):
    """one census entry {line_id, class, cause, faces, fix?}: refusals of R-T638-1."""
    lid = e.get("line_id")
    if e.get("class") not in CLASSES:
        raise RuleError(f"{lid}: class {e.get('class')!r} not in {CLASSES}")
    if not str(e.get("cause") or "").strip():
        raise RuleError(f"{lid}: no named cause")
    fx = e.get("fix")
    if e["class"] == "A_FIX":
        if not fx:
            raise RuleError(f"{lid}: A_FIX needs a fix row")
        if e.get("concrete_class") not in CONCRETE_RELEASED:
            raise RuleError(f"{lid}: A_FIX on concrete {e.get('concrete_class')}: formwork from a HELD volume refused")
        after = fx["after"]
        if after.get("class") != "RELEASED" or D(after.get("measured_net")) is None or D(after["measured_net"]) <= 0:
            raise RuleError(f"{lid}: a fix row releases a figure > 0 (a HELD line is never released as 0)")
        comp = fx.get("companion")
        if fx.get("open_faces") and not comp:
            raise RuleError(f"{lid}: open faces left without a HELD companion")
        if comp is not None:
            if comp.get("class") != "HELD" or comp.get("measured_net") is not None:
                raise RuleError(f"{lid}: companion must be HELD with no value")
            lo, hi = D(comp.get("held_low")), D(comp.get("held_high"))
            if lo is not None and hi is not None and lo > hi:
                raise RuleError(f"{lid}: companion low > high")
        if fx.get("before") != BLANK:
            raise RuleError(f"{lid}: fix row before-state must be the HELD blank line")
    elif fx:
        raise RuleError(f"{lid}: {e['class']} carries no fix row (stays HELD blank, cause named)")
    for f in e.get("faces", []):
        if not str(f.get("cause") or "").strip():
            raise RuleError(f"{lid} face {f.get('face_id')}: no named cause")
    return True


def census_counts(entries):
    by = {k: 0 for k in CLASSES}
    for e in entries:
        check_entry(e)
        by[e["class"]] += 1
    fix = [e for e in entries if e.get("fix")]
    rel = sum((D(e["fix"]["after"]["measured_net"]) for e in fix), Decimal(0))
    return {"lines": len(entries), "by_class": by, "fix_rows": len(fix),
            "companions": sum(1 for e in fix if e["fix"].get("companion")),
            "released_m2": S(q(rel)), "stay_held_blank": len(entries) - len(fix)}
