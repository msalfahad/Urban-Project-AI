"""T-645 development-villa build (research, unwired): the 31 HELD-blank B7 stair finish lines of the 10 Nov trial BOQ
dry run (T-630: candidate ARCH_TAKEOFF_V3.0.58 + WIRING MANIFEST V15 overlay): FIN.STAIR.FLIGHT 14 lm, FIN.MARBLE.RISER
13 m2, FIN.MARBLE.TREAD 2 m2, FIN.STAIR.SOFFIT 2 m2, classed one by one under R-T645-1 (t645_rules.py).

Rebuild (wrapper only): `URBAN_T645_WRITE=1 bash scripts/agent_env.sh pytest --tree task-T-645 tests/t645/test_t645.py::
test_write_outputs`; check: `bash scripts/agent_env.sh pytest --tree task-T-645 tests/t645`.

Reads only merged repository files (sha256-pinned below). The drawn handles and lengths quoted in OWN_READ were re-read
by handle this run on the Drive copies (architectural DXF sha ab54dd55, structural DXF sha 9f9d1179, decoded into
.work/private only); no coordinate, drawing text or client name is stored. No candidate, released (V2.9 + route G),
rule / knowledge version or registry file is touched; the fix rows are proposals for the wiring manifest (lane I)."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import t645_rules as R  # noqa: E402

D, S, q = R.D, R.S, R.q
SCHEMA, RULE = "URBAN_T645_STAIR_FINISH_HOLD_CENSUS_V1", "R-T645-1"
T630 = "research/agents_t630/out/E2E_BOQ_DRY_RUN_T630.json"
NOSING = "research/agents_t412/NOSING_TABLE_T412.csv"
BIND = "research/agents_t412/CANDIDATE_BINDING_T412.json"
T281 = "research/agents_t281/summary.json"
T425 = "research/agents_t425/FLIGHT_TABLE_T425.csv"
PINS = {T630: "e5dde7867c8fe6ad", NOSING: "9da81b33ec1b5f40", BIND: "7ca6e9691c8a6e51", T281: "8cce8bfc55b4c1a0",
        T425: "e24334102a09a343"}
OUT_JSON = HERE / "out" / "STAIR_HOLD_CENSUS_T645.json"
OUT_MD = HERE / "out" / "STAIR_HOLD_CENSUS_T645.md"
SCOPE_CODES = {"FIN.STAIR.FLIGHT": 14, "FIN.MARBLE.RISER": 13, "FIN.MARBLE.TREAD": 2, "FIN.STAIR.SOFFIT": 2}
BLANK = {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None}
TREAD_T = Decimal("0.030")          # UP-STAIR-006 (owner-confirmed default, URBAN_RULES 1.6.0 / 1.7.0): no tread detail drawn
GOING = Decimal("0.300")            # every drawn going re-read this run (front to front by handle)
DC, OA = "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED"

# ---- governing levels and counts (merged, Checker-verified sources; cited, not re-derived) ---------------------------
# (ffl_from, ffl_to, governing risers over that rise, source)
RISE = {
    "ST01_GF": ("1.00", "3.50", 15, "GF FFL +1.00 and half landing +3.50 printed (section A-A, sheet 10); 10 + 5 risers "
                                    "governing (Q-46 A, T-434 MERGED a6b325b3, Checker re-read 0.1667 on the dashed treads)"),
    "ST01_GF2": ("3.50", "5.50", 12, "half landing +3.50 and 1F FFL +5.50 printed; 12 risers section A-A (Q-46 A, T-184)"),
    "ST01_1F": ("5.50", "9.70", 25, "1F FFL +5.50 and 2F FFL +9.70 printed; 12 + 1 (MS2-TR) + 12 risers section A-A "
                                    "(Q-46 A, T-184); landing levels +7.516 / +7.684 are not printed and are not used"),
    "D1": ("0.30", "1.00", 4, "+0.30 (ST p.3, section A-A) and GF FFL +1.00 printed; 4 riser lines on the GF plan (T-184 "
                              "ST-01b, T-412)"),
    "ST02": ("1.00", "5.50", 28, "GF FFL +1.00 and 1F FFL +5.50 printed; 12 + 11 + 5 = 28 risers (T-438 MERGED 63f77c1d: "
                                 "1F plan + ST p.4 govern, Checker AGREE on two drawings); riser ASSUMED - OWNER-APPROVED "
                                 "(Q-50 A cond: round stair reconstructed from the plans, no section)"),
}
# own read this run (handles only): every edge 1.150, goings 0.300, notch at the proud column by its riser-face line
OWN_READ = {
    "MS1-L": "arch GF DC .. 486: 10 fronts 1.150 (C8 drawn 0.575 to the cut, its companion CD 1.150), 9 goings 0.300; "
             "riser faces D0 inside column 2FBD over 0.050 (CE notched; CF / D1 not); ST p.4 45A .. 25E 12 lines 1.150 "
             "over 3.300 (the other reading)",
    "MS1-U": "arch 1F A92 .. ABE 11 fronts 1.150, 10 goings 0.300; ST p.4 east lane 459 .. 25B 12 lines 1.150 at 0.300 "
             "(3.300): 459 is the 12th (1F floor) edge",
    "MS2-L": "arch 1F AC0 .. A97 12 fronts 1.150, 11 goings 0.300; riser face ABB inside column 3005 over 0.050 (AB7 "
             "notched)",
    "MS2-U": "arch 2F 135B .. 1386 11 fronts 1.150, 10 goings 0.300; ST p.5 east lane 644 .. 62F 11 lines: the 12th edge "
             "and the 11th going are drawn on no sheet",
    "D1": "arch GF 481 / 484 / 48F / 490 4 fronts 1.150, 3 goings 0.300",
    "RS-S": "arch 1F B43 .. B4D 11 fronts 1.150, 10 goings 0.300; riser faces B55 / B54 / B53 inside column 300E over "
            "0.050 (B4A / B49 / B48 notched; Checker F-C-T412-1: 300E, not 2FD2)",
    "RS-A": "arch 1F B59 / B5A / B5B / B5C / D22 5 fronts 1.150, 4 goings 0.300",
}
# engine flight -> drawn flight, role (T-425 MERGED 6f159091 / T-429 R-T429-1: carrier = the reading that values the tread)
CARRIER = {"SITE-3759f2457b22cb4a:F1": "MS1-L", "SITE-3759f2457b22cb4a:F2": "D1", "SITE-a95bf979baf4cfae:F3": "MS1-U",
           "SITE-a95bf979baf4cfae:F2": "MS2-L", "SITE-d7254c68fd33723d:F2": "MS2-U",
           "SITE-735e111dcf9b22c8:F2": "RS-S", "SITE-735e111dcf9b22c8:F4": "RS-A",
           "SITE-735e111dcf9b22c8:F1": "RS-C", "SITE-a95bf979baf4cfae:F5": "MS1-T"}
REPEAT = {  # engine flight -> (carrier engine flight, why)
    "SITE-d7254c68fd33723d:F1": ("SITE-a95bf979baf4cfae:F2", "MS2-L read again on the 2F plan through the opening "
                                 "(DOUBLE_COUNT, T-425 confirmed; no flight leaves 2F, T-184 R-STAIR-CONT-1)"),
    "SITE-a95bf979baf4cfae:F4": ("SITE-735e111dcf9b22c8:F2", "RS-S read on the 1F plan (BOUNDED_EXPOSURE reading); "
                                 "the carrier is the GF F2 reading corrected to the drawn 10 treads (T-425 / T-429)"),
    "SITE-735e111dcf9b22c8:F3": ("SITE-735e111dcf9b22c8:F2", "RS-S partial reading FOLDED into GF F2 (T-425 / T-429)"),
    "SITE-a95bf979baf4cfae:F6": ("SITE-735e111dcf9b22c8:F4", "RS-A read on the 1F plan; the carrier is GF F4 corrected to "
                                 "the drawn 4 treads (T-425 / T-438)"),
    "SITE-a95bf979baf4cfae:F1": ("SITE-735e111dcf9b22c8:F1", "RS-C seen through the void from 1F (SEEN_THROUGH, "
                                 "BOUNDED_EXPOSURE); the carrier GF F1 is itself HELD"),
}
SRC_STAIR = ["OWNER_RULE_STAIRS_2026-10-24 s.1 / s.4 (S-4 (8), S-9)", "UP-STAIR-003 / UP-STAIR-006 (t 0.030)",
             "Q-46 A", "research/agents_t412/NOSING_TABLE_T412.csv (T-412 MERGED f9c80501, Checker 21 / 89 re-measured)",
             "research/agents_t425 (T-425 MERGED 6f159091)"]
C_ST4 = ("C-ST-4 / RFI-A04 (open, architect + structural): MS1-L riser count and landing edge: architectural GF plan 10 "
         "fronts over 2.700 (DC .. 486; with section A-A 10 + 5, Q-46 A, T-434) vs ST p.4 12 straight lines over 3.300 "
         "(45A .. 25E); owner 2026-10-22 18:00: MS1-L HELD on the riser-count conflict")
LAST_EDGE = ("MS2-U: the 12th riser's front (2F floor edge) and the 11th going are drawn on no sheet (arch 2F 11 fronts, "
             "ST p.5 11 lines; T-412 N12 HELD, T-429 T429_LAST_GOING; head clash B23, Q-46 RFI)")


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()[:16]


def pins():
    for p, h in PINS.items():
        if h and _sha(p) != h:
            raise R.RuleError(f"input changed: {p} {_sha(p)} != pinned {h}")


def _json(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def scope_lines():
    rows = [r for r in _json(T630)["per_line"] if r["group"] == "B7" and r["item_code"] in SCOPE_CODES
            and r["class"] == "HELD" and r["held_low"] is None and r["held_high"] is None]
    got = {}
    for r in rows:
        got[r["item_code"]] = got.get(r["item_code"], 0) + 1
        if r["measured_net"] is not None:
            raise R.RuleError(f"{r['line_id']}: HELD with a value in the dry run")
    if got != SCOPE_CODES:
        raise R.RuleError(f"scope changed: {got}")
    return rows


def edges():
    out = {}
    with (ROOT / NOSING).open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.setdefault(r["flight"], []).append(r)
    return out


def binding():
    m = {}
    for f in _json(BIND)["flights"]:
        for code, ln in f["lines"].items():
            m[ln["line_id"]] = {"engine_flight": f["engine_flight"], "element_id": f["element_id"], "code": code,
                                "engine_treads": f["engine_treads"], "engine_kind": f["engine_kind"]}
    return m


def flight_geometry():
    """per drawn flight: riser R, drawn widths (low / high where a reading differs), drawn goings."""
    E = edges()

    def dc(fl):
        return [D(r["qty_lm"]) for r in E[fl] if r["status"] == DC]

    def R_(key):
        a, b, n, _ = RISE[key]
        return R.finished_riser(a, b, n)

    g = {
        "D1": {"rise": "D1", "risers": 4, "widths": dc("D1"), "goings": 3, "ev": DC},
        "MS1-U": {"rise": "ST01_GF2", "risers": 12, "widths": dc("MS1-U") + [Decimal("1.150")], "goings": 11, "ev": DC,
                  "note": "12th front = ST p.4 459 (1.150); its position lies in the B20 head clash (Q-46 RFI), which "
                          "moves no riser area (width = the lane 1.150, height R)"},
        "MS2-L": {"rise": "ST01_1F", "risers": 12, "widths": dc("MS2-L"), "goings": 11, "ev": DC},
        "RS-S": {"rise": "ST02", "risers": 11, "widths": dc("RS-S"), "goings": 10, "ev": OA},
        "RS-A": {"rise": "ST02", "risers": 5, "widths": dc("RS-A"), "goings": 4, "ev": OA},
        "MS1-L": {"rise": "ST01_GF", "risers": 10, "widths": dc("MS1-L"), "goings": 9,
                  "hi_widths": [Decimal("1.150")] * 12, "hi_goings": 11},
        "MS2-U": {"rise": "ST01_1F", "risers": 12, "widths": dc("MS2-U"), "goings": 10,
                  "hi_widths": dc("MS2-U") + [D(next(r["beside_lm"] for r in E["MS2-U"] if r["eid"].endswith("N12")))],
                  "hi_goings": None},
    }
    for fl, x in g.items():
        x["R"] = R_(x["rise"])
        if len(x["widths"]) != x["risers"] and "hi_widths" not in x:
            raise R.RuleError(f"{fl}: {len(x['widths'])} widths for {x['risers']} risers")
    return g


def _q(x):
    return S(q(x))


def build():
    pins()
    lines, bind, geo = scope_lines(), binding(), flight_geometry()
    t425 = {r["flight"]: r for r in csv.DictReader((ROOT / T425).open(encoding="utf-8"))}
    soff = _json(T281)
    entries = []
    for ln in sorted(lines, key=lambda r: (r["item_code"], r["line_id"])):
        lid, code = ln["line_id"], ln["item_code"]
        b = bind.get(lid)
        e = {"line_id": lid, "item_code": code, "unit": ln["unit"], "family": ln["family"], "before": dict(BLANK)}
        if code == "FIN.STAIR.SOFFIT":
            entries.append(soffit_entry(e, lid, soff))
            continue
        ef = b["engine_flight"]
        e.update(engine_flight=ef, element_id=b["element_id"])
        if ef in REPEAT:
            car_ef, why = REPEAT[ef]
            car = next(k for k, v in bind.items() if v["engine_flight"] == car_ef and v["code"] == code)
            e.update({"class": "A_CARRIED", "flight": CARRIER[car_ef], "carrier": car,
                      "cause": f"{why}: the {code} quantity of this flight is carried by {car} (one flight, one valued "
                               "line; R-T429-1)", "sources": ["research/agents_t425/BINDING_T425.json",
                                                              "engine/source/arch_v3039.py R-T429-1"]})
            entries.append(e)
            continue
        fl = CARRIER[ef]
        e["flight"] = fl
        if fl in ("MS1-T", "RS-C"):
            entries.append(held_entry(e, fl, code, t425, geo))
            continue
        x = geo[fl]
        if fl in ("MS1-L", "MS2-U"):
            entries.append(open_entry(e, fl, code, x))
            continue
        e.update({"class": "A_DRAWN", "handles": OWN_READ[fl], "sources": SRC_STAIR + [RISE[x["rise"]][3]]})
        if code == "FIN.MARBLE.RISER":
            v = R.visible_riser_m2(x["widths"], x["R"], TREAD_T)
            basis = (f"{x['risers']} risers x (R {_q(x['R'])} - t 0.030) over drawn widths sum {S(sum(x['widths']))} "
                     f"= {_q(v)} m2 (method of the released E1 riser line L-0afa7bd369ec489ebfc2)")
        else:
            v = R.flight_lm([GOING] * x["goings"], x["R"])
            basis = (f"{x['goings']} drawn goings x hypot(0.300, R {_q(x['R'])}) = {_q(v)} lm (pitch line nosing to "
                     "nosing, arch_measure FIN.STAIR.FLIGHT method)")
        e["cause"] = ("BLOCKED_RFI STAIR_RISER_NOT_ESTABLISHED in the candidate (the engine had no riser input); the "
                      "riser follows from the printed levels and the governing count: " + RISE[x["rise"]][3]
                      + (f"; {x['note']}" if x.get("note") else ""))
        e["fix"] = {"kind": "SET", "before": dict(BLANK), "basis": basis,
                    "after": {"class": "RELEASED", "measured_net": _q(v), "evidence": x["ev"]}}
        entries.append(e)
    for e in entries:
        R.check_entry(e)
    return assemble(entries, geo)


def held_entry(e, fl, code, t425, geo):
    r02 = R.finished_riser(*RISE["ST02"][:3])
    if fl == "MS1-T":
        beside = {"FIN.MARBLE.TREAD": "drawn 4-riser fan region 1.495 m2 (engine reading, T-425; T-281 plan 1.495)",
                  "FIN.MARBLE.RISER": "5 risers (count DRAWING-CONFIRMED, A-A) of R 0.166667; winder fronts of the drawn "
                                      "4-riser fan 4.144 lm (T-412) do not subdivide 5",
                  "FIN.STAIR.FLIGHT": "none: a winder pitch line needs a walking line, never assumed (S-9)"}[code]
        e.update({"class": "B_HELD", "cause": "MS1-T winder turn seen from 1F: section A-A governs 5 winders, every "
                  "plan draws a 4-riser fan: the winder subdivision is not drawn (D-67, WINDER_SUBDIVISION_NOT_DRAWN; "
                  "OWNER_RULE_STAIRS S-9: never generated, no walking line) - beside: " + beside,
                  "sources": ["DESIGNER_CLARIFICATIONS D-67", "research/agents_t434 (T-434 MERGED a6b325b3)",
                              "OWNER_RULE_STAIRS_2026-10-24 s.4 S-9"]})
    else:
        lm = Decimal("13.850")
        beside = {"FIN.MARBLE.TREAD": f"engine {t425['RS-C']['candidate_tread_m2_before']} m2; drawn region 4.443096 m2 "
                                      "(T-415)",
                  "FIN.MARBLE.RISER": f"12 radial fronts 13.850 lm (T-412) x (R {_q(r02)} - 0.030) = "
                                      f"{_q(lm * (r02 - TREAD_T))} m2, illustrative only",
                  "FIN.STAIR.FLIGHT": "none: the engine's mid-radius walking line is an assumed offset (S-9)"}[code]
        e.update({"class": "B_HELD", "cause": "RS-C curved flight of the round stair: owner Q-50 A cond holds the curved "
                  "part (no section; RFI-A03 / RFI-S27); a curved going or walking line is never generated (S-9) - "
                  "beside: " + beside,
                  "sources": ["OWNER_QUESTIONS_ANSWERED Q-50 A cond", "research/agents_t415 (T-415 MERGED 8c8372a4)",
                              "research/agents_t412/NOSING_TABLE_T412.csv RS-C", "rfi/A_PRIORITY_RFI.md RFI-A03"]})
    return e


def open_entry(e, fl, code, x):
    if fl == "MS1-L":
        cause, srcs = C_ST4, ["CLARIFICATIONS_CONSULTANT_2026-10-23 row 5 C-ST-4", "rfi/A_PRIORITY_RFI.md RFI-A04",
                              "OWNER_SESSION_CHANGES 2026-10-22 18:00", "research/agents_t434 (T-434)"]
    else:
        cause, srcs = LAST_EDGE, ["research/agents_t412/NOSING_TABLE_T412.csv ST01-MS2U-N12",
                                  "engine/source/arch_v3039.py T429_LAST_GOING", "Q-46 RFI (head clash)"]
    if code == "FIN.MARBLE.RISER":
        lo = R.visible_riser_m2(x["widths"], x["R"], TREAD_T)
        hi = R.visible_riser_m2(x["hi_widths"], x["R"], TREAD_T)
        basis = (f"low {len(x['widths'])} drawn fronts {S(sum(x['widths']))} lm, high {len(x['hi_widths'])} fronts "
                 f"{S(sum(x['hi_widths']))} lm, x (R {_q(x['R'])} - 0.030)")
    else:
        lo = R.flight_lm([GOING] * x["goings"], x["R"])
        hi = R.flight_lm([GOING] * x["hi_goings"], x["R"]) if x["hi_goings"] else None
        basis = (f"low {x['goings']} drawn goings, high " + (f"{x['hi_goings']} goings" if hi else "OPEN (the last "
                 "going is drawn on no sheet)") + f", x hypot(0.300, R {_q(x['R'])})")
    e.update({"class": "C_OPEN", "cause": cause + " - stays HELD; bounded by the drawn readings", "sources": srcs,
              "handles": OWN_READ[fl],
              "fix": {"kind": "SET", "before": dict(BLANK), "basis": basis,
                      "after": {"class": "HELD", "measured_net": None, "held_low": _q(lo),
                                "held_high": _q(hi) if hi is not None else None}}})
    return e


def soffit_entry(e, lid, soff):
    t = soff["totals"]
    if lid == "L-1fcec3328ccd0ea243d4":
        c = soff["MS1-L CONFLICT"]
        ms1l = {"O": min(c["A_architectural"]["true_O"], c["B_structural"]["true_O"]),
                "D": min(c["A_architectural"]["true_D"], c["B_structural"]["true_D"])}
        lo, tot = R.soffit_low({"O": [t["ST-01"]["true_O_measured"], ms1l["O"]],
                                "D": [t["ST-01"]["true_D_measured"], ms1l["D"]]})
        cause = ("ST-01 soffit: T-281 measured rows (method O 17.197803 / D 17.243246 m2 true) + MS1-L in either "
                 "reading (C-ST-4: O 3.677828 .. 4.501478, D 3.225561 .. 4.049212) are present in every reading; the "
                 "high end is OPEN: MS1-T warped soffit and MS2-TR junction not drawn (D-67 / C-ST-3, plan 1.500 m2 "
                 "HELD), column 691 exposure HELD (D-16), method O vs D a RULE_DIFFERENCE (no owner soffit rule), finish "
                 "type of a stair soffit not printed")
        e.update(element_id="STAIR:ST-01:soffit")
    else:
        lo, tot = R.soffit_low({"O": [t["ST-02"]["true_O_measured"]], "D": [t["ST-02"]["true_D_measured"]]})
        cause = ("ST-02 soffit: T-281 measured rows method O 4.460946 / D 4.905788 m2 true; the high end is OPEN: RS-C "
                 "helicoid soffit not drawn (plan 4.443156 m2, Q-50 A cond / C-ST-3), sub-pieces under the 'B3 (With "
                 "Stair)' band and the CA member HELD (Q-61 C, T-258), unknown pairs 0.596481 m2 plan; method O vs D a "
                 "RULE_DIFFERENCE; finish type not printed")
        e.update(element_id="STAIR:ST-02:soffit")
    e.update({"class": "C_OPEN", "cause": cause, "sources": [T281 + " (T-281 MERGED 40518c58)",
                                                             "engine/source/arch_v3032.py STAIR_SOFFIT_T281"],
              "fix": {"kind": "SET", "before": dict(BLANK),
                      "basis": "low = min over methods of the pieces present in every reading: " +
                               ", ".join(f"{m} {_q(v)}" for m, v in sorted(tot.items())) + "; high OPEN",
                      "after": {"class": "HELD", "measured_net": None, "held_low": _q(lo), "held_high": None}}})
    return e


def assemble(entries, geo):
    c = R.census_counts(entries)
    rel = {}
    for e in entries:
        fx = e.get("fix")
        if fx and fx["after"]["class"] == "RELEASED":
            rel.setdefault(e["item_code"], Decimal(0))
            rel[e["item_code"]] += D(fx["after"]["measured_net"])
    bnd = {}
    for e in entries:
        fx = e.get("fix")
        if fx and fx["after"]["class"] == "HELD":
            k = e["item_code"]
            a = bnd.setdefault(k, {"low": Decimal(0), "high": Decimal(0), "open": 0, "n": 0})
            a["n"] += 1
            a["low"] += D(fx["after"]["held_low"])
            if fx["after"]["held_high"] is None:
                a["open"] += 1
            else:
                a["high"] += D(fx["after"]["held_high"])
    risers = {fl: {"R": _q(x["R"]), "risers": x["risers"], "widths_lm": S(sum(x["widths"])), "goings": x["goings"]}
              for fl, x in sorted(geo.items())}
    return {"schema": SCHEMA, "rule": RULE, "task": "T-645",
            "inputs": {p: _sha(p) for p in PINS}, "scope": "B7 FIN.STAIR.FLIGHT / FIN.MARBLE.RISER / FIN.MARBLE.TREAD / "
            "FIN.STAIR.SOFFIT HELD-blank lines (T-630 per_line: class HELD, no bound)",
            "counts": c, "released_by_code": {k: S(v) for k, v in sorted(rel.items())},
            "bounded_by_code": {k: {"n": v["n"], "low": S(v["low"]), "high": "OPEN" if v["open"] else S(v["high"]),
                                    "open_n": v["open"]} for k, v in sorted(bnd.items())},
            "flights": risers, "tread_t_m": S(TREAD_T), "going_m": S(GOING), "own_read": OWN_READ,
            "lines": entries}


def dumps(o):
    return json.dumps(o, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def render_md(b):
    c = b["counts"]
    out = ["# T-645 stair finish HELD-blank census (generated; do not edit)", "",
           f"Rule {b['rule']}; lines {c['lines']}; by class {c['by_class']}; fix rows {c['fix_rows']} "
           f"(released {c['released_rows']}, bounded {c['bounded_rows']}); stay blank {c['stay_held_blank']}; "
           f"carried {c['carried']}.", "",
           "Released (proposed, by code): " + ", ".join(f"{k} {v}" for k, v in b["released_by_code"].items()), "",
           "Bounded HELD (by code): " + ", ".join(f"{k} {v['low']} .. {v['high']} ({v['n']})"
                                                  for k, v in b["bounded_by_code"].items()), "",
           "| line | code | flight | class | after | cause / carrier |", "|---|---|---|---|---|---|"]
    for e in b["lines"]:
        fx = e.get("fix")
        if fx:
            a = fx["after"]
            aft = (f"RELEASED {a['measured_net']} ({a['evidence']})" if a["class"] == "RELEASED"
                   else f"HELD {a['held_low']} .. {a['held_high'] or 'OPEN'}")
        else:
            aft = "HELD blank" if e["class"] != "A_CARRIED" else "carried"
        why = (f"carrier {e['carrier']}" if e["class"] == "A_CARRIED" else e["cause"][:160])
        out.append(f"| {e['line_id']} | {e['item_code']} | {e.get('flight', e.get('element_id'))} | {e['class']} | "
                   f"{aft} | {why} |")
    return "\n".join(out) + "\n"


def write_outputs():
    b = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(dumps(b), encoding="utf-8")
    OUT_MD.write_text(render_md(b), encoding="utf-8")
    return b


if __name__ == "__main__":
    print(dumps(build())[:3000])
