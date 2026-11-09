"""T-644 drawing reader (research only, NOT engine code): the masonry beside BOTH jambs of every one of the 60 lintel
openings of the candidate's STR.CONC.LINTEL lines, measured with the merged LINTEL_BEARING_V3 reader (T-527, which reuses
the T-516 masonry construction and the T-519 V2 reach), so the owner precast rule's 0.15 m bearing can be checked on
built masonry at every opening instead of 20 of them.

Nothing is re-implemented: t527_extract.main is run with the T-516 case table widened to the 60 openings (their V2 band
and gap from the T-175 opening host table, research/agents_t175/T175_OPENING_CONSEQUENCES.csv); the 16 openings T-527
already measured are a CONTROL and must reproduce its committed rows byte for byte (asserted).

Inputs (outside the repository, never committed): <scratch>/t125_inputs.pkl and <scratch>/t125_v2.json, the merged
research/agents_t125 capture of Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha ab54dd55).
Output: research/agents_t644/out/JAMB_EVIDENCE_T644.csv, NUMBERS ONLY (lengths along a wall from a jamb, wall / gap ids).

    python3 -I research/agents_t644/t644_extract.py <scratch>
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in ("agents_t527", "agents_t516", "agents_t519"):
    sys.path.insert(0, str(ROOT / "research" / p))
import t516_extract as X1  # noqa: E402  (read only; its CASES / CENSUS_OF tables are widened in memory only)
import t527_extract as X3  # noqa: E402  (read only)

OUT = HERE / "out" / "JAMB_EVIDENCE_T644.csv"
T527_CSV = ROOT / "research" / "agents_t527" / "out" / "JAMB_EVIDENCE_V3_T527.csv"

# opening -> (storey, V2 band, gap ref) for the 44 openings T-516 did not measure (T-175 host table; P-GF-01 / P-1F-01
# by their head-line gaps OP-020 / OP-009 on the bands the host table names; doorways at a free wall end as T-516 does)
EXTRA = {
    "A-1F-01": ("1F", "WB-FL0027-FL0028", "OP-011"), "A-GF-01": ("GF", "WB-FL0095-FL0096", "OP-027"),
    "D-1F-01": ("1F", "WB-FL0006-FL0007", "OP-004"), "D-1F-05": ("1F", "WB-FL0016-FL0018", "OP-008"),
    "D-1F-06": ("1F", "WB-FL0027-FL0028", "OP-010"), "D-1F-09": ("1F", "WB-FL0013-FL0014", "OP-006"),
    "D-2F-02": ("2F", "WB-FL0024-FL0026", "OP-007"), "D-GF-01": ("GF", "WB-FL0020-FL0021", "OP-009"),
    "D-GF-02": ("GF", "WB-FL0010-FL0011", "DOORWAY"), "D-GF-03": ("GF", "WB-FL0017-FL0018", "OP-005"),
    "D-GF-04": ("GF", "WB-FL0089-FL0090", "OP-026"), "D-GF-05": ("GF", "WB-FL0083-FL0084", "OP-025"),
    "D-GF-07": ("GF", "WB-FL0078-FL0079", "OP-021"), "D-GF-08": ("GF", "WB-FL0025-FL0026", "OP-010"),
    "D-GF-09": ("GF", "WB-FL0041-FL0042", "OP-013"), "L-1F-01": ("1F", "WB-FL0016-FL0018", "OP-007"),
    "L-2F-01": ("2F", "WB-FL0004-FL0005", "OP-002"), "L-GF-01": ("GF", "WB-FL0025-FL0026", "OP-011"),
    "P-1F-01": ("1F", "WB-FL0022-FL0023", "OP-009"), "P-GF-01": ("GF", "WB-FL0076-FL0077", "OP-020"),
    "W01": ("GF", "WB-FL0078-FL0079", "OP-022"), "W04": ("GF", "WB-FL0017-FL0018", "OP-004"),
    "W05": ("GF", "WB-FL0041-FL0042", "OP-014"), "W06": ("GF", "WB-FL0041-FL0042", "OP-015"),
    "W07": ("GF", "WB-FL0041-FL0042", "OP-016"), "W08": ("GF", "WB-FL0017-FL0018", "OP-006"),
    "W09": ("GF", "WB-FL0081-FL0082", "OP-024"), "W10": ("GF", "WB-FL0081-FL0082", "OP-023"),
    "W11": ("GF", "WB-FL0097-FL0098", "OP-028"), "W12": ("GF", "WB-FL0097-FL0098", "OP-029"),
    "W13": ("1F", "WB-FL0074-FL0076", "OP-021"), "W16": ("1F", "WB-FL0041-FL0042", "OP-017"),
    "W19": ("1F", "WB-FL0002-FL0003", "OP-001"), "W20": ("1F", "WB-FL0002-FL0003", "OP-002"),
    "W21": ("1F", "WB-FL0030-FL0031", "OP-013"), "W22": ("1F", "WB-FL0030-FL0031", "OP-014"),
    "W23": ("1F", "WB-FL0030-FL0031", "OP-015"), "W24": ("1F", "WB-FL0002-FL0003", "OP-003"),
    "W25": ("1F", "WB-FL0030-FL0031", "OP-012"), "W26": ("2F", "WB-FL0035-FL0036", "OP-008"),
    "W27": ("2F", "WB-FL0010-FL0011", "OP-003"), "W28": ("2F", "WB-FL0010-FL0011", "OP-004"),
    "W29": ("2F", "WB-FL0010-FL0011", "OP-005"),
}
# no V2 band: measured nowhere (HELD by name in the piece table, never 0)
NOT_MEASURABLE = {"D-GF-14": "no V2 band (T-125 MISSING, GF-W30, T-175): its jambs are not in the masonry capture"}


def cases():
    c = dict(X1.CASES)
    for k, v in EXTRA.items():
        assert k not in c, k
        c[k] = v
    return c


def census_of():
    """gap -> opening id on every band of the 60 (so a stopper names the neighbouring opening, not a gap id)."""
    m = dict(X1.CENSUS_OF)
    for oid, (fl, band, how) in cases().items():
        if how not in ("DOORWAY",):
            m[(fl, band, how)] = oid
    return m


def main(scratch, out=None):
    out = Path(out) if out else OUT
    saved = (X1.CASES, X1.CENSUS_OF)
    X1.CASES, X1.CENSUS_OF = cases(), census_of()     # X3.gap_id reads X1.CENSUS_OF: neighbours named by census id
    try:
        X3.main(scratch, out=out.parent / "_t644_raw.csv")
        back = {f"{k[1]}:{k[2]}": v for k, v in X1.CENSUS_OF.items()}
    finally:
        X1.CASES, X1.CENSUS_OF = saved              # the merged modules are left exactly as imported
    raw = out.parent / "_t644_raw.csv"
    bays = out.parent / X3.BAYS_NAME
    # control: the 16 T-527 openings, every field, byte for byte
    ref = list(csv.DictReader(open(T527_CSV, encoding="utf-8")))
    got = [r for r in csv.DictReader(open(raw, encoding="utf-8")) if r["opening_id"] in {x["opening_id"] for x in ref}]

    def norm(r):            # a stopper T-527 named 'band:ref' is now named by its census id (same gap, same key)
        r = dict(r)
        for f in ("v1_stopper_id", "v2_stopper_id", "stopper_id"):
            r[f] = back.get(r[f], r[f])
        return r
    if [norm(r) for r in got] != [norm(r) for r in ref]:
        bad = [(a["opening_id"], a["side"]) for a, b in zip(got, ref) if dict(a) != dict(b)]
        raise SystemExit(f"control failed: the 16 T-527 openings do not reproduce: {bad[:6]}")
    keep = [r for r in csv.DictReader(open(raw, encoding="utf-8"))]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(keep[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(keep)
    raw.unlink()
    if bays.exists():
        bays.unlink()
    return keep


if __name__ == "__main__":
    rows = main(sys.argv[1])
    print(OUT, len(rows), "ends")
