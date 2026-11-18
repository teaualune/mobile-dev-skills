#!/usr/bin/env bash
# mobile-store-deploy Phase 1: release an .aab to a Google Play testing track
# via the Play Developer API v3 — plain curl + openssl JWT signing. No fastlane.
#
# Usage:
#   android_phase1_upload.sh --package com.example.app --aab PATH --key SERVICE_ACCOUNT.json [--track internal]
#
# Secrets: the service-account key is read from disk into a chmod-700 temp dir
# that is removed on exit; the key contents and OAuth token are never printed.
#
# Exit codes:
#   0  released (edit committed)
#   1  non-auth failure — STOP, do not fall back to Phase 2
#   42 auth/permission failure (HTTP 401/403) — Phase 2 fallback allowed
#   4  usage error
set -euo pipefail

PACKAGE=""
AAB=""
KEY=""
TRACK="internal"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --package) PACKAGE="$2"; shift 2 ;;
    --aab) AAB="$2"; shift 2 ;;
    --key) KEY="$2"; shift 2 ;;
    --track) TRACK="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 4 ;;
  esac
done

[[ -n "$PACKAGE" && -n "$AAB" && -n "$KEY" ]] || { echo "--package, --aab and --key are required" >&2; exit 4; }
[[ -f "$AAB" ]] || { echo "AAB not found: $AAB" >&2; exit 4; }
[[ -r "$KEY" ]] || { echo "service-account key not readable: $KEY" >&2; exit 4; }

umask 077
WORK=$(mktemp -d -t mobile-store-deploy-android)
trap 'rm -rf "$WORK"' EXIT

# --- extract service-account fields (never printed) ---
python3 - "$KEY" "$WORK" <<'PY'
import json, sys
key_path, work = sys.argv[1:3]
with open(key_path) as f:
    sa = json.load(f)
with open(f"{work}/client_email", "w") as f:
    f.write(sa["client_email"])
with open(f"{work}/token_uri", "w") as f:
    f.write(sa.get("token_uri", "https://oauth2.googleapis.com/token"))
with open(f"{work}/private_key.pem", "w") as f:
    f.write(sa["private_key"])
PY

CLIENT_EMAIL=$(cat "$WORK/client_email")
TOKEN_URI=$(cat "$WORK/token_uri")

# --- mint an OAuth token via signed JWT ---
b64url() { openssl base64 -A | tr '+/' '-_' | tr -d '='; }

NOW=$(date +%s)
HEADER=$(printf '{"alg":"RS256","typ":"JWT"}' | b64url)
CLAIMS=$(printf '{"iss":"%s","scope":"https://www.googleapis.com/auth/androidpublisher","aud":"%s","iat":%s,"exp":%s}' \
  "$CLIENT_EMAIL" "$TOKEN_URI" "$NOW" "$((NOW + 3600))" | b64url)
SIG=$(printf '%s.%s' "$HEADER" "$CLAIMS" | openssl dgst -sha256 -sign "$WORK/private_key.pem" -binary | b64url)

HTTP=$(curl -sS -o "$WORK/token.json" -w '%{http_code}' -X POST "$TOKEN_URI" \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer' \
  --data-urlencode "assertion=$HEADER.$CLAIMS.$SIG")
if [[ "$HTTP" != "200" ]]; then
  echo "OAuth token request failed (HTTP $HTTP):" >&2
  cat "$WORK/token.json" >&2
  echo "" >&2
  if [[ "$HTTP" == "401" || "$HTTP" == "403" ]]; then
    exit 42
  fi
  exit 1
fi
ACCESS_TOKEN=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["access_token"])' "$WORK/token.json")

API="https://androidpublisher.googleapis.com/androidpublisher/v3/applications/$PACKAGE"

api_call() { # METHOD URL [extra curl args...] — body written to $WORK/resp.json, prints HTTP code
  local method="$1" url="$2"
  shift 2
  curl -sS -o "$WORK/resp.json" -w '%{http_code}' -X "$method" \
    -H "Authorization: Bearer $ACCESS_TOKEN" "$@" "$url"
}

check() { # HTTP_CODE STEP_NAME
  local http="$1" step="$2"
  if [[ "$http" == "401" || "$http" == "403" ]]; then
    echo "$step failed (HTTP $http — auth/permission):" >&2
    cat "$WORK/resp.json" >&2
    echo "" >&2
    exit 42
  fi
  if [[ "$http" != 2?? ]]; then
    echo "$step failed (HTTP $http):" >&2
    cat "$WORK/resp.json" >&2
    echo "" >&2
    if grep -qi 'already been used' "$WORK/resp.json"; then
      echo "NOTE: duplicate upload — this version code already exists on Play." \
           "Do not auto-bump; rebuild with a new version code if a new release is intended." >&2
    fi
    exit 1
  fi
}

echo "[1/4] edits.insert"
HTTP=$(api_call POST "$API/edits")
check "$HTTP" "edits.insert"
EDIT_ID=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "$WORK/resp.json")

echo "[2/4] edits.bundles.upload ($AAB)"
HTTP=$(api_call POST "https://androidpublisher.googleapis.com/upload/androidpublisher/v3/applications/$PACKAGE/edits/$EDIT_ID/bundles?uploadType=media" \
  -H 'Content-Type: application/octet-stream' --data-binary "@$AAB")
check "$HTTP" "edits.bundles.upload"
VERSION_CODE=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["versionCode"])' "$WORK/resp.json")

echo "[3/4] edits.tracks.update (track=$TRACK, status=completed, no release notes)"
HTTP=$(api_call PUT "$API/edits/$EDIT_ID/tracks/$TRACK" \
  -H 'Content-Type: application/json' \
  -d "{\"track\":\"$TRACK\",\"releases\":[{\"status\":\"completed\",\"versionCodes\":[\"$VERSION_CODE\"]}]}")
check "$HTTP" "edits.tracks.update"

echo "[4/4] edits.commit"
HTTP=$(api_call POST "$API/edits/$EDIT_ID:commit")
check "$HTTP" "edits.commit"

echo ""
echo "-- android_phase1 report --"
echo "package     : $PACKAGE"
echo "aab         : $AAB"
echo "versionCode : $VERSION_CODE"
echo "track       : $TRACK (status: completed, no release notes)"
echo "result      : SUCCESS — edit $EDIT_ID committed"
