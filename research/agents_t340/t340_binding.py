"""T-340 core (every villa): bind a Checker-verified opening REVEAL ledger (T-313 grain) and SILL / THRESHOLD ledger
(T-325 grain) to the candidate's line ids, ONE owner per physical component, and cross-check the wet rooms so that no
reveal surface is already inside a backing-plaster or wall-tile face. Research only: no engine module, no candidate
line changes; lane I applies the FILL tables (T-326 reveals, T-327 sills / thresholds).

Rule R-T340-BIND-1 (research rule, project-independent; provenance UP-REVEAL-001, UP-FIN-PLASTER-001, UP-THR-001,
UP-FIN-PAINT-001 substrate, Q-55 C, Q-37 A, URBAN-REVEAL-FINISH-METHOD v1, T-313 r2 / T-325 / T-336 verdicts):

1. A physical component is (opening id, component). Components: REVEAL_THROUGH_JAMBS / _HEAD (door / gate / arch: one
   surface through the wall), REVEAL_OUT_* and REVEAL_IN_* (window, per side), SILL_OUT / SILL_IN (window),
   THRESHOLD_OUT / THRESHOLD_IN (floor-level window), THRESHOLD (door / arch strip). The two ledgers that both describe a
   window sill or a floor-level window strip describe ONE surface: their areas must agree, else the binding stops.
2. Every component has exactly one owner: an existing candidate line id, or a NEW row name, or none (NOT_APPLICABLE
   with evidence / HELD / UNKNOWN, always blank, never 0). A component in two owners is refused; an existing line that
   owns components of two openings is refused.
3. A door reveal already carried by a FIN.PLASTER 'door jambs and head' line stays ONLY there (a NEW reveal row for that
   door is refused); a door with no such line gets ONE new row in the same family (same owner rule).
4. Sills and thresholds are their own item (never a reveal component): a sill / threshold owned by a reveal row is
   refused, and a reveal owned by a threshold / sill line is refused.
5. Wet rooms: a backing or tile face is the wall face less each opening's part in the band; a reveal is not a wall face.
   The check recomputes every face (gross - deductions = net, residual named) and refuses any reveal / sill / threshold
   component whose owner is a backing or tile line. Reveal finish follows the printed specification or the owner method
   (URBAN-REVEAL-FINISH-METHOD v1: plaster by default, porcelain only where shown, never because the room is wet).
6. A corrected value supersedes the old one: using a superseded value is refused. A layer below a threshold (the
   waterproofing doorway piece) is the same strip, its own layer: the areas are compared by door, a difference named.
"""
from __future__ import annotations

from dataclasses import dataclass, field

TOL = 1e-6
STATUSES = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN",
            "NOT_APPLICABLE_WITH_EVIDENCE")
SILL_COMPONENTS = ("SILL_OUT", "SILL_IN", "THRESHOLD_OUT", "THRESHOLD_IN", "THRESHOLD")
REVEAL_LINE_ITEMS = ("FIN.PLASTER",)                     # 'door jambs and head' lines
SILL_LINE_ITEMS = ("ARCH.WINDOW_REVEAL", "ARCH.THRESHOLD", "FIN.MARBLE.THRESHOLD", "FIN.FLOOR.PORCELAIN")


class BindingError(ValueError):
    """a binding that would count a component twice, lose it, or turn a held quantity into 0"""


def num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    return float(s) if s not in ("", "-", "None") else None


def status_of(evidence, state):
    """map a ledger's evidence / state to WORKFLOW_CONTROLS s.5 (the approved source kept in the text)."""
    e = (evidence or "").strip()
    st = (state or "").strip().upper()
    if st == "NONE" or "(no surface)" in e:
        return "NOT_APPLICABLE_WITH_EVIDENCE"
    if st == "HELD" or e.startswith("HELD"):
        return "HELD"
    if st == "UNRESOLVED" or e.startswith("UNKNOWN"):
        return "UNKNOWN"
    if e.startswith("ASSUMED"):
        return e if "(" in e else "ASSUMED — OWNER-APPROVED"
    if e.startswith("DRAWING-CONFIRMED"):
        return "DRAWING-CONFIRMED"
    if e.startswith("VERIFIED"):
        return "VERIFIED"
    raise BindingError(f"unknown evidence status {evidence!r} / {state!r}")


def is_blank_status(status):
    return status in ("HELD", "UNKNOWN", "NOT_APPLICABLE_WITH_EVIDENCE")


@dataclass
class Component:
    opening: str
    kind: str                       # DOOR / WINDOW / FLOOR_GLAZING / ARCH / GATE
    comp: str                       # REVEAL_<side>_<JAMBS|HEAD> or one of SILL_COMPONENTS
    m2: float | None
    ml: float | None
    pcs: int | None
    status: str
    material: str = ""
    rooms: str = ""
    ledger_line: str = ""           # the line the source ledger bound it to ('' = none)
    sources: list = field(default_factory=list)
    parts: dict = field(default_factory=dict)   # e.g. jambs / head m2 of a reveal

    @property
    def key(self):
        return (self.opening, self.comp)


def _reveal_comp(side, part):
    return f"REVEAL_{side}_{part}"


def is_reveal(comp):
    return comp.startswith("REVEAL_")


def reveal_components(rows, source="T-313"):
    """reveal ledger rows (opening, kind, side THROUGH / OUT / IN, component JAMBS / HEAD / SILL / THRESHOLD /
    FLOOR_STRIP) -> components: each side's jambs and head are their own component (a held jamb never hides a measured
    head); sills and floor strips are sill / threshold components."""
    out = {}
    for r in rows:
        part = r["component"]
        if part in ("JAMBS", "HEAD"):
            comp = _reveal_comp(r["side"], part)
        else:
            comp = {"SILL": "SILL_OUT" if r["side"] == "OUT" else "SILL_IN",
                    "THRESHOLD": "THRESHOLD_OUT", "FLOOR_STRIP": "THRESHOLD_IN"}.get(part)
            if comp is None:
                raise BindingError(f"unknown reveal component {part}")
        ck = (r["opening"], comp)
        if ck in out:
            raise BindingError(f"reveal ledger row twice: {ck}")
        m2, ml = num(r.get("m2")), num(r.get("ml"))
        if (m2 is not None and m2 < 0) or (ml is not None and ml < 0):
            raise BindingError(f"negative quantity {ck}")
        st = status_of(r.get("evidence"), r.get("state"))
        if st in ("HELD", "UNKNOWN") and m2 is not None:
            raise BindingError(f"{ck}: a {st} component carries a figure")
        if st == "NOT_APPLICABLE_WITH_EVIDENCE" and m2 not in (None, 0.0):
            raise BindingError(f"{ck}: a no-surface component carries a figure")
        if st not in ("HELD", "UNKNOWN", "NOT_APPLICABLE_WITH_EVIDENCE") and m2 is None:
            raise BindingError(f"{ck}: a measured component has no figure (missing never becomes 0)")
        line = r.get("line_id") or ""
        out[ck] = Component(r["opening"], r["kind"], comp, m2, ml, None, st, rooms=r.get("room", ""),
                            ledger_line="" if line == "NO_LINE" else line, sources=[source])
    return out


ORDER = {"NOT_APPLICABLE_WITH_EVIDENCE": 0, "VERIFIED": 1, "DRAWING-CONFIRMED": 2, "ASSUMED": 3, "HELD": 4,
         "UNKNOWN": 5}


def _rank(s):
    return ORDER["ASSUMED"] if s.startswith("ASSUMED") else ORDER[s]


def _worst(a, b):
    """the status of a component made of parts: the weakest part governs (HELD / UNKNOWN never upgraded); a measured
    part beside a no-surface part keeps the measured part's status."""
    if "NOT_APPLICABLE_WITH_EVIDENCE" in (a, b) and a != b:
        return b if a == "NOT_APPLICABLE_WITH_EVIDENCE" else a
    return a if _rank(a) >= _rank(b) else b


def sill_components(rows, source="T-325"):
    out = {}
    for r in rows:
        comp = r["component"]
        if comp == "FINISH_CHANGE_EDGE":
            continue                                   # geometry, NOT_AN_ITEM (R-T325-1): never a line
        if comp not in SILL_COMPONENTS:
            raise BindingError(f"unknown sill / threshold component {comp}")
        ck = (r["opening"], comp)
        if ck in out:
            raise BindingError(f"{ck} twice in the sill ledger")
        st = status_of("UNKNOWN" if r["state"] == "UNRESOLVED" else
                       ("DRAWING-CONFIRMED (no surface)" if r["state"] == "NONE" else "DRAWING-CONFIRMED"), r["state"])
        m2 = num(r.get("m2"))
        if st in ("HELD", "UNKNOWN") and m2 is not None:
            raise BindingError(f"{ck}: a {st} component carries a figure")
        line = r.get("line_id") or ""
        out[ck] = Component(r["opening"], r["kind"], comp, m2, num(r.get("edge_ml")),
                            int(r["pcs"]) if (r.get("pcs") or "").strip() else None, st,
                            material=r.get("material", ""), rooms=r.get("floor", ""),
                            ledger_line="" if line == "NO_LINE" else line, sources=[source])
    return out


def merge_ledgers(reveal, sills):
    """one component per (opening, component): a sill / strip described by both ledgers is ONE surface; the areas and
    the bound line must agree (the sill ledger, the item ledger, carries the material and the count)."""
    merged = dict(reveal)
    for k, s in sills.items():
        r = merged.get(k)
        if r is None:
            merged[k] = s
            continue
        if (r.m2 is None) != (s.m2 is None) or (r.m2 is not None and abs(r.m2 - s.m2) > TOL):
            raise BindingError(f"{k}: the two ledgers disagree on one surface ({r.m2} vs {s.m2})")
        if r.ledger_line and s.ledger_line and r.ledger_line != s.ledger_line:
            raise BindingError(f"{k}: the two ledgers bind one surface to two lines")
        s.sources = r.sources + s.sources
        s.ledger_line = s.ledger_line or r.ledger_line
        if r.status != s.status and not (is_blank_status(r.status) and is_blank_status(s.status)):
            s.status = _worst(r.status, s.status)
        merged[k] = s
    return merged


@dataclass
class Owner:
    opening: str
    comp: str
    owner: str                  # an existing line id, 'NEW:<row name>' or '' (blank: NA / HELD / UNKNOWN)
    owner_item: str
    action: str                 # KEEP / NARROW / FILL / RETYPE_FILL / ADD_ROW / HOLD / NOT_APPLICABLE
    m2: float | None
    ml: float | None
    pcs: int | None
    status: str
    material: str
    fill_table: str             # T-326 (reveals) / T-327 (sills, thresholds) / '' (no line action)
    note: str = ""


def assign_owners(components, lines, door_plaster=None, narrow=None, retype=None, new_rows=None):
    """components: {key: Component}; lines: {line_id: {item_code, evidence_state, measured_net, low, high, ...}} of the
    candidate; door_plaster: {door: line_id} (the FIN.PLASTER 'door jambs and head' line of the door);
    narrow: {line_id: (value, why)}; retype: {line_id: (item, why)} for closure lines whose finish an owner rule sets;
    new_rows: {(opening, comp): row name} for missing scope (one row may hold several components of ONE opening).
    A line / row's figure is the sum of its measured components; held / unknown parts stay blank beside it.
    Returns the owner rows (one per component) and the per-carrier summary."""
    door_plaster, narrow, retype, new_rows = door_plaster or {}, narrow or {}, retype or {}, new_rows or {}
    groups = {}
    for k in sorted(components):
        c = components[k]
        line = c.ledger_line
        if line and line not in lines:
            raise BindingError(f"{k}: bound to {line}, which is not a line of the candidate")
        if line:
            item = lines[line]["item_code"]
            if is_reveal(c.comp) and item not in REVEAL_LINE_ITEMS:
                raise BindingError(f"{k}: a reveal owned by a {item} line (sills / thresholds are their own item)")
            if c.comp in SILL_COMPONENTS and item not in SILL_LINE_ITEMS:
                raise BindingError(f"{k}: a sill / threshold owned by a {item} line (a reveal line is not a sill)")
        if c.comp.startswith("REVEAL_THROUGH") and c.opening in door_plaster:
            if line != door_plaster[c.opening]:
                raise BindingError(f"{k}: the door's reveal is carried by FIN.PLASTER {door_plaster[c.opening]}; "
                                   "a second carrier is refused")
        if line and k in new_rows:
            raise BindingError(f"{k}: a NEW row for a component a line already carries (a second carrier)")
        if line:
            carrier = line
        elif k in new_rows:
            carrier = "NEW:" + new_rows[k]
        elif c.status in ("HELD", "UNKNOWN", "NOT_APPLICABLE_WITH_EVIDENCE"):
            carrier = ""
        else:
            raise BindingError(f"{k}: a measured component with no owner (missing scope must get a row)")
        groups.setdefault(carrier or f"NONE:{k}", []).append(c)
    rows, carriers = [], []
    for carrier, cs in sorted(groups.items()):
        ops = {c.opening for c in cs}
        if len(ops) > 1:
            raise BindingError(f"{carrier} owns components of {sorted(ops)} (one carrier, one opening)")
        table = "T-326" if all(is_reveal(c.comp) for c in cs) else "T-327"
        if any(is_reveal(c.comp) for c in cs) and table == "T-327":
            raise BindingError(f"{carrier} mixes reveal and sill / threshold components")
        meas = [c for c in cs if c.status not in ("HELD", "UNKNOWN", "NOT_APPLICABLE_WITH_EVIDENCE")]
        held = [c for c in cs if c.status in ("HELD", "UNKNOWN")]
        value = round(sum(c.m2 for c in meas), 6) if meas else None
        if carrier.startswith("NONE:"):
            c = cs[0]
            act = "NOT_APPLICABLE" if c.status == "NOT_APPLICABLE_WITH_EVIDENCE" else "HOLD"
            rows.append(Owner(c.opening, c.comp, "", "", act, 0.0 if act == "NOT_APPLICABLE" else None,
                              0.0 if act == "NOT_APPLICABLE" else None, None, c.status, c.material, "",
                              "no surface (drawn frame position), no line needed" if act == "NOT_APPLICABLE"
                              else "no carrier; blank, never 0"))
            continue
        if carrier.startswith("NEW:"):
            item = carrier[4:].split("|")[0]
            act, note = ("ADD_ROW", "missing scope: no line in any family") if meas else ("ADD_HELD_ROW", "blank row")
        else:
            ln = lines[carrier]
            item = retype[carrier][0] if carrier in retype else ln["item_code"]
            if meas:
                act, value, note = _line_action(carrier, value, ln, narrow.get(carrier), retype.get(carrier))
            else:
                act, note = ("HOLD", "blank, never 0") if held else ("KEEP_NA", "no surface on any side")
        if held:
            note += "; HELD beside: " + ", ".join(f"{c.comp} {c.status}" for c in held)
        carriers.append({"carrier": carrier, "opening": cs[0].opening, "item": item, "action": act, "m2": value,
                         "ml": round(sum(c.ml or 0 for c in meas), 6) if meas else None,
                         "pcs": sum(c.pcs or 0 for c in meas) if meas and any(c.pcs for c in meas) else None,
                         "components": ";".join(c.comp for c in cs), "held": ";".join(c.comp for c in held),
                         "status": _carrier_status([c.status for c in meas]) if meas else
                         (held[0].status if held else "NOT_APPLICABLE_WITH_EVIDENCE"),
                         "material": "; ".join(sorted({c.material for c in cs if c.material and c.material != "-"})),
                         "fill_table": table, "note": note})
        for c in cs:
            blank = c.status in ("HELD", "UNKNOWN")
            na = c.status == "NOT_APPLICABLE_WITH_EVIDENCE"
            rows.append(Owner(c.opening, c.comp, carrier, item, act, None if blank else (0.0 if na else c.m2),
                              None if blank else (0.0 if na else c.ml), c.pcs, c.status, c.material, table, note))
    _check_once(rows)
    return rows, carriers


def _carrier_status(sts):
    """a carrier's figure is as weak as its weakest measured component (an owner-approved part keeps it ASSUMED)."""
    worst = max(sts, key=_rank)
    return worst


def _line_action(carrier, v, ln, narrow, retype):
    q, lo, hi = num(ln.get("measured_net")), num(ln.get("low")), num(ln.get("high"))
    if narrow is not None:
        nv, why = narrow
        if abs(nv - v) > TOL:
            raise BindingError(f"{carrier}: the narrowed value {nv} is not the ledger value {v}")
        if lo is None or hi is None or not (lo - TOL <= nv <= hi + TOL):
            raise BindingError(f"{carrier}: narrowing outside the line's bound")
        return "NARROW", nv, why
    if retype is not None:
        if q is not None:
            raise BindingError(f"{carrier}: a valued line is not retyped here")
        return "RETYPE_FILL", v, retype[1]
    if q is not None:
        if abs(q - v) > TOL:
            raise BindingError(f"{carrier}: line {q} vs ledger {v} differ (DIFFERS is not a binding)")
        return "KEEP", v, "EQUAL, residual 0.000000"
    if lo is not None and hi is not None:
        if not (lo - TOL <= v <= hi + TOL):
            raise BindingError(f"{carrier}: ledger {v} outside the line's bound {lo} .. {hi}")
        return "KEEP", v, (f"WITHIN_BOUND {lo} .. {hi}: residual {round(v - lo, 6)} to the low end, "
                           f"{round(v - hi, 6)} to the high end")
    return "FILL", v, "the line is blank: filled from the ledger"


def _check_once(rows):
    seen = set()
    for r in rows:
        k = (r.opening, r.comp)
        if k in seen:
            raise BindingError(f"{k} has two owners")
        seen.add(k)
        if r.status in ("HELD", "UNKNOWN") and r.m2 is not None:
            raise BindingError(f"{k}: HELD carried as a figure")


def check_superseded(values, superseded):
    """values: {(door, layer): m2}; superseded: {(door, layer): old m2}. Refuses a superseded figure."""
    for k, old in superseded.items():
        v = values.get(k)
        if v is not None and abs(v - old) <= TOL:
            raise BindingError(f"{k}: the superseded value {old} is used")


def layer_check(thresholds, wp, alias=None):
    """thresholds: {door: finish strip m2}; wp: {door or alias: waterproofing doorway piece m2}. Same strip, two layers:
    return rows door, finish, wp, difference (named), and doors carried by one layer only."""
    alias = alias or {}
    wp_by_door = {}
    for d, v in wp.items():
        dd = alias.get(d, d)
        if dd in wp_by_door:
            raise BindingError(f"waterproofing piece of {dd} twice")
        wp_by_door[dd] = v
    out = []
    for d in sorted(set(thresholds) | set(wp_by_door)):
        f, w = thresholds.get(d), wp_by_door.get(d)
        diff = None if f is None or w is None else round(w - f, 6)
        out.append({"door": d, "finish_m2": f, "wp_m2": w, "difference_m2": diff,
                    "result": ("FINISH ONLY (no wet doorway: no membrane piece)" if w is None else
                               "WP ONLY" if f is None else "EQUAL" if abs(diff) <= TOL else "DIFFERS (named)")})
    return out


def face_closure(faces, openings):
    """faces: [{face_id, length_m, top_m, net_m2, openings: [ids]}]; openings: {(face_id, id): part m2 in the band}.
    gross - deductions = net on every face (no reveal surface inside a face); returns rows with the residual."""
    rows = []
    for f in faces:
        gross = f["length_m"] * f["top_m"]
        ded = 0.0
        for o in f["openings"]:
            part = openings.get((f["face_id"], o))
            if part is None:
                raise BindingError(f"{f['face_id']}: opening {o} has no band part (a valued face with a held deduction)")
            ded += part
        res = round(f["net_m2"] - (gross - ded), 4)
        rows.append({"face_id": f["face_id"], "gross_m2": round(gross, 6), "deductions_m2": round(ded, 6),
                     "net_m2": f["net_m2"], "residual_m2": res})
    return rows


def wet_cross_check(wet_openings, owners, backing_lines, tile_lines, closure_rows, tol=0.00051):
    """wet_openings: [{room, opening, face_id, band_m2}] (openings inside a backed / tiled face); owners: owner rows;
    backing_lines / tile_lines: sets of line ids. Every reveal / sill / threshold of a wet opening is named with its
    owner; an owner among the backing or tile lines is refused; the face closure residual must be within the 4-dp
    rounding of the face figures (else the face carries something beyond wall face less openings)."""
    by_open = {}
    for r in owners:
        by_open.setdefault(r.opening, []).append(r)
    bad = {x["face_id"]: x for x in closure_rows if abs(x["residual_m2"]) > tol}
    if bad:
        raise BindingError(f"face closure fails (a surface beyond the wall face is inside): {sorted(bad)}")
    out = []
    for w in wet_openings:
        for r in sorted(by_open.get(w["opening"], []), key=lambda x: x.comp):
            if r.owner in backing_lines or r.owner in tile_lines:
                raise BindingError(f"{w['opening']} {r.comp}: owned by a backing / tile line {r.owner}")
            out.append({"room": w["room"], "face_id": w["face_id"], "opening": w["opening"], "band_part_m2": w["band_m2"],
                        "component": r.comp, "component_m2": r.m2, "owner": r.owner or "(none)",
                        "owner_item": r.owner_item, "status": r.status, "overlap_m2": 0.0 if r.m2 is not None else None,
                        "why": ("the face deducts the opening's part in the band; the reveal is the surface through the "
                                "wall, not a wall face (closure residual within rounding)"
                                if is_reveal(r.comp) else
                                "a sill / threshold is a horizontal strip, not a wall face")})
    return out
