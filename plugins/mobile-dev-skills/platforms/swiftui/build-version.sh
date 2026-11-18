#!/bin/bash
# Build script template of the SwiftUI adapter (native iOS apps). The
# mobile-build-deploy skill installs it as scripts/build-version.sh in the
# target project; adapt the "Project config" block below.
#
# Version bookkeeping: MARKETING_VERSION (the version) and
# CURRENT_PROJECT_VERSION (the build number), edited where VERSION_SOURCE says.
# The script reads both back before archiving and checks the archived
# Info.plist after it; a mismatch stops it before anything is uploaded.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Project config — ADAPT when installing into a project ────────────────────
# App display name, used only in the .xcarchive filename.
APP_NAME="MyApp"
# The Xcode project, and the workspace when the app is built from one
# (CocoaPods, several projects); paths relative to the project root.
XCODE_PROJECT="MyApp.xcodeproj"
XCODE_WORKSPACE=""
# Build flavors, each with the scheme and the build configuration it archives:
# same order in all three lists; the first flavor is the default. An app
# without flavors keeps one entry.
FLAVORS=(production)
SCHEMES=(MyApp)
CONFIGURATIONS=(Release)
# Where the version lives:
#   project           the project file's lines that hold the app target's
#                     current MARKETING_VERSION / CURRENT_PROJECT_VERSION
#   <path>.xcconfig   that file's MARKETING_VERSION / CURRENT_PROJECT_VERSION
#                     lines (e.g. a project XcodeGen or Tuist generates)
#   agvtool           agvtool new-marketing-version / new-version -all (an
#                     older project whose Info.plist holds literal values)
VERSION_SOURCE="project"
# Info.plist privacy usage keys that must exist in the archived app before it
# is worth uploading (e.g. NSCameraUsageDescription), whether they come from
# the Info.plist file or an INFOPLIST_KEY_ build setting. List every usage key
# (*UsageDescription) the feature specs declare (section 4, "Permissions &
# capabilities") and the app's libraries require; empty ⇒ check skipped.
REQUIRED_USAGE_KEYS=()
# Extra xcodebuild arguments for the archive, e.g. (-allowProvisioningUpdates)
# when automatic signing has to fetch profiles.
XCODEBUILD_EXTRA_ARGS=()
# ─────────────────────────────────────────────────────────────────────────────

FLAVOR="${FLAVORS[0]}"
VERSION=""
IOS_BUILD=""
ANDROID_BUILD=""
DRY_RUN=false

usage() {
    local flavors_disp
    flavors_disp=$(IFS='|'; echo "${FLAVORS[*]}")
    echo "Usage: $0 [--version x.y.z] -i N [--flavor ${flavors_disp}] [--dry-run]"
    echo ""
    echo "  -v, --version       New version (MARKETING_VERSION), e.g. 1.2.2 (default: unchanged)"
    echo "  -i, --ios-build     New build number (CURRENT_PROJECT_VERSION) — required; archives the app"
    echo "  -a, --android-build Not applicable: this script builds the iOS app only"
    echo "  --flavor            One of: ${flavors_disp} (default: ${FLAVORS[0]})"
    echo "  --dry-run           Show the current and new versions without applying them or building"
    echo "                      (-i may be left out to see the current values)"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--version)       VERSION="$2";       shift 2 ;;
        -i|--ios-build)     IOS_BUILD="$2";     shift 2 ;;
        -a|--android-build) ANDROID_BUILD="$2"; shift 2 ;;
        --flavor)           FLAVOR="$2";        shift 2 ;;
        --dry-run)          DRY_RUN=true;       shift ;;
        -h|--help)          usage; exit 0 ;;
        *) echo "Unknown argument: $1"; usage; exit 1 ;;
    esac
done

fail() {
    echo "Error: $*" >&2
    exit 1
}

# --- Validate (nothing is changed before this block passes) ---
[[ -z "$ANDROID_BUILD" ]] || fail "-a/--android-build doesn't apply: this script builds the iOS app only. Nothing was changed."
if [[ -z "$IOS_BUILD" ]] && ! $DRY_RUN; then
    echo "Error: --ios-build is required."
    usage
    exit 1
fi
# CFBundleShortVersionString and CFBundleVersion: up to three period-separated integers.
NUMBER_RE='^[0-9]+(\.[0-9]+){0,2}$'
[[ -z "$IOS_BUILD" || "$IOS_BUILD" =~ $NUMBER_RE ]] || fail "--ios-build must be up to three period-separated integers, got: $IOS_BUILD"
[[ -z "$VERSION" || "$VERSION" =~ $NUMBER_RE ]] || fail "--version must be up to three period-separated integers, got: $VERSION"

[[ ${#SCHEMES[@]} -eq ${#FLAVORS[@]} && ${#CONFIGURATIONS[@]} -eq ${#FLAVORS[@]} ]] \
    || fail "FLAVORS, SCHEMES and CONFIGURATIONS must have one entry each per flavor (ADAPT block)."
IDX=-1
for i in "${!FLAVORS[@]}"; do
    [[ "${FLAVORS[$i]}" == "$FLAVOR" ]] && IDX=$i
done
[[ $IDX -ge 0 ]] || fail "--flavor must be one of: ${FLAVORS[*]}, got: $FLAVOR"
SCHEME="${SCHEMES[$IDX]}"
CONFIGURATION="${CONFIGURATIONS[$IDX]}"

cd "$PROJECT_DIR"
[[ -d "$XCODE_PROJECT" ]] \
    || fail "XCODE_PROJECT not found: $PROJECT_DIR/$XCODE_PROJECT (ADAPT block; a project XcodeGen or Tuist generates must be generated first)."
if [[ -n "$XCODE_WORKSPACE" ]]; then
    [[ -d "$XCODE_WORKSPACE" ]] || fail "XCODE_WORKSPACE not found: $PROJECT_DIR/$XCODE_WORKSPACE (ADAPT block)."
    CONTAINER=(-workspace "$XCODE_WORKSPACE")
else
    CONTAINER=(-project "$XCODE_PROJECT")
fi

command -v xcodebuild >/dev/null 2>&1 || fail "xcodebuild is not installed. Nothing was changed."
XCODE_VERSION_OUT=$(xcodebuild -version 2>&1) \
    || fail "xcodebuild can't run ($(printf '%s\n' "$XCODE_VERSION_OUT" | head -n 1)). Nothing was changed."
XCODE_VERSION=$(printf '%s\n' "$XCODE_VERSION_OUT" | head -n 1)

case "$VERSION_SOURCE" in
    project) VERSION_FILE="$XCODE_PROJECT/project.pbxproj" ;;
    agvtool)
        command -v agvtool >/dev/null 2>&1 || fail "VERSION_SOURCE=agvtool but agvtool is not installed."
        VERSION_FILE="" ;;
    *.xcconfig)
        [[ -f "$VERSION_SOURCE" ]] || fail "VERSION_SOURCE file not found: $PROJECT_DIR/$VERSION_SOURCE"
        VERSION_FILE="$VERSION_SOURCE" ;;
    *) fail "VERSION_SOURCE must be project, agvtool or a path to an .xcconfig file, got: $VERSION_SOURCE" ;;
esac

# The scheme's app target, tab-separated: MARKETING_VERSION, CURRENT_PROJECT_VERSION,
# PRODUCT_BUNDLE_IDENTIFIER, CONFIGURATION (xcodebuild falls back to another one
# for a name the project lacks), and its Info.plist file (empty when generated).
read_settings() {
    local out
    if ! out=$(xcodebuild "${CONTAINER[@]}" -scheme "$SCHEME" -configuration "$CONFIGURATION" -sdk iphoneos -showBuildSettings 2>&1); then
        echo "Error: xcodebuild -showBuildSettings failed for scheme '$SCHEME', configuration '$CONFIGURATION':" >&2
        printf '%s\n' "$out" | tail -n 15 >&2
        return 1
    fi
    printf '%s\n' "$out" | awk '
        function flush() {
            if (app && !done) {
                if (plist != "" && substr(plist, 1, 1) != "/") plist = src "/" plist
                print mv "\t" bv "\t" id "\t" conf "\t" plist; done = 1
            }
            mv = ""; bv = ""; id = ""; conf = ""; src = ""; plist = ""; app = 0
        }
        /^Build settings for action / { flush(); next }
        /^    MARKETING_VERSION = / { mv = substr($0, index($0, "= ") + 2) }
        /^    CURRENT_PROJECT_VERSION = / { bv = substr($0, index($0, "= ") + 2) }
        /^    PRODUCT_BUNDLE_IDENTIFIER = / { id = substr($0, index($0, "= ") + 2) }
        /^    CONFIGURATION = / { conf = substr($0, index($0, "= ") + 2) }
        /^    SRCROOT = / { src = substr($0, index($0, "= ") + 2) }
        /^    INFOPLIST_FILE = / { plist = substr($0, index($0, "= ") + 2) }
        /^    PRODUCT_TYPE = com\.apple\.product-type\.application$/ { app = 1 }
        END { flush() }'
}

# The app target's version and build number, tab-separated: with agvtool, the
# literal values in its own Info.plist (agvtool's -terse1 reads whichever plist
# it lists first); otherwise MARKETING_VERSION and CURRENT_PROJECT_VERSION.
read_versions() {
    local s
    s=$(read_settings) || return 1
    if [[ "$VERSION_SOURCE" == agvtool ]]; then
        printf '%s\t%s\n' "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' "$APP_PLIST" 2>/dev/null || true)" \
                           "$(/usr/libexec/PlistBuddy -c 'Print :CFBundleVersion' "$APP_PLIST" 2>/dev/null || true)"
    else
        printf '%s\n' "$s" | cut -f1,2
    fi
}

ere_escape() { printf '%s' "$1" | sed 's#[][\.*^$/(){}+?|]#\\&#g'; }

# Lines of the project file holding the app target's current value of setting $1.
pbx_lines() {
    grep -cE "^[[:space:]]*$1 = \"?$(ere_escape "$2")\"?;" "$VERSION_FILE" || true
}
# Lines of the .xcconfig that set $1.
xcconfig_lines() {
    grep -cE "^[[:space:]]*$1[[:space:]]*=" "$VERSION_FILE" || true
}

SETTINGS=$(read_settings) || exit 1
[[ -n "$SETTINGS" ]] || fail "scheme '$SCHEME' builds no iOS app target (configuration '$CONFIGURATION')."
BUNDLE_ID=$(printf '%s\n' "$SETTINGS" | cut -f3)
READ_CONFIGURATION=$(printf '%s\n' "$SETTINGS" | cut -f4)
[[ "$READ_CONFIGURATION" == "$CONFIGURATION" ]] \
    || fail "the project has no build configuration '$CONFIGURATION' (xcodebuild would use '$READ_CONFIGURATION'): fix CONFIGURATIONS in the ADAPT block. Nothing was changed."
APP_PLIST=$(printf '%s\n' "$SETTINGS" | cut -f5)
if [[ "$VERSION_SOURCE" == agvtool && ! -f "$APP_PLIST" ]]; then
    fail "VERSION_SOURCE=agvtool needs the app target's own Info.plist file (INFOPLIST_FILE), got '${APP_PLIST}': use VERSION_SOURCE=project. Nothing was changed."
fi
VERSIONS=$(read_versions) || exit 1
CURRENT_VERSION=$(printf '%s\n' "$VERSIONS" | cut -f1)
CURRENT_BUILD=$(printf '%s\n' "$VERSIONS" | cut -f2)
[[ -n "$CURRENT_VERSION" && -n "$CURRENT_BUILD" ]] \
    || fail "can't read the current version through VERSION_SOURCE=$VERSION_SOURCE (got '${CURRENT_VERSION}' / '${CURRENT_BUILD}'). Nothing was changed."

NEW_VERSION="${VERSION:-$CURRENT_VERSION}"
NEW_BUILD="${IOS_BUILD:-$CURRENT_BUILD}"

case "$VERSION_SOURCE" in
    project)
        MV_LINES=$(pbx_lines MARKETING_VERSION "$CURRENT_VERSION")
        BV_LINES=$(pbx_lines CURRENT_PROJECT_VERSION "$CURRENT_BUILD")
        [[ $MV_LINES -gt 0 && $BV_LINES -gt 0 ]] \
            || fail "$VERSION_FILE has no MARKETING_VERSION = $CURRENT_VERSION or CURRENT_PROJECT_VERSION = $CURRENT_BUILD line, so another file sets them (an .xcconfig?): point VERSION_SOURCE at it. Nothing was changed."
        WHERE="$VERSION_FILE ($MV_LINES + $BV_LINES lines)" ;;
    agvtool)
        WHERE="agvtool (every target's Info.plist and the project file)" ;;
    *)
        MV_LINES=$(xcconfig_lines MARKETING_VERSION)
        BV_LINES=$(xcconfig_lines CURRENT_PROJECT_VERSION)
        [[ $MV_LINES -gt 0 && $BV_LINES -gt 0 ]] \
            || fail "$VERSION_FILE sets no MARKETING_VERSION or CURRENT_PROJECT_VERSION. Nothing was changed."
        WHERE="$VERSION_FILE" ;;
esac

echo "Version:  ${CURRENT_VERSION} (${CURRENT_BUILD})  →  ${NEW_VERSION} (${NEW_BUILD})"
echo "Flavor:   $FLAVOR (scheme: $SCHEME, configuration: $CONFIGURATION)"
echo "Bundle:   $BUNDLE_ID"
echo "Xcode:    $XCODE_VERSION"
echo "Source:   $WHERE"
echo "Targets:  iOS ✓"
echo ""

if $DRY_RUN; then
    echo "==> [dry-run] version changes:"
    echo "    MARKETING_VERSION        ${CURRENT_VERSION} → ${NEW_VERSION}"
    echo "    CURRENT_PROJECT_VERSION  ${CURRENT_BUILD} → ${NEW_BUILD}"
    echo ""
    echo "(No files were modified and no builds were run.)"
    exit 0
fi

# --- A. Version bump (idempotent: a re-run after a failed build is safe) ---
case "$VERSION_SOURCE" in
    project)
        sed -i '' -E "s/^([[:space:]]*MARKETING_VERSION = )\"?$(ere_escape "$CURRENT_VERSION")\"?;/\1${NEW_VERSION};/" "$VERSION_FILE"
        sed -i '' -E "s/^([[:space:]]*CURRENT_PROJECT_VERSION = )\"?$(ere_escape "$CURRENT_BUILD")\"?;/\1${NEW_BUILD};/" "$VERSION_FILE" ;;
    agvtool)
        AGV_LOG=$(cd "$(dirname "$XCODE_PROJECT")" \
            && agvtool new-marketing-version "$NEW_VERSION" 2>&1 \
            && agvtool new-version -all "$NEW_BUILD" 2>&1) \
            || { printf '%s\n' "$AGV_LOG" | tail -n 15 >&2; fail "agvtool failed."; } ;;
    *)
        sed -i '' -E "s/^([[:space:]]*MARKETING_VERSION[[:space:]]*=[[:space:]]*)[^[:space:]/;]*/\1${NEW_VERSION}/" "$VERSION_FILE"
        sed -i '' -E "s/^([[:space:]]*CURRENT_PROJECT_VERSION[[:space:]]*=[[:space:]]*)[^[:space:]/;]*/\1${NEW_BUILD}/" "$VERSION_FILE" ;;
esac

VERSIONS=$(read_versions) || exit 1
READ_VERSION=$(printf '%s\n' "$VERSIONS" | cut -f1)
READ_BUILD=$(printf '%s\n' "$VERSIONS" | cut -f2)
if [[ "$READ_VERSION" != "$NEW_VERSION" || "$READ_BUILD" != "$NEW_BUILD" ]]; then
    echo "Error: after the edit the app target reads ${READ_VERSION} (${READ_BUILD}), not ${NEW_VERSION} (${NEW_BUILD})." >&2
    echo "       Something else sets the version (an .xcconfig, a per-configuration value): point VERSION_SOURCE there." >&2
    echo "       The edit to $WHERE is left in place; re-running after the fix is safe." >&2
    exit 1
fi
echo "==> Version set to ${NEW_VERSION} (${NEW_BUILD}) in $WHERE"

# --- B. iOS archive ---
echo ""
echo "==> Archiving iOS (scheme: $SCHEME, configuration: $CONFIGURATION)..."
ARCHIVE_DATE=$(date +%Y-%m-%d)
ARCHIVE_TIME=$(date +"%H.%M.%S")
ARCHIVE_DIR="$HOME/Library/Developer/Xcode/Archives/$ARCHIVE_DATE"
ARCHIVE_PATH="$ARCHIVE_DIR/$APP_NAME $ARCHIVE_DATE $ARCHIVE_TIME.xcarchive"

mkdir -p "$ARCHIVE_DIR"

XCODE_ARGS=(
    archive
    "${CONTAINER[@]}"
    -scheme "$SCHEME"
    -configuration "$CONFIGURATION"
    -sdk iphoneos
    -destination "generic/platform=iOS"
    -archivePath "$ARCHIVE_PATH"
)
if [[ ${#XCODEBUILD_EXTRA_ARGS[@]} -gt 0 ]]; then
    XCODE_ARGS+=("${XCODEBUILD_EXTRA_ARGS[@]}")
fi

if command -v xcpretty &>/dev/null; then
    xcodebuild "${XCODE_ARGS[@]}" | xcpretty
else
    xcodebuild "${XCODE_ARGS[@]}"
fi

ARCHIVED_APP=$(ls -d "$ARCHIVE_PATH"/Products/Applications/*.app 2>/dev/null | head -n 1 || true)
[[ -n "$ARCHIVED_APP" ]] || fail "no app in $ARCHIVE_PATH/Products/Applications — do NOT upload it."

# The archived Info.plist is what App Store Connect reads: check the version
# and the usage keys there, whichever setting produced them.
plist_value() { /usr/libexec/PlistBuddy -c "Print :$1" "$ARCHIVED_APP/Info.plist" 2>/dev/null || true; }
ARCHIVED_VERSION=$(plist_value CFBundleShortVersionString)
ARCHIVED_BUILD=$(plist_value CFBundleVersion)
if [[ "$ARCHIVED_VERSION" != "$NEW_VERSION" || "$ARCHIVED_BUILD" != "$NEW_BUILD" ]]; then
    echo "Error: the archived app is ${ARCHIVED_VERSION} (${ARCHIVED_BUILD}), not ${NEW_VERSION} (${NEW_BUILD})." >&2
    if [[ "$VERSION_SOURCE" == agvtool ]]; then
        echo "       A target that generates its Info.plist (GENERATE_INFOPLIST_FILE) takes the version from MARKETING_VERSION / CURRENT_PROJECT_VERSION over the file's values: use VERSION_SOURCE=project." >&2
    else
        echo "       Its Info.plist may hold literal version values: use VERSION_SOURCE=agvtool, or set them to \$(MARKETING_VERSION) and \$(CURRENT_PROJECT_VERSION)." >&2
    fi
    echo "       Archive left at $ARCHIVE_PATH — do NOT upload it." >&2
    exit 1
fi
echo "    Archived version ${ARCHIVED_VERSION} (${ARCHIVED_BUILD}) ✓"

# A usage key that lives only in a localized InfoPlist.xcstrings builds fine
# but fails App Store validation ("bundle should contain a … key").
if [[ ${#REQUIRED_USAGE_KEYS[@]} -gt 0 ]]; then
    MISSING_KEYS=()
    for key in "${REQUIRED_USAGE_KEYS[@]}"; do
        /usr/libexec/PlistBuddy -c "Print :$key" "$ARCHIVED_APP/Info.plist" >/dev/null 2>&1 \
            || MISSING_KEYS+=("$key")
    done
    if [[ ${#MISSING_KEYS[@]} -gt 0 ]]; then
        echo "Error: archived Info.plist is missing required usage keys: ${MISSING_KEYS[*]}" >&2
        echo "       Add each to the target's Info.plist, or as an INFOPLIST_KEY_<key> build setting — not only to InfoPlist.xcstrings." >&2
        echo "       Archive left at $ARCHIVE_PATH — do NOT upload it." >&2
        exit 1
    fi
    echo "    Info.plist privacy usage descriptions present ✓"
fi

echo ""
echo "iOS archive: $ARCHIVE_PATH"
echo "View in Xcode Organizer: Window → Organizer"

# --- C. Artifact manifest — machine-readable paths for the mobile-build-deploy /
#        mobile-store-deploy skills, so the deploy phase never has to find or
#        guess artifact locations. Reflects the latest run only. ---
MANIFEST="$PROJECT_DIR/build/build-version-artifacts.env"
mkdir -p "$PROJECT_DIR/build"
{
    echo "# Generated by scripts/build-version.sh — artifacts of the latest run (values shell-quoted)."
    echo "BUILT_AT=\"$(date +%Y-%m-%dT%H:%M:%S%z)\""
    echo "FLAVOR=\"$FLAVOR\""
    echo "VERSION_NAME=\"$NEW_VERSION\""
    echo "IOS_BUILD=\"$NEW_BUILD\""
    echo "IOS_ARCHIVE_PATH=\"$ARCHIVE_PATH\""
} > "$MANIFEST"

echo ""
echo "==> Artifact manifest written to $MANIFEST"
sed 's/^/    /' "$MANIFEST"

echo ""
echo "Done!"
