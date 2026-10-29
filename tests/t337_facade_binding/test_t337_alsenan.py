"""T-337 development-villa binding: rebuild byte for byte from the merged ledgers and check the invariants the
lane I package (T-314) relies on. Reads committed research files only (no private drawing)."""

import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t337"
sys.path.insert(0, str(HERE))

import t337_alsenan as T  # noqa: E402

OUT = T.outputs()


def rows(name):
    return list(csv.DictReader(io.StringIO(OUT[name])))


def test_byte_identical_rebuild():
    for name, text in OUT.items():
        assert (HERE / name).read_text(encoding="utf-8") == text, name


def test_candidate_is_v3022_and_binds_its_existing_ids():
    cand = json.loads((HERE / "CANDIDATE_V3022_T337.json").read_text(encoding="utf-8"))
    assert cand["lines_json_sha256_8"] == "7199c8b6" and cand["lines_total"] == 3706
    ids = {x["line_id"]: x for x in cand["facade_lines"]}
    for lid in T.STOREY_LINE.values():
        assert ids[lid]["item_code"] == "FIN.EXT.FINISH" and ids[lid]["measured_net"] is None
    assert not any(x.get("missing") for x in cand["cited_other_lines"])


def test_every_t305_face_once_and_closure_zero():
    faces = rows("BINDING_T337.csv")
    assert len({f["key"] for f in faces}) == len(faces)
    clo = {c["check"]: c for c in rows("CLOSURE_T337.csv")}
    for k in ("residual DC (must be 0)", "residual HELD (must be 0)"):
        assert abs(float(clo[k]["lo"])) < 1e-6 and abs(float(clo[k]["hi"])) < 1e-6
    assert abs(float(clo["plinth: binding gross vs T-311 PLINTH_SEGMENT (29 segments)"]["hi"])) < 1e-6


def test_no_parapet_band_in_a_storey_line_and_no_storey_band_in_a_parapet_line():
    for f in rows("BINDING_T337.csv"):
        if f["kind"] == "parapet":
            assert f["line"].startswith("NEW FIN.EXT.FINISH PARAPET-OUTER"), f["key"]
        if f["line"] in T.STOREY_LINE.values():
            assert f["kind"] == "storey" and f["top"] and float(f["top"]) <= {"GF": 5.5, "1F": 9.7, "2F": 13.9}[
                f["owner_floor"]] + 1e-9, f["key"]


def test_split_storey_lines_and_the_lower_roof_face():
    fill = {f["line"]: f for f in rows("FILL_T314_T337.csv")}
    gf, f1, f2 = (fill[T.STOREY_LINE[k]] for k in ("GF", "1F", "2F"))
    assert abs(float(gf["gross_lo"]) - 469.329) < 1e-3 and gf["point_value"] == ""  # 479.920 - 14.671 + 4.080
    assert abs(float(f1["net_lo"]) - 234.525528) < 1e-6 and f1["point_value"] != ""
    assert float(f2["gross_lo"]) == 125.16 and float(f2["net_lo"]) == 117.305   # 140.060 - 14.900
    lower = [f for f in rows("BINDING_T337.csv") if f["t305_band"] == "over_lower_roof"][0]
    assert lower["line"] == T.STOREY_LINE["GF"] and lower["t305_state"] == "NO_LINE"


def test_openings_once_held_never_zero_and_blank_lines_blank():
    ops = rows("OPENINGS_T337.csv")
    names = [(o["floor"], o["side"], o["opening"]) for o in ops]
    assert len(names) == len(set(names)) == 39
    held = {o["opening"]: o for o in ops if o["status"] == "HELD"}
    assert set(held) == {"W02", "D-GF-07"} and all(float(o["hi"]) > 0 and o["fixed"] == "" for o in held.values())
    assert all(o["line"] in T.STOREY_LINE.values() for o in ops if o["status"] != "NOT_AN_OPENING")
    fill = {f["line"]: f for f in rows("FILL_T314_T337.csv")}
    edge = fill["NEW FIN.EXT.FINISH SLAB-EDGE 1F"]
    assert edge["gross_lo"] == edge["net_lo"] == "" and edge["status"].startswith("HELD")
    for f in rows("FILL_ITEMS_T314_T337.csv"):
        if f["status"].startswith("UNKNOWN"):
            assert f["qty_lo"] == f["qty_hi"] == ""


def test_t324_corrections_carried():
    faces = {f["key"]: f for f in rows("BINDING_T337.csv")}
    nw2 = faces["1F/NW-2/PARAPET/parapet"]
    assert nw2["status"] == "HELD" and abs(float(nw2["lo"]) - 4.5853 * 3.2496 / 3.5283) < 1e-6
    c5 = faces["GF/NE-6x/EDGE/parapet"]
    assert c5["status"] == "HELD" and float(c5["lo"]) == 0.0 and float(c5["hi"]) == 0.6
