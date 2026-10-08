"""S7 - restricted elevated slab rebar QTO: the project-basis release of the 476 PRE-S7.1 candidates.

    python3 -I research/alsenan_slab_rebar_s7/build_s7.py

Reads, after hash-checking the eleven freeze manifests (S4 ... D1.2, PRE-S7 and PRE-S7.1): the frozen PRE-S7.1
registers (candidates, blockers, readiness, strips, transfers, splits, conflicts) and two frozen PRE-S7 registers (the
panel census, for areas and classes, and the opening register, for voids). The frozen PRE-S7.1 code is re-run in
memory (its build(), nothing written) only to recover its local bar strips at full precision; every in-memory register
must be byte-identical to the frozen one, so S7 measures exactly the PRE-S7.1 geometry. Nothing else is opened: no
reference quantity, no donor, no old estimate, no steel-per-volume profile.

Scope never widens: only the 476 candidates carry kg. For each, from its own local bar strips:
    L_total = RATE x DENSITY_FRACTION x sum(strip width x local run)        (equivalent bar length, m)
    kg      = L_total x D^2 / 162
The equivalent bar count (RATE x DENSITY_FRACTION x WIDTH) is never rounded; the physical BBS count stays UNRESOLVED.
Every other PRE-S7.1 item (blocked, transferred to S8, source conflict) and every opening trim / diagonal bar that has
no source is listed with no kg. The one total is RESTRICTED_S7_PROJECT_BASIS_KG, never a final slab total.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import delta_release as DR  # noqa: E402
from engine.source import slab_rebar_qto as S7  # noqa: E402

ROUND = "S7"
POLICY = "S7_RESTRICTED_SLAB_REBAR_QTO_V1"
BASELINE_HEAD = "ac7a477"
R = ROOT / "research"
PRE = R / "alsenan_slab_rebar_pre_s7"
P71 = R / "alsenan_slab_rebar_pre_s7_1"
MANIFESTS = {"S4": R / "alsenan_footing_rebar_s4" / "S4_FREEZE_MANIFEST.json",
             "S4.1": R / "alsenan_footing_rebar_s4_1" / "S4_1_FREEZE_MANIFEST.json",
             "S5": R / "alsenan_ground_system_rebar_s5" / "S5_FREEZE_MANIFEST.json",
             "S6": R / "alsenan_superstructure_beam_rebar_s6" / "S6_FREEZE_MANIFEST.json",
             "S6.1": R / "alsenan_superstructure_beam_rebar_s6_1" / "S6_1_FREEZE_MANIFEST.json",
             "S5.1": R / "alsenan_ground_system_rebar_s5_1" / "S5_1_FREEZE_MANIFEST.json",
             "AD1": R / "ad1_authority_decisions" / "AD1_FREEZE_MANIFEST.json",
             "D1.1": R / "d1_1_stirrup_authority_audit" / "D1_1_FREEZE_MANIFEST.json",
             "D1.2": R / "d1_2_footing_cover_audit" / "D1_2_FREEZE_MANIFEST.json",
             "PRE-S7": PRE / "PRE_S7_FREEZE_MANIFEST.json",
             "PRE-S7.1": P71 / "PRE_S7_1_FREEZE_MANIFEST.json"}
P71_FILES = ["00_README.md", "01_AD2_DECISIONS.json", "02_OWNERSHIP_TRANSFERS.csv", "03_RATE_QTO_REGISTER.csv",
             "04_50_PERCENT_CURTAILMENT_REGISTER.csv", "05_TOP_RULE_IDENTITY.csv", "06_SUPPORT_MISMATCH_SPLITS.csv",
             "07_LOCAL_BAR_STRIPS.csv", "08_UPDATED_COMPONENT_READINESS.csv", "09_REMAINING_CONFLICTS.csv",
             "10_REMAINING_BLOCKERS.csv", "11_S7_RELEASE_CANDIDATES.csv", "12_PROVENANCE.jsonl",
             "PRE_S7_1_SUMMARY.json"]
PRE_FILES = ["01_SLAB_PANEL_CENSUS.csv", "08_OPENING_REGISTER.csv"]
CODE = ["engine/source/slab_rebar_qto.py", "engine/source/rebar_unit_mass.py", "engine/source/delta_release.py",
        "engine/source/slab_qto_authority.py", "engine/source/slab_rebar_readiness.py",
        "engine/source/structural_census.py", "research/external_engine_lab/alsenan_structural_s1.py",
        "research/alsenan_slab_rebar_pre_s7_1/build_pre_s7_1.py", "research/alsenan_slab_rebar_s7/build_s7.py"]
INPUTS = [str(p.relative_to(ROOT)) for p in MANIFESTS.values()] + \
    [f"research/alsenan_slab_rebar_pre_s7_1/{f}" for f in P71_FILES] + \
    [f"research/alsenan_slab_rebar_pre_s7/{f}" for f in PRE_FILES]
DECISION_RECORDS = ["research/alsenan_slab_rebar_pre_s7_1/01_AD2_DECISIONS.json",
                    "research/alsenan_slab_rebar_pre_s7_1/05_TOP_RULE_IDENTITY.csv",
                    "research/alsenan_slab_rebar_pre_s7_1/04_50_PERCENT_CURTAILMENT_REGISTER.csv"]
CANDIDATE_REGISTERS = ["research/alsenan_slab_rebar_pre_s7_1/11_S7_RELEASE_CANDIDATES.csv",
                       "research/alsenan_slab_rebar_pre_s7_1/10_REMAINING_BLOCKERS.csv",
                       "research/alsenan_slab_rebar_pre_s7_1/08_UPDATED_COMPONENT_READINESS.csv"]
OUTPUTS = ["00_README.md", "01_S7_RELEASE_ITEMS.csv", "02_S7_BLOCKED_ITEMS.csv", "03_S7_COMPONENT_SUMMARY.csv",
           "04_S7_BAR_RUNS.csv", "05_S7_PANEL_SUMMARY.csv", "06_S7_SUPPORT_SUMMARY.csv", "07_S7_FLOOR_SUMMARY.csv",
           "08_S7_DIAMETER_SUMMARY.csv", "09_S7_PROJECT_SUMMARY.json", "10_S7_PROVENANCE.jsonl",
           "11_S7_1_CANDIDATES.csv"]
MANIFEST_NAME = "12_S7_FREEZE_MANIFEST.json"
CANDIDATE_POPULATION = 476
CANDIDATE_COMPONENTS = 309
FLOORS = ("GF_ROOF_SLAB", "1F_ROOF_SLAB", "2F_ROOF_SLAB")
FLOOR_LABEL = {"GF_ROOF_SLAB": "GF", "1F_ROOF_SLAB": "1F", "2F_ROOF_SLAB": "2F"}
BOTTOM_RULE = "P15-BOT-STOP-0.125L"
NOTE2_RULE = "P4-6-NOTE-2-TOP-OVER-BEAMS"
OVERRIDDEN_TOP_RULES = ("P15-TOP-NONCONT-0.25L1", "P15-TOP-CONT-0.30Lmax", "P15-TOP-EXTEND-50PCT")
OVERLAP_TOL_MM = 0.5            # drawing precision (PRE-S7.1 SPAN_TOL_MM)
REL_TOL_REGISTER = 1e-5         # the frozen registers print 6 significant digits
ROLE = {"BOTTOM_IN_PANEL": "BOTTOM_IN_PANEL", "BOTTOM_IN_PANEL_CONTINUING": "BOTTOM_CONTINUING_50",
        "BOTTOM_IN_PANEL_CURTAILED": "BOTTOM_CURTAILED_50", "BOTTOM_SUPPORT_CROSSING": "BOTTOM_SUPPORT_CROSSING",
        "TOP_EXTENSION": "TOP_OVER_SUPPORT_EXTENSION", "TOP_SUPPORT_CROSSING": "TOP_SUPPORT_CROSSING"}
BOTTOM_ROLES = ("BOTTOM_IN_PANEL", "BOTTOM_CONTINUING_50", "BOTTOM_CURTAILED_50", "BOTTOM_SUPPORT_CROSSING")
TOP_ROLES = ("TOP_OVER_SUPPORT_EXTENSION", "TOP_SUPPORT_CROSSING")


class Stop(SystemExit):
    pass


def check(cond, what):
    if not cond:
        raise Stop(f"S7 STOP: {what}")


# ------------------------------------------------------------------ io helpers
def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _js(v):
    return json.loads(v) if v not in ("", None) else None


def _f(v):
    return float(v) if v not in ("", None) else None


def _lst(v):
    """A list field from the frozen CSV (JSON text) or from the in-memory PRE-S7.1 item (a list)."""
    if v in ("", None):
        return []
    return list(v) if isinstance(v, (list, tuple)) else json.loads(v)


def _full(v):
    """A quantity written without rounding (to 9 decimals: far below any drawing precision)."""
    if v is None:
        return None
    s = f"{float(v):.9f}".rstrip("0").rstrip(".")
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


def _csv(name, rows, fields):
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


# ------------------------------------------------------------------ frozen inputs
def verify_inputs():
    frozen = {k: DR.verify_frozen(m, ROOT) for k, m in MANIFESTS.items()}
    out71 = _j(MANIFESTS["PRE-S7.1"])["outputs"]
    for f in P71_FILES:
        check(out71.get(f) == _sha(P71 / f), f"PRE-S7.1 {f} is the frozen output")
    in71 = _j(MANIFESTS["PRE-S7.1"])["inputs"]
    out_pre = _j(MANIFESTS["PRE-S7"])["outputs"]
    for f in PRE_FILES:
        check(out_pre.get(f) == _sha(PRE / f), f"PRE-S7 {f} is the frozen output")
    check(in71.get("research/alsenan_slab_rebar_pre_s7/01_SLAB_PANEL_CENSUS.csv") == _sha(PRE / PRE_FILES[0]),
          "PRE-S7.1 was built on this census")
    return frozen


def load_pre71():
    spec = importlib.util.spec_from_file_location("build_pre_s7_1", P71 / "build_pre_s7_1.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def reproduce(M, B):
    """The in-memory PRE-S7.1 registers must be byte-identical to the frozen ones."""
    out71 = _j(MANIFESTS["PRE-S7.1"])["outputs"]
    regs = {"02_OWNERSHIP_TRANSFERS.csv": (B["transfers"], ["TRANSFER_ID", "object_id", "kind", "from_stage",
                                                            "to_stage", "region", "reason", "state", "quantity_lost",
                                                            "source_conflict_preserved"]),
            "03_RATE_QTO_REGISTER.csv": (B["rate_rows"], M.ITEM_FIELDS),
            "06_SUPPORT_MISMATCH_SPLITS.csv": (B["split_rows"], list(B["split_rows"][0])),
            "07_LOCAL_BAR_STRIPS.csv": (B["strip_rows"], list(B["strip_rows"][0])),
            "08_UPDATED_COMPONENT_READINESS.csv": (B["readiness"], list(B["readiness"][0])),
            "10_REMAINING_BLOCKERS.csv": (B["blockers"], M.ITEM_FIELDS),
            "11_S7_RELEASE_CANDIDATES.csv": (B["cands"], M.ITEM_FIELDS)}
    for name, (rows, fields) in regs.items():
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow({k: M._cell(r.get(k)) for k in fields})
        check(hashlib.sha256(buf.getvalue().encode("utf-8")).hexdigest() == out71[name],
              f"in-memory PRE-S7.1 {name} is the frozen register")
    return sorted(regs)


# ------------------------------------------------------------------ strip geometry
def _region(x):
    return (x["t0"], x["t1"], x["s_start"][0], x["s_start"][1], x["s_end"][0], x["s_end"][1])


def _ext_region(x, k):
    t0, t1, a0, a1, b0, b1 = _region(x)
    if k == 0:                                   # from the start face into the panel
        return (t0, t1, a0, a1, a0 + x["L0"] / 3.0, a1 + x["L1"] / 3.0)
    return (t0, t1, b0 - x["L0"] / 3.0, b1 - x["L1"] / 3.0, b0, b1)


def _cross_region(x, k, gap):
    t0, t1, a0, a1, b0, b1 = _region(x)
    if k == 0:                                   # outward from the start face, over the support
        return (t0, t1, a0 - gap[0], a1 - gap[1], a0, a1)
    return (t0, t1, b0, b1, b0 + gap[0], b1 + gap[1])


def _boundary(x, k):
    ref = x[("start_edge_ref", "end_edge_ref")[k]]
    cond = x["end_classes"][k]
    sup = ref.get("support") or ref["kind"]
    nb = ref.get("neighbour")
    return f"{sup} ({cond}{'; beyond: ' + nb if nb else ''})"


def derive_contributions(M, B):
    """Re-derive, strip by strip, what each released PRE-S7.1 item measures (independently of its aggregation):
    in-panel bottom portions, bottom crossings of continuous supports, top extensions and top crossings."""
    Q, SR = M.Q, M.SR
    strips, bfam, sup = B["strips"], B["bfam"], B["sup"]
    side_class, sunken = B["side_class"], B["sunken"]
    stop = M.STOP_FRACTION
    out = defaultdict(list)
    for (pid, d), st in sorted(strips.items()):
        f = bfam.get((pid, d))
        fam_ok = bool(f) and f["state"] == "RESOLVED"
        split = fam_ok and "curt" in f["parents"] and "cont" in f["parents"]
        for x in st:
            check(abs((x["s_end"][0] - x["s_start"][0]) - x["L0"]) <= 1e-6 and
                  abs((x["s_end"][1] - x["s_start"][1]) - x["L1"]) <= 1e-6, f"strip run = face to face {x['id']}")
            mean = 0.5 * (x["L0"] + x["L1"])
            ends = x["end_classes"]
            if fam_ok:
                for it in Q.bottom_strip_items(x["L0"], x["L1"], x["width"], *ends, stop_fraction=stop):
                    if it["lane_hint"] != "RELEASE":
                        continue
                    halves = [(it["item"], it["density_fraction"], it["run_factor"])]
                    if split and it["item"] == "IN_PANEL":
                        halves = [("IN_PANEL_CONTINUING", 0.5, 1.0), ("IN_PANEL_CURTAILED", 0.5, 1.0)]
                    for kind, frac, kf in halves:
                        curt = kind == "IN_PANEL_CURTAILED"
                        n_stop = sum(e in Q._CURTAIL or e in Q._UNCERTAIN for e in ends) if curt and kf < 1.0 else 0
                        check(abs(kf - (1.0 - stop * n_stop)) <= 1e-12, f"curtailment factor {x['id']}")
                        out[("B", pid, d, "BOTTOM_" + kind, frac)].append({
                            "strip": x, "end": None, "frac": frac, "width": x["width"], "run": kf * mean,
                            "base": mean, "deduction": (1.0 - kf) * mean, "extension": 0.0, "n_stop": n_stop,
                            "unresolved_stop_ends": sum(e in Q._UNCERTAIN for e in ends) if n_stop else 0,
                            "region": _region(x), "relation": "IN_PANEL face to face along the local bar line"
                            + (f" less 0.125 x L at {n_stop} stopping end(s)" if n_stop else "")})
            for k, end in enumerate(("start_edge_ref", "end_edge_ref")):
                ref, ec = x[end], ends[k]
                nb = ref.get("neighbour")
                # bottom crossing of a continuous support (same specification), from the lower-id face only
                if ec == Q.END_CONTINUOUS_RUN and pid < nb and ref.get("gap"):
                    g = ref["gap"]
                    out[("BX", ref["support"], f"{pid}|{nb}", d)].append({
                        "strip": x, "end": k, "frac": 0.5, "width": x["width"], "run": 0.5 * (g[0] + g[1]),
                        "base": 0.5 * (g[0] + g[1]), "deduction": 0.0, "extension": 0.0, "n_stop": 0,
                        "unresolved_stop_ends": 0, "region": _cross_region(x, k, g),
                        "relation": f"CROSSING over {ref['support']} from {pid} to {nb} (the continuing half)"})
                # top over supports (plan note 2): square bar lines meeting a beam support that they cross
                sid = ref.get("support")
                if ref["kind"] != "SUPPORT" or not ref["square"] or sup[sid]["BARS_CROSSING"] != d or \
                        ref.get("support_kind") != "BEAM" or sup[sid]["SUPPORT_KIND"] != "BEAM":
                    continue
                out[("TE", sid, pid)].append({
                    "strip": x, "end": k, "frac": 1.0, "width": x["width"], "run": 0.0, "base": mean,
                    "deduction": 0.0, "extension": mean / 3.0, "n_stop": 0, "unresolved_stop_ends": 0,
                    "region": _ext_region(x, k), "relation": f"EXTENSION from the face of {sid} into {pid} "
                                                             "(1/3 x local clear span)"})
                oc = side_class(nb)
                step = oc == "SLAB_IN_SCOPE" and ((pid in sunken) != (nb in sunken))
                cont = Q.edge_continuity(other_side=oc, support_kind="BEAM", level_step=step)
                if cont["state"] == SR.CONTINUOUS and pid < nb and ref.get("gap"):
                    g = ref["gap"]
                    out[("TX", sid, f"{pid}|{nb}")].append({
                        "strip": x, "end": k, "frac": 1.0, "width": x["width"], "run": 0.5 * (g[0] + g[1]),
                        "base": 0.5 * (g[0] + g[1]), "deduction": 0.0, "extension": 0.0, "n_stop": 0,
                        "unresolved_stop_ends": 0, "region": _cross_region(x, k, g),
                        "relation": f"CROSSING over {sid} from {pid} to {nb} (counted once, lower-id face)"})
    return out


def cand_key(c):
    it = c["ITEM"]
    if it in ("BOTTOM_IN_PANEL", "BOTTOM_IN_PANEL_CONTINUING", "BOTTOM_IN_PANEL_CURTAILED"):
        return ("B", c["OWNER"], c["DIRECTION"], it, float(c["DENSITY_FRACTION"]))
    if it == "BOTTOM_SUPPORT_CROSSING":
        return ("BX", c["SUPPORT_ID"], c["SIDE_PANEL"], c["DIRECTION"])
    if it in ("TOP_EXTENSION", "TOP_SUPPORT_CROSSING"):
        return ({"TOP_EXTENSION": "TE", "TOP_SUPPORT_CROSSING": "TX"}[it], c["SUPPORT_ID"], c["SIDE_PANEL"])
    raise Stop(f"S7 STOP: candidate kind {it} has no S7 measurement")


# ------------------------------------------------------------------ authorities of one released item
def authorities(c, role, contribs, B):
    rules = B["rules"]
    rect = B["rect"]
    pid = c["OWNER"] if role in ("BOTTOM_IN_PANEL", "BOTTOM_CONTINUING_50", "BOTTOM_CURTAILED_50") else \
        c["SIDE_PANEL"] if role == "TOP_OVER_SUPPORT_EXTENSION" else None
    irregular = pid is not None and not rect[pid]
    line = B["Q"].URBAN_LOCAL_BAR_LINE_RULE
    geo = S7.PROJECT_GEOMETRY + (f" + {S7.URBAN_OWNER_MEASUREMENT_RULE} ({line}: local run along each bar line)"
                                 if irregular else " (rectangular: local run = clear span)")
    urban = [f"URBAN_RATE_DENSITY (AD2-D02: equivalent count = rate x density x width, unrounded)"]
    if irregular:
        urban.append(f"{line} (AD2-D14)")
    src_rules, ad2 = [], _lst(c["AUTHORITY"])
    a = {"SOURCE_RATIO": None, "SOURCE_RATIO_RULE": None, "SOURCE_RATIO_AUTHORITY": None,
         "SPAN_BASIS": None, "SPAN_BASIS_AUTHORITY": None, "MEASUREMENT_ORIGIN": None,
         "MEASUREMENT_ORIGIN_AUTHORITY": None}
    if role.startswith("BOTTOM"):
        fam = B["bfam"][(c["OWNER"], c["DIRECTION"])] if role != "BOTTOM_SUPPORT_CROSSING" else \
            B["bfam"][(c["SIDE_PANEL"].split("|")[0], c["DIRECTION"])]
        tok = B["tok"].get(fam["token"], {})
        src_rules.append(f"token {fam['token']} ({tok.get('RAW')})")
        count = (f"{S7.PROJECT_SOURCE}: plan callout {tok.get('RAW')} on {fam['panel']} -> {c['RATE_PER_M']} "
                 f"bars/m of Ø{c['DIA_MM']}; equivalent count by URBAN_RATE_DENSITY (AD2-D02); "
                 f"PHYSICAL_BBS_COUNT {S7.UNRESOLVED}")
    else:
        src_rules.append(NOTE2_RULE)
        count = (f"{S7.PROJECT_SOURCE}: plan note 2 (5Ø10/m top steel over beams, both directions) -> "
                 f"{c['RATE_PER_M']} bars/m of Ø{c['DIA_MM']}; equivalent count by URBAN_RATE_DENSITY (AD2-D02); "
                 f"PHYSICAL_BBS_COUNT {S7.UNRESOLVED}")
    frac = float(c["DENSITY_FRACTION"])
    if role in ("BOTTOM_CONTINUING_50", "BOTTOM_CURTAILED_50", "BOTTOM_SUPPORT_CROSSING"):
        src_rules.append(BOTTOM_RULE)
        dens = (f"{S7.PROJECT_SOURCE}: {BOTTOM_RULE} 'STOP 50% OF BOT. REINF. BALANCE CONTINUOUS' -> {frac:g} "
                "(AD2-D04 exact 0.5 / 0.5 density; which physical bars stop stays a BBS question)")
    else:
        dens = f"{S7.PROJECT_SOURCE}: full callout density {frac:g} (no 50 % rule split on this item)"
    if role == "BOTTOM_IN_PANEL" or role == "BOTTOM_CONTINUING_50":
        length = f"{geo}; face to face of the supports (the portion beyond each face is a blocked complement)"
        a.update(SPAN_BASIS="LOCAL_CLEAR_SPAN (face to face along each bar line)",
                 SPAN_BASIS_AUTHORITY=S7.URBAN_OWNER_MEASUREMENT_RULE if irregular else S7.PROJECT_GEOMETRY,
                 MEASUREMENT_ORIGIN="SUPPORT_FACE", MEASUREMENT_ORIGIN_AUTHORITY=S7.PROJECT_GEOMETRY)
    elif role == "BOTTOM_CURTAILED_50":
        r = rules[BOTTOM_RULE]
        extra = []
        if any(x["unresolved_stop_ends"] for x in contribs):
            extra.append("AD2-D15 (a continuity-unresolved end stops the curtailed half as a continuous end would; "
                         "its 0.125 L zone is a blocked complement)")
            urban.append(extra[0])
        ca = S7.curtailment_authority(ratio_rule=BOTTOM_RULE, span_stated_by_source=r["SPAN_DEFINITION"] ==
                                      "CLEAR_SPAN", origin_stated_by_source=r["MEASUREMENT_ORIGIN"] ==
                                      "FACE_OF_SUPPORT", local_bar_line_rule=line if irregular else None,
                                      extra_conventions=extra)
        a.update({k: ca[k] for k in a})
        length = (f"{geo}; less {S7.PROJECT_SOURCE} {BOTTOM_RULE} 0.125 x L (L = clear span, from the face of "
                  "support) at each continuous end" + (" and, under AD2-D15, each continuity-unresolved end"
                                                       if extra else ""))
    elif role in ("BOTTOM_SUPPORT_CROSSING", "TOP_SUPPORT_CROSSING"):
        length = (f"{S7.PROJECT_GEOMETRY}: over the support between the two panel faces along each bar line "
                  "(the far face found beyond each strip end, AD2-D15)")
        a.update(SPAN_BASIS="SUPPORT_GAP (face to face over the support)", SPAN_BASIS_AUTHORITY=S7.PROJECT_GEOMETRY,
                 MEASUREMENT_ORIGIN="SUPPORT_FACE", MEASUREMENT_ORIGIN_AUTHORITY=S7.PROJECT_GEOMETRY)
    else:                                                     # TOP_OVER_SUPPORT_EXTENSION
        n2 = rules[NOTE2_RULE]
        ta = S7.top_extent_authority(ratio_rule=NOTE2_RULE, origin_stated_by_source=bool(n2["MEASUREMENT_ORIGIN"]),
                                     span_stated_by_source=n2["SPAN_DEFINITION"] not in ("", "L_UNDEFINED"),
                                     urban_rule=B["Q"].URBAN_TOP_EXTENT_RULE)
        a.update({k: ta[k] for k in a})
        urban += ta["URBAN_CONVENTIONS"]
        length = (f"{S7.PROJECT_SOURCE} ratio 1/3 ({NOTE2_RULE}: 'length one third of the span'); "
                  f"{S7.URBAN_OWNER_MEASUREMENT_RULE} {B['Q'].URBAN_TOP_EXTENT_RULE}: measured from the support face "
                  f"into the clear span of {pid} (note 2 does not state the origin, the span or total-vs-each-side)"
                  + (f"; local L by {line}" if irregular else ""))
    return {"COUNT_AUTHORITY": count, "DENSITY_AUTHORITY": dens, "LENGTH_AUTHORITY": length,
            "QUANTITY_AUTHORITY": (f"{S7.PROJECT_BASIS_QTO}: rate density over the frozen PRE-S7.1 local bar strips; "
                                   "a lower bound of the physical steel (every blocked portion is excluded, not "
                                   "zero); not a bar-by-bar BBS"),
            "SOURCE_RULE_IDS": src_rules, "URBAN_RULE_IDS": urban, "AD2_DECISIONS": ad2, **a}


# ------------------------------------------------------------------ blocked-item classification
def blocked_category(i):
    it, qs = i["ITEM"], set(_lst(i.get("QUESTIONS")))
    if i["LANE"] == "TRANSFERRED_S8":
        return "S8_SPECIAL_STRUCTURE"
    if it == "TEMPERATURE":
        return "TEMPERATURE"
    if it in ("BOTTOM_END_ANCHORAGE", "TOP_END_ANCHORAGE"):
        return "ANCHORAGE_END_COVER"
    if it in ("BOTTOM_TRANSITION", "BOTTOM_RUN_LAP_SPLICE"):
        return "TRANSITION_LAP_SPLICE"
    if it in ("SUNKEN_STEP_VERTICAL_REBAR", "SUNKEN_EDGE_EXTRA", "LEVEL_CHANGE_DETAIL"):
        return "SUNKEN_EXTRA"
    if it == "TOP_AT_UNRECORDED_EDGE":
        return "EDGE_WITHOUT_SUPPORT_RECORD"
    if it in ("TOP_LOCAL_OVERRIDE_GROUP", "CORNER_GROUP"):
        return "EXPLICIT_COUNT_LENGTH_BLOCKED"
    if it == "FAMILY_BLOCKED":
        return "SOURCE_CONFLICT_FAMILY"
    if "Q-OBLIQUE" in qs:
        return "OBLIQUE_SUPPORT"
    if "Q-HATCH" in qs:
        return "BEARING_WALL_CANDIDATE_SUPPORT"
    if "Q-SUNKEN" in qs:
        return "SUNKEN_LEVEL_CHANGE_CONTINUITY"
    return "CONTINUITY_UNRESOLVED"


def blocked_lane(i):
    if i["LANE"] == "TRANSFERRED_S8":
        return S7.EXCLUDED_SPECIAL_STRUCTURE
    if i["ITEM"] == "FAMILY_BLOCKED":
        return S7.SOURCE_CONFLICT
    return S7.BLOCKED_UNQUANTIFIED


def conflict_ref(i):
    blk = " ".join(_lst(i.get("BLOCKERS")))
    if i["ITEM"] == "FAMILY_BLOCKED":
        return "C-04 COUNT_NOTATION_CONFLICT" if "COUNT_NOTATION" in blk else "C-03 MULTIPLE_CANDIDATE_BINDINGS"
    if "40 CL." in blk:
        return "C-06 COVER_DIMENSION_BINDING (no quantity depends on it)"
    if i.get("S8_REGION") == "STAIR_LIGHTWELL_REGION" or i["OWNER"] == "SP-GF_ROOF_SLAB-21":
        return "C-01 PANEL_VOID_CONFLICT (preserved in S8)"
    return None


# ------------------------------------------------------------------ build
def build():
    frozen = verify_inputs()
    M = load_pre71()
    B = M.build()
    B["Q"] = M.Q
    reproduced = reproduce(M, B)
    cands = _rows(P71 / "11_S7_RELEASE_CANDIDATES.csv")
    blockers71 = _rows(P71 / "10_REMAINING_BLOCKERS.csv")
    readiness = _rows(P71 / "08_UPDATED_COMPONENT_READINESS.csv")
    census = {r["SLAB_PANEL_ID"]: r for r in _rows(PRE / "01_SLAB_PANEL_CENSUS.csv")}
    openings = _rows(PRE / "08_OPENING_REGISTER.csv")
    check(len(cands) == CANDIDATE_POPULATION, f"candidate population {len(cands)}")
    check([c["QTO_ITEM_ID"] for c in cands] == [i["QTO_ITEM_ID"] for i in B["cands"]], "candidate ids")
    check(all(c["LANE"] == S7.PROJECT_BASIS_QTO for c in cands), "every candidate is PROJECT_BASIS_QTO")
    cand_comps = sorted({c["PARENT_COMPONENT_ID"] for c in cands})
    check(len(cand_comps) == CANDIDATE_COMPONENTS, f"candidate components {len(cand_comps)}")
    items71 = B["items"]
    non_cand = [i for i in items71 if i["LANE"] != S7.PROJECT_BASIS_QTO]
    check(len(non_cand) == len(blockers71) + sum(i["LANE"] == "TRANSFERRED_S8" for i in items71),
          "every non-candidate item is blocked or transferred")

    contrib = derive_contributions(M, B)
    keys = [cand_key(c) for c in cands]
    check(not S7.duplicates(keys), f"one candidate per measured key {S7.duplicates(keys)}")
    hatch, explicit = B["hatch_sids"], set(B["explicit"])
    for k in contrib:
        if k not in set(keys):
            check(k[0] in ("TE", "TX") and k[1] in hatch | explicit,
                  f"a measured portion with no candidate must be a blocked hatch-band / override support: {k}")
    s8_panels = set(B["region"]) | {p for p, r in census.items() if r["SCOPE"] != "IN_SCOPE_S7"}

    # ---------------------------------------------------- 01 release items + 04 bar runs
    rel, runs, blocked_cands = [], [], []
    by_comp_blocked = defaultdict(list)
    for i in blockers71:
        by_comp_blocked[i["PARENT_COMPONENT_ID"]].append(i["QTO_ITEM_ID"])
    for n, (c, key) in enumerate(zip(cands, keys), 1):
        role = ROLE[c["ITEM"]]
        cs = contrib.get(key, [])
        rate, frac, dia = float(c["RATE_PER_M"]), float(c["DENSITY_FRACTION"]), int(c["DIA_MM"])
        problems = []
        if not cs:
            problems.append("NO_STRIP_FOUND_FOR_CANDIDATE")
        if any(abs(x["frac"] - frac) > 1e-12 for x in cs):
            problems.append("DENSITY_FRACTION_MISMATCH")
        w_sum = math.fsum(x["width"] for x in cs)
        integ = math.fsum(x["width"] * (x["run"] + x["extension"]) for x in cs) / 1e6
        if abs(w_sum - float(c["DISTRIBUTION_WIDTH_MM"])) > 1e-6:
            problems.append("WIDTH_DOES_NOT_RECONCILE_TO_PRE_S7_1")
        if abs(integ - float(c["RUN_INTEGRAL_M2"])) > REL_TOL_REGISTER * max(integ, 1.0):
            problems.append("RUN_INTEGRAL_DOES_NOT_RECONCILE_TO_PRE_S7_1")
        if len(cs) != int(c["STRIPS"] or len(cs)):
            problems.append("STRIP_COUNT_DOES_NOT_RECONCILE")
        if problems:                                   # S7 never repairs a candidate: it blocks it
            blocked_cands.append({"c": c, "why": problems})
            continue
        q = S7.rate_strip_length(rate, [(x["width"], x["run"] + x["extension"]) for x in cs], fraction=frac)
        m = S7.mass(dia, q["length_m"])
        check(abs(q["equivalent_count"] - float(c["EQUIVALENT_BAR_COUNT"])) <= 1e-6, f"equivalent count {key}")
        check(abs(q["length_m"] - rate * frac * float(c["RUN_INTEGRAL_M2"])) <=
              REL_TOL_REGISTER * max(q["length_m"], 1.0), f"length vs frozen integral {key}")
        sid = c["SUPPORT_ID"] or None
        owner_kind = "PANEL" if role in ("BOTTOM_IN_PANEL", "BOTTOM_CONTINUING_50", "BOTTOM_CURTAILED_50") \
            else "SUPPORT"
        panel = c["OWNER"] if owner_kind == "PANEL" else c["SIDE_PANEL"]
        Wm = q["width_m"]
        mean_of = (lambda f_: math.fsum(x["width"] * x[f_] for x in cs) / w_sum / 1000.0)
        base, run_m, ext_m, ded_m = mean_of("base"), mean_of("run"), mean_of("extension"), mean_of("deduction")
        au = authorities(c, role, cs, B)
        sid_ = f"S7-{n:04d}"
        bar_run = c["RUN_ID"] or f"TOP:{sid}:{c['SIDE_PANEL']}:{c['DIRECTION']}"
        um = m["unit_mass_kg_m"]
        row = {
            "S7_ITEM_ID": sid_, "PRE_S7_1_CANDIDATE_ID": c["QTO_ITEM_ID"], "COMPONENT_ID": c["PARENT_COMPONENT_ID"],
            "OWNER": c["OWNER"], "OWNER_KIND": owner_kind, "PANEL_ID": panel, "SUPPORT_ID": sid,
            "BAR_RUN_ID": bar_run, "FLOOR": c["FLOOR"], "BAR_ROLE": role, "LAYER": "BOTTOM" if
            role in BOTTOM_ROLES else "TOP", "DIRECTION": c["DIRECTION"], "DIAMETER_MM": dia, "RATE_PER_M": rate,
            "EXPLICIT_COUNT": None, "DENSITY_FRACTION": frac, "TRANSVERSE_WIDTH_M": Wm,
            "EQUIVALENT_BAR_COUNT": q["equivalent_count"], "PHYSICAL_BBS_COUNT": S7.UNRESOLVED,
            "LOCAL_CLEAR_SPAN_MEAN_M": base if role not in ("BOTTOM_SUPPORT_CROSSING", "TOP_SUPPORT_CROSSING")
            else None, "CURTAILMENT_DEDUCTION_M": ded_m if role == "BOTTOM_CURTAILED_50" else None,
            "RUN_LENGTH_M": run_m, "EXTENSION_LENGTH_M": ext_m,
            "CALCULATED_EXTENT_M": ded_m if role == "BOTTOM_CURTAILED_50" else ext_m if
            role == "TOP_OVER_SUPPORT_EXTENSION" else None,
            "EQUIVALENT_TOTAL_LENGTH_M": q["length_m"], "UNIT_MASS_KG_M": um, "KG": m["kg"],
            "S7_LANE": S7.s7_lane(count_basis=S7.COUNT_RATE_DENSITY,
                                  length_authorities=[S7.PROJECT_GEOMETRY, S7.PROJECT_SOURCE]),
            "QUANTITY_AUTHORITY": au["QUANTITY_AUTHORITY"], "LENGTH_AUTHORITY": au["LENGTH_AUTHORITY"],
            "COUNT_AUTHORITY": au["COUNT_AUTHORITY"], "DENSITY_AUTHORITY": au["DENSITY_AUTHORITY"],
            "SOURCE_RATIO": au["SOURCE_RATIO"], "SOURCE_RATIO_RULE": au["SOURCE_RATIO_RULE"],
            "SOURCE_RATIO_AUTHORITY": au["SOURCE_RATIO_AUTHORITY"], "SPAN_BASIS": au["SPAN_BASIS"],
            "SPAN_BASIS_AUTHORITY": au["SPAN_BASIS_AUTHORITY"], "MEASUREMENT_ORIGIN": au["MEASUREMENT_ORIGIN"],
            "MEASUREMENT_ORIGIN_AUTHORITY": au["MEASUREMENT_ORIGIN_AUTHORITY"],
            "LAYER_AUTHORITY": c["LAYER_AUTHORITY"], "SOURCE_RULE_IDS": au["SOURCE_RULE_IDS"],
            "URBAN_RULE_IDS": au["URBAN_RULE_IDS"], "AD2_DECISIONS": au["AD2_DECISIONS"],
            "BLOCKED_COMPLEMENTS": sorted(by_comp_blocked.get(c["PARENT_COMPONENT_ID"], [])),
            "STRIPS": len(cs), "SUNKEN_PANEL": panel in B["sunken"] if owner_kind == "PANEL" else
            any(p in B["sunken"] for p in str(panel).split("|")),
            "IRREGULAR_PANEL": owner_kind == "PANEL" and not B["rect"][panel],
            "FORMULA": (f"{rate:g} /m x {frac:g} x {_full(Wm)} m x {_full(run_m + ext_m)} m = "
                        f"{_full(q['length_m'])} m; x {dia}^2/162 = {_full(um)} kg/m -> {_full(m['kg'])} kg"),
            "PROVENANCE": (f"PRE-S7.1 11_S7_RELEASE_CANDIDATES.csv {c['QTO_ITEM_ID']} (manifest "
                           f"{frozen['PRE-S7.1']['manifest_sha256'][:12]}); {len(cs)} local bar strips in "
                           "04_S7_BAR_RUNS.csv")}
        rel.append(row)
        for k_, x in enumerate(cs, 1):
            st = x["strip"]
            con = x["width"] * (x["run"] + x["extension"]) / 1e6
            runs.append({
                "BAR_RUN_ROW_ID": f"{sid_}-{k_:03d}", "S7_ITEM_ID": sid_, "PRE_S7_1_CANDIDATE_ID": c["QTO_ITEM_ID"],
                "BAR_RUN_ID": bar_run, "BAR_ROLE": role, "FLOOR": c["FLOOR"], "PANEL_ID": st["panel"],
                "DIRECTION": st["direction"], "STRIP_ID": st["id"], "STRIP_WIDTH_MM": st["width"],
                "TRANSVERSE_POSITION_MM": [st["t0"], st["t1"]], "LOCAL_CLEAR_SPAN_MM": [st["L0"], st["L1"]],
                "START_BOUNDARY": _boundary(st, 0), "END_BOUNDARY": _boundary(st, 1),
                "OPENING_INTERSECTION": sum(1 for e in ("start_edge", "end_edge") if st[e][0] > 0),
                "SUPPORT_RELATION": x["relation"], "END_USED": None if x["end"] is None else
                ("START", "END")[x["end"]], "BASE_RUN_MM": x["base"],
                "CURTAILMENT_DEDUCTION_MM": x["deduction"] if role == "BOTTOM_CURTAILED_50" else None,
                "STOPPING_ENDS": x["n_stop"] if role == "BOTTOM_CURTAILED_50" else None,
                "RUN_LENGTH_MM": x["run"], "EXTENSION_LENGTH_MM": x["extension"], "DENSITY_FRACTION": frac,
                "CONTRIBUTION_M2": con, "EQUIVALENT_LENGTH_M": rate * frac * con,
                "KG": rate * frac * con * um, "REGION_TS_MM": [round(v, 3) for v in x["region"]]})
    check(not blocked_cands, f"S7 blocked candidates (a PRE-S7.1 candidate failed re-derivation): "
                             f"{[(b['c']['QTO_ITEM_ID'], b['why']) for b in blocked_cands]}")

    # ---------------------------------------------------- 02 blocked / excluded / conflict items (no kg)
    blocked = []
    for i in items71:
        if i["LANE"] == S7.PROJECT_BASIS_QTO:
            continue
        blocked.append({
            "PRE_S7_1_ITEM_ID": i["QTO_ITEM_ID"], "COMPONENT_ID": i["PARENT_COMPONENT_ID"], "ITEM": i["ITEM"],
            "OWNER": i["OWNER"], "FLOOR": i.get("FLOOR"), "DIRECTION": i.get("DIRECTION"),
            "SUPPORT_ID": i.get("SUPPORT_ID"), "SIDE_PANEL": i.get("SIDE_PANEL"), "DIA_MM": i.get("DIA_MM"),
            "COUNT_BASIS": i.get("COUNT_BASIS"), "RATE_PER_M": i.get("RATE_PER_M"),
            "EXPLICIT_COUNT": i.get("EXPLICIT_COUNT"), "COUNT_RELEASED": i.get("COUNT_RELEASED"),
            "DISTRIBUTION_WIDTH_MM": i.get("DISTRIBUTION_WIDTH_MM"), "S7_LANE": blocked_lane(i),
            "CATEGORY": blocked_category(i), "BLOCKERS": _lst(i.get("BLOCKERS")),
            "QUESTIONS": _lst(i.get("QUESTIONS")), "S8_REGION": i.get("S8_REGION"), "CONFLICT_REF": conflict_ref(i),
            "KG": None, "WHY_NO_KG": ("ownership transferred to S8" if i["LANE"] == "TRANSFERRED_S8" else
                                      "true source conflict" if i["ITEM"] == "FAMILY_BLOCKED" else
                                      "count released, length blocked" if i.get("COUNT_RELEASED") else
                                      "extent / count not established by the source or an accepted rule"),
            "S7_ORIGIN": "PRE-S7.1 " + ("TRANSFERRED_S8 item" if i["LANE"] == "TRANSFERRED_S8" else
                                        "10_REMAINING_BLOCKERS.csv")})
    # §20 opening trim / diagonal bars: the voids in or beside S7 panels have no source rule (PRE-S7 08 register)
    nb_of = defaultdict(set)
    for (pid, d), st in B["strips"].items():
        for x in st:
            for e in ("start_edge_ref", "end_edge_ref"):
                if x[e].get("neighbour"):
                    nb_of[x[e]["neighbour"]].add(pid)
    for o in openings:
        if o["TYPE"] != "OPEN_TO_BELOW_FACE":
            continue
        void = o["GEOMETRY"].replace("FACE ", "")
        adj = sorted(nb_of.get(void, set()))
        for part, rule in (("OPENING_TRIM_BARS", o["TRIM_BAR_RULE"]), ("OPENING_DIAGONAL_BARS",
                                                                         o["DIAGONAL_BAR_RULE"])):
            blocked.append({"PRE_S7_1_ITEM_ID": None, "COMPONENT_ID": f"S7-{part}-{o['OPENING_ID'][3:]}",
                            "ITEM": part, "OWNER": o["OPENING_ID"], "FLOOR": o["FLOOR"], "DIRECTION": None,
                            "SUPPORT_ID": None, "SIDE_PANEL": adj, "S7_LANE": S7.BLOCKED_UNQUANTIFIED,
                            "CATEGORY": "OPENING_TRIM", "BLOCKERS": [f"NO_PROJECT_RULE ({rule})"],
                            "QUESTIONS": ["Q-OPENING"], "KG": None,
                            "WHY_NO_KG": "no trim / diagonal bar is drawn or specified for this void",
                            "S7_ORIGIN": "S7 §20 (PRE-S7 08_OPENING_REGISTER.csv)"})
    for k_, b in enumerate(blocked, 1):
        b["S7_BLOCKED_ID"] = f"S7B-{k_:04d}"

    # ---------------------------------------------------- 03 components
    rel_by_comp = defaultdict(list)
    for r in rel:
        rel_by_comp[r["COMPONENT_ID"]].append(r)
    blk_by_comp = defaultdict(list)
    for b in blocked:
        blk_by_comp[b["COMPONENT_ID"]].append(b)
    comp_rows = []
    s7_comp_ids = sorted({b["COMPONENT_ID"] for b in blocked if b["S7_ORIGIN"].startswith("S7")})
    for rd in readiness + [{"COMPONENT_ID": cid, "COMPONENT": blk_by_comp[cid][0]["ITEM"],
                            "OWNER": blk_by_comp[cid][0]["OWNER"], "FLOOR": blk_by_comp[cid][0]["FLOOR"],
                            "DIRECTION": None, "NEW_IN_AD2": "False", "AD2_STATE": None} for cid in s7_comp_ids]:
        cid = rd["COMPONENT_ID"]
        rs, bs = rel_by_comp.get(cid, []), blk_by_comp.get(cid, [])
        lanes = Counter(b["S7_LANE"] for b in bs)
        if rs:
            lane, state = S7.PROJECT_BASIS_QTO, "RELEASED_ALL" if not bs else "RELEASED_PARTIAL"
        elif lanes.get(S7.SOURCE_CONFLICT):
            lane, state = S7.SOURCE_CONFLICT, "SOURCE_CONFLICT"
        elif bs and all(b["S7_LANE"] == S7.EXCLUDED_SPECIAL_STRUCTURE for b in bs):
            lane, state = S7.EXCLUDED_SPECIAL_STRUCTURE, "EXCLUDED_S8"
        else:
            lane, state = S7.BLOCKED_UNQUANTIFIED, "BLOCKED"
        kg = math.fsum(r["KG"] for r in rs) if rs else None
        comp_rows.append({
            "COMPONENT_ID": cid, "COMPONENT": rd["COMPONENT"], "OWNER": rd["OWNER"], "FLOOR": rd.get("FLOOR") or None,
            "DIRECTION": rd.get("DIRECTION") or None, "ORIGIN": "S7 §20" if cid in s7_comp_ids else
            ("PRE-S7.1 (new in AD2)" if rd.get("NEW_IN_AD2") == "True" else "PRE-S7"),
            "AD2_STATE": rd.get("AD2_STATE") or None, "S7_STATE": state, "S7_TERMINAL_LANE": lane,
            "RELEASED_ITEMS": len(rs), "BLOCKED_ITEMS": sum(b["S7_LANE"] == S7.BLOCKED_UNQUANTIFIED for b in bs),
            "EXCLUDED_ITEMS": lanes.get(S7.EXCLUDED_SPECIAL_STRUCTURE, 0),
            "CONFLICT_ITEMS": lanes.get(S7.SOURCE_CONFLICT, 0),
            "DIAMETERS_MM": sorted({r["DIAMETER_MM"] for r in rs}),
            "EQUIVALENT_LENGTH_M": math.fsum(r["EQUIVALENT_TOTAL_LENGTH_M"] for r in rs) if rs else None,
            "KG": kg, "S7_ITEM_IDS": [r["S7_ITEM_ID"] for r in rs], "BLOCKED_ITEM_IDS": [b["S7_BLOCKED_ID"] for b in bs],
            "BLOCKED_CATEGORIES": sorted({b["CATEGORY"] for b in bs}),
            "QUESTIONS": sorted({q for b in bs for q in b["QUESTIONS"] or []})})
        if rd.get("AD2_STATE"):
            exp = {"RELEASED_ALL": "RELEASED_ALL", "RELEASED_PARTIAL": "RELEASED_PARTIAL", "BLOCKED":
                   ("BLOCKED", "SOURCE_CONFLICT"), "TRANSFERRED_S8": "EXCLUDED_S8"}[rd["AD2_STATE"]]
            check(state in (exp if isinstance(exp, tuple) else (exp,)), f"{cid}: S7 state {state} vs AD2 "
                                                                       f"{rd['AD2_STATE']}")

    # ---------------------------------------------------- 05 panels, 06 supports
    s1 = B["s1"]

    def area(pid):
        r = s1.get(pid)
        if not r or not r["polygon_mm"]:
            return _f(census[pid]["GEOMETRIC_AREA_M2"])
        a_ = B["Q"].polygon_area([tuple(p) for p in r["polygon_mm"]]) - math.fsum(
            B["Q"].polygon_area([tuple(p) for p in h]) for h in r["holes_mm"] or [])
        return a_ / 1e6

    def s7_scope(pid):
        r = census[pid]
        if pid in B["region"]:
            return f"S8_TRANSFERRED ({B['region'][pid]})"
        if r["PANEL_CLASS"] == "DENSE_HATCH_CANTILEVER_OR_BEARING_WALL":
            return "BEARING_WALL_CANDIDATE (support band, not a slab panel)"
        return {"IN_SCOPE_S7": "IN_SCOPE_S7", "EXCLUDED_SPECIAL_STRUCTURE": f"EXCLUDED_SPECIAL_STRUCTURE "
                f"({r['PANEL_CLASS']})", "VOID_OR_OPENING": "VOID", "NOT_SLAB": "NOT_SLAB"}.get(r["SCOPE"], r["SCOPE"])
    rel_owned = defaultdict(list)
    top_located = defaultdict(list)
    for r in rel:
        rel_owned[r["OWNER"]].append(r)
        if r["BAR_ROLE"] == "TOP_OVER_SUPPORT_EXTENSION":
            top_located[r["PANEL_ID"]].append(r)
    blk_owned = defaultdict(list)
    for b in blocked:
        blk_owned[b["OWNER"]].append(b)
    panel_rows = []
    for pid in sorted(census, key=lambda p: (FLOORS.index(census[p]["FLOOR"]), p)):
        r, rs = census[pid], rel_owned.get(pid, [])
        bx = [x for x in rs if x["DIRECTION"] == "X"]
        by = [x for x in rs if x["DIRECTION"] == "Y"]
        bs = blk_owned.get(pid, [])
        panel_rows.append({
            "PANEL_ID": pid, "FLOOR": r["FLOOR"], "PANEL_CLASS": r["PANEL_CLASS"], "S7_SCOPE": s7_scope(pid),
            "SHAPE": ("RECTANGULAR" if B["rect"][pid] else "IRREGULAR") if pid in B["rect"] else None,
            "SUNKEN": pid in B["sunken"], "THICKNESS_MM": _f(r["THICKNESS_MM"]), "AREA_M2": area(pid),
            "RELEASED_ITEMS_OWNED": len(rs), "BOTTOM_X_KG": math.fsum(x["KG"] for x in bx) if bx else None,
            "BOTTOM_Y_KG": math.fsum(x["KG"] for x in by) if by else None,
            "PANEL_OWNED_KG": math.fsum(x["KG"] for x in rs) if rs else None,
            "TOP_EXTENSION_KG_LOCATED_HERE": math.fsum(x["KG"] for x in top_located[pid]) if top_located[pid]
            else None, "TOP_EXTENSION_OWNERS": sorted({x["SUPPORT_ID"] for x in top_located[pid]}),
            "BLOCKED_ITEMS_OWNED": len(bs), "BLOCKED_CATEGORIES": sorted({b["CATEGORY"] for b in bs}),
            "NOTE": "top steel over supports is owned by the support (06), shown here only where it lies"})
    sup_ids = sorted({r["SUPPORT_ID"] for r in rel if r["SUPPORT_ID"]} |
                     {b["SUPPORT_ID"] for b in blocked if b.get("SUPPORT_ID")} |
                     {b["OWNER"] for b in blocked if str(b["OWNER"]).startswith("SUP-")})
    split_sids = {k[0] for k in B["split_keys"]}
    support_rows = []
    for sid in sup_ids:
        s = B["sup"][sid]
        rs = [r for r in rel if r["SUPPORT_ID"] == sid]
        owned = [r for r in rs if r["OWNER_KIND"] == "SUPPORT"]
        bs = [b for b in blocked if b.get("SUPPORT_ID") == sid or b["OWNER"] == sid]
        by_role = defaultdict(list)
        for r in owned:
            by_role[r["BAR_ROLE"]].append(r["KG"])
        support_rows.append({
            "SUPPORT_ID": sid, "FLOOR": s["FLOOR"], "SUPPORT_REF": s["SUPPORT_REF"], "SUPPORT_KIND": s["SUPPORT_KIND"],
            "BARS_CROSSING": s["BARS_CROSSING"], "AD2_CONTINUITY": B["ad2_sup"].get(sid, {}).get("continuity"),
            "SIDES": B["ad2_sup"].get(sid, {}).get("sides"), "MISMATCH_SPLIT": sid in split_sids,
            "LOCAL_TOP_OVERRIDE": sid in explicit, "BEARING_WALL_CANDIDATE_BAND": sid in hatch,
            "TOP_EXTENSION_KG": math.fsum(by_role["TOP_OVER_SUPPORT_EXTENSION"]) if
            by_role["TOP_OVER_SUPPORT_EXTENSION"] else None,
            "TOP_EXTENSION_SIDES": sorted(r["PANEL_ID"] for r in owned if r["BAR_ROLE"] == "TOP_OVER_SUPPORT_EXTENSION"),
            "TOP_CROSSING_KG": math.fsum(by_role["TOP_SUPPORT_CROSSING"]) if by_role["TOP_SUPPORT_CROSSING"] else None,
            "BOTTOM_CROSSING_KG": math.fsum(by_role["BOTTOM_SUPPORT_CROSSING"]) if
            by_role["BOTTOM_SUPPORT_CROSSING"] else None,
            "SUPPORT_OWNED_KG": math.fsum(r["KG"] for r in owned) if owned else None,
            "RELEASED_ITEMS_OWNED": len(owned), "BLOCKED_ITEMS": len(bs),
            "BLOCKED_KINDS": sorted({b["ITEM"] for b in bs})})

    # ---------------------------------------------------- totals
    def ksum(pred):
        return math.fsum(r["KG"] for r in rel if pred(r))

    def lsum(pred):
        return math.fsum(r["EQUIVALENT_TOTAL_LENGTH_M"] for r in rel if pred(r))
    totals = {
        "BOTTOM_IN_PANEL_FULL_DENSITY_KG": ksum(lambda r: r["BAR_ROLE"] == "BOTTOM_IN_PANEL"),
        "CONTINUING_BOTTOM_KG": ksum(lambda r: r["BAR_ROLE"] == "BOTTOM_CONTINUING_50"),
        "CURTAILED_BOTTOM_KG": ksum(lambda r: r["BAR_ROLE"] == "BOTTOM_CURTAILED_50"),
        "BOTTOM_SUPPORT_CROSSING_KG": ksum(lambda r: r["BAR_ROLE"] == "BOTTOM_SUPPORT_CROSSING"),
        "BOTTOM_MAIN_PROJECT_BASIS_KG": ksum(lambda r: r["LAYER"] == "BOTTOM"),
        "TOP_EXTENSION_KG": ksum(lambda r: r["BAR_ROLE"] == "TOP_OVER_SUPPORT_EXTENSION"),
        "TOP_SUPPORT_CROSSING_KG": ksum(lambda r: r["BAR_ROLE"] == "TOP_SUPPORT_CROSSING"),
        "TOP_SUPPORT_PROJECT_BASIS_KG": ksum(lambda r: r["LAYER"] == "TOP"),
        "LOCAL_TOP_EXPLICIT_KG": 0.0,
        "SUPPORT_CROSSING_KG": ksum(lambda r: r["BAR_ROLE"] in ("BOTTOM_SUPPORT_CROSSING", "TOP_SUPPORT_CROSSING")),
        S7.RESTRICTED_TOTAL: ksum(lambda r: True)}
    totals["TOTAL_RESTRICTED_S7_PROJECT_BASIS_KG"] = totals[S7.RESTRICTED_TOTAL]
    lengths = {"TOTAL_EQUIVALENT_BAR_LENGTH_M": lsum(lambda r: True),
               "BOTTOM_EQUIVALENT_LENGTH_M": lsum(lambda r: r["LAYER"] == "BOTTOM"),
               "TOP_EQUIVALENT_LENGTH_M": lsum(lambda r: r["LAYER"] == "TOP")}

    # ---------------------------------------------------- 07 floors, 08 diameters
    floor_rows = []
    for fl in FLOORS:
        ps = [p for p in panel_rows if p["FLOOR"] == fl]
        rs = [r for r in rel if r["FLOOR"] == fl]
        cs_ = [c for c in comp_rows if c["FLOOR"] == fl]
        bs = [b for b in blocked if b.get("FLOOR") == fl]
        by_scope = defaultdict(float)
        for p in ps:
            by_scope[p["S7_SCOPE"]] += p["AREA_M2"] or 0.0
        floor_rows.append({
            "FLOOR": fl, "LABEL": FLOOR_LABEL[fl],
            "SLAB_AREA_IN_S7_SCOPE_M2": math.fsum(p["AREA_M2"] for p in ps if p["S7_SCOPE"] == "IN_SCOPE_S7"),
            "PANELS_IN_S7_SCOPE": sum(p["S7_SCOPE"] == "IN_SCOPE_S7" for p in ps),
            "AREA_BY_SCOPE_M2": dict(sorted(by_scope.items())),
            "RELEASED_COMPONENTS": sum(c["S7_TERMINAL_LANE"] == S7.PROJECT_BASIS_QTO for c in cs_),
            "RELEASED_ITEMS": len(rs), "PANEL_OWNED_KG": math.fsum(r["KG"] for r in rs if r["OWNER_KIND"] == "PANEL"),
            "SUPPORT_OWNED_KG": math.fsum(r["KG"] for r in rs if r["OWNER_KIND"] == "SUPPORT"),
            "BOTTOM_MAIN_KG": math.fsum(r["KG"] for r in rs if r["LAYER"] == "BOTTOM"),
            "TOP_SUPPORT_KG": math.fsum(r["KG"] for r in rs if r["LAYER"] == "TOP"),
            "PROJECT_BASIS_KG": math.fsum(r["KG"] for r in rs),
            "EQUIVALENT_LENGTH_M": math.fsum(r["EQUIVALENT_TOTAL_LENGTH_M"] for r in rs),
            "BLOCKED_COMPONENTS": sum(c["S7_TERMINAL_LANE"] == S7.BLOCKED_UNQUANTIFIED for c in cs_),
            "PARTIALLY_RELEASED_COMPONENTS": sum(c["S7_STATE"] == "RELEASED_PARTIAL" for c in cs_),
            "CONFLICT_COMPONENTS": sum(c["S7_TERMINAL_LANE"] == S7.SOURCE_CONFLICT for c in cs_),
            "EXCLUDED_S8_COMPONENTS": sum(c["S7_TERMINAL_LANE"] == S7.EXCLUDED_SPECIAL_STRUCTURE for c in cs_),
            "TEMPERATURE_BLOCKED_COMPONENTS": sum(c["COMPONENT"].startswith("TEMPERATURE") and
                                                  c["S7_TERMINAL_LANE"] == S7.BLOCKED_UNQUANTIFIED for c in cs_),
            "BLOCKED_ITEMS": sum(b["S7_LANE"] == S7.BLOCKED_UNQUANTIFIED for b in bs),
            "EXCLUDED_SPECIAL_REGIONS": sorted({p["S7_SCOPE"] for p in ps if p["S7_SCOPE"] != "IN_SCOPE_S7"})})
    T = totals[S7.RESTRICTED_TOTAL]
    floor_rows.append({"FLOOR": "TOTAL", "LABEL": "ALL", **{
        k: math.fsum(f[k] for f in floor_rows) for k in ("SLAB_AREA_IN_S7_SCOPE_M2", "PANELS_IN_S7_SCOPE",
                                                          "RELEASED_COMPONENTS", "RELEASED_ITEMS", "PANEL_OWNED_KG",
                                                          "SUPPORT_OWNED_KG", "BOTTOM_MAIN_KG", "TOP_SUPPORT_KG",
                                                          "PROJECT_BASIS_KG", "EQUIVALENT_LENGTH_M",
                                                          "BLOCKED_COMPONENTS", "PARTIALLY_RELEASED_COMPONENTS",
                                                          "CONFLICT_COMPONENTS", "EXCLUDED_S8_COMPONENTS",
                                                          "TEMPERATURE_BLOCKED_COMPONENTS", "BLOCKED_ITEMS")}})
    for k in ("PANELS_IN_S7_SCOPE", "RELEASED_COMPONENTS", "RELEASED_ITEMS", "BLOCKED_COMPONENTS",
              "PARTIALLY_RELEASED_COMPONENTS", "CONFLICT_COMPONENTS", "EXCLUDED_S8_COMPONENTS",
              "TEMPERATURE_BLOCKED_COMPONENTS", "BLOCKED_ITEMS"):
        floor_rows[-1][k] = int(floor_rows[-1][k])
    dia_rows = []
    for d_ in sorted({r["DIAMETER_MM"] for r in rel}):
        rs = [r for r in rel if r["DIAMETER_MM"] == d_]
        kg = math.fsum(r["KG"] for r in rs)
        dia_rows.append({"DIAMETER_MM": d_, "UNIT_MASS_KG_M": S7.unit_mass(d_),
                         "EQUIVALENT_LENGTH_M": math.fsum(r["EQUIVALENT_TOTAL_LENGTH_M"] for r in rs), "KG": kg,
                         "PCT_OF_RESTRICTED_S7_KG": 100.0 * kg / T, "ITEMS": len(rs),
                         "BOTTOM_KG": math.fsum(r["KG"] for r in rs if r["LAYER"] == "BOTTOM"),
                         "TOP_KG": math.fsum(r["KG"] for r in rs if r["LAYER"] == "TOP")})

    # ---------------------------------------------------- 11 S7.1 candidates (0 kg in S7)
    s71 = []
    for i in items71:
        if i["LANE"] != S7.BLOCKED_UNQUANTIFIED:
            continue
        qs = _lst(i.get("QUESTIONS"))
        if i["ITEM"] == "BOTTOM_STOP_ZONE_UNRESOLVED":
            would = ("if the end is confirmed NON_CONTINUOUS the curtailed half runs the 0.125 L zone to the face "
                     "(the strip geometry already fixes it); if CONTINUOUS the bars stop and the zone has no steel")
        elif i["ITEM"] == "TOP_EXTENSION" and "Q-HATCH" in qs:
            would = ("if plan note 2 applies over this bearing-wall-candidate band, the 1/3 L extension is measured "
                     "as at every other beam support (the strip geometry already fixes it)")
        else:
            continue
        s71.append({"S7_1_CANDIDATE_ID": None, "PRE_S7_1_ITEM_ID": i["QTO_ITEM_ID"],
                    "COMPONENT_ID": i["PARENT_COMPONENT_ID"], "ITEM": i["ITEM"], "OWNER": i["OWNER"],
                    "FLOOR": i.get("FLOOR"), "DIRECTION": i.get("DIRECTION"), "SUPPORT_ID": i.get("SUPPORT_ID"),
                    "DIA_MM": i.get("DIA_MM"), "RATE_PER_M": i.get("RATE_PER_M"),
                    "DENSITY_FRACTION": i.get("DENSITY_FRACTION"),
                    "DISTRIBUTION_WIDTH_MM": _f(i.get("DISTRIBUTION_WIDTH_MM")), "QUESTION": qs,
                    "DECISION_NEEDED": would, "GEOMETRY_STATE": "DETERMINISTIC (PRE-S7.1 local bar strips)",
                    "FOUND_BY": "S7 (one owner / source decision from quantity-ready; not quantified here)",
                    "KG_IN_S7": 0.0})
    for k_, r in enumerate(s71, 1):
        r["S7_1_CANDIDATE_ID"] = f"S7.1-{k_:03d}"

    # ---------------------------------------------------- gates (§28)
    cid_count = Counter([r["PRE_S7_1_CANDIDATE_ID"] for r in rel] +
                        [b["c"]["QTO_ITEM_ID"] for b in blocked_cands])
    rec_rows = [{"kg": r["KG"], "comp": r["COMPONENT_ID"], "owner": r["OWNER"], "floor": r["FLOOR"],
                 "dia": r["DIAMETER_MM"], "role": r["BAR_ROLE"], "item": r["S7_ITEM_ID"]} for r in rel]
    rec = S7.reconcile(rec_rows, ["item", "comp", "owner", "floor", "dia", "role"])
    run_sum = defaultdict(list)
    for x in runs:
        run_sum[x["S7_ITEM_ID"]].append(x["KG"])
    te_strip_ends = [(c_["strip"]["id"], c_["end"]) for k, v in contrib.items() if k[0] == "TE" and k in set(keys)
                     for c_ in v]
    tx_strip_ends = [(c_["strip"]["id"], c_["end"]) for k, v in contrib.items() if k[0] == "TX" and k in set(keys)
                     for c_ in v]
    top_keys = [(r["SUPPORT_ID"], r["BAR_ROLE"], r["PANEL_ID"]) for r in rel if r["LAYER"] == "TOP"]
    overlaps = {}
    for fl in FLOORS:
        for d in ("X", "Y"):
            for layer, kinds in (("TOP", ("TE", "TX")), ("BOTTOM", ("BX",))):
                regs = [(f"{k}:{c_['strip']['id']}:{c_['end']}", *c_["region"]) for k_, (k, v) in
                        enumerate(sorted(contrib.items(), key=lambda kv: str(kv[0])))
                        if k in set(keys) and k[0] in kinds for c_ in v
                        if c_["strip"]["direction"] == d and B["cs"][c_["strip"]["panel"]]["FLOOR"] == fl]
                if layer == "BOTTOM":
                    seen = set()
                    for k, v in contrib.items():
                        if k in set(keys) and k[0] == "B":
                            for c_ in v:
                                st = c_["strip"]
                                if st["direction"] == d and B["cs"][st["panel"]]["FLOOR"] == fl and \
                                        st["id"] not in seen:
                                    seen.add(st["id"])
                                    regs.append((f"B:{st['id']}", *_region(st)))
                overlaps[f"{fl}:{d}:{layer}"] = S7.strip_overlaps(regs, tol=OVERLAP_TOL_MM)
    per_strip_density = defaultdict(float)
    for k, v in contrib.items():
        if k in set(keys) and k[0] == "B":
            for c_ in v:
                per_strip_density[c_["strip"]["id"]] += c_["frac"]
    # a mismatch is between two different BOTTOM callouts: no bottom run may cross it (the plan-note-2 top bars are
    # one family on both sides and do cross); the left / right in-panel runs stop at their own faces
    split_rel = [r for r in rel if r["BAR_ROLE"] == "BOTTOM_SUPPORT_CROSSING" and
                 (r["SUPPORT_ID"], *r["PANEL_ID"].split("|"), r["DIRECTION"]) in B["split_keys"]]
    split_top = [r for r in rel if r["BAR_ROLE"] == "TOP_SUPPORT_CROSSING" and
                 (r["SUPPORT_ID"], *r["PANEL_ID"].split("|"), r["DIRECTION"]) in B["split_keys"]]
    split_sides = {(k[0], k[3]): (k[1], k[2]) for k in B["split_keys"]}
    split_inpanel = defaultdict(set)
    for r in rel:
        if r["OWNER_KIND"] == "PANEL":
            for (sid_k, d_k), pair in split_sides.items():
                if r["DIRECTION"] == d_k and r["PANEL_ID"] in pair:
                    split_inpanel[(sid_k, d_k)].add(r["PANEL_ID"])
    temp_ids = {c["COMPONENT_ID"] for c in comp_rows if c["COMPONENT"].startswith("TEMPERATURE")}
    labels = [str(v) for r in rel + blocked + comp_rows for v in r.values() if isinstance(v, str)]
    gates = {
        "candidates_terminate_exactly_once": set(cid_count) == {c["QTO_ITEM_ID"] for c in cands} and
        all(v == 1 for v in cid_count.values()) and len(cid_count) == CANDIDATE_POPULATION,
        "no_non_candidate_produces_kg": all(r["PRE_S7_1_CANDIDATE_ID"] in {c["QTO_ITEM_ID"] for c in cands}
                                            for r in rel) and all(b["KG"] is None for b in blocked),
        "mass_reconciles_item_component_owner_floor_diameter_project": rec["ok"] and
        abs(math.fsum(c["KG"] for c in comp_rows if c["KG"] is not None) - T) <= 1e-9 * T and
        abs(math.fsum(p["PANEL_OWNED_KG"] or 0.0 for p in panel_rows) +
            math.fsum(s["SUPPORT_OWNED_KG"] or 0.0 for s in support_rows) - T) <= 1e-9 * T and
        abs(floor_rows[-1]["PROJECT_BASIS_KG"] - T) <= 1e-9 * T and
        abs(math.fsum(d_["KG"] for d_ in dia_rows) - T) <= 1e-9 * T and
        abs(totals["BOTTOM_MAIN_PROJECT_BASIS_KG"] + totals["TOP_SUPPORT_PROJECT_BASIS_KG"] +
            totals["LOCAL_TOP_EXPLICIT_KG"] - T) <= 1e-9 * T and
        all(abs(math.fsum(run_sum[r["S7_ITEM_ID"]]) - r["KG"]) <= 1e-9 * max(r["KG"], 1.0) for r in rel),
        "no_blocked_item_carries_kg": all(b["KG"] is None for b in blocked) and
        all(c["KG"] is None for c in comp_rows if c["S7_TERMINAL_LANE"] in S7.NO_MASS_LANES),
        "no_s8_transfer_carries_s7_kg": not any(set(str(r["PANEL_ID"]).split("|")) & s8_panels or
                                                r["OWNER"] in s8_panels for r in rel),
        "no_temperature_component_carries_kg": not any(r["COMPONENT_ID"] in temp_ids for r in rel) and
        all(c["KG"] is None for c in comp_rows if c["COMPONENT_ID"] in temp_ids),
        "no_overridden_same_role_top_bar_double_counted": not any(
            set(r["SOURCE_RULE_IDS"]) & set(OVERRIDDEN_TOP_RULES) for r in rel),
        "NO_SUPPORT_TOP_BAR_DOUBLE_COUNT": not S7.duplicates(te_strip_ends) and not S7.duplicates(tx_strip_ends)
        and not S7.duplicates(top_keys) and all(not v for k, v in overlaps.items() if k.endswith(":TOP")),
        "no_local_top_override_coexists_with_the_overridden_general_bar": not any(
            r["SUPPORT_ID"] in explicit for r in rel if r["LAYER"] == "TOP"),
        "fifty_plus_fifty_density_is_one_hundred": all(abs(v - 1.0) <= 1e-12 for v in per_strip_density.values()),
        "mismatch_left_right_portions_do_not_overlap": not split_rel and
        all(not v for k, v in overlaps.items() if k.endswith(":BOTTOM")),
        "irregular_strip_integration_reconciles": all(v["reconciled"] for v in B["recon"].values()) and
        not blocked_cands,
        "no_released_item_uses_minimum_cover_or_40cl": all(r["S7_LANE"] == S7.PROJECT_BASIS_QTO for r in rel) and
        not any("MINIMUM_PROJECT_COVER" in r["LENGTH_AUTHORITY"] or "40 CL" in r["LENGTH_AUTHORITY"] for r in rel),
        "equivalent_counts_unrounded": all(abs(r["EQUIVALENT_BAR_COUNT"] - r["RATE_PER_M"] * r["DENSITY_FRACTION"] *
                                               r["TRANSVERSE_WIDTH_M"]) <= 1e-9 for r in rel),
        "unit_mass_is_d_squared_over_162": all(r["UNIT_MASS_KG_M"] == r["DIAMETER_MM"] ** 2 / 162.0 for r in rel),
        "no_forbidden_label": not any(b in s.upper() for s in labels for b in S7.FORBIDDEN_LABELS)}
    check(all(gates.values()), f"S7 conservation gates {[k for k, v in gates.items() if not v]}")
    return locals()


# ------------------------------------------------------------------ write
REL_FIELDS = ["S7_ITEM_ID", "PRE_S7_1_CANDIDATE_ID", "COMPONENT_ID", "OWNER", "OWNER_KIND", "PANEL_ID", "SUPPORT_ID",
              "BAR_RUN_ID", "FLOOR", "BAR_ROLE", "LAYER", "DIRECTION", "DIAMETER_MM", "RATE_PER_M", "EXPLICIT_COUNT",
              "DENSITY_FRACTION", "TRANSVERSE_WIDTH_M", "EQUIVALENT_BAR_COUNT", "PHYSICAL_BBS_COUNT",
              "LOCAL_CLEAR_SPAN_MEAN_M", "CURTAILMENT_DEDUCTION_M", "RUN_LENGTH_M", "EXTENSION_LENGTH_M",
              "CALCULATED_EXTENT_M", "EQUIVALENT_TOTAL_LENGTH_M", "UNIT_MASS_KG_M", "KG", "S7_LANE",
              "QUANTITY_AUTHORITY", "LENGTH_AUTHORITY", "COUNT_AUTHORITY", "DENSITY_AUTHORITY", "SOURCE_RATIO",
              "SOURCE_RATIO_RULE", "SOURCE_RATIO_AUTHORITY", "SPAN_BASIS", "SPAN_BASIS_AUTHORITY",
              "MEASUREMENT_ORIGIN", "MEASUREMENT_ORIGIN_AUTHORITY", "LAYER_AUTHORITY", "SOURCE_RULE_IDS",
              "URBAN_RULE_IDS", "AD2_DECISIONS", "BLOCKED_COMPLEMENTS", "STRIPS", "SUNKEN_PANEL", "IRREGULAR_PANEL",
              "FORMULA", "PROVENANCE"]
BLK_FIELDS = ["S7_BLOCKED_ID", "PRE_S7_1_ITEM_ID", "COMPONENT_ID", "ITEM", "OWNER", "FLOOR", "DIRECTION",
              "SUPPORT_ID", "SIDE_PANEL", "DIA_MM", "COUNT_BASIS", "RATE_PER_M", "EXPLICIT_COUNT", "COUNT_RELEASED",
              "DISTRIBUTION_WIDTH_MM", "S7_LANE", "CATEGORY", "BLOCKERS", "QUESTIONS", "S8_REGION", "CONFLICT_REF",
              "KG", "WHY_NO_KG", "S7_ORIGIN"]
RUN_FIELDS = ["BAR_RUN_ROW_ID", "S7_ITEM_ID", "PRE_S7_1_CANDIDATE_ID", "BAR_RUN_ID", "BAR_ROLE", "FLOOR", "PANEL_ID",
              "DIRECTION", "STRIP_ID", "STRIP_WIDTH_MM", "TRANSVERSE_POSITION_MM", "LOCAL_CLEAR_SPAN_MM",
              "START_BOUNDARY", "END_BOUNDARY", "OPENING_INTERSECTION", "SUPPORT_RELATION", "END_USED",
              "BASE_RUN_MM", "CURTAILMENT_DEDUCTION_MM", "STOPPING_ENDS", "RUN_LENGTH_MM", "EXTENSION_LENGTH_MM",
              "DENSITY_FRACTION", "CONTRIBUTION_M2", "EQUIVALENT_LENGTH_M", "KG", "REGION_TS_MM"]


def summarise(B):
    rel, blocked, comps = B["rel"], B["blocked"], B["comp_rows"]
    cat_items = Counter(b["CATEGORY"] for b in blocked)
    cat_comps = defaultdict(set)
    for b in blocked:
        cat_comps[b["CATEGORY"]].add(b["COMPONENT_ID"])
    fully = {c["COMPONENT_ID"] for c in comps if c["S7_TERMINAL_LANE"] != S7.PROJECT_BASIS_QTO}
    T = B["totals"][S7.RESTRICTED_TOTAL]
    sunk = defaultdict(float)
    for r in rel:
        if r["OWNER_KIND"] == "PANEL" and r["SUNKEN_PANEL"]:
            sunk[r["PANEL_ID"]] += r["KG"]
    return {
        "round": ROUND, "policy": POLICY, "baseline_head": BASELINE_HEAD, "engine_commit": f"{BASELINE_HEAD}+code:"
        f"{code_digest()}", "frozen": {k: {kk: v[kk] for kk in ("manifest", "manifest_sha256", "round",
                                                                 "files_checked")} for k, v in B["frozen"].items()},
        "pre_s7_1_registers_reproduced_in_memory": B["reproduced"],
        "candidate_population": len(B["cands"]), "candidate_components": len(B["cand_comps"]),
        "released_items": len(rel), "blocked_candidates": len(B["blocked_cands"]),
        "released_components": sum(c["S7_TERMINAL_LANE"] == S7.PROJECT_BASIS_QTO for c in comps),
        "released_components_all": sum(c["S7_STATE"] == "RELEASED_ALL" for c in comps),
        "released_components_partial": sum(c["S7_STATE"] == "RELEASED_PARTIAL" for c in comps),
        "released_items_by_lane": dict(Counter(r["S7_LANE"] for r in rel)),
        "released_items_by_role": dict(sorted(Counter(r["BAR_ROLE"] for r in rel).items())),
        "source_derived_physical_items": sum(r["S7_LANE"] == S7.SOURCE_DERIVED_PHYSICAL for r in rel),
        "project_basis_numeric_items": sum(r["S7_LANE"] == S7.PROJECT_BASIS_NUMERIC for r in rel),
        "totals_kg": B["totals"], "lengths_m": B["lengths"], "total_name": S7.RESTRICTED_TOTAL,
        "total_is_final": False,
        "definitions": {
            "BOTTOM_MAIN_PROJECT_BASIS_KG": "BOTTOM_IN_PANEL_FULL_DENSITY + CONTINUING_BOTTOM + CURTAILED_BOTTOM + "
                                            "BOTTOM_SUPPORT_CROSSING",
            "TOP_SUPPORT_PROJECT_BASIS_KG": "TOP_EXTENSION + TOP_SUPPORT_CROSSING (plan note 2, owned by supports)",
            "LOCAL_TOP_EXPLICIT_KG": "3Ø16/Top at SUP-GF_ROOF_SLAB-037: count released, length blocked -> no kg",
            "SUPPORT_CROSSING_KG": "BOTTOM_SUPPORT_CROSSING + TOP_SUPPORT_CROSSING (a cross-cut: already inside the "
                                   "bottom and top subtotals)",
            S7.RESTRICTED_TOTAL: "BOTTOM_MAIN + TOP_SUPPORT + LOCAL_TOP_EXPLICIT; the 476 candidates only; every "
                                 "blocked / excluded portion is outside it (excluded, not zero)"},
        "by_floor_kg": {f["FLOOR"]: f["PROJECT_BASIS_KG"] for f in B["floor_rows"]},
        "by_diameter": {str(d["DIAMETER_MM"]): {"kg": d["KG"], "equivalent_length_m": d["EQUIVALENT_LENGTH_M"],
                                                "pct": d["PCT_OF_RESTRICTED_S7_KG"]} for d in B["dia_rows"]},
        "blocked_items": sum(b["S7_LANE"] == S7.BLOCKED_UNQUANTIFIED for b in blocked),
        "excluded_s8_items": sum(b["S7_LANE"] == S7.EXCLUDED_SPECIAL_STRUCTURE for b in blocked),
        "source_conflict_items": sum(b["S7_LANE"] == S7.SOURCE_CONFLICT for b in blocked),
        "blocked_register_rows": len(blocked),
        "blocked_items_by_category": dict(sorted(cat_items.items())),
        "components_with_blocked_portion_by_category": {k: len(v) for k, v in sorted(cat_comps.items())},
        "components_fully_without_kg_by_category": {k: len(v & fully) for k, v in sorted(cat_comps.items())},
        "BLOCKED_TEMPERATURE_COMPONENTS": len(cat_comps["TEMPERATURE"] & fully),
        "BLOCKED_ANCHORAGE_COMPONENTS": len(cat_comps["ANCHORAGE_END_COVER"]),
        "BLOCKED_TRANSITION_COMPONENTS": len(cat_comps["TRANSITION_LAP_SPLICE"]),
        "BLOCKED_SUNKEN_EXTRA_COMPONENTS": len(cat_comps["SUNKEN_EXTRA"]),
        "components_by_s7_state": dict(sorted(Counter(c["S7_STATE"] for c in comps).items())),
        "components_by_s7_lane": dict(sorted(Counter(c["S7_TERMINAL_LANE"] for c in comps).items())),
        "sunken_panels_base_mesh_kg": dict(sorted(sunk.items())),
        "s8_excluded": {"components": sum(c["S7_TERMINAL_LANE"] == S7.EXCLUDED_SPECIAL_STRUCTURE for c in comps),
                        "items": sum(b["S7_LANE"] == S7.EXCLUDED_SPECIAL_STRUCTURE for b in blocked),
                        "by_region": dict(sorted(Counter(b["S8_REGION"] for b in blocked
                                                         if b["S7_LANE"] == S7.EXCLUDED_SPECIAL_STRUCTURE).items()))},
        "open_source_conflicts": ["C-01 PANEL_VOID_CONFLICT (GF-21, preserved in S8)",
                                  "C-03 MULTIPLE_CANDIDATE_BINDINGS (GF-22 X: two callouts)",
                                  "C-04 COUNT_NOTATION_CONFLICT (552 / 5B9 / 750)",
                                  "C-06 COVER_DIMENSION_BINDING ('40 CL.', no quantity depends on it)",
                                  "C-09 TOP_BAR_BINDING (79F / 7A2)"],
        "authority_corrections": [
            {"id": "S7-AC01", "subject": "top extent over supports (plan note 2)",
             "pre_s7_1_record": "TOP_EXTENSION EXTENT_BASES [URBAN_OWNER_MEASUREMENT_RULE]; the whole extent was "
                                "labelled an Urban rule",
             "correction": "EXTENT_RATIO 1/3 = PROJECT_SOURCE (P4-6-NOTE-2: 'length one third of the span'); only "
                           "the convention measuring it from the support face into each side's clear span (note 2 "
                           "states no origin, no span and not total-vs-each-side) is URBAN_OWNER_MEASUREMENT_RULE "
                           "URBAN_QTO_TOP_OVER_SUPPORT_EXTENT_V1. Kept in separate fields on every S7 item.",
             "quantity_effect": "none (authority labels only; PRE-S7.1 extents unchanged)"},
            {"id": "S7-AC02", "subject": "0.125 L / 50 % bottom curtailment (p.15)",
             "pre_s7_1_record": "EXTENT_BASES [PROJECT_GEOMETRY, PROJECT_SOURCE_RULE] (+ URBAN local bar line on "
                                "irregular panels) in one field",
             "correction": "CURTAILMENT_RATIO 0.125 and DENSITY_FRACTION 0.5 / 0.5 = PROJECT_SOURCE "
                           "(P15-BOT-STOP-0.125L); its span basis (CLEAR_SPAN) and origin (FACE_OF_SUPPORT) are "
                           "also PROJECT_SOURCE (p.15 detail). Recorded separately: the local L along each bar line "
                           "on an irregular panel (URBAN_QTO_LOCAL_BAR_LINE_V1) and the AD2-D15 treatment of a "
                           "continuity-unresolved end.",
             "quantity_effect": "none (authority labels only)"}],
        "s7_1_candidates": len(B["s71"]), "s7_1_candidates_kg": 0.0,
        "opening_trim_blocked_rows": B["cat_items_opening"] if "cat_items_opening" in B else
        sum(b["CATEGORY"] == "OPENING_TRIM" for b in blocked),
        "overlap_checks": {k: len(v) for k, v in B["overlaps"].items()},
        "reconciliation": {lv: {"groups": v["groups"], "ok": v["ok"]} for lv, v in B["rec"]["levels"].items()},
        "gates": B["gates"],
        "flags": {"kg_calculated": True, "scope_widened": False, "references_read_before_freeze": [],
                  "donor_or_code_used": False, "kg_per_m2_or_m3_factor_used": False, "rounded_counts": False,
                  "pre_s7_1_edited": False, "s7_1_started": False, "s8_started": False,
                  "final_total_claimed": False},
        "share_of_total_pct": {k: 100.0 * v / T for k, v in B["totals"].items() if k.endswith("_KG") and
                               k not in ("TOTAL_RESTRICTED_S7_PROJECT_BASIS_KG", S7.RESTRICTED_TOTAL)}}


def readme(B, s):
    t, L = s["totals_kg"], s["lengths_m"]

    def kg(k):
        return f"{t[k]:,.3f}"
    fl = "\n".join(f"| {f['LABEL']} | {f['SLAB_AREA_IN_S7_SCOPE_M2']:.3f} | {f['PANELS_IN_S7_SCOPE']} | "
                   f"{f['RELEASED_COMPONENTS']} | {f['RELEASED_ITEMS']} | {f['PROJECT_BASIS_KG']:,.3f} | "
                   f"{f['BLOCKED_COMPONENTS']} | {f['EXCLUDED_S8_COMPONENTS']} |" for f in B["floor_rows"])
    dia = "\n".join(f"| Ø{d['DIAMETER_MM']} | {d['UNIT_MASS_KG_M']:.6f} | {d['EQUIVALENT_LENGTH_M']:,.3f} | "
                    f"{d['KG']:,.3f} | {d['PCT_OF_RESTRICTED_S7_KG']:.2f} % |" for d in B["dia_rows"])
    cats = "\n".join(f"| {k} | {v} | {s['components_with_blocked_portion_by_category'][k]} | "
                     f"{s['components_fully_without_kg_by_category'][k]} |"
                     for k, v in s["blocked_items_by_category"].items())
    return f"""# S7: restricted elevated slab rebar QTO (project-basis release)

Round {ROUND}, policy `{POLICY}`. Baseline HEAD `{BASELINE_HEAD}`; engine stamp `{s['engine_commit']}`.

This is not the final slab total. It quantifies only the {s['candidate_population']} PRE-S7.1 S7 candidate items,
which come from {s['candidate_components']} components. Every other portion is listed in `02_S7_BLOCKED_ITEMS.csv`
with no kg. Excluded means not quantified, not zero steel.

The one total is **{S7.RESTRICTED_TOTAL} = {kg(S7.RESTRICTED_TOTAL)} kg**, an equivalent bar length of
{L['TOTAL_EQUIVALENT_BAR_LENGTH_M']:,.3f} m. Every released item is `PROJECT_BASIS_QTO`. None is
`SOURCE_DERIVED_PHYSICAL` or `PROJECT_BASIS_NUMERIC`, and nothing is labelled verified, as-built or source-exact.

## How each item is measured

The quantities come from the frozen PRE-S7.1 local bar strips. PRE-S7.1's own code is re-run in memory, and each of
its registers is checked byte for byte against the frozen file.

- **Equivalent length:** `L_total = RATE x DENSITY_FRACTION x sum(strip width x local run)`, in metres.
  - On a rectangle this is `RATE x FRACTION x width x run`.
  - The equivalent bar count `RATE x FRACTION x WIDTH` is never rounded, has no +1, and no ceiling or floor.
  - `PHYSICAL_BBS_COUNT` stays `UNRESOLVED`.
- **Mass:** `kg = L_total x D^2 / 162`, from `rebar_unit_mass`. No kg/m2 or kg/m3 factor is used.
- **Bottom bars.** Measured face to face of the supports.
  - `BOTTOM_IN_PANEL`: full density.
  - `BOTTOM_CONTINUING_50`: half density, face to face.
  - `BOTTOM_CURTAILED_50`: half density, run less 0.125 x L at each stopping end.
  - `BOTTOM_SUPPORT_CROSSING`: the continuing half over a continuous support, counted once.
  - The part beyond each face (anchorage, transition, lap, stop zones at unresolved ends) is blocked and listed.
- **Top bars (plan note 2, 5Ø10/m).** Owned by the support, quantified once.
  - `TOP_OVER_SUPPORT_EXTENSION`: 1/3 x the local clear span, from the support face into each side panel.
  - `TOP_SUPPORT_CROSSING`: over the beam between the faces, counted once.
  - The p.15 rules 0.25 L1, 0.30 Lmax and "extend 50 %" are `OVERRIDDEN_PROJECT_SOURCE` for the same bar role, and
    nothing is added for them.
  - At SUP-GF_ROOF_SLAB-037 the local 3Ø16/Top replaces note 2. Its count is released but its length is not, so it
    carries no kg, and no general 5Ø10/m is measured there.

## Authority split (provenance correction)

- **S7-AC01, top extent.** The 1/3 ratio is `PROJECT_SOURCE` (plan note 2). Only the convention that measures it from
  the support face into each side's clear span is `URBAN_OWNER_MEASUREMENT_RULE`
  (`URBAN_QTO_TOP_OVER_SUPPORT_EXTENT_V1`). Note 2 states no origin and no span, and does not say whether the length is
  a total or per side.
- **S7-AC02, bottom curtailment.** The 0.125 ratio and the 0.5 / 0.5 density are `PROJECT_SOURCE` (p.15). So are its
  span basis (clear span) and origin (face of support). Two conventions are recorded beside them:
  - the local L along each bar line on an irregular panel (`URBAN_QTO_LOCAL_BAR_LINE_V1`);
  - the AD2-D15 treatment of a continuity-unresolved end.
- On every item these sit in separate fields: `SOURCE_RATIO*`, `SPAN_BASIS*`, `MEASUREMENT_ORIGIN*`, `SOURCE_RULE_IDS`
  and `URBAN_RULE_IDS`. Neither correction changes a quantity.

## Totals (kg)

| subtotal | kg |
|---|---|
| BOTTOM_IN_PANEL_FULL_DENSITY_KG | {kg('BOTTOM_IN_PANEL_FULL_DENSITY_KG')} |
| CONTINUING_BOTTOM_KG | {kg('CONTINUING_BOTTOM_KG')} |
| CURTAILED_BOTTOM_KG | {kg('CURTAILED_BOTTOM_KG')} |
| BOTTOM_SUPPORT_CROSSING_KG | {kg('BOTTOM_SUPPORT_CROSSING_KG')} |
| **BOTTOM_MAIN_PROJECT_BASIS_KG** | **{kg('BOTTOM_MAIN_PROJECT_BASIS_KG')}** |
| TOP_EXTENSION_KG | {kg('TOP_EXTENSION_KG')} |
| TOP_SUPPORT_CROSSING_KG | {kg('TOP_SUPPORT_CROSSING_KG')} |
| **TOP_SUPPORT_PROJECT_BASIS_KG** | **{kg('TOP_SUPPORT_PROJECT_BASIS_KG')}** |
| LOCAL_TOP_EXPLICIT_KG | {kg('LOCAL_TOP_EXPLICIT_KG')} |
| SUPPORT_CROSSING_KG (cross-cut: bottom + top crossings) | {kg('SUPPORT_CROSSING_KG')} |
| **{S7.RESTRICTED_TOTAL}** | **{kg(S7.RESTRICTED_TOTAL)}** |

## Floors

| floor | S7 slab area m2 | S7 panels | released components | released items | project-basis kg | blocked components | S8 components |
|---|---|---|---|---|---|---|---|
{fl}

## Diameters

| diameter | kg/m | equivalent length m | kg | share |
|---|---|---|---|---|
{dia}

## Not quantified (02_S7_BLOCKED_ITEMS.csv, no kg)

| category | items | components with such a portion | components with no kg at all |
|---|---|---|---|
{cats}

- **Temperature steel** (160 mm and 180 mm): no exact table row, no interpolation, so it stays blocked.
- **Sunken panels:** the six base meshes are included. The step bars, edge extras and level-change details are
  blocked.
- **S8:** the water-tank panels 2F-01 and 2F-02, the GF-21 light well (its source conflict preserved) and the
  dome / stair-flight sides are all excluded.
- **Voids:** the three voids beside S7 panels have no trim or diagonal bars in the source, so those bars are blocked
  (§20).
- `11_S7_1_CANDIDATES.csv` lists {s['s7_1_candidates']} blocked items whose geometry is already fixed by the strips
  and that one owner or source decision would make quantity-ready. They carry 0 kg here.

## Files

| file | content |
|---|---|
| 01_S7_RELEASE_ITEMS.csv | the {s['released_items']} mass-bearing items, with full formula, authorities, rules and blocked complements |
| 02_S7_BLOCKED_ITEMS.csv | every blocked, excluded (S8) and conflicting portion, and the §20 opening trims; no kg |
| 03_S7_COMPONENT_SUMMARY.csv | every PRE-S7 / AD2 component (and the §20 rows) with its S7 terminal lane |
| 04_S7_BAR_RUNS.csv | strip-level runs of every released item (width, run, boundaries, contribution, kg) |
| 05_S7_PANEL_SUMMARY.csv | every census panel: scope, area, panel-owned kg, and the top steel located there |
| 06_S7_SUPPORT_SUMMARY.csv | every support with an item: owned top / crossing kg, override, split, blocked kinds |
| 07_S7_FLOOR_SUMMARY.csv | GF / 1F / 2F and the total |
| 08_S7_DIAMETER_SUMMARY.csv | equivalent length and kg per diameter |
| 09_S7_PROJECT_SUMMARY.json | totals, counts, authority corrections, gates |
| 10_S7_PROVENANCE.jsonl | one record per item, run, blocked item and component |
| 11_S7_1_CANDIDATES.csv | opportunities found in S7, at 0 kg |
| 12_S7_FREEZE_MANIFEST.json | hashes of code, inputs, outputs, decision records and candidate registers |

The rebuild is `python3 -I research/alsenan_slab_rebar_s7/build_s7.py`, and it is byte-identical. S7 was frozen
before any reference was read. The comparison lives only in `post_freeze/`, which this builder neither reads nor
writes.
"""


def write(B):
    _csv("01_S7_RELEASE_ITEMS.csv", B["rel"], REL_FIELDS)
    _csv("02_S7_BLOCKED_ITEMS.csv", B["blocked"], BLK_FIELDS)
    _csv("03_S7_COMPONENT_SUMMARY.csv", B["comp_rows"], list(B["comp_rows"][0]))
    _csv("04_S7_BAR_RUNS.csv", B["runs"], RUN_FIELDS)
    _csv("05_S7_PANEL_SUMMARY.csv", B["panel_rows"], list(B["panel_rows"][0]))
    _csv("06_S7_SUPPORT_SUMMARY.csv", B["support_rows"], list(B["support_rows"][0]))
    _csv("07_S7_FLOOR_SUMMARY.csv", B["floor_rows"], list(B["floor_rows"][0]))
    _csv("08_S7_DIAMETER_SUMMARY.csv", B["dia_rows"], list(B["dia_rows"][0]))
    _csv("11_S7_1_CANDIDATES.csv", B["s71"], list(B["s71"][0]))
    s = summarise(B)
    _json("09_S7_PROJECT_SUMMARY.json", s)
    src = f"frozen PRE-S7.1 ({B['frozen']['PRE-S7.1']['manifest_sha256'][:12]})"
    with open(HERE / "10_S7_PROVENANCE.jsonl", "w", encoding="utf-8") as f:
        runs_ref = [{"BAR_RUN_ROW_ID": r["BAR_RUN_ROW_ID"], "S7_ITEM_ID": r["S7_ITEM_ID"],
                     "PRE_S7_1_CANDIDATE_ID": r["PRE_S7_1_CANDIDATE_ID"], "STRIP_ID": r["STRIP_ID"],
                     "PANEL_ID": r["PANEL_ID"], "BAR_ROLE": r["BAR_ROLE"],
                     "STRIP_SOURCE": "PRE-S7.1 07_LOCAL_BAR_STRIPS.csv (full record: 04_S7_BAR_RUNS.csv)"}
                    for r in B["runs"]]
        for kind, rows, key in (("RELEASE_ITEM", B["rel"], "S7_ITEM_ID"), ("BAR_RUN", runs_ref, "BAR_RUN_ROW_ID"),
                                ("BLOCKED_ITEM", B["blocked"], "S7_BLOCKED_ID"),
                                ("COMPONENT", B["comp_rows"], "COMPONENT_ID"),
                                ("S7_1_CANDIDATE", B["s71"], "S7_1_CANDIDATE_ID")):
            for r in rows:
                f.write(json.dumps({"kind": kind, "id": r[key], "round": ROUND, "policy": POLICY, "source": src,
                                    "record": r}, sort_keys=True, ensure_ascii=False, default=str) + "\n")
    (HERE / "00_README.md").write_text(readme(B, s), encoding="utf-8")
    return s


def main():
    B = build()
    s = write(B)
    man = {"round": ROUND, "state": "FROZEN_BEFORE_REFERENCE_COMPARISON", "references_read_before_freeze": [],
           "baseline": BASELINE_HEAD, "engine_commit_stamp": s["engine_commit"],
           "rule": "S7 quantifies only the 476 PRE-S7.1 candidates; the post-freeze comparison refuses to run unless "
                   "every hash below still matches; a difference found there needs a new issue, new evidence, a new "
                   "regression and a new version - never an edit of these outputs and never a tuning to a reference",
           "code": {c: _sha(ROOT / c) for c in CODE}, "inputs": {i: _sha(ROOT / i) for i in INPUTS},
           "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
           "decision_records": {i: _sha(ROOT / i) for i in DECISION_RECORDS},
           "candidate_registers": {i: _sha(ROOT / i) for i in CANDIDATE_REGISTERS},
           "frozen_baselines": {k: v["manifest_sha256"] for k, v in B["frozen"].items()},
           "restricted_total_kg": _full(s["totals_kg"][S7.RESTRICTED_TOTAL])}
    _json(MANIFEST_NAME, man)
    print(json.dumps({k: s[k] for k in ("candidate_population", "released_items", "blocked_candidates",
                                        "released_components", "totals_kg", "lengths_m", "by_floor_kg",
                                        "by_diameter", "components_by_s7_state", "gates")}, indent=1))


if __name__ == "__main__":
    main()
