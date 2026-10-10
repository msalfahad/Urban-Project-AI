"""REPORTING V2 - Qortuba adapter: frozen RC1 registers (RC1_REFERENCE, never patched) -> REPORTING_MODEL_V2.

One canonical BOQ item = one line (its own trade-total group, as in the RC1 summary); a MEASURE PAIR (one physical
item measured twice) keeps its first item ADDITIVE and marks the second ALTERNATIVE_MEASURE. The RC1 registers cover
the selected second-floor apartment only and no structure: the foundation sheet says NOT IN SCOPE. Maps, never measures.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.reporting_v2 import layout as L                                                         # noqa: E402
from engine.reporting_v2 import terms as T                                                          # noqa: E402
from engine.reporting_v2.model import (Registers, alias_table, col, display_status, line, na, part, qsum, row,  # noqa: E402
                                       section, sheet)

RC1 = ROOT / "tests/rc1/registers"
FILES = ["CANONICAL_BOQ", "ROOM_QUANTITY_MATRIX", "OPENING_REGISTER", "RC1_DECISION_REGISTER", "QORTUBA_RC1_FREEZE",
         "QA_RECONCILIATION"]
LEVEL = "2F"
TRADE = {"ARCHITECTURAL_FLOOR_FINISH": "FLOOR_TILE", "MARBLE_STONE": "MARBLE", "CEILING": "CEILING",
         "PLASTER_INTERNAL": "PLASTER", "PAINT": "PAINT", "ARCHITECTURAL_WALL_FINISH": "WALL_TILE",
         "WATERPROOFING": "WATERPROOFING"}
LAYER_TRADE = {"SKIRTING": "SKIRTING", "HIDDEN_PROFILE": "HIDDEN_PROFILE", "DOOR_INTERNAL": "DOORS", "DOOR_ENTRANCE": "DOORS",
               "SLIDING_GLAZED_DOOR": "ALUMINIUM_GLAZING", "WINDOW": "WINDOWS"}
MATRIX_COLS = [("FLR-01", "FLOOR (porcelain)"), ("FLR-02", "FLOOR (bath ceramic)"), ("FLR-03", "FLOOR (pantry ceramic)"),
               ("CLG-01", "CEILING"), ("PLS-01", "PLASTER"), ("PNT-01", "PAINT"), ("WTL-01", "WALL TILE"), ("SKT-01", "SKIRTING"),
               ("WPF-01", "WP FLOOR"), ("WPU-01", "WP UPTURN")]


def registers() -> Registers:
    return Registers({f"RC1.{n}": RC1 / f"{n}.json" for n in FILES}, ROOT)


def build_lines(R):
    items = R.data["RC1.CANONICAL_BOQ"]["items"]
    seen_pair, out = set(), []
    for i, it in enumerate(items):
        trade = TRADE.get(it["trade"]) or LAYER_TRADE[it["layer"]]
        pair = it.get("measure_pair")
        alt = pair is not None and pair in seen_pair
        seen_pair.add(it["canonical_item_id"])
        ln = line(it["canonical_item_id"], trade, it["description_en"], it["description_ar"], it["unit"],
                  [part(LEVEL, R.q(f"RC1.CANONICAL_BOQ:/items/{i}/qty"), it["status"], f"{len(it['room_breakdown'])} rooms / strips")],
                  cls="ALTERNATIVE_MEASURE" if alt else "ADDITIVE", alternative_of=pair if alt else None,
                  note="; ".join(it["rules"]))
        ln["group"] = (it["canonical_item_id"], it["description_en"].split(" - ")[0] + (f" - {it['description_en'].split(' - ')[1]}"
                       if " - " in it["description_en"] else ""), it["description_ar"])
        if trade in ("FLOOR_TILE", "CEILING", "PLASTER", "PAINT", "WALL_TILE", "SKIRTING", "WATERPROOFING") and it["unit"] == "m2":
            ln["matrix"] = {"FLOOR_TILE": "FLOOR FINISH", "WALL_TILE": "WALL TILE + PREP"}.get(trade, T.trade(trade)[0]) \
                if it["layer"] != "WALL_TILE_PREP" else "WALL TILE PREP"
        out.append(ln)
    return out


def floor_sheet(R, lines):
    m = R.data["RC1.ROOM_QUANTITY_MATRIX"]
    cols = [col("room", "ROOM / STRIP", "الغرفة", "text", width=34), col("kind", "KIND", "", "text", width=7)]
    cols += [col(k, f"{lab} ({k})", "", "qty", next(x["unit"] for x in lines if x["id"] == k), 11) for k, lab in MATRIX_COLS]
    cols += [col("st", "STATUS", "الحالة", "status", width=10)]
    rows, sums = [], {k: [] for k, _ in MATRIX_COLS}
    for i, r in enumerate(m["rows"]):
        cells = [r["display"], r["kind"]]
        for k, _ in MATRIX_COLS:
            if r["cells"].get(k) is not None:
                c = R.q(f"RC1.ROOM_QUANTITY_MATRIX:/rows/{i}/cells/{k}")
                sums[k].append(c)
                cells.append(c)
            else:
                cells.append(na(""))
        rows.append(row(cells + ["COMPUTED"], cls="BREAKDOWN_ONLY", status="COMPUTED", tech="COMPUTED_SHADOW_COMPLETE"))
    rows.append(row(["SUBTOTAL (column sum; reconciles to the canonical item)", ""] + [qsum(sums[k]) if len(sums[k]) > 1 else dict(sums[k][0]) for k, _ in MATRIX_COLS]
                    + ["COMPUTED"], role="SUBTOTAL", status="COMPUTED", tech="COMPUTED_SHADOW_COMPLETE"))
    rooms = section("ROOMS", T.section("ROOMS"), cols, rows,
                    note="Room quantity matrix (RC1 register): every column adds to its canonical item (register reconciliation "
                         f"{m['state']}); strips are door thresholds.")
    o = R.data["RC1.OPENING_REGISTER"]["records"]
    ocols = [col("id", "OPENING ID", "", "code", width=12), col("kind", "TYPE", "", "text", width=18),
             col("ft", "FROM / TO", "", "text", width=40), col("w", "WIDTH", "", "dim", "m", 9), col("h", "HEIGHT", "", "dim", "m", 9),
             col("hb", "HEIGHT BASIS", "", "text", width=22), col("a", "AREA", "المساحة", "qty", "m2", 10),
             col("st", "STATUS", "", "status", width=10), col("state", "STATE", "", "code", width=24)]
    orows = []
    for i, r in enumerate(o):
        expl = {"WINDOW": "WIN-02", "SLIDING_GLAZED_DOOR": "SGD-02"}.get(r["kind"])
        area = R.q(f"RC1.OPENING_REGISTER:/records/{i}/area_m2") if r.get("area_m2") is not None else na("—")
        st = "INFO" if r["state"] == "OUT_OF_MEASURED_SCOPE" else "COMPUTED"
        orows.append(row([r["opening_id"], r["kind"], f"{r.get('from_display')} / {r.get('to_display')}", r.get("clear_width_m"),
                          r.get("height_m"), r.get("height_basis") or "", area, st, r["state"]],
                         cls="BREAKDOWN_ONLY" if expl and r.get("area_m2") is not None else "TRACE_ONLY", status=st, tech="INFO",
                         explains=f"{expl}@{LEVEL}" if expl and r.get("area_m2") is not None else None))
    openings = section("OPENINGS", T.section("OPENINGS"), ocols, orows,
                       note="Opening register (one record per occurrence). Window / sliding-door areas explain WIN-02 / SGD-02.")
    fcols = [col("code", "ITEM CODE", "", "code", width=12), col("trade", "TRADE", "", "text", width=22),
             col("ar", "", "", "ar", width=30), col("en", "DESCRIPTION", "", "text", width=44), col("q", "QTY", "", "qty", None, 12),
             col("u", "UNIT", "", "text", width=6), col("st", "STATUS", "", "status", width=10), col("cls", "CLASS", "", "cls", width=12)]
    frows = [row([ln["id"], T.trade(ln["trade"])[0], ln["desc_ar"], ln["desc_en"], ln["parts"][0]["cell"] | {"unit": ln["unit"]},
                  ln["unit"], ln["status"], "BREAKDOWN_ONLY"], cls="BREAKDOWN_ONLY", status=ln["status"],
                 tech=ln["parts"][0]["tech"], explains=f"{ln['id']}@{LEVEL}") for ln in lines]
    fin = section("FINISHES", ("FINISHES & OPENINGS ON THIS FLOOR", "التشطيبات والفتحات"), fcols, frows)
    ncols = [col("item", "ITEM", "", "text", width=30), col("st", "STATUS", "", "status", width=10),
             col("why", "WHY", "", "text", width=50), col("need", "WHAT IS NEEDED", "", "text", width=40)]
    nrows = []
    for b in R.data["RC1.RC1_DECISION_REGISTER"]["answers"]["2_blocked"]["release"]:
        code = b.split(" ")[0]
        e = T.explain(code)
        nrows.append(row([b, "INFO", e["why"], e["needed"]], role="NOTE", status="INFO", tech="INFO"))
    notes = section("NOTES", T.section("NOTES"), ncols, nrows,
                    note="No quantity is blocked in RC1; these are release blockers (the quantities stay SHADOW).")
    return sheet("01_SECOND_FLOOR", ("SECOND FLOOR - SELECTED APARTMENT", "الدور الثاني - الشقة المختارة"), "BREAKDOWN",
                 [rooms, openings, fin, notes], level=LEVEL)


def build(run_date: str, registers_commit: str):
    R = registers()
    lines = build_lines(R)
    fz = R.data["RC1.QORTUBA_RC1_FREEZE"]
    proj = {"name_en": "QORTUBA", "name_ar": "", "phase": "RC1 (REFERENCE)", "release_state": "SHADOW / RC1_REFERENCE - NOT APPROVED",
            "subtitle": f"{fz['selected_plan_scope'][:80]}  ·  run {run_date}  ·  RC1 code {fz['code_commit']}  ·  registers {registers_commit}",
            "header": [("Project", "Qortuba - architectural QTO (RC1 reference)"), ("Scope", fz["selected_plan_scope"]),
                       ("Source", f"DXF sha256 {fz['canonical_dxf_sha256'][:16]}… · DWG anchor {fz['dwg_dxf_anchor']}"),
                       ("Phase", f"{fz['name']} - {fz['release_status']}"), ("Run date", run_date),
                       ("Engine version", f"RC1 code {fz['code_commit']} · registers {registers_commit}"),
                       ("Status", "SHADOW - NOT APPROVED · no pricing · frozen RC1_REFERENCE (read only)")]}
    found = sheet("04_FOUNDATION_SUBSTRUCTURE", T.level("FOUNDATION"), "INFO",
                  [section("SUBSTRUCTURE_OTHER", ("NOT IN SCOPE", "خارج النطاق"), [col("n", "NOTE", "", "text", width=120)],
                           [row(["The Qortuba RC1 registers are architectural only (one apartment): no foundation or structural register exists. "
                                 "Nothing is shown rather than an empty table."], role="NOTE")], kind="notes")], level="FOUNDATION")
    fs = floor_sheet(R, lines)
    op = sheet("05_OPENINGS_ALUMINIUM", T.section("OPENINGS"), "SCHEDULE", [fs["sections"][1]])
    d = R.data["RC1.RC1_DECISION_REGISTER"]
    bcols = [col("n", "#", "", "code", width=26), col("st", "STATUS", "", "status", width=10), col("t", "DETAIL", "", "text", width=100)]
    brows = [row([a["id"], "INFO", "; ".join(f"{k}: {v}" for k, v in a.items() if k != "id")], role="NOTE", status="INFO", tech="INFO")
             for a in d["owner_actions"]]
    brows += [row([b, "INFO", T.explain(b.split(" ")[0])["why"]], role="NOTE", status="INFO", tech="INFO")
              for b in d["answers"]["2_blocked"]["release"]]
    bl = sheet("06_BLOCKERS_OWNER_QUESTIONS", ("BLOCKERS / OWNER QUESTIONS", "المعوقات وأسئلة المالك"), "INFO",
               [section("BLOCKERS", T.section("BLOCKERS"), bcols, brows, note="RC1 has no open quantity item; release blockers only.")])
    rules = sorted({r for it in R.data["RC1.CANONICAL_BOQ"]["items"] for r in it["rules"]})
    mcols = [col("id", "RULE / METHOD", "", "code", width=50), col("v", "VERSION", "", "text", width=8)]
    run = [("RC1 code commit", fz["code_commit"]), ("Registers commit", registers_commit), ("Run id", fz["run_id"]),
           ("Canonical BOQ digest", fz["canonical_boq_digest"]), ("RC1 xlsx sha256", fz["xlsx_file_sha256"]),
           ("Report inputs", f"{len(R.files)} frozen register files (TECH_RUN_INFO)")]
    codes = sorted({p["tech"] for ln in lines for p in ln["parts"]})
    me = sheet("07_METHODS_TRACEABILITY", ("METHODS / TRACEABILITY", "المنهجية والتتبع"), "INFO", [
        section("METHODS", T.section("METHODS"), mcols, [row([r.split("@")[0], r.split("@")[1] if "@" in r else ""], role="NOTE") for r in rules]),
        section("RUN", T.section("RUN"), [col("k", "ITEM", "", "text", width=30), col("v", "VALUE", "", "code", width=90)],
                [row([k, v], role="NOTE") for k, v in run]),
        section("STATUS_ALIAS", T.section("STATUS_ALIAS"), [col("c", "TECHNICAL CODE", "", "code", width=40),
                                                           col("d", "DISPLAY", "", "status", width=12), col("h", "RULE", "", "text", width=10)],
                [row([c, dd, h], role="NOTE", status=dd) for c, dd, h in alias_table(codes)])])
    hcols = [col("line", "LINE / LEVEL", "", "code", width=20), col("ref", "REGISTER VALUE (file:/json pointer)", "", "code", width=90),
             col("st", "TECH STATUS", "", "code", width=30)]
    hrows = [row([f"{ln['id']}@{p['level']}", ref, p["tech"]], role="NOTE", tech=p["tech"])
             for ln in lines for p in ln["parts"] for ref in (p["cell"].get("sum") or [p["cell"].get("src")])]
    tech = [sheet("TECH_SOURCE_HANDLES", ("SOURCE HANDLES / VALUE POINTERS", "مصادر القيم"), "TECH", [section("TECH", ("EVERY LINE PART -> REGISTER VALUE", ""), hcols, hrows)]),
            sheet("TECH_RUN_INFO", ("RUN INFO - REPORT INPUT DIGESTS", "معلومات التشغيل"), "TECH",
                  [section("TECH", ("INPUT REGISTERS", ""), [col("n", "REGISTER", "", "code", width=40), col("f", "FILE", "", "text", width=50),
                                                            col("s", "SHA256", "", "code", width=66)],
                           [row([n, v["file"], v["sha256"]], role="NOTE") for n, v in R.inputs().items()])])]
    qs = L.reconciliation_sheet(lines, [LEVEL])
    model = L.assemble(proj, lines, [fs, found, op, bl, me, qs] + tech, R, levels=[LEVEL],
                       key_notes=["Qortuba is RC1_REFERENCE (frozen): this report reads its registers and changes nothing.",
                                  "Measure pairs (MRB-01 / 02, SGD-01 / 02, WIN-01 / 02): the first is ADDITIVE, the second the same item "
                                  "on another basis (ALTERNATIVE_MEASURE)."])
    return model, R
