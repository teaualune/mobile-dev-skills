#!/bin/bash
# Build script template of the Flutter adapter. The mobile-build-deploy skill
# installs it as scripts/build-version.sh in the target project; adapt the
# "Project config" block below.
#
# Version bookkeeping convention this script maintains in pubspec.yaml:
#   version: <name>+<iosBuild>
#   # android: <androidBuild> = <name> (<iosBuild>)
# The `# android:` comment line tracks the Android versionCode independently of
# the iOS build number. Add both lines to pubspec.yaml before the first run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PUBSPEC="$PROJECT_DIR/pubspec.yaml"

# ── Project config — ADAPT when installing into a project ────────────────────
# App display name, used only in the .xcarchive filename.
APP_NAME="MyApp"
# Flutter command, e.g. "fvm flutter". Keep as is to take FLUTTER_CMD from the
# environment, else auto-detect (fvm rule below); a literal value here wins.
FLUTTER_CMD="${FLUTTER_CMD:-}"
# Build flavors the project defines; the first entry is the default. An app
# without flavors leaves the list empty: it builds without --flavor.
FLAVORS=(staging production)
# Extra `flutter build` arguments: one string per flavor, in FLAVORS order (one
# string for an app without flavors), split on spaces. The entry point when it
# isn't lib/main.dart, and the defines the release needs, e.g.
#   "-t lib/main_production.dart --dart-define-from-file=config/prod.json"
# Both the iOS and the Android build get them, so both must accept each flag.
# The header prints them: secrets and values with spaces go in a define file.
# Empty list ⇒ no extra arguments.
BUILD_ARGS=()
# Xcode scheme / configuration. Leave empty to use the flavor name as the
# scheme and "Release-<flavor>" as the configuration (the common Flutter
# flavor setup), or "Runner" and "Release" for an app without flavors.
XCODE_SCHEME=""
XCODE_CONFIGURATION=""
# Fallback iOS deployment target when it cannot be read from project.pbxproj.
# Set to the project's real minimum — some plugins (e.g. firebase-*) require a
# higher target than Flutter's default.
DEFAULT_IOS_TARGET="15.0"
# Info.plist privacy usage keys that must exist in the archived app before it
# is worth uploading (e.g. NSCameraUsageDescription). List every usage key
# (*UsageDescription) the feature specs declare (section 4, "Permissions &
# capabilities") and the app's plugins require; empty ⇒ check skipped.
REQUIRED_USAGE_KEYS=()
# ─────────────────────────────────────────────────────────────────────────────

FLAVOR=""
FLAVOR_GIVEN=false
VERSION=""
IOS_BUILD=""
ANDROID_BUILD=""
DRY_RUN=false

usage() {
    local flavor_help="doesn't apply: this app has no flavors"
    if [[ ${#FLAVORS[@]} -gt 0 ]]; then
        flavor_help="One of: $(IFS='|'; echo "${FLAVORS[*]}") (default: ${FLAVORS[0]})"
    fi
    echo "Usage: $0 [--version x.x.x] [-i N] [-a N] [--flavor <flavor>] [--dry-run]"
    echo ""
    echo "  -v, --version       New app version name, e.g. 1.2.2 (default: unchanged)"
    echo "  -i, --ios-build     New iOS build number — triggers iOS archive when given"
    echo "  -a, --android-build New Android build number — triggers Android AAB build when given"
    echo "  --flavor            ${flavor_help}"
    echo "  --dry-run           Show expected pubspec.yaml changes without applying them or building"
    echo ""
    echo "At least one of --ios-build or --android-build must be provided."
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--version)       VERSION="$2";       shift 2 ;;
        -i|--ios-build)     IOS_BUILD="$2";     shift 2 ;;
        -a|--android-build) ANDROID_BUILD="$2"; shift 2 ;;
        --flavor)           FLAVOR="$2"; FLAVOR_GIVEN=true; shift 2 ;;
        --dry-run)          DRY_RUN=true;       shift ;;
        -h|--help)          usage; exit 0 ;;
        *) echo "Unknown argument: $1"; usage; exit 1 ;;
    esac
done

# --- Validate ---
if [[ -z "$IOS_BUILD" && -z "$ANDROID_BUILD" ]]; then
    echo "Error: at least one of --ios-build or --android-build must be specified."
    usage
    exit 1
fi

# FLAVOR_IDX picks the flavor's BUILD_ARGS entry; an app without flavors uses entry 0.
FLAVOR_IDX=0
if [[ ${#FLAVORS[@]} -eq 0 ]]; then
    if $FLAVOR_GIVEN; then
        echo "Error: --flavor doesn't apply: this app has no flavors (FLAVORS is empty), got: $FLAVOR"
        exit 1
    fi
else
    if ! $FLAVOR_GIVEN; then
        FLAVOR="${FLAVORS[0]}"
    fi
    FLAVOR_IDX=-1
    for i in "${!FLAVORS[@]}"; do
        if [[ "${FLAVORS[$i]}" == "$FLAVOR" ]]; then FLAVOR_IDX=$i; fi
    done
    if [[ $FLAVOR_IDX -lt 0 ]]; then
        echo "Error: --flavor must be one of: ${FLAVORS[*]}, got: $FLAVOR"
        exit 1
    fi
fi

ARGS_EXPECTED=${#FLAVORS[@]}
if [[ $ARGS_EXPECTED -eq 0 ]]; then ARGS_EXPECTED=1; fi
if [[ ${#BUILD_ARGS[@]} -ne 0 && ${#BUILD_ARGS[@]} -ne $ARGS_EXPECTED ]]; then
    echo "Error: BUILD_ARGS has ${#BUILD_ARGS[@]} entries; it needs one per flavor ($ARGS_EXPECTED), or none."
    exit 1
fi

# Flags every `flutter build` below gets: the flavor, then its BUILD_ARGS entry.
FLUTTER_BUILD_FLAGS=()
if [[ -n "$FLAVOR" ]]; then
    FLUTTER_BUILD_FLAGS+=(--flavor "$FLAVOR")
fi
if [[ ${#BUILD_ARGS[@]} -gt 0 ]]; then
    read -r -a EXTRA_FLAGS <<< "${BUILD_ARGS[$FLAVOR_IDX]}"
    FLUTTER_BUILD_FLAGS+=(${EXTRA_FLAGS[@]+"${EXTRA_FLAGS[@]}"})
fi

flutter_build() {
    $FLUTTER_CMD build "$1" ${FLUTTER_BUILD_FLAGS[@]+"${FLUTTER_BUILD_FLAGS[@]}"} "${@:2}"
}

# fvm rule (non-interactive): .fvmrc pins fvm; a .fvm/ directory alone doesn't.
if [[ -z "$FLUTTER_CMD" ]]; then
    if [[ ! -f "$PROJECT_DIR/.fvmrc" ]]; then
        FLUTTER_CMD="flutter"
    elif command -v fvm >/dev/null 2>&1; then
        FLUTTER_CMD="fvm flutter"
    else
        echo "Error: .fvmrc present but fvm is not installed. Nothing was changed." >&2
        echo "       Install fvm, or override the command: FLUTTER_CMD=flutter $0 …" >&2
        exit 1
    fi
fi
# A pinned or passed-in command is checked too, before pubspec.yaml is touched.
if ! command -v "${FLUTTER_CMD%% *}" >/dev/null 2>&1; then
    echo "Error: FLUTTER_CMD=\"$FLUTTER_CMD\" but '${FLUTTER_CMD%% *}' is not installed. Nothing was changed." >&2
    exit 1
fi

# --- A. Parse current pubspec.yaml values and compute new values ---
CURRENT_VERSION_STRING=$(grep '^version:' "$PUBSPEC" | sed 's/version: *//')
CURRENT_VERSION_NAME=$(echo "$CURRENT_VERSION_STRING" | cut -d'+' -f1)
CURRENT_IOS_BUILD=$(echo "$CURRENT_VERSION_STRING" | cut -d'+' -f2)

CURRENT_ANDROID_LINE=$(grep '^# android:' "$PUBSPEC")
CURRENT_ANDROID_BUILD=$(echo "$CURRENT_ANDROID_LINE" | sed 's/^# android: *//' | awk '{print $1}')
CURRENT_ANDROID_SUFFIX=$(echo "$CURRENT_ANDROID_LINE" | sed 's/^# android: *[0-9]* *= *//')

NEW_VERSION_NAME="${VERSION:-$CURRENT_VERSION_NAME}"
NEW_IOS_BUILD="${IOS_BUILD:-$CURRENT_IOS_BUILD}"
NEW_ANDROID_BUILD="${ANDROID_BUILD:-$CURRENT_ANDROID_BUILD}"

if [[ -n "$ANDROID_BUILD" ]]; then
    if [[ -n "$VERSION" || -n "$IOS_BUILD" ]]; then
        NEW_ANDROID_SUFFIX="${NEW_VERSION_NAME} (${NEW_IOS_BUILD})"
    else
        NEW_ANDROID_SUFFIX="$CURRENT_ANDROID_SUFFIX"
    fi
else
    NEW_ANDROID_SUFFIX="$CURRENT_ANDROID_SUFFIX"
fi

echo "Version:  ${CURRENT_VERSION_NAME}+${CURRENT_IOS_BUILD}  →  ${NEW_VERSION_NAME}+${NEW_IOS_BUILD}"
echo "Android:  $CURRENT_ANDROID_BUILD  →  $NEW_ANDROID_BUILD"
echo "Flavor:   ${FLAVOR:-none}"
echo "Args:     ${FLUTTER_BUILD_FLAGS[*]:-none}"
echo "Flutter:  $FLUTTER_CMD"
echo "Targets:  $([ -n "$ANDROID_BUILD" ] && echo 'Android ✓' || echo 'Android -')   $([ -n "$IOS_BUILD" ] && echo 'iOS ✓' || echo 'iOS -')"
echo ""

if $DRY_RUN; then
    echo "==> [dry-run] pubspec.yaml changes:"
    echo "    version: ${NEW_VERSION_NAME}+${NEW_IOS_BUILD}"
    echo "    # android: ${NEW_ANDROID_BUILD} = ${NEW_ANDROID_SUFFIX}"
    echo ""
    echo "(No files were modified and no builds were run.)"
    exit 0
fi

# Apply version line update
sed -i '' "s|^version: .*|version: ${NEW_VERSION_NAME}+${NEW_IOS_BUILD}|" "$PUBSPEC"

# Apply android comment update only when --android-build is given
if [[ -n "$ANDROID_BUILD" ]]; then
    sed -i '' "s|^# android: .*|# android: ${NEW_ANDROID_BUILD} = ${NEW_ANDROID_SUFFIX}|" "$PUBSPEC"
fi

echo "==> pubspec.yaml updated"

# --- B. iOS config sync: the archive reads the version, entry point and
#        defines from ios/Flutter/Generated.xcconfig. ---
cd "$PROJECT_DIR"
# An Android-only run skips it without ios/ or Xcode.
if [[ -n "$IOS_BUILD" ]] || { [[ -d ios ]] && command -v xcodebuild >/dev/null 2>&1; }; then
    echo ""
    echo "==> Syncing iOS build config..."
    flutter_build ios --config-only --release
fi

# --- C. iOS archive ---
if [[ -n "$IOS_BUILD" ]]; then
    echo ""

    # Guard: FlutterGeneratedPluginSwiftPackage/Package.swift is regenerated at
    # Flutter's default iOS 13.0 on every plugin regeneration (pub get, IDE,
    # build prep). Only `flutter build ios` re-applies the bump to the project's
    # IPHONEOS_DEPLOYMENT_TARGET, and it survives only until the next
    # regeneration. If one slipped in after section B (or the Android build
    # above), xcodebuild's SPM resolution fails here when a plugin requires a
    # higher minimum than the regenerated default (e.g. "firebase-* requires
    # 15.0, target supports 13.0"). Re-sync if needed, then verify, right
    # before handing off to xcodebuild.
    GENERATED_PACKAGE="$PROJECT_DIR/ios/Flutter/ephemeral/Packages/FlutterGeneratedPluginSwiftPackage/Package.swift"
    EXPECTED_IOS_TARGET=$(grep -m1 'IPHONEOS_DEPLOYMENT_TARGET' "$PROJECT_DIR/ios/Runner.xcodeproj/project.pbxproj" | sed -E 's/.*= *([0-9.]+);/\1/' || true)
    EXPECTED_IOS_TARGET="${EXPECTED_IOS_TARGET:-$DEFAULT_IOS_TARGET}"

    if ! grep -q "\.iOS(\"${EXPECTED_IOS_TARGET}\")" "$GENERATED_PACKAGE" 2>/dev/null; then
        echo "==> iOS SPM package not at ${EXPECTED_IOS_TARGET}; re-syncing before archive..."
        flutter_build ios --config-only --release
    fi
    if ! grep -q "\.iOS(\"${EXPECTED_IOS_TARGET}\")" "$GENERATED_PACKAGE" 2>/dev/null; then
        echo "Error: $GENERATED_PACKAGE is not targeting iOS ${EXPECTED_IOS_TARGET}." >&2
        echo "       Found: $(grep -o '\.iOS(\"[0-9.]*\")' "$GENERATED_PACKAGE" 2>/dev/null | head -1)" >&2
        echo "       SPM resolution would fail for plugins requiring iOS ${EXPECTED_IOS_TARGET}. Aborting." >&2
        exit 1
    fi
    echo "    iOS SPM package targets iOS ${EXPECTED_IOS_TARGET} ✓"

    SCHEME="${XCODE_SCHEME:-${FLAVOR:-Runner}}"
    CONFIGURATION="${XCODE_CONFIGURATION:-Release${FLAVOR:+-$FLAVOR}}"

    echo ""
    echo "==> Archiving iOS (scheme: $SCHEME)..."
    ARCHIVE_DATE=$(date +%Y-%m-%d)
    ARCHIVE_TIME=$(date +"%H.%M.%S")
    ARCHIVE_DIR="$HOME/Library/Developer/Xcode/Archives/$ARCHIVE_DATE"
    ARCHIVE_PATH="$ARCHIVE_DIR/$APP_NAME $ARCHIVE_DATE $ARCHIVE_TIME.xcarchive"

    mkdir -p "$ARCHIVE_DIR"

    XCODE_ARGS=(
        archive
        -workspace "$PROJECT_DIR/ios/Runner.xcworkspace"
        -scheme "$SCHEME"
        -configuration "$CONFIGURATION"
        -sdk iphoneos
        -destination "generic/platform=iOS"
        -archivePath "$ARCHIVE_PATH"
    )

    if command -v xcpretty &>/dev/null; then
        xcodebuild "${XCODE_ARGS[@]}" | xcpretty
    else
        xcodebuild "${XCODE_ARGS[@]}"
    fi

    # Validate the archived app's Info.plist before it's worth uploading. Apple's
    # App Store check reads the app-root Info.plist (NOT the localized
    # InfoPlist.strings compiled from InfoPlist.xcstrings), so a privacy usage key
    # that lives only in xcstrings builds fine but fails validation with e.g.
    # "bundle should contain a NSPhotoLibraryUsageDescription key". Catch it here.
    if [[ ${#REQUIRED_USAGE_KEYS[@]} -gt 0 ]]; then
        ARCHIVED_APP=$(ls -d "$ARCHIVE_PATH"/Products/Applications/*.app 2>/dev/null | head -1)
        MISSING_KEYS=()
        for key in "${REQUIRED_USAGE_KEYS[@]}"; do
            /usr/libexec/PlistBuddy -c "Print :$key" "$ARCHIVED_APP/Info.plist" >/dev/null 2>&1 \
                || MISSING_KEYS+=("$key")
        done
        if [[ ${#MISSING_KEYS[@]} -gt 0 ]]; then
            echo "Error: archived Info.plist is missing required usage keys: ${MISSING_KEYS[*]}" >&2
            echo "       These must be in ios/Runner/Info.plist itself, not only in InfoPlist.xcstrings." >&2
            echo "       Archive left at $ARCHIVE_PATH — do NOT upload it." >&2
            exit 1
        fi
        echo "    Info.plist privacy usage descriptions present ✓"
    fi

    echo ""
    echo "iOS archive: $ARCHIVE_PATH"
    echo "View in Xcode Organizer: Window → Organizer"
fi

# --- D. Android AAB build ---
if [[ -n "$ANDROID_BUILD" ]]; then
    echo ""
    echo "==> Building Android AAB (versionCode: $NEW_ANDROID_BUILD)..."
    flutter_build aab --build-number "$NEW_ANDROID_BUILD"
    # The file name follows Gradle's flavor dimensions; the variant folder doesn't.
    if [[ -n "$FLAVOR" ]]; then VARIANT="${FLAVOR}Release"; else VARIANT="release"; fi
    AAB_DIR="$PROJECT_DIR/build/app/outputs/bundle/$VARIANT"
    AABS=()
    for f in "$AAB_DIR"/*.aab; do
        if [[ -f "$f" ]]; then AABS+=("$f"); fi
    done
    if [[ ${#AABS[@]} -ne 1 ]]; then
        echo "Error: expected one .aab in $AAB_DIR, found ${#AABS[@]}: ${AABS[*]:-}" >&2
        exit 1
    fi
    AAB_PATH="${AABS[0]}"
    echo "Output: $AAB_PATH"
fi

# --- E. Artifact manifest — machine-readable paths for the mobile-build-deploy /
#        mobile-store-deploy skills, so the deploy phase never has to find or
#        guess artifact locations. Reflects the latest run only. ---
MANIFEST="$PROJECT_DIR/build/build-version-artifacts.env"
mkdir -p "$PROJECT_DIR/build"
{
    echo "# Generated by scripts/build-version.sh — artifacts of the latest run (values shell-quoted)."
    echo "BUILT_AT=\"$(date +%Y-%m-%dT%H:%M:%S%z)\""
    echo "FLAVOR=\"$FLAVOR\""
    echo "VERSION_NAME=\"$NEW_VERSION_NAME\""
    if [[ -n "$IOS_BUILD" ]]; then
        echo "IOS_BUILD=\"$NEW_IOS_BUILD\""
        echo "IOS_ARCHIVE_PATH=\"$ARCHIVE_PATH\""
    fi
    if [[ -n "$ANDROID_BUILD" ]]; then
        echo "ANDROID_BUILD=\"$NEW_ANDROID_BUILD\""
        echo "ANDROID_AAB_PATH=\"$AAB_PATH\""
    fi
} > "$MANIFEST"

echo ""
echo "==> Artifact manifest written to $MANIFEST"
sed 's/^/    /' "$MANIFEST"

echo ""
echo "Done!"
