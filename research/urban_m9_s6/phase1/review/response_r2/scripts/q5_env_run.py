"""Q5 (scratch): run the production CLI on the synthetic villa (base variant) with ARCH_TAKEOFF_V1 / V2 under the
current interpreter. MAKE builds the DXF only (so both interpreters read the same input bytes).
usage: python3 -I q5_env_run.py SRC MAKE|RUN DXF [OUT_DIR METHOD]"""
import contextlib, io, sys
SRC, MODE, DXF = sys.argv[1:4]
sys.path.insert(0, SRC)
if MODE == "MAKE":
    from tools import arch_synth as AS
    AS.villa(DXF)
else:
    OUT, METHOD = sys.argv[4:6]
    from tools import urban_boq_m9 as M9
    with contextlib.redirect_stdout(io.StringIO()):
        code = M9.main(["arch", "--drawings", DXF, "--out", OUT, "--method", METHOD])
    print(sys.version.split()[0], METHOD, "exit", code)
