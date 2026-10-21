"""S8.3A - independent dome-shell reinforcement distribution audit (dated correction layer over the frozen S8.3).

    python3 -I research/alsenan_dome_mesh_s8_3a/build_s8_3a.py

Question: does the frozen shell mesh quantity (Ø12 at 150 mm, meridional and hoop, measured as surface area / spacing)
represent the physically intended bar layout? Reads only the registered structural DXF (ST7757 p.7 DETAIL OF DOME and
the p.5 plan) and the frozen S8.3 outputs. No earlier Urban, contractor or third-party figure is read, and no scenario
is chosen to resemble one. S8.3 and its errata are never written.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "research" / "external_engine_lab"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import curved_member_geometry as G  # noqa: E402
from engine.source import delta_release as DR  # noqa: E402
from engine.source import rebar_unit_mass as UM  # noqa: E402
from engine.source import shell_line_distribution as D  # noqa: E402

ROUND = "S8_3A"
DATE = "2026-10-09"
BASELINE_HEAD = "6ddd988"
R = ROOT / "research"
S83 = R / "alsenan_dome_ring_s8_3"
S83_MANIFEST = S83 / "16_S8_3_FREEZE_MANIFEST.json"
S83_ERRATA = S83 / "errata"
STRUCT_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
EARLIER = json.loads((S83 / "15_S8_3_SUMMARY.json").read_text(encoding="utf-8"))["frozen_baselines"]
CODE = ["engine/source/shell_line_distribution.py", "engine/source/curved_member_geometry.py",
        "engine/source/delta_release.py", "engine/source/rebar_unit_mass.py",
        "research/alsenan_dome_mesh_s8_3a/build_s8_3a.py", "research/external_engine_lab/alsenan_structural_s1.py"]
OUTPUTS = ["00_README.md", "01_SOURCE_EVIDENCE.csv", "02_SCENARIOS.csv", "03_PHYSICAL_LAYOUT_FEASIBILITY.csv",
           "04_STATUS_CHANGES.csv", "05_BAR_OBJECT_RECONCILIATION.csv", "06_MISSING_EVIDENCE.csv",
           "07_FROZEN_VERIFICATION.json", "08_S8_3A_SUMMARY.json"]
MANIFEST_NAME = "09_S8_3A_FREEZE_MANIFEST.json"
UNIT_MASS = {"method": UM.D2_OVER_162, "authority": "the project-wide method S8.3 used", "selected_by": "Urban"}
SPACING = 0.150
TEST_MIN_SPACING = 0.075          # scenario C test rule only: alternate meridians stop where the spacing halves
CLEAR_TOUCH = 0.012               # centre-to-centre spacing at which two Ø12 bars touch
DOMES = ("DOME-A", "DOME-B")
# p.7 objects (handles from the frozen S8.3 notation register and errata)
SHELL_ARCS = ("182B", "182E")
SHELL_LABELS = {"1A0E": "1A0C", "1A15": "1A13"}
SHELL_BAR, HOOP_BLOCK = "1A09", "*U295"
RING_CUTS = ("1A0A", "1A07")
KNOWN = {"1A09": "S8.3 N-1A09 SHELL_ANCHORAGE / SHELL_MERIDIONAL (drawn bar)", "1A0B": "S8.3 N-1A0B RING_LINKS",
         "1A4D": "S8.3-E02 UNLABELLED_JUNCTION_BAR", "1A4F": "S8.3-E02 UNLABELLED_JUNCTION_BAR"}


class Stop(Exception):
    pass


def check(c, m):
    if not c:
        raise Stop(m)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _r(v, nd=9):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        s = f"{v:.9f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    if isinstance(v, (list, tuple, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(name, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in rows[0]})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def _json(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode())
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()[:16]


# ------------------------------------------------------------------ frozen state
def frozen_state():
    man = dict(json.loads(S83_MANIFEST.read_text(encoding="utf-8"))["frozen_baselines"])
    s83 = DR.verify_frozen(S83_MANIFEST, ROOT)
    errata = {p.name: _sha(p) for p in sorted(S83_ERRATA.glob("0*"))}
    return {"s8_3": s83, "s8_3_errata": errata, "earlier_from_s8_3": man}


# ------------------------------------------------------------------ the drawing
def drawing_evidence(src):
    f = src.sheets["DET"]["frame"]
    E = {e["handle"]: e for e in src.entities()["DET"]}
    ext, intr = (src.doc.entitydb[h] for h in SHELL_ARCS)
    c = (ext.dxf.center.x - f[0], ext.dxf.center.y - f[1])
    r_ext, r_int = ext.dxf.radius, intr.dxf.radius
    bar = E[SHELL_BAR]
    arc = [s for s in bar["segs"] if s[0] == "ARC"]
    check(len(arc) == 1, "one arc in the drawn shell bar")
    a0, a1 = math.degrees(arc[0][3]), math.degrees(arc[0][4])
    sweep = G.sweep_deg(a0, a1)
    crosses_crown = G.norm_deg(90.0 - a0) < sweep
    legs = [s for s in bar["segs"] if s[0] != "ARC"]
    dots = []
    for e in src.entities()["DET"]:                        # a list: the exploded dots share handles
        if e["type"] == "INSERT" and e.get("name") == HOOP_BLOCK:
            b = e["bbox"]
            p = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
            dots.append((math.degrees(math.atan2(p[1] - c[1], p[0] - c[0])), math.dist(p, c)))
    dots.sort()
    steps = [b[0] - a[0] for a, b in zip(dots, dots[1:])]
    units_per_mm = (r_ext - r_int) / 100.0                 # the printed '10' cm thickness against the drawn one
    dot_spacing_mm = statistics_mean(steps) * math.pi / 180 * statistics_mean([r for _, r in dots]) / units_per_mm
    labels = []
    for h, lead in SHELL_LABELS.items():
        ln = E[lead]
        tip = min((ln["a"], ln["b"]), key=lambda p: abs(math.dist(p, c) - (r_ext + r_int) / 2))
        labels.append({"handle": h, "text": E[h]["text"], "tip_r": math.dist(tip, c)})
    bar_r = arc[0][2]
    for x in labels:
        x["points_at"] = "MERIDIONAL_BAR_LINE" if abs(x["tip_r"] - bar_r) < abs(x["tip_r"] - (dots[0][1] + 30)) \
            else "HOOP_BAR_DOTS"
    # the p.5 plan: the radial lines inside each dome circle
    plan = src.entities()["FFRS"]
    radial = [e for e in plan if e["type"] == "LINE" and e["layer"] == "S-OPENING"]
    by_centre = Counter((round(e["a"][0]), round(e["a"][1])) for e in radial)
    radial_counts = sorted(n for n in by_centre.values() if n >= 10)     # a fan of lines from one centre
    return {"centre": c, "r_ext": r_ext, "r_int": r_int, "bar_r": bar_r, "bar_arc_deg": [a0, a1], "bar_sweep": sweep,
            "bar_crosses_crown": crosses_crown, "bar_legs": len(legs), "dots": len(dots),
            "dot_angles": [dots[0][0], dots[-1][0]], "dot_step_spread": max(steps) - min(steps),
            "dot_step_deg": statistics_mean(steps), "dot_spacing_mm_at_detail_proportion": dot_spacing_mm,
            "labels": labels, "plan_radial_lines_per_dome": radial_counts, "units_per_mm": units_per_mm}


def statistics_mean(v):
    return sum(v) / len(v)


def bar_objects(src):
    """every reinforcement object drawn in the DETAIL OF DOME (shell and the two ring cuts)"""
    E = src.entities()["DET"]
    by = {e["handle"]: e for e in E}
    boxes = []
    for h in RING_CUTS:
        pts = by[h]["pts"]
        boxes.append((min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)))
    ext = src.doc.entitydb[SHELL_ARCS[0]]
    f = src.sheets["DET"]["frame"]
    c = (ext.dxf.center.x - f[0], ext.dxf.center.y - f[1])
    r_out = ext.dxf.radius

    def where(p):
        if any(b[0] - 1 <= p[0] <= b[2] + 1 and b[1] - 1 <= p[1] <= b[3] + 1 for b in boxes):
            return "RING_CUT"
        if math.dist(p, c) <= r_out + 1 and p[1] >= boxes[0][3] - 1:
            return "SHELL"
        return None
    rows = []
    for e in E:
        if e["layer"] in ("REIN", "S-REIN.D") and e["type"] in ("LWPOLYLINE", "LINE"):
            pts = e.get("pts") or [e["a"], e["b"]]
            zone = "SHELL+RING_CUT" if e["handle"] == SHELL_BAR else (where(pts[0]) or where(pts[-1]))
        elif e["type"] == "CIRCLE" and e["layer"] == "S-HAT.BAT":
            zone = where(e["c"])
        elif e["type"] == "INSERT" and e.get("name") == HOOP_BLOCK:
            b = e["bbox"]
            zone = where(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))
        else:
            continue
        if zone is None:
            continue
        rows.append({"handle": e["handle"], "type": e["type"], "layer": e["layer"], "zone": zone,
                     "r": e.get("r"), "block": e.get("name")})
    return rows


def build():
    import alsenan_structural_s1 as S1
    frozen = frozen_state()
    s83_sum = json.loads((S83 / "15_S8_3_SUMMARY.json").read_text(encoding="utf-8"))
    s83_bars = {r["ITEM_ID"]: r for r in _rows(S83 / "08_REBAR_QTO_REGISTER.csv")}
    src = S1.Source()
    check(src.sha256 == STRUCT_SHA, "the registered structural DXF")
    ev = drawing_evidence(src)
    objs = bar_objects(src)
    sh = s83_sum["shell"]                                   # printed 4.42 / 1.90 / 0.10, exactly as S8.3 used them
    shell = G.shell_between_caps(G.cap_radius(sh["chord_m"], sh["rise_m"]), sh["rise_m"], sh["t_m"])
    Rm, d = shell["r_mid"], shell["centre_below_springing"]
    frame = D.cap_frame(Rm, d)
    check(abs(frame["area"] - sh["area_mid"]) < 1e-8, "the frozen mid-surface is reproduced")
    kgm = UM.kg_per_m(12, UNIT_MASS)
    n_dome = len(DOMES)

    # ------------------------------------------------------------ scenarios
    A = D.uniform_density(frame, SPACING)["total"]
    Bm = D.fixed_meridians(frame, SPACING)
    H = D.hoops_continuous(frame, SPACING)
    Hd = D.hoops_discrete(frame, SPACING, "RIM")
    Hm = D.hoops_discrete(frame, SPACING, "MID")
    C = D.halving_curtailment(frame, SPACING, TEST_MIN_SPACING)
    fab = D.fabrication_counts(Bm["count"], H["count"])
    frozen_kg = s83_sum["released"]["reinforcement_kg"]
    frozen_each = [float(s83_bars[f"RQ-{t}-SHELL_{fam}"]["EQUIVALENT_LENGTH_M"]) for t in DOMES
                   for fam in ("MERIDIONAL", "HOOP")]
    sc = []

    def S(i, name, mer, hoop, lane, authority, formula, note):
        kg = n_dome * (mer + hoop) * kgm
        sc.append({"SCENARIO": i, "NAME": name, "MERIDIONAL_M_PER_DOME": mer, "HOOP_M_PER_DOME": hoop,
                   "TOTAL_M_TWO_DOMES": n_dome * (mer + hoop), "KG_TWO_DOMES": kg, "RATIO_TO_FROZEN": kg / frozen_kg,
                   "LANE": lane, "AUTHORITY": authority, "FORMULA": formula, "NOTE": note})
    S("A", "existing uniform surface density (frozen S8.3)", A, A, "PROJECT_BASIS_QTO (frozen, unchanged)",
      "IDEALIZED_SURFACE_DENSITY_QTO", "each family: A_mid / s; A_mid = 2 pi R_m h_m",
      "spacing 150 mm everywhere on the surface: meridians would have to stop continuously towards the crown")
    S("B", "meridians fixed at 150 mm on the springing circle, springing to crown", Bm["total"], H["total"],
      "SENSITIVITY_ONLY", "INTERPRETATION (spacing read at the springing; no curtailment)",
      "N = 2 pi a / s (unrounded); meridional = N x R_m psi0; hoops = A_mid / s at 150 mm along the meridian",
      "matches the drawn continuous bar; physically the meridians crowd and cross at the crown (03)")
    S("B-FAB", "scenario B with whole bars and whole circles", fab["meridians_whole"] * frame["meridian"],
      Hd["total"], "SENSITIVITY_ONLY", "FABRICATION_ROUNDING_TEST",
      "ceil(N) meridians x R_m psi0; floor(meridian / s) + 1 circles from the springing",
      "rounding only: still no laps, anchorage or crown detail; not a BBS")
    S("C", "test rule: alternate meridians stop where the spacing halves (75 mm)", C["total"], H["total"],
      "SENSITIVITY_ONLY", "TEST_ASSUMPTION (no source)",
      "levels: n meridians from psi_k down to sin(psi_k+1) = s_min n / (2 pi R_m); then n s_min / s continue",
      "an illustrative curtailment rule, stated for testing; the source shows no curtailment")
    check(abs(sc[0]["KG_TWO_DOMES"] - frozen_kg) < 1e-6, "scenario A reproduces the frozen kg")
    check(all(abs(x - A) < 1e-6 for x in frozen_each), "scenario A reproduces the frozen length per direction")

    # ------------------------------------------------------------ 01 source evidence
    lab = {x["points_at"]: x for x in ev["labels"]}
    evd = [
        ("SE-01", "meridional bars", "label 1A0E 'Ø12MM/15cm' points at the drawn bar line (r "
         f"{lab['MERIDIONAL_BAR_LINE']['tip_r']:.1f} vs bar r {ev['bar_r']:.1f})", "bars in the vertical planes "
         "through the dome axis (radial in plan, curved in section)"),
        ("SE-02", "circumferential bars", f"label 1A15 'Ø12MM/15cm' points at the hoop dots; {ev['dots']} dots",
         "horizontal circles at successive heights, cut in the section"),
        ("SE-03", "where the 150 mm spacing is stated", "only in the two label texts; no dimension, no reference "
         "circle, no 'max' or 'at springing'", "the reference location of the meridional spacing is NOT stated"),
        ("SE-04", "hoop spacing along the meridian", f"the dots sit at a constant angular step "
         f"({ev['dot_step_deg']:.4f} deg, spread {ev['dot_step_spread']:.6f}) from {ev['dot_angles'][0]:.2f} to "
         f"{ev['dot_angles'][1]:.2f} deg", "uniform along the arc, i.e. measured along the shell (a vertical spacing "
         "would not be uniform in angle); drawn about every "
         f"{ev['dot_spacing_mm_at_detail_proportion']:.0f} mm, not 150: the drawn pitch is graphic"),
        ("SE-05", "meridian continuity", f"one bar drawn from ring to ring over the crown (arc {ev['bar_arc_deg'][0]:.2f} "
         f"to {ev['bar_arc_deg'][1]:.2f} deg, crosses the crown: {ev['bar_crosses_crown']}), with {ev['bar_legs']} "
         "straight legs and hooks into both ring cuts", "continuous springing to springing as drawn"),
        ("SE-06", "stops, staggers, splices, density changes", "none drawn: no curtailment mark, no lap, no second "
         "spacing, no crown ring, cap mesh or trimming bar", "the section shows one typical bar of each family"),
        ("SE-07", "the plan's radial lines", f"{ev['plan_radial_lines_per_dome']} radial lines per dome on layer "
         "S-OPENING, 18 deg apart", "a dome / opening symbol, not bars: 20 lines on a 13.6 m circle would be 0.68 m "
         "apart, against the 150 mm label"),
        ("SE-08", "status of the drawing", "DETAIL OF DOME (N.I.S): one typical section, cut through the axis",
         "a generic reinforcement specification (size, spacing, directions, anchorage into the ring), not a buildable "
         "radial-bar layout")]
    evidence = [{"ID": i, "QUESTION": q, "OBSERVED": o, "CONCLUSION": c} for i, q, o, c in evd]

    # ------------------------------------------------------------ 03 physical layout feasibility
    feas = []
    rho_75 = D.crowding_radius(Bm["count"], TEST_MIN_SPACING)
    rho_touch = D.crowding_radius(Bm["count"], CLEAR_TOUCH)
    for frac in (1.0, 0.75, 0.5, 0.25, 0.1, 0.05):
        psi = frame["psi0"] * frac
        feas.append({"ITEM": f"fixed meridians: spacing at polar angle {frac:.2f} x psi0 (1 = springing, 0 = crown)",
                     "VALUE": D.spacing_at(frame, Bm["count"], psi), "UNIT": "m",
                     "NOTE": f"plan radius {frame['R'] * math.sin(psi):.3f} m"})
    feas += [
        {"ITEM": "fixed meridians closer than 75 mm inside plan radius", "VALUE": rho_75, "UNIT": "m",
         "NOTE": f"of a {frame['rim_radius']:.3f} m rim: {(rho_75 / frame['rim_radius']) ** 2 * 100:.1f} % of the plan "
                 "area"},
        {"ITEM": "fixed Ø12 meridians touch (12 mm centre to centre) inside plan radius", "VALUE": rho_touch, "UNIT": "m",
         "NOTE": "inside it the bars cannot all pass"},
        {"ITEM": "full arches crossing at the crown (as drawn, ring to ring)", "VALUE": Bm["count"] / 2, "UNIT": "arches",
         "NOTE": "every drawn meridian passes through the apex: not buildable without a crown detail"},
        {"ITEM": "scenario A: meridional length per dome needs continuous curtailment", "VALUE": A, "UNIT": "m",
         "NOTE": "no drawing shows where meridians stop"},
        {"ITEM": "scenario C levels (test rule)", "VALUE": float(len(C["levels"])), "UNIT": "levels",
         "NOTE": f"first stop at plan radius {D.crowding_radius(Bm['count'], TEST_MIN_SPACING):.3f} m; a geometric "
                 f"series to the crown in unrounded counts ({sum(1 for x in C['levels'] if x['count'] >= 1)} levels "
                 "carry at least one bar)"},
        {"ITEM": "whole meridians (fabrication)", "VALUE": float(fab["meridians_whole"]), "UNIT": "bars",
         "NOTE": f"continuous {Bm['count']:.6f}"},
        {"ITEM": "whole hoops from the springing at 150 mm (fabrication)", "VALUE": float(Hd["count"]), "UNIT": "circles",
         "NOTE": f"continuous {H['count']:.6f}; total {Hd['total']:.6f} m vs continuous {H['total']:.6f} m; "
                 f"mid-start {Hm['count']} circles {Hm['total']:.6f} m"},
        {"ITEM": "longest hoop (springing circle of the mid-surface)", "VALUE": frame["rim_circumference"], "UNIT": "m",
         "NOTE": "a lap position and length are not detailed for any hoop"},
        {"ITEM": "one drawn meridian arch, springing to springing, on the mid-surface", "VALUE": 2 * frame["meridian"],
         "UNIT": "m", "NOTE": "plus the legs into both rings (length follows the ring depth, not stated)"}]

    # ------------------------------------------------------------ 04 status changes (dated)
    status = []
    for t in DOMES:
        for fam in ("MERIDIONAL", "HOOP"):
            r = s83_bars[f"RQ-{t}-SHELL_{fam}"]
            status.append({"ITEM_ID": r["ITEM_ID"], "S8_3_LANE": r["LANE"], "S8_3_KG": float(r["KG"]),
                           "S8_3A_LANE": r["LANE"], "S8_3A_KG": float(r["KG"]),
                           "QUANTITY_CONFIDENCE": "IDEALIZED_SURFACE_DENSITY_QTO",
                           "PHYSICAL_DISTRIBUTION": "NOT_ESTABLISHED" if fam == "MERIDIONAL" else
                           "SUPPORTED_ALONG_MERIDIAN (spacing reference only; counts and laps unresolved)",
                           "FABRICATION_GRADE": "UNRESOLVED", "LOWER_BOUND_CLAIM": "NONE", "BBS": "NOT_VALIDATED",
                           "DATE": DATE, "WHY": "the source states Ø12 at 150 mm in two directions but not where the "
                           "meridional spacing applies, nor any curtailment, lap or crown detail" if fam == "MERIDIONAL"
                           else "hoops at 150 mm along the meridian give A / s exactly as a continuous quantity; whole "
                           "circles and laps are not detailed"})
    status.append({"ITEM_ID": "S8.3 released reinforcement (both domes)", "S8_3_LANE": "PROJECT_BASIS_QTO",
                   "S8_3_KG": frozen_kg, "S8_3A_LANE": "PROJECT_BASIS_QTO", "S8_3A_KG": frozen_kg,
                   "QUANTITY_CONFIDENCE": "IDEALIZED_SURFACE_DENSITY_QTO", "PHYSICAL_DISTRIBUTION": "NOT_ESTABLISHED",
                   "FABRICATION_GRADE": "UNRESOLVED", "LOWER_BOUND_CLAIM": "NONE", "BBS": "NOT_VALIDATED", "DATE": DATE,
                   "WHY": f"interpretation range {sc[0]['KG_TWO_DOMES']:.3f} (A) to {sc[1]['KG_TWO_DOMES']:.3f} kg (B); "
                          "neither is shown to be the physical layout"})

    # ------------------------------------------------------------ 05 bar objects against S8.3 + errata
    recon = []
    cuts = Counter()
    for o in objs:
        h = o["handle"]
        if h in KNOWN:
            fam, state = KNOWN[h], "ALREADY_RECORDED"
        elif o["type"] == "INSERT":
            fam, state = "S8.3 N-HOOP-DOTS SHELL_HOOP (graphic)", "ALREADY_RECORDED"
        elif o["type"] == "CIRCLE":
            fam, state = "S8.3 N-RING-DOTS RING_TOP / RING_BOTTOM / RING_SIDE (graphic; E01)", "ALREADY_RECORDED"
        elif o["layer"] == "REIN" and o["zone"] == "RING_CUT":
            fam, state = "RING_LINKS (the right cut's drawn link: same family as N-1A0B)", "REPEAT_OF_RECORDED_FAMILY"
        else:
            fam, state = "UNMAPPED", "NEW_OBJECT"
        cuts[state] += 1
        recon.append({"HANDLE": h, "TYPE": o["type"], "LAYER": o["layer"], "ZONE": o["zone"], "MAPS_TO": fam,
                      "STATE": state, "QUANTITY_EFFECT": "none"})
    recon.sort(key=lambda r: (r["STATE"], r["HANDLE"]))
    recon.append({"HANDLE": "(none drawn)", "TYPE": "", "LAYER": "", "ZONE": "SHELL_CROWN",
                  "MAPS_TO": "crown termination / crown ring / cap mesh", "STATE": "MISSING_INFORMATION (not a drawn bar)",
                  "QUANTITY_EFFECT": "blocks a physical meridian layout; adds no family"})

    # ------------------------------------------------------------ 06 missing evidence
    missing = [
        ("ME-01", "where the meridional 150 mm applies (at the springing, as a maximum, or as an average)",
         "decides between A-type and B-type quantities", "Engineer"),
        ("ME-02", "the meridional arrangement: number of radial bars, which stop and where, or a crown detail (crown "
         "ring, cap mesh, cut-off radius)", "the drawn continuous meridians cannot all pass the crown", "Engineer"),
        ("ME-03", "laps / splices of both families: positions and lengths", "hoops reach 13.6 m on the mid-surface",
         "Engineer"),
        ("ME-04", "anchorage of the meridians into the ring: leg length and hook", "follows the ring depth "
         "'AS PER ARCH' (S8.3 CF-S8.3-03)", "Engineer / architect"),
        ("ME-05", "bar layer position and cover (mid-surface used)", "intrados / extrados change the area by -5 / +5 %",
         "Engineer"),
        ("ME-06", "one mesh or two (S8.3 CF-S8.3-07 read one from the drawing)", "doubles the quantity", "Engineer"),
        ("ME-07", "role and size of the unlabelled junction bar (S8.3-E02)", "already blocked; listed so it is not "
         "lost", "Engineer")]
    missing = [{"ID": i, "MISSING": m, "WHY_IT_MATTERS": w, "WHO": who} for i, m, w, who in missing]

    # ------------------------------------------------------------ 07 frozen verification, summary, manifest
    after = DR.verify_frozen(S83_MANIFEST, ROOT)
    check(after["manifest_sha256"] == frozen["s8_3"]["manifest_sha256"], "S8.3 unchanged")
    errata_now = {p.name: _sha(p) for p in sorted(S83_ERRATA.glob("0*"))}
    check(errata_now == frozen["s8_3_errata"], "S8.3 errata unchanged")
    for o in OUTPUTS + [MANIFEST_NAME]:
        if (HERE / o).exists():
            (HERE / o).unlink()
    _csv(OUTPUTS[1], evidence)
    _csv(OUTPUTS[2], [{k: (_r(v) if isinstance(v, float) else v) for k, v in r.items()} for r in sc])
    _csv(OUTPUTS[3], [{k: (_r(v) if isinstance(v, float) else v) for k, v in r.items()} for r in feas])
    _csv(OUTPUTS[4], [{k: (_r(v) if isinstance(v, float) else v) for k, v in r.items()} for r in status])
    _csv(OUTPUTS[5], recon)
    _csv(OUTPUTS[6], missing)
    _json(OUTPUTS[7], {"s8_3_manifest": after["manifest"], "s8_3_manifest_sha256": after["manifest_sha256"],
                       "s8_3_files_checked": after["files_checked"], "s8_3_errata_sha256": errata_now,
                       "earlier_stages_recorded_by_s8_3": frozen["earlier_from_s8_3"],
                       "verified_before_and_after": True})
    summary = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "corrects": "S8.3 (frozen, unchanged)",
               "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
               "mid_surface": {"R_m": _r(Rm), "centre_below_springing_m": _r(d), "area_m2": _r(frame["area"]),
                               "rim_radius_m": _r(frame["rim_radius"]), "rim_circumference_m": _r(frame["rim_circumference"]),
                               "meridian_m": _r(frame["meridian"]), "psi0_rad": _r(frame["psi0"])},
               "scenarios": {r["SCENARIO"]: {"meridional_m_per_dome": _r(r["MERIDIONAL_M_PER_DOME"]),
                                             "hoop_m_per_dome": _r(r["HOOP_M_PER_DOME"]),
                                             "kg_two_domes": _r(r["KG_TWO_DOMES"]), "lane": r["LANE"]} for r in sc},
               "meridian_count_unrounded": _r(Bm["count"]),
               "frozen_reinforcement_kg": frozen_kg, "frozen_quantity_changed": False,
               "quantity_confidence": "IDEALIZED_SURFACE_DENSITY_QTO", "physical_distribution": "NOT_ESTABLISHED",
               "fabrication_grade": "UNRESOLVED", "lower_bound_claim": "NONE", "bbs": "NOT_VALIDATED",
               "suitable_for_project_basis_boq": "YES_WITH_LABEL",
               "new_bar_objects": cuts.get("NEW_OBJECT", 0), "bar_object_states": dict(sorted(cuts.items())),
               "drawing": {k: (_r(v, 6) if isinstance(v, float) else v) for k, v in ev.items()
                           if k in ("bar_crosses_crown", "bar_sweep", "dots", "dot_step_deg", "dot_step_spread",
                                    "dot_spacing_mm_at_detail_proportion", "plan_radial_lines_per_dome")},
               "references_read": []}
    _json(OUTPUTS[8], summary)
    (HERE / OUTPUTS[0]).write_text(readme(summary, sc, evidence, missing), encoding="utf-8")
    _json(MANIFEST_NAME, {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "DATED_CORRECTION_LAYER",
                          "corrects": "S8.3 (frozen, unchanged)", "references_read": [],
                          "engine_commit_stamp": summary["engine_commit"], "code": {c: _sha(ROOT / c) for c in CODE},
                          "inputs": {str(p.relative_to(ROOT)): _sha(p) for p in
                                     (S83_MANIFEST, S83 / "15_S8_3_SUMMARY.json", S83 / "08_REBAR_QTO_REGISTER.csv")},
                          "drawing_sha256": {"ST7757.dxf": STRUCT_SHA},
                          "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
                          "rule": "a confidence and evidence correction: no frozen quantity changes, no scenario "
                                  "is released"})
    return summary


def readme(s, sc, ev, missing):
    a, b = sc[0], sc[1]
    L = ["# S8.3A: independent dome-shell reinforcement distribution audit", "",
         f"Baseline `{s['baseline']}`. A dated correction layer on the frozen S8.3; S8.3 and its errata verify unchanged.",
         "", "## Answer", "",
         f"- The frozen **{s['frozen_reinforcement_kg']:.6f} kg** stays the S8.3 PROJECT_BASIS_QTO quantity, now "
         "classified **IDEALIZED_SURFACE_DENSITY_QTO**.",
         "  - It is not a physical lower bound and not a validated BBS.",
         "  - The fabrication-grade layout is unresolved.",
         "- The drawing is a generic specification: Ø12 at 150 mm, meridional and hoop, one typical section, N.I.S.",
         "  - It does not say where the meridional 150 mm applies.",
         "  - Its one continuous meridian drawn over the crown cannot be built for every bar.",
         "- The hoops are supported as 150 mm along the meridian. Their continuous total is A / s in every scenario.",
         "- The scenarios differ only in the meridians:", ""]
    L += ["| scenario | meridional m / dome | hoop m / dome | kg, two domes | x frozen | lane |", "|---|---|---|---|---|---|"]
    L += [f"| {r['SCENARIO']} {r['NAME']} | {r['MERIDIONAL_M_PER_DOME']:.6f} | {r['HOOP_M_PER_DOME']:.6f} | "
          f"{r['KG_TWO_DOMES']:.6f} | {r['RATIO_TO_FROZEN']:.4f} | {r['LANE']} |" for r in sc]
    L += ["", "## Formulas", "",
          f"Mid-surface: R_m = {s['mid_surface']['R_m']:.9f} m, centre {s['mid_surface']['centre_below_springing_m']:.9f} "
          f"m below the springing, psi0 = acos(d / R_m) = {s['mid_surface']['psi0_rad']:.9f} rad.",
          "",
          f"- Area: A = 2 pi R_m^2 (1 - cos psi0) = {s['mid_surface']['area_m2']:.9f} m2.",
          f"- Springing circle: 2 pi R_m sin psi0 = {s['mid_surface']['rim_circumference_m']:.9f} m.",
          f"- Meridian, springing to crown: R_m psi0 = {s['mid_surface']['meridian_m']:.9f} m.",
          "- A: L = A / s for each family.",
          f"- B: N = circumference / s = {s['meridian_count_unrounded']:.6f} (unrounded); L_mer = N R_m psi0; "
          "L_hoop = A / s.",
          "- C (a test rule, not a source): every other meridian stops where the spacing falls to 75 mm.",
          f"- kg = L x 12^2 / 162 x {len(DOMES)} domes.", "", "## Drawing evidence", ""]
    L += [f"- **{e['QUESTION']}**: {e['OBSERVED']}. {e['CONCLUSION']}." for e in ev]
    L += ["", "## Missing evidence for a physically defensible quantity", ""] + \
         [f"- {m['ID']} ({m['WHO']}): {m['MISSING']}. {m['WHY_IT_MATTERS']}." for m in missing]
    L += ["", f"No new bar object was found beyond the S8.3 register and errata ({s['bar_object_states']}). The crown "
          "termination is missing information, not a missing drawn bar.", "",
          "## Outputs", ""] + [f"- `{o}`" for o in OUTPUTS] + [f"- `{MANIFEST_NAME}`"]
    return "\n".join(L) + "\n"


def main():
    try:
        s = build()
    except Stop as e:
        raise SystemExit(f"STOP: {e}")
    print(json.dumps({k: s[k] for k in ("scenarios", "quantity_confidence", "new_bar_objects", "frozen_quantity_changed")},
                     indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
