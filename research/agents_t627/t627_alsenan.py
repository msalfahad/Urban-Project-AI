"""T-627 builder (research, unwired): the 24 rows of the B12 opening-area statement sections (T-568/windows-m2: 14 rows
+ 2 HELD, reference 116.900 vs engine 76.256 m2; T-568/alu-doors-m2: 8 rows, 12.0 vs 12.76 m2) each given the own
width x height of its opening from the committed drawing read T627_DRAWN.json (R-T627-1), the pinned statement
(T-620) and the candidate's openings as restated by the merged T-568 (read only).

Built and compared by tests/t627_opening_area_evidence (the wrapper's pytest is the only execution path). Nothing here
changes a candidate, engine, rule / knowledge version, registry or statement file; nothing is released. Class moves are
PROPOSALS for the Checker.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (HERE, ROOT / "research" / "agents_t568"):
    sys.path.insert(0, str(p))
import t627_rules as R  # noqa: E402
import t568_alsenan as E  # noqa: E402  (the candidate's openings, read only)

D = Decimal
DRAWN = HERE / "T627_DRAWN.json"
STATEMENT = ROOT / "research/agents_t620/out/RECONCILED_STATEMENT_T620.json"
STATEMENT_SHA = "db5f7bceb8b6b44b1d9f87c40e83022cdd1123789e4e3be81fe43e9bad298e69"
OUT_JSON = HERE / "out" / "T627_ROW_EVIDENCE.json"
OUT_MD = HERE / "out" / "T627_ROW_EVIDENCE.md"
WIN, DOOR = "T-568/windows-m2", "T-568/alu-doors-m2"
SHEET_DATE = "2026-04-20"          # P7757.dwg modified date (T-201 s.2): the DXF and the DWF plot are one issue
Q55C = D("2.20")
HELD_WAITS = {
    "W02": "D-53 (designer): one 6.33 opening (drawings) or two (render); width 6.332 (printed 633, DIMENSION 8F1) and "
           "head 2.20 at the B-B cut (T-201) are drawn, the count is not settled",
    "W17": "Gate B wiring of owner Q-76 A (F-T568-1): 3.29 x 3.00 = 9.870 m2; the candidate line is still HELD "
           "9.870 .. 11.515; NW prints 305 from +5.50 (DIMENSION 2E97) and chord 269 (2D53)",
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load():
    if _sha(STATEMENT) != STATEMENT_SHA:
        raise R.RuleError("statement changed: re-pin")
    st = json.loads(STATEMENT.read_text(encoding="utf-8"))
    secs = {s["section_id"]: s for s in st["sections_v5"] if s["section_id"] in (WIN, DOOR)}
    return json.loads(DRAWN.read_text(encoding="utf-8")), secs


def _shown(v: str) -> D:
    return (D(v) / 100).quantize(D("0.01"))


def own_window(oid: str, drawn: dict) -> dict:
    pl = drawn["plan"].get(oid, {})          # a curved-on-plan window (W17) has no straight symbol group
    pw = pl.get("printed_width_dims") or []
    w_read = [{"value": _shown(x["shown"]), "kind": "PLAN", "sheet": f"plan DIMENSION {x['handle']}", "date": SHEET_DATE}
              for x in pw]
    pr = drawn["printed"].get(oid)
    h_read = []
    if pr:
        w_read.append({"value": _shown(pr["width_shown"]), "kind": "ELEVATION",
                       "sheet": f"{pr['view']} DIMENSION {pr['width_dim']}", "date": SHEET_DATE})
        h_read.append({"value": _shown(pr["height_shown"]), "kind": "ELEVATION",
                       "sheet": f"{pr['view']} DIMENSION {pr['height_dim']}", "date": SHEET_DATE})
    if not w_read and pl:
        w_read.append({"value": D(pl["width"]).quantize(D("0.01")), "kind": "GEOMETRY", "bound": True,
                       "sheet": "plan masonry jambs " + " / ".join(pl["jamb_handles"])})
    views = []
    for view, by in sorted(drawn["views"].items()):
        for r in by.get(oid, []):
            if r["match"] == "opening":
                views.append((view, r))
                h_read.append({"value": D(r["height"]), "kind": "GEOMETRY", "bound": r["status"] == "BOUND",
                               "sheet": f"DWF {view}"})
    w, h = R.governing(w_read), R.governing(h_read)
    return {"id": oid, "width": w, "height": h, "plan_jamb_width": pl.get("width"),
            "views": [{"view": v, "width": r["width"], "height": r["height"], "status": r["status"],
                       "sill_level": r["bottom_level"], "head_level": r["head_level"]} for v, r in views]}


def own_door(oid: str, drawn: dict) -> dict:
    pl = drawn["plan"][oid]
    w = R.governing([{"value": D(pl["width"]), "kind": "GEOMETRY", "bound": True,
                      "sheet": "plan wall-face ends, both faces " + " / ".join(pl["face_handles"])}])
    views = []
    for view, by in sorted(drawn["views"].items()):
        for r in by.get(oid, []):
            st = r["status"]
            frame_only = r["match"] == "frame" and not any(x["match"] == "opening" and x["status"] == "BOUND"
                                                           for x in by.get(oid, []))
            if r["match"] == "opening" and st == "INNER_OF_FRAME":
                continue
            if r["match"] == "frame" and any(x["match"] == "opening" and x["status"] == "BOUND" for x in by.get(oid, [])):
                continue
            views.append({"sheet": f"DWF {view}", "view": view, "width": r["width"], "height": r["height"],
                          "bottom_level": r["bottom_level"], "head_level": r["head_level"],
                          "bound": st == "BOUND", "frame_only": frame_only, "status": st})
    levels = [x["level"].lstrip("+") for x in pl["plan_levels"] if float(x["distance"]) <= 3.0]
    dh = R.door_height_from_views(views, levels)
    if dh["status"] == "DRAWING_CONFIRMED":
        h = {"value": dh["value"], "basis": "GEOMETRY", "sheet": " / ".join(v["sheet"] for v in views if v["bound"]),
             "status": "DRAWING_CONFIRMED", "why": dh["why"]}
    else:
        h = R.governing([{"value": Q55C, "kind": "OWNER_FALLBACK", "sheet": "owner Q-55 C (no printed door height)"}])
        h["why"] = dh["why"]
        h["geometry_status"] = dh["status"]
    return {"id": oid, "width": w, "height": h, "views": views, "plan_levels": pl["plan_levels"],
            "frame_width_drawn": [v["width"] for v in views if v["frame_only"]]}


NAME = re.compile(r"^(GF|1F|2F) (\S+) (?:vs his ([\d.]+) x ([\d.]+)|\(no unit of his\)) / (.+)$")


def _engine(oid: str) -> dict:
    o = {x["id"]: x for x in E.OPENINGS}[oid]
    a = D(o["area_m2"]) if o["area_m2"] else None
    w = D(o["w_m"])
    return {"width": w, "area": a, "height": (a / w).quantize(D("0.0001")) if a is not None else None,
            "basis": o["basis"]}


def row_evidence(sec: dict, drawn: dict) -> list[dict]:
    out = []
    for r in sec["rows"]:
        m = NAME.match(r["name"])
        if not m:
            raise R.RuleError(f"row name not understood: {r['name']}")
        floor, oid, hw, hh, term = m.groups()
        own = own_window(oid, drawn) if oid.startswith("W") else own_door(oid, drawn)
        eng = _engine(oid)
        rec = {"name": r["name"], "id": oid, "floor": floor, "class": r["class"], "delta": r["delta"],
               "his": None if hw is None else f"{hw} x {hh}", "engine": {k: (None if v is None else str(v))
                                                                      for k, v in eng.items()},
               "own_width": None if own["width"]["value"] is None else str(own["width"]["value"]),
               "own_width_basis": own["width"]["status"] + ": " + str(own["width"]["sheet"]),
               "own_height": None if own["height"]["value"] is None else str(own["height"]["value"]),
               "own_height_basis": own["height"]["status"] + ": " + str(own["height"]["sheet"])}
        if own["height"].get("why"):
            rec["own_height_note"] = own["height"]["why"]
        if r["class"] == "HELD":
            rec.update(evidence="HELD", proposed_class="HELD", waits_on=HELD_WAITS[oid], expected=None)
            out.append(rec)
            continue
        ow, oh = own["width"]["value"], own["height"]["value"]
        if ow is None or oh is None:
            raise R.RuleError(f"{oid}: own reading missing")
        rec["own_area"] = str(R.opening_area(ow, oh))
        rec["engine_minus_own"] = None if eng["area"] is None else str(eng["area"] - D(rec["own_area"]))
        terms = {t["term"]: t["qty"] for t in R.split_terms(ow, oh, hw, hh)}
        key = {"width": "WIDTH", "height": "HEIGHT", "ours only": "OMITTED"}[term]
        rec["expected"] = str(terms[key])
        ev, diff = R.judge_row(r["delta"], terms[key])
        used = [own["width"]] + ([own["height"]] if key in ("HEIGHT", "OMITTED") else [])
        if ev == "DRAWING_CONFIRMED" and any(u["status"] == "ASSUMED_OWNER_APPROVED" for u in used):
            ev = "ASSUMED_OWNER_APPROVED"      # reproduced, but on the owner's fallback height, not on the drawings
        rec["evidence"], rec["diff"] = ev, str(diff)
        pc = r["class"]
        if key == "HEIGHT" and r["class"] == "RULE_DIFFERENCE" and own["height"]["status"] == "DRAWING_CONFIRMED" \
                and eng["height"] is not None and eng["height"] == oh:
            pc = "ENGINE_RIGHT"     # the fallback height is now drawn: his 2.40 is printed / drawn nowhere
        rec["proposed_class"] = pc
        out.append(rec)
    return out


def build() -> dict:
    drawn, secs = load()
    res = {"task": "T-627", "rule": R.RULE_ID, "governing": R.GOVERNING,
           "statement": {"file": str(STATEMENT.relative_to(ROOT)), "sha256": STATEMENT_SHA, "sections": [WIN, DOOR]},
           "drawn": str(DRAWN.relative_to(ROOT)), "sections": {}}
    for sid in (WIN, DOOR):
        sec = secs[sid]
        rows = row_evidence(sec, drawn)
        split_now = R.split_exact([{"delta": r["delta"], "class": r["class"], "evidence": r["evidence"]}
                                   for r in rows], sec["difference"])
        split_prop = R.split_exact([{"delta": r["delta"], "class": r["proposed_class"], "evidence": r["evidence"]}
                                    for r in rows], sec["difference"])
        res["sections"][sid] = {"reference_total": sec["reference_total"], "engine_valued": sec["engine_valued"],
                                "difference": sec["difference"], "rows": rows, "split_statement": split_now,
                                "split_proposed": split_prop,
                                "count": {k: sum(1 for r in rows if r["evidence"] == k)
                                          for k in sorted({r["evidence"] for r in rows})}}
    # every opening behind a row, own vs engine (m2)
    ids = sorted({r["id"] for s in res["sections"].values() for r in s["rows"] if r["evidence"] != "HELD"})
    res["openings_own_vs_engine"] = [{"id": i, "own_area": next(r["own_area"] for s in res["sections"].values()
                                                                for r in s["rows"] if r["id"] == i and "own_area" in r),
                                      "engine_area": _engine(i)["area"] and str(_engine(i)["area"])} for i in ids]
    d9 = own_door("D-GF-09", drawn)
    res["door_findings"] = {
        "D-GF-09": {"plan_masonry_width": str(d9["width"]["value"]), "frame_width_drawn": d9["frame_width_drawn"],
                    "views": d9["views"], "height_status": d9["height"]["status"],
                    "note": "both vector views draw the D120 frame (1.00 m), not the 0.90 masonry opening, and put its "
                            "head at different levels (SW +2.50 from the +0.15 court, NE +3.20 from +1.00): candidates "
                            "only; the height stays Q-55 C (ASSUMED - OWNER-APPROVED)"},
        "D-GF-05": {"note": "no vector view binds it: its only coincident outline (SECTION A-A) belongs to W10 in the "
                            "wall beyond (same-wall support of W09); height stays Q-55 C"},
        "D-2F-01": {"note": "no outline bound in SW / NE / A-A / B-B; height stays Q-55 C"},
    }
    return res


def dumps(d) -> str:
    return json.dumps(d, indent=1, sort_keys=True, ensure_ascii=True, default=str) + "\n"


def render_md(d: dict) -> str:
    L = ["# T-627 row evidence (generated by t627_alsenan.py; do not edit)", ""]
    for sid, s in d["sections"].items():
        L.append(f"## {sid}: reference {s['reference_total']} vs engine {s['engine_valued']} m2, difference "
                 f"{s['difference']}")
        L.append("")
        L.append("| Row | Own w x h (m) | Basis (width ; height) | His | Expected | Delta | Evidence | Class -> proposed |")
        L.append("|---|---|---|---|---|---|---|---|")
        for r in s["rows"]:
            L.append(f"| {r['name']} | {r['own_width']} x {r['own_height']} | {r['own_width_basis']} ; "
                     f"{r['own_height_basis']} | {r['his']} | {r['expected']} | {r['delta']} | {r['evidence']} | "
                     f"{r['class']} -> {r['proposed_class']} |")
        L.append("")
        L.append(f"Split (statement classes): {s['split_statement']}")
        L.append(f"Split (proposed classes): {s['split_proposed']}")
        L.append("")
    L.append("## Door findings")
    for k, v in d["door_findings"].items():
        L.append(f"- {k}: {v['note']}")
    return "\n".join(L) + "\n"
