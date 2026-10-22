"""T-151: the three checker-merged steel hand ledgers of the development villa, typed into the project inputs of
ARCH_TAKEOFF_V3.0.3 (URBAN_V303_STEEL_LEDGERS_V1). Research code, stdlib only; it reads the ledgers as committed and
changes none of their quantities. What it decides, and why (every choice cites its source):

  * a ledger RELEASED row -> RELEASED with schedule_row PRINTED (the row cites its printed schedule / detail); the
    checker conditions of T-149 (2026-10-21 22:40): the word RELEASED means DRAWING-CONFIRMED / NOT RELEASED, and
    UNQUANTIFIED means UNKNOWN; VERIFIED only on the rows a checker run re-measured (CHECKER_REMEASURED below);
  * a held row with a printed range ("a .. b", or readings A / B / C [/ B upper path]) -> HELD_RANGE min .. max of
    the readings (the ledger's own figures; Q-71 open); a held row with one defined figure -> HELD_DEFINED (shown,
    never added); a "minimum only" figure -> HELD_LOWER_BOUND; no figure -> UNQUANTIFIED;
  * T-138 ground beams held over several p.13 section candidates -> ONE record per span over its candidates (the CSV
    prints the first candidate's bars only): min .. max of the defined candidates' kg per metre x the span; a span
    with a candidate that has no project detail (concentrated load) -> UNQUANTIFIED with the defined range as info;
  * straps: owner Q-74 (strap length basis) is OPEN and T-141 (MERGED 6ab7719) holds every strap length, so every
    strap bar and link line is HELD over the three Q-74 readings (A axis face to face, B projection gap, C footing
    centre to centre, from T141_STRAPS.csv); SB2 also over its two schedule rows (issued 100 x 50 20 T18 / 10 T16 and
    the off-sheet 80 x 50 10 T18 / 10 T18, T-138 finding 5, designer D-38);
  * T-149 beams held over candidate marks (HELD_CANDIDATE) -> ONE record per span over its candidates (sum of each
    candidate's components; = T149_SUMMARY candidates);
  * the T-149 checker condition: the end-support top bars that the p.11 / p.12 typical details draw ('0.3 Ln2') and
    no schedule row sizes -> one UNQUANTIFIED record per end of every continuous beam, never 0.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "research"

T148 = {"file": "research/agents_t148/T148_COLUMNS.csv", "task": "T-148 (column steel by bar population)",
        "merge_commit": "8a22eec", "checker_run": "verifier 2026-10-21 18:40 UTC run session_01PFZuWjmnbv17RtevaXGDvs "
        "(MERGED 8a22eec; re-counted GF C11 99.556, 1F C9 79.644, GF C8 85.333 + turn 12.642 kg, 0.0 %)"}
T138 = {"file": "research/agents_t138/T138_MEMBERS.csv", "task": "T-138 r2 (ground-beam and strap steel) + T-141 "
        "(strap lengths HELD, MERGED 6ab7719)", "merge_commit": "0dec24c",
        "checker_run": "verifier 2026-10-21 05:05 UTC run session_015BSkBg12u1VsgNaLdDXPEr (MERGED 0dec24c; note 9 "
        "read on p.8; the two runs over 12 m re-measured); T-141 verifier 2026-10-21 18:40 UTC (MERGED 6ab7719)"}
T149 = {"file": "research/agents_t149/T149_BEAMS.csv", "task": "T-149 (beam steel by bar population)",
        "merge_commit": "4972ac5", "checker_run": "verifier 2026-10-21 22:40 UTC run session_016zmJg8i5ABUuzKA9Wf971C "
        "(MERGED 4972ac5; re-measured GF B22 265.585 kg 0.0 %, GF CB7 98.714 vs 98.703 kg +0.01 %, GF B2 end span "
        "16.296 vs 16.312 kg -0.1 %)"}
T141_STRAPS = "research/agents_t141/T141_STRAPS.csv"
# rows a checker run re-measured by hand (element, component) -> run; everything else RELEASED is DRAWING-CONFIRMED
CHECKER_REMEASURED = {
    ("COL-GF-19", "MAIN BARS net"): "verifier 2026-10-21 18:40 UTC (99.556 kg, 0.0 %)",
    ("COL-1F-41", "MAIN BARS net"): "verifier 2026-10-21 18:40 UTC (79.644 kg, 0.0 %)",
    ("COL-GF-13", "MAIN BARS net"): "verifier 2026-10-21 18:40 UTC (85.333 kg, 0.0 %)",
    ("COL-GF-13", "TURN EXTRA 4 ø 16 (p.15)"): "verifier 2026-10-21 18:40 UTC (12.642 kg, 0.0 %)",
    ("BM-GF-045", "*"): "verifier 2026-10-21 22:40 UTC (GF B22 265.585 kg, 0.0 %)",
    ("BM-GF-013", "*"): "verifier 2026-10-21 22:40 UTC (GF CB7 98.714 vs 98.703 kg, +0.01 %)",
    ("BM-GF-028", "*"): "verifier 2026-10-21 22:40 UTC (GF B2 end span 16.296 vs 16.312 kg, -0.1 %)",
}
SB2_ALT = {"TOP": (10, 18), "BOTTOM": (10, 18)}      # off-sheet 80 x 50 insert (T-138 finding 5), held as a reading
D4_CLOSED = {   # T-155 r2 (MERGED 15fd913, checker 2026-10-21 23:53): ends drawn closed
    "F12": "structural set p.9 footing schedule closed box symbol; p.13 typical footing callout 'Boxed bars'",
    "F13": "structural set p.9 footing schedule closed box symbol; p.13 typical footing callout 'Boxed bars'",
    "F14": "structural set p.9 footing schedule closed box symbol; p.13 typical footing callout 'Boxed bars'",
    "FF": "structural set p.9 footing schedule closed box symbol; p.14 detail of footing FF"}
# the five undrawn columns of V3.0.1 (their steel leaves with their concrete): found from the V3.0.1 scope log in the run


def kgm(d):
    return d * d / 162.0


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def rows(p):
    with open(ROOT / p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def nums(s):
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", str(s))]


def readings(s):
    """'A 11.522 / B 12.023 / C 11.271' or '26.428 / 27.142 / 25.999' -> dict"""
    s = str(s)
    m = re.findall(r"([A-C])\s+(-?\d+(?:\.\d+)?)", s)
    if m:
        return {k: float(v) for k, v in m}
    v = [float(x) for x in s.split("/") if f(x.strip()) is not None]
    return dict(zip("ABC", v))


def dia_of(s):
    m = re.search(r"ø\s*(\d+)|T\s*(\d+)", str(s))
    return float(next(g for g in m.groups() if g)) if m else None


def rec(element, floor, mark, component, state, *, kg=None, low=None, high=None, reasons=(), printed=None,
        schedule_row=None, dia=None, count=None, length=None, readings_=None, part=None, verified_by=None,
        range_basis=None, info=None):
    r = {"element": element, "floor": floor, "mark": mark, "component": component, "state": state, "kg": kg,
         "low": low, "high": high, "reasons": [x for x in reasons if x], "printed": printed,
         "schedule_row": schedule_row, "dia_mm": dia, "count": count, "length_m": length, "readings": readings_,
         "part": part, "verified_by": verified_by, "range_basis": range_basis}
    if info:
        r["info"] = info
    return {k: v for k, v in r.items() if v is not None}


def verified(el, comp):
    return CHECKER_REMEASURED.get((el, comp)) or CHECKER_REMEASURED.get((el, "*"))


# ================================================================================================ T-148 columns
def columns():
    out = []
    for x in rows(T148["file"]):
        el, fl, comp, st = x["id"], x["storey"], x["component"], x["status"]
        why = [x.get("cause")]
        printed = f"{x['reading']}; {x['length_basis']}".strip("; ")
        common = dict(printed=printed, dia=dia_of(x["reading"]), count=f(x["count"]), length=f(x["length_m"]))
        if st == "RELEASED":
            out.append(rec(el, fl, x["mark"], comp, "RELEASED", kg=f(x["kg"]), schedule_row="PRINTED",
                           verified_by=verified(el, comp), **common))
        elif st == "HELD" and "/" in x["kg"]:
            rd = readings(x["kg"])
            out.append(rec(el, fl, x["mark"], comp, "HELD_RANGE", low=min(rd.values()), high=max(rd.values()),
                           readings_=rd, reasons=why, range_basis="readings A / B / C (owner Q-71 open), min .. max",
                           **common))
        elif st == "HELD" and x["kg_hi"]:
            out.append(rec(el, fl, x["mark"], comp, "HELD_RANGE", low=f(x["kg"]), high=f(x["kg_hi"]), reasons=why,
                           range_basis="40 d .. 70 d (p.8 note 9, zone not printed)", **common))
        elif st == "HELD" and x["kg"]:
            out.append(rec(el, fl, x["mark"], comp, "HELD_DEFINED", kg=f(x["kg"]), reasons=why, **common))
        else:
            out.append(rec(el, fl, x["mark"], comp, "UNQUANTIFIED", reasons=why or ["not quantified"], **common))
    return out


# ================================================================================================ T-138 ground system
def _t138():
    spec = importlib.util.spec_from_file_location("t138_hand_ledger", RES / "agents_t138" / "t138_hand_ledger.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ground_system():
    T = _t138()
    straps = {r["mark"]: r for r in rows(T141_STRAPS)}
    out, seen_long = [], set()
    for x in rows(T138["file"]):
        el, comp, st, fam = x["member"], x["component"], x["status"], x["family"]
        why = [st.split(":", 1)[1].strip() if ":" in st else st]
        printed = f"{x['detail']}; {x['length_basis']}; {x['note']}".strip("; ")
        common = dict(printed=printed, dia=f(x["dia_mm"]), length=f(x["length_m"]))
        if fam == "STRAP_BEAM":
            s = straps[el]
            L = {"A": float(s["axis_face_to_face_m"]), "B": float(s["projection_gap_m"]),
                 "C": float(s["footing_centre_to_centre_m"])}
            q74 = ("owner Q-74 open (strap length basis): readings A axis face to face {A:.4f} m, B projection gap "
                   "{B:.4f} m, C footing centre to centre {C:.4f} m (T-141 MERGED 6ab7719 holds every strap)"
                   ).format(**L)
            if comp in ("TOP", "BOTTOM"):
                n, d = int(x["count"]), float(x["dia_mm"])
                opts = {k: n * kgm(d) * v for k, v in L.items()}
                basis = "Q-74 readings A / B / C x the printed row"
                extra = []
                if el == "SB2":
                    n2, d2 = SB2_ALT[comp]
                    opts.update({f"{k}_80x50": n2 * kgm(d2) * v for k, v in L.items()})
                    basis += " (issued 100 x 50 row and off-sheet 80 x 50 row, designer D-38)"
                    extra = ["SB2 schedule rows conflict: issued 100 x 50 vs off-sheet 80 x 50 (designer D-38)"]
                hand = f(x["kg"]) or f(x["held_kg"])
                assert abs(hand - n * kgm(d) * float(x["length_m"])) < 0.01, (el, comp)
                out.append(rec(el, "FOUNDATION", el, comp, "HELD_RANGE", low=min(opts.values()),
                               high=max(opts.values()), readings_={k: round(v, 3) for k, v in opts.items()},
                               reasons=[q74] + extra, range_basis=basis, count=n, **common))
            elif comp.startswith("STIRRUP"):
                rate = nums(comp)[0]
                path = float(x["length_m"])
                dl = float(x["dia_mm"])
                rd = {}
                for k, v in L.items():
                    c = rate * v
                    a = math.ceil(c - 1e-9)
                    rd.update({f"{k}:A": a * path * kgm(dl), f"{k}:B": (a + 1) * path * kgm(dl),
                               f"{k}:C": c * path * kgm(dl)})
                hrd = readings(x["held_kg"])
                assert abs(rd["A:A"] - hrd["A"]) < 0.01 and abs(rd["A:B"] - hrd["B"]) < 0.01, (el, rd, hrd)
                out.append(rec(el, "FOUNDATION", el, comp, "HELD_RANGE", low=min(rd.values()), high=max(rd.values()),
                               readings_={k: round(v, 3) for k, v in rd.items()},
                               reasons=["count owner Q-71 open (A ceil, B A + 1, C fractional)", q74] + why,
                               range_basis="Q-71 readings x Q-74 lengths, min .. max", **common))
            elif ".." in x["held_kg"] and "information only" in x["held_kg"]:
                lo, hi = nums(x["held_kg"])[:2]
                out.append(rec(el, "FOUNDATION", el, comp, "UNQUANTIFIED", reasons=why + [q74],
                               info={"information_only_kg": [lo, hi]}, **common))
            else:
                lo, hi = nums(x["held_kg"])[:2]
                out.append(rec(el, "FOUNDATION", el, comp, "HELD_RANGE", low=lo, high=hi, reasons=why,
                               range_basis="40 d .. 70 d (p.8 note 9, zone not printed)", **common))
            continue
        # ground beams
        if st.startswith("RELEASED"):
            out.append(rec(el, "FOUNDATION", None, comp, "RELEASED", kg=f(x["kg"]), schedule_row="PRINTED",
                           count=f(x["count"]), verified_by=verified(el, comp),
                           **dict(common, printed=f"structural set p.13 ground-beam section {x['detail']}; "
                                                  f"{x['length_basis']}; {x['note']}".strip("; "))))
        elif st == "HELD" and x["held_kg"] and comp in ("TOP", "BOTTOM", "BOTTOM_ROW_1", "BOTTOM_ROW_2"):
            # one record per span over its p.13 candidates (the CSV prints the first candidate's bars only)
            if el in seen_long:
                continue
            seen_long.add(el)
            cands = x["detail"].split("/")
            Ls = float(x["length_m"])
            defined = [c for c in cands if T.DETAILS.get(c)]
            vals = {c: T.per_metre(c) * Ls for c in defined}
            reasons = [f"p.13 section candidates {'/'.join(cands)} (designer D-33 / D-34); {x['note']}".strip("; ")]
            if len(defined) == len(cands):
                out.append(rec(el, "FOUNDATION", None, "LONGITUDINAL (section candidates)", "HELD_RANGE",
                               low=min(vals.values()), high=max(vals.values()),
                               readings_={c: round(v, 3) for c, v in vals.items()}, reasons=reasons,
                               range_basis="min .. max of the defined p.13 candidates x the span", length=Ls,
                               printed=printed))
            else:
                out.append(rec(el, "FOUNDATION", None, "LONGITUDINAL (section candidates)", "UNQUANTIFIED",
                               reasons=reasons + ["a candidate (concentrated load) has no project detail"],
                               info={"defined_candidates_kg": {c: round(v, 3) for c, v in vals.items()}},
                               length=Ls, printed=printed))
        elif st == "HELD" and x["held_kg"]:
            out.append(rec(el, "FOUNDATION", None, comp, "HELD_DEFINED", kg=f(x["held_kg"]), reasons=why, **common))
        elif x["held_kg"] and ".." in x["held_kg"]:
            lo, hi = nums(x["held_kg"])[:2]
            out.append(rec(el, "FOUNDATION", None, comp, "HELD_RANGE", low=lo, high=hi, reasons=why,
                           range_basis="40 d .. 70 d (p.8 note 9, zone not printed)" if "note 9" in st
                           else "ledger range", **common))
        elif x["held_kg"] and "/" in x["held_kg"]:
            rd = readings(x["held_kg"])
            out.append(rec(el, "FOUNDATION", None, comp, "HELD_RANGE", low=min(rd.values()), high=max(rd.values()),
                           readings_=rd, reasons=why, range_basis="readings A / B (owner Q-71 open), min .. max",
                           **common))
        else:
            out.append(rec(el, "FOUNDATION", None, comp, "UNQUANTIFIED", reasons=why, **common))
    return out


# ================================================================================================ T-149 beams
def beams():
    out, cand, cmarks = [], {}, {}
    cont = {}
    for x in rows(T149["file"]):
        el = f"{x['member_id']}:{x['row_id']}" + (f":S{x['span'].replace('/', 'of').replace(' ', '')}"
                                                  if x["span"] else "")
        comp, st, fl = x["component"], x["state"], x["floor"]
        if x["kind"] == "continuous":
            cont.setdefault((fl, x["member_id"]), x["mark"])
        why = [x.get("cause"), x.get("note")]
        printed = x.get("note") or None
        common = dict(dia=f(x["dia"]), count=f(x["count"]), length=f(x["length_m"]), printed=printed)
        rd = {k: f(x[f"kg_{k}"]) for k in ("A", "B", "C", "B_upper") if f(x[f"kg_{k}"]) is not None}
        if "HELD_CANDIDATE" in (st, x["parent"]):
            # a member held over candidate marks: every component over its candidates (a candidate without the
            # component counts 0), one record per member and component
            cm, mk = x["cand"].split("|", 1)
            cmarks.setdefault(cm, set()).add(mk)
            if rd:
                lo, hi, lb = min(rd.values()), max(rd.values()), False
            elif x["kg_hi"]:
                lo, hi, lb = f(x["kg"]), f(x["kg_hi"]), False
            else:
                lo, hi, lb = f(x["kg"]), f(x["kg"]), "minimum" in (x["bars"] + x["note"])
            c = cand.setdefault((cm, comp), {"floor": fl, "v": {}, "lb": False, "why": x.get("cause")})
            o = c["v"].get(mk, (0.0, 0.0))
            c["v"][mk] = (o[0] + (lo or 0.0), o[1] + (hi or 0.0))
            c["lb"] = c["lb"] or lb
            continue
        if st == "RELEASED":
            out.append(rec(el, fl, x["mark"], comp, "RELEASED", kg=f(x["kg"]), schedule_row="PRINTED",
                           verified_by=verified(x["member_id"], comp), **common))
        elif st == "HELD_RANGE" and rd:
            out.append(rec(el, fl, x["mark"], comp, "HELD_RANGE", low=min(rd.values()), high=max(rd.values()),
                           readings_=rd, reasons=why, range_basis="readings A / B / C / B upper path (owner Q-71 "
                           "open), min .. max", **common))
        elif st == "HELD_RANGE" and x["kg_hi"]:
            out.append(rec(el, fl, x["mark"], comp, "HELD_RANGE", low=f(x["kg"]), high=f(x["kg_hi"]), reasons=why,
                           range_basis="ledger range", **common))
        elif st == "HELD_RANGE" and "minimum" in (x["bars"] + x["note"]):
            out.append(rec(el, fl, x["mark"], comp, "HELD_LOWER_BOUND", low=f(x["kg"]), reasons=why, **common))
        elif st in ("HELD_RANGE", "HELD_DEFINED") and x["kg"]:
            out.append(rec(el, fl, x["mark"], comp, "HELD_DEFINED", kg=f(x["kg"]), reasons=why, **common))
        else:
            out.append(rec(el, fl, x["mark"], comp, "UNQUANTIFIED", reasons=[w for w in why if w] or ["not printed"],
                           **common))
    for (cm, comp), c in sorted(cand.items()):
        v = {mk: c["v"].get(mk, (0.0, 0.0)) for mk in sorted(cmarks[cm])}
        lo, hi = min(a for a, _ in v.values()), max(b for _, b in v.values())
        why = [c["why"], "held over the candidate marks " + "/".join(sorted(v)) + " (a candidate without this "
               "component counts 0)"]
        rdg = {k: [round(a, 3), round(b, 3)] for k, (a, b) in v.items()}
        if c["lb"]:
            out.append(rec(cm, c["floor"], "/".join(sorted(v)), comp + " (candidate marks)", "HELD_LOWER_BOUND",
                           low=lo, reasons=why, readings_=rdg))
        else:
            out.append(rec(cm, c["floor"], "/".join(sorted(v)), comp + " (candidate marks)", "HELD_RANGE", low=lo,
                           high=hi, reasons=why, readings_=rdg, range_basis="min .. max over the candidate marks"))
    for (fl, mid), mark in sorted(cont.items()):
        for part in ("END_1", "END_2"):
            out.append(rec(mid, fl, mark, "END-SUPPORT TOP BARS (typical detail '0.3 Ln2')", "UNQUANTIFIED",
                           part=part, reasons=["the p.11 / p.12 typical details draw end-support top bars "
                                               "('0.3 Ln2') that no schedule row sizes: UNKNOWN, never 0 "
                                               "(checker condition 2026-10-21 22:40)"]))
    return out


def totals(recs):
    t = {"released": 0.0, "held_low": 0.0, "held_high": 0.0, "held_defined": 0.0, "held_lower_bound": 0.0,
         "unquantified": 0, "lines": len(recs)}
    for r in recs:
        s = r["state"]
        if s == "RELEASED":
            t["released"] += r["kg"]
        elif s == "HELD_RANGE":
            t["held_low"] += r["low"]
            t["held_high"] += r["high"]
        elif s == "HELD_DEFINED":
            t["held_defined"] += r["kg"]
        elif s == "HELD_LOWER_BOUND":
            t["held_lower_bound"] += r["low"]
        else:
            t["unquantified"] += 1
    return {k: round(v, 6) if isinstance(v, float) else v for k, v in t.items()}


def inputs(project):
    c, g, b = columns(), ground_system(), beams()
    led = []
    for piece, src, scope, recs, ref in (
            ("COLUMN_STEEL", T148, {"physical_element": "COLUMNS", "floors": ["GF", "1F", "2F"]}, c,
             "structural set p.9 schedule of columns + details of column reinforcement, p.15 twisted / planted "
             "column details, p.8 notes 9 and 22; column heights to the controlling member (T-119)"),
            ("GROUND_SYSTEM_STEEL", T138, {"physical_element": "GROUND_BEAMS", "floors": ["FOUNDATION"]}, g,
             "structural set p.3 ground-beams plan, p.13 ground-beam sections, p.10 strap rows SB1 .. SB3, p.2 "
             "foundation plan, p.8 notes 9, 21, 22"),
            ("BEAM_STEEL", T149, {"physical_element": "BEAMS", "floors": ["GF", "1F", "2F"]}, b,
             "structural set p.10 schedule of simple beams, p.11 / p.12 continuous beams + typical details, p.15 / "
             "p.16 details, p.8 notes 9, 21, 22; span register T-110 / T-145")):
        led.append({"piece": piece, "source": dict(src, sha256=sha(src["file"])), "scope": scope,
                    "drawing_reference": ref, "declared_totals": totals(recs), "records": recs})
    return {"schema": "URBAN_V303_STEEL_LEDGERS_V1", "project": project, "ledgers": led,
            "evidence_fix": {"closed_top_ends": D4_CLOSED,
                             "source": "T-155 r2 MERGED 15fd913 (checker 2026-10-21 23:53 UTC re-read p.9 / p.13 / "
                                       "p.14)"}}


if __name__ == "__main__":
    doc = inputs("development villa")
    for lg in doc["ledgers"]:
        print(lg["piece"], json.dumps(lg["declared_totals"]))
