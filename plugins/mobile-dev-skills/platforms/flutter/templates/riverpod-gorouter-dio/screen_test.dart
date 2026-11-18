// Template: widget tests for a screen's section 6 scenarios (Riverpod).
//
// Each description starts with the requirement id and the scenario title,
// exactly as the spec writes them. The spec's `test` anchors point at that text.
//
// Adjust to match project conventions:
//   - Does the project have a shared pump helper (theme, l10n, router)? Use it.
//   - Does it mock with mocktail / mockito instead of overriding with fakes?
//   - Riverpod 3 retries a failed provider: pass `retry: (_, __) => null` to
//     ProviderScope there, or the Error test counts the retries too.

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

// import 'package:app/features/example/...'; // <-- match project paths

Future<void> pumpScreen(
  WidgetTester tester,
  Future<List<Example>> Function() list,
) {
  return tester.pumpWidget(
    ProviderScope(
      overrides: [examplesProvider.overrideWith((ref) => list())],
      child: const MaterialApp(home: ExampleListScreen()),
    ),
  );
}

void main() {
  testWidgets('example.1 Loading', (tester) async {
    final pending = Completer<List<Example>>();
    await pumpScreen(tester, () => pending.future);

    // No pumpAndSettle: the spinner never settles.
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
  });

  testWidgets('example.1 Error', (tester) async {
    var calls = 0;
    await pumpScreen(tester, () async {
      calls++;
      throw Exception('offline');
    });
    await tester.pumpAndSettle();

    expect(find.text('Something went wrong'), findsOneWidget);

    await tester.tap(find.text('Retry'));
    await tester.pumpAndSettle();

    expect(calls, 2);
  });

  testWidgets('example.1 Empty', (tester) async {
    await pumpScreen(tester, () async => []);
    await tester.pumpAndSettle();

    expect(find.text('Nothing here yet'), findsOneWidget);
  });

  testWidgets('example.1 Success', (tester) async {
    final item = Example(id: '1', name: 'First', createdAt: DateTime(2026));
    await pumpScreen(tester, () async => [item]);
    await tester.pumpAndSettle();

    expect(find.text('First'), findsOneWidget);
  });
}
