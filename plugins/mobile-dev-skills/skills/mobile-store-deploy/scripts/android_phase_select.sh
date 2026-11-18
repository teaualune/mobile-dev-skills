#!/usr/bin/env bash
# mobile-store-deploy: decide the Android upload phase from project config.
#
# Prints KEY=VALUE lines:
#   CONFIG_PRESENT=0|1
#   PHASE=1|2
#   SERVICE_ACCOUNT_KEY=<path>            (phase 1 only)
#   SERVICE_ACCOUNT_KEY_ERROR=<detail>    (configured but missing/unreadable — surface to user)
#   AAB_PATH_TEMPLATE=<template>          (always; config's aabPathTemplate, else the Flutter default)
#   DEVELOPER_ID=..., TEAM_NAME=..., APP_NAME_<flavor>=...   (phase 2 hints, when configured)
#
# Usage: android_phase_select.sh [--config .mobile-store-deploy/android.json]
#   Without --config: .mobile-store-deploy/android.json, else the pre-rename
#   .flutter-store-deploy/android.json when only that directory exists. (Never
#   stops when both exist — that's the SKILL.md's job, which passes --config.)
# Exit codes: 0 ok; 4 invalid config (bad JSON, not an object, a wrong-typed key)
set -euo pipefail

CONFIG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --config) CONFIG="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 4 ;;
  esac
done

if [[ -z "$CONFIG" ]]; then
  CONFIG=".mobile-store-deploy/android.json"
  if [[ ! -d .mobile-store-deploy && -d .flutter-store-deploy ]]; then
    CONFIG=".flutter-store-deploy/android.json"
  fi
fi

python3 - "$CONFIG" <<'PY'
import json, os, sys

DEFAULT_AAB = "build/app/outputs/bundle/{flavor}Release/app-{flavor}-release.aab"

cfg_path = sys.argv[1]
if not os.path.isfile(cfg_path):
    print("CONFIG_PRESENT=0")
    print("PHASE=2")
    print(f"AAB_PATH_TEMPLATE={DEFAULT_AAB}")
    sys.exit(0)

try:
    with open(cfg_path) as f:
        cfg = json.load(f)
except (json.JSONDecodeError, UnicodeDecodeError) as e:
    print(f"invalid JSON in {cfg_path}: {e}", file=sys.stderr)
    sys.exit(4)

def invalid(msg):
    print(f"invalid config in {cfg_path}: {msg}", file=sys.stderr)
    sys.exit(4)

# Validate everything before printing, so exit 4 never leaves partial KEY= lines.
if not isinstance(cfg, dict):
    invalid("expected a JSON object")
aab_template = cfg.get("aabPathTemplate", DEFAULT_AAB)
if not isinstance(aab_template, str) or not aab_template.strip():
    invalid("aabPathTemplate must be a non-empty string (remove the key to use the default)")
key = cfg.get("serviceAccountKeyPath")
if key is not None and not isinstance(key, str):
    invalid("serviceAccountKeyPath must be a string")
app_names = cfg.get("appNames")
if app_names is not None and not isinstance(app_names, dict):
    invalid("appNames must be an object (flavor -> Play app name)")

print("CONFIG_PRESENT=1")

key = os.path.expanduser(key or "")
if key and os.path.isfile(key) and os.access(key, os.R_OK):
    print("PHASE=1")
    print(f"SERVICE_ACCOUNT_KEY={key}")
else:
    print("PHASE=2")
    if key:
        print(f"SERVICE_ACCOUNT_KEY_ERROR={key} (configured but missing or unreadable)")

print(f"AAB_PATH_TEMPLATE={aab_template}")

if cfg.get("developerId"):
    print(f"DEVELOPER_ID={cfg['developerId']}")
if cfg.get("teamName"):
    print(f"TEAM_NAME={cfg['teamName']}")
for flavor, name in (app_names or {}).items():
    print(f"APP_NAME_{flavor}={name}")
PY
