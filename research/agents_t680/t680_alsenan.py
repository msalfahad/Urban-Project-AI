"""T-680 builder: stair-shaft ST-01 plaster / paint storey-band lines, round 2 (development villa), R-T680-1 .. -3.
Research only: reads merged, sha256-pinned research inputs; writes out/ only; wires nothing.

    python3 -I research/agents_t680/t680_alsenan.py [--check]

Reads: research/agents_t173 (the merged shaft face model and its shaft-local input: no coordinates, no client data),
research/agents_t201/HEADS_T201.csv (the Checker-verified vector heads of W25 / W27), research/agents_t671/out/
LINE_INDEX_V3_0_65.json (the candidate of record's lines), research/agents_t676 (census classes and coat materials).

Steps: (0) reproduce the candidate / overlay bounds from the T-173 model (baseline, must match to 0.01 m2);
(1) R-T680-1: W25 (the shaft's 1F window, T-173 '1F-north-window') and W27 take their DWF vector sill / head;
(2) R-T680-2: the pier returns go into their storey bands; (3) the 2F band keeps the T-640 FR-T640-28 / -29 D-T173-1
and B3 corrections unchanged; (4) R-T680-3: every target line restated with its change; the two stair-core wet-room
plaster lines name their missing datum.
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

from shapely.geometry import box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t680_rules as R  # noqa: E402

T173 = ROOT / "research/agents_t173"
T201 = ROOT / "research/agents_t201/HEADS_T201.csv"
CAND = ROOT / "research/agents_t671/out/LINE_INDEX_V3_0_65.json"
T676 = ROOT / "research/agents_t676/out/T676_PLASTER_PAINT_CENSUS.json"
OUT = HERE / "out"
PIN = {
    "candidate": "LINE_INDEX_V3_0_65.json",
    "t173_input": "ALSENAN_SHAFT_INPUT.json",
}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


SH = _load("t173_shaft", T173 / "t173_shaft.py")
A = _load("t173_alsenan", T173 / "t173_alsenan.py")
R676 = _load("t676_rules", ROOT / "research/agents_t676/t676_rules.py")

MARKS = [5.50, 9.70]
BANDS = ("GF", "1F", "2F")
LINES = {  # line id -> (band, finish)
    "L-95f2c45c2eccaaeccb08": ("GF", "plaster"), "L-145bd2394f2907558243": ("GF", "paint"),
    "L-0eac839f9132da7bd116": ("1F", "plaster"), "L-2ab93d5029a4b7cc4dca": ("1F", "paint"),
    "L-418121a4b223cb4e8646": ("2F", "plaster"), "L-5a7a5c6f070ec7142ca5": ("2F", "paint"),
}
OVERLAY = {"L-418121a4b223cb4e8646": ("44.512", "49.872"), "L-5a7a5c6f070ec7142ca5": ("42.722", "47.932")}
# T-640 FR-T640-28 / -29 corrections (Checker D-T173-1: roof panel prints T 18, soffit +13.72 not +13.74; roof B3
# downstand at the top of W and E): low end all four, high end the certain W / E ones. Kept unchanged here.
CORR_2F = {"low": Decimal("0.104") + Decimal("0.104") + Decimal("0.05") + Decimal("0.08"),
           "high": Decimal("0.104") + Decimal("0.104")}
# shaft-face opening id in the T-173 model -> T-201 opening id (binding: T-201 READINGS along-facade 13.269 / 13.270 m,
# the two 1.00 m windows stacked on the SW facade = the shaft's 'N' face in the T-173 frame; T-325 'W25 (1F stair),
# W27 (2F stair)', both over outside air; T-201 hosts 1F-W10 / 2F-W02)
BIND = {"1F-north-window": "W25", "W27": "W27"}
WET_ROOMS = {
    "L-a636dabcd4bc7e59169a": "GF-RD36087",
    "L-3f7fb1b37e68e6d6c7b7": "GF-RDF7D28",
}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def heads():
    rows = {r["ID"]: r for r in csv.DictReader(T201.open())}
    out = {}
    for fid, oid in BIND.items():
        r = rows[oid]
        out[fid] = {"id": oid, "status": r["STATUS"], "view": r["SOURCE"].split(";")[0], "sill_m": r["SILL_LEVEL_M"],
                    "head_m": r["HEAD_LEVEL_M"], "width_m": r["WIDTH_M"], "source": r["SOURCE"],
                    "issue_check": r["ISSUE_CHECK"]}
    return out


def geoms(face):
    """The same construction as t173_shaft.measure_face, returning the net geometries (hi, lo)."""
    G = unary_union([SH.rect(*r) for r in face["region"]])
    kc = [c for c in face.get("contacts", []) if c.get("status", "KNOWN") == "KNOWN"]
    hc = [c for c in face.get("contacts", []) if c.get("status") == "HELD"]
    ko = [o for o in face.get("openings", []) if o.get("status") in ("PRINTED", "ASSUMED")]
    ho = [o for o in face.get("openings", []) if o.get("status") == "HELD"]
    K = SH._union(kc).intersection(G)
    O = SH._union(ko).intersection(G.difference(K))
    rest = G.difference(K).difference(O)
    HC = SH._union(hc).intersection(rest)
    HO = SH._union(ho).intersection(rest.difference(HC))
    return rest, rest.difference(HC).difference(HO)


def band_areas(faces, marks=None):
    """-> {'hi': [GF, 1F, 2F], 'lo': [...], 'ret_hi': [...], 'ret_lo': [...], 'whole': (net_hi, net_lo)}."""
    marks = MARKS if marks is None else list(marks)
    n = len(marks) + 1
    hi, lo, rh, rl = [0.0] * n, [0.0] * n, [0.0] * n, [0.0] * n
    for f in faces:
        g_hi, g_lo = geoms(f)
        edges = [-1e9] + marks + [1e9]
        for i, (a, b) in enumerate(zip(edges, edges[1:])):
            clip = box(-1e9, a, 1e9, b)
            hi[i] += g_hi.intersection(clip).area
            lo[i] += g_lo.intersection(clip).area
        for i, v in enumerate(R.returns_by_band(g_hi, f.get("returns", []), marks)):
            rh[i] += v
        for i, v in enumerate(R.returns_by_band(g_lo, f.get("returns", []), marks)):
            rl[i] += v
    whole = SH.measure_shaft(faces)["total"]
    R.check_bands_sum(whole["net_hi"], [a + b for a, b in zip(hi, rh)])
    R.check_bands_sum(whole["net_lo"], [a + b for a, b in zip(lo, rl)])
    return {"hi": hi, "lo": lo, "ret_hi": rh, "ret_lo": rl, "whole": (whole["net_hi"], whole["net_lo"])}


def case_faces(case, finish, apply_heads):
    b, nw = (0.0, A.INP["levels"]["gf_lobby"]) if case == "HI" else (0.10, A.INP["levels"]["gf"])
    top = R.face_top(A.INP["levels"]["roof_mark"], b, A.T)
    if finish == "paint":
        top -= A.DECOR
    faces = A.faces(b, nw, top)
    if apply_heads:
        H = heads()
        north = next(f for f in faces if f["id"].startswith("N "))
        new = []
        for o in north["openings"]:
            if o["id"] in H:
                u0, u1 = o["rect"][0], o["rect"][1]
                new.append(R.opening_from_geometry({"id": o["id"], "u": [u0, u1], "status": "HELD"}, H[o["id"]],
                                                   north["region"]))
            else:
                new.append(o)
        north["openings"] = new
    return faces


def bounds(apply_heads, with_returns):
    res = {}
    for finish in ("plaster", "paint"):
        a_hi = band_areas(case_faces("HI", finish, apply_heads))
        a_lo = band_areas(case_faces("LO", finish, apply_heads))
        for i, band in enumerate(BANDS):
            high = Decimal(repr(a_hi["hi"][i] + (a_hi["ret_hi"][i] if with_returns else 0.0)))
            low = Decimal(repr(a_lo["lo"][i] + (a_lo["ret_lo"][i] if with_returns else 0.0)))
            if band == "2F":
                low, high = low - CORR_2F["low"], high - CORR_2F["high"]
            res[(band, finish)] = {"low": low, "high": high,
                                   "returns": [R.S(a_lo["ret_lo"][i]), R.S(a_hi["ret_hi"][i])]}
    return res


def build():
    cand = json.loads(CAND.read_text())
    lines = {l["line_id"]: l for l in cand["lines"]}
    c676 = {e["line_id"]: e for e in json.loads(T676.read_text())["entries"]}
    base = bounds(False, False)
    # step 0: the baseline must reproduce the candidate (GF / 1F, 2 dp) and the overlay (2F, 3 dp)
    repro = []
    for lid, (band, fin) in LINES.items():
        l = lines[lid]
        b = base[(band, fin)]
        if lid in OVERLAY:
            ref = tuple(Decimal(x) for x in OVERLAY[lid])
            got = (R.q3(b["low"]), R.q3(b["high"]))
        else:
            ref = (Decimal(str(l["held_low"])), Decimal(str(l["held_high"])))
            got = tuple(x.quantize(Decimal("0.01")) for x in (b["low"], b["high"]))
        ok = all(abs(a - c) <= Decimal("0.0051") for a, c in zip(got, ref))
        repro.append({"line_id": lid, "band": band, "finish": fin, "reference": [str(x) for x in ref],
                      "reproduced": [str(x) for x in got], "match": ok})
        if not ok:
            raise R.RuleError(f"{lid}: baseline {got} does not reproduce {ref}")
    step1 = bounds(True, False)
    final = bounds(True, True)
    rows = []
    for lid, (band, fin) in LINES.items():
        l = lines[lid]
        f = final[(band, fin)]
        after = R.line_bound(f["low"], f["high"], "")
        before = (l["held_low"], l["held_high"])
        e = {"line_id": lid, "item_code": l["item_code"], "element_id": l["element_id"], "band": band,
             "finish": fin, "candidate": [before[0], before[1]],
             "overlay_bound": list(OVERLAY[lid]) if lid in OVERLAY else None,
             "step1_heads": [R.S(step1[(band, fin)]["low"]), R.S(step1[(band, fin)]["high"])],
             "returns_lo_hi": f["returns"], **after,
             "change_vs_candidate": R.restate(before[0], before[1], after),
             "change_vs_overlay": (R.restate(*OVERLAY[lid], after) if lid in OVERLAY else None),
             "status": "HELD bound (geometry DRAWING-CONFIRMED; W25 / W27 heads DRAWING-CONFIRMED T-201; build-up b "
                       "and roof datum PROVISIONAL; door heads ASSUMED - OWNER-APPROVED Q-55 C; paint top ASSUMED - "
                       "OWNER-APPROVED Q-48 A)",
             "still_open": _still_open(band)}
        if fin == "plaster":
            t = c676[lid]["materials"]
            th = json.loads(T676.read_text())["thickness_from_t489"]["WALL_PLASTER"]
            e["materials"] = {"WALL_PLASTER (1:4)": R676.coat_materials(after["held_low"], after["held_high"],
                                                                         "WALL_PLASTER", th[0], th[1]),
                              "BOND_COAT spatter dash (1:2)": t["rows"]["BOND_COAT spatter dash (1:2)"],
                              "coat_class": t["coat_class"]}
        rows.append(e)
    wet = []
    for lid, room in WET_ROOMS.items():
        l = lines[lid]
        if l["held_low"] is not None or l["class"] != "HELD":
            raise R.RuleError(f"{lid}: expected a blank HELD line")
        wet.append({"line_id": lid, "item_code": l["item_code"], "element_id": l["element_id"], "class": "HELD",
                    "held_low": None, "held_high": None, "measured_net": None,
                    "missing_datum": [
                        f"{room} finished floor level: +0.30 (lobby) or +1.00 (main GF) - no floor edge or level is "
                        "drawn under the stair-core rooms (T-088; T-173 C-SH-2): designer item",
                        "the top of the wet-wall render: the 1F slab soffit (+5.50 - b - 0.16) or the soffit of the "
                        "beam crossing the room (T-283: bulkhead edges on CONFLICT / HELD beams, Q-61 C)" if
                        room == "GF-RDF7D28" else
                        "the top of the wet-wall render: the 1F slab soffit (+5.50 - b - 0.16), build-up b 0 .. 0.10",
                        "the head of the doorless passage OP-020 (0.90 m, shared with the stair hall; head lines hidden, "
                        "no head printed; T-441)" if room == "GF-RD36087" else
                        "the window OP-014 head / sill (no T-201 record; the line carries the window as EXCLUDED)",
                    ],
                    "why_no_bound": "a 0.70 m floor-datum spread x the room perimeter (T-283 cove runs 4.90 / 6.20 "
                                    "m, not wall faces) with an unestablished render top and a held opening gives no "
                                    "two-sided bound from the drawings; the line stays HELD by name, never 0",
                    "cause_t676": c676[lid]["cause"]})
    sums = {}
    for fin in ("plaster", "paint"):
        rs = [r for r in rows if r["finish"] == fin]
        sums[fin] = {"low": R.S(sum(Decimal(r["held_low"]) for r in rs)),
                     "high": R.S(sum(Decimal(r["held_high"]) for r in rs)),
                     "candidate_bounded_low": R.S(sum(Decimal(str(r["candidate"][0])) for r in rs if r["candidate"][0] is not None)),
                     "candidate_bounded_high": R.S(sum(Decimal(str(r["candidate"][1])) for r in rs if r["candidate"][1] is not None))}
    code_totals = _code_totals(cand, rows, json.loads(T676.read_text()))
    return {"schema": "URBAN_T680_SHAFT_ROUND2_V1", "task": "T-680", "rules": ["R-T680-1", "R-T680-2", "R-T680-3"],
            "code_totals_m2": code_totals,
            "candidate": cand["candidate_version"],
            "inputs": {"candidate_line_index": sha(CAND), "t173_input": sha(T173 / PIN["t173_input"]),
                       "t173_shaft": sha(T173 / "t173_shaft.py"), "t201_heads": sha(T201), "t676_census": sha(T676)},
            "heads_applied": heads(), "baseline_reproduction": repro, "lines": rows, "wet_room_lines": wet,
            "shaft_sums_m2": sums,
            "corrections_2f_kept": {k: str(v) for k, v in CORR_2F.items()}}


def _code_totals(cand, rows, c676):
    """FIN.PLASTER / FIN.PAINT HELD lines of the candidate: bounded sum and blank count, before and after the T-680
    rows (and, beside it, with the T-676 OP-009 fix row that also waits for the plaster Gate B row)."""
    new = {r["line_id"]: (Decimal(r["held_low"]), Decimal(r["held_high"])) for r in rows}
    fix676 = {f["line_id"]: (Decimal(f["value"]), Decimal(f["value"])) for f in c676["fix_rows"]}
    out = {}
    for code in ("FIN.PLASTER", "FIN.PAINT"):
        held = [l for l in cand["lines"] if l["class"] == "HELD" and l["item_code"] == code]
        def tot(over):
            lo = hi = Decimal(0)
            n = blank = 0
            for l in held:
                b = over.get(l["line_id"])
                if b is None and l["held_low"] is not None:
                    b = (Decimal(str(l["held_low"])), Decimal(str(l["held_high"])))
                if b is None:
                    blank += 1
                    continue
                n += 1
                lo, hi = lo + b[0], hi + b[1]
            return {"bounded": n, "blank": blank, "low": format(lo, "f"), "high": format(hi, "f")}
        b, a = tot({}), tot(new)
        out[code] = {"lines": len(held), "before": b, "after_t680": a,
                     "after_t680_and_t676_op009": tot({**new, **fix676}),
                     "change_low": format(Decimal(a["low"]) - Decimal(b["low"]), "f"),
                     "change_high": format(Decimal(a["high"]) - Decimal(b["high"]), "f")}
    return out


def _still_open(band):
    common = ["build-up b 0 .. 0.10 (DCR-6 / DCR-7)"]
    if band == "GF":
        return common + ["NW floor under the winders +0.30 / +1.00 (C-SH-2)", "winder soffit MS1-T (C-ST-3)",
                         "GF doorless passage head to the basin space (OP-020)", "B20 over the GF south wall (Q-46 / OQ-11)"]
    if band == "1F":
        return common + ["winder soffit MS1-T above +5.50: none (the turn ends at +3.50)",
                         "B20 / B23 ends at the stair head (Q-46 / OQ-11)", "GF passage band part above +5.50: none"]
    return common + ["roof datum D-39", "B23 end at the stair head (Q-46 / OQ-11)",
                     "D-T173-1 N correction and roof B3 downstand (low end only, as T-640)"]


def md(r):
    L = ["# T-680 stair-shaft ST-01 plaster / paint storey-band lines, round 2", "",
         f"Candidate {r['candidate']}. Research only, nothing wired.", "",
         "Heads applied (R-T680-1, T-201 DWF vector, Checker-verified):"]
    for k, h in r["heads_applied"].items():
        L.append(f"- {k} = {h['id']}: sill +{h['sill_m']} / head +{h['head_m']}, width {h['width_m']} "
                 f"({h['status']}; {h['source']}; issue check {h['issue_check']})")
    L += ["", "Baseline reproduction (T-173 model + T-640 corrections, before this task's changes):", "",
          "| line | band | finish | reference | reproduced | match |", "|---|---|---|---|---|---|"]
    for b in r["baseline_reproduction"]:
        L.append(f"| {b['line_id']} | {b['band']} | {b['finish']} | {' .. '.join(b['reference'])} | "
                 f"{' .. '.join(b['reproduced'])} | {b['match']} |")
    L += ["", "| line | code | band | candidate | overlay | heads only | returns lo / hi | restated | change low / high |",
          "|---|---|---|---|---|---|---|---|---|"]
    for e in r["lines"]:
        c = "blank" if e["candidate"][0] is None else f"{e['candidate'][0]} .. {e['candidate'][1]}"
        o = "-" if not e["overlay_bound"] else " .. ".join(e["overlay_bound"])
        ch = e["change_vs_overlay"] or e["change_vs_candidate"]
        L.append(f"| {e['line_id']} | {e['item_code']} | {e['band']} | {c} | {o} | {' .. '.join(e['step1_heads'])} | "
                 f"{' / '.join(e['returns_lo_hi'])} | {e['held_low']} .. {e['held_high']} | "
                 f"{ch['delta'][0]} / {ch['delta'][1]} |")
    L += ["", "| code | HELD lines | before: bounded sum (n) + blank | after T-680 | change low / high | with T-676 OP-009 |",
          "|---|---|---|---|---|---|"]
    for k, t in r["code_totals_m2"].items():
        b, a, c = t["before"], t["after_t680"], t["after_t680_and_t676_op009"]
        L.append(f"| {k} | {t['lines']} | {b['low']} .. {b['high']} ({b['bounded']}) + {b['blank']} blank | "
                 f"{a['low']} .. {a['high']} ({a['bounded']}) + {a['blank']} blank | {t['change_low']} / "
                 f"{t['change_high']} | {c['low']} .. {c['high']} |")
    L += ["", "Shaft sums (m2): " + "; ".join(f"{k} {v['low']} .. {v['high']}" for k, v in r["shaft_sums_m2"].items()),
          "", "Plaster coat materials (Q-79 1:4; T-676 R-T676-3):"]
    for e in r["lines"]:
        if "materials" in e:
            m = e["materials"]["WALL_PLASTER (1:4)"]
            L.append(f"- {e['line_id']} {e['band']}: cement {m['cement_bags'][0]} .. {m['cement_bags'][1]} bags, "
                     f"sand {m['sand_m3'][0]} .. {m['sand_m3'][1]} m3; spatter dash HELD; water HELD")
    L += ["", "Stair-core wet-room plaster lines (stay HELD, datum named):"]
    for w in r["wet_room_lines"]:
        L.append(f"- {w['line_id']} {w['element_id']}: " + "; ".join(w["missing_datum"]))
    return "\n".join(L) + "\n"


def main(argv):
    r = build()
    js = json.dumps(r, indent=1, sort_keys=True, default=str) + "\n"
    mdt = md(r)
    pj, pm = OUT / "T680_SHAFT_ROUND2.json", OUT / "T680_SHAFT_ROUND2.md"
    if "--check" in argv:
        ok = pj.read_text() == js and pm.read_text() == mdt
        print("T-680 outputs", "MATCH" if ok else "DIFFER")
        return 0 if ok else 1
    OUT.mkdir(exist_ok=True)
    pj.write_text(js)
    pm.write_text(mdt)
    print(mdt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
