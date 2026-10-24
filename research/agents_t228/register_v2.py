"""T-228 wall register v2: apply CHECKER-MERGED resolutions to register v1, after-coverage by class (any villa).

Research module, imported by nothing in engine/; no quantity is measured here. Register v1 (T-225) is never edited:
v2 = v1 + an ordered list of changes, each naming the merged package (or the Checker verdict) it comes from.

Rule R-T228-1 (resolution ledger; any villa; provenance BLOCKWORK_RESOLUTION_PROGRAMME.md s.2 / s.5, WORKFLOW_CONTROLS
s.1 / s.4 / s.5, ERS s.2.5 / s.2.6):
  1. A change enters the register only from a source in the MERGED table: a package the Checker merged (its merge
     commit on the working branch) or a Checker verdict that rules on a wall. Anything else (a worker value on an
     unmerged branch, a number in a handoff the Checker corrected, a freelancer figure) is refused: UNMERGED_SOURCE.
  2. Two sources that set the same numeric or class field of one wall to different values conflict and are refused
     (CONFLICT) unless a later RULING (a Checker verdict) sets that field; text fields are appended, never lost.
  3. VERIFIED is set only by a ruling that names every component the Checker re-measured: a gross needs length and
     height, a net needs length, height and deductions. A component check never promotes the whole wall.
  4. A quantity resting on an owner-approved fallback (door height Q-55 C, white / black Q-60, Q-75 module) stays
     PROJECT-SPECIFIC even after a Checker re-measure (WORKFLOW_CONTROLS s.5: stays visible).
  5. A range between two readings is carried as its common part (established) + a HELD increment, never as either end.
  6. After the changes every wall row satisfies R-T225-1 (established net = gross - deductions; a HELD net carries no
     figure; no established net on a HELD gross) and the coverage by class reconciles to the gross:
        gross figure = net VERIFIED + net SOURCE-SUPPORTED + net PROJECT-SPECIFIC
                       + deductions on established nets + gross figure of walls whose net is HELD.
"""
from __future__ import annotations

from collections import defaultdict

VER = "VERIFIED"
SS = "SOURCE-SUPPORTED PENDING INDEPENDENT CHECK"
PS = "PROJECT-SPECIFIC"
HELD = "HELD"
CLASSES = (VER, SS, PS, HELD)
ESTABLISHED = (VER, SS, PS)

NUMERIC = ("length_m", "held_length_m", "height_weighted_m", "gross_m2", "deductions_m2", "net_m2", "net_m3", "t_m")
CLASS_FIELDS = ("gross_class", "net_class", "owner_status_class", "length_class", "type_class", "block_type")
TEXT = ("unresolved_reason", "evidence", "calculation", "smallest_held_quantity", "next_package", "openings_in_run",
        "held_openings", "net_bounds_m2", "held_cause_class", "source_ledgers", "verified_by_checker")
TOL = 0.0015


class RegisterError(ValueError):
    """A change or a row the register refuses (code in .code)."""

    def __init__(self, code: str, msg: str):
        super().__init__(f"{code}: {msg}")
        self.code = code


def f(x) -> float:
    return float(x) if x not in ("", None, "-") else 0.0


def has(x) -> bool:
    return x not in ("", None, "-")


def apply(v1_rows, changes, merged):
    """Return (v2_rows, change_log). `changes`: ordered dicts {wall_id, source, set: {field: value}, why,
    op ('set' | 'add'), remeasured: set of components (rulings only)}; `merged`: {source: reference}."""
    rows = {r["wall_id"]: dict(r) for r in v1_rows}
    order = [r["wall_id"] for r in v1_rows]
    owner = {}                       # (wall, field) -> (source, value) for numeric / class fields
    conflicts = {}                   # (wall, field) -> text, cleared only by a later RULING on that field
    log = []
    for c in changes:
        src, wid, op = c["source"], c["wall_id"], c.get("op", "set")
        if src not in merged:
            raise RegisterError("UNMERGED_SOURCE", f"{wid}: source {src!r} is not a checker-merged package or ruling")
        ruling = src.startswith("RULING")
        if op == "add":
            if wid in rows:
                raise RegisterError("DUPLICATE_WALL", f"{wid} already in the register (a piece is counted once)")
            rows[wid] = {k: "" for k in next(iter(rows.values())).keys()}
            rows[wid]["wall_id"] = wid
            order.append(wid)
        elif wid not in rows:
            raise RegisterError("UNKNOWN_WALL", f"{wid}: not in register v1 (use op 'add' for a new piece)")
        r = rows[wid]
        for k, v in c["set"].items():
            if k not in r:
                raise RegisterError("UNKNOWN_FIELD", f"{wid}: {k}")
            v = "" if v is None else str(v)
            if v in (VER,) and k in ("gross_class", "net_class") and not ruling:
                raise RegisterError("VERIFIED_WITHOUT_RULING", f"{wid}.{k}: only a Checker ruling sets VERIFIED")
            if v == VER and k == "gross_class" and not {"length", "height"} <= set(c.get("remeasured", ())):
                raise RegisterError("VERIFIED_INCOMPLETE", f"{wid}: gross VERIFIED needs length + height re-measured")
            if v == VER and k == "net_class" and not {"length", "height", "deductions"} <= set(c.get("remeasured", ())):
                raise RegisterError("VERIFIED_INCOMPLETE", f"{wid}: net VERIFIED needs length + height + deductions")
            if k in TEXT and not ruling and k not in ("held_openings", "openings_in_run", "net_bounds_m2",
                                                        "held_cause_class"):
                old = r[k]
                r[k] = v if not old or op == "add" or v in old else f"{old} || {src}: {v}"
            else:
                prev = owner.get((wid, k))
                if ruling:
                    conflicts.pop((wid, k), None)
                elif prev and prev[0] != src and prev[1] != v:
                    conflicts[(wid, k)] = f"{wid}.{k}: {prev[0]} {prev[1]!r} vs {src} {v!r}"
                owner[(wid, k)] = (src, v)
                r[k] = v
        log.append({"wall_id": wid, "source": src, "reference": merged[src], "op": op,
                    "fields": ";".join(sorted(c["set"])), "why": c.get("why", "")})
    if conflicts:
        raise RegisterError("CONFLICT", "; ".join(conflicts.values()) + " (no Checker ruling on the field)")
    out = [rows[w] for w in order]
    for r in out:
        check_row(r)
    return out, log


HOLD_FIELDS = ("gross_class", "net_class", "net_m2", "net_m3", "owner_status_class", "net_bounds_m2",
               "held_cause_class", "unresolved_reason", "next_package", "smallest_held_quantity", "held_increment_m2",
               "pending_findings_t228")


def hold(rows, findings):
    """R-T228-2 (any villa; ERS s.2 / WORKFLOW_CONTROLS s.8 'a DIFFERS finding that affects a quantity makes that line
    HELD with the finding as its cause'): a new drawing finding that contradicts an established figure may only LOWER
    its class to HELD (never raise a class, never write a number); the figure moves to the bounds text and the finding
    waits for the Checker. Returns the rows (changed in place) and a log."""
    by = {r["wall_id"]: r for r in rows}
    log = []
    for h in findings:
        r = by.get(h["wall_id"])
        if r is None:
            raise RegisterError("UNKNOWN_WALL", h["wall_id"])
        for k, v in h["set"].items():
            if k not in HOLD_FIELDS:
                raise RegisterError("FINDING_WRITES_QUANTITY", f"{h['wall_id']}.{k}: a finding only holds")
            if k in ("gross_class", "net_class", "owner_status_class") and v != HELD:
                raise RegisterError("FINDING_RAISES_CLASS", f"{h['wall_id']}.{k} -> {v}: a finding never raises")
            if k in ("net_m2", "net_m3") and v not in ("", None):
                raise RegisterError("FINDING_WRITES_QUANTITY", f"{h['wall_id']}.{k} = {v}")
            r[k] = "" if v is None else str(v)
        check_row(r)
        log.append({"wall_id": h["wall_id"], "source": h["source"], "reference": h.get("reference", ""), "op": "hold",
                    "fields": ";".join(sorted(h["set"])), "why": h.get("why", "")})
    return rows, log


def gross_from_pieces(pieces, length_m, tol=0.001):
    """Lessons row (Checker 2026-10-23 18:01, T-226): height pieces are measured between drawn band edges and the run is
    closed to its census length on the last member. `pieces` = [(length m, height m), ...]; returns the gross m2.
    Refuses pieces that do not sum to the census length (an unsampled remainder spread at a mean height) and metres
    given in millimetres."""
    if length_m > MAX_LEN or any(h > MAX_H or l > MAX_LEN for l, h in pieces):
        raise RegisterError("UNIT_GUARD", "a wall piece over 200 m or a height over 30 m: millimetres given as metres")
    if any(l <= 0 or h <= 0 for l, h in pieces):
        raise RegisterError("PIECE_HELD", "a piece without a length or height is HELD, never 0")
    s = sum(l for l, _ in pieces)
    if abs(s - length_m) > tol:
        raise RegisterError("PIECES_NOT_CLOSED", f"pieces sum {s:.4f} m != census length {length_m:.4f} m")
    return sum(l * h for l, h in pieces)


MAX_LEN, MAX_H = 200.0, 30.0


def check_row(r) -> None:
    """R-T225-1 on one row (the register refuses an inconsistent row)."""
    if f(r.get("length_m")) > MAX_LEN or f(r.get("height_weighted_m")) > MAX_H:
        raise RegisterError("UNIT_GUARD", f"{r['wall_id']}: length / height out of range (millimetres?)")
    for k in ("gross_class", "net_class"):
        if r[k] not in CLASSES:
            raise RegisterError("UNKNOWN_CLASS", f"{r['wall_id']}.{k} = {r[k]!r}")
    if r["net_class"] in ESTABLISHED:
        if r["gross_class"] not in ESTABLISHED:
            raise RegisterError("NET_ON_HELD_GROSS", f"{r['wall_id']}: established net on a HELD gross")
        if abs(f(r["net_m2"]) - (f(r["gross_m2"]) - f(r["deductions_m2"]))) > TOL:
            raise RegisterError("NET_MISMATCH", f"{r['wall_id']}: net {r['net_m2']} != gross - deductions")
        if r["net_class"] == VER and r["gross_class"] != VER:
            raise RegisterError("VERIFIED_INCOMPLETE", f"{r['wall_id']}: VERIFIED net on an unverified gross")
    elif has(r["net_m2"]):
        raise RegisterError("HELD_WITH_FIGURE", f"{r['wall_id']}: HELD net carries a figure")
    if r["gross_class"] == HELD and r["net_class"] != HELD:
        raise RegisterError("NET_ON_HELD_GROSS", r["wall_id"])


def coverage(rows, key=lambda r: (r["floor"], r["t_m"], r["block_type"])):
    """Per key: walls, lengths, gross by class, net by class, held figures; with the reconciliation identity."""
    out = defaultdict(lambda: defaultdict(float))
    for r in rows:
        a = out[key(r)]
        a["walls"] += 1
        a["length_established_m"] += f(r["length_m"]) - f(r["held_length_m"])
        a["length_held_m"] += f(r["held_length_m"])
        g = f(r["gross_m2"])
        a["gross_figure_m2"] += g
        a["gross " + r["gross_class"]] += g
        if r["net_class"] in ESTABLISHED:
            a["net " + r["net_class"]] += f(r["net_m2"])
            a["deductions_on_established_net_m2"] += f(r["deductions_m2"])
        else:
            a["walls_net_held"] += 1
            a["gross_figure_of_held_net_m2"] += g
            a["deductions_on_held_net_m2 (held scope)"] += f(r["deductions_m2"])
        if r["gross_class"] == VER and r["net_class"] != VER:
            a["walls_gross_verified_net_not"] += 1
    for k, a in out.items():
        rhs = (a["net " + VER] + a["net " + SS] + a["net " + PS] + a["deductions_on_established_net_m2"]
               + a["gross_figure_of_held_net_m2"])
        a["reconciliation_residual_m2"] = round(a["gross_figure_m2"] - rhs, 6)
        if abs(a["reconciliation_residual_m2"]) > 0.002:
            raise RegisterError("NOT_RECONCILED", f"{k}: gross {a['gross_figure_m2']} vs classes {rhs}")
    return out


def length_identity(v1_rows, v2_rows, listed):
    """Total wall length v2 - v1 must equal the sum of the listed length resolutions (T-222 s.2 'a test that the total
    length is unchanged must list them'). Returns the residual (m)."""
    d = sum(f(r["length_m"]) for r in v2_rows) - sum(f(r["length_m"]) for r in v1_rows)
    return round(d - sum(listed.values()), 6) + 0.0
