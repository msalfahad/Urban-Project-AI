"""T-461 (owner directive 2026-11-02 C6): registry housekeeping by NEW versions only.

(a) the paused second project's fixed plaster 3.20 m / ceramic 3.00 m heights -> data/registry/23010_heights_2.1.json
    (HEIGHT_REQUIRED per face, the old values kept as superseded history; 2.0 untouched)
(b) the 1:3 stair-bed mortar no longer 'held' at registry level -> UP-STAIR-017 in URBAN_RULES 1.8.0 (Q-53 C)
(c) UP-GEN-003 PLASTER_PAINT 'OWNER_DECISION_PENDING' -> UP-GEN-003 1.2.0 in URBAN_RULES 1.8.0 (Q-73 A)
(d) knowledge 1.8.0 in engine/source/knowledge.py VERSIONS; URBAN_RULES 1.6.0 / 1.7.0 / 1.8.0 resolved by
    engine/source/rule_store_v2.py and registered in rules/RULES_MANIFEST.json; rule_store.py (V1) unchanged.
Every value below is hand-checked; nothing is read from a client drawing."""

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine import heights as H  # noqa: E402
from engine.source import knowledge as K  # noqa: E402
from engine.source import rule_store as RS1  # noqa: E402
from engine.source import rule_store_v2 as RS2  # noqa: E402

OV18 = ROOT / "rules/owner_decisions/URBAN_RULES_1.8.0.json"
H20 = ROOT / "data/registry/23010_heights.json"
H21 = ROOT / "data/registry/23010_heights_2.1.json"
# files that must stay byte-identical (sha256 at engine 8ccf69b3)
UNTOUCHED = {
    "rules/owner_decisions/URBAN_RULES_1.5.0.json": "50c120c62d191ccfd08f2b3bc6fc79b2f13be4cc81f9a3c2478e4f797f283954",
    "rules/owner_decisions/URBAN_RULES_1.6.0.json": "a9a04c63044685041d90c06b715b99c2da859aeb997a36f672876fbf57008cd8",
    "rules/owner_decisions/URBAN_RULES_1.7.0.json": "84aacdb68bff08577eeeb75b2ade9f2a3863a2c1585259c2eef876c13572cbb0",
    "data/registry/23010_heights.json": "18a23993243cea8ffb4286bc33242f99739f920ee7a49aed4239b042b76b567e",
    "data/trade_rules/23010_ceramic.json": "c5e83f2bda94b087fc908d87091d5a37c38755cb680be7678e306720c5594ca8",
    "data/trade_rules/23010_plaster.json": "211c5b08df0209922d89968a7708bfcdce6ad18fa5d642d662935bc97546e37e",
    "knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.8.0.json": "629cb4a4472e1ce5d56e3e56dfb66c7a86d4d51621551c8bedfe1d45335b1f9d",
    "engine/source/rule_store.py": "1c7f62b3fc81a99c2ea610bc40ebb4dbf29ad73dfd8cde9a6fcb4f3873af87a2",
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def test_no_existing_version_file_was_edited():
    for rel, h in UNTOUCHED.items():
        assert sha(ROOT / rel) == h, rel


# ---------------------------------------------------------------- (a) heights


def _numeric_heights(obj, path=()):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _numeric_heights(v, path + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _numeric_heights(v, path + (str(i),))
    elif path and path[-1] in ("value_m", "height_m") and any("height" in s for s in path):
        yield ".".join(path), str(obj)


def unlisted_hard_coded_heights(new_registry, files):
    """hard-coded project heights in `files` that the new registry neither withdraws nor lists as superseded."""
    listed = {loc for s in new_registry.get("superseded", []) for loc in s["hard_coded_in"]}
    out = []
    for f in files:
        for loc, _v in _numeric_heights(json.loads((ROOT / f).read_text(encoding="utf-8"))):
            if f"{f} {loc}" not in listed:
                out.append(f"{f} {loc}")
    for name, rec in new_registry["domains"].get("DESIGN", {}).items():
        if rec.get("source_type") != H.SECTION_DRAWING:
            out.append(f"2.1 DESIGN {name} = {rec.get('value_m')} from {rec.get('source_type')}")
    return out


OLD_23010 = ("data/registry/23010_heights.json", "data/trade_rules/23010_plaster.json",
             "data/trade_rules/23010_ceramic.json", "data/registry/23010_groups.json")


def test_a_new_height_version_withdraws_the_fixed_heights_per_face():
    new = H.HeightRegistry.load(H21)
    assert new.version == "2.1" and new.project == "23010"
    st = new.status()
    assert st[H.PLASTER] == H.HEIGHT_REQUIRED and st[H.CERAMIC] == H.HEIGHT_REQUIRED and st[H.PAINT] == H.HEIGHT_REQUIRED
    for name in (H.PLASTER, H.CERAMIC):
        with pytest.raises(H.HeightError, match=H.HEIGHT_REQUIRED):
            new.get(name)
        with pytest.raises(H.HeightError):
            new.for_release(name)


def test_a_every_hard_coded_23010_height_is_listed_as_superseded_with_its_old_value():
    raw = json.loads(H21.read_text(encoding="utf-8"))
    assert unlisted_hard_coded_heights(raw, OLD_23010) == []
    old = {s["height_id"]: s["value_m"] for s in raw["superseded"]}
    assert old == {"23010:DESIGN:plaster_height": "3.20", "23010:DESIGN:ceramic_height": "3.00"}
    assert all(s["now"].startswith(H.HEIGHT_REQUIRED) for s in raw["superseded"])
    assert any("UPC-HEIGHT-001" in r for r in raw["rules"]) and any("Q-72" in r for r in raw["rules"])


def test_a_adverse_a_version_that_keeps_a_fixed_height_or_misses_a_file_is_caught():
    raw = json.loads(H21.read_text(encoding="utf-8"))
    bad = json.loads(json.dumps(raw))
    bad["domains"]["DESIGN"]["plaster_height"] = {"value_m": "3.20", "source_type": H.APPROVED_PROJECT_RULE}
    assert any("plaster_height" in x for x in unlisted_hard_coded_heights(bad, OLD_23010))
    short = json.loads(json.dumps(raw))
    short["superseded"][1]["hard_coded_in"] = short["superseded"][1]["hard_coded_in"][:1]
    assert unlisted_hard_coded_heights(short, OLD_23010) == ["data/trade_rules/23010_ceramic.json height_m"]


def test_a_the_old_version_still_reads_as_before():
    old = H.HeightRegistry.load(H20)
    assert str(old.get(H.PLASTER).value_m) == "3.20" and str(old.get(H.CERAMIC).value_m) == "3.00"


# ---------------------------------------------------------------- (b) 1:3 stair bed


def stair_bed_materials(rec, area_m2, bed_m):
    """hand method of UP-STAIR-017: theoretical cement / sand and the separate purchasing layer."""
    if area_m2 is None or bed_m is None:
        return {"status": "HELD", "mortar_m3": None, "cement_kg": None, "cement_bags": None, "sand_m3": None}
    p, a = rec["params"], rec["purchasing_allowance"]
    c_parts, s_parts = (float(x) for x in p["mix_cement_sand"].split(":"))
    m3 = area_m2 * bed_m
    dry = m3 * p["dry_volume_factor"]
    cement_kg = dry * c_parts / (c_parts + s_parts) * p["cement_bulk_density_kg_m3"]
    return {"status": "CALCULATED_PROVISIONAL", "mortar_m3": m3, "cement_kg": cement_kg,
            "cement_bags": cement_kg / p["bag_kg"], "sand_m3": dry * s_parts / (c_parts + s_parts),
            "purchasing_bags": m3 * a["cement_bags_per_m3"], "purchasing_sand_m3": m3 * a["sand_m3_per_m3"]}


def test_b_stair_bed_1_3_rate_is_registered_and_derives_from_the_mix():
    rec = RS2.rule("UP-STAIR-017", "1.8.0")
    assert rec["status"] == "OWNER_APPROVED" and rec["basis"] == "CALCULATED_PROVISIONAL" and "Q-53" in rec["approval"]["source"]
    p = rec["params"]
    assert p["mix_cement_sand"] == "1:3"
    # hand: 1.33 / 4 = 0.3325 m3 cement; x 1440 = 478.8 kg; / 50 = 9.576 bags; 1.33 x 3 / 4 = 0.9975 m3 sand
    assert p["theoretical_cement_m3_per_m3"] == pytest.approx(0.3325, abs=1e-12)
    assert p["theoretical_cement_kg_per_m3"] == pytest.approx(478.8, abs=1e-9)
    assert p["theoretical_cement_bags_per_m3"] == pytest.approx(9.576, abs=1e-12)
    assert p["theoretical_sand_m3_per_m3"] == pytest.approx(0.9975, abs=1e-12)
    one = stair_bed_materials(rec, 1.0, 1.0)
    assert one["cement_kg"] == pytest.approx(p["theoretical_cement_kg_per_m3"])
    assert one["sand_m3"] == pytest.approx(p["theoretical_sand_m3_per_m3"])


def test_b_worked_example_and_purchasing_kept_apart():
    rec = RS2.rule("UP-STAIR-017", "1.8.0")
    ex = rec["worked_examples"][0]
    got = stair_bed_materials(rec, ex["stair_marble_m2"], ex["bed_m"])
    # hand: 10.00 m2 x 0.03 = 0.300 m3; cement 0.300 x 478.8 = 143.64 kg = 2.8728 bags; sand 0.300 x 0.9975 = 0.29925 m3
    for k in ("mortar_m3", "cement_kg", "cement_bags", "sand_m3", "purchasing_bags", "purchasing_sand_m3"):
        assert got[k] == pytest.approx(ex[k], abs=1e-9), k
    assert got["cement_bags"] < got["purchasing_bags"]          # the purchasing layer is never the theoretical quantity


def test_b_adverse_the_1_4_rate_is_not_used_and_missing_inputs_hold():
    rec = RS2.rule("UP-STAIR-017", "1.8.0")
    p = rec["params"]
    assert p["theoretical_cement_bags_per_m3"] != 8.0 and p["theoretical_sand_m3_per_m3"] != 1.1
    assert any("1:4" in n for n in rec["never"])
    # 1:3 needs about a fifth more cement than the 1:4 figure (9.576 / 8.0 = 1.197)
    assert p["theoretical_cement_bags_per_m3"] / 8.0 == pytest.approx(1.197, abs=1e-12)
    held = stair_bed_materials(rec, 12.0, None)
    assert held["status"] == "HELD" and held["cement_bags"] is None      # never 0
    with pytest.raises(KeyError):
        RS2.rule("UP-STAIR-017", "1.7.0")                                  # older sets keep their 'not given'


# ---------------------------------------------------------------- (c) opening deduction


def test_c_plaster_paint_opening_deduction_is_answered_in_1_8_0():
    new = RS2.rule("UP-GEN-003", "1.8.0")
    assert new["version"] == "1.2.0" and new["supersedes"] == "UP-GEN-003@1.1.0"
    assert new["value"]["PLASTER_PAINT"] == "DEDUCT_FULL_OPENINGS" and new["value"]["BLOCKWORK"] == "DEDUCT_FULL_OPENINGS"
    assert new["minimum_deducted_m2"] == 0.0 and "Q-73" in new["approval"]["source"]
    assert "physically built" in new["condition"]
    old = RS2.rule("UP-GEN-003", "1.5.0")
    for k in ("SKIRTING", "WALL_TILE", "WATERPROOFING_UPTURN"):
        assert new["value"][k] == old["value"][k]                        # the other trades are unchanged
    assert {"rule_id": "UP-GEN-003", "from": "1.1.0", "to": "1.2.0", "status": "OWNER_APPROVED"} in \
        RS2.rule_set("1.8.0")["superseded"]


def test_c_adverse_results_under_older_sets_keep_the_pending_entry():
    for v in ("1.5.0", "1.6.0", "1.7.0"):
        assert RS2.rule("UP-GEN-003", v)["value"]["PLASTER_PAINT"] == "OWNER_DECISION_PENDING", v
    assert RS1.rule("UP-GEN-003")["value"]["PLASTER_PAINT"] == "OWNER_DECISION_PENDING"     # V1 default 1.5.0


# ---------------------------------------------------------------- (d) registration


def test_d_knowledge_1_8_0_is_registered_and_loads():
    assert "1.8.0" in K.VERSIONS and K.DEFAULT_VERSION == "1.0.0"
    with K.using("1.8.0"):
        assert K.version() == "1.8.0" and K.registry()["version"] == "1.8.0"
        assert K.rule("UP-HGT-001")["effective_version"] == "1.8.0"
        assert K.digest() == UNTOUCHED["knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.8.0.json"]
    assert K.version() == "1.0.0"


def test_d_rule_store_v2_resolves_every_overlay_and_matches_v1():
    assert RS2.registered() == ["1.4.0", "1.5.0", "1.6.0", "1.7.0", "1.8.0"]
    assert RS2.check_chain() == []
    for v in ("1.4.0", "1.5.0"):
        for prop in (False, True):
            assert RS2.rule_set(v, prop)["digest"] == RS1.rule_set(v, prop)["digest"], (v, prop)
    assert RS2.rule("UP-STAIR-015", "1.6.0")["origin"] == "URBAN_RULES 1.6.0 overlay"
    assert RS2.rule("UP-STAIR-016", "1.7.0")["origin"] == "URBAN_RULES 1.7.0 overlay"
    with pytest.raises(KeyError):
        RS2.rule("UP-STAIR-016", "1.6.0")
    sizes = [len(RS2.rule_set(v)["rules"]) for v in RS2.registered()]
    assert sizes == sorted(sizes) and sizes[-1] - sizes[1] == 3      # + UP-STAIR-015, -016, -017
    assert RS2.rule_ref("UP-GEN-003", "1.8.0")["version"] == "1.2.0"


def test_d_v1_store_and_its_run_record_are_unchanged():
    assert RS1.VERSIONS == ("1.4.0", "1.5.0") and RS1.LATEST_APPROVED == "1.5.0"
    assert RS1.policy_record()["versions"] == ["1.4.0", "1.5.0"]
    assert RS1.check() == []


def test_d_manifest_registers_1_6_to_1_8():
    man = json.loads((ROOT / "rules/RULES_MANIFEST.json").read_text(encoding="utf-8"))
    rec = man["files"]["owner_decisions/URBAN_RULES_1.8.0.json"]
    assert rec["kind"] == "AUTHORED" and rec["sha256"] == sha(OV18)
    assert man["latest_owner_approved"] == "1.5.0"
    for v in ("1.6.0", "1.7.0", "1.8.0"):
        assert man["rule_sets"][v] == [c.split("rules/", 1)[1] for c in RS2.rule_set(v)["chain"]], v
    assert man["resolvers"]["engine/source/rule_store_v2.py"] == RS2.registered()


def test_d_adverse_a_broken_or_unknown_chain_is_refused(tmp_path):
    with pytest.raises(RS2.RuleStoreError, match="unknown rule-set version"):
        RS2.rule_set("1.9.0")
    doc = json.loads(OV18.read_text(encoding="utf-8"))
    wrong_ver = dict(doc, version="1.9.0")
    (tmp_path / "v.json").write_text(json.dumps(wrong_ver), encoding="utf-8")
    probs = RS2.check_chain(dict(RS2.OVERLAYS, **{"2.0.0": str(tmp_path / "v.json")}))
    assert len(probs) == 1 and "says version '1.9.0'" in probs[0]
    orphan = dict(doc, version="1.9.0", base={"rule_set": "URBAN_RULES", "version": "1.6.5", "file": "x"})
    (tmp_path / "o.json").write_text(json.dumps(orphan), encoding="utf-8")
    probs = RS2.check_chain(dict(RS2.OVERLAYS, **{"1.9.0": str(tmp_path / "o.json")}))
    assert len(probs) == 1 and "not a registered overlay" in probs[0]
    skip = dict(doc, version="1.9.0", base={"rule_set": "URBAN_RULES", "version": "1.6.0",
                                            "file": "rules/owner_decisions/URBAN_RULES_1.6.0.json"})
    (tmp_path / "s.json").write_text(json.dumps(skip), encoding="utf-8")
    probs = RS2.check_chain(dict(RS2.OVERLAYS, **{"1.9.0": str(tmp_path / "s.json")}))
    assert len(probs) == 1 and "skips or reorders" in probs[0]
