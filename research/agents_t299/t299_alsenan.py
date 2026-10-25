"""T-299 Alsenan read-only reinforcement ledger reconciliation (development villa; every rule in t299_ledger is generic).

    python3 -I research/agents_t299/t299_alsenan.py            # writes RECON_T299.csv + RECON_SUMMARY_T299.json
    python3 -I research/agents_t299/t299_alsenan.py --check    # rebuilds in memory, compares with the committed files

Inputs (all merged research records; nothing private is read, nothing in engine/ or tools/ is imported):
  research/alsenan_column_rebar_s3/COLUMN_RELEASE_REGISTER.json + COLUMN_MAIN_BAR_REGISTER.json   (S3 column ledger)
  research/alsenan_column_rebar_s3_1/COLUMN_RELEASE_REGISTER.json                                (S3.1, alternative round)
  research/agents_t280/CORE_DATUM_T280.json                                                      (column foundation cores)
  research/agents_t273/LAP_ROWS_T273.csv + summary.json                                          (laps; restated nets)
  research/agents_t265/LEDGER_T265.csv, research/agents_t272/LEDGER_T272.csv                     (ground beams)
  research/agents_t138/T138_MEMBERS.csv                                                          (earlier GB / strap ledger)
  research/agents_t149/T149_BEAMS.csv + T149_SUMMARY.json                                        (superstructure beams)
  research/agents_t299/ROUTE_G_ITEMS_T299.csv  (t299_route_g_extract.py: route G, V6 conventions, no profile)
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))

from t299_ledger import (LedgerError, Row, duplicates, family_totals, kg_to_t, link_count,  # noqa: E402
                         source_residuals, validate)

S3, S31, T280, T265, T272, T273, T138, T149, RG = ("S3", "S3.1", "T-280", "T-265", "T-272", "T-273", "T-138", "T-149",
                                                    "ROUTE_G")
OUT_CSV = HERE / "RECON_T299.csv"
OUT_JSON = HERE / "RECON_SUMMARY_T299.json"
F = lambda v: None if v in ("", None) else float(v)  # noqa: E731


def _csv(p):
    with open(p, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------------- columns ----

S3_STATUS = {"VERIFIED": "SOURCE_LABEL_VERIFIED", "LOWER_BOUND": "LOWER_BOUND", "PROVISIONAL": "PROVISIONAL",
             "BLOCKED": "HELD"}
ROUTE_G_NO_COLUMN_STEEL = ("route G carries no column reinforcement at all (every COLUMNS component MISSING_DATA, "
                           "rebar_completeness); no overlap with route G")


def columns(rg_rows):
    rows = []
    s3 = _json(RES / "alsenan_column_rebar_s3/COLUMN_RELEASE_REGISTER.json")
    s31 = _json(RES / "alsenan_column_rebar_s3_1/COLUMN_RELEASE_REGISTER.json")
    mb = _json(RES / "alsenan_column_rebar_s3/COLUMN_MAIN_BAR_REGISTER.json")["rows"]
    t280 = _json(RES / "agents_t280/CORE_DATUM_T280.json")
    core_part = {r["chain_id"]: r["part_id"] for r in mb if r["floor"] == "FOUNDATION"}
    t280_by_part = {core_part[r["chain_id"]]: r for r in t280["rows"]}
    s31_by_part = {r["part_id"]: r for r in s31["rows"]}
    s3_parts = {r["part_id"] for r in s3["rows"]}

    def bg(r):
        return f'{r["component"]}:{r["part_id"].split("|")[1]}'

    def el(r):
        return r["part_id"].split("|")[0]

    for r in s3["rows"]:
        pid = r["part_id"]
        alt = s31_by_part.get(pid)
        base = dict(family="COLUMNS", element_id=el(r), bar_group=bg(r), source=S3, source_kg=r["kg"],
                    evidence=f"S3 COLUMN_RELEASE_REGISTER part {pid}; occurrence {r['occurrence_id']}")
        if pid in t280_by_part:
            rows.append(Row(row_id=f"S3|{pid}", status="CONVENTION", relation="REPLACED_BY",
                            relation_to=(f"T280|{t280_by_part[pid]['chain_id']}",),
                            reason="label LOWER_BOUND restated CONVENTION_NOT_A_BOUND by T-280 (footing underside put at "
                                   "the formation limit, the printed 0.17 m underlay omitted)", **base))
            if alt is not None:
                rows.append(Row(row_id=f"S3.1|{pid}", family="COLUMNS", element_id=el(alt), bar_group=bg(alt),
                                source=S31, source_kg=alt["kg"], status="CONVENTION", relation="REPLACED_BY",
                                relation_to=(f"T280|{t280_by_part[pid]['chain_id']}",),
                                reason="alternative unit-mass round of the S3 row T-280 restates",
                                evidence=f"S3.1 COLUMN_RELEASE_REGISTER part {pid}"))
            continue
        st = S3_STATUS[r["release_state"]]
        if st == "HELD":
            rows.append(Row(row_id=f"S3|{pid}", status="HELD", relation="HELD",
                            reason=f"S3 BLOCKED (source kg {r['kg']} is a modelled value, not a quantity); "
                                   + ROUTE_G_NO_COLUMN_STEEL, **base))
            if alt is not None:
                rows.append(Row(row_id=f"S3.1|{pid}", family="COLUMNS", element_id=el(alt), bar_group=bg(alt),
                                source=S31, source_kg=alt["kg"], status="HELD", relation="HELD",
                                reason="S3.1 BLOCKED, alternative round of a held S3 row",
                                evidence=f"S3.1 COLUMN_RELEASE_REGISTER part {pid}"))
            continue
        grp = f"COL:{pid}"
        shared = ("the same bar group: S3.1 is the alternative unit-mass round (d^2/162) of S3 (exact density); "
                  "S3 counted because T-280 restates S3's kg; S3.1 never summed")
        flags = ()
        if r["part_id"].endswith("|ANCHORAGE_TOP_STOPPED") or "ANCHORAGE_TOP_STOPPED" in pid:
            flags = ("T280_STOPPING_COLUMN_TOP_DATUM_HELD",)
        rows.append(Row(row_id=f"S3|{pid}", status=st, relation="OVERLAPS" if alt else "INDEPENDENT",
                        quantity_kg=r["kg"], counted=True, overlap_group=grp if alt else "",
                        shared_part=shared if alt else "", reason=ROUTE_G_NO_COLUMN_STEEL, flags=flags, **base))
        if alt is not None:
            ast = S3_STATUS[alt["release_state"]]
            rows.append(Row(row_id=f"S3.1|{pid}", family="COLUMNS", element_id=el(alt), bar_group=bg(alt), source=S31,
                            source_kg=alt["kg"], status=ast if ast != "HELD" else "HELD",
                            relation="OVERLAPS", quantity_kg=None if ast == "HELD" else alt["kg"], counted=False,
                            overlap_group=grp, shared_part=shared,
                            reason="alternative ledger of the S3 bar group; never added to S3",
                            evidence=f"S3.1 COLUMN_RELEASE_REGISTER part {pid}"))
    for r in s31["rows"]:
        if r["part_id"] in s3_parts:
            continue
        rows.append(Row(row_id=f"S3.1|{r['part_id']}", family="COLUMNS", element_id=el(r), bar_group=bg(r), source=S31,
                        source_kg=r["kg"], status="HELD", relation="HELD",
                        reason=f"S3.1-only part ({r['release_state']}: section transition with no ST7757 transition "
                               "detail); no S3 counterpart",
                        evidence=f"S3.1 COLUMN_RELEASE_REGISTER part {r['part_id']}"))
    for pid, t in t280_by_part.items():
        rep = (f"S3|{pid}",) + ((f"S3.1|{pid}",) if pid in s31_by_part else ())
        if t["status"] == "LOWER_BOUND_RESTATED":
            rows.append(Row(row_id=f"T280|{t['chain_id']}", family="COLUMNS", element_id=pid.split("|")[0],
                            bar_group="MAIN_BARS:MAIN_CORE", source=T280, source_kg=t["lower_kg"],
                            status="LOWER_BOUND", relation="REPLACES", quantity_kg=t["lower_kg"], counted=True,
                            replaces=rep,
                            reason=f"T-280 restates the core on the printed chain: {t['lower']['reason']}; upper "
                                   f"{t['upper']}; datum = formation limit + p.13 underlay 0.17 + H",
                            evidence=f"T-280 chain {t['chain_id']}; footing {t['footing_ref']}; ST7757.pdf p.9 / p.13"))
        else:
            fam = t["support_family"]
            why = {"LIFT_PIT_FF": "PIT_DEPTH_NOT_PRINTED (p.14, D-43)", "UNBOUND": "SUPPORT_NOT_BOUND (STR-COL-001)"}.get(
                fam, "TOP_DATUM_NOT_PRINTED (stopping column ends in its closing member)")
            rows.append(Row(row_id=f"T280|{t['chain_id']}", family="COLUMNS", element_id=pid.split("|")[0],
                            bar_group="MAIN_BARS:MAIN_CORE", source=T280, source_kg=None, status="HELD",
                            relation="REPLACES", replaces=rep,
                            reason=f"T-280 HELD: {why}; the S3 kg is withdrawn, not carried",
                            evidence=f"T-280 chain {t['chain_id']}; footing {t['footing_ref']}"))
    # T-273: aggregate restatement of S3 lap / starter / anchorage by state (no new column bars)
    t273 = _json(RES / "agents_t273/summary.json")
    for c in t273["column_already_carried"]:
        comp, st = c["component"], c["release_state"]
        members = [x for x in rows if x.source == S3 and x.bar_group.startswith(comp + ":")
                   and S3_STATUS.get(st) == x.status or (x.source == S3 and x.bar_group.startswith(comp + ":")
                                                         and st == "BLOCKED" and x.status == "HELD")]
        rows.append(Row(row_id=f"T273|COLUMNS|{comp}|{st}", family="COLUMNS", element_id="COLUMNS (aggregate)",
                        bar_group=f"{comp}:{st}", source=T273, source_kg=c["kg"],
                        status="HELD" if st == "BLOCKED" else S3_STATUS[st],
                        relation="OVERLAPS", quantity_kg=None if st == "BLOCKED" else c["kg"], counted=False,
                        overlap_group=f"T273COL:{comp}:{st}", relation_to=tuple(m.row_id for m in members),
                        shared_part=f"T-273 restates S3's {c['rows']} {comp} rows in state {st} (no new bars); its 70 D "
                                    f"figure {c['kg_at_70d']} kg is a scenario, never an addition",
                        reason="aggregate restatement (owner 2026-10-24 s.6 (2): the 54 column laps stay PROVISIONAL)",
                        association="AGGREGATE", evidence="research/agents_t273/summary.json column_already_carried",
                        source_state="T-273:COLUMN_RESTATEMENT"))
    for it in rg_rows:
        if it["family"] == "COLUMNS" and it["unit"] == "m3":
            rows.append(Row(row_id=f"RG|{it['component_id']}|STEEL", family="COLUMNS", element_id=it["component_id"],
                            bar_group="ALL", source=RG, status="HELD", relation="HELD",
                            reason="route G: no reinforcement item for this column (MISSING_DATA); its bars are only in "
                                   "the S3 / T-280 ledgers", association="SOURCE_BINDING",
                            evidence=it["source"]))
    checks = {"t273_column_restatement": []}
    for x in rows:
        if x.source == T273 and x.family == "COLUMNS":
            got = round(sum(next(y for y in rows if y.row_id == m).source_kg or 0 for m in x.relation_to), 3)
            checks["t273_column_restatement"].append({"row": x.row_id, "t273_kg": x.source_kg, "s3_rows_kg": got,
                                                      "residual_kg": round(got - x.source_kg, 3)})
    named = {S3: s3["totals_kg"]["total"], S31: s31["totals_kg"]["total"], T280: t280["lower_kg_restated_rows"],
             "T-273:COLUMN_RESTATEMENT": round(sum(c["kg"] for c in t273["column_already_carried"]), 3)}
    return rows, named, checks


# --------------------------------------------------------------------------------------------------- ground beams ----

def pair_of(member):
    m = re.match(r"GS[A-Z]?-(?:A-)?(.+)-(\d+)$", member)
    if m:
        return m.group(1).replace("-", "+")
    m = re.search(r"\(([^)]+)\)", member)
    if m:
        return m.group(1).replace("-", "+")
    return None


def t265_pair(member):
    return re.sub(r"#\d+$", "", member).replace("ARC:", "")


def ground_beams(rg_rows):
    rows = []
    L = _csv(RES / "agents_t265/LEDGER_T265.csv")
    T72 = _csv(RES / "agents_t272/LEDGER_T272.csv")
    T73 = _csv(RES / "agents_t273/LAP_ROWS_T273.csv")
    B = _csv(RES / "agents_t138/T138_MEMBERS.csv")
    t265_ids = {}
    pairs265 = defaultdict(list)
    for i, r in enumerate(L):
        rid = f"T265|{r['member']}|{r['component']}"
        t265_ids[(r["member"], r["component"])] = rid
        pairs265[t265_pair(r["member"])].append(rid)
    t273_by = {}
    for r in T73:
        if r["floor"] != "GROUND_BEAM":
            continue
        e, c = r["element"].rsplit(" ", 1)
        t273_by[(e, c)] = r
    # T-138 first (rows to be replaced need ids)
    t138_rows = []
    pair_released_t138 = defaultdict(list)
    for i, r in enumerate(B):
        rid = f"T138|{i:03d}|{r['member']}|{r['component']}"
        kg = F(r["kg"])
        fam = "GROUND_BEAMS" if r["family"] == "GROUND_BEAM" else "GROUND_BEAMS:STRAPS"
        base = dict(row_id=rid, family=fam, element_id=r["member"], bar_group=r["component"], source=T138, source_kg=kg,
                    evidence=f"T-138 T138_MEMBERS.csv row {i + 2}; detail {r['detail'] or '-'}; {r['length_basis']}")
        t138_rows.append((r, base))
        if r["family"] == "GROUND_BEAM" and r["status"].startswith("RELEASED (lower bound)"):
            pair_released_t138[pair_of(r["member"])].append(rid)
    # T-265
    replaced_t138 = {}
    for r in L:
        rid = t265_ids[(r["member"], r["component"])]
        pair = t265_pair(r["member"])
        rep = ()
        if r["component"] in ("TOP", "ALL") and pair in pair_released_t138:
            # the first T-265 row of the pair carries the replacement of every released T-138 face-to-face row
            if pair not in replaced_t138:
                rep = tuple(pair_released_t138[pair])
                replaced_t138[pair] = rid
        base = dict(row_id=rid, family="GROUND_BEAMS", element_id=r["member"], bar_group=r["component"], source=T265,
                    source_kg=F(r["kg"]), evidence=f"T-265 LEDGER_T265.csv ({r['family']}); ST7757.pdf p.13 / p.14; "
                                                    f"runs from T-253 (Checker Gate A)", replaces=rep)
        why_rep = ("T-265 restates the pair on the Checker-verified T-253 geometry (T-265 s.4: T-138 572.500 -> 796.319 kg "
                   "main-house exterior; annex / court pairs downgraded to HELD: CONFLICT / no section)") if rep else ""
        comp = r["component"]
        if comp in ("TOP", "BOTTOM_ROW_1", "BOTTOM_ROW_2", "SIDE"):
            t73 = t273_by.get((r["member"], comp))
            rows.append(Row(status="DRAWING_CONFIRMED_LOWER_BOUND", quantity_kg=F(r["kg"]), counted=True,
                            relation="OVERLAPS" if t73 else "INDEPENDENT",
                            overlap_group=f"GB:{r['member']}|{comp}" if t73 else "",
                            shared_part="the run's net bars: T-273 restates them (net_kg) to count laps; counted here"
                            if t73 else "",
                            reason=("route G has no steel for this member (SH08 band, MISSING_DATA)"
                                    + (f"; {why_rep}" if why_rep else "")), **base))
        elif comp == "STIRRUP_COUNT":
            rows.append(Row(status="COUNT_ONLY", relation="REPLACED_BY", relation_to=(f"T272|{r['member']}",),
                            reason=("count envelope superseded by T-272 r2 (per drawn clear span; T-265 "
                                    + (r["n_bars"] or "no count") + ")" + (f"; {why_rep}" if why_rep else "")), **base))
        elif r["status"].startswith("NO_REBAR"):
            rows.append(Row(status="NOT_REQUIRED", relation="HELD", reason="printed PLAIN concrete: no rebar line",
                            **base))
        else:
            rows.append(Row(status="HELD", relation="HELD",
                            reason=f"T-265 {r['status']}: {r['basis'][:160]}" + (f"; {why_rep}" if why_rep else ""),
                            **base))
    # T-138 rows
    for r, base in t138_rows:
        pair = pair_of(r["member"])
        kg = base["source_kg"]
        st = r["status"]
        if r["family"] == "GROUND_BEAM":
            if st.startswith("RELEASED (lower bound)"):
                if pair in replaced_t138:
                    rows.append(Row(status="LOWER_BOUND", relation="REPLACED_BY", relation_to=(replaced_t138[pair],),
                                    reason="restated by T-265 on the same axis pair", association="AXIS_PAIR",
                                    flags=("PAIR_LEVEL_JOIN",), **base))
                else:
                    rows.append(Row(status="LOWER_BOUND", relation="INDEPENDENT", quantity_kg=kg, counted=True,
                                    reason=f"interior / non-exterior ground beam (detail {r['detail']}): no other "
                                           "ledger carries it; route G has no ground-beam steel on SH08", **base))
            elif "interior column" in st:
                rows.append(Row(status="LOWER_BOUND", relation="INDEPENDENT", quantity_kg=kg, counted=True,
                                reason="bar through an interior column (p.13 continuous band): outside T-265's "
                                       "face-to-face scope; T-273 chain rows restate it (not counted there)",
                                flags=("RESTATED_IN_T273_CHAIN",), **base))
            else:
                rep_by = replaced_t138.get(pair)
                rows.append(Row(status="HELD", relation="HELD",
                                reason=f"T-138 {st[:160]}" + (f"; pair now in T-265 ({rep_by})" if rep_by else ""),
                                **base))
    # straps: T-138 vs route G GROUND_BEAMS (SH10)
    rg_strap = defaultdict(list)
    for it in rg_rows:
        if it["family"] == "GROUND_BEAMS" and it["unit"] == "kg":
            m = re.search(r"mark (SB\d+)", it["source"])
            kind = it["item_id"].split(":")[-2]
            rg_strap[(m.group(1) if m else "?", {"BOT": "BOTTOM", "TOP": "TOP", "STI": "STIRRUP"}[kind])].append(it)
    strap_groups = set()
    for r, base in t138_rows:
        if r["family"] != "STRAP_BEAM":
            continue
        comp = "STIRRUP" if r["component"].startswith("STIRRUP") else r["component"]
        g = f"STRAP:{r['member']}|{comp}" if (r["member"], comp) in rg_strap else ""
        if g:
            strap_groups.add((r["member"], comp))
        released = r["status"].startswith("RELEASED")
        shared = ("the strap's bars between footing faces; route G adds two anchorage lengths by convention "
                  "(BEAM_BAR_ANCHORAGE_D) which T-138 holds as bar ends 40 d .. 70 d (note 9, S9)") if g else ""
        rows.append(Row(status="LOWER_BOUND" if released else "HELD", relation="OVERLAPS" if g else "HELD",
                        quantity_kg=base["source_kg"] if released else None, counted=released, overlap_group=g,
                        shared_part=shared, reason=f"T-138 {r['status'][:160]}" + (f"; {r['held_kg']} kg held"
                                                                                  if r["held_kg"] else ""), **base))
    for (mark, comp), its in rg_strap.items():
        for it in its:
            g = f"STRAP:{mark}|{comp}" if (mark, comp) in strap_groups else ""
            rows.append(Row(row_id=f"RG|{it['item_id']}", family="GROUND_BEAMS:STRAPS", element_id=it["component_id"],
                            bar_group=f"{comp} D{it['dia_mm']}", source=RG, source_kg=F(it["base"]),
                            status="CONVENTION", relation="OVERLAPS" if g else "INDEPENDENT",
                            quantity_kg=F(it["base"]), counted=False, overlap_group=g,
                            shared_part="see the T-138 row of the group" if g else "",
                            reason=f"route G {it['category']} / {it['support']} / blocker {it['blocker']}: "
                                   f"{it['formula']}; low {float(it['low']):.3f} high {float(it['high']):.3f} kg; a "
                                   "PROVISIONAL SUBTOTAL item, never counted", association="SOURCE_BINDING",
                            evidence=it["source"]))
    for it in rg_rows:
        if it["family"] == "GROUND_BEAMS" and it["unit"] == "m3" and it["component_id"].startswith("GROUND_BEAMS:GROUND"):
            rows.append(Row(row_id=f"RG|{it['component_id']}|STEEL", family="GROUND_BEAMS",
                            element_id=it["component_id"], bar_group="ALL", source=RG, status="HELD", relation="HELD",
                            reason="route G: band with no steel item (MISSING_DATA, concrete UNRESOLVED / UNBOUND); "
                                   "the bars of these members are in T-265 / T-138", association="SOURCE_BINDING",
                            evidence=it["source"]))
    # T-272: stirrup counts per drawn clear span (Q-71 applied: no first-link offset printed for ground beams)
    for r in T72:
        rid = f"T272|{r['run']}"
        q71, why = link_count(F(r["length_m"]), F(r["spacing_m"]), None, False)
        rows.append(Row(row_id=rid, family="GROUND_BEAMS", element_id=r["run"], bar_group=f"STIRRUPS d{r['d_mm']}",
                        source=T272, status="HELD", relation="REPLACES",
                        replaces=(t265_ids[(r["run"], "STIRRUP_COUNT")],),
                        reason=(f"count {r['count_status']} in [{r['count_low']}, {r['count_high']}]; mass "
                                f"{r['kg_status']} (cut length: {r['cut_length_held'][:120]}); Q-71 (owner 11:51): "
                                f"{why}: the 7.5 cm offset is printed on the p.11 / p.12 continuous-beam details only "
                                "and is not carried to the p.13 / p.14 ground-beam sections (ERS s.3); designer item "
                                "S9 (CLARIFICATIONS_CONSULTANT_2026-10-24)"),
                        evidence=f"T-272 LEDGER_T272.csv run {r['run']} ({r['family']}); ST7757.pdf p.13 / p.14"))
    # T-273 GB lap rows: restated nets + the lap part
    chain_checks = []
    for r in T73:
        e, c = r["element"].rsplit(" ", 1)
        fam = "GROUND_BEAMS" if r["floor"] == "GROUND_BEAM" else "SLABS"
        base = dict(family=fam, element_id=e, source=T273,
                    evidence=f"T-273 LAP_ROWS_T273.csv; {r['drawing_ref'][:120]}")
        if fam == "SLABS":
            rows.append(Row(row_id=f"T273|{r['element']}|NET+LAP", bar_group=c, source_kg=F(r["net_kg"]),
                            status="HELD", relation="HELD",
                            reason="lap HELD; its net restates slab (S7) items outside T-299's scope (not reconciled "
                                   "here, not a quantity of this ledger)", source_state=f"T-273:NET:{r['status']}",
                            **base))
            continue
        lapst = "NOT_REQUIRED" if r["status"] == "NOT_REQUIRED" else "HELD"
        rows.append(Row(row_id=f"T273|{r['element']}|LAP", bar_group=f"{c}:LAP", source_kg=F(r["lap_kg"]),
                        status=lapst, relation="HELD",
                        reason=f"lap {r['status']}: {r['lap_basis'][:140]}", **base))
        if e.startswith("GB-CHAIN"):
            pair = e.replace("GB-CHAIN-", "").replace("/", "+")
            comps = ("BOTTOM_ROW_1", "BOTTOM_ROW_2") if c.startswith("BOTTOM") else (c,)
            runs = [rid for (m, cc), rid in t265_ids.items() if t265_pair(m) == pair and cc == c]
            thru = [x.row_id for x in rows if x.source == T138 and "RESTATED_IN_T273_CHAIN" in x.flags
                    and pair_of(x.element_id) == pair and x.bar_group == ("TOP" if c == "TOP" else "BOTTOM")]
            rows.append(Row(row_id=f"T273|{r['element']}|NET", bar_group=c, source_kg=F(r["net_kg"]),
                            status="DRAWING_CONFIRMED_LOWER_BOUND", relation="OVERLAPS", quantity_kg=F(r["net_kg"]),
                            counted=False, overlap_group=f"GBCHAIN:{e}|{c}", relation_to=tuple(runs + thru),
                            shared_part="the chain's bars = the T-265 face-to-face runs + the T-138 through-column "
                                        "pieces of the same band (bottom pieces carry both bottom rows)",
                            reason="restated to count laps; never a second quantity",
                            source_state=f"T-273:NET:{r['status']}", **base))
            got = sum(next(x for x in rows if x.row_id == i).quantity_kg for i in runs)
            got += sum(next(x for x in rows if x.row_id == i).quantity_kg for i in thru) / len(comps)
            chain_checks.append({"row": f"T273|{r['element']}|NET", "t273_net_kg": F(r["net_kg"]),
                                 "t265_runs_plus_t138_through_kg": round(got, 3),
                                 "residual_kg": round(got - F(r["net_kg"]), 3), "t265_runs": runs, "t138_through": thru})
        else:
            rid265 = t265_ids.get((e, c))
            rows.append(Row(row_id=f"T273|{r['element']}|NET", bar_group=c, source_kg=F(r["net_kg"]),
                            status="DRAWING_CONFIRMED_LOWER_BOUND", relation="OVERLAPS", quantity_kg=F(r["net_kg"]),
                            counted=False, overlap_group=f"GB:{e}|{c}",
                            shared_part="the run's net bars (identical to the T-265 row)",
                            reason=f"restates {rid265} to count laps; never a second quantity",
                            source_state=f"T-273:NET:{r['status']}", **base))
    t73s = _json(RES / "agents_t273/summary.json")["totals"]
    named = {T265: 1310.960, T138: 1479.86,                      # T-265 summary families; T-138 report 'Released total'
             **{f"T-273:NET:{k}": round(v["net_kg"], 6) for k, v in t73s.items()}}
    return rows, named, {"t273_chain_restatement": chain_checks}


# ---------------------------------------------------------------------------------------------------------- beams ----

def t149_kind(comp):
    c = comp.lower()
    for k, v in (("over the end column", "END_COLUMN"), ("ends", "ENDS"), ("links", "LINKS"), ("side bars", "SIDE"),
                 ("top corner", "TOP_CORNER"), ("top over support", "SUPPORT_TOP"), ("bottom", "BOTTOM"),
                 ("top", "TOP"), ("planted", "PLANTED"), ("all bars", "ALL")):
        if k in c:
            return v
    return "OTHER"


RG_KIND = {"BOT": "BOTTOM", "TOP": "TOP", "CB_BOTTOM": "BOTTOM", "CB_SUPPORT_TOP": "SUPPORT_TOP",
           "CB_TOP_THROUGH": "TOP_CORNER", "STI": "LINKS", "CB_STIRRUP": "LINKS"}
RG_INCLUDES = {"BOTTOM": "net + 2 anchorage lengths (convention BEAM_BAR_ANCHORAGE_D) = T-149 net + part of its HELD "
                         "note-9 ends", "TOP": "net + 2 anchorage lengths (convention) = T-149 net + part of its HELD ends",
               "SUPPORT_TOP": "the support bars", "TOP_CORNER": "corner bars (UNRESOLVED in route G)",
               "LINKS": "links by (n/m x L + 1) with code hooks: Q-71 says not universal; T-149 links HELD"}


def beams(rg_rows):
    rows = []
    R = _csv(RES / "agents_t149/T149_BEAMS.csv")
    summ = _json(RES / "agents_t149/T149_SUMMARY.json")
    rg_by = defaultdict(list)
    for it in rg_rows:
        if it["family"] != "BEAMS" or it["unit"] != "kg":
            continue
        m = re.search(r"mark (\S+) \((\w+)\)", it["source"])
        mark, binding = (m.group(1), m.group(2)) if m else ("?", "NONE")
        parts = it["item_id"].split(":")
        kind = RG_KIND.get(parts[-2]) or RG_KIND.get(parts[-1]) or "OTHER"
        rg_by[(it["storey"], mark, kind)].append((it, binding))
    t149_keys = set()
    q71 = []
    for i, r in enumerate(R):
        kind = t149_kind(r["component"])
        key = (r["floor"], r["mark"], kind)
        t149_keys.add(key)
    for i, r in enumerate(R):
        kind = t149_kind(r["component"])
        key = (r["floor"], r["mark"], kind)
        g = f"BEAM:{r['floor']}|{r['mark']}|{kind}" if key in rg_by else ""
        rid = f"T149|{i:03d}|{r['row_id']}|{r['component']}"
        kg = F(r["kg"])
        kgrp = {"LINKS": "LINKS", "ENDS": "ENDS", "SIDE": "SIDE", "END_COLUMN": "END_COLUMN"}.get(kind, "BARS")
        base = dict(row_id=rid, source_state=f"T-149:{r['state']}:{r['parent'] or '-'}:{kgrp}", family="BEAMS", element_id=f"{r['member_id']} {r['mark']}"
                    + (f" span {r['span']}" if r["span"] else ""), bar_group=r["component"], source=T149,
                    source_kg=kg, evidence=f"T-149 T149_BEAMS.csv {r['row_id']}; {r['note'][:100]}",
                    overlap_group=g, shared_part=(f"route G {kind} of the same mark and floor: "
                                                  f"{RG_INCLUDES.get(kind, 'same group')}") if g else "")
        rel = "OVERLAPS" if g else None
        if r["state"] == "RELEASED":
            rows.append(Row(status="DRAWING_CONFIRMED_LOWER_BOUND", relation=rel or "INDEPENDENT", quantity_kg=kg,
                            counted=True, reason="T-149 net, face to face (ends, links, side bars HELD apart)", **base))
            continue
        reason = f"T-149 {r['state']} ({r['parent']}): {r['note'][:140]}"
        if kind == "LINKS":
            cont = r["kind"] != "simple"
            n = re.match(r"links (\d+) ", r["component"])
            s = 1.0 / int(n.group(1)) if n else None
            cnt, why = link_count(F(r["clear_length_m"]), s, 0.075 if cont else None, cont)
            rate_ceil = None
            zone = (F(r["clear_length_m"]) - 0.15) if (cont and n and F(r["clear_length_m"])) else None
            rate_ceil = math.ceil(int(n.group(1)) * zone - 1e-9) if zone else None
            q71.append({"row": rid, "mark": r["mark"], "floor": r["floor"], "kind": r["kind"],
                        "rate_count_ceil_n_x_zone": rate_ceil,
                        "clear_m": F(r["clear_length_m"]), "rate_per_m": int(n.group(1)) if n else None,
                        "t149_A_B_C": [r["links_A"], r["links_B"], r["links_C"]], "q71_count": cnt, "q71_basis": why,
                        "count_status": "PROVISIONAL (junctions / zones not re-checked)" if cnt else "HELD"})
            reason += (f"; Q-71 (owner 11:51) reading: {cnt} links by {why} with the printed 7.5 cm first-link "
                       "offset (p.11 / p.12) and s = 1 / n read from the printed per-metre rate (notation reading; "
                       f"the rate count ceil(n x zone) gives {rate_ceil}); count PROVISIONAL (junctions, zones and an "
                       "extra terminal link not re-checked); mass HELD (link hooks S21, nested links S20)") if cnt else \
                      (f"; Q-71 (owner 11:51): {why}; count HELD, designer item S21 / S20")
        rows.append(Row(status="HELD", relation=rel or "HELD", reason=reason, **base))
    for key, its in rg_by.items():
        g = f"BEAM:{key[0]}|{key[1]}|{key[2]}" if key in t149_keys else ""
        for it, binding in its:
            flags = () if binding == "BOUND" else ("PROXIMITY_ONLY", f"ROUTE_G_BINDING_{binding}")
            held = it["base"] == ""
            rows.append(Row(row_id=f"RG|{it['item_id']}", family="BEAMS", element_id=f"{it['component_id']} {key[1]}",
                            bar_group=f"{key[2]} D{it['dia_mm']}" if it["dia_mm"] else key[2], source=RG,
                            source_kg=F(it["base"]), status="HELD" if held else "CONVENTION",
                            relation="OVERLAPS" if g else ("HELD" if held else "INDEPENDENT"),
                            quantity_kg=None if held else F(it["base"]), counted=False, overlap_group=g,
                            shared_part=f"T-149 rows of {key[1]} {key[0]} {key[2]}" if g else "",
                            reason=(f"route G {it['category']} / {it['support']} / blocker {it['blocker']}: "
                                    f"{it['formula'] or 'no formula'}; a PROVISIONAL SUBTOTAL item, never counted"
                                    + ("" if g else "; no T-149 row of this mark / floor / group: ROUTE_G_ONLY")),
                            association="SOURCE_BINDING" if binding == "BOUND" else "PROXIMITY_FLAGGED",
                            flags=flags + (() if g else ("ROUTE_G_ONLY",)), evidence=it["source"]))
    t, l = summ["totals"], summ["links"]
    named = {"T-149:RELEASED:RELEASED:BARS": t["RELEASED"], "T-149:HELD_DEFINED:HELD_DEFINED:BARS": t["HELD_DEFINED"],
             "T-149:HELD_RANGE:RELEASED:LINKS": l["kg_A"], "T-149:HELD_RANGE:HELD_DEFINED:LINKS": l["kg_A [members held]"],
             "T-149:HELD_RANGE:RELEASED:ENDS": t["range_lo:ends (note 9)"],
             "T-149:HELD_RANGE:HELD_DEFINED:ENDS": t["range_lo:ends (note 9) [members held]"],
             "T-149:HELD_RANGE:RELEASED:SIDE": t["range_lo:side bars (2-bar minimum)"],
             "T-149:HELD_RANGE:HELD_DEFINED:SIDE": t["range_lo:side bars (2-bar minimum) [members held]"],
             "T-149:HELD_RANGE:RELEASED:END_COLUMN": t["range_lo:bars over end columns inside the register span"]}
    return rows, named, {"q71_links": q71}


# ------------------------------------------------------------------------------------------------------- assembly ----

def build():
    rg_rows = _csv(HERE / "ROUTE_G_ITEMS_T299.csv")
    rows, named, checks = [], {}, {}
    for fn in (columns, ground_beams, beams):
        r, n, c = fn(rg_rows)
        rows += r
        named.update(n)
        checks.update(c)
    rg_kg = [it for it in rg_rows if it["unit"] == "kg"]
    rg_named = sum(float(it["base"] or 0) for it in rg_kg)
    for it in rg_kg:   # families outside T-299's scope (footings, slabs, ground slab): listed, never reconciled here
        if it["family"] in ("FOOTINGS", "SLABS", "GROUND_SLAB"):
            rows.append(Row(row_id=f"RG|{it['item_id']}", family=f"OUT_OF_SCOPE:{it['family']}",
                            element_id=it["component_id"], bar_group=it["item_id"].split(":")[-2], source=RG,
                            source_kg=F(it["base"]), status="CONVENTION" if it["base"] else "HELD",
                            relation="INDEPENDENT" if it["base"] else "HELD",
                            quantity_kg=F(it["base"]), counted=False,
                            reason="route G item of a family T-299 does not reconcile (footings T-171 unchanged, slabs, "
                                   "ground slab); listed so route G's 16.39 t closes, never counted",
                            association="SOURCE_BINDING", evidence=it["source"]))
    rg_meta = _json(HERE / "ROUTE_G_SUMMARY_T299.json")
    named[RG] = float(rg_meta["summary_steel_t"]["PLANNING_BASE"]) * 1000.0
    checks["route_g_items_vs_summary_kg"] = round(rg_named - named[RG], 9)
    validate(rows)
    dec = {S3: 3, S31: 3, T280: 3, T265: 3, T138: 3, T149: 3, RG: 9, T273: 6}
    res = source_residuals(rows, named, dec, named_decimals={S3: 3, S31: 3, T280: 3, T265: 3, T138: 2, T149: 2, RG: 12,
                                                              T273: 6})
    return rows, named, checks, res


FIELDS = ["row_id", "family", "element_id", "bar_group", "source", "status", "status_class", "relation", "counted",
          "quantity_kg", "quantity_t", "source_kg", "replaces", "relation_to", "overlap_group", "shared_part",
          "association", "flags", "reason", "evidence"]


def to_csv(rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({"row_id": r.row_id, "family": r.family, "element_id": r.element_id, "bar_group": r.bar_group,
                    "source": r.source, "status": r.status, "status_class": r.status_class, "relation": r.relation,
                    "counted": "Y" if r.counted else "N",
                    "quantity_kg": "" if r.quantity_kg is None else f"{r.quantity_kg:.6f}",
                    "quantity_t": "" if r.quantity_t is None else f"{r.quantity_t:.6f}",
                    "source_kg": "" if r.source_kg is None else f"{r.source_kg:.6f}",
                    "replaces": ";".join(r.replaces), "relation_to": ";".join(r.relation_to),
                    "overlap_group": r.overlap_group, "shared_part": r.shared_part, "association": r.association,
                    "flags": ";".join(r.flags), "reason": r.reason, "evidence": r.evidence})
    return buf.getvalue()


def summary(rows, named, checks, res):
    by = defaultdict(lambda: defaultdict(int))
    for r in rows:
        by[f"{r.family}|{r.source}"][r.relation] += 1
    held_src = defaultdict(float)
    for r in rows:
        if r.status in ("HELD",) and r.source_kg:
            held_src[f"{r.family}|{r.source}"] += r.source_kg
    dup = duplicates(rows)
    flagged = [r.row_id for r in rows if "PROXIMITY_ONLY" in r.flags]
    return {
        "task": "T-299 read-only reinforcement ledger reconciliation (lane S); RECON_LEDGER_V1",
        "unit_rule": "kg internally at full precision; t = kg / 1000 once, 6 decimals (OWNER_RULE_REBAR_2026-10-24 s.1)",
        "rows": len(rows),
        "counted_totals_by_family_and_class": family_totals(rows),
        "never_summed": "class totals are never added across classes; alternative ledgers (S3.1, route G, T-273 nets, "
                        "T-138 replaced rows) are never counted",
        "source_residuals": res,
        "relations_by_family_source": {k: dict(v) for k, v in sorted(by.items())},
        "held_source_kg_not_quantities": {k: round(v, 3) for k, v in sorted(held_src.items())},
        "duplicate_groups": {"count": len(dup), "overlap": sum(1 for d in dup if d["kind"] == "OVERLAP"),
                             "replace": sum(1 for d in dup if d["kind"] == "REPLACE")},
        "proximity_flagged_rows": {"count": len(flagged), "rows": flagged},
        "checks": checks,
        "route_g": {"kg_items_base_kg": round(named[RG], 6), "t": kg_to_t(named[RG]),
                    "label": "PROVISIONAL SUBTOTAL (owner 2026-10-25 10:33 (2)): never a total or a bound"},
    }


def main(argv):
    rows, named, checks, res = build()
    text = to_csv(rows)
    js = json.dumps(summary(rows, named, checks, res), indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    if "--check" in argv:
        ok = OUT_CSV.read_text(encoding="utf-8") == text and OUT_JSON.read_text(encoding="utf-8") == js
        print("T-299 check:", "identical" if ok else "DIFFERS")
        return 0 if ok else 1
    OUT_CSV.write_text(text, encoding="utf-8")
    OUT_JSON.write_text(js, encoding="utf-8")
    print(f"{len(rows)} rows -> {OUT_CSV.name}, {OUT_JSON.name}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except LedgerError as e:
        print("LEDGER REFUSED:", e)
        sys.exit(2)
