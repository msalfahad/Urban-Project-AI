"""T-395 BEAM_RECON_V1: beam concrete reconciliation, depth basis / length basis / section / count / held (pure rules,
stdlib; any villa).

R-T395-1 (physical beam, depth basis): a beam is its drawn plan (between its own drawn edges, ended at the faces of the
members that own the crossings) x a depth. Two readings exist for the depth: FULL (the printed overall depth, the slab
cut at the beam faces: the slab line is NET of the beam plan) and DOWNSTAND (the printed depth less the slab thickness
under the beam, the slab line GROSS over the beam plan). Each is one solid. A FULL-depth beam under a slab line that is
GROSS over its plan bills b x L x t twice and is refused (DOUBLE); a DOWNSTAND beam under a NET slab loses it (GAP) and is
refused. The depth-basis term between two takeoffs = b x L x t on every run where the two sides use different readings,
and 0 where both use the same one (it is never inferred from 'closer to the freelancer').
R-T395-2 (length basis): with column / beam footprints owned by the support (C1: column > beam > slab), a framed span is
measured FACE TO FACE. A centre-line or through-support length on a framed span bills the support footprint a second
time and is refused for the engine side. On the other side it is a RULE_DIFFERENCE whose volume is b x D x (the support
extent along the axis it runs through): it is the counterpart of the column joint + head (T-394 R-T394-3) or of the
carrier beam's own plan.
R-T395-3 (mark decomposition, exact): per storey and mark, with his section (b_h, D_h):
  SECTION = sum_valued (b_e D_e - b_h D_h) x L_e
  HELD    = - b_h D_h x sum_held L_j          (held runs at their drawn length and his section: never 0, never AGREE)
  LENGTH  = b_h D_h x (sum_valued L_e + sum_held L_j - L_h)
  COUNT   = the whole engine value of a mark he has no row for (+), or his whole row of a mark with no drawn run (-)
The terms re-add to (engine valued - his) to 1e-6 m3 by algebra; anything else is a bookkeeping remainder.
R-T395-4 (length split): LENGTH < 0 (his longer by y) is THROUGH_SUPPORT (traced, RULE_DIFFERENCE) up to the drawn
support allowance S = sum of interior support gaps + sum of end support extents along the axis (columns from their own
outline, carrier beams from their width); the part of y beyond S is UNTRACED (unexplained, printed). LENGTH > 0 (engine
longer) is never closed by a support: it is UNTRACED unless a run-level count names it (engine runs he has no row for).
R-T395-5 (closure, T-385 r2): traced causes, HELD and UNRESOLVED / unexplained are summed apart; a HELD run valued 0, a
cause stated as a ratio / percentage / scaling, a split that does not re-add to its term, or a length in mm / cm is
refused.
"""
from __future__ import annotations

TOL = 1e-6
SUPPORT_TOL_M = 0.01          # drawn-edge fit tolerance on a support allowance (m)
CLASSES = ("AGREE", "ENGINE_RIGHT", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "HELD", "UNRESOLVED")


class Refused(ValueError):
    """A reading the rules refuse (double count, gap, held as 0, ratio closure, unit error)."""


def _num(v, name, *, lo=0.0, hi=100.0):
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        raise Refused(f"{name}: not a number")
    v = float(v)
    if v < lo - TOL:
        raise Refused(f"{name}: {v} below {lo}")
    if v > hi:
        raise Refused(f"{name}: {v} looks like mm or cm; lengths and depths are in m")
    return v


# ---------------------------------------------------------------------------------------------------------- R-T395-1
def beam_solid(b, L, D, *, depth_basis, slab_t, slab_basis):
    """R-T395-1: b x L x (D or D - t) with the slab basis checked against it; returns (m3, basis)."""
    b, L, D, t = _num(b, "b", hi=5), _num(L, "L"), _num(D, "D", hi=5), _num(slab_t, "slab t", hi=1)
    if depth_basis not in ("FULL", "DOWNSTAND") or slab_basis not in ("NET", "GROSS"):
        raise Refused("depth basis FULL / DOWNSTAND and slab basis NET / GROSS only")
    if depth_basis == "FULL" and slab_basis == "GROSS":
        raise Refused("DOUBLE: a full-depth beam under a slab billed gross over the beam plan bills b x L x t twice")
    if depth_basis == "DOWNSTAND" and slab_basis == "NET":
        raise Refused("GAP: a downstand beam under a slab net of the beam plan bills b x L x t nowhere")
    if depth_basis == "DOWNSTAND" and D <= t:
        raise Refused("downstand depth not positive")
    h = D if depth_basis == "FULL" else D - t
    return round(b * L * h, 6), depth_basis


def depth_basis_term(runs, eng_basis, his_basis):
    """R-T395-1: the m3 the depth basis moves between two takeoffs (engine - his); runs = [(b, L, t)]."""
    for x in (eng_basis, his_basis):
        if x not in ("FULL", "DOWNSTAND"):
            raise Refused("depth basis FULL / DOWNSTAND only")
    if eng_basis == his_basis:
        return 0.0
    s = sum(_num(b, "b", hi=5) * _num(L, "L") * _num(t, "t", hi=1) for b, L, t in runs)
    return round(s if eng_basis == "FULL" else -s, 6)


def slab_basis_from_area(his_area, net_area, gross_area, tol_m2=None):
    """Which slab basis a printed slab area is: NET or GROSS of the beam plan, or UNRESOLVED. The printed area must lie
    within tol of one reading (default a third of the gap between them, so the two windows never meet)."""
    a, n, g = _num(his_area, "his area", hi=1e5), _num(net_area, "net", hi=1e5), _num(gross_area, "gross", hi=1e5)
    if g - n <= 0:
        raise Refused("gross not above net")
    tol = (g - n) / 3 if tol_m2 is None else _num(tol_m2, "tol", hi=1e4)
    if 2 * tol >= g - n:
        raise Refused("net and gross areas too close to tell the basis apart at this tolerance")
    if abs(a - n) <= tol:
        return "NET"
    if abs(a - g) <= tol:
        return "GROSS"
    return "UNRESOLVED"


# ---------------------------------------------------------------------------------------------------------- R-T395-2
def engine_length(f2f, ends, *, basis):
    """R-T395-2: the engine's length on a framed span. ends = support extents along the axis (m) at each framed end."""
    f2f = _num(f2f, "face-to-face length")
    if basis != "FACE_TO_FACE" and any(_num(e, "support extent", hi=5) > 0 for e in ends):
        raise Refused(f"{basis} on a framed span: the support footprint is billed by the support (C1); face to face only")
    return f2f


def through_lengths(f2f, gaps, ends):
    """R-T395-2: the readings of one run: face to face, centre line (half of each end support) and overall."""
    f2f = _num(f2f, "f2f")
    g = sum(_num(x, "gap", hi=5) for x in gaps)
    e = [_num(x, "end", hi=5) for x in ends]
    return {"FACE_TO_FACE": round(f2f + 0.0, 6), "INTERIOR_THROUGH": round(f2f + g, 6),
            "CENTRE_LINE": round(f2f + g + sum(e) / 2, 6), "OVERALL": round(f2f + g + sum(e), 6)}


# ---------------------------------------------------------------------------------------------------------- R-T395-3
def mark_split(valued, held, his):
    """R-T395-3. valued = [(b, D, L)], held = [L] (drawn length of each held run), his = [(b, D, L, n)] one section.

    Returns dict of terms in m3 (engine - his) and the residual; the terms re-add to the residual (else Refused)."""
    E = sum(_num(b, "b", hi=5) * _num(D, "D", hi=5) * _num(L, "L") for b, D, L in valued)
    for L in held:
        if L is None:
            raise Refused("a held run without a drawn length cannot be split; carry it as HELD open")
        if L == 0:
            raise Refused("held run given as 0 length")
        _num(L, "held L")
    F = sum(_num(b, "b", hi=5) * _num(D, "D", hi=5) * _num(L, "L") * n for b, D, L, n in his)
    out = {"engine": round(E, 6), "his": round(F, 6), "residual": round(E - F, 6),
           "SECTION": 0.0, "HELD": 0.0, "LENGTH": 0.0, "COUNT": 0.0}
    if not his:
        if not valued and held:
            out["HELD"] = 0.0          # held run, no row of his: nothing on either side, carried as HELD open
        out["COUNT"] = round(E, 6)
        return out
    secs = {(round(b, 4), round(D, 4)) for b, D, _, _ in his}
    if len(secs) != 1:
        raise Refused("his rows of one mark carry more than one section: split the mark by section first")
    bh, Dh = secs.pop()
    Lh = sum(L * n for _, _, L, n in his)
    if not valued and not held:
        out["COUNT"] = round(-F, 6)
        return out
    Le = sum(L for _, _, L in valued)
    out["SECTION"] = round(sum((b * D - bh * Dh) * L for b, D, L in valued), 6)
    out["HELD"] = round(-bh * Dh * sum(held), 6)
    out["LENGTH"] = round(bh * Dh * (Le + sum(held) - Lh), 6)
    out["his_section"] = (bh, Dh)
    out["L_engine_valued"], out["L_held"], out["L_his"] = round(Le, 6), round(sum(held), 6), round(Lh, 6)
    s = out["SECTION"] + out["HELD"] + out["LENGTH"] + out["COUNT"]
    if abs(s - out["residual"]) > 1e-5:
        raise Refused(f"terms {s} do not re-add to the residual {out['residual']}")
    return out


# ---------------------------------------------------------------------------------------------------------- R-T395-4
def length_split(length_m3, b_h, D_h, allowance_m, *, run_count_m3=0.0):
    """R-T395-4: LENGTH -> THROUGH_SUPPORT (traced) + RUN_COUNT (traced, engine runs he has no row for) + UNTRACED."""
    bd = _num(b_h, "b", hi=5) * _num(D_h, "D", hi=5)
    A = _num(allowance_m, "support allowance")
    out = {"THROUGH_SUPPORT": 0.0, "RUN_COUNT": 0.0, "UNTRACED": 0.0}
    rest = float(length_m3)
    if run_count_m3:
        if run_count_m3 < 0 or run_count_m3 - rest > 1e-6:
            raise Refused("a run count larger than the engine-longer length term")
        out["RUN_COUNT"] = round(run_count_m3, 6)
        rest -= run_count_m3
    if rest < 0:
        y = -rest / bd                               # his longer, m
        through = min(y, A + SUPPORT_TOL_M)
        out["THROUGH_SUPPORT"] = round(-through * bd, 6)
        out["UNTRACED"] = round(-(y - through) * bd, 6) if y > through else 0.0
    else:
        out["UNTRACED"] = round(rest, 6)
    if abs(sum(out.values()) - length_m3) > 1e-5:
        raise Refused("length split does not re-add")
    return out


# ---------------------------------------------------------------------------------------------------------- R-T395-5
def closure(items):
    """R-T395-5: items = [(cls, m3)] with cls in TRACED / HELD / UNRESOLVED / UNTRACED; ratio-type values refused."""
    tot = {"TRACED": 0.0, "HELD": 0.0, "UNRESOLVED": 0.0, "UNTRACED": 0.0}
    for cls, v in items:
        if cls not in tot:
            raise Refused(f"closure class {cls}")
        if isinstance(v, str):
            raise Refused("a cause stated as a ratio / percentage / text is refused")
        if v is None:
            raise Refused("an empty cause value")
        tot[cls] += float(v)
    return {k: round(v, 6) for k, v in tot.items()}


def held_value(v):
    """A HELD quantity stays blank: 0 is refused."""
    if v == 0:
        raise Refused("HELD shown as 0")
    return v
