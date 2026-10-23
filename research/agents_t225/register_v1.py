"""T-225 wall register v1: status classes, held causes and per-status totals (any villa; research module, imported
by nothing in engine/; no quantity is computed here, every figure is read from the merged per-wall ledger).

Owner status classes (BLOCKWORK_RESOLUTION_PROGRAMME.md s.2, owner 2026-10-23) from the standard evidence statuses
(WORKFLOW_CONTROLS_2026-10-21.md s.5):
    VERIFIED                   -> VERIFIED
    DRAWING-CONFIRMED          -> SOURCE-SUPPORTED PENDING INDEPENDENT CHECK
    ASSUMED — OWNER-APPROVED   -> PROJECT-SPECIFIC
    HELD                       -> HELD
    UNKNOWN                    -> HELD (scope not established; never 0)
OWNER DECISION REQUIRED is never produced by mapping: it is set only for a wall named in an owner question asked
under ERS s.2.7 (none in v1).

Rule R-T225-1 (deductions by host status; any villa). A deduction belongs to the wall that hosts the opening and
carries that wall's net status. A total of net blockwork per status = sum over walls whose net has that status of
(gross - deductions of that wall). Deductions booked on a wall whose gross or net is HELD are reported with the HELD
scope and never subtracted from an established gross or net. Consequently "established gross - all deductions" is not
a net: the difference is exactly
    gap = sum(gross of walls with established gross and HELD net)
          - sum(deductions of walls with established gross and HELD net)
          - sum(deductions of walls with HELD gross)
and tests/t225_wall_register checks it wall by wall.
"""
from __future__ import annotations

from collections import defaultdict

CLASS = {
    "VERIFIED": "VERIFIED",
    "DRAWING-CONFIRMED": "SOURCE-SUPPORTED PENDING INDEPENDENT CHECK",
    "ASSUMED — OWNER-APPROVED": "PROJECT-SPECIFIC",
    "HELD": "HELD",
    "UNKNOWN": "HELD",
}
ESTABLISHED = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED")

# held cause classes, first match wins (order = BLOCKWORK_RESOLUTION_PROGRAMME.md s.4 attribution)
CAUSES = (
    ("lift tie beam size (ST p.8 n.19)", lambda why, t143: "lift tie beam" in why,
     "ST7757.pdf p.8 RECOMMENDATIONS note 19: the tie beam round the lift is called for but its size is not printed",
     "T-227"),
    ("beam depth / register conflict", lambda why, t143: "depth not established" in why,
     "depth of the member above not established in the T-110 beam register (unprinted depth or CONFLICT, Q-61 C)",
     "T-226"),
    ("no member drawn above", lambda why, t143: "no beam or slab underside drawn" in why,
     "no beam or slab underside drawn above the piece on the ST7757 dxf.dxf roof-slab plan (dome opening / column face)",
     "T-226 / T-227"),
    ("held opening", lambda why, t143: "held opening" in why,
     "opening size (head / height) not established for an opening inside the run (T-175 hosts; heads T-201)",
     "T-227 / T-222"),
    ("no wall band or member bound (glazed line / held strip)", lambda why, t143: "no member above bound" in why,
     "no wall band or member bound to the run (glazed line or the 0.40 strip); length from the hand census only",
     "T-227"),
    ("annex datum (Q-54 B)", lambda why, t143: "annex datum" in t143,
     "annex storey datum: +4.30 mark not established as the structural slab top (owner Q-54 B HOLD; section B-B / roof "
     "detail)", "T-227"),
)


def status_class(status: str) -> str:
    if status not in CLASS:
        raise ValueError(f"unknown evidence status {status!r}")
    return CLASS[status]


def cause(hold_reason: str, t143_reason: str = "") -> tuple:
    """(cause class, missing item, package) of a held wall; ValueError when nothing names a cause (a HELD wall
    without a named cause is a register defect, never silently accepted)."""
    for name, test, missing, pkg in CAUSES:
        if test(hold_reason or "", t143_reason or ""):
            return name, missing, pkg
    raise ValueError(f"held wall without a named cause: {hold_reason!r} / {t143_reason!r}")


def f(x) -> float:
    return float(x) if x not in ("", None) else 0.0


def totals(rows, key=lambda r: (r["floor"], r["t_m"], r["block_type"])):
    """Per key: gross by gross status, deductions by host net status, net by net status (R-T225-1)."""
    out = defaultdict(lambda: defaultdict(float))
    for r in rows:
        for s in (r["gross_status"], r["net_status"]):
            if s not in CLASS:
                raise ValueError(f"unknown evidence status {s!r} on {r['row_id']}")
        a = out[key(r)]
        a["walls"] += 1
        a["gross " + r["gross_status"]] += f(r["gross_m2"])
        a["deductions on net " + r["net_status"]] += f(r["deducted_m2"])
        if r["net_status"] in ESTABLISHED:
            if r["gross_status"] not in ESTABLISHED:
                raise ValueError(f"{r['row_id']}: established net on a HELD gross")
            net = f(r["net_m2"])
            if abs(net - (f(r["gross_m2"]) - f(r["deducted_m2"]))) > 0.0015:
                raise ValueError(f"{r['row_id']}: net {net} != gross - deductions")
            a["net " + r["net_status"]] += net
        elif r["net_m2"] not in ("", None):
            raise ValueError(f"{r['row_id']}: HELD net carries a figure")
    return out


def gap(rows) -> dict:
    """Components of (established gross - all deductions) - established net (R-T225-1), with the walls named."""
    g_held_net, d_held_net, d_held_gross = [], [], []
    for r in rows:
        if r["gross_status"] in ESTABLISHED and r["net_status"] not in ESTABLISHED:
            g_held_net.append((r["row_id"], f(r["gross_m2"])))
            if f(r["deducted_m2"]):
                d_held_net.append((r["row_id"], f(r["deducted_m2"])))
        elif r["gross_status"] not in ESTABLISHED and f(r["deducted_m2"]):
            d_held_gross.append((r["row_id"], f(r["deducted_m2"])))
    est_g = sum(f(r["gross_m2"]) for r in rows if r["gross_status"] in ESTABLISHED)
    all_d = sum(f(r["deducted_m2"]) for r in rows)
    est_n = sum(f(r["net_m2"]) for r in rows if r["net_status"] in ESTABLISHED)
    s = lambda L: sum(v for _, v in L)
    return {
        "established_gross": est_g, "all_deductions": all_d, "established_net": est_n,
        "gap": est_g - all_d - est_n,
        "gross_of_established_gross_held_net": g_held_net, "deductions_on_established_gross_held_net": d_held_net,
        "deductions_on_held_gross": d_held_gross,
        "reconstructed": s(g_held_net) - s(d_held_net) - s(d_held_gross),
    }
