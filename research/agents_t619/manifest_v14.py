"""T-619 WIRING MANIFEST V14 + OVERLAY DRY RUN (R-T619-1; lane I, non-candidate, research only).

V14 carries the fix rows of the tasks the Checker MERGED after V13 (T-611): T-608 (lift landing doors), T-610 (beam-beam
crossing zones), T-614 r2 (beam ends at narrow columns; it also withdraws FR-T610-3), T-616 (lintel residual: one cause
text), and lists T-612 / T-617 (statement only, 0 rows). It overlays them on a COPY of the ARCH_TAKEOFF_V3.0.58 line
index AFTER V2 .. V13 (the T-611 order; R-T580-1 / R-T588-1 / R-T593-1 / R-T596-1 / R-T604-1 / R-T611-1 code reused
read only). Nothing is wired; no candidate, released (V2.9 + route G), rule, knowledge or registry file is written; no
drawing is read: every figure comes from a committed, Checker-merged output or the Checker's verdict line, each named.

R-T619-1 (every villa on the engine's line-index scheme):
  (a) MERGED ONLY: a fix row enters only from a task MERGED with a Checker verdict (R-T596-1 (a) code); merged tasks
      whose rows move no line are listed with 0 rows; a task not merged is refused by name.
  (b) WITHDRAWN BY A LATER MERGED VERDICT: a fix row that a later merged Checker verdict withdraws (FR-T610-3 by T-614
      r2) enters with 0 rows and is listed; offering it as a row is refused.
  (c) A RANGE IS NEVER A POINT: a component the Checker carries as a range lo .. hi (FR-T610-1 B27: +0.011252 ..
      +0.012547 m3) enters as the line SET to before + lo AND a companion HELD line on the same element bounded 0 ..
      (hi - lo); the line total then reads lo .. hi. A range with hi <= lo, a SET to any other point, or a range row
      without its companion is refused.
  (d) ONE LINE, ONE PACKAGE: steps on one line chain inside one package (B27 takes FR-T610-1 then FR-T610-2; each step's
      before is the previous step's after); the source's per-row line changes must re-add to its stated net.
  (e) AN EXCLUSION IS EXCLUDED: a released opening that is not the item (lift landing door counted as a passage) leaves
      as EXCLUDED, never RELEASED 0; the family count after must equal the source's family total.
  (f) AN OMITTED ITEM WITH NO PRICED SCOPE IS HELD BLANK: the landing-door assembly enters as a HELD-blank line per
      storey with its count beside, trade HELD by name (never EXCLUDED as 'by others' without a printed note).
  (g) HELD WITHOUT AN OWNER LINE IS NOT WIRED: a held piece whose source names no owning line (FR-T614-H1) is listed by
      name with its bound, never placed on a guessed line and never 0.
  (h) Every line V14 does not write is identical to the V13 overlay; totals move only on the families V14 writes;
      FIN.SKIRTING stays at the V13 total.
Rebuild: `python3 -I research/agents_t619/manifest_v14.py` (`--check`).
"""

from __future__ import annotations

import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
T611_DIR = ROOT / "research/agents_t611"
if str(T611_DIR) not in sys.path:
    sys.path.insert(0, str(T611_DIR))

import manifest_v13 as M13                                            # noqa: E402  (R-T611-1, read only)

M12, M11, M10, M9, OV = M13.M12, M13.M11, M13.M10, M13.M9, M13.OV
D, S = M13.D, M13.S

SCHEMA = "URBAN_T619_WIRING_MANIFEST_V14"
RULE = "R-T619-1"
OUT_JSON = HERE / "out/WIRING_MANIFEST_V14.json"
IN = {
    "T608": ROOT / "research/agents_t608/out/T608_SCOPE_TABLE.json",
    "T610": ROOT / "research/agents_t610/out/T610_BEAM_OVERLAP_CENSUS.json",
    "T614": ROOT / "research/agents_t614/out/T614_BEAM_END_CENSUS.json",
    "T616": ROOT / "research/agents_t616/out/T616_RESIDUAL.json",
    "V13": T611_DIR / "out/WIRING_MANIFEST_V13.json",
    "V13_CODE": T611_DIR / "manifest_v13.py",
}
PINS = {
    "T608": "e138a0f3f7c6d9729f68399a10223ffb7ae6cfd9d859a7bca9a3a58befddd4a8",
    "T610": "8a146a0e2a9df2a8b91ac5373ef9ad341eef63cbad9a38a3c6f9c122cb985483",
    "T614": "ac0e64b82ef0f8bf14f6f450174bdc0f1e6e2336028da91dd4a717dce9b1c237",
    "T616": "0d1d1b06c96410238878d055beaa089ecc1474112094242327405c44d8c31922",
    "V13": "a78e73d770a4429eed1a62dce7d65cfffa781fb86db11c1bf35f84e9072990f9",
    "V13_CODE": "ab7f2736eb67865c6537af1ed9d1aa8234d94cb89565d8916224de3089614428",
}

# R-T619-1 (a): board MERGED verdicts at claim (2026-11-08T07:00Z; Verifier text abridged, full text on BOARD.md)
MERGED = {
    "T-608": {"merge": "3c3aa2f8",
              "verdict": "BOARD T-608 VERIFIER 2026-11-07T23:57Z (e): own read P7757 DXF GF / 1F / 2F: 4 panel lines "
                         "0 / 50 / 100 / 200 mm from the shaft face + shaft cross, stacked: LIFT_LANDING_DOOR x 3 AGREE "
                         "(DRAWING-CONFIRMED); FR-T608-1 ARCH.PASSAGE RELEASED 9 minus the 3 lift lines = 6 pcs AGREE; "
                         "landing-door supply ENGINE_OMISSION HELD-blank x 3 (FR-T608-2); no released quantity changed"},
    "T-610": {"merge": "14cf2579",
              "verdict": "BOARD T-610 VERIFIER 2026-11-07T21:59Z: own re-measure GF B1 x B27 zone 0.014761 m2 AGREE, "
                         "physical 0.014761 x 0.85 = 0.012547 m3; B1 component -0.005295 VERIFIED; B27 component "
                         "+0.011252 rests on the 0.001524 m2 tip attribution inside the model residual: bounded "
                         "+0.011252 .. +0.012547, FR-T610-1 PARTIALLY VERIFIED (1 / 2 line components); FR-T610-2 / -3 / "
                         "-4 NOT re-measured (worker-measured); fix rows enter the next manifest as PARTIALLY VERIFIED"},
    "T-614": {"merge": "a7f1f3af",
              "verdict": "BOARD T-614 VERIFIER 2026-11-08T05:59Z (r2): own re-measure GF CB8 col 2 east +0.002308 m3 "
                         "AGREE (FR-T614-3), GF B24 west end +0.037500 AGREE (FR-T614-4), 1F CB11 west end +0.000878 "
                         "AGREE (FR-T614-5); FR-T614-1 / -2 cited (Checker 03:55 AGREE); FR-T614-1..-5 ENGINE_WRONG "
                         "OMISSION total +0.061576 m3; col 2 west 0.00454 m2 HELD (bound 0.003405 m3); FR-T610-3 "
                         "WITHDRAWAL AGREE (CB8 BAND0040.1 bills no B27 zone)"},
    "T-616": {"merge": "17559e1b",
              "verdict": "BOARD T-616 VERIFIER 2026-11-08T01:00Z (f): no quantity moves; counts ENGINE_RIGHT 3 .. 5 / "
                         "UNRESOLVED 2 .. 4 named (P-GF-01, D-GF-05, A-GF-01 or D-GF-13, D-1F-01 / -06); W17 no "
                         "straight piece ENGINE_RIGHT AGREE; lintel add / drop none"},
    "T-612": {"merge": "66d3ad9c",
              "verdict": "BOARD T-612 VERIFIER 2026-11-07T22:02Z: GF outline ENGINE_RIGHT, -17.013904 lm UNRESOLVED; "
                         "no quantity change (FR-T612-1 statement only)"},
    "T-617": {"merge": "44ee93d5",
              "verdict": "BOARD T-617 VERIFIER 2026-11-08T04:58Z: head DRAWING-BOUNDED above, low end HELD; 0.000 m2 "
                         "on 1F-13 / 2F-01 / GF-08; FR-T617-1 band for the plaster wiring (T-558), nothing wired"},
}
NO_ROW = {
    "T-612": "FR-T612-1 restates the GF -16.913904 lm residual in the reconciled statement (+0.10 ENGINE_RIGHT + "
             "-17.013904 UNRESOLVED); no candidate line moves (statement V11, T-620)",
    "T-617": "FR-T617-1 is for the plaster wiring (T-558): Q-72 plaster keeps D - t 0.59 / 0.59 / 0.24 m2; the merged "
             "verdict moves 0.000 m2 on 1F-13 / 2F-01 / GF-08: no manifest line",
}
NOT_MERGED = {}

# R-T619-1 (b): withdrawn by a later merged verdict
WITHDRAWN = {"FR-T610-3": {"by": "T-614", "why": "CB8 BAND0040.1 does not bill the B27 x CB8 zone on its own extent; "
                                                 "billed once by B27 (owner, deeper); line change 0.000 instead of "
                                                 "-0.000692 m3 (T-614 r2 t610_fix_rows_r2, Checker AGREE)"}}

P_LIFT = "LIFT_LANDING_DOORS (T-608 FR-T608-1 / FR-T608-2)"
P_OVER = "BEAM_CROSSING_ZONES (T-610 FR-T610-1 / -2 / -4; FR-T610-3 withdrawn by T-614 r2)"
P_END = "BEAM_END_PIECES (T-614 r2 FR-T614-1 .. -5)"
P_LINT = "LINTEL_CAUSES (T-616 FR-T616-1)"
LIFT_CODE = "DOOR.LIFT_LANDING"
PASSAGE = ("ARCH.PASSAGE", "pcs")
BEAM = ("STR.CONC.BEAM", "m3")
RANGE_ROWS = {"FR-T610-1": "L-3dddf99008ab922da814"}      # the B27 component the Checker bounds
LINTEL_LINE = "L-d887eecf51c121831336"                    # LINTEL:P-GF-01 (STR.CONC.LINTEL m3, HELD blank)
SKIRT_V13 = "198.558592"
WRITES = {"STR.CONC.BEAM|m3", "ARCH.PASSAGE|pcs", f"{LIFT_CODE}|pcs"}


class ManifestError(Exception):
    pass


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def pins():
    for k, pin in PINS.items():
        if sha256(IN[k]) != pin:
            raise ManifestError(f"PIN: {IN[k].name} sha256 {sha256(IN[k])[:8]} is not the pinned {pin[:8]}")


def require_merged(task, merged=None):
    try:
        return M11.require_merged(task, MERGED if merged is None else merged)
    except M11.ManifestError as e:
        raise ManifestError(str(e)) from None


def no_row_sources(merged=None, no_row=None, not_merged=None):
    try:
        return M13.no_row_sources(MERGED if merged is None else merged, NO_ROW if no_row is None else no_row,
                                  NOT_MERGED if not_merged is None else not_merged)
    except M13.ManifestError as e:
        raise ManifestError(str(e)) from None


def _line(idx, lid, code_unit, cls=None):
    line = idx.get(lid)
    if line is None:
        raise ManifestError(f"{lid}: not in the index")
    if (line["item_code"], line.get("unit")) != code_unit:
        raise ManifestError(f"{lid}: {line['item_code']} {line.get('unit')} is not a {code_unit[0]} {code_unit[1]} line")
    if cls and line["class"] != cls:
        raise ManifestError(f"{lid}: {line['class']}, expected {cls}")
    return line


def _released_n(idx, code_unit):
    return sum(1 for l in idx.values() if (l["item_code"], l.get("unit")) == code_unit and l["class"] == "RELEASED")


# ---- R-T619-1 (e)/(f): lift landing doors ---------------------------------------------------------------------------

def lift_rows(t608, idx, merged=None, source="T-608"):
    src = require_merged(source, merged)
    fr = {r["id"]: r for r in t608["fix_rows"]}
    f1, f2 = fr["FR-T608-1"], fr["FR-T608-2"]
    if f1["kind"] != "SET" or f2["kind"] != "ADD":
        raise ManifestError("FR-T608-1 must be an exclusion SET and FR-T608-2 an ADD")
    ft = f1["family_total"]
    n_before = _released_n(idx, PASSAGE)
    if str(n_before) != ft["before"]:
        raise ManifestError(f"ARCH.PASSAGE released {n_before} is not the source's base {ft['before']} (stale)")
    if int(ft["before"]) - len(f1["lines"]) != int(ft["after"]):
        raise ManifestError(f"{ft['before']} - {len(f1['lines'])} lines != the source's after {ft['after']}")
    want = [o for o in f1["openings"]]
    got = [x[len("new: "):] if x.startswith("new: ") else None for x in f2["lines"]]
    if got != want:
        raise ManifestError(f"FR-T608-2 openings {got} are not FR-T608-1's {want}: one landing door per excluded line")
    rows = []
    for lid, opening in zip(f1["lines"], f1["openings"]):
        line = _line(idx, lid, PASSAGE, "RELEASED")
        if D(line["measured_net"]) != 1:
            raise ManifestError(f"{lid}: a passage line counts 1 pcs, not {line['measured_net']}")
        rows.append(M9.row(P_LIFT, "FR-T608-1", "SET", lid, OV.state(line), M9.excluded(), "DRAWING-CONFIRMED",
                           src["verdict"],
                           beside={"opening": opening, "kind": "LIFT_LANDING_DOOR (R-T608-1)",
                                   "who_is_right": "ENGINE_WRONG: a lift landing door is not a passage",
                                   "rule": "R-T608-1 / register LIFT LANDING DOOR"},
                           note="R-T619-1 (e): leaves as EXCLUDED, never RELEASED 0"))
    for lid, opening in zip(f1["lines"], f1["openings"]):
        elem = idx[lid]["element_id"]
        nid = f"NEW:{LIFT_CODE}:{elem}"
        rows.append(M9.row(P_LIFT, "FR-T608-2", "ADD", nid, None, M9.held(), "HELD", src["verdict"],
                           code=LIFT_CODE, unit="pcs", elem=elem,
                           beside={"opening": opening, "count_nr": "1 (DRAWING-CONFIRMED, T-608 own + Checker read)",
                                   "assembly": "frame + leaves + sill",
                                   "trade": "HELD: no printed note or spec names the lift package (T-608: 0 notes)",
                                   "never": "not priced in DOOR.INTERNAL.PVC; not EXCLUDED as 'by others' until a "
                                            "note / spec says so",
                                   "code": "DOOR.LIFT_LANDING chosen by lane I for the source's 'proposed "
                                           "DOOR.LIFT_LANDING'"},
                           note="R-T619-1 (f): HELD blank, count beside"))
    for r in rows:
        if r["row"] == "FR-T608-1" and r["after"]["class"] != "EXCLUDED":
            raise ManifestError(f"{r['line_id']}: an exclusion must be EXCLUDED")
    return rows


# ---- R-T619-1 (b)/(c)/(d): beam crossing zones -----------------------------------------------------------------------

def withdrawn_check(t614, withdrawn=None):
    """every withdrawn id is restated 0 by the later merged source; returns the listing."""
    w = WITHDRAWN if withdrawn is None else withdrawn
    r2 = {r["id"]: r for r in t614["t610_fix_rows_r2"]}
    text = {v.get("id"): v.get("restated", "") for v in t614.get("F_C_P02_5_r2", {}).values() if isinstance(v, dict)}
    out = {}
    for fid, why in w.items():
        require_merged(why["by"])
        r = r2.get(fid)
        if r is None or not r.get("changed_by_r2") or not text.get(fid, "").startswith("WITHDRAWN"):
            raise ManifestError(f"{fid}: the later source does not withdraw it")
        # the zone is billed once (by the owner) on the r2 extents: every non-owner line bills 0 of it
        owner = [k for k, v in r["billed_r2_m2"].items() if v]
        if len(owner) != 1 or r["billed_r2_m2"][owner[0]] != r["zone_m2"]:
            raise ManifestError(f"{fid}: r2 billing {r['billed_r2_m2']} is not 'billed once by one line'")
        out[fid] = {"by": why["by"], "merge": MERGED[why["by"]]["merge"], "rows": 0, "why": why["why"],
                    "t610_line_changes_m3": r["line_changes_t610_m3"]}
    return out


def overlap_rows(t610, t614, idx, merged=None, source="T-610", ranges=None, withdrawn=None, offered=None):
    """T-610 fix rows -> SET steps (chained per line in one package) + the companion HELD line of a ranged component."""
    src = require_merged(source, merged)
    ranges = RANGE_ROWS if ranges is None else ranges
    w = WITHDRAWN if withdrawn is None else withdrawn
    r2 = {r["id"]: r for r in t614["t610_fix_rows_r2"]}
    fixes = t610["fix_rows"] if offered is None else offered
    rows, state, checks = [], {}, []
    for fr in fixes:
        fid = fr["id"]
        if fid in w:
            if offered is not None:
                raise ManifestError(f"{fid}: withdrawn by {w[fid]['by']} (R-T619-1 (b)): no row")
            continue
        if fid in r2 and r2[fid].get("changed_by_r2"):
            raise ManifestError(f"{fid}: restated by T-614 r2 but not in the withdrawn list")
        ch = {k: D(str(v)) for k, v in fr["line_changes_m3"].items()}
        net = sum(ch.values(), Decimal(0))
        if net != -D(str(fr["engine_minus_physical_m3"])):
            raise ManifestError(f"{fid}: line changes re-add to {S(net)}, not the stated {fr['engine_minus_physical_m3']}")
        rng = None
        if fid in ranges:
            lid_r = ranges[fid]
            z = next((z for z in t610["zones"] if z.get("owner_deeper", {}).get("owner") == lid_r
                      and z["owner_deeper"]["lines"].get(lid_r, {}).get("change_m3") == fr["line_changes_m3"][lid_r]
                      and z["zone_m2"] == fr["zone_m2"]), None)
            if z is None:
                raise ManifestError(f"{fid}: no census zone carries the ranged component")
            zl = z["owner_deeper"]["lines"][lid_r]
            lo, hi = D(str(zl["change_m3"])), D(str(zl["should_m3"]))
            if hi <= lo:
                raise ManifestError(f"{fid}: range {S(lo)} .. {S(hi)} is a point or reversed (R-T619-1 (c))")
            if hi - lo != D(str(zl["engine_in_zone_m3"])):
                raise ManifestError(f"{fid}: width {S(hi - lo)} is not the attributed tip {zl['engine_in_zone_m3']}")
            rng = (lid_r, lo, hi)
        for lid in sorted(ch):
            line = state[lid] if lid in state else _line(idx, lid, BEAM, "RELEASED")
            before = OV.state(line)
            after_v = D(str(before["measured_net"])) + ch[lid]
            if after_v <= 0:
                raise ManifestError(f"{lid}: {before['measured_net']} + {S(ch[lid])} leaves nothing")
            ev = "VERIFIED" if (fid == "FR-T610-1" and lid != (rng[0] if rng else None)) else "PARTIALLY VERIFIED"
            beside = {"pair": fr["pair"], "storey": fr["storey"], "zone_m2": fr["zone_m2"], "change_m3": S(ch[lid]),
                      "verdict": fr["verdict"], "owner_deeper": fr["owner_deeper"],
                      "rule": "R-T610-1 (crossing zone billed once, by the deeper band)",
                      "component_evidence": ev}
            if rng and lid == rng[0]:
                beside["range_m3"] = f"{S(rng[1])} .. {S(rng[2])} (SET at the low end; companion HELD 0 .. "\
                                     f"{S(rng[2] - rng[1])}; R-T619-1 (c))"
            r = M9.row(P_OVER, fid, "SET", lid, before, M9.released(float(after_v)), "PARTIALLY VERIFIED",
                       src["verdict"], beside=beside, note="R-T619-1 (d): one package per line, steps chained")
            rows.append(r)
            state[lid] = dict(idx[lid] if lid not in state else state[lid], **r["after"])
            if rng and lid == rng[0]:
                elem = idx[lid]["element_id"] + f"#{fid}:RANGE"
                rows.append(M9.row(P_OVER, fid, "ADD", f"NEW:{BEAM[0]}:{elem}", None,
                                   M9.held(0.0, float(rng[2] - rng[1])), "PARTIALLY VERIFIED", src["verdict"],
                                   code=BEAM[0], unit=BEAM[1], elem=elem,
                                   beside={"range_of": lid, "low_m3": S(rng[1]), "high_m3": S(rng[2]),
                                           "why": "the B27 tip attribution 0.001524 m2 lies inside the Checker's "
                                                  "model residual: B27 billed 0 .. 0.001295 m3 of the zone before",
                                           "rule": "R-T619-1 (c): a range is never a point"},
                                   note="companion of the ranged SET; HELD 0 .. width"))
        checks.append({"fix_row": fid, "net_m3": S(net), "lines": {k: S(v) for k, v in ch.items()},
                       "range": None if rng is None else {"line": rng[0], "low": S(rng[1]), "high": S(rng[2])}})
    validate_ranges(rows, ranges)
    return rows, checks


def validate_ranges(rows, ranges=None):
    """R-T619-1 (c): every ranged SET has its companion HELD 0 .. width; no ranged row collapsed to a point."""
    ranges = RANGE_ROWS if ranges is None else ranges
    for fid, lid in ranges.items():
        sets = [r for r in rows if r["row"] == fid and r["line_id"] == lid and r["kind"] == "SET"]
        comp = [r for r in rows if r["row"] == fid and r["kind"] == "ADD" and r.get("beside", {}).get("range_of") == lid]
        if len(sets) != 1 or len(comp) != 1:
            raise ManifestError(f"{fid}: a ranged component needs one SET and one companion HELD line "
                                f"(found {len(sets)} / {len(comp)}): a range collapsed to a point is refused")
        c = comp[0]
        lo, hi = D(c["beside"]["low_m3"]), D(c["beside"]["high_m3"])
        a = c["after"]
        if a["class"] != "HELD" or D(a["held_low"]) != 0 or D(a["held_high"]) != hi - lo or hi <= lo:
            raise ManifestError(f"{fid}: companion is not HELD 0 .. {S(hi - lo)}")
        s = sets[0]
        if D(str(s["after"]["measured_net"])) - D(str(s["before"]["measured_net"])) != lo:
            raise ManifestError(f"{fid}: the ranged SET moves {s['before']['measured_net']} -> "
                                f"{s['after']['measured_net']}, not by the low end {S(lo)}")
    return True


# ---- T-614 r2: beam end pieces -------------------------------------------------------------------------------------

def end_rows(t614, idx, merged=None, source="T-614", taken=()):
    src = require_merged(source, merged)
    rows, tot = [], Decimal(0)
    for fr in t614["fix_rows"]:
        lid = fr["line_id"]
        if lid in taken:
            raise ManifestError(f"{fr['id']}: {lid} is written by another package (R1): chain it there")
        line = _line(idx, lid, BEAM, "RELEASED")
        ch = D(str(fr["change_m3"]))
        if ch <= 0:
            raise ManifestError(f"{fr['id']}: an omission adds concrete; {S(ch)} is not an add")
        before = OV.state(line)
        after_v = D(str(before["measured_net"])) + ch
        rows.append(M9.row(P_END, fr["id"], "SET", lid, before, M9.released(float(after_v)), "PARTIALLY VERIFIED",
                           src["verdict"],
                           beside={"mark": fr["mark"], "storey": fr["storey"], "column": fr["column"],
                                   "position": fr["position"], "piece_m2": fr["piece_m2"], "depth_m": fr["depth_m"],
                                   "change_m3": S(ch), "since": fr["since"],
                                   "who_is_right": "ENGINE_WRONG OMISSION (Checker AGREE)",
                                   "rule": "R-T614-1 / UP-CONC-JOINT-001 1.0.0 (beam face to face on drawn members)",
                                   "component_evidence": "VERIFIED (piece re-measured by the Checker); the line as a "
                                                         "whole stays PARTIALLY VERIFIED"},
                           note="piece added to the owning beam line; nothing inside a T-610 crossing zone"))
        tot += ch
    return rows, tot


def end_rulings(t614, idx, rows):
    """a T-614 piece written on one run of a ledger beam whose OTHER runs share the host: EXPLAINED only when every
    other run bills its own rectangle and nothing beyond (T-614 ledger_extents: ext_state and add_state NONE), so the
    piece at this run's end cannot sit in it. Otherwise the conflict stays UNEXPLAINED."""
    ext = {e["line_id"]: e for e in t614["ledger_extents"]}
    out = []
    for r in rows:
        h = OV.host(idx[r["line_id"]]["element_id"])
        others = sorted(k for k, l in idx.items() if k != r["line_id"] and l["class"] != "EXCLUDED"
                        and OV.layer(l["item_code"]) == OV.layer(BEAM[0]) and OV.host(l["element_id"]) == h
                        and l.get("unit") == BEAM[1])
        if not others:
            continue
        bad = [k for k in others if k not in ext or ext[k]["ext_state"] != "NONE" or ext[k]["add_state"] != "NONE"]
        if bad:
            raise ManifestError(f"{r['row']}: {h} shares the host with {bad}, whose extent is not its own rectangle")
        runs = {k: f"{ext[k]['run']} ({ext[k]['length_m']} m, rect {ext[k]['rect_m2']} m2)" for k in others}
        out.append({"layer": OV.layer(BEAM[0]), "host_re": "^" + h.replace(".", r"\.") + "$",
                    "sources": ["CANDIDATE", P_END],
                    "ruling": f"{r['row']} adds the {r['beside']['position']} piece at column {r['beside']['column']} "
                              f"to {r['line_id']}; the other run(s) of the same ledger beam {runs} bill only their own "
                              "rectangle (T-614 ledger_extents ext / add NONE): separate spans, no shared piece",
                    "fix_row": r["row"]})
    return out


def held_not_wired(t614):
    """R-T619-1 (g): held pieces with no owning line named by the source."""
    out = []
    for h in t614["held_rows"]:
        if h.get("line_id"):
            raise ManifestError(f"{h['id']}: names an owning line: wire it as a HELD component instead")
        b = D(str(h["bound_m3"]))
        if b <= 0:
            raise ManifestError(f"{h['id']}: a held piece with bound {S(b)} is no held piece")
        out.append({"id": h["id"], "storey": h["storey"], "marks": h["marks"], "column": h["column"],
                    "bound_m3": f"0 .. {S(b)}", "m2": h["undrawn_unbilled_m2"], "state": h["state"],
                    "wired": "NO: the source names no owning line; never placed on a guessed line, never 0"})
    return out


# ---- T-616: one cause text ----------------------------------------------------------------------------------------

def lintel_rows(idx, merged=None, source="T-616"):
    src = require_merged(source, merged)
    line = idx.get(LINTEL_LINE)
    if line is None or line["item_code"] != "STR.CONC.LINTEL" or line["element_id"] != "LINTEL:P-GF-01":
        raise ManifestError(f"{LINTEL_LINE}: not the P-GF-01 lintel line")
    if line["class"] != "HELD":
        raise ManifestError(f"{LINTEL_LINE}: {line['class']}: FR-T616-1 re-labels a HELD cause only")
    return [M9.row(P_LINT, "FR-T616-1", "TEXT_ONLY", LINTEL_LINE, OV.state(line), None, "HELD", src["verdict"],
                   beside={"cause_before": "head not established",
                           "cause_after": "HEAD_UNDER_BEAM: S1 band over the full width (S8.6 OP-GF-020), lintel "
                                          "0 .. 1, column jamb gives no masonry bearing",
                           "state": "unchanged HELD blank"},
                   note="T-616 s.5: cause text only")]


# ---- overlay ------------------------------------------------------------------------------------------------------

def v13_state():
    """the T-611 build up to its overlay (read only), so V14 steps from the exact V13 state."""
    M13.pins()
    idx, order12, rul, after12, rep12, t584 = M13.v12_state()
    t606 = M13._json(M13.IN["T606"])
    row = M13.floorless_row(t606["finding"], after12, M13.checker_length())
    order, _taken = M13.absorb_label(order12, row["line_id"], row["before"])
    order13 = order + [(M13.P_FLOOR, [row])]
    after13, rep13 = OV.apply(idx, order13, rul)
    return idx, order13, rul, after13, rep13, t584


def _pct(a, b):
    return format(((D(b) - D(a)) / D(a) * 100).quantize(Decimal("0.001")), "f")


def build():
    pins()
    t608, t610, t614, v13j = _json(IN["T608"]), _json(IN["T610"]), _json(IN["T614"]), _json(IN["V13"])
    idx, order13, rul, after13, rep13, t584 = v13_state()
    if len(after13) != v13j["overlay"]["lines"]["after_v13"]:
        raise ManifestError("V13 state rebuild differs from the committed V13 line count")
    for r in v13j["rows"]:
        if not OV.same_state(OV.state(after13[r["line_id"]]), r["after"]):
            raise ManifestError(f"{r['line_id']}: V13 rebuild differs from the committed V13 row")
    t13 = OV.totals(after13)
    if t13["FIN.SKIRTING|lm"] != v13j["skirting"]["FIN.SKIRTING|lm"]["v13"]:
        raise ManifestError("V13 FIN.SKIRTING totals rebuild differs from the committed V13")
    written13 = {op["line_id"] for _, ops in order13 for op in ops}
    sources, refused = no_row_sources()
    withdrawn = withdrawn_check(t614)
    lift = lift_rows(t608, after13)
    over, over_checks = overlap_rows(t610, t614, after13)
    end, end_total = end_rows(t614, after13, taken={r["line_id"] for r in over})
    lint = lintel_rows(after13)
    v14 = [(P_LIFT, lift), (P_OVER, over), (P_END, end), (P_LINT, lint)]
    rows14 = [r for _, rs in v14 for r in rs]
    hit = sorted({r["line_id"] for r in rows14} & written13)
    if hit:
        raise ManifestError(f"V14 writes lines an earlier package writes: {hit} (supersede by name first)")
    M9.validate_rows(rows14)
    order14 = order13 + v14
    rul14 = end_rulings(t614, after13, end)
    after14, rep = OV.apply(idx, order14, list(rul) + rul14)
    v14_lines = {r["line_id"] for r in rows14}
    others = sorted(k for k in set(after13) | set(after14) if k not in v14_lines and after13.get(k) != after14.get(k))
    if others:
        raise ManifestError(f"lines V14 does not write changed: {others[:5]}")
    t14 = OV.totals(after14)
    dt = OV.diff_totals(t13, t14)
    if set(dt) != WRITES:
        raise ManifestError(f"totals moved on {sorted(dt)}, V14 writes {sorted(WRITES)}")
    if t14["FIN.SKIRTING|lm"]["released"] != SKIRT_V13 or t14["FIN.SKIRTING|lm"] != t13["FIN.SKIRTING|lm"]:
        raise ManifestError("FIN.SKIRTING moved")
    if any(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]):
        raise ManifestError(f"unexplained conflicts: {[c for c in rep['conflicts'] if c['status'] == 'UNEXPLAINED']}")
    flagged = [r for r in rep["rows"] if r["status"] != "APPLIED"]
    if any(r["package"] in dict(v14) for r in flagged):
        raise ManifestError(f"a V14 row is not APPLIED: {[r for r in flagged if r['package'] in dict(v14)]}")
    # ARCH.PASSAGE
    pa13, pa14 = t13["ARCH.PASSAGE|pcs"], t14["ARCH.PASSAGE|pcs"]
    if (pa13["released"], pa14["released"], pa14["excluded_n"] - pa13["excluded_n"]) != ("9", "6", 3):
        raise ManifestError(f"ARCH.PASSAGE {pa13['released']} -> {pa14['released']}: not 9 -> 6 with 3 excluded")
    door = t14[f"{LIFT_CODE}|pcs"]
    if (door["held_n"], door["held_blank_n"], door["released_n"]) != (3, 3, 0):
        raise ManifestError(f"{LIFT_CODE}: not 3 HELD-blank lines")
    # B10 beam range
    b13, b14 = t13["STR.CONC.BEAM|m3"], t14["STR.CONC.BEAM|m3"]
    over_net = sum((D(c["net_m3"]) for c in over_checks), Decimal(0))
    d_rel = D(b14["released"]) - D(b13["released"])
    if d_rel != over_net + end_total:
        raise ManifestError(f"B10 released moved {S(d_rel)}, rows say {S(over_net + end_total)}")
    rng = next(c["range"] for c in over_checks if c["range"])
    width = D(rng["high"]) - D(rng["low"])
    if (b14["held_n"] - b13["held_n"], D(b14["held_low"]) - D(b13["held_low"]),
            D(b14["held_high"]) - D(b13["held_high"])) != (1, 0, width):
        raise ManifestError("B10 held moved by more than the one range companion")
    if b14["released_n"] != b13["released_n"] or b14["excluded_n"] != b13["excluded_n"]:
        raise ManifestError("B10 released / excluded line counts moved")
    status = {}
    for r in rep["rows"]:
        status.setdefault(r["package"], {}).setdefault(r["status"], 0)
        status[r["package"]][r["status"]] += 1
    t412 = M11.load_t412()
    nrows, _ = M11.nosing_ledger(t412, M11._json(M11.IN["T598"]))
    cen = M9.census_on(after14, M11.census_edges(t412, nrows), t584, {M9.E1_LINE: ("ST-03", "E1")})
    if cen["doubles"] or cen["orphans"]:
        raise ManifestError("stair census doubles / orphans after V14")
    rel13, rel14 = D(b13["released"]), D(b14["released"])
    table = []
    for r in rows14:
        b, a = r.get("before"), r.get("after")
        table.append({"row": r["row"], "kind": r["kind"], "line_id": r["line_id"],
                      "item": r.get("item_code") or after13.get(r["line_id"], {}).get("item_code"),
                      "before": None if b is None else {k: b[k] for k in ("class", "measured_net", "held_low",
                                                                            "held_high")},
                      "after": None if a is None else {k: a[k] for k in ("class", "measured_net", "held_low",
                                                                           "held_high")},
                      "evidence": r["evidence"]["status"]})
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-619", "candidate": M9.T580.CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in IN.values()},
        "sources_merged": {k: v["merge"] for k, v in MERGED.items()},
        "sources_no_row": sources, "sources_refused": refused, "withdrawn": withdrawn,
        "held_not_wired": held_not_wired(t614),
        "line_table": table,
        "rows": [dict(r) for r in rows14],
        "beam_b10": {
            "STR.CONC.BEAM|m3": {"v13": b13, "v14": b14},
            "fix_rows": over_checks,
            "end_pieces_m3": S(end_total),
            "released_delta_m3": S(d_rel),
            "pct_vs_v13": _pct(rel13, rel14),
            "after_total_range_m3": f"{S(rel14)} .. {S(rel14 + width)} released (+ the FR-T610-1 companion "
                                    f"0 .. {S(width)}); pre-existing HELD {b13['held_low']} .. {b13['held_high']} "
                                    f"unchanged beside",
            "hand": f"{S(rel13)} + {S(over_net)} (T-610 FR-1 low / FR-2 / FR-4) + {S(end_total)} (T-614 FR-1 .. -5) "
                    f"= {S(rel14)} .. {S(rel14 + width)}",
            "not_wired": "FR-T614-H1 HELD 0 .. 0.003405 m3 (no owning line named); GF CB4 BAND0021.1.r2 +0.01355 m3 "
                         "possible double billing (T-614 open, named for the T-610 / T-229 owners, not a fix row); "
                         "1F CB10 crossing zone HELD with its line (T-610)",
        },
        "passage": {"ARCH.PASSAGE|pcs": {"v13": pa13, "v14": pa14},
                    "hand": "9 released - 3 lift landing lines (GF OP-011, 1F OP-007, 2F OP-002) = 6 pcs"},
        "lift_landing_door": {f"{LIFT_CODE}|pcs": door,
                              "note": "3 HELD-blank lines, count 1 beside each, trade HELD by name"},
        "skirting": {"FIN.SKIRTING|lm": t14["FIN.SKIRTING|lm"], "v13_released": SKIRT_V13,
                     "unchanged": "T-608: skirting at the landing doors correct; V14 writes no skirting line"},
        "overlay": {
            "lines": {"base": len(idx), "after_v13": len(after13), "after_v14": len(after14)},
            "order": [{"package": n, "ops": len(o), "status": status.get(n, {})} for n, o in order14],
            "flagged_rows": flagged,
            "stale": sum(r["status"] == "STALE" for r in rep["rows"]),
            "two_package_lines": 0,                     # OV.apply raises R1 otherwise
            "unexplained_conflicts": sum(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]),
            "conflicts": [c for c in rep["conflicts"] if any(l in v14_lines for l in c["lines"])],
            "rulings_v14": rul14,
            "other_lines_changed_vs_v13_overlay": others,
            "v14_vs_v13_totals": dt,
        },
        "stair_edge_census_after_v14": {"edges": cen["edges"], "doubles": len(cen["doubles"]),
                                        "orphans": len(cen["orphans"])},
        "findings": {
            "F-T619-1": "the B27 line takes two crossing-zone steps (FR-T610-1 low end, FR-T610-2) in one package; the "
                        "FR-T610-1 high end is carried by a companion HELD line 0 .. 0.001295 m3, so the B10 total "
                        "reads as a range until the B27 tip attribution is re-measured",
            "F-T619-2": "FR-T614-H1 (GF CB8 col 2 west, 0.00454 m2, bound 0.003405 m3) names no owning line: listed, "
                        "not wired; the T-614 owner (lane S) to name the line before it can enter",
        },
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str) + "\n"


def main(argv):
    text = dumps(build())
    if "--check" in argv:
        ok = OUT_JSON.exists() and OUT_JSON.read_text(encoding="utf-8") == text
        print("T-619 manifest V14: committed output", "is the rebuild" if ok else "DIFFERS from the rebuild")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
