"""V2.9 / V2.11 / V2.12 / V2.13 arch runs with the project inputs the verifier used (T-120 script), lines dumped."""
import json, sys
from pathlib import Path
ROOT = Path(sys.argv[1]); sys.path.insert(0, str(ROOT))
from engine.source import arch_measure as AM
from tools import urban_boq_m9 as M
drawing, out = sys.argv[2], Path(sys.argv[3])
facts = {"schema": AM.FACTS_SCHEMA,
         "sanitary_by_room": json.loads((ROOT/"research/agents_t010/sanitary_reading.json").read_text())["items"],
         "exterior_spaces": json.loads((ROOT/"research/agents_t071/alsenan_facts.json").read_text())}
f13 = dict(facts)
f13["project_data"] = {"schema": "URBAN_PROJECT_DATA_FILE_V1", "project": "dv", "records": [{
    "key": "WET_ZONE_SIZE_GF_PANTRY", "project": "dv", "kind": "table", "unit": "none",
    "value": {"length_m": 4.50, "width_m": 3.00}, "status": "DRAWING-VERIFIED", "drawing_file": Path(drawing).name,
    "drawing_number": "architectural set", "revision": "no revision printed", "sheet": "ground floor plan",
    "reference": "printed 4.50 x 3.00 m at the PANTRY label", "applies_to": {"floors": ["GF"], "members": ["PANTRY"]},
    "reviewer_or_source": "verifier hand reading (T-114 read the same printed size)", "entered_by": "TYPED"}]}
for m, f in (("ARCH_TAKEOFF_V2.10", facts), ("ARCH_TAKEOFF_V2.11", facts), ("ARCH_TAKEOFF_V2.12", facts), ("ARCH_TAKEOFF_V2.13", f13)):
    b, a, _ = M.arch_compute(drawing, method=m, facts=f, project_id="dv")
    d = out / m.split("_")[-1]; d.mkdir(parents=True, exist_ok=True)
    (d / "BOQ_LINES.json").write_text(json.dumps(b["lines"], default=str))
    print(m, len(b["lines"]), flush=True)
