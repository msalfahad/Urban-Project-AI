"""LEVEL_CHAIN_V1 (T-200, residential review R5): every level a named physical datum, with the build-up between them.

A pure CHECK, NOT wired into any method version (ARCH_TAKEOFF_V2.9 .. V3.0.x and route G are unchanged): it produces
datum, link and issue rows, never a BOQ quantity. Standard library only; imports no engine module. Any villa.

Why (PROJECT_UNDERSTANDING_ASSESSMENT s.6 R5; ENGINEERING_REASONING_STANDARD s.2-3): a height is the difference of two
NAMED physical surfaces. Four times on the development villa a height was taken from whichever level was nearest: a
pool's finished water depth used as its concrete wall height, a window sill measured from the plot ground line instead
of its own floor, column necks run to the finished floor level on an unprinted founding depth, and a stair head placed
against a beam whose top was taken to be the finished floor. This module keeps, per storey / element, the chain of
named datums with the printed source of each, the layer (build-up, slab, beam, footing, blinding ...) between each pair,
and the status of every link:

  VERIFIED / DRAWING-CONFIRMED / ASSUMED — OWNER-APPROVED   (WORKFLOW_CONTROLS s.5: the weakest input decides)
  HELD      a datum or layer no sheet prints: the missing item is NAMED, the value stays None (never a convention,
            never 0: R1 / T-186 default guard)
  CONFLICT  two sources print different values for one datum, or two datums and the layer between them disagree

and checks every declared USE of a level by a quantity:

  FINISHED_AS_STRUCTURAL   a finished level (FFL, finished roof, finished pool floor, ...) used where a structural
                           surface is needed (slab / beam / ground-beam top, footing, pool base, ...)
  STRUCTURAL_AS_FINISHED   the reverse
  WRONG_REFERENCE          a relative height (a sill, a head, a storey height) measured from another datum than the
                           one it must be measured from (the floor the element sits on)
  VALUE_NOT_FROM_DRAWINGS  a value used that equals no printed or derived datum of the needed kind (a convention)
  NEEDS_HELD               the needed datum is HELD / CONFLICT: the quantity that uses it is HELD
  OK                       the use takes the needed datum, as printed or derived

Two ZERO systems (an architectural ±0.00 and a structural ±0.00) are one datum only when evidence says so:
`zero_relation_from_marks` fits the level marks both sets print for the same surfaces; values of a system with no
established relation to the base system are not combined (ZERO_RELATION_UNKNOWN), never silently added.

Input (`check(project)`):
  {"base_system": "ARCH", "units": "m" | "mm" (required; every value and layer of the project),
   "zero_relations": [{"system", "offset" (value in base = value in system + offset), "status", "ref"}],
   "chains": [{"chain_id", "family": FLOOR | ROOF | FOUNDATION | POOL | <custom with "links">, "storey", "element",
               "links": [[upper kind, lower kind, layer name], ...] (optional: replaces the family template)}],
   "datums": [{"chain_id", "kind", "value", "system", "status", "ref" (sheet / page / mark / handle: required),
               "bound": None | "AT_MOST" | "AT_LEAST" (a printed limit, e.g. 'excavation not less than 1.5 m below
               ground' = FORMATION AT_MOST ground - 1.5; a bound is a constraint, never a value)}],
   "layers": [{"chain_id", "layer", "thickness" (>= 0), "status", "ref", "method": "DRAWING" | "OWNER_MANUAL"}]
             OWNER_MANUAL layers are reported beside the drawing chain (owner manual method, side by side), never used
             to derive a datum,
   "uses": [{"use_id", "quantity" (what uses the level), "chain_id", "needs": kind, "used": {"chain_id", "kind"}
             | {"value": number} , "measured_from": {"chain_id", "kind"} (for a relative height),
             "must_be_from": {"chain_id", "kind"}, "margin": {"up": m, "down": m} (optional: how far the used level
             may sit from the needed one without changing the quantity, as stated by the use's own ledger), "ref"}]}

Guards (ValueError: a wrong input never becomes a finding): units missing or not m / mm; a level or layer above 300 m
in magnitude (millimetres given as metres); a negative layer; an unknown kind / family / layer / status / method /
bound; a datum, layer or use without ref; a datum on an unknown chain; a use of an unknown chain.
"""

from __future__ import annotations

METHOD = "LEVEL_CHAIN_V1"
RULES = ("ENGINEERING_REASONING_STANDARD.md s.2-3 (define the physical element; notation meaning before arithmetic)",
         "proposed UP-LEVEL-DATUM-001 (every height is the difference of two named datums with a printed source; T-200)",
         "R-POOL-4 r2 (RC wall height = rim -> structure line; finished depth kept beside; T-183)",
         "T-198 lesson (an elevation chain is re-datumed from the floor's own level marker)",
         "owner Q-21 C (founding level held until the arrangement is verified), Q-43 / Q-48 (owner manual heights)",
         "WORKFLOW_CONTROLS s.5 (statuses; HELD never 0); T-186 default guard (no convention where a sheet prints)")

FINISHED = ("FFL", "FINISHED_ROOF", "FINISHED_GROUND", "POOL_FINISHED_FLOOR", "DECK_FINISH", "PARAPET_TOP")
STRUCTURAL = ("SLAB_TOP", "SLAB_SOFFIT", "BEAM_BOTTOM", "GB_TOP", "GB_BOTTOM", "FOOTING_TOP", "FOOTING_BOTTOM",
              "POOL_RIM", "POOL_BASE_TOP", "POOL_BASE_UNDERSIDE")
SUBSTRATE = ("BLINDING_TOP", "FORMATION", "EXISTING_GROUND")
KINDS = FINISHED + STRUCTURAL + SUBSTRATE

TEMPLATES = {
    "FLOOR": (("FFL", "SLAB_TOP", "FLOOR_BUILD_UP"), ("SLAB_TOP", "SLAB_SOFFIT", "SLAB_THICKNESS"),
              ("SLAB_TOP", "BEAM_BOTTOM", "BEAM_DEPTH")),
    "ROOF": (("FINISHED_ROOF", "SLAB_TOP", "ROOF_BUILD_UP"), ("SLAB_TOP", "SLAB_SOFFIT", "SLAB_THICKNESS"),
             ("SLAB_TOP", "BEAM_BOTTOM", "BEAM_DEPTH"), ("PARAPET_TOP", "FINISHED_ROOF", "PARAPET_HEIGHT")),
    "FOUNDATION": (("FFL", "SLAB_TOP", "FLOOR_BUILD_UP"), ("SLAB_TOP", "GB_TOP", "GB_TOP_BELOW_SLAB_TOP"),
                   ("GB_TOP", "GB_BOTTOM", "GB_DEPTH"), ("GB_TOP", "FOOTING_TOP", "NECK_RUN"),
                   ("FOOTING_TOP", "FOOTING_BOTTOM", "FOOTING_DEPTH"), ("FOOTING_BOTTOM", "BLINDING_TOP", "UNDERLAY"),
                   ("BLINDING_TOP", "FORMATION", "BLINDING_THICKNESS"),
                   ("EXISTING_GROUND", "FORMATION", "EXCAVATION_DEPTH")),
    "POOL": (("POOL_RIM", "POOL_FINISHED_FLOOR", "FINISHED_DEPTH"),
             ("POOL_FINISHED_FLOOR", "POOL_BASE_TOP", "FLOOR_BUILD_UP"),
             ("POOL_RIM", "POOL_BASE_TOP", "RC_WALL_HEIGHT"),
             ("POOL_BASE_TOP", "POOL_BASE_UNDERSIDE", "BASE_THICKNESS"),
             ("POOL_BASE_UNDERSIDE", "BLINDING_TOP", "UNDERLAY"), ("BLINDING_TOP", "FORMATION", "BLINDING_THICKNESS"),
             ("EXISTING_GROUND", "FORMATION", "EXCAVATION_DEPTH")),
}
LAYERS = tuple(sorted({lk[2] for t in TEMPLATES.values() for lk in t}))
STATUSES = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN")
RANK = {"VERIFIED": 3, "DRAWING-CONFIRMED": 2, "ASSUMED — OWNER-APPROVED": 1}
METHODS = ("DRAWING", "OWNER_MANUAL")
BOUNDS = (None, "AT_MOST", "AT_LEAST")
CODES = ("CONFLICT", "LINK_MISMATCH", "HELD_LINK", "CONSTRAINT_VIOLATED", "ZERO_RELATION_UNKNOWN",
         "FINISHED_AS_STRUCTURAL", "STRUCTURAL_AS_FINISHED", "WRONG_REFERENCE", "VALUE_NOT_FROM_DRAWINGS",
         "NEEDS_HELD", "OK")
TOL = 0.005           # m: printed levels are to the centimetre; 5 mm agrees, 1 cm does not
MAX_ABS_M = 300.0
SCALE = {"m": 1.0, "mm": 0.001}


def category(kind):
    if kind in FINISHED:
        return "FINISHED"
    if kind in STRUCTURAL:
        return "STRUCTURAL"
    if kind in SUBSTRATE:
        return "SUBSTRATE"
    raise ValueError(f"unknown datum kind {kind!r}")


def _scale(units):
    if units not in SCALE:
        raise ValueError(f"units must be 'm' or 'mm', got {units!r} (nothing is guessed)")
    return SCALE[units]


def _num(v, k, what):
    if v is None or isinstance(v, bool):
        raise ValueError(f"{what}: value missing")
    x = float(v) * k
    if abs(x) > MAX_ABS_M:
        raise ValueError(f"{what}: {x:.3f} m is beyond {MAX_ABS_M} m (millimetres given as metres?)")
    return x


def _status(s, what):
    if s not in STATUSES:
        raise ValueError(f"{what}: unknown status {s!r}")
    return s


def _ref(r, what):
    if not r:
        raise ValueError(f"{what}: ref (sheet / page / mark / handle) is required")
    return r


def _weakest(statuses):
    ranks = [RANK.get(s) for s in statuses]
    if any(r is None for r in ranks):
        return "HELD"
    return min(statuses, key=lambda s: RANK[s])


# ------------------------------------------------------------------------------------------------- zero systems
def zero_relation_from_marks(marks_a, marks_b, units, pos_tol=5.0, min_matches=3):
    """Do two sheets measure from one zero? marks = [{"text", "value", "x", "y", "ref"}] in drawing units (`units`
    gives the VALUE unit). Finds the plan translation that makes the most marks of A land on marks of B with the same
    printed text; then compares the values of the matched pairs.

    Returns {"matched", "unmatched_a", "unmatched_b", "offset" (value_b - value_a, m) | None, "status", "pairs"}:
    DRAWING-CONFIRMED when at least `min_matches` pairs coincide and every pair gives the same offset; CONFLICT when the
    pairs give different offsets; UNKNOWN when fewer than `min_matches` coincide (no relation is inferred)."""
    k = _scale(units)
    best = (0, None)
    for a in marks_a:
        for b in marks_b:
            if a["text"] != b["text"]:
                continue
            dx, dy = b["x"] - a["x"], b["y"] - a["y"]
            n = sum(1 for p in marks_a if any(q["text"] == p["text"] and abs(q["x"] - p["x"] - dx) <= pos_tol
                                              and abs(q["y"] - p["y"] - dy) <= pos_tol for q in marks_b))
            if n > best[0]:
                best = (n, (dx, dy))
    pairs, used_b = [], set()
    if best[1] is not None:
        dx, dy = best[1]
        for p in marks_a:
            for i, q in enumerate(marks_b):
                if i in used_b or q["text"] != p["text"]:
                    continue
                if abs(q["x"] - p["x"] - dx) <= pos_tol and abs(q["y"] - p["y"] - dy) <= pos_tol:
                    pairs.append((p, q))
                    used_b.add(i)
                    break
    offsets = [_num(q["value"], k, "mark") - _num(p["value"], k, "mark") for p, q in pairs]
    if len(pairs) < min_matches:
        status, offset = "UNKNOWN", None
    elif max(offsets) - min(offsets) <= TOL:
        status, offset = "DRAWING-CONFIRMED", round(sum(offsets) / len(offsets), 6)
    else:
        status, offset = "CONFLICT", None
    return {"matched": len(pairs), "unmatched_a": len(marks_a) - len(pairs), "unmatched_b": len(marks_b) - len(used_b),
            "offset": offset, "status": status, "translation": best[1],
            "pairs": [(p.get("ref"), q.get("ref"), p["text"]) for p, q in pairs]}


# ----------------------------------------------------------------------------------------------------- the check
def check(project):
    k = _scale(project.get("units"))
    base = project.get("base_system")
    if not base:
        raise ValueError("base_system is required")
    offsets = {base: (0.0, "VERIFIED", "base system")}
    for z in project.get("zero_relations", []):
        st = _status(z.get("status"), f"zero relation {z.get('system')}")
        _ref(z.get("ref"), f"zero relation {z.get('system')}")
        if st in RANK and z.get("offset") is not None:
            offsets[z["system"]] = (_num(z["offset"], k, "zero offset"), st, z["ref"])

    chains = {}
    for c in project.get("chains", []):
        fam = c.get("family")
        links = c.get("links") or TEMPLATES.get(fam)
        if not links:
            raise ValueError(f"chain {c.get('chain_id')}: unknown family {fam!r} and no links given")
        for u, lo, _ in links:
            category(u), category(lo)
        chains[c["chain_id"]] = {"chain": c, "links": [tuple(x) for x in links]}

    issues = []
    # ---- datums: consolidate per (chain, kind); bounds kept apart
    entries, bounds = {}, []
    for d in project.get("datums", []):
        cid, kind = d.get("chain_id"), d.get("kind")
        if cid not in chains:
            raise ValueError(f"datum on unknown chain {cid!r}")
        category(kind)
        what = f"datum {cid}/{kind}"
        st = _status(d.get("status"), what)
        ref = _ref(d.get("ref"), what)
        if d.get("bound") not in BOUNDS:
            raise ValueError(f"{what}: unknown bound {d.get('bound')!r}")
        v = _num(d.get("value"), k, what) if d.get("value") is not None else None
        system = d.get("system", base)
        if v is not None and system not in offsets:
            issues.append({"code": "ZERO_RELATION_UNKNOWN", "chain_id": cid, "kind": kind, "ref": ref,
                           "detail": f"system {system!r} has no established relation to {base!r}: value not combined"})
            continue
        if v is not None:
            off, zst, _ = offsets[system]
            v = v + off
            if system != base:
                st = _weakest([st, zst])
        if d.get("bound"):
            bounds.append({"chain_id": cid, "kind": kind, "bound": d["bound"], "value": v, "ref": ref,
                           "status": st})
            continue
        entries.setdefault((cid, kind), []).append({"value": v, "status": st, "ref": ref})

    known, conflicts = {}, set()
    datum_rows = []
    for key, es in entries.items():
        vals = [e for e in es if e["value"] is not None and e["status"] in RANK]
        refs = [e["ref"] for e in es]
        if not vals:
            datum_rows.append({"chain_id": key[0], "kind": key[1], "value": None, "status": "HELD",
                               "basis": "NOT_PRINTED", "refs": refs})
            continue
        lo_v, hi_v = min(e["value"] for e in vals), max(e["value"] for e in vals)
        if hi_v - lo_v > TOL:
            conflicts.add(key)
            datum_rows.append({"chain_id": key[0], "kind": key[1], "value": None, "status": "CONFLICT",
                               "basis": "PRINTED", "refs": refs,
                               "values": sorted({round(e["value"], 4) for e in vals})})
            issues.append({"code": "CONFLICT", "chain_id": key[0], "kind": key[1], "refs": refs,
                           "detail": "printed values " + " vs ".join(f"{e['value']:+.3f} ({e['ref']})" for e in vals)})
            continue
        st = _weakest([e["status"] for e in vals])
        known[key] = {"value": vals[0]["value"], "status": st, "basis": "PRINTED", "refs": refs}

    layers, manual = {}, []
    for ly in project.get("layers", []):
        cid, name = ly.get("chain_id"), ly.get("layer")
        if cid not in chains:
            raise ValueError(f"layer on unknown chain {cid!r}")
        what = f"layer {cid}/{name}"
        if ly.get("method", "DRAWING") not in METHODS:
            raise ValueError(f"{what}: unknown method {ly.get('method')!r}")
        if name not in {lk[2] for lk in chains[cid]["links"]}:
            raise ValueError(f"{what}: no link of this chain carries that layer")
        st = _status(ly.get("status"), what)
        ref = _ref(ly.get("ref"), what)
        t = _num(ly.get("thickness"), k, what) if ly.get("thickness") is not None else None
        if t is not None and t < 0:
            raise ValueError(f"{what}: negative thickness")
        row = {"chain_id": cid, "layer": name, "thickness": t, "status": st, "ref": ref}
        if ly.get("method", "DRAWING") == "OWNER_MANUAL":
            manual.append(dict(row, method="OWNER_MANUAL"))
            continue
        if t is None or st not in RANK:
            continue
        prev = layers.get((cid, name))
        if prev and abs(prev["thickness"] - t) > TOL:
            issues.append({"code": "CONFLICT", "chain_id": cid, "layer": name, "refs": [prev["ref"], ref],
                           "detail": f"layer printed {prev['thickness']:.3f} vs {t:.3f}"})
            layers[(cid, name)] = dict(prev, thickness=None, status="CONFLICT")
            continue
        layers[(cid, name)] = row

    # ---- derive along the links until nothing changes (each derivation names its basis)
    changed = True
    while changed:
        changed = False
        for cid, ch in chains.items():
            for u, lo, name in ch["links"]:
                ly = layers.get((cid, name))
                if not ly or ly.get("thickness") is None:
                    continue
                ku, kl = (cid, u), (cid, lo)
                if ku in conflicts or kl in conflicts:
                    continue
                if ku in known and kl not in known:
                    known[kl] = {"value": known[ku]["value"] - ly["thickness"],
                                 "status": _weakest([known[ku]["status"], ly["status"]]),
                                 "basis": f"DERIVED {u} - {name}", "refs": [ly["ref"]], "from": ku}
                    changed = True
                elif kl in known and ku not in known:
                    known[ku] = {"value": known[kl]["value"] + ly["thickness"],
                                 "status": _weakest([known[kl]["status"], ly["status"]]),
                                 "basis": f"DERIVED {lo} + {name}", "refs": [ly["ref"]], "from": kl}
                    changed = True
    # ---- links
    link_rows, mismatch_ends = [], set()
    for cid, ch in chains.items():
        for u, lo, name in ch["links"]:
            ku, kl = (cid, u), (cid, lo)
            ly = layers.get((cid, name))
            row = {"chain_id": cid, "upper": u, "lower": lo, "layer": name, "upper_value": None, "lower_value": None,
                   "thickness": None, "status": None, "missing": [], "detail": ""}
            if ku in conflicts or kl in conflicts or (ly and ly.get("status") == "CONFLICT"):
                row["status"] = "CONFLICT"
                row["detail"] = "a datum or the layer of this link is printed with two values"
                link_rows.append(row)
                continue
            if ku in known:
                row["upper_value"] = round(known[ku]["value"], 4)
            if kl in known:
                row["lower_value"] = round(known[kl]["value"], 4)
            if ku in known and kl in known:
                diff = known[ku]["value"] - known[kl]["value"]
                row["thickness"] = round(diff, 4)
                ins = [known[ku]["status"], known[kl]["status"]]
                if ly and ly.get("thickness") is not None:
                    ins.append(ly["status"])
                    if abs(diff - ly["thickness"]) > TOL:
                        row["status"] = "CONFLICT"
                        row["detail"] = (f"datums give {diff:.3f} m, the layer is printed {ly['thickness']:.3f} m "
                                         f"({ly['ref']})")
                        issues.append({"code": "LINK_MISMATCH", "chain_id": cid, "layer": name,
                                       "detail": row["detail"]})
                        mismatch_ends.update((ku, kl))
                        link_rows.append(row)
                        continue
                row["status"] = _weakest(ins)
                row["detail"] = "datums and layer agree" if ly and ly.get("thickness") is not None else \
                    "thickness from the two datums"
            else:
                miss = [f"{cid}/{x}" for x, kk in ((u, ku), (lo, kl)) if kk not in known]
                if not ly or ly.get("thickness") is None:
                    miss.append(f"{cid}/layer {name}")
                row["status"] = "HELD"
                row["missing"] = miss
                row["detail"] = "not printed: " + ", ".join(miss)
                issues.append({"code": "HELD_LINK", "chain_id": cid, "layer": name, "missing": miss})
            link_rows.append(row)

    # ---- a value DERIVED through a datum of a mismatching link is not established (CONFLICT, never kept)
    tainted, grew = {}, True
    while grew:
        grew = False
        for key, kv in list(known.items()):
            if kv.get("from") is not None and (kv["from"] in mismatch_ends or kv["from"] in tainted):
                tainted[key] = known.pop(key)
                conflicts.add(key)
                grew = True
    for row in link_rows:
        keys = {(row["chain_id"], row["upper"]), (row["chain_id"], row["lower"])}
        if row["status"] != "CONFLICT" and keys & set(tainted):
            row.update(status="CONFLICT", thickness=None, missing=[],
                       detail="depends on a value derived through a link whose printed datums and layer disagree")
    for key, kv in tainted.items():
        datum_rows.append({"chain_id": key[0], "kind": key[1], "value": None, "status": "CONFLICT",
                           "basis": kv["basis"] + " (through a mismatching link)", "refs": kv["refs"],
                           "values": [round(kv["value"], 4)]})
    for key, kv in known.items():
        datum_rows = [r for r in datum_rows if not (r["chain_id"] == key[0] and r["kind"] == key[1])]
        datum_rows.append({"chain_id": key[0], "kind": key[1], "value": round(kv["value"], 4),
                           "status": kv["status"], "basis": kv["basis"], "refs": kv["refs"]})
    issues = [i for i in issues if not (i["code"] == "HELD_LINK" and any(
        r["status"] == "CONFLICT" and r["chain_id"] == i["chain_id"] and r["layer"] == i["layer"] for r in link_rows))]

    # ---- bounds (printed limits): checked when the datum is known, never turned into a value
    for b in bounds:
        if _bound_result(b, known) == "VIOLATED":
            kv = known[(b["chain_id"], b["kind"])]
            issues.append({"code": "CONSTRAINT_VIOLATED", "chain_id": b["chain_id"], "kind": b["kind"],
                           "detail": f"{kv['value']:+.3f} vs {b['bound']} {b['value']:+.3f} ({b['ref']})"})
    use_rows = [_use(u, chains, known, conflicts, k) for u in project.get("uses", [])]
    for r in use_rows:
        if r["code"] != "OK":
            issues.append({"code": r["code"], "use_id": r["use_id"], "detail": r["detail"]})

    counts = {}
    for r in link_rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {"method": METHOD, "rules": RULES, "base_system": base, "zero_systems": sorted(offsets),
            "datums": sorted(datum_rows, key=lambda r: (r["chain_id"], KINDS.index(r["kind"]))),
            "links": link_rows, "owner_manual_layers": manual,
            "bounds": [dict(b, result=_bound_result(b, known)) for b in bounds],
            "uses": use_rows, "issues": issues,
            "summary": {"links": len(link_rows), "by_status": counts,
                        "issues": {c: sum(1 for i in issues if i["code"] == c) for c in CODES
                                   if any(i["code"] == c for i in issues)}}}


def _bound_result(b, known):
    kv = known.get((b["chain_id"], b["kind"]))
    if kv is None or b["value"] is None:
        return "OPEN (the datum is not established; the limit is not a value)"
    ok = kv["value"] <= b["value"] + TOL if b["bound"] == "AT_MOST" else kv["value"] >= b["value"] - TOL
    return "SATISFIED" if ok else "VIOLATED"


def _use(u, chains, known, conflicts, k):
    uid = u.get("use_id")
    _ref(u.get("ref"), f"use {uid}")
    cid, need = u.get("chain_id"), u.get("needs")
    if cid not in chains:
        raise ValueError(f"use {uid}: unknown chain {cid!r}")
    category(need)
    row = {"use_id": uid, "quantity": u.get("quantity"), "needs": f"{cid}/{need}", "code": "OK", "detail": "",
           "sensitivity": None, "ref": u["ref"]}
    need_kv = known.get((cid, need))
    need_val = None if need_kv is None else need_kv["value"]

    mf, mb = u.get("measured_from"), u.get("must_be_from")
    if mf or mb:
        if not (mf and mb):
            raise ValueError(f"use {uid}: measured_from and must_be_from go together")
        a, b = known.get((mf["chain_id"], mf["kind"])), known.get((mb["chain_id"], mb["kind"]))
        if (mf["chain_id"], mf["kind"]) != (mb["chain_id"], mb["kind"]):
            d = None if (a is None or b is None) else a["value"] - b["value"]
            row["code"] = "WRONG_REFERENCE"
            row["detail"] = (f"measured from {mf['chain_id']}/{mf['kind']} instead of {mb['chain_id']}/{mb['kind']}"
                             + ("" if d is None else f": every height read this way is off by {d:+.3f} m"))
            return row
        if b is None:
            row["code"] = "NEEDS_HELD"
            row["detail"] = f"reference {mb['chain_id']}/{mb['kind']} is not established"
        return row

    used = u.get("used") or {}
    if "kind" in used:
        ukey = (used.get("chain_id", cid), used["kind"])
        ucat, ncat = category(used["kind"]), category(need)
        if ukey == (cid, need):
            if (cid, need) in conflicts or need_kv is None:
                row["code"] = "NEEDS_HELD"
                row["detail"] = f"{cid}/{need} is " + ("in CONFLICT" if (cid, need) in conflicts else "HELD")
            return row
        uv = known.get(ukey)
        if ucat == "FINISHED" and ncat == "STRUCTURAL":
            row["code"] = "FINISHED_AS_STRUCTURAL"
        elif ucat == "STRUCTURAL" and ncat == "FINISHED":
            row["code"] = "STRUCTURAL_AS_FINISHED"
        else:
            row["code"] = "WRONG_REFERENCE"
        gap = None if (uv is None or need_val is None) else uv["value"] - need_val
        row["detail"] = (f"uses {ukey[0]}/{ukey[1]} where {cid}/{need} is needed; "
                         + ("the needed datum is not established (HELD): the quantity is HELD"
                            if need_val is None else f"difference {gap:+.3f} m"))
        mg = u.get("margin")
        if mg:
            up, down = _num(mg.get("up"), k, "margin up"), _num(mg.get("down"), k, "margin down")
            if gap is None:
                row["sensitivity"] = (f"quantity unchanged only if the needed datum lies within {down:.3f} m below to "
                                      f"{up:.3f} m above the used one; not established, so not proven")
            else:
                inside = -down - TOL <= -gap <= up + TOL
                row["sensitivity"] = ("difference inside the stated margin: quantity unchanged" if inside else
                                      "difference outside the stated margin: quantity changes")
        return row
    if "value" in used:
        v = _num(used["value"], k, f"use {uid}")
        if need_val is not None and abs(v - need_val) <= TOL:
            return row
        same = [key for key, kv in known.items() if abs(kv["value"] - v) <= TOL and key[0] == cid]
        if need_val is None and (cid, need) not in conflicts:
            row["code"] = "NEEDS_HELD" if not same else (
                "FINISHED_AS_STRUCTURAL" if category(same[0][1]) == "FINISHED" and category(need) == "STRUCTURAL"
                else "VALUE_NOT_FROM_DRAWINGS")
            row["detail"] = (f"value {v:+.3f} used for {cid}/{need}, which no sheet establishes"
                             + (f"; it equals {same[0][0]}/{same[0][1]}" if same else "") + ": the quantity is HELD")
            return row
        if (cid, need) in conflicts:
            row["code"] = "NEEDS_HELD"
            row["detail"] = f"{cid}/{need} is in CONFLICT"
            return row
        row["code"] = ("FINISHED_AS_STRUCTURAL" if same and category(same[0][1]) == "FINISHED"
                       and category(need) == "STRUCTURAL" else "VALUE_NOT_FROM_DRAWINGS")
        row["detail"] = f"value {v:+.3f} used, the drawings give {need_val:+.3f} for {cid}/{need}"
        return row
    raise ValueError(f"use {uid}: give used.kind, used.value or measured_from / must_be_from")
