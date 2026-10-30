"""T-347 development-villa binding: every T-320 buried-structure DISPLACEMENT row -> one ARCH_TAKEOFF_V3.0.24 line id
(or NO_LINE with the reason), the neat pit / trench plans with their overlaps, and the earthworks FILL table for the
lane I row T-350 (B1-02 excavation / B1-03 backfill / B1-04 disposal). Reads ONLY merged research files and the
committed candidate snapshot (no drawing, no private file):

  research/agents_t320/LEDGER_T320.csv, summary.json         (MERGED 5ddb2ba1, displacement ledger)
  research/agents_t170/LEDGER_T170.csv, summary.json         (MERGED 2991be3d, neat pits / trenches, overlaps)
  research/agents_t253/LEDGER_T253.csv                       (run index of the T-320 EXT-MAIN / BOUNDARY rows)
  research/agents_t332/FORMWORK_T332_BY_FACE.csv             (MERGED 61d5597e, run -> candidate line id)
  research/agents_t347/CANDIDATE_V3024_BURIED_LINES.json     (t347_candidate.py on an own V3.0.24 run)

    python3 -I research/agents_t347/t347_alsenan.py [--write]
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t347_rules as R  # noqa: E402

RES = ROOT / "research"
EPS = 1e-6
FRAME_TOL_MM = 2.0
FORMATION_MIN_M = 1.50            # ST p.9 boxed note 1: 'not less than 1.5 m' (a minimum: R-T347-3)
POOL_FORMATION_M = 1.50           # T-183 r2: rim +0.30 - 1.20 - 0.40 - 0.05 - 0.05 - 0.10 = -1.50 (DRAWING-CONFIRMED)
BLINDING_T = 0.10                 # p.13 '10cm Plain con.'


def _csv(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _f(x):
    return None if x in (None, "") else float(x)


def _rng(s):
    if not s:
        return None, None
    a, b = s.split("..")
    return float(a), float(b)


# ------------------------------------------------------------------ inputs

def load():
    cand = _json(HERE / "CANDIDATE_V3024_BURIED_LINES.json")
    return {
        "cand": cand,
        "lines": {l["line_id"]: l for l in cand["lines"]},
        "t320": _csv(RES / "agents_t320/LEDGER_T320.csv"),
        "t320s": _json(RES / "agents_t320/summary.json"),
        "t170": _csv(RES / "agents_t170/LEDGER_T170.csv"),
        "t170s": _json(RES / "agents_t170/summary.json"),
        "t253": [r["item"] for r in _csv(RES / "agents_t253/LEDGER_T253.csv")],
        "t332": _csv(RES / "agents_t332/FORMWORK_T332_BY_FACE.csv"),
    }


def line_qty(l):
    """(value, hi): measured_net, else the bounded high end, else None (a blank line)."""
    v = l.get("measured_net")
    return v, (v if v is not None else l.get("bounded_high"))


# ------------------------------------------------------------------ id binding

_FTG = re.compile(r"^(?:P-C:)?FTG:SH10:([A-Z0-9]+)@(-?\d+),(-?\d+):([0-9a-f]+)$")
_NECK = re.compile(r"^(?:[PU]-C:NECK:COL:|NECK:)SH10:([A-Z0-9]*)@(-?\d+),(-?\d+)$")


def footing_frame(D):
    """The candidate's footing ids are in the GROUND-plan frame, T-170 / T-320 in the FOUNDATION-plan frame: one
    translation, derived from the footings whose element hash is unique on both sides and checked on every footing."""
    t320 = {}
    for r in D["t320"]:
        if r["kind"] == "FOOTING":
            m = _FTG.match(r["group"][4:])
            if m:
                t320[m.group(4)] = (m.group(1), float(m.group(2)), float(m.group(3)))
    cand = {}
    for l in D["cand"]["lines"]:
        if l["item_code"] == "STR.CONC.FOOTING":
            m = _FTG.match(l["element_id"])
            if m:
                cand.setdefault(m.group(4), []).append((m.group(1), float(m.group(2)), float(m.group(3))))
    deltas = []
    for h, (t, x, y) in t320.items():
        c = cand.get(h) or []
        if len(c) == 1 and c[0][0] == t:
            deltas.append((round(c[0][1] - x), round(c[0][2] - y)))
    if len(deltas) < 3:
        raise R.Refused("footing frame: fewer than three footings with a shared hash")
    xs, ys = [d[0] for d in deltas], [d[1] for d in deltas]
    if max(xs) - min(xs) > FRAME_TOL_MM or max(ys) - min(ys) > FRAME_TOL_MM:
        raise R.Refused(f"footing frame: translations disagree beyond {FRAME_TOL_MM} mm {sorted(set(deltas))}")
    # ids print integer mm: the frame is the most frequent translation; spread <= the tolerance (ids rounded)
    return max(set(deltas), key=deltas.count)


def footing_line(D, group, frame):
    if group.endswith("T652:10A5"):
        eid = "P-C:FTG:SH10:T652:10A5"
        hits = [l for l in D["cand"]["lines"] if l["item_code"] == "STR.CONC.FOOTING" and l["element_id"] == eid]
        return (hits[0]["line_id"], "element id P-C:FTG:SH10:T652:10A5 (open outline 1B1B)") if len(hits) == 1 else (None, "")
    m = _FTG.match(group[4:])
    t, x, y = m.group(1), float(m.group(2)) + frame[0], float(m.group(3)) + frame[1]
    hits = []
    for l in D["cand"]["lines"]:
        if l["item_code"] != "STR.CONC.FOOTING":
            continue
        c = _FTG.match(l["element_id"])
        if c and c.group(1) == t and abs(float(c.group(2)) - x) <= FRAME_TOL_MM and abs(float(c.group(3)) - y) <= FRAME_TOL_MM:
            hits.append((l, c.group(4)))
    if len(hits) != 1:
        raise R.Refused(f"footing {group}: {len(hits)} candidate footing lines at the translated position")
    l, h = hits[0]
    note = f"type {t} at the translated position (frame +{frame[0]}, +{frame[1]} mm)"
    if h != m.group(4):
        note += f"; element hash {h} differs from the T-170 hash {m.group(4)} (same outline position, same type)"
    return l["line_id"], note


def neck_line(D, rid, frame):
    m = _NECK.match(rid)
    t, x, y = m.group(1), float(m.group(2)) + frame[0], float(m.group(3)) + frame[1]
    hits = []
    for l in D["cand"]["lines"]:
        if l["item_code"] != "STR.CONC.NECK":
            continue
        c = _NECK.match(l["element_id"])
        if c and c.group(1) == t and abs(float(c.group(2)) - x) <= FRAME_TOL_MM and abs(float(c.group(3)) - y) <= FRAME_TOL_MM:
            hits.append(l)
    if len(hits) != 1:
        raise R.Refused(f"neck {rid}: {len(hits)} candidate neck lines at the translated position")
    return hits[0]["line_id"], f"neck type {t} at the translated position"


def run_map(D):
    """run id -> candidate line id, from the Checker-verified T-332 face binding (one line per run, else refused)."""
    m = {}
    for r in D["t332"]:
        lid = r["new_line_id"] or r["line_id"]
        if not lid:
            continue
        it, fid = r["item"], r["face_id"]
        run = None
        if r["element"] == "GROUND_BEAM":
            x = re.match(r"span (\S+)", it) or re.match(r"(ARC:\S+) ", it)
            run = x.group(1) if x else None
        elif r["element"] == "BOUNDARY" and fid.startswith("R4-185."):
            run = fid.split(".", 1)[1]
        if run:
            m.setdefault(run, set()).add(lid)
    bad = {k: v for k, v in m.items() if len(v) != 1}
    if bad:
        raise R.Refused(f"run -> line not unique: {bad}")
    return {k: next(iter(v)) for k, v in m.items()}


def _by_element(D, code, eid):
    hits = [l for l in D["cand"]["lines"] if l["item_code"] == code and l["element_id"] == eid]
    if len(hits) != 1:
        raise R.Refused(f"{code} {eid}: {len(hits)} lines")
    return hits[0]["line_id"]


def _by_element_suffix(D, code, suffix):
    hits = [l for l in D["cand"]["lines"] if l["item_code"] == code and l["element_id"].endswith(suffix)]
    if len(hits) != 1:
        raise R.Refused(f"{code} *{suffix}: {len(hits)} lines")
    return hits[0]["line_id"]


# ------------------------------------------------------------------ displacement rows (T-320 + the pool split)

def displacement_rows(D):
    rows = []
    for r in D["t320"]:
        lo, hi = _rng(r["range_m3"])
        row = {"id": r["id"], "group": r["group"], "kind": r["kind"], "plan_m2": _f(r["plan_m2"]),
               "value_m3": _f(r["value_m3"]), "range_lo": lo, "range_hi": hi, "coef": _f(r["coef_m3_per_m"]),
               "status": r["status"], "held": r["held"], "above_eg_m3": _f(r["above_EG_excluded_m3"]) or 0.0,
               "source": r["source"], "info": r["info"]}
        if r["id"] == "POOL:ENVELOPE":
            continue                                   # split below: one physical component per owner line
        rows.append(row)
    pd = D["t320s"]["pool_decomposition"]
    above_walls = round(2.828071 - pd["walls_below_EG"], 6)   # T-183 r2 walls 2.828071 = below 2.121053 + above 0.707018
    split = [("POOL:BASE", "POOL_BASE", pd["base"], 0.0), ("POOL:WALLS", "POOL_WALLS", pd["walls_below_EG"], above_walls),
             ("POOL:WATER_SPACE", "VOID", pd["water_space_below_EG"], 0.0),
             ("POOL:FLOOR_BUILDUP", "POOL_LAYER", pd["floor_buildup"], 0.0),
             ("POOL:SCREED_UNDER_BASE", "POOL_LAYER", pd["screed_under_base"], 0.0),
             ("POOL:SCREED_UP_WALLS", "POOL_LAYER", pd["screed_up_walls_below_EG"], 0.0),
             ("POOL:MEMBRANE_UNDER", "POOL_LAYER", pd["membrane_under"], 0.0),
             ("POOL:MEMBRANE_UP_WALLS", "POOL_LAYER", pd["membrane_up_walls_below_EG"], 0.0),
             ("POOL:BLINDING_AT_MEMBRANE_LINE", "BLINDING", pd["blinding_at_membrane_line"], 0.0)]
    tot = sum(s[2] for s in split)
    if abs(tot - 18.325138) > 1e-5:
        raise R.Refused(f"pool split {tot} does not close to the T-320 envelope 18.325138")
    for rid, kind, v, ab in split:
        rows.append({"id": rid, "group": "PIT:POOL", "kind": kind, "plan_m2": None, "value_m3": v, "range_lo": None,
                     "range_hi": None, "coef": 0.0, "status": "DRAWING-CONFIRMED", "held": "",
                     "above_eg_m3": ab, "source": "T-320 pool_decomposition (T-183 r2 p.7 layers)", "info": ""})
    return rows


NETTED_SIDE = "FN"   # D-32: the FN outline is clipped where it meets F9 / F8 (the candidate line is net, F9 / F8 whole)


def net_of_shared(D, rows):
    """Apply the T-320 NETTED shared volumes to the FN side (D-32), so each row carries its net share."""
    by = {r["id"]: r for r in rows}
    log = []
    for s in D["t320s"]["shared"]:
        if s["status"] != "NETTED":
            continue
        a, b = s["a"], s["b"]
        side = b if ":FN@" in b else a
        if ":FN@" not in side:
            raise R.Refused(f"netted volume {a} / {b}: no FN side")
        r = by[side]
        r["value_m3"] = round(r["value_m3"] - s["value_m3"], 6)
        r["plan_m2"] = round(r["plan_m2"] - s["plan_m2"], 6)
        r["netted_m3"] = round((r.get("netted_m3") or 0.0) + s["value_m3"], 6)
        log.append((side, s["value_m3"]))
    return log


def mapping(D, rows, frame):
    rm = run_map(D)
    out, basis = {}, {}
    pit_blind = _by_element_suffix(D, "STR.CONC.BLINDING", "BLINDING_FOOTINGS_RELEASED")
    gb_blind = _by_element_suffix(D, "STR.CONC.BLINDING", "BLINDING_GROUND_BEAM")
    strap_blind = _by_element_suffix(D, "STR.CONC.BLINDING", "BLINDING_STRAP")
    t652_blind = _by_element_suffix(D, "STR.CONC.BLINDING", "BLINDING_FOOTING:FTG:SH10:T652:10A5")
    pool = {"POOL:BASE": _by_element(D, "STR.CONC.POOL", "HL:POOL_CONCRETE:POOL-1:BASE"),
            "POOL:WALLS": _by_element(D, "STR.CONC.POOL", "HL:POOL_CONCRETE:POOL-1:WALLS")}
    for r in rows:
        i, k, g = r["id"], r["kind"], r["group"]
        if g.startswith("PIT:FTG") and k == "FOOTING":
            out[i], basis[i] = footing_line(D, g, frame)
        elif g.startswith("PIT:FTG") and k == "BLINDING":
            if g.endswith("T652:10A5"):
                out[i], basis[i] = t652_blind, "F10 / F blinding line (open outline 1B1B)"
            else:
                out[i], basis[i] = pit_blind, "footing-layer blinding line (union under each footing, T-233)"
        elif g.startswith("PIT:FTG") and k.startswith("UNDERLAY_"):
            out[i], basis[i] = underlay_line(D, r)
        elif k == "LIFT_PIT":
            out[i] = ("NO_LINE", "lift-pit walls + void: no CONC.LIFT_PIT_WALL line in V3.0.24 (T-322: 1.100 m3 per m of "
                                 "pit height, pit depth not printed); the void is not soil and owns no line")
        elif k == "NECK":
            out[i], basis[i] = neck_line(D, i, frame)
        elif i in ("STRAP:SB1", "STRAP:SB2", "STRAP:SB3"):
            out[i] = _by_element(D, "STR.CONC.STRAP", f"HL:STRAP_CONCRETE:{i[6:]}:CONCRETE")
            basis[i] = "strap concrete line (Q-74 axis, face to face)"
        elif i == "STRAP:SB3_IN_F3":
            out[i] = _by_element(D, "STR.CONC.STRAP", "HL:STRAP_CONCRETE:SB3:IN_FOOTING:F3")
            basis[i] = "SB3 inside the F3 outline"
        elif i == "STRAP:SB1_IN_F10F":
            out[i] = _by_element(D, "STR.CONC.STRAP", "HL:STRAP_CONCRETE:SB1:IN_FOOTING:F10_F")
            basis[i] = "SB1 inside the open F10 + F outline"
        elif i == "STRAP:BLINDING":
            out[i], basis[i] = strap_blind, "strap blinding line"
        elif i.startswith("GB:") and k == "BLINDING":
            out[i], basis[i] = gb_blind, "ground-beam blinding line (p.13 10 / 30 / 10)"
        elif i.startswith("GB:") and i != "GB:LOWER_ROW_TWO_BEAM_DETAIL":
            run = i[3:]
            if run.startswith(("EXT-MAIN#", "BOUNDARY-UPPER#")):
                run = D["t253"][int(run.split("#")[1])]
            if run not in rm:
                split = [x for x in D["t332"] if x["tie"] == "SPLIT_UNRESOLVED" and f"span {run} " in x["item"]]
                if split and r["value_m3"] is None and r["range_hi"] is None:
                    out[i] = ("NO_LINE", f"SPLIT_UNRESOLVED: {split[0]['tie_reason']} (T-332 {split[0]['face_id']}); "
                                         "the row carries no value (it cannot be bound once until the length per line "
                                         "is settled)")
                    continue
                raise R.Refused(f"{i}: run {run} has no line in the T-332 binding")
            out[i], basis[i] = rm[run], f"run {run} -> line by the T-332 face binding (MERGED 61d5597e)"
        elif i == "GB:LOWER_ROW_TWO_BEAM_DETAIL":
            out[i] = ("NO_LINE", "conditional element (exists only if d > 0.22 m), drawn on no plan (T-205 / T-042 B3)")
        elif i == "BOUNDARY:LOWER_BAND":
            out[i] = _by_element_suffix(D, "STR.CONC.BOUNDARY_WALL", ":BEAM")
            basis[i] = "boundary-wall foundation beam line (Q-28 A PROVISIONAL)"
        elif i == "BOUNDARY:BRICK_BELOW_NG_AND_PADS":
            out[i] = ("NO_LINE", "brick below N.G. and the 130 x 80 x 30 pads: depth and count not printed (p.14, Q-28); "
                                 "no candidate line (named MISSING)")
        elif i in pool:
            out[i], basis[i] = pool[i], "pool shell line (T-183 r2)"
        elif i == "POOL:WATER_SPACE":
            out[i] = ("NO_LINE", "the pool water space is a VOID inside the excavation: displacement, not a material")
        elif i.startswith(("POOL:SCREED", "POOL:MEMBRANE", "POOL:FLOOR_BUILDUP")):
            out[i] = ("NO_LINE", "pool p.7 layer: no pool WP / screed / build-up line in V3.0.24 (T-342: MISSING, "
                                 "lane I T-310 via the T-336 FILL)")
        elif i in ("POOL:BLINDING_AT_MEMBRANE_LINE", "POOL:BLINDING_BEYOND_MEMBRANE"):
            out[i] = ("NO_LINE", "pool blinding: no pool blinding line in V3.0.24 (the four STR.CONC.BLINDING lines are "
                                 "footings, F10 / F, straps, ground beams); MISSING, named")
        else:
            raise R.Refused(f"no binding rule for displacement row {i}")
    return out, basis


SCREED_T, MEMBRANE_T = 0.05, 0.02   # T-206 VERIFIED underlay 0.07 = 5 cm screed + 2 cm membrane (p.13)


def split_underlay(rows):
    """One T-320 UNDERLAY row (0.07) is two physical components with two owner lines (WP.FOUNDATION screed m3,
    membrane m2): split it 5 / 2 by thickness (both linear in the same plan), so each part has ONE owner (R-T347-1)."""
    out = []
    for r in rows:
        if r["kind"] != "UNDERLAY":
            out.append(r)
            continue
        for part, t in (("SCREED", SCREED_T), ("MEMBRANE", MEMBRANE_T)):
            k = t / (SCREED_T + MEMBRANE_T)
            x = dict(r, id=f"{r['id']}:{part}", kind=f"UNDERLAY_{part}")
            for f in ("value_m3", "range_lo", "range_hi", "netted_m3"):
                if x.get(f) is not None:
                    x[f] = round(x[f] * k, 6)
            out.append(x)
    return out


FF_T322 = {  # T-322 MERGED d3bcd9d4: what p.14 prints under the FF raft (the T-320 FF UNDERLAY row was HELD whole)
    "SCREED": {"range_lo": 0.0, "range_hi": 1.035, "status": "HELD",
               "held": "PIT_DEPTH_NOT_PRINTED (below-EG share); screed 20.700 m2 x 0.05 = 1.035 m3 DRAWING-CONFIRMED (T-322)"},
    "MEMBRANE": {"status": "HELD", "held": "MEMBRANE_THICKNESS_NOT_PRINTED (p.14, T-322); area 20.700 m2 DRAWING-CONFIRMED"},
}


def underlay_line(D, r):
    part = r["kind"].split("_")[1]
    g = r["group"]
    if "FF@" in g:
        eid = {"SCREED": "WPF:LIFT_PIT_BASE_SCREED", "MEMBRANE": "WPF:LIFT_PIT_MEMBRANE_FIXED"}[part]
        code = {"SCREED": "WP.FOUNDATION.LIFT_PIT_SCREED", "MEMBRANE": "WP.FOUNDATION.LIFT_PIT_MEMBRANE"}[part]
    else:
        suf = "_1B1B" if "T652" in g else ""
        eid = {"SCREED": "WPF:FOOTING_PROTECTION_SCREED", "MEMBRANE": "WPF:FOOTING_UNDERLAY_MEMBRANE"}[part] + suf
        code = {"SCREED": "WP.FOUNDATION.FOOTING_SCREED", "MEMBRANE": "WP.FOUNDATION.FOOTING_MEMBRANE"}[part]
    unit = "m3" if part == "SCREED" else "m2"
    hits = [l for l in D["cand"]["lines"] if l["item_code"] == code and l["element_id"] == eid and l["unit"] == unit]
    if len(hits) != 1:
        raise R.Refused(f"underlay {r['id']}: {len(hits)} lines {code} {eid} {unit}")
    return hits[0]["line_id"], f"{code} [{unit}] {eid} (T-219 / T-322)"


# ------------------------------------------------------------------ binding + capacity

def over_cause(o):
    """Each line whose quantity is below the displacement (plus above-EG part) the ledger binds to it: the cause."""
    r = o["rows"]
    if r == ["STRAP:SB3_IN_F3"]:
        return ("STALE LINE RANGE: the candidate keeps the T-174 range 0.0295 .. 0.1181 m3; T-230 (merged before "
                "V3.0.8) showed one straight strap has one level, so the excess runs 0.0295 .. 0.2683 (T-233 finding 4, "
                "MERGED): a lane I correction of the held range, never of a released figure",
                "LEDGER_RIGHT (T-230 / T-233 basis); the line's high end understates")
    if r == ["STRAP:BLINDING"]:
        return ("TWO HELD BASES: ledger 0 .. 0.913 m3 (T-233: 9.13 m2 x 0.10, D-15 none printed under straps) vs line "
                "0.3778 .. 0.7719 (ROUTE_G footprint REACH merge window, V3.0.2): both HELD, neither printed",
                "UNRESOLVED (D-15 designer item); the two ranges are kept, the earthworks row carries the wider")
    if r == ["BOUNDARY:LOWER_BAND"]:
        return ("A HELD RANGE AGAINST A SINGLE READING: ledger 5.639 .. 11.033 m3 (Q-28 A PROVISIONAL: section C1 vs "
                "20 x 40, crossing levels at 10 footings) vs line 7.2204 SOURCE_DERIVED (strip length x one schedule "
                "section): the line shows one reading of an open question as a value",
                "UNRESOLVED (Q-28); the line's state is a question for the Lead / Checker (state, not quantity)")
    return ("DEPTH CLASS: T-242 holds D in [0.30, 0.40] (D-34 title / length basis); the T-320 above-EG figure (or the "
            "annex range) takes D 0.40, the PROVISIONAL line the class depth 0.30; below EG both are 0 on the main "
            "house (ZERO_BY_BOUND), so the displacement account does not move",
            "RULE_DIFFERENCE inside a HELD range (D-34); no displacement effect on the main house")


def binding(D):
    frame = footing_frame(D)
    rows = displacement_rows(D)
    netted = net_of_shared(D, rows)
    rows = split_underlay(rows)
    for r in rows:
        if "FF@" in r["group"] and r["kind"].startswith("UNDERLAY_"):
            r.update(FF_T322[r["kind"].split("_")[1]])
            r["source"] = "T-322 MERGED d3bcd9d4 (p.14 lift detail) over T-320 / T-219"
    mp, basis = mapping(D, rows, frame)
    lines = {}
    for lid, l in D["lines"].items():
        v, hi = line_qty(l)
        lines[lid] = {"quantity": hi, "state": l["evidence_state"], "unit": l["unit"]}
    # R-T347-2 in its measured form: rows whose owner line is blank keep their ledger figure, flagged LINE_HELD
    cap_rows = [dict(r, status=("HELD" if lines.get(mp.get(r["id"]) if isinstance(mp.get(r["id"]), str) else None,
                                                     {}).get("quantity") is None else r["status"])) for r in rows]
    out, load = R.bind(cap_rows, lines, mp, strict=False)
    res = []
    for r, (rid, lid, why) in zip(rows, out):
        l = D["lines"].get(lid) if lid else None
        v, hi = line_qty(l) if l else (None, None)
        state = "NO_LINE" if lid is None else ("BOUND_LINE_HELD" if v is None else "BOUND")
        res.append(dict(r, line_id=lid or "", line_item_code=(l or {}).get("item_code", ""),
                        line_state=(l or {}).get("evidence_state", ""), line_measured=v,
                        line_low=(l or {}).get("bounded_low"), line_high=(l or {}).get("bounded_high"),
                        binding=state, basis=basis.get(rid, ""), reason=why))
    per_line = {}
    for x in res:
        if x["line_id"]:
            p = per_line.setdefault(x["line_id"], {"rows": 0, "value_m3": 0.0, "hi_m3": 0.0, "above_eg_m3": 0.0,
                                                    "unvalued_rows": 0})
            p["rows"] += 1
            if D["lines"][x["line_id"]]["unit"] == "m2":      # an area line: carry the plan area (R-T347-2)
                p["unit"] = "m2"
                if x["plan_m2"] is not None and x["status"] not in ("HELD", "CONFLICT"):
                    p["value_m3"] += x["plan_m2"]
                    p["hi_m3"] += x["plan_m2"]
                else:
                    p["unvalued_rows"] += 1
                continue
            if x["value_m3"] is not None:
                p["value_m3"] += x["value_m3"]
                p["hi_m3"] += x["value_m3"]
            elif x["range_hi"] is not None:
                p["hi_m3"] += x["range_hi"]
            else:
                p["unvalued_rows"] += 1
            p["above_eg_m3"] += x["above_eg_m3"]
    for lid, p in per_line.items():
        l = D["lines"][lid]
        v, hi = line_qty(l)
        p.update({k: round(p[k], 6) for k in ("value_m3", "hi_m3", "above_eg_m3")})
        p["line_measured"], p["line_high"], p["line_state"], p["item_code"] = v, l.get("bounded_high"), \
            l["evidence_state"], l["item_code"]
        p["closure_m3"] = None if v is None else round(v - p["value_m3"] - p["above_eg_m3"], 6)
    for o in load["__over__"]:
        o["cause"], o["verdict"] = over_cause(o)
    overs = {o["line_id"]: o for o in load["__over__"]}
    for x in res:
        if x["line_id"] in overs:
            x["binding"] = "BOUND_OVER_LINE"
    return {"frame_mm": frame, "rows": res, "per_line": per_line, "netted": netted, "over": load["__over__"]}


# ------------------------------------------------------------------ neat plans and overlaps (acceptance b)

def plans(D):
    s = D["t170s"]
    beyond = {g: v["beyond_plot_held_m3"] for g, v in D["t320s"]["groups"].items() if g.startswith("PIT:FTG")}
    pits = []
    for p in s["pits"]:
        pits.append({"id": p["id"], "type": p["type"], "outline_handle": p["outline"] or "",
                     "sheet": "ST7757 dxf.dxf FOUNDATION PLAN (S-FOOTINGS / INSERT F); ST7757.pdf p.13 projection 0.10",
                     "footprint_m2": p["footprint_m2"], "neat_plan_m2": p["neat_plan_m2"],
                     "neat_status": p["neat_status"],
                     "beyond_plot_plan_m2": round(beyond.get("PIT:" + p["id"], 0.0) / BLINDING_T, 6),
                     "depth": "AT_LEAST 1.50 below EG +-0.00 (p.9 note 1 'not less than 1.5 m'); founding level "
                              "HELD (p.8 note 12, Q-21 C)" if p["neat_status"] == "DRAWING-CONFIRMED" else
                              "HELD (" + "; ".join(s["held_pits"].get(p["id"], [])) + ")",
                     "held": "; ".join(s["held_pits"].get(p["id"], []))})
    trenches = [{"id": t["id"], "kind": t["kind"], "mark": t.get("mark") or "", "length_m": t["length_m"],
                 "width_m": t["width_m"], "neat_plan_m2": t["neat_plan_m2"], "neat_status": t["neat_status"],
                 "depth_why": t["excavation_why"]} for t in s["trenches"]]
    overlaps = sorted(s["overlaps"], key=lambda o: (o["w_star_m"], o["a"], o["b"]))
    neat = {p["id"]: p["neat_plan_m2"] for p in pits if p["neat_status"] == "DRAWING-CONFIRMED"}
    real = {(o["a"], o["b"]): o["neat_overlap_m2"] for o in overlaps if o["neat_overlap_m2"] > 0}
    net = R.net_plan(neat, real)
    return {"pits": pits, "trenches": trenches, "overlaps": overlaps, "neat_gross_m2": round(sum(neat.values()), 6),
            "neat_net_m2": round(net, 6), "real_overlaps": {f"{a} / {b}": v for (a, b), v in real.items()}}


# ------------------------------------------------------------------ FILL table (acceptance c)

def fill(D, B, P):
    f8 = D["t320s"]["f8_pool"]["neat_in_env_m2"]
    beyond = sum(p["beyond_plot_plan_m2"] for p in P["pits"])
    pits_plan_lo = P["neat_net_m2"] - beyond - f8
    pd = D["t320s"]["pool_decomposition"]
    pool_env_in_plot = D["t320s"]["z1_by_family_m3"]["pool envelope inside the plot (shell + layers + water space)"]
    ext_blind = sum(r["value_m3"] for r in B["rows"] if r["id"].startswith("GB:EXT-MAIN") and r["kind"] == "BLINDING")
    rows = []

    def add(family, zone, parts, status, held, bound_to, source, coef=None, info=""):
        a = R.aggregate(parts)
        row = {"row_id": f"{family}|{zone}", "family": family, "zone": zone,
               "value_m3": a["value"], "lo_m3": a["lo"], "hi_m3": a["hi"], "coef_m3_per_m_d": coef,
               "bound_classes": a["classes"], "status": status, "held_items": held,
               "bound_to_lines": bound_to, "source": source, "info": info}
        R.check_fill_row(row)
        rows.append(row)

    def lines_of(pred):
        return " ".join(sorted({r["line_id"] for r in B["rows"] if r["line_id"] and pred(r)}))

    pit_pred = lambda r: r["group"].startswith("PIT:FTG") and "T652" not in r["group"] and "FF@" not in r["group"]  # noqa
    neck24 = lambda r: r["kind"] == "NECK" and "FF@" not in r["group"] and "T652" not in r["group"]  # noqa
    # ---- B1-02 EXCAVATION
    add("B1-02 EXCAVATION", "Z1-PITS-24 (24 neat footing pits)",
        [R.part("AT_LEAST", lo=pits_plan_lo * FORMATION_MIN_M)], "HELD",
        "formation only a minimum ('not less than 1.5 m', p.9 note 1; Q-21 C: founding level on site): d >= 0 below "
        "-1.50 HELD; working space not printed (UP-EXC-001, OQ-13); pits vs bulk dig over the east block (OQ-13, T-170 "
        f"w*); D-14 pit plan beyond the plot line {beyond:.4f} m2 HELD; F8 neat plan inside the pool envelope "
        f"{f8:.5f} m2 counted once, in the pool zone",
        lines_of(pit_pred), "T-170 neat plans (DXF outlines) net of the real overlaps; T-320 D-14 / F8-pool",
        coef=P["neat_net_m2"],
        info=f"neat net {P['neat_net_m2']:.6f} - beyond plot {beyond:.4f} - F8 in pool {f8:.5f} = {pits_plan_lo:.6f} m2 "
             f"x 1.50 (the printed minimum, a bound); every metre below the limit adds {P['neat_net_m2']:.3f} m3 before "
             "working space")
    add("B1-02 EXCAVATION", "Z1-PIT-FF (lift raft and pit)", [R.part("HELD", held="pit depth")], "HELD",
        "pit floor 'as per lift manufacturer' (p.14, T-204): FF founding level not printed; blinding projection not "
        "printed (T-322, RFI S23); working space", lines_of(lambda r: "FF@" in r["group"]),
        "T-322 / T-170", info="raft footprint 4.60 x 4.50 = 20.700 m2 (DRAWING-CONFIRMED plan, no depth)")
    add("B1-02 EXCAVATION", "Z1-PIT-F10F (open outline 1B1B)", [R.part("HELD", held="plan")], "HELD",
        "footing plan not established (Q-31 C designer item: one open outline, two tags F10 and F); formation; working "
        "space", lines_of(lambda r: "T652" in r["group"]), "T-170 held_pits")
    add("B1-02 EXCAVATION", "Z1-POOL (pool envelope to the printed -1.50)",
        [R.part("AT_LEAST", lo=pool_env_in_plot)], "HELD",
        "blinding projection beyond the membrane line not printed (T-183 B, >= 1.222); working space; envelope part "
        "beyond the plot line 0.5486 m3 HELD (F-T320-05)", lines_of(lambda r: r["group"] == "PIT:POOL"),
        "T-183 r2 / T-320 pool envelope 12.216759 m2 x 1.50 (printed formation)",
        info="neat envelope inside the plot 17.776576 m3 is a value from a printed level; held parts only add")
    add("B1-02 EXCAVATION", "Z1-TRENCH-EXT-GB-MAIN (17 runs, cut for the blinding only)",
        [R.part("HELD", held="ends")], "HELD",
        "working space not printed; trench ends lie over the footing pits (runs are face to face between necks): the "
        "pit / trench overlap is not netted (positions of run ends against pit outlines not in the inputs, T-170 s.8)",
        lines_of(lambda r: r["id"].startswith("GB:EXT-MAIN")),
        "T-253 Gate A (beam bottom on the outer N.G. +-0.00) / p.13 '10 / 30 / 10'",
        info=f"neat cut L x 0.50 x 0.10 = {ext_blind:.5f} m3 = the blinding itself (an upper part before the pit "
             "overlap, a lower part before the working space: neither bound holds alone)")
    zb = [r for r in B["rows"] if r["status"] == "ZERO_BY_BOUND" and r["kind"] == "GROUND_BEAM"]
    add("B1-02 EXCAVATION", f"Z1-TRENCH-INT-GB-MAIN-ZERO ({len(zb)} runs wholly above EG)",
        [R.part("ZERO_BY_BOUND", held="GB top +0.95 >= D + 0.10 above EG")], "ZERO_BY_BOUND",
        "condition: b_wet <= 0.30 m under a wet floor (dry b 0.05, T-214); else the run is re-measured",
        lines_of(lambda r: r["status"] == "ZERO_BY_BOUND"), "T-242 / T-320 F-T320-04")
    add("B1-02 EXCAVATION", "Z1-TRENCH-INT-GB-MAIN-D33 (sections not printed)", [R.part("HELD", held="D-33")], "HELD",
        "D-33: section of a beam receiving another beam not printed (zero below EG while D <= 0.85)",
        lines_of(lambda r: r["kind"] == "GROUND_BEAM" and "zero below EG while" in r["info"]),
        "T-242 / T-253 s.5")
    add("B1-02 EXCAVATION", "Z1-TRENCH-ANNEX (interior D-34 / D-33, exterior D-35)", [R.part("HELD", held="D-35")],
        "HELD", "annex GB top +0.25: soffits below EG on D-34 ranges; D-33 no section; exterior D-35 annex CONFLICT "
                "(reading L 0.25 vs reading S deeper); trench / pit overlap at the annex footings",
        lines_of(lambda r: r["kind"] == "GROUND_BEAM" and ("D-35" in r["held"] or "D-34" in r["held"]
                                                            or "if p.13 applied" in r["info"])),
        "T-242 / T-253 s.3")
    add("B1-02 EXCAVATION", "Z1-TRENCH-COURT (3 runs)", [R.part("HELD", held="no section")], "HELD",
        "court runs: no printed section (T-253 s.4)", lines_of(lambda r: "court" in r["held"].lower()), "T-253 s.4")
    add("B1-02 EXCAVATION", "Z1-TRENCH-STRAPS (SB1 / SB2 / SB3)", [R.part("HELD", held="strap soffit")], "HELD",
        "strap soffit and blinding not printed (D-15); no blinding projection under straps; working space",
        lines_of(lambda r: r["group"] == "TRENCH:STRAPS"), "T-170 trenches / T-233",
        info="strap footprint 7.889 m2 (T-170), displacement 3.3905 m3 DRAWING-CONFIRMED")
    add("B1-02 EXCAVATION", "Z1-TRENCH-BOUNDARY (p.14 typical boundary wall)", [R.part("HELD", held="Q-28")], "HELD",
        "'AS PER EXCAVATION DEPTH BELOW N.G. LEVEL' (p.14): depth not printed; lower band section / levels Q-28 A "
        "PROVISIONAL; pads count not printed", lines_of(lambda r: r["group"] == "TRENCH:BOUNDARY"), "T-253 / T-233",
        info="upper G.B at N.G. 44.07 m x 0.20 x 0.40 = 3.5256 m3 lies wholly below EG (displacement only)")
    add("B1-02 EXCAVATION", "Z1-LOWER-GB-ROW (p.13 two-beam detail)", [R.part("HELD", held="conditional")], "HELD",
        "exists only if 2.28 + d > 2.50 (d > 0.22 m); drawn on no plan", "", "T-205 / T-042 B3")
    # ---- B1-03 BACKFILL = excavation - displacement (per zone)
    disp24 = sum(r["value_m3"] for r in B["rows"] if pit_pred(r) and r["kind"] in ("BLINDING", "UNDERLAY", "FOOTING")
                 and r["value_m3"] is not None)
    add("B1-03 BACKFILL", "Z1-PITS-24", [R.part("HELD", held="excavation held")], "HELD",
        "excavation HELD (formation, working space, pit vs bulk); neck C8 10E0 CONFLICT; SB3 in F3 HELD; annex ground "
        "beams that dip below EG over a pit (D-34 / D-33 / D-35) have no upper bound, so no lower bound of the backfill "
        "is proved", lines_of(lambda r: pit_pred(r) or neck24(r)),
        "T-320 R-BACKFILL-DISP-1 (backfill = excavated - displacement below EG)",
        coef=round(P["neat_net_m2"] - D["t320s"]["necks"]["coef_m3_per_m"], 6),
        info=f"established displacement in the 24 pits (blinding + underlay + footings, net, incl. D-14) "
             f"{disp24:.6f} m3 + necks >= 4.3278 at d = 0 (+ 4.86 per m); backfill grows by the coefficient per metre "
             "of d (excavation 129.234 - necks 4.86)")
    add("B1-03 BACKFILL", "Z1-POOL", [R.part("HELD", held="projection")], "HELD",
        "inside the neat envelope everything is displacement (shell, p.7 layers, water space): backfill only in the "
        "unprinted blinding projection and the working space", lines_of(lambda r: r["group"] == "PIT:POOL"),
        "T-320 pool decomposition (closes to 1e-6)")
    add("B1-03 BACKFILL", "Z1-TRENCH-EXT-GB-MAIN", [R.part("HELD", held="working space")], "HELD",
        "the neat cut is filled by the blinding (2.79956 = 2.79956 m3): backfill only in the working space (not "
        "printed)", lines_of(lambda r: r["id"].startswith("GB:EXT-MAIN")), "T-253 / T-320")
    add("B1-03 BACKFILL", "Z1-OTHER-TRENCHES (annex, court, straps, boundary, D-33)", [R.part("HELD", held="see B1-02")],
        "HELD", "as their excavation rows (D-33 / D-34 / D-35, court section, D-15, Q-28)", "", "T-320")
    add("B1-03 BACKFILL", "Z2 (fill above EG under the GF ground slab, from excavated soil)",
        [R.part("HELD", held="Z2 not formed")], "HELD",
        "placed fill EG +-0.00 -> slab underside (+0.85 dry, T-214): enclosed plan, wet-floor b (T-221) and the D-33 / "
        "D-34 beam sections not established; a separate zone row, never merged into Z1 (the ground beams above EG "
        "and the interior blinding 15.96 + m3 displace it, not Z1)", "",
        "T-320 s.1 zone Z2; p.13 'Well graded clean compacted fill from excavation material'")
    # ---- B1-04 DISPOSAL
    add("B1-04 DISPOSAL", "ALL ZONES", [R.part("HELD", held="bulking")], "HELD",
        "disposal = excavated - backfill re-used - Z2 fill re-used (the drawing prints the fill 'from excavation "
        "material'); bulking factor: no answered rule (Q-21 C lists disposal separately, gives none); Z2 not formed; "
        "excavation HELD", "", "T-320 s.1 / R-T347-5",
        info="in situ, before the Z2 re-use, disposal equals the displacement below EG (excavation - backfill); "
             "the Z2 draw can exceed it (import) or not: no bound in either direction")
    return rows


# ------------------------------------------------------------------ changes since T-320 (acceptance a)

def changes(D, B):
    L = D["lines"]
    get = lambda lid: L.get(lid) or {}  # noqa
    fflid = next(r["line_id"] for r in B["rows"] if r["id"].endswith("FF@136342,43148:8e679c:FOOTING"))
    blid = next(r["line_id"] for r in B["rows"] if r["id"].endswith("FF@136342,43148:8e679c:BLINDING"))
    walls = get(next(r["line_id"] for r in B["rows"] if r["id"] == "POOL:WALLS"))
    return [
        {"element": "FF raft (lift base)", "t320": "FOOTING range 0 .. 11.385 m3 below EG (HELD: pit depth)",
         "now": f"line {fflid} {get(fflid).get('evidence_state')} {get(fflid).get('measured_net')} m3; raft 4.60 x 4.50 "
                f"x 0.55 = 11.385 DRAWING-CONFIRMED (T-322); the below-EG share stays HELD (pit floor not printed)",
         "delta_m3": "0 on the displacement account (range unchanged); the line volume is confirmed",
         "cause": "T-322 MERGED d3bcd9d4 (FF outline 1B2B = schedule FF 460 / 450 / 55)"},
        {"element": "FF blinding", "t320": "range 0 .. 2.256 m3 (F-T320-03: T-233 2.256 vs T-170 HELD)",
         "now": f"HELD AT_LEAST 2.070 m3 (4.60 x 4.50 x 0.10, projection not printed on p.14); line {blid} "
                f"{get(blid).get('evidence_state')} {get(blid).get('measured_net')} carries the footing layer; the "
                "Checker downgrade DG-3521554d2fd011b9 (V3.0.22) holds the FF part",
         "delta_m3": "low end 0 -> 2.070 (a bound), high end 2.256 no longer supported (the +0.10 projection is the "
                     "p.13 typical, INHERITED for FF only)",
         "cause": "T-322 MERGED (F-T320-03 settled) + DG-3521554d"},
        {"element": "Pool envelope / pool D outline", "t320": "18.3251 m3 = 12.216759 m2 x 1.50; water space 7.2920",
         "now": f"AGREES: water face 8.578838 m2 (T-342 hand D 8.578838) x 0.85 = 7.292012; walls line "
                f"{walls.get('measured_net')} m3 = 2.121053 below EG + 0.707018 above",
         "delta_m3": "0.000", "cause": "T-342 MERGED (pool is a D): T-320 already used the D"},
        {"element": "F12 pit (outline 1ABF)", "t320": "pit 12.6513 m3 (blinding 1.564, underlay 0.9856, footing 9.856, "
                                                       "necks 0.0945 + 0.1512)",
         "now": "AGREES: F12 4.40 x 3.20 x 0.70 = 9.856 on its V3.0.24 line; T-332 re-read 1ABF 4.40 x 3.20",
         "delta_m3": "0.000", "cause": "T-332 MERGED (AGREES row)"},
        {"element": "Parapet family (T-319)", "t320": "not in the account",
         "now": "NOT BURIED: the roof / terrace parapets stand above the slabs; no displacement row, no binding",
         "delta_m3": "0.000", "cause": "T-319 MERGED (V3.0.23)"},
    ]


# ------------------------------------------------------------------ build / write

def build():
    D = load()
    B = binding(D)
    P = plans(D)
    F = fill(D, B, P)
    C = changes(D, B)
    nl = [r for r in B["rows"] if r["binding"] == "NO_LINE"]
    summ = {
        "schema": "T347_SUMMARY_V1", "candidate": D["cand"]["candidate"],
        "candidate_lines_json_sha256": D["cand"]["candidate_lines_json_sha256"],
        "lines_in_candidate": D["cand"]["lines_in_candidate"],
        "earthworks_lines_in_candidate": D["cand"]["earthworks_lines_in_candidate"],
        "frame_mm": B["frame_mm"], "rows": len(B["rows"]),
        "bound": sum(r["binding"] == "BOUND" for r in B["rows"]),
        "bound_line_held": sum(r["binding"] == "BOUND_LINE_HELD" for r in B["rows"]),
        "no_line": len(nl), "no_line_ids": [r["id"] for r in nl],
        "double_count": 0, "netted_to_FN_m3": B["netted"], "over_line_findings": B["over"],
        "bound_over_line": sum(r["binding"] == "BOUND_OVER_LINE" for r in B["rows"]),
        "per_line": B["per_line"], "neat_gross_m2": P["neat_gross_m2"], "neat_net_m2": P["neat_net_m2"],
        "real_overlaps_m2": P["real_overlaps"], "overlap_pairs": len(P["overlaps"]),
        "fill_rows": len(F), "fill_valued": sum(r["value_m3"] is not None for r in F),
        "changes_since_t320": C,
        "z1_established_m3_t320": D["t320s"]["z1_established_m3"],
    }
    return D, B, P, F, summ


def _w(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else (f"{r[k]:.6f}" if isinstance(r[k], float) else r[k])) for k in cols})
    return buf.getvalue()


BIND_COLS = ["id", "group", "kind", "plan_m2", "value_m3", "range_lo", "range_hi", "coef", "above_eg_m3", "netted_m3",
             "status", "held", "binding", "line_id", "line_item_code", "line_state", "line_measured", "line_low",
             "line_high", "basis", "reason", "source"]
FILL_COLS = ["row_id", "family", "zone", "value_m3", "lo_m3", "hi_m3", "coef_m3_per_m_d", "bound_classes", "status",
             "held_items", "bound_to_lines", "source", "info"]
PIT_COLS = ["id", "type", "outline_handle", "footprint_m2", "neat_plan_m2", "neat_status", "beyond_plot_plan_m2",
            "depth", "held", "sheet"]
OVL_COLS = ["a", "b", "neat_overlap_m2", "footing_overlap_m2", "w_star_m"]


def fill_csv(F):
    for r in F:
        R.check_fill_row(r)
    out = _w(F, FILL_COLS)
    for r in csv.DictReader(io.StringIO(out)):        # re-check what was printed (the T-332 lesson)
        R.check_fill_row({k: (v if v != "" else None) for k, v in r.items()})
    return out


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    D, B, P, F, summ = build()
    files = {"BINDING_T347.csv": _w(B["rows"], BIND_COLS), "FILL_T350_T347.csv": fill_csv(F),
             "PITS_T347.csv": _w(P["pits"], PIT_COLS), "OVERLAPS_T347.csv": _w(P["overlaps"], OVL_COLS),
             "summary_t347.json": json.dumps(summ, indent=1, sort_keys=True) + "\n"}
    if "--write" in a:
        for n, t in files.items():
            (HERE / n).write_text(t, encoding="utf-8")
    print(f"rows {summ['rows']}: bound {summ['bound']}, line held {summ['bound_line_held']}, no line {summ['no_line']}; "
          f"frame {summ['frame_mm']}; neat {summ['neat_gross_m2']} -> {summ['neat_net_m2']} m2; FILL {summ['fill_rows']} "
          f"rows, {summ['fill_valued']} valued")
    return files


if __name__ == "__main__":
    main()
