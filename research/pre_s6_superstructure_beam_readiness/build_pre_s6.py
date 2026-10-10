"""PRE-S6 superstructure beam rebar readiness: simple beams + continuous beams (no kg).

    python3 -I research/pre_s6_superstructure_beam_readiness/build_pre_s6.py [ST7757.dxf]

Reads only the Urban project source ST7757.dxf (sha256-checked) through the S1 lab census
(research/external_engine_lab/alsenan_structural_s1.py), the R3 continuous-beam frame parser
(alsenan_rebar_v3.cb_graphics) and the schedule reader V2, plus the frozen S1 registers (checked against the S1 INDEX)
and the R4 rule / visual-claim registers. Nothing else is opened: no reference quantity, no old total, no other
package. Every decision is made by engine/source/beam_rebar_readiness.py; this builder measures and records.

Measurements:
  * binding: every beam tag against every member band / arc band in reach (beam_rebar_readiness.binding_decision),
    iterated to a fixed point on the span claims; shared faces between parallel bands are recorded (face pairing);
  * conservation: every tag, every member span, every arc band, every short band fragment terminates exactly once;
  * schedule semantics: SBT and C-BEAM2 / C-BEAM3 attributes (raw kept apart from interpretation), the header
    labels, REMARKS texts and icon blocks, the MIDDLE REINT. column, '(STIR)' labels, '/m' stirrup-zone dimensions,
    ' t/m' load labels;
  * CB typical headers: each parametric dimension ('0.22 Ln', '7.5cm', '0.15L', '0.3 Ln2', 'L', 'Ln', ...) is bound
    to a bar end and a support face (or two axes / two faces) by its defpoints - never by its text alone;
  * bar runs from support faces; CB bars crossing a support are one run; stirrup counts are lower bounds only;
  * openings: S-OPENING outlines and 'void' inserts against every beam band.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LAB = ROOT / "research" / "external_engine_lab"
for p in (ROOT, LAB):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import alsenan_rebar_v3 as R3  # noqa: E402
import alsenan_structural_s1 as S  # noqa: E402
from engine.source import beam_rebar_readiness as BR  # noqa: E402
from engine.source import schedule_grammar as SG  # noqa: E402

BASELINE = "3b36f2b"
DRAWING_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
DEFAULT_DXF = ROOT / "data" / "inputs" / "by_sha256" / f"{DRAWING_SHA}.dxf"
S1 = ROOT / "research" / "alsenan_structural_census_s1"
R4 = ROOT / "research" / "alsenan_rebar_source_exhaustion_04" / "registers"
CODE = ["engine/source/beam_rebar_readiness.py", "engine/source/schedule_grammar.py",
        "research/external_engine_lab/alsenan_structural_s1.py", "research/external_engine_lab/alsenan_rebar_v3.py",
        "research/external_engine_lab/alsenan_structural_source_v2.py",
        "research/pre_s6_superstructure_beam_readiness/build_pre_s6.py"]
S1_FROZEN = ["BEAM_OCCURRENCE_REGISTER", "BEAM_DEFINITION_REGISTER", "CONTINUOUS_BEAM_OCCURRENCE_REGISTER",
             "COLUMN_VERTICAL_CHAIN_REGISTER"]
INPUTS = [S1 / "INDEX.json"] + [S1 / f"{n}.json" for n in S1_FROZEN] + [
    R4 / "PROJECT_REBAR_RULE_REGISTER.json", R4 / "VISUAL_SOURCE_CLAIM_REGISTER.json"]
SHEETS = ("GFRS", "FFRS", "SFRS")
FLOOR = {"GFRS": "GF_ROOF", "FFRS": "1F_ROOF", "SFRS": "2F_ROOF"}
PLANTED_SHEET = {"GF_ROOF_SLAB": "GFRS", "1F_ROOF_SLAB": "FFRS", "2F_ROOF_SLAB": "SFRS"}
REGISTER_VERSION = "SUPERSTRUCTURE_BEAM_READINESS_V1"
DIM_SNAP_UNITS = 30.0      # defpoint-to-bar-end snap in the N.T.S. typical (< 1/9 of its 280-360 unit text height)
SHARED_FACE_MM = 15.0      # two parallel bands share a face when their facing edges coincide within this
OPENING_DEPTH_MM = 20.0    # an opening outline must reach this far inside a beam band to count as inside it
FIXED_POINT_PASSES = 8
LONG = ("BOTTOM_MAIN", "TOP_MAIN")
OUTPUTS = ["01_BEAM_OCCURRENCE_CONSERVATION.csv", "02_BEAM_BINDING_READINESS.csv",
           "03_SIMPLE_BEAM_SCHEDULE_SEMANTICS.csv", "04_CONTINUOUS_BEAM_SCHEDULE_SEMANTICS.csv",
           "05_CB_SPAN_SEQUENCE.csv", "06_BEAM_BAR_RUN_READINESS.csv", "07_BEAM_SIDE_REBAR_READINESS.csv",
           "08_BEAM_OPENING_OCCURRENCES.csv", "09_BEAM_TOKEN_CORPUS.csv",
           "10_SUPERSTRUCTURE_BEAM_REBAR_READINESS.csv", "11_ENGINEERING_QUESTIONS.md",
           "12_S6_SCOPE_RECOMMENDATION.md", "00_README.md", "PRE_S6_SUMMARY.json", "S6_PROVENANCE_TEMPLATES.json"]


# ============================================================================================ io helpers
def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _j(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, float):
        return f"{v:.6g}" if abs(v) < 1e6 else f"{v:.1f}"
    if isinstance(v, (dict, list, tuple)):
        return json.dumps(_clean(v), sort_keys=True, ensure_ascii=False)
    return str(v)


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if isinstance(o, float) or type(o).__name__.startswith("float"):
        f = float(o)
        return round(f, 4) if math.isfinite(f) else None
    if type(o).__name__.startswith(("int", "uint")):
        return int(o)
    if type(o).__name__ == "bool_":
        return bool(o)
    return o


def _csv(name, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in fields})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def _json(name, obj):
    (HERE / name).write_text(json.dumps(_clean(obj), indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                             encoding="utf-8")


def code_digest():
    h = hashlib.sha256()
    for c in CODE:
        h.update(c.encode())
        h.update((ROOT / c).read_bytes())
    return h.hexdigest()


def _hkey(h):
    try:
        return (0, int(str(h).split(":")[0], 16), str(h))
    except ValueError:
        return (1, 0, str(h))


def _r(v, n=3):
    return None if v is None else round(float(v), n)


# ============================================================================================ inputs
def verify_inputs(dxf):
    if _sha(dxf) != DRAWING_SHA:
        raise SystemExit(f"ST7757.dxf sha256 mismatch: {dxf}")
    if Path(S.DXF).resolve() != Path(dxf).resolve() and _sha(S.DXF) != DRAWING_SHA:
        raise SystemExit("the S1 lab reads a different drawing")
    idx = _j(S1 / "INDEX.json")["registers"]
    for n in S1_FROZEN:
        if _sha(S1 / f"{n}.json") != idx[n]["sha256"]:
            raise SystemExit(f"frozen S1 register changed: {n}")
    return {n: idx[n]["sha256"] for n in S1_FROZEN}


def rules_and_claims():
    rules = {r["rule_id"]: r for r in _j(R4 / "PROJECT_REBAR_RULE_REGISTER.json")["rules"]}
    claims = {c["claim_id"]: c for c in _j(R4 / "VISUAL_SOURCE_CLAIM_REGISTER.json")["claims"]}
    return rules, claims


# ============================================================================================ geometry helpers
def _deg(v):
    return math.degrees(math.atan2(v[1], v[0])) % 180.0


def shared_faces(lines):
    """Parallel bands whose facing edges coincide (|offset gap - (w1 + w2) / 2| <= tol) over > 300 mm: the middle
    face is shared, so at most one of the two can be the beam there (face-pairing evidence, never a decision)."""
    out = defaultdict(list)
    for i, a in enumerate(lines):
        for b in lines[i + 1:]:
            if abs(a["dir"][0] * b["dir"][1] - a["dir"][1] * b["dir"][0]) > 0.02:
                continue
            sgn = 1.0 if a["dir"][0] * b["dir"][0] + a["dir"][1] * b["dir"][1] >= 0 else -1.0
            gap = abs(a["offset"] - sgn * b["offset"])
            if abs(gap - (a["width_mm"] + b["width_mm"]) / 2) > SHARED_FACE_MM:
                continue
            b0, b1 = sorted((sgn * b["t0"], sgn * b["t1"]))
            ov = min(a["t1"], b1) - max(a["t0"], b0)
            if ov > 300:
                out[a["line_id"]].append(b["line_id"])
                out[b["line_id"]].append(a["line_id"])
    return {k: sorted(v) for k, v in out.items()}


def span_at(x, line, along):
    sp = [q for q in x["spans"].get(line["line_id"], []) if q["s0"] - 1 <= along <= q["s1"] + 1]
    return sp[0] if sp else None


def span_key(line_id, q):
    return (line_id, round(q["s0"]), round(q["s1"]))


def obj_id(sheet, key):
    if key[1] is None:
        return f"ARC:{sheet}:{key[0]}"
    return f"SPAN:{sheet}:{key[0]}:{key[1]}-{key[2]}"


def candidates_for(x, t, claims, shared):
    """Every member band / arc band in reach of tag t, with the evidence binding_decision weighs."""
    c = S._text_centre(t)
    out = []
    for line in x["lines"]:
        s_, d = S._proj(line, c)
        lim = max(950.0, line["width_mm"] / 2 + 700)
        if not (line["t0"] - 500 <= s_ <= line["t1"] + 500 and abs(d) <= lim):
            continue
        q = span_at(x, line, s_)
        key = span_key(line["line_id"], q) if q else (line["line_id"], None, None)
        others = [m for h, m in claims.get(key, []) if h != t["handle"]]
        adj = False
        if q:
            sps = x["spans"][line["line_id"]]
            i = sps.index(q)
            for j in (i - 1, i + 1):
                if 0 <= j < len(sps):
                    k2 = span_key(line["line_id"], sps[j])
                    adj = adj or any(m == t["text"] for h, m in claims.get(k2, []) if h != t["handle"])
        out.append({"member_id": line["line_id"], "kind": "LINE", "distance_mm": round(abs(d), 1),
                    "distance_limit_mm": lim, "within_extent": True, "member_dir_deg": _deg(line["dir"]),
                    "width_mm": line["width_mm"], "span_other_marks": others, "same_mark_adjacent": adj,
                    "same_mark_on_span": t["text"] in others, "inside_physical_extent": line["t0"] <= s_ <= line["t1"],
                    "supported_both_ends": bool(q) and q["start"]["kind"] != "FREE_END" and
                    q["end"]["kind"] != "FREE_END",
                    "_key": key, "_along": round(s_, 1), "_shared": shared.get(line["line_id"], [])})
    for a in x["arc_bands"]:
        dd = abs(math.dist(c, a["centre"]) - a["r_mid_mm"])
        if dd > 950:
            continue
        angp = math.degrees(math.atan2(c[1] - a["centre"][1], c[0] - a["centre"][0])) % 360
        rel = (angp - a["start_deg"]) % 360
        if not (rel <= a["sweep_deg"] + 25 or rel >= 360 - 25):
            continue
        key = (a["band_id"], None, None)
        others = [m for h, m in claims.get(key, []) if h != t["handle"]]
        out.append({"member_id": a["band_id"], "kind": "ARC", "distance_mm": round(dd, 1), "within_extent": True,
                    "member_dir_deg": (angp + 90) % 180, "width_mm": a["width_mm"], "span_other_marks": others,
                    "same_mark_adjacent": False, "same_mark_on_span": t["text"] in others,
                    "inside_physical_extent": rel <= a["sweep_deg"], "supported_both_ends": None,
                    "_key": key, "_along": None, "_shared": []})
    return out


def schedule_width_mm(defs, mark):
    d = defs.get(mark)
    return d["fields"]["B_cm"] * 10 if d and d["fields"].get("B_cm") else None


def bind_sheet(x, defs, shared):
    """Fixed point: span claims start from the S1 bindings and are replaced by this round's bound decisions until
    the decisions stop changing (each tag is still decided alone, on its own evidence)."""
    claims = defaultdict(list)
    for o in x["occurrences"]:
        if o.get("span"):
            claims[span_key(o["member"], o["span"])].append((o["tag_handle"], o["tag"]))
        elif o.get("member_kind") == "ARC" and o.get("member"):
            claims[(o["member"], None, None)].append((o["tag_handle"], o["tag"]))
    history = []
    for _ in range(FIXED_POINT_PASSES):
        dec = {}
        for t in sorted(x["tags"], key=lambda t: _hkey(t["handle"])):
            cs = candidates_for(x, t, claims, shared)
            r = BR.binding_decision({"handle": t["handle"], "mark": t["text"],
                                     "rotation_deg": t.get("rotation") or 0.0}, cs,
                                    schedule_width_mm=schedule_width_mm(defs, t["text"]))
            by = {c["member_id"]: c for c in cs}
            r["_key"] = by[r["member_id"]]["_key"] if r["member_id"] else None
            r["_cands"] = cs
            dec[t["handle"]] = r
        sig = tuple(sorted((h, r["decision"], r["member_id"]) for h, r in dec.items()))
        if history and sig == history[-1]:
            return dec, len(history)
        history.append(sig)
        claims = defaultdict(list)
        for t in x["tags"]:
            r = dec[t["handle"]]
            if r["member_id"] and r["_key"]:
                claims[r["_key"]].append((t["handle"], t["text"]))
    raise SystemExit("binding did not reach a fixed point")


# ============================================================================================ planted columns, stair
def planted_columns(B):
    chains = _j(S1 / "COLUMN_VERTICAL_CHAIN_REGISTER.json")["rows"]
    out = []
    for c in chains:
        sh = PLANTED_SHEET.get(c.get("planted_on") or "")
        if not sh:
            continue
        h = (c.get("members_by_sheet") or {}).get(sh)
        col = B["C"]["byid"].get(f"{sh}:{h}")
        if col:
            out.append({"chain_id": c["chain_id"], "sheet": sh, "outline": h, "centre": tuple(col["centre"]),
                        "half": (float(col["dx_mm"]) / 2, float(col["dy_mm"]) / 2), "type": c.get("column_type")})
    return out


def stair_qualifiers():
    d = _j(S1 / "BEAM_OCCURRENCE_REGISTER.json")["summary"]["stair_qualifiers"]
    return {(q["sheet"], q["tag_handle"]): q["qualifier_handle"] for q in d if q.get("tag_handle")}


# ============================================================================================ CB typical headers
def _num_cm(text):
    m = re.fullmatch(r"\s*([0-9.]+)\s*cm\s*", text)
    return float(m.group(1)) / 100.0 if m else None


def typical_headers(msp):
    """The CB schedule headers each carry one N.T.S. typical elevation. Every overridden S-DIM.SCH dimension in it
    is bound by its defpoints: (bar end, support face) -> an extent rule; (axis, axis) or (face, face) -> the
    definition of a span symbol. Labels are checked against the spans they name."""
    titles = sorted([t for t in msp.query("TEXT") if "SCHEDULE OF CONTINUES BEAMS" in (t.dxf.text or "")],
                    key=lambda t: t.dxf.insert.x)
    heads = []
    for i, t in enumerate(titles):
        x0 = t.dxf.insert.x - 2600
        x1 = titles[i + 1].dxf.insert.x - 2600 if i + 1 < len(titles) else t.dxf.insert.x + 25000
        heads.append({"id": f"TYP-{t.dxf.handle}", "title_handle": t.dxf.handle, "title": t.dxf.text,
                      "spans": 3 if "THREE" in t.dxf.text.upper() else 2, "x": (x0, x1), "y": (12000.0, 16400.0)})
    for hd in heads:
        (x0, x1), (y0, y1) = hd["x"], hd["y"]
        bars, faces, axes, dims = [], set(), set(), []
        for e in msp:
            ty = e.dxftype()
            if ty == "LINE":
                pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
            elif ty == "LWPOLYLINE":
                pts = [(p[0], p[1]) for p in e.get_points()]
            elif ty == "DIMENSION":
                p = e.dxf.defpoint
                txt = (e.dxf.text or "").strip()
                if e.dxf.layer == "S-DIM.SCH" and txt and txt != "<>" and x0 <= p.x <= x1 and y0 <= p.y <= y1 + 300:
                    dims.append({"handle": e.dxf.handle, "text": txt, "p2": round(e.dxf.defpoint2.x, 1),
                                 "p3": round(e.dxf.defpoint3.x, 1), "y": round(p.y, 1)})
                continue
            else:
                continue
            if not all(x0 <= a <= x1 and y0 <= b <= y1 for a, b in pts):
                continue
            lay = e.dxf.layer
            for a, b in zip(pts, pts[1:]):
                if lay == "S-REIN.D" and abs(a[1] - b[1]) < 5 and abs(a[0] - b[0]) > 300:
                    bars.append({"bar": e.dxf.handle, "x0": round(min(a[0], b[0]), 1),
                                 "x1": round(max(a[0], b[0]), 1), "y": round(a[1], 1)})
                elif lay == "S-EXTL.D" and abs(a[0] - b[0]) < 5:
                    faces.add(round(a[0], 1))
            if lay == "S-LINE.SCH" and e.dxf.linetype == "CENTER":
                axes.add(round(pts[0][0], 1))
        axes = sorted(axes)
        faces = sorted(faces)
        ys = sorted({b["y"] for b in bars})
        bottom_y = min(ys) if ys else None
        for b in bars:
            b["straddles"] = [k for k, a in enumerate(axes) if 0 < k < len(axes) - 1 and   # interior supports only
                              b["x0"] + 50 < a < b["x1"] - 50]
            b["row"] = "BOTTOM" if b["y"] == bottom_y else "TOP"
        ends = [{"bar": b["bar"], "x": b["x0"]} for b in bars] + [{"bar": b["bar"], "x": b["x1"]} for b in bars]

        def support_of(xf):
            k = min(range(len(axes)), key=lambda i: abs(axes[i] - xf))
            return k, ("LEFT" if xf < axes[k] else "RIGHT")
        span_sym = {}
        for d in dims:
            if re.fullmatch(r"L[n]?\d?", d["text"]):
                ax = [a for a in axes if abs(a - d["p2"]) <= DIM_SNAP_UNITS or abs(a - d["p3"]) <= DIM_SNAP_UNITS]
                fc = [f for f in faces if abs(f - d["p2"]) <= DIM_SNAP_UNITS or abs(f - d["p3"]) <= DIM_SNAP_UNITS]
                lo, hi = sorted((d["p2"], d["p3"]))
                span = 1 + sum(1 for a in axes if a < (lo + hi) / 2) - 1
                basis = "AXIS_TO_AXIS" if len(ax) == 2 else ("FACE_TO_FACE" if len(fc) == 2 else "UNBOUND")
                span_sym[d["text"]] = {"span": span, "basis": basis, "handle": d["handle"]}
                d["role"] = "SPAN_SYMBOL"
                d["binding"] = {"state": "SOURCE_DERIVED_HIGH_CONFIDENCE" if basis != "UNBOUND" else "UNRESOLVED",
                                "basis": basis, "span": span}
        rules = []
        bmap = {b["bar"]: b for b in bars}
        for d in dims:
            if d.get("role"):
                continue
            r = BR.bind_dimension_rule(d, bar_ends=ends, faces=faces, axes=axes, tol_mm=DIM_SNAP_UNITS)
            m = re.fullmatch(r"([0-9.]+)\s*(L[n]?\d?)", d["text"])
            rule = {"dim": d["handle"], "text": d["text"], "bound": r["bound"], "bar": r["bar"],
                    "state": r["state"], "why": None}
            if r["bound"]:
                fx = next(h for k in ("p2", "p3") for h in r["hits"][k]["face"])
                k, side = support_of(fx)
                b = bmap[r["bar"]]
                rule.update(support=k, side=side, bar_row=b["row"], bar_straddles=b["straddles"])
                into = k if side == "LEFT" else k + 1     # the span the bar end lies in
                if m:
                    sym = m.group(2)
                    rule.update(kind="FACTOR", factor=float(m.group(1)), symbol=sym)
                    sd = span_sym.get(sym)
                    if sd is None:
                        rule.update(state="UNRESOLVED", why=f"'{sym}' names no span of this {hd['spans']}-span "
                                                            "typical")
                    elif sd["span"] != into:
                        rule.update(state="UNRESOLVED", why=f"'{sym}' is span {sd['span']} in the typical, but the "
                                                            f"bar end lies in span {into}")
                    else:
                        rule.update(basis=sd["basis"], span=into)
                elif _num_cm(d["text"]) is not None:
                    rule.update(kind="LENGTH", value_m=_num_cm(d["text"]), span=into)
                else:
                    rule.update(state="UNRESOLVED", why="unparsed dimension text")
            else:
                rule.update(why="a defpoint hits no bar end of the typical (the dimension is not bound)")
            rules.append(rule)
        hd.update(axes=axes, faces=faces, bars=bars, dims=dims, span_symbols=span_sym, rules=rules)
    return heads


def header_for(heads, frame_x, n_spans):
    hs = [h for h in heads if h["spans"] == n_spans and h["x"][0] - 3000 <= frame_x <= h["x"][1]]
    return hs[0] if hs else None


def frame_rules(hd, frame):
    """Rules a frame bar may use: a typical rule binds to a frame bar of the same topology (row, straddled
    supports); a support bar must also be drawn as the template (symmetric about its support) - an edited frame
    bar gets no typical rule."""
    out = {}
    if hd is None:
        return out
    for b in frame["bars"]:
        st = list(b["straddles_supports"])
        if b["role"] == "BOTTOM" and st:
            tb = [r for r in hd["rules"] if r.get("bar_row") == "BOTTOM" and r.get("bar_straddles") == st and
                  r.get("support") in st]
            ok = [r for r in tb if r["state"] in BR.FEEDS_S6 and r.get("kind") == "LENGTH"]
            if tb and len(ok) == len(tb) and len({r["value_m"] for r in ok}) == 1 and \
                    {r["support"] for r in ok} == set(st):
                out[b["handle"]] = {"bottom_extension": {"authority": "SOURCE_DERIVED_HIGH_CONFIDENCE",
                                                         "value_m": ok[0]["value_m"],
                                                         "rule_id": f"{hd['id']}:" + "+".join(r["dim"] for r in ok)}}
            else:
                why = "; ".join(f"{r['dim']} '{r['text']}': {r['why'] or r['state']}" for r in tb) or \
                    "no typical dimension bound to this bar topology"
                out[b["handle"]] = {"bottom_extension": {"authority": "UNRESOLVED", "why": why}}
        elif b["role"] == "SUPPORT_TOP" and len(st) == 1:
            k = st[0]
            sym = abs((k - b["u_start"]) - (b["u_end"] - k)) <= 0.02
            tb = [r for r in hd["rules"] if r.get("bar_row") == "TOP" and r.get("support") == k and
                  r.get("bar_straddles") == [k]]
            ok = [r for r in tb if r["state"] in BR.FEEDS_S6 and r.get("kind") == "FACTOR"]
            sides = {r["side"] for r in ok}
            if sym and sides == {"LEFT", "RIGHT"} and len({r["factor"] for r in ok}) == 1 and \
                    {r["basis"] for r in ok} == {"AXIS_TO_AXIS"}:
                out[b["handle"]] = {"support_bar_each_side_factor": {
                    "authority": "SOURCE_DERIVED_HIGH_CONFIDENCE", "value": ok[0]["factor"], "span_basis": "cc_m",
                    "rule_id": f"{hd['id']}:" + "+".join(r["dim"] for r in sorted(ok, key=lambda r: r["side"]))}}
            else:
                why = ("frame bar drawn asymmetric about its support "
                       f"(u {b['u_start']:.3f}-{b['u_end']:.3f}): the typical extent is not shown to apply"
                       if not sym else "; ".join(f"{r['dim']} '{r['text']}': {r['why'] or r['state']}" for r in tb)
                       or "no typical dimension bound at this support")
                out[b["handle"]] = {"support_bar_each_side_factor": {"authority": "UNRESOLVED", "why": why}}
    return out


# ============================================================================================ schedule column texts
def schedule_columns(msp, defs):
    """MIDDLE REINT. / REMARKS / '(STIR)' / ' t/m' / point-load texts of each CB frame; REMARKS icons of the SBT."""
    texts = []
    for e in msp.query("TEXT"):
        if e.dxf.layer == "S-TEXT.SCH":
            texts.append({"handle": e.dxf.handle, "text": e.dxf.text, "x": e.dxf.insert.x, "y": e.dxf.insert.y})
    heads = {k: sorted([t for t in texts if t["text"].strip() == k], key=lambda t: t["x"])
             for k in ("MIDDLE", "REMARKS")}
    cb = {}
    for d in defs.values():
        if d["element"] != "CONTINUOUS_BEAM":
            continue
        fx, fy = d["insert"]
        mid = min(heads["MIDDLE"], key=lambda t: (t["x"] < fx, abs(t["x"] - fx)))
        rem = min(heads["REMARKS"], key=lambda t: (t["x"] < mid["x"], abs(t["x"] - mid["x"])))
        band = [t for t in texts if fy - 200 <= t["y"] <= fy + 5100 and fx - 500 <= t["x"] <= rem["x"] + 2500]
        m_col = [t for t in band if mid["x"] - 800 <= t["x"] <= mid["x"] + 1000]
        r_col = [t for t in band if rem["x"] - 800 <= t["x"] <= rem["x"] + 2500]
        stir = [t for t in band if t["text"].strip() == "(STIR)"]
        tm = [t for t in band if t["text"].strip() == "t/m"]
        pl = [t for t in band if re.fullmatch(r"\s*\d+(\.\d+)?\s*", t["text"]) and t["y"] - fy > 4500 and
              t["x"] < mid["x"] - 1000]
        cb[d["type"]] = {"middle_header": mid["handle"], "remarks_header": rem["handle"],
                         "middle": sorted(m_col, key=lambda t: -t["y"]), "remarks": r_col, "stir": stir,
                         "tm_units": sorted(tm, key=lambda t: t["x"]), "point_load_texts": sorted(
                             pl, key=lambda t: t["x"])}
    # SBT REMARKS icons (blocks STR2 / str3) -> the schedule row whose band holds them
    sbt = [d for d in defs.values() if d["block"] == "SBT"]
    icons = {}
    for i in msp.query("INSERT"):
        if i.dxf.name not in ("STR2", "str3"):
            continue
        p = i.dxf.insert
        best = min(sbt, key=lambda d: abs((d["insert"][1] - 311) - p.y) + 0.001 * abs(d["insert"][0] - p.x))
        if abs((best["insert"][1] - 311) - p.y) <= 336 and 0 < p.x - best["insert"][0] < 15000:
            icons.setdefault(best["type"], []).append({"block": i.dxf.name, "handle": i.dxf.handle,
                                                       "row_insert": best["insert_handle"]})
    hdr = {t["text"].strip(): t["handle"] for t in texts if 105000 <= t["x"] <= 120000 and 17500 <= t["y"] <= 19500}
    return cb, icons, hdr


# ============================================================================================ openings
def opening_objects(src, msp):
    """S-OPENING outlines (lines joined at shared end points) and 'void' inserts, per sheet, local coordinates."""
    from ezdxf import bbox as EB
    out = []
    for sh in SHEETS:
        segs = [e for e in src.entities()[sh] if e.get("layer") == "S-OPENING"]
        pts = []
        for e in segs:
            if e["type"] == "LINE":
                pts.append((e["handle"], [tuple(e["a"]), tuple(e["b"])]))
            elif e["type"] == "ARC":
                c, r = e["c"], e["r"]
                a0, a1 = e["a0"], e["a1"]
                if abs(a0) < 7 and abs(a1) < 7:
                    a0, a1 = math.degrees(a0), math.degrees(a1)
                a1 = a1 + 360 if a1 < a0 else a1
                pts.append((e["handle"], [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / 12)),
                                           c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / 12)))
                                          for i in range(13)]))
        parent = list(range(len(pts)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                if any(math.dist(p, q) <= 5 for p in (pts[i][1][0], pts[i][1][-1]) for q in (pts[j][1][0],
                                                                                              pts[j][1][-1])):
                    parent[find(i)] = find(j)
        groups = defaultdict(list)
        for i in range(len(pts)):
            groups[find(i)].append(pts[i])
        for g in groups.values():
            allp = [p for _, ps in g for p in ps]
            out.append({"sheet": sh, "source": "S-OPENING", "handles": sorted(h for h, _ in g),
                        "points": allp, "segments": [ps for _, ps in g],
                        "bbox": (min(p[0] for p in allp), min(p[1] for p in allp),
                                                 max(p[0] for p in allp), max(p[1] for p in allp))})
    for i in msp.query('INSERT[name=="void"]'):
        b = EB.extents([i])
        cx, cy = (b.extmin.x + b.extmax.x) / 2, (b.extmin.y + b.extmax.y) / 2
        sh = src.sheet_of(cx, cy)
        if sh not in SHEETS:
            continue
        p0, p1 = src.local(sh, b.extmin.x, b.extmin.y), src.local(sh, b.extmax.x, b.extmax.y)
        ring = [p0, (p1[0], p0[1]), p1, (p0[0], p1[1]), p0]
        out.append({"sheet": sh, "source": "void INSERT", "handles": [i.dxf.handle], "points": ring[:4],
                    "segments": [ring], "bbox": (p0[0], p0[1], p1[0], p1[1])})
    out.sort(key=lambda o: (o["sheet"], o["source"], o["handles"]))
    for n, o in enumerate(out, 1):
        o["opening_id"] = f"OPN-{o['sheet']}-{n:03d}"
    return out


def opening_relation(o, x):
    """Only a CLOSED outline is an opening outline (open line work - radial dome lines, hatch strokes - is a symbol).
    Per beam band: INSIDE_BAND when the outline's area overlaps the band by more than 100 x OPENING_DEPTH_MM mm2,
    ON_FACE when its boundary runs along a band face (> 100 mm within OPENING_DEPTH_MM) without entering it."""
    from shapely.geometry import LineString, Polygon
    from shapely.ops import polygonize, unary_union
    lines_ = [LineString(sg) for sg in o["segments"] if len(sg) > 1]
    polys = list(polygonize(unary_union(lines_)))
    o["closed"] = bool(polys)
    rel = []
    bands = []
    for line in x["lines"]:
        (ux, uy), (nx, ny), off, hw = line["dir"], line["normal"], line["offset"], line["width_mm"] / 2
        pts = [(t * ux + (off + a_) * nx, t * uy + (off + a_) * ny)
               for t, a_ in ((line["t0"], -hw), (line["t1"], -hw), (line["t1"], hw), (line["t0"], hw))]
        bands.append((line["line_id"], Polygon(pts)))
    for a in x["arc_bands"]:
        c, r = a["centre"], a["r_mid_mm"]
        arc = LineString([(c[0] + r * math.cos(math.radians(a["start_deg"] + a["sweep_deg"] * i / 48)),
                           c[1] + r * math.sin(math.radians(a["start_deg"] + a["sweep_deg"] * i / 48)))
                          for i in range(49)])
        bands.append((a["band_id"], arc.buffer(a["width_mm"] / 2, cap_style=2)))
    if not polys:          # open line work: recorded (it may enter a band by an overshoot), never an opening
        for mid, band in bands:
            ln = sum(band.intersection(g).length for g in lines_)
            if ln > 50:
                rel.append({"member": mid, "relation": "LINEWORK_ENTERS_BAND", "length_mm": round(ln, 1)})
        return rel
    area = unary_union(polys)
    o["area_m2"] = round(area.area / 1e6, 3)
    for mid, band in bands:
        inter = area.intersection(band).area
        if inter > 100 * OPENING_DEPTH_MM:
            rel.append({"member": mid, "relation": "INSIDE_BAND", "overlap_mm2": round(inter, 1)})
        else:
            along = area.boundary.intersection(band.exterior.buffer(OPENING_DEPTH_MM)).length
            if along > 100:
                rel.append({"member": mid, "relation": "ON_FACE", "along_face_mm": round(along, 1)})
    return rel


# ============================================================================================ main build
def build(dxf=DEFAULT_DXF):
    s1_hashes = verify_inputs(dxf)
    rules, claims = rules_and_claims()
    B = S.build()
    src = B["src"]
    msp = src.msp
    CBG = R3.cb_graphics(dxf)
    defs = {d["type"]: d for d in B["defs"]["definitions"] if d["element"] in ("SIMPLE_BEAM", "CONTINUOUS_BEAM")}
    s1_rows = _j(S1 / "BEAM_OCCURRENCE_REGISTER.json")["rows"]
    s1_by_src = {r["source_id"]: r for r in s1_rows}
    s1_by_span = {(r["sheet"], r["member"], round(r["span_stations_mm"][0])): r for r in s1_rows
                  if r.get("sheet") and r.get("member") and r.get("span_stations_mm")}
    stair = stair_qualifiers()
    planted = planted_columns(B)
    heads = typical_headers(msp)
    cbcols, icons, sbt_hdr = schedule_columns(msp, defs)
    openings = opening_objects(src, msp)
    ctx = {"PROJECT_ID": "ALSENAN", "DRAWING_ID": "ST7757", "DRAWING_SHA": DRAWING_SHA,
           "ENGINE_COMMIT": f"{BASELINE}+code:{code_digest()[:16]}", "REGISTER_VERSION": REGISTER_VERSION,
           "CALCULATION_ROUND": "PRE_S6"}

    cover = rules["COVER_GENERAL_25MM"]
    side_note = rules["SIDE_BARS_NOTE_21"]
    side_threshold = 60.0 if "60" in str(side_note.get("scope")) else None

    # ------------------------------------------------------------------ binding + conservation, per sheet
    tag_rows, geo_rows, bind_rows = [], [], []
    tags_on = defaultdict(list)          # (sheet, key) -> [(handle, mark, decision)]
    decisions, fixed_points, sheet_geo = {}, {}, {}
    for sh in SHEETS:
        x = B["beams"][sh]
        shared = shared_faces(x["lines"])
        dec, passes = bind_sheet(x, defs, shared)
        fixed_points[sh] = passes
        sheet_geo[sh] = {"x": x, "shared": shared, "lines": {l["line_id"]: l for l in x["lines"]},
                         "arcs": {a["band_id"]: a for a in x["arc_bands"]}}
        s1b = x["binding"]
        for t in sorted(x["tags"], key=lambda t: _hkey(t["handle"])):
            r = dec[t["handle"]]
            decisions[(sh, t["handle"])] = r
            if r["member_id"] and r["_key"]:
                tags_on[(sh, r["_key"])].append((t["handle"], t["text"], r))
            for c in r["_cands"]:
                bind_rows.append({
                    "SHEET": sh, "TAG_HANDLE": t["handle"], "MARK": t["text"],
                    "TAG_X": _r(S._text_centre(t)[0], 1), "TAG_Y": _r(S._text_centre(t)[1], 1),
                    "TAG_ROTATION_DEG": _r(t.get("rotation") or 0.0, 2),
                    "S1_STATE": s1b.get(t["handle"], {}).get("state"), "S1_MEMBER": s1b.get(t["handle"], {}).get(
                        "member"), "DECISION": r["decision"], "BOUND_MEMBER": r["member_id"], "STAGE": r["stage"],
                    "WHY": r["why"], "CANDIDATE_MEMBER": c["member_id"], "CANDIDATE_KIND": c["kind"],
                    "IS_BOUND_MEMBER": c["member_id"] == r["member_id"],
                    "DISTANCE_MM": c["distance_mm"], "DISTANCE_LIMIT_MM": _r(c.get("distance_limit_mm") or 950.0, 1),
                    "ORIENTATION_DIFF_DEG": next(rr["orientation_diff_deg"] for rr in r["candidates"]
                                                 if rr["member_id"] == c["member_id"]),
                    "INSIDE_PHYSICAL_EXTENT": c["inside_physical_extent"], "ALONG_MM": c["_along"],
                    "SPAN": None if c["_key"][1] is None else f"{c['_key'][1]}-{c['_key'][2]}",
                    "SPAN_OTHER_MARKS": sorted(set(c["span_other_marks"]) - {t["text"]}),
                    "SAME_MARK_ON_SPAN": c["same_mark_on_span"], "SAME_MARK_ADJACENT_SPAN": c["same_mark_adjacent"],
                    "SUPPORTED_BOTH_ENDS": c["supported_both_ends"], "SHARED_FACE_WITH": c["_shared"],
                    **{k: v for k, v in next(rr["width"] for rr in r["candidates"]
                                             if rr["member_id"] == c["member_id"]).items()},
                    "DECISIVE_EXCLUSIONS": next(rr["decisive_exclusions"] for rr in r["candidates"]
                                                if rr["member_id"] == c["member_id"]),
                    "ROTATION_ONLY_ALTERNATIVE": c["member_id"] in r["rotation_only_alternatives"],
                    "FIXED_POINT_PASSES": passes})
            if not r["_cands"]:
                bind_rows.append({"SHEET": sh, "TAG_HANDLE": t["handle"], "MARK": t["text"],
                                  "DECISION": r["decision"], "WHY": r["why"], "FIXED_POINT_PASSES": passes})

    # tag terminals (one physical span at a time)
    tag_terminal, span_geo_terminal = {}, {}
    for (sh, key), lst in tags_on.items():
        res = BR.span_tag_terminals([{"handle": h, "mark": m, "decision": r["decision"],
                                      "width_state": r["width_state"], "why": r["why"]} for h, m, r in lst])
        for h, v in res["terminals"].items():
            why = v[1]
            if v[0] == "DUPLICATE_TAG":
                why = f"{why} ({obj_id(sh, key)})"
            elif v[0] == "BOUND_SOURCE_CONFLICT" and why and why.startswith("the span carries"):
                why = f"{obj_id(sh, key)} carries {sorted({m for _, m, _ in lst})}"
            tag_terminal[(sh, h)] = (v[0], why)
        span_geo_terminal[(sh, key)] = res["geometry"]
    for sh in SHEETS:
        x = B["beams"][sh]
        for t in sorted(x["tags"], key=lambda t: _hkey(t["handle"])):
            r = decisions[(sh, t["handle"])]
            term, why = tag_terminal.get((sh, t["handle"]), (r["decision"], r["why"]))
            if t["text"] not in defs:
                why = f"{why}; mark {t['text']} has no SBT / C-BEAM schedule row"
            sid = f"BEAMTAG:{sh}:{t['handle']}"
            s1r = s1_by_src.get(sid)
            tag_rows.append({"OBJECT_ID": f"TAG:{sh}:{t['handle']}", "OBJECT_KIND": "TAG", "SHEET": sh,
                             "FLOOR": FLOOR[sh], "MARK": t["text"], "FAMILY_BY_MARK": _family(t["text"]),
                             "TERMINAL": term, "BOUND_GEOMETRY": obj_id(sh, r["_key"]) if r["_key"] else None,
                             "WHY": why, "S1_SOURCE_ID": sid if s1r else None,
                             "S1_BINDING": s1r.get("binding") if s1r else None,
                             "S1_FAMILY": s1r.get("family") if s1r else None,
                             "STAIR_QUALIFIER": stair.get((sh, t["handle"])),
                             "DECISION_STAGE": r["stage"]})

    # geometry terminals
    for sh in SHEETS:
        g = sheet_geo[sh]
        x = g["x"]
        objs = []
        for lid in sorted(x["spans"]):
            for q in x["spans"][lid]:
                objs.append((span_key(lid, q), q, g["lines"][lid]))
        for a in x["arc_bands"]:
            objs.append(((a["band_id"], None, None), None, a))
        line_marks = defaultdict(set)
        for (sh2, key), lst in tags_on.items():
            if sh2 == sh:
                line_marks[key[0]] |= {m for _, m, _ in lst}
        for key, q, mem in objs:
            lst = tags_on.get((sh, key), [])
            marks = sorted({m for _, m, _ in lst})
            prim = [z for z in lst if tag_terminal.get((sh, z[0]), ("",))[0] != "DUPLICATE_TAG"]
            if not lst:
                term = "GEOMETRY_WITHOUT_TAG"
                others = sorted(line_marks.get(key[0], set()))
                why = ("no tag binds this span" + (f"; the member line carries {others} on other spans (continuity "
                                                   "candidate, never bound)" if others else ""))
            elif len(marks) > 1:
                term, why = span_geo_terminal[(sh, key)]
            else:
                term = span_geo_terminal[(sh, key)][0]
                why = "; ".join(f"{h} {m}: {tag_terminal[(sh, h)][1]}" for h, m, _ in prim)
            if key[1] is None:
                sid = f"MEMBER:{sh}:{key[0]}"
                length = mem["length_mm"] / 1000
                kind = "ARC_BAND"
            else:
                sid = f"MEMBER:{sh}:{key[0]}-{round(q['s0'])}"
                length = q["cc_mm"] / 1000
                kind = "MEMBER_SPAN"
            s1r = s1_by_src.get(sid) or (s1_by_span.get((sh, key[0], key[1])) if key[1] is not None else None)
            if s1r is None and lst:
                s1r = next((s1_by_src.get(f"BEAMTAG:{sh}:{h}") for h, _, _ in lst
                            if f"BEAMTAG:{sh}:{h}" in s1_by_src), None)
            geo_rows.append({"OBJECT_ID": obj_id(sh, key), "OBJECT_KIND": kind, "SHEET": sh, "FLOOR": FLOOR[sh],
                             "MARK": "|".join(marks) or None, "TERMINAL": term,
                             "BOUND_TAGS": [h for h, _, _ in lst], "WHY": why,
                             "LENGTH_M": _r(length), "CLEAR_M": _r(q["clear_mm"] / 1000) if q else None,
                             "DRAWN_WIDTH_MM": mem["width_mm"],
                             "START_SUPPORT": (q["start"].get("support_kind") or q["start"].get("kind")) if q else None,
                             "END_SUPPORT": (q["end"].get("support_kind") or q["end"].get("kind")) if q else None,
                             "SHARED_FACE_WITH": g["shared"].get(key[0], []) if q else [],
                             "S1_SOURCE_ID": s1r["source_id"] if s1r else None,
                             "S1_FAMILY": s1r.get("family") if s1r else None,
                             "S1_ROW_PRESENT": s1r is not None})
        for f in sorted(x["fragments"], key=lambda f: f["line_id"]):
            geo_rows.append({"OBJECT_ID": f"FRAGMENT:{sh}:{f['line_id']}", "OBJECT_KIND": "BAND_FRAGMENT",
                             "SHEET": sh, "FLOOR": FLOOR[sh], "TERMINAL": "NOT_BEAM",
                             "WHY": f"paired band {f['length_mm']:.0f} mm long x {f['width_mm']:.0f} mm: shorter than "
                                    "the 600 mm member minimum and no tag binds it (S1 excluded it as a fragment)",
                             "LENGTH_M": _r(f["length_mm"] / 1000), "DRAWN_WIDTH_MM": f["width_mm"],
                             "S1_ROW_PRESENT": False})
    rule_rows = []
    for r in s1_rows:
        if r["family"] in ("LINTEL", "LIFT_TIE"):
            rule_rows.append({"OBJECT_ID": r["source_id"], "OBJECT_KIND": "RULE_POPULATION", "SHEET": None,
                              "FLOOR": r["floor"], "TERMINAL": "OUT_OF_SCOPE_FAMILY", "S1_SOURCE_ID": r["source_id"],
                              "S1_FAMILY": r["family"], "S1_ROW_PRESENT": True,
                              "WHY": f"{r['family']}: no plan geometry on the roof-slab sheets "
                                     f"({'; '.join(r['issues'])}) "
                                     "- not a simple or continuous beam occurrence"})
    cons_rows = tag_rows + geo_rows + rule_rows
    conservation = BR.terminate([{"object_id": r["OBJECT_ID"], "kind": "TAG" if r["OBJECT_KIND"] == "TAG" else
                                  r["OBJECT_KIND"], "terminal": r["TERMINAL"]} for r in cons_rows])
    s1_super = [r for r in s1_rows if r.get("floor") in ("GF_ROOF", "1F_ROOF", "2F_ROOF", "GF", "ALL")]
    mapped = {r["S1_SOURCE_ID"] for r in cons_rows if r.get("S1_SOURCE_ID")}
    s1_unmapped = sorted(r["source_id"] for r in s1_super if r["source_id"] not in mapped)
    if not conservation["all_terminate_once"] or s1_unmapped:
        raise SystemExit(f"conservation failed: {conservation['duplicates'][:5]} "
                         f"{conservation['invalid_terminals'][:5]}"
                         f" S1 unmapped {s1_unmapped[:5]}")

    # ------------------------------------------------------------------ occurrences
    geo_by_id = {r["OBJECT_ID"]: r for r in geo_rows}
    planted_on = defaultdict(list)
    for pc in planted:
        g = sheet_geo[pc["sheet"]]
        for lid, q_list in g["x"]["spans"].items():
            line = g["lines"][lid]
            along, across = S._proj(line, pc["centre"])
            if abs(across) > line["width_mm"] / 2 + 5:
                continue
            for q in q_list:
                if q["start"].get("hi", q["s0"]) < along < q["end"].get("lo", q["s1"]):
                    planted_on[obj_id(pc["sheet"], span_key(lid, q))].append(pc["chain_id"])
    open_rel = {}
    for o in openings:
        o["relations"] = opening_relation(o, sheet_geo[o["sheet"]]["x"])
        for rel in o["relations"]:
            if rel["relation"] == "INSIDE_BAND":
                open_rel.setdefault((o["sheet"], rel["member"]), []).append(o["opening_id"])

    simple_occ, cb_tags = [], defaultdict(list)
    for r in geo_rows:
        if r["OBJECT_KIND"] not in ("MEMBER_SPAN", "ARC_BAND"):
            continue
        sh = r["SHEET"]
        key = _key_of(r["OBJECT_ID"])
        lst = tags_on.get((sh, key), [])
        marks = sorted({m for _, m, _ in lst})
        if any(_family(m) == "CONTINUOUS_BEAM" for m in marks):
            for h, m, dd in lst:
                if _family(m) == "CONTINUOUS_BEAM":
                    cb_tags[(sh, m)].append((h, key, dd))
            continue
        if not lst:
            continue
        simple_occ.append(r)

    # ------------------------------------------------------------------ CB occurrences + span sequence
    cb_occ = []
    for (sh, mark), lst in sorted(cb_tags.items()):
        g = sheet_geo[sh]
        by_line = defaultdict(list)
        for h, key, dd in lst:
            by_line[key[0]].append((h, key, dd))
        clusters, used = [], set()
        for lid in sorted(by_line):
            if lid in used:
                continue
            cl = [lid]
            used.add(lid)
            a = g["lines"].get(lid)
            for l2 in sorted(by_line):
                b = g["lines"].get(l2)
                if l2 in used or a is None or b is None:
                    continue
                if abs(a["dir"][0] * b["dir"][1] - a["dir"][1] * b["dir"][0]) < 0.02 and \
                        abs(a["offset"] - b["offset"]) < 150:
                    cl.append(l2)
                    used.add(l2)
            clusters.append(cl)
        for cl in clusters:
            items = [z for lid in cl for z in by_line[lid]]
            uniq = {}
            for h, key, dd in sorted(items, key=lambda z: _hkey(z[0])):
                uniq.setdefault(key, []).append(h)
            spans = []
            for key in sorted(uniq, key=lambda k: (k[1] if k[1] is not None else 0)):
                q = next(q for q in g["x"]["spans"][key[0]] if span_key(key[0], q) == key)
                gr = geo_by_id[obj_id(sh, key)]
                spans.append({"key": key, "q": q, "tags": uniq[key], "terminal": gr["TERMINAL"],
                              "cc_m": round(q["cc_mm"] / 1000, 3), "clear_m": round(q["clear_mm"] / 1000, 3),
                              "width_mm": gr["DRAWN_WIDTH_MM"]})
            d = defs.get(mark)
            sched = d["fields"]["spans_m"] if d else []
            seq = BR.span_sequence([{"cc_m": s["cc_m"], "clear_m": s["clear_m"]} for s in spans], sched)
            contiguous = all(abs(spans[i]["q"]["s1"] - spans[i + 1]["q"]["s0"]) < 1 and
                             spans[i]["key"][0] == spans[i + 1]["key"][0] for i in range(len(spans) - 1))
            if seq["orientation"] == "REVERSED":       # plan read right-to-left against the schedule frame
                spans = [dict(sp_, q=dict(sp_["q"], start=sp_["q"]["end"], end=sp_["q"]["start"]))
                         for sp_ in reversed(spans)]
            adj = []
            if seq["state"] == "SPAN_COUNT_CONFLICT" and spans:
                for lid in cl:
                    for q in g["x"]["spans"].get(lid, []):
                        k = span_key(lid, q)
                        if k in uniq:
                            continue
                        if any(abs(q["s1"] - s["q"]["s0"]) < 1 or abs(q["s0"] - s["q"]["s1"]) < 1 for s in spans):
                            adj.append({"object": obj_id(sh, k), "cc_m": round(q["cc_mm"] / 1000, 3),
                                        "clear_m": round(q["clear_mm"] / 1000, 3),
                                        "terminal": geo_by_id[obj_id(sh, k)]["TERMINAL"], "s0": q["s0"]})
            ext_state = None
            if adj and len(adj) + len(spans) == len(sched):
                ext = sorted([{"cc_m": s["cc_m"], "s0": s["q"]["s0"]} for s in spans] + adj, key=lambda z: z["s0"])
                ext_state = BR.span_sequence(ext, sched)["state"]
            occ_id = f"CBO-{sh}-{mark}-{cl[0]}"
            cb_occ.append({"id": occ_id, "sheet": sh, "mark": mark, "lines": cl, "spans": spans, "seq": seq,
                           "contiguous": contiguous, "adjacent_untagged": adj, "state_if_extended": ext_state,
                           "definition": d})
    cb_tag_handles = {(o["sheet"], h) for o in cb_occ for s in o["spans"] for h in s["tags"]}

    # ------------------------------------------------------------------ deliverable rows
    span_rows = []
    for o in cb_occ:
        d = o["definition"]
        sw = d["fields"]["B_cm"] * 10 if d else None
        for row in o["seq"]["rows"]:
            i = row["SPAN_INDEX"] - 1
            s = o["spans"][i] if i < len(o["spans"]) else None
            q = s["q"] if s else None
            w = BR.width_match(s["width_mm"] if s else None, sw)
            span_rows.append({
                "CB_OCCURRENCE_ID": o["id"], "MARK": o["mark"], "SHEET": o["sheet"], "SPAN_INDEX": row["SPAN_INDEX"],
                "PLAN_OBJECT_ID": obj_id(o["sheet"], s["key"]) if s else None,
                "START_SUPPORT": _support(q["start"]) if q else None, "END_SUPPORT": _support(q["end"]) if q else None,
                "PHYSICAL_LENGTH_CC_M": s["cc_m"] if s else None, "CLEAR_LENGTH_M": s["clear_m"] if s else None,
                "SUPPORT_FACE_TO_FACE_M": s["clear_m"] if s else None,
                "SCHEDULE_SPAN_M": row["SCHEDULE_SPAN_M"], "DELTA_CC_M": row["DELTA_CC_M"],
                "SPAN_STATE": row["SPAN_STATE"], "SEQUENCE_STATE": o["seq"]["state"],
                "ORIENTATION": o["seq"]["orientation"], "PLAN_POSITION": row.get("PLAN_POSITION"),
                "DELTA_CC_M_REVERSED": row.get("DELTA_CC_M_REVERSED"),
                "SPANS_CONTIGUOUS": o["contiguous"], "DRAWN_WIDTH_MM": w["DRAWN_WIDTH"],
                "SCHEDULE_WIDTH_MM": w["SCHEDULE_WIDTH"], "WIDTH_DELTA_MM": w["DELTA"],
                "WIDTH_MATCH_STATE": w["WIDTH_MATCH_STATE"],
                "BINDING_TERMINAL": s["terminal"] if s else None,
                "SOURCE_HANDLES": {"tags": s["tags"] if s else [], "bands": sheet_geo[o["sheet"]]["lines"][
                    s["key"][0]].get("bands") if s else [], "support_refs": [
                    _support_ref(q["start"]), _support_ref(q["end"])] if q else [],
                    "schedule_row": d["insert_handle"] if d else None},
                "ADJACENT_UNTAGGED_SPANS": o["adjacent_untagged"] if row["SPAN_INDEX"] == 1 else None,
                "STATE_IF_ADJACENT_INCLUDED": o["state_if_extended"] if row["SPAN_INDEX"] == 1 else None,
                "PLAN_TOTAL_CC_M": o["seq"]["plan_total_cc_m"], "SCHEDULE_TOTAL_M": o["seq"]["schedule_total_m"],
                "NEVER_SHARED": True, "NEVER_CAPPED": True})

    # 03 / 04 schedule semantics ------------------------------------------------------------
    sem_s, sem_c, tokens = [], [], []
    occ_count = Counter()
    for r in simple_occ:
        for m in (r["MARK"] or "").split("|"):
            occ_count[m] += 1
    for o in cb_occ:
        occ_count[o["mark"]] += 1
    for t, d in sorted(defs.items(), key=lambda kv: _natkey(kv[0])):
        if d["element"] != "SIMPLE_BEAM":
            continue
        f, raw = d["fields"], d["raw_attributes"]
        rem = f.get("remarks_side_bars")
        ic = icons.get(t, [])

        def sem(family, tags_, value, interp, auth, feeds, why, handles=None):
            sem_s.append({"TYPE": t, "SCHEDULE_ROW": d["insert_handle"], "PAGE": d.get("page"),
                          "PLAN_OCCURRENCES": occ_count.get(t, 0), "FIELD_FAMILY": family,
                          "RAW_ATTRIBUTE_TAGS": tags_, "RAW_VALUES": [raw.get(k) for k in tags_] if tags_ else None,
                          "PARSED": value, "INTERPRETATION": interp, "AUTHORITY": auth, "FEEDS_S6": feeds,
                          "SOURCE_HANDLES": handles or [d["insert_handle"]], "WHY": why})
        hdr = lambda *k: [sbt_hdr.get(x) for x in k if sbt_hdr.get(x)]  # noqa: E731
        sem("BOTTOM_MAIN", ["BOT-B", "BOT-D"], f.get("bottom"), "bottom longitudinal bars (count x diameter)",
            "SOURCE_EXPLICIT", True, "SBT header 'BOTTOM BARS'", [d["insert_handle"]] + hdr("B O T T O M"))
        sem("TOP_MAIN", ["TOP-B", "TOP-D"], f.get("top"), "top longitudinal bars (count x diameter)",
            "SOURCE_EXPLICIT", True, "SBT header 'TOP BARS'", [d["insert_handle"]] + hdr("T O P"))
        sem("TOP_SUPPORT_EXTRA", [], None, "NOT_SCHEDULED", "SOURCE_EXPLICIT", False,
            "the SBT has no support / extra top field; nothing is inferred")
        sem("BOTTOM_EXTRA", [], None, "NOT_SCHEDULED", "SOURCE_EXPLICIT", False, "the SBT has no extra bottom field")
        sem("MID", [], None, "NOT_SCHEDULED", "SOURCE_EXPLICIT", False, "MID bars exist only in the C-BEAM schedules")
        sem("HANGER", [], None, "ABSENT_AS_SEPARATE_COMPONENT", "SOURCE_EXPLICIT", False,
            "no hanger field or detail; the TOP BARS field exists, its hanger role is not asserted")
        if rem:
            tok = {k: rem.get(k) for k in ("raw", "normalised", "count", "dia_mm", "spacing_cm", "text_handle")}
            sem("SIDE_REBAR", ["REMARKS"], tok, "side steel printed in REMARKS; per-face / vertical-spacing semantics "
                "not stated", "UNRESOLVED", False, rem.get("interpretation"), [rem.get("text_handle")])
        else:
            sem("SIDE_REBAR", ["REMARKS"], None, "NONE_PRINTED", "SOURCE_EXPLICIT", False,
                f"REMARKS empty; depth {f.get('H_cm')} cm")
        sem("STIRRUP", ["STI-B", "D"], f.get("stirrups_per_m"), "stirrups per metre x diameter", "SOURCE_EXPLICIT",
            True, "SBT header 'STIRRUPS/m'", [d["insert_handle"]] + hdr("STIRRUPS/m"))
        if ic:
            sem("OTHER", ["REMARKS icon"], [i["block"] for i in ic], "REMARKS icon block (outer + inner closed "
                "rectangles): reads like a multi-link stirrup set; the drawing does not say", "PROJECT_PATTERN_ONLY",
                False, "named block STR2 / str3 with no legend", [i["handle"] for i in ic])
        else:
            sem("OTHER", [], None, "NONE", "SOURCE_EXPLICIT", False, "no other field in this row")
        for fam, (tb, tdia), val in (("BOTTOM_MAIN", ("BOT-B", "BOT-D"), f.get("bottom")),
                                     ("TOP_MAIN", ("TOP-B", "TOP-D"), f.get("top")),
                                     ("STIRRUP", ("STI-B", "D"), f.get("stirrups_per_m"))):
            tokens.append(_token("SBT", d["insert_handle"], f"{t}:{tb}+{tdia}", f"{raw.get(tb)}|{raw.get(tdia)}",
                                 SG.bar_from_cells(raw.get(tb), raw.get(tdia)), fam, t))
        if rem:
            tokens.append(_token("SBT REMARKS", rem.get("text_handle"), f"{t}:REMARKS", rem.get("raw"),
                                 SG.parse_bar(rem.get("raw")), "SIDE_REBAR", t, ambiguous=True))
        for i in ic:
            tokens.append({"TOKEN_ID": f"ICON:{i['handle']}", "SOURCE": "SBT REMARKS icon", "HANDLE": i["handle"],
                           "RAW": i["block"], "NORMALISED": i["block"], "GRAMMAR": "SYMBOL", "TYPE": t,
                           "FIELD_FAMILY": "STIRRUP_TOPOLOGY", "TERMINAL": "BLOCKED_SEMANTICS",
                           "WHY": "unlabelled icon block; legs per set not printed"})
        for k in ("W", "H"):
            tokens.append({"TOKEN_ID": f"SBT:{d['insert_handle']}:{k}", "SOURCE": "SBT", "HANDLE": d["insert_handle"],
                           "RAW": raw.get(k), "NORMALISED": raw.get(k), "GRAMMAR": "SECTION_DIMENSION_CM", "TYPE": t,
                           "FIELD_FAMILY": "SECTION", "TERMINAL": "NOT_REBAR", "WHY": "section dimension (cm)"})

    for t, d in sorted(defs.items(), key=lambda kv: _natkey(kv[0])):
        if d["element"] != "CONTINUOUS_BEAM":
            continue
        f, raw = d["fields"], d["raw_attributes"]
        fr = CBG["frames"].get(t)
        col = cbcols.get(t, {})
        hd = header_for(heads, d["insert"][0], len(f["spans_m"]))
        n = len(f["spans_m"])

        def semc(family, span, tags_, value, interp, auth, why, handles=None, feeds=None):
            sem_c.append({"TYPE": t, "SCHEDULE_ROW": d["insert_handle"], "BLOCK": d["block"], "PAGE": d.get("page"),
                          "PLAN_OCCURRENCES": occ_count.get(t, 0), "SPAN_COUNT": n, "FIELD_FAMILY": family,
                          "SPAN_OR_SUPPORT": span, "RAW_ATTRIBUTE_TAGS": tags_,
                          "RAW_VALUES": [raw.get(k) for k in tags_] if tags_ else None, "PARSED": value,
                          "INTERPRETATION": interp, "AUTHORITY": auth,
                          "FEEDS_S6": (auth in BR.FEEDS_S6) if feeds is None else feeds,
                          "TYPICAL_DETAIL": hd["id"] if hd else None, "SOURCE_HANDLES": handles or [d["insert_handle"]],
                          "WHY": why})
        for k in ("W", "H"):
            semc(k, None, [k], raw.get(k), "section dimension (cm)", "SOURCE_EXPLICIT", "attribute in the B / H column",
                 feeds=True)
        for i in range(n):
            semc("SPAN", f"span {i + 1}", [f"L{i + 1}-M"], f["spans_m"][i],
                 "schedule span length (m), sequence = frame order left to right", "SOURCE_EXPLICIT",
                 "attribute above the span; the frame draws spans equal (N.T.S.)", feeds=False)
            tm = raw.get(f"T/M-{i + 1}")
            semc("T/M", f"span {i + 1}", [f"T/M-{i + 1}"], tm, "design line load in t/m - NOT reinforcement",
                 "SOURCE_EXPLICIT", "' t/m' unit text printed beside the value on the load line of the frame",
                 [d["insert_handle"]] + [u["handle"] for u in col.get("tm_units", [])], feeds=False)
            bot = f["bottom_bars_per_span"][i] if i < len(f["bottom_bars_per_span"]) else None
            semc("BOTTOM", f"span {i + 1}", [f"BOT{i + 1}-B", f"BOT{i + 1}-D"], bot,
                 "bottom bars of the span (count x diameter); topology from the frame graphic", "SOURCE_EXPLICIT",
                 "attribute printed on the frame's bottom bar")
            st = f["stirrups_per_span"][i] if i < len(f["stirrups_per_span"]) else None
            zone = [z["handle"] for z in (fr or {}).get("stirrup_zone_dims", []) if z["u"] == [float(i), float(i + 1)]]
            semc("STIRRUP", f"span {i + 1}", [f"STR{i + 1}-B", f"STR{i + 1}-D"], st,
                 "stirrups per metre x diameter over the span", "SOURCE_EXPLICIT",
                 "'(STIR)' label + a '/m' dimension spanning the span", [d["insert_handle"]] + zone +
                 [s["handle"] for s in col.get("stir", [])])
            tokens.append(_token("C-BEAM", d["insert_handle"], f"{t}:BOT{i + 1}", f"{raw.get(f'BOT{i + 1}-B')}|"
                                 f"{raw.get(f'BOT{i + 1}-D')}", bot, "BOTTOM", t))
            tokens.append(_token("C-BEAM", d["insert_handle"], f"{t}:STR{i + 1}", f"{raw.get(f'STR{i + 1}-B')}|"
                                 f"{raw.get(f'STR{i + 1}-D')}", st, "STIRRUP", t))
            tokens.append({"TOKEN_ID": f"C-BEAM:{d['insert_handle']}:T/M-{i + 1}", "SOURCE": "C-BEAM",
                           "HANDLE": d["insert_handle"], "RAW": tm, "NORMALISED": f"{tm} t/m",
                           "GRAMMAR": "DESIGN_LOAD_T_PER_M", "TYPE": t, "FIELD_FAMILY": "T/M",
                           "TERMINAL": "NOT_REBAR", "WHY": "design line load (' t/m' printed)"})
            tokens.append({"TOKEN_ID": f"C-BEAM:{d['insert_handle']}:L{i + 1}-M", "SOURCE": "C-BEAM",
                           "HANDLE": d["insert_handle"], "RAW": raw.get(f"L{i + 1}-M"),
                           "NORMALISED": f"{raw.get(f'L{i + 1}-M')} m", "GRAMMAR": "SPAN_LENGTH_M", "TYPE": t,
                           "FIELD_FAMILY": "SPAN", "TERMINAL": "NOT_REBAR", "WHY": "span length"})
        # support (MID) bars, from the frame graphic
        for b in sorted((fr or {}).get("bars", []), key=lambda b: (b["role"], b["u_start"])):
            lab = b.get("label") or {}
            st = b["straddles_supports"]
            if b["role"] == "SUPPORT_TOP":
                rul = frame_rules(hd, fr).get(b["handle"], {}).get("support_bar_each_side_factor", {})
                val = {"count": lab.get("count") or None, "dia_mm": lab.get("dia") or None,
                       "extent": f"{rul.get('value')} x Ln each side from the support face (Ln axis-to-axis)"
                       if rul.get("authority") in BR.FEEDS_S6 else None}
                semc("MID", f"support {st}", [lab.get("tag")] if lab.get("tag") else [], val,
                     "support top bars over the interior support (frame label MID / MIDn / callout)",
                     "SOURCE_DERIVED_HIGH_CONFIDENCE" if lab.get("count") and rul.get("authority") in BR.FEEDS_S6
                     else "UNRESOLVED",
                     (f"extent rule {rul.get('rule_id')}" if rul.get("authority") in BR.FEEDS_S6 else
                      f"extent: {rul.get('why')}") + ("" if lab.get("count") else f"; label {b['binding']}"),
                     [b["handle"]])
                tokens.append(_token("C-BEAM frame", b["handle"], f"{t}:{b['handle']}", f"{lab.get('count')}|"
                                     f"{lab.get('dia')}", SG.bar_from_cells(lab.get("count") or None,
                                                                            lab.get("dia") or None),
                                     "MID", t, empty=b["binding"] == "EMPTY_SCHEDULE_CELL"))
            elif b["role"] in ("CONTINUOUS_TOP", "SPAN_TOP"):
                semc("TOP", f"u {b['u_start']:.3f}-{b['u_end']:.3f}", [], {"count": lab.get("count") or None,
                                                                          "dia_mm": lab.get("dia") or None},
                     f"top bar of the frame top row ({b['role']}); count / diameter from the callout fragments "
                     "directly above it; interior end drawn N.T.S.", "SOURCE_DERIVED_HIGH_CONFIDENCE"
                     if b["binding"] == "ONE_TO_ONE_PRINTED" else "UNRESOLVED",
                     "count / diameter bound one-to-one; EXTENT UNRESOLVED (no bound typical rule for this bar)",
                     [b["handle"]] + list(lab.get("handles") or []), feeds=False)
                tokens.append(_token("C-BEAM frame callout", b["handle"], f"{t}:{b['handle']}",
                                     f"{lab.get('count')}|{lab.get('dia')}", SG.bar_from_cells(
                                         lab.get("count") or None, lab.get("dia") or None), "TOP", t))
        semc("HANGER", None, [], None, "the typical elevation draws a second top row lapping the support bars "
             "(unlabelled); the frames draw one top bar per span", "UNRESOLVED",
             "no count / diameter / extent is printed for a separate hanger", feeds=False)
        mid_txt = col.get("middle", [])
        if mid_txt:
            raw_s = " | ".join(m["text"] for m in mid_txt)
            p = [SG.parse_bar(m["text"]) for m in mid_txt]
            bar = next((x for x in p if x.get("count")), {})
            spc = next((int(_num_cm(m["text"]) * 100) for m in mid_txt if _num_cm(m["text"])), None)
            semc("SIDE_REBAR", None, ["MIDDLE REINT."], {"raw": raw_s, "count": bar.get("count"),
                                                         "dia_mm": bar.get("dia_mm"), "spacing_cm": spc},
                 "side steel in the MIDDLE REINT. column (split texts); faces / vertical arrangement not stated",
                 "UNRESOLVED", "split fragments in one cell", [m["handle"] for m in mid_txt], feeds=False)
            for m in mid_txt:
                pb = SG.parse_bar(m["text"])
                tokens.append({"TOKEN_ID": f"TEXT:{m['handle']}", "SOURCE": "C-BEAM MIDDLE REINT.",
                               "HANDLE": m["handle"], "RAW": m["text"], "NORMALISED": pb["normalised"],
                               "GRAMMAR": pb["grammar"], "TYPE": t, "FIELD_FAMILY": "SIDE_REBAR",
                               "TERMINAL": "PARSED_AMBIGUOUS",
                               "WHY": "fragment of a split MIDDLE REINT. cell; per-face / spacing semantics "
                                      "unresolved"})
        else:
            semc("SIDE_REBAR", None, ["MIDDLE REINT."], None, "NONE_PRINTED", "SOURCE_EXPLICIT",
                 f"MIDDLE REINT. empty; H = {f['H_cm']} cm", feeds=False)
        semc("OTHER", None, [], [x["text"] for x in col.get("remarks", [])] or None,
             "REMARKS column content" if col.get("remarks") else "REMARKS empty", "SOURCE_EXPLICIT",
             "REMARKS cell", [x["handle"] for x in col.get("remarks", [])] or None, feeds=False)
        for pl in col.get("point_load_texts", []):
            tokens.append({"TOKEN_ID": f"TEXT:{pl['handle']}", "SOURCE": "C-BEAM load line", "HANDLE": pl["handle"],
                           "RAW": pl["text"], "NORMALISED": pl["text"].strip(), "GRAMMAR": "NUMBER_NO_UNIT",
                           "TYPE": t, "FIELD_FAMILY": "POINT_LOAD_CANDIDATE", "TERMINAL": "NOT_REBAR",
                           "WHY": "number beside a load arrow on the load line; no unit printed"})

    # duplicate tokens (same raw value printed twice at the same place)
    seen_tok = {}
    for tk in tokens:
        k = (tk["SOURCE"], tk["HANDLE"], tk["TOKEN_ID"])
        if k in seen_tok:
            tk["TERMINAL"] = "DUPLICATE_SOURCE"
        seen_tok[k] = tk

    # ------------------------------------------------------------------ readiness per occurrence
    ready_rows, run_rows, side_rows, prov = [], [], [], []

    simple_list = []
    for r in sorted(simple_occ, key=lambda r: r["OBJECT_ID"]):
        sh = r["SHEET"]
        key = _key_of(r["OBJECT_ID"])
        lst = [z for z in tags_on[(sh, key)] if tag_terminal[(sh, z[0])][0] != "DUPLICATE_TAG"]
        mark = r["MARK"]
        h0 = lst[0][0]
        oid = f"BM-{FLOOR[sh]}-{mark}-{key[0]}-{h0}"
        simple_list.append(oid)
        d = defs.get(mark)
        g = sheet_geo[sh]
        q = None if key[1] is None else next(q for q in g["x"]["spans"][key[0]] if span_key(key[0], q) == key)
        w = BR.width_match(r["DRAWN_WIDTH_MM"], d["fields"]["B_cm"] * 10 if d and d["fields"].get("B_cm") else None)
        stair_h = next((stair.get((sh, h)) for h, _, _ in lst if stair.get((sh, h))), None)
        cands = [f"{d['block']}:{d['insert_handle']}"] if d else []
        undefined = []
        if stair_h:
            cands.append("P16-STAIR-BEAM")
            undefined.append(f"'WITH STAIR' qualifier {stair_h}: the p.16 stair-beam detail is an unread candidate")
        if r["OBJECT_ID"] in planted_on:
            cands.append("P15-PLANTED-COLUMN")
            undefined.append(f"carries planted column {planted_on[r['OBJECT_ID']]}: the p.15 detail is a candidate "
                             "(AI transcription, not machine-read)")
        term = r["TERMINAL"]
        if not d:
            app, app_why = "NO_APPLICABLE_DETAIL", f"mark {mark} has no SBT row"
        elif term == "BOUND_SOURCE_CONFLICT":
            app, app_why = "SOURCE_CONFLICT", r["WHY"]
        elif undefined:
            app, app_why = "BLOCKED", "; ".join(undefined) + " (an undefined candidate blocks the component)"
        else:
            app, app_why = "OK", f"SBT row {d['insert_handle']} by mark {mark}; width {w['WIDTH_MATCH_STATE']}"
        provisional = term == "BOUND_CANDIDATE"
        geo_state = "UNRESOLVED"
        if q is not None:
            ks = (_support(q["start"]), _support(q["end"]))
            if q["clear_mm"] <= 0 or q["clear_mm"] > q["cc_mm"] + 1:
                geo_state = "BAR_RUN_GEOMETRY_CONFLICT"
            elif all(k not in (None, "FREE_END") for k in ks):
                geo_state = "CONSISTENT"
        ftf = _r(q["clear_mm"] / 1000) if q else None
        ext_rule = {"authority": "SOURCE_DERIVED_HIGH_CONFIDENCE", "rule_id": "SBT_LONGITUDINAL_SUPPORT_TO_SUPPORT",
                    "why": "SBT 'BOTTOM BARS' / 'TOP BARS' of a simple beam: no curtailment field or detail anywhere "
                           "in the source, so each listed bar spans at least the clear span between support faces"}
        geo_handles = sorted(set(g["lines"][key[0]].get("bands") or [])) if key[1] is not None else \
            sorted(g["arcs"][key[0]].get("edges") or [])
        sup_ids = [_support_ref(q["start"]), _support_ref(q["end"])] if q else []
        base = {"OCCURRENCE_ID": oid, "SUBFAMILY": "SIMPLE_BEAM", "SHEET": sh, "FLOOR": FLOOR[sh], "MARK": mark,
                "GEOMETRY_OBJECT": r["OBJECT_ID"], "BINDING_TERMINAL": term, "DETAIL_ID": cands[0] if cands else None,
                "DETAIL_CANDIDATES": cands, "APPLICABILITY_STATE": app,
                "WHY_APPLICABLE": app_why if app == "OK" else None,
                "WIDTH_MATCH_STATE": w["WIDTH_MATCH_STATE"], "DRAWN_WIDTH_MM": w["DRAWN_WIDTH"],
                "SCHEDULE_WIDTH_MM": w["SCHEDULE_WIDTH"]}
        statuses = []
        dev_why = ("development / anchorage into the supports: no beam-source rule (note 9 70Ø/40Ø is for starter "
                   "bars only; the slab 0.25L / 0.30L rules are never borrowed)")
        for fam in LONG:
            fld = (d or {}).get("fields", {}).get("bottom" if fam == "BOTTOM_MAIN" else "top") or {}
            run = BR.simple_bar_run(family_id=f"{oid}:{fam}", face_to_face_m=ftf,
                                    start_support=sup_ids[0] if sup_ids else None,
                                    end_support=sup_ids[1] if sup_ids else None,
                                    geometry_state=geo_state, extent_rule=ext_rule)
            stt = BR.component_status(applicability=app, count_dia_known=bool(fld.get("count") and fld.get("dia_mm")),
                                      run_state=run["STRAIGHT_RUN_STATE"], additions_blocked=True,
                                      provisional=provisional)
            statuses.append(stt)
            why_b = None if stt in BR.RELEASABLE else (app_why if app != "OK" else (
                "binding is a candidate" if provisional else f"straight run {run['STRAIGHT_RUN_STATE']} "
                f"({'curved member: support faces at the arc ends not established' if q is None else geo_state})"))
            run_rows.append({"BAR_RUN_ID": run["BAR_RUN_ID"], "OCCURRENCE_ID": oid, "SUBFAMILY": "SIMPLE_BEAM",
                             "MARK": mark, "ROLE": fam, "COUNT": fld.get("count"), "DIA_MM": fld.get("dia_mm"),
                             "START_LOCATION": run["START_LOCATION"], "INTERMEDIATE_SUPPORTS": [],
                             "END_LOCATION": run["END_LOCATION"], "SPANS_CROSSED": [1],
                             "STRAIGHT_SEGMENTS": run["STRAIGHT_SEGMENTS"], "STRAIGHT_RUN_M": run["STRAIGHT_RUN_M"],
                             "STRAIGHT_RUN_STATE": run["STRAIGHT_RUN_STATE"],
                             "SUPPORT_1": sup_ids[0] if sup_ids else None, "SUPPORT_2": sup_ids[1] if sup_ids else None,
                             "DEVELOPMENT_1": "BLOCKED_UNQUANTIFIED", "DEVELOPMENT_2": "BLOCKED_UNQUANTIFIED",
                             "HOOK_1": "BLOCKED_UNQUANTIFIED", "HOOK_2": "BLOCKED_UNQUANTIFIED",
                             "COMPLETE_BAR_STATE": "LOWER_BOUND" if run["STRAIGHT_RUN_STATE"] == "VERIFIED"
                             else "BLOCKED_UNQUANTIFIED", "SOURCE_EXTENT": ext_rule, "MISSING": [dev_why],
                             "STATUS": stt})
            ready_rows.append(dict(base, COMPONENT_FAMILY=fam, BAR_RUN_ID=run["BAR_RUN_ID"], COUNT=fld.get("count"),
                                   DIA_MM=fld.get("dia_mm"), STRAIGHT_RUN_M=run["STRAIGHT_RUN_M"],
                                   RUN_STATE=run["STRAIGHT_RUN_STATE"], STATUS=stt, WHY_BLOCKED=why_b,
                                   RULE_ID=ext_rule["rule_id"], AUTHORITY=ext_rule["authority"],
                                   DEVELOPMENT="BLOCKED_UNQUANTIFIED", HOOKS="BLOCKED_UNQUANTIFIED"))
            if stt in BR.RELEASABLE:
                prov.append(BR.provenance_template(
                    context=ctx, occurrence_id=oid, mark=mark, subfamily="SIMPLE_BEAM",
                    source_handles=[h for h, _, _ in lst], schedule_handles=[d["insert_handle"]],
                    geometry_handles=geo_handles, support_ids=sup_ids, detail_id=cands[0],
                    rule_id=ext_rule["rule_id"], convention_id="BAR_STRAIGHT_RUN_FACE_TO_FACE_LOWER_BOUND",
                    authority=ext_rule["authority"], release_state=stt, bar_run_id=run["BAR_RUN_ID"]))
        for fam, why in (("TOP_SUPPORT_EXTRA", "not scheduled in the SBT"),
                         ("BOTTOM_EXTRA", "not scheduled in the SBT")):
            ready_rows.append(dict(base, COMPONENT_FAMILY=fam, STATUS="NOT_APPLICABLE", WHY_BLOCKED=None,
                                   WHY_APPLICABLE=why))
        hg = BR.hanger_readiness(scheduled=None, detailed=None)
        ready_rows.append(dict(base, COMPONENT_FAMILY="HANGER", STATUS="NOT_APPLICABLE", WHY_BLOCKED=None,
                               WHY_APPLICABLE=f"{hg['state']}: {hg['why']} (TOP BARS listed; no hanger role asserted)"))
        # side rebar
        rem = (d or {}).get("fields", {}).get("remarks_side_bars")
        tok = {"raw": rem.get("raw"), "count": rem.get("count"), "dia_mm": rem.get("dia_mm"),
               "spacing_cm": rem.get("spacing_cm"), "text_handle": rem.get("text_handle"), "column": "REMARKS"} \
            if rem else None
        sr = BR.side_rebar_readiness(token=tok, depth_cm=(d or {}).get("fields", {}).get("H_cm"),
                                     note_threshold_cm=side_threshold, note_authority=side_note["source_state"])
        ready_rows.append(dict(base, COMPONENT_FAMILY="SIDE_REBAR", COUNT=tok and tok["count"],
                               DIA_MM=tok and tok["dia_mm"], STATUS=sr["state"],
                               WHY_BLOCKED=sr.get("why") if sr["state"] != "NOT_APPLICABLE" else None,
                               WHY_APPLICABLE=sr.get("why") if sr["state"] == "NOT_APPLICABLE" else None,
                               RULE_ID=side_note["rule_id"]))
        statuses.append(sr["state"])
        # stirrups
        stf = (d or {}).get("fields", {}).get("stirrups_per_m") or {}
        legs = {"state": "UNRESOLVED", "evidence": [i["block"] for i in icons.get(mark, [])] or "NOT_STATED",
                "why": "REMARKS icon block without a legend" if icons.get(mark) else "legs not printed"}
        sre = BR.stirrup_readiness(dia_mm=stf.get("dia_mm"), rate_per_m=stf.get("count"),
                                   rate_state="SOURCE_EXPLICIT" if stf else "UNRESOLVED",
                                   distribution_m=ftf if geo_state == "CONSISTENT" and app in ("OK",) else None,
                                   width_state=w["WIDTH_MATCH_STATE"],
                                   depth_known=bool((d or {}).get("fields", {}).get("H_cm")),
                                   cover_known=cover["source_state"] == "CROSS_VERIFIED_SOURCE", topology=legs,
                                   hooks_state="BLOCKED_UNQUANTIFIED",
                                   end_zone={"state": "NOT_STATED", "why": "no end-zone densification printed"},
                                   first_last={"state": "NOT_STATED", "why": "first / last stirrup position not "
                                                                            "printed; no +1 end bar"})
        cnt_state = "READY_LOWER_BOUND" if sre["COUNT"]["state"] == "LOWER_BOUND" and not provisional else \
            ("PROVISIONAL_ONLY" if sre["COUNT"]["state"] == "LOWER_BOUND" else
             ("SOURCE_CONFLICT" if app == "SOURCE_CONFLICT" else "BLOCKED_COMPONENT"))
        ready_rows.append(dict(base, COMPONENT_FAMILY="STIRRUP_COUNT", COUNT=sre["COUNT"]["value"],
                               DIA_MM=stf.get("dia_mm"), STATUS=cnt_state, STIRRUP_DETAIL=sre,
                               WHY_BLOCKED=None if cnt_state in BR.RELEASABLE else (
                                   app_why if app != "OK" else sre["COUNT"].get("why") or "binding is a candidate"),
                               RULE_ID="STIRRUPS_PER_M_X_CLEAR_RUN_CEIL", AUTHORITY="SOURCE_EXPLICIT"))
        ready_rows.append(dict(base, COMPONENT_FAMILY="STIRRUP_MASS", DIA_MM=stf.get("dia_mm"),
                               STATUS="BLOCKED_COMPONENT", STIRRUP_DETAIL=sre,
                               WHY_BLOCKED="; ".join(sre["MASS"]["missing"]) or "section path not established"))
        ready_rows.append(dict(base, COMPONENT_FAMILY="DEVELOPMENT_ANCHORAGE", STATUS="BLOCKED_COMPONENT",
                               WHY_BLOCKED=dev_why))
        ready_rows.append(dict(base, COMPONENT_FAMILY="HOOKS", STATUS="BLOCKED_COMPONENT",
                               WHY_BLOCKED=f"{rules['HOOKS_AND_BENDS']['source_state']}: no project hook source"))
        _opening_rows(ready_rows, base, open_rel.get((sh, key[0]), []))
        if r["OBJECT_ID"] in planted_on:
            ready_rows.append(dict(base, COMPONENT_FAMILY="PLANTED_COLUMN_EXTRA", STATUS="BLOCKED_COMPONENT",
                                   WHY_BLOCKED=f"carries planted column {planted_on[r['OBJECT_ID']]} (p.15 detail "
                                               "candidate, not machine-read)"))
        if stair_h:
            ready_rows.append(dict(base, COMPONENT_FAMILY="STAIR_EXTRA", STATUS="BLOCKED_COMPONENT",
                                   WHY_BLOCKED=f"'WITH STAIR' qualifier {stair_h}: p.16 stair-beam detail unread"))
        for rr in ready_rows:
            if rr["OCCURRENCE_ID"] == oid:
                rr["OCCURRENCE_STATUS"] = BR.occurrence_status([s for s in statuses if s])

    # CB occurrences
    for o in cb_occ:
        sh, mark, d = o["sheet"], o["mark"], o["definition"]
        fr = CBG["frames"].get(mark)
        hd = header_for(heads, d["insert"][0], len(d["fields"]["spans_m"])) if d else None
        frules = frame_rules(hd, fr) if fr else {}
        terms = [s["terminal"] for s in o["spans"]]
        sw = d["fields"]["B_cm"] * 10 if d else None
        widths = [BR.width_match(s["width_mm"], sw)["WIDTH_MATCH_STATE"] for s in o["spans"]]
        reasons = []
        if not d or not fr:
            app = "NO_APPLICABLE_DETAIL"
            reasons.append("no C-BEAM schedule row / frame for the mark")
        elif o["seq"]["state"] == "SPAN_COUNT_CONFLICT" or not o["contiguous"]:
            app = "BLOCKED"
            reasons.append(f"{len(o['spans'])} bound spans vs {len(d['fields']['spans_m'])} schedule spans"
                           if o["seq"]["state"] == "SPAN_COUNT_CONFLICT" else "bound spans are not contiguous")
        elif "BOUND_SOURCE_CONFLICT" in terms or o["seq"]["state"] == "SPAN_LENGTH_SOURCE_CONFLICT":
            app = "SOURCE_CONFLICT"
            if "BOUND_SOURCE_CONFLICT" in terms:
                reasons.append("a span is BOUND_SOURCE_CONFLICT (" + "; ".join(
                    geo_by_id[obj_id(sh, s["key"])]["WHY"] for s in o["spans"]
                    if s["terminal"] == "BOUND_SOURCE_CONFLICT") + ")")
            if o["seq"]["state"] == "SPAN_LENGTH_SOURCE_CONFLICT":
                reasons.append("plan c/c " + str([s["cc_m"] for s in o["spans"]]) + " vs schedule " +
                               str(d["fields"]["spans_m"]) + " (both kept)")
        else:
            app = "OK"
        provisional = "BOUND_CANDIDATE" in terms
        if provisional:
            reasons.append("a span binding is a candidate")
        cands = ([f"{d['block']}:{d['insert_handle']}"] if d else []) + ([hd["id"]] if hd else [])
        undefined = [obj_id(sh, s["key"]) for s in o["spans"] if obj_id(sh, s["key"]) in planted_on]
        if undefined and app == "OK":
            app = "BLOCKED"
            reasons.append(f"spans {undefined} carry planted columns (p.15 candidate detail undefined)")
            cands.append("P15-PLANTED-COLUMN")
        base = {"OCCURRENCE_ID": o["id"], "SUBFAMILY": "CONTINUOUS_BEAM", "SHEET": sh, "FLOOR": FLOOR[sh],
                "MARK": mark, "GEOMETRY_OBJECT": [obj_id(sh, s["key"]) for s in o["spans"]],
                "BINDING_TERMINAL": terms, "DETAIL_ID": cands[0] if cands else None, "DETAIL_CANDIDATES": cands,
                "APPLICABILITY_STATE": app, "WHY_APPLICABLE": (f"C-BEAM row {d['insert_handle']} + typical "
                                                               f"{hd['id'] if hd else None}; spans "
                                                               f"{o['seq']['state']}") if app == "OK" else None,
                "WIDTH_MATCH_STATE": widths, "SCHEDULE_WIDTH_MM": sw,
                "DRAWN_WIDTH_MM": [s["width_mm"] for s in o["spans"]]}
        app_why = "; ".join(reasons) or None
        statuses = []
        ambiguous = o["seq"]["orientation"] == "AMBIGUOUS"
        spans_in, sups = _cb_inputs(o["spans"], d)
        runs, invariant_roles = [], set()
        if fr and len(fr["support_lines"]) - 1 == len(o["spans"]):
            fbars = [dict(b, straddles=b["straddles_supports"], label=_int_label(b.get("label"))) for b in fr["bars"]]
            runs = BR.cb_bar_runs(occurrence_id=o["id"], frame_bars=fbars, spans=spans_in, supports=sups,
                                  rules={"by_bar": frules})
            if ambiguous:
                # both reading directions match the schedule: a bar-run family releases only when it is identical
                # under both span-to-schedule mappings (candidate invariance), never by choosing one
                m_in, m_sup = _cb_inputs(_mirror(o["spans"]), d)
                runs_r = BR.cb_bar_runs(occurrence_id=o["id"], frame_bars=fbars, spans=m_in, supports=m_sup,
                                        rules={"by_bar": frules})
                for role in {r_["ROLE"] for r_ in runs}:
                    sig = [sorted((r_["COUNT"], r_["DIA_MM"], r_["STRAIGHT_RUN_M"], r_["STRAIGHT_RUN_STATE"])
                                  for r_ in rs if r_["ROLE"] == role) for rs in (runs, runs_r)]
                    if BR.candidate_invariant({"FORWARD": repr(sig[0]), "REVERSED": repr(sig[1])})["state"] == \
                            "INVARIANT":
                        invariant_roles.add(role)
                reasons.append("both reading directions match the schedule (mapping undecided); released only "
                               f"where candidate-invariant: {sorted(invariant_roles) or 'none'}")
                app_why = "; ".join(reasons)
        elif fr:
            reasons.append(f"frame has {len(fr['support_lines']) - 1} spans, plan has {len(o['spans'])}: no bar run")
            app_why = "; ".join(reasons)
        geo_handles = sorted({b for s in o["spans"] for b in (sheet_geo[sh]["lines"][s["key"][0]].get("bands") or [])})
        for run in runs:
            role = {"BOTTOM": "BOTTOM", "SUPPORT_TOP": "MID_SUPPORT_TOP", "CONTINUOUS_TOP": "TOP",
                    "SPAN_TOP": "TOP"}[run["ROLE"]]
            add_blocked = bool(run["MISSING"]) or run["ROLE"] == "BOTTOM"
            r_app = app if app in ("OK", "SOURCE_CONFLICT", "NO_APPLICABLE_DETAIL") else "BLOCKED"
            if ambiguous and run["ROLE"] not in invariant_roles and r_app == "OK":
                r_app = "BLOCKED"
            stt = BR.component_status(applicability=r_app, count_dia_known=bool(run["COUNT"] and run["DIA_MM"]),
                                      run_state=run["STRAIGHT_RUN_STATE"], additions_blocked=add_blocked,
                                      provisional=provisional)
            statuses.append(stt)
            rid = [sg.get("rule_id") for sg in run["STRAIGHT_SEGMENTS"] if sg.get("rule_id")]
            k_in = run["INTERMEDIATE_SUPPORTS"]
            run_rows.append({"BAR_RUN_ID": run["BAR_RUN_ID"], "OCCURRENCE_ID": o["id"],
                             "SUBFAMILY": "CONTINUOUS_BEAM", "MARK": mark, "ROLE": role, "FRAME_ROLE": run["ROLE"],
                             "COUNT": run["COUNT"], "DIA_MM": run["DIA_MM"], "LABEL": run["LABEL"],
                             "START_LOCATION": run["START_LOCATION"], "INTERMEDIATE_SUPPORTS": k_in,
                             "END_LOCATION": run["END_LOCATION"], "SPANS_CROSSED": run["SPANS_CROSSED"],
                             "STRAIGHT_SEGMENTS": run["STRAIGHT_SEGMENTS"], "STRAIGHT_RUN_M": run["STRAIGHT_RUN_M"],
                             "STRAIGHT_RUN_STATE": run["STRAIGHT_RUN_STATE"],
                             "SUPPORT_1": run["START_LOCATION"], "SUPPORT_2": run["END_LOCATION"],
                             "DEVELOPMENT_1": "BLOCKED_UNQUANTIFIED" if run["START_LOCATION"]["at_support"] else
                             "NOT_APPLICABLE", "DEVELOPMENT_2": "BLOCKED_UNQUANTIFIED"
                             if run["END_LOCATION"]["at_support"] else "NOT_APPLICABLE",
                             "HOOK_1": "BLOCKED_UNQUANTIFIED" if run["LEGS"] and run["START_LOCATION"]["at_support"]
                             else "NOT_DRAWN", "HOOK_2": "BLOCKED_UNQUANTIFIED" if run["LEGS"] and
                             run["END_LOCATION"]["at_support"] else "NOT_DRAWN",
                             "COMPLETE_BAR_STATE": ("VERIFIED" if run["STRAIGHT_RUN_STATE"] == "VERIFIED" and
                                                    not run["MISSING"] else "LOWER_BOUND"
                                                    if run["STRAIGHT_RUN_STATE"] in ("VERIFIED", "LOWER_BOUND")
                                                    else "BLOCKED_UNQUANTIFIED"),
                             "SOURCE_EXTENT": {"frame_handle": run["SOURCE_HANDLE"], "rules": rid,
                                               "typical": hd["id"] if hd else None},
                             "MISSING": run["MISSING"], "STATUS": stt,
                             "SPAN_MAPPING": ("CANDIDATE_INVARIANT" if run["ROLE"] in invariant_roles else
                                              "UNDECIDED_DIFFERENT") if ambiguous else o["seq"]["orientation"]})
            ready_rows.append(dict(base, COMPONENT_FAMILY=role, BAR_RUN_ID=run["BAR_RUN_ID"], COUNT=run["COUNT"],
                                   DIA_MM=run["DIA_MM"], STRAIGHT_RUN_M=run["STRAIGHT_RUN_M"],
                                   RUN_STATE=run["STRAIGHT_RUN_STATE"], STATUS=stt,
                                   WHY_BLOCKED=None if stt in BR.RELEASABLE else (
                                       app_why if r_app != "OK" or provisional else "; ".join(run["MISSING"])),
                                   RULE_ID=rid or None, AUTHORITY="SOURCE_DERIVED_HIGH_CONFIDENCE" if rid else None,
                                   DEVELOPMENT=("BLOCKED_UNQUANTIFIED" if run["START_LOCATION"]["at_support"] or
                                                run["END_LOCATION"]["at_support"] else "NOT_APPLICABLE"),
                                   HOOKS="BLOCKED_UNQUANTIFIED" if run["LEGS"] else "NOT_DRAWN"))
            if stt in BR.RELEASABLE:
                prov.append(BR.provenance_template(
                    context=ctx, occurrence_id=o["id"], mark=mark, subfamily="CONTINUOUS_BEAM",
                    source_handles=[h for s in o["spans"] for h in s["tags"]] + [run["SOURCE_HANDLE"]],
                    schedule_handles=[d["insert_handle"]], geometry_handles=geo_handles,
                    support_ids=[x_["ref"] for x_ in sups], detail_id=cands[0], rule_id="+".join(rid) or
                    "FRAME_TOPOLOGY", convention_id="CB_BAR_RUN_FACE_TO_FACE_PLUS_BOUND_TYPICAL",
                    authority="SOURCE_DERIVED_HIGH_CONFIDENCE", release_state=stt, bar_run_id=run["BAR_RUN_ID"]))
        if not runs:
            ready_rows.append(dict(base, COMPONENT_FAMILY="LONGITUDINAL", STATUS="BLOCKED_COMPONENT"
                                   if app != "SOURCE_CONFLICT" else "SOURCE_CONFLICT", WHY_BLOCKED=app_why))
            statuses.append("BLOCKED_COMPONENT")
        hg = BR.hanger_readiness(scheduled=None, detailed={"count": None, "dia_mm": None, "handle": hd and hd["id"]})
        ready_rows.append(dict(base, COMPONENT_FAMILY="HANGER", STATUS="BLOCKED_COMPONENT",
                               WHY_BLOCKED=f"{hg['state']}: the typical draws an unlabelled second top row; the frames "
                                           "draw one top bar per span - hanger count / diameter / extent not printed"))
        col = cbcols.get(mark, {})
        mid_txt = col.get("middle", [])
        tok = None
        if mid_txt:
            bar = next((SG.parse_bar(m["text"]) for m in mid_txt if SG.parse_bar(m["text"]).get("count")), {})
            spc = next((int(_num_cm(m["text"]) * 100) for m in mid_txt if _num_cm(m["text"])), None)
            tok = {"raw": " | ".join(m["text"] for m in mid_txt), "count": bar.get("count"),
                   "dia_mm": bar.get("dia_mm"), "spacing_cm": spc, "text_handle": [m["handle"] for m in mid_txt],
                   "column": "MIDDLE REINT."}
        sr = BR.side_rebar_readiness(token=tok, depth_cm=d["fields"]["H_cm"] if d else None,
                                     note_threshold_cm=side_threshold, note_authority=side_note["source_state"])
        ready_rows.append(dict(base, COMPONENT_FAMILY="SIDE_REBAR", COUNT=tok and tok["count"],
                               DIA_MM=tok and tok["dia_mm"], STATUS=sr["state"],
                               WHY_BLOCKED=sr.get("why") if sr["state"] != "NOT_APPLICABLE" else None,
                               WHY_APPLICABLE=sr.get("why") if sr["state"] == "NOT_APPLICABLE" else None,
                               RULE_ID=side_note["rule_id"]))
        statuses.append(sr["state"])
        st_inv = True
        if ambiguous and d:
            sps = d["fields"]["stirrups_per_span"]
            fw = sorted((repr(sps[i]), o["spans"][i]["clear_m"]) for i in range(len(o["spans"])))
            rv = sorted((repr(sps[i]), o["spans"][len(o["spans"]) - 1 - i]["clear_m"]) for i in range(len(o["spans"])))
            st_inv = BR.candidate_invariant({"FORWARD": repr(fw), "REVERSED": repr(rv)})["state"] == "INVARIANT"
        for i, s in enumerate(o["spans"]):
            stf = d["fields"]["stirrups_per_span"][i] if d and i < len(d["fields"]["stirrups_per_span"]) else {}
            wst = widths[i]
            sre = BR.stirrup_readiness(
                dia_mm=stf.get("dia_mm"), rate_per_m=stf.get("count"),
                rate_state="SOURCE_EXPLICIT" if stf else "UNRESOLVED",
                distribution_m=s["clear_m"] if app == "OK" and st_inv and
                _support(s["q"]["start"]) not in (None, "FREE_END")
                and _support(s["q"]["end"]) not in (None, "FREE_END") else None, width_state=wst,
                depth_known=bool(d and d["fields"].get("H_cm")),
                cover_known=cover["source_state"] == "CROSS_VERIFIED_SOURCE",
                topology={"state": "UNRESOLVED", "evidence": "NOT_STATED", "why": "legs not printed"},
                hooks_state="BLOCKED_UNQUANTIFIED",
                end_zone={"state": "NOT_STATED", "why": "one '/m' zone dimension spans the whole span"},
                first_last={"state": "NOT_STATED", "why": "first / last stirrup position not printed; no +1"})
            cst = "READY_LOWER_BOUND" if sre["COUNT"]["state"] == "LOWER_BOUND" and not provisional else (
                "PROVISIONAL_ONLY" if sre["COUNT"]["state"] == "LOWER_BOUND" else
                "SOURCE_CONFLICT" if app == "SOURCE_CONFLICT" else "BLOCKED_COMPONENT")
            ready_rows.append(dict(base, COMPONENT_FAMILY="STIRRUP_COUNT", SPAN_INDEX=i + 1,
                                   COUNT=sre["COUNT"]["value"], DIA_MM=stf.get("dia_mm"), STATUS=cst,
                                   STIRRUP_DETAIL=sre, RULE_ID="STIRRUPS_PER_M_X_CLEAR_RUN_CEIL",
                                   AUTHORITY="SOURCE_EXPLICIT",
                                   WHY_BLOCKED=None if cst in BR.RELEASABLE else (
                                       app_why if app != "OK" or not st_inv or provisional
                                       else sre["COUNT"].get("why"))))
            ready_rows.append(dict(base, COMPONENT_FAMILY="STIRRUP_MASS", SPAN_INDEX=i + 1, DIA_MM=stf.get("dia_mm"),
                                   STATUS="BLOCKED_COMPONENT", STIRRUP_DETAIL=sre,
                                   WHY_BLOCKED="; ".join(sre["MASS"]["missing"])))
        ready_rows.append(dict(base, COMPONENT_FAMILY="DEVELOPMENT_ANCHORAGE", STATUS="BLOCKED_COMPONENT",
                               WHY_BLOCKED="end-support anchorage of bottom / top bars: no beam-source rule (note 9 is "
                                           "for starter bars only; slab rules are never borrowed)"))
        ready_rows.append(dict(base, COMPONENT_FAMILY="HOOKS", STATUS="BLOCKED_COMPONENT",
                               WHY_BLOCKED="end legs drawn N.T.S. without a dimension; no project hook source"))
        opn = sorted({x_ for s in o["spans"] for x_ in open_rel.get((sh, s["key"][0]), [])})
        _opening_rows(ready_rows, base, opn)
        for rr in ready_rows:
            if rr["OCCURRENCE_ID"] == o["id"]:
                rr["OCCURRENCE_STATUS"] = BR.occurrence_status([s for s in statuses if s])

    # untagged geometry + unbound tags
    untagged = []
    for r in geo_rows:
        if r["TERMINAL"] != "GEOMETRY_WITHOUT_TAG":
            continue
        untagged.append(r["OBJECT_ID"])
        ready_rows.append({"OCCURRENCE_ID": r["OBJECT_ID"], "SUBFAMILY": "UNTAGGED_GEOMETRY", "SHEET": r["SHEET"],
                           "FLOOR": r["FLOOR"], "GEOMETRY_OBJECT": r["OBJECT_ID"], "BINDING_TERMINAL": r["TERMINAL"],
                           "COMPONENT_FAMILY": "ALL", "STATUS": "NO_APPLICABLE_DETAIL", "DETAIL_CANDIDATES": [],
                           "APPLICABILITY_STATE": "NO_APPLICABLE_DETAIL",
                           "WHY_BLOCKED": r["WHY"] + (f" (S1 family {r['S1_FAMILY']})" if r.get("S1_FAMILY") else ""),
                           "OCCURRENCE_STATUS": "BLOCKED"})
    for r in tag_rows:
        if r["TERMINAL"] in ("BLOCKED_BINDING", "TAG_WITHOUT_GEOMETRY"):
            ready_rows.append({"OCCURRENCE_ID": r["OBJECT_ID"], "SUBFAMILY": r["FAMILY_BY_MARK"], "SHEET": r["SHEET"],
                               "FLOOR": r["FLOOR"], "MARK": r["MARK"], "BINDING_TERMINAL": r["TERMINAL"],
                               "COMPONENT_FAMILY": "ALL", "STATUS": "BLOCKED_COMPONENT",
                               "APPLICABILITY_STATE": "BLOCKED", "WHY_BLOCKED": r["WHY"],
                               "OCCURRENCE_STATUS": "BLOCKED"})
    for rr in ready_rows:
        rr.setdefault("WHY_BLOCKED", None)
        if rr["STATUS"] in BR.RELEASABLE:
            rr["WHY_BLOCKED"] = None
        rr["ELEMENT_FAMILY"] = "BEAM"
    if any(r["STATUS"] not in BR.STATUSES for r in ready_rows):
        raise SystemExit("unknown status")

    # 07 side rebar per type
    for t, d in sorted(defs.items(), key=lambda kv: _natkey(kv[0])):
        f = d["fields"]
        if d["element"] == "SIMPLE_BEAM":
            rem = f.get("remarks_side_bars")
            tok = {"raw": rem.get("raw"), "count": rem.get("count"), "dia_mm": rem.get("dia_mm"),
                   "spacing_cm": rem.get("spacing_cm"), "text_handle": rem.get("text_handle"),
                   "column": "REMARKS"} if rem else None
        else:
            mid_txt = cbcols.get(t, {}).get("middle", [])
            tok = None
            if mid_txt:
                bar = next((SG.parse_bar(m["text"]) for m in mid_txt if SG.parse_bar(m["text"]).get("count")), {})
                tok = {"raw": " | ".join(m["text"] for m in mid_txt), "count": bar.get("count"),
                       "dia_mm": bar.get("dia_mm"), "spacing_cm": next((int(_num_cm(m["text"]) * 100)
                                                                         for m in mid_txt if _num_cm(m["text"])), None),
                       "text_handle": [m["handle"] for m in mid_txt], "column": "MIDDLE REINT."}
        sr = BR.side_rebar_readiness(token=tok, depth_cm=f.get("H_cm"), note_threshold_cm=side_threshold,
                                     note_authority=side_note["source_state"])
        side_rows.append({"TYPE": t, "ELEMENT": d["element"], "SCHEDULE_ROW": d["insert_handle"],
                          "PLAN_OCCURRENCES": occ_count.get(t, 0), "DEPTH_CM": f.get("H_cm"),
                          "WIDTH_CM": f.get("B_cm"), "COLUMN": tok["column"] if tok else None,
                          "TOKEN_RAW": tok["raw"] if tok else None,
                          "TOKEN_HANDLES": tok["text_handle"] if tok else None,
                          "COUNT": tok["count"] if tok else None, "DIA_MM": tok["dia_mm"] if tok else None,
                          "SPACING_CM": tok["spacing_cm"] if tok else None,
                          "NOTE_THRESHOLD_CM": side_threshold, "NOTE_ID": side_note["claim_id"],
                          "NOTE_AUTHORITY": side_note["source_state"], "APPLICABILITY": sr["applicability"],
                          "FACES": sr.get("faces"), "VERTICAL_ARRANGEMENT": sr.get("vertical_arrangement"),
                          "BAR_LENGTH": sr.get("bar_length"), "END_TREATMENT": sr.get("end_treatment"),
                          "COUNT_SEMANTICS": sr.get("count_semantics"), "STATE": sr["state"], "WHY": sr.get("why")})

    # 08 openings
    open_rows = []
    for o in openings:
        ins = [r for r in o["relations"] if r["relation"] == "INSIDE_BAND"]
        onf = [r for r in o["relations"] if r["relation"] in ("ON_FACE", "LINEWORK_ENTERS_BAND")]
        stt = "CANDIDATE" if ins else "NOT_APPLICABLE"
        kind = "CLOSED_OUTLINE" if o.get("closed") else "OPEN_LINEWORK"
        open_rows.append({"OPENING_ID": o["opening_id"], "SHEET": o["sheet"], "SOURCE": o["source"],
                          "SOURCE_HANDLES": o["handles"], "BBOX_MM": [round(v, 1) for v in o["bbox"]],
                          "SIZE_MM": [round(o["bbox"][2] - o["bbox"][0], 1), round(o["bbox"][3] - o["bbox"][1], 1)],
                          "OUTLINE_KIND": kind, "AREA_M2": o.get("area_m2"),
                          "INSIDE_BEAM_BANDS": ins, "ON_BEAM_FACES_OR_LINEWORK": onf, "OPENING_STATE": stt,
                          "TRIGGERS": ["OPENING_EXTRA_TOP", "OPENING_EXTRA_BOTTOM", "OPENING_EXTRA_SIDE",
                                       "STIRRUP_EXTRA"] if ins else [],
                          "WHY": ("a plan outline reaches inside a beam band: a physical beam opening is a CANDIDATE "
                                  "only (the plan outline is a slab opening symbol; the p.16 'opening in beam' detail "
                                  "is an unread candidate)") if ins else
                          ("slab opening along a beam face: no opening through a beam" if onf and
                           kind == "CLOSED_OUTLINE" else "slab opening clear of every beam band"
                           if kind == "CLOSED_OUTLINE" else
                           "open S-OPENING line work (no closed outline: diagonals / radials / sides closing on beam "
                           "faces) - a slab-opening symbol, not an outline through a beam" +
                           (f"; enters {[r['member'] for r in onf]} only as line work" if onf else ""))})

    # ------------------------------------------------------------------ conservation csv rows + summary
    def counts(sub):
        occ = {}
        for r in ready_rows:
            if r["SUBFAMILY"] == sub:
                occ[r["OCCURRENCE_ID"]] = r["OCCURRENCE_STATUS"]
        return dict(Counter(occ.values())), len(occ)
    s_counts, s_n = counts("SIMPLE_BEAM")
    c_counts, c_n = counts("CONTINUOUS_BEAM")
    comp = defaultdict(Counter)
    for r in ready_rows:
        comp[(r["SUBFAMILY"], r["COMPONENT_FAMILY"])][r["STATUS"]] += 1
    width_conf = sorted({(r["SHEET"], r["MARK"]) for r in ready_rows
                         if r["SUBFAMILY"] == "SIMPLE_BEAM" and r.get("WIDTH_MATCH_STATE") == "SOURCE_CONFLICT"} |
                        {(r["SHEET"], r["MARK"]) for r in ready_rows if r["SUBFAMILY"] == "CONTINUOUS_BEAM" and
                         "SOURCE_CONFLICT" in (r.get("WIDTH_MATCH_STATE") or [])})
    for p in prov:
        if not BR.provenance_ready(p):
            raise SystemExit(f"provenance template incomplete: {p}")
    summary = {
        "policy": BR.policy_record(), "baseline_commit": BASELINE, "drawing_sha256": DRAWING_SHA,
        "s1_frozen_registers": s1_hashes, "no_kg": True, "context": ctx,
        "binding_fixed_point_passes": fixed_points,
        "tags": dict(Counter(r["TERMINAL"] for r in tag_rows)), "tag_count": len(tag_rows),
        "geometry": {k: dict(v) for k, v in _grp(geo_rows, "OBJECT_KIND", "TERMINAL").items()},
        "conservation": conservation, "s1_rows_mapped": len(s1_super), "s1_rows_unmapped": s1_unmapped,
        "geometry_not_in_s1": sorted(r["OBJECT_ID"] for r in geo_rows if not r.get("S1_ROW_PRESENT") and
                                     r["OBJECT_KIND"] != "BAND_FRAGMENT"),
        "s1_binding_changes": sorted({(r["TAG_HANDLE"], r["S1_STATE"], r["S1_MEMBER"], r["DECISION"],
                                       r["BOUND_MEMBER"]) for r in bind_rows
                                      if r.get("S1_STATE") != "BOUND" or r.get("S1_MEMBER") != r.get("BOUND_MEMBER")}),
        "simple_occurrences": s_n, "simple_occurrence_status": s_counts,
        "cb_occurrences": c_n, "cb_occurrence_status": c_counts,
        "cb_sequence_states": {o["id"]: o["seq"]["state"] for o in cb_occ},
        "untagged_geometry": len(untagged),
        "unbound_tags": sorted(r["OBJECT_ID"] for r in tag_rows if r["TERMINAL"] in ("BLOCKED_BINDING",
                                                                                       "TAG_WITHOUT_GEOMETRY")),
        "candidate_tags": sorted(r["OBJECT_ID"] for r in tag_rows if r["TERMINAL"] == "BOUND_CANDIDATE"),
        "conflict_tags": sorted(r["OBJECT_ID"] for r in tag_rows if r["TERMINAL"] == "BOUND_SOURCE_CONFLICT"),
        "duplicate_tags": sorted(r["OBJECT_ID"] for r in tag_rows if r["TERMINAL"] == "DUPLICATE_TAG"),
        "width_conflicts": [list(w) for w in width_conf],
        "component_status": {f"{a}|{b}": dict(v) for (a, b), v in sorted(comp.items())},
        "typical_rules": [{"header": h["id"], "spans": h["spans"], "span_symbols": h["span_symbols"],
                           "rules": h["rules"]} for h in heads],
        "planted_column_spans": dict(planted_on), "openings": dict(Counter(r["OPENING_STATE"] for r in open_rows)),
        "provenance_templates": len(prov), "cb_tag_handles": len(cb_tag_handles)}

    cons_fields = ["OBJECT_ID", "OBJECT_KIND", "SHEET", "FLOOR", "MARK", "FAMILY_BY_MARK", "TERMINAL",
                   "BOUND_GEOMETRY", "BOUND_TAGS", "WHY", "LENGTH_M", "CLEAR_M", "DRAWN_WIDTH_MM", "START_SUPPORT",
                   "END_SUPPORT", "SHARED_FACE_WITH", "STAIR_QUALIFIER", "DECISION_STAGE", "S1_SOURCE_ID",
                   "S1_BINDING", "S1_FAMILY", "S1_ROW_PRESENT"]
    _csv("01_BEAM_OCCURRENCE_CONSERVATION.csv", cons_rows, cons_fields)
    _csv("02_BEAM_BINDING_READINESS.csv", bind_rows,
         ["SHEET", "TAG_HANDLE", "MARK", "TAG_X", "TAG_Y", "TAG_ROTATION_DEG", "S1_STATE", "S1_MEMBER", "DECISION",
          "BOUND_MEMBER", "STAGE", "WHY", "CANDIDATE_MEMBER", "CANDIDATE_KIND", "IS_BOUND_MEMBER", "DISTANCE_MM",
          "DISTANCE_LIMIT_MM", "ORIENTATION_DIFF_DEG", "INSIDE_PHYSICAL_EXTENT", "ALONG_MM", "SPAN",
          "SPAN_OTHER_MARKS", "SAME_MARK_ON_SPAN", "SAME_MARK_ADJACENT_SPAN", "SUPPORTED_BOTH_ENDS",
          "SHARED_FACE_WITH", "DRAWN_WIDTH", "SCHEDULE_WIDTH", "DELTA", "TOLERANCE", "WIDTH_MATCH_STATE",
          "DECISIVE_EXCLUSIONS", "ROTATION_ONLY_ALTERNATIVE", "FIXED_POINT_PASSES"])
    _csv("03_SIMPLE_BEAM_SCHEDULE_SEMANTICS.csv", sem_s,
         ["TYPE", "SCHEDULE_ROW", "PAGE", "PLAN_OCCURRENCES", "FIELD_FAMILY", "RAW_ATTRIBUTE_TAGS", "RAW_VALUES",
          "PARSED", "INTERPRETATION", "AUTHORITY", "FEEDS_S6", "SOURCE_HANDLES", "WHY"])
    _csv("04_CONTINUOUS_BEAM_SCHEDULE_SEMANTICS.csv", sem_c,
         ["TYPE", "SCHEDULE_ROW", "BLOCK", "PAGE", "PLAN_OCCURRENCES", "SPAN_COUNT", "FIELD_FAMILY",
          "SPAN_OR_SUPPORT", "RAW_ATTRIBUTE_TAGS", "RAW_VALUES", "PARSED", "INTERPRETATION", "AUTHORITY", "FEEDS_S6",
          "TYPICAL_DETAIL", "SOURCE_HANDLES", "WHY"])
    _csv("05_CB_SPAN_SEQUENCE.csv", span_rows,
         ["CB_OCCURRENCE_ID", "MARK", "SHEET", "SPAN_INDEX", "PLAN_OBJECT_ID", "START_SUPPORT", "END_SUPPORT",
          "PHYSICAL_LENGTH_CC_M", "CLEAR_LENGTH_M", "SUPPORT_FACE_TO_FACE_M", "SCHEDULE_SPAN_M", "DELTA_CC_M",
          "SPAN_STATE", "SEQUENCE_STATE", "ORIENTATION", "PLAN_POSITION", "DELTA_CC_M_REVERSED", "SPANS_CONTIGUOUS",
          "DRAWN_WIDTH_MM", "SCHEDULE_WIDTH_MM",
          "WIDTH_DELTA_MM", "WIDTH_MATCH_STATE", "BINDING_TERMINAL", "SOURCE_HANDLES", "ADJACENT_UNTAGGED_SPANS",
          "STATE_IF_ADJACENT_INCLUDED", "PLAN_TOTAL_CC_M", "SCHEDULE_TOTAL_M", "NEVER_SHARED", "NEVER_CAPPED"])
    _csv("06_BEAM_BAR_RUN_READINESS.csv", run_rows,
         ["BAR_RUN_ID", "OCCURRENCE_ID", "SUBFAMILY", "MARK", "ROLE", "FRAME_ROLE", "COUNT", "DIA_MM", "LABEL",
          "START_LOCATION", "INTERMEDIATE_SUPPORTS", "END_LOCATION", "SPANS_CROSSED", "STRAIGHT_SEGMENTS",
          "STRAIGHT_RUN_M", "STRAIGHT_RUN_STATE", "SUPPORT_1", "SUPPORT_2", "DEVELOPMENT_1", "DEVELOPMENT_2",
          "HOOK_1", "HOOK_2", "COMPLETE_BAR_STATE", "SOURCE_EXTENT", "MISSING", "STATUS", "SPAN_MAPPING"])
    _csv("07_BEAM_SIDE_REBAR_READINESS.csv", side_rows,
         ["TYPE", "ELEMENT", "SCHEDULE_ROW", "PLAN_OCCURRENCES", "DEPTH_CM", "WIDTH_CM", "COLUMN", "TOKEN_RAW",
          "TOKEN_HANDLES", "COUNT", "DIA_MM", "SPACING_CM", "NOTE_THRESHOLD_CM", "NOTE_ID", "NOTE_AUTHORITY",
          "APPLICABILITY", "FACES", "VERTICAL_ARRANGEMENT", "BAR_LENGTH", "END_TREATMENT", "COUNT_SEMANTICS",
          "STATE", "WHY"])
    _csv("08_BEAM_OPENING_OCCURRENCES.csv", open_rows,
         ["OPENING_ID", "SHEET", "SOURCE", "SOURCE_HANDLES", "BBOX_MM", "SIZE_MM", "OUTLINE_KIND", "AREA_M2",
          "INSIDE_BEAM_BANDS",
          "ON_BEAM_FACES_OR_LINEWORK", "OPENING_STATE", "TRIGGERS", "WHY"])
    _csv("09_BEAM_TOKEN_CORPUS.csv", sorted(tokens, key=lambda t: (t["SOURCE"], _natkey(t["TYPE"] or ""),
                                                                    t["TOKEN_ID"])),
         ["TOKEN_ID", "SOURCE", "HANDLE", "TYPE", "FIELD_FAMILY", "RAW", "NORMALISED", "GRAMMAR", "TERMINAL", "WHY"])
    _csv("10_SUPERSTRUCTURE_BEAM_REBAR_READINESS.csv",
         sorted(ready_rows, key=lambda r: (r["SUBFAMILY"], r["OCCURRENCE_ID"], r["COMPONENT_FAMILY"],
                                           str(r.get("SPAN_INDEX") or ""), str(r.get("BAR_RUN_ID") or ""))),
         ["OCCURRENCE_ID", "SUBFAMILY", "ELEMENT_FAMILY", "SHEET", "FLOOR", "MARK", "GEOMETRY_OBJECT",
          "BINDING_TERMINAL", "COMPONENT_FAMILY", "SPAN_INDEX", "BAR_RUN_ID", "COUNT", "DIA_MM", "STRAIGHT_RUN_M",
          "RUN_STATE", "DEVELOPMENT", "HOOKS", "STATUS", "OCCURRENCE_STATUS", "DETAIL_ID", "DETAIL_CANDIDATES",
          "APPLICABILITY_STATE", "WHY_APPLICABLE", "WHY_BLOCKED", "WIDTH_MATCH_STATE", "DRAWN_WIDTH_MM",
          "SCHEDULE_WIDTH_MM", "RULE_ID", "AUTHORITY", "STIRRUP_DETAIL"])
    _json("S6_PROVENANCE_TEMPLATES.json", {"context": ctx, "fields": list(BR.PROVENANCE_FIELDS) + ["BAR_RUN_ID"],
                                           "templates": sorted(prov, key=lambda p: (p["ELEMENT_OCCURRENCE_ID"],
                                                                                    p["BAR_RUN_ID"]))})
    _json("PRE_S6_SUMMARY.json", summary)
    import write_docs_pre_s6 as WD
    WD.write(HERE, summary, ready_rows, run_rows, span_rows, side_rows, open_rows, tag_rows, geo_rows, heads, cb_occ)
    index = {"round": "PRE_S6", "baseline": BASELINE, "drawing_sha256": DRAWING_SHA, "no_kg": True,
             "outputs": {o: _sha(HERE / o) for o in OUTPUTS},
             "code": {c: _sha(ROOT / c) for c in CODE + ["research/pre_s6_superstructure_beam_readiness/"
                                                         "write_docs_pre_s6.py"]},
             "inputs": {str(p.relative_to(ROOT)): _sha(p) for p in INPUTS}}
    _json("INDEX.json", index)
    return summary


# ============================================================================================ small helpers
def _natkey(t):
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", str(t))]


def _family(mark):
    return "CONTINUOUS_BEAM" if str(mark).upper().startswith("CB") else "SIMPLE_BEAM"


def _key_of(oid):
    p = oid.split(":")
    if p[0] == "ARC":
        return (p[2], None, None)
    a, b = re.match(r"(-?\d+)-(-?\d+)$", p[3]).groups()
    return (p[2], int(a), int(b))


def _support(s):
    return (s or {}).get("support_kind") or (s or {}).get("kind")


def _support_ref(s):
    s = s or {}
    refs = s.get("refs") or []
    col = [r["ref"] for r in refs if r.get("kind") == "COLUMN"]
    return (col[0] if col else s.get("ref")) or f"{_support(s)}"


def _sup_w(s):
    if s and s.get("lo") is not None and s.get("hi") is not None:
        return round((s["hi"] - s["lo"]) / 1000, 3)
    return None


def _int_label(lab):
    if not lab:
        return lab
    out = dict(lab)
    for k in ("count", "dia"):
        v = out.get(k)
        out[k] = int(v) if isinstance(v, str) and v.strip().isdigit() else (v or None)
    return out


def _mirror(spans):
    return [dict(sp, q=dict(sp["q"], start=sp["q"]["end"], end=sp["q"]["start"])) for sp in reversed(spans)]


def _cb_inputs(spans, d):
    spans_in = [{"index": i + 1, "clear_m": s["clear_m"], "cc_m": s["cc_m"],
                 "schedule_m": d["fields"]["spans_m"][i] if d and i < len(d["fields"]["spans_m"]) else None}
                for i, s in enumerate(spans)]
    sups = []
    for i, s in enumerate(spans):
        q = s["q"]
        if i == 0:
            sups.append({"index": 0, "width_m": _sup_w(q["start"]), "kind": _support(q["start"]),
                         "ref": _support_ref(q["start"])})
        sups.append({"index": i + 1, "width_m": _sup_w(q["end"]), "kind": _support(q["end"]),
                     "ref": _support_ref(q["end"])})
    return spans_in, sups


def _grp(rows, a, b):
    out = defaultdict(Counter)
    for r in rows:
        out[r[a]][r[b]] += 1
    return out


def _token(source, handle, tid, raw, parsed, family, typ, ambiguous=False, empty=False):
    parsed = parsed or {}
    if empty or raw in ("|", "None|None", "|None", "None|"):
        term, why = "BLOCKED_SEMANTICS", "empty schedule cell (no value printed)"
    elif parsed.get("count") and parsed.get("dia_mm"):
        term = "PARSED_AMBIGUOUS" if ambiguous else "PARSED_BOUND"
        why = ("parsed; per-face / spacing semantics unresolved" if ambiguous else
               f"parsed and bound to {typ} {family}")
    else:
        term, why = "UNSUPPORTED", "not parseable by the schedule grammar"
    return {"TOKEN_ID": f"{source}:{tid}", "SOURCE": source, "HANDLE": handle, "RAW": raw,
            "NORMALISED": (f"{parsed.get('count')}Ø{parsed.get('dia_mm')}" if parsed.get("count") else None),
            "GRAMMAR": parsed.get("grammar"), "TYPE": typ, "FIELD_FAMILY": family, "TERMINAL": term, "WHY": why}


def _opening_rows(rows, base, opn):
    rel = [{"member": None, "relation": "INSIDE_BAND", "opening": o} for o in opn]
    for c in BR.opening_components(rel):
        if c["STATE"] == "NOT_APPLICABLE":
            rows.append(dict(base, COMPONENT_FAMILY=c["COMPONENT_FAMILY"], STATUS="NOT_APPLICABLE", WHY_BLOCKED=None,
                             WHY_APPLICABLE="no source-identified opening inside this beam band"))
        else:
            rows.append(dict(base, COMPONENT_FAMILY=c["COMPONENT_FAMILY"], STATUS="BLOCKED_COMPONENT",
                             WHY_BLOCKED=f"opening candidate {opn} inside the band; the p.16 'opening in beam' "
                                         "detail is an unread candidate"))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    dxf = Path(argv[0]) if argv else DEFAULT_DXF
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    s = build(dxf)
    print(json.dumps({k: s[k] for k in ("tag_count", "tags", "simple_occurrences", "simple_occurrence_status",
                                        "cb_occurrences", "cb_occurrence_status", "untagged_geometry",
                                        "provenance_templates")}, indent=1, default=str))


if __name__ == "__main__":
    main()
