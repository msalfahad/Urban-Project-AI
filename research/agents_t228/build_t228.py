"""T-228 blockwork resolution 4/4: wall register v2 (resolution ledger) and after-coverage (Alsenan development villa).

Read-only over merged ledgers; register v1 (T-225) is never edited. Every change names its merged source:
  research/agents_t225/BLOCKWORK_WALL_REGISTER_V1.csv     register v1 (T-225, MERGED 48e6f08a)
  research/agents_t226/register_delta.csv                 heights by member (T-226, MERGED a04f8e21)
  research/agents_t227/register_delta.csv                 heads, annex / lift tests, arched outline (T-227 r2, MERGED ebce3d97)
  research/agents_t215/T215_ROW_EFFECT.csv                45 deg / column ends closed by area (T-215, MERGED 8a9b4b48)
  research/agents_t222/T222_RESULTS.csv                   bay basis, junction piece, P-GF-05 (T-222, MERGED 769cad40)
  research/agents_t238/DELTA_T238.csv                     W26 true outline (T-238, MERGED 242e50b2)
  research/agents_t017/T017_WALL_AGREEMENT.csv            independent census (T-017, MERGED 345f408b): annotation only
  + the Checker verdict rulings on the board (RULINGS below, quoted by date / time; numbers are the Checker's own).
  research/agents_t225/THREE_WAY_BY_FLOOR_SECTION.csv     freelancer columns (comparison only, never an input)

Usage: python3 -I build_t228.py          (writes the outputs next to this script)
       python3 -I build_t228.py --check  (exit 1 if any committed output differs, or a merge commit is not an
                                          ancestor of HEAD when git is available)
"""
from __future__ import annotations

import csv
import io
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import register_v2 as R  # noqa: E402

f, has = R.f, R.has
R3 = lambda v: f"{v:.3f}"
DRIVE = "Drive 'Alsenan chalet project'"
ARCH = f"{DRIVE} / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha ab54dd55)"
ST = f"{DRIVE} / ST7757 dxf.dxf (sha 9f9d1179)"

# source -> reference (merge commit on claude/access-permissions-setup-ii24ws + Checker verdict)
MERGED = {
    "T-226": "MERGED a04f8e21 (Verifier 2026-10-23 18:01 UTC, Gate A)",
    "T-227": "MERGED ebce3d97 (Verifier 2026-10-23 21:05 UTC, Gate A r2)",
    "T-215": "MERGED 8a9b4b48 (Verifier 2026-10-23 15:04 UTC, Gate A part 1)",
    "T-222": "MERGED 769cad40 (Verifier 2026-10-23 20:14 UTC, Gate A)",
    "T-238": "MERGED 242e50b2 (Verifier 2026-10-23 22:50 UTC, Gate A)",
    "T-017": "MERGED 345f408b (Verifier 2026-10-23 23:08 UTC, Gate A; check tool, annotation only)",
    "RULING T-226 18:01": "Verifier 2026-10-23 18:01 UTC, T-226 verdict f / statuses (own drawn-edge re-measure)",
    "RULING GF-W10 21:15": "Verifier 2026-10-23 21:15 UTC, (A) GF-W10 RULING (owner 18:00 request)",
    "RULING T-108 09:11": "Verifier 2026-10-23 09:00-09:11 UTC, T-108 r2 MERGED 01eeafd0 (own 2F-W08 re-measure)",
    "RULING T-143": "Verifier, T-143 verdict (own GF-W01 spans 3.075 + 5.745 + 6.350 + 1.300 = 16.470 m and members; 62.155 m2, 0.0 %)",
}
COMMITS = ("a04f8e21", "ebce3d97", "8a9b4b48", "769cad40", "242e50b2", "345f408b", "01eeafd0", "48e6f08a")

NEW_COLS = ("held_increment_m2", "length_bounds_m", "checker_remeasured", "v2_sources", "census_t017_status",
            "census_t017_length_m", "census_t017_minus_ledger_m", "census_t017_cause", "census_t017_verdict",
            "length_under_UP-MAS-CORNER-001_m (proposed rule, not applied)", "pending_findings_t228")
WHITE_F, BLACK_F = (6.4, 25.0 / 3.0), 12.5        # T-176 / Q-60 supplier faces, Q-75 module (as register v1)


def rd(rel):
    return list(csv.DictReader((ROOT / rel).open(encoding="utf-8")))


def v1():
    rows = rd("research/agents_t225/BLOCKWORK_WALL_REGISTER_V1.csv")
    for r in rows:
        for c in NEW_COLS:
            r[c] = ""
    return rows


# ------------------------------------------------------------------------------------------------ changes
def delta_changes(v1rows, rel, src):
    """Every field a merged delta row changes against register v1 (diff, not the delta's own prose)."""
    base = {r["wall_id"]: r for r in v1rows}
    out = []
    for d in rd(rel):
        b = base[d["wall_id"]]
        s = {k: d[k] for k in b if k in d and d[k] != b[k] and k not in ("calculation",)}
        if s:
            out.append({"wall_id": d["wall_id"], "source": src, "set": s, "why": d["change"]})
    return out


def t215_changes(v1rows):
    base = {r["wall_id"]: r for r in v1rows}
    out = []
    for e in rd("research/agents_t215/T215_ROW_EFFECT.csv"):
        b = base[e["row_id"]]
        lo, hi = f(e["d_gross_m2_min"]), f(e["d_gross_m2_max"])
        L = f(e["closed_length_m"])
        s = {"length_m": f"{L:.3f}", "length_class": R.SS}
        if lo or hi:
            g = f(b["gross_m2"]) + lo
            s.update(gross_m2=R3(g), height_weighted_m=R3(g / (L - f(b["held_length_m"]))))
            if b["net_class"] in R.ESTABLISHED:
                s["net_m2"] = R3(f(b["net_m2"]) + lo)
            if hi - lo > 1e-9:
                s["held_increment_m2"] = (f"0 .. {hi - lo:.4f} (CB2 BM-GF-055 width CONFLICT, schedule 0.20 vs drawn "
                                          f"0.25, Q-61 C(1): never picked)")
        out.append({"wall_id": e["row_id"], "source": "T-215", "set": s,
                    "why": f"end closed by drawn masonry area: {e['t108_physical_m']} -> {L:.4f} m, gross "
                           f"{lo:+.4f} .. {hi:+.4f} m2 (UP-MAS-JUNCTION-001 proposed)"})
    return out


def t222_changes(v1rows):
    base = {r["wall_id"]: r for r in v1rows}
    q = {(r["item"], r["quantity"]): r["value"] for r in rd("research/agents_t222/T222_RESULTS.csv")}
    g = lambda item, k: f(q[(item, k)])
    w25 = base["1F-W25"]
    L25, G25 = g("bay", "1F-W25 physical length incl. stub (m)"), g("bay", "1F-W25 gross (m2)")
    Lb, Gb = g("bay", "1F-W00/W01 change (m)"), g("bay", "1F-W00/W01 change (m2)")
    Lj, Gj = g("bay", "1F-W14+W15 junction piece (m)"), g("bay", "1F-W14+W15 junction piece (m2)")
    Gp = g("P-GF-05", "masonry above the lintel (m2)")
    j = base["1F-W14 + 1F-W15"]
    w00, w05 = base["1F-W00"], base["GF-W05"]
    ev_bay = (f"bay caps on the wall layer of {ARCH} 1F plan (full-thickness caps, T-222 s.2 / READINGS R12 / R13), "
              f"heights CB12 25x75 bands 5DE / 5DF -> 3.45 and slab 0.16 -> 4.04 on {ST} 1F roof slab")
    add = lambda wid, like, s, why: {"wall_id": wid, "source": "T-222", "op": "add", "why": why,
                                     "set": {**{k: like[k] for k in ("floor", "group", "block_type", "type_class",
                                                                     "t_m")}, **s}}
    return [
        {"wall_id": "1F-W25", "source": "T-222", "why": "1F bay basis closed: ends are wall to the full caps",
         "set": {"length_m": R3(L25), "gross_m2": R3(G25), "height_weighted_m": R3(G25 / L25), "net_m2": R3(G25),
                 "evidence": ev_bay}},
        add("1F-W00/W01 BAY-ENDS", w00,
            {"length_m": f"{Lb:.3f}", "held_length_m": "0.000", "length_class": R.SS, "height_weighted_m": R3(Gb / Lb),
             "gross_m2": R3(Gb), "gross_class": R.SS, "deductions_m2": "0.000", "net_m2": R3(Gb), "net_class": R.SS,
             "evidence": ev_bay + "; the straight band WB-FL0041-FL0042 ends at the caps (split between its runs #1 / "
                                  "#2 not drawn: one row, counted once)",
             "unresolved_reason": "pending the Checker's independent re-measure (bay basis not re-measured 20:14)"},
            "1F-W00 / W01 straight-band ends to the bay caps (+0.166 m), a piece in no v1 row"),
        {"wall_id": "1F-W14 + 1F-W15", "source": "T-222", "why": "junction piece at the bay end (in no run, no bound)",
         "set": {"length_m": R3(f(j["length_m"]) + Lj), "gross_m2": R3(f(j["gross_m2"]) + Gj),
                 "height_weighted_m": R3((f(j["gross_m2"]) + Gj) / (f(j["length_m"]) + Lj)),
                 "net_bounds_m2": "11.273 .. 16.525 (P-1F-01 head drawn on no sheet; masonry above 0 .. 4.992)",
                 "smallest_held_quantity": "net 11.273 .. 16.525 m2 (5.252 m2 wide: P-1F-01 masonry above the "
                                           "lintel 0 .. 4.992 + its 1.30 m passage), never 0"}},
        add("GF P-GF-05 ABOVE-LINTEL", w05,
            {"length_m": "1.200", "held_length_m": "0.000", "length_class": R.SS, "height_weighted_m": R3(Gp / 1.2),
             "gross_m2": R3(Gp), "gross_class": R.SS, "deductions_m2": "0.000", "net_m2": R3(Gp), "net_class": R.SS,
             "openings_in_run": "P-GF-05 (below this piece)",
             "evidence": f"court wall WB-FL0017-FL0018 gap 1.200 m on {ARCH} GF plan; head +2.65 (T-201) + lintel L2 0.20 "
                         f"(T-207) -> top +2.85; B1 20x40 band 2AE / 2AF over the opening on {ST} GROUND FLOOR ROOF "
                         f"SLAB, structural top +5.45 (T-214) -> soffit +5.05; 1.20 x (5.05 - 2.85)",
             "unresolved_reason": "component re-measured by the Checker 20:14 (2.640, 0.0 %); not VERIFIED as a wall "
                                  "line (Checker: component only)",
             "checker_remeasured": "length, head, soffit (Checker 20:14: 1.200 m gap, head +2.64 .. +2.68, B1 2AE / 2AF, "
                                   "+5.45; 2.640 m2 = worker 0.0 %)"},
            "masonry above the P-GF-05 lintel, HELD 2.232 .. 2.700 in T-108 / T-215 (in no wall row)"),
    ]


def t238_changes():
    for d in rd("research/agents_t238/DELTA_T238.csv"):
        if d["line"].startswith("BLOCKWORK (2F-W07)"):
            return [{"wall_id": "2F-W07", "source": "T-238", "set": {"deductions_m2": d["new"]},
                     "why": f"W26 masonry deduction {d['old']} -> {d['new']} (true arched outline; Checker 1.8745)"}]
    raise R.RegisterError("MISSING_INPUT", "T-238 2F-W07 row not found")


def rulings():
    """Checker verdicts that set a wall's figures (the Checker's own numbers, never the worker's)."""
    return [
        {"wall_id": "GF-W07", "source": "RULING T-226 18:01", "remeasured": {"length", "height", "deductions"},
         "why": "Checker own drawn-edge pieces: B1 0.950 x 4.10 + CB1 band 0.150 x 3.75 = 4.458 (worker 4.468 refused: "
                "sampled boundary 0.98 / 0.12); no opening in the run",
         "set": {"gross_m2": "4.458", "net_m2": "4.458", "height_weighted_m": R3(4.458 / 1.1), "gross_class": R.VER,
                 "net_class": R.VER, "owner_status_class": R.VER, "net_bounds_m2": "",
                 "verified_by_checker": "VERIFIED m2 (length 1.100, heights 4.10 / 3.75 by the drawn band edges, no "
                                        "opening; Checker 18:01); block type white = Q-60 fallback (PROJECT-SPECIFIC)",
                 "checker_remeasured": "length, height pieces, openings (none)",
                 "unresolved_reason": "", "smallest_held_quantity": ""}},
        {"wall_id": "1F-W05", "source": "RULING T-226 18:01", "remeasured": {"length", "height"},
         "why": "Checker own pieces CB10 2.300 + 3.652 at 3.70 + B23 0.348 at 3.45 = 23.223 (worker 23.254 refused: the "
                "last 0.10 m spread at the mean height); W14 width 2.449 re-measured, height 1.60 not",
         "set": {"gross_m2": "23.223", "height_weighted_m": R3(23.223 / 6.3), "gross_class": R.VER,
                 "net_m2": "19.303", "net_class": R.SS, "owner_status_class": R.SS,
                 "verified_by_checker": "gross VERIFIED (Checker 18:01); net SOURCE-SUPPORTED (W14 height 1.60 not "
                                        "re-measured)",
                 "checker_remeasured": "length, height pieces, W14 width",
                 "unresolved_reason": "net pending the Checker's re-measure of the W14 height (1.60, T-175)"}},
        {"wall_id": "GF-W10", "source": "RULING GF-W10 21:15", "remeasured": {"deductions-partial"},
         "why": "Checker: W05 / W06 / W07 0.60 x 0.80 = 0.480 each (own SW elevation read), D-GF-09 0.90 x 2.20 = 1.980 "
                "(door height Q-55 C), net 50.845 - 3.420 = 47.425 accepted; W.C. stretch level not drawn: HELD "
                "increment",
         "set": {"deductions_m2": "3.420", "held_openings": "", "net_m2": "47.425", "net_class": R.PS,
                 "owner_status_class": R.PS,
                 "net_bounds_m2": "47.425 on the +1.00 floor basis + HELD 0 .. 0.70 x L(W.C. stretch)",
                 "held_increment_m2": "0 .. 0.70 x L(W.C. stretch): the W.C. behind W05 carries no level mark on the GF "
                                      "plan or ST p.3 (+0.30 annex / +1.00 main); L not measured (see report s.4)",
                 "held_cause_class": "", "next_package": "designer (D-45 family / T-088): W.C. floor level",
                 "verified_by_checker": "deductions W05-W07 re-measured (Checker 21:15); gross 50.845, length 12.870 "
                                        "and height 4.00 not; D-GF-09 width not",
                 "checker_remeasured": "W05 / W06 / W07 sizes; CB2 pieces 3.470 + 3.350 at 4.00 (18:01)",
                 "unresolved_reason": "net PROJECT-SPECIFIC: D-GF-09 height 2.20 is the Q-55 C owner fallback "
                                      "(ASSUMED — OWNER-APPROVED); + HELD increment for the W.C. stretch level",
                 "smallest_held_quantity": "0 .. 0.70 x L(W.C. stretch) m2 above the 47.425 (L not measured)"}},
        {"wall_id": "2F-W08", "source": "RULING T-108 09:11", "remeasured": {"length", "height"},
         "why": "Checker own read: 3.000 m clear (faces 128B / 128F, 128C / 1290; north face 127A / 127B; column 2F6F), "
                "B3 20x40 band 399 / 39C under +9.70 -> +13.90: 3.80; D-2F-03 0.80 x 2.20 (Q-55 C)",
         "set": {"gross_class": R.VER,
                 "verified_by_checker": "gross VERIFIED 11.400 (Checker 07:13 / 09:11); net 9.640 re-computed by the "
                                        "Checker but rests on the Q-55 C door height: PROJECT-SPECIFIC",
                 "checker_remeasured": "length 3.000, height 3.80, door width 0.80"}},
        {"wall_id": "GF-W01", "source": "RULING T-143", "remeasured": {"length", "height"},
         "why": "Checker own spans and members (T-143): 16.470 m, 62.155 m2 (0.0 %)",
         "set": {"gross_class": R.VER,
                 "verified_by_checker": "gross VERIFIED 62.155 (Checker, T-143: spans and beams own); net = gross "
                                        "with no opening in the run, but the opening census of the run was not part "
                                        "of that check: net SOURCE-SUPPORTED",
                 "checker_remeasured": "length (4 spans), height per member"}},
    ]


A10 = f"{DRIVE} / p7757_arch_sheet10.pdf (section A-A, 1:100)"
V0959 = "Verifier 2026-10-24 09:59 UTC (T-228 REJECTED, gate e + h; narrow r2)"

# R-T228-3 input: member lines that carry a '(With Stair)' mark on at least one storey frame (own read of ST7757 dxf
# this run, by entity handle; members by the T-110 register, MERGED). Frames: GF = GROUND FLOOR ROOF SLAB (block GFRS),
# 1F = FIRST FLOOR ROOF SLAB (FFRS), 2F = SECOND FLOOR ROOF SLAB (SFRS). A member of one line sits at the same plan
# position on every frame (checked against the T-110 register by line_positions_ok()).
STAIR_LINES = [
    {"line_id": "SL-1 (ST-01 dog-leg shaft beside the lift, outer wall line)",
     "members": {"GF": "BM-GF-015", "1F": "BM-1F-001", "2F": "BM-2F-001"},
     "spans": {"GF": "BEAMS:GF:BAND0016.1", "1F": "BEAMS:1F:BAND0001.1", "2F": "BEAMS:2F:BAND0001.1"},
     "with_stair": {"GF": f"{ST} GFRS frame: text 6B6 '(With Stair)' beside the B3 mark 6B7 (BM-GF-015)",
                    "1F": f"{ST} FFRS frame: text 6B8 '(With Stair)' beside the B3 mark 6B9 (BM-1F-001)"},
     "floor_level_mark": {},
     "floor_at_basis": {},
     "no_floor_evidence": (f"GFRS and FFRS print only 'B3 (With Stair)' on this span (no floor-level band mark; the next "
                           f"marks are CB2 42A / CB9 6C6 on the next span); SFRS prints a plain B3 (79D). {A10}: no slab "
                           f"cut at +5.50 or +9.70 on the stair-wall line; landing members at +3.50 printed and about "
                           f"+7.6 ({V0959}); T-184 ST-01: GF +1.00 -> landing +3.50 -> 1F +5.50 -> landing +7.516 / "
                           f"+7.684 -> 2F +9.70, the floor landings at the far end of the shaft; GF: the stair-foot "
                           f"piece stands on the PRINTED +0.30 landing (F1), not the +1.00 basis")},
    {"line_id": "SL-2 (ST-02 round stair, straight flight along CB3 span 2)",
     "members": {"GF": "BM-GF-057", "1F": "BM-1F-023"},
     "spans": {"GF": "BEAMS:GF:BAND0019.2", "1F": "BEAMS:1F:BAND0027.2"},
     "other_spans_m": {"1F": [6.7083, 3.3]},     # BM-1F-023 spans 1 / 3 (T-110 BAND0027.1 / .3), not under the flight
     "with_stair": {"GF": f"{ST} GFRS frame: text 1826 '(With Stair)' beside the B3 mark 1827 over CB3 span 2 "
                          f"(BM-GF-057)"},
     "floor_level_mark": {"GF": "CB3 20x75 printed under each of the band's 3 spans incl. span 2 (T-110 BM-GF-057; "
                                "T-084: 'B3 (With Stair)' is the cranked stair beam of the TYPICAL DETAIL OF STAIR "
                                "BEAM, a member of its own beside the floor-level CB3)"},
     "floor_at_basis": {"1F": "the floor-level CB3 band printed on the GFRS frame under span 2 carries the 1F floor at "
                              "this line (Q-61 (2) designer item on the B3 / CB3 count stays open: if the designer "
                              "removes CB3 from span 2 this check re-runs)"},
     "no_floor_evidence": "GF: the GF base of GF-W03 under the flight is not printed (GF-W03 already HELD)"},
]
FRAME_STEP_TOL, FRAME_Y_TOL = 0.01, 0.06


def line_positions_ok():
    """Every member of a stair line sits at the same plan position after the frame offset (T-110 x / y, m): one common
    step between consecutive frames for all lines. Returns a list of problems (empty = consistent)."""
    reg = {(r["member_id"], r["component"]): r for r in rd("research/agents_t110/BEAM_MEMBER_REGISTER.csv")}
    steps, bad = [], []
    for ln in STAIR_LINES:
        fr = sorted(ln["members"], key=R.STOREYS.index)
        for a, b in zip(fr, fr[1:]):
            ra, rb = (reg[(ln["members"][a], ln["spans"][a])], reg[(ln["members"][b], ln["spans"][b])])
            steps.append(f(ra["x"]) - f(rb["x"]))
            if abs(f(ra["y"]) - f(rb["y"])) > FRAME_Y_TOL or abs(f(ra["length_m"]) - f(rb["length_m"])) > 0.02:
                bad.append(f"{ln['line_id']}: {ln['members'][a]} / {ln['members'][b]} not at one plan position")
    if steps and max(steps) - min(steps) > FRAME_STEP_TOL:
        bad.append(f"frame steps differ: {min(steps):.3f} .. {max(steps):.3f} m")
    return bad


PIECE = __import__("re").compile(r"(\S+) (BM-(?:GF|1F|2F|3F|RF)-\d{3}) \(h [^)]*\): ([\d.]+) m -> h ([\d.]+|HELD)")
EXTRA_PIECES = [  # pieces whose v1 evidence names the member by its marks only (no BM id in the piece text)
    {"wall_id": "GF-W03", "storey": "GF", "member_top": "BM-GF-057", "length_m": "2.650", "height_m": "HELD",
     "mark": "CB3 and B3 (With Stair)"}]


def wall_pieces(rows):
    """Pieces per wall from the first 'member above / height' list of its evidence (later '||' copies repeat it)."""
    out = []
    for r in rows:
        ev = r["evidence"].split(" || ")[0]
        if "member above / height:" not in ev:
            continue
        seg = ev.split("member above / height:", 1)[1].split("; storey heights", 1)[0]
        for m in PIECE.finditer(seg):
            out.append({"wall_id": r["wall_id"], "storey": r["floor"], "member_top": m.group(2), "length_m": m.group(3),
                        "height_m": m.group(4), "mark": m.group(1)})
    return out + EXTRA_PIECES


def stair_check(rows):
    return R.stair_line_flags(wall_pieces(rows), STAIR_LINES)


FINDINGS = [
    {"wall_id": "GF-W10", "source": "T-228 FINDING F1 (pending Checker)",
     "reference": "own read: P7757.dxf GF plan + section A-A; r2: Checker figures of the eastern pieces (" + V0959 + ")",
     "why": "the 2.500 m stair-foot piece of GF-W10 stands on a PRINTED +0.30 landing, not the +1.00 basis of the "
            "47.425, and section A-A cuts a concrete member on the wall line over D-GF-09: its masonry top is not B3; "
            "r2: R-T228-3 flags the piece (SL-1 base and top), so the wall gross is not established either",
     "set": {"gross_class": "HELD", "net_class": "HELD", "owner_status_class": "HELD", "net_m2": "", "net_m3": "",
             "held_cause_class": "stair-foot datum and top (T-228 F1)",
             "net_bounds_m2": "47.425 on the +1.00 basis (Checker 21:15) is NOT the net. Eastern pieces as their own "
                              "figure (Checker 2026-10-24 09:59): CB2 3.470 x 4.00 + CB2 3.350 x 4.00 + B24 3.550 x 3.75 "
                              "= 40.5925 - W05 / W06 / W07 1.440 = 39.1525 m2 on the +1.00 basis (SOURCE-SUPPORTED, "
                              "the register keeps one row per v1 wall, so the figure is carried here and in "
                              "STAIR_LINE_CHECK.csv) + W.C. stretch 0 .. 0.945 HELD; the stair-foot piece (2.500 m, "
                              "B3 4.10 basis 10.250 - D-GF-09 1.980 = 8.270, not a quantity) is HELD (R-T228-3, F1)",
             "pending_findings_t228": "F1: stair-foot piece of GF-W10 (2.500 m between the column faces S-COL.BON 2F7E "
                                      "and the 213 / 21A column stub, inner face lines 26E / 2AB, door D-GF-09 jambs at "
                                      "the 0.900 m gap of the outer face 2B8): plan LEVEL insert 4AB / text 4AC '+0.30' "
                                      "inside the landing (court outside +0.15, 40A / 4AE); section A-A (cut through "
                                      "D-GF-09) prints +0.30 on the landing, +0.15 outside and '320' from the landing "
                                      "to a hatched (concrete) member on the wall line over the door; the stair shaft "
                                      "carries no 1F slab on that line. F2: W.C. stretch behind W05 = 1.350 m (inner "
                                      "face 2AD / 271 between the column stub 213 and the W.C. partition face; W05 "
                                      "jambs 3E2 / 3E1), no level mark in the W.C.: increment 0 .. 0.70 x 1.350 = "
                                      "0 .. 0.945 m2 (Checker 21:15 basis)",
             "held_increment_m2": "W.C. stretch 0 .. 0.945 (L 1.350 m measured this run, level not drawn)",
             "unresolved_reason": "stair-foot piece: base +0.30 printed (plan and A-A), top = the stair landing member "
                                  "on the wall line (size / soffit from the stair detail, Q-72 / T-173 family), not B3; "
                                  "W.C. floor level not drawn; D-GF-09 height Q-55 C (A-A draws the opening under the "
                                  "member; not scaled here)",
             "next_package": "lane A / S: stair-shaft member on the GF-W10 line (ST stair detail); Checker: F1 / F2",
             "smallest_held_quantity": "stair-foot piece 8.270 m2 on the +1.00 basis (not a quantity) + W.C. 0 .. 0.945; "
                                       "the eastern pieces 39.1525 m2 (Checker 09:59) wait only on the F1 ruling"}},
    {"wall_id": "1F-W10", "source": "T-228 r2 FINDING F3 (R-T228-3; pending Checker)",
     "reference": V0959 + "; own read of ST7757 dxf this run (texts 6B6 / 6B8)",
     "why": "the package's own stair-foot finding F1 applies unchanged to the sibling piece one storey up: the B3 "
            "piece 2.500 m of 1F-W10 lies on line SL-1, whose GFRS / FFRS frames print 'B3 (With Stair)' with no "
            "floor-level member and A-A cuts no slab at +5.50 / +9.70 on that line: the +5.50 floor it was measured on "
            "does not exist there, its top is the cranked stair beam",
     "set": {"gross_class": "HELD", "net_class": "HELD", "owner_status_class": "HELD", "net_m2": "", "net_m3": "",
             "held_cause_class": "stair-shaft piece (T-228 F3, R-T228-3)",
             "net_bounds_m2": "gross 47.869 m2 is NOT established: the three CB9 pieces (3.470 + 3.350 + 3.550 = 10.370 "
                              "m x 3.70) give 38.369 m2 on the +5.50 basis (figure, not a quantity); the B3 piece "
                              "(2.500 m, 3.80 basis 9.500) is HELD; W21 / W22 / W23 / W25 2.940 are not assigned to "
                              "pieces, so no net is formed",
             "unresolved_reason": "B3 piece of SL-1 (ST-01 shaft): no floor at +5.50 on the stair-wall line (A-A), "
                                  "masonry between the +3.50 / about +7.6 landing members and the cranked B3 (With "
                                  "Stair); base / top / height not printed as a wall datum",
             "next_package": "lane A / S: ST-01 shaft wall by landing member (ST stair detail, A-A); Checker: F3",
             "smallest_held_quantity": "B3 piece 2.500 m (9.500 m2 on the +5.50 basis, not a quantity); the CB9 pieces "
                                       "38.369 m2 wait only on the opening split",
             "pending_findings_t228": "F3 (r2, R-T228-3): SL-1 member BM-1F-001 (FFRS 'B3 (With Stair)' text 6B8); base "
                                      "frame GFRS prints 'B3 (With Stair)' text 6B6 at the same plan position "
                                      "(BM-GF-015), no floor-level mark on that span; A-A no slab cut at +5.50; "
                                      "Verifier 09:59 gate e + h"}},
    {"wall_id": "2F-W02", "source": "T-228 r2 FINDING F4 (R-T228-3; already HELD)",
     "reference": V0959,
     "why": "the B3 piece 2.500 m of 2F-W02 (BM-2F-001) lies on SL-1: its base frame FFRS prints 'B3 (With Stair)' "
            "(6B8), A-A cuts no slab at +9.70 on the line: HELD by R-T228-3 as well (the wall was already HELD: beam "
            "depth BM-2F-015 / openings)",
     "set": {"pending_findings_t228": "F4 (r2, R-T228-3): B3 piece 2.500 m (BM-2F-001, SFRS plain B3 79D) on SL-1; base "
                                      "frame FFRS 'B3 (With Stair)' 6B8, no floor-level mark, A-A no slab at +9.70: "
                                      "HELD (already HELD by the BM-2F-015 depth; both causes must clear)"}},
    {"wall_id": "GF-W03", "source": "T-228 r2 FINDING F5 (R-T228-3; already HELD)",
     "reference": "own read of ST7757 dxf this run (text 1826)",
     "why": "GF-W03 (2.650 m under CB3 span 2 / 'B3 (With Stair)', SL-2): its GF basis under the round-stair flight is "
            "not printed: HELD by R-T228-3 as well (already HELD: two marks D-03 / Q-61 (2))",
     "set": {"pending_findings_t228": "F5 (r2, R-T228-3): SL-2 GFRS 'B3 (With Stair)' 1827 / 1826 over CB3 span 2; "
                                      "base not printed: HELD (already HELD by D-03 / Q-61 (2))"}},
]


def census_annotations(rows):
    """T-017 (merged check tool): census length, difference, cause and verdict per wall; corner squares as the
    proposed UP-MAS-CORNER-001 reading beside the ledger length (no quantity changed)."""
    by = {r["row_id"]: r for r in rd("research/agents_t017/T017_WALL_AGREEMENT.csv")}
    for r in rows:
        c = by.get(r["wall_id"])
        if not c:
            r["census_t017_status"] = "NOT IN THE T-017 LIST (piece added after the census)" if r["v2_sources"] else ""
            continue
        r["census_t017_status"] = c["status"]
        r["census_t017_length_m"] = c["census_arch_run_m"]
        r["census_t017_minus_ledger_m"] = c["census_minus_ledger_m"]
        r["census_t017_cause"] = c["cause"]
        r["census_t017_verdict"] = c["verdict_proposal"]
        if c["cause"] == "CORNER_SQUARE_OWNERSHIP":
            r["length_under_UP-MAS-CORNER-001_m (proposed rule, not applied)"] = c["census_arch_run_m"]
        if r["wall_id"] == "GF-W30":
            r["length_bounds_m"] = (f"{f(c['census_arch_run_m']):.3f} .. {f(r['length_m']):.3f} (census both faces + "
                                    f"door + stub + corner .. hand to the oblique centreline; Checker 23:08: range "
                                    f"holds)")


def finish(rows, changed):
    for r in rows:
        if r["wall_id"] not in changed:
            continue
        t, n = f(r["t_m"]), r["net_m2"]
        if r["net_class"] in R.ESTABLISHED:
            r["net_m3"] = R3(f(n) * t)
            ty = r["block_type"]
            if ty == "WHITE":
                r["t176_products"] = (f"WHITE_62.5x25 {f(n) * WHITE_F[0]:.3f} pcs (ASSUMED — OWNER-APPROVED); "
                                      f"WHITE_60x20 {f(n) * WHITE_F[1]:.3f} pcs (ASSUMED — OWNER-APPROVED)")
            elif ty == "BLACK":
                r["t176_products"] = f"BLACK_40x20 {f(n) * BLACK_F:.3f} pcs (ASSUMED — OWNER-APPROVED)"
        else:
            r["net_m3"] = ""
        r["owner_status_class"] = r["net_class"]
        if (r["net_class"] == R.HELD and r["held_cause_class"] == "held opening" and not has(r["held_openings"])
                and "annex datum" in r["unresolved_reason"]):
            # its openings were resolved (T-227 heads); what still holds it is the annex datum named in its reason
            r["held_cause_class"] = "annex datum (Q-54 B)"
            r["next_package"] = "designer D-39 (annex roof slab top / build-up); owner Q-54 B HOLD"
        if r["net_class"] in R.ESTABLISHED and r["net_class"] != R.HELD:
            r["held_cause_class"] = r["held_cause_class"] if r["held_increment_m2"] else ""
        calc(r)
        r["source_ledgers"] = (r["source_ledgers"] + " + v2: " + r["v2_sources"]).strip(" +")


def calc(r):
    hl = f(r["held_length_m"])
    net = f"net {r['net_m2']} m2" if r["net_class"] in R.ESTABLISHED else "net HELD"
    inc = f"; + HELD increment {r['held_increment_m2'].split(' (')[0].split(':')[0]}" if r["held_increment_m2"] else ""
    r["calculation"] = (f"({r['length_m']} - held {hl:.3f}) m x h_w {r['height_weighted_m'] or 'HELD'} m = gross "
                        f"{r['gross_m2'] or 'HELD'} m2 ({r['gross_class']}); - deductions {r['deductions_m2'] or '0.000'}"
                        f" m2 = {net}{inc}")


def after_hold(rows, held_ids):
    """Derived fields of a wall a finding held (r2): the calculation text and the T-176 product counts follow the
    HELD net (a count on a held net is not carried)."""
    for r in rows:
        if r["wall_id"] in held_ids and r["net_class"] == R.HELD:
            calc(r)
            if r["t176_products"] and "HELD pcs" not in r["t176_products"]:
                r["t176_products"] = "; ".join(f"{p.split(' ')[0]} HELD pcs (HELD)"
                                               for p in r["t176_products"].split("; "))


def build_register():
    base = v1()
    ch = (delta_changes(base, "research/agents_t226/register_delta.csv", "T-226")
          + delta_changes(base, "research/agents_t227/register_delta.csv", "T-227")
          + t215_changes(base) + t222_changes(base) + t238_changes() + rulings())
    srcs = defaultdict(list)
    for c in ch:
        if c["source"] not in srcs[c["wall_id"]]:
            srcs[c["wall_id"]].append(c["source"])
    for c in ch:
        c["set"] = {**c["set"], "v2_sources": " + ".join(srcs[c["wall_id"]])}
    rows, log = R.apply(base, ch, MERGED)
    finish(rows, set(srcs))
    rows, hlog = R.hold(rows, FINDINGS)
    after_hold(rows, {h["wall_id"] for h in FINDINGS if "net_class" in h["set"]})
    log += hlog
    census_annotations(rows)
    for r in rows:
        R.check_row(r)
    return v1(), rows, log


# ------------------------------------------------------------------------------------------------ reports
KEY = lambda r: (r["floor"], r["t_m"], r["block_type"])
COV_COLS = ("walls", "length_established_m", "length_held_m", "gross_figure_m2", "gross " + R.VER,
            "gross " + R.SS, "gross " + R.PS, "gross " + R.HELD, "net " + R.VER, "net " + R.SS, "net " + R.PS,
            "deductions_on_established_net_m2", "walls_net_held", "gross_figure_of_held_net_m2",
            "deductions_on_held_net_m2 (held scope)", "reconciliation_residual_m2")


def coverage_table(v1rows, v2rows):
    a, b = R.coverage(v1rows, KEY), R.coverage(v2rows, KEY)
    out = []
    for k in sorted(set(a) | set(b)):
        row = {"floor": k[0], "t_m": k[1], "block_type": k[2]}
        for c in COV_COLS:
            row[f"{c} v1"] = f"{a[k][c]:.3f}" if k in a else "0.000"
            row[f"{c} v2"] = f"{b[k][c]:.3f}" if k in b else "0.000"
        held = [r["wall_id"] + " (" + (r["held_cause_class"] or "held increment") + ")" for r in v2rows
                if KEY(r) == k and (r["net_class"] == R.HELD or r["held_increment_m2"])]
        row["held_walls_v2"] = "; ".join(held)
        out.append(row)
    return out


DESIGNER = {
    "stair-foot datum and top (T-228 F1)": "ST-01 shaft wall on the GF-W10 line: base +0.30 landing printed, top = "
                                           "the stair landing member / cranked 'B3 (With Stair)' (size and soffit "
                                           "from the ST stair detail); W.C. floor level not drawn",
    "stair-shaft piece (T-228 F3, R-T228-3)": "ST-01 shaft wall piece on the 1F-W10 line: no floor at +5.50 (A-A); "
                                              "base / top = the +3.50 and about +7.6 landing members and the cranked "
                                              "B3 (ST stair detail); opening split W21 / W22 / W23 / W25 by piece",
    "annex datum (Q-54 B)": "annex roof slab top / build-up (designer D-39; owner Q-54 B HOLD until the datum is "
                            "verified); B-B puts +4.30 on a layer over the roof band (T-227)",
    "lift tie beam size (ST p.8 n.19)": "size b x h of the GF lift tie beam at +3.00 (ST p.8 note 19; consultant row 7 "
                                        "send-ready, D-43); lift landing heads drawn on no sheet",
    "beam depth / register conflict": "depth of the member above (T-110 register: unprinted depth or CONFLICT, Q-61 C, "
                                      "designer); GF-W03 CB3 / B3 two marks D-03",
    "no member drawn above": "no beam / slab underside drawn over the piece (dome openings 'SEE DETAIL' ring B4, "
                             "1F partitions; column faces); top of wall not drawn",
    "held opening": "opening size (head / height) drawn on no sheet for an opening in the run",
    "no wall band or member bound (glazed line / held strip)": "material, base and top of the 0.40 strip / the 0.20 "
                                                               "outline: printed nowhere (T-227 c)",
}


def blockers(v2rows):
    out = []
    for r in v2rows:
        if r["net_class"] != R.HELD and not r["held_increment_m2"]:
            continue
        cause = r["held_cause_class"] or ("held increment" if r["held_increment_m2"] else "")
        if r["net_class"] == R.HELD:
            if r["gross_class"] == R.HELD and cause.startswith("stair-"):
                kind = "gross and net HELD (stair-line piece, R-T228-3)"
                smallest = r["smallest_held_quantity"]
            elif r["gross_class"] == R.HELD:
                kind = "gross and net HELD"
                smallest = f"gross figure {r['gross_m2'] or '0.000'} m2 on the established pieces (not a quantity)"
                if f(r["held_length_m"]):
                    smallest += f" + held length {r['held_length_m']} m with no height"
            else:
                kind = "gross established, net HELD"
                smallest = (f"net bounds {r['net_bounds_m2']}" if r["net_bounds_m2"]
                            else f"net HELD on gross {r['gross_m2']} ({r['held_openings'] or 'opening'} size)")
        else:
            kind = "net established + HELD increment"
            smallest = r["held_increment_m2"]
        out.append({"wall_id": r["wall_id"], "floor": r["floor"], "t_m": r["t_m"], "block_type": r["block_type"],
                    "status": kind, "cause_class": cause,
                    "exact_missing_item": DESIGNER.get(cause, r["unresolved_reason"][:240]),
                    "wall_specific": r["unresolved_reason"][:400], "held_openings": r["held_openings"],
                    "smallest_affected_quantity": smallest, "gross_figure_m2 (not a quantity when HELD)": r["gross_m2"],
                    "next": r["next_package"]})
    return out


SECTION = lambda r: ("EXTERNAL" if r["group"] == "EXTERNAL" else f"INTERNAL {'0.15' if r['t_m'] == '0.15' else '0.20'}"
                     if r["group"] == "INTERNAL" else "HELD STRIP")


def freelancer_table(v1rows, v2rows):
    fl = {(r["floor"], r["freelancer_section"]): r for r in rd("research/agents_t225/THREE_WAY_BY_FLOOR_SECTION.csv")}
    agg = lambda rows: _agg(rows)
    a, b = agg(v1rows), agg(v2rows)
    out = []
    for k in sorted(fl, key=lambda k: (["GF", "1F", "2F"].index(k[0]), k[1])):
        x = fl[k]
        e1, e2 = a.get(k, defaultdict(float)), b.get(k, defaultdict(float))
        out.append({"floor": k[0], "freelancer_section": k[1],
                    "freelancer_length_m": x["freelancer_length_m (sum B x C)"],
                    "freelancer_gross_m2": x["freelancer_gross_m2"], "freelancer_deductions_m2": x["freelancer_deductions_m2"],
                    "freelancer_net_m2": x["freelancer_net_m2"],
                    "engine_length_v2_m": f"{e2['L']:.3f}", "engine_held_length_v2_m": f"{e2['HL']:.3f}",
                    "engine_net_established_v1_m2": f"{e1['N']:.3f}", "engine_net_established_v2_m2": f"{e2['N']:.3f}",
                    "engine_net_verified_v2_m2": f"{e2['NV']:.3f}",
                    "engine_walls_net_held_v2": int(e2["H"]),
                    "like_for_like": "NO (engine walls held: missing, not 0)" if e2["H"] or e2["HL"] else "YES (net)",
                    "freelancer_other_scope_in_section": x["freelancer_other_scope_in_section"],
                    "note": "comparison column only (programme s.5): never an input or a target"})
    return out


def _agg(rows):
    out = defaultdict(lambda: defaultdict(float))
    for r in rows:
        a = out[(r["floor"], SECTION(r))]
        a["L"] += f(r["length_m"])
        a["HL"] += f(r["held_length_m"])
        if r["net_class"] in R.ESTABLISHED:
            a["N"] += f(r["net_m2"])
            if r["net_class"] == R.VER:
                a["NV"] += f(r["net_m2"])
        else:
            a["H"] += 1
    return out


def to_csv(rows, cols=None):
    cols = cols or list(rows[0].keys())
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in cols})
    return s.getvalue()


def listed_lengths(v1rows, v2rows):
    a = {r["wall_id"]: f(r["length_m"]) for r in v1rows}
    out = {}
    for r in v2rows:
        d = f(r["length_m"]) - a.get(r["wall_id"], 0.0)
        if abs(d) > 1e-9:
            out[r["wall_id"]] = round(d, 4)
    return out


def summary(v1rows, v2rows, log):
    def tot(rows):
        t = defaultdict(float)
        for r in rows:
            g = f(r["gross_m2"])
            t["gross_figure"] += g
            t["gross " + r["gross_class"]] += g
            if r["net_class"] in R.ESTABLISHED:
                t["net " + r["net_class"]] += f(r["net_m2"])
                t["net_m3 established"] += f(r["net_m3"])
            else:
                t["walls_net_held"] += 1
            t["walls"] += 1
            t["length"] += f(r["length_m"])
            t["held_length"] += f(r["held_length_m"])
        return {k: round(v, 3) for k, v in sorted(t.items())}
    raised = [r["wall_id"] for r, o in zip(v2rows, v1rows + [{}] * 9)
              if r["net_class"] in R.ESTABLISHED and _v1class(v1rows, r["wall_id"]) not in R.ESTABLISHED]
    return {"package": "T-228", "v1": tot(v1rows), "v2": tot(v2rows), "changes": len(log),
            "changes_by_source": {s: sum(1 for c in log if c["source"] == s) for s in MERGED},
            "walls_net_newly_established": raised,
            "walls_verified_net": [r["wall_id"] for r in v2rows if r["net_class"] == R.VER],
            "walls_verified_gross": [r["wall_id"] for r in v2rows if r["gross_class"] == R.VER],
            "length_changes_listed_m": listed_lengths(v1rows, v2rows),
            "length_identity_residual_m": R.length_identity(v1rows, v2rows, listed_lengths(v1rows, v2rows)),
            "blockers": len(blockers(v2rows))}


def _v1class(v1rows, wid):
    for r in v1rows:
        if r["wall_id"] == wid:
            return r["net_class"]
    return R.HELD


STAIR_COLS = ("line_id", "wall_id", "storey", "member_top", "mark", "length_m", "height_m", "flagged", "reasons",
              "wall_gross_class_v2", "wall_net_class_v2", "wall_figures", "line_evidence")


def stair_table(v2rows):
    by = {r["wall_id"]: r for r in v2rows}
    ev = {ln["line_id"]: " | ".join(list(ln["with_stair"].values()) + list(ln["floor_level_mark"].values())
                                    + [ln["no_floor_evidence"]]) for ln in STAIR_LINES}
    out = []
    for x in stair_check(v2rows):
        r = by[x["wall_id"]]
        out.append({**{k: x[k] for k in STAIR_COLS[:9]}, "flagged": "HELD" if x["flagged"] else "not held (floor printed)",
                    "wall_gross_class_v2": r["gross_class"], "wall_net_class_v2": r["net_class"],
                    "wall_figures": r["net_bounds_m2"] if x["flagged"] else f"net {r['net_m2']} m2 ({r['net_class']})",
                    "line_evidence": ev[x["line_id"]]})
    return out


def outputs():
    a, b, log = build_register()
    cols = list(b[0].keys())
    return {
        "STAIR_LINE_CHECK.csv": to_csv(stair_table(b), list(STAIR_COLS)),
        "BLOCKWORK_WALL_REGISTER_V2.csv": to_csv(b, cols),
        "CHANGE_LOG_V2.csv": to_csv(log),
        "AFTER_COVERAGE.csv": to_csv(coverage_table(a, b)),
        "BLOCKERS_V2.csv": to_csv(blockers(b)),
        "FREELANCER_COMPARISON_V2.csv": to_csv(freelancer_table(a, b)),
        "summary.json": json.dumps(summary(a, b, log), indent=1, ensure_ascii=False) + "\n",
    }


def ancestry_ok() -> list:
    bad = []
    for c in COMMITS:
        try:
            p = subprocess.run(["git", "-C", str(ROOT), "merge-base", "--is-ancestor", c, "HEAD"], capture_output=True)
        except OSError:
            return []
        if p.returncode not in (0,):
            bad.append(c)
    return bad


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    out = outputs()
    if "--check" in argv:
        diff = [n for n, s in out.items() if (HERE / n).read_text(encoding="utf-8") != s]
        bad = ancestry_ok()
        print("CHECK", "PASS" if not diff and not bad else f"FAIL {diff} not-ancestor {bad}")
        return 1 if diff or bad else 0
    for n, s in out.items():
        (HERE / n).write_text(s, encoding="utf-8")
    print("wrote", ", ".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
