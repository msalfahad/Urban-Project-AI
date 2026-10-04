"""BBS OPTIMISER (V3b) - bar hooks / bends by a recorded code method and deterministic cutting on stock lengths.

Hooks / bends (hook_addition):
    the developed length a hook adds to a straight bar = tail extension + bend arc at the bar centreline - the part of
    the straight leg the bend replaces (inside radius + one bar diameter). The tail and the inside bend diameter come
    from a HOOK_TABLE that names its basis (code, edition, table). The default table records ACI 318-19 Tables 25.3.1
    (standard hooks, deformed bars in tension) and 25.3.2 (stirrup / tie hooks). Its edition is NOT verified against a
    project document here, so every use is PROVISIONAL_CODE_METHOD unless the caller passes verified=True.

Cutting (cut):
    pieces [(mark, length_m, count)] of one diameter are cut from stock bars (default 12.00 m) by first-fit decreasing
    with offcut reuse: pieces sorted by length (desc, then mark), each placed in the first opened bar whose remaining
    length fits it (the remaining part of an opened bar is an offcut; a piece placed there is REUSED OFFCUT), else a new
    stock bar is opened. A piece longer than the stock is an error (the caller splits runs with laps first: split_run).
    Output: purchased bars, purchased length, used length, reused-offcut length, unused offcut (scrap), effective waste %.
Deterministic: the same pieces in any order give the same result. Stdlib only, project-agnostic.
"""

from __future__ import annotations

import hashlib
import json
import math

POLICY_ID = "BBS_OPTIMISER_V1"
STOCK_M = 12.0
KERF_M = 0.0
# ACI 318-19 (edition recorded, not verified against the project): tails and inside bend diameters by bar diameter (mm)
ACI_318_19 = {
    "basis": "ACI 318-19 Table 25.3.1 (standard hooks, deformed bars in tension) and Table 25.3.2 (stirrup / tie hooks)",
    "verified": False,
    "hooks": {
        "90": {"tail_db": 12, "tail_min_mm": 0, "bend_d_db": lambda db: 6 if db <= 25 else 8 if db <= 36 else 10,
               "table": "25.3.1", "use": "longitudinal bar end anchorage"},
        "180": {"tail_db": 4, "tail_min_mm": 65, "bend_d_db": lambda db: 6 if db <= 25 else 8 if db <= 36 else 10,
                "table": "25.3.1", "use": "longitudinal bar end anchorage"},
        "135_TIE": {"tail_db": 6, "tail_min_mm": 75, "bend_d_db": lambda db: 4 if db <= 16 else 6,
                    "table": "25.3.2", "use": "closed stirrup / tie hook"},
        "90_TIE": {"tail_db": 6, "tail_min_mm": 75, "bend_d_db": lambda db: 4 if db <= 16 else 6,
                   "table": "25.3.2", "use": "stirrup / tie hook (db <= 16)"},
    }}
ANGLE = {"90": 90.0, "180": 180.0, "135_TIE": 135.0, "90_TIE": 90.0}


def hook_addition(db_mm, kind, table=ACI_318_19) -> dict:
    """Developed length (m) one hook of `kind` adds to the straight bar length."""
    h = table["hooks"][kind]
    D = h["bend_d_db"](db_mm) * db_mm
    tail = max(h["tail_db"] * db_mm, h["tail_min_mm"])
    r_c = D / 2.0 + db_mm / 2.0
    arc = math.radians(ANGLE[kind]) * r_c
    replaced = D / 2.0 + db_mm
    add = tail + arc - replaced
    return {"kind": kind, "db_mm": db_mm, "inside_bend_d_mm": D, "tail_mm": tail, "arc_mm": round(arc, 3),
            "replaced_mm": replaced, "addition_m": round(add / 1000.0, 6), "basis": table["basis"],
            "table": h["table"], "verified": table["verified"],
            "class": "CODE_METHOD" if table["verified"] else "PROVISIONAL_CODE_METHOD"}


def split_run(run_m, lap_m, stock_m=STOCK_M) -> list:
    """A continuous run longer than the stock: pieces (each <= stock) including the lap overlaps."""
    if run_m <= stock_m + 1e-9:
        return [run_m]
    if lap_m >= stock_m:
        raise ValueError("lap longer than the stock length")
    n_laps = math.ceil((run_m - stock_m) / (stock_m - lap_m) - 1e-12)
    total = run_m + n_laps * lap_m
    pieces = [stock_m] * n_laps
    pieces.append(round(total - n_laps * stock_m, 9))
    return pieces


def cut(pieces, stock_m=STOCK_M, kerf_m=KERF_M) -> dict:
    """pieces [(mark, length_m, count)] of one diameter -> stock bars and the cutting result."""
    flat = []
    for mark, L, n in pieces:
        if L <= 0 or n <= 0:
            continue
        if L > stock_m + 1e-9:
            raise ValueError(f"piece {mark} {L} m longer than the stock {stock_m} m - split the run first")
        flat += [(round(L, 6), str(mark))] * int(n)
    flat.sort(key=lambda p: (-p[0], p[1]))
    bars = []                                              # [remaining, [pieces]]
    reused = 0.0
    for L, mark in flat:
        for b in bars:
            if b[0] + 1e-9 >= L + (kerf_m if b[1] else 0.0):
                b[0] -= L + (kerf_m if b[1] else 0.0)
                b[1].append((mark, L))
                reused += L
                break
        else:
            bars.append([stock_m - L, [(mark, L)]])
    purchased = len(bars) * stock_m
    used = sum(L for L, _ in flat)
    unused = sum(b[0] for b in bars)
    return {"stock_m": stock_m, "pieces": len(flat), "purchased_bars": len(bars), "purchased_m": round(purchased, 6),
            "used_m": round(used, 6), "reused_offcut_m": round(reused, 6), "unused_offcut_m": round(unused, 6),
            "effective_waste_pct": round(100.0 * unused / purchased, 4) if purchased else 0.0,
            "longest_offcut_m": round(max((b[0] for b in bars), default=0.0), 6)}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "stock_m": STOCK_M, "hook_basis": ACI_318_19["basis"],
           "hook_verified": ACI_318_19["verified"],
           "hooks": {k: {kk: (vv if not callable(vv) else "by db") for kk, vv in v.items()}
                     for k, v in ACI_318_19["hooks"].items()},
           "rule": "hook addition = tail + bend arc at the centreline - (inside radius + db); cutting = first-fit "
                   "decreasing on stock bars with offcut reuse; waste = unused offcut / purchased",
           "never": ["internet BBS constants", "a hook class CODE_METHOD while the edition is unverified",
                     "a piece longer than the stock without its laps"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
