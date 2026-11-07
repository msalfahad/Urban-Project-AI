"""T-599: the column-beam joint ownership convention UP-CONC-JOINT-001 1.0.0 (rules/conventions/URBAN_CONVENTIONS_1.0.0.json,
LEAD_ADOPTED under owner Q-62 A, every villa) - its geometric ledger, its provenance check, and the restatement of the
T-590 structural RULE_DIFF rows on it.

The rule (see the record for the full text): at every column head the COLUMN line owns the 3-D intersection of the
column prism (base -> slab top) with each beam prism framing into it; every beam is billed net of every column solid
it meets (face to face when square, clipped by the column outline when oblique); a planted column starts on its
supporting beam's top and cuts nothing of it. Each joint once: never in two lines, never in none. A plan overlap with
no vertical overlap is not a joint and deducts nothing.

    python3 -I research/agents_t599/t599_joint_rule.py --write     out/T599_JOINT_RULE_RESTATEMENT.json / .md
    python3 -I research/agents_t599/t599_joint_rule.py --check     exit 1 when the committed outputs differ

No private input is read; the restatement reads only the committed T-590 audit output and the repository registers.
Nothing is released and no quantity moves: a restatement is a statement-level class label with every delta unchanged.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "agents_t590"))
import t590_rules as R590  # noqa: E402  (merged T-590, read only)

D = Decimal
RULE_ID = "UP-CONC-JOINT-001"
RULE_VERSION = "1.0.0"
RULE_FILE = ROOT / "rules" / "conventions" / "URBAN_CONVENTIONS_1.0.0.json"
RULES_INDEX = ROOT / "docs" / "RULES_INDEX.md"
T590_OUT = ROOT / "research" / "agents_t590" / "out" / "T590_RULE_DIFF_PROVENANCE.json"
OUT = HERE / "out"
JSON_OUT = OUT / "T599_JOINT_RULE_RESTATEMENT.json"
MD_OUT = OUT / "T599_JOINT_RULE_RESTATEMENT.md"
TOL = 1e-9


class JointRuleError(ValueError):
    """A joint ledger or a citation the rule refuses."""


# ===================================================================================== the rule record ==========
def convention_index(path: Path | None = None) -> dict[str, dict]:
    """rule id -> {'version', 'status', 'library'} from the generated docs/RULES_INDEX.md 'Convention records'
    sections (written by tools/codemap.py from rules/conventions/)."""
    text = (path or RULES_INDEX).read_text(encoding="utf-8")
    out: dict[str, dict] = {}
    lib = None
    for line in text.splitlines():
        if line.startswith("## "):
            m = re.match(r"^## Convention records `([^`]+)`", line)
            lib = m.group(1) if m else None
            continue
        if lib is None:
            continue
        m = re.match(r"^\| ((?:UP|PS)-[A-Z0-9-]+-\d{3}) \| ([0-9.]+) \| ([A-Z_]+) \|", line)
        if m:
            out[m.group(1)] = {"version": m.group(2), "status": m.group(3), "library": lib}
    return out


def load_rule(path: Path | None = None, rule_id: str = RULE_ID) -> dict:
    d = json.loads((path or RULE_FILE).read_text(encoding="utf-8"))
    rec = [r for r in d.get("records", []) if r.get("rule_id") == rule_id]
    if len(rec) != 1:
        raise JointRuleError(f"{rule_id}: expected one record in {path or RULE_FILE}, found {len(rec)}")
    r = rec[0]
    if r.get("convention", {}).get("owner_element") != "COLUMN":
        raise JointRuleError(f"{rule_id}: this ledger implements the COLUMN-owns convention only")
    if r.get("owner_approved") is not False or r.get("status") != "LEAD_ADOPTED":
        raise JointRuleError(f"{rule_id}: status must be LEAD_ADOPTED and not owner-approved (Q-62 A delegation)")
    return r


def require_indexed(rule_id: str, version: str, index: dict[str, dict]) -> dict:
    """A row may cite the convention only when docs/RULES_INDEX.md lists that id at that version."""
    rec = index.get(rule_id)
    if rec is None:
        raise JointRuleError(f"{rule_id}: not in docs/RULES_INDEX.md (no recorded rule version: the row stays UNRESOLVED)")
    if rec["version"] != version:
        raise JointRuleError(f"{rule_id}: RULES_INDEX lists {rec['version']}, the row cites {version}")
    return rec


# ======================================================================================== the ledger =============
def _poly(pts) -> Polygon:
    p = Polygon(pts)
    if not p.is_valid or p.area <= 0:
        raise JointRuleError(f"invalid outline {pts}")
    return p


def _norm(members, kind):
    out = []
    seen = set()
    for m in members:
        if m["id"] in seen:
            raise JointRuleError(f"{kind} {m['id']} listed twice")
        seen.add(m["id"])
        for k in ("z0", "z1"):
            if m.get(k) is None:
                raise JointRuleError(f"{kind} {m['id']}: {k} not established (the joint stays HELD, never 0)")
        z0, z1 = float(m["z0"]), float(m["z1"])
        if z1 <= z0:
            raise JointRuleError(f"{kind} {m['id']}: top {z1} not above base {z0}")
        out.append({"id": m["id"], "poly": _poly(m["outline"]), "z0": z0, "z1": z1})
    return out


def joint_ledger(columns: list[dict], beams: list[dict]) -> dict:
    """Columns and beams as vertical prisms {'id', 'outline': [(x, y), ...] in m, 'z0', 'z1' in m}; a column's z1 is
    the slab top it carries (UP-CONC-JOINT-001), a planted column's z0 is its supporting beam's top. -> per joint the
    3-D intersection (plan intersection x vertical overlap) owned by the column; column lines gross; beam lines net of
    every column solid; the union check (billed sum = union of all solids, by exact horizontal slicing)."""
    cols, bms = _norm(columns, "column"), _norm(beams, "beam")
    joints = []
    for c in cols:
        for b in bms:
            a = c["poly"].intersection(b["poly"]).area
            h = min(c["z1"], b["z1"]) - max(c["z0"], b["z0"])
            if a > TOL and h > TOL:
                joints.append({"joint": f"{c['id']}x{b['id']}", "column": c["id"], "beam": b["id"],
                               "plan_m2": round(a, 9), "height_m": round(h, 9), "m3": round(a * h, 9),
                               "owner": c["id"]})
            elif a > TOL:
                joints.append({"joint": f"{c['id']}x{b['id']}", "column": c["id"], "beam": b["id"],
                               "plan_m2": round(a, 9), "height_m": 0.0, "m3": 0.0, "owner": None,
                               "note": "plan overlap without vertical overlap: not a joint, nothing deducted"})
    # beam-beam overlap outside every column is another junction (out of this rule's scope): refused, never guessed
    for i, b1 in enumerate(bms):
        for b2 in bms[i + 1:]:
            if min(b1["z1"], b2["z1"]) - max(b1["z0"], b2["z0"]) <= TOL:
                continue
            ov = b1["poly"].intersection(b2["poly"])
            for c in cols:
                if min(c["z1"], b1["z1"], b2["z1"]) - max(c["z0"], b1["z0"], b2["z0"]) > TOL:
                    ov = ov.difference(c["poly"])
            if ov.area > 1e-7:
                raise JointRuleError(f"beams {b1['id']} / {b2['id']} overlap outside every column "
                                     f"({ov.area:.6f} m2 in plan): a beam-beam junction is outside UP-CONC-JOINT-001")
    lines = {}
    for c in cols:
        lines[c["id"]] = {"kind": "COLUMN", "m3": c["poly"].area * (c["z1"] - c["z0"]),
                          "owns": [j["joint"] for j in joints if j["owner"] == c["id"]]}
    for b in bms:
        # net = beam minus its intersection with the UNION of the columns over each vertical band
        lines[b["id"]] = {"kind": "BEAM", "m3": _prism_minus(b, cols), "owns": []}
    billed = sum(v["m3"] for v in lines.values())
    union = _union_volume(cols + bms)
    if abs(billed - union) > 1e-7:
        raise JointRuleError(f"billed {billed:.9f} m3 != union of solids {union:.9f} m3 (double count or gap)")
    claims = {k: set(v["owns"]) for k, v in lines.items()}
    check_claims([j["joint"] for j in joints if j["owner"]], claims)
    return {"rule": f"{RULE_ID}@{RULE_VERSION}", "joints": joints,
            "lines": {k: {"kind": v["kind"], "m3": round(v["m3"], 9), "owns": v["owns"]} for k, v in lines.items()},
            "billed_m3": round(billed, 9), "union_m3": round(union, 9),
            "joint_m3": round(sum(j["m3"] for j in joints), 9)}


def _bands(members):
    zs = sorted({m["z0"] for m in members} | {m["z1"] for m in members})
    return list(zip(zs, zs[1:]))


def _prism_minus(b, cols):
    vol = 0.0
    for z0, z1 in _bands([b] + cols):
        if z0 < b["z0"] - TOL or z1 > b["z1"] + TOL:
            continue
        cut = [c["poly"] for c in cols if c["z0"] <= z0 + TOL and c["z1"] >= z1 - TOL]
        area = b["poly"].difference(unary_union(cut)).area if cut else b["poly"].area
        vol += area * (z1 - z0)
    return vol


def _union_volume(members):
    vol = 0.0
    for z0, z1 in _bands(members):
        polys = [m["poly"] for m in members if m["z0"] <= z0 + TOL and m["z1"] >= z1 - TOL]
        if polys:
            vol += unary_union(polys).area * (z1 - z0)
    return vol


def check_claims(joints: list[str], claims: dict[str, set[str]]) -> None:
    """Each joint is billed by exactly one line: in two lines -> refused (double count); in none -> refused (gap)."""
    owners: dict[str, list[str]] = {j: [] for j in joints}
    for line, js in claims.items():
        for j in js:
            if j not in owners:
                raise JointRuleError(f"line {line} claims {j}, which is not a joint of the ledger")
            owners[j].append(line)
    for j, ls in owners.items():
        if len(ls) > 1:
            raise JointRuleError(f"joint {j} billed in both {sorted(ls)}: each joint once")
        if not ls:
            raise JointRuleError(f"joint {j} billed in neither line: a gap is never closed by a zero")


# ============================================================================== the T-590 restatement ===========
class Registers(R590.Registers):
    """R-T590-1 registers plus the convention library: a convention record listed in docs/RULES_INDEX.md is a RULE
    with status LEAD_ADOPTED (labelled, never OWNER_APPROVED); any other UP-* id goes to R-T591-1 (a)."""

    def __init__(self, *a, conventions=None, **k):
        super().__init__(*a, **k)
        self.conventions = conventions if conventions is not None else convention_index()

    def judge(self, src):
        if src in self.conventions:
            return "RULE", self.conventions[src]["status"]
        return super().judge(src)


REQUIREMENT_ONLY = {"Q-62": "the joint is measured exactly once under ONE project convention; the owner element is "
                            "chosen by the recorded convention UP-CONC-JOINT-001"}
TRACED = ["Q-62", RULE_ID,
          "REGISTER:ELEMENT_REGISTER 'COLUMN-BEAM JOINT' (Lead 2026-11-07 12:30, corrected: the COLUMN owns the joint "
          "to the slab top, beam face to face; cites T-599)",
          "REGISTER:ERS s.7 rows 2026-10-31 (ADOPTED) and 2026-11-07 (ADOPTED)"]
UNTRACED_REASON = ("F-C-T590-2 (Checker 2026-11-07): the GF 'UNTRACED -> GF B7' row is not a joint convention (it was "
                   "UNRESOLVED in T-545 before T-587 F-T587-2; THROUGH_SUPPORT accepted on 2 / 14 piece ends only): "
                   "counted apart, stays UNRESOLVED, traced in T-600")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _tab(items):
    return {u: {o: {"n": b["n"], "signed": str(b["signed"]), "gross": str(b["gross"])} for o, b in sorted(v.items())}
            for u, v in sorted(R590.R591.per_unit(items).items())}


def restate(t590: dict, reg: Registers, index: dict[str, dict]) -> dict:
    require_indexed(RULE_ID, RULE_VERSION, index)
    rows, head_b, head_a, all_b, all_a = [], [], [], [], []
    for r in t590["rows"]:
        if r["unit"] != "m3":
            continue
        d = D(r["delta"])
        headline = r["live"] and not r["nested_in"]
        untraced = "UNTRACED" in r["name"]
        if untraced:
            out = {"outcome": "UNRESOLVED_APART", "class_after": "UNRESOLVED", "cited": [], "reason": UNTRACED_REASON}
        else:
            if not ("JOINT_HEAD" in r["name"] or "THROUGH_SUPPORT" in r["name"]):
                raise JointRuleError(f"{r['section_id']} row {r['row']}: not a column-beam joint row")
            row = {"class": "RULE_DIFFERENCE", "delta": r["delta"], "name": r["name"],
                   "note": f"joint owner per {RULE_ID}@{RULE_VERSION} (column to the slab top, beam net)",
                   "source": f"{RULE_ID}"}   # R-T591-1 (d): the citation is the rule; the method record is kept apart
            rec = R590.classify(reg, row, TRACED, r["his_side"])
            if rec["outcome"] != "SOURCED":
                raise JointRuleError(f"{r['section_id']} row {r['row']}: expected SOURCED, got {rec['outcome']}")
            out = {"outcome": "SOURCED", "class_after": "RULE_DIFFERENCE", "cited": rec["cited_valid"],
                   "basis_label": "LEAD_ADOPTED under Q-62 A (delegated choice; not owner-approved)",
                   "our_side": rec["sources"]}
        rows.append({"level": r["level"], "section_id": r["section_id"], "row": r["row"], "name": r["name"],
                     "delta_m3": r["delta"], "live": r["live"], "nested_in": r["nested_in"],
                     "superseded_by": r["superseded_by"], "reading_of_record": r["reading_of_record"],
                     "headline": headline, "t590_class": r["class_after"], "measured_record": r["row_source"], "his_side": r["his_side"], **out})
        all_b.append(("m3", "UNRESOLVED", d))
        all_a.append(("m3", out["class_after"], d))
        if headline:
            head_b.append(("m3", "UNRESOLVED", d))
            head_a.append(("m3", out["class_after"], d))
    sb, sa = sum(x[2] for x in head_b), sum(x[2] for x in head_a)
    gb, ga = sum(abs(x[2]) for x in head_b), sum(abs(x[2]) for x in head_a)
    if sb != sa or gb != ga or sum(x[2] for x in all_b) != sum(x[2] for x in all_a):
        raise JointRuleError("a restatement moved a quantity")
    pair = {}
    for r in rows:
        if not r["headline"] or r["outcome"] != "SOURCED":
            continue
        st = r["name"].split()[0] if r["name"].split()[0] in ("GF:", "1F:", "2F:") else r["name"].split()[1]
        st = st.rstrip(":")
        b = pair.setdefault(st, {"beam_THROUGH_SUPPORT_m3": D(0), "column_JOINT_HEAD_m3": D(0)})
        b["beam_THROUGH_SUPPORT_m3" if "THROUGH_SUPPORT" in r["name"] else "column_JOINT_HEAD_m3"] += D(r["delta_m3"])
    pair = {k: {**{n: str(v) for n, v in b.items()},
                "net_m3": str(b["beam_THROUGH_SUPPORT_m3"] + b["column_JOINT_HEAD_m3"])} for k, b in sorted(pair.items())}
    # matched part of each storey pair = the convention (signed 0: the same joint under the other owner); the rest
    # of the beam row is a residual of its own (UNRESOLVED, T-600), never hidden inside the RULE_DIFFERENCE
    split, conv_g, resid_s = {}, D(0), D(0)
    for k, v in pair.items():
        b, c = D(v["beam_THROUGH_SUPPORT_m3"]), D(v["column_JOINT_HEAD_m3"])
        if b < 0 or c > 0:
            raise JointRuleError(f"{k}: pair signs not beam + / column - (reference - engine): no matched convention")
        m = min(b, -c)
        split[k] = {"convention_matched_m3_each_side": str(m), "convention_signed_m3": str(m - m),
                    "residual_unresolved_m3": str(b + c)}
        conv_g += 2 * m
        resid_s += b + c
    apart = sum((D(r["delta_m3"]) for r in rows if r["headline"] and r["outcome"] == "UNRESOLVED_APART"), D(0))
    if resid_s + apart != sa:
        raise JointRuleError(f"headline by cause {resid_s} + {apart} != headline signed {sa}")
    n_joint = sum(1 for r in rows if r["outcome"] == "SOURCED")
    return {
        "schema": "URBAN_T599_JOINT_RULE_RESTATEMENT_V1",
        "rule": f"{RULE_ID}@{RULE_VERSION} (rules/conventions/URBAN_CONVENTIONS_1.0.0.json, LEAD_ADOPTED under Q-62 A)",
        "rules_index": index[RULE_ID],
        "input": "research/agents_t590/out/T590_RULE_DIFF_PROVENANCE.json (T-590 MERGED 7855b9b2): its 38 m3 rows",
        "pins": {k: _sha(ROOT / k) for k in ("research/agents_t590/out/T590_RULE_DIFF_PROVENANCE.json",
                                             "rules/conventions/URBAN_CONVENTIONS_1.0.0.json")},
        "rows_m3": len(rows), "joint_rows_sourced": n_joint,
        "unresolved_apart": [f"{r['section_id']} row {r['row']} {r['delta_m3']} m3" for r in rows
                             if r["outcome"] == "UNRESOLVED_APART"],
        "headline_before": _tab(head_b), "headline_after": _tab(head_a),
        "all_rows_before": _tab(all_b), "all_rows_after": _tab(all_a),
        "headline_signed_m3_unchanged": str(sa), "headline_gross_m3_unchanged": str(ga),
        "column_beam_pair_V7_m3_reference_minus_engine": pair,
        "headline_by_cause_m3": {
            "RULE_DIFFERENCE_SOURCED_matched_joint": {"signed": "0", "gross": str(conv_g)},
            "UNRESOLVED_pair_residual_T600": {"signed": str(resid_s), "gross": str(resid_s)},
            "UNRESOLVED_untraced_apart": {"signed": str(sum(D(r["delta_m3"]) for r in rows if r["headline"]
                                                            and r["outcome"] == "UNRESOLVED_APART"))},
            "check_signed_total": str(resid_s + sum(D(r["delta_m3"]) for r in rows if r["headline"]
                                                    and r["outcome"] == "UNRESOLVED_APART"))},
        "pair_split": split,
        "pair_note": ("F-C-T590-1 restated on the V7 reading (T-545@V7 headline rows + T-551 column rows; sign "
                      "reference - engine as in the statement): the per-storey pair does not cancel; the net is not "
                      "a convention and stays its own residual (T-600). T-590's note quoted the pre-V7 2F beam "
                      "-0.532760 and printed the GF / 1F nets with the opposite sign (-0.620464 / -1.208362): with "
                      "the statement sign the reference carries MORE concrete in the pair (beam through-support > "
                      "column joint head) on every storey"),
        "rows": rows,
        "released_quantities_changed": 0,
    }


def build() -> dict:
    index = convention_index()
    load_rule()
    t590 = json.loads(T590_OUT.read_text(encoding="utf-8"))
    reg = Registers(requirement_only=REQUIREMENT_ONLY, conventions=index)
    return restate(t590, reg, index)


def to_markdown(o: dict) -> str:
    L = ["# T-599 column-beam joint rule: T-590 rows restated (generated)", "",
         f"Rule {o['rule']}; RULES_INDEX: {o['rules_index']}. Input: {o['input']}.", "",
         f"m3 rows {o['rows_m3']}: {o['joint_rows_sourced']} joint rows UNRESOLVED -> RULE_DIFFERENCE SOURCED; "
         f"apart (stays UNRESOLVED): {', '.join(o['unresolved_apart'])}.", "",
         "| | before (T-590) | after (T-599) |", "|---|---|---|",
         f"| headline | {json.dumps(o['headline_before']['m3'])} | {json.dumps(o['headline_after']['m3'])} |",
         f"| all rows (nested / superseded audited beside) | {json.dumps(o['all_rows_before']['m3'])} | "
         f"{json.dumps(o['all_rows_after']['m3'])} |", "",
         f"Headline signed {o['headline_signed_m3_unchanged']} m3 / gross {o['headline_gross_m3_unchanged']} m3 unchanged.",
         "", f"Headline by cause (m3): {json.dumps(o['headline_by_cause_m3'])}.",
         "", "## Column / beam pair, V7 reading (m3, reference - engine)", "",
         "| storey | beam THROUGH_SUPPORT | column JOINT_HEAD | net (residual, T-600) |", "|---|---|---|---|"]
    for k, v in o["column_beam_pair_V7_m3_reference_minus_engine"].items():
        L.append(f"| {k} | {v['beam_THROUGH_SUPPORT_m3']} | {v['column_JOINT_HEAD_m3']} | {v['net_m3']} |")
    L += ["", o["pair_note"], "", "## Rows", "", "| section | row | name | m3 | headline | outcome |", "|---|---|---|---|---|---|"]
    for r in o["rows"]:
        L.append(f"| {r['section_id']} | {r['row']} | {r['name']} | {r['delta_m3']} | {r['headline']} | {r['outcome']} |")
    return "\n".join(L) + "\n"


def main(argv) -> int:
    o = build()
    js = json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n"
    md = to_markdown(o)
    if "--write" in argv:
        OUT.mkdir(exist_ok=True)
        JSON_OUT.write_text(js, encoding="utf-8")
        MD_OUT.write_text(md, encoding="utf-8")
        print(f"written {JSON_OUT.name}, {MD_OUT.name}")
        return 0
    if "--check" in argv:
        ok = JSON_OUT.exists() and JSON_OUT.read_text(encoding="utf-8") == js and MD_OUT.read_text(encoding="utf-8") == md
        print("T599 outputs current" if ok else "T599 outputs STALE")
        return 0 if ok else 1
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
