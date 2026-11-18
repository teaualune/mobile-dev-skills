# Trademark & third-party disclaimers

Informational notices — not part of the MIT License in [`LICENSE`](LICENSE).

"Claude", "Claude Code", and "Anthropic" are trademarks of Anthropic,
PBC. This project is an independent, community-made bundle of skill
files for use with Claude Code. It is not affiliated with, sponsored
by, or endorsed by Anthropic. The license applies only to the
contents of this repository and grants no rights to the "Claude" or
"Anthropic" names, trademarks, or products. References to Claude and
Claude Code in this repository serve solely to identify the tool these
skills are designed to run with.

"Flutter" and "Dart" are trademarks of Google LLC. This project is not
affiliated with, sponsored by, or endorsed by Google or the Flutter
team, and the license grants no rights to those names or
trademarks.

"Kotlin", "Jetpack Compose", "Android Studio" and "Gradle" are
trademarks of their respective owners. This project is not affiliated
with, sponsored by, or endorsed by any of them, and the license grants
no rights to those names or trademarks.

"Apple", "App Store Connect", "TestFlight", "Xcode", "iOS", and
"Swift" are trademarks of Apple Inc. "Google Play", "Play Console",
"Google Cloud", "Android", and "Chrome" are trademarks of Google LLC.
The build and store-deploy skills in this repository invoke publicly
documented first-party tooling — `xcodebuild`, the Xcode account
session, and the Google Play Developer API — to upload artifacts the
user has already built. This project is not affiliated with, sponsored
by, or endorsed by Apple or Google; the license grants no rights
to those names, trademarks, or products, and those names appear solely
to identify the platforms and interfaces the skills target. Use of
those platforms remains governed by the user's own agreements with
Apple and Google (e.g. the Apple Developer Program License Agreement
and the Google Play Developer Distribution Agreement), including the
terms covering API credentials and automated access.

"Firebase" and "Crashlytics" are trademarks of Google LLC, and "Figma"
is a trademark of Figma, Inc. The skills name them only to identify
what a design reference or a crash report comes from, and where
another tool takes over. This project is not affiliated with,
sponsored by, or endorsed by Google or Figma, and the license grants
no rights to those names or trademarks.

The Flutter/Dart packages, Android and Kotlin libraries, and
command-line tools referenced in this repository — including but not
limited to Riverpod, go_router, Dio, freezed, json_serializable,
build_runner, bloc/flutter_bloc, provider, GetX, MobX, auto_route,
chopper, retrofit, get_it, fvm, Hilt and Dagger, Navigation Compose,
Retrofit, OkHttp, kotlinx.serialization, Room, Coil, Robolectric,
Turbine, MockWebServer, ktlint, detekt, xcpretty, bundletool, fastlane,
curl, and OpenSSL, and others named in the skill files — are the
property of their respective authors and are governed by their own
licenses. This repository does not bundle or redistribute
any of these packages or tools; their names appear solely to identify
the technologies the generated code may target or that the scripts may
invoke. No affiliation with or endorsement by any author is implied.

The agents in `agents/` are adapted from ECC (github.com/affaan-m/ECC)
under its MIT License; [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)
reproduces that license, and no affiliation with or endorsement by
ECC's author is implied.

**No warranty / operational risk.** The material in this repository is
provided "as is", without warranty of any kind. This matters most for
the build and deploy skills, which do things that are not free to get
wrong: they edit `pubspec.yaml` or an Xcode project's version settings
(`project.pbxproj`, an `.xcconfig`, `Info.plist` files), run builds,
read a Google Play service-account key and an App Store Connect API key
from paths the user supplies, upload binaries to
App Store Connect and to a Google Play testing track, and can drive a
browser session that is already signed in to the user's Play Console.
Store uploads are effectively permanent per build number and a Play
rollout is a publish. Review what these skills are about to run before
approving it, keep credentials outside the repository, and treat the
resulting releases as your own — the authors accept no liability for
any build, upload, release, credential exposure, or account
consequence arising from their use.
