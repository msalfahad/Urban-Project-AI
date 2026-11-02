"""BLINDING_PIECE_LEDGER_V1 (T-445, research, unwired; shapely for plan geometry, otherwise stdlib).

The physical blinding of a villa's foundation as PIECES, every piece once, each with its own drawing source, plan,
thickness source, volume, status and the ONE candidate line that carries it; then (a) each candidate blinding line
re-added from its pieces, (b) a lane I proposal per line (VALUE / SPLIT / HELD), (c) the comparison residual against
a reference figure (e.g. one plate over a rectangle) split term by term, no piece in two terms.

Physical element (ERS s.2.1). Blinding = a plain-concrete layer of a PRINTED thickness t under a member, on the
formation / compacted fill. Its plan is the member's drawn plan grown by the PRINTED projection p on each side of the
member's GOVERNING detail (mitred corners: a rectangle L x W -> (L + 2p)(W + 2p)). It exists only where a detail draws
it (in the development set: under isolated footings and the four ground-beam sections; 'COMPACTED SOIL' under the
ground slab; no strap section). It is not the underlay (screed / membrane: other trades) and not the footing.

Rules (proposed R-BLIND-PIECE-1, every villa; provenance T-445 on the merged T-233 / T-320 / T-322 ledgers; a new
rule version when adopted):
  1. Thickness: only a PRINTED t gives a volume (Refused otherwise: BLINDING_THICKNESS_NOT_PRINTED).
  2. Projection: PRINTED on the member's governing detail -> the piece is DRAWING-CONFIRMED. INHERITED (printed only
     on a typical detail of another element type) or SCALED -> the piece is HELD with the AT_LEAST bound
     (member plan x t) and its readings listed; it becomes ESTIMATED only under a named owner / RFI label that names
     the reading (never VERIFIED, never 0).
  3. One layer: where grown plans of two measured members overlap, the overlap is counted once and belongs to the
     DEEPER member (R-CONC-OWN-1); equal depths overlapping -> Refused (OVERLAP_OWNER_TIE), never guessed.
     A HELD piece's plan is unknown, so it must not overlap any neighbour in ANY of its readings (Refused otherwise).
  4. A boundary the layer cannot be assumed to cross (the plot line): the part beyond it is its own piece, HELD
     (0 .. outside x t) until the designer answers; the inside part keeps its own status.
  5. A member carrying two readings of its own size (two tags on one outline) is a CONFLICT piece: the scenario
     figures are kept as a range, never one picked, never summed.
  6. Members with no printed blinding geometry (e.g. straps: no section; ground beams whose section choice is open)
     enter as HELD_RANGE pieces with the candidate's range and the blocker; never 0 unless 0 is a stated reading.
  7. A 'plate' (one layer over a whole rectangle or footprint) is NOT a piece unless a detail draws it: Refused
     (PLATE_NOT_DRAWN). It can only be a REFERENCE figure for a comparison, whose surplus over the pieces is a scope
     RULE_DIFFERENCE.
  8. Every piece maps to exactly one candidate line or is MISSING; every line re-adds from its pieces (named readings)
     within TOL; a line with VERIFIED and unverified pieces is SPLIT (value the verified pieces, hold the rest).
Units: 'm' or 'mm' declared on the geometry; mirror / rotation give identical areas.
"""
from __future__ import annotations

from shapely.geometry import Polygon
from shapely.ops import unary_union

METHOD_ID = "BLINDING_PIECE_LEDGER_V1"
DC, VERIFIED, HELD, ESTIMATED, CONFLICT = "DRAWING-CONFIRMED", "VERIFIED", "HELD", "ESTIMATED", "CONFLICT"
UNMEASURED = "HELD (UNMEASURED: no figure)"
AT_LEAST = "HELD (AT_LEAST bound)"
PRINTED, INHERITED, SCALED = "PRINTED", "INHERITED", "SCALED_NOT_PRINTED"
VALUE, SPLIT, KEEP_HELD = "VALUE", "SPLIT", "HELD"
TOL = 0.0005
_UNIT = {"m": 1.0, "mm": 0.001}


class Refused(ValueError):
    def __init__(self, code, msg=""):
        super().__init__(f"{code}: {msg}" if msg else code)
        self.code = code


def _r(x, n=7):
    return None if x is None else round(x + 0.0, n)


def _poly(pts, s):
    if not pts or len(pts) < 3:
        raise Refused("OUTLINE_NOT_GIVEN", repr(pts))
    p = Polygon([(float(x) * s, float(y) * s) for x, y in pts])
    if not p.is_valid or p.area <= 0:
        raise Refused("OUTLINE_INVALID", repr(pts))
    return p


def grow(poly, p):
    """Plan grown by p on every side, mitred (a rectangle stays a rectangle)."""
    if p is None or p < 0:
        raise Refused("PROJECTION_NOT_GIVEN", repr(p))
    return poly.buffer(p, join_style=2, mitre_limit=10.0)


# ---------------------------------------------------------------- 1. plan geometry -> plan records
def plan_from_geometry(members, boundary, unit, projection_m):
    """members: [{'id', 'outline': [(x, y), ...], 'depth_m'}] measured with ONE printed projection_m (metres).
    boundary: plot-line polygon or None. Returns {id: {'outline_m2', 'grown_m2', 'given_m2', 'own_m2', 'inside_m2',
    'outside_m2', 'given_to': {id: m2}}}: one-owner overlap by depth (rule 3), inside / beyond the boundary (rule 4)."""
    if unit not in _UNIT:
        raise Refused("UNIT_NOT_DECLARED", repr(unit))
    s = _UNIT[unit]
    ids = [m["id"] for m in members]
    if len(ids) != len(set(ids)):
        raise Refused("MEMBER_TWICE", repr(ids))
    P = {m["id"]: _poly(m["outline"], s) for m in members}
    D = {m["id"]: float(m["depth_m"]) for m in members}
    for k in ids:
        inside = [n for n in ids if n != k and P[k].intersection(P[n]).area >= P[n].area - 1e-9]
        if inside:
            raise Refused("PLATE_COVERS_MEMBERS", f"{k} contains the outlines {inside}: one layer over several members "
                                                  "is a plate, not a drawn member's blinding (rule 7)")
    G = {k: grow(P[k], projection_m) for k in P}
    B = _poly(boundary, s) if boundary is not None else None
    out = {}
    for k in ids:
        given, taken_by = 0.0, {}
        owners = []
        for n in ids:
            if n == k:
                continue
            a = G[k].intersection(G[n]).area
            if a <= 1e-9:
                continue
            if abs(D[n] - D[k]) < 1e-9:
                raise Refused("OVERLAP_OWNER_TIE", f"{k} / {n} overlap {a:.6f} m2 at equal depth")
            if D[n] > D[k]:
                owners.append(G[n])
                taken_by[n] = _r(a)
        own = G[k].difference(unary_union(owners)) if owners else G[k]
        given = G[k].area - own.area
        ins = own.intersection(B).area if B is not None else own.area
        out[k] = {"outline_m2": _r(P[k].area), "grown_m2": _r(G[k].area), "given_m2": _r(given),
                  "own_m2": _r(own.area), "inside_m2": _r(ins), "outside_m2": _r(own.area - ins), "given_to": taken_by}
    union = unary_union(list(G.values()))
    out["_union"] = {"union_m2": _r(union.area), "sum_grown_m2": _r(sum(g.area for g in G.values())),
                     "inside_m2": _r(union.intersection(B).area if B is not None else union.area)}
    return out


def clearance_ok(held_outline, held_readings_m, neighbours_grown, unit):
    """Rule 3 for a HELD piece: in every reading its grown plan must not touch a neighbour's grown plan."""
    s = _UNIT[unit]
    h = _poly(held_outline, s)
    for p in held_readings_m:
        g = grow(h, p)
        for nid, pts in neighbours_grown.items():
            if g.intersection(_poly(pts, s)).area > 1e-9:
                raise Refused("HELD_PIECE_OVERLAP_UNRESOLVED", f"reading p={p} touches {nid}")
    return True


# ---------------------------------------------------------------- 2. pieces
def _piece(pid, element, line, status, value=None, low=None, high=None, plan_m2=None, t=None, source="",
           thickness_source="", blocker="", readings=None, verdict="", inside_ref=None):
    if status in (HELD, AT_LEAST, CONFLICT, UNMEASURED) and value is not None:
        raise Refused("HELD_WITH_VALUE", pid)
    if status in (DC, VERIFIED, ESTIMATED) and value is None:
        raise Refused("VALUE_MISSING", pid)
    if value is not None and value <= 0:
        raise Refused("ZERO_OR_NEGATIVE_PIECE", f"{pid} {value}")
    if status == VERIFIED and not verdict:
        raise Refused("VERIFIED_WITHOUT_VERDICT", pid)
    if status in (HELD, AT_LEAST, CONFLICT, UNMEASURED) and not blocker:
        raise Refused("HELD_WITHOUT_BLOCKER", pid)
    lo = value if value is not None else low
    hi = value if value is not None else high
    if status == UNMEASURED:
        if lo is not None or hi is not None:
            raise Refused("UNMEASURED_WITH_FIGURE", pid)
    elif lo is None or hi is None or lo > hi + 1e-12:
        raise Refused("RANGE_INVALID", f"{pid} {lo} .. {hi}")
    return {"id": pid, "element": element, "line": line, "status": status, "value": _r(value),
            "low": _r(lo), "high": _r(hi), "plan_m2": _r(plan_m2), "t_m": t, "source": source,
            "thickness_source": thickness_source, "blocker": blocker, "readings": readings or {}, "verdict": verdict,
            "inside_reference": inside_ref if inside_ref is not None else True}


def build(spec):
    """spec: {'thickness': {'value', 'basis', 'source'}, 'measured': [{'id', 'element', 'line', 'inside_m2',
    'outside_m2', 'source', 'verdict'?}], 'beyond_boundary': {'line', 'blocker'}, 'held_projection': [{'id', 'element',
    'line', 'outline_m2', 'readings': {name: p}, 'basis', 'estimate'?: {'label', 'reading'}, 'blocker', 'plan_fn'}],
    'conflict': [{'id', 'element', 'line', 'scenarios': {name: m3}, 'blocker'}], 'held_range': [{'id', 'element',
    'line', 'low', 'high', 'blocker'}], 'plates': [...] (refused), 'projection': {'value', 'basis', 'source'}}"""
    th = spec.get("thickness") or {}
    if th.get("basis") != PRINTED or not th.get("value"):
        raise Refused("BLINDING_THICKNESS_NOT_PRINTED", repr(th))
    t = float(th["value"])
    if spec.get("plates"):
        raise Refused("PLATE_NOT_DRAWN", "a layer over a whole rectangle is a reference figure, never a piece")
    pr = spec.get("projection") or {}
    pieces = []
    meas = spec.get("measured", [])
    if meas and pr.get("basis") != PRINTED:
        raise Refused("PROJECTION_NOT_PRINTED_FOR_MEASURED", repr(pr))
    out_total = 0.0
    for m in meas:
        st = VERIFIED if m.get("verdict") else DC
        pieces.append(_piece(f"{m['id']}:IN", m["element"], m["line"], st, value=m["inside_m2"] * t,
                             plan_m2=m["inside_m2"], t=t, source=m["source"], thickness_source=th["source"],
                             verdict=m.get("verdict", "")))
        out_total += m.get("outside_m2", 0.0)
    if out_total > 1e-9:
        bb = spec.get("beyond_boundary") or {}
        if not bb.get("blocker"):
            raise Refused("BEYOND_BOUNDARY_WITHOUT_BLOCKER")
        per = {m["id"]: _r(m["outside_m2"]) for m in meas if m.get("outside_m2", 0) > 1e-9}
        pieces.append(_piece("BEYOND_BOUNDARY", "blinding projection beyond the boundary", bb["line"], HELD,
                             low=0.0, high=out_total * t, plan_m2=out_total, t=t, blocker=bb["blocker"],
                             readings={"per_member_m2": per}, inside_ref=False))
    for h in spec.get("held_projection", []):
        if h["basis"] not in (INHERITED, SCALED):
            raise Refused("HELD_PROJECTION_BASIS", h["basis"])
        fn = h["plan_fn"]
        rd = {k: _r(fn(p) * t) for k, p in h["readings"].items()}
        bound = h["outline_m2"] * t
        if min(rd.values()) < bound - 1e-12:
            raise Refused("READING_BELOW_AT_LEAST", h["id"])
        est = h.get("estimate")
        if est:
            if not est.get("label") or est.get("reading") not in rd:
                raise Refused("ESTIMATE_WITHOUT_LABEL_OR_READING", h["id"])
            pieces.append(_piece(h["id"], h["element"], h["line"], ESTIMATED, value=rd[est["reading"]],
                                 plan_m2=fn(h["readings"][est["reading"]]), t=t, thickness_source=th["source"],
                                 blocker=h["blocker"], readings=dict(rd, at_least=_r(bound),
                                                                     label=est["label"])))
            pieces[-1]["low"], pieces[-1]["high"] = min(rd.values()), max(rd.values())
        else:
            pieces.append(_piece(h["id"], h["element"], h["line"], AT_LEAST, low=min(rd.values()),
                                 high=max(rd.values()), t=t, thickness_source=th["source"], blocker=h["blocker"],
                                 readings=dict(rd, at_least=_r(bound))))
    for c in spec.get("conflict", []):
        sc = c["scenarios"]
        if len(sc) < 2:
            raise Refused("CONFLICT_NEEDS_TWO_READINGS", c["id"])
        pieces.append(_piece(c["id"], c["element"], c["line"], CONFLICT, low=min(sc.values()), high=max(sc.values()),
                             t=t, blocker=c["blocker"], readings={k: _r(v) for k, v in sc.items()}))
    for g in spec.get("held_range", []):
        pieces.append(_piece(g["id"], g["element"], g["line"], HELD, low=g["low"], high=g["high"], t=t,
                             blocker=g["blocker"], readings=g.get("readings")))
    for u in spec.get("unmeasured", []):
        pieces.append(_piece(u["id"], u["element"], u.get("line", "MISSING"), UNMEASURED, t=t, blocker=u["blocker"],
                             source=u.get("source", ""), readings=u.get("readings")))
    ids = [p["id"] for p in pieces]
    if len(ids) != len(set(ids)):
        raise Refused("PIECE_TWICE", repr(ids))
    return pieces


# ---------------------------------------------------------------- 3. lines
def map_lines(pieces, lines):
    """lines: {line_id: {'state', 'value'?, 'low'?, 'high'?, 'reading'?: {piece_id: reading name}}}.
    Re-adds each line from its pieces (named readings for held pieces) and gives the lane I proposal."""
    by = {}
    for p in pieces:
        if p["line"] not in lines:
            if p["line"] != "MISSING":
                raise Refused("PIECE_ON_UNKNOWN_LINE", f"{p['id']} -> {p['line']}")
            continue
        by.setdefault(p["line"], []).append(p)
    out = {}
    for lid, L in lines.items():
        ps = by.get(lid, [])
        if not ps:
            raise Refused("LINE_WITHOUT_PIECE", lid)
        rmap = L.get("reading", {})
        lo = hi = 0.0
        for p in ps:
            if p["id"] in rmap:
                v = p["readings"][rmap[p["id"]]]
                lo += v
                hi += v
            elif p["value"] is not None:
                lo += p["value"]
                hi += p["value"]
            elif p["id"] in L.get("at_high", ()):
                lo += p["high"]
                hi += p["high"]
            else:
                lo += p["low"]
                hi += p["high"]
        llo = L.get("value", L.get("low"))
        lhi = L.get("value", L.get("high"))
        closes = abs(lo - llo) <= TOL and abs(hi - lhi) <= TOL
        if not closes:
            raise Refused("LINE_DOES_NOT_RE_ADD", f"{lid}: pieces {lo:.6f} .. {hi:.6f} vs line {llo} .. {lhi}")
        ver = [p for p in ps if p["status"] == VERIFIED]
        rest = [p for p in ps if p["status"] != VERIFIED]
        if ver and rest:
            prop = SPLIT
        elif ver:
            prop = VALUE
        else:
            prop = KEEP_HELD
        out[lid] = {"pieces": [p["id"] for p in ps], "pieces_low": _r(lo), "pieces_high": _r(hi),
                    "line_low": llo, "line_high": lhi, "residual_low": _r(lo - llo), "residual_high": _r(hi - lhi),
                    "proposal": prop, "value_m3": _r(sum(p["value"] for p in ver)),
                    "held": [{"id": p["id"], "status": p["status"], "low": p["low"], "high": p["high"],
                              "blocker": p["blocker"]} for p in rest]}
    return out


# ---------------------------------------------------------------- 4. comparison against a reference figure
def reconcile_reference(pieces, valued_ids, reference_m3, reference_basis):
    """residual = engine valued - reference, split into one term per piece inside the reference plan
    (engine valued figure of the piece - the piece) and the scope RULE_DIFFERENCE (pieces - reference).
    Pieces beyond the reference plan (inside_reference False) are listed beside: 0 - 0, never a term.
    Closes exactly at both range ends; no piece in two terms."""
    if not reference_basis:
        raise Refused("REFERENCE_WITHOUT_BASIS")
    unknown = set(valued_ids) - {p["id"] for p in pieces}
    if unknown:
        raise Refused("VALUED_UNKNOWN_PIECE", repr(sorted(unknown)))
    for v in valued_ids:
        p = next(q for q in pieces if q["id"] == v)
        if p["value"] is None:
            raise Refused("HELD_PIECE_VALUED", v)
    terms, beside, no_figure = [], [], []
    s_lo = s_hi = e_val = 0.0
    for p in pieces:
        if not p["inside_reference"]:
            beside.append({"piece": p["id"], "low": p["low"], "high": p["high"], "note": "beyond the reference plan"})
            continue
        if p["status"] == UNMEASURED:
            no_figure.append(p["id"])
            continue
        if p["id"] in valued_ids:
            # a valued piece meets the reference at its valued figure: term 0, the piece enters at that figure
            ev, lo, hi = p["value"], p["value"], p["value"]
        else:
            ev, lo, hi = 0.0, p["low"], p["high"]
        e_val += ev
        # term = ev - piece; the low end of the term uses the piece's high end
        terms.append({"piece": p["id"], "status": p["status"], "valued": p["id"] in valued_ids,
                      "blocker": p["blocker"], "term_low": _r(ev - hi), "term_high": _r(ev - lo)})
        s_lo += lo
        s_hi += hi
    rd = {"term_low": _r(s_lo - reference_m3), "term_high": _r(s_hi - reference_m3),
          "cause": "RULE_DIFFERENCE: " + reference_basis,
          "contains_unmeasured_pieces": no_figure}
    residual = e_val - reference_m3
    lo_sum = sum(t["term_low"] for t in terms) + rd["term_high"]
    hi_sum = sum(t["term_high"] for t in terms) + rd["term_low"]
    if abs(lo_sum - residual) > 1e-6 or abs(hi_sum - residual) > 1e-6:
        raise Refused("REFERENCE_SPLIT_DOES_NOT_CLOSE", f"{lo_sum} / {hi_sum} vs {residual}")
    return {"engine_valued_m3": _r(e_val), "reference_m3": reference_m3, "residual_m3": _r(residual),
            "terms": terms, "rule_difference": rd, "beside": beside,
            "closes": True}
