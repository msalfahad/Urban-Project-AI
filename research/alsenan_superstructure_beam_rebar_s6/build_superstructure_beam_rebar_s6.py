"""ALSENAN S6 - accurate superstructure beam rebar (simple + continuous beams) through the generic engine
engine.source.superstructure_beam_rebar.

    python3 -I research/alsenan_superstructure_beam_rebar_s6/build_superstructure_beam_rebar_s6.py

Blind build: reads ONLY the frozen PRE-S6 package (research/pre_s6_superstructure_beam_readiness), verified against
its INDEX hashes first - never the drawing, never a reference, an old Urban total or a rough profile:
  * 10_SUPERSTRUCTURE_BEAM_REBAR_READINESS.csv  occurrences, component readiness, stirrup details, blocked reasons
  * 06_BEAM_BAR_RUN_READINESS.csv               bar runs (segments, extents, missing ends, span mapping)
  * 05_CB_SPAN_SEQUENCE.csv                     CB spans (c/c, face to face), reading direction, span handles
  * 07 / 08 / 09 / 01                           side bars, openings, the token corpus, object conservation
  * S6_PROVENANCE_TEMPLATES.json, PRE_S6_SUMMARY.json (typical-detail rules, span symbols)
The builder never measures: every length, binding, mapping and blocked reason comes from PRE-S6. It translates the
registers into the engine's input contract, runs the engine, proves S6 does not widen the frozen PRE-S6 scope, and
writes the S6 registers and S6_FREEZE_MANIFEST.json (code, inputs and outputs hashed). The post-freeze comparison
is a separate script that refuses to run unless this manifest still matches. Deterministic: two runs, same bytes.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import superstructure_beam_rebar as SB  # noqa: E402

BASELINE = "d39f5f6"
DRAWING_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
P6 = "research/pre_s6_superstructure_beam_readiness"
CODE = ["engine/source/superstructure_beam_rebar.py", "engine/source/rebar_provenance.py",
        "engine/source/accurate_boq_rebar.py", "engine/source/rebar_model.py", "engine/source/rebar_unit_mass.py",
        "research/alsenan_superstructure_beam_rebar_s6/build_superstructure_beam_rebar_s6.py"]
INPUTS = [f"{P6}/{f}" for f in ("01_BEAM_OCCURRENCE_CONSERVATION.csv", "05_CB_SPAN_SEQUENCE.csv",
                                "06_BEAM_BAR_RUN_READINESS.csv", "07_BEAM_SIDE_REBAR_READINESS.csv",
                                "08_BEAM_OPENING_OCCURRENCES.csv", "09_BEAM_TOKEN_CORPUS.csv",
                                "10_SUPERSTRUCTURE_BEAM_REBAR_READINESS.csv", "S6_PROVENANCE_TEMPLATES.json",
                                "PRE_S6_SUMMARY.json", "INDEX.json")]
OUTPUTS = ["SUPERSTRUCTURE_BEAM_OCCURRENCES.csv", "SUPERSTRUCTURE_BEAM_COMPONENTS.csv",
           "SUPERSTRUCTURE_BEAM_BAR_RUNS.csv", "SUPERSTRUCTURE_BEAM_BBS_NET.csv",
           "SUPERSTRUCTURE_BEAM_STIRRUP_COUNTS.csv", "SUPERSTRUCTURE_BEAM_RELEASE_SUMMARY.json",
           "SUPERSTRUCTURE_BEAM_UNRESOLVED.csv", "SUPERSTRUCTURE_BEAM_PROVENANCE.jsonl",
           "SUPERSTRUCTURE_BEAM_ENGINEERING_FLAGS.csv", "SIMPLE_BEAM_REBAR_SUMMARY.csv",
           "CONTINUOUS_BEAM_REBAR_SUMMARY.csv", "SUPERSTRUCTURE_BEAM_OBJECT_CONSERVATION.csv",
           "SUPERSTRUCTURE_BEAM_TOKEN_TERMINALS.csv", "SUPERSTRUCTURE_BEAM_ENGINEERING_QUESTIONS.csv",
           "SUPERSTRUCTURE_BEAM_OCCURRENCE_REGISTER.json", "S6_1_RELEASE_CANDIDATES.csv", "README.md"]
EXPECTED = {"SIMPLE_BEAM": 89, "CONTINUOUS_BEAM": 13}
EXPECTED_RELEASE = {"SIMPLE_BEAM": {"LOWER_BOUND": 71, "BLOCKED": 18},
                    "CONTINUOUS_BEAM": {"LOWER_BOUND": 7, "BLOCKED": 6}}        # frozen PRE-S6 scope (S6 brief 2)
EXPECTED_STIRRUP_RELEASE = {"SIMPLE_BEAM": 71, "CONTINUOUS_BEAM": 12}            # S6 brief 17
EXPECTED_UNTAGGED, EXPECTED_TAGS, EXPECTED_SIDE = 38, 119, 39
ROLE = {"BOTTOM_MAIN": "BOTTOM_MAIN", "TOP_MAIN": "TOP_MAIN", "BOTTOM": "BOTTOM_MAIN", "TOP": "TOP_MAIN",
        "MID_SUPPORT_TOP": "MID_TOP"}
RELEASABLE = ("READY", "READY_LOWER_BOUND")

# PRE-S6 questions carried forward (S6 brief 32); answers become versioned claims -> an S6.1 delta, never an edit
QUESTIONS = {
    "Q1": "Anchorage / development of beam longitudinal bars at end supports, and bar-end hooks (note 9 70Ø / 40Ø is "
          "starter-bar context only).",
    "Q2": "CB top bars and hangers: the frames draw one top bar per span; the typical draws an end-support bar and an "
          "unlabelled second top row. Which governs, what extents, is the second row a hanger with its own bars?",
    "Q3": "Typical-detail labels: '0.3 Ln2' in the 2-span typicals (no Ln2 exists), the undimensioned left end top "
          "bar, 'L3' in the 3-span typical.",
    "Q4": "3-span middle bottom bar '0.15L': is the extension 0.15 x the clear span it enters? (left out: lower bound)",
    "Q5": "Ln for the MID extent: the typical dimensions Ln axis to axis and L face to face; S6 uses the drawing's own "
          "definition (0.22 x axis-to-axis span from the face). Please confirm.",
    "Q6": "Side bars '2Ø12/30cm' (SBT REMARKS) / '2Ø12' + '30cm' (CB MIDDLE REINT.): per face or total, '/30cm' "
          "meaning, bar length, end treatment.",
    "Q7": "Stirrups: legs (STR2 / str3 icons have no legend), hook type and length, first stirrup position, end zones.",
    "Q8": "Simple-beam SBT bars run at least support face to support face, uncurtailed - please confirm.",
    "Q9": "Special simple beams: curved ring beams (bar stops), WITH STAIR spans (p.16 detail), the planted-column "
          "span (p.15 detail), the cantilever CA (free end, back-span anchorage).",
    "R1": "Bindings left as candidates (445, 45D, 474, 476, 78F).",
    "R2": "Width conflicts: FFRS B6, FFRS CB10, GFRS B21, GFRS B29, GFRS CB2 (drawn band vs schedule B).",
    "R3": "CB span conflicts: CB4, CB5 (span lengths), CB8 (2 tagged spans vs 3 schedule spans).",
    "R4": "CB reading direction: CB2, CB7, CB13 match the schedule both ways. Which end is span 1?",
    "R5": "CB3: its middle span is also tagged 'B3 WITH STAIR'; MID1 differs from the typical (3Ø16 callout on a "
          "longer bar); MID2 is blank.",
    "R6": "38 untagged spans / arcs (incl. six 1F dome-ring arcs): which marks apply?",
}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def _rows(p):
    return list(csv.DictReader(open(ROOT / p, encoding="utf-8")))


def _f(v):
    return None if v in (None, "") else float(v)


def _i(v):
    return None if v in (None, "") else int(float(v))


def _js(v, default=None):
    if v in (None, ""):
        return default
    try:
        return json.loads(v)
    except (TypeError, ValueError):
        return v


def _csv(path, rows, fields=None):
    buf = io.StringIO()
    fields = fields or (list(rows[0].keys()) if rows else ["empty"])
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (json.dumps(v, sort_keys=True, ensure_ascii=False) if isinstance(v, (list, dict, tuple)) else
                        ("" if v is None else (round(v, 6) if isinstance(v, float) else v))) for k, v in r.items()})
    path.write_text(buf.getvalue(), encoding="utf-8")


def _json(path, obj):
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False, default=float) + "\n",
                    encoding="utf-8")


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()


# ------------------------------------------------------------------------------------------------ frozen inputs
def verify_pre_s6():
    idx = _j(f"{P6}/INDEX.json")
    bad = [o for o, h in idx["outputs"].items() if _sha(ROOT / P6 / o) != h]
    if bad:
        raise SystemExit(f"PRE-S6 package changed since its freeze: {bad}")
    if idx.get("drawing_sha256") != DRAWING_SHA or not idx.get("no_kg"):
        raise SystemExit("PRE-S6 INDEX does not name the S6 drawing / is not the no-kg readiness round")
    return idx


def load():
    return {"c01": _rows(f"{P6}/01_BEAM_OCCURRENCE_CONSERVATION.csv"), "c05": _rows(f"{P6}/05_CB_SPAN_SEQUENCE.csv"),
            "c06": _rows(f"{P6}/06_BEAM_BAR_RUN_READINESS.csv"), "c07": _rows(f"{P6}/07_BEAM_SIDE_REBAR_READINESS.csv"),
            "c08": _rows(f"{P6}/08_BEAM_OPENING_OCCURRENCES.csv"), "c09": _rows(f"{P6}/09_BEAM_TOKEN_CORPUS.csv"),
            "c10": _rows(f"{P6}/10_SUPERSTRUCTURE_BEAM_REBAR_READINESS.csv"),
            "tpl": _j(f"{P6}/S6_PROVENANCE_TEMPLATES.json"), "summary": _j(f"{P6}/PRE_S6_SUMMARY.json")}


# ------------------------------------------------------------------------------------------------------- rules
def _applies(r):
    """The bar role a typical-detail dimension is bound to (from its bar row and the supports the bar straddles).
    A 7.5 cm BOTTOM dimension binds the bottom bar; a 0.22 Ln TOP dimension on a bar straddling an interior support
    binds the MID bar; a TOP factor on a bar that straddles nothing is the end-support bar. A TOP length dimension
    is bound to a top bar whose role is not established (Q2) - it applies to no S6 role."""
    row, kind, straddles = r.get("bar_row"), r.get("kind"), r.get("bar_straddles") or []
    if row == "BOTTOM" and kind == "LENGTH":
        return ["BOTTOM_MAIN"]
    if row == "TOP" and kind == "FACTOR":
        return ["MID_TOP"] if straddles else ["TOP_SUPPORT"]
    return []


def rules(summary, c06, n_openings):
    typ = {}
    sym_basis = {}
    for hd in summary["typical_rules"]:
        for s, v in hd["span_symbols"].items():
            sym_basis.setdefault(s, set()).add(v["basis"])
        for r in hd["rules"]:
            rid = f"{hd['header']}:{r['dim']}"
            kind = {"LENGTH": "FIXED_EXTENSION_M", "FACTOR": "FACTOR_OF_SPAN"}.get(r.get("kind"))
            bound = bool(r.get("bound")) and r.get("state") in ("SOURCE_EXPLICIT", "SOURCE_DERIVED_HIGH_CONFIDENCE")
            typ[rid] = {"rule_id": rid, "state": "BOUND" if bound and kind else "UNRESOLVED", "kind": kind,
                        "value": r.get("value_m") if kind == "FIXED_EXTENSION_M" else r.get("factor"),
                        "span_basis": r.get("basis") or (hd["span_symbols"].get(r.get("symbol")) or {}).get("basis"),
                        "applies_to": _applies(r) if bound else [], "text": r.get("text"),
                        "why": r.get("why") or "", "header": hd["header"], "dim": r["dim"], "bar": r.get("bar"),
                        "bar_row": r.get("bar_row"), "support": r.get("support"), "span": r.get("span"),
                        "side": r.get("side"), "symbol": r.get("symbol")}
    for sym, bases in sym_basis.items():
        want = "AXIS_TO_AXIS" if sym.startswith("Ln") else "FACE_TO_FACE"
        if bases != {want}:
            raise SystemExit(f"span symbol {sym} is dimensioned {bases}, expected {want} on every typical")
    # composite ids used by a bar run ('A+B': the two in-span sides of one MID bar)
    for r in c06:
        for s in _js(r["STRAIGHT_SEGMENTS"], []):
            rid = s.get("rule_id")
            if rid and "+" in rid and rid not in typ:
                hd, dims = rid.split(":", 1)
                parts = [typ.get(f"{hd}:{d}") for d in dims.split("+")]
                same = all(parts) and len({(p["state"], p["kind"], p["value"], p["span_basis"],
                                            tuple(p["applies_to"])) for p in parts}) == 1
                p0 = parts[0] if all(parts) else {}
                typ[rid] = {"rule_id": rid, "state": "BOUND" if same and p0.get("state") == "BOUND" else "UNRESOLVED",
                            "kind": p0.get("kind"), "value": p0.get("value"), "span_basis": p0.get("span_basis"),
                            "applies_to": p0.get("applies_to") if same else [], "text": " + ".join(
                                p["text"] for p in parts if p), "why": "" if same else "parts disagree",
                            "header": hd, "dim": dims, "parts": dims.split("+")}
    return {
        "typical": dict(sorted(typ.items())),
        "span_symbols": {"Ln": "AXIS_TO_AXIS", "L": "FACE_TO_FACE", "authority": "SOURCE_DERIVED_HIGH_CONFIDENCE",
                         "why": "every CB typical dimensions Ln / Ln1 / Ln2 axis to axis and L / L1 / L3 face to face "
                                "(dimension defpoints, PRE-S6); the drawing's own definition is used (S6 brief 10, Q5)"},
        "development": {"state": SB.NOT_ESTABLISHED,
                        "why": "no beam-source development rule (note 9 70Ø / 40Ø is starter-bar context only; no 40D, "
                               "70D, code, Urban default or external value is used) - Q1"},
        "bar_end_hooks": {"state": SB.NOT_ESTABLISHED,
                          "why": "end legs drawn N.T.S. without a dimension; no project hook source; column hook rules "
                                 "are not imported - Q1"},
        "stirrup_hooks": {"state": SB.NOT_ESTABLISHED, "why": "hook type / extension not printed - Q7"},
        "stirrup_topology": {"state": SB.NOT_ESTABLISHED,
                             "why": "legs not printed; STR2 / str3 REMARKS icons have no legend - Q7"},
        "side_bar_semantics": {"state": SB.NOT_ESTABLISHED,
                               "why": "'/30cm' semantics not established (per face or total; vertical spacing or "
                                      "other; bar length; end treatment) - never silently read as a vertical spacing "
                                      "(Q6)"},
        "hanger": {"state": SB.NOT_ESTABLISHED,
                   "why": "the CB typical draws an additional unlabelled top row: count / diameter not "
                          "source-established and not inferred from practice (Q2)"},
        "openings_checked": n_openings}


# ------------------------------------------------------------------------------------------------------ tokens
def _parse_nd(norm):
    """'6Ø18' -> (6, 18); anything else -> None."""
    if not norm or "Ø" not in norm:
        return None
    a, b = norm.split("Ø", 1)
    try:
        return int(a), int(b)
    except ValueError:
        return None


def _tok(t):
    return {"token_id": t["TOKEN_ID"], "handle": t["HANDLE"], "type": t["TYPE"], "field_family": t["FIELD_FAMILY"],
            "grammar": t["GRAMMAR"], "terminal": t["TERMINAL"], "raw": t["RAW"], "normalised": t["NORMALISED"]}


class Tokens:
    def __init__(self, c09):
        self.all = c09
        self.by_id = {t["TOKEN_ID"]: t for t in c09}
        self.by_type_fam = defaultdict(list)
        self.by_handle_fam = defaultdict(list)
        for t in c09:
            self.by_type_fam[(t["TYPE"], t["FIELD_FAMILY"])].append(t)
            self.by_handle_fam[(t["HANDLE"], t["FIELD_FAMILY"])].append(t)

    def sbt(self, mark, fam):
        return [_tok(t) for t in self.by_type_fam[(mark, fam)] if t["SOURCE"] == "SBT"]

    def cb_bottom(self, mark, label):
        t = self.by_id.get(f"C-BEAM:{mark}:{label}")
        return [_tok(t)] if t else []

    def cb_stirrup(self, mark, k):
        t = self.by_id.get(f"C-BEAM:{mark}:STR{k}")
        return [_tok(t)] if t else []

    def frame(self, handle, fam):
        return [_tok(t) for t in self.by_handle_fam[(handle, fam)]]

    def empty_cells(self, mark, fam):
        return [t["TOKEN_ID"] for t in self.by_type_fam[(mark, fam)] if t["GRAMMAR"] == "EMPTY"]


# ------------------------------------------------------------------------------------------------- occurrences
def _member(obj):
    p = obj.split(":")
    return p[2] if len(p) > 2 else obj


def _questions(sub):
    q = {"development": "Q1", "stirrup_geometry": "Q7", "side": "Q6", "opening": None}
    if sub == SB.CONTINUOUS_BEAM:
        q.update(hanger="Q2", reading_direction="R4", sequence="R3", top="Q2", mid_ln="Q5", bottom_ext="Q4")
    else:
        q.update(longitudinal="Q8", special="Q9")
    return q


def _simple_blocks(bm):
    st, app = bm["STATUS"], bm["APPLICABILITY_STATE"]
    if st == "SOURCE_CONFLICT":
        return [{"reason": bm["WHY_BLOCKED"], "authority": "SOURCE_CONFLICT", "question_id": "R2",
                 "kind": "WIDTH_SOURCE_CONFLICT"}]
    if st == "PROVISIONAL_ONLY":
        return [{"reason": f"{bm['WHY_BLOCKED']} (tag binding BOUND_CANDIDATE: a candidate never releases steel)",
                 "authority": "UNRESOLVED", "question_id": "R1", "kind": "BINDING_CANDIDATE"}]
    if app == "BLOCKED":
        return [{"reason": bm["WHY_BLOCKED"], "authority": "UNRESOLVED", "question_id": "Q9",
                 "kind": "UNDEFINED_CANDIDATE_DETAIL"}]
    return []


def _cb_blocks(rows10, spans05):
    out = []
    wm = [s["WIDTH_MATCH_STATE"] for s in spans05]
    bt = [s["BINDING_TERMINAL"] for s in spans05]
    seq = spans05[0]["SEQUENCE_STATE"]
    why = next((r["WHY_BLOCKED"] for r in rows10 if r["COMPONENT_FAMILY"] in ("BOTTOM", "LONGITUDINAL")
                and r["STATUS"] in ("SOURCE_CONFLICT", "BLOCKED_COMPONENT") and r["OCCURRENCE_STATUS"] == "BLOCKED"),
               None)
    if "SOURCE_CONFLICT" in wm:
        out.append({"reason": why, "authority": "SOURCE_CONFLICT", "question_id": "R2",
                    "kind": "WIDTH_SOURCE_CONFLICT"})
    elif "BOUND_SOURCE_CONFLICT" in bt:
        out.append({"reason": why, "authority": "SOURCE_CONFLICT", "question_id": "R5", "kind": "TWO_MARKS_ONE_SPAN"})
    if seq != "MATCH":
        out.append({"reason": why if not out else f"span sequence {seq}", "authority": "SOURCE_CONFLICT",
                    "question_id": "R3", "kind": f"CB_{seq}"})
    if "BOUND_CANDIDATE" in bt:
        out.append({"reason": "a span binding is a candidate", "authority": "UNRESOLVED", "question_id": "R1",
                    "kind": "BINDING_CANDIDATE"})
    return out


def _stirrup_attrs(d):
    d = d or {}
    rate = d.get("SPACING_OR_RATE") or {}
    return {"dia_mm": (d.get("DIAMETER") or {}).get("value"),
            "mode": "BARS_PER_METRE" if rate.get("unit") == "per m" else ("SPACING_MM" if rate.get("unit") == "mm"
                                                                          else None),
            "value": rate.get("value"), "legs": d.get("NUMBER_OF_LEGS"), "hooks": d.get("HOOKS"),
            "end_zone": d.get("END_ZONES"), "first_last": d.get("FIRST_LAST_STIRRUP_RULE"),
            "core_path_missing": list((d.get("MASS") or {}).get("missing") or [])}


def _run_record(r6, comp, tpl, idn, toks, mark, sub):
    segs = _js(r6["STRAIGHT_SEGMENTS"], [])
    t = tpl.get(r6["BAR_RUN_ID"]) or {}
    frame = (_js(r6["SOURCE_EXTENT"], {}) or {}).get("frame_handle")
    if sub == SB.SIMPLE_BEAM:
        tokens = toks.sbt(mark, comp)
    elif comp == "BOTTOM_MAIN":
        tokens = toks.cb_bottom(mark, r6["LABEL"])
    elif comp == "MID_TOP":
        tokens = toks.frame(frame, "MID")
    else:
        tokens = toks.frame(frame, "TOP")
    n, d = _i(r6["COUNT"]), _i(r6["DIA_MM"])
    for tk in tokens:
        if tk["terminal"] == "PARSED_BOUND" and _parse_nd(tk["normalised"]) != (n, d):
            raise SystemExit(f"{r6['BAR_RUN_ID']}: {n}Ø{d} != token {tk['token_id']} {tk['normalised']}")
    missing = _js(r6["MISSING"], [])
    status = r6["STATUS"]
    source_block = None
    if status not in RELEASABLE and r6["STRAIGHT_RUN_STATE"] == "BLOCKED_UNQUANTIFIED":
        source_block = "; ".join(missing) or "bar run not established (PRE-S6)"
    return {"BAR_RUN_ID": r6["BAR_RUN_ID"], "component": comp, "frame_role": r6["FRAME_ROLE"] or None,
            "label": r6["LABEL"] or None, "count": n, "dia_mm": d, "segments": segs,
            "register_run_m": _f(r6["STRAIGHT_RUN_M"]), "start_location": _js(r6["START_LOCATION"]),
            "end_location": _js(r6["END_LOCATION"]), "spans_crossed": _js(r6["SPANS_CROSSED"], []),
            "intermediate_supports": _js(r6["INTERMEDIATE_SUPPORTS"], []),
            "source_extent": _js(r6["SOURCE_EXTENT"], {}),
            "source_handles": t.get("SOURCE_HANDLES") or [h for h in (idn["TAG_HANDLES"] + [frame]) if h],
            "schedule_handles": t.get("SCHEDULE_HANDLES") or idn["SCHEDULE_HANDLES"],
            "geometry_handles": t.get("GEOMETRY_HANDLES") or idn["GEOMETRY_HANDLES"],
            "support_ids": t.get("SUPPORT_IDS") or idn.get("SUPPORT_IDS") or [],
            "detail_id": idn["DETAIL_ID"], "authority": t.get("AUTHORITY_STATE") or (
                "SOURCE_DERIVED_HIGH_CONFIDENCE" if status in RELEASABLE else "UNRESOLVED"),
            "convention_id": t.get("CONVENTION_ID") or ("BAR_STRAIGHT_RUN_FACE_TO_FACE_LOWER_BOUND"
                                                        if sub == SB.SIMPLE_BEAM else
                                                        "CB_BAR_RUN_FACE_TO_FACE_PLUS_BOUND_TYPICAL"),
            "run_rule_id": t.get("RULE_ID"), "missing": missing, "source_block": source_block,
            "source_block_authority": "SOURCE_CONFLICT" if status == "SOURCE_CONFLICT" else "UNRESOLVED",
            "question_id": ("Q9" if sub == SB.SIMPLE_BEAM else "Q2" if comp == "TOP_MAIN" else
                            "R5" if comp == "MID_TOP" else "Q4"),
            "source_tokens": tokens,
            "source_text": " || ".join(f"{tk['token_id']} '{tk['normalised']}'" for tk in tokens) or None,
            "_pre": {"STATUS": status, "SPAN_MAPPING": r6["SPAN_MAPPING"], "COMPLETE_BAR_STATE":
                     r6["COMPLETE_BAR_STATE"], "STRAIGHT_RUN_STATE": r6["STRAIGHT_RUN_STATE"]}}


def _run_key(run, n_spans):
    comp = run["component"]
    if comp == "BOTTOM_MAIN":
        cs = [s["span"] for s in run["segments"] if s.get("kind") == "CLEAR_SPAN"]
        return ("SPAN", cs[0]) if cs else None
    if comp == "MID_TOP":
        sup = run["intermediate_supports"]
        return ("SUPPORT", sup[0]) if len(sup) == 1 else None
    sc = run["spans_crossed"]
    return ("SPAN", sc[0]) if len(sc) == 1 else None


def _mirror(key, n):
    return None if key is None else (key[0], n + 1 - key[1]) if key[0] == "SPAN" else (key[0], n - key[1])


def _run_rule(run):
    return [f"{s.get('kind')}:{s.get('rule_id') or ''}" for s in run["segments"]]


def reading_interpretations(runs, n_spans):
    """Both readings of an AMBIGUOUS CB: the bar at a physical place is the schedule bar of that span under FORWARD
    and of the mirrored span under REVERSED. Nothing is chosen; the engine releases only identical interpretations."""
    by_key = {(r["component"], _run_key(r, n_spans)): r for r in runs}
    for r in runs:
        k = _run_key(r, n_spans)
        p = by_key.get((r["component"], _mirror(k, n_spans))) if k else None
        r["interpretations"] = [
            {"name": "FORWARD", "component": r["component"], "count": r["count"], "dia_mm": r["dia_mm"],
             "run_rule": _run_rule(r), "bar_run": r["BAR_RUN_ID"]},
            {"name": "REVERSED", "component": r["component"], "count": p["count"] if p else None,
             "dia_mm": p["dia_mm"] if p else None, "run_rule": _run_rule(p) if p else ["NO_MIRROR_BAR"],
             "bar_run": p["BAR_RUN_ID"] if p else None}]


def occurrences(D, toks):
    tpl = defaultdict(dict)
    for t in D["tpl"]["templates"]:
        tpl[t["ELEMENT_OCCURRENCE_ID"]][t["BAR_RUN_ID"]] = t
    by_occ = defaultdict(list)
    for r in D["c10"]:
        by_occ[r["OCCURRENCE_ID"]].append(r)
    runs6 = defaultdict(list)
    for r in D["c06"]:
        runs6[r["OCCURRENCE_ID"]].append(r)
    spans5 = defaultdict(list)
    for r in D["c05"]:
        spans5[r["CB_OCCURRENCE_ID"]].append(r)
    obj01 = {r["OBJECT_ID"]: r for r in D["c01"]}
    tags_of_geom = defaultdict(list)
    for r in D["c01"]:
        if r["OBJECT_KIND"] == "TAG" and r["BOUND_GEOMETRY"]:
            tags_of_geom[r["BOUND_GEOMETRY"]].append(r["OBJECT_ID"].split(":", 2)[2])
    side = {(r["ELEMENT"], r["TYPE"]): r for r in D["c07"]}
    openings_by_member = defaultdict(list)
    for o in D["c08"]:
        members = {x.get("member") for x in _js(o["ON_BEAM_FACES_OR_LINEWORK"], [])} | \
            {x if isinstance(x, str) else x.get("member") for x in _js(o["INSIDE_BEAM_BANDS"], [])}
        for m in members:
            if m:
                openings_by_member[(o["SHEET"], m)].append(o)
    out, untagged = [], []
    for oid in sorted(by_occ):
        rows = by_occ[oid]
        r0 = rows[0]
        sub = r0["SUBFAMILY"]
        if sub == "UNTAGGED_GEOMETRY":
            o1 = obj01[r0["GEOMETRY_OBJECT"]]
            untagged.append({"object_id": oid, "sheet": r0["SHEET"], "floor": r0["FLOOR"],
                             "object_kind": o1["OBJECT_KIND"], "length_m": _f(o1["LENGTH_M"]),
                             "clear_m": _f(o1["CLEAR_M"]), "drawn_width_mm": _f(o1["DRAWN_WIDTH_MM"]),
                             "start_support": o1["START_SUPPORT"] or None, "end_support": o1["END_SUPPORT"] or None,
                             "s1_source_id": o1["S1_SOURCE_ID"] or None,
                             "why": f"{r0['WHY_BLOCKED']}; {o1['WHY']} (R6)"})
            continue
        fam = {r["COMPONENT_FAMILY"]: r for r in rows if not r["SPAN_INDEX"]}
        mark = r0["MARK"]
        geoms = _js(r0["GEOMETRY_OBJECT"], r0["GEOMETRY_OBJECT"])
        geoms = geoms if isinstance(geoms, list) else [geoms]
        t_occ = tpl.get(oid, {})
        t_any = next(iter(t_occ.values()), {})
        detail = r0["DETAIL_ID"]
        sched = t_any.get("SCHEDULE_HANDLES") or [detail.split(":")[-1]]
        tags = [h for g in geoms for h in tags_of_geom.get(g, [])]
        cb = None
        geometry = {}
        if sub == SB.SIMPLE_BEAM:
            o1 = obj01[geoms[0]]
            sup = t_any.get("SUPPORT_IDS") or []
            start = {"kind": o1["START_SUPPORT"] or "NOT_STATED", "refs": sup[:1]}
            end = {"kind": o1["END_SUPPORT"] or "NOT_STATED", "refs": sup[1:2]}
            geometry = {"object_kind": o1["OBJECT_KIND"], "length_cc_m": _f(o1["LENGTH_M"]),
                        "clear_face_to_face_m": _f(o1["CLEAR_M"]), "drawn_width_mm": _f(o1["DRAWN_WIDTH_MM"]),
                        "stair_qualifier": o1["STAIR_QUALIFIER"] or None}
            gh = t_any.get("GEOMETRY_HANDLES") or [_member(g) for g in geoms]
            bind = r0["BINDING_TERMINAL"]
            auth = {"BOUND_VERIFIED": "SOURCE_DERIVED_HIGH_CONFIDENCE", "BOUND_SOURCE_CONFLICT": "SOURCE_CONFLICT"
                    }.get(bind, "UNRESOLVED")
        else:
            sp = sorted(spans5[oid], key=lambda s: int(s["SPAN_INDEX"]))
            plan = sorted([s for s in sp if s["PLAN_POSITION"]], key=lambda s: int(s["PLAN_POSITION"]))
            sh = {s["SPAN_INDEX"]: _js(s["SOURCE_HANDLES"], {}) for s in sp}
            start = {"kind": plan[0]["START_SUPPORT"] if plan else "NOT_STATED", "order": "PLAN",
                     "refs": (sh[plan[0]["SPAN_INDEX"]].get("support_refs") or [])[:1] if plan else []}
            end = {"kind": plan[-1]["END_SUPPORT"] if plan else "NOT_STATED", "order": "PLAN",
                   "refs": (sh[plan[-1]["SPAN_INDEX"]].get("support_refs") or [])[-1:] if plan else []}
            cb = {"CB_GROUP_ID": oid, "READING_DIRECTION_STATE": sp[0]["ORIENTATION"],
                  "SEQUENCE_STATE": sp[0]["SEQUENCE_STATE"],
                  "SPAN_SEQUENCE": [{"SPAN_INDEX": int(s["SPAN_INDEX"]), "PLAN_POSITION": _i(s["PLAN_POSITION"]),
                                     "PLAN_OBJECT_ID": s["PLAN_OBJECT_ID"] or None} for s in sp],
                  "spans": {s["SPAN_INDEX"]: {"cc_m": _f(s["PHYSICAL_LENGTH_CC_M"]),
                                              "clear_m": _f(s["SUPPORT_FACE_TO_FACE_M"]),
                                              "schedule_span_m": _f(s["SCHEDULE_SPAN_M"]),
                                              "plan_object": s["PLAN_OBJECT_ID"] or None,
                                              "plan_position": _i(s["PLAN_POSITION"]),
                                              "binding": s["BINDING_TERMINAL"] or None,
                                              "width_match": s["WIDTH_MATCH_STATE"],
                                              "drawn_width_mm": _f(s["DRAWN_WIDTH_MM"]),
                                              "schedule_width_mm": _f(s["SCHEDULE_WIDTH_MM"]),
                                              "tags": sh[s["SPAN_INDEX"]].get("tags") or [],
                                              "bands": sh[s["SPAN_INDEX"]].get("bands") or [],
                                              "support_refs": sh[s["SPAN_INDEX"]].get("support_refs") or []}
                            for s in sp}}
            gh = list(dict.fromkeys(t_any.get("GEOMETRY_HANDLES") or [b for s in sp for b in sh[s["SPAN_INDEX"]].get(
                "bands") or []] or [_member(g) for g in geoms]))
            geometry = {"spans": cb["spans"], "plan_total_cc_m": _f(sp[0]["PLAN_TOTAL_CC_M"]),
                        "schedule_total_m": _f(sp[0]["SCHEDULE_TOTAL_M"])}
            bind = _js(r0["BINDING_TERMINAL"], [])
            auth = "SOURCE_CONFLICT" if "BOUND_SOURCE_CONFLICT" in bind else (
                "UNRESOLVED" if "BOUND_CANDIDATE" in bind or not bind else "SOURCE_DERIVED_HIGH_CONFIDENCE")
        idn = {"SOURCE_HANDLES": list(dict.fromkeys(tags + sched)), "GEOMETRY_HANDLES": gh, "TAG_HANDLES": tags,
               "SCHEDULE_HANDLES": sched, "START_SUPPORT": start, "END_SUPPORT": end,
               "DRAWN_WIDTH_MM": _js(r0["DRAWN_WIDTH_MM"]), "SCHEDULE_WIDTH_MM": _js(r0["SCHEDULE_WIDTH_MM"]),
               "WIDTH_MATCH_STATE": _js(r0["WIDTH_MATCH_STATE"]), "DETAIL_ID": detail,
               "DETAIL_CANDIDATES": _js(r0["DETAIL_CANDIDATES"], []), "SCHEDULE_ROW": sched[0],
               "BINDING_STATE": bind, "AUTHORITY_STATE": auth, "GEOMETRY_OBJECTS": geoms,
               "SUPPORT_IDS": t_any.get("SUPPORT_IDS") or []}
        # ---------------------------------------------------------------- blocks / runs / stirrups / statuses
        if sub == SB.SIMPLE_BEAM:
            blocks = _simple_blocks(fam["BOTTOM_MAIN"])
        else:
            blocks = _cb_blocks(rows, sorted(spans5[oid], key=lambda s: int(s["SPAN_INDEX"])))
        runs = []
        for r6 in sorted(runs6[oid], key=lambda z: z["BAR_RUN_ID"]):
            comp = ROLE[r6["ROLE"]]
            rr = _run_record(r6, comp, t_occ, idn, toks, mark, sub)
            if sub == SB.SIMPLE_BEAM and not rr["segments"] and rr["source_block"]:
                rr["source_block"] = fam["BOTTOM_MAIN"]["WHY_BLOCKED"] or rr["source_block"]
            if sub == SB.SIMPLE_BEAM and rr["segments"]:
                clear = geometry["clear_face_to_face_m"]
                if clear is not None and abs(rr["register_run_m"] - clear) > 1e-6:
                    raise SystemExit(f"{rr['BAR_RUN_ID']}: face-to-face run {rr['register_run_m']} != clear {clear}")
            runs.append(rr)
        if cb and cb["READING_DIRECTION_STATE"] == "AMBIGUOUS":
            reading_interpretations(runs, len(cb["spans"]))
            for rr in runs:
                st, _, _ = SB.candidate_invariant(rr["interpretations"])
                pre = rr["_pre"]["SPAN_MAPPING"]
                if (st == "SAME") != (pre == "CANDIDATE_INVARIANT"):
                    raise SystemExit(f"{rr['BAR_RUN_ID']}: S6 candidate invariance {st} != PRE-S6 {pre}")
        stir_rows = sorted([r for r in rows if r["COMPONENT_FAMILY"] == "STIRRUP_COUNT"],
                           key=lambda z: _i(z["SPAN_INDEX"]) or 1)
        stirrups, s61 = [], []
        for r in stir_rows:
            k = _i(r["SPAN_INDEX"]) or 1
            d = _js(r["STIRRUP_DETAIL"], {})
            a = _stirrup_attrs(d)
            cnt = d.get("COUNT") or {}
            tokens = toks.sbt(mark, "STIRRUP") if sub == SB.SIMPLE_BEAM else toks.cb_stirrup(mark, k)
            if cb and a["value"] is None and tokens:                # rate printed per schedule span (STR k)
                nd = _parse_nd(tokens[0]["normalised"])
                a.update(mode="BARS_PER_METRE", value=nd[0], dia_mm=nd[1])
            for tk in tokens:
                if _parse_nd(tk["normalised"]) != (a["value"], a["dia_mm"]):
                    raise SystemExit(f"{oid} span {k}: stirrup {a['value']}/m Ø{a['dia_mm']} != {tk['token_id']}")
            dist = cnt.get("distribution_m")
            if dist is None and cb:
                dist = cb["spans"][str(k)]["clear_m"]
            rec = dict(a, SPAN_INDEX=k, distribution_m=dist,
                       distribution_basis="clear run between support faces (PRE-S6)",
                       register_count=cnt.get("value") if cnt.get("state") == "LOWER_BOUND" else None,
                       source_tokens=tokens, question_id=None, source_block=None,
                       schedule_handles=sched,
                       geometry_handles=(cb["spans"][str(k)]["bands"] if cb else gh) or gh,
                       source_handles=(cb["spans"][str(k)]["tags"] if cb else tags) + [t["handle"] for t in tokens],
                       _pre_status=r["STATUS"])
            if not blocks and r["STATUS"] not in RELEASABLE:
                if cb and cb["READING_DIRECTION_STATE"] == "AMBIGUOUS":
                    n = len(cb["spans"])
                    mt = toks.cb_stirrup(mark, n + 1 - k)
                    alt = _parse_nd(mt[0]["normalised"]) if mt else (None, None)
                    rec["interpretations"] = [
                        {"name": "FORWARD", "component": "STIRRUP_COUNT", "dia_mm": a["dia_mm"],
                         "count": math.ceil(a["value"] * dist - 1e-9), "run_rule": ["BARS_PER_METRE", a["value"]]},
                        {"name": "REVERSED", "component": "STIRRUP_COUNT", "dia_mm": alt[1],
                         "count": math.ceil(alt[0] * dist - 1e-9) if alt[0] else None,
                         "run_rule": ["BARS_PER_METRE", alt[0]]}]
                    st, _, _ = SB.candidate_invariant(rec["interpretations"])
                    if st == "SAME":
                        # invariant here, but PRE-S6 did not assess stirrup invariance: the frozen scope is not
                        # widened inside S6 (S6 brief 2) - recorded as an S6.1 release candidate instead
                        rec["source_block"] = ("FROZEN PRE-S6 SCOPE: both reading directions give the same "
                                               f"{a['value']}Ø{a['dia_mm']}/m on this span (candidate-invariant), "
                                               "but PRE-S6 assessed invariance for bar runs only and blocked this "
                                               "count; S6 does not widen the frozen scope - S6.1 release candidate")
                        rec["question_id"] = "R4"
                        s61.append({"occurrence_id": oid, "mark": mark, "component": "STIRRUP_COUNT",
                                    "span_index": k, "interpretations": rec["interpretations"],
                                    "would_release_count": rec["interpretations"][0]["count"],
                                    "why_not_released": "PRE-S6 frozen scope (S6 brief 2): needs a versioned "
                                                        "claim / S6.1 delta"})
                else:
                    rec["source_block"] = r["WHY_BLOCKED"] or "stirrup count not established (PRE-S6)"
                    rec["question_id"] = "Q9"
            stirrups.append(rec)
        status, hanger = {}, {}
        if sub == SB.SIMPLE_BEAM:
            status["TOP_SUPPORT"] = {"state": "NOT_APPLICABLE", "why": fam["TOP_SUPPORT_EXTRA"]["WHY_APPLICABLE"] +
                                     " (no support bar field in the SBT)", "rule_id": "S6-SBT-NO-SUPPORT-FIELD"}
            status["BOTTOM_SUPPORT"] = {"state": "NOT_APPLICABLE", "why": fam["BOTTOM_EXTRA"]["WHY_APPLICABLE"] +
                                        " (no bottom extra field in the SBT)", "rule_id": "S6-SBT-NO-SUPPORT-FIELD"}
            for c in ("MID_TOP", "MID_BOTTOM"):
                status[c] = {"state": "NOT_APPLICABLE", "why": "a simple beam has one span and no interior support; "
                             "the SBT has no MID field", "rule_id": "S6-SIMPLE-NO-MID"}
            extra = fam.get("STAIR_EXTRA") or fam.get("PLANTED_COLUMN_EXTRA")
            status["OTHER_EXPLICIT_EXTRA"] = (
                {"state": "BLOCKED", "why": extra["WHY_BLOCKED"], "question_id": "Q9",
                 "rule_id": "S6-UNDEFINED-CANDIDATE-DETAIL"} if extra and extra["STATUS"] != "NOT_APPLICABLE" else
                {"state": "NOT_APPLICABLE", "why": "no other explicit extra scheduled or detailed for this occurrence",
                 "rule_id": "S6-NO-OTHER-EXTRA"})
            h = fam["HANGER"]
            hanger = {"state": "ABSENT" if h["STATUS"] == "NOT_APPLICABLE" else "BLOCKED",
                      "why": h["WHY_APPLICABLE"] if h["STATUS"] == "NOT_APPLICABLE" else h["WHY_BLOCKED"]}
        else:
            status["TOP_SUPPORT"] = {
                "state": "BLOCKED", "question_id": "Q2+Q3", "rule_id": "S6-CB-TOP-SUPPORT-UNRESOLVED",
                "why": "typical end-support top bar: the schedule frames draw one top bar per span while the typical "
                       "draws a separate end-support bar dimensioned '0.3 Ln2' (UNRESOLVED: no Ln2 in a 2-span "
                       "typical) - which governs and its extent are not established; not taken from the frames"}
            status["BOTTOM_SUPPORT"] = {"state": "NOT_APPLICABLE", "rule_id": "S6-CB-NO-BOTTOM-SUPPORT",
                                        "why": "no bottom support bar is scheduled or drawn (C-BEAM frames: TOP, "
                                               "BOTTOM, MID only)"}
            status["MID_BOTTOM"] = {"state": "NOT_APPLICABLE", "rule_id": "S6-CB-NO-MID-BOTTOM",
                                    "why": "no bottom MID / support bar in the C-BEAM schedule or typical"}
            status["OTHER_EXPLICIT_EXTRA"] = {"state": "NOT_APPLICABLE", "rule_id": "S6-NO-OTHER-EXTRA",
                                              "why": "no other explicit extra scheduled (load-line numbers are loads, "
                                                     "never steel)"}
            have = {r["component"] for r in runs}
            lw = fam.get("LONGITUDINAL")
            fam_tok = {"TOP_MAIN": "TOP", "BOTTOM_MAIN": "BOTTOM", "MID_TOP": "MID"}
            for c in ("TOP_MAIN", "BOTTOM_MAIN", "MID_TOP"):
                if c not in have:
                    empty = toks.empty_cells(mark, "MID") if c == "MID_TOP" else []
                    status[c] = {"state": "BLOCKED", "question_id": "R3",
                                 "rule_id": "S6-NO-BAR-RUN",
                                 "source_tokens": [_tok(t) for t in toks.by_type_fam[(mark, fam_tok[c])]
                                                   if t["TERMINAL"] == "PARSED_BOUND"],
                                 "why": ((lw or {}).get("WHY_BLOCKED") or "no bar run established") +
                                 (f"; MID schedule cell empty ({', '.join(empty)})" if empty else "")}
            h = fam["HANGER"]
            hanger = {"state": h["WHY_BLOCKED"].split(":", 1)[0] if h["WHY_BLOCKED"] else "UNRESOLVED",
                      "why": h["WHY_BLOCKED"], "question_id": "Q2"}
        sd = side.get((sub, mark))
        side_rec = None
        if sd:
            side_rec = {"applicability": sd["APPLICABILITY"], "raw_text": sd["TOKEN_RAW"] or None,
                        "raw_text_display": (sd["TOKEN_RAW"] or "").replace("%%C", "Ø") or None,
                        "count": _i(sd["COUNT"]), "dia_mm": _i(sd["DIA_MM"]), "spacing_cm": _f(sd["SPACING_CM"]),
                        "token_handles": _js(sd["TOKEN_HANDLES"], []) if sd["TOKEN_HANDLES"].startswith("[") else
                        [h for h in sd["TOKEN_HANDLES"].split(",") if h],
                        "why": sd["WHY"] if sd["APPLICABILITY"] != "PRINTED" else sd["COUNT_SEMANTICS"],
                        "note_id": sd["NOTE_ID"]}
        opens = []
        for g in geoms:
            for o in openings_by_member.get((r0["SHEET"], _member(g)), []):
                opens.append({"opening_id": o["OPENING_ID"], "why": o["WHY"],
                              "state": "NOT_APPLICABLE" if o["OPENING_STATE"] == "NOT_APPLICABLE" else
                              "PHYSICAL_BEAM_OPENING"})
        flags = _flags(sub, blocks, cb, runs, stirrups, side_rec, fam, geometry)
        out.append({"occurrence_id": oid, "subfamily": sub, "mark": mark, "drawing_sha": DRAWING_SHA,
                    "sheet": r0["SHEET"], "floor": r0["FLOOR"], "identity": idn, "geometry": geometry, "cb": cb,
                    "blocks": blocks, "bar_runs": runs, "stirrups": stirrups, "status": status, "side": side_rec,
                    "hanger": hanger, "openings": sorted({o["opening_id"]: o for o in opens}.values(),
                                                         key=lambda z: z["opening_id"]),
                    "questions": _questions(sub), "flags": flags,
                    "_pre": {"OCCURRENCE_STATUS": r0["OCCURRENCE_STATUS"]}, "_s61": s61})
    return out, untagged


def _flags(sub, blocks, cb, runs, stirrups, side_rec, fam, geometry):
    fl = [f"{b['kind']}: {b['question_id']}" for b in blocks]
    if cb:
        rd = cb["READING_DIRECTION_STATE"]
        if rd == "AMBIGUOUS":
            fl.append("READING_DIRECTION_AMBIGUOUS: only candidate-invariant components release (R4)")
        if rd == "REVERSED":
            fl.append("READING_DIRECTION_REVERSED: only the reversed reading matches the schedule (resolved, PRE-S6)")
        if any(r["component"] == "MID_TOP" for r in runs):
            fl.append("MID_EXTENT_LN_AXIS_TO_AXIS: released on the drawing's own Ln definition (Q5 confirmation open)")
        if any(r["component"] == "BOTTOM_MAIN" and any("no bound rule" in m for m in r["missing"]) for r in runs):
            fl.append("BOTTOM_EXTENSION_UNBOUND: an interior-span bottom bar extension (0.15L) adds no length (Q4)")
        if any(s.get("source_block", "") and s["source_block"].startswith("FROZEN PRE-S6 SCOPE") for s in stirrups):
            fl.append("S6_1_CANDIDATE: stirrup count candidate-invariant but outside the frozen PRE-S6 scope")
    else:
        if geometry.get("object_kind") == "ARC_BAND":
            fl.append("CURVED_MEMBER: support faces at the arc ends not established (Q9)")
        if geometry.get("stair_qualifier"):
            fl.append("WITH_STAIR: p.16 stair-beam detail is an unread candidate (Q9)")
        if fam.get("PLANTED_COLUMN_EXTRA") and fam["PLANTED_COLUMN_EXTRA"]["STATUS"] != "NOT_APPLICABLE":
            fl.append("PLANTED_COLUMN: p.15 detail is a candidate (Q9)")
        if any(r["source_block"] and "UNRESOLVED" in (r["source_block"] or "") and r["component"] == "BOTTOM_MAIN"
               and geometry.get("object_kind") != "ARC_BAND" for r in runs):
            fl.append("CANTILEVER_OR_FREE_END: bar run to the free end not established (Q9)")
    if side_rec and side_rec["applicability"] == "PRINTED":
        fl.append(f"SIDE_BAR_SEMANTICS: '{side_rec['raw_text_display']}' kept, quantity blocked (Q6)")
    return fl


# ----------------------------------------------------------------------------------------------- scope / checks
def scope_check(res, occs):
    """S6 never widens the frozen PRE-S6 scope: a released S6 bar run must be READY / READY_LOWER_BOUND in 06, a
    released stirrup count READY_LOWER_BOUND in 10. Also lists where S6 is narrower."""
    pre_run = {r["BAR_RUN_ID"]: r["_pre"]["STATUS"] for o in occs for r in o["bar_runs"]}
    pre_st = {(o["occurrence_id"], s["SPAN_INDEX"]): s["_pre_status"] for o in occs for s in o["stirrups"]}
    widened, narrower = [], []
    for c in res["components"]:
        rel = c["state"] in ("VERIFIED", "LOWER_BOUND")
        if c["bar_run_id"]:
            pre = pre_run.get(c["bar_run_id"])
        elif c["component"] == "STIRRUP_COUNT":
            pre = pre_st.get((c["occurrence_id"], c["span_index"]))
        else:
            pre = None
        if rel and pre not in RELEASABLE:
            widened.append((c["record_id"], pre))
        if not rel and pre in RELEASABLE:
            narrower.append((c["record_id"], pre, c["state"]))
    return widened, narrower


def object_conservation(D, res, untagged):
    occ_of_geom = {}
    for r in res["occurrences"]:
        for g in r["geometry_objects"] or []:
            if g in occ_of_geom:
                raise SystemExit(f"{g} belongs to two S6 occurrences")
            occ_of_geom[g] = r["occurrence_id"]
    ut = {u["object_id"] for u in untagged}
    rows = []
    for o in D["c01"]:
        k, oid = o["OBJECT_KIND"], o["OBJECT_ID"]
        if k == "TAG":
            occ = occ_of_geom.get(o["BOUND_GEOMETRY"])
            term = f"IN_S6_OCCURRENCE ({o['TERMINAL']})" if occ else "UNTERMINATED"
        elif o["TERMINAL"] == "GEOMETRY_WITHOUT_TAG":
            occ = oid if oid in ut else None
            term = "GEOMETRY_WITHOUT_TAG (BLOCKED_TYPE)" if occ else "UNTERMINATED"
        elif o["TERMINAL"] == "NOT_BEAM":
            occ, term = None, "NOT_REBAR_APPLICABLE (band fragment, not a beam)"
        elif o["TERMINAL"] == "OUT_OF_SCOPE_FAMILY":
            occ, term = None, "OUT_OF_SCOPE_FAMILY (not a simple / continuous beam occurrence)"
        else:
            occ = occ_of_geom.get(oid)
            term = f"IN_S6_OCCURRENCE ({o['TERMINAL']})" if occ else "UNTERMINATED"
        rows.append({"object_id": oid, "object_kind": k, "sheet": o["SHEET"], "mark": o["MARK"],
                     "pre_s6_terminal": o["TERMINAL"], "s6_terminal": term, "s6_occurrence_id": occ,
                     "why": o["WHY"]})
    bad = [r["object_id"] for r in rows if r["s6_terminal"] == "UNTERMINATED"]
    if bad:
        raise SystemExit(f"objects without an S6 terminal: {bad}")
    used = set(occ_of_geom) - {r["object_id"] for r in rows}
    if used:
        raise SystemExit(f"S6 geometry objects not in the PRE-S6 conservation register: {sorted(used)}")
    return rows


def token_terminals(D, res):
    blocked_marks = {r["mark"] for r in res["occurrences"] if r["occurrence_state"] == "BLOCKED"}
    consumers = defaultdict(list)
    for c in res["components"]:
        for t in c.get("source_tokens") or []:
            consumers[t["token_id"]].append(c["state"])
    rows = []
    for t in D["c09"]:
        tok = _tok(t)
        term = SB.token_terminal(tok, consumers.get(t["TOKEN_ID"], []),
                                 in_blocked_occurrence=t["TYPE"] in blocked_marks)
        if term.startswith("EXCLUDED") and consumers.get(t["TOKEN_ID"]):
            raise SystemExit(f"non-rebar token {t['TOKEN_ID']} feeds a component")
        rows.append({"token_id": t["TOKEN_ID"], "source": t["SOURCE"], "handle": t["HANDLE"], "type": t["TYPE"],
                     "field_family": t["FIELD_FAMILY"], "raw": t["RAW"], "normalised": t["NORMALISED"],
                     "grammar": t["GRAMMAR"], "pre_s6_terminal": t["TERMINAL"], "s6_terminal": term,
                     "s6_components": len(consumers.get(t["TOKEN_ID"], [])),
                     "s6_released_components": sum(1 for s in consumers.get(t["TOKEN_ID"], [])
                                                   if s in ("VERIFIED", "LOWER_BOUND"))})
    return rows


# ------------------------------------------------------------------------------------------------------ README
def readme(s, cons, ctx, widened, narrower, s61):
    f = s["families"]
    sb, cb = f["SIMPLE_BEAM"], f["CONTINUOUS_BEAM"]
    dia = "; ".join(f"Ø{k}: {v['kg']:.2f} kg / {v['length_m']:.2f} m" for k, v in s["diameter_distribution"].items())
    return f"""# S6 - accurate superstructure beam rebar (simple + continuous beams)

**{s['headline']}: {s['known_source_derived_superstructure_beam_rebar_kg']:.2f} kg (lower bound).**
**{s['final_superstructure_beam_rebar']}.**

Built blind from the frozen PRE-S6 package only (hash-checked); engine `engine/source/superstructure_beam_rebar.py`,
builder `build_superstructure_beam_rebar_s6.py`, stamp `{ctx['ENGINE_COMMIT']}`. Frozen in `S6_FREEZE_MANIFEST.json`
(FROZEN_BEFORE_REFERENCE_COMPARISON) before any reference was opened.

| | SIMPLE_BEAM | CONTINUOUS_BEAM |
|---|---|---|
| occurrences | {sb['occurrences']} | {cb['occurrences']} |
| occurrences by state | {sb['occurrences_by_state']} | {cb['occurrences_by_state']} |
| VERIFIED_KG | {sb['VERIFIED_KG']:.2f} | {cb['VERIFIED_KG']:.2f} |
| LOWER_BOUND_KNOWN_KG | {sb['LOWER_BOUND_KNOWN_KG']:.2f} | {cb['LOWER_BOUND_KNOWN_KG']:.2f} |
| PROVISIONAL_KG | {sb['PROVISIONAL_KG']:.2f} | {cb['PROVISIONAL_KG']:.2f} |
| BLOCKED_MODELLED_KG | {sb['BLOCKED_MODELLED_KG']:.2f} | {cb['BLOCKED_MODELLED_KG']:.2f} |
| BLOCKED_UNQUANTIFIED mass components | {sb['BLOCKED_UNQUANTIFIED_COMPONENTS']} | {cb['BLOCKED_UNQUANTIFIED_COMPONENTS']} |
| blocked count records | {sb['BLOCKED_UNQUANTIFIED_COUNT_RECORDS']} | {cb['BLOCKED_UNQUANTIFIED_COUNT_RECORDS']} |
| known straight length (m) | {sb['known_straight_length_m']:.3f} | {cb['known_straight_length_m']:.3f} |
| released by component | {sb['released_by_component']} | {cb['released_by_component']} |
| stirrup count records / stirrups (LB) | {sb['stirrup_counts_quantified']} / {sb['stirrup_count_lower_bound_total']} | {cb['stirrup_counts_quantified']} / {cb['stirrup_count_lower_bound_total']} |

MID_KNOWN_KG {s['MID_KNOWN_KG']:.2f} kg (CB MID support bars, straight extent only). STIRRUP_COUNT_KNOWN
{s['STIRRUP_COUNT_KNOWN']['records']} records / {s['STIRRUP_COUNT_KNOWN']['stirrups_lower_bound']} stirrups (lower bound, no +1).
STIRRUP_MASS_KNOWN: {s['STIRRUP_MASS_KNOWN']['records']} records (blocked: legs, path, hooks). Untagged geometry kept
visible: {s['untagged_geometry']} (BLOCKED_TYPE). Diameter distribution: {dia}.

## What the numbers are

* kg = count x straight run x D^2/162 on the PRE-S6 source segments only: simple beams support face to support
  face; CB bars clear span + through-support widths + 7.5 cm beyond the far face only where PRE-S6 bound that
  typical dimension to that bar; MID bars 0.22 x Ln (axis to axis, the drawing's own symbol) from each face + the
  support width - re-computed by the engine from the span table and checked against PRE-S6.
* Every released row is LOWER_BOUND: the straight segment is SOURCE_VERIFIED where its extent is complete, but no
  bar is called complete (development, hooks, in-span end treatment not established). VERIFIED_KG is 0 by design.
* PROVISIONAL_KG and BLOCKED_MODELLED_KG are 0: candidate bindings, width conflicts and other blocked occurrences
  carry no hidden kg; their counts, diameters and known geometry stay in the registers.
* ELEMENT_FAMILY is BEAM with ELEMENT_SUBFAMILY SIMPLE_BEAM / CONTINUOUS_BEAM: the frozen generic provenance contract
  (rebar_provenance) knows BEAM, not the subfamilies, and is not edited.

## Never released in S6
CB top bars (frame top bars, end-support bars '0.3 Ln2'), hangers, side bars ('2Ø12/30cm' text kept), development
and hooks, stirrup mass, opening extras (no physical opening in any beam), the curved ring beams, the cantilever,
WITH STAIR and planted-column spans, candidate bindings, width conflicts, CB2 / CB3 / CB4 / CB5 / CB8 / CB10, CB13
bottom bars (readings differ) and every untagged geometry. T/M values are design loads: excluded from parsing,
components, mass and BBS (token terminals EXCLUDED_DESIGN_LOAD).

## Scope
Widened components: {len(widened)} (must be 0). Narrower than PRE-S6: {len(narrower)}. S6.1 release candidates found
but not released (frozen scope): {len(s61)} - see `S6_1_RELEASE_CANDIDATES.csv`.

## Conservation
{chr(10).join(f'* {k}: {v}' for k, v in cons.items())}

## Questions
Carried from PRE-S6 (Q1-Q9, R1-R6): `SUPERSTRUCTURE_BEAM_ENGINEERING_QUESTIONS.csv`. An answer becomes a versioned
claim and an S6.1 delta; the S6 baseline is never rewritten.
"""


# ------------------------------------------------------------------------------------------------------- main
def main():
    verify_pre_s6()
    D = load()
    toks = Tokens(D["c09"])
    R = rules(D["summary"], D["c06"], len(D["c08"]))
    occs, untagged = occurrences(D, toks)
    ctx = {"PROJECT_ID": D["tpl"]["context"]["PROJECT_ID"], "DRAWING_ID": D["tpl"]["context"]["DRAWING_ID"],
           "DRAWING_SHA": DRAWING_SHA, "REVISION": "ALSENAN_ST7757_DXF",
           "ENGINE_COMMIT": f"{BASELINE}+code:{code_digest()[:16]}",
           "REGISTER_VERSION": "SUPERSTRUCTURE_BEAM_REBAR_REGISTER_V1", "CALCULATION_ROUND": "S6",
           "unit_mass": {"method": "D2_OVER_162", "authority": "Urban project default (R3); S6 brief 22"}}
    engine_occs = [{k: v for k, v in o.items() if not k.startswith("_")} for o in occs]
    for o in engine_occs:
        o["bar_runs"] = [{k: v for k, v in r.items() if not k.startswith("_")} for r in o["bar_runs"]]
        o["stirrups"] = [{k: v for k, v in s.items() if not k.startswith("_")} for s in o["stirrups"]]
    res = SB.run(engine_occs, R, ctx, untagged=untagged)
    if not res["conservation"]["all_pass"]:
        raise SystemExit(f"conservation failed: {res['conservation']['checks']}")
    pop = Counter(r["subfamily"] for r in res["occurrences"])
    if dict(pop) != EXPECTED:
        raise SystemExit(f"occurrence population {dict(pop)} != {EXPECTED}")
    for sub, want in EXPECTED_RELEASE.items():
        got = dict(Counter(r["occurrence_state"] for r in res["occurrences"] if r["subfamily"] == sub))
        if got != want:
            raise SystemExit(f"{sub} release {got} != frozen PRE-S6 scope {want}")
    pre_occ = {o["occurrence_id"]: o["_pre"]["OCCURRENCE_STATUS"] for o in occs}
    diff = [r["occurrence_id"] for r in res["occurrences"] if r["occurrence_state"] != pre_occ[r["occurrence_id"]]]
    if diff:
        raise SystemExit(f"occurrence states differ from PRE-S6: {diff}")
    widened, narrower = scope_check(res, occs)
    if widened:
        raise SystemExit(f"S6 would widen the frozen PRE-S6 scope: {widened}")
    stir = {f: res["summary"]["families"][f]["stirrup_counts_quantified"] for f in EXPECTED_STIRRUP_RELEASE}
    if stir != EXPECTED_STIRRUP_RELEASE:
        raise SystemExit(f"stirrup count releases {stir} != {EXPECTED_STIRRUP_RELEASE}")
    if len(res["untagged"]) != EXPECTED_UNTAGGED:
        raise SystemExit(f"untagged geometry {len(res['untagged'])} != {EXPECTED_UNTAGGED}")
    side_n = sum(1 for o in occs if o["side"] and o["side"]["applicability"] == "PRINTED")
    if side_n != EXPECTED_SIDE:
        raise SystemExit(f"side-bar occurrences {side_n} != {EXPECTED_SIDE}")
    objs = object_conservation(D, res, untagged)
    tags = [o for o in objs if o["object_kind"] == "TAG"]
    if len(tags) != EXPECTED_TAGS or len({t["object_id"] for t in tags}) != EXPECTED_TAGS:
        raise SystemExit(f"tags {len(tags)} != {EXPECTED_TAGS}")
    tokrows = token_terminals(D, res)
    s61 = [c for o in occs for c in o["_s61"]]
    reg_v = ctx["REGISTER_VERSION"]

    # ---------------------------------------------------------------------------------------------- registers
    _json(HERE / "SUPERSTRUCTURE_BEAM_OCCURRENCE_REGISTER.json", {
        "register": "SUPERSTRUCTURE_BEAM_OCCURRENCE_REGISTER", "policy": SB.policy_record(), "context": ctx,
        "rules": R, "occurrences": engine_occs, "untagged": untagged,
        "pre_s6_occurrence_status": dict(sorted(pre_occ.items())),
        "scope_check": {"widened": widened, "narrower_than_pre_s6": narrower}})
    occ_fields = ["occurrence_id", "subfamily", "element_family", "mark", "sheet", "floor", "occurrence_terminal",
                  "occurrence_state", "pre_s6_occurrence_status", "known_kg", "known_straight_length_m",
                  "mid_known_kg", "stirrup_count_lower_bound", "stirrup_count_records_released",
                  "unquantified_components", "occurrence_blocking_reason", "components_by_state", "cb_group_id",
                  "span_sequence", "reading_direction_state", "sequence_state", "source_handles", "geometry_handles",
                  "tag_handles", "schedule_handles", "start_support", "end_support", "drawn_width_mm",
                  "schedule_width_mm", "width_match_state", "detail_id", "detail_candidates", "schedule_row",
                  "binding_state", "authority_state", "geometry_objects", "geometry", "flags", "drawing_sha",
                  "register_version"]
    occ_rows = [dict(r, pre_s6_occurrence_status=pre_occ[r["occurrence_id"]], drawing_sha=DRAWING_SHA,
                     register_version=reg_v) for r in res["occurrences"]] + \
        [dict(u, pre_s6_occurrence_status="BLOCKED", drawing_sha=DRAWING_SHA, register_version=reg_v)
         for u in res["untagged"]]
    _csv(HERE / "SUPERSTRUCTURE_BEAM_OCCURRENCES.csv", occ_rows, occ_fields)
    comp_fields = ["record_id", "occurrence_id", "subfamily", "mark", "cb_group_id", "component",
                   "accurate_component", "quantity_kind", "state", "release_basis", "bar_run_id", "span_index",
                   "dia_mm", "bar_count", "straight_run_m", "total_length_m", "kg_per_m", "kg", "count",
                   "count_convention_not_adopted", "known_source_segment_state", "complete_bar_state",
                   "mid_straight_run_state", "raw_text", "spacing_cm", "missing", "missing_facets", "question_id",
                   "why"]
    _csv(HERE / "SUPERSTRUCTURE_BEAM_COMPONENTS.csv", res["components"], comp_fields)
    pre_run = {r["BAR_RUN_ID"]: r["_pre"] for o in occs for r in o["bar_runs"]}
    runs = []
    for c in res["components"]:
        if not c["bar_run_id"]:
            continue
        pv = c["provenance"]
        runs.append({"BAR_RUN_ID": c["bar_run_id"], "CB_GROUP_ID": c["cb_group_id"],
                     "occurrence_id": c["occurrence_id"], "subfamily": c["subfamily"], "mark": c["mark"],
                     "BAR_ROLE": c["component"], "frame_role": c.get("frame_role"), "label": c.get("label"),
                     "count": c.get("bar_count"), "dia_mm": c.get("dia_mm"),
                     "START_LOCATION": c.get("start_location"), "SPANS_CROSSED": c.get("spans_crossed"),
                     "INTERMEDIATE_SUPPORTS": c.get("intermediate_supports"), "END_LOCATION": c.get("end_location"),
                     "SOURCE_EXTENT": c.get("source_extent"), "segments": c.get("segments"),
                     "STRAIGHT_LENGTH_M": c.get("straight_run_m"), "register_run_m": c.get("register_run_m"),
                     "total_length_m": c.get("total_length_m"), "kg": c["kg"], "state": c["state"],
                     "release_basis": c.get("release_basis"),
                     "known_source_segment_state": c.get("known_source_segment_state"),
                     "complete_bar_state": c.get("complete_bar_state") or "NOT_ESTABLISHED",
                     "mid_straight_run_state": c.get("mid_straight_run_state"), "mid_rule": c.get("mid"),
                     "rules_used": c.get("rules_used"), "pre_s6_status": pre_run[c["bar_run_id"]]["STATUS"],
                     "pre_s6_span_mapping": pre_run[c["bar_run_id"]]["SPAN_MAPPING"],
                     "source_handles": pv["SOURCE_HANDLES"], "geometry_handles": pv["GEOMETRY_HANDLES"],
                     "schedule_handles": pv["SCHEDULE_HANDLES"], "missing": c.get("missing"), "why": c["why"]})
    _csv(HERE / "SUPERSTRUCTURE_BEAM_BAR_RUNS.csv", runs)
    _csv(HERE / "SUPERSTRUCTURE_BEAM_BBS_NET.csv", res["bbs"])
    core = {(c["occurrence_id"], c["span_index"]): c for c in res["components"] if c["component"] ==
            "STIRRUP_CORE_PATH"}
    stir_rows = []
    for c in res["components"]:
        if c["component"] != "STIRRUP_COUNT":
            continue
        cp = core[(c["occurrence_id"], c["span_index"])]
        stir_rows.append({"occurrence_id": c["occurrence_id"], "subfamily": c["subfamily"], "mark": c["mark"],
                          "cb_group_id": c["cb_group_id"], "span_index": c["span_index"], "state": c["state"],
                          "count_lower_bound": c.get("count"),
                          "count_convention_not_adopted": c.get("count_convention_not_adopted"),
                          "DIAMETER_MM": c.get("dia_mm"), "RATE_OR_SPACING": c.get("rate_or_spacing"),
                          "distribution_m": c.get("distribution_m"), "NUMBER_OF_LEGS": c.get("legs"),
                          "HOOKS": c.get("hooks"), "END_ZONE": c.get("end_zone"),
                          "FIRST_LAST_RULE": c.get("first_last"), "CORE_PATH_STATE": cp["state"],
                          "CORE_PATH_MISSING": cp.get("missing_facets"), "STIRRUP_KG": None,
                          "release_basis": c.get("release_basis"), "question_id": c.get("question_id"),
                          "why": c["why"]})
    _csv(HERE / "SUPERSTRUCTURE_BEAM_STIRRUP_COUNTS.csv", stir_rows)
    unresolved = [{"occurrence_id": c["occurrence_id"], "subfamily": c["subfamily"], "mark": c["mark"],
                   "record_id": c["record_id"], "component": c["component"], "quantity_kind": c["quantity_kind"],
                   "state": c["state"], "what_is_missing": c.get("missing") or c["why"],
                   "question_id": c.get("question_id") or "", "known_kg": c["kg"], "known_count": c.get("count")}
                  for c in res["components"] if c["state"] in ("BLOCKED_UNQUANTIFIED", "BLOCKED_MODELLED",
                                                               "LOWER_BOUND")]
    unresolved += [{"occurrence_id": u["occurrence_id"], "subfamily": u["subfamily"], "mark": "",
                    "record_id": u["occurrence_id"], "component": "ALL", "quantity_kind": "OCCURRENCE",
                    "state": "BLOCKED_TYPE", "what_is_missing": u["occurrence_blocking_reason"], "question_id": "R6",
                    "known_kg": None, "known_count": None} for u in res["untagged"]]
    _csv(HERE / "SUPERSTRUCTURE_BEAM_UNRESOLVED.csv", unresolved)
    with open(HERE / "SUPERSTRUCTURE_BEAM_PROVENANCE.jsonl", "w", encoding="utf-8") as fh:
        for c in sorted(res["components"], key=lambda z: z["record_id"]):
            fh.write(json.dumps({"record_id": c["record_id"], "state": c["state"],
                                 "quantity_kind": c["quantity_kind"], "kg": c["kg"], "count": c.get("count"),
                                 "is_accurate_part": c["quantity_kind"] == SB.MASS and c["state"] in SB.AR.STATES,
                                 "provenance": c["provenance"]}, sort_keys=True, ensure_ascii=False,
                                default=float) + "\n")
    flags = []
    for o in occs:
        for fl in o["flags"]:
            flags.append({"flag_id": f"FLAG-{len(flags) + 1:03d}", "occurrence_id": o["occurrence_id"],
                          "subfamily": o["subfamily"], "mark": o["mark"], "flag": fl,
                          "effect_on_release": (
                              "BLOCKS_SCHEDULE_DEPENDENT_REBAR" if fl.split(":")[0] in (
                                  "WIDTH_SOURCE_CONFLICT", "BINDING_CANDIDATE", "TWO_MARKS_ONE_SPAN",
                                  "UNDEFINED_CANDIDATE_DETAIL") or fl.startswith("CB_") else
                              "CANDIDATE_INVARIANT_COMPONENTS_ONLY" if fl.startswith("READING_DIRECTION_AMBIGUOUS")
                              else "BLOCKS_LONGITUDINAL_AND_STIRRUPS" if fl.startswith(("CURVED", "CANTILEVER"))
                              else "BLOCKS_OTHER_EXPLICIT_EXTRA" if fl.startswith(("WITH_STAIR", "PLANTED"))
                              else "LOWER_BOUND (extension adds no length)" if fl.startswith("BOTTOM_EXTENSION")
                              else "BLOCKS_SIDE_REBAR_QUANTITY" if fl.startswith("SIDE_BAR")
                              else "NOT_RELEASED_FROZEN_SCOPE" if fl.startswith("S6_1")
                              else "NONE (recorded in provenance)")})
    _csv(HERE / "SUPERSTRUCTURE_BEAM_ENGINEERING_FLAGS.csv", flags)
    sum_fields = [k for k in occ_fields if k not in ("drawing_sha", "register_version", "geometry")]
    for sub, name in ((SB.SIMPLE_BEAM, "SIMPLE_BEAM_REBAR_SUMMARY.csv"),
                      (SB.CONTINUOUS_BEAM, "CONTINUOUS_BEAM_REBAR_SUMMARY.csv")):
        _csv(HERE / name, [r for r in occ_rows if r["subfamily"] == sub], sum_fields)
    _csv(HERE / "SUPERSTRUCTURE_BEAM_OBJECT_CONSERVATION.csv", objs)
    _csv(HERE / "SUPERSTRUCTURE_BEAM_TOKEN_TERMINALS.csv", tokrows)
    q_use = defaultdict(set)
    for c in res["components"]:
        for q in (c.get("question_id") or "").split("+"):
            if q:
                q_use[q].add(c["occurrence_id"])
    for u in res["untagged"]:
        q_use["R6"].add(u["occurrence_id"])
    _csv(HERE / "SUPERSTRUCTURE_BEAM_ENGINEERING_QUESTIONS.csv", [
        {"question_id": q, "carried_from": "PRE-S6 11_ENGINEERING_QUESTIONS.md", "question": QUESTIONS[q],
         "s6_occurrences_blocked_or_bounded": len(q_use.get(q, ())), "occurrences": sorted(q_use.get(q, ())),
         "answer": "OPEN (no answer assumed; an answer becomes a versioned claim -> S6.1 delta)"}
        for q in QUESTIONS])
    _csv(HERE / "S6_1_RELEASE_CANDIDATES.csv", s61 or [{"occurrence_id": "", "mark": "", "component": "",
                                                       "span_index": "", "interpretations": "",
                                                       "would_release_count": "", "why_not_released": ""}],
         ["occurrence_id", "mark", "component", "span_index", "interpretations", "would_release_count",
          "why_not_released"])
    s = res["summary"]
    dia, dia_len = Counter(), Counter()
    for c in res["components"]:
        if c["kg"] is not None:
            dia[c["dia_mm"]] += c["kg"]
            dia_len[c["dia_mm"]] += c["total_length_m"]
    comp_counts = Counter((c["subfamily"], c["component"], c["state"]) for c in res["components"])
    term = Counter(t["s6_terminal"] for t in tokrows)
    obj_term = Counter(o["s6_terminal"].split(" (")[0] for o in objs)
    s.update(conservation=res["conservation"], context=ctx,
             headline_lines=[s["headline"], s["final_superstructure_beam_rebar"]],
             diameter_distribution={str(k): {"kg": dia[k], "length_m": dia_len[k]} for k in sorted(dia)},
             total_source_derived_straight_length_m=sum(dia_len.values()),
             component_population={f"{f}:{c}:{st}": n for (f, c, st), n in sorted(comp_counts.items())},
             provenance={"records": len(res["components"]), "accurate_parts": len(res["parts"]),
                         "validated": len(res["components"]),
                         "contract": "rebar_provenance generic identity (ELEMENT_FAMILY BEAM) + S6 fields "
                                     "(ELEMENT_SUBFAMILY, CB_GROUP_ID, SPAN_INDEX, BAR_RUN_ID, ...)"},
             scope_check={"widened": len(widened), "narrower_than_pre_s6": narrower,
                          "s6_1_release_candidates": len(s61)},
             object_conservation={"objects": len(objs), "by_terminal": dict(sorted(obj_term.items())),
                                  "tags": len(tags)},
             token_conservation={"tokens": len(tokrows), "by_terminal": dict(sorted(term.items()))},
             bar_runs={"total": len(runs), "released": sum(1 for r in runs if r["state"] == "LOWER_BOUND"),
                       "by_role_state": dict(sorted(Counter(f"{r['subfamily']}:{r['BAR_ROLE']}:{r['state']}"
                                                            for r in runs).items()))},
             questions_open=sorted(QUESTIONS))
    _json(HERE / "SUPERSTRUCTURE_BEAM_RELEASE_SUMMARY.json", s)
    (HERE / "README.md").write_text(readme(s, res["conservation"]["checks"], ctx, widened, narrower, s61),
                                    encoding="utf-8")
    manifest = {"round": "S6", "baseline": BASELINE, "state": "FROZEN_BEFORE_REFERENCE_COMPARISON",
                "code": {c: _sha(ROOT / c) for c in CODE}, "inputs": {i: _sha(ROOT / i) for i in INPUTS},
                "outputs": {o: _sha(HERE / o) for o in OUTPUTS}, "engine_commit_stamp": ctx["ENGINE_COMMIT"],
                "references_read_before_freeze": [],
                "rule": "the post-freeze comparison script refuses to run unless every hash above still matches; a "
                        "correction found by the comparison needs a new issue, new evidence, a new regression and a "
                        "new version - never an edit of these outputs and never a tuning to a reference"}
    _json(HERE / "S6_FREEZE_MANIFEST.json", manifest)
    print(json.dumps({"known_kg": s["known_source_derived_superstructure_beam_rebar_kg"],
                      "final": s["final_superstructure_beam_rebar"], "MID_KNOWN_KG": s["MID_KNOWN_KG"],
                      "families": {f: {k: v[k] for k in ("occurrences_by_state", "LOWER_BOUND_KNOWN_KG",
                                                         "BLOCKED_UNQUANTIFIED_COMPONENTS",
                                                         "stirrup_counts_quantified", "released_by_component")}
                                   for f, v in s["families"].items()},
                      "narrower": len(narrower), "s6_1": len(s61)}, indent=1, default=float))


if __name__ == "__main__":
    main()
