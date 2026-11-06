"""T-544 drawing reader (research only, NOT engine code): the 8 lintel ends of the four 1F windows whose lintel is HELD
(head not established, designer D-45): W16 (band WB-FL0041-FL0042, engine OP-017) and W19 / W20 / W24 (band
WB-FL0002-FL0003, engine OP-001 / OP-002 / OP-003), all on the 1F white AAC 0.20 glue host L-2fdc0f97.

Method: exactly the merged LINTEL_BEARING_V3 run (research/agents_t527/t527_extract.main, R-T527-1, on the T-516
masonry construction R-T516-1, both imported read-only and unchanged): only the case list differs. The T-516 module
globals CASES / CENSUS_OF are swapped for the duration of the call and restored afterwards (no merged file edited).

Inputs (outside the repository, never committed): <scratch>/t125_inputs.pkl and <scratch>/t125_v2.json (the merged
research/agents_t125 capture of Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf, sha ab54dd55).
Output: NUMBERS ONLY (lengths along a wall from a jamb, ids; no drawing coordinate): out/JAMB_EVIDENCE_T544.csv.

    python3 -I research/agents_t544/t544_extract.py <scratch> [<out.csv>]
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE.parent
for p in ("agents_t527", "agents_t516", "agents_t519"):
    sys.path.insert(0, str(R / p))
import t516_extract as X1  # noqa: E402  (read only)
import t527_extract as X3  # noqa: E402  (read only)

OUT = HERE / "out" / "JAMB_EVIDENCE_T544.csv"
EXT_NAME = "EXTENDED_SEARCH_T544.csv"
EXT_KEYS = ["opening_id", "side", "search_m", "available_m", "available_6dp_m", "stopper", "stopper_id", "own_band_m",
            "beyond_band_end", "through_walls", "band_length_m", "jamb_from_band_start_m"]
# opening -> (storey, band, engine ref): the T-175 host table (research/agents_t175/T175_OPENING_HOSTS.csv)
CASES = {
    "W16": ("1F", "WB-FL0041-FL0042", "OP-017"),
    "W19": ("1F", "WB-FL0002-FL0003", "OP-001"),
    "W20": ("1F", "WB-FL0002-FL0003", "OP-002"),
    "W24": ("1F", "WB-FL0002-FL0003", "OP-003"),
}
# stopper names for the openings that can bound these ends (T-175 host table)
EXTRA_CENSUS_OF = {("1F", "WB-FL0002-FL0003", "OP-001"): "W19", ("1F", "WB-FL0002-FL0003", "OP-002"): "W20",
                   ("1F", "WB-FL0002-FL0003", "OP-003"): "W24"}


def run(scratch, out=None):
    saved_cases, saved_census = X1.CASES, X1.CENSUS_OF
    try:
        X1.CASES = dict(CASES)
        X1.CENSUS_OF = {**saved_census, **EXTRA_CENSUS_OF}
        return X3.main(str(scratch), out=Path(out) if out else OUT, probe=None)
    finally:
        X1.CASES, X1.CENSUS_OF = saved_cases, saved_census




EXTENDED_SEARCH_M = 20.0          # m: R-T498-2 L_MAX; used only where the merged 3.0 m search stopped at its limit


def extended(scratch, rows):
    """for every end the merged V3 run left at SEARCH_LIMIT (3.0 m): the same V2 reach and V3 stopper order, searched
    to EXTENDED_SEARCH_M along the same line (a measured ceiling, or SEARCH_LIMIT again). -> {(oid, side): record}."""
    import json
    import pickle
    import lintel_bearing_v2 as V2
    import lintel_bearing_v3 as V3
    S = Path(scratch)
    d = pickle.load(open(S / "t125_inputs.pkl", "rb"))
    v = json.load(open(S / "t125_v2.json"))
    out, cache = {}, {}
    for r in rows:
        if r["stopper"] != "SEARCH_LIMIT":
            continue
        oid, side = r["opening_id"], r["side"]
        fl, band, how = CASES[oid]
        if fl not in cache:
            c1 = X1.storey(d["floors"][fl], v["floors"][fl]["v2"])
            cache[fl] = (c1, X3.storey_v3(fl, d["floors"][fl], c1))
        (W, ax, M, cols, gaps, _r), (M3, bays, _recs, _held) = cache[fl]
        a, b, L, (ux, uy) = ax[band]
        half = float(W[band]["t_m"]) / 2
        g = [x for x in gaps if x[1] == band and x[0] == how]
        if len(g) != 1:
            raise SystemExit(f"{oid}: {len(g)} gaps for {how} on {band}")
        jamb, sign = (g[0][2], -1) if side == "START" else (g[0][3], +1)
        e, capped = V2.reach(M3, a, ux, uy, jamb, sign, half, search=EXTENDED_SEARCH_M)
        bay_ids = {s for s, _ in bays}
        named = [(X3.gap_id(fl, x), x[4]) for x in gaps if x is not g[0] and X3.gap_id(fl, x) not in bay_ids]
        if capped:
            stop, sid = "SEARCH_LIMIT", ""
        else:
            s0, s1 = sorted((jamb + sign * e, jamb + sign * (e + V2.PROBE_M)))
            probe = V2.strip(a, ux, uy, s0, s1, half - V2.INSET)
            from shapely.ops import unary_union
            if cols and probe.intersection(unary_union(cols)).area > 1e-12:
                stop, sid = "COLUMN", ""
            elif any(probe.intersection(reg).area > 1e-12 for _s, reg in bays):
                stop, sid = "END_OF_MASONRY", "CURVED_BAY"
            else:
                stop, sid = V2.stopper(e, False, a, ux, uy, jamb, sign, half, [], named)
        rec = X3.end_record(band, how, W, ax, v["floors"][fl]["v2"], jamb, sign, e, capped, stop, sid)
        rec.update(opening_id=oid, side=side, search_m=f"{EXTENDED_SEARCH_M:.1f}", available_6dp_m=f"{e:.6f}",
                   band_length_m=f"{L:.4f}", jamb_from_band_start_m=f"{jamb:.4f}")
        out[(oid, side)] = rec
    return out


def main(scratch, out=None):
    """the V3 run of the 8 ends + the extended search of any SEARCH_LIMIT end; writes both numbers-only CSVs."""
    import csv
    out = Path(out) if out else OUT
    rows = run(scratch, out)
    ext = extended(scratch, rows)
    with open(out.parent / EXT_NAME, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=EXT_KEYS, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(ext[k] for k in sorted(ext))
    return rows, ext


if __name__ == "__main__":
    rows, ext = main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    for r in rows:
        print(r["opening_id"], r["side"], r["clear_width_m"], r["available_m"], r["v3_available_6dp_m"], r["stopper"],
              r["stopper_id"])
    for k, r in sorted(ext.items()):
        print("extended", k, r["available_6dp_m"], r["stopper"])
