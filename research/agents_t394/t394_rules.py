"""T-394 COLUMN_RECON_V1: column concrete reconciliation, height / section / count / scope (pure rules, stdlib; any villa).

R-T394-1 (physical solid, height basis): a storey column is section x (top datum - base datum). The datums are structural
levels (finished level less the drawn build-up, a printed limit is a bound, never a length). The TOP datum depends on who
bills the volume above the soffit: the column runs to the slab TOP only when the slab line is net of the column outline
AND no beam line is billed through it (convention C1: column > beam > slab); a slab billed over the outline stops the
column at the slab soffit, a beam billed through stops it at the beam soffit. A column to the slab top under a slab that
bills the footprint is a DOUBLE and is refused.
R-T394-2 (mark decomposition, exact): per storey and mark, engine valued - freelancer = COUNT + HELD + SECTION + HEIGHT,
  COUNT   = (n_drawn - n_his) x a_his x h_his            (drawn members of the mark, held ones included)
  HELD    = - n_held x a_his x h_his                      (the held members at his section and height: never 0, never AGREE)
  SECTION = sum_valued (a_eng - a_his) x h_his
  HEIGHT  = sum_valued a_eng x (h_eng - h_his)
The four terms close the residual to 1e-6 m3 by algebra; anything else is printed as a bookkeeping remainder.
R-T394-3 (height split): HEIGHT on a valued member is split by its physical cause, in m3:
  JOINT_HEAD  = a_eng x D_ctrl                      the joint + head under the controlling member: the same solid, owned by
                                                    the column line (C1); the other side may carry it in its beam line
  GLOBAL_DEPTH = a_eng x ((h_eng - D_ctrl) - h_his - BASE)   his column stops at a uniform depth instead of the member's
  BASE        = a_eng x (base_his - base_eng)        a base datum difference (two ground-slab levels)
D_ctrl comes from the owner split (URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1); where it is not settled the member's
HEIGHT stays one traced term with its split OPEN (printed, not invented).
R-T394-4 (section class): a SECTION term on a member whose section is a printed-vs-drawn CONFLICT is UNRESOLVED (designer
item), never closed by picking a reading; on a DRAWING-CONFIRMED section it is a DIMENSION cause.
R-T394-5 (closure, T-385 r2): traced (named) causes, HELD and UNRESOLVED / unexplained are summed apart; a HELD member
valued 0, a cause stated as a ratio / percentage / scaling, or a split that does not re-add to its term is refused.
R-T394-6 (scope, wall ring vs columns): a wall ring that runs through column outlines owns only its net band; the column
pieces in it belong to the column / neck lines (R-CONC-OWN-1); the overlap a ring measured gross carries is a DOUBLE on
that side, named by its plan area x its height.
"""
from __future__ import annotations

TOL = 1e-6
CLASSES = ("AGREE", "ENGINE_RIGHT", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "HELD", "UNRESOLVED")


class Refused(ValueError):
    """A reading the rules refuse (double count, held as 0, ratio closure, unit error)."""


def _len(v, name):
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        raise Refused(f"{name}: not a number")
    if abs(v) > 100:
        raise Refused(f"{name}: {v} looks like mm or cm; levels and lengths are in m")
    return float(v)


def column_top(slab_top, slab_t, slab_bills_footprint, beam_through_depth=None):
    """R-T394-1: the column top datum from who bills the volume above the soffit."""
    slab_top = _len(slab_top, "slab_top")
    slab_t = _len(slab_t, "slab_t")
    if beam_through_depth is not None:
        return round(slab_top - _len(beam_through_depth, "beam depth"), 6), "BEAM_SOFFIT"
    if slab_bills_footprint:
        return round(slab_top - slab_t, 6), "SLAB_SOFFIT"
    return round(slab_top, 6), "SLAB_TOP"


def column_solid(a, base, top, *, slab_top, slab_t, slab_bills_footprint, beam_through_depth=None):
    """R-T394-1: section x (top - base); refuses a top that bills a volume another line already bills."""
    a = float(a)
    if a <= 0 or a > 5:
        raise Refused("section area out of range (m2)")
    base = _len(base, "base")
    top = _len(top, "top")
    allowed, kind = column_top(slab_top, slab_t, slab_bills_footprint, beam_through_depth)
    if top > allowed + TOL:
        raise Refused(f"column top {top} above {kind} {allowed}: the volume between is billed by another line (DOUBLE)")
    if top <= base:
        raise Refused("top at or below base")
    return round(a * (top - base), 6)


def decompose_mark(members, his):
    """R-T394-2 / -3 / -4. members: [{id, state VALUED|HELD, a, h, base, d_ctrl or None, section_status}], his: {n, a, h,
    base} or None (no row of his for the mark). Returns the term dict; every term is engine - freelancer, m3."""
    for m in members:
        if m["state"] == "HELD":
            if m.get("m3") not in (None, ""):
                raise Refused(f"{m['id']}: a HELD member carries a value ({m.get('m3')}); held is blank, never 0")
        elif m["state"] != "VALUED":
            raise Refused(f"{m['id']}: unknown state {m['state']}")
    n_his, a_his, h_his = (his["n"], his["a"], his["h"]) if his else (0, 0.0, 0.0)
    base_his = his.get("base") if his else None
    valued = [m for m in members if m["state"] == "VALUED"]
    held = [m for m in members if m["state"] == "HELD"]
    eng = sum(m["a"] * m["h"] for m in valued)
    out = {"n_drawn": len(members), "n_valued": len(valued), "n_held": len(held), "n_his": n_his,
           "engine_m3": round(eng, 6), "his_m3": round(n_his * a_his * h_his, 6)}
    # no row of his for the mark: the drawn members are a COUNT difference at the engine's own valued figure
    out["COUNT"] = round((len(members) - n_his) * a_his * h_his if his else eng, 6)
    out["HELD"] = round(-len(held) * a_his * h_his, 6)
    sec_conf = sec_dim = 0.0
    hgt = {"JOINT_HEAD": 0.0, "GLOBAL_DEPTH": 0.0, "BASE": 0.0, "SPLIT_OPEN": 0.0}
    if his:
        for m in valued:
            s = (m["a"] - a_his) * h_his
            if abs(s) > TOL:
                if m.get("section_status") == "CONFLICT":
                    sec_conf += s
                else:
                    sec_dim += s
            h = m["a"] * (m["h"] - h_his)
            base_term = m["a"] * (base_his - m["base"]) if base_his is not None and m.get("base") is not None else 0.0
            if m.get("d_ctrl") is None:
                hgt["SPLIT_OPEN"] += h
                continue
            jh = m["a"] * m["d_ctrl"]
            hgt["BASE"] += base_term
            hgt["JOINT_HEAD"] += jh
            hgt["GLOBAL_DEPTH"] += h - jh - base_term
    out["SECTION_CONFLICT"] = round(sec_conf, 6)
    out["SECTION_DIMENSION"] = round(sec_dim, 6)
    out.update({f"HEIGHT_{k}": round(v, 6) for k, v in hgt.items()})
    terms = sum(out[k] for k in TERM_KEYS)
    out["residual"] = round(eng - n_his * a_his * h_his, 6)
    out["bookkeeping_remainder"] = round(out["residual"] - terms, 6)
    if abs(out["bookkeeping_remainder"]) > 1e-5:
        raise Refused(f"terms do not re-add to the residual ({out['bookkeeping_remainder']})")
    return out


TERM_KEYS = ("COUNT", "HELD", "SECTION_CONFLICT", "SECTION_DIMENSION", "HEIGHT_JOINT_HEAD", "HEIGHT_GLOBAL_DEPTH",
             "HEIGHT_BASE", "HEIGHT_SPLIT_OPEN")
# cause class of each term (R-T394-5): traced terms carry a verdict; HELD and UNRESOLVED are summed apart
TERM_CLASS = {"COUNT": "TRACED", "SECTION_DIMENSION": "TRACED", "HEIGHT_JOINT_HEAD": "TRACED",
              "HEIGHT_GLOBAL_DEPTH": "TRACED", "HEIGHT_BASE": "TRACED", "HEIGHT_SPLIT_OPEN": "TRACED_SPLIT_OPEN",
              "HELD": "HELD", "SECTION_CONFLICT": "UNRESOLVED"}


def closure(term_rows):
    """R-T394-5: term_rows [{term, m3, cause}] -> traced / traced_split_open / held / unresolved, residual."""
    acc = {"TRACED": 0.0, "TRACED_SPLIT_OPEN": 0.0, "HELD": 0.0, "UNRESOLVED": 0.0}
    for r in term_rows:
        cause = str(r.get("cause", ""))
        if any(w in cause.lower() for w in ("%", "ratio", "percent", "scal", "factor")):
            raise Refused(f"cause '{cause}' is a ratio / scaling: a residual is closed only by physical causes")
        if not isinstance(r["m3"], (int, float)):
            raise Refused("term m3 not a number")
        k = TERM_CLASS.get(r["term"])
        if k is None:
            raise Refused(f"unknown term {r['term']}")
        acc[k] += r["m3"]
    return {k: round(v, 6) for k, v in acc.items()} | {"residual": round(sum(acc.values()), 6)}


def ring_scope(gross_m2, column_pieces_m2, his_m2, his_h, net_h=None):
    """R-T394-6: a wall ring vs the columns in it. Returns the DOUBLE the gross ring carries (column pieces x his height),
    the net band and, if the height is known, its volume; a height not printed leaves the net volume HELD (None)."""
    if column_pieces_m2 < 0 or column_pieces_m2 >= gross_m2:
        raise Refused("column pieces outside the ring")
    net = round(gross_m2 - column_pieces_m2, 6)
    out = {"net_m2": net, "double_on_gross_m3": None, "net_m3": None}
    if abs(his_m2 - gross_m2) <= 1e-3:
        out["double_on_gross_m3"] = round(column_pieces_m2 * _len(his_h, "his_h"), 6)
    if net_h is not None:
        out["net_m3"] = round(net * _len(net_h, "net_h"), 6)
    return out
