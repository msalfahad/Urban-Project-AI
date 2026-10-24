"""T-258 STAIR_DOME_LINE_V1: whole-line closure ledger for stair + dome concrete (pure rules, stdlib only; any villa).

A research module (not wired into any method): it takes one record per physical component of every staircase and every
dome, recomputes each value from its printed primitives with the owner formulas, checks that every component is counted
once and in the right line, and splits the line into

    CLOSABLE        value established from the drawings (VERIFIED / DRAWING-CONFIRMED / ASSUMED — OWNER-APPROVED)
    CONFLICT        two or more drawing readings of one component: carried as [min, max] of ITS readings, never one end
    HELD            a named blocker; a bound only when the drawings give one; never 0
    UNKNOWN         scope or quantity cannot be established (no value)
    OWNED_ELSEWHERE the physical part is billed by another line (beam, slab, column, ground slab): listed, never summed
    BESIDE          drawing-derived concrete the owner method does not carry (knees): shown side by side, never summed

Owner formulas (cited, not re-decided here): steps n x 1/2 r g w (Q-19); waist w x t x hypot(goings g, goings r) between
the first and the last riser line (Q-47 A); landing L x W x t less drawn deductions; the arrival / head wedge 1/2 r g w
inside a landing or plate deducted once (Q-62 A cond); a head or foot inside a full-depth member billed through the
junction is owned by that member (R-CONC-OWN-1 / -1a, T-189 / T-192); a landing at a floor level inside a floor-slab
panel is slab (R-STAIR-LAND-1, T-184). Dome shell: the exact solid between concentric spheres from the printed chord,
rise and thickness (T-185); a dome without a structural detail is HELD.

Units: every length input carries a unit ('m', 'cm', 'mm'); anything else is refused.

r2 (T-258, Verifier 2026-10-24 12:58 / 13:10): check_arrivals (R-STAIR-ARRIVAL-1: every flight's arrival wedge has
exactly one treatment) and resolve_lane_width (R-STAIR-LANE-1: a width is the structural lane, never an architectural
dimension reaching past the slab edge). Both proposed rules; nothing here is wired into a method.
"""

from __future__ import annotations

import math

SCHEMA = "STAIR_DOME_LINE_V1"
UNITS = {"m": 1.0, "cm": 0.01, "mm": 0.001}
EVIDENCE = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN")
CLOSABLE_EVIDENCE = EVIDENCE[:3]
CLASSES = ("CLOSABLE", "CONFLICT", "HELD", "UNKNOWN", "OWNED_ELSEWHERE", "BESIDE")
THIS_LINE = ("STAIR", "DOME")
TOL = 1e-6


class LedgerError(ValueError):
    """A component record that would make the line wrong (double count, silent 0, collapsed conflict, ...)."""


def to_m(value, unit):
    if unit not in UNITS:
        raise LedgerError(f"unit {unit!r} not one of {sorted(UNITS)}")
    return float(value) * UNITS[unit]


# ---------------------------------------------------------------- owner formulas (each one cited in the docstring)

def slope_factor(r, g):
    """1 / cos of the flight pitch: sloped length per plan length."""
    return math.hypot(g, r) / g


def steps_m3(n, r, g, w):
    """Q-19: n step triangles 1/2 r g w."""
    return n * 0.5 * r * g * w


def waist_m3(goings, r, g, w, t):
    """Q-47 A: waist between the first and the last riser line: w t hypot(goings g, goings r)."""
    return w * t * math.hypot(goings * g, goings * r)


def wedge_m3(r, g, w):
    """Q-62 A cond: one step triangle inside a landing or plate, deducted once."""
    return 0.5 * r * g * w


def wedge_in_plate_m3(r, g, w, t_plate=None):
    """Q-62 A cond as applied by T-111 / T-184: the part of the arrival step triangle inside the landing or plate it
    arrives into. A full-depth member (t_plate None) takes the whole triangle; a plate thinner than the riser leaves the
    sliver below its soffit, ((r - t) / r)^2 of the triangle, in the flight."""
    full = wedge_m3(r, g, w)
    if t_plate is None or t_plate >= r:
        return full
    return full * (1.0 - ((r - t_plate) / r) ** 2)


def head_in_member_m3(a, r, g, w, t):
    """R-CONC-OWN-1 (T-189): a flight HEAD whose last riser line lies a (< g) inside a full-depth member billed through:
    the part of the top tread triangle inside it ((a/g)^2 of a step triangle) + the waist over a. The last step triangle
    itself is the Q-62 wedge, deducted separately."""
    if not 0 <= a < g:
        raise LedgerError(f"head overlap a = {a} must lie in [0, g)")
    d = t * slope_factor(r, g)
    return (a / g) ** 2 * wedge_m3(r, g, w) + a * d * w


def foot_in_member_m3(a, r, g, w, t):
    """R-CONC-OWN-1a (T-192): a flight FOOT whose first riser line lies a inside a full-depth member at the floor it
    starts from: only the waist below the floor, (d a - k a^2 / 2) w; never the steps."""
    k = r / g
    d = t * slope_factor(r, g)
    if a < 0 or k * a > d:
        raise LedgerError(f"foot overlap a = {a} outside the waist below the floor")
    return (d * a - k * a * a / 2.0) * w


def flight_m3(n_steps, r, g, goings, w, t, wedges=(), head_a=None, foot_a=None):
    """One flight, owner method, net of its Q-62 wedges and of the parts other members own. `wedges` lists, per
    arrival wedge, the thickness of the plate it arrives into (None = a full-depth member). Returns the parts."""
    if t is None:
        raise LedgerError("waist thickness not printed: the flight is HELD, never computed with 0")
    st = steps_m3(n_steps, r, g, w)
    wa = waist_m3(goings, r, g, w, t)
    we = sum(wedge_in_plate_m3(r, g, w, tp) for tp in wedges)
    hd = head_in_member_m3(head_a, r, g, w, t) if head_a is not None else 0.0
    ft = foot_in_member_m3(foot_a, r, g, w, t) if foot_a is not None else 0.0
    return dict(steps=st, waist=wa, wedges=we, head_owned_elsewhere=hd, foot_owned_elsewhere=ft,
                net=st + wa - we - hd - ft)


def landing_m3(length, width, t, deduct_m2=0.0):
    return (length * width - deduct_m2) * t


def shell_m3(chord, rise, t):
    """T-185: spherical cap shell, outer chord / rise printed, thickness t: solid between concentric spheres."""
    if t is None or rise is None or chord is None:
        raise LedgerError("dome shell needs the printed chord, rise and thickness")
    a = chord / 2.0
    r_o = (a * a + rise * rise) / (2.0 * rise)
    r_i, h_i = r_o - t, rise - t
    return math.pi / 3.0 * (rise ** 2 * (3 * r_o - rise) - h_i ** 2 * (3 * r_i - h_i))


# ---------------------------------------------------------------- one component record

def component(cid, element, part, cls, evidence, owner_line, value=None, readings=None, bound=None, region=None,
              source="", blocker="", geometry_drawn=True, floor_level_landing=False, note="", is_flight=False,
              arrival=None):
    """Build and check one record. `region` names the physical piece (two records with one region = a double count).
    `is_flight` marks a flight or a run of steps; its `arrival` (see arrival()) states the one treatment of the step
    triangle beyond its top riser line (R-STAIR-ARRIVAL-1, checked by check_arrivals)."""
    if cls not in CLASSES:
        raise LedgerError(f"{cid}: class {cls!r}")
    if evidence not in EVIDENCE:
        raise LedgerError(f"{cid}: evidence {evidence!r}")
    rec = dict(id=cid, element=element, part=part, cls=cls, evidence=evidence, owner_line=owner_line,
               value=value, readings=readings, bound=bound, region=region or cid, source=source, blocker=blocker,
               geometry_drawn=geometry_drawn, floor_level_landing=floor_level_landing, note=note,
               is_flight=is_flight, arrival=arrival)
    check_component(rec)
    return rec


def check_component(c):
    cid, cls = c["id"], c["cls"]
    if cls == "CLOSABLE":
        if c["evidence"] not in CLOSABLE_EVIDENCE:
            raise LedgerError(f"{cid}: CLOSABLE needs evidence in {CLOSABLE_EVIDENCE}, got {c['evidence']}")
        if c["value"] is None or c["value"] <= 0:
            raise LedgerError(f"{cid}: a closable component needs a positive value")
        if not c["source"]:
            raise LedgerError(f"{cid}: a closable component names its drawing source")
        if not c["geometry_drawn"]:
            raise LedgerError(f"{cid}: released without drawn geometry (a winder / curved part with no drawn soffit "
                              "is HELD)")
        if c["owner_line"] not in THIS_LINE:
            raise LedgerError(f"{cid}: closable in the stair / dome line but owned by {c['owner_line']}")
    if cls == "CONFLICT":
        rd = c["readings"] or {}
        if len(rd) < 2 or any(v is None for v in rd.values()):
            raise LedgerError(f"{cid}: a CONFLICT carries two or more valued readings")
        lo, hi = min(rd.values()), max(rd.values())
        if c["bound"] is None or abs(c["bound"][0] - lo) > TOL or abs(c["bound"][1] - hi) > TOL:
            raise LedgerError(f"{cid}: CONFLICT range must be exactly [min, max] of its readings {lo:.6f} .. {hi:.6f}")
        if c["value"] is not None:
            raise LedgerError(f"{cid}: a CONFLICT is never collapsed to one value")
        if c["evidence"] != "HELD":
            raise LedgerError(f"{cid}: a CONFLICT is HELD")
        if not c["blocker"]:
            raise LedgerError(f"{cid}: a CONFLICT names the item that settles it")
    if cls in ("HELD", "UNKNOWN"):
        if c["value"] is not None:
            raise LedgerError(f"{cid}: a {cls} component carries no released value (a held part is never a number, "
                              "never 0)")
        b = c["bound"]
        if b is not None and (b[1] is not None and b[1] <= 0):
            raise LedgerError(f"{cid}: a held bound of 0 is a silent 0")
        if not c["blocker"]:
            raise LedgerError(f"{cid}: a {cls} component names its blocker")
        if c["evidence"] != cls:
            raise LedgerError(f"{cid}: class {cls} with evidence {c['evidence']}")
    if cls == "OWNED_ELSEWHERE" and c["owner_line"] in THIS_LINE:
        raise LedgerError(f"{cid}: owned elsewhere but its owner line is {c['owner_line']}")
    if cls == "BESIDE" and c["value"] is None:
        raise LedgerError(f"{cid}: a side-by-side figure carries its value")
    if c["floor_level_landing"] and c["owner_line"] in THIS_LINE and cls in ("CLOSABLE", "CONFLICT", "HELD"):
        raise LedgerError(f"{cid}: a landing at a floor level inside a floor-slab panel is slab concrete "
                          "(R-STAIR-LAND-1), never stair")


# ---------------------------------------------------------------- the whole line

def check_line(components, slab_regions=()):
    """Every component once: one record per region; a region the slab ledger already owns is never stair / dome."""
    seen = {}
    for c in components:
        check_component(c)
        if c["region"] in seen:
            raise LedgerError(f"region {c['region']} in {seen[c['region']]} and {c['id']}: counted twice")
        seen[c["region"]] = c["id"]
        if c["region"] in set(slab_regions) and c["owner_line"] in THIS_LINE and c["cls"] != "OWNED_ELSEWHERE":
            raise LedgerError(f"{c['id']}: region {c['region']} is billed by the slab ledger and again here")
    return True


def totals(components):
    out = dict(closable={e: 0.0 for e in CLOSABLE_EVIDENCE}, closable_total=0.0, conflict=[0.0, 0.0],
               held_low=0.0, held_high=0.0, held_open=[], unknown=[], owned_elsewhere={}, beside=0.0,
               by_element={})
    for c in components:
        el = out["by_element"].setdefault(c["element"], dict(closable=0.0, conflict=[0.0, 0.0], held_open=[]))
        if c["cls"] == "CLOSABLE":
            out["closable"][c["evidence"]] += c["value"]
            out["closable_total"] += c["value"]
            el["closable"] += c["value"]
        elif c["cls"] == "CONFLICT":
            out["conflict"][0] += c["bound"][0]
            out["conflict"][1] += c["bound"][1]
            el["conflict"][0] += c["bound"][0]
            el["conflict"][1] += c["bound"][1]
        elif c["cls"] == "HELD":
            b = c["bound"]
            if b is None or b[0] is None:
                out["held_open"].append(c["id"])
                el["held_open"].append(c["id"])
            else:
                out["held_low"] += b[0]
            if b is not None and b[1] is not None:
                out["held_high"] += b[1]
            elif c["id"] not in out["held_open"]:
                out["held_open"].append(c["id"])
                el["held_open"].append(c["id"])
        elif c["cls"] == "UNKNOWN":
            out["unknown"].append(c["id"])
            el["held_open"].append(c["id"])
        elif c["cls"] == "OWNED_ELSEWHERE":
            v = c["value"] if c["value"] is not None else 0.0
            out["owned_elsewhere"][c["owner_line"]] = out["owned_elsewhere"].get(c["owner_line"], 0.0) + v
        elif c["cls"] == "BESIDE":
            out["beside"] += c["value"]
    out["line_closable"] = not (out["held_open"] or out["unknown"] or out["conflict"][1] > 0 or out["held_high"] > 0)
    return out


def resolve_landing_edge(landing_from, flight_last_riser, flight_width):
    """A landing that a flight arrives into starts at that flight's last riser line. A reading that starts it earlier
    overlaps the flight's last going by (flight_last_riser - landing_from) x flight_width: refused as a double count,
    the overlap returned for the record."""
    overlap = flight_last_riser - landing_from
    if overlap > TOL:
        return dict(accepted=False, overlap_len=overlap, overlap_m2=overlap * flight_width)
    return dict(accepted=True, overlap_len=0.0, overlap_m2=0.0)


# ---------------------------------------------------------------- T-258 r2: arrival wedges and structural lane widths

ARRIVAL_KINDS = ("DEDUCTED", "OWNED_ELSEWHERE", "HELD_JUNCTION", "CONTINUES")


def arrival(kind, into, rows=(), value=None, note=""):
    """The one treatment of a flight's ARRIVAL WEDGE (the step triangle beyond its top riser line, inside whatever it
    arrives into):
        DEDUCTED         the wedge (or its part inside the receiving plate / member) is taken out of the flight value
                         by Q-62 A cond; `value` = the m3 deducted (> 0); the receiver (a stair landing, a slab plate or
                         a beam billed through) carries it once
        OWNED_ELSEWHERE  the wedge lies inside a member of another line (ground slab, ground beam) listed as its own
                         OWNED_ELSEWHERE row(s) in `rows` (valued, or an exposure with no value while unbilled)
        HELD_JUNCTION    the flight arrives into a HELD / CONFLICT / UNKNOWN component (`rows`): the wedge is inside
                         that held part, never released
        CONTINUES        no wedge exists: the flight runs on into the next flight `into` with no landing between"""
    return dict(kind=kind, into=into, rows=tuple(rows), value=value, note=note)


def check_arrivals(components):
    """R-STAIR-ARRIVAL-1 (T-258 r2, proposed; any villa): every flight's arrival wedge has exactly ONE treatment
    (arrival()), each referenced row exists with the class the treatment needs, and no wedge row serves two flights.
    A flight that arrives into a floor with no treatment (its top triangle silently carried as stair concrete, or
    silently dropped) is refused. Returns one record per flight for the ledger."""
    by_id = {c["id"]: c for c in components}
    used = {}
    out = []
    for c in components:
        if not c.get("is_flight"):
            continue
        cid, a = c["id"], c.get("arrival")
        if a is None:
            raise LedgerError(f"{cid}: flight with no arrival-wedge treatment (the triangle beyond its top riser line "
                              "is neither deducted, owned elsewhere, held, nor shown continuing)")
        if a["kind"] not in ARRIVAL_KINDS:
            raise LedgerError(f"{cid}: arrival kind {a['kind']!r} not one of {ARRIVAL_KINDS}")
        if not a["into"]:
            raise LedgerError(f"{cid}: arrival names what the flight arrives into")
        for r in a["rows"]:
            if r not in by_id:
                raise LedgerError(f"{cid}: arrival row {r} is not in the ledger (wedge row missing)")
            if r in used:
                raise LedgerError(f"{cid}: arrival row {r} already serves {used[r]}: one wedge, one flight")
            used[r] = cid
        if a["kind"] == "DEDUCTED":
            if a["value"] is None or a["value"] <= 0:
                raise LedgerError(f"{cid}: a DEDUCTED arrival wedge carries the m3 deducted (> 0)")
        elif a["kind"] == "OWNED_ELSEWHERE":
            if not a["rows"]:
                raise LedgerError(f"{cid}: an arrival wedge owned elsewhere lists its OWNED_ELSEWHERE row(s)")
            for r in a["rows"]:
                rc = by_id[r]
                if rc["cls"] != "OWNED_ELSEWHERE" or rc["owner_line"] in THIS_LINE:
                    raise LedgerError(f"{cid}: arrival row {r} is {rc['cls']} / {rc['owner_line']}, not another line")
            valued = sum(by_id[r]["value"] for r in a["rows"] if by_id[r]["value"] is not None)
            if a["value"] is not None and abs(valued - a["value"]) > TOL:
                raise LedgerError(f"{cid}: arrival value {a['value']:.6f} differs from its rows {valued:.6f}")
        elif a["kind"] == "HELD_JUNCTION":
            if not a["rows"] or any(by_id[r]["cls"] not in ("HELD", "CONFLICT", "UNKNOWN") for r in a["rows"]):
                raise LedgerError(f"{cid}: a held junction names the HELD / CONFLICT / UNKNOWN row it arrives into")
        elif a["kind"] == "CONTINUES":
            nxt = by_id.get(a["into"])
            if nxt is None or not nxt.get("is_flight"):
                raise LedgerError(f"{cid}: CONTINUES into {a['into']}, which is not a flight in the ledger")
        out.append(dict(flight=cid, kind=a["kind"], into=a["into"], rows=list(a["rows"]), value=a["value"],
                        note=a["note"]))
    return out


def resolve_lane_width(declared, lane_from, lane_to):
    """R-STAIR-LANE-1 (T-258 r2, proposed; any villa): a flight's or landing's width is the STRUCTURAL lane, from the
    opening / slab edge to the wall or band face, read on the structural sheet. A width larger than that lane (e.g. an
    architectural dimension reaching the outer face of a balustrade band past the slab edge) overlaps the slab panel
    by (declared - lane) per metre of run: refused, the overlap returned for the record."""
    lane = abs(lane_to - lane_from)
    over = declared - lane
    if over > TOL:
        return dict(accepted=False, lane=lane, overlap_width=over)
    return dict(accepted=True, lane=lane, overlap_width=0.0)
