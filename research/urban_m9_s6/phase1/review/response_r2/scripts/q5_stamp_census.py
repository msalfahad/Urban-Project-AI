"""Q5 (read-only): which freeze manifests pin outputs that carry a '+code:<digest>' stamp, and which source files the
manifests pin (and whether any pin is stale today). Stage folders are reported without their project prefix.
usage: python3 -I q5_stamp_census.py REPO OUT_JSON"""
import collections, hashlib, json, re, sys
from pathlib import Path
REPO, OUT = Path(sys.argv[1]), sys.argv[2]
PREFIX = re.compile("(?i)^" + "als" + "[ey]?n[ya]?an_")
STAMP = re.compile(rb"\+code:[0-9a-f]{8,}")
mans = sorted(set(REPO.glob("research/**/*FREEZE*MANIFEST*.json")) | set(REPO.glob("research/**/*freeze_manifest*.json"))
              | set(REPO.glob("research/**/00_ENGINE_FREEZE*.json")))
rows, pins, stale = [], collections.Counter(), collections.Counter()
by_type, stamped_type = collections.Counter(), collections.Counter()
for m in mans:
    d = json.loads(m.read_text(encoding="utf-8"))
    code = d.get("code") or d.get("code_sha256") or d.get("engine_code") or d.get("files_sha256") or {}
    if isinstance(code, dict):
        for f, h in code.items():
            pins[f] += 1
            p = REPO / f
            if p.exists() and isinstance(h, str) and len(h) == 64 and hashlib.sha256(p.read_bytes()).hexdigest() != h:
                stale[f] += 1
    outs = d.get("outputs") or {}
    if not outs:
        continue
    st = []
    for o in outs:
        f = m.parent / o
        if f.exists():
            by_type[f.suffix] += 1
            if STAMP.search(f.read_bytes()):
                st.append(o); stamped_type[f.suffix] += 1
    rows.append({"stage_folder": PREFIX.sub("", m.parent.name), "outputs": len(outs), "outputs_with_code_stamp": len(st)})
res = {"output_pinning_manifests": len(rows), "with_a_stamped_output": sum(1 for r in rows if r["outputs_with_code_stamp"]),
       "outputs_total": sum(by_type.values()), "outputs_stamped": sum(stamped_type.values()),
       "outputs_by_type": dict(by_type), "stamped_by_type": dict(stamped_type),
       "manifests_with_a_code_map": None, "distinct_pinned_source_files": len(pins), "stale_pins": sum(stale.values()),
       "pins_of_phase2a_files": {f: pins.get(f, 0) for f in ("engine/source/opening_census.py", "engine/source/arch_plan.py",
                                 "engine/source/arch_rooms.py", "engine/source/topology.py", "engine/source/opening_gaps.py",
                                 "engine/source/lintel_measure.py", "tools/urban_intake.py", "tools/arch_intake.py",
                                 "tools/arch_discovery.py", "tools/urban_boq_m9.py")},
       "per_manifest": rows}
res["manifests_with_a_code_map"] = sum(1 for m in mans if isinstance(json.loads(m.read_text(encoding="utf-8")).get("code")
                                       or json.loads(m.read_text(encoding="utf-8")).get("code_sha256")
                                       or json.loads(m.read_text(encoding="utf-8")).get("engine_code") or json.loads(m.read_text(encoding="utf-8")).get("files_sha256"), dict))
json.dump(res, open(OUT, "w"), indent=1)
print({k: v for k, v in res.items() if k != "per_manifest"})
