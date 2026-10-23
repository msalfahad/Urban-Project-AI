"""T-234 Alsenan check: CONC.SLAB as a whole reference line, every slab panel once, from committed inputs only.

    python3 -I research/agents_t234/t234_alsenan_check.py          # writes LEDGER_T234.csv + summary.json here

Inputs: research/agents_t139/PANELS.csv (T-139 MERGED: every face of the three slab sheets of Drive "Alsenan chalet
project" / "ST7757 dxf.dxf" sha 9f9d1179, reproduced byte for byte by this task's own run of T-139 slab_faces.py +
slab_ledger.py); the sunken panels of T-213 (MERGED 0ec8c496); the freelancer's own cells from
tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (RC workbook, sheet 'بلاطات ' rows 11 / 16 / 23 / 24 / 27); engine
figures from the runs named in ENGINE (own runs this task, outside the repository; engine face ids only). Nothing here is
released; integration is a lane I package after the Checker's verdict.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import slab_line as SL  # noqa: E402

NOTE_T = 0.16   # ST7757.pdf p.8 general note 18 (read by eye, T-139 / T-213): roof slabs 16 cm unless otherwise stated
SUNKEN = {"GF-015", "GF-016", "GF-081", "GF-128", "GF-141", "1F-018"}   # T-213 hatches 276 / 275 / 298 / 287 / 280 / 5BF
# Every 'X' / radial opening mark on layer S-OPENING of the three slab sheets (own DXF read, this task) and the face it
# lies in; each is a void face of its own in the partition (never inside a slab panel), so no panel deducts it.
OPENINGS = {
    "GF lift shaft X 54F/550 (1.80 x 1.80)": ("GF-048", "OUTSIDE_PANELS"),
    "GF pool-court void X 42E/42F": ("GF-040", "OUTSIDE_PANELS"),
    "GF light well X 2CF..2D2 + 54B/54C (round stair inside)": ("GF-130", "OUTSIDE_PANELS"),
    "1F lift shaft X 73F/740 (1.80 x 1.80)": ("1F-036", "OUTSIDE_PANELS"),
    "1F west dome radial 604..617 (r 2.2111)": ("1F-073", "OUTSIDE_PANELS"),
    "1F east dome radial 64E..661 (r 2.2111)": ("1F-076/1F-077", "OUTSIDE_PANELS"),
}
# 2F sheet: no S-OPENING mark; the lift box 2F-025 is closed (bars 5d10/m both ways; T-204: the +13.90 slab closes the
# shaft): a slab panel.

# ---- released ARCH_TAKEOFF_V2.9 + route G (tools/release_baseline.py V29_ROUTEG_NO_PROFILE, own run on working head
# 63f4d90e: REPRODUCED, 1,455 lines, BOQ_LINES.csv b96185d4). STR.CONC.SLAB m3 per floor; every released face matched
# to the T-139 face it lies in (engine overlay polygons fitted to the drawing faces: 72 of 75 faces placed, the three
# unplaced are T-139's own named faces d54a5a / cf20e8 / 4c7ca8).
RELEASED = {
    "per_floor": {"GF": 33.489804, "1F": 19.917771, "2F": 8.143810},
    "bounded": [("1F", "b845e1e78b1f74a8", 2.740348, "SLAB_STAIR_ZONE: the west dome square (T-139 s.4: NOT slab)")],
    # (floor, engine face, m2, t released, m3 released, T-139 class of the face it lies in)
    "not_slab_faces": [
        ("GF", "f9b0c2", 0.857337, 0.16, 0.137174, "EDGE_HELD"),       # generic-route line L-0871738f, BM-GF-058 D-05
        ("GF", "b355ef", 0.123648, 0.16, 0.019784, "BEAM_OR_COLUMN"),  # GF-106 junction piece 0.200 wide
        ("GF", "8805bf", 0.127841, 0.16, 0.020455, "BEAM_OR_COLUMN"),  # GF-062 junction piece 0.200 wide
        ("GF", "5708ae", 0.489955, 0.16, 0.078393, "EDGE_HELD"),       # GF-096 outer west strip, BM-GF-061 D-26
        ("GF", "8754c1", 0.086630, 0.16, 0.013861, "NOT_SLAB"),        # GF-014 drafting break mark
        ("GF", "57ec39", 0.201339, 0.16, 0.032214, "OPENING+RING"),    # GF-040 B7 ring piece BM-GF-060 (Q-61 C)
        ("GF", "4868d6", 0.740000, 0.16, 0.118400, "BEAM"),            # GF-097 CB5 span 2 (T-145)
        ("1F", "d54a5a", 0.099261, 0.16, 0.015882, "BEAM_OR_COLUMN"),  # unlabelled span past a column, BM-1F-032 D-04
        ("1F", "cf20e8", 0.086630, 0.16, 0.013861, "NOT_SLAB"),        # drafting break mark
        ("1F", "4c7ca8", 0.620124, 0.16, 0.099220, "EDGE_HELD"),       # SE box outside CB12, BM-1F-035 / -038
        ("1F", "cfe47b", 0.202971, 0.16, 0.032475, "EDGE_HELD"),       # 1F-028 strip outside CB12, BM-1F-036
        ("2F", "ae2689", 0.086630, 0.18, 0.015593, "NOT_SLAB"),        # 2F-008 drafting break mark
        ("2F", "5a1792", 0.271761, 0.18, 0.048917, "EDGE_HELD"),       # 2F-031 0.10 strip west of B15
    ],
    # 2F: the two 'T 18' tags (tank panels 2F-011 / 2F-013) spread to the five untagged panels as SHEET_UNIFORM 0.18
    # (engine/source/slab_engine.py 'uniform' rule) although general note 18 gives them 0.16
    "thickness_spread": [("2F", 31.25, 0.18, NOTE_T)],
}
CANDIDATE = None   # filled from the V3.0.8 run (see summary 'candidate'); None = not reproduced in this run


def load_panels():
    rows = list(csv.DictReader(open(ROOT / "research/agents_t139/PANELS.csv", encoding="utf-8")))
    return rows


def ledger(rows):
    panels = []
    for p in rows:
        if p["cls"] != "SLAB":
            continue
        basis = "GENERAL_NOTE" if "note 18" in p["basis"] else "TAG"
        panels.append(dict(id=p["id"], storey=p["floor"], area_m2=float(p["area"]), t_m=float(p["t"]),
                           t_basis=basis, sunken=p["id"] in SUNKEN, depth_basis="FULL", top_datum="STRUCTURAL",
                           evidence=p["evidence"]))
    census = {k: v[1] for k, v in OPENINGS.items()}
    line = SL.slab_line(panels, general_note_t_m=NOTE_T, openings_census=census)
    return panels, line


def partition(rows):
    """Plan partition of each sheet: every face billed by the one line its class gives it (hand ledger, C1)."""
    out = {}
    for fl in ("GF", "1F", "2F"):
        faces = []
        for p in rows:
            if p["floor"] != fl or "/" in p["id"]:
                continue
            owner = SL.FACE_OWNER[p["cls"]]
            faces.append(dict(id=p["id"], cls=p["cls"], area_m2=float(p["area"]),
                              billed_by=[] if owner is None else [owner.split("|")[0]]))
        out[fl] = SL.face_partition_check(faces)
    return out


def freelancer():
    raw = json.load(open(ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json", encoding="utf-8"))
    cell = {}
    for r in raw["rows"]:
        if r["file"] == "RC" and r["sheet"] == "بلاطات ":
            for k, v in r["cells"].items():
                cell[k] = v["v"]
    fr = {"GF": dict(m2_016=cell["B11"], m3=cell["I11"]),
          "1F": dict(m2_016=cell["B16"], m3=cell["I16"]),
          "2F": dict(m2_016=cell["B23"], m2_018=cell["B24"], m3=cell["I25"]),
          "total": cell["I27"]}
    return fr


def main(write=True):
    rows = load_panels()
    panels, line = ledger(rows)
    part = partition(rows)
    fr = freelancer()
    hand = {k: v["m3"] for k, v in line["by_storey"].items()}
    total = line["measured_m3"]
    # released vs drawing, per floor
    rel = {}
    for fl in ("GF", "1F", "2F"):
        comps = [("%s %s (%s)" % (f[1], f[5], "not slab"), f[4]) for f in RELEASED["not_slab_faces"] if f[0] == fl]
        comps += [("2F untagged panels at the spread tag", a * (t_e - t_h)) for f2, a, t_e, t_h in
                  RELEASED["thickness_spread"] if f2 == fl]
        rel[fl] = dict(released=RELEASED["per_floor"][fl], drawing=hand[fl], components=comps,
                       **SL.reconcile(RELEASED["per_floor"][fl], hand[fl], comps))
    rel_total = sum(RELEASED["per_floor"].values())
    # freelancer vs drawing, per floor (his lump areas)
    t16 = {fl: sum(p["area_m2"] for p in panels if p["storey"] == fl and p["t_m"] == 0.16) for fl in hand}
    t18 = {fl: sum(p["area_m2"] for p in panels if p["storey"] == fl and p["t_m"] == 0.18) for fl in hand}
    corners = sum(p["area_m2"] for p in panels if "dome square corner" in p["evidence"] or "/c" in p["id"])
    frl = {
        "GF": [("lump area 207.00 vs 33 panels %.4f m2 at 0.16" % t16["GF"], (t16["GF"] - fr["GF"]["m2_016"]) * 0.16)],
        "1F": [("eight dome-square corners %.4f m2 drawn as slab outside the ring (T-139)" % corners, corners * 0.16),
               ("lump-area residual (not traceable: one area, no breakdown)",
                (t16["1F"] - fr["1F"]["m2_016"] - corners) * 0.16)],
        "2F": [("panels at 0.16: %.4f vs his %.2f m2" % (t16["2F"], fr["2F"]["m2_016"]),
                (t16["2F"] - fr["2F"]["m2_016"]) * 0.16),
               ("tank panels at 0.18: %.4f vs his %.2f m2" % (t18["2F"], fr["2F"]["m2_018"]),
                (t18["2F"] - fr["2F"]["m2_018"]) * 0.18)],
    }
    fre = {fl: dict(freelancer=fr[fl]["m3"], drawing=hand[fl], components=frl[fl],
                    **SL.reconcile(hand[fl], fr[fl]["m3"], frl[fl])) for fl in ("GF", "1F", "2F")}
    rows_out = []
    rows_out.append(["panel", "storey", "net_m2", "t_m", "t_basis", "sunken", "m3", "status", "edge_owner", "evidence"])
    for p, r in zip(panels, line["panels"]):
        rows_out.append([r["id"], r["storey"], "%.4f" % r["net_m2"], "%.2f" % r["t_m"], r["t_basis"],
                         "yes" if r["sunken"] else "", "%.6f" % r["m3"], "DRAWING-CONFIRMED",
                         "beam / column faces (BEAM > SLAB, C1)", p["evidence"]])
    summary = dict(
        schema=SL.SCHEMA, convention=SL.CONVENTIONS[0], general_note_t_m=NOTE_T,
        panels=len(panels), by_storey={k: dict(n=v["n"], net_m2=round(v["net_m2"], 4), m3=round(v["m3"], 6))
                                       for k, v in line["by_storey"].items()},
        measured_m3=round(total, 6), held=line["held"], status=line["status"],
        openings=OPENINGS, openings_not_deducted=line["openings_not_deducted"],
        sunken_m2=round(sum(p["area_m2"] for p in panels if p["sunken"]), 4),
        partition={k: v["status"] for k, v in part.items()},
        released=dict(total=round(rel_total, 6), bounded=RELEASED["bounded"],
                      per_floor={k: dict(released=v["released"], drawing=round(v["drawing"], 6),
                                         diff=round(v["diff_m3"], 6), explained=round(v["explained_m3"], 6),
                                         residual=round(v["residual_m3"], 6)) for k, v in rel.items()}),
        freelancer=dict(total=fr["total"], per_floor={k: dict(freelancer=v["freelancer"], drawing=round(v["drawing"], 6),
                                                              diff=round(v["diff_m3"], 6),
                                                              components=[(c, round(m, 6)) for c, m in v["components"]],
                                                              residual=round(v["residual_m3"], 6))
                                                      for k, v in fre.items()}),
        candidate=CANDIDATE,
    )
    if not write:
        return summary, rows_out, line, part
    with open(HERE / "LEDGER_T234.csv", "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows_out)
    (HERE / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(measured_m3=summary["measured_m3"], status=summary["status"],
                          released=summary["released"]["total"], freelancer=fr["total"]), indent=1))
    return summary, rows_out, line, part


if __name__ == "__main__":
    main()
