"""T-652 WIRING MANIFEST V19 + overlay dry run on ARCH_TAKEOFF_V3.0.59 (R-T652-1; lane I, non-candidate, research only).

V19 moves the overlay base from the V3.0.58 copy (4,999 lines) to the merged candidate ARCH_TAKEOFF_V3.0.59 (T-498,
Gate B MERGED 4c37ce2c: + 74 blockwork material lines) and carries the verdicts recorded after V18 (T-649, MERGED
89afbd85; claim 2026-11-09T11:07Z):
  - BASE V3.0.59: the 74 ADD rows the overlay package 'T-498' carried since V15 ARE the merged V3.0.59 stage (same line
    id, item, unit, element, state; the summary of record research/agents_t498/summary_t498.json). They leave the
    overlay (the lines are now the candidate's own); every other T-498 row (V2 lintel classes, FR-T615 0.15 m hosts,
    perimeter keys, lintel bars / ceilings) stays chained in the package after them. Proof: the V18 overlay re-applied on
    the V3.0.59 base gives every one of the 5,152 lines byte-equal to V18.
  - F-C-T498-1 (Lead): the 6 valued 0.15 m black hosts are carried by FR-T615-1 / -2 (T-615 MERGED, Checker AGREE) in the
    T-498 package; re-derived here at the V3.0.59 host nets from the merged line records (contract net - REQUIRED RC
    lintel faces x 12.5 / m2, low end released, the HELD face its companion): no row added, the candidate's stale
    'module not stated' text is answered by Q-80 and named as retired.
  - T-650 Checker re-measure (Verifier 2026-11-09 07:06): D-1F-07 HELD BY NAME 0.036 .. 0.04377 m3 (START 0.259 < printed
    MIN 0.40: designer item); L-GF-01 stays HELD blank by the register LIFT LANDING DOOR LINTEL (existence), bearing
    0.40 at printed precision (F-T650-3), RC 0.072 m3 beside only. Replaces the two V18 'Checker re-measure pending'
    rows in their own packages (R1).
  - T-647 r2 (MERGED a521da8a): FR-T647-1 .. -5 the 5 CN column lines above ground -> EXCLUDED (NOT_APPLICABLE WITH
    EVIDENCE: ST p.9 row CN cells struck; a printed absence, not a value); the 17 B11 COUNT-CONVENTION GAP lines are
    already HELD on their bound in the index: listed and checked, no row.
  - T-648 r2 (MERGED 57db7053): its one fix row, the A-GF-01 threshold strip 1.000 x 0.150 = 0.150 m2 DRAWING-CONFIRMED
    (Checker own read AGREE), HELD blank -> RELEASED.
  - T-649 verdict (F-T645-1 RULED): DGP-T649-2543430910268708 / -a20e51752f360854 CHECKER-VALIDATED: MS1-L tread
    3.105 -> HELD 3.105 .. 3.795 m2, MS1-L step 10.35 -> HELD 10.35 .. 12.65 lm (downgrade only, never 0).
  - F-C-T635-1 (Verifier, T-635): the two B10 beams COUNT rows of statement V12 restated PARTIALLY VERIFIED (statement
    op, no line).

R-T652-1 (every villa on the engine's line-index scheme; adds to R-T649-1, which stands whole):
  (a) A MERGED STAGE BECOMES THE BASE ONLY BY EQUALITY: an overlay ADD on a line the merged stage now carries leaves
      the overlay only when line id, item, unit, element and quantity state are equal; any difference is refused.
      The rest of the overlay is re-applied unchanged and must give every line byte-equal.
  (b) A CHECKER RE-MEASURE REPLACES THE PENDING ROW IN ITS PACKAGE (R1): the bound the Checker states is wired with
      its own status; a line the register holds keeps HELD blank with the re-measure named.
  (c) NOT_APPLICABLE is written only on a HELD line, from a merged fix row whose evidence is a printed absence;
      a released line, or a value, is never moved to EXCLUDED.
  (d) A DOWNGRADE WITH A BOUND (validated by the Checker) moves a RELEASED line to HELD low .. high with the released
      value as its low end; never 0, never a value.
  (e) A FREELANCER FIGURE IS NEVER A SOURCE: a row whose source names the freelancer workbook is refused.
Rebuild: `URBAN_T652_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-652
tests/t652_manifest_v19/test_t652.py::test_write_outputs`; check: `... pytest --tree task-T-652 tests/t652_manifest_v19`.
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
T649_DIR = ROOT / "research/agents_t649"
if str(T649_DIR) not in sys.path:
    sys.path.insert(0, str(T649_DIR))

import manifest_v18 as M18                                            # noqa: E402  (R-T649-1, read only)

M17, M15, M9, OV = M18.M17, M18.M15, M18.M9, M18.OV
D, S, q6 = M18.D, M18.S, M18.q6

SCHEMA = "URBAN_T652_WIRING_MANIFEST_V19"
RULE = "R-T652-1"
OUT_JSON = HERE / "out/WIRING_MANIFEST_V19.json"
CANDIDATE = "ARCH_TAKEOFF_V3.0.59 (T-498 Gate B MERGED 4c37ce2c: V3.0.58 4,999 lines + 74 material lines = 5,073)"
IN = {
    "T498": ROOT / "research/agents_t498/summary_t498.json",
    "T647": ROOT / "research/agents_t647/out/HELD_CAUSE_CENSUS_T647.json",
    "T648": ROOT / "research/agents_t648/out/FINISH_HOLD_CAUSE_CENSUS_T648.json",
    "T650": ROOT / "research/agents_t650/out/T650_PAYABLE_FORM.json",
    "T635": ROOT / "research/agents_t635/out/RECONCILED_STATEMENT_T635.json",
    "V18": T649_DIR / "out/WIRING_MANIFEST_V18.json",
    "V18_CODE": T649_DIR / "manifest_v18.py",
}
PINS = {
    "T498": "47737dc2b80b3b656cb57b306b84c695bae3abaab2097c744993798ef9a46765",
    "T647": "610c67b00aab02008db78c30f2056b685e3917a6135071c64b6affb5b3ef0d66",
    "T648": "767d1d3a969a548cd78e144c9d89a191658922d181adf050d774a33df634fcc9",
    "T650": "cd72b44596cc1b2840282ab56f1f6653a7b53b5601db2bb9f3f7bcb7eb0a1fb2",
    "T635": "7820d46acf2507629bcf0d96379a7abb681fcfb8e7eed832dacc4447d06b2965",
    "V18": "08a5d7ff83639c6eea97eb97f6f25cf7abdbe97ef7bb696a73a2a7f3d237eda8",
    "V18_CODE": "e8a24eb1e98414f67fa5f3725022ebeeb53bc0ae88c9616d2a6be45a0b2303b4",
}

# R-T649-1 (a): board MERGED verdicts at claim (2026-11-09T11:07Z; Verifier text abridged, full text on BOARD.md)
MERGED = {
    "T-498": {"merge": "4c37ce2c",
              "verdict": "BOARD T-498 VERIFIER 2026-11-09T05:54Z: GATE B PASS; V3_0_58 c9570e6c -> V3_0_59 75331a76 "
                         "REPRODUCED, 4,999 byte-identical + 74 added; by hand 9 / 9 non-blank lines AGREE; unit / mortar "
                         "lines are DRAWING-CONFIRMED products of VERIFIED hosts x OWNER-CONFIRMED rates (mortar ASSUMED - "
                         "OWNER-APPROVED, 10 mm joint), not new VERIFIED whole lines; 65 blank lines name their cause"},
    "T-615": {"merge": "T-615 MERGED (Verifier 2026-11-08T08:21Z)",
              "verdict": "BOARD T-615 VERIFIER 2026-11-08T08:21Z: GATE A PASS; 15 wall bases 175.871 (low 175.531) -> "
                         "units 2,198.3875 (low 2,194.1375) AGREE; panel 0.0110625 m3 / m2 AGREE; statuses ASSUMED - "
                         "OWNER-APPROVED; waste / procurement HELD"},
    "T-650": {"merge": "2a2e28ca",
              "verdict": "BOARD T-650 CHECKER RE-MEASURE (Verifier 2026-11-09 07:06): D-1F-07 START available 0.259 < "
                         "printed MIN 0.40 (FLAGGED_DEFICIT), END >= 0.40; 0.15 x 0.20 x (0.80 + 0.40) = 0.036 .. 0.15 x "
                         "0.20 x (0.80 + 0.40 + 0.259) = 0.04377 m3 AGREE, stays HELD BY NAME (designer item). L-GF-01: "
                         "jamb to inner corner 0.40000 / 0.40000 m at full DXF precision (F-T650-3 bearing 0.40 at "
                         "printed precision AGREE); RC beside only 0.20 x 0.20 x (1.00 + 2 x 0.40) = 0.072 m3; stays "
                         "HELD by the register LIFT LANDING DOOR LINTEL (existence), never 0; 'Checker re-measure "
                         "pending' LIFTED"},
    "T-647": {"merge": "a521da8a",
              "verdict": "BOARD T-647 VERIFIER 2026-11-09 06:56: GATE A PASS on r2; 17 lines HELD PRINTED_VALUE_GAP "
                         "'COUNT-CONVENTION GAP' 51.574073 kg at A and at A + 1 (a bound, not summed into any total); "
                         "fix rows FR-T647-1 .. 5 (CN NA) only; CN x 5 ST p.9 AGREE"},
    "T-648": {"merge": "57db7053",
              "verdict": "BOARD T-648 VERIFIER 2026-11-09T09:00Z: Gate A PASS (r2); OWN RE-READ: FIX ROW L-868aee12 "
                         "A-GF-01: P7757.dxf faces 1.000 m apart, 0.150 m deep, insert 'arch120' between: 1.000 x 0.150 "
                         "= 0.150 m2 DRAWING-CONFIRMED AGREE (ENGINE_WRONG blank line)"},
    "T-649": {"merge": "89afbd85",
              "verdict": "BOARD T-649 VERIFIER 2026-11-09 06:59: F-T645-1 RULED: DGP-T649-2543430910268708 (MS1-L tread "
                         "3.105 -> HELD 3.105 .. 3.795 m2) and DGP-T649-a20e51752f360854 (MS1-L step 10.35 -> HELD 10.35 "
                         ".. 12.65 lm) CHECKER-VALIDATED (downgrade-only, owner 2026-10-24 23:57); the next manifest (V19) "
                         "applies them"},
    "T-635": {"merge": "abc71ec6",
              "verdict": "BOARD T-635 VERIFIER: F-C-T635-1: B10 T-545/beams rows GF / 1F COUNT -4.576422 / -5.306035 m3 "
                         "carry CHECKER_VERIFIED from the T-545 05:58 verdict that re-measured only B27 and itself said "
                         "PARTIALLY VERIFIED: restate PARTIALLY VERIFIED (statement fold, no candidate quantity)"},
}
P498 = M18.P498
P_LINT = M18.P_LINT
P_CN = "CN_NOT_APPLICABLE (T-647 FR-T647-1 .. -5)"
P_THR = "THRESHOLD_STRIP_A_GF_01 (T-648 fix row)"
P_DGV = "CHECKER_DOWNGRADES_F_T645_1 (T-649 DGP-T649-*)"
REMEASURED = {"D-1F-07": (Decimal("0.036"), Decimal("0.04377")), "L-GF-01": None}
RC_BESIDE_L_GF_01 = Decimal("0.072")
UNITS_PER_M2 = Decimal("12.5")                          # UPC-BLACK-BLOCK-001 1.1.0 (Q-80 A): 1 / (0.40 x 0.20)
PANEL_015 = Decimal("0.0110625")                        # 0.15 x (1 - 0.39 x 0.19 / 0.08) m3 / m2 (T-615, Checker AGREE)
STALE_MODULE = "module of the 0.15 m black block is not stated"
STAGE_STATES = {"BLOCKED_RFI": "HELD", "SOURCE_DERIVED": "RELEASED", "PROVISIONAL": "RELEASED",
                "BOUNDED_EXPOSURE": "HELD"}
FREELANCER_RE = re.compile(r"freelancer|workbook", re.I)
DGV = {"DGP-T649-2543430910268708": ("L-151d92470a81dd1c450b", "FIN.MARBLE.TREAD", "m2", "3.105", "3.795"),
       "DGP-T649-a20e51752f360854": ("L-d4d764ae7bb07b474b6f", "FIN.STAIR.STEP_LM", "lm", "10.35", "12.65")}


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


def no_freelancer(text):
    """R-T652-1 (e)."""
    if FREELANCER_RE.search(str(text or "")):
        raise ManifestError(f"a freelancer figure is never a source: {str(text)[:80]}")


def row(pkg, rid, kind, lid, before, after, evidence, verdict, beside=None, **kw):
    no_freelancer((beside or {}).get("basis"))
    try:
        return M15.row(pkg, rid, kind, lid, before, after, evidence, verdict, beside=beside, **kw)
    except (M15.ManifestError, M9.ManifestError) as e:
        raise ManifestError(str(e)) from None


# ---- (a) the V3.0.59 base -----------------------------------------------------------------------------------------

def stage_state(r):
    a = r["after"]
    cls = STAGE_STATES.get(a["state"])
    if cls is None:
        raise ManifestError(f"{r['line_id']}: stage state {a['state']} has no index class")
    if cls == "RELEASED":
        if a["value"] is None:
            raise ManifestError(f"{r['line_id']}: a released stage line without a value")
        return M9.released(a["value"])
    if a["state"] == "BOUNDED_EXPOSURE":
        if a["low"] is None or a["high"] is None:
            raise ManifestError(f"{r['line_id']}: a bounded stage line without its bound")
        return M9.held(a["low"], a["high"])
    if a["value"] is not None or a["low"] is not None:
        raise ManifestError(f"{r['line_id']}: a blank stage line carries a figure (HELD is never a value)")
    return M9.held()


def stage_lines(t498):
    """the merged V3.0.59 stage as index lines (line id, item, unit, element, state)."""
    out = {}
    for r in t498["rows"]:
        if r["line_id"] in out:
            raise ManifestError(f"{r['line_id']}: two stage rows")
        out[r["line_id"]] = {"line_id": r["line_id"], "item_code": r["item_code"], "unit": r["unit"],
                             "element_id": r["element_id"], **stage_state(r)}
    return out


def base_v3059(idx58, stage):
    clash = sorted(set(idx58) & set(stage))
    if clash:
        raise ManifestError(f"stage lines already in the V3.0.58 base: {clash[:3]}")
    return {**idx58, **stage}


def rebase(order, stage, pkg=P498):
    """(a): drop the overlay ADD rows the merged stage now carries, each only when equal; returns (order, removed)."""
    out, removed, seen = [], [], set()
    for name, ops in order:
        keep = []
        for op in ops:
            lid = op["line_id"]
            if op["kind"] == "ADD" and lid in stage:
                if name != pkg:
                    raise ManifestError(f"{lid}: a stage line added by {name}, not by {pkg}")
                s = stage[lid]
                same = (op["item_code"], op["unit"], op["element_id"]) == (s["item_code"], s["unit"], s["element_id"]) \
                    and OV.same_state(op["after"], s)
                if not same:
                    raise ManifestError(f"{lid}: the overlay ADD {OV.state(op['after'])} is not the merged V3.0.59 "
                                        f"line {OV.state(s)}: refused (R-T652-1 (a))")
                removed.append(op["op_id"])
                seen.add(lid)
                continue
            keep.append(op)
        out.append((name, keep))
    missing = sorted(set(stage) - seen)
    if missing:
        raise ManifestError(f"stage lines the overlay never added: {missing[:3]} (the base move is not an identity)")
    return out, removed


# ---- F-C-T498-1: the 0.15 m black hosts re-derived at the V3.0.59 nets --------------------------------------------

def hosts_015(t498, idx, after):
    """per 0.15 m valued host: contract net (V3.0.59 MAS.BLOCK line) - REQUIRED faces = base; HELD faces = companion."""
    rows, tot = [], {"contract_m2": Decimal(0), "base_m2": Decimal(0), "low_m2": Decimal(0), "units_low": Decimal(0),
                     "units_high": Decimal(0), "panel_low": Decimal(0), "panel_high": Decimal(0)}
    by_host = {}
    for r in t498["rows"]:
        if "t=0.15" not in r["element_id"] or r["item_code"] not in ("MAS.UNITS.BLACK", "MAS.MORTAR.BLACK"):
            continue
        by_host.setdefault(r["source_line_id"], {})[r["item_code"]] = r
    for host, recs in sorted(by_host.items()):
        u, m = recs.get("MAS.UNITS.BLACK"), recs.get("MAS.MORTAR.BLACK")
        if u is None or m is None or u["contract_net_m2"] is None:
            continue                                                   # a held host: its materials follow it
        hl = idx[host]
        if hl["class"] != "RELEASED" or D(hl["measured_net"]) != D(u["contract_net_m2"]):
            raise ManifestError(f"{host}: V3.0.59 host net {hl.get('measured_net')} is not the record's "
                                f"{u['contract_net_m2']} (stale)")
        req = sum((D(f["face_m2"]) for f in u["lintels"] if f["kind"] == "REQUIRED"), Decimal(0))
        hld = sum((D(f["face_max_m2"]) for f in u["lintels"] if f["kind"] != "REQUIRED"), Decimal(0))
        c = D(hl["measured_net"])
        base, low = c - req, c - req - hld
        ul, uh = q6(low * UNITS_PER_M2), q6(base * UNITS_PER_M2)
        pl, ph = q6(low * PANEL_015), q6(base * PANEL_015)
        lu, lm = after[u["line_id"]], after[m["line_id"]]
        if lu["class"] != "RELEASED" or D(lu["measured_net"]) != ul or lm["class"] != "RELEASED" or \
                q6(D(lm["measured_net"])) != pl:
            raise ManifestError(f"{host}: overlay units / mortar {lu.get('measured_net')} / {lm.get('measured_net')} "
                                f"are not the re-derivation {S(ul)} / {S(pl)} at the V3.0.59 net")
        if "not stated" not in u["why"]:
            raise ManifestError(f"{u['line_id']}: the candidate text is not the 'module not stated' hold")
        rows.append({"host": host, "element": u["element_id"].split("#", 1)[-1], "contract_net_m2": S(c),
                     "required_faces_m2": S(req), "held_faces_m2": S(hld),
                     "faces": [f"{f['opening_id']} {f['face_m2'] or f['face_max_m2']} ({f['kind']})" for f in u["lintels"]],
                     "units_line": u["line_id"], "units": [S(ul), S(uh)], "mortar_line": m["line_id"],
                     "panel_mortar_m3": [S(pl), S(ph)],
                     "candidate_text_retired": u["why"], "answered_by": "Q-80 A (owner 2026-11-07: 40 x 20, 12.5 / m2)"})
        for k, v in (("contract_m2", c), ("base_m2", base), ("low_m2", low), ("units_low", ul), ("units_high", uh),
                     ("panel_low", pl), ("panel_high", ph)):
            tot[k] += v
    return rows, {k: S(v) for k, v in tot.items()}


# ---- (b) Checker re-measure of D-1F-07 / L-GF-01 -----------------------------------------------------------------

def remeasure_rows(t650, order, idx_after, merged=None):
    src = require_merged("T-650", merged)
    po = t650["per_opening"]
    out, replaced = {}, []
    for oid, bound in REMEASURED.items():
        v = po[oid]
        lid = v["line_id"]
        line = M17._live(idx_after, lid, "STR.CONC.LINTEL", "m3")
        if line["class"] != "HELD" or line["held_low"] is not None or line["held_high"] is not None:
            raise ManifestError(f"{oid} {lid}: not the HELD blank line V18 left pending")
        pend = [(n, op) for n, ops in order for op in ops if op["line_id"] == lid and op["kind"] == "TEXT_ONLY"
                and "re-measure pending" in str((op.get("beside") or {}).get("cause"))]
        if len(pend) != 1:
            raise ManifestError(f"{oid}: {len(pend)} pending rows (expected the one V18 row)")
        pkg, old = pend[0]
        why = v["why"]
        if bound is not None:
            lo, hi = bound
            if (D(v["low_m3"]), D(v["high_m3"])) != (lo, hi):
                raise ManifestError(f"{oid}: census bound {v['low_m3']} .. {v['high_m3']} is not the Checker's "
                                    f"{S(lo)} .. {S(hi)}")
            r = row(pkg, f"R-T652-1/{oid}", "SET", lid, OV.state(line), M9.held(float(lo), float(hi)), "HELD",
                    src["verdict"], beside={"opening": oid, "cause": f"{why}; Checker re-measured 2026-11-09 07:06: "
                                            f"START 0.259 < printed MIN 0.40, HELD BY NAME (designer item)",
                                            "hand": "0.15 x 0.20 x (0.80 + 0.40) = 0.036 .. 0.15 x 0.20 x (0.80 + 0.40 "
                                                    "+ 0.259) = 0.04377 m3", "rule": "R-T652-1 (b) / R-T524-1"})
        else:
            r = row(pkg, f"R-T652-1/{oid}", "TEXT_ONLY", lid, OV.state(line), None, "HELD", src["verdict"],
                    beside={"opening": oid, "cause": f"{why}; Checker re-measured 2026-11-09 07:06 (bearing 0.40 at "
                                                     "printed precision, F-T650-3); RC beside only "
                                                     f"{S(RC_BESIDE_L_GF_01)} m3 (0.20 x 0.20 x 1.80), never a quantity",
                            "rule": "R-T652-1 (b): the register holds existence"})
        out[old["op_id"]] = r
        replaced.append({"opening": oid, "line": lid, "package": pkg, "replaces": old["op_id"], "kind": r["kind"]})
    return out, replaced


def replace_ops(order, repl):
    seen, out = set(), []
    for name, ops in order:
        new = []
        for op in ops:
            if op["op_id"] in repl:
                new.append(dict(repl[op["op_id"]], package=name))
                seen.add(op["op_id"])
            else:
                new.append(op)
        out.append((name, new))
    if seen != set(repl):
        raise ManifestError(f"rows to replace not found: {sorted(set(repl) - seen)}")
    return out


# ---- (c) T-647 CN NOT_APPLICABLE, count-convention gaps listed ---------------------------------------------------

def cn_rows(t647, idx, order, merged=None):
    src = require_merged("T-647", merged)
    rows = []
    for f in t647["fix_rows"]:
        if f["proposed_state"] != "NOT_APPLICABLE_WITH_EVIDENCE" or not f.get("inputs_printed"):
            raise ManifestError(f"{f['id']}: not a printed-absence NOT_APPLICABLE fix row")
        lid = f["line_id"]
        M18._free(order, lid)
        line = M17._live(idx, lid, "STR.CONC.COLUMN", "m3")
        if line["class"] != "HELD" or line.get("measured_net") is not None:
            raise ManifestError(f"{f['id']}: {lid} is {line['class']}: NOT_APPLICABLE only moves a HELD line "
                                "(R-T652-1 (c))")
        rows.append(row(P_CN, f["id"], "SET", lid, OV.state(line), M9.excluded(), "DRAWING-CONFIRMED", src["verdict"],
                        beside={"basis": f["hand_calculation"], "evidence": f["evidence"],
                                "verdict_proposal": f["verdict_proposal"],
                                "rule": "R-T652-1 (c): a printed absence, not a value"}))
    if len(rows) != 5:
        raise ManifestError(f"T-647: {len(rows)} CN rows (expected 5)")
    return rows


def count_gaps(t647, after):
    """the 17 B11 lines the census holds on the count convention: their index bound is the census kg (3 dp)."""
    out, ka, kb = [], Decimal(0), Decimal(0)
    for g in t647["count_convention_gaps"]:
        l = after[g["line_id"]]
        a, b = D(g["kg_A"]), D(g["kg_B"])
        lo, hi = min(a, b), max(a, b)
        if l["class"] != "HELD" or l.get("measured_net") is not None or \
                abs(D(l["held_low"]) - lo) > Decimal("0.0005") or abs(D(l["held_high"]) - hi) > Decimal("0.0005"):
            raise ManifestError(f"{g['line_id']}: index {OV.state(l)} is not the census bound {S(lo)} .. {S(hi)}")
        ka += a
        kb += b
        out.append({"line_id": g["line_id"], "bars": [g["bars_A"], g["bars_B"]], "kg": [S(a), S(b)],
                    "index_bound": [l["held_low"], l["held_high"]]})
    return out, {"n": len(out), "kg_A": S(ka), "kg_A_plus_1": S(kb)}


# ---- (d) T-648 fix row, F-T645-1 validated downgrades ------------------------------------------------------------

def threshold_row(t648, idx, order, merged=None):
    src = require_merged("T-648", merged)
    if len(t648["fix_rows"]) != 1:
        raise ManifestError("T-648: expected one fix row")
    f = t648["fix_rows"][0]
    lid = f["line_id"]
    M18._free(order, lid)
    line = idx[lid]
    if line["class"] != "HELD" or line["held_low"] is not None or f["kind"] != "SET":
        raise ManifestError(f"{lid}: the T-648 fix row is not a HELD blank line")
    w, d = (D(f["terms"][k][0]) for k in ("clear_width_m", "wall_depth_m"))
    if q6(w * d) != D(f["value"]) or (line["item_code"], line["unit"]) != ("ARCH.THRESHOLD", f["unit"]):
        raise ManifestError(f"{lid}: {S(w)} x {S(d)} is not {f['value']} {f['unit']}")
    return row(P_THR, "FR-T648-1", "SET", lid, OV.state(line), M9.released(float(D(f["value"]))), "DRAWING-CONFIRMED",
               src["verdict"], beside={"basis": f["basis"], "hand": f"{S(w)} x {S(d)} = {f['value']} m2",
                                       "rule": "R-T649-1 (e): a census fix row enters as its merged source states it"})


def downgrade_rows(idx, order, merged=None, validated=None):
    src = require_merged("T-649", merged)
    val = set(validated if validated is not None else re.findall(r"DGP-T649-[0-9a-f]{16}", src["verdict"]))
    rows, chained = [], {}
    for pid, (lid, code, unit, lo, hi) in sorted(DGV.items()):
        if pid not in val:
            raise ManifestError(f"{pid}: a downgrade the Checker did not validate is never applied")
        line = M17._live(idx, lid, code, unit)
        if line["class"] != "RELEASED" or D(line["measured_net"]) != D(lo) or D(hi) <= D(lo):
            raise ManifestError(f"{pid}: {lid} is not RELEASED {lo} (R-T652-1 (d): the released value is the low end)")
        pkg = M18.writer_of(order, lid)
        r = row(pkg or P_DGV, pid, "SET", lid, OV.state(line), M9.held(float(D(lo)), float(D(hi))), "HELD",
                src["verdict"], beside={"cause": "F-T645-1: MS1-L counts 9 goings on the architectural GF plan edges "
                                        "RFI-A04 / C-ST-4 disputes (ST p.4: 11 goings); downgrade-only, CHECKER-VALIDATED",
                                        "downgrade_id": pid, "rule": "R-T652-1 (d)"})
        if pkg:
            chained.setdefault(pkg, []).append(r)
        else:
            rows.append(r)
    return rows, chained


# ---- statement op (F-C-T635-1) -------------------------------------------------------------------------------------

def statement_ops(t635, merged=None):
    require_merged("T-635", merged)
    out = []
    for si, sec in enumerate(t635["sections_v12"]):
        for ri, r in enumerate(sec.get("rows", ())):
            if r.get("source", "").startswith("T-545") and r.get("name") in ("GF: COUNT", "1F: COUNT"):
                if r["evidence_status"] != "CHECKER_VERIFIED" or "PARTIALLY VERIFIED" not in r["evidence_verdict"]:
                    raise ManifestError(f"F-C-T635-1: row {r['name']} is not the overstated stamp")
                out.append({"op": "STATEMENT_EVIDENCE_MOVE", "source": "F-C-T635-1 (Verifier, T-635)",
                            "where": f"sections_v12[{si}].rows[{ri}]", "row": r["name"], "delta_m3": r["delta"],
                            "from": "CHECKER_VERIFIED", "to": "PARTIALLY VERIFIED", "lines": 0,
                            "why": "the T-545 verdict re-measured only B27 (4.1927 m3) and said PARTIALLY VERIFIED: a "
                                   "row-level stamp needs every component re-measured; no engine line moves"})
    if len(out) != 2:
        raise ManifestError(f"F-C-T635-1: {len(out)} rows found (expected 2)")
    return out


# ---- rulings: origin labels moved by the base move; downgraded stair pieces -----------------------------------------

def _key(c):
    return (c["family"], c["host"], c["unit"])


def rulings_v19(conflicts, conflicts18, stage, after18, dg_lines):
    """R-T652-1 (a): a group that was ONE source in V18 and now mixes CANDIDATE (the merged stage lines only) with the
    package that chained after them is one writer then and now (explained); a downgraded stair line beside a known pair
    of distinct pieces (M18.FACE_PAIRS) is explained by that pair. Anything else stays UNEXPLAINED (refused by build)."""
    was = {_key(c): c for c in conflicts18}
    out = []
    for c in conflicts:
        if c["status"] != "UNEXPLAINED":
            continue
        k = _key(c)
        then = {P498 if x == "CANDIDATE" else x for x in c["sources"]}
        prev = was.get(k)
        same_then = prev is None and then == {P498} or \
            prev is not None and prev["status"] == "EXPLAINED" and set(prev["sources"]) == then
        cand = [l for l in c["lines"] if l.startswith("L-") and l in stage]
        base_only = [l for l in c["lines"] if l.startswith("L-") and l not in stage and l in after18 and
                     not any(l == x for x in ())]
        if "CANDIDATE" in c["sources"] and same_then and cand and all(
                x == "CANDIDATE" or x.startswith(P498) for x in c["sources"]) and \
                all(l in stage or not l.startswith("L-") or l in after18 for l in c["lines"]):
            out.append({"layer": c["family"], "host_re": "^" + re.escape(c["host"]) + "$", "sources": c["sources"],
                        "ruling": f"R-T652-1 (a): {len(cand)} merged V3.0.59 stage line(s) and the rows T-498 chains "
                                  "after them on this host: "
                                  + ("one source in V18" if prev is None else f"explained in V18 ({prev['ruling']})")
                                  + "; the stage is now the candidate's own; no line counted twice",
                        "fix_row": "R-T652-1 (a)"})
            continue
        dl = [l for l in c["lines"] if l in dg_lines]
        if dl and len(c["lines"]) == 2:
            codes = frozenset(after18[l]["item_code"] for l in c["lines"])
            pair = M18.FACE_PAIRS.get(codes)
            if pair:
                out.append({"layer": c["family"], "host_re": "^" + re.escape(c["host"]) + "$", "sources": c["sources"],
                            "ruling": f"{dl[0]} downgraded beside {[l for l in c['lines'] if l != dl[0]][0]}: {pair}",
                            "fix_row": "R-T652-1 (d)"})
    return out


# ---- overlay --------------------------------------------------------------------------------------------------------

def overlay_v19():
    """(base59, order19, rul18, after19, rep19, after18, rows, outs, src)."""
    pins()
    src = {k: _json(IN[k]) for k in ("T498", "T647", "T648", "T650", "T635")}
    idx, order18, rul18, after18, rep18, after17, rep17, rows18, outs18, src18, t584 = M18.overlay_v18()
    stage = stage_lines(src["T498"])
    base = base_v3059(idx, stage)
    order_r, removed = rebase(order18, stage)
    after_r, rep_r = OV.apply(base, order_r, rul18)
    if set(after_r) != set(after18) or any(after_r[k] != after18[k] for k in after18):
        raise ManifestError("the V18 overlay on the V3.0.59 base is not byte-equal to V18 (R-T652-1 (a))")
    hosts, hosts_tot = hosts_015(src["T498"], base, after18)
    repl, replaced = remeasure_rows(src["T650"], order_r, after18)
    cn = cn_rows(src["T647"], after18, order_r)
    gaps, gaps_tot = count_gaps(src["T647"], after18)
    thr = threshold_row(src["T648"], after18, order_r)
    dg, dg_chained = downgrade_rows(after18, order_r)
    new_rows = list(repl.values()) + cn + [thr] + dg + [r for v in dg_chained.values() for r in v]
    M9.validate_rows(new_rows)
    order19 = replace_ops(order_r, repl)
    for pkg, rs in dg_chained.items():
        order19 = M15.chain_into(order19, pkg, rs)
    order19 = order19 + [(P_CN, cn), (P_THR, [thr])] + ([(P_DGV, dg)] if dg else [])
    _, rep0 = OV.apply(base, order19, rul18)
    rul19 = list(rul18) + rulings_v19(rep0["conflicts"], rep18["conflicts"], stage, after18,
                                      {r["line_id"] for v in dg_chained.values() for r in v} | {r["line_id"] for r in dg})
    after19, rep19 = OV.apply(base, order19, rul19)
    rows = {"remeasure": list(repl.values()), "cn": cn, "threshold": [thr], "downgrades": dg + [r for v in
                                                                                             dg_chained.values() for r in v]}
    outs = {"stage": stage, "removed": removed, "hosts": hosts, "hosts_tot": hosts_tot, "replaced": replaced,
            "gaps": gaps, "gaps_tot": gaps_tot, "rep_rebased": rep_r}
    outs["rulings_v19"] = rul19[len(rul18):]
    return base, order19, rul19, after19, rep19, after18, rep18, rows, outs, src


def build():
    base, order19, rul, after19, rep, after18, rep18, rows, outs, src = overlay_v19()
    allrows = [r for v in rows.values() for r in v]
    qrows = [r for r in allrows if r["kind"] in ("ADD", "SET", "RECODE")]
    v19_lines = {r["line_id"] for r in qrows}
    others = sorted(k for k in set(after18) | set(after19) if k not in v19_lines and after18.get(k) != after19.get(k))
    if others:
        raise ManifestError(f"lines V19 does not write changed: {others[:5]}")
    t18, t19 = OV.totals(after18), OV.totals(after19)
    dt = OV.diff_totals(t18, t19)
    writes = sorted({f"{after18[r['line_id']]['item_code']}|{after18[r['line_id']].get('unit')}" for r in qrows})
    if sorted(dt) != writes:
        raise ManifestError(f"totals moved on {sorted(dt)}, V19 writes {writes}")
    if any(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]):
        raise ManifestError("unexplained conflicts after V19")
    v19_ops = {r["op_id"] for r in allrows}
    flagged = [r for r in rep["rows"] if r["status"] != "APPLIED"]
    if any(r["op_id"] in v19_ops for r in flagged):
        raise ManifestError(f"a V19 row is not APPLIED: {[r for r in flagged if r['op_id'] in v19_ops]}")
    if len(flagged) != len([r for r in rep18["rows"] if r["status"] != "APPLIED"]):
        raise ManifestError("the flagged rows of V18 changed")
    # hand acceptance per key
    lk = "STR.CONC.LINTEL|m3"
    if q6(D(t19[lk]["held_low"]) - D(t18[lk]["held_low"])) != Decimal("0.036") or \
            q6(D(t19[lk]["held_high"]) - D(t18[lk]["held_high"])) != Decimal("0.04377") or \
            t18[lk]["held_blank_n"] - t19[lk]["held_blank_n"] != 1:
        raise ManifestError("the lintel bound did not move by the D-1F-07 re-measure only")
    ck = "STR.CONC.COLUMN|m3"
    if t19[ck]["excluded_n"] - t18[ck]["excluded_n"] != 5 or t18[ck]["held_n"] - t19[ck]["held_n"] != 5:
        raise ManifestError("the 5 CN lines did not leave HELD for EXCLUDED")
    stage, rr = outs["stage"], outs["rep_rebased"]
    by_code = {}
    for l in stage.values():
        by_code[l["item_code"]] = by_code.get(l["item_code"], 0) + 1
    status = {}
    for r in rep["rows"]:
        status.setdefault(r["package"], {}).setdefault(r["status"], 0)
        status[r["package"]][r["status"]] += 1
    table = []
    for r in allrows:
        b, a = r.get("before"), r.get("after")
        table.append({"row": r["row"], "package": r["package"], "kind": r["kind"], "line_id": r["line_id"],
                      "item": after18[r["line_id"]]["item_code"],
                      "before": None if b is None else {k: b[k] for k in OV.QFIELDS},
                      "after": None if a is None else {k: a[k] for k in OV.QFIELDS},
                      "evidence": r["evidence"]["status"]})
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-652", "candidate": CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in IN.values()},
        "sources_merged": {k: v["merge"] for k, v in MERGED.items()},
        "base_move": {"from": "V3.0.58 copy (4,999 lines)", "to": CANDIDATE, "stage_lines": len(stage),
                      "stage_by_code": dict(sorted(by_code.items())), "overlay_adds_removed": len(outs["removed"]),
                      "rule": "R-T652-1 (a): each removed ADD equal to its merged line; the V18 overlay re-applied on "
                              "the V3.0.59 base is byte-equal to V18 on every line",
                      "lines_after_rebased_v18": len(after18), "rebased_flagged_rows":
                          sum(1 for r in rr["rows"] if r["status"] != "APPLIED")},
        "f_c_t498_1": {"hosts": outs["hosts"], "totals": outs["hosts_tot"],
                       "rule": "R-T498-1 (1) as merged (T-615 Checker AGREE): material base = contract net - REQUIRED RC "
                               "lintel faces (concrete, Q-73: never laid block); a HELD face is a 0 .. face companion; "
                               "units = base x 12.5 / m2 (UPC-BLACK-BLOCK-001 1.1.0, Q-80 A), unrounded (theoretical; "
                               "whole units only at procurement = ceil(theoretical x (1 + sourced waste)), waste HELD); "
                               "panel mortar = base x 0.0110625 m3 / m2",
                       "lead_expectation": "2,232.14 pcs = contract 178.571 m2 x 12.5 with no lintel face taken out"},
        "remeasure": outs["replaced"],
        "count_convention_gaps": {"lines": outs["gaps"], **outs["gaps_tot"],
                                  "rule": "HELD on the census bound (the index carries it at 3 dp); a bound, never "
                                          "summed into a released total, never 0"},
        "statement_only_ops": statement_ops(src["T635"]),
        "line_table": table,
        "rows": [dict(r) for r in allrows],
        "totals": {k: {"v18": t18.get(k), "v19": t19.get(k)} for k in dt},
        "overlay": {
            "lines": {"base_v3_0_59": len(base), "after_v18": len(after18), "after_v19": len(after19)},
            "order": [{"package": n, "ops": len(o), "status": status.get(n, {})} for n, o in order19],
            "flagged_rows": flagged,
            "stale": sum(r["status"] == "STALE" for r in rep["rows"]),
            "unexplained_conflicts": sum(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]),
            "other_lines_changed_vs_v18_overlay": others,
            "v19_vs_v18_totals": dt,
        },
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n"


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    return b
