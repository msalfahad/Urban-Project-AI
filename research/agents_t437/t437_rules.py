"""T-437 rules (pure, stdlib): the 'other unexplained concrete parts' of the r4 roll-up (pool walls, beam lengths,
boundary lengths) tested construction by construction (every villa).

R-T437-1  A FIGURE IS TRACED BY A CONSTRUCTION, NEVER BY THE NEAREST NUMBER. The other side's figure (a length, a
          height) is tested against every construction built from printed / drawn data only (levels, printed layer
          thicknesses, drawn edge lines by handle, support outlines). A construction reproduces it only within the
          tolerance of the precision he states (half a unit of his last digit, never tighter than 0.0005 m and never
          looser than 0.5 m). A construction that mixes two faces of one member (outer length less inner crossings,
          an outer run joined to an inner run) is refused as a physical construction and listed as such.
          Result: exactly one construction, or several that all give the same class -> TRACED (cause named, or
          'cause ambiguous' with every construction listed); several that give different classes -> UNRESOLVED
          (AMBIGUOUS); none -> UNRESOLVED with the nearest constructions and their misfits listed, never taken
          (construction_test).
R-T437-2  A LENGTH IS NEVER TAKEN THROUGH A SUPPORT TWICE. A through-support allowance on a beam run is bounded by the
          drawn room between the engine's valued length and the run's outermost drawn extent (outer faces of the end
          supports / carriers); a support the engine's valued length already contains (a beside-support piece, a run
          valued through a column) gives no further allowance. His length beyond the outermost drawn extent is
          untraced whatever the allowance says: that figure is a LOWER bound of the untraced part (through_bound).
R-T437-3  A ROW COUNT IS SETTLED BY BINDING ROWS TO LABELLED RUNS. His rows of one mark are bound one to one to the
          drawn, labelled runs of that mark by equal length (within his precision). A row left over is a COUNT
          difference only when its length cannot be absorbed by the mark's whole through-support room (R-T437-2);
          otherwise it stays a length question (count_binding).
R-T437-5  A DIFFERENCE INSIDE ONE STEP OF HIS PRINTING IS HIS STEP, NOT A CAUSE IN THE DRAWING. Where his printed length
          is short of the drawn face-to-face length by less than one step of the precision he prints (0.05 m printed
          as x.x5 / x.x0, 0.01 m as x.xx) and the mark has no other difference, the engine (= the drawn length) is
          right and the residual is named STEP (rounding / truncation of his row); a difference of one step or more,
          or his length LONGER than the drawn one, is never a step (within_step).
R-T437-4  A SUB-TRACE RESTATES ONE PART. Sub-parts re-add to their part within 0.000002 m3, carry a verdict from the
          T-428 list, a HELD sub-part is never 0, ENGINE_WRONG names its correction owner, and the part ids of this row
          are disjoint from every other row's part ids (check_split, disjoint).
"""

from __future__ import annotations

import itertools

TOL_PART = 0.000002
VERDICTS = ("AGREE", "ENGINE_RIGHT", "ENGINE_WRONG", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "HELD", "UNRESOLVED",
            "UNTRACED")


class RefusedT437(ValueError):
    pass


def r6(x):
    return round(float(x), 6) + 0.0


def precision_tol(figure_text):
    """Half a unit of the last digit he prints, bounded to [0.0005, 0.5] m. '42' -> 0.5, '71.7' -> 0.05."""
    s = str(figure_text).strip()
    if not s or s.lower() in ("none", "nan"):
        raise RefusedT437("precision: figure missing")
    if "e" in s.lower():
        raise RefusedT437("precision: exponent notation refused")
    dec = len(s.split(".")[1]) if "." in s else 0
    return min(0.5, max(0.0005, 0.5 * 10 ** (-dec)))


def within_step(*, engine_len, his_len, step):
    """R-T437-5. True when 0 <= engine - his < step (his printed step)."""
    if engine_len is None or his_len is None or not step:
        raise RefusedT437("step: a length or the step missing")
    d = r6(engine_len - his_len)
    return {"diff_m": d, "step_m": step, "is_step": 0.0 <= d < step - 1e-9}


def construction_test(target, constructions, *, tol, unit="m"):
    """R-T437-1. constructions: list of dicts {name, value, cls, mixed_faces (bool, default False)}."""
    if target is None:
        raise RefusedT437("construction test: target missing (never 0)")
    if unit != "m":
        raise RefusedT437(f"construction test: unit {unit!r} refused (metres only)")
    if not constructions:
        raise RefusedT437("construction test: no construction offered")
    rows, refused = [], []
    for c in constructions:
        if c.get("value") is None:
            raise RefusedT437(f"construction {c.get('name')!r}: value missing")
        mis = r6(float(target) - float(c["value"]))
        rec = {"name": c["name"], "value": r6(c["value"]), "misfit": mis, "cls": c.get("cls")}
        (refused if c.get("mixed_faces") else rows).append(rec)
    hits = [r for r in rows if abs(r["misfit"]) <= tol + 1e-9]
    near = sorted(rows, key=lambda r: abs(r["misfit"]))[:3]
    if not hits:
        return {"status": "UNRESOLVED", "why": "no construction within tolerance", "tol": tol, "nearest": near,
                "refused_mixed": refused}
    classes = {h["cls"] for h in hits}
    if len(classes) == 1 and None not in classes:
        return {"status": "TRACED", "cls": hits[0]["cls"], "cause_ambiguous": len(hits) > 1, "hits": hits,
                "tol": tol, "refused_mixed": refused}
    return {"status": "UNRESOLVED", "why": "AMBIGUOUS: constructions within tolerance give different classes",
            "hits": hits, "tol": tol, "refused_mixed": refused}


def through_bound(*, his_len, engine_len, outermost_len, support_in_engine_len=0.0, allowance_claimed=None):
    """R-T437-2. Returns the drawn through room, the untraced lower bound (m) and whether a claimed allowance
    over-reads the room (a length taken through a support already deducted / already valued)."""
    for k, v in (("his_len", his_len), ("engine_len", engine_len), ("outermost_len", outermost_len)):
        if v is None:
            raise RefusedT437(f"through bound: {k} missing")
    if outermost_len + 1e-9 < engine_len:
        raise RefusedT437("through bound: outermost drawn extent shorter than the engine's valued length")
    room = r6(outermost_len - engine_len - max(0.0, support_in_engine_len))
    if room < -1e-9:
        raise RefusedT437("through bound: support counted in the engine length exceeds the drawn room")
    room = max(0.0, room)
    excess = r6(his_len - engine_len)
    out = {"room_m": room, "excess_m": excess, "untraced_lower_bound_m": r6(max(0.0, excess - room))}
    if allowance_claimed is not None:
        out["allowance_over_room_m"] = r6(max(0.0, allowance_claimed - room))
    return out


def count_binding(his_rows, drawn_runs, *, through_room):
    """R-T437-3. his_rows: list of (length as he prints it, n); drawn_runs: lengths of the drawn, labelled runs of the
    mark. Each of his rows (longest first) takes the NEAREST drawn run within his precision (precision_tol)."""
    if any(L is None or n is None for L, n in his_rows) or any(L is None for L in drawn_runs):
        raise RefusedT437("count binding: a length or count missing")
    if any(n < 1 or int(n) != n for _, n in his_rows):
        raise RefusedT437("count binding: a row count must be a whole number >= 1")
    his = sorted([(float(L), precision_tol(L)) for L, n in his_rows for _ in range(int(n))], reverse=True)
    left = sorted([float(x) for x in drawn_runs], reverse=True)
    bound, spare = [], []
    for L, tol in his:
        cand = [(abs(L - d), i) for i, d in enumerate(left) if abs(L - d) <= tol + 1e-9]
        j = min(cand)[1] if cand else None
        if j is None:
            spare.append(L)
        else:
            bound.append((r6(L), r6(left.pop(j))))
    spare_len = r6(sum(spare))
    is_count = bool(spare) and not left and spare_len > through_room + 1e-9
    return {"bound": bound, "his_left_over": [r6(x) for x in spare], "drawn_left_over": [r6(x) for x in left],
            "left_over_m": spare_len, "through_room_m": r6(through_room),
            "class": "COUNT" if is_count else ("LENGTH" if spare or left else "AGREE")}


def check_split(part_m3, subparts):
    """R-T437-4. subparts: list of {id, m3, verdict, owner?}."""
    if part_m3 is None:
        raise RefusedT437("split: part figure missing")
    ids = [s["id"] for s in subparts]
    if len(ids) != len(set(ids)):
        raise RefusedT437("split: a sub-part id appears twice")
    for s in subparts:
        if s.get("verdict") not in VERDICTS:
            raise RefusedT437(f"split: verdict {s.get('verdict')!r} not in the T-428 list")
        if s.get("m3") is None:
            raise RefusedT437(f"split: {s['id']} has no figure (HELD is never 0, never blank)")
        if s["verdict"] == "HELD" and abs(s["m3"]) < 1e-12:
            raise RefusedT437(f"split: {s['id']} HELD at 0")
        if s["verdict"] == "ENGINE_WRONG" and not s.get("owner"):
            raise RefusedT437(f"split: {s['id']} ENGINE_WRONG without a correction owner")
    tot = sum(s["m3"] for s in subparts)
    if abs(tot - part_m3) > TOL_PART + 1e-9:
        raise RefusedT437(f"split: sub-parts {r6(tot)} do not re-add to the part {r6(part_m3)}")
    return r6(tot)


def disjoint(mine, others):
    """R-T437-4. mine: iterable of part ids / component names; others: {row: iterable}. Returns the clash map."""
    m = set(mine)
    clash = {row: sorted(m & set(ids)) for row, ids in others.items() if m & set(ids)}
    if clash:
        raise RefusedT437(f"disjointness: shared ids {clash}")
    return True


def subset_constructions(elements, target, *, tol, max_k=4):
    """Helper for R-T437-1 on a mark with several drawn pieces: every sum of at most one reading per piece within tol.
    elements: {piece: {reading: length}}. Returns the hits (list of (misfit, ((piece, reading), ...)))."""
    hits = []
    keys = list(elements)
    for k in range(1, min(max_k, len(keys)) + 1):
        for ks in itertools.combinations(keys, k):
            for alts in itertools.product(*[list(elements[x].items()) for x in ks]):
                s = sum(v for _, v in alts)
                if abs(s - target) <= tol + 1e-9:
                    hits.append((r6(target - s), tuple((x, a) for x, (a, _) in zip(ks, alts))))
    return sorted(hits, key=lambda h: abs(h[0]))

