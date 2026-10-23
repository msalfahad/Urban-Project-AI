"""T-227 on the development villa: blockwork resolution 3/4 (annex datum, lift walls and openings, the 0.40 strip and
GF-H02, the 1F pieces under the two dome openings, the window heads still HELD in the T-225 register v1).

Read-only over merged ledgers; no engine module, method, rule / knowledge version or registry is changed. Inputs (all
committed, merged): research/agents_t225/BLOCKWORK_WALL_REGISTER_V1.csv (T-225, MERGED 48e6f08a), research/agents_t201/
HEADS_T201.csv (T-201, MERGED 5dade783, Checker 07:00: 26 / 29 heights DRAWING-CONFIRMED, 5 VERIFIED),
research/agents_t207/CLOSURE_T207.csv (T-207, MERGED e081911c: W11 / W12 1.95 x 2.20). register_delta.csv holds only
the rows this package changes (v1 is never edited; T-228 builds register v2 from the deltas).

Drawings read this run (cited by Drive folder and title; no drawing content, coordinate or image in the repository):
  Alsenan_Architectural_P7757_Pages_11-12.pdf p.1 SECTION B-B (annex box: floor +0.30, roof mark +4.30 with its
    marker on the TOP of a thin unhatched layer over the hatched roof band; parapet to +4.80; 1F roof band
    continuous under the domes, which are drawn beyond the cut); p.2 fence sheet (no roof detail);
  p7757_arch_sheet10.pdf SECTION A-A (stairs; no lift shaft or landing door drawn);
  ST7757.pdf p.8 RECOMMENDATIONS notes 18 (slabs 16 cm unless stated) and 19 (lift-column tie beams at 3.00 m where
    the storey is higher than 4.30 m; no section); ST7757 dxf.dxf (sha 9f9d1179): every TEXT / MTEXT / ATTRIB /
    DIMENSION (nested): no structural level, no '+4.30', no roof build-up, no tie-beam size; GROUND FLOOR ROOF SLAB
    plan at GF-H01 (B20 band 0.40 with a column inside, section A-A mark 0.95 m west of the column, looking west);
    FIRST FLOOR ROOF SLAB dome openings (circles r 2.211 / 2.411 with radial 'SEE DETAIL' lines) over the 1F pieces;
  P7757.dxf (sha ab54dd55): all text: '+4.30' only as two level marks, no roof / insulation / lift text; plan at
    GF-H01 (0.40 band, both sides exterior, 1.40 m with a 0.80 column) and at the dome openings (1F bath / living
    partition crossing inside the circle).

Usage: python3 -I research/agents_t227/alsenan_t227.py [--check]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import datum_rules as R  # noqa: E402

DRIVE = "Drive 'Alsenan chalet project'"
V1 = ROOT / "research/agents_t225/BLOCKWORK_WALL_REGISTER_V1.csv"
HEADS = ROOT / "research/agents_t201/HEADS_T201.csv"
CLOSURE = ROOT / "research/agents_t207/CLOSURE_T207.csv"
PKG = "T-227"
SS = R.SS

# ---------------------------------------------------------------------------------------------- (a) annex datum
ANNEX_MARKS = {
    "floor": dict(level_m=0.30, kind="FLOOR", drawn_layer_m=0.05, drawn_layer_zone_type="DRY", zone_type="DRY",
                  falls_printed=False),
    "roof": dict(level_m=4.30, kind="ROOF", drawn_layer_m=0.05, drawn_layer_zone_type="ROOF", zone_type="ROOF",
                 falls_printed=True),
}
ANNEX_TEST = [
    ("SECTION B-B (Pages_11-12 p.1)", "the +4.30 marker apex sits on the TOP line of a thin unhatched layer laid over the "
     "hatched roof band (same drawing as T-214's 0.050 / 0.200 band, read again this run at 500 dpi); +4.30 is the "
     "finished-roof line, the hatched structure lies below it", "NOT THE SLAB"),
    ("ST7757 dxf.dxf, all text (nested)", "no structural level of any slab (only the architect's FFL marks +0.15 / "
     "+0.30 / +1.00 / +9.70 copied on the ground-beam plan), no '+4.30', no roof build-up; note 18: slab 0.16 'unless "
     "stated' (thickness only, no level)", "SILENT"),
    ("ST7757.pdf p.1-16 (T-206 read all 16; p.8 re-read this run)", "no S.S.L / T.O.S of the annex roof; the only S.S.L "
     "values are the N.T.S. stair template of p.16 (not a project datum, T-206)", "SILENT"),
    ("roof build-up / roof detail", "no roof detail in the architectural set (Pages_11-12 p.2 is the fence; P7757.dxf "
     "has no roof / insulation / waterproofing text); the only 'INSULATION MEMBRANE' text in ST7757 dxf.dxf is a "
     "foundation detail", "SILENT"),
    ("sanitary-7757.pdf (T-214 citation)", "SLOPE 1 % printed on the +4.30 annex roof: the build-up varies, so a "
     "constant drawn 0.05 cannot be the roof build-up (T-214 CONSTANT_LAYER_VS_FALLS, MERGED b29060c2)", "NOT THE SLAB"),
    ("elevations (T-063 / T-200 DRAWING-CONFIRMED)", "+4.30 roof and parapet +4.80 ('480', 0.50 parapet) on the same "
     "convention as the +5.50 / +9.70 terraces, which are finished levels (T-200)", "FINISHED LEVEL"),
    ("annex door / window heads (T-201)", "W04 / W08 heads +2.80 (2.50 above +0.30): they fix the openings, not the slab "
     "(1.50 m below +4.30 with the lintel and masonry between)", "SILENT"),
    ("annex floor (T-214, MERGED)", "drawn dry layer 0.05 under +0.30: floor slab top +0.25 DRAWING-CONFIRMED", "FLOOR ONLY"),
]

# ---------------------------------------------------------------------------------------------- (b)-(d) held items
LIFT_TIE = dict(storey_m=4.50, threshold_m=4.30, strip_length_m=5.50)   # T-204: clear runs 1.20 + 0.70 + 1.80 + 1.80
LIFT_OPENINGS = ("L-GF-01", "L-1F-01", "L-2F-01")
Q55_FALLBACK = {"height_m": 2.20, "scope": "INTERNAL_DOOR"}    # OWNER_QUESTIONS_ANSWERED Q-55 (C + Urban fallback)
DOME_PIECES = [("1F-W11", 4.01), ("1F-W13", 2.98), ("1F-W13", 1.40), ("1F-W17", 0.44), ("1F-W18", 0.44),
               ("1F-W24", 1.02)]                                   # T-226 PIECE_RESOLUTION.csv (READY cc3a312e)

ANNEX_REASON = ("annex datum (Q-54 B) TESTED by T-227: the documents do NOT make +4.30 the structural slab (B-B draws "
                "+4.30 on top of a layer over the hatched roof; the sanitary set prints SLOPE 1 % on that roof; no "
                "sheet prints the annex roof slab top or its build-up). Missing: the annex roof structural slab top "
                "(or the roof build-up at the walls), designer item D-39. Floor slab top +0.25 is established (T-214), "
                "so each wall height = (+4.30 - b_roof) - 0.25 - member depth")
LIFT_REASON = ("lift tie beam (ST p.8 note 19) TESTED by T-227: required at GF (storey 4.50 > 4.30); its section is "
               "printed on no sheet (p.8 note only; p.14 lift detail and every plan / schedule searched, T-204 + this "
               "run) and the '3.00 m' is not tied to a datum (top, axis or soffit; above FFL or slab). Missing: tie-beam "
               "depth and its level datum (designer D-43); held strip 5.50 m of clear run x depth")
LIFT_OPEN_REASON = ("lift landing opening TESTED by T-227: width 1.00 drawn; head printed / drawn on no sheet (sections "
                    "A-A / B-B show no landing door; no elevation sees the shaft); the owner's 2.20 m door fallback "
                    "(Q-55) is scoped to internal doors and is not extended to a lift entrance (supplier / designer "
                    "item, like the pit depth on ST p.14)")
H01_REASON = ("GF-H01 TESTED by T-227: the plan's 0.40 band (both sides exterior, 1.40 m with a 0.80 column inside, "
              "0.60 m outside it) lies exactly under the 0.40-wide B20 band of the GF roof-slab plan; 0.40 is no block "
              "family; no sheet prints its material or construction; its base (court +0.15 or entrance landing +1.00) "
              "is not fixed: section A-A cuts 0.95 m west of the column looking west, away from it. Missing: what the "
              "band is (block, concrete, two skins) and its base level (designer)")
H02_REASON = ("GF-H02 TESTED by T-227 (from the T-143 hand census; no V2 run, so no plan geometry re-read this run): a "
              "0.20 x 0.90 outline on the furniture / stair layer at the external stair landing; no wall layer, no "
              "material, no height printed. Missing: what it is (stair cheek / planter) and its material (designer)")
DOME_REASON = ("piece under an open dome opening TESTED by T-227: the 1F roof-slab plan draws the dome opening (circles "
               "r 2.211 / 2.411, radial 'SEE DETAIL') over the piece; the ring B4 is on the circle edge only (Q-44 A), "
               "nothing is drawn over the chord inside it; section B-B draws the domes beyond the cut (the 1F roof "
               "band is continuous in that view) and no section cuts these partitions. Missing: what closes the top of "
               "a partition under the dome / skylight void (designer); never the storey height")

# ---------------------------------------------------------------------------------------------- r2: arched openings
# Checker 20:14 (T-227 REJECTED, narrow r2) and UP-OPEN-ARCH-001. Own re-measure this run on Drive 'Alsenan chalet
# project' / P7757_DXF_COMPRESSED.zip (P7757.dxf, sha ab54dd55), NW elevation frame, layer 1, the wall-opening chain
# (not the outer 0.10 surround-band chain, not the window frame on layer W): W16 jambs 2566 / 256A + 49 arch segments
# (crown pair 2785 / 2786); W15 jambs 2889 / 288A + 46 arch segments, the same outline translated 2.046 m. Both read:
# width 1.5523, springing 2.1609 above the +5.50 floor (jamb bottoms), crown 3.000 (+8.50, = printed '300'), arch
# segment by the drawn chain 1.0086 m2 (polygon of the chain, never its chord); band 0.10 outside ('+ 10', band chain
# 1.7523 wide to 3.101). Measured values only; no coordinate is kept in the repository.
ARCH_EVIDENCE = ("arched opening read on its opening line (UP-OPEN-ARCH-001; Checker 20:14 ruling, own re-measure r2): "
                 "P7757.dxf NW frame layer 1, W16 jambs 2566 / 256A + 49-segment arch chain (crown 2785 / 2786), W15 "
                 "jambs 2889 / 288A + 46-segment chain; 1.5523 x 2.1609 + arch 1.0086 = 4.363 m2 each; the 0.10 "
                 "surround band (crown 3.101) is a wall-face element, not the opening")
ARCHED = {oid: R.measured_arched_opening(1.5523, 2.1609, 3.000, 1.0086, band_m=0.10) for oid in ("W15", "W16")}
T175 = ROOT / "research/agents_t175/T175_OPENING_CONSEQUENCES.csv"


def merged_block_deductions():
    """The block deduction each opening carries in the merged T-175 ledger (what register v1 summed)."""
    out = {}
    for r in csv.DictReader(open(T175, encoding="utf-8")):
        if r["block_deduction_m2"]:
            out[r["opening"]] = float(r["block_deduction_m2"])
    return out


EVIDENCE_HEADS = ("heads: research/agents_t201/HEADS_T201.csv (T-201 MERGED 5dade783; Checker 07:00) and "
                  "research/agents_t207/CLOSURE_T207.csv (T-207 MERGED e081911c): drawn geometry on the DWF elevations / "
                  "sections and the current issue")


def f3(x):
    return "" if x is None else f"{x:.3f}"


def read_heads():
    heads = {}
    for r in csv.DictReader(open(HEADS, encoding="utf-8")):
        if r["STATUS"] in R.ESTABLISHED and r["AREA_M2"]:
            heads[r["ID"]] = {"width_m": float(r["WIDTH_M"]), "height_m": float(r["HEIGHT_M"]),
                              "area_m2": float(r["AREA_M2"]), "status": r["STATUS"], "src": "T-201"}
    for r in csv.DictReader(open(CLOSURE, encoding="utf-8")):
        if r["ID"] in ("W11", "W12") and r["AFTER_STATUS"] in R.ESTABLISHED:
            heads[r["ID"]] = {"width_m": 1.95, "height_m": 2.20, "area_m2": 4.290, "status": r["AFTER_STATUS"],
                              "src": "T-207"}
    # r2: an arched opening deducts its true outline, not the T-201 band-crown rectangle (4.805)
    for oid, a in ARCHED.items():
        if oid in heads:
            R.check_masonry_deduction(a["masonry_deduction_m2"], a)
            heads[oid] = {"width_m": None, "height_m": None, "area_m2": round(a["masonry_deduction_m2"], 3),
                          "status": a["status"], "src": "T-227 r2 (UP-OPEN-ARCH-001)",
                          "was_m2": heads[oid]["area_m2"]}
    return heads


def arch_correction(r):
    """Openings of the run whose merged block deduction (summed into register v1) read the band crown as a
    rectangular head: returns (corrected base deductions, list of (id, old, new))."""
    merged = merged_block_deductions()
    ded0 = float(r["deductions_m2"] or 0)
    fixes = []
    held = set(held_ids(r["held_openings"]))
    for oid in held_ids(r["openings_in_run"]):
        if oid in ARCHED and oid not in held and oid in merged:
            new = round(ARCHED[oid]["masonry_deduction_m2"], 3)
            try:
                R.check_masonry_deduction(merged[oid], ARCHED[oid])
            except ValueError:
                fixes.append((oid, merged[oid], new))
                ded0 += new - merged[oid]
    return round(ded0, 3), fixes


def held_ids(cell):
    return [x for x in cell.split(";") if x]


def build():
    rows = list(csv.DictReader(open(V1, encoding="utf-8")))
    cols = list(rows[0].keys())
    heads = read_heads()
    delta, notes = [], []
    for r in rows:
        new = dict(r)
        changes = []
        wid = r["wall_id"]
        reason_bits = []
        # (e) window heads now established in merged ledgers
        ho = held_ids(r["held_openings"])
        closed = [o for o in ho if o in heads]
        if closed:
            gross = float(r["gross_m2"]) if r["gross_m2"] else None
            ded0, fixes = arch_correction(r)
            res = R.apply_heads(gross, r["gross_class"], ded0, ho, heads)
            new["deductions_m2"] = f3(res["deductions_m2"])
            new["held_openings"] = ";".join(res["still_held"])
            fix_txt = "".join(f"; {o} {a:.3f} -> {b:.3f} arched outline (was the band-crown rectangle)"
                              for o, a, b in fixes)
            changes.append(f"deductions_m2 {r['deductions_m2']} -> {new['deductions_m2']} "
                           f"(+{res['added_m2']:.3f}: {', '.join(o + ' ' + format(heads[o]['area_m2'], '.3f') for o in closed)}"
                           f"{fix_txt})")
            changes.append(f"held_openings {r['held_openings']} -> {new['held_openings'] or '-'}")
            hi = None if gross is None else gross - res["deductions_m2"]
            only_openings = r["held_cause_class"] == "held opening" and "also]" not in r["unresolved_reason"]
            if res["net_m2"] is not None and only_openings and float(r["held_length_m"] or 0) == 0:
                t = float(r["t_m"])
                new["net_m2"] = f3(res["net_m2"])
                new["net_class"] = SS
                new["net_bounds_m2"] = ""
                new["net_m3"] = f3(res["net_m2"] * t)
                new["owner_status_class"] = SS
                new["held_cause_class"] = ""
                new["next_package"] = ""
                new["smallest_held_quantity"] = ""
                new["unresolved_reason"] = "pending the Checker's independent re-measure of length, height and deductions"
                new["calculation"] = r["calculation"].replace(
                    f"- deductions {r['deductions_m2']} m2 = net HELD m2",
                    f"- deductions {new['deductions_m2']} m2 = net {new['net_m2']} m2; m3 = net x {t:g} = {new['net_m3']}")
                for k in ("net_m2", "net_class", "net_m3", "owner_status_class"):
                    changes.append(f"{k} {r[k] or '-'} -> {new[k]}")
                changes.append(f"held_cause_class {r['held_cause_class']} -> -")
            else:
                lo = r["net_bounds_m2"].split(" .. ")[0] if r["net_bounds_m2"] else ""
                if hi is not None:
                    new["net_bounds_m2"] = (f"{lo} .. {hi:.3f}" if res["still_held"] and lo else f"{hi:.3f}")
                    if r["gross_class"] == "HELD":
                        new["net_bounds_m2"] = f"{hi:.3f} on the gross figure (not a quantity)"
                    changes.append(f"net_bounds_m2 {r['net_bounds_m2'] or '-'} -> {new['net_bounds_m2']}")
                new["calculation"] = r["calculation"].replace(f"- deductions {r['deductions_m2']} m2",
                                                              f"- deductions {new['deductions_m2']} m2")
                if res["still_held"]:
                    reason_bits.append(f"openings still HELD: {', '.join(res['still_held'])}")
                if r["gross_class"] == "HELD":
                    reason_bits.append("gross HELD (see cause)")
            new["evidence"] = r["evidence"] + "; " + EVIDENCE_HEADS
            if fixes or any(o in ARCHED for o in closed):
                new["evidence"] += "; " + ARCH_EVIDENCE
            new["source_ledgers"] = r["source_ledgers"] + " + T-201 + T-207 (via T-227)"
        # (a)-(d) tested holds: class unchanged, the missing item named
        cause = r["held_cause_class"]
        ur = r["unresolved_reason"]
        tested = None
        if cause == "annex datum (Q-54 B)" or "[annex datum (Q-54 B) also]" in ur:
            tested = ANNEX_REASON
        if cause.startswith("lift tie beam"):
            tested = LIFT_REASON
        if any(o in ho for o in LIFT_OPENINGS):
            tested = (tested + " | " if tested else "") + LIFT_OPEN_REASON
        if wid == "GF-H01":
            tested = H01_REASON
        if wid == "GF-H02":
            tested = H02_REASON
        if wid in {w for w, _ in DOME_PIECES}:
            tested = (tested + " | " if tested else "") + DOME_REASON + \
                f" (pieces {', '.join(f'{L:.2f}' for w, L in DOME_PIECES if w == wid)} m)"
        if wid == "GF-W10" and closed:
            new["unresolved_reason"] = (f"openings W05 / W06 / W07 established (T-201 heads, via T-227); with the T-226 "
                                        f"gross 50.845 m2 (READY cc3a312e, not merged) the net would be 50.845 - "
                                        f"{new['deductions_m2']} = {50.845 - float(new['deductions_m2']):.3f} m2: formed by "
                                        "T-228 only when both are merged | was: " + ur)
            changes.append("unresolved_reason: joint T-226 / T-227 closure stated")
        if tested and new["net_class"] != SS:
            new["unresolved_reason"] = tested + (f" [{'; '.join(reason_bits)}]" if reason_bits else "") + \
                " | was: " + ur
            new["next_package"] = "designer (T-228 ledger)"
            changes.append("unresolved_reason refined (T-227 evidence test; class unchanged)")
        if changes:
            delta.append({"change": "; ".join(changes), "package": PKG, **new})
            notes.append((r, new))
    return rows, cols, delta, notes, heads


def coverage(rows, delta):
    by = {r["wall_id"]: r for r in rows}
    after = dict(by)
    for d in delta:
        after[d["wall_id"]] = {k: v for k, v in d.items() if k not in ("change", "package")}
    out = defaultdict(lambda: [0.0, 0.0])
    for i, src in enumerate((by, after)):
        for r in src.values():
            if r["net_class"] == SS and r["net_m2"]:
                out[(r["floor"], r["t_m"], r["block_type"])][i] += float(r["net_m2"])
    return out


def csv_text(cols, rows):
    s = io.StringIO()
    w = csv.DictWriter(s, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return s.getvalue()


def outputs():
    rows, cols, delta, notes, heads = build()
    dcols = ["change", "package"] + cols
    files = {"register_delta.csv": csv_text(dcols, delta)}
    cov = coverage(rows, delta)
    ba = [{"floor": k[0], "t_m": k[1], "type": k[2], "net_source_supported_before_m2": f3(v[0]),
           "net_source_supported_after_m2": f3(v[1]), "delta_m2": f3(v[1] - v[0])} for k, v in sorted(cov.items())]
    tb, ta = sum(v[0] for v in cov.values()), sum(v[1] for v in cov.values())
    ba.append({"floor": "ALL", "t_m": "", "type": "", "net_source_supported_before_m2": f3(tb),
               "net_source_supported_after_m2": f3(ta), "delta_m2": f3(ta - tb)})
    files["BEFORE_AFTER.csv"] = csv_text(list(ba[0].keys()), ba)
    # annex test + sensitivity
    by = {r["wall_id"]: r for r in rows}
    annex = [r for r in rows if r["held_cause_class"] == "annex datum (Q-54 B)"
             or "[annex datum (Q-54 B) also]" in r["unresolved_reason"]]
    st = R.storey_structural_height(ANNEX_MARKS["floor"], ANNEX_MARKS["roof"])
    sens = R.held_sensitivity_m2_per_cm([float(r["length_m"]) - float(r["held_length_m"] or 0) for r in annex])
    at = [{"source": s, "what it shows": w, "verdict": v} for s, w, v in ANNEX_TEST]
    at.append({"source": "UP-MAS-DATUM-001 on the readings", "what it shows":
               f"floor: {st['floor']['rule']} {st['floor']['status']} slab top {st['floor']['slab_top_m']}; roof: "
               f"{st['roof']['rule']} {st['roof']['status']} ({st['roof']['reason']})", "verdict": st["status"]})
    files["ANNEX_DATUM_TEST.csv"] = csv_text(["source", "what it shows", "verdict"], at)
    held = []
    for r in annex:
        held.append({"item": "annex datum", "wall_id": r["wall_id"], "type": r["block_type"], "t_m": r["t_m"],
                     "length_m": r["length_m"], "gross_figure_m2 (not a quantity)": r["gross_m2"],
                     "smallest_held_quantity": "gross: length x (4.05 - b_roof - member depth); "
                     f"{float(r['length_m']) * 0.01:.4f} m2 per cm of b_roof",
                     "missing": "annex roof structural slab top / roof build-up (D-39)"})
    tie = R.tie_beam_strip(**LIFT_TIE)
    for w in ("GF-W08", "GF-W09", "GF-W13", "GF-W14"):
        r = by[w]
        held.append({"item": "lift tie beam", "wall_id": w, "type": r["block_type"], "t_m": r["t_m"],
                     "length_m": r["length_m"], "gross_figure_m2 (not a quantity)": r["gross_m2"],
                     "smallest_held_quantity": "strip (its share of 5.50 m clear run) x tie-beam depth",
                     "missing": "tie-beam section and the datum of '3.00 m' (D-43)"})
    for o, w in (("L-GF-01", "GF-W08"), ("L-1F-01", "1F-W07"), ("L-2F-01", "2F-W00")):
        h = R.opening_height("LIFT_LANDING", owner_fallback=Q55_FALLBACK)
        held.append({"item": "lift opening", "wall_id": w, "type": by[w]["block_type"], "t_m": by[w]["t_m"],
                     "length_m": "1.00 (opening width)", "gross_figure_m2 (not a quantity)": by[w]["gross_m2"],
                     "smallest_held_quantity": f"{o}: 1.00 m x head (net bounds {by[w]['net_bounds_m2']})",
                     "missing": f"{o} head / structural opening height ({h['status']}: {h['basis']})"})
    for w, t, why in (("GF-H01", 0.40, "material / construction and base level"),
                      ("GF-H02", 0.20, "what it is and its material")):
        held.append({"item": "strip", "wall_id": w, "type": "-", "t_m": f"{t}", "length_m": by[w]["held_length_m"],
                     "gross_figure_m2 (not a quantity)": "-",
                     "smallest_held_quantity": f"{by[w]['held_length_m']} m x height",
                     "missing": f"{why} ({R.band_material(t)['status']})"})
    for w, L in DOME_PIECES:
        held.append({"item": "under dome opening", "wall_id": w, "type": by[w]["block_type"], "t_m": by[w]["t_m"],
                     "length_m": f"{L:.2f}", "gross_figure_m2 (not a quantity)": "-",
                     "smallest_held_quantity": f"{L:.2f} m x height ({R.piece_top()['status']})",
                     "missing": "what closes the partition top under the dome / skylight void"})
    files["HELD_ITEMS_T227.csv"] = csv_text(list(held[0].keys()), held)
    closed_nets = [d for d in delta if d["net_class"] == SS]
    summ = {
        "package": PKG, "inputs": {"register_v1": "research/agents_t225/BLOCKWORK_WALL_REGISTER_V1.csv",
                                   "heads": ["research/agents_t201/HEADS_T201.csv", "research/agents_t207/CLOSURE_T207.csv"]},
        "delta_rows": len(delta),
        "nets_newly_source_supported": {d["wall_id"]: float(d["net_m2"]) for d in closed_nets},
        "nets_newly_source_supported_total_m2": round(sum(float(d["net_m2"]) for d in closed_nets), 3),
        "deductions_added_m2": {d["wall_id"]: d["deductions_m2"] for d in delta if "deductions_m2" in d["change"]},
        "net_source_supported_total_before_after_m2": [round(tb, 3), round(ta, 3)],
        "annex": {"walls": [r["wall_id"] for r in annex], "storey_test": st["status"],
                  "roof_rule": st["roof"]["reason"], "floor_slab_top_m": st["floor"]["slab_top_m"],
                  "gross_figure_m2_not_a_quantity": round(sum(float(r["gross_m2"] or 0) for r in annex), 3),
                  "sensitivity_m2_per_cm_b_roof": sens},
        "lift_tie_beam": tie, "lift_openings": R.opening_height("LIFT_LANDING", owner_fallback=Q55_FALLBACK),
        "dome_pieces_m": round(sum(L for _, L in DOME_PIECES), 2),
        "arched_openings_r2": {oid: {k: a[k] for k in ("width_m", "spring_m", "crown_m", "jamb_rectangle_m2",
                                                       "arch_segment_m2", "masonry_deduction_m2", "window_area_q32a_m2",
                                                       "band_crown_m", "status")}
                               for oid, a in ARCHED.items()},
        "arched_was_m2": {"W15": merged_block_deductions().get("W15"), "W16": heads["W16"].get("was_m2")},
        "verified_by_checker_m2": 0.0,
    }
    files["summary.json"] = json.dumps(summ, indent=1, ensure_ascii=False) + "\n"
    return files


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    files = outputs()
    if a.check:
        bad = [n for n, t in files.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("CHECK", "PASS" if not bad else f"FAIL {bad}")
        return 0 if not bad else 1
    for n, t in files.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print(files["summary.json"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
