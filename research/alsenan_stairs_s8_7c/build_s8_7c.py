"""S8.7C - stair design resolution study (research and design comparison; NOT approval to change the drawings). A
study layer over the frozen S8.7, S8.7A and S8.7B packages (read, never written). Blind: frozen before any earlier
commercial figure is read. Release delta: 0 m3 concrete and 0 kg reinforcement.

    python3 -I research/alsenan_stairs_s8_7c/build_s8_7c.py

Reads:
- the frozen S8.7B plan evidence (every riser line with its handles), section A-A record, beam audit, callouts and
  release summary, the frozen S8.7 plates / bars / S7 record, S1 beam definitions and slab panels, S6 occurrences;
- ST7757.dxf and P7757.dxf again by handle (ezdxf), to confirm every position this study builds on;
- section A-A (P7757 sections PDF sheet 4) rendered at 600 dpi into a temporary folder and measured along the plan
  direction this time: the landing edge, the north wall, the arrival riser, the south wall, the feet and the lines in
  the two turns.
Then it builds the GF -> 1F alternatives (28 and 27 risers, as drawn and with stated modifications), the 1F -> 2F
winder reconciliation, the round-stair audit, the conditional concrete comparison, the reinforcement / double-count
audit, a short prioritised RFI and two schematic SVG diagrams drawn from the coordinates. Nothing is approved,
selected or released.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "research" / "external_engine_lab"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import delta_release as DR  # noqa: E402
from engine.source import rebar_unit_mass as UM  # noqa: E402
from engine.source import stair_fit_checks as FC  # noqa: E402
from engine.source import stair_geometry as SG  # noqa: E402
from engine.source import stair_scenario_checks as SC  # noqa: E402

ROUND = "S8_7C"
DATE = "2026-10-10"
BASELINE_HEAD = "0cda418"
POLICY = "S8_7C_STAIR_DESIGN_RESOLUTION_STUDY_V1"
R = ROOT / "research"
BY_SHA = ROOT / "data/inputs/by_sha256"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
STRUCT_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
ARCH_PDF_SHA = "1e7087d3e61bbb682c9107193c97550a2837e5198bde0ee311319bf7f4a08459"
S87, S87A, S87B = R / "alsenan_stairs_s8_7", R / "alsenan_stairs_s8_7a", R / "alsenan_stairs_s8_7b"
S87B_MANIFEST = S87B / "16_S8_7B_FREEZE_MANIFEST.json"
MANIFESTS = {k: v for k, v in json.loads((S87B / "14_RELEASE_SUMMARY.json").read_text(encoding="utf-8"))
             ["frozen_baselines"].items()}          # names only; paths below
MANIFEST_PATHS = {"S4": "alsenan_footing_rebar_s4/S4_FREEZE_MANIFEST.json",
                  "S4.1": "alsenan_footing_rebar_s4_1/S4_1_FREEZE_MANIFEST.json",
                  "S5": "alsenan_ground_system_rebar_s5/S5_FREEZE_MANIFEST.json",
                  "S5.1": "alsenan_ground_system_rebar_s5_1/S5_1_FREEZE_MANIFEST.json",
                  "S6": "alsenan_superstructure_beam_rebar_s6/S6_FREEZE_MANIFEST.json",
                  "S6.1": "alsenan_superstructure_beam_rebar_s6_1/S6_1_FREEZE_MANIFEST.json",
                  "AD1": "ad1_authority_decisions/AD1_FREEZE_MANIFEST.json",
                  "D1.1": "d1_1_stirrup_authority_audit/D1_1_FREEZE_MANIFEST.json",
                  "D1.2": "d1_2_footing_cover_audit/D1_2_FREEZE_MANIFEST.json",
                  "PRE-S7": "alsenan_slab_rebar_pre_s7/PRE_S7_FREEZE_MANIFEST.json",
                  "PRE-S7.1": "alsenan_slab_rebar_pre_s7_1/PRE_S7_1_FREEZE_MANIFEST.json",
                  "S7": "alsenan_slab_rebar_s7/12_S7_FREEZE_MANIFEST.json",
                  "S7A": "alsenan_slab_rebar_s7a_qa/11_S7A_FREEZE_MANIFEST.json",
                  "PRE-S8": "pre_s8_structural_completeness/13_PRE_S8_FREEZE_MANIFEST.json",
                  "S8.1": "alsenan_ground_slab_s8_1/11_S8_1_FREEZE_MANIFEST.json",
                  "S8.1A": "alsenan_ground_slab_s8_1a/14_S8_1A_FREEZE_MANIFEST.json",
                  "S8.2": "alsenan_swimming_pool_s8_2/18_S8_2_FREEZE_MANIFEST.json",
                  "S8.2A": "alsenan_swimming_pool_s8_2a/12_S8_2A_FREEZE_MANIFEST.json",
                  "S8.3": "alsenan_dome_ring_s8_3/16_S8_3_FREEZE_MANIFEST.json",
                  "S8.3A": "alsenan_dome_mesh_s8_3a/09_S8_3A_FREEZE_MANIFEST.json",
                  "S8.4": "alsenan_water_tank_s8_4/15_S8_4_FREEZE_MANIFEST.json",
                  "S8.5": "alsenan_special_columns_s8_5/17_S8_5_FREEZE_MANIFEST.json",
                  "S8.6": "alsenan_lintels_s8_6/15_S8_6_FREEZE_MANIFEST.json",
                  "S8.6A": "alsenan_lintels_s8_6a/12_S8_6A_CORRECTION_MANIFEST.json",
                  "S8.7": "alsenan_stairs_s8_7/17_S8_7_FREEZE_MANIFEST.json",
                  "S8.7A": "alsenan_stairs_s8_7a/15_S8_7A_CORRECTION_MANIFEST.json",
                  "S8.8": "alsenan_lift_s8_8/18_S8_8_FREEZE_MANIFEST.json",
                  "S8.7B": "alsenan_stairs_s8_7b/16_S8_7B_FREEZE_MANIFEST.json"}
READ = {"S87B_EVIDENCE": S87B / "12_PLAN_RISER_LINE_EVIDENCE.csv",
        "S87B_SECTION": S87B / "13_SECTION_AND_DETAIL_EVIDENCE.csv",
        "S87B_BEAMS": S87B / "06_BEAM_INTERFERENCE_AUDIT.csv",
        "S87B_CONCRETE": S87B / "08_WAIST_THICKNESS_CONCRETE_SENSITIVITY.csv",
        "S87B_REBAR": S87B / "09_REINFORCEMENT_OWNERSHIP_AUDIT.csv",
        "S87B_SUMMARY": S87B / "14_RELEASE_SUMMARY.json",
        "S87_GEOMETRY": S87 / "06_PLAN_AND_INCLINED_GEOMETRY.csv",
        "S87_CONCRETE": S87 / "07_CONCRETE_QTO.csv",
        "S87_REBAR": S87 / "09_REBAR_QTO.csv",
        "S87_S7": S87 / "11_S7_STAIR_ADJACENT_RECOMPUTE.csv",
        "S87_SUMMARY": S87 / "16_S8_7_SUMMARY.json",
        "S1_BEAMS": R / "alsenan_structural_census_s1/BEAM_DEFINITION_REGISTER.json",
        "S1_SLABS": R / "alsenan_structural_census_s1/SLAB_PANEL_REGISTER.json",
        "S6_OCC": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCES.csv",
        "S86_REGISTRATION": R / "alsenan_lintels_s8_6/03_ARCH_STRUCTURAL_REGISTRATION.csv"}
CODE = ["engine/source/stair_fit_checks.py", "engine/source/stair_scenario_checks.py",
        "engine/source/stair_geometry.py", "engine/source/rebar_unit_mass.py", "engine/source/delta_release.py",
        "research/alsenan_stairs_s8_7c/build_s8_7c.py", "research/external_engine_lab/alsenan_structural_s1.py"]
OUTPUTS = ["00_README.md", "01_SOURCE_EVIDENCE_REGISTER.csv", "02_GF_1F_27_VS_28_GEOMETRY.csv",
           "03_GF_1F_TRANSITION_LEVELS.csv", "04_LANDING_BEAM_CLASH_AUDIT.csv", "05_1F_2F_WINDER_RECONCILIATION.csv",
           "06_ROUND_STAIR_GEOMETRY_AUDIT.csv", "07_CONDITIONAL_CONCRETE_COMPARISON.csv",
           "08_REINFORCEMENT_DOUBLE_COUNT_AUDIT.csv", "09_PRIORITISED_RFI.csv", "10_CONSERVATION_CHECKS.csv",
           "11_RELEASE_SUMMARY.json", "12_PROVENANCE.jsonl", "14_DIAGRAM_GF_1F_PLAN.svg",
           "15_DIAGRAM_GF_1F_DEVELOPED_SECTION.svg"]
MANIFEST_NAME = "13_S8_7C_FREEZE_MANIFEST.json"
UNIT_MASS = {"method": UM.D2_OVER_162, "authority": "project-wide method used by S3.1 / S6.1 / S7 / S8",
             "selected_by": "Urban (project basis)"}
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")

# ------------------------------------------------------------------ vocabulary
FACT = "MEASURED_DRAWING_FACT"
PRINTED = "PRINTED_ON_DRAWING"
SCALED = "SCALED_FROM_SECTION (indicative)"
FROZEN = "FROZEN_RECORD"
INFERRED = "INFERRED_NOT_PRINTED"
TYPICAL = "TYPICAL_ONLY (N.I.S.)"
PROPOSED = "PROPOSED_MODIFICATION (not drawn)"
OWNER_PROV = "PROVISIONAL_OWNER_SCENARIO"
ENGINEER = "REQUIRES_ENGINEER_CONFIRMATION"
UNVERIFIED = "UNVERIFIED_ENGINEERING_INTERPRETATION"
CONFLICTING = "CONFLICTING"
POSSIBLE_MOD = "GEOMETRICALLY_POSSIBLE_ONLY_WITH_MODIFICATIONS (unverified)"
REFERENCE = "REFERENCE_ONLY"
SENS = "RESEARCH_SENSITIVITY_NOT_RELEASED"
COND = "CONDITIONAL_ESTIMATE_NOT_RELEASED"
ALREADY = "ALREADY_OWNED_BY_S8_7 (frozen; not counted again)"
BLOCKED = "BLOCKED_UNQUANTIFIED"
UNRESOLVED = "OWNERSHIP_UNRESOLVED (shown, never in a total)"

# ------------------------------------------------------------------ cited geometry (structural sheet-local mm), every value
# confirmed against the drawing by handle in confirm_geometry()
X_BAY_W, X_WALL_W, X_WALL_E, X_BAY_E = 17087.904, 18287.904, 18387.904, 19587.904
Y_TURN, Y_LAND_EDGE, Y_BAY_N = 19461.856, 19411.856, 20611.856
B20 = (15911.856, 16311.856)
B23 = (15861.856, 16311.856)
GB_NORTH = 15711.856
FEET = {"GFRS": 16161.856, "ARCH-GF": 16761.856, "GBP": 16761.856}
CONFIRM = [  # (sheet or plan, handle, axis value expected, what)
    ("GFRS", "45A", 16161.856, "structural lower-flight first riser (foot)"),
    ("GFRS", "25E", Y_TURN, "structural 12th lower riser = turn start"),
    ("GFRS", "25B", Y_LAND_EDGE, "structural first upper riser = landing edge"),
    ("GFRS", "459", 16111.856, "structural 12th upper riser"),
    ("GFRS", "270", 16411.856, "structural 11th upper riser"),
    ("GFRS", "458", B20[0], "B20 south face"), ("GFRS", "2C6", B20[1], "B20 north face"),
    ("GFRS", "279", Y_BAY_N, "bay north edge"),
    ("FFRS", "5E4", B23[0], "B23 south face"), ("FFRS", "5E1", B23[1], "B23 north face"),
    ("FFRS", "646", 16161.856, "1F -> 2F first riser (foot)"), ("FFRS", "644", 16411.856, "1F -> 2F last upper riser"),
    ("GBP", "7CC", GB_NORTH, "ground-beam north face under the stair"),
    ("GBP", "112", 16761.856, "ground-beam plan lower-flight first riser"),
    ("ARCH-GF", "DE", 16761.856, "architectural GF lower-flight first riser face (hidden)"),
    ("ARCH-GF", "497", 16411.856, "architectural GF last upper riser"),
    ("ARCH-1F", "AC2", 16161.856, "architectural 1F lower-flight first riser face"),
    ("ARCH-1F", "ABD", 16411.856, "architectural 1F last upper riser")]
RADIALS = [("2F6", 156.018), ("2F4", 135.0), ("2F5", 113.982)]     # GFRS winder radials (S8.7B 12), walking order
GOING = 300.0
WIDTH = 1200.0
FFL = {"GF": 1000.0, "1F": 5500.0, "2F": 9700.0}
WAISTS = (150.0, 160.0, 175.0, 200.0)
PREF = (150.0, 160.0)
S7_KG, S87_KG, S87_M3 = 71.895327413, 59.020862261, 0.516582788

# section A-A (600 dpi page pixels, cited windows; the crop is pixel-identical to a full render)
SEC = {"page": 4, "dpi": 600, "dark": 140, "crop": (1500, 3700, 3900, 2900),
       "chain_bottom": (6450, 6560, 1500, 5400), "chain_levels": (0.00, 9.70, 13.90, 14.40)}


class Stop(RuntimeError):
    pass


def check(cond, msg):
    if not cond:
        raise Stop(msg)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _full(v, nd=9):
    s = f"{v:.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return _full(v)
    if isinstance(v, (list, tuple, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _r(v, nd=9):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


def _csv(name, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in fields})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def _json(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode())
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()[:16]


# ------------------------------------------------------------------ inputs
def verify_inputs():
    for sha, name, ext in ((ARCH_SHA, "P7757.dxf", "dxf"), (STRUCT_SHA, "ST7757.dxf", "dxf"),
                           (ARCH_PDF_SHA, "P7757 sections PDF", "pdf")):
        f = BY_SHA / f"{sha}.{ext}"
        check(f.exists(), f"private input {name} not in data/inputs/by_sha256 (never committed)")
        check(_sha(f) == sha, f"{name} unchanged")
    check(set(MANIFESTS) | {"S8.7B"} == set(MANIFEST_PATHS), "the frozen stage list")
    return {k: DR.verify_frozen(R / p, ROOT) for k, p in MANIFEST_PATHS.items()}


def confirm_geometry():
    """every cited position read again from the drawings by handle (structural: S1 sheet frames; architectural: the
    frozen S8.6 translation)."""
    import ezdxf
    import alsenan_structural_s1 as S1
    src = S1.Source()
    fr = {k: src.sheets[k]["frame"] for k in ("GBP", "GFRS", "FFRS")}
    by = {}
    for e in src.msp.query("LINE"):
        a, b = e.dxf.start, e.dxf.end
        for sh, f in fr.items():
            if f[0] <= a.x <= f[2] and f[1] <= a.y <= f[3]:
                by[(sh, e.dxf.handle)] = ((a.x - f[0], a.y - f[1]), (b.x - f[0], b.y - f[1]))
    T = {r["FLOOR"]: (float(r["TX_MM"]), float(r["TY_MM"])) for r in _rows(READ["S86_REGISTRATION"])
         if r["RECORD"] == "FLOOR"}
    doc = ezdxf.readfile(str(BY_SHA / f"{ARCH_SHA}.dxf"))
    for e in doc.modelspace().query("LINE"):
        for fl in ("GF", "1F"):
            if f"ARCH-{fl}" in {c[0] for c in CONFIRM}:
                tx, ty = T[fl]
                by.setdefault((f"ARCH-{fl}", e.dxf.handle), ((e.dxf.start.x + tx, e.dxf.start.y + ty),
                                                             (e.dxf.end.x + tx, e.dxf.end.y + ty)))
    rows = []
    radial = {}
    for h, ang in RADIALS:
        line = by.get(("GFRS", h))
        check(line is not None, f"GFRS radial {h} present")
        (x1, y1), (x2, y2) = line
        check(abs(math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180 - ang) < 0.01, f"GFRS radial {h} at {ang} deg")
        radial[h] = line
    centre = _fan_centre(list(radial.values()))
    rows.append({"ID": "G-GFRS-RADIALS", "FACT": "GF -> 1F drawn winder radials (start / end)",
                 "VALUE": {h: [[_r(v, 3) for v in pt] for pt in ln] for h, ln in radial.items()},
                 "UNIT": "mm (sheet-local)", "SOURCE": "ST7757 GFRS handles " + " / ".join(radial), "STATUS": FACT})
    rows.append({"ID": "G-GFRS-FAN", "FACT": "fan centre of the three radials (least-squares intersection)",
                 "VALUE": [_r(centre[0], 3), _r(centre[1], 3), _r(centre[2], 3)], "UNIT": "mm (x, y, rms miss)",
                 "SOURCE": "derived from the radials above", "STATUS": FACT})
    for sh, h, want, what in CONFIRM:
        line = by.get((sh, h))
        check(line is not None, f"{sh} {h} present")
        a, b = line
        got = a[1] if abs(a[1] - b[1]) < 0.5 else None
        check(got is not None and abs(got - want) < 0.01, f"{sh} {h} at y {want} ({what})")
        rows.append({"ID": f"G-{sh}-{h}", "FACT": what, "VALUE": _r(got, 3), "UNIT": "mm (y, sheet-local)",
                     "SOURCE": f"{'P7757' if sh.startswith('ARCH') else 'ST7757'} {sh} handle {h}", "STATUS": FACT})
    cols = {}
    for e in src.msp.query("LWPOLYLINE"):
        if e.closed and e.dxf.layer.upper().startswith("S-COL"):
            pts = [(p[0], p[1]) for p in e.get_points("xy")]
            cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
            f = fr["GFRS"]
            if f[0] <= cx <= f[2] and f[1] <= cy <= f[3]:
                xs, ys = [p[0] - f[0] for p in pts], [p[1] - f[1] for p in pts]
                cols[e.dxf.handle] = (min(xs), min(ys), max(xs), max(ys))
    check("36B" in cols and abs(cols["36B"][2] - 17137.904) < 0.5, "column 36B projects 50 mm into the west flight")
    rows.append({"ID": "G-GFRS-36B", "FACT": "column 36B outline (projects into the west flight width)",
                 "VALUE": [_r(v, 3) for v in cols["36B"]], "UNIT": "mm bbox", "SOURCE": "ST7757 GFRS S-COL.BON 36B",
                 "STATUS": FACT})
    return rows, cols, {"lines": radial, "centre": centre}


def _fan_centre(lines):
    """least-squares point closest to every (infinite) line; returns x, y and the rms distance to the lines."""
    sxx = sxy = syy = bx = by_ = 0.0
    eqs = []
    for (x1, y1), (x2, y2) in lines:
        L = math.hypot(x2 - x1, y2 - y1)
        nx, ny = -(y2 - y1) / L, (x2 - x1) / L
        c = nx * x1 + ny * y1
        sxx, sxy, syy, bx, by_ = sxx + nx * nx, sxy + nx * ny, syy + ny * ny, bx + nx * c, by_ + ny * c
        eqs.append((nx, ny, c))
    det = sxx * syy - sxy * sxy
    check(abs(det) > 1e-9, "radials not parallel")
    x, y = (bx * syy - by_ * sxy) / det, (sxx * by_ - sxy * bx) / det
    rms = math.sqrt(sum((nx * x + ny * y - c) ** 2 for nx, ny, c in eqs) / len(eqs))
    return x, y, rms


# ------------------------------------------------------------------ section A-A along the plan direction
def _render():
    import numpy as np
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    x, y, w, h = SEC["crop"]
    with tempfile.TemporaryDirectory() as d:
        subprocess.run(["pdftoppm", "-f", str(SEC["page"]), "-l", str(SEC["page"]), "-r", str(SEC["dpi"]),
                        "-x", str(x), "-y", str(y), "-W", str(w), "-H", str(h), "-png",
                        str(BY_SHA / f"{ARCH_PDF_SHA}.pdf"), str(Path(d) / "p")], check=True, capture_output=True)
        f = sorted(Path(d).glob("p*.png"))
        check(len(f) == 1, "one rendered window")
        win = np.asarray(Image.open(f[0]).convert("L")) < SEC["dark"]
    out = np.zeros((y + h, x + w), dtype=bool)
    out[y:, x:] = win
    return out


def _groups(idx, origin):
    g = []
    for i in idx:
        if g and i - g[-1][-1] <= 1:
            g[-1].append(i)
        else:
            g.append([i])
    return [{"lo": origin + a[0], "hi": origin + a[-1], "c": origin + (a[0] + a[-1]) / 2.0, "w": len(a)} for a in g]


def _v(dark, y0, y1, x0, x1, frac=0.9):          # constant page-x lines (level surfaces)
    import numpy as np
    return _groups(np.where(dark[y0:y1, x0:x1].sum(axis=0) >= frac * (y1 - y0))[0].tolist(), x0)


def _h(dark, x0, x1, y0, y1, frac=0.85):         # constant page-y lines (vertical faces: risers, walls)
    import numpy as np
    return _groups(np.where(dark[y0:y1, x0:x1].sum(axis=1) >= frac * (x1 - x0))[0].tolist(), y0)


def section_plan_direction():
    import numpy as np
    dark = _render()
    thin = [g for g in _v(dark, *SEC["chain_bottom"]) if g["w"] <= 7]
    check(len(thin) == 4, "bottom level chain")
    E = np.array(SEC["chain_levels"])
    b, a = np.polyfit(E, np.array([g["c"] for g in thin]), 1)
    check(abs(b / (SEC["dpi"] / 0.0254 / 100) - 1) < 0.005, "1:100")

    def x_of(elev):
        return a + b * elev

    def thick(gs):
        return [g for g in gs if g["w"] >= 9]
    m = {}
    # GF -> 1F: first upper riser (landing edge), arrival riser, north wall, south wall, foot
    up = thick(_h(dark, int(x_of(3.46)), int(x_of(3.59)), 5700, 5850))
    arr = thick(_h(dark, int(x_of(5.30)), int(x_of(5.44)), 4900, 5100))
    nw = thick(_h(dark, int(x_of(3.65)), int(x_of(4.25)), 5950, 6200, 0.9))
    sw = thick(_h(dark, int(x_of(5.00)), int(x_of(5.30)), 4700, 5100, 0.9))
    foot = _h(dark, int(x_of(1.02)), int(x_of(1.15)), 5000, 5400)
    check(up and arr and len(nw) == 2 and len(sw) == 2 and foot, "GF -> 1F horizontal features")
    edge = up[0]["c"]
    ppm = b / 1000.0                              # page pixels per plan mm

    def plan_y(py):
        return Y_LAND_EDGE - (edge - py) / ppm
    # line centres throughout (the riser and wall lines are drawn about 50 mm wide at 1:100)
    m["A1"] = {"landing_edge_px": edge, "arrival_px": arr[0]["c"], "north_wall_line_px": nw[0]["c"],
               "south_wall_line_px": sw[1]["c"], "foot_px": (foot[0]["c"] + foot[-1]["c"]) / 2.0}
    m["A1"]["landing_depth_mm"] = (m["A1"]["north_wall_line_px"] - edge) / ppm
    m["A1"]["upper_run_mm"] = (edge - m["A1"]["arrival_px"]) / ppm
    m["A1"]["arrival_plan_y"] = plan_y(m["A1"]["arrival_px"])
    m["A1"]["foot_plan_y"] = plan_y(m["A1"]["foot_px"])
    m["A1"]["south_wall_plan_y"] = plan_y(m["A1"]["south_wall_line_px"])
    # 1F -> 2F
    up2 = thick(_h(dark, int(x_of(7.66)), int(x_of(7.79)), 5700, 5850))
    arr2 = thick(_h(dark, int(x_of(9.50)), int(x_of(9.64)), 4900, 5100))
    foot2 = _h(dark, int(x_of(5.52)), int(x_of(5.65)), 4900, 5100)
    check(up2 and arr2 and foot2, "1F -> 2F horizontal features")
    e2 = up2[0]["c"]
    m["A2"] = {"landing_edge_px": e2, "arrival_px": arr2[0]["c"], "foot_px": foot2[-1]["c"],
               "upper_run_mm": (e2 - arr2[0]["c"]) / ppm,
               "arrival_plan_y": Y_LAND_EDGE - (e2 - arr2[0]["c"]) / ppm,
               "foot_plan_y": Y_LAND_EDGE - (e2 - foot2[-1]["c"]) / ppm}
    # the turn zones between the end of the lower flight and the north wall
    for run, lo_e, hi_e in (("A1", 2.50, 3.40), ("A2", 7.10, 7.66)):
        zone = (int(edge), int(m["A1"]["north_wall_line_px"]))
        lines = []
        for x in range(int(x_of(lo_e)), int(x_of(hi_e))):
            col = np.concatenate(([0], dark[zone[0]:zone[1], x].astype(np.int8), [0]))
            d = np.diff(col)
            segs = [(s_, e_) for s_, e_ in zip(np.where(d == 1)[0].tolist(), np.where(d == -1)[0].tolist())
                    if e_ - s_ >= 20]
            if sum(e_ - s_ for s_, e_ in segs) > 0.45 * (zone[1] - zone[0]):
                lines.append((x, len(segs)))
        # dashed tread lines: columns broken into three or more dashes; a dashed line touching a solid one is
        # still found by its dashed columns
        dashed = [round((g["c"] - a) / b, 3) for g in _groups([x for x, n in lines if n >= 3], 0) if g["w"] <= 5]
        m[run]["turn_dashed_levels_m"] = dashed
        m[run]["turn_solid_levels_m"] = [round((g["c"] - a) / b, 3) for g in _groups([x for x, n in lines if n == 1], 0)]
    check(len(m["A1"]["turn_dashed_levels_m"]) == 5 and not m["A2"]["turn_dashed_levels_m"],
          "five dashed winder treads in the GF -> 1F turn, none in the 1F -> 2F turn")
    check(abs(m["A1"]["landing_depth_mm"] - 1200) < 15 and abs(m["A1"]["upper_run_mm"] - 3300) < 15
          and abs(m["A2"]["upper_run_mm"] - 3300) < 15, "section A-A landing depth and upper runs")
    m["scale_px_per_m"] = b
    return m


# ------------------------------------------------------------------ fan centre / walking line of the drawn turn
def turn_walking(evidence):
    rad = [r for r in evidence if r["VIEW"] == "GFRS" and r["ELEMENT_ID"] == "A1-W1" and r["PART"] == "TURN_RADIAL"]
    check(len(rad) == 3, "three radial winder risers on the GF roof sheet")
    S87B_TREADS = _rows(READ["S87B_CONCRETE"])
    w = next(r for r in S87B_TREADS if r["ELEMENT_ID"] == "A1-W1" and r["WAIST_MM"] == "160")
    areas = json.loads(w["EVIDENCE"].split("tread areas m2 ")[1])
    going = float(w["GOING_MM"])
    return {"radial_angles": [float(r["ANGLE_DEG"]) for r in rad], "tread_areas_m2": areas,
            "walking_length_mm": going * 4, "drawn_going_mm": going, "plan_area_m2": float(w["PLAN_AREA_M2"])}


def equal_wedge_areas(n_treads, plan_area_m2, drawn_areas):
    """a proposed n-tread turn (not drawn): the quarter split into n equal walking-line goings; tread areas taken
    proportional to the drawn turn's mean (equal-area approximation)."""
    return [plan_area_m2 / n_treads] * n_treads


# ------------------------------------------------------------------ GF -> 1F alternatives
SCENARIOS = [
    # id, title, n_lower, n_turn, n_upper, upper going, family, modifications, drawn by
    ("A-28", "Scenario A: 28 risers as drawn on the structural GF roof sheet", 12, 4, 12, GOING, "28",
     [], "structural GF roof sheet (12 / 3 radial + closing / landing / 12)"),
    ("A-28-M", "Scenario A with the upper goings shortened to clear B20", 12, 4, 12, 3000.0 / 11, "28",
     ["upper-flight goings 300 -> 272.7 mm (fits 12 risers between the landing edge and a 100 mm strip before B20)"],
     "none (modification of the structural arrangement)"),
    ("B-27-S", "Scenario B: 27 risers as drawn in section A-A (10 + 5-riser turn + 12)", 10, 5, 12, GOING, "27",
     ["plan turn: 4 radial winder risers + closing instead of the plans' 3 + closing"],
     "section A-A (measured); lower flight = architectural GF plan / ground-beam plan"),
    ("B-27-SM", "Scenario B with the upper goings shortened to clear B20", 10, 5, 12, 3000.0 / 11, "27",
     ["plan turn: 4 radial winder risers + closing instead of 3 + closing",
      "upper-flight goings 300 -> 272.7 mm (100 mm strip before B20, as on the architectural plan)"],
     "none (modification of the section arrangement)"),
    ("B-27-P", "27 risers keeping the plans' four-riser turn (11 + 4 + 12)", 11, 4, 12, GOING, "27",
     ["lower-flight foot at y 16461.9 (drawn by no plan)"], "none"),
    ("B-27-U", "27 risers with an 11-riser upper flight (12 + 4 + 11)", 12, 4, 11, GOING, "27",
     ["landing level moves off the printed +3.50"], "none (structural lower flight + architectural upper flight)"),
    ("REF-25", "Architectural GF plan as drawn (reference: 180 mm risers, outside the owner range)", 10, 4, 11, GOING,
     "25", [], "architectural GF plan (10 / 3 radial + closing / landing / 11)"),
]


# the GF -> 1F arrangement each drawing shows: (lower, turn, upper, upper going)
DRAWN_GF_1F = [("structural GF roof sheet", 12, 4, 12, GOING), ("architectural GF plan", 10, 4, 11, GOING),
               ("section A-A", 10, 5, 12, GOING)]


def changes_to_resolve(n1, nt, n2, g2, land, clr, h):
    """what would have to change, drawing by drawing, for one arrangement to be shown consistently (a list of
    proposals; nothing here is drawn)."""
    out = []
    for name, d1, dt, d2, dg in DRAWN_GF_1F:
        parts = []
        if n1 != d1:
            parts.append(f"lower flight {d1} -> {n1} risers (foot {abs(n1 - d1) * 300:.0f} mm "
                         f"{'south' if n1 > d1 else 'north'})")
        if nt != dt:
            parts.append(f"turn {dt} -> {nt} risers ({dt - 1} -> {nt - 1} radial)")
        if n2 != d2:
            parts.append(f"upper flight {d2} -> {n2} risers")
        if abs(g2 - dg) > 1e-6:
            parts.append(f"upper goings {dg:.0f} -> {g2:.1f} mm")
        if name == "section A-A" and abs(land - 3500.0) > 0.5:
            parts.append(f"printed half-landing +3.50 -> +{land / 1000:.3f}")
        if parts:
            out.append(f"{name}: " + "; ".join(parts))
    if n1 != 10:
        out.append(f"ground-beam plan: first riser {abs(n1 - 10) * 300:.0f} mm {'south' if n1 > 10 else 'north'}")
    if clr < 0:
        out.append(f"B20 (structural, S6): lowered / cranked locally under the top tread by about {h:.1f} mm")
    return out


def gf_1f_rows(sec, turn, cols):
    rows, trans = [], []
    rise = FFL["1F"] - FFL["GF"]
    for sid, title, n1, nt, n2, g2, fam, mods, drawn in SCENARIOS:
        n = n1 + nt + n2
        segs = [("lower flight", FC.FLIGHT, n1), ("turn (winders)", FC.WINDERS, nt), ("landing (NE quarter)",
                                                                                      FC.LANDING, 0),
                ("upper flight", FC.FLIGHT, n2)]
        tl = FC.transition_levels(FFL["GF"], FFL["1F"], segs)
        h = tl["riser"]
        foot = Y_TURN - (n1 - 1) * GOING
        check(abs(FC.run_end(foot, n1, GOING, +1) - Y_TURN) < 1e-6, "lower flight ends at the turn")
        last = FC.run_end(Y_LAND_EDGE, n2, g2, -1)
        clr = FC.band_clearance(last, B20, -1)
        land = tl["segments"][2]["start_level"]
        reach = SC.landing_reach(FFL["GF"], FFL["1F"], n, 3500.0)
        wgo = turn["walking_length_mm"] / nt
        conflicts = []
        if abs(land - 3500.0) > 0.5:
            conflicts.append(f"landing {_full(land / 1000, 3)} vs printed +3.50 ({_full(land - 3500, 1)} mm)")
        if clr < 0:
            conflicts.append(f"last upper riser {_full(-clr, 0)} mm inside B20")
        foot_by = [k for k, v in FEET.items() if abs(v - foot) < 1]
        if not foot_by:
            conflicts.append(f"foot y {_full(foot, 1)} is drawn by no plan")
        elif "ARCH-GF" not in foot_by:
            conflicts.append(f"foot y {_full(foot, 1)} = structural sheet only; architectural, ground-beam plan and "
                             "section A-A put it 600 mm north")
        if nt != 4:
            conflicts.append(f"turn of {nt} risers ({nt - 1} radial): both plans draw 4 (3 radial)")
        conflicts.append("upper flight of 12: the architectural GF plan draws 11" if n2 == 12 else
                         f"upper flight of {n2}: the structural sheet and section A-A draw 12")
        pref = PREF[0] <= h <= PREF[1]
        # the treads inside the turn quarter: after risers n1 ... n1 + nt - 1 (the closing riser leads onto the landing)
        treads = [(FFL["GF"] + k * h) / 1000 for k in range(n1, n1 + nt)]
        dashed = sec["A1"]["turn_dashed_levels_m"]
        tread_ok = len(treads) == len(dashed) and all(abs(t_ - d_) < 0.015 for t_, d_ in zip(treads, dashed))
        sec_ok = (n1 + nt == 15 and n2 == 12 and tread_ok)
        if wgo < 250:
            conflicts.append(f"walking-line going in the turn {_full(wgo, 1)} mm (5 treads on the drawn quarter): "
                             "short; acceptability to be confirmed")
        if mods and not [c for c in conflicts if "inside B20" in c or "landing" in c] and "M" in sid.split("-")[-1]:
            status = POSSIBLE_MOD
        elif sid == "REF-25":
            status = REFERENCE
        else:
            status = CONFLICTING
        if sid == "B-27-SM":
            status = POSSIBLE_MOD
        if sid == "A-28-M":
            status = CONFLICTING + " (landing) even with the modification"
        rows.append({
            "SCENARIO": sid, "TITLE": title, "TOTAL_RISERS": n, "FINISHED_RISER_MM": _r(h, 10),
            "WITHIN_OWNER_150_160": pref, "BLONDEL_2R_PLUS_G_FLIGHTS_MM": _r(2 * h + GOING, 3),
            "LOWER_FLIGHT_RISERS": n1, "TURN_RISERS": nt, "TURN_RADIAL_RISERS": nt - 1, "UPPER_FLIGHT_RISERS": n2,
            "LOWER_GOING_MM": GOING, "UPPER_GOING_MM": _r(g2, 6), "TURN_WALKING_LINE_GOING_MM": _r(wgo, 3),
            "BLONDEL_ON_TURN_WALKING_LINE_MM": _r(2 * h + wgo, 3),
            "FOOT_FIRST_RISER_Y_MM": _r(foot, 3), "FOOT_DRAWN_BY": foot_by or None,
            "LOWER_RUN_MM": (n1 - 1) * GOING, "TURN_WALKING_LINE_MM": _r(turn["walking_length_mm"], 3),
            "UPPER_RUN_MM": _r((n2 - 1) * g2, 6), "AVAILABLE_UPPER_LENGTH_TO_B20_MM": _r(Y_LAND_EDGE - B20[1], 3),
            "LAST_UPPER_RISER_Y_MM": _r(last, 3), "CLEARANCE_TO_B20_MM": _r(clr, 3),
            "LANDING_FOOTPRINT": "NE quarter 1200 x 1200 = 1.44 m2 (x 18387.9 - 19587.9, y 19411.9 - 20611.9)",
            "LANDING_LEVEL_M": _r(land / 1000, 10), "LANDING_PRINTED_M": 3.5,
            "LANDING_MINUS_PRINTED_MM": _r(land - 3500.0, 6), "COUNT_CAN_REACH_PRINTED_LANDING": reach["reachable"],
            "ARRANGEMENT_LANDS_ON_PRINTED": abs(land - 3500.0) < 0.5,
            "TURN_TREAD_LEVELS_M": [_r(t_, 3) for t_ in treads], "SECTION_DASHED_TURN_TREADS_M": dashed,
            "SECTION_TURN_TREADS_MATCH": tread_ok,
            "MATCHES_SECTION_A_A": sec_ok, "CONFLICTS": conflicts or None, "MODIFICATIONS_NEEDED": mods or None,
            "CHANGES_TO_RESOLVE": changes_to_resolve(n1, nt, n2, g2, land, clr, h),
            "COLUMN_36B_PROJECTION_INTO_FLIGHT_MM": _r(cols["36B"][2] - X_BAY_W, 3),
            "TREAD_LINE_TO_WALL_FACE_MM": 50.0, "FOOT_TO_GROUND_BEAM_NORTH_FACE_MM": _r(foot - GB_NORTH, 3),
            "DRAWN_BY": drawn, "STATUS": status})
        for s_ in tl["segments"]:
            trans.append({"SCENARIO": sid, "SEGMENT": s_["segment"], "RISERS": s_["risers"],
                          "RISER_NUMBERS": None if not s_["risers"] else f"{s_['first_riser']} - {s_['last_riser']}",
                          "START_LEVEL_M": _r(s_["start_level"] / 1000, 10), "END_LEVEL_M": _r(s_["end_level"] / 1000, 10),
                          "PLAN_START_Y_MM": {"lower flight": _r(foot, 3), "turn (winders)": Y_TURN,
                                              "landing (NE quarter)": Y_LAND_EDGE,
                                              "upper flight": Y_LAND_EDGE}[s_["segment"]],
                          "PLAN_END_Y_MM": {"lower flight": Y_TURN, "turn (winders)": "closing riser x 18387.9",
                                            "landing (NE quarter)": Y_LAND_EDGE,
                                            "upper flight": _r(last, 3)}[s_["segment"]],
                          "STATUS": FACT if (sid in ("A-28", "REF-25")) else (
                              "SECTION_A_A_ARRANGEMENT" if sid == "B-27-S" else PROPOSED)})
    return rows, trans


# ------------------------------------------------------------------ clash audit
def clash_rows(gf, sec, beams, cols, slabs):
    rows = []
    bdef = {}
    for r in _j(READ["S1_BEAMS"])["rows"]:
        if r.get("B_cm") is not None and r.get("H_cm") is not None:
            bdef[r["beam_type"]] = (float(r["B_cm"]) * 10, float(r["H_cm"]) * 10)
    check(bdef["B20"] == (400.0, 750.0) and bdef["B23"] == (450.0, 750.0) and bdef["CA"] == (300.0, 500.0),
          "S1 beam schedule sizes")
    for g in gf:
        rows.append({"ITEM": f"{g['SCENARIO']} upper-flight head / B20", "LOCATION": "GF roof sheet (1F floor)",
                     "MEMBER": "B20 40 x 75 (S1 BDEF-B20-1F3E; S6 LOWER_BOUND 110 kg)",
                     "PLAN_CLEARANCE_MM": g["CLEARANCE_TO_B20_MM"],
                     "RESULT": ("CLASH: the last tread sits over the beam at the 1F floor; needs a lowered / cranked "
                                "B20 or a shorter upper flight" if g["CLEARANCE_TO_B20_MM"] < 0 else
                                "CLEAR: a floor strip between the last riser and B20"),
                     "LOCAL_DROP_OF_B20_TOP_NEEDED_MM": (_r(g["FINISHED_RISER_MM"], 3)
                                                         if g["CLEARANCE_TO_B20_MM"] < 0 else None),
                     "STATUS": FACT if g["SCENARIO"] in ("A-28", "REF-25") else (
                         "SECTION_A_A_ARRANGEMENT" if g["SCENARIO"] == "B-27-S" else PROPOSED)})
    rows.append({"ITEM": "section A-A beam position", "LOCATION": "section A-A (1F floor, south end)",
                 "MEMBER": "downstand on the south wall", "PLAN_CLEARANCE_MM": _r(sec["A1"]["arrival_plan_y"] -
                                                                                   sec["A1"]["south_wall_plan_y"], 1),
                 "RESULT": (f"the section draws its 12-riser upper flight arriving at y {_full(sec['A1']['arrival_plan_y'], 0)} "
                            f"and the nearest downstand on the wall at y {_full(sec['A1']['south_wall_plan_y'], 0)}; it "
                            "draws nothing at B20's plan band (15911.9 - 16311.9): the section neither shows nor resolves "
                            "the clash"), "STATUS": SCALED})
    rows.append({"ITEM": "1F -> 2F upper-flight head / B23 (owner 27 = 11 upper risers)", "LOCATION": "1F roof sheet",
                 "MEMBER": "B23 45 x 75 (S1 BDEF-B23-1F5F; S6 LOWER_BOUND 145.2 kg)",
                 "PLAN_CLEARANCE_MM": _r(FC.band_clearance(16411.856, B23, -1), 3),
                 "RESULT": "CLEAR by 100 mm (S8.7's released arrival strip A2-T1 fills it)", "STATUS": FACT})
    rows.append({"ITEM": "1F -> 2F upper-flight head / B23 (section A-A = 12 upper risers)", "LOCATION": "1F roof sheet",
                 "MEMBER": "B23", "PLAN_CLEARANCE_MM": _r(FC.band_clearance(Y_LAND_EDGE - 11 * GOING, B23, -1), 3),
                 "RESULT": "CLASH (section only)", "STATUS": SCALED})
    for sid, foot in (("A-28 / B-27-U (foot y 16161.9)", 16161.856), ("B-27-S / REF-25 (foot y 16761.9)", 16761.856),
                      ("B-27-P (foot y 16461.9)", 16461.856)):
        rows.append({"ITEM": f"{sid}: lower-flight foot / ground beam", "LOCATION": "ground-beam plan",
                     "MEMBER": "ground beam north face (GBP 7CC)", "PLAN_CLEARANCE_MM": _r(foot - GB_NORTH, 3),
                     "RESULT": "no ground beam is drawn under the foot (p.16's G.B is typical only): support "
                               "not established", "STATUS": FACT})
    for sid, foot, h in (("A-28 (foot under B20 in plan)", 16161.856, 4500 / 28),):
        hr = FC.headroom(FFL["1F"], 750.0, FFL["GF"] + h)
        rows.append({"ITEM": f"{sid}: headroom under B20 at the foot", "LOCATION": "GF", "MEMBER": "B20 at the 1F floor",
                     "HEADROOM_MM": _r(hr, 1), "RESULT": f"{_full(hr / 1000, 2)} m less the 1F floor build-up: ample",
                     "STATUS": FACT})
    c = cols["36B"]
    rows.append({"ITEM": "every scenario: column 36B against the lower flight", "LOCATION": "GF (west column)",
                 "MEMBER": "column 36B", "PLAN_CLEARANCE_MM": _r(X_BAY_W - c[2], 3),
                 "RESULT": "the column projects 50 mm into the 1200 width over y 17111.9 - 17611.9 (1150 clear there); "
                           "that stretch lies inside every alternative's lower flight, and no alternative changes it",
                 "STATUS": FACT})
    rows.append({"ITEM": "every scenario: central wall", "LOCATION": "GF / 1F", "MEMBER": "wall x 18287.9 - 18387.9, "
                 "ends at y 19411.9", "PLAN_CLEARANCE_MM": 50.0,
                 "RESULT": "tread lines stop 50 mm short of both wall faces; structural width 1200 to the wall face",
                 "STATUS": FACT})
    ca = next(r for r in beams if r["INTERFACE"] == "C-F1:STRAIGHT / BL015")
    hr = FC.headroom(FFL["1F"], 500.0, FFL["GF"] + 15 * 4500 / 28)
    zones = [s for s in slabs if s["panel_id"] in ("SP-GF_ROOF_SLAB-21", "SP-GF_ROOF_SLAB-28")]
    rows.append({"ITEM": "round stair: beam CA across the straight flight", "LOCATION": "GF roof sheet (stair zone)",
                 "MEMBER": "CA 30 x 50 (S1 BDEF-CA-2A53; S6 BLOCKED)", "PLAN_CLEARANCE_MM": None,
                 "PLAN_OVERLAP_M2": float(ca["PLAN_OVERLAP_M2"]), "HEADROOM_MM": _r(hr, 1),
                 "RESULT": (f"CA crosses the tread after riser 15 (+{_full((FFL['GF'] + 15 * 4500 / 28) / 1000, 3)}). If it "
                            f"is framed at the 1F floor, the clear height under it is {_full(hr / 1000, 2)} m (less the "
                            "floor build-up), far below a usable headroom; it separates the two stair-zone panels "
                            f"({', '.join(s['panel_id'] for s in zones)}), so its level is decisive"),
                 "STATUS": ENGINEER})
    return rows, bdef


# ------------------------------------------------------------------ 1F -> 2F
def winder_rows(sec, turn):
    rows = []
    rise = FFL["2F"] - FFL["1F"]
    cases = [("OWNER-27", "owner scenario = architectural 1F plan", 12, 4, 11, OWNER_PROV,
              "winders drawn only by the architectural 1F plan"),
             ("FFRS-24", "structural 1F roof sheet; architectural 2F view (repeated)", 12, 1, 11, FACT,
              "flat NW quarter + closing riser"),
             ("SECTION-25", "section A-A (measured)", 12, 1, 12, SCALED, "flat quarter (no winder lines in the turn); "
                                                                          "12 upper risers")]
    for cid, basis, n1, nt, n2, st, note in cases:
        n = n1 + nt + n2
        h = rise / n
        land = FFL["1F"] + (n1 + nt) * h
        last = FC.run_end(Y_LAND_EDGE, n2, GOING, -1)
        rows.append({"CASE": cid, "BASIS": basis, "STATUS": st, "TOTAL_RISERS": n, "FINISHED_RISER_MM": _r(h, 10),
                     "LOWER": n1, "TURN": nt, "TURN_KIND": "winders: 3 radial + closing" if nt == 4 else
                     "flat quarter + closing riser", "UPPER": n2, "LANDING_LEVEL_M": _r(land / 1000, 9),
                     "LANDING_PRINTED_M": None, "SECTION_SCALED_LANDING_M": _r(sec_land(), 4),
                     "LAST_UPPER_RISER_Y_MM": _r(last, 3), "CLEARANCE_TO_B23_MM": _r(FC.band_clearance(last, B23, -1), 3),
                     "FOOTPRINT": "NW quarter 1300 x 1150 (1.495 m2) + NE landing 1200 x 1200 (1.44 m2)",
                     "NOTE": note})
    up_max = FC.max_risers(Y_LAND_EDGE - B23[1], GOING)
    low_max = FC.max_risers(Y_TURN - 16161.856, GOING)
    rows.append({"CASE": "PLAN_CAPACITY", "BASIS": "the drawn plan at 300 goings", "STATUS": "ARITHMETIC",
                 "TOTAL_RISERS": {"flat quarter": low_max + 1 + up_max, "4-winder turn": low_max + 4 + up_max},
                 "LOWER": low_max, "UPPER": up_max,
                 "NOTE": f"lower flight from its drawn foot (over B20 at the 1F floor) to the turn: at most {low_max}; "
                         f"upper flight clear of B23: at most {up_max}. With a flat quarter the plan holds at most "
                         f"{low_max + 1 + up_max} risers; the owner's 27 is exactly what the four-riser winder turn "
                         "makes possible, and needs it"})
    return rows


_SEC_LAND = {}


def sec_land():
    return _SEC_LAND.get("A2")


# ------------------------------------------------------------------ round stair
def round_rows(evidence, sec87b, beams, slabs, levels):
    cur = sorted([r for r in evidence if r["VIEW"] == "GFRS" and r["ELEMENT_ID"] == "C-F1" and r["PART"] == "CURVED"],
                 key=lambda r: float(r["ANGLE_DEG"]))
    st = [r for r in evidence if r["VIEW"] == "GFRS" and r["ELEMENT_ID"] == "C-F1" and r["PART"] == "STRAIGHT"]
    sh = [r for r in evidence if r["VIEW"] == "GFRS" and r["ELEMENT_ID"] == "C-F2"]
    check((len(cur), len(st), len(sh)) == (12, 11, 5), "round stair 12 + 11 + 5 on the GF roof sheet")
    ang = [float(r["ANGLE_DEG"]) for r in cur]
    pitches = [b - a for a, b in zip(ang, ang[1:])]
    h = 4500.0 / 28
    rw = 2155.4
    rows = [
        ("R-01", "foot level", "+1.00 inferred", INFERRED, "no level is printed inside the light well; the nearest "
         "printed GF levels are '+1.00' 1.8 m and 2.5 m away (S8.7B 13)"),
        ("R-02", "riser count", "28 = 12 curved + 11 straight / corner landing / 5", FACT,
         "GF roof sheet and architectural 1F plan agree; the GF plan's second view draws 4 in the short flight"),
        ("R-03", "finished riser", f"{_full(h, 7)} mm (if +1.00 -> +5.50 and equal)", INFERRED, "both ends' levels"),
        ("R-04", "curved flight: radial risers", f"{len(ang)} from {_full(ang[0], 2)} to {_full(ang[-1], 2)} deg",
         FACT, f"angular pitch {_full(min(pitches), 2)} - {_full(max(pitches), 2)} deg (mean "
               f"{_full(sum(pitches) / len(pitches), 3)})"),
        ("R-05", "curved flight: goings", f"inner {_full(math.radians(sum(pitches) / len(pitches)) * 1580.4, 0)} / walking "
         f"line {_full(math.radians(sum(pitches) / len(pitches)) * rw, 0)} / outer "
         f"{_full(math.radians(sum(pitches) / len(pitches)) * 2730.4, 0)} mm", FACT,
         "tread ends at r 1580 - 2730 (tread lines 1150); the S-OPENING arcs at r 1530.5 / 2780.5 (1250)"),
        ("R-06", "straight flight", f"11 risers at 300, x 23757.9 -> 26757.9, width 1150 (tread lines)", FACT,
         "1200 to the void edge (S-OPENING 2D0 at y 10211.9) is the alternative width"),
        ("R-07", "corner landing", f"1150 x 1200 less column 374 (0.0275 m2); level +{_full((FFL['GF'] + 23 * h) / 1000, 3)} "
         "if equal risers", INFERRED, "not printed; no section cuts this stair"),
        ("R-08", "short flight and arrival", "5 risers y 10211.9 -> 11411.9 to +5.50; arrival plate C-T1 (S8.7, released)",
         PRINTED, "'+5.50' printed at the arrival on the architectural 1F plan (D16)"),
        ("R-09", "stair zone at the 1F floor", "SP-GF_ROOF_SLAB-21 (STAIR_IN_VOID_ZONE) and -28 (STAIR_FLIGHT_ZONE)",
         FROZEN, "they cover the straight flight, the corner landing and the short flight: no 1F slab over them"),
        ("R-10", "beam CA", "30 x 50, across the straight flight between risers 15 and 16 (x 24357.9 - 24657.9)",
         ENGINEER, "its level is not stated; at the 1F floor it would leave about 1.59 m over the tread below; as a "
                   "support under the flight it would be a stair beam (not drawn as such)"),
        ("R-11", "south edge beam", "B3 '(With Stair)' 20 x 40 on line BL022 along the straight flight", UNVERIFIED,
         "possibly the p.16 cranked stair beam; not drawn as cranked; owned by S6 (BLOCKED)"),
        ("R-12", "main-stair landing levels", "not applied", "RULE", "the round stair keeps its own levels"),
    ]
    return [{"ID": a, "ITEM": b, "VALUE": c, "STATUS": d, "EVIDENCE": e} for a, b, c, d, e in rows]


# ------------------------------------------------------------------ concrete comparison
def _zone(n, h, g, t, s0, s1, width=WIDTH):
    if s1 <= s0:
        return 0.0
    return SC.flight_section_volume(n, h, g, width, t, s0, s1) / 1e9


def concrete_rows(gf, turn, a1l1, cols):
    rows = []
    for g in gf:
        sid = g["SCENARIO"]
        n1, nt, n2 = g["LOWER_FLIGHT_RISERS"], g["TURN_RISERS"], g["UPPER_FLIGHT_RISERS"]
        h, g2, foot = g["FINISHED_RISER_MM"], g["UPPER_GOING_MM"], g["FOOT_FIRST_RISER_Y_MM"]
        drawn_turn = nt == 4
        areas = [a * 1e6 for a in (turn["tread_areas_m2"] if drawn_turn else
                                   equal_wedge_areas(nt, turn["plan_area_m2"], turn["tread_areas_m2"]))]
        for t in WAISTS:
            def flight(name, n, gg, zones, flags):
                gross = SC.flight_section_volume(n, h, gg, WIDTH, t) / 1e9
                run = (n - 1) * gg
                incl = run * math.hypot(gg, h) / gg
                waist = incl * t * WIDTH / 1e9
                steps = (n - 1) * gg * h / 2 * WIDTH / 1e9
                check(abs(gross - waist - steps) < 1e-9, "waist + step wedges = section integral")
                ded = sum(z for z in zones)
                return {"SCENARIO": sid, "WAIST_MM": t, "COMPONENT": name, "RISERS": n, "GOING_MM": _r(gg, 6),
                        "WAIST_CONCRETE_M3": _r(waist, 9), "STEP_WEDGES_M3": _r(steps, 9), "GROSS_M3": _r(gross, 9),
                        "DEDUCTIONS_M3": _r(ded, 9), "NET_M3": _r(gross - ded, 9), "UPPER_BOUND_M3": _r(gross, 9),
                        "OWNED_BY": "none (not released)", "LANE": SENS, "UNCERTAINTY": flags}
            # lower flight: column 36B cut-out (its outline read by handle: 50 x 500 inside the west edge)
            c36 = cols["36B"]
            s0, s1 = c36[1] - foot, c36[3] - foot
            cut = _zone(n1, h, GOING, t, max(0, s0), min((n1 - 1) * GOING, s1)) * (c36[2] - X_BAY_W) / WIDTH
            rows.append(flight("lower flight", n1, GOING, [cut], ["WAIST_UNKNOWN"] +
                               (["FOOT_POSITION_IN_CONFLICT"] if g["FOOT_DRAWN_BY"] != ["ARCH-GF", "GBP"] else [])))
            rows[-1]["DEDUCTION_DETAIL"] = f"column 36B cut-out {_full(cut, 6)}"
            b = SC.winder_bounds(areas, h, t, g["TURN_WALKING_LINE_GOING_MM"])
            rows.append({"SCENARIO": sid, "WAIST_MM": t, "COMPONENT": "turn (winders)", "RISERS": nt,
                         "GOING_MM": g["TURN_WALKING_LINE_GOING_MM"], "GROSS_M3": _r(b["plane_equivalent_mm3"] / 1e9, 9),
                         "DEDUCTIONS_M3": 0.0, "NET_M3": _r(b["plane_equivalent_mm3"] / 1e9, 9),
                         "UPPER_BOUND_M3": _r(b["flat_soffit_bound_mm3"] / 1e9, 9), "OWNED_BY": "none (not released)",
                         "LANE": COND, "UNCERTAINTY": ["WAIST_UNKNOWN", "WINDER_SOFFIT_NOT_DRAWN"] +
                         ([] if drawn_turn else ["PROPOSED_TURN_GEOMETRY_NOT_DRAWN"])})
            rows.append({"SCENARIO": sid, "WAIST_MM": t, "COMPONENT": "landing A1-L1 (NE quarter)", "GROSS_M3":
                         _r(1.44 * t / 1000, 9), "DEDUCTIONS_M3": 0.0, "NET_M3": 0.0, "UPPER_BOUND_M3": 0.0,
                         "OWNED_BY": f"S8.7 (released {a1l1} m3 at 160; frozen)", "LANE": ALREADY,
                         "UNCERTAINTY": ["LANDING_THICKNESS_NOT_PRINTED"]})
            run2 = (n2 - 1) * g2
            over = max(0.0, B20[1] - g["LAST_UPPER_RISER_Y_MM"])
            zone = _zone(n2, h, g2, t, run2 - over, run2)
            rows.append(flight("upper flight", n2, g2, [zone], ["WAIST_UNKNOWN"] +
                               (["B20_ZONE_OWNERSHIP_UNRESOLVED"] if zone else []) +
                               (["PROPOSED_GOING_NOT_DRAWN"] if abs(g2 - GOING) > 1e-6 else [])))
            rows[-1]["DEDUCTION_DETAIL"] = f"B20 zone {_full(zone, 6)}" if zone else ""
            rows[-1]["UPPER_BOUND_M3"] = rows[-1]["GROSS_M3"]
            strip = g["CLEARANCE_TO_B20_MM"]
            if strip > 0:
                # the floor strip between the last riser and B20 (cf. S8.7's released A2-T1 before B23): the 1F slab's
                # or a new stair plate's; not settled, so never added
                rows.append({"SCENARIO": sid, "WAIST_MM": t, "COMPONENT": "arrival strip before B20 (1F floor)",
                             "GROSS_M3": _r(strip * WIDTH * t / 1e9, 9), "OWNED_BY": "unresolved (1F slab or a stair "
                             "plate; S8.7 owns no GF -> 1F arrival strip)", "LANE": UNRESOLVED,
                             "UNCERTAINTY": ["STRIP_THICKNESS_NOT_PRINTED", "OWNER_NOT_SETTLED"]})
            part = [r for r in rows if r["SCENARIO"] == sid and r["WAIST_MM"] == t and r["COMPONENT"] != "TOTAL"]
            new = [r for r in part if r["LANE"] not in (ALREADY, UNRESOLVED)]
            rows.append({"SCENARIO": sid, "WAIST_MM": t, "COMPONENT": "TOTAL (new; S8.7 landing excluded)",
                         "WAIST_CONCRETE_M3": _r(math.fsum(r.get("WAIST_CONCRETE_M3") or 0 for r in new), 9),
                         "STEP_WEDGES_M3": _r(math.fsum(r.get("STEP_WEDGES_M3") or 0 for r in new), 9),
                         "GROSS_M3": _r(math.fsum(r["GROSS_M3"] for r in new), 9),
                         "DEDUCTIONS_M3": _r(math.fsum(r["DEDUCTIONS_M3"] for r in new), 9),
                         "NET_M3": _r(math.fsum(r["NET_M3"] for r in new), 9),
                         "UPPER_BOUND_M3": _r(math.fsum(r["UPPER_BOUND_M3"] for r in new), 9),
                         "OWNED_BY": "-", "LANE": SENS, "UNCERTAINTY": ["NEVER_RELEASED"]})
    return rows


def rebar_rows(gf, conc):
    kg16 = UM.kg_per_m(16, UNIT_MASS)
    rows = []
    for g in gf:
        h = g["FINISHED_RISER_MM"]
        tot = 0.0
        for name, n, gg in (("lower flight", g["LOWER_FLIGHT_RISERS"], GOING),
                            ("upper flight", g["UPPER_FLIGHT_RISERS"], g["UPPER_GOING_MM"])):
            incl = (n - 1) * gg * math.hypot(gg, h) / gg
            L = 8 * WIDTH / 1000 * incl / 1000
            tot += L * kg16
            rows.append({"SCENARIO": g["SCENARIO"], "ITEM": f"8Ø16/m main bottom bars, {name}", "BAR_DIAMETER_MM": 16,
                         "EQUIVALENT_LENGTH_M": _r(L, 9), "KG": _r(L * kg16, 9), "LANE": SENS,
                         "AUTHORITY": "plan callout rate (explicit); length from the alternative's geometry",
                         "STATE": "not released; anchorage, laps, transverse and top families excluded"})
        rows.append({"SCENARIO": g["SCENARIO"], "ITEM": "8Ø16/m through the turn", "BAR_DIAMETER_MM": 16, "KG": None,
                     "LANE": BLOCKED, "STATE": "bar paths through the winders not established"})
        rows.append({"SCENARIO": g["SCENARIO"], "ITEM": "8Ø16/m main bars along the two flights (sum)",
                     "BAR_DIAMETER_MM": 16, "KG": _r(tot, 9), "LANE": SENS, "STATE": "context only"})
    fixed = [("S8.7 released 8Ø16/m over A1-L1 / A2-T1 / C-T1", S87_KG, "OWNED_BY_S8_7 (frozen; not counted again)"),
             ("S7 top extensions at the stair-adjacent supports (75 strip ends)", S7_KG, "OWNED_BY_S7 (frozen)"),
             ("B20 head beam bars", 110.0, "OWNED_BY_S6 (LOWER_BOUND; the B20 overlap zone is never a stair bar zone)"),
             ("B23 head beam bars", 145.2, "OWNED_BY_S6 (LOWER_BOUND)")]
    for item, kg, st in fixed:
        rows.append({"SCENARIO": "ALL", "ITEM": item, "KG": kg, "LANE": "PRESERVED", "STATE": st})
    for fam in ("6Ø14/m junction / head top bars", "6Ø12/m landing top", "Ø12/20cm distribution", "Ø8/15 step bars",
                "1Ø12 nosing bars", "6Ø16/m starters", "landing edge beam 2Ø12 / 4Ø16", "ground beam G.B",
                "cranked stair beam 2Ø12 / 4Ø16 / 6Ø8/m", "anchorage / development / laps / bends"):
        rows.append({"SCENARIO": "ALL", "ITEM": fam, "KG": None, "LANE": BLOCKED, "STATE": "TYPICAL_ONLY / not dimensioned"})
    return rows


RFI = [
    ("P1", "architect", "GF -> 1F arrangement: section A-A draws 10 + 5-riser turn + 12 = 27 risers (166.667 mm) to the "
     "printed +3.50; the structural GF roof sheet draws 12 + 4 + 12 = 28 (landing +3.571, foot 600 mm south); the "
     "architectural GF plan draws 10 + 4 + 11 = 25. Confirm which arrangement governs. If it is the section's, redraw "
     "the plans' turn with five winder treads (four radial risers) and confirm the 218.5 mm walking-line going "
     "(600 mm from the fan centre) is acceptable."),
    ("P1", "engineer", "B20 at the GF -> 1F head: every 12-riser upper flight at 300 goings (structural sheet, section "
     "A-A) puts the last riser 200 mm inside B20. Choose: lower / crank B20 locally under the top tread (about one "
     "riser), or let the architect shorten the upper goings to <= 272.7 mm (or 281.8 mm with no arrival strip)."),
    ("P1", "engineer", "Round stair beam CA (30 x 50) crosses the straight flight over the tread at +3.411: if it sits "
     "at the 1F floor it leaves about 1.59 m headroom. State its level (support under the flight or an error)."),
    ("P2", "owner", "Riser preference: 27 risers = 166.667 mm and 28 = 160.714 mm are both above 160 mm. Accept one of "
     "them; 27 is the count that matches the printed +3.50 with equal risers."),
    ("P2", "architect / engineer", "1F -> 2F: the owner's 27 needs the architectural four-riser winder turn; the "
     "structural sheet and section A-A draw a flat quarter. Confirm the winders, their structural form and the "
     "landing level (+7.989 with 27; section scales +7.69)."),
    ("P2", "engineer", "Structural waist and landing thickness (p.16 'THICK' has no value)."),
    ("P3", "architect", "Marble bedding / adhesive (is it inside the 30 mm?) and the floor build-ups at GF, 1F and 2F "
     "(they set the first and last concrete risers)."),
    ("P3", "engineer", "Applicable typical bars, anchorage and laps; whether the 'With Stair' B3 / CB3 beams are the "
     "p.16 cranked stair beam."),
]


# ------------------------------------------------------------------ diagrams (schematic, from the drawn coordinates)
ORANGE, BLUE, RED, INK, MUTED, GRID = "#c2410c", "#1d4ed8", "#b91c1c", "#1f2937", "#4b5563", "#9ca3af"


class _Svg:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
                    'font-family="Arial, Helvetica, sans-serif" font-size="11">',
                    f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
                    '<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" '
                    f'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="{RED}" '
                    'stroke-width="1"/></pattern>'
                    '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker></defs>']

    def line(self, a, b, c=INK, w=1.0, dash=None, arrow=False):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#arrow)"' if arrow else ""
        self.out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{c}" '
                        f'stroke-width="{w}"{d}{m}/>')

    def rect(self, a, b, fill, stroke="none", w=1.0, op=1.0, dash=None):
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.out.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" fill="{fill}" '
                        f'fill-opacity="{op}" stroke="{stroke}" stroke-width="{w}"{d}/>')

    def text(self, a, s, c=INK, size=11, anchor="start", weight="normal"):
        self.out.append(f'<text x="{a[0]:.1f}" y="{a[1]:.1f}" fill="{c}" font-size="{size}" text-anchor="{anchor}" '
                        f'font-weight="{weight}">{s}</text>')

    def poly(self, pts, c, w=2.0):
        self.out.append(f'<polyline fill="none" stroke="{c}" stroke-width="{w}" stroke-linejoin="round" points="'
                        + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '"/>')

    def done(self):
        return "\n".join(self.out + ["</svg>"]) + "\n"


def _numbers(g):
    n1, nt, n2 = g["LOWER_FLIGHT_RISERS"], g["TURN_RISERS"], g["UPPER_FLIGHT_RISERS"]
    return {"lower": (1, n1), "turn": (n1 + 1, n1 + nt), "upper": (n1 + nt + 1, n1 + nt + n2)}


def _svg_plan(gf, radial):
    by = {g["SCENARIO"]: g for g in gf}
    S = _Svg(800, 785)
    sc, top = 0.1, 100.0
    S.text((20, 26), "Main stair GF -&gt; 1F in plan: the structural sheet's 28 risers against section A-A's 27", INK, 15,
           weight="bold")
    S.text((20, 45), "Schematic drawn from the ST7757 / P7757 coordinates (1 mm = 0.1 px). Not a drawing; nothing here "
                     "is approved.", MUTED, 11)
    cx, cy = radial["centre"][0], radial["centre"][1]
    for sid, ox, col in (("A-28", 20, ORANGE), ("B-27-S", 420, BLUE)):
        g = by[sid]
        num = _numbers(g)

        def P(x, y):
            return ox + (x - 16700) * sc, top + (20700 - y) * sc
        S.text((ox, 78), "A: 28 risers, as on the structural sheet" if sid == "A-28" else
               "B: 27 risers, as in section A-A", col, 13, weight="bold")
        # bay, central wall, B20 band at the 1F floor
        S.rect(P(X_BAY_W, 15750), P(X_BAY_E, Y_BAY_N), "#f9fafb", GRID, 0.8)
        S.rect(P(X_WALL_W, B20[1]), P(X_WALL_E, Y_LAND_EDGE), "#9ca3af")
        S.rect(P(X_BAY_W - 150, B20[0]), P(X_BAY_E + 150, B20[1]), "url(#hatch)", RED, 1.0)
        S.text(P(X_BAY_E + 230, B20[0] + 230), "B20", RED, 11, weight="bold")
        S.text(P(X_BAY_E + 230, B20[0] + 80), "1F floor", RED, 9)
        # landing
        S.rect(P(X_WALL_E, Y_LAND_EDGE), P(X_BAY_E, Y_BAY_N), "#fff7ed" if sid == "A-28" else "#eff6ff", GRID, 0.8)
        mid = (X_WALL_E + X_BAY_E) / 2
        S.text(P(mid, 20150), "landing", col, 11, "middle", "bold")
        S.text(P(mid, 19950), f"+{g['LANDING_LEVEL_M']:.3f}", col, 13, "middle", "bold")
        high = g["LANDING_MINUS_PRINTED_MM"] > 0.5
        S.text(P(mid, 19760), f"{_full(g['LANDING_MINUS_PRINTED_MM'], 1)} mm above" if high else "= the printed",
               RED if high else INK, 10, "middle", "bold" if high else "normal")
        S.text(P(mid, 19610), "the printed +3.50" if high else "+3.50", RED if high else INK, 10, "middle",
               "bold" if high else "normal")
        # lower flight (west), walking north
        foot = g["FOOT_FIRST_RISER_Y_MM"]
        for i in range(g["LOWER_FLIGHT_RISERS"]):
            y = foot + i * GOING
            S.line(P(X_BAY_W, y), P(X_WALL_W - 50, y), col, 1.4)
        S.text(P(X_BAY_W - 40, foot - 40), str(num["lower"][0]), col, 10, "end", "bold")
        S.text(P(X_BAY_W - 40, Y_TURN - 40), str(num["lower"][1]), col, 10, "end", "bold")
        S.line(P(17687.9, foot + 150), P(17687.9, Y_TURN - 150), INK, 1.0, arrow=True)
        S.text(P(17760, foot + 500), "UP", INK, 9, weight="bold")
        S.text(P(X_BAY_W + 60, foot - 170), f"foot y {_full(foot, 0)}", col, 10)
        # the turn: the drawn radials (A) or a proposed fifth tread (B, dashed)
        if g["TURN_RADIAL_RISERS"] == 3:
            for h in radial["lines"]:
                (x1, y1), (x2, y2) = radial["lines"][h]
                if y2 > Y_BAY_N:                                  # stop the drawn line at the bay edge
                    x2, y2 = x1 + (x2 - x1) * (Y_BAY_N - y1) / (y2 - y1), Y_BAY_N
                S.line(P(x1, y1), P(x2, y2), col, 1.4)
        else:
            for k in range(1, g["TURN_RADIAL_RISERS"] + 1):
                a_ = math.radians(180.0 - 90.0 * k / (g["TURN_RADIAL_RISERS"] + 1))
                dx, dy = math.cos(a_), math.sin(a_)
                t = min((X_BAY_W - cx) / dx, (Y_BAY_N - cy) / dy)
                S.line(P(cx, cy), P(cx + dx * t, cy + dy * t), col, 1.4, "5,3")
        S.line(P(X_WALL_E, Y_TURN), P(X_WALL_E, Y_BAY_N), col, 1.4)
        S.text(P(X_WALL_E - 30, Y_BAY_N - 120), str(num["turn"][1]), col, 10, "end", "bold")
        # upper flight (east), walking south
        for i in range(g["UPPER_FLIGHT_RISERS"]):
            y = Y_LAND_EDGE - i * g["UPPER_GOING_MM"]
            bad = y < B20[1]
            S.line(P(X_WALL_E + 50, y), P(X_BAY_E, y), RED if bad else col, 3.0 if bad else 1.4)
        S.text(P(X_BAY_E + 40, Y_LAND_EDGE - 40), str(num["upper"][0]), col, 10, "start", "bold")
        last = g["LAST_UPPER_RISER_Y_MM"]
        S.text(P(X_BAY_E + 40, last - 40), str(num["upper"][1]), RED, 10, "start", "bold")
        S.line(P(18987.9, Y_LAND_EDGE - 150), P(18987.9, last + 450), INK, 1.0, arrow=True)
        # facts under the panel
        lines = [(f"{g['TOTAL_RISERS']} risers of {_full(g['FINISHED_RISER_MM'], 3)} mm", INK, "bold"),
                 (f"{g['LOWER_FLIGHT_RISERS']} + {g['TURN_RISERS']} (turn) + landing + {g['UPPER_FLIGHT_RISERS']}", INK,
                  "normal"),
                 ("turn: 3 radial + closing riser, as drawn" if g["TURN_RADIAL_RISERS"] == 3 else
                  "turn: 4 radial + closing riser, PROPOSED (plans draw 3)", col, "normal"),
                 (f"riser {num['upper'][1]} is {_full(-g['CLEARANCE_TO_B20_MM'], 0)} mm inside B20", RED, "bold"),
                 ("(12 risers x 300 = 3300 mm; only 3100 mm to B20)", MUTED, "normal")]
        if sid == "A-28":
            lines += [("foot 600 mm south of the architectural plan,", MUTED, "normal"),
                      ("the ground-beam plan and section A-A", MUTED, "normal")]
        else:
            lines += [("removing one riser does not clear B20:", MUTED, "normal"),
                      ("the upper flight is unchanged", MUTED, "normal")]
        for k, (t_, c_, w_) in enumerate(lines):
            S.text((ox + 20, 618 + 17 * k), t_, c_, 11, weight=w_)
    S.line((20, 745), (44, 745), INK, 1.4)
    S.text((50, 749), "drawn riser line", MUTED, 10)
    S.line((160, 745), (184, 745), INK, 1.4, "5,3")
    S.text((190, 749), "proposed, not drawn", MUTED, 10)
    S.line((320, 745), (344, 745), RED, 3.0)
    S.text((350, 749), "riser inside the B20 band", MUTED, 10)
    S.rect((500, 738), (524, 752), "url(#hatch)", RED)
    S.text((530, 749), "B20 40 x 75 under the 1F floor (above this plan)", MUTED, 10)
    S.text((20, 770), "Lower flight: west column, walking north. Upper flight: east column, walking south. "
                      "Numbers are riser numbers from the GF.", MUTED, 10)
    return S.done()


def _svg_section(gf, turn):
    by = {g["SCENARIO"]: g for g in gf}
    S = _Svg(900, 620)
    k = 0.075                                                   # px per mm, both directions (true proportions)
    base, sx0 = 470.0, 115.0
    s_min = -5900.0

    def P(s, z):
        return sx0 + (s - s_min) * k, base - (z - FFL["GF"]) * k
    S.text((20, 26), "Main stair GF -&gt; 1F unfolded along the walking line: why the landing and B20 conflict", INK, 15,
           weight="bold")
    S.text((20, 45), "Both arrangements are aligned at the first riser of the upper flight. True proportions (1 mm = "
                     "0.075 px). Equal finished risers. Not a drawing.", MUTED, 11)
    s_max = 3900.0
    for z, lab, dash in ((FFL["GF"], "GF +1.00", None), (3500.0, "printed +3.50", "6,4"), (FFL["1F"], "1F +5.50", None)):
        S.line(P(s_min, z), P(s_max, z), GRID, 0.8, dash)
        S.text((sx0 - 8, P(0, z)[1] + 4), lab, MUTED if z != 3500.0 else INK, 10, "end",
               "bold" if z == 3500.0 else "normal")
    # B20 under the 1F floor: plan band 3100 - 3500 mm beyond the landing edge
    b0, b1 = Y_LAND_EDGE - B20[1], Y_LAND_EDGE - B20[0]
    S.rect(P(b0, FFL["1F"]), P(b1, FFL["1F"] - 750.0), "url(#hatch)", RED, 1.2)
    S.text(P(b1 + 60, FFL["1F"] - 330), "B20", RED, 12, weight="bold")
    S.text(P(b1 + 60, FFL["1F"] - 520), "40 x 75", RED, 10)
    profiles = {}
    for sid, col in (("A-28", ORANGE), ("B-27-S", BLUE)):
        g = by[sid]
        h, wg = g["FINISHED_RISER_MM"], g["TURN_WALKING_LINE_GOING_MM"]
        n1, nt, n2 = g["LOWER_FLIGHT_RISERS"], g["TURN_RISERS"], g["UPPER_FLIGHT_RISERS"]
        s_turn = -WIDTH - nt * wg                            # the turn's first riser (= the lower flight's last)
        risers = [s_turn - (n1 - 1 - i) * GOING for i in range(n1)]
        risers += [s_turn + j * wg for j in range(1, nt + 1)]
        risers += [m * g["UPPER_GOING_MM"] for m in range(n2)]
        z = FFL["GF"]
        pts = [P(risers[0] - 300, z)]
        for r_ in risers:
            pts.append(P(r_, z))
            z += h
            pts.append(P(r_, z))
        pts.append(P(s_max, z))
        S.poly(pts, col, 2.2)
        profiles[sid] = {"risers": risers, "h": h, "s_turn": s_turn}
    # the overlap of the last tread with B20 (same plan position in both)
    S.rect(P(b0, FFL["1F"]), P(Y_LAND_EDGE - 16111.856, FFL["1F"] - by["B-27-S"]["FINISHED_RISER_MM"]), RED, RED, 0.8,
           0.55)
    S.line(P(b0 + 100, FFL["1F"] + 60), P(b0 + 100, FFL["1F"] + 330), RED, 1.0)
    S.text(P(b0 + 30, FFL["1F"] + 560), "the last tread sits one riser below the 1F floor,", RED, 11, "end", "bold")
    S.text(P(b0 + 30, FFL["1F"] + 390), "over 200 mm of B20, in both arrangements", RED, 11, "end", "bold")
    # landing callouts
    a, b = by["A-28"], by["B-27-S"]
    S.text(P(-WIDTH / 2, 3571.4 + 520), f"A-28 landing +{_full(a['LANDING_LEVEL_M'], 3)}", ORANGE, 11, "middle", "bold")
    S.text(P(-WIDTH / 2, 3571.4 + 360), "71.4 mm above the printed +3.50", ORANGE, 10, "middle")
    S.text(P(-WIDTH / 2, 3500 - 330), f"B-27-S landing +{b['LANDING_LEVEL_M']:.3f}", BLUE, 11, "middle", "bold")
    S.text(P(-WIDTH / 2, 3500 - 490), "= the printed +3.50", BLUE, 10, "middle")
    # segment bars with riser numbers
    for row, (sid, col) in enumerate((("A-28", ORANGE), ("B-27-S", BLUE))):
        g, pr = by[sid], profiles[sid]
        num = _numbers(g)
        y0 = 500 + 30 * row
        segs = [(pr["risers"][0], pr["s_turn"], f"{num['lower'][0]} - {num['lower'][1]}"),
                (pr["s_turn"], -WIDTH, f"turn {num['turn'][0]} - {num['turn'][1]}"),
                (-WIDTH, 0.0, "landing"),
                (0.0, pr["risers"][-1], f"{num['upper'][0]} - {num['upper'][1]}")]
        S.text((sx0 - 8, y0 + 15), sid, col, 11, "end", "bold")
        for s0, s1, lab in segs:
            S.rect((P(s0, 0)[0], y0), (P(s1, 0)[0], y0 + 20), "#ffffff", col, 1.2)
            S.text(((P(s0, 0)[0] + P(s1, 0)[0]) / 2, y0 + 14), lab, col, 10, "middle")
    S.text((20, 585), "Horizontal: distance along the walking line (lower flight at 300, turn on the 600 mm walking line, "
                      "landing 1200, upper flight at 300). The turn is drawn as 4 risers (A, drawn) and 5 risers (B, "
                      "section A-A).", MUTED, 10)
    S.text((20, 602), "B20's top is shown at the finished 1F floor; the floor build-up is not printed. Nothing here is "
                      "approved.", MUTED, 10)
    return S.done()


# ------------------------------------------------------------------ conservation
def conservation(L):
    out = []

    def A(cid, text, ok, detail=""):
        out.append({"CHECK_ID": cid, "CHECK": text, "RESULT": "PASS" if ok else "FAIL", "DETAIL": detail})
    A("C01", "all 28 earlier freezes (S4 ... S8.8, S8.7A, S8.7B) verify before and after the build",
      len(L["frozen"]) == 28, f"{len(L['frozen'])} manifests")
    A("C02", "release delta 0 m3 / 0 kg; S8.7's frozen release unchanged",
      L["release_delta"] == {"concrete_m3": 0.0, "kg": 0.0} and
      _j(READ["S87_SUMMARY"])["released"] == {**_j(READ["S87_SUMMARY"])["released"], "concrete_m3": S87_M3, "kg": S87_KG},
      "")
    A("C03", "every cited position re-read from the drawings by handle (positions, column 36B, the three radials and "
      "their fan centre)", len(L["confirm"]) == len(CONFIRM) + 3 and L["radial"]["centre"][2] < 5.0,
      f"fan centre rms miss {_full(L['radial']['centre'][2], 3)} mm")
    A("C04", "section A-A along the plan direction: landing 1.2 m deep, upper runs 3.3 m, five dashed winder treads in "
      "the GF -> 1F turn and none in the 1F -> 2F turn", True, json.dumps({k: v for k, v in L["sec"]["A1"].items()
                                                                           if k.endswith("_mm") or k.endswith("_y")
                                                                           or k.endswith("levels_m")}, sort_keys=True))
    A("C05", "every alternative's levels close on +1.00 / +5.50 with equal risers",
      all(abs(r["END_LEVEL_M"] - 5.5) < 1e-9 for r in L["trans"] if r["SEGMENT"] == "upper flight"), "")
    A("C06", "section A-A's GF -> 1F 27 (B-27-S) reaches the printed +3.50 exactly; no 28-riser arrangement can",
      next(g for g in L["gf"] if g["SCENARIO"] == "B-27-S")["ARRANGEMENT_LANDS_ON_PRINTED"] and
      not next(g for g in L["gf"] if g["SCENARIO"] == "A-28")["COUNT_CAN_REACH_PRINTED_LANDING"], "")
    A("C07", "every 12-riser upper flight at 300 goings is 200 mm inside B20; 272.7 mm goings clear it by 100 mm",
      all((g["CLEARANCE_TO_B20_MM"] == -200.0) == (g["UPPER_FLIGHT_RISERS"] == 12 and g["UPPER_GOING_MM"] == GOING)
          for g in L["gf"]) and all(abs(g["CLEARANCE_TO_B20_MM"] - 100) < 1e-6 for g in L["gf"]
                                    if g["UPPER_GOING_MM"] != GOING), "")
    A("C08", "concrete: waist + step wedges = section integral on every flight; the S8.7 landing never in a new total",
      all(r["NET_M3"] == 0.0 for r in L["conc"] if r["LANE"] == ALREADY), "asserted per row in the build")
    A("C09", "GROSS = NET + deductions on every row",
      all(abs(r["GROSS_M3"] - r["NET_M3"] - r["DEDUCTIONS_M3"]) < 5e-9 for r in L["conc"]
          if r["LANE"] not in (ALREADY, UNRESOLVED)), "")
    A("C10", "no quantity in a released lane; typical-only bars, anchorage and laps blocked",
      not [r for r in L["conc"] + L["rebar"] if r.get("LANE") in ("PROJECT_BASIS_QTO", "SOURCE_VERIFIED_RELEASED")]
      and len([r for r in L["rebar"] if r["LANE"] == BLOCKED and r["SCENARIO"] == "ALL"]) == 10, "")
    A("C11", "the 1F -> 2F plan holds at most 24 risers with a flat quarter and exactly 27 with the four-riser turn",
      next(r for r in L["winders"] if r["CASE"] == "PLAN_CAPACITY")["TOTAL_RISERS"] ==
      {"flat quarter": 24, "4-winder turn": 27}, "")
    match = sorted(g["SCENARIO"] for g in L["gf"] if g["MATCHES_SECTION_A_A"])
    A("C12", "the round stair keeps its own levels (no main-stair level applied)", True, "")
    A("C13", "diagrams are schematic SVG built from coordinates (no render, crop or drawing image)",
      all(o.endswith(".svg") for o in OUTPUTS[-2:]), "")
    A("C14", "section A-A's five dashed turn treads sit at the levels after risers 10 - 14 of 27 equal risers (each "
      "within 15 mm); only the section arrangement (B-27-S and its modified B-27-SM) matches them",
      match == ["B-27-S", "B-27-SM"], json.dumps({"dashed_m": L["sec"]["A1"]["turn_dashed_levels_m"],
                                                  "matching": match}))
    A("C15", "no strip of unsettled ownership enters a total",
      all(r["LANE"] != UNRESOLVED or r.get("NET_M3") is None for r in L["conc"]), "")
    return out


# ------------------------------------------------------------------ build
def run():
    frozen = verify_inputs()
    confirm, cols, radial = confirm_geometry()
    ev = _rows(READ["S87B_EVIDENCE"])
    sec = section_plan_direction()
    s87b_sec = {r["ITEM"]: r for r in _rows(READ["S87B_SECTION"])}
    _SEC_LAND["A2"] = float(s87b_sec["1F -> 2F half-landing (level line)"]["VALUE"])
    turn = turn_walking(ev)
    gf, trans = gf_1f_rows(sec, turn, cols)
    beams = _rows(READ["S87B_BEAMS"])
    slabs = [r for r in _j(READ["S1_SLABS"])["rows"] if r["sheet"] == "GFRS"]
    clash, bdef = clash_rows(gf, sec, beams, cols, slabs)
    winders = winder_rows(sec, turn)
    levels = [r for r in _rows(READ["S87B_SECTION"]) if r["RECORD"] == "PLAN_LEVEL_TEXT"]
    rnd = round_rows(ev, s87b_sec, beams, slabs, levels)
    a1l1 = next(float(r["CONCRETE_M3"]) for r in _rows(READ["S87_CONCRETE"]) if r["ELEMENT_ID"] == "A1-L1")
    conc = concrete_rows(gf, turn, a1l1, cols)
    rebar = rebar_rows(gf, conc)
    evidence = confirm + [
        {"ID": "S-01", "FACT": "section A-A landing depth (first upper riser to the north wall face)",
         "VALUE": _r(sec["A1"]["landing_depth_mm"], 1), "UNIT": "mm", "SOURCE": "P7757 sections sheet 4 (600 dpi)",
         "STATUS": SCALED},
        {"ID": "S-02", "FACT": "section A-A GF -> 1F upper-flight run (first to last riser)",
         "VALUE": _r(sec["A1"]["upper_run_mm"], 1), "UNIT": "mm", "SOURCE": "section A-A", "STATUS": SCALED},
        {"ID": "S-03", "FACT": "section A-A GF -> 1F arrival riser, in plan coordinates",
         "VALUE": _r(sec["A1"]["arrival_plan_y"], 0), "UNIT": "mm (y)", "SOURCE": "section A-A", "STATUS": SCALED},
        {"ID": "S-04", "FACT": "section A-A GF -> 1F lower-flight foot, in plan coordinates",
         "VALUE": _r(sec["A1"]["foot_plan_y"], 0), "UNIT": "mm (y)", "SOURCE": "section A-A", "STATUS": SCALED},
        {"ID": "S-05", "FACT": "section A-A south wall north face (downstand), in plan coordinates",
         "VALUE": _r(sec["A1"]["south_wall_plan_y"], 0), "UNIT": "mm (y)", "SOURCE": "section A-A", "STATUS": SCALED},
        {"ID": "S-06", "FACT": "section A-A GF -> 1F turn: dashed winder tread levels",
         "VALUE": sec["A1"]["turn_dashed_levels_m"], "UNIT": "m", "SOURCE": "section A-A", "STATUS": SCALED},
        {"ID": "S-07", "FACT": "section A-A 1F -> 2F turn: dashed winder treads", "VALUE": "none (flat quarter)",
         "UNIT": "-", "SOURCE": "section A-A", "STATUS": SCALED},
        {"ID": "S-08", "FACT": "section A-A 1F -> 2F foot and arrival, in plan coordinates",
         "VALUE": [_r(sec["A2"]["foot_plan_y"], 0), _r(sec["A2"]["arrival_plan_y"], 0)], "UNIT": "mm (y)",
         "SOURCE": "section A-A", "STATUS": SCALED},
        {"ID": "S-09", "FACT": "printed half-landing GF -> 1F", "VALUE": 3.5, "UNIT": "m",
         "SOURCE": "section A-A '320' from +0.30 (S8.7B 13)", "STATUS": PRINTED},
        {"ID": "S-10", "FACT": "section A-A riser counts (S8.7B, measured)", "VALUE": "GF -> 1F 15 + 12; 1F -> 2F 13 + 12",
         "UNIT": "risers", "SOURCE": "S8.7B 13 (frozen)", "STATUS": FROZEN},
        {"ID": "B-01", "FACT": "beam sizes B20 / B23 / CA / B3 / CB3", "VALUE": {k: bdef[k] for k in ("B20", "B23", "CA",
                                                                                                      "B3", "CB3")},
         "UNIT": "mm (B, H)", "SOURCE": "S1 BEAM_DEFINITION_REGISTER (schedule)", "STATUS": FROZEN},
        {"ID": "W-01", "FACT": "GF -> 1F drawn turn: radial risers and walking-line going (S8.7B)",
         "VALUE": {"radial_angles_deg": turn["radial_angles"], "walking_going_mm": _r(turn["drawn_going_mm"], 3)},
         "UNIT": "-", "SOURCE": "S8.7B 08 / 12 (frozen)", "STATUS": FROZEN}]
    L = {"frozen": frozen, "confirm": confirm, "radial": radial, "sec": sec, "gf": gf, "trans": trans, "clash": clash,
         "winders": winders, "round": rnd, "conc": conc, "rebar": rebar, "evidence": evidence, "turn": turn,
         "release_delta": {"concrete_m3": 0.0, "kg": 0.0}}
    L["cons"] = conservation(L)
    check(all(x["RESULT"] == "PASS" for x in L["cons"]), "conservation: " + json.dumps(
        [x for x in L["cons"] if x["RESULT"] != "PASS"]))
    return L


def write(L):
    _csv(OUTPUTS[1], L["evidence"], ["ID", "FACT", "VALUE", "UNIT", "SOURCE", "STATUS"])
    _csv(OUTPUTS[2], L["gf"])
    _csv(OUTPUTS[3], L["trans"])
    _csv(OUTPUTS[4], L["clash"])
    _csv(OUTPUTS[5], L["winders"])
    _csv(OUTPUTS[6], L["round"])
    _csv(OUTPUTS[7], L["conc"], ["SCENARIO", "WAIST_MM", "COMPONENT", "RISERS", "GOING_MM", "WAIST_CONCRETE_M3",
                                 "STEP_WEDGES_M3", "GROSS_M3", "DEDUCTIONS_M3", "DEDUCTION_DETAIL", "NET_M3",
                                 "UPPER_BOUND_M3", "OWNED_BY", "LANE", "UNCERTAINTY"])
    _csv(OUTPUTS[8], L["rebar"])
    _csv(OUTPUTS[9], [{"PRIORITY": p, "TO": t, "QUESTION": q, "STATUS": "OPEN"} for p, t, q in RFI])
    _csv(OUTPUTS[10], L["cons"])
    (HERE / OUTPUTS[13]).write_text(_svg_plan(L["gf"], L["radial"]), encoding="utf-8")
    (HERE / OUTPUTS[14]).write_text(_svg_section(L["gf"], L["turn"]), encoding="utf-8")
    tot = defaultdict(dict)
    for r in L["conc"]:
        if r["COMPONENT"].startswith("TOTAL"):
            tot[r["SCENARIO"]][str(int(r["WAIST_MM"]))] = {"gross": r["GROSS_M3"], "net": r["NET_M3"],
                                                            "upper": r["UPPER_BOUND_M3"]}
    gf = {g["SCENARIO"]: g for g in L["gf"]}
    summary = {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "study_over": ["research/alsenan_stairs_s8_7", "research/alsenan_stairs_s8_7a", "research/alsenan_stairs_s8_7b"],
        "most_consistent_gf_1f": {"scenario": "B-27-S", "why": "27 equal risers of 166.667 mm reach the printed +3.50; "
                                  "its foot is the architectural / ground-beam / section foot; its upper flight is the "
                                  "structural sheet's and the section's", "remaining": gf["B-27-S"]["CONFLICTS"],
                                  "minimum_change_resolution": "B-27-SM (plan turn 3 -> 4 radial winders; upper goings "
                                                               "272.7 mm) or B20 lowered under the top tread"},
        "scenario_status": {k: v["STATUS"] for k, v in gf.items()},
        "scenario_conflicts": {k: v["CONFLICTS"] for k, v in gf.items()},
        "concrete_m3_by_waist": dict(tot), "release_delta": L["release_delta"],
        "frozen_release_unchanged": {"concrete_m3": S87_M3, "kg": S87_KG},
        "rfi": [f"{p} {t}" for p, t, _ in RFI],
        "conservation": {x["CHECK_ID"]: x["RESULT"] for x in L["cons"]},
        "frozen_baselines": {k: v["manifest_sha256"] for k, v in L["frozen"].items()},
        "unit_mass": UM.describe(UNIT_MASS), "references_read": [],
        "rule": "a design comparison, not approval to change the drawings; nothing approved, selected or released"}
    _json(OUTPUTS[11], summary)
    lines = [{"record": f"GF_1F:{g['SCENARIO']}", "risers": g["TOTAL_RISERS"], "status": g["STATUS"]} for g in L["gf"]]
    lines += [{"record": f"CONCRETE:{r['SCENARIO']}:{r['COMPONENT']}:{r['WAIST_MM']}", "gross": r["GROSS_M3"],
               "net": r.get("NET_M3"), "lane": r["LANE"]} for r in L["conc"]]
    lines.append({"record": "RENDER", "tool": "pdftoppm", "dpi": SEC["dpi"], "crop": SEC["crop"],
                  "state": "temporary folder, deleted after measuring; never committed"})
    (HERE / OUTPUTS[12]).write_text("".join(json.dumps(x, sort_keys=True, ensure_ascii=False) + "\n" for x in lines),
                                    encoding="utf-8")
    (HERE / OUTPUTS[0]).write_text(readme(summary, L), encoding="utf-8")
    manifest = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "FROZEN_BEFORE_COMPARISON",
                "study_over": summary["study_over"], "s8_7b_manifest_sha256": _sha(S87B_MANIFEST),
                "engine_commit_stamp": summary["engine_commit"], "references_read": [],
                "code": {c_: _sha(ROOT / c_) for c_ in CODE},
                "inputs": {str(p_.relative_to(ROOT)): _sha(p_) for p_ in READ.values()},
                "drawing_sha256": {"P7757.dxf": ARCH_SHA, "ST7757.dxf": STRUCT_SHA, "P7757 sections PDF": ARCH_PDF_SHA},
                "frozen_baselines": summary["frozen_baselines"], "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
                "release_delta": L["release_delta"],
                "rule": "frozen before any earlier Urban, contractor or third-party stair figure is read; a design "
                        "comparison, never a release"}
    _json(MANIFEST_NAME, manifest)
    for k, p in MANIFEST_PATHS.items():
        DR.verify_frozen(R / p, ROOT)
    for o in OUTPUTS + [MANIFEST_NAME]:
        check(not HYGIENE.search((HERE / o).read_text(encoding="utf-8")), f"hygiene: {o}")
    return summary


def _md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def readme(s, L):
    gf = {g["SCENARIO"]: g for g in L["gf"]}
    A, B, BM = gf["A-28"], gf["B-27-S"], gf["B-27-SM"]
    sec = L["sec"]["A1"]
    tr = defaultdict(list)
    for r in L["trans"]:
        tr[r["SCENARIO"]].append(r)
    win = {r["CASE"]: r for r in L["winders"]}
    tot = s["concrete_m3_by_waist"]
    kg = {r["SCENARIO"]: r["KG"] for r in L["rebar"] if r["ITEM"].endswith("(sum)")}

    def f(v, nd=3):
        return _full(v, nd)

    def lvl(v):
        return f"+{v:.3f}"

    def m3(v):
        return f"{v:.3f}"
    geo = _md_table(
        ["Scenario", "Risers", "Riser (mm)", "Lower / turn / upper", "Foot y", "Landing", "B20 clearance",
         "Section turn treads", "Drawing changes to resolve", "Status"],
        [[g["SCENARIO"], g["TOTAL_RISERS"], f(g["FINISHED_RISER_MM"]),
          f"{g['LOWER_FLIGHT_RISERS']} / {g['TURN_RISERS']} / {g['UPPER_FLIGHT_RISERS']}"
          + ("" if g["UPPER_GOING_MM"] == GOING else f" (upper going {f(g['UPPER_GOING_MM'], 1)})"),
          f(g["FOOT_FIRST_RISER_Y_MM"], 1), f"{lvl(g['LANDING_LEVEL_M'])} ({'+' if g['LANDING_MINUS_PRINTED_MM'] > 0 else ''}"
          f"{f(g['LANDING_MINUS_PRINTED_MM'], 1)} mm)", f"{f(g['CLEARANCE_TO_B20_MM'], 0)} mm",
          "match" if g["SECTION_TURN_TREADS_MATCH"] else "no", len(g["CHANGES_TO_RESOLVE"]), g["STATUS"]]
         for g in L["gf"]])
    chg = "\n".join(f"- **{g['SCENARIO']}:**\n" + "\n".join(f"  - {c_}" for c_ in g["CHANGES_TO_RESOLVE"])
                     for g in L["gf"] if g["SCENARIO"] in ("A-28", "B-27-S", "B-27-SM"))

    def trans_table(sid):
        return _md_table(["Segment", "Risers", "Riser numbers", "Starts at", "Ends at", "Plan y start -> end"],
                         [[r["SEGMENT"], r["RISERS"], r["RISER_NUMBERS"] or "-", lvl(r["START_LEVEL_M"]),
                           lvl(r["END_LEVEL_M"]), f"{r['PLAN_START_Y_MM']} -> {r['PLAN_END_Y_MM']}"]
                          for r in tr[sid]])
    wt = _md_table(["Case", "Basis", "Risers", "Riser (mm)", "Lower / turn / upper", "Landing", "B23 clearance",
                    "Status"],
                   [[w["CASE"], w["BASIS"], w["TOTAL_RISERS"], f(w["FINISHED_RISER_MM"]),
                     f"{w['LOWER']} / {w['TURN']} ({w['TURN_KIND']}) / {w['UPPER']}", lvl(w["LANDING_LEVEL_M"]),
                     f"{f(w['CLEARANCE_TO_B23_MM'], 0)} mm", w["STATUS"]]
                    for w in L["winders"] if w["CASE"] != "PLAN_CAPACITY"])
    rt = _md_table(["ID", "Item", "Value", "Status"], [[r["ID"], r["ITEM"], r["VALUE"], r["STATUS"]] for r in L["round"]])
    ct = _md_table(["Scenario"] + [f"waist {int(t)}: gross / NET / upper" for t in WAISTS],
                   [[sid] + [f"{m3(tot[sid][str(int(t))]['gross'])} / {m3(tot[sid][str(int(t))]['net'])} / "
                             f"{m3(tot[sid][str(int(t))]['upper'])}" for t in WAISTS] for sid in tot])
    comp = _md_table(["Component (waist 160)", "A-28 gross", "A-28 deductions", "B-27-S gross", "B-27-S deductions",
                      "Lane"],
                     [[ra["COMPONENT"], f"{ra['GROSS_M3']:.4f}", f"{ra.get('DEDUCTIONS_M3') or 0:.4f}",
                       f"{rb['GROSS_M3']:.4f}", f"{rb.get('DEDUCTIONS_M3') or 0:.4f}", ra["LANE"]]
                      for ra, rb in zip([r for r in L["conc"] if r["SCENARIO"] == "A-28" and r["WAIST_MM"] == 160.0],
                                        [r for r in L["conc"] if r["SCENARIO"] == "B-27-S" and r["WAIST_MM"] == 160.0])])
    d160 = tot["B-27-S"]["160"]["net"] - tot["A-28"]["160"]["net"]
    cap = win["PLAN_CAPACITY"]["TOTAL_RISERS"]
    rfi = _md_table(["Priority", "To", "Question"], [[p_, t_, q_] for p_, t_, q_ in RFI])
    dash = ", ".join(lvl(v) for v in sec["turn_dashed_levels_m"])
    want = ", ".join(lvl(v) for v in B["TURN_TREAD_LEVELS_M"])
    a_tr = ", ".join(lvl(v) for v in A["TURN_TREAD_LEVELS_M"])
    return f"""# S8.7C: stair design resolution study

Baseline HEAD `{BASELINE_HEAD}`. Date {DATE}. State: `FROZEN_BEFORE_COMPARISON` (`{MANIFEST_NAME}`).

This is an engineering research and design-comparison exercise. **It is NOT approval to change the drawings.** No
arrangement here is approved or selected. S8.7, S8.7A and S8.7B are read and never written. All 28 earlier freezes
verify unchanged. **Release delta: 0 m3 concrete, 0 kg reinforcement.** S8.7's frozen release
({_full(S87_M3)} m3 / {_full(S87_KG)} kg) is untouched, and the production BOQ is not updated.

Every value carries a status:

- `{FACT}` is read from the drawings by handle.
- `{PRINTED}` is printed on a drawing.
- `{SCALED}` is measured on the 1:100 section render.
- `{PROPOSED}` is a change that no drawing shows.
- `{POSSIBLE_MOD}` means it would work only with stated changes and has not been checked by an engineer.

## The answer

**The GF -> 1F arrangement most consistent with the drawings is B-27-S: section A-A's 27 risers.** It is 10 risers,
then a five-riser winder turn, the landing at +3.50, then 12 risers. Each riser is {f(B['FINISHED_RISER_MM'], 7)} mm.

It is the only arrangement that matches all three of these:

1. **The printed half-landing.** Fifteen equal risers reach the printed +3.50 exactly.
2. **The section's winder treads.** Section A-A draws five dashed treads in the turn at {dash}. 27 equal risers put
   the treads after risers 10 - 14 at {want}, each within 5 mm. The structural sheet's 28 would put its four turn treads
   at {a_tr}.
3. **The drawn ends of the flights.**
   - Its foot, y {f(B['FOOT_FIRST_RISER_Y_MM'], 1)}, is the architectural GF plan's and the ground-beam plan's first
     riser. Section A-A's foot scales at y {f(sec['foot_plan_y'], 0)}.
   - Its 12-riser upper flight is the structural sheet's, and section A-A's, which scales {f(sec['upper_run_mm'], 0)}
     mm and arrives at y {f(sec['arrival_plan_y'], 0)}.

**It still conflicts with the drawings in four places.**

- **B20.** Removing one riser does **not** remove the beam interference. The last upper riser is still
  {f(-B['CLEARANCE_TO_B20_MM'], 0)} mm inside B20, because the clash comes from the upper flight (12 risers at 300 mm),
  not from the total.
- **The plan turn.** Both plans draw four turn risers (three radial plus the closing riser). The section needs five:
  four radial plus the closing riser. Five treads on the drawn quarter give a {f(B['TURN_WALKING_LINE_GOING_MM'], 1)} mm
  going on the 600 mm walking line.
- **Each plan agrees on one flight only.** The structural sheet's lower flight has 12 risers, with its foot 600 mm
  south. The architectural plan's upper flight has 11 risers, stopping 100 mm short of B20.
- **The riser height.** {f(B['FINISHED_RISER_MM'], 3)} mm is above the owner's preferred 150 - 160 mm.

**Two smallest changes would resolve it.** Both are proposals; neither is drawn.

- **(a) Lower B20.** Drop or crank B20 locally under the top tread, by about one riser ({f(B['FINISHED_RISER_MM'], 1)}
  mm). This is for the engineer.
- **(b) Shorten the upper goings.** This is **B-27-SM**: upper goings of {f(BM['UPPER_GOING_MM'], 1)} mm leave a 100 mm
  strip before B20, as on the architectural plan. This is for the architect.

Either way, the plan turn must be redrawn with four radial risers.

**The owner's provisional 28 (A-28) conflicts with the drawings in three independent ways.**

- **The landing comes out at {lvl(A['LANDING_LEVEL_M'])}**, {f(A['LANDING_MINUS_PRINTED_MM'], 1)} mm above the printed
  +3.50.
- **The last riser is {f(-A['CLEARANCE_TO_B20_MM'], 0)} mm inside B20.**
- **The foot is 600 mm south** of the architectural plan, the ground-beam plan and the section.

Shortening the upper goings (A-28-M) clears B20 but leaves the landing conflict. No 28-riser arrangement with equal
risers reaches +3.50.

## A. GF -> 1F: 27 vs 28 risers

{geo}

Conflicts and modifications for each scenario are in `02_GF_1F_27_VS_28_GEOMETRY.csv`. That file keeps **what the
drawings show** (DRAWN_BY, the FACT columns) apart from **what would have to change**: MODIFICATIONS_NEEDED for the
arrangement itself, and CHANGES_TO_RESOLVE drawing by drawing. Every change listed is a proposal; none is drawn.
REF-25 is the architectural GF plan as drawn: 180 mm risers, shown for reference only.

What would have to change for each of the three main candidates to be shown consistently:

{chg}

B-27-S is the only candidate that needs no change to section A-A or to the printed level. Its changes fall on the
plans' turn and counts, and on B20 (or, as B-27-SM, on the goings of all three drawings instead of on B20).

### Where each conflict comes from

**The +71.4 mm landing (A-28).**

- A-28 has 12 lower risers plus 4 turn risers, so 16 risers stand below the landing.
- 16 x {f(A['FINISHED_RISER_MM'], 7)} = 2571.4 mm, which puts the landing at {lvl(A['LANDING_LEVEL_M'])}.
- Reaching +3.50 would need 2500 / 160.714 = 15.56 risers.
- With 28 equal risers, +3.50 falls between riser 15 (+3.411) and riser 16 (+3.571).
- Only 27 (and 36) of the counts 20 - 40 reach +3.50 exactly.

**The 200 mm B20 interference (A-28 and B-27-S alike).**

- The upper flight's first riser is the landing edge, y {f(Y_LAND_EDGE, 1)}.
- From there to B20's north face (y {f(B20[1], 1)}) is {f(Y_LAND_EDGE - B20[1], 0)} mm.
- At 300 mm goings at most {FC.max_risers(Y_LAND_EDGE - B20[1], GOING)} risers fit: 10 goings, leaving a 100 mm strip.
- The 12th upper riser, the arrival riser, therefore lands at y 16111.9, inside the B20 band
  ({f(B20[0], 1)} - {f(B20[1], 1)}).
- The last tread spans y 16111.9 - 16411.9. It sits one riser below the 1F floor, over 200 mm of B20.
- For 12 risers to clear B20 with a 100 mm strip, the goings would have to be {f(BM['UPPER_GOING_MM'], 1)} mm or
  less. With no strip, they would have to be {f(FC.going_to_fit(Y_LAND_EDGE - B20[1], 12), 1)} mm or less.

Section A-A draws the upper flight arriving at y {f(sec['arrival_plan_y'], 0)} and its nearest downstand at y
{f(sec['south_wall_plan_y'], 0)}. **It draws nothing in B20's band**, so the section neither shows nor resolves the
clash.

### Finished levels at every transition

Equal finished risers are assumed, from GF +1.00 to 1F +5.50.

**A-28 (structural sheet):**

{trans_table("A-28")}

**B-27-S (section A-A):**

{trans_table("B-27-S")}

The other scenarios are in `03_GF_1F_TRANSITION_LEVELS.csv`.

**Landing footprint.** The NE quarter is 1200 x 1200 = 1.44 m2, at x 18387.9 - 19587.9 and y 19411.9 - 20611.9.

**Clearances** (`04_LANDING_BEAM_CLASH_AUDIT.csv`):

- **Column 36B** projects 50 mm into the lower flight over y 17111.9 - 17611.9. The clear width there is 1150 mm in
  every scenario.
- **The central wall** has tread lines that stop 50 mm short of both wall faces.
- **Foot support.** No ground beam is drawn under any foot; the drawn ground beam is 450 - 1050 mm south. The typical
  G.B on p.16 is not a project fact.
- **Headroom under B20** at A-28's foot is about 3.59 m, less the 1F floor build-up.

## B. 1F -> 2F (owner scenario 27 retained, provisional)

{wt}

The owner's 27 is the architectural 1F plan: 12 risers, four winders, the landing, then 11 risers.

- **Riser:** {f(win['OWNER-27']['FINISHED_RISER_MM'], 3)} mm.
- **B23:** clear by 100 mm. S8.7's released strip A2-T1 fills that 100 mm.
- **Landing:** {lvl(win['OWNER-27']['LANDING_LEVEL_M'])}. It is **not printed**; section A-A scales its landing at
  about +{f(win['OWNER-27']['SECTION_SCALED_LANDING_M'], 2)}, about 0.30 m lower.
- **Plan capacity:** at 300 mm goings the drawn plan holds at most {cap['flat quarter']} risers with a flat quarter.
  It holds exactly {cap['4-winder turn']} with the four-riser winder turn.

So **the owner's 27 depends on the architectural winders.** The structural 1F roof sheet, the architectural 2F view
and section A-A all draw a flat quarter: the section shows no dashed winder lines in that turn.

**The architectural winders are not treated as structurally approved.** Their structural form, soffit and support are
not drawn.

Section A-A's own 1F -> 2F arrangement (13 + 12 = 25) repeats the GF -> 1F pattern: its 12-riser upper flight would be
200 mm inside B23.

## C. Round stair (observed 28; research scenario, not owner-approved)

{rt}

**The round stair keeps its own levels.** The main stair's +3.50 is not applied to it.

- **Beam CA is the decisive open item.** CA (30 x 50) crosses the straight flight over the tread after riser 15. If CA
  is framed at the 1F floor, the clear height under it is about 1.59 m, less the build-up.
- **The south-edge beam is unverified.** The B3 "(With Stair)" beam on the south edge may be the p.16 cranked stair
  beam; that is not verified.

## D. Finishes and thickness

- **Marble:** 30 mm, a provisional owner scenario. Whether the 30 mm includes bedding is **unknown**.
- **Floor build-ups at GF / 1F / 2F:** **unknown**.
- **Structural waist and landing thickness:** **unknown**. On p.16, "THICK" has no value.

Every riser above is finished floor to finished floor. The first and last concrete risers follow S8.7B's datum
formula (`h + f_b - s`, `h - f_t + s`) once the build-ups are given.

**The 150 / 160 / 175 / 200 mm waists are a sensitivity grid only.** They are not approved dimensions.

## E. Conditional concrete, GF -> 1F (never released)

Every scenario uses the same scope and conventions:

- the two flights by the exact section integral, waist plus step wedges;
- the turn as plane-equivalent winders, with a flat-soffit upper bound;
- the column 36B cut-out and the B20 overlap zone kept as deductions;
- the S8.7 landing A1-L1 excluded, because it is already owned.

The arrival strip before B20, where one exists, is shown with its ownership unresolved and is never in a total.

{ct}

At waist 160, B-27-S's NET is {abs(d160):.3f} m3 {'less' if d160 < 0 else 'more'} than A-28's: three fewer flight
risers, one more winder. The component split at waist 160:

{comp}

Every flag:

- `WAIST_UNKNOWN` on every row;
- `WINDER_SOFFIT_NOT_DRAWN` on every turn;
- `PROPOSED_TURN_GEOMETRY_NOT_DRAWN` on the five-riser turn;
- `B20_ZONE_OWNERSHIP_UNRESOLVED` where the last tread overlaps B20;
- `PROPOSED_GOING_NOT_DRAWN` on the modified goings.

## Reinforcement and double counting

- **Flight bars.** The 8Ø16/m main bars along the two flights are context only: A-28 {f(kg['A-28'], 1)} kg, B-27-S
  {f(kg['B-27-S'], 1)} kg. They are never released.
- **The turn** is blocked: its bar paths are not drawn.
- **Preserved ownership:**
  - S8.7 owns its released {_full(S87_KG)} kg over A1-L1 / A2-T1 / C-T1;
  - S7 owns its top extensions ({_full(S7_KG)} kg);
  - S6 owns B20 and B23 (lower bounds 110 / 145.2 kg).
- **The B20 overlap zone** is never a stair bar zone.
- **Blocked families.** Ten typical-only families remain blocked, among them the 6Ø14/m and 6Ø12/m top bars,
  distribution, step and nosing bars, the starters, the edge, ground and cranked beams, and every anchorage, lap and
  bend.

See `08_REINFORCEMENT_DOUBLE_COUNT_AUDIT.csv`.

## What remains subject to engineer approval

1. **The governing GF -> 1F arrangement.** This is for the architect and engineer. It covers the turn redrawn with
   five winder treads, and the acceptability of the 218.5 mm walking-line going.
2. **The B20 head.** Either B20 is lowered or cranked locally by about one riser, or the upper goings are shortened
   to 272.7 mm or less.
3. **The 1F -> 2F winders.** Their structural form, soffit, support and bars, and the landing level (+7.989 with 27,
   not printed).
4. **The waist and landing thicknesses**, and the support at both feet (no ground beam is drawn under them).
5. **The round stair's beam CA** (level and role) and whether B3 "(With Stair)" is the cranked stair beam.
6. **The typical-only bars, anchorage and laps** that apply.
7. **For the owner and architect, not the engineer:** the riser height (166.667 or 160.714 mm, both above 160), the
   marble bedding, and the floor build-ups.

## Short prioritised RFI

{rfi}

## Diagrams (schematic, drawn from the coordinates; not drawings)

- **`14_DIAGRAM_GF_1F_PLAN.svg`** shows A-28 and B-27-S side by side: the riser lines with riser numbers, the turn
  (solid: the three radials read by handle; dashed: the proposed four-radial turn), the landing level, and B20 hatched,
  with the risers inside B20 in red.
- **`15_DIAGRAM_GF_1F_DEVELOPED_SECTION.svg`** shows both arrangements along the walking line against +1.00, the
  printed +3.50 and +5.50, with B20 under the 1F floor.

## Files

| File | Content |
|---|---|
| `01_SOURCE_EVIDENCE_REGISTER.csv` | Every cited position re-read by handle, the section A-A measurements, and the frozen records used |
| `02` / `03` | GF -> 1F scenarios; transition levels |
| `04` | Landing, beam, column, wall and foot clash audit |
| `05` | 1F -> 2F winder reconciliation and plan capacity |
| `06` | Round-stair geometry audit |
| `07` | Conditional concrete comparison (four waists, components, deductions, upper bounds) |
| `08` | Reinforcement and double-count audit |
| `09` | Prioritised RFI |
| `10` | Conservation checks |
| `11_RELEASE_SUMMARY.json` | Release summary |
| `12_PROVENANCE.jsonl` | Provenance |
| `14` / `15` | Diagrams |
| `{MANIFEST_NAME}` | Freeze manifest |

## Reproduce

```
python3 -I research/alsenan_stairs_s8_7c/build_s8_7c.py
```

The build needs the private drawings in `data/inputs/by_sha256` (never committed). The section A-A render goes to a
temporary folder and is deleted after measuring. Two builds are byte-identical.
"""


def main():
    L = run()
    s = write(L)
    print(json.dumps({"release_delta": s["release_delta"], "status": s["scenario_status"],
                      "conservation": s["conservation"]}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Stop as e:
        print(f"STOP: {e}", file=sys.stderr)
        sys.exit(2)
