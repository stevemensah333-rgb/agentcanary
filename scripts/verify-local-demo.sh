#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/cyber-redteam-foundry/src${PYTHONPATH:+:$PYTHONPATH}"
runner="${CANARY_BACKEND_PYTHON:-cyber-redteam-foundry/.venv/bin/python}"
mkdir -p .local
# Expect BLOCK for a deliberately regressed synthetic target.
set +e
"$runner" -m cyberredteam.evaluation.scenarios --suite research/scenarios/v1.json --baseline http://127.0.0.1:9000/baseline/chat --candidate http://127.0.0.1:9000/regressed/chat --split all --output .local/regressed.json
status=$?
set -e
if [ "$status" -ne 2 ]; then echo "Expected regression BLOCK (exit 2), got $status" >&2; exit 1; fi
"$runner" -m cyberredteam.evaluation.scenarios --suite research/scenarios/v1.json --baseline http://127.0.0.1:9000/baseline/chat --candidate http://127.0.0.1:9000/fixed/chat --split all --output .local/fixed.json
"$runner" scripts/import-fixture-demo.py --database .local/canary.db .local/regressed.json .local/fixed.json > .local/releases.json
"$runner" - <<'PY'
import json
from pathlib import Path
from urllib.request import urlopen
summary = json.loads(Path('.local/releases.json').read_text())
base = 'http://127.0.0.1:5173'
with urlopen(base + '/api/auth/session') as response:
    assert json.load(response)['authenticated']
with urlopen(base + '/api/projects') as response:
    assert any(p['project_id'] == summary['project_id'] for p in json.load(response))
for release in summary['releases']:
    with urlopen(base + '/api/releases/' + release['release_id']) as response:
        assert json.load(response)['decision'] == release['decision']
with urlopen('http://127.0.0.1:9000/health') as response:
    health = json.load(response)
    assert health['mode'] == 'integration-fixture' and health['provider_calls'] == 0
print('Verified: fixture HTTP -> persisted differential BLOCK/PASS -> authenticated local dashboard proxy. Provider calls: 0.')
PY
