"""T-675 (lane A, research piece, every villa): MASONRY ROUND 2, the three open masonry findings left by T-670 / T-372 on
ARCH_TAKEOFF_V3.0.63. Nothing is wired: no candidate, no released line, no rule / rulebook version file is changed.

(a) F-T670-1: the two below-N.G. hosts HOUSE_BELOW_NG:MAIN_S / :ANNEX_S carry no colour in their element id, so the
    merged producer (arch_v3059 BY_COLOUR[None]) opened all four material codes on them, two of which (MAS.GLUE.AAC,
    MAS.UNITS.WHITE) describe no physical material. R-T675-1 (PROPOSED, every villa):
      (1) a masonry host whose element id carries no colour takes its colour from its OWN evidence record (the
          engineering-office note it was created from; owner 2026-10-20 10:45: the plan / engineering-office note
          decides black / white and overrides the Urban fallback); a host with no such record keeps all four codes;
      (2) the other colour's material lines on that host are NOT_APPLICABLE_WITH_EVIDENCE (proposal: retired by the
          wiring row with this evidence in the same diff), never valued, never a 0 quantity;
      (3) the host's own colour lines keep the host's committed cause while the host is HELD; a host AT_LEAST plane is
          carried beside in the material's own unit only CONDITIONALLY (the leaf build / thickness not printed),
          never on the line (T-670 rule (4)).
(b) F-T372-2: the B9-04 perimeter components not in the WIRING MANIFEST V20 overlay. R-T675-2 (PROPOSED, every villa,
    refines R-T372-1 (5)): at a FLAGGED_DEFICIT lintel end the bed under the lintel lies on block over at most the
    drawn available masonry for EVERY stopper (T-516 / T-527 'available' already runs through the walls crossed to the
    far face, so beyond it there is no block on the lintel line): high = min(bearing, available) at full precision,
    low 0 (the built bearing is a designer item); a HELD lintel gets [0, 2 x bearing] x f with its cause.
    R-T675-3 (PROPOSED, every villa): a course band's increment over the module is (c - 1) dz with c = the joint-bearing
    ends; C = 1, O (block-to-block, butt or bonded) = 0..1, U (unknown stop) = 0..1, F (free end / jamb) = 0, so
    low = max(0, nC - 1) dz, high = max(0, nC + nO + nU - 1) dz; a band whose high is 0 under every reading (F + U)
    is NOT_APPLICABLE_WITH_EVIDENCE (no increment), not a held quantity; a held piece with its top not drawn adds at
    most one soffit joint per metre of its length: [0, L x f].
(c) F-T372-1: the two 0.20 m perimeter lines staged by the T-580 op 'PERIMETER_MORTAR' carry no evidence stamp, so the
    trial r4 dry run (research/agents_t630/e2e_dry_run.py) prints UNKNOWN. Drawn evidence is restated per wall: own read
    of the face lines in 'P7757' (census source ids, offsets from the wall axis), status by the weakest input.

    bash scripts/agent_env.sh run --tree task-T-675 research/agents_t675/t675_masonry_round2.py [<t125_inputs.pkl>]

The optional pickle (research/agents_t125/alsenan_v2_dump.py output, outside the repository) re-reads the 0.20 m wall
faces; without it the stored own-read figures in FACES_020 are used and marked so. Output: research/agents_t675/out/
(numbers and ids only; no drawing coordinate, no client data).
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t372", ROOT / "research/agents_t372/t372_perimeter_ledger.py")
T372 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T372)

INDEX = ROOT / "research/agents_t665/out/LINE_INDEX_V3_0_63.json"
T670 = ROOT / "research/agents_t670/out/T670_MATERIALS.json"
T372_JSON = ROOT / "research/agents_t372/out/T372_PERIMETER_LEDGER.json"
T520_JUNCTIONS = ROOT / "research/agents_t520/out/JUNCTIONS_T520.csv"
T520_WALLS = ROOT / "research/agents_t520/out/PERIMETER_BY_WALL_T520.csv"
T527_JAMBS = ROOT / "research/agents_t527/out/JAMB_EVIDENCE_V3_T527.csv"
T407 = ROOT / "research/agents_t407/summary_t407.json"
TRIAL_R4 = ROOT / "research/agents_t654/out/TRIAL_BOQ_R4_T654.json"
OUT = ROOT / "research/agents_t675/out"
PINS = {
    INDEX: "cd062bfe777af2393228f31893b71ae7032c8d0e6c1bcbe41b0194e36a8fe8d8",
    T670: "4c58a226a7d3f17f56a4ffaa72229f08bbf4982ef8e52179ce9270c3ae3eb467",
    T520_JUNCTIONS: "b2e5f1864cc2d9ed91cef2c2f4cf4b35f571f45e33496a0ba9621be809a500e0",
    T520_WALLS: "fb5ac4abe455bf5efa8a352ad68cf57defb609c3fac54437a92e94842e3622d1",
    T527_JAMBS: "7ac6e6b93d2a4ac9e7dab3ff0db70d988a256a972b8bb7fb8a139360a43c2ee2",
    TRIAL_R4: "9e032726257c4961972bd7fd8de2620a3f7e2adc1f32a78802764a5289e91733",
}

U_BLACK, MORTAR, GLUE, U_WHITE = "MAS.UNITS.BLACK", "MAS.MORTAR.BLACK", "MAS.GLUE.AAC", "MAS.UNITS.WHITE"
CODES_OF = {"BLACK": (U_BLACK, MORTAR), "WHITE": (GLUE, U_WHITE)}
NA = "NOT_APPLICABLE_WITH_EVIDENCE"
BEARING_M = T372.BEARING_M                 # 0.40 m per end: the candidate's REQUIRED face basis (w + 0.80) x D
FACE, MODULE, JOINT_M = (0.39, 0.19), (0.40, 0.20), 0.010
UNITS_PER_M2 = 12.5                        # UPC-BLACK-BLOCK-001 1.1.0 (Q-75 0.20 / Q-80 A 0.15): 40 x 20 module
STATUS_ASSUMED = "ASSUMED - OWNER-APPROVED"

# Evidence records for colour-less hosts (R-T675-1 (1)): the record each host was created from (T-407, merged 8c0e8349,
# Checker Gate A 2026-11-01 own read of ST p.1 note 2) and the own re-read of this task (ST7757.pdf p.1, 2026-11-10).
HOST_COLOUR_EVIDENCE = {
    "HOUSE_BELOW_NG:MAIN_S": {
        "colour": "BLACK", "source": "ST7757.pdf p.1 (COLUMN & AXIS PLAN) note 2: the neighbour-side exterior ground "
                                     "beams are cast over and under BLACK block built from the foundation level",
        "record": "T-407 run MAIN_S class PRINTED (p.1 n.2); element register BLOCKWORK BELOW N.G.",
        "arch_check": "P7757 architectural DXF: no wall hatch, no block legend and no block-type text on any layer "
                      "(hatches only S-COL.BON SOLID and floor patterns); section B-B draws nothing below the "
                      "+-0.00 ground line: silent, no contrary evidence"},
    "HOUSE_BELOW_NG:ANNEX_S": {
        "colour": "BLACK", "source": "ST7757.pdf p.1 note 2 (as MAIN_S: the annex south run is on the neighbour side)",
        "record": "T-407 run ANNEX_S class PRINTED (p.1 n.2)",
        "arch_check": "as MAIN_S"},
}

# Own read of the 0.20 m black walls of the two UNKNOWN-stamped perimeter lines (P7757.dxf sha256 ab54dd55, census of
# research/agents_t125/alsenan_v2_dump.py on ARCH_TAKEOFF_V2.12): every face source on layer '1', offset from the axis.
FACES_020 = {
    "GF-W01": {"floor": "GF", "census": "WB-FL0001-FL0002", "faces": 11, "offsets_mm": [-100.0, 100.0]},
    "1F-W02": {"floor": "1F", "census": "WB-FL0059-FL0061", "faces": 2, "offsets_mm": [-100.0, 100.0]},
    "1F-W03": {"floor": "1F", "census": "WB-FL0068-FL0070", "faces": 3, "offsets_mm": [-100.0, 100.0]},
    "1F-W09": {"floor": "1F", "census": "WB-FL0024-FL0025", "faces": 2, "offsets_mm": [-100.0, 100.0]},
}
HOSTS_020 = {"L-1c53fadb2f92d1f36d4e": ["GF-W01"], "L-10dd62f66ad05488e63b": ["1F-W02", "1F-W03", "1F-W09"]}


class T675Error(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(float(x) + 0.0, n)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def factor(t):
    """kappa b j (R-T520-1), m3 per metre of joint."""
    return T372.factor(t, FACE, MODULE, JOINT_M)


# ------------------------------------------------------------------------------------------------ (a) colour
def colour_split(host_eid, codes_on_host, evidence):
    """R-T675-1: {code: 'KEEP' | NA} for the material lines of one host; evidence is the host's own record or None."""
    if any(c not in (U_BLACK, MORTAR, GLUE, U_WHITE) for c in codes_on_host):
        raise T675Error(f"{host_eid}: unknown material code")
    if evidence is None:
        return {c: "KEEP" for c in codes_on_host}            # colour not printed: all four stay (cause unchanged)
    col = evidence.get("colour")
    if col not in CODES_OF:
        raise T675Error(f"{host_eid}: evidence names no colour BLACK / WHITE")
    if not evidence.get("source"):
        raise T675Error(f"{host_eid}: a colour without a printed source is not evidence")
    keep = CODES_OF[col]
    if not any(c in keep for c in codes_on_host):
        raise T675Error(f"{host_eid}: no {col} material line on a {col} host: the producer output is not this case")
    return {c: ("KEEP" if c in keep else NA) for c in codes_on_host}


def conditional_black(net_at_least_m2, leaf_t):
    """R-T675-1 (3): beside figures for ONE leaf of a 40 x 20 module black block of thickness leaf_t (conditional)."""
    if net_at_least_m2 is None:
        return None
    if net_at_least_m2 <= 0:
        raise T675Error("an AT_LEAST plane must be positive")
    if leaf_t not in (0.15, 0.20):
        raise T675Error("the 40 x 20 module is owner-confirmed for 0.15 / 0.20 m black block only")
    jr = leaf_t * (1.0 - (FACE[0] * FACE[1]) / (MODULE[0] * MODULE[1]))
    return {"units_at_least_pcs": _r(net_at_least_m2 * UNITS_PER_M2, 4), "mortar_at_least_m3": _r(net_at_least_m2 * jr),
            "joint_m3_per_m2": _r(jr, 7)}


# ------------------------------------------------------------------------------------------------ (b) bed and bands
def bed_end(available_m, stopper, bearing_m=BEARING_M):
    """R-T675-2: metres of block under one lintel end."""
    if available_m is None:
        return {"state": "HELD", "low": None, "high": None, "why": "masonry beyond the jamb not read"}
    if available_m < 0:
        raise T675Error("negative available masonry")
    if stopper not in ("COLUMN", "OPENING", "END_OF_MASONRY", "SEARCH_LIMIT"):
        raise T675Error(f"unknown stopper {stopper!r}")
    if available_m + 1e-9 >= bearing_m:
        return {"state": "EXACT", "low": bearing_m, "high": bearing_m, "why": "available >= bearing"}
    if stopper == "SEARCH_LIMIT":
        raise T675Error("a capped search is never below the bearing")
    return {"state": "RANGE", "low": 0.0, "high": available_m,
            "why": f"FLAGGED_DEFICIT end ({stopper}, drawn available {available_m:.6f} m < {bearing_m:.2f} m printed "
                   "bearing): no block beyond the stopper on the lintel line"}


def bed_lintel(ends, f):
    if any(e["state"] == "HELD" for e in ends):
        return {"state": "HELD", "low": None, "high": None}
    lo, hi = sum(e["low"] for e in ends), sum(e["high"] for e in ends)
    return {"state": "EXACT" if lo == hi else "RANGE", "bearing_low_m": _r(lo), "bearing_high_m": _r(hi),
            "low": _r(lo * f), "high": _r(hi * f)}


def band_bounds(ends):
    """R-T675-3: (low, high) band multipliers of dz for a two-letter end class (C / O / F / U)."""
    if len(ends) != 2 or any(c not in "COFU" for c in ends):
        raise T675Error(f"end class {ends!r} is not two of C / O / F / U")
    n_c = ends.count("C")
    n_var = ends.count("O") + ends.count("U")
    return max(0, n_c - 1), max(0, n_c + n_var - 1)


def band_cause(ends_text):
    t = ends_text.lower()
    why = []
    if "lintel bearing not established" in t:
        oid = next(w for w in ends_text.replace("|", " ").split() if w.startswith("D-"))
        why.append(f"{oid}: FLAGGED_DEFICIT lintel end (T-516 / T-527: drawn available masonry < the printed 0.40 m RC "
                   "lintel bearing; the built bearing decides whether block meets the lintel end in this course band)")
    if "ring" in t or "dome" in t:
        why.append("dome opening piece: top of wall / ring position not drawn (T-227 / T-261)")
    if not why:
        raise T675Error(f"no committed cause for band {ends_text!r}")
    return "DESIGNER ITEM", "; ".join(why)


# ------------------------------------------------------------------------------------------------ inputs
def _load():
    for p, h in PINS.items():
        if _sha(p) != h:
            raise T675Error(f"{p.name}: sha256 {_sha(p)[:8]} is not the merged {h[:8]}")
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    t670 = json.loads(T670.read_text(encoding="utf-8"))
    t372 = json.loads(T372_JSON.read_text(encoding="utf-8"))
    t407 = json.loads(T407.read_text(encoding="utf-8"))
    junctions = list(csv.DictReader(T520_JUNCTIONS.open(encoding="utf-8")))
    walls = {r["wall_id"]: r for r in csv.DictReader(T520_WALLS.open(encoding="utf-8"))}
    jambs = list(csv.DictReader(T527_JAMBS.open(encoding="utf-8")))
    trial = json.loads(TRIAL_R4.read_text(encoding="utf-8"))
    return idx, t670, t372, t407, junctions, walls, jambs, trial


# ------------------------------------------------------------------------------------------------ (a) apply
def part_a(idx, t670, t407):
    lines = {l["line_id"]: l for l in idx["lines"]}
    runs = {r["id"]: r for r in t407["runs"]}
    rows = []
    for host_eid, ev in HOST_COLOUR_EVIDENCE.items():
        mats = [r for r in t670["rows"] if r["host"] == host_eid]
        if len(mats) != 4:
            raise T675Error(f"{host_eid}: {len(mats)} material lines, expected the 4 of BY_COLOUR[None]")
        host_line = lines[mats[0]["host_line_id"]]
        if host_line["class"] != "HELD" or host_line["item_code"] != "MAS.BLOCK":
            raise T675Error(f"{host_eid}: host is not a HELD MAS.BLOCK line")
        split = colour_split(host_eid, [m["code"] for m in mats], ev)
        run = runs[host_eid.split(":")[1]]
        net = run.get("net_at_least_m2")
        for m in sorted(mats, key=lambda r: r["code"]):
            ln = lines[m["material_line_id"]]
            if ln["class"] != "HELD" or ln["measured_net"] is not None or ln["held_low"] is not None:
                raise T675Error(f"{ln['line_id']}: not HELD blank in V3.0.63")
            row = {"host": host_eid, "host_line_id": m["host_line_id"], "material_line_id": m["material_line_id"],
                   "code": m["code"], "unit": m["unit"], "before": "HELD blank", "verdict": split[m["code"]],
                   "evidence": ev["source"], "arch_check": ev["arch_check"]}
            if split[m["code"]] == NA:
                row.update(after=NA, proposal="retire in the wiring row with this evidence in the same diff (never 0, "
                                              "never valued): the host is black block, no AAC unit or glue is laid")
            else:
                row.update(after="HELD blank", cause=m["cause"] + "; leaf build / thickness not printed (T-407 s.7 "
                                                                   "item 4: 0.20 band vs 0.30 beam)")
                if net is not None:
                    c15, c20 = conditional_black(net, 0.15), conditional_black(net, 0.20)
                    if m["code"] == U_BLACK:
                        row["beside_conditional"] = {
                            "AT_LEAST_pcs": c15["units_at_least_pcs"],
                            "condition": f"net AT_LEAST {net} m2 x 12.5 / m2: at least one leaf of 0.15 or 0.20 m black "
                                         "block on the 40 x 20 module (Q-75 / Q-80 A); a two-leaf build only adds"}
                    else:
                        row["beside_conditional"] = {
                            "AT_LEAST_m3": c15["mortar_at_least_m3"], "if_one_020_leaf_m3": c20["mortar_at_least_m3"],
                            "condition": f"net AT_LEAST {net} m2 x 0.07375 t: one 0.15 m leaf at least (0.20 m leaf "
                                         "beside); collar joint of a two-leaf build not included; PROVISIONAL "
                                         "(10 mm joint, owner 2026-10-29)"}
                else:
                    row["beside_conditional"] = {"none": "no bound: annex beam soffit CONFLICT (D-35, RFI-S09); "
                                                         "reading L (net 7.000 m2 -> 87.5 pcs) shown in T-407, not "
                                                         "adopted"}
            rows.append(row)
    return rows


def counts_a(idx, rows):
    """per code: HELD count before / after (NA lines leave the HELD count only through the wiring row)."""
    held = {}
    for l in idx["lines"]:
        if l["item_code"] in (U_BLACK, MORTAR, GLUE, U_WHITE) and l["class"] == "HELD":
            k = l["item_code"]
            held.setdefault(k, {"held": 0, "bounded": 0, "blank": 0})
            held[k]["held"] += 1
            held[k]["bounded" if (l["held_low"] is not None or l["held_high"] is not None) else "blank"] += 1
    out = {}
    for k, v in sorted(held.items()):
        na = sum(1 for r in rows if r["code"] == k and r["verdict"] == NA)
        out[k] = {"before": dict(v), "after": {"held": v["held"] - na, "bounded": v["bounded"],
                                               "blank": v["blank"] - na, NA: na}}
    return out


# ------------------------------------------------------------------------------------------------ (b) apply
def part_b_bed(t372, jambs):
    f = factor(0.15)
    av = {}
    for j in jambs:
        av[(j["opening_id"], j["side"])] = (float(j["v3_available_6dp_m"]), j["stopper"], float(j["wall_t_m"]))
    rows = []
    for b in t372["lintel_bearing_bed"]:
        oid = b["opening_id"]
        if b["state"] == "HELD":
            if (oid, "START") in av or (oid, "END") in av:
                raise T675Error(f"{oid}: jamb evidence exists for a HELD lintel: not this case")
            hi = _r(2 * BEARING_M * f)
            rows.append({"opening_id": oid, "mortar_line_id": b["line_id"], "state": "HELD", "low": 0.0, "high": hi,
                         "was": [None, None],
                         "cause": "DESIGNER ITEM / candidate: the lintel itself is HELD_RANGE (face 0 .. 0.34 m2, "
                                  "T-582 class, inside the held dome piece of 1F-W13 / W17); if built, its bed lies on "
                                  "at most 2 x 0.40 m of block (printed bearing): 0 .. 0.80 f; jamb availability on "
                                  "its END side not read (T-527 lists only D-1F-08 END, 0.8445 m to it)"})
            continue
        ends = []
        for e in b["ends"]:
            a, stop, t = av[(oid, e["side"])]
            if abs(t - 0.15) > 1e-9:
                raise T675Error(f"{oid}: not a 0.15 m wall")
            ends.append(dict(bed_end(a, stop), side=e["side"], available_6dp_m=a, stopper=stop,
                             was=[e["low"], e["high"]]))
        bl = bed_lintel(ends, f)
        rows.append({"opening_id": oid, "mortar_line_id": b["line_id"], "lintel_line_id": b["lintel_line_id"],
                     "state": bl["state"], "low": bl["low"], "high": bl["high"], "was": [b["low"], b["high"]],
                     "bearing_m": [bl["bearing_low_m"], bl["bearing_high_m"]], "ends": ends})
    return rows


def part_b_bands(t372, junctions):
    f = factor(0.15)
    jx = {}
    for j in junctions:
        if j["class"] != "HELD":
            continue
        k = (j["wall_id"], f"{float(j['z0_m']):.4f}", f"{float(j['z1_m']):.4f}", j["end_ids"])
        if k in jx:
            raise T675Error(f"two HELD junction rows {k}")
        jx[k] = j
    rows = []
    for ln in t372["lines"]:
        for h in ln["held_junctions"]:
            k = (h["wall_id"], f"{h['band_m'][0]:.4f}", f"{h['band_m'][1]:.4f}", h["ends"])
            j = jx.pop(k)
            dz = float(j["z1_m"]) - float(j["z0_m"])
            lo_m, hi_m = band_bounds(j["ends"])
            if abs(lo_m * dz - float(j["increment_low_m"])) > 1e-9 or abs(hi_m * dz - float(j["increment_high_m"])) > 1e-9:
                raise T675Error(f"{k}: R-T675-3 does not reproduce T-520 ({j['increment_low_m']} .. "
                                f"{j['increment_high_m']})")
            hi = _r(hi_m * dz * f)
            if abs(hi - h["bound_m3"][1]) > 1e-6:
                raise T675Error(f"{k}: bound {hi} is not T-372's {h['bound_m3']}")
            if hi_m == 0:
                verdict, cls, why = NA, "NO INCREMENT", (f"ends {j['ends']}: a free end (F) and one unknown stop carry "
                                                         "at most one joint-bearing end, the module already credits "
                                                         "one: increment 0 under every reading (R-T675-3)")
            else:
                verdict = "HELD bounded"
                cls, why = band_cause(j["end_ids"])
            rows.append({"wall_id": h["wall_id"], "host_line_id": ln["host_line_id"],
                         "mortar_line_id": ln["mortar_line_id"], "band_m": h["band_m"], "ends": j["ends"],
                         "end_ids": j["end_ids"], "segment_m": [float(j["x0_m"]), float(j["x1_m"])],
                         "low": _r(lo_m * dz * f), "high": hi, "verdict": verdict, "cause_class": cls, "cause": why})
    left = [k for k in jx if k[0] in {r["wall_id"] for r in rows}]
    if left:
        raise T675Error(f"HELD junction rows of these walls not in T-372: {left}")
    return rows


def part_b_pieces(walls, band_rows):
    """held pieces (top of wall not drawn) on the valued hosts: soffit term [0, L x f] per piece (R-T675-3)."""
    f = factor(0.15)
    out = []
    for wid in sorted({r["wall_id"] for r in band_rows}):
        txt = walls[wid]["held_pieces"]
        if not txt:
            continue
        for part in txt.split("; "):
            head = part.split(":", 1)[0]                     # '<piece name> <length> m'
            if not head.endswith(" m"):
                raise T675Error(f"{wid}: held piece {head!r} has no length")
            L = float(head.rsplit(" ", 2)[-2])
            out.append({"wall_id": wid, "piece": head.rsplit(" ", 2)[0], "length_m": L, "low": 0.0,
                        "high": _r(L * f), "cause": part.split(":", 1)[1].strip()})
    return out


def part_b_hosts(t372, band_rows, pieces):
    """per valued mortar line: drawn part (T-372) + held bands + held-piece soffits -> the companion proposal."""
    wall_host = {}
    out = []
    for ln in t372["lines"]:
        if ln["perimeter_state"] == "HELD":
            continue
        for w in ln["walls"]:
            wall_host[w] = ln["mortar_line_id"]
        b = [r for r in band_rows if r["mortar_line_id"] == ln["mortar_line_id"] and r["verdict"] != NA]
        p = [r for r in pieces if r["wall_id"] in ln["walls"]]
        bh = _r(sum(r["high"] for r in b))
        ph = _r(sum(r["high"] for r in p))
        lo, hi = ln["perimeter_low_m3"], ln["perimeter_high_m3"]
        out.append({"mortar_line_id": ln["mortar_line_id"], "host": ln["host"], "walls": ln["walls"], "low": lo,
                    "high_drawn_t372": hi, "held_bands": len(b), "held_bands_high": bh, "held_pieces": len(p),
                    "held_pieces_high": ph, "envelope": [lo, _r(hi + bh + ph)],
                    "companion_proposed": [0.0, _r(hi + bh + ph - lo)], "open_in_v20": bool(p)})
    return out


def v20_companions(trial):
    out = {}
    for r in trial["per_line"]:
        lid = r["line_id"]
        if r["item_code"] == MORTAR and lid.endswith("#FR-T615-3:RANGE"):
            out[lid] = (r["held_low"], r["held_high"])
    return out


# ------------------------------------------------------------------------------------------------ (c) faces
def faces_from_pickle(pkl):
    import pickle
    d = pickle.load(open(pkl, "rb"))
    got = {}
    for wid, rec in FACES_020.items():
        F = d["floors"][rec["floor"]]
        seg = {s["id"]: s for s in F["ents"]["segments"]}
        w = next(x for x in F["walls"] if x["wall_id"] == rec["census"])
        (x0, y0), (x1, y1) = w["centreline"]
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        offs = set()
        for sid in w["source_ids"]:
            s = seg[sid]
            if s["layer"] != "1":
                raise T675Error(f"{wid}: face source {sid} not on the wall layer")
            for px, py in (s["a"], s["b"]):
                offs.add(round((-(px - x0) * uy + (py - y0) * ux) * F["unit_m"] * 1000, 1))
        got[wid] = {"faces": len(w["source_ids"]), "offsets_mm": sorted(offs), "t_census_m": w["t_m"]}
    return got


def part_c(t372, trial, pkl=None):
    own = faces_from_pickle(pkl) if pkl else None
    lines = {l["host_line_id"]: l for l in t372["lines"]}
    stamps = {r["line_id"]: r for r in trial["per_line"]}
    rows = []
    for hid, wids in HOSTS_020.items():
        ln = lines[hid]
        st = stamps[f"NEW:MAS.MORTAR.BLACK:PERIMETER:{hid}"]
        if st["evidence"] != "UNKNOWN":
            raise T675Error(f"{hid}: trial r4 stamp is {st['evidence']}, not the finding's UNKNOWN")
        if abs(st["measured_net"] - ln["perimeter_low_m3"]) > 1e-9:
            raise T675Error(f"{hid}: staged {st['measured_net']} is not T-372's {ln['perimeter_low_m3']}")
        walls = []
        for w in wids:
            rec = FACES_020[w]
            if own is not None:
                if own[w]["offsets_mm"] != rec["offsets_mm"] or own[w]["faces"] != rec["faces"]:
                    raise T675Error(f"{w}: own face read {own[w]} differs from the recorded {rec}")
            t = (rec["offsets_mm"][1] - rec["offsets_mm"][0]) / 1000.0
            walls.append({"wall_id": w, "census": rec["census"], "face_sources": rec["faces"],
                          "offsets_mm": rec["offsets_mm"], "thickness_m": _r(t, 4),
                          "read": "re-read this run from the pickle" if own is not None else "recorded own read"})
        if any(abs(w["thickness_m"] - 0.20) > 1e-9 for w in walls):
            raise T675Error(f"{hid}: a face pair is not 0.20 m apart")
        rows.append({"perimeter_line": st["line_id"], "host_line_id": hid, "host": ln["host"], "walls": walls,
                     "staged_m3": st["measured_net"], "was": "UNKNOWN (T-580 op PERIMETER_MORTAR carries no evidence "
                                                             "stamp; e2e_dry_run.py)",
                     "proposed_stamp": STATUS_ASSUMED,
                     "basis": "thickness DRAWING-CONFIRMED (face lines 0.200 m apart on the wall layer; the P7757 "
                              "DXF has no wall hatch on any layer); colour BLACK (ST p.1 note 2 neighbour-side "
                              "walls / host element id VERIFIED_BLACK); host area VERIFIED; module 40 x 20 OWNER "
                              "CONFIRMED (Q-75); 10 mm joint ASSUMED - OWNER-APPROVED (owner 2026-10-29): weakest = "
                              "ASSUMED - OWNER-APPROVED, line PROVISIONAL, never VERIFIED (T-520 Checker re-measured "
                              "2 / 4 walls)"})
    return rows


# ------------------------------------------------------------------------------------------------ build
def build(pkl=None):
    idx, t670, t372, t407, junctions, walls, jambs, trial = _load()
    a = part_a(idx, t670, t407)
    bed = part_b_bed(t372, jambs)
    bands = part_b_bands(t372, junctions)
    pieces = part_b_pieces(walls, bands)
    hosts = part_b_hosts(t372, bands, pieces)
    comp = v20_companions(trial)
    c = part_c(t372, trial, pkl)
    gfw22 = next(x for ln in t372["lines"] for x in ln["beside_held"] if x["wall_id"] == "GF-W22")
    bed_valued = [r for r in bed if r["state"] != "HELD"]
    tot = {
        "lintel_bed_m3": {"was": [t372["totals"]["lintel_bearing_bed_beside"]["low"],
                                  t372["totals"]["lintel_bearing_bed_beside"]["high"]],
                          "after_8_lintels": [_r(sum(r["bearing_m"][0] for r in bed_valued) * factor(0.15)),
                                              _r(sum(r["bearing_m"][1] for r in bed_valued) * factor(0.15))],
                          "after_bearing_m": [_r(sum(r["bearing_m"][0] for r in bed_valued)),
                                              _r(sum(r["bearing_m"][1] for r in bed_valued))],
                          "sum_of_rounded_rows": [_r(sum(r["low"] for r in bed_valued)),
                                                  _r(sum(r["high"] for r in bed_valued))],
                          "D-1F-09_beside": [0.0, next(r["high"] for r in bed if r["state"] == "HELD")]},
        "held_bands": {"was": {"count": len(bands), "high": t372["totals"]["held_junction_bands_beside"]["high"]},
                       "after": {"held_bounded": sum(1 for r in bands if r["verdict"] != NA),
                                 NA: sum(1 for r in bands if r["verdict"] == NA),
                                 "high": _r(sum(r["high"] for r in bands))}},
        "held_piece_soffits": {"pieces": len(pieces), "high": _r(sum(r["high"] for r in pieces))},
        "gf_w22_beside": {"bound": gfw22["figure_beside"], "cause": gfw22["why"]},
        "materials_a": counts_a(idx, a),
    }
    return {"task": "T-675", "candidate": idx["candidate_version"], "rules": ["R-T675-1", "R-T675-2", "R-T675-3"],
            "factor_015_m3_per_m": _r(factor(0.15), 9), "pinned": {str(p.relative_to(ROOT)): h for p, h in PINS.items()},
            "part_a": a, "part_b": {"lintel_bed": bed, "bands": bands, "pieces": pieces, "hosts": hosts,
                                    "v20_companions": {k: list(v) for k, v in comp.items()}},
            "part_c": c, "totals": tot}


def to_csv(res):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["part", "id", "line_id", "code_or_wall", "before", "after", "low", "high", "cause_or_basis"])
    for r in res["part_a"]:
        w.writerow(["a", r["host"], r["material_line_id"], r["code"], r["before"], r["after"], "", "",
                    r.get("cause", r.get("proposal", ""))[:160]])
    for r in res["part_b"]["lintel_bed"]:
        w.writerow(["b-bed", r["opening_id"], r["mortar_line_id"], "lintel bed", f"{r['was'][0]} .. {r['was'][1]}",
                    r["state"], r["low"], r["high"], r.get("cause", "")[:160]])
    for r in res["part_b"]["bands"]:
        w.writerow(["b-band", f"{r['wall_id']} {r['band_m'][0]}-{r['band_m'][1]} {r['ends']}", r["mortar_line_id"],
                    r["wall_id"], "HELD", r["verdict"], r["low"], r["high"], r["cause"][:160]])
    for r in res["part_b"]["pieces"]:
        w.writerow(["b-piece", f"{r['wall_id']} {r['piece']}", "", r["wall_id"], "OPEN", "HELD bounded", r["low"],
                    r["high"], r["cause"][:160]])
    for r in res["part_c"]:
        w.writerow(["c", r["perimeter_line"][-22:], r["host_line_id"], " ".join(x["wall_id"] for x in r["walls"]),
                    "UNKNOWN", r["proposed_stamp"], r["staged_m3"], r["staged_m3"], r["basis"][:160]])
    return buf.getvalue()


def main(argv):
    res = build(argv[1] if len(argv) > 1 else None)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "T675_MASONRY_ROUND2.json").write_text(json.dumps(res, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                                  encoding="utf-8")
    (OUT / "T675_MASONRY_ROUND2.csv").write_text(to_csv(res), encoding="utf-8")
    print(json.dumps(res["totals"], indent=1, sort_keys=True))
    for h in res["part_b"]["hosts"]:
        print(h["mortar_line_id"], h["walls"], h["envelope"], h["companion_proposed"], "open in V20:", h["open_in_v20"])


if __name__ == "__main__":
    main(sys.argv)
