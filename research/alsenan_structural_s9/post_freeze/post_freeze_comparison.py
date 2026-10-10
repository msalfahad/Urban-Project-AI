"""S9 post-freeze comparison: the frozen whole-building structural BOQ against the earlier figures, after the freeze.

    python3 -I research/alsenan_structural_s9/post_freeze/post_freeze_comparison.py

Reads the frozen S9 package (its manifest and the 29 stage manifests are verified before and after; nothing frozen is
written), then the earlier figures S9 did not read before its freeze:
  * the old Urban V3b BOQ concrete and reinforcement lines (BOQ_LINES_V3B, REBAR_POPULATION_REGISTER);
  * the PRE-S8 structural element census (02) and concrete coverage matrix (03);
  * the R5 architectural stair register (context only).
Every difference is classified (NO_DIFFERENCE, METHOD, SCOPE, AUTHORITY, MISSED_OBJECT, NOT_DECOMPOSABLE,
NOT_COMPARABLE, or a combination) and explained. Nothing here changes a frozen quantity, tunes S9 or releases anything:
a finding that needs a change is recorded for a separately approved correction layer.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import delta_release as DR  # noqa: E402

R = ROOT / "research"
V3B = ROOT / "tests/alsenan/registers_v3b"
PRE_S8 = R / "pre_s8_structural_completeness"
R5_STAIRS = R / "alsenan_arch_truth_05/registers/STAIR_ARCHITECTURAL_REGISTER.json"
MANIFEST = PKG / "16_S9_FREEZE_MANIFEST.json"
OUT = ["00_POST_FREEZE_README.md", "01_OLD_BOQ_CONCRETE_COMPARISON.csv", "02_OLD_BOQ_REBAR_COMPARISON.csv",
       "03_PRE_S8_CENSUS_CROSSWALK.csv", "04_ABSENT_FROM_OLD_BOQ.csv", "05_POST_FREEZE_FINDINGS.csv",
       "06_POST_FREEZE_SUMMARY.json"]
RELEASED = ("RELEASED_FROZEN_STAGE", "RELEASED_S9_DELTA")
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
FORBIDDEN = (44.19, 352.436075, 77.6305, 75.09, 39.7515, 65.965875, 59.8174, 21.8328, 12.348, 337.812, 333.173,
             22.619, 22.916)
RULE = ("comparison only, after the freeze: S9 is not tuned, nothing is released and no frozen quantity changes; a "
        "finding that needs a change goes to a separately approved correction layer")


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _f(v):
    return None if v in (None, "", "None") else float(v)


def _r(v, nd=6):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        s = f"{v:.6f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=keys, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in keys})
    return buf.getvalue()


def _verify():
    """The S9 manifest and the 29 stage manifests it froze over (found by their recorded sha256)."""
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    DR.verify_frozen(MANIFEST, ROOT)
    want = set(m["frozen_baselines"].values())
    found = {}
    for p in sorted(R.glob("*/*.json")):
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if h in want:
            DR.verify_frozen(p, ROOT)
            found[h] = str(p.relative_to(ROOT))
    assert set(found) == want, sorted(want - set(found))
    return {"manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(), "state": m["state"],
            "other_frozen_manifests": len(found)}


# ------------------------------------------------------------------ S9 views
def s9_views():
    conc = _rows(PKG / "02_CONCRETE_BOQ_RECONCILIATION.csv")
    bars = _rows(PKG / "03_REINFORCEMENT_BOQ_RECONCILIATION.csv")
    for c in conc:
        c["_dims"] = json.loads(c["DIMENSIONS"]) if c["DIMENSIONS"].startswith("{") else {}
        c["_rng"] = json.loads(c["CONDITIONAL_RANGE_M3"]) if c["CONDITIONAL_RANGE_M3"] else None
    return conc, bars, json.loads((PKG / "14_RELEASE_SUMMARY.json").read_text(encoding="utf-8"))


def s9_stats(rows):
    rel = math.fsum(_f(c["RELEASED_M3"]) or 0.0 for c in rows if c["LANE"] in RELEASED)
    cond = [c for c in rows if c["LANE"] not in RELEASED and (c["CONDITIONAL_M3"] or c["_rng"])]
    pt = math.fsum(_f(c["CONDITIONAL_M3"]) or 0.0 for c in cond)
    lo = math.fsum((c["_rng"][0] or 0.0) for c in cond if c["_rng"])
    hi = math.fsum((c["_rng"][1] or 0.0) for c in cond if c["_rng"])
    lanes = defaultdict(int)
    for c in rows:
        lanes[c["LANE"]] += 1
    return {"S9_COMPONENTS": len(rows), "S9_RELEASED_M3": _r(rel), "S9_CONDITIONAL_POINT_M3": _r(pt),
            "S9_CONDITIONAL_RANGE_SUM_M3": [_r(lo), _r(hi)] if cond else None,
            "S9_NO_VALUE_COMPONENTS": sum(1 for c in rows if c["LANE"] not in RELEASED and c not in cond and
                                          c["LANE"] not in ("NOT_APPLICABLE", "EXCLUDED_OWNED_BY_OTHER_FAMILY")),
            "S9_LANES": dict(sorted(lanes.items()))}


# ------------------------------------------------------------------ old Urban V3b
def v3b_lines():
    d = json.loads((V3B / "BOQ_LINES_V3B.json").read_text(encoding="utf-8"))
    out = {}
    for x in d["lines"]:
        out[x["code"]] = {"line_id": x["line_id"], "trade": x["trade"], "level": x["level"], "desc": x["desc_en"],
                          "unit": x["unit"], "qty": _f(x["qty"]), "status": x["status"], "formula": x["formula"]}
    return out


def _plate_m2(formula):
    m = re.search(r"net plate ([0-9.]+) m2", formula or "")
    return float(m.group(1)) if m else None


CONCRETE_GROUPS = [
    # (group, V3b codes, S9 filter, class, explanation template)
    ("FOOTINGS", ["C-FTG", "C-FTG-FF10"], lambda c: c["FAMILY"] == "FOOTINGS", "METHOD",
     "same 25 schedule footings (L x W x H) and the same F / F10 conflict blocked; S9 deducts the F9 / FN outline "
     "overlap at its maximum shared prism (0.14 m2 x 0.30 = 0.042 m3) once, V3b does not"),
    ("BLINDING", ["C-BLD-F", "C-BLD-GB", "C-BLD-FULL"], lambda c: c["FAMILY"] == "PLAIN_CONCRETE", "AUTHORITY",
     "V3b uses an owner method (10 cm, 10 cm beyond, full founded footprint); S9 finds no printed blinding thickness or "
     "projection (P8-N16 gives the mix only; p.16 is typical) and keeps it blocked"),
    ("STRAP_BEAMS", ["C-STR"], lambda c: c["FAMILY"] == "GROUND_BEAMS" and c["SUBFAMILY"].startswith("STRAP"),
     "AUTHORITY", "V3b measures all three strap bands; S9 releases the two with explicit sections and keeps SB2 as a "
     "width source conflict (S1 review queue item 9)"),
    ("GROUND_BEAMS", ["C-GB-INT", "C-GB-EXT"], lambda c: c["FAMILY"] == "GROUND_BEAMS" and
     c["SUBFAMILY"].startswith("GROUND_BEAM"), "AUTHORITY",
     "V3b applies the p.13 length classes (< 2.5 / 2.5 - 5 / > 5 m) on its own length basis to 31 interior spans; S9 "
     "releases only the spans whose section is explicit and keeps the class basis (centre-to-centre or clear) as a "
     "consultant question, with a candidate range; exterior 'FOLLOW ARCH' depths are blocked in V3b and an upper bound "
     "only in S9"),
    ("COLUMN_NECKS", ["C-NECK"], lambda c: c["FAMILY"] == "COLUMNS" and c["STOREY"] == "FOUNDATION",
     "NO_DIFFERENCE", "both blocked: the founding level is not printed (S9 shows an indicative value only)"),
    ("GROUND_SLAB", ["C-GSLAB-ZONE-1", "C-GSLAB-ZONE-2"], lambda c: c["FAMILY"] == "GROUND_SLAB", "AUTHORITY + SCOPE",
     "V3b applies 'T = 10 cm' to two whole zones; S8.1 released only the two source-zoned cells and S8.1A kept the "
     "note's scope and cover open for the other faces (conditional in S9)"),
    *[(f"COLUMNS_{s}", [f"C-COL-{s if s != '2F' else '2F'}", f"C-COL-{s}-RES", f"C-JNT-{s}"],
       (lambda st: (lambda c: c["FAMILY"] == "COLUMNS" and c["STOREY"] == st))(s), "METHOD + SCOPE",
       "V3b measures the column clear of the beam depth plus a separate joint (section x beam depth below the slab) and "
       "leaves the slab thickness to the slab plate; S9 measures the full printed floor-to-floor and its slab panels "
       "stop at the faces (S9-MC1). Populations differ: V3b computes every bound column, S9 releases only S2-VERIFIED "
       "occurrences whose drawn section equals the schedule") for s in ("GF", "1F", "2F")],
    *[(f"BEAMS_{s}", [f"C-BEAM-{s}", f"C-BEAM-{s}-RES"],
       (lambda st: (lambda c: c["FAMILY"] == "BEAMS" and c["STOREY"] == st))(s), "AUTHORITY + METHOD",
       "V3b measures clear length x B x (D - t), reading the schedule depth as overall; S9 releases no beam because the "
       "depth convention is not printed and S2 holds the lengths as a lower bound. S9's point B x H x L equals V3b's "
       "downstand plus the B x t strip V3b leaves in its slab plate") for s in ("GF", "1F", "2F")],
    *[(f"SLABS_{s}", [f"C-SLAB-{s}"], (lambda st: (lambda c: c["FAMILY"] == "SLABS" and c["STOREY"] == st))(s),
       "METHOD + SCOPE", "V3b measures one net plate over the beams; S9 measures panels between the beam and column "
       "faces and leaves the stair, dome and tank panels to their own stages (see the area reconciliation)")
      for s in ("GF", "1F", "2F")],
    *[(f"LINTELS_{s}", [f"C-LINT-{s}"], (lambda st: (lambda c: c["FAMILY"] == "LINTELS" and c["STOREY"] == st))(s),
       "AUTHORITY", "V3b gives every opening a lintel of (opening + 2 x 0.40) x wall t x depth; S8.6A releases only "
       "the schedule-bound lintels with confirmed bearing and head function") for s in ("GF", "1F", "2F")],
    ("STAIRS", ["C-STAIR"], lambda c: c["FAMILY"] == "STAIRS", "SCOPE",
     "V3b blocks the stairs technically; S8.7 released the three landing plates and keeps every flight blocked "
     "(S8.7A / S8.7B / S8.7C: owner scenarios not approved)"),
    ("DOMES", ["C-DOME-SHELL-12EB", "C-DOME-RING-12EB", "C-DOME-SHELL-1300", "C-DOME-RING-1300",
               "C-DOME-SHELL-2F33", "C-DOME-RING-2F33"], lambda c: c["FAMILY"] == "DOMES", "METHOD + AUTHORITY",
     "V3b uses 2 pi R h x t for three shells, including a tower-roof shell; S8.3 integrates the two terrace shells and "
     "keeps the tower dome as an architecture-only source conflict; rings are blocked in both"),
    ("POOL", ["C-POOL", "C-POOL-BLD"], lambda c: c["FAMILY"] == "POOL", "AUTHORITY",
     "V3b uses one 1.15 m depth; S8.2 / S8.2A found the depths 'AS PER ARCH' and varying from the deep to the shallow "
     "end, so every pool element stays blocked"),
    ("STRUCTURAL_WALLS", ["C-SWALL"], lambda c: False, "MISSED_OBJECT",
     "both hold no quantity, but S9 has no row at all for the cantilever / bearing-wall bands the PRE-S8 census lists "
     "(F-01)"),
    ("BOUNDARY_WALL", ["C-BWALL"], lambda c: c["FAMILY"] == "BOUNDARY_WALL", "NO_DIFFERENCE",
     "both unquantified (V3b blocked; S9 typical detail vs schedule row B.W conflict)"),
]


def concrete_comparison(conc, v3b):
    out, used = [], set()
    for g, codes, filt, cls, why in CONCRETE_GROUPS:
        pairs = [(c, v3b[c]) for c in codes if c in v3b]
        lines = [x for _, x in pairs]
        used |= {c for c, _ in pairs}
        tech = [x["qty"] for x in lines if x["qty"] is not None]
        q = math.fsum(tech) if tech else None
        st = s9_stats([c for c in conc if filt(c)])
        d = _r(st["S9_RELEASED_M3"] - q) if q is not None else None
        if g == "FOOTINGS":
            assert abs(d + 0.042) < 1e-6, d                                         # exactly the overlap prism
        if cls == "NO_DIFFERENCE":
            assert not st["S9_RELEASED_M3"] and q is None, g
        out.append({"GROUP": g, "V3B_LINES": [f"{x['line_id']} {c}" for c, x in pairs],
                    "V3B_STATUSES": sorted({x["status"] for x in lines}), "V3B_TECHNICAL_M3": _r(q),
                    "V3B_METHOD": "; ".join(dict.fromkeys(x["formula"] for x in lines if x["formula"]))[:300],
                    **{k: v for k, v in st.items() if k != "S9_LANES"}, "S9_LANES": st["S9_LANES"],
                    "S9_RELEASED_MINUS_V3B_M3": d, "CLASS": cls, "EXPLANATION": why})
    rest = sorted(c for c, x in v3b.items() if x["trade"] == "CONCRETE" and c not in used)
    assert not rest, rest
    return out


def slab_area_reconciliation(conc, v3b):
    """V3b's net plate per floor against S9's released panels plus what S9 gives to other owners or to the beams and
    columns (S9-MC1). Context only: it explains the METHOD + SCOPE class, it releases nothing."""
    out = []
    for s in ("GF", "1F", "2F"):
        plate = _plate_m2(v3b[f"C-SLAB-{s}"]["formula"])
        sl = [c for c in conc if c["FAMILY"] == "SLABS" and c["STOREY"] == s]
        rel = math.fsum(c["_dims"].get("area_m2_s1") or 0 for c in sl if c["LANE"] in RELEASED)
        owned = [c for c in conc if c["STOREY"] == s and c["COMPONENT_ID"].startswith("SP-")
                 and c["LANE"] == "EXCLUDED_OWNED_BY_OTHER_FAMILY"]
        other = math.fsum(c["_dims"].get("area_m2_s1") or 0 for c in owned)
        stairs = math.fsum(c["_dims"].get("area_m2_s1") or 0 for c in owned if c["OWNER_FAMILY"] == "STAIRS")
        beams = math.fsum((c["_dims"].get("B_mm") or 0) / 1000 * (c["_dims"].get("clear_m") or 0)
                          for c in conc if c["FAMILY"] == "BEAMS" and c["STOREY"] == s)
        cols = math.fsum((c["_dims"].get("schedule_cm") or [0, 0])[0] * (c["_dims"].get("schedule_cm") or [0, 0])[1]
                         / 1e4 for c in conc if c["FAMILY"] == "COLUMNS" and c["STOREY"] == s
                         and c["_dims"].get("schedule_cm") and None not in c["_dims"]["schedule_cm"])
        expl = rel + other + beams + cols
        out.append({"STOREY": s, "V3B_NET_PLATE_M2": plate, "S9_RELEASED_PANELS_M2": _r(rel, 3),
                    "S9_OTHER_OWNER_PANELS_M2": _r(other, 3), "OF_WHICH_STAIR_ZONES_M2": _r(stairs, 3),
                    "BEAM_FOOTPRINTS_CLEAR_M2": _r(beams, 3), "COLUMN_FOOTPRINTS_M2": _r(cols, 3),
                    "EXPLAINED_M2": _r(expl, 3), "RESIDUAL_M2": _r(plate - expl, 3) if plate else None,
                    "RESIDUAL_IF_V3B_NETS_THE_STAIR_ZONES_M2": _r(plate - expl + stairs, 3) if plate else None,
                    "NOTE": "beam footprints use the clear length where held (curved bands carry none). V3b states one "
                            "net plate and no breakdown, so the residual is not decomposable: a negative residual means "
                            "V3b nets out more than S9 hands to other owners (the stair zones are the likely part), a "
                            "positive one is plate S9 does not place"})
    return out


REBAR_GROUPS = [
    ("COLUMNS", ["COLUMNS", "COLUMN_STARTERS"], "COLUMNS", "METHOD",
     "S3.1 parts; S9-C01 holds the sharp-path ties and hook allowances (1,217.128 kg) conditional; V3b uses a code "
     "method for ties; laps are outside both nets; starters are provisional in both"),
    ("FOOTINGS", ["FOOTINGS", "FOOTING_F_F10"], "FOOTINGS", "NOT_DECOMPOSABLE",
     "V3b states 52 bar sets (4 blocked) and no per-set detail, so the gap cannot be decomposed from the V3b registers; "
     "S4 counts every schedule mat (bottom both ways at 25 footings, top both ways at 5) on cover-adjusted lengths; "
     "F / F10 is blocked in both (F-03)"),
    ("GROUND_BEAMS", ["GROUND", "GROUND_BEAM_EXT"], "GROUND_BEAMS", "METHOD",
     "S5 straight bars + S5.1 through-support runs, less AD1 and D1.1 (link core paths are not lower bounds); V3b uses "
     "a code method and excludes hooks from its technical figure; exterior ground beams unquantified in both"),
    ("BEAMS", ["BEAMS", "BEAM_RESIDUE", "BEAM_SIDE_BARS"], "BEAMS", "METHOD",
     "S6 + S6.1 less D1.1 (1,332.264 kg of link core paths retracted); V3b uses a code method for links and keeps "
     "residue and side bars out of its technical figure"),
    ("SLABS", ["SLAB"], "SLABS", "SCOPE + METHOD",
     "S7 is the restricted project basis (anchorage, continuity, temperature steel, laps and trims blocked); V3b adds "
     "geometric inferences; the tank roof is a separate S8.4 family in S9 (361.209 kg)"),
    ("GROUND_SLAB", ["GROUND_SLAB"], "GROUND_SLAB", "SCOPE", "S8.1 releases the two source-zoned cells only"),
    ("DOMES", ["DOME"], "DOMES", "SCOPE + AUTHORITY",
     "S8.3 releases the two shell meshes; rings, drums, junction bars and laps are blocked and the tower dome is a "
     "source conflict; V3b quantifies all of them"),
    ("LINTELS", ["LINTELS"], "LINTELS", "AUTHORITY", "S8.6A keeps the seven schedule-bound lintels only"),
    ("POOL", ["POOL"], "POOL", "AUTHORITY", "all pool families blocked (depths 'AS PER ARCH')"),
    ("STAIRS", ["STAIRS"], "STAIRS", "SCOPE", "S8.7's three landing plates (8 Ø16 / m); flights blocked in both"),
    ("BOUNDARY_WALL", ["BOUNDARY_WALL"], None, "NO_DIFFERENCE", "no technical kg in either"),
]


def rebar_comparison(bars, s9sum):
    pop = {r["population"]: r for r in json.loads((V3B / "REBAR_POPULATION_REGISTER.json").read_text(
        encoding="utf-8"))["rows"]}
    out, used = [], set()
    fam = s9sum["released_reinforcement_kg_by_family"]
    for g, pops, f9, cls, why in REBAR_GROUPS:
        used |= set(pops)
        tech = math.fsum(float(pop[p]["technical_kg"]) for p in pops)
        hooks = math.fsum(float(pop[p]["hook_kg"]) for p in pops)
        rel = fam.get(f9, 0.0) if f9 else 0.0
        nrel = math.fsum(_f(b["NOT_RELEASED_KG"]) or 0.0 for b in bars if b["FAMILY"] == f9 and
                         b["LANE"] not in RELEASED and b["LANE"] != "SUPERSEDED") if f9 else 0.0
        if cls == "NO_DIFFERENCE":
            assert tech == 0 and rel == 0, g
        out.append({"GROUP": g, "V3B_POPULATIONS": pops, "V3B_TECHNICAL_KG": _r(tech), "V3B_HOOKS_OUTSIDE_KG": _r(hooks),
                    "S9_RELEASED_KG": _r(rel), "S9_NOT_RELEASED_MODELLED_KG": _r(nrel),
                    "S9_RELEASED_MINUS_V3B_KG": _r(rel - tech), "CLASS": cls, "EXPLANATION": why})
    assert set(pop) == used, sorted(set(pop) - used)
    if "WATER_TANK_ROOF" in fam:
        out.append({"GROUP": "WATER_TANK_ROOF", "V3B_POPULATIONS": [], "V3B_TECHNICAL_KG": None,
                    "S9_RELEASED_KG": _r(fam["WATER_TANK_ROOF"]), "CLASS": "SCOPE",
                    "EXPLANATION": "no V3b population of its own (V3b may carry it inside SLAB; not decomposable)"})
    return out


# ------------------------------------------------------------------ PRE-S8 census crosswalk
def pre_s8_crosswalk(conc):
    census = _rows(PRE_S8 / "02_STRUCTURAL_ELEMENT_CENSUS.csv")
    ids = {c["COMPONENT_ID"] for c in conc}
    fams = {c["FAMILY"] for c in conc}
    text = " ".join(c["COMPONENT_ID"] + " " + c["SOURCE"] for c in conc)
    by = defaultdict(list)
    for x in census:
        by[(x["ELEMENT_FAMILY"], x["ROW_KIND"])].append(x)
    stage_rows = {"SPC-": "covered by the owning stage's rows (S8.x population record)", "PS8-": "PRE-S8 evidence row"}
    out = []
    for (fam, kind), xs in sorted(by.items()):
        same = [x for x in xs if x["ELEMENT_ID"] in ids]
        if len(same) == len(xs):
            cls, why = "SAME_ID", "every element is an S9 component"
        elif fam.startswith("CANTILEVER_OR_BEARING_WALL_BAND"):
            cls, why = "MISSED_OBJECT", ("hatch-zone bands on the slab sheets (S7 CLASSIFICATION_BLOCKED, no S1 panel, no "
                                         "owner): S9 registers none of them (F-01)")
        elif fam.startswith("BEAM (CONTINUOUS_BEAM)"):
            marks = sorted({re.search(r"-(CB\d+)-", x["ELEMENT_ID"]).group(1) for x in xs})
            ok = all(f"CONTINUOUS {m}" in " ".join(c["SUBFAMILY"] for c in conc if c["FAMILY"] == "BEAMS")
                     for m in marks)
            cls, why = ("OTHER_ID", f"S9 carries {', '.join(marks)} as S6 span occurrences") if ok else \
                ("MISSED_OBJECT", "a continuous-beam mark has no S9 span")
        elif all(x["ELEMENT_ID"].startswith(("SPC-", "PS8-")) for x in xs):
            cls, why = "STAGE_RECORD", "; ".join(sorted({v for k, v in stage_rows.items()
                                                          if any(x["ELEMENT_ID"].startswith(k) for x in xs)}))
        else:
            cls, why = "PARTIAL", f"{len(same)} of {len(xs)} ids are S9 components"
        out.append({"PRE_S8_FAMILY": fam, "ROW_KIND": kind, "ELEMENTS": len(xs), "IN_S9_BY_ID": len(same),
                    "EXAMPLE_IDS": [x["ELEMENT_ID"] for x in xs[:3]],
                    "PLAN_AREA_M2": _r(math.fsum(float(m.group(1)) for x in xs for m in
                                                 [re.match(r"([0-9.]+) m2", x["PHYSICAL_GEOMETRY"])] if m), 3)
                    if fam.startswith("CANTILEVER_OR_BEARING") else None,
                    "CLASS": cls, "EXPLANATION": why})
    del fams, text
    cov = _rows(PRE_S8 / "03_CONCRETE_COVERAGE_MATRIX.csv")
    for x in cov:
        if x["COVERAGE_STATE"] == "NOT_MEASURED":
            out.append({"PRE_S8_FAMILY": f"03 coverage: {x['FAMILY']} {x['FLOOR']}", "ROW_KIND": "COVERAGE_MATRIX",
                        "ELEMENTS": int(x["ELEMENTS"]), "CLASS": "COVERAGE_NOTE",
                        "EXPLANATION": "PRE-S8 NOT_MEASURED; S9 lane: " + (
                            "BLOCKED (parapets, geometry not printed)" if x["FAMILY"] == "RC_PARAPET" else
                            "BLOCKED (lift, S8.8)" if x["FAMILY"] == "LIFT" else "no S9 row (F-01)"
                            if x["FAMILY"].startswith("CANTILEVER") else
                            "tank roof RELEASED by S8.4; tank walls NOT_IN_SOURCE" if x["FAMILY"] == "WATER_TANK" else
                            "see 02")})
    return out


# ------------------------------------------------------------------ absent from the old BOQ
def absent_from_old_boq(conc, v3b, s9sum):
    out = []
    no_line = [("WATER_TANK_ROOF", "no V3b concrete line (S8.4 releases 2.454 m3; V3b may hold it inside C-SLAB-2F)"),
               ("LIFT", "no V3b line for the pit walls or tie beam (V3b's C-FTG holds FF only); S8.8 keeps them "
                        "blocked / indicative"),
               ("PARAPETS", "no V3b line; S9 blocked (geometry not printed)"),
               ("OTHER", "typical-only details (ribbed slab, casement, beam opening): no V3b line, no S9 quantity")]
    for fam, why in no_line:
        rows = [c for c in conc if c["FAMILY"] == fam]
        st = s9_stats(rows)
        out.append({"DIRECTION": "S9 family with no V3b line", "SUBJECT": fam, "S9_RELEASED_M3": st["S9_RELEASED_M3"],
                    "S9_COMPONENTS": st["S9_COMPONENTS"], "S9_LANES": st["S9_LANES"], "EXPLANATION": why})
    drops = [c for c in conc if c["COMPONENT_ID"].startswith("S9-SUNKEN-DROP-")]
    out.append({"DIRECTION": "S9 component with no V3b line", "SUBJECT": "sunken-slab drops",
                "S9_COMPONENTS": len(drops), "S9_LANES": {"BLOCKED_UNQUANTIFIED": len(drops)},
                "EXPLANATION": "V3b's slab plates hold no drop or step; S9 registers each blocked (drop depth not "
                               "located)"})
    st = s9_stats([c for c in conc if c["FAMILY"] == "STAIRS"])
    out.append({"DIRECTION": "S9 release with no V3b technical value", "SUBJECT": "stair landing plates",
                "S9_RELEASED_M3": st["S9_RELEASED_M3"], "V3B": "B0031 C-STAIR technical BLOCKED",
                "EXPLANATION": "S8.7's three plates are released; V3b's stair line has no technical quantity"})
    for code, why in (("C-JNT-GF", "inside S9's columns (the column owns the joint, S9-MC1)"),
                      ("C-JNT-1F", "inside S9's columns (S9-MC1)"), ("C-JNT-2F", "inside S9's columns (S9-MC1)"),
                      ("C-BLD-FULL", "owner method; S9 blocked (no printed thickness or projection)"),
                      ("C-POOL-BLD", "pool blinding: S8.2 blocked"),
                      ("C-SWALL", "structural walls: no S9 family (F-01)")):
        x = v3b[code]
        out.append({"DIRECTION": "V3b line with no S9 row of its own", "SUBJECT": f"{x['line_id']} {code}",
                    "V3B": f"{x['status']} {x['qty'] if x['qty'] is not None else '-'} {x['unit']}",
                    "EXPLANATION": why})
    return out


def findings(conc, crosswalk):
    hz = next(x for x in crosswalk if x["PRE_S8_FAMILY"].startswith("CANTILEVER_OR_BEARING_WALL_BAND"))
    return [
        {"FINDING": "F-01", "KIND": "MISSED_OBJECT", "SEVERITY": "MEDIUM",
         "SUBJECT": f"{hz['ELEMENTS']} cantilever / bearing-wall hatch bands ({hz['PLAN_AREA_M2']} m2 in plan)",
         "EVIDENCE": "PRE-S8 02 census HZ-* rows (S7 CLASSIFICATION_BLOCKED; no S1 panel; no owner); V3b C-SWALL "
                     "blocked; S9 has no row",
         "EFFECT_ON_S9": "none on any released figure (no thickness is printed, so no volume could be released); "
                         "the inventory and the missing register are incomplete by these rows",
         "RECOMMENDATION": "a dated S9 correction layer registers them as BLOCKED_UNQUANTIFIED with an owner and an "
                           "RFI (legend: cantilever portion vs bearing wall, thickness); needs approval"},
        {"FINDING": "F-02", "KIND": "AUTHORITY", "SEVERITY": "INFO",
         "SUBJECT": "footings: S9 64.304 vs V3b 64.346 m3",
         "EVIDENCE": "difference = the F9 / FN overlap prism 0.042 m3 exactly",
         "EFFECT_ON_S9": "none", "RECOMMENDATION": "confirm the F9 / FN outlines on site or with the engineer "
                                                   "(S9-RFI-07)"},
        {"FINDING": "F-03", "KIND": "NOT_DECOMPOSABLE", "SEVERITY": "HIGH",
         "SUBJECT": "footing steel: S9 (S4) 3,629.6 kg vs V3b 1,132.674 kg",
         "EVIDENCE": "V3b gives 52 bar sets and no per-set detail; S4 counts every schedule mat",
         "EFFECT_ON_S9": "none (S4 is frozen and independently verified)",
         "RECOMMENDATION": "treat the V3b footing steel as unreliable; do not reuse it"},
        {"FINDING": "F-04", "KIND": "METHOD", "SEVERITY": "INFO",
         "SUBJECT": "slabs / beams / columns: V3b and S9 split the same concrete differently",
         "EVIDENCE": "V3b: plate over beams, beam downstand, column clear + joint; S9: panels between faces, beam full "
                     "depth, column full storey (S9-MC1); see the area reconciliation in 01",
         "EFFECT_ON_S9": "none", "RECOMMENDATION": "compare totals only on one convention; never mix lines"},
    ]


# ------------------------------------------------------------------ write
def _check_text(name, text):
    assert not HYG.search(text), name
    for n in re.findall(r"(?<![0-9.])[0-9]+\.[0-9]+(?![0-9])", text):
        v = float(n)
        assert not any(abs(v - x * k) <= 1e-9 * max(1.0, abs(x * k)) for x in FORBIDDEN for k in (1, 1000)), (name, n)


def main():
    pre = _verify()
    conc, bars, s9sum = s9_views()
    v3b = v3b_lines()
    c01 = concrete_comparison(conc, v3b)
    area = slab_area_reconciliation(conc, v3b)
    c02 = rebar_comparison(bars, s9sum)
    c03 = pre_s8_crosswalk(conc)
    c04 = absent_from_old_boq(conc, v3b, s9sum)
    r5 = json.loads(R5_STAIRS.read_text(encoding="utf-8"))
    c04.append({"DIRECTION": "R5 context", "SUBJECT": "R5 stair register",
                "V3B": f"{len(r5['runs'])} straight tread sets; riser height {r5['riser_height']['state']}",
                "EXPLANATION": "architectural finish register; S9 carries S8.7 unchanged and S8.7C's post-freeze already "
                               "classified R5's riser method (METHOD + MISSED_OBJECT); not comparable as a quantity"})
    c05 = findings(conc, c03)
    v3b_tech_m3 = math.fsum(x["qty"] for x in v3b.values() if x["trade"] == "CONCRETE" and x["qty"] is not None)
    v3b_tech_kg = math.fsum(r["V3B_TECHNICAL_KG"] or 0 for r in c02)
    summ = {"round": "S9_POST_FREEZE", "frozen_manifest_sha256": pre["manifest_sha256"],
            "other_frozen_manifests_verified": pre["other_frozen_manifests"],
            "s9_released": {"concrete_m3": s9sum["released_concrete_m3_total"],
                            "reinforcement_kg": s9sum["released_reinforcement_kg_total"]},
            "v3b_technical": {"concrete_m3": _r(v3b_tech_m3), "reinforcement_kg": _r(v3b_tech_kg)},
            "concrete_groups": len(c01), "rebar_groups": len(c02),
            "concrete_classes": _count(r["CLASS"] for r in c01), "rebar_classes": _count(r["CLASS"] for r in c02),
            "footing_difference_m3": next(r["S9_RELEASED_MINUS_V3B_M3"] for r in c01 if r["GROUP"] == "FOOTINGS"),
            "slab_area_reconciliation": area,
            "pre_s8_missed_objects": [x["PRE_S8_FAMILY"] for x in c03 if x["CLASS"] == "MISSED_OBJECT"],
            "findings": [f["FINDING"] + " " + f["KIND"] for f in c05],
            "release_delta": {"concrete_m3": 0.0, "kg": 0.0}, "rule": RULE}
    texts = {OUT[1]: _csv(c01 + [{"GROUP": f"AREA {a['STOREY']}", **{k: v for k, v in a.items() if k != 'STOREY'}}
                                 for a in area]),
             OUT[2]: _csv(c02), OUT[3]: _csv(c03), OUT[4]: _csv(c04), OUT[5]: _csv(c05),
             OUT[6]: json.dumps(summ, indent=1, sort_keys=True, ensure_ascii=False) + "\n"}
    texts[OUT[0]] = readme(summ, c01, c02, c05, area)
    for name, t in texts.items():
        _check_text(name, t)
    for name in OUT:
        (HERE / name).write_text(texts[name], encoding="utf-8")
    post = _verify()
    assert post == pre
    print(json.dumps({k: summ[k] for k in ("s9_released", "v3b_technical", "concrete_classes", "rebar_classes",
                                            "findings")}, indent=1))


def _count(it):
    out = defaultdict(int)
    for k in it:
        out[k] += 1
    return dict(sorted(out.items()))


def _md(head, rows):
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] +
                     ["| " + " | ".join(_cell(v) for v in r) + " |" for r in rows])


def _n(v):
    return "-" if v is None else f"{v:,.3f}"


def readme(s, c01, c02, c05, area):
    return f"""# S9 post-freeze comparison

Run after the S9 freeze (`16_S9_FREEZE_MANIFEST.json`, sha `{s['frozen_manifest_sha256'][:12]}`). The S9 manifest and
the {s['other_frozen_manifests_verified']} stage manifests it froze over verify before and after. {RULE[0].upper() + RULE[1:]}.

**Release delta: 0 m3, 0 kg.**

## Old Urban V3b BOQ, concrete

S9 releases {_n(s['s9_released']['concrete_m3'])} m3. The V3b technical lines total
{_n(s['v3b_technical']['concrete_m3'])} m3. The two use different conventions and populations, so neither total is a
check on the other; each group is classified below.

{_md(['Group', 'V3b m3', 'S9 released m3', 'S9 conditional point m3', 'Class'],
     [[r['GROUP'], _n(r['V3B_TECHNICAL_M3']), _n(r['S9_RELEASED_M3']), _n(r['S9_CONDITIONAL_POINT_M3']), r['CLASS']]
      for r in c01])}

The footings differ by {_n(s['footing_difference_m3'])} m3, which is exactly the F9 / FN overlap prism S9 deducts.

**Slab area reconciliation.** V3b measures one net plate per floor. S9 measures released panels, plus the areas it
gives to other owners and to the beam and column footprints:

{_md(['Storey', 'V3b plate m2', 'S9 panels m2', 'Other owners m2 (stairs)', 'Beams m2', 'Columns m2', 'Residual m2',
      'Residual if V3b nets the stairs m2'],
     [[a['STOREY'], _n(a['V3B_NET_PLATE_M2']), _n(a['S9_RELEASED_PANELS_M2']),
       f"{_n(a['S9_OTHER_OWNER_PANELS_M2'])} ({_n(a['OF_WHICH_STAIR_ZONES_M2'])})", _n(a['BEAM_FOOTPRINTS_CLEAR_M2']),
       _n(a['COLUMN_FOOTPRINTS_M2']), _n(a['RESIDUAL_M2']), _n(a['RESIDUAL_IF_V3B_NETS_THE_STAIR_ZONES_M2'])]
      for a in area])}

V3b states one net plate per floor and no breakdown, so the residual cannot be decomposed further. It is context for
the METHOD + SCOPE class, not a quantity.

## Old Urban V3b BOQ, reinforcement

S9 releases {_n(s['s9_released']['reinforcement_kg'])} kg. The V3b technical populations total
{_n(s['v3b_technical']['reinforcement_kg'])} kg (hooks outside).

{_md(['Group', 'V3b kg', 'S9 released kg', 'S9 not released (modelled) kg', 'Class'],
     [[r['GROUP'], _n(r['V3B_TECHNICAL_KG']), _n(r['S9_RELEASED_KG']), _n(r.get('S9_NOT_RELEASED_MODELLED_KG')),
       r['CLASS']] for r in c02])}

## Findings

{_md(['Finding', 'Kind', 'Severity', 'Subject', 'Recommendation'],
     [[f['FINDING'], f['KIND'], f['SEVERITY'], f['SUBJECT'], f['RECOMMENDATION']] for f in c05])}

F-01 is a genuine S9 omission: the PRE-S8 census lists cantilever / bearing-wall hatch bands that no stage owns, and
S9 (which may not read the PRE-S8 data registers before its freeze) has no row for them. No released figure changes,
because no thickness is printed. They need a separately approved correction layer.

## Files

| File | Content |
|---|---|
| `01_OLD_BOQ_CONCRETE_COMPARISON.csv` | V3b concrete groups vs S9, plus the slab area reconciliation |
| `02_OLD_BOQ_REBAR_COMPARISON.csv` | V3b reinforcement populations vs S9 |
| `03_PRE_S8_CENSUS_CROSSWALK.csv` | Every PRE-S8 census family against the S9 components |
| `04_ABSENT_FROM_OLD_BOQ.csv` | S9 items with no V3b line, V3b lines with no S9 row, R5 context |
| `05_POST_FREEZE_FINDINGS.csv` | Findings and recommendations |
| `06_POST_FREEZE_SUMMARY.json` | Summary |
"""


if __name__ == "__main__":
    main()
