"""T-679 rules (project-agnostic; scope: any candidate line index URBAN_T479_LINE_INDEX_V1 of any villa). Research only,
unwired: reads committed files, computes no quantity of any element, changes no line.

R-T679-1 1.0.0  CONCRETE RECONCILIATION STATEMENT: component -> line -> family subtotal -> trade total, reference apart.
    Provenance: owner 2026-11-08 12:40 (5) prove the aggregation per trade, (7) keep the reference comparison apart;
    T-469 / T-479 line class and verdict binding (RELEASED / HELD / EXCLUDED; VERIFIED_WHOLE / VERIFIED_COMPONENT);
    R-T613-1 (f) (g) (h) (HELD never 0, no % beside HELD, exact re-add); T-653 (local Decimal context only).
    (a) Every line of the trade (item code prefix) is in exactly one family (the registry family that owns its item
        code); an item code owned by no family or by two families is REFUSED (never dropped, never split).
    (b) Per family and unit, four buckets that are NEVER summed together:
          RELEASED  n, exact Decimal sum of measured_net (the repr of the stored number, no rounding);
          HELD BOUNDED  n, low sum .. high sum (both numeric, low <= high, else REFUSED);
          HELD BLANK  n, by census cause class (no quantity; high OPEN);
          EXCLUDED  n (NOT_APPLICABLE_WITH_EVIDENCE / EXCLUDED_WITH_REASON: the index does not split the two).
        A RELEASED line without a number, a HELD line with a number in measured_net, a line with one bound only, a
        unit other than the trade unit, or a HELD line with no cause is REFUSED.
    (c) Trade total = the exact sum of the family subtotals bucket by bucket (and, independently, of the lines): the
        released total, the bounded low .. high total and the blank count are printed side by side; the "engine range"
        of a scope is released + bounded low .. released + bounded high, and its high is OPEN when any blank line is
        in the scope. HELD is never 0 and never added to the released figure.
    (d) Verified share: per scope, n VERIFIED_WHOLE and n VERIFIED_COMPONENT lines (and their sums) over d = released
        + held lines; the two verified classes are never summed and a held or excluded line is never verified.
    (e) Reference comparison APART: per key of the project key map (an item code answers at most one key, else
        REFUSED), the reference quantity, the engine released sum and range of the key's item codes, and
        difference = reference - engine released (R-T613-1 (h) sign). The % of reference is printed ONLY when the key
        holds no HELD line; otherwise it is suppressed with its reason (R-T613-1 (g)). A reference value is never
        used as a quantity; agreement is never proof and no accuracy figure is computed.
    (f) Causes of the difference are quoted from merged verdict sections only (class -> m3, with the section id and
        the candidate it was scored on); a key with no merged section says so (UNRESOLVED, no section); nothing is
        re-classified here.
"""
from __future__ import annotations

from collections import OrderedDict
from decimal import Context, Decimal, localcontext

CTX = Context(prec=40)
RELEASED, HELD, EXCLUDED = "RELEASED", "HELD", "EXCLUDED"
VERIFIED_WHOLE, VERIFIED_COMPONENT = "VERIFIED_WHOLE", "VERIFIED_COMPONENT"
CAUSE_CLASSES = ("DESIGNER ITEM", "OPEN BOUND", "MEASURABLE NOW")
OPEN = "OPEN"


class Refused(ValueError):
    pass


def D(x) -> Decimal:
    """Exact decimal of a stored number: the repr of a float, never a binary expansion, never rounded."""
    if x is None:
        raise Refused("D(None): a missing value is never 0")
    if isinstance(x, bool):
        raise Refused(f"D({x!r}): not a number")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def add(a: Decimal, b: Decimal) -> Decimal:
    with localcontext(CTX):
        return a + b


def sub(a: Decimal, b: Decimal) -> Decimal:
    with localcontext(CTX):
        return a - b


def pct(diff: Decimal, ref: Decimal) -> Decimal:
    with localcontext(CTX):
        return (diff * 100 / ref).quantize(Decimal("0.01"))


def s(x) -> str | None:
    """Print a Decimal exactly (no exponent), None stays None."""
    if x is None:
        return None
    if isinstance(x, str):
        return x
    t = format(x, "f")
    return t


# ------------------------------------------------------------------------------------------------ (a) ownership
def code_owner(families: list[dict], prefix: str) -> dict[str, str]:
    """item code -> family code for every code starting with prefix; two owners -> REFUSED."""
    own: dict[str, str] = {}
    for f in families:
        for c in f.get("item_codes", []):
            if not c.startswith(prefix):
                continue
            if c in own and own[c] != f["code"]:
                raise Refused(f"R-T679-1 (a): {c} owned by {own[c]} and {f['code']} (DOUBLY_OWNED_CODE)")
            own[c] = f["code"]
    return own


# ------------------------------------------------------------------------------------------------ (b) line buckets
def classify(line: dict, unit: str, causes: dict[str, dict]) -> dict:
    """One line -> its bucket. causes: line_id -> {cause_class, source, ...} for HELD lines."""
    lid = line.get("line_id")
    if line.get("unit") != unit:
        raise Refused(f"{lid}: unit {line.get('unit')!r} is not the trade unit {unit!r} (units never mixed)")
    cls = line.get("class")
    lo, hi, net = line.get("held_low"), line.get("held_high"), line.get("measured_net")
    b = line.get("binding") or {}
    if cls == RELEASED:
        if net is None:
            raise Refused(f"{lid}: RELEASED without a number")
        if lo is not None or hi is not None:
            raise Refused(f"{lid}: RELEASED line carries a held bound")
        return {"bucket": RELEASED, "net": D(net), "binding": b.get("binding")}
    if cls == HELD:
        if net is not None:
            raise Refused(f"{lid}: HELD line carries a released number (a held quantity is never released)")
        if b.get("binding") in (VERIFIED_WHOLE, VERIFIED_COMPONENT):
            raise Refused(f"{lid}: a held line is never verified")
        c = causes.get(lid)
        if not c or c.get("cause_class") not in CAUSE_CLASSES:
            raise Refused(f"{lid}: HELD line with no census cause (every HELD line names its cause)")
        if (lo is None) != (hi is None):
            raise Refused(f"{lid}: one bound only in the index (lower-only / upper-only is a blank line + its census)")
        if lo is None:
            return {"bucket": "HELD_BLANK", "cause": c}
        dlo, dhi = D(lo), D(hi)
        if dlo > dhi or dlo < 0:
            raise Refused(f"{lid}: bound {lo} .. {hi} not ordered / negative")
        return {"bucket": "HELD_BOUNDED", "low": dlo, "high": dhi, "cause": c}
    if cls == EXCLUDED:
        if net is not None or lo is not None or hi is not None:
            raise Refused(f"{lid}: EXCLUDED line carries a quantity")
        return {"bucket": EXCLUDED}
    raise Refused(f"{lid}: class {cls!r} unknown")


def empty_bucket() -> dict:
    z = Decimal(0)
    return {"lines": 0, "released_lines": 0, "released": z, "held_bounded_lines": 0, "held_low": z, "held_high": z,
            "held_blank_lines": 0, "held_blank_by_cause": OrderedDict((c, 0) for c in CAUSE_CLASSES),
            "held_bounded_by_cause": OrderedDict((c, 0) for c in CAUSE_CLASSES),
            "excluded_lines": 0, "verified_whole_lines": 0, "verified_whole": z,
            "verified_component_lines": 0, "verified_component": z}


def put(acc: dict, k: dict) -> None:
    acc["lines"] += 1
    b = k["bucket"]
    if b == RELEASED:
        acc["released_lines"] += 1
        acc["released"] = add(acc["released"], k["net"])
        if k["binding"] == VERIFIED_WHOLE:
            acc["verified_whole_lines"] += 1
            acc["verified_whole"] = add(acc["verified_whole"], k["net"])
        elif k["binding"] == VERIFIED_COMPONENT:
            acc["verified_component_lines"] += 1
            acc["verified_component"] = add(acc["verified_component"], k["net"])
    elif b == "HELD_BOUNDED":
        acc["held_bounded_lines"] += 1
        acc["held_low"] = add(acc["held_low"], k["low"])
        acc["held_high"] = add(acc["held_high"], k["high"])
        acc["held_bounded_by_cause"][k["cause"]["cause_class"]] += 1
    elif b == "HELD_BLANK":
        acc["held_blank_lines"] += 1
        acc["held_blank_by_cause"][k["cause"]["cause_class"]] += 1
    else:
        acc["excluded_lines"] += 1


def merge(into: dict, other: dict) -> None:
    for key, v in other.items():
        if isinstance(v, Decimal):
            into[key] = add(into[key], v)
        elif isinstance(v, int):
            into[key] += v
        else:
            for c, n in v.items():
                into[key][c] += n


def scope_view(acc: dict) -> dict:
    """(c) (d): the printed view of one scope; buckets side by side, never summed together."""
    held = acc["held_bounded_lines"] + acc["held_blank_lines"]
    d = acc["released_lines"] + held
    if acc["held_blank_lines"]:
        rng = [s(add(acc["released"], acc["held_low"])), OPEN]
    else:
        rng = [s(add(acc["released"], acc["held_low"])), s(add(acc["released"], acc["held_high"]))]
    out = OrderedDict()
    out["lines"] = acc["lines"]
    out["released"] = {"lines": acc["released_lines"], "m3": s(acc["released"])}
    out["held_bounded"] = {"lines": acc["held_bounded_lines"], "low": s(acc["held_low"]), "high": s(acc["held_high"]),
                           "by_cause": dict(acc["held_bounded_by_cause"])}
    out["held_blank"] = {"lines": acc["held_blank_lines"], "high": OPEN if acc["held_blank_lines"] else None,
                         "by_cause": dict(acc["held_blank_by_cause"])}
    out["excluded"] = {"lines": acc["excluded_lines"]}
    out["engine_range"] = rng
    out["verified_share"] = {"whole": f"{acc['verified_whole_lines']} / {d}", "whole_m3": s(acc["verified_whole"]),
                             "component": f"{acc['verified_component_lines']} / {d}",
                             "component_m3": s(acc["verified_component"])}
    return out


def aggregate(lines: list[dict], families: list[dict], causes: dict[str, dict], *, prefix: str, unit: str) -> dict:
    """lines of one trade -> per family accumulators + trade total by families + trade total by lines (independent)."""
    own = code_owner(families, prefix)
    fam_order = [f["code"] for f in families if any(c.startswith(prefix) for c in f.get("item_codes", []))]
    fams: "OrderedDict[str, dict]" = OrderedDict((c, empty_bucket()) for c in fam_order)
    by_code: "OrderedDict[str, dict]" = OrderedDict()
    by_lines = empty_bucket()
    seen = set()
    for ln in lines:
        code = ln.get("item_code", "")
        if not code.startswith(prefix):
            continue
        lid = ln.get("line_id")
        if lid in seen:
            raise Refused(f"{lid}: line listed twice")
        seen.add(lid)
        if code not in own:
            raise Refused(f"R-T679-1 (a): {code} ({lid}) owned by no family (NO_FAMILY): never dropped")
        k = classify(ln, unit, causes)
        put(fams[own[code]], k)
        put(by_code.setdefault(code, empty_bucket()), k)
        put(by_lines, k)
    by_fams = empty_bucket()
    for acc in fams.values():
        merge(by_fams, acc)
    if by_fams != by_lines:
        raise Refused("R-T679-1 (c): family subtotals do not re-add to the line total")
    return {"families": fams, "codes": by_code, "total": by_lines, "owner": own}


# ------------------------------------------------------------------------------------------------ (e) reference apart
def key_codes(keys: list[dict]) -> dict[str, str]:
    seen: dict[str, str] = {}
    for k in keys:
        for c in k["item_codes"]:
            if c in seen:
                raise Refused(f"R-T679-1 (e): {c} answers two keys ({seen[c]}, {k['key']})")
            seen[c] = k["key"]
    return seen


def compare(keys: list[dict], refs: dict[str, dict], by_code: dict[str, dict], *, unit: str) -> list[dict]:
    """keys: [{key, reference_id, item_codes}], refs: reference_id -> {qty, unit}. Reference never a quantity."""
    key_codes(keys)
    rows = []
    for k in keys:
        r = refs.get(k["reference_id"])
        if r is None:
            raise Refused(f"{k['key']}: reference row {k['reference_id']} absent")
        if r.get("unit") != unit:
            raise Refused(f"{k['key']}: reference unit {r.get('unit')!r} is not {unit!r}")
        acc = empty_bucket()
        present = []
        for c in k["item_codes"]:
            if c in by_code:
                merge(acc, by_code[c])
                present.append(c)
        v = scope_view(acc)
        ref = D(r["qty"])
        diff = sub(ref, acc["released"])
        held = acc["held_bounded_lines"] + acc["held_blank_lines"]
        row = OrderedDict(key=k["key"], reference_id=k["reference_id"], item_codes=k["item_codes"],
                          item_codes_present=present, reference=s(ref), engine=v,
                          difference_ref_minus_released=s(diff))
        if held:
            row["pct_of_reference"] = None
            row["pct_note"] = (f"suppressed: {held} HELD line(s) in the key (R-T613-1 (g)); the difference is "
                               "released-only and is NOT a verdict")
        elif ref == 0:
            row["pct_of_reference"] = None
            row["pct_note"] = "suppressed: reference 0"
        else:
            row["pct_of_reference"] = s(pct(diff, ref))
            row["pct_note"] = "difference / reference, released-only; NOT a verdict, agreement is never proof"
        rows.append(row)
    return rows


def not_keyed(by_code: dict[str, dict], keys: list[dict]) -> list[str]:
    kc = key_codes(keys)
    return [c for c in by_code if c not in kc]
