"""MASONRY_AREA_V1 (T-108): block wall area, volume and installed white-block units per wall run, from the member above.

A ledger piece: NOT wired into any method version (ARCH_TAKEOFF_V2.9 .. V3.0.x and route G are unchanged); nothing
here is read by a released line. Standard library + OPENING_SCOPE_V1 (T-175, also unwired) only.

Owner rules applied (docs/agents/OWNER_QUESTIONS_ANSWERED.md):
  - Q-60 A (2026-10-20 10:45): each block wall goes up to the underside of what sits on it: storey height (slab top to
    slab top) minus the depth of the beam above that piece of wall (schedule "H"), or minus the slab thickness where no
    beam runs over it. A piece whose member above is not drawn, has no printed depth, or is a CONFLICT stays HELD (no
    default depth, no "usual villa" size: Q-19, standard s.2 default guard).
  - Q-69 B (CONDITIONAL): the block length is the PHYSICAL blockwork length (full glazing spans out); the architectural
    run is kept beside it as the owner-manual comparison. The member-above pieces may cover the architectural run: the
    height is weighted over the pieces, then applied to the physical length.
  - Q-73 (CONFIRMED 2026-10-22): the full area of every actual opening is deducted, only from masonry that is built and
    inside the measured run: delegated to OPENING_SCOPE_V1.wall_net (build before deduct).
  - Block type: what the drawings print governs; otherwise the owner fallback "outer white, inner black" (Q-60 answer)
    is ASSUMED — OWNER-APPROVED. Parapets / fences: Q-65 C, material HELD (not decided here).
  - White units: owner supplier sheet in the Q-60 answer: face 62.5 x 25 (thicknesses 10, 15, 20, 25, 30 cm) or face
    60 x 20 (15, 20 cm); units = net installed m2 / face area (6.4 and 8.333 per m2). The product face is not chosen by
    any drawing: both are reported, neither is "the" count. Black units: no supplier face size (Q-75, investigation
    T-176): HELD. Installed units only; waste, cutting, breakage and pallets are a separate procurement method (T-176,
    standard s.3).
  - Atab (precast lintel, 15 x 20, supplier lengths 1.00 / 1.20 / 2.50 / 3.00 / 4.00 m): "only for white blocks"; where
    the project prints a structural lintel schedule it wins and atab is NOT APPLICABLE (never both; owner 10:45 (3)).
    Without a printed schedule the atab length = width + 2 x bearing, the bearing taken only from a given source, else
    HELD; the shortest supplier length that covers it, none above 4.00 m (HELD).
  - Adhesive mortar: coverage not given by the owner: HELD on every wall.

Physical vs installed vs procurement (standard s.3): area and volume here are NET INSTALLED quantities; a volume from a
centreline run carries the T-stem overlap at junctions, reported only when the caller gives it (never estimated).
r2 (Checker rejection 2026-10-23 07:13): the length is the PHYSICAL run of the verified physical module
(MASONRY_CENTRELINE_V2, T-125: a T stem stops on the face of the through wall), so the stem overlap is 0 by
construction; a hand run is a comparison column only (length_source HAND caps the status at HELD) and a T-stem end
measured to the centreline is refused (check_length_source).

Guards (ValueError): a status outside the five section-5 statuses; lengths / depths in millimetres (a piece > 60 m, a
storey > 12 m, a depth > 3 m); a member depth not below the storey height; an unknown block type or member kind.
"""

from __future__ import annotations

from engine.source import opening_scope_v1 as OS

METHOD = "MASONRY_AREA_V1"
RULES = ("Q-60 A (owner 2026-10-20 10:45)", "Q-69 B (owner 2026-10-20 18:45, conditional)",
         "Q-73 (owner, CONFIRMED 2026-10-22) via OPENING_SCOPE_V1", "Q-65 C", "Q-75 / T-176 (black units HELD)",
         "ENGINEERING_REASONING_STANDARD.md s.3 (installed vs procurement, build before deduct)")
STATUSES = OS.STATUSES
DC, AOA, HELD, UNKNOWN = "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN"
MEMBER_KINDS = ("BEAM", "SLAB", "NONE")          # NONE: nothing drawn above (dome opening, column face, not bound)
BLOCK_TYPES = ("WHITE", "BLACK", None)
WHITE_FACES = {"62.5x25": {"face_m": (0.625, 0.25), "t_m": (0.10, 0.15, 0.20, 0.25, 0.30)},
               "60x20": {"face_m": (0.60, 0.20), "t_m": (0.15, 0.20)}}
ATAB_LENGTHS_M = (1.00, 1.20, 2.50, 3.00, 4.00)
MAX_PIECE_M, MAX_STOREY_M, MAX_DEPTH_M = 60.0, 12.0, 3.0
TOL = 1e-9


def _num(v, what, cap):
    return OS._num(v, what, cap)


def _st(s):
    OS._check_status(s)
    return s


def _known(v, s):
    return v is not None and s not in (HELD, UNKNOWN)


def piece_height(storey, member):
    """(height_m or None, status, why) of one piece: storey height minus the depth of what sits on it (Q-60 A)."""
    ss = _st(storey.get("status", UNKNOWN))
    f2f = _num(storey.get("floor_to_floor_m"), "storey height", MAX_STOREY_M)
    kind = member.get("kind")
    if kind not in MEMBER_KINDS:
        raise ValueError(f"member kind {kind!r} not in {MEMBER_KINDS}")
    ms = _st(member.get("status", UNKNOWN))
    if kind == "NONE":
        return None, HELD, "no beam or slab underside drawn above this piece (Q-60 A has nothing to stop at)"
    d = _num(member.get("depth_m"), f"{kind.lower()} depth", MAX_DEPTH_M)
    if f2f is None:
        return None, HELD if ss != UNKNOWN else UNKNOWN, "storey height not established"
    if d is None or not _known(d, ms):
        return None, HELD if ms != UNKNOWN else UNKNOWN, f"{kind.lower()} {member.get('mark') or ''} depth not " \
                                                       f"established ({member.get('why') or 'no printed depth'})"
    if d >= f2f - TOL:
        raise ValueError(f"member depth {d} m is not below the storey height {f2f} m")
    return round(f2f - d, 6), OS.weakest(ss, ms), f"{f2f} - {d} ({kind.lower()} {member.get('mark') or ''})"


LENGTH_SOURCES = ("PHYSICAL_MODULE", "HAND", None)   # r2: where physical_length_m comes from (None: not stated)
END_KINDS = ("T_STEM", "L", "FREE_END", "HELD", "CURVED", "OTHER")


def check_length_source(wall):
    """r2 (T-108 rejection 2026-10-23 07:13, owner Q-69 B 'never count masonry in two segments'). Returns
    (length_status_cap, flags). Refuses (ValueError) a run whose T-stem end is measured to the through-wall centreline:
    that piece of masonry is already in the through wall, so the length counts it twice. A length that is stated to be
    a HAND run (not the verified physical module) is a comparison column, never a quantity: its status is capped at
    HELD. An unstated source changes nothing (backward compatible)."""
    src = wall.get("length_source")
    if src not in LENGTH_SOURCES:
        raise ValueError(f"wall {wall.get('id')}: length source {src!r} not in {LENGTH_SOURCES}")
    for e in wall.get("ends") or ():
        k = e.get("kind")
        if k not in END_KINDS:
            raise ValueError(f"wall {wall.get('id')}: end kind {k!r} not in {END_KINDS}")
        if k == "T_STEM" and e.get("measured_to") not in ("FACE", None):
            raise ValueError(f"wall {wall.get('id')}: a T-stem end measured to the {e.get('measured_to')} of the "
                             f"through wall counts that piece twice (Q-69 B); give the physical length to the face")
    if src == "HAND":
        return HELD, ["LENGTH_SOURCE_HAND"]
    return None, []


def wall_gross(wall, storey):
    """Gross block area of one wall run. `wall`: id, t_m, physical_length_m (+ status), arch_length_m (optional),
    pieces [{length_m, member{kind, mark, depth_m, status}}]. The pieces are the member-above samples along the run;
    their lengths are scaled to the architectural run (or the physical one when no architectural run is given).
    r2: optional length_source / ends (check_length_source) and held_end_max_m: a junction end the physical module
    left unmeasured (up to that length more may be masonry): reported as a HELD bound, never added, never 0."""
    cap, lflags = check_length_source(wall)
    ls = _st(wall.get("length_status", UNKNOWN))
    if cap is not None:
        ls = OS.weakest(ls, cap)
    L = _num(wall.get("physical_length_m"), f"wall {wall.get('id')} length", MAX_PIECE_M)
    La = _num(wall.get("arch_length_m"), f"wall {wall.get('id')} architectural run", MAX_PIECE_M)
    pieces = wall.get("pieces") or []
    out = {"wall": wall.get("id"), "physical_length_m": L, "length_status": ls, "arch_length_m": La, "pieces": []}
    if L is None or not pieces:
        out.update(gross_m2=None, gross_status=HELD if ls != UNKNOWN else UNKNOWN, held_length_m=L,
                   height_weighted_m=None, coverage=None,
                   why="no length" if L is None else "no member above bound to this run", flags=lflags)
        return out
    tot = 0.0
    hl, hk, sts, held_why = 0.0, 0.0, [ls], []
    for p in pieces:
        pl = _num(p.get("length_m"), f"wall {wall.get('id')} piece length", MAX_PIECE_M)
        h, s, why = piece_height(storey, p["member"])
        tot += pl
        out["pieces"].append({"length_m": pl, "height_m": h, "status": s, "why": why})
        if h is None:
            hl += pl
            held_why.append(why)
            sts.append(s)
        else:
            hk += pl * h
            sts.append(s)
    if tot <= TOL:
        raise ValueError(f"wall {wall.get('id')}: pieces have no length")
    ref = La if La is not None else L
    scale = ref / tot
    held_len = round(min(hl * scale, L), 6)
    known_len = max(L - held_len, 0.0)
    hw = (hk / (tot - hl)) if tot - hl > TOL else None
    gross = round(known_len * hw, 6) if hw is not None else (0.0 if known_len <= TOL else None)
    status = OS.weakest(*sts)
    out.update(gross_m2=gross, gross_status=status, held_length_m=held_len, height_weighted_m=hw,
               coverage=round(tot / ref, 6), why="; ".join(sorted(set(held_why))))
    out["flags"] = (["LOW_HEIGHT_COVERAGE"] if tot / ref < 0.8 - TOL else []) + lflags
    out["clear_h_min_m"] = min((p["height_m"] for p in out["pieces"] if p["height_m"] is not None), default=None)
    he = _num(wall.get("held_end_max_m"), f"wall {wall.get('id')} held end", MAX_PIECE_M)
    if he is not None and he > TOL:
        out["held_end"] = {"max_m": he, "status": HELD,
                           "bounds_m2": (0.0, round(he * hw, 6)) if hw is not None else None,
                           "why": wall.get("held_end_why") or "junction end not measured by the physical module "
                                                              "(no clean T or L): 0 .. max more"}
        out["flags"].append("HELD_END")
    return out


def white_units(net_m2, t_m, status):
    """Installed white units per supplier face (no waste); a face not made in this thickness is NOT_AVAILABLE."""
    res = {}
    for name, f in WHITE_FACES.items():
        if not any(abs(t_m - x) < 1e-6 for x in f["t_m"]):
            res[name] = {"units": None, "status": "NOT_AVAILABLE", "why": f"face {name} not supplied in t {t_m} m"}
        elif net_m2 is None:
            res[name] = {"units": None, "status": status}
        else:
            per = 1.0 / (f["face_m"][0] * f["face_m"][1])
            res[name] = {"units": round(net_m2 * per, 3), "per_m2": round(per, 4), "status": status}
    return res


def atab(op_cons, block_type, printed_schedule, bearing):
    """Atab need for one opening consequence (OPENING_SCOPE_V1 dict). bearing: {m, status, source} or None."""
    if block_type != "WHITE":
        return {"status": "NOT_APPLICABLE", "why": "atab only for white blocks (owner Q-60 answer); "
                                                   "the opening's lintel belongs to the structural lintel line"}
    if op_cons["block_deduction"]["status"] == "NOT_APPLICABLE":
        return {"status": "NOT_APPLICABLE", "why": op_cons["block_deduction"].get("why", "no masonry around it")}
    if printed_schedule:
        return {"status": "NOT_APPLICABLE", "why": "the printed structural lintel schedule governs this opening "
                                                   "(owner 10:45 (3): never both)"}
    if op_cons["lintel"].get("status") == "NOT_APPLICABLE" and "head reaches" in op_cons["lintel"].get("why", ""):
        return {"status": "NOT_APPLICABLE", "why": "the head reaches the member above"}
    w, ws = op_cons["width_m"], op_cons["width_status"]
    if not _known(w, ws):
        return {"status": HELD, "why": "opening width not established"}
    if not bearing or not _known(bearing.get("m"), bearing.get("status", UNKNOWN)):
        return {"status": HELD, "why": "no bearing length given by a drawing, note or owner rule (never a default)"}
    need = round(w + 2 * float(bearing["m"]), 6)
    pick = next((x for x in ATAB_LENGTHS_M if x >= need - TOL), None)
    if pick is None:
        return {"status": HELD, "need_m": need, "why": f"needs {need} m > the longest supplier atab 4.00 m"}
    return {"status": OS.weakest(ws, bearing["status"]), "need_m": need, "piece_m": pick, "count": 1,
            "bearing_source": bearing.get("source")}


def wall_ledger(wall, storey, openings=(), printed_lintel_schedule=False, bearing=None, stem_overlap_m3=None):
    """One wall run: gross (Q-60 A x Q-69 B), net (Q-73 via OPENING_SCOPE_V1), m3, white units, atab, adhesive.
    The net value is computed arithmetically even on a HELD gross ('net_candidate_m2'), but only a net whose status is
    not HELD / UNKNOWN is a quantity ('net_m2'); HELD is never 0."""
    bt = wall.get("block_type")
    if bt not in BLOCK_TYPES:
        raise ValueError(f"wall {wall.get('id')}: block type {bt!r} not in {BLOCK_TYPES}")
    ts = _st(wall.get("type_status", UNKNOWN))
    t = _num(wall.get("t_m"), f"wall {wall.get('id')} thickness", 2.0)
    g = wall_gross(wall, storey)
    # arithmetic pass (status DC for the arithmetic only; the real status is applied below), only when the whole
    # length has a height: with a held length an opening may sit in the held part, so no candidate net is formed
    whole = g["gross_m2"] is not None and not (g.get("held_length_m") or 0.0) > TOL
    osw = {"id": wall.get("id"), "construction": "BLOCK", "t_m": t, "gross_m2": g["gross_m2"],
           "gross_status": DC if whole else HELD,
           "clear_h_min_m": g.get("clear_h_min_m")}
    net = OS.wall_net(osw, list(openings))
    status = OS.weakest(g["gross_status"], net["net_status"]) if g["gross_m2"] is not None else g["gross_status"]
    cand = net["net_m2"]
    qty = cand if _known(cand, status) else None
    units_status = OS.weakest(status, ts) if bt else HELD
    if bt == "WHITE":
        units = white_units(qty, t, units_status)
    elif bt == "BLACK":
        units = {"black": {"units": None, "status": HELD,
                           "why": "no black block face size from the drawings or the owner (Q-75 investigation T-176)"}}
    else:
        units = {"any": {"units": None, "status": HELD, "why": "block type not established (Q-65 C or no note)"}}
    at = [{"opening": c["id"], **atab(c, bt, printed_lintel_schedule, bearing)} for c in net["openings"]]
    out = {"wall": wall.get("id"), "floor": wall.get("floor"), "group": wall.get("group"), "t_m": t,
           "block_type": bt, "type_status": ts, "gross": g, "gross_m2": g["gross_m2"], "gross_status": g["gross_status"],
           "deducted_m2": net["deducted_m2"], "held_openings": net["held_openings"],
           "net_candidate_m2": cand, "net_m2": qty, "net_status": status,
           "net_bounds_m2": net.get("net_bounds_m2"), "openings": net["openings"],
           "gross_m3": round(g["gross_m2"] * t, 6) if g["gross_m2"] is not None else None,
           "net_m3": round(qty * t, 6) if qty is not None else None,
           "net_m3_candidate": round(cand * t, 6) if cand is not None else None,
           "units": units, "atab": at,
           "adhesive": {"status": HELD, "why": "adhesive coverage not given (owner Q-60 answer)"}}
    if stem_overlap_m3 is not None:
        so = _num(stem_overlap_m3, "stem overlap", 50.0)
        out["physical_m3"] = round(qty * t - so, 6) if qty is not None else None
        out["stem_overlap_m3"] = so
    return out


def totals(ledgers, keys=("floor", "block_type", "t_m")):
    """Sums by key, each evidence status separately (HELD / UNKNOWN never summed into a quantity)."""
    agg = {}
    for x in ledgers:
        k = tuple(x.get(kk) for kk in keys)
        a = agg.setdefault(k, {"walls": 0, "gross_known_m2": 0.0, "held_length_m": 0.0, "net_by_status": {},
                               "net_candidate_on_held_m2": 0.0, "walls_net_held": 0, "white_units": {}})
        a["walls"] += 1
        a["gross_known_m2"] += x["gross_m2"] or 0.0
        a["held_length_m"] += x["gross"].get("held_length_m") or 0.0
        if x["net_m2"] is not None:
            s = a["net_by_status"].setdefault(x["net_status"], {"walls": 0, "m2": 0.0, "m3": 0.0})
            s["walls"] += 1
            s["m2"] += x["net_m2"]
            s["m3"] += x["net_m3"]
            for f, u in x["units"].items():
                if u.get("units") is not None:
                    a["white_units"].setdefault(f, {})
                    a["white_units"][f][u["status"]] = a["white_units"][f].get(u["status"], 0.0) + u["units"]
        else:
            a["walls_net_held"] += 1
            if x["net_candidate_m2"] is not None:
                a["net_candidate_on_held_m2"] += x["net_candidate_m2"]
    return agg


def policy_record():
    return {"method": METHOD, "rules": list(RULES), "statuses": list(STATUSES), "wired": False,
            "scope": "every villa: block m2 / m3 / installed white units per wall run; procurement in T-176"}
