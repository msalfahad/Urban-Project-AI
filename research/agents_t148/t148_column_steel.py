"""T-148 hand ledger: Alsenan column steel by bar population, per column and storey (lane S, gate 3; NO REPO CODE task).

A research script that only does the arithmetic of a hand table typed from the drawings; it imports nothing from engine/
and changes no released quantity.

    python3 -I research/agents_t148/t148_column_steel.py [--check]

Inputs (typed by hand, never copied client files):
  * SCHEDULE below: structural PDF ST7757 p.9 "Schedule of Columns" (read at 300 dpi this run; four storey bands
    FOUNDATION / GROUND FLOOR / 1st floor / 2nd floor & Top, each SIZE (cm) and REINF "n ø d"; struck cells = no column at
    that level), and p.9 "DETAILS OF COLUMN REINFORCEMENT" ("ST. OF COLUMN- 6ø8/m"; link arrangement by L = long side:
    L <= 50 cm one closed link; 50 < L < 80 cm two overlapping links; 80 < L < 120 cm three links; hooks drawn, no length).
  * p.8 general note 9 (development / lap length not less than 70 d in tension, 40 d in compression) and note 22
    (cover not less than 2.5 cm in columns).
  * T148_T119_INPUT.csv: the 59 columns of the T-119 ledger (agents/task-T-119 444e943, COLUMNS_TO_CONTROLLING_MEMBER.csv,
    sha256 93ae82ae...79fe6b): storey, mark, schedule section, D_ctrl, storey interval, concrete height, status.
Comparison only (never used in a hand value): frozen engine research S3.1 (research/alsenan_column_rebar_s3_1).

Rules: URBAN-REBAR-NET-AND-PROCUREMENT@v1 (kg = count x length x kg/m; net and procurement apart; laps only from the
structural notes; hooks / bends only from a detail with a length, else BLOCKED_DETAILING; never kg/m3),
URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 (T-119 heights), owner Q-71 (OPEN: count from a per-metre / spacing
notation -> readings A ceil, B A + 1, C fractional; HELD), owner Q-54 B (annex interval HELD), UP-QTY-STATUS-001
(held is never 0). Writes T148_COLUMNS.csv (one row per column and storey and component) and T148_SUMMARY.json.
"""

import csv
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
S31 = os.path.join(ROOT, "research/alsenan_column_rebar_s3_1")


def kgm(d_mm):
    """unit mass d^2 / 162 (the project method, rebar_unit_mass D2_OVER_162)."""
    return d_mm * d_mm / 162.0


COVER_M = 0.025      # p.8 note 22: not less than 2.5 cm in columns
LINK_D = 8           # p.9 "ST. OF COLUMN- 6ø8/m"
LINK_RATE = 6.0      # per metre (count rounding = owner Q-71, open)
DEV_K = (40, 70)     # p.8 note 9: 40 d compression .. 70 d tension; zone of a splice not printed -> range, HELD
STOCK_M = 12.0       # URBAN-REBAR-NET-AND-PROCUREMENT@v1 parameters.stock_length_m
SHEET_DX = 38.724    # x offset between the GF / 1F / 2F roof-slab plan frames (T-119 / T-138: 38,724.4 mm)

# p.9 Schedule of Columns, typed from the issued sheet: mark -> storey -> (b cm, h cm, n, d mm) or None (struck cell)
SCHEDULE = {
    "C":   {"FDN": (30, 50, 8, 16),  "GF": (20, 50, 8, 16),   "1F": None,             "2F": None},
    "C1":  {"FDN": (30, 50, 8, 16),  "GF": (20, 50, 8, 16),   "1F": (20, 50, 6, 16),  "2F": (20, 50, 6, 16)},
    "C2":  {"FDN": (30, 50, 8, 16),  "GF": (20, 50, 8, 16),   "1F": (20, 50, 8, 16),  "2F": (20, 50, 6, 16)},
    "C3":  {"FDN": (30, 50, 8, 16),  "GF": (25, 50, 8, 16),   "1F": (20, 50, 6, 16),  "2F": (20, 50, 6, 16)},
    "C4":  {"FDN": (30, 50, 8, 16),  "GF": (25, 50, 8, 16),   "1F": (20, 50, 8, 16),  "2F": (20, 50, 6, 16)},
    "C5":  {"FDN": (30, 60, 10, 16), "GF": (25, 60, 10, 16),  "1F": (20, 50, 8, 16),  "2F": (20, 50, 6, 16)},
    "C6":  {"FDN": (30, 70, 10, 16), "GF": (25, 70, 10, 16),  "1F": (20, 60, 8, 16),  "2F": (20, 50, 8, 16)},
    "C7":  {"FDN": (30, 80, 12, 16), "GF": (25, 80, 12, 16),  "1F": (20, 80, 10, 16), "2F": (20, 60, 8, 16)},
    "C8":  {"FDN": (30, 90, 12, 16), "GF": (25, 90, 12, 16),  "1F": (20, 90, 12, 16), "2F": (20, 70, 10, 16)},
    "C9":  {"FDN": (30, 100, 14, 16), "GF": (25, 100, 14, 16), "1F": (20, 90, 12, 16), "2F": (20, 70, 10, 16)},
    "C10": {"FDN": (30, 70, 10, 16), "GF": (25, 70, 10, 16),  "1F": None,             "2F": None},
    "C11": {"FDN": (30, 110, 14, 16), "GF": (25, 110, 14, 16), "1F": None,             "2F": None},
    "CN":  {"FDN": (30, 30, 4, 14),  "GF": None,              "1F": None,             "2F": None},
}
TURN_COLUMNS = {"COL-GF-09", "COL-GF-13"}  # T-119: GF C9 and GF C8 marked T.C on p.4 (1F outline turned 90 deg)
STOREYS = ["GF", "1F", "2F"]
BELOW = {"GF": "FDN", "1F": "GF", "2F": "1F"}
ABOVE = {"GF": "1F", "1F": "2F", "2F": None}

# drawn proportions of the overlapping links on the p.9 detail (N.T.S., information only, never a release):
# 50 < L < 80: two links each over 0.646 / 0.644 of the core length; 80 < L < 120: 0.797 / 0.793 / 0.231
DRAWN_SUM_L = {2: 1.290, 3: 1.821}


def link_band(long_m):
    """p.9 detail: number of closed links per level from L (long side). The printed limits leave L = 80 cm in no band."""
    L = round(long_m * 100)
    if L <= 50:
        return 1, "L <= 50 cm"
    if 50 < L < 80:
        return 2, "50 < L < 80 cm"
    if 80 < L < 120:
        return 3, "80 < L < 120 cm"
    return None, f"L = {L} cm: no printed band (limits 50 < L < 80 and 80 < L < 120)"


def link_set_lengths(b, h, k, c=COVER_M, d=LINK_D):
    """length of one link level (set) at the bar centreline path, no hooks.
    k = 1: one closed link = core perimeter (exact).  k >= 2 overlapping closed links whose lengths along L are not
    printed: lower bound 2 L_c + 2 k b_c (together they just cover L_c), upper 2 k L_c + 2 k b_c (each over the full
    L_c), drawn proportions as information."""
    dd = d / 1000.0
    bc, lc = min(b, h) - 2 * c - dd, max(b, h) - 2 * c - dd
    if k == 1:
        p = 2 * (bc + lc)
        return p, p, p
    lo = 2 * lc + 2 * k * bc
    hi = 2 * k * lc + 2 * k * bc
    info = 2 * DRAWN_SUM_L[k] * lc + 2 * k * bc
    return lo, hi, info


def q71(length, rate):
    """count readings for a per-metre notation (owner Q-71 OPEN): A ceil, B = A + 1, C fractional."""
    c = length * rate
    a = math.ceil(round(c, 9))
    return a, a + 1, c


def parse_section(s):
    a, b = s.split("x")
    return float(a), float(b)


def load_t119(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def bind_positions(cols):
    """same position on the GF / 1F / 2F roof-slab plans: x + k * SHEET_DX, y within 0.30 m (turn columns 0.15 m)."""
    gf = [c for c in cols if c["storey"] == "GF"]
    pos = {}
    for c in cols:
        k = STOREYS.index(c["storey"])
        x, y = float(c["x"]) + k * SHEET_DX, float(c["y"])
        best = None
        for g in gf:
            dist = math.hypot(float(g["x"]) - x, float(g["y"]) - y)
            if dist < 0.30 and (best is None or dist < best[0]):
                best = (dist, g["id"])
        pos[c["id"]] = best[1] if best else None
    return pos


def run(t119_path, write=True):
    cols = load_t119(t119_path)
    pos = bind_positions(cols)
    by_pos = defaultdict(dict)
    for c in cols:
        if pos[c["id"]]:
            by_pos[pos[c["id"]]][c["storey"]] = c

    rows, problems = [], []
    T = defaultdict(float)

    def add(**kw):
        rows.append(kw)

    for c in cols:
        st, mark, cid = c["storey"], c["mark"], c["id"]
        interval, height, dctrl = float(c["interval"]), float(c["height"]), float(c["D_ctrl"])
        b, h = parse_section(c["section"])
        t119_status = c["status"]
        held_cause = "" if t119_status == "CALCULATED" else f"T-119 {t119_status}: {c['reason']}"
        planted = mark.startswith("P.C")
        sched = None if planted else SCHEDULE.get(mark, {}).get(st)
        if planted:
            held_cause = (held_cause + "; " if held_cause else "") + (
                "BARS_NOT_PRINTED: planted column, p.4 / p.5 / p.6 leader prints only the size (DXF S-TEXT-SLAB "
                f"'{mark}'), no row in the p.9 schedule")
        elif sched is None:
            held_cause = (held_cause + "; " if held_cause else "") + "no schedule row / struck cell at this storey"
            problems.append(f"{cid}: {mark} has no schedule entry at {st}")
        else:
            sb, sh = sched[0] / 100.0, sched[1] / 100.0
            if sorted((sb, sh)) != sorted((b, h)):
                problems.append(f"{cid}: T-119 section {c['section']} vs schedule {sched[0]}x{sched[1]}")
        status = "RELEASED" if not held_cause else "HELD"
        tag = "rel" if status == "RELEASED" else "held"

        # ---- main bars, net: count x (concrete height + D_ctrl through the joint) = count x storey interval -------
        if sched:
            n, d = sched[2], sched[3]
            Lbar = height + dctrl
            assert abs(Lbar - interval) < 1e-9, cid
            kg = n * Lbar * kgm(d)
            T[f"main_{tag}"] += kg
            T[f"main_{tag}_{st}"] += kg
            add(id=cid, storey=st, mark=mark, section=c["section"], component="MAIN BARS net",
                reading=f"p.9 {mark} {st}: {n} ø {d}", count=n, length_m=round(Lbar, 3),
                length_basis=f"height {height:.2f} + D_ctrl {dctrl:.2f} (bars run through the joint) = interval "
                             f"{interval:.2f}", kg=round(kg, 3), kg_hi="", status=status, cause=held_cause)
            # ---- splice at the bottom of this storey (reading P: one lap per bar at every floor) -------------------
            lo, hi = (n * k * d / 1000.0 * kgm(d) for k in DEV_K)
            T["lapP_lo"] += lo
            T["lapP_hi"] += hi
            T[f"lapP_lo_{st}"] += lo
            T[f"lapP_hi_{st}"] += hi
            below = SCHEDULE[mark][BELOW[st]]
            add(id=cid, storey=st, mark=mark, section=c["section"], component="LAP at storey bottom (reading P)",
                reading=f"note 9: {n} bars x 40 d .. 70 d; lower bars {below[2] if below else 'none'} ø "
                        f"{below[3] if below else '-'}" + (" (neck HELD, Q-21 C)" if st == "GF" else ""),
                count=n, length_m=f"{DEV_K[0] * d / 1000:.2f} .. {DEV_K[1] * d / 1000:.2f}",
                length_basis="splice of every bar at this floor; splice position and zone not printed",
                kg=round(lo, 3), kg_hi=round(hi, 3), status="HELD",
                cause="lap zone (tension / compression) not printed; whether bars splice at every floor not printed")
            # ---- bar ends that stop here (count drops above, or top storey): end shape not printed -------------
            up = SCHEDULE[mark].get(ABOVE[st]) if ABOVE[st] else None
            above_col = by_pos.get(pos[cid], {}).get(ABOVE[st]) if ABOVE[st] and pos[cid] else None
            n_up = up[2] if (up and above_col is not None) else 0
            if n - n_up > 0:
                T["ends_unq"] += n - n_up
                add(id=cid, storey=st, mark=mark, section=c["section"], component="BAR ENDS stopping at this roof",
                    reading=f"{n} bars here, {n_up} continue above", count=n - n_up, length_m="",
                    length_basis="anchorage / bend into the slab or beam above: no detail prints it",
                    kg="", kg_hi="", status="HELD (unquantified)", cause="BLOCKED_DETAILING (URBAN-REBAR-NET-AND-"
                    "PROCUREMENT@v1: hooks / bends only from a detail)")
            if below and (below[0], below[1]) != (sched[0], sched[1]):
                tr = f"{below[0]}x{below[1]} -> {sched[0]}x{sched[1]}"
                if True:
                    T["transitions"] += 1
                    add(id=cid, storey=st, mark=mark, section=c["section"], component="SECTION TRANSITION at bottom",
                        reading=f"p.9 {BELOW[st]} {tr}", count="", length_m="",
                        length_basis="crank / offset of the bars from the lower section: no detail",
                        kg="", kg_hi="", status="HELD (unquantified)", cause="BLOCKED_DETAILING")
        else:
            add(id=cid, storey=st, mark=mark, section=c["section"], component="MAIN BARS net", reading="not printed",
                count="", length_m=round(height + dctrl, 3), length_basis="interval", kg="", kg_hi="",
                status="HELD (unquantified)", cause=held_cause)
            T["main_unq_cols"] += 1

        # ---- links over the concrete height (Q-71 readings) -----------------------------------------------------
        k, band = link_band(max(b, h))
        a, bb, cc = q71(height, LINK_RATE)
        if k is None:
            T["links_band_gap_cols"] += 1
            add(id=cid, storey=st, mark=mark, section=c["section"], component="LINKS 6 ø 8 / m",
                reading=band, count=f"A {a} / B {bb} / C {cc:.2f} levels", length_m="",
                length_basis=f"zone = concrete height {height:.2f} m", kg="", kg_hi="", status="HELD (unquantified)",
                cause="link arrangement for L = 80 cm not printed (rule gap; S3 project claim ALS-S3-CLAIM-002 reads "
                      "3 links, project-only, not in the Urban registers); count Q-71")
        else:
            lo, hi, info = link_set_lengths(b, h, k)
            u = kgm(LINK_D)
            kA, kB, kC = a * lo * u, bb * lo * u, cc * lo * u
            kA_hi, kB_hi = a * hi * u, bb * hi * u
            for key, v in (("A", kA), ("B", kB), ("C", kC)):
                T[f"links{key}_lo"] += v
                T[f"links{key}_lo_{st}"] += v
            T["linksB_hi"] += kB_hi
            T["linksA_info"] += a * info * u
            T["linksB_info"] += bb * info * u
            add(id=cid, storey=st, mark=mark, section=c["section"], component="LINKS 6 ø 8 / m",
                reading=f"{band}: {k} closed link(s) per level", count=f"A {a} / B {bb} / C {cc:.2f} levels",
                length_m=(f"{lo:.3f}" if k == 1 else f"{lo:.3f} .. {hi:.3f} (drawn {info:.3f})"),
                length_basis=f"zone = concrete height {height:.2f} m; path at the bar centreline, cover 2.5 cm "
                             f"(note 22), no hooks",
                kg=f"A {kA:.3f} / B {kB:.3f} / C {kC:.3f}" + ("" if k == 1 else " (lower bound)"),
                kg_hi=("" if k == 1 else f"A {kA_hi:.3f} / B {kB_hi:.3f} (upper)"), status="HELD",
                cause="count Q-71 (open)" + ("" if k == 1 else "; overlapping link lengths not printed (p.9 N.T.S.)")
                + "; hooks drawn without length (BLOCKED_DETAILING)" + ("; " + held_cause if held_cause else ""))
        # ---- turned columns (p.4 legend T.C; p.15 "TYP. DETAIL OF TWISTED COLUMN"): 4 ø 16 EXTRA over 1 M below +
        # 1 M above the floor (bars drawn over both dimensioned metres, a short inward bend at the top drawn without a
        # length); spiral stirrups 6 ø 8 / m over the same 2 m round a circle whose diameter is not dimensioned -------
        if cid in TURN_COLUMNS:
            kg = 4 * 2.00 * kgm(16)
            T[f"turn_{tag}"] += kg
            add(id=cid, storey=st, mark=mark, section=c["section"], component="TURN EXTRA 4 ø 16 (p.15)",
                reading="p.15 twisted column: 4 ø 16 EXTRA; dims 1M + 1M", count=4, length_m=2.00,
                length_basis="1 M in the GF column below the floor + 1 M in the 1F column above (printed dimensions)",
                kg=round(kg, 3), kg_hi="", status=status,
                cause=(held_cause + "; " if held_cause else "") + "top bend drawn without length: BLOCKED_DETAILING")
            sa, sb_, sc = q71(2.00, LINK_RATE)
            add(id=cid, storey=st, mark=mark, section=c["section"], component="TURN SPIRAL 6 ø 8 / m (p.15)",
                reading="p.15 spiral stirrups 6 ø 8 / m over 2 m", count=f"A {sa} / B {sb_} / C {sc:.2f} turns",
                length_m="", length_basis="spiral diameter not dimensioned", kg="", kg_hi="",
                status="HELD (unquantified)", cause="diameter not printed; count Q-71")
        jl = LINK_RATE * dctrl
        T["joint_levels_info"] += jl
        add(id=cid, storey=st, mark=mark, section=c["section"], component="LINKS in the joint (information)",
            reading=f"6 / m x D_ctrl {dctrl:.2f} = {jl:.2f} levels", count="", length_m="",
            length_basis="whether links continue through the beam-column joint is not printed", kg="", kg_hi="",
            status="HELD (unquantified)", cause="not printed")

    # ---- reading S: splices only where a continuous bar is longer than the 12 m stock (from GF level up) ----------
    lapS_lo = lapS_hi = 0.0
    chains = []
    for p, ss in by_pos.items():
        present = [s for s in STOREYS if s in ss and not ss[s]["mark"].startswith("P.C")]
        if not present or present[0] != "GF":
            continue
        run_len, n_cont = 0.0, None
        for s in present:
            sched = SCHEDULE[ss[s]["mark"]][s]
            if sched is None:
                break
            run_len += float(ss[s]["interval"])
            n_cont = sched[2] if n_cont is None else min(n_cont, sched[2])
        laps = math.ceil(round(run_len / STOCK_M, 9)) - 1
        if laps > 0:
            d = 16
            lapS_lo += n_cont * laps * DEV_K[0] * d / 1000 * kgm(d)
            lapS_hi += n_cont * laps * DEV_K[1] * d / 1000 * kgm(d)
        chains.append({"gf_id": p, "storeys": present, "run_m": round(run_len, 2), "bars_through": n_cont,
                       "stock_laps_per_bar": laps})

    # ---- comparison: frozen engine research S3.1 (main core per floor, schedule join) -----------------------------
    s31 = {}
    mp = os.path.join(S31, "COLUMN_MAIN_BAR_REGISTER.json")
    if os.path.exists(mp):
        with open(mp, encoding="utf-8") as f:
            reg = json.load(f)["rows"]
        for r in reg:
            if r["floor"] in STOREYS and r["length_kind"] == "CORE_VERTICAL_RUN":
                s31[r["floor"]] = s31.get(r["floor"], 0.0) + (r["kg"] or 0.0)
                s31[f"n_{r['floor']}"] = s31.get(f"n_{r['floor']}", 0) + 1
                s31[f"bars_{r['floor']}"] = s31.get(f"bars_{r['floor']}", 0) + r["count"]

    summary = {
        "columns": len(cols), "rows": len(rows), "input_problems": problems,
        "main_net_released_kg": round(T["main_rel"], 3), "main_net_held_kg": round(T["main_held"], 3),
        "main_net_by_storey": {s: {"released": round(T[f"main_rel_{s}"], 3), "held": round(T[f"main_held_{s}"], 3)}
                               for s in STOREYS},
        "main_unquantified_columns": int(T["main_unq_cols"]),
        "turn_extra_kg": {"released": round(T["turn_rel"], 3), "held": round(T["turn_held"], 3)},
        "net_released_kg": round(T["main_rel"] + T["turn_rel"], 3),
        "net_held_defined_kg": round(T["main_held"] + T["turn_held"], 3),
        "lap_reading_P_kg": [round(T["lapP_lo"], 3), round(T["lapP_hi"], 3)],
        "lap_reading_P_by_storey": {s: [round(T[f"lapP_lo_{s}"], 3), round(T[f"lapP_hi_{s}"], 3)] for s in STOREYS},
        "lap_reading_S_kg": [round(lapS_lo, 3), round(lapS_hi, 3)],
        "links_kg_lower_path": {"A": round(T["linksA_lo"], 3), "B": round(T["linksB_lo"], 3),
                                "C": round(T["linksC_lo"], 3)},
        "links_by_storey_lower_path": {s: {x: round(T[f"links{x}_lo_{s}"], 3) for x in "ABC"} for s in STOREYS},
        "links_B_upper_path_kg": round(T["linksB_hi"], 3),
        "links_drawn_proportion_info_kg": {"A": round(T["linksA_info"], 3), "B": round(T["linksB_info"], 3)},
        "links_band_gap_columns": int(T["links_band_gap_cols"]),
        "joint_link_levels_info": round(T["joint_levels_info"], 2),
        "bar_ends_unquantified": int(T["ends_unq"]), "section_transitions_unquantified": int(T["transitions"]),
        "chains": chains, "engine_s31_main_core": {k: (round(v, 3) if isinstance(v, float) else v)
                                                   for k, v in s31.items()},
    }
    if write:
        keys = ["id", "storey", "mark", "section", "component", "reading", "count", "length_m", "length_basis", "kg",
                "kg_hi", "status", "cause"]
        with open(os.path.join(HERE, "T148_COLUMNS.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, keys)
            w.writeheader()
            w.writerows(rows)
        with open(os.path.join(HERE, "T148_SUMMARY.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=1, ensure_ascii=False)
    return summary, rows


def checks(S, rows):
    """re-add checks: rows -> totals."""
    rel = sum(r["kg"] for r in rows if r["component"] == "MAIN BARS net" and r["status"] == "RELEASED")
    held = sum(r["kg"] for r in rows if r["component"] == "MAIN BARS net" and r["status"] == "HELD")
    assert abs(rel - S["main_net_released_kg"]) < 0.01 and abs(held - S["main_net_held_kg"]) < 0.01
    assert abs(sum(v["released"] for v in S["main_net_by_storey"].values()) - S["main_net_released_kg"]) < 0.01
    assert abs(sum(v["held"] for v in S["main_net_by_storey"].values()) - S["main_net_held_kg"]) < 0.01
    assert abs(sum(v["A"] for v in S["links_by_storey_lower_path"].values()) - S["links_kg_lower_path"]["A"]) < 0.01
    n_main = sum(1 for r in rows if r["component"] == "MAIN BARS net")
    assert n_main == S["columns"], (n_main, S["columns"])
    assert not S["input_problems"], S["input_problems"]


def fixture():
    """non-Alsenan hand fixture (hand-calculated values asserted). A three-storey villa column 'K2', sections 30 x 60 /
    30 x 60 / 25 x 45, bars 8 ø 20 / 6 ø 20 / 4 ø 16, intervals 3.60 / 3.30 / 3.30 m, controlling depths 0.60 / 0.50 / 0.45."""
    u20, u16, u8 = kgm(20), kgm(16), kgm(8)
    # main net = n x interval x d^2/162
    assert abs(8 * 3.60 * u20 - 71.111) < 0.001          # 8 x 3.60 x 2.4691 = 71.111
    assert abs(6 * 3.30 * u20 - 48.889) < 0.001
    assert abs(4 * 3.30 * u16 - 20.859) < 0.001
    # height + D_ctrl = interval (bars through the joint) is independent of the controlling member
    assert abs((3.60 - 0.60) + 0.60 - 3.60) < 1e-12
    # laps reading P at 40 d / 70 d, storey 2 (6 ø 20): 6 x 0.80 x 2.4691 = 11.852; 6 x 1.40 x 2.4691 = 20.741
    assert abs(6 * 0.80 * u20 - 11.852) < 0.001 and abs(6 * 1.40 * u20 - 20.741) < 0.001
    # reading S: 3.60 + 3.30 + 3.30 = 10.20 m < 12 -> no stock lap
    assert math.ceil(10.20 / STOCK_M) - 1 == 0
    # links storey 1: 30 x 60 -> 2 overlapping links (50 < 60 < 80); core b 0.30 - 0.05 - 0.008 = 0.242, L 0.542
    lo, hi, _ = link_set_lengths(0.30, 0.60, 2)
    assert abs(lo - (2 * 0.542 + 4 * 0.242)) < 1e-9 and abs(hi - (4 * 0.542 + 4 * 0.242)) < 1e-9
    # storey 3: 25 x 45 -> one link, 2 x (0.192 + 0.392) = 1.168 m; height 3.30 - 0.45 = 2.85: A ceil(17.1) = 18,
    # B 19, C 17.1 -> A 18 x 1.168 x 0.3951 = 8.306 kg (HELD, Q-71)
    p, _, _ = link_set_lengths(0.25, 0.45, 1)
    a, b, c = q71(2.85, LINK_RATE)
    assert abs(p - 1.168) < 1e-9 and (a, b) == (18, 19) and abs(c - 17.1) < 1e-9
    assert abs(a * p * u8 - 8.306) < 0.001
    # rotation / mirror: link band and lengths use min / max of the section, so 60 x 30 == 30 x 60
    assert link_set_lengths(0.60, 0.30, 2) == link_set_lengths(0.30, 0.60, 2)
    # units: a section typed in mm (300 x 600) converted once gives the same path
    assert link_set_lengths(300 / 1000, 600 / 1000, 2) == link_set_lengths(0.30, 0.60, 2)
    # boundary: L = 80 cm is in no printed band -> HELD, never a number
    assert link_band(0.80)[0] is None and link_band(0.50)[0] == 1 and link_band(0.81)[0] == 3
    # missing data: a mark with no schedule row gives no released steel (HELD), never 0
    assert SCHEDULE.get("K2") is None
    # exact-multiple count: 6 / m over 3.00 m = 18.0 levels -> A 18 (no extra from float noise), B 19
    assert q71(3.00, 6.0)[:2] == (18, 19)
    return True


if __name__ == "__main__":
    t119 = sys.argv[sys.argv.index("--t119") + 1] if "--t119" in sys.argv else os.path.join(HERE, "T148_T119_INPUT.csv")
    S, R = run(t119, write="--check" not in sys.argv)
    checks(S, R)
    fixture()
    out = {k: v for k, v in S.items() if k != "chains"}
    print(json.dumps(out, indent=1, ensure_ascii=False))
    print("chains with a stock lap:", [c for c in S["chains"] if c["stock_laps_per_bar"] > 0])
    print("checks and fixture: PASS")
