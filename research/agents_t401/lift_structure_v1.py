"""LIFT_STRUCTURE_V1 (T-401, research, unwired, stdlib only): the lift as ONE physical element from the founding level to
the roof, split into components, each owned by ONE line (or named MISSING), each with its own status. Any villa without
a basement; the development villa is one input (t401_alsenan.py).

Physical element (ERS s.2.1), bottom up:
  RAFT         the lift footing (raft) L x W x H: the footing line's (CONC.FOOTING); listed, never re-added.
  PIT FLOOR    = raft top: no volume of its own (R-LIFT-BASE-1).
  PIT WALLS    RC ring ON the raft top, plan = drawn ring NET of the lift column sections in its band (R-T394-6); height
               = raft top -> WALL TOP. The wall top is the datum the governing detail draws (ST p.14 of the development
               set: flush with the slab-on-grade TOP, below the F.F.L.). A pit depth quoted from the lowest landing
               F.F.L. (the usual lift-supplier datum) gives the wall height only after the floor build-up F.F.L. -> slab
               top is subtracted: depth_FFL - build_up. Either fact missing -> the wall concrete is HELD (value None).
  SHAFT VOID   the shaft inside the ring at ground level: NOT ground slab (the pit is open), never a slab line's.
  TIE BEAMS    ring beams between the lift columns at a printed height where a storey (FFL -> FFL) exceeds a printed
               limit (ST p.8 note 19 of the development set: 3.00 m when the storey exceeds 4.30 m); length = the clear
               ring runs between column faces; section only if printed, else HELD.
  FLOOR RING   at each suspended floor the beams on the ring band (beam lines; listed, never re-added) and the shaft
               slab state: OPENING (shaft area out of the slab line) or CAP (top of the shaft closed: the shaft panel
               is in the roof slab line = the 'overrun / machine slab' when no separate overrun is drawn).
  SHAFT WALLS  above the wall top: the trade the drawings give ('AS PER PLAN': blockwork on the architectural plans);
               never also an RC wall line.
  COLUMNS      the lift columns / necks: column lines (R-CONC-OWN-1), never also in the ring.

Rules (R-T401-1 .. 5, proposed, every villa; provenance T-401 on ST p.8 / p.14 and the route G plans of the development
set; adopting them is a new rule version):
  R-T401-1  each component is bound to exactly one candidate line id or is MISSING (named, with owner trade); a component
            bound to two lines, or a line bound to two components of different trades, is refused.
  R-T401-2  the pit-wall height is raft top -> wall top on the governing detail's datum; a pit depth quoted to the F.F.L.
            is reduced by the printed build-up; an unprinted build-up or depth leaves the wall HELD; a depth taken from a
            neck height, a default, a neighbour villa or the freelancer is refused (DEPTH_DEFAULTED).
  R-T401-3  the ring band is the pit wall's, the column sections the columns', the shaft void nobody's: a slab line that
            also covers the ring band (PIT_WALL_IN_SLAB_AND_WALL), a wall measured gross through the columns
            (COLUMN_IN_RING_AND_COLUMN) or a slab over the shaft void at ground level (SHAFT_VOID_AS_SLAB) is refused.
  R-T401-4  a HELD or MISSING component carries value None (never 0) and the exact missing fact; a bound only from drawn
            geometry (HELD_AS_ZERO / BOUND_NOT_DRAWN refused).
  R-T401-5  overlap census on the plan, per level band: shared plan area of two VALUED lines in one band = DOUBLE
            (named with both ids and the area); a component plan claimed by no line = GAP (named); 0 DOUBLE required.
Units 'm', 'cm', 'mm' declared; mirror and quarter turns give identical results (axis-aligned rectangles).
"""
from __future__ import annotations

METHOD_ID = "LIFT_STRUCTURE_V1"
DC, HELD, MISSING, LISTED = "DRAWING-CONFIRMED", "HELD", "MISSING", "LISTED"
PRINTED, SUPPLIER = "PRINTED", "SUPPLIER"
WALL_TOP_SLAB, WALL_TOP_FFL = "SLAB_ON_GRADE_TOP", "FFL"
_UNIT = {"m": 1.0, "cm": 0.01, "mm": 0.001}
TOL = 1e-6


class Refused(ValueError):
    def __init__(self, code, msg=""):
        super().__init__(f"{code}: {msg}" if msg else code)
        self.code = code


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def scale(unit):
    if unit not in _UNIT:
        raise Refused("UNIT_NOT_DECLARED", repr(unit))
    return _UNIT[unit]


def rect(r, s=1.0):
    if r is None or len(r) != 4:
        raise Refused("RECT_NOT_GIVEN", repr(r))
    x0, y0, x1, y1 = (float(v) * s for v in r)
    return (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))


def area(r):
    return (r[2] - r[0]) * (r[3] - r[1])


def inter(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    return (x0, y0, x1, y1) if x1 > x0 + TOL and y1 > y0 + TOL else None


def iarea(a, b):
    i = inter(a, b)
    return area(i) if i else 0.0


def inside(a, b):
    return a[0] >= b[0] - TOL and a[1] >= b[1] - TOL and a[2] <= b[2] + TOL and a[3] <= b[3] + TOL


def _sub(iv, cuts):
    out = [iv]
    for c0, c1 in cuts:
        nxt = []
        for a0, a1 in out:
            if c1 <= a0 + TOL or c0 >= a1 - TOL:
                nxt.append((a0, a1))
                continue
            if c0 > a0 + TOL:
                nxt.append((a0, c0))
            if c1 < a1 - TOL:
                nxt.append((c1, a1))
        out = nxt
    return out


def ring_geometry(outer, inner, cols):
    """Gross and net ring plan (m2) and the clear wall runs between column faces (m), measured on the ring centreline
    band per side; columns must lie inside the ring band and touch both faces or one face."""
    if not inside(inner, outer):
        raise Refused("SHAFT_NOT_INSIDE_RING")
    t = {"S": inner[1] - outer[1], "N": outer[3] - inner[3], "W": inner[0] - outer[0], "E": outer[2] - inner[2]}
    if min(t.values()) <= TOL:
        raise Refused("RING_WITHOUT_THICKNESS")
    gross = area(outer) - area(inner)
    col_in_band = 0.0
    for c in cols:
        if iarea(c, inner) > TOL:
            raise Refused("COLUMN_INTO_SHAFT", repr(c))
        if not inter(c, outer):
            raise Refused("COLUMN_NOT_ON_RING", repr(c))
        col_in_band += iarea(c, outer)
    net = gross - col_in_band
    sides = {"S": (outer[0], outer[1], outer[2], inner[1]), "N": (outer[0], inner[3], outer[2], outer[3]),
             "W": (outer[0], inner[1], inner[0], inner[3]), "E": (inner[2], inner[1], outer[2], inner[3])}
    runs = {}
    for k, band in sides.items():
        horiz = k in ("S", "N")
        iv = (band[0], band[2]) if horiz else (band[1], band[3])
        cuts = []
        for c in cols:
            if inter(c, band):
                cuts.append((c[0], c[2]) if horiz else (c[1], c[3]))
        # corners belong to the S / N bands; W / E runs are between the S / N bands already
        runs[k] = sum(b - a for a, b in _sub(iv, cuts))
    return {"gross_m2": gross, "columns_in_band_m2": col_in_band, "net_m2": net, "runs_m": runs,
            "run_total_m": sum(runs.values()), "thickness_m": t}


def wall_height(raft_top, wall_top_datum, pit_depth, build_up):
    """R-T401-2. pit_depth: {'value': m or None, 'basis': PRINTED|SUPPLIER|..., 'datum': SLAB_ON_GRADE_TOP|FFL};
    build_up: FFL -> slab top (m) or None. Returns (value or None, missing facts list)."""
    basis = pit_depth.get("basis")
    v = pit_depth.get("value")
    if v is not None and basis not in (PRINTED, SUPPLIER):
        raise Refused("DEPTH_DEFAULTED", repr(basis))
    if v is not None and v <= 0:
        raise Refused("DEPTH_NOT_POSITIVE", repr(v))
    if wall_top_datum not in (WALL_TOP_SLAB, WALL_TOP_FFL):
        raise Refused("WALL_TOP_DATUM_NOT_DRAWN", repr(wall_top_datum))
    missing = []
    if v is None:
        missing.append("pit depth (lift supplier / designer)")
    datum = pit_depth.get("datum", wall_top_datum)
    if datum not in (WALL_TOP_SLAB, WALL_TOP_FFL):
        raise Refused("DEPTH_DATUM_UNKNOWN", repr(datum))
    if datum == wall_top_datum:
        return (v if not missing else None), missing
    # depth quoted to the FFL, wall top at the slab top (or the reverse): the build-up converts
    if build_up is None:
        missing.append("floor build-up F.F.L. -> slab-on-grade top")
    if missing:
        return None, missing
    h = v - build_up if datum == WALL_TOP_FFL else v + build_up
    if h <= 0:
        raise Refused("WALL_HEIGHT_NOT_POSITIVE", repr(h))
    return h, []


def _comp(cid, component, owner, unit, value, status, line=None, missing=(), low=None, high=None, source="", note=""):
    if status in (HELD, MISSING) and value is not None:
        raise Refused("HELD_WITH_VALUE", cid)
    if status in (HELD, MISSING) and not missing:
        raise Refused("HELD_WITHOUT_MISSING_FACT", cid)
    return {"id": cid, "component": component, "owner_trade": owner, "unit": unit, "value": _r(value),
            "status": status, "line_id": line, "missing": list(missing), "low": _r(low), "high": _r(high),
            "source": source, "note": note}


def build(spec):
    """spec (units in spec['unit']): ring_outer, shaft (inner), columns [rects], raft {rect, depth}, wall_top_datum,
    pit_depth {value, basis, datum}, build_up (m or None), storeys [{name, ffl, next_ffl, shaft: OPENING|CAP,
    ring_beams: [{mark, length, depth}] }], tie_rule {limit, level} or None, tie_section {b, d} or None,
    shaft_wall_trade, bind {component id: line id or None}. Returns the ledger."""
    s = scale(spec.get("unit"))
    outer, inner = rect(spec.get("ring_outer"), s), rect(spec.get("shaft"), s)
    cols = [rect(c, s) for c in spec.get("columns", [])]
    raft = spec.get("raft") or {}
    if not raft.get("rect"):
        raise Refused("NO_LIFT_BASE")
    rr = rect(raft["rect"], s)
    if not inside(outer, rr):
        raise Refused("RING_OUTSIDE_RAFT")
    g = ring_geometry(outer, inner, cols)
    h, miss = wall_height(None, spec.get("wall_top_datum"), spec.get("pit_depth") or {}, spec.get("build_up"))
    bind = spec.get("bind", {})
    used = {}

    def line(cid):
        lid = bind.get(cid)
        if lid is not None:
            if lid in used and used[lid] != cid:
                raise Refused("LINE_BOUND_TWICE", f"{lid}: {used[lid]} / {cid}")
            used[lid] = cid
        return lid

    comps = []
    raft_m3 = area(rr) * float(raft["depth"]) * s
    comps.append(_comp("RAFT", "lift base raft", "STRUCTURE", "m3", raft_m3, DC, line("RAFT"), note="footing line"))
    comps.append(_comp("PIT_FLOOR", "pit floor = raft top", "STRUCTURE", "m3", None, LISTED,
                       note="no volume of its own"))
    comps.append(_comp("PIT_WALL:PLAN", "pit wall ring net plan", "STRUCTURE", "m2", g["net_m2"], DC,
                       note=f"gross {g['gross_m2']:.6f} less columns {g['columns_in_band_m2']:.6f}"))
    wl = line("PIT_WALL")
    if h is None:
        status, value, missing = (HELD if wl else MISSING), None, list(miss) + ([] if wl else ["no candidate line"])
    elif wl:
        status, value, missing = DC, g["net_m2"] * h, []
    else:
        status, value, missing = MISSING, None, [f"no candidate line (value {g['net_m2'] * h:.6f} m3 ready)"]
    comps.append(_comp("PIT_WALL", "pit wall concrete", "STRUCTURE", "m3", value, status, wl, missing=missing,
                       note=f"{g['net_m2']:.6f} m2 x wall height"))
    comps.append(_comp("SHAFT_VOID:GROUND", "shaft void at ground level (not slab)", "NONE", "m2", area(inner), DC,
                       note="out of every slab line"))
    for c_i, c in enumerate(cols):
        comps.append(_comp(f"COLUMN:{c_i + 1}", "lift column / neck", "STRUCTURE", "m2", area(c), LISTED,
                           line(f"COLUMN:{c_i + 1}"), note="column lines; never in the ring"))
    tie = spec.get("tie_rule")
    for st in spec.get("storeys", []):
        name = st["name"]
        hgt = st["next_ffl"] - st["ffl"]
        if tie and hgt > tie["limit"] + TOL:
            tl = line(f"TIE_BEAM:{name}")
            sec = spec.get("tie_section")
            if sec:
                v = g["run_total_m"] * sec["b"] * sec["d"]
                comps.append(_comp(f"TIE_BEAM:{name}", f"lift tie beam at +{tie['level']:.2f} ({name})", "STRUCTURE",
                                   "m3", v if tl else None, DC if tl else MISSING, tl,
                                   missing=() if tl else [f"no candidate line (value {v:.6f} m3 ready)"]))
            else:
                comps.append(_comp(f"TIE_BEAM:{name}", f"lift tie beam at +{tie['level']:.2f} ({name})", "STRUCTURE",
                                   "m3", None, HELD if tl else MISSING, tl, missing=["tie-beam section (b x d)"],
                                   note=f"length {g['run_total_m']:.3f} m DRAWING-CONFIRMED"))
        for b_i, b in enumerate(st.get("ring_beams", [])):
            cid = f"RING_BEAM:{name}:{b['mark']}:{b_i + 1}"
            lid = line(cid)
            comps.append(_comp(cid, f"beam on the ring band ({name})", "STRUCTURE", "m", b["length"] if lid else None,
                               LISTED if lid else MISSING, lid, missing=() if lid else ["no beam line"],
                               note=f"beam line; never re-added; drawn length {b['length']:.3f} m"))
        sh = st.get("shaft")
        if sh not in ("OPENING", "CAP"):
            raise Refused("SHAFT_STATE_NOT_DRAWN", name)
        cid = f"SHAFT_SLAB:{name}"
        lid = line(cid)
        if sh == "CAP":
            comps.append(_comp(cid, f"slab over the shaft ({name}, top of shaft)", "STRUCTURE", "m2",
                               area(inner) if lid else None, LISTED if lid else MISSING, lid,
                               missing=() if lid else ["no roof slab line"], note=f"shaft plan {area(inner):.4f} m2"))
        else:
            if lid is not None:
                raise Refused("SHAFT_OPENING_BILLED_AS_SLAB", f"{name}: {lid}")
            comps.append(_comp(cid, f"shaft opening ({name})", "NONE", "m2", area(inner), DC,
                               note="out of the floor slab"))
    tw = spec.get("shaft_wall_trade")
    comps.append(_comp("SHAFT_WALLS", "shaft walls above the wall top", tw or "UNKNOWN", "-", None,
                       LISTED if tw else HELD, missing=() if tw else ["shaft wall material"]))
    ids = [c["id"] for c in comps]
    if len(ids) != len(set(ids)):
        raise Refused("COMPONENT_TWICE")
    return {"method": METHOD_ID, "ring": {k: (_r(v) if isinstance(v, float) else v) for k, v in g.items()},
            "wall_height_m": _r(h), "wall_missing": miss, "components": comps}


def claims_check(ring_outer, shaft, cols, claims, s=1.0):
    """R-T401-3 + R-T401-5 at ONE level band. claims: [{line, family, rect(s), valued: bool}] in the spec unit.
    Returns {'double': [...], 'gap_m2': {...}}; refuses the three named doubles."""
    outer, inner = rect(ring_outer, s), rect(shaft, s)
    cs = [rect(c, s) for c in cols]
    ring_net = area(outer) - area(inner) - sum(iarea(c, outer) for c in cs)
    rows = []
    for cl in claims:
        rs = [rect(r, s) for r in (cl["rects"] if "rects" in cl else [cl["rect"]])]
        rows.append((cl, rs))
    walls = [cl for cl, _ in rows if cl["family"] == "PIT_WALL"]
    for cl, rs in rows:
        on_shaft = sum(iarea(r, inner) for r in rs)
        on_cols = sum(iarea(r, c) for r in rs for c in cs)
        on_ring = sum(iarea(r, outer) for r in rs) - on_shaft - on_cols
        if cl["family"] == "SLAB" and on_shaft > TOL and cl.get("valued", True) and cl.get("level") == "GROUND":
            raise Refused("SHAFT_VOID_AS_SLAB", cl["line"])
        if cl["family"] == "SLAB" and on_ring > TOL and walls and cl.get("valued", True):
            raise Refused("PIT_WALL_IN_SLAB_AND_WALL", cl["line"])
        if cl["family"] == "PIT_WALL" and on_cols > TOL:
            raise Refused("COLUMN_IN_RING_AND_COLUMN", cl["line"])
    double = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, ra = rows[i]
            b, rb = rows[j]
            sh = sum(iarea(x, y) for x in ra for y in rb)
            if sh > TOL:
                kind = "DOUBLE" if a.get("valued", True) and b.get("valued", True) else "HELD_OVERLAP"
                double.append({"a": a["line"], "b": b["line"], "m2": _r(sh), "kind": kind})
    covered = sum(iarea(r, outer) - iarea(r, inner) for cl, rs in rows if cl["family"] == "PIT_WALL" for r in rs)
    return {"ring_net_m2": _r(ring_net), "pairs": double,
            "doubles": [d for d in double if d["kind"] == "DOUBLE"],
            "gap_ring_m2": _r(max(0.0, ring_net - covered))}
