"""T-406 rules: a reconciliation ROLL-UP. It restates an earlier per-component cause closure (T-385 r2) with the
traces of later, Checker-MERGED tasks, component by component, and prints one current table per family (pure, stdlib
only; every villa, every trade reconciliation).

R-T406-1  BEFORE is the earlier closure as merged: per component its family, verdict and contribution (engine valued -
          freelancer, m3) with its traced / held / unexplained split (T-385 R-T385-6). It is read, never re-derived.
R-T406-2  A component is restated only by a TRACE of a MERGED task: the trace names its source task, and the task must
          be in the merged register (task -> merge commit) given to the roll-up. A trace from a task that is not merged
          (READY, CLAIMED, REJECTED) is refused: an unverified figure never enters the board table.
R-T406-3  A trace is a list of PARTS, each (cause, m3, verdict). The class of a part follows from its verdict only:
          TRACED for AGREE / ENGINE_RIGHT / FREELANCER_RIGHT / RULE_DIFFERENCE / FREELANCER_ARITHMETIC / SCOPE (a named
          scope move to another family, its counterpart named), HELD for HELD, UNEXPLAINED for UNRESOLVED and UNTRACED
          (the untraced remainder of a traced term). A part that states its own class and states one that differs from
          its verdict (an UNRESOLVED or HELD part counted as traced) is refused. A HELD part of 0.000 m3 is refused (a
          held item is never written as 0). A cause stated as a ratio / percentage / scaling is refused.
R-T406-4  The parts of a trace re-add to the component's BEFORE contribution within 0.001 m3, or the trace is refused:
          a trace restates the same residual, it never moves residual between components or families silently. A
          change of the residual itself is a CANDIDATE MOVE (R-T406-6), never a trace.
R-T406-5  A component may be moved to another family row (its own family row for an element several freelancer
          families share); the move is printed, and the grand totals are unchanged by it.
R-T406-6  A CANDIDATE MOVE (a later candidate version changed the engine side) is stated apart, per component, with its
          source (a merged Gate B verdict), its m3 and its class: engine valued m3 withdrawn into a held range is HELD
          (the withheld engine quantity); a valued change with its verified cause is TRACED. The roll-up prints the
          table on the earlier candidate (traces only) and on the current candidate (traces + moves) side by side.
R-T406-7  Per family and in total, BOOKKEEPING closure (every component bound once, the parts re-add to the residual)
          and CAUSE closure (unexplained 0.000 m3) are printed apart; held is its own column, never counted as
          agreement and never as 0; unexplained is never closed by its sign.
"""

from __future__ import annotations

TOL = 0.001
TRACED = ("AGREE", "ENGINE_RIGHT", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "FREELANCER_ARITHMETIC", "SCOPE")
HELD = ("HELD",)
UNEXPLAINED = ("UNRESOLVED", "UNTRACED")
CLASS_OF = {**{v: "TRACED" for v in TRACED}, **{v: "HELD" for v in HELD}, **{v: "UNEXPLAINED" for v in UNEXPLAINED}}
RATIO_WORDS = ("%", "percent", "ratio", "factor", "scaled", "pro rata", "proportion")
BEFORE_KEYS = ("id", "family", "verdict", "contribution_m3", "traced_m3", "held_m3", "unexplained_m3")


class Refused(ValueError):
    """An input that would let an unverified figure, a held part as 0 or an untraced part as traced into the table."""


def r6(x):
    return round(float(x), 6) + 0.0


def part_class(part):
    v = part.get("verdict")
    if v not in CLASS_OF:
        raise Refused(f"part {part.get('cause')!r}: unknown verdict {v!r}")
    cls = CLASS_OF[v]
    if "counted_as" in part and part["counted_as"] != cls:
        raise Refused(f"part {part.get('cause')!r}: verdict {v} is {cls}, counted as {part['counted_as']} refused")
    text = str(part.get("cause") or "").lower()
    if not text.strip():
        raise Refused("a part needs its physical cause stated")
    for w in RATIO_WORDS:
        if w in text:
            raise Refused(f"a cause stated as a ratio / percentage is refused ({w!r}): {part['cause']!r}")
    m3 = part.get("m3")
    if not isinstance(m3, (int, float)) or isinstance(m3, bool):
        raise Refused(f"part {part['cause']!r}: m3 must be a number")
    if cls == "HELD" and abs(m3) < 0.0000005:
        raise Refused(f"part {part['cause']!r}: a HELD part of 0.000 m3 is refused (held is never 0)")
    return cls


def split_of(parts):
    out = {"TRACED": 0.0, "HELD": 0.0, "UNEXPLAINED": 0.0}
    for p in parts:
        out[part_class(p)] += float(p["m3"])
    return {k: r6(v) for k, v in out.items()}


def check_before(before):
    seen = set()
    for c in before:
        for k in BEFORE_KEYS:
            if k not in c:
                raise Refused(f"before component missing {k}")
        if c["id"] in seen:
            raise Refused(f"component {c['id']} twice in the before table")
        seen.add(c["id"])
        s = c["traced_m3"] + c["held_m3"] + c["unexplained_m3"]
        if abs(s - c["contribution_m3"]) > TOL:
            raise Refused(f"before {c['id']}: split {s:.6f} != contribution {c['contribution_m3']:.6f}")


def check_trace(comp, trace, merged):
    src = trace.get("source")
    if src not in merged or not merged[src]:
        raise Refused(f"trace of {comp['id']} from {src!r}: not in the merged register (unverified figure refused)")
    parts = trace.get("parts") or []
    if not parts:
        raise Refused(f"trace of {comp['id']}: no parts")
    s = split_of(parts)
    total = s["TRACED"] + s["HELD"] + s["UNEXPLAINED"]
    if abs(total - comp["contribution_m3"]) > TOL:
        raise Refused(f"trace of {comp['id']} re-adds to {total:.6f}, not its contribution "
                      f"{comp['contribution_m3']:.6f}: a trace restates the residual, it never moves it")
    return s


def check_move(comp, move, merged):
    src = move.get("source")
    if src not in merged or not merged[src]:
        raise Refused(f"candidate move of {comp['id']} from {src!r}: not in the merged register")
    return split_of(move.get("parts") or [])


def rollup(before, traces, merged, family_moves=None, candidate_moves=None):
    """Return (components, families_before, families_after_traces, families_after_moves, totals)."""
    check_before(before)
    ids = {c["id"] for c in before}
    for k in list(traces) + list(family_moves or {}) + list(candidate_moves or {}):
        if k not in ids:
            raise Refused(f"{k}: not a component of the before table")
    rows = []
    for c in before:
        bsplit = {"TRACED": c["traced_m3"], "HELD": c["held_m3"], "UNEXPLAINED": c["unexplained_m3"]}
        t = traces.get(c["id"])
        asplit = check_trace(c, t, merged) if t else dict(bsplit)
        mv = (candidate_moves or {}).get(c["id"])
        msplit = check_move(c, mv, merged) if mv else {"TRACED": 0.0, "HELD": 0.0, "UNEXPLAINED": 0.0}
        rows.append({
            "id": c["id"], "family_before": c["family"], "family_after": (family_moves or {}).get(c["id"], c["family"]),
            "verdict_before": c["verdict"], "contribution_m3": r6(c["contribution_m3"]),
            "before": {k: r6(v) for k, v in bsplit.items()},
            "after": {k: r6(v) for k, v in asplit.items()},
            "trace_source": (t or {}).get("source"), "trace_commit": merged.get((t or {}).get("source")),
            "parts": (t or {}).get("parts", []),
            "move": {k: r6(v) for k, v in msplit.items()}, "move_source": (mv or {}).get("source"),
            "move_parts": (mv or {}).get("parts", []),
            "current": {k: r6(asplit[k] + msplit[k]) for k in asplit},
        })
    def fam(key_family, key_split):
        out = {}
        for r in rows:
            f = out.setdefault(r[key_family], {"components": 0, "residual_m3": 0.0, "TRACED": 0.0, "HELD": 0.0,
                                               "UNEXPLAINED": 0.0})
            f["components"] += 1
            for k in ("TRACED", "HELD", "UNEXPLAINED"):
                f[k] += r[key_split][k]
                f["residual_m3"] += r[key_split][k]
        for f in out.values():
            for k in ("residual_m3", "TRACED", "HELD", "UNEXPLAINED"):
                f[k] = r6(f[k])
            f["bookkeeping_closes"] = abs(f["TRACED"] + f["HELD"] + f["UNEXPLAINED"] - f["residual_m3"]) <= TOL
            f["cause_closes"] = abs(f["UNEXPLAINED"]) <= TOL
        return out
    fb, fa, fc = fam("family_before", "before"), fam("family_after", "after"), fam("family_after", "current")
    def tot(fs):
        t = {k: r6(sum(f[k] for f in fs.values())) for k in ("residual_m3", "TRACED", "HELD", "UNEXPLAINED")}
        t["families_cause_closing"] = sum(1 for f in fs.values() if f["cause_closes"])
        t["families"] = len(fs)
        return t
    totals = {"before": tot(fb), "after_traces": tot(fa), "current": tot(fc)}
    if abs(totals["before"]["residual_m3"] - totals["after_traces"]["residual_m3"]) > TOL:
        raise Refused("traces changed the total residual (bookkeeping)")
    return rows, fb, fa, fc, totals
