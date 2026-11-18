#!/usr/bin/env bash
# mobile-store-deploy: locate and select an .xcarchive by bundle ID + version.
# The CLI replacement for browsing Xcode Organizer.
#
# Usage:
#   ios_find_archive.sh --bundle-id com.example.app [--version 1.2.3] [--build 45] [--archives-dir DIR]
#
# On success prints KEY=VALUE lines:
#   ARCHIVE_PATH=..., BUNDLE_ID=..., VERSION=..., BUILD=..., CREATION_DATE=...
#
# Exit codes:
#   0 exactly one archive selected
#   2 ambiguous — candidates listed on stderr (disambiguate with --build)
#   3 no match — everything discovered listed on stderr
#   4 usage error
set -euo pipefail

BUNDLE_ID=""
WANT_VERSION=""
WANT_BUILD=""
ARCHIVES_DIR="$HOME/Library/Developer/Xcode/Archives"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bundle-id) BUNDLE_ID="$2"; shift 2 ;;
    --version) WANT_VERSION="$2"; shift 2 ;;
    --build) WANT_BUILD="$2"; shift 2 ;;
    --archives-dir) ARCHIVES_DIR="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 4 ;;
  esac
done

[[ -n "$BUNDLE_ID" ]] || { echo "--bundle-id is required" >&2; exit 4; }
[[ -d "$ARCHIVES_DIR" ]] || { echo "archives directory not found: $ARCHIVES_DIR" >&2; exit 4; }

prop() { plutil -extract "ApplicationProperties.$1" raw -o - "$2" 2>/dev/null; }

candidates=()  # "created<TAB>version<TAB>build<TAB>path" — archives matching all filters
all_seen=()    # "bundleid<TAB>version<TAB>build<TAB>path" — every archive discovered

while IFS= read -r -d '' archive; do
  info="$archive/Info.plist"
  [[ -f "$info" ]] || continue
  bid=$(prop CFBundleIdentifier "$info") || continue
  ver=$(prop CFBundleShortVersionString "$info" || echo '?')
  build=$(prop CFBundleVersion "$info" || echo '?')
  created=$(plutil -extract CreationDate raw -o - "$info" 2>/dev/null || echo '1970-01-01T00:00:00Z')
  all_seen+=("$bid"$'\t'"$ver"$'\t'"$build"$'\t'"$archive")
  [[ "$bid" == "$BUNDLE_ID" ]] || continue
  [[ -z "$WANT_VERSION" || "$ver" == "$WANT_VERSION" ]] || continue
  [[ -z "$WANT_BUILD" || "$build" == "$WANT_BUILD" ]] || continue
  candidates+=("$created"$'\t'"$ver"$'\t'"$build"$'\t'"$archive")
done < <(find "$ARCHIVES_DIR" -maxdepth 2 -type d -name '*.xcarchive' -print0)

count=${#candidates[@]}

if [[ $count -eq 0 ]]; then
  {
    echo "No archive matches bundle ID '$BUNDLE_ID'${WANT_VERSION:+, version $WANT_VERSION}${WANT_BUILD:+, build $WANT_BUILD} under $ARCHIVES_DIR"
    echo "Discovered archives (bundle id / version / build / path):"
    if [[ ${#all_seen[@]} -eq 0 ]]; then
      echo "  (none)"
    else
      printf '  %s\n' "${all_seen[@]}"
    fi
  } >&2
  exit 3
fi

if [[ -n "$WANT_VERSION$WANT_BUILD" && $count -gt 1 ]]; then
  {
    echo "Ambiguous: $count archives match bundle ID '$BUNDLE_ID'${WANT_VERSION:+, version $WANT_VERSION}${WANT_BUILD:+, build $WANT_BUILD}."
    echo "Candidates (created / version / build / path):"
    printf '  %s\n' "${candidates[@]}"
    echo "Disambiguate with --build (or a more specific --version)."
  } >&2
  exit 2
fi

selected=$(printf '%s\n' "${candidates[@]}" | sort -r | head -n 1)
IFS=$'\t' read -r created ver build archive <<<"$selected"

echo "ARCHIVE_PATH=$archive"
echo "BUNDLE_ID=$BUNDLE_ID"
echo "VERSION=$ver"
echo "BUILD=$build"
echo "CREATION_DATE=$created"
