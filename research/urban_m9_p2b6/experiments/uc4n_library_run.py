"""Experiment H: the U-C4N/Autocad-MCP headless ezdxf backend (MIT, @cdb1063) as a LIBRARY (not an MCP connection):
rooms_detect on synthetic fixtures. argv: clone dir, dxf..."""
import asyncio, json, sys
sys.path.insert(0, sys.argv[1])
from backends.ezdxf_backend import EzdxfBackend
from engineering.arch.rooms import rooms_detect

async def one(path):
    b = EzdxfBackend()
    await b.drawing_open(path)
    try:
        r = await rooms_detect(b, layers=["A-WALL"])
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"[:300]}
    return {"rooms": [{"area_m2": round(x.get("area_m2") or (x.get("area") or 0) / 1e6, 4), "label": x.get("label")} for x in r.get("rooms", [])],
            "keys": sorted(r)[:12]}

for p in sys.argv[2:]:
    print(p.split("/")[-1], json.dumps(asyncio.run(one(p)))[:600])
