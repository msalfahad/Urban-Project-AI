"""OPENING_CONSISTENCY_V1 (T-194, residential review R6): one opening, every source that shows it, compared attribute
by attribute: plan = elevation = section = schedule (and the project's opening list / census).

A pure CHECK: NOT wired into any method version (ARCH_TAKEOFF_V2.9 .. V3.0.x and route G are unchanged); it produces
issue rows and HELD causes, never a quantity. Standard library only; imports no engine module. Any villa.

Why (ENGINEERING_REASONING_STANDARD.md s.2, PROJECT_UNDERSTANDING_ASSESSMENT s.6 R6): an opening's width, sill, head
and type drive several BOQ lines at once (opening m2, masonry deduction, finish deductions, reveals, sills /
thresholds, lintels). When the plan, the elevations, the sections and a schedule disagree, or one of them is silent,
the line must not be measured from whichever source happens to be read first.

Inputs: observations (dicts), one per (opening, source):
  opening_id  the opening's id in the project's list, or None for an elevation feature still to be bound (see bind)
  source      PLAN | ELEVATION | SECTION | SCHEDULE | CENSUS (CENSUS = a derived opening list built by hand or by a
              tool when no schedule is issued: compared for completeness and values, never an authority over a sheet)
  ref         the sheet / page / view / layer reference (text; required)
  units       "m" or "mm" (required; nothing is guessed)
  kind        DOOR | WINDOW | OPENING (leafless / passage / arch) | GATE | OPEN_SIDE (not a building opening) | None
  width, width_basis   JAMB_TO_JAMB | PRINTED (a printed width; jamb to jamb unless the sheet says otherwise) |
              ARC_OUTER | ARC_FACE | PROJECTED_CHORD (an elevation's horizontal dimension of a plan-curved opening)
  chord_m     (PLAN of a curved opening only) the chord between the jamb ends on the face the elevation projects
  sill, head, level_basis   ABOVE_FFL | LEVEL (absolute level: needs `ffl`) | CHAIN_PART (a part of a printed chain:
              needs `chain_base`, the level the part starts from, and `ffl`)
  storey, facade, pos_m      (elevation binding) storey name, facade name, along-facade position of the centre in
              metres, measured left -> right as the elevation is drawn (for a PLAN record: as seen from outside)
  drawn       True when the source draws the opening (presence); False when it does not; values come only from
              PRINTED dimensions or CAD dimension entities, never from scaled geometry (printed note "not to scale")
  hidden      a reason text when the source cannot show it (section cut, occluded behind a nearer element); NOT_SHOWN
              with that reason, never DIFFERS

Outputs (check()):
  per opening: {attribute: {verdict, values, note}} for EXISTENCE, WIDTH, SILL, HEAD, KIND with verdict AGREES |
  DIFFERS | NOT_SHOWN | NOT_COMPARABLE; issue rows {id, code, detail, boq_lines}; held_causes per BOQ line.
  A value that only one source prints is SINGLE_SOURCE (NOT_SHOWN elsewhere): it is not a disagreement, but nothing
  independent confirms it; a head printed on no source is HEAD_NOT_PRINTED and holds every line that needs it.

Guards (ValueError, a wrong input never becomes a finding): units missing or not m / mm; a metre value above 20 m
(millimetres given as metres); an unknown source / basis / kind; an INFERRED value (a twin, a copy of a neighbour);
one opening twice from one ref; a LEVEL / CHAIN_PART without its datum.
"""

from __future__ import annotations

METHOD = "OPENING_CONSISTENCY_V1"
RULES = ("ENGINEERING_REASONING_STANDARD.md s.2 / s.3 (notation basis before arithmetic)",
         "UP-DOOR-HGT-001 (source order: schedule, section, elevation, dimension, fallback)",
         "UP-OPEN-SCHED-001 (no printed height: width kept, area HELD)", "printed note N09 (not to scale)",
         "WORKFLOW_CONTROLS s.5 (HELD never 0)")

SOURCES = ("PLAN", "ELEVATION", "SECTION", "SCHEDULE", "CENSUS")
KINDS = ("DOOR", "WINDOW", "OPENING", "GATE", "OPEN_SIDE")
WIDTH_BASES = ("JAMB_TO_JAMB", "PRINTED", "ARC_OUTER", "ARC_FACE", "PROJECTED_CHORD")
LEVEL_BASES = ("ABOVE_FFL", "LEVEL", "CHAIN_PART")
VERDICTS = ("AGREES", "DIFFERS", "NOT_SHOWN", "NOT_COMPARABLE")
ATTRS = ("EXISTENCE", "WIDTH", "SILL", "HEAD", "KIND")
MAX_M = 20.0          # one opening's width / sill / head
MAX_POS_M = 300.0     # an along-facade position (a villa facade is far shorter)
TOL_W = 0.01          # 1 cm: a printed "155" against a CAD 1552.3 mm agrees; 2 cm does not
TOL_H = 0.01
TOL_POS = 0.15        # binding tolerance for along-facade positions (identity only, never a quantity)

# Which BOQ lines a finding on one attribute touches (the same opening id feeds each line separately; T-175).
BOQ_LINES = {
    "EXISTENCE": ("OPENING_SUPPLY", "OPENING_M2", "BLOCK_DEDUCTION", "FINISH_DEDUCTION", "REVEAL_ML",
                  "SILL_OR_THRESHOLD_ML", "LINTEL"),
    "WIDTH": ("OPENING_M2", "BLOCK_DEDUCTION", "FINISH_DEDUCTION", "REVEAL_ML", "SILL_OR_THRESHOLD_ML", "LINTEL"),
    "SILL": ("OPENING_M2", "BLOCK_DEDUCTION", "FINISH_DEDUCTION", "REVEAL_ML"),
    "HEAD": ("OPENING_M2", "BLOCK_DEDUCTION", "FINISH_DEDUCTION", "REVEAL_ML", "LINTEL"),
    "KIND": ("OPENING_SUPPLY", "SILL_OR_THRESHOLD_ML", "REVEAL_ML"),
}


# ----------------------------------------------------------------------------------------------------------- input
def _metres(v, units, what, cap=MAX_M):
    if v is None or v == "":
        return None
    v = float(v)
    if units == "mm":
        v = v / 1000.0
    if abs(v) > cap:
        raise ValueError(f"{what} = {v} m is above {cap} m: millimetres given as metres? state units='mm'")
    return v


def normalise(obs):
    """One observation -> a checked record in metres, sill / head above the finished floor. Raises on bad input."""
    oid = obs.get("opening_id")
    src = obs.get("source")
    if src not in SOURCES:
        raise ValueError(f"{oid}: source {src!r} not in {SOURCES}")
    if not obs.get("ref"):
        raise ValueError(f"{oid} / {src}: every observation names its sheet / view (ref)")
    units = obs.get("units")
    if units not in ("m", "mm"):
        raise ValueError(f"{oid} / {src}: units must be 'm' or 'mm', got {units!r} (nothing is guessed)")
    if obs.get("inferred"):
        raise ValueError(f"{oid} / {src}: an INFERRED value (twin, neighbour, copy) is not a source")
    kind = obs.get("kind")
    if kind not in KINDS + (None, ""):
        raise ValueError(f"{oid}: kind {kind!r} not in {KINDS}")
    wb = obs.get("width_basis") or None
    width = _metres(obs.get("width"), units, f"{oid} / {src} width")
    if width is not None and wb not in WIDTH_BASES:
        raise ValueError(f"{oid} / {src}: a width needs its basis, one of {WIDTH_BASES}")
    rec = {"opening_id": oid or None, "source": src, "ref": obs["ref"], "kind": kind or None,
           "width": width, "width_basis": wb, "chord_m": _metres(obs.get("chord_m"), units, f"{oid} chord"),
           "storey": obs.get("storey"), "facade": obs.get("facade"),
           "pos_m": _metres(obs.get("pos_m"), units, f"{oid} position", MAX_POS_M),
           "drawn": obs.get("drawn", True) in (True, "1", "true", "True", "YES", "yes"),
           "hidden": obs.get("hidden") or None, "note": obs.get("note") or ""}
    raw = {}
    lb = obs.get("level_basis") or None
    for key in ("sill", "head"):
        v = _metres(obs.get(key), units, f"{oid} / {src} {key}")
        raw[key] = v
        if v is None:
            rec[key] = None
            continue
        if lb not in LEVEL_BASES:
            raise ValueError(f"{oid} / {src}: a {key} needs its level basis, one of {LEVEL_BASES}")
        if lb == "ABOVE_FFL":
            rec[key] = v
        else:
            ffl = _metres(obs.get("ffl"), units, f"{oid} ffl")
            if ffl is None:
                raise ValueError(f"{oid} / {src}: {lb} {key} needs the finished floor level (ffl)")
            if lb == "LEVEL":
                rec[key] = round(v - ffl, 6)
            else:
                base = _metres(obs.get("chain_base"), units, f"{oid} chain_base")
                if base is None:
                    raise ValueError(f"{oid} / {src}: CHAIN_PART {key} needs chain_base (the level the part starts)")
                rec[key] = round(base + v - ffl, 6)
    rec["level_basis"] = lb
    rec["raw"] = raw
    return rec


# --------------------------------------------------------------------------------------------------------- binding
WIDTH_BIND_M = 0.10   # identity only: wider apart = not the same opening; a smaller gap binds and is reported (DIFFERS)


def _width_ok(f, p):
    """Identity test only: when both sides state a straight width, they must be within WIDTH_BIND_M."""
    straight = ("JAMB_TO_JAMB", "PRINTED")
    if f.get("width") is None or p.get("width") is None:
        return True
    if f.get("width_basis") not in straight or p.get("width_basis") not in straight:
        return True
    return abs(f["width"] - p["width"]) <= WIDTH_BIND_M + 1e-9


def _kind_ok(f, p):
    return f.get("kind") and p.get("kind") and f["kind"] == p["kind"]


def _match(plan, feats, offset, sign, tol):
    """One-to-one binding for one orientation and offset: every (feature, opening) pair on the same storey within
    tol whose straight widths (when both are stated) are within WIDTH_BIND_M is a candidate; candidates are taken
    in the order (kind agrees first, then nearest). Returns (pairs, kind_matches, residual_sum)."""
    cand = []
    for f in feats:
        x = sign * f["pos_m"] + offset
        for p in plan:
            if p["storey"] != f["storey"]:
                continue
            d = abs(p["pos_m"] - x)
            if d <= tol and _width_ok(f, p):
                cand.append((0 if _kind_ok(f, p) else 1, d, id(f), p["opening_id"]))
    pairs, used, kinds, resid = {}, set(), 0, 0.0
    for miss, d, fid, pid in sorted(cand):
        if fid in pairs or pid in used:
            continue
        pairs[fid] = pid
        used.add(pid)
        kinds += 1 - miss
        resid += d
    return pairs, kinds, round(resid, 6)


AMBIGUITY_M = 0.01    # two bindings whose position residuals differ by less than this are not told apart


def bind(plan_records, elevation_features, declared_mirrored=None, tol=TOL_POS):
    """Bind unlabelled elevation features of ONE facade to plan openings by their relative positions.

    plan_records: PLAN records of that facade with opening_id, storey, pos_m (left -> right seen from outside).
    elevation_features: ELEVATION records with opening_id None, storey, pos_m (left -> right as drawn).
    Both orientations are tried (drawn as seen from outside, and mirrored), with every offset that lays one feature
    on one opening. Ranking: most features bound, then most kinds agreeing, then the smallest sum of position
    residuals. Two different bindings that tie on the first two and whose residuals differ by less than AMBIGUITY_M
    are AMBIGUOUS: nothing is bound (twins on a symmetric facade cannot be told apart by position). Positions are
    identity evidence only, never a quantity. Returns {mirrored, offset_m, bound: [(feature, id)], unbound_features,
    unmatched_plan, issues}."""
    plan = [p for p in plan_records if p.get("pos_m") is not None]
    feats = [f for f in elevation_features if f.get("pos_m") is not None]
    results = []
    for sign, mirrored in ((1.0, False), (-1.0, True)):
        seen = set()
        for f in feats:
            for p in plan:
                if p["storey"] != f["storey"]:
                    continue
                off = round(p["pos_m"] - sign * f["pos_m"], 4)
                if off in seen:
                    continue
                seen.add(off)
                pairs, kinds, resid = _match(plan, feats, off, sign, tol)
                key = tuple(sorted((f2["storey"], round(f2["pos_m"], 3), pid) for f2 in feats
                                   for pid in [pairs.get(id(f2))] if pid))
                results.append(((len(pairs), kinds), resid, mirrored, off, pairs, key))
    issues = []
    if not results:
        return {"mirrored": None, "bound": [], "unbound_features": feats, "unmatched_plan": plan,
                "issues": [("BINDING_NOT_POSSIBLE", "no position on one side")]}
    top = max(r[0] for r in results)
    best = sorted((r for r in results if r[0] == top), key=lambda r: r[1])
    rivals = {r[5] for r in best if r[1] - best[0][1] < AMBIGUITY_M}
    if top[0] == 0 or len(rivals) > 1:
        issues.append(("BINDING_AMBIGUOUS", f"{len(rivals)} different bindings fit {top[0]} features equally "
                                            "(symmetric facade or repeated openings): identities NOT bound"))
        return {"mirrored": None, "bound": [], "unbound_features": feats, "unmatched_plan": plan, "issues": issues}
    (n, _), _, mirrored, off, pairs, _ = best[0]
    if declared_mirrored is not None and declared_mirrored != mirrored:
        issues.append(("ORIENTATION_CONFLICT", f"declared mirrored={declared_mirrored} but only mirrored={mirrored} "
                                                f"binds {n} features"))
    if mirrored:
        issues.append(("MIRRORED_VIEW", "the elevation binds only when read mirrored (drawn as seen from inside "
                                         "or flipped): left / right identities follow the mirrored reading"))
    bound = [(f, pairs[id(f)]) for f in feats if id(f) in pairs]
    ids = {pid for _, pid in bound}
    return {"mirrored": mirrored, "offset_m": off, "bound": bound,
            "unbound_features": [f for f in feats if id(f) not in pairs],
            "unmatched_plan": [p for p in plan if p["opening_id"] not in ids], "issues": issues}


# ----------------------------------------------------------------------------------------------------------- check
def _cmp_values(vals, tol):
    """vals: [(source_ref, value)] of known values -> AGREES / DIFFERS (spread) or NOT_SHOWN / single."""
    known = [(r, v) for r, v in vals if v is not None]
    if not known:
        return "NOT_SHOWN", None
    lo, hi = min(v for _, v in known), max(v for _, v in known)
    if hi - lo <= tol + 1e-9:
        return "AGREES", round(hi - lo, 6)
    return "DIFFERS", round(hi - lo, 6)


def check_opening(oid, recs, tol_w=TOL_W, tol_h=TOL_H, lists_present=False):
    """All records of one opening -> attribute verdicts, issues and held causes. lists_present: the project has a
    schedule or an opening list, so an opening on the plan that is in neither is MISSING_FROM_LIST."""
    seen = set()
    for r in recs:
        k = (r["source"], r["ref"])
        if k in seen:
            raise ValueError(f"{oid}: two observations from one source / ref {k}: merge them first")
        seen.add(k)
    out = {"opening_id": oid, "attrs": {}, "issues": [], "held": {}}

    def issue(attr, code, detail):
        out["issues"].append({"opening_id": oid, "attr": attr, "code": code, "detail": detail,
                              "boq_lines": BOQ_LINES[attr]})

    def hold(attr, cause):
        for line in BOQ_LINES[attr]:
            out["held"].setdefault(line, []).append(cause)

    # EXISTENCE
    by_src = {}
    for r in recs:
        by_src.setdefault(r["source"], []).append(r)
    drawn = [r for r in recs if r["drawn"]]
    hidden = [r for r in recs if not r["drawn"] and r["hidden"]]
    absent = [r for r in recs if not r["drawn"] and not r["hidden"]]
    on_plan = any(r["drawn"] for r in by_src.get("PLAN", []))
    listed = any(r["drawn"] for r in by_src.get("SCHEDULE", []) + by_src.get("CENSUS", []))
    kinds = {r["kind"] for r in recs if r["kind"]}
    ex = "AGREES"
    if absent:
        ex = "DIFFERS"
        issue("EXISTENCE", "NOT_DRAWN_ON_SOURCE",
              "; ".join(f'{r["source"]} {r["ref"]} does not draw it (no occlusion / cut stated)' for r in absent))
        hold("EXISTENCE", f"{oid}: presence differs between sources")
    if not on_plan and drawn:
        ex = "DIFFERS"
        issue("EXISTENCE", "NOT_IN_PLAN", "shown on " + ", ".join(sorted({r["source"] for r in drawn})) +
              " but on no plan record: identity / scope to establish")
        hold("EXISTENCE", f"{oid}: not on the plan")
    if lists_present and on_plan and not listed and "OPEN_SIDE" not in kinds:
        ex = "DIFFERS"
        issue("EXISTENCE", "MISSING_FROM_LIST",
              "on the plan but in no schedule / opening list: every line that starts from the list misses it")
        hold("EXISTENCE", f"{oid}: missing from the opening list")
    out["attrs"]["EXISTENCE"] = {"verdict": ex, "drawn": [f'{r["source"]}:{r["ref"]}' for r in drawn],
                                 "hidden": [f'{r["source"]}:{r["ref"]} ({r["hidden"]})' for r in hidden]}

    def compare(attr, vals, tol, unit_txt):
        """vals: [(source, label, value)]. The verdict is taken over SHEET sources only (plan, elevation, section,
        schedule); a CENSUS value is derived, so it confirms nothing: it is checked against the sheets and a
        census value outside them is <ATTR>_LIST_DIFFERS (the list needs correcting; lines read from it are held)."""
        sheet = [(lab, x) for src, lab, x in vals if src != "CENSUS"]
        lst = [(lab, x) for src, lab, x in vals if src == "CENSUS"]
        v, spread = _cmp_values(sheet, tol)
        note = ""
        if v == "AGREES" and len(sheet) == 1:
            v, note = "NOT_COMPARABLE", f"SINGLE_SOURCE {sheet[0][0]} {sheet[0][1]:.3f}: nothing independent " \
                                        "confirms it"
        if v == "DIFFERS":
            issue(attr, f"{attr}_DIFFERS", ", ".join(f"{lab} {x:.3f}" for lab, x in sheet) +
                  f"{unit_txt} (spread {spread:.3f} m)")
            hold(attr, f"{oid}: {attr.lower()} differs between sheets")
        if sheet and lst:
            lo, hi = min(x for _, x in sheet), max(x for _, x in sheet)
            for lab, x in lst:
                if x < lo - tol - 1e-9 or x > hi + tol + 1e-9:
                    issue(attr, f"{attr}_LIST_DIFFERS", f"{lab} {x:.3f} against the sheets " +
                          ", ".join(f"{l2} {y:.3f}" for l2, y in sheet) + unit_txt)
                    hold(attr, f"{oid}: the opening list's {attr.lower()} differs from the sheets")
        if not sheet and lst:
            v = "NOT_SHOWN"
            note = "only the derived list states it: " + ", ".join(f"{lab} {x:.3f}" for lab, x in lst)
            issue(attr, f"{attr}_ONLY_IN_LIST", note)
            hold(attr, f"{oid}: {attr.lower()} only in the derived list")
        return v, note

    # WIDTH: per basis; bases are never compared with each other
    groups = {}
    for r in recs:
        lab = f'{r["source"]}:{r["ref"]}'
        if r["width"] is not None:
            b = "STRAIGHT" if r["width_basis"] in ("JAMB_TO_JAMB", "PRINTED") else r["width_basis"]
            groups.setdefault(b, []).append((r["source"], lab, r["width"]))
        if r["source"] == "PLAN" and r["chord_m"] is not None:
            groups.setdefault("PROJECTED_CHORD", []).append(("PLAN", lab + " (chord on the projected face)",
                                                             r["chord_m"]))
    if not groups:
        wv, notes = "NOT_SHOWN", ["no source prints a width"]
        issue("WIDTH", "WIDTH_NOT_PRINTED", "no source prints or dimensions the width")
        hold("WIDTH", f"{oid}: width not printed")
    else:
        per = {b: compare("WIDTH", vals, tol_w, " m") for b, vals in groups.items()}
        vs = [v for v, _ in per.values()]
        wv = "DIFFERS" if "DIFFERS" in vs else "AGREES" if "AGREES" in vs else \
            "NOT_COMPARABLE" if "NOT_COMPARABLE" in vs else "NOT_SHOWN"
        notes = [f"{b}: {v}{(' (' + n + ')') if n else ''}" for b, (v, n) in sorted(per.items())]
        if len(groups) > 1:
            notes.append("width bases kept apart, never compared with each other")
    out["attrs"]["WIDTH"] = {"verdict": wv, "values": {b: [(lab, x) for _, lab, x in vals]
                                                       for b, vals in groups.items()}, "note": "; ".join(notes)}

    # SILL and HEAD, above the finished floor after basis normalisation
    for attr, key in (("SILL", "sill"), ("HEAD", "head")):
        vals = [(r["source"], f'{r["source"]}:{r["ref"]}', r[key]) for r in recs if r[key] is not None]
        v, note = compare(attr, vals, tol_h, " above FFL")
        raws = {(r["level_basis"], r["raw"][key]) for r in recs if r["raw"].get(key) is not None}
        if len({b_ for b_, _ in raws}) > 1 and len({x for _, x in raws}) > 1 and v == "AGREES":
            issue(attr, f"{attr}_BASIS_MIXED", f"the sources state the {key} on different bases (" +
                  ", ".join(f"{b_} {x:.3f}" for b_, x in sorted(raws)) + "); they agree only after normalising to "
                  "the finished floor: a ledger column of raw values would mix bases")
        if v == "NOT_SHOWN" and not vals and key == "head" and "OPEN_SIDE" not in kinds:
            issue("HEAD", "HEAD_NOT_PRINTED", "no source prints a head / crown: area HELD (UP-OPEN-SCHED-001), "
                  "never 0, never a twin's or a neighbour's value")
            hold("HEAD", f"{oid}: head not printed")
        out["attrs"][attr] = {"verdict": v, "values": [(lab, x) for _, lab, x in vals], "note": note}

    # KIND (a drawn attribute: leaf / handle / glazing; the list's kind is checked against the sheets)
    sheet_k = {r["kind"] for r in recs if r["kind"] and r["source"] != "CENSUS"}
    list_k = {r["kind"] for r in recs if r["kind"] and r["source"] == "CENSUS"}
    n_sheet = len([r for r in recs if r["kind"] and r["source"] != "CENSUS"])
    kv = "NOT_SHOWN" if not sheet_k else "DIFFERS" if len(sheet_k) > 1 else \
        "AGREES" if n_sheet > 1 else "NOT_COMPARABLE"
    if kv == "DIFFERS":
        issue("KIND", "KIND_DIFFERS", ", ".join(f'{r["source"]}:{r["ref"]} {r["kind"]}' for r in recs
                                                if r["kind"] and r["source"] != "CENSUS"))
        hold("KIND", f"{oid}: type differs between sheets")
    if sheet_k and list_k and not list_k <= sheet_k:
        issue("KIND", "KIND_LIST_DIFFERS", f"list {sorted(list_k)} against the sheets {sorted(sheet_k)}")
        hold("KIND", f"{oid}: the list's type differs from the sheets")
    kinds = sheet_k | list_k
    out["attrs"]["KIND"] = {"verdict": kv, "values": sorted(kinds)}
    return out


def check(observations, tol_w=TOL_W, tol_h=TOL_H):
    """observations (already bound: every record carries an opening_id) -> {openings: [...], issues: [...],
    held: {line: [causes]}}. No quantity is produced."""
    recs = [normalise(o) for o in observations]
    unbound = [r for r in recs if not r["opening_id"]]
    if unbound:
        raise ValueError(f"{len(unbound)} observations carry no opening_id: bind() them first (or report them as "
                         "ELEVATION_ONLY)")
    by_id = {}
    for r in recs:
        by_id.setdefault(r["opening_id"], []).append(r)
    lists_present = any(r["source"] in ("SCHEDULE", "CENSUS") for r in recs)
    rows = [check_opening(i, rs, tol_w, tol_h, lists_present) for i, rs in sorted(by_id.items())]
    issues = [x for row in rows for x in row["issues"]]
    held = {}
    for row in rows:
        for line, causes in row["held"].items():
            held.setdefault(line, []).extend(causes)
    return {"method": METHOD, "openings": rows, "issues": issues, "held": held}


def elevation_only_issues(unbound_features):
    """Issue rows for elevation features that bind to no plan opening (an opening drawn on the elevation only)."""
    return [{"opening_id": None, "attr": "EXISTENCE", "code": "ELEVATION_ONLY",
             "detail": f'{f["source"]} {f["ref"]}: feature at {f["pos_m"]:.2f} m ({f.get("storey")}) binds to no '
                       "plan opening: NOT IN THE PLAN", "boq_lines": BOQ_LINES["EXISTENCE"]}
            for f in unbound_features]
