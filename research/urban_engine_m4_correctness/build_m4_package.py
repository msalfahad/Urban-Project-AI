"""M4 package builder: source-evidence corrections on the ST7757 set - every number from a live run.

    python3 -I research/urban_engine_m4_correctness/build_m4_package.py --m3-root M3_WORKTREE \
            [--heldout DIR] [--visual DIR] [--cache DIR]

M3_WORKTREE is the M3 commit (cbfa13e) checked out separately (git worktree add DIR cbfa13e): the M3 numbers are
re-run there in their own process (research/urban_engine_m3_recovery/st7757_snapshot.py), never read from edited
files and never written into the frozen M3 package. The M4 run is the CLI pipeline (tools/urban_boq_m2.compute) with
the architectural plan, the detail evidence and the independent OCR readings; its registers are written to
st7757_route_g/. External estimates appear as positions only. Every text file is refused when it carries owner
text, Arabic source text, a firewalled benchmark number or a file path. --visual DIR receives the review sheet with
the OCR crops and the visual QA PDF (client drawing content: never committed).
"""

from __future__ import annotations

import base64
import csv
import importlib.util
import io
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import ocr_review as OR                  # noqa: E402
from engine.source import provisional_estimate as PE        # noqa: E402
from tools import m4_reports as MR                           # noqa: E402
from tools import urban_boq_m2 as CLI                        # noqa: E402

DRAWING = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
ARCH = ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf"
PROFILE = PKG / "profile_st7757_m4.json"
EVIDENCE = ROOT / "research/urban_engine_m3_recovery/evidence/DETAIL_EVIDENCE.json"
READINGS = PKG / "evidence/OCR_INDEPENDENT_READINGS.json"
M3PKG = ROOT / "research/urban_engine_m3_recovery"
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}|(?i:als[ey]?n[ya]?an)")
SIX = ("FOOTINGS", "COLUMNS", "BEAMS", "GROUND_BEAMS", "SLABS", "GROUND_SLAB")
INTERPRETATION = {
    "TOP": "top bars of the detail", "BOTTOM": "bottom bars (two printed layers are summed)",
    "LINKS": "closed links, diameter / spacing", "SIDE": "side bars per face, count / spacing",
    "REJECTED_FROM_DETAIL": "the read was rejected by the OCR rules: the role it fed stays unresolved"}


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _csv(rows, fields=None):
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    return b.getvalue()


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


# ------------------------------------------------------------------ runs
def m3_snapshot(m3_root):
    out = PKG / ".m3_snapshot.json"
    subprocess.run([sys.executable, "-I", str(M3PKG / "st7757_snapshot.py"), "--engine-root", str(m3_root),
                    "--profile", str(Path(m3_root) / "research/urban_engine_m3_recovery/profile_st7757_m3.json"),
                    "--evidence", str(EVIDENCE), "--out", str(out)], check=True, capture_output=True)
    res = json.loads(out.read_text())
    out.unlink()
    return res


def m4_run(cache=None):
    return CLI.compute([str(DRAWING)], profile=str(PROFILE), route="G", cache_dir=cache, evidence=str(EVIDENCE),
                       arch=[str(ARCH)], evidence_review=str(READINGS))


# ------------------------------------------------------------------ 2 before / after by family
def before_after(m3, R):
    g4 = {(r["trade"], r["family"]): r for r in PE.rollup(R["items"], ("trade", "family"))}
    keys = sorted(set(g4) | {tuple(k.split("|")) for k in m3["families"]},
                  key=lambda k: (k[0], k[1] not in SIX, SIX.index(k[1]) if k[1] in SIX else 0, k[1]))
    out = []
    for t, f in keys:
        a = m3["families"].get(f"{t}|{f}", {})
        b = g4.get((t, f), {})
        out.append({"TRADE": t, "FAMILY": f, "UNIT": "m3" if t == "CONCRETE" else "kg",
                    "M3_LOW": _f(a.get("PROVISIONAL_LOW")), "M3_BASE": _f(a.get("PROVISIONAL_BASE")),
                    "M3_HIGH": _f(a.get("PROVISIONAL_HIGH")), "M3_N_UNRESOLVED": a.get("N_UNRESOLVED", 0),
                    "M3_EXPOSURE_HIGH": _f(a.get("UNRESOLVED_EXPOSURE_HIGH")),
                    "M4_LOW": _f(b.get("PROVISIONAL_LOW")), "M4_BASE": _f(b.get("PROVISIONAL_BASE")),
                    "M4_HIGH": _f(b.get("PROVISIONAL_HIGH")), "M4_N_UNRESOLVED": b.get("N_UNRESOLVED", 0),
                    "M4_EXPOSURE_LOW": _f(b.get("UNRESOLVED_EXPOSURE_LOW")),
                    "M4_EXPOSURE_HIGH": _f(b.get("UNRESOLVED_EXPOSURE_HIGH")),
                    "M4_MINUS_M3_BASE": _f(b.get("PROVISIONAL_BASE")) - _f(a.get("PROVISIONAL_BASE"))})
    for t in ("CONCRETE", "REINFORCEMENT"):
        rows = [r for r in out if r["TRADE"] == t]
        tot = {k: sum(r[k] for r in rows) for k in ("M3_LOW", "M3_BASE", "M3_HIGH", "M3_EXPOSURE_HIGH", "M4_LOW",
                                                     "M4_BASE", "M4_HIGH", "M4_EXPOSURE_LOW", "M4_EXPOSURE_HIGH")}
        out.append(dict({"TRADE": t, "FAMILY": "ALL_FAMILIES", "UNIT": rows[0]["UNIT"] if rows else "",
                         "M3_N_UNRESOLVED": sum(r["M3_N_UNRESOLVED"] for r in rows),
                         "M4_N_UNRESOLVED": sum(r["M4_N_UNRESOLVED"] for r in rows)}, **tot,
                        M4_MINUS_M3_BASE=tot["M4_BASE"] - tot["M3_BASE"]))
    return out


# ------------------------------------------------------------------ 3 component reconciliation M3 -> M4
def _cause(i4, i3, D, c4=None):
    """the M4 rule that changed a component, from the M4 item, the component's M4 concrete item (c4) and the
    detected model (never from a total)."""
    f = (i4 or i3)["family"]
    ctx = i4 if i4 is not None and i4["trade"] == "CONCRETE" else (c4 or {})
    blk = ctx.get("blocker", "")
    if blk == "UNLABELLED_SPAN_ACROSS_SUPPORT":
        return "ALIGNMENT_ONLY_SPAN_NOW_UNRESOLVED", "M3 carried the collinear section across a support; M4 holds it"
    if i4 is None:
        return "REMOVED_OR_RENAMED", "an M3 component M4 does not hold under this id"
    if i4["trade"] == "REINFORCEMENT" and f == "GROUND_BEAMS" and (ctx.get("dimensions") or {}).get("arch_class"):
        return f"GB_EXTERIOR_{ctx['dimensions']['arch_class']}", "the exterior detail's bars follow the evidenced case"
    i4 = i4 if i4["trade"] == "CONCRETE" or ":CB_" in i4["item_id"] else dict(i4, blocker=blk,
                                                                              dimensions=ctx.get("dimensions"))
    blk = i4.get("blocker", "")
    d = i4.get("dimensions") or {}
    if blk == "UNLABELLED_SPAN_ACROSS_SUPPORT":
        return "ALIGNMENT_ONLY_SPAN_NOW_UNRESOLVED", "M3 carried the collinear section across a support; M4 holds it"
    if "INHERITED_BY_SPAN_SEQUENCE" in (i4.get("source") or ""):
        return "SPAN_TAKEN_BY_PRINTED_SEQUENCE", "the printed span sequence of a continuous beam maps the span"
    if f == "GROUND_BEAMS" and blk in ("GB_EXTERIOR_DEPTH", "GB_EXTERIOR_LEVEL_CONFLICT", "GB_EXTERIOR_NOT_EVIDENCED",
                                       "GB_TITLES_AND_LENGTH_BASIS") and d.get("arch_class"):
        return f"GB_EXTERIOR_{d['arch_class']}", "the architectural plan decides the exterior detail"
    if f in ("SLABS", "GROUND_SLAB") and d.get("t_basis") == "PROJECT_DEFAULT":
        return "SLAB_PROJECT_DEFAULT_THICKNESS", "the printed project default replaces the sheet's one tag"
    if f in ("SLABS", "GROUND_SLAB") and d.get("member_overlap_deducted_m2"):
        return "SLAB_MEMBER_OVERLAP_DEDUCTED", "the slab face's overlap with beams / columns is the members'"
    if f == "PLAIN_CONCRETE":
        return "BLINDING_UNION", "blinding plan = union of footing and strip outlines, printed projection"
    if f in ("LINTELS", "STAIRS"):
        return f"{f}_NEW_FAMILY", "measured from the architectural openings / drawn treads"
    if i4["trade"] == "REINFORCEMENT" and ":CB_" in i4["item_id"]:
        return "CB_PHYSICAL_BARS", "continuous-beam bars from the physical bar model"
    if i3 is None:
        return "NEW_OR_RENAMED", "an M4 component M3 did not hold under this id"
    return "VALUE_CHANGED", "same component, value changed by an engine rule"


def reconciliation(m3, R):
    D = R["generic"]["D"]
    a = defaultdict(float)
    i3 = {}
    for i in m3["items"]:
        if i["category"] == "PROVISIONAL":
            k = (i["trade"], i["family"], i["component_id"])
            a[k] += i["base"]
            i3.setdefault(k, i)
    b = defaultdict(float)
    i4 = {}
    for i in R["items"]:
        k = (i["trade"], i["family"], i["component_id"])
        if i["category"] == "PROVISIONAL":
            b[k] += i["base"]
        i4.setdefault(k, i)
    agg = defaultdict(lambda: {"n": 0, "delta": 0.0})
    rows = []
    conc4 = {i["component_id"]: i for i in R["items"] if i["trade"] == "CONCRETE"}
    for k in sorted(set(a) | set(b)):
        d = b.get(k, 0.0) - a.get(k, 0.0)
        if abs(d) < 1e-9:
            continue
        cause, note = _cause(i4.get(k), i3.get(k), D, conc4.get(k[2]))
        g = agg[(k[0], k[1], cause, note)]
        g["n"] += 1
        g["delta"] += d
        rows.append({"TRADE": k[0], "FAMILY": k[1], "COMPONENT_ID": k[2], "M3_BASE": a.get(k, 0.0),
                     "M4_BASE": b.get(k, 0.0), "DELTA": d, "CAUSE": cause,
                     "M4_CATEGORY": (i4.get(k) or {}).get("category", "ABSENT")})
    summ = [{"TRADE": t, "FAMILY": f, "CAUSE": c, "COMPONENTS": v["n"], "DELTA": v["delta"], "NOTE": n}
            for (t, f, c, n), v in sorted(agg.items())]
    return rows, summ


# ------------------------------------------------------------------ 3A-3D source-evidence audits
def cb_audit(m3, R):
    D, items = R["generic"]["D"], R["items"]
    b3 = {i["component_id"]: i for i in m3["items"] if i["trade"] == "CONCRETE" and i["family"] == "BEAMS"}
    b4 = {i["component_id"]: i for i in items if i["trade"] == "CONCRETE" and i["family"] == "BEAMS"}
    rows = []
    for sid, rec in sorted(D["sheets"].items()):
        st = rec["sheet"]["storey"]
        for ln in rec.get("cb_lines", []):
            spans = {p: s["index"] for s in ln["spans"] for p in s["pieces"]}
            for pid in ln["pieces"]:
                cid = f"BEAMS:{st}:{pid}"
                x3, x4 = b3.get(cid, {}), b4.get(cid, {})
                rows.append({"LINE_ID": ln["line_id"], "MARK": ln["mark"], "STATE": ln["state"],
                             "DIRECTION": ln.get("direction") or "", "COMPONENT_ID": cid, "SPAN": spans.get(pid, ""),
                             "PRINTED_SPANS_M": " / ".join(f"{x:g}" for x in ln["printed_m"]),
                             "TAKEN_BY_SEQUENCE": pid in (ln.get("inherited") or []),
                             "M3_CATEGORY": x3.get("category", "ABSENT"), "M3_BASE_M3": x3.get("base"),
                             "M4_CATEGORY": x4.get("category", "ABSENT"), "M4_BASE_M3": x4.get("base"),
                             "M4_BLOCKER": x4.get("blocker", "")})
    for i in items:
        if i["trade"] == "CONCRETE" and i.get("blocker") == "UNLABELLED_SPAN_ACROSS_SUPPORT":
            d = i.get("dimensions") or {}
            x3 = b3.get(i["component_id"], {})
            rows.append({"LINE_ID": "", "MARK": d.get("neighbour_mark", ""), "STATE": "ALIGNMENT_ONLY",
                         "COMPONENT_ID": i["component_id"], "M3_CATEGORY": x3.get("category", "ABSENT"),
                         "M3_BASE_M3": x3.get("base"), "M4_CATEGORY": "UNRESOLVED", "M4_BASE_M3": None,
                         "M4_BLOCKER": i["blocker"], "TAKEN_BY_SEQUENCE": False,
                         "PRINTED_SPANS_M": f"alternative {d.get('alternative_as_neighbour_m3')} m3; exposure "
                                            f"{i['exposure_low']:.3f} - {i['exposure_high']:.3f} m3"})
    return rows


def gb_audit(m3, R):
    g3 = {i["component_id"]: i for i in m3["items"] if i["trade"] == "CONCRETE" and i["family"] == "GROUND_BEAMS"}
    out = []
    for r in MR.gb_exterior(R["generic"]["D"], R["items"], R["generic"].get("arch")):
        x3 = g3.get(f"GROUND_BEAMS:GROUND:{r['BAND']}", {})
        out.append(dict(r, M3_LOW_M3=x3.get("low"), M3_BASE_M3=x3.get("base"), M3_HIGH_M3=x3.get("high"),
                        M3_BLOCKER=x3.get("blocker", ""),
                        EVIDENCE_CLASS={"GB_EXTERIOR_DEPTH": "ARCH_WALL_AND_PRINTED_LEVEL",
                                        "GB_EXTERIOR_LEVEL_CONFLICT": "ARCH_WALL_LEVEL_CONFLICT",
                                        "GB_EXTERIOR_NOT_EVIDENCED": "PERIMETER_ONLY"}.get(r["CASE"],
                                                                                           "CLASS_SECTION")))
    return out


def slab_audit(m3, R):
    s3 = {i["component_id"]: i for i in m3["items"] if i["trade"] == "CONCRETE" and i["family"] in ("SLABS",
                                                                                                     "GROUND_SLAB")}
    out = []
    for r in MR.slab_faces(R["generic"]["D"], R["items"]):
        x3 = s3.get(r["COMPONENT_ID"], {})
        cls = {"PRINTED_IN_PANEL": "PRINTED_PANEL_TAG", "SHEET_UNIFORM": "SHEET_TAG_EXTENDED",
               "PROJECT_DEFAULT": "PROJECT_GENERAL_NOTE", "CONVENTION_DEFAULT": "INFERRED"}.get(r["T_BASIS"],
                                                                                              "NO_EVIDENCE")
        b4, b3 = r["BASE_M3"], x3.get("base")
        out.append(dict(r, EVIDENCE_CLASS=cls, M3_CATEGORY=x3.get("category", "ABSENT"), M3_BASE_M3=b3,
                        DELTA_M3=(b4 or 0.0) - (b3 or 0.0)))
    return out


def blinding_audit(m3, R):
    conv = R["conv"]
    ov = R["generic"]["D"].get("blinding_overlap") or {}
    b3 = {i["component_id"]: i for i in m3["items"] if i["family"] == "PLAIN_CONCRETE"}
    out = []
    for i in R["items"]:
        if i["family"] != "PLAIN_CONCRETE":
            continue
        x3 = b3.get(i["component_id"], {})
        out.append({"ITEM": i["component_id"], "M3_BASE_M3": x3.get("base"), "M4_BASE_M3": i.get("base"),
                    "M4_PLAN_M2": (i.get("dimensions") or {}).get("plan_m2_base"),
                    "MEMBERS": (i.get("dimensions") or {}).get("members"), "FORMULA": i.get("formula", "")})
    for k, label in (("area_m2", "beam strip lying on footing blinding"), ("strip_strip_m2", "strips crossing"),
                     ("footing_footing_m2", "footing projections meeting")):
        if ov.get(k):
            out.append({"ITEM": f"COUNTED_ONCE: {label}", "M4_PLAN_M2": ov[k][1]})
    for cid in ("BLINDING_THICKNESS_M", "BLINDING_PROJECTION_M", "BLINDING_UNDER"):
        if cid in conv.items:
            c = conv[cid]
            out.append({"ITEM": f"CONVENTION {cid}", "M4_PLAN_M2": None,
                        "FORMULA": f"base {c.get('base')} ({c.get('provenance')}): {str(c.get('source'))[:160]}"})
    return out


# ------------------------------------------------------------------ 4 OCR review sheet
def ocr_sheet(R, ev):
    rows = R["generic"].get("ocr_review") or []
    down = OR.downstream(rows, R["items"])
    out = []
    for x in rows:
        roles = [r for _, r in x["applies_to"]]
        out.append({"RECORD_ID": x["record_id"], "PAGE": x["page"], "REGION_PT": x["region_pt"],
                    "CROP_FILE": (x["crop"] or "").split("/")[-1], "OCR_STATE": x["ocr_state"],
                    "OCR_RAW": x["ocr_raw"], "OCR_READS": " | ".join(x["ocr_reads"]),
                    "OCR_READS_DISAGREE": x["reads_disagree"], "GLYPH_VALIDATION": x["glyph_validation"] or "",
                    "OCR_VALUE": x["ocr_value"], "INDEPENDENT_READING": x["independent_text"],
                    "INDEPENDENT_VALUE": x["independent_value"], "READER": x["independent_by"],
                    "OUTCOME": x["outcome"], "CONFIDENCE": x["confidence"],
                    "APPLIES_TO": "; ".join(f"{a} {b}" for a, b in x["applies_to"]),
                    "INTERPRETATION": "; ".join(INTERPRETATION.get(r, r) for r in roles),
                    "STATE_AFTER_REVIEW": x["state_after_review"], "PROMOTED": x["promoted"],
                    "DOWNSTREAM_ITEMS": down[x["record_id"]][0], "DOWNSTREAM_KG_BASE": down[x["record_id"]][1]})
    return out


def ocr_html(rows, crops_dir):
    def img(name):
        p = Path(crops_dir) / name if crops_dir else None
        if p and p.exists():
            return f"<img src='data:image/png;base64,{base64.b64encode(p.read_bytes()).decode()}'>"
        return "(crop not available)"
    tr = "".join(f"<tr><td>{r['RECORD_ID']}</td><td>{img(r['CROP_FILE'])}</td><td>{r['OCR_READS']}</td>"
                 f"<td>{r['OCR_VALUE']}</td><td>{r['INDEPENDENT_READING']}</td><td>{r['OUTCOME']}</td>"
                 f"<td>{r['CONFIDENCE']}</td><td>{r['APPLIES_TO']}</td><td>{r['STATE_AFTER_REVIEW']}</td></tr>"
                 for r in rows)
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'><title>OCR review sheet</title><style>"
            "body{font-family:Arial,sans-serif;margin:16px;color:#1a202c;background:#fff}table{border-collapse:"
            "collapse;font-size:11px}td,th{border:1px solid #cbd5e0;padding:3px 6px;vertical-align:middle}"
            "img{max-width:220px;max-height:60px}</style></head><body><h1>OCR review sheet - p.13 typical-detail "
            "records</h1><p>Each crop beside the OCR reads, the parsed value and an independent reading (a model "
            "reading: a check, never a confirmation). No record is promoted; only a person's confirmation can.</p>"
            "<table><tr><th>record</th><th>crop</th><th>OCR reads</th><th>OCR value</th><th>second reading</th>"
            "<th>outcome</th><th>confidence</th><th>applies to</th><th>state after review</th></tr>" + tr +
            "</table></body></html>")


# ------------------------------------------------------------------ RFIs
def rfis(T, R):
    reg = T["MISSING_REINFORCEMENT_REGISTER"]
    roles = Counter(x for r in reg for x in r["MISSING_ROLES"].split(","))
    ex = T["UNRESOLVED_CONCRETE_EXCEPTIONS"]
    cls = Counter(r["BLOCKER"] for r in ex)
    lines = Counter(r["STATE"] for r in T["CB_LINES"])
    gbc = Counter(r["CASE"] for r in T["ARCH_GB_EXTERIOR"])
    ocr = {r["RECORD_ID"]: r for r in T.get("OCR_REVIEW_SHEET", [])}
    q = [
        ("STRUCTURAL", "Continuous beams: the schedule prints no top bars running through the beam. Which top "
                       "continuous bars apply (count, diameter, laps)?", f"{roles.get('CB_TOP_THROUGH', 0)} beam "
                       "pieces (role CB_TOP_THROUGH)"),
        ("STRUCTURAL", "Continuous beams: support top bars are blank in some schedule cells. Are they omitted or "
                       "missing?", f"{roles.get('CB_SUPPORT_TOP', 0)} beam pieces (CB_SUPPORT_TOP)"),
        ("STRUCTURAL", "Beam spans with no label that continue a labelled beam across a support: confirm each "
                       "span's mark and section.", f"{cls.get('UNLABELLED_SPAN_ACROSS_SUPPORT', 0)} spans "
                                                   "(UNRESOLVED_CONCRETE_EXCEPTIONS)"),
        ("STRUCTURAL", "Continuous-beam lines whose printed span list does not fit the drawn spans, or whose "
                       "direction is ambiguous: which end is span 1, and how many spans?",
         ", ".join(f"{k} {v}" for k, v in sorted(lines.items()) if not k.startswith("MATCH_F"))),
        ("STRUCTURAL", "A beam span printed with two different marks (a continuous-beam mark and a simple-beam "
                       "mark): which applies?", f"{cls.get('MULTIPLE_MARKS', 0)} span(s)"),
        ("STRUCTURAL", "Exterior ground beams under an annex / court floor level: the exterior detail's depth from "
                       "that level is not deeper than the class section. Which section applies?",
         f"{gbc.get('GB_EXTERIOR_LEVEL_CONFLICT', 0)} bands"),
        ("STRUCTURAL", "Ground-beam links of the class under 5 m: the OCR read was rejected; the second reading "
                       "gives Ø8/15cm. Please confirm (a person's confirmation lifts it).",
         f"record EV-0007; {roles.get('LINKS', 0)} ground beams miss links in total"),
        ("STRUCTURAL", "Ground-beam links of the class under 2.5 m: no notation is printed in the detail.",
         "LINKS role of the < 2.5 m class"),
        ("STRUCTURAL", "Project default slab thickness: the general note read by local OCR gives 16 cm. Please "
                       "confirm; it applies to every panel without its own tag.",
         f"{sum(1 for r in T['SLAB_FACES'] if r['T_BASIS'] == 'PROJECT_DEFAULT')} panels"),
        ("STRUCTURAL", "Blinding: confirm the 10 cm plain concrete under ground beams and straps as well as under "
                       "footings, and the 10 cm projection.", "BLINDING_UNDER / BLINDING_PROJECTION_M"),
        ("ARCHITECTURAL", "Openings under a beam: is there masonry between the head of the opening and the beam "
                          "soffit (a lintel), or does the beam act as the lintel?",
         f"{cls.get('LINTEL_NEED_UNDER_BEAM', 0) + cls.get('LINTEL_PARTIAL_BEAM', 0)} openings"),
        ("STRUCTURAL", "Stairs: the waist thickness and the riser count of each flight (the plan holds part of "
                       "each stair only).", "2 stair zones"),
        ("STRUCTURAL", "Column necks / column types without a schedule row.",
         f"{cls.get('NECK_SECTION_OR_FOOTING', 0) + cls.get('TYPE_NOT_IN_SCHEDULE', 0)} columns"),
        ("STRUCTURAL", "Slab panels without a bar tag inside the panel.",
         f"{sum(1 for r in reg if r['FAMILY'] == 'SLABS' and 'no bar tag' in r['REASON'])} panels"),
        ("STRUCTURAL", "A footing labelled with two types and no outline: which type?", "1 footing"),
    ]
    _ = ocr
    return [{"RFI": f"RFI-M4-{k:02d}", "TO": to, "QUESTION": qq, "SCOPE": sc} for k, (to, qq, sc) in enumerate(q, 1)]


# ------------------------------------------------------------------ hygiene
def check_text(name, text, bench):
    if HYGIENE.search(text):
        raise SystemExit(f"hygiene: {name} carries forbidden text")
    if re.search(r"(?i)[a-z]:\\\\|\\\\[a-z0-9_]+\\\\|\.dwg\b|/home/|/tmp/", text):
        raise SystemExit(f"hygiene: {name} carries a file path")
    leak = [b for b in bench if re.search(r"(?<![\d.])" + re.escape(b) + r"(?!\d)", text)]
    if leak:
        raise SystemExit(f"benchmark firewall: {name} carries an external value")


def main(argv):
    a = dict(zip(argv[::2], argv[1::2]))
    m3 = m3_snapshot(Path(a["--m3-root"]).resolve())
    R = m4_run(a.get("--cache"))
    g = R["generic"]
    T = dict(CLI.m4_tables(R))
    ev = json.loads(EVIDENCE.read_text())
    T["OCR_REVIEW_SHEET"] = ocr_sheet(R, ev)
    IC = _module(PKG / "independent_checks.py", "m4ic")
    ic = IC.checks(g["D"], R["items"], g["register"], R["conv"], g.get("arch"))
    recon, recon_sum = reconciliation(m3, R)
    prev = {i["component_id"]: i for i in m3["items"]}
    m3_state = m3["rebar_states"]
    files = {
        "02_BEFORE_AFTER_QUANTITIES.csv": _csv(before_after(m3, R)),
        "03_RECONCILIATION_M3_TO_M4.csv": _csv(recon),
        "03_RECONCILIATION_SUMMARY.csv": _csv(recon_sum),
        "03A_CB_SPAN_AUDIT.csv": _csv(cb_audit(m3, R)),
        "03B_EXTERIOR_GB_AUDIT.csv": _csv(gb_audit(m3, R)),
        "03C_SLAB_THICKNESS_AUDIT.csv": _csv(slab_audit(m3, R)),
        "03D_BLINDING_AUDIT.csv": _csv(blinding_audit(m3, R)),
        "04_OCR_REVIEW_SHEET.csv": _csv(T["OCR_REVIEW_SHEET"]),
        "05_CB_LINES.csv": _csv(T["CB_LINES"]),
        "05_CB_PHYSICAL_BARS.csv": _csv(T["CB_PHYSICAL_BARS"]),
        "06_MISSING_REINFORCEMENT_REGISTER.csv": _csv(T["MISSING_REINFORCEMENT_REGISTER"]),
        "06_MISSING_REINFORCEMENT_SUMMARY.csv": _csv(T["MISSING_REINFORCEMENT_SUMMARY"]),
        "07_UNRESOLVED_CONCRETE_EXCEPTIONS.csv": _csv(T["UNRESOLVED_CONCRETE_EXCEPTIONS"]),
        "07_LINTEL_OPENINGS.csv": _csv(T["LINTEL_OPENINGS"]),
        "08_CONFLICTS.csv": _csv(T["CONFLICTS"]),
        "08_OCR_DERIVED_ITEMS.csv": _csv(T["OCR_DERIVED_ITEMS"]),
        "10_INDEPENDENT_VALIDATION.csv": _csv(ic),
        "12_RFIS.csv": _csv(rfis(T, R)),
    }
    trans = Counter()
    m3reg = {}
    for i in m3["items"]:
        pass
    reg4 = {r["COMPONENT_ID"]: r["REBAR_STATE"] for r in g["register"]}
    numbers = {
        "m3_families": m3["families"], "m3_rebar_states": m3_state,
        "m4_rebar_states": dict(Counter(r["REBAR_STATE"] for r in g["register"])),
        "m4_missing_register_rows": len(T["MISSING_REINFORCEMENT_REGISTER"]),
        "m4_missing_by_existence": dict(Counter(r["EXISTENCE"] for r in T["MISSING_REINFORCEMENT_REGISTER"])),
        "m4_missing_by_previous_state": dict(Counter(f"{r['PREVIOUS_STATE'] or 'NA'}>{r['REBAR_STATE']}"
                                                     for r in T["MISSING_REINFORCEMENT_REGISTER"])),
        "m4_unresolved_concrete": dict(Counter(r["FAMILY"] for r in T["UNRESOLVED_CONCRETE_EXCEPTIONS"])),
        "m4_unresolved_concrete_classes": dict(Counter(r["CLASS"] for r in T["UNRESOLVED_CONCRETE_EXCEPTIONS"])),
        "cb_lines": dict(Counter(r["STATE"] for r in T["CB_LINES"])),
        "gb_exterior_cases": dict(Counter(r["CASE"] for r in T["ARCH_GB_EXTERIOR"])),
        "gb_arch_classes": dict(Counter(r["ARCH_CLASS"] for r in T["ARCH_GB_EXTERIOR"])),
        "slab_thickness_basis": dict(Counter(r["T_BASIS"] for r in T["SLAB_FACES"])),
        "lintels": dict(Counter(r["CATEGORY"] for r in T["LINTEL_OPENINGS"])),
        "ocr_review": dict(Counter(r["OUTCOME"] for r in T["OCR_REVIEW_SHEET"])),
        "independent_checks": dict(Counter(r["RESULT"] for r in ic)),
        "summary": {k: R["summary"][k] for k in ("totals", "rebar_completeness", "missing_steel_components",
                                                 "continuous_beam_lines", "ocr_review", "architectural_evidence")},
        "m3_seconds": m3["seconds"], "m4_seconds": R["seconds"],
    }
    _ = (trans, m3reg, reg4, prev)
    if a.get("--heldout"):
        h = {p.stem: json.loads(p.read_text())["summary"] for p in sorted(Path(a["--heldout"]).glob("*.json"))}
        files["11_HELDOUT_EVALUATION.json"] = json.dumps(h, indent=1)
        numbers["heldout"] = h
    files["00_NUMBERS.json"] = json.dumps(numbers, indent=1, default=str)
    pf = _module(ROOT / "research/alsenan_m1_usable_boq/post_freeze/post_freeze_comparison.py", "m1pf4")
    try:
        m2b = _module(ROOT / "research/urban_engine_m2_generalization/build_m2_reports.py", "m2b4")
        files["09_BENCHMARK_POSITIONS.csv"] = _csv(m2b.benchmark_positions(R["items"]))
    except (FileNotFoundError, KeyError, OSError) as e:          # the comparison data is private
        files["09_BENCHMARK_POSITIONS.csv"] = _csv([{"STATE": "NOT_AVAILABLE", "WHY": type(e).__name__}])
    for name, text in files.items():
        check_text(name, text, pf.BENCH)
    # the route G registers of the M4 run (CSV / JSON / SVG / HTML are committed; xlsx and pdf are generated only)
    out = PKG / "st7757_route_g"
    res = CLI.write_all(R, out, as_of="2026-10-11", pdf=bool(a.get("--visual")), xlsx=True)
    for p in sorted(out.rglob("*")):
        if p.is_file() and p.suffix in (".csv", ".json", ".html", ".svg") and p.name != "run_log.json":
            check_text(str(p.relative_to(PKG)), p.read_text(encoding="utf-8"), pf.BENCH)
    for name, text in files.items():
        (PKG / name).write_text(text, encoding="utf-8")
    if a.get("--visual"):
        vis = Path(a["--visual"])
        vis.mkdir(parents=True, exist_ok=True)
        html = ocr_html(T["OCR_REVIEW_SHEET"], a.get("--crops"))
        (vis / "04_OCR_REVIEW_SHEET.html").write_text(html, encoding="utf-8")
        from tools import urban_structural_boq as M1
        M1.print_pdf(vis / "04_OCR_REVIEW_SHEET.html", vis / "04_OCR_REVIEW_SHEET.pdf")
        for nm in ("M4_VISUAL_QA.pdf", "STRUCTURAL_BOQ.xlsx", "BOQ_REPORT.pdf"):
            if (out / nm).exists():
                (vis / nm).write_bytes((out / nm).read_bytes())
    print(json.dumps({"written": sorted(files), "route_g": len(res["files"]), "numbers": {
        k: numbers[k] for k in ("m4_rebar_states", "m4_missing_by_existence", "independent_checks", "ocr_review")}},
        indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1:])
