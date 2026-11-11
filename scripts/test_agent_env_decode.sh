#!/usr/bin/env bash
# Test: `agent_env.sh decode` (owner 2026-11-11) accepts the three forms the Drive connector hands over (raw bytes,
# plain base64 text, connector JSON with base64 content), unzips zips safely, writes only into .work/private, and fails
# loudly on empty or bad input. Builds a throw-away fake checkout with a READY venv; no network, touches nothing real.
# Run by the owner's main chat: bash scripts/test_agent_env_decode.sh
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
fail() { echo "TEST FAIL: $*"; exit 1; }
ok() { echo "TEST OK: $*"; }

R="$TMP/msalfahad/Urban-Project-AI"; mkdir -p "$R/scripts"
cp "$HERE/scripts/agent_env.sh" "$R/scripts/agent_env.sh"
git -C "$R" init --quiet && git -C "$R" remote add origin "https://github.com/msalfahad/Urban-Project-AI.git"
mkdir -p "$R/.work/board" "$R/.work/engine" "$R/.work/venv/bin" "$R/.work/venv/site"
for m in pytest ezdxf shapely; do mkdir -p "$R/.work/venv/site/$m"; touch "$R/.work/venv/site/$m/__init__.py"; done
printf '#!/usr/bin/env bash\nPYTHONPATH="%s" exec python3 "$@"\n' "$R/.work/venv/site" > "$R/.work/venv/bin/python"; chmod +x "$R/.work/venv/bin/python"
echo "pytest==9.1.1" > "$R/.work/engine/requirements.txt"
sha256sum "$R/.work/engine/requirements.txt" | cut -c1-16 > "$R/.work/venv/.req_hash"
P="$R/.work/private"; IN="$TMP/in"; mkdir -p "$IN"
dec() { (cd "$R" && bash scripts/agent_env.sh decode "$@" 2>&1); }

# inputs: a real zip, a PDF-like binary, and their base64 / connector-JSON forms
python3 -I - "$IN" <<'EOF'
import base64, json, sys, zipfile, os
d = sys.argv[1]
with zipfile.ZipFile(os.path.join(d, "pkg.zip"), "w") as z:
    z.writestr("plans/a.dxf", "0\nSECTION\n"); z.writestr("b.txt", "hello")
pdf = b"%PDF-1.7\n" + bytes(range(256)) * 40
open(os.path.join(d, "doc.pdf"), "wb").write(pdf)
open(os.path.join(d, "doc.b64"), "wb").write(base64.encodebytes(pdf))
zipb = open(os.path.join(d, "pkg.zip"), "rb").read()
open(os.path.join(d, "pkg.json"), "w").write(json.dumps({"content": base64.b64encode(zipb).decode(), "mimeType": "application/zip"}))
with zipfile.ZipFile(os.path.join(d, "evil.zip"), "w") as z:
    z.writestr("../escape.txt", "x")
open(os.path.join(d, "badjson.json"), "w").write(json.dumps({"content": "not base64 !!"}))
open(os.path.join(d, "empty.bin"), "wb").close()
EOF
want_pdf="$(sha256sum "$IN/doc.pdf" | cut -c1-64)"

# 1. raw bytes (the case that used to fail with 'base64 decode failed')
out="$(dec "$IN/pkg.zip" raw.zip)" || fail "raw zip refused: $out"
grep -q "decoded (raw bytes) and unzipped" <<<"$out" || fail "raw zip not reported as raw: $out"
[[ -f "$P/raw/plans/a.dxf" && "$(cat "$P/raw/b.txt")" == hello ]] || fail "raw zip not extracted"
out="$(dec "$IN/doc.pdf" raw.pdf)" || fail "raw pdf refused: $out"
[[ "$(sha256sum "$P/raw.pdf" | cut -c1-64)" == "$want_pdf" ]] || fail "raw pdf bytes changed"
ok "raw downloads (zip, pdf) are written byte for byte; the zip is extracted"

# 2. plain base64 text and 3. connector JSON
out="$(dec "$IN/doc.b64" b64.pdf)" || fail "base64 text refused: $out"
grep -q "(base64 text)" <<<"$out" || fail "base64 not detected: $out"
[[ "$(sha256sum "$P/b64.pdf" | cut -c1-64)" == "$want_pdf" ]] || fail "base64 decode wrong"
out="$(dec "$IN/pkg.json" json.zip)" || fail "connector JSON refused: $out"
grep -q "(connector JSON (base64))" <<<"$out" || fail "JSON not detected: $out"
[[ -f "$P/json/plans/a.dxf" ]] || fail "JSON zip not extracted"
ok "base64 text and connector JSON still decode exactly"

# 4. refusals: path-escaping zip, JSON with bad base64, empty file, bad name; nothing is left behind on failure
out="$(dec "$IN/evil.zip" evil.zip)" && fail "escaping zip accepted: $out"
grep -q "escapes the private folder" <<<"$out" || fail "no escape refusal: $out"
[[ ! -e "$R/.work/escape.txt" && ! -e "$P/escape.txt" ]] || fail "escape file written"
out="$(dec "$IN/badjson.json" bad.bin)" && fail "bad JSON accepted: $out"
grep -q "without valid base64" <<<"$out" || fail "no bad-JSON reason: $out"
[[ ! -e "$P/bad.bin" ]] || fail "partial file left after a failed decode"
out="$(dec "$IN/empty.bin" empty.bin)" && fail "empty file accepted: $out"
grep -q "source file is empty" <<<"$out" || fail "no empty reason: $out"
out="$(dec "$IN/doc.pdf" ../x.pdf)" && fail "path name accepted: $out"
ok "escaping zip, bad JSON, empty file and path names are refused with a reason; no partial file kept"
echo "ALL DECODE TESTS PASSED"
