"""T-428 rules: a reconciliation ROLL-UP r4 by SUB-TRACE. It restates single PARTS of an already merged roll-up (T-406
r3) with the traces of later Checker-MERGED tasks, keeps an ENGINE-SIDE register for engine errors the residual cannot
show, and prints a queued lane I correction only as a labelled SCENARIO beside the current table (pure, stdlib only;
every villa, every trade reconciliation).

R-T428-1  BASE is the merged roll-up as committed: per component its family and its current PARTS (cause, m3, verdict).
          It is read, never re-derived; the parts of every base component re-add to its current split within 1e-6.
R-T428-2  A SUB-TRACE restates exactly ONE base part (matched by component, cause text and m3, found exactly once) into
          sub-parts from a MERGED task; the sub-parts re-add to the part within 0.000002 m3 (a sub-trace never moves
          residual between parts, components or families) and a base part is sub-traced at most once. Refused: an
          unmerged source, a part not found or found twice, a part sub-traced twice, sub-parts that do not re-add.
R-T428-3  Class of a sub-part from its verdict (R-T406-3 carried) plus two verdicts the later Checker verdicts use:
          ENGINE_WRONG (TRACED: the cause is drawn and checked, the engine value is wrong by that m3; the sub-part names
          the task that owns the correction, or it is refused) and BOUNDED_THROUGH_SUPPORTS (TRACED: the mechanism is
          drawn and the m3 lies inside a drawn allowance; the sub-part states the allowance in m and the use in m, use
          <= allowance, or it is refused). Both are printed as their own sub-totals of TRACED, never hidden in it.
R-T428-4  CLASS FROM THE CHECKER VERDICT ONLY: a TRACED or HELD sub-part carries `verdict_ref`, the merged Checker verdict
          (task, merge, what the Checker re-measured) that gives that class; without it the sub-part may only be
          UNRESOLVED / UNTRACED (unexplained). A sub-part's own proposal never outranks the verdict (R-T406-8 carried).
R-T428-5  ENGINE-SIDE REGISTER: an engine value the Checker found wrong, or a value at one end of an unanswered printed
          range, where the comparison with the other side cannot show it (both sides on the same wrong basis, or the
          residual term already in a class), is listed apart with its line ids, m3 (VERIFIED_WRONG point or HELD range
          lo .. hi), source verdict and correction owner. It is never a residual part: its residual effect on the table
          as it stands is 0 and it never changes a total (refused otherwise); an item whose id is also a residual part
          is refused (no residual counted in two parts).
R-T428-6  SCENARIO: a correction from a task that is QUEUED / CLAIMED / READY (not merged) is printed only as a scenario
          column beside the current table, each move with its m3 and class (engine valued withdrawn into a held range =
          HELD; a corrected engine value with a checked cause = the residual change of that TRACED class; an
          ENGINE_WRONG sub-part removed by the correction leaves the table with it). A scenario from a merged task is
          refused (it is a candidate move, R-T406-6), and a scenario residual is always printed beside the as-is
          residual, never alone.
R-T428-7  Totals: per family and in total, bookkeeping closure (parts re-add to the residual) and cause closure
          (unexplained 0) printed apart, as in R-T406-7; every residual part is bound once (unique part ids; the sum of
          all parts equals the grand residual within 0.000005 m3).
"""
from __future__ import annotations

TOL_PART = 0.000002
TOL_COMP = 0.000001
TRACED = ("AGREE", "ENGINE_RIGHT", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "FREELANCER_ARITHMETIC", "SCOPE",
          "ENGINE_WRONG", "BOUNDED_THROUGH_SUPPORTS")
HELD = ("HELD",)
UNEXPLAINED = ("UNRESOLVED", "UNTRACED")
CLASS_OF = {**{v: "TRACED" for v in TRACED}, **{v: "HELD" for v in HELD}, **{v: "UNEXPLAINED" for v in UNEXPLAINED}}
RATIO_WORDS = ("%", "percent", "ratio", "factor", "scaled", "pro rata", "proportion")
SPLITS = ("TRACED", "HELD", "UNEXPLAINED")


class Refused(ValueError):
    """An input that would let an unverified figure, a held part as 0 or an untraced part as traced into the table."""


def r6(x):
    return round(float(x), 6) + 0.0


def part_class(part):
    v = part.get("verdict")
    if v not in CLASS_OF:
        raise Refused(f"part {part.get('cause')!r}: unknown verdict {v!r}")
    cls = CLASS_OF[v]
    text = str(part.get("cause") or "")
    if not text.strip():
        raise Refused("a part needs its physical cause stated")
    for w in RATIO_WORDS:
        if w in text.lower():
            raise Refused(f"a cause stated as a ratio / percentage is refused ({w!r}): {text!r}")
    m3 = part.get("m3")
    if not isinstance(m3, (int, float)) or isinstance(m3, bool):
        raise Refused(f"part {text!r}: m3 must be a number")
    if cls == "HELD" and abs(m3) < 0.0000005:
        raise Refused(f"part {text!r}: a HELD part of 0.000 m3 is refused (held is never 0)")
    if "counted_as" in part and part["counted_as"] != cls:
        raise Refused(f"part {text!r}: verdict {v} is {cls}, counted as {part['counted_as']} refused")
    return cls


def check_subpart(sp):
    cls = part_class(sp)
    if cls in ("TRACED", "HELD") and not str(sp.get("verdict_ref") or "").strip():
        raise Refused(f"sub-part {sp['cause']!r}: class {cls} needs the Checker verdict that gives it (R-T428-4)")
    if sp["verdict"] == "ENGINE_WRONG" and not str(sp.get("correction_owner") or "").strip():
        raise Refused(f"sub-part {sp['cause']!r}: ENGINE_WRONG names the task that owns the correction")
    if sp["verdict"] == "BOUNDED_THROUGH_SUPPORTS":
        a, u = sp.get("allowance_m"), sp.get("used_m")
        if not isinstance(a, (int, float)) or not isinstance(u, (int, float)) or u < 0 or u > a + 1e-9:
            raise Refused(f"sub-part {sp['cause']!r}: a bounded term states its drawn allowance and its use (use <= "
                          f"allowance), got {a!r} / {u!r}")
    return cls


def split_of(parts):
    out = {k: 0.0 for k in SPLITS}
    for p in parts:
        out[part_class(p)] += float(p["m3"])
    return {k: r6(v) for k, v in out.items()}


def check_base(base):
    seen = set()
    for c in base:
        if c["id"] in seen:
            raise Refused(f"component {c['id']} twice in the base")
        seen.add(c["id"])
        if c.get("parts"):
            s = split_of(c["parts"])
            for k in SPLITS:
                if abs(s[k] - c["current"][k]) > TOL_COMP:
                    raise Refused(f"base {c['id']}: parts give {k} {s[k]} != current {c['current'][k]}")


def apply_subtraces(base, subtraces, merged):
    """Return {component id: new part list}. Each sub-trace replaces exactly one base part."""
    check_base(base)
    by = {c["id"]: c for c in base}
    used = set()
    out = {}
    for st in subtraces:
        cid = st.get("component")
        if cid not in by:
            raise Refused(f"sub-trace of {cid!r}: not a component of the base")
        src = st.get("source")
        if src not in merged or not merged[src]:
            raise Refused(f"sub-trace of {cid} from {src!r}: not in the merged register (unverified figure refused)")
        parts = out.get(cid, [dict(p) for p in by[cid].get("parts") or []])
        hits = [i for i, p in enumerate(parts) if p["cause"] == st.get("part_cause")
                and abs(float(p["m3"]) - float(st.get("part_m3", 1e9))) <= 0.0000005 and not p.get("_sub")]
        key = (cid, st.get("part_cause"), r6(st.get("part_m3", 0)))
        if key in used:
            raise Refused(f"{cid}: part {st.get('part_cause')!r} sub-traced twice")
        if len(hits) != 1:
            raise Refused(f"{cid}: part {st.get('part_cause')!r} {st.get('part_m3')} found {len(hits)} times, not once")
        subs = st.get("subparts") or []
        if not subs:
            raise Refused(f"{cid}: a sub-trace needs sub-parts")
        for sp in subs:
            check_subpart(sp)
        tot = sum(float(sp["m3"]) for sp in subs)
        if abs(tot - float(st["part_m3"])) > TOL_PART:
            raise Refused(f"{cid}: sub-parts re-add to {tot:.6f}, not the part {st['part_m3']:.6f}: a sub-trace "
                          "restates a part, it never moves residual")
        used.add(key)
        i = hits[0]
        new = [dict(sp, _sub=True, source=src, source_commit=merged[src], replaces=st["part_cause"]) for sp in subs]
        out[cid] = parts[:i] + new + parts[i + 1:]
    return out


def subtotals(parts):
    s = split_of(parts)
    s["TRACED_of_which_ENGINE_WRONG"] = r6(sum(p["m3"] for p in parts if p["verdict"] == "ENGINE_WRONG"))
    s["TRACED_of_which_BOUNDED"] = r6(sum(p["m3"] for p in parts if p["verdict"] == "BOUNDED_THROUGH_SUPPORTS"))
    s["residual_m3"] = r6(s["TRACED"] + s["HELD"] + s["UNEXPLAINED"])
    return s


def rollup(base, families_base, subtraces, merged, engine_side=(), part_ids=None):
    """families_base: the merged roll-up's current family table. Returns (new parts per component, families, totals)."""
    newparts = apply_subtraces(base, subtraces, merged)
    by = {c["id"]: c for c in base}
    fams = {f: {k: float(v[k]) for k in SPLITS} for f, v in families_base.items()}
    for f, v in families_base.items():
        fams[f]["components"] = v["components"]
    for cid, parts in newparts.items():
        old, new = by[cid]["current"], split_of(parts)
        f = fams[by[cid]["family"]]
        for k in SPLITS:
            f[k] += new[k] - old[k]
    for f in fams.values():
        for k in SPLITS:
            f[k] = r6(f[k])
        f["residual_m3"] = r6(f["TRACED"] + f["HELD"] + f["UNEXPLAINED"])
        f["cause_closes"] = abs(f["UNEXPLAINED"]) <= 0.001
    old_total = sum(float(v[k]) for v in families_base.values() for k in SPLITS)
    totals = {k: r6(sum(f[k] for f in fams.values())) for k in SPLITS}
    totals["residual_m3"] = r6(sum(totals[k] for k in SPLITS))
    totals["families"] = len(fams)
    totals["families_cause_closing"] = sum(1 for f in fams.values() if f["cause_closes"])
    if abs(totals["residual_m3"] - old_total) > 0.000005:
        raise Refused("the sub-traces changed the grand residual (bookkeeping)")
    check_engine_side(engine_side, newparts, part_ids)
    return newparts, fams, totals


def check_engine_side(items, newparts, part_ids=None):
    ids = set(part_ids or ())
    for parts in newparts.values():
        ids |= {p.get("id") for p in parts if p.get("id")}
    seen = set()
    for it in items:
        if it.get("id") in ids:
            raise Refused(f"engine-side item {it.get('id')!r} is also a residual part (counted in two parts)")
        if it.get("id") in seen:
            raise Refused(f"engine-side item {it.get('id')!r} listed twice")
        seen.add(it.get("id"))
        if abs(float(it.get("residual_effect_m3", 1.0))) > 0.0000005:
            raise Refused(f"engine-side item {it.get('id')!r}: it never moves the residual as it stands")
        if not it.get("line_ids") or not str(it.get("verdict_ref") or "").strip():
            raise Refused(f"engine-side item {it.get('id')!r}: line ids and the Checker verdict are required")
        kind = it.get("kind")
        if kind == "VERIFIED_WRONG":
            if not isinstance(it.get("m3"), (int, float)) or abs(it["m3"]) < 0.0000005:
                raise Refused(f"engine-side item {it['id']}: a verified error states its m3")
        elif kind == "HELD_RANGE":
            lo, hi = it.get("range_m3") or (None, None)
            if not isinstance(lo, (int, float)) or not isinstance(hi, (int, float)) or hi < lo or hi <= 0:
                raise Refused(f"engine-side item {it['id']}: a held range states lo .. hi (never 0 .. 0)")
        else:
            raise Refused(f"engine-side item {it.get('id')!r}: kind {kind!r} unknown")
        if not str(it.get("correction_owner") or "").strip():
            raise Refused(f"engine-side item {it.get('id')!r}: names the task that owns the correction")


def scenario(asis_parts, moves, task, merged, status):
    """R-T428-6: a queued correction printed beside the as-is split, never alone. moves: list of
    {cause, m3 (residual change), verdict, removes (optional cause of an ENGINE_WRONG sub-part it removes)}."""
    if task in merged and merged[task]:
        raise Refused(f"{task} is merged: its effect is a candidate move (R-T406-6), not a scenario")
    if status not in ("QUEUED", "TODO", "CLAIMED", "READY"):
        raise Refused(f"{task}: scenario status {status!r} unknown")
    parts = [dict(p) for p in asis_parts]
    for mv in moves:
        if mv.get("removes") is not None:
            hit = [i for i, p in enumerate(parts) if p["cause"] == mv["removes"] and p["verdict"] == "ENGINE_WRONG"]
            if len(hit) != 1:
                raise Refused(f"scenario {task}: removes {mv['removes']!r} found {len(hit)} times among ENGINE_WRONG")
            if abs(float(parts[hit[0]]["m3"]) + float(mv["m3"])) > TOL_PART:
                raise Refused(f"scenario {task}: the removal {mv['m3']} does not cancel the ENGINE_WRONG part "
                              f"{parts[hit[0]]['m3']}")
            parts.pop(hit[0])
            continue
        part_class(mv)
        parts.append({"cause": f"[{task} scenario] {mv['cause']}", "m3": mv["m3"], "verdict": mv["verdict"]})
    return {"task": task, "status": status, "as_is": subtotals(asis_parts), "after": subtotals(parts),
            "parts_after": parts}
