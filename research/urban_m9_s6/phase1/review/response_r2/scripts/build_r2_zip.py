"""Build the S6 review round-2 packages: a public-safe ZIP (the notes in PUB_DIR) and a PRIVATE ZIP (reference-plan
evidence from R2_DIR). Deterministic: fixed entry timestamps and sorted entries.
usage: python3 -I build_r2_zip.py PUB_DIR R2_DIR OUT_DIR REPO
  PUB_DIR  the public notes (R2_*.md / .csv, evidence/, scripts/); also gets its SHA256SUMS.txt written
  R2_DIR   the scratch folder holding the private evidence (priv/, doors/, q5/, Q1_REAL_PLAN_POPULATIONS.json,
           priv_readme.md)
  REPO     the repository (for the benchmark firewall values in its tests)
Gates (public only): the identity rule, Arabic text outside source, and the benchmark firewall (no number within
1e-4 relative of a FORBIDDEN_NUMBERS value at scale 1 / 1e3 / 1e-3)."""
import ast, hashlib, re, sys, zipfile
from pathlib import Path

PUB, R2, OUT, REPO = (Path(a) for a in sys.argv[1:5])
PUB_TOP, PRIV_TOP = "URBAN_M9_S6_R2_RESPONSE", "PRIVATE_DO_NOT_COMMIT"
HYG = re.compile("YEARS" + r" 2013|7757-[A-Z]|(?i:" + "als" + "[ey]?n[ya]?an)|(?i:" + "qor" + "tuba|" + "alra" + "shed|"
                 + "al-ra" + "shed|" + "adai" + "liya)|" + "ae60" + "8411|" + "d025" + "d9f0|" + "restore_zip" + "_extract|"
                 + "P77" + r"57\.dxf|" + "Source" + "_Restore|" + r"D2:\d")
ARAB = re.compile("[؀-ۿ]{3,}")
NUM = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
STAMP = (2026, 10, 13, 0, 0, 0)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def forbidden():
    out = set()
    for t in ("tests/m9_foundation/test_m9_s1_package.py", "tests/structural_comparison_engine/test_rebar_product_firewall.py"):
        for node in ast.walk(ast.parse((REPO / t).read_text(encoding="utf-8"))):
            if isinstance(node, ast.Assign) and any(getattr(x, "id", "") == "FORBIDDEN_NUMBERS" for x in node.targets):
                out |= {float(v) for v in ast.literal_eval(node.value)}
    return out


pub = {p.relative_to(PUB).as_posix(): p.read_bytes() for p in sorted(PUB.rglob("*"))
       if p.is_file() and p.name != "SHA256SUMS.txt" and "__pycache__" not in p.parts}
# ------------------------------------------------------------------ gates on the public notes
FORB, bad = forbidden(), []
for a, b in pub.items():
    text = b.decode("utf-8", "replace")
    for ln in text.splitlines():
        if HYG.search(ln) and "HYG = re.compile" not in ln:
            bad.append((a, "identity"))
        if ARAB.search(ln):
            bad.append((a, "arabic"))
    for m in NUM.finditer(text):
        s = m.group(0).lstrip("-")
        if len(re.sub(r"[^0-9]", "", re.split("[eE]", s)[0]).strip("0")) < 4:
            continue
        v = abs(float(s))
        if v and any(abs(v - x * k) <= 1e-4 * abs(x * k) for x in FORB for k in (1, 1e3, 1e-3)):
            bad.append((a, "firewall"))
assert FORB and not bad, sorted(set(bad))
# ------------------------------------------------------------------ public: sums (also written into PUB_DIR), all-in-one
sums = "".join(f"{sha(b)}  {a}\n" for a, b in sorted(pub.items()))
(PUB / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
order = ["R2_00_README.md", "R2_01_RESPONSE.md", "R2_03_PHASE2A_SCOPE.md", "R2_06_ELIGIBILITY_V0.md",
         "R2_02_ACCEPTANCE_TESTS.csv", "R2_04_CLAIMS_REGISTER.csv"]
allin = ["# S6 review round 2: all documents in one file\n\nThe same text as the files of the package, in reading order "
         "(the two CSV registers are included verbatim at the end).\n"]
for a in order:
    body = pub[a].decode("utf-8")
    allin.append(f"\n\n---\n\n<!-- {a} -->\n\n" + (body if a.endswith(".md") else f"```csv\n{body}```\n"))
zpub = {f"{PUB_TOP}/{a}": b for a, b in pub.items()}
zpub[f"{PUB_TOP}/R2_ALL_IN_ONE.md"] = "".join(allin).encode("utf-8")
zpub[f"{PUB_TOP}/SHA256SUMS.txt"] = "".join(f"{sha(b)}  {a.split('/', 1)[1]}\n" for a, b in sorted(zpub.items())).encode()
# ------------------------------------------------------------------ private
priv = {"00_PRIVATE_README.md": (R2 / "priv_readme.md").read_bytes(),
        "q1/Q1_REAL_PLAN_POPULATIONS.json": (R2 / "Q1_REAL_PLAN_POPULATIONS.json").read_bytes(),
        "q2/Q2_DOOR_EVIDENCE.json": (R2 / "priv" / "Q2_DOOR_EVIDENCE.json").read_bytes(),
        "q2/doors_frozen.json": (R2 / "doors" / "doors_frozen.json").read_bytes(),
        "q2/doors_robust.json": (R2 / "doors" / "doors_robust.json").read_bytes(),
        "q3/Q3_LEDGER_REAL.json": (R2 / "priv" / "Q3_LEDGER_REAL.json").read_bytes(),
        "q3/Q3_LEDGER_REAL.csv": (R2 / "priv" / "Q3_LEDGER_REAL.csv").read_bytes(),
        "q4/Q4_DIMENSION_CENSUS_REAL.json": (R2 / "priv" / "Q4_DIMENSION_CENSUS_REAL.json").read_bytes()}
for p in sorted((R2 / "priv").glob("*.png")):
    priv[f"q2/crops/{p.name}"] = p.read_bytes()
for n in ("rebuild_py311.log", "rebuild_py313.log", "rebuild_py313_isolated.json", "rebuild_py313_isolated.log",
          "blast_baseline.log", "blast_mutated.log", "py313_modified_compare.json", "verify_frozen_tests.txt",
          "iso_dome_ring_s8_3.json", "iso_stairs_s8_7c.json"):
    if (R2 / "q5" / n).exists():
        priv[f"q5/{n}"] = (R2 / "q5" / n).read_bytes()
zpriv = {f"{PRIV_TOP}/{a}": b for a, b in priv.items()}
zpriv[f"{PRIV_TOP}/SHA256SUMS.txt"] = "".join(f"{sha(b)}  {a.split('/', 1)[1]}\n" for a, b in sorted(zpriv.items())).encode()
OUT.mkdir(parents=True, exist_ok=True)
for name, d in (("URBAN_M9_S6_R2_RESPONSE.zip", zpub), ("URBAN_M9_S6_R2_RESPONSE_PRIVATE.zip", zpriv)):
    with zipfile.ZipFile(OUT / name, "w", zipfile.ZIP_DEFLATED) as z:
        for a, b in sorted(d.items()):
            zi = zipfile.ZipInfo(a, date_time=STAMP)
            zi.compress_type, zi.external_attr = zipfile.ZIP_DEFLATED, 0o644 << 16
            z.writestr(zi, b)
    print(name, len(d), "files", (OUT / name).stat().st_size, "bytes", sha((OUT / name).read_bytes()))
