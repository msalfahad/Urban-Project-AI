"""T-696 part (b): R-T696-1 (BOUND_ROUNDING_V1) restated on every bounded B9 line of ARCH_TAKEOFF_V3.0.68.

Every exact end is rebuilt from the line's own stated inputs, read from the Checker-merged ledgers (nothing typed):
  - MAS.UNITS.BLACK / MAS.MORTAR.BLACK / MAS.GLUE.AAC ranges: T-670 rows (host net m2, REQUIRED lintel faces, HELD
    lintel face maxima) -> material base range [net - req - held_max, net - req] x rate (12.5 pcs/m2 Q-75 / Q-80;
    t x (1 - 0.39 x 0.19 / (0.40 x 0.20)) m3/m2, owner 2026-10-29 10 mm joint; AAC glue kg/m2 per thickness from the
    COMPANY_RULEBOOK 1.1.0 record the producer reads);
  - MAS.MORTAR.BLACK.LINTEL_BEARING: T-675 bearing (6 dp, as the ledger records it) x f, f = kappa x t x 0.010,
    kappa = 0.39 x 0.19 / (0.40 x 0.20) / ... (R-T520-1: kappa = unit face / module face = 0.92625); D-1F-09 HELD
    0 .. 2 x 0.40 x f;
  - MAS.MORTAR.BLACK.PERIMETER: per wall from the T-520 ledger lengths (4 dp, as recorded): f x (soffit + vertical
    exact - 0.010 x top corners) for the figure, + f x range_block_end for the high, - f x the other-bearing deficit
    for the low (recovered at 4 dp from the ledger's own low and asserted); + T-675 held junction bands
    (multiplier (c + u + o - 1) x dz x f) and held piece soffits (length x f).
Each recomputed end is asserted to reproduce, under the producers' half-way rounding, the figure the T-370 / T-520 /
T-675 ledgers print (so the inputs are the line's inputs); the restated figure is floor(low) / ceil(high) at 6 dp.

    bash scripts/agent_env.sh run --tree task-T-696 research/agents_t696/t696_b9_bounds.py [--json OUT]

No drawing, workbook, client name or coordinate is read or written here: only merged research ledgers.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import bound_rounding_v1 as BR  # noqa: E402

IDX = ROOT / "research/agents_t672/out/LINE_INDEX_V3_0_68.json"
T670 = ROOT / "research/agents_t670/out/T670_MATERIALS.json"
T372 = ROOT / "research/agents_t372/out/T372_PERIMETER_LEDGER.json"
T675 = ROOT / "research/agents_t675/out/T675_MASONRY_ROUND2.json"
T520 = ROOT / "research/agents_t520/out/PERIMETER_BY_WALL_T520.csv"
RB = ROOT / "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.1.0.json"
PINS = {
    IDX: "fc485958", T670: "4c58a226", T372: "a324087f", T675: "66e63dfc", T520: "fb5ac4ab", RB: "da38d121",
}
IDX_LINES_SHA = "d1de50cb"         # V3.0.68 run of record (T-672)

UNIT_M = ("0.39", "0.19")
MODULE_M = ("0.40", "0.20")
JOINT_M = "0.010"
BLOCKS_PER_M2 = "12.5"             # Q-75 / Q-80 (40 x 20 face), COMPANY_RULEBOOK 1.1.0


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def kappa():
    return BR.D(BR._CTX.divide(BR.mul(*UNIT_M), BR.mul(*MODULE_M)))


def joint_rate(t):
    """installed joint m3 per m2 of wall face: t x (1 - kappa)."""
    return BR.mul(t, BR.add(1, -kappa()))


def f_perim(t):
    """perimeter / bed joint m3 per m of joint: kappa x t x 0.010 (R-T520-1)."""
    return BR.mul(kappa(), t, JOINT_M)


def glue_rate(rb, t):
    """UPC-AAC-GLUE-001 kg/m2 for the thickness (OWNER_CONFIRMED record of the rulebook the producer reads)."""
    for r in rb["records"]:
        if r.get("rule_id") == "UPC-AAC-GLUE-001":
            if r.get("status") != "OWNER_CONFIRMED":
                raise SystemExit("UPC-AAC-GLUE-001 is not OWNER_CONFIRMED")
            v = r["params"]["kg_per_m2_by_thickness_m"]["value"].get(f"{float(t):.2f}")
            if v is None:
                raise SystemExit(f"no AAC glue rate for {t}: HELD")
            return BR.D(v)
    raise SystemExit("rulebook: no UPC-AAC-GLUE-001 record")


def _t_of(host):
    return host.split("t=")[1].split("#")[0]


def base_range(row):
    """T-670 row -> exact material base range [net - req - sum(held max), net - req] (m2)."""
    req = [x["face_m2"] for x in row["lintels"] if x["kind"] == "REQUIRED"]
    held = [x["face_max_m2"] for x in row["lintels"] if x["kind"] == "HELD_RANGE"]
    if any(h is None for h in held):
        raise SystemExit(f"{row['material_line_id']}: a HELD lintel face with no maximum: no bound")
    hi = BR.add(row["host_net_m2"], *[-BR.D(x) for x in req])
    lo = BR.add(hi, *[-BR.D(x) for x in held])
    return lo, hi


def half_ulp(x):
    """half a step of the decimals a measured length is RECORDED with (a printed 4 dp length is the drawn length
    within +/- 0.00005 m); an exact printed 0 (no such piece) stays exactly 0."""
    d = BR.D(x)
    if d == 0:
        return BR.D(0)
    return BR.D(1).scaleb(d.as_tuple().exponent) / 2


def perimeter_walls():
    """per wall: exact low / high envelopes from the T-520 recorded lengths, each length widened by half its recorded
    step (R-T696-1 (4): the ledger keeps lengths at 4 dp, so the exact length is known only to that interval); the
    ledger's half-way figures are asserted to lie inside the envelope."""
    out = {}
    for r in csv.DictReader(T520.open(encoding="utf-8")):
        if not r["soffit_m3"]:
            continue                                   # 2F roof-datum walls: figure only, HELD (D-39)
        t = r["t_m"] if len(r["t_m"]) > 3 else r["t_m"] + "0"
        f = f_perim(t)
        S, V, R = (BR.D(r[k]) for k in ("soffit_m", "vertical_exact_m", "range_block_end_m"))
        hS, hV, hR = half_ulp(r["soffit_m"]), half_ulp(r["vertical_exact_m"]), half_ulp(r["range_block_end_m"])
        corner = BR.mul("0.010", r["top_corners"])
        fig_lo = BR.mul(f, BR.add(S, -hS, V, -hV, -corner))
        fig_hi = BR.mul(f, BR.add(S, hS, V, hV, -corner))
        hi = BR.add(fig_hi, BR.mul(f, BR.add(R, hR)))
        tol = BR.D("0.0000005")
        if not (fig_lo - tol <= BR.D(r["perimeter_figure_m3"]) <= fig_hi + tol and
                BR.add(fig_lo, BR.mul(f, R), -tol) <= BR.D(r["perimeter_high_m3"]) <= hi + tol):
            out[r["wall_id"]] = {"error": "T-520 figure / high outside the envelope of its recorded lengths"}
            continue
        d_lo = BR.D(r["perimeter_figure_m3"]) - BR.D(r["perimeter_low_m3"])
        lo, deficit = fig_lo, None
        if d_lo:
            L = BR.D(BR._CTX.divide(d_lo, f)).quantize(BR.D("0.0001"))      # the other-bearing deficit at 4 dp
            if abs(BR.mul(f, L) - d_lo) > tol:
                raise SystemExit(f"{r['wall_id']}: low deficit is not a 4 dp length x f")
            lo, deficit = BR.add(fig_lo, -BR.mul(f, BR.add(L, half_ulp(L)))), str(L)
        out[r["wall_id"]] = {"t": t, "f": f, "low": lo, "high": hi, "deficit_m": deficit,
                             "ledger": [r["perimeter_low_m3"], r["perimeter_high_m3"]]}
    return out


def band_high(b, f):
    c, u, o = (b["ends"].count(k) for k in "CUO")
    dz = BR.add(b["band_m"][1], -BR.D(b["band_m"][0]))
    return BR.mul(max(0, c + u + o - 1), dz, f)


def build():
    for p, want in PINS.items():
        if want and not _sha(p).startswith(want):
            raise SystemExit(f"{p.name}: sha256 {_sha(p)[:8]} is not the pinned merged file {want}")
    idx = _load(IDX)
    if not idx["inputs"]["lines"].startswith(IDX_LINES_SHA):
        raise SystemExit("line index is not the V3.0.68 run of record")
    cand = {r["line_id"]: r for r in idx["lines"]}
    t670, t372, t675, rb = _load(T670), _load(T372), _load(T675), _load(RB)
    rows = []

    def add_row(line_id, code, unit, what, lo, hi, inputs):
        c = cand[line_id]
        if c["item_code"] != code:
            raise SystemExit(f"{line_id}: {c['item_code']} is not {code}")
        before = [c["held_low"], c["held_high"]]
        if None in before:
            raise SystemExit(f"{line_id}: not a bounded line in V3.0.68")
        hw = [BR.half_way(lo), BR.half_way(hi)]
        new_lo, new_hi = BR.bound(lo, hi)
        rows.append({"line_id": line_id, "item_code": code, "unit": unit, "what": what, "inputs": inputs,
                     "exact": [str(lo), str(hi)], "half_way_of_exact": hw, "v3_0_68": before,
                     "reproduced": hw == before,
                     "r_t696_1": [BR.as_float(new_lo), BR.as_float(new_hi)],
                     "delta": [round(float(new_lo) - before[0], 6), round(float(new_hi) - before[1], 6)],
                     "exact_inside_restated": BR.D(new_lo) <= lo and hi <= BR.D(new_hi),
                     "exact_inside_v3_0_68": BR.D(before[0]) <= lo and hi <= BR.D(before[1])})

    # (1) units / mortar / glue ranges from the T-670 rows
    for r in t670["rows"]:
        a = r["after"]
        if not (isinstance(a, list) and a[0] == "RANGE"):
            continue
        lo_m2, hi_m2 = base_range(r)
        t = _t_of(r["host"])
        if r["code"] == "MAS.UNITS.BLACK":
            rate, unit = BR.D(BLOCKS_PER_M2), "pcs"
        elif r["code"] == "MAS.MORTAR.BLACK":
            rate, unit = joint_rate(t), "m3"
        elif r["code"] == "MAS.GLUE.AAC":
            rate, unit = glue_rate(rb, t), "kg"
        else:
            raise SystemExit(f"unexpected ranged code {r['code']}")
        add_row(r["material_line_id"], r["code"], unit, f"material base {lo_m2} .. {hi_m2} m2 x {rate} ({r['host']})",
                BR.mul(lo_m2, rate), BR.mul(hi_m2, rate),
                {"host_net_m2": r["host_net_m2"], "base_m2": [str(lo_m2), str(hi_m2)], "rate": str(rate)})

    # (2) lintel bearing beds (T-675 bearings)
    f15 = f_perim("0.15")
    bed_ids = {r["element_id"].split(":")[-1]: r["line_id"] for r in idx["lines"]
               if r["item_code"] == "MAS.MORTAR.BLACK.LINTEL_BEARING"}
    for x in t675["part_b"]["lintel_bed"]:
        if x["state"] == "EXACT":
            continue                                   # a point, not a bound (R-T696-1 (3))
        if x["state"] == "HELD":
            lo, hi, bear = BR.D(0), BR.mul(2, "0.40", f15), ["0", "0.80"]
        else:
            bear = [str(BR.D(x["bearing_m"][0])), str(BR.D(x["bearing_m"][1]))]
            lo, hi = BR.mul(bear[0], f15), BR.mul(bear[1], f15)
        add_row(bed_ids[x["opening_id"]], "MAS.MORTAR.BLACK.LINTEL_BEARING", "m3",
                f"lintel {x['opening_id']} bearing {bear[0]} .. {bear[1]} m x f {f15}", lo, hi,
                {"bearing_m": bear, "f_m3_per_m": str(f15)})

    # (3) perimeter joint (T-372 walls via T-520 lengths + T-675 bands / pieces)
    walls = perimeter_walls()
    hosts675 = {h["mortar_line_id"]: h for h in t675["part_b"]["hosts"]}
    per_ids = {r["element_id"].rsplit("#PERIMETER_JOINT", 1)[0].replace("MATERIAL:", ""): r["line_id"]
               for r in idx["lines"] if r["item_code"] == "MAS.MORTAR.BLACK.PERIMETER"}
    for ln in t372["lines"]:
        if ln["perimeter_state"] != "RANGE":
            continue
        ws = ln["walls"]
        bad = [w for w in ws if "error" in walls[w]]
        if bad:
            raise SystemExit(f"{ln['mortar_line_id']}: wall(s) {bad}: {walls[bad[0]]['error']}")
        lo = BR.add(*[walls[w]["low"] for w in ws])
        hi = BR.add(*[walls[w]["high"] for w in ws])
        f = walls[ws[0]]["f"]
        bands = [b for b in t675["part_b"]["bands"] if b["mortar_line_id"] == ln["mortar_line_id"]
                 and b["verdict"] == "HELD bounded"]
        pieces = [p for p in t675["part_b"]["pieces"] if p["wall_id"] in ws]
        for b in bands:
            if BR.half_way(band_high(b, f)) != b["high"]:
                raise SystemExit(f"band {b['wall_id']} {b['band_m']}: high not reproduced")
        for p in pieces:
            if BR.half_way(BR.mul(p["length_m"], f)) != p["high"]:
                raise SystemExit(f"piece {p['wall_id']} {p['piece']}: high not reproduced")
        bh = BR.add(*[band_high(b, f) for b in bands]) if bands else BR.D(0)
        ph = BR.add(*[BR.mul(BR.add(p["length_m"], half_ulp(p["length_m"])), f) for p in pieces]) if pieces \
            else BR.D(0)
        h675 = hosts675.get(ln["mortar_line_id"])
        if h675 and (h675["held_bands"] != len(bands) or h675["held_pieces"] != len(pieces)):
            raise SystemExit(f"{ln['mortar_line_id']}: band / piece count is not the T-675 host's")
        add_row(per_ids[ln["host"]], "MAS.MORTAR.BLACK.PERIMETER", "m3",
                f"walls {', '.join(ws)} drawn + {len(bands)} held bands + {len(pieces)} held pieces",
                lo, BR.add(hi, bh, ph),
                {"walls": ws, "drawn": [str(lo), str(hi)], "bands_high": str(bh), "pieces_high": str(ph)})
    rows.sort(key=lambda r: (r["item_code"], r["line_id"]))
    moved = [r for r in rows if r["delta"] != [0.0, 0.0]]
    return {"schema": "T696_B9_BOUNDS_V1", "rule": f"{BR.RULE_ID} {BR.METHOD} {BR.RULE_VERSION}",
            "candidate": "ARCH_TAKEOFF_V3.0.68", "line_index": IDX_LINES_SHA,
            "pins": {str(p.relative_to(ROOT)): _sha(p)[:8] for p in PINS},
            "kappa": str(kappa()), "f_015": str(f15), "joint_rate_015": str(joint_rate("0.15")),
            "bounded_lines": len(rows), "moved": len(moved),
            "not_reproduced": [r["line_id"] for r in rows if not r["reproduced"]],
            "exact_outside_v3_0_68": [r["line_id"] for r in rows if not r["exact_inside_v3_0_68"]],
            "rows": rows}


if __name__ == "__main__":
    doc = build()
    if "--json" in sys.argv:
        Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                                                                 encoding="utf-8")
    for r in doc["rows"]:
        print(f"{r['line_id'][:10]} {r['item_code'][4:]:<28} {r['unit']:<3} V3.0.68 {r['v3_0_68']} -> "
              f"{r['r_t696_1']} delta {r['delta']} exact-in-old {r['exact_inside_v3_0_68']} repro {r['reproduced']}")
    print(json.dumps({k: doc[k] for k in ("bounded_lines", "moved", "not_reproduced", "exact_outside_v3_0_68",
                                          "kappa", "f_015", "joint_rate_015", "pins")}, indent=1))
