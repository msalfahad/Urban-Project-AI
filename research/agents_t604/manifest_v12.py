"""T-604 WIRING MANIFEST V12 + OVERLAY DRY RUN (R-T604-1; lane I, non-candidate, research only).

V12 carries the Checker-merged fix rows of T-601 (doorless opening jambs: FR-T601-1 the 1F arch jamb skirting, FR-T601-2
the GF OP-020 jamb line NOT_APPLICABLE, FR-T601-3 the lift landing door label) and of T-602 (FR-T602-1 the G-01 street
gate step, Lead amendment 2026-11-07 16:17) onto the candidate of record ARCH_TAKEOFF_V3.0.58, and overlays them on a
COPY of its line index AFTER V2 .. V11 (the T-596 order; R-T580-1 / R-T588-1 / R-T593-1 / R-T596-1 code reused read
only). Nothing is wired; no candidate, released (V2.9 + route G), rule, knowledge or registry file is written. No drawing
is read: every figure comes from a committed, Checker-merged output. T-599 r2 was NOT merged at claim: the column /
beam joint rows keep their UNRESOLVED class with the T-599 pointer and no rule citation (a T-599 row is refused).

R-T604-1 (every villa on the engine's line-index scheme):
  (a) MERGED ONLY: a fix row enters only from a task MERGED with a Checker verdict (R-T596-1 (a) code); a row or a rule
      citation from an unmerged task is refused, and its lines keep their earlier class and pointer.
  (b) DOORLESS JAMB = ITS OWN LINE: a valued jamb fix (census status FIX_ROW: no leaf / frame, both sides DRY, real
      jamb ends) is ONE new skirting line per opening, lm = real jamb ends x wall depth, bound to the opening's own
      room line; the room skirting lines that deduct the opening stay byte-equal (they value no jamb: no double count),
      and no live jamb line may already exist on that opening.
  (c) NOT_APPLICABLE BY RULE: a HELD jamb line whose opening the census rules NOT_APPLICABLE (a wet side, Q-06 A) leaves
      the HELD sum as EXCLUDED with the rule named; never 0, never a value. Any other census status is refused.
  (d) LABEL FIX: TEXT_ONLY on the lines that carry the wrong kind; the line's state never moves.
  (e) GATE STEP WITH NO THRESHOLD LINE: printed BESIDE the gate family's own line of that opening (no new quantity
      line, the line's own state never moves); one payable length, riser m2 = payable x riser height; the opening and
      its drawn edge may not already be claimed by a V10 door-step row; the door-step family ledger (house + gates) is
      the merged source's own total, and his residual stays UNRESOLVED by aggregate (no opening id on his rows, no %).
  (f) SUPERSEDE BY ID: each V12 row names the earlier state, row or open name it replaces.
Rebuild: `python3 -I research/agents_t604/manifest_v12.py` (`--check`).
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
T596_DIR = ROOT / "research/agents_t596"
for _p in (ROOT / "research/agents_t580", ROOT / "research/agents_t588", ROOT / "research/agents_t593", T596_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import manifest_v11 as M11                                            # noqa: E402  (R-T596-1, read only)

M10 = M11.M10
M9 = M11.M9
OV = M11.OV

SCHEMA = "URBAN_T604_WIRING_MANIFEST_V12"
RULE = "R-T604-1"
OUT_JSON = HERE / "out/WIRING_MANIFEST_V12.json"
IN = {
    "T601": ROOT / "research/agents_t601/out/T601_DOORLESS_CENSUS.json",
    "T602": ROOT / "research/agents_t602/out/T602_DOOR_STEPS.json",
    "V10": ROOT / "research/agents_t593/out/WIRING_MANIFEST_V10.json",
    "V11": T596_DIR / "out/WIRING_MANIFEST_V11.json",
    "V11_CODE": T596_DIR / "manifest_v11.py",
}
PINS = {
    "T601": "1ee289bcb13429076dac56eff7ed5210b17445f783bfff89a2dc99825a05005c",
    "T602": "c7cb2f106e7b2039482582c7b95688fd003368928b38b04d325b79f1cc92db40",
    "V10": "c05827ef4c27e365e05f565ed89c46493c95ccaf826a490342a96f83e1dcd3fe",
    "V11": "d909fa02db13e3fdeffec3fe14c805376b89e0457bad2d7da82091bba1657eb3",
}

# R-T604-1 (a): the board's MERGED verdicts (Verifier text, abridged; full text on BOARD.md)
MERGED = {
    "T-601": {"merge": "2a7ad738",
              "verdict": "BOARD T-601 VERIFIER 2026-11-07T13:58Z (e)/(f): own read P7757.dxf: A-1F-01 gap 1000 mm, two "
                         "layer-1 jamb returns 0.150 deep, no leaf: 2 x 0.15 = 0.30 lm AGREE (FREELANCER_RIGHT, "
                         "DRAWING-CONFIRMED jamb; dry sides / floor continuity on T-175 / T-296 records: PARTIALLY "
                         "VERIFIED); GF OP-011 / 1F OP-007 framed lift landing doors, deduction stands, label PASSAGE "
                         "wrong (FR-T601-3); A-GF-01 / P-GF-01 NA (Q-06 A wet side, rule application checked); "
                         "FR-T601-1 209.428592 -> 209.728592 lm applies only when wired (T-604)"},
    "T-602": {"merge": "6d211198",
              "verdict": "BOARD T-602 VERIFIER 2026-11-07T15:02Z (e)/(f): independent re-measure of G-01: boundary gap "
                         "2.500 m clear, plot edge layer 5 through the gap, layer-2 companion 0.050 over the gap, court "
                         "+0.15 / street +-0.00: step 2.500 lm, riser 0.15 -> 0.375 m2 AGREE; G-01 DRAWING-CONFIRMED "
                         "geometry, stone / finish HELD, 0.40 lm UNRESOLVED (no id on his rows); ENGINE_OMISSION "
                         "(FR-T602-1), count FREELANCER_RIGHT"},
}
# the joint-ownership rule task: NOT MERGED at claim (board 2026-11-07T17:03Z: T-599 TODO r2, REJECTED dd3baaa4)
JOINT = {"task": "T-599", "state_at_claim": "TODO r2 (Verifier 2026-11-07T13:58Z REJECTED head dd3baaa4, gates F + H)",
         "pointer": "T-599 (UP-CONC-JOINT-001 1.0.0 pending) / T-600 (per-storey residual)"}

P_JAMB = "DOORLESS_JAMBS (T-601 FR-T601-1 / FR-T601-2 / FR-T601-3)"
P_GATE = "GATE_STEP_G01 (T-602 FR-T602-1)"
V10_DOOR = "DOOR_STEPS (T-592 FR-T592-1 / FR-T592-2)"
REAL_JAMB_ENDS = ("MASONRY_JAMB", "COLUMN_JAMB")
SKIRT = ("FIN.SKIRTING", "lm")
GATE_LEAF = ("EXT.FENCE.GATE", "pcs")
NA_RULES = "Q-06 A / UP-THR-001 1.0.0 (wet side: marble threshold, full-height tile; owner method condition 4)"


class ManifestError(Exception):
    pass


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


D, S = M11.D, M11.S


def pins():
    for k, pin in PINS.items():
        if sha256(IN[k]) != pin:
            raise ManifestError(f"PIN: {IN[k].name} sha256 {sha256(IN[k])[:8]} is not the pinned {pin[:8]}")


def require_merged(task, merged=None):
    try:
        return M11.require_merged(task, MERGED if merged is None else merged)
    except M11.ManifestError as e:
        raise ManifestError(str(e)) from None


def _fix(t601, fid):
    hits = [f for f in t601["fix_rows"] if f["id"] == fid]
    if len(hits) != 1:
        raise ManifestError(f"{fid}: {len(hits)} fix rows in the source")
    return hits[0]


def _engine_op(opening_text):
    m = re.search(r"engine (GF|1F|2F) (OP-\d+)", opening_text)
    if not m:
        raise ManifestError(f"{opening_text!r}: no engine opening id")
    return m.group(1), m.group(2)


def _live(idx, code, unit, contains):
    return sorted(k for k, l in idx.items() if l["class"] != "EXCLUDED" and l["item_code"] == code
                  and l.get("unit") == unit and contains in l["element_id"])


# ---- R-T604-1 (b): doorless jamb line -------------------------------------------------------------------------------

def jamb_add(c, idx, fid="FR-T601-1", source="T-601", merged=None):
    """census row c (status FIX_ROW) -> one ADD row: its own jamb line, bound to the opening's room line."""
    src = require_merged(source, merged)
    if c["status"] != "FIX_ROW" or c["kind"] != "DOORLESS":
        raise ManifestError(f"{c['opening']}: status {c['status']} / {c['kind']} is not a doorless FIX_ROW")
    if c["sides"] != ["DRY", "DRY"]:
        raise ManifestError(f"{c['opening']}: sides {c['sides']}: jamb skirting needs both sides DRY")
    real = sum(e in REAL_JAMB_ENDS for e in c["ends"])
    wall = D(c["wall_t_m"])
    if real == 0 or wall is None or wall <= 0:
        raise ManifestError(f"{c['opening']}: no real jamb or no wall depth (HELD, never 0)")
    lm = (real * wall).quantize(Decimal("0.000001"))
    if D(c["jamb_lm"]) != lm or D(c["fix_lm"]) != lm:
        raise ManifestError(f"{c['opening']}: jamb {c['jamb_lm']} / fix {c['fix_lm']} != {real} x {wall}")
    storey, op = _engine_op(c["opening"])
    room_lines = re.findall(r"L-[0-9a-f]{20}", c["engine_line"] or "")
    if not room_lines:
        raise ManifestError(f"{c['opening']}: no room line named")
    rooms = set()
    for lid in room_lines:
        l = idx.get(lid)
        if l is None or (l["item_code"], l["unit"]) != SKIRT or l["class"] != "RELEASED":
            raise ManifestError(f"{lid}: not a released FIN.SKIRTING lm line")
        rooms.add(l["element_id"].split(":")[-1] if l["element_id"].startswith("SKIRT-") else
                  l["element_id"].split(":")[0])
    host = [r for r in sorted(rooms) if _live(idx, "ARCH.PASSAGE", "pcs", f"{r}:{op}")]
    if len(host) != 1:
        raise ManifestError(f"{c['opening']}: the opening {storey} {op} binds {len(host)} of the named room lines")
    elem = f"SKIRT-T601:{host[0]}:{op}-JAMBS"
    st = host[0].split("-")[0]                      # the room's own storey prefix
    same = [k for k in _live(idx, *SKIRT, f"{op}-JAMBS")
            if idx[k]["element_id"].startswith(f"{st}-") or f":{st}-" in idx[k]["element_id"]]
    if same:
        raise ManifestError(f"{storey} {op}: a live jamb line already exists ({same[0]})")
    lid = f"NEW:FIN.SKIRTING:{elem}"
    r = M9.row(P_JAMB, fid, "ADD", lid, None, M9.released(float(lm)), "PARTIALLY VERIFIED", src["verdict"],
               "FIN.SKIRTING", "lm", elem,
               beside={"opening": c["opening"], "jamb_ends": real, "wall_depth_m": S(wall), "jamb_lm": S(lm),
                       "jamb_faces_dxf": c["jamb_face_handles"], "sides": c["side_names"],
                       "room_lines_unchanged": room_lines, "his_lm": c["his_lm"],
                       "who_is_right": "FREELANCER_RIGHT (ENGINE_WRONG on our side: deducted, no jamb valued)",
                       "evidence_scope": "jamb geometry DRAWING-CONFIRMED (Checker own read); dry sides / floor "
                                         "continuity on the T-175 / T-296 records: PARTIALLY VERIFIED"},
               note="R-T604-1 (b): the room lines deduct the opening and value no jamb; the jamb is its own line")
    r["supersedes"] = ["T-574 row 29 UNRESOLVED -0.30 lm ('bed room 2' group)", "F-T591-1 open jamb name A-1F-01"]
    return r, room_lines


# ---- R-T604-1 (c): HELD jamb line NOT_APPLICABLE -----------------------------------------------------------------

def jamb_na(c, idx, element, fid="FR-T601-2", source="T-601", merged=None):
    src = require_merged(source, merged)
    if c["status"] != "NOT_APPLICABLE":
        raise ManifestError(f"{c['opening']}: census status {c['status']}: only NOT_APPLICABLE leaves the HELD sum")
    if "WET" not in c["sides"]:
        raise ManifestError(f"{c['opening']}: NOT_APPLICABLE without a wet side ({c['sides']})")
    if element not in (c["engine_line"] or ""):
        raise ManifestError(f"{element}: not the census row's engine line")
    hits = _live(idx, *SKIRT, element)
    if len(hits) != 1:
        raise ManifestError(f"{element}: {len(hits)} live lines")
    lid = hits[0]
    before = OV.state(idx[lid])
    if before["class"] != "HELD":
        raise ManifestError(f"{lid}: {before['class']}, not HELD")
    r = M9.row(P_JAMB, fid, "SET", lid, before, M9.excluded(), "PARTIALLY VERIFIED", src["verdict"],
               beside={"opening": c["opening"], "sides": c["side_names"], "rule": NA_RULES,
                       "rfi_b": "kept for the reveal's wall finish (B4 / B5), not for skirting"},
               note="R-T604-1 (c): NOT_APPLICABLE_WITH_EVIDENCE: the wet side takes no skirting; the line leaves the "
                    "HELD sum by rule, never 0")
    r["supersedes"] = ["candidate HELD-blank jamb line (T-443, RFI b) on GF OP-020"]
    return r


# ---- R-T604-1 (d): label fix -------------------------------------------------------------------------------------

def label_rows(census, idx, fid="FR-T601-3", source="T-601", merged=None):
    src = require_merged(source, merged)
    rows = []
    for c in census:
        if c["kind"] != "FRAMED" or "kind PASSAGE on" not in c["opening"]:
            continue
        if c["status"] != "NO_JAMB_SKIRTING" or D(c["jamb_lm"]) != 0:
            raise ManifestError(f"{c['opening']}: a framed landing door takes no jamb")
        lid = re.search(r"kind PASSAGE on (L-[0-9a-f]{20})", c["opening"]).group(1)
        if lid not in idx or (idx[lid]["item_code"], idx[lid]["unit"]) != SKIRT:
            raise ManifestError(f"{lid}: not a skirting line in the index")
        storey, op = _engine_op(c["opening"])
        before = OV.state(idx[lid])
        r = M9.row(P_JAMB, fid, "TEXT_ONLY", lid, before, None, "DRAWING-CONFIRMED", src["verdict"],
                   beside={"opening": f"{storey} {op}", "label_before": "PASSAGE (T-296 deduction kind)",
                           "label_after": "LIFT LANDING DOOR (LIFT DOOR GAP register; T-175 "
                                          f"{c['opening'].split(' ')[0]})",
                           "panel_lines_dxf": c["evidence_ids"].get("panel_lines")},
                   note="R-T604-1 (d): label only; the 1.00 deduction stands; no jamb skirting")
        r["supersedes"] = [f"F-T591-1 HELD-by-name doorless reading of {storey} {op}"]
        rows.append(r)
    if not rows:
        raise ManifestError("no framed landing door carries a PASSAGE label")
    return rows


def pkg_jambs(t601, idx, merged=None):
    census = t601["census"]
    fix = [c for c in census if c["status"] == "FIX_ROW"]
    if len(fix) != 1 or _fix(t601, "FR-T601-1")["effect_lm"] != fix[0]["fix_lm"]:
        raise ManifestError("FR-T601-1 is not the one FIX_ROW of the census")
    add, room_lines = jamb_add(fix[0], idx, merged=merged)
    f2 = _fix(t601, "FR-T601-2")
    elem = re.match(r"(\S+)", f2["line"]).group(1)
    na = [c for c in census if elem in (c["engine_line"] or "")]
    if len(na) != 1:
        raise ManifestError(f"FR-T601-2: {len(na)} census rows on {elem}")
    rows = [add, jamb_na(na[0], idx, elem, merged=merged)] + label_rows(census, idx, merged=merged)
    if D(t601["valued_fix_lm"]) != D(add["after"]["measured_net"]):
        raise ManifestError("valued fix lm differs from the source")
    return (P_JAMB, rows), room_lines


# ---- R-T604-1 (e): gate step beside the gate family's line -------------------------------------------------------

def v10_door_rows(order):
    rows = next((ops for n, ops in order if n == V10_DOOR), None)
    if rows is None:
        raise ManifestError("no V10 door-step package in the order")
    return rows


def gate_step(t602, idx, door_rows, opening="G-01", fid="FR-T602-1", source="T-602", merged=None):
    src = require_merged(source, merged)
    hits = [o for o in t602["openings"] if o["opening"] == opening]
    if len(hits) != 1 or hits[0]["decision"] != "STEP":
        raise ManifestError(f"{opening}: not one STEP opening in the source")
    o = hits[0]
    if any(r["beside"]["opening"] == opening for r in door_rows):
        raise ManifestError(f"{opening}: already a V10 door-step row (double count)")
    pay, rm = D(o["payable_lm"]), D(o["riser_m"])
    if pay is None or pay <= 0:
        raise ManifestError(f"{opening}: no payable length (HELD, never 0)")
    if rm is None or rm <= 0:
        raise ManifestError(f"{opening}: riser {rm}: equal levels make no step; a missing riser is HELD by name")
    if (pay * rm).quantize(Decimal("0.001")) != D(o["riser_m2"]):
        raise ManifestError(f"{opening}: riser m2 {o['riser_m2']} != {pay} x {rm}")
    leaf = _live(idx, *GATE_LEAF, f"FENCE:{opening}:LEAF")
    if len(leaf) != 1:
        raise ManifestError(f"{opening}: {len(leaf)} gate leaf lines (the step needs one gate-family line)")
    if _live(idx, "ARCH.THRESHOLD", "m2", opening) or _live(idx, "FIN.MARBLE.THRESHOLD", "m2", opening):
        raise ManifestError(f"{opening}: a threshold line exists: R-T593-1 (a) binds the step to it instead")
    lid = leaf[0]
    edge = o["edge_pair"]["edge"]
    r = M10.row(P_GATE, fid, "BESIDE", lid, OV.state(idx[lid]), None, "DRAWING-CONFIRMED", src["verdict"],
                beside={"opening": opening, "step_lm_payable": S(pay), "nr": int(o["nr"]), "riser_m": S(rm),
                        "riser_m2": S(D(o["riser_m2"])), "edge": edge, "companion": o["edge_pair"]["companion"],
                        "levels": {"in": o["levels_in"], "out": o["levels_out"]},
                        "material": "stone / finish HELD by name (not printed)",
                        "owner_trade": "marble / stone, door-step family (ELEMENT_REGISTER 'GATE STEP')",
                        "gate_leaf": "stays HELD (T-361); does not change the step"},
                scope="the step's beside figures (DRAWING-CONFIRMED geometry); the gate leaf line's own HELD state "
                      "is unchanged and not re-verified",
                note="R-T604-1 (e): no threshold line exists at a boundary opening; the step sits beside the gate "
                     "family's own line of G-01; never folded into the house door-step total")
    r["supersedes"] = ["V10 door-step his-residual UNRESOLVED (SCOPE) -2.900 lm: 2.500 of it is this ENGINE_OMISSION"]
    return r, f"{opening}:{edge}"


def step_family(t602, door_rows, gate_row):
    """the door-step family ledger after V12 = the V10 rows + the gate step; every V10 figure equals the T-602 one."""
    by = {o["opening"]: o for o in t602["openings"] if o["decision"] == "STEP"}
    lm = m2 = Decimal(0)
    nr, per = 0, []
    for r in door_rows + [gate_row]:
        b = r["beside"]
        o = by.pop(b["opening"], None)
        if o is None:
            raise ManifestError(f"{b['opening']}: no T-602 STEP opening")
        if D(b["step_lm_payable"]) != D(o["payable_lm"]) or D(b["riser_m2"]) != D(o["riser_m2"]):
            raise ManifestError(f"{b['opening']}: manifest {b['step_lm_payable']} / {b['riser_m2']} != T-602 "
                                f"{o['payable_lm']} / {o['riser_m2']}")
        lm += D(b["step_lm_payable"])
        m2 += D(b["riser_m2"])
        nr += int(b["nr"])
        per.append({"opening": b["opening"], "lm": S(D(b["step_lm_payable"])), "riser_m2": S(D(b["riser_m2"])),
                    "line": r["line_id"], "package": r["package"]})
    if by:
        raise ManifestError(f"T-602 steps with no manifest row: {sorted(by)}")
    return {"lm": S(lm), "riser_m2": format(m2.quantize(Decimal("0.001")), "f"), "nr": nr, "by_opening": per}


# ---- overlay ----------------------------------------------------------------------------------------------------

def v11_state():
    """the T-596 build up to its overlay (read only), so V12 steps from the exact V11 state."""
    idx, order10, rul10, after10, rep10, t584 = M11.v10_state()
    t595 = M11._json(M11.IN["T595"])
    v9_ops = next(ops for n, ops in order10 if n == M11.V9_REBAR)
    rebar_pkg, _ = M11.pkg_rebar_v2(t595, v9_ops)
    foot_pkg, _ = M11.pkg_footing(t595, after10)
    order11, _ = M11.supersede(order10, M11.V9_REBAR, rebar_pkg)
    order11 = order11 + [foot_pkg]
    after11, rep11 = OV.apply(idx, order11, rul10)
    return idx, order11, rul10, after11, rep11, t584


def joint_section():
    try:
        require_merged(JOINT["task"])
        raise ManifestError("T-599 is listed as merged: the joint citation must be built, not skipped")
    except ManifestError as e:
        if "listed as merged" in str(e):
            raise
        refusal = str(e)
    return {"rule_task": JOINT["task"], "state_at_claim": JOINT["state_at_claim"], "manifest_rows": 0,
            "refusal": refusal,
            "joint_rows": "the column / beam joint rows keep their class (UNRESOLVED in statement V9, T-603) with the "
                          f"pointer {JOINT['pointer']}; no rule citation from an unmerged task; no quantity change",
            "lines_in_v11": "no manifest V2 .. V11 row writes a joint line: nothing to carry"}


def build():
    pins()
    t601, t602, v10j, v11j = _json(IN["T601"]), _json(IN["T602"]), _json(IN["V10"]), _json(IN["V11"])
    idx, order11, rul, after11, rep11, t584 = v11_state()
    if len(after11) != v11j["overlay"]["lines"]["after_v11"]:
        raise ManifestError("V11 state rebuild differs from the committed V11 line count")
    for r in v11j["rows"]:
        if not OV.same_state(OV.state(after11[r["line_id"]]), r["after"]):
            raise ManifestError(f"{r['line_id']}: V11 rebuild differs from the committed V11 row")
    jamb_pkg, room_lines = pkg_jambs(t601, after11)
    door_rows = v10_door_rows(order11)
    gate_row, gate_claim = gate_step(t602, after11, door_rows)
    gate_pkg = (P_GATE, [gate_row])
    v12 = [jamb_pkg, gate_pkg]
    for _, rows in v12:
        M9.validate_rows(rows)
    order12 = order11 + v12
    after12, rep = OV.apply(idx, order12, rul)
    v12_lines = {r["line_id"] for _, rows in v12 for r in rows}
    others = sorted(k for k in set(after11) | set(after12) if k not in v12_lines and after11.get(k) != after12.get(k))
    if others:
        raise ManifestError(f"lines V12 does not write changed: {others[:5]}")
    for lid in room_lines:
        if after12[lid] != after11[lid]:
            raise ManifestError(f"{lid}: room line moved")
    t11, t12 = OV.totals(after11), OV.totals(after12)
    dt = OV.diff_totals(t11, t12)
    if sorted(dt) != ["FIN.SKIRTING|lm"]:
        raise ManifestError(f"totals moved on {sorted(dt)}: V12 moves FIN.SKIRTING only")
    sk11, sk12 = t11["FIN.SKIRTING|lm"], t12["FIN.SKIRTING|lm"]
    if D(sk11["released"]) != D(t601["candidate_fin_skirting_released_lm"]) or \
            D(sk12["released"]) != D(t601["after_fix_rows_lm"]):
        raise ManifestError(f"FIN.SKIRTING released {sk11['released']} -> {sk12['released']} is not the T-601 "
                            f"{t601['candidate_fin_skirting_released_lm']} -> {t601['after_fix_rows_lm']}")
    if D(sk12["held_low"]) != D(sk11["held_low"]) or D(sk12["held_high"]) != D(sk11["held_high"]):
        raise ManifestError("FIN.SKIRTING held bounds moved")
    # door-step edge census: the V10 claims plus the gate's edge, each drawn edge owned once
    claims = [(k, v["claimant"], v["row"]) for k, v in v10j["door_steps"]["edge_census"]["owners"].items()]
    edge = gate_claim.split(":", 1)[1]
    if any(re.search(rf"\b{re.escape(edge)}\b", k) for k, _, _ in claims):
        raise ManifestError(f"{gate_claim}: the edge is already claimed by a V10 door-step row")
    census = M10.door_edge_census(claims + [(gate_claim, gate_row["line_id"], gate_row["op_id"])])
    if census["excluded_second_readings"]:
        raise ManifestError("a drawn door-step edge is claimed twice")
    fam11 = step_family(t602, door_rows, gate_row)
    fam11_without = {"lm": S(sum((D(r["beside"]["step_lm_payable"]) for r in door_rows), Decimal(0))),
                     "riser_m2": format(sum((D(r["beside"]["riser_m2"]) for r in door_rows), Decimal(0))
                                        .quantize(Decimal("0.001")), "f"),
                     "nr": sum(int(r["beside"]["nr"]) for r in door_rows)}
    rec = t602["reconciliation"]
    if D(fam11["lm"]) != D(rec["ours_lm"]) or D(fam11["riser_m2"]) != D(rec["ours_riser_m2"]) \
            or fam11["nr"] != rec["ours_nr"]:
        raise ManifestError(f"door-step family {fam11['lm']} / {fam11['riser_m2']} / {fam11['nr']} != T-602 "
                            f"{rec['ours_lm']} / {rec['ours_riser_m2']} / {rec['ours_nr']}")
    if D(fam11["lm"]) - D(fam11_without["lm"]) != D(gate_row["beside"]["step_lm_payable"]):
        raise ManifestError("step family moved by more than the gate step")
    his_lm = D(t602["his"]["lm"])
    # the T-412 stair census stays 0 doubles / 0 orphans (V12 writes no step / nosing line)
    t412 = M11.load_t412()
    t598 = M11._json(M11.IN["T598"])
    nrows, _ = M11.nosing_ledger(t412, t598)
    cen = M9.census_on(after12, M11.census_edges(t412, nrows), t584, {M9.E1_LINE: ("ST-03", "E1")})
    if cen["doubles"] or cen["orphans"]:
        raise ManifestError("stair census doubles / orphans after V12")
    status = {}
    for r in rep["rows"]:
        status.setdefault(r["package"], {}).setdefault(r["status"], 0)
        status[r["package"]][r["status"]] += 1
    flagged = [r for r in rep["rows"] if r["status"] != "APPLIED"]
    if any(r["package"] in (P_JAMB, P_GATE) for r in flagged):
        raise ManifestError(f"a V12 row is not APPLIED: {[r for r in flagged if r['package'] in (P_JAMB, P_GATE)]}")
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-604", "candidate": M9.T580.CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in IN.values()},
        "sources_merged": {k: v["merge"] for k, v in MERGED.items()},
        "supersedes": {r["op_id"]: r["supersedes"] for _, rows in v12 for r in rows},
        "joint": joint_section(),
        "skirting": {"FIN.SKIRTING|lm": {"v11": sk11, "v12": sk12},
                     "released_delta_lm": S(D(sk12["released"]) - D(sk11["released"])),
                     "held_lines": f"{sk11['held_n']} -> {sk12['held_n']} (FR-T601-2 OP-020 jamb line HELD-blank -> "
                                   "EXCLUDED by rule; held bounds 0 .. 0 unchanged, no blank became 0)",
                     "room_lines_unchanged": room_lines,
                     "his": "A-1F-01 his 0.30 = ours 0.30 after the fix (AGREE); 'bed room 2' group gap -2.00 -> "
                            "-1.70 lm (T-601 s.3); no %"},
        "door_steps": {"v11_family": fam11_without, "v12_family": fam11,
                       "delta": {"lm": S(D(fam11["lm"]) - D(fam11_without["lm"])),
                                 "riser_m2": S(D(fam11["riser_m2"]) - D(fam11_without["riser_m2"])),
                                 "nr": fam11["nr"] - fam11_without["nr"]},
                       "house_total_unchanged": v10j["door_steps"]["house"],
                       "his": {"lm": S(his_lm), "nr": t602["his"]["nr"], "ours_minus_his_lm": S(D(fam11["lm"]) - his_lm),
                               "v10_residual_lm": v10j["door_steps"]["his"]["ours_minus_his_with_gate_lm"],
                               "split": "-2.900 = -2.500 G-01 ENGINE_OMISSION (closed by FR-T602-1) + -0.400 "
                                        "UNRESOLVED (his rows carry no opening id; no %)",
                               "count": "his 6 = ours 6: FREELANCER_RIGHT on the count"},
                       "edge_census": census},
        "rows": [dict(r, package=n) for n, rs in v12 for r in rs],
        "overlay": {
            "lines": {"base": len(idx), "after_v11": len(after11), "after_v12": len(after12)},
            "order": [{"package": n, "ops": len(o), "status": status.get(n, {})} for n, o in order12],
            "flagged_rows": flagged,
            "stale": sum(r["status"] == "STALE" for r in rep["rows"]),
            "two_package_lines": 0,                    # OV.apply raises R1 otherwise
            "unexplained_conflicts": sum(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]),
            "other_lines_changed_vs_v11_overlay": others,
            "v12_vs_v11_totals": dt,
        },
        "stair_edge_census_after_v12": {"edges": cen["edges"], "doubles": len(cen["doubles"]),
                                        "orphans": len(cen["orphans"])},
        "findings": {
            "F-T604-1": "ARCH.PASSAGE pcs (9 released) counts all three lift landing doors (GF OP-011 L-77a427c8, 1F "
                        "OP-007 L-32d90a7a, 2F OP-002 L-c91732d6) as passages; T-601 settles them as framed landing "
                        "doors. V12 moves no count (label only, Lead amendment); whether the lift landing doors leave "
                        "ARCH.PASSAGE for the lift package is a coding question for the Lead",
            "F-T604-2": "G-01 has no threshold or step line on the candidate: the step sits beside the gate leaf line "
                        "L-124e0c1c (HELD, T-361); T-424 / the door-step family wiring must give it a payable line "
                        "(2.500 lm, riser 0.375 m2) or it stays a beside figure",
            "F-T604-3": "FR-T601-1 is a NEW jamb line (one per opening, as the T-443 OP-020-JAMBS precedent) rather "
                        "than +0.15 on each room line: the two jamb faces are the opening's, and splitting them "
                        "between the bed room and dressing lines would be an unsourced allocation",
        },
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str) + "\n"


def main(argv):
    text = dumps(build())
    if "--check" in argv:
        ok = OUT_JSON.exists() and OUT_JSON.read_text(encoding="utf-8") == text
        print("T-604 manifest V12: committed output", "is the rebuild" if ok else "DIFFERS from the rebuild")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
