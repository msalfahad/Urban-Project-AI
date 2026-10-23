"""LIFT_TANK_V1 (T-204, research, NOT wired into any method version): lift pit and roof water tank as structural elements.

A component ledger for two element kinds that the released route never carries (ELEMENT_CONTINUITY_V1, T-188: LIFT-01
and TANK-01 have no structural BOQ line in any state). It writes component ROWS with a measurement basis and a status;
a quantity is produced only when every dimension it needs is printed. A missing dimension makes the row HELD with the
missing item named; HELD never carries 0 (value None). Standard library only; imports no engine module. Any villa.

Physical element first (ENGINEERING_REASONING_STANDARD s.2 step 1, s.3 'one element, several geometries'):

  LIFT (no basement, pit on its own base): a reinforced-concrete pit ring of thickness t around the pit's inner
  rectangle, rising from the top of the pit base (a footing that is ALSO the pit floor) to the ground-floor datum; the
  lift columns stand inside the ring band. Each of these is its own geometry:
    concrete      net ring plan area x pit height; the column sections inside the ring band belong to the column /
                  neck lines, which are billed at full section through the pit height (R-CONC-OWN-1, T-189), so the
                  ring is measured NET of them (no column is re-added, no ring volume is counted twice);
    formwork      the wall runs of the inner and outer faces x pit height; the column faces on those faces stay with
                  the column formwork (face covered by a member = that member's own face; T-163 lesson);
    bar steel     per face and per wall run between column faces: '/m' count range C (exact n x L) .. A (ceil) .. B
                  (ceil + 1, open run); a run with no column on its face is a closed loop (A = B); the lengths need the
                  pit height and the anchorage (not printed in the typical detail) -> HELD, given per metre of height;
    waterproofing the membrane wraps the base soffit, the base sides (base depth + the printed screed), the base top
                  outside the pit envelope and the pit envelope's outer faces x pit height (the envelope = ring union
                  column sections, so a column that stands proud of the ring adds its returns);
    screed        the printed screed under the base, base plan area x screed thickness;
    tie beams     where a project note asks for beams tying the lift columns at a stated height when a storey is
                  taller than a stated threshold: the clear run between column faces on the wall centreline per storey
                  that meets the condition; the section only if printed.
  The pit base (footing), the lift columns / necks, the blinding and the backfill are listed with the line that already
  owns them, never re-added.

  TANK (on a roof slab): walls, base and cover, each only if drawn with its dimensions; a tank base that IS the roof
  slab belongs to the slab line. 'Tank place' text over slab panels, with no member drawn, gives HELD placeholders with
  the designer item named.

Geometry input: axis-aligned rectangles [x0, y0, x1, y1] in ONE plan frame (a rotated drawing is transformed into the
pit's own frame first; a mirror or a 90-degree turn leaves every result unchanged, tests). Units "mm" or "m".
"""

from __future__ import annotations

import math

METHOD = "LIFT_TANK_V1"
RULES = (
    "ENGINEERING_REASONING_STANDARD s.2 step 1 (element first), s.3 (one element, several geometries; physical vs "
    "procurement; a notation's meaning before its arithmetic), s.4 (rule + test)",
    "R-CONC-OWN-1 (T-189, proposed): the intersection belongs to the member billed through it at full section",
    "URBAN-REBAR-NET-AND-PROCUREMENT@v1: kg = count x length x d^2/162; never kg/m3",
    "T-191 r2 lesson: an open '/m' run carries A (ceil n x L) .. B (ceil n x L + 1); a closed loop A = B",
    "T-186 default guard / no-assumptions: a dimension not printed is HELD, never a default, never 0",
    "T-200 lesson: a finished level is never a concrete dimension (pit height is to the structural top of the base)",
)
UNITS = {"mm": 0.001, "m": 1.0}
NDP = 6


def _need(cond, msg):
    if not cond:
        raise ValueError(msg)


def _r(x):
    return None if x is None else round(x + 0.0, NDP)


def kg_per_m(d_mm):
    """URBAN-REBAR-NET-AND-PROCUREMENT@v1 unit mass (d^2 / 162 kg/m, d in mm)."""
    _need(d_mm > 0, "bar diameter must be > 0")
    return d_mm * d_mm / 162.0


# ---------------------------------------------------------------- rectangle helpers (axis-aligned, metres)
def _rect(r, k, what):
    _need(isinstance(r, (list, tuple)) and len(r) == 4, f"{what}: rectangle [x0, y0, x1, y1] required")
    x0, y0, x1, y1 = (float(v) * k for v in r)
    _need(x1 > x0 and y1 > y0, f"{what}: x1 > x0 and y1 > y0 required")
    return (x0, y0, x1, y1)


def _area(r):
    return (r[2] - r[0]) * (r[3] - r[1])


def _inter(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    return (x0, y0, x1, y1) if x1 > x0 and y1 > y0 else None


def _iarea(a, b):
    i = _inter(a, b)
    return _area(i) if i else 0.0


def _union_area_perimeter(rects):
    """Area and outline length of a union of axis-aligned rectangles (coordinate compression, exact)."""
    xs = sorted({v for r in rects for v in (r[0], r[2])})
    ys = sorted({v for r in rects for v in (r[1], r[3])})
    filled = [[any(r[0] <= xs[i] and xs[i + 1] <= r[2] and r[1] <= ys[j] and ys[j + 1] <= r[3] for r in rects)
               for j in range(len(ys) - 1)] for i in range(len(xs) - 1)]
    area = per = 0.0
    nx, ny = len(xs) - 1, len(ys) - 1
    for i in range(nx):
        for j in range(ny):
            if not filled[i][j]:
                continue
            w, h = xs[i + 1] - xs[i], ys[j + 1] - ys[j]
            area += w * h
            if i == 0 or not filled[i - 1][j]:
                per += h
            if i == nx - 1 or not filled[i + 1][j]:
                per += h
            if j == 0 or not filled[i][j - 1]:
                per += w
            if j == ny - 1 or not filled[i][j + 1]:
                per += w
    return area, per


def _subtract(interval, cuts):
    """Parts of [a, b] not covered by the cut intervals."""
    a, b = interval
    parts = [(a, b)]
    for c0, c1 in sorted(cuts):
        nxt = []
        for p0, p1 in parts:
            if c1 <= p0 or c0 >= p1:
                nxt.append((p0, p1))
                continue
            if c0 > p0:
                nxt.append((p0, c0))
            if c1 < p1:
                nxt.append((c1, p1))
        parts = nxt
    return [p for p in parts if p[1] - p[0] > 1e-9]


def _face_runs(box, cols):
    """Wall runs on the four faces of `box` not covered by a column standing on that face line.

    A column covers a face where its section touches or straddles the face line (flush with it or proud of it); the
    covered part of the face is the column's own face (its formwork and membrane belong to the column)."""
    x0, y0, x1, y1 = box
    runs = {}
    eps = 1e-9
    for side in ("W", "E", "S", "N"):
        if side in ("W", "E"):
            fx = x0 if side == "W" else x1
            cuts = []
            for c in cols:
                # the column section touches or straddles the face line: that part of the face is the column's
                if c[0] <= fx + eps and c[2] >= fx - eps:
                    cuts.append((max(c[1], y0), min(c[3], y1)))
            runs[side] = _subtract((y0, y1), [ct for ct in cuts if ct[1] > ct[0]])
        else:
            fy = y0 if side == "S" else y1
            cuts = []
            for c in cols:
                if c[1] <= fy + eps and c[3] >= fy - eps:
                    cuts.append((max(c[0], x0), min(c[2], x1)))
            runs[side] = _subtract((x0, x1), [ct for ct in cuts if ct[1] > ct[0]])
    return runs


def _bar_counts(runs, n_per_m, closed_if_uncut):
    """Count range of one bar family on one face: C exact, A ceil per run, B ceil + 1 per OPEN run."""
    lengths = [p1 - p0 for side in ("W", "E", "S", "N") for p0, p1 in runs[side]]
    full = sum(lengths)
    if closed_if_uncut:
        c = n_per_m * full
        a = math.ceil(round(c, 9))
        return {"C": _r(c), "A": a, "B": a, "runs": len(lengths), "closed_loop": True}
    c = sum(n_per_m * L for L in lengths)
    a = sum(math.ceil(round(n_per_m * L, 9)) for L in lengths)
    b = sum(math.ceil(round(n_per_m * L, 9)) + 1 for L in lengths)
    return {"C": _r(c), "A": a, "B": b, "runs": len(lengths), "closed_loop": False}


# ---------------------------------------------------------------- lift
def lift_pit(spec):
    """Component rows of one lift pit. See the module docstring for the physical model.

    spec = {"id", "unit": "mm" | "m",
            "pit_inner": rect (inner faces of the pit walls), "pit_inner_ref",
            "wall_t": thickness, "wall_ref",
            "columns": [{"id", "rect", "ref"}]  (lift column sections at the pit level; their line owns them),
            "base": {"id", "L", "B", "D", "ref", "owner_line"} or None  (the pit base = a footing; its line owns it),
            "pit_height": number | None, "pit_height_ref": str  (top of the base to the structural top of the ring;
                                                                never a finished level),
            "detail": {"ref", "state": "PROJECT" | "TYPICAL",
                       "vertical": {"n_per_m", "d", "faces"} | None, "horizontal": {"n_per_m", "d", "faces"} | None,
                       "membrane": bool, "protection_board": bool, "screed_t": number | None,
                       "blinding_t": number | None} | None,
            "tie_beams": {"rule_ref", "threshold", "at", "section": [b, h] | None, "section_ref",
                          "storeys": [{"storey", "height", "ref"}]} | None}
    """
    _need(spec.get("unit") in UNITS, "unit must be 'mm' or 'm'")
    k = UNITS[spec["unit"]]
    eid = spec.get("id")
    _need(bool(eid), "id required")
    inner = _rect(spec.get("pit_inner"), k, "pit_inner")
    _need(bool(spec.get("pit_inner_ref")), "pit_inner_ref required")
    t = spec.get("wall_t")
    _need(isinstance(t, (int, float)) and t > 0, "wall_t > 0 required (a pit ring with no printed thickness is "
                                                 "not measured here)")
    _need(bool(spec.get("wall_ref")), "wall_ref required")
    t = t * k
    outer = (inner[0] - t, inner[1] - t, inner[2] + t, inner[3] + t)
    cols = []
    seen = set()
    for c in spec.get("columns", []):
        _need(c.get("id") and c["id"] not in seen, "column id required and unique")
        _need(bool(c.get("ref")), f"column {c.get('id')}: ref required")
        seen.add(c["id"])
        cols.append((c["id"], _rect(c.get("rect"), k, f"column {c['id']}"), c["ref"]))
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            _need(_iarea(cols[i][1], cols[j][1]) < 1e-12, f"columns {cols[i][0]} / {cols[j][0]} overlap")
    h = spec.get("pit_height")
    if h is not None:
        _need(isinstance(h, (int, float)) and h > 0, "pit_height must be > 0 or None (HELD)")
        _need(bool(spec.get("pit_height_ref")), "pit_height_ref required with a pit height")
        h = h * k

    base = spec.get("base")
    if base:
        _need(all(base.get(x) for x in ("id", "L", "B", "D", "ref", "owner_line")), "base: id, L, B, D, ref, "
                                                                                    "owner_line required")
        bl, bb = base["L"] * k, base["B"] * k
        ow, oh = outer[2] - outer[0], outer[3] - outer[1]
        _need((bl >= ow - 1e-9 and bb >= oh - 1e-9) or (bb >= ow - 1e-9 and bl >= oh - 1e-9),
              "the pit base is smaller than the pit ring")

    rows, findings = [], []

    def row(comp, owner, basis, unit, value, status, ref, missing=None, extra=None):
        _need(status in ("HELD", "LISTED", "DRAWING-CONFIRMED"), f"status {status}")
        _need(status == "DRAWING-CONFIRMED" or value is None, "a HELD / LISTED row carries no value (never 0)")
        _need(status != "DRAWING-CONFIRMED" or value is not None, "a measured row needs its value")
        r = {"element": eid, "component": comp, "owner_line": owner, "basis": basis, "unit": unit,
             "value": _r(value), "status": status, "ref": ref, "missing": missing}
        if extra:
            r.update(extra)
        rows.append(r)

    gross = _area(outer) - _area(inner)
    col_in_ring = {}
    for cid, cr, _ref in cols:
        in_outer = _iarea(cr, outer)
        in_inner = _iarea(cr, inner)
        if in_inner > 1e-12:
            findings.append({"code": "COLUMN_INTO_PIT", "status": "REVIEW", "column": cid,
                             "why": f"{_r(in_inner)} m2 of the column section stands inside the pit clear space"})
        if in_outer - in_inner <= 1e-12:
            findings.append({"code": "COLUMN_OFF_RING", "status": "REVIEW", "column": cid,
                             "why": "column section does not touch the pit ring band"})
        col_in_ring[cid] = in_outer - in_inner
    net = gross - sum(col_in_ring.values())
    _need(net > 0, "columns cover the whole ring")
    hmiss = "pit height: top of the pit base to the structural top of the ring (not printed)"
    href = spec.get("pit_height_ref") or "not printed"
    env_area, env_per = _union_area_perimeter([outer] + [cr for _c, cr, _r2 in cols])

    # concrete
    row("PIT_RING_PLAN_GROSS", "(basis)", f"outer {_r(outer[2]-outer[0])} x {_r(outer[3]-outer[1])} - inner "
        f"{_r(inner[2]-inner[0])} x {_r(inner[3]-inner[1])} (= centreline {_r(gross / t)} m x t {_r(t)})", "m2", gross,
        "DRAWING-CONFIRMED", spec["wall_ref"])
    for cid, a in col_in_ring.items():
        row(f"COLUMN_SECTION_IN_RING:{cid}", "column / neck line (R-CONC-OWN-1: billed at full section)",
            "column section inside the ring band", "m2", a, "DRAWING-CONFIRMED",
            dict((c[0], c[2]) for c in cols)[cid])
    row("PIT_RING_PLAN_NET", "CONC.LIFT_PIT_WALL", "gross ring - column sections in the ring", "m2", net,
        "DRAWING-CONFIRMED", spec["wall_ref"], extra={"net_centreline_m": _r(net / t)})
    if h is None:
        row("PIT_WALL_CONCRETE", "CONC.LIFT_PIT_WALL (new)", f"net ring {_r(net)} m2 x pit height", "m3", None, "HELD",
            href, hmiss)
    else:
        row("PIT_WALL_CONCRETE", "CONC.LIFT_PIT_WALL (new)", f"net ring {_r(net)} m2 x pit height {_r(h)}", "m3",
            net * h, "DRAWING-CONFIRMED", href)

    # formwork
    inner_runs = _face_runs(inner, [cr for _c, cr, _r2 in cols])
    outer_runs = _face_runs(outer, [cr for _c, cr, _r2 in cols])
    lin = sum(p1 - p0 for s in inner_runs.values() for p0, p1 in s)
    lout = sum(p1 - p0 for s in outer_runs.values() for p0, p1 in s)
    row("PIT_WALL_FACE_RUN_INNER", "(basis)", "inner face, column faces excluded", "m", lin, "DRAWING-CONFIRMED",
        spec["wall_ref"])
    row("PIT_WALL_FACE_RUN_OUTER", "(basis)", "outer face, column faces excluded", "m", lout, "DRAWING-CONFIRMED",
        spec["wall_ref"])
    if h is None:
        row("PIT_WALL_FORMWORK", "FORMWORK.LIFT_PIT_WALL (new)", f"({_r(lin)} + {_r(lout)}) m x pit height", "m2",
            None, "HELD", href, hmiss)
    else:
        row("PIT_WALL_FORMWORK", "FORMWORK.LIFT_PIT_WALL (new)", f"({_r(lin)} + {_r(lout)}) m x {_r(h)}", "m2",
            (lin + lout) * h, "DRAWING-CONFIRMED", href)

    det = spec.get("detail")
    # bar steel (never released here: lengths need the height AND the anchorage, which a typical detail leaves open)
    if det:
        _need(det.get("state") in ("PROJECT", "TYPICAL") and det.get("ref"), "detail: state and ref required")
        if det["state"] == "TYPICAL":
            findings.append({"code": "TYPICAL_DETAIL", "status": "REVIEW", "column": None,
                             "why": f"pit geometry from a typical detail ({det['ref']}): arrangement and bars, the "
                                    "'as per' dimensions stay open"})
        for fam in ("vertical", "horizontal"):
            f = det.get(fam)
            if not f:
                row(f"BARS_{fam.upper()}", "BAR_STEEL.LIFT_PIT_WALL (new)", "family not printed", "kg", None, "HELD",
                    det["ref"], f"{fam} bars not printed")
                continue
            _need(f.get("n_per_m", 0) > 0 and f.get("d", 0) > 0 and f.get("faces") in (1, 2),
                  f"{fam}: n_per_m, d, faces (1 or 2) required")
            kgm = kg_per_m(f["d"])
            if fam == "vertical":
                closed = not cols
                cin = _bar_counts(inner_runs, f["n_per_m"], closed)
                cout = _bar_counts(outer_runs, f["n_per_m"], closed)
                faces = [cin, cout] if f["faces"] == 2 else [cin]
                per_m = {e: _r(sum(c[e] for c in faces) * kgm) for e in ("C", "A", "B")}
                row("BARS_VERTICAL", "BAR_STEEL.LIFT_PIT_WALL (new)",
                    f"{f['n_per_m']} d{f['d']}/m per face; counts C {_r(sum(c['C'] for c in faces))} / A "
                    f"{sum(c['A'] for c in faces)} / B {sum(c['B'] for c in faces)} bars; kg per metre of pit height "
                    f"C {per_m['C']} / A {per_m['A']} / B {per_m['B']}", "kg", None, "HELD", det["ref"],
                    "bar length = pit height + embedment in the base + top anchorage (height and anchorage not "
                    "printed)", extra={"count_inner": cin, "count_outer": cout if f["faces"] == 2 else None,
                                       "kg_per_m_of_height": per_m, "kg_per_m": _r(kgm)})
            else:
                run = (lin + lout) if f["faces"] == 2 else lin
                per_m_h = f["n_per_m"] * run * kgm
                row("BARS_HORIZONTAL", "BAR_STEEL.LIFT_PIT_WALL (new)",
                    f"{f['n_per_m']} d{f['d']}/m of height on {f['faces']} face(s); wall run {_r(run)} m between "
                    f"column faces -> {_r(per_m_h)} kg per metre of height before anchorage into the columns", "kg",
                    None, "HELD", det["ref"], "pit height and the anchorage into the columns (not printed)",
                    extra={"kg_per_m_of_height": _r(per_m_h), "kg_per_m": _r(kgm)})
        for xb in det.get("extra_bars", []):
            _need(xb.get("label") and xb.get("count", 0) > 0 and xb.get("d", 0) > 0 and xb.get("run") in
                  ("GROSS_CENTRELINE", "NET_CENTRELINE"), "extra_bars: label, count, d, run required")
            run = gross / t if xb["run"] == "GROSS_CENTRELINE" else net / t
            kgm = kg_per_m(xb["d"])
            row(f"BARS_EXTRA:{xb['label']}", "BAR_STEEL.LIFT_PIT_WALL (new)",
                f"{xb['count']} d{xb['d']} along the {xb['run'].lower().replace('_', ' ')} {_r(run)} m = "
                f"{_r(xb['count'] * run)} m, {_r(xb['count'] * run * kgm)} kg before laps / corner anchorage", "kg",
                None, "HELD", det["ref"], "laps and corner anchorage not printed (typical detail)",
                extra={"run_m": _r(xb["count"] * run), "kg_before_laps": _r(xb["count"] * run * kgm)})
        # waterproofing / protection / screed from the detail's layers
        if det.get("membrane") or det.get("protection_board"):
            base = spec.get("base")
            _need(base is not None, "a membrane round the pit base needs the base")
            L, B, D = (base[x] * k for x in ("L", "B", "D"))
            st = (det.get("screed_t") or 0.0) * k
            soffit = L * B
            sides = 2 * (L + B) * (D + st)
            top_out = L * B - env_area
            _need(top_out >= 0, "pit envelope larger than its base")
            fixed = {"BASE_SOFFIT": soffit, "BASE_SIDES": sides, "BASE_TOP_OUTSIDE_PIT": top_out}
            if det.get("membrane"):
                for nm, v in fixed.items():
                    row(f"MEMBRANE_{nm}", "WP.LIFT_PIT (new, lane A owner method)",
                        {"BASE_SOFFIT": f"{_r(L)} x {_r(B)}",
                         "BASE_SIDES": f"2 x ({_r(L)} + {_r(B)}) x (base {_r(D)} + screed {_r(st)})",
                         "BASE_TOP_OUTSIDE_PIT": f"{_r(L)} x {_r(B)} - pit envelope {_r(env_area)}"}[nm], "m2", v,
                        "DRAWING-CONFIRMED", det["ref"] + " + " + base["ref"])
                if h is None:
                    row("MEMBRANE_PIT_OUTER_FACES", "WP.LIFT_PIT (new)", f"pit envelope outline {_r(env_per)} m x pit "
                        "height", "m2", None, "HELD", href, hmiss)
                else:
                    row("MEMBRANE_PIT_OUTER_FACES", "WP.LIFT_PIT (new)", f"{_r(env_per)} m x {_r(h)}", "m2",
                        env_per * h, "DRAWING-CONFIRMED", href)
            if det.get("protection_board"):
                row("PROTECTION_BOARD_BASE", "WP.LIFT_PIT (new)", "base sides + base top outside the pit", "m2",
                    sides + top_out, "DRAWING-CONFIRMED", det["ref"] + " + " + base["ref"])
                row("PROTECTION_BOARD_WALLS", "WP.LIFT_PIT (new)", f"pit envelope outline {_r(env_per)} m x pit "
                    "height", "m2", None if h is None else env_per * h, "HELD" if h is None else "DRAWING-CONFIRMED",
                    href, hmiss if h is None else None)
            if det.get("screed_t"):
                row("SCREED_UNDER_BASE", "WP.LIFT_PIT (new) / screed", f"{_r(L)} x {_r(B)} x {_r(st)}", "m3",
                    L * B * st, "DRAWING-CONFIRMED", det["ref"] + " + " + base["ref"])
        if det.get("blinding_t"):
            row("BLINDING_UNDER_BASE", "existing blinding line (list, never re-add)",
                f"plain concrete {_r(det['blinding_t'] * k)} under the base", "m3", None, "LISTED", det["ref"])

    if base:
        row("PIT_BASE", f"{base['owner_line']} (list, never re-add)",
            f"{base['id']} {_r(base['L']*k)} x {_r(base['B']*k)} x {_r(base['D']*k)} (pit floor = top of the base)",
            "m3", base["L"] * base["B"] * base["D"] * k ** 3, "DRAWING-CONFIRMED", base["ref"],
            extra={"listed_only": True})
    else:
        findings.append({"code": "PIT_BASE_NOT_DRAWN", "status": "HELD", "column": None,
                         "why": "no base under the pit: pit floor slab and base HELD"})
        row("PIT_BASE", "CONC.LIFT_PIT_BASE (new)", "not drawn", "m3", None, "HELD", spec["pit_inner_ref"],
            "pit base / floor not drawn")

    tb = spec.get("tie_beams")
    if tb:
        _need(tb.get("rule_ref") and isinstance(tb.get("threshold"), (int, float)) and isinstance(tb.get("at"),
              (int, float)), "tie_beams: rule_ref, threshold, at required")
        for s in tb.get("storeys", []):
            _need(s.get("storey") and isinstance(s.get("height"), (int, float)) and s.get("ref"),
                  "tie_beams storey: storey, height, ref required")
            applies = s["height"] * k > tb["threshold"] * k + 1e-9
            if not applies:
                rows.append({"element": eid, "component": f"TIE_BEAMS:{s['storey']}", "owner_line": "(rule not met)",
                             "basis": f"storey height {_r(s['height']*k)} <= threshold {_r(tb['threshold']*k)}",
                             "unit": "m", "value": None, "status": "NOT_REQUIRED", "ref": s["ref"], "missing": None,
                             "applies": False})
                continue
            sec = tb.get("section")
            length = net / t
            row(f"TIE_BEAMS_LENGTH:{s['storey']}", "(basis)", "clear runs between column faces on the wall "
                "centreline", "m", length, "DRAWING-CONFIRMED", s["ref"] + "; " + tb["rule_ref"],
                extra={"applies": True, "at": _r(tb["at"] * k)})
            if sec:
                _need(len(sec) == 2 and min(sec) > 0 and tb.get("section_ref"), "tie beam section [b, h] + ref")
                row(f"TIE_BEAMS_CONCRETE:{s['storey']}", "CONC.LIFT_TIE_BEAM (new)",
                    f"{_r(length)} m x {_r(sec[0]*k)} x {_r(sec[1]*k)}", "m3", length * sec[0] * sec[1] * k * k,
                    "DRAWING-CONFIRMED", tb["section_ref"])
            else:
                row(f"TIE_BEAMS_CONCRETE:{s['storey']}", "CONC.LIFT_TIE_BEAM (new)",
                    f"{_r(length)} m x section", "m3", None, "HELD", tb["rule_ref"], "tie-beam section not printed")
    return {"method": METHOD, "element": eid, "rows": rows, "findings": findings,
            "summary": {"ring_gross_m2": _r(gross), "ring_net_m2": _r(net), "column_in_ring_m2":
                        _r(sum(col_in_ring.values())), "net_centreline_m": _r(net / t), "face_run_inner_m": _r(lin),
                        "face_run_outer_m": _r(lout), "envelope_m2": _r(env_area), "envelope_outline_m": _r(env_per),
                        "held": sum(1 for r in rows if r["status"] == "HELD"),
                        "measured": sum(1 for r in rows if r["status"] == "DRAWING-CONFIRMED")}}


# ---------------------------------------------------------------- tank
def tank(spec):
    """Component rows of one roof water tank.

    spec = {"id", "unit", "place_ref", "searched": str (sheets searched; required),
            "supporting_slab_lines": [line ids] (the slab panels under the tank: listed, never re-added),
            "walls": {"inner": rect, "t", "height", "ref"} | None,
            "base": "ROOF_SLAB" | {"area", "t", "ref"} | None,
            "cover": {"area", "t", "openings": [area, ...], "ref"} | None,
            "designer_item": str (required when anything is missing)}
    """
    _need(spec.get("unit") in UNITS, "unit must be 'mm' or 'm'")
    k = UNITS[spec["unit"]]
    eid = spec.get("id")
    _need(bool(eid) and bool(spec.get("place_ref")), "id and place_ref required")
    _need(bool(spec.get("searched")), "searched required: an absence needs the sheets searched")
    rows = []

    def row(comp, owner, basis, unit, value, status, ref, missing=None):
        rows.append({"element": eid, "component": comp, "owner_line": owner, "basis": basis, "unit": unit,
                     "value": _r(value), "status": status, "ref": ref, "missing": missing})

    for ln in spec.get("supporting_slab_lines", []):
        row("SUPPORTING_SLAB", f"{ln} (slab line: list, never re-add)", "roof slab panel under the tank place", "m3",
            None, "LISTED", spec["place_ref"])
    missing = []
    w = spec.get("walls")
    if w:
        inner = _rect(w.get("inner"), k, "tank walls inner")
        _need(w.get("t", 0) > 0 and w.get("height", 0) > 0 and w.get("ref"), "tank walls: t, height, ref required")
        t, hh = w["t"] * k, w["height"] * k
        ring = (inner[2] - inner[0] + 2 * t) * (inner[3] - inner[1] + 2 * t) - _area(inner)
        row("TANK_WALLS", "CONC.ROOF_TANK (new)", f"ring {_r(ring)} m2 x {_r(hh)}", "m3", ring * hh,
            "DRAWING-CONFIRMED", w["ref"])
    else:
        missing.append("walls")
        row("TANK_WALLS", "CONC.ROOF_TANK (new)", "not drawn", "m3", None, "HELD", spec["searched"],
            "tank walls not drawn (type, footprint, height)")
    b = spec.get("base")
    if b == "ROOF_SLAB":
        row("TANK_BASE", "roof slab line (list, never re-add)", "the roof slab carries the tank directly", "m3", None,
            "LISTED", spec["place_ref"])
    elif b:
        _need(b.get("area", 0) > 0 and b.get("t", 0) > 0 and b.get("ref"), "tank base: area, t, ref required")
        row("TANK_BASE", "CONC.ROOF_TANK (new)", f"{_r(b['area']*k*k)} x {_r(b['t']*k)}", "m3",
            b["area"] * b["t"] * k ** 3, "DRAWING-CONFIRMED", b["ref"])
    else:
        missing.append("base")
        row("TANK_BASE", "CONC.ROOF_TANK (new)", "not drawn", "m3", None, "HELD", spec["searched"],
            "tank base / plinth not drawn (or a statement that the slab carries the tank)")
    c = spec.get("cover")
    if c:
        _need(c.get("area", 0) > 0 and c.get("t", 0) > 0 and c.get("ref"), "tank cover: area, t, ref required")
        opn = sum(c.get("openings", []))
        _need(opn < c["area"], "cover openings exceed the cover")
        row("TANK_COVER", "CONC.ROOF_TANK (new)", f"({_r(c['area']*k*k)} - openings {_r(opn*k*k)}) x {_r(c['t']*k)}",
            "m3", (c["area"] - opn) * c["t"] * k ** 3, "DRAWING-CONFIRMED", c["ref"])
    else:
        missing.append("cover")
        row("TANK_COVER", "CONC.ROOF_TANK (new)", "not drawn", "m3", None, "HELD", spec["searched"],
            "tank cover not drawn (cast cover slab or a prefabricated tank)")
    if missing:
        _need(bool(spec.get("designer_item")), "designer_item required when a tank component is not drawn")
    return {"method": METHOD, "element": eid, "rows": rows, "missing": missing,
            "designer_item": spec.get("designer_item") if missing else None,
            "summary": {"held": sum(1 for r in rows if r["status"] == "HELD"),
                        "measured": sum(1 for r in rows if r["status"] == "DRAWING-CONFIRMED"),
                        "listed": sum(1 for r in rows if r["status"] == "LISTED")}}
