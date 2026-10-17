"""REPORTING V2 - build the Alsenan report (first fixture) and the Qortuba render check from the frozen registers.

    python3 research/external_engine_lab/reporting_v2_build.py <out_dir> <registers_commit> [<junit.xml> <rc>]

Writes into <out_dir>/URBAN_QTO_REPORTING_V2/:
    URBAN_QTO_ALSENAN_REPORTING_V2.xlsx / .pdf      the report
    REPORTING_MODEL_V2.json                         the presentation model (every quantity with its register pointer)
    REPORTING_READBACK_QA.json                      XLSX readback + PDF text checks (Alsenan and Qortuba)
    REPORTING_V2_REGRESSION.json                    zero quantity / status change proof (Alsenan, Qortuba)
    REPORTING_V2_FREEZE.json                        input register digests = report sources; output digests
    REPORTING_V2_DESIGN_SPEC.md                     the design spec (docs/REPORTING_V2_DESIGN_SPEC.md)
    REPORTING_V2_TEST_RESULTS.json                  the one full-suite result (when a junit is given)
    qortuba_check/URBAN_QTO_QORTUBA_REPORTING_V2.xlsx / .pdf + REPORTING_MODEL_V2_QORTUBA.json
and <out_dir>/REPORTING_V2.zip. The run date is the commit date of <registers_commit> (not the clock).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import reporting_v2_alsenan as AL                                                                   # noqa: E402
import reporting_v2_qortuba as QO                                                                   # noqa: E402
from engine.reporting_v2 import model as M                                                          # noqa: E402
from engine.reporting_v2 import pdf as P                                                            # noqa: E402
from engine.reporting_v2 import readback as RB                                                      # noqa: E402
from engine.reporting_v2 import xlsx as X                                                           # noqa: E402

NAME = "URBAN_QTO_REPORTING_V2"
LOGO = ROOT / "assets/logo.png"
CAIRO = ROOT / "assets/fonts/Cairo-Variable.ttf"
SPEC = ROOT / "docs/REPORTING_V2_DESIGN_SPEC.md"
FROZEN = ["tests/alsenan/registers_b2a1", "tests/alsenan/registers_a3", "tests/rc1/registers", "engine/source"]


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(*a) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout.strip()


def dumps(o) -> str:
    return json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n"


def pdf_checks(path, model) -> dict:
    import pymupdf
    doc = pymupdf.open(str(path))
    text = "\n".join(pg.get_text() for pg in doc)
    flat = " ".join(text.split())
    order, pos = [], -1
    for s in model["sheets"]:
        if s["role"] == "TECH":
            continue
        i = flat.find(f"{s['name'][:2]}. {s['title_en']}", pos + 1)
        order.append([s["name"], i])
        pos = max(pos, i)
    missing = []
    for ln in model["lines"]:
        q = ln["qty"]["q"]
        shown = P.fmt_num(q, P._cell_fmt(ln["qty"] | {"unit": ln["unit"]}, {"kind": "qty", "unit": ln["unit"]}, "SUMMARY")) \
            if q is not None else "BLOCKED"
        if ln["id"] not in flat or shown not in flat:
            missing.append([ln["id"], shown])
    in_order = all(i >= 0 for _, i in order) and [i for _, i in order] == sorted(i for _, i in order)
    return {"pages": doc.page_count, "sections_in_order": in_order, "section_positions": order,
            "lines_checked": len(model["lines"]), "lines_missing_in_pdf": missing,
            "state": "PASS" if in_order and not missing else "FAIL"}


def regression(model, regs, label) -> dict:
    """Every quantity the report shows is the frozen register value (or a declared sum of them); every line part keeps
    the register's technical status; the frozen register / engine trees are unchanged since the registers commit."""
    v = M.validate(model, regs)
    parts = [(ln["id"], p) for ln in model["lines"] for p in ln["parts"]]
    changed = []
    for lid, p in parts:
        c = p["cell"]
        if c["q"] is not None:
            src = c.get("sum") or [c["src"]]
            if abs(M.dsum(regs.get(s) for s in src) - c["q"]) > M.TOL:
                changed.append([lid, p["level"], c["q"]])
    return {"project": label, "validation": v["state"], "problems": v["problems"], "line_parts": len(parts),
            "quantity_cells_traced": v["quantity_cells"], "declared_sums": v["declared_sums"], "quantity_changes": changed,
            "status_rule": "every part shows the register's own technical code; the display state is the alias table",
            "input_registers": regs.inputs(), "state": "PASS" if v["state"] == "PASS" and not changed else "FAIL"}


def cross_checks(model, regs) -> list:
    """Declared sums against totals the registers already publish."""
    g = regs.data
    out = []

    def add(name, shown, published):
        out.append({"check": name, "report": shown, "register": published, "equal": abs(shown - published) <= M.TOL})
    ln = {x["id"]: x for x in model["lines"]}
    pc = g["B2A1.PHYSICAL_CONCRETE_REGISTER"]
    for p in ln["CON-SUPER"]["parts"]:
        m = pc["storeys"][p["level"]]["model"]
        add(f"storey {p['level']} total = sum of components", M.dsum(m["by_component_m3"].values()), p["cell"]["q"])
    found = [s for s in model["sheets"] if s["name"] == "04_FOUNDATION_SUBSTRUCTURE"][0]
    for sec, item in (("FOOTINGS", "FOOTINGS"), ("STRAPS", "STRAPS")):
        sub = [r for r in [x for x in found["sections"] if x["id"] == sec][0]["rows"] if r["role"] == "SUBTOTAL"][0]
        q = [c for c in sub["cells"] if M.is_q(c)][0]["q"]
        add(f"{item}: type rows add to the register item", q,
            [r for r in pc["explicit_items"] if r["item"] == item][0]["volume_m3"])
    ab = {r["item"]: r for r in g["A3.ARCH_BOQ"]["rows"]}
    rr = g["A3.ROOM_REGISTER"]["rooms"]
    for fl in ("GF", "1F"):
        add(f"A3 certified rooms {fl} = A3 floor-area subtotal", M.dsum(r["floor_area_m2"] for r in rr if r["floor"] == fl and r["floor_area_m2"] is not None),
            ab[f"A3-FLR-{fl}"]["qty"])
    sv = g["B2A1.STRUCTURAL_VERTICAL_INTERVAL_REGISTER"]
    for fl, s in sv["by_storey"].items():
        add(f"columns {fl}: rows add to by_storey", M.dsum(r["volume_m3"] for r in sv["rows"] if r["floor"] == fl and r.get("volume_m3") is not None),
            s["volume_m3"])
    return out


RECON = "08_QS_RECONCILIATION"
CHECK_PAIRS = {"BEAM_CHECK": ("ulen", "clen"), "COL_CHECK": ("uh", "ch"), "SLAB_CHECK": ("ua", "ca")}


def scenario(model):
    """A what-if a QS would type: manual values on item rows at +0.1 % / +2 % / +20 %, a value on an ENGINE BLOCKED row,
    a non-numeric note, an architectural MATCH, and the Urban measured length / height / area typed into every structural
    check. Returns the edits and the reconciliation status each edited row must reach."""
    s = [x for x in model["sheets"] if x["name"] == RECON][0]
    secs = {x["id"]: x for x in s["sections"]}
    edits, expect = [], []

    def cell(sec, r, ck):
        return r["cells"][[c["key"] for c in sec["columns"]].index(ck)]
    items = secs["ITEMS"]
    num = [r for r in items["rows"] if r["cells"][0] == "ITEM" and cell(items, r, "urban").get("q")]
    blk = [r for r in items["rows"] if r["cells"][0] == "ITEM" and "blocked" in cell(items, r, "urban")]
    for r, f, st in zip(num, (1.001, 1.02, 1.2), ("MATCH", "CLOSE", "REVIEW")):
        edits.append([RECON, "ITEMS", r["key"], "manual", round(cell(items, r, "urban")["q"] * f, 6)])
        expect.append(["ITEMS", r["key"], st])
    if len(num) > 3:
        edits.append([RECON, "ITEMS", num[3]["key"], "manual", "n/a"])
        expect.append(["ITEMS", num[3]["key"], "NOT COMPARABLE"])
    if blk:
        edits.append([RECON, "ITEMS", blk[0]["key"], "manual", 5.0])
        expect.append(["ITEMS", blk[0]["key"], "ENGINE BLOCKED"])
    arch = [r for r in secs["ARCH"]["rows"] if cell(secs["ARCH"], r, "urban").get("q")]
    if arch:
        edits.append([RECON, "ARCH", arch[0]["key"], "manual", cell(secs["ARCH"], arch[0], "urban")["q"]])
        expect.append(["ARCH", arch[0]["key"], "MATCH"])
    for sid, (u, c) in CHECK_PAIRS.items():
        if sid not in secs:
            continue
        for r in secs[sid]["rows"]:
            if r["role"] == "ITEM" and cell(secs[sid], r, u).get("q") is not None:
                edits.append([RECON, sid, r["key"], c, cell(secs[sid], r, u)["q"]])
                expect.append([sid, r["key"], "MATCH"])
    return edits, expect


def whatif_check(path, model, cell_map, workdir):
    edits, expect = scenario(model)
    w = RB.whatif(path, model, cell_map, edits, workdir)
    if w["state"] == "SKIPPED":
        return w
    after = w.pop("model_after")
    secs = {x["id"]: x for x in [s for s in after["sheets"] if s["name"] == RECON][0]["sections"]}
    got = {}
    for sid, rk, st in expect:
        sec = secs[sid]
        r = [x for x in sec["rows"] if x.get("key") == rk][0]
        got[f"{sid}/{rk}"] = [st, r["cells"][[c["key"] for c in sec["columns"]].index("rstatus")]["v"]]
    engine = lambda m: [(s["name"], sec["id"], i, j, c) for s, sec, i, r, j, c in M.iter_cells(m) if M.is_q(c)]
    q0, q1 = engine(model), engine(after)
    summ = lambda m: [c["v"] for c in [x for *_, x in M.iter_cells({"sheets": [m["sheets"][0]]})] if M.is_f(c)]
    w["expected_statuses"] = got
    w["expected_statuses_hold"] = all(a == b for a, b in got.values())
    w["engine_quantities_unchanged_by_inputs"] = q0 == q1
    w["summary_totals_unchanged_by_inputs"] = summ(model) == summ(after)
    w["state"] = "PASS" if w["state"] == "PASS" and w["expected_statuses_hold"] and w["engine_quantities_unchanged_by_inputs"] \
        and w["summary_totals_unchanged_by_inputs"] else "FAIL"
    return w


def build_one(build, out, stem, regs_commit, run_date):
    model, regs = build(run_date, regs_commit)
    v = M.validate(model, regs)
    if v["state"] != "PASS":
        raise SystemExit(f"{stem}: reporting model invalid: {v['problems'][:5]}")
    x = X.render(model, out / f"{stem}.xlsx", logo=LOGO)
    rb = RB.validate(out / f"{stem}.xlsx", model, x["cell_map"])
    with tempfile.TemporaryDirectory() as td:
        rb["libreoffice_recalc"] = RB.recalc(out / f"{stem}.xlsx", x["cell_map"])
        rb["what_if"] = whatif_check(out / f"{stem}.xlsx", model, x["cell_map"], td)
    if rb["libreoffice_recalc"]["state"] != "PASS" or rb["what_if"]["state"] != "PASS":
        rb["state"] = "FAIL"                                  # LibreOffice is required for the build (installed here)
    p = P.render(model, out / f"{stem}.pdf", logo=LOGO, cairo=CAIRO)
    pc = pdf_checks(out / f"{stem}.pdf", model)
    return model, regs, v, x, rb, p, pc


def main(out, regs_commit, junit=None, rc=None):
    out = Path(out)
    pkg = out / NAME
    if pkg.exists():
        shutil.rmtree(pkg)
    (pkg / "qortuba_check").mkdir(parents=True)
    run_date = git("log", "-1", "--format=%cs", regs_commit) or "unknown"
    am, ar, av, ax, arb, ap, apc = build_one(AL.build, pkg, "URBAN_QTO_ALSENAN_REPORTING_V2", regs_commit, run_date)
    qm, qr, qv, qx, qrb, qp, qpc = build_one(QO.build, pkg / "qortuba_check", "URBAN_QTO_QORTUBA_REPORTING_V2", regs_commit, run_date)
    (pkg / "REPORTING_MODEL_V2.json").write_text(dumps(am))
    (pkg / "qortuba_check" / "REPORTING_MODEL_V2_QORTUBA.json").write_text(dumps(qm))
    qa = {"SCHEMA": "URBAN_REPORTING_V2_READBACK_QA_V1",
          "alsenan": {"xlsx": {k: v for k, v in arb.items()}, "pdf": apc,
                      "model_validation": {k: av[k] for k in ("state", "quantity_cells", "declared_sums", "formula_cells", "lines")}},
          "qortuba": {"xlsx": {k: v for k, v in qrb.items()}, "pdf": qpc,
                      "model_validation": {k: qv[k] for k in ("state", "quantity_cells", "declared_sums", "formula_cells", "lines")}},
          "state": "PASS" if all(s == "PASS" for s in (arb["state"], apc["state"], qrb["state"], qpc["state"], av["state"], qv["state"])) else "FAIL"}
    (pkg / "REPORTING_READBACK_QA.json").write_text(dumps(qa))
    diff = {d: git("diff", "--stat", regs_commit, "--", d) for d in FROZEN}
    canon = {it["canonical_item_id"]: [it["qty"], it["status"]] for it in qr.data["RC1.CANONICAL_BOQ"]["items"]}
    shown = {ln["id"]: [ln["qty"]["q"], ln["parts"][0]["tech"]] for ln in qm["lines"]}
    reg = {"SCHEMA": "URBAN_REPORTING_V2_REGRESSION_V1", "registers_commit": regs_commit,
           "frozen_trees_unchanged_since_registers_commit": {d: (s == "") for d, s in diff.items()},
           "engine_changed": diff["engine/source"] != "",
           "alsenan": regression(am, ar, "ALSENAN (A3 + B2A.1 frozen registers)") | {"cross_checks": cross_checks(am, ar)},
           "qortuba": regression(qm, qr, "QORTUBA (RC1 frozen registers)") | {
               "canonical_items_unchanged": canon == shown, "canonical_items": len(canon),
               "rc1_xlsx_sha256_frozen": qr.data["RC1.QORTUBA_RC1_FREEZE"]["xlsx_file_sha256"]}}
    reg["alsenan"]["state"] = "PASS" if reg["alsenan"]["state"] == "PASS" and all(c["equal"] for c in reg["alsenan"]["cross_checks"]) else "FAIL"
    reg["qortuba"]["state"] = "PASS" if reg["qortuba"]["state"] == "PASS" and reg["qortuba"]["canonical_items_unchanged"] else "FAIL"
    reg["state"] = "PASS" if reg["alsenan"]["state"] == reg["qortuba"]["state"] == "PASS" and not reg["engine_changed"] and \
        all(reg["frozen_trees_unchanged_since_registers_commit"].values()) else "FAIL"
    (pkg / "REPORTING_V2_REGRESSION.json").write_text(dumps(reg))
    shutil.copy(SPEC, pkg / "REPORTING_V2_DESIGN_SPEC.md")
    if junit:
        t = ET.parse(junit).getroot()
        s = t if t.tag == "testsuite" else t.find("testsuite")
        a = {k: int(s.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
        xf = sum(1 for c in s.iter("testcase") for k in c if k.tag == "skipped" and "xfail" in (k.get("type", "") + k.get("message", "")))
        tr = {"tests": a["tests"], "passed": a["tests"] - a["failures"] - a["errors"] - a["skipped"], "failures": a["failures"],
              "errors": a["errors"], "skipped": a["skipped"] - xf, "xfailed": xf, "exit_code": int(rc), "head": git("rev-parse", "HEAD"),
              "reporting_v2_tests": sorted({c.get("classname") for c in s.iter("testcase") if "reporting_v2" in (c.get("classname") or "")})}
        (pkg / "REPORTING_V2_TEST_RESULTS.json").write_text(dumps({"SCHEMA": "URBAN_REPORTING_V2_TEST_RESULTS_V1", **tr}))
    fz = {"SCHEMA": "URBAN_REPORTING_V2_FREEZE_V1", "policy": M.POLICY_ID, "registers_commit": regs_commit, "run_date": run_date,
          "code_head": git("rev-parse", "HEAD"),
          "input_register_digests": {"alsenan": ar.inputs(), "qortuba": qr.inputs()},
          "model_input_digests_equal_registers": am["inputs"] == ar.inputs() and qm["inputs"] == qr.inputs(),
          "model_content_digest": {"alsenan": am["content_digest"], "qortuba": qm["content_digest"]},
          "outputs": {p.relative_to(pkg).as_posix(): sha(p) for p in sorted(pkg.rglob("*")) if p.is_file()},
          "rule": "the report transforms layout only: every quantity is a register value (pointer) or a declared sum of them"}
    (pkg / "REPORTING_V2_FREEZE.json").write_text(dumps(fz))
    z = out / "REPORTING_V2.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(q for q in pkg.rglob("*") if q.is_file()):
            zi = zipfile.ZipInfo(f"{NAME}/{p.relative_to(pkg).as_posix()}", date_time=(2026, 10, 3, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(zi, p.read_bytes())
    summary = {"xlsx_sha256": ax["file_sha256"], "pdf_sha256": ap["file_sha256"], "pdf_pages": apc["pages"],
               "qortuba_xlsx_sha256": qx["file_sha256"], "qortuba_pdf_sha256": qp["file_sha256"],
               "readback": qa["state"], "validated_quantity_cells": arb["validated_quantity_cells"],
               "qortuba_validated_quantity_cells": qrb["validated_quantity_cells"], "regression": reg["state"],
               "alsenan_regression": reg["alsenan"]["state"], "qortuba_regression": reg["qortuba"]["state"],
               "engine_changed": reg["engine_changed"], "zip": str(z), "zip_sha256": sha(z)}
    print(json.dumps(summary, indent=1))
    return summary


if __name__ == "__main__":
    main(*sys.argv[1:5])
