"""T-138 hand ledger: ground-beam and foundation-strap steel, bar by bar (NO REPO CODE task: a research script that
only does the arithmetic of the hand table below; it imports nothing from engine/ and changes no released quantity).

    python3 -I research/agents_t138/t138_hand_ledger.py [--check]

Inputs are typed by hand from the drawings (structural PDF ST7757 p.10 "Schedule of Simple Beams", p.13 ground-beam
sections, p.2 foundation plan, p.3 ground-beams plan; the span lengths were read face to face from the structural DXF
entities named in each row). Frozen S5 values are read from research/alsenan_ground_system_rebar_s5 for the side-by-side
comparison only. Writes T138_MEMBERS.csv (one row per member and bar mark) next to this file and prints the totals.
Rules: URBAN-REBAR-NET-AND-PROCUREMENT@v1 (kg = count x length x kg/m, net; hooks / bends / laps only from a detail),
owner Q-71 (OPEN: count of bars printed per metre or at a spacing -> readings A / B / C, HELD), UP-QTY-STATUS-001.
"""

import csv
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
S5_GB = os.path.join(ROOT, "research/alsenan_ground_system_rebar_s5/GROUND_BEAM_REBAR_SUMMARY.csv")
S5_SB = os.path.join(ROOT, "research/alsenan_ground_system_rebar_s5/STRAP_BEAM_REBAR_SUMMARY.csv")


def kgm(d_mm):
    """unit mass d^2/162 (the project / engine method, rebar_unit_mass D2_OVER_162)."""
    return d_mm * d_mm / 162.0


COVER_M = 0.070  # ST7757.pdf p.8 general note 22: 7 cm in concrete against soil (worded "not less than")
STIRRUP_D = 8

# ---- p.13 ground-beam sections (count notation = released; spacing notation = Q-71) --------------------------------
# longitudinal sets as printed: (name, count, dia)
DETAILS = {
    "GT5M": {"title": "More than 5m length, without concentrated load", "b": 0.30, "h": 0.60,
             "bars": [("TOP", 3, 16), ("BOTTOM_ROW_1", 3, 16), ("BOTTOM_ROW_2", 3, 16)], "link": (8, 0.15),
             "side": None},
    "LT5M": {"title": "Less than 5m length, without concentrated load", "b": 0.30, "h": 0.40,
             "bars": [("TOP", 3, 14), ("BOTTOM_ROW_1", 3, 14), ("BOTTOM_ROW_2", 3, 14)], "link": (8, 0.15),
             "side": None},
    "LT2_5M": {"title": "Less than 2.5m length", "b": 0.30, "h": 0.30,
               "bars": [("TOP", 3, 14), ("BOTTOM_ROW_1", 3, 14), ("BOTTOM_ROW_2", 3, 14)], "link": None,
               "side": None},
    "EXT": {"title": "for exterior walls (depth FOLLOW ARCH.)", "b": 0.30, "h": None,
            "bars": [("TOP", 3, 16), ("BOTTOM", 6, 16)], "link": (8, 0.15), "side": "2 T12 / 30 cm"},
    "CONC": None,  # no project detail for a beam with a concentrated load: content unknown
}
S5_DETAIL = {"P13-GB-GT5M": "GT5M", "P13-GB-LT5M": "LT5M", "P13-GB-LT2_5M": "LT2_5M", "P13-GB-EXTERIOR": "EXT",
             "NO_PROJECT_DETAIL_FOR_CONCENTRATED_LOAD": "CONC"}


def per_metre(det):
    return sum(n * kgm(d) for _, n, d in DETAILS[det]["bars"])


# ---- hand span table: the face-to-face length of every ground-beam span (m), read on the ground-beams plan --------
# None = not re-measured here (arc / oblique / boundary end): the frozen S5 bar run is carried and named as such.
# A list = the span the frozen register gives is cut by a column it did not see: the real spans, plus the column
# lengths along the band between them.
HAND = {
    "GSO-107-7CE-1": (0.364, "7DF face y44248 -> column 17BD y44612"),
    "GSO-109-7CB-1": ([4.400, 4.400], "7D0 face y36648 -> column 228 y41048; 228 y41748 -> column 234 y46148 "
                      "(column 228, 0.30 x 0.70, sits on the band: missed by S5, which runs 9.50 across it)", [0.70]),
    "GSO-109-7CB-2": (2.700, "column 234 y46648 -> column 1DC y49348"),
    "GSO-10A-7C9-1": (4.300, "column 218 y36648 -> column 220 y40948"),
    "GSO-10B-7D1-1": (1.200, "7D4 face y36648 -> column 22C y37848"),
    "GSO-10B-7D1-2": (2.300, "column 22C y38348 -> column 223 y40648"),
    "GSO-114-115-7DF-1": (2.325, "7E8 face x107663 -> column 238 x109988"),
    "GSO-114-115-7DF-2": (1.000, "column 238 x110888 -> column 1FC x111888"),
    "GSO-136-7D5-1": (6.000, "column 207 y36648 -> column 204 y42648"),
    "GSO-137-138-1": (2.400, "column 204 x81118 -> column 214 x83518"),
    "GSO-13C-7D9-1": (1.450, "13E face x85218 -> 13F face x86668"),
    "GSO-13D-7D2-1": (5.800, "column 211 x85518 -> column 223 x91318"),
    "GSO-13E-7D6-1": ([4.300, 0.500], "7D4 face y36648 -> column 211 y40948; 211 y41248 -> arc 139/13A y41748 "
                      "(column 211 overlaps the band 0.20 of 0.30: missed by S5, which runs 5.10 across it)", [0.30]),
    "GSO-13F-7D3-1": (4.300, "column 20B y36648 -> 7D2 face y40948"),
    "GSO-140-7D7-1": (4.300, "7D4 face y36648 -> 7D2 face y40948"),
    "GSO-141-7DA-1": (1.200, "7D4 face y36648 -> 142 face y37848"),
    "GSO-142-7D8-1": (2.450, "7D7 face x88868 -> column 22C x91318"),
    "GSO-145-7CA-1": (None, "S5 cuts 0.40 + 2.30; the plan gives column 220 x93918 -> column 228 x95818 = 1.900 "
                      "through junction 178/7DB (x94418..94718): 0.500 + 1.100 if the junction is a node"),
    "GSO-145-7CA-2": (None, "see 145-7CA-1"),
    "GSO-15C-7CC-1": (2.400, "7CB face x96118 -> column 1F2 x98518"),
    "GSO-15D-7C8-1": (1.900, "footing F12 face y47648 (foundation plan, shifted 38724.4 in x) -> 7C3 face y49548"),
    "GSO-15E-15F-1": (2.700, "column 1F5 y46648 -> column 1E0 y49348"),
    "GSO-16F-7FF-1": (1.250, "15E face x98818 -> 15D face x100068"),
    "GSO-170-7C3-1": ([2.400, 3.370], "column 1DC x96118 -> column 1E0 x98518; 1E0 x98818 -> column 1E4 x102188 "
                      "(column 1E0, 0.30 x 0.50 = C2 on F2, sits on the band: missed by S5, which runs 6.22 across it)",
                      [0.30]),
    "GSO-170-7C3-2": (3.350, "column 1E4 x102788 -> column 241 x106138"),
    "GSO-170-7C3-3": (3.250, "column 241 x106638 -> column 17C0 x109888"),
    "GSO-175-7DE-1": (3.750, "7CD face y45798 -> 7C3 face y49548"),
    "GSO-176-7E6-1": (3.750, "7CD face y45798 -> 7C3 face y49548"),
    "GSO-177-7CD-1": (4.970, "column 1EC x100768 -> column 245 x105738 (the frozen 5.32 puts it over 5 m; face to "
                      "face it is under 5 m)"),
    "GSO-177-7CD-2": (None, "column 245 -> arc 157/158: arc end, not re-measured"),
    "GSO-178-7DB-1": (3.800, "145 face y41248 -> column 230 y45048"),
    "GSO-17B-7E5-1": (1.200, "7D0 face y36648 -> 184 face / column 23C y37848"),
    "GSO-17C-7E3-1": (1.928, "7E2 face y41220 -> footing F12 face y43148 (foundation plan)"),
    "GSO-17D-7E4-1": (4.272, "7D0 face y36648 -> 7E1 face y40920"),
    "GSO-17E-17F-1": (None, "oblique band: not re-measured"),
    "GSO-180-181-1": (None, "oblique band: not re-measured"),
    "GSO-180D-180E-1": (2.100, "176 face x102918 -> 175 face x105018"),
    "GSO-1811-1812-1": (None, "east end on the plot boundary: not re-measured"),
    "GSO-182-183-1": (None, "oblique band: not re-measured"),
    "GSO-184-7CF-1": (3.020, "17D face x99818 -> column 24D x102838"),
    "GSO-184-7CF-2": (2.650, "column 24D x103638 -> column 23C x106288"),
    "GSO-184-7CF-3": (5.000, "column 23C x106888 -> 7E0 face x111888 (exactly 5.00: neither 'more than' nor "
                      "'less than' 5 m on the face-to-face basis)"),
    "GSO-185-7C7-1": (0.600, "column 230 x95218 -> 109 face x95818"),
    "GSO-7D0-FC-1": (2.975, "column 218 x93318 -> column 249 x96293"),
    "GSO-7D0-FC-2": (5.745, "column 249 x97393 -> column 251 x103138"),
    "GSO-7D0-FC-3": (6.350, "column 251 x103638 -> column 255 x109988"),
    "GSO-7D0-FC-4": (1.200, "column 255 x110688 -> column 200 x111888"),
    "GSO-7D4-F8-1": (5.450, "column 207 x81218 -> column 20B x86668"),
    "GSO-7D4-F8-2": (4.250, "column 20B x87068 -> 7D1 face x91318"),
    "GSO-7DC-7DD-1": (3.525, "column 24D y38148 -> column 7F5 y41673"),
    "GSO-7DC-7DD-2": (3.525, "column 7F5 y41973 -> 177 face y45498"),
    "GSO-7E0-FD-1": (3.350, "column 200 y36848 -> column 809 y40198"),
    "GSO-7E0-FD-2": (3.250, "column 809 y40498 -> column 1FC y43748"),
    "GSO-7E1-7E2-1": (6.720, "column 228 x96118 -> 7DC face x102838"),
    "GSO-7E7-7E8-1": (3.525, "7CF face y38148 -> column 7ED y41673"),
    "GSO-7E7-7E8-2": (3.525, "column 7ED y41973 -> 177 face y45498"),
    "GSO-7E9-7EA-1": (4.225, "column 7F5 x103138 -> column 7ED x107363"),
    "GSO-A-139-13A-1": (None, "arc band: not re-measured"),
    "GSO-A-157-158-1": (None, "arc band: not re-measured"),
}

# interior columns a continuous released band runs through with the same bars on both sides (p.13 draws the ground-beam
# bars unbroken through the column); length along the band as drawn on the ground-beams plan
THROUGH = [
    ("7D0-FC", "column 249", 1.10, "EXT"), ("7D0-FC", "column 251", 0.50, "EXT"), ("7D0-FC", "column 255", 0.70, "EXT"),
    ("170-7C3", "column 1E0", 0.30, "EXT"), ("170-7C3", "column 1E4", 0.60, "EXT"),
    ("170-7C3", "column 241", 0.50, "EXT"), ("7D4-F8", "column 20B", 0.40, "EXT"),
]

# ---- foundation straps (p.10 schedule; p.2 plan; clear length between footing faces along the strap axis) -----------
STRAPS = {
    "SB1": {"rows": [{"b": 0.70, "h": 0.50, "bottom": (7, 16), "top": (13, 18), "links_per_m": 8}],
            "clear": 4.550, "drawn_band": 7.350,
            "how": "vertical edges 1689 / 1B1C: F10 face y37748 -> F8 face y42298 = 4.550"},
    "SB2": {"rows": [{"b": 1.00, "h": 0.50, "bottom": (10, 16), "top": (20, 18), "links_per_m": 10,
                      "src": "the only SB2 row on the issued sheet p.10 (INSERT 2ABA); plan width 0.987"},
                     {"b": 0.80, "h": 0.50, "bottom": (10, 18), "top": (10, 18), "links_per_m": 10,
                      "src": "INSERT 1FBB, drawn 2.88 m below the schedule frame, not on the issued sheet"}],
            "clear": 2.293, "drawn_band": 5.105,
            "how": "edges 1B08 / 1B09 (u_y 0.9813): F11 face y37848 -> F6 face y40098, 2250 / 0.9813 = 2.293; "
                   "both footing outlines are drawn broken exactly where the strap edges cross"},
    "SB3": {"rows": [{"b": 0.50, "h": 0.40, "bottom": (5, 16), "top": (5, 18), "links_per_m": 7}],
            "clear": 3.258, "drawn_band": 4.696,
            "how": "edges 1B26 / 1B27 (u_y 0.9361): F15 face y37348 -> F3 face y40398, 3050 / 0.9361 = 3.258"},
}


LEN = ("GT5M", "LT5M", "LT2_5M")


def classes(s):
    """p.13 titles on the face-to-face length: 'more than 5m', 'less than 5m', 'less than 2.5m' (below 2.5 m both
    'less than' titles hold; exactly 5.00 m meets neither title, so both stay candidates)."""
    if s > 5.0:
        return {"GT5M"}
    if abs(s - 5.0) < 1e-9:
        return {"GT5M", "LT5M"}
    if s < 2.5:
        return {"LT2_5M", "LT5M"}
    return {"LT5M"}


def q71(length, rate_or_spacing, per_metre=False):
    """count readings for spacing or per-metre notation (owner Q-71 OPEN): A ceil, B = A + 1, C fractional."""
    c = length * rate_or_spacing if per_metre else length / rate_or_spacing
    a = math.ceil(round(c, 9))
    return a, a + 1, c


def link_core(b, h, d=STIRRUP_D, c=COVER_M):
    """outer closed link at the bar centreline, no hooks (hooks / bends not printed: BLOCKED_DETAILING)."""
    d = d / 1000.0
    return 2 * (b - 2 * c - d) + 2 * (h - 2 * c - d)


def run(write=True):
    s5 = {r["occurrence_id"]: r for r in csv.DictReader(open(S5_GB))}
    s5sb = {r["mark"]: r for r in csv.DictReader(open(S5_SB))}
    rows = []
    T = {"rel": 0.0, "held_lo": 0.0, "held_hi": 0.0, "s5": 0.0, "stir_A": 0.0, "stir_B": 0.0, "stir_C": 0.0,
         "stir_n_A": 0, "stir_n_B": 0, "stir_unq": 0, "through": 0.0, "gb_rel": 0.0, "sb_rel": 0.0}
    agree = differ = notm = 0
    for oid in sorted(HAND):
        r = s5[oid]
        ent = HAND[oid]
        hand, note = ent[0], ent[1]
        cands = [S5_DETAIL[x] for x in eval(r["detail_ids"])]
        s5_run = float(r["bar_straight_run_lower_bound_m"]) if r["bar_straight_run_lower_bound_m"] else None
        s5_kg = float(r["known_kg"] or 0)
        T["s5"] += s5_kg
        spans = hand if isinstance(hand, list) else ([hand] if hand is not None else None)
        if spans is None:
            notm += 1
            L, basis = s5_run, "S5 carried (not re-measured)"
        else:
            L, basis = sum(spans), "hand face to face"
            if s5_run is not None and abs(L - s5_run) < 0.0005 and not isinstance(hand, list):
                agree += 1
            else:
                differ += 1
        # length class from the hand spans (face to face), only where it differs from the class of the frozen run
        if spans is not None and s5_run is not None and any(c in LEN for c in cands):
            hand_cls = set().union(*(classes(sp) for sp in spans))
            if hand_cls != classes(s5_run):
                cands = sorted(set(c for c in cands if c not in LEN) | hand_cls)
                note += f" [length class {'/'.join(sorted(classes(s5_run)))} -> {'/'.join(sorted(hand_cls))}]"
        released = r["occurrence_state"] == "LOWER_BOUND"
        defined = [c for c in cands if c != "CONC"]
        bars_same = len(set(tuple(DETAILS[c]["bars"]) for c in defined)) == 1 and len(defined) == len(cands)
        if released and not bars_same:
            released = False  # a candidate change from the hand geometry blocks it
        status = "RELEASED (lower bound)" if released else "HELD"
        why = ("" if released else
               (r["why_not_resolved"] or "candidate details differ: " + "/".join(cands))[:160])
        if L is None:
            status, why = "HELD", "bar run not established (S5 BLOCKED, not re-measured)"
        det = defined[0] if defined else None
        if L is not None and det:
            for name, n, d in DETAILS[det]["bars"]:
                kg = n * L * kgm(d)
                rows.append({"member": oid, "family": "GROUND_BEAM", "component": name, "count": n, "dia_mm": d,
                             "length_m": round(L, 3), "kg": round(kg, 3) if released else "",
                             "held_kg": "" if released else round(kg, 3), "status": status,
                             "detail": "/".join(cands), "length_basis": basis, "note": note if name == "TOP" else ""})
            if released:
                T["rel"] += per_metre(det) * L
                T["gb_rel"] += per_metre(det) * L
            else:
                vals = [per_metre(c) * L for c in defined]
                T["held_lo"] += min(vals)
                T["held_hi"] += max(vals)
                if len(defined) != len(cands):
                    why += " + a candidate with no project detail (unquantified)"
        else:
            rows.append({"member": oid, "family": "GROUND_BEAM", "component": "LONGITUDINAL", "count": "",
                         "dia_mm": "", "length_m": "" if L is None else round(L, 3), "kg": "", "held_kg": "",
                         "status": "HELD (unquantified)", "detail": "/".join(cands), "length_basis": basis,
                         "note": note})
        # stirrups: spacing notation -> Q-71; mass needs the link path (depth) and the hooks (not printed)
        links = set(DETAILS[c]["link"] if DETAILS[c] else None for c in cands)
        if L is not None and len(links) == 1 and None not in links:
            dl, s = links.pop()
            a = b = cc = 0
            for sp in spans or [L]:
                qa, qb, qc = q71(sp, s)
                a, b, cc = a + qa, b + qb, cc + qc
            core = None
            hs = set(DETAILS[c]["h"] for c in cands)
            if len(hs) == 1 and None not in hs:
                core = link_core(0.30, hs.pop())
            T["stir_n_A"] += a
            T["stir_n_B"] += b
            if core:
                for k, n in (("stir_A", a), ("stir_B", b), ("stir_C", cc)):
                    T[k] += n * core * kgm(dl)
            rows.append({"member": oid, "family": "GROUND_BEAM", "component": "STIRRUP T8 @ 150", "count":
                         f"A {a} / B {b} / C {cc:.2f}", "dia_mm": dl, "length_m": "" if core is None else round(core, 3),
                         "kg": "", "held_kg": "" if core is None else f"{a * core * kgm(dl):.3f} / {b * core * kgm(dl):.3f}"
                         f" / {cc * core * kgm(dl):.3f}",
                         "status": "HELD: count Q-71" + ("" if core else "; link path needs the depth (FOLLOW ARCH)")
                         + "; hooks not printed", "detail": "/".join(cands), "length_basis": "clear span",
                         "note": ""})
        else:
            T["stir_unq"] += 1
            rows.append({"member": oid, "family": "GROUND_BEAM", "component": "STIRRUP", "count": "", "dia_mm": "",
                         "length_m": "", "kg": "", "held_kg": "", "status": "HELD (unquantified): candidate links "
                         "differ or are not printed", "detail": "/".join(cands), "length_basis": "", "note": ""})
        if "EXT" in cands:
            rows.append({"member": oid, "family": "GROUND_BEAM", "component": "SIDE 2 T12 @ 300", "count": "",
                         "dia_mm": 12, "length_m": "", "kg": "", "held_kg": "", "status": "HELD (unquantified): "
                         "depth FOLLOW ARCH not printed; spacing count Q-71", "detail": "/".join(cands),
                         "length_basis": "", "note": ""})
        rows.append({"member": oid, "family": "GROUND_BEAM", "component": "BAR ENDS (development / hooks)",
                     "count": "", "dia_mm": "", "length_m": "", "kg": "", "held_kg": "",
                     "status": "HELD (unquantified): no ground-beam anchorage detail", "detail": "", "length_basis": "",
                     "note": why})
    for band, col, ln, det in THROUGH:
        for name, n, d in DETAILS[det]["bars"]:
            rows.append({"member": f"through {col} ({band})", "family": "GROUND_BEAM", "component": name, "count": n,
                         "dia_mm": d, "length_m": ln, "kg": round(n * ln * kgm(d), 3), "held_kg": "",
                         "status": "RELEASED (bar through an interior column, p.13)", "detail": det,
                         "length_basis": "column along the band", "note": ""})
        T["through"] += per_metre(det) * ln
        T["rel"] += per_metre(det) * ln
        T["gb_rel"] += per_metre(det) * ln
    # straps
    sb_rows = {}
    for mark, s in STRAPS.items():
        r0 = s["rows"][0]
        L = s["clear"]
        top = r0["top"][0] * L * kgm(r0["top"][1])
        bot = r0["bottom"][0] * L * kgm(r0["bottom"][1])
        conflict = len(s["rows"]) > 1
        st = "HELD (drawing-resolved candidate, verifier to confirm)" if conflict else "RELEASED (lower bound)"
        for name, (n, d), kg in (("TOP", r0["top"], top), ("BOTTOM", r0["bottom"], bot)):
            rows.append({"member": mark, "family": "STRAP_BEAM", "component": name, "count": n, "dia_mm": d,
                         "length_m": L, "kg": "" if conflict else round(kg, 3), "held_kg": round(kg, 3) if conflict else "",
                         "status": st, "detail": f"{r0['b']*100:.0f} x {r0['h']*100:.0f}", "length_basis":
                         "clear between footing faces", "note": s["how"] if name == "TOP" else ""})
        if conflict:
            alt = s["rows"][1]
            kalt = alt["top"][0] * L * kgm(alt["top"][1]) + alt["bottom"][0] * L * kgm(alt["bottom"][1])
            T["held_lo"] += min(kalt, top + bot)
            T["held_hi"] += max(kalt, top + bot)
            sb_rows[mark] = (top + bot, kalt)
        else:
            T["rel"] += top + bot
            T["sb_rel"] += top + bot
            sb_rows[mark] = (top + bot, None)
        # extension of the bars over the footings: no strap detail prints where they stop
        ext = (s["drawn_band"] - L - 2 * COVER_M)
        ekg = r0["top"][0] * ext * kgm(r0["top"][1]) + r0["bottom"][0] * ext * kgm(r0["bottom"][1])
        rows.append({"member": mark, "family": "STRAP_BEAM", "component": "BARS OVER THE FOOTINGS", "count": "",
                     "dia_mm": "", "length_m": round(ext, 3), "kg": "", "held_kg": f"0 .. {ekg:.3f} (drawn band less "
                     "2 x 70 mm, information only)", "status": "HELD: bar ends not detailed", "detail": "",
                     "length_basis": "drawn strap band", "note": ""})
        T.setdefault("sb_ext", 0.0)
        T["sb_ext"] += ekg
        qa, qb, qc = q71(L, r0["links_per_m"], per_metre=True)
        core = link_core(r0["b"], r0["h"])
        T["stir_n_A"] += qa
        T["stir_n_B"] += qb
        for k, n in (("stir_A", qa), ("stir_B", qb), ("stir_C", qc)):
            T[k] += n * core * kgm(8)
        rows.append({"member": mark, "family": "STRAP_BEAM", "component": f"STIRRUP {r0['links_per_m']} T8 / m",
                     "count": f"A {qa} / B {qb} / C {qc:.2f}", "dia_mm": 8, "length_m": round(core, 3), "kg": "",
                     "held_kg": f"{qa*core*kgm(8):.3f} / {qb*core*kgm(8):.3f} / {qc*core*kgm(8):.3f}",
                     "status": "HELD: count Q-71; outer link only (inner legs not drawn); hooks not printed",
                     "detail": "", "length_basis": "clear span", "note": ""})
    T["agree"], T["differ"], T["notm"] = agree, differ, notm
    T["s5_sb"] = sum(float(s5sb[m]["known_kg"]) for m in s5sb)
    if write:
        with open(os.path.join(HERE, "T138_MEMBERS.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    return T, rows, sb_rows


def fixture():
    """non-Alsenan hand fixture (two straps, count and per-metre notation; mirrored plan does not change a length)."""
    # strap A: 4 T16 top, 4 T16 bottom, clear 3.20 m -> 8 x 3.20 x 1.580247 = 40.454 kg
    a = 8 * 3.20 * kgm(16)
    # strap B, oblique 30 deg off the y axis: faces 2.000 m apart in y -> clear 2.000 / cos30 = 2.309 m;
    # 6 T18 top + 3 T16 bottom: 6 x 2.309 x 2.0 + 3 x 2.309 x 1.580247 = 27.713 + 10.948 = 38.661 kg (L = 2.3094)
    L = 2.0 / math.cos(math.radians(30))
    b = 6 * L * kgm(18) + 3 * L * kgm(16)
    # its links "7 T8 / m" over 2.309 m: A 17, B 18, C 16.166 (Q-71 open: HELD)
    qa, qb, qc = q71(L, 7, per_metre=True)
    # links "T8 @ 150" over 2.309 m: A ceil(15.396) = 16, B 17, C 15.396
    sa, sb_, sc = q71(L, 0.15)
    return round(a, 3), round(L, 3), round(b, 3), (qa, qb, round(qc, 3)), (sa, sb_, round(sc, 3))


if __name__ == "__main__":
    T, rows, sb = run()
    f = fixture()
    assert f[0] == 40.454 and f[1] == 2.309 and f[2] == 38.661 and f[3] == (17, 18, 16.166) and f[4] == (16, 17, 15.396), f
    print(f"rows {len(rows)}; spans re-measured: agree {T['agree']}, differ {T['differ']}, not re-measured {T['notm']}")
    print(f"RELEASED kg {T['rel']:.2f} (ground beams {T['gb_rel']:.2f} incl. through-column {T['through']:.2f}; "
          f"straps {T['sb_rel']:.2f})")
    print(f"HELD longitudinal range kg {T['held_lo']:.2f} .. {T['held_hi']:.2f} (+ unquantified candidates)")
    print(f"HELD links: count A {T['stir_n_A']} / B {T['stir_n_B']}; core-path kg A {T['stir_A']:.2f} / B "
          f"{T['stir_B']:.2f} / C {T['stir_C']:.2f} (where the depth is printed); {T['stir_unq']} spans unquantified")
    print(f"HELD strap bars over footings 0 .. {T['sb_ext']:.2f} kg")
    print(f"frozen S5 known: ground beams {T['s5']:.2f}, straps {T['s5_sb']:.2f}")
    print("straps:", {k: (round(v[0], 3), None if v[1] is None else round(v[1], 3)) for k, v in sb.items()})
    print("fixture:", f)
