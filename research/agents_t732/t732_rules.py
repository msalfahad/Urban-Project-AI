"""T-732 rules (project-agnostic; scope: every villa). Research only, unwired. Built on R-T714-1 (a held formwork line
takes its member's bound face by face), R-T707-1 / -2 (column top bounds from a one-plane plate with thickness zones,
open stand), URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 (T-119: the shaft runs to the soffit of the deepest member
framing in), R-CONC-OWN-1, R-T696-1 (directed rounding) and UP-QTY-STATUS-001; none of them edited.

R-T732-1 1.0.0  A COLUMN FORMWORK LINE WHOSE CONCRETE BOUND MOVED IS RE-DERIVED FROM THE MEMBER'S OWN HELD DIMENSIONS,
                FACE BY FACE; ITS CONCRETE GEOMETRY AND ITS FORMWORK GEOMETRY ARE NOT THE SAME.
    Physical element: the cast faces of one column from the top of the slab (or beam) it stands on up to the slab soffit
    above, less the faces covered by the members framing in (R-CONC-OWN-1). Three parts:
      SHAFT   P x (soffit of the deepest framing member - base): every face is formed (nothing frames below it).
      JOINT   the column faces between that soffit and the slab soffit not covered by a framing member (the walk's
              joint records: D_ctrl - t on a free face, D_ctrl - D_beam under a shallower beam).
      EDGE    a slab free-edge band over the column (outside the column perimeter).
    The concrete line holds the column on its section readings and its HEIGHT (to the slab top); the formwork shaft also
    depends on D_ctrl (the deepest framing depth), which the concrete line does not contain. So:
      (a) consistency first: the concrete bound must be A_min x h_lo .. A_max x h_hi (R-T696-1 floor / ceiling, 6 dp)
          with A from the printed / drawn sections; otherwise refused (a move we cannot decompose is not followed);
      (b) SHAFT low = P_min x (least top bound over the panels the column touches - base - D_max); the column's top
          follows the HIGHEST member framing in (R-T707-1), but the deepest soffit may hang from a member bordering the
          LOWEST panel, so the shaft takes the least top; for a member whose concrete height already runs to the
          controlling soffit (planted columns) D must be settled and is not deducted twice;
          SHAFT high = P_max x (h_hi - D_min); open when the member's high is open (AT_LEAST);
      (c) JOINT records (figures measured by the released walk at the stated section and at D_ctrl = D_min):
          section single AND D settled -> INDEPENDENT (fig .. fig): they contain no storey height;
          section single, D open, record stated at D_min -> 0 .. fig: as D grows the shaft loses P x dD and the
                                          joints gain at most P x dD, so the line is largest at D_min (fig) and its
                                          floor is the shaft;
          section held, or D open with the record at an unstated D -> DEPENDENT (0 .. open);
          0 .. x contact records (decided by a held neighbour) stay CAP (0 .. x);
      (d) EDGE bands: INDEPENDENT only when the section is single and D settled, else DEPENDENT (0 .. open);
      (e) envelope check: the perimeter faces (shaft + joints) never exceed P_max x (h_hi - t_min); a high above it is
          refused (it would mean a record outside the column face).
    Line: low = sum of lows; high = sum of highs when all known; low > 0 and high known -> BOUNDED; low > 0, high open ->
    AT_LEAST; never 0, never a range from 0 (R-T714-1). Refused: a figure in mm read as m (> 100), a negative figure, no
    panel top, D_max < D_min, a shaft height <= 0, a concrete bound that does not decompose.

R-T732-2 1.0.0  A CONCRETE BOUND MOVE MOVES A FORMWORK LINE ONLY THROUGH A FACE READ.
    Census by line id between two candidates: every formwork line whose member state (class / low / high) differs is
    listed old -> new. A moved member with a R-T732-1 face read is restated; one without keeps its earlier formwork class
    and is listed MOVED_NOT_RESTATED (never silently re-bounded from the concrete ratio); an unmoved member's line is
    unchanged by construction.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t696"))
import bound_rounding_v1 as BR  # noqa: E402

D = BR.D
RULES = {"R-T732-1": "1.0.0", "R-T732-2": "1.0.0"}
MAX_M = D("100")          # a length or level above 100 m in a column takeoff is a unit error (mm read as m)


class Refused(ValueError):
    pass


def _m(v, what, *, positive=True):
    if v is None:
        raise Refused(f"{what}: missing (HELD by name, never a default)")
    d = D(v)
    if d < 0 or (positive and d == 0):
        raise Refused(f"{what}: {d} is not a positive dimension")
    if d > MAX_M and "level" not in what:
        raise Refused(f"{what}: {d} m is a unit error (mm read as m)")
    return d


def sections(readings):
    """[(b, d), ...] in m -> (A_min, A_max, P_min, P_max, single)."""
    if not readings:
        raise Refused("no section reading")
    rs = [(_m(b, "section b"), _m(d, "section d")) for b, d in readings]
    areas = [BR.mul(b, d) for b, d in rs]
    pers = [BR.mul(2, BR.add(b, d)) for b, d in rs]
    return min(areas), max(areas), min(pers), max(pers), len(set(rs)) == 1


def check_concrete(member, a_min, a_max, h_lo, h_hi):
    """(a): the member's concrete bound is A_min x h_lo .. A_max x h_hi (floor / ceiling at 6 dp)."""
    lo = BR.round_low(BR.mul(a_min, h_lo))
    if D(member["low"]) != lo:
        raise Refused(f"concrete low {member['low']} is not A_min x h_lo = {lo}: the move does not decompose")
    if member["high"] is not None:
        hi = BR.round_high(BR.mul(a_max, h_hi))
        if D(member["high"]) != hi:
            raise Refused(f"concrete high {member['high']} is not A_max x h_hi = {hi}")
    return True


def shaft(*, p_min, p_max, base, panel_tops_lo, d_min, d_max, d_settled, h_hi, basis="SLAB_TOP"):
    """(b): the shaft face. h_hi = the member's high height (None = open); basis CTRL_SOFFIT: h already net of D."""
    if not panel_tops_lo:
        raise Refused("no panel top bound for the column (R-T707-1 input missing)")
    dmin, dmax = _m(d_min, "D_min"), _m(d_max, "D_max")
    if dmax < dmin:
        raise Refused(f"D_max {dmax} below D_min {dmin}")
    top = min(_m(t, "panel top level", positive=True) for t in panel_tops_lo)
    b = _m(base, "base level", positive=True)
    if basis == "CTRL_SOFFIT":
        if not d_settled:
            raise Refused("a column whose concrete runs to the controlling soffit needs a settled D")
        h_lo = top - b - dmax
        hi = None if h_hi is None else BR.mul(p_max, h_hi)
    elif basis == "SLAB_TOP":
        h_lo = top - b - dmax
        hi = None if h_hi is None else BR.mul(p_max, D(h_hi) - dmin)
    else:
        raise Refused(f"height basis {basis!r} unknown")
    if h_lo <= 0:
        raise Refused(f"shaft height {h_lo} <= 0: no floor (the deepest member reaches the base)")
    return {"low": BR.mul(p_min, h_lo), "high": hi, "h_lo": h_lo, "top_lo": top}


def face(f, *, single, d_settled):
    """(c) / (d): one recorded face -> dict(face_id, dep, low, high)."""
    kind, fid = f["kind"], f["face_id"]
    if kind == "JOINT_CAP":
        return {"face_id": fid, "dep": "CAP_ONLY", "low": D(0), "high": _m(f["hi"], f"{fid} cap")}
    fig = _m(f["fig"], f"{fid} figure")
    if fig > MAX_M:
        raise Refused(f"{fid}: unit error")
    if kind == "JOINT":
        if single and d_settled:
            return {"face_id": fid, "dep": "INDEPENDENT", "low": fig, "high": fig}
        if single and f.get("recorded_at") == "D_MIN":
            return {"face_id": fid, "dep": "AT_D_MIN", "low": D(0), "high": fig}
        return {"face_id": fid, "dep": "DEPENDENT", "low": D(0), "high": None}
    if kind == "EDGE":
        if single and d_settled:
            return {"face_id": fid, "dep": "INDEPENDENT", "low": fig, "high": fig, "outside": True}
        return {"face_id": fid, "dep": "DEPENDENT", "low": D(0), "high": None, "outside": True}
    raise Refused(f"{fid}: face kind {kind!r} unknown")


def column_line(line_id, *, member, sections_m, base, panel_tops_lo, panel_t, h_lo_conc, h_hi, d_min, d_max,
                d_settled, faces, basis="SLAB_TOP"):
    """R-T732-1 for one column formwork line. member = {'cls': BOUNDED|AT_LEAST, 'low', 'high'}."""
    if member["cls"] not in ("BOUNDED", "AT_LEAST"):
        raise Refused(f"{line_id}: member {member['cls']} has no floor to follow")
    a_min, a_max, p_min, p_max, single = sections(sections_m)
    check_concrete(member, a_min, a_max, D(h_lo_conc), None if h_hi is None else D(h_hi))
    sh = shaft(p_min=p_min, p_max=p_max, base=base, panel_tops_lo=panel_tops_lo, d_min=d_min, d_max=d_max,
               d_settled=d_settled, h_hi=h_hi if member["cls"] == "BOUNDED" else None, basis=basis)
    fs = [{"face_id": "SHAFT", "dep": "REDERIVED", "low": sh["low"], "high": sh["high"]}]
    fs += [face(f, single=single, d_settled=d_settled) for f in faces]
    low = BR.add(*[f["low"] for f in fs])
    highs = [f["high"] for f in fs]
    high = BR.add(*highs) if all(h is not None for h in highs) else None
    t_min = min(_m(t, "panel t") for t in panel_t)
    if h_hi is not None:
        full = D(h_hi) + (D(d_min) if basis == "CTRL_SOFFIT" else 0)
        env = BR.mul(p_max, full - t_min)
        per = [f["high"] for f in fs if not f.get("outside")]
        if all(h is not None for h in per) and BR.add(*per) > env:
            raise Refused(f"{line_id}: perimeter faces {BR.add(*per)} above the envelope {env}")
    else:
        env = None
    if low <= 0:
        raise Refused(f"{line_id}: no positive floor")
    if high is not None:
        lo_r, hi_r = BR.bound(low, high)
        cls = "BOUNDED"
    else:
        lo_r, hi_r, cls = BR.round_low(low), None, "AT_LEAST"
    return {"line_id": line_id, "cls": cls, "low": lo_r, "high": hi_r, "faces": fs, "shaft_h_lo": sh["h_lo"],
            "top_lo_used": sh["top_lo"], "p": (p_min, p_max), "a": (a_min, a_max), "single_section": single,
            "envelope": env}


def census(old_members, new_members, restated):
    """R-T732-2: old_members / new_members: {fw_line: (cls, low, high)}; restated: {fw_line: result}."""
    out = []
    for lid in sorted(old_members):
        o, n = old_members[lid], new_members.get(lid)
        if n is None:
            raise Refused(f"{lid}: formwork line missing from the new candidate")
        if o == n:
            continue
        state = "RESTATED" if lid in restated else "MOVED_NOT_RESTATED"
        out.append({"line_id": lid, "member_before": o, "member_after": n, "state": state})
    for lid in restated:
        if lid not in old_members or old_members[lid] == new_members.get(lid):
            raise Refused(f"{lid}: restated without a member move")
    return out
