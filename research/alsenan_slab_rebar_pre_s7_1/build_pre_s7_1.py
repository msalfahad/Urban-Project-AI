"""PRE-S7.1 / AD2 - slab QTO authority / readiness resolution, a delta over frozen PRE-S7 (no kg).

    python3 -I research/alsenan_slab_rebar_pre_s7_1/build_pre_s7_1.py

Reads, after hash-checking the ten freeze manifests (S4 ... D1.2 and PRE-S7): the frozen PRE-S7 registers (census,
tokens, components, supports, rules, runs, conflicts), the frozen S1 slab panel register (panel polygons and edges,
checked against the S1 INDEX) and the Urban project source ST7757.dxf (sha256-checked; beam linework only, for the
dense-hatch geometry). Nothing else is opened: no reference quantity, no donor, no old estimate, no code book.

PRE-S7 is not edited. Every PRE-S7 component terminates exactly once here; its quantity items carry one lane each
(engine/source/slab_qto_authority.py): SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO or BLOCKED_UNQUANTIFIED, or leave S7
(TRANSFERRED_S8). Rates are densities (N x W equivalent bars, unrounded); the physical BBS count stays unresolved.
No bar-length total and no kg is computed: each released item gives its density, distribution width, equivalent bar
count and mean local run, and S7 multiplies.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LAB = ROOT / "research" / "external_engine_lab"
for p in (ROOT, LAB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import alsenan_structural_s1 as S  # noqa: E402
from engine.source import delta_release as DR  # noqa: E402
from engine.source import slab_qto_authority as Q  # noqa: E402
from engine.source import slab_rebar_readiness as SR  # noqa: E402
from engine.source import structural_census as SC  # noqa: E402

ROUND = "PRE-S7.1"
DECISION_SET = "AD2"
POLICY = "AD2_SLAB_QTO_AUTHORITY_V1"
BASELINE_HEAD = "9f89ab6"
DRAWING_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
DXF = ROOT / "data" / "inputs" / "by_sha256" / f"{DRAWING_SHA}.dxf"
R = ROOT / "research"
S1 = R / "alsenan_structural_census_s1"
PRE = R / "alsenan_slab_rebar_pre_s7"
MANIFESTS = {"S4": R / "alsenan_footing_rebar_s4" / "S4_FREEZE_MANIFEST.json",
             "S4.1": R / "alsenan_footing_rebar_s4_1" / "S4_1_FREEZE_MANIFEST.json",
             "S5": R / "alsenan_ground_system_rebar_s5" / "S5_FREEZE_MANIFEST.json",
             "S6": R / "alsenan_superstructure_beam_rebar_s6" / "S6_FREEZE_MANIFEST.json",
             "S6.1": R / "alsenan_superstructure_beam_rebar_s6_1" / "S6_1_FREEZE_MANIFEST.json",
             "S5.1": R / "alsenan_ground_system_rebar_s5_1" / "S5_1_FREEZE_MANIFEST.json",
             "AD1": R / "ad1_authority_decisions" / "AD1_FREEZE_MANIFEST.json",
             "D1.1": R / "d1_1_stirrup_authority_audit" / "D1_1_FREEZE_MANIFEST.json",
             "D1.2": R / "d1_2_footing_cover_audit" / "D1_2_FREEZE_MANIFEST.json",
             "PRE-S7": PRE / "PRE_S7_FREEZE_MANIFEST.json"}
PRE_FILES = ["01_SLAB_PANEL_CENSUS.csv", "03_SLAB_REBAR_TOKENS.csv", "04_COMPONENT_READINESS.csv",
             "05_SUPPORT_REGISTER.csv", "06_SUPPORT_RULES.csv", "07_BAR_RUN_REGISTER.csv", "11_SOURCE_CONFLICTS.csv",
             "PRE_S7_SUMMARY.json"]
CODE = ["engine/source/slab_qto_authority.py", "engine/source/slab_rebar_readiness.py",
        "engine/source/delta_release.py", "engine/source/structural_census.py",
        "research/external_engine_lab/alsenan_structural_s1.py",
        "research/alsenan_slab_rebar_pre_s7_1/build_pre_s7_1.py"]
INPUTS = [str(p.relative_to(ROOT)) for p in MANIFESTS.values()] + [
    "research/alsenan_structural_census_s1/INDEX.json",
    "research/alsenan_structural_census_s1/SLAB_PANEL_REGISTER.json",
    "research/alsenan_structural_census_s1/STRUCTURAL_PROJECT_RULE_REGISTER.json"] + [
    f"research/alsenan_slab_rebar_pre_s7/{f}" for f in PRE_FILES]
OUTPUTS = ["00_README.md", "01_AD2_DECISIONS.json", "02_OWNERSHIP_TRANSFERS.csv", "03_RATE_QTO_REGISTER.csv",
           "04_50_PERCENT_CURTAILMENT_REGISTER.csv", "05_TOP_RULE_IDENTITY.csv", "06_SUPPORT_MISMATCH_SPLITS.csv",
           "07_LOCAL_BAR_STRIPS.csv", "08_UPDATED_COMPONENT_READINESS.csv", "09_REMAINING_CONFLICTS.csv",
           "10_REMAINING_BLOCKERS.csv", "11_S7_RELEASE_CANDIDATES.csv", "12_PROVENANCE.jsonl",
           "PRE_S7_1_SUMMARY.json"]
STOP_FRACTION = 0.125           # P15-BOT-STOP-0.125L (frozen PRE-S7 rule register)
NOTE2_RATE, NOTE2_DIA = 5, 10   # P4-6-NOTE-2: 5Ø10/m (frozen PRE-S7 support register)
HATCH_TOL_MM = 5.0
BAND_OVERLAP_MIN_MM = 50.0
GAP_FACTOR = 1.6                # a crossing gap beyond 1.6 x the drawn support width is not one beam crossing
SPAN_TOL_MM = 0.5               # the far face must span the strip (to drawing precision)
S8 = "S8_SPECIAL_STRUCTURE"
TANK_REGION = "WATER_TANK_SUPPORT_REGION"
LIGHTWELL_REGION = "STAIR_LIGHTWELL_REGION"


class Stop(SystemExit):
    pass


def check(cond, what):
    if not cond:
        raise Stop(f"PRE-S7.1 check failed: {what}")


# ------------------------------------------------------------------ io
def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(name):
    with open(PRE / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _js(v):
    return json.loads(v) if v not in ("", None) else None


def _f(v):
    return float(v) if v not in ("", None) else None


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:.6g}" if abs(v) < 1e15 else str(v)
    if isinstance(v, (list, tuple, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(name, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in fields})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def _json(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _full(v):
    """A quantity written without rounding (to 9 decimals: below any drawing precision)."""
    return None if v is None else f"{float(v):.9f}".rstrip("0").rstrip(".")


def _r(v, n=3):
    return None if v is None else round(float(v), n)


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode())
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()[:16]


def verify_inputs():
    check(_sha(DXF) == DRAWING_SHA, "ST7757.dxf sha256")
    idx = _j(S1 / "INDEX.json")["registers"]
    for n in ("SLAB_PANEL_REGISTER", "STRUCTURAL_PROJECT_RULE_REGISTER"):
        check(_sha(S1 / f"{n}.json") == idx[n]["sha256"], f"frozen S1 {n}")
    frozen = {k: DR.verify_frozen(m, ROOT) for k, m in MANIFESTS.items()}
    pre_out = _j(MANIFESTS["PRE-S7"])["outputs"]
    for f in PRE_FILES:
        check(pre_out.get(f) == _sha(PRE / f), f"PRE-S7 {f} is the frozen output")
    return frozen


# ------------------------------------------------------------------ AD2 decisions (owner, brief AD2 + PRE-S7.1)
DECISIONS = [
    ("AD2-D01", "§1", "QUANTITY_AUTHORITY_LANES", "Three lanes: SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO, "
     "BLOCKED_UNQUANTIFIED. PROJECT_BASIS_QTO is never VERIFIED_PHYSICAL or AS_BUILT."),
    ("AD2-D02", "§2", "RATE_DENSITY_QTO", "N bars/m over W m = N x W equivalent bars, unrounded, no +1, no ceil / "
     "floor. PHYSICAL_BBS_BAR_COUNT stays UNRESOLVED unless a project-source count convention exists."),
    ("AD2-D03", "§3", "EXPLICIT_COUNT_BINDING", "'NØD' without '/m' is EXPLICIT_COUNT only when bound to a discrete "
     "bar group / support-bar graphic / finite reinforcement object. A clear count may release with its length "
     "blocked."),
    ("AD2-D04", "§4", "FIFTY_PERCENT_DENSITY_SPLIT", "A source-stated 50% continue / 50% stop is an exact 0.5 / 0.5 "
     "density split for QTO. Which physical bars stop (and an odd count) stays a BBS question."),
    ("AD2-D05", "§5", "BAR_ROLE_IDENTITY_FIRST", "Rules are compared by bar-role identity first. Different families "
     "coexist; the same family takes LOCAL / FLOOR-SPECIFIC PLAN NOTE > GENERIC TYPICAL DETAIL, never summed; the "
     "loser is OVERRIDDEN_PROJECT_SOURCE. Unresolved identity blocks that top family only."),
    ("AD2-D06", "§6", "ONE_THIRD_SPAN_BASIS", "Where plan note 2 governs and its origin is not explicit: "
     "URBAN_QTO_TOP_OVER_SUPPORT_EXTENT_V1 = 1/3 x CLEAR_SPAN from the SUPPORT FACE into the panel, authority "
     "URBAN_OWNER_MEASUREMENT_RULE (not PROJECT_SOURCE_EXPLICIT)."),
    ("AD2-D07", "§7", "TEMPERATURE_NO_INTERPOLATION", "160 mm (and 180 mm): TABLE_NO_EXACT_ROW, BLOCKED_UNQUANTIFIED. "
     "A blocked temperature component blocks nothing else."),
    ("AD2-D08", "§8", "WATER_TANK_TO_S8", "The two water-tank panels and their T 18 / local reinforcement go to "
     "S8_SPECIAL_STRUCTURE / WATER_TANK_SUPPORT_REGION (ownership transfer, nothing lost)."),
    ("AD2-D09", "§9", "LIGHTWELL_TO_S8", "The light-well / void + stair + T 16 + 8Ø16/m face goes to "
     "S8_SPECIAL_STRUCTURE / STAIR_LIGHTWELL_REGION with SOURCE_CONFLICT_PRESERVED."),
    ("AD2-D10", "§10", "MISMATCH_SPLIT", "Different callouts across a continuous support: LEFT_PANEL_BAR_RUN and "
     "RIGHT_PANEL_BAR_RUN to the support face; continuation / lap / splice / development / transition blocked. "
     "Nothing chosen by majority, size, rate or nearest value."),
    ("AD2-D11", "§11", "LOCAL_TOP_OVERRIDE", "A local '/Top' callout bound to a support overrides the general top "
     "rule for the same role at that location (LOCAL_SOURCE_OVERRIDE / GENERAL_RULE_SUPERSEDED_FOR_ROLE); not "
     "additive without evidence of a second family."),
    ("AD2-D12", "§12", "SUNKEN_MESH_RETAINED", "A sunken panel keeps its normal mesh in S7; SUNKEN_STEP_VERTICAL_"
     "REBAR, SUNKEN_EDGE_EXTRA and LEVEL_CHANGE_DETAIL are separate and blocked unless specified."),
    ("AD2-D13", "§13", "DENSE_HATCH_BY_GEOMETRY", "The dense hatch is classified by geometry, not by the hatch: "
     "outside the perimeter and attached along one support -> CANTILEVER_CANDIDATE; a strip filling a support band "
     "-> BEARING_WALL_CANDIDATE; otherwise CLASSIFICATION_BLOCKED."),
    ("AD2-D14", "§14", "LOCAL_BAR_LINE_MODEL", "Irregular panels are measured by local bar lines: strips per bar "
     "direction, clipped to support faces and openings; the local clear run (and the local L of a span rule) is "
     "URBAN_QTO_LOCAL_BAR_LINE_V1. No bounding rectangle."),
    ("AD2-D15", "§15", "PHYSICAL_CONTINUITY", "No structural slab beyond (outside, void, open to below, no slab) -> "
     "NON_CONTINUOUS; a physical slab beyond that is blocked / special / transferred / at another level / over a "
     "non-beam support -> CONTINUITY_UNRESOLVED. Excluded ownership is not physical absence."),
    ("AD2-D16", "§16", "AMBIGUOUS_CALLOUTS_UNRESOLVED", "'40 CL.' and any callout whose binding is not proven stay "
     "unresolved; no quantity depends on them; nothing is read from graphic scale."),
    ("AD2-D17", "§17", "MINIMUM_COVER_IS_PROJECT_BASIS", "25 mm is MINIMUM_PROJECT_COVER (D1.2). Any quantity using "
     "it as a number is PROJECT_BASIS_QTO, never SOURCE_EXACT or AS_BUILT."),
]


# ------------------------------------------------------------------ geometry helpers
def bbox(ring):
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    return (min(xs), min(ys), max(xs), max(ys))


def in_face(pt, row):
    return SC.point_in_ring(pt, row["polygon_mm"]) and not any(SC.point_in_ring(pt, h)
                                                                for h in row["holes_mm"] or [])


def edge_seg(row, i):
    ring = row["polygon_mm"]
    return tuple(ring[i]), tuple(ring[(i + 1) % len(ring)])


def seg_on_rect_side(seg, rect, tol=HATCH_TOL_MM):
    """Length of a boundary segment lying on a long side of a hatch rectangle."""
    x0, y0, x1, y1 = rect
    horiz = (x1 - x0) >= (y1 - y0)
    best = 0.0
    for c in ((y0, y1) if horiz else (x0, x1)):
        best = max(best, Q._seg_on_line(seg, horiz, c, x0 if horiz else y0, x1 if horiz else y1, tol))
    return best


def structural_lines(E, sheet):
    out = []
    for e in E[sheet]:
        if e["layer"] not in S.BEAM_LAYERS:
            continue
        if e["type"] == "LINE":
            out.append((tuple(e["a"]), tuple(e["b"])))
        elif e["type"] == "LWPOLYLINE" and e.get("pts"):
            pts = [tuple(p) for p in e["pts"]]
            out += list(zip(pts, pts[1:] + ([pts[0]] if e.get("closed") else [])))
    return out


# ------------------------------------------------------------------ build
def build():
    frozen = verify_inputs()
    census = _rows("01_SLAB_PANEL_CENSUS.csv")
    tokens = _rows("03_SLAB_REBAR_TOKENS.csv")
    comps = _rows("04_COMPONENT_READINESS.csv")
    supports = _rows("05_SUPPORT_REGISTER.csv")
    rules = {r["RULE_ID"]: r for r in _rows("06_SUPPORT_RULES.csv")}
    runs = _rows("07_BAR_RUN_REGISTER.csv")
    conflicts_pre = _rows("11_SOURCE_CONFLICTS.csv")
    pre_summary = _j(PRE / "PRE_S7_SUMMARY.json")
    s1 = {r["panel_id"]: r for r in _j(S1 / "SLAB_PANEL_REGISTER.json")["rows"]}
    s1rules = {r["rule_id"]: r for r in _j(S1 / "STRUCTURAL_PROJECT_RULE_REGISTER.json")["rows"]}
    temp_table = {int(k): v for k, v in s1rules["P15-TEMP-TABLE"]["values"]["rows"].items()}
    cs = {c["SLAB_PANEL_ID"]: c for c in census}
    tok = {t["TOKEN_ID"]: t for t in tokens}
    check(len(comps) == 440 and len(supports) == 172, "PRE-S7 populations as frozen")
    src = S.Source(DXF)
    E = src.entities()

    # ---------------------------------------------------- panel ownership in AD2
    in_scope = sorted(p for p, c in cs.items() if c["SCOPE"] == SR.IN_SCOPE)
    tank = sorted(p for p, c in cs.items() if c["PANEL_CLASS"] == "WATER_TANK_PLACE_SLAB")
    lightwell = sorted(p for p, c in cs.items() if c["CONFLICT"] == SR.SOURCE_CONFLICT and not p.startswith("HZ-"))
    check(len(tank) == 2 and len(lightwell) == 1, f"tank {tank} / light well {lightwell}")
    region = {**{p: TANK_REGION for p in tank}, **{p: LIGHTWELL_REGION for p in lightwell}}
    sunken = sorted(p for p in in_scope if cs[p]["PANEL_CLASS"] == "SUNKEN_SLAB")
    rect = {p: cs[p]["SPAN_STATE"] == "SINGLE_VALUED_FACE_TO_FACE" for p in in_scope}

    def side_class(p):
        if not p:
            return "NO_SLAB"
        c = cs[p]
        if c["SCOPE"] == SR.IN_SCOPE:
            return "SLAB_IN_SCOPE"
        if p in region:
            return "SLAB_TRANSFERRED"
        if c["SCOPE"] == SR.EXCLUDED_SPECIAL:
            return "SLAB_EXCLUDED_SPECIAL"
        if c["SCOPE"] == SR.VOID_OR_OPENING:
            return "OPEN_TO_BELOW"
        if c["SCOPE"] == SR.NOT_SLAB:
            return "OUTSIDE_BUILDING" if c["PANEL_CLASS"] == "OUTSIDE_BUILDING_OR_COURT" else "NO_SLAB"
        return "SLAB_CLASSIFICATION_BLOCKED"

    # ---------------------------------------------------- §13 dense hatch by geometry
    hatch_rows = []
    lines_of = {sh: structural_lines(E, sh) for sh in ("GFRS", "FFRS", "SFRS")}
    physical = ("SLAB_PANEL", "STAIR_FLIGHT_ZONE", "STAIR_IN_VOID_ZONE", "DOME_ZONE")
    for hid, c in sorted(cs.items()):
        if not hid.startswith("HZ-"):
            continue
        sh = c["SOURCE_SHEET"]
        rx0, ry0, rx1, ry1 = _js(c["BBOX_MM"])
        horiz = (rx1 - rx0) >= (ry1 - ry0)

        def beyond(side, sh=sh, r=(rx0, ry0, rx1, ry1), horiz=horiz):
            x0, y0, x1, y1 = r
            probes = []
            for k in (0.25, 0.5, 0.75):
                if horiz:
                    x = x0 + k * (x1 - x0)
                    probes.append((x, y0 - 100) if side == "LOW" else (x, y1 + 100))
                else:
                    y = y0 + k * (y1 - y0)
                    probes.append((x0 - 100, y) if side == "LOW" else (x1 + 100, y))
            return any(in_face(q, f) for q in probes for f in s1.values()
                       if f["sheet"] == sh and f["class"] in physical)
        hc = Q.hatch_classification((rx0, ry0, rx1, ry1), structural_lines=lines_of[sh],
                                    slab_faces_beyond=beyond, tol=HATCH_TOL_MM)
        hatch_rows.append({"id": hid, "sheet": sh, "rect": [rx0, ry0, rx1, ry1], **hc})
    hatch_state = {h["id"]: h["state"] for h in hatch_rows}

    # ---------------------------------------------------- supports: views, AD2 continuity (§15), hatch bands
    view_sup = {}
    sup = {s["SUPPORT_ID"]: s for s in supports}
    for s in supports:
        for v in _js(s["VIEWS"]):
            p, i = v.rsplit("#", 1)
            view_sup[(p, int(i))] = s["SUPPORT_ID"]
    ad2_sup = {}
    for s in supports:
        sid = s["SUPPORT_ID"]
        L, Rt = s["LEFT_PANEL"] or None, s["RIGHT_PANEL"] or None
        cont = {}
        for me, other in ((L, Rt), (Rt, L)):
            if me and cs[me]["SCOPE"] == SR.IN_SCOPE:
                oc = side_class(other)
                step = oc == "SLAB_IN_SCOPE" and ((me in sunken) != (other in sunken))
                cont[me] = Q.edge_continuity(other_side=oc, support_kind=s["SUPPORT_KIND"], level_step=step)
        states = sorted({v["state"] for v in cont.values()})
        band = []
        for h in hatch_rows:
            if h["sheet"] != s["SHEET"] or h["state"] != Q.BEARING_WALL_CANDIDATE:
                continue
            ov = 0.0
            for v in _js(s["VIEWS"]):
                p, i = v.rsplit("#", 1)
                ov += seg_on_rect_side(edge_seg(s1[p], int(i)), h["rect"])
            if ov > BAND_OVERLAP_MIN_MM:
                band.append({"hatch": h["id"], "overlap_mm": round(ov, 1)})
        ad2_sup[sid] = {"continuity": states[0] if len(states) == 1 else (SR.CONTINUITY_UNRESOLVED if states else None),
                        "why": sorted({v["why"] for v in cont.values()}), "sides": [L, Rt],
                        "side_class": {"LEFT": side_class(L), "RIGHT": side_class(Rt)},
                        "s7_sides": [p for p in (L, Rt) if p and cs[p]["SCOPE"] == SR.IN_SCOPE],
                        "bearing_wall_band": band, "pre_s7_type": s["SUPPORT_TYPE"]}

    # ---------------------------------------------------- bottom families (from the PRE-S7 components)
    fam = {}
    for c in comps:
        if not c["BAR_ROLE"].startswith("BOTTOM_") and c["COMPONENT"] not in ("TOP_X", "TOP_Y"):
            continue
        t = tok[c["TOKEN"]]
        pid = t["BOUND_TO"] if t["BOUND_TO"].startswith("SP-") else c["OWNER"]
        if c["COMPONENT"] in ("BOTTOM_X", "BOTTOM_Y", "CURTAILMENT_SEGMENT", "TOP_X", "TOP_Y"):
            pid = c["OWNER"]
        key = (pid, c["DIRECTION"], "TOP" if c["COMPONENT"] in ("TOP_X", "TOP_Y") else "BOTTOM")
        f = fam.setdefault(key, {"panel": pid, "direction": c["DIRECTION"], "layer": key[2], "token": c["TOKEN"],
                                 "dia_mm": int(c["DIA_MM"]), "count_mode": c["COUNT_MODE"],
                                 "rate": _f(c["RATE_OR_COUNT"]), "parents": {}, "run": c["BAR_RUN_ID"] or None,
                                 "blockers": set(_js(c["BLOCKERS"])), "layer_authority": c["LAYER_AUTHORITY"]})
        role = {"CURTAILMENT_SEGMENT": "curt", "CONTINUOUS_BAR_RUN": "cont"}.get(c["COMPONENT"], "single")
        check(role not in f["parents"], f"one component per role for {key}")
        f["parents"][role] = c["COMPONENT_ID"]
        if c["BAR_RUN_ID"]:
            f["run"] = c["BAR_RUN_ID"]
    for f in fam.values():
        if f["panel"] in region:
            f["state"] = Q.TRANSFERRED_S8
        elif f["count_mode"] != "BARS_PER_METRE":
            f["state"] = "COUNT_NOTATION_AMBIGUOUS"
        elif "SOURCE_CONFLICT_TWO_CALLOUTS_ONE_DIRECTION" in f["blockers"]:
            f["state"] = "TWO_CALLOUTS_ONE_DIRECTION"
        else:
            f["state"] = "RESOLVED"
    bfam = {(k[0], k[1]): v for k, v in fam.items() if k[2] == "BOTTOM"}

    # ---------------------------------------------------- §14 local bar strips (every in-scope panel, X and Y)
    sup_key = defaultdict(list)
    for s_ in supports:
        sides = frozenset(p for p in (s_["LEFT_PANEL"], s_["RIGHT_PANEL"]) if p)
        sup_key[(s_["SHEET"], s_["SUPPORT_REF"], sides)].append(s_["SUPPORT_ID"])
    check(all(len(v) == 1 for k, v in sup_key.items() if len(k[2]) == 2),
          "one PRE-S7 support per (sheet, ref, two sides); exterior supports are one per edge")
    s1edge = {(pid, e["edge_index"]): e for pid, r in s1.items() for e in (r["edges"] or [])}
    width_of = defaultdict(set)
    for s_ in supports:
        if s_["SUPPORT_WIDTH_MM"]:
            width_of[(s_["SHEET"], s_["SUPPORT_REF"])].add(float(s_["SUPPORT_WIDTH_MM"]))
    ABSENT = Q.OTHER_SIDE_ABSENT

    def near_faces(pid, margin=1500.0):
        r = s1[pid]
        x0, y0, x1, y1 = bbox(r["polygon_mm"])
        out = {}
        for fid, f in s1.items():
            if fid == pid or f["sheet"] != r["sheet"] or not f["polygon_mm"]:
                continue
            b = bbox(f["polygon_mm"])
            if b[0] <= x1 + margin and b[2] >= x0 - margin and b[1] <= y1 + margin and b[3] >= y0 - margin:
                out[fid] = ([tuple(q) for q in f["polygon_mm"]], [[tuple(q) for q in h] for h in f["holes_mm"] or []])
        return out

    def resolve_end(pid, d, x, end, faces):
        ring, i = x[end]
        if ring > 0:
            return {"kind": "OPENING", "support": None, "square": None, "neighbour": None, "source": "HOLE"}
        a, b = edge_seg(s1[pid], i)
        square = Q.edge_crossing_direction(a, b) == d
        e = s1edge.get((pid, i))
        if e is None:
            return {"kind": "NO_SUPPORT_RECORD", "support": None, "square": square, "neighbour": None,
                    "source": "NO_S1_EDGE"}
        sh = s1[pid]["sheet"]
        ref = e["support_ref"]
        ref_s = str(ref) if ref is not None else ""
        outward = -1 if end == "start_edge" else +1
        sv = x["s_start"] if end == "start_edge" else x["s_end"]
        ws = width_of.get((sh, ref_s))
        max_gap = GAP_FACTOR * max(ws) if ws else 1000.0
        tm = 0.5 * (x["t0"] + x["t1"])
        hit = Q.face_beyond(0.5 * (sv[0] + sv[1]), tm, outward, faces, d, max_gap)
        out = {"kind": "SUPPORT", "square": square, "support_kind": e["support"], "ref": ref_s}
        if hit:
            nb = hit["face"]
            via = view_sup.get((pid, i))
            pr = Q.edge_projection(*hit["edge"], d)
            g = None
            if pr and pr["t0"] <= x["t0"] + SPAN_TOL_MM and pr["t1"] >= x["t1"] - SPAN_TOL_MM:
                g = (abs(pr["s_at"](x["t0"]) - sv[0]), abs(pr["s_at"](x["t1"]) - sv[1]))
            out.update(neighbour=nb, source="GEOMETRY", gap=g)
            pair = sup_key.get((sh, ref_s, frozenset({pid, nb})))
            if pair:
                out["support"] = pair[0]
                return out
            if side_class(nb) in ABSENT:
                if via and all(side_class(p) in ABSENT for p in ad2_sup[via]["sides"] if p and p != pid):
                    out["support"] = via
                    out["source"] = "GEOMETRY (no slab beyond; the edge's own PRE-S7 support)"
                    return out
                one = sup_key.get((sh, ref_s, frozenset({pid})))
                if one and len(one) == 1:
                    out["support"] = one[0]
                    out["source"] = "GEOMETRY (no slab beyond; the panel's exterior support on this ref)"
                    return out
            if via:                    # owner: the edge's PRE-S7 support; physics: the face found beyond
                out["support"] = via
                out["source"] = "GEOMETRY (neighbour; S1 named another, owner kept: the edge's PRE-S7 support)"
                return out
            out.update(kind="NO_SUPPORT_RECORD", support=None, source="GEOMETRY (no PRE-S7 support for this edge)")
            return out
        via = view_sup.get((pid, i))
        other = [q for q in ad2_sup[via]["sides"] if q and q != pid] if via else []
        out.update(neighbour=other[0] if other else None, source="S1_EDGE (no face within reach)", gap=None,
                   support=via)
        if not via:
            out["kind"] = "NO_SUPPORT_RECORD"
        return out

    strips = {}
    strip_rows = []
    recon = {}
    for pid in in_scope:
        r = s1[pid]
        poly = [tuple(p) for p in r["polygon_mm"]]
        holes = [[tuple(p) for p in h] for h in r["holes_mm"] or []]
        faces = near_faces(pid)
        for d in ("X", "Y"):
            k_t = 1 if d == "X" else 0
            breaks = sorted({q[k_t] for f in faces.values() for q in f[0]})
            st = Q.bar_strips(poly, holes, d, extra_breaks=breaks)
            rc = Q.strips_reconcile(poly, holes, d, rel_tol=1e-9)
            got = Q.strips_integral(st)
            rc["integral_with_breaks"] = got
            rc["reconciled"] = rc["reconciled"] and abs(got - rc["area"]) <= 1e-9 * max(rc["area"], 1.0)
            recon[(pid, d)] = rc
            for k, x in enumerate(st):
                x["id"] = f"LBS-{pid[3:]}-{d}-{k + 1:03d}"
                x["panel"], x["direction"] = pid, d
                for end in ("start_edge", "end_edge"):
                    x[end + "_ref"] = resolve_end(pid, d, x, end, faces)
            strips[(pid, d)] = st

    def end_class(pid, d, ref):
        if ref["kind"] == "OPENING":
            return Q.END_OPENING, None
        if ref["kind"] == "NO_SUPPORT_RECORD":
            return Q.END_NO_SUPPORT, None
        sid = ref["support"]
        if not ref["square"] or sup[sid]["BARS_CROSSING"] != d:
            return Q.END_OBLIQUE, sid
        other = ref["neighbour"]
        oc = side_class(other)
        step = oc == "SLAB_IN_SCOPE" and ((pid in sunken) != (other in sunken))
        st_ = Q.edge_continuity(other_side=oc, support_kind=ref["support_kind"], level_step=step)["state"]
        if st_ == SR.NON_CONTINUOUS:
            return Q.END_NON_CONTINUOUS, sid
        if st_ == SR.CONTINUITY_UNRESOLVED:
            return Q.END_UNRESOLVED, sid
        mf, of = bfam.get((pid, d)), bfam.get((other, d))
        if mf and of and mf["state"] == of["state"] == "RESOLVED" and mf["dia_mm"] == of["dia_mm"] and \
                mf["rate"] == of["rate"]:
            return Q.END_CONTINUOUS_RUN, sid
        return Q.END_CONTINUOUS_SPLIT, sid

    for (pid, d), st in sorted(strips.items()):
        for x in st:
            ec0, s0 = end_class(pid, d, x["start_edge_ref"])
            ec1, s1_ = end_class(pid, d, x["end_edge_ref"])
            x["end_classes"] = (ec0, ec1)
            x["end_supports"] = (s0, s1_)
            strip_rows.append({
                "LOCAL_BAR_STRIP_ID": x["id"], "PANEL": pid, "FLOOR": cs[pid]["FLOOR"], "BAR_DIRECTION": d,
                "PANEL_SHAPE": "RECTANGULAR" if rect[pid] else "IRREGULAR",
                "TRANSVERSE_POSITION_MM": [_r(x["t0"], 1), _r(x["t1"], 1)], "STRIP_WIDTH_MM": _r(x["width"], 1),
                "START_SUPPORT": s0 or x["start_edge_ref"]["kind"], "END_SUPPORT": s1_ or x["end_edge_ref"]["kind"],
                "START_NEIGHBOUR": x["start_edge_ref"].get("neighbour"),
                "END_NEIGHBOUR": x["end_edge_ref"].get("neighbour"),
                "NEIGHBOUR_SOURCE": [x["start_edge_ref"]["source"], x["end_edge_ref"]["source"]],
                "START_EDGE": x["start_edge"], "END_EDGE": x["end_edge"],
                "START_CONDITION": ec0, "END_CONDITION": ec1,
                "LOCAL_CLEAR_SPAN_MM": [_r(x["L0"], 1), _r(x["L1"], 1)],
                "LOCAL_RUN_LENGTH_MEAN_MM": _r(0.5 * (x["L0"] + x["L1"]), 1),
                "RUN_INTEGRAL_M2": _r(x["integral"] / 1e6, 6),
                "OPENING_INTERSECTIONS": sum(1 for e in ("start_edge", "end_edge") if x[e][0] > 0),
                "MEASUREMENT_RULE": Q.URBAN_LOCAL_BAR_LINE_RULE if not rect[pid] else
                "PROJECT_GEOMETRY (rectangular: local run = clear span)"})

    # ---------------------------------------------------- quantity items
    items = []

    def add(**kw):
        kw.setdefault("KG", None)
        kw["QTO_ITEM_ID"] = f"QI-{len(items) + 1:05d}"
        check(kw.get("LANE") in Q.LANES + (Q.TRANSFERRED_S8,), f"lane of {kw}")
        items.append(kw)
        return kw

    comp_by_id = {c["COMPONENT_ID"]: c for c in comps}

    def rate_fields(rate, frac, width_mm):
        rq = Q.rate_qto(rate, width_mm, fraction=frac)
        return {"COUNT_BASIS": rq["count_basis"], "RATE_PER_M": rate, "DENSITY_FRACTION": frac,
                "DISTRIBUTION_WIDTH_MM": _full(width_mm), "EQUIVALENT_BAR_COUNT": _full(rq["equivalent_bar_count"]),
                "PHYSICAL_BBS_BAR_COUNT": rq["physical_bbs_bar_count"]}

    # bottom families
    fifty_rows = []
    for (pid, d, layer), f in sorted(fam.items()):
        par = f["parents"]
        if f["state"] != "RESOLVED":
            for role, cid in sorted(par.items()):
                if f["state"] == Q.TRANSFERRED_S8:
                    add(PARENT_COMPONENT_ID=cid, ITEM="TRANSFERRED_FAMILY", OWNER=pid, FLOOR=cs[pid]["FLOOR"],
                        DIRECTION=d, DIA_MM=f["dia_mm"], LANE=Q.TRANSFERRED_S8, S8_REGION=region[pid],
                        AUTHORITY=["AD2-D08" if region[pid] == TANK_REGION else "AD2-D09"])
                else:
                    blk = ("COUNT_NOTATION_AMBIGUOUS_NO_PER_METRE" if f["state"] == "COUNT_NOTATION_AMBIGUOUS" else
                           "SOURCE_CONFLICT_TWO_CALLOUTS_ONE_DIRECTION")
                    add(PARENT_COMPONENT_ID=cid, ITEM="FAMILY_BLOCKED", OWNER=pid, FLOOR=cs[pid]["FLOOR"],
                        DIRECTION=d, DIA_MM=f["dia_mm"], COUNT_BASIS=Q.COUNT_UNRESOLVED, LANE=Q.BLOCKED_UNQUANTIFIED,
                        BLOCKERS=[blk], QUESTIONS=["Q-ABSCOUNT" if "COUNT" in blk else "Q-TWOCALL"],
                        AUTHORITY=["AD2-D03"] if "COUNT" in blk else ["AD2-D05"])
            continue
        check(layer == "BOTTOM", f"only bottom families resolve here: {pid} {d}")
        split_parents = "curt" in par and "cont" in par
        agg = defaultdict(lambda: {"width": 0.0, "integral": 0.0, "strips": []})
        blocked = defaultdict(lambda: {"width": 0.0, "strips": []})
        for x in strips[(pid, d)]:
            its = Q.bottom_strip_items(x["L0"], x["L1"], x["width"], *x["end_classes"], stop_fraction=STOP_FRACTION)
            check(Q.item_density_check(its), f"density budget {x['id']}")
            for it in its:
                kind = it["item"]
                halves = [(kind, it["density_fraction"])]
                if split_parents and kind == "IN_PANEL":
                    halves = [("IN_PANEL_CONTINUING", 0.5), ("IN_PANEL_CURTAILED", 0.5)]
                elif split_parents and kind in ("END_ANCHORAGE", "END_DETAIL_AT_OPENING"):
                    halves = [(kind + "|cont", 0.5), (kind + "|curt", 0.5)]
                for h, frac in halves:
                    if it["lane_hint"] == "RELEASE":
                        integ = it["integral"]          # a half on a strip without a curtailing end runs in full
                        a = agg[(h, frac)]
                        a["width"] += it["width"]
                        a["integral"] += integ
                        a["strips"].append(x["id"])
                    else:
                        sid = x["end_supports"][it["end"]]
                        b = blocked[(h, frac, it.get("end_class"), sid)]
                        b["width"] += it["width"]
                        b["strips"].append(x["id"])
        bases_geo = [Q.EXTENT_PROJECT_GEOMETRY] + ([] if rect[pid] else [Q.EXTENT_URBAN_RULE])
        auth_geo = ["AD2-D02"] + ([] if rect[pid] else ["AD2-D14"])

        def parent_of(kind):
            base, _, half = kind.partition("|")
            if not split_parents:
                return par["single"]
            if half == "cont" or base in ("IN_PANEL_CONTINUING", "TRANSITION", "BEYOND_FACE_UNRESOLVED"):
                return par["cont"]
            return par["curt"]
        for (kind, frac), a in sorted(agg.items()):
            base = kind.split("|")[0]
            curt = base == "IN_PANEL_CURTAILED"
            rule = {"IN_PANEL": "face to face along each local bar line",
                    "IN_PANEL_CONTINUING": "face to face along each local bar line (the continuing half reaches "
                                           "every face)",
                    "IN_PANEL_CURTAILED": "face to face less 0.125 x local L at each continuous and each "
                                          "continuity-unresolved end (P15-BOT-STOP-0.125L)"}[base]
            ext = bases_geo + ([Q.EXTENT_PROJECT_RULE] if curt else [])
            add(PARENT_COMPONENT_ID=parent_of(kind), ITEM=f"BOTTOM_{base}", OWNER=pid, FLOOR=cs[pid]["FLOOR"],
                DIRECTION=d, DIA_MM=f["dia_mm"], RUN_ID=f["run"],
                **rate_fields(f["rate"], frac, a["width"]), RUN_INTEGRAL_M2=_r(a["integral"] / 1e6, 6),
                MEAN_RUN_MM=_r(a["integral"] / a["width"], 1), RUN_RULE=rule, EXTENT_BASES=ext,
                LANE=Q.lane(Q.COUNT_RATE_DENSITY, ext),
                AUTHORITY=auth_geo + (["AD2-D04", "P15-BOT-STOP-0.125L"] if base != "IN_PANEL" else []),
                LAYER_AUTHORITY=f["layer_authority"], STRIPS=len(a["strips"]))
        for (kind, frac, ecl, sid), b in sorted(blocked.items(), key=lambda kv: (kv[0][0], str(kv[0][3]),
                                                                                  str(kv[0][2]))):
            base = kind.split("|")[0]
            why = {"END_ANCHORAGE": ("END_ANCHORAGE_SHAPE_ONLY", "Q-ANCHOR"),
                   "END_DETAIL_AT_OPENING": ("OPENING_END_DETAIL_NOT_LOCATED", "Q-OPENING"),
                   "TRANSITION": ("TRANSITION_ACROSS_SUPPORT_NOT_ESTABLISHED", "Q-MISMATCH"),
                   "STOP_ZONE_UNRESOLVED": ("STOP_ZONE_DEPENDS_ON_UNRESOLVED_CONTINUITY", "Q-CONT"),
                   "BEYOND_FACE_UNRESOLVED": ("BEYOND_FACE_DEPENDS_ON_UNRESOLVED_CONTINUITY", "Q-CONT")}[base]
            q = why[1]
            if base in ("STOP_ZONE_UNRESOLVED", "BEYOND_FACE_UNRESOLVED"):
                q = {Q.END_OBLIQUE: "Q-OBLIQUE", Q.END_NO_SUPPORT: "Q-CONT"}.get(ecl, q)
                if ecl == Q.END_UNRESOLVED and sid and any("another level" in w for w in ad2_sup[sid]["why"]):
                    q = "Q-SUNKEN"
            add(PARENT_COMPONENT_ID=parent_of(kind), ITEM=f"BOTTOM_{base}", OWNER=pid, FLOOR=cs[pid]["FLOOR"],
                DIRECTION=d, DIA_MM=f["dia_mm"], RUN_ID=f["run"], SUPPORT_ID=sid, END_CONDITION=ecl,
                COUNT_BASIS=Q.COUNT_RATE_DENSITY, RATE_PER_M=f["rate"], DENSITY_FRACTION=frac,
                DISTRIBUTION_WIDTH_MM=_r(b["width"], 1),
                EQUIVALENT_BAR_COUNT=None if frac is None else f["rate"] * frac * b["width"] / 1000.0,
                PHYSICAL_BBS_BAR_COUNT=Q.UNRESOLVED, EXTENT_BASES=[Q.EXTENT_BLOCKED], LANE=Q.BLOCKED_UNQUANTIFIED,
                BLOCKERS=[why[0]], QUESTIONS=[q], STRIPS=len(b["strips"]),
                AUTHORITY=["AD2-D10"] if base == "TRANSITION" else ["AD2-D15"] if "UNRESOLVED" in base else
                ["AD2-D16"])
        if split_parents:
            fifty_rows.append({"FAMILY": f"{pid}:{d}", "PANEL": pid, "FLOOR": cs[pid]["FLOOR"], "DIRECTION": d,
                               "TOKEN": f["token"], "DIA_MM": f["dia_mm"], "RATE_PER_M": f["rate"],
                               "CURTAILMENT_COMPONENT": par["curt"], "CONTINUOUS_COMPONENT": par["cont"],
                               "SOURCE_RULE": "P15-BOT-STOP-0.125L ('STOP 50% OF BOT. REINF. BALANCE CONTINUOUS')",
                               "WHICH_50_PERCENT_SOURCE": rules["P15-BOT-STOP-0.125L"]["WHICH_50_PERCENT"],
                               "CONTINUOUS_DENSITY_FRACTION": 0.5, "CURTAILED_DENSITY_FRACTION": 0.5,
                               "QTO_BASIS": Q.DENSITY_50_50, "PHYSICAL_SEQUENCING": Q.UNRESOLVED,
                               "ODD_COUNT_RULE": "none assigned (BBS_AMBIGUOUS_ODD_COUNT where a physical count is "
                                                 "odd)", "AUTHORITY": "AD2-D04"})

    # bottom crossings of continuous supports: the continuing half, once per (support, pair), from the lower-id side
    cross_acc = defaultdict(lambda: {"width": 0.0, "integral": 0.0, "gap_unknown": 0.0, "gaps": []})
    seen_hi = defaultdict(lambda: defaultdict(float))
    split_acc = {}
    for (pid, d), st in sorted(strips.items()):
        f = bfam.get((pid, d))
        for x in st:
            for k, end in enumerate(("start_edge_ref", "end_edge_ref")):
                ref, ec = x[end], x["end_classes"][k]
                nb = ref.get("neighbour")
                if ec == Q.END_CONTINUOUS_RUN and pid > nb:
                    seen_hi[(nb, pid, d)][ref["support"]] += x["width"]
                elif ec == Q.END_CONTINUOUS_RUN and pid < nb:
                    c = cross_acc[(ref["support"], pid, nb, d)]
                    if ref.get("gap"):
                        c["width"] += x["width"]
                        c["integral"] += 0.5 * (ref["gap"][0] + ref["gap"][1]) * x["width"]
                        c["gaps"] += list(ref["gap"])
                    else:
                        c["gap_unknown"] += x["width"]
                elif ec == Q.END_CONTINUOUS_SPLIT and f and f["state"] == "RESOLVED":
                    lo, hi = sorted((pid, nb))
                    split_acc.setdefault((ref["support"], lo, hi, d), {"width": 0.0})["width"] += x["width"]
    for (sid, pa, pb, d), c in sorted(cross_acc.items()):
        fa, fb = bfam[(pa, d)], bfam[(pb, d)]
        parent = fa["parents"].get("cont") or fa["parents"].get("single")
        run = fa["run"] if fa["run"] == fb["run"] else f"{fa['run']}+{fb['run']} (joined by AD2 geometric continuity)"
        base = dict(PARENT_COMPONENT_ID=parent, ITEM="BOTTOM_SUPPORT_CROSSING", OWNER=sid, FLOOR=sup[sid]["FLOOR"],
                    DIRECTION=d, DIA_MM=fa["dia_mm"], RUN_ID=run, SUPPORT_ID=sid, SIDE_PANEL=f"{pa}|{pb}",
                    LAYER_AUTHORITY=fa["layer_authority"])
        if c["width"] > 1.0:
            ext = [Q.EXTENT_PROJECT_GEOMETRY]
            add(**base, **rate_fields(fa["rate"], 0.5, c["width"]), RUN_INTEGRAL_M2=_r(c["integral"] / 1e6, 6),
                MEAN_RUN_MM=_r(c["integral"] / c["width"], 1),
                RUN_RULE="over the support between the two panel faces along each bar line (the continuing half, "
                         "counted once per support and pair)", EXTENT_BASES=ext,
                LANE=Q.lane(Q.COUNT_RATE_DENSITY, ext), AUTHORITY=["AD2-D02", "AD2-D04", "AD2-D15",
                                                                   "P15-BOT-STOP-0.125L"])
        if c["gap_unknown"] > 1.0:
            add(**base, COUNT_BASIS=Q.COUNT_RATE_DENSITY, RATE_PER_M=fa["rate"], DENSITY_FRACTION=0.5,
                DISTRIBUTION_WIDTH_MM=_r(c["gap_unknown"], 1), EXTENT_BASES=[Q.EXTENT_BLOCKED],
                LANE=Q.BLOCKED_UNQUANTIFIED, BLOCKERS=["CROSSING_GEOMETRY_NOT_RESOLVED (the far face does not span "
                                                       "the strip)"], QUESTIONS=["Q-CONT"], AUTHORITY=["AD2-D14"])
    lo_w = defaultdict(float)
    for (sid, pa, pb, d), c in cross_acc.items():
        lo_w[(pa, pb, d)] += c["width"] + c["gap_unknown"]
    for (pa, pb, d), by_sid in sorted(seen_hi.items()):
        excess = sum(by_sid.values()) - lo_w.get((pa, pb, d), 0.0)
        if excess > 1.0:
            sid = max(sorted(by_sid), key=lambda k: by_sid[k])
            fb = bfam[(pb, d)]
            add(PARENT_COMPONENT_ID=fb["parents"].get("cont") or fb["parents"].get("single"),
                ITEM="BOTTOM_SUPPORT_CROSSING", OWNER=sid, FLOOR=sup[sid]["FLOOR"], DIRECTION=d, DIA_MM=fb["dia_mm"],
                RUN_ID=fb["run"], SUPPORT_ID=sid, SIDE_PANEL=f"{pb}>{pa}", COUNT_BASIS=Q.COUNT_RATE_DENSITY,
                RATE_PER_M=fb["rate"], DENSITY_FRACTION=0.5, DISTRIBUTION_WIDTH_MM=_r(excess, 1),
                EXTENT_BASES=[Q.EXTENT_BLOCKED], LANE=Q.BLOCKED_UNQUANTIFIED,
                BLOCKERS=["CROSSING_SEEN_FROM_ONE_FACE_ONLY (a junction / set-back beyond one face)"],
                QUESTIONS=["Q-CONT"], AUTHORITY=["AD2-D14"])
    split_rows = []
    for (sid, pa, pb, d), v in sorted(split_acc.items()):
        fa, fb = bfam.get((pa, d)), bfam.get((pb, d))
        spec = Q.mismatch_split(sid, {"family": f"{pa}:{d}", "dia_mm": fa["dia_mm"], "rate": fa["rate"]}
                                if fa and fa["state"] == "RESOLVED" else None,
                                {"family": f"{pb}:{d}", "dia_mm": fb["dia_mm"], "rate": fb["rate"]}
                                if fb and fb["state"] == "RESOLVED" else None)
        check(spec["state"] == "SPLIT_AT_SUPPORT", f"{sid} split")
        split_rows.append({"SUPPORT_ID": sid, "FLOOR": sup[sid]["FLOOR"], "SUPPORT_REF": sup[sid]["SUPPORT_REF"],
                           "BAR_DIRECTION": d, "LEFT_PANEL": pa, "RIGHT_PANEL": pb,
                           "LEFT_FAMILY": f"{pa}:{d}" if fa else None,
                           "LEFT_SPEC": f"{fa['dia_mm']}@{fa['rate']:g}/m ({fa['state']})" if fa else "NO_FAMILY",
                           "RIGHT_FAMILY": f"{pb}:{d}" if fb else None,
                           "RIGHT_SPEC": f"{fb['dia_mm']}@{fb['rate']:g}/m ({fb['state']})" if fb else "NO_FAMILY",
                           "SHARED_WIDTH_MM": _r(v["width"], 1),
                           "LEFT_PANEL_BAR_RUN": spec["runs"][0]["run"], "RIGHT_PANEL_BAR_RUN": spec["runs"][1]["run"],
                           "RUN_END": "SUPPORT_FACE (each side's in-panel items stop at its own face)",
                           "BLOCKED": [b_["part"] for b_ in spec["blocked"]], "CROSSING_ITEM": "NONE",
                           "CHOSEN_BY": "NOTHING (no majority, size, rate or nearest value)", "AUTHORITY": "AD2-D10"})
    split_keys = {(r["SUPPORT_ID"], r["LEFT_PANEL"], r["RIGHT_PANEL"], r["BAR_DIRECTION"]) for r in split_rows}

    # one blocked lap / splice item per multi-panel run
    run_parent = {}
    for f in bfam.values():
        if f["state"] == "RESOLVED" and f["run"] and "cont" in f["parents"]:
            run_parent.setdefault(f["run"], sorted([f["parents"]["cont"]]))
            run_parent[f["run"]] = sorted(set(run_parent[f["run"]] + [f["parents"]["cont"]]))
    for r in runs:
        if r["KIND"] != "BOTTOM_BALANCE_CONTINUOUS" or r["BAR_RUN_ID"] not in run_parent:
            continue
        add(PARENT_COMPONENT_ID=run_parent[r["BAR_RUN_ID"]][0], ITEM="BOTTOM_RUN_LAP_SPLICE", OWNER=r["BAR_RUN_ID"],
            FLOOR=None, DIRECTION=r["DIRECTION"], DIA_MM=int(r["DIAMETER_MM"]), RUN_ID=r["BAR_RUN_ID"],
            COUNT_BASIS=Q.COUNT_RATE_DENSITY, EXTENT_BASES=[Q.EXTENT_BLOCKED], LANE=Q.BLOCKED_UNQUANTIFIED,
            BLOCKERS=["MAIN_BAR_LAP_NOT_LOCATED"], QUESTIONS=["Q-LAP"], AUTHORITY=["AD2-D10"])

    # ---------------------------------------------------- top over supports (§5, §6, §11)
    top_rows = []
    note2 = rules["P4-6-NOTE-2-TOP-OVER-BEAMS"]
    p15n, p15c, p15e = (rules["P15-TOP-NONCONT-0.25L1"], rules["P15-TOP-CONT-0.30Lmax"],
                        rules["P15-TOP-EXTEND-50PCT"])
    N2 = {"rule_id": note2["RULE_ID"], "layer": "TOP", "location": "OVER_SUPPORT", "role": "TOP_OVER_SUPPORT",
          "support": "BEAM", "dia_mm": NOTE2_DIA, "rate": NOTE2_RATE, "scope": Q.FLOOR_PLAN_NOTE}
    ident = []
    for rr, role in ((p15n, "TOP_OVER_SUPPORT"), (p15c, "TOP_OVER_SUPPORT"), (p15e, "TOP_OVER_SUPPORT")):
        G = {"rule_id": rr["RULE_ID"], "layer": "TOP", "location": "OVER_SUPPORT", "role": role, "support": "BEAM",
             "dia_mm": None, "rate": None, "size_deferred_to": Q.FLOOR_PLAN_NOTE, "scope": Q.GENERIC_TYPICAL_DETAIL}
        idn = Q.bar_role_identity(G, N2)
        prec = Q.same_role_precedence([{"rule_id": G["rule_id"], "scope": G["scope"]},
                                       {"rule_id": N2["rule_id"], "scope": N2["scope"]}])
        check(idn["identity"] == Q.SAME_FAMILY and prec["governing"] == N2["rule_id"], f"identity {rr['RULE_ID']}")
        ident.append({"RULE_A": rr["RULE_ID"], "RULE_B": note2["RULE_ID"], "LOCATION": "every beam support",
                      "IDENTITY": idn["identity"],
                      "EVIDENCE": idn["evidence"] + [
                          f"wording A: {rr['WORDING']}", "wording B: plan note 2 (decoded Arabic) - top steel 5Ø10/m "
                          "for the slabs over the beams, length one third of the span, both directions",
                          "leader target A: dimensions to the top bars at the support in the p.15 section; B: a general "
                          "note on each slab plan (no leader)",
                          "graphic layer A: p.15 detail; B: plan note box (S-TITLE TEXT) with the 5%%C10/M text",
                          "detail title A: TYP. SLAB ON BEAMS DETAIL (generic); B: slab plan sheets pp.4-6 (floor "
                          "specific)", "size / spacing: A says 'SEE SCHEDULE OR PLAN'; B supplies 5Ø10/m"],
                      "CONTRADICTIONS": idn["contradictions"], "GOVERNING": prec["governing"],
                      "OVERRIDDEN": prec["overridden"], "OVERRIDDEN_STATE": Q.OVERRIDDEN_PROJECT_SOURCE,
                      "SUMMED": False, "AUTHORITY": "AD2-D05"})
    ident.append({"RULE_A": note2["RULE_ID"], "RULE_B": None, "LOCATION": "every beam support",
                  "IDENTITY": "MEASUREMENT_ORIGIN", "EVIDENCE": [
                      "'length one third of the span' does not state total length vs extension each side, nor the "
                      "origin; AD2-D06 applies the extension reading from the support face",
                      f"rule {Q.URBAN_TOP_EXTENT_RULE}: 1/3 x local clear span from the support face"],
                  "CONTRADICTIONS": [], "GOVERNING": Q.URBAN_TOP_EXTENT_RULE, "OVERRIDDEN": [],
                  "OVERRIDDEN_STATE": None, "SUMMED": False,
                  "AUTHORITY": f"AD2-D06 ({Q.URBAN_OWNER_MEASUREMENT_RULE}, not {Q.PROJECT_SOURCE_EXPLICIT})"})
    explicit = {}
    for t in tokens:
        if t["KIND"] != "SUPPORT_TOP_BAR":
            continue
        if t["TERMINAL_STATE"] == SR.BOUND_TO_SUPPORT:
            ec = Q.explicit_count(t["RAW"], bound_object="SUPPORT_BAR_GRAPHIC")
            ov = Q.local_override(same_role=True, same_location=True)
            explicit[t["BOUND_TO"]] = {"token": t, "count": ec, "override": ov}
            ident.append({"RULE_A": f"token {t['TOKEN_ID']} ({t['RAW']})", "RULE_B": note2["RULE_ID"],
                          "LOCATION": t["BOUND_TO"], "IDENTITY": Q.SAME_FAMILY,
                          "EVIDENCE": ["the drawn '/Top' bar crosses the support between its two panels (PRE-S7 "
                                       "BOUND_TO_SUPPORT)", "same layer (TOP), same role (top over support), same "
                                       "location", "no source shows a second top family there"],
                          "CONTRADICTIONS": [f"specification: {ec['count']}Ø{ec['dia_mm']} vs 5Ø10/m"],
                          "GOVERNING": f"token {t['TOKEN_ID']} ({ov['local']})", "OVERRIDDEN": [note2["RULE_ID"]],
                          "OVERRIDDEN_STATE": ov["general"], "SUMMED": False, "AUTHORITY": "AD2-D11"})
        else:
            ident.append({"RULE_A": f"token {t['TOKEN_ID']} ({t['RAW']})", "RULE_B": note2["RULE_ID"],
                          "LOCATION": "beside a beam line, outside every slab panel", "IDENTITY": Q.IDENTITY_UNRESOLVED,
                          "EVIDENCE": ["drawn parallel to the beam, outside the panels (PRE-S7 C-09)"],
                          "CONTRADICTIONS": ["location: beside the support, not over it"], "GOVERNING": None,
                          "OVERRIDDEN": [], "OVERRIDDEN_STATE": None, "SUMMED": False,
                          "AUTHORITY": "AD2-D05 (unresolved identity: this family stays blocked, nothing else)"})
    check(len(explicit) == 1, "one bound '/Top' callout")

    hatch_sids = {sid for sid, a_ in ad2_sup.items() if a_["bearing_wall_band"]}
    ext_acc = defaultdict(lambda: {"width": 0.0, "integral": 0.0, "strips": 0})
    over_acc = defaultdict(lambda: {"width": 0.0, "integral": 0.0, "gap_unknown": 0.0})
    s8_side = {}
    mapped = defaultdict(int)
    top_hi = defaultdict(lambda: defaultdict(float))
    unrecorded = defaultdict(float)
    for (pid, d), st in sorted(strips.items()):
        for x in st:
            for end in ("start_edge_ref", "end_edge_ref"):
                ref = x[end]
                sid = ref.get("support")
                if ref["kind"] == "NO_SUPPORT_RECORD" and x[end[:-4]][0] == 0:
                    unrecorded[(pid, d)] += x["width"]
                    continue
                if ref["kind"] != "SUPPORT" or not ref["square"] or sup[sid]["BARS_CROSSING"] != d or \
                        ref.get("support_kind") != "BEAM" or sup[sid]["SUPPORT_KIND"] != "BEAM":
                    continue
                mapped[sid] += 1
                e = ext_acc[(sid, pid)]
                e["width"] += x["width"]
                e["integral"] += x["integral"] / 3.0
                e["strips"] += 1
                nb = ref.get("neighbour")
                oc = side_class(nb)
                if oc in ("SLAB_TRANSFERRED", "SLAB_EXCLUDED_SPECIAL"):
                    s8_side[(sid, nb)] = True
                step = oc == "SLAB_IN_SCOPE" and ((pid in sunken) != (nb in sunken))
                cont = Q.edge_continuity(other_side=oc, support_kind="BEAM", level_step=step)
                if cont["state"] == SR.CONTINUOUS:
                    if pid > nb:                                  # counted from the other face
                        top_hi[(nb, pid, d)][sid] += x["width"]
                        continue
                    o = over_acc[(sid, "CROSSING", f"{pid}|{nb}")]
                    if ref.get("gap"):
                        o["width"] += x["width"]
                        o["integral"] += 0.5 * (ref["gap"][0] + ref["gap"][1]) * x["width"]
                    else:
                        o["gap_unknown"] += x["width"]
                elif cont["state"] == SR.NON_CONTINUOUS:
                    over_acc[(sid, "ANCHORAGE", pid)]["width"] += x["width"]
                else:
                    why = "LEVEL_CHANGE" if step else oc
                    over_acc[(sid, "UNRESOLVED:" + why, pid)]["width"] += x["width"]
    top_lo = defaultdict(float)
    for (sid_, kind, who), o in over_acc.items():
        if kind == "CROSSING":
            pa, pb = who.split("|")
            top_lo[(pa, pb, sup[sid_]["BARS_CROSSING"])] += o["width"] + o["gap_unknown"]
    top_excess = defaultdict(list)
    for (pa, pb, d), by_sid in sorted(top_hi.items()):
        excess = sum(by_sid.values()) - top_lo.get((pa, pb, d), 0.0)
        if excess > 1.0:
            top_excess[max(sorted(by_sid), key=lambda k: by_sid[k])].append((pa, pb, excess))
    for c in comps:
        if not c["COMPONENT"].startswith("TOP_SUPPORT"):
            continue
        sid, d = c["OWNER"], c["DIRECTION"]
        s = sup[sid]
        base = dict(PARENT_COMPONENT_ID=c["COMPONENT_ID"], OWNER=sid, FLOOR=s["FLOOR"], DIRECTION=d, SUPPORT_ID=sid)
        for pa, pb, excess in top_excess.get(sid, []):
            add(**base, ITEM="TOP_SUPPORT_CROSSING", DIA_MM=NOTE2_DIA, SIDE_PANEL=f"{pb}>{pa}",
                COUNT_BASIS=Q.COUNT_RATE_DENSITY, RATE_PER_M=NOTE2_RATE, DISTRIBUTION_WIDTH_MM=_r(excess, 1),
                EXTENT_BASES=[Q.EXTENT_BLOCKED], LANE=Q.BLOCKED_UNQUANTIFIED,
                BLOCKERS=["CROSSING_SEEN_FROM_ONE_FACE_ONLY (a junction / set-back beyond one face)"],
                QUESTIONS=["Q-CONT"], AUTHORITY=["AD2-D14"])
        if sid in explicit:
            e = explicit[sid]
            add(**base, ITEM="TOP_LOCAL_OVERRIDE_GROUP", DIA_MM=e["count"]["dia_mm"],
                COUNT_BASIS=Q.COUNT_SOURCE_EXPLICIT, EXPLICIT_COUNT=e["count"]["count"], COUNT_RELEASED=True,
                EXTENT_BASES=[Q.EXTENT_BLOCKED], LANE=Q.lane(Q.COUNT_SOURCE_EXPLICIT, [Q.EXTENT_BLOCKED]),
                BLOCKERS=["OVERRIDE_BAR_LENGTH_NOT_ESTABLISHED (graphic shape only, no extent in the source)"],
                QUESTIONS=["Q-TOPOVR"], AUTHORITY=["AD2-D03", "AD2-D11"],
                NOTE=f"{e['override']['local']}: replaces plan note 2 (5Ø10/m) at {sid} "
                     f"({e['override']['general']}); count {e['count']['count']} released, length blocked")
            top_rows.append({"SUPPORT_ID": sid, "ROLE": "TOP_OVER_SUPPORT", "STATE": e["override"]["general"],
                             "RULE": note2["RULE_ID"]})
            continue
        n_items = 0
        for (sid_, pid), e in sorted(ext_acc.items()):
            if sid_ != sid:
                continue
            n_items += 1
            if sid in hatch_sids:
                add(**base, ITEM="TOP_EXTENSION", DIA_MM=NOTE2_DIA, SIDE_PANEL=pid, COUNT_BASIS=Q.COUNT_RATE_DENSITY,
                    RATE_PER_M=NOTE2_RATE, DENSITY_FRACTION=1.0, DISTRIBUTION_WIDTH_MM=_r(e["width"], 1),
                    EXTENT_BASES=[Q.EXTENT_BLOCKED], LANE=Q.BLOCKED_UNQUANTIFIED,
                    BLOCKERS=["TOP_RULE_APPLICABILITY_AT_BEARING_WALL_CANDIDATE (plan note 2 is for slabs over beams; "
                              "the support band carries the dense hatch)"], QUESTIONS=["Q-HATCH"],
                    AUTHORITY=["AD2-D13"], NOTE=json.dumps(ad2_sup[sid]["bearing_wall_band"]))
                continue
            ext = [Q.EXTENT_URBAN_RULE]
            add(**base, ITEM="TOP_EXTENSION", DIA_MM=NOTE2_DIA, SIDE_PANEL=pid,
                **rate_fields(NOTE2_RATE, 1.0, e["width"]), RUN_INTEGRAL_M2=_r(e["integral"] / 1e6, 6),
                MEAN_RUN_MM=_r(e["integral"] / e["width"], 1),
                RUN_RULE=f"{Q.URBAN_TOP_EXTENT_RULE}: 1/3 x local clear span from the support face into {pid}",
                EXTENT_BASES=ext, LANE=Q.lane(Q.COUNT_RATE_DENSITY, ext),
                AUTHORITY=["AD2-D02", "AD2-D05", "AD2-D06"] + ([] if rect[pid] else ["AD2-D14"]),
                LAYER_AUTHORITY="PROJECT_SOURCE (plan note 2: top steel)", STRIPS=e["strips"])
        for (sid_, nb), _ in sorted(s8_side.items()):
            if sid_ != sid:
                continue
            n_items += 1
            reg = region.get(nb) or ("SPECIAL_STRUCTURE (" + cs[nb]["PANEL_CLASS"] + ", excluded in PRE-S7)")
            add(**base, ITEM="TOP_EXTENSION", DIA_MM=NOTE2_DIA, SIDE_PANEL=nb, LANE=Q.TRANSFERRED_S8, S8_REGION=reg,
                AUTHORITY=["AD2-D08"] if nb in tank else ["AD2-D09"] if nb in lightwell else
                ["PRE-S7 scope (special structure)"])
        if not any(k[0] == sid for k in ext_acc):          # no S7 face on this support: its S7-less sides only
            for pid in [q for q in ad2_sup[sid]["sides"] if q and q in region and not (sid, q) in s8_side]:
                n_items += 1
                add(**base, ITEM="TOP_EXTENSION", DIA_MM=NOTE2_DIA, SIDE_PANEL=pid, LANE=Q.TRANSFERRED_S8,
                    S8_REGION=region[pid], AUTHORITY=["AD2-D08"] if pid in tank else ["AD2-D09"])
        for (sid_, kind, who), o in sorted(over_acc.items()):
            if sid_ != sid:
                continue
            n_items += 1
            if kind == "CROSSING" and sid not in hatch_sids:
                if o["width"] > 1.0:
                    ext = [Q.EXTENT_PROJECT_GEOMETRY]
                    add(**base, ITEM="TOP_SUPPORT_CROSSING", DIA_MM=NOTE2_DIA, SIDE_PANEL=who,
                        **rate_fields(NOTE2_RATE, 1.0, o["width"]), RUN_INTEGRAL_M2=_r(o["integral"] / 1e6, 6),
                        MEAN_RUN_MM=_r(o["integral"] / o["width"], 1),
                        RUN_RULE="over the beam between the two panel faces along each bar line (counted once)",
                        EXTENT_BASES=ext, LANE=Q.lane(Q.COUNT_RATE_DENSITY, ext),
                        AUTHORITY=["AD2-D02", "AD2-D05", "AD2-D15"],
                        LAYER_AUTHORITY="PROJECT_SOURCE (plan note 2: top steel)")
                if o["gap_unknown"] > 1.0:
                    add(**base, ITEM="TOP_SUPPORT_CROSSING", DIA_MM=NOTE2_DIA, SIDE_PANEL=who,
                        COUNT_BASIS=Q.COUNT_RATE_DENSITY, RATE_PER_M=NOTE2_RATE,
                        DISTRIBUTION_WIDTH_MM=_r(o["gap_unknown"], 1), EXTENT_BASES=[Q.EXTENT_BLOCKED],
                        LANE=Q.BLOCKED_UNQUANTIFIED, BLOCKERS=["CROSSING_GEOMETRY_NOT_RESOLVED (the far face does not "
                                                               "span the strip)"], QUESTIONS=["Q-CONT"],
                        AUTHORITY=["AD2-D14"])
            elif kind == "ANCHORAGE":
                add(**base, ITEM="TOP_END_ANCHORAGE", DIA_MM=NOTE2_DIA, SIDE_PANEL=who,
                    COUNT_BASIS=Q.COUNT_RATE_DENSITY, RATE_PER_M=NOTE2_RATE, DISTRIBUTION_WIDTH_MM=_r(o["width"], 1),
                    EXTENT_BASES=[Q.EXTENT_BLOCKED], LANE=Q.BLOCKED_UNQUANTIFIED,
                    BLOCKERS=["TOP_ANCHOR_OVER_BEAM_AND_LEG_SHAPE_ONLY ('40 CL.' unresolved)"],
                    QUESTIONS=["Q-ANCHOR", "Q-ENDCOVER"], AUTHORITY=["AD2-D16"])
            else:
                why = kind.split(":", 1)[1] if ":" in kind else "HATCH_BAND"
                q = "Q-SUNKEN" if why == "LEVEL_CHANGE" else "Q-HATCH" if sid in hatch_sids else \
                    "Q-CONT"
                add(**base, ITEM="TOP_OVER_SUPPORT_UNRESOLVED", DIA_MM=NOTE2_DIA, SIDE_PANEL=who,
                    COUNT_BASIS=Q.COUNT_RATE_DENSITY, RATE_PER_M=NOTE2_RATE, DISTRIBUTION_WIDTH_MM=_r(o["width"], 1),
                    EXTENT_BASES=[Q.EXTENT_BLOCKED], LANE=Q.BLOCKED_UNQUANTIFIED,
                    BLOCKERS=[f"PORTION_OVER_SUPPORT_DEPENDS_ON_CONTINUITY ({why})"], QUESTIONS=[q],
                    AUTHORITY=["AD2-D15"])
        if not n_items:
            moved = any(view_sup.get((x["panel"], x[e_][1])) == sid and x[e_ + "_ref"].get("support") not in
                        (sid, None) for st in strips.values() for x in st for e_ in ("start_edge", "end_edge")
                        if x[e_][0] == 0)
            add(**base, ITEM="TOP_EXTENSION", DIA_MM=NOTE2_DIA, COUNT_BASIS=Q.COUNT_RATE_DENSITY, RATE_PER_M=NOTE2_RATE,
                EXTENT_BASES=[Q.EXTENT_BLOCKED], LANE=Q.BLOCKED_UNQUANTIFIED,
                BLOCKERS=["NO_SQUARE_BAR_LINE_MEETS_THIS_SUPPORT" + (" (its bar lines were mapped by geometry to "
                                                                      "another support record)" if moved else "")],
                QUESTIONS=["Q-OBLIQUE"], AUTHORITY=["AD2-D14"])

    # ---------------------------------------------------- temperature, corner, tank top mesh (§7, §3, §8)
    for c in comps:
        cid, kind, owner = c["COMPONENT_ID"], c["COMPONENT"], c["OWNER"]
        if kind.startswith("TEMPERATURE"):
            if owner in region:
                add(PARENT_COMPONENT_ID=cid, ITEM="TEMPERATURE", OWNER=owner, FLOOR=c["FLOOR"], DIRECTION=c["DIRECTION"],
                    LANE=Q.TRANSFERRED_S8, S8_REGION=region[owner], AUTHORITY=["AD2-D08"])
            else:
                th = _f(cs[owner]["THICKNESS_MM"])
                ti = Q.temperature_item(int(th) if th == int(th) else th, temp_table)
                check(ti["lane"] == Q.BLOCKED_UNQUANTIFIED, f"temperature stays blocked ({owner} {th})")
                add(PARENT_COMPONENT_ID=cid, ITEM="TEMPERATURE", OWNER=owner, FLOOR=c["FLOOR"],
                    DIRECTION=c["DIRECTION"], EXTENT_BASES=[Q.EXTENT_BLOCKED], COUNT_BASIS=Q.COUNT_UNRESOLVED,
                    LANE=Q.BLOCKED_UNQUANTIFIED, BLOCKERS=[f"TABLE_NO_EXACT_ROW ({th:g} mm; no interpolation)"],
                    QUESTIONS=["Q-TEMP"], AUTHORITY=["AD2-D07"])
        elif kind == "CORNER_BAR":
            ec = Q.explicit_count(tok[c["TOKEN"]]["RAW"], bound_object="CORNER_BAR_GROUP")
            add(PARENT_COMPONENT_ID=cid, ITEM="CORNER_GROUP", OWNER=owner, FLOOR=c["FLOOR"], DIRECTION=c["DIRECTION"],
                DIA_MM=ec["dia_mm"], COUNT_BASIS=ec["count_basis"], EXPLICIT_COUNT=ec["count"], COUNT_RELEASED=True,
                EXTENT_BASES=[Q.EXTENT_BLOCKED], LANE=Q.lane(ec["count_basis"], [Q.EXTENT_BLOCKED]),
                BLOCKERS=["CORNER_BAR_LENGTH_NOT_DIMENSIONED", "CORNER_BAR_LAYER_NOT_STATED"],
                QUESTIONS=["Q-CORNER"], AUTHORITY=["AD2-D03"],
                NOTE="bound to the S-REIN-CORNER bar group: the count releases, the length does not")

    # ---------------------------------------------------- §12 sunken extras (new components)
    new_comps = []
    for p in sunken:
        for x in Q.SUNKEN_EXTRAS:
            cid = f"AD2-{x}-{p[3:]}"
            new_comps.append({"COMPONENT_ID": cid, "COMPONENT": x, "OWNER": p, "FLOOR": cs[p]["FLOOR"],
                              "DIRECTION": None})
            add(PARENT_COMPONENT_ID=cid, ITEM=x, OWNER=p, FLOOR=cs[p]["FLOOR"], EXTENT_BASES=[Q.EXTENT_BLOCKED],
                COUNT_BASIS=Q.COUNT_UNRESOLVED, LANE=Q.BLOCKED_UNQUANTIFIED,
                BLOCKERS=["NOT_SPECIFIED (sunken step detail / drop depth not located)"], QUESTIONS=["Q-SUNKEN"],
                AUTHORITY=["AD2-D12"])
    for (p, d), w in sorted(unrecorded.items()):
        cid = f"AD2-TOP_AT_UNRECORDED_EDGE-{p[3:]}-{d}"
        new_comps.append({"COMPONENT_ID": cid, "COMPONENT": "TOP_AT_UNRECORDED_EDGE", "OWNER": p,
                          "FLOOR": cs[p]["FLOOR"], "DIRECTION": d})
        add(PARENT_COMPONENT_ID=cid, ITEM="TOP_AT_UNRECORDED_EDGE", OWNER=p, FLOOR=cs[p]["FLOOR"], DIRECTION=d,
            DISTRIBUTION_WIDTH_MM=_r(w, 1), EXTENT_BASES=[Q.EXTENT_BLOCKED], COUNT_BASIS=Q.COUNT_UNRESOLVED,
            LANE=Q.BLOCKED_UNQUANTIFIED, BLOCKERS=["NO_SUPPORT_RECORD (a short / curved boundary edge with no S1 "
                                                   "support: whether a beam carries top bars there is not known)"],
            QUESTIONS=["Q-EDGE"], AUTHORITY=["AD2-D15"])
    sunken_dec = {p: Q.sunken_decision(boundary=True, callout=bool(bfam.get((p, "X")) or bfam.get((p, "Y"))),
                                       thickness=bool(cs[p]["THICKNESS_MM"]), supports=True) for p in sunken}

    # ---------------------------------------------------- per-component terminal state (§19)
    by_parent = defaultdict(list)
    for it in items:
        by_parent[it["PARENT_COMPONENT_ID"]].append(it)
    decided = {"COUNT_BASIS_UNRESOLVED": "AD2-D02", "EDGE_BAR_UNRESOLVED": "AD2-D02 (BBS only)",
               "WHICH_50_PERCENT_UNRESOLVED": "AD2-D04", "TOP_EXTENT_SOURCE_CONFLICT": "AD2-D05 + AD2-D06",
               "TOP_OVERRIDE_RULE_UNRESOLVED": "AD2-D11", "CONTINUOUS_BAR_SPEC_MISMATCH": "AD2-D10",
               "SPAN_NOT_SINGLE_VALUED": "AD2-D14", "RUN_ALIGNMENT_PARTIAL": "AD2-D14",
               "SUPPORT_CONTINUITY_UNRESOLVED": "AD2-D15 (isolated to end / over-support portions)",
               "SUPPORT_NOT_A_BEAM": "AD2-D15 (isolated to the strips that end there)",
               "TEMPERATURE_REGION_DEPENDS_ON_TOP_EXTENT": "AD2-D06 (the table row is still missing)",
               "CLASSIFICATION_BLOCKED": "AD2-D08 / AD2-D09 (transferred)"}
    readiness = []
    for c in comps + new_comps:
        cid = c["COMPONENT_ID"]
        its = by_parent.get(cid, [])
        check(its, f"{cid} has items")
        lanes = [i["LANE"] for i in its]
        state = Q.component_state([{"lane": x} for x in lanes])
        pre_blk = _js(c.get("BLOCKERS")) or []
        rem = sorted({b for i in its if i["LANE"] == Q.BLOCKED_UNQUANTIFIED for b in i.get("BLOCKERS") or []})
        readiness.append({
            "COMPONENT_ID": cid, "COMPONENT": c["COMPONENT"], "OWNER": c["OWNER"], "FLOOR": c.get("FLOOR"),
            "DIRECTION": c.get("DIRECTION"), "NEW_IN_AD2": cid.startswith("AD2-"),
            "PRE_S7_READINESS": c.get("READINESS"), "PRE_S7_DECISION_ONLY": c.get("DECISION_ONLY"),
            "PRE_S7_BLOCKERS": pre_blk,
            "PRE_S7_BLOCKERS_DECIDED": {b: decided[b] for b in pre_blk if b in decided},
            "AD2_STATE": state,
            "RELEASED_LANES": sorted({x for x in lanes if x in Q.RELEASED_LANES}),
            "ITEMS": len(its), "RELEASED_ITEMS": sum(x in Q.RELEASED_LANES for x in lanes),
            "BLOCKED_ITEMS": sum(x == Q.BLOCKED_UNQUANTIFIED for x in lanes),
            "TRANSFERRED_ITEMS": sum(x == Q.TRANSFERRED_S8 for x in lanes),
            "COUNT_RELEASED": any(i.get("COUNT_RELEASED") for i in its),
            "REMAINING_BLOCKERS": rem, "QUESTIONS": sorted({q for i in its for q in i.get("QUESTIONS") or []}),
            "KG": None})

    # ---------------------------------------------------- 02 ownership transfers
    transfers = []
    for p in tank + lightwell:
        t = Q.ownership_transfer(p, kind="PANEL", to_stage=S8, region=region[p],
                                 reason=cs[p]["SCOPE_REASON"], conflict_preserved=p in lightwell)
        transfers.append(t)
    for t in tokens:
        b = t["BOUND_TO"]
        if b in region:
            transfers.append(Q.ownership_transfer(f"token {t['TOKEN_ID']} ({t['RAW']})", kind="TOKEN", to_stage=S8,
                                                  region=region[b], reason=f"bound to {b}",
                                                  conflict_preserved=b in lightwell))
    gf_tokens = [x for x in _js(cs[lightwell[0]]["TOKENS"]) or []]
    for h in gf_tokens:
        if not any(tr["object_id"].startswith(f"token {h} ") for tr in transfers):
            transfers.append(Q.ownership_transfer(f"token {h} ({tok[h]['RAW'] if h in tok else 'S1 slab token'})",
                                                  kind="TOKEN", to_stage=S8, region=LIGHTWELL_REGION,
                                                  reason=f"bound to {lightwell[0]} (PRE-S7: SOURCE_CONFLICT)",
                                                  conflict_preserved=True))
    for m in _js(cs[lightwell[0]]["THICKNESS_MARKS"]) or []:
        transfers.append(Q.ownership_transfer(f"thickness mark T {m['value_mm'] / 10:g} ({m['handle']})",
                                              kind="THICKNESS_MARK", to_stage=S8, region=LIGHTWELL_REGION,
                                              reason=f"inside {lightwell[0]}", conflict_preserved=True))
    for p in tank:
        for m in _js(cs[p]["THICKNESS_MARKS"]) or []:
            transfers.append(Q.ownership_transfer(f"thickness mark T {m['value_mm'] / 10:g} ({m['handle']})",
                                                  kind="THICKNESS_MARK", to_stage=S8, region=TANK_REGION,
                                                  reason=f"inside {p} (180 mm: its temperature-table gap leaves S7)"))
    for r in readiness:
        if r["AD2_STATE"] == Q.TRANSFERRED_S8:
            regs = sorted({i.get("S8_REGION") for i in by_parent[r["COMPONENT_ID"]]})
            transfers.append(Q.ownership_transfer(r["COMPONENT_ID"], kind="COMPONENT " + r["COMPONENT"],
                                                  to_stage=S8, region="; ".join(regs), reason=f"owner {r['OWNER']}"))
    for it in items:
        if it["LANE"] == Q.TRANSFERRED_S8 and readiness_state(readiness, it["PARENT_COMPONENT_ID"]) != \
                Q.TRANSFERRED_S8:
            transfers.append(Q.ownership_transfer(it["QTO_ITEM_ID"], kind="ITEM " + it["ITEM"], to_stage=S8,
                                                  region=it["S8_REGION"],
                                                  reason=f"the {it.get('SIDE_PANEL')} side of {it['OWNER']}"))
    for k, t in enumerate(transfers):
        t["TRANSFER_ID"] = f"TR-{k + 1:03d}"

    # ---------------------------------------------------- 03 rate register, candidates, blockers
    rate_rows = [i for i in items if i.get("COUNT_BASIS") == Q.COUNT_RATE_DENSITY]
    cands = [i for i in items if i["LANE"] in Q.RELEASED_LANES]
    blockers = [i for i in items if i["LANE"] == Q.BLOCKED_UNQUANTIFIED]

    # ---------------------------------------------------- 09 remaining conflicts
    hatch_final = Counter(h["state"] for h in hatch_rows)
    conf = []
    res = {
        "PANEL_VOID_CONFLICT": ("SOURCE_CONFLICT_PRESERVED (TRANSFERRED_S8: STAIR_LIGHTWELL_REGION)", "AD2-D09", True),
        "UNSUPPORTED_SUPPORT_RULE_APPLICABILITY": ("RESOLVED_BY_IDENTITY_AND_PRECEDENCE (same family; plan note 2 "
                                                   "governs; p.15 extents OVERRIDDEN_PROJECT_SOURCE)",
                                                   "AD2-D05 + AD2-D06", False),
        "MULTIPLE_CANDIDATE_BINDINGS": ("SOURCE_CONFLICT (unchanged: two callouts, one direction)", None, True),
        "COUNT_NOTATION_CONFLICT": ("SOURCE_CONFLICT (unchanged: bound to a panel, not to a finite bar group)",
                                    "AD2-D03", True),
        "THICKNESS_PRIOR_REGISTER_CONFLICT": ("RESOLVED_BY_SOURCE (unchanged)", None, False),
        "COVER_DIMENSION_BINDING": ("UNRESOLVED (no quantity depends on '40 CL.')", "AD2-D16", True),
        "TOP_BAR_BINDING": ("SOURCE_CONFLICT (unchanged: identity with plan note 2 unresolved)", "AD2-D05", True),
        "ASYMMETRIC_SUPPORT_VIEW": ("RESOLVED_BY_GEOMETRY (each bar line finds the face beyond its own end; the "
                                    "PRE-S7 support stays the owner)", "AD2-D14 + AD2-D15", False),
        "CONTINUOUS_BAR_SPEC_MISMATCH": ("RESOLVED_BY_SPLIT (left / right runs to the support face; transition "
                                         "blocked)", "AD2-D10", False)}
    for c in conflicts_pre:
        kind = c["KIND"]
        where = _js(c["WHERE"]) if c["WHERE"].startswith("[") else c["WHERE"]
        if kind == "CLASSIFICATION":
            if isinstance(where, list) and where and where[0].startswith("HZ-"):
                st = (f"RECLASSIFIED_BY_GEOMETRY ({', '.join(f'{k} {v}' for k, v in sorted(hatch_final.items()))})")
                conf.append({"PRE_S7_CONFLICT_ID": c["CONFLICT_ID"], "KIND": kind, "WHERE": where,
                             "AD2_STATE": st, "DECISION": "AD2-D13",
                             "TRUE_SOURCE_CONFLICT": hatch_final.get(SR.CLASSIFICATION_BLOCKED, 0) > 0,
                             "NOTE": "the legend's two meanings stay a legend ambiguity; geometry places each strip"})
            else:
                conf.append({"PRE_S7_CONFLICT_ID": c["CONFLICT_ID"], "KIND": kind, "WHERE": where,
                             "AD2_STATE": "TRANSFERRED_S8 (WATER_TANK_SUPPORT_REGION)", "DECISION": "AD2-D08",
                             "TRUE_SOURCE_CONFLICT": False, "NOTE": "ownership, not a conflict of values"})
            continue
        st, dec, true = res[kind]
        conf.append({"PRE_S7_CONFLICT_ID": c["CONFLICT_ID"], "KIND": kind, "WHERE": where, "AD2_STATE": st,
                     "DECISION": dec, "TRUE_SOURCE_CONFLICT": true, "NOTE": None})

    # topology corrections found by geometry (the PRE-S7 support type vs what lies beyond each strip end)
    phys = defaultdict(lambda: defaultdict(float))
    beyond = defaultdict(set)
    to_state = {Q.END_NON_CONTINUOUS: SR.NON_CONTINUOUS, Q.END_CONTINUOUS_RUN: SR.CONTINUOUS,
                Q.END_CONTINUOUS_SPLIT: SR.CONTINUOUS, Q.END_UNRESOLVED: SR.CONTINUITY_UNRESOLVED}
    for (pid, d), st in strips.items():
        for x in st:
            for k, e in enumerate(("start_edge_ref", "end_edge_ref")):
                ref, ec = x[e], x["end_classes"][k]
                if ec in to_state and ref.get("support") and ref["source"].startswith("GEOMETRY"):
                    phys[ref["support"]][to_state[ec]] += x["width"]
                    beyond[ref["support"]].add(ref.get("neighbour"))
    topo = []
    for sid, by in sorted(phys.items()):
        pre = sup[sid]["SUPPORT_TYPE"]
        other = {k: round(v, 1) for k, v in sorted(by.items()) if k != pre and v > 1.0}
        if other:
            topo.append({"PRE_S7_CONFLICT_ID": f"G-{len(topo) + 1:02d}", "KIND": "TOPOLOGY_CORRECTION_BY_GEOMETRY",
                         "WHERE": sid, "AD2_STATE": f"PRE-S7 {pre}; geometry beyond the faces: "
                                                   + ", ".join(f"{k} over {v:g} mm" for k, v in other.items()),
                         "DECISION": "AD2-D15 (physical continuity from the face found beyond each bar line)",
                         "TRUE_SOURCE_CONFLICT": False,
                         "NOTE": "S1 edge neighbour vs face found beyond: " + ", ".join(sorted(str(b) for b in
                                                                                             beyond[sid]))})
    conf += topo

    # ---------------------------------------------------- gates (§19)
    pre_ids = [c["COMPONENT_ID"] for c in comps]
    term = {r["COMPONENT_ID"]: r["AD2_STATE"] for r in readiness}
    tcons = Q.transfer_conservation(pre_ids + [c["COMPONENT_ID"] for c in new_comps], term)
    density_ok = True
    for (pid, d), st in strips.items():
        f = bfam.get((pid, d))
        if not f or f["state"] != "RESOLVED":
            continue
        for x in st:
            density_ok &= Q.item_density_check(Q.bottom_strip_items(x["L0"], x["L1"], x["width"], *x["end_classes"]))
    cross_once = Counter((i["SUPPORT_ID"], i["ITEM"], i.get("SIDE_PANEL"), i["DIRECTION"], i["LANE"]) for i in items
                         if i["ITEM"].endswith("SUPPORT_CROSSING"))
    pairs = {(i["SUPPORT_ID"], i["ITEM"], i["DIRECTION"], tuple(i["SIDE_PANEL"].split("|"))) for i in items
             if i["ITEM"].endswith("SUPPORT_CROSSING") and "|" in str(i.get("SIDE_PANEL"))}
    density_ok &= not any((sd, it, d, (b_, a_)) in pairs for sd, it, d, (a_, b_) in pairs)
    s8_leak = [i["QTO_ITEM_ID"] for i in cands if i["OWNER"] in region or i.get("SIDE_PANEL") in region or
               i.get("S8_REGION")]
    note2_at_override = [i for i in items if i.get("SUPPORT_ID") in explicit and i["ITEM"] in
                         ("TOP_EXTENSION", "TOP_SUPPORT_CROSSING", "TOP_END_ANCHORAGE", "TOP_OVER_SUPPORT_UNRESOLVED")]
    temp_sep = all(len(by_parent[c["COMPONENT_ID"]]) == 1 and by_parent[c["COMPONENT_ID"]][0]["ITEM"] == "TEMPERATURE"
                   for c in comps if c["COMPONENT"].startswith("TEMPERATURE"))
    split_cross = [i for i in items if i["ITEM"] == "BOTTOM_SUPPORT_CROSSING" and
                   (i["SUPPORT_ID"], *i["SIDE_PANEL"].split("|"), i["DIRECTION"]) in split_keys]
    gates = {
        "every_pre_s7_component_terminates_once": tcons["every_object_once"] and tcons["no_unknown"],
        "ownership_transfer_loses_no_component": all(t["quantity_lost"] is False for t in transfers) and all(
            any(t["object_id"] == c for t in transfers) for c in pre_ids if term[c] == Q.TRANSFERRED_S8) and all(
            any(t["object_id"] == i["QTO_ITEM_ID"] for t in transfers) for i in items
            if i["LANE"] == Q.TRANSFERRED_S8 and term[i["PARENT_COMPONENT_ID"]] != Q.TRANSFERRED_S8),
        "rate_density_never_duplicates_a_group": density_ok and all(v == 1 for v in cross_once.values()),
        "fifty_plus_fifty_is_one_hundred": all(r["CONTINUOUS_DENSITY_FRACTION"] + r["CURTAILED_DENSITY_FRACTION"]
                                               == 1.0 for r in fifty_rows),
        "mismatch_splits_do_not_overlap": not split_cross,
        "local_top_does_not_coexist_with_the_superseded_rule": not note2_at_override,
        "temperature_components_stay_separate": temp_sep,
        "s8_transfers_never_in_s7_candidates": not s8_leak,
        "local_strips_reconcile_to_panel_geometry": all(v["reconciled"] for v in recon.values()),
        "no_kg_in_pre_s7_1": all(i["KG"] is None for i in items) and all(r["KG"] is None for r in readiness),
        "no_released_item_uses_40cl_or_cover": all(Q.EXTENT_MINIMUM_COVER not in (i.get("EXTENT_BASES") or [])
                                                   for i in cands),
        "no_forbidden_label": not any(str(v).upper() in Q.FORBIDDEN_LABELS for i in items for v in i.values()
                                      if isinstance(v, str))}
    check(all(gates.values()), f"conservation gates {gates}")
    return locals()


def readiness_state(readiness, cid):
    for r in readiness:
        if r["COMPONENT_ID"] == cid:
            return r["AD2_STATE"]
    return None


# ------------------------------------------------------------------ write
ITEM_FIELDS = ["QTO_ITEM_ID", "PARENT_COMPONENT_ID", "ITEM", "OWNER", "FLOOR", "DIRECTION", "SUPPORT_ID",
               "SIDE_PANEL", "RUN_ID", "END_CONDITION", "DIA_MM", "COUNT_BASIS", "RATE_PER_M", "EXPLICIT_COUNT",
               "COUNT_RELEASED", "DENSITY_FRACTION", "DISTRIBUTION_WIDTH_MM", "EQUIVALENT_BAR_COUNT",
               "PHYSICAL_BBS_BAR_COUNT", "RUN_INTEGRAL_M2", "MEAN_RUN_MM", "RUN_RULE", "EXTENT_BASES", "LANE",
               "AUTHORITY", "LAYER_AUTHORITY", "BLOCKERS", "QUESTIONS", "S8_REGION", "STRIPS", "NOTE", "KG"]


def write(B):
    _json("01_AD2_DECISIONS.json", {
        "decision_set": DECISION_SET, "authority": "URBAN_OWNER_DECISION (AD2 + PRE-S7.1 brief)",
        "baseline_head": BASELINE_HEAD, "frozen_pre_s7": B["frozen"]["PRE-S7"]["manifest_sha256"],
        "decisions": [{"id": a, "brief_section": b, "name": c, "decision": d} for a, b, c, d in DECISIONS],
        "lanes": list(Q.LANES), "never": list(Q.FORBIDDEN_LABELS),
        "urban_rules": {Q.URBAN_TOP_EXTENT_RULE: "1/3 x local clear span from the support face into the panel "
                                                 "(AD2-D06)",
                        Q.URBAN_LOCAL_BAR_LINE_RULE: "local clear run along each bar line; local L for span rules on "
                                                     "irregular panels (AD2-D14)"},
        "no_kg": True})
    _csv("02_OWNERSHIP_TRANSFERS.csv", B["transfers"], ["TRANSFER_ID", "object_id", "kind", "from_stage",
                                                         "to_stage", "region", "reason", "state", "quantity_lost",
                                                         "source_conflict_preserved"])
    _csv("03_RATE_QTO_REGISTER.csv", B["rate_rows"], ITEM_FIELDS)
    _csv("04_50_PERCENT_CURTAILMENT_REGISTER.csv", B["fifty_rows"], list(B["fifty_rows"][0]))
    _csv("05_TOP_RULE_IDENTITY.csv", B["ident"], ["RULE_A", "RULE_B", "LOCATION", "IDENTITY", "EVIDENCE",
                                                  "CONTRADICTIONS", "GOVERNING", "OVERRIDDEN", "OVERRIDDEN_STATE",
                                                  "SUMMED", "AUTHORITY"])
    _csv("06_SUPPORT_MISMATCH_SPLITS.csv", B["split_rows"], list(B["split_rows"][0]))
    _csv("07_LOCAL_BAR_STRIPS.csv", B["strip_rows"], list(B["strip_rows"][0]))
    _csv("08_UPDATED_COMPONENT_READINESS.csv", B["readiness"], list(B["readiness"][0]))
    _csv("09_REMAINING_CONFLICTS.csv", B["conf"], ["PRE_S7_CONFLICT_ID", "KIND", "WHERE", "AD2_STATE", "DECISION",
                                                   "TRUE_SOURCE_CONFLICT", "NOTE"])
    _csv("10_REMAINING_BLOCKERS.csv", B["blockers"], ITEM_FIELDS)
    _csv("11_S7_RELEASE_CANDIDATES.csv", B["cands"], ITEM_FIELDS)
    with open(HERE / "12_PROVENANCE.jsonl", "w", encoding="utf-8") as f:
        src = f"ST7757.dxf {DRAWING_SHA[:12]} + frozen S1 + frozen PRE-S7 ({B['frozen']['PRE-S7']['manifest_sha256'][:12]})"
        for kind, rows, key in (("DECISION", [{"id": a} for a, *_ in DECISIONS], "id"),
                                ("TRANSFER", B["transfers"], "TRANSFER_ID"),
                                ("STRIP", B["strip_rows"], "LOCAL_BAR_STRIP_ID"),
                                ("ITEM", B["items"], "QTO_ITEM_ID"),
                                ("COMPONENT", B["readiness"], "COMPONENT_ID"),
                                ("HATCH", B["hatch_rows"], "id"),
                                ("SUPPORT", [{"id": k, **v} for k, v in sorted(B["ad2_sup"].items())], "id")):
            for r in rows:
                f.write(json.dumps({"kind": kind, "id": r[key], "round": ROUND, "decision_set": DECISION_SET,
                                    "source": src, "record": r}, sort_keys=True, ensure_ascii=False,
                                   default=str) + "\n")
    s = summarise(B)
    _json("PRE_S7_1_SUMMARY.json", s)
    (HERE / "00_README.md").write_text(readme(B, s), encoding="utf-8")
    return s


def summarise(B):
    rd, items, cands = B["readiness"], B["items"], B["cands"]
    pre = [r for r in rd if not r["NEW_IN_AD2"]]
    st = Counter(r["AD2_STATE"] for r in pre)
    rate_pre = [r for r in pre if "COUNT_BASIS_UNRESOLVED" in r["PRE_S7_BLOCKERS"]]
    fifty_pre = [r for r in pre if "WHICH_50_PERCENT_UNRESOLVED" in r["PRE_S7_BLOCKERS"]]
    irregular = sorted(p for p in B["in_scope"] if not B["rect"][p])
    irr_rel = sorted({i["OWNER"] for i in cands if i["OWNER"] in irregular and i["ITEM"].startswith("BOTTOM_")} |
                     {i.get("SIDE_PANEL") for i in cands if i.get("SIDE_PANEL") in irregular})
    sunk_rel = sorted({i["OWNER"] for i in cands if i["OWNER"] in B["sunken"]} |
                      {i.get("SIDE_PANEL") for i in cands if i.get("SIDE_PANEL") in B["sunken"]})
    temp_block = [r for r in pre if r["COMPONENT"].startswith("TEMPERATURE") and r["AD2_STATE"] == "BLOCKED"]
    return {
        "round": ROUND, "decision_set": DECISION_SET, "policy": POLICY, "baseline_head": BASELINE_HEAD,
        "no_kg": True, "s7_started": False,
        "frozen": {k: {kk: v[kk] for kk in ("manifest", "manifest_sha256", "round", "files_checked")}
                   for k, v in B["frozen"].items()},
        "decisions_recorded": len(DECISIONS),
        "pre_s7": {"components": len(pre), "s7_release_candidates": B["pre_summary"]["s7_release_candidates"],
                   "conditional_candidates": B["pre_summary"]["conditional_candidates"],
                   "blocked": B["pre_summary"]["blocked_from_s7"]},
        "components_by_ad2_state": dict(st),
        "new_components": len([r for r in rd if r["NEW_IN_AD2"]]),
        "components_with_released_quantity": sum(r["RELEASED_ITEMS"] > 0 for r in pre),
        "items": len(items), "items_by_lane": dict(Counter(i["LANE"] for i in items)),
        "candidate_items": len(cands),
        "candidate_items_by_lane": dict(Counter(i["LANE"] for i in cands)),
        "candidate_items_by_kind": dict(Counter(i["ITEM"] for i in cands)),
        "source_derived_candidates": sum(i["LANE"] == Q.SOURCE_DERIVED_PHYSICAL for i in cands),
        "project_basis_candidates": sum(i["LANE"] == Q.PROJECT_BASIS_QTO for i in cands),
        "source_derived_counts_released_length_blocked": sum(bool(i.get("COUNT_RELEASED")) for i in items),
        "blocked_items": len(B["blockers"]),
        "blocked_items_by_kind": dict(Counter(i["ITEM"] for i in B["blockers"])),
        "blocked_components": st.get("BLOCKED", 0),
        "rate_components": len(rate_pre),
        "rate_components_unlocked": sum(r["RELEASED_ITEMS"] > 0 for r in rate_pre),
        "fifty_percent_components": len(fifty_pre),
        "fifty_percent_components_unlocked": sum(r["RELEASED_ITEMS"] > 0 for r in fifty_pre),
        "fifty_percent_families": len(B["fifty_rows"]),
        "top_rule_identity": {"conclusion": Q.SAME_FAMILY, "governing": "P4-6-NOTE-2-TOP-OVER-BEAMS",
                              "overridden": ["P15-TOP-NONCONT-0.25L1", "P15-TOP-CONT-0.30Lmax",
                                             "P15-TOP-EXTEND-50PCT"],
                              "extent_rule": Q.URBAN_TOP_EXTENT_RULE, "authority": Q.URBAN_OWNER_MEASUREMENT_RULE,
                              "local_override_supports": sorted(B["explicit"])},
        "mismatch_supports_split": len({r["SUPPORT_ID"] for r in B["split_rows"]}),
        "mismatch_split_rows": len(B["split_rows"]),
        "continuous_supports_one_run": len({i["SUPPORT_ID"] for i in cands if i["ITEM"] == "BOTTOM_SUPPORT_CROSSING"}),
        "irregular_panels": len(irregular), "irregular_panels_recovered": len(irr_rel),
        "sunken_panels": len(B["sunken"]), "sunken_panels_recovered": len(sunk_rel),
        "sunken_mesh": {p: v["mesh"] for p, v in B["sunken_dec"].items()},
        "transferred_components_by_region": dict(Counter(
            "; ".join(sorted({i.get("S8_REGION") for i in B["by_parent"][r["COMPONENT_ID"]]}))
            for r in pre if r["AD2_STATE"] == Q.TRANSFERRED_S8)),
        "transferred_side_items_by_region": dict(Counter(
            i["S8_REGION"] for i in items if i["LANE"] == Q.TRANSFERRED_S8 and
            B["term"][i["PARENT_COMPONENT_ID"]] != Q.TRANSFERRED_S8)),
        "lightwell_transferred": {"panel": B["lightwell"],
                                  "objects": len([t for t in B["transfers"] if t["region"] == LIGHTWELL_REGION])},
        "transfers": len(B["transfers"]),
        "temperature_components_blocked": len(temp_block),
        "remaining_true_source_conflicts": [c["PRE_S7_CONFLICT_ID"] + " " + c["KIND"] for c in B["conf"]
                                            if c["TRUE_SOURCE_CONFLICT"]],
        "dense_hatch": {h["id"]: h["state"] for h in B["hatch_rows"]},
        "topology_corrections_by_geometry": [t["WHERE"] for t in B["topo"]],
        "questions_new_in_ad2": {
            "Q-CONT": "Continuity / crossing at a support whose far side is a junction, a set-back or a slab analysed "
                      "elsewhere: which bars stop, anchor or run through?",
            "Q-OBLIQUE": "Bars meeting a support they do not cross squarely (slanted beams, notches): end detail?",
            "Q-EDGE": "Short / curved boundary edges with no support record: what supports the slab there and do top "
                      "bars apply?"},
        "questions_carried_from_pre_s7": sorted({q for i in B["blockers"] for q in (i.get("QUESTIONS") or [])} -
                                                {"Q-CONT", "Q-OBLIQUE", "Q-EDGE"}),
        "blocked_items_by_question": dict(Counter(q for i in B["blockers"] for q in (i.get("QUESTIONS") or []))),
        "support_continuity_pre_s7": dict(Counter(v["pre_s7_type"] for v in B["ad2_sup"].values())),
        "support_continuity_ad2": dict(Counter(str(v["continuity"]) for v in B["ad2_sup"].values())),
        "support_continuity_changed": sorted(k for k, v in B["ad2_sup"].items()
                                             if v["continuity"] and v["continuity"] != v["pre_s7_type"]),
        "local_bar_strips": len(B["strip_rows"]),
        "strip_reconciliation": all(v["reconciled"] for v in B["recon"].values()),
        "gates": B["gates"], "engine_commit": f"{BASELINE_HEAD}+code:{code_digest()}",
        "flags": {"kg_calculated": False, "bar_length_total_calculated": False, "s7_started": False,
                  "interpolated_temperature": False, "nts_measured": False, "donor_or_code_used": False,
                  "pre_s7_edited": False, "references_read": []}}


def readme(B, s):
    by_state = ", ".join(f"{k} {v}" for k, v in sorted(s["components_by_ad2_state"].items()))
    L = [
        "# PRE-S7.1 / AD2: slab QTO authority / readiness resolution", "",
        f"**Round:** `{ROUND}` · **Decisions:** `{DECISION_SET}` ({s['decisions_recorded']}) · **Policy:** `{POLICY}` · "
        f"**Baseline:** HEAD `{BASELINE_HEAD}` · built by `build_pre_s7_1.py` (blind, byte-identical rebuild) · "
        "**No kg, no bar-length total, S7 not started.**", "",
        "A delta over frozen PRE-S7. PRE-S7 is not edited: its freeze manifest and the nine before it (S4 ... D1.2) "
        "were hash-checked before anything was read. Every PRE-S7 component terminates exactly once here.", "",
        "## Lanes", "",
        "- `SOURCE_DERIVED_PHYSICAL`: the source gives count, extent and role.",
        "- `PROJECT_BASIS_QTO`: the source gives specification / rate / role; Urban measures with a declared rule "
        "(rate density N x W unrounded, the 0.5 / 0.5 curtailment density, 1/3 x local clear span from the support "
        "face, local bar lines). Never VERIFIED_PHYSICAL or AS_BUILT.",
        "- `BLOCKED_UNQUANTIFIED`: the bar, its applicability, extent or classification is not established.", "",
        "## Result", "",
        f"- PRE-S7: {s['pre_s7']['s7_release_candidates']} release candidates, {s['pre_s7']['conditional_candidates']} "
        f"conditional on owner decisions, {s['pre_s7']['blocked']} blocked.",
        f"- PRE-S7.1 components: {by_state} (+ {s['new_components']} new blocked components). "
        f"{s['components_with_released_quantity']} PRE-S7 components release quantity.",
        f"- Released items: {s['candidate_items']} ({', '.join(f'{k} {v}' for k, v in sorted(s['candidate_items_by_lane'].items()))}); "
        f"source-derived counts released with blocked lengths: {s['source_derived_counts_released_length_blocked']}. "
        f"Blocked items: {s['blocked_items']}.",
        f"- Rate components unlocked {s['rate_components_unlocked']} / {s['rate_components']}; 50% components "
        f"unlocked {s['fifty_percent_components_unlocked']} / {s['fifty_percent_components']}.",
        "- Top bars over beams: plan note 2 and the p.15 top bars are one physical family (p.15 defers size and "
        "spacing to the plan). The floor plan note governs; p.15's 0.25 L1 / 0.30 max L / 'extend 50%' are "
        "OVERRIDDEN_PROJECT_SOURCE. The extent is the Urban rule 1/3 x local clear span from the support face "
        "(URBAN_OWNER_MEASUREMENT_RULE). The bound '/Top' callout overrides note 2 at its own support.",
        f"- Mismatched continuous supports split left / right: {s['mismatch_supports_split']} supports "
        f"({s['mismatch_split_rows']} panel pairs); continuous supports with a released one-run crossing: "
        f"{s['continuous_supports_one_run']}.",
        f"- Irregular panels recovered {s['irregular_panels_recovered']} / {s['irregular_panels']} (local bar lines); "
        f"sunken panels recovered {s['sunken_panels_recovered']} / {s['sunken_panels']} (mesh kept, step extras "
        "blocked).",
        f"- Temperature components blocked: {s['temperature_components_blocked']} (160 mm, no table row); they "
        "block nothing else.",
        f"- S8 transfers: {s['transfers']} records (water tank, light well, special-structure sides of supports).",
        f"- Topology corrections found by geometry (the face beyond each bar line, not the S1 edge neighbour): "
        f"{len(s['topology_corrections_by_geometry'])} supports (09_REMAINING_CONFLICTS.csv, G-rows).",
        f"- Remaining true source conflicts: {', '.join(s['remaining_true_source_conflicts'])}.", "",
        "## Files", "", "| File | Content |", "|---|---|",
        "| 01_AD2_DECISIONS.json | the 17 owner decisions and the two Urban rules |",
        "| 02_OWNERSHIP_TRANSFERS.csv | S7 -> S8 transfers (panels, tokens, marks, components, support sides) |",
        "| 03_RATE_QTO_REGISTER.csv | every rate-based item: N, fraction, W, N x W (unrounded), BBS count unresolved |",
        "| 04_50_PERCENT_CURTAILMENT_REGISTER.csv | 0.5 / 0.5 density split per family |",
        "| 05_TOP_RULE_IDENTITY.csv | bar-role identity, precedence, the Urban extent rule, the local override |",
        "| 06_SUPPORT_MISMATCH_SPLITS.csv | left / right runs to the face; transitions blocked |",
        "| 07_LOCAL_BAR_STRIPS.csv | local bar-line strips per panel and direction, with what lies beyond each end |",
        "| 08_UPDATED_COMPONENT_READINESS.csv | every PRE-S7 component (+ new blocked components), one state each |",
        "| 09_REMAINING_CONFLICTS.csv | PRE-S7 conflicts re-evaluated + topology corrections by geometry |",
        "| 10_REMAINING_BLOCKERS.csv | blocked items with their question |",
        "| 11_S7_RELEASE_CANDIDATES.csv | released items: lane, density, width, equivalent bars, mean local run |",
        "| 12_PROVENANCE.jsonl | one line per record |", "| PRE_S7_1_SUMMARY.json | counts, gates, flags |", ""]
    return "\n".join(L)


def main():
    B = build()
    B["frozen"] = B["frozen"]
    s = write(B)
    man = {"round": ROUND, "state": "FROZEN", "references_read_before_freeze": [],
           "rule": "a readiness delta over frozen PRE-S7: no kg; frozen stages are never edited",
           "engine_commit_stamp": s["engine_commit"],
           "code": {c: _sha(ROOT / c) for c in CODE}, "inputs": {i: _sha(ROOT / i) for i in INPUTS},
           "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
           "drawing_sha256": {"ST7757.dxf": DRAWING_SHA},
           "frozen_baselines": {k: v["manifest_sha256"] for k, v in B["frozen"].items()}}
    _json("PRE_S7_1_FREEZE_MANIFEST.json", man)
    print(json.dumps({k: s[k] for k in ("components_by_ad2_state", "candidate_items_by_lane", "blocked_items",
                                        "rate_components_unlocked", "fifty_percent_components_unlocked",
                                        "mismatch_supports_split", "irregular_panels_recovered",
                                        "sunken_panels_recovered", "gates")}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
