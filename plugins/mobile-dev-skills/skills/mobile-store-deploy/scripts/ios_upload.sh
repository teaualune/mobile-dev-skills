#!/usr/bin/env bash
# mobile-store-deploy: merge ExportOptions overrides and upload an .xcarchive
# to App Store Connect (TestFlight) with xcodebuild. Native CLI only — no fastlane.
#
# Usage:
#   ios_upload.sh --archive PATH [--project-config PATH] [--api-key-config PATH]
#                 [--template PATH] [--dry-run]
#
#   --archive         path to the .xcarchive to upload (required)
#   --project-config  path to the project's ios.json (.mobile-store-deploy/ios.json) — verbatim
#                     ExportOptions keys, deep-merged over the template (project wins)
#   --api-key-config  path to the project's ios-api-key.json (.mobile-store-deploy/ios-api-key.json):
#                     {"keyPath": …, "keyID": …, "issuerID": …}; must stay uncommitted
#   --template        ExportOptions template plist
#                     (default: ../templates/ExportOptions.default.plist)
#   --dry-run         merge + validate + print the xcodebuild command, do not run it
#
# Auth: an App Store Connect API key when one is configured — the environment's
# ASC_API_KEY_PATH, ASC_API_KEY_ID and ASC_API_ISSUER_ID (all three), else
# --api-key-config — passed as -authenticationKeyPath/-authenticationKeyID/
# -authenticationKeyIssuerID. Otherwise the Apple ID session saved in Xcode
# (Settings > Accounts), the same session the Organizer wizard uses. The key
# file is referenced by path only; its contents are never read or printed here
# (the key ID and issuer ID are identifiers, not secrets, and are printed).
#
# Exit codes: 0 success (or dry-run OK); 1 xcodebuild failed; 4 usage/config error
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TEMPLATE="$SCRIPT_DIR/../templates/ExportOptions.default.plist"
ARCHIVE=""
PROJECT_CONFIG=""
API_KEY_CONFIG=""
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive) ARCHIVE="$2"; shift 2 ;;
    --project-config) PROJECT_CONFIG="$2"; shift 2 ;;
    --api-key-config) API_KEY_CONFIG="$2"; shift 2 ;;
    --template) TEMPLATE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 4 ;;
  esac
done

[[ -n "$ARCHIVE" ]] || { echo "--archive is required" >&2; exit 4; }
[[ -d "$ARCHIVE" ]] || { echo "archive not found: $ARCHIVE" >&2; exit 4; }
[[ -f "$TEMPLATE" ]] || { echo "template not found: $TEMPLATE" >&2; exit 4; }
if [[ -n "$PROJECT_CONFIG" && ! -f "$PROJECT_CONFIG" ]]; then
  echo "project config not found: $PROJECT_CONFIG" >&2
  exit 4
fi

# --- App Store Connect API key (optional; fail loud on a partial or committable setup) ---
# A file inside the project's git work tree must be ignored and untracked, so it
# can't be committed; a file in another repository (a private secrets repo) is fine.
PROJECT_TOP=$(git rev-parse --show-toplevel 2>/dev/null || true)
must_stay_uncommitted() {
  local file="$1" what="$2" dir base top
  dir=$(cd "$(dirname "$file")" && pwd)
  base=$(basename "$file")
  top=$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null) || return 0
  [[ -z "$PROJECT_TOP" || "$top" == "$PROJECT_TOP" ]] || return 0
  if git -C "$dir" ls-files --error-unmatch -- "$base" >/dev/null 2>&1; then
    echo "$what is tracked by git: $file — it must never be committed (git rm --cached it, then ignore it)." >&2
    exit 4
  fi
  if ! git -C "$dir" check-ignore -q -- "$base"; then
    echo "$what is not gitignored: $file — add it to .gitignore first, or keep it outside the repository." >&2
    exit 4
  fi
}

AUTH_SOURCE=""
KEY_PATH=""; KEY_ID=""; ISSUER_ID=""
if [[ -n "$API_KEY_CONFIG" ]]; then
  [[ -f "$API_KEY_CONFIG" ]] || { echo "API key config not found: $API_KEY_CONFIG" >&2; exit 4; }
  must_stay_uncommitted "$API_KEY_CONFIG" "API key config"
fi
if [[ -n "${ASC_API_KEY_PATH:-}${ASC_API_KEY_ID:-}${ASC_API_ISSUER_ID:-}" ]]; then
  if [[ -z "${ASC_API_KEY_PATH:-}" || -z "${ASC_API_KEY_ID:-}" || -z "${ASC_API_ISSUER_ID:-}" ]]; then
    echo "set all three of ASC_API_KEY_PATH, ASC_API_KEY_ID and ASC_API_ISSUER_ID, or none of them." >&2
    exit 4
  fi
  KEY_PATH="$ASC_API_KEY_PATH"; KEY_ID="$ASC_API_KEY_ID"; ISSUER_ID="$ASC_API_ISSUER_ID"
  AUTH_SOURCE="environment"
elif [[ -n "$API_KEY_CONFIG" ]]; then
  plutil -convert xml1 -o /dev/null "$API_KEY_CONFIG" 2>/dev/null \
    || { echo "API key config is not valid JSON: $API_KEY_CONFIG" >&2; exit 4; }
  KEY_PATH=$(plutil -extract keyPath raw -o - "$API_KEY_CONFIG" 2>/dev/null || true)
  KEY_ID=$(plutil -extract keyID raw -o - "$API_KEY_CONFIG" 2>/dev/null || true)
  ISSUER_ID=$(plutil -extract issuerID raw -o - "$API_KEY_CONFIG" 2>/dev/null || true)
  if [[ -z "$KEY_PATH" || -z "$KEY_ID" || -z "$ISSUER_ID" ]]; then
    echo "API key config needs string values keyPath, keyID and issuerID: $API_KEY_CONFIG" >&2
    exit 4
  fi
  AUTH_SOURCE="$API_KEY_CONFIG"
fi
if [[ -n "$AUTH_SOURCE" ]]; then
  [[ "$KEY_PATH" == "~/"* ]] && KEY_PATH="$HOME/${KEY_PATH#\~/}"
  [[ -f "$KEY_PATH" && -r "$KEY_PATH" ]] || {
    echo "API key file not found or unreadable: $KEY_PATH (from $AUTH_SOURCE)" >&2
    exit 4
  }
  must_stay_uncommitted "$KEY_PATH" "API key file"
fi

WORK=$(mktemp -d -t mobile-store-deploy-ios)
MERGED="$WORK/ExportOptions.plist"
LOG="$WORK/xcodebuild-upload.log"

python3 - "$TEMPLATE" "${PROJECT_CONFIG:-}" "$MERGED" <<'PY'
import json, plistlib, sys

tpl_path, cfg_path, out_path = sys.argv[1:4]
with open(tpl_path, "rb") as f:
    merged = plistlib.load(f)

def deep_merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            deep_merge(dst[k], v)
        else:
            dst[k] = v

if cfg_path:
    with open(cfg_path) as f:
        deep_merge(merged, json.load(f))

with open(out_path, "wb") as f:
    plistlib.dump(merged, f)
PY

# --- validate merged options (fail loud; never guess signing) ---
opt() { plutil -extract "$1" raw -o - "$MERGED" 2>/dev/null || true; }

METHOD=$(opt method)
DESTINATION=$(opt destination)
SIGNING_STYLE=$(opt signingStyle)

[[ "$METHOD" == "app-store-connect" ]] || {
  echo "merged ExportOptions has method='$METHOD' (expected app-store-connect)" >&2
  exit 4
}
[[ "$DESTINATION" == "upload" ]] || {
  echo "merged ExportOptions has destination='$DESTINATION' (expected upload)" >&2
  exit 4
}

EXTRA_FLAGS=()
case "$SIGNING_STYLE" in
  automatic)
    EXTRA_FLAGS=(-allowProvisioningUpdates)
    ;;
  manual)
    if ! plutil -extract provisioningProfiles xml1 -o - "$MERGED" >/dev/null 2>&1; then
      echo "signingStyle=manual but no provisioningProfiles in merged ExportOptions." >&2
      echo "Add them to ${PROJECT_CONFIG:-.mobile-store-deploy/ios.json} — a signing identity is never guessed." >&2
      exit 4
    fi
    ;;
  *)
    echo "signingStyle is missing or invalid in merged ExportOptions (got '${SIGNING_STYLE:-<absent>}')." >&2
    echo "Set \"signingStyle\": \"automatic\" or \"manual\" in ${PROJECT_CONFIG:-.mobile-store-deploy/ios.json}" >&2
    echo "(manual also needs provisioningProfiles + teamID + signingCertificate)." >&2
    exit 4
    ;;
esac

ABID=$(plutil -extract ApplicationProperties.CFBundleIdentifier raw -o - "$ARCHIVE/Info.plist" 2>/dev/null || echo '?')
AVER=$(plutil -extract ApplicationProperties.CFBundleShortVersionString raw -o - "$ARCHIVE/Info.plist" 2>/dev/null || echo '?')
ABUILD=$(plutil -extract ApplicationProperties.CFBundleVersion raw -o - "$ARCHIVE/Info.plist" 2>/dev/null || echo '?')

XCARGS=(-exportArchive -archivePath "$ARCHIVE" -exportOptionsPlist "$MERGED" -exportPath "$WORK/export")
if [[ ${#EXTRA_FLAGS[@]} -gt 0 ]]; then
  XCARGS+=("${EXTRA_FLAGS[@]}")
fi
if [[ -n "$AUTH_SOURCE" ]]; then
  XCARGS+=(-authenticationKeyPath "$KEY_PATH" -authenticationKeyID "$KEY_ID" -authenticationKeyIssuerID "$ISSUER_ID")
  AUTH="App Store Connect API key $KEY_PATH (from $AUTH_SOURCE)"
else
  AUTH="Apple ID session saved in Xcode"
fi

echo "-- effective ExportOptions ($MERGED) --"
plutil -p "$MERGED"
echo "-- auth --"
echo "$AUTH"
echo "-- command --"
printf 'xcodebuild'
printf ' %q' "${XCARGS[@]}"
printf '\n'

if [[ $DRY_RUN -eq 1 ]]; then
  echo "DRY RUN — not uploading."
  exit 0
fi

set +e
xcodebuild "${XCARGS[@]}" 2>&1 | tee "$LOG"
STATUS=${PIPESTATUS[0]}
set -e

echo ""
echo "-- ios_upload report --"
echo "archive     : $ARCHIVE"
echo "bundle id   : $ABID"
echo "version     : $AVER ($ABUILD)"
echo "signing     : $SIGNING_STYLE"
echo "auth        : $AUTH"
echo "log         : $LOG"
if grep -qi 'warning' "$LOG"; then
  echo "warnings from xcodebuild/App Store Connect (first 20):"
  grep -i 'warning' "$LOG" | head -n 20 | sed 's/^/  /'
fi
if [[ $STATUS -eq 0 ]]; then
  echo "result      : SUCCESS — uploaded to App Store Connect (TestFlight processing may take a while)"
else
  echo "result      : FAILED (xcodebuild exit $STATUS)"
  if grep -qiE 'redundant binary|bundle version must be higher|already been uploaded|previously uploaded' "$LOG"; then
    echo "note        : App Store Connect reports a duplicate bundle version — this build was already uploaded." \
         "Do not auto-bump; rebuild with a new build number if a new upload is intended."
  fi
  exit 1
fi
