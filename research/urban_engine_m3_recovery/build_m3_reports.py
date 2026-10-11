"""M3 package builder: before / after on the Alsenan ST7757 set, reconciliation, reinforcement completeness, coverage,
benchmark positions and the held-out evaluation summary - every number from a live run.

    python3 -I research/urban_engine_m3_recovery/build_m3_reports.py --m2-root M2_WORKTREE [--heldout DIR]

M2_WORKTREE is the M2 commit (c5123a7) checked out separately (git worktree add DIR c5123a7): the M2 numbers are
re-run there in their own process, never read from edited files and never written into the frozen M2 package. The
frozen M1 replay is read from its committed registers. External estimates appear as positions only. Every file is
refused when it carries owner text, Arabic source text, a firewalled benchmark number or a file path.
"""

from __future__ import annotations

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

from engine.source import family_coverage as FC              # noqa: E402
from engine.source import generic_route as GR               # noqa: E402
from engine.source import provisional_estimate as PE        # noqa: E402
from tools import urban_intake as UI                        # noqa: E402

DRAWING = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
PROFILE = PKG / "profile_st7757_m3.json"
EVIDENCE = PKG / "evidence/DETAIL_EVIDENCE.json"
GENERIC = ROOT / "engine/profiles/URBAN_M3_GENERIC_CONVENTIONS_V2.json"
M1 = ROOT / "research/alsenan_m1_usable_boq/boq"
M2PKG = ROOT / "research/urban_engine_m2_generalization"
HYGIENE = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}|(?i:als[ey]?n[ya]?an)")
SIX = ("FOOTINGS", "COLUMNS", "BEAMS", "GROUND_BEAMS", "SLABS", "GROUND_SLAB")
STOREY_OF = {"GF_ROOF": "GF", "GFRS": "GF", "1F_ROOF": "1F", "FFRS": "1F", "2F_ROOF": "2F", "SFRS": "2F"}
CLASSES = ("Corrected omission", "Corrected double count", "Source interpretation", "Provisional assumption",
           "Remaining extraction failure", "Remaining source ambiguity")


def _rows(p):
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


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


def _module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ runs
def m2_snapshot(m2_root):
    """the M2 engine on the same drawing, in its own process (its modules never meet the current ones)."""
    out = PKG / ".m2_snapshot.json"
    subprocess.run([sys.executable, "-I", str(PKG / "st7757_snapshot.py"), "--engine-root", str(m2_root),
                    "--profile", str(Path(m2_root) / "research/urban_engine_m2_generalization/profile_st7757.json"),
                    "--out", str(out)], check=True, capture_output=True)
    res = json.loads(out.read_text())
    out.unlink()
    return res


def m3_run():
    I = UI.read(DRAWING)
    conv = GR.merge_conventions(json.loads(GENERIC.read_text()), json.loads(PROFILE.read_text()))
    ev = json.loads(EVIDENCE.read_text())
    D = GR.detect(I, typical_widths_m=GR.typical_gb_widths(conv))
    items, reg, risk = GR.items_from(D, conv, GR.storey_heights(conv), evidence=ev)
    PE.check(items, conv)
    return D, conv, ev, items, reg, risk


# ------------------------------------------------------------------ 1 detection before / after
def detection_rows(m2, D, items, risk):
    snap3 = {}
    for sid, rec in sorted(D["sheets"].items()):
        r = {}
        if rec.get("footings"):
            r["footings"] = Counter(f["state"] for f in rec["footings"])
        if "beams" in rec:
            r["bands"] = Counter(b["state"] for b in rec["beams"])
            r["marks"] = Counter(m["state"] for m in rec.get("marks", []))
        if rec.get("slab"):
            r["faces"] = Counter(f["class"] for f in rec["slab"]["faces"])
        if rec.get("straps"):
            r["straps"] = Counter(b["state"] for b in rec["straps"]["bands"])
        snap3[sid] = r
    rows = []
    for sid in sorted(set(m2["detection"]) | set(snap3)):
        a, b = m2["detection"].get(sid, {}), snap3.get(sid, {})
        role = a.get("role") or D["sheets"][sid]["sheet"]["role"]
        for kind in ("footings", "bands", "marks", "faces", "straps"):
            ka, kb = a.get(kind) or {}, b.get(kind) or {}
            for state in sorted(set(ka) | set(kb)):
                if ka.get(state, 0) or kb.get(state, 0):
                    rows.append({"SHEET": sid, "ROLE": role, "OBJECT": kind.upper(), "STATE": state,
                                 "M2": ka.get(state, 0), "M3": kb.get(state, 0),
                                 "CHANGE": kb.get(state, 0) - ka.get(state, 0)})
    rk2, rk3 = m2["risk"], Counter(r["KIND"] for r in risk)
    for k in sorted(set(rk2) | set(rk3)):
        rows.append({"SHEET": "ALL", "ROLE": "COVERAGE_RISK", "OBJECT": "RISK", "STATE": k, "M2": rk2.get(k, 0),
                     "M3": rk3.get(k, 0), "CHANGE": rk3.get(k, 0) - rk2.get(k, 0)})
    return rows


# ------------------------------------------------------------------ 2 families: M2 / M3 / frozen
def family_rows(m2, items, trade):
    frozen = {(r["trade"], r["family"]): r for r in _rows(M1 / "FAMILY_SUMMARY.csv")}
    g3 = {(r["trade"], r["family"]): r for r in PE.rollup(items, ("trade", "family"))}
    fams = sorted({k[1] for k in frozen if k[0] == trade} | {k[1] for k in g3 if k[0] == trade} |
                  {k.split("|")[1] for k in m2["families"] if k.startswith(trade + "|")},
                  key=lambda f: (f not in SIX, SIX.index(f) if f in SIX else 0, f))
    out = []
    for f in fams:
        a = m2["families"].get(f"{trade}|{f}", {})
        b = g3.get((trade, f), {})
        z = frozen.get((trade, f), {})
        out.append({"FAMILY": f, "UNIT": "m3" if trade == "CONCRETE" else "kg", "IN_CORE_SIX": f in SIX,
                    "M2_GENERIC_BASE": _f(a.get("PROVISIONAL_BASE")), "M2_N_UNRESOLVED": a.get("N_UNRESOLVED", 0),
                    "M3_LOW": _f(b.get("PROVISIONAL_LOW")), "M3_BASE": _f(b.get("PROVISIONAL_BASE")),
                    "M3_HIGH": _f(b.get("PROVISIONAL_HIGH")), "M3_N_UNRESOLVED": b.get("N_UNRESOLVED", 0),
                    "M3_EXPOSURE_LOW": _f(b.get("UNRESOLVED_EXPOSURE_LOW")),
                    "M3_EXPOSURE_HIGH": _f(b.get("UNRESOLVED_EXPOSURE_HIGH")),
                    "FROZEN_M1_PLANNING_BASE": _f(z.get("PLANNING_BASE")), "FROZEN_M1_N_UNRESOLVED": z.get("N_UNRESOLVED", ""),
                    "M3_MINUS_M2": _f(b.get("PROVISIONAL_BASE")) - _f(a.get("PROVISIONAL_BASE")),
                    "M3_MINUS_FROZEN": _f(b.get("PROVISIONAL_BASE")) - _f(z.get("PLANNING_BASE"))})
    tot = {k: sum(r[k] for r in out if r["IN_CORE_SIX"]) for k in ("M2_GENERIC_BASE", "M3_LOW", "M3_BASE", "M3_HIGH",
                                                                    "FROZEN_M1_PLANNING_BASE")}
    out.append(dict({"FAMILY": "CORE_SIX_TOTAL", "UNIT": out[0]["UNIT"] if out else "", "IN_CORE_SIX": True}, **tot,
                    M3_MINUS_M2=tot["M3_BASE"] - tot["M2_GENERIC_BASE"],
                    M3_MINUS_FROZEN=tot["M3_BASE"] - tot["FROZEN_M1_PLANNING_BASE"]))
    return out


# ------------------------------------------------------------------ 3 reconciliation M2 -> M3, tagged by cause
def _tags(D):
    """component id -> (feature, class, note) for the components an M3 change made or altered."""
    t = {}
    for sid, rec in D["sheets"].items():
        for f in rec.get("footings", []):
            cid = f["member_id"]
            if f["state"] == "LABEL_ONLY":
                t[cid] = ("FOOTING_LABEL_ONLY", "Provisional assumption", "schedule size, outline not confirmed")
            elif f["state"] == "LABEL_TYPE_CONFLICT":
                t[cid] = ("FOOTING_LABEL_TYPE_CONFLICT", "Remaining source ambiguity", "two types labelled at one "
                                                                                       "footing; larger type base")
            elif not any(ch.isdigit() for ch in f["mark"]):
                t[cid] = ("FOOTING_TYPE_MARK_WITHOUT_NUMBER", "Corrected omission", f"type mark {f['mark']} has no "
                                                                                    "number (the M2 pattern refused it)")
            elif f.get("outline_kind") == "POLYGON" or str(f.get("outline_kind", "")).startswith("TEMPLATE") or \
                    f.get("binding") in ("LABEL_NEAR_OUTLINE", "LABEL_OUTSIDE_NEAREST_OUTLINE"):
                t[cid] = ("FOOTING_OUTLINE_RECOVERED", "Corrected omission", f"{f.get('outline_kind')} / "
                                                                             f"{f.get('binding')}")
        rule_of = {b["band_id"]: b.get("rule") for b in rec.get("bands", [])}
        fam = "GROUND_BEAMS" if rec["sheet"]["role"] == "GROUND_BEAM_PLAN" else "BEAMS"
        for b in rec.get("beams", []):
            cid = f"{fam}:{rec['sheet']['storey']}:{b['band_id']}"
            rule = rule_of.get(b["band_id"])
            if rule in ("INTERVENING_FACE_PART", "SHARED_FACE_UNAMBIGUOUS_PART"):
                t[cid] = (rule, "Corrected omission", "strip the pairing had dropped whole")
            elif rule == "SINGLE_FACE_INFERRED":
                t[cid] = (rule, "Provisional assumption", "one face drawn, second at the scheduled width")
            elif "INHERITED" in (b.get("binding") or "") and b.get("state") == "BOUND":
                t.setdefault(cid, ("INHERITED_ALONG_LINE", "Provisional assumption", "section of the collinear mark"))
            if fam == "GROUND_BEAMS" and "OUTSIDE" in rec.get("band_sides", {}).get(b["band_id"], []):
                t[cid] = ("GB_EXTERIOR_DETAIL", "Provisional assumption", "perimeter band, exterior depth from levels")
        for b in (rec.get("straps") or {}).get("bands", []):
            t[f"GROUND_BEAMS:FOUNDATION:{b['band_id']}"] = ("STRAP_BEAM", "Corrected omission" if b["state"] == "BOUND"
                                                            else "Remaining source ambiguity", b["state"])
        if rec.get("slab"):
            sfam = "GROUND_SLAB" if rec["sheet"]["role"] == "GROUND_BEAM_PLAN" else "SLABS"
            for f in rec["slab"]["faces"]:
                cid = f"{sfam}:{rec['sheet']['storey']}:{f['face_id']}"
                if f.get("region") == "STAIR_ZONE":
                    t[cid] = ("STAIR_ZONE_EXCLUDED", "Source interpretation", f["region_reason"])
                elif f.get("region") == "UNRESOLVED":
                    t[cid] = ("FREE_COLUMN_CELL", "Remaining source ambiguity", f["region_reason"])
                elif f["class"] == "OPEN_BOUNDARY" and f.get("region") in ("STRUCTURAL_SLAB", "GROUND_SLAB"):
                    t[cid] = ("OPEN_BOUNDARY_RECOVERED", "Corrected omission", f["region_reason"])
    return t


def reconciliation(m2, D, items, reg):
    """component by component, M2 -> M3, per trade and family: the same component with a new value, a component only
    M3 has, a component only M2 had. Each M3 change carries the cause tag of the M3 rule that made it, and its class
    (CLASSES); untagged differences are reported as such, never hidden in a total."""
    tags = _tags(D)

    def tag_of(i):
        tg = tags.get(i["component_id"])
        if i["family"] == "PLAIN_CONCRETE":
            tg = ("BLINDING", "Corrected omission", "printed 10 cm plain concrete; projection a convention")
        elif i["family"] == "COLUMNS" and i["storey"] == "FOUNDATION":
            tg = ("COLUMN_NECK", "Corrected omission", "neck height from the printed levels")
        elif i["trade"] == "REINFORCEMENT" and i["family"] == "GROUND_BEAMS" and \
                i["blocker"] == "OCR_DERIVED_UNREVIEWED":
            tg = ("GB_BARS_FROM_PDF_EVIDENCE", "Corrected omission", "typical-detail bars, OCR read, vector-glyph "
                                                                     "checked, unreviewed")
        elif tg and tg[0] == "STRAP_BEAM" and tg[2] != "BOUND":
            tg = ("STRAP_BEAM_DUPLICATE_ROW", "Remaining source ambiguity", "two schedule rows; the drawn width "
                                                                            "selects one")
        return tg
    a = defaultdict(float)
    for i in m2["items"]:
        if i["category"] == "PROVISIONAL":
            a[(i["trade"], i["family"], i["component_id"])] += i["base"]
    b, btag = defaultdict(float), {}
    for i in items:
        if i["category"] == "PROVISIONAL":
            k = (i["trade"], i["family"], i["component_id"])
            b[k] += i["base"]
            btag.setdefault(k, tag_of(i))
    unres = {i["component_id"]: i for i in items if i["category"] == "UNRESOLVED" and i["trade"] == "CONCRETE"}
    state3 = {r["COMPONENT_ID"]: r["REBAR_STATE"] for r in reg}
    agg = defaultdict(lambda: {"n": 0, "delta": 0.0})
    for k in set(a) | set(b):
        trade, fam, cid = k
        d = b.get(k, 0.0) - a.get(k, 0.0)
        if abs(d) < 1e-9:
            continue
        kind = "SAME_COMPONENT_NEW_VALUE" if k in a and k in b else ("ONLY_M3" if k in b else "ONLY_M2")
        tg = btag.get(k) if k in b else None
        if kind == "ONLY_M2" and k[0] == "CONCRETE" and cid in unres:
            u = unres[cid]
            tg = tags.get(cid) or (f"NOW_UNRESOLVED", "Remaining extraction failure", "")
            tg = (f"NOW_UNRESOLVED:{u['blocker']}", tg[1], f"held out of the totals: {tg[2] or u['blocker']}")
        elif kind == "ONLY_M2" and state3.get(cid) == "EXPLICIT_NONE":
            tg = ("ABSENT_ON_STOREY_PLAN", "Source interpretation", "no outline on that storey's slab plan")
        if tg:
            feat, cls, note = tg
        elif kind == "ONLY_M2":
            feat, cls, note = "REMOVED_OR_RENAMED", "", "an M2 component M3 does not hold under this id (topology " \
                                                       "changes re-number faces and bands)"
        elif kind == "ONLY_M3":
            feat, cls, note = "NEW_OR_RENAMED", "", "an M3 component M2 did not hold under this id"
        else:
            feat, cls, note = "VALUE_CHANGED", "", "same component, value changed by an engine rule"
        g = agg[(trade, fam, kind, feat, cls, note)]
        g["n"] += 1
        g["delta"] += d
    out = [{"TRADE": t, "FAMILY": f, "KIND": kd, "CHANGE": ft, "CLASS": c, "COMPONENTS": v["n"], "DELTA": v["delta"],
            "NOTE": n} for (t, f, kd, ft, c, n), v in sorted(agg.items())]
    for i in items:                                              # what M3 holds out of the totals, and why
        if i["category"] == "UNRESOLVED" and i["trade"] == "CONCRETE":
            tg = tags.get(i["component_id"])
            cls = tg[1] if tg else ("Remaining source ambiguity" if i["blocker"] in (
                "AMBIGUOUS", "MULTIPLE_MARKS", "SCHEDULE_CONFLICT", "SLAB_CELL_FREE_COLUMNS") else
                "Remaining extraction failure")
            out.append({"TRADE": "CONCRETE", "FAMILY": i["family"], "KIND": "M3_UNRESOLVED",
                        "CHANGE": i["blocker"], "CLASS": cls, "COMPONENTS": 1, "DELTA": 0.0,
                        "NOTE": f"exposure {i['exposure_low'] or 0:.3f} - {i['exposure_high'] or 0:.3f} m3, not in "
                                f"any total ({i['component_id']})"})
    summ = []
    for (trade, fam) in sorted({(k[0], k[1]) for k in set(a) | set(b)}):
        A = sum(v for k, v in a.items() if k[:2] == (trade, fam))
        B = sum(v for k, v in b.items() if k[:2] == (trade, fam))
        tagged = sum(r["DELTA"] for r in out if r["TRADE"] == trade and r["FAMILY"] == fam and r["CLASS"] and
                     r["KIND"] != "M3_UNRESOLVED")
        summ.append({"TRADE": trade, "FAMILY": fam, "M2_BASE": A, "M3_BASE": B, "DELTA": B - A,
                     "DELTA_WITH_A_CAUSE_TAG": tagged, "DELTA_UNTAGGED": B - A - tagged})
    return out, summ


# ------------------------------------------------------------------ 4 beams by mark against the frozen replay
def beams_by_mark(items):
    fz = defaultdict(lambda: [0.0, 0])
    for cat in ("PROVISIONAL", "VERIFIED"):
        for r in _rows(M1 / f"{cat}_REGISTER.csv"):
            if r["TRADE"] != "CONCRETE" or r["FAMILY"] != "BEAMS":
                continue
            m = re.match(r"(?:BM|CBO)-([0-9A-Z_]+)-([A-Z]+\d+[A-Z]?)", r["COMPONENT_ID"])
            if m and STOREY_OF.get(m.group(1)):
                k = (STOREY_OF[m.group(1)], m.group(2))
                fz[k][0] += _f(r["BASE"])
                fz[k][1] += 1
    fu = Counter()
    for r in _rows(M1 / "UNRESOLVED_REGISTER.csv"):
        m = re.match(r"(?:BM|CBO)-([0-9A-Z_]+)-([A-Z]+\d+[A-Z]?)", r["COMPONENT_ID"])
        if r["TRADE"] == "CONCRETE" and r["FAMILY"] == "BEAMS" and m and STOREY_OF.get(m.group(1)):
            fu[(STOREY_OF[m.group(1)], m.group(2))] += 1
    g = defaultdict(lambda: [0.0, 0, 0])
    for i in items:
        if i["trade"] != "CONCRETE" or i["family"] != "BEAMS":
            continue
        m = re.search(r"; mark (\S+) ", i["source"])
        k = (i["storey"], m.group(1) if m else "(no mark)")
        if i["category"] == "PROVISIONAL":
            g[k][0] += i["base"]
            g[k][1] += 1
        else:
            g[k][2] += 1
    out = []
    for k in sorted(set(fz) | set(g) | set(fu)):
        a, b = fz.get(k, [0.0, 0]), g.get(k, [0.0, 0, 0])
        out.append({"STOREY": k[0], "MARK": k[1], "FROZEN_M1_BASE_M3": a[0], "FROZEN_M1_ITEMS": a[1],
                    "FROZEN_M1_UNRESOLVED": fu.get(k, 0), "M3_BASE_M3": b[0], "M3_ITEMS": b[1], "M3_UNRESOLVED": b[2],
                    "M3_MINUS_FROZEN": b[0] - a[0]})
    return out


# ------------------------------------------------------------------ 5 the 89 historical components
def completeness_89(D, reg):
    m2b = _module(M2PKG / "build_m2_reports.py", "m2b")
    rows = m2b.reinforcement_completeness(D, reg)
    old = {r["M1_COMPONENT_ID"]: r for r in _rows(M2PKG / "05_REINFORCEMENT_COMPLETENESS_89.csv")}
    out = []
    for r in rows:
        o = old.get(r["M1_COMPONENT_ID"], {})
        out.append({"M1_COMPONENT_ID": r["M1_COMPONENT_ID"], "FAMILY": r["FAMILY"], "STOREY": r["STOREY"],
                    "M1_CATEGORY": r["M1_CATEGORY"], "M2_GENERIC_REBAR_STATE": o.get("GENERIC_REBAR_STATE", ""),
                    "M3_MATCH_METHOD": r["MATCH_METHOD"], "M3_GENERIC_COMPONENT_ID": r["GENERIC_COMPONENT_ID"],
                    "M3_GENERIC_REBAR_STATE": r["GENERIC_REBAR_STATE"], "M3_REASON": r["GENERIC_REASON"],
                    "M3_PROVISIONAL_KG": r["GENERIC_PROVISIONAL_KG"],
                    "CHANGE": "SAME" if o.get("GENERIC_REBAR_STATE") == r["GENERIC_REBAR_STATE"] else
                              f"{o.get('GENERIC_REBAR_STATE', '?')} -> {r['GENERIC_REBAR_STATE']}"})
    return out


def performance(m2, cold, warm):
    m2log = json.loads((M2PKG / "alsenan_route_g/run_log.json").read_text())
    steps = lambda d: {x["step"]: x["seconds"] for x in d["steps"]}            # noqa: E731
    return {"note": "machine timings of the one-command run on ST7757 (same container); the export step prints two "
                    "PDFs with Chromium",
            "m2_cli_run": {"steps": steps(m2log), "seconds_compute": m2log["seconds_compute"]},
            "m3_cli_run_cold_cache": {"steps": steps(cold), "seconds_compute": cold["seconds_compute"]},
            "m3_cli_run_warm_cache": {"steps": steps(warm), "seconds_compute": warm["seconds_compute"]},
            "m2_engine_live": m2["seconds"],
            "caching": "the intake of a drawing is cached by its sha256 and the intake code digest (--cache DIR): a "
                       "warm run skips the DXF read",
            "incremental_recalculation": "a convention change re-prices from the detected model without re-reading "
                                         "or re-detecting (route_generic rebuild; SENSITIVITY.csv is built that way, "
                                         "one rebuild per alternative)"}


def dashboard(fam_c, fam_s, rc, cov, held, numbers):
    def table(rows, cols, fmt=None):
        h = "".join(f"<th>{c}</th>" for c in cols)
        b = "".join("<tr>" + "".join(f"<td>{(fmt or {}).get(c, lambda v: v)(r.get(c, ''))}</td>" for c in cols) +
                    "</tr>" for r in rows)
        return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"
    n = lambda v: f"{v:,.2f}" if isinstance(v, (int, float)) else v                # noqa: E731
    sheets = ["SH10_FOUNDATION_PLAN_FOUNDATION", "SH08_GROUND_BEAM_PLAN_GROUND", "SH06_SLAB_PLAN_GF",
              "SH04_SLAB_PLAN_1F", "SH02_SLAB_PLAN_2F"]
    def svg(p):                                    # inline: the page is self-contained (no paths, no names)
        return p.read_text(encoding="utf-8") if p.exists() else "<p>(not generated)</p>"
    before = sorted((M2PKG).glob("*/overlays"))
    imgs = "".join(f"<h3>{sid}</h3><div class='pair'><figure>{svg(before[0] / (sid + '.svg')) if before else ''}"
                   f"<figcaption>before (M2 engine)</figcaption></figure><figure>"
                   f"{svg(PKG / 'st7757_route_g/overlays' / (sid + '.svg'))}<figcaption>after (M3 engine)</figcaption>"
                   "</figure></div>" for sid in sheets)
    cols = ["FAMILY", "M2_GENERIC_BASE", "M3_LOW", "M3_BASE", "M3_HIGH", "M3_N_UNRESOLVED", "FROZEN_M1_PLANNING_BASE"]
    hrows = [dict(SET=k, **{x: v[x]["recall"] for x in ("detect_beams",)}, MAE_BEAMS=v["mean_abs_error"].get(
        "BEAMS_TOTAL_DEPTH"), MAE_FOOTINGS=v["mean_abs_error"].get("FOOTINGS"), SUCCESS=v["end_to_end_success"])
             for k, v in sorted(held.items())]
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>M3 coverage dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{{font-family:Arial,sans-serif;margin:16px;color:#1a202c;background:#fff}}table{{border-collapse:collapse;
margin:8px 0 18px}}td,th{{border:1px solid #cbd5e0;padding:3px 7px;font-size:12px}}th{{background:#edf2f7}}
.pair{{display:flex;gap:12px;flex-wrap:wrap}}figure{{margin:0;flex:1 1 420px;min-width:0}}figure svg{{width:100%;
height:auto;border:1px solid #a0aec0}}
.b{{background:#fff5f5;border:1px solid #feb2b2;padding:8px}}</style></head><body>
<h1>M3 real-drawing recovery: coverage dashboard (ST7757)</h1>
<p class="b">Planning estimate engine. Not engineering-approved. No quantity is construction-approved; categories are
Verified / Provisional / Unresolved / Not detected, and a new project is never Verified. The gate stays INCOMPLETE.</p>
<h2>Concrete by family (m3)</h2>{table(fam_c, cols, {c: n for c in cols[1:]})}
<h2>Reinforcement by family (kg)</h2>{table(fam_s, cols, {c: n for c in cols[1:]})}
<h2>Reinforcement state of every concrete component</h2>
{table([dict(STATE=k, COMPONENTS=v) for k, v in sorted(rc["totals"].items())], ["STATE", "COMPONENTS"])}
<p>Components without a full bar quantity: {rc["missing_steel_components"]} (counts, never 0 kg).</p>
<h2>Families outside the core six</h2>{table(cov, ["FAMILY", "STATE", "EVIDENCE", "NEEDED"])}
<h2>Held-out synthetic drawings (seeds 501-540, never used before)</h2>
{table(hrows, ["SET", "SUCCESS", "detect_beams", "MAE_BEAMS", "MAE_FOOTINGS"])}
<h2>Before / after overlays</h2>{imgs}
<p>Evidence records: {numbers["evidence_records"]}.</p></body></html>
"""


def check_text(name, text, bench):
    if HYGIENE.search(text):
        raise SystemExit(f"hygiene: {name} carries forbidden text")
    if re.search(r"(?i)[a-z]:\\\\|\\\\[a-z0-9_]+\\\\|\.dwg\b", text):
        raise SystemExit(f"hygiene: {name} carries a file path")
    leak = [b for b in bench if re.search(r"(?<![\d.])" + re.escape(b) + r"(?!\d)", text)]
    if leak:
        raise SystemExit(f"benchmark firewall: {name} carries an external value")


def main(argv):
    a = dict(zip(argv[::2], argv[1::2]))
    m2 = m2_snapshot(Path(a["--m2-root"]).resolve())
    D, conv, ev, items, reg, risk = m3_run()
    rc = GR.rebar_completeness(items, reg)
    cov = FC.coverage(D, items, risk, GR.scope_scan(D), ev)
    m2b = _module(M2PKG / "build_m2_reports.py", "m2b_bench")
    bench_rows = m2b.benchmark_positions(items)
    recon, recon_sum = reconciliation(m2, D, items, reg)
    files = {
        "02_BEFORE_AFTER_DETECTION.csv": _csv(detection_rows(m2, D, items, risk)),
        "03_CONCRETE_BY_FAMILY.csv": _csv(family_rows(m2, items, "CONCRETE")),
        "04_REINFORCEMENT_BY_FAMILY.csv": _csv(family_rows(m2, items, "REINFORCEMENT")),
        "05_RECONCILIATION_M2_TO_M3.csv": _csv(recon),
        "05_RECONCILIATION_SUMMARY.csv": _csv(recon_sum),
        "06_BEAMS_BY_MARK_VS_FROZEN.csv": _csv(beams_by_mark(items)),
        "07_REINFORCEMENT_COMPLETENESS_89.csv": _csv(completeness_89(D, reg)),
        "08_MISSING_STEEL_BY_FAMILY_STOREY.csv": _csv(rc["by_family_storey"]),
        "09_BENCHMARK_POSITIONS.csv": _csv(bench_rows),
        "10_UNRESOLVED_REGISTER.csv": _csv([{k: i[k] for k in ("item_id", "component_id", "trade", "family",
                                                               "storey", "blocker", "exposure_low", "exposure_high",
                                                               "expression")} for i in items
                                            if i["category"] == "UNRESOLVED"]),
        "11_NOT_DETECTED_REGISTER.csv": _csv(cov),
        "11_COVERAGE_RISK.csv": _csv([{"KIND": r["KIND"], "WHERE": r["WHERE"]} for r in risk]),
    }
    numbers = {"m2_seconds": m2["seconds"], "m2_rebar_states": m2["rebar_states"],
               "m3_rebar_states": dict(Counter(r["REBAR_STATE"] for r in reg)),
               "missing_steel_components": rc["missing_steel_components"], "rebar_totals": rc["totals"],
               "classes": dict(Counter(r["CLASS"] for r in recon)),
               "evidence_records": dict(Counter(r["state"] for r in ev["records"])),
               "evidence_details": [d["detail_id"] for d in ev["details"]],
               "coverage_states": {c["FAMILY"]: c["STATE"] for c in cov}}
    if a.get("--heldout"):
        h = {}
        for p in sorted(Path(a["--heldout"]).glob("*.json")):
            h[p.stem] = json.loads(p.read_text())["summary"]
        files["13_HELDOUT_EVALUATION.json"] = json.dumps(h, indent=1)
    if a.get("--runlog-cold") and a.get("--runlog-warm"):
        files["14_PERFORMANCE.json"] = json.dumps(performance(m2, json.loads(Path(a["--runlog-cold"]).read_text()),
                                                              json.loads(Path(a["--runlog-warm"]).read_text())),
                                                  indent=1)
    held = {p.stem: json.loads(p.read_text())["summary"] for p in sorted(Path(a["--heldout"]).glob("*.json"))} \
        if a.get("--heldout") else {}
    files["12_COVERAGE_DASHBOARD.html"] = dashboard(family_rows(m2, items, "CONCRETE"),
                                                    family_rows(m2, items, "REINFORCEMENT"), rc, cov, held, numbers)
    files["00_NUMBERS.json"] = json.dumps(numbers, indent=1, default=str)
    pf = _module(ROOT / "research/alsenan_m1_usable_boq/post_freeze/post_freeze_comparison.py", "m1pf3")
    for name, text in files.items():
        check_text(name, text, pf.BENCH)
        (PKG / name).write_text(text, encoding="utf-8")
    print(json.dumps({"written": sorted(files), "numbers": numbers}, indent=1, default=str))


if __name__ == "__main__":
    main(sys.argv[1:])
