"""T-641 WIRING MANIFEST V17 + OVERLAY DRY RUN (R-T641-1; lane I, non-candidate, research only).

V17 carries into the overlay the fix rows verdicted after V16 (T-631, MERGED; claim 2026-11-08T21:01Z):
  - F-T631-1 (V16 finding, Lead row T-641): the floor BED on the two T-625 hosts follows the porcelain finish it lies
    under: GF bed m2 L-20a8e714 takes the same two steps as the GF porcelain (-0.013272 footprint, -0.393843 strings low
    end) and the same companion HELD 0 .. 0.393843; the 1F bed m2 L-ebce765b takes the 1F margin companion HELD 0 ..
    0.376. The bed MORTAR m3 lines follow their bed area by the candidate's own Q-45 floor bed range 0.03 .. 0.04 m
    (checked on both lines before any step: 109.478417 x 0.03 / 0.04 = 3.284353 / 4.379137; 33.411036 x 0.03 / 0.04 =
    1.002331 / 1.336441): line low = low-end area x 0.03, high = low-end area x 0.04, companion HELD 0 .. width x 0.04.
  - F-T628-1 (T-628 MERGED a7ee000d, Verifier 15:55Z, own re-measure AGREE): the boundary-wall foundation band line
    L-6290a9f3 HELD 7.2204 .. 7.2204 (UNSUPPORTED BASIS DG-6dd9f1ca, one plot side lost) -> HELD 5.6392 .. 11.0328 m3
    (free 70.49 x 0.20 x 0.40 .. centre line 91.94 x 0.20 x 0.60, Q-28): the footing-line bound 77.1204 .. 77.8432 ->
    75.5392 .. 81.6556 m3. Class HELD unchanged, never a point.
  - T-638 (MERGED 175443b8, Verifier 18:05Z): 54 A_FIX formwork rows +33.127058 m2: 4 GF column shafts 27.002 VERIFIED
    (Checker 4 / 4 components) each with its joint-face companion HELD (R-T638-1 RELEASE_LOW_END), 50 split-member walk
    faces 6.125058 m2 carried PARTIALLY VERIFIED, status CALCULATED (F-C-T638-1: never VERIFIED until a REST piece is
    re-walked). Every concrete line each face binds to is checked RELEASED here (R-T638-1).
  - T-639 (MERGED e31e38b5, Verifier 19:59Z): FR-T639-1 .. -6 GF column main bars 58 T16 x 4.50 m = 412.444444 kg
    (Checker own schedule read AGREE): 6 HELD blank kg lines RELEASED.
  - T-640 (MERGED 36f53264, Verifier 17:04Z): 33 A_BOUND fix rows HELD blank -> HELD bounded, 87.234 .. 138.53962 m2
    (bounds only, never a point); the 27 return-paint rows chain inside RETURN_PAINT_FACES, the package that added them
    (R1). Each return paint high end is checked equal to its named RELEASED plaster face.
Listed with 0 rows: T-626 (roof residual split TOLERANCE 0.001332 + UNRESOLVED 0.521668 m2 on his lump row: no line),
T-627 (windows ENGINE_RIGHT 3.975 m2 confirmed; F-T627-1 RULED, Verifier 16:56Z: three door heights 2.20 ENGINE_RIGHT,
0.580 m2 RULE_DIFFERENCE -> ENGINE_RIGHT, engine already = own: a statement class move, no line), T-634 (GF-15 W03
glazing -0.015161 m2 is an opening-ledger figure inside a TOLERANCE line residual, Checker 'opening ledger only'; the 26
door returns 23.069556 vs 23.07 m2 -0.000444 TOLERANCE; paint-return bracket 19.17 .. 23.069556 listed, the T-640 per-line
low 0 stands, Checker OP-021), T-640 FR-T640-30 / -31 (RETIRE proposals, not ruled), T-639 F-T639-1 (T-643's row).
Refused by name (not MERGED at claim): T-637 (READY r2), T-644 (READY), T-642 / T-643 (TODO).

R-T641-1 (every villa on the engine's line-index scheme):
  (a) MERGED ONLY (R-T631-1 (a)); merged tasks with no line move are listed with 0 rows; unmerged refused by name.
  (b) ONE WRITER PER LINE (R1): a row on a line an earlier package writes chains inside that package.
  (c) THE BED FOLLOWS ITS FINISH: on every floor host whose finish m2 an overlay package moves, the bed m2 of the same
      host takes the same steps and companions (equal before, equal after), and the bed mortar m3 follows the bed area by
      the thickness range the candidate line already carries (proved from the line, never typed); a finish moved without
      its bed, or a bed whose thickness range is not the line's, is refused.
  (d) A HELD BOUND REPLACED BY A MERGED DRAWING RANGE STAYS HELD with both ends (never a point, never released).
  (e) A CENSUS FIX ROW ENTERS AS ITS MERGED SOURCE STATES IT (before checked against V16, after = the stated state);
      evidence is capped by the verdict: a CALCULATED face the Checker did not re-measure is PARTIALLY VERIFIED, never
      VERIFIED; a face is released only when every concrete line it binds to is RELEASED.
  (f) A proposal the Checker did not rule (RETIRE_CARRIED), a statement class move with no line change, and a TOLERANCE
      residual are listed with their figures, never wired.
  (g) Every line V17 does not write is identical to the V16 overlay; totals move only on the keys V17 writes.
Rebuild: pytest-driven writer (tests/t641_manifest_v17, URBAN_T641_WRITE=1); `--check` compares.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
T631_DIR = ROOT / "research/agents_t631"
if str(T631_DIR) not in sys.path:
    sys.path.insert(0, str(T631_DIR))

import manifest_v16 as M16                                            # noqa: E402  (R-T631-1, read only)

M15, M9, OV = M16.M15, M16.M9, M16.OV
D, S = M16.D, M16.S

SCHEMA = "URBAN_T641_WIRING_MANIFEST_V17"
RULE = "R-T641-1"
OUT_JSON = HERE / "out/WIRING_MANIFEST_V17.json"
IN = {
    "T628": ROOT / "research/agents_t628/out/T628_FOOTING_LIFT_ROWS.json",
    "T638": ROOT / "research/agents_t638/out/FORMWORK_HOLD_CENSUS_T638.json",
    "T639": ROOT / "research/agents_t639/out/REBAR_HOLD_CENSUS_T639.json",
    "T640": ROOT / "research/agents_t640/out/HOLD_CENSUS_T640.json",
    "T634": ROOT / "research/agents_t634/out/T634_PLASTER_PAINT_REMEASURE.json",
    "T627": ROOT / "research/agents_t627/out/T627_ROW_EVIDENCE.json",
    "T626": ROOT / "research/agents_t626/out/T626_ROW_EVIDENCE.json",
    "V16": T631_DIR / "out/WIRING_MANIFEST_V16.json",
    "V16_CODE": T631_DIR / "manifest_v16.py",
}
PINS = {
    "T628": "281d95f44cd9293a15206025ce0289968aa41523cfd115f6f595158bb55e5c75",
    "T638": "a75276c82547c7ccb3630fc1960ff38f2baceb2380afdabc03a3bccd8ea137c7",
    "T639": "0555f732893dd7d3ea812b33ab7a20e4cf600d251770a02dbfd7dc5d09989c69",
    "T640": "390a7602e3a0c2bbad93369edb713c12af49adb9cbdc1473bf2bc55dc6ed7ed8",
    "T634": "5d678d5458cd2dd5d37f3c0269db9190f4cabacc31ac797e53a0f8c2b3c26139",
    "T627": "491f2f7fbfbf2208d4a5793224364b21e2ffb072b335886411a6b638bddf81bf",
    "T626": "717b9f55c8363c8044ee818bfd11d840acfb1ef532c940b6571bf34c553f1bbf",
    "V16": "be619bf1cc08e9fad82a985213f5bc4e512f738e273152bf0bd3088b9d218f4f",
    "V16_CODE": "799f8a991d7256e6645c032b138d0ab3e31a019e95ca5d86c18229885bdb33c4",
}

# R-T641-1 (a): board MERGED verdicts at claim (2026-11-08T21:01Z; Verifier text abridged, full text on BOARD.md)
MERGED = {
    "T-626": {"merge": "74e52c34",
              "verdict": "BOARD T-626 VERIFIER 2026-11-08T13:59Z: classes stand; +4.30 annex TOLERANCE 0.001332 accepted; "
                         "residual 0.521668 UNRESOLVED on his lump row; no line moved"},
    "T-627": {"merge": "a7ee000d",
              "verdict": "BOARD T-627 VERIFIER 2026-11-08T15:57Z + F-T627-1 RULED 16:56Z: windows ENGINE_RIGHT 3.975 "
                         "confirmed; D-GF-01 / -03 / -06 heights 2.20 own DWF read (6.3801 vs engine 6.380 AGREE): 0.580 m2 "
                         "RULE_DIFFERENCE 0.960 -> 0.380, ENGINE_RIGHT -1.720 -> -1.140 for the next statement / manifest"},
    "T-628": {"merge": "a7ee000d",
              "verdict": "BOARD T-628 VERIFIER 2026-11-08T15:55Z: band own re-measure: ring 91.94 x 0.20, free 70.49 m: "
                         "range 5.6392 .. 11.0328 AGREE; F-T628-1: 7.2204 UNSUPPORTED (DG-6dd9f1ca), line bounded "
                         "75.5392 .. 81.6556"},
    "T-631": {"merge": "V16", "verdict": "BOARD T-631 VERIFIER: V16 MERGED (the base); F-T631-1 for the Lead"},
    "T-634": {"merge": "52230429",
              "verdict": "BOARD T-634 VERIFIER 2026-11-08T19:59Z: W03 own 5.10186 m AGREE, ledger 5.106 ENGINE_WRONG "
                         "-0.00414 m (opening ledger only, line within tolerance); paint-return finding 19.17 .. 23.07 "
                         "endorsed for the T-569 wiring row; no line moved"},
    "T-638": {"merge": "175443b8",
              "verdict": "BOARD T-638 VERIFIER 2026-11-08T18:05Z: column shafts COL-GF-01 / -02 / -03 / -09 27.002 m2 "
                         "VERIFIED (4 / 4 components); 50 split-member faces 6.125058 m2 stay CALCULATED (F-C-T638-1: "
                         "carry as CALCULATED, not VERIFIED)"},
    "T-639": {"merge": "e31e38b5",
              "verdict": "BOARD T-639 VERIFIER 2026-11-08T19:59Z: GR rows C2 / C4 / C5 / C9 own attribute dump: counts "
                         "and diameters of FR-T639-1 .. 6 AGREE; 58 bars x 4.50 = 261 m -> 412.444444 kg AGREE"},
    "T-640": {"merge": "36f53264",
              "verdict": "BOARD T-640 VERIFIER 2026-11-08T17:04Z: 72 / 72 classed; A_BOUND 33 -> fix rows HELD bounded "
                         "87.234 .. 138.540 m2; OP-021 paint 0 .. 1.40 own AGREE, low end 0 stands; ST_2F plaster own"},
}
NO_ROW = {
    "T-626": "roof residual split TOLERANCE 0.001332 + UNRESOLVED 0.521668 m2 sits on his lump row: no engine line moves",
    "T-627": "windows ENGINE_RIGHT 3.975 m2 confirmed; doors 0.580 m2 RULE_DIFFERENCE -> ENGINE_RIGHT (engine = own "
             "6.380 m2): a statement class move (statement V12, T-635), no line",
    "T-631": "manifest V16: the base of V17 (rebuilt and compared, not restated)",
    "T-634": "GF-15 W03 -0.015161 m2 is an opening-ledger figure inside the line's TOLERANCE residual (line 56.0131 vs own "
             "56.018968, -0.005868); returns 23.069556 vs 23.07 (-0.000444) TOLERANCE; paint-return bracket listed",
}
NOT_MERGED = {"T-637": "READY r2 at claim (BOQ_FAMILY_MASTER 1.56.0)", "T-644": "READY at claim (B9-02 lintel pieces)",
              "T-642": "TODO at claim (P02 / P04 + parapet)", "T-643": "TODO at claim (rebar on HELD concrete, F-T639-1)"}

GF_PORC, F1_PORC = M16.GF_PORC, M16.F1_PORC
BAND_LINE = "L-6290a9f3d93f38cd46d6"
BAND = ("STR.CONC.BOUNDARY_WALL", "m3")
P_STAIR = M16.P_STAIR
P_RET = "RETURN_PAINT_FACES"
P_BED = "FLOOR_BED_FOLLOWS_FINISH (T-641 F-T631-1)"
P_BAND = "FOOTING_BAND_RANGE (T-628 F-T628-1)"
P_FW = "FORMWORK_HOLD_RELEASE (T-638 FR-T638-1 .. -54)"
P_BARS = "GF_COLUMN_MAIN_BARS (T-639 FR-T639-1 .. -6)"
P_FIN = "FINISH_HOLD_BOUNDS (T-640 FR-T640-n)"
Q6 = Decimal("0.000001")
FOOT_STATEMENT = (Decimal("77.1204"), Decimal("77.8432"))


class ManifestError(Exception):
    pass


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def q6(x):
    return Decimal(x).quantize(Q6, rounding=ROUND_HALF_UP)


def pins():
    for k, pin in PINS.items():
        if sha256(IN[k]) != pin:
            raise ManifestError(f"PIN: {IN[k].name} sha256 {sha256(IN[k])[:8]} is not the pinned {pin[:8]}")


def require_merged(task, merged=None):
    m = MERGED if merged is None else merged
    if task not in m or not m[task].get("merge") or not m[task].get("verdict"):
        raise ManifestError(f"{task} is not MERGED with a Checker verdict: its rows cannot enter a manifest")
    return m[task]


def no_row_sources(merged=None, no_row=None, not_merged=None):
    m = MERGED if merged is None else merged
    out = {t: {"merge": require_merged(t, m)["merge"], "rows": 0, "why": why}
           for t, why in (NO_ROW if no_row is None else no_row).items()}
    refused = {}
    for t, why in (NOT_MERGED if not_merged is None else not_merged).items():
        if t in m:
            raise ManifestError(f"{t} is listed as not merged but carries a merge: build its rows")
        refused[t] = {"refusal": f"{t} is not MERGED with a Checker verdict", "state": why}
    return out, refused


def writer_of(order, lid):
    return M16.writer_of(order, lid)


def _st(x):
    """a stated state (strings or numbers) as an index state of floats / None."""
    return {k: (x.get(k) if k == "class" else (None if x.get(k) is None else float(D(x.get(k))))) for k in OV.QFIELDS}


def _live(idx, lid, code=None, unit=None):
    line = idx.get(lid)
    if line is None:
        raise ManifestError(f"{lid}: not in the index")
    if code and (line["item_code"], line.get("unit")) != (code, unit):
        raise ManifestError(f"{lid}: {line['item_code']} {line.get('unit')} is not {code} {unit}")
    return line


def _before_ok(idx, lid, stated):
    line = idx.get(lid)
    if line is None or not OV.same_state(OV.state(line), _st(stated)):
        raise ManifestError(f"{lid}: stated before {stated} is not the V16 state {OV.state(line) if line else None} "
                            "(stale source)")
    return line


# ---- F-T631-1: the bed follows its finish ---------------------------------------------------------------------------

def finish_moves(rows, finish_lines):
    """from the overlay rows that moved the floor finish: per finish line, its ordered SET deltas and companion widths."""
    out = {f: {"steps": [], "companions": []} for f in finish_lines}
    for r in rows:
        if r["kind"] == "SET" and r["line_id"] in out:
            b, a = D(r["before"]["measured_net"]), D(r["after"]["measured_net"])
            if b is None or a is None:
                raise ManifestError(f"{r['line_id']}: a finish step without a released value")
            out[r["line_id"]]["steps"].append((r["row"], q6(a - b)))
        elif r["kind"] == "ADD" and (r.get("beside") or {}).get("range_of") in out:
            a = r["after"]
            if a["class"] != "HELD" or D(a["held_low"]) != 0:
                raise ManifestError(f"{r['line_id']}: a finish companion that is not HELD 0 .. width")
            out[r["beside"]["range_of"]]["companions"].append((r["row"], D(a["held_high"])))
    return out


def bed_of(idx, finish_lid):
    """the bed m2 and bed m3 lines on the finish line's host (element '<finish element>:bed'), exactly one each."""
    fe = idx[finish_lid]["element_id"]
    found = {}
    for k, l in idx.items():
        if l["class"] != "EXCLUDED" and l["element_id"] == fe + ":bed" and l["item_code"].startswith("FIN.FLOOR.BED"):
            if l.get("unit") in found:
                raise ManifestError(f"{fe}: two live bed lines in {l.get('unit')} ({found[l['unit']]}, {k})")
            found[l.get("unit")] = k
    if set(found) != {"m2", "m3"}:
        raise ManifestError(f"{fe}: bed lines {sorted(found)} are not one m2 and one m3 line")
    return found["m2"], found["m3"]


def bed_thickness(m2_value, m3_line):
    """the floor-bed thickness range the m3 line already carries, proved from the line (never typed): (0.03, 0.04)."""
    a, lo, hi = D(m2_value), D(m3_line["held_low"]), D(m3_line["held_high"])
    if m3_line["class"] != "HELD" or lo is None or hi is None:
        raise ManifestError(f"{m3_line['line_id']}: bed mortar is not a HELD range")
    for t_lo, t_hi in ((Decimal("0.03"), Decimal("0.04")),):     # Q-45 floor bed 3 .. 4 cm (AGENT_BRIEF)
        if q6(a * t_lo) == lo and q6(a * t_hi) == hi:
            return t_lo, t_hi
    raise ManifestError(f"{m3_line['line_id']}: {S(lo)} .. {S(hi)} m3 is not {S(a)} m2 x the Q-45 floor bed 0.03 .. 0.04")


def bed_rows(idx_v15, idx_v16, order, moves, merged=None, source="T-625"):
    """R-T641-1 (c): the bed m2 takes the finish steps and companions; the mortar follows the bed area."""
    src = require_merged(source, merged)
    rows, rulings, hand = [], [], []
    for fin, mv in moves.items():
        if not mv["steps"] and not mv["companions"]:
            continue
        m2, m3 = bed_of(idx_v16, fin)
        for lid in (m2, m3):
            if writer_of(order, lid):
                raise ManifestError(f"{lid}: written by {writer_of(order, lid)}: chain it there (R1)")
        f0, b0 = idx_v15[fin], idx_v16[m2]
        if b0["class"] != "RELEASED" or D(b0["measured_net"]) != D(f0["measured_net"]):
            raise ManifestError(f"{m2}: bed {b0['measured_net']} is not the finish {f0['measured_net']} before the move")
        t_lo, t_hi = bed_thickness(b0["measured_net"], idx_v16[m3])
        cur2, cur3, area = OV.state(b0), OV.state(idx_v16[m3]), D(b0["measured_net"])
        steps = []
        for fid, delta in mv["steps"]:
            area = area + delta
            ev = "HELD" if fid == mv["steps"][-1][0] and mv["companions"] and any(c[0] == fid for c in mv["companions"]) \
                else "PARTIALLY VERIFIED"
            a2 = M9.released(float(area))
            rows.append(M9.row(P_BED, f"{fid}/BED", "SET", m2, cur2, a2, ev, src["verdict"],
                               beside={"follows": f"{fin} {fid} {S(delta)} m2", "change_m2": S(delta),
                                       "rule": "R-T641-1 (c): the bed m2 takes the finish step"},
                               note="F-T631-1"))
            a3 = M9.held(float(q6(area * t_lo)), float(q6(area * t_hi)))
            rows.append(M9.row(P_BED, f"{fid}/MORTAR", "SET", m3, cur3, a3, "HELD", src["verdict"],
                               beside={"follows": f"{m2} {S(area)} m2", "thickness_m": f"{S(t_lo)} .. {S(t_hi)}",
                                       "hand": f"{S(area)} x {S(t_lo)} = {S(q6(area * t_lo))}; x {S(t_hi)} = "
                                               f"{S(q6(area * t_hi))}",
                                       "rule": "R-T641-1 (c): the mortar follows the bed area (Q-45 floors 3 .. 4 cm)"},
                               note="F-T631-1"))
            cur2, cur3 = a2, a3
            steps.append(f"{fid} {S(delta)}")
        for fid, width in mv["companions"]:
            for unit, lid, w in (("m2", m2, width), ("m3", m3, q6(width * t_hi))):
                elem = idx_v16[lid]["element_id"] + f"#{fid}:RANGE"
                rows.append(M9.row(P_BED, f"{fid}/BED-{unit}", "ADD", f"NEW:{idx_v16[lid]['item_code']}:{unit}:{elem}", None,
                                   M9.held(0.0, float(w)), "HELD", src["verdict"], code=idx_v16[lid]["item_code"],
                                   unit=unit, elem=elem,
                                   beside={"range_of": lid, "width": S(w),
                                           "hand": S(width) + (f" m2 x {S(t_hi)} = {S(w)} m3" if unit == "m3" else " m2"),
                                           "rule": "R-T641-1 (c): the bed carries the finish companion"},
                                   note="companion of the bed beside its finish companion"))
            if not any(r["line_id"] in (m2, m3) for r in rows if r["kind"] == "SET"):
                host = OV.host(idx_v16[m2]["element_id"])
                if any(x["host_re"] == "^" + re.escape(host) + "$" for x in rulings):
                    raise ManifestError(f"{host}: two companion rulings on one bed host")
                rulings.append({"layer": OV.layer(idx_v16[m2]["item_code"]), "host_re": "^" + re.escape(host) + "$",
                                "sources": ["CANDIDATE", P_BED],
                                "ruling": f"{fid} bed companions HELD 0 .. {S(width)} m2 / 0 .. {S(q6(width * t_hi))} m3 "
                                          f"beside their own bed lines {m2} / {m3} (unchanged): range widths, never a "
                                          "second bed",
                                "fix_row": f"{fid}/BED"})
        hand.append({"finish": fin, "bed_m2": m2, "bed_m3": m3, "steps": steps,
                     "companions": [f"{c[0]} 0 .. {S(c[1])}" for c in mv["companions"]],
                     "thickness_m": [S(t_lo), S(t_hi)]})
    return rows, rulings, hand


def bed_follows(idx, finish_lines):
    """R-T641-1 (c) acceptance on an overlay result: bed m2 == finish m2 (line and companions); mortar on the bed."""
    out = []
    for fin in finish_lines:
        fe = idx[fin]["element_id"]
        m2, m3 = bed_of(idx, fin)
        if idx[m2]["class"] != idx[fin]["class"] or D(idx[m2]["measured_net"]) != D(idx[fin]["measured_net"]):
            raise ManifestError(f"{fe}: finish {idx[fin]['measured_net']} moved without its bed {idx[m2]['measured_net']}")

        def comps(prefix):
            return sorted(D(l["held_high"]) for k, l in idx.items() if l["class"] == "HELD"
                          and l["element_id"].startswith(prefix + "#") and l["element_id"].endswith(":RANGE")
                          and l.get("unit") == "m2" and l["item_code"] == idx[fin if prefix == fe else m2]["item_code"])
        cf, cb = comps(fe), comps(fe + ":bed")
        if cf != cb:
            raise ManifestError(f"{fe}: finish companions {[S(x) for x in cf]} are not the bed's {[S(x) for x in cb]}")
        t_lo, t_hi = bed_thickness(idx[m2]["measured_net"], idx[m3])          # the mortar sits on the bed area
        c3 = sorted(D(l["held_high"]) for l in idx.values() if l["class"] == "HELD" and l.get("unit") == "m3"
                    and l["element_id"].startswith(fe + ":bed#") and l["element_id"].endswith(":RANGE"))
        if c3 != [q6(x * t_hi) for x in cb]:
            raise ManifestError(f"{fe}: bed mortar companions {[S(x) for x in c3]} do not follow the bed's")
        out.append({"host": fe, "finish": S(D(idx[fin]["measured_net"])), "bed": S(D(idx[m2]["measured_net"])),
                    "companions_m2": [S(x) for x in cf], "mortar_m3": [S(D(idx[m3]["held_low"])),
                                                                      S(D(idx[m3]["held_high"]))],
                    "mortar_companions_m3": [S(x) for x in c3]})
    return out


# ---- F-T628-1: the boundary-wall foundation band -------------------------------------------------------------------

def band_row(t628, idx, order, merged=None, source="T-628"):
    src = require_merged(source, merged)
    fr = next((f for f in t628["fix_rows"] if f["id"] == "F-T628-1"), None)
    row = next((r for r in t628["lines"]["T-551/footing-line"]["rows"]
                if (r.get("evidence") or {}).get("held_line") == BAND_LINE), None)
    if fr is None or row is None:
        raise ManifestError("F-T628-1: no fix row / band record on the band line")
    ev = row["evidence"]
    lo, hi = (D(x) for x in ev["quoted_bound"]["bound"])
    free, cl = D(ev["free_m"]), D(ev["centre_line_m"])
    if q6(free * Decimal("0.20") * Decimal("0.40")) != lo or q6(cl * Decimal("0.20") * Decimal("0.60")) != hi:
        raise ManifestError(f"F-T628-1: {S(lo)} .. {S(hi)} is not free x 0.20 x 0.40 .. centre line x 0.20 x 0.60")
    old = D(ev["held_line_bound_m3"])
    if D(ev["quoted_bound"]["replaced"]) != old:
        raise ManifestError("F-T628-1: the replaced bound is not the line's bound")
    if writer_of(order, BAND_LINE):
        raise ManifestError(f"{BAND_LINE}: written by {writer_of(order, BAND_LINE)} (R1)")
    line = _live(idx, BAND_LINE, *BAND)
    st = OV.state(line)
    if line["class"] != "HELD" or D(st["held_low"]) != old or D(st["held_high"]) != old:
        raise ManifestError(f"{BAND_LINE}: {st} is not HELD {S(old)} .. {S(old)} (stale)")
    sl, sh = (D(x) for x in fr["statement_engine_bounded"])
    cl_, ch_ = (D(x) for x in fr["corrected_engine_bounded"])
    if (sl, sh) != FOOT_STATEMENT or cl_ != sl - old + lo or ch_ != sh - old + hi:
        raise ManifestError(f"F-T628-1: footing line {S(sl)} .. {S(sh)} -> {S(cl_)} .. {S(ch_)} is not the band swap")
    r = M9.row(P_BAND, "F-T628-1", "SET", BAND_LINE, st, M9.held(float(lo), float(hi)), "HELD", src["verdict"],
               beside={"replaced_bound_m3": S(old), "basis": ev["quoted_bound"]["basis"],
                       "hand": f"{S(free)} x 0.20 x 0.40 = {S(lo)} .. {S(cl)} x 0.20 x 0.60 = {S(hi)}",
                       "downgrade": ev["downgrade"], "crossings": ev["crossings"],
                       "footing_line_bound_m3": f"{S(sl)} .. {S(sh)} -> {S(cl_)} .. {S(ch_)}",
                       "rule": "R-T641-1 (d): HELD with both ends, never a point"})
    return r, {"old": S(old), "range": [S(lo), S(hi)], "footing_line": [S(cl_), S(ch_)]}


# ---- T-638: formwork census fix rows -------------------------------------------------------------------------------

def formwork_rows(t638, idx, order, merged=None, source="T-638"):
    src = require_merged(source, merged)
    A = [l for l in t638["lines"] if l["class"] == "A_FIX"]
    if len(A) != t638["counts"]["by_class"]["A_FIX"] or len(A) != t638["counts"]["fix_rows"]:
        raise ManifestError("T-638: A_FIX rows do not match the census counts")
    rows, shafts, split = [], Decimal(0), Decimal(0)
    for l in A:
        f, lid = l["fix"], l["line_id"]
        if writer_of(order, lid):
            raise ManifestError(f"{lid}: written by {writer_of(order, lid)}: chain it there (R1)")
        line = _before_ok(idx, lid, f["before"])
        if (line["item_code"], line.get("unit")) != ("STR.FORMWORK", "m2"):
            raise ManifestError(f"{lid}: not a STR.FORMWORK m2 line")
        binds = ([l["concrete_line"]] if l.get("concrete_line") else []) + list(l.get("member_lines") or [])
        if not binds or any(idx.get(b, {}).get("class") != "RELEASED" for b in binds):
            raise ManifestError(f"{f['id']}: a bound concrete line of {lid} is not RELEASED (R-T638-1)")
        v = D(f["after"]["measured_net"])
        if f["after"]["class"] != "RELEASED" or v is None or v <= 0:
            raise ManifestError(f"{f['id']}: after {f['after']} is not a released face")
        shaft = f["kind"] == "RELEASE_LOW_END"
        if shaft:
            ck = l["checks"][0]
            if q6(abs(v - D(ck["method_m2"]))) != 0 or abs(v - D(ck["hand_m2"])) > Decimal("0.0015"):
                raise ManifestError(f"{f['id']}: {S(v)} is not the method / hand shaft {ck}")
            shafts += v
        else:
            if f["kind"] != "RELEASE" or f.get("companion"):
                raise ManifestError(f"{f['id']}: kind {f['kind']} with a companion is not a split release")
            split += v
        ev = "VERIFIED" if shaft else "PARTIALLY VERIFIED"
        rows.append(M9.row(P_FW, f["id"], "SET", lid, OV.state(line), M9.released(float(v)), ev, src["verdict"],
                           beside={"basis": f["basis"], "member": l.get("member"), "binds_released": binds,
                                   "status": "VERIFIED (Checker 4 / 4 components)" if shaft else
                                             "CALCULATED (F-C-T638-1: not re-walked; cause 1 / 1, quantity 0 / 1)",
                                   "rule": "R-T638-1 / R-T641-1 (e)"}))
        c = f.get("companion")
        if shaft:
            if not c or c["class"] != "HELD" or D(c["held_low"]) is None or D(c["held_high"]) is None:
                raise ManifestError(f"{f['id']}: a shaft release without its joint-face companion")
            elem = line["element_id"] + f"#{f['id']}:JOINT_FACES"
            rows.append(M9.row(P_FW, f["id"], "ADD", f"NEW:STR.FORMWORK:{elem}", None,
                               M9.held(float(D(c["held_low"])), float(D(c["held_high"]))), "HELD", src["verdict"],
                               code="STR.FORMWORK", unit="m2", elem=elem,
                               beside={"faces": c["faces"], "cause": c["cause"], "companion_of": lid,
                                       "rule": "R-T638-1 RELEASE_LOW_END: the joint faces stay HELD beside the shaft"},
                               note="companion of the released shaft"))
    total = shafts + split
    if S(total) != t638["counts"]["released_m2"].rstrip("0").rstrip("."):
        raise ManifestError(f"T-638: rows re-add to {S(total)}, census says {t638['counts']['released_m2']}")
    return rows, {"shafts_m2": S(shafts), "split_m2": S(split), "total_m2": S(total)}


# ---- T-639: GF column main bars ------------------------------------------------------------------------------------

def bars_rows(t639, idx, order, merged=None, source="T-639"):
    src = require_merged(source, merged)
    fr = sorted(t639["fix_rows"], key=lambda x: int(x["fix_row"].split("-")[-1]))
    if [f["fix_row"] for f in fr] != [f"FR-T639-{i}" for i in range(1, 7)]:
        raise ManifestError("T-639: fix rows are not FR-T639-1 .. -6")
    rows, tot = [], Decimal(0)
    for f in fr:
        lid = f["line_id"]
        if writer_of(order, lid):
            raise ManifestError(f"{lid}: written by {writer_of(order, lid)} (R1)")
        line = _live(idx, lid, "STR.REBAR", "kg")
        if line["class"] != "HELD" or line["held_low"] is not None or line["held_high"] is not None \
                or line["element_id"] != f["element_id"]:
            raise ManifestError(f"{lid}: {OV.state(line)} is not the HELD blank {f['element_id']} (stale)")
        kgm = q6(Decimal(f["dia_mm"]) ** 2 / Decimal(162))
        kg = q6(f["count"] * D(f["length_m"]) * Decimal(f["dia_mm"]) ** 2 / Decimal(162))
        if kgm != D(f["kg_per_m"]) or kg != D(f["kg"]):
            raise ManifestError(f"{f['fix_row']}: {f['count']} x {f['length_m']} x d^2/162 = {S(kg)}, not {f['kg']}")
        tot += kg
        rows.append(M9.row(P_BARS, f["fix_row"], "SET", lid, OV.state(line), M9.released(float(kg)), "VERIFIED",
                           src["verdict"],
                           beside={"column": f["column"], "mark": f["mark"], "printed": f["printed"],
                                   "hand": f["formula"], "rule": "R-T639-1 class D (D_ctrl settled, concrete RELEASED)"}))
    return rows, {"kg": S(tot)}


# ---- T-640: finish census bounds -----------------------------------------------------------------------------------

def finish_rows(t640, idx, order, merged=None, source="T-640"):
    src = require_merged(source, merged)
    A = [l for l in t640["lines"] if l["class"] == "A_BOUND"]
    if len(A) != t640["counts"]["by_class"]["A_BOUND"]:
        raise ManifestError("T-640: A_BOUND rows do not match the census counts")
    own, chained, listed, lo, hi = [], [], {}, Decimal(0), Decimal(0)
    for l in A:
        f, lid = l["fix"], l["line_id"]
        if f["kind"] != "SET" or f["after"]["class"] != "HELD":
            raise ManifestError(f"{f['id']}: an A_BOUND row that is not a HELD SET")
        line = _before_ok(idx, lid, f["before"])
        a_lo, a_hi = D(f["after"]["held_low"]), D(f["after"]["held_high"])
        if a_lo is None or a_hi is None or a_hi <= 0 or a_lo > a_hi:
            raise ManifestError(f"{f['id']}: bound {a_lo} .. {a_hi} is not a bounded range")
        pkg = writer_of(order, lid)
        if pkg not in (None, P_RET):
            raise ManifestError(f"{lid}: written by {pkg}: not a package V17 may chain into")
        beside = {"cause": l["cause"], "basis": f["basis"], "family": l["family"],
                  "rule": "R-T640-1 / R-T641-1 (e): bounds only, never a point"}
        if pkg == P_RET:
            pl = re.search(r"\((L-[0-9a-f]{20})\)", f["basis"])
            p = idx.get(pl.group(1)) if pl else None
            p_hi = None if p is None else D(p["measured_net"]) if p["class"] == "RELEASED" else D(p.get("held_high"))
            if p is None or p_hi != a_hi or a_lo != 0 or p["item_code"] != "FIN.PLASTER":
                raise ManifestError(f"{f['id']}: high end {S(a_hi)} is not the plaster face it names (released value "
                                    "or the HELD plaster's own high end)")
            beside["plaster_face"] = pl.group(1)
        r = M9.row(pkg or P_FIN, f["id"], "SET", lid, OV.state(line), M9.held(float(a_lo), float(a_hi)), "HELD",
                   src["verdict"], beside=beside)
        (chained if pkg else own).append(r)
        lo, hi = lo + a_lo, hi + a_hi
    tl, th = (D(x) for x in t640["fix_bound_total_m2"])
    if (lo, hi) != (tl, th):
        raise ManifestError(f"T-640: rows re-add to {S(lo)} .. {S(hi)}, census says {S(tl)} .. {S(th)}")
    for l in t640["lines"]:
        if "fix" in l and l["class"] != "A_BOUND":
            listed[l["fix"]["id"]] = {"line": l["line_id"], "kind": l["fix"]["kind"], "carrier": l.get("carrier"),
                                      "why": "proposal the Checker did not rule (R-T641-1 (f)); the line stays HELD blank "
                                             "with its carrier named, never 0"}
    return own, chained, listed, {"low": S(lo), "high": S(hi)}


# ---- listed, not wired ---------------------------------------------------------------------------------------------

def listed_sources(t634, t626, t627, t639):
    ret = t634["returns"]
    gf15 = t634["rooms"]["GF-15"]["paint_G1"]
    if D(ret["own_total"]) - D(ret["engine_valued"]) != D(ret["own_minus_engine"]):
        raise ManifestError("T-634 returns do not re-add")
    wet = sum((D(r["return_m2"]) for r in ret["rows"] if r["both_sides_wet"]), Decimal(0))
    if q6(wet) != D(ret["both_sides_wet_m2"]) or D(ret["paint_return_bound"][0]) != q6(D(ret["own_total"]) - wet) \
            .quantize(Decimal("0.01")):
        raise ManifestError("T-634 paint-return bracket is not own total less the wet-wet returns")
    return {
        "T-634 GF-15 W03": {"opening_ledger_m2": "-0.015161", "line": gf15["engine_line"], "own_net": gf15["net_own"],
                            "line_minus_own": gf15["line_minus_own"], "class": gf15["class"],
                            "why": "Checker: 'opening ledger only, line within tolerance' (W03 5.10186 vs 5.106 m)"},
        "T-634 door returns": {"own_m2": ret["own_total"], "engine_m2": ret["engine_valued"],
                               "diff_m2": ret["own_minus_engine"], "class": "TOLERANCE (D-GF-10 0.779556 vs 0.78)",
                               "paint_return_bracket_m2": ret["paint_return_bound"],
                               "wet_wet_doors": [r["id"] for r in ret["rows"] if r["both_sides_wet"]],
                               "why": "the bracket assumes the 21 non-wet returns painted whole; the T-640 per-line low 0 "
                                      "(frame-covered depth unprinted) stands by the Checker's OP-021 verdict, so V17 "
                                      "wires the per-line bounds and lists the bracket for statement V12"},
        "T-626 roof residual": {"tolerance_m2": "0.001332", "unresolved_m2": "0.521668",
                                "why": "his lump roof row; +4.30 annex 55.560332 vs line 55.559: TOLERANCE accepted; no "
                                       "engine line moves"},
        "T-627 class moves": {"windows_engine_right_m2": "3.975", "doors_height_m2": "0.580",
                              "rule_difference_m2": "0.960 -> 0.380", "engine_right_m2": "-1.720 -> -1.140",
                              "why": "engine = own (6.380 m2 on Q-55 C 2.20 = the drawn heights): statement V12 class "
                                     "move, no line"},
        "T-639 F-T639-1": {"kg": t639["finding_F_T639_1"]["kg"], "lines": len(t639["finding_F_T639_1"]["lines"]),
                           "why": "released column bar lines on HELD concrete: T-643's row (TODO), not V17's"},
    }


# ---- overlay ------------------------------------------------------------------------------------------------------

def v16_state():
    """the T-631 build up to its overlay (read only), so V17 steps from the exact V16 state."""
    M16.pins()
    t624, t622, t625 = M16._json(M16.IN["T624"]), M16._json(M16.IN["T622"]), M16._json(M16.IN["T625"])
    idx, order15, rul15, after15, rep15, t584 = M16.v15_state()
    wedge, chained, rul_w, _ = M16.t624_rows(t624, after15, order15)
    gf14 = M16.gf14_row(t622, after15, order15)
    stair, rul_s, _, _ = M16.t625_rows(t625, after15, order15)
    order16 = M15.chain_into(order15, M16.P_OVER, chained) + \
        [(M16.P_WEDGE, wedge), (M16.P_GF14, [gf14]), (M16.P_STAIR, stair)]
    rul16 = list(rul15) + rul_w + rul_s
    after16, rep16 = OV.apply(idx, order16, rul16)
    return idx, after15, order16, rul16, after16, rep16, stair, t584


def build():
    pins()
    t628, t638, t639, t640 = (_json(IN[k]) for k in ("T628", "T638", "T639", "T640"))
    t634, t626, t627 = _json(IN["T634"]), _json(IN["T626"]), _json(IN["T627"])
    v16j = _json(IN["V16"])
    idx, after15, order16, rul16, after16, rep16, stair, t584 = v16_state()
    if len(after16) != v16j["overlay"]["lines"]["after_v16"]:
        raise ManifestError("V16 state rebuild differs from the committed V16 line count")
    last = {}
    for r in v16j["rows"]:
        if r["kind"] in ("ADD", "SET"):
            last[r["line_id"]] = r
    for r in last.values():
        if not OV.same_state(OV.state(after16[r["line_id"]]), r["after"]):
            raise ManifestError(f"{r['line_id']}: V16 rebuild differs from the committed V16 row")
    t16 = OV.totals(after16)
    for k, v in v16j["overlay"]["v16_vs_v15_totals"].items():
        if t16[k] != v["after"]:
            raise ManifestError(f"{k}: V16 rebuild totals differ from the committed V16")
    sources, refused = no_row_sources()
    moves = finish_moves(stair, (GF_PORC, F1_PORC))
    bed, rul_b, bed_hand = bed_rows(after15, after16, order16, moves, source="T-631")
    band, band_out = band_row(t628, after16, order16)
    fw, fw_out = formwork_rows(t638, after16, order16)
    bars, bars_out = bars_rows(t639, after16, order16)
    fin, fin_ret, fin_listed, fin_out = finish_rows(t640, after16, order16)
    rows17 = bed + [band] + fw + bars + fin + fin_ret
    M9.validate_rows(rows17)
    order17 = M15.chain_into(order16, P_RET, fin_ret) + \
        [(P_BED, bed), (P_BAND, [band]), (P_FW, fw), (P_BARS, bars), (P_FIN, fin)]
    rul17 = list(rul16) + rul_b
    after17, rep = OV.apply(idx, order17, rul17)
    v17_lines = {r["line_id"] for r in rows17}
    others = sorted(k for k in set(after16) | set(after17) if k not in v17_lines and after16.get(k) != after17.get(k))
    if others:
        raise ManifestError(f"lines V17 does not write changed: {others[:5]}")
    t17 = OV.totals(after17)
    dt = OV.diff_totals(t16, t17)
    writes = sorted({f"{(r.get('item_code') or after16[r['line_id']]['item_code'])}|"
                     f"{(r.get('unit') or after16[r['line_id']].get('unit'))}" for r in rows17})
    if sorted(dt) != writes:
        raise ManifestError(f"totals moved on {sorted(dt)}, V17 writes {writes}")
    if any(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]):
        raise ManifestError(f"unexplained conflicts: {[c for c in rep['conflicts'] if c['status'] == 'UNEXPLAINED']}")
    flagged = [r for r in rep["rows"] if r["status"] != "APPLIED"]
    v17_ops = {r["op_id"] for r in rows17}
    if any(r["op_id"] in v17_ops for r in flagged):
        raise ManifestError(f"a V17 row is not APPLIED: {[r for r in flagged if r['op_id'] in v17_ops]}")
    if len(flagged) != len([r for r in rep16["rows"] if r["status"] != "APPLIED"]):
        raise ManifestError("the flagged rows of V16 changed")
    follows = bed_follows(after17, (GF_PORC, F1_PORC))
    # hand acceptance per key
    fwk, bk = "STR.FORMWORK|m2", "STR.REBAR|kg"
    if q6(D(t17[fwk]["released"]) - D(t16[fwk]["released"])) != D(fw_out["total_m2"]):
        raise ManifestError("formwork released did not move by the T-638 rows")
    if q6(D(t17[bk]["released"]) - D(t16[bk]["released"])) != D(bars_out["kg"]):
        raise ManifestError("rebar released did not move by the T-639 rows")
    bwk = "|".join(BAND)
    if q6(D(t17[bwk]["held_high"]) - D(t16[bwk]["held_high"])) != D(band_out["range"][1]) - D(band_out["old"]) or \
            q6(D(t17[bwk]["held_low"]) - D(t16[bwk]["held_low"])) != D(band_out["range"][0]) - D(band_out["old"]):
        raise ManifestError("boundary-wall HELD bounds did not move by the band swap")
    hb = Decimal(0), Decimal(0)
    for k in dt:
        if k.startswith("FIN.") and not k.startswith("FIN.FLOOR.BED"):
            hb = (hb[0] + D(t17[k]["held_low"]) - D(dt[k]["before"]["held_low"]),
                  hb[1] + D(t17[k]["held_high"]) - D(dt[k]["before"]["held_high"]))
    if (q6(hb[0]), q6(hb[1])) != (q6(D(fin_out["low"])), q6(D(fin_out["high"]))):
        raise ManifestError(f"T-640 keys moved {S(hb[0])} .. {S(hb[1])}, rows say {fin_out}")
    status = {}
    for r in rep["rows"]:
        status.setdefault(r["package"], {}).setdefault(r["status"], 0)
        status[r["package"]][r["status"]] += 1
    M11 = M15.M11
    t412 = M11.load_t412()
    nrows, _ = M11.nosing_ledger(t412, M11._json(M11.IN["T598"]))
    cen = M9.census_on(after17, M11.census_edges(t412, nrows), t584, {M9.E1_LINE: ("ST-03", "E1")})
    if cen["doubles"] or cen["orphans"]:
        raise ManifestError("stair census doubles / orphans after V17")
    table = []
    for r in rows17:
        b, a = r.get("before"), r.get("after")
        table.append({"row": r["row"], "package": r["package"], "kind": r["kind"], "line_id": r["line_id"],
                      "item": r.get("item_code") or after16[r["line_id"]]["item_code"],
                      "before": None if b is None else {k: b[k] for k in OV.QFIELDS},
                      "after": None if a is None else {k: a[k] for k in OV.QFIELDS},
                      "evidence": r["evidence"]["status"]})
    by_ev = {}
    for r in rows17:
        by_ev[r["evidence"]["status"]] = by_ev.get(r["evidence"]["status"], 0) + 1
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-641", "candidate": M9.T580.CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in IN.values()},
        "sources_merged": {k: v["merge"] for k, v in MERGED.items()},
        "sources_no_row": sources, "sources_refused": refused,
        "supersedes": {"V16 downstream_not_moved (F-T631-1, 4 bed lines)": "FLOOR_BED_FOLLOWS_FINISH (moved, R-T641-1 (c))",
                       "V16 band bound 7.2204 m3 (L-6290a9f3, UNSUPPORTED)": "F-T628-1 HELD 5.6392 .. 11.0328"},
        "held_not_wired": {"T-640": fin_listed, **listed_sources(t634, t626, t627, t639),
                           "T-638 strip D": "slab-edge strip 2 x 0.865 m2 HELD (no section / thickness): no owning line"},
        "line_table": table,
        "rows": [dict(r) for r in rows17],
        "rows_by_evidence": by_ev,
        "bed": {"hand": bed_hand, "after_v17": follows,
                "totals": {k: {"v16": t16.get(k), "v17": t17.get(k)} for k in dt if k.startswith("FIN.FLOOR.BED")}},
        "band": {**band_out, "totals": {bwk: {"v16": t16[bwk], "v17": t17[bwk]}}},
        "formwork": {**fw_out, "totals": {fwk: {"v16": t16[fwk], "v17": t17[fwk]}},
                     "freelancer": "FREELANCER_NO_ROW (T-163 / T-474 s.8): no %"},
        "rebar": {**bars_out, "totals": {bk: {"v16": t16[bk], "v17": t17[bk]}}},
        "finish_bounds": {**fin_out, "totals": {k: {"v16": t16[k], "v17": t17[k]} for k in dt
                                                if k.startswith("FIN.") and not k.startswith("FIN.FLOOR.BED")}},
        "overlay": {
            "lines": {"base": len(idx), "after_v16": len(after16), "after_v17": len(after17)},
            "order": [{"package": n, "ops": len(o), "status": status.get(n, {})} for n, o in order17],
            "flagged_rows": flagged,
            "stale": sum(r["status"] == "STALE" for r in rep["rows"]),
            "two_package_lines": 0,                     # OV.apply raises R1 otherwise
            "unexplained_conflicts": sum(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]),
            "conflicts": [c for c in rep["conflicts"] if any(l in v17_lines for l in c["lines"])],
            "rulings_v17": rul_b,
            "other_lines_changed_vs_v16_overlay": others,
            "v17_vs_v16_totals": dt,
        },
        "stair_edge_census_after_v17": {"edges": cen["edges"], "doubles": len(cen["doubles"]),
                                        "orphans": len(cen["orphans"])},
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str) + "\n"


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    return b


def main(argv):
    text = dumps(build())
    if "--check" in argv:
        ok = OUT_JSON.exists() and OUT_JSON.read_text(encoding="utf-8") == text
        print("T-641 manifest V17: committed output", "is the rebuild" if ok else "DIFFERS from the rebuild")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
