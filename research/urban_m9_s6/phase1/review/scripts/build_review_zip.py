"""Build the S6 Phase 1 independent-review package: a public-safe ZIP and a PRIVATE ZIP (client-derived evidence).
usage: python3 -I build_review_zip.py REPO SCRATCH OUT_DIR COMMIT
Text-first: every file is .md / .csv / .json / .py / .patch / .txt / .dxf / .svg, except one PNG crop (private).
"""
import hashlib, json, re, subprocess, sys, zipfile
from pathlib import Path

REPO, S, OUT, COMMIT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
R, P1 = S / "review", S / "s6p1"
PUB_TOP, PRIV_TOP = "URBAN_M9_S6_PHASE1_INDEPENDENT_REVIEW", "PRIVATE_DO_NOT_COMMIT"
S5, S6R = "6eba0d2", "6b7a2e4"
HYG = re.compile("YEARS" + r" 2013|7757-[A-Z]|(?i:als[ey]?n[ya]?an)|(?i:qortuba|alrashed|al-rashed|adailiya)|ae608411|d025d9f0"
                 r"|restore_zip_extract|P7757\.dxf|Source_Restore")
ARAB = re.compile("[؀-ۿ]{3,}")
RULE_LINE = 'PATTERN = re.compile("YEARS' + ' 2013'          # the hygiene rule itself (tests/m9_s6/test_s6_hygiene.py)

pub, priv = {}, {}


def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, check=True).stdout


def add(d, top, arc, data):
    d[f"{top}/{arc}"] = data if isinstance(data, bytes) else data.encode("utf-8")


def addp(arc, data):
    add(pub, PUB_TOP, arc, data)


def addv(arc, data):
    add(priv, PRIV_TOP, arc, data)


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------ public: review documents
for p in sorted((R / "pub").glob("*")):
    addp(p.name, p.read_bytes())
addp("12_DEFECT_MATRIX_BEFORE_AFTER.csv", (REPO / "research/urban_m9_s6/phase1/S6P1_01_DEFECT_MATRIX_BEFORE_AFTER.csv").read_bytes())
addp("15_AREA_RECONCILIATION_SYNTHETIC.json", (REPO / "research/urban_m9_s6/phase1/S6P1_05_AREA_RECONCILIATION_SYNTHETIC.json").read_bytes())
# discovery schema + examples
addp("discovery/S6_02_DRAWING_DISCOVERY_SCHEMA.json", (REPO / "research/urban_m9_s6/S6_02_DRAWING_DISCOVERY_SCHEMA.json").read_bytes())
addp("discovery/S6_02_SAMPLE_DISCOVERY_REPORT_SYNTHETIC_VILLA.json",
     (REPO / "research/urban_m9_s6/S6_02_SAMPLE_DISCOVERY_REPORT_SYNTHETIC_VILLA.json").read_bytes())
for p in sorted((REPO / "research/urban_m9_s6/phase1").glob("S6P1_04_*.json")):
    addp(f"discovery/{p.name}", p.read_bytes())
# entity / geometry census (synthetic villa, V2)
syn = P1 / "chk_syn_v2"
disc = json.loads((syn / "DRAWING_DISCOVERY.json").read_text())
rr = json.loads((syn / "RUN_RULES.json").read_text())
census = {"drawing": "synthetic villa (tools/arch_synth), V2 at " + COMMIT,
          "stage_1_inventory": disc["stages"].get("1_inventory"), "stage_6_geometry_readiness": disc["stages"].get("6_geometry_readiness"),
          "documents": disc.get("documents"), "arch_reader": rr["arch"].get("arch_reader")}
addp("14_ENTITY_GEOMETRY_CENSUS_SYNTHETIC.json", json.dumps(census, indent=1) + "\n")
# hashes: frozen V1 (taken at 6b7a2e4) vs V1 now, and V2 outputs (synthetic)
B = json.loads((P1 / "baseline/BASELINE_HASHES.json").read_text())


def hashes(d):
    return {p.name: sha(p.read_bytes()) for p in sorted(d.iterdir()) if p.is_file()}


now_v1 = hashes(P1 / "chk_syn_v1")
hj = {"frozen_v1_taken_at": B.get("head"), "commit": COMMIT,
      "synthetic_v1": {f: {"frozen": h, "now": now_v1.get(f), "identical": now_v1.get(f) == h} for f, h in B["synthetic_v1"].items()},
      "synthetic_v2_outputs": hashes(syn), "rules": B.get("rules"),
      "note": "reference-plan V1 / V2 hashes are in the PRIVATE package"}
hj["synthetic_v1_all_identical"] = all(v["identical"] for v in hj["synthetic_v1"].values())
addp("17_HASHES_V1_V2.json", json.dumps(hj, indent=1) + "\n")
# regression
addp("regression/TEST_GATE_M9_S6P1.json", (REPO / "research/urban_m9_s6/phase1/TEST_GATE_M9_S6P1.json").read_bytes())
for n in ("rep_before", "rep_v1", "rep_v1strict", "rep_v2", "dwg_before", "dwg_v1", "dwg_v1strict", "dwg_v2", "arch_v"):
    if (P1 / f"{n}.txt").exists():
        addp(f"regression/sweep_{n}.txt", (P1 / f"{n}.txt").read_bytes())
# source changed (full files) and dependencies
changed = [l.split("\t")[1] for l in git("diff", "--name-status", S5, COMMIT, "--", "engine", "tools").decode().splitlines()]
for f in changed:
    addp(f"source_changed/{f}", (REPO / f).read_bytes())
mods = [l.strip() for l in (R / "work/deps/modules.txt").read_text().splitlines() if l.strip()]
deps = [m for m in mods if m.startswith(("engine/source/", "tools/")) and m not in changed and not m.endswith("__init__.py")]
private_deps = []
for m in deps:
    b = (REPO / m).read_bytes()
    if HYG.search(b.decode("utf-8", "replace")):
        private_deps.append(m)
        addv(f"source_dependencies_withheld_from_public/{m}", b)
    else:
        addp(f"source_dependencies/{m}", b)
others = [m for m in mods if m not in changed and m not in deps]
addp("source_dependencies/00_DEPENDENCIES.md",
     "# Unchanged modules on the V2 execution path\n\n"
     "The modules below were recorded from `sys.modules` after an in-process `arch --method ARCH_TAKEOFF_V2` run of the synthetic villa.\n\n"
     "## Included here (unchanged since " + S5 + ")\n\n" + "".join(f"- `{m}`\n" for m in deps if m not in private_deps) +
     "\n## Withheld from the public package (a comment carries a project name; the file is in the PRIVATE package)\n\n" +
     "".join(f"- `{m}`\n" for m in private_deps) +
     "\n## Loaded only because `engine/__init__.py` imports them (not used by the architectural path; not included)\n\n" +
     "".join(f"- `{m}`\n" for m in others) + "\n")
# diffs
addp("diff/diff_S5_6eba0d2_to_c757d8a_code.patch", git("diff", S5, COMMIT, "--", "engine", "tools", "tests"))
addp("diff/diff_S5_6eba0d2_to_c757d8a_research_notes.patch", git("diff", S5, COMMIT, "--", "research"))
addp("diff/diff_S6review_6b7a2e4_to_c757d8a_code.patch", git("diff", S6R, COMMIT, "--", "engine", "tools", "tests"))
addp("diff/DIFFSTAT.txt", git("diff", "--stat", S5, COMMIT))
# tests
for p in sorted((REPO / "tests/m9_s6").rglob("*")):
    if p.is_file() and "__pycache__" not in p.parts:
        addp(f"tests/m9_s6/{p.relative_to(REPO / 'tests/m9_s6')}", p.read_bytes())
# investigation A fixtures
for p in sorted((R / "fixtures").rglob("*")):
    if p.is_file():
        addp(f"fixtures_investigation_A/{p.relative_to(R / 'fixtures')}", p.read_bytes())
# scripts
addv("scripts/inspect_pieces.py", (R / "scripts/inspect_pieces.py").read_bytes())    # names the reference plan's segments
for n in ("threshold_probe.py", "qdiff.py", "rfi_audit.py", "m4_lintel_probe.py", "build_review_zip.py"):
    addp(f"scripts/{n}", (R / "scripts" / n).read_bytes())
for p in sorted((REPO / "research/urban_m9_s6/phase1/repro").glob("*.py")):
    addp(f"scripts/phase1_repro/{p.name}", p.read_bytes())
addp("scripts/phase1_repro/v1_snapshot.py", (REPO / "research/urban_m9_s6/phase1/v1_snapshot.py").read_bytes())
# committed phase 1 + S6 review notes
for p in sorted((REPO / "research/urban_m9_s6").glob("*")):
    if p.is_file():
        addp(f"phase1_notes/{p.name}", p.read_bytes())
for p in sorted((REPO / "research/urban_m9_s6/phase1").glob("*")):
    if p.is_file():
        addp(f"phase1_notes/phase1/{p.name}", p.read_bytes())

# ------------------------------------------------------------------ private
for p in sorted((R / "priv").glob("*")):
    addv(p.name, p.read_bytes())
addv("B_RFI_AUDIT_README.md", "# B: the 85-record audit\n\n`B_RFI_AUDIT_85.csv` has one row per BLOCKED_RFI line V2 adds over V1 on the reference plan. "
     "`B_RFI_AUDIT_85.json` holds the same rows plus the summary. The classes and groups are explained in the public "
     "`06_INVESTIGATION_B_RFI_AUDIT.md`. Generated by `scripts/rfi_audit.py V1_OUT V2_OUT CSV JSON`.\n")
addv("C_AREA_RECONCILIATION_REAL.json", (P1 / "private/S6P1_05_AREA_RECONCILIATION_REAL.json").read_bytes())
addv("C_FINISH_COVERAGE_REAL_V2.json", (P1 / "final_real_v2/FINISH_COVERAGE.json").read_bytes())
addv("D_DISCOVERY_REAL_V2.json", (P1 / "final_real_v2/DRAWING_DISCOVERY.json").read_bytes())
addv("D_ENTITY_CENSUS_REAL_V2.json", json.dumps({"arch_reader": json.loads((P1 / "final_real_v2/RUN_RULES.json").read_text())["arch"].get("arch_reader")}, indent=1) + "\n")
for n in ("BOQ_LINES.json", "ARCH_OPENINGS.json", "ARCH_ROOMS.json", "ARCH_PLAN.json", "ARCH_WALLS.json", "ARCH_FLOOR_AREAS.json",
          "UNRESOLVED.json", "DRAWING_DISCOVERY.json", "FINISH_COVERAGE.json", "COVERAGE.json", "MATERIAL_RESULTS.json", "RUN_RULES.json"):
    addv(f"real_v2_outputs/{n}", (P1 / "final_real_v2" / n).read_bytes())
addv("real_v1_outputs/BOQ_LINES.json", (P1 / "chk_real_v1/BOQ_LINES.json").read_bytes())
addv("real_v1_outputs/ARCH_PLAN.json", (P1 / "chk_real_v1/ARCH_PLAN.json").read_bytes())
for p in sorted((P1 / "private/real_v1strict_discovery").glob("*")):
    addv(f"real_v1strict_discovery/{p.name}", p.read_bytes())
for n in ("S6P1_REAL_VARIANTS_BEFORE_HEAD_V1.json", "S6P1_REAL_VARIANTS_V2.json", "S6P1_V1_V2_REAL.json", "S6P1_THRESHOLD_SLACK_EXPERIMENT_REAL.json",
          "00_PRIVATE_README.md"):
    addv(f"phase1_private/{n}", (P1 / "private" / n).read_bytes())
for p in sorted((P1 / "private/test_run").glob("*")):
    addv(f"phase1_private/test_run/{p.name}", p.read_bytes())
addv("phase1_private/test_run/real_plan_tests.log", (P1 / "testrun/real_plan_tests.log").read_bytes())
real = {"frozen_v1_taken_at": B.get("head"), "commit": COMMIT,
        "real_v1": {f: {"frozen": h, "now": hashes(P1 / "chk_real_v1").get(f)} for f, h in B["real_v1"].items()},
        "real_v2_outputs": hashes(P1 / "final_real_v2"), "real_v1strict_outputs": hashes(P1 / "final_real_v1strict")}
for v in real["real_v1"].values():
    v["identical"] = v["frozen"] == v["now"]
real["real_v1_all_identical"] = all(v["identical"] for v in real["real_v1"].values())
addv("HASHES_REAL_V1_V2.json", json.dumps(real, indent=1) + "\n")
addv("00_PRIVATE_README.md", (R / "priv_readme.md").read_bytes())

# ------------------------------------------------------------------ hygiene (public only)
bad = []
for a, b in pub.items():
    text = b.decode("utf-8", "replace")
    lines = [ln for ln in text.splitlines() if RULE_LINE not in ln and "HYG = re.compile" not in ln and "|restore_zip_extract" not in ln]
    if any(HYG.search(ln) for ln in lines):
        bad.append((a, "identity"))
    is_source = "/source_changed/" in a or "/source_dependencies/" in a or "/diff/" in a
    if not is_source and any(ARAB.search(ln) for ln in lines) and not a.endswith(".dxf"):
        bad.append((a, "arabic outside source"))
assert not bad, bad

# ------------------------------------------------------------------ index, all-in-one, sums, zips
docs = sorted(a for a in pub if a.count("/") == 1 and a.endswith(".md") and not a.endswith("00_INDEX.md"))
allin = ["# S6 Phase 1 independent review: all documents in one file\n\nThe same text as the numbered files of the package, concatenated in reading order.\n"]
for a in docs:
    allin.append("\n\n---\n\n<!-- " + a.split("/", 1)[1] + " -->\n\n" + pub[a].decode("utf-8"))
addp("18_ALL_IN_ONE.md", "".join(allin))
idx = (R / "index_head.md").read_text()
rows = "".join(f"| `{a.split('/', 1)[1]}` | {len(b):,} |\n" for a, b in sorted(pub.items()))
addp("00_INDEX.md", idx + "\n## Every file in this package\n\n| File | Bytes |\n|---|---|\n" + rows)
OUT.mkdir(parents=True, exist_ok=True)
for top, d, name in ((PUB_TOP, pub, "URBAN_M9_S6_PHASE1_INDEPENDENT_REVIEW.zip"),
                     (PRIV_TOP, priv, "URBAN_M9_S6_PHASE1_INDEPENDENT_REVIEW_PRIVATE.zip")):
    sums = "".join(f"{sha(b)}  {a.split('/', 1)[1]}\n" for a, b in sorted(d.items()))   # relative to the package folder
    d[f"{top}/SHA256SUMS.txt"] = sums.encode()
    with zipfile.ZipFile(OUT / name, "w", zipfile.ZIP_DEFLATED) as z:
        for a, b in sorted(d.items()):
            zi = zipfile.ZipInfo(a, date_time=(2026, 10, 13, 0, 0, 0))     # fixed: the archive bytes are reproducible
            zi.compress_type, zi.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
            z.writestr(zi, b)
    print(name, len(d), "files", (OUT / name).stat().st_size, "bytes")
print("withheld from public:", private_deps)
