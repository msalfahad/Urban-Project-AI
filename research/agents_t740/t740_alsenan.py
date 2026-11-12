"""T-740 development-villa builder: PAINT AREA RULE (UP-FIN-PAINT-002) restated face by face on ARCH_TAKEOFF_V3.0.74
(research, unwired: no line moves; wiring is a later hub package).

Reads only repository files, each sha256-pinned (an edited input stops the build):
  research/agents_t717/out/LINE_INDEX_V3_0_74.json   candidate of record V3.0.74 (T-717 FINISH_GATE_B_V2)
  research/agents_t292/OPENING_DEDUCTIONS_T292.csv   per-opening ledger (width / sill / head, owner G1 deductions)
  research/agents_t709/out/T709_RESIDUALS.json       R-T709-1 double-height band terms, R-T709-4 return-paint flags
Typed here (cited): per dry room face lm and heights (T-556 R-T556-1 plaster to the soffit, DRAWING-CONFIRMED floor
build-up; owner G1 paint to the finished ceiling, Q-48 A; annex datum bound Q-54 B, T-701 R-T701-2), the beam ends
(T-556 BEAM_ENDS from the T-110 schedule), the stair-shaft 2F decor band (T-173 / T-680). No coordinate, client name,
drawing content or workbook text is stored.

    python3 -I research/agents_t740/t740_alsenan.py           # writes out/T740_PAINT_RULE.json and .md
    python3 -I research/agents_t740/t740_alsenan.py --check   # rebuilds in memory, compares byte for byte
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import t740_rules as R  # noqa: E402

D, q6 = R.D, R.q6
INDEX = ROOT / "research/agents_t717/out/LINE_INDEX_V3_0_74.json"
OPEN = ROOT / "research/agents_t292/OPENING_DEDUCTIONS_T292.csv"
T709 = ROOT / "research/agents_t709/out/T709_RESIDUALS.json"
PINS = {INDEX: "6733cbc143cdfffd82eeaee54457f97bbfa7b91b541f648a411825887b8b3bca",
        OPEN: "4d75de86848509e4a3b37bd4825dfd2d65e26f35eea5bd0ee3227f954277f5dd",
        T709: "fcbd5aa7d9a12018358a757a284fa746302f44b9ddb122f51c9ad7a53bd82151"}
OUT_JSON = HERE / "out" / "T740_PAINT_RULE.json"
OUT_MD = HERE / "out" / "T740_PAINT_RULE.md"
CODES = ("FIN.PLASTER", "FIN.PAINT", "FIN.EXT.FINISH", "EXT.FENCE.PLASTER", "EXT.FENCE.PAINT")

# ---- typed, cited inputs: the 11 dry room faces -------------------------------------------------------------------
# heights above the room's finished floor, per end (low scenario, high scenario); T-556 rows / T-701 dry_rooms.
#   GF main: plaster 4.29 (4.50 - 0.05 - 0.16), paint G1 3.65; 1F / 2F: plaster 3.99 (4.20 - 0.05 - 0.16), paint 3.35;
#   annex GF-01 / GF-04: plaster S = s - 0.46, paint H = s - 1.05 over one datum s (Q-54 B; T-701 R-T701-2), so the
#   ends pair as S 3.084 / H 2.494 (low) and S 3.84 / H 3.25 (high): band height 0.59 at both ends.
# items: ("opening", id, ledger) -> geometry from the T-292 ledger;  ("held", id, width) an opening with no printed
#   height (deducted in full at the low end, 0 at the high end, T-292 'h HELD');  ("fixed", id, m2, band m2, why) an
#   outline whose area the ledgers fix (arched / hole-height windows);  ("beam", mark, width lo, width hi, depth below
#   the soffit, ends lo, ends hi) T-556 BEAM_ENDS (depth = schedule h - slab 0.16).
# engine_paint: the paint line's own deduction per item where it is not the ledger's (back-derived, labelled).
GF, F1 = ("4.29", "4.29", "3.65", "3.65"), ("3.99", "3.99", "3.35", "3.35")
ANNEX = ("3.084", "3.84", "2.494", "3.25")
DRY = [
    ("GF-01", "GF", "20.127", ANNEX, [
        ("fixed2", "W11 + W12", ("8.601824", "8.601824"), ("0", "0"),
         "hole height 2.20 x w (T-207, DRAWING-CONFIRMED; W12 1.95492 x 2.20 = 4.300824, F-T709-1): sill HELD, head "
         "taken at or below the paint top as in both lines"),
        ("opening", "D-GF-01", None), ("held", "A-GF-01", "1.0"),
        ("beam", "CB6", "0.2", "0.2", "0.59", 2, 2)],
     {"W11 + W12": (("8.591", "6.28705"), "back-derived from the paint line (L x H - line - the other items): the "
                                         "paint line still carries W12 4.29 at its low end (F-T717-1) and the "
                                         "pre-T-207 window basis at its high end")}),
    ("GF-04", "GF", "12.5", ANNEX, [("opening", "W04", None), ("opening", "D-GF-03", None),
                                    ("opening", "D-GF-04", None)], {}),
    ("GF-15", "GF", "21.537", GF, [("opening", "D-GF-14", None), ("opening", "W03", "GF-15"),
                                   ("opening", "D-GF-13", None)], {}),
    ("GF-08", "GF", "53.188", GF, [("opening", "D-GF-08", None), ("held", "L-GF-01", "1.0"),
                                   ("opening", "D-GF-13", None), ("opening", "W03", "GF-08"),
                                   ("held", "W02", "6.33"), ("opening", "D-GF-07", None),
                                   ("beam", "B26", "0.65", "0.65", "0.69", 2, 0),
                                   ("beam", "B27", "0.9", "0.9", "0.69", 2, 0)], {}),
    ("1F-01", "1F", "17.7", F1, [("opening", "D-1F-02", None), ("opening", "D-1F-01", None), ("opening", "W14", None),
                                 ("beam", "B6", "0.25", "0.2", "0.34", 2, 2)], {}),
    ("1F-04", "1F", "17.4", F1, [("opening", "D-1F-03", None), ("opening", "W24", None),
                                 ("opening", "D-1F-04", None)], {}),
    ("1F-10", "1F", "16.2", F1, [("opening", "D-1F-08", None), ("held", "A-1F-01", "1.0"),
                                 ("beam", "B19", "0.4", "0.4", "0.59", 2, 2),
                                 ("beam", "B6", "0.25", "0.2", "0.34", 2, 2)], {}),
    ("1F-11", "1F", "22.149", F1, [
        ("fixed2", "W17", ("9.858", "4.4361"), ("0", "0"),
         "arched outline HELD between w x springing 1.35 and w x crown 3.00 (Q-76 A, UP-OPEN-ARCH-001 v1.1); crown "
         "3.00 below the paint top 3.35: no band part"),
        ("opening", "D-1F-10", None), ("opening", "D-1F-09", None)],
     {"W17": (("8.99655", "8.74145"), "back-derived from the paint line: the paint line still deducts W17 on the "
                                      "pre-Q-76 outline (T-292 owner G1 basis), not the 4.4361 .. 9.858 bound")}),
    ("1F-13", "1F", "39.45", F1, [("held", "L-1F-01", "1.0"), ("opening", "D-1F-05", None),
                                  ("opening", "D-1F-08", None), ("opening", "D-1F-09", None),
                                  ("fixed2", "W15 + W16", ("8.726", "8.726"), ("0", "0"),
                                   "arched outlines 4.363 each (T-238 delta), head 3.10 below the paint top"),
                                  ("opening", "D-1F-03", None), ("fixed2", "D-1F-02", ("0.924", "0.924"), ("0", "0"),
                                                                 "door part on this face (T-556 ledger)")], {}),
    ("2F-03", "2F", "18.9", F1, [("opening", "D-2F-02", None), ("opening", "D-2F-03", None), ("opening", "W29", None),
                                 ("beam", "B2", "0.2", "0.2", "0.24", 2, 2)], {}),
    ("2F-01", "2F", "9.009", F1, [("held", "L-2F-01", "1.0"), ("opening", "D-2F-02", None),
                                  ("opening", "D-2F-01", None), ("beam", "B15", "0.2", "0.2", "1.04", 2, 0)], {}),
]
ELEMENT = {r: (f"HL:WALL_FINISH:{r.replace('-', '_')}:PLASTER", f"HL:WALL_FINISH:{r.replace('-', '_')}:PAINT")
           for r, *_ in DRY}
# openings whose sill / head the T-292 merged_size does not print (T-201 heads / T-128 r3 doors are printed for the rest)
GEOM_TYPED = {"D-GF-08": ("1.0", "0.0", "2.2", "T-556 ledger 2.20 m2 (door 1.0 x 2.2)"),
              "D-GF-13": ("1.0", "0.0", "2.2", "T-556 ledger 2.20 m2 (door 1.0 x 2.2)"),
              "D-GF-14": ("0.8", "0.0", "2.2", "T-556 ledger 1.76 m2 (door 0.8 x 2.2)"),
              "D-GF-01": ("1.0", "0.0", "2.2", "T-556 ledger 2.20 m2 (door 1.0 x 2.2)"),
              "D-1F-05": ("0.9", "0.0", "2.2", "T-556 ledger 1.98 m2 (door 0.9 x 2.2)"),
              "D-1F-08": ("0.9", "0.0", "2.2", "T-556 ledger 1.98 m2 (door 0.9 x 2.2)"),
              "D-1F-09": ("0.9", "0.0", "2.2", "T-556 ledger 1.98 m2 (door 0.9 x 2.2)"),
              "D-2F-02": ("0.9", "0.0", "2.2", "T-556 ledger 1.98 m2 (door 0.9 x 2.2)"),
              "D-2F-03": ("0.8", "0.0", "2.2", "T-556 ledger 1.76 m2 (door 0.8 x 2.2)")}
# stair shaft (Q-72: full exposed height, no false ceiling inside the shaft) and its 2F decor band under the roof:
# 0.15 m (T-173 paint top) x faces W 5.20 + E 5.20 + N 2.50 = 12.90 lm, + the pier-return band 0.015 (T-680 returns
# plaster 0.394 / 0.404 vs paint 0.379 / 0.389)
SHAFT_2F_BAND = ("0.15", "12.90", "0.015")
# returns with wet rooms on both sides (T-634 / R-T709-4 NOT_ESTABLISHED): the reveal may be tiled
FLOOR_RE = re.compile(r"(GF|1F|2F|ST_GF|ST_1F|ST_2F)")


def _pinned(p):
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != PINS[p]:
        raise SystemExit(f"input changed: {p.relative_to(ROOT)} sha256 {h} (pinned {PINS[p]})")
    return p


def _ledger():
    out = {}
    with open(_pinned(OPEN), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.setdefault((r["room"], r["opening_id"]), r)
            out.setdefault(("*", r["opening_id"]), r)
    return out


def _geom(led, room, oid, key):
    r = led.get((key or room, oid)) or led.get(("*", oid))
    m = re.match(r"w ([\d.]+) sill ([\d.]+) head ([\d.]+)", (r or {}).get("merged_size", ""))
    if m:
        return m.group(1), m.group(2), m.group(3), f"T-292 ledger {r['room']} {oid}: {r['merged_size']} ({r['merged_source']})"
    if oid in GEOM_TYPED:
        return GEOM_TYPED[oid]
    raise SystemExit(f"no geometry for {room} {oid}")


def _floor(element):
    if element.startswith(("HL:WALL_FINISH:ST_", "PAINT-BAND", "PLASTER-BAND")):
        return {"ST_GF": "GF", "ST_1F": "1F", "ST_2F": "2F"}.get(element.split(":")[2][:5], "GF") \
            if element.startswith("HL:") else "GF"
    if element.startswith("HL:WALL_FINISH:"):
        return element.split(":")[2][:2]
    if element.startswith(("FENCE", "GF-FACADE", "1F-FACADE", "2F-FACADE")):
        return "EXT"
    return element[:2]


def _val(x):
    """line -> (lo, hi) or None (blank) or 'EXCLUDED'."""
    if x["class"] == "EXCLUDED":
        return "EXCLUDED"
    if x["class"] == "RELEASED":
        v = D(x["measured_net"])
        return (v, v)
    if x["held_low"] is None or x["held_high"] is None:
        return None
    return (D(x["held_low"]), D(x["held_high"]))


def _s(t):
    return None if t is None else [str(q6(t[0])), str(q6(t[1]))]


def dry_room(led, row, lines):
    room, floor, lm, H, items, eng = row
    L = D(lm)
    pl, pt = (D(H[0]), D(H[1])), (D(H[2]), D(H[3]))
    pel, tel = ELEMENT[room]
    P, Q = lines[pel], lines[tel]
    assert P["value"] not in (None, "EXCLUDED") and Q["value"] not in (None, "EXCLUDED"), room
    ends = []
    led_items = []
    for e in (0, 1):
        band_h = pl[e] - pt[e]
        sum_pl = sum_band = sum_rule = sum_eng = D(0)
        named = []
        rows = []
        for it in items:
            kind = it[0]
            if kind == "opening":
                w, s, h, src = _geom(led, room, it[1], it[2])
                a_pl = D(w) * R.overlap(s, h, 0, pl[e])
                a_b = R.opening_band_part(w, s, h, pt[e], pl[e])
                a_eng = R.opening_paint_part(w, s, h, pt[e])
                name = it[1]
            elif kind == "held":
                w = D(it[2])
                a_pl, a_b, a_eng = (w * pl[e], w * band_h, w * pt[e]) if e == 0 else (D(0), D(0), D(0))
                name, src = it[1], f"width {it[2]}, no printed height (T-292 'h HELD'): full at the low end, 0 high"
            elif kind == "fixed2":
                a_pl, a_b = D(it[2][e]), D(it[3][e])
                a_eng = a_pl - a_b
                name, src = it[1], it[4]
            elif kind == "beam":
                _, mark, w_lo, w_hi, depth, n_lo, n_hi = it
                w, n = (D(w_lo), n_lo) if e == 0 else (D(w_hi), n_hi)
                inb, below = R.beam_end_split(w, depth, band_h, n)
                a_pl, a_b, a_eng = inb + below, inb, D(0)
                name, src = f"beam {mark}", (f"T-556 BEAM_ENDS {mark} b {w} x depth below the soffit {depth}, {n} "
                                              f"ends; the paint line deducts no beam end")
            else:
                raise SystemExit(kind)
            a_rule = a_pl - a_b                       # the rule's paint deduction on this face (R-T740-2)
            if name in eng:
                a_eng = D(eng[name][0][e])
            sum_pl += a_pl
            sum_band += a_b
            sum_rule += a_rule
            sum_eng += a_eng
            diff = a_rule - a_eng                     # engine paint - rule paint from this item
            if diff != 0:
                cause = "BEAM_END_BELOW_CEILING" if kind == "beam" else "OPENING_BASIS_MISMATCH"
                named.append((cause, diff, name))
            rows.append({"item": name, "plaster_ded": str(q6(a_pl)), "band_part": str(q6(a_b)),
                         "rule_paint_ded": str(q6(a_rule)), "engine_paint_ded": str(q6(a_eng)),
                         "source": eng[name][1] if name in eng else src})
        p_reb = L * pl[e] - sum_pl
        q_reb = L * pt[e] - sum_eng
        p_line, q_line = P["value"][e], Q["value"][e]
        if q6(p_reb) != q6(p_line):
            raise SystemExit(f"{room} end {e}: plaster rebuild {p_reb} != line {p_line}")
        gross, bnd = R.band(L, pl[e], pt[e], [sum_band])
        rnd = q_line - q_reb
        if rnd:
            named.append(("LEDGER_ROUNDING", rnd, "paint line vs its own ledger (L x H - deductions)"))
        al = R.allocate(p_line, q_line, bnd, 0, [(c, v) for c, v, _ in named])
        ends.append({"end": ("low", "high")[e], "plaster_top": str(pl[e]), "paint_top": str(pt[e]),
                     "band_gross": str(gross), **{k: v for k, v in al.items() if k != "named"},
                     "named": [{"cause": c, "m2": str(q6(v)), "what": n} for c, v, n in named], "items": rows})
        led_items = rows
    return {"room": room, "floor": floor, "face_lm": lm, "plaster_line": P["line_id"], "paint_line": Q["line_id"],
            "plaster": _s(P["value"]), "engine_paint": _s(Q["value"]), "paint_class": Q["class"],
            "rule_paint": [ends[0]["rule_paint"], ends[1]["rule_paint"]], "ends": ends}


def build():
    idx = json.loads(_pinned(INDEX).read_text(encoding="utf-8"))
    t709 = json.loads(_pinned(T709).read_text(encoding="utf-8"))
    led = _ledger()
    lines = {}
    for x in idx["lines"]:
        if x["item_code"] in CODES:
            lines[x["element_id"]] = {"line_id": x["line_id"], "code": x["item_code"], "class": x["class"],
                                      "value": _val(x)}
    used = set()
    faces = []

    def face(cls, floor, pl_el, pt_el, plaster, eng, rule, band_lo_hi, tiled_lo_hi, named, note):
        """one face record (both ends); plaster / eng / rule as (lo, hi), None (blank) or 'EXCLUDED'."""
        rec = {"class": cls, "floor": floor, "plaster_element": pl_el, "paint_element": pt_el,
               "plaster_line": lines[pl_el]["line_id"] if pl_el else None,
               "paint_line": lines[pt_el]["line_id"] if pt_el else None,
               "plaster": plaster if isinstance(plaster, str) else _s(plaster),
               "engine_paint": eng if isinstance(eng, str) else _s(eng),
               "rule_paint": rule if isinstance(rule, str) else _s(rule),
               "band": _s(band_lo_hi), "tiled": _s(tiled_lo_hi), "named": named, "note": note}
        for el in (pl_el, pt_el):
            if el:
                used.add(el)
        faces.append(rec)
        return rec

    def num(v):
        return None if v in (None, "EXCLUDED") else v

    # ---- DRY rooms
    dry = [dry_room(led, row, lines) for row in DRY]
    for r in dry:
        pe, te = ELEMENT[r["room"]]
        lo, hi = r["ends"]
        rule = (D(lo["rule_paint"]), D(hi["rule_paint"]))
        named = [{"end": e["end"], **n} for e in r["ends"] for n in e["named"]]
        face("DRY", r["floor"], pe, te, lines[pe]["value"], lines[te]["value"], (min(rule), max(rule)),
             (D(lo["band"]), D(hi["band"])), (D(0), D(0)), named,
             f"face {r['face_lm']} lm; residual {lo['residual']} / {hi['residual']}")
    # ---- STAIR SHAFT
    for st in ("ST_GF", "ST_1F", "ST_2F"):
        pe, te = f"HL:WALL_FINISH:{st}:PLASTER", f"HL:WALL_FINISH:{st}:PAINT"
        P, Q = lines[pe]["value"], lines[te]["value"]
        if st == "ST_2F":
            b = D(SHAFT_2F_BAND[0]) * D(SHAFT_2F_BAND[1]) + D(SHAFT_2F_BAND[2])
            note = ("decor band under the roof 0.15 x 12.90 lm (T-173 faces W 5.20 + E 5.20 + N 2.50) + pier returns "
                    "0.015 (T-680)")
        else:
            b, note = D(0), "Q-72: full exposed height through the shaft, no false ceiling: no band"
        rule = (P[0] - b, P[1] - b)
        named = []
        for e in (0, 1):
            al = R.allocate(P[e], Q[e], b, 0, [])
            if al["residual"] != 0:
                named.append({"end": ("low", "high")[e], "cause": "LEDGER_ROUNDING", "m2": str(al["residual"]),
                              "what": "untraced"})
        face("SHAFT", st[3:], pe, te, P, Q, rule, (b, b), (D(0), D(0)), named, note)
    # ---- DOUBLE-HEIGHT band (R-T709-1): the GF-08 band strip over the void has no false ceiling
    dh = t709["a_double_height"]
    pe = next(k for k in lines if k.startswith("PLASTER-BAND@"))
    te = next(k for k in lines if k.startswith("PAINT-BAND@"))
    P, Q = lines[pe]["value"], lines[te]["value"]
    lm_lo = D(dh["gf_solid_under_lm"])
    lm_hi = lm_lo + D("0.15")                  # column returns proud 0.05 (T-709 high end)
    gf_band_h = D("4.29") - D("3.65")
    contact = D("0.052900")                    # ST-02 landing against the wall in the band (T-709 low end, 0 .. 0.0529)
    strip = (lm_lo * gf_band_h - contact, lm_hi * gf_band_h)
    rule = (P[0] + strip[0], P[1] + strip[1])
    named = []
    for e in (0, 1):
        al = R.allocate(P[e], Q[e], -strip[e], 0, [])
        named.append({"end": ("low", "high")[e], "cause": "VOID_NO_CEILING", "m2": str(q6(-strip[e])),
                      "what": "GF-08 band strip over the void returned as paint (no false ceiling over a void)",
                      "residual": str(al["residual"])})
    face("DOUBLE_HEIGHT", "GF", pe, te, P, Q, rule, (-strip[0], -strip[1]), (D(0), D(0)), named,
         f"void strip {lm_lo} .. {lm_hi} lm x 0.64 (GF plaster 4.29 - paint 3.65); low end less the ST-02 landing "
         f"contact 0.0529 (T-709, 0 .. 0.0529 bound: its low end), high end with the 0.15 lm column returns")
    # ---- WET rooms, RETURNS, EXCLUDED, EXTERIOR: by element suffix
    wet_both = {r["face_id"] for r in t709["c_return_paint"]["rows"]
                if "NOT_ESTABLISHED" in str((r.get("paint_row") or {}).get("flag", ""))}
    assert len(wet_both) == 5, wet_both     # T-634: 5 doors with wet rooms on both sides
    for el in sorted(lines):
        if el in used:
            continue
        ln = lines[el]
        if ln["code"] != "FIN.PLASTER" and ln["code"] not in ("FIN.EXT.FINISH", "EXT.FENCE.PLASTER"):
            continue
        fl = _floor(el)
        v = ln["value"]
        if ln["code"] == "FIN.EXT.FINISH":
            face("EXTERIOR", "EXT", el, None, v, None, None, None, None, [],
                 "one facade line per floor, finish and quantity HELD blank; Sigma = the exterior plaster area "
                 "(owner notes 2026-10-21): external paint follows the external plaster face by face")
            continue
        if ln["code"] == "EXT.FENCE.PLASTER":
            te = el.replace(":PLASTER", ":PAINT")
            face("EXTERIOR", "EXT", el, te, v, lines[te]["value"], None if v is None else v, None, None, [],
                 "fence face: paint = plaster face by face; both HELD blank")
            continue
        if el.endswith(":JAMBS_HEAD:HELD") or el.endswith(":door jambs and head") or ":JAMBS_HEAD:VALUED" in el:
            te = el + ":RETURN_PAINT"
            Q = lines[te]["value"]
            if v is None:
                face("RETURN", fl, el, te, None, None, None, None, None, [], "plaster return blank: paint HELD by name")
                continue
            if el in wet_both:
                face("RETURN", fl, el, te, v, Q, (D(0), v[1]), (D(0), D(0)), (v[1], D(0)),
                     [{"end": "low", "cause": "TILED", "m2": str(q6(v[1])),
                       "what": "wet rooms on both sides: the reveal may be tiled (not established), HELD"}],
                     "reading A; HELD 0 .. plaster (tiled part not established)")
                continue
            face("RETURN", fl, el, te, v, Q, v, (D(0), D(0)), (D(0), D(0)),
                 [{"end": "low", "cause": "RETURN_RULE_RESTATED", "m2": str(q6(Q[0] - v[0])),
                   "what": "engine low end 0 (frame-covered depth); under the rule the reveal paint = its plaster"}],
                 "reading A (owner words: 'the Area is the same'); reading B (board paraphrase 'reveals' as lm) "
                 "would give 0 m2 + lm: HELD for the Checker / Lead reading")
            continue
        if el.endswith(":plaster band above ceiling"):
            face("WET_BAND", fl, el, None, v, (D(0), D(0)) if v is not None else None,
                 (D(0), D(0)) if v is not None else None, v, (D(0), D(0)) if v is not None else None,
                 [], "band above the ceiling: no paint (Q-72 / T-690)")
            continue
        base = el.rsplit(":", 1)[0]
        cands = [k for k in lines if k.startswith(base + ":") and lines[k]["code"] == "FIN.PAINT"]
        te = cands[0] if cands else None
        if v == "EXCLUDED":
            face("EXCLUDED", fl, el, te, "EXCLUDED", lines[te]["value"] if te else None, "EXCLUDED", None, None, [],
                 "superseded room-route line (EXCLUDED in the candidate)")
            continue
        if el == "HL:WALL_FINISH:GF_07:PLASTER" or (te and te.endswith("paint above wall tile")):
            face("WET_RENDER", fl, el, te, v, (D(0), D(0)), (D(0), D(0)) if v is not None else None, (D(0), D(0)),
                 v, [], "levelling render under full-height porcelain (UP-FIN-WALL-001 1.8.0, Q-48 A: tile to the "
                        "ceiling; R-T701-3): the whole face is tiled, no paint face")
            continue
        raise SystemExit(f"unclassified plaster face {el}")
    # paint lines not reached through a plaster face
    left = sorted(k for k in lines if k not in used and lines[k]["code"] in ("FIN.PAINT", "EXT.FENCE.PAINT"))
    for el in left:
        ln = lines[el]
        if ln["value"] == "EXCLUDED":
            face("EXCLUDED", _floor(el), None, el, "EXCLUDED", "EXCLUDED", "EXCLUDED", None, None, [],
                 "wet room 'paint above wall tile' / room-route paint: EXCLUDED in the candidate, no paint face")
            continue
        raise SystemExit(f"paint line with no plaster face: {el}")

    # ---- census and totals
    def addr(acc, key, t):
        if t is None or isinstance(t, str):
            return
        a = acc.setdefault(key, [D(0), D(0)])
        a[0] += D(t[0])
        a[1] += D(t[1])

    def census(code):
        out = {"released": D(0), "held": [D(0), D(0)], "blank": 0, "excluded": 0, "lines": 0}
        for x in idx["lines"]:
            if x["item_code"] != code:
                continue
            out["lines"] += 1
            v = _val(x)
            if v == "EXCLUDED":
                out["excluded"] += 1
            elif v is None:
                out["blank"] += 1
            elif x["class"] == "RELEASED":
                out["released"] += v[0]
            else:
                out["held"][0] += v[0]
                out["held"][1] += v[1]
        return {"lines": out["lines"], "released": str(q6(out["released"])), "held": _s(out["held"]),
                "blank": out["blank"], "excluded": out["excluded"],
                "total": _s((out["released"] + out["held"][0], out["released"] + out["held"][1]))}

    totals, by_floor, by_class = {}, {}, {}
    for f in faces:
        for key, t in (("plaster", f["plaster"]), ("engine_paint", f["engine_paint"]), ("rule_paint", f["rule_paint"])):
            if f["class"] == "EXTERIOR" and key == "plaster" and f["paint_element"] is None:
                pass
            addr(totals, key, t)
            addr(by_floor.setdefault(f["floor"], {}), key, t)
            addr(by_class.setdefault(f["class"], {}), key, t)
        if f["class"] in ("DRY", "SHAFT", "DOUBLE_HEIGHT", "WET_BAND", "WET_RENDER", "RETURN"):
            addr(by_class[f["class"]], "band", f["band"])
            addr(by_class[f["class"]], "tiled", f["tiled"])
    blank = {k: sum(1 for f in faces if f[k] is None) for k in ("plaster", "engine_paint", "rule_paint")}
    # FIN codes only (the board's figures): exterior / fence lines are all blank
    fin_plaster = census("FIN.PLASTER")
    fin_paint = census("FIN.PAINT")
    tp = totals["plaster"]
    assert _s(tp) == fin_plaster["total"], (_s(tp), fin_plaster["total"])
    te_ = totals["engine_paint"]
    assert _s(te_) == fin_paint["total"], (_s(te_), fin_paint["total"])
    # gap allocation over every face: gap = band + tiled - (engine - rule)
    alloc = {}
    for e in (0, 1):
        gap = tp[e] - te_[e]
        b = sum((D(f["band"][e]) for f in faces if f["band"]), D(0))
        t = sum((D(f["tiled"][e]) for f in faces if f["tiled"]), D(0))
        causes = {}
        for f in faces:
            for n in f["named"]:
                if n["end"] == ("low", "high")[e] and n["cause"] not in ("TILED", "VOID_NO_CEILING"):
                    causes[n["cause"]] = causes.get(n["cause"], D(0)) + D(n["m2"])
        em = te_[e] - totals["rule_paint"][e]
        resid = em - sum(causes.values(), D(0))
        ident = gap - b - t + em
        if ident != 0:
            raise SystemExit(f"face records inconsistent: gap - band - tiled + (engine - rule) = {ident}")
        alloc[("low", "high")[e]] = {"gap": str(q6(gap)), "band_incl_void_credit": str(q6(b)),
                                     "tiled": str(q6(t)), "engine_minus_rule": str(q6(em)),
                                     "engine_minus_rule_by_cause": {k: str(q6(v)) for k, v in sorted(causes.items())},
                                     "residual": str(q6(resid))}
    # released and held kept apart, by the class of the engine's paint line on the face
    split = {"RELEASED": {"engine_paint": [D(0), D(0)], "rule_paint": [D(0), D(0)], "lines": 0},
             "HELD": {"engine_paint": [D(0), D(0)], "rule_paint": [D(0), D(0)], "lines": 0}}
    for f in faces:
        if not f["paint_element"] or isinstance(f["engine_paint"], str) or f["engine_paint"] is None:
            continue
        if lines[f["paint_element"]]["class"] == "EXCLUDED":
            continue                           # wet faces: the engine's paint line is EXCLUDED (no paint face)
        k = "RELEASED" if lines[f["paint_element"]]["class"] == "RELEASED" else "HELD"
        split[k]["lines"] += 1
        for key in ("engine_paint", "rule_paint"):
            if f[key] is not None and not isinstance(f[key], str):
                split[k][key][0] += D(f[key][0])
                split[k][key][1] += D(f[key][1])
    split = {k: {"lines": v["lines"], "engine_paint": _s(v["engine_paint"]), "rule_paint": _s(v["rule_paint"])}
             for k, v in split.items()}
    out = {"schema": "URBAN_T740_PAINT_RULE_V1", "candidate": idx["candidate_version"],
           "rule": {"id": R.RULE_ID, "version": R.RULE_VERSION, "file": R.RULEBOOK},
           "inputs_sha256_16": {str(p.relative_to(ROOT)): h[:16] for p, h in PINS.items()},
           "census_board": {"FIN.PLASTER": fin_plaster, "FIN.PAINT": fin_paint},
           "totals": {k: _s(v) for k, v in totals.items()}, "paint_by_engine_class": split,
           "blank_faces": blank,
           "by_floor": {fl: {k: _s(v) for k, v in d.items()} for fl, d in sorted(by_floor.items())},
           "by_class": {c: {k: _s(v) for k, v in d.items()} for c, d in sorted(by_class.items())},
           "allocation": alloc, "dry_rooms": dry, "faces": faces}
    return out


def md(o):
    L = [f"# T-740 paint area rule {o['rule']['id']} {o['rule']['version']} on {o['candidate']} (generated; research, "
         "unwired)", "",
         "Rule: paint m2 = plaster m2 of the same face - band above a false ceiling - tiled part; corners and edges are "
         "lm, never area. Ends paired by scenario (low with low).", "",
         "## Totals (m2; FIN.PLASTER / FIN.PAINT, every non-excluded line once)", "",
         "| | plaster | engine paint | rule paint |", "|---|---|---|---|"]
    t = o["totals"]
    L.append(f"| all | {t['plaster'][0]} .. {t['plaster'][1]} | {t['engine_paint'][0]} .. {t['engine_paint'][1]} | "
             f"{t['rule_paint'][0]} .. {t['rule_paint'][1]} |")
    for fl, d in o["by_floor"].items():
        g = lambda k: (f"{d[k][0]} .. {d[k][1]}" if k in d else "-")  # noqa: E731
        L.append(f"| {fl} | {g('plaster')} | {g('engine_paint')} | {g('rule_paint')} |")
    for k, v in o["paint_by_engine_class"].items():
        L.append(f"| paint lines engine {k} ({v['lines']}) | | {v['engine_paint'][0]} .. {v['engine_paint'][1]} | "
                 f"{v['rule_paint'][0]} .. {v['rule_paint'][1]} |")
    L += ["", f"Blank faces: {o['blank_faces']}", "", "## By class", "", "| class | plaster | engine paint | rule paint | band | tiled |",
          "|---|---|---|---|---|---|"]
    for c, d in o["by_class"].items():
        g = lambda k: (f"{d[k][0]} .. {d[k][1]}" if k in d else "-")  # noqa: E731
        L.append(f"| {c} | {g('plaster')} | {g('engine_paint')} | {g('rule_paint')} | {g('band')} | {g('tiled')} |")
    L += ["", "## Gap allocation (plaster - engine paint = band + tiled - (engine - rule), per end)", ""]
    for e, a in o["allocation"].items():
        L.append(f"- {e}: gap {a['gap']} = band {a['band_incl_void_credit']} + tiled {a['tiled']} - "
                 f"(engine - rule) {a['engine_minus_rule_by_cause']}; residual {a['residual']}")
    L += ["", "## Dry rooms (per end)", "", "| room | end | plaster | engine paint | band | rule paint | named (engine - rule) | residual |",
          "|---|---|---|---|---|---|---|---|"]
    for r in o["dry_rooms"]:
        for i, e in enumerate(r["ends"]):
            nm = "; ".join(f"{n['cause']} {n['m2']} ({n['what']})" for n in e["named"]) or "-"
            L.append(f"| {r['room']} | {e['end']} | {r['plaster'][i]} | {r['engine_paint'][i]} | {e['band']} | "
                     f"{e['rule_paint']} | {nm} | {e['residual']} |")
    L += ["", "## Faces", "", "| class | floor | plaster element | plaster | engine paint | rule paint | named | note |",
          "|---|---|---|---|---|---|---|---|"]
    for f in o["faces"]:
        nm = "; ".join(f"{n['end']} {n['cause']} {n['m2']}" for n in f["named"]) or "-"
        L.append(f"| {f['class']} | {f['floor']} | {f['plaster_element'] or f['paint_element']} | {f['plaster']} | "
                 f"{f['engine_paint']} | {f['rule_paint']} | {nm} | {f['note']} |")
    return "\n".join(L) + "\n"


def main(argv):
    o = build()
    js = json.dumps(o, indent=1, ensure_ascii=False, sort_keys=False, default=str) + "\n"
    mdt = md(o)
    if "--check" in argv:
        ok = OUT_JSON.read_text(encoding="utf-8") == js and OUT_MD.read_text(encoding="utf-8") == mdt
        print("T740 outputs " + ("match" if ok else "DIFFER"))
        return 0 if ok else 1
    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(js, encoding="utf-8")
    OUT_MD.write_text(mdt, encoding="utf-8")
    print(json.dumps({"totals": o["totals"], "allocation": o["allocation"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
