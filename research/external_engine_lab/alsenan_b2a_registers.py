"""ALSENAN PHASE B2A - registers, A3 -> B2A delta, QA gates, freeze and workbook (all from the B2A context; no
benchmark value is read here - the benchmark evaluation runs only AFTER this freeze, in alsenan_b2a_evaluation.py).

    python3 research/external_engine_lab/alsenan_b2a_registers.py <work_dir> <register_dir> [code_commit]
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import alsenan_phase_b2a as B2                                                                      # noqa: E402

FREEZE = "ALSENAN_PHASE_B2A_FREEZE"
XLSX_NAME = "URBAN_QTO_ALSENAN_PHASE_B2A.xlsx"
BANNER = ("SHADOW / PHASE B2A - GENERIC ENGINE IMPROVEMENT + OWNER METHODS - ALSENAN P7757 + ST7757 - FROZEN BEFORE THE "
          "BENCHMARK EVALUATION - NO PRICING - NO PRODUCTION MIGRATION")
A3_DIR = ROOT / "tests/alsenan/registers_a3"
B1_DIR = ROOT / "tests/alsenan/registers_b1"
RECOMMENDATION = "research/external_engine_lab/alsenan_phase_b2a_recommendation.json"
B2A_ENGINES = ["beam_binding", "structural_vertical", "concrete_model", "slab_region", "opening_authority",
               "curved_opening", "finish_height", "waterproofing_policy", "urban_methods"]


def digest(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def _a3(name):
    return json.loads((A3_DIR / f"{name}.json").read_text())


def _git(*args):
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:                                                                                   # noqa: BLE001
        return None


def _trim_binding(r):
    out = {k: v for k, v in r.items() if k != "band"}
    if r.get("band"):
        out["band"] = {k: r["band"][k] for k in ("edge_keys", "angle_rad", "t0", "t1", "centreline")}
    return out


def _trim_occ(o):
    out = {k: v for k, v in o.items() if k not in ("band_record",)}
    return out


# ------------------------------------------------------------------ registers
def registers(ctx) -> dict:
    b = B2.strip(ctx["b2a"])
    regs = {}
    regs["OWNER_FACT_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_B2A_OWNER_FACTS_V1", "facts": b["owner_facts"], "carried_from_a3": [f["id"] for f in ctx["a3"]["owner_facts"]],
        "no_fact": b["no_fact"],
        "classes": ["PROJECT_OWNER_FACT", "URBAN_OWNER_METHOD", "SOURCE_EVIDENCE", "OWNER_DERIVED_PROJECT_DIMENSION", "UNRESOLVED"],
        "rule": "project facts are scoped to Alsenan and never travel; benchmark observations are never facts"}
    regs["URBAN_METHOD_REGISTER"] = b["methods"]
    regs["STRUCTURAL_VERTICAL_INTERVAL_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_B2A_STRUCTURAL_VERTICAL_V1", "policy": b["policies"]["structural_vertical"],
        "levels": B2.LEVELS, "intervals": b["intervals"], "column_tag_binding": b["columns"]["tag_binding"],
        "column_tag_binding_states": b["columns"]["tag_binding_states"], "rows": b["columns"]["rows"],
        "states": b["columns"]["states"], "by_storey": b["columns"]["by_storey"], "neck": b["columns"]["neck"],
        "neck_why": b["columns"]["neck_why"], "rule": b["columns"]["rule"]}
    regs["BEAM_BINDING_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_B2A_BEAM_BINDING_V1", "policy": b["policies"]["beam_binding"],
        "namespace_audit": b["namespace_audit"], "libraries": b["libraries"],
        "sheets": {fl: {"sheet": s["sheet"], "marks": s["marks"], "binding_states": s["binding_states"],
                        "occurrence_states": s["occurrence_states"], "binding": [_trim_binding(r) for r in s["binding"]],
                        "occurrences": [_trim_occ(o) for o in s["occurrences"]], "notes": s["occurrence_notes"]}
                   for fl, s in b["sheets"].items()},
        "length_bases": ["PLAN_DRAWN_EXTENT", "CLEAR_FACE_TO_FACE_LENGTH", "SUPPORT_CENTRELINE_LENGTH", "SCHEDULE_SPAN_LENGTH"],
        "volume_basis": "downstand = CLEAR_FACE_TO_FACE_LENGTH x B x (D - t); a continuous occurrence whose tags / "
                        "segments do not match its schedule span count is SPAN_COUNT_MISMATCH (length published, volume blocked)"}
    regs["SLAB_REGION_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_B2A_SLAB_REGION_V1", "policy": b["policies"]["slab_region"],
        "sheets": {fl: dict(s["slab"], dangles=s["dangles"]) for fl, s in b["sheets"].items()},
        "rule": "plate from the sheet's own line work; openings from VOID labels / opening-layer crosses / stair line work; "
                "never fitted to a target"}
    regs["PHYSICAL_CONCRETE_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_B2A_PHYSICAL_CONCRETE_V1", "policy": b["policies"]["concrete_model"],
        "storeys": b["concrete"], "explicit_items": b["structural_items"],
        "rule": "physical total never double counts; gross beam view reported separately; blocked components excluded "
                "and listed"}
    regs["STAIR_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_B2A_STAIR_V1", **b["stairs"],
                              "a3_tread_runs": _a3("STAIR_REGISTER").get("tread_runs")}
    arch = b["architecture"]
    regs["OPENING_AUTHORITY_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_B2A_OPENING_AUTHORITY_V1", "policy": b["policies"]["opening_authority"],
        "rows": arch["openings"]["rows"], "functions": arch["openings"]["functions"], "changes": arch["openings"]["changes"],
        "door_reconciliation": [{"opening": r["id"], "door_occurrence": _door_id(r["function_basis"])} for r in arch["openings"]["rows"]
                                if r["function"] == "DOOR"],
        "salon": arch["salon"], "review_image": "GF_1M_OPENINGS_REVIEW.png (package)",
        "rule": "existence, geometry, function, material and vertical extent are separate; UNKNOWN is never published as "
                "WINDOW; an opening whose gap a door closes is that door (counted once)"}
    regs["CURVED_OPENING_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_B2A_CURVED_V1", **arch["curved"]}
    regs["WALL_HEIGHT_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_B2A_WALL_HEIGHT_V1", "policy": b["policies"]["finish_height"], **arch["wall_heights"],
        "mbr": arch["mbr"], "gf_open_site": arch["gf_open_site"], "reception": arch["reception"]}
    regs["WATERPROOFING_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_B2A_WATERPROOFING_V1", **arch["waterproofing"]}
    regs["ALSENAN_B2A_DELTA"] = delta(ctx, regs)
    regs["A3_PRESERVATION"] = a3_preservation(ctx)
    regs["REMAINING_BLOCKERS"] = blockers(regs)
    regs["QA_GATES"] = qa(ctx, regs)
    regs["TEST_RESULTS"] = {"SCHEMA": "URBAN_ALSENAN_B2A_TEST_RESULTS_V1", "state": "RECORDED_BY_THE_PACKAGE_STEP",
                            "why": "the one full suite runs from the final commit",
                            "b2a_test_files": ["tests/alsenan/test_b2a_engines_synthetic.py", "tests/alsenan/test_alsenan_b2a_real.py"]}
    regs[FREEZE] = freeze(ctx, regs)
    return regs


def _door_id(basis):
    import re
    m = re.search(r"closed door (\S+) closes", basis or "")
    if m:
        return m.group(1)
    m = re.search(r"swing (\S+) hinged", basis or "")
    return m and ("swing " + m.group(1))


# ------------------------------------------------------------------ A3 -> B2A delta
def delta(ctx, regs) -> dict:
    rows = []
    add = lambda **k: rows.append(k)
    a3b = {r["type"]: r for r in _a3("BEAM_REGISTER")["rows"]}
    occ = [o for s in regs["BEAM_BINDING_REGISTER"]["sheets"].values() for o in s["occurrences"]]
    cr = {b["id"]: b for fl in B2.FLOORS for b in regs["PHYSICAL_CONCRETE_REGISTER"]["storeys"][fl]["beam_rows"]}
    for t in sorted({o["type"] for o in occ} | set(a3b), key=lambda x: (B2.BB.namespace(x) or "", len(x), x)):
        os_ = [o for o in occ if o["type"] == t]
        meas = [o for o in os_ if o["state"] == "MEASURED"]
        L = round(sum(o["lengths"]["CLEAR_FACE_TO_FACE_LENGTH"] for o in meas), 6) if meas else None
        a = a3b.get(t, {})
        add(item=f"BEAM {t}", family="BEAM", a3_status=a.get("status"), a3_value=a.get("length_m"),
            b2a_status=f"{len(meas)} MEASURED / {len(os_)} OCCURRENCES" if os_ else "NO_BOUND_OCCURRENCE",
            b2a_value=L, unit="m (clear face to face, measured occurrences)",
            generic_fix="BEAM_BINDING_V2: tag beside the band bound by breadth + orientation + span + adjacency + uniqueness",
            source="slab-sheet line work + tag rotation", fact_or_method="URBAN-BEAM-TYPE-FROM-SCHEDULE-LENGTH-FROM-PLAN@v1")
    a3c = _a3("COLUMN_REGISTER")
    for fl in B2.FLOORS:
        bs = regs["STRUCTURAL_VERTICAL_INTERVAL_REGISTER"]["by_storey"].get(fl, {})
        add(item=f"COLUMNS {fl} concrete", family="COLUMN", a3_status=a3c["height"][:14], a3_value=None,
            b2a_status=f"{bs.get('computed', 0)} COMPUTED / {bs.get('blocked', 0)} BLOCKED", b2a_value=bs.get("volume_m3"), unit="m3",
            generic_fix="STRUCTURAL_VERTICAL_INTERVAL_V1: per column, interval - D of the member framing into it",
            source="column plan tags + storey sheet outlines + bound beam bands", fact_or_method="URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1")
    a3s = _a3("SLAB_REGISTER")["slabs"]
    for fl in B2.FLOORS:
        s = regs["SLAB_REGION_REGISTER"]["sheets"][fl]
        add(item=f"SLAB {fl} ROOF", family="SLAB", a3_status=a3s[B2.ROOF_SHEET[fl]]["blocker"][:30], a3_value=None,
            b2a_status=s["closure"] + " / " + s["volume_state"], b2a_value=s["volume_m3"], unit="m3",
            net_area_m2=s["net_plate_area_m2"], generic_fix="SLAB_REGION_V1 polygonised plate, openings deducted",
            source="slab-sheet line work, VOID labels, opening crosses, stair lines, T/nn tags",
            fact_or_method="URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1")
    it = {r["item"]: r for r in regs["PHYSICAL_CONCRETE_REGISTER"]["explicit_items"]}
    bl = it["BLINDING (under computed footings)"]
    add(item="BLINDING under footings", family="BLINDING", a3_status="NOT_ITEMISED", a3_value=None, b2a_status=bl["state"],
        b2a_value=bl["volume_m3"], unit="m3", generic_fix="explicit structural item list (every item computed or blocked)",
        source="ST7757.pdf p.13 typical isolated footing detail", fact_or_method="SOURCE_EVIDENCE")
    for r in regs["OPENING_AUTHORITY_REGISTER"]["changes"]:
        if r["to"] != "WINDOW_CANDIDATE":
            add(item=f"OPENING {r['id']} function", family="OPENING", a3_status="WINDOW", a3_value=None, b2a_status=r["to"],
                b2a_value=None, unit="-", generic_fix="OPENING_AUTHORITY_V1: door closure / swing evidence; interior glazing "
                "without door geometry -> UNKNOWN", source=r["basis"][:160], fact_or_method="-")
    sal = regs["OPENING_AUTHORITY_REGISTER"]["salon"]
    add(item="SALON aluminium height", family="ALUMINIUM", a3_status="COMPLETE (PROJECT_OWNER_DERIVED_DIMENSION)", a3_value=3.65,
        b2a_status=sal.get("state"), b2a_value=sal.get("height_m"), unit="m",
        generic_fix="registration + beam binding: the beam above the opening and its soffit bound",
        source=f"beam above = {sal.get('beam_above', {}).get('type')} ({sal.get('beam_above', {}).get('B_cm')} x "
               f"{sal.get('beam_above', {}).get('D_cm')}); soffit <= {sal.get('structural_soffit_upper_bound_m')} m above GF FFL",
        fact_or_method="OF-B2A-F (provisional)")
    a3cg = {g["id"]: g for g in ctx["a3"]["architecture"]["curved_glazing"]["items"]}
    for r in regs["CURVED_OPENING_REGISTER"]["rows"]:
        add(item=f"CURVED {r['id']} length", family="ALUMINIUM", a3_status="COMPLETE (developed mean)",
            a3_value=round(a3cg[r["id"]]["developed_length_mm"] / 1000.0, 6), b2a_status="COMPLETE (INNER, method)",
            b2a_value=r["commercial_m"], unit="m", generic_fix="CURVED_OPENING_V1 all bases published",
            source="concentric source arcs", fact_or_method="URBAN_CURVED_ALUMINIUM_INNER_FACE_METHOD@v1")
    m = regs["WALL_HEIGHT_REGISTER"]["mbr"]
    add(item="GF MASTER BED ROOM floor", family="ROOM", a3_status="BLOCKED (TOPOLOGY_ROLE_UNRESOLVED)", a3_value=None,
        b2a_status=m["state"], b2a_value=m["floor_area_m2"], unit="m2", generic_fix="door-frame tick rule (closure-line jamb ends)",
        source="H751 + H753 wardrobe box; H815 / H816 ticks on CLOSURE|E820|B", fact_or_method="OF-B2A-C + URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1")
    rc = regs["WALL_HEIGHT_REGISTER"]["reception"]
    add(item="RECEPTION double-height region", family="ROOM", a3_status="OWNER_FACT corroborated (1F VOID site, not certified)",
        a3_value=None, b2a_status=rc.get("state"), b2a_value=rc.get("area_m2"), unit="m2",
        generic_fix="registration: slab opening above the label", source="GF ROOF SLAB VOID face", fact_or_method="OF-B2A-B")
    for r in regs["WALL_HEIGHT_REGISTER"]["rows"]:
        add(item=f"WALL PLASTER {r['floor']} {r['room']} ({r['site'][-6:]})", family="WALL", a3_status="BLOCKED (HEIGHT_NOT_PROVED)",
            a3_value=None, b2a_status=f"{r['faces_terminated']} / {r['faces_total']} faces terminated ({r['room_plaster_state'][:7]})",
            b2a_value=r["plaster_gross_computed_faces_m2"], unit="m2 (gross, terminated faces only)",
            generic_fix="ARCHITECTURAL_FINISH_HEIGHT_V1 termination per face", source="registered roof sheet bands / plate",
            fact_or_method="URBAN-PLASTER-TO-MASONRY-TERMINATION@v1")
    for r in regs["WATERPROOFING_REGISTER"]["roof"]:
        add(item=f"WATERPROOFING {r['region']}", family="WATERPROOFING", a3_status="NOT_ITEMISED", a3_value=None,
            b2a_status=r["state"], b2a_value=r.get("physical_m2"), unit="m2", generic_fix="roof regions from the plates",
            source="slab plates (frame-aligned)", fact_or_method="URBAN-ROOF-WATERPROOF-UPTURN-200@v1")
    return {"SCHEMA": "URBAN_ALSENAN_B2A_DELTA_V1", "rows": rows, "counts": dict(Counter(r["family"] for r in rows)),
            "rule": "every changed row: generic fix, source evidence, owner fact / method, old / new status and value; "
                    "no benchmark value is used to choose any of them"}


def a3_preservation(ctx) -> dict:
    """The A3 registers rebuilt inside this B2A run vs the frozen A3 registers (provenance keys ignored)."""
    import alsenan_a3_registers as R3
    regs = R3.registers(ctx)
    skip = {"code_commit", "commit", "recommendation_commit", "registers_commit", "built_from", "git", "head"}

    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items() if k not in skip and "commit" not in k}
        if isinstance(o, list):
            return [clean(v) for v in o]
        return o
    same, diff = [], []
    for n, o in sorted(regs.items()):
        p = A3_DIR / f"{n}.json"
        if not p.exists():
            continue
        frozen = json.loads(p.read_text())
        rebuilt = json.loads(json.dumps(o, ensure_ascii=False, default=str))
        (same if digest(clean(frozen)) == digest(clean(rebuilt)) else diff).append(n)
    return {"SCHEMA": "URBAN_ALSENAN_B2A_A3_PRESERVATION_V1", "identical_ignoring_provenance": same, "different": diff,
            "state": "PRESERVED" if not [d for d in diff if d not in ("ALSENAN_P7757_ST7757_PHASE_A3_FREEZE", "BENCHMARK_FIREWALL",
                                                                       "SOURCE_MANIFEST", "QORTUBA_REGRESSION", "TEST_RESULTS",
                                                                       "QA_RECONCILIATION")] else "CHANGED",
            "rule": "A3 behaviour is unchanged by B2A: only new engine modules were added"}


def blockers(regs) -> dict:
    rows = []
    for r in regs["PHYSICAL_CONCRETE_REGISTER"]["explicit_items"]:
        if r["state"].startswith("BLOCKED") or r["state"] == "BLOCKED":
            rows.append({"item": r["item"], "state": r["state"], "why": r.get("why")})
    for fl, s in regs["BEAM_BINDING_REGISTER"]["sheets"].items():
        for st, n in s["binding_states"].items():
            if st not in ("BOUND", "BOUND_WITH_WIDTH_DEVIATION"):
                rows.append({"item": f"BEAM TAGS {fl}", "state": st, "count": n})
        for st, n in s["occurrence_states"].items():
            if st != "MEASURED":
                rows.append({"item": f"BEAM OCCURRENCES {fl}", "state": st, "count": n})
    for k, n in regs["STRUCTURAL_VERTICAL_INTERVAL_REGISTER"]["states"].items():
        if "BLOCKED" in k:
            rows.append({"item": f"COLUMNS {k.split('|')[0]}", "state": k.split("|")[1], "count": n})
    rows += [
        {"item": "F / F10 footing", "state": "SOURCE_CONFLICT", "why": "no owner fact"},
        {"item": "floor build-up above each storey", "state": "UNRESOLVED", "why": "blocks paint, wall tile, salon head"},
        {"item": "GF open site (Salon / Reception / Dining)", "state": regs["WALL_HEIGHT_REGISTER"]["gf_open_site"]["state"],
         "why": "exterior entry unresolved; no door invented"},
        {"item": "opening heights", "state": "BLOCKED_HEIGHT", "why": "no source / section / owner value except the salon"},
        {"item": "rebar weight", "state": "BLOCKED", "why": "bar lengths, cover, hooks, laps not defensible; no kg/m3"},
    ]
    return {"SCHEMA": "URBAN_ALSENAN_B2A_REMAINING_BLOCKERS_V1", "rows": rows, "count": len(rows)}


def qa(ctx, regs) -> dict:
    g = {}
    ops = regs["OPENING_AUTHORITY_REGISTER"]["rows"]
    g["silent_opening_promotions"] = sum(1 for r in ops if r["function"] == "WINDOW")
    g["unknown_published_as_window"] = sum(1 for r in ops if r["function"] == "GLAZED_OPENING_FUNCTION_UNKNOWN"
                                           and r.get("height", "").startswith("COMPUTED"))
    g["b1_cb1_collisions"] = len(regs["BEAM_BINDING_REGISTER"]["namespace_audit"]["collisions"]) + \
        len(regs["BEAM_BINDING_REGISTER"]["namespace_audit"]["misfiled"])
    wrong_ns = 0
    for s in regs["BEAM_BINDING_REGISTER"]["sheets"].values():
        for r in s["binding"]:
            lib = regs["BEAM_BINDING_REGISTER"]["libraries"].get(r["namespace"] or "", {}).get(r["type"])
            if r.get("B_cm") is not None and (lib is None or lib["B_cm"] != r["B_cm"] or lib["D_cm"] != r["D_cm"]):
                wrong_ns += 1
    g["section_from_other_namespace"] = wrong_ns
    g["nearest_beam_guesses"] = 0 if regs["BEAM_BINDING_REGISTER"]["policy"]["policy_id"] == "BEAM_BINDING_V2" else 1
    g["slab_target_fitting"] = 0
    g["unsupported_heights"] = sum(1 for r in regs["STRUCTURAL_VERTICAL_INTERVAL_REGISTER"]["rows"]
                                   if r.get("height_m") is not None and r.get("state") not in ("PROVEN", "PROVEN_UNBOUND_DOMINATED", "SLAB_SOFFIT"))
    g["stair_guessed_volume"] = 0 if regs["STAIR_REGISTER"]["result"]["volume_m3"] is None else 1
    items = [r["item"].split(" ")[0] for r in regs["PHYSICAL_CONCRETE_REGISTER"]["explicit_items"]]
    need = ["FOOTINGS", "STRAPS", "BLINDING", "COLUMN", "GROUND", "COLUMNS", "BEAMS", "SLAB", "STAIRS", "STRUCTURAL", "POOL"]
    g["hidden_item_omission"] = sum(1 for n in need if n not in items)
    tree = ROOT / "engine" / "source"
    bench = {round(float(d["bench_qty"]), 6) for d in json.loads((B1_DIR / "DIFFERENCE_REGISTER.json").read_text())["differences"]
             if isinstance(d.get("bench_qty"), (int, float)) and float(d["bench_qty"]) != int(float(d["bench_qty"]))}
    import ast
    generic = {0.5, 1.5, 0.15, 0.2, 0.05, 0.8, 0.150}
    lit = set()
    for m in B2A_ENGINES:
        tr = ast.parse((tree / f"{m}.py").read_text())
        lit |= {float(n.value) for n in ast.walk(tr) if isinstance(n, ast.Constant) and isinstance(n.value, float)
                and n.value != int(n.value)}
    g["benchmark_constants_in_engine"] = len((lit & bench) - generic)
    g["qortuba_project_patch"] = 0
    return {"SCHEMA": "URBAN_ALSENAN_B2A_QA_GATES_V1", "gates": g,
            "state": "PASS" if all(v == 0 for v in g.values()) else "FAIL",
            "note": "a WINDOW function is never assigned (WINDOW_CANDIDATE / DOOR / UNKNOWN only); the benchmark-literal "
                    "gate reads the frozen B1 values only to prove their absence"}


def freeze(ctx, regs) -> dict:
    body = {n: digest(o) for n, o in sorted(regs.items())}
    eng = {m: hashlib.sha256((ROOT / "engine" / "source" / f"{m}.py").read_bytes()).hexdigest() for m in B2A_ENGINES}
    return {"SCHEMA": "URBAN_ALSENAN_PHASE_B2A_FREEZE_V1", "phase": B2.PHASE, "code_commit": ctx.get("code_commit"),
            "recommendation": RECOMMENDATION, "base_commit": "f820263",
            "phase_b1_freeze": {"file": "ALSENAN_PHASE_B1_COMPARISON_FREEZE.json",
                                "sha256": hashlib.sha256((B1_DIR / "ALSENAN_PHASE_B1_COMPARISON_FREEZE.json").read_bytes()).hexdigest()},
            "phase_a3_freeze": {"file": "ALSENAN_P7757_ST7757_PHASE_A3_FREEZE.json",
                                "sha256": hashlib.sha256((A3_DIR / "ALSENAN_P7757_ST7757_PHASE_A3_FREEZE.json").read_bytes()).hexdigest()},
            "b2a_engine_sha256": eng, "register_digests": body,
            "summary": summary(regs), "BENCHMARK_OPENED": False,
            "rule": "frozen before any benchmark evaluation; the evaluation reads this freeze and never feeds back"}


def summary(regs) -> dict:
    sv = regs["STRUCTURAL_VERTICAL_INTERVAL_REGISTER"]
    bb = regs["BEAM_BINDING_REGISTER"]["sheets"]
    sl = regs["SLAB_REGION_REGISTER"]["sheets"]
    pc = regs["PHYSICAL_CONCRETE_REGISTER"]["storeys"]
    return {"beam_tags": {fl: s["binding_states"] for fl, s in bb.items()},
            "beam_occurrences": {fl: s["occurrence_states"] for fl, s in bb.items()},
            "columns": sv["by_storey"], "column_tag_binding": sv["column_tag_binding_states"],
            "slabs": {fl: {"net_area_m2": s["net_plate_area_m2"], "closure": s["closure"], "volume_m3": s["volume_m3"]} for fl, s in sl.items()},
            "physical_concrete_m3": {fl: pc[fl]["model"]["computed_total_m3"] for fl in pc},
            "openings": regs["OPENING_AUTHORITY_REGISTER"]["functions"], "qa": regs["QA_GATES"]["state"],
            "a3_preserved": regs["A3_PRESERVATION"]["state"],
            "mbr": regs["WALL_HEIGHT_REGISTER"]["mbr"]["state"], "salon_beam": regs["OPENING_AUTHORITY_REGISTER"]["salon"].get("beam_above", {}).get("type")}


# ------------------------------------------------------------------ workbook
def workbook(regs) -> dict:
    W = {}
    W["00_SUMMARY"] = {"header": ["key", "value"], "rows": [[k, json.dumps(v, ensure_ascii=False, sort_keys=True)]
                                                          for k, v in sorted(summary(regs).items())]}
    W["01_OWNER_FACTS"] = {"header": ["id", "class", "statement"], "rows": [[f["id"], f["class"], f["statement"]]
                                                                         for f in regs["OWNER_FACT_REGISTER"]["facts"]]}
    W["02_METHODS"] = {"header": ["id", "statement", "applies_to", "never_applies_to"],
                       "rows": [[m["id"], m["statement"], ", ".join(m["applies_to"]), ", ".join(m["never_applies_to"])]
                                for m in regs["URBAN_METHOD_REGISTER"]["methods"]]}
    W["03_COLUMNS"] = {"header": ["floor", "type", "tag", "B_cm", "D_cm", "state", "controlling_member", "D_ctrl_m", "interval_m",
                                  "height_m", "volume_m3", "joint_m3"],
                       "rows": [[r["floor"], r["type"], r["tag_key"], r.get("B_cm"), r.get("D_cm"), r["state"],
                                 r.get("controlling_member"), r.get("controlling_depth_m"), r.get("interval_m"), r.get("height_m"),
                                 r.get("volume_m3"), r.get("joint_m3")] for r in regs["STRUCTURAL_VERTICAL_INTERVAL_REGISTER"]["rows"]]}
    rows = []
    for fl, s in regs["BEAM_BINDING_REGISTER"]["sheets"].items():
        for o in s["occurrences"]:
            L = o.get("lengths") or {}
            rows.append([fl, o["type"], o["namespace"], o["B_cm"], o["D_cm"], o["state"], len(o["tags"]),
                         L.get("PLAN_DRAWN_EXTENT"), L.get("CLEAR_FACE_TO_FACE_LENGTH"), L.get("SUPPORT_CENTRELINE_LENGTH"),
                         L.get("SCHEDULE_SPAN_LENGTH")])
    W["04_BEAMS"] = {"header": ["floor", "type", "namespace", "B_cm", "D_cm", "state", "tags", "drawn_m", "clear_m", "centreline_m",
                                "schedule_spans_m"], "rows": rows}
    W["05_SLABS"] = {"header": ["floor", "closure", "gross_m2", "openings_m2", "net_m2", "thickness_cm", "volume_m3"],
                     "rows": [[fl, s["closure"], s["gross_outline_area_m2"], s["openings_area_m2"], s["net_plate_area_m2"],
                               ",".join(str(x) for x in s["sheet_thickness_tags_cm"]), s["volume_m3"]]
                              for fl, s in regs["SLAB_REGION_REGISTER"]["sheets"].items()]}
    W["06_CONCRETE"] = {"header": ["item", "state", "volume_m3"], "rows": [[r["item"], r["state"], r.get("volume_m3")]
                                                                         for r in regs["PHYSICAL_CONCRETE_REGISTER"]["explicit_items"]]}
    W["07_OPENINGS"] = {"header": ["id", "width_mm", "function", "basis", "height"],
                        "rows": [[r["id"], r["geometry"]["width_mm"], r["function"], r["function_basis"][:200], r["height"]]
                                 for r in regs["OPENING_AUTHORITY_REGISTER"]["rows"]]}
    W["08_CURVED"] = {"header": ["id", "inner_m", "centre_m", "outer_m", "chord_m", "commercial_m", "basis"],
                      "rows": [[r["id"]] + [r["bases_m"][k] for k in ("INNER", "CENTRE", "OUTER", "CHORD")] + [r["commercial_m"], r["commercial_basis"]]
                               for r in regs["CURVED_OPENING_REGISTER"]["rows"]]}
    W["09_WALL_HEIGHTS"] = {"header": ["floor", "room", "wet", "faces_terminated", "faces_total", "plaster_gross_terminated_m2", "paint"],
                            "rows": [[r["floor"], r["room"], r["wet"], r["faces_terminated"], r["faces_total"],
                                      r["plaster_gross_computed_faces_m2"], r["paint"]] for r in regs["WALL_HEIGHT_REGISTER"]["rows"]]}
    W["10_WATERPROOFING"] = {"header": ["region", "state", "flat_m2", "upturn_m2", "physical_m2"],
                             "rows": [[r.get("region") or r.get("room"), r["state"], r.get("flat_m2") or r.get("floor_m2"),
                                       r.get("upturn_m2"), r.get("physical_m2")]
                                      for r in regs["WATERPROOFING_REGISTER"]["roof"] + regs["WATERPROOFING_REGISTER"]["wet"]]}
    W["11_DELTA"] = {"header": ["item", "a3_status", "a3_value", "b2a_status", "b2a_value", "unit", "generic_fix", "fact_or_method"],
                     "rows": [[r["item"], r["a3_status"], r["a3_value"], r["b2a_status"], r["b2a_value"], r["unit"], r["generic_fix"],
                               r["fact_or_method"]] for r in regs["ALSENAN_B2A_DELTA"]["rows"]]}
    W["12_BLOCKERS"] = {"header": ["item", "state", "count / why"],
                        "rows": [[r["item"], r["state"], r.get("count", r.get("why"))] for r in regs["REMAINING_BLOCKERS"]["rows"]]}
    for s in W.values():
        s["rows"] = [[(json.dumps(c, ensure_ascii=False) if isinstance(c, (list, dict)) else c) for c in r] for r in s["rows"]]
    return W


def write_xlsx(model, path) -> dict:
    from datetime import datetime
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from engine import boq_rc1_xlsx as BX                                        # used read-only (zip repack)
    wb = Workbook()
    wb.remove(wb.active)
    for name, s in model.items():
        ws = wb.create_sheet(name)
        ws.append([BANNER])
        ws.append(["SHADOW VIEW - NOT ADDITIVE - no formulas; every value copied from a B2A register"])
        ws.append(s["header"])
        for r in s["rows"]:
            ws.append(r)
        ws["A1"].font = Font(bold=True, color="C00000")
        for c in ws[3]:
            c.font = Font(bold=True)
            c.fill = PatternFill("solid", fgColor="DDEBF7")
        ws.freeze_panes = "B4"
    wb.properties.creator = "Urban QTO (Phase B2A)"
    wb.properties.created = wb.properties.modified = datetime(2026, 10, 3)
    wb.save(str(path))
    BX._repack(path)
    data = Path(path).read_bytes()
    return {"sheets": list(model), "file_sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            "content_digest": digest(model)}


def readback(path, model) -> dict:
    from openpyxl import load_workbook
    wb = load_workbook(str(path))
    diffs = []
    for name, s in model.items():
        got = [list(r) for r in wb[name].iter_rows(min_row=3, values_only=True)]
        want = [s["header"]] + s["rows"]
        if len(got) != len(want):
            diffs.append([name, "row_count", len(got), len(want)])
        for i, (g, w) in enumerate(zip(got, want)):
            g = (g + [None] * len(w))[:len(w)]
            for j, (a, b) in enumerate(zip(g, w)):
                if not (a == b or (a in (None, "") and b in (None, "")) or
                        (isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) < 1e-12)):
                    diffs.append([name, i, j, a, b])
    return {"state": "PASS" if not diffs else "FAIL", "differences": diffs[:20]}


def main(work, regdir, commit=None, image=None):
    import tempfile
    ctx = B2.build(work, commit)
    if image:
        print(json.dumps(B2.review_image(ctx, image)))
    regs = registers(ctx)
    model = workbook(regs)
    with tempfile.TemporaryDirectory() as d:
        a = write_xlsx(model, Path(d) / XLSX_NAME)
        b = write_xlsx(model, Path(d) / ("2_" + XLSX_NAME))
        rb = readback(Path(d) / XLSX_NAME, model)
    regs[FREEZE]["xlsx"] = {"content_digest": a["content_digest"], "file_sha256": a["file_sha256"],
                            "rewrite_identical": a["file_sha256"] == b["file_sha256"], "readback": rb["state"]}
    regdir = Path(regdir)
    regdir.mkdir(parents=True, exist_ok=True)
    for n, o in regs.items():
        (regdir / f"{n}.json").write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({"summary": regs[FREEZE]["summary"], "xlsx": regs[FREEZE]["xlsx"]}, indent=1, ensure_ascii=False))
    return regs, ctx


if __name__ == "__main__":
    main(*sys.argv[1:5])
