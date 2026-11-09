"""T-649 WIRING MANIFEST V18 + OVERLAY DRY RUN (R-T649-1; lane I, non-candidate, research only).

V18 carries into the overlay the fix rows and records verdicted after V17 (T-641, MERGED; claim 2026-11-09T05:00Z):
  - T-642 (MERGED 1c7411a5): FR-T642-2 the strip north of column 353 (route G piece BAND0030.2, carried once by HELD
    L-efd3f780 0.04 .. 0.12 m3): RELEASED 0.050 m3 low end (0.20 x 0.50 x B4 0.50, Checker own re-measure AGREE) + its
    companion HELD 0 .. 0.025 m3 (B4 0.50 vs B7 0.75 depth, no mark on the strip; R-T619-1). FR-T642-4: BAND0049 0.282743
    m3 depth DRAWING-CONFIRMED (TEXT_ONLY stamp, no quantity). FR-T642-1 / -3 (CB12, GF B11): ENGINE_RIGHT no-change
    restates, listed with their figures.
  - T-643 (MERGED f136248f): the 4 Checker-validated downgrade-only records DGP-T643-fdb3ed37 / 943b0c58 / ca59159e /
    196fcf58 (owner 2026-10-24 23:57): COL-2F-50 / -51 / -53 / -54 main bars 39.822 kg each RELEASED -> HELD blank on
    the undeclared roof datum (D-39), never 0. B11 released 9375.305760 -> 9216.017760 kg on the T-643 base; on V17
    (+412.444445 T-639) 9787.750205 -> 9628.462205 kg.
  - T-645 (MERGED ebc5a76a): 16 fix rows: 10 A_DRAWN SET RELEASED (B7-03 risers +6.836036 m2 -> 1.96 + 6.836036 =
    8.796036 m2 on the trade; B7-01 flights 13.36392 lm) with the Checker-capped statuses (D1 / MS1-U / MS2-L
    DRAWING-CONFIRMED, RS-S / RS-A ASSUMED - OWNER-APPROVED); 6 C_OPEN SET HELD bounded (high OPEN where stated).
  - T-646 (MERGED af50c864): 3 roof falls-screed lines HELD blank -> AT_LEAST 2.512672 / 3.324832 / 4.791492 m3 (sum
    10.628996 .. OPEN); the 40 other lines stay HELD blank with their census cause (trial BOQ cause source).
  - T-650 (MERGED 2a2e28ca, Lead ruling F-T650-3): STR.CONC.LINTEL lines chained in the package that writes them
    (T-498, R1): 2 NEW bounds (A-1F-01, P-1F-01), 8 HELD BY NAME bounds (D-GF-11 + D-GF-12 one pair range carried on the
    D-GF-11 line, the D-GF-12 line names it), D-1F-07 kept HELD blank naming 'Checker re-measure pending' (Checker
    T-650 LIMIT: not re-measured), L-GF-01 HELD blank by the lift landing door register + 'Checker re-measure pending'.
  - Lead ruling F-T645-1 on the MS1-L tread / step lines (see mstair_ruling): proposal only, never applied here.
  - T-633 (MERGED 2f103248) D-GF-06 head class RULE_DIFFERENCE -> ENGINE_RIGHT: a statement-only op (no line).
  - T-525 (MERGED c7565fb9) master 1.57.0 and F-T525-1 (stale B8-06 open text): no-quantity, carried by the trial BOQ.
Refused by name (not MERGED at claim): T-647 (TODO r2), T-648 (READY).

R-T649-1 (every villa on the engine's line-index scheme):
  (a) MERGED ONLY (R-T641-1 (a)); merged tasks with no line move are listed with 0 rows; unmerged refused by name.
  (b) ONE WRITER PER LINE (R1): a row on a line an earlier package writes (quantity or text) chains inside it.
  (c) A DOWNGRADE MOVES A LINE TO HELD ONLY: a downgrade-only record whose before is not the RELEASED engine quantity
      it names, or whose after is not HELD (never 0, never a value), is refused; it is applied only when the Checker
      validated it (board verdict); a worker's own downgrade proposal is listed, never applied.
  (d) A RELEASED LOW END CARRIES ITS COMPANION: a SET that releases the low end of a HELD range adds the remainder as
      its own HELD 0 .. width line, and low + width re-adds to the range the Checker endorsed.
  (e) A CENSUS FIX ROW ENTERS AS ITS MERGED SOURCE STATES IT (before checked against V17; status capped by the verdict).
  (f) A QUANTITY IS NEVER MORE CERTAIN THAN ITS INPUTS (F-T645-1, lesson T-643): a released line whose count is the
      same drawn edges a HELD conflict disputes takes a downgrade PROPOSAL (listed, not applied).
  (g) A BOUND THE CHECKER DID NOT RE-MEASURE WHERE THE VERDICT SAYS IT MUST BE stays HELD blank naming the pending
      re-measure; a pair range sharing one pier is carried once (R-T524-1).
  (h) Every line V18 does not write is identical to the V17 overlay; totals move only on the keys V18 writes.
Rebuild: pytest-driven writer (tests/t649_manifest_v18, URBAN_T649_WRITE=1); `--check` compares.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
T641_DIR = ROOT / "research/agents_t641"
if str(T641_DIR) not in sys.path:
    sys.path.insert(0, str(T641_DIR))

import manifest_v17 as M17                                            # noqa: E402  (R-T641-1, read only)

M16, M15, M9, OV = M17.M16, M17.M15, M17.M9, M17.OV
D, S, q6 = M17.D, M17.S, M17.q6

SCHEMA = "URBAN_T649_WIRING_MANIFEST_V18"
RULE = "R-T649-1"
OUT_JSON = HERE / "out/WIRING_MANIFEST_V18.json"
IN = {
    "T642": ROOT / "research/agents_t642/out/T642_FIX_ROWS.json",
    "T643": ROOT / "research/agents_t643/out/REBAR_ON_HELD_CONCRETE_T643.json",
    "T645": ROOT / "research/agents_t645/out/STAIR_HOLD_CENSUS_T645.json",
    "T646": ROOT / "research/agents_t646/out/ROOF_FENCE_HOLD_CENSUS_T646.json",
    "T650": ROOT / "research/agents_t650/out/T650_PAYABLE_FORM.json",
    "T633": ROOT / "research/agents_t633/out/T633_ROW_EVIDENCE.json",
    "V17": T641_DIR / "out/WIRING_MANIFEST_V17.json",
    "V17_CODE": T641_DIR / "manifest_v17.py",
}
PINS = {
    "T642": "5ce2188f8862d7ab449e8bc89f7ef5c8b8b4ea23bdd7040df0c73860159f028d",
    "T643": "37efdee9765cbc296ccccca3012a4d246857d508bd3d3481e58d3c5a93de237b",
    "T645": "3e1384ee4e84bf9ed74a976e3a27170aad0fe4b049d76708cfe7dc3f60fe9629",
    "T646": "fd4988c7f2f9cf0d187a1eebaf57897c640ea3a0114d98314cc4f6fe9c4197cf",
    "T650": "cd72b44596cc1b2840282ab56f1f6653a7b53b5601db2bb9f3f7bcb7eb0a1fb2",
    "T633": "5040f0c40a52735e91e8db47046de80d58919d2645f1c0da6236a06fe3eac8cc",
    "V17": "7a0889aaa9f488cf5bea38a363b1a1342e779f399635b433800be4c1215c4065",
    "V17_CODE": "384a8b2ec57bc75d23812bb63944b1221617a9339cbb327390217ccae3d0b21a",
}

# R-T649-1 (a): board MERGED verdicts at claim (2026-11-09T05:00Z; Verifier text abridged, full text on BOARD.md)
MERGED = {
    "T-642": {"merge": "1c7411a5",
              "verdict": "BOARD T-642 VERIFIER 2026-11-08T21:54Z: OWN ST7757 re-measure: (b) 2B2/2B3 through col 353 0.20 x "
                         "0.50 = 0.100 m2 AGREE; FR-T642-2 0.050 SET + HELD 0..0.025 per R-T619-1 AGREE, carried by HELD "
                         "L-efd3f780; (d) block 'b7' TEXT 482 marks the arc: 0.282743 DRAWING-CONFIRMED; (a) CB12 and (c) "
                         "GF B11 ENGINE_RIGHT"},
    "T-643": {"merge": "f136248f",
              "verdict": "BOARD T-643 VERIFIER 2026-11-09T00:05Z: DOWNGRADE 4 (2F-50/51/53/54, 159.288 kg): L runs to "
                         "LEVEL.STRUCTURAL_TOP.ROOF.MAIN, undeclared (D-39): CHECKER-VALIDATED downgrade-only proposals "
                         "DGP-T643-fdb3ed37 / 943b0c58 / ca59159e / 196fcf58 (HELD, never 0; applied only by a wiring "
                         "package; B11 released 9375.305760 -> 9216.017760 kg)"},
    "T-645": {"merge": "ebc5a76a",
              "verdict": "BOARD T-645 VERIFIER 2026-11-08T23:03Z: OWN RE-MEASURE D1 (riser 0.667 m2, flight 1.041933 lm) "
                         "and MS2-L (riser 1.8975 m2, flight 3.782209 lm) AGREE 4 / 4; statuses D1 / MS1-U / MS2-L "
                         "DRAWING-CONFIRMED, RS-S / RS-A ASSUMED - OWNER-APPROVED (Q-50 A cond), C_OPEN bounded never 0, "
                         "B_HELD named"},
    "T-646": {"merge": "af50c864",
              "verdict": "BOARD T-646 VERIFIER 2026-11-09T00:57Z: fence 82.0705 / 83.1305 m2 at-most AGREE (layers HELD); "
                         "ROOF-430 screed own grid V 3.400815, minus D-band 3.324832 m3 AGREE (strict low); roof screed "
                         "AT_LEAST, high OPEN"},
    "T-650": {"merge": "2a2e28ca",
              "verdict": "BOARD T-650 VERIFIER 2026-11-09T03:43Z: ST p.13 schedule + MIN.40cm AGREE; W14 0.195, P-1F-01 "
                         "0.063, A-1F-01 0.054 AGREE (A-1F-01 width engine-read: CHECKER-PARTIAL); 8 BOUNDED low 0.619, "
                         "10 HELD BY NAME 0.372692 .. 0.437542; LIMIT: D-1F-07 and L-GF-01 NOT re-measured, must be "
                         "re-measured before T-649 wires them"},
    "T-633": {"merge": "2f103248",
              "verdict": "BOARD T-633 VERIFIER 2026-11-09T04:01Z: 39 / 39 rows evidenced; D-GF-06 head 2.20 class move "
                         "RULE_DIFFERENCE -> ENGINE_RIGHT proposed for the statement"},
    "T-525": {"merge": "c7565fb9",
              "verdict": "BOARD T-525 VERIFIER 2026-11-09T03:43Z: master 1.57.0 promotes T-507 only; F-T525-1 text "
                         "finding (stale B8-06 open sentence)"},
    "T-641": {"merge": "57620ab8", "verdict": "BOARD T-641 VERIFIER 2026-11-08T21:56Z: V17 MERGED (the base of V18)"},
}
NO_ROW = {
    "T-633": "D-GF-06 height row -0.20 m2 RULE_DIFFERENCE -> ENGINE_RIGHT (head drawn 2.20, T-627 binding): a statement "
             "class move (statement V12, T-635), no engine line",
    "T-525": "BOQ_FAMILY_MASTER 1.57.0 (the trial BOQ r2 grouping); F-T525-1 stale B8-06 open text carried as a "
             "no-quantity reader correction in the trial BOQ r2",
    "T-641": "manifest V17: the base of V18 (rebuilt and compared, not restated)",
}
NOT_MERGED = {"T-647": "TODO r2 at claim (B11 structural HELD causes)", "T-648": "READY at claim (finishes HELD causes)"}

P498 = "T-498"                     # the overlay package that writes the STR.CONC.LINTEL lines (LINTEL_V3)
P_DG = "CHECKER_DOWNGRADES (T-643 DGP-T643-*)"
P_STRIP = "STRIP_COL353 (T-642 FR-T642-2 / FR-T642-4)"
P_STAIR = "STAIR_FINISH_HOLD_RELEASE (T-645 FR-T645-n)"
P_ROOF = "ROOF_SCREED_AT_LEAST (T-646 R-T646-1)"
P_LINT = "LINTEL_RC_BOUNDS (T-650 R-T650-1)"
STRIP_LINE, BAND49_LINE = "L-efd3f7806bf10b6a8e98", "L-5bc1baae70fcc325abea"
EVID_ASSUMED = M15.EVID_ASSUMED
PENDING = "Checker re-measure pending (T-650 verdict LIMIT: not re-measured on the drawing; must be re-measured before " \
          "its bound is wired)"
PENDING_IDS = ("D-1F-07", "L-GF-01")
F_T645_1 = {"flight": "MS1-L", "element": "GF-R31F8AE:flight 1",
            "codes": {"FIN.MARBLE.TREAD": ("m2", Decimal("0.300") * Decimal("1.150")),
                      "FIN.STAIR.STEP_LM": ("lm", Decimal("1.150"))}}


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
    return M17._st(x)


def _before_ok(idx, lid, stated):
    line = idx.get(lid)
    if line is None or not OV.same_state(OV.state(line), _st(stated)):
        raise ManifestError(f"{lid}: stated before {stated} is not the V17 state {OV.state(line) if line else None} "
                            "(stale source)")
    return line


def _evid(s):
    """a source status as a WORKFLOW_CONTROLS s.5 status (the hyphen spelling of ASSUMED — OWNER-APPROVED mapped)."""
    s = (s or "").replace(" - ", " — ")
    if s not in M15.EVIDENCE:
        raise ManifestError(f"status {s!r} is not a WORKFLOW_CONTROLS s.5 status")
    return s


def _free(order, lid, allowed=()):
    pkg = writer_of(order, lid)
    if pkg is not None and pkg not in allowed:
        raise ManifestError(f"{lid}: written by {pkg}: chain it there (R1)")
    return pkg


# ---- T-642: the strip north of column 353 -------------------------------------------------------------------------

def strip_rows(t642, idx, order, merged=None, source="T-642"):
    src = require_merged(source, merged)
    fr = {f["id"]: f for f in t642["fix_rows"]}
    f2, f4 = fr.get("FR-T642-2"), fr.get("FR-T642-4")
    if f2 is None or f4 is None or f2["line_id"] != STRIP_LINE or f4["line_id"] != BAND49_LINE:
        raise ManifestError("T-642: FR-T642-2 / FR-T642-4 are not the strip and BAND0049 lines")
    item = t642["items"]["b"]
    e, dr = item["engine"]["line"], item["drawn"]
    _free(order, STRIP_LINE)
    line = M17._live(idx, STRIP_LINE, "STR.CONC.BEAM", "m3")
    lo0, hi0 = D(e["held_low_m3"]), D(e["held_high_m3"])
    if line["class"] != "HELD" or D(line["held_low"]) != lo0 or D(line["held_high"]) != hi0:
        raise ManifestError(f"{STRIP_LINE}: {OV.state(line)} is not the HELD {S(lo0)} .. {S(hi0)} T-642 read (stale)")
    low = D(f2["change_m3"])
    plan = q6(D(dr["width_m"]) * D(dr["length_m"]))
    b4, b7 = D(dr["depths_allowed_by_the_drawing"]["B4"]), D(dr["depths_allowed_by_the_drawing"]["B7"])
    c = f2["companion"]
    clo, chi = (D(x) for x in c["held_m3"])
    if q6(plan * b4) != low or clo != 0 or q6(plan * b7) != low + chi:
        raise ManifestError(f"FR-T642-2: {S(low)} + 0 .. {S(chi)} is not {S(plan)} m2 x B4 {S(b4)} .. B7 {S(b7)}")
    if not (lo0 <= low <= hi0 and low + chi <= hi0):
        raise ManifestError("FR-T642-2: the released low end and its companion leave the line's own range")
    rows = [M9.row(P_STRIP, "FR-T642-2", "SET", STRIP_LINE, OV.state(line), M9.released(float(low)), "VERIFIED",
                   src["verdict"],
                   beside={"hand": f"{S(dr['width_m'])} x {S(dr['length_m'])} = {S(plan)} m2 x B4 {S(b4)} = {S(low)} m3",
                           "replaced_range_m3": f"{S(lo0)} .. {S(hi0)}", "piece": "route G BAND0030.2 (carried once)",
                           "rule": "R-T649-1 (d) / R-T619-1: the low end released, the depth remainder its own line"})]
    elem = c["element"]
    rows.append(M9.row(P_STRIP, "FR-T642-2", "ADD", f"NEW:STR.CONC.BEAM:{elem}", None, M9.held(0.0, float(chi)), "HELD",
                       src["verdict"], code="STR.CONC.BEAM", unit="m3", elem=elem,
                       beside={"cause": c["cause"], "companion_of": STRIP_LINE,
                               "hand": f"{S(plan)} x ({S(b7)} - {S(b4)}) = {S(chi)} m3",
                               "rule": "R-T649-1 (d): HELD 0 .. width beside the released low end, never 0"},
                       note="companion of the released strip low end"))
    _free(order, BAND49_LINE)
    b49 = M17._live(idx, BAND49_LINE, "STR.CONC.BEAM", "m3")
    d = t642["items"]["d"]
    if b49["class"] != "RELEASED" or D(b49["measured_net"]) != D(d["engine"]["line_value_m3"]) or \
            D(d["delta_own_minus_line_m3"]) != 0:
        raise ManifestError(f"{BAND49_LINE}: not the released {d['engine']['line_value_m3']} the T-642 read binds")
    rows.append(M9.row(P_STRIP, "FR-T642-4", "TEXT_ONLY", BAND49_LINE, OV.state(b49), None, "DRAWING-CONFIRMED",
                       src["verdict"],
                       beside={"stamp": "depth B7 0.75 DRAWING-CONFIRMED by the arc's printed label (block 'b7', TEXT "
                                        f"{d['printed_mark']['text_handle']}); quantity unchanged {S(D(b49['measured_net']))} m3",
                               "rule": "R-T649-1 (e): a status the verdict states, no quantity"}))
    return rows, {"released_m3": S(low), "companion_m3": [S(clo), S(chi)], "replaced": [S(lo0), S(hi0)],
                  "band0049_m3": S(D(b49["measured_net"]))}


def listed_t642(t642):
    out = {}
    for k in ("a", "c"):
        it = t642["items"][k]
        out[it["fix_row"]["id"]] = {"line": it["fix_row"]["line_id"], "status": it["fix_row"]["status"],
                                    "verdict": it["verdict"] if "verdict" in it else it.get("finding"),
                                    "why": "ENGINE_RIGHT no-change restate (Checker AGREE): no op, the line stands"}
    return out


# ---- T-643: Checker-validated downgrade-only records ------------------------------------------------------------

def downgrade_rows(t643, idx, order, merged=None, source="T-643", validated=None):
    src = require_merged(source, merged)
    val = set(validated if validated is not None else
              ("DGP-T643-" + h for h in re.findall(r"\b([0-9a-f]{8})\b", src["verdict"].split("CHECKER-VALIDATED", 1)[-1])))
    p1 = t643["part1"]
    props = p1["downgrade_proposals"]
    rows, tot = [], Decimal(0)
    for p in props:
        pid = p["proposal_id"]
        if pid[:17] not in val:
            raise ManifestError(f"{pid}: a downgrade the Checker did not validate is never applied (R-T649-1 (c))")
        if p.get("state") != "HELD" or len(p["line_ids"]) != 1:
            raise ManifestError(f"{pid}: a downgrade-only record moves one line to HELD only (state {p.get('state')})")
        lid = p["line_ids"][0]
        _free(order, lid)
        line = idx.get(lid)
        if line is None or line["class"] != "RELEASED" or D(line["measured_net"]) != D(p["engine_qty"]):
            raise ManifestError(f"{pid}: {lid} is not RELEASED {p['engine_qty']} {p['unit']} (a downgrade never "
                                "promotes, never moves a line it does not name)")
        if (line["item_code"], line.get("unit")) != ("STR.REBAR", p["unit"]):
            raise ManifestError(f"{pid}: {lid} is not a STR.REBAR {p['unit']} line")
        tot += D(line["measured_net"])
        rows.append(M9.row(P_DG, pid[:17], "SET", lid, OV.state(line), M9.held(), "HELD", src["verdict"],
                           beside={"cause": p["reason"], "downgrade_id": pid, "engine_qty_kg": p["engine_qty"],
                                   "evidence": p["evidence"], "owner_rule": "owner 2026-10-24 23:57 downgrade-only record",
                                   "rule": "R-T649-1 (c): RELEASED -> HELD blank, never 0, never a value"}))
    if q6(tot) != q6(D(p1["kg_proposed_held"])) or \
            q6(D(p1["released_B11_before_kg"]) - tot) != q6(D(p1["released_B11_if_downgrades_applied_kg"])):
        raise ManifestError(f"T-643: downgrades re-add to {S(tot)} kg, record says {p1['kg_proposed_held']}")
    if {r["row"] for r in rows} != val:
        raise ManifestError("T-643: the validated downgrade ids are not the records applied")
    return rows, {"kg": S(tot), "n": len(rows), "t643_base_kg": [p1["released_B11_before_kg"],
                                                                p1["released_B11_if_downgrades_applied_kg"]]}


# ---- T-645: stair finish census fix rows --------------------------------------------------------------------------

def stair_rows(t645, idx, order, merged=None, source="T-645"):
    src = require_merged(source, merged)
    fixes = [l for l in t645["lines"] if l.get("fix")]
    if len(fixes) != t645["counts"]["fix_rows"]:
        raise ManifestError("T-645: fix rows do not match the census counts")
    rows, rel, bnd = [], {}, {}
    for n, l in enumerate(sorted(fixes, key=lambda x: x["line_id"]), 1):
        f, lid = l["fix"], l["line_id"]
        _free(order, lid)
        line = _before_ok(idx, lid, f["before"])
        if (line["item_code"], line["element_id"]) != (l["item_code"], l["element_id"]):
            raise ManifestError(f"{lid}: {line['item_code']} {line['element_id']} is not the census line")
        a = f["after"]
        if a["class"] == "RELEASED":
            if l["class"] != "A_DRAWN" or D(a["measured_net"]) is None or D(a["measured_net"]) <= 0:
                raise ManifestError(f"{lid}: a release that is not an A_DRAWN value")
            ev = _evid(a.get("evidence"))
            after = M9.released(float(D(a["measured_net"])))
            rel[l["item_code"]] = rel.get(l["item_code"], Decimal(0)) + D(a["measured_net"])
        else:
            if a["class"] != "HELD" or l["class"] != "C_OPEN" or D(a["held_low"]) is None:
                raise ManifestError(f"{lid}: a HELD fix row that is not a C_OPEN bound with a low end")
            lo, hi = D(a["held_low"]), D(a.get("held_high"))
            if hi is not None and hi < lo:
                raise ManifestError(f"{lid}: bound {S(lo)} .. {S(hi)}")
            ev = "HELD"
            after = M9.held(float(lo), None if hi is None else float(hi))
            b = bnd.setdefault(l["item_code"], {"low": Decimal(0), "high": Decimal(0), "open": 0, "n": 0})
            b["low"] += lo
            b["n"] += 1
            if hi is None:
                b["open"] += 1
            else:
                b["high"] += hi
        r = M15.row(P_STAIR, f"FR-T645/{l.get('flight') or l['element_id']}/{l['item_code']}", "SET", lid,
                    OV.state(line), after, ev, src["verdict"],
                    beside={"basis": f["basis"], "flight": l.get("flight"),
                            "cause": l.get("cause") if a["class"] == "HELD" else None,
                                                "rule": "R-T645-1 / R-T649-1 (e)"})
        rows.append(r)
    for code, v in t645["released_by_code"].items():
        if q6(rel.get(code, Decimal(0))) != q6(D(v)):
            raise ManifestError(f"T-645: {code} releases re-add to {S(rel.get(code, 0))}, census says {v}")
    for code, v in t645["bounded_by_code"].items():
        b = bnd.get(code)
        if b is None or q6(b["low"]) != q6(D(v["low"])) or b["n"] != v["n"] or \
                (v["high"] == "OPEN") != (b["open"] > 0) or (v["high"] != "OPEN" and q6(b["high"]) != q6(D(v["high"]))):
            raise ManifestError(f"T-645: {code} bounds re-add to {b}, census says {v}")
    return rows, {"released": {k: S(v) for k, v in rel.items()},
                  "bounded": {k: {"low": S(v["low"]), "high": "OPEN" if v["open"] else S(v["high"]), "n": v["n"]}
                              for k, v in bnd.items()}}


FACE_PAIRS = {frozenset({"FIN.MARBLE.RISER", "FIN.MARBLE.TREAD"}): "the riser face and the tread face of one flight: two "
              "faces of the stair finish, each measured once (OWNER_RULE_STAIRS s.1)",
              frozenset({"FIN.STAIR.FLIGHT", "FIN.STAIR.STEP_LM"}): "the flight pitch line (nosing to nosing) and the "
              "step lengths (front x count) of one flight: two measures of different pieces, never one counted twice"}


def stair_rulings(rows, idx):
    """R-T649-1 (e): a T-645 line beside a candidate line of the same layer on its flight is explained only when the two
    item codes are a known pair of distinct pieces; one code twice on a flight is a double count and is refused."""
    out = []
    for r in rows:
        l = idx[r["line_id"]]
        for k, o in idx.items():
            if k == r["line_id"] or o["class"] == "EXCLUDED" or o.get("unit") != l.get("unit") or \
                    OV.layer(o["item_code"]) != OV.layer(l["item_code"]) or OV.host(o["element_id"]) != OV.host(l["element_id"]):
                continue
            pair = FACE_PAIRS.get(frozenset({o["item_code"], l["item_code"]}))
            if pair is None:
                raise ManifestError(f"{r['line_id']} {l['item_code']} beside {k} {o['item_code']} on {l['element_id']}: "
                                    "not a known pair of distinct pieces (double count)")
            out.append({"layer": OV.layer(l["item_code"]), "host_re": "^" + re.escape(OV.host(l["element_id"])) + "$",
                        "sources": ["CANDIDATE", P_STAIR], "ruling": f"{l['item_code']} {r['line_id']} beside "
                        f"{o['item_code']} {k}: {pair}", "fix_row": r["row"]})
    return out


def mstair_ruling(t645, idx, order, t645_rows):
    """Lead ruling F-T645-1 on the MS1-L tread / step lines (R-T649-1 (f)): returns the per-line ruling + proposals."""
    fl = t645["flights"][F_T645_1["flight"]]
    goings = int(fl["goings"])
    held_flight = next(r for r in t645_rows if r["beside"]["flight"] == F_T645_1["flight"]
                       and r["line_id"] in idx and idx[r["line_id"]]["item_code"] == "FIN.STAIR.FLIGHT")
    a = held_flight["after"]
    if a["class"] != "HELD":
        raise ManifestError("F-T645-1: the MS1-L flight line is not HELD: the ruling does not apply")
    # the HELD flight bound is goings x hypot: its two ends give the disputed going counts
    pitch = Decimal(str((Decimal("0.300") ** 2 + D(fl["R"]) ** 2).sqrt()))
    g_lo = int((D(a["held_low"]) / pitch).to_integral_value())
    g_hi = int((D(a["held_high"]) / pitch).to_integral_value())
    if g_lo != goings or g_hi <= g_lo:
        raise ManifestError(f"F-T645-1: flight bound gives {g_lo} .. {g_hi} goings, census {goings}")
    out, proposals = [], []
    for lid, l in sorted(idx.items()):
        if l["element_id"] != F_T645_1["element"] or l["item_code"] not in F_T645_1["codes"] or l["class"] != "RELEASED":
            continue
        unit, per = F_T645_1["codes"][l["item_code"]]
        v = D(l["measured_net"])
        n = v / per
        if n != n.to_integral_value() or int(n) != g_lo:
            raise ManifestError(f"{lid}: {S(v)} {unit} is not {g_lo} goings x {S(per)}")
        hi = q6(per * g_hi)
        independent = False        # the edges counted are the disputed ones: arch DC .. 486 vs ST p.4 45A .. 25E
        dg = {"proposal_id": "DGP-T649-" + hashlib.sha256(f"F-T645-1|{lid}".encode()).hexdigest()[:16],
              "schema": "URBAN_CHECKER_DOWNGRADE_V1 (PROPOSAL, not issued)", "line_ids": [lid], "unit": unit,
              "engine_qty": S(v), "state": "HELD", "proposed_bound": [S(v), S(hi)], "checker": None, "resolved": False,
              "reason": f"F-T645-1: {l['item_code']} on MS1-L counts {g_lo} goings from the architectural GF plan edges "
                        f"(DC .. 486), the very edges C-ST-4 / RFI-A04 disputes against ST p.4 (45A .. 25E, {g_hi} "
                        f"goings); the same census holds the MS1-L flight {a['held_low']} .. {a['held_high']} lm on "
                        f"{g_lo} .. {g_hi} goings: a quantity is never more certain than its inputs (T-643 lesson)"}
        out.append({"line_id": lid, "item_code": l["item_code"], "unit": unit, "released": S(v),
                    "goings_counted": g_lo, "goings_disputed": [g_lo, g_hi],
                    "count_independent_of_held_riser_count": independent,
                    "ruling": "DOWNGRADE PROPOSED (not applied: a worker proposal; the Checker validates or refuses)",
                    "proposal": dg["proposal_id"]})
        proposals.append(dg)
    if len(out) != len(F_T645_1["codes"]):
        raise ManifestError(f"F-T645-1: {len(out)} released MS1-L tread / step lines, expected {len(F_T645_1['codes'])}")
    return out, proposals


# ---- T-646: roof falls screed AT_LEAST ---------------------------------------------------------------------------

def roof_rows(t646, idx, order, merged=None, source="T-646"):
    src = require_merged(source, merged)
    rows, lo = [], Decimal(0)
    for l in sorted((x for x in t646["lines"] if x.get("fix")), key=lambda x: x["line_id"]):
        f, lid = l["fix"], l["line_id"]
        _free(order, lid)
        line = _before_ok(idx, lid, f["before"])
        a = f["after"]
        if a["class"] != "HELD" or D(a["held_low"]) is None or a.get("held_high") is not None:
            raise ManifestError(f"{lid}: a T-646 screed row that is not AT_LEAST (low, high OPEN)")
        if line["item_code"] != "FIN.ROOF.SCREED":
            raise ManifestError(f"{lid}: not a FIN.ROOF.SCREED line")
        lo += D(a["held_low"])
        rows.append(M9.row(P_ROOF, f"R-T646-1/{l['element_id']}", "SET", lid, OV.state(line),
                           M9.held(float(D(a["held_low"])), None), "HELD", src["verdict"],
                           beside={"basis": f["basis"], "cause": l.get("cause") or "screed high end OPEN: the falls "
                                   "thickness above the strict low is not printed", "rule": "R-T646-1 AT_LEAST"}))
    v = t646["bounded_by_code"]["FIN.ROOF.SCREED"]
    if q6(lo) != q6(D(v["low"])) or v["high"] != "OPEN" or len(rows) != t646["counts"]["fix_rows"]:
        raise ManifestError(f"T-646: screed lows re-add to {S(lo)}, census says {v}")
    return rows, {"low_m3": S(lo), "high": "OPEN", "n": len(rows)}


# ---- T-650: lintel RC bounds (chained in T-498) -------------------------------------------------------------------

def lintel_rows(t650, idx, order, merged=None, source="T-650", pending=PENDING_IDS):
    src = require_merged(source, merged)
    po = t650["per_opening"]
    pairs = {i: (k, p) for k, p in t650["pairs"].items() for i in p["ids"]}
    chained, own, held_named, lo, hi, open_on = [], [], {}, Decimal(0), Decimal(0), []
    for oid in sorted(po):
        v = po[oid]
        lid = v["line_id"]
        line = M17._live(idx, lid, "STR.CONC.LINTEL", "m3")
        now = {"class": v["line_class_now"], "held_low": v["line_low_now"], "held_high": v["line_high_now"],
               "measured_net": None}
        if not OV.same_state(OV.state(line), now):
            raise ManifestError(f"{oid} {lid}: V17 {OV.state(line)} is not the T-650 'now' {now} (stale)")
        if v["state"] == "HELD" and oid not in pending:
            continue                                   # cause restated only: the trial BOQ reads it as a cause record
        pkg = _free(order, lid, allowed=(P498,))
        tgt, beside = (chained if pkg else own), {"opening": oid, "why": v["why"], "form": v["form"],
                                                  "rule": "R-T650-1 / R-T649-1 (g)"}
        if oid in pending:
            held_named[oid] = {"line": lid, "state": "HELD blank", "cause": f"{v['why']}; {PENDING}"}
            tgt.append(M9.row(pkg or P_LINT, f"R-T650-1/{oid}", "TEXT_ONLY", lid, OV.state(line), None, "HELD",
                              src["verdict"], beside=dict(beside, cause=f"{v['why']}; {PENDING}",
                                                          withheld_bound_m3=[v["low_m3"], v["high_m3"]])))
            continue
        if oid in pairs:
            pk, p = pairs[oid]
            first = p["ids"][0]
            if oid != first:
                held_named[oid] = {"line": lid, "state": "HELD blank (carried in the pair bound)",
                                   "cause": f"pair {pk}: range carried once on the {first} line (R-T524-1)"}
                tgt.append(M9.row(pkg or P_LINT, f"R-T650-1/{oid}", "TEXT_ONLY", lid, OV.state(line), None, "HELD",
                                  src["verdict"], beside=dict(beside, cause=f"pair {pk}: its range {p['low_m3']} .. "
                                                              f"{p['high_m3']} m3 is carried once on the {first} line "
                                                              f"({po[first]['line_id']}); HELD, never 0, never summed twice")))
                continue
            b_lo, b_hi = D(p["low_m3"]), D(p["high_m3"])
            beside = dict(beside, pair=pk, pier_m=p["pier_m"], ids=p["ids"])
        else:
            b_lo, b_hi = D(v["low_m3"]), D(v["high_m3"])
        if b_lo is None or b_lo <= 0 or (b_hi is not None and b_hi < b_lo):
            raise ManifestError(f"{oid}: bound {b_lo} .. {b_hi} is not a HELD range with a low end")
        lo += b_lo
        if b_hi is None:
            open_on.append(oid)
        else:
            hi += b_hi
        if v["change"] == "UNCHANGED":
            continue                                   # already the V17 state
        cause = v["why"] + ("; CHECKER-PARTIAL: width engine-read" if oid == "A-1F-01" else "")
        tgt.append(M9.row(pkg or P_LINT, f"R-T650-1/{oid}", "SET", lid, OV.state(line),
                          M9.held(float(b_lo), None if b_hi is None else float(b_hi)), "HELD", src["verdict"],
                          beside=dict(beside, cause=cause, state=v["state"])))
    sm = t650["summary"]["m3_bounded_set"]
    wl = sum((D(po[o]["low_m3"]) for o in pending if po[o]["low_m3"] is not None), Decimal(0))
    wh = sum((D(po[o]["high_m3"]) for o in pending if po[o]["high_m3"] is not None), Decimal(0))
    if q6(lo + wl) != q6(D(sm["low_m3"])) or q6(hi + wh) != q6(D(sm["high_known_part_m3"])) or \
            sorted(open_on) != sorted(sm["high_open_on"]):
        raise ManifestError(f"T-650: bounds re-add to {S(lo)} + withheld {S(wl)} .. {S(hi)} + {S(wh)}, summary {sm}")
    return chained, own, {"low_m3": S(lo), "high_known_part_m3": S(hi), "high_open_on": open_on,
                          "withheld": {o: [po[o]["low_m3"], po[o]["high_m3"]] for o in pending},
                          "withheld_low_high_m3": [S(wl), S(wh)], "held_named": held_named,
                          "t650_summary_m3": [S(D(sm["low_m3"])), S(D(sm["high_known_part_m3"]))]}


# ---- overlay ------------------------------------------------------------------------------------------------------

def v17_state():
    """the T-641 build up to its overlay (read only, same calls, same order), so V18 steps from the exact V17 state."""
    M17.pins()
    t628, t638, t639, t640 = (M17._json(M17.IN[k]) for k in ("T628", "T638", "T639", "T640"))
    idx, after15, order16, rul16, after16, rep16, stair, t584 = M17.v16_state()
    moves = M17.finish_moves(stair, (M17.GF_PORC, M17.F1_PORC))
    bed, rul_b, _ = M17.bed_rows(after15, after16, order16, moves, source="T-631")
    band, _ = M17.band_row(t628, after16, order16)
    fw, _ = M17.formwork_rows(t638, after16, order16)
    bars, _ = M17.bars_rows(t639, after16, order16)
    fin, fin_ret, _, _ = M17.finish_rows(t640, after16, order16)
    order17 = M15.chain_into(order16, M17.P_RET, fin_ret) + \
        [(M17.P_BED, bed), (M17.P_BAND, [band]), (M17.P_FW, fw), (M17.P_BARS, bars), (M17.P_FIN, fin)]
    rul17 = list(rul16) + rul_b
    after17, rep17 = OV.apply(idx, order17, rul17)
    return idx, order17, rul17, after17, rep17, t584


def check_v17(after17, v17j):
    if len(after17) != v17j["overlay"]["lines"]["after_v17"]:
        raise ManifestError("V17 state rebuild differs from the committed V17 line count")
    t17 = OV.totals(after17)
    for k, v in v17j["overlay"]["v17_vs_v16_totals"].items():
        if t17[k] != v["after"]:
            raise ManifestError(f"{k}: V17 rebuild totals differ from the committed V17")
    last = {}
    for r in v17j["rows"]:
        if r["kind"] in ("ADD", "SET"):
            last[r["line_id"]] = r
    for r in last.values():
        if not OV.same_state(OV.state(after17[r["line_id"]]), r["after"]):
            raise ManifestError(f"{r['line_id']}: V17 rebuild differs from the committed V17 row")
    return t17


def v18_order(order17, rows):
    """V18 packages after V17; lintel rows on T-498 lines chain inside T-498 (R1)."""
    order18 = M15.chain_into(order17, P498, rows["lintel_chained"])
    new = [(P_STRIP, rows["strip"]), (P_DG, rows["downgrades"]), (P_STAIR, rows["stair"]), (P_ROOF, rows["roof"])]
    if rows["lintel_own"]:
        new.append((P_LINT, rows["lintel_own"]))
    return order18 + new


def build_rows(idx_after17, order17, src):
    strip, strip_out = strip_rows(src["T642"], idx_after17, order17)
    dg, dg_out = downgrade_rows(src["T643"], idx_after17, order17)
    stair, stair_out = stair_rows(src["T645"], idx_after17, order17)
    ruling, proposals = mstair_ruling(src["T645"], idx_after17, order17, stair)
    roof, roof_out = roof_rows(src["T646"], idx_after17, order17)
    lch, lown, lint_out = lintel_rows(src["T650"], idx_after17, order17)
    rows = {"strip": strip, "downgrades": dg, "stair": stair, "roof": roof, "lintel_chained": lch, "lintel_own": lown}
    outs = {"strip": strip_out, "downgrades": dg_out, "stair": stair_out, "roof": roof_out, "lintels": lint_out,
            "f_t645_1": {"lines": ruling, "proposals": proposals}}
    return rows, outs


def overlay_v18():
    """(idx, order18, rul18, after18, rep18, after17, rep17, rows, outs, src, t584): the full V18 state."""
    pins()
    src = {k: _json(IN[k]) for k in ("T642", "T643", "T645", "T646", "T650", "T633")}
    idx, order17, rul17, after17, rep17, t584 = v17_state()
    check_v17(after17, _json(IN["V17"]))
    rows, outs = build_rows(after17, order17, src)
    allrows = [r for v in rows.values() for r in v]
    M9.validate_rows(allrows)
    order18 = v18_order(order17, rows)
    rul18 = list(rul17) + stair_rulings(rows["stair"], after17)
    after18, rep18 = OV.apply(idx, order18, rul18)
    outs["rulings_v18"] = rul18[len(rul17):]
    return idx, order18, rul18, after18, rep18, after17, rep17, rows, outs, src, t584


def statement_only(t633):
    r = next(x for x in t633["rows"] if x.get("opening") == "D-GF-06" and x.get("statement_class") == "RULE_DIFFERENCE")
    return [{"op": "STATEMENT_CLASS_MOVE", "source": "T-633", "row": r["name"], "index": r["index"],
             "from": r["statement_class"], "to": r["class_proposed"], "delta_m2": r["own_delta"],
             "basis": r["basis"], "lines": 0,
             "why": "his 2.40 head vs the drawn 2.20 (T-627 binding) is not an owner-rule difference: statement V12 "
                    "(T-635) carries the class; no engine line moves"}]


def build():
    idx, order18, rul18, after18, rep, after17, rep17, rows, outs, src, t584 = overlay_v18()
    v17j = _json(IN["V17"])
    t17 = check_v17(after17, v17j)
    sources, refused = no_row_sources()
    allrows = [r for v in rows.values() for r in v]
    qrows = [r for r in allrows if r["kind"] in ("ADD", "SET", "RECODE")]
    v18_lines = {r["line_id"] for r in qrows}
    others = sorted(k for k in set(after17) | set(after18) if k not in v18_lines and after17.get(k) != after18.get(k))
    if others:
        raise ManifestError(f"lines V18 does not write changed: {others[:5]}")
    t18 = OV.totals(after18)
    dt = OV.diff_totals(t17, t18)
    writes = sorted({f"{(r.get('item_code') or after17[r['line_id']]['item_code'])}|"
                     f"{(r.get('unit') or after17[r['line_id']].get('unit'))}" for r in qrows})
    if sorted(dt) != writes:
        raise ManifestError(f"totals moved on {sorted(dt)}, V18 writes {writes}")
    if any(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]):
        raise ManifestError(f"unexplained conflicts: {[c for c in rep['conflicts'] if c['status'] == 'UNEXPLAINED']}")
    flagged = [r for r in rep["rows"] if r["status"] != "APPLIED"]
    v18_ops = {r["op_id"] for r in allrows}
    if any(r["op_id"] in v18_ops for r in flagged):
        raise ManifestError(f"a V18 row is not APPLIED: {[r for r in flagged if r['op_id'] in v18_ops]}")
    if len(flagged) != len([r for r in rep17["rows"] if r["status"] != "APPLIED"]):
        raise ManifestError("the flagged rows of V17 changed")
    # hand acceptance per key
    bk = "STR.REBAR|kg"
    b11 = q6(D(t18[bk]["released"]))
    if b11 != q6(D(t17[bk]["released"]) - D(outs["downgrades"]["kg"])) or \
            b11 != q6(D(outs["downgrades"]["t643_base_kg"][1]) + Decimal("412.444445")):
        raise ManifestError(f"B11 released {S(b11)} is not 9216.017760 + the T-639 overlay 412.444445")
    if t18[bk]["held_blank_n"] != t17[bk]["held_blank_n"] + 4:
        raise ManifestError("the 4 downgraded rebar lines are not HELD blank")
    rk = {"FIN.MARBLE.RISER|m2", "FIN.STAIR.FLIGHT|lm"}
    for k in rk:
        code = k.split("|")[0]
        if q6(D(t18[k]["released"]) - D(t17[k]["released"])) != q6(D(outs["stair"]["released"][code])):
            raise ManifestError(f"{k} released did not move by the T-645 rows")
    sk = "FIN.ROOF.SCREED|m3"
    if q6(D(t18[sk]["held_low"]) - D(t17[sk]["held_low"])) != q6(D(outs["roof"]["low_m3"])) or \
            t18[sk]["held_high_open_n"] - t17[sk]["held_high_open_n"] != 3:
        raise ManifestError("roof screed AT_LEAST did not move by the T-646 rows")
    beam = "STR.CONC.BEAM|m3"
    if q6(D(t18[beam]["released"]) - D(t17[beam]["released"])) != q6(D(outs["strip"]["released_m3"])) or \
            q6(D(t17[beam]["held_high"]) - D(t18[beam]["held_high"])) != \
            q6(D(outs["strip"]["replaced"][1]) - D(outs["strip"]["companion_m3"][1])):
        raise ManifestError("beam concrete did not move by FR-T642-2 (released low end + companion)")
    status = {}
    for r in rep["rows"]:
        status.setdefault(r["package"], {}).setdefault(r["status"], 0)
        status[r["package"]][r["status"]] += 1
    M11 = M15.M11
    t412 = M11.load_t412()
    nrows, _ = M11.nosing_ledger(t412, M11._json(M11.IN["T598"]))
    cen = M9.census_on(after18, M11.census_edges(t412, nrows), t584, {M9.E1_LINE: ("ST-03", "E1")})
    if cen["doubles"] or cen["orphans"]:
        raise ManifestError("stair census doubles / orphans after V18")
    table = []
    for r in allrows:
        b, a = r.get("before"), r.get("after")
        table.append({"row": r["row"], "package": r["package"], "kind": r["kind"], "line_id": r["line_id"],
                      "item": r.get("item_code") or after17[r["line_id"]]["item_code"],
                      "before": None if b is None else {k: b[k] for k in OV.QFIELDS},
                      "after": None if a is None else {k: a[k] for k in OV.QFIELDS},
                      "evidence": r["evidence"]["status"]})
    by_ev = {}
    for r in allrows:
        by_ev[r["evidence"]["status"]] = by_ev.get(r["evidence"]["status"], 0) + 1
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-649", "candidate": M9.T580.CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in IN.values()},
        "sources_merged": {k: v["merge"] for k, v in MERGED.items()},
        "sources_no_row": sources, "sources_refused": refused,
        "statement_only_ops": statement_only(src["T633"]),
        "held_not_wired": {"T-642": listed_t642(src["T642"]),
                           "T-646": f"{len(src['T646']['lines']) - outs['roof']['n']} lines stay HELD blank with their "
                                    "census cause (trial BOQ r2 cause source)",
                           "T-650": f"{sum(1 for v in src['T650']['per_opening'].values() if v['state'] == 'HELD')} "
                                    "lines CAUSE_RESTATED (HELD blank, trial BOQ r2 cause source); "
                                    + "; ".join(f"{k} {v['state']}" for k, v in outs["lintels"]["held_named"].items())},
        "f_t645_1": outs["f_t645_1"],
        "line_table": table,
        "rows": [dict(r) for r in allrows],
        "rows_by_evidence": by_ev,
        "strip": {**outs["strip"], "totals": {beam: {"v17": t17[beam], "v18": t18[beam]}}},
        "downgrades": {**outs["downgrades"], "totals": {bk: {"v17": t17[bk], "v18": t18[bk]}}},
        "stair": {**outs["stair"], "totals": {k: {"v17": t17.get(k), "v18": t18.get(k)} for k in dt
                                              if k.startswith(("FIN.MARBLE", "FIN.STAIR"))}},
        "roof": {**outs["roof"], "totals": {sk: {"v17": t17[sk], "v18": t18[sk]}}},
        "lintels": {**outs["lintels"], "totals": {k: {"v17": t17.get(k), "v18": t18.get(k)} for k in dt
                                                  if k.startswith("STR.CONC.LINTEL")}},
        "overlay": {
            "lines": {"base": len(idx), "after_v17": len(after17), "after_v18": len(after18)},
            "order": [{"package": n, "ops": len(o), "status": status.get(n, {})} for n, o in order18],
            "flagged_rows": flagged,
            "stale": sum(r["status"] == "STALE" for r in rep["rows"]),
            "two_package_lines": 0,                     # OV.apply raises R1 otherwise
            "unexplained_conflicts": sum(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]),
            "conflicts": [c for c in rep["conflicts"] if any(l in v18_lines for l in c["lines"])],
            "rulings_v18": outs["rulings_v18"],
            "other_lines_changed_vs_v17_overlay": others,
            "v18_vs_v17_totals": dt,
        },
        "stair_edge_census_after_v18": {"edges": cen["edges"], "doubles": len(cen["doubles"]),
                                        "orphans": len(cen["orphans"])},
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n"


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    return b


def main(argv):
    text = dumps(build())
    if "--check" in argv:
        ok = OUT_JSON.exists() and OUT_JSON.read_text(encoding="utf-8") == text
        print("T-649 manifest V18: committed output", "is the rebuild" if ok else "DIFFERS from the rebuild")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
