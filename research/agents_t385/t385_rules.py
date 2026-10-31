"""T-385 rules: a concrete reconciliation of a candidate against a freelancer's rows, family by family, component by
component (pure, stdlib only; every villa).

R-T385-1  A family's residual is (engine VALUED m3) - (freelancer row m3). It is split into COMPONENTS, each one physical
          element (or one population of identical elements) bound to the engine line ids that carry it and the freelancer
          sheet rows that carry it. Every candidate concrete line of the family is bound exactly once and every
          freelancer sub-row exactly once; a line or a row bound twice, or not bound, is refused.
R-T385-2  A component's contribution is (engine valued part) - (freelancer part). An engine part that is HELD (blank,
          BLOCKED_RFI, BOUNDED_EXPOSURE, a downgraded line) contributes 0 to the engine side and is reported as a HELD
          named item with its bound; it is NEVER counted as agreement and never written as an engine 0 quantity. A
          component whose engine side is wholly HELD has verdict HELD, whatever the freelancer figure.
R-T385-3  The sum of the contributions equals the family residual within 0.001 m3; anything else is an UNEXPLAINED
          remainder stated in m3. A freelancer row total that differs from the sum of his own sub-rows is a named cause
          (FREELANCER_ARITHMETIC) with its m3, never absorbed into another component.
R-T385-4  A cause is stated in physical terms (dimension, depth, count, scope, level band, wrong basis) with its m3 from
          the two quantities; a cause expressed as a ratio, a percentage or a scaling of the residual is refused.
R-T385-5  Verdict proposals per component: ENGINE_RIGHT (hand figure from the drawing given), FREELANCER_RIGHT,
          RULE_DIFFERENCE (both follow a rule; the rules differ: named), HELD (engine side open: named item),
          ENGINE_ONLY / FREELANCER_ONLY scope with their class, UNRESOLVED (named). AGREE only when both sides are valued
          and the contribution is within 0.001 m3.
R-T385-6  (r2, cause closure; Checker F-T385-1 / F-T385-2) Bookkeeping closure (every line and row bound once, the
          contributions sum to the residual) is NOT cause closure. A family's residual is split three ways:
          named_causes_m3 = only TRACED contributions (verdict AGREE / ENGINE_RIGHT / FREELANCER_RIGHT /
          RULE_DIFFERENCE, the FREELANCER_ARITHMETIC cause included); held_named_m3 = HELD components (own column);
          unexplained_m3 = residual - named - held, i.e. every UNRESOLVED contribution + the part of a traced component
          its cause split does not cover + any bookkeeping remainder. A traced component with several causes carries a
          cause_split (each cause physical, in m3); split short of the contribution prints the remainder as untraced.
          An UNRESOLVED or HELD component given a cause split (an untraced contribution counted as a named cause), or a
          typed traced / unexplained figure, is refused.
"""

from __future__ import annotations

TOL = 0.001          # m3, the acceptance tolerance of the family closure
QTY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
VERDICTS = ("AGREE", "ENGINE_RIGHT", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "HELD", "UNRESOLVED")
CAUSE_CLASSES = ("DIMENSION", "DEPTH", "COUNT", "SCOPE", "LEVEL_BAND", "WRONG_BASIS", "HELD_ITEM",
                 "FREELANCER_ARITHMETIC", "CLASSIFICATION", "AGREE")
RATIO_WORDS = ("%", "percent", "ratio", "factor", "scaled", "pro rata", "proportion")
TRACED_VERDICTS = ("AGREE", "ENGINE_RIGHT", "FREELANCER_RIGHT", "RULE_DIFFERENCE")
SPLIT_CLASSES = tuple(c for c in CAUSE_CLASSES if c not in ("HELD_ITEM", "AGREE"))
TYPED_CLOSURE_KEYS = ("traced_m3", "named_causes_m3", "unexplained_m3", "untraced_m3", "held_named_m3")


class Refused(ValueError):
    """An input that would hide a held quantity as 0, double count, or close a residual by a ratio."""


def r6(x):
    return None if x is None else round(float(x), 6) + 0.0


def line_class(line, downgraded_ids=()):
    """('VALUED', qty) / ('HELD', (low, high) or None) / ('EXCLUDED', None) for one candidate line (contractual view:
    a line under a downgrade record is HELD, its engine figure kept for audit only)."""
    ev = line.get("evidence_state")
    net = line.get("measured_net")
    if ev in ("NOT_APPLICABLE_WITH_EVIDENCE", "EXCLUDED_WITH_REASON"):
        return "EXCLUDED", None
    bound = None
    lo, hi = line.get("bounded_low"), line.get("bounded_high")
    if lo is None and isinstance(line.get("bounded_range"), dict):
        lo, hi = line["bounded_range"].get("low"), line["bounded_range"].get("high")
    if lo is not None and hi is not None:
        bound = (float(lo), float(hi))
    if line.get("line_id") in set(downgraded_ids):
        # a downgraded line's own range rests on the basis the record found unsupported: it is no bound (R-T385-2)
        return "HELD", None
    if ev in QTY_STATES and net is not None:
        return "VALUED", float(net)
    return "HELD", bound


def check_cause_text(text):
    t = (text or "").lower()
    if not t.strip():
        raise Refused("a component needs its physical cause stated")
    for w in RATIO_WORDS:
        if w in t:
            raise Refused(f"a cause stated as a ratio / percentage is refused ({w!r}): {text!r}")


def component(comp, lines_by_id, fl_rows, downgraded_ids=()):
    """One component: {'id', 'engine_lines': [...], 'freelancer_rows': [...], 'cause_class', 'cause', 'verdict', ...}.
    Returns the computed row."""
    cid = comp["id"]
    check_cause_text(comp.get("cause"))
    if comp.get("cause_class") not in CAUSE_CLASSES:
        raise Refused(f"{cid}: unknown cause class {comp.get('cause_class')!r}")
    if comp.get("verdict") not in VERDICTS:
        raise Refused(f"{cid}: unknown verdict {comp.get('verdict')!r}")
    if "engine_m3" in comp or "contribution_m3" in comp:
        raise Refused(f"{cid}: engine m3 and contribution are computed from the lines, never typed in")
    valued, held_n, held_lo, held_hi, held_unbounded, audit = 0.0, 0, 0.0, 0.0, 0, 0.0
    for lid in comp.get("engine_lines", []):
        if lid not in lines_by_id:
            raise Refused(f"{cid}: line {lid} is not in the candidate")
        ln = lines_by_id[lid]
        cls, v = line_class(ln, downgraded_ids)
        if cls == "VALUED":
            valued += v
        elif cls == "HELD":
            held_n += 1
            if ln.get("measured_net") is not None:
                audit += float(ln["measured_net"])
            if v is None:
                held_unbounded += 1
            else:
                held_lo += v[0]
                held_hi += v[1]
    fl = 0.0
    for ref in comp.get("freelancer_rows", []):
        if ref not in fl_rows:
            raise Refused(f"{cid}: freelancer row {ref} unknown")
        fl += float(fl_rows[ref])
    fl += float(comp.get("freelancer_arithmetic_m3", 0.0))
    contrib = valued - fl
    n_valued = len(comp.get("engine_lines", [])) - held_n
    verdict = comp["verdict"]
    if held_n and n_valued == 0 and comp.get("engine_lines"):
        if verdict != "HELD":
            raise Refused(f"{cid}: the engine side is wholly HELD: verdict must be HELD, not {verdict}")
    if verdict == "AGREE":
        if held_n:
            raise Refused(f"{cid}: a component with a HELD part can never be AGREE (held is not agreement)")
        if abs(contrib) > TOL:
            raise Refused(f"{cid}: AGREE with a contribution of {contrib:.6f} m3")
    if verdict == "HELD" and not held_n:
        raise Refused(f"{cid}: verdict HELD with no held engine line")
    # R-T385-6 cause closure
    for k in TYPED_CLOSURE_KEYS:
        if k in comp:
            raise Refused(f"{cid}: {k} is computed from the contribution and the cause split, never typed in")
    split = comp.get("cause_split")
    if split is not None and verdict not in TRACED_VERDICTS:
        raise Refused(f"{cid}: a {verdict} contribution is untraced: it cannot carry named causes (cause_split)")
    traced = held_named = unexplained = 0.0
    split_txt = ""
    if verdict in TRACED_VERDICTS:
        if split:
            for s in split:
                check_cause_text(s.get("cause"))
                if s.get("cause_class") not in SPLIT_CLASSES:
                    raise Refused(f"{cid}: unknown split cause class {s.get('cause_class')!r}")
                if not isinstance(s.get("m3"), (int, float)) or isinstance(s.get("m3"), bool):
                    raise Refused(f"{cid}: every split cause needs its m3")
            traced = sum(float(s["m3"]) for s in split)
            split_txt = "; ".join(f"{s['cause_class']} {r6(s['m3']):.6f}: {s['cause']}" for s in split)
        elif split is not None:
            raise Refused(f"{cid}: an empty cause split names no cause")
        else:
            traced = contrib                  # one stated cause covers the whole contribution
        unexplained = contrib - traced
    elif verdict == "HELD":
        held_named = contrib
    else:                                     # UNRESOLVED: named and bound, not traced
        unexplained = contrib
    return {"id": cid, "family": comp["family"], "element": comp.get("element", ""),
            "engine_lines": len(comp.get("engine_lines", [])), "engine_valued_m3": r6(valued),
            "held_lines": held_n, "held_low_m3": r6(held_lo) if held_n > held_unbounded else None,
            "held_high_m3": r6(held_hi) if held_n and not held_unbounded else None,
            "held_unbounded_lines": held_unbounded, "held_audit_engine_m3": r6(audit) if held_n else None,
            "freelancer_rows": ";".join(comp.get("freelancer_rows", [])), "freelancer_m3": r6(fl),
            "contribution_m3": r6(contrib), "traced_m3": r6(traced), "held_named_m3": r6(held_named),
            "unexplained_m3": r6(unexplained), "cause_split": split_txt,
            "cause_class": comp["cause_class"], "cause": comp["cause"],
            "verdict": verdict, "evidence": comp.get("evidence", "")}


def family(fam, comps, family_lines, lines_by_id, fl_rows, fl_family_total, downgraded_ids=()):
    """Closure of one family: every line once, every freelancer row once, contributions sum to the residual."""
    seen_l, seen_r = {}, {}
    rows = []
    for c in comps:
        for lid in c.get("engine_lines", []):
            if lid in seen_l:
                raise Refused(f"line {lid} bound twice ({seen_l[lid]} and {c['id']})")
            seen_l[lid] = c["id"]
        for ref in c.get("freelancer_rows", []):
            if ref in seen_r:
                raise Refused(f"freelancer row {ref} bound twice ({seen_r[ref]} and {c['id']})")
            seen_r[ref] = c["id"]
        rows.append(component(c, lines_by_id, fl_rows, downgraded_ids))
    missing = sorted(set(family_lines) - set(seen_l))
    if missing:
        raise Refused(f"{fam}: {len(missing)} candidate line(s) bound to no component, e.g. {missing[:3]}")
    extra = sorted(set(seen_l) - set(family_lines))
    if extra:
        raise Refused(f"{fam}: line(s) of another family bound here, e.g. {extra[:3]}")
    valued = sum(r["engine_valued_m3"] for r in rows)
    residual = valued - float(fl_family_total)
    bound_sum = sum(r["contribution_m3"] for r in rows)
    bookkeeping = residual - bound_sum                       # a missing line / row or a sub-total slip
    named = sum(r["traced_m3"] for r in rows)
    held_named = sum(r["held_named_m3"] for r in rows)
    unexplained = residual - named - held_named              # UNRESOLVED + untraced remainders + bookkeeping
    held_lo = sum(r["held_low_m3"] or 0.0 for r in rows)      # bounded held lines only; unbounded ones counted apart
    held_hi_ok = all(r["held_high_m3"] is not None for r in rows if r["held_lines"])
    held_hi = sum(r["held_high_m3"] or 0.0 for r in rows) if held_hi_ok else None
    return rows, {"family": fam, "engine_valued_m3": r6(valued),
                  "held_lines": sum(r["held_lines"] for r in rows),
                  "held_low_m3": r6(held_lo), "held_high_m3": r6(held_hi),
                  "held_unbounded_lines": sum(r["held_unbounded_lines"] for r in rows),
                  "freelancer_m3": r6(fl_family_total), "residual_m3": r6(residual),
                  "named_causes_m3": r6(named), "held_named_m3": r6(held_named), "unexplained_m3": r6(unexplained),
                  "unresolved_m3": r6(sum(r["unexplained_m3"] for r in rows if r["verdict"] == "UNRESOLVED")),
                  "untraced_remainder_m3": r6(sum(r["unexplained_m3"] for r in rows if r["verdict"] in TRACED_VERDICTS)),
                  "bookkeeping_remainder_m3": r6(bookkeeping),
                  "bookkeeping_closes": abs(bookkeeping) <= TOL, "cause_closes": abs(unexplained) <= TOL}
