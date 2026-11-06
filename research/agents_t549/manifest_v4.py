"""T-549 WIRING MANIFEST V4: the T-538 manifest (V3, pinned) extended by EVERY piece merged after it, up to the pinned
V4 base, on the candidate of record ARCH_TAKEOFF_V3.0.58. Research / integration preparation only (lane I,
non-candidate): nothing here writes a candidate, released, rule, knowledge or registry file; nothing is wired.

R-T549-1 MANIFEST COVERAGE (every villa; provenance F-C-T536-1 / T-538 lesson, this task): a wiring manifest names the
range of merges it covers, (previous manifest base, this manifest base], walked on the FIRST-PARENT line of the working
branch. Every 'Merge agents/task-T-<n>' commit in that range must be a source of the manifest (with its merge commit)
or a declared NO_WIRING piece with its reason; a merged piece missing from the manifest, a source outside the range, or
a source whose merge commit is not the one in the range is refused. The range is pinned, so a later merge never turns
the committed manifest red (it belongs to the next manifest), and the check is built on a synthetic repository in the
tests, never on live board state.

What V4 adds over V3, each from the merged piece's own committed output or its own function (no quantity typed here):
  - T-534 stair bed area: the V3 'both branches' statement resolves to AT_LEAST 35.4313 m2 on the 11 released lines.
  - T-542 stair bed beyond the treads: 11 bedded parts (7 HELD riser lines + 4 landings with no line) = 20.92611 m2,
    each lifting the V7 bed line by line; F-T542-1 GF hall / lobby floor-bed mix travels with the material hold.
  - T-537 r2 R-T498-2 ranged host faces: the two staged glue hosts and the AAC glue group change against V2 / V3.
  - T-533 R-T533-1 0.15 m black-block module HELD: 6 host lines / 15 walls; their 12 staged material lines stay HELD.
  - T-539 R-T539-1 accessory ledgers V2: the V3 'ties +30 / mesh +40.90 / +44.10 NO LINE' becomes 18 + 12 HELD,
    owner 40.90 / drawing 44.20, strip +0, and three proposed line codes.
  - T-541 roof WP reconciliation, T-543 blockwork reconciliation, T-548 statement builder: no line moves; consistency
    against the candidate and V2 stated (F-T549-1).
Every source commit must be an ancestor of HEAD (manifest_t536.check_sources). No private drawing is read here.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load(rel, name):
    p = ROOT / rel
    if str(p.parent) not in sys.path:
        sys.path.insert(0, str(p.parent))
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


M3 = _load("research/agents_t538/manifest_v3.py", "manifest_v3_t549")          # read only
M2, M1 = M3.M2, M3.M1
ManifestError = M3.ManifestError
_r, sha256 = M1._r, M1.sha256

SCHEMA = "URBAN_T549_WIRING_MANIFEST_V4"
OUT_JSON = ROOT / "research/agents_t549/WIRING_MANIFEST_V4.json"
V3_JSON = ROOT / "research/agents_t538/WIRING_MANIFEST_V3.json"
V2_JSON = M3.V2_JSON
T533_WALLS = ROOT / "research/agents_t533/out/WALLS_015_T533.csv"
T533_SUM = ROOT / "research/agents_t533/out/SUMMARY_T533.json"
T534 = ROOT / "research/agents_t534/out/T534_STAIR_BED_RECONCILE.json"
T539_SUM = ROOT / "research/agents_t539/out/SUMMARY_T539.json"
T539_FAM = ROOT / "research/agents_t539/out/LINE_FAMILIES_T539.json"
T541 = ROOT / "research/agents_t541/out/T541_ROOF_WP_RECONCILE.json"
T542 = ROOT / "research/agents_t542/out/T542_STAIR_BED_CLASSES.json"
T543 = ROOT / "research/agents_t543/out/T543_BLOCKWORK_RECONCILE.json"
T548 = ROOT / "research/agents_t548/out/RECONCILED_STATEMENT_T548.json"
T500 = ROOT / "research/agents_t500/out/TILE_BED_MORTAR_T500.csv"
T537_APPLY = "research/agents_t537/t537_apply.py"

# the covered range: (V3 base, V4 base] on the first-parent line of the working branch
V3_BASE = "9c160d22"          # Merge agents/task-T-538 (WIRING MANIFEST V3)
V4_BASE = "3f3b580c"          # Merge agents/task-T-542 (the newest merge when T-549 was claimed)

NEW_PIECES = {
    "T-533": {"merge": "93aba0d6", "gate": "A", "rules": ["R-T533-1"],
              "verdict": "Verifier 2026-11-05T22:12Z GATE A PASS a-h: 0.15 m black-block module HELD after the source "
                         "census (drawings / spec 04220 / Q-75 / supplier / Bayt Al-Omr); scenarios beside only"},
    "T-534": {"merge": "3c772b79", "gate": "A", "rules": ["R-T534-1", "R-T534-2", "R-T534-3"],
              "verdict": "Verifier 2026-11-05T18:05Z GATE A PASS (stands at the 22:05Z merge): Q-53 39.485 -> "
                         "candidate 35.4313 m2 reconciled by cause, residual 0"},
    "T-537": {"merge": "ac3c77b2", "gate": "A", "rules": ["R-T498-2"],
              "verdict": "Verifier 2026-11-06T00:05Z r2 GATE A PASS a-h: ranged lintel host faces; HELD_BY_NAME L_hi by "
                         "measured ceilings; F-T537-1 low end of the 1F host has no proven basis"},
    "T-539": {"merge": "9b754fad", "gate": "A", "rules": ["R-T539-1"],
              "verdict": "Verifier 2026-11-06T00:05Z GATE A PASS a-h: accessory ledgers V2 on END_CENSUS_V3; ties on "
                         "0.15 m walls HELD (R-T533-1)"},
    "T-541": {"merge": "322c1409", "gate": "A", "rules": ["R-T541-1"],
              "verdict": "Verifier 2026-11-05T23:00Z merged: roof WP vs the freelancer by signed component, no "
                         "ENGINE_WRONG; residuals +0.523 m2 / +11.893 lm UNRESOLVED"},
    "T-542": {"merge": "3f3b580c", "gate": "A", "rules": ["R-T542-1", "R-T542-2", "R-T542-3"],
              "verdict": "Verifier 2026-11-06T02:24Z merged: stair bed classes beyond the treads (risers, landings)"},
    "T-543": {"merge": "8e93e987", "gate": "A", "rules": ["R-T543-1"],
              "verdict": "Verifier 2026-11-06T02:20Z merged: B9 blockwork vs the freelancer by component, no "
                         "ENGINE_WRONG"},
    "T-548": {"merge": "42ae2e5f", "gate": "A", "rules": ["R-T548-1"],
              "verdict": "Verifier 2026-11-06T02:22Z merged: reconciled-quantities statement builder (reads T-541 / "
                         "T-534)"},
}
NO_WIRING = {
    "T-541": "reconciliation vs the freelancer: moves no line; consistency with V2 / the candidate checked (F-T549-1)",
    "T-543": "reconciliation vs the freelancer: moves no line; engine figures equal the candidate MAS.BLOCK lines",
    "T-548": "statement builder: moves no line; re-run after each package (its roof rows hold after F steps 1-2)",
}
PIECES = dict(M3.PIECES, **NEW_PIECES)
NOT_SOURCES = {
    "T-498": "agents/task-T-498 @ e3e2ebb5 stage (BLOCKED on the wrapper allow-list): line ids and states only, no "
             "figure read",
}

RULE_COVERAGE = (
    "R-T549-1 MANIFEST COVERAGE (every villa; provenance F-C-T536-1 / T-538, T-549): a wiring manifest names its range "
    "(previous manifest base, this base] on the first-parent line; every 'Merge agents/task-T-<n>' in it is a source "
    "with that merge commit or a declared NO_WIRING piece with its reason; a merged piece missing from the manifest, a "
    "source outside the range or with another merge commit is refused. The range is pinned: a later merge belongs to "
    "the next manifest and never turns this one red.")

MERGE_RE = re.compile(r"^Merge (?:branch '|remote-tracking branch 'origin/)?agents/task-(T-\d+)'?(?::|\b)")


# ------------------------------------------------------------------------------------------------- pins / coverage
def v3_manifest():
    if sha256(V3_JSON) != V3_PIN:
        raise ManifestError(f"PIN: {V3_JSON.name} sha256 {sha256(V3_JSON)[:8]} is not the pinned {V3_PIN[:8]}")
    return json.loads(V3_JSON.read_text(encoding="utf-8"))


V3_PIN = "8d524c53e952ba9128c33dbed6c9243f587925278605b8225315943a34eb0ab2"     # the merged V3 (9c160d22)


def _git(root, *a):
    r = subprocess.run(["git", "-C", str(root), *a], capture_output=True)
    if r.returncode != 0:
        raise ManifestError(f"COVERAGE: git {' '.join(a[:2])} failed ({r.stderr.decode().strip()[:80]})")
    return r.stdout.decode()


def merges_in_range(base, head, root=None):
    """{task: full merge sha} of the 'Merge agents/task-T-<n>' commits on the first-parent line in (base, head]."""
    root = ROOT if root is None else root
    out = {}
    for ln in _git(root, "log", "--first-parent", "--merges", "--format=%H%x09%s", f"{base}..{head}").splitlines():
        sha, _, subj = ln.partition("\t")
        m = MERGE_RE.match(subj)
        if not m:
            continue
        if m.group(1) in out:
            raise ManifestError(f"COVERAGE: {m.group(1)} merged twice in the range")
        out[m.group(1)] = sha
    return out


def check_coverage(pieces, base=V3_BASE, head=V4_BASE, root=None):
    """R-T549-1: every merge in the range is a piece of the manifest with that merge commit; nothing outside it."""
    found = merges_in_range(base, head, root)
    missing = sorted(set(found) - set(pieces))
    if missing:
        raise ManifestError(f"MISSING_FROM_MANIFEST: {missing} merged in ({base}, {head}] but not in the manifest")
    extra = sorted(set(pieces) - set(found))
    if extra:
        raise ManifestError(f"OUT_OF_RANGE: {extra} are not merges of ({base}, {head}]")
    wrong = sorted(t for t, p in pieces.items() if not found[t].startswith(p["merge"]))
    if wrong:
        raise ManifestError(f"OUT_OF_RANGE: {wrong} name another merge commit than the one in the range")
    return {"range": [base, head], "first_parent_merges": len(found), "covered": sorted(found)}


def _src(*tids):
    return [{"task": t, "merge": PIECES[t]["merge"], "checker": PIECES[t]["verdict"]} for t in tids]


def _csv(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------- T-534 + T-542 stair
V7_RATE = {"bed_m": 0.03, "cement_bags_per_m3": 9.576, "sand_m3_per_m3": 0.9975}     # UP-STAIR-017 via T-528 / T-534


def stair_bed(idx, v3):
    """V3 stated T-534 both ways; T-534 is merged in this tree, so the S / F package applies the 'merged' branch. The
    11 lines are re-read from the candidate (class RELEASED) and from T-534's own B table; the V7 figures from T-534."""
    t = _json(T534)
    b_rel = sorted(l["line_id"] for l in t["B_candidate"]["lines"] if l["class"] == "RELEASED")
    v3s = v3["stair_bed_area"]
    if b_rel != sorted(v3s["lines"]):
        raise ManifestError("T-534 released stair-bed lines are not the V3 / candidate 11 lines")
    area = _r(sum(idx[k]["measured_net"] for k in b_rel), 4)
    v7 = t["v7"]["on_candidate_B"]
    if area != _r(v7["area_m2"], 4) or area != _r(v3s["area_m2"], 4):
        raise ManifestError(f"stair area {area}: candidate, T-534 and V3 disagree")
    if abs(area * V7_RATE["bed_m"] - v7["mortar_m3_low"]) > 1e-6:
        raise ManifestError("V7 mortar is not area x 0.03")
    held = [{"line_id": l["line_id"], "key": l["key"], "class": l["class"]} for l in t["B_candidate"]["lines"]
            if l["class"] != "RELEASED"]
    after = M3.stair_area_state(True, area)
    return {"before_v3": v3s["until_then"], "after": after, "lines": b_rel, "area_m2": area,
            "held_or_excluded_lines": {"HELD": len([h for h in held if h["class"] == "HELD"]),
                                       "EXCLUDED": len([h for h in held if h["class"] == "EXCLUDED"]),
                                       "ids": sorted(h["line_id"] for h in held)},
            "v7_on_it": {"mortar_m3": v7["mortar_m3_low"], "cement_bags_installed": v7["cement_bags_low"],
                         "sand_m3_installed": v7["sand_m3_low"],
                         "procurement": "HELD: F-T518-2 (stair-bed loss scope) still open; the 10.62939 bags "
                                        "allowance and the V7 + Q-45 5 % figure are never stacked"},
            "source": _src("T-534"), "evidence_status": "AT_LEAST (20 HELD + 3 EXCLUDED stair-bed lines named, never 0)"}


def stair_beyond(idx):
    """T-542: the bedded parts with no released candidate line yet. Each is a line-by-line lift of the V7 bed when its
    own marble line is released (riser) or added (landing); the V7 figures beside are area x the V7 rate."""
    t = _json(T542)
    rows = [r for r in t["rows"] if r["bed_class"] == "STAIR_BED" and not r["in_v7_wire"]]
    out, area = [], 0.0
    for r in rows:
        lid = r["line_id"]
        if lid is not None and idx.get(lid, {}).get("class") != "HELD":
            raise ManifestError(f"T-542 {r['key']} {r['surface']}: line {lid} is not HELD on the candidate")
        m3 = _r(r["bed_m2"] * V7_RATE["bed_m"])
        if abs(m3 - r["mortar_m3_low"]) > 1e-6:
            raise ManifestError(f"T-542 {r['key']}: mortar {r['mortar_m3_low']} is not bed x 0.03")
        area += r["bed_m2"]
        out.append({"key": r["key"], "surface": r["surface"], "line_id": lid,
                    "before": {"class": "HELD", "value": None} if lid else {"class": "NO_LINE", "value": None},
                    "lift_when": ("its HELD riser line is released (B7-03, T-412 counts)" if lid else
                                  "its landing line is added (T-502, T-493 F-1 .. F-4)"),
                    "bed_m2": r["bed_m2"], "v7_mortar_m3": m3,
                    "v7_cement_bags": _r(m3 * V7_RATE["cement_bags_per_m3"]),
                    "v7_sand_m3": _r(m3 * V7_RATE["sand_m3_per_m3"]), "status": r["status_label"]})
    s = t["summary"]["beyond_v7_wire"]
    if _r(area) != _r(s["area_m2"]) or len(out) != s["parts"]:
        raise ManifestError(f"T-542 beyond-the-wire {area} / {len(out)} parts is not its summary")
    wire = t["summary"]["in_v7_wire"]
    return {"rule": "R-T542-1 .. 3", "parts": out, "area_m2": _r(area), "risers": len([o for o in out if o["line_id"]]),
            "landings": len([o for o in out if not o["line_id"]]),
            "tolerance_not_wired": {"t542_in_wire_m2": wire["area_m2"], "candidate_lines_m2": 35.4313,
                                    "difference_m2": _r(wire["area_m2"] - 35.4313, 4),
                                    "rule": "the V7 wire is on the candidate line nets; T-542's printed-dimension "
                                            "total carries the 0.0012 polygon TOLERANCE and never replaces them"},
            "never_by_total": "the V7 bed reaches 56.3586 m2 only line by line; no total is wired",
            "source": _src("T-542")}


def floor_bed_mix(idx):
    """F-T542-1: two floor-bed lines released at the dry 1:4 rule under a finish that is HELD (floor or landing). Their
    T-500 binding rows go stale on the MIX when the floor-bed materials are wired: named, both alternatives shown."""
    t = _json(T542)
    fb = {r["floor_bed_line"]: r for r in t["summary"]["landing"]["floor_bed_family_beside"]}
    rows = {r["pair_m2_line"]: r for r in _csv(T500)}
    out = []
    for lid, f in sorted(fb.items()):
        b = rows[lid]
        if idx[lid]["class"] != "RELEASED" or abs(idx[lid]["measured_net"] - float(b["area_m2"])) > 1e-9:
            raise ManifestError(f"{lid}: the T-500 row is not the candidate floor-bed line")
        m3 = _r(float(b["area_m2"]) * V7_RATE["bed_m"])
        out.append({"floor_bed_line": lid, "key": f["key"], "t500_row": b["id"], "area_m2": float(b["area_m2"]),
                    "now_1_4": {"mortar_m3": [float(b["installed_m3_low"]), float(b["installed_m3_high"])],
                                "cement_bags": [float(b["cement_bags_low"]), float(b["cement_bags_high"])],
                                "sand_m3": [float(b["sand_m3_low"]), float(b["sand_m3_high"])]},
                    "if_marble_landing_1_3": {"mortar_m3": m3, "cement_bags": _r(m3 * V7_RATE["cement_bags_per_m3"]),
                                              "sand_m3": _r(m3 * V7_RATE["sand_m3_per_m3"])},
                    "state": "STALE_ON_MIX: the finish is HELD (RFI-B-A12), so the 1:4 dry-floor mix is not "
                             "established; the wiring carries a range covering both mixes or HELD on the mix "
                             "(named, not chosen here)"})
    lo14 = _r(sum(o["now_1_4"]["sand_m3"][0] for o in out))
    s13 = _r(sum(o["if_marble_landing_1_3"]["sand_m3"] for o in out))
    return {"finding": "F-T542-1", "rows": out, "sand_1_4_low_m3": lo14, "sand_1_3_m3": s13,
            "sand_below_1_4_low_m3": _r(lo14 - s13), "source": _src("T-542")}


# ------------------------------------------------------------------------------------------------- T-537 host faces
def host_faces(v2):
    t = _load(T537_APPLY, "t537_apply_t549").build()
    v2h = {h["host_line_id"]: h for h in v2["stream_S"]["host_material_lines"]}
    rows = []
    for h in sorted(t["hosts"], key=lambda x: x["host_line_id"]):
        old = v2h[h["host_line_id"]]
        if old["t498_stage_line"] != h["t498_stage_line"]:
            raise ManifestError(f"{h['host_line_id']}: T-537 and V2 name different stage lines")
        a = h["after_r_t498_2"]
        rows.append({"host_line_id": h["host_line_id"], "t498_stage_line": h["t498_stage_line"],
                     "contract_net_m2": h["contract_net_m2"], "kg_per_m2": h["kg_per_m2"],
                     "v2_expected_after": {"kg_range": old["after"]["kg_range"],
                                           "bags_25kg_range": old["after"]["bags_25kg_range"],
                                           "state": old["after"]["state"]},
                     "v4_expected_after": {"base_m2": a["base"]["base_m2"], "glue_kg": a["glue_kg"],
                                           "bags_25kg_net": a["bags_25kg_net"]},
                     "stale": True, "cause": "R-T498-2 r2: faces D x [L_lo, L_hi], L_hi by measured ceilings; a "
                                             "min-bearing 'max' opens the face (F-T537-1)"})
    g = t["glue_group"]
    if g["t530_after"]["at_least"] != v2["stream_S"]["glue_group"]["after"]["at_least"]:
        raise ManifestError("T-537 glue group 'before' is not the V2 expectation")
    return {"rule": "R-T498-2 1.0.0 r2", "hosts": rows,
            "glue_group": {"v2_expected_after": v2["stream_S"]["glue_group"]["after"],
                           "v4_expected_after": {k: g["after_r_t498_2"][k] for k in ("status", "at_least",
                                                                                     "to_buy_at_least")},
                           "why": "the known part shrinks because the 1F host becomes OPEN (HELD blank), not because "
                                  "less glue is needed"},
            "bindings_stale": sorted(k for k in v2["stale_bindings"]["go_stale_by_this_wiring"] if "glue" in k),
            "source": _src("T-537")}


# ------------------------------------------------------------------------------------------------- T-533 0.15 module
def block_module(idx, v2):
    walls = _csv(T533_WALLS)
    s = _json(T533_SUM)
    hosts = {}
    for w in walls:
        if w["status"] != "HELD" or any(w[k] for k in ("units_nr", "panel_mortar_m3", "cement_bags", "sand_m3")):
            raise ManifestError(f"T-533 {w['wall_id']}: a 0.15 m wall carries a figure")
        hosts.setdefault(w["line_id"], []).append(w)
    out = []
    for lid, ws in sorted(hosts.items()):
        l = idx[lid]
        if l["item_code"] != "MAS.BLOCK" or "t=0.15" not in l["element_id"] or "BLACK" not in l["element_id"]:
            raise ManifestError(f"{lid}: not a 0.15 m black MAS.BLOCK line")
        c = _r(sum(float(w["contract_m2"]) for w in ws), 4)
        if l["class"] != "RELEASED" or abs(c - l["measured_net"]) > 1e-6:
            raise ManifestError(f"{lid}: T-533 walls {c} m2 are not the candidate line {l['measured_net']}")
        out.append({"host_line": lid, "element_id": l["element_id"], "contract_m2": l["measured_net"],
                    "walls": sorted(w["wall_id"] for w in ws),
                    "materials": "units / panel mortar / cement / sand HELD blank by name (R-T533-1); the MAS.BLOCK "
                                 "contract line itself stays RELEASED, unchanged"})
    tot = _r(sum(o["contract_m2"] for o in out), 4)
    if abs(tot - s["contract_m2"]) > 1e-6:
        raise ManifestError(f"T-533 contract {s['contract_m2']} is not the 6 host lines {tot}")
    beside = {p["wall"] for p in v2["stream_S"]["perimeter_held_beside"]}
    miss = sorted({w["wall_id"] for w in walls} - beside)
    if miss:
        raise ManifestError(f"V2 perimeter holds do not name the 0.15 m walls {miss}")
    return {"rule": s["rule"], "result": s["result"], "missing_datum": s["missing_datum"], "host_lines": out,
            "walls": len(walls), "contract_m2": tot, "excluded_walls": s["excluded"],
            "candidate_lines_moved": 0,
            "stage_material_lines": "every T-498 stage MAS.UNITS.BLACK / MAS.MORTAR.BLACK line on these 6 hosts must "
                                    "stay HELD by name with the R-T533-1 datum; a stage figure at 12.5 / m2 (the "
                                    "0.20 m module) on any of them is refused (see stage_check)",
            "t523_bindings": "units_nr / laying_material on the 6 hosts are HELD in T-523 with the same datum: "
                             "consistent, not stale (one STALE_NET read on L-adb393d6, carried from V2)",
            "scenarios_beside": {k: {"units_per_m2": v["units_per_m2"]} for k, v in s["scenarios"].items()},
            "scenario_rule": "S-A / S-B / S-C are beside only; none is a source (never the 0.20 m module)",
            "source": _src("T-533")}


def stage_check(stage_rows, hosts):
    """T-498 stage rows (ids / item / state only): every black units / mortar line on a 0.15 m host is HELD."""
    bad, seen = [], []
    for r in stage_rows:
        if r["source_line_id"] in hosts and r["item_code"] in ("MAS.UNITS.BLACK", "MAS.MORTAR.BLACK"):
            seen.append(r["line_id"])
            if r["state"] not in ("HELD", "BLOCKED_RFI") or r.get("value") is not None:
                bad.append(r["line_id"])
    if bad:
        raise ManifestError(f"R-T533-1: stage lines {bad} carry a 0.15 m black material figure")
    return sorted(seen)


# ------------------------------------------------------------------------------------------------- T-539 accessories
def accessories(idx, v3):
    s, fam = _json(T539_SUM), _json(T539_FAM)
    v3t = v3["end_census_v3"]["ties_and_mesh"]
    end = s["ties_v2_end"]
    held_015 = sum(f["S-A"] for f in s["end_ties"]["held_015_figures"].values())
    if end["ties_measured"] + held_015 != v3t["d_ties_nr"]:
        raise ManifestError("T-539 end ties measured + 0.15 m figures are not the V3 / T-526 +30")
    vj = s["end_vjoint"]
    if vj["owner_m"] != v3t["d_mesh_owner_ml"] or vj["drawing_m_t317_raw"] != v3t["d_mesh_drawing_ml"]:
        raise ManifestError("T-539 V-joint bands do not start from the V3 figures")
    codes = [f["proposed_code"] for f in fam]
    present = sorted({l["item_code"] for l in idx.values()} & (set(codes) | set(M2.TIE_MESH_CODES)))
    if present:
        raise ManifestError(f"accessory codes {present} already carry candidate lines: a new line would double count")
    return {"rule": s["rule"], "v3": {"ties_nr": v3t["d_ties_nr"], "mesh_owner_ml": v3t["d_mesh_owner_ml"],
                                      "mesh_drawing_ml": v3t["d_mesh_drawing_ml"], "state": v3t["state"]},
            "v4_end_ties": {"measured_nr": end["ties_measured"], "measured_ends": s["end_ties"]["measured_ends"],
                            "held_015_by_name": sorted(s["end_ties"]["held_015_figures"]),
                            "held_015_s_a_beside_nr": held_015,
                            "why": "12 of the T-526 +30 were counted on the 0.20 m course over 0.15 m walls (R-T533-1)"},
            "v4_end_vjoint_mesh": {"owner_ml": vj["owner_m"], "drawing_ml_classed": vj["drawing_m_classed"],
                                   "drawing_ml_raw": vj["drawing_m_t317_raw"],
                                   "residual_ml": _r(vj["drawing_m_classed"] - vj["drawing_m_t317_raw"], 4),
                                   "why": "GF-W16 end 0 exterior Sigma side one band 3.75 (classed as R-T355-4) vs raw "
                                          "3.65; neither band chosen (Q-77)"},
            "v4_end_strip_ml": s["end_strip_added_m"],
            "proposed_lines": [{"code": f["proposed_code"], "family": f["family"], "unit": f["unit"],
                                "status": f["status"], "quantity_v2": f["quantity_v2_alsenan"]} for f in fam],
            "candidate_lines_with_these_codes": present, "candidate_lines_moved": 0, "source": _src("T-539")}


# ------------------------------------------------------------------------------------------------- T-541 / T-543 / T-548
def roof_consistency(v2):
    """F-T549-1: T-541 (and T-548 after it) value the roof WP at the F package's EXPECTED after (V2), not at V3.0.58."""
    t = _json(T541)
    cv = v2["stream_F"]["code_views"]
    seven = M1._v3058_t507_lines()
    held = {r["line_id"]: r for r in v2["stream_F"]["lines"] if r["before"]["class"] == "HELD"}
    out = {}
    for key, code in (("membrane", "FIN.WP.ROOF"), ("upturn", "FIN.WP.ROOF_UPTURN")):
        eng = float(t[key]["engine_total"])
        if abs(eng - cv[code]["released_after"]) > 1e-6:
            raise ManifestError(f"T-541 {key} engine {eng} is not the V2 expected after {cv[code]['released_after']}")
        hl = sorted(k for k, r in held.items() if r["item_code"] == code and seven[k]["class"] == "HELD")
        out[key] = {"t541_engine": eng, "candidate_v3_0_58_released": cv[code]["released_before"],
                    "difference": _r(eng - cv[code]["released_before"]),
                    "lines_valued_only_after_wiring": [{"line_id": k, "candidate": "HELD 0 .. %s" %
                                                        seven[k]["held_high"], "v2_after": held[k]["after"]["value"]}
                                                       for k in hl]}
        if abs(sum(x["v2_after"] for x in out[key]["lines_valued_only_after_wiring"]) - out[key]["difference"]) > 1e-6:
            raise ManifestError(f"T-541 {key}: the difference is not the lines held on the candidate")
    st = _json(T548)
    absent = st["provenance"]["valued_lines_not_in_V3_0_57_index"]
    return {"finding": "F-T549-1", **out, "t548_absent_lines": absent,
            "state": "the T-541 / T-548 roof rows hold on the candidate only after F package steps 1-2 (T-522 / "
                     "T-529) wire the ledge membrane and the two upturns; until then their 'engine valued' is the "
                     "expected after, not V3.0.58",
            "candidate_lines_moved": 0, "source": _src("T-541", "T-548")}


def blockwork_consistency(idx):
    t = _json(T543)
    mb = {k: l for k, l in idx.items() if l["item_code"] == "MAS.BLOCK"}
    rel = _r(sum(l["measured_net"] for l in mb.values() if l["class"] == "RELEASED"), 4)
    held = sorted(k for k, l in mb.items() if l["class"] != "RELEASED")
    if abs(rel - float(t["engine_valued_total"])) > 1e-6:
        raise ManifestError(f"T-543 engine {t['engine_valued_total']} is not the candidate MAS.BLOCK released {rel}")
    if sorted(x["line_id"] for x in t["engine_held_lines"]) != held:
        raise ManifestError("T-543 held lines are not the candidate HELD MAS.BLOCK lines")
    return {"engine_valued_m2": rel, "held_lines": len(held), "freelancer_m2": float(t["freelancer_total"]),
            "gap_m2": float(t["gap"]), "by_cause": t["by_cause"], "candidate_lines_moved": 0,
            "state": "consistent with V3.0.58: no line moves; MAS.BLOCK is the host of the S package materials, "
                     "its contract lines never move by materials wiring (R-T453-5)", "source": _src("T-543")}


# ------------------------------------------------------------------------------------------------- packages / build
def packages():
    return {
        "T-498 (S package, stream S)": {
            "needs": ["stair_bed: none", "host_faces (T-537 r2) at step 5", "block_module (T-533) at steps 2 and 7",
                      "groups at step 7 with the V4 glue group"],
            "order": ["1 T-525", "2 T-498 stage (74 material lines; 0.15 m black units / mortar stay HELD, "
                      "R-T533-1)", "3 the 60 lintel bindings (F-T530-1)", "4 lintel lines (V3 basis, T-527)",
                      "5 host faces by R-T498-2 r2 (T-537): GF L-d14c6c9b [23.4459, 23.895] kg, 1F L-4b9a29d4 HELD "
                      "blank, AT_MOST 451.60893 kg beside", "6 perimeter mortar (T-520 = T-526 = T-532)",
                      "7 groups (R-T523-1): AAC glue AT_LEAST 17.643906 .. 18.16227 bags HELD (V2 said 35.387755 .. "
                      "36.226627)", "8 lintel bars: two HELD AT_LEAST lines (V3, T-531)"],
            "blocked_by": "wrapper allow-list (T-498 / T-525)"},
        "T-363 (B9 masonry accessories)": {
            "needs": ["accessories (T-539)"],
            "order": ["1 add MAS.TIE.SHARMAT (B9-06 proposed) 151 measured + 104 junctions HELD",
                      "2 add MAS.MESH.BED_JOINT (B9-07 proposed) 175.4844 m.l, 0.15 m / white walls HELD",
                      "3 MAS.MESH.JOINT (B9-03) per class, owner and drawing bands both shown (Q-77)"],
            "blocked_by": "T-498 (the host material lines first) and the family registry rows for B9-06 / B9-07"},
        "T-372 (B9-04 masonry joints)": {
            "needs": ["block_module (T-533): 0.15 m panel / perimeter mortar HELD"],
            "order": ["after T-363 (worker 1 order); superseded or narrowed by T-506's verdict (Lead 2026-11-04)"],
            "blocked_by": "T-363"},
        "T-513 (BAND_GAP_CLASSES_V1, stream F)": {
            "needs": ["none of the V4 pieces moves a band-gap line"], "order": ["unchanged"],
            "blocked_by": "wrapper allow-list"},
        "F package (V7 stair bed; no board row yet)": {
            "needs": ["stair_bed (T-534)", "stair_beyond (T-542)", "floor_bed_mix (F-T542-1)",
                      "roof_consistency (F-T549-1)"],
            "order": ["1 T-522 window run + ledge pieces", "2 T-529 ledge exposure (the T-541 / T-548 roof rows hold "
                      "from here)", "3 T-517 build-up lines", "4 FINISH V6 reader only",
                      "5 V7 on the 11 released stair lines AT_LEAST 35.4313 m2 (T-534 merged); procurement HELD "
                      "until F-T518-2", "6 each T-542 part lifts V7 when its own line is released / added (T-502 "
                      "landings, B7-03 risers)", "7 floor-bed materials: GF hall / lobby mix with the material hold"],
            "blocked_by": "wrapper allow-list; F-T518-2 for the stair procurement; the Lead names the row"},
    }


def build(stage_rows=None):
    v3 = v3_manifest()
    v2 = M3.v2_manifest()
    M2.check_sources(PIECES)
    cov = check_coverage(NEW_PIECES)
    idx = M1.line_index()
    bm = block_module(idx, v2)
    man = {
        "schema": SCHEMA, "candidate": M1.CANDIDATE, "task": "T-549",
        "supersedes": "T-538 WIRING_MANIFEST_V3.json (V3; every V3 / V2 statement carried unless listed in v3_to_v4)",
        "rule": RULE_COVERAGE, "coverage": cov,
        "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in
                   (V3_JSON, T533_WALLS, T533_SUM, T534, T539_SUM, T539_FAM, T541, T542, T543, T548, T500,
                    ROOT / T537_APPLY)},
        "pieces_new": {k: dict(v) for k, v in sorted(NEW_PIECES.items())},
        "no_wiring": NO_WIRING, "not_sources": NOT_SOURCES,
        "stair_bed": stair_bed(idx, v3),
        "stair_beyond": stair_beyond(idx),
        "floor_bed_mix": floor_bed_mix(idx),
        "host_faces": host_faces(v2),
        "block_module": bm,
        "accessories": accessories(idx, v3),
        "roof_consistency": roof_consistency(v2),
        "blockwork_consistency": blockwork_consistency(idx),
        "packages": packages(),
        "candidate_lines_moved_v3_to_v4": 0, "released_quantities_changed": 0, "candidate_files_touched": 0,
    }
    if stage_rows is not None:
        man["block_module"]["stage_lines_held"] = stage_check(stage_rows, {h["host_line"] for h in bm["host_lines"]})
    man["v3_to_v4"] = v3_to_v4(man)
    man["findings"] = [
        "F-T549-1: T-541 / T-548 value the roof WP at the F package's expected after (V2), 0.639573 m2 / 1.051616 lm "
        "over V3.0.58 on 3 lines still HELD; their rows hold only after F steps 1-2",
        "F-T549-2: V2 expected after of the two staged glue hosts and of the AAC glue group are stale (T-537 r2): the "
        "1F host is HELD blank (AT_MOST 451.60893 kg), the group AT_LEAST 17.643906 .. 18.16227 bags",
        "F-T549-3: V3 'ties +30 nr' is 18 measured + 12 HELD by name (0.15 m module, R-T533-1): a package wiring the V3 "
        "figure would release 12 ties on a module of another thickness",
        "F-T542-1 carried: GF hall / lobby floor-bed rows stale on the mix (range of both mixes or HELD on the mix)",
    ]
    return man


def v3_to_v4(man):
    sf, hf, ac = man["stair_bed"], man["host_faces"], man["accessories"]
    rows = [{"what": "stair bed area (V7)", "v3": sf["before_v3"], "v4": sf["after"], "cause": "T-534 merged"}]
    for h in hf["hosts"]:
        rows.append({"what": f"host glue {h['t498_stage_line']} (stage)", "v3": h["v2_expected_after"],
                     "v4": h["v4_expected_after"]["glue_kg"], "cause": "T-537 r2 R-T498-2"})
    rows.append({"what": "AAC glue group", "v3": hf["glue_group"]["v2_expected_after"],
                 "v4": hf["glue_group"]["v4_expected_after"], "cause": "T-537 r2"})
    rows.append({"what": "column-end ties / mesh", "v3": ac["v3"],
                 "v4": {"ties_measured_nr": ac["v4_end_ties"]["measured_nr"],
                        "ties_held_by_name": ac["v4_end_ties"]["held_015_by_name"],
                        "mesh_owner_ml": ac["v4_end_vjoint_mesh"]["owner_ml"],
                        "mesh_drawing_ml": ac["v4_end_vjoint_mesh"]["drawing_ml_classed"],
                        "strip_ml": ac["v4_end_strip_ml"]}, "cause": "T-539 R-T539-1 (+ R-T533-1)"})
    return rows


def stage_rows_from_branch(ref="origin/agents/task-T-498"):
    """the T-498 stage rows (line id, source, item, state; NO figure read) from its committed summary, if fetched."""
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{ref}:research/agents_t498/summary_t498.json"],
                       capture_output=True)
    if r.returncode != 0:
        return None
    return [{"line_id": x["line_id"], "source_line_id": x["source_line_id"], "item_code": x["item_code"],
             "state": x["after"]["state"], "value": x["after"]["value"]} for x in json.loads(r.stdout)["rows"]]


def dumps(man):
    return M1.dumps(man)


if __name__ == "__main__":
    m = build()
    if "--check" in sys.argv:
        ok = dumps(m) == OUT_JSON.read_text(encoding="utf-8")
        print("CHECK", "OK" if ok else "DIFFERS")
        sys.exit(0 if ok else 1)
    if "--stage" in sys.argv:
        print(json.dumps(stage_check(stage_rows_from_branch() or [], {h["host_line"] for h in
                                                                       m["block_module"]["host_lines"]})))
        sys.exit(0)
    OUT_JSON.write_text(dumps(m), encoding="utf-8")
    print("written", OUT_JSON.relative_to(ROOT))
