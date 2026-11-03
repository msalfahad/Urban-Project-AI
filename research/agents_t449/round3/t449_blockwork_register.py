"""T-449 round 3 (BLOCKWORK): the A1 correction register of every per-project input that reaches a blockwork
(masonry) line of the candidate of record.

Owner follow-up directive 2026-11-02 (MISSION.md, A1): every project-specific correction is
  (A) a DRAWING-DERIVED RULE (reusable logic with tests),
  (B) a DECLARED PROJECT FACT (per-project config, URBAN_PROJECT_CONFIG_V1, engine/project_config.py), or
  (C) an UNEXPLAINED PATCH (made only to match the freelancer or an earlier engine result): removed.

Census: every project-input builder the candidate run feeds (research/agents_t422/v3044_run.py, V3.0.2 .. V3.0.44) is
built and scanned for masonry; a builder REACHES a blockwork line when its method creates or changes a masonry line or
the masonry range beside one:
  V3.0.26 lines   per wall x item (MAS.BLOCK m2, ARCH.WALL_PANEL m2, ARCH.WALL_VOLUME m3) of the T-333 fill (T-279)
  V3.0.23 chains  parapet runs: the block alternative above the RC upstand, a range beside the parapet lines (T-324)
  V3.0.35 lines   boundary fence EXT.FENCE.BLOCK / BLOCK_COUNT (HELD, with the plane beside) (T-405)
  V3.0.19 trace   per opening, the MASONRY trade state of the glazed host (NOT_APPLICABLE) (T-249 / T-255)
Every other builder that names masonry does so in text only (guard evidence, a source note): listed with the reason.

Per wall the rule's geometry comes from the Checker-merged wall-piece ledgers, newest first: T-261 split pieces
(MERGED, register v3 parts), T-274 exact pieces (MERGED, register v3), register v2 evidence (T-228, MERGED); beam
depths and slab thicknesses from the printed readings those ledgers carry (and the schedule text of the T-333 fill);
openings from the T-333 opening-height basis (drawn outlines; Q-55 doors by width x the declared fallback). The rule's
result is compared with the carried figure:
  A-REPRODUCED   the generic rule + declared facts give the carried state and figure (residual named)
  A-SPECIFIED    drawing-derived and Checker-verified, rule named, generic code or geometry reader not reproducing
  B              the entry is itself a declared project fact
  C              its basis is a freelancer / benchmark / earlier engine figure: removed (none found)

Read-only: imports the merged builders (each pins its own ledgers by sha256), writes only where it is told to.

    python3 -I research/agents_t449/round3/t449_blockwork_register.py [out_dir] [--facts-out FILE]
"""

from __future__ import annotations

import csv
import hashlib
import importlib
import io
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.project_config import parse_project_config, load_project_config  # noqa: E402
from engine.source import blockwork_basis_rules_v1 as R  # noqa: E402

RUN = ROOT / "research/agents_t422/v3044_run.py"
FACTS = HERE / "DEVELOPMENT-VILLA-T131.blockwork_facts.json"
CONCRETE_FACTS = ROOT / "research/agents_t449/DEVELOPMENT-VILLA-T131.concrete_facts.json"
V2 = ROOT / "research/agents_t228/BLOCKWORK_WALL_REGISTER_V2.csv"
V4 = ROOT / "research/agents_t288/BLOCKWORK_WALL_REGISTER_V4.csv"
CHANGED_V4 = ROOT / "research/agents_t288/CHANGED_WALLS_V4.csv"
SUNKEN = ROOT / "research/agents_t288/SUNKEN_PIECES_T288.csv"
T274 = ROOT / "research/agents_t274/T274_CORRECTED.csv"
T274_NBA = ROOT / "research/agents_t274/T274_NET_BEFORE_AFTER.csv"
T261 = ROOT / "research/agents_t261/T261_SPLIT.csv"
FILL = ROOT / "research/agents_t333/FILL_T333.csv"
OHB = ROOT / "research/agents_t333/OPENING_HEIGHT_BASIS_T333.csv"
LBA = ROOT / "research/agents_t333/LINE_BEFORE_AFTER_T333.csv"
PID = "development-villa-t131"
PRINT_TOL = 0.0005        # the fill prints m2 to 4 decimals
DIAG_TOL = 0.005          # +-0.5 % diagnostic (owner follow-up 2026-11-02)
C_WORDS = re.compile(r"freelancer|workbook|benchmark|reference boq|to match", re.I)
MAS_TEXT = re.compile(r"MAS\.|blockwork|masonry", re.I)

F_STOREY = {"GF": "STOREY_HEIGHT.GF.MAIN", "1F": "STOREY_HEIGHT.1F.MAIN", "2F": "STOREY_HEIGHT.2F.MAIN"}
F_ANNEX = "STOREY_HEIGHT.GF.ANNEX"            # NOT declared (owner Q-54 B): the annex walls stay HELD
F_DOOR = "OPENING.DOOR.FALLBACK_HEIGHT"
F_UPSTAND = "PARAPET.RC_UPSTAND.MIN_ABOVE_SLAB"  # declared in round 1 (concrete facts)

REACH = {
    "ARCH_TAKEOFF_V3.0.26": ("lines", "arch_v3026 BLOCKWORK_FILL: per wall per item on the held storey x thickness "
                                      "masonry lines (MAS.BLOCK / ARCH.WALL_PANEL / ARCH.WALL_VOLUME)"),
    "ARCH_TAKEOFF_V3.0.23": ("chains[].runs[].block_alt_m2", "arch_v3023 parapet family: the block alternative above "
                                                              "the RC upstand (MAS.BLOCK, exclusive with RC), beside"),
    "ARCH_TAKEOFF_V3.0.35": ("lines[EXT.FENCE.BLOCK*]", "arch_v3035 boundary fence: block net / block count HELD lines "
                                                        "with the wall plane beside"),
    "ARCH_TAKEOFF_V3.0.19": ("opening_trace[].trades.MASONRY", "arch_v3019 opening trace: the MASONRY state of each "
                                                               "traced opening (no quantity)"),
}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _rows(p):
    return list(csv.DictReader(io.StringIO(Path(p).read_text(encoding="utf-8"))))


def _f(v):
    return None if v in ("", None) else float(v)


# ================================================================================================ census
def _builders():
    """version -> (module, function, with_pid) exactly as the candidate run calls them."""
    src = RUN.read_text(encoding="utf-8")
    for m in sorted(set(re.findall(r'"research" / "(agents_t\d+)"', src)) | {"agents_t422"}):
        p = str(ROOT / "research" / m)
        if p not in sys.path:
            sys.path.insert(0, p)
    imps = dict((b, a) for a, b in re.findall(r"import (\w+) as (L\w*)", src))
    out = {"ARCH_TAKEOFF_V3.0.2": ("v302_run", "INPUTS", False)}
    for v, L, fn, arg in re.findall(r'"v(30\d+)_inputs.json"\)\.write_text\(json\.dumps\((L\w*)\.(\w+)\((\w*)', src):
        out.setdefault("ARCH_TAKEOFF_V3.0." + v[2:], (imps[L], fn, bool(arg)))
    return dict(sorted(out.items(), key=lambda kv: int(kv[0].rsplit(".", 1)[1])))


def _build(mod, fn, with_pid):
    f = getattr(importlib.import_module(mod), fn)
    if not callable(f):
        return f
    if mod == "t350_inputs":                       # the run passes its first zone's template line (v3044_run.py)
        return f(PID, template=f.__globals__["zones"]()[0]["bound_lines"][0])
    return f(PID) if with_pid else f()


def census():
    rows, docs = [], {}
    for ver, (mod, fn, with_pid) in _builders().items():
        d = _build(mod, fn, with_pid)
        docs[ver] = d
        txt = json.dumps(d, ensure_ascii=False, sort_keys=True)
        words = len(MAS_TEXT.findall(txt))
        if ver in REACH:
            reach, why = "REACHES", REACH[ver][1]
        elif words:
            reach, why = "TEXT_ONLY", ("masonry named in text only (default-guard evidence / source notes / held "
                                       "reasons of other trades): the method makes or moves no masonry line from it")
        else:
            reach, why = "NONE", "no masonry in the input"
        rows.append({"version": ver, "builder": f"{mod}.{fn}", "schema": d.get("schema") if isinstance(d, dict)
                     else None, "masonry_words": words, "reach": reach, "why": why,
                     "section": REACH.get(ver, ("",))[0]})
    return rows, docs


# ================================================================================================ geometry readers
MEMBER = re.compile(r"\b(BM-[0-9A-Z]+-\d+)\b")
MARK = re.compile(r"\b(C?B\d+)\b")
SLAB = re.compile(r"\bslab (?:corner )?([0-9A-Z]+-\d+)")
EV_PIECE = re.compile(r"(?P<name>[^,;:()]*?)\((?:slab t (?P<t>[\d.]+)|h (?P<d>[\d.]+) (?P<c>[A-Z_]+)|[^)]*)\)[^:;()]*: "
                      r"(?P<L>[\d.]+) m -> h (?P<H>[\d.]+|HELD)")
EX_PIECE = re.compile(r"^(?P<name>.+?) \((?:h (?P<d>[\d.]+)|t (?P<t>[\d.]+)|h not printed)\)(?P<rest>.*?) "
                      r"(?P<L>[\d.]+) m h (?P<H>[\d.]+)$")
EX_HELD = re.compile(r"^(?P<name>\S+) (?P<L>[\d.]+) m HELD")
JUNCTION = re.compile(r"junction close (?P<x>[+-][\d.]+) m, d_gross (?P<a>[+-][\d.]+) \.\. (?P<b>[+-][\d.]+) m2")
SCHED = re.compile(r"(C?B\d+) (BM-[0-9A-Z]+-\d+) \(C-BEAM\d+ \S+ W \d+ H (\d+)\)")
SHARED = re.compile(r"corner shared with \S+ (BM-[0-9A-Z]+-\d+) \(h ([\d.]+)\)")


class Readings:
    """printed member depths / slab thicknesses as the merged ledgers read them (member id, mark, slab id)."""

    def __init__(self, v2, t274, fill):
        self.member, self.mark, self.slab = defaultdict(set), defaultdict(set), defaultdict(set)
        for r in v2.values():
            for x in EV_PIECE.finditer(r["evidence"]):
                self._add(x["name"], _f(x["d"]), _f(x["t"]))
        for r in t274.values():
            for tok in r["exact_pieces"].split(" | "):
                m = EX_PIECE.match(tok.split("; ")[-1].strip())
                if m and (m["d"] or m["t"]):
                    self._add(m["name"], _f(m["d"]), _f(m["t"]))
        for r in fill:
            for mk, mem, h in SCHED.findall(r["conflict"]):
                self.member[mem].add(int(h) / 100.0)
                self.mark[mk].add(int(h) / 100.0)

    def _add(self, name, d, t):
        if t is not None:
            for s in SLAB.findall("slab " + name.split("slab ")[-1]) if "slab" in name else []:
                self.slab[s].add(t)
            return
        if d is None:
            return
        mem = MEMBER.search(name)
        if mem:
            self.member[mem.group(1)].add(d)
        mk = MARK.search(name)
        if mk:
            self.mark[mk.group(1)].add(d)

    def soffit(self, name):
        """(depth, slab_t, None) or (None, None, why) for a piece name."""
        s = SLAB.search(name)
        if s:
            ts = self.slab.get(s.group(1)) or set().union(*self.slab.values())
            ts = ts if len(ts) == 1 else set()
            return (None, next(iter(ts)), None) if ts else (None, None, f"slab {s.group(1)} thickness not read")
        mem = MEMBER.search(name)
        if mem and len(self.member.get(mem.group(1), ())) == 1:
            return next(iter(self.member[mem.group(1)])), None, None
        mk = MARK.search(name)
        if mk and len(self.mark.get(mk.group(1), ())) == 1:
            return next(iter(self.mark[mk.group(1)])), None, None
        return None, None, f"depth of '{name.strip()}' not read uniquely from a merged schedule reading"


def pieces_t261(rows, rd):
    out, readings = [], []
    for i, r in enumerate(rows):
        L = float(r["length_m"])
        pid = f"{i}:{r['piece']}"
        if r["piece_status"] == "HELD":
            out.append(R.Piece(pid, L, held_reason=r["held_item"][:160] or r["piece"]))
            continue
        name = r["piece"].split(" ", 1)[1] if " " in r["piece"] else r["piece"]
        d, t, why = rd.soffit(name)
        out.append(R.Piece(pid, L, depth_m=d, slab_t_m=t, held_reason=why))
        readings.append((pid, _f(r["height_m"])))
    return out, readings, []


def pieces_t274(row, census_m, rd, sunken_slabs):
    out, readings, notes = [], [], []
    toks = [t.strip() for t in row["exact_pieces"].split(" | ")]
    adjust = 0.0
    for i, tok in enumerate(toks):
        j = JUNCTION.search(tok)
        if j:
            if j["a"] != j["b"]:
                notes.append(f"RANGE: T-215 junction close d_gross {j['a']} .. {j['b']} m2 (two readings)")
            adjust = float(j["x"])
        body = tok.split("; ")[-1]
        m, mh = EX_PIECE.match(body), EX_HELD.match(body)
        if m:
            L = float(m["L"]) + adjust
            adjust = 0.0
            name = m["name"]
            if m["d"] or m["t"]:
                d, t, why = _f(m["d"]), _f(m["t"]), None
            else:
                sh = SHARED.search(m["rest"])
                d, t, why = (float(sh.group(2)), None, None) if sh else rd.soffit(name)
                if sh:
                    notes.append(f"corner piece of an unprinted member at the deeper shared member ({sh.group(1)})")
            s = SLAB.search(name)
            out.append(R.Piece(f"{i}:{name}", L, depth_m=d, slab_t_m=t, held_reason=why,
                               sunken=bool(s and s.group(1) in sunken_slabs)))
            readings.append((f"{i}:{name}", float(m["H"])))
        elif mh:
            out.append(R.Piece(f"{i}:{mh['name']}", float(mh["L"]), held_reason="nothing with a printed soffit is "
                                                                                    "drawn over this length"))
        if "wholly under one soffit" in tok:
            notes.append("UNIFORM_SOFFIT: the run is wholly under one soffit; the masonry is the census length")
    if any(n.startswith("UNIFORM_SOFFIT") for n in notes):
        soffits = {(p.depth_m, p.slab_t_m) for p in out if not p.held_reason}
        if len(soffits) == 1 and not any(p.held_reason for p in out):
            d, t = soffits.pop()
            h = readings[0][1]
            out, readings = [R.Piece("census", census_m, depth_m=d, slab_t_m=t)], [("census", h)]
    return out, readings, notes


def pieces_v2(row, rd, sunken_slabs):
    seg = row["evidence"].split("||")[-1]
    m = re.search(r"member above / height:(.*?);\s*storey", seg)
    if not m:
        return None, [], ["no member-above reading in the register v2 evidence"]
    out, readings = [], []
    for i, x in enumerate(EV_PIECE.finditer(m.group(1))):
        name = x["name"].strip()
        pid = f"{i}:{name[-40:]}"
        if x["H"] == "HELD":
            out.append(R.Piece(pid, float(x["L"]), held_reason=name[-80:] or "held soffit"))
            continue
        d, t = _f(x["d"]), _f(x["t"])
        s = SLAB.search("slab " + name.split("slab ")[-1]) if t is not None and "slab" in name else None
        out.append(R.Piece(pid, float(x["L"]), depth_m=d, slab_t_m=t,
                           sunken=bool(s and s.group(1) in sunken_slabs)))
        readings.append((pid, float(x["H"])))
    return out, readings, []


# ================================================================================================ openings
OPEN_TOK = re.compile(r"(?P<id>[A-Z]+-?[0-9A-Z-]*\d+) (?:(?P<a>[\d.]+) )?(?P<st>DEDUCTED|IN_HELD_PIECE|ON_HELD_WALL|"
                      r"HELD)")
DOOR_W = re.compile(r";\s*([\d.]+) x ([\d.]+) = ([\d.]+)\s*$")


def openings_of(fill_row, ohb):
    ops, missing = [], []
    for x in OPEN_TOK.finditer(fill_row["opening_deductions"] or ""):
        if x["st"] == "HELD":
            ops.append(R.Opening(x["id"], "HELD"))           # size not established: not deductible -> wall HELD
            continue
        b = ohb.get(x["id"])
        if x["st"] == "ON_HELD_WALL" and b is None:
            ops.append(R.Opening(x["id"], "ON_HELD_WALL", outline_m2=float(x["a"])))
            continue
        if x["st"] == "IN_HELD_PIECE":
            ops.append(R.Opening(x["id"], "IN_HELD_PIECE", in_held_piece=True))
        elif b is None:
            missing.append(x["id"])
        elif b["height_basis"].startswith("ASSUMED"):
            w = DOOR_W.search(b["basis_source"])
            ops.append(R.Opening(x["id"], R.DOOR, width_m=float(w.group(1))) if w else R.Opening(x["id"], R.DOOR))
        else:
            ops.append(R.Opening(x["id"], b["kind"], outline_m2=float(b["deduction_m2"])))
    return ops, missing


# ================================================================================================ V3.0.26 entries
def _entry(version, line_id, element, action, patch, cls, rule, **kw):
    e = {"version": version, "line_id": line_id, "element_id": element, "action": action, "patch": patch,
         "class": cls, "rule": rule}
    e.update(kw)
    return e


def _res(res):
    return {"state": res.state, "value": res.value, "status": res.status, "upper_m2": res.upper_m2,
            "drop_length_m": res.drop_length_m, "deducted_m2": res.deducted_m2, "held": list(res.held),
            "facts_used": list(res.facts_used), "formula": res.formula[:600]}


def _fill_state(st):
    return {"VERIFIED": "VALUED", "DRAWING-CONFIRMED": "VALUED", "ASSUMED — OWNER-APPROVED": "VALUED",
            "ASSUMED - OWNER-APPROVED": "VALUED", "ESTABLISHED PART + HELD": "PART", "HELD ON DROP": "DROP", "HELD": "HELD"}[st]


def wall_rule(cfg, w, fill_row, src):
    """-> (WallResult or None, geometry source, notes, reading mismatches)."""
    rd, v2, v4, t274, t261, sunk, ohb = (src[k] for k in ("rd", "v2", "v4", "t274", "t261", "sunk", "ohb"))
    reg = v4.get(w) or {}
    floor = reg.get("floor") or w[:2]
    v2r = v2.get(w) or {}
    annex = "annex datum" in (fill_row["held_item"] or "") + " " + (v2r.get("unresolved_reason") or "")
    storey = F_ANNEX if annex else F_STOREY[floor]
    held_notes = [x for x in (v2r.get("held_cause_class") or "", reg.get("held_items") or "")
                  if "lift tie beam" in x][:1]
    sk = sunk.get(w, set())
    pcs = None
    if w in t261:
        pcs, rdg, notes = pieces_t261(t261[w], rd)
        geo = "T-261 split (MERGED)"
    elif w in t274:
        pcs, rdg, notes = pieces_t274(t274[w], float(t274[w]["census_m"]), rd, sk)
        geo = "T-274 exact pieces (MERGED)"
    elif w in v2:
        pcs, rdg, notes = pieces_v2(v2[w], rd, sk)
        geo = "register v2 evidence (T-228, MERGED)"
        if pcs is None and fill_row["status"] != "HELD":
            return None, geo, notes, []
    elif fill_row["status"] == "HELD":
        pcs, rdg, notes, geo = [], [], [], "none (no wall band or member bound in any merged ledger)"
    else:
        return None, "none", ["no merged piece ledger names the wall"], []
    if not pcs and fill_row["status"] != "HELD":
        return None, geo, notes + ["no piece read"], []
    pcs = pcs or []
    ops, missing = openings_of(fill_row, ohb)
    if missing:
        notes.append(f"opening(s) {missing} not in the T-333 opening-height basis")
    try:
        res = R.wall_net(cfg, w, storey, pcs, ops, door_fallback_fact=F_DOOR,
                         held_notes=[f"printed note calls for an unsized member over the wall: {n}" for n in held_notes])
    except R.BlockworkRuleError as ex:
        return None, geo, notes + [f"rule refused the read geometry: {ex}"], []
    st, _ = R.storey_height(cfg, storey)
    bad = []
    for pid, h in rdg:
        p = next(p for p in pcs if p.piece_id == pid)
        rh, _ = R.piece_height(st, p) if st is not None else (None, None)
        if rh is not None and h is not None and abs(rh - h) > 1e-6:
            bad.append(f"{pid}: rule h {rh} vs ledger h {h}")
    return res, geo, notes, bad


PENDING = (   # (test on the reasons / wall, the rule the generic code still owes) - every A-SPECIFIED wall names one
    (lambda w, t: "BAY-ENDS" in w, "R-MAS-BAY-CAP-1 (pending): full-thickness bay caps on the wall layer, one row per "
                                   "cap pair at the soffit of the band over them (T-222 s.2); no cap reader yet"),
    (lambda w, t: "ABOVE-LINTEL" in w, "R-MAS-ABOVE-LINTEL-1 (pending): masonry over a lintel = width x (soffit level "
                                       "- (head + lintel depth)) (T-201 / T-207 levels); no head-level reader yet"),
    (lambda w, t: w == "1F-W25", "R-MAS-BAY-CAP-1 (pending): the T-222 bay piece is read from the cap layer, not "
                                 "from a member-above reading"),
    (lambda w, t: "RANGE" in t, "R-MAS-JUNCTION-CLOSE-1 (pending): a T-215 junction close with two readings gives a "
                                "RANGE; the carried figure is its LOW end with no increment named (finding "
                                "F-T449-R3-2)"),
    (lambda w, t: "drop length" in t, "R-MAS-DROP-1 + R-MAS-JUNCTION-CLOSE-1: the d coefficient L is the panel clip "
                                      "before the junction close / v4 re-cut; the junction's own length is open for "
                                      "the Checker's re-clip (T-288 SUNKEN_PIECES)"),
    (lambda w, t: w == "GF-W01", "R-MAS-PIECE-HEIGHT-1 on the v4 sliver (0.0026 m inside B26's drawn outline at "
                                 "3.65): B26's printed depth is in no merged schedule reading the reader uses"),
    (lambda w, t: "NON_POSITIVE" in t or "exceed" in t, "R-MAS-WALL-NET-1: the opening position against the held "
                                                        "pieces is not read"),
)


def pending(wall_id, why, src):
    t = " | ".join(str(x) for x in why)
    for test, text in PENDING:
        if test(wall_id, t):
            return text
    return "rule named in not_reproduced; generic reader pending"


def wall_entries(cfg, doc, src):
    out = []
    fill = {(r["line_id"], r["wall_id"]): r for r in _rows(FILL)}
    changed = {r["wall_id"]: r for r in _rows(CHANGED_V4)}
    mas = {}
    for ln in doc["lines"]:
        if ln["item_code"] != "MAS.BLOCK":
            continue
        for w in ln["walls"]:
            fr = fill[(ln["line_id"], w["wall_id"])]
            patch = {"status": w["status"], "carried": w["carried"], "upper_at_d0": w["upper_at_d0"],
                     "drop_length_m": w["drop_coefficient"], "part_status": w["part_status"]}
            base = dict(item_code="MAS.BLOCK", floor=ln["floor"], thickness_m=ln["family"])
            if C_WORDS.search(json.dumps(w, ensure_ascii=False)):
                e = _entry("ARCH_TAKEOFF_V3.0.26", ln["line_id"], w["wall_id"], w["status"], patch, "C", None, **base)
                out.append(e)
                mas[w["wall_id"]] = e
                continue
            res, geo, notes, bad = wall_rule(cfg, w["wall_id"], fr, src)
            want = _fill_state(w["status"])
            target = w["carried"] if want in ("VALUED", "PART") else (w["upper_at_d0"] if want == "DROP" else None)
            e = _entry("ARCH_TAKEOFF_V3.0.26", ln["line_id"], w["wall_id"], w["status"], patch, None,
                       res.rule if res else None, geometry=geo, notes=notes, **base)
            if res is not None:
                e["rule_result"] = _res(res)
            got = None if res is None else (res.upper_m2 if res.state == R.DROP else res.value)
            why = []
            if res is None:
                why.append("no rule result: " + "; ".join(notes))
            elif res.state != want:
                why.append(f"rule state {res.state} vs carried {want}")
            if bad:
                why.append("height readings not storey - depth: " + "; ".join(bad[:3]))
            if res is not None and want == "DROP" and abs((res.drop_length_m or 0) - (w["drop_coefficient"] or 0)) \
                    > PRINT_TOL:
                why.append(f"drop length rule {res.drop_length_m} vs carried {w['drop_coefficient']}")
            if res is not None and want in ("VALUED", "PART", "DROP") and w["status"] != "HELD ON DROP":
                eff = w["part_status"] if want == "PART" else w["status"]
                if (res.status == R.ASSUMED_OWNER_APPROVED) != eff.startswith("ASSUMED"):
                    why.append(f"rule status {res.status} vs carried {eff}")
            if any(n.startswith("RANGE") for n in notes):
                why.append([n for n in notes if n.startswith("RANGE")][0] + f"; carried {target} = one end")
            resid = None
            if not why and target is not None and got is not None:
                resid = round(target - got, 6)
                e["carried_minus_rule_m2"] = resid
                if abs(resid) > PRINT_TOL:
                    cause = (changed.get(w["wall_id"]) or {}).get("cause") or (src["v4"].get(w["wall_id"]) or {}).get(
                        "cause_v4") or (src["t274nba"].get(w["wall_id"]) or {}).get("why") or ""
                    if cause == "unchanged":
                        cause = ""
                    if abs(resid) <= DIAG_TOL * abs(target) and cause:
                        e["residual_named"] = f"{resid:+.4f} m2 ({100 * resid / target:+.3f} %): {cause[:400]}"
                    else:
                        why.append(f"rule {got} vs carried {target} ({resid:+.4f} m2)" +
                                   (f"; register v4 cause: {cause[:300]}" if cause else ""))
            elif not why and want == "HELD" and res is not None:
                e["held_reproduced"] = list(res.held)[:4]
            e["class"] = "A-SPECIFIED" if why else "A-REPRODUCED"
            if why:
                e["rule_pending"] = pending(w["wall_id"], why, src)
            if why:
                e["not_reproduced"] = " | ".join(str(x) for x in why)[:900]
            out.append(e)
            mas[w["wall_id"]] = e
    for ln in doc["lines"]:
        if ln["item_code"] == "MAS.BLOCK":
            continue
        for w in ln["walls"]:
            m = mas[w["wall_id"]]
            mw = m["patch"]
            patch = {"status": w["status"], "carried": w["carried"]}
            if ln["item_code"] == "ARCH.WALL_PANEL":
                ok = w["status"] == mw["status"] and w["carried"] == mw["carried"]
                rule = "R-MAS-PANEL-SAME-1"
                want = mw["carried"]
            else:
                want = None if mw["carried"] is None else round(mw["carried"] * ln["family"], 6)
                ok = w["status"] == mw["status"] and ((want is None and w["carried"] is None) or (
                    want is not None and w["carried"] is not None and abs(w["carried"] - want) <= PRINT_TOL))
                rule = "R-MAS-VOLUME-1"
            cls = m["class"] if ok else "A-SPECIFIED"
            e = _entry("ARCH_TAKEOFF_V3.0.26", ln["line_id"], w["wall_id"], w["status"], patch, cls, rule,
                       item_code=ln["item_code"], floor=ln["floor"], thickness_m=ln["family"],
                       follows=f"MAS.BLOCK {m['line_id']} {w['wall_id']} ({m['class']})", rule_value=want,
                       facts_used=list((m.get("rule_result") or {}).get("facts_used", [])),
                       rule_state=(m.get("rule_result") or {}).get("state"))
            if not ok:
                e["not_reproduced"] = f"carried {w['carried']} vs {rule} {want}"
            elif cls == "A-SPECIFIED":
                e["not_reproduced"] = f"follows its MAS.BLOCK wall: {m.get('not_reproduced', '')}"[:900]
            out.append(e)
    return out


# ================================================================================================ other versions
def parapet_entries(cfg, doc):
    out = []
    for c in doc["chains"]:
        for r in c["runs"]:
            eid = f"{c['element_id']}:{r['run']}"
            res = R.parapet_block_alternative(cfg, r["run"], r["centreline_hi_m"], r["h_hi_m"], F_UPSTAND,
                                              material_decided_rc=(r["material"] == "RC"))
            patch = {"block_alt_m2": r["block_alt_m2"], "note": r.get("block_alt_note")}
            e = _entry("ARCH_TAKEOFF_V3.0.23", c.get("roof_wp_line_id"), eid, f"PARAPET_{r['material']}", patch, None,
                       res.rule, rule_result={"state": res.state, "low": res.low, "high": res.high,
                                              "formula": res.formula, "facts_used": list(res.facts_used),
                                              "held_reason": res.held_reason},
                       floor=c["floor"], run_kind=r["kind"], centreline_hi_m=r["centreline_hi_m"],
                       h_hi_m=r["h_hi_m"], corrections=r.get("corrections"))
            pb = r["block_alt_m2"]
            if pb is None:
                e["class"] = "A-SPECIFIED"
                e["not_reproduced"] = (f"no block alternative booked ({(r.get('block_alt_note') or '')[:160]}); the "
                                       f"rule gives [0, {res.high}] m2 beside, owed by the blockwork binding")
            elif abs(pb[0] - res.low) <= 1e-6 and abs(pb[1] - res.high) <= 1e-5:
                e["class"] = "A-REPRODUCED"
            else:
                e["class"] = "A-SPECIFIED"
                e["not_reproduced"] = (f"carried {pb} vs rule [{res.low}, {res.high}] m2 at the run's current "
                                       f"centreline {r['centreline_hi_m']} m (corrections: "
                                       f"{'; '.join(r.get('corrections') or [])[:200]})")
            out.append(e)
    return out


def fence_entries(doc):
    out = []
    plane = {l["run"]: l for l in doc["lines"] if l["action"] == "FENCE_VALUE" and l["item_code"] == "EXT.FENCE.WALL"}
    for l in doc["lines"]:
        if not l["item_code"].startswith("EXT.FENCE.BLOCK"):
            continue
        b = l.get("beside")
        p = plane.get(l.get("run"))
        patch = {"evidence_status": l.get("evidence_status"), "beside": b}
        rule = "R-MAS-FENCE-HELD-1"
        if l["item_code"] == "EXT.FENCE.BLOCK_COUNT":
            ok = l.get("evidence_status") == "HELD" and b is None
            why = "block count HELD until the block type / size is declared for the fence (Q-65 C)"
        elif p is not None:
            want = round(p["terms"]["length_m"] * p["terms"]["height_m"], 6)
            ok = (l.get("evidence_status") == "HELD" and b is not None and b["kind"] == "AT_MOST"
                  and abs(b["value"] - want) <= PRINT_TOL)
            why = (f"block net HELD (columns not counted, lower band material open); beside AT_MOST = plane "
                   f"{p['terms']['length_m']} x {p['terms']['height_m']} = {want} m2")
        else:
            ok = l.get("evidence_status") == "HELD" and b is None
            why = "plane itself HELD: no beside figure"
        e = _entry("ARCH_TAKEOFF_V3.0.35", None, l["element_id"], l["action"], patch,
                   "A-REPRODUCED" if ok else "A-SPECIFIED", rule, item_code=l["item_code"], rule_basis=why)
        if not ok:
            e["not_reproduced"] = why
        out.append(e)
    return out


def trace_entries(doc, ohb):
    """V3.0.19 opening trace, MASONRY trade: NOT_APPLICABLE in a glazed host (R-MAS-GLAZED-HOST-1), or the opening's
    deduction on its host wall (R-MAS-OPENING-DEDUCT-1: the drawn outline inside the masonry, T-333 basis)."""
    out = []
    for t in doc.get("opening_trace", []):
        m = (t.get("trades") or {}).get("MASONRY")
        if not m:
            continue
        b = ohb.get(t["opening"])
        if m.get("state") == "NOT_APPLICABLE":
            ok, rule = "glazed" in (m.get("why") or ""), "R-MAS-GLAZED-HOST-1"
            basis = ("an opening in a glazed host line builds no masonry (build before deduct): the masonry trade is "
                     "NOT_APPLICABLE for it")
        else:
            rule = "R-MAS-OPENING-DEDUCT-1"
            ok = b is not None and m.get("value") is not None and abs(float(b["deduction_m2"]) - m["value"]) <= \
                PRINT_TOL
            basis = (f"deducted on host {b['host']} by its drawn outline inside the masonry {b['deduction_m2']} m2 "
                     f"(T-333 basis; the host wall entry reproduces it)" if b else "opening not in the T-333 basis")
        e = _entry("ARCH_TAKEOFF_V3.0.19", None, f"OPENING:{t['opening']}", m.get("state"), m,
                   "A-REPRODUCED" if ok else "A-SPECIFIED", rule, item_code="MASONRY_TRACE", rule_basis=basis)
        if not ok:
            e["not_reproduced"] = basis
        out.append(e)
    return out


# ================================================================================================ facts
def _fact(fid, kind, value, unit, src_kind, ref, by, date, lines, note):
    return {"fact_id": fid, "version": 1, "quantity_kind": kind, "value": value, "unit": unit,
            "source": {"kind": src_kind, "reference": ref},
            "approval": {"status": "APPROVED", "by": by, "date": date},
            "affected_lines": sorted(lines), "confidence": "CONFIRMED", "note": note}


def declared_facts(usage):
    rev = ("a DRAWING-CONFIRMED reading of the printed set (architectural section chain), not a designer approval "
           "(Checker F-C-T449-1); the same storey heights every Checker-verified wall of register v4 uses")
    facts = [
        _fact(F_STOREY["GF"], "LENGTH", 4.50, "m", "DRAWING",
              "p7757_arch_sheet10.pdf section A-A level chain '450' (T-112); = structural tops +5.45 - +0.95 "
              "(round 1 LEVEL.STRUCTURAL_TOP.1F.MAIN - LEVEL.STRUCTURAL_TOP.GF.MAIN); owner Q-60 A uses it",
              "DESIGNER", "2026-10-20", usage[F_STOREY["GF"]], rev),
        _fact(F_STOREY["1F"], "LENGTH", 4.20, "m", "DRAWING",
              "p7757_arch_sheet10.pdf section A-A level chain '420' (T-112); = structural tops +9.65 - +5.45 "
              "(round 1 level facts); owner Q-60 A uses it", "DESIGNER", "2026-10-20", usage[F_STOREY["1F"]], rev),
        _fact(F_STOREY["2F"], "LENGTH", 4.20, "m", "DRAWING",
              "p7757_arch_sheet10.pdf section A-A level chain '420' between the 2F slab and the main roof slab "
              "(T-112); owner Q-60 A uses it", "DESIGNER", "2026-10-20", usage[F_STOREY["2F"]],
              rev + "; the main roof structural top is NOT declared as a level (round 1 holds 13 columns at it, "
                    "D-39 / Q-54 B): finding F-T449-R3-1 for the Checker"),
        _fact(F_DOOR, "LENGTH", 2.20, "m", "OWNER_DECISION",
              "OWNER_QUESTIONS_ANSWERED Q-55 C: Urban fallback internal door height 2.20 m, ASSUMED, only where the "
              "drawings are silent; measured width kept", "PROJECT_OWNER", "2026-10-20", usage[F_DOOR],
              "evidence status ASSUMED — OWNER-APPROVED on every wall that deducts such a door"),
    ]
    return {"schema": "URBAN_PROJECT_CONFIG_V1", "project_id": "DEVELOPMENT-VILLA-T131", "config_version": "1.0.0",
            "note": "T-449 round 3 (blockwork): declared facts of the training villa's masonry lines. NOT declared: "
                    "STOREY_HEIGHT.GF.ANNEX (owner Q-54 B: HOLD; the annex walls stay HELD); the 15 cm black block "
                    "module (no masonry line counts blocks). The parapet RC upstand is the round-1 concrete fact.",
            "facts": facts}


def fact_usage(entries):
    use = defaultdict(set)
    for e in entries:
        if e["class"] != "A-REPRODUCED" or not e.get("line_id") or e["version"] != "ARCH_TAKEOFF_V3.0.26":
            continue
        rr = e.get("rule_result") or {}
        state = rr.get("state", e.get("rule_state"))
        if state in (R.VALUED, R.PART, R.DROP):
            for f in rr.get("facts_used", e.get("facts_used", [])):
                use[f].add(e["line_id"])
    return {k: sorted(v) for k, v in use.items()}


class _Merged:
    """lookup over the blockwork facts, then the round-1 concrete facts (the parapet upstand)."""

    def __init__(self, *cfgs):
        self.cfgs = cfgs
        self.project_id = cfgs[0].project_id
        self.config_version = cfgs[0].config_version
        self.content_sha256 = cfgs[0].content_sha256

    def lookup(self, fid):
        lk = None
        for c in self.cfgs:
            lk = c.lookup(fid)
            if lk.usable or c.history(fid):
                return lk
        return lk

    def history(self, fid):
        return tuple(x for c in self.cfgs for x in c.history(fid))


def _boot_cfg():
    return parse_project_config(declared_facts(defaultdict(lambda: ["L-BOOT"])))


def load_cfg(cfg=None):
    base = cfg or (load_project_config(FACTS) if FACTS.exists() else _boot_cfg())
    return _Merged(base, load_project_config(CONCRETE_FACTS))


# ================================================================================================ build
def sources():
    v2 = {r["wall_id"]: r for r in _rows(V2)}
    t274 = {r["wall_id"]: r for r in _rows(T274)}
    t261 = defaultdict(list)
    for r in _rows(T261):
        t261[r["wall_id"]].append(r)
    sunk = defaultdict(set)
    for r in _rows(SUNKEN):
        sunk[r["wall_id"]].add(r["panel_face"])
    fill = _rows(FILL)
    return {"t274nba": {r["wall_id"]: r for r in _rows(T274_NBA)},"v2": v2, "v4": {r["wall_id"]: r for r in _rows(V4)}, "t274": t274, "t261": dict(t261),
            "sunk": dict(sunk), "ohb": {r["opening_id"]: r for r in _rows(OHB)}, "rd": Readings(v2, t274, fill)}


def line_check(entries):
    """per V3.0.26 MAS.BLOCK line: the merged declared figures vs the rule's sums of its reproduced walls."""
    lba = {r["line_id"]: r for r in _rows(LBA)}
    out = {}
    by = defaultdict(list)
    for e in entries:
        if e["version"] == "ARCH_TAKEOFF_V3.0.26" and e["item_code"] == "MAS.BLOCK":
            by[e["line_id"]].append(e)
    for lid, es in sorted(by.items()):
        r = lba.get(lid, {})
        det = sum(float(r.get(k) or 0) for k in ("verified", "drawing_confirmed", "owner_approved"))
        parts = float(r.get("established_parts") or 0)
        rule_det = rule_parts = 0.0
        n_rep = n_spec = 0
        for e in es:
            v = (e.get("rule_result") or {}).get("value")
            if e["class"] == "A-REPRODUCED":
                n_rep += 1
            elif e["class"] == "A-SPECIFIED":
                n_spec += 1
            if e["class"] == "A-REPRODUCED" and v is not None:
                if e["action"] == "ESTABLISHED PART + HELD":
                    rule_parts += v
                else:
                    rule_det += v
        out[lid] = {"floor": es[0]["floor"], "thickness_m": es[0]["thickness_m"], "walls": len(es),
                    "reproduced": n_rep, "specified": n_spec, "declared_determinate_m2": round(det, 4),
                    "declared_established_parts_m2": round(parts, 4), "rule_determinate_m2": round(rule_det, 4),
                    "rule_established_parts_m2": round(rule_parts, 4),
                    "all_walls_reproduced": n_spec == 0}
        if n_spec == 0:
            for k, a, b in (("determinate", det, rule_det), ("parts", parts, rule_parts)):
                out[lid][f"{k}_diff_pct"] = None if a == 0 else round(100 * (b - a) / a, 4)
    return out


def build(cfg=None):
    cens, docs = census()
    cfg = load_cfg(cfg)
    src = sources()
    entries = []
    entries += wall_entries(cfg, docs["ARCH_TAKEOFF_V3.0.26"], src)
    entries += parapet_entries(cfg, docs["ARCH_TAKEOFF_V3.0.23"])
    entries += fence_entries(docs["ARCH_TAKEOFF_V3.0.35"])
    entries += trace_entries(docs["ARCH_TAKEOFF_V3.0.19"], src["ohb"])
    counts, by_ver = defaultdict(int), defaultdict(lambda: defaultdict(int))
    for e in entries:
        counts[e["class"]] += 1
        by_ver[e["version"]][e["class"]] += 1
    mas = [e for e in entries if e["version"] == "ARCH_TAKEOFF_V3.0.26" and e["item_code"] == "MAS.BLOCK"]
    rel = [e for e in mas if e["class"] == "A-REPRODUCED" and e["patch"]["carried"] is not None]
    return {
        "schema": "T449_CORRECTION_REGISTER_V1", "round": "3 BLOCKWORK",
        "candidate_of_record": "ARCH_TAKEOFF_V3.0.44 (inputs as research/agents_t422/v3044_run.py)",
        "project_config": {"file": str(FACTS.relative_to(ROOT)), "project_id": cfg.project_id,
                           "config_version": cfg.config_version, "content_sha256": cfg.content_sha256,
                           "also": str(CONCRETE_FACTS.relative_to(ROOT)) + " (PARAPET.RC_UPSTAND.MIN_ABOVE_SLAB)"},
        "rules_module": {"file": "engine/source/blockwork_basis_rules_v1.py", "version": R.RULE_VERSION},
        "census": cens,
        "counts": dict(sorted(counts.items())),
        "by_version": {k: dict(sorted(v.items())) for k, v in sorted(by_ver.items())},
        "mas_block": {"walls": len(mas),
                      "by_state": {k: sum(e["action"] == k for e in mas) for k in sorted({e["action"] for e in mas})},
                      "reproduced_with_figure": len(rel),
                      "carried_m2": round(math.fsum(e["patch"]["carried"] for e in rel), 4),
                      "rule_m2": round(math.fsum(e["rule_result"]["value"] for e in rel), 4),
                      "max_abs_residual_m2": round(max((abs(e.get("carried_minus_rule_m2") or 0) for e in rel),
                                                       default=0.0), 6)},
        "lines": line_check(entries),
        "fact_usage": fact_usage(entries),
        "not_declared": {
            F_ANNEX: "owner Q-54 B: HOLD until a document makes +4.30 the structural slab; every annex wall stays "
                     "HELD (reproduced as HELD by the rule)",
            "MAS.BLACK_BLOCK_MODULE_15CM": "no candidate masonry line counts blocks (the T-448 / T-453 material "
                                           "ledger does, beside the candidate)"},
        "out_of_scope": {
            "ARCH_TAKEOFF_V3.0.4": "its inputs are the T-167 profile-audit run files; arch_v304 makes no masonry line",
            "route G masonry": "the released route's blockwork lines are BLOCKED_RFI blank on the candidate since "
                               "V3.0.15 (no per-project input)"},
        "entries": entries,
    }


CSV_COLS = ("version", "line_id", "element_id", "item_code", "action", "class", "rule", "patch", "rule_state",
            "rule_value", "rule_upper_or_high", "carried_minus_rule_m2", "facts_used", "residual_named",
            "not_reproduced")


def to_csv(reg):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_COLS)
    for e in reg["entries"]:
        rr = e.get("rule_result") or {}
        w.writerow([e["version"], e.get("line_id") or "", e.get("element_id") or "", e.get("item_code") or "",
                    e["action"], e["class"], e.get("rule") or "", json.dumps(e["patch"], ensure_ascii=False,
                                                                             sort_keys=True),
                    rr.get("state", ""), rr.get("value", e.get("rule_value", "")),
                    rr.get("upper_m2", rr.get("high", "")), e.get("carried_minus_rule_m2", ""),
                    ";".join(rr.get("facts_used", [])), e.get("residual_named", ""), e.get("not_reproduced", "")])
    return buf.getvalue()


def write_facts(path):
    reg = build(cfg=_boot_cfg())
    data = declared_facts(defaultdict(list, reg["fact_usage"]))
    parse_project_config(data)
    Path(path).write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--facts-out" in args:
        i = args.index("--facts-out")
        write_facts(args[i + 1])
        del args[i:i + 2]
    reg = build()
    if args:
        out = Path(args[0])
        out.mkdir(parents=True, exist_ok=True)
        (out / "CORRECTION_REGISTER_BLOCKWORK_T449.json").write_text(
            json.dumps(reg, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        (out / "CORRECTION_REGISTER_BLOCKWORK_T449.csv").write_text(to_csv(reg), encoding="utf-8")
    print(json.dumps({k: reg[k] for k in ("counts", "by_version", "mas_block")}, indent=1))
