"""T-593 WIRING MANIFEST V10 + OVERLAY DRY RUN (R-T593-1; lane I, non-candidate, research only).

V10 carries the merged pieces T-592 (external door steps: one payable length, the D-GF-09 riser, the gate) and T-585
(stair-flight skirting in two forms, bounded held pieces; yard skirting and E1 landing skirting as NO_LINE) onto the
candidate of record ARCH_TAKEOFF_V3.0.58, and overlays them on a COPY of its line index AFTER V2 .. V9 (the T-588
order, R-T588-1 / R-T580-1 code reused read only). Nothing is wired; no candidate, released (V2.9 + route G), rule,
knowledge or registry file is written. No drawing is read: every figure comes from a committed, Checker-merged output.

R-T593-1 (every villa on the engine's line-index scheme):
  (a) DOOR STEP = one element, one payable length (ELEMENT_REGISTER 'EXTERNAL DOOR STEP, PAYABLE LENGTH'): the step is
      printed BESIDE its owning threshold line (no second line, the line's own state never moves); payable lm = the
      line's strip width, and payable lm x wall depth must equal the line's own m2 (value or exact bound) where the line
      carries one; the visible nosing is an attribute <= the payable length; a row stating both lengths as payable is
      refused; a riser with no outside level printed in its region stays HELD by name (never 0).
  (b) GATE STEP: same element class (register 'GATE STEP'), its own row, never summed into the house total; PARTIAL
      while its outer level is not re-read.
  (c) DOOR EDGE CENSUS: every drawn door-step edge is claimed by exactly one row; a second reading claiming the same
      edge is EXCLUDED with the claim it repeats, never a second quantity.
  (d) TWO-FORM PIECES (ORR-007 open): a piece measured in both forms writes each form's line as an exact bound (low =
      high = that form's measure), never released, never added across forms; a held piece is bounded only on the form
      its source bounds; a bound over two lines (winder pair) is printed beside both and moves neither.
  (e) NO_LINE rows (an element ruled NOT_IN_DRAWING) are proved by the absence of any live line on that element, before
      and after the overlay.
  (f) A pending package's TEXT_ONLY op may be ABSORBED by name into a V10 row on the same line only when it writes no
      quantity and its stated before equals the V10 row's before (one Gate B unit per line, R1 kept).
Rebuild: `python3 -I research/agents_t593/manifest_v10.py` (`--check`).
"""

from __future__ import annotations

import copy
import csv
import hashlib
import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
T588_DIR = ROOT / "research/agents_t588"
T580_DIR = ROOT / "research/agents_t580"
for _p in (T580_DIR, T588_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import overlay as OV                                                  # noqa: E402  (R-T580-1, read only)
import manifest_v9 as M9                                              # noqa: E402  (R-T588-1, read only)

SCHEMA = "URBAN_T593_WIRING_MANIFEST_V10"
RULE = "R-T593-1"
OUT_JSON = HERE / "out/WIRING_MANIFEST_V10.json"
IN = {
    "T592": ROOT / "research/agents_t592/out/T592_DOOR_STEPS.json",
    "T585": ROOT / "research/agents_t585/out/T585_SKIRTING_FOLLOWUPS.json",
    "T501": ROOT / "research/agents_t501/LINES_T501.csv",
    "V9": T588_DIR / "out/WIRING_MANIFEST_V9.json",
    "V9_CODE": T588_DIR / "manifest_v9.py",
}
PINS = {
    "T592": "c32be0ed6d17ff05e3a116fafb3c0bb241a90d9cdfaf602877e16977e256f689",
    "T585": "207d4c6a35172786a54caaa1732351cac23947ed3e69228fb815a8538361bb7e",
    "T501": "1551662ca02dbca17add9ebd9201e8de13857d5aed5981cf882108c1996f9bbd",
    "V9": "42463dfe7a94b47166e04cfbf4167ce68dda2bf5b7239a498b81c0f92c95b711",
}
EVIDENCE = M9.EVIDENCE
WALL_DEPTH = Decimal("0.200")          # T-592 'wall_depth_m' at every house door (T-150 wall thickness basis)
THRESHOLD_CODES = ("ARCH.THRESHOLD", "FIN.MARBLE.THRESHOLD")

VERDICT = {
    "T-592:HOUSE": "BOARD T-592 VERIFIER 2026-11-07T07:59Z (e)/(f): own DXF read, wall gaps 1.000 / 0.900 / 1.000 / "
                   "0.900 = 3.800 lm nr 4, edges 3.500 AGREE, D-GF-09 riser 0.15 DRAWING-CONFIRMED (F-C-T584-2 "
                   "closed), riser 3.80 x 0.15 = 0.570 m2 AGREE: VERIFIED as a research quantity; F-C-T584-1 closed",
    "T-592:GATE": "BOARD T-592 VERIFIER 2026-11-07T07:59Z (e): gate B8 / B9 gap 1.000, 8F 0.900 AGREE; gate outer "
                  "level +-0.00 by region reach not re-read by hand: gate PARTIAL; owner trade by ELEMENT_REGISTER "
                  "'GATE STEP' (Lead 08:15)",
    "T-585:FLIGHTS": "BOARD T-585 VERIFIER 2026-11-07T05:58Z (e)(3)-(4)/(f): E1 pitch 1.470544 AGREE, winders 2.350 .. "
                     "2.620191 AGREE, flight lower bound 19.359049 AGREE; the 13 flight pitches rest on T-501 (merged), "
                     "not re-measured: two forms + bounds PARTIALLY VERIFIED",
    "T-585:YARD": "BOARD T-585 VERIFIER 2026-11-07T05:58Z (e)(1)/(f): 0 of 83 DXF strings name a skirting / base: "
                  "yard DRAWING-CONFIRMED 0 lm basis CONFIRMED, face lengths worker-measured (PARTIALLY VERIFIED); "
                  "his 81.32 lm RULE_DIFFERENCE / FREELANCER_SCOPE ACCEPTED",
    "E1_LANDING": "BOARD T-585 VERIFIER F-C-T585-1 + ELEMENT_REGISTER 'E1 LANDING SKIRTING' (Lead 2026-11-07 08:15): "
                  "exterior landing, no printed base: YARD SKIRTING criterion governs, NOT_IN_DRAWING, no line; the "
                  "ENGINE_OMISSION proposal withdrawn; E1 landing walls 3.500 lm geometry VERIFIED (named only)",
}


class ManifestError(Exception):
    pass


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def D(x):
    return None if x is None or x == "" else Decimal(str(x))


def S(x):
    if x is None:
        return None
    x = Decimal(x)
    return "0" if x == 0 else format(x.normalize(), "f")


def pins():
    for k, pin in PINS.items():
        if sha256(IN[k]) != pin:
            raise ManifestError(f"PIN: {IN[k].name} sha256 {sha256(IN[k])[:8]} is not the pinned {pin[:8]}")


# ---- rows ------------------------------------------------------------------------------------------------------

def row(pkg, fix_row, kind, line_id, before, after, evidence, verdict, beside=None, note=None, scope=None):
    """V9 row; a BESIDE row's evidence is that of its beside figures (the line's own state does not move)."""
    if kind == "BESIDE":
        if after is not None:
            raise ManifestError(f"{line_id}: a BESIDE row moves no quantity")
        if evidence not in EVIDENCE:
            raise ManifestError(f"{line_id}: evidence status {evidence!r} is not a WORKFLOW_CONTROLS s.5 status")
        r = M9.row(pkg, fix_row, kind, line_id, before, None, "HELD" if before["class"] == "HELD" else "UNKNOWN",
                   verdict, beside=beside, note=note)
        r["evidence"] = {"status": evidence, "verdict_line": verdict,
                         "scope": scope or "the beside figures; the line's own state is unchanged and not re-verified"}
        return r
    return M9.row(pkg, fix_row, kind, line_id, before, after, evidence, verdict, beside=beside, note=note)


# ---- R-T593-1 (a)-(c): door steps ---------------------------------------------------------------------------------

def step_figures(o):
    """one opening of a T-592-shaped record -> the step's beside figures; refuses two payable lengths."""
    if "payable_lm" not in o or o.get("nosing_basis", "").startswith("PAYABLE"):
        raise ManifestError(f"{o.get('opening')}: one payable length required (nosing is an attribute)")
    pay, nos = D(o["payable_lm"]), D(o["nosing_lm"])
    if pay is None or pay <= 0:
        raise ManifestError(f"{o['opening']}: no payable length")
    if nos is not None and nos > pay:
        raise ManifestError(f"{o['opening']}: nosing {nos} longer than the stone {pay}")
    rm = D(o.get("riser_m"))
    if rm is None:
        if not o.get("riser_m2_bound"):
            raise ManifestError(f"{o['opening']}: riser with no figure must be HELD with its bound by name")
        riser = {"riser_m2": None, "riser_m2_held": list(o["riser_m2_bound"])}
    else:
        if rm <= 0:
            raise ManifestError(f"{o['opening']}: riser {rm} <= 0 (equal levels make no step)")
        m2 = (pay * rm).quantize(Decimal("0.001"))
        if D(o["riser_m2"]) != m2:
            raise ManifestError(f"{o['opening']}: riser m2 {o['riser_m2']} != {pay} x {rm}")
        riser = {"riser_m2": S(m2), "riser_m": S(rm)}
    return {"step_lm_payable": S(pay), "nr": int(o.get("nr", 1)), "nosing_lm_attribute": S(nos),
            "payable_basis": o["payable_basis"], **riser}


def line_m2(line):
    """the threshold line's own m2: its value, or an exact HELD bound (low = high); else None."""
    if line["class"] == "RELEASED":
        return D(line["measured_net"])
    lo, hi = D(line.get("held_low")), D(line.get("held_high"))
    return lo if lo is not None and lo == hi else None


def check_binding(opening, o, line, depth=WALL_DEPTH):
    if line["item_code"] not in THRESHOLD_CODES or line["unit"] != "m2":
        raise ManifestError(f"{opening}: owning line {line['line_id']} is {line['item_code']} {line['unit']}, "
                            f"not a threshold m2 line")
    w = D(o.get("t325_strip_width_m"))
    if w is not None and w != D(o["payable_lm"]):
        raise ManifestError(f"{opening}: payable {o['payable_lm']} != strip width {w}")
    m2 = line_m2(line)
    if m2 is not None and (D(o["payable_lm"]) * depth).quantize(Decimal("0.000001")) != m2:
        raise ManifestError(f"{opening}: {o['payable_lm']} x {depth} != line m2 {m2} ({line['line_id']})")
    return {"strip_width_m": S(w) if w is not None else None, "wall_depth_m": S(depth),
            "line_m2": S(m2) if m2 is not None else None,
            "payable_x_depth_eq_line_m2": m2 is not None}


def door_edge_census(claims):
    """claims: [(edge_key, claimant, row_id)] in priority order; the first claim owns, later ones are EXCLUDED."""
    owner, excluded = {}, []
    for key, who, rid in claims:
        if key in owner:
            excluded.append({"edge": key, "claimant": who, "row": rid, "class": "EXCLUDED",
                             "repeats": owner[key]["row"]})
        else:
            owner[key] = {"claimant": who, "row": rid}
    return {"edges": len(owner), "owners": owner, "excluded_second_readings": excluded}


def pkg_door_steps(t592, idx, gate_line=None):
    """FR-T592-1 (4 house doors, beside the owning threshold lines) + FR-T592-2 (the gate, its own row)."""
    P = "DOOR_STEPS (T-592 FR-T592-1 / FR-T592-2)"
    rows, claims, house = [], [], {"lm": Decimal(0), "nr": 0, "riser_m2": Decimal(0), "nosing": Decimal(0)}
    for name, o in sorted(t592["openings"].items()):
        gate = o["owning_line"] is None
        lid = gate_line if gate else o["owning_line"]
        if lid is None or lid not in idx:
            raise ManifestError(f"{name}: no owning line in the index")
        line = idx[lid]
        fig = step_figures(o)
        bind = check_binding(name, o, line) if not gate else {
            "strip_width_m": None, "wall_gap_m": S(D(o["payable_lm"])), "wall_depth_m": S(D(o["wall_depth_m"])),
            "line_m2": None, "strip_evidence_m2_not_wired": S(D(o["payable_lm"]) * D(o["wall_depth_m"])),
            "t325_state": o["t325_state"]}
        beside = {"opening": name, **fig, "binding": bind, "material": "by the strip's specification (HELD)",
                  "owner_trade": "marble / stone, door-step family (ELEMENT_REGISTER)"}
        edge = o["nosing_source"]
        if gate:
            beside.update(status="PARTIAL", partial_cause="gate outer level +-0.00 by region reach, not re-read by "
                                                          "hand; never folded into the house door-step total")
            rows.append(row(P, "FR-T592-2", "BESIDE", lid, OV.state(line), None, "PARTIALLY VERIFIED",
                            VERDICT["T-592:GATE"], beside=beside,
                            note="gate step beside the candidate's own HELD-blank D-GF-15 threshold line "
                                 "(T-592 printed owning_line null: F-T593-1)"))
        else:
            if o.get("drawing_conflict"):
                beside["drawing_conflict_named"] = o["drawing_conflict"]
            rows.append(row(P, "FR-T592-1", "BESIDE", lid, OV.state(line), None, "VERIFIED", VERDICT["T-592:HOUSE"],
                            beside=beside))
            house["lm"] += D(o["payable_lm"])
            house["nr"] += fig["nr"]
            house["riser_m2"] += D(fig["riser_m2"]) if fig["riser_m2"] is not None else Decimal(0)
            house["nosing"] += D(o["nosing_lm"])
        claims.append((f"{name}:{edge}", lid, rows[-1]["op_id"]))
    return P, rows, claims, {"house_lm": S(house["lm"]), "house_nr": house["nr"],
                             "house_riser_m2": format(house["riser_m2"].quantize(Decimal("0.001")), "f"),
                             "house_nosing_attribute_lm": S(house["nosing"])}


def absorb(order, pkg_name, line_id, v10_before):
    """R-T593-1 (f): take pkg_name's TEXT_ONLY op on line_id out of the order, returned to be carried by V10."""
    out, taken = [], None
    for n, ops in order:
        if n != pkg_name:
            out.append((n, ops))
            continue
        keep = []
        for op in ops:
            if op["line_id"] == line_id:
                if op["kind"] != "TEXT_ONLY" or op.get("after") is not None:
                    raise ManifestError(f"{op['op_id']}: only a TEXT_ONLY op with no after can be absorbed")
                if not OV.same_state(op["before"], v10_before):
                    raise ManifestError(f"{op['op_id']}: stated before differs from the V10 row's before")
                taken = op
            else:
                keep.append(op)
        out.append((n, keep))
    if taken is None:
        raise ManifestError(f"{pkg_name} has no op on {line_id} to absorb")
    return out, taken


# ---- R-T593-1 (d): stair-flight skirting in two forms -----------------------------------------------------------

def load_pieces(path=None):
    return {r["pid"]: r for r in csv.DictReader(Path(path or IN["T501"]).open(encoding="utf-8"))
            if r["kind"] in ("FLIGHT", "STEP")}


def skirting_lines(idx):
    out = {}
    for lid, l in idx.items():
        if l["item_code"] in ("FIN.STAIR.SKIRTING.SLOPED", "FIN.STAIR.SKIRTING.ZIGZAG") \
                and l["element_id"].startswith("STAIR-SKIRT:"):
            form = "SLOPED" if l["item_code"].endswith("SLOPED") else "ZIGZAG"
            key = (l["element_id"][len("STAIR-SKIRT:"):], form)
            if key in out:
                raise ManifestError(f"two {form} lines on {key[0]}")
            out[key] = lid
    return out


def pkg_stair_skirting(pieces, t585, idx):
    P = "STAIR_SKIRTING_FORMS (T-585 flights)"
    lines = skirting_lines(idx)
    held_of = {}
    for st in t585["stairs"]["by_stair"].values():
        for h in st["held"]:
            held_of[h["pid"]] = h
        for s in st["steps_held"]:
            held_of[s["pid"]] = {"pid": s["pid"], "class": s["status"], "bound": [s["lo"], s["hi"]],
                                 "cause": s["cause"], "form": "ZIGZAG"}
    pairs = {k: held_of.pop(k) for k in [k for k in held_of if " + " in k]}
    pair_of = {pid: (k, h) for k, h in pairs.items() for pid in k.split(" + ")}
    rows, sums = [], {"SLOPED": Decimal(0), "ZIGZAG": Decimal(0), "n": 0}
    for pid, p in sorted(pieces.items()):
        sl, zz = lines.get((pid, "SLOPED")), lines.get((pid, "ZIGZAG"))
        if sl is None or zz is None:
            raise ManifestError(f"{pid}: no SLOPED / ZIGZAG line pair in the index")
        bs, bz = OV.state(idx[sl]), OV.state(idx[zz])
        if p["status"] == "HELD-FORM":
            ps, pzz = D(p["sloped_lm"]), D(p["zigzag_lm"])
            if ps is None or pzz is None or ps > pzz:
                raise ManifestError(f"{pid}: a two-form piece needs both forms, pitch <= zigzag")
            for lid, form, v, b in ((sl, "SLOPED", ps, bs), (zz, "ZIGZAG", pzz, bz)):
                rows.append(row(P, "T-585 two forms", "SET", lid, b, M9.held(float(v), float(v)),
                                "PARTIALLY VERIFIED", VERDICT["T-585:FLIGHTS"],
                                beside={"piece": pid, "form": form, "other_form_line": zz if lid == sl else sl},
                                note="exact measure of this form; ORR-007 picks the payable form; never added to "
                                     "the other form, never released"))
            sums["SLOPED"] += ps
            sums["ZIGZAG"] += pzz
            sums["n"] += 1
        elif pid in pair_of:
            pname, pair = pair_of[pid]
            for lid, b, form in ((sl, bs, "SLOPED"), (zz, bz, "ZIGZAG")):
                if form == "SLOPED":
                    rows.append(row(P, "T-585 winder pair", "BESIDE", lid, b, None, "PARTIALLY VERIFIED",
                                    VERDICT["T-585:FLIGHTS"],
                                    beside={"pair": pname, "pair_bound_lm": pair["bound"],
                                            "cause": pair["cause"]},
                                    note="a bound over two lines moves neither line (R-T593-1 (d))"))
                else:
                    rows.append(row(P, "T-585 not bounded", "TEXT_ONLY", lid, b, None, "HELD",
                                    VERDICT["T-585:FLIGHTS"], note="zigzag form of the winder pair: no bound formed"))
        else:
            h = held_of.get(pid)
            if h is None:
                raise ManifestError(f"{pid}: held piece not in T-585")
            lo, hi = D(h["bound"][0]), D(h["bound"][1])
            form = h.get("form", "SLOPED")
            target, other = (sl, zz) if form == "SLOPED" else (zz, sl)
            bt, bo = (bs, bz) if form == "SLOPED" else (bz, bs)
            if hi is None:
                rows.append(row(P, "T-585 unbounded", "TEXT_ONLY", target, bt, None, "HELD", VERDICT["T-585:FLIGHTS"],
                                note=f"{h['class']}: no bound formed; {h['cause']}"))
            else:
                rows.append(row(P, "T-585 held bound", "SET", target, bt, M9.held(float(lo), float(hi)), "HELD",
                                VERDICT["T-585:FLIGHTS"], beside={"piece": pid, "form": form, "class": h["class"]},
                                note=h["cause"]))
            rows.append(row(P, "T-585 not bounded", "TEXT_ONLY", other, bo, None, "HELD", VERDICT["T-585:FLIGHTS"],
                            note=f"{'zigzag' if form == 'SLOPED' else 'sloped'} form of {pid}: T-585 bounds the "
                                 f"{form.lower()} form only"))
    if S(sums["SLOPED"]) != t585["stairs"]["two_form_pitch_lm"] or S(sums["ZIGZAG"]) != \
            t585["stairs"]["two_form_zigzag_lm"]:
        raise ManifestError(f"two-form sums {sums} differ from T-585")
    pair_lo = sum((D(h["bound"][0]) for h in pairs.values()), Decimal(0))
    return P, rows, {"two_form_pieces": sums["n"], "pitch_lm": S(sums["SLOPED"]), "zigzag_lm": S(sums["ZIGZAG"]),
                     "winder_pair_bound_lm": {k: h["bound"] for k, h in pairs.items()},
                     "flight_lower_bound_lm": S(sums["SLOPED"] + pair_lo),
                     "t585_flight_lo": t585["stairs"]["flight_lo"]}


RULINGS_V10 = [
    {"layer": "FIN.STAIR", "host_re": r"^STAIR-SKIRT:", "sources": ["CANDIDATE", "STAIR_SKIRTING_FORMS (T-585 flights)"],
     "ruling": "FIN.STAIR.SKIRTING.SLOPED and .ZIGZAG on one STAIR-SKIRT piece are the two forms of ONE skirting "
               "(ORR-007 picks one); a held piece bounds only the form its source bounds; never added across forms",
     "fix_row": "T-585 two forms / held bound (R-T593-1 (d))"},
]


# ---- R-T593-1 (e): NO_LINE rows ---------------------------------------------------------------------------------

def no_line_rows(t585):
    y = t585["yard"]["totals_lm"]
    land = t585["e1_landing"]
    return [
        {"row": "E1 LANDING SKIRTING", "element": "GF-COURT E1 landing walls (house face, stub, pantry face)",
         "class": "NO_LINE", "status": "NOT_IN_DRAWING", "measured_beside_lm": land["landing_lm"],
         "probe": {"codes": ["FIN.SKIRTING", "FIN.STAIR.SKIRTING.SLOPED", "FIN.STAIR.SKIRTING.ZIGZAG"],
                   "element_contains": ["E1-L", "E1-LD", "E1:landing", "E1#LANDING"]},
         "replaces": "T-585 ENGINE_OMISSION proposal (withdrawn by the Lead ruling)", "verdict_line": VERDICT["E1_LANDING"]},
        {"row": "YARD SKIRTING", "element": "46 yard faces (west court, side walk, porch, pool court)",
         "class": "NO_LINE", "status": "NOT_IN_DRAWING (0 DRAWING-CONFIRMED)",
         "beside": {"drawing_confirmed_lm": y["DRAWING-CONFIRMED"],
                    "wall_foot_not_in_drawing_lm": y["NOT_IN_DRAWING_physical_wall_foot"],
                    "under_unprinted_sills_hi_lm": y["NOT_IN_DRAWING_under_unprinted_sills_range_hi"],
                    "unresolved_bound_lm": y["UNRESOLVED_bound"], "no_face_lm": y["NO_FACE"],
                    "his_lm": t585["yard"]["his"]["yard_skirting_lm"],
                    "who_is_right": "RULE_DIFFERENCE / FREELANCER_SCOPE (his = his paving perimeter)"},
         "probe": {"codes": ["FIN.SKIRTING"], "element_contains": ["YARD", "COURT", "PORCH", "POOL-DECK", "SIDE-WALK"]},
         "open": "the porch / pool-court faces UNRESOLVED 0 .. 11.61 lm (floor finish HELD, OD-1) have no HELD line: "
                 "named for the Lead (F-T593-2), not added here",
         "verdict_line": VERDICT["T-585:YARD"]},
    ]


def probe_no_line(idx, r):
    hits = sorted(k for k, l in idx.items() if l["class"] != "EXCLUDED" and l["item_code"] in r["probe"]["codes"]
                  and any(s in l["element_id"] for s in r["probe"]["element_contains"]))
    return hits


# ---- overlay ----------------------------------------------------------------------------------------------------

def v9_state():
    T = M9.T580
    m, idx, st = T.manifests(), T.base_index(), T.stage()
    base = T.packages(m, idx, st)
    t578, t583, t584, v8 = (M9._json(M9.IN[k]) for k in ("T578", "T583", "T584", "V8"))
    v9 = M9.v9_packages(t578, t583, t584, v8, idx)
    order9 = M9.overlay_order(base, v9)
    rul9 = list(T.RULINGS) + M9.RULINGS_V9
    after9, rep9 = OV.apply(idx, order9, rul9)
    return idx, order9, rul9, after9, rep9, t584


GATE_LINE = "L-56acf34557c315f65bb1"       # GF-THRESHOLD-D-GF-15:threshold strip:HELD (candidate V3.0.58)
ABSORB = ("T-423 r2", "L-c8b5c7f742b22388339e")


def build():
    pins()
    t592, t585 = _json(IN["T592"]), _json(IN["T585"])
    pieces = load_pieces()
    idx, order9, rul9, after9, rep9, t584 = v9_state()
    if idx[GATE_LINE]["element_id"] != "GF-THRESHOLD-D-GF-15:threshold strip:HELD":
        raise ManifestError("gate line is not the D-GF-15 threshold line")
    # V10 rows are stated against the index as it stands after V9 (the before of each V10 step)
    Pd, door_rows, claims, house = pkg_door_steps(t592, after9, GATE_LINE)
    Ps, sk_rows, sk = pkg_stair_skirting(pieces, t585, after9)
    order, taken = absorb(order9, ABSORB[0], ABSORB[1], OV.state(after9[ABSORB[1]]))
    for r in door_rows:
        if r["line_id"] == ABSORB[1]:
            r["absorbs"] = {"op_id": taken["op_id"], "kind": taken["kind"], "note": taken.get("note"),
                            "rule": "R-T593-1 (f)"}
    v10 = [(Pd, door_rows), (Ps, sk_rows)]
    for _, rows in v10:
        M9.validate_rows(rows)
    order10 = order + v10
    rul10 = rul9 + RULINGS_V10
    after10, rep = OV.apply(idx, order10, rul10)
    v10_lines = {r["line_id"] for _, rows in v10 for r in rows}
    others = sorted(k for k in set(after9) | set(after10) if k not in v10_lines and after9.get(k) != after10.get(k))
    nl = no_line_rows(t585)
    for r in nl:
        r["live_lines_before"] = probe_no_line(after9, r)
        r["live_lines_after"] = probe_no_line(after10, r)
        if r["live_lines_before"] or r["live_lines_after"]:
            raise ManifestError(f"NO_LINE {r['row']}: live lines {r['live_lines_after']}")
    door_census = door_edge_census(claims)
    # the T-412 stair census stays 0 doubles / 0 orphans after V10 (V10 writes no step / nosing line)
    edges = M9.load_edges()
    stair_census = M9.census_on(after10, edges, t584, {M9.E1_LINE: ("ST-03", "E1")})
    status = {}
    for r in rep["rows"]:
        status.setdefault(r["package"], {}).setdefault(r["status"], 0)
        status[r["package"]][r["status"]] += 1
    t9, t10 = OV.totals(after9), OV.totals(after10)
    return {
        "schema": SCHEMA, "rule": RULE, "task": "T-593", "candidate": M9.T580.CANDIDATE,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in IN.values()},
        "replaces": {"FR-T584-2 (T-584: edge 3.50 lm, riser 0.390 m2 + D-GF-09 HELD 0 .. 0.270)":
                     "FR-T592-1 house 3.800 lm nr 4, riser 0.570 m2 (FR-T584-2 closed, F-C-T584-1 / F-C-T584-2 closed)",
                     "T-585 E1 landing ENGINE_OMISSION proposal (3.500 lm)": "NO_LINE NOT_IN_DRAWING (F-C-T585-1)"},
        "absorbed": {"op_id": taken["op_id"], "into": next(r["op_id"] for r in door_rows if r["line_id"] == ABSORB[1]),
                     "why": "R1: one Gate B unit per line; the T-423 r2 op writes no quantity and states the same "
                            "before"},
        "door_steps": {"house": house, "gate": {"step_lm": t592["totals"]["gate_payable_lm"],
                                                "riser_m2": t592["totals"]["gate_riser_m2"],
                                                "nosing_attribute_lm": t592["totals"]["gate_nosing_lm_attribute"],
                                                "status": "PARTIAL", "in_house_total": False},
                       "t592_totals": t592["totals"],
                       "his": {"lm": t592["compare"]["his_door_steps_lm"], "nr": t592["compare"]["his_nr"],
                               "ours_minus_his_house_lm": t592["compare"]["gap_house_lm"],
                               "ours_minus_his_with_gate_lm": t592["compare"]["gap_with_gate_lm"],
                               "verdict": "UNRESOLVED (SCOPE): no door id on his rows; no %"},
                       "edge_census": door_census},
        "stair_skirting": sk,
        "no_line_rows": nl,
        "rows": [dict(r, package=n) for n, rows in v10 for r in rows],
        "overlay": {
            "lines": {"base": len(idx), "after_v9": len(after9), "after_v10": len(after10)},
            "order": [{"package": n, "ops": len(o), "status": status.get(n, {})} for n, o in order10],
            "flagged_rows": [r for r in rep["rows"] if r["status"] != "APPLIED"],
            "stale": sum(r["status"] == "STALE" for r in rep["rows"]),
            "two_package_lines": 0,                    # OV.apply raises R1 otherwise
            "conflicts": rep["conflicts"],
            "unexplained_conflicts": sum(c["status"] == "UNEXPLAINED" for c in rep["conflicts"]),
            "other_lines_changed_vs_v9_overlay": others,
            "v10_vs_v9_totals": OV.diff_totals(t9, t10),
        },
        "stair_edge_census_after_v10": {"doubles": len(stair_census["doubles"]), "orphans": len(stair_census["orphans"]),
                                        "edges": stair_census["edges"]},
        "findings": {
            "F-T593-1": "T-592 prints owning_line null for the gate (T-325 UNRESOLVED) but V3.0.58 carries a HELD-blank "
                        "ARCH.THRESHOLD line for D-GF-15 (L-56acf345...); the gate step sits beside it as its own row; "
                        "the strip m2 (1.000 x 0.200 = 0.200 evidence) is NOT wired",
            "F-T593-2": "the yard porch / pool-court skirting UNRESOLVED 0 .. 11.61 lm (OD-1) has no HELD line: absent, "
                        "not 0; Lead to rule whether a HELD line is owed",
            "F-T593-3": "the four house threshold lines hold their m2 as HELD exact bounds (0.2 / 0.18 / 0.18) or "
                        "RELEASED (D-GF-05 0.2): each equals payable lm x 0.200 wall depth, so the step binds the right "
                        "line; the lines' own states are not moved by V10",
        },
        "candidate_files_touched": 0, "released_quantities_changed": 0,
    }


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, default=str) + "\n"


def main(argv):
    text = dumps(build())
    if "--check" in argv:
        ok = OUT_JSON.exists() and OUT_JSON.read_text(encoding="utf-8") == text
        print("T-593 manifest V10: committed output", "is the rebuild" if ok else "DIFFERS from the rebuild")
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
