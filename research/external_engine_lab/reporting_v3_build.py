"""REPORTING V3 build - URBAN_QTO_ALSENAN_FINAL_BOQ package from the frozen V3a registers.

    python3 research/external_engine_lab/reporting_v3_build.py <v3_register_dir> <out_dir> [junit.xml rc]

Writes <out_dir>/URBAN_QTO_ALSENAN_FINAL_BOQ/ (11 workbooks, completeness xlsx, two PDFs, JSON records) and the zip.
Every quantity comes from BOQ_LINES / MASTER_MATRIX; formulas are subtotals / totals / reconciliation only.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from engine.reporting_v3 import pdf as P, readback as RB, workbooks as W              # noqa: E402

NAME = "URBAN_QTO_ALSENAN_FINAL_BOQ"
LOGO = ROOT / "assets/logo.png"
CAIRO = ROOT / "assets/fonts/Cairo-Variable.ttf"
META = {"project": "ALSENAN VILLA (P7757 / ST7757)", "phase": "FINAL BOQ V3 (V3a freeze)"}
FIXED = (1980, 1, 1, 0, 0, 0)


def jl(p):
    return json.loads(Path(p).read_text())


def dumps(o):
    return json.dumps(o, indent=1, ensure_ascii=False, sort_keys=False) + "\n"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def model_from(regdir) -> dict:
    r = Path(regdir)
    boq = jl(r / "BOQ_LINES.json")
    return {"lines": boq["lines"], "levels": boq["levels"], "level_names": boq["level_names"], "trades": boq["trades"],
            "master": jl(r / "MASTER_MATRIX.json"), "completeness": jl(r / "BOQ_COMPLETENESS_MATRIX.json"),
            "blockers": jl(r / "FINAL_BLOCKER_REGISTER.json"), "questions": jl(r / "FINAL_OWNER_QUESTION_REGISTER.json")}


# ------------------------------------------------------------------ PDF documents
def _fmt(v):
    return None if v is None else round(v, 3)


def _short(text, n=110):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


def final_report(model, regdir) -> dict:
    r = Path(regdir)
    rooms = jl(r / "ROOM_REGISTER_V3.json")
    topo = jl(r / "V3_TOPOLOGY_REGISTER.json")
    trades = {t[1]: (t[0], t[2]) for t in model["trades"]}
    pages = [{"cover": True, "blocks": [{"p": "Quantities from the frozen Urban engine; formulas only for subtotals, totals "
                                               "and reconciliation. No benchmark calibration. No pricing."}]}]
    skim = owner_actions(model)
    pages.append({"title_en": "OWNER ACTIONS + QUICK SKIM", "title_ar": "إجراءات المالك وملخص سريع",
                  "blocks": [{"h": "Owner actions"}, {"ul": skim["actions"]}, {"h": "Quick skim"}, {"ul": skim["skim"]}]})
    mrows, cur = [], None
    for m in model["master"]["rows"]:
        if m["trade"] != cur:
            cur = m["trade"]
            mrows.append({"group": f"{trades[cur][0]} {cur.replace('_', ' ')}  |  {trades[cur][1]}"})
        mrows.append([m["item"], m["item_ar"], m["unit"]] + [_fmt(m[lv]) or "-" for lv in model["levels"]] +
                     [_fmt(m["total"]) or "-", m["status"]])
    pages.append({"title_en": "MASTER SUMMARY - TRADE x LEVEL", "title_ar": "الملخص العام",
                  "blocks": [{"table": {"head": ["ITEM", "البند", "UNIT", "GF", "1F", "2F + ROOF", "OTHER + EXT", "TOTAL", "STATUS"],
                                        "rows": mrows, "num": [3, 4, 5, 6, 7], "status": 8, "ar": [1]}},
                             {"p": model["master"]["rule"]}]})
    pages.append({"title_en": "BOQ COMPLETENESS MATRIX", "title_ar": "مصفوفة الاكتمال",
                  "blocks": [{"table": {"head": ["TRADE", "البند", "EXPECTED", "COMPUTED", "PARTIAL", "REVIEW", "BLOCKED",
                                                 "NOT IN SRC", "COVER %", "CORE %"],
                                        "rows": [[c["trade"], c["trade_ar"], c["expected_items"], c["computed"], c["partial"],
                                                  c["review"], c["blocked"], c["not_in_source"], c["coverage_pct"],
                                                  c["core_coverage_pct"]] for c in model["completeness"]["rows"]],
                                        "num": [2, 3, 4, 5, 6, 7, 8, 9], "ar": [1]}},
                             {"p": model["completeness"]["rule"]}]})
    # rooms page
    rr = [[x["id"], x["class"], x["name_en"], x["name_ar"], x["room_class"], _fmt(x["area_m2"]), x["status"]]
          for x in rooms["rows"] if x["class"] != "OPENING_STRIP"]
    pages.append({"title_en": "ROOM / ZONE REGISTER (V3 TOPOLOGY)", "title_ar": "سجل الغرف",
                  "blocks": [{"p": "Rooms closed by the V3 generic rules (door closures, jamb-frame closure B, double-leaf "
                                   "doors, drafting-gap joins); Arabic names decoded from the legacy CAD font."},
                             {"table": {"head": ["ID", "CLASS", "NAME", "الاسم", "ROOM CLASS", "AREA m2", "STATUS"], "rows": rr,
                                        "num": [5], "ar": [3], "status": 6}}]})
    for code, t, ar, _ in model["trades"]:
        xs = [x for x in model["lines"] if x["trade"] == t]
        rows = []
        for lv in model["levels"]:
            ys = [x for x in xs if x["level"] == lv]
            if not ys:
                continue
            en, lar = model["level_names"][lv]
            rows.append({"group": f"{en}  |  {lar}"})
            rows += [[x["group"], x["code"], x["desc_en"], x["desc_ar"], _short(x["formula"]), x["unit"], _fmt(x["qty"]),
                      x["status"]] for x in ys]
        pages.append({"title_en": f"{code} {t.replace('_', ' ')} - BY LEVEL", "title_ar": ar,
                      "blocks": [{"table": {"head": ["GROUP", "CODE", "DESCRIPTION", "الوصف", "CALCULATION / REASON", "UNIT", "QTY",
                                                     "STATUS"], "rows": rows, "num": [6], "ar": [3], "status": 7}},
                                 {"p": "Full calculation text, inputs and source trace: workbook " + code + " (DETAIL and TRACE sheets)."}]})
    pages.append({"title_en": "FINAL BLOCKERS", "title_ar": "المعوقات",
                  "blocks": [{"table": {"head": ["ID", "AREA", "BLOCKER", "LINES", "CLASS", "WHY"],
                                        "rows": [[b["id"], b["area"], b["blocker"], b["lines"], b["class"], b["why"]]
                                                 for b in model["blockers"]["rows"]]}}]})
    pages.append({"title_en": "OWNER QUESTIONS (BATCHED)", "title_ar": "أسئلة المالك",
                  "blocks": [{"table": {"head": ["GROUP", "ID", "QUESTION"],
                                        "rows": [[q["group"], q["id"], q["question"]] for q in model["questions"]["rows"]]}},
                             {"p": model["questions"]["rule"]}]})
    pages.append({"title_en": "METHODS AND AUTHORITY", "title_ar": "الطرق والمرجعية",
                  "blocks": [{"ul": ["Authority order: SOURCE > PROJECT_OWNER_FACT > URBAN_FALLBACK > BLOCKED (OD-V3-1).",
                                     "Floor build-up 0.10 m is URBAN_FALLBACK (paint / wall-tile heights), never SOURCE.",
                                     "Finish geometry released without material; dry floors porcelain, wet / service tiled; "
                                     "ceilings BY_SPEC (OD-V3-2).",
                                     "Rebar: NET from complete bar sets; PROCUREMENT adds laps only beyond 12 m; hooks / "
                                     "bends never invented (BLOCKED_DETAILING) (OD-V3-3).",
                                     "Extras (beads, spatter dash, cornice) are separate REVIEW items, never inside "
                                     "plaster / paint (OD-V3-4).",
                                     f"Topology closures added: {sum(len(f['closures_added']) for f in topo['floors'].values())} "
                                     "(zero material, never a wall or finish quantity) (OD-V3-7)."]}]})
    return {"title": "URBAN BOQ - FINAL REPORT - ALSENAN", "title_ar": "تقرير جدول الكميات النهائي - السنان",
            "subtitle": META["project"] + " | " + META["phase"], "pages": pages}


def owner_actions(model) -> dict:
    m = {(r["trade"], r["item"], r["unit"]): r for r in model["master"]["rows"]}

    def tot(t, i, u):
        r = m.get((t, i, u))
        return f"{r['total']:,.2f} {u}" if r else "-"
    blocked = sum(1 for x in model["lines"] if x["status"] == "BLOCKED")
    actions = [f"{q['id']}: {q['question']}" for q in model["questions"]["rows"][:8]]
    skim = [f"Reinforced concrete {tot('CONCRETE', 'Reinforced concrete', 'm3')} computed scope (necks, exterior ground "
            "beams, stairs, pool, annex slab blocked).",
            f"Rebar NET {tot('REBAR', 'Net design weight (complete sets)', 'kg')}; straight weight of sets awaiting hook "
            f"detailing {tot('REBAR', 'Straight weight - sets with hooks not detailed', 'kg')}; slab bars blocked.",
            f"Floor finish {tot('FLOORING_PORCELAIN', 'Floor finish', 'm2')}, ceilings {tot('CEILINGS', 'Ceiling area', 'm2')} "
            "- every room closed or classified; Arabic names decoded.",
            f"Blockwork 200 {tot('BLOCKWORK', 'Blockwork 200 mm', 'm2')}, 150 {tot('BLOCKWORK', 'Blockwork 150 mm', 'm2')}, "
            f"parapets {tot('BLOCKWORK', 'Parapet blockwork', 'm2')}.",
            f"Internal plaster {tot('PLASTER_PAINT', 'Internal plaster', 'm2')}; paint {tot('PLASTER_PAINT', 'Internal paint', 'm2')} "
            "(0.10 m build-up = URBAN_FALLBACK).",
            f"Wall tile {tot('WALL_TILE_WATERPROOFING', 'Wall tile', 'm2')}; roof WP {tot('WALL_TILE_WATERPROOFING', 'Roof waterproofing', 'm2')}.",
            f"Openings: areas blocked on heights; widths {tot('ALUMINIUM_OPENINGS', 'Opening widths', 'lm')}.",
            f"{blocked} BLOCKED lines carry their reason; nothing blocked enters a total."]
    return {"actions": actions, "skim": skim}


def tech_audit(model, regdir, extra) -> dict:
    r = Path(regdir)
    topo = jl(r / "V3_TOPOLOGY_REGISTER.json")
    qa = jl(r / "FINAL_QA.json")
    fz = jl(r / "FINAL_FREEZE.json")
    rb = jl(r / "REBAR_REGISTER.json")
    pages = [{"cover": True, "blocks": [{"p": "Technical audit: engine changes, topology evidence, registers, QA, digests, "
                                              "Qortuba regression and the post-freeze benchmark evaluation."}]}]
    trows = []
    for fl, f in topo["floors"].items():
        trows.append([fl, f["sites_frozen"], f["sites_v3"], f["labels_established_frozen"], f["labels_established_v3"],
                      len(f["closures_added"]), sum(1 for d in f["doors"].values() if d.get("state") == "CLOSED"),
                      len(f["wall_gaps"]), len(f["drafting_gaps"]), len(f["text_role_changes"])])
    pages.append({"title_en": "V3 TOPOLOGY - WHAT THE GENERIC FIXES CHANGED", "title_ar": "تغييرات الطوبولوجيا",
                  "blocks": [{"table": {"head": ["FLOOR", "SITES FROZEN", "SITES V3", "LABELS FROZEN", "LABELS V3", "CLOSURES",
                                                 "DOORS CLOSED/COMPLETED", "WALL GAPS", "DRAFTING JOINS", "TEXT ROLE CHANGES"],
                                        "rows": trows, "num": list(range(1, 10))}},
                             {"ul": ["near-collinear ray hit (sub-nanometre skew treated as crossing in the frozen rule)",
                                     "closure B from the door's own jamb frames (wall interior strips no longer join rooms)",
                                     "double-leaf door motif + door-in-wall-gap closure",
                                     "drafting-gap join <= 10 mm (OD-V3-7); 10-50 mm stays review-only",
                                     "tag families scoped to the source revision; bilingual corroboration (TR-V3-B)"]}]})
    drows = []
    for fl, f in topo["floors"].items():
        for d in f["decoded_labels"]:
            drows.append([fl, d["english"], d["arabic"], d["corroboration"].get("state")])
    pages.append({"title_en": "LEGACY ARABIC LABELS DECODED", "title_ar": "النصوص العربية المفكوكة",
                  "blocks": [{"table": {"head": ["FLOOR", "ENGLISH", "ARABIC (decoded)", "CORROBORATION"], "rows": drows, "ar": [2]}}]})
    sets = [s for k, v in rb.items() if isinstance(v, list) for s in v]
    from collections import Counter
    c = Counter((s["element"], s["status"]) for s in sets)
    pages.append({"title_en": "REBAR BAR SETS", "title_ar": "مجموعات التسليح",
                  "blocks": [{"table": {"head": ["ELEMENT", "STATUS", "SETS"], "rows": [[k[0], k[1], v] for k, v in sorted(c.items())],
                                        "num": [2], "status": 1}},
                             {"p": "cover 2.5 cm / 7 cm against soil and laps 70Ø / 40Ø from p.8; stirrups per metre from the "
                                   "schedule headers; footing bars straight per p.13; hooks / bends / closing BLOCKED_DETAILING."}]})
    pages.append({"title_en": "QA CHECKS", "title_ar": "فحوصات الجودة",
                  "blocks": [{"table": {"head": ["CHECK", "RESULT"], "rows": [[k, "PASS" if v else "FAIL"] for k, v in qa["checks"].items()],
                                        "status": 1}}] + [{"kv": [[k, v] for k, v in extra["qa"].items()]}]})
    pages.append({"title_en": "REGISTER DIGESTS (V3a FREEZE)", "title_ar": "بصمات السجلات",
                  "blocks": [{"table": {"head": ["REGISTER", "SHA-256"], "rows": [[k, v] for k, v in fz["register_digests"].items()]}}]})
    q = extra.get("qortuba")
    if q:
        pages.append({"title_en": "QORTUBA REGRESSION (RC1_REFERENCE, SHADOW)", "title_ar": "انحدار قرطبة",
                      "blocks": [{"kv": [["state", q["state"]], ["frozen sites", q["frozen_sites"]], ["V3 sites", q["v3_sites"]],
                                         ["text roles v3 identical", q["text_roles_v3_identical_sites"]],
                                         ["two-pass identical", q["v3_two_pass_identical_sites"]], ["rule", q["rule"]]]}]})
    ev = extra.get("evaluation")
    if ev:
        pages.append({"title_en": "BENCHMARK EVALUATION - AFTER FREEZE (EVALUATION ONLY)", "title_ar": "تقييم بعد التجميد",
                      "blocks": [{"p": ev["rule"]},
                                 {"table": {"head": ["BENCHMARK", "BENCH QTY", "V3 ITEM", "V3 QTY", "V3 STATUS", "DIFF %", "COMPARABILITY"],
                                            "rows": [[x["benchmark"], x["benchmark_qty"], x["v3_item"], x["v3_qty"], x["v3_status"],
                                                      x["difference_pct"], x["comparability"]] for x in ev["rows"]],
                                            "num": [1, 3, 5], "status": 4}}]})
    pages.append({"title_en": "DISCLOSURES", "title_ar": "إفصاحات",
                  "blocks": [{"ul": extra["disclosures"]}]})
    return {"title": "URBAN BOQ - TECHNICAL AUDIT - ALSENAN", "title_ar": "التدقيق الفني - السنان",
            "subtitle": META["project"] + " | " + META["phase"], "pages": pages}


DISCLOSURES = [
    "Development runs during this round were superseded and are not the frozen result: the first V3 topology runs before "
    "the drafting-gap join, jamb-frame closure B and bilingual rule existed; one register pair differed only by Python "
    "bytecode paths in the file-open audit (fixed by omitting code files from the recorded audit).",
    "The GF hall / dining / reception / pantry / garden-planter zone is one open-plan site (no wall, no door in the source); "
    "it is published as an OPEN_PLAN_ZONE and never split by invented lines.",
    "The 3.24 m2 site repeated on every storey is treated as a vertical shaft candidate (lift): no finish is measured in it "
    "until the owner confirms (Q-A1).",
    "Benchmark / freelancer values were opened only after the V3a freeze, through the frozen B1 register; no quantity changed.",
]


# ------------------------------------------------------------------ build
def build(regdir, out, junit=None, rc=None, qortuba=None, evaluation=None) -> dict:
    out = Path(out)
    pkg = out / NAME
    if pkg.exists():
        shutil.rmtree(pkg)
    pkg.mkdir(parents=True)
    model = model_from(regdir)
    files, qa = {}, {}
    for code, t, ar, _ in model["trades"]:
        res = W.trade_book(model, code, t, ar, pkg, META)
        files[res["file"]] = res
    for fn in (W.master_book, W.recon_book, W.completeness_book):
        res = fn(model, pkg, META)
        files[res["file"]] = res
    for f, res in files.items():
        v = RB.validate(pkg / f, res["cell_map"])
        rc_ = RB.recalc(pkg / f, res["cell_map"])
        qa[f] = {"readback": v["state"], "checked": v["checked"], "recalc": rc_["state"], "formulas": rc_.get("formulas"),
                 "problems": v["problems"][:3] + rc_.get("mismatches", [])[:3]}
    qrec = jl(qortuba) if qortuba else None
    erec = jl(evaluation) if evaluation else None
    xqa = {"workbooks": len(files), "readback_all_pass": all(x["readback"] == "PASS" for x in qa.values()),
           "recalc_all_pass": all(x["recalc"] == "PASS" for x in qa.values()),
           "formula_cells": sum(x["formulas"] or 0 for x in qa.values()),
           "value_cells": sum(x["checked"]["value"] for x in qa.values())}
    fr = final_report(model, regdir)
    pr = P.render(fr, pkg / "URBAN_BOQ_FINAL_REPORT.pdf", logo=LOGO, cairo=CAIRO)
    ta = tech_audit(model, regdir, {"qa": xqa, "qortuba": qrec, "evaluation": erec, "disclosures": DISCLOSURES})
    pt = P.render(ta, pkg / "URBAN_BOQ_TECHNICAL_AUDIT.pdf", logo=LOGO, cairo=CAIRO)
    r = Path(regdir)
    for n in ("BOQ_COMPLETENESS_MATRIX", "FINAL_BLOCKER_REGISTER", "FINAL_OWNER_QUESTION_REGISTER"):
        shutil.copy(r / f"{n}.json", pkg / f"{n}.json")
    eqa = jl(r / "FINAL_QA.json")
    final_qa = {"SCHEMA": "URBAN_ALSENAN_V3_FINAL_QA_PACKAGE_V1", "engine_registers": {"state": eqa["state"], "checks": eqa["checks"]},
                "workbooks": qa, "summary": xqa, "pdf": {"final_report_pages": len(fr["pages"]), "technical_audit_pages": len(ta["pages"])},
                "qortuba_shadow": qrec and qrec["state"],
                "state": "PASS" if eqa["state"] == "PASS" and xqa["readback_all_pass"] and xqa["recalc_all_pass"] else "FAIL"}
    (pkg / "FINAL_QA.json").write_text(dumps(final_qa))
    if junit:
        t = ET.parse(junit).getroot()
        s = t if t.tag == "testsuite" else t.find("testsuite")
        a = {k: int(s.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
        tr = {"SCHEMA": "URBAN_ALSENAN_V3_TEST_RESULTS_V1", "tests": a["tests"],
              "passed": a["tests"] - a["failures"] - a["errors"] - a["skipped"], "failures": a["failures"],
              "errors": a["errors"], "skipped": a["skipped"], "exit_code": int(rc) if rc is not None else None}
        (pkg / "TEST_RESULTS.json").write_text(dumps(tr))
    freeze = {"SCHEMA": "URBAN_ALSENAN_V3_FINAL_FREEZE_V1", "register_freeze": jl(r / "FINAL_FREEZE.json"),
              "files": {p.name: sha(p) for p in sorted(pkg.iterdir()) if p.is_file() and p.name != "FINAL_FREEZE.json"},
              "pdf": {"final_report": pr, "technical_audit": pt}}
    (pkg / "FINAL_FREEZE.json").write_text(dumps(freeze))
    zp = out / f"{NAME}.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(pkg.iterdir()):
            zi = zipfile.ZipInfo(f"{NAME}/{p.name}", date_time=FIXED)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o600 << 16
            z.writestr(zi, p.read_bytes())
    return {"qa": final_qa["state"], "summary": xqa, "zip": str(zp), "zip_sha256": sha(zp), "files": sorted(freeze["files"])}


if __name__ == "__main__":
    a = sys.argv[1:]
    kw = {}
    for x in a[2:]:
        k, _, v = x.partition("=")
        kw[k] = v
    print(json.dumps(build(a[0], a[1], **kw), indent=1))
