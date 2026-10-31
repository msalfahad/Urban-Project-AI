"""T-398 rules: stair, dome and pool-pump concrete reconciled PIECE BY PIECE against a freelancer's rows (pure, stdlib
only; every villa). Research only: no candidate line, quantity or released cell is changed by these rules.

R-T398-1  PHYSICAL ELEMENT FIRST. A stair is reconciled per piece (flight, landing plate, turn, steps on grade, waist),
          a dome per shell (above the springing) with its ring and drum named apart, a pump room per wall / floor. Each
          piece carries one owner (STAIR, BEAM, SLAB, GROUND_SLAB, COLUMN, DOME, POOL); a piece given two owners
          (a landing in the stair AND in the slab, a stair head in the flight AND in the beam, a ring in the shell AND
          in the beam) is refused (DOUBLE). A piece owned elsewhere is listed, never valued in the stair family.
R-T398-2  FLIGHT VOLUME (owner method Q-19 + Q-47 A): steps = n_triangles x 1/2 x riser x going x width; waist = plan run
          x sec(pitch) x waist thickness x width, the waist measured to the soffit line PARALLEL to the pitch line
          through the nosings minus t / cos. A waist measured to the nosing line AND triangles added on top counts the
          step triangles twice: refused. Pieces inside a beam or slab that bills through are deducted (R-T398-1).
R-T398-3  PLATE COMPARISON. A freelancer flight row 'width x plan length x one thickness' is split against the drawn
          flight in m3, signs engine - freelancer, in this order: WIDTH = -(w_his - w) x L_his x T_his;
          LENGTH = -(L_his - L_drawn) x w x T_his; THICKNESS_BASIS = (steps + waist on the drawn run) - L_drawn x w x
          T_his; OWNERSHIP = -(pieces owned by a beam / slab, Q-62 wedges). The terms sum to the contribution exactly.
          A term is TRACED only when both its sides are drawn / printed figures: a width, length or area of his that no
          drawn one reproduces within 0.01 m (0.01 m2) is UNTRACED (R-T398-4 / -5 alike) and goes to the unexplained column with the
          nearest drawn candidate printed (never 'closest to the freelancer').
R-T398-4  LANDING / PLATE: AREA = (A_drawn - A_his) x t_drawn, THICKNESS = (t_drawn - t_his) x A_his. A printed slab
          thickness ('T 16') governs; a thickness of his that is printed nowhere is a THICKNESS_BASIS cause, ENGINE_RIGHT.
R-T398-5  DOME SHELL = the spherical cap shell above the springing: pi/3 [h^2 (3 R_o - h) - h_i^2 (3 R_i - h_i)],
          R_o = (c^2 / 4 + h^2) / 2h, R_i = R_o - t, h_i = h - t. A developed area x t is compared through the shell's
          own equivalent area (volume / t): AREA = (V / t - A_his) x t. The ring belongs to the beam family (Q-61 C(3))
          and the drum to its own item; a ring or a drum inside the shell figure is refused (R-T398-1).
R-T398-6  CLOSURE (T-385 R-T385-6 applied per piece): contribution = engine valued - freelancer; named = TRACED terms
          only; held = HELD pieces (never 0: a held piece typed as 0 or given a value is refused); unexplained =
          contribution - named - held, printed by part (untraced term, UNRESOLVED component). A freelancer row of
          'count x unit' may be bound by its own printed unit to several pieces (his own element unit, not a ratio);
          any other split of a row (by length share, area share, percentage) is refused.
R-T398-7  NOT DRAWN: an element of his that no sheet of either set draws (searched by layer, text and detail) is a
          SCOPE item: engine HELD named item, never 0 and never valued from his row; a designer fact row is proposed.
"""

from __future__ import annotations

import math

TOL = 0.001                      # m3 closure tolerance
LEN_TOL = 0.01                   # m, R-T398-3 traced-length tolerance
AREA_TOL = 0.01                  # m2
OWNERS = ("STAIR", "BEAM", "SLAB", "GROUND_SLAB", "GROUND_BEAM", "COLUMN", "DOME", "POOL")
VERDICTS = ("AGREE", "ENGINE_RIGHT", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "HELD", "UNRESOLVED")
TRACED_VERDICTS = ("AGREE", "ENGINE_RIGHT", "FREELANCER_RIGHT", "RULE_DIFFERENCE")
TERM_CLASSES = ("WIDTH", "LENGTH", "THICKNESS_BASIS", "OWNERSHIP", "AREA", "COUNT", "SCOPE")
RATIO_WORDS = ("%", "percent", "ratio", "factor", "scaled", "pro rata", "proportion", "share")


class Refused(ValueError):
    """An input that would hide a held quantity as 0, count a solid twice, or close a residual by a ratio."""


def r6(x):
    return None if x is None else round(float(x), 6) + 0.0


def _pos(name, v):
    if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v <= 0:
        raise Refused(f"{name} must be a positive drawn / printed number in metres, got {v!r}")
    if v > 60:
        raise Refused(f"{name} = {v}: not a villa dimension in metres (millimetres passed as metres?)")
    return float(v)


def run_from_risers(segments, unit=1.0):
    """Drawn riser / tread lines [((x1, y1), (x2, y2)), ...] in drawing units (unit = metres per drawing unit) ->
    (number of lines, run between the first and last line, mean line length). Parallel lines only; independent of
    rotation and mirroring (distances along the common normal)."""
    if len(segments) < 2:
        raise Refused("a run needs at least two drawn riser lines")
    if not isinstance(unit, (int, float)) or unit <= 0:
        raise Refused("the drawing unit must be stated")
    (ax, ay), (bx, by) = segments[0]
    L0 = math.hypot(bx - ax, by - ay)
    if L0 == 0:
        raise Refused("zero-length riser line")
    ux, uy = (bx - ax) / L0, (by - ay) / L0
    nx, ny = -uy, ux
    offs, lens = [], []
    for (x1, y1), (x2, y2) in segments:
        L = math.hypot(x2 - x1, y2 - y1)
        if L == 0 or abs(((x2 - x1) * uy - (y2 - y1) * ux) / L) > 1e-3:
            raise Refused("riser lines not parallel: a winder or a curved flight is not a straight run")
        offs.append(((x1 + x2) / 2) * nx + ((y1 + y2) / 2) * ny)
        lens.append(L)
    return len(segments), (max(offs) - min(offs)) * unit, sum(lens) / len(lens) * unit


def check_text(t):
    s = (t or "").lower()
    if not s.strip():
        raise Refused("a cause needs its physical statement")
    for w in RATIO_WORDS:
        if w in s:
            raise Refused(f"a cause stated as a ratio / share is refused ({w!r})")


# ---------------------------------------------------------------- R-T398-1 ownership
def ownership(pieces):
    """pieces: [{'id', 'owners': [..]}]. Each piece exactly one owner; returns {id: owner}."""
    out = {}
    for p in pieces:
        own = p.get("owners") or []
        if len(own) != 1:
            raise Refused(f"{p['id']}: {len(own)} owners {own}: one solid, one owner (DOUBLE or orphan)")
        if own[0] not in OWNERS:
            raise Refused(f"{p['id']}: unknown owner {own[0]!r}")
        if p["id"] in out:
            raise Refused(f"{p['id']}: listed twice")
        out[p["id"]] = own[0]
    return out


# ---------------------------------------------------------------- R-T398-2 flight
def flight(n_triangles, riser, going, width, run, waist, waist_basis="PARALLEL_SOFFIT"):
    """Owner-method gross volume of a straight flight on its drawn run (m, m3)."""
    if waist_basis == "TO_NOSING":
        raise Refused("waist measured to the nosing line with the step triangles added: the triangles twice (R-T398-2)")
    if waist_basis != "PARALLEL_SOFFIT":
        raise Refused(f"unknown waist basis {waist_basis!r}")
    if not isinstance(n_triangles, int) or n_triangles <= 0:
        raise Refused("the number of step triangles is a drawn count")
    r, g, w, L, t = (_pos(n, v) for n, v in (("riser", riser), ("going", going), ("width", width), ("run", run),
                                             ("waist", waist)))
    sec = math.hypot(r, g) / g
    steps = n_triangles * 0.5 * r * g * w
    wst = L * sec * t * w
    return {"steps_m3": r6(steps), "waist_m3": r6(wst), "gross_m3": r6(steps + wst), "sec": sec}


def plate_terms(engine_gross, owned_deductions, run, width, his_len, his_width, his_thk, drawn_lengths=()):
    """R-T398-3: split (engine net - his plate) into WIDTH / LENGTH / THICKNESS_BASIS / OWNERSHIP terms in m3."""
    L, w, Lh, wh, Th = (_pos(n, v) for n, v in (("run", run), ("width", width), ("his length", his_len),
                                                ("his width", his_width), ("his thickness", his_thk)))
    g = float(engine_gross)
    ded = sum(float(d) for d in owned_deductions)
    if any(float(d) < 0 for d in owned_deductions):
        raise Refused("an owned-elsewhere deduction is a positive solid")
    cands = sorted(set(float(x) for x in drawn_lengths) | {L})
    near = min(cands, key=lambda x: abs(x - Lh))
    terms = [
        {"term": "WIDTH", "m3": -(wh - w) * Lh * Th, "traced": abs(wh - w) <= LEN_TOL},
        {"term": "LENGTH", "m3": -(Lh - L) * w * Th, "traced": abs(near - Lh) <= LEN_TOL,
         "nearest_drawn_m": near},
        {"term": "THICKNESS_BASIS", "m3": g - L * w * Th, "traced": True},
        {"term": "OWNERSHIP", "m3": -ded, "traced": True},
    ]
    for t in terms:
        t["m3"] = r6(t["m3"])
    return terms


# ---------------------------------------------------------------- R-T398-4 landing
def landing_terms(area, thk, his_area, his_thk, drawn_areas=()):
    A, t, Ah, th = (_pos(n, v) for n, v in (("area", area), ("thickness", thk), ("his area", his_area),
                                            ("his thickness", his_thk)))
    cands = sorted(set(float(x) for x in drawn_areas) | {A})
    near = min(cands, key=lambda x: abs(x - Ah))
    return [{"term": "AREA", "m3": r6((A - Ah) * t), "traced": abs(near - Ah) <= AREA_TOL, "nearest_drawn_m2": near},
            {"term": "THICKNESS_BASIS", "m3": r6((t - th) * Ah), "traced": True}]


# ---------------------------------------------------------------- R-T398-5 dome
def cap_shell(chord, rise, thk, includes=()):
    if set(includes) & {"RING", "DRUM"}:
        raise Refused(f"the shell is measured above the springing; {sorted(set(includes))} belong to their own items")
    c, h, t = _pos("chord", chord), _pos("rise", rise), _pos("thickness", thk)
    if t >= h:
        raise Refused("shell thickness not below the rise")
    Ro = (c * c / 4 + h * h) / (2 * h)
    Ri, hi = Ro - t, h - t
    v = math.pi / 3 * (h * h * (3 * Ro - h) - hi * hi * (3 * Ri - hi))
    return {"R_o": r6(Ro), "V_m3": r6(v), "outer_area_m2": r6(2 * math.pi * Ro * h), "equiv_area_m2": r6(v / t)}


def shell_terms(shell_v, thk, his_area, his_thk, drawn_areas=()):
    t, Ah, th = _pos("thickness", thk), _pos("his area", his_area), _pos("his thickness", his_thk)
    v = float(shell_v)
    cands = sorted(set(float(x) for x in drawn_areas) | {v / t})
    near = min(cands, key=lambda x: abs(x - Ah))
    return [{"term": "AREA", "m3": r6((v / t - Ah) * t), "traced": abs(near - Ah) <= AREA_TOL, "nearest_drawn_m2": near},
            {"term": "THICKNESS_BASIS", "m3": r6((t - th) * Ah), "traced": True}]


# ---------------------------------------------------------------- R-T398-6 closure
def component(c):
    """c: {'id','element','pieces':[{'id','state':'VALUED'|'HELD'|'OWNED_ELSEWHERE','m3' (VALUED),
    'low','high' (HELD, optional)}], 'his_m3' (his part, by his own printed unit), 'his_unit' (str), 'verdict',
    'cause', 'terms' (optional list from plate_terms / landing_terms / shell_terms)}."""
    cid = c["id"]
    check_text(c.get("cause"))
    if c.get("verdict") not in VERDICTS:
        raise Refused(f"{cid}: unknown verdict {c.get('verdict')!r}")
    for k in ("contribution_m3", "named_m3", "unexplained_m3", "held_m3", "engine_m3"):
        if k in c:
            raise Refused(f"{cid}: {k} is computed, never typed in")
    if "his_split" in c:
        raise Refused(f"{cid}: a freelancer row split other than by his own printed unit is refused (R-T398-6)")
    valued, held_n, lo, hi, unb = 0.0, 0, 0.0, 0.0, 0
    for p in c.get("pieces", []):
        st = p.get("state")
        if st == "VALUED":
            valued += float(p["m3"])
        elif st == "HELD":
            if "m3" in p:
                raise Refused(f"{cid}/{p['id']}: a HELD piece carries no value (never 0, never a figure)")
            held_n += 1
            if p.get("low") is None or p.get("high") is None:
                unb += 1
            else:
                lo += float(p["low"])
                hi += float(p["high"])
        elif st in ("OWNED_ELSEWHERE", "EXCLUDED"):
            if "m3" in p and st == "EXCLUDED":
                raise Refused(f"{cid}/{p['id']}: an EXCLUDED (not applicable) line carries no value")
        else:
            raise Refused(f"{cid}/{p['id']}: unknown piece state {st!r}")
    his = float(c.get("his_m3", 0.0))
    contrib = valued - his
    v = c["verdict"]
    n_val = sum(1 for p in c.get("pieces", []) if p.get("state") == "VALUED")
    if held_n and not n_val and v != "HELD":
        raise Refused(f"{cid}: engine side wholly HELD: verdict HELD, not {v}")
    if v == "HELD" and not held_n and not c.get("held_named_item"):
        raise Refused(f"{cid}: HELD needs a held piece or a named held item")
    if v == "AGREE" and (held_n or abs(contrib) > TOL):
        raise Refused(f"{cid}: AGREE only with no held part and a contribution within {TOL} m3")
    terms = c.get("terms")
    named = held = unexpl = 0.0
    untraced = 0.0
    if terms is not None and v not in TRACED_VERDICTS:
        raise Refused(f"{cid}: a {v} component cannot carry traced terms")
    if v in TRACED_VERDICTS:
        if held_n:
            raise Refused(f"{cid}: a traced component with a held piece: split the held piece into its own component")
        if terms:
            for t in terms:
                if t["term"] not in TERM_CLASSES:
                    raise Refused(f"{cid}: unknown term {t['term']!r}")
            s = sum(t["m3"] for t in terms)
            if abs(s - contrib) > TOL:
                raise Refused(f"{cid}: terms {s:.6f} do not sum to the contribution {contrib:.6f}")
            named = sum(t["m3"] for t in terms if t["traced"])
            untraced = sum(t["m3"] for t in terms if not t["traced"])
        else:
            named = contrib
        unexpl = contrib - named
    elif v == "HELD":
        held = contrib
    else:
        unexpl = contrib
    return {"id": cid, "element": c.get("element", ""), "engine_valued_m3": r6(valued), "held_pieces": held_n,
            "held_low_m3": r6(lo) if held_n > unb else None, "held_high_m3": r6(hi) if held_n and not unb else None,
            "held_unbounded": unb, "his_unit": c.get("his_unit", ""), "freelancer_m3": r6(his),
            "contribution_m3": r6(contrib), "named_m3": r6(named), "held_named_m3": r6(held),
            "unexplained_m3": r6(unexpl), "untraced_term_m3": r6(untraced),
            "terms": "; ".join(f"{t['term']} {t['m3']:+.6f}{'' if t['traced'] else ' UNTRACED'}" for t in (terms or [])),
            "verdict": v, "cause": c["cause"], "evidence": c.get("evidence", "")}


def family(name, comps, his_rows_total):
    """Closure over the components of one family; his rows must be bound in full by their own units."""
    bound_his_total = sum(float(c.get("his_m3", 0.0)) for c in comps)
    if abs(float(his_rows_total) - float(bound_his_total)) > TOL:
        raise Refused(f"{name}: his rows {his_rows_total:.6f} bound {bound_his_total:.6f}: a row part left unbound")
    seen = set()
    for c in comps:
        for p in c.get("pieces", []):
            if p["id"] in seen:
                raise Refused(f"piece {p['id']} bound twice")
            seen.add(p["id"])
    rows = [component(c) for c in comps]
    resid = sum(r["contribution_m3"] for r in rows)
    named = sum(r["named_m3"] for r in rows)
    held = sum(r["held_named_m3"] for r in rows)
    return rows, {"family": name, "engine_valued_m3": r6(sum(r["engine_valued_m3"] for r in rows)),
                  "freelancer_m3": r6(his_rows_total), "residual_m3": r6(resid), "named_m3": r6(named),
                  "held_named_m3": r6(held), "unexplained_m3": r6(resid - named - held),
                  "untraced_terms_m3": r6(sum(r["untraced_term_m3"] for r in rows)),
                  "unresolved_m3": r6(sum(r["unexplained_m3"] for r in rows if r["verdict"] == "UNRESOLVED")),
                  "held_pieces": sum(r["held_pieces"] for r in rows)}
