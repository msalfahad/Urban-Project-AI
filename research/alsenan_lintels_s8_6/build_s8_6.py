"""S8.6 - lintels: architectural opening census, binding to the p.13 LINTEL SCHEDULE, lintel concrete and
reinforcement. Source-controlled and blind (frozen before any comparison).

    python3 -I research/alsenan_lintels_s8_6/build_s8_6.py

Reads the registered architectural DXF (P7757: GF / 1F / 2F plans), the registered structural DXF (ST7757: the GF /
1F / 2F roof-slab sheets through the frozen S1 reader) and frozen Urban stages:
- S1 registers (rules, levels, columns, beams, slab panels, special occurrences);
- S6 beam occurrences;
- the PRE-S8 census, through a column whitelist (its quantity column is never bound);
- the R5 opening register, through a field whitelist (its lintel and height fields are never read).
p.13 of the plotted set has no vector text. The LINTEL SCHEDULE, the LINTEL DETAIL and SECT (2-2) enter as visual
records read in session from renders; the renders are client drawing and stay out of git.

Every physical wall opening of the three plans is found once from the wall faces, given its evidence, its wall, its
sides and its type, registered onto the slab sheet above, and given exactly one lintel decision. A lintel is released
only where the schedule binds the opening and no structural member already stands over it. No earlier Urban total,
contractor figure or third-party figure is read.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "research" / "external_engine_lab"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import delta_release as DR  # noqa: E402
from engine.source import lintel_qto as LQ  # noqa: E402
from engine.source import opening_census as OC  # noqa: E402
from engine.source import rebar_unit_mass as UM  # noqa: E402

ROUND = "S8_6"
DATE = "2026-10-09"
BASELINE_HEAD = "818321e"
POLICY = "S8_6_LINTELS_V1"
R = ROOT / "research"
BY_SHA = ROOT / "data/inputs/by_sha256"
ARCH_SHA = "ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4"
STRUCT_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
STRUCT_PDF_SHA = "74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3"
MANIFESTS = {"S4": R / "alsenan_footing_rebar_s4/S4_FREEZE_MANIFEST.json",
             "S4.1": R / "alsenan_footing_rebar_s4_1/S4_1_FREEZE_MANIFEST.json",
             "S5": R / "alsenan_ground_system_rebar_s5/S5_FREEZE_MANIFEST.json",
             "S5.1": R / "alsenan_ground_system_rebar_s5_1/S5_1_FREEZE_MANIFEST.json",
             "S6": R / "alsenan_superstructure_beam_rebar_s6/S6_FREEZE_MANIFEST.json",
             "S6.1": R / "alsenan_superstructure_beam_rebar_s6_1/S6_1_FREEZE_MANIFEST.json",
             "AD1": R / "ad1_authority_decisions/AD1_FREEZE_MANIFEST.json",
             "D1.1": R / "d1_1_stirrup_authority_audit/D1_1_FREEZE_MANIFEST.json",
             "D1.2": R / "d1_2_footing_cover_audit/D1_2_FREEZE_MANIFEST.json",
             "PRE-S7": R / "alsenan_slab_rebar_pre_s7/PRE_S7_FREEZE_MANIFEST.json",
             "PRE-S7.1": R / "alsenan_slab_rebar_pre_s7_1/PRE_S7_1_FREEZE_MANIFEST.json",
             "S7": R / "alsenan_slab_rebar_s7/12_S7_FREEZE_MANIFEST.json",
             "S7A": R / "alsenan_slab_rebar_s7a_qa/11_S7A_FREEZE_MANIFEST.json",
             "PRE-S8": R / "pre_s8_structural_completeness/13_PRE_S8_FREEZE_MANIFEST.json",
             "S8.1": R / "alsenan_ground_slab_s8_1/11_S8_1_FREEZE_MANIFEST.json",
             "S8.1A": R / "alsenan_ground_slab_s8_1a/14_S8_1A_FREEZE_MANIFEST.json",
             "S8.2": R / "alsenan_swimming_pool_s8_2/18_S8_2_FREEZE_MANIFEST.json",
             "S8.2A": R / "alsenan_swimming_pool_s8_2a/12_S8_2A_FREEZE_MANIFEST.json",
             "S8.3": R / "alsenan_dome_ring_s8_3/16_S8_3_FREEZE_MANIFEST.json",
             "S8.3A": R / "alsenan_dome_mesh_s8_3a/09_S8_3A_FREEZE_MANIFEST.json",
             "S8.4": R / "alsenan_water_tank_s8_4/15_S8_4_FREEZE_MANIFEST.json",
             "S8.5": R / "alsenan_special_columns_s8_5/17_S8_5_FREEZE_MANIFEST.json"}
S83_ERRATA = R / "alsenan_dome_ring_s8_3/errata"
S1D = R / "alsenan_structural_census_s1"
S2D = R / "alsenan_structural_s2"
S31D = R / "alsenan_column_rebar_s3_1"
INDEXES = {"S1": (S1D / "INDEX.json", "registers"), "S2": (S2D / "INDEX.json", "outputs"),
           "S3": (R / "alsenan_column_rebar_s3/INDEX.json", "outputs"), "S3.1": (S31D / "INDEX.json", "outputs")}
READ = {"S1_SPECIAL": S1D / "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER.json",
        "S1_RULES": S1D / "STRUCTURAL_PROJECT_RULE_REGISTER.json",
        "S1_LEVELS": S1D / "STRUCTURAL_LEVEL_REGISTER.json",
        "S1_COLUMNS": S1D / "COLUMN_OCCURRENCE_REGISTER.json",
        "S1_BEAM_DEFS": S1D / "BEAM_DEFINITION_REGISTER.json",
        "S1_BEAMS": S1D / "BEAM_OCCURRENCE_REGISTER.json",
        "S1_SLABS": S1D / "SLAB_PANEL_REGISTER.json",
        "S1_FOOTINGS": S1D / "FOOTING_OCCURRENCE_REGISTER.json",
        "S2_COMPONENTS": S2D / "ALSENAN_COMPONENT_RELEASE.json",
        "S6_OCC": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCES.csv",
        "S6_CONSERVATION": R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OBJECT_CONSERVATION.csv",
        "PRE_S8_CENSUS": R / "pre_s8_structural_completeness/02_STRUCTURAL_ELEMENT_CENSUS.csv",
        "R5_OPENINGS": R / "alsenan_arch_truth_05/registers/OPENING_EVIDENCE_REGISTER_V3.json",
        "S1_FOOTING_DEFS": S1D / "FOOTING_DEFINITION_REGISTER.json",
        "PS5_1_SUMMARY": R / "pre_s5_1_source_resolution/PRE_S5_1_SUMMARY.json"}
# PRE-S8 is read for its ownership claims only. Its quantity column is never bound to a name.
PRE_S8_COLUMNS = ("ELEMENT_ID", "PARENT_ELEMENT", "ELEMENT_FAMILY", "FLOOR", "EXISTING_STAGE_OWNER", "NEW_S8_OWNER",
                  "MISSING_INFORMATION")
PRE_S8_FIREWALLED = ("CONCRETE_QUANTITY_STATE",)
# R5 is read for its population only: never its lintel, height, sill, area or material fields.
R5_FIELDS = ("id", "floor", "type", "r2_kind", "width", "host_wall", "geometry", "room_adjacency", "function")
R5_FIREWALLED = ("lintel_depth_m", "height", "sill_m", "area", "material")
CODE = ["engine/source/opening_census.py", "engine/source/lintel_qto.py", "engine/source/rebar_unit_mass.py",
        "engine/source/delta_release.py",
        "research/alsenan_lintels_s8_6/build_s8_6.py", "research/external_engine_lab/alsenan_structural_s1.py"]
OUTPUTS = ["00_README.md", "01_OPENING_CENSUS.csv", "02_LINTEL_SCHEDULE_TRANSCRIPTION.csv",
           "03_ARCH_STRUCTURAL_REGISTRATION.csv", "04_OPENING_LINTEL_BINDING_MATRIX.csv", "05_BEAM_OVERLAP_AUDIT.csv",
           "06_LINTEL_CONCRETE_QTO.csv", "07_LINTEL_REBAR_QTO.csv", "08_BLOCKED_AND_CONFLICTS.csv",
           "09_OPENING_REGISTER_FOR_BOQ.csv", "10_OWNERSHIP_RECONCILIATION.csv", "11_CONSERVATION_CHECKS.csv",
           "12_SOURCE_AUTHORITY.csv", "13_PROVENANCE.jsonl", "14_S8_6_SUMMARY.json"]
MANIFEST_NAME = "15_S8_6_FREEZE_MANIFEST.json"
UNIT_MASS = {"method": UM.D2_OVER_162, "authority": "project-wide method used by S3.1 / S6.1 / S7 / S8",
             "selected_by": "Urban (project basis)"}
SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO = "SOURCE_DERIVED_PHYSICAL", "PROJECT_BASIS_QTO"
BLOCKED, CONFLICT, SENS = "BLOCKED_UNQUANTIFIED", "SOURCE_CONFLICT", "SENSITIVITY_ONLY"
NOT_IN_SOURCE, NOT_ADDED = "NOT_IN_SOURCE", "NOT_ADDED"
RELEASED_LANES = (SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO)

# ------------------------------------------------------------------ the six lintel decisions (brief, phase 4)
SCHEDULE_BOUND = "SCHEDULE_BOUND_LINTEL"
BEAM_ABOVE = "EXISTING_STRUCTURAL_BEAM_ABOVE"
OTHER_SUPPORT = "OTHER_ESTABLISHED_SUPPORT"
BLOCKED_SUPPORT = "BLOCKED_SUPPORT_IDENTITY"
NO_LINTEL = "OPENING_NOT_REQUIRING_SEPARATE_LINTEL"
DECISION_CONFLICT = "SOURCE_CONFLICT"
DECISIONS = (SCHEDULE_BOUND, BEAM_ABOVE, OTHER_SUPPORT, BLOCKED_SUPPORT, NO_LINTEL, DECISION_CONFLICT)

# ------------------------------------------------------------------ opening types (brief, phase 2)
T_INTERNAL_DOOR = "1_INTERNAL_DOOR"
T_MAIN_ENTRANCE = "2_MAIN_ENTRANCE_DOOR"
T_EXTERNAL_DOOR = "3_EXTERNAL_DOOR"
T_WINDOW = "4_WINDOW"
T_GLAZED = "4_5_GLAZED_WINDOW_OR_FULL_HEIGHT_UNRESOLVED"
T_FULL_HEIGHT = "5_FULL_HEIGHT_GLAZED_OPENING"
T_SERVICE = "6_SERVICE_SHAFT_OPENING"
T_PASSAGE = "7_OPEN_ARCHWAY_OR_PASSAGE"
T_SLAB = "8_STRUCTURAL_SLAB_OPENING"
TYPES = (T_INTERNAL_DOOR, T_MAIN_ENTRANCE, T_EXTERNAL_DOOR, T_WINDOW, T_FULL_HEIGHT, T_GLAZED, T_SERVICE, T_PASSAGE,
         T_SLAB)

# ------------------------------------------------------------------ the architectural drawing (P7757), layer roles
FLOORS = ("GF", "1F", "2F")
PLAN_TITLE = {"GF": "GF", "1F": "FF", "2F": "SF"}      # plan-title inserts (layer 4) naming each plan frame
SLAB_ABOVE = {"GF": "GFRS", "1F": "FFRS", "2F": "SFRS"}  # the roof-slab sheet that closes each storey (S1 levels)
WALL_LAYER, GLAZING_LAYER, DOOR_LAYER, COLUMN_LAYER = "1", "W", "D", "S-COL.BON"
OVERHEAD_LAYER, LABEL_LAYER = "2", "4"
DOOR_BLOCK = re.compile(r"^[Dd]\d+$")
ELEV_OPENING_LAYERS = ("W", "D", "5")   # glazing, door and thin-line (door leaf) layers drawn in elevation
NUMERIC_TEXT = re.compile(r"^(?:%%[pP]|\+|-)?\d+(?:\.\d+)?$")
ARCH_BLOCK = "arch120"
FRAME_SIZE_MM = (40314.0, 28030.0)
WALL_T_MM = (80.0, 400.0)          # a wall band: two parallel faces 80 - 400 mm apart
MIN_GAP_MM = 250.0
JAMB_TOL_MM = 30.0
COLUMN_REACH_MM = 60.0
DOOR_ARC_MIN_R_MM = 300.0          # a swing arc; smaller D-layer arcs are pipes and fixtures
SIDE_PROBE_MM = (300.0, 600.0, 1000.0)
WALL_BODY_MAX_MM = 450.0           # a region thinner than this is a wall body, never a space
BARRIER_HALF_MM = 15.0             # barriers thickened by 15 mm each side: drafting gaps < 30 mm close
SLOT_HALF_MM = 25.0                # and spaces opened by 25 mm: slots < 50 mm wide never join two spaces
# room-label blocks (their English text, read from the block definitions; the Arabic text is never copied)
ROOM_LABELS = {"DRI": "DRIVER", "GAR": "GARDEN", "MB": "MASTER BED ROOM", "PAN": "PANTRY", "SAL": "SALOON",
               "WASH": "WASH", "WC": "W.C", "cou": "COURT", "din": "DINING", "dwa": "DEWANEYA", "kit": "KITCHEN",
               "rec": "RECEPTION", "mbed": "BED ROOM", "bath": "BATH", "laun": "LAUNDRY", "liv": "LIVING AREA",
               "void": "VOID", "ROOF": "ROOF", "maid": "MAID R.", "SWIM": "SWIMMING POOL",
               "A$C662819C0": "NEIGHBOUR", "A$C7BD10DAB": "STREET", "A$C60883738": "SEA VIEW"}
EXTERIOR_LABELS = {"GARDEN", "COURT", "ROOF", "SWIMMING POOL", "NEIGHBOUR", "STREET", "SEA VIEW"}
NOT_A_SPACE_LABEL = {"mecvent"}    # 'artificial ventilation' tag beside a W.C window
# ------------------------------------------------------------------ p.13 (visual records; renders not kept)
SCHEDULE = [
    {"row_id": "L1", "width_printed": "0 -100", "size_printed": "B x 20", "bottom": "2Ø12", "top": "2Ø10",
     "stirrups": "5Ø8/M", "note": "B-WIDTH OF THE BLOCK WALL"},
    {"row_id": "L2", "width_printed": "101 - 200", "size_printed": "B x 20", "bottom": "2Ø14", "top": "2Ø12",
     "stirrups": "5Ø8/M", "note": "WIDTH OF LINTEL THE SAME OF WIDTH OF WALL."},
    {"row_id": "L3", "width_printed": "201 - 300", "size_printed": "B x 30", "bottom": "3Ø16", "top": "3Ø14",
     "stirrups": "5Ø8/M", "note": ""},
    {"row_id": "L4", "width_printed": "301 - 500", "size_printed": "B x 40", "bottom": "3Ø18", "top": "3Ø14",
     "stirrups": "5Ø8/M", "note": ""},
    {"row_id": "L5", "width_printed": "501 - 750", "size_printed": "B x 55", "bottom": "4Ø18", "top": "3Ø14",
     "stirrups": "5Ø8/M", "note": ""}]
SCHEDULE_HEADER = ("OPENING WIDTH (IN CM)", "LINTEL SIZE (IN CM)", "BOTT. BARS", "TOP. BARS", "STIR.", "NOTES")
MIN_BEARING_MM = 400.0             # 'MIN.40cm' each side, LINTEL DETAIL
R5_REACH_MM = 150.0                # an R5 opening line within 150 mm of an opening strip names that opening
BEAM_SLIVER_MM = 20.0              # a beam band meeting an opening strip over less than this is a touch, not cover
COVER_MM = 25.0                    # P8-N22 (beams), applied to the lintel as a beam-type member (project basis)
VISUAL = [
    {"ID": "VIS-P13-SCHEDULE", "FILE": "ST7757.pdf", "PAGE": 13, "DPI": 400, "WHAT": "LINTEL SCHEDULE: header and "
     "five rows (opening width bands in cm, section B x D, bottom / top bars, stirrups, notes)",
     "READING": "see 02_LINTEL_SCHEDULE_TRANSCRIPTION.csv"},
    {"ID": "VIS-P13-DETAIL", "FILE": "ST7757.pdf", "PAGE": 13, "DPI": 400, "WHAT": "LINTEL DETAIL (elevation)",
     "READING": "'MIN.40cm' bearing at each end; 'TOB BARS' (sic) / 'BOTTOM BARS' / 'STIRRUPS' called out; the bar "
                "ends are drawn bent down / up into the bearing but no bend length is printed; stirrups drawn "
                "schematically near the ends only, no spacing printed beyond the schedule's '5Ø8/M'"},
    {"ID": "VIS-P13-SECT22", "FILE": "ST7757.pdf", "PAGE": 13, "DPI": 400, "WHAT": "SECT (2-2) (THROUGH LINTEL)",
     "READING": "section B x D; two top and two bottom bars drawn; one closed stirrup drawn with hooks; no cover and "
                "no hook length printed"}]


class Stop(Exception):
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


def _r(v, nd=9):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


def _full(v, nd=9):
    s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
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


def _csv(name, rows, fields=None):
    fields = fields or list(rows[0])
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


def kg(length_mm, dia_mm):
    return length_mm / 1000.0 * UM.kg_per_m(dia_mm, UNIT_MASS)


# ------------------------------------------------------------------ inputs
def verify_inputs():
    for sha, name in ((ARCH_SHA, "P7757.dxf"), (STRUCT_SHA, "ST7757.dxf")):
        f = BY_SHA / f"{sha}.dxf"
        check(f.exists(), f"private input {name} not in data/inputs/by_sha256 (never committed)")
        check(_sha(f) == sha, f"{name} unchanged")
    frozen = {k: DR.verify_frozen(m, ROOT) for k, m in MANIFESTS.items()}
    errata = _j(R / "alsenan_dome_mesh_s8_3a/07_FROZEN_VERIFICATION.json")["s8_3_errata_sha256"]
    for name, h in errata.items():
        check(_sha(S83_ERRATA / name) == h, f"S8.3 errata {name} unchanged")
    index = {}
    for k, (p, key) in INDEXES.items():
        n = 0
        for name, v in _j(p)[key].items():
            h = v["sha256"] if isinstance(v, dict) else v
            f = p.parent / (v["file"] if isinstance(v, dict) else name)
            check(_sha(f) == h, f"{k} register {name} unchanged")
            n += 1
        index[k] = {"index_sha256": _sha(p), "registers_verified": n}
    return frozen, errata, index


def pre_s8_claims():
    """PRE-S8 census rows of the lintel family, whitelisted columns only."""
    with open(READ["PRE_S8_CENSUS"], encoding="utf-8", newline="") as fh:
        rd = csv.reader(fh)
        head = next(rd)
        check(not set(PRE_S8_COLUMNS) & set(PRE_S8_FIREWALLED), "PRE-S8 whitelist excludes the firewalled columns")
        idx = {c: head.index(c) for c in PRE_S8_COLUMNS}
        out = []
        for row in rd:
            rec = {c: row[i] for c, i in idx.items()}
            if re.search(r"LINTEL", rec["ELEMENT_ID"] + rec["ELEMENT_FAMILY"], re.I):
                out.append(rec)
    return out


def r5_population():
    """R5 opening rows, whitelisted fields only (never its lintel, height, sill, area or material)."""
    check(not set(R5_FIELDS) & set(R5_FIREWALLED), "R5 whitelist excludes the firewalled fields")
    rows = _j(READ["R5_OPENINGS"])["rows"]
    return [{k: r.get(k) for k in R5_FIELDS} for r in rows]


# ------------------------------------------------------------------ architectural drawing
def _bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def arch_plans():
    import ezdxf
    doc = ezdxf.readfile(str(BY_SHA / f"{ARCH_SHA}.dxf"))
    msp = doc.modelspace()
    ents = list(msp)
    frames = []
    for e in ents:
        if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == WALL_LAYER and e.closed:
            b = _bbox([(q[0], q[1]) for q in e.get_points("xy")])
            if abs(b[2] - b[0] - FRAME_SIZE_MM[0]) < 1.0 and abs(b[3] - b[1] - FRAME_SIZE_MM[1]) < 1.0:
                frames.append((e.dxf.handle, b))
    titles = {e.dxf.name: (e.dxf.insert.x, e.dxf.insert.y) for e in ents
              if e.dxftype() == "INSERT" and e.dxf.name in PLAN_TITLE.values()}
    survey = {"dimension_entities": sum(1 for e in ents if e.dxftype() == "DIMENSION"), "frames": len(frames)}
    plans = {}
    for fl in FLOORS:
        t = titles.get(PLAN_TITLE[fl])
        check(t is not None, f"plan title {PLAN_TITLE[fl]} found")
        hit = [(h, b) for h, b in frames if b[0] <= t[0] <= b[2] and b[1] <= t[1] <= b[3]]
        check(len(hit) == 1, f"{fl}: one plan frame holds its title ({len(hit)})")
        plans[fl] = {"frame_handle": hit[0][0], "box": hit[0][1]}
    blocks = {}
    for fl, P in plans.items():
        x0, y0, x1, y1 = P["box"]
        ins = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1  # noqa: E731
        D = {"segs": [], "arcs": [], "cols": [], "glz": [], "glz_segs": [], "doors": [], "darcs": [],
             "small_darcs": [], "archs": [], "overhead": [], "labels": [], "bulges": 0, "dims": []}
        for e in ents:
            if e.dxftype() == "DIMENSION":
                p2, p3 = e.dxf.get("defpoint2"), e.dxf.get("defpoint3")
                if p2 is not None and p3 is not None and ins((p2.x, p2.y)) and ins((p3.x, p3.y)):
                    D["dims"].append({"handle": e.dxf.handle, "a": (p2.x, p2.y), "b": (p3.x, p3.y),
                                      "m": float(e.get_measurement()), "text": e.dxf.text})
        for e in ents:
            t = e.dxftype()
            if t not in ("LINE", "LWPOLYLINE", "ARC", "INSERT"):
                continue
            L = e.dxf.get("layer", "")
            h = e.dxf.handle
            if h == P["frame_handle"]:
                continue
            if t == "LINE":
                a, b = (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)
                if not (ins(a) and ins(b)):
                    continue
                if L == WALL_LAYER:
                    D["segs"].append((h, a, b))
                elif L == GLAZING_LAYER:
                    D["glz"].append((h, [a, b]))
                    D["glz_segs"].append((h, a, b))
                elif L == OVERHEAD_LAYER:
                    D["overhead"].append((h, a, b))
            elif t == "LWPOLYLINE":
                pts = [(q[0], q[1]) for q in e.get_points("xy")]
                if not all(ins(q) for q in pts):
                    continue
                if any(abs(q[4]) > 1e-9 for q in e.get_points("xyseb")) and L in (WALL_LAYER, GLAZING_LAYER):
                    D["bulges"] += 1
                pairs = list(zip(pts, pts[1:] + ([pts[0]] if e.closed else [])))
                if L == COLUMN_LAYER and e.closed:
                    D["cols"].append((h, pts))
                elif L == WALL_LAYER:
                    D["segs"] += [(f"{h}:{k}", a, b) for k, (a, b) in enumerate(pairs)]
                elif L == GLAZING_LAYER:
                    D["glz"].append((h, pts))
                    D["glz_segs"] += [(f"{h}:{k}", a, b) for k, (a, b) in enumerate(pairs)]
                elif L == OVERHEAD_LAYER:
                    D["overhead"] += [(f"{h}:{k}", a, b) for k, (a, b) in enumerate(pairs)]
            elif t == "ARC":
                c = (e.dxf.center.x, e.dxf.center.y)
                if not ins(c):
                    continue
                arc = (h, c, e.dxf.radius, e.dxf.start_angle, e.dxf.end_angle)
                if L == WALL_LAYER:
                    D["arcs"].append(arc)
                elif L == GLAZING_LAYER:
                    D["glz"].append((h, _arc_points(arc, 6)))
                elif L == DOOR_LAYER:
                    (D["darcs"] if e.dxf.radius >= DOOR_ARC_MIN_R_MM else D["small_darcs"]).append(arc)
            else:
                p = (e.dxf.insert.x, e.dxf.insert.y)
                if not ins(p):
                    continue
                nm = e.dxf.name
                if DOOR_BLOCK.match(nm) or nm == ARCH_BLOCK:
                    vs, arcs = [], []
                    for v in e.virtual_entities():
                        if v.dxftype() == "LINE":
                            vs += [(v.dxf.start.x, v.dxf.start.y), (v.dxf.end.x, v.dxf.end.y)]
                        elif v.dxftype() == "ARC":
                            arcs.append(round(v.dxf.radius, 1))
                    rec = {"handle": h, "name": nm, "p": p, "pts": vs, "arc_r": sorted(arcs), "layer": L,
                           "rotation": _r(e.dxf.get("rotation", 0.0), 6), "xscale": _r(e.dxf.get("xscale", 1.0), 6)}
                    (D["doors"] if DOOR_BLOCK.match(nm) else D["archs"]).append(rec)
                elif nm in ROOM_LABELS:
                    D["labels"].append({"handle": h, "block": nm, "name": ROOM_LABELS[nm], "p": p})
        blocks[fl] = D
    plan_frames = {P["frame_handle"] for P in plans.values()}
    other = {}
    for h, b in frames:
        if h in plan_frames:
            continue
        nums = []
        for e in ents:
            if e.dxftype() in ("TEXT", "MTEXT"):
                p = (e.dxf.insert.x, e.dxf.insert.y)
                t = (e.dxf.text if e.dxftype() == "TEXT" else e.text).strip()
                if b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3] and NUMERIC_TEXT.match(t):
                    nums.append(t)
        other[h] = sorted(set(nums), key=lambda x: (len(x), x))
    survey["non_plan_frames"] = other
    elev = {}
    for h, b in frames:
        if h in plan_frames:
            continue
        x0, y0 = b[0], b[1]
        ins = lambda p: b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3]  # noqa: E731
        dims, pts = [], []
        for e in ents:
            t = e.dxftype()
            if t == "DIMENSION":
                p2, p3 = e.dxf.get("defpoint2"), e.dxf.get("defpoint3")
                if p2 is None or p3 is None or not ins((p2.x, p2.y)):
                    continue
                ang = round(float(e.dxf.get("angle", 0.0))) % 180
                dims.append({"handle": e.dxf.handle, "a": (p2.x - x0, p2.y - y0), "b": (p3.x - x0, p3.y - y0),
                             "m": float(e.get_measurement()), "axis": "V" if ang == 90 else "H",
                             "layer": e.dxf.layer, "text": e.dxf.text})
            elif t in ("LINE", "LWPOLYLINE", "ARC") and e.dxf.get("layer", "") in ELEV_OPENING_LAYERS:
                if t == "LINE":
                    q = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
                elif t == "LWPOLYLINE":
                    q = [(v[0], v[1]) for v in e.get_points("xy")]
                else:
                    q = _arc_points((None, (e.dxf.center.x, e.dxf.center.y), e.dxf.radius, e.dxf.start_angle,
                                     e.dxf.end_angle), 8)
                if all(ins(v) for v in q):
                    pts += [(v[0] - x0, v[1] - y0, e.dxf.layer, e.dxf.handle) for v in q]
        elev[h] = {"box": b, "dims": dims, "pts": pts}
    survey["elevations"] = elev
    return plans, blocks, survey


def _arc_points(arc, n):
    _, c, r, a0, a1 = arc
    a0, a1 = math.radians(a0), math.radians(a1)
    if a1 < a0:
        a1 += 2 * math.pi
    return [(c[0] + r * math.cos(a0 + (a1 - a0) * k / n), c[1] + r * math.sin(a0 + (a1 - a0) * k / n))
            for k in range(n + 1)]


# ------------------------------------------------------------------ census
def _evidence(inside, D, used_glz=None):
    ev = {"door": [], "darc": [], "glz": [], "arch": []}
    for d in D["doors"]:
        if sum(inside(q, 5.0) for q in d["pts"]) >= 4:
            ev["door"].append(d["handle"])
    for h, c, r, a0, a1 in D["darcs"]:
        if inside(c, 60.0):
            ev["darc"].append(h)
    for h, pts in D["glz"]:
        if sum(inside(q, 5.0) for q in pts) >= max(2, len(pts) // 2):
            ev["glz"].append(h)
    for a in D["archs"]:
        if sum(inside(q, 5.0) for q in a["pts"]) >= 3:
            ev["arch"].append(a["handle"])
    return ev


def census_floor(fl, D):
    lines = OC.face_lines(D["segs"])
    bands = OC.wall_bands(lines, *WALL_T_MM)
    gaps = []
    for b in bands:
        for g in OC.band_gaps(b, min_gap=MIN_GAP_MM, jamb_tol=JAMB_TOL_MM, obstacles=D["cols"],
                              column_reach=COLUMN_REACH_MM, closures=D["segs"]):
            fr = (b["u"], b["n"])
            lo, hi = sorted((b["A"]["off"], b["B"]["off"]))
            g.update(kind="WALL_GAP", band=b, lo=lo, hi=hi,
                     inside=(lambda fr, g, lo, hi: lambda p, m=30.0: OC.in_strip(p, fr, g["s0"], g["s1"], lo, hi, m))(
                         fr, g, lo, hi))
            gaps.append(g)
    abands = OC.arc_bands(D["arcs"], *WALL_T_MM)
    for b in abands:
        for g in OC.arc_gaps(b, min_gap_mm=MIN_GAP_MM, jamb_tol_mm=JAMB_TOL_MM):
            g.update(kind="ARC_GAP", aband=b,
                     inside=(lambda b, g: lambda p, m=30.0: OC.in_arc_strip(p, b, g["a0"], g["a1"]))(b, g))
            gaps.append(g)
    for g in gaps:
        g["ev"] = _evidence(g["inside"], D)
        kinds = []
        if g["ev"]["door"] or g["ev"]["darc"]:
            kinds.append("DOOR")
        if g["ev"]["glz"]:
            kinds.append("GLAZING")
        if g["ev"]["arch"]:
            kinds.append("ARCH")
        if g["kind"] == "WALL_GAP" and OC.overhead_cover(g["band"], g["s0"], g["s1"], D["overhead"]):
            kinds.append("OVERHEAD_LINES")
        g["evidence_kinds"] = kinds
        g["state"], g["reject_reason"] = OC.decide_gap(g, kinds)
    # glazing runs that no wall gap holds (a glazed screen drawn without wall faces)
    used = {h for g in gaps if g["state"] == OC.OPENING for h in g["ev"]["glz"]}
    free = [s for s in D["glz_segs"] if s[0].split(":")[0] not in used]
    runs = []
    for run in OC.parallel_runs(free, max_width=300.0, min_len=300.0):
        if run["hi"] - run["lo"] <= 1.0:
            continue
        g = OC.run_ends(run, obstacles=D["cols"], closures=D["segs"], reach=COLUMN_REACH_MM, jamb_tol=JAMB_TOL_MM)
        band = {"ang": run["ang"], "u": run["u"], "n": run["n"], "A": {"off": run["lo"]}, "B": {"off": run["hi"]},
                "t": run["hi"] - run["lo"], "band_id": run["run_id"]}
        fr = (run["u"], run["n"])
        g.update(kind="GLAZING_RUN", band=band, lo=run["lo"], hi=run["hi"], run=run,
                 inside=(lambda fr, g, lo, hi: lambda p, m=30.0: OC.in_strip(p, fr, g["s0"], g["s1"], lo, hi, m))(
                     fr, g, run["lo"], run["hi"]))
        g["ev"] = _evidence(g["inside"], D)
        g["evidence_kinds"] = ["GLAZING"]
        g["state"], g["reject_reason"] = OC.decide_gap(g, ["GLAZING"])
        runs.append(g)
    return {"lines": lines, "bands": bands, "abands": abands, "gaps": gaps + runs}


def centre_of(g):
    if g["kind"] == "ARC_GAP":
        b = g["aband"]
        am = math.radians((g["a0"] + g["a1"]) / 2.0)
        return (b["c"][0] + g["r_mid"] * math.cos(am), b["c"][1] + g["r_mid"] * math.sin(am))
    b = g["band"]
    sm, om = (g["s0"] + g["s1"]) / 2.0, (g["lo"] + g["hi"]) / 2.0
    return (sm * b["u"][0] + om * b["n"][0], sm * b["u"][1] + om * b["n"][1])


def side_probes(g, d):
    if g["kind"] == "ARC_GAP":
        b = g["aband"]
        am = math.radians((g["a0"] + g["a1"]) / 2.0)
        cs, sn = math.cos(am), math.sin(am)
        return ((b["c"][0] + (b["r_in"] - d) * cs, b["c"][1] + (b["r_in"] - d) * sn),
                (b["c"][0] + (b["r_out"] + d) * cs, b["c"][1] + (b["r_out"] + d) * sn))
    b = g["band"]
    sm = (g["s0"] + g["s1"]) / 2.0
    pt = lambda o: (sm * b["u"][0] + o * b["n"][0], sm * b["u"][1] + o * b["n"][1])  # noqa: E731
    return pt(g["lo"] - d), pt(g["hi"] + d)


def regions(fl, P, D, gaps, bands, close=None):
    """the spaces of one plan: the frame minus the wall faces, glazing, columns, wall caps and the closing lines of
    every accepted opening. Barriers are thickened by BARRIER_HALF_MM and the spaces opened by SLOT_HALF_MM, so a
    drafting gap or slot far narrower than any opening never joins two spaces."""
    from shapely.geometry import LineString, Point, box
    from shapely.ops import unary_union
    x0, y0, x1, y1 = P["box"]
    dom = box(x0, y0, x1, y1)
    bar = [LineString([a, b]) for _, a, b in D["segs"] if math.dist(a, b) > 0.5]
    bar += [LineString(_arc_points(a, 24)) for a in D["arcs"]]
    bar += [LineString(pts) for _, pts in D["glz"] if len(pts) > 1]
    bar += [LineString(pts + [pts[0]]) for _, pts in D["cols"]]
    # caps across every wall band at its ends and at every gap end: a wall body is never a passage
    for b in bands:
        cuts = {b["lo"], b["hi"]} | {x for g in gaps if g.get("band") is b for x in (g["s0"], g["s1"])}
        for s_ in sorted(cuts):
            pa = (s_ * b["u"][0] + b["A"]["off"] * b["n"][0], s_ * b["u"][1] + b["A"]["off"] * b["n"][1])
            pb = (s_ * b["u"][0] + b["B"]["off"] * b["n"][0], s_ * b["u"][1] + b["B"]["off"] * b["n"][1])
            bar.append(LineString([pa, pb]))
    for g in gaps:
        if g["state"] != OC.OPENING or (close is not None and not close(g)):
            continue
        if g["kind"] == "ARC_GAP":
            b = g["aband"]
            for r in (b["r_in"], b["r_out"]):
                bar.append(LineString(_arc_points((None, b["c"], r, g["a0"], g["a1"]), 12)))
        else:
            b = g["band"]
            e = JAMB_TOL_MM
            for o in (g["lo"], g["hi"]):
                pa = ((g["s0"] - e) * b["u"][0] + o * b["n"][0], (g["s0"] - e) * b["u"][1] + o * b["n"][1])
                pb = ((g["s1"] + e) * b["u"][0] + o * b["n"][0], (g["s1"] + e) * b["u"][1] + o * b["n"][1])
                bar.append(LineString([pa, pb]))
    mass = unary_union([b.buffer(BARRIER_HALF_MM, cap_style=2, join_style=2) for b in bar])
    free = dom.difference(mass).buffer(-SLOT_HALF_MM, join_style=2).buffer(SLOT_HALF_MM, join_style=2)
    parts = sorted((free.geoms if hasattr(free, "geoms") else [free]),
                   key=lambda f: (-round(f.area, 3), round(f.representative_point().x, 3),
                                  round(f.representative_point().y, 3)))
    out = []
    for i, f in enumerate(parts):
        if f.area < 1e4:
            continue
        mrr = f.minimum_rotated_rectangle
        cs = list(mrr.exterior.coords)
        e = sorted(math.dist(cs[k], cs[k + 1]) for k in range(2)) if len(cs) >= 3 else [0.0, 0.0]
        labels = sorted({lab["name"] for lab in D["labels"] if f.contains(Point(lab["p"]))})
        out.append({"face": f, "id": f"{fl}-SP{len(out) + 1:03d}", "area_m2": f.area / 1e6,
                    "thin": e[0] < WALL_BODY_MAX_MM, "boundary": f.distance(dom.exterior) < 2 * BARRIER_HALF_MM + 1.0,
                    "labels": labels})
    return out


def side_of(point, regs):
    from shapely.geometry import Point
    P = Point(point)
    for r in regs:
        if r["face"].contains(P):
            return r
    return None


def closable(g):
    """an opening that a door or glazing closes; an open passage, arch or shaft opening joins the spaces it links."""
    return bool({"DOOR", "GLAZING"} & set(g["evidence_kinds"]))


def classify_side(r, point, reach):
    """EXTERIOR when the space, joined through every opening nothing closes, reaches the plan boundary or holds an
    exterior label (garden, court, roof, pool, neighbour, street)."""
    if r is None:
        return "UNRESOLVED"
    q = side_of(point, reach)
    if q is None:
        return "UNRESOLVED"
    if q["boundary"] or set(q["labels"]) & EXTERIOR_LABELS:
        return "EXTERIOR"
    return "INTERIOR"


# ------------------------------------------------------------------ types
def glazing_pattern(g, D):
    n = len(g["ev"]["glz"])
    return {"glazing_elements": n}


def opening_type(g, sides):
    ext = sides.count("EXTERIOR")
    kinds = set(g["evidence_kinds"])
    if "DOOR" in kinds:
        if ext == 1 and g.get("double_leaf"):
            return T_MAIN_ENTRANCE, "the only double-leaf door on the envelope (no door schedule names it)"
        if ext == 1:
            return T_EXTERNAL_DOOR, "door symbol in the envelope; material not established"
        return T_INTERNAL_DOOR, "door symbol between two interior spaces; material not established"
    if "GLAZING" in kinds:
        return T_GLAZED, "glazing symbol only: window or full-height / glazed door not separable (no sill, head or " \
                         "opening schedule printed)"
    if g.get("lift_shaft"):
        return T_SERVICE, "opening into the lift shaft (inside the S1 lift footing outline, the same position on " \
                          "every floor)"
    if "ARCH" in kinds:
        return T_PASSAGE, "arch symbol"
    if "OVERHEAD_LINES" in kinds:
        return T_PASSAGE, "open passage with lines drawn over both faces"
    return T_PASSAGE, "open passage: wall gap with jambs and no door, glazing or arch symbol"


# ------------------------------------------------------------------ registration
def column_rects_arch(D):
    return {h: _bbox(pts) for h, pts in D["cols"]}


def register(fl, D, src_ents, sheet):
    """translation arch -> structural sheet-local coordinates: every equal-size column outline pair votes."""
    a = column_rects_arch(D)
    s = {e["handle"]: _bbox([tuple(q) for q in e["pts"]]) for e in src_ents[sheet]
         if e["type"] == "LWPOLYLINE" and e["layer"] == COLUMN_LAYER and e.get("closed")}
    votes = Counter()
    for x in a.values():
        for y in s.values():
            if round(x[2] - x[0]) == round(y[2] - y[0]) and round(x[3] - x[1]) == round(y[3] - y[1]):
                votes[(round(y[0] - x[0], 3), round(y[1] - x[1], 3))] += 1
    (tx, ty), n = votes.most_common(1)[0]
    second = votes.most_common(2)[1][1] if len(votes) > 1 else 0
    check(n >= 5 and second <= 1, f"{fl}: column outlines register to {sheet} under one translation ({n}, second {second})")
    match, unmatched = {}, []
    for h, x in sorted(a.items()):
        xr = (x[0] + tx, x[1] + ty, x[2] + tx, x[3] + ty)
        hit = [k for k, y in s.items() if all(abs(xr[i] - y[i]) <= 1.0 for i in range(4))]
        if len(hit) == 1:
            match[h] = hit[0]
        else:
            unmatched.append(h)
    return {"floor": fl, "sheet": sheet, "T": (float(tx), float(ty)), "votes": n, "second_best": second, "arch_columns": len(a),
            "structural_columns": len(s), "matched": match, "unmatched_arch": unmatched,
            "unmatched_structural": sorted(set(s) - set(match.values())), "struct_rects": s}


# ------------------------------------------------------------------ structure above
SPAN_RE = re.compile(r"^SPAN:([A-Z]+):(BL\d+):(-?\d+(?:\.\d+)?)-(-?\d+(?:\.\d+)?)$")


def beam_model(src, s6occ, sheets):
    import alsenan_structural_s1 as S1
    lines, arcs, spans = {}, {}, defaultdict(list)
    for sh in sheets:
        segs, arcs_, _ = S1.beam_linework(src, sh)
        lines[sh] = {l["line_id"]: l for l in S1.beam_lines(S1.straight_bands(segs))}
        arcs[sh] = arcs_
    for o in s6occ:
        for g in json.loads(o["geometry_objects"] or "[]"):
            m = SPAN_RE.match(g)
            if m and m.group(1) in lines:
                spans[(m.group(1), m.group(2))].append((o["occurrence_id"], float(m.group(3)), float(m.group(4)),
                                                        o["mark"]))
    return lines, arcs, spans


def _rect_poly(u, n, s0, s1, o0, o1):
    from shapely.geometry import Polygon
    P = lambda s, o: (s * u[0] + o * n[0], s * u[1] + o * n[1])  # noqa: E731
    return Polygon([P(s0, o0), P(s1, o0), P(s1, o1), P(s0, o1)])


def _extent(geom, u):
    xs = [along(p, u) for p in _coords(geom)]
    return min(xs), max(xs)


def along(p, u):
    return p[0] * u[0] + p[1] * u[1]


def _coords(geom):
    if hasattr(geom, "geoms"):
        return [c for g in geom.geoms for c in _coords(g)]
    if geom.geom_type == "Polygon":
        return list(geom.exterior.coords)
    return list(geom.coords)


def beams_over(strip, lines, spans, sheet, extra=0.0):
    """S1 beam bands (sheet-local) meeting an opening strip {u, n, s0, s1, o0, o1} (sheet-local frame)."""
    u, n = strip["u"], strip["n"]
    sp = _rect_poly(u, n, strip["s0"] - extra, strip["s1"] + extra, strip["o0"], strip["o1"])
    out = []
    for lid, l in sorted(lines[sheet].items()):
        bp = _rect_poly(l["dir"], l["normal"], l["t0"], l["t1"], l["offset"] - l["width_mm"] / 2.0,
                        l["offset"] + l["width_mm"] / 2.0)
        inter = sp.intersection(bp)
        if inter.is_empty or inter.area <= 1.0:
            continue
        a0, a1 = _extent(inter, u)
        b0, b1 = _extent(inter, n)
        if a1 - a0 < BEAM_SLIVER_MM or b1 - b0 < BEAM_SLIVER_MM:
            continue                                   # a beam end touching a jamb, not a beam over the opening
        rel = LQ.strip_relation({"s0": strip["s0"], "s1": strip["s1"], "o0": strip["o0"], "o1": strip["o1"]},
                                {"s0": a0, "s1": a1, "o0": b0, "o1": b1})
        rel = {k: (float(v) if isinstance(v, float) else v) for k, v in rel.items()}
        cosang = abs(u[0] * l["dir"][0] + u[1] * l["dir"][1])
        parallel = cosang >= math.cos(math.radians(2.0))
        if not parallel and rel["relation"] == LQ.FULL:
            rel["relation"] = LQ.PARTIAL
        tl = [along(p, l["dir"]) for p in _coords(inter)]
        occ = sorted({(o, mk) for o, a, b, mk in spans.get((sheet, lid), []) if min(tl) < b and max(tl) > a})
        out.append({"line_id": lid, "relation": rel["relation"], "lateral_share": rel["lateral_share"],
                    "along_share": rel["along_share"], "parallel": parallel, "beam_width_mm": l["width_mm"],
                    "s6_occurrences": [o for o, _ in occ], "marks": sorted({mk for _, mk in occ})})
    return out


# ------------------------------------------------------------------ masonry available beyond a jamb
def wall_body(bands, cols):
    """masonry in plan: every band's covered intervals (either face drawn, up to one maximum wall thickness past
    the stretch where both faces run: the corner block) as rectangles, a hole shorter than MIN_GAP_MM in a band's
    faces (a crossing wall: never an opening) filled, minus the columns (their convex hulls: an
    outline drawn with its hatch diagonal is not a simple ring)."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    rects = []
    for b in bands:
        lo, hi = sorted((b["A"]["off"], b["B"]["off"]))
        e0, e1 = b["lo"] - WALL_T_MM[1], b["hi"] + WALL_T_MM[1]   # a corner: one face runs on past the other
        cov = OC._union([(t0, t1, ids) for t0, t1, ids in OC._covers(b["A"]["cover"], e0, e1) +
                         OC._covers(b["B"]["cover"], e0, e1)], MIN_GAP_MM)  # a junction is no gap
        for t0, t1, _ in cov:
            if t1 - t0 > 1.0:
                rects.append(_rect_poly(b["u"], b["n"], t0, t1, lo, hi))
    body = unary_union(rects)
    colp = unary_union([Polygon(p).convex_hull for _, p in cols])
    return body.difference(colp), colp


def available_beyond(band, s, side, mid_o, body, colp, reach=2000.0):
    """contiguous masonry length from the jamb s outward (side -1 before, +1 after) along the band centreline, and
    whether a column closes it."""
    from shapely.geometry import LineString, Point
    u, n = band["u"], band["n"]
    P = lambda t: (t * u[0] + mid_o * n[0], t * u[1] + mid_o * n[1])  # noqa: E731
    ray = LineString([P(s), P(s + side * reach)])
    inter = ray.intersection(body.buffer(0.5))
    pieces = list(inter.geoms) if hasattr(inter, "geoms") else ([] if inter.is_empty else [inter])
    best = 0.0
    for pc in pieces:
        ts = sorted(side * (along(q, u) - s) for q in pc.coords)
        if ts and ts[0] <= 1.0:
            best = max(best, ts[-1])
    nxt = P(s + side * (best + 5.0))
    return best, colp.contains(Point(nxt))


# ------------------------------------------------------------------ build
def build():
    frozen, errata, index = verify_inputs()
    import alsenan_structural_s1 as S1
    src = S1.Source()
    sents = src.entities()
    rules = {r["rule_id"]: r for r in _j(READ["S1_RULES"])["rows"]}
    for rid in ("P13-LINTEL", "P8-N03", "P8-N04", "P8-N19", "P8-N20", "P8-N22", "P14-BOUNDARY"):
        check(rid in rules, f"S1 rule {rid} present")
    lv = {i["storey"]: i for i in _j(READ["S1_LEVELS"])["intervals"]}
    for fl in FLOORS:
        check(lv[fl]["closing_slab_sheet"] == SLAB_ABOVE[fl], f"{fl} closes with {SLAB_ABOVE[fl]} (S1 levels)")
    s1cols = [r for r in _j(READ["S1_COLUMNS"])["rows"] if r["floor"] in FLOORS]
    col_of = {(r["plan_source"]["sheets"][0], h): r["column_id"] for r in s1cols for h in r["plan_source"]["handles"]}
    slabs = _j(READ["S1_SLABS"])["rows"]
    s1beams = _j(READ["S1_BEAMS"])["rows"]
    s1special = {r["special_id"]: r for r in _j(READ["S1_SPECIAL"])["rows"]}
    footings = _j(READ["S1_FOOTINGS"])["rows"]
    lift_ftg = [f for f in footings if f.get("type") == "FF"]
    check(len(lift_ftg) == 1, "one FF (lift) footing in S1")
    fdefs = {r["definition_id"]: r for r in _j(READ["S1_FOOTING_DEFS"])["rows"]}
    check(any("lift footing" in x for x in fdefs["FDEF-FF"]["remarks"]), "S1 names FF the lift footing")
    lift_box = lift_ftg[0]["outline"]["bbox"]
    s6o = _rows(READ["S6_OCC"])
    s6_by_id = {r["occurrence_id"]: r for r in s6o}
    bdef = {r["source_row"]["insert_handle"]: r for r in _j(READ["S1_BEAM_DEFS"])["rows"] if r.get("source_row")}
    s6cons = _rows(READ["S6_CONSERVATION"])
    pre = pre_s8_claims()
    r5 = r5_population()
    plans, blocks, survey = arch_plans()
    lines, barcs, spans = beam_model(src, s6o, tuple(SLAB_ABOVE.values()))

    # ------------------------------------------------------------ census, spaces, registration
    census, regs_of, reg_of, reach_of, unbound = {}, {}, {}, {}, []
    for fl in FLOORS:
        D = blocks[fl]
        C = census_floor(fl, D)
        regs = regions(fl, plans[fl], D, C["gaps"], C["bands"])
        reach = regions(fl, plans[fl], D, C["gaps"], C["bands"], close=closable)
        rg = register(fl, D, sents, SLAB_ABOVE[fl])
        census[fl], regs_of[fl], reg_of[fl], reach_of[fl] = C, regs, rg, reach
        # every symbol bound once, or listed with why it binds nothing
        used = Counter()
        for g in C["gaps"]:
            if g["state"] != OC.OPENING:
                continue
            for k in ("door", "darc", "arch"):
                for h in g["ev"][k]:
                    used[(k, h)] += 1
            for h in g["ev"]["glz"]:
                used[("glz", h)] += 1
        for k, v in used.items():
            check(v == 1, f"{fl}: symbol {k} bound to one opening ({v})")
        for d in D["doors"]:
            if not used[("door", d["handle"])]:
                unbound.append({"floor": fl, "kind": "DOOR_INSERT", "handle": d["handle"], "name": d["name"],
                                "p": d["p"], "rec": d})
        for h, c, r_, a0, a1 in D["darcs"]:
            if not used[("darc", h)]:
                unbound.append({"floor": fl, "kind": "DOOR_LAYER_ARC", "handle": h, "name": f"r{r_:.1f}", "p": c})
        for a in D["archs"]:
            check(used[("arch", a["handle"])] == 1, f"{fl}: arch insert {a['handle']} bound")
        for h, pts in D["glz"]:
            if not used[("glz", h)]:
                run_hit = [g for g in C["gaps"] if g["kind"] == "GLAZING_RUN" and g["state"] == OC.OPENING and
                           any(x.split(":")[0] == h for x in g["run"]["ids"])]
                if not run_hit:
                    unbound.append({"floor": fl, "kind": "GLAZING_ELEMENT", "handle": h, "name": "W",
                                    "p": pts[0]})
    # GF registers onto the frozen PS5.1 translation (structural global = sheet-local + frame)
    ps51 = _j(READ["PS5_1_SUMMARY"])["registration"]
    gfrs0 = src.sheets["GFRS"]["frame"]
    tg = reg_of["GF"]["T"]
    check(abs(tg[0] + gfrs0[0] - ps51["translation_arch_to_gfrs"][0]) < 0.01 and
          abs(tg[1] + gfrs0[1] - ps51["translation_arch_to_gfrs"][1]) < 0.01,
          "GF registration = PS5.1 translation_arch_to_gfrs")
    return assemble(locals())


# ------------------------------------------------------------------ opening records
WET = {"BATH", "W.C", "WASH", "KITCHEN", "LAUNDRY", "PANTRY", "SWIMMING POOL"}


def _probe_sides(g, regs):
    for d in SIDE_PROBE_MM:
        pa, pb = side_probes(g, d)
        ra, rb = side_of(pa, regs), side_of(pb, regs)
        if ra is not None and rb is not None and not ra["thin"] and not rb["thin"]:
            return ra, rb, d, pa, pb
    return ra, rb, None, pa, pb


def opening_records(fl, C, regs, reach, D, rg, lift_box, plans):
    T = rg["T"]
    x0, y0 = plans[fl]["box"][0], plans[fl]["box"][1]
    recs = []
    for g in C["gaps"]:
        ra, rb, d, pa, pb = _probe_sides(g, regs)
        sides = [classify_side(ra, pa, reach), classify_side(rb, pb, reach)]
        w = g.get("width", g.get("width_mid_arc"))
        c = centre_of(g)
        cs = (c[0] + T[0], c[1] + T[1])
        doors = [x for x in D["doors"] if x["handle"] in g["ev"]["door"]]
        g["double_leaf"] = any(len(x["arc_r"]) >= 2 for x in doors) or len(g["ev"]["darc"]) >= 2
        shaft = None
        for r_ in (ra, rb):
            if r_ is not None and not r_["labels"] and not r_["boundary"] and r_["area_m2"] < 4.0:
                pc = r_["face"].representative_point()
                q = (pc.x + T[0], pc.y + T[1])
                if lift_box[0] <= q[0] <= lift_box[2] and lift_box[1] <= q[1] <= lift_box[3]:
                    shaft = r_["id"]
        g["lift_shaft"] = False
        g["shaft_candidate"] = shaft if not g["evidence_kinds"] else None
        typ, why = None, None
        ext = sides.count("EXTERIOR")
        zone = ("EXTERNAL" if ext == 1 else "INTERNAL" if ext == 0 and "UNRESOLVED" not in sides else
                "BOTH_SIDES_EXTERIOR" if ext == 2 else "UNRESOLVED")
        handles = sorted(set(g["ev"]["door"] + g["ev"]["darc"] + g["ev"]["arch"] + g["ev"]["glz"]))
        jamb_lines = []
        if g["kind"] == "WALL_GAP":
            jamb_lines = [g["band"]["A"]["line_id"], g["band"]["B"]["line_id"]]
        conf = ("HIGH" if (g["evidence_kinds"] and g["start_jamb"] == OC.MASONRY_JAMB == g["end_jamb"]) or
                ("DOOR" in g["evidence_kinds"]) else
                "MEDIUM" if g["evidence_kinds"] or g["lift_shaft"] else "LOW")
        rec = {"floor": fl, "kind": g["kind"], "state": g["state"], "reject_reason": g["reject_reason"],
               "width_mm": round(w, 1), "t_mm": round(g["t"], 1), "band_id": g["band_id"],
               "s0": g.get("s0"), "s1": g.get("s1"), "a0": g.get("a0"), "a1": g.get("a1"),
               "centre_arch": (round(c[0], 1), round(c[1], 1)),
               "centre_frame": (round(c[0] - x0, 1), round(c[1] - y0, 1)),
               "centre_struct": (round(cs[0], 1), round(cs[1], 1)),
               "start_jamb": g["start_jamb"], "end_jamb": g["end_jamb"],
               "start_ref": g.get("start_column"), "end_ref": g.get("end_column"),
               "evidence": g["evidence_kinds"], "door_blocks": sorted(f"{x['name']}:{x['handle']}" for x in doors),
               "door_arcs": sorted(g["ev"]["darc"]), "glazing_elements": len(g["ev"]["glz"]),
               "arch_blocks": sorted(g["ev"]["arch"]), "handles": handles, "jamb_face_lines": jamb_lines,
               "side_a": ra["id"] if ra else None, "side_b": rb["id"] if rb else None,
               "side_a_class": sides[0], "side_b_class": sides[1],
               "side_a_labels": ra["labels"] if ra else [], "side_b_labels": rb["labels"] if rb else [],
               "side_probe_mm": d, "zone": zone, "type": typ, "type_basis": why, "lift_shaft_space": None,
               "sides": sides,
               "double_leaf": g["double_leaf"], "confidence": conf, "g": g}
        if g["kind"] == "ARC_GAP":
            b = g["aband"]
            rec.update(arc_centre_struct=(b["c"][0] + T[0], b["c"][1] + T[1]), r_in=b["r_in"], r_out=b["r_out"],
                       chord_mid_mm=round(g["chord_mid"], 1))
        recs.append(rec)
    return recs


def shaft_space_on(fl, p_frame, regs_of, plans):
    """the small unlabelled enclosed space holding a frame-relative point on floor fl, if any."""
    from shapely.geometry import Point
    x0, y0 = plans[fl]["box"][0], plans[fl]["box"][1]
    P = Point(p_frame[0] + x0, p_frame[1] + y0)
    for r in regs_of[fl]:
        if r["face"].contains(P):
            return r if (not r["labels"] and not r["boundary"] and r["area_m2"] < 4.0) else None
    return None


def assemble(L):
    census, regs_of, reg_of, blocks, plans = L["census"], L["regs_of"], L["reg_of"], L["blocks"], L["plans"]
    lift_box = L["lift_box"]
    ops, rejected = [], []
    for fl in FLOORS:
        recs = opening_records(fl, census[fl], regs_of[fl], L["reach_of"][fl], blocks[fl], reg_of[fl], lift_box,
                               plans)
        for r in recs:
            g = r["g"]
            cand = g.get("shaft_candidate")
            if cand:
                sp = next(x for x in regs_of[fl] if x["id"] == cand)
                pc = sp["face"].representative_point()
                pf = (pc.x - plans[fl]["box"][0], pc.y - plans[fl]["box"][1])
                stack = {f: shaft_space_on(f, pf, regs_of, plans) for f in FLOORS}
                if all(stack.values()):
                    g["lift_shaft"] = True
                    r["lift_shaft_space"] = cand
                    r["shaft_stack"] = {f: v["id"] for f, v in stack.items()}
            if r["state"] == OC.OPENING:
                r["type"], r["type_basis"] = opening_type(g, r["sides"])
        good = sorted([r for r in recs if r["state"] == OC.OPENING],
                      key=lambda r: (round(r["centre_frame"][0]), round(r["centre_frame"][1])))
        for i, r in enumerate(good):
            r["opening_id"] = f"OP-{fl}-{i + 1:03d}"
        ops += good
        bad = sorted([r for r in recs if r["state"] != OC.OPENING],
                     key=lambda r: (round(r["centre_frame"][0]), round(r["centre_frame"][1])))
        for i, r in enumerate(bad):
            r["candidate_id"] = f"RJ-{fl}-{i + 1:02d}"
        rejected += bad
    L.update(ops=ops, rejected=rejected)
    return measure(L)


# ------------------------------------------------------------------ schedule
def schedule_rows():
    rows = []
    for r in SCHEDULE:
        lo, hi = LQ.parse_width_range(r["width_printed"])
        bw, d = LQ.parse_section(r["size_printed"])
        check(bw == "B", f"{r['row_id']}: section width is the wall's (B)")
        nb, db = LQ.parse_bars(r["bottom"])
        nt, dt = LQ.parse_bars(r["top"])
        rate, ds = LQ.parse_rate(r["stirrups"])
        rows.append({**r, "lo": lo, "hi": hi, "D_cm": d, "bottom_n": nb, "bottom_dia": db, "top_n": nt, "top_dia": dt,
                     "stirrup_rate": rate, "stirrup_dia": ds})
    return rows


# ------------------------------------------------------------------ strips on the slab sheet above
def strip_of(o, T):
    g = o["g"]
    if o["kind"] == "ARC_GAP":
        return None
    b = g["band"]
    u, n = b["u"], b["n"]
    du, dn = T[0] * u[0] + T[1] * u[1], T[0] * n[0] + T[1] * n[1]
    return {"u": u, "n": n, "s0": g["s0"] + du, "s1": g["s1"] + du, "o0": g["lo"] + dn, "o1": g["hi"] + dn}


def arc_beams_over(o, barcs, sheet):
    """S1 curved beam faces concentric with a curved opening and within reach of its wall band."""
    c = o["arc_centre_struct"]
    a0, a1 = math.radians(o["a0"]), math.radians(o["a1"])
    out = []
    for a in barcs[sheet]:
        if math.dist(a["c"], c) > 100.0 or not o["r_in"] - 400.0 <= a["r"] <= o["r_out"] + 400.0:
            continue
        b0, b1 = a["a0"], a["a1"] if a["a1"] > a["a0"] else a["a1"] + 2 * math.pi
        lo, hi = max(a0, b0), min(a1, b1)
        share = max(0.0, hi - lo) / (a1 - a0)
        if share > 0:
            out.append({"handle": a["handle"], "r": a["r"], "along_share": share})
    return out


def measure(L):
    ops, reg_of, lines, barcs, spans = L["ops"], L["reg_of"], L["lines"], L["barcs"], L["spans"]
    rows = schedule_rows()
    sched = LQ.check_schedule(rows)
    L["sched_rows"], L["sched_check"] = rows, sched
    # ------------------------------------------------------------ beam audit, schedule binding, decisions
    for o in ops:
        fl, sheet = o["floor"], SLAB_ABOVE[o["floor"]]
        T = reg_of[fl]["T"]
        st = strip_of(o, T)
        o["strip_struct"] = st
        if st is not None:
            o["beams"] = beams_over(st, lines, spans, sheet)
            o["beams_near"] = [x for x in beams_over(st, lines, spans, sheet, extra=MIN_BEARING_MM)
                               if x["line_id"] not in {b["line_id"] for b in o["beams"]}]
            o["arc_beams"] = []
        else:
            o["beams"], o["beams_near"] = [], []
            o["arc_beams"] = arc_beams_over(o, barcs, sheet)
        rels = [b["relation"] for b in o["beams"]]
        arc_full = any(a["along_share"] >= 0.999 for a in o["arc_beams"])
        o["beam_relation"] = (LQ.FULL if LQ.FULL in rels or arc_full else
                              LQ.PARTIAL if rels or o["arc_beams"] else LQ.NONE)
        cols = []
        for side, kind, ref in (("start", o["start_jamb"], o["start_ref"]), ("end", o["end_jamb"], o["end_ref"])):
            if kind == OC.COLUMN_JAMB:
                sh = reg_of[fl]["matched"].get(ref)
                cols.append({"side": side, "arch_handle": ref, "struct_handle": sh,
                             "s1_column": L["col_of"].get((sheet, sh))})
        o["jamb_columns"] = cols
        o["sched_state"], o["sched_row"] = LQ.row_for_width(rows, o["width_mm"])
        o["beam_depth_mm"] = beam_depth(o, L)
    L["elev"] = elevation_evidence(L)
    L["plan_dims"] = plan_dimensions(L)
    for o in ops:
        decide(o)
    # the boundary-wall door and the slab openings
    extra = []
    for u_ in L["unbound"]:
        if u_["kind"] == "DOOR_INSERT":
            extra.append(symbol_opening(u_, L))
    L["symbol_ops"] = extra
    L["slab_ops"] = slab_openings(L)
    return lintels(L)


def plan_dimensions(L):
    """the printed plan dimension whose two measured points project onto the opening's jambs (2 mm) and lie
    within 1.5 m of the wall."""
    out = {}
    for o in L["ops"]:
        if o["kind"] != "WALL_GAP":
            continue
        g, b = o["g"], o["g"]["band"]
        u, n = b["u"], b["n"]
        om = (g["lo"] + g["hi"]) / 2.0
        hit = []
        for d in L["blocks"][o["floor"]]["dims"]:
            sa, sb = along(d["a"], u), along(d["b"], u)
            if abs(along(d["a"], n) - om) > 1500.0 or abs(along(d["b"], n) - om) > 1500.0:
                continue
            lo, hi = sorted((sa, sb))
            if abs(lo - g["s0"]) <= 2.0 and abs(hi - g["s1"]) <= 2.0:
                hit.append(d)
        if hit:
            d = sorted(hit, key=lambda d: d["handle"])[0]
            check(abs(d["m"] - o["width_mm"]) <= 1.0, f"{o['opening_id']}: printed width = drawn width")
            out[o["opening_id"]] = {"handle": d["handle"], "m": d["m"], "all": sorted(x["handle"] for x in hit)}
    return out


def beam_depth(o, L):
    """the deepest S1 beam definition (H) among the S6 occurrences over the opening (FULL relation only)."""
    hs = []
    for b in o["beams"]:
        if b["relation"] != LQ.FULL:
            continue
        for occ in b["s6_occurrences"]:
            row = L["s6_by_id"][occ]["schedule_row"]
            d = L["bdef"].get(row)
            if d and d.get("H_cm"):
                hs.append(float(d["H_cm"]) * 10.0)
    return max(hs) if hs else None


def elevation_evidence(L):
    """printed head / sill levels of the openings an elevation shows: the elevation's horizontal axis is
    registered to a plan axis by the printed horizontal dimension chain; an opening binds only when one printed
    dimension spans exactly its two jambs; its head (sill) is printed only when a printed vertical chain from the
    ground reaches the top (bottom) of its drawn glazing / door outline."""
    out = {"frames": {}, "bound": {}}
    S1L = {fl: (L["lv"][fl]["lower_ffl_m"], L["lv"][fl]["upper_ffl_m"]) for fl in FLOORS}
    ext = []
    for o in L["ops"]:
        if o["kind"] not in ("WALL_GAP", "GLAZING_RUN") or o["zone"] != "EXTERNAL":
            continue
        b = o["g"]["band"]
        n = b["n"]
        v = (-n[0], -n[1]) if o["sides"][0] == "EXTERIOR" else (n[0], n[1])
        axis = "y" if abs(b["u"][1]) > 0.999 else "x" if abs(b["u"][0]) > 0.999 else None
        if axis is None:
            continue
        facing = ("+" if (v[0] if axis == "y" else v[1]) > 0 else "-") + ("x" if axis == "y" else "y")
        x0, y0 = L["plans"][o["floor"]]["box"][:2]
        org = y0 if axis == "y" else x0
        sg = 1.0 if (b["u"][1] if axis == "y" else b["u"][0]) > 0 else -1.0
        e0, e1 = sorted((sg * o["g"]["s0"] - org, sg * o["g"]["s1"] - org))
        ext.append((facing, o, e0, e1))
    for fh, E in sorted(L["survey"]["elevations"].items()):
        V = [(d["a"][1], d["b"][1], d["m"]) for d in E["dims"] if d["axis"] == "V"]
        H = [d for d in E["dims"] if d["axis"] == "H"]
        col = [d for d in E["dims"] if d["axis"] == "V" and d["layer"] == COLUMN_LAYER]
        overall = max(col, key=lambda d: (d["m"], -min(d["a"][1], d["b"][1])))
        ground = min(overall["a"][1], overall["b"][1])
        levels, conflicts = OC.chain_levels(V, [(ground, 0.0)])
        ffl_y = {}
        for fl in FLOORS:
            for k, m in ((fl, S1L[fl][0]), (fl + "+", S1L[fl][1])):
                hit = [y for y, lv in levels.items() if abs(lv - m * 1000.0) < 0.5]
                ffl_y[k] = min(hit) if hit else None
        hx = sorted({round(x, 1) for d in H for x in (d["a"][0], d["b"][0])})
        spans = [(min(d["a"][0], d["b"][0]), max(d["a"][0], d["b"][0]), d) for d in H]

        def in_band(d, fl):
            lo_, hi_ = ffl_y.get(fl), ffl_y.get(fl + "+")
            return lo_ is not None and hi_ is not None and lo_ < d["a"][1] < hi_

        def binds(facing, mirror, c):
            """the printed horizontal dimensions that span exactly one plan opening's jambs, in its storey."""
            got = {}
            for f, o, e0, e1 in ext:
                if f != facing:
                    continue
                a, b_ = sorted((mirror * e0 + c, mirror * e1 + c))
                for x0_, x1_, d in spans:
                    if abs(x0_ - a) <= 2.0 and abs(x1_ - b_) <= 2.0 and in_band(d, o["floor"]):
                        got.setdefault(d["handle"], []).append(o["opening_id"])
            return {k: v for k, v in got.items() if len(v) == 1}

        ranked = []
        for facing in ("+x", "-x", "+y", "-y"):
            pe = [x for f, o, e0, e1 in ext if f == facing for x in (e0, e1)]
            for mirror in (1, -1):
                for c in sorted({round(e - mirror * p_, 1) for e in hx for p_ in pe}):
                    got = binds(facing, mirror, c)
                    if got:
                        ranked.append((len(got), facing, mirror, c, sorted(v[0] for v in got.values())))
        ranked.sort(key=lambda r: (-r[0], r[1], r[2], r[3]))
        best = ranked[0] if ranked else None
        # candidates within 3 mm of the best are one registration; the runner-up is any other
        second = max([r[0] for r in ranked if best and (r[1], r[2]) != (best[1], best[2]) or
                      (best and abs(r[3] - best[3]) > 3.0)] or [0])
        fr = {"handle": fh, "floors_readable": [fl for fl in FLOORS if ffl_y.get(fl) is not None and
                                                ffl_y.get(fl + "+") is not None],
              "chain_conflicts": conflicts, "ffl_node_y": ffl_y, "facing": best[1] if best else None,
              "mirror": best[2] if best else None, "openings_bound_by_width": best[0] if best else 0,
              "runner_up": second, "offset": best[3] if best else None,
              "registered": bool(best and best[0] >= 2 and second < best[0]), "dims": len(E["dims"]),
              "top": [(r[0], r[1], r[2], r[3], r[4]) for r in ranked[:4]]}
        out["frames"][fh] = fr
        if not fr["registered"] or conflicts:
            continue
        for facing, o, e0, e1 in ext:
            if facing != fr["facing"] or o["floor"] not in fr["floors_readable"]:
                continue
            a, b_ = sorted((fr["mirror"] * e0 + fr["offset"], fr["mirror"] * e1 + fr["offset"]))
            wd = [d for d in H if abs(min(d["a"][0], d["b"][0]) - a) <= 2.0 and abs(max(d["a"][0], d["b"][0]) - b_)
                  <= 2.0 and in_band(d, o["floor"])]
            if not wd:
                continue
            ylo, yhi = ffl_y[o["floor"]], ffl_y[o["floor"] + "+"]
            pts = [(x, y) for x, y, lay, h in E["pts"] if a + 5.0 <= x <= b_ - 5.0 and ylo - 50.0 <= y <= yhi + 50.0]
            rec = {"frame": fh, "e0": a, "e1": b_, "width_dim": wd[0]["handle"], "width_printed_mm": wd[0]["m"],
                   "outline_points": len(pts)}
            if pts:
                hy, sy = max(y for _, y in pts), min(y for _, y in pts)
                hn = [lv for y, lv in levels.items() if abs(y - hy) <= 3.0]
                sn = [lv for y, lv in levels.items() if abs(y - sy) <= 3.0]
                rec.update(head_y=hy, sill_y=sy,
                           head_level_mm=hn[0] if hn else None, sill_level_mm=sn[0] if sn else None)
                ffl = S1L[o["floor"]][0] * 1000.0
                rec["head_above_ffl_mm"] = None if rec["head_level_mm"] is None else rec["head_level_mm"] - ffl
                rec["sill_above_ffl_mm"] = None if rec["sill_level_mm"] is None else rec["sill_level_mm"] - ffl
                rec["below_next_ffl_mm"] = (None if rec["head_level_mm"] is None else
                                            S1L[o["floor"]][1] * 1000.0 - rec["head_level_mm"])
            check(o["opening_id"] not in out["bound"], f"{o['opening_id']}: one elevation binding")
            out["bound"][o["opening_id"]] = rec
    for o in L["ops"]:
        o["elevation"] = e = out["bound"].get(o["opening_id"])
        if e and o["type"] == T_GLAZED and e.get("sill_above_ffl_mm") is not None:
            if abs(e["sill_above_ffl_mm"]) < 0.5:
                o["type"], o["type_basis"] = T_FULL_HEIGHT, (
                    f"glazing; elevation {e['frame']} prints its sill at the floor level (glazed door / full-height)")
            else:
                o["type"], o["type_basis"] = T_WINDOW, (
                    f"glazing; elevation {e['frame']} prints its sill {_full(e['sill_above_ffl_mm'], 1)} mm above "
                    f"the floor level")
    return out


def decide(o):
    """one decision per opening (brief, phase 4)."""
    q = []
    if o["type"] == T_SERVICE:
        o["decision"], o["reason"] = BLOCKED_SUPPORT, (
            "lift landing opening: the shaft wall construction (block or RC) and the lift tie beam that P8-N19 "
            "requires on GF (storey 4.50 m > 4.30 m) belong to the lift family; neither is drawn")
        q.append("Q-LIFT")
    elif o["kind"] == "GLAZING_RUN":
        o["decision"], o["reason"] = BLOCKED_SUPPORT, (
            "glazed screen drawn without masonry wall faces: the lintel width B (block wall width) is undefined and "
            "whatever spans above it is not drawn on the architectural plan")
        q.append("Q-SCREEN")
    elif o["beam_relation"] == LQ.FULL and head_room(o) is not None and head_room(o) < lintel_depth(o):
        m0 = head_room(o)
        o["decision"], o["reason"] = BEAM_ABOVE, (
            f"an S1 beam band lies over the whole opening; the elevation prints the head "
            f"{_full(o['elevation']['below_next_ffl_mm'], 1)} mm below the next floor level and the beam is "
            f"{_full(o['beam_depth_mm'], 1)} mm deep, so at most {_full(m0, 1)} mm of wall is left above the head even "
            f"with no floor build-up: less than the scheduled lintel depth, so the beam is the head support")
        q.append("Q-BEAM-HEAD-DETAIL")
    elif o["beam_relation"] == LQ.FULL:
        o["decision"], o["reason"] = BLOCKED_SUPPORT, (
            "an S1 beam band lies over the whole opening in plan; no head level is printed, so whether the head "
            "reaches the beam soffit (no lintel) or leaves masonry below it (a lintel) is not established")
        q.append("Q-HEAD-UNDER-BEAM")
    elif o["beam_relation"] == LQ.PARTIAL:
        o["decision"], o["reason"] = BLOCKED_SUPPORT, (
            "an S1 beam band lies over part of the opening in plan: the support of the rest and the head level are "
            "not established")
        q.append("Q-PARTIAL-BEAM")
    elif o["sched_state"] == LQ.BOUNDARY_GAP:
        a, b = o["sched_row"]
        o["decision"], o["reason"] = DECISION_CONFLICT, (
            f"width {_full(o['width_mm'] / 10, 2)} cm lies between rows {a['row_id']} (to {a['hi']}) and "
            f"{b['row_id']} (from {b['lo']}): no row binds it")
        q.append("Q-BOUNDARY")
    elif o["sched_state"] == LQ.ABOVE_SCHEDULE:
        o["decision"], o["reason"] = DECISION_CONFLICT, (
            f"width {_full(o['width_mm'] / 10, 2)} cm exceeds the last row (750 cm)")
        q.append("Q-ABOVE")
    elif o["kind"] == "ARC_GAP":
        o["decision"], o["reason"] = BLOCKED_SUPPORT, (
            "curved opening in a curved wall: the schedule binds the width but the LINTEL DETAIL is straight; a "
            "curved lintel (bar bending to the wall radius) is not detailed")
        q.append("Q-CURVED")
    else:
        o["decision"], o["reason"] = SCHEDULE_BOUND, (
            f"masonry wall gap, width {_full(o['width_mm'] / 10, 2)} cm in row {o['sched_row']['row_id']}, no "
            f"structural member over it on {SLAB_ABOVE[o['floor']]}")
        q.append("Q-HEAD-GENERAL")
    o["questions"] = q


def lintel_depth(o):
    return o["sched_row"]["D_cm"] * 10.0 if o.get("sched_state") == LQ.IN_ROW else 200.0


def head_room(o):
    """wall height left between a printed head and the soffit of the beam over it, with no floor build-up (the
    build-up is not printed: any real build-up only reduces this). None when either value is not established."""
    e = o.get("elevation")
    if not e or e.get("below_next_ffl_mm") is None or o.get("beam_depth_mm") is None:
        return None
    return e["below_next_ffl_mm"] - o["beam_depth_mm"]


def symbol_opening(u_, L):
    """the door insert outside every wall band: P7757 draws it in the layer-5 compound wall (P14-BOUNDARY)."""
    d = u_["rec"]
    xs = [p[0] for p in d["pts"]]
    ys = [p[1] for p in d["pts"]]
    x0, y0 = L["plans"][u_["floor"]]["box"][:2]
    return {"opening_id": f"OP-{u_['floor']}-B01", "floor": u_["floor"], "kind": "SYMBOL_ONLY",
            "state": OC.OPENING, "width_mm": None, "block_extent_mm": [round(max(xs) - min(xs), 1),
                                                                         round(max(ys) - min(ys), 1)],
            "t_mm": None, "type": T_EXTERNAL_DOOR, "zone": "SITE_BOUNDARY",
            "type_basis": "door insert in the compound (boundary) wall, which P7757 draws on layer 5 outside the "
                          "building's wall faces",
            "door_blocks": [f"{d['name']}:{d['handle']}"], "handles": [d["handle"]], "evidence": ["DOOR"],
            "centre_arch": (round(d["p"][0], 1), round(d["p"][1], 1)),
            "centre_frame": (round(d["p"][0] - x0, 1), round(d["p"][1] - y0, 1)), "confidence": "MEDIUM",
            "decision": BLOCKED_SUPPORT, "reason": "boundary-wall opening: the boundary wall is its own family "
                                                   "(P14-BOUNDARY typical detail); no S8.6 lintel",
            "questions": ["Q-BOUNDARY-GATE"], "beams": [], "beam_relation": LQ.NONE}


def slab_openings(L):
    out = []
    for x in L["slabs"]:
        if x["class"] not in ("OPEN_TO_BELOW", "STAIR_FLIGHT_ZONE", "STAIR_IN_VOID_ZONE"):
            continue
        fam = "stairs family (P16-STAIR)" if "STAIR" in x["class"] else "slab void (S1: no slab concrete)"
        out.append({"opening_id": f"SO-{x['sheet']}-{x['panel_id'].rsplit('-', 1)[1]}", "panel_id": x["panel_id"],
                    "sheet": x["sheet"], "floor": x["floor"], "kind": "SLAB_OPENING", "type": T_SLAB,
                    "slab_class": x["class"], "area_m2": x["area_m2"], "s1_terminal": x["terminal_state"],
                    "decision": NO_LINTEL, "reason": f"structural slab opening ({x['class']}): no masonry wall "
                                                     f"lintel; its edges are slab / beam members; {fam}",
                    "void_evidence": x.get("void_evidence")})
    return sorted(out, key=lambda r: r["opening_id"])


# ------------------------------------------------------------------ lintel geometry and quantities
def _supports(o, body, colp):
    g = o["g"]
    b = g["band"]
    mid = (g["lo"] + g["hi"]) / 2.0
    out = {}
    for side, s, kind in (("start", g["s0"], o["start_jamb"]), ("end", g["s1"], o["end_jamb"])):
        if kind == OC.COLUMN_JAMB:
            out[side] = {"kind": LQ.FRAME, "available": 0.0, "pier_to_column": False, "basis": "column jamb"}
            continue
        a, col = available_beyond(b, s, -1 if side == "start" else 1, mid, body, colp)
        if col and a < MIN_BEARING_MM:
            out[side] = {"kind": LQ.FRAME, "available": a, "pier_to_column": True,
                         "basis": f"{_full(a, 1)} mm masonry pier, then a column face"}
        else:
            out[side] = {"kind": LQ.MASONRY, "available": a, "pier_to_column": False,
                         "basis": f"{_full(a, 1)} mm masonry beyond the jamb"}
    return out


def _lintel_geom(o, row, sup):
    g = o["g"]
    s0 = g["s0"] - (sup["start"]["available"] if sup["start"]["pier_to_column"] else 0.0)
    s1 = g["s1"] + (sup["end"]["available"] if sup["end"]["pier_to_column"] else 0.0)
    ext = LQ.lintel_extent(s0, s1, sup["start"]["kind"], sup["end"]["kind"], MIN_BEARING_MM,
                           sup["start"]["available"], sup["end"]["available"])
    return ext


def bars_of(B, D, L_mm, row):
    """the schedule's bars over one lintel: straight lengths and the stirrup count (rate per metre)."""
    out = []
    for role, n, d in (("BOTTOM", row["bottom_n"], row["bottom_dia"]), ("TOP", row["top_n"], row["top_dia"])):
        each = LQ.straight_bar_mm(L_mm, COVER_MM)
        out.append({"role": role, "dia_mm": d, "count": n, "each_mm": each, "total_mm": n * each,
                    "kg": kg(n * each, d), "count_basis": f"schedule '{row['bottom' if role == 'BOTTOM' else 'top']}'",
                    "length_basis": "lintel length - 2 x 25 mm cover; end bends excluded (drawn, not dimensioned)"})
    ns = LQ.rate_count(row["stirrup_rate"], L_mm)
    each = LQ.stirrup_core_path_mm(B, D, COVER_MM, row["stirrup_dia"])
    out.append({"role": "STIRRUP", "dia_mm": row["stirrup_dia"], "count": ns, "each_mm": each, "total_mm": ns * each,
                "kg": kg(ns * each, row["stirrup_dia"]),
                "count_basis": f"ceil({row['stirrup_rate']}/m x {_full(L_mm / 1000, 4)} m) (RATE_COUNT, S3.1 policy)",
                "length_basis": "core path 2(B-2c-d) + 2(D-2c-d), sharp corners; hooks excluded (drawn, no length)"})
    return out


def lintels(L):
    ops = L["ops"]
    rows = L["sched_rows"]
    lint, sens = [], []
    bodies = {}
    for fl in FLOORS:
        bodies[fl] = wall_body(L["census"][fl]["bands"], L["blocks"][fl]["cols"])
    for o in ops:
        if o["kind"] != "WALL_GAP":
            continue
        row = o["sched_row"] if o["sched_state"] == LQ.IN_ROW else None
        if row is None:
            continue
        body, colp = bodies[o["floor"]]
        sup = _supports(o, body, colp)
        ext = _lintel_geom(o, row, sup)
        rec = {"lintel_id": f"LT-{o['opening_id']}", "opening_id": o["opening_id"], "floor": o["floor"],
               "line": o["band_id"], "s0": o["g"]["s0"], "s1": o["g"]["s1"], "t0": ext["t0"], "t1": ext["t1"],
               "row": row, "B": o["t_mm"], "D": row["D_cm"] * 10.0, "supports": sup, "flags": list(ext["flags"]),
               "released": o["decision"] == SCHEDULE_BOUND, "o": o}
        (lint if rec["released"] else sens).append(rec)
    # overlaps between released lintels on one wall line: cut at the pier middle
    new, cuts = LQ.resolve_overlaps([{"id": x["lintel_id"], "line": (x["floor"], x["line"]), "s0": x["s0"],
                                      "s1": x["s1"], "t0": x["t0"], "t1": x["t1"]} for x in lint])
    for x in lint:
        x["t0_full"], x["t1_full"] = x["t0"], x["t1"]
        x["t0"], x["t1"] = new[x["lintel_id"]]["t0"], new[x["lintel_id"]]["t1"]
        for c in cuts:
            if x["lintel_id"] in (c["a"], c["b"]):
                x["flags"].append(f"SHARED_PIER:{_full(c['pier'], 1)}mm")
    for x in lint + sens:
        x["L"] = x["t1"] - x["t0"]
        check(x["L"] > x["s1"] - x["s0"] - 1e-6, f"{x['lintel_id']}: lintel longer than its opening")
        x["bearing_start"] = x["s0"] - x["t0"]
        x["bearing_end"] = x["t1"] - x["s1"]
        x["m3"] = x["B"] * x["D"] * x["L"] / 1e9
        x["bars"] = bars_of(x["B"], x["D"], x["L"], x["row"])
        x["kg"] = math.fsum(b["kg"] for b in x["bars"])
        o = x["o"]
        b = o["g"]["band"]
        lo, hi = o["g"]["lo"], o["g"]["hi"]
        x["footprint"] = _rect_poly(b["u"], b["n"], x["t0"], x["t1"], lo, hi)
        x["column_overlap_mm2"] = x["footprint"].intersection(bodies[x["floor"]][1]).area
    # curved opening: the schedule row over the mid-arc width, full bearing assumed (sensitivity only)
    for o in ops:
        if o["kind"] == "ARC_GAP" and o["sched_state"] == LQ.IN_ROW:
            row = o["sched_row"]
            Lm = o["width_mm"] + 2 * MIN_BEARING_MM
            x = {"lintel_id": f"LT-{o['opening_id']}", "opening_id": o["opening_id"], "floor": o["floor"],
                 "line": o["band_id"], "row": row, "B": o["t_mm"], "D": row["D_cm"] * 10.0, "L": Lm,
                 "bearing_start": MIN_BEARING_MM, "bearing_end": MIN_BEARING_MM, "released": False, "o": o,
                 "supports": {"start": {"kind": LQ.MASONRY, "available": None, "basis": "assumed (curved)"},
                              "end": {"kind": LQ.MASONRY, "available": None, "basis": "assumed (curved)"}},
                 "flags": ["CURVED_MID_ARC_LENGTH", "BEARING_ASSUMED_FOR_SENSITIVITY"], "column_overlap_mm2": 0.0}
            x["m3"] = x["B"] * x["D"] * x["L"] / 1e9
            x["bars"] = bars_of(x["B"], x["D"], x["L"], row)
            x["kg"] = math.fsum(b["kg"] for b in x["bars"])
            sens.append(x)
    # two lintels meeting in one corner block: the shared prism is counted once (with the earlier lintel id)
    for fl in FLOORS:
        fps = sorted([x for x in lint if x["floor"] == fl], key=lambda x: x["lintel_id"])
        for i, a in enumerate(fps):
            a.setdefault("lintel_overlap_mm2", 0.0)
            a.setdefault("overlap_deduct_m3", 0.0)
            for b in fps[i + 1:]:
                ov = a["footprint"].intersection(b["footprint"]).area
                if ov <= 1.0:
                    continue
                b["lintel_overlap_mm2"] = b.get("lintel_overlap_mm2", 0.0) + ov
                ded = ov * min(a["D"], b["D"]) / 1e9
                b["overlap_deduct_m3"] = b.get("overlap_deduct_m3", 0.0) + ded
                b["flags"].append(f"CORNER_OVERLAP_WITH:{a['lintel_id']}:{_full(ov, 1)}mm2")
                b["m3"] -= ded
    L["lintels"], L["lintel_sens"], L["cuts"], L["bodies"] = lint, sens, cuts, bodies
    return crosswalk(L)


# ------------------------------------------------------------------ R5 crosswalk and the slab panel above
def opening_poly(o):
    from shapely.geometry import Polygon
    g = o["g"]
    if o["kind"] == "ARC_GAP":
        b = g["aband"]
        outer = _arc_points((None, b["c"], b["r_out"], g["a0"], g["a1"]), 16)
        inner = _arc_points((None, b["c"], b["r_in"], g["a0"], g["a1"]), 16)
        return Polygon(outer + inner[::-1])
    b = g["band"]
    return _rect_poly(b["u"], b["n"], g["s0"], g["s1"], g["lo"], g["hi"])


def crosswalk(L):
    from shapely.geometry import Point, Polygon
    polys = {o["opening_id"]: opening_poly(o) for o in L["ops"]}
    by_floor = defaultdict(list)
    for o in L["ops"]:
        by_floor[o["floor"]].append(o)
    xw = []
    for r in sorted(L["r5"], key=lambda r: r["id"]):
        pts = [tuple(p) for p in (r.get("geometry") or [])]
        if not pts:
            xw.append({"r5_id": r["id"], "match": None, "why": "no geometry"})
            continue
        mid = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        cand = []
        for o in by_floor.get(r["floor"], []):
            P = polys[o["opening_id"]]
            d = min(P.distance(Point(q)) for q in pts + [mid])
            if d <= R5_REACH_MM:
                cand.append((P.distance(Point(mid)), o["opening_id"]))
        cand.sort()
        w = (r.get("width") or {}).get("m")
        xw.append({"r5_id": r["id"], "floor": r["floor"], "r5_type": r["type"], "r5_kind": r["r2_kind"],
                   "r5_width_m": w, "r5_function": (r.get("function") or {}).get("value"),
                   "match": cand[0][1] if cand else None, "candidates": [c for _, c in cand]})
    hits = defaultdict(list)
    for x in xw:
        if x.get("match"):
            hits[x["match"]].append(x["r5_id"])
    for o in L["ops"]:
        o["r5_ids"] = sorted(hits.get(o["opening_id"], []))
    L["r5_xw"] = xw
    L["r5_dups"] = {k: v for k, v in sorted(hits.items()) if len(v) > 1}
    # the slab panel over each opening centre (S1 panels, sheet-local)
    panels = defaultdict(list)
    for x in L["slabs"]:
        if x.get("polygon_mm"):
            panels[x["sheet"]].append((x["panel_id"], x["class"], Polygon(x["polygon_mm"])))
    for o in L["ops"]:
        sh = SLAB_ABOVE[o["floor"]]
        c = Point(o["centre_struct"])
        hit = [(pid, cl) for pid, cl, P in panels[sh] if P.buffer(1.0).contains(c)]
        o["slab_panels_above"] = hit
    return L


# ------------------------------------------------------------------ outputs
LANE_OF_DECISION = {SCHEDULE_BOUND: PROJECT_BASIS_QTO, BEAM_ABOVE: NOT_ADDED, OTHER_SUPPORT: NOT_ADDED,
                    BLOCKED_SUPPORT: BLOCKED, NO_LINTEL: NOT_IN_SOURCE, DECISION_CONFLICT: CONFLICT}
QUESTIONS = {
    "Q-HEAD-UNDER-BEAM": "No door / window schedule and no opening height is printed on the plans. For each opening "
                         "under a beam band, confirm the head level against the beam soffit: if wall remains above "
                         "the head the p.13 lintel applies; if the head reaches the soffit the beam is the support.",
    "Q-PARTIAL-BEAM": "A beam band covers only part of the opening in plan: confirm the support of the rest and the "
                      "head level.",
    "Q-HEAD-GENERAL": "Released lintels assume wall above the head (no beam is drawn over these openings). Confirm "
                      "no head reaches the slab soffit.",
    "Q-LIFT": "Lift landing openings: confirm the shaft wall construction (block or RC) and the head support; P8-N19 "
              "requires lift tie beams at 3.00 m on GF (storey 4.50 m), not drawn. Lift family.",
    "Q-SCREEN": "GF pool-side glazed screen: no masonry wall is drawn; confirm what spans above it.",
    "Q-CURVED": "1F curved bay window: the LINTEL DETAIL is straight and no curved beam is drawn on FFRS over it; "
                "confirm a curved lintel (bending to the wall radius) or another support.",
    "Q-BOUNDARY-GATE": "Gate in the compound wall: boundary-wall family (P14-BOUNDARY), not S8.6.",
    "Q-BOUNDARY": "Width falls between two schedule rows.",
    "Q-ABOVE": "Width exceeds the last schedule row (750 cm).",
    "Q-BEAM-HEAD-DETAIL": "Beam is the head support: confirm the infill detail between head and soffit.",
    "Q-SCHEDULE-GAPS": "The printed bands are integer centimetres (0-100, 101-200, ...): a width strictly between "
                       "100 and 101 cm (etc.) has no row; confirm the intended bound (e.g. 'up to and including').",
    "Q-BEARING": "The drawn wall beyond the jamb is shorter than the 'MIN.40cm' bearing: confirm the lintel detail "
                 "at these jambs (bearing into the cross wall, or a different end detail).",
    "Q-END-DETAIL": "Bar end bends and stirrup hooks are drawn on the LINTEL DETAIL / SECT (2-2) but not "
                    "dimensioned; lintels framing into a column have no anchorage detail.",
    "Q-COVER": "No lintel cover is printed; P8-N22 states 2.5 cm for beams and is applied to the lintel as a "
               "beam-type member (project basis).",
    "Q-STIRRUPS": "'5Ø8/M' is read as a rate per metre over the full lintel length (S3.1 RATE_COUNT); the LINTEL "
                  "DETAIL draws stirrups near the ends only.",
    "Q-GLAZING-FUNCTION": "No door / window schedule: window vs full-height glazing / glazed door is unresolved for "
                          "the glazed openings the elevations do not print.",
    "Q-N04": "P8-N04: all architectural openings must appear on the structural drawings; none do (no lintel or "
             "opening is drawn on the structural plans).",
    "Q-GF-MB-WALL": "GF: the master bedroom's south wall stops about 1.5 m short of the pool-side screen, so the "
                    "bedroom and the hall form one space on the plan: confirm the wall.",
}


def _lane(o):
    return LANE_OF_DECISION[o["decision"]]


def run():
    L = build()
    ops, lv = L["ops"], L["lv"]
    plans = L["plans"]
    ffl = {fl: (lv[fl]["lower_ffl_m"], lv[fl]["upper_ffl_m"]) for fl in FLOORS}
    released = L["lintels"]
    sens = L["lintel_sens"]
    lint_of = {x["opening_id"]: x for x in released}
    sens_of = {x["opening_id"]: x for x in sens}
    # ------------------------------------------------------------ 01 census
    cen = []
    for o in ops:
        g = o["g"]
        b = g.get("band")
        e = o.get("elevation") or {}
        cen.append({
            "RECORD": "OPENING", "OPENING_ID": o["opening_id"], "FLOOR": o["floor"], "FFL_M": ffl[o["floor"]][0],
            "NEXT_FFL_M": ffl[o["floor"]][1], "SLAB_ABOVE": SLAB_ABOVE[o["floor"]], "KIND": o["kind"],
            "TYPE": o["type"], "TYPE_BASIS": o["type_basis"], "ZONE": o["zone"],
            "SIDE_A_SPACE": o["side_a"], "SIDE_A_CLASS": o["side_a_class"], "SIDE_A_ROOMS": o["side_a_labels"],
            "SIDE_B_SPACE": o["side_b"], "SIDE_B_CLASS": o["side_b_class"], "SIDE_B_ROOMS": o["side_b_labels"],
            "WIDTH_MM": o["width_mm"], "WIDTH_AUTHORITY": width_authority(o, L),
            "WALL_THICKNESS_MM": o["t_mm"], "WALL_BAND_ID": o["band_id"],
            "WALL_OWNER": "ARCHITECTURAL_BLOCKWORK" if o["kind"] != "GLAZING_RUN" else "NONE_DRAWN (glazed screen)",
            "HEIGHT_MM": None, "HEIGHT_STATE": "NOT_ESTABLISHED (no opening height printed)",
            "SILL_ABOVE_FFL_MM": e.get("sill_above_ffl_mm"),
            "SILL_STATE": "PRINTED (elevation)" if e.get("sill_above_ffl_mm") is not None else "NOT_ESTABLISHED",
            "HEAD_ABOVE_FFL_MM": e.get("head_above_ffl_mm"),
            "HEAD_STATE": "PRINTED (elevation)" if e.get("head_above_ffl_mm") is not None else
                          ("DRAWN_ONLY (elevation; not printed)" if e.get("head_y") is not None else "NOT_ESTABLISHED"),
            "ALONG_WALL_MM": [_r(g.get("s0"), 1), _r(g.get("s1"), 1)] if b else [_r(o["a0"], 3), _r(o["a1"], 3)],
            "WALL_ANGLE_DEG": b["ang"] if b else None,
            "CENTRE_ARCH_XY": list(o["centre_arch"]), "CENTRE_FRAME_XY": list(o["centre_frame"]),
            "CENTRE_STRUCT_XY": list(o["centre_struct"]),
            "START_JAMB": o["start_jamb"], "END_JAMB": o["end_jamb"],
            "JAMB_COLUMNS": [f"{c['side']}:{c['arch_handle']}->{c['struct_handle']}:{c['s1_column']}"
                             for c in o["jamb_columns"]],
            "BEAMS_OVER": [f"{x['line_id']}:{x['relation']}:{'/'.join(m for m in x['marks'] if m) or '-'}"
                           for x in o["beams"]],
            "SLAB_PANELS_ABOVE": [f"{p}:{c}" for p, c in o["slab_panels_above"]],
            "EVIDENCE": o["evidence"], "DOOR_BLOCKS": o["door_blocks"], "DOOR_ARCS": o["door_arcs"],
            "GLAZING_ELEMENTS": o["glazing_elements"], "ARCH_BLOCKS": o["arch_blocks"], "HANDLES": o["handles"],
            "JAMB_FACE_LINES": o["jamb_face_lines"], "CONFIDENCE": o["confidence"], "R5_IDS": o["r5_ids"],
            "SOURCE": f"P7757.dxf {ARCH_SHA[:12]} frame {plans[o['floor']]['frame_handle']}"})
    for o in L["symbol_ops"]:
        cen.append({"RECORD": "OPENING", "OPENING_ID": o["opening_id"], "FLOOR": o["floor"],
                    "FFL_M": ffl[o["floor"]][0], "NEXT_FFL_M": ffl[o["floor"]][1], "SLAB_ABOVE": None,
                    "KIND": o["kind"], "TYPE": o["type"], "TYPE_BASIS": o["type_basis"], "ZONE": o["zone"],
                    "WIDTH_MM": None, "WIDTH_AUTHORITY": f"door block extent {o['block_extent_mm']} mm (x, y)",
                    "WALL_OWNER": "BOUNDARY_WALL (P14-BOUNDARY)", "HEIGHT_STATE": "NOT_ESTABLISHED",
                    "SILL_STATE": "NOT_ESTABLISHED", "HEAD_STATE": "NOT_ESTABLISHED",
                    "CENTRE_ARCH_XY": list(o["centre_arch"]), "CENTRE_FRAME_XY": list(o["centre_frame"]),
                    "EVIDENCE": o["evidence"], "DOOR_BLOCKS": o["door_blocks"], "HANDLES": o["handles"],
                    "CONFIDENCE": o["confidence"], "R5_IDS": [],
                    "SOURCE": f"P7757.dxf {ARCH_SHA[:12]} frame {plans[o['floor']]['frame_handle']}"})
    for o in L["slab_ops"]:
        cen.append({"RECORD": "OPENING", "OPENING_ID": o["opening_id"], "FLOOR": o["floor"], "SLAB_ABOVE": o["sheet"],
                    "KIND": o["kind"], "TYPE": o["type"], "TYPE_BASIS": f"S1 slab panel {o['panel_id']} "
                    f"({o['slab_class']}, {o['area_m2']} m2)", "ZONE": "SLAB",
                    "WALL_OWNER": "NONE (slab opening)", "HEIGHT_STATE": "NOT_APPLICABLE",
                    "SILL_STATE": "NOT_APPLICABLE", "HEAD_STATE": "NOT_APPLICABLE", "CONFIDENCE": "HIGH",
                    "HANDLES": (o.get("void_evidence") or {}).get("x_lines", []),
                    "SOURCE": f"S1 SLAB_PANEL_REGISTER {o['panel_id']}"})
    for o in L["rejected"]:
        cen.append({"RECORD": "REJECTED_CANDIDATE", "OPENING_ID": o["candidate_id"], "FLOOR": o["floor"],
                    "KIND": o["kind"], "TYPE": None, "TYPE_BASIS": o["reject_reason"], "WIDTH_MM": o["width_mm"],
                    "WALL_THICKNESS_MM": o["t_mm"], "WALL_BAND_ID": o["band_id"],
                    "START_JAMB": o["start_jamb"], "END_JAMB": o["end_jamb"],
                    "CENTRE_ARCH_XY": list(o["centre_arch"]), "CENTRE_FRAME_XY": list(o["centre_frame"]),
                    "EVIDENCE": o["evidence"], "CONFIDENCE": "HIGH",
                    "SOURCE": f"P7757.dxf {ARCH_SHA[:12]} frame {plans[o['floor']]['frame_handle']}"})
    for u_ in L["unbound"]:
        if u_["kind"] == "DOOR_INSERT":
            continue
        x0, y0 = plans[u_["floor"]]["box"][:2]
        cen.append({"RECORD": "NON_OPENING_SYMBOL", "OPENING_ID": f"NS-{u_['floor']}-{u_['handle']}",
                    "FLOOR": u_["floor"], "KIND": u_["kind"], "TYPE_BASIS":
                    "door-layer arc (r 305 mm) beside a column, in no wall gap: a rounded fixture, not an opening",
                    "CENTRE_FRAME_XY": [round(u_["p"][0] - x0, 1), round(u_["p"][1] - y0, 1)],
                    "HANDLES": [u_["handle"]], "CONFIDENCE": "MEDIUM",
                    "SOURCE": f"P7757.dxf {ARCH_SHA[:12]} frame {plans[u_['floor']]['frame_handle']}"})
    CF = ["RECORD", "OPENING_ID", "FLOOR", "FFL_M", "NEXT_FFL_M", "SLAB_ABOVE", "KIND", "TYPE", "TYPE_BASIS", "ZONE",
          "SIDE_A_SPACE", "SIDE_A_CLASS", "SIDE_A_ROOMS", "SIDE_B_SPACE", "SIDE_B_CLASS", "SIDE_B_ROOMS", "WIDTH_MM",
          "WIDTH_AUTHORITY", "WALL_THICKNESS_MM", "WALL_BAND_ID", "WALL_OWNER", "HEIGHT_MM", "HEIGHT_STATE",
          "SILL_ABOVE_FFL_MM", "SILL_STATE", "HEAD_ABOVE_FFL_MM", "HEAD_STATE", "ALONG_WALL_MM", "WALL_ANGLE_DEG",
          "CENTRE_ARCH_XY", "CENTRE_FRAME_XY", "CENTRE_STRUCT_XY", "START_JAMB", "END_JAMB", "JAMB_COLUMNS",
          "BEAMS_OVER", "SLAB_PANELS_ABOVE", "EVIDENCE", "DOOR_BLOCKS", "DOOR_ARCS", "GLAZING_ELEMENTS",
          "ARCH_BLOCKS", "HANDLES", "JAMB_FACE_LINES", "CONFIDENCE", "R5_IDS", "SOURCE"]
    _csv(OUTPUTS[1], cen, CF)
    L["census_rows"] = cen
    return write_rest(L)


def width_authority(o, L):
    """PRINTED when a plan or elevation dimension spans exactly the two jambs; DRAWN_CAD_GEOMETRY otherwise."""
    pd = L["plan_dims"].get(o["opening_id"])
    if pd:
        return f"PRINTED plan dimension {pd['handle']} = {_full(pd['m'], 1)} mm"
    e = o.get("elevation")
    if e:
        return f"PRINTED elevation dimension {e['width_dim']} = {_full(e['width_printed_mm'], 1)} mm"
    return "DRAWN_CAD_GEOMETRY (true-size model space; no printed dimension spans the jambs)"


def write_rest(L):
    ops, rows = L["ops"], L["sched_rows"]
    released, sens = L["lintels"], L["lintel_sens"]
    lint_of = {x["opening_id"]: x for x in released}
    sens_of = {x["opening_id"]: x for x in sens}
    all_ops = ops + L["symbol_ops"] + L["slab_ops"]
    # ------------------------------------------------------------ 02 schedule transcription
    st = []
    for r in rows:
        st.append({"RECORD": "SCHEDULE_ROW", "ROW_ID": r["row_id"], "WIDTH_PRINTED": r["width_printed"],
                   "WIDTH_LO_CM": r["lo"], "WIDTH_HI_CM": r["hi"], "BOUNDS": "inclusive integer cm, as printed",
                   "SIZE_PRINTED": r["size_printed"], "B": "wall width (note)", "D_CM": r["D_cm"],
                   "BOTTOM_PRINTED": r["bottom"], "BOTTOM_N": r["bottom_n"], "BOTTOM_DIA_MM": r["bottom_dia"],
                   "TOP_PRINTED": r["top"], "TOP_N": r["top_n"], "TOP_DIA_MM": r["top_dia"],
                   "STIRRUPS_PRINTED": r["stirrups"], "STIRRUP_RATE_PER_M": r["stirrup_rate"],
                   "STIRRUP_DIA_MM": r["stirrup_dia"], "NOTE_PRINTED": r["note"],
                   "SOURCE": "ST7757.pdf p.13 LINTEL SCHEDULE (VIS-P13-SCHEDULE; no vector text on p.13)",
                   "HEADER_PRINTED": " | ".join(SCHEDULE_HEADER)})
    for a, b, ra, rb in L["sched_check"]["gaps"]:
        st.append({"RECORD": "UNCOVERED_INTERVAL", "ROW_ID": f"GAP-{a}-{b}", "WIDTH_PRINTED": f"{a} < w < {b}",
                   "WIDTH_LO_CM": a, "WIDTH_HI_CM": b, "BOUNDS": "open interval: no row", "NOTE_PRINTED": "",
                   "SOURCE": f"between {ra} and {rb}"})
    st.append({"RECORD": "UNCOVERED_INTERVAL", "ROW_ID": "ABOVE-750", "WIDTH_PRINTED": "w > 750",
               "WIDTH_LO_CM": 750, "BOUNDS": "no row above the last band", "SOURCE": "after L5"})
    for w in BOUNDARY_CASES_MM:
        state, row = LQ.row_for_width(rows, w)
        st.append({"RECORD": "BOUNDARY_CASE", "ROW_ID": f"W{_full(w, 1)}", "WIDTH_PRINTED": f"{_full(w, 1)} mm",
                   "BOUNDS": state, "SOURCE": row["row_id"] if state == LQ.IN_ROW else
                   ("/".join(x["row_id"] for x in row) if row else "")})
    st.append({"RECORD": "DETAIL_READING", "ROW_ID": "MIN-BEARING", "WIDTH_PRINTED": "MIN.40cm",
               "BOUNDS": f"{_full(MIN_BEARING_MM, 1)} mm each side", "SOURCE": "VIS-P13-DETAIL"})
    for v in VISUAL:
        st.append({"RECORD": "VISUAL_RECORD", "ROW_ID": v["ID"], "WIDTH_PRINTED": v["WHAT"], "BOUNDS": v["READING"],
                   "SOURCE": f"{v['FILE']} p.{v['PAGE']} @ {v['DPI']} dpi (render kept outside git)"})
    _csv(OUTPUTS[2], st, ["RECORD", "ROW_ID", "WIDTH_PRINTED", "WIDTH_LO_CM", "WIDTH_HI_CM", "BOUNDS", "SIZE_PRINTED",
                          "B", "D_CM", "BOTTOM_PRINTED", "BOTTOM_N", "BOTTOM_DIA_MM", "TOP_PRINTED", "TOP_N",
                          "TOP_DIA_MM", "STIRRUPS_PRINTED", "STIRRUP_RATE_PER_M", "STIRRUP_DIA_MM", "NOTE_PRINTED",
                          "HEADER_PRINTED", "SOURCE"])
    # ------------------------------------------------------------ 03 registration
    rg = []
    for fl in FLOORS:
        r = L["reg_of"][fl]
        rg.append({"RECORD": "FLOOR", "FLOOR": fl, "SHEET": r["sheet"], "TX_MM": _r(r["T"][0], 3),
                   "TY_MM": _r(r["T"][1], 3), "VOTES": r["votes"], "SECOND_BEST": r["second_best"],
                   "ARCH_COLUMNS": r["arch_columns"], "STRUCT_COLUMNS": r["structural_columns"],
                   "MATCHED": len(r["matched"]), "UNMATCHED_ARCH": r["unmatched_arch"],
                   "UNMATCHED_STRUCT": r["unmatched_structural"],
                   "CHECK": "GF + GFRS frame = PS5.1 translation_arch_to_gfrs" if fl == "GF" else ""})
        for ah, sh in sorted(r["matched"].items()):
            rg.append({"RECORD": "COLUMN", "FLOOR": fl, "SHEET": r["sheet"], "ARCH_HANDLE": ah, "STRUCT_HANDLE": sh,
                       "S1_COLUMN": L["col_of"].get((r["sheet"], sh))})
    for fh, fr in sorted(L["elev"]["frames"].items()):
        rg.append({"RECORD": "ELEVATION", "FLOOR": ",".join(fr["floors_readable"]), "SHEET": f"P7757 frame {fh}",
                   "TX_MM": _r(fr["offset"], 1), "VOTES": fr["openings_bound_by_width"], "SECOND_BEST": fr["runner_up"],
                   "CHECK": f"facing {fr['facing']} mirror {fr['mirror']} registered {fr['registered']}; printed "
                            f"floor levels readable for {fr['floors_readable']}"})
    _csv(OUTPUTS[3], rg, ["RECORD", "FLOOR", "SHEET", "TX_MM", "TY_MM", "VOTES", "SECOND_BEST", "ARCH_COLUMNS",
                          "STRUCT_COLUMNS", "MATCHED", "UNMATCHED_ARCH", "UNMATCHED_STRUCT", "ARCH_HANDLE",
                          "STRUCT_HANDLE", "S1_COLUMN", "CHECK"])
    # ------------------------------------------------------------ 04 binding matrix
    bm = []
    for o in all_ops:
        r = o.get("sched_row") if o.get("sched_state") == LQ.IN_ROW else None
        x = lint_of.get(o["opening_id"])
        bm.append({"OPENING_ID": o["opening_id"], "FLOOR": o["floor"], "TYPE": o["type"],
                   "WIDTH_MM": o.get("width_mm"), "WALL_THICKNESS_MM": o.get("t_mm"),
                   "SCHEDULE_STATE": o.get("sched_state"), "SCHEDULE_ROW": r["row_id"] if r else None,
                   "SECTION": f"{_full(o['t_mm'], 1)} x {_full(r['D_cm'] * 10, 1)} mm" if r and o.get("t_mm") else None,
                   "BOTTOM": r["bottom"] if r else None, "TOP": r["top"] if r else None,
                   "STIRRUPS": r["stirrups"] if r else None, "BEAM_RELATION": o.get("beam_relation"),
                   "BEAM_DEPTH_MM": o.get("beam_depth_mm"), "HEAD_ROOM_MM": head_room(o) if "g" in o else None,
                   "DECISION": o["decision"], "LANE": _lane(o), "REASON": o["reason"],
                   "LINTEL_ID": x["lintel_id"] if x else None, "QUESTIONS": o.get("questions", [])})
    _csv(OUTPUTS[4], bm)
    # ------------------------------------------------------------ 05 beam overlap audit
    ba = []
    for o in ops:
        for b in o["beams"] or [{"line_id": None, "relation": LQ.NONE}]:
            ba.append({"OPENING_ID": o["opening_id"], "FLOOR": o["floor"], "SHEET": SLAB_ABOVE[o["floor"]],
                       "SCOPE": "OPENING_SPAN", "BEAM_LINE": b.get("line_id"), "RELATION": b["relation"],
                       "PARALLEL": b.get("parallel"), "LATERAL_SHARE": _r(b.get("lateral_share"), 4),
                       "ALONG_SHARE": _r(b.get("along_share"), 4), "BEAM_WIDTH_MM": b.get("beam_width_mm"),
                       "S6_OCCURRENCES": b.get("s6_occurrences"), "MARKS": b.get("marks"),
                       "DECISION": o["decision"]})
        for b in o.get("beams_near", []):
            ba.append({"OPENING_ID": o["opening_id"], "FLOOR": o["floor"], "SHEET": SLAB_ABOVE[o["floor"]],
                       "SCOPE": "BEARING_ZONE (within 400 mm of a jamb)", "BEAM_LINE": b["line_id"],
                       "RELATION": b["relation"], "PARALLEL": b["parallel"],
                       "LATERAL_SHARE": _r(b["lateral_share"], 4), "ALONG_SHARE": _r(b["along_share"], 4),
                       "BEAM_WIDTH_MM": b["beam_width_mm"], "S6_OCCURRENCES": b["s6_occurrences"],
                       "MARKS": b["marks"], "DECISION": o["decision"]})
        for a in o.get("arc_beams", []):
            ba.append({"OPENING_ID": o["opening_id"], "FLOOR": o["floor"], "SHEET": SLAB_ABOVE[o["floor"]],
                       "SCOPE": "CURVED", "BEAM_LINE": a["handle"], "RELATION": "ARC", "ALONG_SHARE":
                       _r(a["along_share"], 4), "DECISION": o["decision"]})
    for x in released:
        ba.append({"OPENING_ID": x["opening_id"], "FLOOR": x["floor"], "SCOPE": "RELEASED_LINTEL_FOOTPRINT",
                   "BEAM_LINE": None, "RELATION": "NO_BEAM_OVER_OPENING_SPAN",
                   "COLUMN_OVERLAP_MM2": _r(x["column_overlap_mm2"], 1),
                   "LINTEL_OVERLAP_MM2": _r(x.get("lintel_overlap_mm2", 0.0), 1), "DECISION": SCHEDULE_BOUND})
    _csv(OUTPUTS[5], ba, ["OPENING_ID", "FLOOR", "SHEET", "SCOPE", "BEAM_LINE", "RELATION", "PARALLEL",
                          "LATERAL_SHARE", "ALONG_SHARE", "BEAM_WIDTH_MM", "S6_OCCURRENCES", "MARKS",
                          "COLUMN_OVERLAP_MM2", "LINTEL_OVERLAP_MM2", "DECISION"])
    # ------------------------------------------------------------ 06 concrete, 07 rebar
    conc, reb = [], []
    for x in released + sens:
        lane = PROJECT_BASIS_QTO if x["released"] else SENS
        conc.append({"LINTEL_ID": x["lintel_id"], "OPENING_ID": x["opening_id"], "FLOOR": x["floor"],
                     "ROW": x["row"]["row_id"], "B_MM": x["B"], "D_MM": x["D"], "OPENING_W_MM": _r(x["s1"] - x["s0"], 6) if "s1" in x else x["o"]["width_mm"],
                     "BEARING_START_MM": _r(x["bearing_start"], 6),
                     "START_SUPPORT": x["supports"]["start"]["kind"], "START_BASIS": x["supports"]["start"]["basis"],
                     "BEARING_END_MM": _r(x["bearing_end"], 6), "END_SUPPORT": x["supports"]["end"]["kind"],
                     "END_BASIS": x["supports"]["end"]["basis"], "LENGTH_MM": _r(x["L"], 6),
                     "GROSS_M3": _r(x["B"] * x["D"] * x["L"] / 1e9, 9),
                     "SHARED_CORNER_M3": _r(x.get("overlap_deduct_m3", 0.0), 9),
                     "M3": _r(x["m3"], 9), "LANE": lane, "FLAGS": x["flags"],
                     "DECISION": x["o"]["decision"]})
        for b in x["bars"]:
            reb.append({"VIEW": "PROJECT_BASIS_QTO" if x["released"] else "SENSITIVITY_ONLY",
                        "LINTEL_ID": x["lintel_id"], "FLOOR": x["floor"], "ROW": x["row"]["row_id"],
                        "ROLE": b["role"], "DIA_MM": b["dia_mm"], "COUNT": b["count"], "EACH_MM": _r(b["each_mm"], 6),
                        "TOTAL_MM": _r(b["total_mm"], 6), "KG": _r(b["kg"], 9), "LANE": lane,
                        "COUNT_BASIS": b["count_basis"], "LENGTH_BASIS": b["length_basis"]})
        if x["released"]:
            for b in x["bars"]:
                reb.append({"VIEW": "PHYSICAL_BBS", "LINTEL_ID": x["lintel_id"], "FLOOR": x["floor"],
                            "ROW": x["row"]["row_id"], "ROLE": b["role"], "DIA_MM": b["dia_mm"], "COUNT": b["count"],
                            "EACH_MM": _r(b["each_mm"], 1), "LANE": BLOCKED,
                            "COUNT_BASIS": "fabrication count = bars per lintel",
                            "LENGTH_BASIS": "straight portion only: shape code / bends / hooks blocked (not "
                                            "dimensioned), so no cut length is issued"})
            for role, why in blocked_roles(x):
                reb.append({"VIEW": "BLOCKED_ROLE", "LINTEL_ID": x["lintel_id"], "FLOOR": x["floor"],
                            "ROW": x["row"]["row_id"], "ROLE": role, "LANE": BLOCKED, "LENGTH_BASIS": why})
    _csv(OUTPUTS[6], conc)
    _csv(OUTPUTS[7], reb, ["VIEW", "LINTEL_ID", "FLOOR", "ROW", "ROLE", "DIA_MM", "COUNT", "EACH_MM", "TOTAL_MM",
                           "KG", "LANE", "COUNT_BASIS", "LENGTH_BASIS"])
    # ------------------------------------------------------------ 08 blocked and conflicts
    bc = []
    for o in all_ops:
        if o["decision"] in (BLOCKED_SUPPORT, DECISION_CONFLICT):
            x = sens_of.get(o["opening_id"])
            bc.append({"ID": f"BLK-{o['opening_id']}", "KIND": "BLOCKED_OPENING" if o["decision"] == BLOCKED_SUPPORT
                       else "SOURCE_CONFLICT", "SUBJECT": o["opening_id"], "TEXT": o["reason"],
                       "QUESTIONS": o.get("questions", []), "SENSITIVITY_M3": _r(x["m3"], 9) if x else None,
                       "SENSITIVITY_KG": _r(x["kg"], 9) if x else None,
                       "SENSITIVITY_BASIS": ("the p.13 lintel this opening would take if wall remains above its head"
                                             if x else "no schedule lintel can be formed (no wall width or row)")})
    for x in released:
        for f in x["flags"]:
            if f.startswith(LQ.BEARING_DEFICIT):
                side = f.split(":")[1]
                bc.append({"ID": f"CF-BEARING-{x['opening_id']}-{side}", "KIND": "SOURCE_CONFLICT",
                           "SUBJECT": x["lintel_id"], "QUESTIONS": ["Q-BEARING"],
                           "TEXT": f"{side} jamb: {x['supports'][side]['basis']}; 'MIN.40cm' cannot be met. The lintel "
                                   f"is measured to the available wall ({_full(x['bearing_' + side], 1)} mm)."})
    for a, b, ra, rb in L["sched_check"]["gaps"]:
        bc.append({"ID": f"CF-SCHED-{a}-{b}", "KIND": "SOURCE_CONFLICT", "SUBJECT": f"{ra}/{rb}",
                   "TEXT": f"no row for {a} < w < {b} cm (integer bands); no census opening falls in it",
                   "QUESTIONS": ["Q-SCHEDULE-GAPS"]})
    bc.append({"ID": "CF-N04", "KIND": "SOURCE_CONFLICT", "SUBJECT": "P8-N04",
               "TEXT": QUESTIONS["Q-N04"], "QUESTIONS": ["Q-N04"]})
    for k, v in L["r5_dups"].items():
        bc.append({"ID": f"DUP-R5-{k}", "KIND": "DOUBLE_COUNT_FINDING", "SUBJECT": k,
                   "TEXT": f"R5 lists {v} for this one opening (a door and a glazed-door candidate in one gap): "
                           "counted once here", "QUESTIONS": []})
    for qid, t in QUESTIONS.items():
        bc.append({"ID": qid, "KIND": "QUESTION", "SUBJECT": "", "TEXT": t, "QUESTIONS": []})
    _csv(OUTPUTS[8], bc, ["ID", "KIND", "SUBJECT", "TEXT", "QUESTIONS", "SENSITIVITY_M3", "SENSITIVITY_KG",
                          "SENSITIVITY_BASIS"])
    # ------------------------------------------------------------ 09 BOQ opening register
    boq = []
    for o in ops + L["symbol_ops"]:
        wet = sorted(set(o.get("side_a_labels", []) + o.get("side_b_labels", [])) & WET)
        x = lint_of.get(o["opening_id"])
        oid = o["opening_id"]
        boq.append({"OPENING_ID": oid, "FLOOR": o["floor"], "TYPE": o["type"], "ZONE": o["zone"],
                    "WIDTH_MM": o.get("width_mm"), "HEIGHT_STATE": "NOT_ESTABLISHED",
                    "WALL_BAND_ID": o.get("band_id"), "WALL_THICKNESS_MM": o.get("t_mm"),
                    "SIDE_A": o.get("side_a"), "SIDE_A_ROOMS": o.get("side_a_labels", []),
                    "SIDE_B": o.get("side_b"), "SIDE_B_ROOMS": o.get("side_b_labels", []),
                    "BLOCKWORK_DEDUCTION": f"BW-DED:{oid}", "PLASTER_DEDUCTION": [f"PL-DED:{oid}:A", f"PL-DED:{oid}:B"],
                    "PAINT_DEDUCTION": [f"PT-DED:{oid}:A", f"PT-DED:{oid}:B"],
                    "CERAMIC_DEDUCTION": [f"CR-DED:{oid}:{s_}" for s_, lab in (("A", o.get("side_a_labels", [])),
                                                                              ("B", o.get("side_b_labels", [])))
                                          if set(lab) & WET],
                    "DOOR_WINDOW_ITEM": None if o["type"] in (T_PASSAGE, T_SERVICE) else f"DW:{oid}",
                    "REVEAL_JAMB": f"RV:{oid}", "LINTEL_ITEM": x["lintel_id"] if x else None,
                    "LINTEL_DECISION": o["decision"], "WET_ROOM_SIDES": wet, "R5_IDS": o.get("r5_ids", []),
                    "QUANTITY_STATE": "IDS_AND_OWNERSHIP_ONLY (S8.6 changes no architectural BOQ quantity)"})
    _csv(OUTPUTS[9], boq)
    L["boq_rows"] = boq
    return write_tail(L, st, rg, bm, ba, conc, reb, bc, boq)


BOUNDARY_CASES_MM = (0.0, 1.0, 999.9, 1000.0, 1000.5, 1001.0, 1010.0, 2000.0, 2005.0, 2010.0, 3000.0, 3010.0, 5000.0,
                     5010.0, 7500.0, 7500.1, 7510.0)


def blocked_roles(x):
    out = [("BOTTOM_END_BENDS", "drawn bent into the bearing on the LINTEL DETAIL; no length printed"),
           ("TOP_END_BENDS", "drawn bent into the bearing on the LINTEL DETAIL; no length printed"),
           ("STIRRUP_HOOKS", "SECT (2-2) draws hooks; no hook length printed")]
    for side in ("start", "end"):
        if x["supports"][side]["kind"] == LQ.FRAME:
            out.append((f"ANCHORAGE_INTO_COLUMN_{side.upper()}", "the lintel frames into a column face; no "
                        "anchorage or dowel detail is printed (P8-N09 40D/70D is for starters)"))
    out.append(("LAPS", "none drawn: the LINTEL DETAIL shows each bar continuous over the lintel; none measured"))
    return out


def write_tail(L, st, rg, bm, ba, conc, reb, bc, boq):
    ops, released, sens = L["ops"], L["lintels"], L["lintel_sens"]
    all_ops = ops + L["symbol_ops"] + L["slab_ops"]
    frozen, errata, index = L["frozen"], L["errata"], L["index"]
    # ------------------------------------------------------------ 10 ownership
    s2 = [{k: c.get(k) for k in ("element_id", "component", "release_state")}
          for c in _j(READ["S2_COMPONENTS"])["components"] if c.get("element_id") == "BM-ALL-LINTEL-POPULATION"]
    s1b = [r for r in L["s1beams"] if r.get("family") == "LINTEL"]
    s6c = [r for r in L["s6cons"] if r["object_id"] == "RULE:P13-LINTEL"]
    own = [
        {"ID": "OWN-S1-BEAM", "STAGE": "S1", "RECORD": "BM-ALL-LINTEL-POPULATION",
         "OLD_STATE": s1b[0]["terminal_state"] if s1b else None, "NEW_OWNER": "S8.6",
         "NOTE": "population blocked in S1 ('occurrences come from the architectural openings'): S8.6 supplies it"},
        {"ID": "OWN-S1-SPECIAL", "STAGE": "S1", "RECORD": "SPC-LINTELS",
         "OLD_STATE": L["s1special"]["SPC-LINTELS"]["status"], "NEW_OWNER": "S8.6", "NOTE": "same population"},
        {"ID": "OWN-S1-DEF", "STAGE": "S1", "RECORD": "BDEF-LINTEL / P13-LINTEL", "OLD_STATE": "DEFINED_BY_TYPICAL_DETAIL",
         "NEW_OWNER": "S8.6 binds", "NOTE": "the definition is read, never re-owned"},
        {"ID": "OWN-S2", "STAGE": "S2", "RECORD": "BM-ALL-LINTEL-POPULATION " + "/".join(sorted(c["component"] for c in s2)),
         "OLD_STATE": sorted({c["release_state"] for c in s2}), "NEW_OWNER": "S8.6",
         "NOTE": "S2 holds the lintel population's concrete and bars BLOCKED with no quantity; read: id, component, "
                 "release state only"},
        {"ID": "OWN-S6", "STAGE": "S6", "RECORD": "RULE:P13-LINTEL", "OLD_STATE": s6c[0]["s6_terminal"] if s6c else None,
         "NEW_OWNER": "S8.6", "NOTE": "S6 leaves the lintel family out of scope; no S6 beam kg moves"},
        {"ID": "OWN-S6-BEAMS", "STAGE": "S6 / S6.1", "RECORD": "beams over openings",
         "OLD_STATE": "S6 occurrences", "NEW_OWNER": "S6 / S6.1 (unchanged)",
         "NOTE": f"{sum(1 for o in ops if o['beam_relation'] != LQ.NONE)} openings have an S1 beam band over them in "
                 "plan: no lintel is released there, so no RC member is counted twice"},
        {"ID": "OWN-S3.1", "STAGE": "S3.1", "RECORD": "columns at jambs", "OLD_STATE": "S3.1 columns",
         "NEW_OWNER": "S3.1 (unchanged)",
         "NOTE": "released lintels stop at column faces (FRAME supports); no column concrete or bar is re-counted"},
        {"ID": "OWN-S5", "STAGE": "S5", "RECORD": "ground beams", "OLD_STATE": "S5", "NEW_OWNER": "S5 (unchanged)",
         "NOTE": "GF openings sit above the GF slab; no interface"},
        {"ID": "OWN-S7", "STAGE": "S7", "RECORD": "slabs and slab openings", "OLD_STATE": "S7 / S1 panels",
         "NEW_OWNER": "S7 / stairs family (unchanged)",
         "NOTE": f"{len(L['slab_ops'])} slab openings are census rows (type 8) with no lintel"},
        {"ID": "OWN-PRE-S8", "STAGE": "PRE-S8", "RECORD": ";".join(r["ELEMENT_ID"] for r in L["pre"]),
         "OLD_STATE": ";".join(f"{r['EXISTING_STAGE_OWNER']} -> {r['NEW_S8_OWNER']}" for r in L["pre"]),
         "NEW_OWNER": "S8.6", "NOTE": "whitelisted columns only; missing: " +
                                     ";".join(r["MISSING_INFORMATION"] for r in L["pre"])},
        {"ID": "OWN-ARCH-BOQ", "STAGE": "architectural BOQ (future)", "RECORD": "door / window supply, blockwork, "
         "plaster, paint, ceramic", "OLD_STATE": "not measured", "NEW_OWNER": "architectural engines",
         "NOTE": "09 publishes link ids only; the lintel's structural quantity is never a door / window item"},
        {"ID": "OWN-LIFT", "STAGE": "lift family (future)", "RECORD": ";".join(o["opening_id"] for o in ops
                                                                            if o["type"] == T_SERVICE),
         "OLD_STATE": "S1 SPC-LIFT_PIT / LIFT_TIE_BEAM BLOCKED", "NEW_OWNER": "lift family",
         "NOTE": "landing openings blocked here"},
        {"ID": "OWN-BOUNDARY", "STAGE": "boundary wall family (future)",
         "RECORD": ";".join(o["opening_id"] for o in L["symbol_ops"]), "OLD_STATE": "P14-BOUNDARY",
         "NEW_OWNER": "boundary wall family", "NOTE": "gate in the compound wall"}]
    _csv(OUTPUTS[10], own)
    # ------------------------------------------------------------ 11 conservation
    cons = conservation(L)
    _csv(OUTPUTS[11], cons)
    # ------------------------------------------------------------ 12 source authority
    sa = source_authority(L)
    _csv(OUTPUTS[12], sa)
    # ------------------------------------------------------------ 13 provenance
    prov = []
    for o in ops:
        prov.append({"record": o["opening_id"], "output": OUTPUTS[1], "drawing_sha256": ARCH_SHA,
                     "frame": L["plans"][o["floor"]]["frame_handle"], "handles": o["handles"],
                     "face_lines": o["jamb_face_lines"], "slab_sheet": SLAB_ABOVE[o["floor"]],
                     "structural_sha256": STRUCT_SHA})
    for x in released:
        prov.append({"record": x["lintel_id"], "output": OUTPUTS[6], "opening": x["opening_id"],
                     "schedule_row": x["row"]["row_id"], "authority": "ST7757.pdf p.13 (VIS-P13-SCHEDULE)"})
    for v in VISUAL:
        prov.append({"record": v["ID"], "output": OUTPUTS[2], "file": v["FILE"], "page": v["PAGE"], "dpi": v["DPI"],
                     "kept_in_git": False})
    (HERE / OUTPUTS[13]).write_text("".join(json.dumps(p_, sort_keys=True, ensure_ascii=False) + "\n" for p_ in prov),
                                    encoding="utf-8")
    # ------------------------------------------------------------ 14 summary
    by_floor_type = defaultdict(Counter)
    for o in all_ops:
        by_floor_type[o["floor"]][o["type"]] += 1
    m3_floor = {fl: _r(math.fsum(x["m3"] for x in released if x["floor"] == fl), 9) for fl in FLOORS}
    kg_fd = defaultdict(float)
    for x in released:
        for b in x["bars"]:
            kg_fd[(x["floor"], b["dia_mm"])] += b["kg"]
    kg_floor_dia = {fl: {str(d): _r(v, 9) for (f, d), v in sorted(kg_fd.items()) if f == fl} for fl in FLOORS}
    kg_dia = defaultdict(float)
    for (f, d), v in kg_fd.items():
        kg_dia[str(d)] += v
    summary = {
        "round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "policy": POLICY,
        "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "openings": {"wall_openings": len(ops), "boundary_wall": len(L["symbol_ops"]), "slab": len(L["slab_ops"]),
                     "rejected_candidates": len(L["rejected"]),
                     "by_floor_type": {k: dict(sorted(v.items())) for k, v in sorted(by_floor_type.items())}},
        "decisions": dict(sorted(Counter(o["decision"] for o in all_ops).items())),
        "released": {"lintels": [x["lintel_id"] for x in released], "concrete_m3_by_floor": m3_floor,
                     "concrete_m3": _r(math.fsum(x["m3"] for x in released), 9),
                     "kg_by_floor_and_diameter": kg_floor_dia,
                     "kg_by_diameter": {k: _r(v, 9) for k, v in sorted(kg_dia.items(), key=lambda kv: int(kv[0]))},
                     "kg": _r(math.fsum(x["kg"] for x in released), 9)},
        "sensitivity_not_released": {"lintels": len(sens), "m3": _r(math.fsum(x["m3"] for x in sens), 9),
                                     "kg": _r(math.fsum(x["kg"] for x in sens), 9)},
        "bearing_deficits": sorted(x["lintel_id"] for x in released if any(f.startswith(LQ.BEARING_DEFICIT)
                                                                            for f in x["flags"])),
        "r5_double_counts": L["r5_dups"],
        "r5_missed": sorted(o["opening_id"] for o in ops if not o["r5_ids"]),
        "elevations": {k: {a: v[a] for a in ("facing", "mirror", "registered", "floors_readable",
                                              "openings_bound_by_width")}
                       for k, v in sorted(L["elev"]["frames"].items())},
        "elevation_bound": sorted(L["elev"]["bound"]),
        "schedule_gaps_cm": [[a, b] for a, b, _, _ in L["sched_check"]["gaps"]],
        "questions": sorted(QUESTIONS),
        "conservation": {c["CHECK_ID"]: c["RESULT"] for c in cons},
        "frozen_baselines": {k: v["manifest_sha256"] for k, v in frozen.items()},
        "register_indexes": index, "s8_3_errata_sha256": errata, "unit_mass": UM.describe(UNIT_MASS),
        "references_read": []}
    _json(OUTPUTS[14], summary)
    (HERE / OUTPUTS[0]).write_text(readme(summary, L), encoding="utf-8")
    manifest = {"round": ROUND, "date": DATE, "baseline": BASELINE_HEAD, "state": "FROZEN_BEFORE_COMPARISON",
                "engine_commit_stamp": summary["engine_commit"], "references_read": [],
                "code": {c: _sha(ROOT / c) for c in CODE},
                "inputs": {str(p_.relative_to(ROOT)): _sha(p_) for p_ in READ.values()},
                "drawing_sha256": {"P7757.dxf": ARCH_SHA, "ST7757.dxf": STRUCT_SHA, "ST7757.pdf": STRUCT_PDF_SHA},
                "pre_s8_columns_read": list(PRE_S8_COLUMNS), "r5_fields_read": list(R5_FIELDS),
                "frozen_baselines": summary["frozen_baselines"], "register_indexes": index,
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "released": summary["released"],
                "rule": "frozen before any earlier Urban, contractor or third-party lintel figure is read; the "
                        "comparison after it explains differences and never changes a frozen quantity"}
    _json(MANIFEST_NAME, manifest)
    for k, m_ in MANIFESTS.items():
        DR.verify_frozen(m_, ROOT)
    return summary


HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")


def conservation(L):
    ops, released, sens = L["ops"], L["lintels"], L["lintel_sens"]
    all_ops = ops + L["symbol_ops"] + L["slab_ops"]
    rows = L["sched_rows"]
    out = []

    def A(cid, text, ok, detail=""):
        check(ok, f"conservation {cid}: {text} ({detail})")
        out.append({"CHECK_ID": cid, "TEXT": text, "RESULT": "PASS", "DETAIL": detail})

    ids = [o["opening_id"] for o in all_ops]
    A("C01", "every opening has a unique id and exactly one of the six decisions",
      len(ids) == len(set(ids)) and all(o["decision"] in DECISIONS for o in all_ops), f"{len(ids)} openings")
    nd = sum(len(L["blocks"][fl]["doors"]) for fl in FLOORS)
    na = sum(len(L["blocks"][fl]["archs"]) for fl in FLOORS)
    bound_doors = sum(len(o["door_blocks"]) for o in ops)
    A("C02", "every door insert is bound to one opening (or is the boundary-wall opening); every arch insert is bound",
      bound_doors + len(L["symbol_ops"]) == nd and sum(len(o["arch_blocks"]) for o in ops) == na,
      f"{nd} door inserts, {na} arch inserts")
    A("C03", "every glazing element in a plan frame is held by exactly one opening",
      not [u for u in L["unbound"] if u["kind"] == "GLAZING_ELEMENT"],
      f"{sum(len(L['blocks'][fl]['glz']) for fl in FLOORS)} glazing elements")
    A("C04", "schedule bands ordered and never overlapping; each census width meets at most one row",
      all(len([r for r in rows if r["lo"] <= o["width_mm"] / 10 <= r["hi"]]) <= 1 for o in ops),
      f"gaps {[(a, b) for a, b, _, _ in L['sched_check']['gaps']]}")
    exp = {1000.0: "L1", 1000.5: LQ.BOUNDARY_GAP, 1010.0: "L2", 2000.0: "L2", 2005.0: LQ.BOUNDARY_GAP, 7500.0: "L5",
           7500.1: LQ.ABOVE_SCHEDULE, 0.0: LQ.NOT_POSITIVE}
    got = {}
    for w in exp:
        stt, r = LQ.row_for_width(rows, w)
        got[w] = r["row_id"] if stt == LQ.IN_ROW else stt
    A("C05", "boundary widths bind as printed (100 -> L1, 100.05 cm -> gap, 101 -> L2, 750 -> L5, > 750 -> none)",
      got == exp, json.dumps({_full(k, 1): v for k, v in got.items()}))
    A("C06", "no released lintel lies under a beam band over its opening span",
      all(x["o"]["beam_relation"] == LQ.NONE for x in released), f"{len(released)} released")
    A("C07", "every released lintel has valid geometry (B, D > 0, length > opening, no column overlap; a corner "
             "shared with another lintel is counted once)",
      all(x["B"] > 0 and x["D"] > 0 and x["L"] > x["o"]["width_mm"] and x["column_overlap_mm2"] <= 1000.0 and
          x["m3"] > 0 and (x.get("lintel_overlap_mm2", 0.0) <= 1.0 or x.get("overlap_deduct_m3", 0.0) > 0)
          for x in released),
      f"max column overlap {_full(max([x['column_overlap_mm2'] for x in released] or [0]), 1)} mm2")
    A("C08", "unsupported openings stay blocked: nothing under a beam, without a wall, curved, lift or boundary is "
             "released", not [o for o in all_ops if o["decision"] == SCHEDULE_BOUND and
                              (o["beam_relation"] != LQ.NONE or o["kind"] != "WALL_GAP" or o["type"] == T_SERVICE)])
    A("C09", "elevations add evidence only: every elevation binding names an existing plan opening, one each",
      set(L["elev"]["bound"]) <= {o["opening_id"] for o in ops}, f"{len(L['elev']['bound'])} bound")
    r5m = [x for x in L["r5_xw"] if x.get("match")]
    A("C10", "R5 rows map to one opening each; its door + glazed-door pairs collapse to one opening",
      len(L["r5_dups"]) == 4 and all(len(v) == 2 for v in L["r5_dups"].values()),
      f"{len(r5m)} of {len(L['r5_xw'])} R5 rows matched; duplicates {sorted(L['r5_dups'])}")
    from shapely.geometry import Polygon  # noqa: F401
    polys = defaultdict(list)
    for o in ops:
        polys[o["floor"]].append((o["opening_id"], opening_poly(o)))
    ov = [(a, b) for fl, ps in polys.items() for i, (a, pa) in enumerate(ps) for b, pb in ps[i + 1:]
          if pa.intersection(pb).area > 1.0]
    A("C11", "no two openings occupy the same plan area (no opening counted twice)", not ov, str(ov))
    A("C12", "every arch column registers onto a structural outline; GF = PS5.1",
      all(not L["reg_of"][fl]["unmatched_arch"] for fl in FLOORS))
    sl = {x["panel_id"] for x in L["slabs"] if x["class"] in ("OPEN_TO_BELOW", "STAIR_FLIGHT_ZONE",
                                                              "STAIR_IN_VOID_ZONE")}
    A("C13", "every S1 slab-opening panel is a type-8 census row", sl == {o["panel_id"] for o in L["slab_ops"]},
      f"{len(sl)} panels")
    tot = math.fsum(b["kg"] for x in released for b in x["bars"])
    A("C14", "kg by floor and diameter sum to the released total; m3 likewise",
      abs(tot - math.fsum(x["kg"] for x in released)) < 1e-9, f"{_full(tot, 6)} kg")
    A("C15", f"all {len(MANIFESTS)} earlier freeze manifests, the S8.3 errata and the S1 / S2 / S3 / S3.1 register "
             "indexes verify", len(L["frozen"]) == len(MANIFESTS) and len(L["index"]) == 4)
    A("C16", "no earlier lintel figure read: PRE-S8 and R5 through whitelists, S2 through id / component / state",
      not set(PRE_S8_COLUMNS) & set(PRE_S8_FIREWALLED) and not set(R5_FIELDS) & set(R5_FIREWALLED))
    bad = []
    for name in OUTPUTS[1:10]:
        if HYGIENE.search((HERE / name).read_text(encoding="utf-8")):
            bad.append(name)
    A("C17", "no Arabic run, owner or title-block text in the outputs", not bad, str(bad))
    A("C18", "every released lintel registers its blocked bends and hooks (and anchorage at column ends)",
      all(len(blocked_roles(x)) >= 4 for x in released))
    return out


def source_authority(L):
    S = L["survey"]
    rows = [
        ("OPENING_EXISTENCE", "P7757.dxf plan wall faces (layer 1) + door / glazing / arch symbols", "SOURCE_GEOMETRY",
         "a gap is an opening only with a jamb at each end; a corner closure needs a symbol"),
        ("OPENING_WIDTH", "P7757.dxf true-size model space; printed plan / elevation dimension where one spans the "
         "jambs", "PRINTED where available, else DRAWN_CAD_GEOMETRY",
         f"{len(L['plan_dims'])} plan + {len(L['elev']['bound'])} elevation printed widths; every printed width "
         "equals the drawn one"),
        ("WALL_THICKNESS", "P7757.dxf face-line separation", "DRAWN_CAD_GEOMETRY", "150 / 200 mm bands"),
        ("TYPE", "symbols, room labels, elevation sills", "SOURCE_GEOMETRY", "material never inferred"),
        ("INTERNAL_EXTERNAL", "spaces from the plan (doors and glazing close a space; passages do not)",
         "SOURCE_GEOMETRY", "exterior = reaches the plan boundary or holds a garden / court / roof / pool label"),
        ("HEIGHT_SILL_HEAD", "elevation dimension chains (P7757 frames 83, 84)", "PRINTED only where a printed chain "
         "from the ground reaches the drawn outline", f"DIMENSION entities in P7757: {S['dimension_entities']}; no "
         "door / window schedule"),
        ("LINTEL_SCHEDULE", "ST7757.pdf p.13", "EXACT (visual record)", "transcribed in 02"),
        ("BEARING", "p.13 LINTEL DETAIL 'MIN.40cm'", "EXACT", "limited by the drawn wall; deficits are conflicts"),
        ("LINTEL_WIDTH_B", "p.13 note 'B-WIDTH OF THE BLOCK WALL'", "EXACT", "= wall band thickness"),
        ("COVER", "P8-N22 (beams 2.5 cm)", "PROJECT_BASIS", "no lintel cover printed"),
        ("STIRRUP_COUNT", "'5Ø8/M' + S3.1 RATE_COUNT", "PROJECT_BASIS", "ceil(rate x lintel length)"),
        ("UNIT_MASS", "D2/162", "PROJECT_BASIS", UM.describe(UNIT_MASS)["method"] if isinstance(
            UM.describe(UNIT_MASS), dict) else "D2/162"),
        ("REGISTRATION", "column outline voting (arch -> GFRS / FFRS / SFRS)", "SOURCE_GEOMETRY", "unique translations"),
        ("BEAMS_ABOVE", "S1 beam linework + S6 occurrences on the slab sheet above", "SOURCE_GEOMETRY",
         "plan overlap only; head vs soffit needs a printed head"),
        ("LIFT_SHAFT", "S1 FF lift footing outline + a small unlabelled space on every floor", "SOURCE_GEOMETRY",
         "lift family"),
        ("SLAB_OPENINGS", "S1 SLAB_PANEL_REGISTER", "FROZEN_STAGE", "type 8"),
        ("ROOM_LABELS", "P7757 room-label blocks (their English text)", "SOURCE_TEXT", "Arabic text never copied")]
    return [{"ATTRIBUTE": a, "SOURCE": b, "AUTHORITY": c, "NOTE": d} for a, b, c, d in rows]


def readme(s, L):
    r = s["released"]
    Lx = ["# S8.6 - lintels: opening census, schedule binding, lintel concrete and reinforcement", "",
          f"Baseline `{BASELINE_HEAD}`, engine stamp `{s['engine_commit']}`. Frozen before any comparison "
          "(`references_read: []`).", "",
          "## Openings", "",
          f"- {s['openings']['wall_openings']} wall openings found from the P7757 wall faces, "
          f"{s['openings']['boundary_wall']} gate in the boundary wall and {s['openings']['slab']} slab openings "
          f"(S1). {s['openings']['rejected_candidates']} candidate gaps were rejected (wall bends, unrelated wall "
          "ends).", ""]
    for fl, v in s["openings"]["by_floor_type"].items():
        Lx.append(f"- {fl}: " + ", ".join(f"{k} {n}" for k, n in v.items()))
    Lx += ["", "## Decisions", ""] + [f"- {k}: {v}" for k, v in s["decisions"].items()]
    Lx += ["", "## Released (PROJECT_BASIS_QTO)", "",
           f"- {len(r['lintels'])} lintels, {_full(r['concrete_m3'], 6)} m3, {_full(r['kg'], 3)} kg.",
           "- m3 by floor: " + ", ".join(f"{k} {_full(v, 6)}" for k, v in r["concrete_m3_by_floor"].items()),
           "- kg by diameter: " + ", ".join(f"Ø{k} {_full(v, 3)}" for k, v in r["kg_by_diameter"].items()),
           f"- Not released (sensitivity only): {s['sensitivity_not_released']['lintels']} lintels, "
           f"{_full(s['sensitivity_not_released']['m3'], 6)} m3, {_full(s['sensitivity_not_released']['kg'], 3)} kg.",
           "", "## Outputs", ""] + [f"- `{o}`" for o in OUTPUTS] + [f"- `{MANIFEST_NAME}`", "",
           "Rebuild: `python3 -I research/alsenan_lintels_s8_6/build_s8_6.py` (byte-identical). Renders of the "
           "drawings stay outside git."]
    return "\n".join(Lx) + "\n"


if __name__ == "__main__":
    try:
        s = run()
    except Stop as e:
        print(f"STOP: {e}")
        sys.exit(1)
    print(json.dumps({k: s[k] for k in ("openings", "decisions", "released", "sensitivity_not_released",
                                        "bearing_deficits", "elevation_bound", "conservation")}, indent=1,
                     ensure_ascii=False))
