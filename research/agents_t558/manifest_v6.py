"""T-558 WIRING MANIFEST V6: the T-555 manifest (V5, pinned) extended by EVERY piece merged after it, up to the pinned
V6 base, on the candidate of record ARCH_TAKEOFF_V3.0.58, PLUS the wiring row V5 left without an owner (F-T555-3): the
DRY FIN.PLASTER height correction, now on PLASTER_HEIGHT_METHOD_V1 (T-556, R-T556-1) instead of the T-552 bound.
Research / integration preparation only (lane I, non-candidate): nothing here writes a candidate, released, rule,
knowledge or registry file; nothing is wired.

Coverage by R-T549-1 (V4's own check_coverage, reused): range (V5 base 47d74505, V6 base 431ac67f] on the first-parent
line; every 'Merge agents/task-T-<n>' in it is a source with that merge commit or a declared NO_WIRING piece.

What V6 changes against V5, each from the merged piece's own committed output or its own function (no quantity typed):
  - T-556 R-T556-1: the 11 DRY FIN.PLASTER room lines get their plaster-height range (T-556 rows 'new_lo .. new_hi');
    it supersedes the T-552 bound V5 carried (Checker 10:20: GF-15 T-552 bound over-stated by 3.268 m2, W03 head above
    the paint line). Every line stays HELD (each has a face under a roof whose build-up is not printed, D-39 / DCR-6):
    the 4 RELEASED lines 217.2081 m2 -> HELD (BOUNDED) 262.01799 .. 262.05199 m2; the 2 HELD-blank lines (GF-01,
    GF-04) gain a bound; the 5 HELD-bounded lines move their bound.
  - the T-454 / T-489 plaster material bindings of those lines, ONE BY ONE: the read (class / net / held range) of
    every binding changes; the figure-bearing ones are the WALL_PLASTER mortar m3 rows, whose bound follows T-454's own
    rule (t454_plaster_materials.py: held range x the WALL_PLASTER reference thickness, rounded 9), reproduced first
    on the bounds the T-454 table already prints. The level-4 estimate beside a released line (net x 0.020) goes,
    because a HELD line has no area: it becomes a bound beside. HELD stays HELD; no binding carries a value.
  - FIN.PAINT: expected after = before for EVERY paint line (45); the 11 paint lines paired with the moved plaster
    lines are listed room by room (register 'WALL PLASTER HEIGHT vs PAINT HEIGHT': only B5 plaster moves).
  - T-550 / T-559 (blockwork to cause, ENGINE_WRONG none), T-557 (statement adapters), T-555 (V5 itself): no line moves.
Every source commit must be an ancestor of HEAD (manifest_t536.check_sources). No private drawing is read here.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(rel, name):
    p = ROOT / rel
    if str(p.parent) not in sys.path:
        sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M5 = _load("research/agents_t555/manifest_v5.py", "manifest_v5_t558")              # read only
M4, M2, M1 = M5.M4, M5.M2, M5.M1
ManifestError = M5.ManifestError
sha256 = M1.sha256

from engine.source import plaster_materials_table_v1 as P   # noqa: E402  (T-454's reference thickness and _r)

SCHEMA = "URBAN_T558_WIRING_MANIFEST_V6"
RULE = "R-T558-1"
OUT_JSON = ROOT / "research/agents_t558/WIRING_MANIFEST_V6.json"
V5_JSON = M5.OUT_JSON
V5_PIN = "fbdfa500039b11e9c43edf901e468bf5693f11e5faa66575291b8c9ae7149636"     # the merged V5 (e3e0ed0e)
T556 = ROOT / "research/agents_t556/out/T556_PLASTER_HEIGHT.json"

V5_BASE = M5.V5_BASE          # 47d74505 Merge agents/task-T-547
V6_BASE = "431ac67f"          # Merge agents/task-T-557 (the newest merge when T-558 was claimed)

NEW_PIECES = {
    "T-550": {"merge": "f052dfeb", "gate": "A", "rules": ["R-T550-1"],
              "verdict": "Verifier 2026-11-06 08:05Z GATE A PASS: blockwork UNRESOLVED 101.43 m2 to physical causes, "
                         "H1 measured, own raw-DXF read; ENGINE_WRONG none; no line moves"},
    "T-555": {"merge": "e3e0ed0e", "gate": "A", "rules": ["R-T549-1"],
              "verdict": "Verifier 2026-11-06 08:08Z GATE A PASS: WIRING MANIFEST V5; F-T555-3 plaster height with no "
                         "owning row -> T-556 / T-558"},
    "T-556": {"merge": "655b9eac", "gate": "A", "rules": ["R-T556-1"],
              "verdict": "Verifier 2026-11-06 10:20Z GATE A PASS: PLASTER_HEIGHT_METHOD_V1; own raw-DXF re-measure "
                         "1F-04 63.141 and 2F-03 69.775 m2 AGREE, GF-15 66.529 by hand (T-552 bound over-stated "
                         "3.268, Checker error recorded); every line HELD; PARTIALLY VERIFIED 2 / 11; wiring T-558"},
    "T-557": {"merge": "431ac67f", "gate": "A", "rules": ["R-T557-1"],
              "verdict": "Verifier 2026-11-06 10:20Z GATE A PASS: statement adapters T-545 / T-547 / T-552 + T-550 "
                         "restatement; no quantity moves; plaster restatement superseded by T-556"},
    "T-559": {"merge": "f6636468", "gate": "A", "rules": ["R-T559-1", "R-T559-2"],
              "verdict": "Verifier 2026-11-06 10:20Z GATE A PASS: blockwork leftover 25.92 m2 by opening id and "
                         "parapet edge member; ENGINE_WRONG none; no line moves"},
}
NO_WIRING = {
    "T-550": "reconciliation to cause (blockwork vs the freelancer): moves no line; ENGINE_WRONG none found",
    "T-555": "the V5 manifest itself: superseded here (every V5 statement carried unless listed in v5_to_v6)",
    "T-557": "statement adapters: moves no line; its F-T557-2 ENGINE_WRONG (plaster height) is the T-556 row wired here",
    "T-559": "reconciliation leftover (blockwork openings / parapet edge members): moves no line; ENGINE_WRONG none",
}
PIECES = dict(M5.PIECES, **NEW_PIECES)

PLASTER_LAYER = "WALL_PLASTER"            # the one plaster layer with a sourced thickness (T-454 REFERENCE, EXACT)
TABLES = ("T-454", "T-489")


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def v5_manifest():
    if sha256(V5_JSON) != V5_PIN:
        raise ManifestError(f"PIN: {V5_JSON.name} sha256 {sha256(V5_JSON)[:8]} is not the pinned {V5_PIN[:8]}")
    return _json(V5_JSON)


def _src(*tids):
    return [{"task": t, "merge": PIECES[t]["merge"], "checker": PIECES[t]["verdict"]} for t in tids]


def _d(x):
    return None if x is None else Decimal(str(x))


def _f(x):
    return None if x is None else float(Decimal(str(x)))


# ------------------------------------------------------------------------------------------------- plaster lines
def plaster_lines(idx, v5, t556=None):
    """per DRY FIN.PLASTER line: candidate before -> V5 expectation (T-552) -> V6 expectation (T-556), HELD."""
    t = t556 if t556 is not None else _json(T556)
    if not t["method"].startswith("PLASTER_HEIGHT_METHOD_V1"):
        raise ManifestError("T-556 output is not PLASTER_HEIGHT_METHOD_V1")
    v5rows = {r["line_id"]: r for r in v5["plaster_height"]["rows"]}
    rows6 = {r["line_id"]: r for r in t["rows"]}
    if set(rows6) != set(v5rows):
        raise ManifestError(f"T-556 lines {sorted(set(rows6) ^ set(v5rows))} differ from the V5 plaster lines")
    rows, rel_b, lo_a, hi_a, rel_lo, rel_hi = [], Decimal(0), Decimal(0), Decimal(0), Decimal(0), Decimal(0)
    for lid in [r["line_id"] for r in v5["plaster_height"]["rows"]]:
        r, l, r5 = rows6[lid], idx[lid], v5rows[lid]
        if l["item_code"] != "FIN.PLASTER" or l["class"] != r["candidate_class"]:
            raise ManifestError(f"{lid}: not the {r['candidate_class']} FIN.PLASTER line T-556 names")
        lo, hi = Decimal(r["new_lo"]), Decimal(r["new_hi"])
        if lo > hi or lo <= 0:
            raise ManifestError(f"{lid}: T-556 range {lo} .. {hi} inverted or not positive")
        if [Decimal(x) for x in r["t552_restated"]] != [_d(x) for x in r5["after"]["bound_m2"]]:
            raise ManifestError(f"{lid}: T-556's T-552 column is not the V5 expectation")
        old = [Decimal(x) for x in r["old_paint_height_basis"]["value"]] if r["old_paint_height_basis"]["value"] else None
        if l["class"] == "RELEASED":
            net = _d(l["measured_net"])
            if old != [net, net]:
                raise ManifestError(f"{lid}: T-556 'old' is not the released candidate value {net}")
            before = {"class": "RELEASED", "value": float(net), "held_m2": None}
            rel_b, rel_lo, rel_hi = rel_b + net, rel_lo + lo, rel_hi + hi
        else:
            hl = [_d(l["held_low"]), _d(l["held_high"])] if l["held_low"] is not None else None
            if (old or None) != hl:
                raise ManifestError(f"{lid}: T-556 'old' {old} is not the candidate held range {hl}")
            before = {"class": "HELD", "value": None, "held_m2": None if hl is None else [float(x) for x in hl]}
        lo_a, hi_a = lo_a + lo, hi_a + hi
        rows.append({"line_id": lid, "room": r["room"], "element_id": l["element_id"], "before": before,
                     "v5_expected_after": r5["after"],
                     "v6_expected_after": {"class": "HELD", "state": "HELD (BOUNDED)", "value": None,
                                           "held_low": float(lo), "held_high": float(hi),
                                           "H_floor_m": r["H_floor_m"], "H_roof_scenario_m": r["H_roof_scenario_m"],
                                           "roof_share": r["roof_share"],
                                           "openings_head_above_G1": r["openings_head_above_G1"]},
                     "v5_to_v6_m2": [float(lo - _d(r5["after"]["bound_m2"][0])),
                                     float(hi - _d(r5["after"]["bound_m2"][1]))],
                     "why_held": r["status"]})
    t4 = t["released_4_lines"]
    if Decimal(t4["old"]) != rel_b or [Decimal(x) for x in t4["new"]] != [rel_lo, rel_hi]:
        raise ManifestError("T-556 released_4_lines is not the sum of its released rows")
    if [Decimal(x) for x in t["totals"]["new"]] != [lo_a, hi_a]:
        raise ManifestError("T-556 totals.new is not the sum of its rows")
    paint_rel = sum((_d(l["measured_net"]) for l in idx.values()
                     if l["item_code"] == "FIN.PAINT" and l["class"] == "RELEASED"), Decimal(0))
    if paint_rel != rel_b:
        raise ManifestError(f"released dry plaster {rel_b} is not the released paint {paint_rel}: cause unproven")
    plaster_rel = sum((_d(l["measured_net"]) for l in idx.values()
                       if l["item_code"] == "FIN.PLASTER" and l["class"] == "RELEASED"), Decimal(0))
    return {"method": t["method"], "rows": rows,
            "released_lines": sum(1 for r in rows if r["before"]["class"] == "RELEASED"),
            "held_lines": sum(1 for r in rows if r["before"]["class"] == "HELD"),
            "released_before_m2": float(rel_b), "equals_released_paint_m2": float(paint_rel),
            "released_after_bound_m2": [float(rel_lo), float(rel_hi)],
            "released_change_pct": [float(((rel_lo - rel_b) / rel_b * 100).quantize(Decimal("0.01"))),
                                    float(((rel_hi - rel_b) / rel_b * 100).quantize(Decimal("0.01")))],
            "all_11_after_bound_m2": [float(lo_a), float(hi_a)],
            "v5_all_11_bound_m2": [float(Decimal(x)) for x in t["totals"]["t552"]],
            "code_view": {"FIN.PLASTER_released_now_m2": float(plaster_rel),
                          "FIN.PLASTER_released_after_m2": float(plaster_rel - rel_b),
                          "moved_to_held_bounded_m2": [float(rel_lo), float(rel_hi)]},
            "supersedes": "V5 plaster_height (T-552 bound) for these 11 lines",
            "source": _src("T-556")}


# ------------------------------------------------------------------------------------------------- bindings
def _bound_rule(lo, hi):
    """T-454's own bound beside a HELD line (t454_plaster_materials.py: held range x reference thickness, round 9)."""
    t = P.REFERENCE[PLASTER_LAYER]["thickness_m"]
    if t is None or P.REFERENCE[PLASTER_LAYER]["kind"] != "EXACT":
        raise ManifestError("T-454 WALL_PLASTER reference thickness is not an EXACT sourced value")
    return [P._r(lo * t, 9), P._r(hi * t, 9)]


def reproduce_bound_rule(bindings):
    """the rule must reproduce every bound the T-454 / T-489 tables already print on a bounded HELD FIN.PLASTER line."""
    n = 0
    for b in bindings:
        if b["table"] not in TABLES or b.get("item_code") != "FIN.PLASTER":
            continue
        hr = (b.get("read") or {}).get("held_read") or [None, None]
        if b["material"] == PLASTER_LAYER and b["kind"] == "mortar_m3" and hr[0] is not None:
            if b["bound"] != _bound_rule(hr[0], hr[1]):
                raise ManifestError(f"BOUND_RULE: {b['table']}|{b['row']} bound {b['bound']} is not "
                                    f"{_bound_rule(hr[0], hr[1])} (held range x reference thickness)")
            n += 1
    if n == 0:
        raise ManifestError("BOUND_RULE: no printed bound to reproduce the rule on")
    return n


def _key(b):
    return f"{b['table']}|{b['row']}|{b['kind']}"


def bindings(pl, bs, v5):
    """every T-454 / T-489 binding on the 11 lines: before (as the T-523 map reads it) -> expected after, one by one."""
    after = {r["line_id"]: r["v6_expected_after"] for r in pl["rows"]}
    mine = [b for b in bs if b["line_id"] in after]
    if any(b["table"] not in TABLES for b in mine):
        raise ManifestError("a binding on a dry plaster line comes from a table other than T-454 / T-489")
    if any(b["value"] is not None for b in mine):
        raise ManifestError("a plaster binding on a paint-height line carries a released value")
    rows = []
    for b in sorted(mine, key=_key):
        a = after[b["line_id"]]
        fig = b["material"] == PLASTER_LAYER and b["kind"] == "mortar_m3"
        bound_after = _bound_rule(a["held_low"], a["held_high"]) if fig else None
        before = {"class_read": b["read"]["class_read"], "net_read": b["read"]["net_read"],
                  "held_read": b["read"]["held_read"], "value": b["value"], "bound": b["bound"],
                  "estimate_beside": b.get("estimate_beside"), "wiring_state": b.get("wiring_state")}
        exp = {"class_read": "HELD", "net_read": None, "held_read": [a["held_low"], a["held_high"]], "value": None,
               "bound": bound_after, "estimate_beside": None,
               "wiring_state": "BOUND_ONLY" if bound_after is not None else "HELD"}
        figure_change = (before["bound"], before["estimate_beside"]) != (exp["bound"], exp["estimate_beside"])
        rows.append({"key": _key(b), "line_id": b["line_id"], "table": b["table"], "material": b["material"],
                     "kind": b["kind"], "before": before, "expected_after": exp,
                     "change": "FIGURE" if figure_change else "READ_ONLY",
                     "in_v5_stale_list": _key(b) in set(v5["plaster_height"]["bindings_stale"])})
    v5s = set(v5["plaster_height"]["bindings_stale"])
    keys = {r["key"] for r in rows}
    if not v5s <= keys:
        raise ManifestError(f"V5 stale bindings {sorted(v5s - keys)[:3]} are not bindings of the 11 lines")
    if len(rows) != len(v5s) + v5["plaster_height"]["bindings_held_blank_unchanged"]:
        raise ManifestError("the binding set of the 11 lines is not the V5 stale + V5 blank sets")
    fig = [r for r in rows if r["change"] == "FIGURE"]
    sums = {}
    for tb in TABLES:
        rel = [r for r in rows if r["table"] == tb and r["material"] == PLASTER_LAYER and r["kind"] == "mortar_m3"]
        est_b = sum((_d(r["before"]["estimate_beside"]) for r in rel if r["before"]["estimate_beside"] is not None),
                    Decimal(0))
        bl_b = [sum((_d(r["before"]["bound"][i]) for r in rel if r["before"]["bound"]), Decimal(0)) for i in (0, 1)]
        bl_a = [sum((_d(r["expected_after"]["bound"][i]) for r in rel), Decimal(0)) for i in (0, 1)]
        sums[tb] = {"wall_plaster_mortar_m3_estimate_beside_before": float(est_b),
                    "wall_plaster_mortar_m3_estimate_beside_after": 0.0,
                    "wall_plaster_mortar_m3_bound_before": [float(x) for x in bl_b],
                    "wall_plaster_mortar_m3_bound_after": [float(x) for x in bl_a],
                    "lines": len(rel)}
    return {"rule": "T-454 bound beside a HELD line: held range x WALL_PLASTER reference thickness "
                    f"{P.REFERENCE[PLASTER_LAYER]['thickness_m']} m (EXACT, level-4 ENGINEERING ESTIMATE source), "
                    "rounded 9 (research/agents_t454/t454_plaster_materials.py); T-489 reads V1 m3",
            "rows": rows, "count": len(rows), "v5_stale": len(v5s),
            "v5_blank_unchanged": v5["plaster_height"]["bindings_held_blank_unchanged"],
            "figure_changes": len(fig), "read_only_changes": len(rows) - len(fig),
            "figure_changes_not_in_v5_stale": sorted(r["key"] for r in fig if not r["in_v5_stale_list"]),
            "v5_stale_read_only_now": sorted(r["key"] for r in rows if r["in_v5_stale_list"] and r["change"] ==
                                             "READ_ONLY"),
            "table_sums": sums, "table_sums_note": "per table only: T-489 reads the T-454 mortar m3 (one physical "
                                                    "mortar), so the two tables are never added together",
            "values_after": 0,
            "why": "a binding reads its line; the 11 lines all move (4 RELEASED -> HELD, 2 blank -> bounded, 5 "
                   "re-bounded), so every binding is re-read; only WALL_PLASTER mortar m3 carries a figure (a bound "
                   "beside); bond coat (no thickness) and cement / sand (NEEDS_MIX) stay HELD blank"}


# ------------------------------------------------------------------------------------------------- paint (one owner)
def paint_unchanged(idx, pl):
    """FIN.PAINT expected after = before for every paint line; the 11 paint lines of the moved rooms listed by room."""
    paint = sorted((l for l in idx.values() if l["item_code"] == "FIN.PAINT"), key=lambda l: l["line_id"])
    by_el = {l["element_id"]: l for l in paint}
    pairs = []
    for r in pl["rows"]:
        el = r["element_id"]
        if not el.endswith(":PLASTER"):
            raise ManifestError(f"{r['line_id']}: element {el} is not a PLASTER face element")
        p = by_el.get(el[: -len(":PLASTER")] + ":PAINT")
        if p is None:
            raise ManifestError(f"{r['room']}: no FIN.PAINT line on the same face")
        pb = {"class": p["class"], "value": p["measured_net"], "held": [p["held_low"], p["held_high"]]}
        same = (r["before"]["class"], r["before"]["value"]) == (p["class"], p["measured_net"]) and (
            r["before"]["held_m2"] or [None, None]) == [p["held_low"], p["held_high"]]
        if not same:
            raise ManifestError(f"{r['room']}: plaster before is not its paint line: the shared-height cause is not "
                                "proven for this room")
        pairs.append({"room": r["room"], "plaster_line": r["line_id"], "paint_line": p["line_id"],
                      "paint_before": pb, "paint_expected_after": pb,
                      "plaster_expected_after": [r["v6_expected_after"]["held_low"],
                                                 r["v6_expected_after"]["held_high"]]})
    allp = [{"line_id": l["line_id"], "element_id": l["element_id"], "class": l["class"], "value": l["measured_net"],
             "held": [l["held_low"], l["held_high"]], "expected_after": "= before"} for l in paint]
    rel = sum((_d(l["measured_net"]) for l in paint if l["class"] == "RELEASED"), Decimal(0))
    return {"register": "ELEMENT_REGISTER 'WALL PLASTER HEIGHT vs PAINT HEIGHT': B5 plaster full height (slab / roof "
                        "underside), B6 paint to the finished ceiling (G1); only FIN.PLASTER moves",
            "pairs": pairs, "paint_lines": allp, "paint_lines_count": len(allp),
            "paint_released_before_m2": float(rel), "paint_released_after_m2": float(rel),
            "paint_lines_moved": 0}


# ------------------------------------------------------------------------------------------------- wiring row
def wiring_row(pl, bd, pa):
    """F-T555-3: the owning wiring item of the plaster correction (a Gate B package of its own)."""
    return {
        "id": "PLASTER_HEIGHT_V1_WIRING", "closes": "F-T555-3 (no owning row in V5)", "method": pl["method"],
        "candidate": M1.CANDIDATE, "gate": "B (integration package; a RELEASED line moving to HELD is a Gate B change "
                                          "of its own, never inside another package)",
        "steps": [
            f"1. {pl['released_lines']} RELEASED dry FIN.PLASTER lines {pl['released_before_m2']} m2 -> HELD (BOUNDED) "
            f"{pl['released_after_bound_m2']} m2 (held_low / held_high from T-556 new_lo / new_hi); FIN.PLASTER "
            f"released {pl['code_view']['FIN.PLASTER_released_now_m2']} -> "
            f"{pl['code_view']['FIN.PLASTER_released_after_m2']} m2",
            f"2. {pl['held_lines']} HELD lines: held_low / held_high = T-556 range (2 blank lines gain one)",
            f"3. {bd['count']} T-454 / T-489 bindings re-read ({bd['figure_changes']} figure changes: WALL_PLASTER "
            "mortar m3 bound beside; the rest read-only), each to its 'expected_after' in this manifest",
            f"4. FIN.PAINT: {pa['paint_lines_count']} lines byte-identical (paint stays at G1)",
            "5. every other candidate line byte-identical; HELD stays HELD (no plaster line is released)"],
        "order": "after T-498 (one candidate package at a time); T-423 r2 (paint / skirting) must not carry it",
        "blocked_by": "board row not yet opened (Lead); wrapper allow-list for candidate packages (T-498 / T-525)",
        "evidence_status": "PARTIALLY VERIFIED 2 / 11 rooms (Checker raw-DXF re-measure 1F-04, 2F-03; GF-15 by hand); "
                           "roof faces ASSUMED at the drawn-section scenario, HELD (D-39 / DCR-6)",
    }


def packages():
    return {
        "T-498 (S package)": {"v6_changes": [], "why": "T-550 / T-559 restate the blockwork reconciliation to cause; "
                                                       "ENGINE_WRONG none; no MAS line or glue host moves (V5 holds)"},
        "T-509 (B1-04 disposal)": {"v6_changes": [], "why": "no V6 piece touches B1 earthworks lines"},
        "T-423 r2 (paint / skirting)": {"v6_changes": [], "why": "FIN.PAINT unchanged (paint_unchanged); the plaster "
                                                                 "correction is PLASTER_HEIGHT_V1_WIRING only"},
        "T-363 / T-372 / T-513 / F package": {"v6_changes": [], "why": "no V6 piece moves their lines"},
        "PLASTER_HEIGHT_V1_WIRING (new, closes F-T555-3)": {"v6_changes": ["see wiring_row"],
                                                            "why": "T-556 merged; V5's T-552 bound superseded"},
    }


def v5_to_v6(pl, bd):
    out = []
    for r in pl["rows"]:
        out.append({"what": f"plaster {r['room']} {r['line_id']}", "v5": r["v5_expected_after"]["bound_m2"],
                    "v6": [r["v6_expected_after"]["held_low"], r["v6_expected_after"]["held_high"]],
                    "delta_m2": r["v5_to_v6_m2"], "cause": "T-556 (supersedes T-552 bound)"})
    out.append({"what": "plaster bindings", "v5": f"{bd['v5_stale']} stale named, none listed with an after",
                "v6": f"{bd['count']} listed one by one ({bd['figure_changes']} FIGURE, {bd['read_only_changes']} "
                      "READ_ONLY)", "cause": "T-556 + T-454 bound rule"})
    return out


def build(t556=None, bs=None):
    v5 = v5_manifest()
    M2.check_sources(PIECES)
    cov = M4.check_coverage(NEW_PIECES, V5_BASE, V6_BASE)
    if not set(NO_WIRING) <= set(NEW_PIECES):
        raise ManifestError("a NO_WIRING piece is not a piece of this manifest")
    if "T-556" in NO_WIRING:
        raise ManifestError("T-556 moves 11 lines: it is never a NO_WIRING piece")
    idx = M1.line_index()
    bs = bs if bs is not None else M5._t523()["bindings"]
    n_rule = reproduce_bound_rule(bs)
    pl = plaster_lines(idx, v5, t556)
    bd = bindings(pl, bs, v5)
    pa = paint_unchanged(idx, pl)
    man = {
        "schema": SCHEMA, "rule": RULE, "candidate": M1.CANDIDATE, "task": "T-558",
        "supersedes": "T-555 WIRING_MANIFEST_V5.json (every V5 / V4 / V3 / V2 statement carried unless listed in "
                      "v5_to_v6)",
        "coverage_rule": M4.RULE_COVERAGE, "coverage": cov,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in
                   (V5_JSON, T556, ROOT / M5.T523_MAP, ROOT / "research/agents_t454/t454_plaster_materials.py",
                    ROOT / "engine/source/plaster_materials_table_v1.py")},
        "pieces_new": {k: dict(v) for k, v in sorted(NEW_PIECES.items())}, "no_wiring": NO_WIRING,
        "bound_rule_reproduced_on": n_rule,
        "plaster_lines": pl, "bindings": bd, "paint": pa,
        "wiring_row": wiring_row(pl, bd, pa), "packages": packages(),
        "candidate_lines_moved_v5_to_v6": 0, "released_quantities_changed": 0, "candidate_files_touched": 0,
    }
    man["v5_to_v6"] = v5_to_v6(pl, bd)
    man["findings"] = [
        "F-T558-1: V5 named 58 stale plaster bindings and 74 unchanged, with no after; on T-556 all 132 bindings of "
        "the 11 lines are re-read (the 2 blank lines gain a held range), "
        f"{bd['figure_changes']} change a figure; listed one by one here",
        "F-T558-2: V5's expectation for the 11 lines was the T-552 bound; T-556 (Checker 10:20) supersedes it "
        "(GF-15 -2.19 .. -4.34 m2, W03 head above the paint line); a package built on V5 would carry a wrong bound",
        "F-T558-3: F-T555-3 now has an owning wiring item (PLASTER_HEIGHT_V1_WIRING); the Lead still has to open its "
        "board row (Gate B, after T-498)",
    ]
    return man


def pin():
    """the sha256 of the merged V5 (printed for the PIN constant; never written by build)."""
    return sha256(V5_JSON)


def dumps(man):
    return M1.dumps(man)


if __name__ == "__main__":
    if "--pin" in sys.argv:
        print(pin())
        sys.exit(0)
    m = build()
    if "--check" in sys.argv:
        ok = dumps(m) == OUT_JSON.read_text(encoding="utf-8")
        print("CHECK", "OK" if ok else "DIFFERS")
        sys.exit(0 if ok else 1)
    OUT_JSON.write_text(dumps(m), encoding="utf-8")
    print("written", OUT_JSON.relative_to(ROOT))
