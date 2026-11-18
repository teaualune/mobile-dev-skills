# Standards — Flutter

Flutter rules, on top of the common `../standards.md`. They apply to all hand-written Dart code, on top of the detected conventions.

## Code

- **No null-assertion operator (`!`) in hand-written code.** Extract the nullable expression into a local variable, null-check it, then use the promoted local — fields don't promote, so the local is required:

  ```dart
  // Bad:  if (card.foo != null) use(card.foo!);
  // Good:
  final foo = card.foo;
  if (foo != null) use(foo);
  ```

  For nullable-returning calls (e.g. `Color.lerp(...)`), prefer `?? <sensible fallback>` over `!`. Exempt: generated files (`*.g.dart`, `*.freezed.dart`, generated l10n output) and the `is!` type-test operator, which is not a null assertion.

- **Refreshable scroll view skeleton.** For complicated scroll views — heterogeneous blocks, especially with pull-to-refresh — use this structure instead of `ListView`:

  ```dart
  RefreshIndicator.adaptive(
    onRefresh: ...,
    child: SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      child: SafeArea( // SafeArea is the FIRST child of the scroll view — do not wrap RefreshIndicator with it
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [ /* blocks */ ],
        ),
      ),
    ),
  )
  ```

  Why this shape: `SingleChildScrollView` + `Column` handles heterogeneous blocks better than `ListView`; `AlwaysScrollableScrollPhysics` keeps pull-to-refresh firing when content is shorter than the viewport; `SafeArea` inside the scroll view keeps the refresh spinner positioned correctly while still insetting content; `stretch` makes blocks fill the width the way `ListView` children do. A homogeneous item list may still use `ListView.separated` — but prefer `RefreshIndicator.adaptive` over plain `RefreshIndicator` either way.

- **Strings in ARB files.** When the project uses `.arb` files, each new user-visible string goes into every locale's file.
- **A provisional stub's delay** is `Future.delayed(const Duration(milliseconds: 400))`.
- **Branch on `defaultTargetPlatform`.** Behavior that differs per platform reads `defaultTargetPlatform` (`package:flutter/foundation.dart`) or `Theme.of(context).platform`, never `Platform.isIOS` / `Platform.isAndroid` from `dart:io`, which a test can't change.

## Tests

- **Form.** A screen state or user action is a widget test, `testWidgets('saved-articles.1 Empty', …)`; repository and state tests use `test(…)`, or the project's own helper such as `blocTest(…)`. For the Riverpod stack with nothing to mirror, start from `templates/riverpod-gorouter-dio/screen_test.dart`.
- **Unescaped titles.** Double quotes when the title holds an apostrophe, a raw string (`r'…'`) when it holds `$` or a backslash.
- **Platform scenarios.** A scenario tagged `<!-- platform: ios -->` is a `testWidgets` with `variant: TargetPlatformVariant.only(TargetPlatform.iOS)` (`TargetPlatform.android` for `android`), or a `test` that sets `debugDefaultTargetPlatformOverride` and resets it with `addTearDown`.
- **Native interfaces.** Screen and state tests fake the interface class. The wrapper around a channel gets its own test, with the channel faked through `TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler`; Pigeon's generated code gets none.
- **Host tests** live under `test/`. Tests under `integration_test/` need a device.
