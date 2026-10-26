"""T-306 suspended-slab reinforcement BOUND decomposition (research ledger, lane S; every villa).

Physical element: the bars of one suspended slab panel in one direction, split into three bar populations that the
candidate carries as three BOUND lines each: the bottom mesh (printed 'n o d/m' label, p.15 curtailment, the half that
crosses a continuous beam), the top bars over the supports (sheet note 2 'top 5 o 10/m over the beams for one third of
the span' vs the p.15 TYP. SLAB ON BEAMS DETAIL) and the development / anchorage at the bar ends (note 9 40 d .. 70 d).

The question is not 'how many kg' but WHY each line is a range: every kg of the spread high - low is assigned to the
one unprinted value that opens it, residual 0 (only storage rounding of the 3 dp ledger figures, named).

Rules (research rules R306-1 .. R306-8, stdlib only, no rule-file version; provenance T-152, T-179, T-297, owner
Q-71 12:36 / OWNER_RULE_REBAR_2026-10-24 s.2 / s.6):
  R306-1  a rate label 'n o d/m' is a distribution rate, never a count: its count is a BOUND between the defensible
          boundary-bar readings A = ceil(rate x W) (bars centred in their strips) and B = A + 1 (a bar on each edge);
          reading it as n bars in all is refused (count_from_label).
  R306-2  a count label 'n o d' with a drawn bar length is DRAWING_CONFIRMED (kg = n x L x d^2 / 162); a bare label in
          a mesh context ('5 o 10', no '/m') carries both readings (n in all, n per metre) and stays a BOUND.
  R306-3  layers: '(T&B)' = two layers; one record per (panel, direction, layer set, population); two records with
          one key, or two layers booked on one single-layer record, are refused (defect B14, de-dup of identical
          labels).
  R306-4  an end length (development / anchorage / lap) is DRAWING_CONFIRMED only from a drawn length; note 9 (the
          starter-bar development note) is a BOUND with datum HELD; the owner 40 d / 60 d lap convention is a
          PROPOSAL (OWNER_RULE_REBAR s.2) and is refused as a measured or confirmed basis.
  R306-5  a top-bar extent that no sheet prints is never given a value: unprinted -> HELD / BOUND, a value offered
          with no printed source is refused.
  R306-6  a bound must contain every defensible reading of its own line (lo <= each reading <= hi); a reading outside
          it is reported by name (BOUND_EXCLUDES_READING), never dropped.
  R306-7  decomposition closes: the named causes of a line sum to its high - low to storage rounding (0.0015 kg per
          3 dp figure involved); otherwise the line is refused.
  R306-8  kg internal, t = kg / 1000 once; causes are summed per cause only, never into a quantity.
"""

import csv
import json
import math
import re
from collections import defaultdict

ROUND_TOL = 0.0015            # kg: one 3 dp storage rounding per figure, two figures per difference
DEV_K = (40, 70)              # p.8 note 9 (as carried by the candidate)

# cause codes, each with the single unprinted value that opens it
CAUSES = {
    "COUNT_CONVENTION": "boundary-bar positions of an 'n o d/m' mesh (first / last bar from the support face) are not "
                        "printed: A = ceil(rate x W) centred vs B = A + 1 on both edges (Q-71 governs footings and "
                        "links, owner 12:36; not extended to slabs, ERS s.3)",
    "LABEL_MEANING": "a slab label printed without '/m' ('5 o 10'): 5 bars in all or 5 per metre is not printed",
    "TOP_NOTE2_WORDING": "sheet note 2 'one third of the span': whole bar (L/6 each side, reading i) or each side "
                         "(L/3 each side, reading ii) is not printed",
    "TOP_NOTE2_VS_P15": "sheet note 2 and the p.15 typical detail (0.30 max(L1, L2) continuous, 0.25 L1 end) give "
                        "different extents: two drawings of the set disagree (designer item)",
    "TOP_CROSSING": "the part of the top bar over the beam band: exists only under the 'each side' readings, whose "
                    "governing extent is the open item above",
    "ANCHORAGE_LENGTH": "the bar-end length is not dimensioned for slab bars: note 9 (40 d .. 70 d) names the starter-"
                        "bar situations (owner 2026-10-24 s.6 (1)); p.15 draws edge-beam anchorage to 40 mm of the "
                        "far face, no length",
    "STORAGE_ROUNDING": "3 dp storage of the ledger figures (not an engineering cause)",
}


def kgm(d_mm):
    """unit mass d^2 / 162 kg/m (the project method, as the candidate lines)."""
    return d_mm * d_mm / 162.0


# ---------------------------------------------------------------------------------------------- R306-1 .. R306-5
_RATE = re.compile(r"^\s*(\d+)\s*[øoØ]\s*(\d+)\s*/\s*m\b")
_COUNT = re.compile(r"^\s*(\d+)\s*[øoØ]\s*(\d+)\s*(?!/)")


def parse_label(text):
    """-> dict(kind RATE | COUNT_OR_BARE, n, d, layers). '(T&B)' doubles the layers (R306-3)."""
    layers = 2 if "T&B" in text.replace(" ", "") else 1
    m = _RATE.match(text)
    if m:
        return dict(kind="RATE", n=int(m.group(1)), d=int(m.group(2)), layers=layers)
    m = _COUNT.match(text)
    if m:
        return dict(kind="COUNT_OR_BARE", n=int(m.group(1)), d=int(m.group(2)), layers=layers)
    raise ValueError(f"label {text!r}: not a bar notation")


def count_from_label(label, spread_m=None, mesh_context=True):
    """R306-1 / R306-2. Returns ('COUNT', n) for a count label outside a mesh, ('BOUND', a, b) for a rate (A, B) and
    ('READINGS', n, a, b) for a bare label in a mesh context. A rate read as a count is refused (spread missing)."""
    p = parse_label(label) if isinstance(label, str) else label
    if spread_m is not None and spread_m > 100.0:
        raise ValueError(f"UNIT_REFUSED: distribution width {spread_m} reads as mm, not m")
    if p["kind"] == "RATE":
        if spread_m is None or spread_m <= 0:
            raise ValueError("RATE_AS_COUNT_REFUSED: 'n o d/m' is a distribution rate; a count needs the "
                             "distribution width (never n bars in all)")
        a = int(math.ceil(p["n"] * spread_m - 1e-9))
        return ("BOUND", a, a + 1)
    if mesh_context and spread_m:
        a = int(math.ceil(p["n"] * spread_m - 1e-9))
        return ("READINGS", p["n"], a, a + 1)
    return ("COUNT", p["n"])


def component(label, bar_length_m, spread_m=None, mesh_context=False, length_source=None):
    """kg status of one bar population whose bars all have the drawn length bar_length_m (R306-2 / R306-5).
    -> dict(status DRAWING_CONFIRMED | BOUND, kg | low/high)."""
    if bar_length_m is None or length_source in (None, "", "UNPRINTED"):
        if bar_length_m is not None:
            raise ValueError("UNPRINTED_EXTENT_REFUSED: a bar length offered with no printed source")
        return dict(status="HELD", reason="bar length not printed")
    p = parse_label(label)
    u = kgm(p["d"]) * p["layers"]
    c = count_from_label(p, spread_m, mesh_context)
    if c[0] == "COUNT":
        return dict(status="DRAWING_CONFIRMED", kg=c[1] * bar_length_m * u, count=c[1], source=length_source)
    lo, hi = min(c[1:]), max(c[1:])
    return dict(status="BOUND", low=lo * bar_length_m * u, high=hi * bar_length_m * u, counts=c[1:],
                datum="boundary-bar convention not printed", datum_status="HELD")


def end_length(basis, d_mm, length_m=None):
    """R306-4: bar-end length basis -> (status, low_m, high_m)."""
    if basis == "DRAWN":
        if length_m is None:
            raise ValueError("DRAWN end length without a length")
        return ("DRAWING_CONFIRMED", length_m, length_m)
    if basis == "NOTE9":
        return ("BOUND", DEV_K[0] * d_mm / 1000.0, DEV_K[1] * d_mm / 1000.0)
    if basis == "OWNER_40D_60D":
        raise ValueError("LAP_PROPOSAL_REFUSED: the owner 40 d / 60 d lap method is a proposal under assessment "
                         "(OWNER_RULE_REBAR_2026-10-24 s.2), not an approved basis")
    raise ValueError(f"end basis {basis!r} not recognised")


def bar_end(support, basis, d_mm, length_m=None):
    """R306-4 by end kind (p.15 TYP. SLAB ON BEAMS DETAIL, drawing-derived): CONTINUOUS -> no development (50 % stop
    0.125 L short, the balance runs on = the crossing half of the bottom line); a length booked there is refused.
    NON_CONTINUOUS -> the drawn anchorage (edge-beam width - 40 mm + hook leg) or HELD; OPENING_EDGE -> HELD unless a
    detail is drawn."""
    if support == "CONTINUOUS":
        if basis not in (None, "NONE"):
            raise ValueError("CONTINUOUS_END_LENGTH_REFUSED: the typical detail draws no development at a continuous "
                             "support (stop short / run on)")
        return ("NOT_APPLICABLE", 0.0, 0.0)
    if support in ("NON_CONTINUOUS", "OPENING_EDGE"):
        if basis in (None, "NONE"):
            return ("HELD", None, None)
        return end_length(basis, d_mm, length_m)
    raise ValueError(f"support kind {support!r} not recognised")


def check_keys(records):
    """R306-3: one record per (element, direction, layers, population); a two-layer label on a one-layer record is
    refused."""
    seen = set()
    for r in records:
        k = (r["element"], r["part"], r["layers"], r["component"])
        if k in seen:
            raise ValueError(f"DUPLICATE_RECORD_REFUSED: {k} booked twice (two layers merged under one label?)")
        seen.add(k)
        lab = r.get("printed")
        if lab and parse_label(lab)["layers"] != r["layers"]:
            raise ValueError(f"LAYER_MISMATCH_REFUSED: {r['element']} {r['part']} label {lab!r} vs layers "
                             f"{r['layers']}")
    return True


# ---------------------------------------------------------------------------------------------- R306-6 / R306-7
def close(line_id, low, high, causes, n_figures):
    """R306-7: the causes (dict code -> kg, signed) must sum to high - low within the storage rounding of the figures;
    the remainder is booked as STORAGE_ROUNDING. Returns the completed cause dict."""
    for k in causes:
        if k not in CAUSES:
            raise ValueError(f"{line_id}: unknown cause {k}")
    spread = high - low
    if spread < -1e-9:
        raise ValueError(f"{line_id}: high below low")
    rest = spread - sum(causes.values())
    if abs(rest) > ROUND_TOL * n_figures + 1e-9:
        raise ValueError(f"{line_id}: causes do not close the spread ({rest:+.6f} kg unexplained)")
    out = dict(causes)
    out["STORAGE_ROUNDING"] = out.get("STORAGE_ROUNDING", 0.0) + rest
    return out


def contains(line_id, low, high, readings, tol=0.0015):
    """R306-6: names every reading outside [low, high]."""
    return [dict(line=line_id, reading=k, kg=round(v, 6), low=low, high=high)
            for k, v in readings.items() if v < low - tol or v > high + tol]


def decompose_bottom(line_id, low, high, kgA, kgB, xA, xB, label_reading_kg=None):
    a, b = kgA + xA, kgB + xB
    c = {"COUNT_CONVENTION": abs(b - a)}
    readings = {"A": a, "B": b}
    if label_reading_kg is not None:
        c["LABEL_MEANING"] = (max(a, b, label_reading_kg) - min(a, b, label_reading_kg)) - abs(b - a)
        readings["label_n_in_all"] = label_reading_kg
    flags = ["SKEW_B_BELOW_A"] if b < a - 1e-9 else []
    return close(line_id, low, high, c, 4 + (1 if label_reading_kg is not None else 0)), \
        contains(line_id, low, high, readings), flags


def decompose_dev(line_id, low, high, nA, nB, d_mm, layers):
    """low = nA x 2 x 40 d, high = nB x 2 x 70 d (the candidate's own basis): count part at 40 d, then the 40 -> 70 d
    part at count B."""
    u = kgm(d_mm) * layers
    count = (nB - nA) * 2 * DEV_K[0] * d_mm / 1000.0 * u
    anch = nB * 2 * (DEV_K[1] - DEV_K[0]) * d_mm / 1000.0 * u
    readings = {"A_40d": nA * 2 * DEV_K[0] * d_mm / 1000.0 * u, "A_70d": nA * 2 * DEV_K[1] * d_mm / 1000.0 * u,
                "B_40d": nB * 2 * DEV_K[0] * d_mm / 1000.0 * u, "B_70d": nB * 2 * DEV_K[1] * d_mm / 1000.0 * u}
    return close(line_id, low, high, {"COUNT_CONVENTION": count, "ANCHORAGE_LENGTH": anch}, 2), \
        contains(line_id, low, high, readings), []


def decompose_top(line_id, low, high, rd, tb_panel=False):
    """rd: {'i': (A, B), 'ii': (A, B), 'p15': (A, B), 'cross': (A, B)} kg. Candidate: low = min over readings at A,
    high = max over readings at B + max crossing. Path: reading i -> ii (note-2 wording) -> the governing high
    reading (note 2 vs p.15) at count A, then count A -> B, then the crossing."""
    names = ("i", "ii", "p15")
    lo_r = min(names, key=lambda k: rd[k][0])
    hi_r = max(names, key=lambda k: rd[k][1])
    c = defaultdict(float)
    # extent at count A, from the low reading to the high reading, via ii
    path = [lo_r]
    if lo_r != "ii" and hi_r != lo_r:
        path.append("ii")
    if hi_r not in path:
        path.append(hi_r)
    for p, q in zip(path, path[1:]):
        code = "TOP_NOTE2_WORDING" if {p, q} == {"i", "ii"} else "TOP_NOTE2_VS_P15"
        c[code] += rd[q][0] - rd[p][0]
    c["COUNT_CONVENTION"] += rd[hi_r][1] - rd[hi_r][0]
    c["TOP_CROSSING"] += max(rd["cross"])
    readings = {f"{k}_{t}": rd[k][j] for k in names for j, t in enumerate("AB")}
    readings.update({f"{k}_{t}+cross": rd[k][j] + rd["cross"][j] for k in ("ii", "p15") for j, t in enumerate("AB")})
    if tb_panel:
        readings["no_note2_bars_over_TB_mesh"] = 0.0
    flags = ["TB_PANEL_NOTE2_OPEN"] if tb_panel else []
    return close(line_id, low, high, dict(c), 3), contains(line_id, low, high, readings), flags


# ---------------------------------------------------------------------------------------------- the ledger
def _rng(text):
    a, b = (float(v) for v in str(text).split()[0].split(".."))
    return a, b


def _top_readings(text):
    out = {}
    for k in ("i", "ii", "p15", "crossing"):
        m = re.search(r"\b%s ([\d.]+)\.\.([\d.]+)" % k, text)
        if not m:
            raise ValueError(f"top reading {k} missing in {text!r}")
        out["cross" if k == "crossing" else k] = (float(m.group(1)), float(m.group(2)))
    return out


def build(basis_rows, t152_rows):
    """basis_rows: the SLABS rows of LINE_BASIS_T297.csv (BOUND only are decomposed); t152_rows: T152_SLAB_STEEL.csv.
    -> (decomposition rows, findings)."""
    t152 = {}
    for r in t152_rows:
        k = (f"SLAB:{r['panel']}", r["direction"])
        if k in t152:
            raise ValueError(f"T-152 row {k} twice")
        t152[k] = r
    out, outside, keyrecs = [], [], []
    for r in basis_rows:
        if r["family"] != "SLABS" or r["basis_status"] != "BOUND":
            continue
        comp, part = (s.strip() for s in r["bar_group"].split("|"))
        t = t152[(r["members"], part)]
        lo, hi = float(r["bound_low_kg"]), float(r["bound_high_kg"])
        d, lay = int(t["d_mm"]), int(t["layers"])
        keyrecs.append(dict(element=r["members"], part=part, layers=lay, component=comp, printed=t["printed"]))
        if comp == "BOTTOM MESH":
            lab = None
            if t["status"] == "HELD_LABEL":
                lab = float(re.search(r"count reading \d+ bars = ([\d.]+) kg", t["note"]).group(1))
            causes, outs, flags = decompose_bottom(r["line_id"], lo, hi, float(t["kg_A"]), float(t["kg_B"]),
                                                   float(t["kg_cross_A"]), float(t["kg_cross_B"]), lab)
        elif comp == "DEVELOPMENT / ANCHORAGE":
            causes, outs, flags = decompose_dev(r["line_id"], lo, hi, int(t["bars_A"]), int(t["bars_B"]), d, lay)
            if t["status"] == "HELD_LABEL":
                n5 = parse_label(t["printed"])["n"]
                five = n5 * 2 * DEV_K[0] * d / 1000.0 * kgm(d) * lay
                outs += contains(r["line_id"], lo, hi, {"label_n_in_all_40d": five})
                flags = flags + ["LABEL_MEANING_NOT_IN_DEV_BOUND"]
        elif comp == "TOP BARS OVER SUPPORTS":
            causes, outs, flags = decompose_top(r["line_id"], lo, hi, _top_readings(t["top_held_kg"]),
                                                tb_panel=(lay == 2))
        else:
            raise ValueError(f"{r['line_id']}: population {comp!r} not mapped")
        tc, tn = (int(v) for v in t["ends_continuous"].split("/"))
        out.append(dict(line_id=r["line_id"], element=r["members"], direction=part, population=comp,
                        printed=t["printed"], d_mm=d, layers=lay, label_status=t["status"],
                        low_kg=lo, high_kg=hi, spread_kg=round(hi - lo, 6),
                        ends_continuous_A=tc, ends_A=tn,
                        **{f"c_{k}": round(v, 9) for k, v in sorted(causes.items())},
                        flags=";".join(flags)))
        outside += outs
    check_keys(keyrecs)
    return out, outside


def totals(rows):
    T = defaultdict(float)
    by = defaultdict(lambda: defaultdict(float))
    for r in rows:
        for k, v in r.items():
            if k.startswith("c_"):
                T[k[2:]] += v
                by[r["population"]][k[2:]] += v
    return T, by
