#!/usr/bin/env bash
# flutter-store-deploy: decide the Android upload phase from project config.
#
# Prints KEY=VALUE lines:
#   CONFIG_PRESENT=0|1
#   PHASE=1|2
#   SERVICE_ACCOUNT_KEY=<path>            (phase 1 only)
#   SERVICE_ACCOUNT_KEY_ERROR=<detail>    (configured but missing/unreadable — surface to user)
#   DEVELOPER_ID=..., TEAM_NAME=..., APP_NAME_<flavor>=...   (phase 2 hints, when configured)
#
# Usage: android_phase_select.sh [--config .flutter-store-deploy/android.json]
# Exit codes: 0 ok; 4 invalid config
set -euo pipefail

CONFIG=".flutter-store-deploy/android.json"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 4 ;;
  esac
done

python3 - "$CONFIG" <<'PY'
import json, os, sys

cfg_path = sys.argv[1]
if not os.path.isfile(cfg_path):
    print("CONFIG_PRESENT=0")
    print("PHASE=2")
    sys.exit(0)

try:
    with open(cfg_path) as f:
        cfg = json.load(f)
except (json.JSONDecodeError, UnicodeDecodeError) as e:
    print(f"invalid JSON in {cfg_path}: {e}", file=sys.stderr)
    sys.exit(4)

print("CONFIG_PRESENT=1")

key = os.path.expanduser(cfg.get("serviceAccountKeyPath") or "")
if key and os.path.isfile(key) and os.access(key, os.R_OK):
    print("PHASE=1")
    print(f"SERVICE_ACCOUNT_KEY={key}")
else:
    print("PHASE=2")
    if key:
        print(f"SERVICE_ACCOUNT_KEY_ERROR={key} (configured but missing or unreadable)")

if cfg.get("developerId"):
    print(f"DEVELOPER_ID={cfg['developerId']}")
if cfg.get("teamName"):
    print(f"TEAM_NAME={cfg['teamName']}")
for flavor, name in (cfg.get("appNames") or {}).items():
    print(f"APP_NAME_{flavor}={name}")
PY
